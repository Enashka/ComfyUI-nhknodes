"""
Text template engine with placeholder replacement using bracket syntax.
Write templates like "The [a] walks in the [b]" and connect inputs to replace placeholders.
Uses [a] [b] [c] [d] syntax - works seamlessly with JSON templates.
Category: nhk/text
"""

class TextTemplate:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "default": "The [a] walks in the [b]",
                    "multiline": True,
                    "placeholder": "Template with placeholders [a] [b] [c] [d]",
                    "tooltip": "Template text with [placeholder] syntax. Placeholders: [a] [b] [c] [d]"
                }),
            },
            "optional": {
                "a": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [a] placeholder"
                }),
                "b": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [b] placeholder"
                }),
                "c": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [c] placeholder"
                }),
                "d": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [d] placeholder"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process_template"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Text template engine with placeholder replacement using bracket syntax"

    def process_template(self, template="", a="", b="", c="", d=""):
        if not template:
            return ("",)

        # Simple string replacement for [a], [b], [c], [d]
        result = template.replace("[a]", a).replace("[b]", b).replace("[c]", c).replace("[d]", d)

        return (result,)

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "📝 Text Template (nhk)",
}
