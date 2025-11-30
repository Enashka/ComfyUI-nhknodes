"""
Combines unlimited text inputs into a single output with dynamic inputs.
Perfect for merging multiple text sources with customizable separators.
Category: nhk/text
"""

class TextCombiner:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "separator": ("STRING", {
                    "default": "\\n",
                    "placeholder": "Enter separator (\\n for line break, --- for divider, etc.)",
                    "tooltip": "Separator between combined texts (\\n=newline, \\t=tab)"
                }),
            },
            "optional": {},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("combined_text",)
    FUNCTION = "combine_texts"
    CATEGORY = "nhk/text"
    DESCRIPTION = "Combines unlimited text inputs into a single output with dynamic inputs"
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True
    
    def combine_texts(self, separator="\\n", **kwargs):
        actual_separator = separator.replace("\\n", "\n").replace("\\t", "\t")
        
        texts = []
        for key, value in kwargs.items():
            if key.startswith("text") and isinstance(value, str) and value.strip():
                texts.append(value.strip())
        
        if texts:
            combined = actual_separator.join(texts)
            return (combined,)
        else:
            return ("",)

NODE_CLASS_MAPPINGS = {
    "TextCombiner": TextCombiner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextCombiner": "📝 Text Combiner (nhk)",
}