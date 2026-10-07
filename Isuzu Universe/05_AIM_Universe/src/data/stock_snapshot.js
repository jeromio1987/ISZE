/* ===========================================================================
   CONNECT-06 - Accept a small optional stock snapshot for a defined case.

   Scoped, permitted observation with known part, date, on-hand / reserved /
   available definitions and source. Case-specific unless a separate recurring
   agreement exists. Do not reconstruct inventory by subtracting sales to dealer
   from ISZE billing. A missing snapshot leaves the narrower review usable.

   Unknown reserved stock must not become available stock through a default zero.
   Declining a stock contribution must not close an unrelated commercial or
   application request.

   Synthetic fixtures only. No real stock file.
   =========================================================================== */
(function (root) {
  'use strict';

  function deepClone(value) {
    return JSON.parse(JSON.stringify(value == null ? null : value));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function isKnownNumber(v) {
    return v !== undefined && v !== null && v !== '' && Number.isFinite(Number(v));
  }

  function snapshotsOf(caseRecord) {
    return Array.isArray(caseRecord && caseRecord.stock_snapshots)
      ? caseRecord.stock_snapshots.map(function (s) { return deepClone(s); })
      : [];
  }

  function requestsOf(caseRecord, key) {
    return Array.isArray(caseRecord && caseRecord[key])
      ? caseRecord[key].map(function (r) { return deepClone(r); })
      : [];
  }

  /* Resolve available quantity. Unknown reserved never defaults to zero. */
  function resolveAvailable(onHand, reserved) {
    if (!isKnownNumber(onHand)) {
      return {
        available: null,
        available_known: false,
        reserved_known: isKnownNumber(reserved),
        statement: 'On-hand quantity is unknown, so available stock is unknown.'
      };
    }
    if (!isKnownNumber(reserved)) {
      return {
        available: null,
        available_known: false,
        reserved_known: false,
        statement: 'Reserved stock is unknown. Available stock is not derived by treating reserved as zero.'
      };
    }
    var available = Number(onHand) - Number(reserved);
    return {
      available: available,
      available_known: true,
      reserved_known: true,
      statement: 'Available stock is on-hand minus known reserved.'
    };
  }

  /* Accept an optional stock snapshot on a defined case. Synthetic observation. */
  function acceptStockSnapshot(caseRecord, snapshot, options) {
    caseRecord = caseRecord || {};
    snapshot = snapshot || {};
    options = options || {};

    var part = name(snapshot.part_number);
    var asOf = name(snapshot.as_of) || name(snapshot.observation_date);
    var source = name(snapshot.source);
    if (!part) {
      return { ok: false, error: 'A stock snapshot needs a part number.', case_record: caseRecord };
    }
    if (!asOf) {
      return { ok: false, error: 'A stock snapshot needs an observation date.', case_record: caseRecord };
    }
    if (!source) {
      return { ok: false, error: 'A stock snapshot needs a source.', case_record: caseRecord };
    }

    var onHand = isKnownNumber(snapshot.on_hand) ? Number(snapshot.on_hand) : null;
    var reserved = isKnownNumber(snapshot.reserved) ? Number(snapshot.reserved) : null;
    /* Explicit unknown markers stay unknown; never coerce blank/undefined reserved to 0. */
    if (snapshot.reserved === undefined || snapshot.reserved === null || snapshot.reserved === '' ||
        String(snapshot.reserved).toLowerCase() === 'unknown') {
      reserved = null;
    }

    var resolved = resolveAvailable(onHand, reserved);
    var list = snapshotsOf(caseRecord);
    var row = {
      snapshot_id: name(options.snapshot_id) || name(snapshot.snapshot_id) || ('SS-' + (list.length + 1)),
      part_number: part,
      as_of: asOf,
      on_hand: onHand,
      reserved: reserved,
      available: resolved.available,
      available_known: resolved.available_known,
      reserved_known: resolved.reserved_known,
      source: source,
      synthetic: true,
      contribution: 'accepted',
      definitions: {
        on_hand: 'Units physically held at the stated location on as_of.',
        reserved: 'Units already committed and not free to promise; unknown means not stated.',
        available: 'On-hand minus known reserved only. Unknown reserved blocks available.'
      },
      statement: resolved.statement
    };
    list.push(row);

    var next = Object.assign({}, caseRecord, {
      stock_snapshots: list,
      commercial_requests: requestsOf(caseRecord, 'commercial_requests'),
      application_requests: requestsOf(caseRecord, 'application_requests'),
      stock_contribution: Object.assign({}, caseRecord.stock_contribution || {}, {
        status: 'accepted',
        last_snapshot_id: row.snapshot_id
      })
    });

    return {
      ok: true,
      snapshot: row,
      case_record: next,
      statement: 'Optional stock snapshot accepted for the case. Synthetic observation only.'
    };
  }

  /* Decline a stock contribution without closing unrelated open requests. */
  function declineStockContribution(caseRecord, options) {
    caseRecord = caseRecord || {};
    options = options || {};

    var commercial = requestsOf(caseRecord, 'commercial_requests');
    var application = requestsOf(caseRecord, 'application_requests');
    var beforeCommercialOpen = commercial.filter(function (r) {
      return r && r.status === 'open';
    }).length;
    var beforeApplicationOpen = application.filter(function (r) {
      return r && r.status === 'open';
    }).length;

    /* Do not mutate status of unrelated commercial or application requests. */
    var next = Object.assign({}, caseRecord, {
      stock_snapshots: snapshotsOf(caseRecord),
      commercial_requests: commercial,
      application_requests: application,
      stock_contribution: {
        status: 'declined',
        declined_at: name(options.declined_at) || null,
        declined_by: name(options.declined_by) || null,
        reason: name(options.reason) || 'Stock contribution declined for this case.',
        synthetic: true
      }
    });

    var afterCommercialOpen = next.commercial_requests.filter(function (r) {
      return r && r.status === 'open';
    }).length;
    var afterApplicationOpen = next.application_requests.filter(function (r) {
      return r && r.status === 'open';
    }).length;

    return {
      ok: true,
      case_record: next,
      commercial_open_before: beforeCommercialOpen,
      commercial_open_after: afterCommercialOpen,
      application_open_before: beforeApplicationOpen,
      application_open_after: afterApplicationOpen,
      closed_unrelated_request: false,
      statement: 'Stock contribution declined. Unrelated commercial and application requests stay as they were.'
    };
  }

  /* Narrower review remains usable when no snapshot is present. */
  function reviewWithoutSnapshot(caseRecord) {
    caseRecord = caseRecord || {};
    var list = snapshotsOf(caseRecord);
    return {
      ok: true,
      usable: true,
      has_snapshot: list.length > 0,
      stock_required: false,
      statement: list.length
        ? 'Stock snapshot is present and optional for the narrower review.'
        : 'No stock snapshot is present. The narrower commercial review remains usable.'
    };
  }

  var API = {
    resolveAvailable: resolveAvailable,
    acceptStockSnapshot: acceptStockSnapshot,
    declineStockContribution: declineStockContribution,
    reviewWithoutSnapshot: reviewWithoutSnapshot
  };

  root.AIMStockSnapshot = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
