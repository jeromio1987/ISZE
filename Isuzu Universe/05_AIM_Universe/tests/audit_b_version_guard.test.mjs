#!/usr/bin/env node
/* ===========================================================================
   Audit fix B (U27): a saved scenario whose stored engine version is older
   than the running engine is refused on reopen.

   How to run
     node --test tests/audit_b_version_guard.test.mjs

   Synthetic fixtures only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync, existsSync } from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const store = require(join(ROOT, 'src', 'case', 'store.js'));
const engine = require(join(ROOT, 'src', 'engine', 'engine.js'));
const appConn = require(process.env.AIM_APP_CONNECTION_PATH || join(ROOT, 'src', 'case', 'app_connection.js'));

const FIXTURE = join(ROOT, 'tests', 'fixtures', 'synthetic_payload.json');
engine.setPayload(JSON.parse(readFileSync(
  existsSync(FIXTURE) ? FIXTURE : join(ROOT, 'payload', 'synthetic_payload.json'), 'utf8')));

const SCENARIO = {
  price_before: 100, price_after: 100, quantity_before: 100, quantity_after: null,
  cost_eur: 60, support_eur: 0, scope: 'all', quantity_label: 'manual scenario', pack_size: 1
};
const OLD_VERSION = 'SYN-OLD-ENGINE-0.0';

function ageEveryEngineVersion(v) {
  if (Array.isArray(v)) return v.map(ageEveryEngineVersion);
  if (v && typeof v === 'object') {
    const o = {};
    for (const k of Object.keys(v)) o[k] = k === 'engine_version' ? OLD_VERSION : ageEveryEngineVersion(v[k]);
    return o;
  }
  return v;
}

test('RUN-02 audit B: reopening a record saved under an older engine version is refused', () => {
  const adapter = store.makeMemoryAdapter();
  const conn = appConn.makeAppConnection({ store, engine, adapter });
  const saved = conn.saveScenario({ case_id: 'SYN-CASE-AUDIT-B', part_number: 'SYN-PN-B', by: 'synthetic' }, SCENARIO);
  assert.equal(saved.ok, true);
  assert.notEqual(engine.CONTRACT_VERSION, OLD_VERSION);

  const fresh = conn.reopenScenario(saved.case_id, saved.version);
  assert.equal(fresh.ok, true, 'control: an unedited record reopens');

  const stored = adapter.load(saved.case_id);
  const aged = ageEveryEngineVersion(stored);
  assert.ok(JSON.stringify(aged).includes(OLD_VERSION), 'the stored record carries an engine version to age');
  adapter.save(saved.case_id, aged);

  const reopened = conn.reopenScenario(saved.case_id, saved.version);
  assert.equal(reopened.engine_version, OLD_VERSION);
  assert.equal(reopened.match.engine_version_match, false);
  assert.equal(reopened.ok, false);
  assert.equal(reopened.ui.status, 'error');
});
