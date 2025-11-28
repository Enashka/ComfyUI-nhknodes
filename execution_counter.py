"""
Counts workflow executions and stops queue when target is reached.
Perfect for batch processing - generate exactly N images then stop.
Thread-safe with automatic queue halting via exception handling.
Category: nhk
"""

import time
import threading

class AnyType(str):
    """Wildcard type that matches any input"""
    def __ne__(self, __value: object) -> bool:
        return False

anyType = AnyType("*")

class ExecutionCounter:
    """
    Counts executions and stops queue when target is reached.
    Perfect for batch processing large numbers of workflows.
    """
    
    def __init__(self):
        self.current_count = 0
        self.target_count = 0
        self.should_stop = False
        self.lock = threading.Lock()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": (anyType, {}),
                "target_count": ("INT", {
                    "default": 100,
                    "min": 1,
                    "max": 10000,
                    "step": 1,
                    "tooltip": "Stop queue after this many executions"
                }),
                "reset_counter": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Reset counter back to 0"
                }),
            }
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always trigger re-execution to count properly"""
        return float("NaN")
    
    RETURN_TYPES = (anyType, "STRING", "INT", "BOOLEAN")
    RETURN_NAMES = ("output", "status", "current_count", "should_stop")
    FUNCTION = "execute"
    CATEGORY = "nhk/utility"
    DESCRIPTION = "Counts workflow executions and stops queue when target is reached"
    
    def execute(self, input, target_count=100, reset_counter=False):
        with self.lock:
            # Handle reset
            if reset_counter:
                self.current_count = 0
                self.should_stop = False
                self.target_count = target_count
                print(f"ExecutionCounter: Reset to 0, target set to {target_count}")
                return (input, f"Reset - Count: 0/{target_count}", 0, False)
            
            # Update target if changed
            if self.target_count != target_count:
                self.target_count = target_count
                print(f"ExecutionCounter: Target updated to {target_count}")
            
            # Increment counter
            self.current_count += 1
            
            # Check if we should stop
            if self.current_count > self.target_count:
                # HARD STOP - Raise exception to halt workflow
                error_msg = f"ExecutionCounter: TARGET REACHED! Completed {self.current_count-1}/{self.target_count} executions. Stopping workflow."
                print(error_msg)
                raise RuntimeError(error_msg)
            
            elif self.current_count == self.target_count:
                self.should_stop = True
                status = f"FINAL RUN - Count: {self.current_count}/{self.target_count} - WILL STOP AFTER THIS"
                print(f"ExecutionCounter: {status}")
            else:
                self.should_stop = False
                status = f"Running - Count: {self.current_count}/{self.target_count}"
                print(f"ExecutionCounter: {status}")
            
            return (input, status, self.current_count, self.should_stop)
    
    def _stop_queue(self):
        """Attempt to stop the ComfyUI queue"""
        try:
            # This would need ComfyUI's server reference
            # For now, just log that we reached the target
            print("ExecutionCounter: Target reached - Queue should be stopped manually")
            
            # Alternative approach: raise an exception to halt execution
            if self.should_stop:
                # This will cause the workflow to fail and stop processing
                # Users can then clear the queue manually
                pass
                
        except Exception as e:
            print(f"ExecutionCounter: Error in stop mechanism: {e}")

# Node registration
NODE_CLASS_MAPPINGS = {
    "ExecutionCounter": ExecutionCounter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExecutionCounter": "⏱️ Execution Counter (nhk)"
}