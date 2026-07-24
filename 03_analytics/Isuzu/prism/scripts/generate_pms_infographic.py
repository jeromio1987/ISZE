#!/usr/bin/env python3
"""
Generate print-ready PMS infographic pages (Genuine + BVP rows, category per page).

Output: ISZE/outputs/pms-infographic/<category>.html

Usage:
  python scripts/generate_pms_infographic.py              # all PMS categories
  python scripts/generate_pms_infographic.py --test     # oil filters test page only
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, GENUINE_BVP_CROSSREF_CSV, ISZE_ROOT  # noqa: E402

CROSSREF_CSV = GENUINE_BVP_CROSSREF_CSV
OUT_DIR = ISZE_ROOT / "outputs" / "pms-infographic"

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
ISZE_LIGHT = "#D6E4F0"

CATEGORY_ORDER = [
    ("oil_filter", "Oil Filters"),
    ("fuel_filter", "Fuel Filters"),
    ("air_filter", "Air Filters"),
    ("brake_pad", "Brake Pads"),
    ("brake_shoe", "Brake Shoes"),
    ("clutch_disc", "Clutch Discs"),
    ("clutch_pressure_plate", "Clutch Pressure Plates"),
]

CATEGORY_SVG: dict[str, str] = {
    "oil_filter": """
      <ellipse cx="40" cy="72" rx="22" ry="6" fill="#c8d4e4"/>
      <rect x="18" y="22" width="44" height="50" rx="6" fill="#e8eef5" stroke="#1B3A6B" stroke-width="2"/>
      <rect x="26" y="14" width="28" height="12" rx="3" fill="#9aa8bc" stroke="#1B3A6B" stroke-width="1.5"/>
      <path d="M22 38 h36" stroke="#E87722" stroke-width="3" stroke-linecap="round"/>
      <circle cx="40" cy="48" r="8" fill="none" stroke="#1B3A6B" stroke-width="1.5"/>
    """,
    "fuel_filter": """
      <rect x="14" y="28" width="52" height="38" rx="4" fill="#e8eef5" stroke="#1B3A6B" stroke-width="2"/>
      <rect x="8" y="36" width="10" height="22" rx="2" fill="#9aa8bc"/>
      <rect x="62" y="36" width="10" height="22" rx="2" fill="#9aa8bc"/>
      <line x1="20" y1="42" x2="60" y2="42" stroke="#E87722" stroke-width="2"/>
      <line x1="20" y1="52" x2="60" y2="52" stroke="#1B3A6B" stroke-width="1.5" opacity="0.5"/>
    """,
    "air_filter": """
      <rect x="12" y="30" width="56" height="36" rx="4" fill="#f4f7fb" stroke="#1B3A6B" stroke-width="2"/>
      <path d="M18 34 v28 M26 34 v28 M34 34 v28 M42 34 v28 M50 34 v28 M58 34 v28"
            stroke="#1B3A6B" stroke-width="1" opacity="0.35"/>
      <rect x="20" y="22" width="40" height="10" rx="2" fill="#E87722" opacity="0.85"/>
    """,
    "brake_pad": """
      <path d="M16 58 L24 24 L56 24 L64 58 Z" fill="#3d3d3d" stroke="#1B3A6B" stroke-width="2"/>
      <rect x="28" y="30" width="24" height="20" rx="2" fill="#E87722" opacity="0.9"/>
      <ellipse cx="40" cy="62" rx="26" ry="5" fill="#c8d4e4"/>
    """,
    "brake_shoe": """
      <path d="M20 62 Q40 18 60 62" fill="none" stroke="#1B3A6B" stroke-width="3"/>
      <path d="M24 58 Q40 28 56 58" fill="#3d3d3d" stroke="#1B3A6B" stroke-width="1.5"/>
      <circle cx="28" cy="54" r="4" fill="#E87722"/>
      <circle cx="52" cy="54" r="4" fill="#E87722"/>
    """,
    "clutch_disc": """
      <circle cx="40" cy="44" r="26" fill="#e8eef5" stroke="#1B3A6B" stroke-width="2"/>
      <circle cx="40" cy="44" r="10" fill="#fff" stroke="#1B3A6B" stroke-width="2"/>
      <circle cx="40" cy="20" r="3" fill="#E87722"/><circle cx="58" cy="32" r="3" fill="#E87722"/>
      <circle cx="58" cy="56" r="3" fill="#E87722"/><circle cx="40" cy="68" r="3" fill="#E87722"/>
      <circle cx="22" cy="56" r="3" fill="#E87722"/><circle cx="22" cy="32" r="3" fill="#E87722"/>
    """,
    "clutch_pressure_plate": """
      <circle cx="40" cy="44" r="28" fill="#d0d8e4" stroke="#1B3A6B" stroke-width="2"/>
      <circle cx="40" cy="44" r="12" fill="#fff" stroke="#1B3A6B" stroke-width="2"/>
      <rect x="36" y="10" width="8" height="14" rx="2" fill="#E87722"/>
      <rect x="36" y="64" width="8" height="14" rx="2" fill="#E87722"/>
    """,
}


def format_pn(pn: str) -> str:
    s = re.sub(r"\D", "", str(pn))
    if len(s) == 10:
        return f"{s[:5]}-{s[5:]}"
    return str(pn)


def load_pairs() -> pd.DataFrame:
    df = pd.read_csv(CROSSREF_CSV, dtype=str)
    df = df[df["pms_flag"].astype(str).str.lower() == "true"].copy()
    df = df.dropna(subset=["genuine_pn", "bvp_pn", "pms_category"])
    df["genuine_pn"] = df["genuine_pn"].str.strip()
    df["bvp_pn"] = df["bvp_pn"].str.strip()
    df["pms_category"] = df["pms_category"].str.strip()
    # Prefer catalog rows with vehicle/engine over registry-only stubs
    df["_rank"] = df["sheet_source"].apply(
        lambda s: 0 if str(s) != "PMS_PN_REGISTRY" else 1
    )
    df = df.sort_values(["pms_category", "genuine_pn", "bvp_pn", "_rank"])
    df = df.drop_duplicates(subset=["pms_category", "genuine_pn", "bvp_pn"], keep="first")
    return df.drop(columns=["_rank"])


def _esc(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return html.escape(str(val).strip())


def part_svg(category: str) -> str:
    body = CATEGORY_SVG.get(category, CATEGORY_SVG["oil_filter"])
    return f'<svg viewBox="0 0 80 80" class="part-icon" aria-hidden="true">{body}</svg>'


def render_card(row: pd.Series, category: str) -> str:
    veh = _esc(row.get("vehicle_model")) or "—"
    eng = _esc(row.get("engine_type")) or "—"
    origin = _esc(row.get("origin"))
    ctype = _esc(row.get("catalog_type"))
    meta = " · ".join(x for x in [ctype, origin] if x)
    return f"""
    <article class="part-card">
      <div class="illus">{part_svg(category)}</div>
      <div class="pn-rows">
        <div class="pn-row genuine">
          <span class="label">Genuine</span>
          <span class="pn">{format_pn(row['genuine_pn'])}</span>
        </div>
        <div class="pn-row bvp">
          <span class="label">BVP</span>
          <span class="pn">{format_pn(row['bvp_pn'])}</span>
        </div>
      </div>
      <p class="fitment" title="{veh} · {eng}"><strong>Models</strong> {veh}</p>
      <p class="fitment subtle"><strong>Engine</strong> {eng}</p>
      {f'<p class="meta">{meta}</p>' if meta else ''}
    </article>
    """


def render_page(category: str, title: str, rows: pd.DataFrame, *, test_banner: bool) -> str:
    cards = "\n".join(render_card(r, category) for _, r in rows.iterrows())
    banner = (
        '<div class="test-banner">TEST PAGE — review layout &amp; styling before full export</div>'
        if test_banner
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ISZE PMS — {title}</title>
  <style>
    @page {{ size: A4 landscape; margin: 10mm; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Segoe UI", system-ui, sans-serif;
      color: #1a1a2e;
      background: #f0f3f8;
    }}
    .page {{
      width: 277mm;
      min-height: 190mm;
      margin: 0 auto;
      padding: 8mm 10mm 6mm;
      background: #fff;
      page-break-after: always;
    }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ width: auto; min-height: auto; margin: 0; padding: 0; }}
      .no-print {{ display: none !important; }}
    }}
    header.page-head {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      border-bottom: 3px solid {ISZE_BLUE};
      padding-bottom: 4mm;
      margin-bottom: 5mm;
    }}
    .brand {{ display: flex; align-items: center; gap: 3mm; }}
    .brand-mark {{
      width: 10mm; height: 10mm;
      background: {ISZE_BLUE};
      color: #fff;
      font-weight: 800;
      font-size: 7pt;
      display: flex; align-items: center; justify-content: center;
      letter-spacing: -0.5px;
    }}
    h1 {{ font-size: 18pt; font-weight: 700; color: {ISZE_BLUE}; line-height: 1.1; }}
    .subtitle {{ font-size: 9pt; color: #5a6a7a; margin-top: 1mm; }}
    .page-meta {{ text-align: right; font-size: 8pt; color: #5a6a7a; }}
    .page-meta strong {{ color: {ISZE_ORANGE}; font-size: 9pt; display: block; }}
    .test-banner {{
      background: {ISZE_ORANGE};
      color: #fff;
      text-align: center;
      font-size: 8pt;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 2mm;
      margin-bottom: 4mm;
      border-radius: 2px;
    }}
    .legend {{
      display: flex;
      gap: 6mm;
      font-size: 7.5pt;
      margin-bottom: 4mm;
      color: #5a6a7a;
    }}
    .legend span {{ display: flex; align-items: center; gap: 2mm; }}
    .swatch {{ width: 4mm; height: 3mm; border-radius: 1px; }}
    .swatch.g {{ background: {ISZE_BLUE}; }}
    .swatch.b {{ background: {ISZE_ORANGE}; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 3.5mm;
    }}
    .part-card {{
      border: 1px solid {ISZE_LIGHT};
      border-radius: 3px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      background: #fafbfd;
    }}
    .illus {{
      background: linear-gradient(180deg, #eef3f9 0%, #fff 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2mm 0 1mm;
      min-height: 22mm;
    }}
    .part-icon {{ width: 16mm; height: 16mm; }}
    .pn-rows {{ display: flex; flex-direction: column; }}
    .pn-row {{
      display: grid;
      grid-template-columns: 14mm 1fr;
      align-items: center;
      gap: 2mm;
      padding: 1.4mm 2.5mm;
      font-size: 7.5pt;
    }}
    .pn-row.genuine {{ background: {ISZE_BLUE}; color: #fff; }}
    .pn-row.bvp {{ background: {ISZE_ORANGE}; color: #fff; }}
    .pn-row .label {{
      font-size: 6pt;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      opacity: 0.9;
      font-weight: 600;
    }}
    .pn-row .pn {{
      font-family: "Consolas", "SF Mono", monospace;
      font-weight: 700;
      font-size: 7.5pt;
      letter-spacing: 0.02em;
    }}
    .fitment {{
      font-size: 6.2pt;
      line-height: 1.35;
      padding: 1.2mm 2.5mm 0;
      color: #3a4a5a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .fitment.subtle {{ padding-top: 0.5mm; color: #6a7a8a; }}
    .fitment strong {{ font-weight: 600; color: {ISZE_BLUE}; margin-right: 1mm; }}
    .meta {{
      font-size: 5.8pt;
      color: #8a96a6;
      padding: 0.5mm 2.5mm 1.5mm;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    footer {{
      margin-top: 4mm;
      padding-top: 2mm;
      border-top: 1px solid {ISZE_LIGHT};
      font-size: 6.5pt;
      color: #8a96a6;
      display: flex;
      justify-content: space-between;
    }}
    .print-hint.no-print {{
      text-align: center;
      padding: 4mm;
      font-size: 9pt;
      color: #5a6a7a;
    }}
    .print-hint a {{ color: {ISZE_BLUE}; }}
  </style>
</head>
<body>
  <p class="print-hint no-print">Open in browser → <strong>Ctrl+P</strong> → Save as PDF (landscape). <a href="index.html">All pages</a></p>
  <section class="page">
    {banner}
    <header class="page-head">
      <div class="brand">
        <div class="brand-mark">IZ</div>
        <div>
          <h1>{title}</h1>
          <p class="subtitle">PMS Genuine ↔ BVP cross-reference · {len(rows)} pairs</p>
        </div>
      </div>
      <div class="page-meta">
        <strong>Preventive Maintenance</strong>
        BVP Parts Catalog · ISZE
      </div>
    </header>
    <div class="legend">
      <span><i class="swatch g"></i> Row 1 — Genuine OE part number</span>
      <span><i class="swatch b"></i> Row 2 — BVP equivalent</span>
    </div>
    <div class="grid">
      {cards}
    </div>
    <footer>
      <span>Source: BVP PARTS CATALOG.xlsx · derived/genuine_bvp_crossref.csv</span>
      <span>{title} · {category}</span>
    </footer>
  </section>
</body>
</html>
"""


def write_index(categories_written: list[tuple[str, str]]) -> None:
    links = "\n".join(
        f'    <li><a href="{cat}.html">{title}</a></li>'
        for cat, title in categories_written
    )
    index = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>PMS Infographic Index</title>
<style>
  body {{ font-family: system-ui; max-width: 40rem; margin: 2rem auto; color: #1B3A6B; }}
  h1 {{ font-size: 1.4rem; }}
  ul {{ line-height: 1.8; }}
  a {{ color: #E87722; }}
</style></head><body>
<h1>ISZE PMS Infographic Pages</h1>
<p>Print each page landscape (A4). Product illustrations are placeholders — swap for photos when available.</p>
<ul>
{links}
  <li><a href="test-oil-filters.html"><strong>TEST — Oil Filters (review)</strong></a></li>
</ul>
</body></html>
"""
    (OUT_DIR / "index.html").write_text(index, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Only generate test oil filter page")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_pairs()
    written: list[tuple[str, str]] = []

    if args.test:
        cat, title = "oil_filter", "Oil Filters"
        sub = df[df["pms_category"] == cat]
        out = OUT_DIR / "test-oil-filters.html"
        out.write_text(render_page(cat, title, sub, test_banner=True), encoding="utf-8")
        print(f"Wrote {out} ({len(sub)} pairs)")
        return

    for cat, title in CATEGORY_ORDER:
        sub = df[df["pms_category"] == cat]
        if sub.empty:
            continue
        out = OUT_DIR / f"{cat}.html"
        out.write_text(render_page(cat, title, sub, test_banner=False), encoding="utf-8")
        written.append((cat, title))
        print(f"Wrote {out.name} ({len(sub)} pairs)")

    # Test page duplicate for review
    sub = df[df["pms_category"] == "oil_filter"]
    (OUT_DIR / "test-oil-filters.html").write_text(
        render_page("oil_filter", "Oil Filters", sub, test_banner=True), encoding="utf-8"
    )
    write_index(written)
    print(f"Done — {OUT_DIR}")


if __name__ == "__main__":
    main()
