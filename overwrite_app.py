"""One-time script to overwrite app.py with the clean version."""
import shutil
import os

src = r"c:\Users\PC\hr\app_new.py"
dst = r"c:\Users\PC\hr\app.py"

shutil.copy2(src, dst)
print(f"Copied {src} -> {dst}")
print(f"New file size: {os.path.getsize(dst)} bytes")
