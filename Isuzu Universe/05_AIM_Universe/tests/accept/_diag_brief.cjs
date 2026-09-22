#!/usr/bin/env node
'use strict';
/* Diagnostic: what does the participant brief actually contain?

Prints the key structure of the brief that the UI's export route builds, and the
allowlist it was built against. No restricted values are printed - only key names
and whether a value is present. Nothing here is an acceptance check.
*/
const H = require('./lib/harness.cjs');
const exportRoute = H.requireModule(H.PATHS.exportData);
const recipients = H.requireModule(H.PATHS.recipients);
const contracts = H.requireModule(H.PATHS.contracts);

const caseObject = { case_id: 'SYNTH-CASE', customer: 'Synthetic participant', market: 'SYNTH',
  part_number: 'SYNTH-PART-A', unit: 'unit', title: 'Synthetic case', version: 1, state: 'draft' };
const scenario = { price_before: 100, price_after: 94, quantity_before: 1000, quantity_after: 1200,
  quantity_label: 'manual scenario', scope: 'all', support_eur: 500, cost_eur: 987654.4321,
  cost_basis_id: 'FWD_B', evidence_period: 'synthetic period', offer_effective_date: '2025-10-01' };
const result = H.requireModule(H.PATHS.engine).calculate({
  price_before: 100, price_after: 94, quantity_before: 1000, quantity_after: 1200,
  scope: 'all', support_eur: 500, cost_eur: 987654.4321, quantity_label: 'manual scenario' });

const brief = exportRoute.memberBrief(caseObject, scenario, result,
  { exported_at: '2026-09-22T00:00:00Z', request_note: 'A note a person typed.' });
const bytes = exportRoute.toBytes(brief, true);

console.log('--- participant brief from src/data/export.js ---');
console.log('top-level keys in payload:', Object.keys(brief.payload));
console.log('payload as written:');
console.log(bytes.text);
console.log('length:', bytes.length);

console.log('--- the allowlist it was built against (src/data/export.js) ---');
const keys = exportRoute.allowlistFor('member');
console.log(Object.keys(keys).sort().join(', '));
for (const container of ['reference', 'offer', 'price', 'quantity', 'customers', 'limits']) {
  console.log(`container "${container}" is in the allowlist:`, Object.prototype.hasOwnProperty.call(keys, container));
}

console.log('--- declared in contracts.js RECIPIENTS.member ---');
console.log('permits     :', contracts.RECIPIENTS.member.permits.join(', '));
console.log('leaf_fields :', contracts.RECIPIENTS.member.leaf_fields.join(', '));

console.log('--- hardened internal record, nested containers ---');
const intRec = recipients.internalRecord({ case: caseObject, scenario, result,
  extra: { review: null, sources: [], history: [] } });
console.log(JSON.stringify(intRec.payload.limits, null, 2));

console.log('--- the UI module internal record, same input ---');
const uiInt = exportRoute.internalRecord(caseObject, scenario, result,
  { exported_at: null, review: null, sources: [], history: [] });
console.log('top-level keys:', Object.keys(uiInt.payload));
console.log('limits:', JSON.stringify(uiInt.payload.limits, null, 2));
console.log('scenario keys:', uiInt.payload.scenario ? Object.keys(uiInt.payload.scenario) : null);
console.log('result keys:', uiInt.payload.result ? Object.keys(uiInt.payload.result).slice(0, 20) : null);

console.log('--- the hardened module, same input ---');
const hard = recipients.memberBrief({ case: caseObject, scenario, result,
  meta: { exported_at: '2026-09-22T00:00:00Z', request_note: 'A note a person typed.' } });
console.log('top-level keys in payload:', Object.keys(hard.payload));
console.log('length:', recipients.toBytes(hard, true).length);
