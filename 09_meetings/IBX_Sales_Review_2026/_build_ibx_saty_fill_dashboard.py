"""Build IBX-only Mode A dashboard: SaTy mix + Individual Fill Rate.

Self-contained HTML (embedded JSON + Chart.js CDN with local fallback).
Outlook draft helper: --draft-mail (Save only — never Send).

    python _build_ibx_saty_fill_dashboard.py
    python _build_ibx_saty_fill_dashboard.py --draft-mail
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MEET = ROOT / "09_meetings" / "IBX_Sales_Review_2026"
OUT_HTML = MEET / "IBX_SaTy_Fill_Rate_Dashboard.html"
OUT_META = MEET / "IBX_SaTy_Fill_Rate_Dashboard.meta.json"
DRAFT_RESULT = MEET / "outlook_draft_ibx_saty_fill_result.json"
CHART_JS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

SALES_FACT = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
Q1_EXPORT = ROOT / "01_data" / "00_derived" / "q1fy2027_export_with_saty.csv"
KPI_MASTER = ROOT / "01_data" / "11_planning" / "KPI Master File june 2026.xlsx"

# IBX = Benelux — prefer Belgium v1.4 (corrected network averages); leave v1.3 intact
IDS_BE_ZIP = ROOT / "09_meetings" / "IDS_2026_Belgium_v1.4" / "IDS_2026_Belgium_v1.4.zip"
IDS_BE_HTML = (
    ROOT / "09_meetings" / "IDS_2026_Belgium_v1.4" / "Belgium"
    / "IDS_2026_dealer_compare_Belgium.html"
)

TO = "jerome.van.der.pluym@isuzu-e.com"
SUBJECT = "IBX — SaTy evolution + Individual Fill Rate dashboard (+ IDS Belgium pack)"

# Digitized from Jerome's attached Individual Fill Rate chart (2026-08-12).
# KPI Master June 2026 First Fill Rate for IBX is N/D from Apr 2025 onward.
FILL_SERIES = [
    {"ym": "2025-07", "label": "Jul 2025", "pct": 86},
    {"ym": "2025-08", "label": "Aug 2025", "pct": 91},
    {"ym": "2025-09", "label": "Sep 2025", "pct": 89},
    {"ym": "2025-10", "label": "Oct 2025", "pct": 89},
    {"ym": "2025-11", "label": "Nov 2025", "pct": 91},
    {"ym": "2025-12", "label": "Dec 2025", "pct": 85},
    {"ym": "2026-01", "label": "Jan 2026", "pct": 94},
    {"ym": "2026-02", "label": "Feb 2026", "pct": 91},
    {"ym": "2026-03", "label": "Mar 2026", "pct": 87},
    {"ym": "2026-04", "label": "Apr 2026", "pct": 86},
    {"ym": "2026-05", "label": "May 2026", "pct": 88},
    {"ym": "2026-06", "label": "Jun 2026", "pct": 91},
    {"ym": "2026-07", "label": "Jul 2026", "pct": 93},
]

CODED = {"SOR", "VOR", "RUSH", "SVOR", "PRD"}


def _norm_sold_to(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def saty_monthly_from_sales_fact() -> pd.DataFrame:
    df = pd.read_parquet(SALES_FACT)
    ibx = df[_norm_sold_to(df["sold_to"]) == "90"].copy()
    ibx["billing_date"] = pd.to_datetime(ibx["billing_date"], errors="coerce")
    ibx = ibx.dropna(subset=["billing_date"])
    ibx["ym"] = ibx["billing_date"].dt.to_period("M").astype(str)
    ibx["saty"] = ibx["saty"].fillna("").astype(str).str.strip().str.upper()
    keep = ibx[ibx["saty"].isin(CODED)].copy()
    g = keep.groupby(["ym", "saty"], as_index=False)["net_sales_value"].sum()
    tot = g.groupby("ym")["net_sales_value"].transform("sum")
    g["share_pct"] = (100.0 * g["net_sales_value"] / tot).round(1)
    g["eur"] = g["net_sales_value"].round(2)
    g["source"] = "sales_fact.parquet"
    return g


def saty_monthly_from_q1_export() -> pd.DataFrame:
    exp = pd.read_csv(
        Q1_EXPORT,
        low_memory=False,
        usecols=["Billing Date", "Sold_to", "EUR_Amount", "SaTy"],
    )
    ibx = exp[_norm_sold_to(exp["Sold_to"]) == "90"].copy()
    ibx["Billing Date"] = pd.to_datetime(ibx["Billing Date"], errors="coerce")
    ibx = ibx.dropna(subset=["Billing Date"])
    ibx["ym"] = ibx["Billing Date"].dt.to_period("M").astype(str)
    ibx["saty"] = ibx["SaTy"].fillna("").astype(str).str.strip().str.upper()
    keep = ibx[ibx["saty"].isin(CODED)].copy()
    g = keep.groupby(["ym", "saty"], as_index=False)["EUR_Amount"].sum()
    tot = g.groupby("ym")["EUR_Amount"].transform("sum")
    g["share_pct"] = (100.0 * g["EUR_Amount"] / tot).round(1)
    g["eur"] = g["EUR_Amount"].round(2)
    g["source"] = "q1fy2027_export_with_saty.csv"
    return g[["ym", "saty", "share_pct", "eur", "source"]]


def build_saty_series() -> list[dict]:
    """Jul 2025–Jun 2026: sales_fact through Mar; Q1 export Apr–Jun."""
    sf = saty_monthly_from_sales_fact()
    q1 = saty_monthly_from_q1_export()
    months = [f"2025-{m:02d}" for m in range(7, 13)] + [
        f"2026-{m:02d}" for m in range(1, 7)
    ]
    labels = {
        "2025-07": "Jul 2025",
        "2025-08": "Aug 2025",
        "2025-09": "Sep 2025",
        "2025-10": "Oct 2025",
        "2025-11": "Nov 2025",
        "2025-12": "Dec 2025",
        "2026-01": "Jan 2026",
        "2026-02": "Feb 2026",
        "2026-03": "Mar 2026",
        "2026-04": "Apr 2026",
        "2026-05": "May 2026",
        "2026-06": "Jun 2026",
    }
    out: list[dict] = []
    for ym in months:
        src = q1 if ym >= "2026-04" else sf
        sub = src[src["ym"] == ym]
        sor = float(sub.loc[sub["saty"] == "SOR", "share_pct"].sum()) if len(sub) else None
        vor = float(sub.loc[sub["saty"] == "VOR", "share_pct"].sum()) if len(sub) else None
        rush = float(sub.loc[sub["saty"] == "RUSH", "share_pct"].sum()) if len(sub) else 0.0
        eur = float(sub["eur"].sum()) if len(sub) else None
        source = str(sub["source"].iloc[0]) if len(sub) else None
        out.append(
            {
                "ym": ym,
                "label": labels[ym],
                "sor_pct": sor,
                "vor_pct": vor,
                "rush_pct": rush,
                "coded_eur": eur,
                "source": source,
            }
        )
    return out


def kpi_first_fill_note() -> dict:
    """Confirm KPI Master gap for IBX First Fill (do not invent fills from MOS)."""
    note = {
        "file": str(KPI_MASTER),
        "metric": "First Fill Rate · IBX (BENELUX)",
        "status": "N/D from Apr 2025 onward in KPI Master File june 2026.xlsx",
        "fill_cur_target_file": str(
            ROOT / "01_data" / "11_planning" / "ISZE_DB_KPI_Targets_FY2627_v1.xlsx"
        ),
        "fill_cur_snapshot": 0.85,
        "fill_target": 0.90,
        "dashboard_fill_source": (
            "Digitized labeled points from Jerome Individual Fill Rate chart "
            "(Jul 2025–Jul 2026), attached 2026-08-12"
        ),
    }
    return note


def build_payload() -> dict:
    saty = build_saty_series()
    return {
        "db": "IBX",
        "display": "IBX (Benelux)",
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "A",
        "saty": {
            "title": "Order type mix over time (SaTy)",
            "subtitle": (
                "Share of billed € by order type — stock (SOR) vs urgent (VOR). "
                "Coded lines only."
            ),
            "months": saty,
            "sources": [
                {
                    "path": str(SALES_FACT),
                    "window": "Jul 2025 – Mar 2026",
                    "filter": "sold_to 90 · coded SaTy SOR/VOR/RUSH/SVOR/PRD",
                },
                {
                    "path": str(Q1_EXPORT),
                    "window": "Apr 2026 – Jun 2026",
                    "filter": "Sold_to 90 · coded SaTy",
                },
            ],
            "note": (
                "Jul 2026 SaTy not yet in the reconciled Apr+ billing export. "
                "Customer satisfaction (KPI Master) is N/A for IBX — SaTy here is order type."
            ),
        },
        "fill_rate": {
            "title": "Individual Fill Rate",
            "subtitle": "IBX · Jul 2025 – Jul 2026",
            "months": FILL_SERIES,
            "kpi_master_gap": kpi_first_fill_note(),
            "style_note": "Chart style aligned to Jerome Individual Fill Rate visual.",
        },
        "ids": {
            "ibx_country": "Belgium (Benelux); Netherlands is a separate IDS bucket",
            "v14_midi": (
                "MIDI Country Packs v1.4 = FR/IT/ES/CH; Belgium has its own "
                "IDS_2026_Belgium_v1.4 pack (corrected network averages)"
            ),
            "attachment": str(IDS_BE_ZIP if IDS_BE_ZIP.is_file() else IDS_BE_HTML),
            "version": "v1.4 Belgium pack (corrected network averages; IBX-relevant)",
        },
    }


def render_html(payload: dict) -> str:
    data_json = json.dumps(payload, ensure_ascii=False)
    chart_tag = ""
    if CHART_JS.is_file():
        # Prefer CDN; local copy noted in footer for offline attempts
        chart_tag = f"<!-- local Chart.js also at {CHART_JS.as_posix()} -->"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>IBX — SaTy evolution &amp; Individual Fill Rate</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
{chart_tag}
<style>
:root {{
  --navy:#0f2744; --red:#c41230; --ink:#1a1a1a; --muted:#5c6570;
  --line:#d9d3c9; --bg:#f7f5f2; --card:#fff; --ok:#1f6b3a;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI", Calibri, sans-serif; background:var(--bg); color:var(--ink); }}
.topbar {{ height:6px; background:var(--red); }}
header {{ background:var(--navy); color:#fff; padding:22px 28px 18px; }}
header h1 {{ margin:0 0 6px; font-size:24px; font-weight:650; }}
header p {{ margin:0; opacity:.88; font-size:13px; max-width:52rem; }}
.badge {{ display:inline-block; margin-top:12px; background:#5c6570; color:#fff;
  padding:4px 12px; font-size:12px; font-weight:700; letter-spacing:.04em; }}
main {{ max-width:1100px; margin:0 auto; padding:22px 18px 40px; }}
.card {{ background:var(--card); border:1px solid var(--line); padding:18px 20px; margin-bottom:16px; }}
.card h2 {{ margin:0 0 4px; font-size:16px; color:var(--navy); }}
.card .sub {{ margin:0 0 14px; font-size:12px; color:var(--muted); }}
.chart-wrap {{ position:relative; height:340px; }}
.chart-wrap.fill {{ height:360px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px; }}
.kpi {{ background:var(--card); border:1px solid var(--line); padding:12px 14px; }}
.kpi .l {{ font-size:10px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
.kpi .v {{ font-size:20px; font-weight:700; color:var(--navy); margin-top:4px; }}
.note {{ font-size:11px; color:var(--muted); line-height:1.45; margin:10px 0 0; }}
footer {{ font-size:11px; color:var(--muted); margin-top:8px; }}
.footbar {{ height:6px; background:var(--red); margin-top:24px; }}
@media (max-width:720px) {{ .kpis {{ grid-template-columns:1fr 1fr; }} .chart-wrap,.chart-wrap.fill {{ height:280px; }} }}
</style>
</head>
<body>
<div class="topbar"></div>
<header>
  <h1>IBX — SaTy evolution &amp; fill rate</h1>
  <p>Benelux distributor view. Order-type mix (SaTy) from ISZE billing, plus Individual Fill Rate
     for Jul 2025–Jul 2026. Open this file directly — charts are embedded.</p>
  <span class="badge">IBX</span>
</header>
<main>
  <div class="kpis" id="kpis"></div>

  <section class="card">
    <h2>Order type mix over time (SaTy)</h2>
    <p class="sub">Stock orders (SOR) vs urgent orders (VOR) — share of billed €, coded lines only</p>
    <div class="chart-wrap"><canvas id="satyChart"></canvas></div>
    <p class="note" id="satyNote"></p>
  </section>

  <section class="card">
    <h2>INDIVIDUAL FILL RATE</h2>
    <p class="sub">IBX · Jul 2025 – Jul 2026</p>
    <div class="chart-wrap fill"><canvas id="fillChart"></canvas></div>
    <p class="note" id="fillNote"></p>
  </section>

  <footer id="footer"></footer>
</main>
<div class="footbar"></div>

<script id="payload" type="application/json">{data_json}</script>
<script>
(function(){{
  const D = JSON.parse(document.getElementById('payload').textContent);
  const saty = D.saty.months;
  const fill = D.fill_rate.months;

  const lastSaty = [...saty].reverse().find(r => r.sor_pct != null);
  const lastFill = fill[fill.length - 1];
  const avgFill = (fill.reduce((a,b)=>a+b.pct,0) / fill.length).toFixed(1);
  const kpis = document.getElementById('kpis');
  kpis.innerHTML = [
    ['Latest SaTy month', lastSaty ? lastSaty.label : '—'],
    ['SOR share (latest)', lastSaty ? lastSaty.sor_pct.toFixed(1) + '%' : '—'],
    ['VOR share (latest)', lastSaty ? lastSaty.vor_pct.toFixed(1) + '%' : '—'],
    ['Fill rate (Jul 2026)', lastFill.pct + '% · avg ' + avgFill + '%'],
  ].map(([l,v]) => `<div class="kpi"><div class="l">${{l}}</div><div class="v">${{v}}</div></div>`).join('');

  document.getElementById('satyNote').textContent = D.saty.note;
  document.getElementById('fillNote').textContent =
    D.fill_rate.kpi_master_gap.dashboard_fill_source +
    '. KPI Master First Fill for IBX is N/D from Apr 2025 (snapshot fill cur 85% / target 90%).';
  document.getElementById('footer').textContent =
    'Built ' + D.built_utc + ' · IDS attach: ' + D.ids.version +
    ' · ' + D.ids.v14_midi;

  const labels = saty.map(r => r.label);
  new Chart(document.getElementById('satyChart'), {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{
          label: 'Stock (SOR) %',
          data: saty.map(r => r.sor_pct),
          borderColor: '#0f2744',
          backgroundColor: 'rgba(15,39,68,.08)',
          tension: 0.2,
          pointRadius: 3,
          borderWidth: 2,
        }},
        {{
          label: 'Urgent (VOR) %',
          data: saty.map(r => r.vor_pct),
          borderColor: '#c41230',
          backgroundColor: 'rgba(196,18,48,.06)',
          tension: 0.2,
          pointRadius: 3,
          borderWidth: 2,
        }},
      ],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ position: 'top' }},
        tooltip: {{ callbacks: {{ label: c => `${{c.dataset.label}}: ${{c.parsed.y}}%` }} }},
      }},
      scales: {{
        y: {{
          min: 0, max: 100,
          ticks: {{ callback: v => v + '%' }},
          grid: {{ color: '#eee' }},
          title: {{ display: true, text: 'Share of billed €' }},
        }},
        x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }} }},
      }},
    }},
  }});

  const fillLabels = fill.map(r => r.label);
  const fillVals = fill.map(r => r.pct);
  // simple linear trend for style match
  const n = fillVals.length;
  const xMean = (n - 1) / 2;
  const yMean = fillVals.reduce((a,b)=>a+b,0) / n;
  let num = 0, den = 0;
  for (let i = 0; i < n; i++) {{ num += (i - xMean) * (fillVals[i] - yMean); den += (i - xMean) ** 2; }}
  const slope = den ? num / den : 0;
  const intercept = yMean - slope * xMean;
  const trend = fillVals.map((_, i) => +(intercept + slope * i).toFixed(2));

  new Chart(document.getElementById('fillChart'), {{
    type: 'line',
    data: {{
      labels: fillLabels,
      datasets: [
        {{
          label: 'IBX fill rate',
          data: fillVals,
          borderColor: '#111',
          borderDash: [5, 4],
          pointStyle: 'rect',
          pointRadius: 4,
          pointBackgroundColor: '#111',
          tension: 0.15,
          borderWidth: 1.5,
          datalabels: undefined,
        }},
        {{
          label: 'Trend',
          data: trend,
          borderColor: '#666',
          borderDash: [2, 3],
          pointRadius: 0,
          borderWidth: 1,
          tension: 0,
        }},
      ],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: c => `${{c.parsed.y}}%` }} }},
      }},
      scales: {{
        y: {{
          min: 84, max: 100,
          ticks: {{ stepSize: 2, callback: v => v + '%' }},
          grid: {{ color: '#e8e8e8' }},
        }},
        x: {{
          grid: {{ display: false }},
          ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 7 }},
        }},
      }},
    }},
    plugins: [{{
      id: 'fillLabels',
      afterDatasetsDraw(chart) {{
        const meta = chart.getDatasetMeta(0);
        const ctx = chart.ctx;
        ctx.save();
        ctx.font = '600 11px Segoe UI, sans-serif';
        ctx.fillStyle = '#c41230';
        ctx.textAlign = 'center';
        meta.data.forEach((pt, i) => {{
          const v = fillVals[i];
          ctx.fillText(v + '%', pt.x, pt.y - 10);
        }});
        ctx.restore();
      }},
    }}],
  }});
}})();
</script>
</body>
</html>
"""


def write_outputs(payload: dict) -> Path:
    OUT_HTML.write_text(render_html(payload), encoding="utf-8")
    OUT_META.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Keep a copy of Chart.js next to HTML for optional offline use (CDN primary)
    if CHART_JS.is_file():
        dest = MEET / "_ui"
        dest.mkdir(exist_ok=True)
        shutil.copy2(CHART_JS, dest / "chart.umd.min.js")
    return OUT_HTML


def draft_outlook(html: Path) -> dict:
    import win32com.client  # type: ignore

    attach_ids = IDS_BE_ZIP if IDS_BE_ZIP.is_file() else IDS_BE_HTML
    body = (
        "Jerome,\n\n"
        "IBX-only dashboard (self-contained HTML — double-click to open):\n"
        f"  {html}\n\n"
        "Charts\n"
        "1. SaTy evolution — stock (SOR) vs urgent (VOR) share of billed € "
        "(Jul 2025–Jun 2026). Sources: sales_fact + q1fy2027_export_with_saty, sold_to 90.\n"
        "2. Individual Fill Rate — Jul 2025–Jul 2026 points from your attached chart "
        "(KPI Master June 2026 has First Fill N/D for IBX from Apr 2025).\n\n"
        "IDS\n"
        "IBX = Benelux (Belgium). Attached: Belgium dealer compare pack v1.4 "
        "(corrected network averages — same wave as MIDI Baumann averages fix).\n"
        f"File: {attach_ids.name}\n"
        "Dashboard mirror: 02_dashboards/ids/IDS_2026_dealer_compare_Belgium.html\n"
        "Also on disk: Netherlands pack if you need the NL bucket separately.\n\n"
        "Draft only — not sent.\n"
    )

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = TO
    mail.Subject = SUBJECT
    mail.Body = body
    mail.Attachments.Add(str(html.resolve()))
    mail.Attachments.Add(str(attach_ids.resolve()))
    if IDS_BE_HTML.is_file() and attach_ids.suffix.lower() == ".zip":
        # zip already contains HTML; skip duplicate
        pass
    mail.Save()
    try:
        mail.Display(False)
    except Exception:  # noqa: BLE001
        pass

    result = {
        "to": TO,
        "subject": SUBJECT,
        "attachments": [str(html.resolve()), str(attach_ids.resolve())],
        "dashboard": str(html.resolve()),
        "ids_attachment": str(attach_ids.resolve()),
        "ids_note": "Belgium v1.4 — corrected network averages (IBX Benelux)",
        "draft_only": True,
        "sent": False,
        "saved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    DRAFT_RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-mail", action="store_true", help="Outlook Save draft only")
    args = ap.parse_args()

    payload = build_payload()
    html = write_outputs(payload)
    print(f"Wrote {html}")
    print(f"Meta  {OUT_META}")

    if args.draft_mail:
        r = draft_outlook(html)
        print(f"DRAFT saved (not sent): {r['subject']}")
        print(f"  To: {r['to']}")
        for a in r["attachments"]:
            print(f"  Attach: {a}")
        print(f"  Meta: {DRAFT_RESULT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
