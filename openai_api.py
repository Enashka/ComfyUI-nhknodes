"""
Chat with OpenAI GPT-4o with vision capabilities.
Send text messages and/or images to get AI responses.
Requires OPENAI_API_KEY in .env file.
Category: nhk/ai
"""

import os
import time
import random
import torch
import numpy as np
from PIL import Image
import base64
import io
from openai import OpenAI

class LLMChat:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ([
                    "gpt-4o", 
                    "gpt-4o-mini", 
                    "chatgpt-4o-latest (nhk)",
                    "gpt-5 (nhk)",
                    "gpt-5-mini", 
                    "gpt-5-nano"
                ], {"default": "gpt-4o"}),
                "system_message": ("STRING", {
                    "multiline": True,
                    "default": " (nhk)",
                    "placeholder": "System prompt"
                }),
                "user_message": ("STRING", {
                    "multiline": True,
                    "default": " (nhk)",
                    "placeholder": "User message"
                }),
            },
            "optional": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "chat_completion"
    CATEGORY = "nhk/ai"
    DESCRIPTION = "Chat with OpenAI GPT-4o with vision capabilities"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution every time by returning a random value"""
        return f"llm_chat_{time.time()}_{random.randint(1000, 9999)}"
    
    def pil_to_base64(self, image: Image.Image) -> str:
        """Converts a PIL Image to a Base64 encoded string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def chat_completion(self, model, system_message="", user_message="", image=None):
        """OpenAI API call with vision support"""
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ("Error: OPENAI_API_KEY not found in environment variables",)
        
        # Validate inputs
        if not user_message or not user_message.strip():
            return ("Error: User message cannot be empty",)
        
        try:
            client = OpenAI(api_key=api_key)
            
            # Use Responses API for GPT-5 models, Chat Completions for GPT-4 models
            if model.startswith("gpt-5"):
                # Responses API format - system message goes in input array
                input_content = []
                
                # Add system message first if provided
                if system_message and system_message.strip():
                    input_content.append({"role": "system", "content": system_message.strip()})
                
                # Add user message and image
                if image is not None:
                    # Convert ComfyUI tensor to PIL Image with explicit cleanup
                    tensor_cpu = image.cpu()
                    numpy_array = np.clip(255. * tensor_cpu.numpy().squeeze(), 0, 255).astype(np.uint8)
                    pil_image = Image.fromarray(numpy_array)
                    base64_image = self.pil_to_base64(pil_image)

                    # Explicit cleanup
                    del tensor_cpu, numpy_array, pil_image
                    
                    input_content.append({
                        "role": "user (nhk)",
                        "content": [
                            {"type": "input_text", "text": user_message.strip()},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{base64_image}"}
                        ]
                    })
                else:
                    input_content.append({"role": "user", "content": user_message.strip()})
                
                response = client.responses.create(
                    model=model,
                    input=input_content,
                    reasoning={"effort": "minimal"},
                    text={"verbosity": "low"}
                )
                return (response.output_text,)
                
            else:
                # Chat Completions API format for GPT-4 models
                messages = []
                if system_message and system_message.strip():
                    messages.append({"role": "system", "content": system_message.strip()})
                
                if image is not None:
                    # Convert ComfyUI tensor to PIL Image with explicit cleanup
                    tensor_cpu = image.cpu()
                    numpy_array = np.clip(255. * tensor_cpu.numpy().squeeze(), 0, 255).astype(np.uint8)
                    pil_image = Image.fromarray(numpy_array)
                    base64_image = self.pil_to_base64(pil_image)

                    # Explicit cleanup
                    del tensor_cpu, numpy_array, pil_image
                    
                    user_content = [
                        {"type": "text", "text": user_message.strip()},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                else:
                    user_content = user_message.strip()
                    
                messages.append({"role": "user", "content": user_content})
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=2048
                )
                return (response.choices[0].message.content,)
            
        except Exception as e:
            return (f"Error calling OpenAI API: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "LLMChat": LLMChat
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LLMChat": "🤖 OpenAI API (nhk)",
}