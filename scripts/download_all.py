import json
import os
import urllib.request
import time
import re

with open("all_captured_urls.json", "r") as f:
    data = json.load(f)

x_urls = data["x"]
y_urls = data["y"]

images_dir = r"dataset/images"
masks_dir = r"dataset/masks"
os.makedirs(images_dir, exist_ok=True)
os.makedirs(masks_dir, exist_ok=True)

def get_id(fname):
    m = re.match(r"^(\d+)", fname)
    return int(m.group(1)) if m else None

# Download Y masks first
print(f"Starting download of {len(y_urls)} masks...", flush=True)
for fname, url in y_urls.items():
    dest = os.path.join(masks_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        continue
    print(f"Downloading mask {fname}...", flush=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as out_f:
                out_f.write(resp.read())
            print(f"Downloaded {fname} ({os.path.getsize(dest)} bytes)", flush=True)
            break
        except Exception as e:
            print(f"Error {fname} (attempt {attempt}): {e}", flush=True)
            time.sleep(1)

# Download missing X
print(f"Starting download of missing images...", flush=True)
for fname, url in x_urls.items():
    dest = os.path.join(images_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        continue
    print(f"Downloading image {fname}...", flush=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as out_f:
                out_f.write(resp.read())
            print(f"Downloaded {fname} ({os.path.getsize(dest)} bytes)", flush=True)
            break
        except Exception as e:
            print(f"Error {fname} (attempt {attempt}): {e}", flush=True)
            time.sleep(1)

images = set(os.listdir(images_dir))
masks = set(os.listdir(masks_dir))
print(f"Total images on disk: {len(images)}", flush=True)
print(f"Total masks on disk: {len(masks)}", flush=True)

pairs = []
for img in sorted(images, key=lambda x: get_id(x) or 9999):
    pid = get_id(img)
    mask_name = f"{pid} (2).png"
    if mask_name in masks:
        pairs.append((pid, img, mask_name))

print(f"Total matched pairs: {len(pairs)}", flush=True)
print(f"Matched plan IDs: {[p[0] for p in pairs]}", flush=True)
