import os
from PIL import Image
import numpy as np
from collections import defaultdict

masks_dir = r"dataset/masks"
mask_files = [f for f in os.listdir(masks_dir) if f.endswith(".png")]

color_histogram = defaultdict(int)
plan_color_breakdown = {}

for mf in sorted(mask_files)[:25]:
    path = os.path.join(masks_dir, mf)
    arr = np.array(Image.open(path).convert("RGB"))
    colors, counts = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    plan_color_breakdown[mf] = []
    
    total = arr.shape[0] * arr.shape[1]
    for c, cnt in zip(colors, counts):
        if cnt > 1000: # filter tiny antialiasing
            c_tuple = tuple(c.tolist())
            color_histogram[c_tuple] += cnt
            pct = (cnt / total) * 100
            plan_color_breakdown[mf].append((c_tuple, cnt, round(pct, 2)))

print(f"Audited {len(plan_color_breakdown)} masks.")
print("\nGlobal Most Common Colors (> 0.05% total dataset volume):")
for c, total_cnt in sorted(color_histogram.items(), key=lambda x: -x[1])[:15]:
    print(f"  RGB {list(c)}: {total_cnt:,} total px")

print("\nPer-Plan Top Non-Black Colors in Masks:")
for mf in list(plan_color_breakdown.keys())[:10]:
    non_black = [x for x in plan_color_breakdown[mf] if x[0] != (0, 0, 0)]
    print(f"\n{mf}:")
    for c, cnt, pct in non_black[:6]:
        print(f"   RGB {list(c)}: {cnt:,} px ({pct}%)")
