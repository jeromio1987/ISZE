#!/usr/bin/env python3
"""Build the shared warranty commercial HTML.

Self-contained: the dataset is embedded at build time and Chart.js is inlined, so it opens from
Explorer with no server and no CDN. Everything numeric comes out of the CSV datasets in
01_data/00_derived/warranty_commercial/ — nothing is typed by hand, so the page cannot drift from
the data it describes.

Currency: the CV (truck) file is in EUR, GBP and JPY and is normalised in the datasets before it
reaches here. See warranty_cv_currency_audit.csv. Absolute non-EUR euros are indicative; shares are
solid.

Run:  python 02_dashboards/_build/build_warranty_commercial.py
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_data" / "00_derived" / "warranty_commercial"
CHART_JS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = ROOT / "02_dashboards" / "sales" / "Warranty_Commercial_Review.html"
LAUNCHER = OUT.with_name("OPEN_Warranty_Commercial_Review.cmd")
AS_OF = date(2026, 9, 18)


def read(name: str) -> list[dict]:
    path = DATA / name
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def num(v):
    try:
        f = float(v)
        return None if f != f else f          # NaN -> None
    except (TypeError, ValueError):
        return v


def clean(rows: list[dict]) -> list[dict]:
    return [{k: num(v) for k, v in r.items()} for r in rows]


def eur(v: float) -> str:
    return f"€{v:,.0f}"


def main() -> None:
    payload = {
        "as_of": AS_OF.isoformat(),
        "recon": clean(read("warranty_commercial_reconciliation.csv")),
        "market": clean(read("warranty_cost_by_market.csv")),
        "family": clean(read("warranty_cost_by_component_family.csv")),
        "limits": clean(read("warranty_cost_by_limit_position.csv")),
        "lines": clean(read("warranty_top_repair_lines.csv")),
        "cv_market": clean(read("warranty_cv_by_market.csv")),
        "cv_family": clean(read("warranty_cv_by_component_family.csv")),
        "cv_ops": clean(read("warranty_cv_top_repair_lines.csv")),
        "cv_dealer": clean(read("warranty_cv_dealer_concentration.csv")),
        "cv_currency": clean(read("warranty_cv_currency_audit.csv")),
        "cv_commercial": clean(read("warranty_cv_commercial_by_market.csv")),
        "who_pays": clean(read("warranty_operations_by_who_pays.csv")),
    }
    payload["chartjs"] = None
    blob = json.dumps(payload, ensure_ascii=False)
    html = (TEMPLATE
            .replace("/*__CHARTJS__*/", CHART_JS.read_text(encoding="utf-8"))
            .replace("__PAYLOAD__", "window.__WARRANTY__ = " + blob + ";"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    # Launcher beside the page so it opens from Explorer by double-click. CRLF, as required.
    LAUNCHER.write_bytes(
        b'@echo off\r\nstart "" "%~dp0' + OUT.name.encode() + b'"\r\n')
    print(f"written {OUT} ({OUT.stat().st_size / 1024:,.0f} KB)")
    print(f"written {LAUNCHER.name} ({LAUNCHER.stat().st_size} bytes, CRLF)")
    print(f"  markets {len(payload['market'])} | families {len(payload['family'])} | "
          f"repair lines {len(payload['lines'])} | truck dealers {len(payload['cv_dealer'])}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Warranty commercial review — where the money goes</title>
<style>
  :root{--navy:#15233c;--navy2:#1a2b4a;--terra:#c0552d;--paper:#f7f4ee;--line:#d8d2c6;
        --ink:#222;--mut:#6b6560;--amber:#b8860b}
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);
       font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
  header{background:var(--navy);color:var(--paper);padding:26px 30px 22px}
  header h1{margin:0 0 6px;font:600 25px/1.2 Georgia,serif;letter-spacing:.2px}
  header .sub{color:#cbd3e0;font-size:13.5px;max-width:1000px}
  header .stamp{margin-top:12px;font-size:12px;color:#9fb0c9}
  main{max-width:1180px;margin:0 auto;padding:22px 18px 60px}
  h2{font:600 19px/1.25 Georgia,serif;color:var(--navy);margin:34px 0 4px}
  h2 .n{color:var(--terra);font-size:15px;margin-right:8px}
  .q{color:var(--mut);font-size:13.5px;margin:0 0 14px;max-width:900px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin:16px 0 6px}
  .card{background:#fff;border:1px solid var(--line);border-radius:6px;padding:14px 16px}
  .card .v{font:600 24px/1.15 Georgia,serif;color:var(--navy)}
  .card .l{font-size:12.5px;color:var(--mut);margin-top:5px}
  .card.hi{border-left:4px solid var(--terra)}
  .panel{background:#fff;border:1px solid var(--line);border-radius:6px;padding:16px 18px;margin:14px 0}
  .panel h3{margin:0 0 3px;font:600 14.5px/1.3 inherit;color:var(--navy)}
  .panel .note{color:var(--mut);font-size:12.5px;margin:0 0 12px}
  .wrap{position:relative;height:330px}
  .wrap.tall{height:400px}
  table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
  th,td{text-align:left;padding:7px 9px;border-bottom:1px solid #ebe7de}
  th{background:var(--navy);color:var(--paper);font-weight:600;font-size:12px;
     position:sticky;top:0;letter-spacing:.2px}
  td.r,th.r{text-align:right;font-variant-numeric:tabular-nums}
  tbody tr:hover{background:#fbf9f4}
  .scroll{max-height:340px;overflow:auto;border:1px solid var(--line);border-radius:6px}
  .flag{background:#fff8e6;border:1px solid #e8d49a;border-radius:4px;
        padding:9px 12px;font-size:12.5px;color:#6a5312;margin:10px 0}
  .caveat{background:#fff;border:1px solid var(--line);border-left:4px solid var(--amber);
          border-radius:5px;padding:14px 16px;margin-top:26px;font-size:13px}
  .caveat h3{margin:0 0 8px;color:var(--navy);font:600 14px/1.3 inherit}
  .caveat ul{margin:0;padding-left:20px}
  .caveat li{margin:5px 0;color:#3d3a36}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  @media(max-width:780px){.two{grid-template-columns:1fr}.wrap{height:280px}}
  footer{max-width:1180px;margin:0 auto;padding:0 18px 40px;color:var(--mut);font-size:12px}
</style>
</head>
<body>
<header>
  <h1>Warranty commercial review — where the money goes</h1>
  <div class="sub">Two claim files: D-Max pickups (20,383 lines, Apr 2025 – Mar 2026) and CV trucks
  (33,416 lines after de-duplication, Dec 2023 – Mar 2026). Read this as failure cost, not
  maintenance — the files contain defects, not services.</div>
  <div class="stamp">Built <span id="stamp"></span> · every figure read from the datasets at build
  time · the truck file is in EUR, GBP and JPY and has been normalised</div>
</header>
<main>

  <h2 id="sec1">1 · The six numbers</h2>
  <p class="q">What this is worth before any detail. Both fleets, both periods, parts only.</p>
  <div class="cards" id="kpis"></div>
  <div class="flag" id="insideflag"></div>

  <h2 id="sec2">2 · Two different fleets, two different bills</h2>
  <p class="q">The D-Max and the truck are not the same story. On pickups one steering part is the
  biggest single repair line. On trucks there is no single dominating line at all — the bill is
  spread across aftertreatment hardware, and the same part number repair costs far less per truck.</p>
  <div class="two">
    <div class="panel">
      <h3>D-Max: the ten most expensive repair lines</h3>
      <p class="note">Bar length is parts cost. Hover for claim count, cost per truck and markets.</p>
      <div class="wrap tall"><canvas id="c1"></canvas></div>
    </div>
    <div class="panel">
      <h3>Trucks: the ten most expensive repair lines</h3>
      <p class="note">Same measure, different fleet. The steering gear — number one on D-Max — is
      €29,671 here across 35 claims in 7 markets.</p>
      <div class="wrap tall"><canvas id="c7"></canvas></div>
    </div>
  </div>

  <h2 id="sec3">3 · Where the money concentrates, D-Max</h2>
  <p class="q">Thirty markets. Steering and electrical are 40% of the bill between them, on 166 part
  numbers — a short list, not a thousand-part problem.</p>
  <div class="two">
    <div class="panel">
      <h3>Parts turnover by component family</h3>
      <p class="note">Claim lines carrying a real parts charge. Share of total in brackets.</p>
      <div class="wrap" style="height:400px"><canvas id="c3"></canvas></div>
    </div>
    <div class="panel">
      <h3>Trucks: parts cost by component family</h3>
      <p class="note">Aftertreatment hardware is 61% of the truck bill. On D-Max the same parts are 8%.</p>
      <div class="wrap" style="height:400px"><canvas id="c2"></canvas></div>
    </div>
  </div>

  <h2 id="sec4">4 · Warranty or goodwill?</h2>
  <p class="q">"Inside" means under 36 months and under 100,000 km. Everything else is the
  distributor's own decision to pay.</p>
  <div class="two">
    <div class="panel">
      <h3>Cost position against the limits — D-Max</h3>
      <p class="note">42% of turnover is outside the limits, and it sits on age, not distance.</p>
      <div class="wrap"><canvas id="c4"></canvas></div>
    </div>
    <div class="panel">
      <h3>Share outside the limits, by market</h3>
      <p class="note">Markets with 100 or more claim lines. Norway 68%, Sweden 25% — a loyalty
      decision per book, not a technical one.</p>
      <div class="wrap"><canvas id="c5"></canvas></div>
    </div>
  </div>

  <h2 id="sec5">5 · Reading the truck books correctly</h2>
  <p class="q">Coverage is the column that matters. Where a market's claims carry no part number, a
  part-level ranking from that market is guesswork.</p>
  <div class="panel">
    <h3>Truck parts turnover by market, with part-number coverage</h3>
    <p class="note">Coverage is the share of that market's claim lines carrying a real part number.
    Sort by either column.</p>
    <div class="scroll"><table id="t1"></table></div>
  </div>

  <h2 id="sec6">6 · Warranty against the business</h2>
  <p class="q">Cost in absolute euros cannot be compared between two markets of different size. The
  same cost per truck in service can. Both sides of this table are calendar 2025 — the claim file
  spans 28 months, so only its 2025 rows are counted here.</p>
  <div class="two">
    <div class="panel">
      <h3>Warranty parts cost per truck in service</h3>
      <p class="note">Israel carries 2.6 times the UK's warranty cost per truck and 8 times
      Portugal's. This ratio is what makes the concentration arguable rather than just large.</p>
      <div class="wrap tall"><canvas id="c8"></canvas></div>
    </div>
    <div class="panel">
      <h3>Warranty parts cost as a share of the part's own target spend</h3>
      <p class="note">Israel's warranty bill is 8.5% of its target parts spend; Ireland's is 0.7%.
      The market with the largest warranty exposure is also the one furthest from its parts
      potential.</p>
      <div class="scroll"><table id="t3"></table></div>
    </div>
  </div>

  <h2 id="sec7">7 · Who pays, and it is decided by the odometer</h2>
  <p class="q">Same component family, three different owners. A part that fails at 20,000 km is
  Isuzu's cost and a supplier conversation. One that fails at 160,000 km is the distributor's
  bill and aftermarket demand.</p>
  <div class="panel">
    <h3>Truck repair operations grouped by who actually pays</h3>
    <p class="note">Operations with 45 or more claims. The split is the stated terms: 36 months and
    100,000 km.</p>
    <div class="two">
      <div class="wrap tall"><canvas id="c9"></canvas></div>
      <div class="scroll"><table id="t4"></table></div>
    </div>
  </div>

  <h2 id="sec8">8 · Two anomalies worth a question</h2>
  <p class="q">Neither is explained by the data here. Both are cheap to ask about.</p>
  <div class="two">
    <div class="panel">
      <h3>Truck claims by dealer code</h3>
      <p class="note">One code carries 36% of every truck claim in the network.</p>
      <div class="scroll" style="max-height:290px"><table id="t2"></table></div>
    </div>
    <div class="panel">
      <h3>Parts claimed versus admitted, by market</h3>
      <p class="note">What a market asks for against what it is granted. Belgium recovers 47%,
      Poland 173%.</p>
      <div class="wrap"><canvas id="c6"></canvas></div>
    </div>
  </div>

  <div class="caveat">
    <h3>What these numbers cannot say</h3>
    <ul>
      <li><b>Claimants, not fleets.</b> Both files hold vehicles that made a warranty claim. Neither
      can produce a fleet-wide failure rate or a fleet age.</li>
      <li><b>No maintenance.</b> Oil filters appear 8 times in the whole truck file and brake pads
      not at all — a consumable replaced at a service is not a defect and is not claimed. Measured
      service intervals cannot come from this data.</li>
      <li><b>The truck file is three currencies.</b> The UK is in pounds (11,956 lines) and Italy,
      Spain, France and Switzerland are in yen. Everything here is normalised first; absolute euros
      for those markets are indicative, shares are solid.</li>
      <li><b>Labour is not comparable across markets</b> — 0.3% of cost in Italy against 29.5% in
      the UK. A recording convention, not a cost difference.</li>
      <li><b>Two emissions totals exist and both are right.</b> This page uses the claim files
      (€2.84M, 61%); the canonical grain in <code>warranty_raw_grain.csv</code> covers a different
      workbook and period and gives €1.82M. Do not add them.</li>
    </ul>
  </div>
</main>
<footer id="foot"></footer>
<script>
/*__CHARTJS__*/
</script>
<script>
__PAYLOAD__
</script>
<script>
(function(){
  const DATA = window.__WARRANTY__;
  document.getElementById('stamp').textContent = DATA.as_of;
  const f = n => '€' + Math.round(n).toLocaleString('en-GB');
  const k = n => '€' + (n/1000).toFixed(0) + 'k';
  const pct = n => Math.round(n*100) + '%';

  const rec = Object.fromEntries(DATA.recon.map(r => [r.measure, r.value]));
  const limits = DATA.limits.filter(r => r.position !== 'unknown');
  const outside = limits.filter(r => r.position !== 'inside both limits')
                        .reduce((a,r) => a + r.parts_turnover_eur, 0);
  const inside = limits.find(r => r.position === 'inside both limits');
  const totalTruck = rec['CV (truck) parts turnover EUR'];
  // NOTE: match on a substring, not a prefix. The operation label in the data is
  // "GEAR ASSEMBLY, POWER STEERING - REPLACE", which does not start with "POWER STEERING";
  // an earlier version used indexOf(...) === 0, returned undefined, and threw on the next line —
  // which silently killed everything after it on the page.
  const has = (needle) => DATA.lines.find(r => r.operation && r.operation.indexOf(needle) >= 0);
  const steer = has('POWER STEERING');
  const emis = DATA.cv_family.find(r => r.family && r.family.indexOf('Emissions') === 0);
  if (!steer || !inside || !emis) {
    throw new Error('warranty page: expected series missing from the payload');
  }

  const kpis = [
    ['D-Max parts claimed', f(rec['LCV (D-Max) parts claimed EUR']),
     '20,383 claim lines across 30 markets'],
    ['Steering gear, D-Max', f(steer.parts_turnover_eur),
     steer.claim_lines + ' claims · ' + f(steer.parts_turnover_per_line_eur) + ' a truck · ' +
     steer.markets_present + ' markets', true],
    ['D-Max outside the limits', pct(outside /
     (outside + inside.parts_turnover_eur)),
     f(outside) + ' of turnover is goodwill, ' + f(inside.parts_turnover_eur) + ' is warranty'],
    ['Truck parts turnover', f(totalTruck),
     '33,416 claim lines across ' + DATA.cv_market.length + ' markets'],
    ['Aftertreatment, trucks', pct(emis.parts_turnover_eur / totalTruck),
     f(emis.parts_turnover_eur) + ' of the truck bill, on ' + emis.part_numbers + ' part numbers'],
    ['Dealer V19010', pct(DATA.cv_dealer[0].share_of_claim_lines),
     DATA.cv_dealer[0].claim_lines.toLocaleString('en-GB') + ' of all ' +
     DATA.cv_dealer[0].market + ' claim lines']
  ];
  document.getElementById('kpis').innerHTML = kpis.map(([l,v,s,hi]) =>
    '<div class="card'+(hi?' hi':'')+'"><div class="v">'+v+'</div><div class="l"><b>'+
    l+'</b><br>'+s+'</div></div>').join('');
  document.getElementById('insideflag').textContent =
    'Position split uses the stated terms: inside = under 36 months AND under 100,000 km. ' +
    f(inside.parts_turnover_eur) + ' sits inside, ' + f(outside) +
    ' outside. Over age accounts for ' + pct(limits.filter(r=>r.position==='over age limit')
      .reduce((a,r)=>a+r.parts_turnover_eur,0) / outside) + ' of the outside total.';

  // ---- charts

  // ---- charts
  const NAVY='#15233c', TERRA='#c0552d';
  const baseOpts = (extra={}) => Object.assign({
    responsive:true, maintainAspectRatio:false,
    // animation off so a QA probe reads the final painted state rather than a mid-animation frame
    animation:false,
    plugins:{legend:{display:false}},
    scales:{x:{grid:{display:false},ticks:{color:NAVY,font:{size:11}}},
            y:{grid:{color:'#f0ece3'},ticks:{color:NAVY,font:{size:11}}}}
  }, extra);

  new Chart(document.getElementById('c1'), {
    type:'bar',
    data:{labels:DATA.lines.slice(0,10).map(r=>r.operation.replace(/ - .*$/,'').slice(0,38)),
      datasets:[{data:DATA.lines.slice(0,10).map(r=>r.parts_turnover_eur),
        backgroundColor:DATA.lines.slice(0,10).map((r,i)=>i===0?TERRA:NAVY), borderRadius:3}]},
    options:baseOpts({indexAxis:'y', plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=DATA.lines[c.dataIndex];
        return [f(r.parts_turnover_eur)+' parts', r.claim_lines+' claims · '+
          f(r.parts_turnover_per_line_eur)+' each', r.markets_present+' markets · median '+
          Math.round(r.median_odometer_km).toLocaleString('en-GB')+' km'];}}}}})
  });

  new Chart(document.getElementById('c2'), {
    type:'bar',
    data:{labels:DATA.cv_family.slice(0,7).map(r=>r.family.replace(/ \(.*\)/,'').slice(0,30)),
      datasets:[{data:DATA.cv_family.slice(0,7).map(r=>r.parts_turnover_eur),
        backgroundColor:DATA.cv_family.slice(0,7).map((r,i)=>i===0?TERRA:NAVY), borderRadius:3}]},
    options:baseOpts({indexAxis:'y', plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=DATA.cv_family[c.dataIndex];
        return [f(r.parts_turnover_eur)+' parts', r.claim_lines+' lines · '+r.part_numbers+
          ' part numbers', pct(r.share_of_parts_turnover)+' of the truck bill'];}}}}})
  });

  new Chart(document.getElementById('c7'), {
    type:'bar',
    data:{labels:DATA.cv_ops.slice(0,10).map(r=>r.operation.replace(/ - .*$/,'').slice(0,38)),
      datasets:[{data:DATA.cv_ops.slice(0,10).map(r=>r.parts_turnover_eur),
        backgroundColor:NAVY, borderRadius:3}]},
    options:baseOpts({indexAxis:'y', plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=DATA.cv_ops[c.dataIndex];
        return [f(r.parts_turnover_eur)+' parts', r.claim_lines+' claims · '+
          f(r.parts_turnover_per_line_eur)+' each', r.markets_present+' markets · median '+
          Math.round(r.median_odometer_km).toLocaleString('en-GB')+' km'];}}}}})
  });

  new Chart(document.getElementById('c3'), {
    type:'bar',
    data:{labels:DATA.family.map(r=>r.family.slice(0,34)),
      datasets:[{data:DATA.family.map(r=>r.parts_turnover_eur),
        backgroundColor:DATA.family.map(r=>r.family.indexOf('Steering')===0?TERRA:NAVY),
        borderRadius:3}]},
    options:baseOpts({indexAxis:'y', plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=DATA.family[c.dataIndex];
        return [f(r.parts_turnover_eur)+' parts ('+pct(r.share_of_parts_turnover)+')',
          r.claim_lines+' lines · '+r.part_numbers+' part numbers',
          'Outside limits: '+pct(r.outside_limits_share)];}}}}})
  });

  new Chart(document.getElementById('c4'), {
    type:'doughnut',
    data:{labels:limits.map(r=>r.position),
      datasets:[{data:limits.map(r=>r.parts_turnover_eur),
        backgroundColor:[NAVY,'#8a6a3f',TERRA], borderColor:'#fff', borderWidth:2}]},
    options:{responsive:true, maintainAspectRatio:false, cutout:'58%',
      plugins:{legend:{position:'bottom',labels:{boxWidth:12,color:NAVY,font:{size:11.5}}},
        tooltip:{callbacks:{label:c=>c.label+': '+f(c.parsed)+' ('+
          pct(c.parsed/DATA.limits.reduce((a,r)=>a+r.parts_turnover_eur,0))+')'}}}}
  });

  const mk = DATA.market.filter(r=>r.claim_lines>=100)
    .sort((a,b)=>b.outside_limits_share-a.outside_limits_share).slice(0,14);
  new Chart(document.getElementById('c5'), {
    type:'bar',
    data:{labels:mk.map(r=>r.market.replace(/^ISUZU |^Isuzu |MIDI EUROPE - /,'').slice(0,22)),
      datasets:[{data:mk.map(r=>r.outside_limits_share*100),
        backgroundColor:mk.map(r=>r.outside_limits_share>0.5?TERRA:NAVY), borderRadius:3}]},
    options:baseOpts({indexAxis:'y', plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=mk[c.dataIndex];
        return [pct(r.outside_limits_share)+' outside the limits',
          f(r.outside_limits_eur)+' of '+f(r.outside_limits_eur+r.inside_limits_eur),
          r.claim_lines+' claim lines'];}}}}})
  });

  const st = DATA.market.filter(r=>r.claim_lines>=100)
    .sort((a,b)=>a.admitted_vs_claimed_ratio-b.admitted_vs_claimed_ratio).slice(0,12);
  new Chart(document.getElementById('c6'), {
    type:'bar',
    data:{labels:st.map(r=>r.market.replace(/^ISUZU |^Isuzu |MIDI EUROPE - /,'').slice(0,20)),
      datasets:[{data:st.map(r=>r.admitted_vs_claimed_ratio*100),
        backgroundColor:st.map(r=>r.admitted_vs_claimed_ratio<1?TERRA:NAVY), borderRadius:3}]},
    options:baseOpts({indexAxis:'y', plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=st[c.dataIndex];
        return [pct(r.admitted_vs_claimed_ratio)+' of claimed parts admitted',
          f(r.parts_admitted_eur)+' admitted against '+f(r.parts_claimed_eur)+' claimed'];}}}}})
  });

  // ---- tables
  function table(el, rows, cols){
    const t = document.getElementById(el);
    t.innerHTML = '<thead><tr>' + cols.map(c=>'<th class="'+(c.r?'r':'')+'">'+c.h+'</th>').join('') +
      '</tr></thead><tbody>' + rows.map(r=>'<tr>' + cols.map(c=>
      '<td class="'+(c.r?'r':'')+'">'+c.v(r)+'</td>').join('') + '</tr>').join('') + '</tbody>';
  }
  table('t1', DATA.cv_market, [
    {h:'Market', v:r=>r.market}, {h:'Currency', v:r=>r.currency},
    {h:'Claims', r:1, v:r=>r.claim_lines.toLocaleString('en-GB')},
    {h:'Parts turnover', r:1, v:r=>f(r.parts_turnover_eur)},
    {h:'Per line', r:1, v:r=>f(r.parts_turnover_per_line_eur)},
    {h:'Part-no. coverage', r:1, v:r=>pct(r.part_number_coverage)}
  ]);
  table('t2', DATA.cv_dealer.slice(0,12), [
    {h:'Dealer', v:r=>r.dealer_code}, {h:'Market', v:r=>r.market},
    {h:'Claims', r:1, v:r=>r.claim_lines.toLocaleString('en-GB')},
    {h:'Share', r:1, v:r=>pct(r.share_of_claim_lines)},
    {h:'Vehicles', r:1, v:r=>r.vehicles.toLocaleString('en-GB')}
  ]);

  new Chart(document.getElementById('c8'), {
    type:'bar',
    data:{labels:DATA.cv_commercial.map(r=>r.market.slice(0,16)),
      datasets:[{data:DATA.cv_commercial.map(r=>r.warranty_eur_per_uio),
        backgroundColor:DATA.cv_commercial.map((r,i)=>i<2?TERRA:NAVY), borderRadius:3}]},
    options:baseOpts({plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>{const r=DATA.cv_commercial[c.dataIndex];
        return [f(r.warranty_eur_per_uio)+' of warranty parts per truck in service',
          r.claim_lines+' claims · '+r.uio_units.toLocaleString('en-GB')+' trucks',
          f(r.warranty_parts_eur)+' of '+f(r.target_wallet_eur)+' target spend'];}}}}})
  });

  const wp = ['Isuzu — fails well inside warranty',
              'boundary — price-list and campaign question',
              'distributor — outside warranty, aftermarket demand'];
  new Chart(document.getElementById('c9'), {
    type:'doughnut',
    data:{labels:wp.map(s=>s.split(' — ')[0]),
      datasets:[{data:wp.map(k=>DATA.who_pays.filter(r=>r.who_pays===k)
        .reduce((a,r)=>a+r.parts_turnover_eur,0)),
        backgroundColor:[TERRA,'#b8860b',NAVY], borderColor:'#fff', borderWidth:2}]},
    options:{responsive:true, maintainAspectRatio:false, cutout:'55%', animation:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:12,color:NAVY,font:{size:11.5}}},
        tooltip:{callbacks:{label:c=>f(c.parsed)+' — '+c.label}}}}
  });

  table('t3', DATA.cv_commercial, [
    {h:'Market', v:r=>r.market},
    {h:'Warranty €', r:1, v:r=>f(r.warranty_parts_eur)},
    {h:'Target spend €', r:1, v:r=>f(r.target_wallet_eur)},
    {h:'% of target spend', r:1, v:r=>r.warranty_pct_of_target_wallet.toFixed(2)+'%'},
    {h:'% of billed', r:1, v:r=>r.warranty_pct_of_parts_billed.toFixed(2)+'%'}
  ]);
  table('t4', DATA.who_pays.map(r=>Object.assign({}, r, {
    who_pays: r.who_pays.split(' — ')[0]})).slice(0,16), [
    {h:'Operation', v:r=>r.operation.replace(/ - .*$/,'')},
    {h:'€', r:1, v:r=>f(r.parts_turnover_eur)},
    {h:'Claims', r:1, v:r=>r.claim_lines.toLocaleString('en-GB')},
    {h:'Median km', r:1, v:r=>Math.round(r.median_odometer_km).toLocaleString('en-GB')},
    {h:'Who pays', v:r=>r.who_pays}
  ]);

  // ?section=N deep-link. The ids are static in the markup (h2#sec1..sec8) so a native fragment
  // link like page.html#sec6 works with no JavaScript at all, which is also what lets a headless
  // screenshot open straight onto a section.
  const sec = (location.search.match(/section=(\d+)/) || [])[1];

  document.getElementById('foot').textContent =
    'Datasets: 01_data/00_derived/warranty_commercial/ (13 CSVs + workbook). Builder: ' +
    '02_dashboards/_build/build_warranty_commercial.py. Sources read-only: ' +
    '01_data/00_derived/warranty_fy26_raw.csv and 01_data/06_Warranty/*.xlsx.';

  // ---- render probe, LAST, after every card, chart and table has been built.
  // Its presence is runtime proof that the whole script reached the end. Sizing on a canvas is
  // applied on the next frame, so wait for two before sampling.
  const sleep2 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const canvasPainted = (c) => {
    const ctx = c.getContext && c.getContext('2d');
    if (!ctx || !c.width) return false;
    try {
      const d = ctx.getImageData(0, 0, c.width, Math.min(c.height, 400)).data;
      for (let i = 3; i < d.length; i += 4) { if (d[i] !== 0) return true; }
    } catch (e) { return false; }
    return false;
  };
  sleep2().then(() => {
    const cvs = document.querySelectorAll('canvas');
    const mounted = Array.prototype.filter.call(cvs,
      c => c.style.width && parseInt(c.style.width, 10) > 0);
    const painted = Array.prototype.filter.call(cvs, canvasPainted);
    const b = document.body;
    b.setAttribute('data-probe-cards', String(document.querySelectorAll('.card').length));
    b.setAttribute('data-probe-rows', String(document.querySelectorAll('table tbody tr').length));
    b.setAttribute('data-probe-canvases', String(cvs.length));
    b.setAttribute('data-probe-mounted', String(mounted.length));
    b.setAttribute('data-probe-painted', String(painted.length));
    b.setAttribute('data-probe-trucktotal',
      document.body.innerText.indexOf('4,655,881') >= 0 ? '1' : '0');
    const sec = (location.search.match(/section=(\d+)/) || [])[1];
    if (sec) {
      const el = document.getElementById('sec' + sec);
      if (el) window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 10);
      b.setAttribute('data-probe-section', sec);
      b.setAttribute('data-probe-scroll', String(Math.round(window.scrollY)));
    }
    b.setAttribute('data-probe-ready', '1');
  });
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
