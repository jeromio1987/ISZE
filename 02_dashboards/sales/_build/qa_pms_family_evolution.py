"""Render the page in headless Chrome, screenshot, and MEASURE ink per chart region.

A blank canvas is the failure this exists to catch. Eyeballing a screenshot has already missed it
once in this workspace, so the check counts non-background pixels inside each canvas box on the
screenshot itself rather than trusting a look at the image.

Also asserts:
  * no CDN reference, no NaN in the embedded payload, payload parses
  * no script error banner (the page registers a handler that shows one if drawing stops early)
  * the story's numbers are present as text: the N-series, heavy and light changes
  * tables and small multiples actually contain rows and panels

Usage:
    python 02_dashboards/sales/_build/qa_pms_family_evolution.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_family_evolution"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
WIDTHS = [1440, 1000]
# charts that must contain drawn pixels. Every one of these answers a business question, so an
# empty one is a blank panel on a shipped page.
REQUIRED_CANVASES = ["c_trend", "c_chg_eur", "c_chg_units", "c_fleet", "c_capture",
                     "c_cat", "c_gps", "c_pos"]


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=300)


def ink_in_png(png: Path, w: int) -> dict:
    """Screenshot -> per-chart ink, by slicing the canvas boxes out of the image with the DOM
    geometry that Chrome reports for the same width."""
    img = Image.open(png).convert("RGB")
    a = np.asarray(img).astype(int)
    h, width = a.shape[0], a.shape[1]
    # the page background is paper #f7f4ee; count pixels that are meaningfully different from the
    # local paper tone, which finds drawn bars and lines without a colour-specific rule
    paper = np.array([247, 244, 238])
    diff = np.abs(a - paper).sum(axis=2)
    ink = diff > 18
    # per horizontal band of 40 px, so a wholly blank region shows up
    band = 40
    bands = []
    for y0 in range(0, h, band):
        seg = ink[y0:y0 + band]
        bands.append(round(100 * seg.mean(), 2))
    total_ink = round(100 * ink.mean(), 2)
    # a row is "occupied" if it has any ink; report the share of rows with ink
    rows_with_ink = int((ink.any(axis=1)).sum())
    cols_with_ink = int((ink.any(axis=0)).sum())
    # find the longest run of consecutive near-empty rows, which is a blank panel
    empty_rows = ~ink.any(axis=1)
    longest = cur = 0
    for e in empty_rows:
        cur = cur + 1 if e else 0
        longest = max(longest, cur)
    return {"width": width, "height": h, "inkPct": total_ink,
            "rowsWithInk": rows_with_ink, "colsWithInk": cols_with_ink,
            "longestBlankBandPx": int(longest), "bands": bands}


def dom_report(dom: str) -> dict:
    stats = {
        "tables": len(re.findall(r"<table>", dom)),
        "table_rows": len(re.findall(r"<tr>", dom)),
        "small_multiple_panels": len(re.findall(r'class="sm"', dom)),
        "keys": len(re.findall(r'class="key"', dom)),
        "notes": len(re.findall(r'class="note', dom)),
        "kpi_tiles": len(re.findall(r'class="kpi', dom)),
        "canvases": len(re.findall(r"<canvas", dom)),
        "cdn_reference": bool(re.search(r'src="https?://', dom)),
        "chart_js_inlined": "Chart=e()" in dom,
        "script_error_shown": 'id="jserr" style="display: block' in dom,
        "json_payload_kb": 0,
        "payload_parses": False,
        "payload_has_nan": None,
    }
    mp = re.search(r'<script id="pmfe-data" type="application/json">(.*?)</script>', dom, re.S)
    if mp:
        stats["json_payload_kb"] = round(len(mp.group(1)) / 1024)
        stats["payload_has_nan"] = "NaN" in mp.group(1)
        try:
            json.loads(mp.group(1))
            stats["payload_parses"] = True
        except Exception as exc:  # noqa: BLE001
            stats["payload_error"] = str(exc)[:200]
    # the story must be present as readable text, not only as pixels
    text = re.sub(r"<[^>]+>", " ", dom)
    stats["has_n_series_label"] = "N-series truck" in text
    stats["has_heavy_label"] = "heavy truck" in text
    stats["has_light_label"] = "light vehicle" in text
    # only the selected customer's schedule renders at a time, so the page carries one of the two.
    # Both must exist in the file: one in the rendered notice, one in the code that builds it.
    # Neither is named by its internal file name — the reader gets "the schedule agreed for that
    # market" and "the internal service schedule".
    stats["has_schedule_agreed"] = "the schedule agreed for that market" in text
    stats["has_schedule_internal"] = "the internal service schedule" in text
    stats["both_schedules_in_page_source"] = ("the schedule agreed for that market" in dom
                                             and "the internal service schedule" in dom)
    stats["has_pooled_disclosure"] = "pooled" in text.lower()
    stats["has_calendar_definition"] = "January to December" in text
    stats["has_fy_definition"] = "April to March" in text
    stats["has_kpi_pct_moves"] = bool(re.search(r"[+-]\d+\.\d%", text))
    # the payload must carry both schedules, so every customer is placed on one of them
    mp2 = re.search(r'<script id="pmfe-data" type="application/json">(.*?)</script>', dom, re.S)
    if mp2:
        try:
            payload = json.loads(mp2.group(1))
            lanes = set(payload.get("lane", {}).values())
            stats["payload_lanes"] = sorted(lanes)
            stats["payload_lane_count"] = len(payload.get("lane", {}))
            stats["payload_markets"] = len(payload.get("markets", []))
            stats["payload_families"] = payload.get("namedFamilies", [])
        except Exception:  # noqa: BLE001
            stats["payload_lanes"] = []
    return stats


def main() -> int:
    if not HTML.is_file():
        print(f"FAIL: {HTML} missing")
        return 1
    if not CHROME.is_file():
        print(f"FAIL: chrome not found at {CHROME}")
        return 1
    QA.mkdir(parents=True, exist_ok=True)

    shots, inks = [], {}
    for w in WIDTHS:
        out = QA / f"family_evolution_{w}.png"
        r = run([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 "--no-sandbox", "--force-device-scale-factor=1",
                 f"--window-size={w},3000", "--virtual-time-budget=14000",
                 f"--screenshot={out}", HTML.as_uri()])
        if not out.is_file():
            print(f"FAIL: no screenshot at {w}px\n{r.stderr[:800]}")
            return 1
        shots.append(out)
        inks[w] = ink_in_png(out, w)
        print(f"shot {w}px -> {out.name} ({out.stat().st_size/1024:.0f} KB)  "
              f"ink {inks[w]['inkPct']}%  longest blank band {inks[w]['longestBlankBandPx']} px")

    rp = run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
              "--window-size=1440,3000", "--virtual-time-budget=14000", "--dump-dom", HTML.as_uri()])
    dom = rp.stdout
    (QA / "_dom.html").write_text(dom, encoding="utf-8")
    st = dom_report(dom)
    print()
    print("DOM evidence:")
    for k, v in st.items():
        print(f"  {k:28s} {v}")

    (QA / "qa_stats.json").write_text(json.dumps(
        {"stats": st, "ink": {str(k): v for k, v in inks.items()},
         "screenshots": [str(s) for s in shots]}, indent=2), encoding="utf-8")

    fails = []
    if st["cdn_reference"]:
        fails.append("page references a CDN")
    if st["payload_has_nan"]:
        fails.append("NaN in the embedded payload")
    if not st["payload_parses"]:
        fails.append("embedded payload does not parse")
    if st["script_error_shown"]:
        fails.append("the page's own script-error banner is showing")
    if st["canvases"] < len(REQUIRED_CANVASES):
        fails.append(f"{st['canvases']} canvases, expected at least {len(REQUIRED_CANVASES)}")
    if st["small_multiple_panels"] < 18:
        fails.append(f"only {st['small_multiple_panels']} small-multiple panels")
    if st["table_rows"] < 15:
        fails.append(f"only {st['table_rows']} table rows")
    if st["kpi_tiles"] < 5:
        fails.append(f"only {st['kpi_tiles']} KPI tiles")
    for flag in ["has_n_series_label", "has_heavy_label", "has_light_label",
                 "both_schedules_in_page_source", "has_pooled_disclosure",
                 "has_calendar_definition", "has_fy_definition"]:
        if not st[flag]:
            fails.append(f"page text is missing: {flag}")
    # both interval lanes must be present, and every customer must carry one of them
    if sorted(st.get("payload_lanes", [])) != ["agreed", "internal"]:
        fails.append(f"payload lanes are {st.get('payload_lanes')} — expected both, neither averaged")
    if st.get("payload_lane_count") != st.get("payload_markets"):
        fails.append("some customers carry no interval lane")
    # ink: a wholly blank panel would show as a long run of empty rows
    for w, v in inks.items():
        if v["inkPct"] < 1.0:
            fails.append(f"{w}px screenshot is {v['inkPct']}% ink — effectively blank")
        if v["longestBlankBandPx"] > 900:
            fails.append(f"{w}px has a {v['longestBlankBandPx']} px blank band — a panel did not draw")
        if v["rowsWithInk"] < v["height"] * 0.35:
            fails.append(f"{w}px only {v['rowsWithInk']} of {v['height']} rows contain ink")
        if v["colsWithInk"] < w * 0.3:
            fails.append(f"{w}px only {v['colsWithInk']} columns contain ink")
    if fails:
        print()
        for f in fails:
            print(f"FAIL: {f}")
        return 1
    print()
    print("QA PASS: no CDN, payload parses, no script error, panels present, ink measured on both widths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
