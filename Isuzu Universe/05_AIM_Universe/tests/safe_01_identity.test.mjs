#!/usr/bin/env node
/* ===========================================================================
   SAFE-01 acceptance tests: Connect approved identity with an explicit
   development-only mode.

   How to run
     node --test tests/safe_01_identity.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Shared-mode startup rejects development identity and missing approved
         identity configuration.
     E2  A user identity is established outside client-controlled organisation
         fields.

   Synthetic fixtures only. No real sign-in, accounts, passwords or tokens.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const identity = require(join(ROOT, 'src', 'data', 'identity.js'));

test('SAFE-01 E1: Shared-mode startup rejects development identity and missing approved identity configuration.', () => {
  const missing = identity.resolveStartupIdentity({
    mode: 'shared',
    buildKind: 'development',
    approvedProviderConfig: null,
    enableDevelopmentIdentity: false
  });
  assert.equal(missing.ok, false);
  assert.equal(missing.code, 'MISSING_APPROVED_IDENTITY_CONFIGURATION');

  const devInShared = identity.resolveStartupIdentity({
    mode: 'shared',
    buildKind: 'development',
    approvedProviderConfig: { configured: true, provider: 'synthetic-flag-only' },
    requestedIdentity: { mode: 'development-only', role: 'viewer' }
  });
  assert.equal(devInShared.ok, false);
  assert.equal(devInShared.code, 'DEVELOPMENT_IDENTITY_REFUSED_IN_SHARED');

  const enableDevInShared = identity.resolveStartupIdentity({
    mode: 'shared',
    buildKind: 'development',
    approvedProviderConfig: { configured: true, provider: 'synthetic-flag-only' },
    enableDevelopmentIdentity: true
  });
  assert.equal(enableDevInShared.ok, false);
  assert.equal(enableDevInShared.code, 'DEVELOPMENT_IDENTITY_REFUSED_IN_SHARED');

  const internalDev = identity.makeDevIdentity({ role: 'case_owner' }, 'INTERNAL');
  assert.equal(internalDev.ok, false);
  assert.equal(internalDev.code, 'DEVELOPMENT_IDENTITY_IMPOSSIBLE_IN_INTERNAL');

  const internalStartup = identity.resolveStartupIdentity({
    mode: 'shared',
    buildKind: 'INTERNAL',
    approvedProviderConfig: { configured: true },
    enableDevelopmentIdentity: true
  });
  assert.equal(internalStartup.ok, false);
  assert.equal(internalStartup.code, 'DEVELOPMENT_IDENTITY_IMPOSSIBLE_IN_INTERNAL');

  const localDev = identity.resolveStartupIdentity({
    mode: 'development',
    buildKind: 'development',
    enableDevelopmentIdentity: true,
    role: 'case_owner',
    name: 'synthetic-dev'
  });
  assert.equal(localDev.ok, true);
  assert.equal(localDev.mode, 'development-only');
  assert.equal(localDev.authenticated, false);
  assert.equal(localDev.development_only, true);
  assert.match(localDev.label, /DEVELOPMENT-ONLY/i);
});

test('SAFE-01 E2: A user identity is established outside client-controlled organisation fields.', () => {
  const claims = {
    subject: 'synth-user-001',
    role: 'viewer',
    tenant: 'ORG-ALPHA',
    display_name: 'Synthetic Viewer',
    issued_by: 'synthetic-provider-claims'
  };
  const clientTriesToSwitch = {
    organisation: 'ORG-BETA',
    distributor: 'ORG-BETA',
    account: 'OTHER-ACCOUNT',
    tenant: 'ORG-BETA',
    customer: 'ORG-BETA'
  };

  const established = identity.establishIdentity(claims, clientTriesToSwitch);
  assert.equal(established.ok, true);
  assert.equal(established.mode, 'approved');
  assert.equal(established.authenticated, true);
  assert.equal(established.tenant, 'ORG-ALPHA');
  assert.notEqual(established.tenant, clientTriesToSwitch.organisation);
  assert.notEqual(established.tenant, clientTriesToSwitch.distributor);
  assert.ok(established.client_organisation_fields_ignored.length >= 1);
  assert.ok(
    established.client_organisation_fields_ignored.includes('organisation')
      || established.client_organisation_fields_ignored.includes('distributor')
      || established.client_organisation_fields_ignored.includes('tenant')
  );

  const noClaims = identity.establishIdentity(null, { organisation: 'ORG-BETA' });
  assert.equal(noClaims.ok, false);
  assert.equal(noClaims.code, 'NO_PROVIDER_CLAIMS');

  const claimsWithoutTenant = identity.establishIdentity({
    subject: 'synth-user-002',
    role: 'viewer'
  }, { organisation: 'ORG-BETA' });
  assert.equal(claimsWithoutTenant.ok, false);
  assert.equal(claimsWithoutTenant.code, 'TENANT_NOT_IN_CLAIMS');
});
