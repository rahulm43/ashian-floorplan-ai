import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.assistant import AshianAssistant

assistant = AshianAssistant()

test_queries = [
    "What is the smallest room in plan 1?",
    "What is the total room area in plan 12?",
    "Which room in plan 1 has the most windows?",
    "How many doors does plan 10 have?",
    "How many windows does plan 1 have?",
    "Which plans have more than 5 windows?",
    "Which plan has the highest number of rooms?",
    "What is the total number of doors across all plans?"
]

print("--- Testing Extended Architectural Questions ---")
for q in test_queries:
    res = assistant.ask_gemini_direct(q)
    print(f"\nQ: {q}")
    print(f"A: {res['answer']}")
    print(f"SQL: {res.get('sql_query')}")
