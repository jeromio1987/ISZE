const path = require('path');
const ROOT = path.join(__dirname, '..');
const E = require(path.join(ROOT, 'src', 'engine', 'engine.js'));
E.setPayload({ verifiedCosts: [], costBases: [], meta: {} });

// The agent claims: the all-volume case was always correct, and the repair shows
// on INCREMENTAL scope. Test both, and check the arithmetic by hand.
function byHand(scope, p0, p1, q0, q1, cost, support) {
  const gpBefore = q0 * (p0 - cost);
  const extra = q1 - q0;
  const gpAfter = (scope === 'all')
    ? q1 * (p1 - cost) - support
    : gpBefore + extra * (p1 - cost) - support;
  const perUnit = p1 - cost;
  // On all-volume: losing x units from q1 gives up x*(p1-cost); profit holds
  // while gpAfter - x*perUnit >= gpBefore.
  // On incremental: the existing units are untouched, so the additional units
  // must earn back their own shortfall; the floor is the extra volume needed.
  const floor = (gpAfter - gpBefore) / perUnit;
  return { gpBefore, gpAfter, perUnit, floor_all_volume: q1 - floor };
}

const configs = [
  { scope: 'all', p0: 100, p1: 110, q0: 100, q1: 120, cost: 60, support: 500 },
  { scope: 'incremental', p0: 100, p1: 110, q0: 100, q1: 120, cost: 60, support: 500 },
  { scope: 'all', p0: 100, p1: 110, q0: 100, q1: 100, cost: 60, support: 500 },
];

for (const c of configs) {
  const r = E.calculate({
    price_before: c.p0, price_after: c.p1, quantity_before: c.q0,
    quantity_after: c.q1, cost_eur: c.cost, support_eur: c.support, scope: c.scope
  });
  const h = byHand(c.scope, c.p0, c.p1, c.q0, c.q1, c.cost, c.support);
  console.log('scope=' + c.scope + '  price ' + c.p0 + '->' + c.p1 + '  qty ' + c.q0 + '->' + c.q1
    + '  cost ' + c.cost + '  support ' + c.support);
  console.log('   engine  gp_tol=' + String(r.tolerable_loss_gp_pct).padEnd(8)
    + ' qty_preserve_gp=' + String(r.qty_preserve_gp).padEnd(8)
    + ' binding=' + r.tolerable_volume_loss_pct);
  console.log('   by hand gpBefore=' + h.gpBefore + '  gpAfter=' + h.gpAfter
    + '  perUnit=' + h.perUnit + '  all-volume floor=' + h.floor_all_volume.toFixed(2));
  const implied = r.qty_preserve_gp;
  if (implied !== null && c.scope === 'all') {
    console.log('   implied tolerable loss = ' + (100 * (1 - implied / c.q1)).toFixed(2) + '%');
  }
  console.log('');
}

// Does the incremental figure now match the algebra?
console.log('--- the incremental claim, checked ---');
const inc = E.calculate({ price_before: 100, price_after: 120, quantity_before: 100,
  quantity_after: 110, cost_eur: 60, support_eur: 500, scope: 'incremental' });
const gpB = 100 * (100 - 60);
const gpA = gpB + 10 * (120 - 60) - 500;
console.log('  100 units at 100, 10 more at 120, cost 60, support 500, incremental');
console.log('  gpBefore=' + gpB + '  gpAfter=' + gpA);
console.log('  engine gp_tol=' + inc.tolerable_loss_gp_pct + '  qty_preserve_gp=' + inc.qty_preserve_gp);
console.log('  the arithmetic that matters: profit RISES by ' + (gpA - gpB)
  + ', so no volume loss is needed and the extra 10 units already cover the support.');
