"""
Wall extraction module for ASHIAN floor plan understanding system.
Extracts structural wall regions, pixel area, bounding boxes, and segments.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np

from src.config import MIN_WALL_AREA_PX


class WallExtractor:
    """Extracts wall regions and spatial boundaries."""

    def __init__(self, min_area_px: int = MIN_WALL_AREA_PX):
        self.min_area_px = min_area_px

    def extract_walls(
        self,
        wall_binary_mask: np.ndarray,
        plan_id: int
    ) -> Tuple[Dict, List[Dict]]:
        """
        Extract wall segments and aggregate wall metrics.
        Returns:
            wall_summary: Aggregated metrics (total wall area, segment count).
            wall_segments: List of wall segment dictionaries.
        """
        if wall_binary_mask is None or np.count_nonzero(wall_binary_mask) == 0:
            return {"plan_id": plan_id, "total_wall_pixels": 0, "segment_count": 0}, []

        total_pixels = int(np.count_nonzero(wall_binary_mask))

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            wall_binary_mask, connectivity=8
        )

        segments = []
        segment_counter = 1

        for label_idx in range(1, num_labels):
            area = int(stats[label_idx, cv2.CC_STAT_AREA])
            if area < self.min_area_px:
                continue

            x = int(stats[label_idx, cv2.CC_STAT_LEFT])
            y = int(stats[label_idx, cv2.CC_STAT_TOP])
            w = int(stats[label_idx, cv2.CC_STAT_WIDTH])
            h = int(stats[label_idx, cv2.CC_STAT_HEIGHT])
            cx, cy = float(centroids[label_idx][0]), float(centroids[label_idx][1])

            segments.append({
                "wall_id": plan_id * 1000 + segment_counter,
                "plan_id": plan_id,
                "area_pixels": area,
                "bbox_x": x,
                "bbox_y": y,
                "bbox_width": w,
                "bbox_height": h,
                "centroid_x": round(cx, 2),
                "centroid_y": round(cy, 2)
            })
            segment_counter += 1

        summary = {
            "plan_id": plan_id,
            "total_wall_pixels": total_pixels,
            "segment_count": len(segments)
        }

        return summary, segments
