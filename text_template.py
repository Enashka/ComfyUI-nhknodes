"""
Text template engine with dynamic placeholder replacement.
Write templates like "The [text_1] walks in the [text_2]" and connect inputs to replace placeholders.
Category: nhk/text
"""

import re

class TextTemplate:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "default": "The [text_1] walks in the [text_2]",
                    "multiline": True,
                    "placeholder": "Enter template with placeholders like [text_1], [text_2], etc."
                }),
            },
            "optional": {},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process_template"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Text template engine with dynamic placeholder replacement"
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True
    
    def process_template(self, template="", **kwargs):
        if not template:
            return ("",)
        
        # Find all placeholders in the template like [text_1], [text_2], etc.
        placeholders = re.findall(r'\[([^]]+)\]', template)
        
        # Replace each placeholder with its corresponding input value
        result = template
        for placeholder in placeholders:
            if placeholder in kwargs and kwargs[placeholder]:
                # Replace all instances of [placeholder] with the input value
                result = result.replace(f'[{placeholder}]', str(kwargs[placeholder]))
            else:
                # If no input connected, leave placeholder as is or replace with empty
                result = result.replace(f'[{placeholder}]', f'[{placeholder}]')
        
        return (result,)

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "📝 Text Template (nhk)",
}