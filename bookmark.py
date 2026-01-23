"""
Canvas bookmark for quick navigation.
Place anywhere on canvas and press the shortcut key to jump to it.
Double-click the node to navigate to it.
Category: nhk/utility
"""

class Bookmark:
    """
    Virtual node for canvas navigation.
    No execution - purely frontend functionality.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "shortcut_key": ("STRING", {
                    "default": "1",
                    "tooltip": "Keyboard shortcut to jump to this bookmark (e.g. '1', 'ctrl+2', 'alt+shift+3')"
                }),
                "zoom": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.5,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "Zoom level when navigating to bookmark"
                }),
                "anchor": (["upper-left", "upper-right"], {
                    "default": "upper-left",
                    "tooltip": "Where to position the bookmark node in viewport"
                }),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "bookmark"
    CATEGORY = "nhk/utility"
    OUTPUT_NODE = True
    DESCRIPTION = "Canvas bookmark with keyboard shortcut navigation (double-click or press shortcut to jump)"

    def bookmark(self, shortcut_key="1", zoom=1.0, anchor="upper-left"):
        """
        Virtual node - no actual execution.
        Navigation is handled by JavaScript frontend.
        """
        return ()


NODE_CLASS_MAPPINGS = {
    "Bookmark": Bookmark
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Bookmark": "🔖 Bookmark (nhk)",
}
