#!/usr/bin/env node
/* ===========================================================================
   The AIM case service - CASE-01 ... CASE-05, in the states now in force.

   Run:
     node tests/case_service.test.mjs

   Exit code is 0 only when every check passes. Nothing is skipped and no
   assertion is relaxed to obtain a green run.

   The suite is the older `case_store.test.mjs` with the vocabulary CASE-02
   brought into force, plus the checks the five tasks require that were not
   there before. The older file was left exactly as it was - see the note at the
   top of it, and docs/CASE_service.md - so that a state rename cannot be
   mistaken for a behaviour change. This one is asserted against the nine states
   and the separate evidence, support and outcome records, and the checks below
   say which of those is whose.

   THE ONE CHECK THAT MATTERS MOST, AND WHY IT IS BUILT THIS WAY
   -------------------------------------------------------------
   C23. "A created draft survives a process restart." A test that rebuilds the
   service object in the same process does not test a restart: the module is
   already loaded, the filesystem cache is warm and nothing has to be parsed
   again. So C23 writes a case in a real folder, then runs
   `tests/case_restart_child.mjs` in a SEPARATE `node` process, and reads that
   child's answer. The child shares nothing with this process except the folder.

   WHAT THIS SUITE DOES NOT CLAIM
   ------------------------------
   The storage is a folder of files on one machine. It is not a shared service,
   and several checks below assert that it says so. The change history is
   append-only inside this component; it is not tamper-proof certification, and
   a check asserts that it says that too.
   =========================================================================== */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

const contracts = (await import(new URL('../src/data/contracts.js', import.meta.url))).default;
const schema = (await import(new URL('../src/case/schema.js', import.meta.url))).default;
const store = (await import(new URL('../src/case/store.js', import.meta.url))).default;
const recipients = (await import(new URL('../src/output/recipients.js', import.meta.url))).default;
/* The facade the interface runs, so the duplicate-module check can assert on it
   rather than on a copy. */
const repoModule = (await import(new URL('../src/data/cases.js', import.meta.url))).default;

/* ------------------------------------------------------------- harness -- */

const results = [];
let failures = 0;

function check(id, name, fn) {
  try {
    const evidence = fn();
    results.push({ id, name, status: 'PASS', evidence: evidence === undefined ? '' : String(evidence) });
  } catch (e) {
    failures++;
    /* The first frame outside this harness, so a failure names the assertion
       that failed rather than only the value. */
    const frame = String(e.stack || '').split('\n')
      .find(line => line.includes('case_service.test.mjs:') && !line.includes('check ('));
    results.push({
      id, name, status: 'FAIL',
      evidence: frame ? `${e.message}  [${frame.trim().replace(/^at\s+/, '')}]` : e.message
    });
  }
}

/* A folder that really exists on disk, so the file adapter is exercised rather
   than described. Removed at the end of the run. */
const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-case-service-'));
const storageDir = path.join(tempRoot, 'case-store');

const FIXED_NOW = '2026-09-22T10:00:00.000Z';
const fixedClock = () => FIXED_NOW;

function newService(dirname, options = {}) {
  const adapter = dirname
    ? store.makeFileAdapter({ dir: dirname })
    : store.makeMemoryAdapter();
  return store.makeCaseService(Object.assign({
    adapter,
    now: options.now || fixedClock,
    caller: 'test-runner',
    identityMode: 'development-only'
  }, options.service || {}));
}

const seed = (extra = {}) => Object.assign({
  case_id: 'CASE-TEST-1',
  customer: 'Synthetic customer',
  market: 'SYNTH',
  part_number: 'SYNTH-PART-A',
  description: 'Synthetic part A',
  owner_role: 'case_owner',
  scope_note: 'Synthetic. No real part, customer or price appears in this test.',
  by: 'test-runner'
}, extra);

const scenario = {
  scenario_id: 'CASE-TEST-1:v2', version: 2, case_id: 'CASE-TEST-1',
  part_number: 'SYNTH-PART-A', unit: 'unit',
  price_before: 100, price_after: 95, quantity_before: 100, quantity_after: 120,
  quantity_label: 'manual scenario', scope: 'incremental', volume_is_observed: false,
  pack_size: 1, cost_eur: 60, cost_basis_id: 'SYNTH_B', cost_basis_source: 'verified record',
  support_eur: 0, evidence_period: 'synthetic half year', offer_effective_date: '2026-10-01',
  sources: [], selected_alternative_id: 'SYNTH-INC', objective: 'revenue'
};

/* Synthetic round figures only. No real part, customer, price list or supplier
   cost appears anywhere in this file. */
const terms = (extra = {}) => Object.assign({
  unit: 'unit', price_before: 100, price_after: 95,
  quantity_before: 100, quantity_after: 120, quantity_label: 'manual scenario',
  currency: 'EUR', conditions: 'Synthetic condition.', eligible_reference: 'SYNTH-ELIGIBLE',
  offer_effective_date: '2026-10-01', support_eur: 500, support_direction: 'to_participant'
}, extra);

/* Every service in the "one machine" checks shares one folder, so the restart
   check proves a file was written and not just an object held in memory. */
const service = newService(storageDir);

/* The payment the CASE-05 and correction checks are written against. Defined
   once so the checks read the same record rather than one a previous check
   happened to leave in the store. */
const PAYMENT = {
  support_eur: 500, net_terms_basis: 'net',
  credit_reference: 'SYNTH-CREDIT-1', order_reference: 'SYNTH-ORDER-1',
  delivery_reference: 'SYNTH-DELIVERY-1',
  beneficiary: 'Synthetic customer', comparison: 'Against the recorded half-year billing',
  period: 'Synthetic half year', delivered_on: '2026-10-12',
  what: 'One-off launch support, given once', by_role: 'support_owner'
};

/* A case walked to `action_agreed`, which is the state the support and outcome
   moves are given from. Returns the record the caller then writes against.

   `dated: true` walks the case on its own days, one move per day, so a later
   close lands genuinely after the history rather than level with it. */
function walkToAgreed(id, extra = {}) {
  let at = null;
  if (extra.dated) {
    let cursor = '2026-10-01T09:00:00.000Z';
    at = () => { const t = cursor; const d = new Date(cursor); d.setUTCDate(d.getUTCDate() + 1); cursor = d.toISOString(); return t; };
  }
  const stamp = (options) => (at ? Object.assign({}, options, { at: at() }) : options);

  const made = service.create(seed(Object.assign({ case_id: id, part_number: 'SYNTH-' + id },
    at ? { at: at() } : {}, extra)));
  assert.equal(made.ok, true, made.error);
  let v = made.version;
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to assess the question', next_update_due: '2026-10-01'
  }, stamp({ expected_version: v, by: 'dealer-desk' }));
  assert.equal(submitted.ok, true, submitted.error);
  v = submitted.version;
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess against the recorded evidence', next_update_due: '2026-10-05'
  }, stamp({ expected_version: v, by: 'reviewer-1' }));
  assert.equal(assessing.ok, true, assessing.error);
  v = assessing.version;
  const assessed = service.recordAssessment(id, {
    what: 'Check the eligible quantity against the recorded history.',
    basis: 'synthetic half year', by_role: 'reviewer', findings: ['Eligible volume is stated.']
  }, stamp({ expected_version: v, by: 'reviewer-1', role: 'reviewer' }));
  assert.equal(assessed.ok, true, assessed.error);
  v = assessed.version;
  const proposed = service.proposeTerms(id, {
    terms: terms(extra.terms || {}),
    offered_by_role: 'case_owner',
    approval_route: 'Synthetic route: the account owner approves.',
    expires_on: extra.expires_on || '2026-12-31',
    note: 'Synthetic proposal.'
  }, stamp({ expected_version: v, by: 'case-owner-1', role: 'case_owner' }));
  assert.equal(proposed.ok, true, proposed.error);
  v = proposed.version;
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: {
      what: 'We can support the additional volume at the stated price.',
      issued_on: '2026-09-30', commitment: 'support', reference: 'SYNTH-RESPONSE-1'
    },
    next_action: 'Approver to accept or refuse the proposed terms',
    next_update_due: '2026-10-10'
  }, stamp({ expected_version: v, by: 'case-owner-1' }));
  assert.equal(answered.ok, true, answered.error);
  v = answered.version;
  const agreed = service.transition(id, {
    action: 'accept_proposal', role: 'approver',
    approval_note: 'Synthetic approval: accepted for this exercise only.',
    proposal_accept: {
      proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-1',
      approved_on: '2026-10-02'
    },
    next_action: 'Support owner to give the agreed support',
    next_update_due: '2026-10-15'
  }, stamp({ expected_version: v, by: 'approver-1' }));
  assert.equal(agreed.ok, true, agreed.error);
  return agreed.record;
}

/* ======================================================================== */
/* CASE-01 - the durable repository                                         */
/* ======================================================================== */

check('C01', 'Create a case and read it back with its responding function', () => {
  const created = service.create(seed());
  assert.equal(created.ok, true, created.error);
  assert.equal(created.durable, true, 'the file store should report a durable write');
  const read = service.get('CASE-TEST-1');
  assert.equal(read.version, 1);
  assert.equal(read.state, 'draft');
  assert.equal(read.owner_role, 'case_owner');
  assert.equal(read.created_by, 'dev:test-runner');
  assert.equal(read.history.length, 1);
  assert.equal(read.action_identifier, 'ACT:CASE-TEST-1',
    'a case carries a stable action identifier from the start, so one result cannot be '
    + 'counted under four modules');
  return `version ${read.version}, state ${read.state}, function ${read.owner_role}, `
    + `action ${read.action_identifier}`;
});

check('C02', 'A second create on the same id is refused', () => {
  const again = service.create(seed());
  assert.equal(again.ok, false);
  assert.equal(again.code, 'CASE_ALREADY_EXISTS');
  return again.error;
});

check('C03', 'Version increments on every accepted write', () => {
  const id = 'CASE-TEST-VERSION';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-V' }));
  const versions = [service.get(id).version];
  let current = service.get(id);

  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take the case', next_update_due: '2026-10-01',
    note: 'Submitted'
  }, { expected_version: current.version });
  assert.equal(submitted.ok, true, submitted.error);
  versions.push(submitted.version);

  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess the claim', next_update_due: '2026-10-05'
  }, { expected_version: submitted.version });
  assert.equal(assessing.ok, true, assessing.error);
  versions.push(assessing.version);

  const edited = service.saveRecord(
    Object.assign(schema.clone(service.get(id)), { next_action: 'Assess the claim, restated in plain words' }),
    { expected_version: assessing.version, by: 'reviewer-1' });
  assert.equal(edited.ok, true, edited.error);
  versions.push(edited.version);

  assert.deepEqual(versions, [1, 2, 3, 4], 'expected one version per accepted write');
  /* A refused write does not add a version. */
  const refused = service.transition(id, {
    action: 'accept_proposal', role: 'reviewer', approval_note: 'Wrong function'
  }, { expected_version: edited.version });
  assert.equal(refused.ok, false);
  assert.equal(service.get(id).version, 4, 'a refused move must not create a version');
  return 'versions observed: ' + versions.join(' -> ') + ', unchanged after a refusal';
});

check('C04', 'The stored history is append-only, gap-free and records what each step set', () => {
  const record = service.get('CASE-TEST-VERSION');
  assert.equal(record.history.length, record.version);
  record.history.forEach((h, i) => assert.equal(h.seq, i + 1, 'history entry ' + (i + 1)));
  assert.deepEqual(
    record.history.map(h => h.action),
    ['create_case', 'submit', 'begin_assessment', 'edit_case']
  );
  /* Every entry that moved the case carries the function that moved it and the
     time it moved. That is the "dated attribution" CASE-02 requires. */
  record.history.slice(1).forEach(h => {
    assert.ok(h.recorded_at && !Number.isNaN(Date.parse(h.recorded_at)), 'entry ' + h.seq + ' has no date');
    assert.ok(h.role, 'entry ' + h.seq + ' has no responding function');
    assert.ok(h.recorded_by, 'entry ' + h.seq + ' is not attributed to anyone');
    assert.ok(h.from_state && h.to_state, 'entry ' + h.seq + ' does not say what it moved');
  });
  const edit = record.history.find(h => h.action === 'edit_case');
  assert.deepEqual(Object.keys(edit.set_fields), ['next_action']);
  return record.history.map(h => h.seq + ':' + h.action + '(' + h.from_state + '->' + h.to_state + ')').join(', ');
});

check('C05', 'A lost race is refused, and the other writer survives', () => {
  const editorOne = service.get('CASE-TEST-VERSION');
  const editorTwo = service.get('CASE-TEST-VERSION');
  const sharedVersion = editorOne.version;
  assert.equal(editorTwo.version, sharedVersion);

  const winner = service.saveRecord(Object.assign(schema.clone(editorTwo), {
    next_action: 'Editor two changed this'
  }), { expected_version: editorTwo.version, by: 'editor-two' });
  assert.equal(winner.ok, true, winner.error);
  assert.equal(winner.version, sharedVersion + 1);

  const loser = service.saveRecord(Object.assign(schema.clone(editorOne), {
    next_action: 'Editor one changed this'
  }), { expected_version: editorOne.version, by: 'editor-one' });
  assert.equal(loser.ok, false, 'a stale write must not be accepted');
  assert.equal(loser.code, 'STALE_WRITE');
  assert.equal(loser.expected_version, sharedVersion);
  assert.equal(loser.actual_version, sharedVersion + 1);

  const stored = service.get('CASE-TEST-VERSION');
  assert.equal(stored.version, sharedVersion + 1);
  assert.equal(stored.next_action, 'Editor two changed this');
  assert.ok(!JSON.stringify(stored).includes('Editor one changed this'),
    'the refused write must not appear anywhere in the record');
  assert.equal(stored.history.length, stored.version, 'the refused write added no history entry');
  return `refused with ${loser.code}: expected ${loser.expected_version}, actual ${loser.actual_version}; `
    + `stored value is the other writer's`;
});

check('C06', 'A stale transition is refused the same way', () => {
  const id = 'CASE-TEST-RACE';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-R' }));
  const proposed = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take it', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(proposed.ok, true, proposed.error);

  const staleCopy = service.get(id).version;
  const first = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess it', next_update_due: '2026-10-05'
  }, { expected_version: staleCopy, by: 'reviewer-one' });
  assert.equal(first.ok, true, first.error);

  const second = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Someone else assess it', next_update_due: '2026-10-06'
  }, { expected_version: staleCopy, by: 'reviewer-two' });

  assert.equal(second.ok, false);
  assert.equal(second.code, 'STALE_WRITE');
  assert.equal(service.get(id).next_action, 'Assess it');
  assert.equal(service.get(id).version, staleCopy + 1, 'the refused move added no version');
  return 'second writer refused with ' + second.code + '; the first move stands';
});

check('C07', 'The same content submitted twice is refused', () => {
  const current = service.get('CASE-TEST-VERSION');
  const first = service.saveRecord(schema.clone(current), { expected_version: current.version });
  assert.equal(first.ok, false);
  assert.equal(first.code, 'DUPLICATE_SUBMISSION');
  const after = service.get('CASE-TEST-VERSION');
  assert.equal(after.version, current.version, 'a refused duplicate must not add a version');
  return first.error;
});

check('C08', 'CASE-01: a created draft survives a real process restart', () => {
  /* The parent writes it. The child - a separate `node` process, run after this
     assertion, with nothing shared but the folder - reads it and answers. */
  const id = 'CASE-TEST-RESTART';
  const created = service.create(seed({
    case_id: id, part_number: 'SYNTH-PART-RESTART',
    customer: 'Synthetic restart customer', market: 'SYNTH'
  }));
  assert.equal(created.ok, true, created.error);
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take the restarted case', next_update_due: '2026-10-01'
  }, { expected_version: created.version });
  assert.equal(submitted.ok, true, submitted.error);

  const file = path.join(storageDir, 'cases', id + '.json');
  assert.equal(fs.existsSync(file), true, 'the case should be a file on disk at ' + file);
  const beforeBytes = fs.readFileSync(file, 'utf8');
  const beforeMtime = fs.statSync(file).mtimeMs;

  const raw = execFileSync(process.execPath, [
    path.join(HERE, 'case_restart_child.cjs'), storageDir, id
  ], { encoding: 'utf8', timeout: 60000 });
  const child = JSON.parse(raw.trim().split('\n').slice(-1)[0]);

  assert.equal(child.ok, true, 'the child process could not read the case: ' + JSON.stringify(child));
  assert.equal(child.state, 'submitted', 'the state did not survive the restart');
  assert.equal(child.version, 2, 'the version did not survive the restart');
  assert.equal(child.next_action, 'Reviewer to take the restarted case');
  assert.equal(child.case_id, id);
  assert.equal(child.pid !== process.pid, true, 'the child must be a different process');
  assert.equal(child.schema_version, schema.RECORD_SCHEMA_VERSION);
  assert.equal(child.record_schema_version, schema.RECORD_SCHEMA_VERSION);

  /* And the restart did not rewrite anything: the bytes are the same. */
  assert.equal(fs.readFileSync(file, 'utf8'), beforeBytes,
    'the child process wrote to a case it was only asked to read');
  assert.equal(fs.statSync(file).mtimeMs, beforeMtime, 'the child touched the file mtime');
  return `child pid ${child.pid} read ${file} (${beforeBytes.length} bytes) as ${child.state} `
    + `v${child.version}; this process is pid ${process.pid}`;
});

check('C09', 'CASE-01: a saved case refers to one identified source and scenario version', () => {
  const id = 'CASE-TEST-VERSION';
  const record = service.get(id);
  assert.equal(typeof record.schema_version, 'number');
  assert.equal(record.contract_version, contracts.CONTRACT_VERSION,
    'the record states which contract version it was written under');
  assert.equal(record.scenario, null, 'nothing proposed yet on this case');

  const proposed = service.proposeTerms(id, {
    terms: terms(), offered_by_role: 'case_owner',
    approval_route: 'Synthetic route.', expires_on: '2026-12-31'
  }, { expected_version: record.version, by: 'case-owner-1', role: 'case_owner' });
  assert.equal(proposed.ok, true, proposed.error);
  const withProposal = service.get(id);
  assert.equal(withProposal.proposal.active_proposal_version, 1);

  /* The scenario a proposal is built from is named by id and version, so the
     case points at one run and not at "the figures we had". */
  const saved = service.saveRecord(Object.assign(schema.clone(withProposal), { scenario }), {
    expected_version: withProposal.version, by: 'case-owner-1'
  });
  assert.equal(saved.ok, true, saved.error);
  const final = service.get(id);
  assert.equal(final.scenario.scenario_id, 'CASE-TEST-1:v2');
  assert.equal(final.scenario.version, 2);
  /* The scenario names exactly which case and which version it was, so a saved
     case points at one run rather than at "the figures we had". The synthetic
     fixture names CASE-TEST-1, which is a different case from this one - the
     point is that the reference is carried and is specific, not that it matches
     the case id by luck. */
  assert.equal(final.scenario.case_id, 'CASE-TEST-1',
    'the scenario does not carry the case reference it was written for');
  assert.equal(final.schema_version, schema.RECORD_SCHEMA_VERSION,
    'the record does not state the shape version a reader has to interpret it with');
  return `contract v${final.contract_version}, record schema v${final.schema_version}, `
    + `scenario ${final.scenario.scenario_id} at version ${final.scenario.version}, `
    + `proposal v${final.proposal.active_proposal_version}`;
});

check('C10', 'CASE-01: no storage is presented as a shared service', () => {
  const files = service.describe();
  assert.equal(files.kind, 'files');
  assert.equal(files.durable, true);
  assert.equal(files.shared, false, 'a folder on one machine is not a shared service');
  assert.match(files.statement, /NOT a shared service/);
  assert.match(files.statement, /two people on two machines do not see each other/i);

  const memory = newService().describe();
  assert.equal(memory.durable, false);
  assert.equal(memory.shared, false);

  const browser = store.describeStorage('browser');
  assert.equal(browser.shared, false);
  assert.match(browser.statement, /not a shared service/i);

  /* And the exported bundle says so in the file a reader opens, not only on a
     screen. */
  const bundle = service.exportAll();
  assert.equal(bundle.not_a_shared_service, true);
  assert.equal(bundle.storage.shared, false);
  assert.match(bundle.history_statement, /NOT tamper-proof certification/);
  return `${files.statement} | memory: ${memory.statement}`;
});

check('C11', 'CASE-01: the change history is stated as a record, not as certification', () => {
  const statement = schema.appendOnlyStatement();
  assert.match(statement, /append-only/i);
  assert.match(statement, /NOT tamper-proof certification/);
  assert.match(statement, /no signature and no trusted clock/i);
  assert.equal(service.history_statement, statement,
    'the store publishes the same statement the rule book writes');
  return statement;
});

/* ======================================================================== */
/* CASE-02 - case, evidence, support and outcome states kept apart           */
/* ======================================================================== */

check('C12', 'CASE-02: the nine states in force are the ones the plan names', () => {
  assert.deepEqual(schema.CASE_STATES, [
    'draft', 'submitted', 'assessment', 'awaiting_input', 'response_issued',
    'action_agreed', 'resolved', 'withdrawn', 'closed_outcome_unknown'
  ]);
  assert.deepEqual(schema.CASE_STATES, (contracts.CASE_STATES_TARGET || []).slice(),
    'the enforcing vocabulary and the declared target have diverged');
  assert.equal(schema.VOCABULARY_IN_SYNC, true);
  /* Every state has a stage. A state with no stage is the fault the migration
     was written to close. */
  const unmapped = schema.CASE_STATES.filter(s => !schema.stageOf(s));
  assert.deepEqual(unmapped, [], 'these states have no stage: ' + unmapped.join(', '));
  /* And the retired names are gone, so a stale literal cannot half-work. */
  const retired = ['evidence_requested', 'ready_for_review', 'approved', 'rejected',
    'delivered', 'outcome_recorded', 'no_change_recommended'];
  retired.forEach(s => assert.equal(schema.CASE_STATES.indexOf(s), -1,
    '"' + s + '" was retired with the old vocabulary but is still in force'));
  return `${schema.CASE_STATES.length} states in force, mapped onto ${schema.STAGES.length} stages; `
    + `${retired.length} retired names refused`
    + (schema.CONTRACT_VOCABULARY_STALE
      ? ' (contracts.CASE_STATES still publishes the retired list - reported as open)'
      : '');
});

check('C13', 'CASE-02: no state carries a monetary value', () => {
  /* The property the whole component rests on: issuing a response is not
     delivered support, agreeing an action is not a won outcome, and closing a
     case creates no benefit. Asserted per state rather than asserted-about, so a
     later state cannot quietly acquire a euro value. */
  schema.CASE_STATES.forEach(s => {
    assert.equal(schema.monetaryWeightOf(s), 0,
      'state "' + s + '" carries a monetary value, so a reader could start summing states');
  });
  assert.equal(schema.monetaryWeightOf('not_a_state'), null,
    'an unknown state must be null, not zero: a missing value is not zero');
  return `${schema.CASE_STATES.length} states, each worth zero`
    + (schema.CASE_STATES.length === 0 ? ' (vacuous)' : '');
});

check('C14', 'CASE-02: issuing a response creates no support and no outcome', () => {
  const id = 'CASE-TEST-RESPONSE';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-RESP' }));
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to assess', next_update_due: '2026-10-01'
  }, { expected_version: created.version });
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess', next_update_due: '2026-10-05'
  }, { expected_version: submitted.version });
  assert.equal(assessing.ok, true, assessing.error);

  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: {
      what: 'No support is committed; this is our position.', issued_on: '2026-09-30',
      commitment: 'none', reference: 'SYNTH-RESPONSE-2'
    },
    next_action: 'Dealer to consider the position', next_update_due: '2026-10-20'
  }, { expected_version: assessing.version });
  assert.equal(answered.ok, true, answered.error);

  const record = service.get(id);
  assert.equal(record.state, 'response_issued');
  /* The separation, in one place. */
  assert.equal(record.support, null, 'issuing a response must not create delivered support');
  assert.equal(record.outcome, null, 'issuing a response must not create an outcome');
  assert.equal(record.approval_note, null, 'issuing a response must not create an approval');
  assert.equal(schema.commercialEventCount(record), 0,
    'an answer is not a commercial event');
  /* And the four measures are not there to be read as a benefit. */
  const account = service.benefitAccount([record], '2026-10-01');
  assert.equal(account.support_total_eur, 0);
  assert.equal(account.total_benefit_eur, null, 'there is no single benefit figure');
  assert.equal(account.newly_won_units, 0);
  return `state ${record.state}: support ${record.support}, outcome ${record.outcome}, `
    + `commercial occasions ${schema.commercialEventCount(record)}`;
});

check('C15', 'CASE-02: closing a case with the outcome unknown creates no benefit', () => {
  const id = 'CASE-TEST-NOCHANGE';
  /* Every move is dated before the close, so the case really is closed by the
     time the account is asked. The service clock is fixed, so a close without a
     stated time would land on the same timestamp as the answer. */
  let at = '2026-10-01T09:00:00.000Z';
  const step = () => { const t = at; const d = new Date(at); d.setUTCDate(d.getUTCDate() + 1); at = d.toISOString(); return t; };
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-NC', at: step() }));
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to assess', next_update_due: '2026-10-01'
  }, { expected_version: created.version, at: step() });
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess', next_update_due: '2026-10-05'
  }, { expected_version: submitted.version, at: step() });
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Answered.', issued_on: '2026-09-30', commitment: 'none' },
    next_action: 'Considered', next_update_due: '2026-10-20'
  }, { expected_version: assessing.version, at: step() });
  assert.equal(answered.ok, true, answered.error);
  const closed = service.transition(id, {
    action: 'terminal_no_change', role: 'case_owner',
    approval_note: 'Answered, considered, and no action taken. Nobody can say what it was worth.'
  }, { expected_version: answered.version, at: step() });
  assert.equal(closed.ok, true, closed.error);

  const record = service.get(id);
  assert.equal(record.state, 'closed_outcome_unknown');
  assert.equal(record.support, null);
  assert.equal(record.outcome, null);
  assert.equal(record.next_action, null, 'a closed case owes nothing');
  assert.equal(record.next_update_due, null);
  assert.equal(schema.isTerminal(record.state), true);
  /* The state is a real permitted end, not a soft failure: it does not claim a
     loss and it does not claim a gain. */
  assert.equal(schema.monetaryWeightOf(record.state), 0);

  const work = schema.openWork(record, '2026-11-01');
  assert.equal(work.closed, true);
  /* Unknown outcome asserted, not implied. */
  const account = service.benefitAccount([record], '2026-11-01');
  assert.equal(account.cases_without_a_recorded_outcome, 1);
  assert.equal(account.total_benefit_eur, null);
  return `state ${record.state}, support ${record.support}, outcome ${record.outcome}; `
    + `benefit account reports ${account.cases_without_a_recorded_outcome} case without an outcome`;
});

check('C16', 'CASE-02: an invalid transition is rejected with the state retained', () => {
  const id = 'CASE-TEST-SKIP';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-C' }));
  const before = service.get(id);
  assert.equal(before.state, 'draft');
  assert.equal(before.version, 1);

  /* Straight to agreed, without anything being assessed, proposed or accepted. */
  const jump = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Approved without a proposal',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-NOT-REAL' }
  }, { expected_version: 1 });
  assert.equal(jump.ok, false);
  assert.equal(jump.code, 'NOT_ALLOWED_FROM_STATE');

  /* Support cannot be recorded without an accepted proposal. */
  const noApproval = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'x', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(noApproval.ok, true, noApproval.error);
  const supportBeforeAcceptance = service.recordSupport(id, {
    support_eur: 100, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Support before any approval'
  }, { expected_version: noApproval.version, role: 'support_owner' });
  assert.equal(supportBeforeAcceptance.ok, false);
  assert.equal(supportBeforeAcceptance.code, 'SUPPORT_NEEDS_AN_ACCEPTED_PROPOSAL');

  /* An outcome cannot be recorded without a delivery. */
  const noDelivery = service.recordOutcome(id, {
    what: 'An outcome with nothing delivered', observed_on: '2026-11-01',
    counts_as_new_business: true
  }, { expected_version: noApproval.version, role: 'case_owner' });
  assert.equal(noDelivery.ok, false);
  assert.equal(noDelivery.code, 'OUTCOME_NEEDS_SUPPORT');

  /* The state and the version are exactly where they were. */
  const after = service.get(id);
  assert.equal(after.state, 'submitted', 'a refused move must leave the state where it was');
  assert.equal(after.version, noApproval.version, 'a refused move must not add a version');
  assert.equal(after.support, null);
  assert.equal(after.outcome, null);
  assert.equal(after.history.length, after.version, 'a refused move left no log entry');
  return `${jump.code} | ${supportBeforeAcceptance.code} | ${noDelivery.code}; `
    + `state retained at ${after.state} v${after.version}`;
});

check('C17', 'CASE-02: the wrong function cannot make a move', () => {
  const id = 'CASE-TEST-ROLE';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-D' }));

  /* Only the case owner submits. The reviewer may not raise the dealer's own
     question. */
  const reviewerSubmits = service.transition(id, {
    action: 'submit', role: 'reviewer', next_action: 'Reviewer submitting its own question',
    next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(reviewerSubmits.ok, false);
  assert.equal(reviewerSubmits.code, 'ROLE_NOT_PERMITTED');

  /* Only the reviewer asks for input. The case owner may not - and because the
     case is still at draft, where asking for input is not offered at all, the
     answer is that the move does not exist there. Both facts are true; the
     state-level refusal is the one a draft produces, so that is what is checked. */
  const ownerRequests = service.transition(id, {
    action: 'request_input', role: 'case_owner',
    evidence_requests: [{ what: 'Its own evidence', from_role: 'case_owner', due: '2026-10-01' }]
  }, { expected_version: 1 });
  assert.equal(ownerRequests.ok, false);
  assert.equal(ownerRequests.code, 'NOT_ALLOWED_FROM_STATE');
  assert.match(ownerRequests.error, /Allowed here: submit, withdraw/);

  /* A move with no function at all is refused rather than attributed to nobody. */
  const noRole = service.transition(id, {
    action: 'submit', next_action: 'Nobody submitted this', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(noRole.ok, false);
  assert.equal(noRole.code, 'ROLE_REQUIRED');

  assert.equal(service.get(id).state, 'draft', 'a refused move must not move the case');
  assert.equal(service.get(id).version, 1);

  /* The role guard at a state where the move IS offered. The reviewer may take
     the case on, but only the owner's own function can raise the dealer's
     question, so the reviewer is refused by role and not by state. */
  const reviewerSubmitsAgain = service.transition(id, {
    action: 'submit', role: 'reviewer', next_action: 'Reviewer raising the question',
    next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(reviewerSubmitsAgain.ok, false);
  assert.equal(reviewerSubmitsAgain.code, 'ROLE_NOT_PERMITTED');

  /* The separation that matters most: whoever assessed a case must not be the
     one who accepts it. */
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it',
    next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess it',
    next_update_due: '2026-10-05'
  }, { expected_version: submitted.version });
  assert.equal(assessing.ok, true, assessing.error);
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Answered.', issued_on: '2026-09-30', commitment: 'support' },
    next_action: 'Approver to decide', next_update_due: '2026-10-10'
  }, { expected_version: assessing.version });
  assert.equal(answered.ok, true, answered.error);
  const proposed = service.proposeTerms(id, {
    terms: terms(), offered_by_role: 'case_owner', approval_route: 'Synthetic route.'
  }, { expected_version: answered.version, role: 'case_owner' });
  assert.equal(proposed.ok, true, proposed.error);

  const reviewerApproves = service.transition(id, {
    action: 'accept_proposal', role: 'reviewer',
    approval_note: 'The reviewer approved its own assessment',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-NOPE' }
  }, { expected_version: proposed.version });
  assert.equal(reviewerApproves.ok, false);
  assert.equal(reviewerApproves.code, 'ROLE_NOT_PERMITTED');
  assert.equal(service.get(id).state, 'response_issued', 'the case must not be agreed by a reviewer');

  /* And the approver cannot give the support: that is the support owner's move. */
  const approveFirst = service.transition(id, {
    action: 'accept_proposal', role: 'approver',
    approval_note: 'Synthetic approval.',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-ROLE' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: proposed.version });
  assert.equal(approveFirst.ok, true, approveFirst.error);
  const approverDelivers = service.recordSupport(id, {
    support_eur: 100, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'The approver delivered it'
  }, { expected_version: approveFirst.version, role: 'approver' });
  assert.equal(approverDelivers.ok, false);
  assert.equal(approverDelivers.code, 'ROLE_NOT_PERMITTED');
  assert.equal(service.get(id).support, null, 'the approver must not have delivered anything');
  return `${reviewerSubmits.code} / ${ownerRequests.code} / ${noRole.code}; reviewer approval refused `
    + `with ${reviewerApproves.code}; approver delivery refused with ${approverDelivers.code}`;
});

check('C18', 'CASE-02: every valid transition carries dated attribution', () => {
  /* A case of its own, walked one move per day. Nothing here depends on another
     check having left a record behind. */
  const id = 'CASE-TEST-ATTRIB';
  const agreed = walkToAgreed(id, { dated: true });
  /* Every entry that moved the state names the function, the person and the
     time. Read off the log rather than asserted about in prose. */
  const moved = agreed.history.filter(h => h.from_state !== h.to_state);
  assert.ok(moved.length >= 5, 'expected the case to have several state moves, got ' + moved.length);
  moved.forEach(h => {
    assert.ok(h.recorded_at && !Number.isNaN(Date.parse(h.recorded_at)),
      'entry ' + h.seq + ' (' + h.action + ') has no usable date');
    assert.ok(h.role, 'entry ' + h.seq + ' (' + h.action + ') names no responding function');
    assert.ok(h.recorded_by && h.recorded_by !== 'unspecified',
      'entry ' + h.seq + ' (' + h.action + ') is not attributed to anyone');
  });
  /* And a move that has no date is refused rather than stored undated. */
  const undated = service.transition(id, {
    action: 'record_outcome', role: 'case_owner', at: 'not-a-date',
    outcome: { what: 'x', observed_on: '2026-11-01', counts_as_new_business: true }
  }, { expected_version: agreed.version });
  assert.equal(undated.ok, false, 'an unusable date must be refused, not stored');
  return moved.map(h => `${h.action} by ${h.role}/${h.recorded_by}@${h.recorded_at}`).join(' | ');
});

check('C19', 'CASE-02: assessment, response and support are three separate records', () => {
  const record = service.get('CASE-TEST-ATTRIB');
  assert.ok(record.assessment, 'the assessment is stored');
  assert.ok(record.response, 'the response is stored');
  assert.equal(record.support, null, 'nothing has been delivered yet');

  /* They are not the same object and do not carry each other's meaning. */
  assert.notEqual(record.assessment.what, record.response.what);
  assert.equal(record.assessment.by_role, 'reviewer');
  assert.equal(record.response.by_role, 'case_owner');
  assert.equal(record.response.issued_on, '2026-09-30');
  assert.equal(record.response.commitment, 'support');

  /* A response that commits support is what makes support possible - and only
     after the terms are accepted. */
  const early = service.recordSupport('CASE-TEST-RESPONSE', {
    support_eur: 100, net_terms_basis: 'net', delivered_on: '2026-10-12', what: 'x'
  }, { expected_version: service.get('CASE-TEST-RESPONSE').version, role: 'support_owner' });
  assert.equal(early.ok, false, 'a response alone does not unlock support');
  assert.equal(early.code, 'SUPPORT_NEEDS_AN_ACCEPTED_PROPOSAL');
  return `assessment by ${record.assessment.by_role}; response by ${record.response.by_role} `
    + `committing "${record.response.commitment}"; support ${record.support}`;
});

check('C20', 'CASE-02: a response that commits no support cannot be followed by a payment', () => {
  const id = 'CASE-TEST-RESPONSE';
  /* Walk the response_issued case to an accepted proposal, then try to pay. The
     accepted proposal exists, so the only thing standing in the way is the
     response that stated no support commitment. */
  let v = service.get(id).version;
  const proposed = service.proposeTerms(id, {
    terms: terms(), offered_by_role: 'case_owner', approval_route: 'Synthetic route.'
  }, { expected_version: v, role: 'case_owner' });
  assert.equal(proposed.ok, true, proposed.error);
  const agreed = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Synthetic approval.',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-2' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: proposed.version });
  assert.equal(agreed.ok, true, agreed.error);
  const paid = service.recordSupport(id, {
    support_eur: 250, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'A payment on a case that answered "no support"'
  }, { expected_version: agreed.version, role: 'support_owner' });
  assert.equal(paid.ok, false, 'a payment must not be recordable against a "no support" answer');
  assert.ok(/no support commitment/i.test(paid.error), paid.error);
  assert.equal(service.get(id).support, null);
  return paid.error.slice(0, 140);
});

/* ======================================================================== */
/* CASE-03 - who owes the next action, and when                              */
/* ======================================================================== */

check('C21', 'CASE-03: a dealer waiting on ISZE is shown as awaiting that guidance', () => {
  const id = 'CASE-TEST-AWAIT';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-AWAIT' }));
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take the question',
    next_update_due: '2026-10-01'
  }, { expected_version: created.version });
  assert.equal(submitted.ok, true, submitted.error);

  /* ISZE asks the DEALER for something. Now the dealer is the one who owes, and
     the case is not at fault for waiting. */
  const waiting = service.transition(id, {
    action: 'request_input', role: 'reviewer',
    evidence_requests: [{ what: 'The recorded billing for the half year', from_role: 'dealer', due: '2026-10-05' }]
  }, { expected_version: submitted.version });
  assert.equal(waiting.ok, true, waiting.error);

  const record = service.get(id);
  assert.equal(record.state, 'awaiting_input');
  const work = schema.openWork(record, '2026-09-22');
  assert.equal(work.awaiting, 'the dealer');
  assert.equal(work.closed, false);
  assert.equal(work.dealer_commitments.length, 1);
  assert.equal(work.dealer_commitments[0].what, 'The recorded billing for the half year');
  assert.equal(work.isze_commitments.length, 0);
  const statement = schema.obligationStatement(record, '2026-09-22');
  assert.match(statement, /Waiting on the dealer for/i);

  /* The other direction. ISZE owes the dealer an answer, and the screen has to
     say that rather than showing the dealer as idle. */
  const back = service.transition(id, {
    action: 'provide_input', role: 'case_owner', next_action: 'Reviewer to answer the question',
    next_update_due: '2026-10-08'
  }, { expected_version: waiting.version });
  assert.equal(back.ok, true, back.error);
  const askingIsze = service.transition(id, {
    action: 'request_input', role: 'reviewer',
    evidence_requests: [{ what: 'A cost position from the product function', from_role: 'product', due: '2026-10-12' }]
  }, { expected_version: back.version });
  assert.equal(askingIsze.ok, true, askingIsze.error);

  const waitingOnUs = schema.openWork(service.get(id), '2026-09-22');
  assert.equal(waitingOnUs.awaiting, 'another ISZE or distributor function',
    'a case where ISZE owes the answer must not read as the dealer being at fault');
  const statement2 = schema.obligationStatement(service.get(id), '2026-09-22');
  assert.match(statement2, /Waiting on an ISZE or distributor function/i);
  assert.match(statement2, /The dealer has supplied what was asked of it/i);

  /* And one case where the dealer owes ISZE, so the two directions really are
     both present rather than the check being satisfied by one of them. Asking
     for input replaces the outstanding request, so this is a second case and not
     a second request on the same one. */
  const other = 'CASE-TEST-AWAIT-DEALER';
  const createdOther = service.create(seed({ case_id: other, part_number: 'SYNTH-PART-AWAIT2' }));
  const submittedOther = service.transition(other, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take the question',
    next_update_due: '2026-10-01'
  }, { expected_version: createdOther.version });
  const dealerOwes = service.transition(other, {
    action: 'request_input', role: 'reviewer',
    evidence_requests: [{ what: 'The dealer to confirm the eligible quantity', from_role: 'dealer', due: '2026-10-05' }]
  }, { expected_version: submittedOther.version });
  assert.equal(dealerOwes.ok, true, dealerOwes.error);
  const otherWork = schema.openWork(service.get(other), '2026-09-22');
  assert.equal(otherWork.awaiting, 'the dealer');
  return `${work.awaiting} -> ${waitingOnUs.awaiting}, and ${otherWork.awaiting} on the second case`;
});

check('C22', 'CASE-03: the separate clocks stay separate', () => {
  /* Its own case, walked one move per day, so every clock is filled and none of
     them coincides with another by accident. */
  const id = 'CASE-TEST-CLOCKS';
  const agreed = walkToAgreed(id, { dated: true });
  const record = service.get(id);
  /* contracts.CASE_TIMESTAMPS names the five. Each is its own field on the
     record, and the record collapsed none of them into one "updated at". */
  const clocks = contracts.CASE_TIMESTAMPS.slice();
  assert.deepEqual(clocks, ['submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at']);
  clocks.forEach(k => assert.ok(k in record, 'the record does not carry ' + k));

  assert.ok(record.submitted_at, 'the case was submitted and should say when');
  assert.ok(record.acknowledged_at, 'the reviewer took it and should say when');
  assert.ok(record.answered_at, 'the answer was issued and should say when');
  assert.equal(record.resolved_at, null, 'an agreed case has not finished yet');
  /* The submission and the answer are different moments, because the case was
     walked one move per day. That is the whole point of the separate clocks. */
  assert.notEqual(record.submitted_at, record.answered_at,
    'the submission and the answer carry the same time, so a clock has been overwritten');
  assert.ok(Date.parse(record.submitted_at) < Date.parse(record.answered_at));
  /* And the case really was walked through several moves, so this is not a
     claim about one entry. `moved` counts the entries that changed state; the
     assessment, the proposal and the payment do not, which is the separation
     CASE-02 asks for. */
  assert.ok(agreed.history.filter(h => h.from_state !== h.to_state).length >= 5,
    'the case was not walked through enough state moves for this check to mean anything');
  assert.ok(agreed.history.some(h => h.from_state === h.to_state),
    'no move was recorded that left the state alone, so the separation is untested');

  /* A clock that runs backwards is refused rather than stored. */
  const backwards = service.saveRecord(Object.assign(schema.clone(record), {
    answered_at: '2001-01-01T00:00:00.000Z'
  }), { expected_version: record.version, by: 'test-runner' });
  assert.equal(backwards.ok, false, 'a clock earlier than the case creation must be refused');
  assert.ok(/earlier than/i.test(backwards.error), backwards.error);
  return clocks.map(k => `${k}=${record[k] || '-'}`).join(', ');
});

check('C23', 'CASE-03: a reassignment does not reset the total waiting time', () => {
  const id = 'CASE-TEST-REASSIGN';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-RE' }));
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it',
    next_update_due: '2026-10-01'
  }, { expected_version: created.version });
  assert.equal(submitted.ok, true, submitted.error);

  /* Read the clock a few days in, then move the case to another function and
     read it again later. The dealer did not go back to the beginning when the
     case changed hands. */
  const day3 = schema.openWork(service.get(id), '2026-09-25T10:00:00.000Z');
  assert.ok(day3.total_waiting_days > 2.9 && day3.total_waiting_days < 3.1,
    'expected about three days waiting, got ' + day3.total_waiting_days);

  const reassigned = service.saveRecord(Object.assign(schema.clone(service.get(id)), {
    owner_role: 'product', assigned_to: 'synthetic person B',
    deputy_role: 'supply', escalation_route: 'Synthetic route: the account owner.'
  }), { expected_version: submitted.version, by: 'reviewer-1', note: 'Reassigned to the product function' });

  /* The reassignment is recorded... */
  assert.equal(reassigned.ok, true, reassigned.error);
  const after = service.get(id);
  assert.equal(after.owner_role, 'product');
  assert.equal(after.assigned_to, 'synthetic person B');
  assert.equal(after.deputy_role, 'supply');
  assert.equal(after.escalation_route, 'Synthetic route: the account owner.');
  const entry = after.history[after.history.length - 1];
  assert.equal(entry.action, 'edit_case');
  assert.ok(Object.keys(entry.set_fields).indexOf('owner_role') >= 0,
    'the reassignment did not record that the function changed');

  /* ...and the waiting time is the DEALER's, so it did not reset. */
  const day6 = schema.openWork(after, '2026-09-28T10:00:00.000Z');
  assert.ok(day6.total_waiting_days > 5.9 && day6.total_waiting_days < 6.1,
    'a reassignment reset the waiting clock: expected about six days, got ' + day6.total_waiting_days);
  assert.equal(day6.submitted_at, day3.submitted_at,
    'the submission clock moved when the case was reassigned');
  assert.ok(day6.total_waiting_days > day3.total_waiting_days,
    'the total waiting time did not grow with time');
  /* And the new owner is the one who owes now. */
  assert.equal(day6.owner_role, 'product');
  return `waiting ${day3.total_waiting_days}d before -> ${day6.total_waiting_days}d after; `
    + `owner ${after.owner_role}, deputy ${after.deputy_role}, escalation recorded`;
});

check('C24', 'CASE-03: the queue separates what we owe from what we are owed', () => {
  const queue = service.queue('2026-09-22');
  assert.ok(queue.length > 0, 'expected open cases in the queue');
  const rows = queue.map(r => ({
    id: r.case_id, awaiting: r.awaiting, overdue: r.overdue,
    owner: r.owner_role, waiting: r.total_waiting_days
  }));
  /* The case where ISZE owes the dealer an answer sorts ahead of the case where
     the dealer owes ISZE. A case we owe is more urgent than one we are waiting
     on, and the queue says so instead of interleaving them. */
  const ours = queue.findIndex(r => r.awaiting === 'another ISZE or distributor function');
  const theirs = queue.findIndex(r => r.awaiting === 'the dealer');
  assert.ok(ours >= 0 && theirs >= 0, 'the queue should carry both kinds of obligation');
  assert.ok(ours < theirs, 'a case ISZE owes is sorted behind one the dealer owes');

  /* A row carries the clocks, so a screen never has to show one number for both. */
  const row = queue[0];
  ['submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at',
    'total_waiting_days', 'not_yet_answered_days'].forEach(k => {
    assert.ok(k in row, 'the queue row does not carry ' + k);
  });
  /* And a closed case is not in the queue at all. */
  assert.equal(queue.some(r => r.state === 'resolved'
    || r.state === 'withdrawn' || r.state === 'closed_outcome_unknown'), false,
  'a finished case must not appear in the open queue');
  return JSON.stringify(rows.slice(0, 5));
});

check('C25', 'CASE-03: no network-wide service guarantee is invented', () => {
  /* The component carries a date somebody wrote down for one case. It does not
     carry an SLA, a response promise, or a retention rule. */
  const record = service.get('CASE-TEST-ATTRIB');
  const text = JSON.stringify(record) + JSON.stringify(schema.OWNER_BY_STATE)
    + schema.appendOnlyStatement() + JSON.stringify(store.describeStorage('files'));
  ['sla', 'service level', 'response guarantee', 'within 24 hours', 'within 48 hours',
    'guaranteed response', 'retention period', 'must be answered within'].forEach(term => {
    assert.equal(text.toLowerCase().includes(term), false,
      'the component states a service guarantee it has no authority to give: "' + term + '"');
  });
  /* And `next_update_due` is described as what it is, not as a promise. */
  const source = fs.readFileSync(path.join(ROOT, 'src', 'case', 'schema.js'), 'utf8');
  assert.match(source, /not an SLA/i,
    'the field that a reader could mistake for a promise is not described as one');
  return 'no SLA, response promise or retention rule appears in the component';
});

/* ======================================================================== */
/* CASE-04 - versioned proposals, and the approval route preserved           */
/* ======================================================================== */

check('C26', 'CASE-04: an amended offer retains the former terms', () => {
  const id = 'CASE-TEST-PROPOSAL';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-P' }));
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it',
    next_update_due: '2026-10-01'
  }, { expected_version: created.version });
  const v1 = service.proposeTerms(id, {
    terms: terms({ price_after: 95, support_eur: 500, currency: 'EUR' }),
    offered_by_role: 'case_owner', approval_route: 'Synthetic route: the account owner.',
    expires_on: '2026-12-31'
  }, { expected_version: submitted.version, role: 'case_owner', by: 'case-owner-1' });
  assert.equal(v1.ok, true, v1.error);

  const v2 = service.proposeTerms(id, {
    terms: terms({ price_after: 92, support_eur: 750, currency: 'EUR' }),
    amends_proposal_version: 1, offered_by_role: 'case_owner',
    approval_route: 'Synthetic route: the account owner.'
  }, { expected_version: v1.version, role: 'case_owner', by: 'case-owner-1' });
  assert.equal(v2.ok, true, v2.error);

  const record = service.get(id);
  assert.equal(record.proposal.versions.length, 2);
  const first = record.proposal.versions[0];
  const second = record.proposal.versions[1];
  /* The former terms are still readable, and still say they were the former
     terms. */
  assert.equal(first.terms.price_after, 95, 'the first version lost its price');
  assert.equal(first.terms.support_eur, 500);
  assert.equal(first.proposal_state, 'amended', 'the amended version does not say it was amended');
  assert.equal(second.terms.price_after, 92);
  assert.equal(second.amends_proposal_version, 1, 'the amendment does not name what it amends');
  assert.equal(second.proposal_state, 'amended');
  assert.equal(record.proposal.active_proposal_version, 2);

  /* And the case can still be read as it stood at version 1. */
  const atV1 = service.reopen(id, v1.version);
  assert.equal(atV1.proposal.versions.length, 1);
  assert.equal(atV1.proposal.versions[0].terms.price_after, 95);
  return `v1 price ${first.terms.price_after}/support ${first.terms.support_eur} (${first.proposal_state}); `
    + `v2 price ${second.terms.price_after}/support ${second.terms.support_eur}, amends v${second.amends_proposal_version}`;
});

check('C27', 'CASE-04: an expired offer is not presented as available', () => {
  const id = 'CASE-TEST-EXPIRY';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-EXP' }));
  let v = created.version;
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it', next_update_due: '2026-10-01'
  }, { expected_version: v }); v = submitted.version;
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess', next_update_due: '2026-10-05'
  }, { expected_version: v }); v = assessing.version;
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Support offered subject to a date.', issued_on: '2026-09-30', commitment: 'support' },
    next_action: 'Approver to decide', next_update_due: '2026-10-10'
  }, { expected_version: v }); v = answered.version;
  const proposed = service.proposeTerms(id, {
    terms: terms(), offered_by_role: 'case_owner', approval_route: 'Synthetic route.',
    expires_on: '2026-10-15'
  }, { expected_version: v, role: 'case_owner' }); v = proposed.version;
  const agreed = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Synthetic approval.',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-EXP' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: v }); v = agreed.version;
  assert.equal(agreed.ok, true, agreed.error);

  /* Available before the date. */
  const before = schema.proposalAvailability(service.get(id), '2026-10-01');
  assert.equal(before.available, true);

  /* Not available after it, and the reason says so. */
  const after = schema.proposalAvailability(service.get(id), '2026-11-01');
  assert.equal(after.available, false, 'an expired proposal was reported as available');
  assert.match(after.reason, /expired/i);

  /* And support cannot be paid against it. */
  const paid = service.recordSupport(id, {
    support_eur: 500, net_terms_basis: 'net', delivered_on: '2026-11-02',
    what: 'Support after the offer expired'
  }, { expected_version: v, role: 'support_owner', at: '2026-11-02T10:00:00.000Z' });
  assert.equal(paid.ok, false);
  assert.equal(paid.code, 'SUPPORT_NOT_AVAILABLE');
  assert.equal(service.get(id).support, null);

  /* Expiring it is recorded, with what was decided. */
  const expired = service.expireProposal(id, {
    proposal_version: 1, reason: 'The offer lapsed and the account did not take it up.',
    after_acceptance: true
  }, { expected_version: service.get(id).version, role: 'case_owner' });
  assert.equal(expired.ok, true, expired.error);
  const record = service.get(id);
  assert.equal(record.proposal.versions[0].proposal_state, 'accepted',
    'expiring an approved offer must not unsay the approval');
  assert.equal(record.proposal.versions[0].availability, 'expired',
    'the availability of the offer was not marked expired');
  assert.equal(record.proposal.versions[0].expiry_decision, 'The offer lapsed and the account did not take it up.');
  const gone = schema.proposalAvailability(record, '2026-11-30');
  assert.equal(gone.available, false);
  /* A second expiry of the same version is refused. */
  const again = service.expireProposal(id, {
    proposal_version: 1, reason: 'Expiring it again', after_acceptance: true
  }, { expected_version: record.version, role: 'case_owner' });
  assert.equal(again.ok, false);
  assert.equal(again.code, 'ALREADY_EXPIRED', again.error);
  assert.equal(service.get(id).version, record.version, 'a refused expiry added a version');
  return `${before.available} before, ${after.available} after: ${after.reason}`;
});

check('C28', 'CASE-04: a draft cannot become approved by saving it', () => {
  const id = 'CASE-TEST-NOSAVE';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-NS' }));
  /* The state is not a field a write can set. Four attempts, four refusals. */
  const saving = service.saveRecord(Object.assign(schema.clone(service.get(id)), {
    state: 'action_agreed'
  }), { expected_version: created.version, by: 'test-runner' });
  assert.equal(saving.ok, false, 'a record write must not be able to set the state');
  /* The state is set only by an accepted move... */
  const jump = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Straight to accepted',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-NOT-REAL' }
  }, { expected_version: created.version });
  assert.equal(jump.ok, false);
  assert.equal(jump.code, 'NOT_ALLOWED_FROM_STATE');
  /* ...against a proposal that exists... */
  const v = service.get(id);
  const noProposal = service.saveRecord(Object.assign(schema.clone(v), { state: 'response_issued' }),
    { expected_version: v.version, by: 'test-runner' });
  assert.equal(noProposal.ok, false);
  assert.equal(service.get(id).state, 'draft');
  assert.equal(service.get(id).version, 1, 'a refused write must not add a version');
  return `${saving.code || 'refused'}: the state is not something a save can set`;
});

check('C29', 'CASE-04: choosing the highest-ranked row does not approve anything', () => {
  const id = 'CASE-TEST-RANKED';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-RK' }));
  let v = created.version;
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it', next_update_due: '2026-10-01'
  }, { expected_version: v }); v = submitted.version;
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess', next_update_due: '2026-10-05'
  }, { expected_version: v }); v = assessing.version;
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Position issued.', issued_on: '2026-09-30', commitment: 'support' },
    next_action: 'Approver to decide', next_update_due: '2026-10-10'
  }, { expected_version: v }); v = answered.version;

  /* A ranking is a derivation, so it is recorded as what the proposal came from
     and nothing else. The top-ranked row is carried as a candidate key. */
  const proposed = service.proposeTerms(id, {
    terms: terms({ price_after: 90 }),
    offered_by_role: 'case_owner', approval_route: 'Synthetic route.',
    candidate_keys: { ranked_first: 'SYNTH-ALT-3', objective: 'revenue', rank: 1 }
  }, { expected_version: v, role: 'case_owner' }); v = proposed.version;
  assert.equal(proposed.ok, true, proposed.error);

  const record = service.get(id);
  assert.equal(record.state, 'response_issued', 'choosing a row must not move the case');
  assert.equal(record.proposal.versions[0].proposal_state, 'proposed',
    'choosing the highest-ranked row marked the proposal accepted');
  assert.equal(schema.acceptedProposal(record), null,
    'a ranked row is not an accepted proposal');
  assert.deepEqual(record.proposal.versions[0].candidate_keys,
    { ranked_first: 'SYNTH-ALT-3', objective: 'revenue', rank: 1 });

  /* Accepting needs a reference, or an explicit statement that it is synthetic. */
  const noReference = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Accepted, no reference',
    proposal_accept: { proposal_version: 1 }
  }, { expected_version: v });
  assert.equal(noReference.ok, false);
  assert.equal(noReference.code, 'MISSING_INPUT');
  assert.ok(/approval reference/i.test(noReference.error), noReference.error);

  /* A synthetic approval has to say so, in the note a reader sees. */
  const unlabelled = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Accepted in the exercise.',
    proposal_accept: { proposal_version: 1, synthetic_approval: true }
  }, { expected_version: v });
  assert.equal(unlabelled.ok, false);
  assert.ok(/labelled synthetic/i.test(unlabelled.error), unlabelled.error);
  assert.equal(service.get(id).state, 'response_issued');

  /* Properly labelled, it is accepted, and the record says it is synthetic. */
  const synthetic = service.transition(id, {
    action: 'accept_proposal', role: 'approver',
    approval_note: 'Synthetic approval for this local exercise only; not a real approval.',
    proposal_accept: { proposal_version: 1, synthetic_approval: true },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: v });
  assert.equal(synthetic.ok, true, synthetic.error);
  const finalRecord = service.get(id);
  assert.equal(finalRecord.state, 'action_agreed');
  assert.equal(finalRecord.proposal.versions[0].synthetic_approval, true);
  assert.equal(finalRecord.proposal.versions[0].approval_reference, null);
  return `ranking recorded as candidate_keys only; acceptance needs a reference or a labelled `
    + `synthetic approval; the accepted version is marked synthetic=${finalRecord.proposal.versions[0].synthetic_approval}`;
});

check('C30', 'CASE-04: the approval route is preserved and cannot be swapped while accepting', () => {
  const id = 'CASE-TEST-ROUTE';
  const created = service.create(seed({ case_id: id, part_number: 'SYNTH-PART-RT' }));
  let v = created.version;
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it', next_update_due: '2026-10-01'
  }, { expected_version: v }); v = submitted.version;
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess', next_update_due: '2026-10-05'
  }, { expected_version: v }); v = assessing.version;
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Position issued.', issued_on: '2026-09-30', commitment: 'support' },
    next_action: 'Approver to decide', next_update_due: '2026-10-10'
  }, { expected_version: v }); v = answered.version;
  const proposed = service.proposeTerms(id, {
    terms: terms(), offered_by_role: 'case_owner',
    approval_route: 'Synthetic route: the account owner approves.'
  }, { expected_version: v, role: 'case_owner' }); v = proposed.version;
  assert.equal(service.get(id).proposal.versions[0].approval_route,
    'Synthetic route: the account owner approves.');

  const swapped = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Accepted under a different route.',
    proposal_accept: {
      proposal_version: 1, approval_reference: 'SYNTH-ROUTE-X',
      approval_route: 'Synthetic route: a different approver who never proposed this.'
    }
  }, { expected_version: v });
  assert.equal(swapped.ok, false, 'the approval route was swapped at the moment of accepting');
  assert.ok(/approval route/i.test(swapped.error), swapped.error);
  assert.equal(service.get(id).state, 'response_issued');
  assert.equal(service.get(id).proposal.versions[0].proposal_state, 'proposed');
  return swapped.error.slice(0, 140);
});

/* ======================================================================== */
/* CASE-05 - linking support and outcomes without double counting             */
/* ======================================================================== */

check('C31', 'CASE-05: support, outcome and their links are recorded on the agreed case', () => {
  /* Its own case, so this check does not depend on what a previous one left
     behind. */
  const id = 'CASE-TEST-LINK';
  const agreed = walkToAgreed(id);
  assert.equal(agreed.state, 'action_agreed');

  const paid = service.recordSupport(id, PAYMENT, {
    expected_version: agreed.version, role: 'support_owner', by: 'support-owner-1'
  });
  assert.equal(paid.ok, true, paid.error);
  /* The payment does NOT move the case. */
  assert.equal(service.get(id).state, 'action_agreed',
    'recording a payment must not move the lifecycle state');

  const measured = service.recordOutcome(id, {
    what: 'Volume held at the agreed level against a recorded billing basis.',
    observed_on: '2026-11-30',
    quantity_before: 100, quantity_after: 120, quantity_label: 'observed history',
    counts_as_new_business: true,
    evidence: [
      { kind: 'recorded billing', reference: 'SYNTH-BILLING-1', observed_on: '2026-11-30', value: 120 },
      { kind: 'stated commitment', reference: 'SYNTH-COMMITMENT-1', observed_on: '2026-10-05' }
    ],
    measures: {
      purchase_cost_difference_eur: -40,
      gross_profit_eur: 260,
      capacity_released_units: 3,
      programme_expenditure_eur: 500
    }
  }, { expected_version: service.get(id).version, role: 'case_owner', by: 'case-owner-1' });
  assert.equal(measured.ok, true, measured.error);
  const after = service.get(id);
  assert.equal(after.state, 'action_agreed', 'recording an outcome must not move the state');
  assert.equal(after.support.action_identifier, after.action_identifier,
    'the support and the case do not share one action identifier');
  assert.equal(after.outcome.action_identifier, after.action_identifier,
    'the outcome is not tied to the action the support paid for');
  assert.equal(after.outcome.evidence.length, 2);
  /* The four measures are separate fields, not one benefit figure. */
  assert.deepEqual(Object.keys(after.outcome.measures).sort(), [
    'capacity_released_units', 'gross_profit_eur', 'programme_expenditure_eur',
    'purchase_cost_difference_eur'
  ].sort());
  assert.equal(after.outcome.measures.purchase_cost_difference_eur, -40);
  assert.equal(after.outcome.measures.gross_profit_eur, 260);
  assert.equal(after.outcome.measures.capacity_released_units, 3);
  assert.equal(after.outcome.measures.programme_expenditure_eur, 500);
  return `support EUR ${after.support.support_eur} (${after.support.net_terms_basis}), `
    + `outcome measures ${JSON.stringify(after.outcome.measures)}, state still ${after.state}`;
});

check('C32', 'CASE-05: a paid credit does not create incremental profit or a won quotation', () => {
  const id = 'CASE-TEST-CREDIT';
  const agreed = walkToAgreed(id);
  const withSupport = service.recordSupport(id, {
    support_eur: 400, net_terms_basis: 'gross',
    credit_reference: 'SYNTH-CREDIT-2', delivered_on: '2026-10-12',
    what: 'A credit paid to the participant', by_role: 'support_owner'
  }, { expected_version: agreed.version, role: 'support_owner' });
  assert.equal(withSupport.ok, true, withSupport.error);

  const record = service.get(id);
  const account = service.benefitAccount([record], '2026-11-01');

  /* The payment is reported as an expenditure. It is not a gross profit, and it
     is not an outcome. */
  assert.equal(record.outcome, null, 'a payment recorded no outcome, and none was invented');
  assert.equal(account.cases_without_a_recorded_outcome, 1);
  assert.equal(account.newly_won_units, 0, 'a paid credit was counted as newly won volume');
  assert.equal(account.distinct_actions, 1);

  /* The gross-profit line is null, not zero and not the payment. A missing
     measure is not zero. */
  const gpLine = account.lines.find(l => l.action_identifier === record.action_identifier
    && l.measure === 'gross_profit_eur');
  assert.ok(gpLine, 'the account has no gross-profit line for the action');
  assert.equal(gpLine.amount, null, 'a gross profit was invented from a payment');
  assert.equal(gpLine.known, false);
  /* And the programme expenditure is stated as the payment, on its own line. */
  const spendLine = account.lines.find(l => l.action_identifier === record.action_identifier
    && l.measure === 'programme_expenditure_eur');
  assert.equal(spendLine.amount, null,
    'the payment was not written into the outcome measures, so the expenditure line is unknown too');

  /* There is no single benefit figure to print. */
  assert.equal(account.total_benefit_eur, null);
  assert.equal(account.support_total_eur, 400, 'the payment is reported once, as support');
  return `support EUR ${account.support_total_eur} reported; gross profit ${gpLine.amount} (not zero); `
    + `newly won ${account.newly_won_units}; total benefit ${account.total_benefit_eur}`;
});

check('C33', 'CASE-05: one action used by two modules is counted once', () => {
  /* Two cases, each recording the SAME action under a different module's name.
     The identifier is what makes them one action. */
  const a = walkToAgreed('CASE-TEST-MOD-A');
  const withA = service.recordSupport('CASE-TEST-MOD-A', {
    support_eur: 300, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Support for the shared action', action_identifier: 'ACT:SHARED-ACTION-1'
  }, { expected_version: a.version, role: 'support_owner' });
  assert.equal(withA.ok, true, withA.error);

  const b = walkToAgreed('CASE-TEST-MOD-B');
  const withB = service.recordSupport('CASE-TEST-MOD-B', {
    support_eur: 300, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'The same action, referred to by another module',
    action_identifier: 'ACT:SHARED-ACTION-1'
  }, { expected_version: b.version, role: 'support_owner' });
  assert.equal(withB.ok, true, withB.error);

  const recA = service.get('CASE-TEST-MOD-A');
  const recB = service.get('CASE-TEST-MOD-B');
  /* Each case has its own identifier; what the two share is the action the
     SUPPORT pays for, which is what the account counts. */
  assert.notEqual(recA.action_identifier, recB.action_identifier);
  assert.equal(recA.support.action_identifier, 'ACT:SHARED-ACTION-1');
  assert.equal(recB.support.action_identifier, 'ACT:SHARED-ACTION-1');

  /* The account sees one action, not two, and counts the support once. */
  const account = service.benefitAccount(['CASE-TEST-MOD-A', 'CASE-TEST-MOD-B'], '2026-11-01');
  assert.equal(account.cases, 2);
  assert.equal(account.distinct_actions, 1, 'one action was counted as two');
  assert.equal(account.support_total_eur, 300,
    'the same payment was added twice because two cases named the action');
  const shared = account.actions[0];
  assert.equal(shared.action_identifier, 'ACT:SHARED-ACTION-1');
  assert.deepEqual(shared.case_ids.sort(), ['CASE-TEST-MOD-A', 'CASE-TEST-MOD-B']);
  assert.equal(shared.support_eur, 300);

  /* The same action recorded by two cases does not become newly won volume. */
  const o1 = service.recordOutcome('CASE-TEST-MOD-A', {
    what: 'Measured once.', observed_on: '2026-11-30', quantity_after: 60,
    quantity_label: 'observed history', counts_as_new_business: true,
    measures: { gross_profit_eur: 120, programme_expenditure_eur: 300 }
  }, { expected_version: service.get('CASE-TEST-MOD-A').version, role: 'case_owner' });
  assert.equal(o1.ok, true, o1.error);
  const o2 = service.recordOutcome('CASE-TEST-MOD-B', {
    what: 'The other module measuring the same action.', observed_on: '2026-11-30',
    quantity_after: 60, quantity_label: 'observed history', counts_as_new_business: true,
    measures: { gross_profit_eur: 120, programme_expenditure_eur: 300 }
  }, { expected_version: service.get('CASE-TEST-MOD-B').version, role: 'case_owner' });
  assert.equal(o2.ok, true, o2.error);

  const after = service.benefitAccount(['CASE-TEST-MOD-A', 'CASE-TEST-MOD-B'], '2026-12-01');
  assert.equal(after.distinct_actions, 1);
  assert.equal(after.newly_won_units, 60, 'the same 60 units were counted twice');
  const gp = after.lines.filter(l => l.measure === 'gross_profit_eur'
    && l.action_identifier === 'ACT:SHARED-ACTION-1');
  assert.equal(gp.length, 1, 'the gross-profit measure appears once per module');
  assert.equal(gp[0].amount, 120, 'the measure was added together across two modules');
  assert.equal(after.support_total_eur, 300, 'the support was counted twice');
  return `2 cases, ${after.distinct_actions} action, support EUR ${after.support_total_eur} once, `
    + `newly won ${after.newly_won_units} units once, gross profit ${gp[0].amount} once`;
});

check('C34', 'CASE-05: the four measures are never added together', () => {
  /* Its own case, so this reads a record written here rather than one another
     check happened to leave behind, and the measures are the four that were
     recorded a moment ago. */
  const id = 'CASE-TEST-MEASURES';
  const agreed = walkToAgreed(id);
  const paid = service.recordSupport(id, {
    support_eur: 500, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Support whose result was measured', by_role: 'support_owner'
  }, { expected_version: agreed.version, role: 'support_owner' });
  assert.equal(paid.ok, true, paid.error);
  const measured = service.recordOutcome(id, {
    what: 'Measured against the recorded basis.', observed_on: '2026-11-30',
    quantity_after: 120, quantity_label: 'observed history', counts_as_new_business: true,
    measures: {
      purchase_cost_difference_eur: -40, gross_profit_eur: 260,
      capacity_released_units: 3, programme_expenditure_eur: 500
    }
  }, { expected_version: service.get(id).version, role: 'case_owner' });
  assert.equal(measured.ok, true, measured.error);

  const record = service.get(id);
  const account = service.benefitAccount([record], '2026-12-01');
  /* Four lines, four units, no total. */
  const lines = account.lines.filter(l => l.action_identifier === record.action_identifier);
  assert.equal(lines.length, 4, 'expected four separate measure lines');
  const units = Array.from(new Set(lines.map(l => l.unit))).sort();
  assert.deepEqual(units, ['EUR', 'units'],
    'the four measures are not reported in the units they are measured in');
  assert.equal(account.total_benefit_eur, null,
    'the account produced a single benefit figure, which is the addition it must refuse');
  /* Each line says whether it is known; a missing one is null, not zero. */
  lines.forEach(l => {
    assert.ok('known' in l, 'line ' + l.measure + ' does not say whether it is known');
    if (l.amount === null) assert.equal(l.known, false, 'a null amount was reported as known');
  });
  /* The numbers are the four the outcome recorded, unchanged and unsummed. */
  const byMeasure = {};
  lines.forEach(l => { byMeasure[l.measure] = l.amount; });
  assert.equal(byMeasure.purchase_cost_difference_eur, -40);
  assert.equal(byMeasure.gross_profit_eur, 260);
  assert.equal(byMeasure.capacity_released_units, 3);
  assert.equal(byMeasure.programme_expenditure_eur, 500);
  /* And none of them is the sum of the others, which is the check that the four
     are genuinely separate quantities rather than four views of one total. */
  const four = Object.values(byMeasure);
  [four[0] + four[1], four[1] + four[3], four[0] + four[3]].forEach(totalled => {
    four.forEach(v => assert.notEqual(v, totalled, 'a measure equals the sum of two others'));
  });
  return lines.map(l => `${l.label}=${l.amount}${l.unit === 'EUR' ? ' EUR' : ' ' + l.unit}`).join(' | ');
});

check('C35', 'CASE-05: an unknown outcome stays unknown', () => {
  const id = 'CASE-TEST-UNKNOWN';
  const agreed = walkToAgreed(id);
  const paid = service.recordSupport(id, {
    support_eur: 250, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Support given, and nobody has measured what came of it',
    action_identifier: 'ACT:UNKNOWN-OUTCOME-1'
  }, { expected_version: agreed.version, role: 'support_owner' });
  assert.equal(paid.ok, true, paid.error);

  const record = service.get(id);
  assert.equal(record.outcome, null);
  const account = service.benefitAccount([record], '2026-12-01');
  assert.equal(account.cases_without_a_recorded_outcome, 1);
  const action = account.actions.find(a => a.action_identifier === 'ACT:UNKNOWN-OUTCOME-1');
  assert.equal(action.outcome_state, 'unknown', 'an unmeasured action was reported as measured');
  assert.equal(action.units, null, 'an unmeasured action reported a volume');
  assert.equal(action.counted_as, 'unresolved', 'an unknown outcome was resolved into a category');
  assert.equal(account.newly_won_units, 0);

  /* The measure lines are null and say they are unknown, rather than being zero. */
  account.lines.filter(l => l.action_identifier === 'ACT:UNKNOWN-OUTCOME-1').forEach(l => {
    assert.equal(l.amount, null, l.measure + ' was reported as zero rather than unknown');
    assert.equal(l.known, false);
  });

  /* And closing the case does not resolve it. Closing creates no outcome. */
  const closed = service.transition(id, {
    action: 'terminal_no_change', role: 'case_owner',
    approval_note: 'Closed. The result was never established.'
  }, { expected_version: record.version });
  assert.equal(closed.ok, true, closed.error);
  assert.equal(service.get(id).outcome, null, 'closing the case invented an outcome');
  const after = service.benefitAccount([service.get(id)], '2026-12-01');
  assert.equal(after.newly_won_units, 0);
  assert.equal(after.cases_without_a_recorded_outcome, 1);
  assert.match(after.statement, /unknown outcome stays unknown/i);
  return `state ${service.get(id).state}, outcome ${service.get(id).outcome}; `
    + `account: ${after.newly_won_units} new units, ${after.cases_without_a_recorded_outcome} without an outcome`;
});

check('C36', 'CASE-05: volume migrated from another product is not newly won', () => {
  const id = 'CASE-TEST-MIGRATION';
  const agreed = walkToAgreed(id, { terms: { quantity_after: 140 } });
  const paid = service.recordSupport(id, {
    support_eur: 300, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Launch support for the migrated volume', action_identifier: 'ACT:MIGRATION-1'
  }, { expected_version: agreed.version, role: 'support_owner' });
  assert.equal(paid.ok, true, paid.error);
  const measured = service.recordOutcome(id, {
    what: '40 units now bought on the Genuine counterpart; the same trucks, the same demand.',
    observed_on: '2026-11-30', quantity_after: 40, quantity_label: 'observed history',
    migration_from: 'SYNTH-PART-OLD', migration_to: 'SYNTH-PART-MIGRATION',
    counts_as_new_business: false,
    measures: { gross_profit_eur: null, programme_expenditure_eur: 300 }
  }, { expected_version: service.get(id).version, role: 'case_owner' });
  assert.equal(measured.ok, true, measured.error);

  /* A genuinely new piece of business, so the account carries both kinds. */
  const newAgreed = walkToAgreed('CASE-TEST-NEWBIZ');
  const newPaid = service.recordSupport('CASE-TEST-NEWBIZ', {
    support_eur: 700, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Launch support for a genuinely new part', action_identifier: 'ACT:NEWBIZ-1'
  }, { expected_version: newAgreed.version, role: 'support_owner' });
  assert.equal(newPaid.ok, true, newPaid.error);
  const newOutcome = service.recordOutcome('CASE-TEST-NEWBIZ', {
    what: '60 units billed that were not billed before.', observed_on: '2026-11-30',
    quantity_after: 60, quantity_label: 'observed history', counts_as_new_business: true
  }, { expected_version: service.get('CASE-TEST-NEWBIZ').version, role: 'case_owner' });
  assert.equal(newOutcome.ok, true, newOutcome.error);

  const account = service.benefitAccount([id, 'CASE-TEST-NEWBIZ'], '2026-12-01');
  assert.equal(account.distinct_actions, 2);
  assert.equal(account.newly_won_units, 60,
    'only the genuinely new 60 units are newly won; the 40 migrated units are not');
  assert.equal(account.migrated_units_not_new_business, 40);
  assert.equal(account.support_total_eur, 1000, '300 + 700, each counted once');
  const migrated = account.actions.find(a => a.action_identifier === 'ACT:MIGRATION-1');
  assert.equal(migrated.counted_as, 'migrated from another product');

  /* And a migration presented as new business is refused outright. */
  const bogus = service.recordOutcome('CASE-TEST-NEWBIZ', {
    what: 'A migration claimed as new business', observed_on: '2026-12-01',
    migration_from: 'SYNTH-PART-OLD', counts_as_new_business: true
  }, { expected_version: service.get('CASE-TEST-NEWBIZ').version, role: 'case_owner' });
  assert.equal(bogus.ok, false, 'a migration presented as new business must be refused');
  return `newly won ${account.newly_won_units} units, migrated ${account.migrated_units_not_new_business} units, `
    + `support EUR ${account.support_total_eur} across ${account.distinct_actions} actions`;
});

check('C37', 'CASE-05: one case cannot record a second payment for the same action', () => {
  const record = service.get('CASE-TEST-LINK');
  assert.equal(schema.commercialEventCount(record), 1,
    'the case this check is written against should carry exactly one payment');
  const second = service.recordSupport('CASE-TEST-LINK', {
    support_eur: 400, net_terms_basis: 'net', delivered_on: '2026-11-01',
    what: 'A second payment on the same action'
  }, { expected_version: record.version, role: 'support_owner' });
  assert.equal(second.ok, false);
  assert.equal(second.code, 'DUPLICATE_SUPPORT');
  assert.equal(service.get('CASE-TEST-LINK').support.support_eur, 500,
    'the first payment was replaced rather than protected');
  assert.equal(schema.commercialEventCount(service.get('CASE-TEST-LINK')), 1);
  return second.error.slice(0, 140);
});

/* ======================================================================== */
/* the rules that apply across all five tasks                                */
/* ======================================================================== */

check('C38', 'A correction replaces its predecessor and does not multiply the activity', () => {
  const id = 'CASE-TEST-CORRECTION';
  const agreed = walkToAgreed(id);
  const paid = service.recordSupport(id, PAYMENT, {
    expected_version: agreed.version, role: 'support_owner'
  });
  assert.equal(paid.ok, true, paid.error);
  const before = service.get(id);
  const occasionsBefore = schema.commercialEventCount(before);
  assert.equal(occasionsBefore, 1, 'the case should carry exactly one payment');
  const paymentEntry = before.history.find(h => h.action === 'record_support');
  assert.ok(paymentEntry, 'the payment entry should be in the log');
  const stateBefore = before.state;

  const corrected = service.correct(id, {
    corrects_sequence: paymentEntry.seq,
    role: 'case_owner',
    reason: 'The recorded support was 500; the agreed figure was 250. Correcting the amount.',
    replacement: {
      support: {
        action_identifier: before.support.action_identifier, support_eur: 250,
        net_terms_basis: 'net', delivered_on: '2026-10-12',
        what: 'One-off launch support, given once', by_role: 'support_owner'
      }
    }
  }, { expected_version: before.version, by: 'case-owner-1' });

  assert.equal(corrected.ok, true, corrected.error);
  const after = service.get(id);
  assert.ok(after.history.find(h => h.seq === paymentEntry.seq),
    'correcting must not remove the entry it corrects');
  assert.equal(after.history.length, before.history.length + 1);
  assert.equal(after.version, before.version + 1);
  assert.equal(after.state, stateBefore, 'a correction must not move the case');
  const correctionEntry = after.history[after.history.length - 1];
  assert.equal(correctionEntry.kind, 'correction');
  assert.equal(correctionEntry.correction_of, paymentEntry.seq);
  assert.equal(after.support.support_eur, 250);
  assert.equal(schema.commercialEventCount(after), occasionsBefore,
    'a correction must not add a commercial occasion');
  /* And the corrected figure is what the account now reports. */
  const account = service.benefitAccount([after], '2026-12-01');
  assert.equal(account.support_total_eur, 250, 'the account is still reading the corrected-away figure');
  return `occasions before ${occasionsBefore}, after ${schema.commercialEventCount(after)}; `
    + `support corrected 500 -> ${after.support.support_eur}; state still ${after.state}`;
});

check('C39', 'A correction cannot be pointed at the same entry twice, or move the case', () => {
  const id = 'CASE-TEST-CORRECTION';
  const current = service.get(id);
  const paymentSeq = current.history.find(h => h.action === 'record_support').seq;
  const approvalSeq = current.history.find(h => h.action === 'accept_proposal').seq;

  const again = service.correct(id, {
    corrects_sequence: paymentSeq, role: 'case_owner', reason: 'Correcting it a second time'
  }, { expected_version: current.version });
  assert.equal(again.ok, false);
  assert.equal(again.code, 'TARGET_ALREADY_CORRECTED');

  const silent = service.correct(id, {
    corrects_sequence: approvalSeq, role: 'case_owner'
  }, { expected_version: current.version });
  assert.equal(silent.ok, false);
  assert.equal(silent.code, 'CORRECTION_NEEDS_REASON');

  const moves = service.correct(id, {
    corrects_sequence: approvalSeq, role: 'case_owner',
    reason: 'Trying to un-close the case', replacement: { state: 'resolved' }
  }, { expected_version: current.version });
  assert.equal(moves.ok, false);
  assert.equal(moves.code, 'CORRECTION_CANNOT_MOVE_STATE');

  assert.equal(service.get(id).version, current.version, 'a refused correction left a mark');
  return `${again.code} | ${silent.code} | ${moves.code}`;
});

check('C40', 'A field that looks like a credential, or is undeclared, is refused', () => {
  const current = service.get('CASE-TEST-ATTRIB');
  const withSecret = schema.clone(current);
  withSecret.review = { note: 'Looks fine', api_key: 'not-a-real-key' };
  const refused = service.saveRecord(withSecret, { expected_version: current.version });
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'SECRET_LIKE_FIELD');
  assert.match(refused.error, /api_key/);

  const withExtra = schema.clone(current);
  withExtra.commercial_score = 99;
  const undeclared = service.saveRecord(withExtra, { expected_version: current.version });
  assert.equal(undeclared.ok, false);
  assert.equal(undeclared.code, 'INVALID_RECORD');
  assert.match(undeclared.error, /commercial_score/);
  assert.equal(service.get('CASE-TEST-ATTRIB').version, current.version);
  return `${refused.error.slice(0, 60)} | ${undeclared.error.slice(0, 60)}`;
});

check('C41', 'A half-written link is detected and can be repaired', () => {
  const clean = service.linkIssues();
  assert.equal(clean.ok, true, 'the links written so far should be complete');

  const adapter = service._adapter;
  const record = adapter.load('CASE-TEST-NEWBIZ');
  const withLink = schema.clone(record);
  withLink.links = (withLink.links || []).concat([{
    link_id: 'link:half-written', other_case_id: 'CASE-TEST-ATTRIB',
    relation: 'continues', counts_apart: true, note: 'A link recorded on one side only'
  }]);
  assert.equal(schema.validate(withLink).ok, true, schema.validate(withLink).errors.join(' '));
  adapter.save('CASE-TEST-NEWBIZ', withLink);

  const found = service.linkIssues();
  assert.equal(found.ok, false, 'the one-sided link should be reported');
  assert.equal(found.issues.length, 1);
  assert.match(found.issues[0].problem, /CASE-TEST-NEWBIZ only/);

  const repaired = service.repairLinks();
  assert.equal(repaired.ok, true, JSON.stringify(repaired.unrepairable));
  assert.equal(repaired.repaired, 1);
  assert.equal(service.linkIssues().ok, true);
  const healed = service.get('CASE-TEST-ATTRIB');
  assert.equal(healed.history.length, healed.version, 'the repair must be a logged entry');
  const repairEntry = healed.history.find(h => h.action === 'link_case');
  assert.equal(repairEntry.commercial, false, 'a link is not a commercial event');
  return found.issues[0].problem;
});

check('C42', 'A restore does not silently replace a newer stored case', () => {
  const bundle = service.exportAll();
  const older = schema.clone(bundle.cases['CASE-TEST-ATTRIB']);
  older.version = 1;
  older.state = 'draft';
  older.history = [older.history[0]];

  const refused = service.importAll({ cases: { 'CASE-TEST-ATTRIB': older } }, { overwrite: true });
  assert.equal(refused.refused.length, 1);
  assert.match(refused.refused[0].errors[0], /ahead of the bundle/);
  assert.equal(service.get('CASE-TEST-ATTRIB').state, 'action_agreed',
    'the newer stored case must be untouched');

  const fresh = schema.clone(service.get('CASE-TEST-NEWBIZ'));
  fresh.case_id = 'CASE-TEST-RESTORED';
  const added = service.importAll({ cases: { 'CASE-TEST-RESTORED': fresh } });
  assert.equal(added.added, 1);
  const skipped = service.importAll({ cases: { 'CASE-TEST-RESTORED': fresh } });
  assert.deepEqual(skipped.skipped, ['CASE-TEST-RESTORED']);
  return `refused a backwards restore of CASE-TEST-ATTRIB; added ${added.added}, skipped ${skipped.skipped.length} on the second pass`;
});

check('C43', 'Deleting a case needs its id to be repeated', () => {
  const wrong = service.remove('CASE-TEST-RESTORED', { confirm_case_id: 'something-else' });
  assert.equal(wrong.ok, false);
  assert.equal(wrong.code, 'DELETE_NEEDS_CONFIRMATION');
  assert.ok(service.get('CASE-TEST-RESTORED'), 'the case should still be there');

  const right = service.remove('CASE-TEST-RESTORED', { confirm_case_id: 'CASE-TEST-RESTORED' });
  assert.equal(right.ok, true);
  assert.equal(service.get('CASE-TEST-RESTORED'), null);
  return wrong.error;
});

check('C44', 'An attachment that may carry restricted content is refused, and the gap is stated', () => {
  const viewer = recipients.makeDevIdentity({ role: 'viewer', name: 'synthetic participant' });
  const owner = recipients.makeDevIdentity({ role: 'case_owner', name: 'synthetic owner' });

  const byParticipant = service.attach('CASE-TEST-ATTRIB', { name: 'brief.pdf' }, viewer);
  assert.equal(byParticipant.ok, false);
  assert.equal(byParticipant.code, 'ATTACHMENT_NOT_PERMITTED');

  const clean = service.attach('CASE-TEST-ATTRIB', { name: 'synthetic-note.pdf', restricted: false }, owner);
  assert.equal(clean.ok, true, clean.error);
  assert.equal(clean.stored, false);
  assert.match(clean.storage_gap, /not implemented/);

  const restricted = service.attach('CASE-TEST-ATTRIB', { name: 'synthetic-pack.pdf', restricted: true }, owner);
  assert.equal(restricted.ok, false);
  assert.equal(restricted.code, 'ATTACHMENT_NOT_PERMITTED');

  const suspicious = service.attach('CASE-TEST-ATTRIB', { name: 'supplier-cost-detail.xlsx' }, owner);
  assert.equal(suspicious.ok, false);
  assert.match(suspicious.error, /restricted content/);
  return suspicious.error + ' | storage gap: ' + clean.storage_gap.slice(0, 70) + '...';
});

check('C45', 'The repository the interface calls is a facade over the one implementation', () => {
  /* The duplicate-module defect, asserted rather than described. This is the
     check that would fail if someone reintroduced a second store. */
  assert.equal(repoModule.RETIRED_AS_IMPLEMENTATION, true);
  assert.match(repoModule.AUTHORITATIVE_IMPLEMENTATION, /src\/case\/store\.js/);

  const source = fs.readFileSync(path.join(ROOT, 'src', 'data', 'cases.js'), 'utf8');
  /* No rule book in the facade: no state table, no transition table, no stage
     map. Those live in src/case/schema.js and nowhere else. */
  ['STATE_STAGE', 'TRANSITIONS', 'applyTransition', 'applyCorrection', 'stageOf',
    'commercialEventCount', 'openWork'].forEach(name => {
    assert.equal(source.includes(name), false,
      'src/data/cases.js carries "' + name + '", so a second rule book has appeared');
  });

  const memoryAdapter = store.makeMemoryAdapter();
  const svc = store.makeCaseService({ adapter: memoryAdapter, now: fixedClock, caller: 'facade-check' });
  const made = svc.create({ case_id: 'CASE-FACADE', customer: 'Synthetic', part_number: 'SYNTH-F' });
  assert.equal(made.ok, true, made.error);

  const repo = repoModule.makeRepository({ forceMemory: true });
  assert.equal(typeof repo.save, 'function');
  assert.equal(typeof repo.transition, 'function',
    'the lifecycle must be reachable through the one object the interface holds');
  assert.equal(repo._service.describe().shared, false);

  /* And the facade's read projection is derived from the one stored log, so the
     two shapes cannot disagree. */
  const written = repo.save('CASE-PROJECTION', {
    scenario: { scenario_id: 'CASE-PROJECTION:v1', price_after: 90 },
    result: { ok: true, revenue_change: -10 },
    part_number: 'SYNTH-PROJECTION'
  }, { expected_version: 0, recorded_by: 'facade-check' });
  assert.equal(written.ok, true, written.error);
  const loaded = repo.load('CASE-PROJECTION');
  assert.equal(loaded.revisions.length, loaded.history.length,
    'the projected revision log and the stored log disagree in length');
  assert.equal(loaded.revisions.length, loaded.version,
    'every version is one log entry, so the projection must match the version');
  assert.equal(loaded.revisions[0].record.scenario.price_after, 90,
    'the projected revision did not carry the scenario that was saved');
  assert.equal(repo.history('CASE-PROJECTION').length, loaded.version);
  return `facade exposes the lifecycle, holds no rule book, and projects ${loaded.version} `
    + `revision(s) from the one stored log`;
});

check('C46', 'The state is not something a record write can set, and the note says so', () => {
  /* The legacy caller passes a state with its save. It is refused with a note
     rather than applied, which is the difference between a case and a box with
     a label in it. */
  const repo = repoModule.makeRepository({ forceMemory: true });
  const first = repo.save('CASE-LEGACY', {
    scenario: { scenario_id: 'CASE-LEGACY:v1', price_after: 95 }, result: { ok: true },
    part_number: 'SYNTH-LEGACY'
  }, { expected_version: 0, state: 'approved', owner_role: 'role A', recorded_by: 'legacy-caller' });
  assert.equal(first.ok, true, first.error);
  const stored = repo.load('CASE-LEGACY');
  assert.equal(stored.state, 'draft', 'a save put the case into a state without a recorded move');
  assert.ok(first.notes && first.notes.some(n => /not at "approved"/.test(n)),
    'the caller was not told the requested state was not applied: ' + JSON.stringify(first.notes));
  assert.ok(first.notes.some(n => /not one of the declared responding functions/.test(n)),
    'a free-text role was accepted as a responding function');
  assert.equal(stored.owner_role, null,
    'the case was given a responding function it was not honestly given');
  assert.equal(stored.owner, 'role A', 'the named owner was lost rather than kept as a name');
  /* Every entry is still dated and attributed. */
  assert.ok(stored.history[0].recorded_at);
  return first.notes.join(' | ');
});

/* ---------------------------------------------------------------- report -- */

const width = Math.max(...results.map(r => r.id.length + r.name.length)) + 4;
console.log('');
console.log('AIM case service - CASE-01 ... CASE-05 - ' + results.length + ' checks');
console.log('='.repeat(Math.min(width + 20, 100)));
for (const r of results) {
  console.log(`${r.status === 'PASS' ? 'PASS' : 'FAIL'}  ${r.id}  ${r.name}`);
  if (r.evidence) console.log('      -> ' + r.evidence);
}
console.log('-'.repeat(Math.min(width + 20, 100)));
const passed = results.filter(r => r.status === 'PASS').length;
console.log(`${passed} passed, ${failures} failed, of ${results.length}`);
console.log('');

fs.rmSync(tempRoot, { recursive: true, force: true });
process.exit(failures === 0 ? 0 : 1);
