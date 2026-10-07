#!/usr/bin/env node
/* ===========================================================================
   RANGE-07 acceptance tests: Use authentic, permitted product images with a
   clear fallback.

   How to run
     node --test tests/range_07_product_images.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A missing image does not break identification or the case workflow.
     E2  An image points to its known source/reference and cannot silently be
         copied to a different part.

   Sufficiency: no image in this repo has a recorded permission, so the index
   is empty of authentic assets and the fallback path is what is verified.
   No image is downloaded.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'product_images.js'));

test('RANGE-07 E1: A missing image does not break identification or the case workflow.', () => {
  /* Empty index: no recorded permissions in the repo. */
  const empty = mod.makeImageIndex([]);
  assert.equal(empty.permittedCount(), 0);
  const missing = empty.resolveForPart('SYNTH-PART-NO-IMAGE');
  assert.equal(missing.ok, true);
  assert.equal(missing.has_image, false);
  assert.equal(missing.fallback, true);
  assert.equal(missing.identification_intact, true);
  assert.equal(missing.case_workflow_intact, true);

  const id = empty.caseIdentification('SYNTH-PART-NO-IMAGE');
  assert.equal(id.ok, true);
  assert.equal(id.identification_broken, false);
  assert.equal(id.case_workflow_broken, false);

  /* With a synthetic permission record (labelled synthetic), resolve still works. */
  const withPerm = mod.makeImageIndex([{
    image_id: 'SYN-IMG-1',
    part_number: 'SYNTH-PART-WITH-IMAGE',
    permission_record: 'SYNTHETIC-PERMISSION-RECORD-ONLY',
    source: 'synthetic-fixture://SYN-IMG-1',
    synthetic: true
  }]);
  const hit = withPerm.resolveForPart('SYNTH-PART-WITH-IMAGE');
  assert.equal(hit.has_image, true);
  assert.equal(hit.fallback, false);
  assert.equal(hit.source, 'synthetic-fixture://SYN-IMG-1');
  const stillMissing = withPerm.caseIdentification('SYNTH-PART-OTHER');
  assert.equal(stillMissing.identification_broken, false);
  assert.equal(stillMissing.case_workflow_broken, false);
});

test('RANGE-07 E2: An image points to its known source/reference and cannot silently be copied to a different part.', () => {
  const idx = mod.makeImageIndex([{
    image_id: 'SYN-IMG-2',
    part_number: 'SYNTH-PART-A',
    permission_record: 'SYNTHETIC-PERMISSION-RECORD-ONLY',
    source: 'synthetic-fixture://SYN-IMG-2',
    synthetic: true
  }]);
  const same = idx.associateImage('SYN-IMG-2', 'SYNTH-PART-A');
  assert.equal(same.ok, true);
  assert.equal(same.source, 'synthetic-fixture://SYN-IMG-2');

  const cross = idx.associateImage('SYN-IMG-2', 'SYNTH-PART-B');
  assert.equal(cross.ok, false);
  assert.equal(cross.code, 'CROSS_PART_COPY_REFUSED');
  assert.equal(cross.recorded_part, 'SYNTH-PART-A');
  assert.equal(cross.requested_part, 'SYNTH-PART-B');
  assert.equal(cross.source, 'synthetic-fixture://SYN-IMG-2');
  assert.match(cross.statement, /cannot silently be copied/);
});
