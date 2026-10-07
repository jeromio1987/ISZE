#!/usr/bin/env node
'use strict';
/* ===========================================================================
   ACCEPT-01 / BASE-05 - corrected engine, independent acceptance check.

   The supplied independent review wrote 30 targeted checks (R01-R30) against
   the frozen v03 HTML. This file carries every one of those expectations over
   to the maintained module in src/engine/engine.js, which is the source the
   corrected build actually uses.

   HOW THE PORT WAS DONE
     - The original expectation is reproduced verbatim in ORIGINAL below, so a
       reader can see what is being asserted and what was changed.
     - No assertion was relaxed, deleted or rewritten to obtain a green report.
     - Where the assertion had to be re-pointed (a renamed function or a moved
       contract), the new call is stated in ADAPTED, and both the original and
       the adapted form are reported.
     - Where an original assertion still fails, it is reported as a failure with
       the observed value. It has not been removed.

   What this does NOT do
     - It does not certify the underlying supplier workbooks, the FX authority,
       cost eligibility or any commercial approval.
     - It does not replace the developer's own suite in tests/run_tests.cjs.
       That suite is the author's; this one is the reviewer's.
     - It does not read a rebuilt HTML. It loads src/engine/engine.js directly,
       so it can run while the build output is mid-write.
   =========================================================================== */
const H = require('./lib/harness.cjs');
const path = require('node:path');
const fs = require('node:fs');

const run = H.makeRun('ACCEPT-01', 'Corrected financial engine - 30 supplied checks carried to src/engine/engine.js', [
  'Expectations R01-R30 are the supplied reviewer set. They are not the author\'s suite.',
  'Arithmetic inputs are synthetic. They are not ISZE business figures.',
  'Node vm is not a security boundary; the frozen file executed here is the one that was reviewed.'
]);

/* ------------------------------------------------------------ ORIGINAL ---- */
/* The supplied set, verbatim from 06_Working/AIM_v03_HANDOFF_20260922/tests/review_engine.cjs.
   Kept as documentation of the intent that must survive the port.

   R01 Unchanged all-volume scenario reconciles
   R02 Missing cost preserves revenue but not invented profit
   R03 Zero cost is an explicit value
   R04 Negative starting quantity is rejected
   R05 Revenue-up/profit-down trade-off is detected
   R06 Profit-up/revenue-down trade-off is detected
   R07 Simple all-volume price-cut break-even is correct
   R08 Simple all-volume price-increase loss bound is correct
   R09 Incremental scope reports combined margin, not discounted-unit margin
   R10 Margin reconciles to reported profit after stated support
   R11 Incremental-only revenue preservation keeps existing price
   R12 Incremental-only profit preservation keeps existing contribution
   R13 Incremental-only support recovery uses additional-unit contribution
   R14 Negative proposed quantity is rejected
   R15 Non-finite proposed quantity is rejected
   R16 Infinite proposed quantity is rejected
   R17 Invalid support is rejected, not silently replaced with zero
   R18 Unchanged price with added support does not claim no extra volume is required
   R19 One case ranking uses one gross-profit baseline across alternatives
   R20 Ranking and both-objective entry points use the same stated quantity
   R21 Recorded baseline revenue is conserved, or explicitly labelled as a rounded scenario
   R22 Invalid effective date does not silently select October
   R23 Date outside all documented windows is unresolved
   R24 Migration without source/target quantities is unresolved, not a computed zero
   R25 Distributor strip removes the direct cost field from engine results
   R26 Distributor audit detects a minimal nested direct-cost object
   R27 Candidate records declare their actual reporting period
   R28 Same-scenario arithmetic is deterministic
   R29 September and October selection differentiates explicit supported dates
   R30 Every numeric embedded source value is finite
*/

/* ------------------------------------------------------------ ADAPTED ----- */
/* re-pointed calls, with the reason:
   E.v03run(...)              -> E.calculate(...)              engine entry point, renamed
   E.v03conditionalTest(r)    -> E.conditionalTest(r)          same function, public name
   E.v03rank(c,obj)           -> E.rankAlternatives(c,obj,{payload})   now takes the payload explicitly
   E.v03both(c,a)             -> E.bothObjectives(c,a,{payload})        same
   E.v03baseline(c)           -> E.baseline(c)                  same
   E.v03costForDate(pn,d)     -> E.costForDate(payload,pn,d)    payload now an argument, not a global
   E.v03strip / E.v03audit    -> output/recipients.js memberBrief + buildAllowed
                                 The v03 helpers are gone. The assertion they stood for is kept and
                                 re-pointed at the construction that replaced them.
*/

const engine = H.requireModule(H.PATHS.engine);
const contracts = H.requireModule(H.PATHS.contracts);
// RETIRED-MODULE-USE: src/output/recipients.js - the only module that still exposes
// the v03 strip/audit helpers R25 and R26 were originally written against, and the
// permission/identity stand-in R27b and the module list below record. R25 and R26
// assert on src/data/export.js, the module the build assembles; this load is kept so
// the recorded comparison between the two copies stays visible rather than deleted.
const recipients = H.requireModule(H.PATHS.recipients);
const E = engine;
const data = H.frozenPayload();

/* The frozen payload's own cost basis metadata, reported so an unresolved basis
   is visible rather than assumed. */
run.cost_basis_declared = (data.meta.costBases || []).map(b => ({
  basis_id: b.basis_id, status: b.status,
  offer_effective_from: b.offer_effective_from || null,
  offer_effective_to: b.offer_effective_to ?? null
}));

run.tested_files = H.pin([H.PATHS.engine, H.PATHS.contracts, H.PATHS.recipients,
  H.PATHS.frozen, H.PATHS.scenario, H.PATHS.cases]);

const calc = (extra = {}) => E.calculate(Object.assign({
  price_before: 100, price_after: 100, quantity_before: 100, quantity_after: 100,
  cost_eur: 60, support_eur: 0, scope: 'all', quantity_label: 'manual scenario'
}, extra));

const rankWith = (c, obj) => E.rankAlternatives(c, obj, { payload: data });
const bothWith = (c, a) => E.bothObjectives(c, a, { payload: data });

/* =========================================================== R01 - R18 ===== */

H.test(run, 'R01', 'Unchanged all-volume scenario reconciles', () => {
  const r = calc();
  H.eq(r.ok, true, 'ok');
  H.approx(r.revenue_after, 10000, 1e-8, 'revenue_after');
  H.approx(r.gp_after, 4000, 1e-8, 'gp_after');
  H.approx(r.margin_after_pct, 40, 1e-8, 'margin_after_pct');
  return 'Synthetic price 100, quantity 100, unit cost 60';
});

H.test(run, 'R02', 'Missing cost preserves revenue but not invented profit', () => {
  const r = calc({ cost_eur: null });
  H.eq(r.gp_after, null, 'gp_after');
  H.approx(r.revenue_after, 10000, 1e-8, 'revenue_after');
  return 'gp_after null while revenue stated';
});

H.test(run, 'R03', 'Zero cost is an explicit value', () => {
  const r = calc({ cost_eur: 0 });
  H.approx(r.margin_after_pct, 100, 1e-8, 'margin_after_pct');
  H.eq(r.cost_is_zero, true, 'cost_is_zero');
  return 'cost 0 gives margin 100 and cost_is_zero true';
});

H.test(run, 'R04', 'Negative starting quantity is rejected', () => {
  H.eq(calc({ quantity_before: -1 }).ok, false, 'ok');
  return 'rejected';
});

H.test(run, 'R05', 'Revenue-up/profit-down trade-off is detected', () => {
  const r = calc({ price_after: 90, quantity_after: 125 });
  H.isTrue(r.flags.some(f => f.code === 'REV_UP_GP_DOWN'), 'no REV_UP_GP_DOWN flag on ' + JSON.stringify(r.flags.map(f => f.code)));
  return 'flag REV_UP_GP_DOWN present';
});

H.test(run, 'R06', 'Profit-up/revenue-down trade-off is detected', () => {
  const r = calc({ price_after: 110, quantity_after: 90 });
  H.isTrue(r.flags.some(f => f.code === 'GP_UP_REV_DOWN'), 'no GP_UP_REV_DOWN flag on ' + JSON.stringify(r.flags.map(f => f.code)));
  return 'flag GP_UP_REV_DOWN present';
});

H.test(run, 'R07', 'Simple all-volume price-cut break-even is correct', () => {
  const r = calc({ price_after: 80 });
  H.approx(r.qty_preserve_revenue, 125, 1e-8, 'qty_preserve_revenue');
  H.approx(r.qty_preserve_gp, 200, 1e-8, 'qty_preserve_gp');
  return 'revenue break-even 125, profit break-even 200';
});

H.test(run, 'R08', 'Simple all-volume price-increase loss bound is correct', () => {
  const r = calc({ price_after: 110 });
  H.approx(r.tolerable_loss_revenue_pct, 9.09, 0.001, 'tolerable_loss_revenue_pct');
  return '9.09%';
});

H.test(run, 'R09', 'Incremental scope reports combined margin, not discounted-unit margin', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 120 });
  H.approx(r.revenue_after, 11600, 1e-8, 'revenue_after');
  H.approx(r.gp_after, 4400, 1e-8, 'gp_after');
  H.approx(r.margin_after_pct, 100 * r.gp_after / r.revenue_after, 1e-9, 'margin_after_pct vs reported gp/revenue');
  return `revenue ${r.revenue_after}, gp ${r.gp_after}, margin ${r.margin_after_pct} = reported gp / reported revenue`;
});

H.test(run, 'R10', 'Margin reconciles to reported profit after stated support', () => {
  const r = calc({ support_eur: 500 });
  H.approx(r.gp_after, 3500, 1e-8, 'gp_after');
  H.approx(r.margin_after_pct, 35, 1e-8, 'margin_after_pct');
  return 'support deducted once, margin 35%';
});

H.test(run, 'R11', 'Incremental-only revenue preservation keeps existing price', () => {
  const r = calc({ scope: 'incremental', price_after: 80 });
  H.approx(r.qty_preserve_revenue, 100, 1e-8, 'qty_preserve_revenue');
  return 'existing units already hold revenue';
});

H.test(run, 'R12', 'Incremental-only profit preservation keeps existing contribution', () => {
  const r = calc({ scope: 'incremental', price_after: 80 });
  H.approx(r.qty_preserve_gp, 100, 1e-8, 'qty_preserve_gp');
  return 'existing units already hold gross profit';
});

H.test(run, 'R13', 'Incremental-only support recovery uses additional-unit contribution', () => {
  const r = calc({ scope: 'incremental', price_after: 80, support_eur: 200 });
  H.approx(r.qty_preserve_gp, 110, 1e-8, 'qty_preserve_gp');
  return '100 existing + 10 additional at 20 EUR contribution';
});

H.test(run, 'R14', 'Negative proposed quantity is rejected', () => {
  H.eq(calc({ quantity_after: -1 }).ok, false, 'ok');
  return 'rejected';
});

H.test(run, 'R15', 'Non-finite proposed quantity is rejected', () => {
  H.eq(calc({ quantity_after: NaN }).ok, false, 'ok');
  return 'rejected';
});

H.test(run, 'R16', 'Infinite proposed quantity is rejected', () => {
  H.eq(calc({ quantity_after: Infinity }).ok, false, 'ok');
  return 'rejected';
});

H.test(run, 'R17', 'Invalid support is rejected, not silently replaced with zero', () => {
  H.eq(calc({ support_eur: 'invalid' }).ok, false, 'ok');
  return 'rejected';
});

H.test(run, 'R18', 'Unchanged price with added support does not claim no extra volume is required', () => {
  const r = calc({ support_eur: 500 });
  const txt = E.conditionalTest(r).join(' ');
  H.isTrue(!txt.includes('no volume response is required to hold either'), 'the v03 sentence is still produced: ' + txt);
  return 'wording states the support must be recovered, not that no response is needed';
});

/* =========================================================== R19 - R30 ===== */

H.test(run, 'R19', 'One case ranking uses one gross-profit baseline across alternatives', () => {
  const detail = data.cases.map(c => {
    const ranked = rankWith(c, 'revenue').ranked;
    return { case: c.id, distinct: new Set(ranked.map(x => x.result.gp_before)).size };
  });
  const bad = detail.filter(d => d.distinct > 1).map(d => d.case);
  H.eq(bad.length, 0, 'cases with more than one profit baseline (' + JSON.stringify(detail) + ')');
  return 'one profit baseline per case across ' + data.cases.length + ' cases';
});

H.test(run, 'R20', 'Ranking and both-objective entry points use the same stated quantity', () => {
  const c = data.cases.find(x => x.id === 'ITUK-PADS');
  const a = c.alternatives.find(x => x.alternative_id === 'PADS-VOL');
  const r = rankWith(c, 'revenue').ranked.find(x => x.alternative.alternative_id === a.alternative_id).result;
  const b = bothWith(c, a).result;
  H.approx(b.quantity_after, r.quantity_after, 1e-9, 'quantity_after rank vs both');
  H.approx(b.revenue_change, r.revenue_change, 1e-9, 'revenue_change rank vs both');
  H.approx(b.gp_change, r.gp_change, 1e-9, 'gp_change rank vs both');
  return `both entry points give quantity ${r.quantity_after}`;
});

H.test(run, 'R21', 'Recorded baseline revenue is conserved, or explicitly labelled as a rounded scenario', () => {
  const c = data.cases.find(x => x.id === 'ITUK-PADS');
  const b = E.baseline(c);
  const gap = Math.abs(b.revenue - c.baselineDefined.observed_billing_eur);
  H.isTrue(gap < 0.005 || /rounded.*scenario/i.test(b.basis_statement),
    `historical labelled baseline does not reconcile (gap ${gap}) and is not labelled a rounded scenario: ${b.basis_statement}`);
  return `labelled: ${b.basis_statement}`;
});

H.test(run, 'R22', 'Invalid effective date does not silently select October', () => {
  const r = E.costForDate(data, data.cases[0].pn, 'not-a-date');
  H.isTrue(r === null || r.error || r.ok === false, `returned ${JSON.stringify(r)}`);
  return 'refused rather than defaulted';
});

H.test(run, 'R23', 'Date outside all documented windows is unresolved', () => {
  const r = E.costForDate(data, data.cases[0].pn, '2035-01-01');
  H.isTrue(r === null || r.error || r.ok === false, `returned ${JSON.stringify(r)}`);
  return 'refused rather than defaulted';
});

H.test(run, 'R24', 'Migration without source/target quantities is unresolved, not a computed zero', () => {
  const c = data.cases.find(x => x.id === 'IMOTORS-OIL');
  const row = rankWith(c, 'revenue').ranked.find(x => x.alternative.kind === 'migration');
  H.isTrue(row !== undefined, 'no migration alternative found in the frozen case');
  const r = row.result;
  H.isTrue(!r.ok || r.migration_status === 'unresolved' || r.revenue_change === null,
    'migration is returned as an ordinary unchanged single-part calculation: ' + JSON.stringify({ ok: r.ok, status: r.migration_status, revenue_change: r.revenue_change }));
  return `migration reported unresolved (ok=${r.ok}, status=${r.migration_status})`;
});

H.test(run, 'R25', 'Distributor output does not carry the direct cost field, even when the input does', () => {
  /* ORIGINAL: E.v03strip(calc()) must not keep a `cost` property.
     ADAPTED: the input is deliberately loaded with cost fields, then built for
     a participant. A field nobody declared must not survive, at any depth.

     RE-POINTED 2026-09-22: this was asked of src/output/recipients.js, which
     tools/build.py lists as a "duplicate export builder" and does not assemble.
     src/data/export.js is the builder that decides what a distributor receives.
     The requirement is unchanged: the participant bytes carry no cost field. */
  const shippedExport = H.requireModule(H.PATHS.exportData);
  const engineResult = calc();
  const scenarioForExport = {
    price_before: 100, price_after: 90, quantity_before: 100, quantity_after: 100,
    quantity_label: 'manual scenario', scope: 'all', support_eur: 0,
    cost_eur: 60, cost_basis_id: 'FWD_B', evidence_period: 'synthetic', offer_effective_date: '2025-10-01'
  };
  const caseForExport = { case_id: 'SYNTH', customer: 'Synthetic', part_number: 'SYNTH-PART', unit: 'unit' };
  const metaForExport = { exported_at: '2026-09-22T00:00:00Z' };

  const exportArgs = {
    shipped: shippedExport.memberBrief(caseForExport, scenarioForExport, engineResult, metaForExport),
    retired: recipients.memberBrief({
      case: caseForExport, scenario: scenarioForExport, result: engineResult, meta: metaForExport })
  };
  run.r25_module_comparison = {};
  for (const [which, exported] of Object.entries(exportArgs)) {
    const bytesFor = exported.payload === null
      ? { text: '', length: 0 } : shippedExport.toBytes(exported, false);
    run.r25_module_comparison[which] = {
      module: which === 'shipped' ? 'src/data/export.js' : 'src/output/recipients.js (retired)',
      top_level_cost_key: Object.prototype.hasOwnProperty.call(exported.payload || {}, 'cost'),
      restricted_field_name_in_bytes: /"(cost|cost_eur|gp_after|margin_after_pct)"/.test(bytesFor.text),
      bytes: bytesFor.length
    };
  }

  /* Asserted on the SHIPPED module; the retired module's answer is recorded. */
  const exported = exportArgs.shipped;
  const bytes = exported.payload === null ? { text: '', length: 0 } : shippedExport.toBytes(exported, false);
  H.isTrue(!Object.prototype.hasOwnProperty.call(exported.payload || {}, 'cost'),
    'top-level cost survived in the SHIPPED export module (src/data/export.js)');
  H.isTrue(!/"(cost|cost_eur|gp_after|margin_after_pct)"/.test(bytes.text),
    'restricted field name present in the participant bytes built by the SHIPPED module');
  return `${bytes.length} bytes from src/data/export.js carry no cost, gp or margin field name; `
    + `retired module recorded at run.r25_module_comparison.retired`;
});

H.test(run, 'R26', 'A minimal nested direct-cost object set for a participant is caught or refused', () => {
  /* ORIGINAL: E.v03strip({scenario:{cost:60,margin_pp_change:4}}) must not keep
     scenario.cost, or E.v03audit must report a finding.
     ADAPTED: the allowlist build is the replacement for v03strip.

     RE-POINTED 2026-09-22: asked of the SHIPPED module (src/data/export.js).
     Its allowlist builder and audit are the ones the artifact carries, so this
     assertion is about the product. The retired module's answer is recorded. */
  const shippedExport = H.requireModule(H.PATHS.exportData);
  const nestedCostSource = { scenario: { cost: 60, margin_pp_change: 4 } };
  const answers = {
    shipped: shippedExport.buildAllowed(nestedCostSource, shippedExport.allowlistFor('member')),
    retired: recipients.buildAllowed(nestedCostSource, recipients.allowlistFor('member'))
  };
  const auditOf = {
    shipped: shippedExport.audit(answers.shipped, 'member'),
    retired: recipients.audit(answers.retired, 'member')
  };
  run.r26_module_comparison = {
    shipped_module: 'src/data/export.js',
    shipped_built: answers.shipped,
    shipped_audit_findings: auditOf.shipped.findings,
    retired_module: 'src/output/recipients.js (retired)',
    retired_built: answers.retired,
    retired_audit_findings: auditOf.retired.findings
  };

  const built = answers.shipped;
  const keptCost = built.scenario && Object.prototype.hasOwnProperty.call(built.scenario, 'cost');
  const auditFindings = auditOf.shipped;
  H.isTrue(!keptCost || auditFindings.findings.length > 0,
    'nested cost remains in the SHIPPED module (src/data/export.js) and its audit returns no findings: '
    + JSON.stringify({ built, auditFindings }));
  return `shipped module: nested cost not carried (${JSON.stringify(built)}); audit findings `
    + `${auditFindings.findings.length}; retired module recorded at run.r26_module_comparison.retired`;
});

H.test(run, 'R27', 'Candidate records declare their actual reporting period (original form)', () => {
  /* ORIGINAL, UNCHANGED. The frozen payload is the same data the corrected build
     publishes under a corrected label, so this assertion is still expected to
     fail on the deep data. Kept, not deleted. See R27b for the adapted form. */
  const fields = Object.keys(data.candidateScreen[0] || {});
  H.isTrue(fields.some(k => /^(period|reporting_period|year|date_from|period_start)$/.test(k)),
    'no period or year field in candidate records: ' + fields.join(','));
  return 'period field present';
});

H.test(run, 'R27b', 'Candidate screen declares its reporting basis, and does not infer one', () => {
  /* ADAPTED form of R27, added alongside the original rather than replacing it.
     F10's fix is to declare the basis and refuse to guess the period, so the
     question becomes: does the screen say what its basis is, and does it refuse
     to promote a record whose period is undeclared? */
  const cand = H.requireModule(H.PATHS.candidates);
  const basis = cand.reportingBasis(data.candidateScreen);
  H.eq(basis.declared, false, 'basis.declared');
  H.isTrue(/undeclared|no reporting period/i.test(basis.statement), 'statement does not declare the gap: ' + basis.statement);
  const blockers = cand.promotionBlockers(data.candidateScreen[0], data).blockers.map(b => b.code);
  H.isTrue(blockers.indexOf('PERIOD_UNDECLARED') >= 0, 'PERIOD_UNDECLARED not among the promotion blockers: ' + JSON.stringify(blockers));
  return `basis declared=${basis.declared}; blockers ${JSON.stringify(blockers)}`;
});

H.test(run, 'R28', 'Same-scenario arithmetic is deterministic', () => {
  H.eq(JSON.stringify(calc({ price_after: 90 })), JSON.stringify(calc({ price_after: 90 })), 'two runs');
  return 'identical output for identical input';
});

H.test(run, 'R29', 'September and October selection differentiates explicit supported dates', () => {
  /* ORIGINAL, UNCHANGED. The payload declares OCT26 as its default forward
     basis with offer_effective_from 2026-10-01 and no declared end. */
  const a = E.costForDate(data, data.cases[0].pn, '2026-09-22');
  const b = E.costForDate(data, data.cases[0].pn, '2026-10-01');
  H.eq(a && a.basis_id, 'SEP26', 'basis for 2026-09-22');
  H.eq(b && b.basis_id, 'OCT26', 'basis for 2026-10-01');
  return 'SEP26 for September, OCT26 for October';
});

H.test(run, 'R30', 'Every numeric embedded source value is finite', () => {
  const walk = x => {
    if (typeof x === 'number') H.isTrue(Number.isFinite(x), 'non-finite number in the payload');
    else if (x && typeof x === 'object') Object.values(x).forEach(walk);
  };
  walk(data);
  return 'no NaN or Infinity in the embedded payload';
});

/* ===================================================== reviewer additions === */

run.results.push({ id: 'A01', name: '--- reviewer additions below this line ---', status: 'PASS', evidence: 'separator', separator: true });
run.results.pop();

H.test(run, 'A01', 'Every case and alternative: ranking and both-objective agree on quantity and on both results', () => {
  const rows = [];
  for (const c of data.cases) {
    const ranked = rankWith(c, 'revenue').ranked;
    for (const row of ranked) {
      const twin = bothWith(c, row.alternative).result;
      const same = (x, y) => (x === null && y === null) || (x !== null && y !== null && Math.abs(x - y) < 1e-9);
      if (!same(twin.quantity_after, row.result.quantity_after)
        || !same(twin.revenue_change, row.result.revenue_change)
        || !same(twin.gp_change, row.result.gp_change)) {
        rows.push({ case: c.id, alternative: row.alternative.alternative_id,
          rank: { q: row.result.quantity_after, rev: row.result.revenue_change, gp: row.result.gp_change },
          both: { q: twin.quantity_after, rev: twin.revenue_change, gp: twin.gp_change } });
      }
    }
  }
  H.eq(rows.length, 0, 'disagreements: ' + JSON.stringify(rows));
  const n = data.cases.reduce((s, c) => s + (c.alternatives || []).length, 0);
  return `all ${n} alternatives across ${data.cases.length} cases agree`;
});

H.test(run, 'A02', 'All-volume arithmetic: revenue and profit both equal the stated definition', () => {
  const r = calc({ price_after: 90, quantity_after: 130, cost_eur: 55, support_eur: 400 });
  H.approx(r.revenue_after, 90 * 130, 1e-9, 'revenue_after = price x total quantity');
  H.approx(r.gp_after, 90 * 130 - 55 * 130 - 400, 1e-9, 'gp_after = revenue - cost of goods - support');
  H.approx(r.margin_after_pct, 100 * r.gp_after / r.revenue_after, 1e-9, 'margin = reported gp / reported revenue');
  H.eq(r.support_counted_once, true, 'support_counted_once');
  H.eq(r.bridge_reconciles, true, 'bridge_reconciles');
  return `revenue ${r.revenue_after}, gp ${r.gp_after}, bridge reconciles`;
});

H.test(run, 'A03', 'Incremental arithmetic keeps existing units at the old price and counts support once', () => {
  const r = calc({ scope: 'incremental', price_after: 90, quantity_after: 130, cost_eur: 55, support_eur: 400 });
  H.approx(r.revenue_after, 100 * 100 + 90 * 30, 1e-9, 'revenue = unchanged units at old price + extra at new price');
  H.approx(r.gp_after, 100 * 100 + 90 * 30 - 55 * 130 - 400, 1e-9, 'gp after support');
  H.approx(r.extra_quantity, 30, 1e-9, 'extra_quantity');
  H.approx(r.discount_on_existing_volume_eur, 0, 1e-9, 'no discount given away on already-buying units');
  H.eq(r.bridge_reconciles, true, 'bridge_reconciles');
  return `revenue ${r.revenue_after}, gp ${r.gp_after}, extra units ${r.extra_quantity}`;
});

H.test(run, 'A04', 'Incremental-only refuses a proposed total below the existing quantity', () => {
  const r = calc({ scope: 'incremental', price_after: 90, quantity_after: 40 });
  H.eq(r.ok, false, 'ok');
  H.isTrue(/fewer units/i.test(r.error || ''), 'error does not name the impossible assumption: ' + r.error);
  return 'refused rather than clamped: ' + r.error;
});

H.test(run, 'A05', 'Zero and negative contribution are unresolved, not a silent quantity', () => {
  const atCost = calc({ price_after: 60, quantity_after: 100 });
  H.isTrue(atCost.qty_preserve_gp === null, 'profit break-even stated although price does not exceed cost: ' + atCost.qty_preserve_gp);
  H.isTrue(/not attainable/i.test(atCost.qty_preserve_gp_label || ''), 'label does not say the target is unattainable: ' + atCost.qty_preserve_gp_label);
  const belowCost = calc({ price_after: 50 });
  H.isTrue(belowCost.qty_preserve_gp === null, 'profit break-even stated below cost');
  H.isTrue(belowCost.flags.some(f => f.code === 'PRICE_AT_OR_BELOW_COST'), 'missing PRICE_AT_OR_BELOW_COST flag');
  const incBelowCost = calc({ scope: 'incremental', price_after: 50, quantity_after: 120, support_eur: 300 });
  H.isTrue(incBelowCost.qty_preserve_gp === null, 'incremental profit break-even stated although no unit recovers support');
  return 'at-cost, below-cost and incremental-below-cost all unresolved with a reason';
});

H.test(run, 'A06', 'Pack rounding: "more than" is the smallest orderable quantity above the threshold', () => {
  const one = calc({ price_after: 80, pack_size: 1 });
  H.approx(one.qty_preserve_revenue, 125, 1e-9, 'threshold at pack 1');
  H.eq(one.extra_qty_to_exceed_revenue, 26, 'smallest order above 125 at pack 1 (125 + 1 - 100)');
  const fifty = calc({ price_after: 80, pack_size: 50 });
  H.eq(fifty.extra_qty_to_exceed_revenue, 50, 'smallest order above 125 at pack 50 (150 - 100)');
  const twelve = calc({ price_after: 80, pack_size: 12 });
  /* smallestPackAbove(125, 12) = floor(125/12)*12 + 12 = 120 + 12 = 132, less the
     base quantity of 100 = 32. The orderable total is 132, which is above 125. */
  H.eq(twelve.extra_qty_to_exceed_revenue, 32, 'smallest order above 125 at pack 12 (132 - 100)');
  H.isTrue(fifty.extra_qty_to_exceed_revenue + fifty.quantity_before > fifty.qty_preserve_revenue,
    'the orderable quantity must be strictly above the threshold');
  H.isTrue(twelve.extra_qty_to_exceed_revenue + twelve.quantity_before > twelve.qty_preserve_revenue,
    'the orderable quantity must be strictly above the threshold');
  return 'pack 1 -> 26, pack 12 -> 32, pack 50 -> 50, each strictly above the 125 threshold';
});

H.test(run, 'A07', 'Invalid pack size is refused rather than treated as one', () => {
  H.eq(calc({ pack_size: 0 }).ok, false, 'pack_size 0');
  H.eq(calc({ pack_size: -5 }).ok, false, 'pack_size -5');
  H.eq(calc({ pack_size: 'many' }).ok, false, 'pack_size "many"');
  return 'zero, negative and non-numeric pack sizes all refused';
});

H.test(run, 'A08', 'Blank proposed quantity means the recorded quantity, and says so', () => {
  const r = calc({ quantity_after: null });
  H.eq(r.ok, true, 'ok');
  H.approx(r.quantity_after, 100, 1e-9, 'quantity_after falls back to the base quantity');
  H.isTrue(r.conditional.some(c => /recorded quantity/i.test(c)), 'no statement that the quantity is the recorded one');
  return 'blank falls back to 100 with a stated condition';
});

H.test(run, 'A09', 'A proposed quantity of zero is a withdrawal, not a pricing scenario', () => {
  const r = calc({ quantity_after: 0 });
  H.eq(r.ok, false, 'ok');
  H.isTrue(/withdrawal/i.test(r.error || ''), 'error does not name withdrawal: ' + r.error);
  return r.error;
});

H.test(run, 'A10', 'Cost basis selection refuses an undeclared end date instead of defaulting forward', () => {
  /* The payload declares OCT26 with offer_effective_from 2026-10-01 and no end.
     The engine treats an undeclared end as unresolved. This records the
     consequence for the default forward basis. */
  const basis = (data.meta.costBases || []).find(b => b.basis_id === data.meta.defaultForwardBasis);
  const r = E.costForDate(data, data.cases[0].pn, basis.offer_effective_from);
  H.isTrue(r && r.ok === true && r.basis_id === basis.basis_id,
    `the engine cannot select the payload's own default forward basis ${basis.basis_id} from its own from-date ${basis.offer_effective_from}: ${JSON.stringify(r)}`);
  return `${basis.basis_id} selected from ${basis.offer_effective_from}`;
});

H.test(run, 'A11', 'Every returned numeric output is finite or null', () => {
  const scenarios = [
    {}, { price_after: 80 }, { price_after: 140 }, { support_eur: 500 },
    { scope: 'incremental', price_after: 80, support_eur: 200 },
    { cost_eur: null }, { cost_eur: 0 }, { quantity_after: null },
    { quantity_after: 500 }, { pack_size: 24, price_after: 95 }
  ];
  const bad = [];
  scenarios.forEach((s, i) => {
    const r = calc(s);
    Object.keys(r).forEach(k => {
      const v = r[k];
      if (typeof v === 'number' && !Number.isFinite(v)) bad.push({ scenario: i, field: k, value: String(v) });
    });
  });
  H.eq(bad.length, 0, 'non-finite outputs: ' + JSON.stringify(bad));
  return `${scenarios.length} scenarios, every numeric output finite or null`;
});

H.test(run, 'A12', 'The same alternative cannot produce two different quantities through two entry points, in any case', () => {
  const rows = [];
  for (const c of data.cases) {
    const byAlt = {};
    rankWith(c, 'revenue').ranked.forEach(r => { byAlt[r.alternative.alternative_id] = r.result.quantity_after; });
    for (const a of c.alternatives || []) {
      const q = bothWith(c, a).result.quantity_after;
      if (byAlt[a.alternative_id] !== undefined && byAlt[a.alternative_id] !== q) {
        rows.push({ case: c.id, alternative: a.alternative_id, rank: byAlt[a.alternative_id], both: q });
      }
    }
  }
  H.eq(rows.length, 0, 'quantity disagreements: ' + JSON.stringify(rows));
  return 'one normalisation across both entry points';
});

H.test(run, 'A13', 'Ranking order is deterministic and depends only on the selected objective', () => {
  for (const c of data.cases) {
    const a = rankWith(c, 'revenue').ranked.map(r => r.alternative.alternative_id);
    const b = rankWith(c, 'revenue').ranked.map(r => r.alternative.alternative_id);
    H.eq(JSON.stringify(a), JSON.stringify(b), `${c.id} revenue order repeats`);
    const g = rankWith(c, 'grossProfit').ranked.map(r => r.alternative.alternative_id);
    H.eq(g.length, a.length, `${c.id} both objectives rank the same alternatives`);
  }
  return 'stable order per objective across ' + data.cases.length + ' cases';
});

H.test(run, 'A14', 'Changing the objective changes ordering, never the assumptions', () => {
  const rows = [];
  for (const c of data.cases) {
    const rev = rankWith(c, 'revenue').ranked;
    const gp = rankWith(c, 'grossProfit').ranked;
    rev.forEach(r => {
      const twin = gp.find(x => x.alternative.alternative_id === r.alternative.alternative_id);
      if (!twin) { rows.push({ case: c.id, alternative: r.alternative.alternative_id, issue: 'missing under the other objective' }); return; }
      if (twin.result.quantity_after !== r.result.quantity_after
        || twin.result.price_after !== r.result.price_after
        || twin.result.revenue_change !== r.result.revenue_change
        || twin.result.gp_change !== r.result.gp_change) {
        rows.push({ case: c.id, alternative: r.alternative.alternative_id, issue: 'result changed with the objective' });
      }
    });
    H.eq(JSON.stringify(rev.map(x => x.alternative.alternative_id).slice().sort()),
      JSON.stringify(gp.map(x => x.alternative.alternative_id).slice().sort()),
      `${c.id} same alternative set under both objectives`);
  }
  H.eq(rows.length, 0, 'objective changed an assumption or a result: ' + JSON.stringify(rows));
  return 'ordering is the only thing that moves between objectives';
});

H.test(run, 'A15', 'Gross margin is never the margin on the discounted units only, once support is stated', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 120, support_eur: 1000 });
  H.approx(r.gp_after, 11600 - 120 * 60 - 1000, 1e-9, 'gp_after');
  H.approx(r.margin_after_pct, 100 * r.gp_after / r.revenue_after, 1e-9, 'combined margin');
  H.isTrue(Math.abs(r.margin_after_pct - r.margin_unit_after_pct) > 1e-6,
    'the unit margin and the combined margin must be distinguishable, not the same number');
  H.isTrue(r.margin_unit_after_pct !== null, 'unit margin is stated separately and labelled');
  return `combined ${r.margin_after_pct}% vs unit ${r.margin_unit_after_pct}%, both stated`;
});

H.test(run, 'A16', 'A missing cost states revenue and refuses to state profit', () => {
  const r = calc({ cost_eur: null, price_after: 85 });
  H.approx(r.revenue_after, 85 * 100, 1e-9, 'revenue still stated');
  H.eq(r.gp_after, null, 'gp_after');
  H.eq(r.margin_after_pct, null, 'margin_after_pct');
  H.eq(r.cost_missing_not_zero, true, 'cost_missing_not_zero');
  H.isTrue(r.conditional.some(c => /not calculated/i.test(c)), 'no statement that profit is not calculated');
  return 'revenue stated, profit and margin withheld with a reason';
});

/* ----------------------------------------------------------------- output -- */

run.modules_loaded_from = {
  engine: path.relative(H.ROOT, H.PATHS.engine).replace(/\\/g, '/'),
  contracts: path.relative(H.ROOT, H.PATHS.contracts).replace(/\\/g, '/'),
  recipients: path.relative(H.ROOT, H.PATHS.recipients).replace(/\\/g, '/')
};
run.scope = 'Independent acceptance check of the corrected calculation module. Synthetic arithmetic. '
  + 'Does not validate the underlying supplier workbooks, FX authority, cost eligibility, commercial '
  + 'approval, production access or identity.';
run.note_on_brief_naming = 'The task brief names src/engine/pricing.js. No such file exists in this '
  + 'build. The maintained engine is src/engine/engine.js and that is what was tested; its checksum '
  + 'is pinned in tested_files.';

const s = H.write(run, 'accept_01_engine.json');
process.exitCode = H.exitCode(s);
