#!/usr/bin/env node
/* RANGE-05: unsupported migration stays financially unresolved. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));
const engine = require(path.join(ROOT, 'src/engine/engine.js'));
const payload = JSON.parse(fs.readFileSync(path.join(ROOT, 'payload/aim_payload_20260922.json'), 'utf8'));
const FIX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/range_05_unresolved.json'), 'utf8'));

test('RANGE-05 E1: IMOTORS-OIL migration no longer returns a misleading single-product no-change result', () => {
  engine.setPayload(payload);
  const oil = payload.cases.find((c) => c.id === 'IMOTORS-OIL');
  assert.ok(oil, 'IMOTORS-OIL case missing from payload');
  const ranked = engine.rankAlternatives(oil);
  const mig = ranked.ranked.find((x) => x.alternative.kind === 'migration');
  assert.ok(mig, 'IMOTORS-OIL migration alternative missing');
  assert.equal(mig.result.migration_status, 'unresolved');
  assert.equal(mig.result.ok, false);
  assert.equal(mig.result.revenue_change, null,
    'unresolved migration reported a numeric revenue change');
  assert.equal(mig.result.gp_change, null,
    'unresolved migration reported a numeric gross-profit change');
  // Not a single-product no-change: benefit is unknown, not zero.
  assert.equal(typeof evidence.rangeMigrationBenefit, 'function');
  const benefit = evidence.rangeMigrationBenefit(oil, { engine, payload });
  assert.equal(benefit.benefit_state, 'unknown');
  assert.equal(benefit.benefit_eur, null);
  assert.notEqual(benefit.benefit_eur, 0);
  assert.equal(benefit.counterpart_invented, false);
  assert.match(benefit.statement, /unknown|unresolved|not a single-product/i);
  assert.equal(/proven|lost sales|factor\s*0\./i.test(benefit.statement), false);
});

test('RANGE-05 E2: unknown benefit is labelled unknown; no zero saving or imagined counterpart', () => {
  const unsupported = evidence.rangeMigrationBenefit(null, { migration: FIX.unsupported });
  assert.equal(unsupported.benefit_state, 'unknown');
  assert.equal(unsupported.benefit_eur, null);
  assert.equal(unsupported.counterpart_invented, false);
  assert.match(unsupported.statement, /unknown/i);

  const hypo = evidence.rangeMigrationBenefit(null, { migration: FIX.hypothetical_complete });
  assert.equal(hypo.is_hypothetical, true);
  assert.equal(hypo.benefit_state, 'hypothetical');
  assert.ok(hypo.benefit_eur !== null);
  assert.match(hypo.statement, /hypothetical|sensitivity/i);
  assert.equal(hypo.eligible_commercial_recommendation, false);
});
