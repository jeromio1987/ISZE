#!/usr/bin/env node
/* ===========================================================================
   REVIEW-06 acceptance tests: recurrence, interruption and new purchasing.

   How to run
     node --test tests/review_06_recurrence.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (REVIEW-06):
     E1  A month absent from the data cannot produce a lapsed flag.
     E2  A supersession or combined-account change shows an explanation and
         not a false lost/new pair.

   Pattern: tests/review_04_contributors.test.mjs (evidence module).
   Data: tests/fixtures/review_06_recurrence.json (invented values only).
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

const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_06_recurrence.json'), 'utf8'));

function byId(id) {
  return FX.cases.find((c) => c.id === id);
}

function flagText(rec) {
  const bits = [];
  bits.push(rec.rule || '');
  bits.push(rec.pattern || '');
  (rec.flags || []).forEach((f) => bits.push(String(f)));
  (rec.explanations || []).forEach((e) => {
    bits.push(e.kind || '');
    bits.push(e.statement || '');
  });
  (rec.months || []).forEach((m) => {
    bits.push(m.period || '');
    bits.push(m.billingState || '');
    bits.push(m.flag || '');
  });
  return bits.join('\n').toLowerCase();
}

test('REVIEW-06 E1: a month absent from the data cannot produce a lapsed flag', () => {
  assert.equal(typeof evidence.purchasingActivity, 'function',
    'AIMEvidence.purchasingActivity is missing');

  const outside = byId('REVIEW06-OUTSIDE');
  const rec = evidence.purchasingActivity(outside);
  assert.ok(rec, 'purchasingActivity returned nothing');
  assert.ok(rec.rule && /covered|billingState|recorded|outside/i.test(rec.rule),
    'the stated rule is missing or does not name covered months');
  assert.equal(rec.score, null, 'a score was invented');
  assert.equal(rec.rating, null, 'a rating was invented');

  /* Outside-supplied-period months must be marked missing, never lapsed. */
  const outsideMonths = (rec.months || []).filter((m) => m.billingState === 'outside supplied period');
  assert.ok(outsideMonths.length >= 6, 'outside months were not surfaced');
  outsideMonths.forEach((m) => {
    assert.equal(m.covered, false, m.period + ' treated as covered');
    assert.equal(m.missing, true, m.period + ' not marked missing');
    assert.notEqual(m.flag, 'lapsed', m.period + ' produced a lapsed flag from outside data');
  });

  /* Pattern for continuous recorded covered months is not lapsed. */
  assert.notEqual(rec.pattern, 'lapsed',
    'outside months at the end of the calendar produced a lapsed pattern');
  assert.ok(!(rec.flags || []).includes('lapsed'),
    'a lapsed flag was raised from months outside the supplied period');

  /* A month literally absent from the series (2024-12) must not invent a lapsed flag. */
  const periods = new Set((outside.series || []).map((r) => r.period));
  assert.equal(periods.has('2024-12'), false, 'fixture unexpectedly holds 2024-12');
  const invented = (rec.months || []).find((m) => m.period === '2024-12');
  if (invented) {
    assert.equal(invented.covered, false);
    assert.equal(invented.missing, true);
    assert.notEqual(invented.flag, 'lapsed');
  }
  assert.ok(!(rec.flags || []).some((f) => f === 'lapsed' && String(f).includes('2024-12')));

  /* Number changes on covered months are marked explicitly. */
  const changes = rec.number_changes || [];
  assert.ok(Array.isArray(changes), 'number_changes missing');
  assert.ok(changes.length >= 1, 'quantity changes on covered months were not marked');

  const gap = evidence.purchasingActivity(byId('REVIEW06-GAP'));
  assert.notEqual(gap.pattern, 'lapsed',
    'a covered gap plus trailing outside months became lapsed');
  const gapOutside = (gap.months || []).filter((m) => m.billingState === 'outside supplied period');
  gapOutside.forEach((m) => {
    assert.notEqual(m.flag, 'lapsed', m.period + ' lapsed from outside supplied period');
  });
});

test('REVIEW-06 E2: a supersession or combined-account change shows an explanation and not a false lost/new pair', () => {
  assert.equal(typeof evidence.purchasingActivity, 'function',
    'AIMEvidence.purchasingActivity is missing');

  for (const id of ['REVIEW06-SUPER', 'REVIEW06-COMBINED']) {
    const caseRec = byId(id);
    const rec = evidence.purchasingActivity(caseRec);
    assert.ok(rec, id + ': no result');
    assert.ok((rec.explanations || []).length >= 1, id + ': no explanation for the transfer');

    const text = flagText(rec);
    if (id === 'REVIEW06-SUPER') {
      assert.match(text, /supersession|newest number|newest-number/,
        id + ': explanation does not name the supersession / newest-number change');
    } else {
      assert.match(text, /combined-account|combined account|account merged|accounts merged/,
        id + ': explanation does not name the combined-account change');
    }

    /* False lost/new pair: both flags present with no explanation would fail.
       With an explanation present, neither lost nor new may stand as a proven pair. */
    const flags = rec.flags || [];
    const hasLost = flags.includes('lost') || flags.includes('lapsed');
    const hasNew = flags.includes('new');
    if (hasLost && hasNew) {
      assert.fail(id + ': false lost/new pair without absorbing the relationship explanation');
    }
    assert.equal(rec.false_pair_avoided, true,
      id + ': false_pair_avoided is not true when a relationship explains the movement');
    assert.ok(rec.explanations.every((e) => e.statement && e.related_pn),
      id + ': explanation missing statement or related part reference');
    assert.doesNotMatch(text, /proven lost sales|largest opportunity|score\s*\d|rating\s*\d/,
      id + ': forbidden rating or lost-sales claim appeared');
  }
});
