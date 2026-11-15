"""
Unit tests for Computer Vision extraction modules.
"""

from pathlib import Path
import sys
import numpy as np
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.mask_analyzer import MaskAnalyzer
from src.room_extractor import RoomExtractor
from src.door_extractor import DoorExtractor
from src.window_extractor import WindowExtractor
from src.wall_extractor import WallExtractor
from src.config import CLASS_COLORS


def test_mask_analyzer_color_distance():
    analyzer = MaskAnalyzer()
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[0:5, 0:5] = CLASS_COLORS["room"]  # (255, 142, 70)

    binary = analyzer.extract_binary_mask(img, "room")
    assert binary.shape == (10, 10)
    assert np.count_nonzero(binary[0:5, 0:5]) > 0
    assert np.count_nonzero(binary[5:10, 5:10]) == 0


def test_room_extractor_synthetic():
    extractor = RoomExtractor(min_area_px=50)
    # Create synthetic binary mask with 2 distinct room blobs
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:30, 10:30] = 255  # 400 px
    mask[60:90, 60:90] = 255  # 900 px

    rooms, labeled = extractor.extract_rooms(mask, plan_id=99)
    assert len(rooms) == 2
    assert rooms[0]["plan_id"] == 99
    assert rooms[0]["area_pixels"] in [400, 900]
    assert rooms[1]["area_pixels"] in [400, 900]
    assert rooms[0]["bbox_width"] in [20, 30]


def test_door_extractor_connectivity():
    door_ext = DoorExtractor(min_area_px=10, dilation_radius=15)

    # 2 rooms side by side
    labeled_rooms = np.zeros((100, 100), dtype=np.int32)
    labeled_rooms[10:90, 10:45] = 1
    labeled_rooms[10:90, 55:90] = 2

    rooms = [
        {"room_index": 1, "room_id": 99001, "associated_doors": []},
        {"room_index": 2, "room_id": 99002, "associated_doors": []}
    ]

    # Door between the two rooms at x=48..52, y=45..55
    door_mask = np.zeros((100, 100), dtype=np.uint8)
    door_mask[45:55, 48:52] = 255

    doors, connections = door_ext.extract_doors(door_mask, 99, labeled_rooms, rooms)
    assert len(doors) == 1
    assert len(connections) == 1
    assert connections[0]["room_a_id"] == 99001
    assert connections[0]["room_b_id"] == 99002


def test_window_extractor_association():
    win_ext = WindowExtractor(min_area_px=10, dilation_radius=15)

    labeled_rooms = np.zeros((100, 100), dtype=np.int32)
    labeled_rooms[20:80, 20:80] = 1

    rooms = [
        {"room_index": 1, "room_id": 99001, "associated_windows": []}
    ]

    # Window on outer wall touching room
    win_mask = np.zeros((100, 100), dtype=np.uint8)
    win_mask[18:22, 40:60] = 255

    windows = win_ext.extract_windows(win_mask, 99, labeled_rooms, rooms)
    assert len(windows) == 1
    assert 99001 in windows[0]["associated_rooms"]
    assert len(rooms[0]["associated_windows"]) == 1
