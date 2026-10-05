const path = require('path');
const ROOT = path.join(__dirname, '..');
const E = require(path.join(ROOT, 'src', 'engine', 'engine.js'));
E.setPayload({ verifiedCosts: [], costBases: [], meta: {} });

// The claim under review: the "tolerable volume loss" figure overstates the
// tolerance because the break-even formula adds support that profit has already
// had deducted. Check the algebra directly rather than trusting either side.
function handCheck(p0, p1, q0, cost, support) {
  const gpBefore = q0 * (p0 - cost);
  // The volume at which profit after the increase, less support, equals gpBefore:
  //   f*q0*(p1-cost) - support = gpBefore
  const f = (gpBefore + support) / (q0 * (p1 - cost));
  return { gpBefore, tolerablePct: 100 * (1 - f) };
}

const cases = [
  { name: 'clean increase, no support', p0: 100, p1: 110, q0: 100, cost: 60, support: 0 },
  { name: 'increase with 500 support', p0: 100, p1: 110, q0: 100, cost: 60, support: 500 },
  { name: 'increase with 2000 support', p0: 100, p1: 110, q0: 100, cost: 60, support: 2000 },
  { name: 'small increase, 500 support', p0: 100, p1: 102, q0: 100, cost: 60, support: 500 },
];

console.log('scenario                        engine says   algebra says   verdict');
console.log('-'.repeat(78));
for (const c of cases) {
  const r = E.calculate({
    price_before: c.p0, price_after: c.p1, quantity_before: c.q0,
    quantity_after: c.q0, cost_eur: c.cost, support_eur: c.support, scope: 'all'
  });
  const hand = handCheck(c.p0, c.p1, c.q0, c.cost, c.support);
  const engineGp = r.tolerable_loss_gp_pct;
  const agree = engineGp !== null && Math.abs(engineGp - hand.tolerablePct) < 0.01;
  console.log(c.name.padEnd(32)
    + String(engineGp).padEnd(14)
    + hand.tolerablePct.toFixed(2).padEnd(15)
    + (agree ? 'agree' : 'DIFFER'));
}
console.log('');
console.log('Revenue tolerance is reported separately and is unchanged by this:');
const r = E.calculate({ price_before: 100, price_after: 110, quantity_before: 100,
  quantity_after: 100, cost_eur: 60, support_eur: 500, scope: 'all' });
console.log('  tolerable_loss_revenue_pct :', r.tolerable_loss_revenue_pct);
console.log('  tolerable_loss_gp_pct      :', r.tolerable_loss_gp_pct);
console.log('  tolerable_volume_loss_pct  :', r.tolerable_volume_loss_pct, '(the binding limit shown)');
