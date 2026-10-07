#!/usr/bin/env node
/* ===========================================================================
   RUN-02 acceptance tests: Connect cases and scenarios to the maintained
   application.

   How to run
     node --test tests/run_02_app_connection.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  UI save/reopen matches the identified engine version, exact inputs and
         stored result.
     E2  Tampering with a client-submitted profit/result does not create an
         accepted server-side record.

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
const appConn = require(join(ROOT, 'src', 'case', 'app_connection.js'));

const FIXTURE = join(ROOT, 'tests', 'fixtures', 'synthetic_payload.json');
const payload = JSON.parse(readFileSync(
  existsSync(FIXTURE) ? FIXTURE : join(ROOT, 'payload', 'synthetic_payload.json'),
  'utf8'
));
engine.setPayload(payload);

const SCENARIO = {
  price_before: 100,
  price_after: 100,
  quantity_before: 100,
  quantity_after: null,
  cost_eur: 60,
  support_eur: 0,
  scope: 'all',
  quantity_label: 'manual scenario',
  pack_size: 1
};

test('RUN-02 E1: UI save/reopen matches the identified engine version, exact inputs and stored result.', () => {
  const conn = appConn.makeAppConnection({ store, engine });
  const saved = conn.saveScenario({
    case_id: 'SYN-CASE-RUN02-E1',
    part_number: 'SYN-PN-RUN02',
    by: 'synthetic_ui'
  }, SCENARIO);

  assert.equal(saved.ok, true);
  assert.equal(saved.ui.loading, false);
  assert.equal(saved.ui.status, 'ready');
  assert.equal(saved.snapshot.engine_version, engine.CONTRACT_VERSION);
  assert.deepEqual(saved.snapshot.inputs, SCENARIO);
  assert.ok(saved.snapshot.stored_result);

  const reopened = conn.reopenScenario(saved.case_id, saved.version);
  assert.equal(reopened.ok, true);
  assert.equal(reopened.engine_version, engine.CONTRACT_VERSION);
  assert.deepEqual(reopened.inputs, SCENARIO);
  assert.ok(reopened.stored_result);
  assert.equal(reopened.match.engine_version_match, true);
  assert.equal(reopened.match.inputs_match, true);
  assert.equal(reopened.match.stored_result_present, true);
  assert.deepEqual(reopened.stored_result, saved.snapshot.stored_result);
});

test('RUN-02 E2: Tampering with a client-submitted profit/result does not create an accepted server-side record.', () => {
  const conn = appConn.makeAppConnection({ store, engine });
  const trusted = conn.computeTrusted(SCENARIO);
  const tamperedProfit = Number(trusted.profit_eur) + 9999;

  const rejected = conn.acceptConsequentialRecord({
    new_case_id: 'SYN-CASE-RUN02-E2-TAMPER',
    part_number: 'SYN-PN-RUN02',
    inputs: SCENARIO,
    client_profit_eur: tamperedProfit,
    client_result: Object.assign({}, trusted.result, { gp_after: tamperedProfit })
  });

  assert.equal(rejected.ok, false);
  assert.equal(rejected.accepted, false);
  assert.ok(
    rejected.code === 'CLIENT_PROFIT_TAMPER_REJECTED' ||
      rejected.code === 'CLIENT_RESULT_TAMPER_REJECTED'
  );

  const listed = conn.service.list ? conn.service.list() : null;
  /* Ensure no accepted consequential record was stored for the tamper attempt. */
  if (listed && listed.ok && Array.isArray(listed.cases)) {
    const hit = listed.cases.find((c) => c.case_id === 'SYN-CASE-RUN02-E2-TAMPER');
    assert.ok(!hit || !hit.consequential_acceptance || hit.consequential_acceptance.accepted !== true);
  }

  const honest = conn.acceptConsequentialRecord({
    new_case_id: 'SYN-CASE-RUN02-E2-OK',
    part_number: 'SYN-PN-RUN02',
    inputs: SCENARIO,
    client_profit_eur: trusted.profit_eur
  });
  assert.equal(honest.ok, true);
  assert.equal(honest.accepted, true);
  assert.equal(honest.engine_version, engine.CONTRACT_VERSION);
  assert.equal(Number(honest.profit_eur), Number(trusted.profit_eur));
});
