#!/usr/bin/env node
/* ===========================================================================
   Durable case record - runnable checks (CASE-01 ... CASE-08, F12).

   Run:
     node tests/case_store.test.mjs

   Exit code is 0 only when every check passes. Nothing is skipped and no
   assertion is relaxed to obtain a green run.

   What is checked
   ---------------
     1  a case can be created and read back, with a named owner
     2  the version increments on every accepted write
     3  a lost race is refused rather than silently overwriting (CASE-07)
     4  the same content submitted twice is refused (CASE-07)
     5  a proposal is not an approval, an approval is not a delivery, and a
        delivery is not an outcome (CASE-02)
     6  the wrong role cannot make a move
     7  a record that is waiting says who owes it and when (CASE-03)
     8  a correction replaces its predecessor and does not multiply the
        activity (CASE-06)
     9  one delivery plus a correction of it is one commercial occasion
    10  volume migrated from another Isuzu product is not newly won business
        (CASE-05)
    11  a one-sided link is detected and can be repaired
    12  a case written to a folder is read back by a new service - a real
        restart, not the same object in memory (RUN-01 / RUN-07)
    13  a field that looks like a credential is refused
    14  a restore does not silently replace a newer stored case
    15  deleting a case needs its id to be repeated
    16  an attachment that may be restricted is refused, and the storage gap is
        stated rather than hidden (SAFE-06)
    17  every state published in contracts.js has a lifecycle stage here, so a
        new shared state cannot pass unnoticed
   =========================================================================== */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

const contracts = (await import(new URL('../src/data/contracts.js', import.meta.url))).default;
const schema = (await import(new URL('../src/case/schema.js', import.meta.url))).default;
const store = (await import(new URL('../src/case/store.js', import.meta.url))).default;
const recipients = (await import(new URL('../src/output/recipients.js', import.meta.url))).default;

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
      .find(line => line.includes('case_store.test.mjs:') && !line.includes('check ('));
    results.push({
      id, name, status: 'FAIL',
      evidence: frame ? `${e.message}  [${frame.trim().replace(/^at\s+/, '')}]` : e.message
    });
  }
}

/* A folder that really exists on disk, so the file adapter is exercised rather
   than described. Removed at the end of the run. */
const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-case-'));
const storageDir = path.join(tempRoot, 'case-store');

const FIXED_NOW = '2026-09-22T10:00:00.000Z';
const fixedClock = () => FIXED_NOW;

function newService(dirname) {
  const adapter = dirname
    ? store.makeFileAdapter({ dir: dirname })
    : store.makeMemoryAdapter();
  return store.makeCaseService({
    adapter,
    now: fixedClock,
    caller: 'test-runner',
    identityMode: 'development-only'
  });
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

/* Every service in the "in one machine" checks shares one folder, so the restart
   check proves a file was written and not just an object held in memory. */
const service = newService(storageDir);

/* ------------------------------------------------------------ the checks -- */

check('C01', 'Create a case and read it back with its owner', () => {
  const created = service.create(seed());
  assert.equal(created.ok, true, created.error);
  assert.equal(created.durable, true, 'the file store should report a durable write');
  const read = service.get('CASE-TEST-1');
  assert.equal(read.version, 1);
  assert.equal(read.state, 'draft');
  assert.equal(read.owner_role, 'case_owner');
  assert.equal(read.created_by, 'dev:test-runner');
  assert.equal(read.history.length, 1);
  return `version ${read.version}, state ${read.state}, owner ${read.owner_role}`;
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

  /* An evidence request is the legal first move out of draft. */
  const requested = service.transition(id, {
    action: 'request_evidence', role: 'reviewer',
    evidence_requests: [{ what: 'Recorded billing for the period', from_role: 'case_owner', due: '2026-10-05' }],
    next_action: 'Case owner to supply the recorded billing',
    next_update_due: '2026-10-05',
    note: 'Evidence requested'
  }, { expected_version: current.version });
  assert.equal(requested.ok, true, requested.error);
  versions.push(requested.version);

  /* Then the proposal, which is a second accepted write. */
  const submit = service.transition(id, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Distributor owner to accept or refuse the proposal',
    next_update_due: '2026-10-10'
  }, { expected_version: requested.version });
  assert.equal(submit.ok, true, submit.error);
  versions.push(submit.version);

  /* Then a plain edit, which is also a write. */
  const edited = service.save(Object.assign(schema.clone(service.get(id)), {
    next_action: 'Distributor owner to accept or refuse, restated in plain words'
  }), { expected_version: submit.version, by: 'case-owner' });
  assert.equal(edited.ok, true, edited.error);
  versions.push(edited.version);

  assert.deepEqual(versions, [1, 2, 3, 4], 'expected one version per accepted write');
  /* A refused write does not add a version. */
  const refused = service.transition(id, {
    action: 'approve', role: 'reviewer', approval_note: 'Wrong role'
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
    ['create_case', 'request_evidence', 'submit_for_review', 'edit_case']
  );
  /* The proposal entry carries the scenario that was proposed at that point. */
  const proposal = record.history.find(h => h.action === 'submit_for_review');
  assert.equal(proposal.stage, 'proposal');
  assert.equal(proposal.scenario.price_after, 95, 'the entry carries what was proposed');
  assert.equal(proposal.set_fields.state, 'ready_for_review');
  /* The edit entry names what it changed. */
  const edit = record.history.find(h => h.action === 'edit_case');
  assert.deepEqual(Object.keys(edit.set_fields), ['next_action']);
  return record.history.map(h => h.seq + ':' + h.action).join(', ');
});

check('C05', 'A lost race is refused, and the other writer survives', () => {
  /* Two editors open the same case at the same version. */
  const editorOne = service.get('CASE-TEST-VERSION');
  const editorTwo = service.get('CASE-TEST-VERSION');
  const sharedVersion = editorOne.version;
  assert.equal(editorTwo.version, sharedVersion);

  /* Editor two saves first, and wins. */
  const winner = service.save(Object.assign(schema.clone(editorTwo), {
    next_action: 'Editor two changed this'
  }), { expected_version: editorTwo.version, by: 'editor-two' });
  assert.equal(winner.ok, true, winner.error);
  assert.equal(winner.version, sharedVersion + 1);

  /* Editor one now saves from the copy it read. This must be refused. */
  const loser = service.save(Object.assign(schema.clone(editorOne), {
    next_action: 'Editor one changed this'
  }), { expected_version: editorOne.version, by: 'editor-one' });
  assert.equal(loser.ok, false, 'a stale write must not be accepted');
  assert.equal(loser.code, 'STALE_WRITE');
  assert.equal(loser.expected_version, sharedVersion);
  assert.equal(loser.actual_version, sharedVersion + 1);

  /* The thing that matters: the winner's text is still on disk. */
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
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Approver to accept or refuse', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(proposed.ok, true, proposed.error);

  /* Two approvers both open the proposal at the same version. */
  const staleCopy = service.get(id).version;
  const first = service.transition(id, {
    action: 'approve', role: 'approver',
    approval_note: 'Accepted by the first approver',
    next_action: 'Support owner to schedule the agreed support',
    next_update_due: '2026-10-20'
  }, { expected_version: staleCopy, by: 'approver-one' });
  assert.equal(first.ok, true, first.error);

  const second = service.transition(id, {
    action: 'approve', role: 'approver',
    approval_note: 'Accepted by the second approver',
    next_action: 'Something else',
    next_update_due: '2026-10-21'
  }, { expected_version: staleCopy, by: 'approver-two' });

  assert.equal(second.ok, false);
  assert.equal(second.code, 'STALE_WRITE');
  const stored = service.get(id);
  assert.equal(stored.approval_note, 'Accepted by the first approver');
  assert.equal(stored.version, staleCopy + 1, 'the refused approval added no version');
  return 'second approver refused with ' + second.code + '; the first approval stands';
});

check('C07', 'The same content submitted twice is refused', () => {
  const current = service.get('CASE-TEST-VERSION');
  const first = service.save(schema.clone(current), { expected_version: current.version });
  assert.equal(first.ok, false);
  assert.equal(first.code, 'DUPLICATE_SUBMISSION');
  const after = service.get('CASE-TEST-VERSION');
  assert.equal(after.version, current.version, 'a refused duplicate must not add a version');
  return first.error;
});

check('C08', 'A proposal is not an approval, an approval is not a delivery, and a delivery is not an outcome', () => {
  /* Walk a fresh case through all four stages and record the stage at each. */
  const id = 'CASE-TEST-STAGES';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-B' }));
  const stages = [];

  const proposed = service.transition(id, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Reviewer to check the evidence', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(proposed.ok, true, proposed.error);
  stages.push(proposed.stage);

  /* The point of this check: a proposal must not read as an approval. */
  assert.equal(proposed.state, 'ready_for_review');
  assert.notEqual(proposed.state, 'approved');
  let record = service.get(id);
  assert.equal(record.support, null, 'a proposal has not delivered anything');
  assert.equal(record.outcome, null, 'a proposal has no outcome');
  assert.equal(record.approval_note, null, 'a proposal carries no approval');

  /* Approving is a different move, by a different role. */
  const approved = service.transition(id, {
    action: 'approve', role: 'approver', approval_note: 'Accepted as proposed',
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: proposed.version });
  assert.equal(approved.ok, true, approved.error);
  stages.push(approved.stage);
  assert.equal(approved.state, 'approved');
  record = service.get(id);
  assert.equal(record.support, null, 'an approval has not delivered anything yet');
  assert.equal(record.outcome, null, 'an approval has no outcome');

  /* Delivering is a third move. */
  const delivered = service.transition(id, {
    action: 'record_delivery', role: 'support_owner',
    support: {
      support_eur: 500, delivered_on: '2026-10-12',
      what: 'One-off launch support, given once'
    },
    next_action: 'Case owner to record what it achieved', next_update_due: '2026-12-01'
  }, { expected_version: approved.version });
  assert.equal(delivered.ok, true, delivered.error);
  stages.push(delivered.stage);
  assert.equal(delivered.state, 'delivered');
  record = service.get(id);
  assert.equal(record.support.support_eur, 500);
  assert.equal(record.outcome, null, 'a delivery has no outcome until one is recorded');

  /* The outcome is the fourth move, and it is a separate entry. */
  const outcome = service.transition(id, {
    action: 'record_outcome', role: 'case_owner',
    outcome: {
      what: 'Volume held at the agreed level; no further support paid',
      observed_on: '2026-11-30', quantity_after: 120,
      quantity_label: 'observed history', counts_as_new_business: true
    }
  }, { expected_version: delivered.version });
  assert.equal(outcome.ok, true, outcome.error);
  stages.push(outcome.stage);
  assert.equal(outcome.state, 'outcome_recorded');

  assert.deepEqual(stages, ['proposal', 'approval', 'delivery', 'outcome']);
  const evidence = schema.stageEvidence(service.get(id));
  assert.equal(evidence.commercial_occasions, 1, 'one delivery is one commercial occasion, not four');
  assert.equal(evidence.proposal_recorded, true);
  assert.equal(evidence.approval_recorded, true);
  assert.equal(evidence.delivery_recorded, true);
  assert.equal(evidence.outcome_recorded, true);
  return 'stages ' + stages.join(' -> ') + '; commercial occasions: ' + evidence.commercial_occasions;
});

check('C09', 'A stage cannot be reached by skipping the one before it', () => {
  const id = 'CASE-TEST-SKIP';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-C' }));
  /* Straight to approved, without proposing anything. */
  const jump = service.transition(id, {
    action: 'approve', role: 'approver', approval_note: 'Approved without a proposal'
  }, { expected_version: 1 });
  assert.equal(jump.ok, false);
  assert.equal(jump.code, 'NOT_ALLOWED_FROM_STATE');

  /* Delivery cannot be recorded without an approval. */
  const noApproval = service.transition(id, {
    action: 'record_delivery', role: 'support_owner',
    support: { support_eur: 100, delivered_on: '2026-10-12', what: 'Support before any approval' }
  }, { expected_version: 1 });
  assert.equal(noApproval.ok, false);
  assert.equal(noApproval.code, 'NOT_ALLOWED_FROM_STATE');

  /* An outcome cannot be recorded without a delivery. */
  const noDelivery = service.transition(id, {
    action: 'record_outcome', role: 'case_owner',
    outcome: { what: 'An outcome with nothing delivered', observed_on: '2026-11-01', counts_as_new_business: true }
  }, { expected_version: 1 });
  assert.equal(noDelivery.ok, false);
  assert.equal(noDelivery.code, 'NOT_ALLOWED_FROM_STATE');
  return jump.error;
});

check('C10', 'The wrong role cannot make a move', () => {
  /* Where the move itself is available at this state, the role guard is the
     thing being tested, so the refusal names the role. */
  const id = 'CASE-TEST-ROLE';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-D' }));

  /* Only a case owner proposes. A reviewer may not. */
  const reviewerProposes = service.transition(id, {
    action: 'submit_for_review', role: 'reviewer', scenario,
    next_action: 'Reviewer proposing its own review', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(reviewerProposes.ok, false);
  assert.equal(reviewerProposes.code, 'ROLE_NOT_PERMITTED');

  /* Only a reviewer asks for evidence. A case owner may not. */
  const ownerRequests = service.transition(id, {
    action: 'request_evidence', role: 'case_owner',
    evidence_requests: [{ what: 'Its own evidence', from_role: 'case_owner', due: '2026-10-01' }],
    next_action: 'Owner to supply its own evidence', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(ownerRequests.ok, false);
  assert.equal(ownerRequests.code, 'ROLE_NOT_PERMITTED');

  /* A move with no role at all is refused rather than attributed to nobody. */
  const noRole = service.transition(id, {
    action: 'submit_for_review', scenario,
    next_action: 'Nobody proposed this', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(noRole.ok, false);
  assert.equal(noRole.code, 'ROLE_REQUIRED');

  /* Nothing above moved the case. */
  assert.equal(service.get(id).state, 'draft', 'a refused move must not move the case');
  assert.equal(service.get(id).version, 1);

  /* Now the separation that matters most: at a real proposal, a reviewer must
     not be the one who accepts it. */
  const proposed = service.transition(id, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Approver to accept or refuse', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(proposed.ok, true, proposed.error);
  const reviewerApproves = service.transition(id, {
    action: 'approve', role: 'reviewer', approval_note: 'The reviewer approved its own proposal'
  }, { expected_version: proposed.version });
  assert.equal(reviewerApproves.ok, false);
  /* Two independent reasons a reviewer cannot approve: the move is an approver's
     move, and (were it offered) the role is wrong. Either way it is refused, and
     the case must not be approved. */
  assert.ok(['ROLE_NOT_PERMITTED', 'NOT_ALLOWED_FROM_STATE'].includes(reviewerApproves.code),
    'expected a refusal, got ' + reviewerApproves.code);
  assert.equal(service.get(id).state, 'ready_for_review', 'the case must not be approved by a reviewer');
  assert.equal(service.get(id).approval_note, null);

  /* And an approver cannot give the support: that is the support owner's move. */
  const approveFirst = service.transition(id, {
    action: 'approve', role: 'approver', approval_note: 'Accepted, so a delivery is now possible',
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: proposed.version });
  assert.equal(approveFirst.ok, true, approveFirst.error);
  const approverDelivers = service.transition(id, {
    action: 'record_delivery', role: 'approver',
    support: { support_eur: 100, delivered_on: '2026-10-12', what: 'Approver delivered it' }
  }, { expected_version: approveFirst.version });
  assert.equal(approverDelivers.ok, false);
  assert.equal(approverDelivers.code, 'ROLE_NOT_PERMITTED');
  assert.equal(service.get(id).state, 'approved', 'the approver must not have delivered anything');
  return `${reviewerProposes.code} / ${ownerRequests.code} / ${noRole.code}; `
    + `reviewer approval refused with ${reviewerApproves.code}; approver delivery refused with ${approverDelivers.code}`;
});

check('C11', 'A move that is missing what it needs is refused with a plain reason', () => {
  const id = 'CASE-TEST-INPUT';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-E' }));
  const noDate = service.transition(id, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Reviewer to check the evidence'
  }, { expected_version: 1 });
  assert.equal(noDate.ok, false);
  assert.equal(noDate.code, 'MISSING_INPUT');
  assert.match(noDate.error, /next_update_due/);

  const badSupport = service.transition(id, {
    action: 'request_evidence', role: 'reviewer',
    evidence_requests: [{ what: 'Billing rows', from_role: 'case_owner' }]
  }, { expected_version: 1 });
  assert.equal(badSupport.ok, false);
  assert.equal(badSupport.code, 'MISSING_INPUT');
  assert.match(badSupport.error, /due/);
  return noDate.error;
});

check('C12', 'A waiting record says who owes the next action and when (CASE-03)', () => {
  const id = 'CASE-TEST-OWNER';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-F' }));
  const proposed = service.transition(id, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Distributor owner to accept or refuse',
    next_update_due: '2026-10-10',
    owner_role: 'approver'
  }, { expected_version: 1 });
  assert.equal(proposed.ok, true, proposed.error);

  const work = schema.openWork(service.get(id), '2026-09-22');
  assert.equal(work.owner_role, 'approver');
  assert.equal(work.next_action, 'Distributor owner to accept or refuse');
  assert.equal(work.next_update_due, '2026-10-10');
  assert.equal(work.overdue, false);
  assert.equal(work.due_today, false);

  /* And the queue shows it, overdue first. */
  const overdueCase = service.create(seed({ case_id: 'CASE-TEST-LATE', part_number: 'SYNTH-PART-G' }));
  assert.equal(overdueCase.ok, true, overdueCase.error);
  service.transition('CASE-TEST-LATE', {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Long overdue evidence', next_update_due: '2026-09-01'
  }, { expected_version: 1 });
  const queue = service.queue('2026-09-22');
  assert.equal(queue.length >= 2, true, 'expected at least two open cases');
  assert.equal(queue[0].case_id, 'CASE-TEST-LATE', 'the overdue case should sort first');
  assert.equal(queue[0].overdue, true);
  return `owner ${work.owner_role}, due ${work.next_update_due}; queue head ${queue[0].case_id} overdue ${queue[0].overdue}`;
});

check('C13', 'A closed case owes nothing further', () => {
  const work = schema.openWork(service.get('CASE-TEST-STAGES'), '2026-09-22');
  assert.equal(work.closed, true);
  assert.equal(work.next_action, null);
  assert.equal(work.next_update_due, null);
  assert.equal(work.overdue, false);
  /* And it cannot be reopened, because that would let one occasion run twice. */
  const reopen = service.transition('CASE-TEST-STAGES', {
    action: 'reopen_case', role: 'case_owner', next_action: 'Run it again'
  }, { expected_version: service.get('CASE-TEST-STAGES').version });
  assert.equal(reopen.ok, false);
  assert.equal(reopen.code, 'CASE_IS_FINISHED');
  return reopen.error;
});

check('C14', 'A correction replaces its predecessor and does not multiply the activity (CASE-06)', () => {
  const id = 'CASE-TEST-STAGES';
  const before = service.get(id);
  const occasionsBefore = schema.commercialEventCount(before);
  const deliveryEntry = before.history.find(h => h.action === 'record_delivery');
  assert.ok(deliveryEntry, 'the delivery entry should be in the log');

  const corrected = service.correct(id, {
    corrects_sequence: deliveryEntry.seq,
    role: 'case_owner',
    reason: 'The recorded support was 500; the agreed figure was 250. Correcting the amount.',
    replacement: {
      support: {
        event_id: before.support.event_id, support_eur: 250,
        delivered_on: '2026-10-12', what: 'One-off launch support, given once', by_role: 'support_owner'
      }
    }
  }, { expected_version: before.version, by: 'case-owner' });

  assert.equal(corrected.ok, true, corrected.error);
  const after = service.get(id);

  /* The earlier entry is still there: the decision made on it stays visible. */
  assert.ok(after.history.find(h => h.seq === deliveryEntry.seq),
    'correcting must not remove the entry it corrects');
  assert.equal(after.history.length, before.history.length + 1);
  assert.equal(after.version, before.version + 1);

  /* The correction names what it replaced. */
  const correctionEntry = after.history[after.history.length - 1];
  assert.equal(correctionEntry.kind, 'correction');
  assert.equal(correctionEntry.correction_of, deliveryEntry.seq);
  assert.equal(after.correction_of, deliveryEntry.seq);

  /* The value is corrected. */
  assert.equal(after.support.support_eur, 250);
  assert.equal(after.support.event_id, before.support.event_id, 'the occasion keeps its identity');

  /* And the activity is not counted twice. */
  assert.equal(schema.commercialEventCount(after), occasionsBefore,
    'a correction must not add a commercial occasion');
  assert.equal(schema.commercialEventCount(after), 1);

  return `occasions before ${occasionsBefore}, after ${schema.commercialEventCount(after)}; `
    + `support corrected 500 -> ${after.support.support_eur}`;
});

check('C15', 'A correction cannot be pointed at the same entry twice', () => {
  const id = 'CASE-TEST-STAGES';
  const current = service.get(id);
  const deliverySeq = current.history.find(h => h.action === 'record_delivery').seq;
  const approveSeq = current.history.find(h => h.action === 'approve').seq;

  /* The delivery has already been corrected. A second correction of it would
     fork the trail, so it is refused. */
  const again = service.correct(id, {
    corrects_sequence: deliverySeq, role: 'case_owner',
    reason: 'Correcting it a second time'
  }, { expected_version: current.version });
  assert.equal(again.ok, false);
  assert.equal(again.code, 'TARGET_ALREADY_CORRECTED');

  /* A correction with no reason is refused: a silent correction is not a record. */
  const silent = service.correct(id, {
    corrects_sequence: approveSeq, role: 'case_owner'
  }, { expected_version: current.version });
  assert.equal(silent.ok, false);
  assert.equal(silent.code, 'CORRECTION_NEEDS_REASON');

  /* And a correction cannot be used to move the case. */
  const moves = service.correct(id, {
    corrects_sequence: approveSeq, role: 'case_owner',
    reason: 'Trying to un-close the case', replacement: { state: 'delivered' }
  }, { expected_version: current.version });
  assert.equal(moves.ok, false);
  assert.equal(moves.code, 'CORRECTION_CANNOT_MOVE_STATE');

  /* None of the three attempts left a mark on the stored record. */
  assert.equal(service.get(id).version, current.version);
  return `${again.code} | ${silent.code} | ${moves.code}`;
});

check('C16', 'One case cannot record a second delivery of the same support', () => {
  /* Built against the rule book directly, because the lifecycle would not
     normally offer the move twice. The case is wound back to "approved" with no
     support and no outcome, but the log still carries the delivery already made
     on it - which is exactly the situation the guard is for. */
  const record = service.get('CASE-TEST-STAGES');
  assert.equal(schema.commercialEventCount(record), 1, 'the log should already carry one delivery');
  const doctored = schema.clone(record);
  doctored.state = 'approved';
  doctored.support = null;
  doctored.outcome = null;
  doctored.next_action = 'Support owner to give the agreed support';
  doctored.next_update_due = '2026-10-15';
  assert.equal(schema.validate(doctored).ok, true, schema.validate(doctored).errors.join(' '));

  const attempt = schema.applyTransition(doctored, {
    action: 'record_delivery', role: 'support_owner', by: 'test-runner', at: FIXED_NOW,
    support: { support_eur: 400, delivered_on: '2026-11-01', what: 'A second support payment' }
  });
  assert.equal(attempt.ok, false);
  assert.equal(attempt.code, 'DUPLICATE_SUPPORT');
  assert.equal(schema.commercialEventCount(doctored), 1);
  return attempt.error;
});

check('C17', 'Volume migrated from another Isuzu product is not newly won business (CASE-05)', () => {
  /* A migration case: 40 units moved from a BVP part to the Genuine counterpart. */
  const migId = 'CASE-TEST-MIGRATION';
  service.create(seed({ case_id: migId, part_number: 'SYNTH-GENUINE-A' }));
  const migProposed = service.transition(migId, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Approver to accept the migration', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  const migApproved = service.transition(migId, {
    action: 'approve', role: 'approver', approval_note: 'Migration accepted',
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: migProposed.version });
  const migDelivered = service.transition(migId, {
    action: 'record_delivery', role: 'support_owner',
    support: { support_eur: 300, delivered_on: '2026-10-12', what: 'Launch support for the migrated volume' },
    next_action: 'Case owner to record the outcome', next_update_due: '2026-12-01'
  }, { expected_version: migApproved.version });
  assert.equal(migDelivered.ok, true, migDelivered.error);
  const migOutcome = service.transition(migId, {
    action: 'record_outcome', role: 'case_owner',
    outcome: {
      what: '40 units now bought on the Genuine counterpart; the same trucks, the same demand',
      observed_on: '2026-11-30', quantity_after: 40, quantity_label: 'observed history',
      migration_from: 'SYNTH-PART-A', migration_to: 'SYNTH-GENUINE-A',
      counts_as_new_business: false
    }
  }, { expected_version: migDelivered.version });
  assert.equal(migOutcome.ok, true, migOutcome.error);

  /* Link the migration to the case it came from. */
  const link = service.linkCases('CASE-TEST-STAGES', migId, 'migrates_to', {
    expected_versions: {
      'CASE-TEST-STAGES': service.get('CASE-TEST-STAGES').version,
      [migId]: service.get(migId).version
    }
  });
  assert.equal(link.ok, true, link.error);
  assert.equal(link.spec.counts_apart, false, 'a migration is not a separate commercial event');

  /* A genuinely new piece of business, so the rollup has both kinds. */
  const newId = 'CASE-TEST-NEW';
  service.create(seed({ case_id: newId, part_number: 'SYNTH-PART-H' }));
  const newProposed = service.transition(newId, {
    action: 'submit_for_review', role: 'case_owner', scenario,
    next_action: 'Approver to accept', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  const newApproved = service.transition(newId, {
    action: 'approve', role: 'approver', approval_note: 'Accepted',
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: newProposed.version });
  const newDelivered = service.transition(newId, {
    action: 'record_delivery', role: 'support_owner',
    support: { support_eur: 700, delivered_on: '2026-10-12', what: 'Launch support for a genuinely new part' },
    next_action: 'Case owner to record the outcome', next_update_due: '2026-12-01'
  }, { expected_version: newApproved.version });
  assert.equal(newDelivered.ok, true, newDelivered.error);
  const newOutcome = service.transition(newId, {
    action: 'record_outcome', role: 'case_owner',
    outcome: {
      what: '60 units billed that were not billed before', observed_on: '2026-11-30',
      quantity_after: 60, quantity_label: 'observed history', counts_as_new_business: true
    }
  }, { expected_version: newDelivered.version });
  assert.equal(newOutcome.ok, true, newOutcome.error);

  /* Now roll the whole portfolio up conservatively. */
  const rollup = service.conservativeRollup([migId, newId], '2026-12-01');
  assert.equal(rollup.newly_won_units, 60,
    'only the genuinely new 60 units are newly won; the 40 migrated units are not');
  assert.equal(rollup.migrated_units_not_new_business, 40);
  assert.equal(rollup.support_total_eur, 1000, '300 + 700, each counted once');
  assert.equal(rollup.distinct_commercial_occasions, 2);
  const migratedRow = rollup.rows.find(r => r.case_id === migId);
  assert.equal(migratedRow.counted_as, 'migrated from another product');
  /* And an outcome that claims a migration is new business is refused outright. */
  const bogus = schema.applyTransition(service.get(newId), {
    action: 'record_outcome', role: 'case_owner', by: 'test-runner', at: FIXED_NOW,
    outcome: { what: 'Migration claimed as new business', observed_on: '2026-12-01',
      migration_from: 'SYNTH-PART-A', counts_as_new_business: true }
  });
  assert.equal(bogus.ok, false, 'a migration presented as new business must be refused');
  return `newly won ${rollup.newly_won_units} units, migrated ${rollup.migrated_units_not_new_business} units, `
    + `support EUR ${rollup.support_total_eur} across ${rollup.distinct_commercial_occasions} occasions`;
});

check('C18', 'A half-written link is detected and can be repaired', () => {
  const clean = service.linkIssues();
  assert.equal(clean.ok, true, 'the links written above should be complete');

  /* Force one side of a link away, without touching the other. This is what a
     partially applied write looks like: one case carries the link and the other
     does not. The record itself stays valid, which is why the link check has to
     exist separately. */
  const adapter = service._adapter;
  const record = adapter.load('CASE-TEST-NEW');
  const withLink = schema.clone(record);
  withLink.links = (withLink.links || []).concat([{
    link_id: 'link:half-written', other_case_id: 'CASE-TEST-STAGES',
    relation: 'continues', counts_apart: true, note: 'A link recorded on one side only'
  }]);
  assert.equal(schema.validate(withLink).ok, true, schema.validate(withLink).errors.join(' '));
  adapter.save('CASE-TEST-NEW', withLink);

  const found = service.linkIssues();
  assert.equal(found.ok, false, 'the one-sided link should be reported');
  assert.equal(found.issues.length, 1);
  assert.match(found.issues[0].problem, /CASE-TEST-NEW only/);

  const repaired = service.repairLinks();
  assert.equal(repaired.ok, true, JSON.stringify(repaired.unrepairable));
  assert.equal(repaired.repaired, 1);
  assert.equal(service.linkIssues().ok, true);
  /* The repair is in the log, so the case can still be rebuilt at any version. */
  const healed = service.get('CASE-TEST-STAGES');
  assert.equal(healed.history.length, healed.version, 'the repair must be a logged entry');
  const repairEntry = healed.history.find(h => h.action === 'link_case');
  assert.equal(repairEntry.kind, 'link');
  assert.equal(repairEntry.commercial, false, 'a link is not a commercial event');
  return found.issues[0].problem;
});

check('C19', 'A record survives a real restart: a new service reads the same folder', () => {
  /* The service that wrote everything above is left behind. These are new
     objects, built from the folder on disk. */
  const reopened = newService(storageDir);
  const record = reopened.get('CASE-TEST-STAGES');
  assert.ok(record, 'the case should still be there after the service was rebuilt');
  assert.equal(record.version >= 6, true);
  assert.equal(record.state, 'outcome_recorded');
  assert.equal(record.support.support_eur, 250, 'the correction survived');
  assert.equal(schema.commercialEventCount(record), 1);

  /* The file itself is on disk, not an object held in memory. */
  const filename = path.join(storageDir, 'cases', 'CASE-TEST-STAGES.json');
  assert.equal(fs.existsSync(filename), true, 'expected a case file at ' + filename);
  const fromDisk = JSON.parse(fs.readFileSync(filename, 'utf8'));
  assert.equal(fromDisk.case_id, 'CASE-TEST-STAGES');
  assert.equal(fromDisk.support.support_eur, 250);

  /* And the queue is rebuilt from disk too. */
  const queue = reopened.queue('2026-09-22');
  assert.equal(queue.some(row => row.case_id === 'CASE-TEST-LATE'), true);
  return `${filename} (${fs.statSync(filename).size} bytes), version ${fromDisk.version}`;
});

check('C20', 'Reopening an earlier version shows the case as it stood then', () => {
  const id = 'CASE-TEST-STAGES';
  const current = service.get(id);
  const approvalEntry = current.history.find(h => h.action === 'approve');
  const deliveryEntry = current.history.find(h => h.action === 'record_delivery');
  const outcomeEntry = current.history.find(h => h.action === 'record_outcome');

  /* As it stood at the approval: proposed and accepted, nothing delivered. */
  const atApproval = service.reopen(id, approvalEntry.seq);
  assert.equal(atApproval.version, approvalEntry.seq);
  assert.equal(atApproval.state, 'approved');
  assert.equal(atApproval.support, null, 'at the approval nothing had been delivered');
  assert.equal(atApproval.outcome, null);
  assert.equal(atApproval.scenario.price_after, 95, 'the proposed inputs are preserved');
  assert.equal(atApproval.approval_note, 'Accepted as proposed');

  /* As it stood at the delivery: given, not yet measured. */
  const atDelivery = service.reopen(id, deliveryEntry.seq);
  assert.equal(atDelivery.state, 'delivered');
  assert.equal(atDelivery.support.support_eur, 500, 'the support as it stood before the correction');
  assert.equal(atDelivery.outcome, null);
  assert.equal(atDelivery.stage, 'delivery');

  /* And the latest, with the corrected support and the outcome. */
  const latest = service.reopen(id);
  assert.equal(latest.version, current.version);
  assert.equal(latest.state, 'outcome_recorded');
  assert.equal(latest.support.support_eur, 250, 'the corrected amount');
  assert.equal(latest.outcome.quantity_after, 120);
  assert.equal(latest.stage, 'outcome');

  /* Asking for a version that does not exist is refused, not guessed at. */
  const beyond = service.reopen(id, current.version + 5);
  assert.equal(beyond.ok, false);
  assert.equal(beyond.code, 'NO_SUCH_VERSION');
  assert.equal(beyond.actual_version, undefined);

  assert.ok(outcomeEntry, 'the outcome entry should be in the log');
  assert.equal(outcomeEntry.stage, 'outcome');
  return `at v${approvalEntry.seq}: ${atApproval.state} / support ${atApproval.support}; `
    + `at v${deliveryEntry.seq}: ${atDelivery.state} / support EUR ${atDelivery.support.support_eur}; `
    + `latest v${latest.version}: ${latest.state} / support EUR ${latest.support.support_eur}`;
});

check('C21', 'A field that looks like a credential is refused', () => {
  const current = service.get('CASE-TEST-STAGES');
  const withSecret = schema.clone(current);
  withSecret.review = { note: 'Looks fine', api_key: 'not-a-real-key' };
  const refused = service.save(withSecret, { expected_version: current.version });
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'SECRET_LIKE_FIELD');
  assert.match(refused.error, /api_key/);

  const inScenario = schema.clone(current);
  inScenario.scenario = Object.assign({}, current.scenario, { source_password: 'hunter2' });
  const alsoRefused = service.save(inScenario, { expected_version: current.version });
  assert.equal(alsoRefused.ok, false);
  assert.equal(alsoRefused.code, 'SECRET_LIKE_FIELD');
  return refused.error;
});

check('C22', 'An undeclared field cannot be stored on a case', () => {
  const current = service.get('CASE-TEST-STAGES');
  const withExtra = schema.clone(current);
  withExtra.commercial_score = 99;
  const refused = service.save(withExtra, { expected_version: current.version });
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'INVALID_RECORD');
  assert.match(refused.error, /commercial_score/);
  return refused.error;
});

check('C23', 'A restore does not silently replace a newer stored case', () => {
  const bundle = service.exportAll();
  /* Take the current case, wind it back, and offer it as a restore. */
  const older = schema.clone(bundle.cases['CASE-TEST-STAGES']);
  older.version = 1;
  older.state = 'draft';
  older.history = [older.history[0]];

  const refused = service.importAll({ cases: { 'CASE-TEST-STAGES': older } }, { overwrite: true });
  assert.equal(refused.refused.length, 1);
  assert.match(refused.refused[0].errors[0], /ahead of the bundle/);
  assert.equal(service.get('CASE-TEST-STAGES').state, 'outcome_recorded',
    'the newer stored case must be untouched');

  /* A case that is not stored yet is restored; one that is, is skipped. */
  const fresh = schema.clone(service.get('CASE-TEST-NEW'));
  fresh.case_id = 'CASE-TEST-RESTORED';
  const added = service.importAll({ cases: { 'CASE-TEST-RESTORED': fresh } });
  assert.equal(added.added, 1);
  const skipped = service.importAll({ cases: { 'CASE-TEST-RESTORED': fresh } });
  assert.deepEqual(skipped.skipped, ['CASE-TEST-RESTORED']);
  return `refused a backwards restore of CASE-TEST-STAGES; added ${added.added}, skipped ${skipped.skipped.length} on the second pass`;
});

check('C24', 'Deleting a case needs its id to be repeated', () => {
  const wrong = service.remove('CASE-TEST-RESTORED', { confirm_case_id: 'something-else' });
  assert.equal(wrong.ok, false);
  assert.equal(wrong.code, 'DELETE_NEEDS_CONFIRMATION');
  assert.ok(service.get('CASE-TEST-RESTORED'), 'the case should still be there');

  const right = service.remove('CASE-TEST-RESTORED', { confirm_case_id: 'CASE-TEST-RESTORED' });
  assert.equal(right.ok, true);
  assert.equal(service.get('CASE-TEST-RESTORED'), null);
  return wrong.error;
});

check('C25', 'An attachment that may carry restricted content is refused, and the gap is stated (SAFE-06)', () => {
  const viewer = recipients.makeDevIdentity({ role: 'viewer', name: 'synthetic participant' });
  const owner = recipients.makeDevIdentity({ role: 'case_owner', name: 'synthetic owner' });

  /* A participant cannot attach at all. */
  const byParticipant = service.attach('CASE-TEST-STAGES', { name: 'brief.pdf' }, viewer);
  assert.equal(byParticipant.ok, false);
  assert.equal(byParticipant.code, 'ATTACHMENT_NOT_PERMITTED');

  /* An owner can attach a clean file, and is told the bytes were not stored. */
  const clean = service.attach('CASE-TEST-STAGES', { name: 'synthetic-note.pdf', restricted: false }, owner);
  assert.equal(clean.ok, true, clean.error);
  assert.equal(clean.stored, false);
  assert.match(clean.storage_gap, /not implemented/);

  /* A file declared restricted is refused. */
  const restricted = service.attach('CASE-TEST-STAGES', { name: 'synthetic-pack.pdf', restricted: true }, owner);
  assert.equal(restricted.ok, false);
  assert.equal(restricted.code, 'ATTACHMENT_NOT_PERMITTED');

  /* A file whose name suggests a restricted source is refused too. */
  const suspicious = service.attach('CASE-TEST-STAGES', { name: 'supplier-cost-detail.xlsx' }, owner);
  assert.equal(suspicious.ok, false);
  assert.equal(suspicious.code, 'ATTACHMENT_NOT_PERMITTED');
  assert.match(suspicious.error, /restricted content/);
  return suspicious.error + ' | storage gap: ' + clean.storage_gap.slice(0, 70) + '...';
});

check('C26', 'Every state published in contracts.js has a lifecycle stage', () => {
  const unmapped = contracts.CASE_STATES.filter(s => !schema.stageOf(s));
  assert.deepEqual(unmapped, [], 'these states have no stage: ' + unmapped.join(', '));
  /* And the four stages a reader must be able to tell apart are all distinct. */
  const stages = ['ready_for_review', 'approved', 'delivered', 'outcome_recorded'].map(schema.stageOf);
  assert.equal(new Set(stages).size, 4, 'proposal, approval, delivery and outcome must be four stages');
  assert.deepEqual(stages, ['proposal', 'approval', 'delivery', 'outcome']);
  return `${contracts.CASE_STATES.length} contract states mapped onto ${schema.STAGES.length} stages`;
});

check('C27', 'The store describes honestly what it is', () => {
  const described = service.describe();
  assert.equal(described.kind, 'files');
  assert.equal(described.durable, true);
  assert.equal(described.shared, false, 'a folder on one machine is not a shared service');
  assert.match(described.statement, /Not shared/);
  const memory = newService().describe();
  assert.equal(memory.durable, false);
  assert.equal(memory.shared, false);
  return `${described.statement} | ${memory.statement}`;
});

/* ---------------------------------------------------------------- report -- */

const width = Math.max(...results.map(r => r.id.length + r.name.length)) + 4;
console.log('');
console.log('AIM durable case record - ' + results.length + ' checks');
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