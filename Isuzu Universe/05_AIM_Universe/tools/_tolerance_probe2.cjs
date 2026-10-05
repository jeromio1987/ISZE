const path = require('path');
const ROOT = path.join(__dirname, '..');
const E = require(path.join(ROOT, 'src', 'engine', 'engine.js'));
E.setPayload({ verifiedCosts: [], costBases: [], meta: {} });

// The review reports: "100 units at 100 with a cost of 60, 20 more at 110, 500 of
// support - it reported a profit-preservation allowance of 25% when the arithmetic
// gives 8.33%." Test that exact configuration against the engine on disk.
const cfg = {
  price_before: 100, price_after: 110,
  quantity_before: 100, quantity_after: 120,
  cost_eur: 60, support_eur: 500, scope: 'all'
};
const r = E.calculate(cfg);
console.log('exact configuration from the review:');
console.log('  ' + JSON.stringify(cfg));
console.log('');
console.log('  ok                        :', r.ok, r.error || '');
console.log('  tolerable_loss_revenue_pct:', r.tolerable_loss_revenue_pct);
console.log('  tolerable_loss_gp_pct     :', r.tolerable_loss_gp_pct);
console.log('  tolerable_volume_loss_pct :', r.tolerable_volume_loss_pct);
console.log('  qty_preserve_gp           :', r.qty_preserve_gp);
console.log('  quantity_before           :', r.quantity_before);
console.log('');

// What does the algebra give for a price increase where support is present?
// The profitable-volume fraction f satisfies  f*q0*(p1-cost) - support = gp_before
const p0 = 100, p1 = 110, q0 = 100, cost = 60, support = 500;
const gpBefore = q0 * (p0 - cost);
const f = (gpBefore + support) / (q0 * (p1 - cost));
console.log('the algebra for a 100 -> 110 increase at q0=100, cost 60, support 500:');
console.log('  tolerable volume loss     :', (100 * (1 - f)).toFixed(2) + '%');
console.log('  (a NEGATIVE value means profit cannot be held at all, because the');
console.log('   500 of support exceeds what the 10 EUR rise on 100 units earns)');
console.log('');

// And the case where the rise DOES out-earn the support:
const s2 = 300;
const f2 = (gpBefore + s2) / (q0 * (p1 - cost));
const r2 = E.calculate({ price_before: p0, price_after: p1, quantity_before: q0,
  quantity_after: q0, cost_eur: cost, support_eur: s2, scope: 'all' });
console.log('same but with 300 support (the rise out-earns it):');
console.log('  algebra                   :', (100 * (1 - f2)).toFixed(2) + '%');
console.log('  engine tolerable_loss_gp  :', r2.tolerable_loss_gp_pct);
console.log('  agree                     :', Math.abs((100 * (1 - f2)) - r2.tolerable_loss_gp_pct) < 0.01);
