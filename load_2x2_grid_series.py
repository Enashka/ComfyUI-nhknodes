"""
Loads images from a directory and splits each 2x2 grid into individual images.
Each source image is treated as a 2x2 grid and extracted in order:
upper-left → upper-right → bottom-left → bottom-right → next file.

Features:
- Two modes: single_image (by index), random (by seed)
- Use control_after_generate=increment for auto-advancing through grid positions
- Reset capability to restart sequences
- Outputs current position (global across all grids) and total count
- Label-based counter tracking for multiple independent sequences

Perfect for processing grid-based image sequences.
Category: nhk/image
"""

import os
import glob
import random
import torch
import numpy as np
from PIL import Image, ImageOps

# Convert PIL to tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

class Load2x2GridSeries:
    """
    Loads images from a directory, treating each as a 2x2 grid.
    Extracts grid cells in order: upper-left, upper-right, bottom-left, bottom-right.

    Two modes:
    - single_image: Load specific grid cell by index (use control_after_generate=increment to auto-advance)
    - random: Load random grid cell using seed

    Features:
    - reset: Set to True to reset counter to first grid cell
    - Outputs current_index and total_images (total grid cells across all files)
    - label: Unique identifier for tracking separate sequences independently
    """

    # In-memory storage for counter per label (used with control_after_generate=increment)
    _counters = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["single_image", "random"], {
                    "tooltip": "single_image: load by index (use with control_after_generate=increment for sequences), random: load random grid cell by seed"
                }),
                "path": ("STRING", {
                    "default": '',
                    "multiline": False,
                    "tooltip": "Directory path containing grid images to load"
                }),
                "pattern": ("STRING", {
                    "default": '*',
                    "multiline": False,
                    "tooltip": "Glob pattern to filter files (e.g., '*.png', 'img_*.jpg', '**/*.png' for recursive)"
                }),
                "index": ("INT", {
                    "default": 0,
                    "tooltip": "Starting index for single_image mode (auto-increments with control_after_generate)"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "tooltip": "Seed for random mode (same seed = same random grid cell)"
                }),
                "label": ("STRING", {
                    "default": 'Grid2x2_001',
                    "multiline": False,
                    "tooltip": "Unique identifier for tracking this sequence independently from others"
                }),
                "reset": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Reset counter back to index 0"
                }),
                "separator_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "tooltip": "Width of separator lines between grid cells (in pixels). Excludes this many pixels from center cross."
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("image", "filename", "current_index", "total_images", "grid_position", "position_name")
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = "nhk/image"

    def load_image(self, mode, path, pattern, index, seed, label, reset, separator_width):
        # Reset counter if requested
        if reset:
            self._counters[label] = 0
            print(f"Grid Series {label}: Counter reset to 0")

        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            return (torch.zeros(1, 512, 512, 3), "", 0, 0, 0, "none")

        # Get all image files
        image_paths = []
        allowed_extensions = ('.jpeg', '.jpg', '.png', '.tiff', '.gif', '.bmp', '.webp')

        for file_name in glob.glob(os.path.join(glob.escape(path), pattern), recursive=True):
            if file_name.lower().endswith(allowed_extensions):
                abs_file_path = os.path.abspath(file_name)
                image_paths.append(abs_file_path)

        image_paths.sort()

        if not image_paths:
            print(f"No valid images found in {path} with pattern {pattern}")
            return (torch.zeros(1, 512, 512, 3), "", 0, 0, 0, "none")

        # Each image contains 4 grid cells (2x2)
        total_grid_cells = len(image_paths) * 4
        current_index = 0

        # Select grid cell based on mode
        if mode == "single_image":
            # Get current counter for this label (increments when control_after_generate=increment)
            current_index = self._counters.get(label, index)

            # Wrap around if at end
            if current_index >= total_grid_cells:
                current_index = 0

            # Increment counter for next time (used by control_after_generate)
            self._counters[label] = (current_index + 1) % total_grid_cells
            print(f"Grid Series {label}: Loading grid cell {current_index + 1}/{total_grid_cells}")

        else:  # random
            random.seed(seed)
            current_index = random.randint(0, total_grid_cells - 1)

        # Calculate which file and which grid position
        file_index = current_index // 4
        grid_position = current_index % 4  # 0=upper-left, 1=upper-right, 2=bottom-left, 3=bottom-right

        position_names = ["upper-left", "upper-right", "bottom-left", "bottom-right"]
        position_name = position_names[grid_position]

        selected_path = image_paths[file_index]

        # Load and process image
        try:
            image = Image.open(selected_path)
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")

            # Get dimensions and split into 2x2 grid
            width, height = image.size
            half_width = width // 2
            half_height = height // 2

            # Calculate separator offsets (half on each side of center)
            # For separator_width=1: exclude center pixel
            # For separator_width=2: exclude 1 pixel on each side of center
            h_offset = separator_width // 2 + (separator_width % 2)  # Offset from center horizontal
            v_offset = separator_width // 2 + (separator_width % 2)  # Offset from center vertical

            # Extract the appropriate quadrant based on grid_position
            # Adjust crop boxes to exclude separator pixels
            if grid_position == 0:  # upper-left
                crop_box = (0, 0, half_width - h_offset, half_height - v_offset)
            elif grid_position == 1:  # upper-right
                crop_box = (half_width + (separator_width - h_offset), 0, width, half_height - v_offset)
            elif grid_position == 2:  # bottom-left
                crop_box = (0, half_height + (separator_width - v_offset), half_width - h_offset, height)
            else:  # grid_position == 3, bottom-right
                crop_box = (half_width + (separator_width - h_offset), half_height + (separator_width - v_offset), width, height)

            cropped_image = image.crop(crop_box)

            filename = os.path.basename(selected_path)

            print(f"  File: {filename}, Position: {position_name} ({grid_position+1}/4)")

            return (pil2tensor(cropped_image), filename, current_index, total_grid_cells, grid_position, position_name)

        except Exception as e:
            print(f"Error loading image {selected_path}: {e}")
            return (torch.zeros(1, 512, 512, 3), "", 0, total_grid_cells, 0, "error")

# Register the node
NODE_CLASS_MAPPINGS = {
    "Load2x2GridSeries": Load2x2GridSeries,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Load2x2GridSeries": "🔲 Load 2x2 Grid Series (nhk)",
}
