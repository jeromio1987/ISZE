"""Atomic install: write content to a temp file beside the target, then os.replace.

Truncating writes on some files in this workspace fail with OSError [Errno 22];
os.replace over a temp file in the same directory works.

Usage: python _atomic_install.py <source> <target>
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
target = Path(sys.argv[2])
if not src.exists():
    raise SystemExit(f"source missing: {src}")
tmp = target.with_name(target.name + ".tmp_install")
shutil.copy2(src, tmp)
os.replace(tmp, target)
print(f"installed {src} -> {target} ({target.stat().st_size} bytes)")
