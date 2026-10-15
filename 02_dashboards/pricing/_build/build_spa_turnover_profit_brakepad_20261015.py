# -*- coding: utf-8 -*-
"""Build SPA turnover-vs-profit exercise HTML — brake pad case + Duncan."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ROOT / "02_dashboards" / "pricing"
HTML = OUT_DIR / "ISZE_SPA_Turnover_vs_Profit_BrakePad_Exercise_2026-10-15.html"
CMD = OUT_DIR / "OPEN_SPA_Turnover_vs_Profit_BrakePad_Exercise.cmd"
SCEN = OUT_DIR / "_build" / "_tmp_brake_pad_spa_exercise_20261015.json"

sc = json.loads(SCEN.read_text(encoding="utf-8"))
fam = sc["family"]
kit = sc["kit_8982447940"]
ela = sc["elasticity"]
be = sc["break_even_at_minus_20pct_price"]

# pick key scenarios for chart
want = [
    "brake_pad reading / linear",
    "brake_pad reading / CE",
    "AIM Brakes reading / CE",
    "claimed -4 / linear",
    "dealer stress / CE",
    "dealer central / CE",
]
scen_map = {s["label"]: s for s in sc["scenarios_minus_20pct_price"]}
bars = [scen_map[k] for k in want if k in scen_map]

# euro bars for pad reading vs claimed on family
pad_lin = scen_map["brake_pad reading / linear"]
claimed = scen_map["claimed -4 / linear"]

payload = {
    "meta": {
        "title": "SPA approval — turnover vs profit (brake pad exercise)",
        "as_of": "2026-10-15",
        "audience": "internal",
        "window_family": "ITUK brake pads CY2025 (PMS total)",
        "window_kit": "ITUK billed 8982447940 CY2025",
    },
    "family": fam,
    "kit": kit,
    "elasticity": ela,
    "break_even": be,
    "gm0_assumption_pct": sc["gm0_assumption_pct"],
    "scenarios": bars,
    "duncan": {
        "mail_proposal": "2026-09-15 — PMS Project - Braking to Jerome",
        "mail_yoshimoto": "2026-10-06 — Duncan to Suzuki san (FYI to Jerome): SPA rejected by Yoshimoto san",
        "primary_pn": "8982447940",
        "secondary_pn": "8982169220",
        "ituk_gp_n75_pct": 18.3,
        "ituk_gp_n35_pct": 41.9,
        "n75_units_2023": 2802,
        "n75_units_2025": 2367,
        "n75_units_2026_ann": 2478,
        "recommended_floor_pct": 10,
        "stretch": "restore N75 to 2023 volume",
        "quote_reject": "Yoshimoto san will only approve the SPA if there is growth in units/profit.",
        "quote_hold": "I wanted to launch the PMS project on the 1st of October, but without price support, it has been put on hold.",
        "quote_rework": "We are re-working the SPA so we show units/profit growth so Yoshimoto san will approve.",
        "quote_slide6": "In 2026 ITUK reduced margin to help Retail Price as SPA rejected.",
    },
}

# CSS bar widths from qty uplift (cap 100 for display of claimed)
def w(pct, cap=160):
    return max(2, min(100, abs(pct) / cap * 100))

bar_rows = []
for s in bars:
    bar_rows.append(
        f"""<div class="bar-row" data-lab="{s['label']}">
  <div class="lab">{s['label']}</div>
  <div class="track"><div class="fill {'bad' if 'claimed' in s['label'] else 'ok'}" style="width:{w(s['d_qty_pct']):.1f}%"></div></div>
  <div class="num">qty {s['d_qty_pct']:+.0f}% · euro {s['d_eur_pct']:+.0f}% · profit {s['d_profit_pct']:+.0f}%</div>
</div>"""
    )

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>SPA turnover vs profit — brake pad exercise</title>
<style>
:root {{ --navy:#15233c; --terra:#c0552d; --paper:#f7f4ee; --ink:#222; --muted:#6b6256; --line:#ddd6c8; --ok:#1d6b4f; --bad:#9b2c2c; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:15px/1.45 system-ui,Segoe UI,sans-serif; color:var(--ink); background:var(--paper); }}
h1,h2,h3 {{ font-family:Georgia,serif; color:var(--navy); margin:0 0 .4rem; }}
header {{ background:var(--navy); color:var(--paper); padding:1.4rem 1.6rem 1.2rem; }}
header h1 {{ color:var(--paper); font-size:1.55rem; }}
header p {{ margin:.35rem 0 0; color:#c9c2b4; max-width:62rem; }}
main {{ max-width:980px; margin:0 auto; padding:1.2rem 1.2rem 3rem; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.7rem; margin:1rem 0 1.2rem; }}
.kpi {{ background:#fff; border:1px solid var(--line); padding:.75rem .85rem; position:relative; cursor:help; }}
.kpi .lbl {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
.kpi .val {{ font:700 1.35rem/1.15 Georgia,serif; color:var(--navy); margin-top:.2rem; }}
.kpi .sub {{ font-size:.78rem; color:var(--muted); margin-top:.15rem; }}
.kpi:hover::after {{ content:attr(data-tip); position:absolute; left:0; right:0; top:100%; z-index:5; margin-top:.35rem; background:var(--navy); color:var(--paper); padding:.65rem .75rem; font-size:.78rem; line-height:1.35; border-top:3px solid var(--terra); }}
section {{ background:#fff; border:1px solid var(--line); padding:1rem 1.1rem 1.15rem; margin:0 0 1rem; }}
section h2 {{ font-size:1.15rem; }}
.lead {{ color:var(--muted); margin:0 0 .8rem; }}
.verdict {{ border-left:4px solid var(--terra); padding:.15rem 0 .15rem .9rem; margin:0 0 1rem; }}
.verdict strong {{ color:var(--navy); }}
.bar-row {{ display:grid; grid-template-columns:11.5rem 1fr 14rem; gap:.55rem; align-items:center; margin:.45rem 0; }}
.bar-row .lab {{ font-size:.78rem; color:var(--navy); }}
.bar-row .track {{ background:#ece7dc; height:1.05rem; }}
.bar-row .fill {{ height:100%; background:var(--ok); }}
.bar-row .fill.bad {{ background:var(--terra); }}
.bar-row .num {{ font-size:.78rem; color:var(--muted); text-align:right; }}
table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
th,td {{ border-bottom:1px solid var(--line); padding:.45rem .4rem; text-align:left; }}
th {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.03em; color:var(--muted); }}
td.r, th.r {{ text-align:right; font-variant-numeric:tabular-nums; }}
.tag {{ display:inline-block; font-size:.7rem; padding:.1rem .4rem; background:#ece7dc; color:var(--navy); }}
.tag.warn {{ background:#f3d9cf; color:#6a2a12; }}
.tag.ok {{ background:#d7ebe2; color:#144433; }}
blockquote {{ margin:.6rem 0; padding:.55rem .8rem; background:#f3f0e8; border-left:3px solid var(--navy); color:#333; font-size:.92rem; }}
.foot {{ font-size:.75rem; color:var(--muted); margin-top:.8rem; }}
ul.plain {{ margin:.3rem 0 .6rem 1.1rem; padding:0; }}
ul.plain li {{ margin:.25rem 0; }}
@media (max-width:820px) {{
  .kpis {{ grid-template-columns:1fr 1fr; }}
  .bar-row {{ grid-template-columns:1fr; }}
  .bar-row .num {{ text-align:left; }}
}}
</style>
</head>
<body>
<header>
  <h1>SPA approval — turnover vs profit</h1>
  <p>Internal exercise, 15 October 2026. Brake pad price/volume check, Duncan’s ITUK braking SPA, and why the dual approval base (turnover and profit) is blocking the GPS SPA route.</p>
</header>
<main>

<section class="verdict">
  <h2>Verdict</h2>
  <p><strong>A −20% price does not produce +80% brake-pad sales on our numbers.</strong> That claim needs a price sensitivity of about −4. The pad reading is about −1.6; all brakes about −2.4. Even those are rough. Duncan’s own SPA asks for about +10% volume as the floor, not +80%. Yoshimoto san rejected the SPA unless there is growth in units and profit — that dual base is the hard KPI.</p>
</section>

<div class="kpis">
  <div class="kpi" data-tip="ITUK PMS total brake-pad capture, calendar 2025. Expected units from the service model; actual from billed lines.">
    <div class="lbl">ITUK pad capture 2025</div>
    <div class="val">{fam['capture_rate']*100:.0f}%</div>
    <div class="sub">{fam['actual_qty']:,.0f} of {fam['expected_qty']:,.0f} kits · €{fam['actual_rev_eur']:,.0f} billed</div>
  </div>
  <div class="kpi" data-tip="Main N75 front pad kit billed by ISZE to ITUK (sold-to 2575), calendar 2025.">
    <div class="lbl">Kit 8982447940</div>
    <div class="val">€{kit['eur']:,.0f}</div>
    <div class="sub">{kit['qty']:,.0f} pcs · €{kit['asp_eur']:.0f} avg · {kit['share_of_family_eur']*100:.0f}% of ITUK pad euros</div>
  </div>
  <div class="kpi" data-tip="From Duncan’s SPA pack (dealer net price vs his cost). Matches the August meeting note that ITUK pad margin is already thin after logistics.">
    <div class="lbl">ITUK margin on N75 kit</div>
    <div class="val">18.3%</div>
    <div class="sub">N35 kit 41.9% — N75 has no room for a further ITUK cut</div>
  </div>
  <div class="kpi" data-tip="Qty needed just to keep the same euro after a 20% price cut (+25%), and to keep the same euro profit if starting margin is 53% class (+61%).">
    <div class="lbl">Break-even after −20% price</div>
    <div class="val">+{be['qty_for_same_eur_pct']:.0f}% / +{be['qty_for_same_profit_pct']:.0f}%</div>
    <div class="sub">same billed euro · same profit (53% start margin)</div>
  </div>
</div>

<section>
  <h2>What happens if we cut pad price 20%?</h2>
  <p class="lead">Chart question: how much extra volume does each sensitivity reading imply, and what does that do to billed euros and profit?</p>
  {''.join(bar_rows)}
  <table style="margin-top:.9rem">
    <thead><tr><th>Reading</th><th class="r">Qty</th><th class="r">Billed €</th><th class="r">Profit €</th><th class="r">Margin</th></tr></thead>
    <tbody>
      <tr><td>Pad reading (−1.59), simple</td><td class="r">{pad_lin['d_qty_pct']:+.0f}%</td><td class="r">{pad_lin['d_eur_pct']:+.0f}%</td><td class="r">{pad_lin['d_profit_pct']:+.0f}%</td><td class="r">53% → 41%</td></tr>
      <tr><td><span class="tag warn">Claimed −4 → +80% qty</span></td><td class="r">{claimed['d_qty_pct']:+.0f}%</td><td class="r">{claimed['d_eur_pct']:+.0f}%</td><td class="r">{claimed['d_profit_pct']:+.0f}%</td><td class="r">53% → 41%</td></tr>
      <tr><td>Dealer stress proxy (−0.81)</td><td class="r">{scen_map['dealer stress / CE']['d_qty_pct']:+.0f}%</td><td class="r">{scen_map['dealer stress / CE']['d_eur_pct']:+.0f}%</td><td class="r">{scen_map['dealer stress / CE']['d_profit_pct']:+.0f}%</td><td class="r">53% → 41%</td></tr>
    </tbody>
  </table>
  <p class="foot">Elasticity from price_volume_elasticity.csv (pad β={ela['brake_pad_beta']}, se {ela['brake_pad_se']}, 95% band {ela['brake_pad_ci95'][0]} to {ela['brake_pad_ci95'][1]}; AIM Brakes β={ela['aim_brakes_beta']}). Low power — direction only. Starting ISZE class margin 53% is an illustration for the cut arithmetic; Duncan’s pack shows ITUK already at 18.3% on the N75 kit.</p>
</section>

<section>
  <h2>Duncan example — brake SPA after Japan</h2>
  <p class="lead">15 September 2026: Duncan sent the braking presentation and SPA business case after the August Japan meeting (focus brakes, not filtration). Primary line N75 kit 8982447940; secondary N35 8982169220.</p>
  <table>
    <thead><tr><th>Item</th><th class="r">2023</th><th class="r">2025</th><th class="r">2026 ann.</th><th>Note</th></tr></thead>
    <tbody>
      <tr><td>N75 pad kit wholesale units (ITUK)</td><td class="r">2,802</td><td class="r">2,367</td><td class="r">2,478</td><td>Parc up, intensity down — SPA case</td></tr>
      <tr><td>Duncan programme floor</td><td class="r" colspan="3">+10% vs protected dealer baseline</td><td>Not +80%</td></tr>
      <tr><td>Stretch</td><td class="r" colspan="3">Restore N75 to 2023 volume</td><td>~+435 N75 units in his scenario table</td></tr>
      <tr><td>ITUK GP on N75 kit</td><td class="r" colspan="3">18.3%</td><td>No further ITUK cut without ISZE/IML SPA</td></tr>
    </tbody>
  </table>
  <blockquote>6 Oct 2026 — Duncan to Suzuki san (copied to Jerome as FYI): “The SPA proposal was rejected by Norihiro Yoshimoto san, not ITUK. Yoshimoto san will only approve the SPA if there is growth in units/profit… without price support, [1 Oct launch] has been put on hold. We are re-working the SPA so we show units/profit growth so Yoshimoto san will approve.”</blockquote>
  <p>He went straight to the Japan / Yoshimoto loop on the braking SPA. That matches the dual base problem: turnover growth alone is not enough under the current approval rule.</p>
  <p class="foot">Sources: mail PMS Project - Braking (15 Sep); FW PMS Project - Braking (6 Oct); workbook PMS_Brake_Incentive_Baseline_and_SPA_Business_Case.xlsx; deck PMS Project Brake Sales Promotion.pptx. Files under 01_data\\90_INBOX\\_duncan_brake_spa_20260915\\.</p>
</section>

<section>
  <h2>Why SPA applications stay few — and hard to approve</h2>
  <p class="lead">During GPS / sales reviews we asked distributors for SPAs. Few formal applications came back. The ones that did (UTI spa2 rounds, IUK wipers, ITUK brakes) struggle on the approval math.</p>
  <ul class="plain">
    <li><span class="tag">Turnover base</span> — more billed euros / more pieces than the reference period.</li>
    <li><span class="tag warn">Profit base</span> — more euro profit than before, even after the discount. That is the hard one when the distributor needs a real price cut.</li>
    <li>On pads, a −20% price already cuts unit margin from 53% to ~41% at ISZE (illustration). You need about +61% volume just to hold the same profit. The honest pad reading does not give you that.</li>
    <li>August ITUK MoM already left open: SPA approval criteria — turnover-only vs profit — ISZE management decision.</li>
  </ul>
</section>

<section>
  <h2>Ask for management</h2>
  <p>Finance has been saying our margin is already high. On the commercial book, profit is the easier side of plan; turnover is the one slightly behind. If Yoshimoto san’s rule stays “units and profit”, every meaningful SPA (Duncan’s brakes first) dies on the profit base.</p>
  <p><strong>Ask:</strong> approve SPA cases where we clearly grow turnover (and units), even if euro profit on those lines is flat or slightly down — provided the company margin/profit position overall stays healthy. That is the only approval KPI that is realistically hard for GPS SPA work. Without it, distributors stop applying, and ITUK’s brake PMS stays on hold.</p>
</section>

<section>
  <h2>Breakdown — numbers used</h2>
  <table>
    <thead><tr><th>Block</th><th>Figure</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>ITUK pad family CY2025</td><td>{fam['actual_qty']:,.0f} pcs · €{fam['actual_rev_eur']:,.0f} · capture {fam['capture_rate']*100:.1f}% · gap €{fam['revenue_gap_eur']:,.0f}</td><td>pms_capture_by_db_year.csv</td></tr>
      <tr><td>Kit 8982447940 CY2025</td><td>{kit['qty']:,.0f} pcs · €{kit['eur']:,.0f} · ASP €{kit['asp_eur']:.2f}</td><td>sales_fact.parquet · sold-to 2575</td></tr>
      <tr><td>Pad elasticity</td><td>β {ela['brake_pad_beta']} (se {ela['brake_pad_se']})</td><td>price_volume_elasticity.csv</td></tr>
      <tr><td>Duncan N75 units</td><td>2023 2,802 · 2025 2,367 · 2026 ann. 2,478</td><td>Duncan SPA deck / workbook</td></tr>
      <tr><td>Duncan ITUK GP%</td><td>N75 18.3% · N35 41.9%</td><td>Duncan SPA deck slide 9</td></tr>
      <tr><td>Yoshimoto reject</td><td>units and profit growth required</td><td>Duncan → Suzuki 6 Oct 2026</td></tr>
    </tbody>
  </table>
  <p class="foot">Internal only. Not a list change. Margin 53% in the cut arithmetic is the class illustration for ISZE; do not confuse with Duncan’s 18.3% ITUK margin on the N75 kit. Profit vs turnover vs plan is the finance/management framing Jerome asked to stress — exact YTD GP% vs BP not re-derived in this page from the daily billing file (that file is euros billed vs BP, not GP).</p>
</section>

<script type="application/json" id="payload">{json.dumps(payload, ensure_ascii=False)}</script>
</body>
</html>
"""

HTML.write_text(html, encoding="utf-8")
# CRLF cmd
cmd = '@echo off\r\nstart "" "%~dp0ISZE_SPA_Turnover_vs_Profit_BrakePad_Exercise_2026-10-15.html"\r\n'
CMD.write_bytes(cmd.encode("ascii"))
print("HTML", HTML, HTML.stat().st_size)
print("CMD", CMD)
# paint check counts
text = html
assert 'class="bar-row"' in text and text.count('class="bar-row"') >= 4
assert "Yoshimoto" in text and "8982447940" in text
assert "+80%" in text or "+80" in text
print("PAINT_MARKERS_OK", "bar-rows", text.count('class="bar-row"'))
