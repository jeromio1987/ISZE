#!/usr/bin/env python3
"""Dump the rendered DOM and locate where the page stops painting."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Tonnage_Evolution.html"
OUT = ROOT / "02_dashboards" / "sales" / "_qa_tonnage"
OUT.mkdir(parents=True, exist_ok=True)
DUMP = OUT / "dom_dump.html"

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="domprobe_")
url = "file:///" + str(HTML).replace("\\", "/")
cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
       "--no-default-browser-check", f"--user-data-dir={prof}",
       "--virtual-time-budget=9000", "--dump-dom", url]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
DUMP.write_text(r.stdout or "", encoding="utf-8")
print("exit", r.returncode, "stdout chars", len(r.stdout or ""))
err = (r.stderr or "")
err_lines = [x for x in err.splitlines() if x.strip() and "DevTools" not in x
             and "Fontconfig" not in x and "GPU" not in x]
print("--- stderr (filtered) ---")
for x in err_lines[:20]:
    print("   ", x)

d = r.stdout or ""


def show(label: str, pat: str, span: int = 220) -> None:
    m = re.search(pat, d, re.S)
    if not m:
        print(f"{label:22s} NOT FOUND")
        return
    snippet = re.sub(r"\s+", " ", m.group(1))[:span]
    print(f"{label:22s} {snippet}")


print()
print("--- rendered DOM ---")
print("canvas tags          ", d.count("<canvas"))
show("kpis", r'<div class="kpis" id="kpis">(.{0,300})')
show("laneNotice", r'<div id="laneNotice">(.{0,300})')
show("sm_grid", r'<div id="sm_grid"[^>]*>(.{0,200})')
show("t_basis", r'<div class="card"><div id="t_basis">(.{0,200})')
show("t_catgap", r'<div id="t_catgap">(.{0,200})')
show("foot", r'<footer id="foot">(.{0,160})')
show("lg_fleet", r'<div class="legend" id="lg_fleet">(.{0,160})')

print()
print("--- how far into the body does painted content go? ---")
# The last element that got populated tells us where JS stopped
markers = [
    ("kpis", 'id="kpis"'), ("laneNotice", 'id="laneNotice"'), ("lg_fleet", 'id="lg_fleet"'),
    ("n_expected", 'id="n_expected"'), ("n_gap", 'id="n_gap"'), ("t_catgap", 'id="t_catgap"'),
    ("n_mix", 'id="n_mix"'), ("n_evo", 'id="n_evo"'), ("n_aim", 'id="n_aim"'),
    ("n_netgap", 'id="n_netgap"'), ("sm_grid", 'id="sm_grid"'), ("n_sm", 'id="n_sm"'),
    ("n_gps", 'id="n_gps"'), ("n_pos", 'id="n_pos"'), ("t_basis", 'id="t_basis"'),
    ("foot", 'id="foot"'),
]
for label, token in markers:
    i = d.find(token)
    if i < 0:
        print(f"  {label:14s} marker absent")
        continue
    # look at the ~400 chars after the marker: is there child content?
    seg = d[i:i + 700]
    closed = seg.find("</div>")
    filled = "data-tip" in seg or "<table" in seg or "<canvas" in seg or "kpi" in seg
    print(f"  {label:14s} offset {i:6d}  populated={filled}")
