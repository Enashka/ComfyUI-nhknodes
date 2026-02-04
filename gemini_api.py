"""
Gemini API node for image generation and multimodal chat.
Supports up to 4 input images, text prompts, and outputs both image and text.
Requires GOOGLE_API_KEY in .env file.
Category: nhk/ai
"""

import os
import time
import random
import base64
import numpy as np
from PIL import Image
import io

from google import genai
from google.genai import types

# Load .env file from nhknodes directory
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".env")
load_dotenv(_env_path)


class GeminiImageChat:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "System instructions (optional)",
                    "tooltip": "System instructions to guide model behavior"
                }),
                "user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Describe what you want to generate or ask about the images",
                    "tooltip": "Main prompt for generation or image analysis"
                }),
            },
            "optional": {
                "model": ([
                    "gemini-3-pro-image-preview",
                    "gemini-2.5-flash-image"
                ], {
                    "default": "gemini-3-pro-image-preview",
                    "tooltip": "Gemini model (Pro = higher quality, Flash = faster)"
                }),
                "image_1": ("IMAGE", {
                    "tooltip": "First optional input image"
                }),
                "image_2": ("IMAGE", {
                    "tooltip": "Second optional input image"
                }),
                "image_3": ("IMAGE", {
                    "tooltip": "Third optional input image"
                }),
                "image_4": ("IMAGE", {
                    "tooltip": "Fourth optional input image"
                }),
                "aspect_ratio": ([
                    "3:4",
                    "1:1",
                    "2:3",
                    "3:2",
                    "4:3",
                    "4:5",
                    "5:4",
                    "9:16",
                    "16:9",
                    "21:9"
                ], {
                    "default": "3:4",
                    "tooltip": "Aspect ratio for generated image"
                }),
                "image_size": ([
                    "1K",
                    "2K",
                    "4K"
                ], {
                    "default": "2K",
                    "tooltip": "Output image resolution (4K for higher quality)"
                }),
                "output_mode": ([
                    "text_and_image",
                    "text_only",
                    "image_only"
                ], {
                    "default": "text_and_image",
                    "tooltip": "What type of output to request from the model"
                }),
                "temperature": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "tooltip": "Temperature controls randomness (0=deterministic, 2=very random)"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "tooltip": "Random seed for reproducibility (0=random)"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("image", "text",)
    FUNCTION = "generate"
    CATEGORY = "nhk/ai"
    DESCRIPTION = "Generate images and text with Gemini"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution every time"""
        return f"gemini_{time.time()}_{random.randint(1000, 9999)}"

    def tensor_to_pil(self, tensor) -> Image.Image:
        """Convert ComfyUI image tensor to PIL Image"""
        tensor_cpu = tensor.cpu()
        numpy_array = np.clip(255. * tensor_cpu.numpy().squeeze(), 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(numpy_array)
        del tensor_cpu, numpy_array
        return pil_image

    def pil_to_tensor(self, pil_image: Image.Image):
        """Convert PIL Image to ComfyUI image tensor (torch)"""
        import torch
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        numpy_array = np.array(pil_image).astype(np.float32) / 255.0
        tensor = torch.from_numpy(numpy_array).unsqueeze(0)
        return tensor

    def generate(self, system_prompt, user_prompt, model="gemini-3-pro-image-preview",
                 image_1=None, image_2=None, image_3=None, image_4=None,
                 aspect_ratio="3:4", image_size="2K", output_mode="text_and_image",
                 temperature=1.0, seed=0):
        """Call Gemini API for image generation/analysis"""

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return (None, f"Error: GOOGLE_API_KEY not found. Checked .env at: {_env_path}")

        if not user_prompt or not user_prompt.strip():
            return (None, "Error: User prompt cannot be empty")

        try:
            client = genai.Client(api_key=api_key)

            # Build contents array
            contents = []
            if system_prompt and system_prompt.strip():
                contents.append(f"System instructions: {system_prompt.strip()}\n\n")
            contents.append(user_prompt.strip())

            # Add input images
            for img in [image_1, image_2, image_3, image_4]:
                if img is not None:
                    pil_img = self.tensor_to_pil(img)
                    contents.append(pil_img)

            # Configure response modalities
            if output_mode == "text_only":
                modalities = ['TEXT']
            elif output_mode == "image_only":
                modalities = ['IMAGE']
            else:
                modalities = ['TEXT', 'IMAGE']

            # Build image config - Flash doesn't support imageSize
            if "flash" in model:
                image_cfg = types.ImageConfig(aspectRatio=aspect_ratio)
            else:
                image_cfg = types.ImageConfig(aspectRatio=aspect_ratio, imageSize=image_size)

            # Build generation config with temperature and seed
            config_params = {
                "response_modalities": modalities,
                "image_config": image_cfg,
                "temperature": temperature
            }

            # Only set seed if non-zero (0 means random)
            if seed != 0:
                config_params["seed"] = seed

            config = types.GenerateContentConfig(**config_params)

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )

            # Extract results
            result_text = ""
            result_image = None

            if not response.candidates:
                return (None, f"No response from API. Response: {response}")

            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                return (None, f"No content in response. Candidate: {candidate}")

            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    result_text += part.text
                elif hasattr(part, 'inline_data') and part.inline_data:
                    raw_data = part.inline_data.data
                    if isinstance(raw_data, str):
                        image_data = base64.b64decode(raw_data)
                    else:
                        image_data = raw_data
                    pil_image = Image.open(io.BytesIO(image_data))
                    result_image = self.pil_to_tensor(pil_image)

            return (result_image, result_text if result_text else "No text returned")

        except Exception as e:
            return (None, f"Error calling Gemini API: {str(e)}")


NODE_CLASS_MAPPINGS = {
    "GeminiImageChat": GeminiImageChat
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GeminiImageChat": "🍌 Gemini API (nhk)",
}
