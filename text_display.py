"""
Interactive text viewer with UI display and pass-through functionality.
Perfect for visualizing outputs, debugging workflows, and monitoring text content.
Includes pass-through output for chaining nodes together.
Category: nhk
"""

class TextDisplay:
    """
    Display text content in the UI while passing it through unchanged.
    Useful for debugging workflows and monitoring text as it flows through nodes.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "display_text"
    OUTPUT_NODE = True
    CATEGORY = "nhk/text"
    DESCRIPTION = "Interactive text viewer with UI display and pass-through functionality"

    def display_text(self, text):
        """Display text in UI and pass it through for chaining"""
        return {"ui": {"text": (text,)}, "result": (text,)}

NODE_CLASS_MAPPINGS = {
    "TextDisplay": TextDisplay,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextDisplay": "📄 Text Display (nhk)",
}