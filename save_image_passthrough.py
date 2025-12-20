"""
Save image with passthrough output for conditional routing.
Saves images to disk AND returns the image for further processing.
Perfect for use with ConditionalRouter and lazy evaluation.
Category: nhk/image
"""

import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import folder_paths
import comfy.utils

class SaveImagePassthrough:
    """
    Saves images to disk and returns them for further processing.
    Unlike standard SaveImage, this node has IMAGE output for routing.
    """

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {
                    "forceInput": True,
                    "tooltip": "Images to save"
                }),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "Prefix for saved filenames"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "saved_path")
    OUTPUT_TOOLTIPS = (
        "Image passthrough for further processing",
        "Path where image was saved"
    )
    FUNCTION = "save_images"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Save images and pass them through for conditional routing"

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        """Save images and return them for further processing"""

        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        results = []
        saved_paths = []

        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = None
            if prompt is not None or extra_pnginfo is not None:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            filepath = os.path.join(full_output_folder, file)

            img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            saved_paths.append(filepath)
            counter += 1

        saved_path_str = saved_paths[0] if saved_paths else ""

        return {
            "ui": {"images": results},
            "result": (images, saved_path_str)
        }


class PreviewImagePassthrough:
    """
    Preview image in UI and return it for further processing.
    Unlike standard PreviewImage, this node has IMAGE output for routing.
    """

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + ''.join(np.random.choice(list('abcdefghijklmnopqrstupvxyz'), 5))
        self.compress_level = 1

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {
                    "forceInput": True,
                    "tooltip": "Images to preview"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_TOOLTIPS = ("Image passthrough for further processing",)
    FUNCTION = "preview_images"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Preview images and pass them through for conditional routing"

    def preview_images(self, images, prompt=None, extra_pnginfo=None):
        """Preview images and return them for further processing"""

        filename_prefix = "Preview"
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        results = []

        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            filepath = os.path.join(full_output_folder, file)

            img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return {
            "ui": {"images": results},
            "result": (images,)
        }


# Node registration
NODE_CLASS_MAPPINGS = {
    "SaveImagePassthrough": SaveImagePassthrough,
    "PreviewImagePassthrough": PreviewImagePassthrough,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImagePassthrough": "💾 Save Image + (nhk)",
    "PreviewImagePassthrough": "👁️ Preview Image + (nhk)",
}
