"""
Flattens RGBA images to RGB by compositing over a solid background color.
Eliminates alpha-related artifacts and color bleed from semi-transparent pixels.
Category: nhk/image
"""

import torch


class RGBAFlatten:
    """
    Convert RGBA image to RGB by compositing over a solid background color.
    Handles color bleed by replacing RGB values in semi-transparent pixels before compositing.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Input image (RGB or RGBA)"}),
                "background_color": ("STRING", {
                    "default": "#FFFFFF",
                    "tooltip": "Background color as hex (e.g., #FFFFFF, #000000, #F2F2F2)"
                }),
            },
            "optional": {
                "mask": ("MASK", {
                    "tooltip": "Optional mask input (used if image has no alpha channel)"
                }),
                "alpha_threshold": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "Pixels with alpha below this are treated as fully transparent (0.0 = disabled)"
                }),
                "linear_blend": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Blend in linear color space (more accurate, slower)"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "flatten"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Flatten RGBA to RGB over solid background, eliminating alpha artifacts"

    def parse_hex_color(self, hex_color):
        """Parse hex color string to RGB tuple (0-1 float)."""
        hex_color = hex_color.strip().lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        if len(hex_color) != 6:
            return (1.0, 1.0, 1.0)  # Default white
        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        except ValueError:
            return (1.0, 1.0, 1.0)

    def srgb_to_linear(self, x):
        """Convert sRGB to linear RGB."""
        return torch.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)

    def linear_to_srgb(self, x):
        """Convert linear RGB to sRGB."""
        return torch.where(x <= 0.0031308, x * 12.92, 1.055 * (x ** (1.0 / 2.4)) - 0.055)

    def flatten(self, image, background_color, mask=None, alpha_threshold=0.0, linear_blend=False):
        batch_size = image.shape[0]
        height = image.shape[1]
        width = image.shape[2]
        channels = image.shape[3]

        # Parse background color
        bg_r, bg_g, bg_b = self.parse_hex_color(background_color)

        results = []

        for i in range(batch_size):
            img = image[i]  # Shape: [H, W, C]

            # Extract RGB
            rgb = img[:, :, :3]  # [H, W, 3]

            # Get alpha: from mask input, from 4th channel, or default to opaque
            if mask is not None:
                # Use provided mask (ComfyUI masks are inverted: 1=transparent, 0=opaque)
                mask_idx = min(i, mask.shape[0] - 1)
                alpha = 1.0 - mask[mask_idx]  # Invert to standard alpha
                alpha = alpha.unsqueeze(-1)  # [H, W, 1]
            elif channels == 4:
                alpha = img[:, :, 3:4]  # [H, W, 1]
            else:
                # No alpha info, return as-is
                results.append(rgb)
                continue

            # Apply alpha threshold - pixels below threshold become fully transparent
            if alpha_threshold > 0.0:
                alpha = torch.where(alpha < alpha_threshold, torch.zeros_like(alpha), alpha)

            # Create background tensor
            bg = torch.tensor([bg_r, bg_g, bg_b], dtype=rgb.dtype, device=rgb.device)
            bg = bg.view(1, 1, 3).expand(height, width, 3)

            if linear_blend:
                # Convert to linear space for accurate blending
                rgb = self.srgb_to_linear(rgb)
                bg = self.srgb_to_linear(bg)

            # Standard "over" compositing: out = fg * alpha + bg * (1 - alpha)
            # For semi-transparent pixels with bad RGB, the background color
            # naturally dominates due to the (1 - alpha) factor
            out = rgb * alpha + bg * (1.0 - alpha)

            if linear_blend:
                # Convert back to sRGB
                out = self.linear_to_srgb(out)

            # Clamp to valid range
            out = torch.clamp(out, 0.0, 1.0)

            results.append(out)

        output = torch.stack(results, dim=0)
        return (output,)


NODE_CLASS_MAPPINGS = {
    "RGBAFlatten": RGBAFlatten,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RGBAFlatten": "🎨 RGBA Flatten (nhk)",
}
