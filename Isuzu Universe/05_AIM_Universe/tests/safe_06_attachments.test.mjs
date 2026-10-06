#!/usr/bin/env node
/* ===========================================================================
   SAFE-06 acceptance tests: Protect attachments throughout upload, storage
   and access.

   How to run
     node --test tests/safe_06_attachments.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A case attachment cannot be fetched through an unauthorised direct link
         or reused in another case by guessing its identifier.
     E2  Disallowed or unscanned files remain unavailable for wider use; failure
         does not erase the saved case.

   Synthetic files only.
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
const attachments = require(path.join(ROOT, 'src', 'data', 'attachments.js'));

function tempRoot(label) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-safe06-' + label + '-'));
  return {
    root,
    cleanup() {
      try { fs.rmSync(root, { recursive: true, force: true }); } catch (e) { /* ignore */ }
    }
  };
}

test('SAFE-06 E1: A case attachment cannot be fetched through an unauthorised direct link or reused in another case by guessing its identifier.', () => {
  const t = tempRoot('e1');
  try {
    const store = attachments.makeAttachmentStore({ rootDir: t.root });
    const caseA = { case_id: 'SYN-CASE-ATT-A' };
    const up = store.upload('SYN-CASE-ATT-A', {
      name: 'synthetic-note.txt',
      bytes: Buffer.from('synthetic attachment body', 'utf8')
    }, { scanned: true, caseRecord: caseA });
    assert.equal(up.ok, true);
    assert.equal(up.case_id, 'SYN-CASE-ATT-A');

    const unauth = store.fetch(up.attachment_id, {});
    assert.equal(unauth.ok, false);
    assert.equal(unauth.code, 'ATTACHMENT_UNAUTHORISED');

    const otherCase = store.fetch(up.attachment_id, { case_id: 'SYN-CASE-ATT-B' });
    assert.equal(otherCase.ok, false);
    assert.equal(otherCase.code, 'ATTACHMENT_CASE_MISMATCH');

    const wrongScope = store.fetch(up.attachment_id, {
      authorised_case_ids: ['SYN-CASE-ATT-B']
    });
    assert.equal(wrongScope.ok, false);
    assert.equal(wrongScope.code, 'ATTACHMENT_UNAUTHORISED');

    const ok = store.fetch(up.attachment_id, {
      case_id: 'SYN-CASE-ATT-A',
      authorised_case_ids: ['SYN-CASE-ATT-A']
    });
    assert.equal(ok.ok, true);
    assert.equal(ok.case_id, 'SYN-CASE-ATT-A');
    assert.equal(ok.auto_forward_original, false);

    const shared = store.shareShortResponse(up.attachment_id, {
      case_id: 'SYN-CASE-ATT-A',
      authorised_case_ids: ['SYN-CASE-ATT-A'],
      short_response: 'Synthetic short reply'
    });
    assert.equal(shared.ok, true);
    assert.equal(shared.original_attached, false);
    assert.equal(shared.auto_forward_original, false);
  } finally {
    t.cleanup();
  }
});

test('SAFE-06 E2: Disallowed or unscanned files remain unavailable for wider use; failure does not erase the saved case.', () => {
  const t = tempRoot('e2');
  try {
    const store = attachments.makeAttachmentStore({ rootDir: t.root });
    const savedCase = {
      case_id: 'SYN-CASE-ATT-KEEP',
      customer: 'ORG-ALPHA',
      state: 'draft',
      note: 'Synthetic case that must survive a refused upload.'
    };

    const traversal = store.upload(savedCase.case_id, {
      name: '../secret.txt',
      bytes: Buffer.from('nope', 'utf8')
    }, { scanned: true, caseRecord: savedCase });
    assert.equal(traversal.ok, false);
    assert.equal(traversal.code, 'PATH_TRAVERSAL_REFUSED');
    assert.equal(traversal.case_erased, false);
    assert.equal(traversal.case_still_present, true);
    assert.equal(savedCase.case_id, 'SYN-CASE-ATT-KEEP');
    assert.equal(savedCase.state, 'draft');

    const exe = store.upload(savedCase.case_id, {
      name: 'payload.exe',
      bytes: Buffer.from('MZ', 'utf8')
    }, { scanned: true, caseRecord: savedCase });
    assert.equal(exe.ok, false);
    assert.equal(exe.code, 'EXECUTABLE_CONTENT_REFUSED');
    assert.equal(exe.case_erased, false);
    assert.equal(savedCase.case_id, 'SYN-CASE-ATT-KEEP');

    const quarantined = store.upload(savedCase.case_id, {
      name: 'unscanned.txt',
      bytes: Buffer.from('synthetic unscanned', 'utf8')
    }, { scanned: false, caseRecord: savedCase });
    assert.equal(quarantined.ok, true);
    assert.equal(quarantined.quarantined, true);
    assert.equal(quarantined.available_for_wider_use, false);
    assert.equal(quarantined.case_erased, false);

    const fetchQ = store.fetch(quarantined.attachment_id, {
      case_id: savedCase.case_id,
      authorised_case_ids: [savedCase.case_id]
    });
    assert.equal(fetchQ.ok, false);
    assert.equal(fetchQ.code, 'ATTACHMENT_QUARANTINED');
    assert.equal(fetchQ.case_erased, false);
    assert.equal(savedCase.state, 'draft');
  } finally {
    t.cleanup();
  }
});