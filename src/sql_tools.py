"""
Secure SQL execution engine and database tool layer for ASHIAN AI Assistant.
Enforces read-only safety validation, parameterized execution, and query verification.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from src.database import DatabaseManager


class SafeQueryEngine:
    """
    Enforces strict security restrictions on SQL execution:
    - Read-only queries only (SELECT)
    - Anti-injection validation
    - Disallows table modification, schema manipulation, or multi-statement injections
    - Plan existence verification
    """

    # Forbidden SQL keywords / statements
    DANGEROUS_PATTERNS = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
        r"\bALTER\b", r"\bCREATE\b", r"\bREPLACE\b", r"\bTRUNCATE\b",
        r"\bATTACH\b", r"\bDETACH\b", r"\bPRAGMA\b", r"\bEXEC\b",
        r"\bVACUUM\b", r"\bGRANT\b", r"\bREVOKE\b"
    ]

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate whether a SQL statement is safe to execute.
        Returns:
            (is_safe, error_message)
        """
        clean = sql_query.strip()
        if not clean:
            return False, "Query string is empty."

        # Reject multi-statement chaining
        statements = [s for s in clean.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are strictly forbidden."

        single_stmt = statements[0].strip()

        # Must begin with SELECT or WITH (for CTEs)
        if not re.match(r"^(SELECT|WITH)\b", single_stmt, re.IGNORECASE):
            return False, "Only SELECT read-only queries are permitted."

        # Check for any forbidden tokens
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, single_stmt, re.IGNORECASE):
                kw = pattern.replace("\\b", "")
                return False, f"Prohibited SQL keyword detected: {kw}."

        return True, None

    def execute_safe_query(self, sql_query: str, params: Tuple = ()) -> Dict[str, Any]:
        """
        Safely execute a verified read-only SQL query.
        """
        is_safe, error = self.validate_sql(sql_query)
        if not is_safe:
            return {
                "success": False,
                "error": error,
                "query": sql_query,
                "rows": [],
                "columns": [],
                "row_count": 0
            }

        # Normalize statement (remove trailing semicolon if present)
        clean_sql = sql_query.strip().rstrip(";")
        rows, err = self.db.execute_read_query(clean_sql, params)

        if err:
            return {
                "success": False,
                "error": err,
                "query": clean_sql,
                "rows": [],
                "columns": [],
                "row_count": 0
            }

        columns = list(rows[0].keys()) if rows else []
        return {
            "success": True,
            "error": None,
            "query": clean_sql,
            "rows": rows,
            "columns": columns,
            "row_count": len(rows)
        }

    def plan_exists(self, plan_id: int) -> bool:
        """Verify whether a plan ID is present in the database."""
        res = self.execute_safe_query("SELECT 1 FROM plans WHERE plan_id = ?", (plan_id,))
        return res["success"] and res["row_count"] > 0

    def get_all_plan_ids(self) -> List[int]:
        """Return sorted list of all registered plan IDs."""
        res = self.execute_safe_query("SELECT plan_id FROM plans ORDER BY plan_id ASC;")
        if res["success"]:
            return [r["plan_id"] for r in res["rows"]]
        return []

    # ==========================================
    # Predefined Deterministic Query Methods
    # ==========================================

    def count_rooms(self, plan_id: int) -> Dict[str, Any]:
        query = "SELECT COUNT(*) AS room_count FROM rooms WHERE plan_id = ?;"
        return self.execute_safe_query(query, (plan_id,))

    def get_largest_room(self, plan_id: int) -> Dict[str, Any]:
        query = """
        SELECT room_id, room_index, category, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height
        FROM rooms
        WHERE plan_id = ?
        ORDER BY area_pixels DESC
        LIMIT 1;
        """
        return self.execute_safe_query(query, (plan_id,))

    def count_doors(self, plan_id: int) -> Dict[str, Any]:
        query = "SELECT COUNT(*) AS door_count FROM doors WHERE plan_id = ?;"
        return self.execute_safe_query(query, (plan_id,))

    def find_plans_with_doors_greater_than(self, threshold: int) -> Dict[str, Any]:
        query = """
        SELECT plan_id, COUNT(*) AS door_count
        FROM doors
        GROUP BY plan_id
        HAVING COUNT(*) > ?
        ORDER BY door_count DESC;
        """
        return self.execute_safe_query(query, (threshold,))

    def find_rooms_without_windows(self, plan_id: int) -> Dict[str, Any]:
        query = """
        SELECT room_id, room_index, category, area_pixels, centroid_x, centroid_y
        FROM rooms
        WHERE plan_id = ? AND window_count = 0
        ORDER BY room_index ASC;
        """
        return self.execute_safe_query(query, (plan_id,))

    def get_average_room_count(self) -> Dict[str, Any]:
        query = "SELECT ROUND(AVG(total_rooms), 2) AS average_rooms FROM plans;"
        return self.execute_safe_query(query)

    def list_room_areas(self, plan_id: int) -> Dict[str, Any]:
        query = """
        SELECT room_id, room_index, category, area_pixels
        FROM rooms
        WHERE plan_id = ?
        ORDER BY room_index ASC;
        """
        return self.execute_safe_query(query, (plan_id,))

    def get_room_positions(self, plan_id: int) -> Dict[str, Any]:
        query = """
        SELECT room_id, room_index, category, bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y
        FROM rooms
        WHERE plan_id = ?
        ORDER BY room_index ASC;
        """
        return self.execute_safe_query(query, (plan_id,))

    def get_room_connections(self, plan_id: int) -> Dict[str, Any]:
        query = """
        SELECT connection_id, plan_id, room_a_id, room_b_id, door_id, connection_type
        FROM room_connections
        WHERE plan_id = ?
        ORDER BY connection_id ASC;
        """
        return self.execute_safe_query(query, (plan_id,))

    def get_plan_summary(self, plan_id: int) -> Dict[str, Any]:
        query = "SELECT * FROM plans WHERE plan_id = ?;"
        return self.execute_safe_query(query, (plan_id,))
