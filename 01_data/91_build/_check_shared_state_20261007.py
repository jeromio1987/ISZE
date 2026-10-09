"""Check the current state of the shared page files, because another session is editing too."""
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OPS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops")
files = [
    OPS / "ISZE_Backlog_IML_WK41.html",
    OPS / "_build_backlog_iml_wk41.py",
    OPS / "_qa_charts" / "matrix_probe.js",
    OPS / "_qa_charts" / "matrix.csv",
]
now = time.time()
for f in files:
    if not f.exists():
        print(f"MISSING {f.name}")
        continue
    age = (now - f.stat().st_mtime) / 60
    print(f"{f.name:34s} {f.stat().st_size/1024:9.1f} KB  modified {age:6.1f} min ago")

s = (OPS / "ISZE_Backlog_IML_WK41.html").read_text(encoding="utf-8")
m = re.search(r'"build":"([^"]+)"', s)
print()
print("build stamp in payload :", m.group(1) if m else "none")
print("size MB                :", round(len(s) / 1048576, 2))
print("deep-dive blurb present:", "deep dive for that distributor" in s)
print("t-dparts-lines present :", "t-dparts-lines" in s)
print("animation:false count  :", s.count("animation:false"))
print("warn hosts             :", len(re.findall(r'id="warn-p-[a-z]+"', s)))
