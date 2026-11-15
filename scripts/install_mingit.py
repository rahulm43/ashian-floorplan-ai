import os
import urllib.request
import zipfile
from pathlib import Path

target_dir = Path("C:/Users/Lenovo/.local/git")
target_dir.mkdir(parents=True, exist_ok=True)
git_exe = target_dir / "cmd" / "git.exe"

if not git_exe.exists():
    url = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/MinGit-2.47.1-64-bit.zip"
    zip_path = target_dir / "mingit.zip"
    print(f"Downloading MinGit from {url}...")
    urllib.request.urlretrieve(url, zip_path)
    print("Extracting MinGit...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(target_dir)
    if zip_path.exists():
        zip_path.unlink()
    print("MinGit installed successfully!")
else:
    print("MinGit already exists at", git_exe)

print("Git exists:", git_exe.exists())
