"""
Edit with Krita Node - Linux workspace-based integration
Saves image to workspace/editing/, launches Krita, waits for edits, reimports
"""

import torch
import numpy as np
from PIL import Image
import os
import time
import subprocess
from pathlib import Path
from comfy.model_management import throw_exception_if_processing_interrupted

# Hack: string type that is always equal in not equal comparisons
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any = AnyType("*")

class EditWithKrita:
    def __init__(self):
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "timeout": ("INT", {
                    "default": 300,
                    "min": 10,
                    "max": 3600,
                    "step": 10,
                    "display": "number",
                    "tooltip": "Maximum time to wait for edits (seconds)"
                }),
            },
            "optional": {
                "enabled": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Enable/disable editing - when disabled, image passes through unchanged"
                }),
                "edit_directory": ("STRING", {
                    "default": "/home/nhk/workspace/editing",
                    "tooltip": "Directory where images are saved for editing"
                }),
                "notify": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Show desktop notification when ready to edit"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "edit_image"
    CATEGORY = "nhk/image"
    OUTPUT_NODE = True

    def edit_image(self, image, timeout, enabled=True, edit_directory="/home/nhk/workspace/editing", notify=True):
        """
        Main editing workflow:
        1. Save image to edit directory
        2. Launch Krita (or wait if already open)
        3. Monitor file for changes
        4. Reload and return edited image
        """

        # Pass through if disabled
        if not enabled:
            return (image,)

        # Handle batch of images
        output_images = []
        batch_size = image.shape[0]

        for i in range(batch_size):
            single_image = image[i:i+1]
            edited = self._edit_single_image(single_image, timeout, edit_directory, notify)
            output_images.append(edited)

        # Concatenate all edited images back into batch
        return (torch.cat(output_images, dim=0),)

    def _edit_single_image(self, image, timeout, edit_directory, notify):
        """Edit a single image"""

        # Ensure edit directory exists
        edit_dir = Path(edit_directory).expanduser()
        edit_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = int(time.time() * 1000)
        filename = f"comfy_edit_{timestamp}.png"
        filepath = edit_dir / filename

        # Save image to disk
        self._save_image(image, filepath)
        print(f"[Edit with Krita] Saved image to: {filepath}")

        # Get initial modification time
        initial_mtime = os.path.getmtime(filepath)

        # Launch Krita with the image
        self._launch_krita(filepath, notify)

        # Wait for file to be modified
        print(f"[Edit with Krita] Waiting for edits (timeout: {timeout}s)...")
        if self._wait_for_modification(filepath, initial_mtime, timeout):
            print(f"[Edit with Krita] Changes detected, reloading image...")
        else:
            print(f"[Edit with Krita] Timeout reached, using original image")

        # Load the (possibly edited) image
        edited_image = self._load_image(filepath)

        # Optional: Clean up temp file after a short delay
        # (keeping it for now so user can reference it)

        return edited_image

    def _save_image(self, image_tensor, filepath):
        """Convert tensor to PIL and save"""
        # Convert from torch tensor (B,H,W,C) float32 [0,1] to numpy uint8 [0,255]
        i = 255. * image_tensor.cpu().numpy()
        img_array = np.clip(i[0], 0, 255).astype(np.uint8)

        # Save as PNG
        Image.fromarray(img_array).save(filepath, format='PNG')

    def _load_image(self, filepath):
        """Load image from disk and convert to tensor"""
        img = Image.open(filepath).convert("RGB")
        img_array = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(img_array)[None,]  # Add batch dimension

    def _launch_krita(self, filepath, notify):
        """Launch Krita with the image file"""

        # Try multiple methods to launch Krita
        krita_commands = [
            ['/home/nhk/Applications/krita-5.2.13-x86_64.AppImage', str(filepath)],  # AppImage
            ['krita', str(filepath)],           # System PATH
            ['flatpak', 'run', 'org.kde.krita', str(filepath)],  # Flatpak
            ['xdg-open', str(filepath)],        # Default image handler
        ]

        launched = False
        for cmd in krita_commands:
            try:
                # Launch in background, don't wait for it to exit
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True  # Detach from parent process
                )
                print(f"[Edit with Krita] Launched: {' '.join(cmd)}")
                launched = True
                break
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

        if not launched:
            print(f"[Edit with Krita] Warning: Could not launch Krita automatically.")
            print(f"[Edit with Krita] Please open manually: {filepath}")

        # Show desktop notification if enabled
        if notify:
            self._show_notification(filepath)

    def _show_notification(self, filepath):
        """Show desktop notification using notify-send"""
        try:
            subprocess.run([
                'notify-send',
                '--icon=krita',
                '--urgency=normal',
                'ComfyUI: Edit with Krita',
                f'Image ready for editing:\n{filepath.name}\n\nSave the file when done to continue workflow.'
            ], timeout=2)
        except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            # Silently fail if notify-send not available
            pass

    def _wait_for_modification(self, filepath, initial_mtime, timeout):
        """
        Wait for file modification or timeout.
        Returns True if file was modified, False if timeout.
        """
        start_time = time.monotonic()
        check_interval = 0.5  # Check every 500ms

        while time.monotonic() - start_time < timeout:
            # Allow ComfyUI to interrupt if needed
            throw_exception_if_processing_interrupted()

            # Check if file has been modified
            try:
                current_mtime = os.path.getmtime(filepath)
                if current_mtime > initial_mtime:
                    # Give Krita time to finish writing
                    time.sleep(0.5)
                    return True
            except OSError:
                # File might be temporarily unavailable during save
                pass

            time.sleep(check_interval)

        return False


NODE_CLASS_MAPPINGS = {
    "EditWithKrita": EditWithKrita,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EditWithKrita": "🎨 Edit with Krita",
}
