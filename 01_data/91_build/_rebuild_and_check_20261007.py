"""Rebuild the page and syntax-check the emitted script.

Escaping-heavy one-liners keep breaking in PowerShell, so the check lives here instead.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BUILDER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\_build_backlog_iml_wk41.py")
HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\ISZE_Backlog_IML_WK41.html")
TMP = Path(r"C:\Users\jerom\Desktop\claude\ISZE\_tmp_page.js")

r = subprocess.run([sys.executable, str(BUILDER)], capture_output=True, text=True, encoding="utf-8", errors="replace")
tail = [ln for ln in (r.stdout or "").splitlines() if ln.startswith("wrote") or "Error" in ln]
print("builder:", " | ".join(tail) or "(no 'wrote' line)")
if r.returncode != 0:
    print("BUILD FAILED")
    print((r.stderr or "")[-1500:])
    raise SystemExit(1)

s = HTML.read_text(encoding="utf-8")
m = re.search(r'"build":"([^"]+)"', s)
print("build stamp :", m.group(1) if m else "none")
print("size MB     :", round(len(s) / 1048576, 2))

blocks = re.findall(r"<script>(.*?)</script>", s, re.S)
TMP.write_text(blocks[-1], encoding="utf-8")
c = subprocess.run(["node", "--check", str(TMP)], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("JS parse    :", "OK" if c.returncode == 0 else "FAIL")
if c.returncode != 0:
    print((c.stderr or "")[:900])
