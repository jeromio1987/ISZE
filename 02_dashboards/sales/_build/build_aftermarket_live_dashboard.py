#!/usr/bin/env python3
"""Build self-contained Aftermarket Live Pricing briefing (embedded scrape JSON).

JP-clear shared: Block-0 margin frame first, then charts.
Reference = customer/workshop price after distributor +40% and dealer +27.5%.
Never lead with PR00×1.785. Never say \"soft\". Custom formula popovers.
Double-click / file:// OK. Local Plotly only (no CDN).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRAPE = ROOT / "01_data" / "14_dashboards" / "partgroups_explorer" / "partgroups_scrape.json"
OUT = ROOT / "02_dashboards" / "pricing" / "ISZE_Aftermarket_Live_Pricing_Dashboard.html"
MIN_N = 3


def build_aftermarket_live_html(scrape: dict | None = None) -> Path:
    if scrape is None:
        scrape = json.loads(SCRAPE.read_text(encoding="utf-8"))
    payload = json.dumps(scrape, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE · Aftermarket Live Pricing</title>
<style>
:root{{--red:#CC0E1E;--ink:#1A1A1A;--muted:#5A5A5A;--line:#E4E4E7;--amber:#B45309;--ok:#15803D;--bg:#FAFAFA}}
*{{box-sizing:border-box}}
body{{margin:0;background:#fff;color:var(--ink);font:15px/1.55 "Segoe UI",Arial,Helvetica,sans-serif}}
.wrap{{max-width:1140px;margin:0 auto;padding:0 28px 80px}}
header{{border-bottom:3px solid var(--red);padding:34px 0 18px;margin-bottom:18px}}
.brand{{font:800 12px/1 Arial Black,Arial;letter-spacing:.2em;color:var(--red);margin-bottom:12px}}
h1{{font-size:28px;margin:0 0 8px;letter-spacing:-.3px}}
.sub{{color:var(--muted);max-width:920px;font-size:14.5px}}
.stamp{{margin-top:10px;font-size:12px;color:var(--muted)}}
.back{{margin-top:8px;font-size:13px}}.back a{{color:var(--red)}}
.frame{{border:1px solid var(--line);border-top:4px solid var(--red);padding:18px 20px;margin:0 0 22px;background:#fff}}
.frame h2{{margin:0 0 12px;font-size:18px}}
.frame .q{{margin:0 0 12px;padding-bottom:12px;border-bottom:1px solid #F0F0F0}}
.frame .q:last-child{{border-bottom:none;margin-bottom:0;padding-bottom:0}}
.frame .ql{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--red);margin-bottom:4px}}
.frame p{{margin:0;font-size:14.5px;line-height:1.55}}
.frame .footn{{margin-top:12px;font-size:12px;color:var(--muted)}}
.story{{background:#FDF3F4;border-left:4px solid var(--red);padding:14px 16px;margin:0 0 18px}}
.story h2{{margin:0 0 6px;font-size:17px}}
.story ul{{margin:6px 0 0;padding-left:18px}}.story li{{margin:4px 0}}
.defs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:0 0 20px}}
.def{{border:1px solid var(--line);padding:11px 12px;background:var(--bg);cursor:pointer}}
.def b{{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}}
.def .f{{font-size:11.5px;font-family:Consolas,monospace}}
.def .p{{font-size:12px;color:var(--muted);margin-top:4px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin:0 0 24px}}
.kpi{{border:1px solid var(--line);border-top:3px solid var(--red);padding:12px 13px;cursor:pointer}}
.kpi.amber{{border-top-color:var(--amber)}}
.kpi .v{{font-size:26px;font-weight:800;letter-spacing:-.7px}}
.kpi .l{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:5px;font-weight:600}}
.kpi .n{{font-size:11.5px;color:var(--muted);margin-top:4px}}
section{{margin:0 0 34px;padding-top:10px;border-top:1px solid var(--line)}}
h2{{font-size:17px;margin:0 0 4px}}
.lead{{color:var(--muted);font-size:13.5px;margin:0 0 12px;max-width:920px}}
.why{{border:1px solid #F0D7B0;background:#FEF8F0;padding:12px 14px;margin:0 0 14px;font-size:13.5px;color:#7A4A12}}
.why b{{color:var(--amber)}}
.card{{border:1px solid var(--line);padding:14px 16px;margin:0 0 12px}}
.card h3{{margin:0 0 8px;font-size:13.5px}}
.chart{{min-height:340px}}
.trust{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}}
.tchip{{border:1px solid var(--line);padding:10px 12px;font-size:12.5px}}
.tchip .s{{font-weight:700;margin-bottom:3px}}
.tchip.dead{{border-left:3px solid var(--red)}}
.tchip.ok{{border-left:3px solid var(--ok)}}
.tchip.thin{{border-left:3px solid var(--amber)}}
details.ev{{border:1px solid var(--line);padding:0;margin:10px 0 0}}
details.ev>summary{{cursor:pointer;padding:11px 14px;font-weight:600;font-size:13px;background:var(--bg);list-style:none}}
details.ev>summary::-webkit-details-marker{{display:none}}
details.ev>summary::before{{content:'▸ ';color:var(--red)}}
details.ev[open]>summary::before{{content:'▾ '}}
.scroll{{max-height:360px;overflow:auto;border-top:1px solid var(--line)}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{background:var(--red);color:#fff;text-align:left;padding:8px 9px;font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;cursor:pointer}}
td{{padding:7px 9px;border-bottom:1px solid #F0F0F0;vertical-align:top}}
tbody tr:nth-child(even){{background:#FAFAFA}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.under{{color:var(--red);font-weight:600}}
.notes{{font-size:12.5px;color:var(--muted)}}
.foot{{font-size:11.5px;color:#999;margin-top:28px;border-top:1px solid var(--line);padding-top:12px}}
#tip{{display:none;position:fixed;z-index:9999;max-width:360px;background:#1A1A1A;color:#fff;padding:12px 14px;border-radius:8px;font-size:12.5px;line-height:1.45;pointer-events:none;box-shadow:0 8px 24px rgba(0,0,0,.25)}}
#tip .tl{{font-weight:700;margin-bottom:4px}}
#tip .tf{{font-family:Consolas,monospace;color:#F5D0D3;margin-bottom:6px;font-size:12px}}
#tip .te{{color:#D4D4D8;white-space:pre-line}}
</style>
<script src="../_ui/plotly.min.js"></script>
</head>
<body>
<div id="tip" role="tooltip"></div>
<div class="wrap">
<header>
  <div class="brand">ISZE</div>
  <h1>Aftermarket Live Pricing</h1>
  <p class="sub">Online shops versus our reference customer / workshop price — after distributor and dealer margins. Not Eucon PartsPool.</p>
  <div class="stamp" id="stamp">Loading…</div>
  <div class="back"><a href="http://127.0.0.1:8766/ISZE_PartGroups_Sales_Explorer.html">Part-Groups Explorer (http://127.0.0.1:8766 — run OPEN_PartGroups_Explorer.cmd once if the link fails)</a></div>
</header>

<div class="frame" id="frame"></div>
<div class="story" id="story"></div>
<div class="defs" id="defs"></div>
<div class="kpis" id="kpis"></div>

<section>
  <h2>1 · Where are we exposed?</h2>
  <p class="lead">Each bubble is a part number. Left = shop further below our reference customer price. Higher = more CY2025 sales. Larger = more illustrative pressure. Hover for the arithmetic.</p>
  <div class="card"><div class="chart" id="bubbleChart"></div></div>
  <details class="ev"><summary>Evidence · sales on undercut parts</summary><div class="scroll" id="expTbl"></div></details>
</section>

<section>
  <h2>2 · Where is the catalogue channel torn?</h2>
  <div class="why" id="whyKs"></div>
  <p class="lead">Same PN on KS: aftermarket quote vs genuine quote vs our reference customer price. The gap is the channel story — not “ISZE vs KS”.</p>
  <div class="card"><div class="chart" id="dumbbellChart"></div></div>
  <details class="ev"><summary>Evidence · channel spread by part</summary><div class="scroll" id="spreadTbl"></div></details>
</section>

<section>
  <h2>3 · Which part families sit below our reference?</h2>
  <p class="lead">Median shop ÷ reference customer price by AIM category. Left of 1.0 = shops cheaper than our reference (pressure). Right of 1.0 = shops dearer — can include a legitimate OEM premium. Bars with fewer than {MIN_N} hits are grey (directional only — not statistically reliable).</p>
  <div class="card"><div class="chart" id="heatChart"></div></div>
</section>

<section>
  <h2>4 · Can we trust the feeds?</h2>
  <p class="lead">Integrity before action. Autodoc has no usable PN history on disk — do not treat it as a competitive signal.</p>
  <div class="trust" id="trust"></div>
</section>

<section>
  <h2>Notes</h2>
  <ul class="notes" id="caveats"></ul>
</section>
<p class="foot">Self-contained briefing · scrape embedded · shared · Rebuild via partgroups payload builder</p>
</div>
<script type="application/json" id="scrape-data">{payload}</script>
<script>
(function(){{
  var S = JSON.parse(document.getElementById('scrape-data').textContent);
  var k = S.kpis || {{}}, story = S.story || {{}}, defs = story.definitions || {{}}, basis = S.compare_basis || {{}}, frame = story.frame || {{}};
  var MIN_N = (basis.min_n_family != null) ? basis.min_n_family : {MIN_N};
  var tipEl = document.getElementById('tip');

  function pct(v){{ if(v==null||isNaN(v)) return '—'; return (v*100).toFixed(0)+'%'; }}
  function money(v){{ if(v==null||isNaN(v)) return '—'; return '€'+Math.round(v).toLocaleString('en-GB'); }}
  function money2(v){{ if(v==null||isNaN(v)) return '—'; return Number(v).toFixed(2); }}

  function showTip(e, label, formula, example){{
    tipEl.innerHTML = '<div class="tl">'+label+'</div><div class="tf">'+(formula||'')+'</div><div class="te">'+(example||'')+'</div>';
    tipEl.style.display = 'block'; moveTip(e);
  }}
  function moveTip(e){{
    var x = e.clientX + 14, y = e.clientY + 14;
    var w = tipEl.offsetWidth || 280, h = tipEl.offsetHeight || 80;
    if(x + w > window.innerWidth - 12) x = e.clientX - w - 12;
    if(y + h > window.innerHeight - 12) y = e.clientY - h - 12;
    tipEl.style.left = x + 'px'; tipEl.style.top = y + 'px';
  }}
  function hideTip(){{ tipEl.style.display = 'none'; }}
  function bindTip(el, label, formula, example){{
    if(!el) return;
    el.addEventListener('mouseenter', function(e){{ showTip(e, label, formula, example); }});
    el.addEventListener('mousemove', moveTip);
    el.addEventListener('mouseleave', hideTip);
  }}
  function defTip(key, fallbackExample){{
    var d = defs[key] || {{}};
    return {{ label: d.label || key, formula: d.formula || '', example: fallbackExample || d.plain || '' }};
  }}

  document.getElementById('stamp').textContent =
    'Built '+(S.built_at_utc||'—')+' · reference = ISZE list → +40% distributor → +27.5% dealer · embedded (double-click OK)';

  document.getElementById('frame').innerHTML =
    '<h2>'+(frame.title||'What this briefing tracks')+'</h2>'+
    '<div class="q"><div class="ql">What we track</div><p>'+(frame.track||'')+'</p></div>'+
    '<div class="q"><div class="ql">What good looks like</div><p>'+(frame.good||'')+'</p></div>'+
    '<div class="q"><div class="ql">What this is not</div><p>'+(frame.not_this||'')+'</p></div>'+
    '<div class="footn">'+(frame.margin_plain||'')+' '+(frame.min_n_rule||'')+'</div>';

  document.getElementById('story').innerHTML =
    '<h2>'+(story.headline||'Aftermarket vs reference customer price')+'</h2><ul>'+
    (story.bullets||[]).map(function(b){{return '<li>'+b+'</li>';}}).join('')+'</ul>';

  document.getElementById('defs').innerHTML = ['reference_sellout','price_index','genuine_index','am_index','channel_spread','price_pressure'].map(function(key){{
    var d = defs[key]; if(!d) return '';
    return '<div class="def" data-def="'+key+'"><b>'+d.label+'</b><div class="f">'+d.formula+'</div><div class="p">'+d.plain+'</div></div>';
  }}).join('');
  Array.prototype.forEach.call(document.querySelectorAll('.def'), function(el){{
    var t = defTip(el.getAttribute('data-def'));
    bindTip(el, t.label, t.formula, t.example);
  }});

  var ks = k.ks_gen_vs_am || {{}};
  var kpiSpec = [
    {{key:'price_index', label:'Median shop / reference', val: k.median_am_vs_street!=null?k.median_am_vs_street.toFixed(2):'—', sub: pct(k.share_undercut_street)+' of hits below reference', cls:'',
      ex: 'Median of (shop € ÷ reference customer price €) across '+(k.real_pn_price_hits||0)+' real PN hits. Below 1.0 = undercut pressure; near 1.0 = near reference (neutral); above 1.0 can be an OEM premium — not a failure.'}},
    {{key:null, label:'Sales on undercut list', val: money(k.exposure_rev_cy2025_eur), sub:'CY2025 on evidence PNs', cls:'',
      lab:'Sales on undercut list', form:'Sum of CY2025 sales € on top undercut part numbers', ex:'Evidence scale — not booked lost revenue.'}},
    {{key:'price_pressure', label:'Illustrative pressure', val: money(k.illustrative_price_pressure_eur), sub:'sales × gap to reference', cls:'amber',
      ex: 'CY2025 sales × (1 − price index) on the undercut evidence list — not a P&L write-off.'}},
    {{key:'channel_spread', label:'KS channel spread', val: k.ks_channel_spread_median!=null?k.ks_channel_spread_median.toFixed(2):'—', sub:'median genuine − AM (n='+(ks.n||0)+')', cls:'',
      ex: 'Median of (genuine÷reference − AM÷reference) on KS dual-listed PNs.'}}
  ];
  document.getElementById('kpis').innerHTML = kpiSpec.map(function(c,i){{
    return '<div class="kpi '+c.cls+'" data-kpi="'+i+'"><div class="v">'+c.val+'</div><div class="l">'+c.label+'</div><div class="n">'+c.sub+'</div></div>';
  }}).join('');
  Array.prototype.forEach.call(document.querySelectorAll('.kpi'), function(el){{
    var c = kpiSpec[+el.getAttribute('data-kpi')];
    var t = c.key ? defTip(c.key, c.ex) : {{label:c.lab, formula:c.form, example:c.ex}};
    bindTip(el, t.label, t.formula, t.example);
  }});

  document.getElementById('whyKs').innerHTML = '<b>Why this lens:</b> '+(story.why_ks_gen_vs_am||'');

  function whenPlotly(fn){{
    if(window.Plotly) return fn();
    var n=0,t=setInterval(function(){{ if(window.Plotly||++n>50){{ clearInterval(t); if(window.Plotly) fn(); }} }},100);
  }}

  whenPlotly(function(){{
    var exp = (S.revenue_exposure_undercut||[]).filter(function(r){{ return r.street_index!=null && r.rev_cy2025_eur; }});
    var pressure = exp.map(function(r){{ return Math.max(0, (r.rev_cy2025_eur||0)*(1-(r.street_index||1))); }});
    var maxP = Math.max.apply(null, pressure.concat([1]));
    Plotly.newPlot('bubbleChart',[{{
      x: exp.map(function(r){{ return r.street_index; }}),
      y: exp.map(function(r){{ return r.rev_cy2025_eur; }}),
      mode:'markers',
      text: exp.map(function(r){{ return (r.description||r.pn||'').slice(0,36); }}),
      customdata: exp.map(function(r,i){{ return [r.pn, r.am_eur, r.street_eur, r.source, pressure[i]]; }}),
      marker:{{
        size: pressure.map(function(p){{ return 10 + 28*(p/maxP); }}),
        color: exp.map(function(r){{ var i=r.street_index||1; return i<0.35?'#CC0E1E':(i<0.7?'#B45309':'#5A5A5A'); }}),
        opacity:0.85, line:{{width:1, color:'#fff'}}
      }},
      hovertemplate:
        '<b>%{{text}}</b><br>%{{customdata[0]}}<br>'+
        'Price index %{{x:.2f}} = shop €%{{customdata[1]}} ÷ reference customer price €%{{customdata[2]}}<br>'+
        'CY25 sales €%{{y:,.0f}}<br>'+
        'Illustrative pressure €%{{customdata[4]:,.0f}} = sales × (1 − index)<br>'+
        'Source: %{{customdata[3]}}<extra></extra>'
    }}],{{
      margin:{{t:20,r:20,b:50,l:70}}, height:420,
      xaxis:{{title:'Price index (shop ÷ reference customer price)  ·  ← deeper undercut', range:[0, Math.max(1.15, 1.05*Math.max.apply(null, exp.map(function(r){{return r.street_index||0;}})||1))], gridcolor:'#eee', zeroline:false}},
      yaxis:{{title:'CY2025 sales €', gridcolor:'#eee'}},
      shapes:[{{type:'line', x0:1, x1:1, y0:0, y1:1, yref:'paper', line:{{color:'#999', dash:'dot'}}}}],
      annotations:[{{x:1, y:1.02, xref:'x', yref:'paper', text:'Our reference (=1.0) — not a target', showarrow:false, font:{{size:10, color:'#888'}}}}],
      font:{{family:'Segoe UI, Arial, sans-serif', size:11}}
    }},{{displayModeBar:false, responsive:true}});

    var gen = (S.ks_genuine_vs_am||[]).slice().sort(function(a,b){{
      var sa=a.channel_spread!=null?a.channel_spread:((a.gen_vs_street||0)-(a.am_vs_street||0));
      var sb=b.channel_spread!=null?b.channel_spread:((b.gen_vs_street||0)-(b.am_vs_street||0));
      return sb-sa;
    }}).slice(0,12).reverse();
    var labels = gen.map(function(r){{ return (r.description||r.pn||'').slice(0,26); }});
    var traces = [];
    for(var i=0;i<gen.length;i++){{
      var g=gen[i];
      traces.push({{ x:[g.am_vs_street, g.gen_vs_street], y:[labels[i], labels[i]], mode:'lines', line:{{color:'#D4D4D8', width:3}}, showlegend:false, hoverinfo:'skip' }});
    }}
    traces.push({{
      x: gen.map(function(r){{ return r.am_vs_street; }}), y: labels, mode:'markers', name:'AM vs reference',
      marker:{{size:11, color:'#CC0E1E'}},
      customdata: gen.map(function(r){{ return [r.pn, r.am_eur, r.street_eur]; }}),
      hovertemplate:'AM vs reference %{{x:.2f}} = AM €%{{customdata[1]}} ÷ reference €%{{customdata[2]}}<br>%{{customdata[0]}}<extra></extra>'
    }});
    traces.push({{
      x: gen.map(function(){{ return 1; }}), y: labels, mode:'markers', name:'Reference (=1.0)',
      marker:{{size:8, color:'#1A1A1A', symbol:'line-ns-open', line:{{width:2, color:'#1A1A1A'}}}},
      customdata: gen.map(function(r){{ return [r.pn, r.street_eur]; }}),
      hovertemplate:'Reference customer price €%{{customdata[1]}} = ISZE list → +40% distributor → +27.5% dealer<br>%{{customdata[0]}}<extra></extra>'
    }});
    traces.push({{
      x: gen.map(function(r){{ return r.gen_vs_street; }}), y: labels, mode:'markers', name:'Genuine vs reference',
      marker:{{size:11, color:'#1A1A1A'}},
      customdata: gen.map(function(r){{
        var sp = r.channel_spread!=null?r.channel_spread:((r.gen_vs_street||0)-(r.am_vs_street||0));
        return [r.pn, r.gen_eur, r.street_eur, r.am_eur, r.am_vs_street, sp];
      }}),
      hovertemplate:
        'Genuine vs reference %{{x:.2f}} = genuine €%{{customdata[1]}} ÷ reference €%{{customdata[2]}}<br>'+
        'AM vs reference %{{customdata[4]:.2f}} = AM €%{{customdata[3]}} ÷ reference €%{{customdata[2]}}<br>'+
        'Channel spread %{{customdata[5]:.2f}}<br>%{{customdata[0]}}<extra></extra>'
    }});
    Plotly.newPlot('dumbbellChart', traces, {{
      margin:{{t:30,r:20,b:45,l:150}}, height: Math.max(360, gen.length*32),
      xaxis:{{title:'Index vs reference customer price (1.0 = our reference)', range:[0, Math.max(1.35, 1.1*Math.max.apply(null, gen.map(function(r){{return Math.max(r.gen_vs_street||0,r.am_vs_street||0);}})))] , gridcolor:'#eee'}},
      yaxis:{{tickfont:{{size:10}}}}, legend:{{orientation:'h', y:1.12}},
      shapes:[{{type:'line', x0:1, x1:1, y0:-0.5, y1:gen.length-0.5, line:{{color:'#999', dash:'dot'}}}}],
      font:{{family:'Segoe UI, Arial, sans-serif', size:11}}
    }},{{displayModeBar:false, responsive:true}});

    // Family chart — min-n gate
    var heat = (S.category_heat||[]).slice().reverse();
    Plotly.newPlot('heatChart',[{{
      y: heat.map(function(r){{
        var tag = r.n < MIN_N ? ' · n<'+MIN_N+' directional' : '';
        return r.aim_category+' (n='+r.n+')'+tag;
      }}),
      x: heat.map(function(r){{ return r.median_street_index; }}),
      type:'bar', orientation:'h',
      marker:{{ color: heat.map(function(r){{
        if(r.n < MIN_N) return '#D4D4D8';
        var i=r.median_street_index||1; return i<0.5?'#CC0E1E':(i<1?'#B45309':'#5A5A5A');
      }}) }},
      customdata: heat.map(function(r){{ return [r.p25, r.p75, r.n, r.n < MIN_N ? 'Directional only — n<'+MIN_N+' not reliable for ranking' : 'Usable sample (n≥'+MIN_N+')']; }}),
      hovertemplate:'%{{y}}<br>Median price index %{{x:.2f}} = median(shop € ÷ reference customer price €)<br>P25–P75: %{{customdata[0]:.2f}}–%{{customdata[1]:.2f}}<br>%{{customdata[3]}}<extra></extra>'
    }}],{{
      margin:{{t:8,r:20,b:40,l:200}}, height: Math.max(300, heat.length*30),
      xaxis:{{ title:'Median shop € / reference customer price €', range:[0, Math.max(1.6, 1.1*Math.max.apply(null, heat.map(function(r){{return r.median_street_index||0;}})||1))], gridcolor:'#eee'}},
      shapes:[{{type:'line', x0:1, x1:1, y0:-0.5, y1:Math.max(0,heat.length-0.5), line:{{color:'#999', dash:'dot'}}}}],
      annotations:[{{x:1, y:1.02, xref:'x', yref:'paper', text:'Our reference (=1.0) · grey = n<'+MIN_N, showarrow:false, font:{{size:10, color:'#888'}}}}],
      font:{{family:'Segoe UI, Arial, sans-serif', size:11}}
    }},{{displayModeBar:false, responsive:true}});
  }});

  var thRef = defTip('reference_sellout'), thIdx = defTip('price_index'), thGen = defTip('genuine_index'), thAm = defTip('am_index'), thSp = defTip('channel_spread');

  document.getElementById('expTbl').innerHTML =
    '<table><thead><tr><th>Source</th><th>Part</th>'+
    '<th class="n tiph" data-t="ref">Reference €</th><th class="n">Shop €</th>'+
    '<th class="n tiph" data-t="idx">Price index</th><th class="n">CY25 sales €</th></tr></thead><tbody>'+
    (S.revenue_exposure_undercut||[]).slice(0,25).map(function(r){{
      var ex = 'Price index = '+money2(r.am_eur)+' ÷ '+money2(r.street_eur)+' = '+(r.street_index!=null?r.street_index:'—')+
        '\\nReference = ISZE list → +40% distributor → +27.5% dealer';
      return '<tr class="tiprow" data-ex="'+ex.replace(/"/g,'&quot;')+'"><td>'+r.source+'</td><td>'+(r.description||'')+'<div style="color:#888;font-size:11px">'+(r.pn||'')+'</div></td><td class="n">'+(r.street_eur!=null?r.street_eur:'—')+'</td><td class="n">'+(r.am_eur!=null?r.am_eur:'—')+'</td><td class="n under">'+(r.street_index!=null?r.street_index:'—')+'</td><td class="n">'+(r.rev_cy2025_eur!=null?Math.round(r.rev_cy2025_eur).toLocaleString('en-GB'):'—')+'</td></tr>';
    }}).join('')+'</tbody></table>';

  var spreads = (S.ks_genuine_vs_am||[]).slice().sort(function(a,b){{
    var sa=a.channel_spread!=null?a.channel_spread:((a.gen_vs_street||0)-(a.am_vs_street||0));
    var sb=b.channel_spread!=null?b.channel_spread:((b.gen_vs_street||0)-(b.am_vs_street||0));
    return sb-sa;
  }});
  document.getElementById('spreadTbl').innerHTML =
    '<table><thead><tr>'+
    '<th class="tiph" data-t="gen">Genuine vs reference</th><th class="tiph" data-t="am">AM vs reference</th>'+
    '<th class="tiph" data-t="sp">Channel spread</th><th>Part</th></tr></thead><tbody>'+
    spreads.slice(0,20).map(function(r){{
      var sp=r.channel_spread!=null?r.channel_spread:((r.gen_vs_street||0)-(r.am_vs_street||0));
      var ex = 'Genuine vs reference = '+money2(r.gen_eur)+' ÷ '+money2(r.street_eur)+' = '+(r.gen_vs_street!=null?r.gen_vs_street.toFixed(2):'—')+
        '\\nAM vs reference = '+money2(r.am_eur)+' ÷ '+money2(r.street_eur)+' = '+(r.am_vs_street!=null?r.am_vs_street.toFixed(2):'—')+
        '\\nChannel spread = '+sp.toFixed(2)+'\\nReference = ISZE list → +40% distributor → +27.5% dealer';
      return '<tr class="tiprow" data-ex="'+ex.replace(/"/g,'&quot;')+'"><td class="n">'+(r.gen_vs_street!=null?r.gen_vs_street.toFixed(2):'—')+'</td><td class="n under">'+(r.am_vs_street!=null?r.am_vs_street.toFixed(2):'—')+'</td><td class="n"><b>'+sp.toFixed(2)+'</b></td><td>'+(r.description||r.pn)+'<div style="color:#888;font-size:11px">'+r.pn+'</div></td></tr>';
    }}).join('')+'</tbody></table>';

  var tipMap = {{ref: thRef, idx: thIdx, gen: thGen, am: thAm, sp: thSp}};
  Array.prototype.forEach.call(document.querySelectorAll('.tiph'), function(th){{
    var t = tipMap[th.getAttribute('data-t')]; if(t) bindTip(th, t.label, t.formula, t.example);
  }});
  Array.prototype.forEach.call(document.querySelectorAll('.tiprow'), function(tr){{
    tr.addEventListener('mouseenter', function(e){{ showTip(e, 'Worked example', 'shop ÷ reference customer price', tr.getAttribute('data-ex')||''); }});
    tr.addEventListener('mousemove', moveTip);
    tr.addEventListener('mouseleave', hideTip);
  }});

  var adHist = S.autodoc_history || {{}};
  document.getElementById('trust').innerHTML = (S.sources||[]).map(function(r){{
    var cls='thin', note='Thin / limited fill';
    if(r.source==='Autodoc' || (r.placeholders_dropped||0)>50){{
      cls='dead';
      note = adHist.note || 'No usable Autodoc PN history on disk — placeholders only';
    }} else if((r.fill_rate_real||0)>=0.1 && r.kind==='pn_basket'){{
      cls='ok'; note='Usable PN hits';
    }} else if(r.kind==='category_shop'){{
      cls='thin'; note='No PN join — excluded from decisions';
    }}
    return '<div class="tchip '+cls+'"><div class="s">'+r.source+'</div>'+note+'<br>Hits '+(r.real_price_hits||0)+' · last '+(r.last_scraped_sample||'—')+'</div>';
  }}).join('');

  document.getElementById('caveats').innerHTML = (S.caveats||[]).map(function(c){{return '<li>'+c+'</li>';}}).join('');
}})();
</script>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = build_aftermarket_live_html()
    print(f"wrote {p} ({p.stat().st_size/1e6:.3f} MB)")
