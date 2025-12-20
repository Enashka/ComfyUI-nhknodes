"""
AI-powered image quality evaluation using Qwen3VL vision model.
Analyzes images against custom criteria and outputs pass/fail decisions with confidence scores.
Perfect for quality control, automated filtering, and conditional workflow routing.
Category: nhk/ai
"""

import time
import random
import requests
import json
import base64
import tempfile
import os
import re
from PIL import Image
import torch
import numpy as np

class ImageEvaluator:
    """
    Evaluates images using Qwen3VL vision model.
    Returns boolean pass/fail, confidence score, and detailed reasoning.
    Designed for workflow branching and quality control.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Image to evaluate"
                }),
                "evaluation_criteria": ("STRING", {
                    "multiline": True,
                    "default": "Is this image high quality, sharp, and well-composed?",
                    "placeholder": "Describe what makes a good image...",
                    "tooltip": "Criteria for evaluation - be specific about what you want"
                }),
                "confidence_threshold": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider",
                    "tooltip": "Minimum confidence score to pass (0.0-1.0)"
                }),
                "model": ([
                    "qwen3-vl:8b",
                    "llama3.2-vision:11b",
                ], {
                    "default": "qwen3-vl:8b",
                    "tooltip": "Vision model to use for evaluation"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider",
                    "tooltip": "Lower = more consistent, higher = more varied judgments"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "BOOLEAN", "FLOAT", "STRING", "STRING")
    RETURN_NAMES = ("image", "passed", "confidence", "reasoning", "info")
    OUTPUT_TOOLTIPS = (
        "Original image passthrough",
        "True if meets criteria AND confidence ≥ threshold",
        "AI confidence score (0.0-1.0)",
        "AI's detailed explanation of judgment",
        "Summary: model, threshold, result"
    )
    FUNCTION = "evaluate"
    CATEGORY = "nhk/ai"
    DESCRIPTION = "AI-powered image evaluation with confidence scoring for workflow control"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution every time"""
        return f"image_eval_{time.time()}_{random.randint(1000, 9999)}"

    def tensor_to_pil(self, tensor):
        """Convert ComfyUI tensor to PIL Image"""
        if len(tensor.shape) == 4:
            tensor = tensor[0]
        i = 255. * tensor.cpu().numpy().squeeze()
        img = Image.fromarray(i.astype('uint8'))
        return img

    def extract_confidence_score(self, text):
        """
        Extract confidence score from AI response.
        Looks for patterns like: "confidence: 0.85", "8/10", "85%", etc.
        """
        text_lower = text.lower()

        # Pattern 1: "confidence: 0.85" or "confidence score: 85"
        confidence_match = re.search(r'confidence[:\s]+(?:score[:\s]+)?([0-9.]+)', text_lower)
        if confidence_match:
            score = float(confidence_match.group(1))
            # Normalize to 0-1 range if needed
            if score > 1.0:
                score = score / 100.0
            return min(max(score, 0.0), 1.0)

        # Pattern 2: "8/10", "7 out of 10"
        rating_match = re.search(r'(\d+)\s*(?:/|out of)\s*(\d+)', text_lower)
        if rating_match:
            numerator = float(rating_match.group(1))
            denominator = float(rating_match.group(2))
            return min(max(numerator / denominator, 0.0), 1.0)

        # Pattern 3: "85%"
        percent_match = re.search(r'(\d+)%', text_lower)
        if percent_match:
            return min(max(float(percent_match.group(1)) / 100.0, 0.0), 1.0)

        # Pattern 4: Look for quality keywords and assign scores
        if any(word in text_lower for word in ['excellent', 'outstanding', 'perfect']):
            return 0.95
        elif any(word in text_lower for word in ['good', 'high quality', 'well']):
            return 0.80
        elif any(word in text_lower for word in ['acceptable', 'decent', 'okay']):
            return 0.60
        elif any(word in text_lower for word in ['poor', 'bad', 'low quality']):
            return 0.30

        # Default: neutral score
        return 0.5

    def determine_pass_fail(self, text):
        """
        Determine if the evaluation is pass or fail based on response text.
        Returns boolean.
        """
        text_lower = text.lower()

        # Explicit yes/no
        if re.search(r'\byes\b', text_lower):
            return True
        if re.search(r'\bno\b', text_lower):
            return False

        # Pass/fail keywords
        pass_keywords = ['pass', 'good', 'high quality', 'excellent', 'sharp', 'well-composed', 'acceptable']
        fail_keywords = ['fail', 'poor', 'bad', 'low quality', 'blurry', 'poorly composed', 'unacceptable']

        pass_count = sum(1 for keyword in pass_keywords if keyword in text_lower)
        fail_count = sum(1 for keyword in fail_keywords if keyword in text_lower)

        if pass_count > fail_count:
            return True
        elif fail_count > pass_count:
            return False

        # Default to True (benefit of the doubt)
        return True

    def evaluate(self, image, evaluation_criteria, confidence_threshold=0.7, model="qwen3-vl:8b", temperature=0.3):
        """Evaluate image using Qwen3VL and return pass/fail decision"""

        if not evaluation_criteria or not evaluation_criteria.strip():
            error_msg = "Error: Evaluation criteria cannot be empty"
            return (image, False, 0.0, error_msg, error_msg)

        try:
            # Convert tensor to PIL Image
            pil_image = self.tensor_to_pil(image)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                pil_image.save(tmp_file.name, 'JPEG', quality=95)
                temp_path = tmp_file.name

            try:
                # Encode image to base64
                with open(temp_path, 'rb') as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                # Craft evaluation prompt
                system_prompt = """You are an expert image quality evaluator. Analyze images carefully and provide:
1. A clear YES or NO answer to the evaluation criteria
2. A confidence score (0.0 to 1.0 or percentage)
3. Brief reasoning for your judgment

Format your response clearly with these three elements."""

                user_prompt = f"""Evaluation criteria: {evaluation_criteria.strip()}

Analyze this image and respond with:
1. Answer: YES or NO
2. Confidence: [your confidence score 0.0-1.0]
3. Reasoning: [brief explanation]"""

                # Prepare API payload
                payload = {
                    "model": model,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "images": [img_base64],
                    "options": {
                        "temperature": temperature,
                        "num_predict": 300,
                    }
                }

                # Call Ollama API
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=120
                )

                response.raise_for_status()
                result = response.json()

                # Extract response text
                response_text = result.get("response", "").strip()

                if not response_text:
                    error_msg = "Error: Empty response from Ollama"
                    return (image, False, 0.0, error_msg, error_msg)

                # Parse response
                confidence_score = self.extract_confidence_score(response_text)
                initial_judgment = self.determine_pass_fail(response_text)

                # Final decision: both AI judgment AND confidence threshold must pass
                passed = initial_judgment and (confidence_score >= confidence_threshold)

                # Create info string
                info = f"Model: {model} | Confidence: {confidence_score:.2f} | Threshold: {confidence_threshold:.2f} | {'PASSED' if passed else 'FAILED'}"

                print(f"ImageEvaluator: {info}")
                print(f"ImageEvaluator: Reasoning: {response_text[:200]}...")

                return (image, passed, confidence_score, response_text, info)

            finally:
                # Clean up temporary file
                os.unlink(temp_path)

        except requests.exceptions.ConnectionError:
            error_msg = "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
            return (image, False, 0.0, error_msg, error_msg)
        except requests.exceptions.Timeout:
            error_msg = "Error: Ollama request timed out"
            return (image, False, 0.0, error_msg, error_msg)
        except Exception as e:
            error_msg = f"Error during evaluation: {str(e)}"
            return (image, False, 0.0, error_msg, error_msg)

NODE_CLASS_MAPPINGS = {
    "ImageEvaluator": ImageEvaluator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageEvaluator": "🔍 Image Evaluator (nhk)",
}
