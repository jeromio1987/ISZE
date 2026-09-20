
(async () => {
  const out = {charts:{}, counts:{}, errors:[]};
  window.addEventListener('error', e => out.errors.push(String(e.message)));
  await new Promise(r => setTimeout(r, 400));
  const cs = window.Chart ? Object.keys(Chart.instances || {}) : [];
  for (const id of ['c-league','c-l1','c-mix','c-src']) {
    const el = document.getElementById(id);
    const ch = el && Chart.getChart(el);
    out.charts[id] = ch ? {
      type: ch.config.type,
      points: ch.data.datasets.reduce((n,d)=>n + (d.data?d.data.length:0), 0),
      drawn: !!(ch.chartArea && ch.chartArea.width > 10),
      area: ch.chartArea ? [Math.round(ch.chartArea.width), Math.round(ch.chartArea.height)] : null
    } : null;
  }
  out.counts.kpi = document.querySelectorAll('#kpis .kpi').length;
  out.counts.drillRows = document.querySelectorAll('#drill tbody tr').length;
  out.counts.movers = document.querySelectorAll('#movers tbody tr').length;
  out.counts.custs = document.querySelectorAll('#custs tbody tr').length;
  out.counts.leagueOptions = document.querySelectorAll('#db option').length;
  out.counts.srcOptions = document.querySelectorAll('#src option').length;
  out.headline = {
    kpi: Array.from(document.querySelectorAll('#kpis .kpi')).slice(0,4)
      .map(k => (k.querySelector('.val')||{}).textContent)
  };
  out.canvasBlank = {};
  for (const id of ['c-league','c-l1','c-mix','c-src']) {
    const cv = document.getElementById(id);
    if (!cv) { out.canvasBlank[id] = 'missing'; continue; }
    const g = cv.getContext('2d');
    const d = g.getImageData(0,0,cv.width,cv.height).data;
    let nonWhite = 0;
    for (let i=0;i<d.length;i+=4*97) { if (d[i]<245||d[i+1]<245||d[i+2]<245) nonWhite++; }
    out.canvasBlank[id] = nonWhite;
  }
  return out;
})()
