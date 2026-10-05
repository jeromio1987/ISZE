#!/usr/bin/env node
/* ===========================================================================
   DATA-03 acceptance tests: original references and versioned part
   relationships are preserved.

   How to run
     node --test tests/data_03_references.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (DATA-03):
     E1  Leading-zero and nonnumeric reference tests round-trip unchanged.
     E2  A classification or successor update creates a new relationship
         version without rewriting a saved decision.

   src/data/evidence.js is loaded as data_contracts.test.mjs loads it. Every
   reference, family and source below is invented. The restricted payload is
   never read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));

const REFS = ['0001234', '000-SYN-01', '8-97000001-0', ' 0042 ', 'SYN/12.0', '00000', 'syn-lower-07'];

test('DATA-03 E1: leading-zero and nonnumeric references round-trip unchanged', () => {
  REFS.forEach((raw) => {
    const ref = evidence.partReference(raw);
    assert.equal(typeof ref.original_reference, 'string');
    assert.equal(ref.original_reference, raw, 'the reference was changed on intake: ' + JSON.stringify(raw));
    assert.equal(ref.received_as_number, false);
    const back = evidence.partReference(JSON.parse(JSON.stringify(ref)).original_reference);
    assert.equal(back.original_reference, raw, 'the reference did not survive a save and reload');
  });
  const keys = REFS.map((r) => evidence.partReference(r).match_key);
  assert.equal(new Set(keys).size, REFS.length, 'two different references were given one match key');
  assert.equal(evidence.partReference('0001234').match_key === evidence.partReference('1234').match_key, false,
    'leading zeros were dropped from the match key');

  const num = evidence.partReference(1234);
  assert.equal(num.original_reference, '1234');
  assert.equal(num.received_as_number, true, 'a reference that arrived as a number is not flagged');
  assert.match(num.statement, /arrived as a number/);
});

test('DATA-03 E2: a classification or successor update creates a new relationship version without rewriting a saved decision', () => {
  const ledger = evidence.makeRelationshipLedger();
  const c1 = ledger.record({ kind: 'classification', reference: '0001234', value: 'Synthetic family A',
    source: 'Synthetic parts tree 1', source_version: 'v1', effective_from: '2026-01-01' });
  assert.equal(c1.ok, true);
  assert.equal(c1.relationship.version, 1);
  const s1 = ledger.record({ kind: 'successor', reference: '0001234', value: '0001235',
    source: 'Synthetic price file', source_version: '2026-01', effective_from: '2026-01-01' });
  assert.equal(s1.ok, true);
  const refused = ledger.record({ kind: 'fits', reference: '0001234', value: 'x', source: 'Synthetic' });
  assert.equal(refused.ok, false, 'an untyped relationship was recorded');

  const decision = { decision_id: 'SYN-DEC-1', part_reference: '0001234', recorded_on: '2026-02-01',
    relationships_used: [c1.relationship.relationship_id, s1.relationship.relationship_id] };
  const saved = JSON.parse(JSON.stringify(decision));

  const c2 = ledger.record({ kind: 'classification', reference: '0001234', value: 'Synthetic family B',
    source: 'Synthetic parts tree 2', source_version: 'v2', effective_from: '2026-03-01' });
  const s2 = ledger.record({ kind: 'successor', reference: '0001234', value: '0001236',
    source: 'Synthetic price file', source_version: '2026-03', effective_from: '2026-03-01' });
  assert.equal(c2.relationship.version, 2);
  assert.equal(s2.relationship.version, 2);
  assert.notEqual(c2.relationship.relationship_id, c1.relationship.relationship_id);

  const hist = ledger.history('0001234', 'classification');
  assert.equal(hist.length, 2, 'the earlier classification version was overwritten');
  assert.equal(hist[0].value, 'Synthetic family A');
  assert.equal(hist[0].superseded_by, c2.relationship.relationship_id);
  assert.equal(ledger.current('0001234', 'classification', '2026-02-15').value, 'Synthetic family A');
  assert.equal(ledger.current('0001234', 'classification', '2026-03-15').value, 'Synthetic family B');

  assert.deepEqual(decision, saved, 'the saved decision was rewritten by the update');
  const view = ledger.decisionView(decision);
  assert.deepEqual(view.used.map((r) => r.value), ['Synthetic family A', '0001235'],
    'the decision no longer reads the relationships it was saved with');
  assert.equal(view.newer_versions.length, 2, 'the newer versions are not named beside the saved decision');
  assert.equal(view.part_reference, '0001234', 'the transacted reference was replaced by its successor');

  const unclassified = ledger.unclassified(['0001234', '000-SYN-01']);
  assert.deepEqual(unclassified, ['000-SYN-01'], 'an unclassified reference was dropped or classified');
});