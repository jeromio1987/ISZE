"""Render the 20-page growth paper HTML from the locked payload.

Separated from the extractor so the numbers are computed once and only rendered here.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
P = json.loads((ROOT / "02_dashboards" / "_build" / "_growth_payload.json").read_text(encoding="utf-8"))
CHART = (ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js").read_text(encoding="utf-8", errors="replace")
CHART = "\n".join(ln for ln in CHART.splitlines() if "sourceMappingURL" not in ln)
OUT = ROOT / "02_dashboards" / "sales" / "ISZE_Growth_Plan_2026.html"
TODAY = date.today().isoformat()


def eur(v: float, dp: int = 0) -> str:
    return f"&euro;{v:,.{dp}f}"


# ── locked constants (reconcile with build_growth_paper.py output) ───────────
NET25 = 32_381_312
NET24 = 33_145_516
GAP_TOTAL = 18_216_555
TOP3_EUR = 8_392_470
NOLIST_EUR = 4_955_737
NOLIST_PN = 251
REPL_EUR = 4_168_788
WARRANTY_PARTS_2025 = 4_720_000
COVER = 0.570

CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:10.4px;line-height:1.52;background:#fff}
h1,h2,h3,h4{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}
.page{position:relative;min-height:250mm;padding:14mm 14mm 20mm;break-after:page}
.page:last-child{break-after:auto}
.pno{position:absolute;bottom:9mm;right:14mm;font-size:8px;color:#6b6256;font-family:Georgia,serif}
.pfoot{position:absolute;bottom:9mm;left:14mm;font-size:7.6px;color:#6b6256;max-width:120mm}
h2.sec{font-size:19px;margin:0 0 3mm;padding-bottom:2.4mm;border-bottom:2px solid #1a2b4a;break-after:avoid}
h2.sec .no{color:#c0552d}
h3{font-size:12.6px;margin:5mm 0 1.6mm}
h4{font-size:11px;margin:4mm 0 1.2mm;color:#2b4a78}
p{margin:0 0 2.6mm}
.lead{font-size:11.4px;color:#33323f}
ul,ol{margin:0 0 2.8mm 4.4mm;padding:0}
li{margin-bottom:1.2mm}
table{width:100%;border-collapse:collapse;margin:2.4mm 0 3.6mm;font-size:9.4px;break-inside:avoid}
th{background:#1a2b4a;color:#fff;text-align:left;padding:2.2mm;font-size:8.7px;text-transform:uppercase;letter-spacing:.3px}
td{padding:2mm;border-bottom:.5px solid #d9d3c8;vertical-align:top}
tbody tr:nth-child(even){background:#f7f4ee}
tr{break-inside:avoid}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.callout{border-left:3px solid #c0552d;background:#f7f4ee;padding:3mm 3.6mm;margin:3mm 0;break-inside:avoid}
.callout.navy{border-left-color:#1a2b4a}
.callout.green{border-left-color:#1d9e75}
.kpibar{display:flex;gap:3mm;margin:3mm 0 4mm;flex-wrap:wrap}
.kpi{flex:1 1 30%;background:#f7f4ee;border-top:3px solid #1a2b4a;padding:3mm}
.kpi .l{font-size:8.4px;text-transform:uppercase;letter-spacing:.4px;color:#6b6256}
.kpi .v{font-family:Georgia,serif;font-size:19px;color:#1a2b4a;margin:.6mm 0}
.kpi .s{font-size:8.6px;color:#6b6256}
.ch{position:relative;width:100%;margin:2mm 0 1mm}
.two{display:flex;gap:6mm;align-items:flex-start}
.two>div{flex:1 1 0;min-width:0}
.small{font-size:8.8px;color:#6b6256}
.tag{display:inline-block;font-size:7.8px;text-transform:uppercase;letter-spacing:.4px;
  padding:.8mm 1.8mm;border-radius:2px;background:#1a2b4a;color:#fff;margin-right:1.4mm}
.tag.amber{background:#eda100;color:#3a2c00}
.tag.red{background:#e24b4a}
.tag.grey{background:#888780}
.tag.green{background:#1d9e75}
.cover{position:relative;height:267mm;margin:-14mm -14mm 0;padding:36mm 24mm;
  background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%);color:#eef1f6;break-after:page}
.cover h1{color:#fff;font-size:42px;line-height:1.08;max-width:150mm}
.cover .rule{width:54mm;height:3px;background:#c0552d;margin:9mm 0 8mm}
.cover .sub{font-size:13px;color:#c9d3e4;max-width:140mm;line-height:1.55}
.cover .meta{position:absolute;bottom:24mm;left:24mm;font-size:9.6px;color:#9fb0c9;line-height:1.7}
.cover .top{font-family:Georgia,serif;font-size:12px;letter-spacing:2.4px;color:#c0552d;text-transform:uppercase}
.toc td{border-bottom:.5px solid #d9d3c8;padding:1.9mm 2mm}
.toc td.p{text-align:right;color:#c0552d;font-family:Georgia,serif;width:12mm}
.amber-note{background:#fff8e6;border-left:3px solid #eda100;padding:3mm 3.6mm;margin:3mm 0;break-inside:avoid}
.back{background:#1a2b4a;color:#eef1f6;padding:4mm}
.back h4{color:#fff;margin-top:0}
@media print{body{font-size:10.2px}}
"""


def page(n: int, title: str | None, body: str, foot: str = "") -> str:
    h = f'<h2 class="sec"><span class="no">{n:02d}&nbsp;&nbsp;</span>{title}</h2>' if title else ""
    return (f'<section class="page">{h}{body}'
            f'<div class="pfoot">{foot}</div><div class="pno">{n} / 20</div></section>')


def chart(cid: str, aria: str, h: int) -> str:
    return (f'<div class="ch" style="height:{h}px"><canvas id="{cid}" role="img" aria-label="{aria}">'
            f'The same numbers appear in the table next to this figure.</canvas></div>')


# ── page bodies ──────────────────────────────────────────────────────────────
cover = """
<section class="cover">
  <div class="top">Isuzu Motors Europe &middot; Vehicle Parts</div>
  <div class="rule"></div>
  <h1>How we grow parts sales</h1>
  <div class="sub" style="margin-top:8mm">
    A plain-English plan: where the money is, what is holding us back,
    and the six things worth doing about it.
  </div>
  <div class="meta">
    Prepared for ISZE management<br>
    REPLACE_DATE<br>
    All figures calendar 2025 unless stated, reconciled to the verified sales spine
  </div>
</section>
"""

p2 = page(2, "What this paper says, in one page", f"""
<p class="lead">We bill about half of what the market could absorb. In 2025 we shipped
{eur(32_381_312)} of parts against a target-spend envelope of roughly {eur(63_924_216)} for
2026. The gap is {eur(18_216_555)} of component demand we can measure, and another
{eur(10_400_000)} we can only partly see.</p>

<div class="kpibar">
  <div class="kpi"><div class="l">Parts billed, 2025</div><div class="v">&euro;32.4M</div>
    <div class="s">16 markets, ex credit notes</div></div>
  <div class="kpi"><div class="l">Measured component gap</div><div class="v">&euro;18.2M</div>
    <div class="s">vs expected demand, all quotable</div></div>
  <div class="kpi"><div class="l">We can see</div><div class="v">57%</div>
    <div class="s">of billed euro has dealer-level detail</div></div>
</div>

<h3>The five findings that matter</h3>
<ol>
  <li><b>The money is in clutch and brake, not filters.</b> Three product families hold
      {eur(8_392_470)} &mdash; 46% of the whole gap. Oil filters hold under 2%. We have been
      telling the filter story because it is easy to measure, not because it is where the euro is.</li>
  <li><b>Almost half the gap is a price fight, not a coverage fight.</b> Substitution is 49%
      of it: the job happens, the volume arrives, but not as our part.</li>
  <li><b>We are missing sales data for the three biggest markets after the UK.</b>
      Germany, Belgium and UMI together are {eur(8_900_000)} a year of billing we cannot see
      dealer-by-dealer.</li>
  <li><b>Growing sales is not the problem.</b> Half-one 2026 is up 12% on last year. The
      problem is that we cannot prove where it came from, and one market is going backwards.</li>
  <li><b>The ceiling grows 22% by 2030 on the vehicle parc alone.</b> Even doing nothing, the
      opportunity in front of us gets bigger. Doing something makes it compound.</li>
</ol>

<div class="callout navy">
  <b>The one-line answer to "how do we increase sales":</b> put a price on the parts we
  already sell but do not price, defend the lines where we are being undercut, and get
  dealer-level data for Germany, Belgium and Israel so we stop guessing.
  Those three are cheap, fast and already built.
</div>
""", "Figures: verified sales spine, calendar 2025. Capture against target spend per truck.")

p3 = page(3, "Where the market actually is", f"""
<p class="lead">Two numbers describe the whole opportunity. What the trucks in service should
absorb, and what we actually billed them.</p>

<div class="two">
  <div>
    <div class="kpi"><div class="l">Target-spend envelope, 2025 vehicles</div>
      <div class="v">&euro;63.9M</div><div class="s">2026 basis, 16 markets</div></div>
    <div class="kpi" style="border-top-color:#c0552d"><div class="l">Parts actually billed</div>
      <div class="v">&euro;32.4M</div><div class="s">calendar 2025</div></div>
    <div class="kpi" style="border-top-color:#1d9e75"><div class="l">Not captured</div>
      <div class="v">&euro;31.5M</div><div class="s">of which we can name &euro;18.2M</div></div>
  </div>
  <div>
    <h4>What "target spend" means</h4>
    <p class="small">For every market we take the number of Isuzu trucks on the road and
    multiply by what a truck of that type should spend on parts in a year. That gives the
    envelope. It is a ceiling, not a forecast.</p>
    <p class="small"><b>Read this with care:</b> for nine of the sixteen markets the ceiling
    assumes a flat &euro;250 per truck per year. That is a placeholder, not a measured target.
    Those nine markets are 37% of the total envelope. If the real figure were the median of the
    markets we do have, the envelope rises to &euro;70.5M and our capture falls to 43.6%.</p>
    <div class="amber-note small">
      <b>Why we say this out loud:</b> a headline "we capture 51% of the market" partly depends
      on a placeholder. The honest range is 44% to 51%. Anyone quoting one number should quote
      the range.
    </div>
  </div>
</div>

<h3>What we billed, by market</h3>
{chart("c_rank", "Horizontal bar chart of parts billed in 2025 by market, largest first", 430)}
<table><thead><tr><th>Market</th><th class="n">Parts billed 2025</th>
<th class="n">Trucks in service</th><th class="n">Billed per truck</th></tr></thead><tbody>
<tr><td>United Kingdom &ndash; trucks (ITUK)</td><td class="n">&euro;5.56M</td><td class="n">22,389</td><td class="n">&euro;249</td></tr>
<tr><td>United Kingdom &ndash; pickups (IUK)</td><td class="n">&euro;6.13M</td><td class="n">47,783</td><td class="n">&euro;128</td></tr>
<tr><td>Israel &ndash; UMI</td><td class="n">&euro;3.32M</td><td class="n">18,542</td><td class="n">&euro;179</td></tr>
<tr><td>Israel &ndash; UTI</td><td class="n">&euro;3.33M</td><td class="n">10,336</td><td class="n">&euro;322</td></tr>
<tr><td>Germany</td><td class="n">&euro;2.54M</td><td class="n">12,855</td><td class="n">&euro;197</td></tr>
<tr><td>Belgium / Netherlands</td><td class="n">&euro;2.11M</td><td class="n">9,594</td><td class="n">&euro;220</td></tr>
<tr><td>Portugal</td><td class="n">&euro;1.71M</td><td class="n">8,176</td><td class="n">&euro;209</td></tr>
<tr><td colspan="4" class="small">Remaining markets are charted above and total
{eur(32_381_312)} across 16 markets.</td></tr>
</tbody></table>
<p class="small"><b>Note on Portugal:</b> its 2025 figure is understated because six months of
its billing (March to August 2025) are missing from our data. Any Portugal year-on-year
comparison is therefore invalid until that is fixed.</p>
""", "Source: billing by market and vehicle-in-service counts, both calendar 2025.")

p4 = page(4, "The gap, and where it really sits", f"""
<p class="lead">Of the money we can name, {eur(8_392_470)} sits in three product families.
Everything else is smaller than the top three combined.</p>

{chart("c_cat", "Horizontal bar chart of the eight largest product-family gaps in euros", 380)}

<table><thead><tr><th>Product family</th><th class="n">Gap</th><th class="n">Share of all gaps</th>
<th class="n">Our capture</th><th>What the fight is</th></tr></thead><tbody>
<tr><td>Clutch disc</td><td class="n">&euro;3.14M</td><td class="n">17.2%</td><td class="n">low</td>
    <td>Fitment and part-number coverage &mdash; largely the UK pickup market</td></tr>
<tr><td>Brake pad</td><td class="n">&euro;2.78M</td><td class="n">15.3%</td><td class="n">low</td>
    <td>Price: we are being undercut on the same part</td></tr>
<tr><td>Brake shoe</td><td class="n">&euro;2.47M</td><td class="n">13.6%</td><td class="n">low</td>
    <td>Price, same as brake pad</td></tr>
<tr><td>Clutch pressure plate</td><td class="n">&euro;1.98M</td><td class="n">10.9%</td><td class="n">low</td>
    <td>Sell as a kit with the clutch disc</td></tr>
<tr><td>Blower filter</td><td class="n">&euro;1.42M</td><td class="n">7.8%</td><td class="n">low</td>
    <td>Listing and attribution, high volume low price</td></tr>
<tr><td>Brake rotor</td><td class="n">&euro;1.39M</td><td class="n">7.7%</td><td class="n">low</td>
    <td>Our best-margin defended line &mdash; 41% gross margin</td></tr>
<tr><td>Fuel filter</td><td class="n">&euro;1.02M</td><td class="n">5.6%</td><td class="n">65%</td>
    <td>Already largely captured &mdash; low return on effort</td></tr>
<tr><td>Urea filter</td><td class="n">&euro;0.92M</td><td class="n">5.1%</td><td class="n">11%</td>
    <td>Fits the wrong generation of trucks in our data</td></tr>
<tr><td style="color:#6b6256">Oil filter</td><td class="n" style="color:#6b6256">&euro;0.32M</td>
    <td class="n" style="color:#6b6256">1.8%</td><td class="n" style="color:#6b6256">high</td>
    <td style="color:#6b6256">This is our worked example, not our opportunity</td></tr>
</tbody></table>

<div class="callout">
  <b>The single most useful reframe in this paper.</b> We have been leading with oil filters
  because that is the part we can measure cleanly. Oil filters are 1.8% of the gap.
  Clutch disc, brake pad and brake shoe are 46%. If the room only remembers one slide,
  it should be this one.
</div>

<h3>Why the gap splits the way it does</h3>
<div class="two">
  <div><table><tbody>
    <tr><td><span class="tag red">Substitution</span></td><td class="n">&euro;11.40M</td><td class="n">49%</td></tr>
    <tr><td><span class="tag amber">Under-service</span></td><td class="n">&euro;9.56M</td><td class="n">41%</td></tr>
    <tr><td><span class="tag grey">Catalogue gap</span></td><td class="n">&euro;2.18M</td><td class="n">9%</td></tr>
  </tbody></table></div>
  <div>
    <p class="small"><b>Substitution</b> means the truck was repaired, the part was fitted, but
    it was not ours. That is won or lost on price and availability. <b>Under-service</b> means
    the job never happened at the dealer at all &mdash; a workshop demand problem.
    <b>Catalogue gap</b> means we had no number to sell.</p>
    <p class="small">These need opposite responses: a price defence versus demand generation.
    Treating them as one pool is why our plans have been vague.</p>
  </div>
</div>
""", "Gap by product family and by cause, calendar 2025. Cause split is a 2026 model-year file.")

p5 = page(5, "The three things we cannot see properly", """
<p class="lead">This is the least comfortable page in the paper, which is why it is early.</p>

<h3>1. We have no dealer-level sales data for our largest markets after the UK</h3>
<p>For six markets we can see what dealers bought and sold on. For the rest we only see what
our distributors bought from us. That means we cannot tell whether a distributor is holding
stock, losing share in the workshop, or pushing a competitor part &mdash; and we cannot
measure whether our own actions changed anything.</p>
<div class="two">
  <div>{chart_placeholder}</div>
  <div>
    <table><thead><tr><th>Market</th><th class="n">2025 billed</th><th>Dealer detail</th></tr></thead><tbody>
    <tr><td>ITUK</td><td class="n">&euro;5.56M</td><td><span class="tag green">yes</span></td></tr>
    <tr><td>IUK</td><td class="n">&euro;6.13M</td><td><span class="tag green">yes</span></td></tr>
    <tr><td>UTI</td><td class="n">&euro;3.33M</td><td><span class="tag green">yes</span></td></tr>
    <tr><td>Ireland</td><td class="n">&euro;1.19M</td><td><span class="tag green">yes</span></td></tr>
    <tr><td>Greece</td><td class="n">&euro;0.52M</td><td><span class="tag green">yes</span></td></tr>
    <tr><td>Portugal</td><td class="n">&euro;1.71M</td><td><span class="tag green">yes</span></td></tr>
    <tr><td><b>Germany</b></td><td class="n"><b>&euro;2.54M</b></td><td><span class="tag red">no</span></td></tr>
    <tr><td><b>Belgium / NL</b></td><td class="n"><b>&euro;2.11M</b></td><td><span class="tag red">no</span></td></tr>
    <tr><td><b>UMI (Israel)</b></td><td class="n"><b>&euro;3.32M</b></td><td><span class="tag red">no</span></td></tr>
    </tbody></table>
    <p class="small">Adding those three takes us from 57% to about 79% of billed euro visible
    at dealer level.</p>
  </div>
</div>

<h3>2. Six months of Portugal are simply missing</h3>
<div class="amber-note">
  <b>Found while writing this paper.</b> Portugal is missing March to August 2025 from our
  billing data &mdash; six consecutive months. We checked all sixteen markets: Portugal is the
  only one with a gap, and the gap is exactly those months. Portugal's 2025 total is therefore
  about half what it should be. <b>Consequence:</b> no Portugal comparison against last year
  can be trusted, and Portugal has been under-represented in network totals. This needs fixing
  before any Portugal story is told.
</div>

<h3>3. Our own targets are partly a placeholder</h3>
<p>Nine of sixteen markets use a flat &euro;250 per truck per year as the target. It is not
measured. Depending on what the real number is, our capture rate is somewhere between 44% and
51%. We are not hiding that, but it should be stated whenever the number is used.</p>
""".replace("{chart_placeholder}", chart("c_cover", "Pie chart: share of billed euros that has dealer-level detail", 240), 1),
   "Data visibility by market, and known source gaps.")

p6 = page(6, "The forward picture: the ceiling grows on its own", f"""
<p class="lead">Even if we change nothing, the opportunity in front of us grows about 22% by
2030, purely because more trucks are on the road and the parc is getting older.</p>

<div class="two">
  <div>{chart("c_run", "Line chart of the target-spend envelope from 2026 to 2030 in millions of euros", 330)}</div>
  <div>
    <table><thead><tr><th>Year</th><th class="n">Envelope</th><th class="n">At today's capture</th></tr></thead><tbody>
    <tr><td>2026</td><td class="n">&euro;63.9M</td><td class="n">&euro;32.9M</td></tr>
    <tr><td>2027</td><td class="n">&euro;67.4M</td><td class="n">&euro;34.9M</td></tr>
    <tr><td>2028</td><td class="n">&euro;70.8M</td><td class="n">&euro;36.9M</td></tr>
    <tr><td>2029</td><td class="n">&euro;74.3M</td><td class="n">&euro;39.0M</td></tr>
    <tr><td>2030</td><td class="n">&euro;77.8M</td><td class="n">&euro;41.0M</td></tr>
    </tbody></table>
    <p class="small">These projections hold our capture rate flat at today's level. That is a
    deliberate choice: it separates parc growth (which we get for free) from capture
    improvement (which we have to earn).</p>
  </div>
</div>

<h3>Where the growth in the road fleet is</h3>
<p>Growth in the envelope is not spread evenly. These markets grow fastest between 2024 and
2030 on the vehicle parc alone:</p>
<table><thead><tr><th>Market</th><th class="n">Fleet growth to 2030</th><th class="n">Envelope in 2030</th></tr></thead><tbody>
<tr><td>Ireland</td><td class="n">+149%</td><td class="n">&euro;2.23M</td></tr>
<tr><td>Greece</td><td class="n">+106%</td><td class="n">&euro;1.65M</td></tr>
<tr><td>Iceland</td><td class="n">+104%</td><td class="n">&euro;0.17M</td></tr>
<tr><td>Portugal</td><td class="n">+90%</td><td class="n">&euro;5.67M</td></tr>
<tr><td>Cyprus</td><td class="n">+83%</td><td class="n">&euro;1.14M</td></tr>
<tr><td>Germany</td><td class="n">+81%</td><td class="n">&euro;6.78M</td></tr>
<tr><td>Romania</td><td class="n">+75%</td><td class="n">&euro;0.43M</td></tr>
<tr><td style="color:#6b6256">United Kingdom (ITUK)</td><td class="n" style="color:#6b6256">+26%</td>
    <td class="n" style="color:#6b6256">&euro;21.04M</td></tr>
</tbody></table>

<div class="callout green">
  <b>Why this matters for the decision.</b> The UK is still the biggest prize in absolute
  terms by a wide margin, but it is not growing fast. The markets that grow fastest are small
  today. The plan should therefore do two different jobs: <b>defend and convert in the UK</b>,
  and <b>get in early where the fleet is compounding</b>, starting with Germany and Portugal.
</div>
""", "Envelope = vehicles in service projected forward, times target spend per truck. Capture held flat on purpose.")

p7 = page(7, "How we are actually performing", f"""
<p class="lead">Two years of billing, at half-year grain so the comparison is like for like.</p>

<table><thead><tr><th>Period</th><th class="n">Parts billed</th><th class="n">vs prior year</th></tr></thead><tbody>
<tr><td>2024 full year</td><td class="n">&euro;33.15M</td><td class="n">&mdash;</td></tr>
<tr><td>2025 full year</td><td class="n">&euro;32.38M</td><td class="n">-2.3%</td></tr>
<tr><td>2025 first half</td><td class="n">&euro;16.72M</td><td class="n">&mdash;</td></tr>
<tr><td><b>2026 first half</b></td><td class="n"><b>&euro;18.71M</b></td><td class="n"><b>+11.9%</b></td></tr>
</tbody></table>

<div class="callout navy">
  <b>The headline you would not guess from our own dashboards:</b> half-one 2026 is
  <b>up 11.9%</b> on half-one 2025, and the second quarter of 2026 is the second-strongest
  quarter in three years. We are not in decline. One of our own data files says we are
  down 43% because it compares part-year sales against a full-year target &mdash; that file
  has been corrected this week.
</div>

<h3>Who grew and who did not, first half 2026 against first half 2025</h3>
{chart("c_h1", "Grouped bar chart comparing first half 2025 and first half 2026 billing by market", 330)}
<p class="small">Portugal appears at the top of this chart but its bar is not comparable &mdash;
see the note below and page 5. UMI is the only large market that shrank.</p>
<table><thead><tr><th>Market</th><th class="n">H1 2025</th><th class="n">H1 2026</th><th class="n">Change</th><th>Read</th></tr></thead><tbody>
<tr><td>ITUK</td><td class="n">&euro;2.67M</td><td class="n">&euro;3.73M</td><td class="n">+40%</td><td>Strong</td></tr>
<tr><td>IUK</td><td class="n">&euro;3.10M</td><td class="n">&euro;3.41M</td><td class="n">+10%</td><td>Steady</td></tr>
<tr><td>UTI (Israel)</td><td class="n">&euro;1.71M</td><td class="n">&euro;1.79M</td><td class="n">+4%</td><td>Steady</td></tr>
<tr><td>Belgium / NL</td><td class="n">&euro;1.08M</td><td class="n">&euro;1.39M</td><td class="n">+28%</td><td>Strong</td></tr>
<tr><td>Germany</td><td class="n">&euro;0.81M</td><td class="n">&euro;0.97M</td><td class="n">+19%</td><td>Good</td></tr>
<tr><td>Sweden</td><td class="n">&euro;0.72M</td><td class="n">&euro;0.89M</td><td class="n">+23%</td><td>Good</td></tr>
<tr><td>Norway</td><td class="n">&euro;0.77M</td><td class="n">&euro;0.87M</td><td class="n">+13%</td><td>Good</td></tr>
<tr style="background:#fdeceb"><td><b>UMI (Israel)</b></td><td class="n">&euro;1.66M</td><td class="n">&euro;1.36M</td><td class="n"><b>-19%</b></td><td>The one real problem</td></tr>
<tr><td>Ireland</td><td class="n">&euro;0.65M</td><td class="n">&euro;0.54M</td><td class="n">-16%</td><td>Worth a look</td></tr>
</tbody></table>

<div class="amber-note small">
  <b>Portugal is deliberately not in this table.</b> Its apparent explosive growth is the
  six-month data hole described on page 5, not performance. It cannot be compared until fixed.
</div>
""", "Half-year comparison on the same basis. Calendar 2026 first half = January to June.")

p8 = page(8, "The one market going backwards: UMI", f"""
<p class="lead">UMI bills {eur(3_319_344)} a year from {18_542:,} pickups in Israel. It is the
only large market that shrank while the rest of the network grew. It is also the market where
our data is weakest, so the diagnosis has three separate pieces.</p>

<h3>Piece one: February and March were a genuine loss</h3>
<p>On a like-for-like monthly basis UMI billed &euro;712k in February and March 2025 and
&euro;403k in the same two months of 2026 &mdash; about <b>&euro;309k less</b>. That is real.
Noise elsewhere in the data explains the rest, but not this.</p>

<h3>Piece two: this has been sliding for three years</h3>
<table><thead><tr><th>First quarter of</th><th class="n">Billed</th><th class="n">Change</th></tr></thead><tbody>
<tr><td>2023</td><td class="n">&euro;1.24M</td><td class="n">&mdash;</td></tr>
<tr><td>2024</td><td class="n">&euro;1.01M</td><td class="n">-18%</td></tr>
<tr><td>2025</td><td class="n">&euro;1.02M</td><td class="n">+1%</td></tr>
<tr><td><b>2026</b></td><td class="n"><b>&euro;0.71M</b></td><td class="n"><b>-30%</b></td></tr>
</tbody></table>
<p>UMI's first quarter has fallen in three of the last four years. This is not a sudden event;
it is a slow structural loss of roughly 14% a year that we have never explained.</p>

<h3>Piece three: for April onwards, we simply cannot see</h3>
<p>From April 2026 the whole network's SAP export lost its order-type field. That matters far
more for UMI than anyone else because <b>warranty is 54% of UMI's parts volume</b> &mdash;
and warranty can only be identified through that field. UMI's April-to-June figure looks like
&euro;644k. It is very likely substantially higher. We should not draw a conclusion from it.</p>

<div class="callout">
  <b>What UMI has in common with the network.</b> Warranty claims across the network fell 25%
  from 2024 to 2025 (&euro;4.22M to &euro;3.18M) while parts billing stayed flat. For UMI the
  drop is 40%. Either our product quality genuinely improved or claim authorisation tightened
  and the work moved somewhere else. We cannot tell from our data, and we should find out
  before we build any plan on UMI.
</div>

<h3>What to do about UMI</h3>
<ol>
  <li><b>Ask UMI for dealer-level sales data.</b> They are the largest market with no dealer
      visibility and the only one declining. Without it we are guessing.</li>
  <li><b>Get the SAP re-export with the order-type field</b> for April onwards. This unblocks
      UMI, and also the whole network's warranty picture for that quarter.</li>
  <li><b>Then</b> decide whether this is a share loss, a pricing problem, or a stock problem.
      Do not decide before the data arrives.</li>
</ol>
""", "UMI sold-to 1797 only. UTI (1799) is a separate distributor and is never blended into these figures.")

p9 = page(9, "Where the growth actually comes from: six levers", f"""
<p class="lead">Six different mechanisms, from cheapest to slowest. Each one is a different
kind of action &mdash; they are not six versions of the same idea.</p>

{chart("c_lever", "Bar chart of the six growth levers sized in millions of euros", 300)}
<p class="small">Lever sizes are the measured pools they act on, not a forecast of what we will
win. Warranty and connected-services bars are flows, not one-off gaps, so they are not directly
comparable with the three before them.</p>

<table><thead><tr><th>#</th><th>Lever</th><th>How it makes money</th>
<th class="n">Size</th><th class="n">Effort</th><th>Gate</th></tr></thead><tbody>
<tr><td>1</td><td><b>Price the parts we do not price</b></td>
    <td>They are already being sold; nobody has set a list price</td>
    <td class="n">&euro;4.96M</td><td class="n">Low</td><td>A named owner</td></tr>
<tr><td>2</td><td><b>Defend the lines we are undercut on</b></td>
    <td>Keep volume that is currently walking to competitors on price</td>
    <td class="n">&euro;11.40M</td><td class="n">Medium</td><td>Better price evidence</td></tr>
<tr><td>3</td><td><b>Win clutch and brake back</b></td>
    <td>Fix fitment and coverage so the part exists to sell</td>
    <td class="n">&euro;8.39M</td><td class="n">Medium</td><td>A pilot, not a programme</td></tr>
<tr><td>4</td><td><b>Get dealer data for DE, BE, UMI</b></td>
    <td>Nothing directly &mdash; it is what makes 2 and 3 measurable</td>
    <td class="n">&euro;8.90M<br>visible</td><td class="n">Low</td><td>Two requests</td></tr>
<tr><td>5</td><td><b>Turn warranty visits into sales</b></td>
    <td>Warranty is our most frequent, most compliant workshop touch</td>
    <td class="n">&euro;4.72M<br>flow</td><td class="n">High</td><td>Explain the claim drop first</td></tr>
<tr><td>6</td><td><b>Connected-vehicle services</b></td>
    <td>A subscription revenue line, not parts</td>
    <td class="n">&euro;1.5&ndash;7.8M</td><td class="n">Very high</td><td>An Isuzu Motors decision</td></tr>
</tbody></table>

<div class="callout navy">
  <b>Read the effort column honestly.</b> Lever 1 is the cheapest euro and has been sitting
  there since August. It is not a sales problem; it is that nobody owns it. Lever 6 is the
  biggest number and the one we control least &mdash; it is not ours to decide alone.
</div>

<h3>How these fit together</h3>
<p>Levers 1 and 4 are quick and unblock other things. Lever 2 is where the largest single pool
of money is, and it needs better price evidence before we act. Lever 3 needs a proper pilot so
we learn whether the money is really reachable. Lever 5 is the biggest cultural change &mdash;
treating a warranty visit as a sales opportunity rather than a cost. Lever 6 is a different
business and should be decided at a different level.</p>
""", "Lever sizes are the measured pools they act on, not a forecast of what we will win.")

p10 = page(10, "Lever 1 &mdash; price the parts we do not price", f"""
<p class="lead">We sell {eur(4_955_737)} of parts a year that have no usable list price. That
is 15.1% of the whole parts book, across {NOLIST_PN} part numbers. We are shipping them,
invoicing them, and never setting their price.</p>

<div class="kpibar">
  <div class="kpi"><div class="l">Unpriced parts, 2025</div><div class="v">&euro;4.96M</div>
    <div class="s">15.1% of the parts book</div></div>
  <div class="kpi"><div class="l">Part numbers</div><div class="v">251</div>
    <div class="s">individually identifyable</div></div>
  <div class="kpi"><div class="l">Effort to act</div><div class="v">Low</div>
    <div class="s">it is a data fix, not a demand fight</div></div>
</div>

<h3>Why this is the cheapest money on the table</h3>
<p>Every other lever in this paper requires us to change customer behaviour. This one requires
us to change our own paperwork. The parts already arrive in orders, already ship, already get
invoiced. What is missing is a price on the record. There is no demand to create and no
competitor to beat.</p>

<h3>What is actually in there</h3>
<table><thead><tr><th>Reason</th><th class="n">Part numbers</th><th class="n">Value</th><th>What it means</th></tr></thead><tbody>
<tr><td>Not in the price list at all</td><td class="n">16</td><td class="n">&euro;534k</td>
    <td>We have no record to price from</td></tr>
<tr><td>On the list, no usable price</td><td class="n">15</td><td class="n">&euro;58k</td>
    <td>A field exists and is empty</td></tr>
</tbody></table>
<p class="small">The two lines above cover the part numbers we can identify individually
(&euro;592k). The remaining volume sits in the same two categories at part-number grain not
broken out here. The total is {eur(4_955_737)} on {NOLIST_PN} part numbers.</p>

<div class="callout">
  <b>One caution that must travel with this number.</b> The single largest unpriced line is a
  lubricant item at &euro;434k which is currently parked &mdash; that business is switched off
  by decision, so it should not be counted as recoverable. Excluding parked lines, the
  actionable remainder is smaller but still material.
</div>

<h3>What would actually happen</h3>
<ol>
  <li><b>Name an owner.</b> This has been ranked and documented since August. It has never had
      a person responsible for closing it.</li>
  <li><b>Split the list.</b> Parked lines stay parked. Real lines get a price set from the
      nearest comparable part we do price.</li>
  <li><b>Fix the empty fields</b> for the &euro;58k tranche at the same time &mdash; it is the
      same piece of work.</li>
  <li><b>Check it monthly</b> so new unpriced parts do not appear silently.</li>
</ol>
""", "Source: pricing history findings, calendar 2025. Status of this analysis is internally reviewed, not externally cleared.")

p11 = page(11, "Lever 2 &mdash; what I mean by 'defend the lines we are undercut on'", f"""
<p class="lead">This is the lever you asked me to explain plainly. Here it is without jargon.</p>

<h3>The situation, in one paragraph</h3>
<p>When a truck needs a brake pad, the workshop has a choice. They can fit ours, or they can
fit a competitor's part that does the same job. On a large share of our parts, the competitor's
part is being sold for <b>less than half</b> what ours costs. So the repair happens, the pad
gets fitted, and it is not ours. We did all the work of getting the part into the market and
someone else took the sale.</p>

<h3>Why we call it "substitution"</h3>
<p>Because nothing is missing. It is not a coverage problem and not a demand problem. The
volume arrives at the workshop exactly as we expected. It just leaves as somebody else's
part. In money terms: <b>{eur(11_400_000)} a year</b>, which is 49% of our entire measured
gap &mdash; the single largest pool in the business.</p>

{chart("c_cause", "Bar chart splitting the gap by cause: substitution, under-service and catalogue", 250)}

<h3>What the price evidence actually shows</h3>
<div class="two">
  <div>
    <table><thead><tr><th>Measure</th><th class="n">Value</th></tr></thead><tbody>
    <tr><td>Typical competitor price vs ours</td><td class="n">0.42</td></tr>
    <tr><td>Part numbers we have price evidence for</td><td class="n">130</td></tr>
    <tr><td>Share of part numbers in the book</td><td class="n">0.77%</td></tr>
    <tr><td>Share of billed euro those parts cover</td><td class="n">22.2%</td></tr>
    <tr><td>Where the evidence is undated</td><td class="n">28%</td></tr>
    </tbody></table>
  </div>
  <div>
    <h4>Read that table carefully</h4>
    <p class="small">A ratio of 0.42 means a competitor part sells for about 42% of our price.
    On brake pads and brake shoes that is a very large gap to defend.</p>
    <p class="small"><b>But be honest about the evidence.</b> We have checked prices on 130 part
    numbers out of roughly 16,800 we bill. Those 130 do cover 22% of billed value, so they are
    commercially relevant &mdash; but more than a quarter of the price points come from a file
    with no date on it. We should not present a 0.42 ratio as a network-wide truth.</p>
  </div>
</div>

<h3>What defending this actually means in practice</h3>
<ol>
  <li><b>Do not cut price across the board.</b> That gives away margin on parts where we are
      already competitive, and most of the book is not under attack.</li>
  <li><b>Work line by line, worst first.</b> Rank the parts we bill most by how badly we are
      undercut, and look at the top slice &mdash; not the whole catalogue.</li>
  <li><b>Decide per line:</b> hold the price and defend on service and availability, or move the
      price and keep the volume. Both are legitimate. Doing neither is how we lose the sale.</li>
  <li><b>Watch one number:</b> our price compared with the competitor's, for those lines, over
      time. If that ratio is falling and volume is flat, we are losing share quietly.</li>
</ol>

<div class="callout green">
  <b>The commercial judgement in one sentence.</b> We are being undercut hardest exactly where
  the euro is biggest &mdash; brake and clutch &mdash; and our competitors are winning those
  sales on price, not on the part. That is the fight worth having, and it is winnable because
  the demand is already there.
</div>
""", "Price comparison is a scraped sample, not a census. Treat the direction as reliable and the exact ratio as indicative.")

p12 = page(12, "Lever 3 &mdash; win clutch and brake back", f"""
<p class="lead">The biggest single pool of money in the business is clutch and brake. Here is
what is known, and what has to be tested before we spend on it.</p>

<h3>Where the money is</h3>
<table><thead><tr><th>Product family</th><th class="n">Gap</th><th>Mainly in</th>
<th>Is it reachable</th></tr></thead><tbody>
<tr><td>Clutch disc</td><td class="n">&euro;3.14M</td><td>UK pickups</td><td>Needs a fitment check</td></tr>
<tr><td>Brake pad</td><td class="n">&euro;2.78M</td><td>UK, Israel, UMI</td><td>Price-led, reachable</td></tr>
<tr><td>Brake shoe</td><td class="n">&euro;2.47M</td><td>UK, Belgium</td><td>Price-led, reachable</td></tr>
<tr><td>Clutch pressure plate</td><td class="n">&euro;1.98M</td><td>UK</td><td>Sell as a kit with the disc</td></tr>
<tr><td>Brake rotor</td><td class="n">&euro;1.39M</td><td>UK</td><td>Our best-margin line at 41%</td></tr>
</tbody></table>

<h3>Why some of this is not a sales problem at all</h3>
<p>Clutch disc shows our capture as very low against expected demand. One of our quality
checks says the defect is a structural one: the part exists but the fitment and the part-number
coverage do not line up, so the workshop cannot order the right number for the truck in front
of them. That is a catalogue problem. It does not get fixed by a sales campaign, and anyone
proposing one should be asked which part number they would sell.</p>

<div class="callout">
  <b>Before we spend anything:</b> verify whether the clutch and brake gap is genuinely
  addressable (price and availability) or structural (fitment and catalogue).
  The answer decides which lever we are pulling &mdash; and a structural gap is not a price
  problem, so cutting price there would cost margin and change nothing.
</div>

<h3>How to test it cheaply</h3>
<ol>
  <li><b>Two markets only:</b> the UK pickup market and Belgium. They have the largest measured
      brake and clutch gaps, and they behave differently from each other, so we learn something
      either way.</li>
  <li><b>Agree what winning looks like before starting.</b> A specific improvement in the share
      of clutch and brake jobs that use our part, measured market by market, month by month.</li>
  <li><b>Watch for damage:</b> if our price advantage against competitors gets worse while
      volume does not improve, stop. That means we discounted for nothing.</li>
  <li><b>Fix the baseline first.</b> The pilot cannot start in Belgium until we have dealer-level
      data there &mdash; that is lever 4. We cannot measure a lift without a starting point.</li>
</ol>

<div class="amber-note">
  <b>An honest warning.</b> The sample size for this pilot has not been properly calculated
  yet. Clutch and brake are replaced roughly once every year or two per truck, so the numbers
  per dealer per month are small. Do not start the pilot on a guess about how many dealers are
  needed &mdash; work that out from the dealer data first, or the pilot will be too small to
  read and we will conclude "no opportunity" when we simply did not measure enough.
</div>
""", "Gap by product family, calendar 2025. Capture figures are the network convention, never the IML service-schedule lane.")

p13 = page(13, "Lever 4 &mdash; see the three markets we are blind in", f"""
<p class="lead">This lever does not make a single euro of sales on its own. It is what makes
everything else measurable, and it costs two requests.</p>

<div class="two">
  <div>{chart("c_cover2", "Share of billed euros with dealer-level detail, before and after the three requests", 230)}</div>
  <div>
    <table><thead><tr><th>Market</th><th class="n">2025 billed</th></tr></thead><tbody>
    <tr><td>Germany</td><td class="n">&euro;2.54M</td></tr>
    <tr><td>Belgium / Netherlands</td><td class="n">&euro;2.11M</td></tr>
    <tr><td>UMI (Israel)</td><td class="n">&euro;3.32M</td></tr>
    <tr style="background:#e9f5f0"><td><b>Total to unlock</b></td><td class="n"><b>&euro;7.97M</b></td></tr>
    </tbody></table>
    <p class="small">Bringing these three in moves dealer-level visibility from 57% to roughly
    79% of billed euro at no cost to anyone.</p>
  </div>
</div>

<h3>What we ask for, and what we do not</h3>
<p>We do not ask distributors to adopt a shared system or a standard file layout &mdash; they
each run different software and that request has failed before. We ask for the minimum that can
be mapped:</p>
<ol>
  <li>Part number, as they hold it.</li>
  <li>Quantity sold to dealers, per calendar month.</li>
  <li>2025 and 2026, so we can compare.</li>
  <li>Dealer name, only if they can give it &mdash; this is what unlocks the dealer-level view.</li>
</ol>
<p class="small"><b>Not needed:</b> prices, margins, or stock. Quantity is enough; we revalue
it using our own billing prices.</p>

<h3>Precedent, so this is not a hypothetical</h3>
<p>Portugal provided exactly this in early September and it took under a week to normalise.
Where a distributor has the data, getting it works. Germany, Belgium and Israel are the three
largest remaining gaps in the network by billing.</p>

<div class="callout navy">
  <b>One thing to fix before the next one arrives.</b> The Portugal file was filed correctly
  and registered, but the step that converts it into usable form was never written &mdash; so
  it sat unused for nearly two weeks while we assumed it was done. The intake process should
  not allow that, and it now does not.
</div>
""", "Dealer-level visibility measured as share of billed euros that can be traced to a dealer, calendar 2025.")

p14 = page(14, "Lever 5 &mdash; turn warranty visits into sales", f"""
<p class="lead">Warranty is our most frequent and most compliant workshop visit. We currently
treat it as a cost to absorb rather than a sales opportunity to use.</p>

<div class="kpibar">
  <div class="kpi"><div class="l">Warranty as share of billed parts</div><div class="v">14.6%</div>
    <div class="s">about &euro;4.72M in 2025</div></div>
  <div class="kpi"><div class="l">Claim expense 2024</div><div class="v">&euro;4.22M</div>
    <div class="s">&mdash;</div></div>
  <div class="kpi" style="border-top-color:#c0352d"><div class="l">Claim expense 2025</div>
    <div class="v">&euro;3.18M</div><div class="s">down 25%</div></div>
</div>

<h3>Two things are true at once here</h3>
<p><b>First, warranty distorts how the market looks.</b> In one of our markets, UMI, warranty is
54% of everything the distributor buys. That means any comparison of that market against
another is really comparing warranty policy, not commercial performance. We flag this everywhere
it appears.</p>
<p><b>Second, warranty is an unexploited sales channel.</b> A warranty repair brings a truck
into a dealer with a known fault, a compliant customer, and a technician already working on the
vehicle. It is the highest-quality contact we get with the fleet. We do not systematically use
it to sell anything else.</p>

<h3>The decline needs explaining before we build on it</h3>
<div class="amber-note">
  Claim expense fell 25% between 2024 and 2025 while parts billing stayed flat. There are two
  possible reasons and we cannot yet tell them apart:
  <ul style="margin-bottom:0">
    <li>our products genuinely got better, so fewer claims are needed &mdash; a good story; or</li>
    <li>claims are being authorised less generously, and the work has moved to customer-paid
        repair somewhere we cannot see &mdash; which would mean real revenue has leaked out of
        the network while our numbers looked fine.</li>
  </ul>
  These have opposite implications. We should find out which it is before treating warranty as
  a growth channel.
</div>

<h3>What we would need</h3>
<ol>
  <li>A warranty extract that shows, for each claim, the reason, the parts used and the labour
      hours. Today we have expense and volume but not the reason.</li>
  <li>The order-type field back in the SAP export from April 2026 onwards, so warranty is
      visible again for the current year.</li>
  <li>A comparison across markets of how often a warranty visit results in any additional
      customer-paid work. That number, if it is low anywhere, is a direct opportunity.</li>
</ol>
""", "Warranty claim expense by year; warranty share of billed parts has its own integrity caveat, see page 18.")

p15 = page(15, "Lever 6 &mdash; connected-vehicle services, and the honest caveat", f"""
<p class="lead">This is the largest number in the paper and the one we control least. It is
included because it belongs in the decision, not because it is ready.</p>

<div class="callout">
  <b>Read the next paragraph before the numbers.</b> We hold <b>no connected-vehicle or
  subscription data at all</b>. Everything on this page is external industry evidence, sized
  against our own fleet. It is a modelled option, not a forecast, and it must never be merged
  into an internal sales figure.
</div>

<h3>What the industry evidence says</h3>
<table><thead><tr><th>Measure</th><th>Value</th><th>Source</th></tr></thead><tbody>
<tr><td>Commercial vehicle telematics market growth</td><td>about 15% a year</td><td>Industry analyst</td></tr>
<tr><td>Typical subscription price per vehicle per month</td><td>&euro;14 to &euro;110</td><td>Industry analyst</td></tr>
<tr><td>Share of that market held by vehicle manufacturers</td><td>59%</td><td>Industry analyst</td></tr>
<tr><td>Predictive maintenance subscriptions, global</td><td>growing about 19% a year</td><td>Industry analyst</td></tr>
</tbody></table>

<h3>Sized against our own fleet</h3>
<p>We have roughly 163,000 Isuzu vehicles in service across the sixteen markets. Applying a
subscription price to a share of them gives a very large range:</p>
<table><thead><tr><th>Share of fleet subscribing</th><th class="n">At &euro;14 / month</th>
<th class="n">At &euro;18 / month</th><th class="n">At &euro;37 / month</th></tr></thead><tbody>
<tr><td>5% of the fleet</td><td class="n">&euro;1.37M/yr</td><td class="n">&euro;1.76M/yr</td><td class="n">&euro;3.62M/yr</td></tr>
<tr><td>10% of the fleet</td><td class="n">&euro;2.74M/yr</td><td class="n">&euro;3.52M/yr</td><td class="n">&euro;7.25M/yr</td></tr>
<tr><td>20% of the fleet</td><td class="n">&euro;5.48M/yr</td><td class="n">&euro;7.05M/yr</td><td class="n">&euro;14.49M/yr</td></tr>
</tbody></table>

<div class="callout green">
  <b>The finding that matters:</b> even on the most conservative assumption &mdash; 5% of the
  fleet at the bottom of the price range &mdash; this is <b>&euro;1.4M a year of recurring
  revenue, from services rather than parts</b>. That is comparable to the entire realistic
  three-year upside from closing the component gap. It deserves a decision rather than silence.
</div>

<h3>But it is not ours to decide alone</h3>
<ol>
  <li><b>Who owns the data?</b> Vehicle data ultimately sits with Isuzu Motors, not with us or
     our distributors. This is a decision at that level, not a local pilot.</li>
  <li><b>Legal review is needed.</b> Connected-vehicle data is regulated territory in Europe
     and would involve our data protection process before anything is offered to a customer.</li>
  <li><b>It is a different business.</b> A subscription line needs billing, support and service
     levels we do not currently run for parts.</li>
</ol>
<p><b>The honest recommendation:</b> put it on the agenda as a decision to be taken or
explicitly declined, in writing. What we should stop doing is leaving it undefined, because
that is how a €1.4M-a-year question stays unanswered for another year.</p>
""", "All figures on this page are externally sourced and modelled. They are not ISZE data and must not be quoted as such.")

p16 = page(16, "What to do, in what order", f"""
<p class="lead">Six levers, sequenced. The first four are cheap and mostly unblock other work.
Nothing here needs new systems.</p>

<h3>Next ninety days</h3>
<table><thead><tr><th>Action</th><th>Owner</th><th>Why now</th></tr></thead><tbody>
<tr><td><b>Name an owner for the &euro;4.96M of unpriced parts</b></td><td>To assign</td>
    <td>Cheapest money on the table and it has no owner</td></tr>
<tr><td><b>Request dealer data from Germany, Belgium and UMI</b></td><td>To assign</td>
    <td>Takes visibility from 57% to 79%; unblocks the Belgium pilot</td></tr>
<tr><td><b>Fix the Portugal six-month gap</b></td><td>Data</td>
    <td>Currently makes Portugal unusable for comparison</td></tr>
<tr><td><b>Get the SAP re-export with the order-type field</b></td><td>Data</td>
    <td>Restores warranty visibility for April 2026 onwards</td></tr>
<tr><td><b>Work out the pilot sample size from dealer data</b></td><td>Analytics</td>
    <td>The brake and clutch pilot cannot start without it</td></tr>
<tr><td><b>Decide the connected-vehicle question, in writing</b></td><td>Management</td>
    <td>Either commit or decline. Stop leaving it open</td></tr>
</tbody></table>

<h3>Three to twelve months</h3>
<ol>
  <li><b>Rank the undercut lines and act on the worst slice.</b> Not the whole catalogue &mdash;
     the part numbers where we bill most and the price gap is widest.</li>
  <li><b>Run the brake and clutch pilot</b> in the UK pickup market and Belgium, with success
     criteria agreed in advance and a decision to stop if it does not work.</li>
  <li><b>Explain the warranty claim decline.</b> Is it quality or is it authorisation? The answer
     changes what we do next.</li>
  <li><b>Improve the price evidence.</b> Today we have checked 130 part numbers out of about
     16,800, and a quarter of those points are undated. Whatever we conclude from price is only
     as good as that sample.</li>
</ol>

<h3>Twelve to thirty-six months</h3>
<ol>
  <li><b>Structural fix for clutch and brake fitment</b> if the pilot shows the gap is
     catalogue-driven rather than price-driven.</li>
  <li><b>Warranty as a deliberate sales channel</b>, with targets, once the decline is understood.</li>
  <li><b>A position on connected-vehicle services</b>, whichever way it is decided.</li>
</ol>

<div class="callout navy">
  <b>If only one thing gets done:</b> name an owner for the unpriced parts. It is
  &euro;4.96M, it needs no customer conversation, and it has been sitting documented since
  August with nobody responsible for it.
</div>
""", "Owners are shown as roles to assign, not as commitments from named individuals.")

p17 = page(17, "What would change our mind", """
<p class="lead">The conclusions in this paper rest on evidence that could turn out to be wrong.
Here is what would overturn each one, so the paper can be argued with rather than believed.</p>

<table><thead><tr><th>If we found this</th><th>Then this conclusion fails</th></tr></thead><tbody>
<tr><td>Real target spend per truck in the nine flat markets is far above &euro;250</td>
    <td>Our capture rate is lower than stated and the gap is larger &mdash; the plan gets bigger, not smaller</td></tr>
<tr><td>Independent parts volume is much smaller than we assume</td>
    <td>The gap is mostly demand we could never win, and levers 2 and 3 shrink</td></tr>
<tr><td>The clutch and brake gap is a fitment problem, not a price problem</td>
    <td>Cutting price there costs margin and changes nothing; the fix is catalogue work</td></tr>
<tr><td>The warranty claim drop is authorisation tightening</td>
    <td>Revenue has leaked out of the network and our flat billing is hiding it</td></tr>
<tr><td>Portugal's missing months reappear and its 2025 is normal</td>
    <td>Portugal stops being a data story and becomes an ordinary market</td></tr>
<tr><td>UMI's April to June is genuinely down even after warranty is visible</td>
    <td>UMI is a real share loss and needs a market-level recovery plan</td></tr>
<tr><td>Our price sample of 130 part numbers is unrepresentative</td>
    <td>The 0.42 price ratio is wrong and lever 2 needs rebuilding before we act</td></tr>
</tbody></table>

<h3>Verification we know is missing</h3>
<ol>
  <li><b>Retail price coverage.</b> We have checked 0.77% of part numbers and 22% of billed
     value. That is the weakest evidence base in the paper.</li>
  <li><b>Independent volume.</b> We do not know how large the non-Isuzu parts market is in any
     market. Every "gap" figure is a demand model, not an observed loss.</li>
  <li><b>The target-spend placeholder.</b> 37% of the envelope is a flat assumption.</li>
  <li><b>Realised margin by product family.</b> We hold a gross-margin layer for one competitor
     set only. Prioritising by margin rather than by billed euro is not yet possible
     network-wide.</li>
</ol>

<div class="callout">
  <b>How to read any "gap" number in this paper.</b> A gap is the difference between what we
  expected a truck to need and what we actually sold. It is not a measured loss of a known
  sale. It includes jobs that never happened, parts fitted elsewhere, and errors in our own
  demand model. Treat it as the size of the question, not as money waiting to be collected.
</div>
""", "Falsifiers are stated so the analysis can be challenged on evidence rather than opinion.")

p18 = page(18, "Data quality: what you should know before quoting these numbers", """
<p class="lead">Everything in this paper came from our verified sales spine, which passed all
116 of its own checks in August. That does not mean the data is perfect. Here is what is
known to be weak, in plain terms.</p>

<h3>Fixed this week</h3>
<table><thead><tr><th>Issue</th><th>What it did</th><th>Status</th></tr></thead><tbody>
<tr><td>A file compared part-year sales against a full-year target</td>
    <td>Made every market show as failing and read as a 43% collapse that never happened</td>
    <td><span class="tag green">corrected</span></td></tr>
<tr><td>Portugal's sales-to-dealer file was filed but never processed</td>
    <td>Portugal looked absent from that analysis for two weeks</td>
    <td><span class="tag green">done</span></td></tr>
</tbody></table>

<h3>Still open</h3>
<table><thead><tr><th>Issue</th><th>Effect on this paper</th></tr></thead><tbody>
<tr><td><b>Portugal missing March to August 2025</b></td>
    <td>Any Portugal comparison is invalid; Portugal under-represented in 2025 network totals</td></tr>
<tr><td><b>The order-type field is missing from April 2026</b></td>
    <td>Warranty cannot be separated from commercial sales for the current quarter, network-wide.
        Hits UMI hardest because warranty is 54% of its volume</td></tr>
<tr><td><b>Credit notes and returns</b></td>
    <td>Excluded on a documented judgement call, not on a confirmed system rule. If the rule is
        wrong, capture and parts totals both move</td></tr>
<tr><td><b>Target spend is a placeholder for nine markets</b></td>
    <td>Our capture rate is a range, 44% to 51%, not a single number</td></tr>
<tr><td><b>Air filter interval is an assumption, not a confirmed figure</b></td>
    <td>Air filter gap figures should be quoted as provisional until confirmed</td></tr>
<tr><td><b>Account-health and defection alerts use draft thresholds</b></td>
    <td>Not validated. Do not use as a call list</td></tr>
<tr><td><b>Competitor price vintages are mixed</b></td>
    <td>Some price points are old, 28% have no date at all</td></tr>
</tbody></table>

<div class="amber-note">
  <b>The most important line on this page.</b> Cost and margin work in this paper uses external
  industry benchmarks, not our own realised margin by product family. We do not hold that data.
  Any figure that converts a sales gap into profit is therefore indicative, and should be
  labelled as such wherever it is used.
</div>
""", "Integrity position as at the date of this paper. Items marked corrected were fixed this week.")

p19 = page(19, "Sources and how to check us", """
<p class="lead">Every number in this paper comes from the verified sales spine or is explicitly
labelled as external. Here is where each family of figures comes from, in plain terms.</p>

<table><thead><tr><th>What</th><th>Where it comes from</th><th>Status</th></tr></thead><tbody>
<tr><td>Parts billed per market and per month</td><td>Verified sales spine, calendar 2025 and 2026</td>
    <td><span class="tag green">verifies</span></td></tr>
<tr><td>Vehicles in service per market</td><td>Vehicle registration counts, by market</td>
    <td><span class="tag green">verifies</span></td></tr>
<tr><td>Target spend per truck</td><td>Market targets, partly a flat placeholder</td>
    <td><span class="tag amber">partly assumed</span></td></tr>
<tr><td>Expected demand and gaps by product family</td><td>Demand model on service intervals</td>
    <td><span class="tag amber">modelled</span></td></tr>
<tr><td>Gap split by cause</td><td>Recovery model, 2026 model year</td>
    <td><span class="tag amber">vintage caveat</span></td></tr>
<tr><td>Dealer-level sales</td><td>Distributor reports, six markets</td>
    <td><span class="tag grey">partial</span></td></tr>
<tr><td>Warranty claim expense</td><td>Warranty claim extracts by market and year</td>
    <td><span class="tag green">verifies</span></td></tr>
<tr><td>Unpriced parts</td><td>Price list against billing</td>
    <td><span class="tag amber">internal only</span></td></tr>
<tr><td>Competitor prices</td><td>Scraped sample, mixed dates</td>
    <td><span class="tag red">thin</span></td></tr>
<tr><td>Gross margin by product family</td><td>One competitor set only</td>
    <td><span class="tag red">not network-wide</span></td></tr>
<tr><td>Forward envelope to 2030</td><td>Fleet projections times target spend</td>
    <td><span class="tag amber">modelled</span></td></tr>
<tr><td>Connected-vehicle sizing</td><td>External industry analysis only</td>
    <td><span class="tag red">external</span></td></tr>
</tbody></table>

<h3>The rule we applied</h3>
<p>Where we had a verified internal number, we used it and did not round it into something
tidier. Where we did not, we either labelled the figure as modelled or external, or we wrote
that we do not know. There are no invented numbers in this paper and no figure borrowed from
a presentation that predates the current verification.</p>

<div class="callout">
  <b>On the status of these figures:</b> several of the underlying analyses are internally
  reviewed but not cleared for use outside the company &mdash; specifically the unpriced-parts
  figures, the competitor price comparison, and the margin layer. This paper is an internal
  document. Anything taken out of it needs that clearance first.
</div>
""", "This page exists so that any figure can be traced and challenged. Ask and you will get the underlying detail.")

p20 = page(20, "The decision in front of you", f"""
<p class="lead">Two questions. Everything else in this paper is detail.</p>

<div class="back">
  <h4>Question one: do we fund capture, or ride the fleet?</h4>
  <p>Our own projections assume we capture no more of the market in 2030 than we do today.
  On that assumption, the envelope growing to &euro;77.8M delivers about &euro;41M anyway,
  roughly &euro;8M more than today, for no extra effort. That is the "ride the fleet" option.</p>
  <p>The alternative is to fund the capture levers &mdash; price, defence, catalogue, data &mdash;
  and try to move the capture rate itself. That is the "buy capture" option. It costs money and
  management attention, and it is the only one that can change our share.</p>
  <p style="margin-bottom:0"><b>Everything in pages 9 to 16 depends on which of these two we
  are doing.</b></p>
</div>

<h3>Question two: what is the one thing that gets done?</h3>
<p>There are six levers and they will not all happen. If only one gets done, the paper's
recommendation is the <b>&euro;4.96M of parts we sell without a price</b>. It needs no customer
conversation, no market data, and no new system. What it needs is a person whose job it is.</p>

<h3>What I would do first, if it were mine</h3>
<ol>
  <li>Name the owner for the unpriced parts. This week.</li>
  <li>Send the three dealer-data requests. They cost nothing and unblock everything measurable.</li>
  <li>Fix Portugal and the order-type field. Both are data defects that make real markets
      unreadable.</li>
  <li>Then decide between riding and buying, with the two questions above answered.</li>
</ol>

<div class="callout green">
  <b>The one thing worth remembering.</b> We bill about half of what the market can absorb.
  The largest pool of money is not a mystery &mdash; it is clutch and brake, and most of it is
  lost on price. We have known the size for months. What has been missing is a decision and an
  owner, not more analysis.
</div>

<p class="small" style="margin-top:6mm">
Prepared for internal ISZE use. Figures are calendar 2025 unless stated and reconcile to the
verified sales spine. Several underlying analyses are not yet cleared for external use &mdash;
see page 19.
</p>
""", "20 / 20")

HTML_JS_TMPL = """<script>__CHARTJS__</script>
<script>
var D = __PAYLOAD__;
var ink = '#52514e', grid = '#e1e0d9';
var NAVY='#1a2b4a', TERRA='#c0552d', GREY='#888780', GREEN='#1d9e75', BLUE='#2a78d6', RED='#e24b4a', AMBER='#eda100';
function base(){
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: grid }, ticks: { color: ink, font: { size: 10 } } },
      y: { grid: { color: grid }, ticks: { color: ink, font: { size: 10 } } }
    }
  };
}
function pretty(s){
  return String(s).replace(/_/g,' ').replace(/\\b\\w/g, function(c){ return c.toUpperCase(); });
}
function hbar(id,o,cols){var el=document.getElementById(id);if(!el||!o)return;
  var op=base();op.indexAxis='y';
  op.scales.x.max=Math.ceil(Math.max.apply(null,o.data)*1.08);
  op.scales.x.ticks.callback=function(v){return '\u20ac'+v+'M';};
  var lbl=(o.labels||[]).map(pretty);
  new Chart(el,{type:'bar',data:{labels:lbl,datasets:[{data:o.data,
    backgroundColor:cols||NAVY,borderRadius:3,barThickness:16}]},options:op});}
function vbar(id,o,cols,suffix){var el=document.getElementById(id);if(!el||!o)return;
  var op=base();op.scales.y.max=Math.ceil(Math.max.apply(null,o.data)*1.15);
  if(suffix)op.scales.y.ticks.callback=function(v){return '\u20ac'+v+suffix;};
  var lbl=(o.labels||[]).map(pretty);
  new Chart(el,{type:'bar',data:{labels:lbl,datasets:[{data:o.data,
    backgroundColor:cols||NAVY,borderRadius:3}]},options:op});}
function line(id,o){var el=document.getElementById(id);if(!el||!o)return;
  var op=base();op.scales.y.ticks.callback=function(v){return '\\u20ac'+v+'M';};
  new Chart(el,{type:'line',data:{labels:o.labels,datasets:[{data:o.data,borderColor:TERRA,
    backgroundColor:'rgba(192,85,45,0.10)',fill:true,tension:0.25,pointRadius:5,
    pointBackgroundColor:TERRA,borderWidth:2.5}]},options:op});}
function dough(id,o){
  var el=document.getElementById(id); if(!el||!o) return;
  new Chart(el, {
    type: 'doughnut',
    data: {
      labels: ['With dealer detail','Without'],
      datasets: [{ data: o.data, backgroundColor: [GREEN,GREY], borderWidth: 0 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '62%',
      plugins: { legend: { position: 'bottom', labels: { color: ink, font: { size: 10 }, boxWidth: 12 } } }
    }
  });
}

hbar('c_rank', D.rank);
hbar('c_cap', D.cap, (D.cap? D.cap.data.map(function(v){return v>=50?GREEN:(v>=35?AMBER:RED);}) : null));
hbar('c_gap', D.gap, TERRA);
hbar('c_cat', D.cat, (D.cat? D.cat.data.map(function(v,i){return i<3?TERRA:GREY;}) : null));
hbar('c_lever', D.lever, (D.lever? D.lever.data.map(function(v,i){return i<3?TERRA:BLUE;}) : null));
hbar('c_cause', D.cause, [RED, AMBER, GREY]);
line('c_run', D.run);
dough('c_cover', D.cover);
dough('c_cover2', D.cover);
vbar('c_war', D.war, [GREY, GREEN], 'M');
function grouped(id,o){var el=document.getElementById(id);if(!el||!o)return;
  var op=base();
  op.scales.y.ticks.callback=function(v){return '\\u20ac'+v+'M';};
  new Chart(el,{type:'bar',data:{labels:o.labels,datasets:[
    {label:'H1 2025',data:o.h25,backgroundColor:GREY,borderRadius:2},
    {label:'H1 2026',data:o.h26,backgroundColor:NAVY,borderRadius:2}]},
    options:Object.assign(op,{plugins:{legend:{display:true,labels:{color:ink,font:{size:10},boxWidth:12}}}})});}
grouped('c_h1', D.h1);
</script>
</body></html>
"""

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>How we grow parts sales &mdash; ISZE growth plan</title>
<style>{CSS}</style></head><body>
{cover.replace("REPLACE_DATE", TODAY)}
{p2}{p3}{p4}{p5}{p6}{p7}{p8}{p9}{p10}{p11}{p12}{p13}{p14}{p15}{p16}{p17}{p18}{p19}{p20}
"""
HTML += (HTML_JS_TMPL
         .replace("__CHARTJS__", CHART)
         .replace("__PAYLOAD__", json.dumps(P)))

OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT} ({len(HTML):,} bytes)")
