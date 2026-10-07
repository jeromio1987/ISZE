#!/usr/bin/env node
/* ===========================================================================
   RUN-04 acceptance tests: Separate configuration, secrets and restricted
   working files.

   How to run
     node --test tests/run_04_config_separation.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A clean code package and diagnostic log contain no credentials or
         private data tables.
     E2  Missing identity/storage configuration cannot start a seemingly live
         external service with permissive defaults.

   No real secrets are created or read. Synthetic labels only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'config_separation.js'));

test('RUN-04 E1: A clean code package and diagnostic log contain no credentials or private data tables.', () => {
  const pkg = mod.scanPackage([
    { path: 'src/data/config_separation.js', content: 'export function startExternalService() { return { ok: true }; }' },
    { path: 'tests/run_04_config_separation.test.mjs', content: 'synthetic fixture; no secret values' },
    { path: 'README.md', content: 'Development identity is labelled. No participant private tables here.' }
  ]);
  assert.equal(pkg.ok, true);
  assert.equal(pkg.clean, true);
  assert.equal(pkg.findings.length, 0);

  const log = mod.scanDiagnosticLog([
    '2026-10-06T12:00:00Z START synthetic refresh job SYN-JOB-1',
    '2026-10-06T12:00:01Z OK source=SYN-SOURCE version=v1',
    '2026-10-06T12:00:02Z END'
  ]);
  assert.equal(log.ok, true);
  assert.equal(log.clean, true);
  assert.equal(log.findings.length, 0);

  const dirty = mod.scanPackage([
    { path: 'leak.js', content: 'const api_key = "SYNTHETIC_SHOULD_FAIL_SCAN";' }
  ]);
  assert.equal(dirty.clean, false);
  assert.ok(dirty.findings.some((f) => f.kind === 'credential'));
});

test('RUN-04 E2: Missing identity/storage configuration cannot start a seemingly live external service with permissive defaults.', () => {
  const refused = mod.startExternalService({
    mode: 'production',
    identity_configured: false,
    storage_configured: false
  });
  assert.equal(refused.ok, false);
  assert.equal(refused.started, false);
  assert.equal(refused.live_appearance, false);
  assert.equal(refused.permissive_defaults, false);
  assert.equal(refused.code, 'CONFIG_MISSING_FAIL_CLOSED');
  assert.ok(refused.missing.includes('identity'));
  assert.ok(refused.missing.includes('storage'));

  const partial = mod.startExternalService({
    mode: 'live',
    identity_configured: true,
    storage_configured: false
  });
  assert.equal(partial.started, false);
  assert.equal(partial.live_appearance, false);
  assert.equal(partial.permissive_defaults, false);

  const dev = mod.startExternalService({
    mode: 'development',
    development_only: true,
    identity_configured: false,
    storage_configured: false
  });
  assert.equal(dev.started, true);
  assert.equal(dev.live_appearance, false);
  assert.equal(dev.development_only, true);
});
