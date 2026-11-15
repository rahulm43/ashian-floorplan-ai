"""
Door extraction and room connectivity module for ASHIAN floor plan system.
Detects doors, computes spatial attributes, and determines inter-room connections.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np

from src.config import MIN_DOOR_AREA_PX, MAX_DOOR_AREA_PX, ADJACENCY_DILATION_RADIUS


class DoorExtractor:
    """Extracts door instances and associates doors with adjacent rooms."""

    def __init__(
        self,
        min_area_px: int = MIN_DOOR_AREA_PX,
        max_area_px: int = MAX_DOOR_AREA_PX,
        dilation_radius: int = ADJACENCY_DILATION_RADIUS
    ):
        self.min_area_px = min_area_px
        self.max_area_px = max_area_px
        self.dilation_radius = dilation_radius

    def extract_doors(
        self,
        door_binary_mask: np.ndarray,
        plan_id: int,
        labeled_room_mask: np.ndarray,
        rooms: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract doors and determine connections between rooms.
        Returns:
            doors_list: List of door dictionaries.
            connections_list: List of room connection dictionaries.
        """
        if door_binary_mask is None or np.count_nonzero(door_binary_mask) == 0:
            return [], []

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            door_binary_mask, connectivity=8
        )

        # Lookup from room_index (1..N) to room_id
        room_id_map = {r["room_index"]: r["room_id"] for r in rooms}
        room_obj_map = {r["room_id"]: r for r in rooms}

        doors = []
        connections = []
        connection_pairs_seen = set()
        door_counter = 1

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

            door_id = plan_id * 1000 + door_counter

            # Identify adjacent rooms using spatial dilation overlap
            single_door_mask = (labels == label_idx).astype(np.uint8) * 255
            dilated = cv2.dilate(single_door_mask, dilation_kernel, iterations=1)

            # Find overlapping room indices in the labeled room mask
            overlap_labels = np.unique(labeled_room_mask[dilated > 0])
            adjacent_room_indices = [int(lbl) for lbl in overlap_labels if lbl > 0]
            adjacent_room_ids = [room_id_map[lbl] for lbl in adjacent_room_indices if lbl in room_id_map]

            # Associate door with rooms
            for rid in adjacent_room_ids:
                if door_id not in room_obj_map[rid]["associated_doors"]:
                    room_obj_map[rid]["associated_doors"].append(door_id)

            # If door touches 2 distinct rooms, record inter-room connection
            if len(adjacent_room_ids) >= 2:
                for i in range(len(adjacent_room_ids)):
                    for j in range(i + 1, len(adjacent_room_ids)):
                        r1 = min(adjacent_room_ids[i], adjacent_room_ids[j])
                        r2 = max(adjacent_room_ids[i], adjacent_room_ids[j])
                        pair_key = (r1, r2, door_id)
                        if pair_key not in connection_pairs_seen:
                            connection_pairs_seen.add(pair_key)
                            connections.append({
                                "plan_id": plan_id,
                                "room_a_id": r1,
                                "room_b_id": r2,
                                "door_id": door_id,
                                "connection_type": "door"
                            })

            doors.append({
                "door_id": door_id,
                "plan_id": plan_id,
                "door_index": door_counter,
                "area_pixels": area,
                "bbox_x": x,
                "bbox_y": y,
                "bbox_width": w,
                "bbox_height": h,
                "centroid_x": round(cx, 2),
                "centroid_y": round(cy, 2),
                "associated_rooms": adjacent_room_ids,
                "is_exterior": len(adjacent_room_ids) <= 1
            })

            door_counter += 1

        return doors, connections
