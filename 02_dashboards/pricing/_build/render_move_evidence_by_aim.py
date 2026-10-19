# -*- coding: utf-8 -*-
"""Render ISZE_Price_Move_Evidence_by_AIM_2026-10-15.html from move_evidence_by_aim.json (self-contained, no CDN)."""
import json, html
from pathlib import Path

R = Path(__file__).resolve().parents[3]
J = json.loads((R / "02_dashboards/pricing/_build/move_evidence_by_aim.json").read_text(encoding="utf-8"))
OUT = R / "02_dashboards/pricing/ISZE_Price_Move_Evidence_by_AIM_2026-10-15.html"
e = html.escape


def eur(x): return "EUR " + f"{x:,.0f}"
def m(x): return f"EUR {x/1e6:.2f}M"
def pc(x, d=1): return f"{x*100:.{d}f}%"


base = J["base_total"]
L = [r for r in J["l1"] if r["billed"] >= 100000]
rest = [r for r in J["l1"] if r["billed"] < 100000]
rival_billed = sum(r["rival_billed"] for r in J["l1"])
extra_total = sum(r["extra"] for r in J["l1"])
brakes = next(r for r in L if r["name"] == "Brakes")
pad = next(r for r in J["pms"] if r["key"] == "brake_pad")

# bubble chart: x = step, y = share of billed euros with a rival price, bubble = billed
W, H, ML, MR, MT, MB = 900, 430, 62, 20, 20, 52
xmin, xmax, ymax, ymin = 0.02, 0.085, 0.70, -0.07
def X(v): return ML + (v - xmin) / (xmax - xmin) * (W - ML - MR)
def Y(v): return H - MB - (v - ymin) / (ymax - ymin) * (H - MT - MB)
bmax = max(r["billed"] for r in L)
svg = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Price move against rival price coverage per AIM category">']
for t in [0, .1, .2, .3, .4, .5, .6, .7]:
    svg.append(f'<line x1="{ML}" x2="{W-MR}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="gl"/><text x="{ML-8}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{int(round(t*100))}%</text>')
for t in [.02, .03, .04, .05, .06, .07, .08]:
    svg.append(f'<text x="{X(t):.1f}" y="{H-MB+18}" class="ax" text-anchor="middle">+{int(round(t*100))}%</text>')
svg.append(f'<text x="{(ML+W-MR)/2}" y="{H-8}" class="axt" text-anchor="middle">Base price step for the category (weighted by what we billed)</text>')
svg.append(f'<text transform="translate(16 {(MT+H-MB)/2}) rotate(-90)" class="axt" text-anchor="middle">Share of billed euros with a rival price seen</text>')
svg.append(f'<rect x="{X(.06):.1f}" y="{Y(.25):.1f}" width="{X(xmax)-X(.06):.1f}" height="{Y(0)-Y(.25):.1f}" class="zone"/>')
svg.append(f'<text x="{X(.0605):.1f}" y="{Y(.25)-6:.1f}" class="zt">Move above 6%, rival prices on under a quarter of billing</text>')
NAME = {"Intake Exhaust Emission": "Intake, exhaust", "Maintenance Service": "Service items"}
for r in L:
    cx, cy = X(r["step"]), Y(r["rival_share"])
    rad = 6 + 26 * (r["billed"] / bmax) ** .5
    svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" class="bub"><title>{e(r["name"])}: billed {m(r["billed"])}, step {pc(r["step"],2)}, rival price on {pc(r["rival_share"],0)} of billed euros ({int(r["rival_parts"])} parts)</title></circle>')
    off = {"Brakes": (-rad - 6, 4), "Cabin Interior": (rad + 6, 4), "Maintenance Service": (0, -rad - 5), "Clutch": (0, -rad - 5),
           "Intake Exhaust Emission": (rad + 6, -4), "Accident & Body": (rad + 6, 8), "Electrical": (-6, rad + 14),
           "Fuel System": (-rad - 6, 4), "Steering": (rad + 6, 4)}.get(r["name"])
    if off is None:
        continue
    a ="start" if off[0] > 0 else ("end" if off[0] < 0 else "middle")
    svg.append(f'<text x="{cx+off[0]:.1f}" y="{cy+off[1]:.1f}" class="bl" text-anchor="{a}">{e(NAME.get(r["name"], r["name"]))}</text>')
svg.append("</svg>")
chart = "\n".join(svg)


def tip(txt, t): return f'<span class="tip" tabindex="0" data-tip="{e(t)}">{txt}</span>'


rows = []
for r in sorted(L, key=lambda r: -r["extra"]):
    rows.append(f'<tr><td>{e(r["name"])}</td><td class="n">{m(r["billed"])}</td><td class="n">{pc(r["step"],2)}</td><td class="n">{eur(r["extra"])}</td>'
                f'<td class="n">{int(r["rival_parts"])}</td><td class="n">{pc(r["rival_share"],0)}</td></tr>')
rest_b = sum(r["billed"] for r in rest)
rest_x = sum(r["extra"] for r in rest)
rest_rp = int(sum(r["rival_parts"] for r in rest))
rows.append(f'<tr class="dim"><td>{len(rest)} small categories (each under EUR 0.1M)</td><td class="n">{m(rest_b)}</td><td class="n">n/a</td><td class="n">{eur(rest_x)}</td><td class="n">{rest_rp}</td><td class="n">{pc(sum(r["rival_billed"] for r in rest)/rest_b,0)}</td></tr>')

T = J["tender_rows"]
byd = {}
for r in T:
    d = byd.setdefault(r["dist"], {"opp": set(), "now": 0.0, "after": 0.0})
    d["opp"].add(r["opp"]); d["now"] += r["now"]; d["after"] += r["after"]
trows = "".join(f'<tr><td>{e(k.title())}</td><td class="n">{len(v["opp"])}</td><td class="n">{eur(v["now"])}</td><td class="n">{eur(v["after"])}</td><td class="n">+{eur(v["after"]-v["now"])}</td></tr>'
                for k, v in sorted(byd.items(), key=lambda kv: -kv[1]["now"]))
bycat = {}
for r in T:
    d = bycat.setdefault(r["label"], {"now": 0.0, "step": r["step"], "rs": r["rival_share"]})
    d["now"] += r["now"]
crows = "".join(f'<tr><td>{e(k)}</td><td class="n">{eur(v["now"])}</td><td class="n">+{pc(v["step"],1)}</td><td class="n">{pc(v["rs"],0)}</td></tr>'
                for k, v in sorted(bycat.items(), key=lambda kv: -kv[1]["now"]) if v["now"] > 0)
tn, ta = J["tender_total_now"], J["tender_total_after"]

hi = [r for r in L if r["step"] >= .06 and r["rival_share"] < .25]
hi_b = sum(r["billed"] for r in hi)
hi_x = sum(r["extra"] for r in hi)
thin = [r for r in L if r["name"] in ("Accident & Body", "Electrical", "Intake Exhaust Emission", "Steering", "Lighting")]
thin_b = sum(r["billed"] for r in thin)
thin_share = sum(r["rival_billed"] for r in thin) / thin_b

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price move evidence by AIM category</title>
<style>
:root{{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#d9d3c7;--mute:#5b6577;--card:#fff}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#10151f;--ink:#e8e4da;--line:#2b3548;--mute:#9aa5b8;--card:#1a2233}}}}
*{{box-sizing:border-box}} html,body{{overflow-x:hidden}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}}
.wrap{{max-width:1040px;margin:0 auto;padding:28px 16px 44px}}
h1{{font:700 28px/1.2 Georgia,serif;color:var(--navy);margin:0 0 6px}} h2{{font:700 20px/1.3 Georgia,serif;color:var(--navy);margin:34px 0 6px}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]) h1,:root:not([data-theme="light"]) h2{{color:#f7f4ee}}}}
.sub{{color:var(--mute);margin:0 0 16px}} .q{{color:var(--mute);margin:0 0 10px;font-style:italic}}
.verdict{{background:var(--navy);color:#f7f4ee;border-left:6px solid var(--terra);padding:16px 18px;border-radius:4px;font-size:16px}} .verdict b{{color:#fff}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}}
.k{{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--terra);padding:10px 12px;border-radius:3px}} .k b{{display:block;font:700 22px Georgia,serif;color:var(--navy)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]) .k b{{color:#f7f4ee}}}}
.k span{{font-size:13px;color:var(--mute)}}
.dia{{overflow-x:auto}} svg{{width:100%;min-width:640px;height:auto;display:block}}
.gl{{stroke:var(--line);stroke-width:1}} .ax{{font:12px system-ui;fill:var(--mute)}} .axt{{font:600 12px system-ui;fill:var(--mute)}}
.bub{{fill:#15233c;fill-opacity:.55;stroke:#15233c;stroke-width:1.5}} .bl{{font:600 12px system-ui;fill:var(--ink);paint-order:stroke;stroke:var(--paper);stroke-width:3px}}
.zone{{fill:#c0552d;fill-opacity:.09;stroke:#c0552d;stroke-dasharray:6 4}} .zt{{font:600 12px system-ui;fill:#c0552d}}
table{{width:100%;border-collapse:collapse;margin:8px 0;background:var(--card)}} th{{background:var(--navy);color:#f7f4ee;text-align:left;padding:8px 10px;font-size:13px}}
td{{padding:8px 10px;border-bottom:1px solid var(--line);font-size:14px}} td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}} tr.dim td{{color:var(--mute)}}
.tw{{overflow-x:auto}} .tw table{{min-width:560px}}
.tip{{position:relative;border-bottom:1px dotted var(--terra);cursor:help}}
.tip::after{{content:attr(data-tip);position:absolute;left:0;top:130%;width:min(300px,70vw);background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:8px 10px;border-radius:3px;font:400 12px/1.4 system-ui;opacity:0;pointer-events:none;transition:opacity .12s;z-index:60}}
.tip:hover::after,.tip:focus::after{{opacity:1}}
.note{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--terra);padding:10px 14px;margin:10px 0;font-size:14px}}
.foot{{color:var(--mute);font-size:12px;margin-top:28px;border-top:1px solid var(--line);padding-top:10px}} .foot code{{font-size:11px;word-break:break-all}}
</style></head><body><div class="wrap">
<h1>Which price moves have evidence behind them</h1>
<p class="sub">Internal read, 15 October 2026. The 22 markets in the price revision simulator v6 (no MIDI). Base: what we billed, July 2025 to June 2026, {m(base)}.</p>

<div class="verdict"><b>Most of the price move has no rival price behind it.</b> Rival prices exist for {J["rival_pns_in_base"]} of {J["parts_in_base"]:,} parts we billed, which is {pc(rival_billed/base,0)} of billed euros. Brakes is the one large category with real coverage ({pc(brakes["rival_share"],0)}), and it also carries the largest step of the big categories (+{brakes["step"]*100:.1f}%). {len(hi)} categories moving above 6% have rival prices on under a quarter of their billing: {m(hi_b)} billed, about {eur(hi_x)} of the extra euros. Tenders are real but small: the {J["tender_opps"]} tenders in your markets that carry parts demand are worth {eur(tn)} a year at today's price.</div>

<div class="kpis">
<div class="k"><b>{pc(J["weighted_step"],2)}</b><span>{tip("weighted base price step on this base","Billed euros times each part's base price step, summed, divided by total billed. The official index of 5.9616% weights by quantity at the prior base price, so the two differ by 0.04 points.")}</span></div>
<div class="k"><b>{eur(extra_total)}</b><span>{tip("extra euros a year, no volume reaction","Billed euros times the base price step, summed over all parts. This is the move before any drop in what dealers buy.")}</span></div>
<div class="k"><b>{pc(rival_billed/base,0)}</b><span>{tip("of billed euros have a rival price seen","Billed euros of parts that carry at least one aftermarket price for the same part (exact or cross-referenced), divided by total billed. Genuine parts sold outside our network are not counted as rivals.")}</span></div>
<div class="k"><b>{eur(tn)}</b><span>{tip("yearly parts demand in the tenders we can size","Addressable service-parts euros per year, summed over the tenders in tender_data.json that carry a service demand and a matched distributor. Valued at today's price, if won.")}</span></div>
</div>

<h2>Link 1: where the move meets rival prices</h2>
<p class="q">For each AIM category, is the price step backed by prices we have seen from rivals?</p>
<div class="dia">{chart}</div>
<div class="note">Reading it: bubble size is billed euros; hover a bubble for its name and numbers, and the table below lists every category. The shaded box is the weak spot, a big move with little rival evidence. Rival coverage says we have looked, not that the move is safe. Where it is low, we do not know either way. The comparison basis for rival prices is still provisional, so this page counts coverage and does not claim a price gap.</div>
<div class="tw"><table><tr><th>AIM category</th><th class="n">Billed</th><th class="n">Base price step</th><th class="n">Extra euros a year</th><th class="n">Parts with a rival price</th><th class="n">Billed euros covered</th></tr>{"".join(rows)}</table></div>

<h2>Link 2: tender demand at the revised list</h2>
<p class="q">If the list moves, what happens to the parts demand in the tenders we can size?</p>
<div class="tw"><table><tr><th>Distributor</th><th class="n">Tenders</th><th class="n">Per year, today's price</th><th class="n">Per year, revised list</th><th class="n">Change</th></tr>{trows}
<tr><td><b>Total</b></td><td class="n"><b>{J["tender_opps"]}</b></td><td class="n"><b>{eur(tn)}</b></td><td class="n"><b>{eur(ta)}</b></td><td class="n"><b>+{eur(ta-tn)}</b></td></tr></table></div>
<div class="tw"><table><tr><th>Service category in the tenders</th><th class="n">Per year, today</th><th class="n">Base price step</th><th class="n">Billed euros with a rival price</th></tr>{crows}</table></div>
<div class="note">The honest reading: the connection now works, but these tenders are too small to move a pricing decision. {J["tender_opps"]} tenders, three distributors (Germany, Ireland, Portugal), {eur(tn)} a year. Only these {J["tender_opps_book"]} of 734 tenders carry both a parts demand and a matched distributor; most of the rest have no fleet size, so no demand can be calculated. The revised list adds {eur(ta-tn)} a year to that demand ({pc(ta/tn-1,1)}). No tender has a recorded outcome, so we still cannot say which price wins.</div>

<h2>What this says for the price decision</h2>
<div class="note"><b>1.</b> Brakes is where evidence and move meet: largest step, rival prices on most of the billing. Check this one first; brake pads alone step +{pad["step"]*100:.1f}%.<br>
<b>2.</b> Accident and body, electrical, intake and exhaust, steering and lighting carry {m(thin_b)} of billing with rival prices on {pc(thin_share,0)} of it. A move there is a judgement, not evidence. Extending the rival price search to these categories is where closing the data gap pays most.<br>
<b>3.</b> Tenders do not yet inform price. Recording wins, losses and prices on your distributors' tenders is the only way that changes.</div>

<p class="foot">Sources and method. Billed base and base price step per part: <code>02_dashboards/pricing/_build/price_tool_html_v6_2026-10-15/payload6.json</code> (ties to the simulator base, EUR 32,595,852.63, difference 0.00). Rival prices: <code>01_data/00_derived/price_observations.parquet</code>, {J["obs_rows"]:,} observations, aftermarket price types only, same-part matches only (exact OEM or cross-reference); {J["genuine_pns_in_base"]:,} base parts also have a genuine price seen outside our network, not counted here. Tenders: <code>01_data/14_dashboards/tender_data.json</code> (generated 12 Oct 2026), opportunities with a matched distributor and service demand, re-priced with each service category's base price step. Built by <code>02_dashboards/pricing/_build/build_move_evidence_by_aim.py</code> and <code>render_move_evidence_by_aim.py</code>; the simulator v6 file is untouched. AIM is our parts category tree; base price is the yen list price before exchange rate and discount.</p>
</div></body></html>"""
OUT.write_text(page, encoding="utf-8")
print("wrote", OUT, len(page))
