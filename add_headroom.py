"""
Adds headroom to images by scaling them down within the original canvas.
Perfect for giving characters breathing room when their heads are too close to the top edge.
The image is anchored to the bottom-center, with configurable background fill.
Category: nhk/image
"""

import torch
import numpy as np
from PIL import Image

class AddHeadroom:
    """
    Reduces image size by a percentage while keeping the original canvas dimensions.
    Image is anchored bottom-center with selectable background fill (white/black/transparent).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Input image or batch to add headroom"}),
                "reduction_percent": ("FLOAT", {
                    "default": 10.0,
                    "min": 0.0,
                    "max": 50.0,
                    "step": 0.5,
                    "display": "number",
                    "tooltip": "Percentage to reduce image size (creates headroom)"
                }),
                "background": (["black", "white", "transparent"], {
                    "tooltip": "Background fill color for headroom area"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "add_headroom"
    CATEGORY = "nhk/image"

    def add_headroom(self, image, reduction_percent, background):
        # Handle batch of images
        batch_size = image.shape[0]
        results = []

        for i in range(batch_size):
            # Get single image (H, W, C)
            single_image = image[i]

            # Get original dimensions
            original_height, original_width = single_image.shape[0], single_image.shape[1]

            # Calculate new dimensions (reduced by percentage)
            scale_factor = 1.0 - (reduction_percent / 100.0)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)

            # Convert to PIL for resizing
            img_array = (single_image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_array)

            # Resize the image
            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create canvas with appropriate mode and background
            if background == "transparent":
                canvas = Image.new("RGBA", (original_width, original_height), (0, 0, 0, 0))
                # Convert resized image to RGBA if needed
                if resized_image.mode != "RGBA":
                    resized_image = resized_image.convert("RGBA")
            else:
                # Determine if original image has alpha channel
                has_alpha = single_image.shape[2] == 4 if len(single_image.shape) == 3 else False
                mode = "RGBA" if has_alpha else "RGB"

                if background == "white":
                    bg_color = (255, 255, 255, 255) if has_alpha else (255, 255, 255)
                else:  # black
                    bg_color = (0, 0, 0, 255) if has_alpha else (0, 0, 0)

                canvas = Image.new(mode, (original_width, original_height), bg_color)

                # Convert resized image to match canvas mode
                if resized_image.mode != mode:
                    resized_image = resized_image.convert(mode)

            # Calculate position: centered horizontally, anchored to bottom
            paste_x = (original_width - new_width) // 2
            paste_y = original_height - new_height

            # Paste resized image onto canvas
            canvas.paste(resized_image, (paste_x, paste_y))

            # Convert back to tensor
            canvas_array = np.array(canvas).astype(np.float32) / 255.0
            canvas_tensor = torch.from_numpy(canvas_array)

            results.append(canvas_tensor)

        # Stack batch
        output = torch.stack(results, dim=0)

        return (output,)

# Register the node
NODE_CLASS_MAPPINGS = {
    "AddHeadroom": AddHeadroom,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AddHeadroom": "🧑 Add Headroom (nhk)",
}
