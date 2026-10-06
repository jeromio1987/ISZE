#!/usr/bin/env node
/* RANGE-01: pairing, supersession and fitment are different relationships. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));

test('RANGE-01 E1: a successor link cannot automatically become an interchangeable Genuine/BVP pair', () => {
  assert.equal(typeof evidence.makeRangeRelationshipLedger, 'function',
    'AIMEvidence.makeRangeRelationshipLedger is missing');
  assert.equal(typeof evidence.interchangeablePairStatus, 'function',
    'AIMEvidence.interchangeablePairStatus is missing');

  const ledger = evidence.makeRangeRelationshipLedger();
  const succ = ledger.record({
    type: 'supersession',
    part_a: '000-OLD-01',
    part_b: '000-NEW-01',
    source: 'Synthetic price file',
    source_version: '2026-01',
    authority: 'approved',
    conditions: { application_vehicle: 'synthetic N-series' }
  });
  assert.equal(succ.ok, true, 'an approved supersession should record');
  const pairAttempt = evidence.interchangeablePairStatus(succ.relationship);
  assert.equal(pairAttempt.interchangeable, false,
    'a supersession was treated as an interchangeable Genuine/BVP pair');
  assert.match(pairAttempt.statement, /supersession|successor|not an interchangeable/i);

  const asPairing = ledger.record({
    type: 'pairing',
    part_a: '000-OLD-01',
    part_b: '000-NEW-01',
    source: 'Synthetic catalogue',
    source_version: 'v1',
    authority: 'approved',
    conditions: { application_vehicle: 'synthetic N-series' }
  });
  assert.equal(asPairing.ok, true);
  const pairOk = evidence.interchangeablePairStatus(asPairing.relationship);
  assert.equal(pairOk.interchangeable, true,
    'an approved pairing should be interchangeable');

  const refused = ledger.record({
    type: 'pairing',
    part_a: '000-S-01',
    part_b: '000-S-02',
    source: 'Synthetic',
    authority: 'approved',
    promoted_from: 'successor'
  });
  assert.equal(refused.ok, false,
    'a successor was silently accepted as a pairing');
});

test('RANGE-01 E2: an unapproved relationship remains a candidate even when price and cost are present', () => {
  assert.equal(typeof evidence.rangeCommercialRole, 'function',
    'AIMEvidence.rangeCommercialRole is missing');
  const ledger = evidence.makeRangeRelationshipLedger();
  const row = ledger.record({
    type: 'pairing',
    part_a: '000-G-01',
    part_b: '000-B-01',
    source: 'Synthetic catalogue',
    source_version: 'v1',
    authority: 'candidate',
    conditions: {}
  });
  assert.equal(row.ok, true);
  const role = evidence.rangeCommercialRole(row.relationship, {
    price_present: true,
    cost_present: true,
    price_eur: 12.5,
    cost_eur: 4.0
  });
  assert.equal(role.role, 'candidate',
    'price and cost upgraded an unapproved relationship off candidate');
  assert.equal(role.interchangeable, false);
  assert.match(role.statement, /candidate|not approved|unapproved/i);
  assert.equal(role.price_present, true);
  assert.equal(role.cost_present, true);
});

test('RANGE-01 E3: two approved relationships of different type on one pair never merge into one', () => {
  const ledger = evidence.makeRangeRelationshipLedger();
  const a = ledger.record({
    type: 'pairing', part_a: '000-P-01', part_b: '000-P-02',
    source: 'Synthetic catalogue', source_version: 'v1', authority: 'approved', conditions: {}
  });
  const b = ledger.record({
    type: 'fitment', part_a: '000-P-01', part_b: '000-P-02',
    source: 'Synthetic EPC', source_version: 'v1', authority: 'approved',
    conditions: { application_vehicle: 'synthetic N75' }
  });
  assert.equal(a.ok && b.ok, true);
  const listed = ledger.listForPair('000-P-01', '000-P-02');
  assert.equal(listed.length, 2, 'two typed relationships were merged into one record');
  const types = listed.map((r) => r.type).sort();
  assert.deepEqual(types, ['fitment', 'pairing']);
  assert.notEqual(listed[0].relationship_id, listed[1].relationship_id);
});
