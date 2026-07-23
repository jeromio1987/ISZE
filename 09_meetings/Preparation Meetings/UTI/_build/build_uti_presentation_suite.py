#!/usr/bin/env python3
"""Rebuild all UTI PMS presentations (IML + FY) and presentation map."""
from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
BUILD = Path(__file__).resolve().parent


def run(name: str) -> None:
    script = BUILD / name
    print(f"\n=== {name} ===")
    subprocess.run([sys.executable, str(script)], check=True)


def write_map() -> None:
    today = date.today().isoformat()
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>UTI Presentation Map — IML · Fiscal Year</title>
<style>
  body {{ font-family: "Segoe UI", Calibri, sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
  h1 {{ color: #CC0E1E; border-bottom: 3px solid #CC0E1E; padding-bottom: 0.35rem; }}
  h2 {{ margin-top: 1.75rem; font-size: 1.05rem; color: #1a2b4a; }}
  a {{ color: #CC0E1E; font-weight: 600; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; margin: 0.5rem 0 1rem; }}
  th {{ background: #1a2b4a; color: #fff; text-align: left; padding: 0.45rem 0.6rem; }}
  td {{ padding: 0.45rem 0.6rem; border-bottom: 1px solid #e5e5e5; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .tag {{ font-size: 0.72rem; background: #f0f0f0; padding: 0.12rem 0.4rem; border-radius: 4px; white-space: nowrap; }}
  .tag.iml {{ background: #e8f0f8; color: #1a3a5c; }}
  .tag.fy {{ background: #fff3cd; color: #856404; }}
  .note {{ background: #fff8f8; border-left: 4px solid #CC0E1E; padding: 0.75rem 1rem; font-size: 0.88rem; margin: 1rem 0; line-height: 1.5; }}
  .archive {{ color: #777; font-size: 0.85rem; }}
  footer {{ margin-top: 2rem; font-size: 0.8rem; color: #777; }}
</style>
</head>
<body>
<h1>UTI presentation map</h1>
<p>All PMS materials below use <strong>IML v7 intervals</strong>, <strong>100% addressable</strong>, and <strong>fiscal-year billing</strong> (ISZE FY = Apr–Mar). Rebuilt {today}.</p>

<div class="note">
  <strong>Methodology (UTI PMS):</strong> Oil / fuel / air <strong>1.25×/yr</strong> (40,000 km @ 50,000 km/yr) · Brake &amp; clutch <strong>0.5×/yr</strong> · Cover capped at <strong>100%</strong> in charts.
  Superseded PRISM N75 / CY-only views are in <code>PMS_Dashboards_Archive/</code>.
</div>

<h2>Show to UTI — PMS</h2>
<table>
  <tr><th>File</th><th>What it shows</th><th>Tags</th></tr>
  <tr>
    <td><a href="ITUK_UTI_PMS_Study_CappedCapture_FY_IML.html">ITUK_UTI_PMS_Study_CappedCapture_FY_IML.html</a></td>
    <td>Family cover snapshot — Filters / Brakes / Clutch vs ITUK benchmark (attached deck, recalculated)</td>
    <td><span class="tag iml">IML</span> <span class="tag fy">FY2025</span></td>
  </tr>
  <tr>
    <td><a href="ITUK_UTI_PMS_Study_CappedCapture_v1.html">ITUK_UTI_PMS_Study_CappedCapture_v1.html</a></td>
    <td>Alias → same as above (legacy filename)</td>
    <td><span class="tag iml">IML</span> <span class="tag fy">FY2025</span></td>
  </tr>
  <tr>
    <td><a href="UTI_PMS_Evolution.html">UTI_PMS_Evolution.html</a></td>
    <td>11 charts — FY2023–FY2025 cover trend, gaps, attach rates, IML schedule table with km</td>
    <td><span class="tag iml">IML</span> <span class="tag fy">FY</span></td>
  </tr>
</table>

<h2>Show to UTI — GPS &amp; narrative</h2>
<table>
  <tr><th>File</th><th>What it shows</th><th>Tags</th></tr>
  <tr>
    <td><a href="UTI_Dashboard_Show.html">UTI_Dashboard_Show.html</a></td>
    <td>GPS wallet, attach, filter mix — toggle FY (default recommended for meeting)</td>
    <td><span class="tag fy">FY toggle</span></td>
  </tr>
  <tr>
    <td><a href="UTI_Meeting_Show_UTI.html">UTI_Meeting_Show_UTI.html</a></td>
    <td>Narrative one-pager · GPS SPU history</td>
    <td>GPS</td>
  </tr>
  <tr>
    <td><a href="UTI_GPS_Stretch_Proposal.pptx">UTI_GPS_Stretch_Proposal.pptx</a></td>
    <td>FY27 stretch proposal — +1.8pp → 38.3% GPS · €3.25M BP · €25K incentive at FY close</td>
    <td><span class="tag fy">FY2027</span> PPT</td>
  </tr>
</table>

<h2>Internal</h2>
<table>
  <tr><th>File</th><th>Notes</th></tr>
  <tr><td><a href="UTI_Dashboard_Internal.html">UTI_Dashboard_Internal.html</a></td><td>Full dashboard + caveats</td></tr>
  <tr><td><a href="UTI_Meeting_Internal.html">UTI_Meeting_Internal.html</a></td><td>Data audit</td></tr>
  <tr><td><a href="PMS_Dashboards_Archive/">PMS_Dashboards_Archive/</a></td><td class="archive">Old PRISM / CY versions (do not use in meeting)</td></tr>
</table>

<h2>Rebuild</h2>
<pre style="background:#f5f5f5;padding:0.75rem;font-size:0.85rem">python _build/build_uti_presentation_suite.py</pre>
<p class="archive">All HTML files use local <code>assets/chart.umd.min.js</code> — works offline.</p>

<footer>ISZE · UTI meeting pack · IML v7 + FY billing engine: <code>_build/uti_iml_fy_engine.py</code></footer>
</body>
</html>"""
    (OUT / "UTI_Presentation_Map.html").write_text(html, encoding="utf-8")
    # Meeting pack points to map
    pack = OUT / "UTI_Meeting_Pack.html"
    pack.write_text(
        pack.read_text(encoding="utf-8").split("<h1>")[0]
        + """<h1>UTI meeting — open here</h1>
<p><a href="UTI_Presentation_Map.html"><strong>→ UTI Presentation Map</strong></a> — all IML + FY materials (start here).</p>
<p class="archive" style="color:#666;font-size:0.9rem">Generated pack · July 2026</p>
<h2>Quick links</h2>
<ul>
  <li><a href="UTI_Presentation_Map.html">UTI_Presentation_Map.html</a></li>
  <li><a href="ITUK_UTI_PMS_Study_CappedCapture_FY_IML.html">PMS family study (FY2025 IML)</a></li>
  <li><a href="UTI_PMS_Evolution.html">PMS FY evolution</a></li>
  <li><a href="UTI_Dashboard_Show.html">GPS dashboard</a></li>
  <li><a href="UTI_GPS_Stretch_Proposal.pptx">GPS stretch proposal (PPT)</a></li>
</ul>
</body>
</html>""",
        encoding="utf-8",
    )
    print(f"Wrote {OUT / 'UTI_Presentation_Map.html'}")


def main() -> None:
    run("ensure_offline_assets.py")
    run("build_uti_pms_capped_study.py")
    run("build_uti_pms_evolution.py")
    run("_build_uti_dashboard.py")
    run("build_uti_gps_stretch_slide.py")
    write_map()
    print("\nDone — open UTI_Presentation_Map.html")


if __name__ == "__main__":
    main()
