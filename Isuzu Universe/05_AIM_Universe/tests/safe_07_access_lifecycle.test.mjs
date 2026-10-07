#!/usr/bin/env node
/* ===========================================================================
   SAFE-07 acceptance tests: Implement role changes, departure and record-use
   decisions.

   How to run
     node --test tests/safe_07_access_lifecycle.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Revoked users cannot retrieve protected records through an old link or
         active session beyond the accepted policy.
     E2  Stopping an optional feed does not silently delete unrelated permitted
         historical responses.

   Synthetic fixtures only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const mod = require(join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'data', 'access_lifecycle.js'));

const FIXED = '2026-10-06T16:00:00.000Z';

test('SAFE-07 E1: Revoked users cannot retrieve protected records through an old link or active session beyond the accepted policy.', () => {
  const life = mod.makeAccessLifecycle({ now: () => FIXED });
  life.registerUser({ subject: 'synth-user-1', role: 'viewer', tenant: 'ORG-ALPHA' });
  const sess = life.openSession('synth-user-1');
  assert.equal(sess.ok, true);
  const link = life.issueLink('synth-user-1', 'SYN-RECORD-1');
  assert.equal(link.ok, true);

  const before = life.retrieveThroughSession(sess.session.session_id, 'SYN-RECORD-1');
  assert.equal(before.ok, true);
  const beforeLink = life.retrieveThroughLink(link.link.link_id);
  assert.equal(beforeLink.ok, true);

  const revoked = life.revokeUser('synth-user-1', {
    retention_note: 'Owner policy applies; no universal retention period is invented here.'
  });
  assert.equal(revoked.ok, true);
  assert.equal(revoked.policy.downloaded_copies_remotely_recallable, false);
  assert.match(revoked.policy.statement, /not claimed to be remotely recallable/i);

  const afterSess = life.retrieveThroughSession(sess.session.session_id, 'SYN-RECORD-1');
  assert.equal(afterSess.ok, false);
  assert.ok(['SESSION_REVOKED', 'USER_REVOKED'].includes(afterSess.code));

  const afterLink = life.retrieveThroughLink(link.link.link_id);
  assert.equal(afterLink.ok, false);
  assert.ok(['LINK_REVOKED', 'USER_REVOKED'].includes(afterLink.code));
});

test('SAFE-07 E2: Stopping an optional feed does not silently delete unrelated permitted historical responses.', () => {
  const life = mod.makeAccessLifecycle({ now: () => FIXED });
  life.registerUser({ subject: 'synth-user-2', role: 'viewer', tenant: 'ORG-ALPHA' });
  life.startOptionalFeed('FEED-OPT-1', 'synth-user-2');
  life.recordHistoricalResponse({
    response_id: 'RESP-FEED-1',
    feed_id: 'FEED-OPT-1',
    subject: 'synth-user-2',
    body: 'Synthetic feed response',
    permitted: true
  });
  life.recordHistoricalResponse({
    response_id: 'RESP-UNRELATED-1',
    feed_id: null,
    subject: 'synth-user-2',
    body: 'Synthetic unrelated permitted historical response',
    permitted: true
  });

  const stopped = life.stopOptionalFeed('FEED-OPT-1');
  assert.equal(stopped.ok, true);
  assert.equal(stopped.deleted_unrelated_historical_responses, false);
  assert.equal(stopped.historical_responses_retained, 2);
  assert.ok(stopped.retained.some((r) => r.response_id === 'RESP-UNRELATED-1'));
  assert.ok(stopped.retained.some((r) => r.response_id === 'RESP-FEED-1'));
});