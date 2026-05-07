"""
Crops an image (and its mask) to the bounding box of the mask, with a single
padding value applied uniformly on all sides. Designed to follow SAM3 / any
mask-producing node so you get a tight, framed cutout of the detected object.
Outputs the cropped image, the cropped mask, and the bbox (x, y, w, h) for
later stitch-back if needed.
Category: nhk/image
"""

import torch


class CropToMask:
    """
    Compute the bounding box of the mask, expand it by `padding` pixels on
    every side (clamped to image bounds), and crop image + mask to that box.
    If the mask is empty, the original image and mask are returned unchanged.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Image to crop (BHWC)"}),
                "mask": ("MASK", {"tooltip": "Mask defining the object bounding box"}),
                "padding": ("INT", {
                    "default": 32,
                    "min": -2048,
                    "max": 4096,
                    "step": 1,
                    "tooltip": "Pixels added on all sides of the mask bbox. Negative values tighten the crop."
                }),
            },
            "optional": {
                "mask_threshold": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "Pixels with mask value above this count as 'object' when computing the bbox"
                }),
                "divisible_by": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 256,
                    "step": 1,
                    "tooltip": "Round the crop width/height up to a multiple of this value (e.g. 8, 16, 64). 1 = disabled."
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "x", "y", "width", "height")
    FUNCTION = "crop"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Crop image+mask to mask bbox with uniform padding (great after SAM3)"

    def _round_up(self, value, multiple):
        if multiple <= 1:
            return value
        return ((value + multiple - 1) // multiple) * multiple

    def crop(self, image, mask, padding, mask_threshold=0.5, divisible_by=1):
        # image: [B, H, W, C], mask: [B, H, W] (ComfyUI conventions)
        if image.ndim != 4:
            raise ValueError(f"CropToMask: expected IMAGE with 4 dims, got {image.shape}")
        if mask.ndim != 3:
            # Some upstream nodes hand back [H, W]; normalize.
            if mask.ndim == 2:
                mask = mask.unsqueeze(0)
            else:
                raise ValueError(f"CropToMask: expected MASK with 3 dims, got {mask.shape}")

        B, H, W, C = image.shape

        # Use the first mask in the batch to define the bbox (typical SAM3 case:
        # batch of 1, or batch matching image batch but same subject framing).
        m = mask[0]
        binary = m > mask_threshold

        if not torch.any(binary):
            # Empty mask -> pass through unchanged so the workflow doesn't crash.
            print("[CropToMask] mask is empty above threshold; returning original image/mask.")
            return (image, mask, 0, 0, W, H)

        # Find tight bbox of mask
        rows = torch.any(binary, dim=1)
        cols = torch.any(binary, dim=0)
        ys = torch.where(rows)[0]
        xs = torch.where(cols)[0]
        y_min = int(ys[0].item())
        y_max = int(ys[-1].item())  # inclusive
        x_min = int(xs[0].item())
        x_max = int(xs[-1].item())  # inclusive

        # Apply uniform padding
        x0 = x_min - padding
        y0 = y_min - padding
        x1 = x_max + 1 + padding  # exclusive
        y1 = y_max + 1 + padding  # exclusive

        # Round size up to divisible_by (expand symmetrically when possible)
        if divisible_by > 1:
            cur_w = x1 - x0
            cur_h = y1 - y0
            new_w = self._round_up(max(cur_w, 1), divisible_by)
            new_h = self._round_up(max(cur_h, 1), divisible_by)
            extra_w = new_w - cur_w
            extra_h = new_h - cur_h
            x0 -= extra_w // 2
            x1 += extra_w - (extra_w // 2)
            y0 -= extra_h // 2
            y1 += extra_h - (extra_h // 2)

        # Clamp to image bounds
        x0 = max(0, min(W, x0))
        y0 = max(0, min(H, y0))
        x1 = max(0, min(W, x1))
        y1 = max(0, min(H, y1))

        # Guard against degenerate crops (e.g. extreme negative padding)
        if x1 <= x0 or y1 <= y0:
            print(f"[CropToMask] degenerate crop after padding ({x0},{y0})-({x1},{y1}); returning original.")
            return (image, mask, 0, 0, W, H)

        cropped_image = image[:, y0:y1, x0:x1, :].contiguous()
        cropped_mask = mask[:, y0:y1, x0:x1].contiguous()

        out_w = x1 - x0
        out_h = y1 - y0
        return (cropped_image, cropped_mask, x0, y0, out_w, out_h)


NODE_CLASS_MAPPINGS = {
    "CropToMask": CropToMask,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropToMask": "🎯 Crop To Mask (nhk)",
}
