#!/usr/bin/env python3
"""Build Mode A exec aftersales paper (self-contained HTML + Chart.js inline)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "02_dashboards" / "sales" / "ISZE_Exec_Aftersales_Paper.html"
CHART = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

VERIFY_AT = "2026-08-25T17:19:54Z"
BILLING_MAX = "2026-06-30"
VERIFY_PASS, VERIFY_FAIL = 116, 0


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
    wallet_bars = bars(
        [
            ("ITUK", 11.61, "€11.6M below ceiling", "#c0552d"),
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
    pms_net = bars(
        [
            ("Ireland", 100, "100% cap · 191% raw", "#6b7c93"),
            ("ITUK", 100, "100% cap · 116% raw", "#6b7c93"),
            ("Greece", 97.2, "97%", "#1d9e75"),
            ("UTI", 91.3, "91%", "#1d9e75"),
            ("Cyprus", 91.2, "91%", "#1d9e75"),
            ("UMI", 85.2, "85%", "#1d9e75"),
            ("Belgium", 62.6, "63%", "#c48a16"),
            ("Portugal", 52.1, "52%", "#c48a16"),
            ("Sweden", 48.7, "49%", "#c48a16"),
            ("IUK", 37.7, "38%", "#c0453c"),
            ("Hungary", 45.0, "45%", "#c48a16"),
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
    price_cov = bars(
        [
            ("Denmark", 17.09, "17%", "#c48a16"),
            ("Hungary", 13.26, "13%", "#c0453c"),
            ("Sweden", 13.04, "13%", "#c0453c"),
            ("ITUK", 12.55, "13%", "#c0453c"),
            ("Norway", 12.29, "12%", "#c0453c"),
            ("Ireland", 10.27, "10%", "#c0453c"),
            ("Greece", 10.22, "10%", "#c0453c"),
            ("Belgium", 6.30, "6%", "#6b6256"),
            ("Germany", 6.37, "6%", "#6b6256"),
            ("UTI", 2.97, "3%", "#6b6256"),
            ("UMI", 1.02, "1%", "#6b6256"),
        ],
        max_v=20,
    )
    repl = bars(
        [
            ("Billed, no matching sell-out", 500, "500", "#c0552d"),
            ("High sell-through vs bill", 400, "400", "#c48a16"),
            ("Sell-out with no bill", 380, "380", "#2b4a78"),
            ("Low sell-through", 315, "315", "#8a6a4a"),
        ],
        max_v=500,
    )
    tenders = bars(
        [
            ("EU above-threshold feed", 159, "159", "#2b4a78"),
            ("Germany national", 41, "41", "#1d9e75"),
            ("France national", 20, "20", "#1d9e75"),
            ("Poland national", 16, "16", "#1d9e75"),
            ("Belgium national", 6, "6", "#1d9e75"),
            ("Israel national", 5, "5", "#1d9e75"),
            ("Italy national", 1, "1", "#c48a16"),
            ("UK Contracts Finder", 1, "1", "#c48a16"),
        ],
        max_v=159,
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
  padding:11mm 12mm 14mm;position:relative;box-shadow:0 2px 10px rgba(21,35,60,.18);
  break-after:page;page-break-after:always;overflow:hidden
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
.chart-wrap{position:relative;height:168px}
.bars{display:flex;flex-direction:column;gap:4px}
.bar-row{display:grid;grid-template-columns:minmax(72px,28%) 1fr minmax(92px,30%);gap:6px;align-items:center;font-size:11px}
.bl{color:#52514e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bt{background:#eceae4;height:13px;border-radius:2px;overflow:hidden}
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
.swot-cell{background:#fff;border:1px solid #e3ded3;padding:8px 10px;margin-bottom:8px}
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
  .paper-page{box-shadow:none;margin:0;width:auto;min-height:0}
  .stat .tip{display:none !important}
  .chart-wrap{display:none}
}
"""

    pages = []

    # --- 1 Cover ---
    pages.append(f"""
<section class="paper-page cover" id="p1" data-page="1">
  <header class="ph"><span class="pk">ISZE · IML top management</span><span class="pn">Page 1 of 16</span></header>
  <p style="padding:8px 12mm 0;color:#a9bad4;letter-spacing:.16em;text-transform:uppercase;font-size:11px;margin:0">Aftersales parts hub · not vehicle manufacturing</p>
  <h1>Where the European parts wallet sits — and which five decisions would move it</h1>
  <div class="rule"></div>
  <p class="thesis">We located <b style="color:#fff">€30.8M of a €60.2M CY2025 wallet</b>. UK truck cover is <b style="color:#fff">35.1%</b> on the IML schedule (€2.04M gap). Independent unit volume is <b style="color:#fff">UNKNOWN</b>. Five existing decisions would move 90 days.</p>
  <div class="stats">
    <div class="stat" tabindex="0">
      <div class="l">Network GPS · CY2025</div>
      <div class="v">51.1%</div>
      <div class="s">€30.76M of a €60.22M max-spend ceiling</div>
      <div class="tip">GPS here is captured parts sales ÷ theoretical wallet (max-spend ceiling, not a forecast). Traffic-light spend-per-unit is a sibling metric on page 3. Does not include unsigned list-to-pocket euros.</div>
    </div>
    <div class="stat" tabindex="0">
      <div class="l">UK truck oil-filter cover</div>
      <div class="v">35.1%</div>
      <div class="s">IML service schedule · UIO 22,389 · gap €2.04M (5 cat.)</div>
      <div class="tip">External worked example: IML service frequency on the full UK registered parc. A separate network-comparable ranking (different denominator) is used only to place distributors next to each other — never as this 35.1%.</div>
    </div>
    <div class="stat" tabindex="0">
      <div class="l">Genuine share of what was sold</div>
      <div class="v">96.5%</div>
      <div class="s">Network captured mix CY2025 · BVP 3.5% (€1.06M)</div>
      <div class="tip">Mix of billed genuine vs BVP. This is quality of what was sold, not a capture rate. BVP has no capture %. Residual of PMS is not independent-garage share.</div>
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
    <div><b>3</b> Network wallet and GPS</div>
    <div><b>4</b> Workshop-basket cover</div>
    <div><b>5</b> Mix — quality of what was sold</div>
    <div><b>6</b> Distributor league</div>
    <div><b>7</b> Dealer network scores</div>
    <div><b>8</b> Price vs reference sell-out</div>
    <div><b>9</b> Demand, replenishment, forecast</div>
    <div><b>10</b> Public tenders</div>
    <div><b>11</b> Integrity and labelled holes</div>
    <div><b>12–13</b> SWOT (ISZE aftersales)</div>
    <div><b>14</b> Five asks in 90 days</div>
    <div><b>15</b> What would change our mind</div>
    <div><b>16</b> Sources and verify stamp</div>
  </div>
  <footer class="pf">Mode A · English · printable A4 · self-contained (no network required to paint)</footer>
</section>
""")

    # --- 2 How to read ---
    pages.append(page(2, "Legend", "How to read this paper",
        "Every headline here is either a signed CY2025 fact, a labelled YTD, or an explicit UNKNOWN — never a blended Israel, never a fake independent-garage share.",
        f"""
<p class="lede">This is an aftersales paper for the European parts hub. It is not a Japan P&amp;L, not a vehicle-sales review, and not a new 0–100 score (that scoring family is closed).</p>
<div class="grid2">
  <div class="card">
    <h3>What the numbers are</h3>
    <p><b>GPS</b> — euros of parts sold per unit in parc, and captured sales versus a max-spend ceiling. Green spend-per-unit is ≥ €150, amber €50–150, red &lt; €50. Ceiling is not a forecast.</p>
    <p><b>PMS total</b> — units sold in the service basket versus expected demand. Headline is total (genuine + BVP). Genuine is a quality lens only.</p>
    <p><b>Mix</b> — of what was sold, how much is genuine vs BVP. Mix is not capture. BVP has no capture rate.</p>
    <p><b>CY2025</b> is complete. <b>2026 YTD</b> is 1 January–{BILLING_MAX}. Partial years are never annualised.</p>
  </div>
  <div class="card">
    <h3>What the numbers are not</h3>
    <p><b>Two UK-truck covers exist.</b> This paper’s worked example is the IML service schedule (oil-filter 35.1%, UIO 22,389, gap €2.04M). When distributors are ranked against each other we use one shared denominator (bucketed parc 23,068 for that row). They answer different questions; they are not two versions of “the” capture %.</p>
    <p><b>Israel is two distributors</b> — UTI and UMI — always two rows. The Israel dealer-score round is UMI only.</p>
    <p><b>IUK is not ITUK.</b> Ireland is not IUK. Independent-garage <b>unit volume is UNKNOWN</b>. <code>100% − PMS</code> is residual: lost service + DIY + other-OEM + export + interval error + parc error + IAM. Not IAM alone.</p>
  </div>
</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Independent-garage unit share · unsigned list-to-pocket euros (existence of a pocket gap may be named; the euro is not quoted here) · air-filter interval pending IML confirmation on the network-comparable view · UK-truck brake wear 0.4 vs 0.8.</div>
<div class="callout good"><b>Reference sell-out</b> = list × 1.40 × 1.275 (= ×<b>1.785</b>). Price index = shop price ÷ reference sell-out. We say OEM peer retail / dealer sell-out / reference sell-out — never a slang label for the counter.</div>
<p class="lede" style="margin-top:10px"><span class="legend"><span><i class="tl g"></i>Green ≥ €150/UIO or a signed fact</span> <span><i class="tl a"></i>Amber — incomplete or watch</span> <span><i class="tl r"></i>Red — material gap on a signed definition</span> <span><i class="tl" style="background:#6b6256"></i>Grey — UNKNOWN</span></span></p>
"""))

    # --- 3 GPS ---
    pages.append(page(3, "Wallet", "Network wallet and GPS",
        "CY2025 the hub captured €30.76M of a €60.22M max-spend ceiling (51.1%); three distributors hold most of the euro still below that ceiling.",
        f"""
<p class="lede">Spend per unit on the GPS traffic light is green in 15 of 18 markets with parc. That is not the same as filling the ceiling: ITUK is green at €249/unit and still sits at 32.4% of its theoretical wallet — the largest euro pool below the ceiling.</p>
<div class="chartbox">
  <div class="chartttl">Euros still below the GPS ceiling concentrate in three distributors · CY2025</div>
  {wallet_bars}
  <div class="chart-wrap"><canvas id="cWallet" aria-hidden="true"></canvas></div>
</div>
<div class="chartbox">
  <div class="chartttl">Spend per unit is green across most of the parc; Hungary, UK LCV and Greece are amber · CY2025</div>
  {gps_spu}
  <div class="chart-wrap"><canvas id="cGps" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="callout amber"><b>UMI warranty distorts the green light.</b> Headline spend per unit is €179 (green). Strip warranty parts and it is €82 (red). Always read UMI as a pair.</div>
  <div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Ukraine, Armenia, Kazakhstan and Palestine bill parts but have no GPS parc in this league — omitted, not zero. MIDI is not an ISZE customer row here. 2026 YTD spend per unit is half a year against a full-year parc — it is not a traffic light.</div>
</div>
<p class="lede">2026 year-to-date parts billed in the 18 GPS markets: <b>€8.76M</b> through {BILLING_MAX}. That is a stub, not a run-rate.</p>
"""))

    # --- 4 Capture ---
    pages.append(page(4, "Workshop basket", "Capture — what the service schedule still misses",
        "On the IML service schedule the UK truck oil-filter cover is 35.1% (UIO 22,389); the five-category revenue gap is €2.04M, and air plus wear — not oil — hold most of it.",
        f"""
<p class="lede">This page’s worked example is the IML service schedule signed for UK truck correspondence: filters at 1.25 services per year, clutch and brake at 0.5, addressable 100%, parc 22,389. Actual oil-filter units 9,818 versus 27,986 expected.</p>
<div class="grid2">
  <div class="chartbox">
    <div class="chartttl">Cover on the IML service schedule is a workshop gap, not a saturated filter book · CY2025</div>
    {iml_cover}
  </div>
  <div class="chartbox">
    <div class="chartttl">Air and wear hold the euro: €736k air, €642k brake, €393k clutch · CY2025</div>
    {iml_gap}
    <div class="chart-wrap"><canvas id="cImlGap" aria-hidden="true"></canvas></div>
  </div>
</div>
<table>
  <thead><tr><th>Category</th><th class="n">Cover</th><th class="n">Gap €</th><th class="n">Actual units</th></tr></thead>
  <tbody>
    <tr><td>Oil filter</td><td class="n">35.1%</td><td class="n">140,602</td><td class="n">9,818</td></tr>
    <tr><td>Fuel filter</td><td class="n">65.1%</td><td class="n">127,440</td><td class="n">18,228</td></tr>
    <tr><td>Air filter</td><td class="n">13.2%</td><td class="n">736,037</td><td class="n">3,692</td></tr>
    <tr><td>Clutch</td><td class="n">7.8%</td><td class="n">392,559</td><td class="n">411</td></tr>
    <tr><td>Brake</td><td class="n">35.3%</td><td class="n">641,833</td><td class="n">3,953</td></tr>
    <tr><td><b>Five categories</b></td><td class="n"><b>35.9% wtd</b></td><td class="n"><b>2,038,471</b></td><td class="n">—</td></tr>
  </tbody>
</table>
<div class="callout amber"><b>Network-comparable ranking uses a different denominator</b> (bucketed parc 23,068 for the UK truck row; shared service factors across distributors). On that ranking UK truck oil-filter total is above 100% uncapped — valid when actuals include sales beyond the truck-only proxy. It is <b>not</b> the 35.1% above. Ireland’s uncapped 191% is why this paper does not plot a “best market” series.</div>
<div class="chartbox">
  <div class="chartttl">Network-comparable oil-filter total (capped display) — for ranking only, not the IML story · CY2025</div>
  {pms_net}
  <div class="chart-wrap"><canvas id="cPms" aria-hidden="true"></canvas></div>
</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Jobs not sold through the dealer. Independent-garage units. Air-filter interval on the network-comparable view is a provisional 0.5 factor until IML confirms the ratio. Category comparison on that view is directional only.</div>
"""))

    # --- 5 Mix ---
    pages.append(page(5, "Quality", "Mix — quality of what was sold, not capture",
        "Of the €30.76M captured in CY2025, 96.5% is genuine and 3.5% is BVP (€1.06M) — mix sits two orders of magnitude below the euro still outside the wallet ceiling.",
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
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Gross-profit given up to down-trade is a modelled extra, not a GPS headline. This page quotes mix of billed euros, which is signed. Do not add mix “loss” to the €29.5M below-ceiling pool — different questions.</div>
"""))

    # --- 6 League ---
    pages.append(page(6, "League", "Distributor league — GPS, workshop cover, mix",
        "Read three columns together: spend per unit, network-comparable oil-filter total, and genuine mix — and keep UTI, UMI, ITUK and IUK as four different rows.",
        """
<table>
  <thead>
    <tr><th>Distributor</th><th class="n">GPS €/UIO</th><th>Light</th><th class="n">Wallet GPS%</th><th class="n">Oil-filter total*</th><th class="n">Genuine mix</th></tr>
  </thead>
  <tbody>
    <tr><td>Ireland</td><td class="n">389</td><td><i class="tl g"></i>Green</td><td class="n">124.2%</td><td class="n">100% cap</td><td class="n">95.5%</td></tr>
    <tr><td>UTI (Israel)</td><td class="n">322</td><td><i class="tl g"></i>Green</td><td class="n">40.3%</td><td class="n">91%</td><td class="n">88.9%</td></tr>
    <tr><td>ITUK (UK truck)</td><td class="n">249</td><td><i class="tl g"></i>Green</td><td class="n">32.4%</td><td class="n">100% cap</td><td class="n">97.3%</td></tr>
    <tr><td>Belgium</td><td class="n">220</td><td><i class="tl g"></i>Green</td><td class="n">86.0%</td><td class="n">63%</td><td class="n">96.6%</td></tr>
    <tr><td>Portugal</td><td class="n">209</td><td><i class="tl g"></i>Green</td><td class="n">56.0%</td><td class="n">52%</td><td class="n">94.0%</td></tr>
    <tr><td>Germany</td><td class="n">197</td><td><i class="tl g"></i>Green</td><td class="n">66.6%</td><td class="n">15%</td><td class="n">99.3%</td></tr>
    <tr><td>UMI (Israel)</td><td class="n">179</td><td><i class="tl g"></i>Green†</td><td class="n">71.6%</td><td class="n">85%</td><td class="n">96.3%</td></tr>
    <tr><td>Norway</td><td class="n">179</td><td><i class="tl g"></i>Green</td><td class="n">71.5%</td><td class="n">48%</td><td class="n">98.2%</td></tr>
    <tr><td>Sweden</td><td class="n">151</td><td><i class="tl g"></i>Green</td><td class="n">60.6%</td><td class="n">49%</td><td class="n">99.9%</td></tr>
    <tr><td>Greece</td><td class="n">139</td><td><i class="tl a"></i>Amber</td><td class="n">54.6%</td><td class="n">97%</td><td class="n">92.2%</td></tr>
    <tr><td>IUK (UK LCV)</td><td class="n">128</td><td><i class="tl a"></i>Amber</td><td class="n">51.3%</td><td class="n">38%</td><td class="n">99.1%</td></tr>
    <tr><td>Hungary</td><td class="n">88</td><td><i class="tl a"></i>Amber</td><td class="n">35.4%</td><td class="n">45%</td><td class="n">96.6%</td></tr>
  </tbody>
</table>
<p class="lede">*Oil-filter total is the <b>network-comparable</b> rate (capped at 100% for display). ITUK’s 35.1% IML figure is the worked example on page 4 — do not substitute it into this column. †UMI ex-warranty spend per unit is €82.</p>
<div class="callout amber">Ireland’s wallet GPS above 100% means billed parts exceeded the max-spend ceiling — over-target, not a data bug. Germany’s 15% oil-filter total on the shared denominator is the weak workshop row in this league, despite a green spend-per-unit.</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> No “Israel” average. No IUK+ITUK blend. CIS rows without parc stay off this table.</div>
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

    # --- 8 Price ---
    pages.append(page(8, "Price", "Price versus reference sell-out — evidence, not share",
        "Aftermarket price evidence exists, but it covers well under 15% of billed euros in almost every market — so this paper will not headline “we are X% versus independent.”",
        f"""
<p class="lede">Reference sell-out = list × <b>1.785</b> (distributor +40%, then dealer +27.5%). Price index = shop ÷ that reference. Scrapes (UK workshop basket 2023; DE/NO online basket March 2026) are <b>price</b>, not volume.</p>
<div class="chartbox">
  <div class="chartttl">The 2023 UK workshop basket covers 1–17% of each distributor’s CY2025 billed euro — too thin to be a market</div>
  {price_cov}
  <div class="chart-wrap"><canvas id="cPrice" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>What we can say</h3>
    <p>38 unique part numbers carry a 2023 UK independent workshop purchase price. A newer 44-line DE/NO online basket is dated 29 March 2026 — a different vintage, still a thin sample. Where shop sits below reference sell-out, the counter arithmetic is against genuine. That is a price fact on those lines.</p>
  </div>
  <div class="unk-panel">
    <span class="unk-tag">UNKNOWN</span>
    Independent-garage <b>unit volume</b>. Coverage of billed euro is 12.6% at ITUK, 3.0% at UTI, 1.0% at UMI, 17.1% at Denmark (the high). Below ~15% we do not say “the aftermarket is X% of the book.” Dealer sell-out longs exist only for ITUK, IUK, Ireland, UTI and Greece — elsewhere the hole is a missing file, not 0%.
  </div>
</div>
<div class="callout">A pocket gap between list and net billed <b>exists</b> as an internal question. The euro is <b>not signed</b> for external quote (decision board, ask 1). It is not a hero on this page.</div>
"""))

    # --- 9 Demand ---
    pages.append(page(9, "Operations", "Demand, replenishment, forecast honesty",
        "Replenishment exceptions are an operational fact on the five distributors that have dealer sell-out; the forecast surface is real (median WAPE 49.4% on 548 series) and is not a signed live forecast.",
        f"""
<p class="lede">Sell-out files exist for ITUK, IUK, Ireland, UTI and Greece. Everywhere else, “no exception” would mean “no file,” not a clean pipeline. Greece in particular carries a heavy billed-without-sell-out pile — treat that market’s sell-out as partial.</p>
<div class="chartbox">
  <div class="chartttl">1,595 CY2025 exception rows sit on five distributors only — the rest of the network is a source gap</div>
  {repl}
  <div class="chart-wrap"><canvas id="cRepl" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>Forecast surface (not go-live)</h3>
    <p>548 series back-tested. Median WAPE <b>49.4%</b>. Catalogue list coverage cited for a go-live gate is 98.2%. Gate G1 is <b>unsigned</b>. Override policy (who may change a forecast) is also unsigned. This is a surface the room can inspect — not a number to put in a live allocation.</p>
  </div>
  <div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Realised euros past the billing horizon. Growth-factor 1.24 / 1.25 still unsigned (inherits into any forecast that uses it). Book B cannot become a price move until alloc ambition is named (+4% / +5% / launch-only).</div>
</div>
<div class="callout amber">Do not read 2026 year-to-date as a decline versus CY2025. Capture-trend alerts that treated a stub year as a full year were a known false cliff; complete-year declining pairs still on the books: Ireland clutch kit, ITUK brake rotor, Romania brake rotor, Romania clutch kit, UTI clutch kit (five, not thirty-three).</div>
"""))

    # --- 10 Tenders ---
    pages.append(page(10, "Public volume", "Public tenders — portal coverage, not credentials",
        "The live notice feed is real (226 opportunities in the last published cut) and systematically incomplete below the EU threshold; Nordics national feeds are live — the remaining gap is portals, not keys.",
        f"""
<p class="lede">Notice count is not fleet potential and not award euro. Most notices in the cut have no extractable value (248 of 249 raw rows flagged missing value). Do not celebrate a small vehicle extract as market size.</p>
<div class="chartbox">
  <div class="chartttl">The EU above-threshold feed still supplies most rows; national sources add France, Germany, Poland — Spain is not in this cut</div>
  {tenders}
  <div class="chart-wrap"><canvas id="cTender" aria-hidden="true"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <h3>Footprint (29 countries)</h3>
    <p>A 25 August 2026 portal map lists <b>16 live</b> national (or UK) sources, <b>2 code-ready</b> (Spain still blocked by a web firewall; Lithuania needs a portal key we do not chase here), remainder national-dark — TED or equivalent only below threshold. Nordics (Norway, Finland) are live.</p>
  </div>
  <div class="unk-panel"><span class="unk-tag">UNKNOWN</span> Award euros. Below-threshold volume in dark countries. Israel domestic IEC from a non-IL address. This paper does not invent a tender wallet.</div>
</div>
<div class="callout good">Credentials for the Nordic national APIs are done. The commercial conversation is which national portals to wire next (Spain is the ready fetcher behind a firewall), not a setup sheet.</div>
"""))

    # --- 11 Integrity ---
    pages.append(page(11, "Holes", "Data integrity and first-class UNKNOWNs",
        "The books are green (116 pass / 0 fail) and still carry labelled holes: independent unit volume, unsigned pocket euros, a provisional air interval, an unsigned forecast, and sell-out files on only five distributors.",
        """
<table>
  <thead><tr><th>Hole</th><th>What we know</th><th>What we do not</th></tr></thead>
  <tbody>
    <tr><td>Independent volume</td><td>Price baskets exist (38 PN 2023 UK; 44 PN Mar 2026 DE/NO)</td><td>Unit share. Residual of PMS is not IAM.</td></tr>
    <tr><td>List-to-pocket</td><td>A pocket gap exists as an internal question</td><td>A signed euro for this room</td></tr>
    <tr><td>Air interval</td><td>Network-comparable air uses a 0.5 factor so categories are directional</td><td>IML-confirmed ratio</td></tr>
    <tr><td>UK truck brake factor</td><td>0.4 is applied on the network-comparable path</td><td>Whether 0.8 is the right wear rate</td></tr>
    <tr><td>Sell-out files</td><td>ITUK, IUK, Ireland, UTI, Greece</td><td>Every other GPS market — source gap, not 0%</td></tr>
    <tr><td>2026 Apr–Jun credits</td><td>Quarter is in the fact table through 30 Jun</td><td>Sales-type codes on that extract (sign-based exclusion only)</td></tr>
    <tr><td>UMI GPS</td><td>€179/unit including warranty; €82 without</td><td>How the room wants the headline framed</td></tr>
    <tr><td>LCV intervals</td><td>Schedules on disk (15k km with SCR, 20k without)</td><td>Chassis / registration-year cutoffs to weight the parc</td></tr>
    <tr><td>Forecast G1</td><td>Surface live, WAPE 49.4%, 548 series</td><td>Go-live signature and override policy</td></tr>
    <tr><td>CIS / MIDI</td><td>Bill or warranty may exist</td><td>GPS league rows (by design, not missing files)</td></tr>
  </tbody>
</table>
<div class="callout amber">Credit and return lines on positive value were excluded from GPS and PMS as a documented judgment — not an ERP-confirmed netting rule. If the next extract with sales-type codes reverses the call, GPS and capture move. That is reversible on purpose.</div>
<div class="unk-panel"><span class="unk-tag">UNKNOWN</span> This panel is the product. Smoothing a hole into a chart is how a Grade A paper becomes Grade D.</div>
"""))

    # --- 12 SWOT S/W ---
    pages.append(page(12, "SWOT · internal", "Strengths and weaknesses — ISZE aftersales",
        "Strengths are a green book and a genuine-heavy mix; weaknesses are a €2.04M UK-truck service gap on the IML schedule, a €29.5M pool still below the GPS ceiling, and unsigned pocket and forecast gates.",
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
        "Spend per unit is green in 15 of 18 GPS markets with parc.",
        "Ireland €389 · UTI €322 · ITUK €249 per unit CY2025 (green ≥ €150).",
        "2026 YTD spend-per-unit is a stub year. UMI green €179 becomes €82 without warranty.",
        "A decision to traffic-light UMI on the ex-warranty number in every pack.")}
    {cell(
        "Dealer sell-out exists where it exists — five distributors, not a blank network.",
        "ITUK dealer sell-out CY2025 €11.0M at the counter versus €5.56M ISZE→DB billed (same parc).",
        "Most GPS markets have no sell-out file. Greece sell-out looks partial (heavy billed-without-sell-out).",
        "One additional large-market sell-out long.")}
  </div>
  <div class="swot-q">
    <h3>Weaknesses</h3>
    {cell(
        "UK truck workshop cover on the IML service schedule is 35.1% oil-filter.",
        "UIO 22,389 · 9,818 actual vs 27,986 expected · five-category gap €2.04M (air €736k, brake €642k, clutch €393k).",
        "Independent jobs not in the dealer. This 35.1% is not the network-comparable 100% cap / 116% raw.",
        "One family of independent unit counts on oil or air.")}
    {cell(
        "Half the theoretical wallet still sits outside captured sales.",
        "€29.46M below a €60.22M CY2025 ceiling (51.1% GPS). ITUK + IUK + UTI hold most of that euro. Ceiling = max-spend, not a forecast.",
        "That residual is not independent-garage share.",
        "A signed split of residual into lost service / IAM / DIY / other-OEM — we do not have it.")}
    {cell(
        "Realization (list-to-pocket) is not signed for this room.",
        "Existence of a pocket gap: named. Euro: not quoted.",
        "The unsigned euro itself.",
        "Written sign-off on year-matched list-to-net joins.")}
    {cell(
        "The forecast cannot go live on current signatures.",
        "Median WAPE 49.4% on 548 series · G1 unsigned · override policy unsigned.",
        "Realised euros past 30 June 2026.",
        "G1 yes/no and who may change a forecast.")}
  </div>
</div>
"""))

    # --- 13 SWOT O/T ---
    pages.append(page(13, "SWOT · external", "Opportunities and threats — still sourced or UNKNOWN",
        "The named euro opportunities are the IML-schedule air and wear gaps and a revision pack that cannot move price until alloc ambition is set; the named threat is independent price evidence without independent volume.",
        f"""
<div class="swot">
  <div class="swot-q">
    <h3>Opportunities</h3>
    {cell(
        "Air and wear on the IML UK-truck schedule are the largest named gaps.",
        "Air €736k · brake €642k · clutch €393k of the €2.04M. Fuel is already 65.1% cover.",
        "Air interval on the network-comparable view still provisional. Brake 0.4 vs 0.8 still open.",
        "IML air-ratio confirmation and a locked brake wear factor.")}
    {cell(
        "A revision pack is built and waiting for an ambition, not for more analysis.",
        "Book B × guardrail overlay exists (review list, not a price move). Alloc +4% / +5% / launch-only is unsigned.",
        "Which ambition the room wants. Seed euros for no-L12M part numbers similarly unsigned.",
        "Ask B1 on the decision board — one number.")}
    {cell(
        "National tender portals still to wire, with Spain already coded.",
        "16 of 29 footprint countries live nationally; Spain fetcher ready behind a firewall. Live cut: 226 opportunities, 18 due in 14 days.",
        "Award euro. Below-threshold volume in dark countries.",
        "Spain firewall path, then the next dark national — not a credential chase.")}
    {cell(
        "OEM-peer retail coverage can be completed on the billed book.",
        "Today 1–17% of billed euro joins a priced independent line. Reference sell-out formula is agreed (×1.785).",
        "Unit volume even after prices fill.",
        "Price coverage on a material share of billed euro — still not an IAM %.")}
  </div>
  <div class="swot-q">
    <h3>Threats</h3>
    {cell(
        "Independent price at the counter undercuts reference sell-out on a thin basket.",
        "38 PN (2023 UK workshop) · 44 PN (Mar 2026 DE/NO online). Coverage too thin to be share.",
        "Independent unit volume. Vintage mix if Mode A files stay unlabelled (ask B10).",
        "One family of independent unit counts, or honest vintage labels on every Mode A price file.")}
    {cell(
        "Calling residual PMS “independent share” would steer the room at the wrong enemy.",
        "Network GPS residual vs ceiling €29.46M · IML UK-truck residual vs schedule €2.04M. Different questions.",
        "The true IAM split of either residual.",
        "Any IAM % invented from 100% − PMS — refuse it.")}
    {cell(
        "Interval error can move capture without a single extra sale.",
        "Air 0.5 provisional · UK-truck brake 0.4 applied vs 0.8 still argued. LCV 15k vs 20k km needs chassis cutoffs.",
        "The locked IML ratios for air and LCV parc weights.",
        "Asks on air ratio, brake factor (B9), LCV cutoffs.")}
    {cell(
        "ICE Golden Window (2025–2032) is time-bounded; a new composite score will not extend it.",
        "Stance: peak ICE D-Max / N-series parts window is open now. Scoring 0–100 is closed.",
        "Exact year of peak by market.",
        "Parc cohort by market — not a revived score.")}
  </div>
</div>
"""))

    # --- 14 Asks ---
    pages.append(page(14, "90 days", "Five asks already on the table",
        "Nothing here is a new programme — these five are waiting on a named answer; without them revision stays a list, forecast stays a surface, and realization stays internal.",
        """
<div class="ask"><div class="no">1</div><div>
  <h3>Sign list-to-pocket — or keep realization internal</h3>
  <p>Year-matched list-to-net joins ran as validation. Until there is a written sign-off, this paper will not quote the pocket euro. <b>No answer:</b> Mode A packs stay silent on realization; the internal question does not disappear.</p>
</div></div>
<div class="ask"><div class="no">2</div><div>
  <h3>G1 — sign the forecast surface, or wait</h3>
  <p>98.2% catalogue coverage is the cited gate. Median WAPE 49.4% (548 series) is already on the table. <b>No answer:</b> forecast cannot go live; allocation cannot inherit it. A separate ask still sits behind G1: who may override, with an audit trail.</p>
</div></div>
<div class="ask"><div class="no">3</div><div>
  <h3>Book B alloc ambition — +4% / +5% / launch-only</h3>
  <p>The revision pack is a review list until this number exists. <b>No answer:</b> no DB-specific list move, no ranked alloc, no “we will fix price” claim that survives contact with the guardrails.</p>
</div></div>
<div class="ask"><div class="no">4</div><div>
  <h3>UK truck brake wear — 0.4 or 0.8</h3>
  <p>0.4 is applied on the network-comparable path and is not locked as the IML story. <b>No answer:</b> do not quote UK-truck brake cover as settled. (Air 0.5 on the comparable view is the sibling interval ask, still provisional.)</p>
</div></div>
<div class="ask"><div class="no">5</div><div>
  <h3>Account-health thresholds — calibrate before it is a call list</h3>
  <p>Draft flags already fire on most of the book (10 red / 6 amber of 17 distributors on the last snapshot). <b>No answer:</b> that queue is not a call list. Early warning on sales stays the call list until amber/red are signed.</p>
</div></div>
<div class="unk-panel"><span class="unk-tag">NOT AN ASK</span> Nordic tender API keys — done. Gross/SPA on billing — closed, net-only forever. A new 0–100 score — closed. This paper is not added to the build queue as a programme.</div>
<p class="lede">Also waiting, not in the five: seed euros for no-recent-sales part numbers; growth-factor 1.24/1.25; auto-HOLD on independent-undercut; competitor vintage labels on Mode A files; approved route for company text; shared mailbox works-council step; DPO path. One answer each, already written down.</p>
"""))

    # --- 15 Falsifiers ---
    pages.append(page(15, "Disagree well", "What would change our mind",
        "These are the smallest facts that would rewrite the thesis — not moving goalposts.",
        """
<ol style="padding-left:18px;max-width:92ch">
  <li style="margin-bottom:8px"><b>One family of independent unit counts</b> (oil filter or air, one large market). Would let us retire “IAM volume UNKNOWN” and stop treating residual PMS as a mystery blend.</li>
  <li style="margin-bottom:8px"><b>Written list-to-pocket sign-off</b> on year-matched joins. Would move realization from “exists, unsigned” to a Mode A euro — or kill the figure if the join fails.</li>
  <li style="margin-bottom:8px"><b>G1 on the forecast surface</b> (or an explicit wait). Would turn WAPE 49.4% from a honesty footnote into either a live input or a parked prototype.</li>
  <li style="margin-bottom:8px"><b>IML air-interval confirmation</b> replacing the provisional 0.5 on the network-comparable view. Would make air vs oil cover comparable without a caveat.</li>
  <li style="margin-bottom:8px"><b>UK-truck brake 0.4 vs 0.8 locked</b>. Would make brake cover quotable on the comparable path.</li>
  <li style="margin-bottom:8px"><b>One more large-market dealer sell-out long</b> (Germany or Belgium would change the replenishment story). Would prove whether billed-without-sell-out is a Greece/file problem or a network pattern.</li>
  <li style="margin-bottom:8px"><b>Next SAP extract with sales-type codes for Apr–Jun 2026</b>. Would confirm or reverse the credit/return judgment on that quarter.</li>
  <li style="margin-bottom:8px"><b>UMI ex-warranty as the default GPS headline</b> in this room. Would recast UMI from green €179 to red €82 without any new data.</li>
</ol>
<div class="callout">If none of these arrive, the thesis on page 1 still holds: we locate about half the ceiling, the UK-truck IML gap is €2.04M, independent volume is UNKNOWN, and five named decisions are the bottleneck — not another score, not another analysis pass.</div>
"""))

    # --- 16 Sources ---
    pages.append(page(16, "Audit", "Sources, as-of, verify stamp",
        f"Verify is green: {VERIFY_PASS} pass / {VERIFY_FAIL} fail at {VERIFY_AT}; billing through {BILLING_MAX}; filenames live on this page only.",
        f"""
<table class="src">
  <thead><tr><th>Claim in this paper</th><th>Definition / grain</th><th>Where</th></tr></thead>
  <tbody>
    <tr><td>51.1% · €30.76M / €60.22M</td><td>GPS captured vs max-spend ceiling, CY2025, 18 GPS markets</td><td>metrics snapshot · wallet waterfall</td></tr>
    <tr><td>35.1% · €2.04M · UIO 22,389</td><td>IML service schedule, UK truck, CY2025, 5 categories</td><td>Apr 2026 PMS analysis / IML constants (FACTS §1)</td></tr>
    <tr><td>Oil-filter total 116% raw / 100% cap</td><td>Network-comparable, UK truck, UIO 23,068 — ranking only</td><td>PMS capture by distributor × year</td></tr>
    <tr><td>96.5% genuine mix</td><td>Captured genuine ÷ captured total, CY2025</td><td>wallet waterfall (ITUK 97.3% also in snapshot)</td></tr>
    <tr><td>GPS €/UIO league</td><td>Net parts ÷ parc; green ≥ €150</td><td>GPS spend-per-unit by distributor</td></tr>
    <tr><td>€8.76M 2026 YTD</td><td>18 GPS markets, Jan–{BILLING_MAX}, not annualised</td><td>same GPS file, year 2026</td></tr>
    <tr><td>Dealer scores</td><td>Points vs country mean; Israel = UMI only</td><td>IDS 2026 dealer network extract</td></tr>
    <tr><td>Price coverage 1–17%</td><td>2023 UK workshop basket ∩ CY2025 billed euro</td><td>Eucon UK 2023 price-gap meta</td></tr>
    <tr><td>WAPE 49.4%</td><td>548 series, unsigned G1</td><td>forecast baseline meta (P5.2/P5.6)</td></tr>
    <tr><td>226 opportunities</td><td>Last published tender cut 25 Aug 2026</td><td>tender feed JSON</td></tr>
    <tr><td>16 / 29 national live</td><td>Portal map 25 Aug 2026 (not award €)</td><td>country tender portals map</td></tr>
    <tr><td>1,595 replenishment rows</td><td>CY2025, five DBs with sell-out only</td><td>replenishment exceptions</td></tr>
    <tr><td>Shell €520k UMI</td><td>Fiscal 2025, 5500* lubricants, excluded from pure GPS</td><td>GPS pure-sales extract</td></tr>
    <tr><td>Five declining pairs</td><td>Complete years only (stub year excluded from slope)</td><td>capture trajectory</td></tr>
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
    <p>Pages 1, 4 (worked example), 12, 14 — IML service schedule 35.1% / €2.04M / 22,389.<br>
    Pages 4 (ranking bars), 6 — network-comparable oil-filter total, different denominator.<br>
    Never shown as one number without that split.</p>
  </div>
</div>
<p class="lede">Open this file with the sibling launcher <kbd>OPEN_ISZE_Exec_Aftersales_Paper.cmd</kbd> (Windows) or <kbd>OPEN_ISZE_Exec_Aftersales_Paper.sh</kbd>. Double-click paints without a server; charts are CSS bars plus inline Chart.js (no CDN).</p>
"""))

    js_boot = r"""
(function(){
  if (typeof Chart === 'undefined') return;
  const ink = '#15233c', terr = '#c0552d', grid = '#e6e2d8';
  Chart.defaults.font.family = 'Segoe UI, Helvetica, Arial, sans-serif';
  Chart.defaults.font.size = 10;
  Chart.defaults.color = '#52514e';
  function bar(id, labels, data, colors){
    const el = document.getElementById(id);
    if (!el) return;
    new Chart(el, {type:'bar', data:{labels:labels, datasets:[{data:data, backgroundColor:colors, borderWidth:0}]},
      options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
        scales:{x:{ticks:{maxRotation:50, autoSkip:false}, grid:{display:false}},
                y:{grid:{color:grid}, beginAtZero:true}}}});
  }
  bar('cWallet', ['ITUK','IUK','UTI','PT','UMI','DE','HU','NO'],
      [11.61,5.81,4.94,1.34,1.32,1.27,0.60,0.57],
      [terr,terr,terr,'#8a6a4a','#8a6a4a','#8a6a4a','#8a6a4a','#8a6a4a']);
  bar('cGps', ['IE','UTI','ITUK','FI','BE','PT','DE','UMI','NO','SE','GR','IUK','HU'],
      [389,322,249,231,220,209,197,179,179,151,139,128,88],
      ['#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c48a16','#c48a16']);
  bar('cImlGap', ['Air','Brake','Clutch','Oil','Fuel'], [736,642,393,141,127],
      ['#c0453c',terr,terr,'#8a6a4a','#8a6a4a']);
  bar('cPms', ['IE','ITUK','GR','UTI','CY','UMI','BE','PT','SE','IUK','HU','DE'],
      [100,100,97,91,91,85,63,52,49,38,45,15],
      ['#6b7c93','#6b7c93','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c48a16','#c48a16','#c0453c','#c48a16','#c0453c']);
  bar('cMix', ['UTI','CY','GR','PT','IE','UMI','BE','ITUK','IUK','DE','SE'],
      [11.1,8.5,7.8,6.0,4.5,3.7,3.4,2.7,0.9,0.7,0.1],
      [terr,terr,terr,'#c48a16','#c48a16',ink,'#2b4a78','#2b4a78','#1d9e75','#1d9e75','#1d9e75']);
  bar('cIds', ['MT','PT','HU','PL','UK CV','UK LCV','LU','RO','BE','NL','DK','NO','GR','IL UMI'],
      [89.3,86.9,86.2,84.1,83.8,81.7,80,79.6,78.6,76.3,75.7,75.2,73.9,60.9],
      ['#1d9e75','#1d9e75','#1d9e75','#1d9e75','#2b4a78','#2b4a78','#2b4a78','#2b4a78','#c48a16','#c48a16','#c48a16','#c48a16','#c48a16','#c0453c']);
  bar('cPrice', ['DK','HU','SE','ITUK','NO','IE','GR','BE','DE','UTI','UMI'],
      [17.1,13.3,13.0,12.6,12.3,10.3,10.2,6.3,6.4,3.0,1.0],
      ['#c48a16','#c0453c','#c0453c','#c0453c','#c0453c','#c0453c','#c0453c','#6b6256','#6b6256','#6b6256','#6b6256']);
  bar('cRepl', ['No sell-out','High ST','No bill','Low ST'], [500,400,380,315],
      [terr,'#c48a16','#2b4a78','#8a6a4a']);
  bar('cTender', ['EU','DE','FR','PL','BE','IL','IT','UK'], [159,41,20,16,6,5,1,1],
      ['#2b4a78','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c48a16']);
})();
"""

    html = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\"/>\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>\n"
        "<title>ISZE aftersales — where the wallet sits</title>\n"
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
    for bad in ("street", "iml v7", "model b", "prism lane", "jerome"):
        if bad in low:
            raise SystemExit(f"forbidden token in HTML: {bad}")
    if "cdn.jsdelivr" in low or "cdnjs.cloudflare" in low:
        raise SystemExit("CDN Chart.js forbidden")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes) pages={html.count('paper-page')}")


if __name__ == "__main__":
    main()
