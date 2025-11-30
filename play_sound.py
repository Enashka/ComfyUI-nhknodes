# Hack: string type that is always equal in not equal comparisons
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


# Our any instance wants to be a wildcard string
any = AnyType("*")


class PlaySound:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "any": (any, {"tooltip": "Pass-through input (any type)"}),
            "mode": (["always", "on empty queue"], {
                "tooltip": "When to play sound: always or only when queue is empty"
            }),
            "volume": ("FLOAT", {
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.5,
                "tooltip": "Sound volume (0.0 to 1.0)"
            }),
            "file": ("STRING", {
                "default": "notify.mp3",
                "tooltip": "Path to sound file to play"
            })
        }}

    FUNCTION = "nop"
    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True,)
    OUTPUT_NODE = True
    RETURN_TYPES = (any,)

    CATEGORY = "nhk/utility"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def nop(self, any, mode, volume, file):
        return {"ui": {"a": []}, "result": (any,)}


NODE_CLASS_MAPPINGS = {
    "PlaySound": PlaySound,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PlaySound": "🔊 Play Sound (nhk)",
}