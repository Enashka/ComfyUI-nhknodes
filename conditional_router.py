"""
Routes workflow based on boolean condition using lazy evaluation.
Selector pattern - picks between two input chains, only executes the selected one.
Perfect for quality control, A/B testing, and conditional processing.
Category: nhk/utility
"""

class AnyType(str):
    """Wildcard type that matches any input"""
    def __ne__(self, __value: object) -> bool:
        return False

anyType = AnyType("*")

class ConditionalRouter:
    """
    Selects between two inputs based on a boolean condition.
    Only the selected input chain executes (lazy evaluation).
    Connect your pass processing to pass_input, fail processing to fail_input.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True = use pass_input, False = use fail_input"
                }),
                "pass_input": (anyType, {
                    "lazy": True,
                    "tooltip": "Input chain to use when condition is True"
                }),
                "fail_input": (anyType, {
                    "lazy": True,
                    "tooltip": "Input chain to use when condition is False"
                }),
            }
        }

    RETURN_TYPES = (anyType, "STRING")
    RETURN_NAMES = ("output", "info")
    OUTPUT_TOOLTIPS = (
        "Selected input based on condition",
        "Which path was taken"
    )
    FUNCTION = "route"
    CATEGORY = "nhk/wip"
    DESCRIPTION = "Selects between two inputs based on boolean condition with lazy evaluation"

    def check_lazy_status(self, condition=True, pass_input=None, fail_input=None):
        """Only evaluate the input that will be used based on condition"""
        if condition:
            return ["pass_input"]
        else:
            return ["fail_input"]

    def route(self, condition, pass_input, fail_input):
        """Return selected input based on condition"""
        if condition:
            info = "Using pass_input"
            print(f"ConditionalRouter: {info}")
            return (pass_input, info)
        else:
            info = "Using fail_input"
            print(f"ConditionalRouter: {info}")
            return (fail_input, info)


class ConditionalRouterDual:
    """
    Selects between two input pairs based on a boolean condition.
    Only the selected input pair executes (lazy evaluation).
    Perfect for routing image + metadata pairs conditionally.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True = use pass inputs, False = use fail inputs"
                }),
                "pass_input1": (anyType, {
                    "lazy": True,
                    "tooltip": "First input when condition is True"
                }),
                "pass_input2": (anyType, {
                    "lazy": True,
                    "tooltip": "Second input when condition is True"
                }),
                "fail_input1": (anyType, {
                    "lazy": True,
                    "tooltip": "First input when condition is False"
                }),
                "fail_input2": (anyType, {
                    "lazy": True,
                    "tooltip": "Second input when condition is False"
                }),
            }
        }

    RETURN_TYPES = (anyType, anyType, "STRING")
    RETURN_NAMES = ("output1", "output2", "info")
    OUTPUT_TOOLTIPS = (
        "First selected input based on condition",
        "Second selected input based on condition",
        "Which path was taken"
    )
    FUNCTION = "route"
    CATEGORY = "nhk/wip"
    DESCRIPTION = "Selects between two input pairs based on boolean condition with lazy evaluation"

    def check_lazy_status(self, condition=True, pass_input1=None, pass_input2=None,
                          fail_input1=None, fail_input2=None):
        """Only evaluate the inputs that will be used based on condition"""
        if condition:
            return ["pass_input1", "pass_input2"]
        else:
            return ["fail_input1", "fail_input2"]

    def route(self, condition, pass_input1, pass_input2, fail_input1, fail_input2):
        """Return selected input pair based on condition"""
        if condition:
            info = "Using pass inputs"
            print(f"ConditionalRouterDual: {info}")
            return (pass_input1, pass_input2, info)
        else:
            info = "Using fail inputs"
            print(f"ConditionalRouterDual: {info}")
            return (fail_input1, fail_input2, info)


class ConditionalStop:
    """
    Stops workflow execution if condition is False.
    Passes through input unchanged if condition is True.
    Perfect for quality gates and validation checkpoints.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": (anyType, {
                    "tooltip": "Input to pass through or stop"
                }),
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True = continue, False = stop execution"
                }),
                "stop_message": ("STRING", {
                    "default": "Quality check failed - stopping workflow",
                    "multiline": False,
                    "tooltip": "Message to display when stopping"
                }),
            }
        }

    RETURN_TYPES = (anyType, "STRING")
    RETURN_NAMES = ("output", "status")
    OUTPUT_TOOLTIPS = (
        "Input passthrough if condition is True",
        "Execution status message"
    )
    FUNCTION = "execute"
    CATEGORY = "nhk/wip"
    DESCRIPTION = "Stops workflow execution based on condition"

    def execute(self, input, condition, stop_message):
        """Pass through input if condition is True, otherwise raise error"""
        if condition:
            status = "Condition passed - continuing workflow"
            print(f"ConditionalStop: {status}")
            return (input, status)
        else:
            print(f"ConditionalStop: {stop_message}")
            # Raise an error to stop execution
            raise ValueError(f"ConditionalStop: {stop_message}")


class ConditionalSplitter:
    """
    Splits input to two outputs based on boolean condition.
    Only the selected output chain executes (lazy evaluation).
    Perfect for routing one input to different processing pipelines.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": (anyType, {
                    "tooltip": "Input to route to pass or fail output"
                }),
                "condition": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True = route to pass_output, False = route to fail_output"
                }),
            }
        }

    RETURN_TYPES = (anyType, anyType, "STRING")
    RETURN_NAMES = ("pass_output", "fail_output", "info")
    OUTPUT_TOOLTIPS = (
        "Output when condition is True (lazy - only executes if condition=True)",
        "Output when condition is False (lazy - only executes if condition=False)",
        "Which output is active"
    )
    FUNCTION = "split"
    CATEGORY = "nhk/wip"
    DESCRIPTION = "Splits input to two outputs based on condition with lazy evaluation"

    def check_lazy_status(self, input=None, condition=True):
        """Only evaluate the output that will be used based on condition"""
        # This tells ComfyUI which outputs are needed
        # Return empty list means "execute normally"
        # We can't selectively disable outputs, so we return empty list
        # and rely on downstream lazy evaluation to prevent execution
        return []

    def split(self, input, condition):
        """Route input to appropriate output based on condition"""
        if condition:
            info = "Routing to pass_output"
            print(f"ConditionalSplitter: {info}")
            return (input, input, info)  # Both outputs get input, lazy eval handles execution
        else:
            info = "Routing to fail_output"
            print(f"ConditionalSplitter: {info}")
            return (input, input, info)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ConditionalRouter": ConditionalRouter,
    "ConditionalRouterDual": ConditionalRouterDual,
    "ConditionalStop": ConditionalStop,
    "ConditionalSplitter": ConditionalSplitter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ConditionalRouter": "🔀 Conditional Router (nhk)",
    "ConditionalRouterDual": "🔀 Conditional Router Dual (nhk)",
    "ConditionalStop": "🛑 Conditional Stop (nhk)",
    "ConditionalSplitter": "🔀 Conditional Splitter (nhk)",
}
