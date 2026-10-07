#!/usr/bin/env node
/* ===========================================================================
   CONNECT-07 acceptance tests: Connect the existing tender feed to an owned
   investigation.

   How to run
     node --test tests/connect_07_tender_investigation.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  An expired/cancelled notice cannot be shown as a current actionable
         deadline.
     E2  An award cannot automatically create billing, gross profit or a won
         parts quotation.

   Synthetic tender-feed shaped fixtures only. The live feed
   ISZE/01_data/14_dashboards/tender_data.json is never written. Notice value
   is never translated into Isuzu parts revenue.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'tender_investigation.js'));

const CASE0 = {
  case_id: 'SYN-CASE-TENDER-01',
  part_number: 'SYN-PN-TENDER',
  tender_investigations: []
};

const SYN_EXPIRED = {
  opportunity_id: 'SYN-TEND-EXPIRED-01',
  title: 'Synthetic expired municipal workshop notice',
  buyer: 'Synthetic Buyer Council',
  country: 'Syntheticland',
  deadline_date: '2026-01-15',
  published_latest: '2025-12-01',
  lifecycle: 'expired',
  notice_type: 'procedure',
  value_amount: 100000,
  currency: 'EUR',
  source: 'synthetic_tender_feed',
  url: 'https://example.test/synthetic-expired'
};

const SYN_CANCELLED = {
  opportunity_id: 'SYN-TEND-CANCEL-01',
  title: 'Synthetic cancelled framework notice',
  buyer: 'Synthetic Agency',
  country: 'Syntheticland',
  deadline_date: '2026-12-01',
  published_latest: '2026-06-01',
  lifecycle: 'cancelled',
  notice_type: 'procedure',
  value_amount: 250000,
  currency: 'EUR',
  source: 'synthetic_tender_feed'
};

const SYN_OPEN = {
  opportunity_id: 'SYN-TEND-OPEN-01',
  title: 'Synthetic open parts-support notice',
  buyer: 'Synthetic Fleet Owner',
  country: 'Syntheticland',
  deadline_date: '2026-11-30',
  published_latest: '2026-09-01',
  lifecycle: 'competition',
  notice_type: 'procedure',
  value_amount: 80000,
  currency: 'EUR',
  source: 'synthetic_tender_feed'
};

const SYN_AWARD = {
  opportunity_id: 'SYN-TEND-AWARD-01',
  title: 'Synthetic award notice',
  buyer: 'Synthetic Award Body',
  country: 'Syntheticland',
  deadline_date: '2026-05-01',
  published_latest: '2026-06-15',
  lifecycle: 'result',
  notice_type: 'award',
  outcome: 'awarded',
  value_amount: 500000,
  currency: 'EUR',
  source: 'synthetic_tender_feed'
};

test('CONNECT-07 E1: An expired/cancelled notice cannot be shown as a current actionable deadline.', () => {
  const expiredView = mod.actionableDeadline(SYN_EXPIRED, { as_of: '2026-10-06' });
  assert.equal(expiredView.ok, true);
  assert.equal(expiredView.actionable, false);
  assert.ok(
    /expired|cancelled|canceled/i.test(expiredView.statement || ''),
    'statement must name expired/cancelled'
  );

  const cancelledView = mod.actionableDeadline(SYN_CANCELLED, { as_of: '2026-10-06' });
  assert.equal(cancelledView.ok, true);
  assert.equal(cancelledView.actionable, false);

  const openView = mod.actionableDeadline(SYN_OPEN, { as_of: '2026-10-06' });
  assert.equal(openView.ok, true);
  assert.equal(openView.actionable, true);
  assert.equal(openView.deadline_date, '2026-11-30');

  const attached = mod.attachTenderInvestigation(CASE0, SYN_EXPIRED, {
    owner: 'synthetic_analyst',
    state: 'reviewed',
    attached_at: '2026-10-06T14:00:00Z'
  });
  assert.equal(attached.ok, true);
  assert.equal(attached.investigation.actionable_deadline, false);
  assert.equal(attached.investigation.notice.opportunity_id, 'SYN-TEND-EXPIRED-01');
  assert.equal(attached.investigation.notice.value_as_parts_revenue, null);
  assert.notEqual(
    attached.investigation.notice.value_amount,
    attached.investigation.isuzu_parts_revenue_eur
  );
  assert.equal(attached.investigation.isuzu_parts_revenue_eur, null);
});

test('CONNECT-07 E2: An award cannot automatically create billing, gross profit or a won parts quotation.', () => {
  const attached = mod.attachTenderInvestigation(CASE0, SYN_AWARD, {
    owner: 'synthetic_analyst',
    state: 'known_outcome',
    attached_at: '2026-10-06T15:00:00Z',
    known_outcome: 'awarded'
  });
  assert.equal(attached.ok, true);

  const effects = mod.awardFinancialEffects(attached.investigation);
  assert.equal(effects.ok, true);
  assert.equal(effects.auto_created, false);
  assert.equal(effects.billing, null);
  assert.equal(effects.gross_profit, null);
  assert.equal(effects.won_parts_quotation, null);
  assert.equal(effects.isuzu_parts_revenue_eur, null);
  assert.ok(
    /does not|cannot|not automatically/i.test(effects.statement || ''),
    'statement must refuse automatic financial creation'
  );

  // Notice value must not become parts revenue on the case either.
  assert.equal(attached.case_record.isuzu_parts_revenue_eur, undefined);
  assert.equal(attached.investigation.isuzu_parts_revenue_eur, null);
  assert.ok(attached.investigation.notice.value_amount === 500000);
  assert.notEqual(attached.investigation.notice.value_amount, effects.billing);
});
