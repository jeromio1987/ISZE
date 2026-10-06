#!/usr/bin/env node
/* ===========================================================================
   REVIEW-04 reconciliation tests: parts behind a purchasing movement.

   How to run
     node --test tests/review_04_contributors.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (REVIEW-04):
     E1  Displayed contributors plus stated remainder reproduce the selected
         movement.
     E2  Quantity-only sources stay quantity-only; a descriptive change is not
         labelled proven lost sales.

   Pattern: tests/data_07_reconcile.test.mjs.
   Data: tests/fixtures/review_04_contributors.json (invented values only).
   The restricted payload is never read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const evidence = require(path.join(ROOT, 'src', 'data', 'evidence.js'));

const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_04_contributors.json'), 'utf8'));
const CASE_IDS = FX.cases.map((c) => c.id);
const COMPARES = ['half', 'annual'];

function panelText(rec) {
  const bits = [];
  bits.push(rec.statement || '');
  bits.push(rec.remainder && rec.remainder.statement ? rec.remainder.statement : '');
  (rec.contributors || []).forEach((c) => {
    bits.push(c.status || '');
    bits.push(c.pn || '');
    if (c.eur_delta === null || c.eur_delta === undefined) bits.push('euro not stated');
    else bits.push(String(c.eur_delta));
  });
  if (rec.remainder) {
    bits.push(rec.remainder.status || '');
    bits.push(String(rec.remainder.quantity_delta));
    bits.push(String(rec.remainder.eur_delta));
  }
  return bits.join('\n');
}

test('REVIEW-04 E1: contributors plus remainder equal the selected movement for each case and comparison', () => {
  assert.equal(CASE_IDS.length, 5);
  for (const caseId of CASE_IDS) {
    const caseRec = FX.cases.find((c) => c.id === caseId);
    for (const compare of COMPARES) {
      const rec = evidence.movementContributors(caseRec, compare);
      assert.equal(rec.ok, true, caseId + '/' + compare + ': ' + rec.statement);
      assert.equal(rec.compare, compare);
      const move = caseRec.comparisons[compare];
      const expectQ = move.current.quantity - move.prior.quantity;
      const expectE = Math.round((move.current.eur - move.prior.eur) * 100) / 100;
      assert.equal(rec.movement.quantity, expectQ);
      assert.equal(rec.movement.eur, expectE);

      const sumQ = rec.contributors.reduce((s, c) => s + c.quantity_delta, 0) + rec.remainder.quantity_delta;
      const sumE = rec.contributors.reduce((s, c) => s + (c.eur_stated ? c.eur_delta : 0), 0) + rec.remainder.eur_delta;
      assert.equal(sumQ, expectQ, caseId + '/' + compare + ': quantity does not reconcile');
      assert.equal(Math.round(sumE * 100) / 100, expectE, caseId + '/' + compare + ': euro does not reconcile');
      assert.equal(rec.remainder.pn, caseRec.pn);
      assert.equal(rec.remainder.role, 'own_part');

      /* Half-year related rows contribute only on half; annual leaves them out. */
      if (compare === 'annual') {
        assert.equal(rec.contributors.length, 0, caseId + '/annual: related half rows must not be counted');
        assert.equal(rec.remainder.quantity_delta, expectQ);
      }
    }
  }
});

test('REVIEW-04 E2: quantity-only sources never invent euro and descriptive change is not labelled lost sales', () => {
  const oil = FX.cases.find((c) => c.id === 'IMOTORS-OIL');
  const rec = evidence.movementContributors(oil, 'half');
  assert.equal(rec.ok, true, rec.statement);
  const qtyOnly = rec.contributors.find((c) => c.pn === 'SYN-REL-OIL-B');
  assert.ok(qtyOnly, 'quantity-only related reference is missing from contributors');
  assert.equal(qtyOnly.eur_delta, null, 'quantity-only row invented an euro delta');
  assert.equal(qtyOnly.eur_stated, false);
  assert.equal(qtyOnly.prior.eur, null);
  assert.equal(qtyOnly.current.eur, null);

  for (const caseId of CASE_IDS) {
    const caseRec = FX.cases.find((c) => c.id === caseId);
    for (const compare of COMPARES) {
      const r = evidence.movementContributors(caseRec, compare);
      const text = panelText(r).toLowerCase();
      assert.equal(text.includes('lost sales'), false,
        caseId + '/' + compare + ': panel text contains "lost sales"');
      /* Descriptive related status may be present; it must not be upgraded. */
      r.contributors.forEach((c) => {
        if (c.status) {
          assert.match(c.status, /Candidate|seller-related|Genuine|BVP/i);
          assert.doesNotMatch(c.status, /proven lost sales/i);
        }
      });
    }
  }
});
