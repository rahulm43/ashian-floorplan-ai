"""
Master extraction pipeline for ASHIAN floor plan understanding system.
Processes images and masks, extracts entities with verified multi-color signatures,
populates SQLite, and produces multi-panel architectural inspection figures.
"""

import json
import time
from pathlib import Path
import cv2

from src.config import (
    EXTRACTED_DATA_DIR,
    VISUALIZATIONS_DIR,
    DATABASE_PATH,
    MIN_ROOM_AREA_PX
)
from src.data_loader import FloorPlanDataLoader
from src.mask_analyzer import MaskAnalyzer
from src.room_extractor import RoomExtractor
from src.door_extractor import DoorExtractor
from src.window_extractor import WindowExtractor
from src.wall_extractor import WallExtractor
from src.visualization import FloorPlanVisualizer
from src.database import DatabaseManager


def run_full_pipeline(max_visualizations: int = 6):
    print("=" * 70)
    print("  ASHIAN – Audited Multi-Color Extraction & Ingestion Pipeline")
    print("=" * 70)

    loader = FloorPlanDataLoader()
    pairs = loader.discover_pairs()
    mask_pairs = [p for p in pairs if p["has_mask"]]
    print(f"[Loader] Found {len(mask_pairs)} plans with masks available.")

    # Initialize audited components
    analyzer = MaskAnalyzer()
    room_ext = RoomExtractor()
    door_ext = DoorExtractor()
    window_ext = WindowExtractor()
    wall_ext = WallExtractor()
    visualizer = FloorPlanVisualizer()
    db = DatabaseManager(DATABASE_PATH)

    processed_count = 0
    total_rooms_found = 0
    total_doors_found = 0
    total_windows_found = 0
    total_connections_found = 0
    visualizations_generated = 0

    target_annotated_plans = {1, 2, 4, 10, 12}

    for plan_meta in mask_pairs:
        plan_id = plan_meta["plan_id"]
        start_time = time.time()

        image_rgb, mask_rgb, meta = loader.load_pair(plan_id)
        if image_rgb is None or mask_rgb is None:
            continue

        try:
            # 1. Multi-color class decomposition
            class_masks = analyzer.extract_all_masks(mask_rgb)

            # 2. Extract Rooms
            rooms, labeled_room_mask = room_ext.extract_rooms(
                class_masks.get("room"), plan_id
            )

            # 3. Extract Doors & Connectivity
            doors, connections = door_ext.extract_doors(
                class_masks.get("door"), plan_id, labeled_room_mask, rooms
            )

            # 4. Extract Windows
            windows = window_ext.extract_windows(
                class_masks.get("window"), plan_id, labeled_room_mask, rooms
            )

            # 5. Extract Walls
            wall_summary, wall_segments = wall_ext.extract_walls(
                class_masks.get("wall"), plan_id
            )

            exec_time_ms = round((time.time() - start_time) * 1000, 2)

            # 6. Database Transactional Ingestion
            db.insert_extracted_plan(
                plan_meta=plan_meta,
                rooms=rooms,
                doors=doors,
                windows=windows,
                wall_summary=wall_summary,
                wall_segments=wall_segments,
                connections=connections,
                exec_time_ms=exec_time_ms,
                status="success"
            )

            # 7. Export structured JSON artifact
            extracted_record = {
                "plan_id": plan_id,
                "metadata": plan_meta,
                "rooms": rooms,
                "doors": doors,
                "windows": windows,
                "walls": wall_summary,
                "connections": connections,
                "execution_time_ms": exec_time_ms
            }
            json_out_path = EXTRACTED_DATA_DIR / f"plan_{plan_id}.json"
            with open(json_out_path, "w", encoding="utf-8") as jf:
                json.dump(extracted_record, jf, indent=2)

            # 8. Generate Visualizations for key plans
            if plan_id in target_annotated_plans or visualizations_generated < max_visualizations:
                # Combined View
                visualizer.create_combined_view(
                    image_rgb=image_rgb,
                    rooms=rooms,
                    doors=doors,
                    windows=windows,
                    labeled_mask=labeled_room_mask,
                    plan_id=plan_id,
                    save_filename=f"annotated_plan_{plan_id}.png"
                )
                # 4-View Audit Panel
                visualizer.generate_four_view_panel(
                    image_rgb=image_rgb,
                    mask_rgb=mask_rgb,
                    rooms=rooms,
                    doors=doors,
                    windows=windows,
                    labeled_mask=labeled_room_mask,
                    plan_id=plan_id,
                    save_filename=f"plan_{plan_id}_audit_panel.png"
                )
                visualizations_generated += 1

            processed_count += 1
            total_rooms_found += len(rooms)
            total_doors_found += len(doors)
            total_windows_found += len(windows)
            total_connections_found += len(connections)

            print(
                f"[Plan {plan_id:03d}] Extracted -> Rooms: {len(rooms):2d} | "
                f"Doors: {len(doors):2d} | Windows: {len(windows):2d} | "
                f"Links: {len(connections):2d} ({exec_time_ms:.1f}ms)",
                flush=True
            )

        except Exception as e:
            print(f"[Error] Failed to process Plan {plan_id}: {e}", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("  AUDITED EXTRACTION SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(f"Total Plans Processed     : {processed_count}", flush=True)
    print(f"Total Rooms Extracted     : {total_rooms_found}", flush=True)
    print(f"Total Doors Extracted     : {total_doors_found}", flush=True)
    print(f"Total Windows Extracted   : {total_windows_found}", flush=True)
    print(f"Total Inter-Room Links    : {total_connections_found}", flush=True)
    print(f"Visualizations Generated  : {visualizations_generated}", flush=True)
    print(f"Database Stored At        : {DATABASE_PATH}", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    run_full_pipeline()
