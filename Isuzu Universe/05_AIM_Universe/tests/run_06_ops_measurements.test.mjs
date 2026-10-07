#!/usr/bin/env node
/* ===========================================================================
   RUN-06 acceptance tests: Record operational failures and useful-work
   measurements.

   How to run
     node --test tests/run_06_ops_measurements.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A failed import or save can be investigated from its safe error
         reference and tested build.
     E2  Acknowledgement, substantive response, resolution and
         participant-confirmed usefulness are separate measurements.

   Synthetic fixtures only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'ops_measurements.js'));

test('RUN-06 E1: A failed import or save can be investigated from its safe error reference and tested build.', () => {
  const rec = mod.makeOpsRecorder({ now: () => 1_000_000 });
  const fail = rec.recordFailure({
    kind: 'failed_import',
    reference: 'SYN-ERR-IMPORT-1',
    build: 'v04-synthetic-test',
    stage: 'import',
    started_at: 999_000,
    ended_at: 1_000_000,
    message: 'Synthetic import refused a malformed row',
    context: { case_id: 'SYN-CASE-1', cost_eur: 99.99, private_note: 'secret' }
  });
  assert.equal(fail.ok, false);
  assert.equal(fail.reference, 'SYN-ERR-IMPORT-1');
  assert.equal(fail.build, 'v04-synthetic-test');
  assert.equal(fail.elapsed_ms, 1000);
  assert.equal(fail.confidential_copied, false);
  assert.equal('cost_eur' in fail.safe_context, false);
  assert.equal('private_note' in fail.safe_context, false);
  assert.equal(fail.safe_context.case_id, 'SYN-CASE-1');

  const found = rec.investigate('SYN-ERR-IMPORT-1');
  assert.equal(found.ok, true);
  assert.equal(found.build, 'v04-synthetic-test');
  assert.equal(found.kind, 'failed_import');
});

test('RUN-06 E2: Acknowledgement, substantive response, resolution and participant-confirmed usefulness are separate measurements.', () => {
  const rec = mod.makeOpsRecorder();
  const kinds = [
    'acknowledgement',
    'substantive_response',
    'resolution',
    'participant_confirmed_usefulness'
  ];
  kinds.forEach((kind, i) => {
    const m = rec.recordMeasurement({
      kind,
      case_id: 'SYN-CASE-1',
      started_at: 1000 + i * 100,
      ended_at: 1100 + i * 100
    });
    assert.equal(m.ok, true, m.error);
    assert.equal(m.kind, kind);
    assert.equal(m.invented, false);
    assert.equal(m.measured, true);
  });
  const refused = rec.recordMeasurement({ kind: 'login_count', elapsed_ms: 5 });
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'MEASUREMENT_KIND_REFUSED');
  const s = rec.summary();
  assert.equal(s.measurement_counts.acknowledgement, 1);
  assert.equal(s.measurement_counts.substantive_response, 1);
  assert.equal(s.measurement_counts.resolution, 1);
  assert.equal(s.measurement_counts.participant_confirmed_usefulness, 1);
  assert.match(s.statement, /separate measurements/);
});
