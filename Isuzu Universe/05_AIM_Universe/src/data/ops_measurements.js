/* ===========================================================================
   RUN-06 - Record operational failures and useful-work measurements.

   Log versioned errors, failed saves/imports, response stages and task effort
   without copying confidential case contents. Measure actual timing.
   Separate acknowledgement, substantive response, resolution and
   participant-confirmed usefulness. Visits and login counts are not usefulness.

   Synthetic fixtures only.
   =========================================================================== */
(function (root) {
  'use strict';

  function deepClone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }
  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  var CONFIDENTIAL_KEYS = ['cost_eur', 'margin', 'gross_profit', 'dealer_email', 'private_note'];

  function stripConfidential(obj) {
    var out = deepClone(obj || {});
    CONFIDENTIAL_KEYS.forEach(function (k) { if (k in out) delete out[k]; });
    return out;
  }

  function makeOpsRecorder(options) {
    options = options || {};
    var clock = typeof options.now === 'function' ? options.now : function () { return Date.now(); };
    var failures = [];
    var measurements = [];

    function recordFailure(event) {
      event = event || {};
      var started = event.started_at != null ? Number(event.started_at) : null;
      var ended = event.ended_at != null ? Number(event.ended_at) : clock();
      var elapsed_ms = (started != null && isFinite(started) && isFinite(ended)) ? (ended - started) : null;
      var row = {
        ok: false,
        reference: name(event.reference) || ('ERR-' + (failures.length + 1)),
        kind: name(event.kind) || 'failed_save',
        build: name(event.build) || name(event.tested_build) || null,
        stage: name(event.stage) || null,
        message: name(event.message) || 'Operation failed',
        elapsed_ms: elapsed_ms,
        safe_context: stripConfidential(event.context || {}),
        confidential_copied: false,
        synthetic: true
      };
      failures.push(deepClone(row));
      return deepClone(row);
    }

    function investigate(reference) {
      var ref = name(reference);
      for (var i = 0; i < failures.length; i++) {
        if (failures[i].reference === ref) {
          return {
            ok: true,
            reference: ref,
            build: failures[i].build,
            kind: failures[i].kind,
            stage: failures[i].stage,
            message: failures[i].message,
            elapsed_ms: failures[i].elapsed_ms,
            statement: 'Failure investigated from its safe error reference and tested build.'
          };
        }
      }
      return { ok: false, code: 'UNKNOWN_REFERENCE', error: 'No failure with that reference.' };
    }

    /* Separate measurements: acknowledgement, substantive response, resolution,
       participant-confirmed usefulness. Visits/logins are not usefulness. */
    function recordMeasurement(event) {
      event = event || {};
      var kind = name(event.kind);
      var allowed = {
        acknowledgement: true,
        substantive_response: true,
        resolution: true,
        participant_confirmed_usefulness: true,
        preparation: true,
        correction: true,
        review: true,
        follow_through: true
      };
      if (!allowed[kind]) {
        return {
          ok: false,
          code: 'MEASUREMENT_KIND_REFUSED',
          error: 'Visits and login counts are not usefulness or financial benefit.',
          kind: kind
        };
      }
      var started = event.started_at != null ? Number(event.started_at) : null;
      var ended = event.ended_at != null ? Number(event.ended_at) : null;
      var elapsed_ms = (started != null && ended != null && isFinite(started) && isFinite(ended))
        ? (ended - started) : null;
      if (elapsed_ms == null && event.elapsed_ms != null) elapsed_ms = Number(event.elapsed_ms);
      var row = {
        ok: true,
        kind: kind,
        case_id: name(event.case_id),
        elapsed_ms: elapsed_ms,
        invented: false,
        measured: elapsed_ms != null,
        synthetic: true
      };
      measurements.push(deepClone(row));
      return deepClone(row);
    }

    function summary() {
      var byKind = {};
      measurements.forEach(function (m) {
        byKind[m.kind] = (byKind[m.kind] || 0) + 1;
      });
      return {
        failure_count: failures.length,
        measurement_counts: byKind,
        statement: 'Acknowledgement, substantive response, resolution and participant-confirmed usefulness are separate measurements.'
      };
    }

    return {
      recordFailure: recordFailure,
      investigate: investigate,
      recordMeasurement: recordMeasurement,
      summary: summary,
      failures: function () { return deepClone(failures); },
      measurements: function () { return deepClone(measurements); }
    };
  }

  var API = { makeOpsRecorder: makeOpsRecorder, stripConfidential: stripConfidential };
  root.AIMOpsMeasurements = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
