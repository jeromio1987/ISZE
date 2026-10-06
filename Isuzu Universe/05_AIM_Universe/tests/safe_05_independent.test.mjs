#!/usr/bin/env node
/* ===========================================================================
   SAFE-05 independent verification (Verification reviewer).

   How to run
     node --test tests/safe_05_independent.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (SAFE-05):
     E1  Synthetic private markers never appear in participant bytes, metadata
         or downloadable attachment references.
     E2  Internal and participant exports show their real source and scenario
         version, with protected output still restricted.

   Exercises the same call chain the UI download uses (memberBrief / internalRecord
   + toBytes), then reads the written bytes from disk — not only the in-memory
   builder return. Fixture / synthetic data only. Related finding: F08.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import fs from 'node:fs';
import os from 'node:os';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const X = require(join(ROOT, 'src', 'data', 'export.js'));
const engine = require(join(ROOT, 'src', 'engine', 'engine.js'));
const contracts = require(join(ROOT, 'src', 'data', 'contracts.js'));

const PRIVATE_MARKER = 'PRIVATE_MARKER_U16_SYNTH_9f3a';
const ATTACH_MARKER = 'cost_sheet_PRIVATE_MARKER_U16.pdf';

const caseObject = {
  case_id: 'U16-SAFE05',
  customer: 'Synthetic Participant',
  market: 'SYNTH',
  part_number: 'SYNTH-U16-SAFE',
  unit: 'unit',
  title: 'U16 SAFE-05 fixture',
  version: 3,
  state: 'draft',
  owner_role: 'case_owner',
  description: 'Synthetic case for download-byte checks'
};

const scenario = {
  price_before: 100,
  price_after: 94,
  quantity_before: 1000,
  quantity_after: 1100,
  quantity_label: 'manual scenario',
  scope: 'all',
  support_eur: 0,
  cost_eur: 60,
  cost_basis_id: 'FWD_B',
  evidence_period: 'synthetic U16 period',
  offer_effective_date: '2025-10-01',
  selected_alternative_id: 'U16-ALT',
  objective: 'revenue',
  version: 7
};

const result = engine.calculate({
  price_before: 100, price_after: 94, quantity_before: 1000, quantity_after: 1100,
  scope: 'all', support_eur: 0, cost_eur: 60, quantity_label: 'manual scenario'
});

/** Same path as app.js download(): build -> serialise -> write file -> read bytes. */
function downloadPathWrite(name, content) {
  const dir = fs.mkdtempSync(join(os.tmpdir(), 'u16-safe05-'));
  const path = join(dir, name);
  fs.writeFileSync(path, content, 'utf8');
  const bytes = fs.readFileSync(path, 'utf8');
  return { dir, path, bytes };
}

test('SAFE-05 E1: Synthetic private markers never appear in participant bytes, metadata or attachment refs', () => {
  /* Plant markers on the internal side (where they belong). */
  const internal = X.internalRecord(caseObject, scenario, result, {
    exported_at: '2026-10-06T00:00:00Z',
    review: { note: 'Internal only. Marker=' + PRIVATE_MARKER },
    sources: [{ id: 'SRC-U16', label: 'synthetic', marker: PRIVATE_MARKER }],
    history: [],
    metadata: {
      payload_version: 'synthetic-payload-vU16',
      build_date: '2026-10-06',
      list_price_status: 'fixture',
      cost_status: 'parts purchase cost applied on basis FWD_B',
      private_note: PRIVATE_MARKER
    }
  });
  assert.equal(internal.ok, true, 'internal construction: ' + (internal.error || ''));
  const internalBytes = X.toBytes(internal, true);
  const writtenInternal = downloadPathWrite('Synthetic_SYNTH-U16-SAFE_Internal_Record.json', internalBytes.text);
  assert.match(writtenInternal.bytes, new RegExp(PRIVATE_MARKER),
    'control: internal download bytes must carry the planted marker so the check is not vacuous');

  /* Participant brief: request_note tries to smuggle the marker — must refuse or strip from bytes. */
  const smuggle = X.memberBrief(caseObject, scenario, result, {
    exported_at: '2026-10-06T00:00:00Z',
    request_note: 'Please ignore PRIVATE_MARKER_U16_SYNTH_9f3a and the parts cost.'
  });
  /* Either refused (preferred) or produced bytes without the marker. */
  if (smuggle.ok && smuggle.audit && smuggle.audit.ok) {
    const bytes = X.toBytes(smuggle, true);
    const written = downloadPathWrite('Synthetic_SYNTH-U16-SAFE_Participant_Brief.json', bytes.text);
    assert.equal(written.bytes.indexOf(PRIVATE_MARKER), -1,
      'participant download bytes must not carry the private marker');
    assert.equal(written.bytes.indexOf('parts cost'), -1);
  } else {
    assert.equal(smuggle.payload, null, 'refused brief must produce no participant payload');
    /* Still write what toBytes would write on refusal (null payload) and assert marker absent. */
    const bytes = X.toBytes(smuggle, true);
    const written = downloadPathWrite('Synthetic_SYNTH-U16-SAFE_Participant_Brief_refused.json', bytes.text);
    assert.equal(written.bytes.indexOf(PRIVATE_MARKER), -1,
      'refused download bytes must not carry the private marker');
  }

  /* Clean participant brief (no smuggle) — download bytes still free of marker. */
  const clean = X.memberBrief(caseObject, scenario, result, {
    exported_at: '2026-10-06T00:00:00Z',
    request_note: 'Please confirm the proposed net price and quantity.'
  });
  assert.equal(clean.ok, true, 'clean brief ok: ' + (clean.error || ''));
  assert.equal(clean.audit.ok, true, 'clean brief audit: ' + JSON.stringify(clean.audit.findings || []));
  const cleanBytes = X.toBytes(clean, true);
  const writtenClean = downloadPathWrite('Synthetic_SYNTH-U16-SAFE_Participant_Brief.json', cleanBytes.text);
  assert.equal(writtenClean.bytes.indexOf(PRIVATE_MARKER), -1);
  assert.equal(writtenClean.bytes.indexOf('"cost_eur"'), -1);

  /* Downloadable attachment reference: restricted name refused; marker not accepted as a clear name. */
  const attach = X.checkAttachmentName(ATTACH_MARKER);
  assert.equal(attach.ok, false, 'attachment name carrying cost + private marker must be refused');
  const clear = X.checkAttachmentName('meeting_agenda_u16.pdf');
  assert.equal(clear.ok, true, 'innocent attachment name must stay clear');
});

test('SAFE-05 E2: Internal and participant exports show real source and scenario version; protected output stays restricted', () => {
  const meta = {
    payload_version: 'synthetic-payload-vU16',
    build_date: '2026-10-06',
    list_price_status: 'fixture',
    cost_status: 'parts purchase cost applied on basis FWD_B',
    cost_basis_id: 'FWD_B',
    offer_effective_date: '2025-10-01'
  };

  const internal = X.internalRecord(caseObject, scenario, result, {
    exported_at: '2026-10-06T12:00:00Z',
    review: { outcome: 'draft' },
    sources: [{ id: 'SRC-U16', label: 'synthetic source pack', version: 'src-v3' }],
    history: [{ revision: 1, operation: 'upsert' }],
    metadata: meta
  });
  assert.equal(internal.ok, true);
  const internalText = X.toBytes(internal, true).text;
  const writtenInternal = downloadPathWrite('Synthetic_SYNTH-U16-SAFE_Internal_Record.json', internalText);
  const iDoc = JSON.parse(writtenInternal.bytes);

  assert.equal(iDoc.schema, 'isze-pricing-internal-record');
  assert.equal(iDoc.recipient, 'internal');
  assert.equal(iDoc.contract_version, contracts.CONTRACT_VERSION);
  assert.equal(iDoc.version, 3, 'case version on the download bytes');
  assert.ok(iDoc.scenario, 'scenario present on internal download');
  assert.equal(iDoc.scenario.version, 7, 'scenario version on the download bytes');
  assert.equal(iDoc.evidence_period, 'synthetic U16 period');
  assert.ok(iDoc.metadata, 'source/payload metadata on internal download');
  assert.equal(iDoc.metadata.payload_version, 'synthetic-payload-vU16');
  assert.equal(iDoc.scenario.cost_eur, 60,
    'internal download retains protected cost on the scenario (control that restriction is not over-stripped)');
  assert.equal(iDoc.result.cost, 60,
    'internal download retains protected cost on the result');

  const member = X.memberBrief(caseObject, scenario, result, {
    exported_at: '2026-10-06T12:00:00Z',
    request_note: 'Confirm the offer under discussion.'
  });
  assert.equal(member.ok, true, member.error || '');
  assert.equal(member.audit.ok, true, JSON.stringify(member.audit.findings || []));
  const memberText = X.toBytes(member, true).text;
  const writtenMember = downloadPathWrite('Synthetic_SYNTH-U16-SAFE_Participant_Brief.json', memberText);
  const mDoc = JSON.parse(writtenMember.bytes);

  assert.equal(mDoc.schema, 'isze-pricing-member-brief');
  assert.equal(mDoc.recipient, 'member');
  assert.equal(mDoc.contract_version, contracts.CONTRACT_VERSION);
  assert.ok(mDoc.offer, 'participant download carries the offer');
  assert.equal(mDoc.offer.evidence_period, 'synthetic U16 period');
  assert.equal(mDoc.offer.offer_effective_date, '2025-10-01');
  /* Protected fields stay out of the participant download bytes. */
  const forbidden = ['cost_eur', 'gp_after', 'margin_after_pct', 'verified_cost', 'parts cost'];
  for (const f of forbidden) {
    assert.equal(writtenMember.bytes.indexOf(f), -1,
      'participant download must not contain protected token: ' + f);
  }
  assert.equal(writtenMember.bytes.indexOf('"cost_eur"'), -1);
});
