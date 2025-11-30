"""
Resizes and positions images within a custom canvas size.
Scale images up/down and move them horizontally/vertically within a new canvas.
Perfect for repositioning subjects, creating compositions, or preparing frames for video.
Category: nhk/image
"""

import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw
import numpy as np

class VisualResizer:
    """
    Resizes and positions an image within a custom canvas.
    Allows scaling the input image and positioning it anywhere on the canvas.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Input image or batch to resize and position"}),
                "canvas_width": ("INT", {
                    "default": 1024,
                    "tooltip": "Width of output canvas"
                }),
                "canvas_height": ("INT", {
                    "default": 1024,
                    "tooltip": "Height of output canvas"
                }),
                "image_width": ("INT", {
                    "default": 512,
                    "tooltip": "Width to resize image to"
                }),
                "image_height": ("INT", {
                    "default": 512,
                    "tooltip": "Height to resize image to"
                }),
                "offset_x": ("INT", {
                    "default": 0,
                    "tooltip": "Horizontal offset from center (pixels)"
                }),
                "offset_y": ("INT", {
                    "default": 0,
                    "tooltip": "Vertical offset from center (pixels)"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resize_and_position"
    OUTPUT_NODE = True
    CATEGORY = "nhk/image"

    def resize_and_position(self, image, canvas_width, canvas_height, image_width, image_height,
                           offset_x, offset_y):

        # Handle batch of images
        batch_size = image.shape[0]
        results = []

        for i in range(batch_size):
            # Get single image (H, W, C)
            single_image = image[i]

            # Convert to PIL for easier manipulation
            img_array = (single_image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_array)

            # Resize the image
            resized_image = pil_image.resize((image_width, image_height))

            # Create black canvas
            canvas = Image.new("RGB", (canvas_width, canvas_height), (0, 0, 0))

            # Calculate position (center + offset)
            paste_x = (canvas_width - image_width) // 2 + offset_x
            paste_y = (canvas_height - image_height) // 2 + offset_y

            # Paste image onto canvas
            canvas.paste(resized_image, (paste_x, paste_y))

            canvas_array = np.array(canvas).astype(np.float32) / 255.0
            canvas_tensor = torch.from_numpy(canvas_array)

            results.append(canvas_tensor)

        # Stack batch
        output = torch.stack(results, dim=0)

        return (output,)

# Register the node
NODE_CLASS_MAPPINGS = {
    "VisualResizer": VisualResizer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisualResizer": "📏 Visual Resizer (nhk)",
}