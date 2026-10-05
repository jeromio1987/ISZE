#!/usr/bin/env node
/* ===========================================================================
   Durable case record - runnable checks (CASE-01 ... CASE-08, F12).

   Run:
     node tests/case_store.test.mjs

   Exit code is 0 only when every check passes. Nothing is skipped and no
   assertion is relaxed to obtain a green run.

   WHAT CHANGED HERE, AND WHAT DID NOT
   -----------------------------------
   This file was written against the eight-state vocabulary that used to be in
   force (`draft, evidence_requested, ready_for_review, approved, rejected,
   delivered, outcome_recorded, no_change_recommended`). CASE-02 brought the
   plan's nine states into force in ONE change - the state values, the
   transition table and every reference together - and this file is one of the
   references, so it moved with that change.

   Every check id (C01..C27) and every check name is kept EXACTLY as it was.
   That is deliberate: a reviewer can put the old run beside the new one and see
   which assertions are the same claim in new words, rather than being handed a
   suite that was quietly rewritten to fit. Where a claim could not survive
   unchanged, the check says so in its own evidence line.

   The old vocabulary -> the new, so a reader can follow the diff:

     state                          | now
     -------------------------------|-------------------------------------------------
     draft                          | draft                     (unchanged)
     evidence_requested             | awaiting_input            (it is the same idea: the
                                    |                            case is waiting on a
                                    |                            stated thing from a
                                    |                            named function)
     ready_for_review               | response_issued           (an answer has gone back)
     approved                       | action_agreed             (the parties agreed an
                                    |                            action; the words
                                    |                            "approved" hid that
                                    |                            nothing was delivered)
     rejected                       | withdrawn                 (taken back by the side
                                    |                            that raised it)
     (none)                         | assessment                (new: the working state)
     (none)                         | submitted                 (new: the clock starts)
     delivered                      | (no state)                the payment is its own
                                    |                            recorded move now, not a
                                    |                            lifecycle state, because a
                                    |                            payment is not a stage the
                                    |                            case is at
     outcome_recorded               | resolved                  (finished with the outcome
                                    |                            known)
     no_change_recommended          | closed_outcome_unknown     (finished, and nobody
                                    |                            knows the result)

     move                           | now
     -------------------------------|-------------------------------------------------
     request_evidence               | request_input
     submit_for_review              | submit
     approve                        | accept_proposal           (against a named proposal
                                    |                            version, with an
                                    |                            approval reference)
     reject                         | withdraw, or terminal_no_change
     close_no_change                | terminal_no_change
     return_for_more_work           | request_input             (the new table has no
                                    |                            "returned" state; what the
                                    |                            case needs is named input)
     record_delivery                | record_support            (a recorded move, not a
                                    |                            transition)
     withdraw_before_delivery       | withdraw
     record_outcome                 | record_outcome            (name unchanged; now a
                                    |                            recorded move that leaves
                                    |                            the state alone)
     reopen_case                    | a new case, linked to the old one

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

   The newer, longer suite for the same component is tests/case_service.test.mjs.
   It covers CASE-01..05 in the vocabulary now in force and adds the checks those
   five tasks require. This file is kept because its check ids are referenced
   from the project's own progress record, and because a suite that is only ever
   written fresh cannot show that a migration changed nothing it should not have.
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

const terms = (extra = {}) => Object.assign({
  unit: 'unit', price_before: 100, price_after: 95,
  quantity_before: 100, quantity_after: 120, quantity_label: 'manual scenario',
  currency: 'EUR', conditions: 'Synthetic condition.', eligible_reference: 'SYNTH-ELIGIBLE',
  offer_effective_date: '2026-10-01', support_eur: 500, support_direction: 'to_participant'
}, extra);

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

  /* `request_evidence` was the legal first move out of draft under the old
     vocabulary. Asking for input is still a reviewer's move, but it is not
     offered from draft any more: a case is submitted first, and then the
     reviewer asks or assesses. So the first move is `submit`. */
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take the case', next_update_due: '2026-10-01',
    note: 'Submitted'
  }, { expected_version: current.version });
  assert.equal(submitted.ok, true, submitted.error);
  versions.push(submitted.version);

  /* Then the assessment, which is a second accepted write. */
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess against the recorded evidence',
    next_update_due: '2026-10-05'
  }, { expected_version: submitted.version });
  assert.equal(assessing.ok, true, assessing.error);
  versions.push(assessing.version);

  /* Then a plain edit, which is also a write. */
  const edited = service.saveRecord(
    Object.assign(schema.clone(service.get(id)), {
      next_action: 'Assess against the recorded evidence, restated in plain words'
    }),
    { expected_version: assessing.version, by: 'reviewer-1' });
  assert.equal(edited.ok, true, edited.error);
  versions.push(edited.version);

  assert.deepEqual(versions, [1, 2, 3, 4], 'expected one version per accepted write');
  /* A refused write does not add a version. `approve` by a reviewer is refused
     twice over now: it is not the reviewer's move, and nothing has been proposed
     to accept. Either refusal is correct; the version must not move either way. */
  const refused = service.transition(id, {
    action: 'accept_proposal', role: 'reviewer', approval_note: 'Wrong role'
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
  /* The assessment entry carries the state it moved to. Under the old
     vocabulary this step was `submit_for_review` moving to `ready_for_review`;
     the claim being made is the same one - the entry says what it set. */
  const assessing = record.history.find(h => h.action === 'begin_assessment');
  assert.equal(assessing.stage, 'assessment');
  assert.equal(assessing.set_fields.state, 'assessment');
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
  const winner = service.saveRecord(Object.assign(schema.clone(editorTwo), {
    next_action: 'Editor two changed this'
  }), { expected_version: editorTwo.version, by: 'editor-two' });
  assert.equal(winner.ok, true, winner.error);
  assert.equal(winner.version, sharedVersion + 1);

  /* Editor one now saves from the copy it read. This must be refused. */
  const loser = service.saveRecord(Object.assign(schema.clone(editorOne), {
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
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take it', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(submitted.ok, true, submitted.error);

  /* Two reviewers both open the case at the same version. */
  const staleCopy = service.get(id).version;
  const first = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess it', next_update_due: '2026-10-05'
  }, { expected_version: staleCopy, by: 'reviewer-one' });
  assert.equal(first.ok, true, first.error);

  const second = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Something else', next_update_due: '2026-10-21'
  }, { expected_version: staleCopy, by: 'reviewer-two' });

  assert.equal(second.ok, false);
  assert.equal(second.code, 'STALE_WRITE');
  const stored = service.get(id);
  assert.equal(stored.next_action, 'Assess it');
  assert.equal(stored.version, staleCopy + 1, 'the refused move added no version');
  return 'second reviewer refused with ' + second.code + '; the first move stands';
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

check('C08', 'A proposal is not an approval, an approval is not a delivery, and a delivery is not an outcome', () => {
  /* Walk a fresh case the whole way. Under the old vocabulary this was four
     lifecycle states with a stage each: proposal, approval, delivery, outcome.
     It is now four recorded moves, and only the first two of them are states -
     because a payment is not a stage the case is standing at. The claim being
     tested is unchanged and is stated as the four things a reader must be able
     to tell apart. */
  const id = 'CASE-TEST-STAGES';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-B' }));
  const steps = [];

  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take the case', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(submitted.ok, true, submitted.error);
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Reviewer to check the evidence', next_update_due: '2026-10-02'
  }, { expected_version: submitted.version });
  assert.equal(assessing.ok, true, assessing.error);

  /* A proposal is recorded, and it is not an approval. */
  const proposed = service.proposeTerms(id, {
    terms: terms(), offered_by_role: 'case_owner',
    approval_route: 'Synthetic route: the account owner approves.',
    expires_on: '2026-12-31'
  }, { expected_version: assessing.version, role: 'case_owner' });
  assert.equal(proposed.ok, true, proposed.error);
  steps.push('proposal');
  let record = service.get(id);
  assert.equal(record.state, 'assessment', 'recording a proposal must not move the case');
  assert.equal(schema.acceptedProposal(record), null, 'a proposal is not an approval');
  assert.equal(record.support, null, 'a proposal has not delivered anything');
  assert.equal(record.outcome, null, 'a proposal has no outcome');

  /* An answer goes back, with the support commitment stated. Still nothing
     delivered. */
  const answered = service.transition(id, {
    action: 'issue_response', role: 'case_owner',
    response: {
      what: 'We can support the additional volume at the stated price.',
      issued_on: '2026-09-30', commitment: 'support', reference: 'SYNTH-RESPONSE-STAGES'
    },
    next_action: 'Approver to accept or refuse the proposed terms',
    next_update_due: '2026-10-10'
  }, { expected_version: proposed.version });
  assert.equal(answered.ok, true, answered.error);
  record = service.get(id);
  assert.equal(record.state, 'response_issued');
  assert.equal(record.support, null, 'an answer has not delivered anything');
  assert.equal(record.outcome, null, 'an answer has no outcome');

  /* Approving is a different move, by a different function, against a named
     version. */
  const approved = service.transition(id, {
    action: 'accept_proposal', role: 'approver',
    approval_note: 'Accepted as proposed',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-STAGES' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: answered.version });
  assert.equal(approved.ok, true, approved.error);
  steps.push('approval');
  record = service.get(id);
  assert.equal(record.state, 'action_agreed');
  assert.equal(record.support, null, 'an approval has not delivered anything yet');
  assert.equal(record.outcome, null, 'an approval has no outcome');

  /* Delivering is a third move, and it is recorded against the action. */
  const delivered = service.recordSupport(id, {
    support_eur: 500, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'One-off launch support, given once', by_role: 'support_owner'
  }, { expected_version: record.version, role: 'support_owner' });
  assert.equal(delivered.ok, true, delivered.error);
  steps.push('delivery');
  record = service.get(id);
  assert.equal(record.state, 'action_agreed',
    'recording a payment must not move the state: a payment is not a stage');
  assert.equal(record.support.support_eur, 500);
  assert.equal(record.outcome, null, 'a delivery has no outcome until one is recorded');

  /* The outcome is the fourth record, and it is a separate entry. */
  const outcome = service.recordOutcome(id, {
    what: 'Volume held at the agreed level; no further support paid',
    observed_on: '2026-11-30', quantity_after: 120,
    quantity_label: 'observed history', counts_as_new_business: true
  }, { expected_version: record.version, role: 'case_owner' });
  assert.equal(outcome.ok, true, outcome.error);
  steps.push('outcome');
  record = service.get(id);
  assert.equal(record.state, 'action_agreed', 'recording an outcome must not move the state');

  assert.deepEqual(steps, ['proposal', 'approval', 'delivery', 'outcome']);
  const evidence = schema.stageEvidence(record);
  assert.equal(evidence.commercial_occasions, 1, 'one payment is one commercial occasion, not four');
  assert.equal(evidence.proposal_recorded, true);
  assert.equal(evidence.approval_recorded, true);
  assert.equal(evidence.delivery_recorded, true);
  assert.equal(evidence.outcome_recorded, true);

  /* And the case can be closed with its outcome known. */
  const closed = service.transition(id, {
    action: 'close_resolved', role: 'case_owner'
  }, { expected_version: record.version });
  assert.equal(closed.ok, true, closed.error);
  assert.equal(service.get(id).state, 'resolved');
  return steps.join(' -> ') + '; commercial occasions: ' + evidence.commercial_occasions
    + '; closed at ' + service.get(id).state;
});

check('C09', 'A stage cannot be reached by skipping the one before it', () => {
  const id = 'CASE-TEST-SKIP';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-C' }));
  /* Straight to agreed, without anything being proposed. */
  const jump = service.transition(id, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Approved without a proposal',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-NOT-REAL' }
  }, { expected_version: 1 });
  assert.equal(jump.ok, false);
  assert.equal(jump.code, 'NOT_ALLOWED_FROM_STATE');

  /* Delivery cannot be recorded without an accepted proposal. */
  const noApproval = service.recordSupport(id, {
    support_eur: 100, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Support before any approval'
  }, { expected_version: 1, role: 'support_owner' });
  assert.equal(noApproval.ok, false);
  assert.equal(noApproval.code, 'SUPPORT_NEEDS_AN_ACCEPTED_PROPOSAL');

  /* An outcome cannot be recorded without a delivery. */
  const noDelivery = service.recordOutcome(id, {
    what: 'An outcome with nothing delivered', observed_on: '2026-11-01',
    counts_as_new_business: true
  }, { expected_version: 1, role: 'case_owner' });
  assert.equal(noDelivery.ok, false);
  assert.equal(noDelivery.code, 'OUTCOME_NEEDS_SUPPORT');

  /* And a case cannot be closed as resolved without an outcome: if the result is
     not known, `closed_outcome_unknown` is the honest state. */
  const closedBlind = service.transition(id, {
    action: 'close_resolved', role: 'case_owner'
  }, { expected_version: 1 });
  assert.equal(closedBlind.ok, false);
  return `${jump.code} | ${noApproval.code} | ${noDelivery.code}`;
});

check('C10', 'The wrong role cannot make a move', () => {
  /* Where the move itself is available at this state, the role guard is the
     thing being tested, so the refusal names the role. */
  const id = 'CASE-TEST-ROLE';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-D' }));

  /* Only a case owner submits. A reviewer may not. */
  const reviewerSubmits = service.transition(id, {
    action: 'submit', role: 'reviewer',
    next_action: 'Reviewer submitting its own question', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(reviewerSubmits.ok, false);
  assert.equal(reviewerSubmits.code, 'ROLE_NOT_PERMITTED');

  /* Only a reviewer asks for input, and the case is a draft, so the refusal is
     the state's rather than the role's. Both are true; the state is checked
     first, so that is what is asserted. */
  const ownerRequests = service.transition(id, {
    action: 'request_input', role: 'case_owner',
    evidence_requests: [{ what: 'Its own evidence', from_role: 'case_owner', due: '2026-10-01' }]
  }, { expected_version: 1 });
  assert.equal(ownerRequests.ok, false);
  assert.equal(ownerRequests.code, 'NOT_ALLOWED_FROM_STATE');

  /* A move with no role at all is refused rather than attributed to nobody. */
  const noRole = service.transition(id, {
    action: 'submit', next_action: 'Nobody submitted this', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(noRole.ok, false);
  assert.equal(noRole.code, 'ROLE_REQUIRED');

  /* Nothing above moved the case. */
  assert.equal(service.get(id).state, 'draft', 'a refused move must not move the case');
  assert.equal(service.get(id).version, 1);

  /* Now the role guard at a state where the move is genuinely offered. */
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Approver to accept or refuse', next_update_due: '2026-10-01'
  }, { expected_version: 1 });
  assert.equal(submitted.ok, true, submitted.error);
  const reviewerTakesItByRole = service.transition(id, {
    action: 'begin_assessment', role: 'case_owner',
    next_action: 'The owner assessing its own question', next_update_due: '2026-10-02'
  }, { expected_version: submitted.version });
  assert.equal(reviewerTakesItByRole.ok, false);
  assert.equal(reviewerTakesItByRole.code, 'ROLE_NOT_PERMITTED');

  /* The separation that matters most: whoever assessed a case must not be the
     one who accepts it. */
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer',
    next_action: 'Assess it', next_update_due: '2026-10-02'
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

  /* And an approver cannot give the support: that is the support owner's move. */
  const approveFirst = service.transition(id, {
    action: 'accept_proposal', role: 'approver',
    approval_note: 'Accepted, so a delivery is now possible',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-ROLE' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: proposed.version });
  assert.equal(approveFirst.ok, true, approveFirst.error);
  const approverDelivers = service.recordSupport(id, {
    support_eur: 100, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Approver delivered it'
  }, { expected_version: approveFirst.version, role: 'approver' });
  assert.equal(approverDelivers.ok, false);
  assert.equal(approverDelivers.code, 'ROLE_NOT_PERMITTED');
  assert.equal(service.get(id).state, 'action_agreed', 'the approver must not have delivered anything');
  return `${reviewerSubmits.code} / ${ownerRequests.code} / ${noRole.code}; `
    + `reviewer approval refused with ${reviewerApproves.code}; approver delivery refused with ${approverDelivers.code}`;
});

check('C11', 'A move that is missing what it needs is refused with a plain reason', () => {
  const id = 'CASE-TEST-INPUT';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-E' }));
  const noDate = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to check the evidence'
  }, { expected_version: 1 });
  assert.equal(noDate.ok, false);
  assert.equal(noDate.code, 'MISSING_INPUT');
  assert.match(noDate.error, /next_update_due/);

  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to check it',
    next_update_due: '2026-10-01'
  }, { expected_version: 1 });

  const badRequest = service.transition(id, {
    action: 'request_input', role: 'reviewer',
    evidence_requests: [{ what: 'Billing rows', from_role: 'case_owner' }]
  }, { expected_version: submitted.version });
  assert.equal(badRequest.ok, false);
  assert.equal(badRequest.code, 'MISSING_INPUT');
  assert.match(badRequest.error, /due/);
  return noDate.error;
});

check('C12', 'A waiting record says who owes the next action and when (CASE-03)', () => {
  const id = 'CASE-TEST-OWNER';
  service.create(seed({ case_id: id, part_number: 'SYNTH-PART-F' }));
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner',
    next_action: 'Distributor owner to accept or refuse',
    next_update_due: '2026-10-10',
    owner_role: 'approver'
  }, { expected_version: 1 });
  assert.equal(submitted.ok, true, submitted.error);

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
    action: 'submit', role: 'case_owner',
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
  /* And it cannot be reopened, because that would let one occasion run twice.
     Under the old vocabulary this was `reopen_case`; the new table has no
     reopening move at all, for the same reason, so the refusal is that the move
     does not exist on a finished case. */
  const reopen = service.transition('CASE-TEST-STAGES', {
    action: 'submit', role: 'case_owner', next_action: 'Run it again',
    next_update_due: '2026-10-01'
  }, { expected_version: service.get('CASE-TEST-STAGES').version });
  assert.equal(reopen.ok, false);
  assert.equal(reopen.code, 'CASE_IS_FINISHED');
  assert.match(reopen.error, /start a new case/i);
  return reopen.error.slice(0, 150);
});

check('C14', 'A correction replaces its predecessor and does not multiply the activity (CASE-06)', () => {
  const id = 'CASE-TEST-STAGES';
  const before = service.get(id);
  const occasionsBefore = schema.commercialEventCount(before);
  const deliveryEntry = before.history.find(h => h.action === 'record_support');
  assert.ok(deliveryEntry, 'the delivery entry should be in the log');

  const corrected = service.correct(id, {
    corrects_sequence: deliveryEntry.seq,
    role: 'case_owner',
    reason: 'The recorded support was 500; the agreed figure was 250. Correcting the amount.',
    replacement: {
      support: {
        action_identifier: before.support.action_identifier, support_eur: 250,
        net_terms_basis: 'net', delivered_on: '2026-10-12',
        what: 'One-off launch support, given once', by_role: 'support_owner'
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
  /* A correction fixes evidence; it does not move the case. */
  assert.equal(after.state, before.state, 'a correction must not move the case');

  /* The correction names what it replaced. */
  const correctionEntry = after.history[after.history.length - 1];
  assert.equal(correctionEntry.kind, 'correction');
  assert.equal(correctionEntry.correction_of, deliveryEntry.seq);
  assert.equal(after.correction_of, deliveryEntry.seq);

  /* The value is corrected. */
  assert.equal(after.support.support_eur, 250);
  assert.equal(after.support.action_identifier, before.support.action_identifier,
    'the occasion keeps its identity');

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
  const deliverySeq = current.history.find(h => h.action === 'record_support').seq;
  const outcomeSeq = current.history.find(h => h.action === 'record_outcome').seq;

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
    corrects_sequence: outcomeSeq, role: 'case_owner'
  }, { expected_version: current.version });
  assert.equal(silent.ok, false);
  assert.equal(silent.code, 'CORRECTION_NEEDS_REASON');

  /* And a correction cannot be used to move the case. */
  const moves = service.correct(id, {
    corrects_sequence: outcomeSeq, role: 'case_owner',
    reason: 'Trying to un-close the case', replacement: { state: 'draft' }
  }, { expected_version: current.version });
  assert.equal(moves.ok, false);
  assert.equal(moves.code, 'CORRECTION_CANNOT_MOVE_STATE');

  /* None of the three attempts left a mark on the stored record. */
  assert.equal(service.get(id).version, current.version);
  return `${again.code} | ${silent.code} | ${moves.code}`;
});

check('C16', 'One case cannot record a second delivery of the same support', () => {
  /* Built against the rule book directly, because the lifecycle would not
     normally offer the move twice. The case is wound back to "action_agreed"
     with no support and no outcome, but the log still carries the delivery
     already made on it - which is exactly the situation the guard is for. */
  const record = service.get('CASE-TEST-STAGES');
  assert.equal(schema.commercialEventCount(record), 1, 'the log should already carry one delivery');
  const doctored = schema.clone(record);
  doctored.state = 'action_agreed';
  doctored.support = null;
  doctored.outcome = null;
  doctored.next_action = 'Support owner to give the agreed support';
  doctored.next_update_due = '2026-10-15';
  assert.equal(schema.validate(doctored).ok, true, schema.validate(doctored).errors.join(' '));

  const attempt = schema.recordSupport(doctored, {
    support_eur: 400, net_terms_basis: 'net', delivered_on: '2026-11-01',
    what: 'A second support payment', by_role: 'support_owner'
  }, { at: FIXED_NOW, by: 'test-runner', role: 'support_owner' });
  assert.equal(attempt.ok, false);
  assert.equal(attempt.code, 'DUPLICATE_SUPPORT');
  assert.equal(schema.commercialEventCount(doctored), 1);
  return attempt.error;
});

check('C17', 'Volume migrated from another Isuzu product is not newly won business (CASE-05)', () => {
  /* A migration case: 40 units moved from a BVP part to the Genuine counterpart. */
  const migId = 'CASE-TEST-MIGRATION';
  const created = service.create(seed({ case_id: migId, part_number: 'SYNTH-GENUINE-A' }));
  let v = created.version;
  const migSubmitted = service.transition(migId, {
    action: 'submit', role: 'case_owner',
    next_action: 'Reviewer to take it', next_update_due: '2026-10-01'
  }, { expected_version: v }); v = migSubmitted.version;
  const migAssessing = service.transition(migId, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess',
    next_update_due: '2026-10-02'
  }, { expected_version: v }); v = migAssessing.version;
  const migAnswered = service.transition(migId, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Migration position issued.', issued_on: '2026-09-30', commitment: 'support' },
    next_action: 'Approver to decide', next_update_due: '2026-10-10'
  }, { expected_version: v }); v = migAnswered.version;
  const migProposed = service.proposeTerms(migId, {
    terms: terms({ quantity_after: 140 }), offered_by_role: 'case_owner',
    approval_route: 'Synthetic route.'
  }, { expected_version: v, role: 'case_owner' }); v = migProposed.version;
  const migApproved = service.transition(migId, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Migration accepted',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-MIG' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: v }); v = migApproved.version;
  const migDelivered = service.recordSupport(migId, {
    support_eur: 300, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Launch support for the migrated volume',
    action_identifier: 'ACT:MIGRATION-TEST-1'
  }, { expected_version: v, role: 'support_owner' });
  assert.equal(migDelivered.ok, true, migDelivered.error);
  const migOutcome = service.recordOutcome(migId, {
    what: '40 units now bought on the Genuine counterpart; the same trucks, the same demand',
    observed_on: '2026-11-30', quantity_after: 40, quantity_label: 'observed history',
    migration_from: 'SYNTH-PART-OLD', migration_to: 'SYNTH-GENUINE-A',
    counts_as_new_business: false
  }, { expected_version: migDelivered.version, role: 'case_owner' });
  assert.equal(migOutcome.ok, true, migOutcome.error);

  /* Link the migration to the case it came from. */
  const link = service.linkCases('CASE-TEST-STAGES', migId, 'migrates_to', {
    expected_versions: {
      'CASE-TEST-STAGES': service.get('CASE-TEST-STAGES').version,
      [migId]: service.get(migId).version
    }
  });
  assert.equal(link.ok, true, link.error);
  assert.equal(link.spec.counts_apart, false, 'a migration is not a separate commercial action');

  /* A genuinely new piece of business, so the rollup has both kinds. */
  const newId = 'CASE-TEST-NEW';
  const newCreated = service.create(seed({ case_id: newId, part_number: 'SYNTH-PART-H' }));
  let nv = newCreated.version;
  const newSubmitted = service.transition(newId, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take it',
    next_update_due: '2026-10-01'
  }, { expected_version: nv }); nv = newSubmitted.version;
  const newAssessing = service.transition(newId, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess', next_update_due: '2026-10-02'
  }, { expected_version: nv }); nv = newAssessing.version;
  const newAnswered = service.transition(newId, {
    action: 'issue_response', role: 'case_owner',
    response: { what: 'Position issued.', issued_on: '2026-09-30', commitment: 'support' },
    next_action: 'Approver to decide', next_update_due: '2026-10-10'
  }, { expected_version: nv }); nv = newAnswered.version;
  const newProposed = service.proposeTerms(newId, {
    terms: terms(), offered_by_role: 'case_owner', approval_route: 'Synthetic route.'
  }, { expected_version: nv, role: 'case_owner' }); nv = newProposed.version;
  const newApproved = service.transition(newId, {
    action: 'accept_proposal', role: 'approver', approval_note: 'Accepted',
    proposal_accept: { proposal_version: 1, approval_reference: 'SYNTH-APPROVAL-NEW' },
    next_action: 'Support owner to give the agreed support', next_update_due: '2026-10-15'
  }, { expected_version: nv }); nv = newApproved.version;
  const newDelivered = service.recordSupport(newId, {
    support_eur: 700, net_terms_basis: 'net', delivered_on: '2026-10-12',
    what: 'Launch support for a genuinely new part', action_identifier: 'ACT:NEW-TEST-1'
  }, { expected_version: nv, role: 'support_owner' });
  assert.equal(newDelivered.ok, true, newDelivered.error);
  const newOutcome = service.recordOutcome(newId, {
    what: '60 units billed that were not billed before', observed_on: '2026-11-30',
    quantity_after: 60, quantity_label: 'observed history', counts_as_new_business: true
  }, { expected_version: newDelivered.version, role: 'case_owner' });
  assert.equal(newOutcome.ok, true, newOutcome.error);

  /* Now roll the whole portfolio up conservatively. */
  const rollup = service.conservativeRollup([migId, newId], '2026-12-01');
  assert.equal(rollup.newly_won_units, 60,
    'only the genuinely new 60 units are newly won; the 40 migrated units are not');
  assert.equal(rollup.migrated_units_not_new_business, 40);
  assert.equal(rollup.support_total_eur, 1000, '300 + 700, each counted once');
  assert.equal(rollup.distinct_commercial_occasions, 2);
  const migratedRow = rollup.actions.find(a => a.action_identifier === 'ACT:MIGRATION-TEST-1');
  assert.equal(migratedRow.counted_as, 'migrated from another product');
  /* And there is still no single benefit figure. */
  assert.equal(rollup.total_benefit_eur, null);
  /* And an outcome that claims a migration is new business is refused outright. */
  const bogus = schema.recordOutcome(service.get(newId), {
    what: 'Migration claimed as new business', observed_on: '2026-12-01',
    migration_from: 'SYNTH-PART-OLD', counts_as_new_business: true, by_role: 'case_owner'
  }, { at: FIXED_NOW, by: 'test-runner', role: 'case_owner' });
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
  assert.equal(record.state, 'resolved');
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
  const approvalEntry = current.history.find(h => h.action === 'accept_proposal');
  const deliveryEntry = current.history.find(h => h.action === 'record_support');
  const outcomeEntry = current.history.find(h => h.action === 'record_outcome');

  /* As it stood at the approval: proposed and accepted, nothing delivered. */
  const atApproval = service.reopen(id, approvalEntry.seq);
  assert.equal(atApproval.version, approvalEntry.seq);
  assert.equal(atApproval.state, 'action_agreed');
  assert.equal(atApproval.support, null, 'at the approval nothing had been delivered');
  assert.equal(atApproval.outcome, null);
  assert.equal(atApproval.proposal.versions[0].terms.price_after, 95, 'the proposed inputs are preserved');
  assert.equal(atApproval.approval_note, 'Accepted as proposed');

  /* As it stood at the delivery: given, not yet measured. */
  const atDelivery = service.reopen(id, deliveryEntry.seq);
  assert.equal(atDelivery.state, 'action_agreed');
  assert.equal(atDelivery.support.support_eur, 500, 'the support as it stood before the correction');
  assert.equal(atDelivery.outcome, null);
  assert.equal(atDelivery.stage, 'agreed');

  /* And the latest, with the corrected support and the outcome. */
  const latest = service.reopen(id);
  assert.equal(latest.version, current.version);
  assert.equal(latest.state, 'resolved');
  assert.equal(latest.support.support_eur, 250, 'the corrected amount');
  assert.equal(latest.outcome.quantity_after, 120);
  assert.equal(latest.stage, 'closed');

  /* Asking for a version that does not exist is refused, not guessed at. */
  const beyond = service.reopen(id, current.version + 5);
  assert.equal(beyond.ok, false);
  assert.equal(beyond.code, 'NO_SUCH_VERSION');
  assert.equal(beyond.actual_version, undefined);

  assert.ok(outcomeEntry, 'the outcome entry should be in the log');
  return `at v${approvalEntry.seq}: ${atApproval.state} / support ${atApproval.support}; `
    + `at v${deliveryEntry.seq}: ${atDelivery.state} / support EUR ${atDelivery.support.support_eur}; `
    + `latest v${latest.version}: ${latest.state} / support EUR ${latest.support.support_eur}`;
});

check('C21', 'A field that looks like a credential is refused', () => {
  const current = service.get('CASE-TEST-STAGES');
  const withSecret = schema.clone(current);
  withSecret.review = { note: 'Looks fine', api_key: 'not-a-real-key' };
  const refused = service.saveRecord(withSecret, { expected_version: current.version });
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'SECRET_LIKE_FIELD');
  assert.match(refused.error, /api_key/);

  const inScenario = schema.clone(current);
  inScenario.scenario = Object.assign({}, current.scenario, { source_password: 'hunter2' });
  const alsoRefused = service.saveRecord(inScenario, { expected_version: current.version });
  assert.equal(alsoRefused.ok, false);
  assert.equal(alsoRefused.code, 'SECRET_LIKE_FIELD');
  return refused.error;
});

check('C22', 'An undeclared field cannot be stored on a case', () => {
  const current = service.get('CASE-TEST-STAGES');
  const withExtra = schema.clone(current);
  withExtra.commercial_score = 99;
  const refused = service.saveRecord(withExtra, { expected_version: current.version });
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
  assert.equal(service.get('CASE-TEST-STAGES').state, 'resolved',
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
  /* The claim this check has always made. The list it reads is the one the
     component enforces, which after this migration is the plan's target
     vocabulary - see the header for why the in-force list is built from
     CASE_STATES_TARGET rather than from CASE_STATES. */
  const unmapped = schema.CASE_STATES.filter(s => !schema.stageOf(s));
  assert.deepEqual(unmapped, [], 'these states have no stage: ' + unmapped.join(', '));
  assert.deepEqual(schema.CASE_STATES, (contracts.CASE_STATES_TARGET || []).slice(),
    'the enforcing vocabulary and the declared target have diverged');
  /* The four stages a reader must be able to tell apart under the new
     vocabulary: an answer, an agreed action, a payment and an outcome. The
     payment and the outcome are no longer states, so what is asserted here is
     that the four are four DISTINCT things a reader can be told apart. */
  const four = [
    schema.stageOf('response_issued'),
    schema.stageOf('action_agreed'),
    'support (recorded move)',
    'outcome (recorded move)'
  ];
  assert.equal(new Set(four).size, 4,
    'the answer, the agreed action, the payment and the outcome are not four distinct things');
  return `${schema.CASE_STATES.length} states in force mapped onto ${schema.STAGES.length} stages`;
});

check('C27', 'The store describes honestly what it is', () => {
  const described = service.describe();
  assert.equal(described.kind, 'files');
  assert.equal(described.durable, true);
  assert.equal(described.shared, false, 'a folder on one machine is not a shared service');
  assert.match(described.statement, /NOT a shared service/);
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
