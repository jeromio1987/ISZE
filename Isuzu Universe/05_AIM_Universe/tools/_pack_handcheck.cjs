const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');
const PAY = path.join(ROOT, 'payload', 'aim_payload_20260922.json');
const PACK = path.join(ROOT, '..', 'GPT_HANDOVER_2026-09-22');

const d = JSON.parse(fs.readFileSync(PAY, 'utf8'));

// Everything identifying the payload carries.
const coreParts = new Set((d.verifiedCosts || []).map((r) => String(r.part_number)));
const screenParts = new Set((d.candidateScreen || []).map((r) => String(r.part_number)).filter(Boolean));
const allParts = new Set([...coreParts, ...screenParts]);
const offers = Array.isArray(d.offers) ? d.offers : Object.values(d.offers || {});
const sellers = new Set(offers.map((o) => o.seller).filter(Boolean));
const costs4 = new Set();
for (const r of d.verifiedCosts || []) {
  for (const c of Object.values(r.cost_bases || {})) {
    if (typeof c.cost_eur === 'number') costs4.add(c.cost_eur.toFixed(4));
  }
}

function files(dir) {
  const out = [];
  (function walk(p) {
    for (const e of fs.readdirSync(p, { withFileTypes: true })) {
      const q = path.join(p, e.name);
      if (e.isDirectory()) walk(q);
      else out.push(q);
    }
  })(dir);
  return out;
}

console.log('payload: ' + allParts.size + ' part numbers, ' + sellers.size + ' sellers, '
  + costs4.size + ' four-decimal costs');
console.log('');

let hits = 0;
for (const f of files(PACK)) {
  let t;
  try { t = fs.readFileSync(f, 'utf8'); } catch (_) { continue; }
  const rel = path.relative(PACK, f);
  const lines = t.split('\n');
  lines.forEach((line, i) => {
    const parts = [...allParts].filter((p) => p && line.includes(p));
    const sels = [...sellers].filter((s) => s && line.includes(s));
    const cst = [...costs4].filter((c) => line.includes(c));
    if (parts.length || sels.length || cst.length) {
      hits++;
      const what = [];
      if (parts.length) what.push('PART ' + parts.join(','));
      if (sels.length) what.push('SELLER ' + sels.join(','));
      if (cst.length) what.push('COST4 ' + cst.join(','));
      console.log(rel + ':' + (i + 1) + '  [' + what.join('  ') + ']');
      console.log('    ' + line.trim().slice(0, 150));
    }
  });
}
console.log('');
console.log(hits ? 'TOTAL LINES: ' + hits : 'CLEAN: nothing identifying found.');
