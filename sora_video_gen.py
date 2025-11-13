"""
Generate videos using OpenAI Sora API.
Text-to-video and image-to-video generation with progress tracking.
Requires OPENAI_API_KEY in .env file.
Category: nhk/ai
"""

import os
import sys
import time
import random
import torch
import numpy as np
from PIL import Image
import tempfile
import folder_paths
import requests
from comfy_api.input_impl import VideoFromFile

class SoraVideoGen:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["sora-2", "sora-2-pro"], {"default": "sora-2"}),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Describe the video: shot type, subject, action, setting, lighting..."
                }),
                "size": ([
                    "1920x1080",
                    "1080x1920",
                    "1280x720",
                    "720x1280"
                ], {"default": "1280x720"}),
                "seconds": (["5", "8", "10"], {"default": "8"}),
            },
            "optional": {
                "input_image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "generate_video"
    CATEGORY = "nhk/ai"
    DESCRIPTION = "Generate videos using OpenAI Sora API"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution every time"""
        return f"sora_gen_{time.time()}_{random.randint(1000, 9999)}"

    def tensor_to_pil(self, image_tensor):
        """Convert ComfyUI IMAGE tensor to PIL Image"""
        tensor_cpu = image_tensor.cpu()
        numpy_array = np.clip(255. * tensor_cpu.numpy().squeeze(), 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(numpy_array)

        # Cleanup
        del tensor_cpu, numpy_array

        return pil_image

    def generate_video(self, model, prompt, size, seconds, input_image=None):
        """Generate video using Sora API via REST"""

        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Error: OPENAI_API_KEY not found in environment variables")

        # Validate prompt
        if not prompt or not prompt.strip():
            raise ValueError("Error: Prompt cannot be empty")

        try:
            base_url = "https://api.openai.com/v1/videos"
            headers = {"Authorization": f"Bearer {api_key}"}

            print(f"\n{'='*60}")
            print(f"🎬 Starting Sora video generation")
            print(f"Model: {model}")
            print(f"Size: {size}")
            print(f"Duration: {seconds}s")
            print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"{'='*60}\n")

            # Prepare multipart form data
            files = {
                "model": (None, model),
                "prompt": (None, prompt.strip()),
                "size": (None, size),
                "seconds": (None, seconds)
            }

            # Handle input image if provided
            tmp_path = None
            if input_image is not None:
                print("📸 Using input image as first frame reference")
                pil_image = self.tensor_to_pil(input_image)

                tmp_path = tempfile.mktemp(suffix='.png')
                pil_image.save(tmp_path, format='PNG')

                files["input_reference"] = ("reference.png", open(tmp_path, 'rb'), 'image/png')

            # Create video job
            response = requests.post(base_url, headers=headers, files=files)

            # Clean up temp file if used
            if tmp_path and os.path.exists(tmp_path):
                if "input_reference" in files:
                    files["input_reference"][1].close()
                os.unlink(tmp_path)

            response.raise_for_status()
            video = response.json()

            video_id = video["id"]
            print(f"✓ Job created: {video_id}")
            print(f"Status: {video['status']}\n")

            # Poll for completion with progress bar
            bar_length = 40

            while video["status"] in ("in_progress", "queued"):
                time.sleep(2)

                # Get status
                status_response = requests.get(f"{base_url}/{video_id}", headers=headers)
                status_response.raise_for_status()
                video = status_response.json()

                progress = video.get("progress", 0)
                filled_length = int((progress / 100) * bar_length)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                status_text = "Queued" if video["status"] == "queued" else "Processing"

                sys.stdout.write(f"\r{status_text}: [{bar}] {progress:.1f}%")
                sys.stdout.flush()

            # Clear progress line
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()

            # Check for failure
            if video["status"] == "failed":
                error_msg = video.get("error", {}).get("message", "Video generation failed")
                raise RuntimeError(f"Sora API error: {error_msg}")

            print(f"✓ Video generation completed!")
            print(f"Downloading video content...")

            # Download video
            download_response = requests.get(
                f"{base_url}/{video_id}/content",
                headers=headers,
                stream=True
            )
            download_response.raise_for_status()

            # Save to ComfyUI output directory
            output_dir = folder_paths.get_output_directory()
            timestamp = int(time.time())
            filename = f"sora_{timestamp}_{video_id[-8:]}.mp4"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"✓ Saved to: {filename}")
            print(f"{'='*60}\n")

            # Return VideoInput object for ComfyUI
            return (VideoFromFile(filepath),)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error generating video: {str(e)}")

NODE_CLASS_MAPPINGS = {
    "SoraVideoGen": SoraVideoGen
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SoraVideoGen": "🎬 Sora Video Generation"
}
