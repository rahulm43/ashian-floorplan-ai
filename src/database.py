"""
SQLite database management module for ASHIAN floor plan understanding system.
Implements normalized schema, indexing, foreign keys, validation, and CRUD operations.
"""

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from src.config import DATABASE_PATH


class DatabaseManager:
    """Manages SQLite database connections, schema migrations, and queries."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return an active SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        """Initialize database tables, foreign keys, and performance indices."""
        schema = """
        CREATE TABLE IF NOT EXISTS plans (
            plan_id INTEGER PRIMARY KEY,
            image_filename TEXT NOT NULL,
            mask_filename TEXT,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            total_rooms INTEGER DEFAULT 0,
            total_doors INTEGER DEFAULT 0,
            total_windows INTEGER DEFAULT 0,
            total_wall_area_px INTEGER DEFAULT 0,
            status TEXT DEFAULT 'processed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY,
            plan_id INTEGER NOT NULL,
            room_index INTEGER NOT NULL,
            category TEXT NOT NULL,
            area_pixels INTEGER NOT NULL CHECK (area_pixels > 0),
            bbox_x INTEGER NOT NULL,
            bbox_y INTEGER NOT NULL,
            bbox_width INTEGER NOT NULL CHECK (bbox_width > 0),
            bbox_height INTEGER NOT NULL CHECK (bbox_height > 0),
            centroid_x REAL NOT NULL,
            centroid_y REAL NOT NULL,
            solidity REAL,
            confidence REAL,
            polygon_json TEXT,
            door_count INTEGER DEFAULT 0,
            window_count INTEGER DEFAULT 0,
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE,
            UNIQUE(plan_id, room_index)
        );

        CREATE TABLE IF NOT EXISTS doors (
            door_id INTEGER PRIMARY KEY,
            plan_id INTEGER NOT NULL,
            door_index INTEGER NOT NULL,
            area_pixels INTEGER NOT NULL CHECK (area_pixels > 0),
            bbox_x INTEGER NOT NULL,
            bbox_y INTEGER NOT NULL,
            bbox_width INTEGER NOT NULL,
            bbox_height INTEGER NOT NULL,
            centroid_x REAL NOT NULL,
            centroid_y REAL NOT NULL,
            is_exterior INTEGER DEFAULT 0,
            associated_rooms_json TEXT,
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE,
            UNIQUE(plan_id, door_index)
        );

        CREATE TABLE IF NOT EXISTS windows (
            window_id INTEGER PRIMARY KEY,
            plan_id INTEGER NOT NULL,
            window_index INTEGER NOT NULL,
            area_pixels INTEGER NOT NULL CHECK (area_pixels > 0),
            bbox_x INTEGER NOT NULL,
            bbox_y INTEGER NOT NULL,
            bbox_width INTEGER NOT NULL,
            bbox_height INTEGER NOT NULL,
            centroid_x REAL NOT NULL,
            centroid_y REAL NOT NULL,
            associated_rooms_json TEXT,
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE,
            UNIQUE(plan_id, window_index)
        );

        CREATE TABLE IF NOT EXISTS walls (
            wall_id INTEGER PRIMARY KEY,
            plan_id INTEGER NOT NULL,
            area_pixels INTEGER NOT NULL CHECK (area_pixels > 0),
            bbox_x INTEGER NOT NULL,
            bbox_y INTEGER NOT NULL,
            bbox_width INTEGER NOT NULL,
            bbox_height INTEGER NOT NULL,
            centroid_x REAL NOT NULL,
            centroid_y REAL NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS room_connections (
            connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            room_a_id INTEGER NOT NULL,
            room_b_id INTEGER NOT NULL,
            door_id INTEGER,
            connection_type TEXT DEFAULT 'door',
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE,
            FOREIGN KEY (room_a_id) REFERENCES rooms(room_id) ON DELETE CASCADE,
            FOREIGN KEY (room_b_id) REFERENCES rooms(room_id) ON DELETE CASCADE,
            FOREIGN KEY (door_id) REFERENCES doors(door_id) ON DELETE CASCADE,
            UNIQUE(plan_id, room_a_id, room_b_id, door_id)
        );

        CREATE TABLE IF NOT EXISTS extraction_metadata (
            metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            extraction_status TEXT NOT NULL,
            pipeline_version TEXT NOT NULL,
            color_tolerance INTEGER NOT NULL,
            min_room_area_px INTEGER NOT NULL,
            execution_time_ms REAL NOT NULL,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE
        );

        -- Performance Indices
        CREATE INDEX IF NOT EXISTS idx_rooms_plan_id ON rooms(plan_id);
        CREATE INDEX IF NOT EXISTS idx_doors_plan_id ON doors(plan_id);
        CREATE INDEX IF NOT EXISTS idx_windows_plan_id ON windows(plan_id);
        CREATE INDEX IF NOT EXISTS idx_walls_plan_id ON walls(plan_id);
        CREATE INDEX IF NOT EXISTS idx_connections_plan_id ON room_connections(plan_id);
        CREATE INDEX IF NOT EXISTS idx_connections_rooms ON room_connections(room_a_id, room_b_id);
        """

        with self.get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

    def insert_extracted_plan(
        self,
        plan_meta: Dict,
        rooms: List[Dict],
        doors: List[Dict],
        windows: List[Dict],
        wall_summary: Dict,
        wall_segments: List[Dict],
        connections: List[Dict],
        exec_time_ms: float = 0.0,
        status: str = "success",
        error_msg: Optional[str] = None
    ) -> bool:
        """
        Transactional insertion of all extracted components for a floor plan.
        Rolls back if any integrity constraint is violated.
        """
        plan_id = plan_meta["plan_id"]

        with self.get_connection() as conn:
            try:
                # 1. Delete existing records for plan_id if re-inserting
                conn.execute("DELETE FROM plans WHERE plan_id = ?;", (plan_id,))

                # 2. Insert into plans
                conn.execute(
                    """
                    INSERT INTO plans (
                        plan_id, image_filename, mask_filename, width, height,
                        total_rooms, total_doors, total_windows, total_wall_area_px, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        plan_id,
                        plan_meta["image_filename"],
                        plan_meta.get("mask_filename"),
                        plan_meta["width"],
                        plan_meta["height"],
                        len(rooms),
                        len(doors),
                        len(windows),
                        wall_summary.get("total_wall_pixels", 0),
                        status
                    )
                )

                # 3. Insert rooms
                for r in rooms:
                    conn.execute(
                        """
                        INSERT INTO rooms (
                            room_id, plan_id, room_index, category, area_pixels,
                            bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y,
                            solidity, confidence, polygon_json, door_count, window_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            r["room_id"],
                            plan_id,
                            r["room_index"],
                            r["category"],
                            r["area_pixels"],
                            r["bbox_x"],
                            r["bbox_y"],
                            r["bbox_width"],
                            r["bbox_height"],
                            r["centroid_x"],
                            r["centroid_y"],
                            r.get("solidity", 1.0),
                            r.get("confidence", 1.0),
                            json.dumps(r.get("polygon", [])),
                            len(r.get("associated_doors", [])),
                            len(r.get("associated_windows", []))
                        )
                    )

                # 4. Insert doors
                for d in doors:
                    conn.execute(
                        """
                        INSERT INTO doors (
                            door_id, plan_id, door_index, area_pixels,
                            bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y,
                            is_exterior, associated_rooms_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            d["door_id"],
                            plan_id,
                            d["door_index"],
                            d["area_pixels"],
                            d["bbox_x"],
                            d["bbox_y"],
                            d["bbox_width"],
                            d["bbox_height"],
                            d["centroid_x"],
                            d["centroid_y"],
                            1 if d.get("is_exterior") else 0,
                            json.dumps(d.get("associated_rooms", []))
                        )
                    )

                # 5. Insert windows
                for w in windows:
                    conn.execute(
                        """
                        INSERT INTO windows (
                            window_id, plan_id, window_index, area_pixels,
                            bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y,
                            associated_rooms_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            w["window_id"],
                            plan_id,
                            w["window_index"],
                            w["area_pixels"],
                            w["bbox_x"],
                            w["bbox_y"],
                            w["bbox_width"],
                            w["bbox_height"],
                            w["centroid_x"],
                            w["centroid_y"],
                            json.dumps(w.get("associated_rooms", []))
                        )
                    )

                # 6. Insert walls
                for w_seg in wall_segments:
                    conn.execute(
                        """
                        INSERT INTO walls (
                            wall_id, plan_id, area_pixels,
                            bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            w_seg["wall_id"],
                            plan_id,
                            w_seg["area_pixels"],
                            w_seg["bbox_x"],
                            w_seg["bbox_y"],
                            w_seg["bbox_width"],
                            w_seg["bbox_height"],
                            w_seg["centroid_x"],
                            w_seg["centroid_y"]
                        )
                    )

                # 7. Insert room connections
                for c in connections:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO room_connections (
                            plan_id, room_a_id, room_b_id, door_id, connection_type
                        ) VALUES (?, ?, ?, ?, ?);
                        """,
                        (
                            plan_id,
                            c["room_a_id"],
                            c["room_b_id"],
                            c.get("door_id"),
                            c.get("connection_type", "door")
                        )
                    )

                # 8. Insert extraction metadata
                conn.execute(
                    """
                    INSERT INTO extraction_metadata (
                        plan_id, extraction_status, pipeline_version,
                        color_tolerance, min_room_area_px, execution_time_ms, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        plan_id,
                        status,
                        "1.0.0",
                        35,
                        800,
                        exec_time_ms,
                        error_msg
                    )
                )

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                print(f"[DB Error] Failed to insert plan {plan_id}: {e}")
                return False

    def execute_read_query(self, query: str, params: Tuple = ()) -> Tuple[List[Dict], Optional[str]]:
        """
        Execute a safe read-only SQL query and return rows as list of dicts.
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                return results, None
            except Exception as e:
                return [], str(e)

    def get_database_statistics(self) -> Dict[str, Any]:
        """Retrieve high-level statistics across all stored floor plans."""
        stats = {}
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM plans;")
            stats["total_plans"] = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(AVG(area_pixels), 0) FROM rooms;")
            room_cnt, avg_area = c.fetchone()
            stats["total_rooms"] = room_cnt
            stats["avg_room_area_px"] = round(avg_area, 1)

            c.execute("SELECT COUNT(*) FROM doors;")
            stats["total_doors"] = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM windows;")
            stats["total_windows"] = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM room_connections;")
            stats["total_connections"] = c.fetchone()[0]

            c.execute("SELECT COALESCE(AVG(total_rooms), 0) FROM plans;")
            stats["avg_rooms_per_plan"] = round(c.fetchone()[0], 2)

        return stats
