/* ===========================================================================
   SAFE-01 - approved identity with an explicit development-only mode.

   What this module does
   ---------------------
   Resolves the identity used at startup and on the shared case service. A
   development-only stand-in is allowed for local work, and is labelled on every
   record so nobody can mistake it for a signed-in person. An INTERNAL build
   cannot enable that stand-in. Shared-mode startup refuses both a development
   identity and a missing approved identity-provider configuration.

   What this module does not do
   ----------------------------
   It does not wire a real identity provider, create accounts, store passwords,
   or accept client-supplied organisation fields as authority. Real provider
   and tenant configuration need the authorised IT owner.
   =========================================================================== */
(function (root) {
  'use strict';

  var IDENTITY_MODES = ['approved', 'development-only'];
  var KNOWN_ROLES = ['requester', 'case_owner', 'reviewer', 'approver', 'support_owner', 'viewer'];
  var BUILD_KINDS = ['development', 'INTERNAL', 'shared'];

  function reject(code, error, extra) {
    return Object.assign({ ok: false, code: code, error: error }, extra || {});
  }

  /* Loud development-only stand-in. Impossible when buildKind is INTERNAL. */
  function makeDevIdentity(spec, buildKind) {
    spec = spec || {};
    var kind = buildKind || spec.buildKind || 'development';
    if (String(kind).toUpperCase() === 'INTERNAL') {
      return reject(
        'DEVELOPMENT_IDENTITY_IMPOSSIBLE_IN_INTERNAL',
        'A development-only identity cannot be enabled in an INTERNAL build. '
          + 'Use an approved identity provider configuration, or build a non-INTERNAL artifact.'
      );
    }
    var role = spec.role;
    if (KNOWN_ROLES.indexOf(role) < 0) {
      throw new Error('A development identity needs a known role. Got "' + role + '".');
    }
    return {
      ok: true,
      mode: 'development-only',
      authenticated: false,
      subject: 'dev:' + role + (spec.name ? ':' + spec.name : ''),
      display_name: spec.name || null,
      role: role,
      internal: spec.internal !== false,
      tenant: spec.tenant || null,
      tenant_verified: false,
      issued_by: 'development-only shim - NOT an authentication',
      buildKind: kind,
      development_only: true,
      label: 'DEVELOPMENT-ONLY IDENTITY - NOT A SIGNED-IN PERSON',
      note: 'Not a signed-in person. No identity provider authenticated this subject.',
      statement: 'Not an authentication. A development-only identity for local work.'
    };
  }

  /* Shared / production shape when an approved provider is configured.
     Without a provider config this always refuses (honest gap). */
  function requireApprovedIdentity(providerConfig) {
    if (!providerConfig || !providerConfig.configured) {
      return reject(
        'IDENTITY_NOT_AVAILABLE',
        'No approved identity provider is configured for this component, so no signed-in '
          + 'person can be established. Development-only identity is separate and must not be '
          + 'enabled for shared-mode startup or an INTERNAL build.'
      );
    }
    return reject(
      'IDENTITY_PROVIDER_NOT_WIRED',
      'An approved identity-provider configuration is present as a local flag only. '
        + 'Real provider wiring needs the authorised IT owner and is not implemented here.'
    );
  }

  /* Startup resolution. Shared mode refuses development identity and a missing
     approved configuration. INTERNAL builds refuse enabling development identity. */
  function resolveStartupIdentity(options) {
    options = options || {};
    var mode = options.mode || 'shared';
    var buildKind = options.buildKind || 'development';
    var providerConfig = options.approvedProviderConfig || null;
    var requested = options.requestedIdentity || null;

    if (String(buildKind).toUpperCase() === 'INTERNAL') {
      if (requested && requested.mode === 'development-only') {
        return reject(
          'DEVELOPMENT_IDENTITY_IMPOSSIBLE_IN_INTERNAL',
          'Shared-mode or INTERNAL startup cannot enable a development-only identity.',
          { mode: mode, buildKind: buildKind }
        );
      }
      if (options.enableDevelopmentIdentity === true) {
        return reject(
          'DEVELOPMENT_IDENTITY_IMPOSSIBLE_IN_INTERNAL',
          'enableDevelopmentIdentity is refused in an INTERNAL build.',
          { mode: mode, buildKind: buildKind }
        );
      }
    }

    if (mode === 'shared') {
      if (!providerConfig || !providerConfig.configured) {
        return reject(
          'MISSING_APPROVED_IDENTITY_CONFIGURATION',
          'Shared-mode startup rejects a missing approved identity configuration.',
          { mode: mode, buildKind: buildKind }
        );
      }
      if (requested && requested.mode === 'development-only') {
        return reject(
          'DEVELOPMENT_IDENTITY_REFUSED_IN_SHARED',
          'Shared-mode startup rejects a development-only identity.',
          { mode: mode, buildKind: buildKind }
        );
      }
      if (options.enableDevelopmentIdentity === true) {
        return reject(
          'DEVELOPMENT_IDENTITY_REFUSED_IN_SHARED',
          'Shared-mode startup rejects enabling a development-only identity.',
          { mode: mode, buildKind: buildKind }
        );
      }
      return requireApprovedIdentity(providerConfig);
    }

    if (options.enableDevelopmentIdentity === true || (requested && requested.mode === 'development-only')) {
      var role = (requested && requested.role) || options.role || 'case_owner';
      var tenant = (requested && requested.tenant) || options.tenant || null;
      return makeDevIdentity({
        role: role,
        name: (requested && requested.name) || options.name || null,
        tenant: tenant,
        buildKind: buildKind
      }, buildKind);
    }

    if (providerConfig && providerConfig.configured) {
      return requireApprovedIdentity(providerConfig);
    }

    return reject(
      'NO_IDENTITY_RESOLVED',
      'No identity was resolved. Enable development-only for local work, or supply an approved provider configuration.',
      { mode: mode, buildKind: buildKind }
    );
  }

  /* Establish an identity from provider claims. Client-controlled organisation
     fields are ignored for membership. Tenant comes only from validated claims. */
  function establishIdentity(providerClaims, clientFields) {
    clientFields = clientFields || {};
    if (!providerClaims || typeof providerClaims !== 'object') {
      return reject(
        'NO_PROVIDER_CLAIMS',
        'A user identity cannot be established without provider claims outside the client request.'
      );
    }
    if (providerClaims.mode === 'development-only') {
      return reject(
        'DEVELOPMENT_CLAIMS_NOT_PROVIDER',
        'Development-only claims are not an approved provider. Use makeDevIdentity in development mode only.'
      );
    }
    if (!providerClaims.subject || !providerClaims.role) {
      return reject(
        'INCOMPLETE_PROVIDER_CLAIMS',
        'Provider claims must carry subject and role. Organisation fields on the client request are ignored.'
      );
    }
    if (KNOWN_ROLES.indexOf(providerClaims.role) < 0) {
      return reject(
        'UNKNOWN_PROVIDER_ROLE',
        'Provider role "' + providerClaims.role + '" is not a known role.'
      );
    }
    var tenant = providerClaims.tenant || providerClaims.organisation_id || null;
    if (!tenant) {
      return reject(
        'TENANT_NOT_IN_CLAIMS',
        'Organisation membership must come from provider claims, not from client-controlled fields.'
      );
    }
    var ignored = [];
    ['organisation', 'organisation_id', 'distributor', 'account', 'tenant', 'customer'].forEach(function (k) {
      if (clientFields[k] != null) ignored.push(k);
    });
    return {
      ok: true,
      mode: 'approved',
      authenticated: true,
      subject: String(providerClaims.subject),
      display_name: providerClaims.display_name || null,
      role: providerClaims.role,
      tenant: String(tenant),
      tenant_verified: true,
      issued_by: providerClaims.issued_by || 'approved-provider-claims',
      client_organisation_fields_ignored: ignored,
      statement: 'Identity established from provider claims. Client organisation fields were not used as authority.'
    };
  }

  var API = {
    IDENTITY_MODES: IDENTITY_MODES,
    KNOWN_ROLES: KNOWN_ROLES,
    BUILD_KINDS: BUILD_KINDS,
    makeDevIdentity: makeDevIdentity,
    requireApprovedIdentity: requireApprovedIdentity,
    resolveStartupIdentity: resolveStartupIdentity,
    establishIdentity: establishIdentity
  };

  root.AIMIdentity = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
