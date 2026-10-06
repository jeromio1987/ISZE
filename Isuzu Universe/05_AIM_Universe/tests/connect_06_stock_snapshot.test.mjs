#!/usr/bin/env node
/* ===========================================================================
   CONNECT-06 acceptance tests: Accept a small optional stock snapshot for a
   defined case.

   How to run
     node --test tests/connect_06_stock_snapshot.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Unknown reserved stock cannot become available stock through a default zero.
     E2  Declining a stock contribution does not close an unrelated commercial or
         application request.

   Synthetic fixtures only. No real stock file.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'stock_snapshot.js'));

const CASE0 = {
  case_id: 'SYN-CASE-STOCK-01',
  part_number: 'SYN-PN-STOCK',
  commercial_requests: [
    { request_id: 'CR-1', kind: 'commercial', status: 'open', subject: 'Synthetic price review' }
  ],
  application_requests: [
    { request_id: 'AR-1', kind: 'application', status: 'open', subject: 'Synthetic BVP application check' }
  ],
  stock_snapshots: []
};

test('CONNECT-06 E1: Unknown reserved stock cannot become available stock through a default zero.', () => {
  const accepted = mod.acceptStockSnapshot(CASE0, {
    part_number: 'SYN-PN-STOCK',
    as_of: '2026-10-06',
    on_hand: 12,
    reserved: 'unknown',
    source: 'synthetic_stock_observation'
  }, { snapshot_id: 'SS-1' });

  assert.equal(accepted.ok, true);
  const snap = accepted.snapshot;
  assert.equal(snap.on_hand, 12);
  assert.equal(snap.reserved, null);
  assert.equal(snap.reserved_known, false);
  assert.equal(snap.available_known, false);
  assert.equal(snap.available, null);
  assert.notEqual(snap.available, 12);
  assert.notEqual(snap.available, 0);
  assert.ok(
    (snap.statement || '').toLowerCase().includes('unknown') ||
      (snap.statement || '').toLowerCase().includes('not derived'),
    'statement must refuse deriving available from a default-zero reserved'
  );

  const missing = mod.reviewWithoutSnapshot({ case_id: 'SYN-CASE-STOCK-02', stock_snapshots: [] });
  assert.equal(missing.ok, true);
  assert.equal(missing.usable, true);
  assert.equal(missing.has_snapshot, false);
});

test('CONNECT-06 E2: Declining a stock contribution does not close an unrelated commercial or application request.', () => {
  const declined = mod.declineStockContribution(CASE0, {
    declined_at: '2026-10-06T12:00:00Z',
    declined_by: 'synthetic_analyst',
    reason: 'No stock file offered for this case'
  });

  assert.equal(declined.ok, true);
  assert.equal(declined.case_record.stock_contribution.status, 'declined');
  assert.equal(declined.closed_unrelated_request, false);
  assert.equal(declined.commercial_open_before, 1);
  assert.equal(declined.commercial_open_after, 1);
  assert.equal(declined.application_open_before, 1);
  assert.equal(declined.application_open_after, 1);

  const commercial = declined.case_record.commercial_requests;
  const application = declined.case_record.application_requests;
  assert.equal(commercial[0].status, 'open');
  assert.equal(application[0].status, 'open');
  assert.notEqual(commercial[0].status, 'closed');
  assert.notEqual(application[0].status, 'closed');
});
