#!/usr/bin/env node
/* ===========================================================================
   RUN-05 acceptance tests: Show due actions without automatically sending
   messages.

   How to run
     node --test tests/run_05_due_actions.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A due item identifies the unresolved obligation and opens the correct
         permitted case.
     E2  No email or external notification is sent during development or a
         test run.

   Synthetic fixtures only. Nothing is ever sent.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'due_actions.js'));

const AS_OF = '2026-10-06';

function seedBoard() {
  return mod.makeDueActionBoard();
}

test('RUN-05 E1: A due item identifies the unresolved obligation and opens the correct permitted case.', () => {
  const board = seedBoard();
  const items = [
    {
      case_id: 'SYN-DUE-A',
      obligation: 'Reviewer to answer the comparable quotation for SYN-DUE-A',
      responsible_person: 'Synthetic reviewer',
      next_update_due: '2026-10-01',
      waiting_since: '2026-09-20',
      permitted: true
    },
    {
      case_id: 'SYN-DUE-B',
      obligation: 'Owner to confirm volume for SYN-DUE-B',
      responsible_person: 'Synthetic owner',
      next_update_due: '2026-10-20',
      waiting_since: '2026-10-01',
      permitted: true
    },
    {
      case_id: 'SYN-DUE-X',
      obligation: 'Hidden obligation',
      responsible_person: 'Other org',
      next_update_due: '2026-09-01',
      waiting_since: '2026-08-01',
      permitted: false
    }
  ];
  const due = board.listDue(items, AS_OF);
  assert.equal(due.length, 2);
  assert.equal(due[0].case_id, 'SYN-DUE-A');
  assert.equal(due[0].overdue, true);
  assert.match(due[0].statement, /Unresolved obligation/);
  assert.equal(due[0].obligation, items[0].obligation);

  const cases = [
    { case_id: 'SYN-DUE-A', version: 3 },
    { case_id: 'SYN-DUE-B', version: 1 }
  ];
  const opened = board.openDueItem(due[0], cases);
  assert.equal(opened.ok, true, opened.error);
  assert.equal(opened.opened_case_id, 'SYN-DUE-A');
  assert.equal(opened.obligation, items[0].obligation);
  assert.equal(opened.version, 3);

  const refused = board.openDueItem(items[2], cases);
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'NOT_PERMITTED');

  const moved = board.reassign(items[0], 'Synthetic deputy', AS_OF);
  assert.equal(moved.waiting_age_reset, false);
  assert.equal(moved.waiting_days_before, moved.waiting_days_after);
  assert.equal(moved.item.waiting_since, '2026-09-20');
});

test('RUN-05 E2: No email or external notification is sent during development or a test run.', () => {
  const board = seedBoard();
  const draft = board.prepareDraftSummary({
    case_id: 'SYN-DUE-A',
    obligation: 'Reviewer to answer the comparable quotation for SYN-DUE-A'
  }, 'internal');
  assert.equal(draft.status, 'draft');
  assert.equal(draft.sent, false);
  assert.equal(draft.case_link, 'case://SYN-DUE-A');

  const attempt = board.sendExternalNotification({
    channel: 'email',
    case_id: 'SYN-DUE-A',
    at: '2026-10-06T12:00:00Z',
    body: draft.body
  });
  assert.equal(attempt.sent, false);
  assert.equal(attempt.blocked, true);
  assert.equal(attempt.code, 'SEND_DISABLED');
  assert.equal(board.sentCount(), 0);
  assert.equal(board.outboundAttempts().length, 1);
  assert.equal(board.outboundAttempts()[0].sent, false);
});
