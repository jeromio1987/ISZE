#!/usr/bin/env python3
"""Build shared exec aftersales paper (self-contained HTML + Chart.js inline)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "02_dashboards" / "sales" / "ISZE_Exec_Aftersales_Paper.html"
CHART = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
IAM_BUILDER = ROOT / "02_dashboards" / "pricing" / "_build" / "build_iam_price_vs_billed_pn.py"

VERIFY_AT = "2026-08-25T17:19:54Z"
BILLING_MAX = "2026-06-30"
VERIFY_PASS, VERIFY_FAIL = 116, 0

REF_SELL_OUT_EN = (
    "Reference dealer price is the ISZE list price times 1.40 to the dealer "
    "times 1.275 to the customer price we use as the reference dealer price we compare to shops "
    "(= ×1.785). Price index = shop or aftermarket quote ÷ that reference."
)

TENDER_JSON = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
WALLET_WATERFALL = ROOT / "01_data" / "00_derived" / "wallet_waterfall.csv"
PLACEHOLDER_EUR_PER_UIO = 250.0


def load_placeholder_share(year: str = "2025") -> tuple[int, float]:
    """Derive the flat €250/UIO placeholder from wallet_waterfall.csv.

    Returns (market count, share of the ceiling). Measured 2026-09-16: 8 markets, 0.36996.
    """
    import csv

    rows = [r for r in csv.DictReader(WALLET_WATERFALL.open(newline="", encoding="utf-8-sig")) if r["year"] == year]
    total = sum(float(r["theoretical_wallet_eur"]) for r in rows)
    flat_sum = 0.0
    flat_n = 0
    for r in rows:
        units = float(r["uio_units"])
        if units and abs(float(r["theoretical_wallet_eur"]) / units - PLACEHOLDER_EUR_PER_UIO) <= 0.01:
            flat_n += 1
            flat_sum += float(r["theoretical_wallet_eur"])
    return flat_n, (flat_sum / total if total else 0.0)


# Derived at build time from wallet_waterfall.csv (measured 2026-09-16: 8 markets, 37.0%).
PLACEHOLDER_N, PLACEHOLDER_SHARE = load_placeholder_share()
PLACEHOLDER_PCT = f"{PLACEHOLDER_SHARE * 100:.0f}%"
PLACEHOLDER_PCT_1 = f"{PLACEHOLDER_SHARE * 100:.1f}%"


def load_ceiling(year: str = "2025") -> dict:
    """Derive the ceiling headline from wallet_waterfall.csv instead of hardcoding it.

    Every one of these figures used to be a literal in this file: "EUR 60.2M", "51.1%",
    "EUR 30.76M". When the N35/N75 split landed on 2026-09-17 the wallet fell to EUR 55.25M and
    the same billed book read 55.7% — and this paper kept printing the old numbers because they
    were typed, not read. Deriving them means the next pipeline change flows through, and
    verify_exec_aftersales_paper.py can assert the page against the source.
    """
    import csv

    rows = [r for r in csv.DictReader(WALLET_WATERFALL.open(newline="", encoding="utf-8-sig"))
            if r["year"] == year]
    wall = sum(float(r["theoretical_wallet_eur"]) for r in rows)
    cap = sum(float(r["captured_total_eur"]) for r in rows)
    uncap = sum(float(r["addressable_uncaptured_eur"]) for r in rows)
    pct = (cap / wall * 100) if wall else 0.0
    return {
        "rows": len(rows), "wallet": wall, "captured": cap,
        "uncaptured": uncap, "pct": pct,
        "wallet_m": wall / 1e6, "captured_m": cap / 1e6,
        "wallet_s": f"€{wall / 1e6:.2f}M", "captured_s": f"€{cap / 1e6:.2f}M",
        "pct_s": f"{pct:.1f}%", "uncaptured_m": uncap / 1e6,
    }


CEILING = load_ceiling()

# ITUK's own cover on the same basis, for the "largest euro pool below the ceiling" line.
# Per-market cover on the same basis, read from the ceiling file at build time.
# These were hardcoded literals until 2026-09-22, which is why correcting the ceiling did
# not change them: the printed league table kept the pre-correction numbers. Reading them
# from the file means the next ceiling move cannot leave the table behind again.
COVER_PCT: dict[str, float] = {}
try:
    import csv as _csv

    _rows = [r for r in _csv.DictReader(WALLET_WATERFALL.open(newline="", encoding="utf-8-sig"))
             if r["year"] == "2025"]
    COVER_PCT = {r["distributor_code"]: float(r["gps_pct"]) for r in _rows}
    _r = [r for r in _rows if r["distributor_code"] == "ITUK"]
    if _r:
        ITUK_PCT = float(_r[0]["gps_pct"])
        ITUK_WALLET_M = float(_r[0]["theoretical_wallet_eur"]) / 1e6
        ITUK_SPU = (float(_r[0]["theoretical_wallet_eur"]) / float(_r[0]["uio_units"]))
except Exception:
    ITUK_PCT = None


def cov(code: str) -> str:
    """Cover % for a market, read from the ceiling file. Falls back to a visible gap."""
    v = COVER_PCT.get(code)
    return f"{v:.1f}%" if v is not None else "n/a"


def load_tender_stats() -> dict:
    """Live tender feed summary for page 10 (as-of at build time)."""
    td = json.loads(TENDER_JSON.read_text(encoding="utf-8"))
    meta = td.get("meta") or {}
    stats = meta.get("stats") or {}
    sources = meta.get("source_counts") or {}
    # Addressable aftersales euros (tiny vs replenishment)
    ops = td.get("opportunities") or []
    gps_sum = 0.0
    gps_n = 0
    for op in ops:
        if not isinstance(op, dict):
            continue
        v = op.get("gps_addressable_per_year_eur")
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv > 0:
            gps_sum += fv
            gps_n += 1
    return {
        "generated_at": meta.get("generated_at") or "",
        "opportunities": int(stats.get("opportunities") or 0),
        "due_14d": int(stats.get("due_14d") or 0),
        # 2026-09-20: counted over opportunities (the same rows the lists use), not
        # over raw notices. The old key measured notices and disagreed with the
        # page's own row count. Fall back for an older feed.
        "missing_value": int(
            stats.get("missing_value_opportunities", stats.get("missing_value")) or 0
        ),
        "missing_deadline": int(
            stats.get("missing_deadline_opportunities", stats.get("missing_deadline")) or 0
        ),
        "lifecycle_unknown": int(stats.get("lifecycle_unknown") or 0),
        "raw_notices": int(stats.get("raw_notices") or 0),
        "aftersales_tagged": int(stats.get("aftersales_tagged") or 0),
        "portals_reporting": len(sources),
        "gps_addressable_sum": gps_sum,
        "gps_nonzero_ops": gps_n,
        "source_counts": sources,
    }


def load_iam_pn_slice(limit: int = 12) -> tuple[list[dict], dict]:
    """Top billed parts with an aftermarket scrape price — not country dots."""
    spec = importlib.util.spec_from_file_location("iam_pn_build", IAM_BUILDER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {IAM_BUILDER}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["iam_pn_build"] = mod
    spec.loader.exec_module(mod)
    points, stats, _pms = mod.build_points()
    am = [p for p in points if "aftermarket" in (p.get("kind") or "")]
    by_pn: dict[str, dict] = {}
    for p in am:
        cur = by_pn.get(p["pn"])
        if cur is None or p["price_index"] < cur["price_index"]:
            by_pn[p["pn"]] = p
    ranked = sorted(by_pn.values(), key=lambda x: -float(x["billed_eur"]))[:limit]
    return ranked, stats


def chart_js() -> str:
    raw = CHART.read_text(encoding="utf-8")
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    return raw


def bars(rows: list[tuple[str, float, str, str]], max_v: float | None = None, unit: str = "") -> str:
    """rows: label, value, display, colour. CSS first-paint; class bar-row."""
    if max_v is None:
        max_v = max((abs(r[1]) for r in rows), default=1) or 1
    html = ['<div class="bars" role="img">']
    for label, val, disp, col in rows:
        pct = min(100.0, 100.0 * abs(val) / max_v)
        html.append(
            f'<div class="bar-row"><span class="bl">{label}</span>'
            f'<span class="bt"><span class="bf" style="width:{pct:.1f}%;background:{col}"></span></span>'
            f'<span class="bv">{disp}{unit}</span></div>'
        )
    html.append("</div>")
    return "\n".join(html)


def cell(claim: str, money: str, unk: str, decide: str) -> str:
    return (
        f'<article class="swot-cell">'
        f"<p class='claim'>{claim}</p>"
        f"<p class='money'>{money}</p>"
        f"<p class='unk-line'><span class='unk-tag'>UNKNOWN</span> {unk}</p>"
        f"<p class='dec'>Would change the cell: {decide}</p>"
        f"</article>"
    )


def page(num: int, kicker: str, title: str, verdict: str, body: str, extra_class: str = "") -> str:
    return f"""
<section class="paper-page {extra_class}" id="p{num}" data-page="{num}">
  <header class="ph">
    <span class="pk">{kicker}</span>
    <span class="pn">Page {num} of 16</span>
  </header>
  <h2>{title}</h2>
  <p class="verdict">{verdict}</p>
  {body}
  <footer class="pf">ISZE aftersales · CY2025 year of record · YTD through {BILLING_MAX} · verify {VERIFY_PASS}/{VERIFY_FAIL} · {VERIFY_AT}</footer>
</section>
"""


def build_html() -> str:
    gps_spu = bars(
        [
            ("Ireland", 388.57, "€389", "#1d9e75"),
            ("UTI (Israel)", 322.32, "€322", "#1d9e75"),
            ("ITUK (UK truck)", 248.54, "€249", "#1d9e75"),
            ("Finland", 230.83, "€231", "#1d9e75"),
            ("Belgium", 219.86, "€220", "#1d9e75"),
            ("Portugal", 209.12, "€209", "#1d9e75"),
            ("Germany", 197.27, "€197", "#1d9e75"),
            ("UMI (Israel)", 179.02, "€179", "#1d9e75"),
            ("Norway", 178.65, "€179", "#1d9e75"),
            ("Sweden", 151.42, "€151", "#1d9e75"),
            ("Greece", 139.04, "€139", "#c48a16"),
            ("IUK (UK LCV)", 128.33, "€128", "#c48a16"),
            ("Hungary", 88.39, "€88", "#c48a16"),
        ],
        max_v=388.57,
    )
    below_ceiling_bars = bars(
        [
            ("ITUK", 11.61, "€11.6M below target", "#c0552d"),
            ("IUK", 5.81, "€5.8M", "#c0552d"),
            ("UTI", 4.94, "€4.9M", "#c0552d"),
            ("Portugal", 1.34, "€1.3M", "#8a6a4a"),
            ("UMI", 1.32, "€1.3M", "#8a6a4a"),
            ("Germany", 1.27, "€1.3M", "#8a6a4a"),
            ("Hungary", 0.60, "€0.6M", "#8a6a4a"),
            ("Norway", 0.57, "€0.6M", "#8a6a4a"),
        ],
        max_v=11.61,
    )
    pn_slice, pn_stats = load_iam_pn_slice(12)
    pn_price_bars = bars(
        [
            (
                (p.get("description") or p["pn"])[:28],
                float(p["price_index"]),
                f'{float(p["price_index"]):.2f} · €{float(p["billed_eur"])/1000:.0f}k',
                "#c0552d" if p["shop_below_reference"] else "#1d9e75",
            )
            for p in pn_slice
        ],
        max_v=1.0,
    )
    pn_table_rows = "\n".join(
        f'<tr><td>{p["pn"]}</td><td>{(p.get("description") or "")[:42]}</td>'
        f'<td class="n">{float(p["price_index"]):.2f}</td>'
        f'<td class="n">€{float(p["billed_eur"]):,.0f}</td>'
        f'<td>{(p.get("vintage") or "")[:28]}</td></tr>'
        for p in pn_slice
    )
    iml_cover = bars(
        [
            ("Fuel filter", 65.1, "65.1%", "#1d9e75"),
            ("Brake", 35.3, "35.3%", "#c48a16"),
            ("Oil filter", 35.1, "35.1%", "#c48a16"),
            ("Air filter", 13.2, "13.2%", "#c0453c"),
            ("Clutch", 7.8, "7.8%", "#c0453c"),
        ],
        max_v=100,
    )
    iml_gap = bars(
        [
            ("Air filter", 736, "€736k", "#c0453c"),
            ("Brake", 642, "€642k", "#c0552d"),
            ("Clutch", 393, "€393k", "#c0552d"),
            ("Oil filter", 141, "€141k", "#8a6a4a"),
            ("Fuel filter", 127, "€127k", "#8a6a4a"),
        ],
        max_v=736,
    )
    # Network component gap from pms_opportunity_matrix (CY2025) — opportunity euro lead
    cat_gap = bars(
        [
            ("Clutch disc", 3.14, "€3.14M", "#c0453c"),
            ("Brake pad", 2.78, "€2.78M", "#c0453c"),
            ("Brake shoe", 2.47, "€2.47M", "#c0552d"),
            ("Clutch pressure plate", 1.98, "€1.98M", "#c0552d"),
            ("Blower filter", 1.42, "€1.42M", "#c48a16"),
            ("Brake rotor", 1.39, "€1.39M", "#c48a16"),
            ("Fuel filter", 1.02, "€1.02M", "#8a6a4a"),
            ("Clutch kit", 0.96, "€0.96M", "#8a6a4a"),
        ],
        max_v=3.14,
    )
    gap_types = bars(
        [
            ("Substitution", 11.40, "€11.4M · 49%", "#c0552d"),
            ("Under-service", 9.56, "€9.6M · 41%", "#c48a16"),
            ("Catalogue gap", 2.18, "€2.2M · 9%", "#6b7c93"),
        ],
        max_v=11.40,
    )
    pms_net = bars(
        [
            ("Ireland", 100, "100% cap · 191% raw", "#6b7c93"),
            ("ITUK", 100, "100% cap · 116% raw", "#6b7c93"),
            ("Greece", 97.2, "97%", "#1d9e75"),
            ("UTI", 91.3, "91%", "#1d9e75"),
            ("UMI", 85.2, "85%", "#1d9e75"),
            ("Belgium", 62.6, "63%", "#c48a16"),
            ("IUK", 37.7, "38%", "#c0453c"),
            ("Germany", 15.1, "15%", "#c0453c"),
        ],
        max_v=100,
    )
    mix_bvp = bars(
        [
            ("UTI", 11.1, "11.1% BVP", "#c0552d"),
            ("Cyprus", 8.5, "8.5%", "#c0552d"),
            ("Greece", 7.8, "7.8%", "#c0552d"),
            ("Portugal", 6.0, "6.0%", "#c48a16"),
            ("Ireland", 4.5, "4.5%", "#c48a16"),
            ("UMI", 3.7, "3.7%", "#2b4a78"),
            ("Belgium", 3.4, "3.4%", "#2b4a78"),
            ("ITUK", 2.7, "2.7%", "#2b4a78"),
            ("IUK", 0.9, "0.9%", "#1d9e75"),
            ("Germany", 0.7, "0.7%", "#1d9e75"),
            ("Sweden", 0.1, "0.1%", "#1d9e75"),
        ],
        max_v=12,
    )
    ids_avg = bars(
        [
            ("Malta", 89.3, "89", "#1d9e75"),
            ("Portugal", 86.9, "87", "#1d9e75"),
            ("Hungary", 86.2, "86", "#1d9e75"),
            ("Poland", 84.1, "84", "#1d9e75"),
            ("UK truck", 83.8, "84", "#2b4a78"),
            ("UK LCV", 81.7, "82", "#2b4a78"),
            ("Luxembourg", 80.0, "80", "#2b4a78"),
            ("Romania", 79.6, "80", "#2b4a78"),
            ("Belgium", 78.6, "79", "#c48a16"),
            ("Netherlands", 76.3, "76", "#c48a16"),
            ("Denmark", 75.7, "76", "#c48a16"),
            ("Norway", 75.2, "75", "#c48a16"),
            ("Greece", 73.9, "74", "#c48a16"),
            ("Israel (UMI)", 60.9, "61", "#c0453c"),
        ],
        max_v=100,
    )
    repl = bars(
        [
            ("Billed, no matching sales to dealer", 500, "500", "#c0552d"),
            ("High sales to dealer vs bill", 400, "400", "#c48a16"),
            ("Sales to dealer with no bill", 380, "380", "#2b4a78"),
            ("Low sales to dealer", 315, "315", "#8a6a4a"),
        ],
        max_v=500,
    )
    tender = load_tender_stats()
    # Top national / EU source bars from live feed (sorted)
    src_items = sorted(
        ((str(k), int(v)) for k, v in (tender["source_counts"] or {}).items()),
        key=lambda kv: -kv[1],
    )[:8]
    # Strip emoji flags for shared labels
    def _src_label(raw: str) -> str:
        clean = "".join(ch for ch in raw if ord(ch) < 128).strip(" -_")
        return clean or raw[:18]

    tenders = bars(
        [
            (_src_label(lab), float(val), str(val), "#2b4a78" if i == 0 else "#1d9e75")
            for i, (lab, val) in enumerate(src_items)
        ]
        or [("Live feed", float(tender["opportunities"]), str(tender["opportunities"]), "#2b4a78")],
        max_v=max((v for _, v in src_items), default=1) or 1,
    )

    css = r"""
@page { size: A4; margin: 12mm; }
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#d9d3c8;font-size:12.4px;line-height:1.45}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:#15233c;margin:0;font-weight:600}
a{color:#15233c}
.sheet{max-width:210mm;margin:0 auto;padding:12px 0 40px}
.paper-page{
  background:#f7f4ee;color:#222;width:210mm;min-height:277mm;margin:0 auto 14px;
  padding:9mm 11mm 16mm;position:relative;box-shadow:0 2px 10px rgba(21,35,60,.18);
  break-after:page;page-break-after:always
}
.paper-page.cover{padding:0;background:#15233c;color:#eef1f6}
.ph{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;
  font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#6b6256}
.cover .ph{color:#a9bad4;padding:10mm 12mm 0}
.pn{letter-spacing:.08em}
h2{font-size:20px;line-height:1.2;margin:0 0 8px;padding-bottom:6px;border-bottom:2px solid #15233c}
.cover h1{color:#fff;font-size:28px;line-height:1.12;padding:0 12mm}
.rule{width:54mm;height:3px;background:#c0552d;margin:10px 12mm 12px}
.thesis{padding:0 12mm;color:#d5dce8;font-size:15px;max-width:78ch;margin:0 0 16px}
.verdict{font-size:13.5px;margin:0 0 12px;color:#15233c;font-weight:600}
.verdict:first-letter{font-family:Georgia,serif}
.lede{margin:0 0 10px;color:#3a3a3a;max-width:92ch}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;padding:0 12mm 12mm}
@media(min-width:700px){.stats{grid-template-columns:repeat(4,1fr)}}
.stat{background:rgba(255,255,255,.07);border-left:3px solid #c0552d;padding:10px 12px;position:relative}
.stat .l{font-size:10px;color:#a9bad4;text-transform:uppercase;letter-spacing:.4px}
.stat .v{font-size:22px;color:#fff;font-family:Georgia,serif;margin-top:2px}
.stat .s{font-size:10.5px;color:#9fb0cc;margin-top:3px;line-height:1.35}
.stat .tip{display:none;position:absolute;left:0;top:calc(100% + 6px);width:min(280px,70vw);
  background:#f7f4ee;color:#222;border-top:3px solid #c0552d;padding:10px 12px;z-index:20;
  font-size:11.5px;line-height:1.4;box-shadow:0 8px 20px rgba(0,0,0,.25)}
.stat:hover .tip,.stat:focus-within .tip{display:block}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0}
.card{background:#fff;border:1px solid #e3ded3;padding:10px 12px;border-radius:4px}
.card h3{font-size:13px;margin-bottom:6px}
.chartbox{background:#fff;border:1px solid #e3ded3;border-radius:5px;padding:10px 12px 8px;margin:8px 0 10px}
.chartttl{font-size:11.5px;color:#15233c;font-weight:600;margin-bottom:8px;font-family:Georgia,serif}
.chart-wrap{position:relative;height:200px;display:none}
.bars{display:flex;flex-direction:column;gap:3px}
.bar-row{display:grid;grid-template-columns:minmax(72px,28%) 1fr minmax(92px,30%);gap:5px;align-items:center;font-size:10.5px}
.bl{color:#52514e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bt{background:#eceae4;height:11px;border-radius:2px;overflow:hidden}
.bf{display:block;height:100%;min-width:2px}
.bv{text-align:right;font-variant-numeric:tabular-nums;color:#15233c}
.callout{border-left:3px solid #c0552d;background:#fff;padding:8px 12px;margin:8px 0;border-radius:0 4px 4px 0}
.callout.good{border-left-color:#1d9e75;background:#f2faf6}
.callout.amber{border-left-color:#c48a16;background:#fdf6e8}
.callout.unk,.unk-panel{border-left:3px solid #6b6256;background:#eeeae3;padding:8px 12px;margin:8px 0}
.unk-tag{display:inline-block;background:#6b6256;color:#f7f4ee;font-size:9px;letter-spacing:.08em;
  padding:1px 6px;border-radius:2px;margin-right:4px;font-weight:700}
table{width:100%;border-collapse:collapse;margin:8px 0;font-size:11.2px;background:#fff}
th{background:#15233c;color:#fff;text-align:left;padding:5px 7px;font-size:9.5px;text-transform:uppercase;letter-spacing:.3px}
td{padding:5px 7px;border-bottom:1px solid #e8e3d8}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:nth-child(even){background:#faf8f4}
.tl{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:middle}
.g{background:#1d9e75}.a{background:#c48a16}.r{background:#c0453c}
.swot{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.swot-q h3{font-size:14px;margin-bottom:8px;padding-bottom:4px;border-bottom:2px solid #c0552d}
.swot-cell{background:#fff;border:1px solid #e3ded3;padding:6px 8px;margin-bottom:6px;break-inside:avoid}
.swot-cell .claim{font-weight:600;color:#15233c;margin:0 0 4px}
.swot-cell .money{margin:0 0 4px;color:#3a3a3a}
.swot-cell .unk-line,.swot-cell .dec{margin:0 0 3px;font-size:11px;color:#52514e}
.ask{display:grid;grid-template-columns:42px 1fr;gap:8px;background:#fff;border:1px solid #e3ded3;padding:8px 10px;margin:0 0 8px}
.ask .no{font-family:Georgia,serif;font-size:22px;color:#c0552d}
.ask h3{font-size:13.5px;margin-bottom:2px}
.toc{padding:0 12mm 14mm;color:#c8d3e4;font-size:11.5px;columns:2;column-gap:24px}
.toc b{color:#fff;font-weight:600}
.legend span{display:inline-block;margin-right:12px}
.pf{position:absolute;left:12mm;right:12mm;bottom:7mm;font-size:8.5px;color:#6b6256;border-top:1px solid #e3ded3;padding-top:4px}
.cover .pf{color:#8aa0bd;border-top-color:#2b3d5c}
.src td{font-size:10.5px}
kbd{font-family:Consolas,monospace;font-size:10px;background:#eceae4;padding:1px 4px}
@media print{
  body{background:#fff}
  .sheet{padding:0;max-width:none}
  .paper-page{box-shadow:none;margin:0;width:auto;min-height:0;padding:8mm 10mm 10mm}
  .stat .tip{display:none !important}
  .chart-wrap, body.js-ok .chart-wrap{display:none !important}
  body.js-ok .chartbox:has(.chart-wrap) .bars{display:flex !important}
  .pf{position:static;margin-top:8px}
  h2{font-size:17px}
  .verdict{font-size:12.5px}
}
body.js-ok .chart-wrap{display:block}
body.js-ok .chartbox:has(.chart-wrap) .bars{display:none}
"""

    pages = []

    # --- 1 Cover ---
    pages.append(f"""
<section class="paper-page cover" id="p1" data-page="1">
  <header class="ph"><span class="pk">ISZE · IML top management</span><span class="pn">Page 1 of 16</span></header>
  <p style="padding:8px 12mm 0;color:#a9bad4;letter-spacing:.16em;text-transform:uppercase;font-size:11px;margin:0">Aftersales commercialisation · not vehicle manufacturing</p>
  <h1>The quotable gap is clutch and brake — not the filter worked example</h1>
  <div class="rule"></div>
  <p class="thesis">We billed <b style="color:#fff">{CEILING['captured_s']} against a {CEILING['wallet_s']} CY2025 target-spend ceiling</b> ({CEILING['pct_s']}). <b style="color:#fff">{PLACEHOLDER_PCT} of that ceiling is a flat €250/UIO placeholder</b> — cover reads 29–44% under defensible alternatives. The largest quotable component gaps are <b style="color:#fff">clutch disc €3.14M, brake pad €2.78M, brake shoe €2.47M</b> (46% of an €18.22M basket gap). Independent unit volume is <b style="color:#fff">UNKNOWN</b>. Ready levers already sit on the table.</p>
  <div class="stats">
    <div class="stat" tabindex="0">
      <div class="l">Parts billed vs target · CY2025</div>
      <div class="v">{CEILING['pct_s']}</div>
      <div class="s">{CEILING['captured_s']} of {CEILING['wallet_s']} · {PLACEHOLDER_PCT} of ceiling is flat €250/UIO</div>
      <div class="tip">Captured parts billed ÷ max-spend ceiling (target spend per truck × trucks in service — not a forecast). {PLACEHOLDER_N} near-flat markets at ~€250/UIO hold {PLACEHOLDER_PCT} of the ceiling. Sensitivity: 43.6% (non-flat median €364), 40.6% (Portugal €423), 29.4% (ITUK €745). Traffic-light spend per truck is a sibling metric on page 3.</div>
    </div>
    <div class="stat" tabindex="0">
      <div class="l">Top 3 category gaps</div>
      <div class="v">€8.39M</div>
      <div class="s">Clutch disc + brake pad + brake shoe · 46% of €18.22M</div>
      <div class="tip">From the PMS opportunity matrix (CY2025, 14-category service basket). Oil filter on that matrix is only €0.32M (1.8%). The IML UK-truck oil-filter 35.1% story on page 4 is a method illustration — not the euro lead.</div>
    </div>
    <div class="stat" tabindex="0">
      <div class="l">Eucon GP at risk (scraped set)</div>
      <div class="v">€2.21M</div>
      <div class="s">44 PNs · rotor GM 40.8% · pad kit 32.2%</div>
      <div class="tip">Gross-profit layer from the Eucon UK 2023 contested set — scraped-set evidence, not ISZE realised CO-PA. External ATD blended GP rates are never merged into the verify spine. Prefer margin over billed euro when prioritising.</div>
    </div>
    <div class="stat" tabindex="0">
      <div class="l">Books as-of</div>
      <div class="v">30 Jun 2026</div>
      <div class="s">Verify {VERIFY_PASS} pass / {VERIFY_FAIL} fail · CY2026 = Jan–Jun YTD</div>
      <div class="tip">Last billing date in the parts fact table. CY2025 is complete. Never annualise YTD into a fake full year. Apr–Jun 2026 sales-type codes are incomplete — credit/return exclusion for that quarter is sign-based only.</div>
    </div>
  </div>
  <div class="toc">
    <div><b>2</b> How to read the numbers</div>
    <div><b>3</b> Parts billed vs target + ceiling honesty</div>
    <div><b>4</b> Component gap ranking + gap types</div>
    <div><b>5</b> Mix — quality of what was sold</div>
    <div><b>6</b> Distributor league</div>
    <div><b>7</b> Dealer network scores</div>
    <div><b>8</b> Price, margin, no-list PNs</div>
    <div><b>9</b> Demand, replenishment, forecast</div>
    <div><b>10</b> Public tenders (live)</div>
    <div><b>11</b> Holes — warranty, telematics, integrity</div>
    <div><b>12–13</b> SWOT (ISZE aftersales)</div>
    <div><b>14</b> Ready levers in 90 days</div>
    <div><b>15</b> What would change our mind</div>
    <div><b>16</b> Sources and verify stamp</div>
  </div>
  <footer class="pf">shared · English · printable A4 · self-contained (no network required to paint)</footer>
</section>
""")

    # --- 2 How to read ---
    pages.append(page(2, "Legend", "How to read this paper",
        "Every headline here is either a signed CY2025 fact, a labelled YTD, or an explicit UNKNOWN — never a blended Israel, never a fake independent-garage share, never an external GP rate dressed as a verify KPI.",
        f"""
<p class="lede">This is an aftersales <b>commercialisation</b> paper for the European parts hub. It is not a Japan P&amp;L, not a vehicle-sales review, and not a new 0–100 score (that scoring family is closed).</p>
<div class="grid2">
  <div class="card">
    <h3>What the numbers are</h3>
    <p><b>Parts billed vs target</b> — euros billed versus a max-spend ceiling (target spend per truck × trucks in service). <b>Ceiling is not a forecast</b>, and about {PLACEHOLDER_PCT} of it is a flat €250/UIO placeholder — page 3 prints the sensitivity. Green spend-per-truck is ≥ €150. Spend per truck and workshop cover are two different questions.</p>
    <p><b>PMS total</b> — units sold in the service basket versus expected demand. Headline is total (genuine + BVP). Genuine is a quality lens only.</p>
    <p><b>Component gap ranking</b> — from the opportunity matrix. That ranking is the euro lead; the UK-truck IML oil-filter story is a method illustration.</p>
    <p><b>Gross margin</b> on page 8 is Eucon scraped-set evidence (or UNKNOWN). External industry GP composites stay labelled external.</p>
    <p><b>CY2025</b> is complete. <b>2026 YTD</b> is 1 January–{BILLING_MAX}. Partial years are never annualised.</p>
  </div>
  <div class="card">
    <h3>What the numbers are not</h3>
    <p><b>Two UK-truck covers exist.</b> Method illustration = IML service schedule (oil-filter 35.1%, UIO 22,389, gap €2.04M). Distributor ranking uses one shared denominator (bucketed trucks in service 23,068). They answer different questions. IML filters assume 1.25 services/yr; the network lane uses 0.5 — that alone is a 2.5× denominator difference.</p>
    <p><b>Israel is two distributors</b> — UTI and UMI — always two rows. The Israel dealer-score round is UMI only.</p>
    <p><b>IUK is not ITUK.</b> Ireland is not IUK. Independent-garage <b>unit volume is UNKNOWN</b>. <code>100% − PMS</code> is residual, not IAM alone. Telematics and subscriptions have <b>no workspace data</b> — sized as a modelled option or named as a data gap, never merged into an internal KPI.</p>
  </div>
</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Independent-garage unit share · unsigned list-to-pocket euros · air-filter interval pending IML confirmation · UK-truck brake wear 0.4 vs 0.8 · ISZE realised CO-PA margin by category · connected-vehicle / VIN feed.</div>
<div class="callout good">{REF_SELL_OUT_EN} We say OEM peer retail / reference dealer price — never slang for the counter.</div>
<p class="lede" style="margin-top:10px"><span class="legend"><span><i class="tl g"></i>Green ≥ €150/UIO or a signed fact</span> <span><i class="tl a"></i>Amber — incomplete or watch</span> <span><i class="tl r"></i>Red — material gap on a signed definition</span> <span><i class="tl" style="background:#6b6256"></i>Grey — UNKNOWN</span></span></p>
"""))

    # --- 3 GPS ---
    pages.append(page(3, "Billed vs target", "Parts billed versus target spend — and the placeholder in the ceiling",
        f"CY2025 the hub billed {CEILING['captured_s']} against a {CEILING['wallet_s']} max-spend ceiling ({CEILING['pct_s']}). About {PLACEHOLDER_PCT} of that ceiling is a flat €250/UIO placeholder — the same billed book reads 29–44% cover under defensible alternatives.",
        f"""
<p class="lede">Spend per truck on the traffic light is green in 15 of 18 markets with trucks in service. That is not the same as filling the ceiling: ITUK is green per truck and still sits at {ITUK_PCT:.1f}% of its target spend — the largest euro pool below the ceiling.</p>
<div class="callout amber"><b>{PLACEHOLDER_PCT} of the {CEILING['wallet_s']} ceiling is a flat €250/UIO placeholder</b> ({PLACEHOLDER_N} near-flat markets). Sensitivity if those markets used other signed targets: non-flat median €364 → cover <b>43.6%</b>; Portugal €423 → <b>40.6%</b>; ITUK €745 → <b>29.4%</b>. The {('€%.0fM' % CEILING['uncaptured_m'])} residual inherits the assumption. Ceiling = max-spend, not a forecast.</div>
<div class="chartbox">
  <div class="chartttl">Euros still below the target-spend ceiling concentrate in three distributors · CY2025</div>
  {below_ceiling_bars}
  <div class="chart-wrap"><canvas id="cBelowCeiling" aria-hidden="true"></canvas></div>
</div>
<div class="chartbox">
  <div class="chartttl">Spend per truck is green across most of the trucks in service; Hungary, UK LCV and Greece are amber · CY2025</div>
  {gps_spu}
  <div class="chart-wrap"><canvas id="cGps" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="callout amber"><b>UMI warranty distorts the green light.</b> Headline spend per truck is €179 (green). Strip warranty parts and it is €82 (red). This paper recommends the room keep both figures and prefer the ex-warranty number when comparing capture quality across distributors.</div>
  <div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Ukraine, Armenia, Kazakhstan and Palestine bill parts but have no GPS trucks in service in this league — about €1.62M CY2025 omitted, not zero. MIDI is not an ISZE customer row here. 2026 YTD spend per truck is half a year against a full-year trucks-in-service base — it is not a traffic light.</div>
</div>
<p class="lede">2026 year-to-date parts billed in the 18 GPS markets: <b>€8.76M</b> through {BILLING_MAX}. That is a stub, not a run-rate.</p>
"""))

    # --- 4 Capture / opportunity ---
    pages.append(page(4, "Opportunity", "Component gaps — clutch and brake lead; oil filter is the method story",
        "The quotable network basket gap is €18.22M. Clutch disc, brake pad and brake shoe alone are €8.39M (46%). The UK-truck IML oil-filter 35.1% story remains the method illustration — not the euro lead.",
        f"""
<p class="lede">Rank by euro at stake from the opportunity matrix (CY2025). Oil filter on that matrix is €0.32M (1.8%). Gap types (model year 2026 file): substitution €11.40M · under-service €9.56M · catalogue gap €2.18M — opposite commercial responses.</p>
<div class="chartbox">
  <div class="chartttl">Largest component gaps: clutch disc €3.14M, brake pad €2.78M, brake shoe €2.47M · CY2025</div>
  {cat_gap}
  <div class="chart-wrap"><canvas id="cCatGap" aria-hidden="true"></canvas></div>
</div>
<div class="chartbox">
  <div class="chartttl">Gap type (2026 model vintage): substitution is a price fight; under-service is a workshop-demand fight</div>
  {gap_types}
  <div class="chart-wrap"><canvas id="cGapTypes" aria-hidden="true"></canvas></div>
</div>
<div class="callout"><b>Method illustration — not the opportunity lead.</b> IML UK-truck service schedule: filters 1.25/yr (network lane uses 0.5 — a 2.5× denominator difference), clutch and brake 0.5, trucks in service 22,389. Oil-filter cover 35.1%, five-category gap €2.04M (air €736k, brake €642k, clutch €393k). Keep this as the worked example of schedule math — do not let it own the room’s priority list.</div>
<div class="chartbox">
  <div class="chartttl">IML UK-truck five-category gap euros (method illustration) · CY2025</div>
  {iml_gap}
  <div class="chart-wrap"><canvas id="cImlGap" aria-hidden="true"></canvas></div>
</div>
<div class="callout amber"><b>Network-comparable ranking uses a different denominator</b> (bucketed trucks in service 23,068 for the UK truck row). On that ranking UK truck oil-filter total is above 100% uncapped — valid when actuals include sales beyond the truck-only proxy. It is <b>not</b> the 35.1% IML figure. Ireland’s uncapped 191% is why this paper does not plot a “best market” series.</div>
<div class="chartbox">
  <div class="chartttl">Network-comparable oil-filter total (capped display) — for ranking only · CY2025</div>
  {pms_net}
  <div class="chart-wrap"><canvas id="cPms" aria-hidden="true"></canvas></div>
</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Jobs not sold through the dealer are not independent-garage volume. Air-filter interval on the network-comparable view is a provisional 0.5 factor until IML confirms. Capture-recovery gap types are a 2026 model year file — labelled as such.</div>
"""))

    # --- 5 Mix ---
    pages.append(page(5, "Quality", "Mix — quality of what was sold, not capture",
        "Of the €30.76M billed in CY2025, 96.5% is genuine and 3.5% is BVP (€1.06M) — mix sits two orders of magnitude below the euro still outside the target-spend ceiling.",
        f"""
<p class="lede">BVP is a down-trade inside the tent. It has <b>no capture rate</b>. Treating BVP mix as “BVP capture” would invent a KPI. The commercial question is whether mix is eating margin on a book we already sell — not whether we “captured BVP.”</p>
<div class="chartbox">
  <div class="chartttl">BVP is a thin slice of captured sales except at UTI, Cyprus, Greece and Portugal · CY2025</div>
  {mix_bvp}
  <div class="chart-wrap"><canvas id="cMix" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>Distributor mix (captured book)</h3>
    <p>ITUK 97.3% genuine · UTI 88.9% genuine (11.1% BVP) · UMI 96.3% genuine · IUK 99.1% genuine. UTI and UMI are two Israel distributors — never averaged.</p>
  </div>
  <div class="callout">
    <h3>Shell 5500* is lubricant, not bumper iron</h3>
    <p>Prefix 5500* on the UMI book is Shell Rimula, excluded from “pure” GPS sales and stored separately. Fiscal 2025 Shell on UMI: <b>€520k</b>. Do not bury it in unclassified hardware. The older “€442k lubricants project” line is not used here — it was never tied to this extract.</p>
  </div>
</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Gross-profit given up to down-trade is a modelled extra, not a GPS headline. This page quotes mix of billed euros, which is signed. Do not add mix “loss” to the €29.5M below-target pool — different questions.</div>
"""))

    # --- 6 League ---
    pages.append(page(6, "League", "Distributor league — three separate columns",
        "Read three columns as three questions: spend per truck, network-comparable oil-filter cover, and genuine mix — never one blended score. Keep UTI, UMI, ITUK and IUK as four different rows.",
        f"""
<table>
  <thead>
    <tr><th>Distributor</th><th class="n">€ / truck</th><th>Light</th><th class="n">Billed vs target %</th><th class="n">Oil-filter total*</th><th class="n">Genuine mix</th></tr>
  </thead>
  <tbody>
    <tr><td>Ireland</td><td class="n">389</td><td><i class="tl g"></i>Green</td><td class="n">{cov('IRELAND')}</td><td class="n">100% cap</td><td class="n">95.5%</td></tr>
    <tr><td>UTI (Israel)</td><td class="n">322</td><td><i class="tl g"></i>Green</td><td class="n">{cov('UTI')}</td><td class="n">91%</td><td class="n">88.9%</td></tr>
    <tr><td>ITUK (UK truck)</td><td class="n">249</td><td><i class="tl g"></i>Green</td><td class="n">{cov('ITUK')}</td><td class="n">100% cap</td><td class="n">97.3%</td></tr>
    <tr><td>Belgium</td><td class="n">220</td><td><i class="tl g"></i>Green</td><td class="n">{cov('BELGIUM')}</td><td class="n">63%</td><td class="n">96.6%</td></tr>
    <tr><td>Portugal</td><td class="n">209</td><td><i class="tl g"></i>Green</td><td class="n">{cov('PORTUGAL')}</td><td class="n">52%</td><td class="n">94.0%</td></tr>
    <tr><td>Germany</td><td class="n">197</td><td><i class="tl g"></i>Green</td><td class="n">{cov('GERMANY')}</td><td class="n">15%</td><td class="n">99.3%</td></tr>
    <tr><td>UMI (Israel)</td><td class="n">179</td><td><i class="tl g"></i>Green†</td><td class="n">{cov('UMI')}</td><td class="n">85%</td><td class="n">96.3%</td></tr>
    <tr><td>Norway</td><td class="n">179</td><td><i class="tl g"></i>Green</td><td class="n">{cov('NORWAY')}</td><td class="n">48%</td><td class="n">98.2%</td></tr>
    <tr><td>Sweden</td><td class="n">151</td><td><i class="tl g"></i>Green</td><td class="n">{cov('SWEDEN')}</td><td class="n">49%</td><td class="n">99.9%</td></tr>
    <tr><td>Greece</td><td class="n">139</td><td><i class="tl a"></i>Amber</td><td class="n">{cov('GREECE')}</td><td class="n">97%</td><td class="n">92.2%</td></tr>
    <tr><td>IUK (UK LCV)</td><td class="n">128</td><td><i class="tl a"></i>Amber</td><td class="n">{cov('IUK')}</td><td class="n">38%</td><td class="n">99.1%</td></tr>
    <tr><td>Hungary</td><td class="n">88</td><td><i class="tl a"></i>Amber</td><td class="n">{cov('HUNGARY')}</td><td class="n">45%</td><td class="n">96.6%</td></tr>
  </tbody>
</table>
<p class="lede">*Oil-filter total is the <b>network-comparable</b> rate (capped at 100% for display). ITUK’s 35.1% IML figure is the method illustration on page 4 — do not substitute it into this column. †UMI ex-warranty spend per truck is €82 — <b>prefer that number when comparing capture quality</b>; keep €179 when describing billed book including warranty.</p>
<div class="callout amber">Ireland’s billed-vs-target above 100% means parts billed exceeded the max-spend ceiling — over-target, not a data bug. Germany’s 15% oil-filter total on the shared denominator is the weak workshop row in this league, despite a green spend-per-truck.</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> No “Israel” average. No IUK+ITUK blend. CIS rows without trucks in service stay off this table.</div>
"""))

    # --- 7 IDS ---
    pages.append(page(7, "Dealers", "Dealer network scores versus country average",
        "Israel’s dealer round is the UMI network only (mean 60.9) — UTI did not sit that round — and four MIDI countries use a different points scale, so they are not plotted as percentages.",
        f"""
<p class="lede">Dealer score versus <b>that country’s</b> average. Labels in English. This page is a league of country means on the 0–100 packs, not a map (maps belong in the country packs, and only when pins are not clustered on a country centroid).</p>
<div class="chartbox">
  <div class="chartttl">UMI’s Israel dealer mean sits well below Portugal, Hungary and both UK networks · IDS 2026</div>
  {ids_avg}
  <div class="chart-wrap"><canvas id="cIds" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>Israel (UMI) — top of that network</h3>
    <p>Country mean <b>60.9</b> (29 dealers). Highest: Kfir Yaud 69.6 · Eden Garage Rishon 68.6 · Tel Hanan Haifa 68.6 · UMI Petach Tikva 67.5. Every one of those still sits below Portugal’s mean (86.9) and UK truck mean (83.8).</p>
  </div>
  <div class="callout amber">
    <h3>France, Italy, Spain, Switzerland — different scale</h3>
    <p>Those packs store raw points in the thousands, not a 0–100 percentage. Plotting them on this chart would fake a 5,000% score. They participated; they are not in this bar. Use the country pack for those rooms.</p>
  </div>
</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> UTI dealer scores for this IDS round — they did not participate. Do not back-fill from UMI. Weak-sector radar overlays are diagnostic clutter and are not shown.</div>
"""))

    # --- 8 Price (by part number on scraped set — not 18 country dots) ---
    n_parts = int(pn_stats.get("n_parts") or 0)
    n_below = int(pn_stats.get("n_shop_below_reference") or 0)
    med_ix = float(pn_stats.get("median_price_index") or 0)
    pages.append(page(8, "Price · margin", "Aftermarket price, Eucon margin, and no-list part numbers",
        f"On the {n_parts} parts with an aftermarket scrape and a CY2025 billed line, median price index is {med_ix:.2f}. Eucon adds €2.21M GP at risk on 44 PNs. NO_LIST on the pricing findings is about €4.96M across 251 part numbers.",
        f"""
<p class="lede">{REF_SELL_OUT_EN} Scrapes are <b>price</b>, not volume. About 28% of scrape points sit on an undated Autodoc file — vintage stays honest.</p>
<div class="chartbox">
  <div class="chartttl">Top {len(pn_slice)} parts by CY2025 billed € on the scraped set — price index (shop ÷ reference). Below 1 = shop cheaper than our reference</div>
  {pn_price_bars}
  <div class="chart-wrap"><canvas id="cPrice" aria-hidden="true"></canvas></div>
</div>
<table>
  <thead><tr><th>Part</th><th>Description</th><th class="n">Price index</th><th class="n">Billed €</th><th>Scrape vintage</th></tr></thead>
  <tbody>
    {pn_table_rows}
  </tbody>
</table>
<div class="grid2">
  <div class="card">
    <h3>Gross margin layer (Eucon UK 2023 set)</h3>
    <p><b>€2.21M GP at risk</b> across 44 contested part numbers. Brake rotor gross margin <b>40.8%</b>; brake pad kit <b>32.2%</b>. This is scraped-set evidence for prioritisation — not ISZE realised CO-PA. Prefer margin over billed euro when ranking defence lines.</p>
  </div>
  <div class="card">
    <h3>NO_LIST — cheapest euro on the table</h3>
    <p>Pricing findings: about <b>€4.96M</b> across <b>251</b> part numbers with no usable list price (on-list-no-price plus absent-from-list). That is a data/governance fix inside the opportunity set — not a demand fight.</p>
  </div>
</div>
<div class="grid2">
  <div class="card">
    <h3>What we can say on price</h3>
    <p><b>{n_parts}</b> unique part numbers · <b>{n_below}</b> with at least one shop quote below reference · median price index <b>{med_ix:.2f}</b>. That is a price fact — not an aftermarket share. Set is euro-relevant (~22% of the CY2025 parts book) but not PN-representative (0.77% of billed PNs).</p>
  </div>
  <div class="unk-panel">
    <span class="unk-tag">UNKNOWN</span>
    Independent-garage <b>unit volume</b>. ISZE realised gross margin by category (CO-PA) is not in the workspace — Eucon is the interim layer. Sales-to-dealer files exist for six distributors including Portugal (60.0% of GPS billed euro).
  </div>
</div>
<div class="callout">Full scatter: sibling launcher <kbd>OPEN_ISZE_IAM_Price_vs_Billed_PN.cmd</kbd>. A pocket gap between list and net billed <b>exists</b> as an internal question; the euro is <b>not signed</b> for external quote.</div>
"""))

    # --- 9 Demand ---
    pages.append(page(9, "Operations", "Demand, replenishment, forecast honesty",
        "Sales-to-dealer files cover 60.0% of GPS billed euro (six distributors including Portugal). Replenishment exceptions remain an observed-subset fact. Forecast median WAPE 49.4% on 548 of 636 series is normal for intermittent spares — a surface, not a signed live forecast.",
        f"""
<p class="lede">Sales-to-dealer files exist for ITUK, IUK, Ireland, UTI, Greece and Portugal = <b>60.0% of GPS billed euro</b> (€18.45M of €30.76M). Germany + Belgium would add €4.65M and lift visibility to <b>75.1%</b>. Everywhere else, “no exception” would mean “no file,” not a clean pipeline.</p>
<div class="chartbox">
  <div class="chartttl">1,595 CY2025 exception rows sit on the observed sales-to-dealer subset — not the whole network</div>
  {repl}
  <div class="chart-wrap"><canvas id="cRepl" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>Forecast surface (not go-live)</h3>
    <p><b>548 of 636</b> series back-tested. Median WAPE <b>49.4%</b> — defensible for intermittent spare parts (practice often cites 40–70%). Bias % and Forecast Value Added vs the naive baseline are not yet printed. Gate G1 is <b>unsigned</b>. Override policy is also unsigned.</p>
  </div>
  <div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Realised euros past the billing horizon. Growth-factor 1.24 / 1.25 still unsigned. The price list we might revise cannot become a price move until alloc ambition is named (+4% / +5% / launch-only) — about €510k–€638k/yr on the L12M basis.</div>
</div>
<div class="callout amber">Do not read 2026 year-to-date as a decline versus CY2025. Capture-trend alerts that treated a stub year as a full year were a known false cliff; complete-year declining pairs still on the books: Ireland clutch kit, ITUK brake rotor, Romania brake rotor, Romania clutch kit, UTI clutch kit (five, not thirty-three).</div>
"""))

    # --- 10 Tenders ---
    t_asof = (tender.get("generated_at") or "")[:19].replace("T", " ")
    t_ops = tender["opportunities"]
    t_due = tender["due_14d"]
    t_miss = tender["missing_value"]
    t_raw = tender["raw_notices"]
    t_portals = tender["portals_reporting"]
    t_gps = tender["gps_addressable_sum"]
    t_gps_n = tender["gps_nonzero_ops"]
    pages.append(page(10, "Public volume", "Public tenders — live feed, footprint play not parts revenue",
        f"Live feed as of {t_asof or 'build time'}: {t_ops} opportunities, {t_due} due in 14 days, {t_miss} of {t_raw} rows missing value, {t_portals} national sources reporting. After-sales addressable on the feed is tiny versus replenishment leakage.",
        f"""
<p class="lede">Notice count is not fleet potential and not award euro. Nordics national APIs are done — the remaining gap is portals, not credentials. Of {t_ops} opportunities, only <b>{t_gps_n}</b> carry a GPS-addressable euro (about <b>€{t_gps:,.0f}/yr</b>). That is roughly 1/48th of the visible replenishment leakage (€2.68M). <b>Tenders are a relationship and footprint play, not a parts-revenue play.</b></p>
<div class="chartbox">
  <div class="chartttl">Live source mix on the tender feed · as of {t_asof or 'build'}</div>
  {tenders}
  <div class="chart-wrap"><canvas id="cTender" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>Live cut</h3>
    <p><b>{t_ops}</b> opportunities · <b>{t_due}</b> due in 14 days · <b>{t_miss}</b> of <b>{t_raw}</b> missing extractable value · <b>{t_portals}</b> sources reporting · aftersales-tagged <b>{tender['aftersales_tagged']}</b>.</p>
  </div>
  <div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Award euros. Below-threshold volume in dark countries. Israel domestic IEC from a non-IL address. Do not invent a tender spend pool from notice counts.</div>
</div>
<div class="callout good">Credentials for the Nordic national APIs are done. Wire the next national portal (Spain fetcher is code-ready behind a firewall) — do not re-open a key setup sheet.</div>
"""))

    # --- 11 Integrity ---
    pages.append(page(11, "Holes", "Warranty, telematics, integrity — first-class UNKNOWNs",
        "Warranty parts are €4.72M (14.6% of the CY2025 billed book); claim expense fell 25% year-on-year. Telematics has no workspace data — sized only as a modelled option. Account-health thresholds are not calibrated.",
        """
<table>
  <thead><tr><th>Hole</th><th>What we know</th><th>What we do not</th></tr></thead>
  <tbody>
    <tr><td>Warranty flow</td><td>€4.72M parts billed = 14.6% of book; claim expense €4.22M → €3.18M (−25%); UMI warranty is 54% of UMI’s book</td><td>Whether the claim decline is quality or tighter authorisation — and whether dealers then push work into customer-pay at lower capture</td></tr>
    <tr><td>Telematics / subscriptions</td><td>No VIN / connected-vehicle feed in the workspace. External sizing only: at 5% attach × €20/unit/month on the 163k GPS trucks in service ≈ €1.96M/yr gross (illustrative)</td><td>OEM data ownership; real attach; ISZE product position</td></tr>
    <tr><td>Independent volume</td><td>Price baskets exist on the scraped PN set (page 8)</td><td>Unit share. Residual of PMS is not IAM.</td></tr>
    <tr><td>List-to-pocket</td><td>A pocket gap exists as an internal question</td><td>A signed euro for this room</td></tr>
    <tr><td>Sales-to-dealer coverage</td><td>Six DBs including Portugal = 60.0% of GPS billed euro; DE+BE would reach 75.1%</td><td>Every other GPS market — source gap, not 0%</td></tr>
    <tr><td>Account health</td><td>10 RED / 6 AMBER of 17 on 2026-08 snapshot · <b>thresholds_calibrated: false</b></td><td>A signed call list (Early Warning remains the sales call list)</td></tr>
    <tr><td>Defection queue</td><td>25 alerts across 14 distributors; 9 carry zero trailing-12-month revenue</td><td>Recoverable base on the zero-revenue rows</td></tr>
    <tr><td>Air / brake factors</td><td>Network air 0.5 provisional; UK-truck brake 0.4 applied</td><td>IML-locked ratios</td></tr>
    <tr><td>Forecast G1</td><td>WAPE 49.4% on 548 of 636 series</td><td>Go-live signature, bias %, FVA vs naive</td></tr>
    <tr><td>CIS / MIDI</td><td>Bill or warranty may exist (~€1.62M CIS without trucks in service)</td><td>GPS league rows (by design)</td></tr>
  </tbody>
</table>
<div class="callout amber">Credit and return lines on positive value were excluded from GPS and PMS as a documented judgment — not an ERP-confirmed netting rule. If the next extract with sales-type codes reverses the call, GPS and capture move.</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> This panel is the product. Smoothing a hole into a chart is how a careful paper becomes an unreliable one. External telematics figures must never merge into an internal verify KPI.</div>
"""))

    # --- 12 SWOT S/W ---
    pages.append(page(12, "SWOT · internal", "Strengths and weaknesses — ISZE aftersales",
        "Strengths are a green book, genuine-heavy mix, and ready commercial packs; weaknesses are an €18.22M component gap led by clutch/brake, a ceiling that is " + PLACEHOLDER_PCT + " placeholder, and unsigned pocket/forecast/alloc gates.",
        f"""
<p class="lede">Entity = the European parts hub. Internal evidence only on this page. Every cell has a claim, a euro or volume, an UNKNOWN, and the fact that would rewrite it.</p>
<div class="swot">
  <div class="swot-q">
    <h3>Strengths</h3>
    {cell(
        "The parts book is verified and current through 30 June 2026.",
        "116 pass / 0 fail · 514,037 lines · GPS-facing parts base €112.09M (2023 through YTD).",
        "Apr–Jun 2026 sales-type codes missing; credit/return exclusion for that quarter is sign-based only.",
        "Next extract with sales-type codes confirming or reversing the credit rule.")}
    {cell(
        "What we sell is still overwhelmingly genuine.",
        "96.5% genuine / 3.5% BVP of €30.76M captured CY2025 (€1.06M BVP). ITUK 97.3% genuine.",
        "Mix is not capture. BVP has no capture rate.",
        "A large distributor where BVP becomes the sold book.")}
    {cell(
        "A price-revision pack and a no-list register already exist.",
        "The price list we might revise: 6,326 PNs · €12.76M L12M · +4% ≈ €510k/yr · +5% ≈ €638k/yr. NO_LIST ≈ €4.96M / 251 PNs.",
        "Alloc ambition still unsigned (no_alloc_run). Realised CO-PA margin by category still missing.",
        "One signed alloc ambition and a named owner for the 251 no-list PNs.")}
  </div>
  <div class="swot-q">
    <h3>Weaknesses</h3>
    {cell(
        "Component gaps concentrate in clutch and brake, not filters.",
        "€18.22M matrix gap · clutch disc €3.14M · brake pad €2.78M · brake shoe €2.47M (46%). Oil filter €0.32M.",
        "Independent-garage unit volume. Structural fitment vs commercial share on 92–95% unfilled lines.",
        "A brake/clutch pilot with pre-registered success criteria — or a fitment audit that reclassifies the gap.")}
    {cell(
        "The headline cover inherits a flat-ceiling placeholder.",
        f"{CEILING['pct_s']} of {CEILING['wallet_s']} · " + PLACEHOLDER_PCT + " of ceiling at flat €250/UIO · sensitivity 29.4–43.6%.",
        "Per-market age-spend curves.",
        "Age-band targets replacing the flat €250 assumption.")}
    {cell(
        "Realization, forecast G1, and account-health thresholds are unsigned.",
        "Pocket euro: not quoted. WAPE 49.4% on 548 of 636. Account health 10 RED / 6 AMBER with thresholds_calibrated: false.",
        "Bias % / FVA vs naive; recoverable base on zero-revenue defection rows.",
        "Written list-to-pocket sign-off, G1 yes/no, and calibrated thresholds.")}
  </div>
</div>
"""))

    # --- 13 SWOT O/T ---
    pages.append(page(13, "SWOT · external", "Opportunities and threats — still sourced or UNKNOWN",
        "Named euro opportunities are the matrix clutch/brake gaps, price-list revision ambition, no-list PNs, and DE/BE sales-to-dealer files; the named threat is independent price without independent volume — plus a telematics option with no VIN feed.",
        f"""
<div class="swot">
  <div class="swot-q">
    <h3>Opportunities</h3>
    {cell(
        "Sign price-list revision ambition — highest return per unit of effort already built.",
        "6,326 PNs · €12.76M L12M. +4% ≈ €510k/yr · +5% ≈ €638k/yr on L12M. Pack built 2026-08-19; no_alloc_run today.",
        "Which ambition (+4% / +5% / launch-only). Cross-check vs price-index &lt; 0.5 lines before publishing.",
        "One signed alloc ambition.")}
    {cell(
        "Close no-list and the two missing sales-to-dealer files (Germany, Belgium).",
        "NO_LIST ≈ €4.96M / 251 PNs. DE+BE sales-to-dealer files would lift visibility 60.0% → 75.1% of billed euro.",
        "Owner for the 251 PNs. DB IT cooperation for the three files.",
        "Named owners and verified sales-to-dealer longs.")}
    {cell(
        "Brake and clutch capture is the pilot, not oil filter.",
        "€8.39M in the top three categories. Eucon rotor GM 40.8% / pad kit 32.2% for margin prioritisation.",
        "Per-dealer variance for a formal power calculation — do not open a pilot on a guess sample size.",
        "Pre-registered ≥8 pt capture lift on brake pad (and clutch) with price-index guardrails.")}
    {cell(
        "Telematics is a modelled option — or a written no.",
        "Illustrative: 5% attach × €20/unit/month on 163k GPS trucks in service ≈ €1.96M/yr gross (external sizing). Comparable to base-case 36-month component SOM.",
        "VIN / connected-vehicle feed and OEM data ownership — data we do not have.",
        "A board decision either to build or to state ISZE will not.")}
  </div>
  <div class="swot-q">
    <h3>Threats</h3>
    {cell(
        "Independent price at the counter undercuts reference dealer price on a thin basket.",
        f"{n_parts} PN on the scraped ∩ billed set · {n_below} with a shop quote below reference. Coverage too thin to be share.",
        "Independent unit volume. Vintage labels must stay honest on every shared price file.",
        "One family of independent unit counts, or honest vintage labels on every shared price file.")}
    {cell(
        "Calling residual PMS “independent share” would steer the room at the wrong enemy.",
        f"Target-spend residual ~{('€%.0fM' % CEILING['uncaptured_m'])} · matrix gap €18.22M · IML UK-truck schedule gap €2.04M. Different questions.",
        "The true IAM split of either residual.",
        "Any IAM % invented from 100% − PMS — refuse it.")}
    {cell(
        "Tender notice counts look like a revenue pool and are not.",
        f"Live: {t_ops} opportunities · ~€{t_gps:,.0f}/yr GPS-addressable on {t_gps_n} rows — footprint, not parts €.",
        "Award euros.",
        "Keep tenders out of the parts-revenue priority list.")}
    {cell(
        "The ICE peak window (2025–2032) is time-bounded; a new composite score will not extend it.",
        "Stance: peak ICE D-Max / N-series parts window is open now. Scoring 0–100 is closed.",
        "Exact year of peak by market.",
        "Fleet cohort by market — not a revived score.")}
  </div>
</div>
"""))

    # --- 14 Asks ---
    pages.append(page(14, "90 days", "Ready levers and five asks already on the table",
        "Lead with what is already built: price-list revision ambition, no-list ownership, and DE/BE sales-to-dealer files. Then the five signed asks. Nothing here is a new programme.",
        """
<div class="ask"><div class="no">1</div><div>
  <h3>The price list we might revise — alloc ambition +4% / +5% / launch-only</h3>
  <p>6,326 PNs · €12.76M L12M already packed. +4% ≈ €510k/yr · +5% ≈ €638k/yr. Highest return-per-effort action available today. <b>No answer:</b> no DB-specific list move that survives the guardrails.</p>
</div></div>
<div class="ask"><div class="no">2</div><div>
  <h3>Name an owner for NO_LIST (~€4.96M / 251 PNs)</h3>
  <p>Cheapest euro on the table — a list/price governance fix, not a demand programme. <b>No answer:</b> the gap stays unowned inside the opportunity set.</p>
</div></div>
<div class="ask"><div class="no">3</div><div>
  <h3>Sign list-to-pocket — or keep realization internal</h3>
  <p>Year-matched list-to-net joins ran as validation. Until there is a written sign-off, this paper will not quote the pocket euro. <b>No answer:</b> shared packs stay silent on realization.</p>
</div></div>
<div class="ask"><div class="no">4</div><div>
  <h3>G1 — sign the forecast surface, or wait</h3>
  <p>Median WAPE 49.4% on 548 of 636 series is already on the table (normal for intermittent spares). Bias % and FVA vs naive still missing. <b>No answer:</b> forecast cannot go live; allocation cannot inherit it.</p>
</div></div>
<div class="ask"><div class="no">5</div><div>
  <h3>Account-health thresholds — calibrate before it is a call list</h3>
  <p>Draft flags: 10 RED / 6 AMBER of 17 · <b>thresholds_calibrated: false</b>. Defection: 25 alerts, 9 with zero trailing revenue. <b>No answer:</b> that queue is not a call list. Early warning on sales stays the call list until amber/red are signed.</p>
</div></div>
<div class="unk-panel"><span class="unk-tag">NOT AN ASK</span> Nordic tender API keys — done. Gross/SPA on billing — closed, net-only forever. A new 0–100 score — closed. Oil-filter as the network opportunity lead — retired by the matrix. This paper is not a new programme on the build queue.</div>
<p class="lede">Also waiting: UK-truck brake 0.4 vs 0.8; DE/BE sales-to-dealer files files; growth-factor 1.24/1.25; DPO path before any telematics build; connected-vehicle position (build or written no).</p>
"""))

    # --- 15 Falsifiers ---
    pages.append(page(15, "Disagree well", "What would change our mind",
        "These are the smallest facts that would rewrite the thesis — not moving goalposts.",
        f"""
<ol style="padding-left:18px;max-width:92ch">
  <li style="margin-bottom:8px"><b>Age-spend curves replacing flat €250/UIO</b> on the {PLACEHOLDER_N} placeholder markets. Would rewrite the {CEILING['pct_s']} headline and the {('€%.0fM' % CEILING['uncaptured_m'])} residual.</li>
  <li style="margin-bottom:8px"><b>One family of independent unit counts</b> (oil or air, one large market). Would retire “IAM volume UNKNOWN.”</li>
  <li style="margin-bottom:8px"><b>ISZE realised gross margin by category (CO-PA)</b>. Would replace Eucon scraped-set GP as the prioritisation layer.</li>
  <li style="margin-bottom:8px"><b>Written list-to-pocket sign-off</b> on year-matched joins — or kill the figure if the join fails.</li>
  <li style="margin-bottom:8px"><b>G1 on the forecast surface</b> (or an explicit wait), plus bias % / FVA vs naive.</li>
  <li style="margin-bottom:8px"><b>Germany or Belgium sales-to-dealer long</b>. Would prove whether replenishment leakage is a five-DB story or a network pattern (path to 75.1% of billed euro).</li>
  <li style="margin-bottom:8px"><b>Next SAP extract with sales-type codes for Apr–Jun 2026</b>. Would confirm or reverse the credit/return judgment.</li>
  <li style="margin-bottom:8px"><b>A connected-vehicle / VIN decision</b> — build telematics or state in writing that ISZE will not.</li>
</ol>
<div class="callout">If none of these arrive, the thesis on page 1 still holds: we bill about half a ceiling that is {PLACEHOLDER_PCT} placeholder; the quotable gap is clutch and brake (€8.39M of €18.22M); Eucon GP and the price list are ready levers; independent volume is UNKNOWN; tenders are footprint not parts €.</div>
"""))

    # --- 16 Sources ---
    pages.append(page(16, "Audit", "Sources, as-of, verify stamp",
        f"Verify is green: {VERIFY_PASS} pass / {VERIFY_FAIL} fail at {VERIFY_AT}; billing through {BILLING_MAX}; filenames live on this page only.",
        f"""
<table class="src">
  <thead><tr><th>Claim in this paper</th><th>Definition / grain</th><th>Where</th></tr></thead>
  <tbody>
    <tr><td>{CEILING['pct_s']} · {CEILING['captured_s']} / {CEILING['wallet_s']} · {PLACEHOLDER_PCT} flat €250</td><td>Parts billed vs max-spend ceiling; placeholder share of ceiling</td><td>max-spend waterfall CSV (assumption_note)</td></tr>
    <tr><td>€18.22M · clutch disc €3.14M · brake pad €2.78M · brake shoe €2.47M</td><td>PMS opportunity matrix CY2025 category gaps</td><td>pms_opportunity_matrix.csv</td></tr>
    <tr><td>Substitution €11.4M / under-service €9.6M / catalogue gap €2.2M</td><td>Capture recovery model year 2026</td><td>capture_recovery_model.csv</td></tr>
    <tr><td>35.1% · €2.04M · UIO 22,389</td><td>IML service schedule method illustration, UK truck</td><td>Apr 2026 PMS analysis / FACTS §1</td></tr>
    <tr><td>€2.21M GP at risk · rotor 40.8% · pad kit 32.2%</td><td>Eucon UK 2023 scraped set (not CO-PA)</td><td>eucon_price_gap.csv</td></tr>
    <tr><td>NO_LIST ≈ €4.96M / 251 PNs</td><td>Pricing findings network no usable list</td><td>pricing_history_findings.json</td></tr>
    <tr><td>Warranty €4.72M = 14.6% · claims €3.18M (−25%)</td><td>Parts billed warranty share; claim expense YoY</td><td>gps_spu + warranty_by_db_year</td></tr>
    <tr><td>Sales to dealer 60.0% of billed euro (to 75.1% with DE/BE)</td><td>Six DBs with sales-to-dealer longs / GPS billed</td><td>max-spend waterfall CSV + sales-to-dealer longs</td></tr>
    <tr><td>Price list 6,326 PNs · €12.76M · +4%/+5%</td><td>Revision pack; no_alloc_run</td><td>book_b_bucket_summary + revision meta</td></tr>
    <tr><td>{t_ops} opportunities · {t_due} due 14d · ~€{t_gps:,.0f}/yr addressable</td><td>Live tender feed as of {t_asof or 'build'}</td><td>tender_data.json</td></tr>
    <tr><td>WAPE 49.4% · 548 of 636</td><td>Unsigned forecast surface</td><td>forecast_baseline.meta.json</td></tr>
    <tr><td>10 RED / 6 AMBER · thresholds_calibrated: false</td><td>Account-health draft flags</td><td>account_health.meta.json</td></tr>
    <tr><td>Telematics ~€1.96M/yr @ 5%×€20</td><td>External modelled option — not an internal KPI</td><td>named data gap (no VIN feed)</td></tr>
    <tr><td>PN price vs aftermarket</td><td>{n_parts} PN scraped ∩ CY2025 billed; median index {med_ix:.2f}</td><td>IAM vs billed PN builder</td></tr>
  </tbody>
</table>
<div class="grid2">
  <div class="card">
    <h3>Verify stamp</h3>
    <p>Pass {VERIFY_PASS} · fail {VERIFY_FAIL} · generated {VERIFY_AT}<br>
    Fact table 514,037 rows · billed {BILLING_MAX}<br>
    GPS-facing parts €112.09M (cumulative 2023–YTD)</p>
  </div>
  <div class="card">
    <h3>Which cover, which page</h3>
    <p>Pages 1, 4 (matrix ranking), 12–14 — component gaps and ready levers.<br>
    Page 4 method block + page 6 — IML 35.1% illustration and network-comparable ranking (different denominators).<br>
    External telematics / ATD GP never merge into verify KPIs.</p>
  </div>
</div>
<p class="lede">Open this file with the sibling launcher <kbd>OPEN_ISZE_Exec_Aftersales_Paper.cmd</kbd>. Double-click paints without a server; charts are CSS bars plus inline Chart.js (no CDN).</p>
"""))

    pn_labels = [((p.get("description") or p["pn"])[:22]).replace("'", "") for p in pn_slice]
    pn_vals = [round(float(p["price_index"]), 3) for p in pn_slice]
    pn_cols = ["'#c0552d'" if p["shop_below_reference"] else "'#1d9e75'" for p in pn_slice]
    js_boot = r"""
(function(){
  try {
    var q = (location.hash || '').replace(/^#p/, '') || new URLSearchParams(location.search).get('page');
    if (q) {
      document.querySelectorAll('.paper-page').forEach(function(el){
        if (el.getAttribute('data-page') !== q) el.style.display = 'none';
      });
      document.body.style.background = '#f7f4ee';
    }
  } catch (e) {}
  if (typeof Chart === 'undefined') return;
  document.querySelectorAll('.chart-wrap').forEach(function(el){ el.style.display = 'block'; });
  const ink = '#15233c', terr = '#c0552d', grid = '#e6e2d8';
  Chart.defaults.font.family = 'Segoe UI, Helvetica, Arial, sans-serif';
  Chart.defaults.font.size = 10;
  Chart.defaults.color = '#52514e';
  function bar(id, labels, data, colors){
    const el = document.getElementById(id);
    if (!el) return;
    new Chart(el, {type:'bar', data:{labels:labels, datasets:[{data:data, backgroundColor:colors, borderWidth:0, barPercentage:0.72, categoryPercentage:0.8}]},
      options:{indexAxis:'y', responsive:true, maintainAspectRatio:false, animation:false,
        plugins:{legend:{display:false}},
        scales:{x:{grid:{color:grid}, beginAtZero:true},
                y:{grid:{display:false}, ticks:{autoSkip:false}}}}});
  }
  bar('cBelowCeiling', ['ITUK','IUK','UTI','PT','UMI','DE','HU','NO'],
      [11.61,5.81,4.94,1.34,1.32,1.27,0.60,0.57],
      [terr,terr,terr,'#8a6a4a','#8a6a4a','#8a6a4a','#8a6a4a','#8a6a4a']);
  bar('cGps', ['IE','UTI','ITUK','FI','BE','PT','DE','UMI','NO','SE','GR','IUK','HU'],
      [389,322,249,231,220,209,197,179,179,151,139,128,88],
      ['#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c48a16','#c48a16']);
  bar('cImlGap', ['Air','Brake','Clutch','Oil','Fuel'], [736,642,393,141,127],
      ['#c0453c',terr,terr,'#8a6a4a','#8a6a4a']);
  bar('cCatGap', ['Clutch disc','Brake pad','Brake shoe','Clutch PP','Blower','Brake rotor','Fuel','Clutch kit'],
      [3.14,2.78,2.47,1.98,1.42,1.39,1.02,0.96],
      ['#c0453c','#c0453c',terr,terr,'#c48a16','#c48a16','#8a6a4a','#8a6a4a']);
  bar('cGapTypes', ['Substitution','Under-service','Catalogue gap'], [11.4,9.56,2.18],
      [terr,'#c48a16','#6b7c93']);
  bar('cPms', ['IE','ITUK','GR','UTI','UMI','BE','IUK','DE'],
      [100,100,97,91,85,63,38,15],
      ['#6b7c93','#6b7c93','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c0453c','#c0453c']);
  bar('cMix', ['UTI','CY','GR','PT','IE','UMI','BE','ITUK','IUK','DE','SE'],
      [11.1,8.5,7.8,6.0,4.5,3.7,3.4,2.7,0.9,0.7,0.1],
      [terr,terr,terr,'#c48a16','#c48a16',ink,'#2b4a78','#2b4a78','#1d9e75','#1d9e75','#1d9e75']);
  bar('cIds', ['MT','PT','HU','PL','UK CV','UK LCV','LU','RO','BE','NL','DK','NO','GR','IL UMI'],
      [89.3,86.9,86.2,84.1,83.8,81.7,80,79.6,78.6,76.3,75.7,75.2,73.9,60.9],
      ['#1d9e75','#1d9e75','#1d9e75','#1d9e75','#2b4a78','#2b4a78','#2b4a78','#2b4a78','#c48a16','#c48a16','#c48a16','#c48a16','#c48a16','#c0453c']);
""" + (
        f"  bar('cPrice', {json.dumps(pn_labels)}, {json.dumps(pn_vals)}, [{','.join(pn_cols)}]);\n"
    ) + (
        "  bar('cRepl', ['No sales to dealer','High vs bill','No bill','Low vs bill'], [500,400,380,315],\n"
        "      [terr,'#c48a16','#2b4a78','#8a6a4a']);\n"
        f"  bar('cTender', {json.dumps([_src_label(l)[:16] for l, _ in src_items] or ['Live'])},\n"
        f"      {json.dumps([float(v) for _, v in src_items] or [float(t_ops)])},\n"
        f"      {json.dumps(['#2b4a78' if i == 0 else '#1d9e75' for i in range(max(len(src_items), 1))])});\n"
    ) + """  document.body.classList.add('js-ok');
})();
"""

    html = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\"/>\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>\n"
        "<title>ISZE aftersales — opportunity and commercialisation</title>\n"
        "<style>\n" + css + "\n</style>\n</head>\n<body>\n"
        '<div class="sheet">\n' + "".join(pages) + "\n</div>\n"
        "<script>\n" + chart_js() + "\n</script>\n"
        "<script>\n" + js_boot + "\n</script>\n"
        "</body>\n</html>\n"
    )
    return html


def main() -> None:
    html = build_html()
    low = html.lower()
    for bad in ("street", "wallet", "sell-out", "sell-through", "book b", "iml v7", "model b", "prism lane", "jerome"):
        if bad in low:
            raise SystemExit(f"forbidden token in HTML: {bad}")
    if "cdn.jsdelivr" in low or "cdnjs.cloudflare" in low:
        raise SystemExit("CDN Chart.js forbidden")
    if "bar-row" not in html:
        raise SystemExit("no bar-row paint fallback")
    if html.count('data-page=') < 16:
        raise SystemExit("expected 16 data-page markers")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes) pages={html.count('paper-page')}")


if __name__ == "__main__":
    main()
