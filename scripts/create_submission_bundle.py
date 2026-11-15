"""
Script to create clean submission zip bundle for ASHIAN project.
"""

import os
from pathlib import Path
import zipfile

def create_bundle():
    project_root = Path(__file__).resolve().parent.parent
    zip_path = project_root / "ASHIAN_Submission_Bundle.zip"
    
    items = [
        "app.py",
        "run_pipeline.py",
        "requirements.txt",
        "README.md",
        ".env.example",
        "src",
        "database",
        "evaluation",
        "outputs",
        "docs",
        "tests"
    ]
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item_name in items:
            item_path = project_root / item_name
            if not item_path.exists():
                continue
            if item_path.is_file():
                zf.write(item_path, item_name)
            else:
                for root, dirs, files in os.walk(item_path):
                    # Exclude caches
                    if "__pycache__" in root or ".pytest_cache" in root:
                        continue
                    for file in files:
                        if file.endswith(".pyc") or file.endswith(".tmp"):
                            continue
                        full_file = Path(root) / file
                        rel_path = full_file.relative_to(project_root)
                        zf.write(full_file, str(rel_path))
                        
    size_mb = round(zip_path.stat().st_size / (1024 * 1024), 2)
    print(f"Bundle successfully created: {zip_path} ({size_mb} MB)")

if __name__ == "__main__":
    create_bundle()
