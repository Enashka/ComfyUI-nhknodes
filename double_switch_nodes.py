"""
Universal switch with two pairs of inputs (A1/A2 and B1/B2).
Boolean selector chooses between outputting A pair or B pair.
Uses lazy evaluation for efficiency - only processes the selected inputs.
Category: nhk
"""

class AnyType(str):
    """Wildcard type that matches any input"""
    def __ne__(self, __value: object) -> bool:
        return False

anyType = AnyType("*")

class DoubleSwitch:
    """
    Universal double switch with two sets of inputs (A1, A2 and B1, B2).
    Selector chooses between outputting the A pair or B pair.
    Works with any data type using lazy evaluation for efficiency.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selector": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True = output A inputs, False = output B inputs"
                }),
                "A1": (anyType, {"lazy": True, "tooltip": "First input of A pair"}),
                "A2": (anyType, {"lazy": True, "tooltip": "Second input of A pair"}),
                "B1": (anyType, {"lazy": True, "tooltip": "First input of B pair"}),
                "B2": (anyType, {"lazy": True, "tooltip": "Second input of B pair"}),
            }
        }
    
    RETURN_TYPES = (anyType, anyType)
    RETURN_NAMES = ("output1", "output2")
    FUNCTION = "execute"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Universal switch with two pairs of inputs (A1/A2 and B1/B2)"
    
    def check_lazy_status(self, selector=True, A1=None, A2=None, B1=None, B2=None):
        """Only evaluate the inputs that will be used based on selector"""
        if selector:
            return ["A1", "A2"]
        else:
            return ["B1", "B2"]
    
    def execute(self, selector, A1, A2, B1, B2):
        """Return either A pair or B pair based on selector"""
        if selector:
            return (A1, A2)
        else:
            return (B1, B2)

class DoubleSwitchOut:
    """
    Double switch output that takes one double input and switches between 
    two different double outputs (A1/A2 or B1/B2) based on selector.
    Works with any data type using lazy evaluation for efficiency.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selector": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True = output to A outputs, False = output to B outputs"
                }),
                "input1": (anyType, {"tooltip": "First input to route"}),
                "input2": (anyType, {"tooltip": "Second input to route"}),
            }
        }
    
    RETURN_TYPES = (anyType, anyType, anyType, anyType)
    RETURN_NAMES = ("A1", "A2", "B1", "B2")
    FUNCTION = "execute"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Takes one double input and switches between two different double outputs"
    
    def execute(self, selector, input1, input2):
        """Route double input to either A outputs or B outputs based on selector"""
        if selector:
            # Output to A pair, B pair gets None
            return (input1, input2, None, None)
        else:
            # Output to B pair, A pair gets None
            return (None, None, input1, input2)

# Node registration
NODE_CLASS_MAPPINGS = {
    "DoubleSwitch": DoubleSwitch,
    "DoubleSwitchOut": DoubleSwitchOut,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DoubleSwitch": "🔀 Double Switch - In (nhk)",
    "DoubleSwitchOut": "🔀 Double Switch - Out (nhk)",
}