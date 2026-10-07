#!/usr/bin/env node
/* ===========================================================================
   RUN-08 acceptance tests: Package an internal release and a recoverable
   deployment route.

   How to run
     node --test tests/run_08_release_package.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A second developer can start the release candidate and reproduce the
         selected internal journey from the instructions.
     E2  The delivered source package omits private data and identifies
         unverified/live-use restrictions; no public publishing occurs.

   Build the package locally; do not deploy, upload or publish.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'release_package.js'));

test('RUN-08 E1: A second developer can start the release candidate and reproduce the selected internal journey from the instructions.', () => {
  const packager = mod.makeReleasePackager();
  const pkg = packager.buildPackage({
    version: '0.4.0-internal-u24',
    actual_changes: ['RUN-05 due actions', 'RUN-06 ops measurements'],
    files: [{ path: 'README.md', content: 'internal only' }],
    dependency_lock: 'package-lock.json'
  });
  assert.equal(pkg.ok, true);
  assert.ok(pkg.instructions.build);
  assert.ok(pkg.instructions.start);
  assert.ok(pkg.instructions.test);
  const started = packager.startReleaseCandidate(pkg, {
    journey_steps: [
      { step: 'open', ok: true },
      { step: 'select case', ok: true },
      { step: 'save', ok: true }
    ]
  });
  assert.equal(started.ok, true);
  assert.equal(started.started, true);
  assert.equal(started.journey_reproduced, true);
  assert.equal(started.deployed, false);
  assert.equal(started.published, false);
});

test('RUN-08 E2: The delivered source package omits private data and identifies unverified/live-use restrictions; no public publishing occurs.', () => {
  const packager = mod.makeReleasePackager();
  const dirty = packager.buildPackage({
    version: '0.4.0-bad',
    files: [{ path: 'leak.txt', content: 'participant_private row' }]
  });
  assert.equal(dirty.ok, false);
  assert.equal(dirty.code, 'PRIVATE_DATA_IN_PACKAGE');
  assert.equal(dirty.published, false);

  const plan = packager.buildPackage({
    version: '0.4.0-plan',
    call_task_plan_a_release: true,
    files: [{ path: 'ok.txt', content: 'clean' }]
  });
  assert.equal(plan.ok, false);
  assert.equal(plan.code, 'TASK_PLAN_IS_NOT_A_RELEASE');

  const clean = packager.buildPackage({
    version: '0.4.0-internal-u24',
    actual_changes: ['internal packaging'],
    files: [{ path: 'src/data/release_package.js', content: 'module only' }]
  });
  assert.equal(clean.ok, true);
  assert.equal(clean.restrictions.external_deployment_disabled, true);
  assert.equal(clean.restrictions.unverified_live_use, true);
  assert.equal(clean.restrictions.public_publishing, false);
  assert.equal(clean.published, false);
  assert.equal(clean.deployed, false);
  const deploy = packager.deployExternal();
  assert.equal(deploy.ok, false);
  assert.equal(deploy.deployed, false);
  assert.equal(deploy.published, false);
});
