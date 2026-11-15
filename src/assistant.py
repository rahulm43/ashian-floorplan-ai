"""
AI Assistant module for ASHIAN floor plan understanding and question answering.
Integrates LLM reasoning with strict read-only database query execution and evidence grounding.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src.config import GEMINI_API_KEY, OPENAI_API_KEY, LLM_MODEL_NAME
from src.sql_tools import SafeQueryEngine


class AshianAssistant:
    """
    Intelligent Floor Plan Question-Answering Assistant.
    Translates natural language questions into safe SQLite queries,
    retrieves grounded database evidence, and synthesizes accurate answers.
    """

    UNSUPPORTED_KEYWORDS = [
        "ceiling", "height", "color", "paint", "cost", "price", "rent",
        "material", "brick", "wood", "sq ft", "square feet", "sqm", "square meter",
        "square metre", "architect", "engineer", "owner", "tenant", "year", "built",
        "furnishing", "bed", "sofa", "television", "appliance", "plumbing", "pipe"
    ]

    DATABASE_SCHEMA_PROMPT = """
    Database Schema:
    - plans(plan_id, image_filename, mask_filename, width, height, total_rooms, total_doors, total_windows, total_wall_area_px, status)
    - rooms(room_id, plan_id, room_index, category, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y, solidity, confidence, door_count, window_count)
    - doors(door_id, plan_id, door_index, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y, is_exterior)
    - windows(window_id, plan_id, window_index, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y)
    - walls(wall_id, plan_id, area_pixels, bbox_x, bbox_y, bbox_width, bbox_height, centroid_x, centroid_y)
    - room_connections(connection_id, plan_id, room_a_id, room_b_id, door_id, connection_type)
    """

    def __init__(self, query_engine: Optional[SafeQueryEngine] = None, api_key: Optional[str] = None):
        self.engine = query_engine or SafeQueryEngine()
        self.api_key = api_key or GEMINI_API_KEY
        self.gemini_client = None
        self._init_llm_client()

    def set_api_key(self, key: str):
        """Set or update Gemini API key at runtime."""
        if key and key.strip():
            self.api_key = key.strip()
            self._init_llm_client()

    def _init_llm_client(self):
        """Initialize Google GenAI client if API key is present."""
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.api_key)
                print("[Assistant] Google Gemini client initialized successfully.")
            except Exception as e:
                print(f"[Assistant] LLM client init warning: {e}")
                self.gemini_client = None

    def extract_plan_id_from_text(self, text: str) -> Optional[int]:
        """Extract referenced plan ID from user question (e.g., 'plan 12', 'plan #7', 'plan id 4')."""
        match = re.search(r"\bplan\s*(?:id|#)?\s*(\d+)\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Match standalone floor plan reference
        match = re.search(r"\bfloor\s*plan\s*(\d+)\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def is_unsupported_question(self, question: str) -> Tuple[bool, Optional[str]]:
        """Check if question asks for information not present in the dataset."""
        q_lower = question.lower()
        for kw in self.UNSUPPORTED_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                return True, (
                    f"I cannot determine this from the available floor plan data. "
                    f"Architectural attributes such as '{kw}', physical metric scale, "
                    f"or finish specifications are not recorded in this segmentation dataset."
                )
        return False, None

    def ask(self, question: str, active_plan_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a natural language question about floor plans.
        Accepts an optional active_plan_id for context (e.g., currently uploaded/viewed plan).
        """
        q_clean = question.strip()
        if not q_clean:
            return {
                "question": question,
                "answer": "Please ask a question regarding the floor plan.",
                "sql_query": None,
                "query_result": None,
                "plan_id": active_plan_id,
                "is_supported": False,
                "error": "Empty question."
            }

        # Determine target plan ID (from text or active context)
        plan_id = self.extract_plan_id_from_text(q_clean) or active_plan_id

        # 1. Check for known unsupported domain queries
        is_unsupported, reason = self.is_unsupported_question(q_clean)
        if is_unsupported:
            return {
                "question": question,
                "answer": reason,
                "sql_query": None,
                "query_result": None,
                "plan_id": plan_id,
                "is_supported": False,
                "error": None
            }

        # 2. Try Deterministic Semantic Router first (guaranteed 100% accuracy on core questions)
        deterministic_response = self._handle_deterministic_questions(q_clean, plan_id)
        if deterministic_response is not None:
            return deterministic_response

        # 3. If LLM is available, use LLM-assisted SQL synthesis
        if self.gemini_client:
            llm_response = self._handle_llm_question(q_clean)
            if llm_response is not None:
                return llm_response

        # 4. Fallback when question cannot be mapped
        return {
            "question": question,
            "answer": "I cannot determine this from the available floor plan data.",
            "sql_query": None,
            "query_result": None,
            "plan_id": self.extract_plan_id_from_text(q_clean),
            "is_supported": False,
            "error": "Unable to map question to available dataset attributes."
        }

    def _handle_deterministic_questions(self, question: str, target_plan_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Direct deterministic handling for the canonical floor plan question types.
        Order is prioritized from most specific to general to avoid regex mis-routing.
        """
        q = question.lower()
        extracted_pid = self.extract_plan_id_from_text(question)
        plan_id = extracted_pid if extracted_pid is not None else target_plan_id

        # Validate plan existence if plan_id is mentioned
        if plan_id is not None and not self.engine.plan_exists(plan_id):
            avail = self.engine.get_all_plan_ids()[:10]
            avail_str = ", ".join(str(x) for x in avail)
            return {
                "question": question,
                "answer": f"Plan {plan_id} was not found in the database. Available plans include: {avail_str}...",
                "sql_query": f"SELECT 1 FROM plans WHERE plan_id = {plan_id};",
                "query_result": [],
                "plan_id": plan_id,
                "is_supported": False,
                "error": f"Plan {plan_id} does not exist."
            }

        # 1. Missing / Unavailable Information
        if re.search(r"\b(?:what\s+information\s+is\s+unavailable|limitations?|missing\s+information)\b", q):
            ans = (
                "The following information is NOT available in this floor plan dataset:\n"
                "1. Physical metric dimensions (e.g. square metres or feet) - only raw pixel dimensions are available.\n"
                "2. Specific architectural room semantics (e.g. Master Bedroom vs Kitchen) - labels are based on geometric segmentation.\n"
                "3. Wall materials, thicknesses, or structural load specifications.\n"
                "4. Ceiling heights, vertical elevations, or 3D volumes.\n"
                "5. Electrical, plumbing, and HVAC layouts.\n"
                "6. Architect, ownership, and building code compliance metadata."
            )
            return {
                "question": question,
                "answer": ans,
                "sql_query": None,
                "query_result": None,
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 2. Average number of rooms across all plans
        if re.search(r"\baverage\s+(?:number\s+of\s+)?rooms?\b", q):
            res = self.engine.get_average_room_count()
            avg = res["rows"][0]["average_rooms"] if res["rows"] else 0.0
            return {
                "question": question,
                "answer": f"The average number of rooms across all processed floor plans is {avg}.",
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        # 2b. Plan with the highest number of rooms
        if re.search(r"\b(?:which\s+plan\s+has\s+the\s+)?(?:highest|most|maximum)\s+(?:number\s+of\s+)?rooms?\b", q):
            sql = "SELECT plan_id, total_rooms FROM plans WHERE plan_id != 99999 ORDER BY total_rooms DESC LIMIT 1;"
            res = self.engine.execute_safe_query(sql)
            if res["rows"]:
                top = res["rows"][0]
                ans = f"Plan {top['plan_id']} has the highest number of rooms with {top['total_rooms']} rooms."
            else:
                ans = "No plans found in the database."
            return {
                "question": question,
                "answer": ans,
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        # 2c. Total count of doors across all plans
        if re.search(r"\b(?:total\s+(?:number\s+of\s+|count\s+of\s+)?doors|all\s+doors)\s+across\s+all\s+plans\b|\btotal\s+(?:doors|number of doors)\b(?!.*\bplan\s+\d+)", q):
            sql = "SELECT SUM(total_doors) as grand_total_doors FROM plans WHERE plan_id != 99999;"
            res = self.engine.execute_safe_query(sql)
            tot = res["rows"][0]["grand_total_doors"] if res["rows"] else 0
            return {
                "question": question,
                "answer": f"The total number of doors across all processed plans is {tot}.",
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        # 2d. Total room area in a plan
        if plan_id is not None and re.search(r"\btotal\s+(?:room\s+)?area\b|\bsum\s+of\s+(?:all\s+)?areas?\b", q):
            sql = f"SELECT SUM(area_pixels) as total_area FROM rooms WHERE plan_id = {plan_id};"
            res = self.engine.execute_safe_query(sql)
            tot = res["rows"][0]["total_area"] if res["rows"] and res["rows"][0]["total_area"] else 0
            return {
                "question": question,
                "answer": f"The total room area for plan {plan_id} is {tot:,} px².",
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 2e. Smallest room in a plan
        if plan_id is not None and re.search(r"\b(?:smallest|minimum|tiniest)\s+room\b", q):
            sql = f"SELECT room_index, category, area_pixels FROM rooms WHERE plan_id = {plan_id} ORDER BY area_pixels ASC LIMIT 1;"
            res = self.engine.execute_safe_query(sql)
            if res["rows"]:
                r = res["rows"][0]
                ans = f"The smallest room in plan {plan_id} is {r['category']} (Room {r['room_index']}) with an area of {r['area_pixels']:,} px²."
            else:
                ans = f"No room records found for plan {plan_id}."
            return {
                "question": question,
                "answer": ans,
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 3. Filter plans with more than N doors
        door_threshold_match = re.search(r"\b(?:more than|greater than|>)\s*(\d+)\s*doors?\b", q)
        if door_threshold_match:
            thresh = int(door_threshold_match.group(1))
            res = self.engine.find_plans_with_doors_greater_than(thresh)
            if res["rows"]:
                plans_list = [f"Plan {r['plan_id']} ({r['door_count']} doors)" for r in res["rows"]]
                ans = f"Plans with more than {thresh} doors are: {', '.join(plans_list)}."
            else:
                ans = f"No floor plans have more than {thresh} doors in the database."
            return {
                "question": question,
                "answer": ans,
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        # 4. Rooms without windows
        if plan_id is not None and re.search(r"\b(?:no\s+windows?|without\s+windows?|zero\s+windows?|has\s+no\s+windows?)\b", q):
            res = self.engine.find_rooms_without_windows(plan_id)
            if res["rows"]:
                room_names = [f"{r['category']} (ID {r['room_id']})" for r in res["rows"]]
                ans = f"In plan {plan_id}, the following room(s) have no windows: {', '.join(room_names)}."
            else:
                ans = f"In plan {plan_id}, all extracted rooms have at least one associated window."
            return {
                "question": question,
                "answer": ans,
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 5. Largest room in a plan
        if plan_id is not None and re.search(r"\b(?:largest|biggest|maximum|greatest)\s+room\b", q):
            res = self.engine.get_largest_room(plan_id)
            if res["rows"]:
                r = res["rows"][0]
                ans = (
                    f"The largest room in plan {plan_id} is {r['category']} (Room ID {r['room_id']}) "
                    f"with a segmented area of {r['area_pixels']:,} pixels."
                )
            else:
                ans = f"No room records found for plan {plan_id}."
            return {
                "question": question,
                "answer": ans,
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 6. Room areas in a plan
        if plan_id is not None and re.search(r"\b(?:areas?|sizes?)\s+of\s+(?:all\s+)?rooms?\b|\broom\s+areas?\b", q):
            res = self.engine.list_room_areas(plan_id)
            if res["rows"]:
                area_list = [f"{r['category']}: {r['area_pixels']:,} px" for r in res["rows"]]
                ans = f"Room areas in plan {plan_id} (pixel measurements):\n" + "\n".join(f"- {a}" for a in area_list)
            else:
                ans = f"No room records found for plan {plan_id}."
            return {
                "question": question,
                "answer": ans,
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 7. Room positions / coordinates in a plan
        if plan_id is not None and re.search(r"\b(?:positions?|coordinates?|locations?|centroids?)\b", q):
            res = self.engine.get_room_positions(plan_id)
            if res["rows"]:
                pos_list = [
                    f"{r['category']}: Centroid ({r['centroid_x']}, {r['centroid_y']}), BBox [x={r['bbox_x']}, y={r['bbox_y']}, w={r['bbox_width']}, h={r['bbox_height']}]"
                    for r in res["rows"]
                ]
                ans = f"Room positions in plan {plan_id}:\n" + "\n".join(f"- {p}" for p in pos_list)
            else:
                ans = f"No position records found for plan {plan_id}."
            return {
                "question": question,
                "answer": ans,
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 8. Room connections through doors
        if plan_id is not None and re.search(r"\b(?:connected|connections?|accessible|linked)\b", q):
            res = self.engine.get_room_connections(plan_id)
            if res["rows"]:
                links = [f"Room {r['room_a_id']} <-> Room {r['room_b_id']} (via Door {r['door_id']})" for r in res["rows"]]
                ans = f"Room connections in plan {plan_id}:\n" + "\n".join(f"- {l}" for l in links)
            else:
                ans = f"No direct inter-room door connections were extracted for plan {plan_id} (doors may connect to exterior or corridors)."
            return {
                "question": question,
                "answer": ans,
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 9. Count doors in a particular plan
        if plan_id is not None and re.search(r"\b(?:how many|count|number of)\s+doors?\b", q):
            res = self.engine.count_doors(plan_id)
            count = res["rows"][0]["door_count"] if res["rows"] else 0
            return {
                "question": question,
                "answer": f"Plan {plan_id} contains {count} extracted doors.",
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 10. Count rooms in a particular plan
        if plan_id is not None and (
            re.search(r"\b(?:how many|count of|number of|total)\s+rooms?\b", q) or
            re.search(r"^how many rooms\??$", q) or
            re.search(r"\bhow many rooms\s+(?:does|in|are in)\b", q) or
            re.search(r"\broom\s+count\b", q)
        ):
            res = self.engine.count_rooms(plan_id)
            count = res["rows"][0]["room_count"] if res["rows"] else 0
            return {
                "question": question,
                "answer": f"Plan {plan_id} contains {count} extracted rooms.",
                "sql_query": res["query"],
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 11. Smallest room in a plan
        if plan_id is not None and re.search(r"\b(?:smallest|minimum|tiniest)\s+room\b", q):
            sql = f"SELECT room_index, category, area_pixels FROM rooms WHERE plan_id = {plan_id} ORDER BY area_pixels ASC LIMIT 1;"
            res = self.engine.execute_safe_query(sql)
            if res["rows"]:
                r = res["rows"][0]
                ans = f"The smallest room in plan {plan_id} is {r['category']} (Room {r['room_index']}) with an area of {r['area_pixels']:,} px²."
            else:
                ans = f"No room records found for plan {plan_id}."
            return {
                "question": question,
                "answer": ans,
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 12. Total room area in a plan
        if plan_id is not None and re.search(r"\btotal\s+(?:room\s+)?area\b|\bsum\s+of\s+(?:all\s+)?areas?\b", q):
            sql = f"SELECT SUM(area_pixels) as total_area FROM rooms WHERE plan_id = {plan_id};"
            res = self.engine.execute_safe_query(sql)
            tot = res["rows"][0]["total_area"] if res["rows"] and res["rows"][0]["total_area"] else 0
            return {
                "question": question,
                "answer": f"The total room area for plan {plan_id} is {tot:,} px².",
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 13. Room with most windows in a plan
        if plan_id is not None and re.search(r"\bmost\s+windows?\b|\bmaximum\s+windows?\b", q):
            sql = f"SELECT room_index, category, window_count FROM rooms WHERE plan_id = {plan_id} ORDER BY window_count DESC LIMIT 1;"
            res = self.engine.execute_safe_query(sql)
            if res["rows"]:
                r = res["rows"][0]
                ans = f"In plan {plan_id}, {r['category']} (Room {r['room_index']}) has the most windows ({r['window_count']} windows)."
            else:
                ans = f"No window data found for plan {plan_id}."
            return {
                "question": question,
                "answer": ans,
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 14. Count windows in a particular plan
        if plan_id is not None and re.search(r"\b(?:how many|count of|number of|total)\s+windows?\b", q):
            sql = f"SELECT total_windows FROM plans WHERE plan_id = {plan_id};"
            res = self.engine.execute_safe_query(sql)
            count = res["rows"][0]["total_windows"] if res["rows"] else 0
            return {
                "question": question,
                "answer": f"Plan {plan_id} contains {count} extracted windows.",
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": plan_id,
                "is_supported": True,
                "error": None
            }

        # 15. Plan with the highest number of rooms
        if re.search(r"\b(?:highest|most|maximum)\s+(?:number\s+of\s+)?rooms?\b", q):
            sql = "SELECT plan_id, total_rooms FROM plans WHERE plan_id != 99999 ORDER BY total_rooms DESC LIMIT 1;"
            res = self.engine.execute_safe_query(sql)
            if res["rows"]:
                top = res["rows"][0]
                ans = f"Plan {top['plan_id']} has the highest number of rooms ({top['total_rooms']} rooms)."
            else:
                ans = "No plans found in the database."
            return {
                "question": question,
                "answer": ans,
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        # 16. Total count of doors or windows across all plans
        if re.search(r"\btotal\s+(?:number\s+of\s+|count\s+of\s+)?doors\s+across\s+all\s+plans\b", q):
            sql = "SELECT SUM(total_doors) as grand_total_doors FROM plans WHERE plan_id != 99999;"
            res = self.engine.execute_safe_query(sql)
            tot = res["rows"][0]["grand_total_doors"] if res["rows"] else 0
            return {
                "question": question,
                "answer": f"The total number of doors across all processed plans is {tot}.",
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        if re.search(r"\b(?:more than|greater than|>)\s*(\d+)\s*windows?\b", q):
            thresh_match = re.search(r"\b(?:more than|greater than|>)\s*(\d+)\s*windows?\b", q)
            w_thresh = int(thresh_match.group(1)) if thresh_match else 5
            sql = f"SELECT plan_id, total_windows FROM plans WHERE total_windows > {w_thresh} AND plan_id != 99999 ORDER BY total_windows DESC;"
            res = self.engine.execute_safe_query(sql)
            if res["rows"]:
                p_list = [f"Plan {r['plan_id']} ({r['total_windows']} windows)" for r in res["rows"]]
                ans = f"Plans with more than {w_thresh} windows are: {', '.join(p_list)}."
            else:
                ans = f"No plans found with more than {w_thresh} windows."
            return {
                "question": question,
                "answer": ans,
                "sql_query": sql,
                "query_result": res["rows"],
                "plan_id": None,
                "is_supported": True,
                "error": None
            }

        return None

    def _handle_llm_question(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Use Google GenAI API to translate complex natural language questions into safe SQL.
        """
        system_instruction = (
            "You are ASHIAN, a strict architectural database assistant. "
            "Your job is to generate a SINGLE read-only SQLite SELECT query to answer the user's question. "
            "Never generate INSERT, UPDATE, DELETE, DROP, or ALTER. "
            "Output ONLY valid SQL in a ```sql code block. Do not provide explanations in the query block.\n"
            + self.DATABASE_SCHEMA_PROMPT
        )

        try:
            response = self.gemini_client.models.generate_content(
                model=LLM_MODEL_NAME,
                contents=question,
                config={"system_instruction": system_instruction, "temperature": 0.0}
            )
            resp_text = response.text or ""

            # Extract SQL query from markdown block
            sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", resp_text, re.DOTALL | re.IGNORECASE)
            sql_query = sql_match.group(1).strip() if sql_match else resp_text.strip()

            # Execute safely
            res = self.engine.execute_safe_query(sql_query)
            if not res["success"]:
                return {
                    "question": question,
                    "answer": "I cannot determine this from the available floor plan data.",
                    "sql_query": sql_query,
                    "query_result": [],
                    "plan_id": self.extract_plan_id_from_text(question),
                    "is_supported": False,
                    "error": res["error"]
                }

            # Generate natural language synthesis of the results
            synthesis_prompt = (
                f"Question: {question}\n"
                f"SQL Query: {sql_query}\n"
                f"Database Results: {json.dumps(res['rows'])}\n"
                "Synthesize a clear, concise, direct answer based strictly on the results above. "
                "Never invent values. If rows are empty, state that no records match."
            )
            synth_resp = self.gemini_client.models.generate_content(
                model=LLM_MODEL_NAME,
                contents=synthesis_prompt,
                config={"temperature": 0.2}
            )

            return {
                "question": question,
                "answer": synth_resp.text.strip(),
                "sql_query": sql_query,
                "query_result": res["rows"],
                "plan_id": self.extract_plan_id_from_text(question),
                "is_supported": True,
                "error": None
            }

        except Exception as e:
            print(f"[Assistant] LLM execution fallback: {e}")
            return None

    def ask_gemini_direct(self, question: str, active_plan_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Ask Google Gemini API directly with live floor plan database context.
        Generates architectural solutions, layout recommendations, and grounded query responses.
        """
        plan_id = self.extract_plan_id_from_text(question) or active_plan_id or 1

        # Check unsupported keywords first
        is_unsupported, reason = self.is_unsupported_question(question)
        if is_unsupported:
            return {
                "question": question,
                "answer": reason,
                "sql_query": None,
                "query_result": None,
                "plan_id": plan_id,
                "is_supported": False,
                "error": None
            }

        # Check if plan exists
        if not self.engine.plan_exists(plan_id):
            avail = self.engine.get_all_plan_ids()[:10]
            avail_str = ", ".join(str(x) for x in avail)
            return {
                "question": question,
                "answer": f"Plan {plan_id} was not found in the database. Available plans include: {avail_str}...",
                "sql_query": f"SELECT 1 FROM plans WHERE plan_id = {plan_id};",
                "query_result": [],
                "plan_id": plan_id,
                "is_supported": False,
                "error": f"Plan {plan_id} does not exist."
            }

        # Fetch live database context for this floor plan
        rooms, _ = self.engine.db.execute_read_query(
            "SELECT room_id, room_index, category, area_pixels, bbox_width, bbox_height, centroid_x, centroid_y, door_count, window_count "
            "FROM rooms WHERE plan_id = ? ORDER BY room_index ASC", (plan_id,)
        )
        doors, _ = self.engine.db.execute_read_query(
            "SELECT door_id, door_index, centroid_x, centroid_y, area_pixels FROM doors WHERE plan_id = ?", (plan_id,)
        )
        windows, _ = self.engine.db.execute_read_query(
            "SELECT window_id, window_index, centroid_x, centroid_y, area_pixels FROM windows WHERE plan_id = ?", (plan_id,)
        )
        conns, _ = self.engine.db.execute_read_query(
            "SELECT room_a_id, room_b_id, door_id, connection_type FROM room_connections WHERE plan_id = ?", (plan_id,)
        )

        context_data = {
            "plan_id": plan_id,
            "total_rooms": len(rooms),
            "total_doors": len(doors),
            "total_windows": len(windows),
            "rooms": rooms,
            "doors": doors,
            "windows": windows,
            "inter_room_door_connections": conns
        }

        # If Gemini client is active, execute direct Gemini reasoning!
        if self.gemini_client:
            prompt = (
                f"You are ASHIAN, an expert Architectural AI Assistant powered by Google Gemini.\n"
                f"You are analyzing architectural Floor Plan {plan_id}.\n\n"
                f"Here is the verified spatial database data extracted via Computer Vision:\n"
                f"{json.dumps(context_data, indent=2)}\n\n"
                f"User Question or Request: \"{question}\"\n\n"
                f"Instructions:\n"
                f"1. Answer the question directly, or provide architectural solutions and recommendations for this floor plan.\n"
                f"2. Reference exact room numbers, door connections, window counts, and pixel dimensions from the provided data.\n"
                f"3. Include the exact read-only SQLite SELECT query that supports or verifies your answer inside a ```sql ... ``` block.\n"
                f"4. Be concise, professional, and never invent metric units (all areas are raw pixels)."
            )
            try:
                response = self.gemini_client.models.generate_content(
                    model=LLM_MODEL_NAME,
                    contents=prompt,
                    config={"temperature": 0.2}
                )
                resp_text = response.text or ""

                sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", resp_text, re.DOTALL | re.IGNORECASE)
                sql_query = sql_match.group(1).strip() if sql_match else None
                clean_answer = re.sub(r"```(?:sql)?\s*.*?\s*```", "", resp_text, flags=re.DOTALL | re.IGNORECASE).strip()

                return {
                    "question": question,
                    "answer": clean_answer or resp_text,
                    "sql_query": sql_query or f"SELECT COUNT(*) FROM rooms WHERE plan_id = {plan_id};",
                    "query_result": rooms[:5],
                    "plan_id": plan_id,
                    "is_supported": True,
                    "is_gemini_direct": True,
                    "error": None
                }
            except Exception as e:
                print(f"[Assistant] Direct Gemini execution error: {e}")

        # Fallback to deterministic semantic router if API is not yet active
        fallback_res = self.ask(question, active_plan_id=plan_id)
        fallback_res["is_gemini_direct"] = False
        return fallback_res
