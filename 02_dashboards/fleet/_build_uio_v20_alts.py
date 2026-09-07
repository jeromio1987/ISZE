# -*- coding: utf-8 -*-
"""Three structurally different visual treatments of UIO V20 vs the live file."""
from __future__ import annotations

from pathlib import Path

FLEET = Path(__file__).resolve().parent
ROOT = FLEET.parent
CHART_JS = ROOT / "_ui" / "chart.umd.min.js"

NAVY, TERR, PAPER, INK, MUTED, GOOD, BAD, LINE = (
    "#15233c",
    "#c0552d",
    "#f7f4ee",
    "#222",
    "#6b6256",
    "#2e7d54",
    "#b23b3b",
    "#d9d3c8",
)


def chart_js() -> str:
    raw = CHART_JS.read_text(encoding="utf-8")
    return raw.replace("//# sourceMappingURL=chart.umd.min.js.map", "")


def css() -> str:
    return f"""
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:{INK};background:#e8e4dc;font-size:15px;line-height:1.4}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;margin:0;color:{NAVY}}}
.banner{{background:#c9a227;color:{NAVY};font-weight:700;font-size:12px;letter-spacing:.05em;text-transform:uppercase;padding:9px 28px}}
.wrap{{max-width:1180px;margin:0 auto}}
.page{{background:{PAPER};padding:22px 28px 32px}}
.foot{{padding:12px 28px 24px;font-size:11px;color:{MUTED};background:{PAPER};border-top:1px solid {LINE}}}
.alts{{display:flex;gap:8px;flex-wrap:wrap;padding:10px 28px;background:{NAVY}}}
.alts a{{color:{PAPER};text-decoration:none;font-size:12px;padding:6px 10px;border:1px solid #3d5278}}
.alts a.on{{background:{TERR};border-color:{TERR};color:#fff}}
.kpi-tip{{cursor:help;position:relative}}
.kpi-tip:hover::after{{content:attr(data-tip);position:absolute;z-index:30;left:0;top:100%;margin-top:6px;width:min(320px,70vw);background:{NAVY};color:{PAPER};font-size:12px;font-weight:400;text-transform:none;letter-spacing:0;padding:10px 12px;border-left:3px solid {TERR}}}
"""


def nav(active: str) -> str:
    items = [
        ("UIO_V20_THREE_ALTS.html", "chooser", "Chooser"),
        ("UIO_V20_ALT1_TWO_WORLDS.html", "alt1", "1 · Two worlds"),
        ("UIO_V20_ALT2_SURVIVAL.html", "alt2", "2 · Survival curve"),
        ("UIO_V20_ALT3_WHO_MOVES.html", "alt3", "3 · Who moves"),
    ]
    links = []
    for href, key, lab in items:
        on = ' class="on"' if key == active else ""
        links.append(f'<a href="{href}"{on}>{lab}</a>')
    return '<div class="alts">' + "".join(links) + "</div>"


def foot() -> str:
    return """<footer class="foot">Proposed method — not in the live car park file. Sources: car park method note July 2026 (UK pickup locked 30 July); IMIT November 2025 pickup study; Irish registrations vs shipments 2020–2024; Israel Ministry of Transport 30 June 2026; Portugal registration years to 31 Dec 2025; Portugal wear-item age check CY2025 (0–2 year cut is illustrative).</footer>"""


def shell(title: str, active: str, body: str, extra_css: str = "", extra_js: str = "") -> str:
    js = chart_js()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{css()}{extra_css}</style>
</head>
<body>
<div class="wrap">
<div class="banner">Proposed method — not yet in the live car park file</div>
{nav(active)}
{body}
{foot()}
</div>
<script>{js}</script>
<script>{extra_js}</script>
</body>
</html>"""


def polyline(xy, color, width=3):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    return f'<polyline fill="none" stroke="{color}" stroke-width="{width}" points="{d}"/>'


def survival_svg() -> str:
    ages = list(range(0, 34))
    live = [(a, 100 * (0.97**a)) for a in ages]
    # Spec: 5y 96%, 10y 55%, 15y none
    real_knots = {0: 100, 5: 96, 10: 55, 15: 0}
    real = []
    for a in ages:
        if a <= 15:
            keys = sorted(real_knots)
            for i in range(len(keys) - 1):
                a0, a1 = keys[i], keys[i + 1]
                if a0 <= a <= a1:
                    t = (a - a0) / (a1 - a0) if a1 != a0 else 0
                    y = real_knots[a0] + t * (real_knots[a1] - real_knots[a0])
                    real.append((a, y))
                    break
        else:
            real.append((a, 0))
    w, h, pad = 700, 300, 44

    def Xx(x):
        return pad + x / 33 * (w - 2 * pad)

    def Yy(y):
        return h - pad - y / 100 * (h - 2 * pad)

    live_xy = [(Xx(a), Yy(v)) for a, v in live]
    real_xy = [(Xx(a), Yy(v)) for a, v in real]
    grid = ""
    for y in (0, 25, 50, 75, 100):
        grid += f'<line x1="{pad}" x2="{w-pad}" y1="{Yy(y):.1f}" y2="{Yy(y):.1f}" stroke="{LINE}" stroke-width="1"/>'
        grid += f'<text x="{pad-8}" y="{Yy(y)+4:.1f}" text-anchor="end" font-size="11" fill="{MUTED}">{y}%</text>'
    for x in (0, 5, 10, 15, 20, 25, 33):
        grid += f'<text x="{Xx(x):.1f}" y="{h-18}" text-anchor="middle" font-size="11" fill="{MUTED}">{x}</text>'
    # markers at year 15
    m15l = (Xx(15), Yy(100 * (0.97**15)))
    m15r = (Xx(15), Yy(0))
    return f'''<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Share of a truck cohort still on the road by age. Live file 63 percent at year 15. Survival method zero.">
  {grid}
  {polyline(live_xy, BAD, 3)}
  {polyline(real_xy, TERR, 3.5)}
  <circle cx="{m15l[0]:.1f}" cy="{m15l[1]:.1f}" r="5" fill="{BAD}"/>
  <circle cx="{m15r[0]:.1f}" cy="{m15r[1]:.1f}" r="5" fill="{TERR}"/>
  <text x="{m15l[0]+8:.1f}" y="{m15l[1]-8:.1f}" font-size="12" fill="{BAD}">Live file · 63% still counted</text>
  <text x="{m15r[0]+8:.1f}" y="{m15r[1]-10:.1f}" font-size="12" fill="{TERR}">V20 · gone</text>
  <text x="{w/2}" y="{h-4}" text-anchor="middle" font-size="12" fill="{MUTED}">Vehicle age (years)</text>
</svg>'''


def overstate_mountain() -> str:
    years = [2026, 2027, 2028, 2029, 2030]
    pcts = [7.8, 15.6, 23.2, 30.6, 37.7]
    w, h, pad = 640, 240, 40

    def Xx(i):
        return pad + i / 4 * (w - 2 * pad)

    def Yy(p):
        return h - pad - p / 40 * (h - 2 * pad)

    pts = [(Xx(i), Yy(p)) for i, p in enumerate(pcts)]
    area = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    base = f"{pts[-1][0]:.1f},{h-pad:.1f} {pts[0][0]:.1f},{h-pad:.1f}"
    bars = ""
    for i, p in enumerate(pcts):
        bars += f'<text x="{Xx(i):.1f}" y="{Yy(p)-8:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="{NAVY}">{p}%</text>'
        bars += f'<text x="{Xx(i):.1f}" y="{h-18}" text-anchor="middle" font-size="11" fill="{MUTED}">{years[i]}</text>'
    return f'''<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Grand Total overstatement 7.8 percent in 2026 rising to 37.7 percent in 2030">
  <polygon fill="#c0552d22" stroke="none" points="{area} {base}"/>
  {polyline(pts, TERR, 3)}
  {bars}
</svg>'''


def diverging_svg() -> str:
    rows = [
        ("Ireland pickups 2030", -26.0),
        ("Ireland light trucks 2030", -19.0),
        ("Grand Total 2030", -37.7),
        ("UK pickup 2026", -8.8),
        ("Portugal parts wallet", -21.9),
        ("Israel trucks 2026", 30.3),
    ]
    w, h = 760, 340
    mid = 430
    maxabs = 40
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Where V20 moves the number versus the live file">']
    out.append(f'<line x1="{mid}" x2="{mid}" y1="28" y2="{h-20}" stroke="{NAVY}" stroke-width="1.5"/>')
    out.append(f'<text x="{mid-10}" y="20" text-anchor="end" font-size="12" fill="{TERR}">V20 smaller</text>')
    out.append(f'<text x="{mid+10}" y="20" text-anchor="start" font-size="12" fill="{GOOD}">V20 larger</text>')
    for i, (lab, val) in enumerate(rows):
        y = 40 + i * 48
        mag = abs(val) / maxabs * 250
        out.append(f'<text x="8" y="{y+16}" font-size="13" fill="{NAVY}">{lab}</text>')
        if val < 0:
            x = mid - mag
            out.append(f'<rect class="bar-row" x="{x:.1f}" y="{y}" width="{mag:.1f}" height="22" fill="{TERR}"/>')
            out.append(f'<text x="{x-8:.1f}" y="{y+16}" text-anchor="end" font-size="13" font-weight="700" fill="{NAVY}">{val:.0f}%</text>')
        else:
            out.append(f'<rect class="bar-row" x="{mid}" y="{y}" width="{mag:.1f}" height="22" fill="{GOOD}"/>')
            out.append(f'<text x="{mid+mag+8:.1f}" y="{y+16}" font-size="13" font-weight="700" fill="{NAVY}">+{val:.0f}%</text>')
    out.append("</svg>")
    return "\n".join(out)


def ireland_svg() -> str:
    # grouped bars
    cats = [("Light trucks", 1645, 1382), ("Pickups", 3174, 2527)]
    w, h, pad = 520, 220, 48
    ymax = 3600

    def Y(v):
        return h - 36 - v / ymax * (h - 70)

    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Ireland 2030 live file versus survival">']
    for i, (lab, a, b) in enumerate(cats):
        x0 = 80 + i * 220
        parts.append(f'<rect class="bar-row" x="{x0}" y="{Y(a):.1f}" width="44" height="{h-36-Y(a):.1f}" fill="{BAD}"/>')
        parts.append(f'<rect class="bar-row" x="{x0+52}" y="{Y(b):.1f}" width="44" height="{h-36-Y(b):.1f}" fill="{GOOD}"/>')
        parts.append(f'<text x="{x0+22}" y="{Y(a)-6:.1f}" text-anchor="middle" font-size="12" fill="{BAD}">{a:,}</text>')
        parts.append(f'<text x="{x0+74}" y="{Y(b)-6:.1f}" text-anchor="middle" font-size="12" fill="{GOOD}">{b:,}</text>')
        parts.append(f'<text x="{x0+48}" y="{h-12}" text-anchor="middle" font-size="12" fill="{MUTED}">{lab}</text>')
    parts.append(f'<text x="20" y="18" font-size="11" fill="{BAD}">■ Live file</text>')
    parts.append(f'<text x="120" y="18" font-size="11" fill="{GOOD}">■ Survival</text>')
    parts.append("</svg>")
    return "".join(parts)


def age_stack_svg() -> str:
    bands = [("0–2 yr", 31.9, TERR), ("3–5", 30.7, "#2a78d6"), ("6–8", 26.7, "#85b7eb"), ("9+", 10.7, "#888780")]
    w, h = 520, 70
    x = 0
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Portugal wear base by age">']
    for lab, pct, col in bands:
        ww = pct / 100 * w
        parts.append(f'<rect class="bar-row" x="{x:.1f}" y="0" width="{ww:.1f}" height="36" fill="{col}"/>')
        if pct > 12:
            parts.append(f'<text x="{x+ww/2:.1f}" y="24" text-anchor="middle" font-size="12" fill="#fff" font-weight="700">{pct}%</text>')
        x += ww
    x = 0
    for lab, pct, col in bands:
        ww = pct / 100 * w
        parts.append(f'<text x="{x+4:.1f}" y="58" font-size="11" fill="{MUTED}">{lab}</text>')
        x += ww
    parts.append("</svg>")
    return "".join(parts)


def uk_pair_svg() -> str:
    return f'''<svg viewBox="0 0 400 120" width="100%" role="img" aria-label="UK pickup 2026 49280 versus 44926">
  <rect x="10" y="20" width="170" height="80" fill="#f8ecea" stroke="{LINE}"/>
  <text x="95" y="42" text-anchor="middle" font-size="11" fill="{BAD}">DO NOT USE</text>
  <text x="95" y="78" text-anchor="middle" font-size="26" font-family="Georgia,serif" fill="{BAD}">49,280</text>
  <rect x="220" y="20" width="170" height="80" fill="#eaf6f1" stroke="{LINE}"/>
  <text x="305" y="42" text-anchor="middle" font-size="11" fill="{GOOD}">USE THIS</text>
  <text x="305" y="78" text-anchor="middle" font-size="26" font-family="Georgia,serif" fill="{GOOD}">44,926</text>
</svg>'''


ALT1_CSS = f"""
.split{{display:grid;grid-template-columns:1fr 1fr;min-height:420px}}
.world{{padding:28px 26px}}
.world.live{{background:{NAVY};color:{PAPER}}}
.world.v20{{background:{PAPER};color:{NAVY};border-left:3px solid {TERR}}}
.world h1{{font-size:28px;color:inherit}}
.world.live h1{{color:{PAPER}}}
.world .tag{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;opacity:.8}}
.giant{{font-family:Georgia,serif;font-size:56px;line-height:1;margin:8px 0 6px}}
.world.live .giant{{color:#f3c4b4}}
.world.v20 .giant{{color:{TERR}}}
.arrow{{font-size:42px;line-height:1;margin:12px 0}}
.world p{{font-size:14px;max-width:28em}}
.bottom{{display:grid;grid-template-columns:1.2fr .8fr;gap:16px;padding:8px 0 0}}
@media(max-width:800px){{.split,.bottom{{grid-template-columns:1fr}}}}
"""

ALT1_BODY = f"""
<div class="split">
  <section class="world live">
    <div class="tag">Live file</div>
    <h1>Trucks live 33 years</h1>
    <div class="giant kpi-tip" data-tip="3% scrap a year implies 1 ÷ 0.03 = 33 years. History in the same file uses about 10% a year.">3%</div>
    <p>scrap each year · park keeps growing</p>
    <div class="arrow">↗ +22.8%</div>
    <p>Pickup park 2025–2030, while new registrations fall 29%.</p>
    <p style="margin-top:18px;font-size:13px;opacity:.85">UK pickup 2026 climbs to 49,280. Ireland 2030 light trucks 1,645. Grand Total 2030 is 37.7% above a survival forecast.</p>
  </section>
  <section class="world v20">
    <div class="tag">V20</div>
    <h1>Same life as history</h1>
    <div class="giant kpi-tip" data-tip="Truck survival about 10.2% a year = 9.8 year life. Pickups 12.3% = 8.1 years.">9.8y</div>
    <p>trucks · pickups 8.1 years</p>
    <div class="arrow" style="color:{TERR}">↘ must fall</div>
    <p>Pickup park cannot grow when registrations cannot hold 125,000 units.</p>
    <p style="margin-top:18px;font-size:13px;color:{MUTED}">UK pickup 2026 = 44,926 (−6%). Ireland 2030 light trucks 1,382. Israel rebuilt to 14,019.</p>
  </section>
</div>
<div class="page">
  <div class="bottom">
    <div>
      <h2 style="font-size:18px;margin-bottom:8px">The gap compounds</h2>
      {overstate_mountain()}
    </div>
    <div>
      <h2 style="font-size:18px;margin-bottom:8px">UK pickup 2026</h2>
      {uk_pair_svg()}
      <p style="font-size:13px;color:{MUTED}">47,783 × (1 − 12.3%) + 3,020 = 44,926. A second route lands 3 units away.</p>
    </div>
  </div>
</div>
"""

ALT2_CSS = f"""
.hero{{padding:8px 0 12px}}
.hero h1{{font-size:30px;margin:0 0 6px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}}
.call{{border-left:3px solid {TERR};background:#fff;padding:12px 16px;margin:12px 0}}
@media(max-width:800px){{.two{{grid-template-columns:1fr}}}}
"""

ALT2_BODY = f"""
<div class="page">
  <div class="hero">
    <h1>The change is a curve, not a slogan</h1>
    <p style="color:{MUTED};max-width:46em">At year 15 the live file still counts 63% of a truck cohort. The survival method used for 1990–2025 is already at zero. That is why 2026–2030 inflates.</p>
    {survival_svg()}
    <div class="call">At <strong>year 15</strong> the two methods disagree completely. Nothing in the parc changed on 1 January 2026 — only the arithmetic.</div>
  </div>
  <div class="two">
    <div>
      <h2 style="font-size:18px;margin-bottom:8px">Ireland 2030 once the curve is used</h2>
      {ireland_svg()}
      <p style="font-size:13px;color:{MUTED}">216 new trucks a year settles near 2,100. Under 3% scrap it settles near 7,200.</p>
    </div>
    <div>
      <h2 style="font-size:18px;margin-bottom:8px">Portugal — age of the parts base</h2>
      {age_stack_svg()}
      <p style="font-size:13px;color:{MUTED};margin-top:8px">Terracotta = 0–2 years (31.9% of clutch/brake expected). Those vehicles almost never need the part. Pickup park: 62% aged 10 or under.</p>
      <div style="position:relative;height:180px"><canvas id="chartWear" role="img" aria-label="Wear capture live versus excluding 0-2 years">Clutch disc 2.8 to 4.2 percent. Brake rotor 14.6 to 21.6.</canvas></div>
    </div>
  </div>
</div>
"""

ALT2_JS = """
(function(){
  if(typeof Chart==='undefined') return;
  var el=document.getElementById('chartWear');
  if(!el) return;
  new Chart(el,{type:'bar',data:{
    labels:['Clutch disc','Clutch kit','Brake rotor','Brake pad'],
    datasets:[
      {label:'Live model',data:[2.8,7.6,14.6,0.9],backgroundColor:'#888780',barThickness:16},
      {label:'Excl. 0–2 years',data:[4.2,11.4,21.6,1.4],backgroundColor:'#c0552d',barThickness:16}
    ]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10}}},
      scales:{x:{min:0,max:24,ticks:{stepSize:8,callback:v=>v+'%'}},y:{grid:{display:false}}}}});
})();
"""

ALT3_CSS = f"""
.lede{{max-width:48em;color:{MUTED};margin:0 0 16px}}
.grid2{{display:grid;grid-template-columns:1.15fr .85fr;gap:18px}}
@media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
"""

ALT3_BODY = f"""
<div class="page">
  <h1 style="font-size:30px;margin-bottom:6px">Who moves when age is used</h1>
  <p class="lede">V20 is not “everything smaller.” Israel is too low today. Portugal’s parts wallet is too heavy because a 3.5 t truck is charged as 7.5 t. The live file is too high where scrap was 3%.</p>
  {diverging_svg()}
  <div class="grid2" style="margin-top:20px">
    <div>
      <h2 style="font-size:18px;margin-bottom:8px">Age mix that the wallet ignores today</h2>
      {age_stack_svg()}
      <p style="font-size:13px;color:{MUTED};margin-top:10px">Portugal wear base. Israel still has 1,680 trucks aged 16–27 (12% of that fleet) — they should not get a young-truck parts wallet.</p>
      <div style="position:relative;height:200px;margin-top:8px"><canvas id="chartIE" role="img" aria-label="Ireland 2030 grouped bars">Ireland trucks 1645 vs 1382, pickups 3174 vs 2527.</canvas></div>
    </div>
    <div>
      <h2 style="font-size:18px;margin-bottom:8px">UK pickup 2026</h2>
      {uk_pair_svg()}
      {overstate_mountain()}
    </div>
  </div>
</div>
"""

ALT3_JS = """
(function(){
  if(typeof Chart==='undefined') return;
  var ie=document.getElementById('chartIE');
  if(!ie) return;
  new Chart(ie,{type:'bar',data:{
    labels:['Light trucks','Pickups'],
    datasets:[
      {label:'Live file',data:[1645,3174],backgroundColor:'#b23b3b',barThickness:22},
      {label:'Survival',data:[1382,2527],backgroundColor:'#2e7d54',barThickness:22}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10}}},
      scales:{y:{min:0,max:3600,ticks:{stepSize:1200}},x:{grid:{display:false}}}}});
})();
"""

CHOOSER_CSS = f"""
.page h1{{font-size:32px;margin-bottom:8px}}
.cards{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:18px}}
.card{{display:block;background:#fff;border:1px solid {LINE};padding:16px;text-decoration:none;color:{INK};min-height:280px}}
.card:hover{{border-color:{TERR}}}
.card h2{{font-size:18px;margin:8px 0}}
.card p{{font-size:13px;color:{MUTED};margin:0}}
.thumb{{height:120px;margin-bottom:8px;overflow:hidden}}
@media(max-width:900px){{.cards{{grid-template-columns:1fr}}}}
"""

CHOOSER_BODY = f"""
<div class="page">
  <h1>Three ways to see the same change</h1>
  <p style="color:{MUTED};max-width:40em">The first page was mostly cards. These three are pictures. Same numbers. Pick the one you would put in front of someone.</p>
  <div class="cards">
    <a class="card" href="UIO_V20_ALT1_TWO_WORLDS.html">
      <div class="thumb"><svg viewBox="0 0 200 80" width="100%"><rect width="98" height="80" fill="{NAVY}"/><rect x="102" width="98" height="80" fill="{PAPER}" stroke="{TERR}"/><text x="49" y="46" text-anchor="middle" fill="#f3c4b4" font-size="22">↗</text><text x="151" y="46" text-anchor="middle" fill="{TERR}" font-size="22">↘</text></svg></div>
      <h2>1 · Two worlds</h2>
      <p>Live file on the left, V20 on the right. You see 33-year life vs 9.8 years before you read a sentence.</p>
    </a>
    <a class="card" href="UIO_V20_ALT2_SURVIVAL.html">
      <div class="thumb">{survival_svg()}</div>
      <h2>2 · Survival curve</h2>
      <p>The mechanism. At year 15 the live file still counts 63% of a cohort. V20 counts none.</p>
    </a>
    <a class="card" href="UIO_V20_ALT3_WHO_MOVES.html">
      <div class="thumb">{diverging_svg()}</div>
      <h2>3 · Who moves</h2>
      <p>Not everything shrinks. Israel goes up. Portugal’s wallet comes down. Ireland and the Grand Total come down.</p>
    </a>
  </div>
</div>
"""


def main() -> None:
    files = {
        "UIO_V20_ALT1_TWO_WORLDS.html": shell(
            "V20 · two worlds", "alt1", ALT1_BODY, ALT1_CSS
        ),
        "UIO_V20_ALT2_SURVIVAL.html": shell(
            "V20 · survival curve", "alt2", ALT2_BODY, ALT2_CSS, ALT2_JS
        ),
        "UIO_V20_ALT3_WHO_MOVES.html": shell(
            "V20 · who moves", "alt3", ALT3_BODY, ALT3_CSS, ALT3_JS
        ),
        "UIO_V20_THREE_ALTS.html": shell(
            "V20 · three visuals", "chooser", CHOOSER_BODY, CHOOSER_CSS
        ),
    }
    for name, html in files.items():
        path = FLEET / name
        path.write_text(html, encoding="utf-8")
        print(f"Wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
