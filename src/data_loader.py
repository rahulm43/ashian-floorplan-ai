"""
Data loader module for ASHIAN floor plan understanding system.
Handles floor plan images, segmentation masks, and pair discovery.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from src.config import IMAGES_DIR, MASKS_DIR


def extract_plan_id(filename: str) -> Optional[int]:
    """Extract numeric plan ID from filename (e.g., '12.png' -> 12, '12 (2).png' -> 12)."""
    match = re.match(r"^(\d+)", filename)
    if match:
        return int(match.group(1))
    return None


class FloorPlanDataLoader:
    """Manages discovery and loading of floor plan images and segmentation masks."""

    def __init__(self, images_dir: Path = IMAGES_DIR, masks_dir: Path = MASKS_DIR):
        self.images_dir = Path(images_dir)
        self.masks_dir = Path(masks_dir)

    def discover_pairs(self) -> List[Dict]:
        """
        Scan images and masks directories and return all matched pairs.
        Returns a list of dictionaries with plan metadata.
        """
        if not self.images_dir.exists():
            return []

        image_files = sorted(
            [f for f in os.listdir(self.images_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))],
            key=lambda x: extract_plan_id(x) or 999999
        )
        mask_files = set(
            os.listdir(self.masks_dir) if self.masks_dir.exists() else []
        )

        pairs = []
        for img_name in image_files:
            plan_id = extract_plan_id(img_name)
            if plan_id is None:
                continue

            # Check potential mask naming conventions in Kaggle dataset
            possible_masks = [
                f"{plan_id} (2).png",
                f"{plan_id}_mask.png",
                f"{plan_id}.png"
            ]

            matched_mask = None
            for candidate in possible_masks:
                if candidate in mask_files:
                    matched_mask = candidate
                    break

            img_path = self.images_dir / img_name
            mask_path = self.masks_dir / matched_mask if matched_mask else None

            # Get dimensions safely
            width, height = 0, 0
            is_valid = False
            try:
                with Image.open(img_path) as pil_img:
                    width, height = pil_img.size
                    is_valid = True
            except Exception:
                pass

            pairs.append({
                "plan_id": plan_id,
                "image_filename": img_name,
                "image_path": str(img_path),
                "mask_filename": matched_mask,
                "mask_path": str(mask_path) if mask_path else None,
                "width": width,
                "height": height,
                "has_mask": mask_path is not None,
                "is_valid": is_valid
            })

        return pairs

    def load_pair(self, plan_id: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Dict]:
        """
        Load original image (RGB) and mask (RGB) for a given plan ID.
        """
        pairs = self.discover_pairs()
        plan_meta = next((p for p in pairs if p["plan_id"] == plan_id), None)

        if not plan_meta:
            return None, None, {"error": f"Plan {plan_id} not found."}

        # Load original image
        img_bgr = cv2.imread(plan_meta["image_path"])
        if img_bgr is None:
            return None, None, {"error": f"Failed to read image for plan {plan_id}."}
        image_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # Load mask if present
        mask_rgb = None
        if plan_meta["mask_path"] and os.path.exists(plan_meta["mask_path"]):
            mask_bgr = cv2.imread(plan_meta["mask_path"])
            if mask_bgr is not None:
                mask_rgb = cv2.cvtColor(mask_bgr, cv2.COLOR_BGR2RGB)

        return image_rgb, mask_rgb, plan_meta
