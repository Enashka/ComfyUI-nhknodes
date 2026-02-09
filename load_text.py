"""
Load text files with auto-incrementing index and folder scanning.
Perfect companion to SaveText node for cycling through saved content.
Supports auto-increment, wrap-around, and flexible file patterns. Category: nhk/text
"""

import os
import glob
import re
from pathlib import Path

class LoadText:

    def __init__(self):
        self.last_index = {}  # Store last index per unique configuration
        self.repeat_counter = {}  # Store repeat counter per unique configuration

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "Folder path (empty = ComfyUI output folder)",
                    "tooltip": "Target directory to scan for text files"
                }),
                "base_filename": ("STRING", {
                    "multiline": False,
                    "default": "saved_text",
                    "placeholder": "Base filename to match",
                    "tooltip": "Base name pattern to match against files"
                }),
                "file_extension": (["txt", "md"], {"default": "txt"}),
                "counter_format": ("STRING", {
                    "multiline": False,
                    "default": "_{counter:03d}",
                    "placeholder": "Counter format: _{counter:03d} matches _001, _002, etc.",
                    "tooltip": "Format string for numeric counter pattern"
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Automatically advance to next file on each execution"
                }),
            },
            "optional": {
                "set_to": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "tooltip": "Set to specific index (0 = continue from last, >0 = jump to that index)"
                }),
                "repeat_count": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Load same file this many times before advancing to next"
                }),
                "wrap_around": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Return to first file after reaching the last one"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("text_content", "loaded_filepath", "available_count", "current_filename", "repeat_status")
    FUNCTION = "load_text"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Load text files with auto-incrementing index and folder scanning"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always trigger re-execution to handle repeat counting properly"""
        return float("NaN")

    def _get_folder_path(self, folder_path):
        """Get the actual folder path to scan"""
        if folder_path and folder_path.strip():
            return Path(folder_path.strip())
        else:
            # Use ComfyUI output directory
            try:
                import folder_paths
                return Path(folder_paths.output_directory)
            except ImportError:
                return Path("output")

    def _create_config_key(self, folder_path, base_filename, counter_format, file_extension):
        """Create unique key for this configuration to track auto-increment state"""
        return f"{folder_path}|{base_filename}|{counter_format}|{file_extension}"

    def _scan_matching_files(self, folder_path, base_filename, counter_format, file_extension):
        """Scan folder for files matching the pattern and return sorted list with indices"""

        if not folder_path.exists():
            print(f"LoadText: Folder does not exist: {folder_path}")
            return {}

        # Convert counter format to regex pattern
        # Handle different counter format variations
        if "{counter:03d}" in counter_format:
            counter_pattern = counter_format.replace("{counter:03d}", r"(\d{3})")
        elif "{counter:02d}" in counter_format:
            counter_pattern = counter_format.replace("{counter:02d}", r"(\d{2})")
        elif "{counter:01d}" in counter_format:
            counter_pattern = counter_format.replace("{counter:01d}", r"(\d{1})")
        elif "{counter:d}" in counter_format:
            counter_pattern = counter_format.replace("{counter:d}", r"(\d+)")
        elif "{counter}" in counter_format:
            counter_pattern = counter_format.replace("{counter}", r"(\d+)")
        else:
            # Fallback - assume simple numeric pattern
            counter_pattern = counter_format + r"(\d+)" if counter_format else r"(\d+)"

        # Create full regex pattern
        search_pattern = f"{re.escape(base_filename)}{counter_pattern}\\.{file_extension}"

        # Find all matching files
        file_index_map = {}  # index -> filepath

        try:
            for file_path in folder_path.glob(f"{base_filename}*{file_extension}"):
                match = re.match(search_pattern, file_path.name)
                if match:
                    try:
                        index = int(match.group(1))
                        file_index_map[index] = file_path
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            print(f"LoadText: Error scanning files: {e}")

        return file_index_map

    def load_text(self, folder_path, base_filename, file_extension, counter_format,
                  auto_increment=True, set_to=0, repeat_count=1, wrap_around=True):
        """Load text file with auto-incrementing functionality"""

        # Get folder path
        folder = self._get_folder_path(folder_path)

        # Create configuration key for auto-increment tracking
        config_key = self._create_config_key(str(folder), base_filename, counter_format, file_extension)

        # Handle set_to override
        if set_to > 0:
            self.last_index[config_key] = set_to
            self.repeat_counter[config_key] = 0  # Reset repeat counter
            print(f"LoadText: Set to index {set_to}")

        # Scan for available files
        file_map = self._scan_matching_files(folder, base_filename, counter_format, file_extension)
        available_count = len(file_map)

        if available_count == 0:
            print(f"LoadText: No matching files found in {folder}")
            return ("", "", 0, "", "0/0")

        # Determine which index to load
        if auto_increment:
            # Get or initialize tracking for this configuration
            if config_key not in self.last_index:
                # Find first available index if no set_to specified
                if set_to == 0 and file_map:
                    self.last_index[config_key] = min(file_map.keys())
                else:
                    self.last_index[config_key] = set_to if set_to > 0 else 1
                print(f"LoadText: NEW CONFIG {config_key} - initialized last_index to {self.last_index[config_key]}")
            if config_key not in self.repeat_counter:
                self.repeat_counter[config_key] = 0
                print(f"LoadText: NEW CONFIG {config_key} - initialized repeat_counter to 0")

            print(f"LoadText: BEFORE - repeat_counter={self.repeat_counter[config_key]}, last_index={self.last_index[config_key]}")

            # Increment repeat counter first
            self.repeat_counter[config_key] += 1

            # Current target is the last_index we're on
            target_index = self.last_index[config_key]

            # Check if we need to advance to next file AFTER this execution
            if self.repeat_counter[config_key] >= repeat_count:
                # Reset repeat counter and advance to next index for NEXT execution
                old_index = self.last_index[config_key]
                self.repeat_counter[config_key] = 0
                self.last_index[config_key] += 1
                print(f"LoadText: ADVANCING - repeat limit reached, moving from index {old_index} to {self.last_index[config_key]} for next execution")

            print(f"LoadText: AFTER - repeat_counter={self.repeat_counter[config_key]}, target_index={target_index}")

            # Handle wrap-around
            if target_index not in file_map:
                if wrap_around and file_map:
                    # Find the minimum available index
                    min_index = min(file_map.keys())
                    target_index = min_index
                    self.last_index[config_key] = min_index
                    self.repeat_counter[config_key] = 1  # Set to 1 since we're about to load this file
                    print(f"LoadText: Wrapped around to index {min_index}")
                else:
                    # No wrap-around, try to find the highest available index
                    if file_map:
                        max_index = max(file_map.keys())
                        target_index = max_index
                        self.last_index[config_key] = max_index
                        print(f"LoadText: Reached end, staying at index {max_index}")
                    else:
                        return ("", "", available_count, "", "0/0")
        else:
            # Manual index mode - use set_to directly
            target_index = set_to if set_to > 0 else 1

        # Load the target file
        if target_index in file_map:
            target_file = file_map[target_index]
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Create repeat status string
                repeat_status = f"{self.repeat_counter[config_key]}/{repeat_count}" if auto_increment else "1/1"
                repeat_info = f" (repeat {repeat_status})" if auto_increment and repeat_count > 1 else ""
                print(f"LoadText: Loaded {target_file.name} (index {target_index}){repeat_info}")
                return (content, str(target_file), available_count, target_file.name, repeat_status)

            except Exception as e:
                repeat_status = f"{self.repeat_counter[config_key]}/{repeat_count}" if auto_increment else "1/1"
                print(f"LoadText: Error reading {target_file}: {e}")
                return ("", str(target_file), available_count, target_file.name, repeat_status)
        else:
            repeat_status = "0/0" if auto_increment else "1/1"
            print(f"LoadText: File with index {target_index} not found")
            return ("", "", available_count, f"index_{target_index}_not_found", repeat_status)

# Node registration
NODE_CLASS_MAPPINGS = {
    "LoadText": LoadText
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadText": "📂 Load Text (nhk)"
}
