from PIL import Image
from pathlib import Path

vis_dir = Path("outputs/visualizations")
img1 = vis_dir / "room_seg_1.png"
img2 = vis_dir / "annotated_plan_1.png"
img3 = vis_dir / "openings_1.png"

print("room_seg_1 exists:", img1.exists(), "size:", Image.open(img1).size if img1.exists() else None)
print("annotated_plan_1 exists:", img2.exists(), "size:", Image.open(img2).size if img2.exists() else None)
print("openings_1 exists:", img3.exists(), "size:", Image.open(img3).size if img3.exists() else None)
