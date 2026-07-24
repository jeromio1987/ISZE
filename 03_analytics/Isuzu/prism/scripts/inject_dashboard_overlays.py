#!/usr/bin/env python3
"""Inject derived tables into static HTML dashboards (marker-based)."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_GPS_MATRIX_CSV,
    COMPETITIVENESS_AUTODOC_RISK_CSV,
    DASHBOARDS_DIR,
    TENDER_MONITOR_DIR,
    TOOLS_DIR,
)

GOLDEN_HTML = DASHBOARDS_DIR / "fleet" / "ITUK_ZEV_Golden_Window_Dashboard.html"
COMP_HTML = DASHBOARDS_DIR / "sales" / "ISZE_Competitiveness_Dashboard.html"
TENDER_HTML = DASHBOARDS_DIR / "ops" / "ISZE_Tender_Monitor_v2.html"
TENDER_XLSX_CANDIDATES = [
    TENDER_MONITOR_DIR / "tenders_output.xlsx",
    TENDER_MONITOR_DIR / "isuzu_tenders_v3.xlsx",
    TOOLS_DIR / "tender_scraper" / "tenders_output.xlsx",
]

MARKER_GOLDEN = "<!-- ISZE_GOLDEN_GPS_OVERLAY -->"
MARKER_COMP = "<!-- ISZE_AUTODOC_CLASS_C -->"
MARKER_TENDER = "<!-- ISZE_TENDER_ROWS -->"


OVERLAY_DEDUP_RE = re.compile(
    r"(?:<div class='card' style='margin-top:16px'><div class='sec-title'>ISZE · GPS × AIM overlay.*?</div>\s*)+",
    re.DOTALL,
)


def _patch(path: Path, marker: str, fragment: str) -> bool:
    if not path.is_file():
        print(f"  skip missing {path.name}")
        return False
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        print(f"  marker missing in {path.name} — add {marker}")
        return False
    before, after = text.split(marker, 1)
    before = OVERLAY_DEDUP_RE.sub("", before)
    new_text = before + fragment + "\n" + marker + after
    path.write_text(new_text, encoding="utf-8")
    print(f"  patched {path.name}")
    return True


def _golden_table() -> str:
    if not AIM_GPS_MATRIX_CSV.exists():
        return "<p><em>Run build_aim_gps_matrix.py</em></p>"
    df = pd.read_csv(AIM_GPS_MATRIX_CSV)
    yr = int(df["year"].max())
    sub = df[df["year"] == yr].sort_values("gps_spu_eur", ascending=False).head(18)
    rows = []
    for _, r in sub.iterrows():
        rows.append(
            f"<tr><td>{html.escape(str(r['distributor_code']))}</td>"
            f"<td class='r'>€{r['gps_spu_eur']:,.0f}</td>"
            f"<td class='r'>{100*r['aim_high_risk_pct']:.1f}%</td>"
            f"<td>{html.escape(str(r['quadrant_label']))}</td></tr>"
        )
    return (
        f"<div class='card' style='margin-top:16px'><div class='sec-title'>"
        f"ISZE · GPS × AIM overlay (CY{yr})</div>"
        f"<table><tr><th>Distributor</th><th class='r'>GPS SPU</th>"
        f"<th class='r'>AIM high-risk %</th><th>Quadrant</th></tr>"
        + "".join(rows)
        + "</table><p style='font-size:11px;color:#666;margin-top:8px'>"
        "Source: PRISM derived · prioritise PMS in Golden Window distributors with low GPS.</p></div>"
    )


def _comp_table() -> str:
    if not COMPETITIVENESS_AUTODOC_RISK_CSV.exists():
        return "<p><em>Run build_competitiveness_autodoc_risk.py</em></p>"
    df = pd.read_csv(COMPETITIVENESS_AUTODOC_RISK_CSV).head(25)
    rows = []
    for _, r in df.iterrows():
        rows.append(
            f"<tr><td>{html.escape(str(r.get('part_number','')))}</td>"
            f"<td>{html.escape(str(r.get('description',''))[:50])}</td>"
            f"<td class='r'>€{float(r.get('pr00_eur',0)):,.2f}</td>"
            f"<td class='r'>€{float(r.get('autodoc_min_eur',0)):,.2f}</td>"
            f"<td class='r'>{100*float(r.get('ratio',0)):.0f}%</td></tr>"
        )
    return (
        "<div class='src-note' style='margin-top:12px'><strong>Class C · Autodoc &lt; 75% PR00</strong> "
        f"({len(pd.read_csv(COMPETITIVENESS_AUTODOC_RISK_CSV))} PNs scraped)</div>"
        "<div class='tbl-wrap'><table><tr><th>PN</th><th>Description</th>"
        "<th class='tr'>PR00</th><th class='tr'>Autodoc min</th><th class='tr'>Ratio</th></tr>"
        + "".join(rows)
        + "</table></div>"
    )


def _tender_rows() -> str:
    path = next((p for p in TENDER_XLSX_CANDIDATES if p.is_file()), None)
    if not path:
        return "<tr><td colspan='5'><em>tenders_output.xlsx not found</em></td></tr>"
    df = pd.read_excel(path)
    rows = []
    for _, r in df.head(40).iterrows():
        cols = list(df.columns)
        title = str(r.get(cols[0], r.iloc[0]) if cols else "")
        buyer = str(r.get(cols[1], "")) if len(cols) > 1 else ""
        date = str(r.get(cols[2], "")) if len(cols) > 2 else ""
        rows.append(
            f"<tr><td>{html.escape(title[:80])}</td>"
            f"<td>{html.escape(buyer[:40])}</td><td>{html.escape(date[:20])}</td></tr>"
        )
    return "".join(rows) if rows else "<tr><td colspan='3'>No tenders in file</td></tr>"


def main() -> int:
    _patch(GOLDEN_HTML, MARKER_GOLDEN, _golden_table())
    _patch(COMP_HTML, MARKER_COMP, _comp_table())
    if TENDER_HTML.is_file():
        frag = (
            "<tbody id='tender-injected'>"
            + _tender_rows()
            + "</tbody>"
        )
        # inject into tbody if marker inside table
        text = TENDER_HTML.read_text(encoding="utf-8")
        if MARKER_TENDER in text:
            TENDER_HTML.write_text(
                text.replace(MARKER_TENDER, _tender_rows() + "\n" + MARKER_TENDER),
                encoding="utf-8",
            )
            print(f"  patched {TENDER_HTML.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
