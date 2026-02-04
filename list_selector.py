"""
Selects a value from a list or uses a default input.
Index 0 = use default, 1+ = pick from list (1-indexed).
Batch mode outputs the entire list.
Category: nhk/utility
"""


class ListSelector:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "list": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Newline-separated list of values"
                }),
                "index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1,
                    "tooltip": "0 = use default input, 1+ = select from list (1-indexed)"
                }),
                "batch": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If true, output entire list (ignores index)"
                }),
            },
            "optional": {
                "default": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "Value to use when index is 0"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    FUNCTION = "select"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Select from list by index, use default, or batch entire list"
    OUTPUT_IS_LIST = (True,)

    def select(self, list, index, batch, default=""):
        # Parse list into items
        items = [line.strip() for line in list.split('\n') if line.strip()]

        if batch:
            # Return entire list
            if not items:
                return ([default] if default else [""],)
            return (items,)

        if index == 0:
            # Use default input
            return ([default],)
        else:
            # Pick from list (1-indexed)
            list_index = index - 1
            if list_index < len(items):
                return ([items[list_index]],)
            else:
                # Out of range - return last item or default
                return ([items[-1]] if items else [default],)


NODE_CLASS_MAPPINGS = {
    "ListSelector": ListSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ListSelector": "📋 List Selector (nhk)",
}
