"""
Controls workflow branching with interval-based on/off switching.
Enables connected path every Nth execution - perfect for conditional processing.
Use cases: upscale every 5th image, generate video every 10th output, etc.
Category: nhk/utility
"""

import threading

class AnyType(str):
    """Wildcard type that matches any input"""
    def __ne__(self, __value: object) -> bool:
        return False

anyType = AnyType("*")

class IntervalGate:
    """
    Enables a workflow path every Nth execution.
    Perfect for conditional processing like periodic upscaling or video generation.
    """
    
    def __init__(self):
        self.execution_count = 0
        self.lock = threading.Lock()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": (anyType, {"tooltip": "Input data to pass through"}),
                "interval": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Enable gate every N executions (e.g., 5 = every 5th execution)"
                }),
                "reset_counter": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Reset execution counter back to 0"
                }),
            }
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always trigger re-execution to count properly"""
        return float("NaN")
    
    RETURN_TYPES = (anyType, "BOOLEAN", "STRING", "INT")
    RETURN_NAMES = ("output", "gate_enabled", "status", "execution_count")
    FUNCTION = "execute"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Controls workflow branching with interval-based on/off switching"
    
    def execute(self, input, interval=5, reset_counter=False):
        with self.lock:
            # Handle reset
            if reset_counter:
                self.execution_count = 0
                print(f"IntervalGate: Counter reset to 0")
                return (input, False, f"Reset - Count: 0, Interval: {interval}", 0)
            
            # Increment counter
            self.execution_count += 1
            
            # Check if gate should be enabled (every Nth execution)
            gate_enabled = (self.execution_count % interval) == 0
            
            if gate_enabled:
                status = f"GATE ENABLED - Execution {self.execution_count} (every {interval})"
                print(f"IntervalGate: {status}")
            else:
                next_trigger = interval - (self.execution_count % interval)
                status = f"Gate disabled - Execution {self.execution_count}, next trigger in {next_trigger}"
                print(f"IntervalGate: {status}")
            
            return (input, gate_enabled, status, self.execution_count)

# Node registration
NODE_CLASS_MAPPINGS = {
    "IntervalGate": IntervalGate
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IntervalGate": "🚪 Interval Gate (nhk)"
}