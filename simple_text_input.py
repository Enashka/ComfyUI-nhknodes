"""
Simple text input field that passes through text without any processing.
Perfect for entering text content that flows directly to other nodes.
Category: nhk/text
"""

class SimpleTextInput:
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {
                    "multiline": True,
                    "default": "Enter your text here... (nhk)",
                    "placeholder": "Type text or connect from another node"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "pass_through_text"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Simple text input field that passes through text without any processing"
    
    def pass_through_text(self, text_input):
        return (text_input,)

NODE_CLASS_MAPPINGS = {
    "SimpleTextInput": SimpleTextInput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleTextInput": "📝 Simple Text Input (nhk)",
}