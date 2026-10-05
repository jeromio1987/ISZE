

(function(){
  try {
    var q = (location.hash || '').replace(/^#p/, '') || new URLSearchParams(location.search).get('page');
    if (q) {
      document.querySelectorAll('.paper-page').forEach(function(el){
        if (el.getAttribute('data-page') !== q) el.style.display = 'none';
      });
      document.body.style.background = '#f7f4ee';
    }
  } catch (e) {}
  if (typeof Chart === 'undefined') return;
  document.querySelectorAll('.chart-wrap').forEach(function(el){ el.style.display = 'block'; });
  const ink = '#15233c', terr = '#c0552d', grid = '#e6e2d8';
  Chart.defaults.font.family = 'Segoe UI, Helvetica, Arial, sans-serif';
  Chart.defaults.font.size = 10;
  Chart.defaults.color = '#52514e';
  function bar(id, labels, data, colors){
    const el = document.getElementById(id);
    if (!el) return;
    new Chart(el, {type:'bar', data:{labels:labels, datasets:[{data:data, backgroundColor:colors, borderWidth:0, barPercentage:0.72, categoryPercentage:0.8}]},
      options:{indexAxis:'y', responsive:true, maintainAspectRatio:false, animation:false,
        plugins:{legend:{display:false}},
        scales:{x:{grid:{color:grid}, beginAtZero:true},
                y:{grid:{display:false}, ticks:{autoSkip:false}}}}});
  }
  bar('cBelowCeiling', ['ITUK','IUK','UTI','PT','UMI','DE','HU','NO'],
      [6.65,5.81,4.94,1.34,1.32,1.27,0.60,0.57],
      [terr,terr,terr,'#8a6a4a','#8a6a4a','#8a6a4a','#8a6a4a','#8a6a4a']);
  bar('cGps', ['IE','UTI','ITUK','FI','BE','PT','DE','UMI','NO','SE','GR','IUK','HU'],
      [389,322,249,231,220,209,197,179,179,151,139,128,88],
      ['#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c48a16','#c48a16']);
  bar('cImlGap', ['Air','Brake','Clutch','Oil','Fuel'], [736,642,393,141,127],
      ['#c0453c',terr,terr,'#8a6a4a','#8a6a4a']);
  bar('cCatGap', ['Clutch disc','Brake pad','Brake shoe','Clutch PP','Blower','Brake rotor','Fuel','Clutch kit'],
      [3.14,2.78,2.47,1.98,1.42,1.39,1.02,0.96],
      ['#c0453c','#c0453c',terr,terr,'#c48a16','#c48a16','#8a6a4a','#8a6a4a']);
  bar('cGapTypes', ['Substitution','Under-service','Catalogue gap'], [11.4,9.56,2.18],
      [terr,'#c48a16','#6b7c93']);
  bar('cPms', ['IE','ITUK','GR','UTI','UMI','BE','IUK','DE'],
      [100,100,97,91,85,63,38,15],
      ['#6b7c93','#6b7c93','#1d9e75','#1d9e75','#1d9e75','#c48a16','#c0453c','#c0453c']);
  bar('cMix', ['UTI','CY','GR','PT','IE','UMI','BE','ITUK','IUK','DE','SE'],
      [11.1,8.5,7.8,6.0,4.5,3.7,3.4,2.7,0.9,0.7,0.1],
      [terr,terr,terr,'#c48a16','#c48a16',ink,'#2b4a78','#2b4a78','#1d9e75','#1d9e75','#1d9e75']);
  bar('cIds', ['MT','PT','HU','PL','UK CV','UK LCV','LU','RO','BE','NL','DK','NO','GR','IL UMI'],
      [89.3,86.9,86.2,84.1,83.8,81.7,80,79.6,78.6,76.3,75.7,75.2,73.9,60.9],
      ['#1d9e75','#1d9e75','#1d9e75','#1d9e75','#2b4a78','#2b4a78','#2b4a78','#2b4a78','#c48a16','#c48a16','#c48a16','#c48a16','#c48a16','#c0453c']);
  bar('cPrice', ["ROTOR; DISC BRK,FRT", "PAD KIT; CALIPER,DISC ", "PAD KIT; CALIPER,DISC ", "FILTER; ACL", "ELEMENT KIT; FUEL FILT", "ELEMENT; OIL FILTER", "FILTER; BLOWER UNIT", "PUMP ASM; DEF,DCM SPLY", "PUMP; WATER", "TURBOCHARGER ASM", "NOZZLE ASM; INJ", "PAD KIT; DISC BRK,W/O "], [0.248, 0.407, 0.29, 0.062, 0.095, 0.193, 0.08, 0.442, 0.97, 0.799, 0.678, 0.542], ['#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d','#c0552d']);
  bar('cRepl', ['No sales to dealer','High vs bill','No bill','Low vs bill'], [500,400,380,315],
      [terr,'#c48a16','#2b4a78','#8a6a4a']);
  bar('cTender', ["EU", "DE-OV", "PL-BZP", "Norway", "FR-BOAMP", "PT-BASE", "BE", "Israel"],
      [156.0, 150.0, 20.0, 18.0, 17.0, 11.0, 6.0, 5.0],
      ["#2b4a78", "#1d9e75", "#1d9e75", "#1d9e75", "#1d9e75", "#1d9e75", "#1d9e75", "#1d9e75"]);
  document.body.classList.add('js-ok');
})();

