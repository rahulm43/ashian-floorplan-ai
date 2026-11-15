import os
from PIL import Image
import numpy as np
from collections import defaultdict

masks_dir = r"dataset/masks"
mask_files = sorted([f for f in os.listdir(masks_dir) if f.endswith(".png")])

print(f"Total masks found: {len(mask_files)}", flush=True)

# Sample 15 diverse plans
sample_files = mask_files[:15]

for mf in sample_files:
    path = os.path.join(masks_dir, mf)
    img = Image.open(path).convert("RGB")
    arr = np.array(img)[::4, ::4] # 16x subsampling for ultra-fast audit
    
    colors, counts = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    sorted_idx = np.argsort(-counts)
    
    total = arr.shape[0] * arr.shape[1]
    non_black = []
    for idx in sorted_idx:
        c = tuple(colors[idx].tolist())
        cnt = counts[idx]
        pct = (cnt / total) * 100
        if c != (0, 0, 0) and pct > 0.05:
            non_black.append((c, cnt, round(pct, 2)))
            
    print(f"\nMask: {mf} (Size: {img.size})", flush=True)
    for c, cnt, pct in non_black[:6]:
        print(f"   RGB {list(c)}: {pct}%", flush=True)
