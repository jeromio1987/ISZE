#!/usr/bin/env node
/* ===========================================================================
   SAFE-02 acceptance tests: Enforce organisation, account and case permissions
   on the server.

   How to run
     node --test tests/safe_02_permissions.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Changing a distributor/account/case identifier in a request cannot
         return another participant's records or counts.
     E2  Permissions are tested on direct service requests, not only on hidden
         menu options.

   Synthetic fixtures only. No real accounts or dealer data.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const backend = require('../src/case/server/server.js');
const permissions = require('../src/case/server/permissions.js');

const FIXED_NOW = '2026-10-06T15:00:00.000Z';

function tempDb(label) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-safe02-' + label + '-'));
  return {
    root,
    dbPath: path.join(root, 'cases.sqlite'),
    cleanup() {
      try { fs.rmSync(root, { recursive: true, force: true }); } catch (e) { /* ignore */ }
    }
  };
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  const body = await res.json();
  return { status: res.status, body };
}

function claims(tenant, subject) {
  return JSON.stringify({
    subject: subject || ('synth-' + tenant),
    role: 'viewer',
    tenant: tenant,
    issued_by: 'synthetic-provider-claims'
  });
}

test('SAFE-02 E1: Changing a distributor/account/case identifier in a request cannot return another participant\'s records or counts.', async () => {
  const db = tempDb('e1');
  let running = null;
  try {
    running = backend.startSharedBackend({
      dbPath: db.dbPath,
      host: '127.0.0.1',
      port: 0,
      now: () => FIXED_NOW,
      seed: false,
      allowDevelopmentFallback: true
    });
    const addr = await running.ready;

    const ownerClaims = JSON.stringify({
      subject: 'synth-owner',
      role: 'case_owner',
      tenant: 'ORG-ALPHA',
      issued_by: 'synthetic-provider-claims'
    });

    const a = await fetchJson(addr.url + '/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-aim-claims': ownerClaims },
      body: JSON.stringify({
        case_id: 'SYN-CASE-ALPHA',
        customer: 'ORG-ALPHA',
        market: 'SYNTH',
        part_number: 'SYN-PN-A',
        description: 'Synthetic alpha case',
        owner_role: 'case_owner',
        scope_note: 'Synthetic. No real part, customer or price appears in this test.',
        by: 'safe-02'
      })
    });
    assert.equal(a.status, 201, JSON.stringify(a.body));

    const b = await fetchJson(addr.url + '/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-aim-claims': ownerClaims },
      body: JSON.stringify({
        case_id: 'SYN-CASE-BETA',
        customer: 'ORG-BETA',
        market: 'SYNTH',
        part_number: 'SYN-PN-B',
        description: 'Synthetic beta case',
        owner_role: 'case_owner',
        scope_note: 'Synthetic. No real part, customer or price appears in this test.',
        by: 'safe-02'
      })
    });
    assert.equal(b.status, 201, JSON.stringify(b.body));

    /* Participant for ORG-ALPHA asks for ORG-BETA via query string. */
    const listed = await fetchJson(
      addr.url + '/cases?distributor=ORG-BETA&organisation=ORG-BETA&account=ORG-BETA',
      { headers: { 'x-aim-claims': claims('ORG-ALPHA') } }
    );
    assert.equal(listed.status, 200, JSON.stringify(listed.body));
    assert.equal(listed.body.count, 0);
    assert.deepEqual(listed.body.cases, []);
    assert.equal(listed.body.authorised_tenant, 'ORG-ALPHA');

    const cross = await fetchJson(addr.url + '/cases/SYN-CASE-BETA', {
      headers: { 'x-aim-claims': claims('ORG-ALPHA') }
    });
    assert.equal(cross.status, 403);
    assert.equal(cross.body.ok, false);
    assert.equal(cross.body.count, 0);
    assert.ok(!cross.body.record);

    const own = await fetchJson(addr.url + '/cases/SYN-CASE-ALPHA', {
      headers: { 'x-aim-claims': claims('ORG-ALPHA') }
    });
    assert.equal(own.status, 200);
    assert.equal(own.body.record.case_id, 'SYN-CASE-ALPHA');

    const scopedList = await fetchJson(addr.url + '/cases', {
      headers: { 'x-aim-claims': claims('ORG-ALPHA') }
    });
    assert.equal(scopedList.status, 200);
    assert.equal(scopedList.body.count, 1);
    assert.deepEqual(scopedList.body.cases.map((r) => r.case_id), ['SYN-CASE-ALPHA']);
  } finally {
    if (running) await running.close();
    db.cleanup();
  }
});

test('SAFE-02 E2: Permissions are tested on direct service requests, not only on hidden menu options.', async () => {
  const db = tempDb('e2');
  let running = null;
  try {
    running = backend.startSharedBackend({
      dbPath: db.dbPath,
      host: '127.0.0.1',
      port: 0,
      now: () => FIXED_NOW,
      seed: false,
      allowDevelopmentFallback: false
    });
    const addr = await running.ready;

    /* Direct service layer (no UI). */
    const identityA = permissions.resolveRequestIdentity({
      providerClaims: {
        subject: 'synth-a',
        role: 'viewer',
        tenant: 'ORG-ALPHA',
        issued_by: 'synthetic-provider-claims'
      },
      body: { distributor: 'ORG-BETA', organisation: 'ORG-BETA' },
      allowDevelopmentFallback: false
    });
    assert.equal(identityA.ok, true);
    assert.equal(identityA.tenant, 'ORG-ALPHA');

    running.service.create({
      case_id: 'SYN-DIRECT-A',
      customer: 'ORG-ALPHA',
      market: 'SYNTH',
      part_number: 'SYN-PN-DA',
      description: 'Synthetic direct A',
      owner_role: 'case_owner',
      scope_note: 'Synthetic. No real part, customer or price appears in this test.',
      by: 'safe-02'
    });
    running.service.create({
      case_id: 'SYN-DIRECT-B',
      customer: 'ORG-BETA',
      market: 'SYNTH',
      part_number: 'SYN-PN-DB',
      description: 'Synthetic direct B',
      owner_role: 'case_owner',
      scope_note: 'Synthetic. No real part, customer or price appears in this test.',
      by: 'safe-02'
    });

    const query = permissions.authorizeCaseQuery(running.service, identityA, {
      distributor: 'ORG-BETA'
    });
    assert.equal(query.ok, true);
    assert.equal(query.count, 0);

    const denied = permissions.authorizeCaseRead(running.service, identityA, 'SYN-DIRECT-B');
    assert.equal(denied.ok, false);
    assert.equal(denied.code, 'CASE_OUTSIDE_SCOPE');

    const allowed = permissions.authorizeCaseRead(running.service, identityA, 'SYN-DIRECT-A');
    assert.equal(allowed.ok, true);
    assert.equal(allowed.record.case_id, 'SYN-DIRECT-A');

    /* Same checks over the HTTP service surface (still not a menu). */
    const noClaims = await fetchJson(addr.url + '/cases');
    assert.equal(noClaims.status, 401);

    const httpList = await fetchJson(addr.url + '/cases?distributor=ORG-BETA', {
      headers: { 'x-aim-claims': claims('ORG-ALPHA') }
    });
    assert.equal(httpList.status, 200);
    assert.equal(httpList.body.count, 0);

    const httpCross = await fetchJson(addr.url + '/cases/SYN-DIRECT-B', {
      headers: { 'x-aim-claims': claims('ORG-ALPHA') }
    });
    assert.equal(httpCross.status, 403);
  } finally {
    if (running) await running.close();
    db.cleanup();
  }
});