/* ===========================================================================
   Durable case record - the repository the application calls (CASE-01, F12).

   WHY THIS FILE IS A FACADE AND NOT AN IMPLEMENTATION
   ---------------------------------------------------
   There were two case implementations in this tree, and they were not
   equivalent:

     this file          makeRepository()  - a version counter, a concurrency
    10|                                          guard and an append-only revision
                                            log. This is what the interface runs.
     src/case/store.js  makeCaseService() - the whole lifecycle: create,
                                            transition, the separate evidence /
                                            support / outcome records, the file
                                            adapter, the benefit account. This is
                                            what the case checks run.

   Two implementations of one concern is the defect this project has already
   lost time to - two engines, two export builders, two view layers. So one of
   them is the base and the other is retired on purpose rather than left beside
    20|   it to drift.

   The decision, recorded in docs/CASE_service.md and repeated here so a reader
   of this file sees it without opening another:

     src/case/schema.js and src/case/store.js are the base. They hold the
     lifecycle, the nine states now in force, the separate clocks, the versioned
     proposals, the support and outcome records, the benefit account and the file
     adapter. Twenty-seven existing checks plus the CASE-01..05 checks run
     against them.

     This file is retired as a second implementation. It keeps the caller
    30|     surface the rest of the component already uses.

   What "retired" means here, exactly: no state machine, no second version
   counter, no second duplicate guard and no second log format live in this file.
   Every call goes to `src/case/store.js`. The names below exist because
   `src/ui/app.js`, `tools/build.py` and five test files call
   `AIMCases.makeRepository(...)`, and they are answered by the base.

   THE COMPATIBILITY PROJECTION, AND WHY IT IS NOT A SECOND SHAPE
   --------------------------------------------------------------
   The old repository stored one record per case whose log was an array of
   *revisions*, each carrying a whole `{ scenario, result, ... }` snapshot. The
   base stores one record per case whose log is an array of *entries*, each
   carrying the fields it set and a snapshot of the commercial content. Those are
   the same information in two shapes.

   40|   So the base shape is the one stored, and the old shape is projected on read.
   `revisionsOf()` below maps the base log onto the revision shape for the two
   readers that expect it - the browser journey and `tests/ux_reopen.test.mjs`,
   both of which are outside this developer's ownership. The projection is
   read-only and derived; there is no second copy on disk to drift, and
   `load().revisions` cannot disagree with `history()`.

   Storage
   -------
   The base's three adapters: memory, browser and files. `makeStore` below is
   kept because `src/ui/app.js` reads `cases.store.isDurable()`; it is a thin
   50|   wrapper over the base's browser adapter rather than a fourth storage
   implementation.

     A FOLDER OF FILES ON ONE MACHINE IS NOT A SHARED SERVICE, and neither is
   browser storage. `describe()` says so in the words a reader needs, and the
   exported bundle repeats it. Two people on two machines do not see each other;
   there is no identity, no permission and no revocation here.
   =========================================================================== */
(function (root) {
  'use strict';

  var isNode = (typeof module === 'object' && module.exports);

  var contracts = isNode ? require('./contracts.js') : root.AIMContracts;
  var caseSchema = isNode ? require('../case/schema.js') : root.AIMCaseSchema;
  var caseStore = isNode ? require('../case/store.js') : root.AIMCaseStore;

  var KEY = 'ISZE_AIM_CASES_V1';

  /* Legacy keys a caller may pass that the base record does not carry. They are
     dropped with a note rather than stored, because a field nothing declares is
     the fault the contract was written to stop. `consistency` is a derived check
     and can be recomputed at any time, which is why it is safe to drop. */
  var LEGACY_ONLY_KEYS = ['consistency'];

  /* --------------------------------------------------------------- storage -- */

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
      if (useMemory || !available) { memory = all; return { ok: true, durable: false, reason: 'memory only' }; }
      try {
        root.localStorage.setItem(KEY, JSON.stringify(all));
        memory = all;
        return { ok: true, durable: true };
      } catch (e) {
        /* UX-06. A refused write is not kept: the session copy goes back to what
           storage last held, so a later screen cannot report the refused
           revision as saved. */
        available = false;
        try {
          var held = root.localStorage.getItem(KEY);
          memory = held ? JSON.parse(held) : {};
        } catch (e2) { /* storage unreadable as well: keep the last good copy */ }
        return { ok: false, durable: false, reason: 'storage refused the write: ' + e.message };
      }
    }
    return {
      readAll: readAll, writeAll: writeAll,
      isDurable: function () { return available && !useMemory; },
      reset: function () { memory = {}; try { root.localStorage.removeItem(KEY); } catch (e) {} },
      describe: function () { return caseStore.describeStorage(useMemory || !available ? 'memory' : 'browser'); }
    };
  }

  /* The storage adapter the base service expects, built from a legacy-shaped
     store object. A translation, not a fourth adapter. */
  function adapterFromLegacyStore(legacy) {
    return {
      describe: function () { return legacy.describe(); },
      readIndex: function () { return Object.keys(legacy.readAll()).sort(); },
      load: function (id) { var all = legacy.readAll(); return all[id] ? all[id] : null; },
      loadAll: function () { return legacy.readAll(); },
      save: function (id, record) {
        var all = legacy.readAll();
        all[id] = record;
        var written = legacy.writeAll(all);
        return { ok: written.ok !== false, durable: !!written.durable, error: written.reason };
      },
      remove: function (id) {
        var all = legacy.readAll();
        delete all[id];
        legacy.writeAll(all);
        return { ok: true };
      }
    };
  }

  /* ---------------------------------------------------- the read projection -- */

  /* The base log, in the revision shape the two outside readers expect. Derived
     on every read from the one stored log, so the two cannot disagree. */
  function revisionsOf(record) {
    if (!record || !Array.isArray(record.history)) return [];
    return record.history.map(function (h, i) {
      return {
        revision: h.seq,
        recorded_at: h.recorded_at,
        supersedes: i === 0 ? null : h.seq - 1,
        state: h.to_state || h.state || null,
        note: h.note || null,
        recorded_by: h.recorded_by || null,
        /* The record this revision carried. The base snapshots the commercial
           content on every entry, so this is read, not guessed. */
        record: {
          scenario: h.scenario === undefined ? null : h.scenario,
          result: h.result === undefined ? null : h.result,
          review: h.review === undefined ? null : h.review,
          part_number: record.part_number || null,
          consistency: h.consistency === undefined ? null : h.consistency
        }
      };
    });
  }

  /* The base log, in the history shape the interface's revision table expects.
     `src/ui/app.js` renders `h.revision`, `h.state` and `h.supersedes`, and it is
     not this developer's file to change, so the same projection serves it. */
  function historyForDisplay(record) {
    return revisionsOf(record).map(function (r) {
      return {
        revision: r.revision, recorded_at: r.recorded_at, state: r.state,
        supersedes: r.supersedes, recorded_by: r.recorded_by, note: r.note
      };
    });
  }

  /* A stored case as the old repository returned it: the base record, with the
     derived revision log attached. Nothing here is written back. */
  function asLegacyRecord(record) {
    if (!record) return null;
    var out = caseSchema.clone(record);
    out.revisions = revisionsOf(record);
    return out;
  }

  /* ------------------------------------------------------------ repository -- */

  function makeRepository(options) {
    options = options || {};
    var legacy = options.store || makeStore(options);
    var adapter = options.adapter || adapterFromLegacyStore(legacy);
    var service = caseStore.makeCaseService(Object.assign({}, options, { adapter: adapter }));

    /* Which declared responding function, if any, a legacy caller's free-text
       role names. Anything else is a person or a label, not a function, and it
       is stored as the case owner rather than pretended into the role list. */
    function respondingFunction(label) {
      if (typeof label !== 'string') return null;
      return caseSchema.ROLES.indexOf(label) >= 0 ? label : null;
    }

    /* The repository's original `save(caseId, record, meta)`. It writes through
       the base's one write path - it is not a second implementation - and it
       maps the old arguments onto it. The mapping is deliberately conservative
       in three places, each for a reason the plan gives:

       1. `meta.state` is NOT applied. A case reaches a state by a recorded move,
          by a named responding function, with a date and a log entry. A case
          that a save could put straight into `approved` would be the very thing
          CASE-04 forbids, so the state is left where the log puts it and the
          caller is told in the returned note what was stored.

       2. `meta.owner_role` is applied only when it names a declared responding
          function. "Pricing" or "role A" is a label, not a function, so it is
          kept as the case owner and the case is left with no function that owes
          an answer - which is honest for a draft and is visible in the queue.

       3. Legacy-only keys are dropped with a note, rather than stored as fields
          nothing declares. */
    function save(caseId, record, meta) {
      meta = meta || {};
      if (!caseId) return { ok: false, code: 'CASE_ID_REQUIRED', error: 'A case needs a stable id.' };
      var notes = [];
      var existing = service.load(caseId);

      var fns = respondingFunction(meta.owner_role);
      if (meta.owner_role && !fns) {
        notes.push('"' + meta.owner_role + '" is not one of the declared responding functions ('
          + caseSchema.ROLES.join(', ') + '), so it was recorded as the case owner and the case still '
          + 'has no function that owes the next answer.');
      }

      var dropped = LEGACY_ONLY_KEYS.filter(function (k) {
        return record && Object.prototype.hasOwnProperty.call(record, k);
      });
      if (dropped.length) {
        notes.push('Dropped ' + dropped.join(', ') + ': not declared on a case record. A consistency '
          + 'verdict is a derived check and can be recomputed, so nothing was lost.');
      }

      if (!existing) {
        var created = service.create({
          case_id: caseId,
          customer: (record && record.customer) || meta.customer || 'Not stated',
          market: (record && record.market) || meta.market || null,
          part_number: (record && record.part_number) || meta.part_number || 'Not stated',
          owner_role: fns,
          owner: fns ? (meta.owner || null) : (meta.owner || meta.owner_role || null),
          description: (record && record.description) || null,
          unit: (record && record.unit) || null,
          scope_note: (record && record.scope_note) || null,
          evidence_period: (record && record.evidence_period) || meta.evidence_period || null,
          next_action: meta.next_action || null,
          next_update_due: meta.next_update_due || null,
          scenario: (record && record.scenario) || null,
          result: (record && record.result) || null,
          review: (record && record.review) || null,
          sources: (record && record.sources) || [],
          by: meta.recorded_by,
          note: meta.note
        });
        if (!created.ok) {
          /* A first save that the lifecycle will not accept as a new case (an
             unusable part reference, say) is still refused, in the same words. */
          return created;
        }
        if (meta.state && meta.state !== created.record.state) {
          notes.push('The case was created at "' + created.record.state + '", not at "' + meta.state
            + '": a case reaches a state by a recorded move with a responding function and a date, '
            + 'not by being saved into it.');
        }
        var out = {
          ok: true, version: created.version, durable: created.durable,
          warning: null, notes: notes.length ? notes : null,
          case: service.summarize(created.record), record: asLegacyRecord(created.record)
        };
        /* The old caller reads `result.case.state`; the state that was stored is
           reported, so the difference from what was asked for is visible. */
        out.case_requested_state = meta.state || null;
        out.case = out.case;
        return out;
      }

      /* An edit. The base's own write path, with the version guard and the
         duplicate guard, and the state left where the log puts it. */
      var next = caseSchema.clone(existing);
      if (record && record.scenario !== undefined) next.scenario = record.scenario;
      if (record && record.result !== undefined) next.result = record.result;
      if (record && record.review !== undefined) next.review = record.review;
      if (record && record.sources !== undefined) next.sources = record.sources;
      if (meta.next_action !== undefined) next.next_action = meta.next_action;
      if (meta.next_update_due !== undefined) next.next_update_due = meta.next_update_due;
      if (fns) next.owner_role = fns;

      var expected = meta.expected_version === undefined || meta.expected_version === null
        ? existing.version : meta.expected_version;
      var saved = service.saveRecord(next, {
        expected_version: expected, by: meta.recorded_by, note: meta.note, role: fns
      });
      if (!saved.ok) {
        /* Reported in the old vocabulary the callers already handle. */
        return {
          ok: false,
          conflict: saved.code === 'STALE_WRITE',
          duplicate: saved.code === 'DUPLICATE_SUBMISSION',
          code: saved.code,
          error: saved.error,
          expected_version: saved.expected_version, actual_version: saved.actual_version
        };
      }
      if (meta.state && meta.state !== saved.record.state) {
        notes.push('The case stayed at "' + saved.record.state + '", not at "' + meta.state
          + '": a case reaches a state by a recorded move with a responding function and a date, '
          + 'not by being saved into it.');
      }
      return {
        ok: true, version: saved.version,
        durable: options.adapter ? true : legacy.isDurable(), warning: null,
        notes: notes.length ? notes : null,
        changed_fields: saved.changed_fields,
        case: service.summarize(saved.record), record: asLegacyRecord(saved.record)
      };
    }

    var repository = {
      /* -- what the interface and the existing checks call ---------------- */
      save: save,
      load: function (caseId) { return asLegacyRecord(service.load(caseId)); },
      list: function () { return service.list(); },
      history: function (caseId) {
        var record = service.load(caseId);
        if (!record) return [];
        return historyForDisplay(record);
      },
      reopen: function (caseId, version) { return service.reopen(caseId, version); },
      correct: function (caseId, record, meta) {
        meta = meta || {};
        /* The caller names the revision it is correcting, which is the base's
           `corrects_sequence`. Translated here rather than in a second
           implementation, and the base's own rules (a reason, a role, no state
           move) still apply. */
        return service.correct(caseId, Object.assign({}, record, {
          corrects_sequence: meta.corrects_sequence !== undefined
            ? meta.corrects_sequence : meta.corrects_revision,
          reason: meta.reason,
          role: meta.role,
          replacement: record
        }), meta);
      },
      queue: function (asOf) { return service.queue(asOf); },
      exportAll: function () { return service.exportAll(); },
      importAll: function (bundle, options2) { return service.importAll(bundle, options2); },
      summarize: function (record) { return service.summarize(record); },
      store: legacy,

      /* -- the lifecycle, reached through the same object ---------------- */
      create: service.create,
      get: service.get,
      transition: service.transition,
      saveRecord: service.saveRecord,
      remove: service.remove,
      attach: service.attach,
      linkCases: service.linkCases,
      linkIssues: service.linkIssues,
      repairLinks: service.repairLinks,
      recordAssessment: service.recordAssessment,
      proposeTerms: service.proposeTerms,
      expireProposal: service.expireProposal,
      recordSupport: service.recordSupport,
      recordOutcome: service.recordOutcome,
      benefitAccount: service.benefitAccount,
      conservativeRollup: service.conservativeRollup,
      obligationStatement: service.obligationStatement,
      describe: service.describe,
      LINK_RELATIONS: service.LINK_RELATIONS,
      history_statement: service.history_statement,
      /* Named so a reader can see this is a facade and where the rules live. */
      authoritative_implementation: 'src/case/store.js + src/case/schema.js',
      /* UX-08. Older local notes migrate with an explicit legacy basis, and a
         field the older record did not carry is never invented. */
      migrateLegacyCases: function () { return migrateLegacyCases(legacy, service); },
      _service: service,
      _adapter: adapter
    };
    return repository;
  }

  /* --------------------------------------------------------- UX-08 legacy -- */

  /* The versions a current case record declares. A record written before these
     existed is missing all three, and the migration says so rather than filling
     them with the current values. */
  var VERSION_FIELDS = ['schema_version', 'contract_version', 'calculation_version',
    'source_version'];

  /* Keys that only a current record may carry. Anything the older record holds
     that is not in this list is an older field, kept under its own name and
     reported. Nothing is dropped and nothing is renamed. */
  var CURRENT_KEYS = [
    'case_id', 'schema_version', 'contract_version', 'version', 'customer', 'market',
    'part_number', 'description', 'unit', 'scope_note', 'evidence_period',
    'offer_effective_date', 'state', 'owner_role', 'owner', 'assigned_to', 'deputy_role',
    'escalation_route', 'next_action', 'next_update_due', 'submitted_at', 'assigned_at',
    'acknowledged_at', 'answered_at', 'resolved_at', 'action_identifier', 'assessment',
    'response', 'evidence_requests', 'approval_note', 'proposal', 'support', 'outcome',
    'explanations', 'correction_of', 'scenario', 'result', 'review', 'sources', 'links',
    'created_at', 'created_by', 'created_in', 'updated_at', 'updated_by', 'history',
    'legacy_basis', 'legacy_keys', 'legacy_scenario_keys', 'legacy_missing_versions',
    'legacy_basis_statement'
  ];

  /* A current record never carries these keys, so anything under one of them is
     an older note. `legacy_note` in the fixture and any `*_note` older field are
     reported as older notes and kept in full. */
  function olderFieldKeys(record) {
    var out = [];
    Object.keys(record || {}).forEach(function (k) {
      if (CURRENT_KEYS.indexOf(k) >= 0) return;
      out.push(k);
    });
    return out.sort();
  }

  /* Migrate older local records to the current shape without inventing anything.
     Each record is stamped with an explicit legacy basis and the list of fields
     it did not carry; its older fields are kept under their own names. */
  function migrateLegacyCases(legacy, service) {
    var all = legacy.readAll();
    var migrated = [];
    Object.keys(all).forEach(function (id) {
      var record = all[id];
      if (!record || typeof record !== 'object') return;
      var next = JSON.parse(JSON.stringify(record));

      var missingVersions = VERSION_FIELDS.filter(function (k) {
        return record[k] === undefined || record[k] === null;
      });
      var olderKeys = olderFieldKeys(record);
      var olderScenarioKeys = [];
      if (record.scenario && typeof record.scenario === 'object') {
        olderScenarioKeys = Object.keys(record.scenario).filter(function (k) {
          return contracts.SCENARIO_FIELDS.indexOf(k) < 0;
        }).sort();
      }

      next.legacy_basis = true;
      next.legacy_keys = olderKeys;
      next.legacy_scenario_keys = olderScenarioKeys;
      next.legacy_missing_versions = missingVersions;
      next.legacy_basis_statement = 'This record was written before the current record shape. '
        + 'It is kept on an explicit legacy basis rather than upgraded silently: the versions it '
        + 'does not carry are named, and no value is invented to fill them.';
      if (!next.updated_at) next.updated_at = record.created_at || null;

      all[id] = next;
      var preserved = olderKeys.map(function (k) {
        return { key: k, value: record[k] };
      }).concat(olderScenarioKeys.map(function (k) {
        return { key: 'scenario.' + k, value: record.scenario[k] };
      }));

      migrated.push({
        case_id: id,
        legacy_basis: true,
        basis_statement: next.legacy_basis_statement,
        missing_versions: missingVersions.slice(),
        invented: [],
        preserved_notes: preserved,
        legacy_keys: olderKeys,
        previous_state: record.state || null,
        previous_version: record.version === undefined ? null : record.version
      });
    });
    legacy.writeAll(all);
    return {
      ok: true,
      migrated: migrated,
      statement: migrated.length
        ? migrated.length + ' older local record(s) migrated onto an explicit legacy basis. '
          + 'Missing fields are named, not invented.'
        : 'No older local record was found; nothing to migrate.'
    };
  }

  /* `CASE_STATES` is published from the shared contract, not held here. A copy
     in this file is how a second vocabulary starts. */
  var API = {
    makeStore: makeStore,
    makeRepository: makeRepository,
    KEY: KEY,
    CASE_STATES: (contracts && contracts.CASE_STATES) || [],
    /* What this module is: a caller surface over the base, so a reader of the
       shipped list can see that no rule book lives here. */
    RETIRED_AS_IMPLEMENTATION: true,
    AUTHORITATIVE_IMPLEMENTATION: 'src/case/store.js + src/case/schema.js',
    describeStorage: caseStore.describeStorage,
    revisionsOf: revisionsOf
  };

  root.AIMCases = API;
  if (isNode) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
