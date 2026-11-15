import cv2
import numpy as np
from PIL import Image

mask_path = r"dataset/masks/1 (2).png"
img_path = r"dataset/images/1.png"

mask = np.array(Image.open(mask_path).convert("RGB"))
img = cv2.imread(img_path)

# Room colors: Teal [0, 142, 142] and Coral [255, 142, 70]
room_colors = [np.array([0, 142, 142], dtype=np.float32), np.array([255, 142, 70], dtype=np.float32)]

# Door colors: Green [139, 186, 0] and Red [214, 70, 70]
door_colors = [np.array([139, 186, 0], dtype=np.float32), np.array([214, 70, 70], dtype=np.float32)]

# Window colors: Yellow [246, 189, 15]
window_colors = [np.array([246, 189, 15], dtype=np.float32)]

# Wall colors: Ice blue [175, 216, 248]
wall_colors = [np.array([175, 216, 248], dtype=np.float32)]

def get_multi_color_mask(img_rgb, targets, tolerance=35):
    combined = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
    for tgt in targets:
        diff = img_rgb.astype(np.float32) - tgt
        dist = np.sqrt(np.sum(diff ** 2, axis=-1))
        matched = (dist <= tolerance).astype(np.uint8) * 255
        combined = cv2.bitwise_or(combined, matched)
    return combined

room_mask = get_multi_color_mask(mask, room_colors)
door_mask = get_multi_color_mask(mask, door_colors)
window_mask = get_multi_color_mask(mask, window_colors)
wall_mask = get_multi_color_mask(mask, wall_colors)

# Connected components on rooms
# Clean morphological closing to avoid splitting single rooms
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
cleaned_room_mask = cv2.morphologyEx(room_mask, cv2.MORPH_CLOSE, kernel)

num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned_room_mask, connectivity=8)

valid_rooms = []
for i in range(1, num_labels):
    area = stats[i, cv2.CC_STAT_AREA]
    if area >= 800: # Min room threshold
        valid_rooms.append((i, area, stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]))

# Connected components on doors
num_doors, d_labels, d_stats, d_centroids = cv2.connectedComponentsWithStats(door_mask, connectivity=8)
valid_doors = [i for i in range(1, num_doors) if 30 <= d_stats[i, cv2.CC_STAT_AREA] <= 20000]

# Connected components on windows
num_wins, w_labels, w_stats, w_centroids = cv2.connectedComponentsWithStats(window_mask, connectivity=8)
valid_wins = [i for i in range(1, num_wins) if 30 <= w_stats[i, cv2.CC_STAT_AREA] <= 20000]

print("=== PLAN 1 EXTRACTION AUDIT WITH MULTI-COLOR MATCHING ===")
print(f"Total room pixels detected : {np.count_nonzero(room_mask):,} px")
print(f"Total valid rooms extracted: {len(valid_rooms)}")
for idx, (lbl, area, w, h) in enumerate(valid_rooms, 1):
    print(f"  Room {idx}: {area:,} px (width={w}, height={h})")

print(f"\nTotal door pixels detected : {np.count_nonzero(door_mask):,} px")
print(f"Total valid doors extracted: {len(valid_doors)}")

print(f"\nTotal window pixels detected: {np.count_nonzero(window_mask):,} px")
print(f"Total valid windows extracted: {len(valid_wins)}")
