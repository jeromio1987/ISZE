#!/usr/bin/env node
/* ===========================================================================
   RUN-01 acceptance tests: Choose and prepare the smallest reusable shared backend.

   How to run
     node --test tests/run_01_shared_backend.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (RUN-01):
     E1  The selected service starts from clean disposable storage and applies
         migrations reproducibly.
     E2  There is one owner of cases and one pricing implementation/contract;
         no second inconsistent financial engine is introduced.

   Synthetic fixtures and disposable temp databases only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const backend = require('../src/case/server/server.js');
const store = require('../src/case/store.js');
const engine = require('../src/engine/engine.js');

const FIXED_NOW = '2026-10-06T12:00:00.000Z';

function tempDb(label) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-run01-' + label + '-'));
  return {
    root,
    dbPath: path.join(root, 'cases.sqlite'),
    cleanup() {
      try { fs.rmSync(root, { recursive: true, force: true }); } catch (e) { /* ignore */ }
    }
  };
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  const body = await res.json();
  return { status: res.status, body };
}

test('RUN-01 E1: The selected service starts from clean disposable storage and applies migrations reproducibly.', async () => {
  const a = tempDb('a');
  const b = tempDb('b');
  let running = null;
  try {
    const first = backend.applyMigrations(a.dbPath, { now: () => FIXED_NOW });
    assert.equal(first.ok, true);
    assert.ok(first.applied.includes('001_init.sql'));
    assert.deepEqual(first.applied_this_run, ['001_init.sql']);

    const again = backend.applyMigrations(a.dbPath, { now: () => FIXED_NOW });
    assert.equal(again.ok, true);
    assert.deepEqual(again.applied_this_run, []);
    assert.deepEqual(again.applied, first.applied);

    const fpA = backend.migrationFingerprint(a.dbPath);

    const onB = backend.applyMigrations(b.dbPath, { now: () => FIXED_NOW });
    assert.equal(onB.ok, true);
    const fpB = backend.migrationFingerprint(b.dbPath);
    assert.deepEqual(fpB.migrations, fpA.migrations);
    assert.deepEqual(fpB.tables, fpA.tables);
    assert.ok(fpA.tables.includes('cases'));
    assert.ok(fpA.tables.includes('schema_migrations'));

    running = backend.startSharedBackend({
      dbPath: a.dbPath,
      host: '127.0.0.1',
      port: 0,
      now: () => FIXED_NOW,
      seed: true
    });
    const addr = await running.ready;
    assert.equal(addr.host, '127.0.0.1');

    const health = await fetchJson(addr.url + '/health');
    assert.equal(health.status, 200);
    assert.equal(health.body.ok, true);
    assert.equal(health.body.storage.kind, 'sqlite');
    assert.equal(health.body.storage.shared, true);
    assert.deepEqual(health.body.fingerprint.migrations, fpA.migrations);
    assert.equal(running.seed.ok, true);
    assert.equal(running.seed.record.case_id, 'SYNTH-RUN01-SEED');

    const listed = await fetchJson(addr.url + '/cases');
    assert.equal(listed.status, 200);
    assert.ok(listed.body.cases.some((c) => c.case_id === 'SYNTH-RUN01-SEED'));

    await running.close();
    running = null;

    // Restart against the same disposable file: migrations stay applied, seed survives.
    running = backend.startSharedBackend({
      dbPath: a.dbPath,
      host: '127.0.0.1',
      port: 0,
      now: () => FIXED_NOW,
      seed: true
    });
    const addr2 = await running.ready;
    const health2 = await fetchJson(addr2.url + '/health');
    assert.equal(health2.body.ok, true);
    assert.deepEqual(health2.body.fingerprint.migrations, fpA.migrations);
    const got = await fetchJson(addr2.url + '/cases/SYNTH-RUN01-SEED');
    assert.equal(got.status, 200);
    assert.equal(got.body.record.case_id, 'SYNTH-RUN01-SEED');
    assert.equal(got.body.record.part_number, 'SYNTH-PART-RUN01');
  } finally {
    if (running) await running.close();
    a.cleanup();
    b.cleanup();
  }
});

test('RUN-01 E2: There is one owner of cases and one pricing implementation/contract; no second inconsistent financial engine is introduced.', async () => {
  const tmp = tempDb('e2');
  let running = null;
  try {
    const own = backend.owners();
    assert.equal(own.cases, 'AIMCaseStore.makeCaseService');
    assert.equal(own.pricing, 'AIMEngine.calculate');

    assert.equal(typeof store.makeCaseService, 'function');
    assert.equal(typeof engine.calculate, 'function');

    const guard = backend.assertNoSecondFinancialEngine();
    assert.equal(guard.ok, true, guard.error);
    assert.deepEqual(guard.offenders, []);

    running = backend.startSharedBackend({
      dbPath: tmp.dbPath,
      host: '127.0.0.1',
      port: 0,
      now: () => FIXED_NOW,
      seed: false
    });
    const addr = await running.ready;

    const created = await fetchJson(addr.url + '/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_id: 'SYNTH-RUN01-E2',
        customer: 'Synthetic customer',
        market: 'SYNTH',
        part_number: 'SYNTH-PART-E2',
        description: 'Synthetic E2 part',
        owner_role: 'case_owner',
        scope_note: 'Synthetic. No real part, customer or price appears in this test.',
        by: 'run-01-e2'
      })
    });
    assert.equal(created.status, 201, JSON.stringify(created.body));
    assert.equal(created.body.ok, true);
    assert.equal(created.body.durable, true);
    assert.equal(created.body.storage.kind, 'sqlite');
    assert.equal(created.body.storage.shared, true);
    assert.equal(created.body.record.case_id, 'SYNTH-RUN01-E2');

    // Case ownership is makeCaseService (versioned record), not a second store.
    assert.equal(created.body.record.version, 1);
    assert.equal(created.body.record.state, 'draft');

    const ownersHttp = await fetchJson(addr.url + '/owners');
    assert.equal(ownersHttp.body.ok, true);
    assert.equal(ownersHttp.body.owners.cases, backend.CASE_OWNER);
    assert.equal(ownersHttp.body.owners.pricing, backend.PRICING_OWNER);

    // Pricing contract remains the single engine entry point; the shared backend
    // does not ship a calculate() of its own.
    const serverDir = path.join(__dirname, '../src/case/server');
    for (const name of fs.readdirSync(serverDir).filter((f) => f.endsWith('.js'))) {
      const src = fs.readFileSync(path.join(serverDir, name), 'utf8');
      assert.equal(/function\s+calculate\s*\(/.test(src), false, name + ' must not define calculate');
    }
    assert.match(String(engine.calculate), /function|=>/);
  } finally {
    if (running) await running.close();
    tmp.cleanup();
  }
});
