"""
Combines unlimited images into a single batch tensor with dynamic inputs.
Perfect for batch processing multiple images simultaneously.
Auto-adds input slots as you connect images - no more 6-image limit.
Category: nhk
"""

import torch

class ImageGridBatch:
    """
    Creates a batch from a dynamic number of input images.
    Simply combines multiple images into a single batch tensor.
    Output displays as separate images in batch rather than a composite.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # Frontend JS dynamically adds IMAGE inputs; keep declarations empty
        return {
            "required": {},
            "optional": {},
        }
    
    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("batch", "batch_count")
    FUNCTION = "create_batch"
    CATEGORY = "nhk/image"
    DESCRIPTION = "Combines unlimited images into a single batch tensor with dynamic inputs"
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        # Accept dynamic inputs; validation handled at runtime
        return True
    
    def create_batch(self, **kwargs):
        # Collect all connected IMAGE tensors regardless of input names
        images = [
            value for value in kwargs.values() if isinstance(value, torch.Tensor)
        ]
        
        if not images:
            # Return empty batch if no inputs
            return (torch.empty((0, 0, 0, 3), dtype=torch.float32), 0)
        
        # Simply concatenate all images into a single batch
        batch_tensor = torch.cat(images, dim=0)
        
        return (batch_tensor, len(images))

# Node registration
NODE_CLASS_MAPPINGS = {
    "ImageGridBatch": ImageGridBatch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageGridBatch": "📦 Image Grid Batch (nhk)"
}