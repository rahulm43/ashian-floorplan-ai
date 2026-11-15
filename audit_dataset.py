import os
from PIL import Image
import numpy as np

images_dir = r"dataset/images"
masks_dir = r"dataset/masks"

sample_ids = [1, 2, 3, 4, 10, 12]

print("=" * 70)
print("  DATASET INTEGRITY & PAIRING AUDIT")
print("=" * 70)

for pid in sample_ids:
    img_name = f"{pid}.png"
    mask_name = f"{pid} (2).png"
    
    img_path = os.path.join(images_dir, img_name)
    mask_path = os.path.join(masks_dir, mask_name)
    
    img_exists = os.path.exists(img_path)
    mask_exists = os.path.exists(mask_path)
    
    print(f"\n--- PLAN {pid} ---")
    print(f"Image: {img_name} (Exists: {img_exists})")
    print(f"Mask : {mask_name} (Exists: {mask_exists})")
    
    if img_exists and mask_exists:
        with Image.open(img_path) as im:
            im_size = im.size
            im_mode = im.mode
        with Image.open(mask_path) as mk:
            mk_size = mk.size
            mk_mode = mk.mode
            mk_colors = mk.getcolors(maxcolors=256)
        
        print(f"Image Size: {im_size}, Mode: {im_mode}")
        print(f"Mask Size : {mk_size}, Mode: {mk_mode}")
        if im_size != mk_size:
            print(f"⚠️ MISMATCH: Image size {im_size} != Mask size {mk_size}!")
        else:
            print("✓ Dimensions match.")
            
        # Inspect mask numpy array
        mk_arr = np.array(Image.open(mask_path).convert("RGB"))
        colors, counts = np.unique(mk_arr.reshape(-1, 3), axis=0, return_counts=True)
        sorted_idx = np.argsort(-counts)
        print(f"Total unique RGB colors in mask: {len(colors)}")
        print("Top 8 colors by pixel count:")
        total_px = mk_arr.shape[0] * mk_arr.shape[1]
        for idx in sorted_idx[:8]:
            c = colors[idx]
            cnt = counts[idx]
            pct = (cnt / total_px) * 100
            print(f"  RGB {c.tolist()}: {cnt:,} px ({pct:.2f}%)")
