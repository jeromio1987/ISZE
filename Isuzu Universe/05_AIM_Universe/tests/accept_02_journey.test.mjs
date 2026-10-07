#!/usr/bin/env node
/* ===========================================================================
   ACCEPT-02 acceptance tests: Test the complete browser journey, not only
   isolated screens.

   How to run
     node --test tests/accept_02_journey.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  All claimed working routes complete with the same context and result
         at each step.
     E2  A blocked browser environment is reported as untested, not converted
         into a passed restart/persistence test.

   The live file:// journey is tests/accept/accept_02_journey.py (already in
   accept/run_all.ps1). These node checks pin the two REQUIRED EVIDENCE lines.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'browser_journey.js'));

test('ACCEPT-02 E1: All claimed working routes complete with the same context and result at each step.', () => {
  const ctx = { case_id: 'SYN-J1', objective: 'revenue', scenario_id: 'SYN-J1:v1' };
  const result = { revenue_after: 1100, gp_after: 400 };
  const okSteps = [
    { step: 'select', completed: true, context: ctx, result },
    { step: 'edit', completed: true, context: ctx, result },
    { step: 'save', completed: true, context: ctx, result },
    { step: 'export', completed: true, context: ctx, result },
    { step: 'restart', completed: true, context: ctx, result },
    { step: 'reopen', completed: true, context: ctx, result }
  ];
  const good = mod.verifyRouteContinuity(okSteps);
  assert.equal(good.ok, true, good.statement);
  assert.equal(good.steps_checked, 6);

  const broken = mod.verifyRouteContinuity([
    { step: 'select', completed: true, context: ctx, result },
    { step: 'reopen', completed: true, context: ctx, result: { revenue_after: 999, gp_after: 1 } }
  ]);
  assert.equal(broken.ok, false);
  assert.ok(broken.mismatches.some((m) => m.reason === 'result changed'));
});

test('ACCEPT-02 E2: A blocked browser environment is reported as untested, not converted into a passed restart/persistence test.', () => {
  const blocked = mod.reportBrowserEnvironment({ blocked: true, reason: 'Chrome not available in this environment' });
  assert.equal(blocked.status, 'UNTESTED');
  assert.equal(blocked.passed, false);
  assert.equal(blocked.restart_persistence_passed, false);
  assert.equal(blocked.blocked, true);
  assert.match(blocked.statement, /untested/);

  const notStarted = mod.reportBrowserEnvironment({ started: false });
  assert.equal(notStarted.status, 'UNTESTED');
  assert.equal(notStarted.restart_persistence_passed, false);

  const ready = mod.reportBrowserEnvironment({ started: true, blocked: false });
  assert.equal(ready.status, 'READY');
  assert.equal(ready.blocked, false);
  assert.equal(ready.restart_persistence_passed, null);
});
