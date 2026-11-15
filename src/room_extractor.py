"""
Room extraction module for ASHIAN floor plan understanding system.
Uses connected component analysis, contour detection, and moment computation.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np

from src.config import MIN_ROOM_AREA_PX


class RoomExtractor:
    """Extracts room instances from binary room masks."""

    def __init__(self, min_area_px: int = MIN_ROOM_AREA_PX):
        self.min_area_px = min_area_px

    def extract_rooms(
        self,
        room_binary_mask: np.ndarray,
        plan_id: int
    ) -> Tuple[List[Dict], np.ndarray]:
        """
        Extract room instances, bounding boxes, centroids, and pixel areas.
        Returns:
            rooms_list: List of dictionaries with extracted room attributes.
            labeled_mask: 2D array where each pixel contains the room index (0 for non-room).
        """
        if room_binary_mask is None or np.count_nonzero(room_binary_mask) == 0:
            return [], np.zeros((1, 1), dtype=np.int32)

        # Morphological close to bridge minor boundary gaps while maintaining separation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed_mask = cv2.morphologyEx(room_binary_mask, cv2.MORPH_CLOSE, kernel)

        # Connected component analysis with statistics
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            closed_mask, connectivity=8
        )

        rooms = []
        labeled_mask = np.zeros_like(labels, dtype=np.int32)
        room_counter = 1

        # Skip label 0 (background)
        for label_idx in range(1, num_labels):
            area = int(stats[label_idx, cv2.CC_STAT_AREA])
            if area < self.min_area_px:
                continue

            x = int(stats[label_idx, cv2.CC_STAT_LEFT])
            y = int(stats[label_idx, cv2.CC_STAT_TOP])
            w = int(stats[label_idx, cv2.CC_STAT_WIDTH])
            h = int(stats[label_idx, cv2.CC_STAT_HEIGHT])
            cx, cy = float(centroids[label_idx][0]), float(centroids[label_idx][1])

            # Generate unique global room ID
            room_id = plan_id * 1000 + room_counter
            labeled_mask[labels == label_idx] = room_counter

            # Extract contour for solidity calculation and polygonal boundary
            component_mask = (labels == label_idx).astype(np.uint8) * 255
            contours, _ = cv2.findContours(
                component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            solidity = 0.0
            polygon_pts = []
            if contours:
                c = max(contours, key=cv2.contourArea)
                hull = cv2.convexHull(c)
                hull_area = cv2.contourArea(hull)
                solidity = float(area / hull_area) if hull_area > 0 else 0.0

                # Approximate polygon with Douglas-Peucker for clean geometry
                epsilon = 0.01 * cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, epsilon, True)
                polygon_pts = approx.reshape(-1, 2).tolist()

            # Assign room category: without OCR/text or architectural ground truth labels,
            # we adhere strictly to the requirement: "Do not assign room names based only on visual guesses."
            # We record identifiable geometric classification.
            category = f"Room {room_counter}"

            # Extraction confidence based on component solidity and clear boundaries
            confidence = round(min(1.0, max(0.6, solidity)), 3)

            rooms.append({
                "room_id": room_id,
                "plan_id": plan_id,
                "room_index": room_counter,
                "category": category,
                "area_pixels": area,
                "bbox_x": x,
                "bbox_y": y,
                "bbox_width": w,
                "bbox_height": h,
                "centroid_x": round(cx, 2),
                "centroid_y": round(cy, 2),
                "solidity": round(solidity, 3),
                "confidence": confidence,
                "polygon": polygon_pts,
                "associated_doors": [],
                "associated_windows": []
            })

            room_counter += 1

        return rooms, labeled_mask
