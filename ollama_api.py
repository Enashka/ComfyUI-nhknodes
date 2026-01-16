"""
Chat with local Ollama models.
Send text messages and/or images to get AI responses from locally hosted LLMs.
Supports both text-only and vision-language models.
No API key required.
Category: nhk/ai
"""

import time
import random
import requests
import json
import base64
import tempfile
import os
import re
from PIL import Image
import torch
import numpy as np

class OllamaChat:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ([
                    "qwen3:8b",
                    "qwen3:30b",
                    "qwen3:30b-a3b-instruct-2507-q4_K_M",
                    "qwen3-vl:8b",
                    "llama3.2-vision:11b",
                    "gemma3-27b-it-q8",
                    "devstral:24b-small-2505-q8_0",
                    "moondream:latest",
                    "minicpm-v:latest"
                ], {
                    "default": "qwen3:8b",
                    "tooltip": "Local Ollama model to use (models with 'vl' or 'vision' support images)"
                }),
                "system_message": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "System prompt",
                    "tooltip": "System message to set assistant behavior and context"
                }),
                "user_message": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "User message",
                    "tooltip": "User message/prompt to send to the model"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider",
                    "tooltip": "Randomness in responses (0=deterministic, 2=very random)"
                }),
                "max_tokens": ("INT", {
                    "default": 512,
                    "min": 50,
                    "max": 131072,
                    "step": 50,
                    "tooltip": "Maximum response length in tokens"
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "Optional image for vision-enabled models (qwen3-vl, llama3.2-vision)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("info", "thinking", "response")
    FUNCTION = "chat_completion"
    CATEGORY = "nhk/ai"
    DESCRIPTION = "Chat with local Ollama models (text and/or vision)"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution every time by returning a random value"""
        return f"ollama_chat_{time.time()}_{random.randint(1000, 9999)}"

    def tensor_to_pil(self, tensor):
        """Convert ComfyUI tensor to PIL Image"""
        # Handle batch of images (take first one)
        if len(tensor.shape) == 4:
            tensor = tensor[0]

        # Convert from tensor format to PIL
        i = 255. * tensor.cpu().numpy().squeeze()
        img = Image.fromarray(i.astype('uint8'))
        return img

    def _clean_text(self, text, strip_think=True):
        if not isinstance(text, str):
            return ""

        cleaned = text.strip()
        if not cleaned:
            return ""

        if strip_think:
            # Strip <think>...</think> blocks if they slipped into the response
            cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
        return cleaned

    def _collect_texts(self, content):
        """Recursively gather non-thinking text segments from nested data."""
        collected = []

        if isinstance(content, str):
            text = self._clean_text(content)
            if text:
                collected.append(text)
            return collected

        if isinstance(content, dict):
            item_type = str(content.get("type", "")).lower()
            if "think" in item_type or "reason" in item_type:
                return collected

            # Prefer explicit text/content fields
            if "text" in content:
                collected.extend(self._collect_texts(content["text"]))
            if "content" in content:
                collected.extend(self._collect_texts(content["content"]))
            return collected

        if isinstance(content, (list, tuple)):
            for item in content:
                collected.extend(self._collect_texts(item))
            return collected

        return collected

    def _extract_response_text(self, result):
        """Prefer legacy response field first, then structured content."""
        response_text = self._clean_text(result.get("response", ""))
        if response_text:
            return response_text

        message = result.get("message")
        if message is not None:
            message_texts = self._collect_texts(message)
            if message_texts:
                return "\n\n".join(message_texts)

        # Some models may return additional content fields
        for key in ("content", "final", "output"):
            if key in result:
                texts = self._collect_texts(result[key])
                if texts:
                    return "\n\n".join(texts)

        return ""

    def _collect_thinking_segments(self, content):
        """Gather thinking/reasoning text segments."""
        collected = []

        if isinstance(content, str):
            text = self._clean_text(content, strip_think=False)
            if text:
                collected.append(text)
            return collected

        if isinstance(content, dict):
            item_type = str(content.get("type", "")).lower()
            if "think" in item_type or "reason" in item_type:
                if "text" in content:
                    collected.extend(self._collect_thinking_segments(content["text"]))
                if "content" in content:
                    collected.extend(self._collect_thinking_segments(content["content"]))
                return collected

            # dive into nested fields to catch embedded thinking
            if "text" in content:
                collected.extend(self._collect_thinking_segments(content["text"]))
            if "content" in content:
                collected.extend(self._collect_thinking_segments(content["content"]))
            return collected

        if isinstance(content, (list, tuple)):
            for item in content:
                collected.extend(self._collect_thinking_segments(item))
            return collected

        return collected

    def _extract_thinking_text(self, result):
        thinking_parts = []

        top_level = self._clean_text(result.get("thinking", ""), strip_think=False)
        if top_level:
            thinking_parts.append(top_level)

        message = result.get("message")
        if message is not None:
            thinking_parts.extend(self._collect_thinking_segments(message))

        for key in ("content", "final", "output"):
            if key in result:
                thinking_parts.extend(self._collect_thinking_segments(result[key]))

        joined = "\n\n".join(part for part in thinking_parts if part)
        return joined.strip()

    def chat_completion(self, model, system_message="", user_message="", temperature=0.7, max_tokens=512, image=None):
        """Ollama API call via HTTP with optional image support"""

        # Validate inputs
        if not user_message or not user_message.strip():
            error_msg = "Error: User message cannot be empty"
            return (error_msg, "", error_msg)

        try:
            # Default system message if none provided
            if not system_message or system_message.strip() == "":
                system_message = "You are a helpful AI assistant."

            # Prepare API payload
            payload = {
                "model": model,
                "prompt": user_message.strip(),
                "system": system_message.strip(),
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "hide_thinking": True  # always request final answer only
                }
            }

            # Add image if provided (will be silently ignored by non-vision models)
            if image is not None:
                # Convert tensor to PIL Image
                pil_image = self.tensor_to_pil(image)

                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    pil_image.save(tmp_file.name, 'JPEG', quality=95)
                    temp_path = tmp_file.name

                try:
                    # Encode image to base64
                    with open(temp_path, 'rb') as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                    payload["images"] = [img_base64]
                finally:
                    # Clean up temporary file
                    os.unlink(temp_path)

            # Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=120
            )

            response.raise_for_status()
            result = response.json()

            # Extract response and thinking traces separately
            response_text = self._extract_response_text(result)
            thinking_text = self._extract_thinking_text(result)

            if not response_text:
                error_msg = "Error: Empty response from Ollama"
                info = f"{error_msg} (Model: {model})"
                return (info, thinking_text or "", error_msg)

            info = f"Model: {model}, Temp: {temperature}, Max tokens: {max_tokens}, Hide thinking: True"
            if image is not None:
                info += " [with image]"

            return (info, thinking_text or "", response_text)

        except requests.exceptions.ConnectionError:
            error_msg = "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
            return (error_msg, "", error_msg)
        except requests.exceptions.Timeout:
            error_msg = "Error: Ollama request timed out"
            return (error_msg, "", error_msg)
        except Exception as e:
            error_msg = f"Error calling Ollama API: {str(e)}"
            return (error_msg, "", error_msg)

NODE_CLASS_MAPPINGS = {
    "OllamaChat": OllamaChat
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaChat": "🦙 Ollama API (nhk)",
}
