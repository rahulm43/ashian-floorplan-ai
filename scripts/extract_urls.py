import json
import re
import urllib.parse
import os

transcript_path = r"C:\Users\Lenovo\.gemini\antigravity\brain\32020c53-47bb-401e-8cde-96451e0ab971\.system_generated\logs\transcript_full.jsonl"
with open(transcript_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace escaped ampersands first
text_clean = text.replace(r"\\u0026", "&").replace(r"\u0026", "&").replace(r"\\", "")

# Now find all full storage.googleapis.com URLs up to quote or whitespace
pattern = r'https://storage\.googleapis\.com/kagglesdsdata/datasets/5966119/9745714/(?:X|Y)/[^\s"\'\\]+'
matches = set(re.findall(pattern, text_clean))
print(f"Total full matches: {len(matches)}")

x_urls = {}
y_urls = {}

for url in matches:
    path_part = url.split("?")[0]
    fname = os.path.basename(urllib.parse.unquote(path_part))
    # verify it has signature
    if "X-Goog-Signature=" in url:
        if "/X/" in url:
            x_urls[fname] = url
        elif "/Y/" in url:
            y_urls[fname] = url

print(f"Valid signed X count: {len(x_urls)}")
print(f"Valid signed Y count: {len(y_urls)}")
print("Sample Y filename and length:", list(y_urls.keys())[:5])
sample_y = list(y_urls.values())[0]
print("Sample Y URL end:", sample_y[-60:])

with open("all_captured_urls.json", "w") as out_f:
    json.dump({"x": x_urls, "y": y_urls}, out_f, indent=2)
print("Updated all_captured_urls.json successfully!")
