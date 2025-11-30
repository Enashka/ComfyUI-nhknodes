"""
Advanced image loader with folder browsing and preview functionality.
Browse any folder, sort by multiple methods, and preview on hover.
Includes web API endpoints for dynamic folder listing and image serving.
Category: nhk
"""

import os
import glob
import folder_paths
from server import PromptServer
from aiohttp import web
from nodes import LoadImage

@PromptServer.instance.routes.post("/nhknodes/images")
async def get_nhk_images(request):
    body = await request.json()
    folder_path = body.get("folder_path", folder_paths.get_output_directory())
    sort_method = body.get("sort_method", "name_asc")

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return web.json_response({})

    # Get list of image files
    image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp", "*.tiff"]
    files = []
    for ext in image_extensions:
        files.extend(glob.glob(os.path.join(folder_path, ext)))
        files.extend(glob.glob(os.path.join(folder_path, ext.upper())))

    # Sort files based on method
    if sort_method == "name_asc":
        files.sort(key=lambda x: os.path.basename(x).lower())
    elif sort_method == "name_desc":
        files.sort(key=lambda x: os.path.basename(x).lower(), reverse=True)
    elif sort_method == "newest_first":
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    elif sort_method == "oldest_first":
        files.sort(key=lambda x: os.path.getmtime(x))
    elif sort_method == "recently_modified":
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    elif sort_method == "oldest_modified":
        files.sort(key=lambda x: os.path.getmtime(x))
    else:  # Default fallback
        files.sort(key=lambda x: os.path.basename(x).lower())

    images = {}
    for file_path in files:
        item_name = os.path.basename(file_path)
        images[item_name] = item_name  # Just use filename as key and value

    return web.json_response(images)

@PromptServer.instance.routes.get("/nhknodes/view")
async def view_nhk_image(request):
    folder_path = request.query.get("folder_path", folder_paths.get_output_directory())
    filename = request.query.get("filename")
    
    if not filename or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return web.Response(status=404)
        
    image_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(image_path) or not os.path.commonpath([folder_path, os.path.abspath(image_path)]) == folder_path:
        return web.Response(status=404)

    return web.FileResponse(image_path, headers={"Content-Disposition": f"filename=\"{filename}\""})

@PromptServer.instance.routes.get("/nhknodes/files")
async def get_nhk_files(request):
    folder_path = request.query.get("folder_path", folder_paths.get_output_directory())
    
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return web.json_response([])

    # Get list of image files
    image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"]
    files = []
    
    for file in os.listdir(folder_path):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            files.append(file)
    
    return web.json_response(sorted(files))

class ImageLoaderWithPreviews:
    @classmethod
    def INPUT_TYPES(s):
        output_dir = folder_paths.get_output_directory()
        return {
            "required": {
                "folder_path": ("STRING", {
                    "default": output_dir,
                    "multiline": False,
                    "tooltip": "Directory path containing images to load"
                }),
                "image": ("STRING", {
                    "default": "",
                    "tooltip": "Image filename (select from dropdown with preview on hover)"
                }),
                "sort_method": (["name_asc", "name_desc", "newest_first", "oldest_first", "recently_modified", "oldest_modified"], {
                    "default": "newest_first",
                    "tooltip": "Sorting method for image list"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "filename")
    FUNCTION = "load_image_with_previews"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Load an image with preview functionality from any folder. Select folder path and get image previews on hover."

    def load_image_with_previews(self, folder_path, image, sort_method):
        if not image or not image.strip():
            raise ValueError("No image selected")
            
        # Validate folder path exists
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise ValueError(f"Folder path does not exist: {folder_path}")
            
        # Construct the full image path
        image_path = os.path.join(folder_path, image)
        
        # Validate image file exists
        if not os.path.exists(image_path):
            raise ValueError(f"Image not found: {image_path}")
            
        # Validate image file is within the specified folder (security check)
        if not os.path.commonpath([folder_path, os.path.abspath(image_path)]) == folder_path:
            raise ValueError(f"Image path outside of specified folder: {image_path}")
            
        # Validate file is an image
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"]
        if not any(image.lower().endswith(ext) for ext in image_extensions):
            raise ValueError(f"File is not a supported image format: {image}")
        
        # Use the LoadImage functionality directly
        from PIL import Image, ImageOps, ImageSequence
        import node_helpers
        import numpy as np
        import torch
        
        img = node_helpers.pillow(Image.open, image_path)
        output_images = []
        output_masks = []
        
        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image_tensor = i.convert("RGB")
            image_tensor = np.array(image_tensor).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_tensor)[None,]
            
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            
            output_images.append(image_tensor)
            output_masks.append(mask.unsqueeze(0))
        
        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]
        
        # Add filename as third output
        filename = os.path.splitext(os.path.basename(image))[0]
        
        return (output_image, output_mask, filename)

NODE_CLASS_MAPPINGS = {
    "ImageLoaderWithPreviews": ImageLoaderWithPreviews,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageLoaderWithPreviews": "🖼️ Image Loader With Previews (nhk)",
}