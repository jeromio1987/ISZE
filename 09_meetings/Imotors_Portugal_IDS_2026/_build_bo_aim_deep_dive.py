# -*- coding: utf-8 -*-
from pathlib import Path
import csv, json, html as H

base = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imotors_bo_compare_20261006\IMOTORS_BO_AIM_ANALYSIS_20261006")
out_dir = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026")
html_path = out_dir / "IMotors_BO_AIM_Deep_Dive_20261006.html"
cmd_path = out_dir / "OPEN_IMotors_BO_AIM_Deep_Dive.cmd"

summary = json.loads((base / "summary.json").read_text(encoding="utf-8"))
l1 = list(csv.DictReader((base / "by_aim_l1.csv").open(encoding="utf-8")))
l2 = list(csv.DictReader((base / "by_aim_l1_l2.csv").open(encoding="utf-8")))
pn = list(csv.DictReader((base / "top_pn_by_eur.csv").open(encoding="utf-8")))
age = list(csv.DictReader((base / "age_band_by_aim_l1.csv").open(encoding="utf-8")))

def eur(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def fmt_eur(x):
    v = eur(x)
    return f"€{v:,.0f}" if abs(v) >= 1000 else f"€{v:,.2f}"

def pct(x):
    return f"{eur(x) * 100:.1f}%"

total_eur = eur(summary.get("eur_amount_total") or sum(eur(r["eur_amount"]) for r in l1))
saty = summary.get("saty") or {}
saty_eur = {"SOR": 107132, "RUSH": 25552, "VOR": 22005}

def bars(rows, label_key, value_key, max_n=12, color="#c0552d"):
    rows = sorted(rows, key=lambda r: -eur(r[value_key]))[:max_n]
    mx = max((eur(r[value_key]) for r in rows), default=1) or 1
    parts = []
    for r in rows:
        w = 100 * eur(r[value_key]) / mx
        lab = H.escape(str(r[label_key]))
        parts.append(
            f'<div class="bar-row"><div class="bar-lab">{lab}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{w:.1f}%;background:{color}"></div></div>'
            f'<div class="bar-val">{fmt_eur(r[value_key])}</div></div>'
        )
    return "\n".join(parts)

l1_bars = bars([{**r, "label": r["aim_l1"]} for r in l1], "label", "eur_amount", 8, "#1a2b4a")
l2_rows = [{**r, "label": f"{r['aim_l1']} · {r['aim_l2']}"} for r in l2[:14]]
l2_bars = bars(l2_rows, "label", "eur_amount", 14, "#c0552d")
comp_eur = sum(eur(r["eur_amount"]) for r in l2 if r["aim_l1"] == "Competitive parts")

bands = ["0-7", "8-14", "15-30", "31-60"]
fams = ["Competitive parts", "Repair parts", "Accident parts", "High value repair"]
age_map = {(r["age_band"], r["aim_l1"]): eur(r["eur_amount"]) for r in age}
age_cells = []
for fam in fams:
    cells = "".join(
        f'<td class="heat" data-v="{age_map.get((b, fam), 0):.0f}">{fmt_eur(age_map.get((b, fam), 0))}</td>'
        for b in bands
    )
    age_cells.append(f"<tr><th>{H.escape(fam)}</th>{cells}</tr>")

pn_rows_html = []
for i, r in enumerate(pn[:30], 1):
    saty_raw = r.get("saty") or ""
    pn_rows_html.append(
        "<tr>"
        f'<td class="num">{i}</td>'
        f'<td class="mono">{H.escape(r["pn"])}</td>'
        f"<td>{H.escape(r['desc'])}</td>"
        f"<td>{H.escape(r['aim_l1'])}<div class=\"sub\">{H.escape(r['aim_l2'])}</div></td>"
        f'<td class="num">{fmt_eur(r["eur_amount"])}</td>'
        f'<td class="num">{H.escape(str(int(float(r["qty"]))))}</td>'
        f'<td class="num">{H.escape(r["lines"])}</td>'
        f'<td class="num">{H.escape(r["oldest_days"])}d</td>'
        f'<td class="mono small">{H.escape(saty_raw)}</td>'
        "</tr>"
    )

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>I-Motors open orders × AIM — deep dive 6 Oct 2026</title>
<style>
:root {{
  --ink:#1a2332; --muted:#5c6b7a; --paper:#f6f3ee; --card:#fff;
  --navy:#15233c; --terra:#c0552d; --line:#d9d2c5; --ok:#2f6b4f; --warn:#a66b1a; --bad:#9b2c2c;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans:"Segoe UI",system-ui,-apple-system,sans-serif;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.55 var(--sans); }}
.wrap {{ max-width:1180px; margin:0 auto; padding:28px 22px 80px; }}
header.hero {{
  background:linear-gradient(145deg,#15233c 0%,#243b5c 55%,#3a2a22 100%);
  color:#f7f4ee; border-radius:18px; padding:34px 34px 28px; margin-bottom:28px;
  box-shadow:0 18px 40px rgba(21,35,60,.22);
}}
header.hero .kicker {{ letter-spacing:.12em; text-transform:uppercase; font-size:11px; opacity:.75; }}
header.hero h1 {{ font-family:var(--serif); font-weight:600; font-size:clamp(1.7rem,3vw,2.35rem); margin:10px 0 12px; line-height:1.15; }}
header.hero .lede {{ font-size:1.05rem; max-width:62ch; opacity:.92; }}
.meta {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }}
.chip {{ background:rgba(247,244,238,.1); border:1px solid rgba(247,244,238,.22); padding:6px 10px; border-radius:999px; font-size:12px; }}
.grid {{ display:grid; gap:16px; }}
.g4 {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
.g2 {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
@media (max-width:900px) {{ .g4,.g2 {{ grid-template-columns:1fr; }} }}
.kpi {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 16px 14px; }}
.kpi .lbl {{ font-size:11px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }}
.kpi .val {{ font-family:var(--serif); font-size:1.85rem; margin-top:4px; }}
.kpi .note {{ font-size:12px; color:var(--muted); margin-top:6px; }}
.kpi.warn {{ border-color:#e2c089; background:#fff9ef; }}
.kpi.bad {{ border-color:#e2b0b0; background:#fff5f5; }}
.kpi.ok {{ border-color:#b7d3c3; background:#f3faf6; }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:22px 22px 18px; margin:18px 0; }}
section h2 {{ font-family:var(--serif); font-size:1.45rem; margin:0 0 8px; color:var(--navy); }}
section h3 {{ font-size:1.02rem; margin:18px 0 8px; color:var(--navy); }}
.prose {{ max-width:75ch; }}
.prose p {{ margin:0 0 12px; }}
.callout {{ border-left:4px solid var(--terra); background:#faf6f2; padding:12px 14px; border-radius:0 10px 10px 0; margin:14px 0; }}
.callout.navy {{ border-left-color:var(--navy); background:#f3f6fa; }}
.callout.bad {{ border-left-color:var(--bad); background:#fff5f5; }}
.callout.ok {{ border-left-color:var(--ok); background:#f3faf6; }}
.bar-row {{ display:grid; grid-template-columns:220px 1fr 72px; gap:10px; align-items:center; margin:6px 0; }}
@media (max-width:700px) {{ .bar-row {{ grid-template-columns:1fr; gap:2px; }} }}
.bar-lab {{ font-size:12.5px; color:var(--ink); }}
.bar-track {{ background:#ece7de; height:12px; border-radius:999px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:999px; }}
.bar-val {{ font-variant-numeric:tabular-nums; font-size:12.5px; text-align:right; color:var(--muted); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:8px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
th {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:#f7f4ee; background:var(--navy); }}
tbody tr:nth-child(even) {{ background:#faf8f4; }}
.num {{ font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }}
.mono {{ font-family:Consolas,"Courier New",monospace; font-size:12px; }}
.small {{ font-size:11px; color:var(--muted); }}
.sub {{ font-size:11px; color:var(--muted); }}
.heat {{ text-align:right; font-variant-numeric:tabular-nums; }}
.toc {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 0; }}
.toc a {{ color:var(--navy); text-decoration:none; background:#eef2f7; border:1px solid #d5deea; padding:6px 10px; border-radius:999px; font-size:12px; }}
.toc a:hover {{ background:#e2eaf4; }}
.two-col {{ display:grid; grid-template-columns:1.2fr .8fr; gap:18px; }}
@media (max-width:900px) {{ .two-col {{ grid-template-columns:1fr; }} }}
ul.tight {{ margin:8px 0 0 18px; padding:0; }}
ul.tight li {{ margin:6px 0; }}
.footer {{ color:var(--muted); font-size:12px; margin-top:28px; line-height:1.45; }}
.tag {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:6px; background:#eef2f7; color:var(--navy); }}
.tag.terra {{ background:#f6e6dc; color:#8a3a1a; }}
.tag.bad {{ background:#f8e0e0; color:#7a2222; }}
.tag.ok {{ background:#dff0e6; color:#21553a; }}
</style>
</head>
<body>
<div class="wrap">
<header class="hero">
  <div class="kicker">I-Motors · Portugal · internal deep dive · 6 Oct 2026</div>
  <h1>September open orders are young, competitive-heavy, and not the same thing as their 495 back-order lines</h1>
  <p class="lede">We have a full AIM cut of our open sales-order book to I-Motors (sold-to 519). Their KPI only gives a monthly back-order <em>count</em>. That is why a PN-level match is still missing — and why Lisbon should open on definitions before it opens on blame.</p>
  <div class="meta">
    <span class="chip">Our open book: 906 lines · €154.7k · 745 PNs</span>
    <span class="chip">Their KPI B/O Sep: 495 lines (was 282 in Aug)</span>
    <span class="chip">Fill rate to dealers: 85.4% Aug → 81.0% Sep</span>
    <span class="chip">AIM: catalogue families (Competitive / Repair / Accident / High value)</span>
  </div>
</header>

<nav class="toc" aria-label="Sections">
  <a href="#verdict">Verdict</a>
  <a href="#compare">495 vs 906</a>
  <a href="#anatomy">Open-book anatomy</a>
  <a href="#aim">AIM families</a>
  <a href="#money">Money parts</a>
  <a href="#age">Age × family</a>
  <a href="#story">What it means</a>
  <a href="#ask">Wednesday asks</a>
  <a href="#method">Method</a>
</nav>

<section id="verdict">
  <h2>1. Verdict</h2>
  <div class="prose">
    <p>I-Motors’ September fill-rate drop and the jump in back-order lines sit next to an ISZE open-order book that is almost entirely <strong>September-created</strong>, median age <strong>21 days</strong>, oldest line <strong>35 days</strong>. This is not a cemetery of ancient back orders. It is a fresh availability stress: thin stock (MOS still under 3.0) meeting a September rebound in sales to dealers (€417k vs €304k in August).</p>
    <p>On our side, <strong>45% of the open euro</strong> is Competitive parts — exhaust, brakes, filters, steering, suspension. That is the same commercial surface as SPA and price talks. Exhaust / emissions alone (DPD, EGR, NOx, DEF) is loud. VOR is only 92 lines but holds the expensive workshop stoppers (partial engine, cylinder heads, turbos).</p>
  </div>
  <div class="callout bad">
    <strong>Hard limit:</strong> Nuno’s KPI sheet has no part numbers. Until Astara sends a PN-level back-order extract (or we file an IMOTORS BO OVERVIEW), we cannot prove which of their 495 misses are our supply gap versus their warehouse.
  </div>
</section>

<div class="grid g4" style="margin:18px 0">
  <div class="kpi"><div class="lbl">Our open EUR</div><div class="val">{fmt_eur(total_eur)}</div><div class="note">Sold-to 519 · EXPORT 6 Oct</div></div>
  <div class="kpi"><div class="lbl">Open lines / PNs</div><div class="val">906<span style="font-size:1rem;color:#5c6b7a"> / 745</span></div><div class="note">All created Sep 2026</div></div>
  <div class="kpi warn"><div class="lbl">Their B/O lines (KPI)</div><div class="val">495</div><div class="note">Aug was 282 · first-fill misses</div></div>
  <div class="kpi bad"><div class="lbl">Fill rate to dealers</div><div class="val">81.0%</div><div class="note">Aug 85.4% · target 85%</div></div>
</div>

<section id="compare">
  <h2>2. Why 495 and 906 must not be subtracted</h2>
  <div class="two-col">
    <div class="prose">
      <p>Two numbers that look comparable and are not:</p>
      <ul class="tight">
        <li><strong>Their 495</strong> — KPI “B/O lines”: dealer order lines that were not immediately and fully allocated from I-Motors stock (first fill). Monthly count. No PN.</li>
        <li><strong>Our 906</strong> — open sales-document lines from I-Motors to ISZE that have not closed yet. Has PN, qty, euro, SaTy, create date.</li>
      </ul>
      <p>A dealer miss can be: (a) I-Motors warehouse empty while we have stock in Belgium, (b) we also have no stock and an open order, (c) a superseded / wrong PN, (d) a timing cut-off. Without their PN list we are guessing which bucket.</p>
      <div class="callout navy">For Lisbon: agree the definition first, then ask for the top 20 aged lines behind the 495. Only then compare to our open book.</div>
    </div>
    <div>
      <h3>What we can already say</h3>
      <table>
        <thead><tr><th>Signal</th><th>Read</th></tr></thead>
        <tbody>
          <tr><td>MOS 2.49 (Sep)</td><td>Still under 3.0 target while sales to dealers bounced</td></tr>
          <tr><td>B/O 282 → 495</td><td>Availability broke with demand rebound</td></tr>
          <tr><td>Our book all Sep</td><td>Problem is recent intake / cover, not old dirt</td></tr>
          <tr><td>Fill 81%</td><td>Below 85% target after August looked fine</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section id="anatomy">
  <h2>3. Anatomy of our open book</h2>
  <div class="grid g2">
    <div>
      <h3>By order type (SaTy)</h3>
      <table>
        <thead><tr><th>Type</th><th class="num">Lines</th><th class="num">EUR</th><th class="num">Share €</th></tr></thead>
        <tbody>
          <tr><td>SOR <span class="tag">stock / normal</span></td><td class="num">{saty.get('SOR',658)}</td><td class="num">{fmt_eur(saty_eur['SOR'])}</td><td class="num">{pct(saty_eur['SOR']/total_eur)}</td></tr>
          <tr><td>RUSH</td><td class="num">{saty.get('RUSH',156)}</td><td class="num">{fmt_eur(saty_eur['RUSH'])}</td><td class="num">{pct(saty_eur['RUSH']/total_eur)}</td></tr>
          <tr><td>VOR <span class="tag terra">vehicle off road</span></td><td class="num">{saty.get('VOR',92)}</td><td class="num">{fmt_eur(saty_eur['VOR'])}</td><td class="num">{pct(saty_eur['VOR']/total_eur)}</td></tr>
        </tbody>
      </table>
      <p class="small" style="margin-top:10px">VOR is 10% of lines but 14% of euro — and holds the partial engine and heads. That is the workshop-stopper layer.</p>
    </div>
    <div>
      <h3>Age of open lines (as of 6 Oct)</h3>
      <table>
        <thead><tr><th>Band</th><th class="num">Meaning</th></tr></thead>
        <tbody>
          <tr><td>Min / median / p90 / max</td><td class="num">6 / 21 / 33 / 35 days</td></tr>
          <tr><td>Created month</td><td class="num">100% September 2026</td></tr>
        </tbody>
      </table>
      <div class="callout ok" style="margin-top:14px">
        If this were a multi-quarter BO pile, ages would stretch past 90–180 days. They do not. The fight is September cover and September demand.
      </div>
    </div>
  </div>
</section>

<section id="aim">
  <h2>4. AIM families — where the euro sits</h2>
  <p class="prose">Catalogue AIM (Competitive / Repair / Accident / High value). This is the commercial cut for pricing and SPA — not the technical workbook axis (Engine / Intake Exhaust…).</p>
  <h3>Level 1</h3>
  <div class="bar-chart">{l1_bars}</div>
  <div class="grid g4" style="margin-top:16px">
    <div class="kpi"><div class="lbl">Competitive</div><div class="val">{pct(0.4477)}</div><div class="note">{fmt_eur(69256.55)} · wear &amp; service</div></div>
    <div class="kpi"><div class="lbl">Repair</div><div class="val">{pct(0.1861)}</div><div class="note">{fmt_eur(28789.9)} · engine / sensors</div></div>
    <div class="kpi"><div class="lbl">Accident</div><div class="val">{pct(0.1774)}</div><div class="note">{fmt_eur(27437.17)} · body / lighting</div></div>
    <div class="kpi"><div class="lbl">High value repair</div><div class="val">{pct(0.1239)}</div><div class="note">{fmt_eur(19164.13)} · turbo / inj / gearbox</div></div>
  </div>
  <h3>Level 2 — the money list</h3>
  <div class="bar-chart">{l2_bars}</div>
  <div class="callout">
    <strong>Commercial read:</strong> Competitive alone is {fmt_eur(comp_eur)}. Inside it, exhaust + brakes + filters are more than a third of the whole open book. That is exactly the basket where a short SPA wave (with I-Motors passing price to dealers) can move volume — but only if the parts are on the shelf.
  </div>
</section>

<section id="money">
  <h2>5. Money parts — top 30 by open euro</h2>
  <p class="prose">Use this as the Wednesday shortlist. Ask which of these are also on their 495, and which are warehouse-only misses on their side.</p>
  <div style="overflow:auto">
  <table>
    <thead>
      <tr>
        <th>#</th><th>PN</th><th>Part</th><th>AIM</th><th class="num">EUR</th><th class="num">Qty</th><th class="num">Lines</th><th class="num">Age</th><th>SaTy</th>
      </tr>
    </thead>
    <tbody>
      {''.join(pn_rows_html)}
    </tbody>
  </table>
  </div>
  <h3>Patterns in the top of the list</h3>
  <ul class="tight prose">
    <li><strong>Workshop stoppers:</strong> partial engine (€4.4k VOR), cylinder heads (€2.5k VOR), turbos (€3.3k + VOR lines), injectors (€3.3k).</li>
    <li><strong>Exhaust / emissions cluster:</strong> DPD, EGR coolers/valves, NOx sensor, DEF pump/tank — many SOR lines aged 30+ days.</li>
    <li><strong>Volume wear:</strong> oil filter element 220 pcs / €1.0k; fuel filter kit 144 pcs; brake pad kits — classic competitive cover items.</li>
    <li><strong>Filing note:</strong> two cylinder-block lines sit under Accident / Body in the catalogue cut — treat as AIM filing noise when you talk “body”; they are engine hardware in the room.</li>
  </ul>
</section>

<section id="age">
  <h2>6. Age × family — where the wait is</h2>
  <p class="prose">Euro still open by age band and AIM L1. Competitive parts dominate every band from 8 days upward — including the 31–60 day pocket (€21.6k).</p>
  <div style="overflow:auto">
  <table>
    <thead><tr><th>Family</th><th class="num">0–7d</th><th class="num">8–14d</th><th class="num">15–30d</th><th class="num">31–60d</th></tr></thead>
    <tbody>
      {''.join(age_cells)}
    </tbody>
  </table>
  </div>
  <div class="callout navy">
    The 31–60 day Competitive pocket is the “September early intake still open” layer — steering unit, DPD, pad kits, oil filters. That is the list to clear first if you want fill rate back to 85% without rebuilding blind stock.
  </div>
</section>

<section id="story">
  <h2>7. What this means for the trip</h2>
  <div class="two-col">
    <div class="prose">
      <h3>At the three dealers</h3>
      <p>You still cannot allocate these euros to Rolmax / Auto Reno / Socarros. The dealer walk stays qualitative on availability:</p>
      <ul class="tight">
        <li>When I-Motors is out — wait, buy outside, or substitute? How often last month?</li>
        <li>Which families leave first (filters / brakes / exhaust)?</li>
        <li>Multi-site stock (Auto Reno): who holds what?</li>
      </ul>
      <p>Floor answers become the story that makes the Wednesday PN ask unavoidable.</p>
    </div>
    <div class="prose">
      <h3>At I-Motors Lisbon</h3>
      <ul class="tight">
        <li>Sep fill 81% + B/O 495 + MOS 2.49 is one mechanism: thin stock × demand rebound.</li>
        <li>Our open book says the euro is Competitive + exhaust/brakes/filters + a VOR engine layer.</li>
        <li>Do not accept “stock is fine because August fill was 85%.” August is stale.</li>
        <li>GPS locked figure for the trip stays <strong>63.3%</strong> — separate from this availability story.</li>
      </ul>
    </div>
  </div>
</section>

<section id="ask">
  <h2>8. Force decisions on Wednesday</h2>
  <ol class="prose">
    <li><strong>PN extract for the 495</strong> — invoice/order date, PN, qty, age, dealer if they have it. Without this, IDS visits cannot connect to parts euros.</li>
    <li><strong>Top 20 aged lines</strong> behind Sep fill 81% — mark each: ISZE open / I-Motors warehouse only / superseded.</li>
    <li><strong>Stock floor</strong> — when does MOS get back to 3.0 without killing fill rate again? Which competitive families get the first reorder wave?</li>
    <li><strong>SPA candidates</strong> — exhaust / brakes / filters / steering from this open book: which ones will they pass to dealers if ISZE moves price for a period?</li>
    <li><strong>VOR stoppers</strong> — partial engine + heads + turbos: ETA and escalation path before the dealer visits end.</li>
  </ol>
</section>

<section id="method">
  <h2>9. Method &amp; sources</h2>
  <table>
    <thead><tr><th>Input</th><th>Role</th></tr></thead>
    <tbody>
      <tr><td>EXPORT.XLSX (self-mail “Order”, 6 Oct 09:32)</td><td>ISZE open sales orders; filter sold-to <span class="mono">519</span> IMOTORS</td></tr>
      <tr><td>Nuno KPI check sheet Aug–Sep (1 Oct)</td><td>Fill rate, MOS, B/O line counts, sales to dealers €</td></tr>
      <tr><td>aim_pn_classification_release_2026-10-04.csv</td><td>Catalogue AIM L1/L2 for commercial cut</td></tr>
      <tr><td>I-Motors PN-level BO OVERVIEW</td><td><span class="tag bad">missing</span> — blocks true match</td></tr>
    </tbody>
  </table>
  <p class="small" style="margin-top:12px">Analysis folder: <span class="mono">01_data\\90_INBOX\\_imotors_bo_compare_20261006\\IMOTORS_BO_AIM_ANALYSIS_20261006\\</span></p>
</section>

<p class="footer">Internal / private. GPS Capture for the Portugal trip remains the locked meeting figure 63.3%. This page does not replace the IDS dealer fiches; it arms the availability and AIM conversation for Lisbon.</p>
</div>
<script>
(function(){{
  const cells=[...document.querySelectorAll('td.heat')];
  const vals=cells.map(c=>+c.dataset.v||0);
  const mx=Math.max(...vals,1);
  cells.forEach(c=>{{
    const v=+c.dataset.v||0;
    const t=v/mx;
    c.style.background='rgba(192,85,45,'+(0.08+0.55*t)+')';
    if(t>0.55) c.style.color='#fff';
  }});
}})();
</script>
</body>
</html>
"""

html_path.write_text(doc, encoding="utf-8")
cmd_path.write_bytes(b'@echo off\r\nstart "" "%~dp0IMotors_BO_AIM_Deep_Dive_20261006.html"\r\n')
print("HTML", html_path, html_path.stat().st_size)
print("CMD CRLF", b"\r\n" in cmd_path.read_bytes())
print("bar-row", doc.count("bar-row"))
print("table rows", doc.count("<tr>"))
