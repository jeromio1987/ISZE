# -*- coding: utf-8 -*-
"""Portugal thin visit pack — questions first, part examples for intel. Sources only."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]

BRIEF_KPI = {
    "jul": {"fill": "83.6%", "mos": "2.62", "bo": "279", "std": "€393k", "stock": "€544k"},
    "aug": {"fill": "85.4%", "mos": "2.20", "bo": "282", "std": "€304k", "stock": "€504k"},
    "sep": {"fill": "81.0%", "mos": "2.49", "bo": "495", "std": "€417k", "stock": "€499k"},
}

# Example parts for intel prompts (from competitive shortlist / PMS gaps — not a full catalogue)
PART_EXAMPLES = [
    ("Front brake pads", "8975056801 / 8982447940", "Brakes — price vs independent?"),
    ("Front brake disc", "8982488951", "Brakes — stock / wait / buy outside?"),
    ("Clutch kit", "5876102060", "Clutch — kits vs pieces; who wins the job?"),
    ("Clutch disc", "8982120690", "Clutch — genuine vs AM / Chinese?"),
    ("Air filter", "5876150021", "Filters — shelf at I-Motors or outside?"),
    ("Fuel filter", "8982399830", "Filters — customer price story"),
    ("Radiator", "8983355671", "Cooling — where do they buy when slow?"),
    ("DPD / DPF can", "8981776324", "Emission — new / clean / exchange?"),
]

CSS = """
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#cfc8bc;--muted:#5a6570;}
*{box-sizing:border-box}
body{margin:0;font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);background:var(--paper);}
h1,h2,h3{font-family:Georgia,serif;color:var(--navy);margin:0 0 .4rem}
.page{max-width:900px;margin:0 auto;padding:16px 18px 36px}
.banner{background:var(--navy);color:#f7f4ee;padding:12px 14px;margin-bottom:12px}
.banner h1{color:#f7f4ee;font-size:1.25rem}
.banner .meta{opacity:.9;font-size:.88rem;margin-top:3px}
.section{background:#fff;border:1px solid var(--line);padding:11px 13px;margin:10px 0}
.section h2{font-size:1.02rem;border-bottom:2px solid var(--terra);padding-bottom:3px;margin-bottom:8px}
.q{margin:7px 0;padding:8px 10px;background:var(--paper);border-left:3px solid var(--navy)}
.q .n{font-weight:700;color:var(--terra);margin-right:6px}
.q .why{font-size:.82rem;color:var(--muted);margin-top:2px}
.ex{font-size:.82rem;color:var(--navy);margin-top:4px;padding:4px 6px;background:#eef2f7;border:1px solid #d5dde8}
.blank{border:1px dashed var(--line);min-height:34px;background:#fff;margin-top:4px}
.zero{display:grid;grid-template-columns:1fr auto auto auto auto;gap:3px 6px;align-items:center;font-size:.85rem;margin:3px 0}
.zero .code{font-family:ui-monospace,Consolas,monospace;font-size:.78rem;color:var(--navy)}
.mark{display:inline-block;width:13px;height:13px;border:1.5px solid var(--navy);vertical-align:middle;margin-right:2px}
.legend{font-size:.78rem;color:var(--muted);margin:4px 0 8px}
.do-not{background:#f8e8e2;border:1px solid #e0b8a8;padding:7px 9px;font-size:.86rem;margin:6px 0}
.do-not strong{color:var(--terra)}
table{width:100%;border-collapse:collapse;font-size:.84rem}
th,td{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}
th{background:var(--navy);color:#f7f4ee}
tr:nth-child(even) td{background:#faf8f4}
.foot{font-size:.75rem;color:var(--muted);margin-top:14px;border-top:1px solid var(--line);padding-top:7px}
.kaizen{display:grid;grid-template-columns:2fr 1fr 1fr;gap:5px;margin-top:5px}
.kaizen input{border:1px solid var(--line);padding:5px;width:100%}
.intel-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media print{
  body{background:#fff}
  .page{max-width:none;padding:0}
  .section,.banner{break-inside:avoid}
}
@media (max-width:700px){.intel-grid{grid-template-columns:1fr}}
"""

DPD = [
    ("When a D-Max DPD fails, what do you do today — new OE, aftermarket, or off-car cleaning?",
     "Maps the real path before any programme talk."),
    ("What do you (or the customer) typically pay for cleaning or exchange, all-in?",
     "COLLECT one euro figure — do not invent."),
    ("Would you send a sealed can to a FR hub (2–3 day turnaround) if collection/return were arranged?",
     "Yes / no / only if € X."),
    ("What downtime can the workshop accept before they just fit a new unit?",
     "Is 24–72h usable?"),
    ("Who cleans DPFs locally in PT / ES border, if anyone?",
     "Name of cleaner / city."),
]


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def q_block(n: str, ask: str, why: str = "", example: str = "") -> str:
    bits = [f'<div class="q"><span class="n">{esc(n)}</span>{esc(ask)}']
    if why:
        bits.append(f'<div class="why">{esc(why)}</div>')
    if example:
        bits.append(f'<div class="ex">Example parts to probe: {esc(example)}</div>')
    bits.append('<div class="blank"></div></div>')
    return "".join(bits)


DEALERS = {
    "ROLMAX": {
        "file": "WALK_ROLMAX.html",
        "title": "Rolmax — questions + intel",
        "when": "Mon afternoon · Vila Nova de Gaia / Porto",
        "ids": "90.7%",
        "assessed": "2026-04-29",
        "nuno": "good",
        "angle": "Good dealer calibration. Still lose wear/filters? Do they sell R&M?",
        "zeros": [
            ("C.4-20", "Workshop volume reported to distributor?"),
            ("A.3-2", "Name badge at reception"),
            ("A.2-4", "Aftersales promo (service contract / health report)"),
            ("B.5-11", "AED"),
            ("C.1-19 / C.1-20", "Service van + 24/7 roadside"),
            ("D.2-16", "R&M / extended warranty offer"),
        ],
        "intel_extra": [
            ("R1", "Do you get Allianz roadside jobs? How often last month?",
             "Same Allianz story Luís wrote for network steering."),
            ("R2", "Do you sell R&M / extended warranty, or only when the customer asks?",
             "IDS zero D.2-16."),
            ("R3", "On front pads / discs / clutch — who wins the job when the customer wants cheaper?",
             "Probe: pad 8975056801, disc 8982488951, clutch kit 5876102060."),
        ],
    },
    "AUTO_RENO": {
        "file": "WALK_AUTO_RENO_PACOS_FERREIRA.html",
        "title": "Auto Reno Paços — questions + intel",
        "when": "Tue morning · Paços de Ferreira",
        "ids": "96.1%",
        "assessed": "2026-04-07",
        "nuno": "average (IDS = top of Portugal)",
        "angle": "High form score vs Nuno “average”. Multi-site stock is the intel.",
        "zeros": [
            ("C.4-20", "Workshop volume to distributor"),
            ("A.1-22", "24/7 contact"),
            ("B.5-11", "AED"),
            ("B.6-5", "Customer S-classification in database"),
            ("C.1-19 / C.1-20", "Van + roadside"),
            ("D.1-10", "Outside-hours parts delivery"),
        ],
        "intel_extra": [
            ("A1", "Where does stock really sit — Paços, Penafiel, Minho? Who decides?",
             "Central warehouse vs site stock."),
            ("A2", "Why does Nuno call you “average” if IDS is top of Portugal?",
             "Ask Nuno privately if needed — volume / loyalty / genuine mix?"),
            ("A3", "When I-Motors is slow on filters or brakes, which site orders outside?",
             "Probe: air filter 5876150021, fuel filter 8982399830, pads 8975056801."),
        ],
    },
    "SOCARROS": {
        "file": "WALK_SOCARROS_CALDAS.html",
        "title": "Socarros Caldas — questions + intel",
        "when": "Tue afternoon · Caldas da Rainha",
        "ids": "82.1%",
        "assessed": "2026-04-30",
        "nuno": "weaker stop",
        "angle": "Weakest IDS. Best place to hear why genuine share is hard.",
        "zeros": [
            ("A.1-8…11 / A.1-22", "Reception / premises / 24/7 contact"),
            ("B.1-2", "Local UIO used for parts + service planning?"),
            ("B.5-1 / B.5-11", "Fire clearance / AED"),
            ("C.1-19 / C.1-20", "Van + roadside"),
            ("D.1-10", "Outside-hours parts access"),
            ("E.1-5", "Lead response time tracking"),
        ],
        "intel_extra": [
            ("S1", "Which part families do you lose to independents / Chinese?",
             "Name families: filters, pads, clutch, body…"),
            ("S2", "Is I-Motors delivery or price the usual reason?",
             "One clear answer."),
            ("S3", "On clutch / brake shoe / pads — what does the customer pay outside vs here?",
             "Probe: clutch kit 5876102060, pads 8975056801, disc 8982488951."),
        ],
    },
}


def walk_html(d: dict) -> str:
    # Shared commercial intel questions FIRST
    commercial = [
        q_block("Q1", "How are parts and service sales this year vs last? What moved?",
                "Intel: up/down and why (fleet / price / stock)."),
        q_block("Q2", "Are your customer prices competitive vs independent / Chinese / OEM peer?",
                "On which families?",
                "Front pads, discs, clutch kit, air/fuel filter, radiator — see pocket list below."),
        q_block("Q3", "How is cooperation with I-Motors (stock, delivery, returns, training, price support)?",
                "What should Astara unlock for you?"),
        q_block("Q4", "Where do you get parts when I-Motors is slow or expensive?",
                "Honest answer = the GPS / genuine-share story.",
                "Name the brand / channel if they say it."),
        q_block("Q5", "Central warehouse / multi-site: stock here, or pull from another site?",
                "Who decides what you hold?"),
        q_block("Q6", "When a part is not on the shelf at I-Motors — wait, buy outside, or substitute? How often last month?",
                "Fill-rate probe for Wednesday (Sep fill 81%).",
                "Ask on: pads, discs, clutch, filters, DPD."),
    ]
    extras = [q_block(n, ask, why) for n, ask, why in d["intel_extra"]]
    dpd = [q_block(f"DPD{i}", a, w) for i, (a, w) in enumerate(DPD, 1)]
    zeros = []
    for code, label in d["zeros"]:
        zeros.append(
            f'<div class="zero"><div><span class="code">{esc(code)}</span> — {esc(label)}</div>'
            f'<label><span class="mark"></span>OK</label>'
            f'<label><span class="mark"></span>Fixed</label>'
            f'<label><span class="mark"></span>Open</label>'
            f'<label><span class="mark"></span>n/a</label></div>'
        )
    ex_rows = "".join(
        f"<tr><td>{esc(name)}</td><td><code>{esc(pn)}</code></td><td>{esc(hint)}</td>"
        f'<td class="blank" style="min-width:120px"></td></tr>'
        for name, pn, hint in PART_EXAMPLES
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(d['title'])}</title>
<style>{CSS}</style></head><body>
<div class="page">
  <div class="banner">
    <h1>{esc(d['title'])}</h1>
    <div class="meta">{esc(d['when'])} · IDS {esc(d['ids'])} · assessed {esc(d['assessed'])} · Nuno: {esc(d['nuno'])}</div>
    <div class="meta">{esc(d['angle'])}</div>
  </div>

  <div class="section">
    <h2>1. Commercial intel (same six everywhere — compare answers)</h2>
    <p class="legend">Write what they say. Part numbers below are prompts only — not an accusation list.</p>
    {''.join(commercial)}
  </div>

  <div class="section">
    <h2>2. This dealer — extra intel</h2>
    {''.join(extras)}
  </div>

  <div class="section">
    <h2>3. Pocket part examples — gather what they do</h2>
    <p class="legend">For each: genuine / AM / Chinese / wait? Rough customer € if they say it. Leave blank if unknown.</p>
    <table>
      <thead><tr><th>Part (words)</th><th>Example PN</th><th>Ask</th><th>Your note</th></tr></thead>
      <tbody>{ex_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>4. DPD / DPF interest (Peter — interest only)</h2>
    <div class="do-not"><strong>Do not:</strong> promise a programme or a price · mix ITUK truck new-in-lieu into pickup talk · invent euros.</div>
    {''.join(dpd)}
    <p class="legend">One-line report: today path / rough € / FR hub yes-no / max downtime / local cleaner.</p>
  </div>

  <div class="section">
    <h2>5. IDS zeros (walk only — do not re-score the form)</h2>
    <div class="legend"><span class="mark"></span>OK &nbsp; Fixed since April &nbsp; Still open &nbsp; n/a</div>
    {''.join(zeros)}
  </div>

  <div class="section">
    <h2>6. Close</h2>
    <p><b>Max 3 Kaizen</b></p>
    <div class="kaizen"><div>Action</div><div>Owner</div><div>Date</div>
      <input><input><input><input><input><input><input><input><input>
    </div>
    <p style="margin-top:8px"><b>One sentence for Wednesday — what Astara must unlock:</b></p>
    <div class="blank" style="min-height:44px"></div>
    <p style="margin-top:8px"><b>Intel worth repeating in Lisbon:</b></p>
    <div class="blank" style="min-height:44px"></div>
  </div>

  <div class="foot">Internal · Oct 2026 Portugal visit · GPS locked 63.3% · Sources: visit brief, IDS fiche, DPD case study, competitive shortlist examples. No dealer-grain sales-to-dealer euros — do not invent.</div>
</div>
</body></html>
"""


def wednesday_html(pms_rows: list, spa_unique: list) -> str:
    k = BRIEF_KPI
    pms_ex = "".join(
        f"<tr><td>{esc(r.get('label') or r['pms_category'])}</td>"
        f"<td>{r.get('capture_pct')}%</td><td>€{(r.get('revenue_gap_eur') or 0):,.0f}</td></tr>"
        for r in pms_rows[:6]
    )
    spa_ex = "".join(
        f"<tr><td>{esc(r['pn'])}</td><td>{esc(r['description'])}</td>"
        f"<td>€{r['db_revenue_cy_eur']:,.0f}</td></tr>"
        for r in spa_unique[:8]
    )
    part_ex = "".join(
        f"<tr><td>{esc(n)}</td><td><code>{esc(pn)}</code></td><td>{esc(h)}</td></tr>"
        for n, pn, h in PART_EXAMPLES
    )
    qs = [
        q_block("1", "Sep fill 81% vs Aug 85.4% — which part numbers / families drove the miss?",
                "Ask for top 20 by back-order age.",
                "Start families: brakes, clutch, filters, DPD, body."),
        q_block("2", "Back-order lines 495 (was 282) — temporary catch-up or structural under-stock?",
                "When does MOS get back to 3.0 without killing fill again?"),
        q_block("3", "Sales-to-dealer monthly feed — go-live date + columns?",
                "Need: invoice date, PN, qty; dealer code if they have it. Without dealer grain IDS visits cannot link to euros."),
        q_block("4", "GPS 63.3% / PMS ~32% — do you accept these as the working FY figures?",
                "Locked trip figure for GPS; PMS from ledger CY2025."),
        q_block("5", "Lubricants — status of central purchasing / Shell path?",
                "One status line."),
        q_block("6", "SPA — which part families will you propose for volume?",
                "ISZE support examples on SPA_ASK_SHORTLIST.html — not a closed deal.",
                "Clutch, brake pads/shoes, filters, DPD; see pocket PNs."),
        q_block("7", "Luís — which of REN / IP / Lisbon / Madeira / Arval still needs an ISZE parts decision?",
                "Plus: named case for optional year-3 cover; who owns tender early-warning to ISZE?"),
        q_block("8", "IDS network Kaizen — C.4-20 workshop reporting, roadside/Allianz, AED: I-Motors standard or dealer-only?",
                "Bring floor notes from the three dealers."),
    ]
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Wednesday — questions for I-Motors / Astara</title>
<style>{CSS}</style></head><body>
<div class="page">
  <div class="banner">
    <h1>Wednesday — questions for I-Motors / Astara</h1>
    <div class="meta">Nuno + Luís · Lisbon · Force answers, not a tour · GPS locked <b>63.3%</b></div>
  </div>

  <div class="section">
    <h2>Sep context (Nuno KPI — use in Q1–Q2, not as the meeting)</h2>
    <table>
      <thead><tr><th>Month</th><th>First fill</th><th>MOS</th><th>BO lines</th><th>Sales to dealers</th><th>Stock</th></tr></thead>
      <tbody>
        <tr><td>Jul</td><td>{k['jul']['fill']}</td><td>{k['jul']['mos']}</td><td>{k['jul']['bo']}</td><td>{k['jul']['std']}</td><td>{k['jul']['stock']}</td></tr>
        <tr><td>Aug</td><td><b>{k['aug']['fill']}</b></td><td>{k['aug']['mos']}</td><td>{k['aug']['bo']}</td><td>{k['aug']['std']}</td><td>{k['aug']['stock']}</td></tr>
        <tr><td>Sep</td><td><b>{k['sep']['fill']}</b></td><td>{k['sep']['mos']}</td><td><b>{k['sep']['bo']}</b></td><td>{k['sep']['std']}</td><td>{k['sep']['stock']}</td></tr>
      </tbody>
    </table>
    <p class="legend">Sep broke fill while sales to dealers rebounded (€417k vs €304k Aug). Thin stock story.</p>
  </div>

  <div class="section">
    <h2>Force questions</h2>
    {''.join(qs)}
  </div>

  <div class="section">
    <h2>Pocket part / family examples (for the SPA + fill conversation)</h2>
    <table>
      <thead><tr><th>Part</th><th>Example PN</th><th>Why ask</th></tr></thead>
      <tbody>{part_ex}</tbody>
    </table>
    <p class="legend">Full ask list: SPA_ASK_SHORTLIST.html in this folder.</p>
  </div>

  <div class="section intel-grid">
    <div>
      <h2>PMS gaps (CY2025 — euros)</h2>
      <p class="legend">Capture 32.4% · gap €774k. Use as “which families?” not a lecture.</p>
      <table><thead><tr><th>Family</th><th>Capture</th><th>Gap €</th></tr></thead>
      <tbody>{pms_ex}</tbody></table>
    </div>
    <div>
      <h2>SPA support examples (CY billed)</h2>
      <p class="legend">Astara still to propose. AM prices mostly not PT shops.</p>
      <table><thead><tr><th>PN</th><th>Part</th><th>CY €</th></tr></thead>
      <tbody>{spa_ex}</tbody></table>
    </div>
  </div>

  <div class="section">
    <h2>Luís R&amp;M / tenders — confirm</h2>
    <p>200+ tender units 2026: Lisbon 29 NLR · Madeira 4 NPR · IP 96 D-Max · REN 15 D-Max + service · CV year-3 by I-Motors · Arval developing. Allianz roadside → network workshops.</p>
    <div class="blank" style="min-height:50px"></div>
  </div>

  <div class="section">
    <h2>July still open (tick)</h2>
    <label><span class="mark"></span> Clutch kits vs parts</label><br>
    <label><span class="mark"></span> Obsolete stock list</label><br>
    <label><span class="mark"></span> EDI capabilities</label><br>
    <label><span class="mark"></span> BCS F-series brackets</label><br>
    <label><span class="mark"></span> Aftersales hours questionnaire</label>
  </div>

  <div class="section">
    <h2>Leave Lisbon with</h2>
    {q_block("A", "Dated sales-to-dealer feed commitment OR named blocker")}
    {q_block("B", "Named R&M / tender next step")}
    {q_block("C", "SPA families Astara will propose")}
    {q_block("D", "Dealer-floor intel to act on (from Mon–Tue notes)")}
  </div>

  <div class="foot">Sources: visit brief · Nuno Sep KPI · NUMBERS_LEDGER PMS/SPA · Luís 2 Oct · July minutes. Detail: SPA_ASK_SHORTLIST.html</div>
</div>
</body></html>
"""


def spa_shortlist_html(shortlist, near_miss, spa_unique, pms_rows) -> str:
    rows = "".join(
        f"<tr><td>{esc(r['pn'])}</td><td>{esc(r.get('description',''))}</td>"
        f"<td>{esc(r.get('aim_l1','') or '')}</td>"
        f"<td>€{float(r.get('std_list_lost') or 0):,.0f}</td>"
        f"<td>{float(r.get('index_ref_vs_am_median') or 0):.2f}</td></tr>"
        for r in shortlist
    )
    nm = "".join(
        f"<tr><td>{esc(r.get('pn',''))}</td><td>{esc(r.get('description',''))}</td>"
        f"<td>{esc(r.get('aim_l1','') or '')}</td>"
        f"<td>€{float(r.get('std_list_lost') or 0):,.0f}</td></tr>"
        for r in near_miss[:10]
    )
    spa = "".join(
        f"<tr><td>{esc(r['pn'])}</td><td>{esc(r['description'])}</td>"
        f"<td>€{r['db_revenue_cy_eur']:,.0f}</td><td>{r.get('delta_pct','')}%</td></tr>"
        for r in spa_unique
    )
    pms = "".join(
        f"<tr><td>{esc(r.get('label') or r['pms_category'])}</td>"
        f"<td>{r.get('capture_pct')}%</td><td>€{(r.get('revenue_gap_eur') or 0):,.0f}</td></tr>"
        for r in pms_rows[:8]
    )
    asks = [
        q_block("S1", "Which families will Astara propose for SPA volume?",
                "Clutch, brake pad/shoe, filters, DPD, body…"),
        q_block("S2", "Can you table Portuguese workshop / dealer buy prices on the top lines?",
                "AM probes on file are mostly DE/NO/UK — not PT."),
        q_block("S3", "Which of these 26 are already on SPA or special terms today?",
                "Collect yes/no per family if not per PN."),
        q_block("S4", "On near-miss lines with no AM price (exhaust pipe, DEF tank, DPD, EGR…) — do dealers buy outside?",
                "Intel from Mon–Tue floors."),
    ]
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>SPA ask — questions + example parts</title>
<style>{CSS}</style></head><body>
<div class="page">
  <div class="banner">
    <h1>SPA ask — questions + example parts</h1>
    <div class="meta">Ask list for Astara · not a closed deal · PT shop prices mostly missing</div>
  </div>
  <div class="do-not"><strong>Honesty:</strong> AM brand prices cover ~32% of competitive StD list €. Reference dealer = list × 1.40 × 1.275. List € lost ≠ proven lost to AM alone.</div>

  <div class="section">
    <h2>Questions first</h2>
    {''.join(asks)}
  </div>

  <div class="section">
    <h2>Example parts — dropping and expensive vs AM (26)</h2>
    <p class="legend">Combined list € lost on hits €13,805. Use as conversation examples.</p>
    <table><thead><tr><th>PN</th><th>Part</th><th>Family</th><th>List € lost</th><th>Ref÷AM</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>

  <div class="section">
    <h2>Near-miss — dropping, no AM price (get a quote)</h2>
    <table><thead><tr><th>PN</th><th>Part</th><th>Family</th><th>List € lost</th></tr></thead>
    <tbody>{nm}</tbody></table>
  </div>

  <div class="section">
    <h2>Dashboard SPA candidates (14 unique) + PMS gaps</h2>
    <div class="intel-grid">
      <table><thead><tr><th>PN</th><th>Part</th><th>CY €</th><th>Δ retail</th></tr></thead><tbody>{spa}</tbody></table>
      <table><thead><tr><th>Family</th><th>Capture</th><th>Gap €</th></tr></thead><tbody>{pms}</tbody></table>
    </div>
  </div>
  <div class="foot">Sources: competitive_price_overlap 2026-10-06 · NUMBERS_LEDGER spa_candidates + pms (as_of 2026-08-19)</div>
</div>
</body></html>
"""


def load_sources():
    ledger = json.loads(
        (ROOT / "09_meetings/PORTUGAL_Operating_Dashboard_2026/NUMBERS_LEDGER.json").read_text(encoding="utf-8")
    )
    pms_rows = ledger["sections"]["pms"]["by_category"]
    seen = {}
    for r in ledger["sections"]["spa_candidates"]["rows"]:
        seen.setdefault(r["pn"], r)
    spa_unique = list(seen.values())
    short_path = ROOT / "09_meetings/IMotors_FY2027_BPR/_competitive_price_overlap_20261006/shortlist_dropping_and_overpriced_vs_am.csv"
    nm_path = ROOT / "09_meetings/IMotors_FY2027_BPR/_competitive_price_overlap_20261006/near_miss_dropping_no_am_price.csv"
    shortlist = list(csv.DictReader(short_path.open(encoding="utf-8")))
    near_miss = list(csv.DictReader(nm_path.open(encoding="utf-8")))
    return pms_rows, spa_unique, shortlist, near_miss


def write_drafts():
    pre = """Hello Nuno,

Before Monday could you confirm for Rolmax, Auto Reno Pacos Ferreira and Socarros Caldas:
exact address, contact name and phone, who from Astara joins each stop, and how long we have (90-120 min target).

Also leave-by time Pacos to Caldas on Tuesday, and whether Luis can join Wednesday Lisbon.

Kind regards,
"""
    wed = """Hello Nuno, Hello Luis,

For Wednesday Lisbon I would like to close on:
Sep fill 81% and the 495 back-order lines (top families / PN),
sales-to-dealer monthly feed go-live (invoice date, PN, qty, dealer if available),
SPA families you will propose,
and the open R&M / tender cases (REN, IP, Lisbon, Madeira, Arval) that still need an ISZE parts decision.

Kind regards,
"""
    (OUT / "DRAFT_mail_Nuno_previsit.txt").write_text(pre, encoding="utf-8", newline="\r\n")
    (OUT / "DRAFT_mail_Nuno_Luis_Wednesday_agenda.txt").write_text(wed, encoding="utf-8", newline="\r\n")


def write_index():
    base = OUT
    visit = base.parent
    imotors = visit.parent
    text = f"""# Portugal visit pack — one folder

Everything for the road questions + part examples lives here:

`{base}`

## In this folder

| File | Use |
|---|---|
| `WALK_ROLMAX.html` | Mon — questions + intel + part examples + DPD + IDS zeros |
| `WALK_AUTO_RENO_PACOS_FERREIRA.html` | Tue morning — same |
| `WALK_SOCARROS_CALDAS.html` | Tue afternoon — same |
| `WEDNESDAY_DB_ONEPAGER.html` | Wed Lisbon — force questions + pocket parts |
| `SPA_ASK_SHORTLIST.html` | SPA questions + 26 example PNs + near-miss + PMS |
| `DRAFT_mail_Nuno_previsit.txt` | Outlook draft (you send) |
| `DRAFT_mail_Nuno_Luis_Wednesday_agenda.txt` | Outlook draft (you send) |
| `OPEN_Portugal_Thin_Pack.cmd` | Double-click launcher |
| `_build_thin_pack.py` | Rebuild script (sources only) |

## Already elsewhere (not rebuilt)

| Piece | Path |
|---|---|
| Visit brief | `{visit / 'VISIT_BRIEF_Jerome_IDS_test_case.md'}` |
| IDS pocket fiches | `{visit}` (`IDS_2026_*.html`) |
| IDS network compare | `{imotors / 'IDS_2026_dealer_compare_Portugal.html'}` |
| Sep BPR PPTX | `{ROOT / '09_meetings' / 'IMotors_FY2027_BPR' / 'I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx'}` |
| AIM DLR | `{ROOT / '02_dashboards' / 'sales' / 'ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html'}` |
| DPD case study | `{ROOT / '02_dashboards' / 'sales' / 'ISZE_DPD_Case_Study_20261006.html'}` |

## Locked numbers

- GPS **63.3%** · PMS CY2025 **32.4%** / gap **€774k**
- Sep fill **81.0%** · MOS **2.49** · BO **495** · sales to dealers **€417k**
"""
    (OUT / "PACK_INDEX.md").write_text(text, encoding="utf-8")


def write_open_cmd():
    cmd = (
        "@echo off\r\n"
        'start "" "%~dp0"\r\n'
        'start "" "%~dp0PACK_INDEX.md"\r\n'
        'start "" "%~dp0WALK_ROLMAX.html"\r\n'
        'start "" "%~dp0WEDNESDAY_DB_ONEPAGER.html"\r\n'
    )
    (OUT / "OPEN_Portugal_Thin_Pack.cmd").write_bytes(cmd.encode("ascii"))


def main():
    pms_rows, spa_unique, shortlist, near_miss = load_sources()
    for d in DEALERS.values():
        (OUT / d["file"]).write_text(walk_html(d), encoding="utf-8")
        print("wrote", d["file"])
    (OUT / "WEDNESDAY_DB_ONEPAGER.html").write_text(wednesday_html(pms_rows, spa_unique), encoding="utf-8")
    (OUT / "SPA_ASK_SHORTLIST.html").write_text(
        spa_shortlist_html(shortlist, near_miss, spa_unique, pms_rows), encoding="utf-8"
    )
    write_drafts()
    write_index()
    write_open_cmd()
    print("DONE", OUT)


if __name__ == "__main__":
    main()
