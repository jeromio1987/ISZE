/* ===========================================================================
   Durable case record (CASE-01 ... CASE-08, F12).

   v03 kept one mutable blob in localStorage: no version, no history, no owner,
   no separate proposal and outcome, and a second edit silently overwrote the
   first. This module keeps an append-only revision log per case, so a case is
   the sequence of decisions taken on it rather than whatever is in the box now.

   Storage note: there is no approved shared backend for this component yet
   (RUN-01 records that as an open decision). The record is deliberately written
   behind this interface so that swapping the store for a real service does not
   change the case shape or the callers.
   =========================================================================== */
(function (root) {
  'use strict';

  var contracts = (typeof module === 'object' && module.exports)
    ? require('./contracts.js') : root.AIMContracts;

  var KEY = 'ISZE_AIM_CASES_V1';

  function nowISO() { return new Date().toISOString(); }

  /* Storage adapter. A browser keeps localStorage; Node keeps an object, so the
     same tests run without a browser. */
  function makeStore(options) {
    options = options || {};
    var memory = {}, useMemory = options.forceMemory || false;
    var available = true;

    function readAll() {
      if (useMemory || !available) return memory;
      try {
        var raw = root.localStorage.getItem(KEY);
        return raw ? JSON.parse(raw) : {};
      } catch (e) {
        available = false;
        return memory;
      }
    }
    function writeAll(all) {
      memory = all;
      if (useMemory || !available) return { ok: true, durable: false, reason: 'memory only' };
      try {
        root.localStorage.setItem(KEY, JSON.stringify(all));
        return { ok: true, durable: true };
      } catch (e) {
        available = false;
        return { ok: false, durable: false, reason: 'storage refused the write: ' + e.message };
      }
    }
    return {
      readAll: readAll, writeAll: writeAll,
      isDurable: function () { return available && !useMemory; },
      reset: function () { memory = {}; try { root.localStorage.removeItem(KEY); } catch (e) {} }
    };
  }

  function makeRepository(options) {
    var store = (options && options.store) || makeStore(options);

    function load(caseId) {
      var all = store.readAll();
      return all[caseId] ? all[caseId] : null;
    }

    function list() {
      var all = store.readAll();
      return Object.keys(all).map(function (id) {
        var c = all[id];
        return {
          case_id: id, version: c.version, state: c.state,
          owner_role: c.owner_role, next_action: c.next_action,
          next_update_due: c.next_update_due,
          part_number: c.revisions.length ? c.revisions[0].record.part_number : null,
          updated_at: c.updated_at, revision_count: c.revisions.length
        };
      }).sort(function (a, b) { return String(b.updated_at).localeCompare(String(a.updated_at)); });
    }

    /* Append a revision. Never overwrite: a correction is a new revision that
       names its predecessor, so the decision made on the old evidence survives. */
    function save(caseId, record, meta) {
      meta = meta || {};
      var all = store.readAll();
      var existing = all[caseId] || null;
      var expected = meta.expected_version;
      var currentVersion = existing ? existing.version : 0;

      /* Concurrency guard (CASE-07). A writer working from a stale copy is told
         rather than allowed to clobber. */
      if (expected !== undefined && expected !== null && expected !== currentVersion) {
        return { ok: false, conflict: true, expected_version: expected,
          actual_version: currentVersion,
          error: 'This case was changed by someone else after you opened it (expected version '
            + expected + ', the record is at ' + currentVersion + '). Reload before saving.' };
      }

      var state = meta.state || (existing ? existing.state : 'draft');
      if (contracts.CASE_STATES.indexOf(state) < 0) {
        return { ok: false, error: 'Unknown case state "' + state + '".' };
      }

      /* Reject a duplicate submission of the same revision content. */
      if (existing) {
        var last = existing.revisions[existing.revisions.length - 1];
        if (last && JSON.stringify(last.record) === JSON.stringify(record)
            && last.state === state) {
          return { ok: false, duplicate: true,
            error: 'That is the same content as the current revision. Nothing was saved.' };
        }
      }

      var version = currentVersion + 1;
      var revision = {
        revision: version,
        recorded_at: nowISO(),
        supersedes: currentVersion || null,
        state: state,
        record: record,
        note: meta.note || null,
        recorded_by: meta.recorded_by || 'unspecified'
      };

      var next = {
        case_id: caseId,
        version: version,
        state: state,
        owner_role: meta.owner_role || (existing ? existing.owner_role : null),
        next_action: meta.next_action !== undefined ? meta.next_action
          : (existing ? existing.next_action : null),
        next_update_due: meta.next_update_due !== undefined ? meta.next_update_due
          : (existing ? existing.next_update_due : null),
        created_at: existing ? existing.created_at : revision.recorded_at,
        updated_at: revision.recorded_at,
        /* The revision log is the case. Nothing is ever removed from it. */
        revisions: (existing ? existing.revisions : []).concat([revision]),
        outcome: meta.outcome !== undefined ? meta.outcome : (existing ? existing.outcome : null),
        delivered_support: meta.delivered_support !== undefined
          ? meta.delivered_support : (existing ? existing.delivered_support : null)
      };

      all[caseId] = next;
      var written = store.writeAll(all);
      return {
        ok: true, version: version, durable: written.durable,
        warning: written.ok ? null : written.reason,
        case: summarize(next)
      };
    }

    /* A correction names the revision it replaces and never multiplies the
       activity it corrects. */
    function correct(caseId, replacementRecord, meta) {
      meta = meta || {};
      var existing = load(caseId);
      if (!existing) return { ok: false, error: 'No such case to correct.' };
      return save(caseId, replacementRecord, {
        expected_version: meta.expected_version,
        state: meta.state || existing.state,
        note: meta.note || ('Correction of revision ' + (meta.corrects_revision || existing.version)),
        recorded_by: meta.recorded_by,
        owner_role: existing.owner_role,
        next_action: existing.next_action,
        next_update_due: existing.next_update_due,
        outcome: existing.outcome,
        delivered_support: existing.delivered_support
      });
    }

    function summarize(caseRecord) {
      var latest = caseRecord.revisions[caseRecord.revisions.length - 1];
      return {
        case_id: caseRecord.case_id, version: caseRecord.version, state: caseRecord.state,
        owner_role: caseRecord.owner_role, next_action: caseRecord.next_action,
        next_update_due: caseRecord.next_update_due,
        updated_at: caseRecord.updated_at,
        revision_count: caseRecord.revisions.length,
        latest_revision: latest ? latest.revision : null,
        scenario: latest ? latest.record.scenario || null : null,
        result: latest ? latest.record.result || null : null
      };
    }

    function history(caseId) {
      var c = load(caseId);
      if (!c) return [];
      return c.revisions.map(function (r) {
        return { revision: r.revision, recorded_at: r.recorded_at, state: r.state,
          supersedes: r.supersedes, recorded_by: r.recorded_by, note: r.note };
      });
    }

    /* Reopen with the same assumptions and the same results (UX-08). */
    function reopen(caseId, version) {
      var c = load(caseId);
      if (!c) return null;
      var wanted = version || c.version;
      var rev = c.revisions.filter(function (r) { return r.revision === wanted; })[0];
      if (!rev) return null;
      return { case_id: caseId, version: wanted, state: rev.state,
        scenario: rev.record.scenario, result: rev.record.result,
        review: rev.record.review || null };
    }

    /* The actionable queue (CASE-08): what is due, and who owes it. */
    function queue(asOfDate) {
      var today = asOfDate || nowISO().slice(0, 10);
      return list().map(function (row) {
        var overdue = !!(row.next_update_due && row.next_update_due < today);
        return {
          case_id: row.case_id, state: row.state, owner_role: row.owner_role,
          next_action: row.next_action, next_update_due: row.next_update_due,
          overdue: overdue, version: row.version, part_number: row.part_number
        };
      }).filter(function (row) {
        return row.next_update_due || row.next_action || row.state !== 'draft';
      }).sort(function (a, b) {
        if (a.overdue !== b.overdue) return a.overdue ? -1 : 1;
        return String(a.next_update_due || '9999').localeCompare(String(b.next_update_due || '9999'));
      });
    }

    function exportAll() {
      return { schema: 'isze-aim-cases', contract_version: contracts.CONTRACT_VERSION,
        exported_at: nowISO(), cases: store.readAll() };
    }

    /* Recovery from an exported bundle (RUN-07). */
    function importAll(bundle, options2) {
      options2 = options2 || {};
      if (!bundle || !bundle.cases) return { ok: false, error: 'Not a case bundle.' };
      var all = store.readAll(), added = 0, skipped = 0;
      Object.keys(bundle.cases).forEach(function (id) {
        if (all[id] && !options2.overwrite) { skipped++; return; }
        all[id] = bundle.cases[id]; added++;
      });
      var written = store.writeAll(all);
      return { ok: true, added: added, skipped: skipped, durable: written.durable };
    }

    return {
      save: save, load: load, list: list, history: history, reopen: reopen,
      correct: correct, queue: queue, exportAll: exportAll, importAll: importAll,
      summarize: summarize, store: store
    };
  }

  var API = { makeStore: makeStore, makeRepository: makeRepository, KEY: KEY,
    CASE_STATES: (contracts && contracts.CASE_STATES) || [] };
  root.AIMCases = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
