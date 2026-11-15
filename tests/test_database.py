"""
Unit and integration tests for SQLite Database layer.
"""

from pathlib import Path
import sys
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import DatabaseManager


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    manager = DatabaseManager(db_path)
    yield manager
    try:
        db_path.unlink()
    except Exception:
        pass


def test_database_initialization(temp_db):
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {r[0] for r in cursor.fetchall()}
    expected = {"plans", "rooms", "doors", "windows", "walls", "room_connections", "extraction_metadata"}
    assert expected.issubset(tables)


def test_insert_and_query_plan(temp_db):
    plan_meta = {
        "plan_id": 999,
        "image_filename": "999.png",
        "mask_filename": "999 (2).png",
        "width": 1000,
        "height": 800
    }
    rooms = [
        {
            "room_id": 999001,
            "room_index": 1,
            "category": "Room 1",
            "area_pixels": 25000,
            "bbox_x": 10,
            "bbox_y": 10,
            "bbox_width": 200,
            "bbox_height": 125,
            "centroid_x": 110.0,
            "centroid_y": 72.5,
            "associated_doors": [999001],
            "associated_windows": []
        }
    ]
    doors = [
        {
            "door_id": 999001,
            "door_index": 1,
            "area_pixels": 500,
            "bbox_x": 200,
            "bbox_y": 50,
            "bbox_width": 10,
            "bbox_height": 30,
            "centroid_x": 205.0,
            "centroid_y": 65.0,
            "is_exterior": False,
            "associated_rooms": [999001]
        }
    ]

    success = temp_db.insert_extracted_plan(
        plan_meta=plan_meta,
        rooms=rooms,
        doors=doors,
        windows=[],
        wall_summary={"total_wall_pixels": 4000},
        wall_segments=[],
        connections=[]
    )
    assert success is True

    # Verify query
    rows, err = temp_db.execute_read_query("SELECT total_rooms, total_doors FROM plans WHERE plan_id = ?", (999,))
    assert err is None
    assert len(rows) == 1
    assert rows[0]["total_rooms"] == 1
    assert rows[0]["total_doors"] == 1


def test_foreign_key_cascade(temp_db):
    plan_meta = {
        "plan_id": 888,
        "image_filename": "888.png",
        "width": 500,
        "height": 500
    }
    rooms = [
        {
            "room_id": 888001,
            "room_index": 1,
            "category": "Room 1",
            "area_pixels": 1000,
            "bbox_x": 5, "bbox_y": 5, "bbox_width": 20, "bbox_height": 50,
            "centroid_x": 15.0, "centroid_y": 30.0
        }
    ]
    temp_db.insert_extracted_plan(plan_meta, rooms, [], [], {}, [], [])

    # Deleting plan 888 must cascade delete rooms
    with temp_db.get_connection() as conn:
        conn.execute("DELETE FROM plans WHERE plan_id = 888;")
        conn.commit()

    rows, _ = temp_db.execute_read_query("SELECT COUNT(*) as c FROM rooms WHERE plan_id = 888;")
    assert rows[0]["c"] == 0
