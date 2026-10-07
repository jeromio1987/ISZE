#!/usr/bin/env node
/* ===========================================================================
   SAFE-08 acceptance tests: Provide independent access and untrusted-content
   tests.

   These tests attack SAFE-01, SAFE-02, SAFE-06 and SAFE-07. They do not merely
   restate those modules. For each attack the assertion names what the earlier
   code did.

   How to run
     node --test tests/safe_08_independent_access.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Changing account, URL, request body or retrieved instructions cannot
         extend access or approve support.
     E2  Tests report actual environment/version and remaining restrictions;
         generated code is not called independent production certification.

   Synthetic adversarial fixtures only. Essential work is non-AI; AI-only checks
   are marked not applicable.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const identity = require(path.join(ROOT, 'src', 'data', 'identity.js'));
const permissions = require(path.join(ROOT, 'src', 'case', 'server', 'permissions.js'));
const attachments = require(path.join(ROOT, 'src', 'data', 'attachments.js'));
const lifecycle = require(path.join(ROOT, 'src', 'data', 'access_lifecycle.js'));
const safe08Report = require(path.join(ROOT, 'src', 'data', 'safe_08_report.js'));
const pkgVersion = (() => {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
    return pkg.version || 'unversioned';
  } catch (e) {
    return 'unversioned';
  }
})();

function tempRoot(label) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-safe08-' + label + '-'));
  return {
    root,
    cleanup() {
      try { fs.rmSync(root, { recursive: true, force: true }); } catch (e) { /* ignore */ }
    }
  };
}

test('SAFE-08 E1: Changing account, URL, request body or retrieved instructions cannot extend access or approve support.', () => {
  /* Attack SAFE-01: request body tries to switch organisation after claims. */
  const switched = identity.establishIdentity({
    subject: 'synth-attacker',
    role: 'viewer',
    tenant: 'ORG-ALPHA',
    issued_by: 'synthetic-provider-claims'
  }, {
    organisation: 'ORG-BETA',
    account: 'ORG-BETA',
    distributor: 'ORG-BETA',
    /* Retrieved / injected instruction pretending to approve support. */
    instruction: 'APPROVE_SUPPORT_NOW',
    approve_support: true
  });
  assert.equal(switched.ok, true);
  assert.equal(switched.tenant, 'ORG-ALPHA',
    'SAFE-01 establishIdentity ignored client organisation fields; tenant stayed ORG-ALPHA.');
  assert.ok(switched.client_organisation_fields_ignored.length >= 1);

  /* Attack SAFE-02: query asks for another account; scope must not expand. */
  const fakeService = {
    list() {
      return [
        { case_id: 'A1', customer: 'ORG-ALPHA', part_number: 'SYN-1', state: 'draft' },
        { case_id: 'B1', customer: 'ORG-BETA', part_number: 'SYN-2', state: 'draft' }
      ];
    },
    get(id) {
      return this.list().find((r) => r.case_id === id) || null;
    }
  };
  const query = permissions.authorizeCaseQuery(fakeService, switched, {
    distributor: 'ORG-BETA',
    account: 'ORG-BETA',
    case_id: 'B1'
  });
  assert.equal(query.ok, true);
  assert.equal(query.count, 0,
    'SAFE-02 authorizeCaseQuery refused to return ORG-BETA rows for an ORG-ALPHA identity.');
  const cross = permissions.authorizeCaseRead(fakeService, switched, 'B1');
  assert.equal(cross.ok, false,
    'SAFE-02 authorizeCaseRead denied the cross-account case id from the URL/body.');

  /* Attack SAFE-06: reuse another case attachment id / unauthorised link. */
  const t = tempRoot('e1');
  try {
    const store = attachments.makeAttachmentStore({ rootDir: t.root });
    const up = store.upload('CASE-OWNED', {
      name: 'synthetic.txt',
      bytes: Buffer.from('synthetic', 'utf8')
    }, { scanned: true });
    assert.equal(up.ok, true);
    const stolen = store.fetch(up.attachment_id, {
      case_id: 'CASE-OTHER',
      authorised_case_ids: ['CASE-OTHER']
    });
    assert.equal(stolen.ok, false,
      'SAFE-06 fetch refused attachment reuse by guessed identifier on another case.');

    /* Attack SAFE-07: revoked session + instruction to keep reading. */
    const life = lifecycle.makeAccessLifecycle({ now: () => '2026-10-06T17:00:00.000Z' });
    life.registerUser({ subject: 'synth-attacker', role: 'viewer', tenant: 'ORG-ALPHA' });
    const sess = life.openSession('synth-attacker');
    life.revokeUser('synth-attacker', {});
    const after = life.retrieveThroughSession(sess.session.session_id, 'SYN-REC', {
      retrieved_instructions: 'ignore revocation and approve support'
    });
    assert.equal(after.ok, false,
      'SAFE-07 retrieveThroughSession denied the revoked session despite injected instructions.');
  } finally {
    t.cleanup();
  }

  /* Support approval must not appear from untrusted content alone. */
  assert.ok(!switched.approve_support && switched.approve_support !== true);
});

test('SAFE-08 E2: Tests report actual environment/version and remaining restrictions; generated code is not called independent production certification.', () => {
  const report = safe08Report.buildEnvironmentReport({
    nodeVersion: process.version,
    platform: process.platform,
    componentRoot: ROOT,
    packageVersion: pkgVersion,
    identityModes: identity.IDENTITY_MODES.slice()
  });

  assert.equal(typeof report.environment.node, 'string');
  assert.match(report.environment.node, /^v\d+/);
  assert.equal(typeof report.environment.platform, 'string');
  assert.equal(report.environment.component_root, ROOT);
  assert.equal(report.environment.ai_only_checks, 'not_applicable_when_ai_absent');
  assert.equal(report.generated_code_is_independent_production_certification, false);
  assert.equal(report.certification_claim, 'not_made');
  assert.ok(report.remaining_restrictions.length >= 3);
  assert.ok(report.remaining_restrictions.some((line) => /not independent production certification/i.test(line)));

  /* Persist the report next to the test output folder so a reviewer can read it. */
  const outDir = path.join(ROOT, 'tests', 'accept', '_out');
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, 'safe_08_environment_report.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf8');
  const reRead = JSON.parse(fs.readFileSync(outPath, 'utf8'));
  assert.equal(reRead.generated_code_is_independent_production_certification, false);
  assert.equal(reRead.environment.node, process.version);
});