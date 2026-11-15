"""
Window extraction module for ASHIAN floor plan understanding system.
Detects windows and associates them with adjacent room regions.
"""

from typing import Dict, List
import cv2
import numpy as np

from src.config import MIN_WINDOW_AREA_PX, MAX_WINDOW_AREA_PX, ADJACENCY_DILATION_RADIUS


class WindowExtractor:
    """Extracts window instances and associates them with adjacent rooms."""

    def __init__(
        self,
        min_area_px: int = MIN_WINDOW_AREA_PX,
        max_area_px: int = MAX_WINDOW_AREA_PX,
        dilation_radius: int = ADJACENCY_DILATION_RADIUS
    ):
        self.min_area_px = min_area_px
        self.max_area_px = max_area_px
        self.dilation_radius = dilation_radius

    def extract_windows(
        self,
        window_binary_mask: np.ndarray,
        plan_id: int,
        labeled_room_mask: np.ndarray,
        rooms: List[Dict]
    ) -> List[Dict]:
        """
        Extract windows, spatial boundaries, and associated rooms.
        Returns a list of window dictionaries.
        """
        if window_binary_mask is None or np.count_nonzero(window_binary_mask) == 0:
            return []

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            window_binary_mask, connectivity=8
        )

        room_id_map = {r["room_index"]: r["room_id"] for r in rooms}
        room_obj_map = {r["room_id"]: r for r in rooms}

        windows = []
        window_counter = 1

        dilation_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (self.dilation_radius, self.dilation_radius)
        )

        for label_idx in range(1, num_labels):
            area = int(stats[label_idx, cv2.CC_STAT_AREA])
            if area < self.min_area_px or area > self.max_area_px:
                continue

            x = int(stats[label_idx, cv2.CC_STAT_LEFT])
            y = int(stats[label_idx, cv2.CC_STAT_TOP])
            w = int(stats[label_idx, cv2.CC_STAT_WIDTH])
            h = int(stats[label_idx, cv2.CC_STAT_HEIGHT])
            cx, cy = float(centroids[label_idx][0]), float(centroids[label_idx][1])

            window_id = plan_id * 1000 + window_counter

            # Identify adjacent rooms via spatial dilation
            single_window_mask = (labels == label_idx).astype(np.uint8) * 255
            dilated = cv2.dilate(single_window_mask, dilation_kernel, iterations=1)

            overlap_labels = np.unique(labeled_room_mask[dilated > 0])
            adjacent_room_indices = [int(lbl) for lbl in overlap_labels if lbl > 0]
            adjacent_room_ids = [room_id_map[lbl] for lbl in adjacent_room_indices if lbl in room_id_map]

            # Associate window with room objects
            for rid in adjacent_room_ids:
                if window_id not in room_obj_map[rid]["associated_windows"]:
                    room_obj_map[rid]["associated_windows"].append(window_id)

            windows.append({
                "window_id": window_id,
                "plan_id": plan_id,
                "window_index": window_counter,
                "area_pixels": area,
                "bbox_x": x,
                "bbox_y": y,
                "bbox_width": w,
                "bbox_height": h,
                "centroid_x": round(cx, 2),
                "centroid_y": round(cy, 2),
                "associated_rooms": adjacent_room_ids
            })

            window_counter += 1

        return windows
