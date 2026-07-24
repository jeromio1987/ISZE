#!/usr/bin/env python3
"""Fix broken dashboard links, dedupe overlays, archive superseded HTML."""
from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DASHBOARDS_DIR, DERIVED_DIR, ISZE_ROOT, TENDER_MONITOR_DIR  # noqa: E402

DASH = DASHBOARDS_DIR
ARCHIVE = DASH / "_archive"

LINK_FIXES = [
    ("ISUZU_UIO_Dashboard_2026_v11.html", "ISUZU_UIO_Dashboard_2026_v18.html"),
]

REDIRECTS = [
    {
        "name": "ISZE_GPS_Network_SPU_Dashboard.html",
        "target": "ISZE_GPS_Dashboard_v9.html",
        "title": "Network GPS (legacy v8)",
        "reason": "Superseded by GPS v9 — full CY2025 LCV+CV warranty split, UIO v18, max-spend traffic lights.",
    },
    {
        "name": "ISZE_GPS_TargetStudy_Reconciliation_Dashboard.html",
        "target": "ISZE_GPS_Dashboard_v9.html",
        "title": "ITUK Target Study reconciliation",
        "reason": "Merged into GPS v9 (ITUK Target Study + business-plan tab).",
    },
]

OVERLAY_RE = re.compile(
    r"(?:<div class='card' style='margin-top:16px'><div class='sec-title'>ISZE · GPS × AIM overlay.*?</div>\s*)+",
    re.DOTALL,
)
MARKER_GOLDEN = "<!-- ISZE_GOLDEN_GPS_OVERLAY -->"


def _redirect_html(title: str, target: str, reason: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0;url={target}">
<title>Redirect — {title}</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:48px auto;max-width:640px;padding:0 20px;color:#1a1a1a}}
a{{color:#CC0E1E}}</style></head><body>
<h1>{title}</h1>
<p>Superseded <strong>{datetime.now().strftime('%Y-%m-%d')}</strong>. Use
<a href="{target}">{target}</a>.</p>
<p>{reason}</p>
<p>Archived copy: <code>Dashboards/_archive/</code></p>
</body></html>
"""


def _dash_html(name: str) -> Path:
    """Resolve dashboard HTML by basename (02_dashboards themed subfolders)."""
    direct = DASH / name
    if direct.is_file():
        return direct
    hits = [p for p in DASH.rglob(name) if "_archive" not in p.parts]
    return hits[0] if hits else direct


def fix_links() -> int:
    n = 0
    for path in DASH.rglob("*.html"):
        if "_archive" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in LINK_FIXES:
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            print(f"  links: {path.name}")
            n += 1
    return n


def dedupe_golden_overlay() -> None:
    path = _dash_html("ITUK_ZEV_Golden_Window_Dashboard.html")
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if MARKER_GOLDEN not in text:
        return
    before, after = text.split(MARKER_GOLDEN, 1)
    before = OVERLAY_RE.sub("", before)
    path.write_text(before + MARKER_GOLDEN + after, encoding="utf-8")
    print("  deduped ITUK_ZEV_Golden_Window overlay")


def archive_and_redirect(spec: dict) -> None:
    src = _dash_html(spec["name"])
    if not src.is_file():
        print(f"  skip missing {spec['name']}")
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    archived = ARCHIVE / spec["name"].replace(".html", f"_archived_{stamp}.html")
    if not archived.exists():
        shutil.copy2(src, archived)
        print(f"  archived -> {archived.name}")
    src.write_text(
        _redirect_html(spec["title"], spec["target"], spec["reason"]),
        encoding="utf-8",
    )
    print(f"  redirect stub: {spec['name']} -> {spec['target']}")


def archive_uio_v17() -> None:
    src = _dash_html("ISUZU_UIO_Dashboard_2026_v17.html")
    if not src.is_file():
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    archived = ARCHIVE / f"ISUZU_UIO_Dashboard_2026_v17_archived_{stamp}.html"
    if not archived.exists():
        shutil.copy2(src, archived)
        print(f"  archived -> {archived.name}")
    src.write_text(
        _redirect_html(
            "UIO Dashboard v17",
            "ISUZU_UIO_Dashboard_2026_v18.html",
            "Workbook upgraded to v18 (Jun 2026). PRISM pipeline reads v18 via config.py.",
        ),
        encoding="utf-8",
    )
    print("  redirect stub: ISUZU_UIO_Dashboard_2026_v17.html -> v18")


def write_open_issues() -> None:
    out = DERIVED_DIR / "_data_integrity_open_issues.md"
    lines = [
        "# Data integrity — open issues",
        "",
        f"**Updated:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "Pipeline verification: **green** (see `_verification_report.md`). Items below are **source gaps** or **known limitations**, not build failures.",
        "",
        "## Cannot fix without new source data",
        "",
        "| ID | Issue | Impact | Action owner |",
        "|---|---|---|---|",
        "| **UMI-WARR** | Israel LCV absent from `Warranty_LCV_2025.xlsx` (`DistributorName` has no Israel/UMI rows) | UMI ex-warranty GPS overstated; `warranty_data_gap=true` | ISZJ claim export / warranty team |",
        "| **CV-BLANK** | CV warranty `Sheet4` has €314K under blank country bucket | Ireland/Portugal CV warranty are lower bounds | Source file cleanup in claim pivot |",
        "| **IRE-CV** | Ireland CV warranty 82% price-map coverage | CV component undercounted | Accept or re-price from ITUK map |",
        "| **PT-CV** | Portugal CV warranty 52% price-map coverage | CV component undercounted | Same as above |",
        "",
        "## Out of PMS/GPS exercise scope (by design)",
        "",
        "| Market | Why |",
        "|---|---|",
        "| UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE | Bill parts but not in 18-db GPS-base / PMS parc config |",
        "| MIDI (FR, IT, ES…) | LCV warranty in file but not separate GPS calculator rows |",
        "",
        "## Dashboard / feed staleness (monitor)",
        "",
        "| Item | Status |",
        "|---|---|",
        "| `tender_data.json` | Refresh via `04_tools/ISZE_Tender_Monitor_Install/publish_tender.ps1` when tenders needed |",
        "| `metrics_snapshot.json` | Run `build_metrics_snapshot.py` after pipeline post-verify |",
        "| Competitiveness IAM scrape | No data-as-of stamp — scrape may be stale |",
        "| Streamlit `pages/2_GPS.py` | Live calc without warranty toggle — use GPS v9 HTML or Evidence `/gps` |",
        "",
        "## Fixed this session",
        "",
        "- GPS warranty wired into `gps_spu_by_distributor.csv` + `isze_data.json`",
        "- PMS per-DB summary for 18 distributors",
        "- Broken `v11` UIO links → `v18`",
        "- Superseded GPS HTML → redirect to v9",
        "- UIO v17 → redirect to v18 (full file in `Dashboards/_archive/`)",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote {out.relative_to(ISZE_ROOT)}")


def main() -> int:
    print("patch_dashboard_integrity:")
    n = fix_links()
    dedupe_golden_overlay()
    for spec in REDIRECTS:
        archive_and_redirect(spec)
    archive_uio_v17()
    write_open_issues()
    print(f"done ({n} link patches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
