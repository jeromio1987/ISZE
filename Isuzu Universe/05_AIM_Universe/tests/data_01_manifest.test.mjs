#!/usr/bin/env node
/* ===========================================================================
   DATA-01 acceptance tests: a source manifest on every analytical input.

   How to run
     node --test tests/data_01_manifest.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (DATA-01):
     E1  A candidate source without a known period can be inspected as
         unvalidated data but cannot support a dated change claim.
     E2  Source generation date, observation period and offer date remain
         separate.

   Data: the synthetic fixture only. No restricted payload is read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const require = createRequire(import.meta.url);

const manifest = require(path.join(ROOT, 'src', 'data', 'manifest.js'));
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'synthetic_payload.json'), 'utf8'));

test('DATA-01 E1: a candidate source with no known period is inspectable as unvalidated but cannot support a dated change claim', () => {
  const m = manifest.build(FX);
  const cand = manifest.find(m, 'MAN-09');
  assert.ok(cand, 'the candidate-screen record is missing from the manifest');
  assert.equal(cand.period, null, 'a period was invented for the candidate source');
  assert.equal(cand.period_state, 'undeclared');
  assert.equal(cand.validation_state, 'unvalidated');

  const look = manifest.claimSupport(cand, 'inspect');
  assert.equal(look.allowed, true, 'an undated source must still be inspectable');
  assert.equal(look.validation_state, 'unvalidated');
  assert.match(look.statement, /unvalidated/i);

  const dated = manifest.claimSupport(cand, 'dated_change');
  assert.equal(dated.allowed, false, 'an undated source was allowed to support a dated change claim');
  assert.equal(dated.code, 'PERIOD_UNDECLARED');

  /* Control: a record with a declared period does support a dated claim, so the
     refusal above is about the missing period and not a blanket refusal. */
  const billed = manifest.find(m, 'MAN-01');
  assert.equal(billed.validation_state, 'period declared');
  assert.equal(manifest.claimSupport(billed, 'dated_change').allowed, true);

  /* The payload's own build date is present in the fixture. It must not be
     borrowed as the candidate period. */
  assert.ok(FX.meta.buildDate, 'fixture lost its build date; the control below proves nothing');
  assert.notEqual(cand.period, FX.meta.buildDate);
  assert.equal(manifest.claimSupport(null, 'dated_change').allowed, false);
});

test('DATA-01 E2: generation date, observation period and offer date stay three separate fields', () => {
  const OFFER = '2026-10-01';
  const m = manifest.build(FX, { offer_effective_date: OFFER });

  const pack = manifest.find(m, 'MAN-07');
  assert.equal(pack.clocks.generated_date, '2026-09-22');
  assert.equal(pack.clocks.observation_period, pack.period);
  assert.equal(pack.clocks.offer_date, OFFER);
  assert.notEqual(pack.clocks.generated_date, pack.clocks.offer_date);
  assert.notEqual(pack.clocks.observation_period, pack.clocks.generated_date);

  /* A record with none of its own dates keeps all of them empty except the
     caller's offer date: none is filled from another. */
  const cand = manifest.find(m, 'MAN-09');
  assert.equal(cand.clocks.generated_date, null, 'a generation date was invented');
  assert.equal(cand.clocks.observation_period, null, 'the offer or build date was used as a period');
  assert.equal(cand.clocks.offer_date, OFFER);

  /* Without an offer date the offer clock stays empty; it is not taken from the
     generation date or the period. */
  const noOffer = manifest.build(FX);
  const pack2 = manifest.find(noOffer, 'MAN-07');
  assert.equal(pack2.clocks.offer_date, null, 'an offer date was invented from another clock');
  assert.equal(pack2.clocks.generated_date, '2026-09-22');

  /* Every record carries the three clocks under their own names. */
  m.records.forEach((r) => {
    assert.ok(r.clocks, r.reference_id + ' has no clocks');
    ['generated_date', 'observation_period', 'offer_date'].forEach((k) => {
      assert.ok(Object.prototype.hasOwnProperty.call(r.clocks, k), r.reference_id + ' lacks ' + k);
    });
  });
});