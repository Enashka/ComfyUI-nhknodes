"""
Loads images from a directory in sequence, by index, or randomly.
Features:
- Two modes: single_image (by index), random (by seed)
- Use control_after_generate=increment for auto-advancing through sequence
- Reset capability to restart sequences
- Outputs current position and total count for tracking progress
- Label-based counter tracking for multiple independent sequences
Perfect for processing image sequences frame by frame.
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

class LoadImageSeries:
    """
    Loads images from a directory with two modes:
    - single_image: Load specific image by index (use control_after_generate=increment to auto-advance)
    - random: Load random image using seed

    Features:
    - reset: Set to True to reset counter to first image
    - Outputs current_index and total_images for progress tracking
    - label: Unique identifier for tracking separate sequences independently
    """

    # In-memory storage for counter per label (used with control_after_generate=increment)
    _counters = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["single_image", "random"], {
                    "tooltip": "single_image: load by index (use with control_after_generate=increment for sequences), random: load random image by seed"
                }),
                "path": ("STRING", {
                    "default": '',
                    "multiline": False,
                    "tooltip": "Directory path containing images to load"
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
                    "tooltip": "Seed for random mode (same seed = same random image)"
                }),
                "label": ("STRING", {
                    "default": 'Series001',
                    "multiline": False,
                    "tooltip": "Unique identifier for tracking this sequence independently from others"
                }),
                "reset": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Reset counter back to index 0"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "filename", "current_index", "total_images")
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = "nhk/image"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-run each execution so the counter can advance even if inputs stay the same
        return float("nan")

    def load_image(self, mode, path, pattern, index, seed, label, reset):
        # Reset counter if requested
        if reset:
            self._counters[label] = 0
            print(f"Series {label}: Counter reset to 0")

        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            return (torch.zeros(1, 512, 512, 3), "", 0, 0)

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
            return (torch.zeros(1, 512, 512, 3), "", 0, 0)

        total_images = len(image_paths)
        current_index = 0

        # Select image based on mode
        if mode == "single_image":
            # Get current counter for this label (increments when control_after_generate=increment)
            current_index = self._counters.get(label, index)

            # Wrap around if at end
            if current_index >= len(image_paths):
                current_index = 0

            selected_path = image_paths[current_index]

            # Increment counter for next time (used by control_after_generate)
            self._counters[label] = (current_index + 1) % len(image_paths)
            print(f"Series {label}: Loading image {current_index + 1}/{len(image_paths)}")

        else:  # random
            random.seed(seed)
            current_index = random.randint(0, len(image_paths) - 1)
            selected_path = image_paths[current_index]

        # Load and process image
        try:
            image = Image.open(selected_path)
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")

            filename = os.path.basename(selected_path)
            return (pil2tensor(image), filename, current_index, total_images)

        except Exception as e:
            print(f"Error loading image {selected_path}: {e}")
            return (torch.zeros(1, 512, 512, 3), "", 0, total_images)

# Register the node
NODE_CLASS_MAPPINGS = {
    "LoadImageSeries": LoadImageSeries,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageSeries": "📸 Load Image Series (nhk)",
}