"""
Extract Grid Panel
Extracts a single panel from a grid image using spreadsheet-style notation (a1, b3, etc.).
Row = letter (a=0, b=1...), Column = number (1=0, 2=1...).
Supports variable grid sizes and separator widths.
Category: nhk/image
"""

import torch
import numpy as np
from PIL import Image

def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def tensor2pil(tensor):
    return Image.fromarray(np.clip(255. * tensor.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

class ExtractGridPanel:
    """
    Extracts a single panel from a grid image.
    Panel notation: letter + number (e.g., a1, b2, c3)
    - Letter = row (a=first row, b=second row, etc.)
    - Number = column (1=first column, 2=second column, etc.)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Grid image to extract panel from"
                }),
                "rows": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 10,
                    "tooltip": "Number of rows in the grid"
                }),
                "columns": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 10,
                    "tooltip": "Number of columns in the grid"
                }),
                "panel": ("STRING", {
                    "default": "a1",
                    "tooltip": "Panel to extract (e.g., a1, b2, c3). Letter=row, number=column."
                }),
                "separator_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "tooltip": "Width of separator lines between panels (pixels)"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "panel_name", "width", "height")
    FUNCTION = "extract_panel"
    CATEGORY = "nhk/image"

    def extract_panel(self, image, rows, columns, panel, separator_width):
        # Parse panel notation (e.g., "a1", "b3", "c2")
        panel = panel.strip().lower()

        if len(panel) < 2:
            print(f"Invalid panel notation: {panel}")
            return (image, panel, 0, 0)

        # Extract row letter and column number
        row_letter = ""
        col_str = ""

        for i, char in enumerate(panel):
            if char.isalpha():
                row_letter += char
            else:
                col_str = panel[i:]
                break

        if not row_letter or not col_str:
            print(f"Invalid panel notation: {panel}")
            return (image, panel, 0, 0)

        try:
            # Convert letter to row index (a=0, b=1, etc.)
            row_idx = ord(row_letter[-1]) - ord('a')
            # Convert number to column index (1=0, 2=1, etc.)
            col_idx = int(col_str) - 1
        except ValueError:
            print(f"Invalid panel notation: {panel}")
            return (image, panel, 0, 0)

        # Validate indices
        if row_idx < 0 or row_idx >= rows:
            print(f"Row '{row_letter}' out of range (max: {chr(ord('a') + rows - 1)})")
            return (image, panel, 0, 0)

        if col_idx < 0 or col_idx >= columns:
            print(f"Column '{col_str}' out of range (max: {columns})")
            return (image, panel, 0, 0)

        # Convert tensor to PIL
        pil_image = tensor2pil(image)
        img_width, img_height = pil_image.size

        # Calculate cell dimensions (accounting for separators)
        total_sep_width = separator_width * (columns - 1)
        total_sep_height = separator_width * (rows - 1)

        cell_width = (img_width - total_sep_width) // columns
        cell_height = (img_height - total_sep_height) // rows

        # Calculate crop coordinates
        left = col_idx * (cell_width + separator_width)
        top = row_idx * (cell_height + separator_width)
        right = left + cell_width
        bottom = top + cell_height

        # Ensure we don't exceed image bounds
        right = min(right, img_width)
        bottom = min(bottom, img_height)

        # Crop the panel
        cropped = pil_image.crop((left, top, right, bottom))

        panel_width, panel_height = cropped.size
        print(f"Extracted panel {panel.upper()}: row={row_idx}, col={col_idx}, size={panel_width}x{panel_height}")

        return (pil2tensor(cropped), panel.upper(), panel_width, panel_height)


NODE_CLASS_MAPPINGS = {
    "ExtractGridPanel": ExtractGridPanel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExtractGridPanel": "⏹️ Extract Grid Panel (nhk)",
}
