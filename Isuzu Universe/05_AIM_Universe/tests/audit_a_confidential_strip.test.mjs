#!/usr/bin/env node
/* ===========================================================================
   Audit fix A (U27): confidential keys are removed at any depth, and the
   confidential_copied flag comes from a re-scan of the output.

   How to run
     node --test tests/audit_a_confidential_strip.test.mjs

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

const NESTED = {
  context: { case: { cost_eur: 41.75, dealer_email: 'x@y.z' }, note: 'n' },
  lines: [{ margin: 0.3, part: 'SYN-PN' }, [{ private_note: 'deep' }]]
};

test('RUN-06 audit A: nested confidential values are stripped, other values stay', () => {
  const out = mod.stripConfidential(NESTED);
  assert.deepEqual(out.context.case, {});
  assert.equal(out.context.note, 'n');
  assert.deepEqual(out.lines[0], { part: 'SYN-PN' });
  assert.deepEqual(out.lines[1][0], {});
  assert.deepEqual(mod.findConfidential(out), []);
});

test('RUN-06 audit A: recordFailure keeps nested confidential values out of safe_context', () => {
  const rec = mod.makeOpsRecorder({ now: () => 1 });
  const row = rec.recordFailure({ reference: 'SYN-A', context: NESTED });
  assert.equal(JSON.stringify(row).includes('41.75'), false);
  assert.equal(JSON.stringify(row).includes('x@y.z'), false);
  assert.equal(row.safe_context.context.note, 'n');
  assert.equal(row.confidential_copied, false);
});

test('RUN-06 audit A negative control: the scan catches a planted key when the strip is skipped', () => {
  const planted = JSON.parse(JSON.stringify(NESTED));
  const hits = mod.findConfidential(planted);
  assert.ok(hits.includes('context.case.cost_eur'));
  assert.ok(hits.includes('context.case.dealer_email'));
  assert.ok(hits.includes('lines.1.0.private_note'));
  const rec = mod.makeOpsRecorder({ now: () => 1, strip: (v) => JSON.parse(JSON.stringify(v)) });
  const row = rec.recordFailure({ reference: 'SYN-A-NEG', context: NESTED });
  assert.equal(row.confidential_copied, true);
});
