#!/usr/bin/env node
/* ===========================================================================
   RUN-03 acceptance tests: Run selected refresh jobs without duplication or
   partial state.

   How to run
     node --test tests/run_03_refresh_jobs.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Two simultaneous runs do not accept duplicate activity.
     E2  An interrupted job retains the last accepted source and displays what
         failed; unrelated evidence keeps its own date.

   Disposable synthetic jobs only. No scheduled-job registry or Windows tasks.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'refresh_jobs.js'));

test('RUN-03 E1: Two simultaneous runs do not accept duplicate activity.', () => {
  const runner = mod.makeRefreshRunner({ maxRetries: 1 });
  const pair = runner.runSimultaneous({
    job_id: 'SYN-JOB-A',
    source_id: 'SYN-SOURCE-BILLING',
    version: 'v1',
    evidence_date: '2026-10-01',
    at: '2026-10-06T10:00:00Z',
    payload: { label: 'synthetic_billing_v1' }
  }, {
    job_id: 'SYN-JOB-B',
    source_id: 'SYN-SOURCE-BILLING',
    version: 'v1-dup',
    evidence_date: '2026-10-01',
    at: '2026-10-06T10:00:01Z',
    payload: { label: 'synthetic_billing_dup' }
  });

  assert.equal(pair.first.ok, true);
  assert.equal(pair.first.accepted, true);
  assert.equal(pair.second.ok, false);
  assert.equal(pair.second.accepted, false);
  assert.equal(pair.second.duplicate, true);
  assert.equal(pair.second.code, 'LOCK_HELD');
  assert.equal(runner.getSource('SYN-SOURCE-BILLING').version, 'v1');
});

test('RUN-03 E2: An interrupted job retains the last accepted source and displays what failed; unrelated evidence keeps its own date.', () => {
  const runner = mod.makeRefreshRunner({ maxRetries: 1 });
  const prior = runner.runJob({
    job_id: 'SYN-JOB-PRIOR',
    source_id: 'SYN-SOURCE-PRICES',
    version: 'v3',
    evidence_date: '2026-09-15',
    at: '2026-10-05T09:00:00Z'
  });
  assert.equal(prior.accepted, true);

  runner.acceptSource('SYN-SOURCE-UNRELATED', 'u1', {
    evidence_date: '2026-08-01',
    accepted_at: '2026-08-02T00:00:00Z',
    payload: { label: 'unrelated_evidence' }
  });

  const interrupted = runner.runJob({
    job_id: 'SYN-JOB-INT',
    source_id: 'SYN-SOURCE-PRICES',
    version: 'v4-fail',
    evidence_date: '2026-10-06',
    at: '2026-10-06T11:00:00Z',
    interrupt: true,
    fail_at: 'apply_payload'
  });

  assert.equal(interrupted.ok, false);
  assert.equal(interrupted.interrupted, true);
  assert.equal(interrupted.failed_step, 'apply_payload');
  assert.ok(interrupted.last_accepted);
  assert.equal(interrupted.last_accepted.version, 'v3');
  assert.equal(interrupted.last_accepted.evidence_date, '2026-09-15');
  assert.equal(runner.getSource('SYN-SOURCE-PRICES').version, 'v3');

  const dates = runner.evidenceDates();
  assert.equal(dates['SYN-SOURCE-UNRELATED'], '2026-08-01');
  assert.equal(dates['SYN-SOURCE-PRICES'], '2026-09-15');
  assert.ok(runner.failures().some((f) => f.job_id === 'SYN-JOB-INT'));
});
