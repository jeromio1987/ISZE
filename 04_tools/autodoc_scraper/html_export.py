"""
ISZE - IAM Threat Matrix HTML export
=====================================
Builds two standalone HTML files from a scored dataframe:
  - iam_matrix_plex.html       (IBM Plex Sans, navy blue, white cards - live cockpit style)
  - iam_matrix_broadsheet.html (Fraunces serif, sepia, burgundy - Aged Broadsheet)

Both are self-contained: data + Plotly + CSS inline. Drop into browser, no server needed.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

QUADRANT_ORDER = ["Dangerous", "Nuisance", "Watch", "Ignore"]


def _prepare_records(scored: pd.DataFrame) -> tuple[list[dict], dict]:
    """Build records for embedding + quadrant counts."""
    cols = [
        "PN", "Description", "primary_threat_brand", "brand_tier",
        "PR00_EUR", "dealer_workshop_price", "best_price_eur",
        "threat_score", "quality_score", "quadrant",
        "Rev_CY2025_EUR",
    ]
    if "best_url" in scored.columns:
        cols.append("best_url")
    df = scored[[c for c in cols if c in scored.columns]].copy()
    for nc in ["PR00_EUR", "dealer_workshop_price", "best_price_eur",
               "threat_score", "quality_score", "Rev_CY2025_EUR"]:
        if nc in df.columns:
            df[nc] = pd.to_numeric(df[nc], errors="coerce")
    df = df.fillna("")
    records = df.to_dict("records")
    counts = scored["quadrant"].value_counts().to_dict() if "quadrant" in scored.columns else {}
    return records, counts


def _plotly_div(scored: pd.DataFrame) -> str:
    """Return a self-contained Plotly chart div (with plotly.js included)."""
    import plotly.express as px
    plot = scored.dropna(subset=["threat_score", "quality_score"]).copy()
    plot["Rev_CY2025_EUR_size"] = plot["Rev_CY2025_EUR"].clip(lower=1000)
    if plot.empty:
        return "<p>No scored PNs.</p>"
    fig = px.scatter(
        plot,
        x="quality_score",
        y="threat_score",
        size="Rev_CY2025_EUR_size",
        color="quadrant",
        color_discrete_map={
            "Dangerous": "#b52a1c",
            "Nuisance":  "#c05010",
            "Watch":     "#0c2461",
            "Ignore":    "#9aa0a8",
        },
        hover_data={
            "PN": True, "Description": True, "primary_threat_brand": True,
            "Rev_CY2025_EUR": ":.0f", "Rev_CY2025_EUR_size": False,
        },
        labels={
            "quality_score": "Quality (IAM brand tier)",
            "threat_score":  "Threat",
        },
    )
    fig.add_hline(y=50, line_dash="dash", line_color="#888", line_width=1)
    fig.add_vline(x=50, line_dash="dash", line_color="#888", line_width=1)
    fig.add_annotation(x=25, y=95, text="<b>NUISANCE</b>", showarrow=False,
                       font=dict(color="#c05010", size=11), opacity=0.6)
    fig.add_annotation(x=80, y=95, text="<b>DANGEROUS</b>", showarrow=False,
                       font=dict(color="#b52a1c", size=11), opacity=0.7)
    fig.add_annotation(x=80, y=10, text="<b>WATCH</b>", showarrow=False,
                       font=dict(color="#0c2461", size=11), opacity=0.6)
    fig.add_annotation(x=25, y=10, text="<b>IGNORE</b>", showarrow=False,
                       font=dict(color="#9aa0a8", size=11), opacity=0.5)
    fig.update_layout(
        height=540,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 105], gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(range=[0, 105], gridcolor="rgba(0,0,0,0.06)"),
        margin=dict(l=40, r=20, t=10, b=40),
        legend=dict(orientation="h", y=-0.15),
    )
    # NOTE (2026-07-09 fix): was include_plotlyjs="cdn". Plotly is now loaded once,
    # inline, in the page <head> (see build_executive_dashboard.py) — same pattern
    # category_bar_div already assumed. Do not re-embed the library per-chart.
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _eur(v) -> str:
    try:
        f = float(v)
        return f"€{f:,.0f}" if abs(f) >= 100 else f"€{f:.2f}"
    except (ValueError, TypeError):
        return "—"


def _quadrant_table_rows(scored: pd.DataFrame, quadrant: str, n: int = 12) -> str:
    sub = scored[scored["quadrant"] == quadrant].sort_values(
        ["threat_score", "Rev_CY2025_EUR"], ascending=[False, False]
    ).head(n)
    if sub.empty:
        return "<tr><td colspan='8' class='empty'>No PNs in this quadrant.</td></tr>"
    rows = []
    for _, r in sub.iterrows():
        url = r.get("best_url") or ""
        link = f'<a href="{url}" target="_blank" rel="noopener">↗</a>' if url else ""
        rows.append(
            "<tr>"
            f"<td class='pn'>{r['PN']}</td>"
            f"<td>{r['Description']}</td>"
            f"<td class='brand'>{r.get('primary_threat_brand', '')}</td>"
            f"<td class='num'>{_eur(r.get('PR00_EUR'))}</td>"
            f"<td class='num'>{_eur(r.get('dealer_workshop_price'))}</td>"
            f"<td class='num'>{_eur(r.get('best_price_eur'))}</td>"
            f"<td class='score t'>{float(r.get('threat_score') or 0):.0f}</td>"
            f"<td class='score q'>{float(r.get('quality_score') or 0):.0f}</td>"
            f"<td class='num'>{_eur(r.get('Rev_CY2025_EUR'))}</td>"
            f"<td class='lnk'>{link}</td>"
            "</tr>"
        )
    return "\n".join(rows)


# ────────────────────────────────────────────────────────────────────
# THEME 1: IBM Plex / blue (live cockpit style)
# ────────────────────────────────────────────────────────────────────

PLEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IAM Threat Matrix · ISZE</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #f2f4f8; --bg2: #ffffff; --bg3: #f4f7fb;
  --border: #dde3ec; --border2: #c8d0dc;
  --text: #4a5568; --text2: #6a7a8a; --text3: #8a96a8;
  --ink: #0f1923; --blue: #0c2461;
  --red: #b52a1c; --orange: #c05010; --grey: #9aa0a8;
  --red-dim: #fbeae8; --orange-dim: #fef3e2; --blue-dim: #eef2fb; --grey-dim: #f0f1f4;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:'IBM Plex Sans',sans-serif;
       padding:32px 24px 80px; max-width:1280px; margin:0 auto; }
.header { display:flex; align-items:flex-end; justify-content:space-between;
          margin-bottom:32px; padding-bottom:20px; border-bottom:2px solid var(--blue); }
.header h1 { font-size:1.9rem; font-weight:700; color:var(--ink); letter-spacing:-0.02em; }
.header h1 span { color:var(--blue); }
.meta { font-size:0.72rem; color:var(--text3); letter-spacing:0.12em;
        text-transform:uppercase; margin-top:4px; }
.subtitle { font-size:0.95rem; color:var(--text2); margin-top:6px; max-width:780px; line-height:1.5; }

.kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:28px; }
.kpi { background:var(--bg2); border:1px solid var(--border); border-radius:6px;
       padding:16px 18px; position:relative; overflow:hidden; }
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--accent); }
.kpi.dangerous { --accent:var(--red); }
.kpi.nuisance  { --accent:var(--orange); }
.kpi.watch     { --accent:var(--blue); }
.kpi.ignore    { --accent:var(--grey); }
.kpi-label { font-size:0.68rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--text3); }
.kpi-value { font-family:'IBM Plex Mono',monospace; font-size:2rem; font-weight:600;
             color:var(--ink); margin-top:6px; }
.kpi-sub { font-size:0.72rem; color:var(--text2); margin-top:2px; }

.chart-card { background:var(--bg2); border:1px solid var(--border); border-radius:6px;
              padding:18px; margin-bottom:28px; }
.chart-card h2 { font-size:0.78rem; letter-spacing:0.1em; text-transform:uppercase;
                 color:var(--text2); margin-bottom:12px; font-weight:600; }

.quadrants { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
@media (max-width:980px) { .quadrants { grid-template-columns:1fr; } }
.quad-card { background:var(--bg2); border:1px solid var(--border); border-radius:6px;
             padding:16px 18px; }
.quad-card.dangerous { border-left:4px solid var(--red); }
.quad-card.nuisance  { border-left:4px solid var(--orange); }
.quad-card.watch     { border-left:4px solid var(--blue); }
.quad-card.ignore    { border-left:4px solid var(--grey); }
.quad-card h3 { font-size:1.05rem; font-weight:700; color:var(--ink); margin-bottom:4px; }
.quad-card .qdesc { font-size:0.78rem; color:var(--text2); margin-bottom:14px; line-height:1.45; }

table { width:100%; border-collapse:collapse; font-size:0.78rem; }
th { text-align:left; font-weight:600; color:var(--text3); font-size:0.66rem;
     letter-spacing:0.08em; text-transform:uppercase;
     padding:8px 6px; border-bottom:1px solid var(--border); }
td { padding:7px 6px; border-bottom:1px solid var(--border); color:var(--text); }
td.pn { font-family:'IBM Plex Mono',monospace; font-size:0.74rem; color:var(--ink); }
td.brand { font-weight:600; color:var(--blue); }
td.num { font-family:'IBM Plex Mono',monospace; text-align:right; font-size:0.74rem; }
td.score { text-align:center; font-weight:600; font-family:'IBM Plex Mono',monospace; }
td.score.t { color:var(--red); }
td.score.q { color:var(--blue); }
td.lnk a { color:var(--blue); text-decoration:none; }
td.lnk a:hover { text-decoration:underline; }
td.empty { text-align:center; color:var(--text3); padding:24px; font-style:italic; }

.footer { margin-top:36px; padding-top:18px; border-top:1px solid var(--border);
          font-size:0.7rem; color:var(--text3); letter-spacing:0.05em; }
</style></head>
<body>
<div class="header">
  <div>
    <h1>IAM <span>Threat × Quality</span> Matrix</h1>
    <div class="meta">ISZE Aftermarket Intelligence · {timestamp}</div>
    <div class="subtitle">{subtitle}</div>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi dangerous"><div class="kpi-label">Dangerous</div><div class="kpi-value">{n_dangerous}</div><div class="kpi-sub">High threat + high quality</div></div>
  <div class="kpi nuisance"><div class="kpi-label">Nuisance</div><div class="kpi-value">{n_nuisance}</div><div class="kpi-sub">Budget brand undercutting</div></div>
  <div class="kpi watch"><div class="kpi-label">Watch</div><div class="kpi-value">{n_watch}</div><div class="kpi-sub">Premium IAM, not yet aggressive</div></div>
  <div class="kpi ignore"><div class="kpi-label">Ignore</div><div class="kpi-value">{n_ignore}</div><div class="kpi-sub">Low threat + low quality</div></div>
</div>

<div class="chart-card">
  <h2>2×2 — Quality × Threat (bubble size = CY2025 revenue at risk)</h2>
  {plotly_div}
</div>

<div class="quadrants">
  <div class="quad-card dangerous"><h3>Dangerous</h3><div class="qdesc">High-quality IAM (Bosch/Denso/Febi tier) actively undercutting dealer-sell-to-workshop genuine. Strategic priority.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_dangerous}</tbody></table>
  </div>
  <div class="quad-card nuisance"><h3>Nuisance</h3><div class="qdesc">Budget brand pricing pressure. Marketing/comms problem — workshops reluctant to use these on Isuzu.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_nuisance}</tbody></table>
  </div>
  <div class="quad-card watch"><h3>Watch</h3><div class="qdesc">Premium IAM brands present but not aggressive on price. Could become dangerous.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_watch}</tbody></table>
  </div>
  <div class="quad-card ignore"><h3>Ignore</h3><div class="qdesc">Low quality + low threat. Noise.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_ignore}</tbody></table>
  </div>
</div>

<div class="footer">Generated {timestamp} · Sources: Autodoc UK + KS International + Mekonomen · Brand tiers from iam_brand_tiers.csv</div>
</body></html>"""


# ────────────────────────────────────────────────────────────────────
# THEME 2: Aged Broadsheet (Fraunces / sepia / burgundy)
# ────────────────────────────────────────────────────────────────────

BROADSHEET_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IAM Threat Matrix · ISZE</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,400&family=Instrument+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --paper:   #f5eedd;
  --paper2:  #efe7d3;
  --ink:     #1a1612;
  --ink2:    #3d342a;
  --ink3:    #6a5d4d;
  --rule:    #a89a82;
  --burgundy:#8b1a2e;
  --burgundy-dim:#e8d4d7;
  --rust:    #b85820;
  --moss:    #4a5d3a;
  --slate:   #2a3a52;
  --grey:    #877b67;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--paper); color:var(--ink2); font-family:'Instrument Sans',sans-serif;
       padding:40px 28px 80px; max-width:1280px; margin:0 auto; line-height:1.5;
       background-image:
         radial-gradient(circle at 15% 10%, rgba(168,154,130,0.08) 0, transparent 35%),
         radial-gradient(circle at 85% 80%, rgba(139,26,46,0.04) 0, transparent 40%); }

.masthead { text-align:center; padding-bottom:24px; border-bottom:3px double var(--rule); margin-bottom:28px; position:relative; }
.masthead-overline { font-family:'DM Mono',monospace; font-size:0.7rem; letter-spacing:0.3em;
                     text-transform:uppercase; color:var(--ink3); margin-bottom:10px; }
.masthead h1 { font-family:'Fraunces',serif; font-weight:900; font-style:italic;
               font-size:clamp(2.2rem, 5vw, 3.8rem); color:var(--ink); letter-spacing:-0.02em;
               line-height:1; font-variation-settings:"opsz" 144; }
.masthead h1 em { font-style:italic; color:var(--burgundy); }
.masthead-rule { display:flex; align-items:center; justify-content:center; gap:18px;
                 margin-top:14px; font-family:'DM Mono',monospace; font-size:0.7rem;
                 letter-spacing:0.18em; text-transform:uppercase; color:var(--ink3); }
.masthead-rule .dot { width:5px; height:5px; border-radius:50%; background:var(--burgundy); }
.subtitle { font-family:'Fraunces',serif; font-size:1.05rem; color:var(--ink2);
            text-align:center; max-width:820px; margin:18px auto 0; line-height:1.55;
            font-style:italic; font-weight:400; }

.kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:32px; }
.kpi { background:var(--paper2); border:1px solid var(--rule); padding:20px 18px;
       position:relative; }
.kpi.dangerous { border-top:4px solid var(--burgundy); }
.kpi.nuisance  { border-top:4px solid var(--rust); }
.kpi.watch     { border-top:4px solid var(--slate); }
.kpi.ignore    { border-top:4px solid var(--grey); }
.kpi-label { font-family:'DM Mono',monospace; font-size:0.66rem; letter-spacing:0.18em;
             text-transform:uppercase; color:var(--ink3); }
.kpi-value { font-family:'Fraunces',serif; font-size:2.4rem; font-weight:900;
             color:var(--ink); margin-top:4px; line-height:1; font-variation-settings:"opsz" 96; }
.kpi-sub { font-family:'Fraunces',serif; font-style:italic; font-size:0.85rem;
           color:var(--ink3); margin-top:8px; }

.chart-card { background:var(--paper2); border:1px solid var(--rule); padding:24px;
              margin-bottom:32px; position:relative; }
.chart-card::before { content:''; position:absolute; top:-1px; left:-1px; right:-1px;
                       height:3px; background:repeating-linear-gradient(90deg,
                       var(--burgundy) 0, var(--burgundy) 8px, transparent 8px, transparent 14px); }
.chart-card h2 { font-family:'Fraunces',serif; font-size:1.4rem; font-weight:700;
                 color:var(--ink); margin-bottom:6px; font-style:italic; }
.chart-card .h2-meta { font-family:'DM Mono',monospace; font-size:0.66rem;
                       letter-spacing:0.14em; text-transform:uppercase;
                       color:var(--ink3); margin-bottom:16px; }

.quadrants { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
@media (max-width:980px) { .quadrants { grid-template-columns:1fr; } }
.quad-card { background:var(--paper2); border:1px solid var(--rule); padding:22px; }
.quad-card.dangerous { border-left:6px solid var(--burgundy); }
.quad-card.nuisance  { border-left:6px solid var(--rust); }
.quad-card.watch     { border-left:6px solid var(--slate); }
.quad-card.ignore    { border-left:6px solid var(--grey); }
.quad-card h3 { font-family:'Fraunces',serif; font-size:1.6rem; font-weight:900;
                color:var(--ink); margin-bottom:4px; font-variation-settings:"opsz" 96; }
.quad-card.dangerous h3 { color:var(--burgundy); }
.quad-card.nuisance h3  { color:var(--rust); }
.quad-card.watch h3     { color:var(--slate); }
.quad-card .qdesc { font-family:'Fraunces',serif; font-style:italic; font-size:0.92rem;
                    color:var(--ink2); margin-bottom:18px; line-height:1.5; }

table { width:100%; border-collapse:collapse; font-size:0.78rem; font-family:'Instrument Sans',sans-serif; }
th { text-align:left; font-family:'DM Mono',monospace; font-weight:500; color:var(--ink3);
     font-size:0.62rem; letter-spacing:0.12em; text-transform:uppercase;
     padding:9px 6px; border-bottom:1px solid var(--rule); }
td { padding:8px 6px; border-bottom:1px dotted var(--rule); color:var(--ink2); }
td.pn { font-family:'DM Mono',monospace; font-size:0.72rem; color:var(--ink); font-weight:500; }
td.brand { font-family:'Fraunces',serif; font-weight:700; color:var(--burgundy); font-size:0.84rem; }
td.num { font-family:'DM Mono',monospace; text-align:right; font-size:0.72rem; color:var(--ink); }
td.score { text-align:center; font-family:'Fraunces',serif; font-weight:700; font-size:0.95rem; }
td.score.t { color:var(--burgundy); }
td.score.q { color:var(--slate); }
td.lnk a { color:var(--burgundy); text-decoration:none; font-weight:700; }
td.lnk a:hover { text-decoration:underline; }
td.empty { text-align:center; color:var(--ink3); padding:24px;
           font-family:'Fraunces',serif; font-style:italic; }

.footer { margin-top:40px; padding-top:20px; border-top:3px double var(--rule);
          font-family:'DM Mono',monospace; font-size:0.66rem; letter-spacing:0.14em;
          text-transform:uppercase; color:var(--ink3); text-align:center; }
</style></head>
<body>
<div class="masthead">
  <div class="masthead-overline">ISZE Aftermarket Intelligence — Bulletin</div>
  <h1>IAM <em>Threat × Quality</em> Matrix</h1>
  <div class="masthead-rule"><span class="dot"></span><span>{timestamp}</span><span class="dot"></span><span>Apples to apples</span><span class="dot"></span><span>One PN, one threat brand</span><span class="dot"></span></div>
  <p class="subtitle">{subtitle}</p>
</div>

<div class="kpi-row">
  <div class="kpi dangerous"><div class="kpi-label">Dangerous</div><div class="kpi-value">{n_dangerous}</div><div class="kpi-sub">High threat & high quality</div></div>
  <div class="kpi nuisance"><div class="kpi-label">Nuisance</div><div class="kpi-value">{n_nuisance}</div><div class="kpi-sub">Budget brand pressure</div></div>
  <div class="kpi watch"><div class="kpi-label">Watch</div><div class="kpi-value">{n_watch}</div><div class="kpi-sub">Premium IAM, not yet sharp</div></div>
  <div class="kpi ignore"><div class="kpi-label">Ignore</div><div class="kpi-value">{n_ignore}</div><div class="kpi-sub">Noise</div></div>
</div>

<div class="chart-card">
  <h2>The map of the threat</h2>
  <div class="h2-meta">Quality × Threat · bubble size = revenue at risk</div>
  {plotly_div}
</div>

<div class="quadrants">
  <div class="quad-card dangerous"><h3>Dangerous</h3><div class="qdesc">Bosch, Denso, Febi-tier IAM brands actively undercutting dealer-sell-to-workshop genuine. The strategic priority.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_dangerous}</tbody></table>
  </div>
  <div class="quad-card nuisance"><h3>Nuisance</h3><div class="qdesc">Budget brand pricing pressure. A marketing problem — workshops reluctant to fit these.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_nuisance}</tbody></table>
  </div>
  <div class="quad-card watch"><h3>Watch</h3><div class="qdesc">Premium IAM present but not aggressive on price yet. Could escalate.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_watch}</tbody></table>
  </div>
  <div class="quad-card ignore"><h3>Ignore</h3><div class="qdesc">Low quality, low threat. Below the line.</div>
    <table><thead><tr><th>PN</th><th>Description</th><th>Brand</th><th>PR00</th><th>DLR→WS</th><th>AM</th><th>T</th><th>Q</th><th>Rev CY25</th><th></th></tr></thead><tbody>{rows_ignore}</tbody></table>
  </div>
</div>

<div class="footer">Generated {timestamp} · Sources: Autodoc UK · KS International · Mekonomen · Brand tiers curated</div>
</body></html>"""


def _render(template: str, scored: pd.DataFrame, subtitle: str) -> str:
    counts = scored["quadrant"].value_counts().to_dict() if "quadrant" in scored.columns else {}
    replacements = {
        "{timestamp}":     datetime.now().strftime("%d %B %Y · %H:%M"),
        "{subtitle}":      subtitle,
        "{n_dangerous}":   str(int(counts.get("Dangerous", 0))),
        "{n_nuisance}":    str(int(counts.get("Nuisance", 0))),
        "{n_watch}":       str(int(counts.get("Watch", 0))),
        "{n_ignore}":      str(int(counts.get("Ignore", 0))),
        "{plotly_div}":    _plotly_div(scored),
        "{rows_dangerous}":_quadrant_table_rows(scored, "Dangerous"),
        "{rows_nuisance}": _quadrant_table_rows(scored, "Nuisance"),
        "{rows_watch}":    _quadrant_table_rows(scored, "Watch"),
        "{rows_ignore}":   _quadrant_table_rows(scored, "Ignore"),
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def build_html(scored: pd.DataFrame, out_path: Path, theme: str = "plex") -> Path:
    """Build a single HTML matrix file. theme = 'plex' (default) or 'broadsheet'."""
    n = len(scored)
    n_scored = scored["quadrant"].ne("No data").sum() if "quadrant" in scored.columns else n
    subtitle = (
        f"Scoring {n_scored} parts numbers across {scored['primary_threat_brand'].nunique() if 'primary_threat_brand' in scored.columns else 0} "
        f"aftermarket brands. Threat = apples-to-apples economic risk to the dealer chain. "
        f"Quality = brand tier ⊕ OE-supplier signal."
    )
    template = BROADSHEET_TEMPLATE if theme == "broadsheet" else PLEX_TEMPLATE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render(template, scored, subtitle), encoding="utf-8")
    return out_path


def build_both_previews(scored: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    """Legacy: build both themes side-by-side."""
    return {
        "IBM Plex (default)":  build_html(scored, out_dir / "iam_matrix_plex.html", "plex"),
        "Aged Broadsheet":     build_html(scored, out_dir / "iam_matrix_broadsheet.html", "broadsheet"),
    }
