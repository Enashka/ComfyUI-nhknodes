"""
Automatically cycles through unlimited connected inputs on each execution.
Perfect for testing multiple prompts, models, or parameters in sequence.
Features configurable stay count - stay on each input for N executions before switching.
Category: nhk/utility
"""

class AnyType(str):
    """Wildcard type that matches any input"""
    def __ne__(self, __value: object) -> bool:
        return False

anyType = AnyType("*")

class CyclingSwitch:
    """
    Cycles through unlimited connected inputs automatically with dynamic input support.
    Auto-resets to first input when cycle completes or input count changes.
    Supports staying on each input for a specified number of executions.
    """
    
    def __init__(self):
        self.current_index = 0
        self.last_input_count = 0
        self.execution_count_on_current_input = 0
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reset": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Reset cycle back to first input"
                }),
                "stay_count": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Number of executions to stay on each input before switching"
                }),
            },
            "optional": {},
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        # Accept dynamic inputs; validation handled at runtime
        return True
    
    RETURN_TYPES = (anyType, "STRING", "INT", "INT")
    RETURN_NAMES = ("output", "info", "current_index", "executions_on_input")
    FUNCTION = "execute"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Automatically cycles through unlimited connected inputs with configurable stay duration"
    
    def execute(self, reset=False, stay_count=1, **kwargs):
        # Collect all connected inputs (excluding reset and stay_count parameters)
        inputs = [
            value for key, value in kwargs.items() 
            if key not in ['reset', 'stay_count'] and value is not None
        ]
        
        input_count = len(inputs)
        
        # Handle case with no inputs
        if input_count == 0:
            return (None, "No inputs connected", 0, 0)
        
        # Reset if requested or input count changed
        if reset or input_count != self.last_input_count:
            self.current_index = 0
            self.last_input_count = input_count
            self.execution_count_on_current_input = 0
        
        # Ensure index is within bounds (in case inputs were removed)
        if self.current_index >= input_count:
            self.current_index = 0
            self.execution_count_on_current_input = 0
        
        # Increment execution count for current input
        self.execution_count_on_current_input += 1
        
        # Get current input
        selected_input = inputs[self.current_index]
        
        # Create info string
        info = f"Using input {self.current_index + 1} of {input_count}, execution {self.execution_count_on_current_input}/{stay_count}"
        
        # Check if we should advance to next input
        if self.execution_count_on_current_input >= stay_count:
            # Advance to next input for next execution
            self.current_index = (self.current_index + 1) % input_count
            self.execution_count_on_current_input = 0
        
        return (selected_input, info, self.current_index + 1, self.execution_count_on_current_input)

# Node registration
NODE_CLASS_MAPPINGS = {
    "CyclingSwitch": CyclingSwitch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CyclingSwitch": "🔄 Cycling Switch (nhk)"
}