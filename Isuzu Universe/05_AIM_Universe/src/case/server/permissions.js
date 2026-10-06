/* ===========================================================================
   SAFE-02 - organisation, account and case permissions on the server.

   Client filters (distributor, account, case id in the request body or query)
   are presentation only. Authorised scope comes from the validated identity
   (provider claims established outside those fields). Unrecognised scope is
   denied by default.
   =========================================================================== */
(function (root) {
  'use strict';

  var identityMod = null;
  try { identityMod = require('../../data/identity.js'); } catch (e) { identityMod = null; }

  function reject(code, error, extra) {
    return Object.assign({ ok: false, allowed: false, code: code, error: error }, extra || {});
  }

  /* Resolve the request identity from server-held claims. Body/query organisation
     fields cannot grant a different tenant. */
  function resolveRequestIdentity(options) {
    options = options || {};
    var claims = options.providerClaims || null;
    var clientFields = Object.assign({}, options.query || {}, options.body || {});
    if (!identityMod) {
      return reject('IDENTITY_MODULE_MISSING', 'Identity module is not available on the server.');
    }
    if (!claims) {
      /* Local disposable backend only. Shared-mode tests supply claims explicitly. */
      if (options.allowDevelopmentFallback) {
        var local = identityMod.makeDevIdentity({
          role: 'case_owner',
          name: 'local-backend',
          tenant: null,
          internal: true
        }, 'development');
        if (local && local.ok) {
          local.local_backend_fallback = true;
          return local;
        }
      }
      return reject('NO_SERVER_IDENTITY', 'No server-established identity claims were supplied.');
    }
    return identityMod.establishIdentity(claims, clientFields);
  }

  function isInternalOperator(identity) {
    if (!identity || identity.ok === false) return false;
    if (identity.local_backend_fallback) return true;
    return !!(identity.internal === true
      && ['case_owner', 'reviewer', 'approver'].indexOf(identity.role) >= 0
      && identity.tenant_verified === true);
  }

  /* Direct service read of one case. Changing the requested case id cannot return
     another organisation's record. */
  function authorizeCaseRead(service, identity, requestedCaseId) {
    if (!identity || identity.ok === false) {
      return reject('NOT_AUTHORISED', 'A validated identity is required.',
        { records: [], count: 0 });
    }
    if (!identity.local_backend_fallback && !identity.tenant) {
      return reject('NOT_AUTHORISED', 'A validated identity with organisation membership is required.',
        { records: [], count: 0 });
    }
    var record = service.get(requestedCaseId);
    if (!record) {
      return reject('NO_SUCH_CASE', 'No case was found for the requested identifier.',
        { records: [], count: 0 });
    }
    if (isInternalOperator(identity)) {
      return { ok: true, allowed: true, record: record, count: 1 };
    }
    if (String(record.customer) !== String(identity.tenant)) {
      return reject('CASE_OUTSIDE_SCOPE',
        'The requested case is outside the authorised organisation scope.',
        { records: [], count: 0 });
    }
    return { ok: true, allowed: true, record: record, count: 1 };
  }

  /* List / search / counts. A client-supplied distributor or account filter cannot
     expand scope beyond the identity tenant. */
  function authorizeCaseQuery(service, identity, clientFilter) {
    clientFilter = clientFilter || {};
    if (!identity || identity.ok === false) {
      return reject('NOT_AUTHORISED', 'A validated identity is required.',
        { rows: [], count: 0 });
    }
    if (!identity.local_backend_fallback && !identity.tenant) {
      return reject('NOT_AUTHORISED', 'A validated identity with organisation membership is required.',
        { rows: [], count: 0 });
    }
    var all = service.list() || [];
    var rows = [];
    all.forEach(function (r) {
      if (!r) return;
      if (!isInternalOperator(identity) && String(r.customer) !== String(identity.tenant)) return;
      /* Client filter may narrow within scope, never widen. */
      if (clientFilter.distributor && String(clientFilter.distributor) !== String(r.customer)) return;
      if (clientFilter.account && String(clientFilter.account) !== String(r.customer)
        && String(clientFilter.account) !== String(r.purchasing_account || '')) return;
      if (clientFilter.case_id && String(clientFilter.case_id) !== String(r.case_id)) return;
      rows.push({
        case_id: r.case_id,
        customer: r.customer,
        part_number: r.part_number || null,
        state: r.state || null
      });
    });
    /* If the client asked for another organisation's distributor, the answer is
       empty for their scope — not the other organisation's rows. */
    return {
      ok: true,
      allowed: true,
      rows: rows,
      count: rows.length,
      authorised_tenant: identity.tenant,
      client_filter_applied_within_scope_only: true
    };
  }

  var API = {
    resolveRequestIdentity: resolveRequestIdentity,
    authorizeCaseRead: authorizeCaseRead,
    authorizeCaseQuery: authorizeCaseQuery,
    isInternalOperator: isInternalOperator
  };

  if (typeof module === 'object' && module.exports) module.exports = API;
  else root.AIMCasePermissions = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
