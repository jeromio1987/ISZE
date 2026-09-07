# -*- coding: utf-8 -*-
"""Build shareable UIO V20 infographic HTML (inline Chart.js, no CDN)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 02_dashboards
FLEET = Path(__file__).resolve().parent
CHART_JS = ROOT / "_ui" / "chart.umd.min.js"
OUT = FLEET / "UIO_V20_WHAT_GETS_BETTER.html"


def chart_js_inline() -> str:
    raw = CHART_JS.read_text(encoding="utf-8")
    raw = raw.replace("//# sourceMappingURL=chart.umd.min.js.map", "")
    return raw


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Car park V20 — what gets better</title>
<style>
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#e8e4dc;font-size:15px;line-height:1.45}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}
.wrap{max-width:1120px;margin:0 auto;padding:0 0 48px}
.cover{background:linear-gradient(155deg,#15233c 0%,#203759 58%,#2b4a78 100%);color:#f7f4ee;padding:36px 40px 28px}
.cover h1{color:#f7f4ee;font-size:34px;line-height:1.12;font-weight:400}
.cover .rule{width:72px;height:3px;background:#c0552d;margin:16px 0 14px}
.cover .lede{font-size:16px;max-width:46em;color:#e8edf4}
.banner{background:#c9a227;color:#15233c;font-weight:700;font-size:13px;letter-spacing:.04em;text-transform:uppercase;padding:10px 40px}
.page{background:#f7f4ee;padding:28px 40px 8px}
.kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 28px}
.kpi{background:#fff;border:1px solid #d9d3c8;border-top:3px solid #c0552d;padding:14px 14px 12px;position:relative}
.kpi .lab{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#6b6256;margin-bottom:6px}
.kpi .val{font-family:Georgia,serif;font-size:28px;color:#15233c;line-height:1.1}
.kpi .sub{font-size:12px;color:#6b6256;margin-top:6px}
.kpi-tip{cursor:help}
.kpi-tip:hover::after{content:attr(data-tip);position:absolute;left:8px;right:8px;top:100%;z-index:20;margin-top:6px;background:#15233c;color:#f7f4ee;font-size:12px;font-weight:400;text-transform:none;letter-spacing:0;line-height:1.4;padding:10px 12px;border-left:3px solid #c0552d;box-shadow:0 8px 24px rgba(21,35,60,.25)}
h2.sec{font-size:22px;margin:8px 0 6px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}
h2.sec .no{color:#c0552d}
.sec-lead{color:#6b6256;margin:0 0 16px;max-width:52em}
.grid-2{display:grid;grid-template-columns:1.15fr .85fr;gap:20px;margin:0 0 28px}
.card{background:#fff;border:1px solid #d9d3c8;padding:16px 18px 18px}
.card h3{font-size:15px;margin:0 0 12px;color:#15233c}
.wins{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0 0 32px}
.win{background:#fff;border:1px solid #d9d3c8;padding:14px 16px 16px;display:flex;gap:12px;align-items:flex-start}
.win .n{flex:0 0 28px;font-family:Georgia,serif;font-size:22px;color:#c0552d;line-height:1}
.win h3{font-size:14px;margin:0 0 4px}
.win p{margin:0;font-size:13px;color:#3a3540}
.bar-row{display:grid;grid-template-columns:72px 1fr 64px;gap:10px;align-items:center;margin:8px 0}
.bar-row .yr{font-size:13px;color:#6b6256}
.bar-row .track{height:22px;background:#e8e4dc;border-radius:2px;overflow:hidden}
.bar-row .fill{height:100%;background:#c0552d;min-width:4px}
.bar-row .pct{font-size:13px;font-weight:700;color:#15233c;text-align:right}
.compare{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.bad,.good{padding:16px;text-align:center;border:1px solid #d9d3c8}
.bad{background:#f8ecea}
.good{background:#eaf6f1}
.bad .tag,.good .tag{font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.bad .tag{color:#b23b3b}
.good .tag{color:#2e7d54}
.num{font-family:Georgia,serif;font-size:32px;line-height:1.1}
.bad .num{color:#b23b3b}
.good .num{color:#2e7d54}
.age-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin:0 0 24px}
.chart-box{position:relative;height:220px}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 24px;font-size:13px}
.flow span{background:#15233c;color:#f7f4ee;padding:8px 12px}
.flow .arr{background:transparent;color:#c0552d;font-weight:700;padding:0 2px}
.note{font-size:12px;color:#6b6256;margin:8px 0 0}
.callout{border-left:3px solid #c0552d;background:#fff;padding:12px 16px;margin:0 0 24px}
.foot{padding:16px 40px 28px;font-size:11px;color:#6b6256;border-top:1px solid #d9d3c8;background:#f7f4ee}
.ie-pair{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.ie-pair .cell{padding:10px;background:#f7f4ee;border:1px solid #d9d3c8;text-align:center}
.ie-pair .cell strong{display:block;font-family:Georgia,serif;font-size:22px;color:#15233c}
.wear-row{display:grid;grid-template-columns:120px 1fr 1fr;gap:8px;align-items:center;font-size:13px;margin:6px 0}
.wear-row .h{font-size:11px;text-transform:uppercase;color:#6b6256}
@media(max-width:900px){
  .kpi-strip,.wins,.age-grid,.grid-2{grid-template-columns:1fr}
  .cover,.page,.banner,.foot{padding-left:20px;padding-right:20px}
}
</style>
</head>
<body>
<div class="wrap">
<div class="banner">Proposed method — not yet in the live car park file</div>
<header class="cover">
  <h1>What V20 changes in the car park</h1>
  <div class="rule"></div>
  <p class="lede">One survival method for every year. The forecast stops treating a truck as if it lasts 33 years. Vehicle age then feeds parts expected — a young park and an old park are not the same wallet.</p>
</header>

<div class="page">
  <div class="kpi-strip">
    <div class="kpi kpi-tip" data-tip="Grand Total forecast overstatement if the 3% scrap rule is kept. Derived by applying the historical survival curve instead of removing 3% of the fleet each year. 2030 is 37.7% too high.">
      <div class="lab">2030 too high by</div>
      <div class="val">37.7%</div>
      <div class="sub">starts at 7.8% in 2026</div>
    </div>
    <div class="kpi kpi-tip" data-tip="United Kingdom pickup calendar 2026. 47,783 × (1 − 12.3% pickup scrap) + 3,020 new registrations = 44,926. A second route (IMIT year-on-year on the same 2025 level) lands 3 units away. Do not use 49,280.">
      <div class="lab">UK pickup 2026</div>
      <div class="val">44,926</div>
      <div class="sub">−6.0% vs 2025 · not 49,280</div>
    </div>
    <div class="kpi kpi-tip" data-tip="IMIT November 2025 pickup registrations fall 29% into 2026. At 10,845 new units a year and 8.1 years average life the park can only hold about 88,000. About 125,000 are already on the road. The park has to come down. Today’s file still grows it 22.8% to 2030.">
      <div class="lab">Pickup park</div>
      <div class="val">Must fall</div>
      <div class="sub">regs −29% · file still +22.8%</div>
    </div>
    <div class="kpi kpi-tip" data-tip="Israel government registered trucks at 30 June 2026: 14,019. The live file is about a quarter lower in every year (roughly 3,300–3,700 missing). Rebuild on the government count; do not multiply the old rows by 1.25.">
      <div class="lab">Israel 2026</div>
      <div class="val">14,019</div>
      <div class="sub">government count · file ~25% low</div>
    </div>
  </div>

  <h2 class="sec"><span class="no">01</span> Forecast size</h2>
  <p class="sec-lead">From 2026 the live file scraps 3% a year. That implies a 33-year life. History in the same file uses ~10% a year for trucks (~9.8 years) and ~12.3% for pickups (8.1 years). Nothing in the real world changed on 1 January 2026 — only the arithmetic.</p>
  <div class="grid-2">
    <div class="card">
      <h3>How much the Grand Total is overstated</h3>
      <div class="bar-row"><span class="yr">2026</span><div class="track"><div class="fill" style="width:21%"></div></div><span class="pct">7.8%</span></div>
      <div class="bar-row"><span class="yr">2027</span><div class="track"><div class="fill" style="width:41%"></div></div><span class="pct">15.6%</span></div>
      <div class="bar-row"><span class="yr">2028</span><div class="track"><div class="fill" style="width:62%"></div></div><span class="pct">23.2%</span></div>
      <div class="bar-row"><span class="yr">2029</span><div class="track"><div class="fill" style="width:81%"></div></div><span class="pct">30.6%</span></div>
      <div class="bar-row"><span class="yr">2030</span><div class="track"><div class="fill" style="width:100%"></div></div><span class="pct">37.7%</span></div>
      <p class="note">Bars scaled to 37.7%. Same gap shows up if you fit the published dashboard series to “keep 97% + add new units”.</p>
    </div>
    <div class="card">
      <h3>UK pickup 2026 — two numbers</h3>
      <div class="compare">
        <div class="bad"><div class="tag">Do not use</div><div class="num">49,280</div><div class="note">+3.1% vs 2025 · 3% scrap</div></div>
        <div class="good"><div class="tag">Use this</div><div class="num">44,926</div><div class="note">−6.0% vs 47,783</div></div>
      </div>
      <p class="note" style="margin-top:14px">Keep the 2025 level (47,783). Apply pickup scrap 12.3% and add IMIT 2026 registrations ≈ 3,020. A second check using IMIT’s own UK fleet year-on-year lands on 44,923 — three units apart.</p>
      <h3 style="margin-top:18px">Pickup direction (network)</h3>
      <p class="note">IMIT registrations: 16,977 (2024) → 10,845 (2026), <strong>−29%</strong>. Sustainable park at 8.1 years ≈ 88,000. Already on the road ≈ 125,000. Today’s file still grows the pickup park <strong>+22.8%</strong> to 2030. Both cannot be true.</p>
    </div>
  </div>

  <h2 class="sec"><span class="no">02</span> Eight things that get better</h2>
  <div class="wins">
    <article class="win"><div class="n">1</div><div><h3>One engine, 1990–2030</h3><p>Same survival curve after 2025 as before. Trucks ~10% a year (~9.8 years). Pickups 12.3% (8.1 years). Delete the 3% / 33-year join.</p></div></article>
    <article class="win"><div class="n">2</div><div><h3>Forecast stops inflating</h3><p>Grand Total too high 7.8% in 2026, 37.7% by 2030. Ireland 2030 light trucks 1,645 vs 1,382; pickups 3,174 vs 2,527.</p></div></article>
    <article class="win"><div class="n">3</div><div><h3>Pickup park turns down</h3><p>Falling registrations cannot grow a fleet. Once real scrap is applied, pickup rows turn down on their own. That flows into spend per vehicle and capture rates.</p></div></article>
    <article class="win"><div class="n">4</div><div><h3>UK pickup locked at 44,926</h3><p>Calendar 2026 for GPS / extended target. Two independent routes agree. Do not quote 49,280. UK trucks (separate rows) already use a proper survival model — leave those.</p></div></article>
    <article class="win"><div class="n">5</div><div><h3>Plan vs vehicles on the road</h3><p>Ireland shipments vs government registrations 2020–2024 match within 1.3% over five years. Use the sales plan for the level; smooth single years (lag). Medium-duty rows with no history stay out of the Grand Total until a first real registration — zero medium units in 3,238 shipment records.</p></div></article>
    <article class="win"><div class="n">6</div><div><h3>Israel rebuilt on government data</h3><p>14,019 trucks at 30 June 2026. Add missing weight classes (7.6–10 t and 12.1–16 t) and an age floor for trucks still registered after 15 years. Do not scale old rows by 1.25.</p></div></article>
    <article class="win"><div class="n">7</div><div><h3>Confidence is labelled</h3><p>Belgium, Cyprus, Malta and Greece have no registration history. A shipment check that looks like 0.3–3% scrap is not real for trucks. Germany 2019–2024 was reconstructed from one 2025 point.</p></div></article>
    <article class="win"><div class="n">8</div><div><h3>Parts wallet by truck size</h3><p>A 3.5 t N35 is today charged like a 7.5 t N75. Portugal is the market that moves: wallet about −22% if split (order of size, not a restated official GPS %). Decode weight from chassis series, not from the number in the model code.</p></div></article>
  </div>
  <div class="callout"><strong>Shipment VIN file:</strong> a check, not a replacement car park. It cannot rebuild 15–20 years of history. It does confirm scrap near 10% (Ireland 13.3%, Portugal 7.4%), the Ireland five-year match, and that medium-duty forecast rows are not in the shipment record. Method notes in the workbook will match the numbers. The current fleet dashboard should not be forwarded until the workbook is rebuilt.</div>

  <h2 class="sec" id="age"><span class="no">03</span> Why age of the car park matters</h2>
  <p class="sec-lead">Two jobs. Survival by registration year sets <em>how many</em> vehicles are on the road. Age mix then sets <em>how much parts demand</em> that park should generate. Do not treat a 20-year truck like a 3-year one.</p>
  <div class="flow">
    <span>Registration year</span><span class="arr">→</span>
    <span>Survival curve</span><span class="arr">→</span>
    <span>Vehicles on the road</span><span class="arr">→</span>
    <span>Headcount</span>
    <span class="arr">+</span>
    <span>Age mix → parts expected</span>
  </div>

  <div class="age-grid">
    <div class="card">
      <h3>Ireland 2030 — 3% vs survival</h3>
      <div class="ie-pair">
        <div class="cell">Light trucks<strong>1,645 → 1,382</strong>19% too high</div>
        <div class="cell">Pickups<strong>3,174 → 2,527</strong>26% too high</div>
      </div>
      <p class="note">If Ireland registers 216 trucks a year forever, the park settles near 216 × 9.8 ≈ 2,100. Under 3% scrap it settles near 7,200. 2030 is only the start of the error.</p>
      <div class="chart-box"><canvas id="chartIE" role="img" aria-label="Ireland 2030 live file versus survival method for trucks and pickups">Ireland 2030: trucks 1645 vs 1382; pickups 3174 vs 2527.</canvas></div>
    </div>
    <div class="card">
      <h3>Portugal pickups — share aged 10 or under</h3>
      <svg viewBox="0 0 200 140" width="100%" height="160" role="img" aria-label="Portugal pickup park: 62 percent aged 10 years or under">
        <circle cx="70" cy="70" r="48" fill="none" stroke="#d9d3c8" stroke-width="18"/>
        <circle cx="70" cy="70" r="48" fill="none" stroke="#c0552d" stroke-width="18" stroke-dasharray="186.9 114.7" stroke-dashoffset="0" transform="rotate(-90 70 70)"/>
        <text x="70" y="66" text-anchor="middle" font-family="Georgia,serif" font-size="22" fill="#15233c">62%</text>
        <text x="70" y="84" text-anchor="middle" font-size="10" fill="#6b6256">age ≤ 10</text>
        <text x="132" y="48" font-size="12" fill="#15233c">On the road</text>
        <text x="132" y="66" font-size="11" fill="#c0552d">● 62% ≤ 10 years</text>
        <text x="132" y="84" font-size="11" fill="#6b6256">○ 38% older</text>
      </svg>
      <p class="note">National registration years at 31 Dec 2025. Older vehicles still registered should not get a full young-vehicle parts wallet. Israel: 1,680 trucks first registered 1999–2010 are still on the road (12% of that fleet, aged 16–27).</p>
    </div>
    <div class="card">
      <h3>Portugal wear items — age of the base</h3>
      <div class="bar-row"><span class="yr">0–2 yr</span><div class="track"><div class="fill" style="width:100%"></div></div><span class="pct">31.9%</span></div>
      <div class="bar-row"><span class="yr">3–5 yr</span><div class="track"><div class="fill" style="width:96%;background:#2a78d6"></div></div><span class="pct">30.7%</span></div>
      <div class="bar-row"><span class="yr">6–8 yr</span><div class="track"><div class="fill" style="width:84%;background:#2a78d6"></div></div><span class="pct">26.7%</span></div>
      <div class="bar-row"><span class="yr">9+ yr</span><div class="track"><div class="fill" style="width:34%;background:#888780"></div></div><span class="pct">10.7%</span></div>
      <p class="note">Nearly a third of the current clutch and brake expected base is 0–2 years old — vehicles that almost never need either. Illustrative cut, not a field replacement table.</p>
    </div>
  </div>

  <div class="card" style="margin-bottom:28px">
    <h3>Wear capture — same sales, fairer base (Portugal, illustrative)</h3>
    <p class="note" style="margin-bottom:12px">Taking 0–2 year vehicles out of the clutch/brake base lifts reported capture about 40–50% relative. Clutch and brake capture is still very low; age resizes the gap, it does not close it. Do not quote the right-hand column as an official network number.</p>
    <div class="wear-row"><span class="h"></span><span class="h">Live model</span><span class="h">Excluding 0–2 years</span></div>
    <div class="wear-row"><span>Clutch disc</span><span>2.8%</span><span>4.2%</span></div>
    <div class="wear-row"><span>Clutch kit</span><span>7.6%</span><span>11.4%</span></div>
    <div class="wear-row"><span>Brake rotor</span><span>14.6%</span><span>21.6%</span></div>
    <div class="wear-row"><span>Brake pad</span><span>0.9%</span><span>1.4%</span></div>
    <div class="chart-box" style="height:200px"><canvas id="chartWear" role="img" aria-label="Portugal wear capture live model versus excluding vehicles aged 0 to 2 years">Clutch disc 2.8 to 4.2 percent; brake rotor 14.6 to 21.6 percent.</canvas></div>
  </div>
</div>
<footer class="foot">
  Sources: car park method note (July 2026, UK pickup arithmetic locked 30 July 2026); IMIT November 2025 pickup study; Irish government registrations vs shipments 2020–2024; Israel Ministry of Transport registered fleet at 30 June 2026; Portugal national registration years to 31 December 2025; Portugal wear-item age check, calendar 2025 (0–2 year cut is illustrative). Live workbook remains the current version until this method is applied.
</footer>
</div>
<script>
__CHART_JS__
</script>
<script>
(function(){
  var ink='#52514e', grid='#e1e0d9';
  if(typeof Chart==='undefined') return;
  Chart.defaults.font.family='"Segoe UI",Helvetica,Arial,sans-serif';
  Chart.defaults.color=ink;
  var ie=document.getElementById('chartIE');
  if(ie){
    new Chart(ie,{type:'bar',
      data:{labels:['Light trucks','Pickups'],
        datasets:[
          {label:'Live file',data:[1645,3174],backgroundColor:'#b23b3b',barThickness:18},
          {label:'Survival method',data:[1382,2527],backgroundColor:'#2e7d54',barThickness:18}
        ]},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{position:'bottom',labels:{boxWidth:10}}},
        scales:{y:{min:0,max:3500,ticks:{stepSize:1000,color:ink},grid:{color:grid}},
                x:{grid:{display:false},ticks:{color:ink}}}}});
  }
  var w=document.getElementById('chartWear');
  if(w){
    new Chart(w,{type:'bar',
      data:{labels:['Clutch disc','Clutch kit','Brake rotor','Brake pad'],
        datasets:[
          {label:'Live model',data:[2.8,7.6,14.6,0.9],backgroundColor:'#888780',barThickness:16},
          {label:'Excl. 0–2 years',data:[4.2,11.4,21.6,1.4],backgroundColor:'#c0552d',barThickness:16}
        ]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
        plugins:{legend:{position:'bottom',labels:{boxWidth:10}}},
        scales:{x:{min:0,max:24,ticks:{stepSize:8,callback:function(v){return v+'%';},color:ink},grid:{color:grid}},
                y:{grid:{display:false},ticks:{color:ink}}}}});
  }
})();
</script>
</body>
</html>
"""


def main() -> None:
    js = chart_js_inline()
    html = HTML.replace("__CHART_JS__", js)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
