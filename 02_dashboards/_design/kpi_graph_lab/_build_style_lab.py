"""Style Lab — the same KPI rendered in genuinely different visual identities.

Jerome's point (2026-09-16): the Graph Lab varied chart FORM but ran one house
style (navy/terracotta/Georgia) through every card. That is the same look in
different shapes. This board renders ONE KPI — spend per truck per year, by
market — in nine distinct visual identities so the LOOK can be chosen.

No CDN, no chart library. Inline SVG + CSS only. Self-contained.
"""
import os, sys, io, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OUT = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_design\kpi_graph_lab\KPI_Style_Lab.html'

# real data: spend per unit CY2025, 17 markets with a denominator
D = [
    ('Hungary', 88.39), ('IUK (UK LCV)', 128.33), ('Greece', 139.04), ('Romania', 163.60),
    ('Denmark', 174.17), ('Norway', 178.65), ('UMI (Israel LCV)', 179.02), ('Cyprus', 185.63),
    ('Germany', 197.27), ('Malta', 198.56), ('Portugal', 209.12), ('Iceland', 210.05),
    ('Belgium', 219.86), ('Finland', 230.83), ('ITUK (UK CV)', 248.54), ('UTI (Israel CV)', 322.32),
    ('Ireland', 388.57),
]
NET = 188.16

h = []
h.append('''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KPI style lab &mdash; one number, nine visual identities</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#e9e6df;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}
.pghead{background:#111;color:#fff;padding:30px 26px 26px}
.pghead h1{margin:0;font-size:1.9rem;font-weight:700;letter-spacing:-.01em}
.pghead p{margin:.5rem 0 0;color:#b9b4ab;max-width:900px;font-size:.94rem;line-height:1.55}
.pghead .meta{margin-top:.9rem;font-size:.78rem;color:#8b867e}
.wrap{max-width:1320px;margin:0 auto;padding:22px 16px 60px}
.slab{background:#ece9e2;border-radius:12px;margin:0 0 26px;overflow:hidden;
box-shadow:0 1px 4px rgba(0,0,0,.09)}
.slabhead{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap;
padding:13px 18px;background:#fff;border-bottom:1px solid #d8d4cb}
.slabhead .n{font-size:.68rem;font-weight:800;letter-spacing:.14em;color:#8a847a}
.slabhead h2{margin:0;font-size:1.02rem;font-weight:700}
.slabhead .why{font-size:.8rem;color:#6d685f;margin-left:auto;max-width:560px;text-align:right}
.slabbody{padding:20px}
.note{font-size:.78rem;color:#6d685f;margin-top:12px;line-height:1.5}

/* ---------- 1. ISZE house (current) ---------- */
.house{background:#f7f4ee;padding:22px}
.house h3{font-family:Georgia,serif;color:#15233c;margin:0 0 3px;font-size:1.03rem}
.house .q{color:#c0552d;font-size:.79rem;font-weight:700;margin-bottom:12px}
.hrow{display:grid;grid-template-columns:132px 1fr 62px;gap:9px;align-items:center;margin:3px 0}
.hrow .l{font-size:.78rem;color:#222}
.hrow .t{height:13px;background:#e8e2d6;border-radius:2px}
.hrow .f{height:100%;background:#c0552d;border-radius:2px}
.hrow .v{font-size:.78rem;text-align:right;color:#222;font-style:normal}

/* ---------- 2. Ark editorial ---------- */
.ark{background:#000;color:#fff;padding:30px 26px}
.ark .kick{font-size:.7rem;letter-spacing:.3em;color:#ff3b1f;font-weight:800}
.ark h3{font-family:Georgia,serif;font-size:2.3rem;line-height:1.02;margin:.5rem 0 .3rem;font-weight:400;
letter-spacing:-.02em}
.ark .q{color:#8d8d8d;font-size:.86rem;margin-bottom:20px;text-transform:uppercase;letter-spacing:.1em}
.arow{display:grid;grid-template-columns:150px 1fr 70px;gap:8px;align-items:center;margin:5px 0}
.arow .l{font-size:.8rem;color:#fff}
.arow .t{height:9px;background:#262626}
.arow .f{height:100%;background:#fff}
.arow.hi .f{background:#ff3b1f}
.arow .v{font-size:.82rem;text-align:right;font-weight:700;font-variant-numeric:tabular-nums}

/* ---------- 3. FT / Economist data journalism ---------- */
.ft{background:#fff8f0;padding:26px;font-family:Georgia,'Times New Roman',serif}
.ft h3{font-size:1.35rem;margin:0 0 2px;color:#0d0d0d;font-weight:400;line-height:1.2}
.ft .q{font-size:.8rem;color:#666;font-style:italic;margin-bottom:18px;
padding-bottom:10px;border-bottom:1px solid #d9d2c7}
.ftrow{display:grid;grid-template-columns:140px 1fr 58px;gap:8px;align-items:baseline;margin:4px 0}
.ftrow .l{font-size:.79rem;color:#333}
.ftrow .t{height:1px;position:relative;top:-5px}
.ftrow .f{height:11px;background:#a3238e}
.ftrow .v{font-size:.79rem;text-align:right;font-variant-numeric:tabular-nums}

/* ---------- 4. Bloomberg terminal ---------- */
.bb{background:#0a0a0a;padding:22px;font-family:'Consolas','SF Mono',monospace;color:#e8e8e8}
.bb .bar{background:#1c1c1c;padding:6px 10px;margin:-22px -22px 16px;display:flex;gap:16px;
font-size:.72rem;color:#7a7a7a;border-bottom:1px solid #262626}
.bb .bar b{color:#ffb000}
.bb h3{font-size:.9rem;margin:0 0 2px;color:#ffb000;font-weight:600}
.bb .q{font-size:.72rem;color:#7a7a7a;margin-bottom:14px}
.bbrow{display:grid;grid-template-columns:150px 1fr 62px 54px;gap:7px;align-items:center;font-size:.75rem;margin:2px 0}
.bbrow .l{color:#c8c8c8}
.bbrow .t{height:11px;background:#1c1c1c}
.bbrow .f{height:100%;background:#00a86b}
.bbrow.lo .f{background:#d1341a}
.bbrow .v{text-align:right;color:#fff;font-variant-numeric:tabular-nums}
.bbrow .s{text-align:right;color:#7a7a7a}

/* ---------- 5. Annual-report financial ---------- */
.ar{background:#fbfaf7;padding:30px;font-family:Georgia,serif}
.ar h3{font-size:1.3rem;margin:0;color:#1c2f4a;font-weight:400}
.ar .q{font-size:.8rem;color:#8a7f6a;margin:.25rem 0 6px;letter-spacing:.04em}
.ar .rule{height:3px;background:linear-gradient(90deg,#b8963f 0 34%,#1c2f4a 34% 100%);margin-bottom:20px}
.arow2{display:grid;grid-template-columns:150px 1fr 62px;gap:10px;align-items:center;margin:7px 0}
.arow2 .l{font-size:.83rem;color:#1c2f4a}
.arow2 .t{height:16px;background:#eee9df}
.arow2 .f{height:100%;background:#1c2f4a}
.arow2.g .f{background:#b8963f}
.arow2 .v{font-size:.83rem;text-align:right;font-variant-numeric:tabular-nums}

/* ---------- 6. Modern SaaS / soft ---------- */
.saas{background:#fbfbff;padding:26px;font-family:-apple-system,'Segoe UI',system-ui,sans-serif}
.saas h3{font-size:1.05rem;margin:0 0 3px;color:#1a1a2e;font-weight:650}
.saas .q{font-size:.8rem;color:#7c7c8a;margin-bottom:16px}
.srow{display:grid;grid-template-columns:140px 1fr 60px;gap:10px;align-items:center;margin:6px 0}
.srow .l{font-size:.8rem;color:#4a4a5a}
.srow .t{height:18px;background:#eef0f7;border-radius:9px;overflow:hidden}
.srow .f{height:100%;background:linear-gradient(90deg,#7c5cff,#a78bfa);border-radius:9px}
.srow .v{font-size:.8rem;text-align:right;color:#1a1a2e;font-weight:600}

/* ---------- 7. PIE / donut: composition ---------- */
.pie{background:#fff;padding:26px}
.pie h3{font-size:1.05rem;margin:0 0 3px;color:#0f1e33}
.pie .q{font-size:.81rem;color:#6b7280;margin-bottom:16px}
.pieflex{display:flex;gap:30px;align-items:center;flex-wrap:wrap}
.plegend{font-size:.82rem;line-height:1.85}
.plegend .sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:7px}
.plegend b{font-variant-numeric:tabular-nums}

/* ---------- 8. Heatmap / treemap ---------- */
.heat{background:#fdfcfa;padding:24px}
.heat h3{font-size:1.03rem;margin:0 0 3px;color:#111}
.heat .q{font-size:.8rem;color:#6d685f;margin-bottom:14px}
.hgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:5px}
.cell{padding:11px 9px;border-radius:5px;color:#fff;font-size:.74rem;line-height:1.35}
.cell b{display:block;font-size:1.02rem;font-variant-numeric:tabular-nums}

/* ---------- 9. Slope / dot editorial ---------- */
.slope{background:#fff;padding:26px;font-family:Georgia,serif}
.slope h3{font-size:1.2rem;margin:0 0 3px;color:#111;font-weight:400}
.slope .q{font-size:.8rem;color:#666;font-style:italic;margin-bottom:14px}
.srow2{display:grid;grid-template-columns:150px 1fr 56px;gap:9px;align-items:center;margin:6px 0}
.srow2 .l{font-size:.8rem}
.srow2 .track{height:2px;background:#e6e2d8;position:relative}
.srow2 .dot{position:absolute;top:-5px;width:12px;height:12px;border-radius:50%;background:#111}
.srow2 .v{font-size:.8rem;text-align:right;font-variant-numeric:tabular-nums}

.foot{margin-top:26px;padding:16px 18px;background:#fff;border-radius:10px;
font-size:.78rem;color:#6d685f;line-height:1.6}
</style></head><body>''')

h.append(f'''<div class="pghead">
<h1>One number, nine visual identities</h1>
<p>The Graph Lab varied the <b>chart form</b> but ran one house style through every card &mdash;
navy, terracotta, Georgia. This board does the opposite: it takes a single KPI and renders it in nine
genuinely different visual languages, so the <b>look</b> can be chosen rather than inherited. Includes
the composition forms the catalogue was missing.</p>
<div class="meta">KPI: spend per truck per year, CY2025 &middot; 17 markets with a fleet denominator &middot;
network average &euro;{NET:.2f} &middot; source gps_spu_by_distributor.csv &middot;
illustrative intent, real figures &middot; snapshot 16 September 2026</div>
</div><div class="wrap">''')

# ---- 1 house
h.append('''<div class="slab"><div class="slabhead"><span class="n">01</span>
<h2>ISZE house &mdash; what we use today</h2>
<div class="why">Navy / terracotta / Georgia. The current identity. Shown first so the rest read as alternatives to it, not as decoration.</div>
</div><div class="slabbody"><div class="house">
<h3>What does a vehicle in each market spend on parts?</h3>
<div class="q">Spend per truck per year, CY2025, ranked</div>''')
mx = D[-1][1]
for n, v in reversed(D):
    hi = ' style="font-weight:700"' if v > 300 else ''
    h.append(f'<div class="hrow"><div class="l"{hi}>{html.escape(n)}</div>'
             f'<div class="t"><div class="f" style="width:{v/mx*100:.1f}%"></div></div>'
             f'<div class="v">&euro;{v:.0f}</div></div>')
h.append('</div><div class="note">Reads as a table with bars attached. Calm, but every chart on every page looks like this &mdash; which is the complaint.</div></div></div></div>')

# ---- 2 Ark
h.append('''<div class="slab"><div class="slabhead"><span class="n">02</span>
<h2>Ark editorial &mdash; high contrast, oversized, single vivid accent</h2>
<div class="why">What Ark Invest Big Ideas actually does: black ground, huge serif headline, white bars, one hot accent for the outlier. Editorial magazine, not dashboard.</div>
</div><div class="slabbody"><div class="ark">
<div class="kick">SPEND PER TRUCK</div>
<h3>Three markets spend<br>twice the network average</h3>
<div class="q">Parts spend per vehicle in service &middot; CY2025</div>''')
mx = D[-1][1]
for n, v in reversed(D):
    cls = 'arow hi' if v > 300 else 'arow'
    h.append(f'<div class="{cls}"><div class="l">{html.escape(n)}</div>'
             f'<div class="t"><div class="f" style="width:{v/mx*100:.1f}%"></div></div>'
             f'<div class="v">&euro;{v:.0f}</div></div>')
h.append('</div><div class="note">The headline makes the claim; the bars evidence it. Highest contrast of the nine, and the only one that works as a printed page in a board pack.</div></div></div></div>')

# ---- 3 FT
FT = [('#a3238e', 'a3238e')]
h.append('''<div class="slab"><div class="slabhead"><span class="n">03</span>
<h2>Data journalism &mdash; restrained, serif, single hue</h2>
<div class="why">FT / Economist register: serif headline, thin rules, one colour, no chart junk. Built for reading a long argument, not glancing at a screen.</div>
</div><div class="slabbody"><div class="ft">
<h3>The gap between the best and worst market is 4.4 times</h3>
<div class="q">Spend per truck per year, CY2025, 17 markets with a vehicle denominator</div>''')
mx = D[-1][1]
for n, v in reversed(D):
    h.append(f'<div class="ftrow"><div class="l">{html.escape(n)}</div>'
             f'<div class="t"><div class="f" style="width:{v/mx*100:.2f}%"></div></div>'
             f'<div class="v">&euro;{v:.0f}</div></div>')
h.append('</div><div class="note">Least decorative of the nine. Slower to scan, but a reader who trusts prose will trust this more than a dark chart.</div></div></div></div>')

# ---- 4 Bloomberg
h.append('''<div class="slab"><div class="slabhead"><span class="n">04</span>
<h2>Terminal &mdash; dark, dense, monospaced, status-coloured</h2>
<div class="why">Bloomberg register: maximum data per pixel, monospace figures, amber labels, colour carrying status. For daily operational use, not for a deck.</div>
</div><div class="slabbody"><div class="bb">
<div class="bar"><span><b>ISZE</b> GPS.SPU</span><span>CY2025</span><span>17 MKTS</span><span>AVG <b>188.16</b></span></div>
<h3>SPEND PER UNIT &mdash; RANKED DESC</h3>
<div class="q">EURO PER VEHICLE IN SERVICE / CALENDAR 2025</div>''')
mx = D[-1][1]
for n, v in reversed(D):
    cls = 'bbrow lo' if v < NET else 'bbrow'
    sign = '+' if v > NET else ''
    h.append(f'<div class="{cls}"><div class="l">{html.escape(n)}</div>'
             f'<div class="t"><div class="f" style="width:{v/mx*100:.1f}%"></div></div>'
             f'<div class="v">{v:,.2f}</div>'
             f'<div class="s">{sign}{(v-NET)/NET*100:.0f}%</div></div>')
h.append('</div><div class="note">Shows deviation from the network average in the last column. The densest option, and the one an analyst would actually keep open all day.</div></div></div></div>')

# ---- 5 annual report
h.append('''<div class="slab"><div class="slabhead"><span class="n">05</span>
<h2>Annual report &mdash; formal, navy and gold, conservative</h2>
<div class="why">The register a CFO and an audit committee expect. Slightly heavier type, a gold-to-navy rule, generous spacing. Reads as an official document.</div>
</div><div class="slabbody"><div class="ar">
<h3>Parts spend per vehicle in service</h3>
<div class="q">Calendar year 2025 &middot; seventeen markets</div>
<div class="rule"></div>''')
mx = D[-1][1]
for n, v in reversed(D):
    cls = 'arow2 g' if v > 300 else 'arow2'
    h.append(f'<div class="{cls}"><div class="l">{html.escape(n)}</div>'
             f'<div class="t"><div class="f" style="width:{v/mx*100:.1f}%"></div></div>'
             f'<div class="v">&euro;{v:.0f}</div></div>')
h.append('</div><div class="note">For the IML and management pack. Least likely to be challenged on style, most likely to be called &#8220;proper&#8221;.</div></div></div></div>')

# ---- 6 SaaS
h.append('''<div class="slab"><div class="slabhead"><span class="n">06</span>
<h2>Product analytics &mdash; soft, rounded, modern</h2>
<div class="why">The SaaS register: pill bars, soft gradients, generous radii, sans throughout. Familiar to anyone under forty and to distributors using modern tools.</div>
</div><div class="slabbody"><div class="saas">
<h3>Spend per truck</h3>
<div class="q">CY2025 &middot; 17 markets</div>''')
mx = D[-1][1]
for n, v in reversed(D):
    h.append(f'<div class="srow"><div class="l">{html.escape(n)}</div>'
             f'<div class="t"><div class="f" style="width:{v/mx*100:.1f}%"></div></div>'
             f'<div class="v">&euro;{v:.0f}</div></div>')
h.append('</div><div class="note">Pleasant and light, but the softest of the nine &mdash; it can make a serious gap look like a friendly progress bar.</div></div></div></div>')

# ---- 7 PIE
# composition: where the network-wide billed euro sits, a genuine share question
SEG = [('Belgium', 2.14, '#1c2f4a'), ('Germany', 2.58, '#2b4a78'), ('Portugal', 1.71, '#3f6ea8'),
       ('Ireland', 1.23, '#5b8cc4'), ('Nordics (SE/NO/DK/FI/IS)', 4.52, '#89b0d8'),
       ('Israel (UMI + UTI)', 6.79, '#c0552d'), ('UK (IUK + ITUK)', 11.99, '#8a3a17'),
       ('Benelux + rest', 3.37, '#8b8578')]
TOT = sum(s[1] for s in SEG)
h.append(f'''<div class="slab"><div class="slabhead"><span class="n">07</span>
<h2>Composition &mdash; pie, donut and share</h2>
<div class="why">The form the catalogue was missing entirely. Answers &#8220;what share of the total?&#8221;, which is one of the most common KPI questions and cannot be answered by a ranking bar.</div>
</div><div class="slabbody"><div class="pie">
<h3>How concentrated is the network's parts revenue?</h3>
<div class="q">Share of parts billed by market group, CY2025, 18 coded distributors</div>
<div class="pieflex">''')

# donut via SVG stroke-dasharray
import math
R, C = 92, 108
circ = 2 * math.pi * R
off = 0.0
h.append(f'<svg width="216" height="216" viewBox="0 0 216 216" role="img" aria-label="Donut chart of revenue share by market group">')
h.append(f'<circle cx="{C}" cy="{C}" r="{R}" fill="none" stroke="#f0ece4" stroke-width="34"/>')
for nm, val, col in SEG:
    frac = val / TOT
    dash = frac * circ
    h.append(f'<circle cx="{C}" cy="{C}" r="{R}" fill="none" stroke="{col}" stroke-width="34" '
             f'stroke-dasharray="{dash:.2f} {circ-dash:.2f}" '
             f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {C} {C})"/>')
    off += dash
h.append(f'<text x="{C}" y="{C-4}" text-anchor="middle" font-family="Georgia,serif" '
         f'font-size="26" fill="#1c2f4a">&euro;33.3M</text>')
h.append(f'<text x="{C}" y="{C+14}" text-anchor="middle" font-family="system-ui" '
         f'font-size="10" fill="#8a847a">PARTS BILLED CY2025</text></svg>')

h.append('<div class="plegend">')
for nm, val, col in SEG:
    h.append(f'<div><span class="sw" style="background:{col}"></span>{html.escape(nm)} '
             f'<b>&euro;{val:.2f}M &middot; {val/TOT*100:.0f}%</b></div>')
h.append('</div></div>')
h.append('''<div class="note">A pie is weak for ranking but strong for proportion &mdash; two groups carry 56% of the money. Use it for share, never for comparison between similar slices.</div>
</div></div></div>''')

# ---- 8 heatmap
h.append('''<div class="slab"><div class="slabhead"><span class="n">08</span>
<h2>Heat tiles &mdash; colour as the measure, no axes at all</h2>
<div class="why">For a wall of markets where the pattern matters more than the precise value. Reads instantly at distance; useless for exact figures, so the number is printed inside every tile.</div>
</div><div class="slabbody"><div class="heat">
<h3>Which markets are hot and which are cold?</h3>
<div class="q">Spend per truck per year, CY2025 &middot; colour intensity is the measure</div>
<div class="hgrid">''')
mx = D[-1][1]
for n, v in D:
    t = v / mx
    r = int(28 + t * 165); g = int(47 + t * 38); b = int(74 + t * 11)
    h.append(f'<div class="cell" style="background:rgb({r},{g},{b})">{html.escape(n)}'
             f'<b>&euro;{v:.0f}</b></div>')
h.append('</div><div class="note">Nine of these fit where three bar charts would. The trade: a reader cannot tell &euro;197 from &euro;210 by colour, only by reading.</div></div></div></div>')

# ---- 9 dot/slope
h.append(f'''<div class="slab"><div class="slabhead"><span class="n">09</span>
<h2>Dot plot with a reference line &mdash; the analyst's choice</h2>
<div class="why">One dot per market against a fixed scale, with the network average drawn as a line. Shows both level and distance from the average without a second chart.</div>
</div><div class="slabbody"><div class="slope">
<h3>How far is each market from the network average?</h3>
<div class="q">Spend per truck per year, CY2025 &middot; the rule marks &euro;{NET:.0f}</div>''')
mx = D[-1][1]
avgpct = NET / mx * 100
for n, v in reversed(D):
    h.append(f'<div class="srow2"><div class="l">{html.escape(n)}</div>'
             f'<div class="track"><div class="dot" style="left:calc({v/mx*100:.1f}% - 6px)"></div>'
             f'<div style="position:absolute;left:{avgpct:.1f}%;top:-6px;width:2px;height:14px;'
             f'background:#c0552d"></div></div>'
             f'<div class="v">&euro;{v:.0f}</div></div>')
h.append(f'''</div><div class="note">The most information per unit of ink of the nine. The orange rule is the network average at &euro;{NET:.0f}; every dot is a market, and the distance from the rule is the story. This is the form I would put on the KPI dashboard.</div></div></div></div>''')

h.append('''<div class="foot">
<b>What this board is.</b> A style comparison, not a finished page and not wired to live data. Each slab renders the
same KPI in a different visual language so the identity can be chosen deliberately. All figures are real
(gps_spu_by_distributor.csv, CY2025) but the layout is illustrative.<br><br>
<b>What is deliberately absent.</b> No 2026&ndash;2030 fleet forecast &mdash; those columns are overstated and await
correction. No chart library and no CDN; everything is inline SVG and CSS so nothing can go blank offline.<br><br>
<b>Next step, for Jerome's call.</b> Pick the identity &mdash; or two, one for internal analyst use and one for the
IML and management pack &mdash; and that choice gets applied to the KPI dashboard, which is where the ten growth
KPIs and five Competitive-parts measures land on real data per distributor.
</div></div></body></html>''')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write('\n'.join(h))
print('WROTE', OUT, round(os.path.getsize(OUT) / 1024, 1), 'KB')
