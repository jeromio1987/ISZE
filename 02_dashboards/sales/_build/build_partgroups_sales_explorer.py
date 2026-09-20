#!/usr/bin/env python3
"""Build slim Part-Groups Sales Explorer (4 tabs, external JSON, shared Plotly).

Usage (from ISZE root):
  python 02_dashboards/sales/_build/build_partgroups_sales_explorer.py
  python 02_dashboards/sales/_build/build_partgroups_sales_explorer.py --from-original
  python 02_dashboards/sales/_build/build_partgroups_sales_explorer.py --gps-scrape-only

Size budget: HTML shell < ~500 KB. Never re-inline plotly.js or pnyear into HTML.
Data: 01_data/14_dashboards/partgroups_explorer/ (+ synced copy under sales/partgroups_data/).
Open via OPEN_PartGroups_Explorer.cmd (starts local HTTP). Do not double-click the HTML —
agg/pnyear are multi-MB and need fetch. Aftermarket Live Pricing is self-contained (embedded JSON).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Local payload builders (Ireland V20 UIO overlay + street-basis scrape)
from build_partgroups_payloads import (  # noqa: E402
    build_gps_pms as _payload_gps_pms,
    build_scrape as _payload_scrape,
    sync_sibling as _payload_sync,
)

ROOT = Path(__file__).resolve().parents[3]
BUILD = Path(__file__).resolve().parent
EXTRACT = BUILD / "_extracted"
HISTORY = BUILD / "history" / "ISZE_PartGroups_Sales_Explorer_2026-08-11_from_Downloads.html"
OUT_HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PartGroups_Sales_Explorer.html"
DATA = ROOT / "01_data" / "14_dashboards" / "partgroups_explorer"
SIBLING = ROOT / "02_dashboards" / "sales" / "partgroups_data"
PACK = ROOT / "02_dashboards" / "pricing" / "pricing_full_analysis_pack.json"
PMS_CSV = ROOT / "01_data" / "00_derived" / "pricing_pack_pms_total_by_db_year.csv"
GPS_CSV = ROOT / "01_data" / "00_derived" / "pricing_pack_aim_gps_cy2025.csv"
SCRAPER = ROOT / "04_tools" / "autodoc_scraper"
ASOF = SCRAPER / "scrape_asof.json"
README = ROOT / "02_dashboards" / "sales" / "partgroups_data" / "README.md"

GBP_EUR = 1.17


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def extract_from_original(src: Path) -> None:
    """Split the fat Downloads HTML into CSS / body / app JS / JSON payloads."""
    EXTRACT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    t = src.read_text(encoding="utf-8", errors="replace")

    head = t[t.find("<head") : t.find("</head>")]
    style_m = re.search(r"<style>(.*?)</style>", head, re.I | re.S)
    css = style_m.group(1) if style_m else ""
    (EXTRACT / "original.css").write_text(css, encoding="utf-8")

    body_start = t.find("<body")
    body_open_end = t.find(">", body_start) + 1
    first_script = t.find("<script", body_open_end)
    ui_html = t[body_open_end:first_script]
    (EXTRACT / "original_body.html").write_text(ui_html, encoding="utf-8")

    for sid, fname in [
        ("agg-data", "partgroups_agg.json"),
        ("pnyear-data", "partgroups_pnyear.json"),
        ("competitive-data", "partgroups_competitive.json"),
        ("meta-data", "partgroups_meta.json"),
    ]:
        m = re.search(
            rf'<script id="{sid}" type="application/json">(.*?)</script>',
            t,
            re.I | re.S,
        )
        if not m:
            raise SystemExit(f"missing {sid} in {src}")
        obj = json.loads(m.group(1))
        (DATA / fname).write_text(
            json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
            encoding="utf-8",
        )

    scripts = list(
        re.finditer(r"<script(?![^>]*src=)(?![^>]*id=)>(.*?)</script>", t, re.I | re.S)
    )
    app = None
    for m in scripts:
        body = m.group(1).strip()
        if body.startswith("/**") and "plotly" in body[:120].lower():
            continue
        if "(function" in body[:200] or "'use strict'" in body[:200]:
            app = body
    if not app:
        raise SystemExit("could not find app JS")
    (EXTRACT / "original_app.js").write_text(app, encoding="utf-8")
    print(f"extracted from {src}")


def sync_sibling() -> None:
    SIBLING.mkdir(parents=True, exist_ok=True)
    for p in DATA.glob("partgroups_*.json"):
        shutil.copy2(p, SIBLING / p.name)


def build_gps_pms() -> dict:
    """Delegate to payload module (V20 UIO overlay + flags)."""
    return _payload_gps_pms()


def build_scrape() -> dict:
    """Delegate to payload module (street ×1.785, placeholder filter, FX)."""
    return _payload_scrape()


def patch_app_js(original: str) -> str:
    """Adapt original explorer JS for external JSON, lazy pnyear, and tabs."""
    js = original

    # shared wording in competitive notes
    js = js.replace("internal / Jerome-only", "Internal / Jerome-only")
    js = js.replace("Mode-B work-in-progress", "internal work-in-progress")
    js = js.replace("explicitly a internal", "explicitly an internal")

    old_boot = """  function parseCompact(id){
    var obj = JSON.parse(document.getElementById(id).textContent);
    var cols = obj.columns, rows = obj.rows;
    return rows.map(function(r){
      var o = {};
      for (var i=0;i<cols.length;i++) o[cols[i]] = r[i];
      return o;
    });
  }
  var AGG = parseCompact('agg-data');
  var PNYEAR = parseCompact('pnyear-data');
  var COMPETITIVE = parseCompact('competitive-data');
  var META = JSON.parse(document.getElementById('meta-data').textContent);

  document.getElementById('stampDate').textContent = META.date_max;
  document.getElementById('topMeta').innerHTML = META.date_min + ' → ' + META.date_max + ' &middot; ' +
    META.db_codes_present.length + ' distributors &middot; GPS-eligible net sales';
"""

    new_boot = """  function parseCompactObj(obj){
    var cols = obj.columns, rows = obj.rows;
    return rows.map(function(r){
      var o = {};
      for (var i=0;i<cols.length;i++) o[cols[i]] = r[i];
      return o;
    });
  }
  function dataUrl(name){ return 'partgroups_data/' + name; }
  function loadJson(name){
    return fetch(dataUrl(name)).then(function(r){
      if(!r.ok) throw new Error('Failed to load '+name+' ('+r.status+'). Double-click OPEN_PartGroups_Explorer.cmd — do not open the HTML via file://.');
      return r.json();
    });
  }

  var AGG = null;
  var PNYEAR = null;
  var PNYEAR_LOADING = null;
  var COMPETITIVE = null;
  var META = null;
  var GPS_PMS = null;
  var SCRAPE = null;
  var activeTab = 'sales';
  var gpsRendered = false;
  var scrapeRendered = false;

  function ensurePnyear(){
    if(PNYEAR) return Promise.resolve(PNYEAR);
    if(PNYEAR_LOADING) return PNYEAR_LOADING;
    var el = document.getElementById('moversWrap');
    if(el) el.innerHTML = '<div class="empty-msg">Loading part-number sample (~12 MB)…</div>';
    PNYEAR_LOADING = loadJson('partgroups_pnyear.json').then(function(obj){
      PNYEAR = parseCompactObj(obj);
      PNYEAR_LOADING = null;
      return PNYEAR;
    });
    return PNYEAR_LOADING;
  }
"""
    if old_boot not in js:
        raise SystemExit("boot block not found — original_app.js changed")
    js = js.replace(old_boot, new_boot)

    # renderL1L2 uses PNYEAR when L1 selected — make async-aware
    old_l2pn = """    document.getElementById('l2ChartTitle').innerHTML = 'Top part numbers in '+state.l1+' <span class="toggle-table" data-target="l2Tbl">Table view</span>';
    var pnRows = PNYEAR.filter(function(r){"""
    new_l2pn = """    document.getElementById('l2ChartTitle').innerHTML = 'Top part numbers in '+state.l1+' <span class="toggle-table" data-target="l2Tbl">Table view</span>';
    document.getElementById('l2Chart').innerHTML = '<div class="empty-msg">Loading part-number sample…</div>';
    ensurePnyear().then(function(){ renderL1L2Pn(); }).catch(function(err){
      document.getElementById('l2Chart').innerHTML = '<div class="empty-msg">'+String(err.message||err)+'</div>';
    });
    return;
  }
  function renderL1L2Pn(){
    var pnRows = PNYEAR.filter(function(r){"""
    if old_l2pn not in js:
        raise SystemExit("L1L2 PN block not found")
    js = js.replace(old_l2pn, new_l2pn)

    # Close the early-return path: after empty-msg for pnKeys, we need extra closing for renderL1L2Pn
    # The original ends renderL1L2 with the empty check then }. We'll leave structure; renderL1L2Pn ends at same place.

    old_movers = """  function renderMovers(){
    var rows = PNYEAR.filter(function(r){"""
    new_movers = """  function renderMovers(){
    document.getElementById('moversWrap').innerHTML = '<div class="empty-msg">Loading part-number sample…</div>';
    ensurePnyear().then(function(){ renderMoversInner(); }).catch(function(err){
      document.getElementById('moversWrap').innerHTML = '<div class="empty-msg">'+String(err.message||err)+'</div>';
    });
  }
  function renderMoversInner(){
    var rows = PNYEAR.filter(function(r){"""
    if old_movers not in js:
        raise SystemExit("movers block not found")
    js = js.replace(old_movers, new_movers)

    old_render_all = """  function renderAll(){
    renderFilterUI();
    renderKPI();
    renderTrend();
    renderDbChart();
    renderL1L2();
    renderBvp();
    renderComp();
    renderMovers();
  }"""
    new_render_all = """  function renderAll(){
    renderFilterUI();
    renderKPI();
    if(activeTab==='sales'){
      renderTrend();
      renderDbChart();
      renderL1L2();
      renderBvp();
      renderMovers();
    } else if(activeTab==='competitive'){
      renderComp();
    } else if(activeTab==='gps'){
      renderGpsPms();
    } else if(activeTab==='scrape'){
      renderScrape();
    }
  }

  function pct(v){
    if(v==null || isNaN(v)) return '—';
    return (v*100).toFixed(1)+'%';
  }

  function renderGpsPms(){
    var root = document.getElementById('gpsPmsRoot');
    if(!GPS_PMS){ root.innerHTML = '<div class="empty-msg">GPS + PMS data not loaded</div>'; return; }
    var h = GPS_PMS.headline || {};
    var ub = GPS_PMS.uio_basis || {};
    var integ = GPS_PMS.integrity || {};
    var badge = GPS_PMS.quotable_externally ? 'ok' : 'amber';
    var ieSpu = h.gps_spu_ireland_corrected;
    var ieWallet = h.gps_capture_vs_wallet_ireland;
    var kpis = [
      ['PMS total capture CY2025', pct(h.pms_total_capture_cy2025), h.pms_metric || 'total', 'accent'],
      ['Ireland GPS €/UIO (V20)', ieSpu!=null ? ('€'+Math.round(ieSpu)) : '—', 'UIO '+((ub.ireland_cy2025_uio!=null)?ub.ireland_cy2025_uio:'2,161')+' — pack '+((ub.ireland_pack_uio_rejected!=null)?ub.ireland_pack_uio_rejected:'3,056')+' rejected', ''],
      ['Ireland vs wallet', ieWallet!=null ? pct(ieWallet) : '—', 'GPS sales ÷ V20 wallet (prefer over blended €/UIO)', ''],
      ['Integrity', (integ.score!=null?integ.score:'—')+'/100', integ.band || '', badge==='amber'?'':'']
    ];
    var kpiHtml = '<div class="kpi-grid">'+kpis.map(function(c){
      return '<div class="kpi-card '+c[3]+'"><div class="kpi-label">'+c[0]+'</div><div class="kpi-value">'+c[1]+'</div><div class="kpi-sub">'+c[2]+'</div></div>';
    }).join('')+'</div>';
    var callout = '<div class="notes-card" style="border-left-color:#B45309"><h3>Network lens · UIO V20 overlay</h3><ul>'+
      (GPS_PMS.notes||[]).map(function(n){return '<li>'+n+'</li>';}).join('')+
      '<li><b>UIO basis:</b> '+(ub.rule||'V20 carpark')+' — file <code>'+(ub.file||'')+'</code>.</li>'+
      '<li><b>Provisional:</b> '+(integ.label||'see pricing full analysis pack')+' — deep-link <a href="'+(GPS_PMS.deep_link_gps||'#')+'">GPS dashboard</a>.</li>'+
      '</ul></div>';

    var pms = (GPS_PMS.pms_by_db_cy2025||[]).slice().sort(function(a,b){return a.capture_rate-b.capture_rate;});
    Plotly.newPlot('gpsPmsCaptureChart', [{
      x: pms.map(function(r){return r.capture_rate*100;}),
      y: pms.map(function(r){return r.distributor_code;}),
      type:'bar', orientation:'h',
      marker:{color: pms.map(function(r){return r.basis_breach?'#B45309':'#2a78d6';})},
      hovertemplate:'%{y}: %{x:.1f}%<extra></extra>'
    }], {
      margin:{t:10,r:20,b:30,l:100}, height: Math.max(360, pms.length*18),
      xaxis:{title:'PMS total capture %', tickfont:{size:10}, gridcolor:'#eeeeec'},
      yaxis:{tickfont:{size:9}},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});

    var sc = (GPS_PMS.gps_pms_scatter_cy2025||[]).filter(function(r){return r.pms_total_capture!=null && r.gps_spu_eur!=null;});
    Plotly.newPlot('gpsPmsScatterChart', [{
      x: sc.map(function(r){return r.pms_total_capture*100;}),
      y: sc.map(function(r){return r.gps_spu_eur;}),
      text: sc.map(function(r){return r.db+(r.uio_corrected?' ★':'');}),
      customdata: sc.map(function(r){return [(r.uio_units!=null?Math.round(r.uio_units):'—'), (r.gps_capture_vs_wallet!=null?(r.gps_capture_vs_wallet*100).toFixed(1)+'%':'—'), (r.quality_flags||[]).join(' | ')||'—'];}),
      mode:'markers+text', textposition:'top center',
      marker:{size: sc.map(function(r){return r.uio_corrected?14:10;}), color: sc.map(function(r){
        if(r.db==='UTI'||r.db==='UMI') return '#CC0E1E';
        if(r.uio_corrected) return '#B45309';
        return '#2a78d6';
      })},
      hovertemplate:'%{text}<br>PMS total %{x:.1f}%<br>GPS SPU €%{y:.0f}<br>UIO %{customdata[0]}<br>vs wallet %{customdata[1]}<br>%{customdata[2]}<extra></extra>'
    }], {
      margin:{t:20,r:20,b:50,l:60}, height:400,
      xaxis:{title:'PMS total capture %', gridcolor:'#eeeeec'},
      yaxis:{title:'GPS € / UIO (V20 where overlaid)', gridcolor:'#eeeeec'},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});

    var walletRows = (GPS_PMS.gps_pms_scatter_cy2025||[]).filter(function(r){return r.gps_capture_vs_wallet!=null;})
      .slice().sort(function(a,b){return a.gps_capture_vs_wallet-b.gps_capture_vs_wallet;});
    if(walletRows.length && document.getElementById('gpsPmsWalletChart')){
      Plotly.newPlot('gpsPmsWalletChart', [{
        x: walletRows.map(function(r){return r.gps_capture_vs_wallet*100;}),
        y: walletRows.map(function(r){return r.db;}),
        type:'bar', orientation:'h',
        marker:{color: walletRows.map(function(r){return r.db==='IRELAND'?'#B45309':(r.db==='UTI'||r.db==='UMI'?'#CC0E1E':'#2a78d6');})},
        hovertemplate:'%{y}: %{x:.1f}% of wallet<extra></extra>'
      }], {
        margin:{t:10,r:20,b:30,l:100}, height: Math.max(320, walletRows.length*16),
        xaxis:{title:'GPS sales ÷ V20 wallet %', gridcolor:'#eeeeec'},
        yaxis:{tickfont:{size:9}},
        font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
      }, {displayModeBar:false, responsive:true});
    }

    var tbl = '<div class="tbl-scroll"><table class="data-tbl"><thead><tr><th>DB</th><th>Country</th><th>PMS total</th><th>UIO</th><th>GPS SPU €</th><th>vs wallet</th><th>Flags</th></tr></thead><tbody>'+
      (GPS_PMS.gps_pms_scatter_cy2025||[]).slice().sort(function(a,b){return (b.pms_total_capture||0)-(a.pms_total_capture||0);}).map(function(r){
        var flag = (r.db==='UTI'||r.db==='UMI') ? ' <span class="partial-flag">(Israel — do not blend)</span>' : '';
        if(r.uio_corrected) flag += ' <span class="partial-flag">UIO V20</span>';
        var flags = (r.quality_flags||[]).slice(0,2).join(' · ') || '—';
        var pmsCell = pct(r.pms_total_capture)+(r.pms_total_capture!=null && r.pms_total_capture>1?' <span class="partial-flag">basis breach</span>':'');
        return '<tr><td>'+r.db+flag+'</td><td>'+(r.country||'')+'</td><td>'+pmsCell+'</td><td>'+(r.uio_units!=null?Math.round(r.uio_units):'—')+'</td><td>'+(r.gps_spu_eur!=null?Math.round(r.gps_spu_eur):'—')+'</td><td>'+(r.gps_capture_vs_wallet!=null?pct(r.gps_capture_vs_wallet):'—')+'</td><td style="font-size:10px;max-width:280px">'+flags+'</td></tr>';
      }).join('')+'</tbody></table></div>';

    document.getElementById('gpsPmsKpis').innerHTML = kpiHtml;
    document.getElementById('gpsPmsCallout').innerHTML = callout;
    document.getElementById('gpsPmsTable').innerHTML = tbl;
    gpsRendered = true;
  }

  function renderScrape(){
    if(!SCRAPE){ document.getElementById('scrapeRoot').innerHTML = '<div class="empty-msg">Scrape data not loaded</div>'; return; }
    var k = SCRAPE.kpis || {};
    var story = SCRAPE.story || {};
    var frame = story.frame || {};
    var defs = story.definitions || {};
    var basis = SCRAPE.compare_basis || {};
    var ks = k.ks_gen_vs_am || {};
    var src = SCRAPE.sources || [];
    var link = '../pricing/ISZE_Aftermarket_Live_Pricing_Dashboard.html';
    function tip(d){ if(!d) return ''; return (d.label||'')+'\n'+(d.formula||'')+'\n'+(d.plain||''); }
    function money(v){ if(v==null||isNaN(v)) return '—'; return '€'+Math.round(v).toLocaleString('en-GB'); }

    var kpiHtml = '<div class="kpi-grid">'+[
      ['Median shop / reference', k.median_am_vs_street!=null?k.median_am_vs_street.toFixed(2):'—', tip(defs.price_index)||'shop € ÷ reference customer price', 'accent'],
      ['Sales on undercut list', money(k.exposure_rev_cy2025_eur), 'CY2025 evidence PNs', ''],
      ['Illustrative pressure', money(k.illustrative_price_pressure_eur), tip(defs.price_pressure)||'sales × gap to reference', ''],
      ['KS channel spread', k.ks_channel_spread_median!=null?k.ks_channel_spread_median.toFixed(2):'—', 'genuine − AM vs reference (n='+(ks.n||0)+')', '']
    ].map(function(c){
      return '<div class="kpi-card '+c[3]+'" title="'+(c[2]||'').replace(/"/g,'&quot;')+'"><div class="kpi-label">'+c[0]+'</div><div class="kpi-value">'+c[1]+'</div><div class="kpi-sub">'+String(c[2]).split('\n')[0]+'</div></div>';
    }).join('')+'</div>';

    var caveatsHtml =
      '<p style="margin:0 0 10px"><a href="'+link+'"><b>Open full aftermarket briefing →</b></a></p>'+
      (frame.track?('<p style="margin:0 0 6px"><b>What we track:</b> '+frame.track+'</p>'):'')+
      (frame.good?('<p style="margin:0 0 6px"><b>What good looks like:</b> '+frame.good+'</p>'):'')+
      (frame.not_this?('<p style="margin:0 0 8px"><b>What this is not:</b> '+frame.not_this+'</p>'):'')+
      '<p style="margin:0 0 8px"><b>'+(story.headline||'')+'</b></p>'+
      '<ul>'+(story.bullets||[]).slice(0,3).map(function(c){return '<li>'+c+'</li>';}).join('')+'</ul>'+
      '<p class="note" style="margin-top:10px">'+(frame.margin_plain||'Reference customer price = ISZE list → +40% distributor → +27.5% dealer.')+'</p>';

    Plotly.newPlot('scrapeFillChart', [{
      x: src.map(function(r){return r.source;}),
      y: src.map(function(r){return (r.fill_rate_real||0)*100;}),
      type:'bar',
      marker:{color: src.map(function(r){return (r.placeholders_dropped||0)>0?'#B45309':'#eb6834';})},
      hovertemplate:'%{x}<br>real hit rate %{y:.1f}%<extra></extra>'
    }], {
      margin:{t:10,r:10,b:80,l:50}, height:300,
      yaxis:{title:'Real hit rate %', gridcolor:'#eeeeec'},
      xaxis:{tickangle:-25, tickfont:{size:10}}
    }, {displayModeBar:false, responsive:true});

    var heat = SCRAPE.category_heat || [];
    var MIN_N = (basis.min_n_family!=null)?basis.min_n_family:3;
    if(heat.length && document.getElementById('scrapeHeatChart')){
      Plotly.newPlot('scrapeHeatChart', [{
        x: heat.map(function(r){return r.median_street_index;}),
        y: heat.map(function(r){return r.aim_category+' (n='+r.n+')'+(r.n<MIN_N?' · directional':'');}),
        type:'bar', orientation:'h',
        marker:{color: heat.map(function(r){
          if(r.n<MIN_N) return '#D4D4D8';
          var i=r.median_street_index||1; return i<0.5?'#CC0E1E':(i<1?'#B45309':'#5A5A5A');
        })},
        hovertemplate:'%{y}<br>Median %{x:.2f} = shop ÷ reference customer price<extra></extra>'
      }], {
        margin:{t:10,r:20,b:40,l:180}, height: Math.max(260, heat.length*26),
        xaxis:{title:'Median shop / reference', range:[0, Math.max(1.2, Math.max.apply(null, heat.map(function(r){return r.median_street_index||0;}))*1.1)], gridcolor:'#eeeeec'},
        shapes:[{type:'line', x0:1, x1:1, y0:-0.5, y1:heat.length-0.5, line:{color:'#999', dash:'dot'}}]
      }, {displayModeBar:false, responsive:true});
    }

    document.getElementById('scrapeKpis').innerHTML = kpiHtml;
    document.getElementById('scrapeCaveats').innerHTML = caveatsHtml;
    document.getElementById('scrapeSources').innerHTML = '<div class="note">Full briefing (Block-0 frame + charts) → <a href="'+link+'">Aftermarket Live Pricing</a>. Explorer needs <code>OPEN_PartGroups_Explorer.cmd</code> then http://127.0.0.1:8766/</div>';
    var und = document.getElementById('scrapeUndercuts'); if(und) und.innerHTML = '';
    var exp = document.getElementById('scrapeExposure'); if(exp) exp.innerHTML = '';
    var gen = document.getElementById('scrapeGenAm'); if(gen) gen.innerHTML = '';
    scrapeRendered = true;
  }

  function showTab(tab){
    activeTab = tab;
    Array.prototype.forEach.call(document.querySelectorAll('.tab-btn'), function(b){
      b.classList.toggle('active', b.dataset.tab===tab);
    });
    Array.prototype.forEach.call(document.querySelectorAll('.tab-panel'), function(p){
      p.classList.toggle('active', p.dataset.tab===tab);
    });
    // filters apply to sales + competitive
    document.getElementById('filterBar').style.display = (tab==='sales'||tab==='competitive') ? '' : 'none';
    document.getElementById('kpiGrid').style.display = (tab==='sales') ? '' : 'none';
    renderAll();
  }"""
    if old_render_all not in js:
        raise SystemExit("renderAll block not found")
    js = js.replace(old_render_all, new_render_all)

    old_tail = """  document.getElementById('grainToggle').querySelector('button[data-g="quarter"]').classList.add('active');
  renderNotes();
  renderAll();
})();"""
    new_tail = """  document.getElementById('grainToggle').querySelector('button[data-g="quarter"]').classList.add('active');

  document.getElementById('tabBar').addEventListener('click', function(e){
    var b = e.target.closest('.tab-btn'); if(!b) return;
    showTab(b.dataset.tab);
  });

  Promise.all([
    loadJson('partgroups_agg.json'),
    loadJson('partgroups_competitive.json'),
    loadJson('partgroups_meta.json'),
    loadJson('partgroups_gps_pms.json'),
    loadJson('partgroups_scrape.json')
  ]).then(function(arr){
    AGG = parseCompactObj(arr[0]);
    COMPETITIVE = parseCompactObj(arr[1]);
    META = arr[2];
    GPS_PMS = arr[3];
    SCRAPE = arr[4];

    // rebuild catalogs that depended on AGG at boot
    dbTotals = sumBy(AGG, function(r){return r.db_code;}, function(r){return r.net_eur;});
    dbList = Object.keys(dbTotals).sort(function(a,b){return dbTotals[b]-dbTotals[a];});
    l1Totals = sumBy(AGG, function(r){return r.aim_l1;}, function(r){return r.net_eur;});
    l1List = Object.keys(l1Totals).sort(function(a,b){return l1Totals[b]-l1Totals[a];});
    l1l2Map = {};
    AGG.forEach(function(r){
      if(!l1l2Map[r.aim_l1]) l1l2Map[r.aim_l1] = {};
      l1l2Map[r.aim_l1][r.aim_l2] = (l1l2Map[r.aim_l1][r.aim_l2]||0) + r.net_eur;
    });
    dbColor = {};
    dbList.slice(0,8).forEach(function(db,i){ dbColor[db]=PAL[i]; });
    state.dbs = new Set(dbList.slice(0,6));
    DATA_MIN_YM = META.date_min.slice(0,7);
    DATA_MAX_YM = META.date_max.slice(0,7);

    document.getElementById('stampDate').textContent = META.date_max;
    document.getElementById('topMeta').innerHTML = META.date_min + ' → ' + META.date_max + ' &middot; ' +
      META.db_codes_present.length + ' distributors &middot; GPS-eligible net sales';
    document.getElementById('loadBanner').style.display = 'none';
    renderNotes();
    showTab('sales');
  }).catch(function(err){
    document.getElementById('loadBanner').innerHTML = '<b>Could not load data.</b> '+String(err.message||err)+
      '<br><b>Fix:</b> double-click <code>OPEN_PartGroups_Explorer.cmd</code> in this folder (starts HTTP + opens the page). Never open this HTML via file:// — the sales JSON is too large to embed.';
    document.getElementById('loadBanner').style.display = 'block';
  });
})();"""
    if old_tail not in js:
        raise SystemExit("tail block not found")
    js = js.replace(old_tail, new_tail)

    # Move catalog derivation that ran at parse time — it currently still references AGG immediately.
    # We need to change `var dbTotals = sumBy(AGG,...` into late-init placeholders.
    old_derive = """  // ---- derive DB / L1 / L2 catalogs, sorted by total revenue -------------
  function sumBy(rows, keyFn, valFn){
    var m = {};
    rows.forEach(function(r){ var k=keyFn(r); m[k]=(m[k]||0)+valFn(r); });
    return m;
  }
  var dbTotals = sumBy(AGG, function(r){return r.db_code;}, function(r){return r.net_eur;});
  var dbList = Object.keys(dbTotals).sort(function(a,b){return dbTotals[b]-dbTotals[a];});
  var l1Totals = sumBy(AGG, function(r){return r.aim_l1;}, function(r){return r.net_eur;});
  var l1List = Object.keys(l1Totals).sort(function(a,b){return l1Totals[b]-l1Totals[a];});
  var l1l2Map = {};
  AGG.forEach(function(r){
    if(!l1l2Map[r.aim_l1]) l1l2Map[r.aim_l1] = {};
    l1l2Map[r.aim_l1][r.aim_l2] = (l1l2Map[r.aim_l1][r.aim_l2]||0) + r.net_eur;
  });

  var dbColor = {};
  dbList.slice(0,8).forEach(function(db,i){ dbColor[db]=PAL[i]; });

  // ---- state ---------------------------------------------------------------
  var state = {
    l1: 'All',
    l2: 'All',
    grain: 'quarter',
    dbs: new Set(dbList.slice(0,6))
  };"""
    new_derive = """  // ---- derive DB / L1 / L2 catalogs (filled after AGG loads) -------------
  function sumBy(rows, keyFn, valFn){
    var m = {};
    rows.forEach(function(r){ var k=keyFn(r); m[k]=(m[k]||0)+valFn(r); });
    return m;
  }
  var dbTotals = {};
  var dbList = [];
  var l1Totals = {};
  var l1List = [];
  var l1l2Map = {};
  var dbColor = {};

  // ---- state ---------------------------------------------------------------
  var state = {
    l1: 'All',
    l2: 'All',
    grain: 'quarter',
    dbs: new Set()
  };"""
    if old_derive not in js:
        raise SystemExit("derive block not found")
    js = js.replace(old_derive, new_derive)

    # DATA_MIN_YM used META at boot — defer
    old_dates = """  var DATA_MIN_YM = META.date_min.slice(0,7);
  var DATA_MAX_YM = META.date_max.slice(0,7);"""
    new_dates = """  var DATA_MIN_YM = '2023-01';
  var DATA_MAX_YM = '2026-03';"""
    if old_dates not in js:
        raise SystemExit("date block not found")
    js = js.replace(old_dates, new_dates)

    return js


def build_html(app_js: str, css: str) -> str:
    extra_css = """
  .tab-bar { display:flex; gap:0; background:var(--surface); border-bottom:1px solid var(--border); padding:0 28px; }
  .tab-btn { border:none; background:transparent; padding:12px 16px; font-size:12.5px; font-weight:600; color:var(--ink-2); cursor:pointer; font-family:inherit; border-bottom:2px solid transparent; }
  .tab-btn.active { color:var(--brand-red); border-bottom-color:var(--brand-red); }
  .tab-btn:hover { color:var(--ink); }
  .tab-panel { display:none; }
  .tab-panel.active { display:block; }
  .load-banner { display:none; margin:14px 28px; padding:14px 16px; border:1px solid #F0D7B0; background:#FEF8F0; color:#B45309; border-radius:10px; font-size:12.5px; line-height:1.55; }
  .load-banner code { background:#fff; padding:1px 5px; border-radius:4px; }
"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE Part-Groups Sales Explorer</title>
<style>
{css}
{extra_css}
</style>
<script src="_ui/plotly.min.js"></script>
</head>
<body>
<div class="stamp">Data as of <strong id="stampDate">—</strong> &nbsp;·&nbsp; internal tool — verify freshness before sharing externally &nbsp;·&nbsp; shell slimmed (external JSON + shared Plotly)</div>
<div class="top-bar">
  <div>
    <div class="brand"><span class="dot"></span><h1>Part-Groups Sales Explorer</h1></div>
    <div class="crumb">ISZE · Open with <code>OPEN_PartGroups_Explorer.cmd</code> (not double-click HTML) · data in <code>partgroups_data/</code></div>
  </div>
  <div class="meta" id="topMeta">Loading…</div>
</div>
<div id="loadBanner" class="load-banner">Loading data…</div>
<div class="tab-bar" id="tabBar" role="tablist">
  <button type="button" class="tab-btn active" data-tab="sales">Sales</button>
  <button type="button" class="tab-btn" data-tab="competitive">Competitive (Eucon)</button>
  <button type="button" class="tab-btn" data-tab="gps">GPS + PMS</button>
  <button type="button" class="tab-btn" data-tab="scrape">Aftermarket scrape</button>
</div>

<div class="main">
  <div class="kpi-grid" id="kpiGrid"></div>

  <div class="filter-bar" id="filterBar">
    <div class="filter-row">
      <div class="filter-group">
        <label>Part group</label>
        <select id="selL1"></select>
      </div>
      <div class="filter-group">
        <label>Subcategory</label>
        <select id="selL2"></select>
      </div>
      <div class="filter-group">
        <label>Timeline grain</label>
        <div class="grain-toggle" id="grainToggle">
          <button data-g="month">Month</button>
          <button data-g="quarter">Quarter</button>
          <button data-g="fy">FY</button>
          <button data-g="cy">CY</button>
        </div>
      </div>
      <div class="filter-group" style="flex:1;min-width:280px">
        <label>Distributors <span id="dbCountLabel" style="text-transform:none;font-weight:400;color:#999"></span></label>
        <div class="chip-wrap" id="dbChips"></div>
      </div>
      <div class="filter-actions">
        <button class="btn-mini" id="btnAllDb">All DBs</button>
        <button class="btn-mini" id="btnTop6Db">Top 6 DBs</button>
        <button class="btn-mini" id="btnReset">Reset filters</button>
      </div>
    </div>
  </div>

  <div class="tab-panel active" data-tab="sales">
  <div class="grid2">
    <div class="card">
      <h3>Net sales trend <span class="toggle-table" data-target="trendTbl">Table view</span></h3>
      <div class="scope-line" id="scopeTrend"></div>
      <div class="chart-container" id="trendChart"></div>
      <div class="tbl-scroll" id="trendTbl" style="display:none"></div>
      <div class="note">Split by DB shown when ≤8 distributors are selected (color-safe series cap); otherwise shows the combined total. GPS-eligible net sales only — see data notes below.</div>
    </div>
    <div class="card">
      <h3>By distributor <span class="toggle-table" data-target="dbTbl">Table view</span></h3>
      <div class="scope-line" id="scopeDb"></div>
      <div class="chart-container" id="dbChart"></div>
      <div class="tbl-scroll" id="dbTbl" style="display:none"></div>
    </div>
  </div>

  <div class="grid2">
    <div class="card">
      <h3 id="l1ChartTitle">Part groups <span class="toggle-table" data-target="l1Tbl">Table view</span></h3>
      <div class="scope-line" id="scopeL1"></div>
      <div class="chart-container" id="l1Chart"></div>
      <div class="tbl-scroll" id="l1Tbl" style="display:none"></div>
      <div class="note">Click a bar to drill into that part group's subcategories (also settable via the Part group filter above).</div>
    </div>
    <div class="card">
      <h3 id="l2ChartTitle">Subcategories <span class="toggle-table" data-target="l2Tbl">Table view</span></h3>
      <div class="scope-line" id="scopeL2"></div>
      <div class="chart-container" id="l2Chart"></div>
      <div class="tbl-scroll" id="l2Tbl" style="display:none"></div>
    </div>
  </div>

  <div class="grid1">
    <div class="card">
      <h3>Genuine vs BVP mix <span class="toggle-table" data-target="bvpTbl">Table view</span></h3>
      <div class="scope-line" id="scopeBvp"></div>
      <div class="chart-container" id="bvpChart"></div>
      <div style="font-size:11px;color:#666;margin-top:6px" id="bvpCoverageLine"></div>
      <div class="tbl-scroll" id="bvpTbl" style="display:none"></div>
      <div class="note" id="bvpNote">Only Brakes, Filters, Clutch/Driveline, Suspension, Electrical, Cooling and Cab/Misc have a BVP-alternative catalog. Other part groups show as 100% Genuine because ISZE runs no BVP line for them. See the Competitive tab for Eucon price-gap exposure.</div>
    </div>
  </div>

  <div class="grid1">
    <div class="card">
      <h3 id="moversTitle">Top part-number movers</h3>
      <div class="scope-line" id="scopeMovers"></div>
      <div id="moversWrap"></div>
      <div class="note">Ranked by absolute EUR change within the current DB + part-group + subcategory filter. Compares the two most recent <b>complete</b> periods at the timeline grain selected above. Part-number sample loads on demand (~12 MB JSON).</div>
    </div>
  </div>

  <div class="notes-card">
    <h3>Data notes — read before presenting these numbers externally</h3>
    <ul id="notesList"></ul>
  </div>
  </div><!-- /sales -->

  <div class="tab-panel" data-tab="competitive">
    <div class="card">
      <h3>Competitive price-gap exposure <span class="toggle-table" data-target="compTbl">Table view</span></h3>
      <div class="scope-line" id="scopeComp"></div>
      <div class="chart-container" id="compChart"></div>
      <div class="tbl-scroll" id="compTbl" style="display:none"></div>
      <div class="note">Real Eucon-sourced benchmark (<code>01_data/01_Pricing/</code>, priced 2026-08-10/11).
      Genuine OEM peers (DAF, Toyota, Ford) and online IAM brands (Blue Print, Febi Bilstein, Ridex…) via Eucon PartsPool (DE+NO, 29 Mar 2026).
      Correlation to ISZE price ≈ 0.69. <b>Narrow sample — 51 part numbers</b>, mostly Brakes/Filters/Fuel/Intake — internal WIP.
      Bars = % gap vs ISZE street-equivalent; negative (red) = competitor undercuts. Part-group / subcategory filters above apply; DB/timeline filters do not (fixed survey).</div>
    </div>
  </div>

  <div class="tab-panel" data-tab="gps">
    <div id="gpsPmsKpis"></div>
    <div id="gpsPmsCallout"></div>
    <div class="grid2">
      <div class="card">
        <h3>PMS total capture by distributor (CY2025)</h3>
        <div class="chart-container" id="gpsPmsCaptureChart"></div>
        <div class="note">Headline = <b>PMS total</b> capture. Amber bars = expected-qty basis breach (&gt;100%).</div>
      </div>
      <div class="card">
        <h3>PMS total vs GPS €/UIO (V20 overlay)</h3>
        <div class="chart-container" id="gpsPmsScatterChart"></div>
        <div class="note">★ / amber = UIO corrected from V20 carpark. UTI/UMI in red — never blend. Prefer capture-vs-wallet for Ireland.</div>
      </div>
    </div>
    <div class="card">
      <h3>GPS sales ÷ V20 wallet %</h3>
      <div class="chart-container" id="gpsPmsWalletChart"></div>
      <div class="note">Where V20 wallet exists. Ireland highlighted — blended €/UIO mixes CV+LCV so wallet % is the cleaner read.</div>
    </div>
    <div class="card" id="gpsPmsTable"></div>
    <div id="gpsPmsRoot" style="display:none"></div>
  </div>

  <div class="tab-panel" data-tab="scrape">
    <div id="scrapeKpis"></div>
    <div class="notes-card"><h3>Aftermarket vs reference sell-out</h3><div id="scrapeCaveats"></div></div>
    <div class="grid2">
      <div class="card">
        <h3>Feed trust (summary)</h3>
        <div class="chart-container" id="scrapeFillChart"></div>
      </div>
      <div class="card">
        <h3>Part families vs reference (summary)</h3>
        <div class="chart-container" id="scrapeHeatChart"></div>
      </div>
    </div>
    <div class="card"><div id="scrapeSources"></div></div>
    <div id="scrapeUndercuts" style="display:none"></div>
    <div id="scrapeExposure" style="display:none"></div>
    <div id="scrapeGenAm" style="display:none"></div>
    <div id="scrapeRoot" style="display:none"></div>
  </div>

  <div class="footer">ISZE Part-Groups Sales Explorer · sales_fact aggregates + Eucon competitive + network GPS/PMS + live shop scrapes · Internal tool · HTML shell budget &lt;500 KB · Rebuild: python 02_dashboards/sales/_build/build_partgroups_sales_explorer.py</div>
</div>

<script>
{app_js}
</script>
</body>
</html>
"""


def write_readme() -> None:
    README.write_text(
        """# Part-Groups explorer data

Canonical JSON also lives in `01_data/14_dashboards/partgroups_explorer/`.
This folder is the sibling copy fetched by `ISZE_PartGroups_Sales_Explorer.html`.

## Size budget

| File | Role |
|------|------|
| `partgroups_agg.json` | Sales aggregates (~3.7 MB) — first paint |
| `partgroups_pnyear.json` | PN movers / drill (~12 MB) — lazy |
| `partgroups_competitive.json` | Eucon panel (~140 KB) |
| `partgroups_meta.json` | Stamps |
| `partgroups_gps_pms.json` | Network GPS + PMS total |
| `partgroups_scrape.json` | Live shop scrape summary |

HTML shell must stay under ~500 KB (Plotly via local `_ui/plotly.min.js` copy of `02_dashboards/_ui/plotly.min.js`).

## Open

**Always** double-click `OPEN_PartGroups_Explorer.cmd` (starts HTTP on 8766 and opens the page).
Do **not** open `ISZE_PartGroups_Sales_Explorer.html` via Explorer double-click — multi-MB JSON needs HTTP.

Aftermarket Live Pricing (`02_dashboards/pricing/ISZE_Aftermarket_Live_Pricing_Dashboard.html`) is **self-contained** (scrape JSON embedded) — double-click OK.

## Rebuild

```powershell
python 02_dashboards/sales/_build/build_partgroups_sales_explorer.py
```
""",
        encoding="utf-8",
    )


def ensure_plotly_copy() -> None:
    src = ROOT / "02_dashboards" / "_ui" / "plotly.min.js"
    dest_dir = ROOT / "02_dashboards" / "sales" / "_ui"
    dest = dest_dir / "plotly.min.js"
    if not src.exists():
        raise SystemExit(f"missing shared plotly: {src}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    if (not dest.exists()) or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)
        print(f"copied plotly -> {dest}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--from-original",
        action="store_true",
        help="Re-extract JSON/CSS/JS from the Downloads history snapshot",
    )
    ap.add_argument(
        "--gps-scrape-only",
        action="store_true",
        help="Only refresh gps_pms + scrape JSON (no HTML rewrite)",
    )
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)

    if args.from_original:
        if not HISTORY.exists():
            raise SystemExit(f"missing history snapshot: {HISTORY}")
        extract_from_original(HISTORY)

    needed = ["partgroups_agg.json", "partgroups_competitive.json", "partgroups_meta.json"]
    missing = [n for n in needed if not (DATA / n).exists()]
    if missing:
        if HISTORY.exists():
            print("missing", missing, "— extracting from history snapshot")
            extract_from_original(HISTORY)
        else:
            raise SystemExit(f"missing {missing} and no history snapshot")

    build_gps_pms()
    build_scrape()
    sync_sibling()
    from build_aftermarket_live_dashboard import build_aftermarket_live_html

    am = build_aftermarket_live_html()
    print(f"wrote {am} ({am.stat().st_size/1e6:.3f} MB, scrape embedded)")
    ensure_plotly_copy()
    write_readme()
    # launcher for fat explorer (multi-MB JSON) — never rely on “run http.server” chat tips
    launcher = ROOT / "02_dashboards" / "sales" / "OPEN_PartGroups_Explorer.cmd"
    if not launcher.exists():
        print(f"WARNING: missing launcher {launcher}")

    if args.gps_scrape_only:
        print("gps/scrape refreshed; HTML unchanged")
        return

    css = (EXTRACT / "original.css").read_text(encoding="utf-8")
    app_src = (EXTRACT / "original_app.js").read_text(encoding="utf-8")
    app_js = patch_app_js(app_src)
    (EXTRACT / "patched_app.js").write_text(app_js, encoding="utf-8")
    html = build_html(app_js, css)
    OUT_HTML.write_text(html, encoding="utf-8")
    mb = OUT_HTML.stat().st_size / 1e6
    print(f"wrote {OUT_HTML} ({mb:.3f} MB)")
    if mb > 0.5:
        print("WARNING: HTML shell exceeds 0.5 MB budget")
    for p in sorted(SIBLING.glob("partgroups_*.json")):
        print(f"  data {p.name}: {p.stat().st_size/1e6:.3f} MB")


if __name__ == "__main__":
    main()
