"""
Mask analyzer module for ASHIAN floor plan understanding system.
Decomposes multi-modal semantic floor plan masks into class-specific binary masks.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np

from src.config import CLASS_COLOR_SIGNATURES, COLOR_TOLERANCE


class MaskAnalyzer:
    """Decomposes semantic floor plan masks into class-specific binary masks."""

    def __init__(self, color_tolerance: int = COLOR_TOLERANCE):
        self.color_tolerance = color_tolerance
        self.signatures = CLASS_COLOR_SIGNATURES

    def extract_binary_mask(
        self,
        mask_rgb: np.ndarray,
        class_name: str,
        tolerance: int = None
    ) -> np.ndarray:
        """
        Extract a clean binary mask (0 or 255 uint8) for a semantic class,
        supporting multiple color signatures per class.
        """
        if mask_rgb is None or class_name not in self.signatures:
            return np.zeros((1, 1), dtype=np.uint8)

        tol = tolerance if tolerance is not None else self.color_tolerance
        target_colors = self.signatures[class_name]

        combined = np.zeros(mask_rgb.shape[:2], dtype=np.uint8)
        mask_float = mask_rgb.astype(np.float32)

        for tgt in target_colors:
            target_np = np.array(tgt, dtype=np.float32)
            diff = mask_float - target_np
            dist = np.sqrt(np.sum(diff ** 2, axis=-1))
            matched = (dist <= tol).astype(np.uint8) * 255
            combined = cv2.bitwise_or(combined, matched)

        # Morphological clean up to remove single-pixel boundary noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

        return cleaned

    def extract_all_masks(self, mask_rgb: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract binary masks for all semantic classes (room, wall, door, window).
        """
        if mask_rgb is None:
            return {}

        results = {}
        for class_name in ["room", "wall", "door", "window", "background"]:
            results[class_name] = self.extract_binary_mask(mask_rgb, class_name)

        return results

    def get_class_statistics(self, mask_rgb: np.ndarray) -> Dict[str, int]:
        """
        Calculate total pixel count for each semantic class.
        """
        masks = self.extract_all_masks(mask_rgb)
        stats = {}
        for name, binary in masks.items():
            stats[f"{name}_pixels"] = int(np.count_nonzero(binary))
        return stats
