"""
Load images from a folder and attach per-image prompts from a markdown lookup.

Prompt file format (markdown):
# Shot Prompts

shot_01.png
Close-up, soft light on subject

shot_02.png
Wide shot, dramatic shadows

- Blank lines separate entries
- First non-empty line in an entry is the filename
- Remaining lines in the entry are the prompt
- Optional wildcard entry: "*" as filename applies to any image not listed

Category: nhk/image
"""

import glob
import os
import random
from typing import Dict, Tuple

import numpy as np
import torch
from PIL import Image, ImageOps


def pil2tensor(image: Image.Image) -> torch.Tensor:
    """Convert a PIL image to a normalized tensor."""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class LoadImageSeriesWithPrompts:
    """
    Loads images from a directory with two modes (single_image or random) and
    attaches prompts from a markdown lookup file.

    Features:
    - reset: Set to True to reset counter to first image
    - label: Unique identifier for tracking separate sequences independently
    - default_prompt input is used when no file-specific prompt exists
    """

    _counters: Dict[str, int] = {}

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
                "prompt_file": ("STRING", {
                    "default": '',
                    "multiline": False,
                    "tooltip": "Markdown file mapping filenames to prompts (optional)"
                }),
                "default_prompt": ("STRING", {
                    "default": '',
                    "multiline": True,
                    "tooltip": "Fallback prompt when no file-specific prompt exists"
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
                    "default": 'SeriesWithPrompts001',
                    "multiline": False,
                    "tooltip": "Unique identifier for tracking this sequence independently from others"
                }),
                "reset": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Reset counter back to index 0"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "prompt", "filename", "current_index", "total_images")
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = "nhk/image"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-run each execution so the counter can advance even if inputs stay the same
        return float("nan")

    def _load_prompt_map(self, prompt_file: str) -> Tuple[Dict[str, str], str]:
        """
        Returns a mapping of filename (lowercase) -> prompt and an optional wildcard prompt.
        Wildcard entry uses "*" as filename.
        """
        if not prompt_file or not os.path.exists(prompt_file):
            return {}, ""

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Could not read prompt file {prompt_file}: {e}")
            return {}, ""

        prompt_map: Dict[str, str] = {}
        wildcard_prompt = ""

        # Split by blank lines to get entries
        for section in content.split("\n\n"):
            lines = [line.strip() for line in section.splitlines() if line.strip()]
            if len(lines) < 2:
                continue

            filename = lines[0]
            prompt_text = "\n".join(lines[1:]).strip()
            if not prompt_text:
                continue

            if filename == "*":
                wildcard_prompt = prompt_text
            else:
                prompt_map[filename.lower()] = prompt_text

        return prompt_map, wildcard_prompt

    def _select_image(self, mode: str, image_paths, index: int, seed: int, label: str):
        """Selects an image path and updates counters based on the mode."""
        if mode == "single_image":
            current_index = self._counters.get(label, index)
            if current_index >= len(image_paths):
                current_index = 0
            selected_path = image_paths[current_index]
            self._counters[label] = (current_index + 1) % len(image_paths)
        else:
            random.seed(seed)
            current_index = random.randint(0, len(image_paths) - 1)
            selected_path = image_paths[current_index]

        return selected_path, current_index

    def load_image(self, mode, path, pattern, prompt_file, default_prompt, index, seed, label, reset):
        if reset:
            self._counters[label] = 0
            print(f"Series {label}: Counter reset to 0")

        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            return (torch.zeros(1, 512, 512, 3), default_prompt, "", 0, 0)

        image_paths = []
        allowed_extensions = ('.jpeg', '.jpg', '.png', '.tiff', '.gif', '.bmp', '.webp')

        for file_name in glob.glob(os.path.join(glob.escape(path), pattern), recursive=True):
            if file_name.lower().endswith(allowed_extensions):
                image_paths.append(os.path.abspath(file_name))

        image_paths.sort()

        if not image_paths:
            print(f"No valid images found in {path} with pattern {pattern}")
            return (torch.zeros(1, 512, 512, 3), default_prompt, "", 0, 0)

        total_images = len(image_paths)
        selected_path, current_index = self._select_image(mode, image_paths, index, seed, label)
        filename = os.path.basename(selected_path)
        print(f"Series {label}: Loading image {current_index + 1}/{total_images}: {filename}")

        try:
            image = Image.open(selected_path)
            image = ImageOps.exif_transpose(image).convert("RGB")
            prompt_map, wildcard_prompt = self._load_prompt_map(prompt_file)

            if prompt_file and not prompt_map and not wildcard_prompt:
                print(f"No prompts loaded from {prompt_file}. Check path and markdown formatting.")

            prompt = prompt_map.get(filename.lower(), wildcard_prompt or default_prompt)
            return (pil2tensor(image), prompt, filename, current_index, total_images)
        except Exception as e:
            print(f"Error loading image {selected_path}: {e}")
            return (torch.zeros(1, 512, 512, 3), default_prompt, "", current_index, total_images)


NODE_CLASS_MAPPINGS = {
    "LoadImageSeriesWithPrompts": LoadImageSeriesWithPrompts,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageSeriesWithPrompts": "📁 Image Series With Prompts (nhk)",
}
