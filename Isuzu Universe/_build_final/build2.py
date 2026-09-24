# -*- coding: utf-8 -*-
"""Isuzu Universe - the white paper, edition 2 (23 September 2026).

Built as a build-up: the OEM's data problem -> sales to dealer as an exchange -> dealers and
their maintenance data -> Deal of the Day as the engagement engine -> tools -> engagement design ->
money and return -> decisions.

Run:  python build2.py
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

OUT_PDF = os.path.join(ROOT, "ISUZU_UNIVERSE_WHITE_PAPER_FINAL_v2_2026-09-23.pdf")
HTML = os.path.join(HERE, "white_paper_final_v2.html")
QA = os.path.join(HERE, "_qa2")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ------------------------------------------------------------------ numbers (all from source)
ids = C.ids_stats()
n_db, billed_2025 = C.network_total()
cov = C.s2d_coverage()
pms = C.pms_capture_2025()
c25, c24 = C.concession_totals("2025"), C.concession_totals("2024")
iuk = C.iuk_air()
pads = C.ituk_portugal_iuk()[("ITUK", "brake_pad")]
pad24, pad25 = float(pads["total_eur_2024"]), float(pads["total_eur_2025"])
q24, q25 = float(pads["total_qty_2024"]), float(pads["total_qty_2025"])
split = C.brake_split_values()
split_tot = sum(v for _, v in split)
pt = C.portugal_values()
el = C.elasticity()
br = el["AIM: Brakes"]
st, dc, oc = C.tender_stats()
ituk_billed, dlod_share = C.dlod_ituk_share()
gps = C.gps_2025()
ceiling = sum(float(r["max_spend_eur"] or 0) for r in gps)
placeholder = [r for r in gps if r["uio_units"] and float(r["uio_units"] or 0) > 0 and r["max_spend_eur"]
               and abs(float(r["max_spend_eur"]) / float(r["uio_units"]) - 250) < 0.01]
placeholder_eur = sum(float(r["max_spend_eur"]) for r in placeholder)
iuk_filters_2025 = sum(float(r["billed_eur"]) for r in C.load("pms_campaign_suspect_by_db_family_2024_2025.csv")
                       if r["year"] == "2025" and r["distributor_code"] == "IUK" and r["pms_category"].endswith("filter"))
dl = C.ituk_dealers()

assert abs(pad24 - 347389.58) < 0.01 and abs(pad25 - 302366.25) < 0.01
assert abs(billed_2025 - 32381311.55) < 0.01 and n_db == 22
assert ids["rows"] == 519 and ids["scored"] == 490
assert len(cov["y25"]) == 6 and len(cov["any"]) == 7 and len(dl) == 64

E = C.eur
K = C.eurk
pct = lambda a, b: (b - a) / a * 100  # noqa: E731
logo = base64.b64encode(open(os.path.join(ROOT, "_assets", "isuzu_logo_white.png"), "rb").read()).decode()
no_data = n_db - len(cov["any"])


# ------------------------------------------------------------------ helpers
def fig(svg, caption, source):
    return f'<figure>{svg}<figcaption><b>{caption}</b> <span class="src">{source}</span></figcaption></figure>'


def table(head, rows, cls=""):
    h = "".join(f"<th>{x}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


PARTS, CHAPS = [], []


def part(no, roman, title, key, keyline, chapters):
    PARTS.append((no, roman, title))
    secs = "".join(f"<li>{s}</li>" for s in chapters)
    return f"""
<section class="opener">
  <div class="op-no">{roman}</div>
  <div class="op-mark">Part {roman}</div>
  <h1 class="op-title">{title}</h1>
  <div class="op-rule"></div>
  <div class="op-key">{key}</div>
  <div class="op-keyline">{keyline}</div>
  <ul class="op-secs">{secs}</ul>
</section>"""


def chapter(no, title, lead):
    CHAPS.append((no, title))
    return f'<div class="chap"><div class="chno">Chapter {no}</div><h1 class="chtitle">{title}</h1><p class="lead">{lead}</p></div>'


CSS = open(os.path.join(HERE, "build.py"), encoding="utf-8").read().split('CSS = """', 1)[1].split('"""', 1)[0]
CSS += """
.chap { break-before: page; margin-bottom: 4mm; }
.chno { font-size: 8.5pt; letter-spacing: .22em; text-transform: uppercase; color: #D71920; font-weight: bold; }
.chtitle { font-size: 22pt; line-height: 1.12; color: #24282C; margin: 1.5mm 0 3mm; }
.chap .lead { border-left: 3px solid #D71920; padding-left: 4mm; }
.ladder { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; margin: 3mm 0 4mm; break-inside: avoid; }
.ladder .col h4 { margin: 0 0 2mm; font-size: 10pt; color: #fff; background: #24282C; padding: 1.8mm 3mm; }
.rung { display: grid; grid-template-columns: 9mm 1fr; border-bottom: .6px solid #E4E5E7; padding: 1.8mm 0; font-size: 8.5pt; }
.rung .lv { font-weight: bold; color: #D71920; font-size: 11pt; }
.rung .g { color: #6B7078; }
.tag { display: inline-block; font-size: 7pt; font-weight: bold; padding: .3mm 1.4mm; border-radius: 1mm; white-space: nowrap; }
.t-live { background: #24282C; color: #fff; } .t-proto { background: #B9BDC3; color: #24282C; } .t-build { background: #D71920; color: #fff; }
.flow { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3mm; margin: 3mm 0 4mm; break-inside: avoid; }
.flow div { background: #F5F5F4; border-top: 3px solid #24282C; padding: 2.5mm 3mm; font-size: 8.6pt; }
.flow div.r { border-top-color: #D71920; background: #FBEDED; }
.flow h5 { margin: 0 0 1mm; font-size: 9.2pt; color: #24282C; }
"""

H = []
# ================================================================== COVER
H.append(f"""
<section class="cover">
  <img class="logo" src="data:image/png;base64,{logo}" alt="Isuzu">
  <div class="kicker">ISZE PARTS EUROPE  ·  WHITE PAPER</div>
  <h1>Isuzu Universe</h1>
  <div class="sub">We see every part leave our warehouse. After the distributor's invoice, we see almost nothing. Universe is how we earn the rest.</div>
  <div class="rule"></div>
  <div class="hero">{C.fig_visibility(dark=True)}
    <div class="herocap"><b>What ISZE can see of its own aftermarket, 2025, as a share of the {E(billed_2025 / 1e6, 1)}M billed to {n_db} distributors.</b>
    Named-dealer detail exists for one distributor. Nothing reaches us from the workshop or the end customer.</div>
  </div>
  <div class="settles">
    <div>Why an OEM that cannot see its dealers cannot manage its aftermarket</div>
    <div>Sales to dealer: a two-way exchange the distributor also wins from</div>
    <div>Dealers and their maintenance data, and Deal of the Day as the lever</div>
    <div>What we can build, how we get everyone in, and what it must return</div>
  </div>
  <div class="by"><span>Prepared by <b>Jérôme Van der Pluym</b>, VP Sales, ISZE</span><span>23 September 2026</span></div>
</section>
""")

# ================================================================== SUMMARY
H.append(f"""
<h2>The paper on one page</h2>
<p class="lead">The argument builds in five steps. Each one is the reason for the next.</p>
<ol class="steps">
<li><b>We cannot see our own aftermarket.</b> ISZE, part of Isuzu Motors, billed {E(billed_2025, 2)} of parts to {n_db} distributors in 2025. Only {len(cov['y25'])} of them sent any sales-to-dealer data for 2025, and only one sent it by named dealer ({cov['named_eur'] / billed_2025 * 100:.1f}% of billing). Some do not track it at all. We already tie 20% of the normal distributor rebate to KPI reporting, and it buys a file, not a habit.</li>
<li><b>The next big thing is sales-to-dealer data, as an exchange.</b> The distributor knows which dealer bought which parts and which dealer sold which trucks. ISZE knows the parts, the service intervals and the fleet. Together, and only together, that shows which dealer is losing maintenance business. We give the distributor that view of its own network, so it can develop its dealers, and it sends us the data that makes the view possible.</li>
<li><b>Dealers bring the workshop.</b> Maintenance records are the one source that turns modelled demand into observed demand. Dealers share them when they get something back: their own Dealer Standards profile, a service-due list, a workshop benchmark and better offers.</li>
<li><b>Deal of the Day is the engine.</b> A prepared, time-limited offer that pays only on extra volume. Measuring extra volume needs a baseline, and the baseline is sales-to-dealer data. The data ask is built into the offer rather than bolted on.</li>
<li><b>It has to pay back.</b> One point of maintenance-parts capture across the modelled network is worth about {K(pms['point'])} of revenue a year. The €100,000 route is 0.31% of one year's billing. The money is released in stages, against gates that measure data, use and return.</li>
</ol>
{table(["Decision this month", "Recommendation"], [
    ["<b>1. Re-point the KPI rebate</b>", "Link the existing 20% rebate share to a monthly sales-to-dealer standard (part × dealer), in tiers. No new money."],
    ["<b>2. Fund Deal of the Day</b>", "A named line of €60,000 to €90,000 inside the €100,000 route. Only Deals of the Day above €150,000 of eligible billing, and only with a sales-to-dealer baseline."],
    ["<b>3. Start with two distributors and ten dealers</b>", "Isuzu Truck UK (named-dealer data exists) and one more that commits to the standard. Build the dealer maintenance scorecard and the Dealer Standards Studio first."],
])}
<p><b>What this paper does not claim.</b> No realised return, no approved budget, no forecast of extra sales, and no participant has agreed to anything. Figures marked <i>illustrative</i> are arithmetic on stated inputs, not forecasts.</p>
""")

H.append("""<section class="newpage"><h2>Contents</h2><table class="toc">@@TOC@@</table>
<div class="callout" style="margin-top:8mm"><p><b>How to read the evidence.</b>
<span class="label m">Measured</span> is counted in ISZE's own records. <span class="label i">Inferred</span> is a conclusion drawn from measured data.
<span class="label p">Proposed</span> is a design or decision not yet taken. <span class="label i">Reported</span> is what the ISZE team knows from working with distributors but has not measured.
Where something is unknown, the paper says so.</p></div></section>""")

# ================================================================== PART I
H.append(part(1, "I", "The problem", f"{cov['named_eur'] / billed_2025 * 100:.1f}%",
              "of what ISZE bills can be followed to a named dealer. For the rest, the invoice is where our sight ends.",
              ["1 · What an OEM cannot see", "2 · What detail shows when we have it"]))

H.append(chapter(1, "What an OEM cannot see",
                 "Isuzu Motors Europe sells parts to distributors, and distributors sell them to dealers. We know exactly what leaves our warehouse. After the distributor's invoice, our view goes dark."))
H.append(f"""
<h2><span class="n">1.1</span>Where our sight stops</h2>
{fig(C.fig_visibility(), "Five layers of the aftermarket, and how much of each ISZE can see.", f"Share of the {E(billed_2025, 2)} billed to {n_db} distributors in calendar 2025. Sales-to-dealer detail: the files distributors sent for 2025.")}
<p><span class="label m">Measured</span> In 2025 ISZE billed {E(billed_2025, 2)} of parts to {n_db} distributors. {len(cov['y25'])} of them sent any 2025 sales-to-dealer data: together {E(cov['y25_eur'] / 1e6, 1)}M, or {cov['y25_eur'] / billed_2025 * 100:.1f}% of billing. Five of those six send national quantities per part number and nothing below it. Only Isuzu Truck UK sent data by named dealer: {len(dl)} dealers, for one year, covering {cov['named_eur'] / billed_2025 * 100:.1f}% of billing. The other {no_data} distributors send nothing below the invoice. Nothing reaches ISZE from a dealer's sales to its customers, and ISZE holds one dealer's workshop records, obtained once.</p>
<p><span class="label i">Reported</span> Some distributors do not track their sales to dealers at part level at all. For them the problem is not willingness to share: there is nothing to share yet.</p>

<h2><span class="n">1.2</span>What we already pay to see</h2>
<p><span class="label m">Measured</span> Since 2025, 20% of the normal distributor rebate is linked to reporting a set of major KPIs. It works as a floor: the file arrives, because the rebate depends on it. It does not buy part-by-dealer detail, a monthly rhythm, or anything the distributor uses itself, so the file is as thin as the condition allows. For years ISZE has asked for information and returned too little visible value for the request to stay alive.</p>
<div class="callout"><p><b>A reporting obligation can start an exchange. Only a useful tool keeps it going.</b> The test for everything in this paper: if the rebate condition disappeared tomorrow, would the distributor still send the data, because it wants what comes back?</p></div>

<h2><span class="n">1.3</span>What not seeing costs</h2>
{table(["Blind spot", "What it means today"], [
    ["Which dealer is losing maintenance business", f"Impossible to say outside one market. No distributor sends trucks sold or serviced per dealer, so no dealer can be measured against its own fleet."],
    ["How much of the maintenance market ISZE supplies", f"<span class='label i'>Modelled</span> ISZE supplied about {pms['capture']:.0f}% of the modelled need for the maintenance-parts families in {pms['dbs']} markets in 2025. Where the other {100 - pms['capture']:.0f}% goes (aftermarket, other channels, or services not done) cannot be seen."],
    ["The size of the prize", f"{placeholder_eur / ceiling * 100:.0f}% of the modelled target-spend ceiling ({K(placeholder_eur)} of {K(ceiling)}) rests on a flat €250-per-truck assumption, because those markets report no purchasing rate."],
    ["Whether a price change worked", "Price response can only be measured on ISZE-to-distributor stocking, not on dealer demand, so pricing decisions run on thresholds, not evidence."],
    ["Whether support paid off", "€90,000 of Don't Lose the Deal credits since 2023 and 199 tender opportunities in the queue, with zero recorded outcomes."],
])}
<p><span class="label i">Inferred</span> Every one of these gaps closes on the same two sources: <b>sales to dealer, by part and dealer</b>, and <b>what the workshop actually fitted</b>. That is where the rest of this paper goes.</p>
""")

H.append(chapter(2, "What detail shows when we have it",
                 "Before asking anyone for more data, this chapter shows what it does when it exists. Every example rests on a new parts classification system built by Jérôme Van der Pluym. It places every Isuzu part number in a family, a product group and a product form, and keeps Genuine and Best Value side by side."))
H.append(f"""
<h2><span class="n">2.1</span>Isuzu Truck UK brake pads</h2>
{fig(C.fig_brake_pads(), f"Value fell {abs(pct(pad24, pad25)):.1f}%. Units fell {abs(pct(q24, q25)):.1f}%.", "ISZE billing to Isuzu Truck UK, brake pads, full calendar 2024 and 2025.")}
<p><span class="label m">Measured</span> Brake pads billed to Isuzu Truck UK fell from {E(pad24, 2)} in 2024 to {E(pad25, 2)} in 2025, while units fell from {q24:,.0f} to {q25:,.0f}. A revenue view suggests a demand problem, a volume view suggests a price problem, and neither is the right first question. Across the three braking categories, {E(split_tot, 2)} was lost, and pads are {split[0][1] / split_tot * 100:.1f}% of it. The starting sentence changes from "braking is down" to "brake pads are down", which a distributor can act on.</p>

<h2><span class="n">2.2</span>Portugal clutch kits: a mistake prevented</h2>
{fig(C.fig_portugal(), "The line grew while Genuine fell.", "ISZE billing to the Portuguese distributor, clutch kits, full calendar 2024 and 2025.")}
<p><span class="label m">Measured</span> Combined clutch-kit billing rose {pct(pt['total_eur_2024'], pt['total_eur_2025']):+.1f}% while Genuine fell from {E(pt['genuine_eur_2024'], 2)} to {E(pt['genuine_eur_2025'], 2)}; units were flat at {pt['total_qty_2024']:,.0f} and {pt['total_qty_2025']:,.0f} kits. A Genuine-only view would have launched a recovery action for a business that grew. Here the tool earns its place by preventing a mistake.</p>

<h2><span class="n">2.3</span>The ranked family view</h2>
{fig(C.fig_family_ranked(), "Where the maintenance-parts money is, and where it is discounted.", "ISZE billing of maintenance parts with a reference price, 24 distributors, calendar 2025. Ten largest families.")}
<p><span class="label m">Measured</span> Front brake pads (36.0% of €423k) and blower filters (25.2% of €374k) carry heavy concession on modest bases: a handful of large deals, not a pricing position. Brake rotors (3.4% of €1.30M) and oil filters (1.5% of €557k) carry almost none. Their pricing is settled, and if they hold an opportunity it lies in coverage, which is exactly what ISZE cannot see without dealer data.</p>
<div class="callout"><p><b>The point of Part I.</b> At distributor level, detail already changes decisions. Everything in the next part is about taking the same detail one level down, to the dealer, where the maintenance business is actually won or lost.</p></div>
""")

# ================================================================== PART II
H.append(part(2, "II", "The exchange", f"{len(dl)} dealers",
              "at Isuzu Truck UK are the only named dealers ISZE can see. The next big thing is to see all of them, with the distributor, for the distributor.",
              ["3 · The next big thing: sales to dealer", "4 · Bringing the dealers in: maintenance data"]))

H.append(chapter(3, "The next big thing: sales to dealer",
                 "Give the distributor a view of its own dealer network that it cannot build alone, and it will send the data that makes the view possible. That is the whole value proposition."))
H.append(f"""
<h2><span class="n">3.1</span>Two halves of one answer</h2>
<div class="flow">
  <div><h5>The distributor holds</h5>Which dealer bought which part, when, and how many. Which dealer sold which trucks, and where they are serviced.</div>
  <div><h5>ISZE holds</h5>The parts classification, service intervals per model, the fleet in service, reference and competitor prices, and benchmarks across 22 networks.</div>
  <div class="r"><h5>Together</h5>For every dealer: how many maintenance parts its trucks should need, how many it bought, and where the gap is.</div>
</div>
<p>Neither side can answer <i>"which of my dealers is losing maintenance business?"</i> alone. The distributor knows it sold many trucks through a dealer, but not what those trucks should consume. ISZE knows what a truck consumes, but not which dealer looks after it. The exchange is that simple, and it serves the distributor first: developing its dealers is its job, and this is the tool for it.</p>

<h2><span class="n">3.2</span>Where we are weak, seen from the market</h2>
{fig(C.fig_oil_capture(), "Oil filters: every service needs one, so the gap is the cleanest signal.", "Units billed by ISZE against units the fleet model expects from vehicles in service and service intervals, calendar 2025. Red: under 50%. Ireland is left out because the model base there gives a figure above 100%, which means the base is wrong, not that capture is complete.")}
<p><span class="label i">Modelled</span> In Germany ISZE supplies about 15% of the oil filters the fleet should need, at Isuzu UK 38%, and in Greece 97%. This is as far down as ISZE can see today. Inside each market, some dealers will be near 100% and others near zero. The distributor average hides both, and the market view cannot tell them apart.</p>

<h2><span class="n">3.3</span>What the one dealer-level market already shows</h2>
{fig(C.fig_ituk_dealers(), "The spread across dealers is wide, and we cannot yet say who is strong.", "Isuzu Truck UK sales to its dealers, calendar 2025, valued at ISZE's average selling price per part.")}
<p><span class="label m">Measured</span> Isuzu Truck UK's {len(dl)} dealers bought {E(sum(dl) / 1e6, 2)}M of parts from their distributor in 2025. The ten largest took {sum(dl[:10]) / sum(dl) * 100:.1f}% of it, and the median dealer bought {K(dl[len(dl) // 2])}. What this cannot tell us is whether a dealer buying {K(dl[len(dl) // 2])} is doing well. That depends on how many trucks it looks after, and the distributor has that number in its own vehicle sales.</p>

<h2><span class="n">3.4</span>The product: a dealer maintenance scorecard</h2>
<p><span class="label p">Proposed</span> One page per dealer, owned by the distributor, refreshed monthly:</p>
{table(["Line", "Where it comes from"], [
    ["Trucks sold through this dealer, by model and year", "Distributor (its own vehicle sales)"],
    ["Maintenance parts those trucks should need this year, by family", "ISZE (service intervals × fleet model × classification)"],
    ["Maintenance parts the dealer actually bought, by family, Genuine and Best Value", "Distributor (sales to dealer)"],
    ["Dealer maintenance capture, by family, against its country and anonymous network peers", "Both"],
    ["Local competitor price position on the families where capture is low", "ISZE (public online price monitoring)"],
    ["The dealer's Dealer Standards result on the parts and service sections", "ISZE (Isuzu Dealer Standards)"],
    ["Suggested action: a visit, a stock review, a Deal of the Day", "Both, decided by the distributor"],
])}
<p><span class="label p">Illustrative</span> A dealer sold 400 trucks over five years. The model says those trucks need about 800 oil filters a year; the dealer bought 180 from its distributor. That is 23% capture, while the country sits at 60%. The distributor now knows which dealer to visit, which family to talk about, and whether price is the problem. Illustrative figures, not a real dealer.</p>

<h2><span class="n">3.5</span>The exchange with the distributor</h2>
{table(["The distributor gives", "The distributor gets"], [
    ["Sales to dealer, monthly, by part number and dealer (any format)", "The dealer maintenance scorecard for every dealer"],
    ["Trucks sold per dealer, by model and year", "The Parts Atlas: its own business by family, product form, Genuine and Best Value"],
    ["Two or three definitions, agreed once", "A monthly network review in its own language, prepared, not requested"],
    ["One line when a supported deal or tender closes", "Deal of the Day, prepared and part-funded (chapter 5)"],
    ["", "The 20% KPI rebate share, released on the data standard (chapter 7)"],
])}
<p>Ordinary service (availability questions, part lookups, day-to-day quotations) is never conditional on any of this. It stays in the existing business, and a distributor that sends nothing still gets it. Universe is what comes on top.</p>
""")

H.append(chapter(4, "Bringing the dealers in: maintenance data",
                 "Sales to dealer shows what a dealer bought. Maintenance data shows what the workshop actually did: which trucks came in, which parts went on, and which parts did not come from us. It is the one source that turns modelled demand into observed demand."))
H.append(f"""
<h2><span class="n">4.1</span>Why the workshop matters</h2>
<p>Every modelled figure in this paper assumes how often a truck is serviced and what is fitted. The workshop record replaces the assumption with the fact. It shows the service that happened, the mileage at which it happened, and the parts fitted, including parts that were not bought through the Isuzu channel. ISZE has done this once, with one dealer's workshop export: vehicles, jobs and fitted parts could be matched. It works; it just has never been asked for at scale.</p>

<h2><span class="n">4.2</span>What we ask, and nothing more</h2>
{table(["Field", "Why"], [
    ["Job date and mileage", "Turns an assumed service interval into an observed one"],
    ["Vehicle model and year (vehicle identifier pseudonymised)", "Ties the job to the fleet model without identifying a customer"],
    ["Operation performed", "Separates routine service from repairs"],
    ["Parts fitted: part number, quantity, and whether it came through the Isuzu channel", "Shows capture and leakage at the point of fitting"],
])}
<p>Monthly, as the dealer's own workshop system exports it, in any format. No customer names, no prices, no labour rates. The dealer decides what goes further than its distributor.</p>

<h2><span class="n">4.3</span>What the dealer gets back</h2>
<div class="flow">
  <div class="r"><h5>Its own Dealer Standards profile</h5>Its answers in the real question wording, section by section, against its country and an anonymous network average, with an action coach that turns a weak answer into three concrete steps.</div>
  <div class="r"><h5>A service-due list</h5>Which trucks in its own workshop history are due for which maintenance in the next 90 days: work it can book, not a report.</div>
  <div class="r"><h5>A workshop benchmark</h5>Parts per job, service intervals achieved and share of jobs using Isuzu-channel parts, against anonymous peers in its own quartile.</div>
</div>
<p>Plus Deal of the Day offers matched to the trucks it will actually service, and a funded €600 setup task to connect its workshop export once. <span class="label p">Proposed</span></p>

<h2><span class="n">4.4</span>The door is already open: Isuzu Dealer Standards</h2>
{fig(C.fig_ids_hist(), f"{ids['scored']} of {ids['rows']} dealers already carry a recorded score, average {ids['avg']:.1f}.", "Isuzu Dealer Standards network lists, September 2026: 519 dealer records across 19 networks, one assessment round.")}
<p><span class="label m">Measured</span> {ids['rows']} dealers across 19 networks completed the Dealer Standards self-assessment, and {ids['scored']} have an individual score. That is the base rate for what this network does when it is asked. <span class="label i">Reported</span> The per-country dealer comparison built in-house (dealer against its country and an anonymous network average, on a map) is already used in feedback meetings, and distributors and dealers respond well to it. Until 2026 the results arrived as Excel sheets that took about five people to process.</p>
<p><span class="label i">Inferred</span> This is the only place where ISZE holds something every dealer wants to look at and cannot assemble for itself. So the dealer journey opens with it: the first thing a dealer sees is its own assessment, not a supplier's reading of its business. The maintenance-data ask comes second, attached to the tools that need it.</p>

<h2><span class="n">4.5</span>The dealer's worries, answered</h2>
{table(["The worry", "The answer built into the design"], [
    ["\"My supplier's supplier is looking at my book.\"", "Everything reaches the dealer through its own distributor. The dealer sees its own data first and decides what goes further."],
    ["\"This will be used against me.\"", "No public league table. Each dealer sees its own position and anonymous quartiles. Nothing is published by name."],
    ["\"Customer data and privacy.\"", "No customer names; vehicle identifiers pseudonymised; aggregates where a financial figure is needed."],
    ["\"I have no time at the counter.\"", "No forms. One export connection, funded once, then automatic. The first session is ten minutes with a finished profile."],
    ["\"What if I don't take part?\"", "Ordinary service does not change. Participation adds tools and offers; it never removes anything."],
])}
""")

# ================================================================== PART III
H.append(part(3, "III", "Engagement", "€500",
              "of gross profit turns on one choice in a Deal of the Day: give the discount on the extra units, not on all of them.",
              ["5 · Deal of the Day: the engagement engine", "6 · What we can build", "7 · Designing for maximum engagement"]))

H.append(chapter(5, "Deal of the Day: the engagement engine",
                 "ISZE helps a distributor prepare a specific, time-limited offer: a reasoned product selection, the right dealers, transparent economics and a way to learn from what follows. It is the part of Universe people feel in thirty seconds, and it is the one that spends money, so it has to buy data and evidence as well as volume."))
H.append(f"""
<h2><span class="n">5.1</span>Why it is the engine</h2>
<div class="flow">
  <div><h5>It needs a baseline</h5>Support is paid only on extra volume, so every Deal of the Day starts from what the chosen dealers bought before, which is sales-to-dealer data for the selected families.</div>
  <div><h5>It needs targeting</h5>The right dealers are the ones with trucks due and low capture, which is the maintenance scorecard and the service-due list.</div>
  <div class="r"><h5>It returns a result</h5>Contribution measured on the same scope before and after, which is the evidence the programme needs to justify the next euro.</div>
</div>
<p>The data ask is built into the offer rather than bolted on. A distributor that wants Deal of the Day support sends the baseline because the mechanism cannot work without it, not because a form requires it. <b>Not to be confused with Don't Lose the Deal</b> (chapter 6), Isuzu Truck UK's existing support for competitive quotations.</p>

<h2><span class="n">5.2</span>Which units get the discount</h2>
{fig(C.fig_scope_effect(), "The same 120 units, two ways of paying for them.", "Illustrative: 100-unit baseline at €100 net and €70 parts cost, 20 extra units, 5% concession. Not an Isuzu price or offer.")}
<p><span class="label p">Illustrative</span> If all 120 units get 5% off, gross profit stays at €3,000, so the 20 extra units bought nothing. If only the 20 extra units get the discount, gross profit is €3,500. The €500 comes from the scope of the concession alone. <b>Support is paid on extra volume against a documented baseline, never on all volume.</b></p>

<h2><span class="n">5.3</span>The size floor</h2>
{fig(C.fig_size_floor(), "Small Deals of the Day cannot pay for themselves.", "Illustrative: 30% gross margin and 5% off the extra units, so 25 cents of gross profit per extra euro. Not a forecast.")}
<p>At €150,000 of eligible billing, €2,500 of support needs {C.uplift_needed(150000, 2500):.1f}% extra sales and €5,000 needs {C.uplift_needed(150000, 5000):.1f}%. At €50,000 it would take {C.uplift_needed(50000, 2500):.0f}% and {C.uplift_needed(50000, 5000):.0f}%. <span class="label p">Proposed</span> Support only above <b>€150,000 of eligible billing</b>. Several dealers or families can be pooled to reach it.</p>

<h2><span class="n">5.4</span>Where concession already sits, and a pilot candidate</h2>
{fig(C.fig_concession_db(), "The deepest concession is not in the largest markets.", "ISZE maintenance-parts billing with a reference price, calendar 2025. Twelve highest shares of 24 distributors.")}
<p><span class="label m">Measured</span> {c25['ge20_pct']:.1f}% of {E(c25['billed'] / 1e6, 2)}M maintenance-parts billing in 2025 sat at least 20% under reference, down from {c24['ge20_pct']:.1f}% in 2024. The highest shares sit in small markets, so without a size floor the money would follow them.</p>
<p><span class="label m">Measured</span> <b>Isuzu UK air filters</b> rose from {K(iuk['2024'][0])} to {K(iuk['2025'][0])} while the deep-discount share fell from {iuk['2024'][1]:.1f}% to {iuk['2025'][1]:.1f}%. <span class="label p">Proposed</span> A strong pilot candidate as part of a wider filter selection for Isuzu UK (filters together {K(iuk_filters_2025)} in 2025), because on its own it sits below the floor.</p>

<h2><span class="n">5.5</span>Why thresholds, not forecasts</h2>
<p><span class="label m">Measured</span> Distributor purchasing response to list-price moves between 2024 and 2025 is too weak to forecast from. For maintenance-service parts it is negative, but the uncertainty is half the size of the estimate and it explains less than 1% of the movement. For brakes it is flat to slightly positive, with an uncertainty three times the estimate. For lubrication the price moved too uniformly to measure. Of the brakes change, roughly {K(abs(float(br['eur_sensitive_price_up_vol_down'])))} sits where price rose and volume fell, {K(float(br['eur_passed_price_up_vol_up']))} where both rose, and {K(abs(float(br['eur_leak_price_flat_vol_down'])))} where volume fell with price flat. This is stocking, not dealer demand. Dealer-level data is exactly what would make a real measurement possible. Until then, every Deal of the Day is judged against a threshold.</p>

<h2><span class="n">5.6</span>The funding line</h2>
{table(["Line", "Proposed", "Basis"], [
    ["Deal of the Day support", "€35,000 to €50,000", "8 to 12 Deals of the Day at €2,500 to €5,000, above the floor, each with a sales-to-dealer baseline"],
    ["Dealer enablement", "€15,000 to €25,000", "25 to 40 accepted setup tasks at €600: connecting a workshop export, or a first sales-to-dealer feed"],
    ["Independent evaluation", "€10,000 to €15,000", "Two waves, at 90 and 180 days, including returns; published whether favourable or not"],
    ["<b>Total cash</b>", "<b>€60,000 to €90,000</b>", "Inside the existing €100,000 route"],
], "num")}
<p>The current position, that Deal of the Day needs its own approved commercial treatment and is not automatically funded, is a control, not an answer. This paper asks for the line to be named.</p>
""")

H.append(chapter(6, "What we can build",
                 "AI has made good software cheap to build. The tools below can be built in-house, quickly, in the languages of each market. What cannot be built is the data behind them, so every tool is chosen for what it gives the participant and what it brings back."))
H.append(f"""
<p><span class="tag t-live">Live</span> in use today · <span class="tag t-proto">Prototype</span> built, not yet shared · <span class="tag t-build">To build</span> designed in this paper</p>
<h2><span class="n">6.1</span>For distributors</h2>
{table(["Tool", "What it gives", "What it brings back", "Status"], [
    ["<b>Dealer maintenance scorecard</b>", "Capture per dealer and family against its own trucks; who to visit and about what", "Sales to dealer; trucks sold per dealer", '<span class="tag t-build">To build</span>'],
    ["<b>Parts Atlas</b>", "Its own business by family, product form, Genuine and Best Value; the reference behind every movement", "Corrections; agreed definitions", '<span class="tag t-proto">Prototype</span>'],
    ["<b>Deal of the Day builder</b>", "Choose a family; get eligible dealers, the baseline, the additional-only economics, the break-even and a ready offer sheet in its language", "Baseline data; the result of each Deal of the Day", '<span class="tag t-build">To build</span>'],
    ["<b>Data intake assistant</b>", "Drop in any export (Excel, workshop system, CSV); AI maps it to the standard and says what is missing", "Makes giving data nearly free, including for distributors that do not track it yet", '<span class="tag t-build">To build</span>'],
    ["<b>Monthly network brief</b>", "A prepared one-page review in its own language: what moved, which dealers, what to do", "A monthly reason to send data on time", '<span class="tag t-build">To build</span>'],
    ["<b>Competitor price watch</b>", "Where Isuzu parts sit against public online prices, by family", "Nothing extra; builds trust", '<span class="tag t-proto">Prototype</span>'],
    ["<b>Tender radar</b>", "Public opportunities with the aftersales content visible, qualified and dated", "One line per outcome", '<span class="tag t-live">Live</span>'],
])}
<h2><span class="n">6.2</span>For dealers</h2>
{table(["Tool", "What it gives", "What it brings back", "Status"], [
    ["<b>Dealer Standards compare</b>", "Itself against its country and an anonymous network average, on a map", "Engagement with the assessment", '<span class="tag t-live">Live</span>'],
    ["<b>Dealer Standards Studio and action coach</b>", "Its own answers explorable; AI turns each weak answer into three steps with an owner and a date", "A development plan; progress", '<span class="tag t-build">To build</span>'],
    ["<b>Service-due list</b>", "Trucks in its own history due for maintenance in the next 90 days", "Workshop export", '<span class="tag t-build">To build</span>'],
    ["<b>Workshop benchmark</b>", "Parts per job, intervals achieved, channel share, against anonymous peers", "Workshop export", '<span class="tag t-build">To build</span>'],
    ["<b>Quote defender</b>", "A five-minute case form: photograph the competitor quote, get a fast support decision", "The Don't Lose the Deal case record (6.4)", '<span class="tag t-build">To build</span>'],
])}

<h2><span class="n">6.3</span>What we deliberately do not build</h2>
<p>Availability enquiries, part and Best Value lookups, day-to-day quotation handling and support administration stay in the existing business. A programme that also answered availability questions would be judged on response times against a system that already does it. <b>The boundary is also the offer:</b> <i>we are not asking you to feed a support desk, and the support desk does not get better or worse depending on what you send us.</i></p>

<h2><span class="n">6.4</span>Don't Lose the Deal: from payment to case</h2>
{fig(C.fig_dlod_credits(), "A recurring €30,000 a year, and no case behind any of it.", "ISZE credit notes to Isuzu Truck UK carrying the programme name, June 2023 to March 2026.")}
<p><span class="label m">Measured</span> Isuzu Truck UK's programme for competitive quotations runs on a memorandum of understanding, a rebate credit note and Japan-side sign-off. It has paid €30,000 a year: €90,000 across 2023, 2025 and 2026. €30,000 is {dlod_share:.2f}% of Isuzu Truck UK's 2025 billing. <b>Zero cases are recorded:</b> no part, dealer, competitor quote or outcome. The intent is to roll it out to every dealer. At €30,000 per market that is €90,000 for three markets or €570,000 for nineteen ({570000 / billed_2025 * 100:.2f}% of 2025 billing). Rolled out as it stands, every market would buy the payment and inherit the blindness. The quote defender fixes it: part, dealer, dated competitor quote, support requested and granted, outcome, and the follow-on order reference. That is about five minutes per case, attached to the credit note that is raised anyway.</p>

<h2><span class="n">6.5</span>Tenders: from notice to outcome</h2>
{fig(C.fig_tender_funnel(), "From public notice to pursuit decision, and then nothing.", "The live public-tender feed, 22 September 2026.")}
<p><span class="label m">Measured</span> {st['raw_notices']} notices reduce to {st['opportunities']} opportunities, {st['aftersales_tagged']} with an aftersales signal and {st['action_queue']} in the action queue; no outcome is recorded. A tender's advertised value is not Isuzu parts revenue, and a notice count is not a pipeline. ISZE asks for one line when a tender is won, lost or declined. <b>One decision closes both gaps: record the outcome of every supported case, in one shape.</b></p>
""")

H.append(chapter(7, "Designing for maximum engagement",
                 "Engagement is not a communication problem. It is a design problem: what each party gets, how soon, how often, and what it costs them to give something back."))
H.append(f"""
<h2><span class="n">7.1</span>Six principles</h2>
{table(["Principle", "What it means in practice"], [
    ["<b>Give first</b>", "Every participant receives something finished before anything is asked: a prepared network review, its own Dealer Standards profile."],
    ["<b>Value in the first ten minutes</b>", "No registration, no form, no upload in the first session. The first screen is the participant's own data."],
    ["<b>Make the distributor the hero</b>", "The distributor invites its dealers, owns the scorecard and decides the action. ISZE never goes round it."],
    ["<b>Make giving data nearly free</b>", "Any format through the intake assistant; a funded setup task; one connection, then automatic."],
    ["<b>A reason to come back every month</b>", "The monthly brief, the refreshed service-due list, the Deal of the Day calendar. Each depends on this month's data."],
    ["<b>Recognition without a league table</b>", "Each participant sees its own position and anonymous quartiles. No public ranking by name."],
])}

<h2><span class="n">7.2</span>Engagement ladders</h2>
<div class="ladder">
<div class="col"><h4>Distributor</h4>
<div class="rung"><div class="lv">1</div><div><b>Receives</b> a prepared network review from the report it already sends. <span class="g">Asks nothing new.</span></div></div>
<div class="rung"><div class="lv">2</div><div><b>Sends</b> sales to dealer monthly, by part and dealer. <span class="g">Gets the Parts Atlas and the monthly brief; first rebate tier.</span></div></div>
<div class="rung"><div class="lv">3</div><div><b>Adds</b> trucks sold per dealer. <span class="g">Gets the dealer maintenance scorecard; full rebate tier.</span></div></div>
<div class="rung"><div class="lv">4</div><div><b>Uses</b> the scorecard in its own dealer meetings and runs a Deal of the Day. <span class="g">Gets part-funded offers.</span></div></div>
<div class="rung"><div class="lv">5</div><div><b>Records</b> outcomes for deals and tenders. <span class="g">Gets faster support decisions, evidence for the next budget.</span></div></div>
</div>
<div class="col"><h4>Dealer</h4>
<div class="rung"><div class="lv">1</div><div><b>Sees</b> its own Dealer Standards profile, via its distributor. <span class="g">Asks nothing.</span></div></div>
<div class="rung"><div class="lv">2</div><div><b>Corrects</b> a prepared review of its purchases. <span class="g">"Your reading is wrong" is a success.</span></div></div>
<div class="rung"><div class="lv">3</div><div><b>Chooses</b> a development priority with the action coach. <span class="g">Owns the plan.</span></div></div>
<div class="rung"><div class="lv">4</div><div><b>Connects</b> its workshop export (funded €600). <span class="g">Gets the service-due list and the benchmark.</span></div></div>
<div class="rung"><div class="lv">5</div><div><b>Joins</b> Deals of the Day matched to its trucks, and logs quotes it wants to defend. <span class="g">Gets better offers and faster support.</span></div></div>
</div>
</div>

<h2><span class="n">7.3</span>The incentive stack: existing money first</h2>
{table(["Lever", "Who", "How", "New money?"], [
    ["<b>Re-point the 20% KPI rebate share</b>", "Distributors", "Tier 1 = today's KPI report. Tier 2 = monthly sales to dealer by part and dealer. Tier 3 = plus trucks sold per dealer and outcomes. Released per tier, for meeting a standard, never per record.", "No"],
    ["<b>Deal of the Day support</b>", "Distributors, dealers", "Available only with a sales-to-dealer baseline; targeted at dealers with trucks due", "Inside the €100k route"],
    ["<b>Funded setup task, €600</b>", "Dealers, distributors that do not track yet", "Pays for the one-time connection of a workshop export or a first sales-to-dealer feed", "Inside the €100k route"],
    ["<b>Dealer Standards recognition</b>", "Dealers", "Propose that data-driven workshop management (sharing and using maintenance data) counts in the next Dealer Standards round", "No"],
    ["<b>Tools themselves</b>", "Everyone", "The scorecard, service-due list and benchmark exist only for those who send the data behind them", "Internal time"],
])}
<p><span class="label i">Inferred</span> The re-pointed rebate is the strongest lever and costs nothing extra: the money is already paid, and today it buys a thin file. The same money can buy part-by-dealer detail every month. For distributors that do not track sales to dealer yet, the setup task and the intake assistant turn "we can't" into "we can".</p>

<h2><span class="n">7.4</span>Open for decision: a participation score</h2>
<div class="callout"><p><span class="label p">Proposed, not decided</span> A score could make the tiers above visible and fair. If introduced, it counts useful exchange, not volume: agreed data on time and complete, corrections made, maintenance data shared, a tool used for a named decision, outcomes recorded. Each participant sees only its own. Ordinary service never depends on it. What it unlocks, if anything beyond the rebate tiers, is still to be decided. No scores are given in this paper.</p></div>

<h2><span class="n">7.5</span>What not to do</h2>
{table(["Do not", "Why"], [
    ["Pay per record, row or data field", "It rewards disclosure volume, not useful work"],
    ["Make ordinary service conditional on contribution", "It turns a normal service into a bargaining chip and destroys trust"],
    ["Publish a dealer league table", "Turnover favours large dealers; the first public ranking ends the second data request"],
    ["Ask for resale prices or customer names", "Not needed, and the most sensitive items on the list"],
    ["Approach a dealer directly", "The distributor owns the relationship"],
    ["Count logins or uploads as success", "Neither shows that a decision improved"],
])}
""")

# ================================================================== PART IV
H.append(part(4, "IV", "Money and decisions", "0.31%",
              "of one year's parts billing: the size of the €100,000 route. Released in stages, against gates that measure data, use and return.",
              ["8 · The money and the return", "9 · Decisions, build order and stop"]))

H.append(chapter(8, "The money and the return",
                 "Budget can be found. It has to come back. This chapter sets the denominator, names three sources of return, and ties the second stage of money to measured gates."))
H.append(f"""
<h2><span class="n">8.1</span>The denominator</h2>
{fig(C.fig_denominator(), "Every envelope in this paper is under 2% of one year's billing.", f"ISZE parts billed to {n_db} distributors, calendar 2025. Don't Lose the Deal routes at €30,000 per market a year.")}

<h2><span class="n">8.2</span>Three sources of return</h2>
{table(["Source", "How it is measured", "What it is worth"], [
    ["<b>1. Deal of the Day contribution</b>", "Parts gross profit on extra volume, same scope before and after, net of support", "At €2,500 per beneficial action, the €100,000 route needs 40 (8.3)"],
    ["<b>2. Maintenance-parts capture</b>", "Capture for pilot dealers against comparable dealers not in the pilot, family by family", f"<span class='label i'>Modelled</span> 1 point of capture across the modelled network ≈ {K(pms['point'])} of revenue a year (8.4)"],
    ["<b>3. Data</b>", "Share of billing visible by named dealer, monthly", f"From {cov['named_eur'] / billed_2025 * 100:.1f}% today. It unlocks the scorecard, real price-response measurement and evaluation of every support euro"],
])}

<h2><span class="n">8.3</span>The hurdle for Deal of the Day</h2>
{fig(C.fig_hurdle(), "At €2,500 per beneficial action, the €100,000 route needs 40.", "Illustrative: envelope ÷ assumed contribution per action.")}
<p>A pilot of ten Deals of the Day proves the method, not the return. It produces the first real measurement of how often a Deal of the Day qualifies, and that rate decides the second stage.</p>

<h2><span class="n">8.4</span>The capture hurdle</h2>
{fig(C.fig_capture_points(), f"The €100,000 route pays back with 1 to 2 points of capture.", f"Illustrative. Modelled 2025 maintenance-parts need of {K(pms['modelled'])} a year across {pms['dbs']} markets and {pms['families']} families, valued at ISZE's average selling price; {pms['excluded']} market-family combinations where the model base gives more than 100% are left out. ISZE's actual gross margin is not stated in this paper.")}
<p><span class="label i">Modelled</span> ISZE supplies about {pms['capture']:.0f}% of the modelled maintenance-parts need today. At a 30% gross margin, the €100,000 route is earned back by {100000 / 0.3 / pms['point']:.1f} points of capture network-wide, and the €300,000 route by {300000 / 0.3 / pms['point']:.1f}. A modelled gap is not recoverable revenue. The pilot measures capture in pilot dealers against comparable dealers, and only that measured difference counts.</p>

<h2><span class="n">8.5</span>Stage gates</h2>
{table(["Stage", "Money", "Gate to the next stage (proposed thresholds, for decision)"], [
    ["<b>1. Prove</b> (two quarters)", "€100,000 route: Deal of the Day €60–90k, rest as planned", "Monthly part-by-dealer sales to dealer from at least 3 distributors · at least 10 dealers sending workshop exports · at least 2 Deals of the Day above the floor, with measured contribution · a capture baseline for pilot dealers"],
    ["<b>2. Scale</b> (four quarters)", "€300,000 route", "Named-dealer visibility above 40% of billing · capture in pilot dealers above comparable dealers · Deal of the Day qualifying rate known and positive"],
    ["<b>3. Run</b>", "From the measured return", "Contribution plus capture gain covers the running cost"],
])}
<p>The re-pointed 20% rebate share runs alongside, outside these envelopes. The euro value of that share is not stated in this paper and should be added before the funding discussion.</p>

<h2><span class="n">8.6</span>The price of a dealer</h2>
{fig(C.fig_price_of_dealer(), "The same €15,000 is a gesture or a programme, depending on where it goes.", "Dealer counts from the Dealer Standards network lists, September 2026.")}
<p>Spread over 519 dealers, €15,000 buys nothing. Spent as twenty-five funded setup tasks in two pilot markets, it buys twenty-five connected workshops.</p>
""")

H.append(chapter(9, "Decisions, build order and stop",
                 "Three decisions this month, one order to build in, and one stop condition that does not bend."))
H.append(f"""
<h2><span class="n">9.1</span>The decisions</h2>
{table(["Decision", "Recommendation", "What has to be true first"], [
    ["<b>Re-point the KPI rebate</b>", "Link the 20% share to the sales-to-dealer standard, in three tiers", "The tier definitions are written and legally reviewed"],
    ["<b>Fund Deal of the Day</b>", "€60,000 to €90,000 named inside the €100,000 route, €150,000 floor, baseline required", "The selection rule is agreed and the first Deal of the Day is named"],
    ["<b>Start the pilot</b>", "Isuzu Truck UK plus one distributor that commits to tier 2; ten dealers across the two", "The classification is fixed to one named release; the first scorecard is prepared before the first invitation"],
])}
<h2><span class="n">9.2</span>The build order</h2>
{table(["Stage", "Result", "Evidence to move on"], [
    ["1. Fix the classification release", "One named version and build date", "A family view reproduces from it"],
    ["2. Build the intake assistant and the scorecard", "Isuzu Truck UK's 64 dealers scored, once their trucks per dealer arrive", "The distributor names a dealer it will act on"],
    ["3. Open the Dealer Standards Studio", "Ten dealers see their own profile first", "Corrections, plans, reasons for non-use recorded"],
    ["4. Connect workshops", "Funded setup tasks; service-due list and benchmark live", "Exports arrive monthly without chasing"],
    ["5. Run Deal of the Day", "At least two above the floor, with a baseline", "Contribution measured before, during and after, including returns"],
    ["6. Record outcomes", "Quote defender and tender outcomes in one shape", "Cases close with the record filled"],
    ["7. Evaluate at the gate", "A stated result, favourable or not", "Measured data, use and return, not a rendered screen"],
])}
<h2><span class="n">9.3</span>Go, no-go and stop</h2>
<div class="callout"><p><b>Go</b> if a real participant completed a real task, the output was correct against its source, and the participant can name the decision it changed. <b>No-go</b> if the only evidence is that a screen rendered or a demonstration looked good. <b>Stop</b> if, after two eligible cycles, no participant can name a decision the tool changed, or a confidentiality weakness cannot be closed. It does not pause or widen the sample.</p>
<p>The honest test: <b>if the rebate condition were removed tomorrow, would the distributor still send the data?</b></p></div>

<h2><span class="n">9.4</span>The unowned answer, and the other risks</h2>
<p><b>The answer needs an owner.</b> Tools raise questions: why is this dealer at 23%? Nobody has yet been named, given hours or funded to answer them. Software is cheap and a person's time is not. Without a named owner, the product arrives looking complete and the point of it never happens.</p>
<p><b>Delivery.</b> There is no production system yet: no shared identity, access control or storage. Until that is built and independently reviewed, sharing stays distributor-led and document-based. Only the authorised distributor sees its own accounts; only the dealer sees its own record; no distributor sees another's data.</p>
<p><b>Competition law and privacy.</b> The European motor-vehicle block exemption regime runs until 31 May 2028. Nothing here is a legal determination, and the design must be reviewed before any shared output is used. Three standing rules: no exclusivity in exchange for information; no price coordination between distributors (each is compared with its own history and anonymous aggregates only); no resale-price instruction. Workshop data comes pseudonymised, with no customer names.</p>
{table(["Still unknown", "Why it matters"], [
    ["The euro value of the 20% rebate share", "Needed to weigh the programme against the incentive already paid"],
    ["Which distributors can produce trucks sold per dealer", "It decides where the scorecard can run first"],
    ["How often a Deal of the Day qualifies", "The number that decides stage 2"],
    ["Whether dealers keep sending workshop exports after the first", "The real test of the dealer design"],
    ["ISZE's gross margin on maintenance parts", "Needed to turn capture points into return"],
    ["Whether a participation score is introduced", "Open for decision (7.4)"],
])}
""")

# ================================================================== REFERENCE
H.append(f"""
<h2 class="newpage">Reference: terms and sources</h2>
{table(["Term", "Meaning"], [
    ["Parts billed", "ISZE sales to the stated distributor"],
    ["Sales to dealer", "The distributor's recorded sales to its dealers; not a dealer's sales to its customers"],
    ["Maintenance parts (PMS)", "Periodic maintenance and service parts: filters, brakes, clutch and related wear parts"],
    ["Maintenance capture", "Units supplied through the Isuzu channel ÷ units the fleet model expects from vehicles in service and service intervals"],
    ["Target spend per truck", "A modelled expectation of what a market could spend per vehicle"],
    ["Parts gross profit", "Revenue less parts purchase cost; freight, duty, overheads and rebates excluded"],
    ["Deep concession", "Billed at least 20% under the reference price"],
    ["Best Value parts", "The lower-priced counter part sold alongside Genuine"],
    ["Isuzu Truck UK / Isuzu UK", "Two separate UK distributors, trucks and pickups, never combined"],
])}
{table(["Source", "Used for"], [
    ["ISZE billing to distributors, 2023 to 2026", "Parts billed, the examples, the denominator, Don't Lose the Deal credits"],
    ["Distributors' sales-to-dealer files, 2025", "Coverage, the Isuzu Truck UK dealer spread"],
    ["ISZE fleet and maintenance model, 2025", "Maintenance capture, oil-filter view, value of a capture point, target-spend ceiling"],
    ["ISZE maintenance-parts pricing analysis, 2024 and 2025", "Concession, air filters, price response"],
    ["Isuzu Dealer Standards network lists and compare tool, 2026", "Dealer counts, scores, the dealer journey"],
    ["Public-tender feed, 22 September 2026", "The tender funnel"],
    ["Don't Lose the Deal rollout design, September 2026", "Rollout routes and the cost of the case record"],
])}
<p class="src">Historical observations keep their original period. Tools, journeys, incentives, thresholds and funding lines are proposals as of 23 September 2026.</p>
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
    chap_by_part = {1: [1, 2], 2: [3, 4], 3: [5, 6, 7], 4: [8, 9]}
    for no, roman, title in PARTS:
        rows.append(f'<tr><td class="no">{roman}</td><td><b>{title}</b></td><td class="pg">{pages.get(("P", no), "")}</td></tr>')
        for c in chap_by_part[no]:
            t = dict(CHAPS)[c]
            rows.append(f'<tr><td class="no" style="color:#6B7078;font-weight:normal">{c}</td><td style="padding-left:6mm">{t}</td><td class="pg" style="font-weight:normal">{pages.get(("C", c), "")}</td></tr>')
    rows.append(f'<tr><td class="no"></td><td>Reference: terms and sources</td><td class="pg">{pages.get("ref", "")}</td></tr>')
    return "".join(rows)


def find_pages(pdf):
    doc = fitz.open(pdf)
    out = {}
    for i, pg in enumerate(doc):
        if i < 3:
            continue
        flat = re.sub(r"\s", "", pg.get_text()).upper()
        for no, roman, _ in PARTS:
            if flat.startswith(roman) and f"PART{roman}" in flat and ("P", no) not in out:
                out[("P", no)] = i + 1
        for c, title in CHAPS:
            key = "CHAPTER" + str(c) + re.sub(r"\s", "", title).upper()[:12]
            if key in flat and ("C", c) not in out:
                out[("C", c)] = i + 1
        if "REFERENCE:TERMSANDSOURCES" in flat:
            out["ref"] = i + 1
    return out, len(doc)


if __name__ == "__main__":
    tmp = OUT_PDF + ".pass1.pdf"
    render(page_html(toc_rows({})), tmp)
    pages, n = find_pages(tmp)
    render(page_html(toc_rows(pages)), OUT_PDF)
    pages2, n2 = find_pages(OUT_PDF)
    os.remove(tmp)
    print("pages", n2, "found", len(pages2), sorted(pages2.items(), key=lambda kv: kv[1]))
    os.makedirs(QA, exist_ok=True)
    for f in os.listdir(QA):
        os.remove(os.path.join(QA, f))
    doc = fitz.open(OUT_PDF)
    for i, pg in enumerate(doc):
        pg.get_pixmap(dpi=70).save(os.path.join(QA, f"p{i + 1:02d}.png"))
    text = "\n".join(p.get_text() for p in doc)
    banned = [r"\bcampaign", r"\bAIM\b", r"\bPRISM\b", r"\bDLOD\b", r"\bIDS\b", r"\.csv", r"\.json", r"\.py\b", r"_build",
              r"internal draft", r"business owner", r"snapshot", r"workspace", r"\bGPS\b", r"\bBVP\b", r"\bIML\b",
              r"\bITUK\b", r"\bIUK\b", r"Suzuki"]
    for b in banned:
        hits = re.findall(r".{0,40}" + b + r".{0,40}", text, flags=re.I)
        if hits:
            print(f"  BANNED {b!r}: {len(hits)} e.g. {hits[0]!r}")
    print("done", OUT_PDF)
