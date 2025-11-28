"""
Creates visual grid layouts from unlimited images with dynamic inputs.
Configurable spacing, background colors, and grid arrangement.
Auto-scales and centers images while preserving aspect ratios.
Category: nhk
"""

import torch
import math

class ImageGridComposite:
    """
    Creates a grid composite from a dynamic number of input images.
    Images are arranged left-to-right, top-to-bottom with configurable spacing.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                    "tooltip": "Total width of output composite (height calculated automatically)"
                }),
                "images_per_row": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 20,
                    "step": 1,
                    "tooltip": "Number of images per row in the grid"
                }),
                "spacing": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Spacing between images in pixels"
                }),
                "background_color": (["black", "white", "gray", "red", "green", "blue"], {
                    "default": "black (nhk)",
                    "tooltip": "Background color for spacing and empty cells"
                }),
            },
            "optional": {},
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("composite", "width", "height")
    FUNCTION = "create_composite"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Creates visual grid layouts from unlimited images with dynamic inputs"
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        # Accept dynamic inputs; validation handled at runtime
        return True
    
    def create_composite(self, width, images_per_row, spacing, background_color, **kwargs):
        # Collect all connected IMAGE tensors regardless of input names
        images = [
            value for value in kwargs.values() if isinstance(value, torch.Tensor)
        ]
        
        if not images:
            # Return a blank image if no inputs
            height = 512
            blank = torch.zeros((1, height, width, 3), dtype=torch.float32)
            return (blank, width, height)
        
        # Get color values
        color_map = {
            "black": (0.0, 0.0, 0.0),
            "white": (1.0, 1.0, 1.0),
            "gray": (0.5, 0.5, 0.5),
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 1.0, 0.0),
            "blue": (0.0, 0.0, 1.0),
        }
        bg_color = color_map[background_color]
        
        # Calculate grid dimensions
        num_images = len(images)
        num_rows = math.ceil(num_images / images_per_row)
        
        # Calculate cell dimensions
        total_spacing_width = (images_per_row - 1) * spacing
        cell_width = (width - total_spacing_width) // images_per_row
        
        # Calculate what each image should be scaled to fit in its cell
        # First, determine the maximum dimensions needed for any cell
        max_scaled_height = 0
        for img in images:
            img_height, img_width = img.shape[1], img.shape[2]
            
            # Calculate scale factors to fit within cell
            scale_w = cell_width / img_width if img_width > cell_width else 1.0
            scale_h = float('inf')  # No height limit yet, will be determined
            scale = min(scale_w, scale_h) if scale_h != float('inf') else scale_w
            
            # Calculate scaled dimensions
            scaled_height = int(img_height * scale) if scale < 1.0 else img_height
            max_scaled_height = max(max_scaled_height, scaled_height)
        
        cell_height = max_scaled_height
        
        # Now recalculate with height constraints
        final_cell_height = cell_height
        for img in images:
            img_height, img_width = img.shape[1], img.shape[2]
            
            # Calculate scale factors to fit within cell
            scale_w = cell_width / img_width if img_width > cell_width else 1.0
            scale_h = final_cell_height / img_height if img_height > final_cell_height else 1.0
            scale = min(scale_w, scale_h)
            
            # If any image still doesn't fit, increase cell height
            if scale < 1.0:
                scaled_height = int(img_height * scale)
                final_cell_height = max(final_cell_height, scaled_height)
        
        cell_height = final_cell_height
        
        # Calculate total composite height
        total_spacing_height = (num_rows - 1) * spacing
        composite_height = num_rows * cell_height + total_spacing_height
        
        # Get batch size from first image
        batch_size = images[0].shape[0]
        channels = images[0].shape[3]
        
        # Create composite tensor filled with background color
        composite = torch.full(
            (batch_size, composite_height, width, channels),
            0.0,
            dtype=torch.float32,
            device=images[0].device
        )
        
        # Fill with background color
        for c in range(channels):
            if c < len(bg_color):
                composite[:, :, :, c] = bg_color[c]
            else:
                composite[:, :, :, c] = bg_color[0]  # Use first color component for extra channels
        
        # Place images in grid
        for i, image in enumerate(images):
            row = i // images_per_row
            col = i % images_per_row
            
            # Calculate position
            y_start = row * (cell_height + spacing)
            x_start = col * (cell_width + spacing)
            
            # Get original image dimensions
            img_height, img_width = image.shape[1], image.shape[2]
            
            # Calculate scale to fit within cell (preserve aspect ratio)
            scale_w = cell_width / img_width if img_width > 0 else 1.0
            scale_h = cell_height / img_height if img_height > 0 else 1.0
            scale = min(scale_w, scale_h, 1.0)  # Never upscale, only downscale
            
            # Calculate scaled dimensions
            scaled_width = max(1, int(img_width * scale))
            scaled_height = max(1, int(img_height * scale))
            
            # Scale the image if needed
            if scale < 1.0:
                # Use ComfyUI's scaling function
                import comfy.utils
                scaled_image = comfy.utils.common_upscale(
                    image.movedim(-1, 1), scaled_width, scaled_height, "lanczos", "disabled"
                ).movedim(1, -1)
            else:
                scaled_image = image
                scaled_height = img_height
                scaled_width = img_width
            
            # Calculate centering within cell
            y_offset = (cell_height - scaled_height) // 2
            x_offset = (cell_width - scaled_width) // 2
            
            # Calculate actual placement coordinates
            y_pos = y_start + y_offset
            x_pos = x_start + x_offset
            
            # Place the scaled image
            composite[:, y_pos:y_pos + scaled_height, x_pos:x_pos + scaled_width, :] = scaled_image
        
        return (composite, width, composite_height)

# Node registration
NODE_CLASS_MAPPINGS = {
    "ImageGridComposite": ImageGridComposite
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageGridComposite": "🎯 Image Grid Composite (nhk)"
}