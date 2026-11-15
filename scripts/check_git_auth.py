import os
import subprocess

print("GITHUB_TOKEN in env:", "GITHUB_TOKEN" in os.environ)
print("GH_TOKEN in env:", "GH_TOKEN" in os.environ)

# Check Windows credential manager for github.com
try:
    res = subprocess.run(["cmd.exe", "/c", "cmdkey /list | findstr /i github"], capture_output=True, text=True)
    print("cmdkey output:", res.stdout.strip())
except Exception as e:
    print("cmdkey error:", e)
