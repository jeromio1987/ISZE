(function(){
  'use strict';
  var PAL = ['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300','#4a3aa7','#e34948'];
  var GRAY = '#c3c2b7';

  function parseCompactObj(obj){
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

  // ---- derive DB / L1 / L2 catalogs (filled after AGG loads) -------------
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
  };

  // ---- time bucketing --------------------------------------------------
  function fyOf(ym){ var y=+ym.slice(0,4), m=+ym.slice(5,7); return m>=4 ? 'FY'+(y+1) : 'FY'+y; }
  function qOf(ym){ var y=ym.slice(0,4), m=+ym.slice(5,7); return y+'-Q'+(Math.floor((m-1)/3)+1); }
  function bucketOf(ym, grain){
    if(grain==='month') return ym;
    if(grain==='quarter') return qOf(ym);
    if(grain==='fy') return fyOf(ym);
    return ym.slice(0,4); // cy
  }
  function pad2(n){ return (n<10?'0':'')+n; }
  var DATA_MIN_YM = '2023-01';
  var DATA_MAX_YM = '2026-03';
  // the [startYm, endYm] a bucket label WOULD cover if the period were full --
  // used to detect buckets the data only partially covers (e.g. "FY2023" here
  // is really just Jan-Mar 2023, not a full Apr-Mar fiscal year).
  function bucketMonthRange(bucket, grain){
    if(grain==='month') return [bucket, bucket];
    if(grain==='quarter'){
      var y = +bucket.slice(0,4), q = +bucket.slice(6);
      var startM = (q-1)*3+1;
      return [y+'-'+pad2(startM), y+'-'+pad2(startM+2)];
    }
    if(grain==='fy'){
      var fy = +bucket.slice(2);
      return [(fy-1)+'-04', fy+'-03'];
    }
    return [bucket+'-01', bucket+'-12']; // cy
  }
  function isBucketComplete(bucket, grain){
    var r = bucketMonthRange(bucket, grain);
    return r[0] >= DATA_MIN_YM && r[1] <= DATA_MAX_YM;
  }

  // ---- filtering ---------------------------------------------------------
  function filteredRows(opts){
    opts = opts || {};
    var useL1 = opts.ignoreL1 ? null : state.l1;
    var useL2 = opts.ignoreL2 ? null : state.l2;
    var useDb = opts.ignoreDb ? null : state.dbs;
    return AGG.filter(function(r){
      if(useDb && !useDb.has(r.db_code)) return false;
      if(useL1 && useL1!=='All' && r.aim_l1!==useL1) return false;
      if(useL2 && useL2!=='All' && r.aim_l2!==useL2) return false;
      return true;
    });
  }

  function fmtEur(v){
    var av = Math.abs(v);
    if(av>=1e6) return '€'+(v/1e6).toFixed(2)+'M';
    if(av>=1e3) return '€'+(v/1e3).toFixed(0)+'K';
    return '€'+v.toFixed(0);
  }
  function fmtEurFull(v){ return '€'+Math.round(v).toLocaleString('en-GB'); }

  // Every chart card gets this line so it's self-explanatory on its own --
  // which DBs, which category, which time window -- without needing to
  // scroll back up to the filter bar (or read a screenshot out of context).
  var GRAIN_LABEL = {month:'by month', quarter:'by quarter', fy:'by fiscal year (Apr–Mar)', cy:'by calendar year'};
  function scopeCaption(){
    var dbTxt = state.dbs.size===dbList.length ? 'all '+dbList.length+' distributors' : state.dbs.size+' of '+dbList.length+' distributors';
    var catTxt = state.l1==='All' ? 'all part groups' : (state.l2==='All' ? state.l1 : state.l1+' → '+state.l2);
    return '<b>'+dbTxt+'</b> &middot; <b>'+catTxt+'</b> &middot; '+META.date_min+' → '+META.date_max+' ('+GRAIN_LABEL[state.grain]+')';
  }

  // ================= KPI ROW =================
  function renderKPI(){
    var rows = filteredRows();
    var total = rows.reduce(function(s,r){return s+r.net_eur;},0);
    var qty = rows.reduce(function(s,r){return s+r.qty;},0);
    var nDb = new Set(rows.map(function(r){return r.db_code;})).size;
    var nL1 = new Set(rows.map(function(r){return r.aim_l1;})).size;
    var nL2 = new Set(rows.map(function(r){return r.aim_l2;})).size;
    var cards = [
      ['Net sales (filtered)', fmtEur(total), rows.length+' agg. rows', 'accent'],
      ['Units', qty.toLocaleString('en-GB'), 'billed qty', ''],
      ['Distributors in view', nDb, 'of '+dbList.length+' network-wide', ''],
      ['Part groups in view', nL1, 'of '+l1List.length+' AIM L1 categories', ''],
      ['Subcategories in view', nL2, 'AIM L2', ''],
      ['Network clean total', fmtEur(META.clean_eur), (META.excluded_eur/META.gross_eur*100).toFixed(1)+'% excluded from gross', 'good'],
    ];
    document.getElementById('kpiGrid').innerHTML = cards.map(function(c){
      return '<div class="kpi-card '+c[3]+'"><div class="kpi-label">'+c[0]+'</div><div class="kpi-value">'+c[1]+'</div><div class="kpi-sub">'+c[2]+'</div></div>';
    }).join('');
  }

  // ================= FILTER UI =================
  function renderFilterUI(){
    var selL1 = document.getElementById('selL1');
    selL1.innerHTML = '<option value="All">All part groups</option>' + l1List.map(function(l1){
      return '<option value="'+l1+'">'+l1+' ('+fmtEur(l1Totals[l1])+')</option>';
    }).join('');
    selL1.value = state.l1;

    var selL2 = document.getElementById('selL2');
    if(state.l1==='All'){
      selL2.innerHTML = '<option value="All">All subcategories</option>';
      selL2.disabled = true;
    } else {
      selL2.disabled = false;
      var l2s = Object.keys(l1l2Map[state.l1]||{}).sort(function(a,b){return l1l2Map[state.l1][b]-l1l2Map[state.l1][a];});
      selL2.innerHTML = '<option value="All">All subcategories</option>' + l2s.map(function(l2){
        return '<option value="'+l2+'">'+l2+' ('+fmtEur(l1l2Map[state.l1][l2])+')</option>';
      }).join('');
    }
    selL2.value = state.l2;

    document.getElementById('dbChips').innerHTML = dbList.map(function(db){
      var active = state.dbs.has(db);
      return '<span class="chip'+(active?' active':'')+'" data-db="'+db+'" title="'+(META.db_display[db]||db)+'">'+db+'</span>';
    }).join('');
    document.getElementById('dbCountLabel').textContent = '('+state.dbs.size+' of '+dbList.length+' selected)';

    Array.prototype.forEach.call(document.querySelectorAll('#grainToggle button'), function(b){
      b.classList.toggle('active', b.dataset.g===state.grain);
    });
  }

  // ================= TREND CHART =================
  function renderTrend(){
    document.getElementById('scopeTrend').innerHTML = scopeCaption();
    var rows = filteredRows();
    var splitByDb = state.dbs.size<=8 && state.dbs.size>=1;
    var buckets = {};
    rows.forEach(function(r){
      var b = bucketOf(r.ym, state.grain);
      if(!buckets[b]) buckets[b]={};
      var key = splitByDb ? r.db_code : 'Total';
      buckets[b][key] = (buckets[b][key]||0) + r.net_eur;
    });
    var xs = Object.keys(buckets).sort();
    var partial = {};
    xs.forEach(function(x){ partial[x] = !isBucketComplete(x, state.grain); });
    var anyPartial = xs.some(function(x){return partial[x];});
    var tickText = xs.map(function(x){ return partial[x] ? x+' *' : x; });
    var seriesKeys = splitByDb ? dbList.filter(function(d){return state.dbs.has(d);}) : ['Total'];
    var traces = seriesKeys.map(function(k,i){
      var color = splitByDb ? (dbColor[k]||PAL[i%8]) : '#2a78d6';
      return {
        x: xs, y: xs.map(function(x){return (buckets[x]&&buckets[x][k])||0;}),
        type:'scatter', mode:'lines+markers', name: k,
        line:{width:2, color: color},
        marker:{size:7, color:color, symbol: xs.map(function(x){return partial[x] ? 'circle-open' : 'circle';}),
                line:{width: xs.map(function(x){return partial[x] ? 2 : 0;})}},
        hovertemplate: '%{x}'+(anyPartial?'%{customdata}':'')+'<br>'+k+': %{y:,.0f} EUR<extra></extra>',
        customdata: xs.map(function(x){return partial[x] ? ' (partial period)' : '';})
      };
    });
    // shade the partial buckets so the eye catches them before reading labels
    var shapes = xs.map(function(x,i){
      if(!partial[x]) return null;
      return {type:'rect', xref:'x', yref:'paper', x0:i-0.5, x1:i+0.5, y0:0, y1:1,
              fillcolor:'#eda100', opacity:0.07, line:{width:0}};
    }).filter(Boolean);
    Plotly.newPlot('trendChart', traces, {
      margin:{t:10,r:10,b:40,l:60}, height:340,
      xaxis:{title:'', tickfont:{size:10}, gridcolor:'#eeeeec', type:'category', tickmode:'array', tickvals:xs, ticktext:tickText},
      yaxis:{title:'EUR', tickfont:{size:10}, gridcolor:'#eeeeec', tickformat:',.0f'},
      legend:{orientation:'h', y:-0.25, font:{size:10}},
      hovermode:'x unified', shapes: shapes,
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});

    var existingFlag = document.getElementById('trendPartialFlag');
    if(existingFlag) existingFlag.remove();
    if(anyPartial){
      var flagDiv = document.createElement('div');
      flagDiv.id = 'trendPartialFlag';
      flagDiv.className = 'partial-flag';
      flagDiv.style.marginTop = '8px';
      flagDiv.style.fontSize = '11px';
      flagDiv.textContent = '* period only partially covered by the data (shaded on the chart) — not a real trend point, don\'t read it as one.';
      document.getElementById('trendChart').insertAdjacentElement('afterend', flagDiv);
    }

    var tbl = '<table class="data-tbl"><thead><tr><th>Period</th>'+seriesKeys.map(function(k){return '<th>'+k+'</th>';}).join('')+'</tr></thead><tbody>'+
      xs.map(function(x){
        return '<tr><td>'+x+(partial[x]?' <span class="partial-flag">(partial)</span>':'')+'</td>'+seriesKeys.map(function(k){return '<td>'+fmtEurFull((buckets[x]&&buckets[x][k])||0)+'</td>';}).join('')+'</tr>';
      }).join('') + '</tbody></table>';
    document.getElementById('trendTbl').innerHTML = tbl;
  }

  // ================= DB COMPARISON BAR =================
  function renderDbChart(){
    document.getElementById('scopeDb').innerHTML = 'Highlighted = selected distributors &middot; <b>'+
      (state.l1==='All' ? 'all part groups' : (state.l2==='All' ? state.l1 : state.l1+' → '+state.l2))+'</b> &middot; total across '+
      META.date_min+' → '+META.date_max+' (all distributors shown for context, not just the ones selected above)';
    var rows = filteredRows({ignoreDb:true});
    var byDb = {};
    rows.forEach(function(r){ if(state.dbs.has(r.db_code) || state.dbs.size===dbList.length) byDb[r.db_code]=(byDb[r.db_code]||0)+r.net_eur; });
    // show all DBs regardless of chip selection here so users see where they stand vs network
    byDb = {};
    rows.forEach(function(r){ byDb[r.db_code]=(byDb[r.db_code]||0)+r.net_eur; });
    var ks = Object.keys(byDb).sort(function(a,b){return byDb[a]-byDb[b];});
    var colors = ks.map(function(k){ return state.dbs.has(k) ? '#2a78d6' : '#c3c2b7'; });
    Plotly.newPlot('dbChart', [{
      x: ks.map(function(k){return byDb[k];}), y: ks, type:'bar', orientation:'h',
      marker:{color:colors}, hovertemplate:'%{y}: %{x:,.0f} EUR<extra></extra>'
    }], {
      margin:{t:10,r:20,b:30,l:90}, height: Math.max(340, ks.length*16),
      xaxis:{title:'EUR', tickfont:{size:10}, gridcolor:'#eeeeec'},
      yaxis:{tickfont:{size:9}},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});
    document.getElementById('dbTbl').innerHTML = '<table class="data-tbl"><thead><tr><th>Distributor</th><th>Net EUR</th></tr></thead><tbody>'+
      ks.slice().reverse().map(function(k){return '<tr><td>'+(META.db_display[k]||k)+'</td><td>'+fmtEurFull(byDb[k])+'</td></tr>';}).join('')+'</tbody></table>';
  }

  // ================= L1 / L2 BREAKDOWN =================
  function renderL1L2(){
    var showingL1 = state.l1==='All';
    document.getElementById('l1ChartTitle').innerHTML = (showingL1?'Part groups':'Subcategories of '+state.l1) + ' <span class="toggle-table" data-target="l1Tbl">Table view</span>';
    var scopeTxt = (state.dbs.size===dbList.length?'all '+dbList.length:state.dbs.size+' of '+dbList.length)+' distributors selected'+
      ' &middot; total across '+META.date_min+' → '+META.date_max+' (not broken out by period — bar = whole-window total)';
    document.getElementById('scopeL1').innerHTML = scopeTxt;
    document.getElementById('scopeL2').innerHTML = scopeTxt;
    var rowsForL1 = filteredRows({ignoreL1:true, ignoreL2:true});
    var byKey = {};
    rowsForL1.forEach(function(r){
      var k = showingL1 ? r.aim_l1 : r.aim_l2;
      if(!showingL1 && r.aim_l1!==state.l1) return;
      byKey[k]=(byKey[k]||0)+r.net_eur;
    });
    var ks = Object.keys(byKey).sort(function(a,b){return byKey[b]-byKey[a];}).slice(0,15);
    Plotly.newPlot('l1Chart', [{
      x: ks, y: ks.map(function(k){return byKey[k];}), type:'bar',
      marker:{color:'#eb6834'}, hovertemplate:'%{x}: %{y:,.0f} EUR<extra></extra>'
    }], {
      margin:{t:10,r:10,b:110,l:60}, height:340,
      xaxis:{tickfont:{size:9}, tickangle:-40},
      yaxis:{title:'EUR', tickfont:{size:10}, gridcolor:'#eeeeec'},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});
    document.getElementById('l1Tbl').innerHTML = '<table class="data-tbl"><thead><tr><th>'+(showingL1?'Part group':'Subcategory')+'</th><th>Net EUR</th></tr></thead><tbody>'+
      ks.map(function(k){return '<tr><td>'+k+'</td><td>'+fmtEurFull(byKey[k])+'</td></tr>';}).join('')+'</tbody></table>';

    if(state.l1==='All'){
      // second chart: top subcategories network-wide
      document.getElementById('l2ChartTitle').innerHTML = 'Top subcategories (network-wide) <span class="toggle-table" data-target="l2Tbl">Table view</span>';
      var rows2 = filteredRows({ignoreL2:true});
      var byL2 = {};
      rows2.forEach(function(r){ byL2[r.aim_l2]=(byL2[r.aim_l2]||0)+r.net_eur; });
      var ks2 = Object.keys(byL2).sort(function(a,b){return byL2[b]-byL2[a];}).slice(0,15);
      Plotly.newPlot('l2Chart', [{
        x: ks2, y: ks2.map(function(k){return byL2[k];}), type:'bar',
        marker:{color:'#1baf7a'}, hovertemplate:'%{x}: %{y:,.0f} EUR<extra></extra>'
      }], {
        margin:{t:10,r:10,b:110,l:60}, height:340,
        xaxis:{tickfont:{size:9}, tickangle:-40},
        yaxis:{title:'EUR', tickfont:{size:10}, gridcolor:'#eeeeec'},
        font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
      }, {displayModeBar:false, responsive:true});
      document.getElementById('l2Tbl').innerHTML = '<table class="data-tbl"><thead><tr><th>Subcategory</th><th>Net EUR</th></tr></thead><tbody>'+
        ks2.map(function(k){return '<tr><td>'+k+'</td><td>'+fmtEurFull(byL2[k])+'</td></tr>';}).join('')+'</tbody></table>';
      return;
    }
    // a specific part group is selected: the first chart already shows its
    // subcategories, so use the second panel for top part numbers instead
    // of repeating the same bars (2024+2025 combined, current DB/L2 filter).
    document.getElementById('l2ChartTitle').innerHTML = 'Top part numbers in '+state.l1+' <span class="toggle-table" data-target="l2Tbl">Table view</span>';
    document.getElementById('l2Chart').innerHTML = '<div class="empty-msg">Loading part-number sample…</div>';
    ensurePnyear().then(function(){ renderL1L2Pn(); }).catch(function(err){
      document.getElementById('l2Chart').innerHTML = '<div class="empty-msg">'+String(err.message||err)+'</div>';
    });
    return;
  }
  function renderL1L2Pn(){
    var pnRows = PNYEAR.filter(function(r){
      if(!state.dbs.has(r.db_code)) return false;
      if(r.aim_l1!==state.l1) return false;
      if(state.l2!=='All' && r.aim_l2!==state.l2) return false;
      return true;
    });
    var byPn2 = {};
    pnRows.forEach(function(r){
      var k = r.part_number, label = r.description || r.part_number;
      if(!byPn2[k]) byPn2[k] = {label:label, total:0};
      byPn2[k].total += r.net_sales_value;
    });
    var pnKeys = Object.keys(byPn2).sort(function(a,b){return byPn2[b].total-byPn2[a].total;}).slice(0,15);
    Plotly.newPlot('l2Chart', [{
      x: pnKeys.map(function(k){return byPn2[k].label;}), y: pnKeys.map(function(k){return byPn2[k].total;}), type:'bar',
      marker:{color:'#1baf7a'}, hovertemplate:'%{x}: %{y:,.0f} EUR<extra></extra>'
    }], {
      margin:{t:10,r:10,b:110,l:60}, height:340,
      xaxis:{tickfont:{size:9}, tickangle:-40},
      yaxis:{title:'EUR (CY24+CY25)', tickfont:{size:10}, gridcolor:'#eeeeec'},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});
    document.getElementById('l2Tbl').innerHTML = '<table class="data-tbl"><thead><tr><th>Part</th><th>Net EUR (CY24+CY25)</th></tr></thead><tbody>'+
      pnKeys.map(function(k){return '<tr><td>'+byPn2[k].label+'</td><td>'+fmtEurFull(byPn2[k].total)+'</td></tr>';}).join('')+'</tbody></table>';
    if(pnKeys.length===0) document.getElementById('l2Chart').innerHTML = '<div class="empty-msg">No part-number sample kept for this DB/category combination (only the top ~40 by revenue per DB×part-group are retained network-wide to keep the file size sane).</div>';
  }

  // ================= BVP vs GENUINE =================
  function renderBvp(){
    document.getElementById('scopeBvp').innerHTML = scopeCaption();
    var rows = filteredRows();
    var bvp = rows.reduce(function(s,r){return s+r.bvp_eur;},0);
    var gen = rows.reduce(function(s,r){return s+r.genuine_catalog_eur;},0);
    var total = rows.reduce(function(s,r){return s+r.net_eur;},0);
    var catalogued = bvp + gen;
    var coveragePct = total>0 ? (catalogued/total*100) : 0;
    var hasBvpProgram = catalogued > 0.02*total;
    document.getElementById('bvpCoverageLine').textContent = '';
    if(!hasBvpProgram){
      document.getElementById('bvpChart').innerHTML = '<div class="empty-msg">No meaningful BVP-catalog coverage for this selection ('+coveragePct.toFixed(1)+'% of net sales) — ISZE does not run a Best-Value-Parts alternative here.<br>Net sales shown are effectively 100% Genuine / non-BVP-eligible.</div>';
      document.getElementById('bvpTbl').innerHTML = '';
      return;
    }
    // Chart the split WITHIN the BVP-eligible catalogue only -- mixing in the
    // "not catalogued" volume (which dominates for most categories) swamps
    // the one thing this chart exists to show. Coverage is called out as text.
    var bvpShare = catalogued>0 ? (bvp/catalogued*100) : 0;
    var genShare = 100 - bvpShare;
    Plotly.newPlot('bvpChart', [{
      y:['Within BVP catalog'], x:[gen], name:'Genuine', type:'bar', orientation:'h', marker:{color:'#2a78d6'},
      hovertemplate:'Genuine: %{x:,.0f} EUR ('+genShare.toFixed(1)+'%)<extra></extra>'
    },{
      y:['Within BVP catalog'], x:[bvp], name:'BVP', type:'bar', orientation:'h', marker:{color:'#eda100'},
      hovertemplate:'BVP: %{x:,.0f} EUR ('+bvpShare.toFixed(1)+'%)<extra></extra>'
    }], {
      barmode:'stack', margin:{t:10,r:10,b:40,l:110}, height:160,
      xaxis:{title:'EUR (BVP-catalogued only)', tickfont:{size:10}, gridcolor:'#eeeeec'},
      legend:{orientation:'h', y:-0.3, font:{size:10}},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});
    document.getElementById('bvpCoverageLine').textContent = fmtEurFull(catalogued)+' of '+fmtEurFull(total)+
      ' net sales in this selection ('+coveragePct.toFixed(1)+'%) sits in a BVP-eligible part group; the rest has no BVP alternative.';
    document.getElementById('bvpTbl').innerHTML = '<table class="data-tbl"><tbody>'+
      '<tr><td>Genuine (within catalog)</td><td>'+fmtEurFull(gen)+' ('+genShare.toFixed(1)+'%)</td></tr>'+
      '<tr><td>BVP</td><td>'+fmtEurFull(bvp)+' ('+bvpShare.toFixed(1)+'%)</td></tr>'+
      '<tr><td>Not BVP-eligible (other part groups)</td><td>'+fmtEurFull(total-catalogued)+'</td></tr>'+
      '</tbody></table>';
  }

  // ================= COMPETITIVE PRICE-GAP (real Eucon-sourced data) =====
  function renderComp(){
    var rows = COMPETITIVE.filter(function(r){
      if(state.l1!=='All' && r.aim_l1!==state.l1) return false;
      if(state.l2!=='All' && r.aim_l2!==state.l2) return false;
      return true;
    });
    var nPn = new Set(rows.map(function(r){return r.part_number;})).size;
    document.getElementById('scopeComp').innerHTML = '<b>'+rows.length+' comparisons</b> across <b>'+nPn+' part numbers</b> &middot; '+
      (state.l1==='All' ? 'all categories with a sample' : state.l1) + ' &middot; not affected by the DB/timeline filters above (this is a fixed price survey, not a sales time series)';
    if(rows.length===0){
      document.getElementById('compChart').innerHTML = '<div class="empty-msg">No priced comparison sample for '+
        (state.l2!=='All'?state.l2:state.l1)+' yet. Sampled categories: '+
        Array.from(new Set(COMPETITIVE.map(function(r){return r.aim_l1;}))).sort().join(', ')+'.</div>';
      document.getElementById('compTbl').innerHTML = '';
      return;
    }
    // A competitor priced under 15% of ISZE's price is almost never a real
    // like-for-like match at this level (e.g. a full turbocharger assembly
    // matched to a €29 "Ajusa" price -- Ajusa sells gasket/seal kits, not
    // turbos). Flag rather than silently rank these as if they were normal
    // findings -- same principle as the original AutoDoc file's failure,
    // just narrower: a real data source can still contain bad individual
    // matches, so don't launder them into a confident-looking chart.
    var UNVERIFIED_THRESHOLD = -85;
    // Collapse to one bar per (part, competitor) -- Plotly silently SUMS bars
    // that share an identical categorical y-label (e.g. the same PN vs the
    // same brand surveyed in both DE and NO), which would otherwise inflate
    // a genuine -98% gap into a rendered -1200%+. Average across markets
    // instead; full per-market detail stays in the table below.
    var byPair = {};
    rows.forEach(function(r){
      var k = r.part_number+'|'+r.competitor_name;
      if(!byPair[k]) byPair[k] = {description:r.description, part_number:r.part_number, competitor_name:r.competitor_name,
        competitor_type:r.competitor_type, markets:[], gaps:[], isze:[], comp:[]};
      byPair[k].markets.push(r.market); byPair[k].gaps.push(r.pct_gap);
      byPair[k].isze.push(r.isze_price_eur); byPair[k].comp.push(r.competitor_price_eur);
    });
    function avg(a){ return a.reduce(function(s,v){return s+v;},0)/a.length; }
    var pairs = Object.keys(byPair).map(function(k){
      var o = byPair[k];
      return {description:o.description, part_number:o.part_number, competitor_name:o.competitor_name,
        competitor_type:o.competitor_type, market:Array.from(new Set(o.markets)).join('/'),
        pct_gap: avg(o.gaps), isze_price_eur: avg(o.isze), competitor_price_eur: avg(o.comp), n: o.gaps.length};
    });
    var sorted = pairs.slice().sort(function(a,b){return a.pct_gap-b.pct_gap;}).slice(0,25);
    var labels = sorted.map(function(r){return (r.pct_gap<UNVERIFIED_THRESHOLD?'⚠ ':'')+(r.description||r.part_number)+' vs '+r.competitor_name+(r.n>1?' ('+r.n+')':'');});
    var colors = sorted.map(function(r){
      if(r.pct_gap<UNVERIFIED_THRESHOLD) return '#c3c2b7';
      return r.pct_gap<-15 ? '#d03b3b' : (r.pct_gap<0 ? '#eda100' : '#0ca30c');
    });
    var nFlagged = rows.filter(function(r){return r.pct_gap<UNVERIFIED_THRESHOLD;}).length;
    Plotly.newPlot('compChart', [{
      x: sorted.map(function(r){return r.pct_gap;}), y: labels, type:'bar', orientation:'h',
      marker:{color:colors},
      customdata: sorted.map(function(r){return [r.competitor_type, r.market, r.isze_price_eur, r.competitor_price_eur];}),
      hovertemplate: '%{y}<br>%{customdata[0]} &middot; %{customdata[1]}<br>ISZE €%{customdata[2]} vs competitor €%{customdata[3]}<br>Gap: %{x:.1f}%<extra></extra>'
    }], {
      margin:{t:10,r:20,b:30,l:260}, height: Math.max(340, sorted.length*20),
      xaxis:{title:'% gap vs ISZE (negative = competitor cheaper)', tickfont:{size:10}, gridcolor:'#eeeeec', zeroline:true, zerolinecolor:'#c3c2b7'},
      yaxis:{tickfont:{size:9}},
      font:{family:'-apple-system, Segoe UI, system-ui, sans-serif', size:11}
    }, {displayModeBar:false, responsive:true});
    var existingWarn = document.getElementById('compUnverifiedFlag');
    if(existingWarn) existingWarn.remove();
    if(nFlagged>0){
      var w = document.createElement('div');
      w.id = 'compUnverifiedFlag';
      w.className = 'partial-flag';
      w.style.marginTop = '8px';
      w.style.fontSize = '11px';
      w.textContent = '⚠ '+nFlagged+' comparison(s) shown in gray at competitor price < 15% of ISZE\'s — implausible for the product type (e.g. a full assembly matched to a gasket-kit brand). Treat as an unverified match, not a real price finding, until confirmed against the actual competitor listing.';
      document.getElementById('compChart').insertAdjacentElement('afterend', w);
    }
    document.getElementById('compTbl').innerHTML = '<table class="data-tbl"><thead><tr><th>Part</th><th>Type</th><th>Competitor</th><th>Market</th><th>ISZE €</th><th>Competitor €</th><th>Gap %</th></tr></thead><tbody>'+
      rows.slice().sort(function(a,b){return a.pct_gap-b.pct_gap;}).map(function(r){
        var cls = r.pct_gap<0 ? 'num-neg' : 'num-pos';
        var flag = r.pct_gap<UNVERIFIED_THRESHOLD ? ' ⚠' : '';
        return '<tr><td>'+(r.description||r.part_number)+flag+'</td><td>'+r.competitor_type+'</td><td>'+r.competitor_name+'</td><td>'+r.market+'</td><td>'+r.isze_price_eur.toFixed(2)+'</td><td>'+r.competitor_price_eur.toFixed(2)+'</td><td class="'+cls+'">'+r.pct_gap.toFixed(1)+'%</td></tr>';
      }).join('')+'</tbody></table>';
  }

  // ================= TOP MOVERS =================
  function renderMovers(){
    document.getElementById('moversWrap').innerHTML = '<div class="empty-msg">Loading part-number sample…</div>';
    ensurePnyear().then(function(){ renderMoversInner(); }).catch(function(err){
      document.getElementById('moversWrap').innerHTML = '<div class="empty-msg">'+String(err.message||err)+'</div>';
    });
  }
  function renderMoversInner(){
    var rows = PNYEAR.filter(function(r){
      if(!state.dbs.has(r.db_code)) return false;
      if(state.l1!=='All' && r.aim_l1!==state.l1) return false;
      if(state.l2!=='All' && r.aim_l2!==state.l2) return false;
      return true;
    });
    // bucket at the SAME grain selected in the timeline toggle up top, then
    // compare the two most recent buckets that are actually complete --
    // comparing into a partial period (e.g. CY2026 here) would read as a
    // fake collapse that's really just "the period isn't over yet".
    var bucketSet = {};
    rows.forEach(function(r){ bucketSet[bucketOf(r.ym, state.grain)] = true; });
    var completeBuckets = Object.keys(bucketSet).filter(function(b){ return isBucketComplete(b, state.grain); }).sort();
    if(completeBuckets.length < 2){
      document.getElementById('moversTitle').textContent = 'Top part-number movers';
      document.getElementById('scopeMovers').innerHTML = 'Not enough complete '+GRAIN_LABEL[state.grain]+' periods in this filter to compare — pick a coarser grain (e.g. FY or CY) or widen the filter.';
      document.getElementById('moversWrap').innerHTML = '';
      return;
    }
    var periodB = completeBuckets[completeBuckets.length-1]; // most recent complete
    var periodA = completeBuckets[completeBuckets.length-2]; // one before it
    document.getElementById('moversTitle').textContent = 'Top part-number movers, '+periodA+' → '+periodB;
    document.getElementById('scopeMovers').innerHTML = scopeCaption() + ' &middot; comparing the two most recent complete periods at this grain';

    var byPn = {};
    rows.forEach(function(r){
      var b = bucketOf(r.ym, state.grain);
      if(b!==periodA && b!==periodB) return;
      var k = r.db_code+'|'+r.part_number;
      if(!byPn[k]) byPn[k] = {db:r.db_code, pn:r.part_number, desc:r.description, a:0, b:0};
      if(b===periodA) byPn[k].a += r.net_sales_value;
      if(b===periodB) byPn[k].b += r.net_sales_value;
    });
    var list = Object.keys(byPn).map(function(k){
      var o = byPn[k]; o.delta = o.b - o.a; return o;
    });
    var gainers = list.filter(function(o){return o.delta>0;}).sort(function(a,b){return b.delta-a.delta;}).slice(0,12);
    var losers = list.filter(function(o){return o.delta<0;}).sort(function(a,b){return a.delta-b.delta;}).slice(0,12);
    function tbl(title, arr){
      if(arr.length===0) return '<div><h4 style="font-size:11px;margin-bottom:6px">'+title+'</h4><div class="empty-msg" style="padding:16px">None in this filter</div></div>';
      return '<div><h4 style="font-size:11px;margin-bottom:6px">'+title+'</h4><div class="tbl-scroll" style="max-height:340px"><table class="data-tbl"><thead><tr><th>DB</th><th>Part</th><th>'+periodA+'</th><th>'+periodB+'</th><th>Δ</th></tr></thead><tbody>'+
        arr.map(function(o){
          var cls = o.delta>=0?'num-pos':'num-neg';
          return '<tr><td>'+o.db+'</td><td>'+(o.desc||o.pn)+'</td><td>'+fmtEurFull(o.a)+'</td><td>'+fmtEurFull(o.b)+'</td><td class="'+cls+'">'+(o.delta>=0?'+':'')+fmtEurFull(o.delta)+'</td></tr>';
        }).join('')+'</tbody></table></div></div>';
    }
    document.getElementById('moversWrap').innerHTML = '<div class="grid2">'+tbl('Top gainers', gainers)+tbl('Top losers', losers)+'</div>';
  }

  // ================= NOTES =================
  function renderNotes(){
    var pct = (META.excluded_eur/META.gross_eur*100).toFixed(1);
    var notes = [
      '<b>Exclusions applied</b> (GPS-eligible basis): SaTy limited to SOR/VOR/RUSH/PRD/SVOR/DR (CR, RE, ZDR, FD dropped); TRANSPORT, REBATE, SERVICE, LATE PAYMENT INTEREST and DEMURRAGE description lines dropped; Shell Rimula lubricant material codes (55004*/55007*) dropped. Total excluded: '+fmtEurFull(META.excluded_eur)+' of '+fmtEurFull(META.gross_eur)+' gross ('+pct+'%).',
      '<b>Israel is two distributors, not one.</b> UMI (LCV) and UTI (CV/trucks) share a SAP payer code in the raw export; this dashboard splits them correctly using the “Sold-to pt” field, per the repo rule to never blend UTI+UMI. Shown as two separate rows throughout.',
      '<b>Coverage:</b> '+META.date_min+' to '+META.date_max+'. At FY grain, <b>FY2023 is only Jan–Mar 2023</b> (a quarter, not a full Apr–Mar year) and <b>CY2026 is only Jan–Mar</b> at CY grain — both are flagged with a "*" and shaded wherever they appear on the trend chart, and skipped by the top-movers comparison so a partial period never gets compared against a full one.',
      '<b>BVP catalog coverage is partial by design.</b> Only Brakes, Filters, Clutch/Driveline, Suspension, Electrical, Cooling and Cab/Misc have a BVP-alternative catalog. Body Exterior and most other groups show ~100% "Genuine" because no BVP line exists for them. The competitive price-gap panel is the closest read for those groups, but its sample is narrow (see below).',
      '<b>Competitive price-gap panel replaced with real data.</b> The original <code>competitiveness_autodoc_risk.csv</code> failed a sanity check (93% duplicate placeholder price, ~0 correlation to ISZE price) and was dropped. In its place: two genuinely priced sources from the <code>isze_pricing</code> programme (<code>01_data/01_Pricing/</code>, priced 2026-08-10/11) — ISZE vs genuine OEM peer parts (DAF/Toyota/Ford, Eucon price survey) and ISZE vs online IAM aftermarket brands (Blue Print, Febi Bilstein etc., Eucon PartsPool, Germany+Norway). Correlation to ISZE price: 0.69 (real). <b>Sample is narrow — 51 part numbers</b>, concentrated in Brakes/Filters/Fuel/Intake, explicitly a internal work-in-progress per its own status notes (many vehicle-platform gaps intentionally left blank rather than guessed at). Don\'t read silence on a category as "no competition" — it may just not be surveyed yet.',
      '<b>A handful of distributor codes are unresolved</b> (~€360 total, one line) and fall into no DB — immaterial, excluded from all views. "IMG" (SAP code 105, ~'+fmtEurFull(dbTotals['IMG']||0)+' total) is flagged in the internal distributor master mapping as a possible Germany service department, not a parts-selling DB — treat that row with caution pending confirmation.',
      'Data classification is 99.9% complete against the AIM taxonomy (unclassified part numbers are '+fmtEurFull(l1Totals['Unclassified']||0)+', 0.1% of clean network sales).',
    ];
    document.getElementById('notesList').innerHTML = notes.map(function(n){return '<li>'+n+'</li>';}).join('');
  }

  // ================= RENDER ALL =================
  function renderAll(){
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
    function tip(d){ if(!d) return ''; return (d.label||'')+'
'+(d.formula||'')+'
'+(d.plain||''); }
    function money(v){ if(v==null||isNaN(v)) return '—'; return '€'+Math.round(v).toLocaleString('en-GB'); }

    var kpiHtml = '<div class="kpi-grid">'+[
      ['Median shop / reference', k.median_am_vs_street!=null?k.median_am_vs_street.toFixed(2):'—', tip(defs.price_index)||'shop € ÷ reference customer price', 'accent'],
      ['Sales on undercut list', money(k.exposure_rev_cy2025_eur), 'CY2025 evidence PNs', ''],
      ['Illustrative pressure', money(k.illustrative_price_pressure_eur), tip(defs.price_pressure)||'sales × gap to reference', ''],
      ['KS channel spread', k.ks_channel_spread_median!=null?k.ks_channel_spread_median.toFixed(2):'—', 'genuine − AM vs reference (n='+(ks.n||0)+')', '']
    ].map(function(c){
      return '<div class="kpi-card '+c[3]+'" title="'+(c[2]||'').replace(/"/g,'&quot;')+'"><div class="kpi-label">'+c[0]+'</div><div class="kpi-value">'+c[1]+'</div><div class="kpi-sub">'+String(c[2]).split('
')[0]+'</div></div>';
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
  }

  // ================= EVENTS =================
  document.getElementById('selL1').addEventListener('change', function(e){
    state.l1 = e.target.value; state.l2 = 'All'; renderAll();
  });
  document.getElementById('selL2').addEventListener('change', function(e){
    state.l2 = e.target.value; renderAll();
  });
  document.getElementById('dbChips').addEventListener('click', function(e){
    var chip = e.target.closest('.chip'); if(!chip) return;
    var db = chip.dataset.db;
    if(state.dbs.has(db)) state.dbs.delete(db); else state.dbs.add(db);
    if(state.dbs.size===0) state.dbs.add(db);
    renderAll();
  });
  document.getElementById('grainToggle').addEventListener('click', function(e){
    var b = e.target.closest('button'); if(!b) return;
    state.grain = b.dataset.g; renderAll();
  });
  document.getElementById('btnAllDb').addEventListener('click', function(){ state.dbs = new Set(dbList); renderAll(); });
  document.getElementById('btnTop6Db').addEventListener('click', function(){ state.dbs = new Set(dbList.slice(0,6)); renderAll(); });
  document.getElementById('btnReset').addEventListener('click', function(){
    state = { l1:'All', l2:'All', grain:'quarter', dbs:new Set(dbList.slice(0,6)) };
    renderAll();
  });
  document.addEventListener('click', function(e){
    var t = e.target.closest('.toggle-table'); if(!t) return;
    var el = document.getElementById(t.dataset.target);
    if(!el) return;
    var showing = el.style.display !== 'none';
    el.style.display = showing ? 'none' : 'block';
    t.textContent = showing ? 'Table view' : 'Chart view';
    var chartEl = el.previousElementSibling;
    if(chartEl && chartEl.classList && chartEl.classList.contains('chart-container')) chartEl.style.display = showing ? '' : 'none';
  });

  document.getElementById('grainToggle').querySelector('button[data-g="quarter"]').classList.add('active');

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
})();