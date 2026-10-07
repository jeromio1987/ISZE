"""Freeze a snapshot of the page for stable testing, and report what is in it."""
from __future__ import annotations

import datetime as dt
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OPS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops")
QA = OPS / "_qa_charts"

src = OPS / "ISZE_Backlog_IML_WK41.html"
dst = QA / "frozen_now.html"
shutil.copy2(src, dst)

s = src.read_text(encoding="utf-8")
b = re.search(r'"build":"([^"]+)"', s)
print("page mtime       :", dt.datetime.fromtimestamp(src.stat().st_mtime))
print("builder mtime    :", dt.datetime.fromtimestamp((OPS / "_build_backlog_iml_wk41.py").stat().st_mtime))
print("build stamp      :", b.group(1) if b else "none")
print("animation:false  :", s.count("animation:false"))
print("my defensive layr:", "Fallbacks used during this render" in s)
print("warning slots    :", s.count('id="warn-p-'))
print("other writer text:", "deep dive for that distributor" in s)
print("frozen snapshot  :", dst)
