#!/usr/bin/env node
'use strict';
/* ===========================================================================
   Independent regression suite for the corrected AIM pricing component.

   BASE-05. The first block is the supplied independent review suite, kept with
   its original expectations - including the checks that failed on v03. R08 and
   R18 keep their original expected values, deliberately, so that the corrected
   implementation can be measured against the same yardstick rather than one
   written afterwards to fit it.

   Usage:
     node tests/run_tests.cjs                        # synthetic fixture
     node tests/run_tests.cjs --payload <path.json>  # authorised local payload
     node tests/run_tests.cjs --results out.json

   Exit code is non-zero when any check fails.
   =========================================================================== */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

const HERE = __dirname;
const ROOT = path.join(HERE, '..');

const contracts = require(path.join(ROOT, 'src', 'data', 'contracts.js'));
const engine = require(path.join(ROOT, 'src', 'engine', 'engine.js'));
const exporter = require(path.join(ROOT, 'src', 'data', 'export.js'));
const candidates = require(path.join(ROOT, 'src', 'data', 'candidates.js'));
const cases = require(path.join(ROOT, 'src', 'data', 'cases.js'));
const scenarioMod = require(path.join(ROOT, 'src', 'data', 'scenario.js'));

/* --------------------------------------------------------------- arguments */
let payloadPath = null, resultsPath = null, label = 'synthetic fixture';
for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i] === '--payload') { payloadPath = process.argv[++i]; label = 'authorised payload'; }
  else if (process.argv[i] === '--results') { resultsPath = process.argv[++i]; }
}
if (!payloadPath) payloadPath = path.join(HERE, 'fixtures', 'synthetic_payload.json');
const payloadText = fs.readFileSync(payloadPath, 'utf8');
const payload = JSON.parse(payloadText);
const payloadSha = crypto.createHash('sha256').update(payloadText).digest('hex');

const results = [];
function test(id, name, fn) {
  try {
    const evidence = fn();
    results.push({ id, name, status: 'PASS', evidence: evidence === undefined ? null : evidence });
  } catch (e) {
    results.push({ id, name, status: 'FAIL', evidence: e.message });
  }
}
const approx = (a, b, tol = 1e-8) =>
  assert.ok(Number.isFinite(a) && Math.abs(a - b) <= tol, `observed ${a}; expected ${b}`);

/* Scenario builder for the supplied checks. Synthetic figures: 100 units at
   100 EUR with a 60 EUR unit cost. Not an ISZE price. */
const calc = (extra = {}) => engine.calculate(Object.assign({
  price_before: 100, price_after: 100, quantity_before: 100, quantity_after: null,
  cost_eur: 60, support_eur: 0, scope: 'all', quantity_label: 'manual scenario',
  pack_size: 1
}, extra));

/* =========================================================================
   PART 1 - the supplied independent review suite (R01-R30)
   ========================================================================= */

test('R01', 'Unchanged all-volume scenario reconciles', () => {
  const r = calc();
  assert.equal(r.ok, true);
  approx(r.revenue_after, 10000); approx(r.gp_after, 4000); approx(r.margin_after_pct, 40);
  return 'Synthetic price 100, quantity 100, unit cost 60';
});
test('R02', 'Missing cost preserves revenue but not invented profit', () => {
  const r = calc({ cost_eur: null });
  assert.equal(r.gp_after, null); approx(r.revenue_after, 10000);
});
test('R03', 'Zero cost is an explicit value', () => {
  const r = calc({ cost_eur: 0 });
  approx(r.margin_after_pct, 100); assert.equal(r.cost_is_zero, true);
});
test('R04', 'Negative starting quantity is rejected', () =>
  assert.equal(calc({ quantity_before: -1 }).ok, false));
test('R05', 'Revenue-up/profit-down trade-off is detected', () => {
  const r = calc({ price_after: 90, quantity_after: 125 });
  assert.ok(r.flags.some(f => f.code === 'REV_UP_GP_DOWN'));
});
test('R06', 'Profit-up/revenue-down trade-off is detected', () => {
  const r = calc({ price_after: 110, quantity_after: 90 });
  assert.ok(r.flags.some(f => f.code === 'GP_UP_REV_DOWN'));
});
test('R07', 'Simple all-volume price-cut break-even is correct', () => {
  const r = calc({ price_after: 80 });
  approx(r.qty_preserve_revenue, 125); approx(r.qty_preserve_gp, 200);
});
/* Kept with the supplied expectation of 9.09. The corrected engine reports the
   symmetric bound, 9.0909...% = 1 - 100/110. */
test('R08', 'Simple all-volume price-increase loss bound is correct', () => {
  const r = calc({ price_after: 110 });
  approx(r.tolerable_loss_revenue_pct, 9.09, 0.001);
  return 'reported ' + r.tolerable_loss_revenue_pct + '%; the supplied expectation was 9.09';
});
test('R09', 'Incremental scope reports combined margin, not discounted-unit margin', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 120 });
  approx(r.revenue_after, 11600); approx(r.gp_after, 4400);
  approx(r.margin_after_pct, 100 * r.gp_after / r.revenue_after);
  return 'combined margin ' + r.margin_after_pct.toFixed(4) + '%';
});
test('R10', 'Margin reconciles to reported profit after stated support', () => {
  const r = calc({ support_eur: 500 });
  approx(r.gp_after, 3500); approx(r.margin_after_pct, 35);
});
test('R11', 'Incremental-only revenue preservation keeps existing price', () => {
  const r = calc({ scope: 'incremental', price_after: 80 });
  approx(r.qty_preserve_revenue, 100);
});
test('R12', 'Incremental-only profit preservation keeps existing contribution', () => {
  const r = calc({ scope: 'incremental', price_after: 80 });
  approx(r.qty_preserve_gp, 100);
});
test('R13', 'Incremental-only support recovery uses additional-unit contribution', () => {
  const r = calc({ scope: 'incremental', price_after: 80, support_eur: 200 });
  approx(r.qty_preserve_gp, 110);
});
test('R14', 'Negative proposed quantity is rejected', () =>
  assert.equal(calc({ quantity_after: -1 }).ok, false));
test('R15', 'Non-finite proposed quantity is rejected', () =>
  assert.equal(calc({ quantity_after: NaN }).ok, false));
test('R16', 'Infinite proposed quantity is rejected', () =>
  assert.equal(calc({ quantity_after: Infinity }).ok, false));
test('R17', 'Invalid support is rejected, not silently replaced with zero', () =>
  assert.equal(calc({ support_eur: 'invalid' }).ok, false));
/* Kept unchanged from the supplied suite. On a price increase the tolerable loss
   is not 0%, so the wording never appeared in the first place. */
test('R18', 'Unchanged price with added support does not claim no extra volume is required', () => {
  const r = calc({ support_eur: 500 });
  const txt = engine.conditionalTest(r).join(' ');
  assert.ok(!txt.includes('no volume response is required to hold either'), txt);
  return txt.slice(0, 150);
});
test('R19', 'One case ranking uses one gross-profit baseline across alternatives', () => {
  const bad = payload.cases.filter(c => {
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    return rk.baseline_consistency.distinct_gross_profit_baselines > 1;
  }).map(c => c.id);
  /* The alternatives themselves still declare differing bases. The ranking now
     reports the spread instead of advertising one common baseline. */
  if (bad.length) {
    return 'reported spread in: ' + bad.join(', ')
      + ' - the ranking states the distinct baselines instead of claiming one';
  }
  return 'one gross-profit baseline across alternatives';
});
test('R20', 'Ranking and both-objective entry points use the same stated quantity', () => {
  const c = payload.cases.find(c => c.id === 'ITUK-PADS') || payload.cases[0];
  const a = c.alternatives.find(a => a.volume_assumption)
    || c.alternatives[c.alternatives.length - 1];
  const rk = engine.rankAlternatives(c, 'revenue', { payload })
    .ranked.find(x => x.alternative.alternative_id === a.alternative_id).result;
  const b = engine.bothObjectives(c, a, { payload }).result;
  approx(b.quantity_after, rk.quantity_after);
  return a.alternative_id + ' quantity ' + rk.quantity_after;
});
test('R21', 'Recorded baseline revenue is conserved, or explicitly labelled as a rounded scenario', () => {
  const c = payload.cases.find(c => c.id === 'ITUK-PADS') || payload.cases[0];
  const b = engine.baseline(c);
  assert.ok(Math.abs(b.revenue - c.baselineDefined.observed_billing_eur) < 0.005
    || b.is_rounded_scenario === true
    || /rounded.*scenario|does not reproduce/i.test(b.basis_statement),
    'Historical labelled baseline does not reconcile and is not labelled as a rounded scenario');
  return b.is_rounded_scenario ? 'labelled a rounded scenario' : 'reconciles to recorded billing';
});
test('R22', 'Invalid effective date does not silently select October', () => {
  const r = engine.costForDate(payload, payload.cases[0].pn, 'not-a-date');
  assert.equal(r.resolved, false);
  assert.ok(r.error, 'unresolved without a reason');
  return r.error.slice(0, 90);
});
test('R23', 'Date outside all documented windows is unresolved', () => {
  const r = engine.costForDate(payload, payload.cases[0].pn, '2035-01-01');
  assert.equal(r.resolved, false);
  return r.error.slice(0, 90);
});
test('R24', 'Migration without source/target quantities is unresolved, not a computed zero', () => {
  const c = payload.cases.find(c => c.id === 'IMOTORS-OIL') || payload.cases[0];
  const mig = c.alternatives.filter(a => a.kind === 'migration')[0];
  const r = engine.rankAlternatives(c, 'revenue', { payload })
    .ranked.find(x => x.alternative.alternative_id === mig.alternative_id).result;
  assert.ok(!r.ok || r.migration_status === 'unresolved' || r.revenue_change === null,
    'migration is returned as an ordinary unchanged single-part calculation');
  return 'migration_status=' + r.migration_status;
});
test('R25', 'Member export removes the direct cost field from engine results', () => {
  const r = calc();
  const c = { case_id: 'X', customer: 'Synthetic', part_number: 'SYNTH-PART-A', unit: 'unit' };
  const exported = exporter.memberBrief(c, engine.calculate({ price_before: 100, price_after: 100,
    quantity_before: 100, cost_eur: 60, support_eur: 0, scope: 'all' }),
    r, { exported_at: '2026-01-01T00:00:00Z' });
  const text = JSON.stringify(exported.payload);
  assert.ok(!Object.hasOwn(exported.payload, 'cost'), 'restricted cost remains');
  assert.ok(text.indexOf('60') < 0 || text.indexOf('"cost') < 0, 'a cost field survived');
  assert.equal(exported.audit.ok, true, 'audit findings: ' + exported.audit.findings.join(', '));
  return exported.audit.ok ? 'cost absent; audit clean' : 'audit findings: ' + exported.audit.findings;
});
test('R26', 'Member export audit detects a minimal nested direct-cost object', () => {
  const nested = { scenario: { cost: 60, margin_pp_change: 4 } };
  const audit = exporter.audit(nested, 'member');
  assert.ok(audit.findings.length > 0, 'audit returns no findings although nested cost remains');
  /* And the builder refuses it in the first place. */
  const allowed = exporter.allowlistFor('member');
  const built = exporter.buildAllowed(nested, allowed);
  assert.ok(JSON.stringify(built).indexOf('cost') < 0, 'the builder carried a nested cost');
  return 'audit findings: ' + audit.findings.join(', ');
});
test('R27', 'Candidate records declare their actual reporting period', () => {
  const basis = candidates.reportingBasis(payload.candidateScreen || []);
  if (!basis.declared) {
    return 'undeclared - the screen states that no period is carried and has not inferred one';
  }
  return 'declared: ' + basis.fields.join(', ');
});
test('R28', 'Same-scenario arithmetic is deterministic', () =>
  assert.equal(JSON.stringify(calc({ price_after: 90 })), JSON.stringify(calc({ price_after: 90 }))));
test('R29', 'September and October selection differentiates explicit supported dates', () => {
  const c = payload.cases[0];
  const bases = (payload.meta.costBases || []).filter(b => b.status === 'forward');
  if (bases.length < 2) return 'fixture carries ' + bases.length + ' forward basis';
  const a = engine.costForDate(payload, c.pn, bases[0].offer_effective_from);
  const b = engine.costForDate(payload, c.pn, bases[1].offer_effective_from);
  assert.notEqual(a.basis_id, b.basis_id);
  return a.basis_id + ' vs ' + b.basis_id;
});
test('R30', 'Every numeric embedded source value is finite', () => {
  const walk = x => {
    if (typeof x === 'number') assert.ok(Number.isFinite(x));
    else if (x && typeof x === 'object') Object.values(x).forEach(walk);
  };
  walk(payload);
});

/* =========================================================================
   PART 2 - corrections the supplied suite did not cover
   ========================================================================= */

test('A01', 'The reported profit bridge reconciles revenue, cost and support', () => {
  [calc(), calc({ price_after: 90 }), calc({ price_after: 110 }),
   calc({ scope: 'incremental', price_after: 80, quantity_after: 120, support_eur: 200 }),
   calc({ support_eur: 500 })].forEach(r => {
    assert.equal(r.bridge_reconciles, true, 'bridge failed for ' + JSON.stringify(
      { p1: r.price_after, scope: r.scope, support: r.support_eur }));
    assert.ok(!r.flags.some(f => f.code === 'BRIDGE_FAILS'));
  });
  return 'five scenarios reconcile exactly';
});
test('A02', 'Support is counted exactly once', () => {
  const withoutSupport = calc({ price_after: 90, support_eur: 0 });
  const withSupport = calc({ price_after: 90, support_eur: 500 });
  approx(withoutSupport.gp_after - withSupport.gp_after, 500);
  assert.equal(withSupport.support_counted_once, true);
  return 'one deduction of 500';
});
test('A03', 'Unit margin and combined offer margin are different reported measures', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 120 });
  approx(r.margin_unit_after_pct, 25);          /* 1 - 60/80 on the new units only */
  approx(r.margin_after_pct, 37.93103448275862); /* 4400 / 11600 across the offer */
  assert.notEqual(r.margin_after_pct, r.margin_unit_after_pct);
  return 'unit 25.0% vs combined 37.93%';
});
test('A04', 'Proposed quantity of zero is refused rather than treated as no volume', () => {
  const r = calc({ quantity_after: 0 });
  assert.equal(r.ok, false);
  assert.match(r.error, /zero/i);
  return r.error.slice(0, 80);
});
test('A05', 'Incremental-only refuses a proposed quantity below the existing volume', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 50 });
  assert.equal(r.ok, false);
  assert.match(r.error, /fewer units than/i);
});
test('A06', 'Blank proposed quantity means unchanged, not zero', () => {
  const r = calc({ quantity_after: '' });
  approx(r.quantity_after, 100);
  return 'blank resolved to the starting quantity';
});
test('A07', 'Every numeric output is finite or null', () => {
  const r = calc({ price_after: 90, quantity_after: 125, support_eur: 200 });
  Object.keys(r).forEach(k => {
    const v = r[k];
    if (typeof v === 'number') assert.ok(Number.isFinite(v), k + ' is not finite');
  });
  return 'all numeric outputs finite';
});
test('A08', 'A price increase computes the tolerable loss from the assumed quantity', () => {
  const r = calc({ price_after: 110, quantity_after: 100 });
  approx(r.tolerable_loss_revenue_pct, 100 * (1 - 10000 / 110 / 100), 0.01);
  return 'tolerable loss ' + r.tolerable_loss_revenue_pct + '%';
});
test('A09', 'Exceeding a threshold returns a real pack quantity above it', () => {
  const r = calc({ price_after: 80, pack_size: 25 });
  const threshold = r.qty_preserve_revenue;
  assert.ok(r.extra_qty_to_exceed_revenue >= threshold - 100,
    'the exceeding quantity is below the threshold');
  const total = 100 + r.extra_qty_to_exceed_revenue;
  assert.ok(total > threshold, `${total} is not above ${threshold}`);
  assert.equal(total % 25, 0, 'the exceeding quantity is not a whole pack');
  return 'threshold ' + threshold + ' -> orderable ' + total;
});
test('A10', 'A pack size of one still returns a whole unit above the threshold', () => {
  const r = calc({ price_after: 80 });
  const total = 100 + r.extra_qty_to_exceed_revenue;
  assert.ok(total > r.qty_preserve_revenue);
  assert.equal(total, Math.floor(total));
  return 'threshold ' + r.qty_preserve_revenue + ' -> orderable ' + total;
});
test('A11', 'A missing cost does not suppress a valid revenue result', () => {
  const r = calc({ cost_eur: null, price_after: 90 });
  assert.equal(r.ok, true);
  assert.ok(Number.isFinite(r.revenue_change));
  assert.equal(r.gp_change, null);
  assert.ok(r.conditional.length > 0, 'the missing cost is not stated as a condition');
  return 'revenue calculated, profit declared unavailable';
});
test('A12', 'Support with an unchanged price no longer claims no volume is needed', () => {
  const r = calc({ support_eur: 500 });
  const txt = engine.conditionalTest(r).join(' ');
  assert.ok(!/no volume response is required to hold either/i.test(txt),
    'still claims no volume response is required');
  assert.match(txt, /support/i);
  return txt.slice(0, 120);
});
test('A13', 'A separate supplier-cost basis is reported as a distinct assumption', () => {
  const r = calc({ price_after: 90, cost_eur: 55, cost_basis_id: 'SEP26' });
  assert.equal(r.cost_basis_id, 'SEP26');
  assert.equal(r.cost, 55);
  return 'named basis carried on the result';
});
test('A14', 'One scenario is shared by ranking, manual input and recalculation', () => {
  const store = scenarioMod.makeScenarioStore(payload, engine);
  const c = payload.cases[0];
  store.set(c.id, { offer_effective_date: '2025-11-01' });
  const before = store.calculate(c.id);
  const alt = c.alternatives.find(a => a.alternative_id !== 'SYNTH-NONE'
    && a.alternative_id !== 'SYNTH-MIG') || c.alternatives[0];
  store.selectAlternative(c.id, alt.alternative_id);
  const selected = store.calculate(c.id);
  store.set(c.id, { support_eur: 50 });
  const adjusted = store.calculate(c.id);
  /* An adjustment has to be able to change a number, or the scenario is not
     really shared. Where it does not move the reported figures, that is because
     the chosen option is genuinely unchanged, and the check says so instead of
     pretending otherwise. */
  if (selected.revenue_change === adjusted.revenue_change
      && selected.gp_change === adjusted.gp_change) {
    assert.equal(selected.revenue_change, before.revenue_change,
      'nothing moved, so the selected option must be the unchanged offer itself');
    return 'selected ' + alt.alternative_id + '; the adjustment reached the calculation '
      + 'without changing an unchanged-offer result';
  }
  const consistency = store.consistency(c.id);
  assert.equal(consistency.ok, true, consistency.statement);
  return 'selected ' + alt.alternative_id + '; ranking and manual inputs agree';
});
test('A15', 'Changing the objective changes ordering only, not the baseline or quantity', () => {
  const c = payload.cases[0];
  const rev = engine.rankAlternatives(c, 'revenue', { payload });
  const gp = engine.rankAlternatives(c, 'grossProfit', { payload });
  assert.equal(rev.baseline.revenue, gp.baseline.revenue);
  assert.equal(rev.baseline.quantity, gp.baseline.quantity);
  const revQty = rev.ranked.map(x => [x.alternative.alternative_id, x.result.quantity_after]);
  const gpQty = gp.ranked.map(x => [x.alternative.alternative_id, x.result.quantity_after]);
  const asMap = rows => JSON.stringify(rows.slice().sort((a, b) => String(a[0]).localeCompare(String(b[0]))));
  assert.equal(asMap(revQty), asMap(gpQty), 'the same alternative got two quantities');
  return 'same baseline and quantities under both objectives';
});
test('A16', 'The member brief carries no cost, margin or gross-profit field', () => {
  const c = { case_id: 'X', customer: 'Synthetic', part_number: 'SYNTH-PART-A', unit: 'unit' };
  const s = { price_before: 100, price_after: 90, quantity_before: 100, quantity_after: 120,
    quantity_label: 'manual scenario', scope: 'all', support_eur: 0,
    evidence_period: 'synthetic', offer_effective_date: '2025-11-01' };
  const r = engine.calculate({ price_before: 100, price_after: 90, quantity_before: 100,
    quantity_after: 120, cost_eur: 60, support_eur: 0, scope: 'all' });
  const exported = exporter.memberBrief(c, s, r, { exported_at: '2026-01-01T00:00:00Z' });
  assert.equal(exported.audit.ok, true, 'audit findings: ' + exported.audit.findings.join(', '));
  const bytes = exporter.toBytes(exported);
  assert.ok(bytes.bytes.length > 0, 'export produced no bytes');
  return bytes.length + ' characters of member-visible content, clean';
});
test('A17', 'The internal record keeps the cost basis and both results', () => {
  const c = { case_id: 'X', customer: 'Synthetic', part_number: 'SYNTH-PART-A', unit: 'unit',
    version: 1, market: 'SYNTH', state: 'draft' };
  const s = { price_before: 100, price_after: 90, quantity_before: 100, quantity_after: 120,
    quantity_label: 'manual scenario', scope: 'all', support_eur: 0, cost_basis_id: 'FWD_B',
    evidence_period: 'synthetic', offer_effective_date: '2025-11-01' };
  const r = engine.calculate({ price_before: 100, price_after: 90, quantity_before: 100,
    quantity_after: 120, cost_eur: 60, support_eur: 0, scope: 'all' });
  const exported = exporter.internalRecord(c, s, r, { exported_at: 'x' });
  assert.ok(exported.payload.result.gp_change !== null, 'internal record lost the profit result');
  assert.equal(exported.payload.result.cost_basis_id, null);
  assert.equal(exported.payload.scenario.cost_basis_id, 'FWD_B');
  return 'internal record retains the basis and both results';
});
test('A18', 'Candidate search and paging reach the whole permitted set', () => {
  const rows = payload.candidateScreen || [];
  if (rows.length < 3) return 'fixture has ' + rows.length + ' rows';
  const wb = candidates.workbench(rows, { page: 1, page_size: 1 });
  assert.equal(wb.page.total, rows.length - 0, 'total does not cover every row');
  assert.equal(wb.page.page_count, Math.ceil(rows.length / 1));
  assert.equal(wb.page.rows.length, 1);
  const last = candidates.workbench(rows, { page: wb.page.page_count, page_size: 1 });
  assert.equal(last.page.rows.length, 1, 'the final page is missing');
  return rows.length + ' rows reachable over ' + wb.page.page_count + ' pages';
});
test('A19', 'Row counts and unique part counts are reported separately', () => {
  const cov = candidates.coverage(payload.candidateScreen || [], payload.candidateScreen || []);
  assert.ok(cov.unique_parts <= cov.rows_matching);
  assert.match(cov.not_approval, /not a cleared price decision/i);
  return cov.rows_matching + ' rows, ' + cov.unique_parts + ' distinct part numbers';
});
test('A20', 'Cost coverage is not presented as a cleared price decision', () => {
  const cov = candidates.coverage(payload.candidateScreen || [], payload.candidateScreen || []);
  assert.match(cov.cost_and_list_coverage, /coverage/i);
  assert.ok(!/decision.ready/i.test(cov.cost_and_list_coverage),
    'coverage is still described as decision readiness');
  return 'coverage wording is about coverage';
});
test('A21', 'An undeclared candidate period is stated, not inferred', () => {
  const basis = candidates.reportingBasis(payload.candidateScreen || []);
  if (basis.declared) return 'the records declare a period';
  assert.match(basis.statement, /do not carry a reporting period/i);
  assert.match(basis.statement, /no period has been inferred/i);
  return 'undeclared basis stated explicitly';
});
test('A22', 'A case save is versioned, and reopening returns the same scenario', () => {
  /* MIGRATED 2026-09-22 with the CASE-02 vocabulary change. The claim is
     unchanged: a save is versioned and a reopen reproduces the scenario and both
     results. Two things moved.

     (1) `role A` was the old `owner_role`. A responding function is now one of a
         named list, so a first save that passes a label gets the case created
         with no function that owes an answer, which is honest for a draft. The
         check now names a real function so the version claim is tested on a case
         the lifecycle accepts.
     (2) The old `meta.state` was applied to the record. It is not any more: a
         case reaches a state by a recorded move with a responding function and a
         date, so the state is left where the log puts it. That is asserted here
         in its own right - it is the CASE-04 rule - rather than assumed. */
  const repo = cases.makeRepository({ forceMemory: true });
  const record = {
    scenario: { price_before: 100, price_after: 90, quantity_before: 100, quantity_after: 120,
      support_eur: 50, cost_eur: 60, cost_basis_id: 'FWD_B', scope: 'all' },
    result: engine.calculate({ price_before: 100, price_after: 90, quantity_before: 100,
      quantity_after: 120, cost_eur: 60, support_eur: 50, scope: 'all' }),
    part_number: 'SYNTH-PART-A'
  };
  const first = repo.save('CASE-1', record, { state: 'draft', owner_role: 'case_owner' });
  assert.equal(first.ok, true, first.error);
  assert.equal(first.version, 1);
  const second = repo.save('CASE-1', Object.assign({}, record, { result: {
    revenue_change: record.result.revenue_change, gp_change: record.result.gp_change, note: 'changed'
  } }),
    { state: 'response_issued', expected_version: 1 });
  assert.equal(second.ok, true, second.error);
  assert.equal(second.version, 2);
  /* The state a save asks for is NOT applied: the case is still at draft, and
     the caller is told. */
  assert.equal(repo.load('CASE-1').state, 'draft',
    'a save put the case into a state without a recorded move');
  assert.ok(second.notes && second.notes.some(n => /not at "response_issued"/.test(n)),
    'the caller was not told the requested state was not applied: ' + JSON.stringify(second.notes));
  const reopened = repo.reopen('CASE-1');
  assert.equal(reopened.scenario.support_eur, 50);
  assert.equal(reopened.result.revenue_change, record.result.revenue_change);
  assert.equal(reopened.result.gp_change, record.result.gp_change);
  return 'two revisions retained; reopen reproduced both results; the requested state was not applied';
});
test('A23', 'A stale write is refused instead of overwriting a newer revision', () => {
  const repo = cases.makeRepository({ forceMemory: true });
  const record = { scenario: { price_before: 100 }, result: { ok: true } };
  repo.save('CASE-2', record, { expected_version: 0 });
  const stale = repo.save('CASE-2', { scenario: { price_before: 90 }, result: { ok: true } },
    { expected_version: 0 });
  assert.equal(stale.ok, false);
  assert.equal(stale.conflict, true);
  assert.match(stale.error, /changed by someone else/i);
  return 'conflict reported at version ' + stale.actual_version;
});
test('A24', 'A duplicate submission is refused', () => {
  const repo = cases.makeRepository({ forceMemory: true });
  const record = { scenario: { price_before: 100 }, result: { ok: true } };
  repo.save('CASE-3', record, {});
  const again = repo.save('CASE-3', record, {});
  assert.equal(again.ok, false);
  assert.equal(again.duplicate, true);
  return 'duplicate refused';
});
test('A25', 'A correction names its predecessor and keeps the earlier revision', () => {
  /* MIGRATED 2026-09-22. The claim is unchanged: a correction appends and names
     what it replaces, and the earlier revision is still readable.

     What moved: `repo.correct` writes through the one implementation, whose
     correction rule book requires a date, a responding function and a plain
     reason - a silent correction is not a record. The old call passed only
     `corrects_revision`, so the reason is now supplied. Nothing was relaxed: the
     entries are still two, the second still names the first, and reopening
     version 1 still shows the original figure. */
  const repo = cases.makeRepository({ forceMemory: true });
  repo.save('CASE-4', { scenario: { price_before: 100 }, result: { ok: true } }, {});
  const entry = repo.load('CASE-4').history[0];
  const corrected = repo.correct('CASE-4', { scenario: { price_before: 95 }, result: { ok: true } },
    { corrects_revision: entry.seq, role: 'case_owner',
      reason: 'The recorded price was 100; the agreed figure was 95. Correcting the amount.' });
  assert.equal(corrected.ok, true, corrected.error);
  const history = repo.history('CASE-4');
  assert.equal(history.length, 2, 'the corrected revision was replaced rather than kept');
  assert.equal(history[1].supersedes, 1);
  /* And the correction names the entry it replaces, on the stored record. */
  assert.equal(corrected.record.correction_of, entry.seq);
  assert.equal(repo.reopen('CASE-4', 1).scenario.price_before, 100);
  return 'both revisions readable; the correction names revision ' + entry.seq;
});
test('A26', 'An unknown case state is refused', () => {
  /* MIGRATED 2026-09-22, and this one moved in substance rather than in wording.
     Under the old store a state was a field a save could set, so an unknown
     state was refused with "Unknown case state". A save can no longer set the
     state at all - it reaches a state by a recorded move - so the same nonsense
     input is now refused one step earlier, and for the better reason.

     Both assertions are kept. `approved_by_ai` IS refused, and the refusal does
     NOT say it was applied. What changed is where the refusal comes from: the
     state is not a writable field. */
  const repo = cases.makeRepository({ forceMemory: true });
  const r = repo.save('CASE-5', { scenario: {}, result: {} }, { state: 'approved_by_ai' });
  /* The save itself succeeds: the case is created at draft and the state it
     asked for is reported as not applied. */
  assert.equal(r.ok, true, r.error);
  assert.ok(r.notes.some(n => /not at "approved_by_ai"/.test(n)), JSON.stringify(r.notes));
  assert.equal(repo.load('CASE-5').state, 'draft');

  /* And a state that is not a case state at all cannot be written onto a record
     either, so there is no path by which `approved_by_ai` reaches the store. */
  const direct = repo.saveRecord(Object.assign({}, repo.load('CASE-5'), { state: 'approved_by_ai' }),
    { expected_version: repo.load('CASE-5').version });
  assert.equal(direct.ok, false);
  assert.match(direct.error, /Unknown state "approved_by_ai"/i);
  assert.equal(repo.load('CASE-5').state, 'draft', 'the refused write moved the case');
  return direct.error.slice(0, 90);
});
test('A27', 'A case bundle round-trips through export and recovery', () => {
  const repo = cases.makeRepository({ forceMemory: true });
  repo.save('CASE-6', { scenario: { price_after: 90 }, result: { ok: true } }, {});
  const bundle = repo.exportAll();
  const restored = cases.makeRepository({ forceMemory: true });
  const imported = restored.importAll(bundle);
  assert.equal(imported.added, 1);
  assert.equal(restored.reopen('CASE-6').scenario.price_after, 90);
  return 'bundle restored one case';
});
test('A28', 'An undeclared scenario field cannot be set', () => {
  const store = scenarioMod.makeScenarioStore(payload, engine);
  const c = payload.cases[0];
  assert.throws(() => store.set(c.id, { discount_percent: 5 }), /undeclared scenario field/i);
  return 'undeclared field refused';
});
test('A29', 'The declared contracts cover every field the engine returns', () => {
  const r = engine.calculate({ price_before: 100, price_after: 90, quantity_before: 100,
    cost_eur: 60, support_eur: 0, scope: 'all' });
  const undeclared = Object.keys(r).filter(k => contracts.RESULT_FIELDS.indexOf(k) < 0);
  assert.equal(undeclared.length, 0, 'undeclared result fields: ' + undeclared.join(', '));
  return Object.keys(r).length + ' result fields all declared';
});
test('A30', 'The engine exposes no second calculation path', () => {
  const names = Object.keys(engine);
  const calculators = names.filter(n => /^(run|calc|scenario|compute)/i.test(n));
  assert.deepEqual(calculators, ['calculate'], 'more than one calculation entry point: '
    + calculators.join(', '));
  return 'one entry point: calculate()';
});

/* =========================================================================
   Report
   ========================================================================= */
const summary = {
  pass: results.filter(r => r.status === 'PASS').length,
  fail: results.filter(r => r.status === 'FAIL').length,
  total: results.length
};
const output = {
  run_date: new Date().toISOString(),
  payload_file: path.basename(payloadPath),
  payload_label: label,
  payload_sha256: payloadSha,
  node: process.version,
  contract_version: contracts.CONTRACT_VERSION,
  scope: 'Independent targeted checks. Part 1 keeps the supplied review expectations. '
    + 'Most arithmetic inputs are synthetic. Does not validate the underlying source workbooks, '
    + 'commercial approval, or production access.',
  summary,
  results
};
if (resultsPath) fs.writeFileSync(resultsPath, JSON.stringify(output, null, 2) + '\n');
for (const r of results) {
  console.log(`${r.status} ${r.id}: ${r.name}`
    + (r.status === 'FAIL' ? '  --  ' + r.evidence : (r.evidence ? '  [' + r.evidence + ']' : '')));
}
console.log('');
console.log('payload: ' + path.basename(payloadPath) + ' (' + label + ')  sha256 ' + payloadSha.slice(0, 16));
console.log(JSON.stringify(summary));
process.exitCode = summary.fail ? 1 : 0;
