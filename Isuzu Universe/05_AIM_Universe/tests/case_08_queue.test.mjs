#!/usr/bin/env node
/* ===========================================================================
   CASE-08 acceptance tests: an actionable internal queue and reusable history.

   How to run
     node --test tests/case_08_queue.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (CASE-08):
     E1  A due item opens its exact case and outstanding obligation.
     E2  Searching a part does not reveal restricted cases or count another
         organisation's private records.

   src/case/store.js is loaded as case_store.test.mjs loads it, on the memory
   adapter with a fixed clock. Every case, organisation and part below is
   invented. The restricted payload is never read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';

const schema = (await import(new URL('../src/case/schema.js', import.meta.url))).default;
const store = (await import(new URL('../src/case/store.js', import.meta.url))).default;
const exportModule = (await import(new URL('../src/data/export.js', import.meta.url))).default;

const FIXED_NOW = '2026-09-22T10:00:00.000Z';
const AS_OF = '2026-09-22';
const ORG_A = 'Synthetic distributor A';
const ORG_B = 'Synthetic distributor B';
const PART = 'SYNTH-PART-Q';

function newService() {
  return store.makeCaseService({ adapter: store.makeMemoryAdapter(), now: () => FIXED_NOW,
    caller: 'test-runner', identityMode: 'development-only' });
}

const scenarioFor = (id) => ({
  scenario_id: id + ':v3', version: 3, case_id: id, part_number: PART, unit: 'unit',
  price_before: 100, price_after: 96, quantity_before: 100, quantity_after: 110,
  quantity_label: 'manual scenario', scope: 'incremental', volume_is_observed: false,
  pack_size: 1, cost_eur: 60, cost_basis_id: 'SYNTH_B', cost_basis_source: 'verified record',
  support_eur: 0, evidence_period: 'synthetic half year', offer_effective_date: '2026-10-01',
  sources: [], selected_alternative_id: 'SYNTH-INC', objective: 'revenue'
});

function seedCase(service, id, customer, part, due, extra) {
  const created = service.create({ case_id: id, customer, market: 'SYNTH', part_number: part,
    description: 'Synthetic part', owner_role: 'case_owner', by: 'test-runner',
    scope_note: 'Synthetic. No real part, customer or price appears in this test.' });
  assert.equal(created.ok, true, created.error);
  const submitted = service.transition(id, { action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to send the comparable quotation for ' + id, next_update_due: due,
    note: 'Submitted' }, { expected_version: created.version });
  assert.equal(submitted.ok, true, submitted.error);
  const saved = service.saveRecord(Object.assign(schema.clone(service.get(id)),
    { scenario: scenarioFor(id) }, extra || {}), { expected_version: submitted.version });
  assert.equal(saved.ok, true, saved.error);
  return saved.version;
}

function build() {
  const service = newService();
  seedCase(service, 'SYN-CASE-A', ORG_A, PART, '2026-09-20');
  seedCase(service, 'SYN-CASE-B', ORG_B, PART, '2026-10-10');
  seedCase(service, 'SYN-CASE-C', ORG_A, PART, '2026-10-12',
    { sources: [{ reference_id: 'SYN-SRC-1', kind: 'supplier cost', title: 'Synthetic restricted source', restricted: true }] });
  seedCase(service, 'SYN-CASE-D', ORG_A, 'SYNTH-PART-OTHER', '2026-10-15');
  return service;
}

test('CASE-08 E1: a due item opens its exact case and outstanding obligation', () => {
  const service = build();
  const due = service.queue(AS_OF);
  assert.equal(due[0].case_id, 'SYN-CASE-A', 'the overdue item is not first in the queue');

  const opened = service.openQueueItem(due[0].case_id, AS_OF);
  assert.equal(opened.ok, true, opened.error);
  const stored = service.get('SYN-CASE-A');
  assert.equal(opened.case_id, 'SYN-CASE-A');
  assert.equal(opened.version, stored.version, 'the item opened a different version of the case');
  assert.equal(opened.saved_context.version, stored.version);
  assert.deepEqual(opened.saved_context.scenario, scenarioFor('SYN-CASE-A'), 'the saved scenario was not opened as saved');
  assert.equal(opened.obligation.next_action, 'Reviewer to send the comparable quotation for SYN-CASE-A');
  assert.equal(opened.obligation.next_update_due, '2026-09-20');
  assert.equal(opened.obligation.overdue, true, 'an overdue obligation is not marked overdue');
  assert.match(opened.obligation.statement, /Reviewer to send the comparable quotation for SYN-CASE-A/);

  const missing = service.openQueueItem('SYN-CASE-NONE', AS_OF);
  assert.equal(missing.ok, false, 'a queue item for no case opened something');
});

test('CASE-08 E2: searching a part does not reveal restricted cases or count another organisation\'s private records', () => {
  const service = build();
  const internal = service.search({ part_number: PART }, { mode: 'internal', as_of: AS_OF });
  assert.deepEqual(internal.rows.map((r) => r.case_id).sort(), ['SYN-CASE-A', 'SYN-CASE-B', 'SYN-CASE-C']);

  const viewer = exportModule.makeDevIdentity({ role: 'viewer', tenant: ORG_A });
  const shared = service.search({ part_number: PART }, { mode: 'shared', identity: viewer, as_of: AS_OF });
  assert.equal(shared.ok, true, shared.statement);
  assert.deepEqual(shared.rows.map((r) => r.case_id), ['SYN-CASE-A'], 'a restricted or another organisation\'s case was returned');
  assert.equal(shared.count, 1);
  const text = JSON.stringify(shared);
  ['SYN-CASE-B', 'SYN-CASE-C', ORG_B, 'Synthetic restricted source'].forEach((needle) => {
    assert.equal(text.includes(needle), false, 'the shared result mentions ' + needle);
  });
  assert.equal(shared.count, shared.rows.length, 'the shared count is not the rows it shows');
  const keys = [];
  (function walk(v) { if (v && typeof v === 'object') Object.keys(v).forEach((k) => { keys.push(k); walk(v[k]); }); })(shared);
  assert.deepEqual(keys.filter((k) => /hidden|withheld|total|excluded/i.test(k)), [], 'the shared result carries a count beyond what it shows');
  assert.doesNotMatch(shared.statement, /hidden|withheld|other organisation|restricted/i,
    'the shared statement reveals that other records exist');

  const noOrg = service.search({ part_number: PART }, { mode: 'shared',
    identity: exportModule.makeDevIdentity({ role: 'viewer' }), as_of: AS_OF });
  assert.equal(noOrg.ok, false);
  assert.deepEqual(noOrg.rows, []);
});