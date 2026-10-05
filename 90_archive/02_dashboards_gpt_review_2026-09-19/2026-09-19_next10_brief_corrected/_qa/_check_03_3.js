
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

  // Truck repair operations, placed by their own median age and distance against the stated limits.
  // The claim files carry no funding decision, so the earlier payer labels are replaced by the
  // position the data actually supports. Same rows, same euro, no amounts changed.
  const ops = DATA.who_pays.slice();
  const posOf = r => r.median_age_years > 3 || r.median_odometer_km > 100000
    ? 'over the stated limits'
    : 'inside the stated limits';
  new Chart(document.getElementById('c9'), {
    type:'doughnut',
    data:{labels:['inside the stated limits','over the stated limits'],
      datasets:[{data:['inside the stated limits','over the stated limits']
        .map(p => ops.filter(r => posOf(r) === p)
        .reduce((a, r) => a + r.parts_turnover_eur, 0)),
        backgroundColor:[NAVY,TERRA], borderColor:'#fff', borderWidth:2}]},
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
    who_pays: r.median_age_years > 3 || r.median_odometer_km > 100000
      ? 'over the stated limits'
      : 'inside the stated limits'})).slice(0,16), [
    {h:'Operation', v:r=>r.operation.replace(/ - .*$/,'')},
    {h:'€', r:1, v:r=>f(r.parts_turnover_eur)},
    {h:'Claims', r:1, v:r=>r.claim_lines.toLocaleString('en-GB')},
    {h:'Median km', r:1, v:r=>Math.round(r.median_odometer_km).toLocaleString('en-GB')},
    {h:'Position vs the limits', v:r=>r.who_pays}
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
