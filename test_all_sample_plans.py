import cv2
import numpy as np
from PIL import Image

room_colors = [np.array([0, 142, 142], dtype=np.float32), np.array([255, 142, 70], dtype=np.float32)]
door_colors = [np.array([139, 186, 0], dtype=np.float32), np.array([214, 70, 70], dtype=np.float32)]
window_colors = [np.array([246, 189, 15], dtype=np.float32)]
wall_colors = [np.array([175, 216, 248], dtype=np.float32)]

def get_multi_color_mask(img_rgb, targets, tolerance=35):
    combined = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
    for tgt in targets:
        diff = img_rgb.astype(np.float32) - tgt
        dist = np.sqrt(np.sum(diff ** 2, axis=-1))
        matched = (dist <= tolerance).astype(np.uint8) * 255
        combined = cv2.bitwise_or(combined, matched)
    return combined

sample_plans = [1, 2, 3, 4, 10, 12]

for pid in sample_plans:
    mask_path = f"dataset/masks/{pid} (2).png"
    mask = np.array(Image.open(mask_path).convert("RGB"))
    
    room_mask = get_multi_color_mask(mask, room_colors)
    door_mask = get_multi_color_mask(mask, door_colors)
    window_mask = get_multi_color_mask(mask, window_colors)
    wall_mask = get_multi_color_mask(mask, wall_colors)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned_room = cv2.morphologyEx(room_mask, cv2.MORPH_CLOSE, kernel)
    
    n_rooms, _, r_stats, _ = cv2.connectedComponentsWithStats(cleaned_room, connectivity=8)
    rooms = [i for i in range(1, n_rooms) if r_stats[i, cv2.CC_STAT_AREA] >= 800]
    
    n_doors, _, d_stats, _ = cv2.connectedComponentsWithStats(door_mask, connectivity=8)
    doors = [i for i in range(1, n_doors) if 30 <= d_stats[i, cv2.CC_STAT_AREA] <= 20000]
    
    n_wins, _, w_stats, _ = cv2.connectedComponentsWithStats(window_mask, connectivity=8)
    windows = [i for i in range(1, n_wins) if 30 <= w_stats[i, cv2.CC_STAT_AREA] <= 20000]
    
    print(f"Plan {pid:2d} -> Rooms: {len(rooms):2d} | Doors: {len(doors):2d} | Windows: {len(windows):2d} | Wall Px: {np.count_nonzero(wall_mask):,}")
