const errs = [];
const log = console.error;
console.error = (...a) => { errs.push(a.join(' ')); log(...a); };
window.addEventListener('error', e => errs.push('onerror: ' + e.message));
setTimeout(() => {
  const t = document.querySelectorAll('table tbody tr').length;
  const cv = document.querySelectorAll('#c1,#c2,#c3,#c4,#c5,#c6');
  let painted = 0;
  cv.forEach(c => { const p = c.getContext && c.getContext('2d');
    if (p && c.width > 0) painted++; });
  document.title = JSON.stringify({errors: errs, tableRows: t, canvases: cv.length, painted: painted});
}, 3000);
