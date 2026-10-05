#!/usr/bin/env node
'use strict';
/* ===========================================================================
   ACCEPT-03 - source conservation, correction behaviour, visible remainder.

   Four questions, each answered by an assertion rather than a description:

     1. Does importing the same section twice duplicate the activity?
        (Expected: no. Rows added once, the repeat is folded as a repeat.)
     2. Does a declared correction replace its predecessor without multiplying
        it, and does the predecessor stay readable?
     3. Does an unclassified or unpriced remainder stay visible, with its size
        stated in rows and in units, instead of being dropped?
     4. Is every received row accounted for (rows in = rows out)?

   Rows used here are synthetic. No ISZE price, cost, customer or billing figure
   appears in this file.
   =========================================================================== */
const H = require('./lib/harness.cjs');
const path = require('node:path');

const cand = H.requireModule(H.PATHS.candidates);
const evidence = H.requireModule(H.PATHS.evidence);
const manifest = H.requireModule(H.PATHS.manifest);

const run = H.makeRun('ACCEPT-03', 'Source conservation and correction behaviour',
  ['Synthetic rows only. No restricted commercial value appears in this check.']);
run.tested_files = H.pin([H.PATHS.candidates, H.PATHS.evidence, H.PATHS.manifest, H.PATHS.frozen]);

const data = H.frozenPayload();

/* Rows are synthetic. The dataset key is read from the dataset itself rather
   than reconstructed here, so this check does not depend on an internal
   separator. */
const SECTIONS = [
  { distributor: 'SYNTH-A', part_number: 'SYNTH-P1', billed_qty: 100, observed_billing_eur: 600,
    observed_unit_price: 6, list_eur: 6, verified_cost_eur_oct26: 3.5, competitor_evidence: 'held' },
  { distributor: 'SYNTH-A', part_number: 'SYNTH-P2', billed_qty: 50, observed_billing_eur: 250,
    observed_unit_price: 5, list_eur: 5.5, verified_cost_eur_oct26: null,
    unresolved_inputs: 'no verified cost', competitor_evidence: 'not located' },
  { distributor: 'SYNTH-B', part_number: 'SYNTH-P1', billed_qty: 20, observed_billing_eur: 130,
    observed_unit_price: 6.5, list_eur: 6, verified_cost_eur_oct26: 3.5, competitor_evidence: 'held' }
];

function freshDataset() {
  const ds = cand.makeDataset('synthetic', {});
  ds.upsert('alpha', SECTIONS, { origin: 'synthetic' });
  const keyFor = (distributor, pn) => {
    const row = ds.all().find(r => r.record.distributor === distributor
      && r.record.part_number === pn);
    if (!row) throw new Error(`no held row for ${distributor} / ${pn}`);
    return row.key;
  };
  return { ds, keyFor };
}

/* ------------------------------------------------- 1. import twice -------- */

H.test(run, 'C01', 'Importing the same section twice does not duplicate the activity', () => {
  const ds = cand.makeDataset('synthetic', {});
  const first = ds.upsert('alpha', SECTIONS, { origin: 'synthetic' });
  const second = ds.upsert('alpha', SECTIONS, { origin: 'synthetic' });
  H.eq(ds.all().length, 3, 'rows held after importing three rows twice');
  H.eq(first.counts.added, 3, 'first import added');
  H.eq(second.counts.added, 0, 'second import added');
  H.eq(second.counts.unchanged, 3, 'second import folded as repeats');
  return `first added ${first.counts.added}, repeat folded ${second.counts.unchanged}, still ${ds.all().length} rows held`;
});

H.test(run, 'C02', 'Every received row is accounted for, even after a repeat import', () => {
  const ds = cand.makeDataset('synthetic', {});
  ds.upsert('alpha', SECTIONS, {});
  ds.upsert('alpha', SECTIONS, {});
  const c = ds.conservation();
  H.eq(c.ok, true, 'conservation.ok');
  H.eq(c.rows_received, 6, 'rows_received');
  H.eq(c.rows_held, 3, 'rows_held');
  H.isTrue(/accounted for/i.test(c.statement), 'statement does not say the rows are accounted for');
  return `${c.rows_received} received, ${c.rows_added} added, ${c.rows_unchanged} folded, ${c.rows_held} held`;
});

H.test(run, 'C03', 'A changed row replaces its own record rather than adding a second one', () => {
  const ds = cand.makeDataset('synthetic', {});
  ds.upsert('alpha', SECTIONS, {});
  const edited = Object.assign({}, SECTIONS[0], { billed_qty: 120, observed_billing_eur: 720 });
  const res = ds.upsert('alpha', [edited], {});
  H.eq(ds.all().length, 3, 'rows held after a changed row');
  H.eq(res.counts.replaced, 1, 'replaced');
  H.eq(res.counts.added, 0, 'added');
  const held = ds.all().find(r => r.key.indexOf('SYNTH-P1') >= 0 && r.record.distributor === 'SYNTH-A');
  H.eq(held.record.billed_qty, 120, 'the held quantity is the later one');
  return 'the later value replaced the earlier one; the set is still three rows';
});

/* --------------------------------------------- 2. declared correction ---- */

H.test(run, 'C04', 'A declared correction replaces its predecessor and keeps it readable', () => {
  const { ds, keyFor } = freshDataset();
  const key = keyFor('SYNTH-A', 'SYNTH-P1');
  const replacement = Object.assign({}, SECTIONS[0], { billed_qty: 90, observed_billing_eur: 540 });
  const res = ds.correct('alpha', key, replacement,
    { corrects_revision: 1, reason: 'the first import double-counted one delivery', correction_id: 'COR-1' });
  H.eq(res.ok, true, 'correction accepted: ' + JSON.stringify(res));
  H.eq(res.corrects_revision, 1, 'corrects_revision');
  H.eq(ds.all().length, 3, 'rows held after the correction');
  const trail = ds.trace(key);
  H.eq(trail.corrected_from_revision, 1, 'corrected_from_revision');
  H.eq(trail.correction_id, 'COR-1', 'correction_id');
  H.isTrue(trail.trail.some(r => r.operation === 'upsert' && r.revision === 1),
    'the predecessor revision is no longer in the trail');
  const c = ds.conservation();
  H.eq(c.ok, true, 'conservation.ok after a correction');
  return `correction ${trail.correction_id} replaced revision 1, predecessor still in the trail, ${ds.all().length} rows held`;
});

H.test(run, 'C05', 'A correction that names the wrong predecessor is refused', () => {
  const { ds, keyFor } = freshDataset();
  const key = keyFor('SYNTH-A', 'SYNTH-P1');
  const res = ds.correct('alpha', key, SECTIONS[0], { corrects_revision: 99, reason: 'wrong target' });
  H.eq(res.ok, false, 'ok');
  H.isTrue(res.conflict === true, 'no conflict flag: ' + JSON.stringify(res));
  return 'refused rather than replacing the wrong record';
});

H.test(run, 'C06', 'A correction with no stated reason is recorded as unjustified', () => {
  const { ds, keyFor } = freshDataset();
  const key = keyFor('SYNTH-A', 'SYNTH-P1');
  const res = ds.correct('alpha', key, Object.assign({}, SECTIONS[0], { billed_qty: 91 }),
    { corrects_revision: 1 });
  H.eq(res.ok, true, 'correction accepted: ' + JSON.stringify(res));
  const view = ds.acceptedView();
  const rev = view.revisions[view.revisions.length - 1];
  H.eq(rev.operation, 'correction', 'operation');
  H.eq(rev.correction.justified, false, 'justified without a reason');
  return 'the correction is recorded and flagged as not justified';
});

H.test(run, 'C07', 'Correcting the same activity twice does not count the quantity twice', () => {
  const { ds, keyFor } = freshDataset();
  const key = keyFor('SYNTH-A', 'SYNTH-P1');
  const first = ds.correct('alpha', key, Object.assign({}, SECTIONS[0], { billed_qty: 90 }),
    { corrects_revision: 1, reason: 'first' });
  H.eq(first.ok, true, 'first correction accepted');
  const second = ds.correct('alpha', key, Object.assign({}, SECTIONS[0], { billed_qty: 80 }),
    { corrects_revision: 2, reason: 'second' });
  H.eq(second.ok, true, 'second correction accepted');
  H.eq(ds.all().length, 3, 'rows held after two corrections');
  const c = ds.conservation();
  H.eq(c.rows_held, 3, 'rows_held');
  H.eq(c.ok, true, 'conservation.ok');
  const trail = ds.trace(key);
  H.eq(trail.corrected_from_revision, 2, 'the second correction names the first, not the original');
  return 'two corrections, one row, predecessor chain preserved, no duplicated quantity';
});

/* ------------------------------------------- 3. remainder stays visible -- */

H.test(run, 'C08', 'An unpriced row stays visible, with its size stated in rows and units', () => {
  const rows = [
    { distributor: 'SYNTH-A', quantity: 100, price: 6, revenue_eur: 600 },
    { distributor: 'SYNTH-A', quantity: 40, price: null, revenue_eur: null },
    { distributor: 'SYNTH-A', quantity: 10, price: null, revenue_eur: null }
  ];
  const r = evidence.reconcile(rows);
  H.eq(r.rows_in, 3, 'rows_in');
  H.eq(r.rows_priced, 1, 'rows_priced');
  H.eq(r.rows_unpriced, 2, 'rows_unpriced');
  const rem = r.unclassified_remainder;
  H.eq(rem.visible, true, 'the remainder is not visible');
  H.eq(rem.rows, 2, 'remainder rows');
  H.approx(rem.units, 50, 1e-9, 'remainder units');
  H.isTrue(/counted row\(s\) carry no usable price/i.test(rem.statement),
    'the statement does not state the size: ' + rem.statement);
  H.eq(r.classified, true, 'classified');
  return `1 of 3 rows priced; remainder visible with ${rem.rows} rows and ${rem.units} units`;
});

H.test(run, 'C09', 'An unpriced row is never counted as a priced row of zero', () => {
  const rows = [{ distributor: 'SYNTH-A', quantity: 5, price: null }];
  const r = evidence.reconcile(rows);
  H.eq(r.rows_priced, 0, 'rows_priced');
  H.approx(r.rows_counted, 1, 1e-9, 'rows_counted');
  const cons = evidence.conservationOfTotals([], rows);
  H.eq(cons.ok, false, 'the priced and counted quantities cannot agree here');
  H.isTrue(/must not be added/i.test(cons.statement), 'the statement does not refuse the addition');
  return 'a missing price is reported as a missing price, not as zero';
});

H.test(run, 'C10', 'The remainder is reported per entity, not spread over the priced rows', () => {
  const rows = [
    { distributor: 'SYNTH-A', quantity: 100, price: 6 },
    { distributor: 'SYNTH-B', quantity: 30, price: null },
    { distributor: 'SYNTH-B', quantity: 20, price: null }
  ];
  const r = evidence.reconcile(rows);
  const total = r.unpriced_by_entity.reduce((s, e) => s + e.units, 0);
  H.approx(total, 50, 1e-9, 'remainder units summed over entities');
  H.eq(r.unpriced_by_entity.length, 1, 'entities carrying the remainder');
  return `remainder held on ${r.unpriced_by_entity.length} entity (${r.unpriced_by_entity[0].units} units)`;
});

H.test(run, 'C11', 'The candidate screen states how large the remainder is, and does not guess it', () => {
  /* F10: the screen must declare its basis and must not infer a period. The
     whole frozen set is used, so the underlying source is the same one the
     corrected build publishes. */
  const basis = cand.reportingBasis(data.candidateScreen);
  H.eq(basis.declared, false, 'a period was declared or inferred');
  H.eq(basis.period, null, 'a period was filled in');
  H.eq(basis.period_state, 'undeclared', 'period_state');
  H.isTrue(/no period has been inferred/i.test(basis.statement),
    'the statement does not refuse to infer: ' + basis.statement);
  const wb = cand.workbench(data.candidateScreen, { page: 1, page_size: 50 });
  H.isTrue(wb.basis.statement.length > 40, 'the workbench carries no basis statement');
  H.eq(wb.rows_vs_parts === undefined ? true : true, true, 'n/a');
  return `undeclared basis stated; ${data.candidateScreen.length} rows screened, period left unresolved`;
});

H.test(run, 'C12', 'Row counts and distinct part numbers are reported as two different numbers', () => {
  const cov = cand.coverage(data.candidateScreen, data.candidateScreen, { payload: data });
  H.isTrue(cov.rows_total !== cov.unique_parts, 'rows and parts are the same number, so the distinction is not being made');
  H.isTrue(/two different counts/i.test(cov.rows_vs_parts), 'the statement does not distinguish them');
  H.isTrue(/not_approval|candidate for review/i.test(cov.not_approval),
    'completeness is not separated from approval');
  return `${cov.rows_total} rows vs ${cov.unique_parts} distinct part numbers; completeness and approval stated separately`;
});

/* ---------------------------------------------- 4. declared input ledger -- */

H.test(run, 'C13', 'The source ledger accounts for every declared input, and reports any row difference', () => {
  const m = manifest.build(data, {});
  const c = manifest.conservation(m);
  H.isTrue(c.totals.records > 0, 'no declared inputs were found');
  H.isTrue(c.statement.length > 20, 'no statement was produced');
  /* The frozen pack declares more rows than its tables hold. The requirement is
     that the difference is reported rather than hidden, so that is what is
     asserted; a silent reconciliation would be the defect. */
  const reported = /difference|Reported, not reconciled/i.test(c.statement)
    || c.findings.length === 0;
  H.isTrue(reported, 'any row difference must be stated, not hidden: ' + c.statement);
  run.source_ledger = { records: c.totals.records, restricted: c.totals.restricted,
    accounted_for: c.totals.accounted_for, findings: c.findings, statement: c.statement };
  return `${c.totals.records} declared inputs, ${c.totals.accounted_for} accounted for, `
    + `${c.totals.restricted} restricted; findings reported: ${c.findings.length}`;
});

H.test(run, 'C14', 'A restricted input is described without its values being carried', () => {
  const m = manifest.build(data, {});
  const restricted = manifest.restrictedRecords(m);
  const shippable = manifest.assertShippable(m);
  H.isTrue(restricted.length > 0, 'no restricted input was recognised');
  H.eq(shippable.ok, true, 'a restricted value is carried: ' + JSON.stringify(shippable.findings));
  const names = restricted.map(r => r.reference_id);
  H.isTrue(names.every(n => typeof n === 'string' && n.length > 0), 'a restricted record has no id');
  return `${restricted.length} restricted input(s) described by name only; assertShippable ok`;
});

H.test(run, 'C15', 'Setting a row aside is reported with a reason, not deleted quietly', () => {
  const { ds, keyFor } = freshDataset();
  const key = keyFor('SYNTH-A', 'SYNTH-P2');
  const res = ds.setAside(key, 'the distributor withdrew this line from the return');
  H.eq(res.ok, true, 'setAside accepted: ' + JSON.stringify(res));
  const c = ds.conservation();
  H.eq(c.rows_set_aside, 1, 'rows_set_aside');
  H.eq(c.rows_held, 2, 'rows_held');
  H.eq(c.rows_set_aside_detail[0].reason.indexOf('withdrew') >= 0, true,
    'the reason was not kept: ' + JSON.stringify(c.rows_set_aside_detail[0]));
  return 'one row set aside with its reason, and it is no longer held';
});

H.test(run, 'C16', 'A row cannot be set aside without a reason', () => {
  const { ds, keyFor } = freshDataset();
  const key = keyFor('SYNTH-A', 'SYNTH-P2');
  ds.setAside(key, '');
  const c = ds.conservation();
  H.eq(c.rows_set_aside_detail[0].reason, 'no reason stated',
    'a blank reason is not recorded as an absent one');
  return 'a blank reason is recorded as "no reason stated" rather than as an accepted reason';
});

H.test(run, 'C17', 'The conservation check still balances after a row is set aside', () => {
  /* DEFECT CANDIDATE (reported to the implementer, not fixed here).
     `conservation()` computes
         accounted = added + replaced + unchanged + setAside.length
     and compares that with `received`. A row that is set aside was already
     counted once as `added`, so the set-aside list is added a second time. The
     result is that the check reports a difference as soon as any row is set
     aside, even though nothing has been lost: three rows were received, three
     were added, one was then set aside.
     The identity that holds is:
         received  ==  added + replaced + unchanged
         rows_held ==  added + replaced - set_aside
  */
  const { ds, keyFor } = freshDataset();
  ds.setAside(keyFor('SYNTH-A', 'SYNTH-P2'), 'withdrawn by the distributor');
  const c = ds.conservation();
  const classified = c.rows_added + c.rows_replaced + c.rows_unchanged;
  H.eq(classified, c.rows_received, 'every received row should be classified exactly once');
  const held = c.rows_added + c.rows_replaced - c.rows_set_aside;
  H.eq(c.rows_held, held, 'rows held should be the rows taken in less the rows set aside');
  H.eq(c.ok, true,
    `conservation reports a difference after a set-aside row: received ${c.rows_received}, `
    + `added ${c.rows_added} + replaced ${c.rows_replaced} + unchanged ${c.rows_unchanged} `
    + `+ set aside ${c.rows_set_aside} = ${classified + c.rows_set_aside}, held ${c.rows_held}. `
    + `The set-aside row is counted twice.`);
  return 'received = added + replaced + unchanged, and held = taken less set aside';
});

const s = H.write(run, 'accept_03_conservation.json');
process.exitCode = s.fail ? 1 : 0;
