"""
ISZE — PMS x IAM bridge view (internal, unaudited).

Puts two ALREADY-SEPARATE, already-audited numbers on one screen so you can eyeball
them together:

  - PMS lost ISZE GP by category, from engine.compute_view() (product B in
    PRODUCT_LOGIC.md — signed off, authoritative for PMS/ITUK claims).
  - IAM competitor price benchmark by category, from the scraper CSVs in this
    folder (product C, layer C — context only, never PMS actuals).

This does NOT multiply the two into a single blended euro figure. Decision rule 4
in PRODUCT_LOGIC.md says explicitly: never cite IAM substitution loss as PMS
leakage. Side-by-side is the ceiling of what this view claims to show.

Category granularity mismatch (do not "fix" by editing engine.py or
cv_category_crawler.py without separate sign-off — both drive already-audited
outputs):
  - engine.py's PN_TO_PMS_CATEGORY has 12 categories (brake split front/rear,
    clutch split into disc/pressure plate/release bearing, cabin filter separate).
  - KS International and Mekonomen are PN-level (via engine.normalize_scraped_prices)
    so they inherit the fine category from the PMS PN match directly.
  - Tranzparts / T&M Commercials / Auto 365 are category-level only (confirmed
    2026-07-09/10: none of these catalogs are indexed by Isuzu OEM part number —
    see each scraper's module docstring). Their classify_pms_category() in
    cv_category_crawler.py only has 5 coarse buckets (oil/fuel/air filter, clutch,
    brake — no front/rear, no cabin filter). True PN-level join for these three is
    not achievable without building an OEM-PN <-> aftermarket-SKU crossref, which
    is a separate, much larger project (the abandoned autodoc_crossref_scraper.py
    attempt is the cautionary example). ROLLUP maps the 5 coarse buckets to the
    fine categories below for display only.

Output: _html_previews/isze_pms_iam_bridge.html (self-contained, no CDN deps).

Usage:
    python build_pms_iam_bridge.py [--market "ITUK (PMS Calc pilot)"]
"""
from __future__ import annotations

import argparse
import html
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
_BUNDLE = SCRIPT_DIR / "_HANDOFF_BUNDLE"
if str(_BUNDLE) not in sys.path:
    sys.path.insert(0, str(_BUNDLE))

from engine import compute_view  # noqa: E402
from sources_loader import load_sources_config, resolve_paths, load_v3_pn_matrix  # noqa: E402

# Coarse scraper bucket -> fine engine.py categories it can represent.
# One coarse bucket rolls up to several fine categories because the scraper
# can't tell them apart from a product title alone (see module docstring).
ROLLUP: dict[str, list[str]] = {
    "oil_filter": ["Oil filter"],
    "fuel_filter": ["Fuel filter"],
    "air_filter": ["Air filter"],
    "clutch": ["Clutch disc", "Pressure plate", "Release bearing"],
    "brake": [
        "Brake pad (front)", "Brake pad (rear)",
        "Brake disc (front)", "Brake disc (rear)",
        "Brake lining",
    ],
}

CATEGORY_SCRAPE_FILES = [
    ("Tranzparts", "tranzparts_results.csv"),
    ("T&M Commercials", "tmc_results.csv"),
    ("Auto 365", "auto365_results.csv"),
]


def _load_excel_sheets(path: Path) -> dict[str, pd.DataFrame]:
    if not path or not path.exists():
        return {}
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {sh: pd.DataFrame(list(wb[sh].values)) for sh in wb.sheetnames}
    wb.close()
    return out


def _load_category_scrapes() -> pd.DataFrame:
    """Category-level scraper CSVs, rolled up to (fine_category, site) min/avg."""
    rows: list[dict] = []
    for site, fname in CATEGORY_SCRAPE_FILES:
        p = SCRIPT_DIR / fname
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype=str, low_memory=False)
        if df.empty or "PMS_Category" not in df.columns or "Price_EUR" not in df.columns:
            continue
        df["Price_EUR"] = pd.to_numeric(df["Price_EUR"], errors="coerce")
        df = df.dropna(subset=["Price_EUR"])
        for coarse, prices in df.groupby("PMS_Category")["Price_EUR"]:
            fine_cats = ROLLUP.get(coarse)
            if not fine_cats:
                continue
            for fine in fine_cats:
                rows.append({
                    "category": fine,
                    "site": site,
                    "coarse_bucket": coarse,
                    "n": len(prices),
                    "min_eur": round(float(prices.min()), 2),
                    "avg_eur": round(float(prices.mean()), 2),
                })
    return pd.DataFrame(rows)


def build_bridge(market: str) -> tuple[pd.DataFrame, dict]:
    cfg = load_sources_config()
    paths = resolve_paths(cfg) if cfg else {}
    if not paths:
        raise SystemExit("sources.yaml did not resolve any paths — check _HANDOFF_BUNDLE/sources.yaml")

    v3 = load_v3_pn_matrix(paths)
    uio_sheets = _load_excel_sheets(paths.get("uio_overview"))
    pms_sheets = _load_excel_sheets(paths.get("pms_coverage_calculator"))

    scraped_files = [
        ("AD_UK", "autodoc_results.csv"),
        ("MEK", "mekonomen_results.csv"),
        ("KS", "ks_results.csv"),
    ]
    scraped = None
    for prefix, fname in scraped_files:
        p = SCRIPT_DIR / fname
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype={"PN": str}, low_memory=False)
        if "PN" not in df.columns:
            continue
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        df = df.rename(columns={c: f"{prefix}__{c}" for c in df.columns if c != "PN"})
        scraped = df if scraped is None else scraped.merge(df, on="PN", how="outer")
    scraped = scraped if scraped is not None else pd.DataFrame()

    defaults = (cfg.get("defaults") or {}) if cfg else {}
    result = compute_view(
        v3=v3,
        uio_sheets=uio_sheets,
        pms_sheets=pms_sheets,
        scraped=scraped,
        market_scope=market,
        distributor=None,
        isze_gp_pct=0.35,
        horizon_years=None,
        pms_basket="Maintenance + Wear Repair (PMS pilot)",
        period_type="CY",
        sales_year=2025,
        cfg=cfg,
        paths=paths,
        pms_data_mode="auto",
        ituk_uio_source=defaults.get("ituk_uio_source", "smmt_car_park"),
    )
    if result is None or "error" in result:
        msg = result["error"].iloc[0]["message"] if result and "error" in result else "compute_view() returned nothing"
        raise SystemExit(f"PMS engine could not build a category view: {msg}")

    category_view = result.get("Category lost sales")
    if category_view is None or category_view.empty:
        raise SystemExit("PMS engine returned an empty category view for this market scope.")

    iam_by_cat = _load_category_scrapes()
    return category_view, {"iam_by_cat": iam_by_cat, "market": market}


def _render_html(category_view: pd.DataFrame, iam_by_cat: pd.DataFrame, market: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    methodology_note = (
        str(category_view["methodology_note"].iloc[0])
        if "methodology_note" in category_view.columns and not category_view.empty
        else ""
    )
    rows_html = []
    for _, r in category_view.sort_values("lost_isze_gp", ascending=False).iterrows():
        cat = r["category"]
        iam_rows = iam_by_cat[iam_by_cat["category"] == cat] if not iam_by_cat.empty else pd.DataFrame()
        if iam_rows.empty:
            iam_cell = "<span class='muted'>no scrape match</span>"
        else:
            parts = []
            for _, ir in iam_rows.sort_values("min_eur").iterrows():
                parts.append(
                    f"{html.escape(ir['site'])}: min &euro;{ir['min_eur']:.2f} / "
                    f"avg &euro;{ir['avg_eur']:.2f} (n={int(ir['n'])})"
                )
            iam_cell = "<br>".join(parts)

        avg_pr00 = r.get("avg_pr00", 0.0) or 0.0
        iam_min = iam_rows["min_eur"].min() if not iam_rows.empty else None
        gap_cell = "<span class='muted'>&mdash;</span>"
        if iam_min is not None and avg_pr00 > 0:
            gap_pct = (avg_pr00 - iam_min) / avg_pr00
            gap_cell = f"{gap_pct:+.0%}" if gap_pct >= 0 else f"<span class='neg'>{gap_pct:+.0%}</span>"

        rows_html.append(f"""
        <tr>
          <td>{html.escape(str(cat))}</td>
          <td class="num">&euro;{r['lost_isze_gp']:,.0f}</td>
          <td class="num">{r['capture_rate']:.0%}</td>
          <td class="num">&euro;{avg_pr00:,.2f}</td>
          <td>{iam_cell}</td>
          <td class="num">{gap_cell}</td>
        </tr>""")

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>ISZE PMS x IAM Bridge (internal)</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 24px; color: #1a1a1a; background: #fff; }}
  .banner {{ background: #fff3cd; border: 1px solid #e0a800; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }}
  .banner b {{ color: #7a5600; }}
  h1 {{ font-size: 20px; margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 12px; margin-bottom: 16px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #f5f5f5; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .muted {{ color: #999; }}
  .neg {{ color: #c0392b; font-weight: 600; }}
  .foot {{ margin-top: 20px; font-size: 12px; color: #666; }}
</style></head>
<body>
<div class="banner">
  <b>INTERNAL VIEW &mdash; NOT AUDITED &mdash; do not use for external / ITUK claims.</b><br>
  PMS columns (Lost ISZE GP, Capture, ISZE PR00) are from the signed-off engine.compute_view() &mdash;
  same numbers as isze_executive_pms.html. IAM columns are scraped competitor prices, context only.
  These are shown side-by-side, <b>not combined into one figure</b> &mdash; see PRODUCT_LOGIC.md decision rule 4
  (never cite IAM substitution loss as PMS leakage). Price gap % is PMS wholesale (PR00) vs cheapest
  scraped IAM price found &mdash; a directional read, not a validated substitution-loss estimate.<br>
  <b>ITUK scope caveat (from the engine itself):</b> {html.escape(methodology_note)}
  Per AUDIT_STATUS.md, ITUK-tab potential/capture is <b>diagnostic only</b> &mdash; use the PRISM "All distributors"
  row, not this tab, for a real capture-rate claim. The Lost GP / Capture columns below can look extreme
  (whole-fleet PMS Calc assumptions vs a partial dealer-sales actuals feed) &mdash; read them as a category
  ranking signal, not a validated euro figure.
</div>
<h1>PMS x IAM bridge &mdash; {html.escape(market)}</h1>
<div class="meta">Built {ts} &middot; category-level IAM match for Tranzparts/T&amp;M/Auto365 (rolled up from 5 coarse buckets &mdash;
see script docstring); PN-level match not possible for these three sites (not indexed by Isuzu OEM PN).</div>
<table>
  <thead><tr>
    <th>PMS category</th>
    <th>Lost ISZE GP (&euro;)</th>
    <th>Capture</th>
    <th>ISZE PR00 avg</th>
    <th>IAM scrape (site: min/avg, n)</th>
    <th>Price gap vs cheapest IAM</th>
  </tr></thead>
  <tbody>{"".join(rows_html)}</tbody>
</table>
<div class="foot">
  Sources: PMS engine = _HANDOFF_BUNDLE/engine.py compute_view(); IAM = tranzparts_results.csv, tmc_results.csv,
  auto365_results.csv in this folder (refreshed by refresh_and_check_drift.py). No PN-level bridge exists for
  these three sources &mdash; see build_pms_iam_bridge.py docstring.
</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="ITUK (PMS Calc pilot)")
    args = ap.parse_args()

    category_view, meta = build_bridge(args.market)
    out_html = _render_html(category_view, meta["iam_by_cat"], meta["market"])

    out_dir = SCRIPT_DIR / "_html_previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "isze_pms_iam_bridge.html"
    out_path.write_text(out_html, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
