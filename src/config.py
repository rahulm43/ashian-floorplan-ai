"""
Configuration settings for ASHIAN Floor Plan Understanding System.
Audited and updated with exact multi-class RGB signatures across Kaggle CVC-FPP dataset.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
MASKS_DIR = DATASET_DIR / "masks"

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "ashian.db"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EXTRACTED_DATA_DIR = OUTPUTS_DIR / "extracted_data"
VISUALIZATIONS_DIR = OUTPUTS_DIR / "visualizations"
REPORTS_DIR = OUTPUTS_DIR / "reports"

EVALUATION_DIR = PROJECT_ROOT / "evaluation"
TEST_QUESTIONS_PATH = EVALUATION_DIR / "test_questions.json"
EVALUATION_RESULTS_PATH = EVALUATION_DIR / "results.json"
EVALUATION_REPORT_PATH = EVALUATION_DIR / "report.md"

# Ensure directories exist
for directory in [
    DATASET_DIR, IMAGES_DIR, MASKS_DIR, DATABASE_DIR,
    OUTPUTS_DIR, EXTRACTED_DATA_DIR, VISUALIZATIONS_DIR,
    REPORTS_DIR, EVALUATION_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# Extraction & CV Hyperparameters
MIN_ROOM_AREA_PX = 800       # Minimum pixel area for a valid room region
MIN_DOOR_AREA_PX = 30        # Minimum pixel area for a door
MAX_DOOR_AREA_PX = 20000     # Maximum pixel area for a door
MIN_WINDOW_AREA_PX = 30      # Minimum pixel area for a window
MAX_WINDOW_AREA_PX = 20000   # Maximum pixel area for a window
MIN_WALL_AREA_PX = 100       # Minimum pixel area for a wall region

ADJACENCY_DILATION_RADIUS = 30  # Pixel radius for door/window room association

# Audited Ground Truth Semantic Class Multi-RGB Signatures
# The Kaggle CVC-FPP dataset contains two primary annotation styles:
# 1. Rooms: Teal [0, 142, 142] (Subset A) AND Coral Orange [255, 142, 70] (Subset B)
# 2. Walls: Soft Ice Blue [175, 216, 248]
# 3. Doors: Olive/Lime Green [139, 186, 0] AND Red/Coral [214, 70, 70]
# 4. Windows: Golden Yellow / Amber [246, 189, 15]
# 5. Background: Pure Black [0, 0, 0]
CLASS_COLOR_SIGNATURES = {
    "room": [
        (0, 142, 142),     # Dark Teal / Cyan (Subset A)
        (255, 142, 70),    # Coral Orange (Subset B)
    ],
    "wall": [
        (175, 216, 248),   # Soft Ice Blue
    ],
    "door": [
        (139, 186, 0),     # Lime Green Doors
        (214, 70, 70),     # Red / Coral Portals
    ],
    "window": [
        (246, 189, 15),    # Golden Yellow / Amber
    ],
    "background": [
        (0, 0, 0),         # Pure Black
    ]
}

# Legacy single-color mapping alias for backward compatibility
CLASS_COLORS = {
    "room": (255, 142, 70),
    "wall": (175, 216, 248),
    "door": (139, 186, 0),
    "window": (246, 189, 15),
    "background": (0, 0, 0)
}

# Color tolerance radius in RGB Euclidean distance
COLOR_TOLERANCE = 38

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.5-flash")
