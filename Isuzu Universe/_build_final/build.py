# -*- coding: utf-8 -*-
"""Isuzu Universe - the white paper (final edition, 23 September 2026).

Builds one HTML file with inline SVG charts, renders it to PDF with headless Chrome
(network blocked), fills the contents page numbers in a second pass, and rasterises every
page for visual QA.

Run:  python build.py
"""
import base64
import os
import re
import subprocess
import sys
import tempfile

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import charts as C  # noqa: E402

OUT_PDF = os.path.join(ROOT, "ISUZU_UNIVERSE_WHITE_PAPER_FINAL_2026-09-23.pdf")
HTML = os.path.join(HERE, "white_paper_final.html")
QA = os.path.join(HERE, "_qa")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ------------------------------------------------------------------ numbers (all from source)
ids = C.ids_stats()
n_db, billed_2025 = C.network_total()
c25, c24 = C.concession_totals("2025"), C.concession_totals("2024")
iuk = C.iuk_air()
pads = C.ituk_portugal_iuk()[("ITUK", "brake_pad")]
pad24, pad25 = float(pads["total_eur_2024"]), float(pads["total_eur_2025"])
q24, q25 = float(pads["total_qty_2024"]), float(pads["total_qty_2025"])
split = C.brake_split_values()
split_tot = sum(v for _, v in split)
pt = C.portugal_values()
el = C.elasticity()
ms, br = el["AIM: Maintenance Service"], el["AIM: Brakes"]
st, dc, oc = C.tender_stats()
ituk_billed, dlod_share = C.dlod_ituk_share()
gps = C.gps_2025()
ceiling = sum(float(r["max_spend_eur"] or 0) for r in gps)
placeholder = [r for r in gps if r["uio_units"] and float(r["uio_units"] or 0) > 0 and r["max_spend_eur"]
               and abs(float(r["max_spend_eur"]) / float(r["uio_units"]) - 250) < 0.01]
placeholder_eur = sum(float(r["max_spend_eur"]) for r in placeholder)
iuk_filters_2025 = sum(float(r["billed_eur"]) for r in C.load("pms_campaign_suspect_by_db_family_2024_2025.csv")
                       if r["year"] == "2025" and r["distributor_code"] == "IUK" and r["pms_category"].endswith("filter"))

assert abs(pad24 - 347389.58) < 0.01 and abs(pad25 - 302366.25) < 0.01
assert abs(billed_2025 - 32381311.55) < 0.01 and n_db == 22
assert ids["rows"] == 519 and ids["scored"] == 490

E = C.eur
pct = lambda a, b: (b - a) / a * 100  # noqa: E731
logo = base64.b64encode(open(os.path.join(ROOT, "_assets", "isuzu_logo_white.png"), "rb").read()).decode()

# ------------------------------------------------------------------ helpers
def fig(svg, caption, source):
    return (f'<figure>{svg}<figcaption><b>{caption}</b> <span class="src">{source}</span></figcaption></figure>')


def table(head, rows, cls=""):
    h = "".join(f"<th>{x}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


CHAPTERS = []


def opener(no, title, key, keyline, sections):
    CHAPTERS.append((no, title))
    secs = "".join(f"<li>{s}</li>" for s in sections)
    return f"""
<section class="opener">
  <div class="op-no">{no:02d}</div>
  <div class="op-mark">Chapter {no:02d}</div>
  <h1 class="op-title">{title}</h1>
  <div class="op-rule"></div>
  <div class="op-key">{key}</div>
  <div class="op-keyline">{keyline}</div>
  <ul class="op-secs">{secs}</ul>
</section>"""


# ------------------------------------------------------------------ CSS
CSS = """
@page { size: A4; margin: 17mm 17mm 19mm 17mm;
  @bottom-left { content: "Isuzu Universe  ·  The white paper  ·  23 September 2026"; font: 7.5pt Arial, sans-serif; color: #6B7078; }
  @bottom-right { content: counter(page); font: bold 8pt Arial, sans-serif; color: #D71920; } }
@page dark { margin: 0; @bottom-left { content: none; } @bottom-right { content: none; } }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; line-height: 1.5; color: #1E2124; background: #FFFFFF; }
h2 { font-size: 15pt; color: #24282C; margin: 0 0 3mm; padding-top: 1mm; break-after: avoid; }
h2 .n { color: #D71920; margin-right: 2.5mm; }
h3 { font-size: 11pt; color: #24282C; margin: 5mm 0 1.5mm; break-after: avoid; }
p { margin: 0 0 2.6mm; orphans: 3; widows: 3; }
b, strong { color: #24282C; }
.lead { font-size: 11pt; line-height: 1.5; color: #24282C; }
.label { display: inline-block; font-size: 7pt; font-weight: bold; letter-spacing: .06em; text-transform: uppercase;
  padding: .4mm 1.6mm; border-radius: 1mm; margin-right: 1.5mm; vertical-align: .3mm; }
.m { background: #24282C; color: #fff; } .p { background: #D71920; color: #fff; } .i { background: #B9BDC3; color: #24282C; }
figure { margin: 3.5mm 0 4.5mm; break-inside: avoid; }
figcaption { font-size: 8pt; color: #6B7078; margin-top: 1.5mm; border-top: .6px solid #E4E5E7; padding-top: 1.2mm; }
figcaption b { color: #24282C; }
table { width: 100%; border-collapse: collapse; margin: 2.5mm 0 4mm; font-size: 8.6pt; break-inside: avoid; }
th { background: #24282C; color: #fff; text-align: left; padding: 1.8mm 2.2mm; font-size: 7.8pt; letter-spacing: .03em; }
td { padding: 1.7mm 2.2mm; border-bottom: .6px solid #E4E5E7; vertical-align: top; }
tbody tr:nth-child(even) td { background: #F5F5F4; }
table.num td:nth-child(2) { white-space: nowrap; font-weight: bold; }
.callout { border-left: 3px solid #D71920; background: #F5F5F4; padding: 3mm 4mm; margin: 3mm 0 4mm; break-inside: avoid; }
.callout p:last-child { margin-bottom: 0; }
.keep { break-inside: avoid; }
.newpage { break-before: page; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }
.steps { counter-reset: s; list-style: none; padding: 0; margin: 2mm 0 3mm; }
.steps li { counter-increment: s; position: relative; padding: 0 0 1.8mm 8mm; }
.steps li::before { content: counter(s); position: absolute; left: 0; top: .2mm; width: 5mm; height: 5mm; border-radius: 50%;
  background: #D71920; color: #fff; font-size: 7.5pt; font-weight: bold; text-align: center; line-height: 5mm; }
ul.plain { margin: 1mm 0 3mm; padding-left: 5mm; } ul.plain li { margin-bottom: 1.2mm; }
.bignum { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 3mm 0 4mm; break-inside: avoid; }
.bignum div { background: #F5F5F4; border-top: 3px solid #24282C; padding: 2.5mm 3mm; }
.bignum div.r { border-top-color: #D71920; }
.bignum .v { font-size: 17pt; font-weight: bold; color: #24282C; line-height: 1.1; }
.bignum div.r .v { color: #D71920; }
.bignum .l { font-size: 7.8pt; color: #6B7078; margin-top: 1mm; line-height: 1.3; }

/* dark pages: cover and chapter openers */
.cover, .opener { page: dark; break-before: page; break-after: page; width: 210mm; height: 297mm; overflow: hidden;
  background: #24282C; color: #E9EAEC; position: relative; }
.cover { break-before: auto; padding: 20mm 20mm 0; }
.cover .logo { height: 9mm; }
.cover .kicker { margin-top: 20mm; font-size: 8.5pt; letter-spacing: .22em; color: #A9AEB5; font-weight: bold; }
.cover h1 { font-size: 46pt; line-height: 1.02; color: #FFFFFF; margin: 4mm 0 0; letter-spacing: -.01em; }
.cover .sub { font-size: 14pt; line-height: 1.4; color: #D9DBDE; margin-top: 6mm; max-width: 150mm; }
.cover .rule, .opener .op-rule { width: 42mm; height: 3px; background: #D71920; margin: 9mm 0 7mm; }
.cover .hero { background: #2E3338; border-radius: 2mm; padding: 5mm 6mm 3mm; }
.cover .herocap { font-size: 9pt; color: #C4C7CC; margin-top: 2mm; line-height: 1.45; }
.cover .herocap b { color: #FFFFFF; }
.cover .settles { margin-top: 8mm; display: grid; grid-template-columns: 1fr 1fr; gap: 2.5mm 8mm; font-size: 9.3pt; color: #D9DBDE; }
.cover .settles div { border-left: 2px solid #D71920; padding-left: 3mm; }
.cover .by { position: absolute; left: 20mm; right: 20mm; bottom: 16mm; font-size: 9pt; color: #A9AEB5;
  border-top: .6px solid #474D54; padding-top: 3mm; display: flex; justify-content: space-between; }
.cover .by b { color: #FFFFFF; }
.opener { padding: 38mm 22mm 0; }
.op-no { position: absolute; right: 14mm; top: 150mm; font-size: 150pt; font-weight: bold; color: #2E3338; line-height: 1; z-index: 0; }
.opener > *:not(.op-no) { position: relative; z-index: 1; }
.opener > .op-secs { position: absolute; }
.op-mark { font-size: 9pt; letter-spacing: .24em; text-transform: uppercase; color: #D71920; font-weight: bold; }
.op-title { font-size: 34pt; line-height: 1.08; color: #FFFFFF; margin: 4mm 0 0; max-width: 150mm; }
.op-key { font-size: 64pt; font-weight: bold; color: #FFFFFF; line-height: 1; margin-top: 30mm; }
.op-keyline { font-size: 14pt; color: #D9DBDE; line-height: 1.4; max-width: 140mm; margin-top: 4mm; }
.op-secs { position: absolute; left: 22mm; right: 22mm; bottom: 22mm; list-style: none; padding: 4mm 0 0; margin: 0;
  border-top: .6px solid #474D54; columns: 2; column-gap: 10mm; font-size: 9pt; color: #A9AEB5; }
.op-secs li { margin-bottom: 1.6mm; break-inside: avoid; }
.toc { width: 100%; font-size: 10.5pt; }
.toc td { padding: 2.6mm 1mm; border-bottom: .6px solid #E4E5E7; background: #fff !important; }
.toc td.no { color: #D71920; font-weight: bold; width: 12mm; }
.toc td.pg { text-align: right; font-weight: bold; width: 14mm; }
.src { color: #8A8F96; }
"""

# ------------------------------------------------------------------ content
H = []
H.append(f"""
<section class="cover">
  <img class="logo" src="data:image/png;base64,{logo}" alt="Isuzu">
  <div class="kicker">ISZE PARTS EUROPE  ·  WHITE PAPER</div>
  <h1>Isuzu Universe</h1>
  <div class="sub">Tools that distributors and dealers want to use, in exchange for the information that makes those tools better.</div>
  <div class="rule"></div>
  <div class="hero">{C.cover_argument()}
    <div class="herocap"><b>Isuzu Truck UK brake pads, 2024 to 2025.</b> Value fell {abs(pct(pad24, pad25)):.1f}%, units fell {abs(pct(q24, q25)):.1f}%.
    A revenue view suggests a demand problem, a volume view suggests a price problem. Only product detail shows where to act, and that is what Universe gives a distributor.</div>
  </div>
  <div class="settles">
    <div>What Universe is, and the routine service it deliberately leaves out</div>
    <div>How a Deal of the Day is funded, and what it has to earn</div>
    <div>What dealers and distributors receive, and what they are asked for</div>
    <div>What to build first, and the condition under which it stops</div>
  </div>
  <div class="by"><span>Prepared by <b>Jérôme Van der Pluym</b>, VP Sales, ISZE</span><span>23 September 2026</span></div>
</section>
""")

H.append(f"""
<h2>The paper on one page</h2>
<p class="lead"><b>What Universe is.</b> A programme that gives distributors and dealers tools worth opening and, in return, earns the parts and aftersales information that makes the next answer sharper. The tools are the offer. The exchange is the point.</p>
<p><b>Why now.</b> ISZE has asked its distributors for information for years without returning enough visible value to keep the request alive. A reporting obligation can start an exchange; only a useful tool keeps it going. The 2025 arrangement that tied a share of the normal distributor rebate to a performance submission is the floor, not the mechanism.</p>
<p><b>What it is not.</b> Availability questions, part and Best Value lookups, day-to-day quotation handling and support administration stay in the existing business. They are not modules of Universe, not rewards for taking part, and not bargaining chips for more data.</p>
<h3>Three decisions for this month</h3>
{table(["Decision", "Recommendation", "What has to be true first"], [
    ["<b>1. Fund Deal of the Day</b>", "A named line of €60,000 to €90,000 inside the existing €100,000 route. A Deal of the Day qualifies only above €150,000 of eligible billing.", "The selection rule is agreed and the first eligible Deal of the Day is named."],
    ["<b>2. Approach ten dealers</b>", "Through their distributor, arriving with a finished review of the dealer's own business and asking for a correction, not for data.", "A prepared review exists from information ISZE already holds."],
    ["<b>3. Build two tools first</b>", "The Parts Atlas and the Dealer Standards Studio.", "The parts classification is fixed to one named release."],
])}
<div class="bignum">
  <div><div class="v">{E(billed_2025 / 1e6, 1)}M</div><div class="l">parts billed to {n_db} distributors in 2025, the base every envelope is measured against</div></div>
  <div class="r"><div class="v">0.31%</div><div class="l">the €100,000 route as a share of that base: the right size for a pilot</div></div>
  <div><div class="v">40</div><div class="l">beneficial actions at €2,500 each are needed to earn back €100,000</div></div>
  <div class="r"><div class="v">0</div><div class="l">outcomes recorded for Don't Lose the Deal or for public tenders</div></div>
</div>
<div class="callout"><p><b>One decision closes two gaps.</b> Don't Lose the Deal and the tender feed can both qualify and support a deal, and neither can show that it won anything, because nobody writes the outcome down. Agree to record one line per closed case.</p></div>
<p><b>Still open.</b> Nobody has yet been named to answer a distributor's or a dealer's question once the tools raise one, and the money depends on that. Whether participation should carry a score is also still to be decided (chapter 5).</p>
<p><b>What this paper does not claim.</b> No realised return, no approved budget, no forecast of extra sales. No participant has accepted anything. Where money is discussed, the paper states the hurdle, not a predicted outcome.</p>
""")

H.append("""<section class="newpage"><h2>Contents</h2><table class="toc">@@TOC@@</table>
<div class="callout" style="margin-top:8mm"><p><b>How to read the evidence.</b> Every substantive statement carries one of three labels.
<span class="label m">Measured</span> is counted in ISZE's own records. <span class="label i">Inferred</span> is a conclusion drawn from measured data.
<span class="label p">Proposed</span> is a design or decision not yet taken. Where something is unknown, the paper says so and does not fill the gap with an assumption.
Illustrative arithmetic is labelled as such and is never a forecast.</p></div></section>""")

# ---------------------------------------------------------------- 1 Deal of the Day
H.append(opener(1, "Deal of the Day", "€500",
                "of gross profit turns on one choice: give the discount on the extra units, not on all of them.",
                ["What a Deal of the Day is", "Which units get the discount", "The size floor",
                 "Where concession already sits", "A candidate for the pilot", "Why thresholds, not forecasts",
                 "The funding line"]))
H.append(f"""
<h2><span class="n">1.1</span>What a Deal of the Day is</h2>
<p class="lead">ISZE helps a distributor prepare a specific, time-limited commercial offer: a reasoned product selection, the right audience, transparent economics, and a way to learn from what follows. The value is in the preparation behind the offer, not in the discount.</p>
<p>It is the most concrete thing Universe does, and the one a distributor's parts manager understands in thirty seconds. That is why it opens this paper. It is also the one that spends money, so it has to be designed so that the money buys evidence.</p>
<p><b>Not to be confused with Don't Lose the Deal</b> (chapter 4), which is Isuzu Truck UK's existing support for competitive quotations. The initials are the same and the products are different.</p>

<h2><span class="n">1.2</span>Which units get the discount</h2>
{fig(C.fig_scope_effect(), "The same 120 units, two ways of paying for them.", "Illustrative arithmetic: 100-unit baseline at €100 net and €70 parts cost, 20 extra units, 5% concession. Not an Isuzu price, offer or forecast.")}
<p><span class="label p">Illustrative</span> A distributor sells 100 units a period at €100 net, with €70 of parts cost: €3,000 of gross profit. A Deal of the Day lifts volume to 120 units at a 5% concession. If every unit gets the discount, gross profit stays at €3,000, so the 20 extra units have bought nothing. If only the 20 extra units get the discount and the baseline keeps its normal price, gross profit is €3,500. The €500 difference comes from the scope of the concession alone and assumes no change in demand.</p>
{table(["Mechanism", "Adds by construction?", "Verdict"], [
    ["Concession on extra volume only, against a documented baseline", "Yes", "<b>Test first</b>"],
    ["Fixed contribution per Deal of the Day", "No", "Test"],
    ["Concession on all volume, baseline included", "No. It costs five times as much on the same volume", "Not as standard"],
    ["Payment per record or data field submitted", "No. It rewards disclosure, not decisions", "Do not use"],
    ["Prize for the largest sales total", "No. Business sizes cannot be compared", "Do not use"],
])}

<h2><span class="n">1.3</span>The size floor</h2>
<p>A Deal of the Day costs preparation and support whether it is large or small. With the same illustrative economics (a 30% gross margin and a 5% concession on the extra units, so 25 cents of gross profit on every extra euro sold), the chart shows how much extra business one Deal of the Day has to produce just to pay back its own support.</p>
{fig(C.fig_size_floor(), "Small Deals of the Day cannot pay for themselves.", "Illustrative arithmetic: extra sales × 25% gross profit = support cost. Not a forecast of response.")}
<p>At €150,000 of eligible billing, €2,500 of support needs {C.uplift_needed(150000, 2500):.1f}% extra sales and €5,000 needs {C.uplift_needed(150000, 5000):.1f}%. At €50,000 the same support needs {C.uplift_needed(50000, 2500):.0f}% and {C.uplift_needed(50000, 5000):.0f}%, which no discount of this size should be expected to deliver. <span class="label p">Proposed</span> A Deal of the Day qualifies for support only above <b>€150,000 of eligible billing</b>.</p>

<h2><span class="n">1.4</span>Where concession already sits</h2>
<p><span class="label m">Measured</span> Maintenance parts (PMS) billed {E(c25["billed"] / 1e6, 2)}M across {c25["n"]} distributors in 2025 on lines carrying a reference price. Of that, {c25["ge20_pct"]:.1f}% ({E(c25["ge20"])}) was billed at least 20% under the reference price and {c25["ge30_pct"]:.1f}% at least 30% under. In 2024 the same shares were {c24["ge20_pct"]:.1f}% and {c24["ge30_pct"]:.1f}% of {E(c24["billed"] / 1e6, 2)}M. The fall is real and favourable.</p>
{fig(C.fig_concession_db(), "The deepest concession is not in the largest markets.", "ISZE billing of maintenance parts with a reference price, calendar 2025. Red: under €500k billed and at least 15% deep-discounted. The twelve highest shares of 24 distributors are shown.")}
<p><span class="label i">Inferred</span> Ukraine, Portugal and Germany carry high deep-discount shares on modest billed bases. A support programme without a size floor would spend most of its money in the smallest markets, because that is where the share is highest. The data argues for the floor; caution alone would not.</p>

<h2><span class="n">1.5</span>A candidate for the pilot: Isuzu UK air filters</h2>
{fig(C.fig_iuk_air(), "A line whose concession is already moving.", "ISZE billing of air filters to Isuzu UK, calendar 2024 and 2025, lines with a reference price.")}
<p><span class="label m">Measured</span> Air filters billed to Isuzu UK rose from {C.eurk(iuk["2024"][0])} in 2024 to {C.eurk(iuk["2025"][0])} in 2025, while the share billed at least 20% under the reference price fell from {iuk["2024"][1]:.1f}% to {iuk["2025"][1]:.1f}%. This line already has a measured concession history, at a distributor where account-level detail exists. It is the right place to test whether a prepared Deal of the Day adds anything a concession alone does not.</p>
<p><span class="label p">Proposed</span> On its own, at {C.eurk(iuk["2025"][0])}, the line sits below the €150,000 floor. It qualifies as part of a wider filter selection for the same distributor (Isuzu UK filters together billed {C.eurk(iuk_filters_2025)} in 2025), or if the floor is set lower. That choice belongs to the funding decision. Nothing has been agreed with the distributor.</p>

<h2><span class="n">1.6</span>Why thresholds, not forecasts</h2>
<p><span class="label m">Measured</span> ISZE has measured how distributor purchasing responded to list-price moves between 2024 and 2025. For maintenance-service parts the response is negative, but the uncertainty is half the size of the estimate and it explains less than 1% of the movement. For brakes it is flat to slightly positive, with an uncertainty three times the size of the estimate. For lubrication it cannot be measured at all, because the price moved almost uniformly. Of the brakes change, roughly {E(abs(float(br["eur_sensitive_price_up_vol_down"])), 0)[:-4]}k sits where price rose and volume fell, {E(float(br["eur_passed_price_up_vol_up"]), 0)[:-4]}k where both rose, and {E(abs(float(br["eur_leak_price_flat_vol_down"])), 0)[:-4]}k where volume fell with price flat. This is ISZE-to-distributor purchasing, not dealer demand, and demand shocks are not controlled for. The evidence is too weak to forecast from, which is why every Deal of the Day in this paper is judged against a threshold: what would have to happen, not what will.</p>

<h2><span class="n">1.7</span>The funding line</h2>
{table(["Line", "Proposed", "Basis", "What has to be demonstrated"], [
    ["Deal of the Day support", "€35,000 to €50,000", "8 to 12 Deals of the Day at €2,500 to €5,000 each, all above the size floor", "Qualifying Deals of the Day exist; contribution is measured on the same scope before and after"],
    ["Dealer enablement", "€15,000 to €25,000", "25 to 40 accepted setup tasks at €600", "A documented task, an accepted deliverable, and later use"],
    ["Independent evaluation", "€10,000 to €15,000", "Two waves, at 90 and 180 days, including returns", "The result is published whether it is favourable or not"],
    ["<b>Total cash</b>", "<b>€60,000 to €90,000</b>", "Inside the existing €100,000 route, without touching the engineering or assurance lines", "—"],
    ["Internal preparation", "Not costed here", "Shown as internal time, not assumed free", "A named owner and a stated allocation"],
], "num")}
<div class="callout"><p><b>Name the line.</b> The current position, that Deal of the Day support needs its own approved commercial treatment and is not automatically funded from an enablement allocation, is a control, not an answer. This paper asks for the line to be named.</p>
<p><b>What it must earn.</b> At €2,500 of contribution per beneficial action, €60,000 to €90,000 needs 24 to 36 qualifying actions before internal costs. A pilot of ten Deals of the Day proves the method, not the return. What it delivers is the first real measurement of how often a Deal of the Day qualifies, and that rate is the number any expansion should be decided on.</p></div>
""")

# ---------------------------------------------------------------- 2 Product detail
H.append(opener(2, "What product detail shows", f"{split[0][1] / split_tot * 100:.1f}%",
                "of the braking decline at Isuzu Truck UK is one product: brake pads. A total says the business moved. Detail says where.",
                ["The parts classification system", "Isuzu Truck UK brake pads", "Where the decline sits",
                 "Portugal clutch kits: a mistake prevented", "The ranked family view", "What the classification refuses to do"]))
H.append(f"""
<h2><span class="n">2.1</span>The parts classification system</h2>
<p class="lead">Every example in this chapter rests on a new parts classification system built by Jérôme Van der Pluym. It places every Isuzu part number in a family, a product group and a product form (element, housing, assembly or kit) and keeps Genuine and Best Value side by side.</p>
<p>It answers the question a total cannot: <i>what is really changing in this parts business, and which references explain it?</i> A distributor's parts business can be flat while its composition moves a great deal, and a change in mix hides a change in quantity. The classification is what lets a parts manager move from "our parts business moved" to "brake pads moved, and these are the references behind it".</p>

<h2><span class="n">2.2</span>Isuzu Truck UK brake pads</h2>
{fig(C.fig_brake_pads(), f"Value fell {abs(pct(pad24, pad25)):.1f}%. Units fell {abs(pct(q24, q25)):.1f}%.", "ISZE billing to Isuzu Truck UK, brake pads, full calendar 2024 and 2025.")}
<p><span class="label m">Measured</span> Parts billed to Isuzu Truck UK in brake pads fell from {E(pad24, 2)} in 2024 to {E(pad25, 2)} in 2025, a reduction of {E(pad24 - pad25, 2)}. Units fell from {q24:,.0f} to {q25:,.0f}. Read the two halves together: a revenue view suggests a demand problem, a quantity view suggests a price problem, and neither is the right first question. The gap between the two percentages is the first thing a parts manager should look at. The national figure of 22,389 Isuzu trucks in the UK is context, not the population that buys each pad, and it is not divided among dealers.</p>

<h2><span class="n">2.3</span>Where the decline sits</h2>
{fig(C.fig_brake_split(), f"{E(split_tot, 2)} across three braking categories; pads are {split[0][1] / split_tot * 100:.1f}% of it.", "Same source and period.")}
<p><span class="label i">Inferred</span> The starting sentence changes from "braking products are down" to "brake pads are down", which is something a distributor can act on. It does not support one remedy across all braking products, and it does not turn the reduction into recoverable revenue.</p>

<h2><span class="n">2.4</span>Portugal clutch kits: a mistake prevented</h2>
{fig(C.fig_portugal(), "The line grew while Genuine fell.", "ISZE billing to the Portuguese distributor, clutch kits, full calendar 2024 and 2025.")}
<p><span class="label m">Measured</span> Combined clutch-kit billing rose from {E(pt["total_eur_2024"], 2)} to {E(pt["total_eur_2025"], 2)} ({pct(pt["total_eur_2024"], pt["total_eur_2025"]):+.1f}%). Genuine fell from {E(pt["genuine_eur_2024"], 2)} to {E(pt["genuine_eur_2025"], 2)}, while Best Value rose from {E(pt["bvp_eur_2024"], 2)} to {E(pt["bvp_eur_2025"], 2)}. Units were flat: {pt["total_qty_2024"]:,.0f} kits, then {pt["total_qty_2025"]:,.0f}.</p>
<p><span class="label i">Inferred</span> A Genuine-only view would have proposed a recovery action for a business that grew. Here the tool earns its place by preventing a mistake rather than finding an opportunity. Genuine and Best Value are one commercial offer, and only the classification shows both answers at once.</p>

<h2><span class="n">2.5</span>The ranked family view</h2>
{fig(C.fig_family_ranked(), "Where the maintenance-parts money is, and where it is discounted.", "ISZE billing of maintenance parts with a reference price, 24 distributors, calendar 2025. The ten largest families by billing.")}
<p><span class="label m">Measured</span> Two families carry a large deep-discount share on a modest base: front brake pads at 36.0% of €423k and blower filters at 25.2% of €374k. That is the shape of a handful of large deals, not a broad pricing position. Two large families carry almost none: brake rotors at 3.4% of €1.30M and oil filters at 1.5% of €557k.</p>
<p><span class="label i">Inferred</span> A family whose pricing is settled has no price opportunity. If it has an opportunity at all, it lies in range, application or coverage. Saying so stops a settled line being offered up as a Deal of the Day candidate.</p>

<h2><span class="n">2.6</span>What the classification refuses to do</h2>
<ol class="steps">
<li><b>A product is not an opportunity just because a participant has not bought it.</b> No recorded purchase, a documented range gap, a coverage exclusion, a number change and an irrelevant application are five different findings.</li>
<li><b>An element, a housing, an assembly and a kit are never averaged into one unit price.</b> Doing so describes a changing mix and calls it a price change.</li>
<li><b>A missing relationship stays a visible gap.</b> It is never filled with a plausible match based on similar wording.</li>
<li><b>Classification does not establish fitment.</b> A successor relationship says one number replaces another. Whether the replacement fits a given truck is validated separately before any alternative is recommended.</li>
</ol>
<div class="callout"><p><b>One condition before any family label reaches a distributor.</b> The classification must be fixed to one named release, with a version and a build date. Until then, family labels are for use inside ISZE only, because two people in the same meeting could open two versions and get two answers for the same part number.</p></div>
""")

# ---------------------------------------------------------------- 3 Programme
H.append(opener(3, "The programme", "5 tools", "Three foundations ISZE already holds, five tools a participant opens by choice, and one boundary that keeps routine service out.",
                ["The scope boundary", "The three foundations", "The five tools", "Market and revenue analytics",
                 "The Dealer Standards Studio", "Pricing, range and offers"]))
H.append(f"""
<h2><span class="n">3.1</span>The scope boundary</h2>
<p class="lead">Universe is not a better support desk. A normal service is not a reward for participation, and participation is not the price of a normal service.</p>
{table(["Outside Universe: stays in the existing business", "Inside Universe: a commercial capability beyond that service"], [
    ["When will this part arrive?", "Recurring, evidenced constraints may inform a range study. No arrival-enquiry workflow is built."],
    ["Is a Best Value alternative available?", "Combined Genuine and Best Value positioning, product composition and range development."],
    ["Can you handle this quotation?", "Competitive evidence and transparent economics for a chosen pricing or range decision."],
    ["Can you follow up this training action?", "An explorable Dealer Standards profile and a development plan the dealer chooses."],
    ["Can you submit or administer this tender?", "Relevant fleet and tender intelligence, and a reasoned decision on which opportunities to pursue."],
])}
<p>The boundary matters commercially for two reasons. First, a programme that also answers availability questions will be judged on availability response times, and it will lose that comparison to a system that already answers them. Second, <b>the boundary is the offer</b>. The sentence that changes how a distributor's parts manager reads the approach is: <i>we are not asking you to feed a support desk, and the support desk does not get better or worse depending on what you send us.</i></p>

<h2><span class="n">3.2</span>The three foundations</h2>
{table(["Foundation", "What it holds", "The question it answers"], [
    ["<b>The parts classification system</b>", "Every part number in a family, product group and product form, with Genuine and Best Value side by side", "What is really changing in my parts business, and which references explain it?"],
    ["<b>Isuzu Dealer Standards</b>", f"The dealer self-assessment: {ids['rows']} dealer records across 19 networks, {ids['scored']} of them with a score", "What did the dealer record about itself, and has anything moved?"],
    ["<b>The market and revenue analytics platform</b>", "Vehicles in service per market and model, target spend per truck against parts billed, maintenance-parts revenue capture, competitor price monitoring from public online prices, and the public-tender feed", "Where should we concentrate effort, and is the evidence strong enough to act on?"],
])}

<h2><span class="n">3.3</span>The five tools</h2>
{table(["Tool", "The question it answers", "Built on", "Designed for"], [
    ["<b>Parts Atlas</b>", "What is really changing in my parts business, and where?", "Purchasing history and the classification", "Distributor parts manager, dealer principal"],
    ["<b>Dealer Standards Studio</b>", "What should I improve, and what has moved?", "The dealer's own assessment and development record", "Dealer principal, distributor network manager"],
    ["<b>Range &amp; Offer Planner</b>", "Which products belong in this offer, and for whom?", "An Atlas selection plus account coverage", "Distributor commercial lead"],
    ["<b>Pricing &amp; Margin Lab</b>", "What does this trade-off do to revenue and margin?", "Comparable evidence and stated unit economics", "Distributor commercial lead, ISZE"],
    ["<b>Market Intelligence</b>", "Where should we concentrate effort?", "Fleet, revenue capture, online price monitoring, tenders", "Distributor management, ISZE"],
])}
<p>A participant usually starts with the one question it can answer today with evidence it already has. The tools share a selection (entity, account, period, product range, permitted audience) rather than a screen, so a user can carry a selection from the Atlas into an offer plan without rebuilding it. A Dealer Standards plan needs no pricing data, and a pricing study needs no assessment. The tools are connected where the next decision gets better, and only there.</p>

<h2><span class="n">3.4</span>Market and revenue analytics</h2>
<p>The platform brings four views together that were previously held apart: the <b>fleet</b> (Isuzu vehicles in service by market and model), <b>target spend per truck</b> against parts actually billed, <b>maintenance-parts revenue capture</b> by vehicle and service interval, and <b>competitor price monitoring from public online prices</b>. It also carries an early-warning view on distributors and dealers and the public-tender feed described in chapter 4. Its job is to show where revenue is being left on the table, and to say when the evidence is not strong enough to act on.</p>
{fig(C.fig_network_billing(), "Where the parts business is.", f"ISZE parts billed to {n_db} distributors, calendar 2025. Red: the three largest.")}
<p><span class="label m">Measured</span> For 2025 the model puts the ceiling on target spend at {E(ceiling)} across the markets with a fleet figure, against {E(billed_2025, 2)} of parts actually billed. Of that ceiling, {E(placeholder_eur)} ({placeholder_eur / ceiling * 100:.2f}%) comes from {len(placeholder)} markets where no measured purchasing rate exists and a flat €250 per truck is assumed.</p>
<div class="callout"><p><b>The ceiling is not revenue.</b> It is what a market could spend on parts on a modelled basis, not money available to ISZE, and two-fifths of it is an assumption. Multiplying it by a recovery percentage would invent a revenue case this paper refuses to make. Its correct use is comparative: this market sits at this share of its own ceiling, the next market at that share, and the order is the decision input.</p></div>
<p>Three rules keep the numbers honest. A national vehicle total is never allocated to dealers by sales, visits or geography. A part that serves several vehicle classes stays shared unless exclusive fitment proves which model it belongs to. And a modelled gap is not recoverable sales and not a business case.</p>

<h2><span class="n">3.5</span>The Dealer Standards Studio</h2>
<p>The Studio turns the dealer self-assessment into a development tool rather than a questionnaire archive. What a dealer would see, in order:</p>
<ol class="steps">
<li>Its own sections (premises, organisation, service, parts and accessories, vehicle sales), each with the number of questions answered, unanswered and not applicable.</li>
<li>The actual questions as worded, with its own recorded answer against each. Strengths are shown as visibly as weaknesses.</li>
<li>Why a chosen question is worth attention. A comparison against a group is offered only where the questionnaire and scoring are compatible.</li>
<li>A development priority it chooses, with milestones, an owner and the evidence it decides to keep.</li>
</ol>
<p><b>Three records, and none updates another.</b> The assessment is what was recorded. The development record is what the dealer agreed to do. A later reassessment is a new record. Completing a milestone does not amend an answer, raise a score or prove a commercial outcome. That is what keeps the tool useful before a second assessment round exists. There is no distributor score derived from dealer assessments and no public league table.</p>

<h2><span class="n">3.6</span>Pricing, range and offers</h2>
<p><b>Pricing &amp; Margin Lab.</b> Combines competitive positioning with scenarios the user controls. Parts gross profit is revenue less the parts purchase cost of the quantities sold; freight, duty, overheads and distributor rebates are excluded from that measure, and any extra costs are shown once in a separate view. The quantity needed to preserve revenue or gross profit is an arithmetic threshold, not a forecast. Selling prices and margins further down the channel are never mandatory contributions.</p>
<p><b>Range &amp; Offer Planner.</b> Takes an Atlas selection and turns it into a proposed range decision or Deal of the Day brief: which products, for which accounts or vehicle segments, how Genuine and Best Value are positioned, and what would show that it worked. Execution stays in the existing business. Universe does not become an order platform or a quotation desk.</p>
""")

# ---------------------------------------------------------------- 4 Protecting the deal
H.append(opener(4, "Protecting the deal", "0", "cases recorded in a programme that has paid €90,000 since 2023. The money is labelled. The case is not.",
                ["Don't Lose the Deal at Isuzu Truck UK", "The label, and the missing case", "Rolling it out to every dealer",
                 "What a defended job must leave behind", "The public-tender feed", "One decision closes both"]))
H.append(f"""
<h2><span class="n">4.1</span>Don't Lose the Deal at Isuzu Truck UK</h2>
<p class="lead">Don't Lose the Deal is Isuzu Truck UK's existing programme for competitive quotations: support that helps a dealer keep a job when the customer has a cheaper alternative in front of them. It runs on a memorandum of understanding, a rebate credit note that moves the money, and Japan-side sign-off.</p>
{fig(C.fig_dlod_credits(), "A recurring €30,000 a year, and no case behind any of it.", "ISZE credit notes to Isuzu Truck UK carrying the programme name in the typed reference, June 2023 to March 2026.")}
<p><span class="label m">Measured</span> Five credits carry the programme name: three in 2023 and early 2024 that together make €30,000 for 2023, then €30,000 in February 2025 and €30,000 in March 2026. This is a recurring arrangement, not a one-off. €30,000 is {dlod_share:.2f}% of the {E(ituk_billed / 1e6, 2)}M ISZE billed to Isuzu Truck UK in 2025, which is why the programme is affordable there. The first two 2023 credits carry a slightly different label. One question to Isuzu Truck UK confirms whether they are the same programme, and it should be asked before any baseline for a rollout is fixed.</p>

<h2><span class="n">4.2</span>The label, and the missing case</h2>
<p>The programme name survives in the reference typed on the original invoice records, but the working billing file that everyone searches drops that field. A search there finds nothing, and that is how the programme came to look as if it left no trace. The chain from programme name to billing line is broken in the middle, and a broken chain can be repaired: keep the field.</p>
<p>The deeper gap does not move. <b>Five labelled payments, zero recorded cases:</b> not one part reference, dealer, competitor quote, price gap or won-or-lost outcome. A credit note proves that support was paid. It does not prove that the customer was kept or that anything happened that would not have happened anyway. Anyone who reads rebate volume as a result is reading a payment as an outcome.</p>

<h2><span class="n">4.3</span>Rolling it out to every dealer</h2>
<p>The intent is to run Don't Lose the Deal for every ISZE dealer, with Isuzu Truck UK as the template. That makes the gap urgent: rolled out as it stands, every new market buys the payment and inherits the inability to judge it. The cheapest moment to fix the record is now, while there is one arrangement to amend rather than nineteen.</p>
{table(["Route", "Support per year", "Share of 2025 parts billed"], [
    ["Three largest markets, twelve-month evidence pilot", "€90,000", f"{90000 / billed_2025 * 100:.2f}%"],
    ["All nineteen markets", "€570,000", f"{570000 / billed_2025 * 100:.2f}%"],
], "num")}
<p><span class="label p">Proposed</span> At €30,000 per market a year. The money is affordable. Judging it is the harder part, and three constraints decide the design:</p>
<ul class="plain">
<li><b>The sign-off path, not the cash, is very likely the binding limit.</b> Depending on case size, a network programme generates between roughly eight and 160 approval events a month. The design answer is to agree the envelope once and approve cases locally against a written rule. That is only safe together with the case record below.</li>
<li><b>Cheap cuts both ways.</b> A cost small enough to approve without argument is also small enough to approve without evaluation. Three years of the full network at this level, unmeasured, is about 5% of one year's parts spent on a bet nobody can judge.</li>
<li><b>An uncapped rollout buys activity, not evidence.</b> Record first, then scale.</li>
</ul>

<h2><span class="n">4.4</span>What a defended job must leave behind</h2>
{table(["Field", "Why it cannot be reconstructed later"], [
    ["The part", "Without the reference, the case cannot be tied to a family, the only level at which an outcome can be compared."],
    ["The dealer", "Which account asked, and where. Without it there is no before-and-after."],
    ["The competitor evidence", "What was quoted against us, and when. A price claim with no date is not evidence."],
    ["The outcome", "Won, lost, or no decision. The third state must be visible; it is not a loss."],
    ["Date, support requested and granted", "What was asked for against what was given."],
    ["The follow-on order reference", "Lets a win be verified in the ledger rather than asserted by the person who benefits from the support."],
])}
<p>This takes about five minutes per case, attached to a credit note that is raised anyway: roughly €1,800 to €6,500 a year across the network. It must ride the existing credit-note step rather than become a system with its own login. A record makes a case judgeable; only a before-and-after view makes the programme evaluable.</p>

<h2><span class="n">4.5</span>The public-tender feed</h2>
{fig(C.fig_tender_funnel(), "From public notice to pursuit decision, and then nothing.", "The live public-tender feed, generated 22 September 2026.")}
<p><span class="label m">Measured</span> {st["raw_notices"]} notices reduce to {st["opportunities"]} distinct opportunities, of which {st["aftersales_tagged"]} carry an aftersales signal (a parts, service or maintenance element a distributor could supply). {st["action_queue"]} are in the action queue and {st["due_14d"]} are due within fourteen days. Decisions recorded so far: {dc["Attack"]} attack, {dc["Selective"]} selective, {dc["Watch"]} watch, {dc["Ignore"]} ignore. {st["missing_value_opportunities"]} of the {st["opportunities"]} opportunities carry no value figure, and the paper does not invent one. No outcomes are recorded, so the feed cannot yet show a win rate.</p>
<p>Four rules apply. A tender's advertised value is not expected Isuzu parts revenue, and an award is not parts billed. A notice count is not a pipeline; the deliverable is a qualified shortlist. Every opportunity carries its source and the date it was seen, because a distributor who chases a closed tender stops reading the feed. And declining is a valid outcome, with the reason recorded.</p>
<p><b>The give and the ask.</b> ISZE gives country-relevant opportunities with the aftersales content made visible early enough to act on, and, where it fits, a combined vehicle and aftersales proposal with a headquarters brief that makes the requested decision unmistakable. ISZE asks for one line when a tender is won, lost or ignored.</p>

<h2><span class="n">4.6</span>One decision closes both</h2>
<div class="callout"><p>In both Don't Lose the Deal and the tender feed, the event that matters happens outside ISZE, and the only trace on ISZE's side is a part that eventually ships. ISZE can do everything up to the outcome and nothing after it. <b>Agree to record outcomes, one line per closed case, in one shape both can read.</b> It is not a system, a report or a permission. It is an agreement that when a case closes, one line gets written down.</p></div>
""")

# ---------------------------------------------------------------- 5 Participation
H.append(opener(5, "Participation", f"{ids['rows']}", "dealer self-assessments already exist across 19 networks. That is what this network does when it is asked. Anything harder needs a reason the participant can feel.",
                ["The exchange: what we offer, what we ask", "What ISZE already holds for dealers", "How a dealer joins",
                 "How a distributor joins", "Open for decision: a participation score", "What not to do"]))
H.append(f"""
<h2><span class="n">5.1</span>The exchange: what we offer, what we ask</h2>
<p class="lead">Traction comes from offering something a participant would use even if the reporting obligation disappeared tomorrow. The offer comes first, and it has to be real.</p>
<div class="two">
<div>{table(["What we offer"], [
    ["<b>Dealers.</b> Their own Dealer Standards answers in the real question wording, explorable by section"],
    ["<b>Dealers.</b> A development priority they choose, with milestones and evidence they control"],
    ["<b>Dealers.</b> A prepared review of their own recorded purchasing, with a way to correct it"],
    ["<b>Dealers.</b> A visible record of who owes the next step, including ISZE and the distributor"],
    ["<b>Distributors.</b> A prepared national and network review, monthly, after a usable submission"],
    ["<b>Distributors.</b> Product detail behind any movement, and a Deal of the Day brief on a chosen case"],
    ["<b>Distributors.</b> A tender proposal framework, and a development record per dealer"],
])}</div>
<div>{table(["What we ask in return"], [
    ["<b>The report already sent.</b> Reused, not re-requested; two or three definitions agreed once"],
    ["<b>Corrections.</b> \"Your reading is wrong\" is a successful outcome"],
    ["<b>Maintenance and service data.</b> Which vehicles were serviced and which parts were fitted. It is the one input that turns modelled demand into observed demand"],
    ["<b>Outcomes.</b> One line when a supported deal or tender closes"],
    ["<b>Never asked by default.</b> Dealer resale prices, customer identities, full inventory"],
])}
<p><span class="label p">Proposed</span> Ordinary service is never conditional on any of this.</p></div>
</div>
<p><b>The sentence a dealer principal hears.</b> "A review prepared from your recorded purchases" can sound like "my supplier's supplier is looking at my book". The design answers it directly. The review reaches the dealer only through its distributor, it covers what the distributor already receives, and the dealer decides what, if anything, goes further.</p>

<h2><span class="n">5.2</span>What ISZE already holds for dealers</h2>
{fig(C.fig_ids_hist(), f"{ids['scored']} dealers carry a recorded score, average {ids['avg']:.1f}.", "Isuzu Dealer Standards network lists, September 2026: 519 dealer records across 19 networks, one assessment round.")}
{fig(C.fig_ids_networks(), "Two thirds of the known estate already has an individual result.", "Same source. France, Spain and Switzerland are listed without individual scores; Italy has 7 of 41.")}
<p><span class="label i">Inferred</span> This is the strongest dealer asset in the programme: the only place where ISZE holds something a dealer wants to look at and cannot easily assemble for itself. So the design opens with it. The first thing a dealer sees is its own assessment, not a supplier's reading of its business. The scores are self-assessments from one round with no per-dealer date. They are context, not a performance measure.</p>

<h2><span class="n">5.3</span>How a dealer joins</h2>
<ol class="steps">
<li><b>Through the distributor.</b> The distributor chooses whom to invite. ISZE does not approach a dealer directly.</li>
<li><b>Its own Dealer Standards profile first.</b> The dealer sees its own answers and chooses one development priority.</li>
<li><b>A prepared review, no form.</b> Built from information already held. No registration and no upload in the first session.</li>
<li><b>Ask for a correction, not for data.</b> "Your reading is wrong" and "no action needed" are both successful outcomes.</li>
<li><b>Record the plan.</b> Milestones, owner and evidence, and the record stays with the dealer.</li>
<li><b>Propose the next task, not the next report.</b> A repeat invitation depends on an actual commercial decision.</li>
</ol>
<p>A funded, bounded setup task (€600, section 1.7) gives the dealer's time a price and gives the distributor something to offer rather than something to ask for.</p>

<h2><span class="n">5.4</span>How a distributor joins</h2>
<ol class="steps">
<li><b>A director-level conversation, not a data request.</b> The recurring report is reused; nothing extra is required for the core review.</li>
<li><b>Agree two or three definitions once.</b> Covered accounts, channels and products.</li>
<li><b>Receive the first prepared review</b>, with the question behind it stated.</li>
<li><b>Choose one case</b>: one range, one account pattern or one Deal of the Day, with a named owner on the distributor's side.</li>
<li><b>Extend only where a case needs it</b>, for a defined purpose, with a named recipient and a stated return.</li>
</ol>
<p>Two things turn acceptance into use. Answer a question the distributor already has, because a review that is merely available is not read. And make the distributor's own dealer development the visible output, because that is the framing in which the review serves the distributor's interest rather than ISZE's.</p>

<h2><span class="n">5.5</span>Open for decision: a participation score</h2>
<div class="callout"><p><span class="label p">Proposed, not decided</span> Whether participation should carry a score, what it counts and what it unlocks is still open and is not settled in this paper. No scores are given here. If a score is introduced, four principles would hold:</p>
<ul class="plain">
<li>It counts useful exchange and decisions, not data volume, logins or uploads.</li>
<li>Each participant sees its own score. There is no public league table.</li>
<li>Ordinary service never depends on it.</li>
<li>Candidate components, for discussion: the agreed report on time and complete; corrections made; maintenance and service data shared; a tool used for a named decision; outcomes recorded.</li>
</ul></div>

<h2><span class="n">5.6</span>What not to do</h2>
{table(["Do not", "Why"], [
    ["Pay per submitted record, row or field", "It rewards disclosure volume rather than useful work"],
    ["Make ordinary service conditional on contribution", "It turns a normal service into a bargaining chip and destroys the premise"],
    ["Build a public dealer league table", "Turnover favours large businesses, and assessment coverage differs by market"],
    ["Ask for dealer resale prices by default", "Not needed for the core review, and the most sensitive item on the list"],
    ["Approach a dealer directly", "The distributor owns the relationship and the audience decision"],
    ["Count logins or uploads as participation", "Neither is evidence that a decision improved"],
])}
""")

# ---------------------------------------------------------------- 6 Money
H.append(opener(6, "The money", "0.31%", "of one year's parts billing: the size of the €100,000 route. The right size for a pilot, and the wrong size for a platform.",
                ["The denominator", "The hurdle", "The price of a dealer", "The existing rebate floor", "Which route"]))
H.append(f"""
<h2><span class="n">6.1</span>The denominator</h2>
{fig(C.fig_denominator(), "Every envelope in this paper is under 2% of one year's billing.", f"ISZE parts billed to {n_db} distributors, calendar 2025, {E(billed_2025, 2)}. The Don't Lose the Deal routes are at €30,000 per market a year.")}
<p><span class="label m">Measured</span> ISZE billed {E(billed_2025, 2)} of parts to {n_db} distributors in 2025. The €100,000 route is 0.31% of that and the €300,000 route 0.93%. The programme does not need to move the whole business to justify itself, and it must not be presented as if it will.</p>

<h2><span class="n">6.2</span>The hurdle</h2>
{fig(C.fig_hurdle(), "At €2,500 per beneficial action, the €100,000 route needs 40.", "Illustrative arithmetic: envelope ÷ assumed contribution per action. The contribution is an assumption, not an estimate of dealer profitability.")}
<p><span class="label p">Illustrative</span> At €500 per beneficial action the €100,000 route needs 200 of them and the €300,000 route 600. At €5,000, 20 and 60. The honest break-even for €100,000 is <b>40 qualifying actions at €2,500 each</b>. That number belongs in the funding discussion, not in a footnote after approval. A pilot of ten Deals of the Day at €2,500 each is €25,000 against €100,000: it establishes whether the mechanism produces qualifying actions at all. The hurdle is higher again once internal time is included, so report the cash-only and the fully costed comparison separately.</p>

<h2><span class="n">6.3</span>The price of a dealer</h2>
{fig(C.fig_price_of_dealer(), "The same €15,000 is a gesture or a programme, depending on where it goes.", "Dealer counts from the Dealer Standards network lists, September 2026: 519 in total, 44 at Isuzu Truck UK, 16 in Portugal.")}
<p><span class="label i">Inferred</span> €15,000 spread across 519 dealers is €28.90 each and buys nothing that survives contact with a dealer principal. The same €15,000 spent as twenty-five accepted setup tasks at €600 in two pilot markets buys twenty-five completed onboarding experiences. Same money, completely different product. The recommendation is the second.</p>

<h2><span class="n">6.4</span>The existing rebate floor</h2>
<p><span class="label m">Measured</span> In 2025 a share of the normal distributor rebate was tied to a major performance submission, and the submission arrived. That is the floor: the file exists because the rebate depends on it. Nothing in that arrangement gives a distributor a reason to open anything, correct anything or send anything the rebate does not name. The euro value of that share is not stated in this paper. It should be added before the funding discussion, so the programme is weighed against the incentive already being paid.</p>

<h2><span class="n">6.5</span>Which route</h2>
<p><span class="label p">Proposed</span> Start at the €100,000 route and re-point its Deal of the Day element as set out in section 1.7. The €300,000 route adds dealer enablement and resilience before anyone knows how often a Deal of the Day qualifies, so it should wait for that rate. Nothing here is a new budget request or an approved expenditure. It is a recommendation inside the existing €0, €100,000 and €300,000 planning envelopes.</p>
""")

# ---------------------------------------------------------------- 7 Decisions
H.append(opener(7, "Decisions, and when to stop", "3", "decisions this month, one order to build in, and one stop condition that does not bend.",
                ["The three decisions", "The build order", "Go, no-go and stop", "Ownership and the unowned answer",
                 "Delivery, competition and privacy", "What is still unknown"]))
H.append(f"""
<h2><span class="n">7.1</span>The three decisions</h2>
{table(["Decision", "Recommendation", "What has to be true first"], [
    ["<b>Fund Deal of the Day</b>", "€60,000 to €90,000 as a named line inside the €100,000 route, with a €150,000 floor per Deal of the Day", "The selection rule is agreed and the first Deal of the Day is named"],
    ["<b>Approach ten dealers</b>", "Through the distributor, opening with the dealer's own Dealer Standards profile and a prepared review", "A prepared review exists from data already held"],
    ["<b>Build two tools first</b>", "Parts Atlas and Dealer Standards Studio", "The classification is fixed to one named release"],
])}

<h2><span class="n">7.2</span>The build order</h2>
{table(["Stage", "Result", "Evidence needed to move on"], [
    ["1. Agree scope and portfolio", "Five tools and the written exclusion of routine service", "This paper and the presentation say the same thing"],
    ["2. Fix the classification release", "One named version and build date", "A family and product-form view reproduces from it"],
    ["3. Open two prepared views", "An Atlas view and a Dealer Standards profile, ready before the first invitation", "A participant completes a real task and finds it clearer than today's review"],
    ["4. Run the dealer sample", "Ten dealers in two markets, including one reluctant to add reporting work", "Corrections, useful output, total effort and reasons for non-use, all recorded"],
    ["5. Run Deal of the Day", "At least two Deals of the Day above the floor", "Contribution measured on the same scope before, during and after, including returns"],
    ["6. Record outcomes", "One case record for Don't Lose the Deal and tenders", "Cases closing with the fields in section 4.4"],
    ["7. Evaluate, then extend or narrow", "A stated result, favourable or not", "Real evidence of effort and usefulness, not a rendered screen"],
])}
<p>The order is a dependency order, not a schedule. Stage 2 blocks stage 3. No earlier week estimate is carried over as a promise.</p>

<h2><span class="n">7.3</span>Go, no-go and stop</h2>
<div class="callout"><p><b>Go</b> if, at the pilot review, a real participant completed a real analytical task, the output was correct against its source, and the participant can name the decision it changed.</p>
<p><b>No-go</b> if the only evidence is that a screen rendered, a file arrived, or somebody said the demonstration looked good.</p>
<p><b>Stop</b> if, after two eligible cycles, no participant can name a decision the tool changed, or if a confidentiality or identity weakness cannot be closed. The programme stops. It does not pause, add a report, or widen the population to look for a better sample.</p>
<p>The honest test underneath all of it: <b>if the incentive that produces the file today were removed tomorrow, would anyone open the tool anyway?</b></p></div>

<h2><span class="n">7.4</span>Ownership, and the unowned answer</h2>
<p>The commercial question, the design of the exchange, the analytical examples and the definition of a useful output are owned inside ISZE Parts. Specialist work is bounded, each piece a task with an accepted deliverable and a handover: access isolation, durable shared records, reliable imports, recovery, and any connection to company systems. Existing classification, analytics and Dealer Standards work is reused where fit for purpose, not rebuilt.</p>
<p><b>What no amount of software closes is the answer.</b> The product pays off when ISZE answers a participant's question, and nobody has yet been named, given hours, or funded to do that. Software is cheap at the margin and a person's time is not. The risk is that the cheap half gets built, the expensive half gets deferred, and the product arrives looking complete while the thing it was for never happens.</p>

<h2><span class="n">7.5</span>Delivery, competition and privacy</h2>
<p><b>Delivery.</b> There is no production system yet: no shared case service, no production identity, no attachment storage. The access rules that matter (only the authorised distributor sees its own accounts and terms, only the dealer sees its own record, no distributor sees another's submissions) must be enforced by the operating application and by what exports contain, not by hidden menus. Until that is built and independently reviewed, the first shared use stays distributor-led and document-based.</p>
<p><b>Competition law.</b> Under the European motor-vehicle block exemption framework, the current regime runs until 31 May 2028. Nothing here is a legal determination, and the design has not yet been reviewed for competition-law compliance. Three standing rules are proposed: <b>no exclusivity in exchange for information</b>; <b>no price coordination between distributors</b>, so Universe compares a distributor with its own history and permitted aggregates and never passes one distributor's terms or plans to another; and <b>no resale-price instruction</b>, so ISZE sets its net price to the distributor and Universe neither prescribes nor keeps dealer resale prices. The responsible function reviews this before any shared output is used with a participant.</p>
<p><b>Privacy.</b> The recurring exchange is price-free by default. Selling prices, resale margins, customer identities, vehicle identifiers, full inventory and workshop job cards are never added silently. Where a financial outcome is needed, a locally calculated aggregate may be enough, and an aggregate is not automatically anonymous.</p>

<h2><span class="n">7.6</span>What is still unknown</h2>
{table(["Unknown", "Why it matters"], [
    ["Who answers the participant's question", "The product pays off only when someone does, and the money depends on it"],
    ["How often a Deal of the Day qualifies", "It is the number that decides whether expansion is warranted"],
    ["Whether a dealer returns after the first task", "It is the stop test, and it has never been observed"],
    ["Whether a defended job would otherwise have been lost", "Without it, Don't Lose the Deal spend cannot be read as a return"],
    ["Why a customer bought elsewhere", "The question behind every commercial gap; the billing system never recorded it"],
    ["Whether a distributor's dealers cover the vehicles that buy a part", "Without it, a coverage statement is a guess"],
    ["Whether a participation score is introduced, and what it unlocks", "Open for decision (section 5.5)"],
    ["The euro value of the rebate share tied to reporting", "Needed to weigh the programme against the incentive already paid"],
])}
""")

# ---------------------------------------------------------------- reference
H.append(f"""
<h2 class="newpage">Reference: terms used in this paper</h2>
{table(["Term", "Meaning"], [
    ["Parts billed", "ISZE sales to the stated distributor"],
    ["Sales to dealer", "The distributor's recorded onward sales to its dealers; not what a dealer sold to a customer"],
    ["Parts gross profit", "Revenue less the parts purchase cost of the quantities sold; freight, duty, overheads and distributor rebates excluded"],
    ["Contribution", "Parts gross profit less extra Deal of the Day costs not already included"],
    ["Reference price", "The applicable list reference for the entity and period. A reference valuation is not a transaction"],
    ["Deep concession", "A billed price at least 20% under the reference price, on a line that carries one"],
    ["Best Value parts", "The lower-priced counter part sold alongside Genuine. A pairing is a catalogue relationship, not a fitment approval"],
    ["Maintenance parts (PMS)", "Periodic maintenance and service parts: filters, brakes, clutch and related wear parts"],
    ["Target spend per truck", "A modelled expectation of what a market could spend per vehicle, which depends on assumptions"],
    ["Eligible fleet", "The vehicles a selected part actually applies to; never allocated from a national total"],
    ["Qualifying Deal of the Day", "One whose eligible billing base is above the stated floor"],
    ["Isuzu Truck UK / Isuzu UK", "Two separate UK distributors, trucks and pickups respectively, never combined"],
    ["Calendar and fiscal year", "Isuzu's fiscal year runs April to March. The historical examples here compare full calendar years"],
])}
<h3>Where the numbers come from</h3>
{table(["Source", "Used for"], [
    ["ISZE billing to distributors, calendar 2023 to 2026", "Parts billed, the brake-pad and clutch-kit examples, the denominator, the Don't Lose the Deal credits"],
    ["ISZE maintenance-parts pricing analysis, 2024 and 2025", "Deep concession by distributor and family, the Isuzu UK air-filter case, the price-response measurement"],
    ["Target spend per truck model, 2025", "The modelled ceiling and the share resting on the flat per-truck assumption"],
    ["Isuzu Dealer Standards network lists, September 2026", "Dealer counts, score distribution, the price of a dealer"],
    ["Public-tender feed, 22 September 2026", "The tender funnel and recorded decisions"],
    ["Don't Lose the Deal network rollout design, September 2026", "Rollout routes, approval volume and the cost of the case record"],
])}
<p class="src">Every chart in this paper is drawn from these records at the time the paper was produced. Historical observations keep their original period. Tool designs, journeys and funding lines are proposals as of 23 September 2026.</p>
""")

BODY = "\n".join(H)


def page_html(toc_rows):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Isuzu Universe white paper</title>
<style>{CSS}</style></head><body>{BODY.replace("@@TOC@@", toc_rows)}</body></html>"""


def render(html_text, pdf_path):
    with open(HTML, "w", encoding="utf-8") as fh:
        fh.write(html_text)
    prof = tempfile.mkdtemp(prefix="chrome_prof_")
    url = "file:///" + HTML.replace("\\", "/")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    "--proxy-server=127.0.0.1:9", "--virtual-time-budget=5000", f"--user-data-dir={prof}",
                    f"--print-to-pdf={pdf_path}", url], check=True, capture_output=True)


def toc_rows(pages):
    rows = []
    for no, title in CHAPTERS:
        rows.append(f'<tr><td class="no">{no:02d}</td><td>{title}</td><td class="pg">{pages.get(no, "")}</td></tr>')
    rows.append(f'<tr><td class="no"></td><td>Reference: terms and sources</td><td class="pg">{pages.get("ref", "")}</td></tr>')
    return "".join(rows)


def find_pages(pdf):
    doc = fitz.open(pdf)
    out = {}
    for i, pg in enumerate(doc):
        txt = pg.get_text()
        flat = re.sub(r"\s", "", txt).upper()
        for no, _ in CHAPTERS:
            if f"CHAPTER{no:02d}" in flat and no not in out and i > 2:
                out[no] = i + 1
        if "Reference: terms used in this paper" in txt:
            out["ref"] = i + 1
    return out, len(doc)


if __name__ == "__main__":
    tmp = OUT_PDF + ".pass1.pdf"
    render(page_html(toc_rows({})), tmp)
    pages, n = find_pages(tmp)
    render(page_html(toc_rows(pages)), OUT_PDF)
    pages2, n2 = find_pages(OUT_PDF)
    os.remove(tmp)
    assert pages == pages2, (pages, pages2)
    print("pages", n2, "chapters", pages2)
    os.makedirs(QA, exist_ok=True)
    for f in os.listdir(QA):
        os.remove(os.path.join(QA, f))
    doc = fitz.open(OUT_PDF)
    for i, pg in enumerate(doc):
        pg.get_pixmap(dpi=70).save(os.path.join(QA, f"p{i + 1:02d}.png"))
    text = "\n".join(p.get_text() for p in doc)
    banned = [r"\bcampaign", r"\bAIM\b", r"\bPRISM\b", r"\bDLOD\b", r"\bDLAD\b", r"\bIDS\b", r"\.csv", r"\.json", r"\.md\b",
              r"\.py\b", r"_build", r"internal draft", r"business owner", r"snapshot", r"checks, 0 fail", r"megaprompt",
              r"workspace", r"\bGPS\b", r"\bBVP\b", r"\bIML\b", r"\bITUK\b", r"\bIUK\b"]
    for b in banned:
        hits = re.findall(r".{0,40}" + b + r".{0,40}", text, flags=re.I)
        print(f"  banned {b!r}: {len(hits)}" + (f"  e.g. {hits[0]!r}" if hits else ""))
    print("done", OUT_PDF)
