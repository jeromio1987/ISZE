#!/usr/bin/env python3
"""Billed vs sales to dealer — GPS FY2026 — warranty as its own euro line.

Do not stuff FY + warranty into the calendar mix builder.
Sales-to-dealer files are qty-only. Euro on that layer = qty × our billed
unit price (FY weighted average). Warranty is full FY (not pro-rated).
Stock (billed in the same months − sales to dealer) only after parking warranty.
"""
from __future__ import annotations

import html
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
ISZE_ROOT = PRISM.parents[2]
sys.path.insert(0, str(PRISM))
sys.path.insert(0, str(ISZE_ROOT / "01_data" / "91_build"))

from config import (  # noqa: E402
    DASHBOARDS_DIR,
    DASHBOARDS_JSON_DIR,
    DERIVED_DIR,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import normalize_pn  # noqa: E402
from modules.fiscal import gps_fy_dates, sales_fiscal_from_gps_fy  # noqa: E402
from modules.sales_loader import _finish_sales_frame  # noqa: E402

import db_dlr_commercial_common as C  # noqa: E402

GPS_FY = 2026
SALES_FISCAL = sales_fiscal_from_gps_fy(GPS_FY)
NETWORKS = ("IUK", "ITUK", "IRELAND", "UTI", "GREECE")
IUK_DISC_PN = "8983767550"
YEAR_PLUS_MONTHS_TRAP_QTY = 7642.0
DROP_LINE_KIND = frozenset({"freight", "rebate", "finance", "adjustment"})
WARR_CSV = DERIVED_DIR / "distributor_warranty_expense_fiscal.csv"
WARR_ALIAS = DERIVED_DIR / "warranty_by_db_FY_canonical.csv"
OUT_CSV = DERIVED_DIR / "billed_vs_std_warranty_fy2026.csv"
OUT_JSON = DASHBOARDS_JSON_DIR / "billed_vs_std_warranty_fy2026.json"
OUT_HTML = DASHBOARDS_DIR / "sales" / "Dealer_Billed_vs_Sales_to_Dealer_FY2026.html"
OUT_CMD = DASHBOARDS_DIR / "sales" / "OPEN_Billed_vs_Sales_to_Dealer_FY2026.cmd"
CHART_JS = ISZE_ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

DISPLAY = {
    "IUK": "UK pickup",
    "ITUK": "UK truck",
    "IRELAND": "Ireland",
    "UTI": "UTI",
    "GREECE": "Greece",
}
WARR_DB_TO_CODE = {
    "IUK": "IUK",
    "ITUK": "ITUK",
    "UTI": "UTI",
    "Ireland": "IRELAND",
    "IRELAND": "IRELAND",
    "Greece": "GREECE",
    "GREECE": "GREECE",
}
COVERAGE_EXTRA = {
    "ITUK": "No January–March 2026 dealer file.",
    "UTI": "Snapshots start August 2025.",
    "GREECE": "No calendar-2026 dealer file.",
}

_MONTH_PERIOD = re.compile(r"^\d{4}-\d{2}$")
_MONTH_ABBR = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def fy_year_months(gps_fy: int = GPS_FY) -> list[str]:
    start, end = gps_fy_dates(gps_fy)
    idx = pd.period_range(start[:7], end[:7], freq="M")
    return [str(p) for p in idx]


def keep_monthly_std_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep YYYY-MM rows only. Year / YTD totals must not be added on top."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    out = df.copy()
    if "period_grain" in out.columns:
        grain = out["period_grain"].astype(str).str.strip().str.lower()
        out = out[grain.eq("month")]
    period_col = "year_month" if "year_month" in out.columns else "period"
    if period_col in out.columns:
        out = out[out[period_col].astype(str).str.match(_MONTH_PERIOD, na=False)]
    return out


def filter_commercial_billed(sales: pd.DataFrame) -> pd.DataFrame:
    """FY billed euros: drop CR/RE, freight, and non-part text lines. Keep tools."""
    out = sales.copy()
    if "is_credit_note" in out.columns:
        out = out[~out["is_credit_note"]]
    if "line_kind" in out.columns:
        out = out[~out["line_kind"].isin(DROP_LINE_KIND)]
    out["part_number"] = out["part_number"].map(normalize_pn)
    return out.dropna(subset=["part_number"])


def load_warranty_fy(path: Path | None = None, gps_fy: int = GPS_FY) -> dict[str, float]:
    """Canonical distributor warranty expense. Not gps_master warr_*."""
    csv_path = path or (WARR_CSV if WARR_CSV.exists() else WARR_ALIAS)
    df = pd.read_csv(csv_path)
    col = f"warr_FY{gps_fy}"
    if col not in df.columns:
        raise ValueError(f"{csv_path} missing {col}")
    out: dict[str, float] = {}
    for raw, val in zip(df["db"].astype(str).str.strip(), pd.to_numeric(df[col], errors="coerce")):
        code = WARR_DB_TO_CODE.get(raw)
        if code and pd.notna(val):
            out[code] = float(val)
    return out


def pretty_month(ym: str) -> str:
    year, month = ym.split("-")
    return f"{_MONTH_ABBR[int(month) - 1]} {year}"


def month_span_label(months: list[str]) -> str:
    if not months:
        return "No dealer months"
    months = sorted(months)
    n = len(months)
    return f"{pretty_month(months[0])} – {pretty_month(months[-1])} ({n} months)"


def load_std_monthly_fy(db: str, gps_fy: int = GPS_FY) -> pd.DataFrame:
    months = set(fy_year_months(gps_fy))
    start_cal = gps_fy - 1
    frames = [
        keep_monthly_std_rows(C.load_sellout_network_monthly(db, start_cal)),
        keep_monthly_std_rows(C.load_sellout_network_monthly(db, gps_fy)),
    ]
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame(columns=list(C.SELL_NETWORK_MONTHLY_COLS))
    sell = pd.concat(frames, ignore_index=True)
    sell = keep_monthly_std_rows(sell)
    if sell.empty or "year_month" not in sell.columns:
        return pd.DataFrame(columns=list(C.SELL_NETWORK_MONTHLY_COLS))
    sell = sell[sell["year_month"].isin(months)].copy()
    sell["sellout_qty"] = pd.to_numeric(sell["sellout_qty"], errors="coerce").fillna(0)
    return sell


def std_qty_for_pn(db: str, part_number: str, gps_fy: int = GPS_FY) -> float:
    sell = load_std_monthly_fy(db, gps_fy)
    if sell.empty:
        return 0.0
    pn = normalize_pn(part_number)
    hit = sell[sell["part_number"].map(normalize_pn) == pn]
    return float(pd.to_numeric(hit["sellout_qty"], errors="coerce").fillna(0).sum())


def _round_eur(n: float) -> int:
    return int(round(float(n)))


def _fmt_eur(n: object) -> str:
    if n is None or (isinstance(n, float) and (math.isnan(n) or math.isinf(n))):
        return "—"
    v = _round_eur(float(n))
    if v < 0:
        return f"−€{abs(v):,}"
    return f"€{v:,}"


def _e(text: object) -> str:
    return html.escape(str(text) if text is not None else "")


def _clean(obj: object) -> object:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            return obj
    return obj


def load_fy_billed() -> pd.DataFrame:
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    sales = _finish_sales_frame(sales, mapping)
    sales = sales[sales["fiscal_year"] == SALES_FISCAL]
    sales = filter_commercial_billed(sales)
    sales = sales[sales["distributor_code"].isin(NETWORKS)].copy()
    sales["year_month"] = sales["billing_date"].dt.to_period("M").astype(str)
    sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce").fillna(0)
    sales["billed_qty"] = pd.to_numeric(sales["billed_qty"], errors="coerce").fillna(0)
    return sales


def fy_asp(billed: pd.DataFrame) -> pd.DataFrame:
    pos = billed[billed["billed_qty"] > 0]
    g = pos.groupby(["distributor_code", "part_number"], as_index=False).agg(
        billed_eur=("net_sales_value", "sum"),
        billed_qty=("billed_qty", "sum"),
    )
    g["asp_eur"] = g["billed_eur"] / g["billed_qty"]
    return g[["distributor_code", "part_number", "asp_eur"]]


def compute_rows(billed: pd.DataFrame | None = None) -> list[dict]:
    billed = load_fy_billed() if billed is None else billed
    asp = fy_asp(billed)
    warranty = load_warranty_fy()
    rows = []
    for db in NETWORKS:
        bill_db = billed[billed["distributor_code"] == db]
        billed_fy = float(bill_db["net_sales_value"].sum())
        warr = float(warranty.get(db, 0.0))
        sell = load_std_monthly_fy(db)
        months = sorted(sell["year_month"].unique().tolist()) if not sell.empty else []
        billed_overlap = float(
            bill_db[bill_db["year_month"].isin(months)]["net_sales_value"].sum()
        ) if months else 0.0
        if sell.empty:
            std_eur = 0.0
        else:
            net = sell.groupby("part_number", as_index=False)["sellout_qty"].sum()
            a = asp[asp["distributor_code"] == db][["part_number", "asp_eur"]]
            g = net.merge(a, on="part_number", how="left")
            std_eur = float((g["sellout_qty"] * g["asp_eur"].fillna(0)).sum())
        extra = COVERAGE_EXTRA.get(db, "")
        coverage = month_span_label(months)
        if extra:
            coverage = f"{coverage}. {extra}"
        billed_fy_i = _round_eur(billed_fy)
        warr_i = _round_eur(warr)
        overlap_i = _round_eur(billed_overlap)
        std_i = _round_eur(std_eur)
        stock_i = _round_eur(billed_overlap - std_eur)
        commercial_i = _round_eur(billed_fy - warr)
        if db == "IUK":
            reading = (
                f"We billed {_fmt_eur(billed_fy_i)} and sales to dealer is {_fmt_eur(std_i)}. "
                f"Warranty {_fmt_eur(warr_i)} sits in billed. That is not destock. "
                f"After parking warranty, billed vs sales to dealer is {_fmt_eur(stock_i)}."
            )
        elif len(months) < 12:
            reading = (
                f"Warranty {_fmt_eur(warr_i)} is the full FY and is not pro-rated. "
                f"Sales to dealer covers {coverage.split('.')[0]}. "
                f"Compare billed in those months ({_fmt_eur(overlap_i)}) to sales to dealer "
                f"({_fmt_eur(std_i)}), not the full FY billed ({_fmt_eur(billed_fy_i)}). "
                "Park warranty before reading stock."
            )
        else:
            reading = (
                f"Warranty {_fmt_eur(warr_i)} is the full FY. "
                f"Billed in those months {_fmt_eur(overlap_i)} vs sales to dealer {_fmt_eur(std_i)}. "
                "Park warranty before reading stock."
            )
        rows.append(
            {
                "distributor_code": db,
                "label": DISPLAY[db],
                "months": months,
                "month_count": len(months),
                "coverage": coverage,
                "complete_fy": len(months) == 12,
                "billed_fy_eur": billed_fy_i,
                "warranty_fy_eur": warr_i,
                "commercial_eur": commercial_i,
                "billed_overlap_eur": overlap_i,
                "std_eur": std_i,
                "stock_eur": stock_i,
                "reading": reading,
            }
        )
    return rows


def _bar_width(value: float, peak: float) -> float:
    if peak <= 0:
        return 0.0
    return max(2.0, min(100.0, 100.0 * abs(value) / peak))


def render_html(rows: list[dict], generated: str) -> str:
    start, end = gps_fy_dates(GPS_FY)
    iuk = next(r for r in rows if r["distributor_code"] == "IUK")
    peak = max(
        max(r["billed_overlap_eur"], r["warranty_fy_eur"], r["std_eur"]) for r in rows
    )
    kpis = [
        ("UK pickup we billed", iuk["billed_fy_eur"], "Full FY, ex credit notes"),
        ("UK pickup warranty", iuk["warranty_fy_eur"], "Claim euros sitting in billed"),
        ("UK pickup sales to dealer", iuk["std_eur"], "Same 12 months · billed unit price"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="val">{_fmt_eur(v)}</div><div class="lbl">{_e(l)}<br/>{_e(s)}</div></div>'
        for l, v, s in kpis
    )
    banners = []
    for r in rows:
        klass = "ok" if r["complete_fy"] else "amber"
        banners.append(
            f'<div class="banner {klass}"><strong>{_e(r["label"])}</strong> — {_e(r["coverage"])}</div>'
        )
    bar_rows = []
    for r in rows:
        for key, lab, color in (
            ("billed_overlap_eur", "We billed (same months)", "#1d4ed8"),
            ("warranty_fy_eur", "Warranty (full FY)", "#b45309"),
            ("std_eur", "Sales to dealer", "#0f766e"),
        ):
            w = _bar_width(r[key], peak)
            bar_rows.append(
                f'<div class="bar-row"><span class="blab">{_e(r["label"])} · {_e(lab)}</span>'
                f'<span class="btrack"><span class="bfill" style="width:{w:.1f}%;background:{color}"></span></span>'
                f'<span class="bval">{_fmt_eur(r[key])}</span></div>'
            )
    body_rows = []
    for r in rows:
        body_rows.append(
            "<tr>"
            f"<td>{_e(r['label'])}</td>"
            f"<td>{_e(r['coverage'])}</td>"
            f"<td class='n'>{_fmt_eur(r['billed_fy_eur'])}</td>"
            f"<td class='n'>{_fmt_eur(r['warranty_fy_eur'])}</td>"
            f"<td class='n'>{_fmt_eur(r['commercial_eur'])}</td>"
            f"<td class='n'>{_fmt_eur(r['billed_overlap_eur'])}</td>"
            f"<td class='n'>{_fmt_eur(r['std_eur'])}</td>"
            f"<td class='n'>{_fmt_eur(r['stock_eur'])}</td>"
            f"<td>{_e(r['reading'])}</td>"
            "</tr>"
        )
    chart_payload = {
        "labels": [r["label"] for r in rows],
        "billed": [r["billed_overlap_eur"] for r in rows],
        "warranty": [r["warranty_fy_eur"] for r in rows],
        "std": [r["std_eur"] for r in rows],
    }
    callout = (
        f"FY{GPS_FY} = {start} to {end}. Euros first. Three lines: we billed, warranty, "
        "sales to dealer. Warranty is claim euros sitting in billed — not dealer sales. "
        "Park it before you read destock or restock. Sales to dealer exists only for "
        "UK pickup, UK truck, Ireland, UTI and Greece. Align what we billed to those same months. "
        "Do not invent missing months. Warranty stays the full FY. "
        "This is not a business-review pack."
    )
    iuk_note = (
        f"UK pickup we billed {_fmt_eur(iuk['billed_fy_eur'])} and sales to dealer "
        f"{_fmt_eur(iuk['std_eur'])} — the same money, about €6.0M. Warranty "
        f"{_fmt_eur(iuk['warranty_fy_eur'])} is the GPS hole, not destock. "
        f"Commercial versus sales to dealer is {_fmt_eur(iuk['commercial_eur'] - iuk['std_eur'])}, "
        "which is the warranty line. Do not read billed minus sales to dealer as stock "
        "until warranty is parked."
    )
    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Billed vs sales to dealer — FY{GPS_FY}</title>
<script>/*INLINE_CHART_JS*/</script>
<style>
:root {{ --red:#CC0E1E; --bg:#f4f5f7; --card:#fff; --text:#1a1a1a; --muted:#5a5a5a; --border:#e4e4e7; --blue:#1d4ed8; --amber:#b45309; --teal:#0f766e; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--bg); color:var(--text); }}
header {{ background:linear-gradient(135deg,var(--red),#9a0b17); color:#fff; padding:1.4rem 2rem; }}
header h1 {{ margin:0.2rem 0; font-size:1.45rem; }}
.badge {{ display:inline-block; margin-top:0.4rem; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; }}
.wrap {{ max-width:1280px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; overflow-x:auto; }}
section h2 {{ margin:0 0 0.6rem; font-size:1.02rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.25rem; }}
.callout {{ padding:0.7rem 0.95rem; border-left:4px solid var(--red); background:#fff8f8; font-size:0.9rem; margin-bottom:1rem; }}
.callout.insight {{ border-left-color:var(--amber); background:#fffbeb; }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; }}
.kpi {{ flex:1 1 180px; background:var(--bg); border-left:4px solid var(--red); padding:0.65rem 0.85rem; border-radius:6px; }}
.kpi .val {{ font-size:1.2rem; font-weight:700; }}
.kpi .lbl {{ font-size:0.75rem; color:var(--muted); margin-top:0.2rem; }}
.banner {{ padding:0.45rem 0.7rem; border-radius:6px; font-size:0.82rem; margin:0.35rem 0; }}
.banner.ok {{ background:#ecfdf5; border-left:4px solid var(--teal); }}
.banner.amber {{ background:#fffbeb; border-left:4px solid var(--amber); }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
.tbl th {{ background:var(--red); color:#fff; padding:0.4rem 0.5rem; text-align:left; }}
.tbl td {{ padding:0.4rem 0.5rem; border-bottom:1px solid var(--border); vertical-align:top; }}
.tbl td.n {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.muted {{ color:var(--muted); font-size:0.85rem; }}
.bar-row {{ display:grid; grid-template-columns:minmax(200px,280px) 1fr 110px; gap:0.45rem; align-items:center; margin:0.28rem 0; font-size:0.78rem; }}
.btrack {{ background:#ececec; border-radius:4px; height:12px; overflow:hidden; }}
.bfill {{ display:block; height:100%; }}
.bval {{ text-align:right; font-variant-numeric:tabular-nums; }}
.legend span {{ display:inline-block; width:10px; height:10px; margin-right:0.3rem; vertical-align:middle; }}
@media(max-width:800px){{ .bar-row {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.8rem;letter-spacing:0.08em;opacity:0.9">ISZE · billed vs sales to dealer · FY{GPS_FY}</div>
  <h1>We billed, warranty, and sales to dealer</h1>
  <span class="badge">FY{GPS_FY} · {start} – {end} · generated {generated}</span>
</header>
<div class="wrap">
  <div class="callout">{_e(callout)}</div>
  <div class="callout insight"><strong>UK pickup.</strong> {_e(iuk_note)}</div>
  <section>
    <h2>UK pickup — the three euro lines</h2>
    <div class="kpi-row">{kpi_html}</div>
  </section>
  <section>
    <h2>Dealer-file months</h2>
    <p class="muted">Banner the months we have. Do not fill a missing month. Warranty is the full FY on every row.</p>
    {"".join(banners)}
  </section>
  <section>
    <h2>Euros by distributor</h2>
    <p class="legend muted">
      <span style="background:#1d4ed8"></span>We billed (same months)
      <span style="background:#b45309;margin-left:0.8rem"></span>Warranty (full FY)
      <span style="background:#0f766e;margin-left:0.8rem"></span>Sales to dealer
    </p>
    {"".join(bar_rows)}
    <canvas id="chartMoney" height="280" style="margin-top:1rem"></canvas>
  </section>
  <section>
    <h2>The table</h2>
    <p class="muted">Sales to dealer euro uses our billed unit price on their dealer file. It is not their invoice. Last money column is destock / restock only after warranty is parked. Incomplete months: compare billed in those months, not the full FY billed, to sales to dealer.</p>
    <table class="tbl">
      <thead>
        <tr>
          <th>Distributor</th>
          <th>Sales-to-dealer months</th>
          <th>We billed (FY)</th>
          <th>Warranty (FY)</th>
          <th>Commercial (billed − warranty)</th>
          <th>We billed in those months</th>
          <th>Sales to dealer</th>
          <th>After parking warranty: billed in months − sales to dealer</th>
          <th>How to read it</th>
        </tr>
      </thead>
      <tbody>
        {"".join(body_rows)}
      </tbody>
    </table>
  </section>
</div>
<footer class="muted" style="text-align:center;padding:1rem;font-size:0.75rem">
  FY billed vs sales to dealer with warranty as its own line. Calendar 2025 mix page is a leftover.
</footer>
<script type="application/json" id="chart-data">{json.dumps(chart_payload, allow_nan=False)}</script>
<script>
function initCharts() {{
  if (typeof Chart === 'undefined') return;
  const D = JSON.parse(document.getElementById('chart-data').textContent);
  const el = document.getElementById('chartMoney');
  if (!el) return;
  new Chart(el, {{
    type: 'bar',
    data: {{
      labels: D.labels,
      datasets: [
        {{ label: 'We billed (same months)', data: D.billed, backgroundColor: '#1d4ed8' }},
        {{ label: 'Warranty (full FY)', data: D.warranty, backgroundColor: '#b45309' }},
        {{ label: 'Sales to dealer', data: D.std, backgroundColor: '#0f766e' }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'bottom' }} }},
      scales: {{ y: {{ beginAtZero: true, ticks: {{ callback: function(v) {{ return '€' + Number(v).toLocaleString(); }} }} }} }}
    }}
  }});
}}
document.addEventListener('DOMContentLoaded', initCharts);
window.addEventListener('load', initCharts);
</script>
</body>
</html>"""
    chart_js = CHART_JS.read_text(encoding="utf-8")
    return html_out.replace("/*INLINE_CHART_JS*/", chart_js)


def write_outputs(rows: list[dict]) -> None:
    generated = date.today().isoformat()
    start, end = gps_fy_dates(GPS_FY)
    payload = {
        "gps_fy": GPS_FY,
        "sales_fiscal_year": SALES_FISCAL,
        "window_start": start,
        "window_end": end,
        "generated": generated,
        "warranty_source": str(WARR_CSV.name),
        "rows": rows,
        "notes": {
            "std": "qty × our billed unit price (FY weighted average). Not their invoice.",
            "warranty": "Full FY. Do not pro-rate to dealer-file months.",
            "stock": "billed in the same months minus sales to dealer, after parking warranty.",
        },
    }
    payload = _clean(payload)
    DASHBOARDS_JSON_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    html_out = render_html(rows, generated)
    visible = re.sub(r"<script[\s\S]*?</script>", " ", html_out, flags=re.I)
    if "NaN" in visible:
        raise RuntimeError("NaN in HTML body")
    OUT_HTML.write_text(html_out, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\nstart "" "%~dp0Dealer_Billed_vs_Sales_to_Dealer_FY2026.html"\n',
        encoding="utf-8",
    )


def main() -> int:
    if not SALES_FACT_PARQUET.exists():
        print(f"missing {SALES_FACT_PARQUET}")
        return 1
    if not CHART_JS.exists():
        print(f"missing {CHART_JS}")
        return 1
    rows = compute_rows()
    write_outputs(rows)
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_CMD}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")
    for r in rows:
        print(
            f"{r['distributor_code']:8} billed {r['billed_fy_eur']:,}  "
            f"warr {r['warranty_fy_eur']:,}  std {r['std_eur']:,}  "
            f"stock {r['stock_eur']:,}  {r['coverage']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
