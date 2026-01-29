"""
Extended text template engine with 8 placeholder inputs.
Write templates like "The [a] walks in the [b]" and connect inputs to replace placeholders.
Uses [a] through [h] syntax - works seamlessly with JSON templates.
Category: nhk/text
"""

class TextTemplateExtended:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "default": "The [a] walks in the [b]",
                    "multiline": True,
                    "placeholder": "Template with placeholders [a] [b] [c] [d] [e] [f] [g] [h]",
                    "tooltip": "Template text with [placeholder] syntax. Placeholders: [a] through [h]"
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
                "e": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [e] placeholder"
                }),
                "f": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [f] placeholder"
                }),
                "g": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [g] placeholder"
                }),
                "h": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "(optional) Value for [h] placeholder"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process_template"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Extended text template engine with 8 placeholder inputs"

    def process_template(self, template="", a="", b="", c="", d="", e="", f="", g="", h=""):
        if not template:
            return ("",)

        # Simple string replacement for [a] through [h]
        result = template
        for letter, value in [("a", a), ("b", b), ("c", c), ("d", d), ("e", e), ("f", f), ("g", g), ("h", h)]:
            result = result.replace(f"[{letter}]", value)

        return (result,)

NODE_CLASS_MAPPINGS = {
    "TextTemplateExtended": TextTemplateExtended,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplateExtended": "📝 Text Template Extended (nhk)",
}
