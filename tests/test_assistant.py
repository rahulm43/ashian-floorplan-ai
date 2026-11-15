"""
Unit tests for AI Assistant, SQL security validation, and QA grounding.
"""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sql_tools import SafeQueryEngine
from src.assistant import AshianAssistant


def test_sql_security_filter():
    engine = SafeQueryEngine()

    # Allowed queries
    safe_queries = [
        "SELECT COUNT(*) FROM rooms WHERE plan_id = 12;",
        "SELECT room_id, area_pixels FROM rooms ORDER BY area_pixels DESC LIMIT 1;",
        "WITH room_summary AS (SELECT plan_id, COUNT(*) as c FROM rooms GROUP BY plan_id) SELECT * FROM room_summary;"
    ]
    for q in safe_queries:
        is_safe, err = engine.validate_sql(q)
        assert is_safe is True, f"Failed safe query: {q} ({err})"

    # Prohibited queries
    dangerous_queries = [
        "DROP TABLE rooms;",
        "DELETE FROM plans WHERE plan_id = 1;",
        "UPDATE rooms SET area_pixels = 0;",
        "INSERT INTO plans (plan_id) VALUES (999);",
        "SELECT * FROM rooms; DROP TABLE doors;",  # Multi-statement injection
        "ATTACH DATABASE 'evil.db' AS evil;",
        "PRAGMA table_info(rooms);"
    ]
    for dq in dangerous_queries:
        is_safe, err = engine.validate_sql(dq)
        assert is_safe is False, f"Should have blocked: {dq}"


def test_assistant_canonical_answers():
    assistant = AshianAssistant()

    # 1. Room counting
    res = assistant.ask("How many rooms does plan 12 have?")
    assert "Plan 12 contains" in res["answer"]
    assert res["is_supported"] is True
    assert res["sql_query"] is not None

    # 2. Average rooms
    res = assistant.ask("What is the average number of rooms across all plans?")
    assert "average number of rooms" in res["answer"].lower()
    assert res["is_supported"] is True

    # 3. Unsupported query refusal
    res = assistant.ask("What color are the walls painted in plan 12?")
    assert "cannot determine" in res["answer"].lower()
    assert res["is_supported"] is False

    # 4. Invalid plan ID
    res = assistant.ask("How many rooms does plan 88888 have?")
    assert "not found" in res["answer"].lower()
    assert res["is_supported"] is False
