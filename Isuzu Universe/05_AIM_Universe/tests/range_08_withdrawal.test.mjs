#!/usr/bin/env node
/* RANGE-08: withdraw a relationship without rewriting history. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));

const FIX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/range_08_withdrawal.json'), 'utf8'));

test('RANGE-08 E1: withdrawing a pairing flags affected active cases but preserves the original saved evidence', () => {
  assert.equal(typeof evidence.makeRangeRelationshipLedger, 'function');
  assert.equal(typeof evidence.withdrawRangeRelationship, 'function',
    'AIMEvidence.withdrawRangeRelationship is missing');
  assert.equal(typeof evidence.rangeWithdrawalImpact, 'function',
    'AIMEvidence.rangeWithdrawalImpact is missing');

  const ledger = evidence.makeRangeRelationshipLedger();
  const recorded = ledger.record({
    type: 'pairing',
    part_a: FIX.pairing.part_a,
    part_b: FIX.pairing.part_b,
    source: FIX.pairing.source,
    source_version: FIX.pairing.source_version,
    authority: 'approved',
    conditions: FIX.pairing.conditions
  });
  assert.equal(recorded.ok, true);
  const before = JSON.parse(JSON.stringify(recorded.relationship));

  const withdrawn = evidence.withdrawRangeRelationship(ledger, recorded.relationship.relationship_id, {
    reason: FIX.withdrawal_reason,
    withdrawn_by: 'synthetic technical authority',
    withdrawn_at: '2026-10-06'
  });
  assert.equal(withdrawn.ok, true);
  assert.equal(withdrawn.relationship.authority, 'withdrawn');
  assert.ok(withdrawn.relationship.saved_evidence, 'original saved evidence missing after withdrawal');
  assert.equal(withdrawn.relationship.saved_evidence.authority, 'approved');
  assert.equal(withdrawn.relationship.saved_evidence.part_a, before.part_a);
  assert.equal(withdrawn.relationship.saved_evidence.part_b, before.part_b);
  assert.equal(withdrawn.relationship.saved_evidence.source, before.source);
  assert.ok(withdrawn.relationship.version > before.version);

  const impact = evidence.rangeWithdrawalImpact(FIX.cases, withdrawn.relationship);
  assert.ok(Array.isArray(impact.affected_case_ids));
  assert.ok(impact.affected_case_ids.includes('IMOTORS-CABIN'),
    'active case that relied on the pairing was not flagged');
  assert.equal(impact.affected_case_ids.includes('ITUK-PADS'), false,
    'unrelated case was incorrectly flagged');
  assert.equal(impact.requires_fresh_review, true);
  assert.match(impact.statement, /fresh review|withdrawn/i);

  const listed = ledger.listForPair(FIX.pairing.part_a, FIX.pairing.part_b);
  assert.equal(listed.length, 1);
  assert.equal(listed[0].authority, 'withdrawn');
  assert.equal(listed[0].saved_evidence.authority, 'approved');
});

test('RANGE-08 E2: new scenarios cannot silently reuse the withdrawn application approval', () => {
  assert.equal(typeof evidence.canReuseApplicationApproval, 'function',
    'AIMEvidence.canReuseApplicationApproval is missing');

  const ledger = evidence.makeRangeRelationshipLedger();
  const recorded = ledger.record({
    type: 'pairing',
    part_a: FIX.pairing.part_a,
    part_b: FIX.pairing.part_b,
    source: FIX.pairing.source,
    source_version: FIX.pairing.source_version,
    authority: 'approved',
    conditions: FIX.pairing.conditions
  });
  const withdrawn = evidence.withdrawRangeRelationship(ledger, recorded.relationship.relationship_id, {
    reason: FIX.withdrawal_reason
  });
  assert.equal(withdrawn.ok, true);

  const reuse = evidence.canReuseApplicationApproval(withdrawn.relationship);
  assert.equal(reuse.allowed, false,
    'withdrawn application approval was silently reusable');
  assert.match(reuse.statement, /cannot reuse|withdrawn|fresh review/i);

  const caseWithWithdrawn = {
    id: 'IMOTORS-CABIN',
    parts: FIX.cases[0].parts,
    packEvidence: {
      relationships: [{
        part_number_a: FIX.pairing.part_a,
        part_number_b: FIX.pairing.part_b,
        relationship_type: 'catalogue pairing',
        validation_status: 'withdrawn',
        authority: 'withdrawn',
        source_document: FIX.pairing.source
      }]
    }
  };
  const view = evidence.exactRangeComparison(caseWithWithdrawn, { audience: 'internal' });
  assert.notEqual(String(view.relationship_authority || '').toLowerCase(), 'approved pairing',
    'exact comparison reused a withdrawn pairing as approved');
  assert.match(String(view.relationship_authority || view.statement || ''), /withdrawn|not approved|counterpart/i);

  const role = evidence.rangeCommercialRole(withdrawn.relationship, {
    price_present: true, cost_present: true
  });
  assert.equal(role.role, 'withdrawn',
    'rangeCommercialRole promoted a withdrawn relationship off withdrawn');
  assert.equal(role.interchangeable, false);
});
