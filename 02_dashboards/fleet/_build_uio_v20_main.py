# -*- coding: utf-8 -*-
"""Canonical UIO V20 infographic: original brief, visual-first, shareable."""
from __future__ import annotations

import importlib.util
from pathlib import Path

FLEET = Path(__file__).resolve().parent
ALTS = FLEET / "_build_uio_v20_alts.py"
OUT = FLEET / "UIO_V20_WHAT_GETS_BETTER.html"

spec = importlib.util.spec_from_file_location("uio_v20_alts", ALTS)
alts = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(alts)

NAVY, TERR, PAPER, MUTED, GOOD, BAD = (
    alts.NAVY,
    alts.TERR,
    alts.PAPER,
    alts.MUTED,
    alts.GOOD,
    alts.BAD,
)

EXTRA_CSS = f"""
.cover{{background:linear-gradient(155deg,{NAVY} 0%,#203759 60%,#2b4a78 100%);color:{PAPER};padding:28px 32px 22px}}
.cover h1{{color:{PAPER};font-size:32px;line-height:1.12;font-weight:400}}
.cover .rule{{width:64px;height:3px;background:{TERR};margin:12px 0 12px}}
.cover p{{max-width:46em;margin:0;opacity:.92}}
.split{{display:grid;grid-template-columns:1fr 1fr}}
.world{{padding:22px 24px}}
.world.live{{background:{NAVY};color:{PAPER}}}
.world.v20{{background:{PAPER};color:{NAVY};border-left:3px solid {TERR}}}
.world .tag{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.8;margin-bottom:6px}}
.world h2{{font-size:22px;color:inherit;margin:0 0 8px}}
.world.live h2{{color:{PAPER}}}
.giant{{font-family:Georgia,serif;font-size:48px;line-height:1;margin:4px 0}}
.world.live .giant{{color:#f3c4b4}}
.world.v20 .giant{{color:{TERR}}}
.page h2.sec{{font-size:22px;margin:18px 0 8px;padding-bottom:6px;border-bottom:2px solid {NAVY}}}
.page h2.sec .no{{color:{TERR}}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:12px 0 20px}}
.wins{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0 22px}}
.win{{background:#fff;border:1px solid {alts.LINE};padding:12px 12px 14px}}
.win .n{{font-family:Georgia,serif;font-size:20px;color:{TERR}}}
.win h3{{font-size:13px;margin:4px 0}}
.win .fig{{font-family:Georgia,serif;font-size:22px;color:{NAVY};margin:4px 0}}
.win p{{margin:0;font-size:12px;color:{MUTED}}}
.call{{border-left:3px solid {TERR};background:#fff;padding:12px 16px;margin:8px 0 18px}}
@media(max-width:900px){{.split,.two,.wins{{grid-template-columns:1fr 1fr}}}}
@media(max-width:620px){{.split,.two,.wins{{grid-template-columns:1fr}}}}
"""

BODY = f"""
<header class="cover">
  <h1>What V20 changes in the car park</h1>
  <div class="rule"></div>
  <p>One survival method for every year. The forecast stops treating a truck as if it lasts 33 years. Vehicle age then feeds parts expected — a young park and an old park are not the same wallet.</p>
</header>
<div class="split">
  <section class="world live">
    <div class="tag">Live file</div>
    <h2>Trucks live 33 years</h2>
    <div class="giant kpi-tip" data-tip="3% scrap a year implies 1 ÷ 0.03 = 33 years.">3%</div>
    <p>scrap each year · pickup park still +22.8% to 2030</p>
  </section>
  <section class="world v20">
    <div class="tag">V20</div>
    <h2>Same life as history</h2>
    <div class="giant kpi-tip" data-tip="Truck survival about 10.2% a year = 9.8 year life. Pickups 12.3% = 8.1 years.">9.8y</div>
    <p>trucks · pickups 8.1 years · park turns down when registrations fall</p>
  </section>
</div>
<div class="page">
  <h2 class="sec"><span class="no">01</span> The change is a curve</h2>
  <p style="color:{MUTED};max-width:48em">At year 15 the live file still counts 63% of a truck cohort. The survival method already used for 1990–2025 is at zero. That is why 2026–2030 inflates.</p>
  {alts.survival_svg()}
  <div class="call">Nothing in the parc changed on 1 January 2026 — only the arithmetic.</div>

  <h2 class="sec"><span class="no">02</span> Who moves</h2>
  <p style="color:{MUTED};max-width:48em">Not everything gets smaller. Israel is too low today. Portugal’s parts wallet is too heavy because a 3.5 t truck is charged as 7.5 t.</p>
  {alts.diverging_svg()}
  <div class="two">
    <div>
      <h3 style="margin:12px 0 8px">The gap compounds</h3>
      {alts.overstate_mountain()}
    </div>
    <div>
      <h3 style="margin:12px 0 8px">UK pickup 2026</h3>
      {alts.uk_pair_svg()}
      <p style="font-size:13px;color:{MUTED}">47,783 × (1 − 12.3%) + 3,020 = 44,926. A second route lands 3 units away.</p>
    </div>
  </div>

  <h2 class="sec"><span class="no">03</span> Eight things that get better</h2>
  <div class="wins">
    <article class="win"><div class="n">1</div><h3>One engine 1990–2030</h3><div class="fig">9.8y</div><p>Kill the 3% / 33-year join. Pickups 8.1 years.</p></article>
    <article class="win"><div class="n">2</div><h3>Forecast size</h3><div class="fig">37.7%</div><p>Grand Total too high by 2030. Starts at 7.8% in 2026.</p></article>
    <article class="win"><div class="n">3</div><h3>Pickup direction</h3><div class="fig">Must fall</div><p>Regs −29%. Live file still +22.8%. Sustainable park ~88k vs ~125k on the road.</p></article>
    <article class="win"><div class="n">4</div><h3>UK pickup locked</h3><div class="fig">44,926</div><p>−6.0% vs 47,783. Do not quote 49,280. UK trucks already correct — leave those.</p></article>
    <article class="win"><div class="n">5</div><h3>Plan vs the road</h3><div class="fig">1.3%</div><p>Ireland ship vs register over five years. Smooth years. Medium-duty plan rows out of Grand Total (0 in 3,238 shipments).</p></article>
    <article class="win"><div class="n">6</div><h3>Israel on government data</h3><div class="fig">14,019</div><p>File ~25% low. Add missing weight classes and an age floor. Do not ×1.25.</p></article>
    <article class="win"><div class="n">7</div><h3>Confidence labelled</h3><div class="fig">4 mkts</div><p>Belgium, Cyprus, Malta, Greece: no registration history. Germany 2019–2024 reconstructed from one 2025 point.</p></article>
    <article class="win"><div class="n">8</div><h3>Wallet by truck size</h3><div class="fig">−22%</div><p>Portugal order of size if N35 split from N75. Decode weight from chassis series, not the number in the model code.</p></article>
  </div>
  <div class="call"><strong>Shipment VIN file:</strong> a check, not a replacement car park. It confirms scrap near 10% (Ireland 13.3%, Portugal 7.4%) and that medium-duty forecast rows are not in the shipment record. Current fleet dashboard should not be forwarded until the workbook is rebuilt.</div>

  <h2 class="sec" id="age"><span class="no">04</span> Why age of the car park matters</h2>
  <p style="color:{MUTED};max-width:48em">Survival by registration year sets how many vehicles are on the road. Age mix then sets how much parts demand that park should generate. Do not treat a 20-year truck like a 3-year one.</p>
  <div class="two">
    <div>
      <h3 style="margin:0 0 8px">Ireland 2030 — 3% vs survival</h3>
      {alts.ireland_svg()}
      <p style="font-size:13px;color:{MUTED}">216 new trucks a year settles near 2,100. Under 3% scrap it settles near 7,200.</p>
    </div>
    <div>
      <h3 style="margin:0 0 8px">Portugal pickups — share aged 10 or under</h3>
      <svg viewBox="0 0 200 140" width="100%" role="img" aria-label="Portugal pickup park 62 percent aged 10 or under">
        <circle cx="70" cy="70" r="48" fill="none" stroke="#d9d3c8" stroke-width="18"/>
        <circle cx="70" cy="70" r="48" fill="none" stroke="{TERR}" stroke-width="18" stroke-dasharray="186.9 114.7" transform="rotate(-90 70 70)"/>
        <text x="70" y="66" text-anchor="middle" font-family="Georgia,serif" font-size="22" fill="{NAVY}">62%</text>
        <text x="70" y="84" text-anchor="middle" font-size="10" fill="{MUTED}">age ≤ 10</text>
        <text x="132" y="66" font-size="12" fill="{TERR}">62% ≤ 10 years</text>
        <text x="132" y="84" font-size="12" fill="{MUTED}">38% older</text>
      </svg>
      <p style="font-size:13px;color:{MUTED}">Israel: 1,680 trucks aged 16–27 still registered (12% of that fleet) should not get a young-truck parts wallet.</p>
    </div>
  </div>
  <h3 style="margin:8px 0">Portugal wear items — age of the base</h3>
  {alts.age_stack_svg()}
  <p style="font-size:13px;color:{MUTED};margin:8px 0 10px">Terracotta = 0–2 years (31.9%). Those vehicles almost never need clutch or brake. Illustrative cut — age resizes capture, it does not close the leakage.</p>
  <div style="position:relative;height:200px"><canvas id="chartWear" role="img" aria-label="Portugal wear capture live versus excluding 0-2 years">Clutch disc 2.8 to 4.2 percent. Brake rotor 14.6 to 21.6.</canvas></div>
</div>
"""

JS = """
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
      scales:{x:{min:0,max:24,ticks:{stepSize:8,callback:function(v){return v+'%';}}},y:{grid:{display:false}}}}});
})();
"""


def main() -> None:
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Car park V20 — what gets better</title>
<style>{alts.css()}{EXTRA_CSS}</style>
</head>
<body>
<div class="wrap">
<div class="banner">Proposed method — not yet in the live car park file</div>
{BODY}
{alts.foot()}
</div>
<script>{alts.chart_js()}</script>
<script>{JS}</script>
</body>
</html>"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
