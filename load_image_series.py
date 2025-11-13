"""
Loads images from a directory in sequence, by index, or randomly.
Features:
- Three modes: single_image (by index), incremental_image (auto-advance), random (by seed)
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
    Loads images from a directory with three modes:
    - single_image: Load specific image by index
    - incremental_image: Load next image in sequence (auto-advances each execution)
    - random: Load random image using seed

    Features:
    - reset: Set to True to reset incremental counter to first image
    - Outputs current_index and total_images for progress tracking
    - label: Unique identifier for tracking separate sequences independently
    """

    # In-memory storage for incremental counter per label
    _counters = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["single_image", "incremental_image", "random"],),
                "path": ("STRING", {"default": '', "multiline": False}),
                "pattern": ("STRING", {"default": '*', "multiline": False}),
                "index": ("INT", {"default": 0}),
                "seed": ("INT", {"default": 0}),
                "label": ("STRING", {"default": 'Series001', "multiline": False}),
                "reset": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "filename", "current_index", "total_images")
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = "nhk/image"

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
            if index < 0 or index >= len(image_paths):
                print(f"Invalid image index {index}. Found {len(image_paths)} images.")
                return (torch.zeros(1, 512, 512, 3), "", 0, total_images)
            selected_path = image_paths[index]
            current_index = index

        elif mode == "incremental_image":
            # Get current counter for this label
            current_index = self._counters.get(label, 0)

            # Wrap around if at end
            if current_index >= len(image_paths):
                current_index = 0

            selected_path = image_paths[current_index]

            # Increment counter for next time
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
    "LoadImageSeries": "📸 Load Image Series",
}