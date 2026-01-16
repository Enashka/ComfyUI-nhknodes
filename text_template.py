"""
Text template engine with placeholder replacement using Python format strings.
Write templates like "The {a} walks in the {b}" and connect inputs to replace placeholders.
Uses Python str.format() syntax - see https://docs.python.org/3/library/string.html#format-string-syntax
Category: nhk/text
"""

class TextTemplate:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "default": "The {a} walks in the {b}",
                    "multiline": True,
                    "placeholder": "Template with placeholders {a} {b} {c}",
                    "tooltip": "Template text with {placeholder} syntax. Use {a:.2f} for formatting, {a:05d} for padding. Use {{ }} to write literal braces."
                }),
            },
            "optional": {
                "a": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for {a} placeholder"
                }),
                "b": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for {b} placeholder"
                }),
                "c": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for {c} placeholder"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process_template"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Text template engine with placeholder replacement using Python format strings"

    def process_template(self, template="", a="", b="", c=""):
        if not template:
            return ("",)

        # Use Python's str.format() to replace placeholders
        result = template.format(a=a, b=b, c=c)

        return (result,)

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "📝 Text Template (nhk)",
}