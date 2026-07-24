#!/usr/bin/env python3
"""
Assemble the six offset visuals into ONE self-contained static HTML page.
Zero server, double-click to open, drop on Netlify. Plotly is inlined once.

  python scripts/build_static_dashboard.py
  -> Data/derived/insights/offset_insights.html
"""
from __future__ import annotations

import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR  # noqa: E402
from modules import advanced_visuals as av  # noqa: E402

OUT = DERIVED_DIR / "insights" / "offset_insights.html"
OUT.parent.mkdir(parents=True, exist_ok=True)

HIGHLIGHT = "ITUK"

SECTIONS = [
    ("1 · Distributor Movement", av.fig_trajectory_quiver(DERIVED_DIR, HIGHLIGHT)),
    ("2 · Lumpiness → Airfreight", av.fig_lumpiness_airfreight(DERIVED_DIR)),
    ("3 · Demand-Flow Sankey", av.fig_demand_flow_sankey(DERIVED_DIR)),
    ("4 · VOR Pricing Power", av.fig_vor_pricing_power(DERIVED_DIR, HIGHLIGHT)),
    ("5 · Premium vs Defection", av.fig_premium_defection(DERIVED_DIR, HIGHLIGHT)),
    ("6 · Capture-Ceiling Bridge", av.fig_capture_ceiling(DERIVED_DIR, HIGHLIGHT)),
]

CSS = """
<style>
 body{font-family:Segoe UI,sans-serif;margin:0;background:#F4F6F9;color:#1B3A6B;}
 .hero{background:linear-gradient(120deg,#1B3A6B,#2C5AA0 60%,#E87722);color:#fff;padding:2rem;}
 .hero h1{margin:0;font-size:2rem;} .hero p{margin:.4rem 0 0;color:#E8F0FA;}
 .card{background:#fff;margin:1.25rem auto;max-width:1100px;border-radius:12px;
   box-shadow:0 1px 4px rgba(0,0,0,.08);padding:.5rem 1rem 1rem;}
 .note{max-width:1100px;margin:1rem auto;color:#C62828;font-size:.85rem;}
</style>
"""

parts = [CSS,
         '<div class="hero"><h1>PRISM — Offset Insights</h1>'
         f'<p>Six cross-data visuals · highlight: {HIGHLIGHT} · all figures from real sales_fact</p></div>',
         '<div class="note">⚠️ The Sankey "Leakage" leg is an INFERENCE (under-service gap), '
         'not a measured competitor figure — internal use only.</div>']

for i, (title, fig) in enumerate(SECTIONS):
    html = fig.to_html(full_html=False, include_plotlyjs=("cdn" if i == 0 else False))
    parts.append(f'<div class="card"><h2>{title}</h2>{html}</div>')

OUT.write_text(
    "<!doctype html><html><head><meta charset='utf-8'><title>PRISM Offset Insights</title></head>"
    "<body>" + "".join(parts) + "</body></html>",
    encoding="utf-8",
)
print(f"-> {OUT}")
