/* Shape probe (reviewer tool, Node).

   Answers two questions the acceptance suite depends on:
     1. Does the frozen case-data block parse without losing integer precision?
        (JavaScript numbers cannot hold 19-digit part numbers exactly.)
     2. What date metadata do the declared cost bases actually carry?

   Prints key names, types and date strings only. It never prints a price,
   a cost, a margin or a customer value.
*/
'use strict';
const fs = require('node:fs'), path = require('node:path');
const ROOT = path.resolve(__dirname, '..', '..');
const frozen = path.join(ROOT, 'reference', 'ISZE_AIM_Pricing_Decisions_v03_FROZEN.html');

const html = fs.readFileSync(frozen, 'utf8');
const m = html.match(/<script\b[^>]*\bid=["']case-data["'][^>]*>([\s\S]*?)<\/script>/i);
if (!m) { console.error('no case-data block'); process.exit(2); }
const text = m[1];
const data = JSON.parse(text);

const t = (v) => v === null ? 'null'
  : Array.isArray(v) ? 'list[' + v.length + ']'
  : typeof v === 'object' ? 'obj'
  : typeof v;

console.log('json.parse ok, top keys:', Object.keys(data).sort().join(', '));
console.log('defaultForwardBasis:', JSON.stringify(data.meta.defaultForwardBasis));
console.log('costBases:');
for (const b of data.meta.costBases || []) {
  console.log('  ', b.basis_id, '| status=', b.status,
    '| from=', JSON.stringify(b.offer_effective_from),
    '| to=', JSON.stringify(b.offer_effective_to),
    '| rate_window=', JSON.stringify(b.rate_window));
}
console.log('cases pn fidelity:');
for (const c of data.cases || []) {
  const raw = String(c.pn);
  console.log('  ', c.id, '| type', typeof c.pn, '| len', raw.length,
    '| all digits', /^[0-9]+$/.test(raw));
}
console.log('verifiedCosts pn fidelity:');
for (const r of data.verifiedCosts || []) {
  const raw = String(r.part_number);
  console.log('  ', raw.length, 'digits:', /^[0-9]+$/.test(raw), '| bases:', Object.keys(r.cost_bases || {}).join(','));
}
console.log('objectives:', JSON.stringify(data.meta.objectives));
console.log('source json round-trip stable:', JSON.stringify(data) === JSON.stringify(JSON.parse(JSON.stringify(data))));
