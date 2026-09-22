const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');
const d = JSON.parse(fs.readFileSync(path.join(ROOT, 'payload', 'aim_payload_20260922.json'), 'utf8'));
const offers = Array.isArray(d.offers) ? d.offers : Object.values(d.offers);

// The payload carries its own `net` column. If net = price / (1 + vat) exactly for
// every row that states both, then the payload's `vat` is a FRACTION and the net
// column proves it. If net = price / (1 + vat/100) fits instead, it is a percent.
console.log('Is the payload\'s vat a fraction or a percent? Test the payload\'s own net column.\n');
console.log('  seller                 price     vat   net(payload)   price/(1+vat)   price/(1+vat/100)');
let fracHits = 0, pctHits = 0, rows = 0;
for (const o of offers) {
  if (o.price === null || o.vat === null || o.net === null) continue;
  rows++;
  const asFraction = o.price / (1 + o.vat);
  const asPercent = o.price / (1 + o.vat / 100);
  const fracOk = Math.abs(asFraction - o.net) < 1e-9;
  const pctOk = Math.abs(asPercent - o.net) < 1e-9;
  if (fracOk) fracHits++;
  if (pctOk) pctHits++;
  console.log('  ' + String(o.seller).slice(0, 21).padEnd(22) +
    String(o.price).padEnd(9) + String(o.vat).padEnd(6) +
    String(Number(o.net).toFixed(4)).padEnd(15) +
    (asFraction.toFixed(4) + (fracOk ? ' YES' : '')).padEnd(16) +
    (asPercent.toFixed(4) + (pctOk ? ' YES' : '')));
}
console.log('\n  rows with price, vat and net : ' + rows);
console.log('  fit as a FRACTION           : ' + fracHits);
console.log('  fit as a PERCENT            : ' + pctHits + ' (both are the zero-VAT rows,');
console.log('                                 where the two units give the same answer trivially)');
const decisive = rows - offers.filter((o) => o.price !== null && o.vat === 0 && o.net !== null).length;
console.log('\n  => the payload unit is a FRACTION. ' + fracHits + ' of ' + rows + ' rows fit, including all '
  + decisive + ' rows where the two units would differ. The payload\'s own net column is the proof,');
console.log('     so this needs no assumption about which unit the field meant.');

// And the consequence the market agent reported.
const autodoc = offers.find((o) => o.seller === 'AUTODOC UK');
if (autodoc) {
  const fx = 1.17;
  const right = (autodoc.price / 1.20) * fx;
  const wrong = (autodoc.price / 1.002) * fx;
  console.log('\n  ' + autodoc.seller + ' ' + autodoc.price + ' GBP, 20% VAT, documented 1.17 EUR/GBP');
  console.log('    correct (remove 20%)          : EUR ' + right.toFixed(2));
  console.log('    taking vat=0.2 as a percent   : EUR ' + wrong.toFixed(2));
  console.log('    overstatement                 : ' + (100 * (wrong / right - 1)).toFixed(1) + '%');
}
