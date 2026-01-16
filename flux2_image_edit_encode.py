# Flux2 Image Edit Encode
# Simplified text+image encoding for Flux2 Klein image editing workflows.
# Consolidates CLIPTextEncode + VAEEncode + ReferenceLatent chain into one node.

import math
import torch
import comfy.utils
import node_helpers


class TextEncodeFlux2ImageEdit:
    """
    Simplified encoding node for Flux2 Klein image editing.
    Combines prompt encoding with reference image latent attachment.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            },
            "optional": {
                "vae": ("VAE",),
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "image3": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "encode"
    CATEGORY = "nhk/conditioning"

    DESCRIPTION = "Encodes prompt and reference images for Flux2 Klein image editing. Returns both positive (with prompt) and negative (zeroed) conditioning with reference latents attached."

    def encode(self, clip, prompt, vae=None, image1=None, image2=None, image3=None):
        # Encode the prompt
        tokens = clip.tokenize(prompt)
        positive_cond = clip.encode_from_tokens_scheduled(tokens)

        # Create zeroed conditioning for negative
        negative_cond = clip.encode_from_tokens_scheduled(tokens)
        # Zero out the conditioning
        negative_cond = self._zero_out_conditioning(negative_cond)

        # Process reference images if VAE provided
        if vae is not None:
            images = [image1, image2, image3]
            ref_latents = []

            for image in images:
                if image is not None:
                    latent = self._encode_reference_image(image, vae)
                    ref_latents.append(latent)

            # Attach reference latents to both conditionings
            if len(ref_latents) > 0:
                positive_cond = node_helpers.conditioning_set_values(
                    positive_cond, {"reference_latents": ref_latents}, append=True
                )
                negative_cond = node_helpers.conditioning_set_values(
                    negative_cond, {"reference_latents": ref_latents}, append=True
                )

        return (positive_cond, negative_cond)

    def _encode_reference_image(self, image, vae):
        """Scale image to ~1MP and encode with VAE."""
        samples = image.movedim(-1, 1)
        total = int(1024 * 1024)  # Target ~1 megapixel

        scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
        width = round(samples.shape[3] * scale_by / 8.0) * 8
        height = round(samples.shape[2] * scale_by / 8.0) * 8

        s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
        return vae.encode(s.movedim(1, -1)[:, :, :, :3])

    def _zero_out_conditioning(self, conditioning):
        """Zero out the conditioning tensors."""
        out = []
        for c in conditioning:
            # c is a tuple of (tensor, dict)
            pooled_output = c[1].get("pooled_output", None)
            cond_dict = c[1].copy()
            if pooled_output is not None:
                cond_dict["pooled_output"] = torch.zeros_like(pooled_output)
            out.append((torch.zeros_like(c[0]), cond_dict))
        return out


NODE_CLASS_MAPPINGS = {
    "TextEncodeFlux2ImageEdit": TextEncodeFlux2ImageEdit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextEncodeFlux2ImageEdit": "Text Encode Flux2 Image Edit (nhk)",
}
