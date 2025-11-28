"""
Comprehensive size picker with model-optimized presets for Flux, Qwen, and SDXL.
All dimensions are multiples of 32 for optimal generation quality.
Includes popular aspect ratios: square, landscape, portrait, ultrawide, and cinema.
Category: nhk
"""

import torch
import comfy.model_management

MAX_RESOLUTION=16384

class SizePicker:
    """
    Universal size picker with model-optimized presets for multiple AI models
    All dimensions are multiples of 32 for optimal generation quality
    """
    
    def __init__(self):
        self.device = comfy.model_management.intermediate_device()
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "resolution": ([
                    # 1:1 Square
                    "1024x1024 (1:1 Flux)",
                    "1328x1328 (1:1 Qwen)",
                    "1408x1408 (1:1 Flux Ultra)",
                    "1440x1440 (1:1 Flux Ultra)",
                    "1920x1920 (1:1 Ultra High-End)",
                    "2048x2048 (1:1 Seedream)",

                    # 16:9 Landscape (YouTube standard)
                    "1536x864 (16:9 Flux)",
                    "1664x928 (16:9 Qwen)",
                    "1792x1008 (16:9 Flux)",
                    "1920x1088 (16:9 Ultra)",
                    "2560x1440 (16:9 Ultra)",

                    # 9:16 Portrait (TikTok/Reels)
                    "864x1536 (9:16 Flux)",
                    "928x1664 (9:16 Qwen)",
                    "1008x1792 (9:16 Flux)",
                    "1088x1920 (9:16 Ultra)",
                    "1440x2560 (9:16 Ultra)",

                    # 4:5 Portrait (Instagram feed)
                    "1024x1280 (4:5 Flux)",
                    "1152x1440 (4:5 Flux)",
                    "896x1120 (4:5 Flux)",

                    # 3:4 Portrait (Instagram supported)
                    "960x1280 (3:4 Flux)",
                    "1104x1472 (3:4 Qwen)",
                    "1056x1408 (3:4 Flux)",
                    "1200x1600 (3:4 Ultra)",
                    "1728x2304 (3:4 Seedream)",

                    # 4:3 Landscape
                    "1152x864 (4:3 Flux)",
                    "1472x1140 (4:3 Qwen)",
                    "1280x960 (4:3 Flux)",
                    "1408x1056 (4:3 Flux)",
                    "2304x1728 (4:3 Seedream)",

                    # 3:2 Landscape
                    "1536x1024 (3:2 Flux)",
                    "1584x1056 (3:2 Qwen)",
                    "1344x896 (3:2 Flux)",
                    "1216x800 (3:2 Flux)",
                    "2496x1664 (3:2 Seedream)",

                    # 2:3 Portrait
                    "1024x1536 (2:3 Flux)",
                    "1056x1584 (2:3 Qwen)",
                    "896x1344 (2:3 Flux)",
                    "800x1216 (2:3 Flux)",
                    "1664x2496 (2:3 Seedream)",

                    # 1:3 Portrait (Ultra Tall)
                    "1296x4096 (1:3 Seedream)",

                    # 2:1 Landscape
                    "1024x512 (2:1 Flux)",
                    "1152x576 (2:1 Flux)",
                    "1280x640 (2:1 Flux)",
                    "1408x704 (2:1 Qwen)",
                    "1600x800 (2:1 Ultra)",

                    # 21:9 Ultrawide
                    "1344x576 (21:9 Flux)",
                    "2016x864 (21:9 Flux)",
                    "2688x1152 (21:9 Ultra)",
                    "3024x1296 (21:9 Seedream)",

                    # 1.91:1 Social/Link cards
                    "1216x640 (1.91:1 Flux)",
                    "1472x768 (1.91:1 Flux)",
                    "1856x972 (1.91:1 Ultra)",

                    # 2.39:1 Cinemascope
                    "1920x800 (2.39:1 Cinema)",
                    "2112x896 (2.39:1 Cinema)",

                    # SDXL Legacy
                    "1024x1024 (1:1 SDXL Base)",
                    "832x1216 (2:3 SDXL Portrait)",
                    "1216x832 (3:2 SDXL Landscape)",
                    "1344x768 (16:9 SDXL)",
                    "1536x640 (12:5 SDXL Wide)",

                    # Smaller Resolutions
                    "640x640 (1:1 Small)",
                    "512x512 (1:1 Compact)",
                    "768x768 (1:1 Medium)",
                    "896x896 (1:1 SD Format)",
                    "512x768 (2:3 Small Portrait)",
                    "768x512 (3:2 Small Landscape)",
                    "640x360 (16:9 Small)",
                    "480x848 (9:16 Small Portrait)",
                    "544x960 (9:16 Medium Portrait)",
                    "608x1088 (9:16 Large Portrait)",
                ], {"default": "1024x1024 (1:1 Flux)"}),
                
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
                
                "width_override": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": MAX_RESOLUTION, 
                    "step": 64,
                    "tooltip": "Override width (0 = use preset)"
                }),
                
                "height_override": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": MAX_RESOLUTION, 
                    "step": 64,
                    "tooltip": "Override height (0 = use preset)"
                }),
            }
        }
    
    RETURN_TYPES = ("LATENT", "INT", "INT", "STRING")
    RETURN_NAMES = ("latent", "width", "height", "info")
    FUNCTION = "execute"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Comprehensive size picker with model-optimized presets for Flux, Qwen, and SDXL"
    
    def execute(self, resolution, batch_size, width_override=0, height_override=0):
        # Parse resolution from dropdown
        dimensions = resolution.split(" ")[0]  # Get "1024x1024" part
        width_str, height_str = dimensions.split("x")
        
        # Use override if provided, otherwise use preset
        width = width_override if width_override > 0 else int(width_str)
        height = height_override if height_override > 0 else int(height_str)
        
        # Create empty latent tensor
        # Latent space is 1/8 the pixel dimensions
        latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=self.device)
        
        # Generate info string
        if width_override > 0 or height_override > 0:
            info = f"Custom: {width}x{height} (overridden)"
        else:
            # Extract aspect ratio and MP info from original string
            info_part = resolution.split(" ", 1)[1]  # Get "(1:1, 1.0MP)" part
            info = f"{width}x{height} {info_part}"
        
        return ({"samples": latent}, width, height, info)

# Node registration
NODE_CLASS_MAPPINGS = {
    "SizePicker": SizePicker
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SizePicker": "📐 Size Picker (nhk)"
}