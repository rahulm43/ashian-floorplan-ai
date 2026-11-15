"""
Generate individual view files for each plan:
- room_seg_{pid}.png
- openings_{pid}.png
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from PIL import Image

from src.config import IMAGES_DIR, MASKS_DIR, VISUALIZATIONS_DIR, DATABASE_PATH
from src.database import DatabaseManager
from src.data_loader import FloorPlanDataLoader
from src.mask_analyzer import MaskAnalyzer
from src.room_extractor import RoomExtractor
from src.door_extractor import DoorExtractor
from src.window_extractor import WindowExtractor
from src.visualization import FloorPlanVisualizer

def generate_individual_views():
    loader = FloorPlanDataLoader()
    analyzer = MaskAnalyzer()
    room_ext = RoomExtractor()
    door_ext = DoorExtractor()
    win_ext = WindowExtractor()
    vis = FloorPlanVisualizer()

    plans_to_render = [1, 2, 3, 4, 10, 12]

    for pid in plans_to_render:
        try:
            img, mask, meta = loader.load_pair(pid)
            if img is None or mask is None:
                continue

            class_masks = analyzer.extract_all_masks(mask)
            rooms, labeled_mask = room_ext.extract_rooms(class_masks.get("room"), pid)
            doors, connections = door_ext.extract_doors(class_masks.get("door"), pid, labeled_mask, rooms)
            windows = win_ext.extract_windows(class_masks.get("window"), pid, labeled_mask, rooms)

            # View B: Room segmentation
            room_view = vis.render_room_segmentation_view(img, rooms, labeled_mask, plan_id=pid)
            cv2.imwrite(str(VISUALIZATIONS_DIR / f"room_seg_{pid}.png"), cv2.cvtColor(room_view, cv2.COLOR_RGB2BGR))

            # View C: Openings
            openings_view = vis.render_doors_windows_view(img, doors, windows, plan_id=pid)
            cv2.imwrite(str(VISUALIZATIONS_DIR / f"openings_{pid}.png"), cv2.cvtColor(openings_view, cv2.COLOR_RGB2BGR))

            print(f"Plan {pid}: generated room_seg_{pid}.png and openings_{pid}.png")
        except Exception as e:
            print(f"Error rendering plan {pid}: {e}")

if __name__ == "__main__":
    generate_individual_views()
