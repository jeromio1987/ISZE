#!/usr/bin/env node
/* ===========================================================================
   DATA-07 reconciliation tests: joins, class applicability and the unmatched
   remainder (TASKS_96.txt, DATA-07; roadmap B02, B03, B11).

   BUILD says: add control checks before/after source joins, retain unmatched
   accounts and parts in appropriate totals, expose mapping exceptions, and
   detect many-to-many multiplication, non-additive class applicability and
   repeated market totals - using the existing approved analytical definitions,
   not a new model.

   REQUIRED EVIDENCE
     E1  A duplicate classification mapping cannot inflate quantity or euro.
     E2  Matched plus unmatched totals reconcile to the same permitted source
         scope.

   How to run
     node --test tests/data_07_reconcile.test.mjs

   The layer under test is src/data/manifest.js, which owns source identity and
   the join controls. Its own entity rules (distributor / purchasing account /
   site as three separate fields) are the definitions reused here; this file
   adds no second model. The fixture in this file is invented, with invented
   values, and the restricted payload is never read.

   The two controls are:
     reconcileClassTotals(rows, mappings)
       A classification mapping is joined onto the rows. Where one source key is
       mapped to more than one class at once the row is many-to-many: its value
       is shared by both classes rather than held by each, so it is placed in an
       explicit shared bucket and never added into a single class total.
     reconcileScope(rows, permitted)
       A permitted join scope (distributor + purchasing account) is applied to
       the rows. Rows that do not join are kept in their own visible remainder
       with their size in rows, units and euro rather than being dropped.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

const manifest = require(path.join(ROOT, 'src', 'data', 'manifest.js'));

/* --------------------------------------------------------------- fixture -- */

/* Invented rows. Four rows, 185 units and EUR 1,850 in total. SYNTH-PN-A is
   billed to TESTUK/A1 and to TESTOTHER/B1, which is why the same part number
   appears twice: a part number alone does not identify a row. */
function rows() {
  return [
    { distributor: 'TESTUK', purchasing_account: 'A1', part_number: 'SYNTH-PN-A',
      quantity: 100, euro: 1000, class_code: 'C' },
    { distributor: 'TESTUK', purchasing_account: 'A1', part_number: 'SYNTH-PN-B',
      quantity: 50, euro: 500, class_code: 'C' },
    { distributor: 'TESTUK', purchasing_account: 'A2', part_number: 'SYNTH-PN-C',
      quantity: 25, euro: 250, class_code: 'D' },
    { distributor: 'TESTOTHER', purchasing_account: 'B1', part_number: 'SYNTH-PN-A',
      quantity: 10, euro: 100, class_code: 'D' }
  ];
}

/* A duplicate classification: SYNTH-PN-A on TESTUK/A1 is mapped to both C and D
   at once. The row is one row with one value, and the mapping does not create a
   second one. */
function duplicateMappings() {
  return [
    { distributor: 'TESTUK', purchasing_account: 'A1', part_number: 'SYNTH-PN-A',
      class_code: 'C' },
    { distributor: 'TESTUK', purchasing_account: 'A1', part_number: 'SYNTH-PN-A',
      class_code: 'D' }
  ];
}

/* ------------------------------------------------------ DATA-07 E1: class -- */

test('DATA-07 E1: a duplicate classification mapping cannot inflate quantity or euro', () => {
  const data = rows();
  const withoutMappings = manifest.reconcileClassTotals(data, []);
  const withDuplicates = manifest.reconcileClassTotals(data, duplicateMappings());

  /* The counted source scope is unchanged by a mapping that disagrees with
     itself: the same four rows, the same 185 units, the same EUR 1,850. */
  assert.equal(withDuplicates.rows_in, withoutMappings.rows_in,
    'sharing a classification changed the number of rows counted');
  assert.equal(withDuplicates.quantity_total, withoutMappings.quantity_total,
    'the duplicate classification inflated the counted quantity');
  assert.equal(withDuplicates.euro_total, withoutMappings.euro_total,
    'the duplicate classification inflated the counted euro');
  assert.equal(withDuplicates.quantity_total, 185);
  assert.equal(withDuplicates.euro_total, 1850);

  /* The control passes: nothing is lost and nothing is counted twice. */
  assert.equal(withDuplicates.ok, true, withDuplicates.statement);

  /* Every unit and every euro lands in exactly one bucket: a single class, or
     the shared bucket. */
  assert.equal(withDuplicates.sum_of_class_totals_quantity + withDuplicates.shared.quantity,
    withDuplicates.quantity_total, 'the class buckets do not sum back to the counted quantity');
  assert.equal(withDuplicates.sum_of_class_totals_euro + withDuplicates.shared.euro,
    withDuplicates.euro_total, 'the class buckets do not sum back to the counted euro');

  /* The many-to-many row is visible as such, and it is the shared row only. */
  assert.equal(withDuplicates.shared.rows, 1, 'the shared mapping is not reported');
  assert.equal(withDuplicates.shared.quantity, 100);
  assert.equal(withDuplicates.shared.euro, 1000);
  assert.equal(withDuplicates.shared_mappings.length, 1,
    'the shared mapping is not listed as a mapping exception');
  assert.deepEqual(withDuplicates.shared_mappings[0].classes.slice().sort(), ['C', 'D']);
  assert.match(withDuplicates.multi_class_statement, /more than one class/i);

  /* And the single-class totals are not inflated by it. */
  const classC = withDuplicates.class_totals.find((c) => c.class_code === 'C');
  const classD = withDuplicates.class_totals.find((c) => c.class_code === 'D');
  assert.equal(classC.quantity, 50, 'class C also took the shared row');
  assert.equal(classD.quantity, 35, 'class D also took the shared row');
  assert.equal(classC.euro, 500);
  assert.equal(classD.euro, 350);

  /* Without the duplicate the same row joins one class cleanly, and the totals
     are still the same totals. */
  assert.equal(withoutMappings.shared.rows, 0);
  assert.equal(withoutMappings.class_totals.find((c) => c.class_code === 'C').quantity, 150);
});

/* ------------------------------------------------------ DATA-07 E2: scope -- */

test('DATA-07 E2: matched plus unmatched totals reconcile to the same permitted source scope', () => {
  const data = rows();
  /* The permitted join scope: two accounts, three of the four rows. */
  const permitted = [
    { distributor: 'TESTUK', purchasing_account: 'A1' },
    { distributor: 'TESTUK', purchasing_account: 'A2' }
  ];
  const rec = manifest.reconcileScope(data, permitted);

  assert.equal(rec.rows_in, 4, 'a row went missing before the join');
  assert.equal(rec.quantity_total, 185);
  assert.equal(rec.euro_total, 1850);

  assert.equal(rec.matched.rows, 3, 'the matched population is wrong');
  assert.equal(rec.matched.quantity, 175);
  assert.equal(rec.matched.euro, 1750);
  assert.equal(rec.unmatched.rows, 1, 'the unmatched remainder is not kept visible');
  assert.equal(rec.unmatched.quantity, 10);
  assert.equal(rec.unmatched.euro, 100);

  assert.equal(rec.matched.rows + rec.unmatched.rows, rec.rows_in,
    'matched plus unmatched does not reconcile to the permitted source scope');
  assert.equal(rec.matched.quantity + rec.unmatched.quantity, rec.quantity_total,
    'the quantities do not reconcile');
  assert.equal(rec.matched.euro + rec.unmatched.euro, rec.euro_total,
    'the euro does not reconcile');
  assert.equal(rec.ok, true, rec.statement);

  /* The unmatched row is named by entity, not folded into a matched account. */
  assert.equal(rec.unmatched_by_entity.length, 1);
  assert.match(rec.unmatched_by_entity[0].entity_label, /TESTOTHER/);
  assert.equal(rec.unmatched_by_entity[0].rows, 1);
  assert.equal(rec.unmatched_by_entity[0].quantity, 10);
  assert.match(rec.statement, /unmatched/i);
});
