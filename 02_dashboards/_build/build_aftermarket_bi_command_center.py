#!/usr/bin/env python3
"""Aftermarket BI suite index — retired command center (internal).

The former single mega-dashboard mixed non-additive metrics (replenishment €,
PMS capture %, price-list ambition, GPS opportunity). This builder now writes
a suite map that links to the focused pages instead.

Writes : 02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html
         02_dashboards/sales/OPEN_Aftermarket_BI_Command_Center.cmd
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import tier_a_dashboard_common as T  # noqa: E402

ISZE = Path(__file__).resolve().parents[2]
OUT_HTML = ISZE / "02_dashboards" / "sales" / "ISZE_Aftermarket_BI_Command_Center.html"
OUT_CMD = ISZE / "02_dashboards" / "sales" / "OPEN_Aftermarket_BI_Command_Center.cmd"

SUITE_PAGES = (
    {
        "href": "ISZE_Lost_Sales_Model.html",
        "title": "Executive aftermarket opportunity",
        "question": "Where is uncaptured target spend, by market and service family?",
        "detail": (
            "Market-level GPS ceiling and cover from the lost-sales model. "
            "Euro-first, with fleet denominator and service-family context. "
            "Not the same basis as replenishment PN rows."
        ),
    },
    {
        "href": "ISZE_PMS_Family_Evolution_v2.html",
        "title": "Family performance diagnostic",
        "question": "How did parts billed and service capture move by AIM family over time?",
        "detail": (
            "Calendar and ISZE-year views per distributor. "
            "Capture and euro trends — diagnostic, not additive to replenishment €."
        ),
    },
    {
        "href": "ISZE_PMS_Tonnage_Evolution.html",
        "title": "Service-demand / tonnage diagnostic",
        "question": "Where does expected service demand sit across tonnage bands?",
        "detail": (
            "Modelled demand vs observed parts billed, band by band. "
            "Fleet and target-spend basis stated on that page."
        ),
    },
    {
        "href": "ISZE_DB_DLR_Replenishment_CY2025.html",
        "title": "Replenishment exceptions (five-distributor subset)",
        "question": "Which PN×DB rows show bill vs dealer-sales imbalance?",
        "detail": (
            "CY2025 replenishment register for ITUK · UTI · IRELAND · IUK · GREECE "
            "only — distributors with dealer sales files. "
            "Reference-price exposure where bill exceeds dealer sales; overstock where the reverse."
        ),
    },
    {
        "href": "ISZE_DB_Leakage_Review_CY2025.html",
        "title": "Narrative explainer (non-additive diagnostics)",
        "question": "What story ties replenishment, pricing guardrails and capture together?",
        "detail": (
            "Written walk-through of the five-distributor replenishment cut. "
            "Figures here must not be summed with GPS opportunity or PMS capture %."
        ),
    },
)

EXTRA_CSS = """
.basis-strip{background:#fff;border:1px solid #d9d3c8;border-left:4px solid #15233c;
  padding:14px 18px;margin:0 0 24px;font-size:13px;line-height:1.65}
.basis-strip b{color:#15233c;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
.basis-strip div+div{margin-top:8px}
.retired-banner{background:#f8e4dc;border-left:4px solid #c0552d;padding:16px 18px;
  margin:0 0 24px;font-size:14.5px;line-height:1.55}
.retired-banner strong{color:#8a3030}
.suite-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px}
@media(max-width:820px){.suite-grid{grid-template-columns:1fr}}
.suite-card{display:block;background:#fff;border:1px solid #d9d3c8;padding:18px 20px;
  text-decoration:none;color:#222;transition:border-color .15s,box-shadow .15s}
.suite-card:hover{border-color:#c0552d;box-shadow:0 4px 16px rgba(21,35,60,.08)}
.suite-card h3{font-family:Georgia,serif;font-size:17px;color:#1a2b4a;margin:0 0 6px}
.suite-card .q{font-size:13.5px;color:#6b6256;margin:0 0 10px;font-style:italic}
.suite-card .detail{font-size:13px;color:#444;margin:0 0 12px;line-height:1.5}
.suite-card .open{font-size:12px;text-transform:uppercase;letter-spacing:.06em;
  color:#c0552d;font-weight:600}
.section-h{font-family:Georgia,serif;font-size:20px;color:#1a2b4a;margin:28px 0 14px;
  padding-bottom:8px;border-bottom:2px solid #1a2b4a}
"""


def _esc(s: object) -> str:
    return (
        str(s if s is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace('"', "&quot;")
    )


def _suite_cards_html() -> str:
    parts = []
    for p in SUITE_PAGES:
        parts.append(
            f'<a class="suite-card suite-link" href="{_esc(p["href"])}">'
            f'<h3>{_esc(p["title"])}</h3>'
            f'<p class="q">{_esc(p["question"])}</p>'
            f'<p class="detail">{_esc(p["detail"])}</p>'
            f'<span class="open">Open {_esc(p["href"])} →</span></a>'
        )
    return "".join(parts)


def write_html(built_at: str | None = None) -> None:
    built = (built_at or datetime.now(UTC).strftime("%Y-%m-%d"))[:10]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Aftermarket suite map — command center retired</title>
<style>{T.TIER_A_CSS}{EXTRA_CSS}</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · Aftermarket BI · internal</div>
    <h1>Command center retired — use focused pages</h1>
    <div class="rule"></div>
    <p class="lead">This URL used to host one combined dashboard. It mixed replenishment reference-price exposure,
    PMS capture %, price-list ambition and GPS opportunity on one screen — metrics that do not add together.
    Open the page below that matches your question.</p>
  </div>
</div>
<div class="wrap">

  <div class="retired-banner" id="retirement-notice">
    <strong>Retired as a single mega-dashboard.</strong>
    The former command center stacked non-additive views (five-distributor replenishment €,
    18-market GPS opportunity, PMS capture rates, price-list guardrails) without keeping their
    denominators separate. Those charts and tables are removed from this page. Use the suite links below.
  </div>

  <div class="basis-strip" id="basis-strip">
    <div><b>Scope</b> — Replenishment pages cover five distributors with dealer sales files
    (ITUK · UTI · IRELAND · IUK · GREECE). That is not the full 18-market network.
    UTI≠UMI · IUK≠ITUK · IRELAND≠IUK.</div>
    <div><b>Non-additive</b> — Reference-price exposure €, target-spend opportunity €, capture %
    and price-list ambition use different bases. Do not sum figures across suite pages.</div>
    <div><b>Reference dealer price</b> — Where replenishment pages value a qty gap:
    ISZE list × 1.40 to the dealer × 1.275 to the customer price we use as reference dealer price
    (PR00 × 1.785 in the data).</div>
    <div><b>Period</b> — Replenishment subset is CY2025 unless a linked page states otherwise.</div>
  </div>

  <h2 class="section-h">Aftermarket suite — pick your question</h2>
  <div class="suite-grid" id="suite-grid">
    {_suite_cards_html()}
  </div>

  <div class="callout">
    <strong>Which page when?</strong>
    Start with <em>Executive aftermarket opportunity</em> for market-level euro gaps and fleet context.
    Use <em>Replenishment exceptions</em> for PN-level bill vs dealer-sales imbalance in the five-distributor subset.
    Use <em>Family</em> or <em>Tonnage</em> diagnostics for capture and demand shape over time.
    Use <em>Narrative explainer</em> when you need the written story, not another combined chart wall.
  </div>

  <p class="foot">Built {built} · Suite index only · Former command center retired {built} · Internal.</p>
</div>
</body>
</html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_Aftermarket_BI_Command_Center.html"\r\n',
        encoding="utf-8",
    )


def rebuild_siblings() -> None:
    scripts = [
        ISZE / "01_data" / "91_build" / "build_db_dlr_commercial_stack.py",
        ISZE / "02_dashboards" / "sales" / "_build" / "build_db_dlr_replenishment_cy2025.py",
        ISZE / "01_data" / "91_build" / "build_book_b_review_workbook.py",
    ]
    for s in scripts:
        if s.is_file():
            print(f"rebuilding {s.name}...")
            subprocess.run([sys.executable, str(s)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Aftermarket BI suite index (retired command center)")
    ap.add_argument("--all", action="store_true", help="Also rebuild replenishment + price list HTML")
    args = ap.parse_args()
    if args.all:
        rebuild_siblings()
    write_html()
    verify = HERE / "verify_aftermarket_bi_command_center.py"
    if verify.is_file():
        rc = subprocess.run([sys.executable, str(verify)], check=False)
        if rc.returncode != 0:
            return rc.returncode
    size_kb = OUT_HTML.stat().st_size / 1024
    print(f"wrote {OUT_HTML} ({size_kb:.1f} KB, suite index)")
    print(f"wrote {OUT_CMD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
