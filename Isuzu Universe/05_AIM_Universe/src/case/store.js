/* ===========================================================================
   AIM case store - persistence, versioning and concurrent-edit control
   (CASE-01 ... CASE-08, RUN-01, RUN-04, RUN-07, F12).

   What v03 had
   ------------
   One JSON blob in browser storage under the key ISZE_AIM_PRICING_02. Saving
   again replaced the blob. Two people, or one person in two tabs, silently
   overwrote each other. There was no version, no owner, no history and no way
   to say what the case was before the last edit.

   What this file does
   -------------------
   It keeps one record per case, gives every accepted write a new version, keeps
   the write log append-only, and refuses a write that was prepared from an
   older version than the one on disk. It speaks to storage through a small
   adapter so the same code runs against a browser, against memory in a test,
   and against files on disk that genuinely survive a restart.

   Storage that exists today
   -------------------------
     memory     - a test, or a demonstration. Nothing survives.
     browser    - the same browser profile only. It survives a page reload, and
                  only sometimes a browser restart. It was never tested across a
                  real restart, so it is not claimed to be durable.
     files      - one JSON file per case in a folder. This one really does
                  survive a restart and is the default here.

   What none of them is
   --------------------
   None of these three is a shared service. Files on one machine are not a
   shared service either: two people on two machines do not see each other, and
   a file folder has no identity, no permission and no revocation. The adapter
   reports what it is in `describe()`, and the interface is the same one a
   server would implement, so moving to a server later does not change a case
   record or a caller.

   Concurrency
   -----------
   Optimistic, on the version number. A caller reads a record, keeps the version
   it read, and passes it back as `expected_version`. If the stored record has
   moved on, the write is refused with code `STALE_WRITE` and the caller is told
   what it would have overwritten. Nothing is merged silently and nothing is
   clobbered.
   =========================================================================== */
(function (root) {
  'use strict';

  var schema = (typeof module === 'object' && module.exports)
    ? require('./schema.js') : root.AIMCaseSchema;

  var INDEX_NAME = '_index.json';

  /* Key names that must never appear in a case record. Settings and credentials
     live outside this component (RUN-04); if one turns up inside a record the
     write is refused rather than stored. */
  var SECRET_LIKE = /(pass(word|phrase)|secret|token|api[_-]?key|client[_-]?secret|credential|bearer|private[_-]?key|cookie)/i;

  function scanForSecrets(value, path, found) {
    path = path || '';
    found = found || [];
    if (value === null || value === undefined) return found;
    if (Array.isArray(value)) {
      value.forEach(function (v, i) { scanForSecrets(v, path + '[' + i + ']', found); });
      return found;
    }
    if (typeof value === 'object') {
      Object.keys(value).forEach(function (k) {
        if (SECRET_LIKE.test(k)) found.push(path + '.' + k);
        scanForSecrets(value[k], path + '.' + k, found);
      });
    }
    return found;
  }

  function describeStorage(kind, extra) {
    var base = {
      memory: {
        kind: 'memory', durable: false, shared: false,
        statement: 'Held in this process only. Nothing survives the process ending.'
      },
      browser: {
        kind: 'browser', durable: false, shared: false,
        statement: 'Held in this browser profile only. Survives a page reload; a real browser '
          + 'restart was never tested, so it is not claimed.'
      },
      files: {
        kind: 'files', durable: true, shared: false,
        statement: 'One JSON file per case on this machine. Survives a restart. Not shared '
          + 'between people or machines, and it carries no identity of its own.'
      }
    }[kind] || { kind: kind, durable: false, shared: false, statement: 'Unknown storage.' };
    return Object.assign(base, extra || {});
  }

  /* ------------------------------------------------------ storage adapters -- */

  function makeMemoryAdapter(seed) {
    var data = seed ? JSON.parse(JSON.stringify(seed)) : {};
    return {
      describe: function () { return describeStorage('memory'); },
      readIndex: function () { return Object.keys(data).sort(); },
      load: function (id) { return data[id] ? JSON.parse(JSON.stringify(data[id])) : null; },
      loadAll: function () { return JSON.parse(JSON.stringify(data)); },
      save: function (id, record) { data[id] = JSON.parse(JSON.stringify(record)); return { ok: true }; },
      remove: function (id) { delete data[id]; return { ok: true }; }
    };
  }

  /* A Web Storage object (window.localStorage) is passed in, so this module can
     be tested without a browser. */
  function makeBrowserAdapter(storage) {
    if (!storage) throw new Error('makeBrowserAdapter needs a storage object such as window.localStorage.');
    var memory = {};
    var available = true;
    function readAll() {
      if (!available) return memory;
      try {
        var raw = storage.getItem(indexKey());
        return raw ? JSON.parse(raw) : {};
      } catch (e) { available = false; return memory; }
    }
    function writeAll(all) {
      memory = all;
      if (!available) return { ok: false, error: 'Browser storage refused the write.' };
      try { storage.setItem(indexKey(), JSON.stringify(all)); return { ok: true }; }
      catch (e) { available = false; return { ok: false, error: 'Browser storage refused the write: ' + e.message }; }
    }
    function indexKey() { return INDEX_NAME.replace('.json', '.browser'); }
    return {
      describe: function () {
        return describeStorage('browser', {
          durable: available,
          namespace: indexKey()
        });
      },
      readIndex: function () { return Object.keys(readAll()).sort(); },
      load: function (id) { var all = readAll(); return all[id] ? all[id] : null; },
      loadAll: function () { return readAll(); },
      save: function (id, record) { var all = readAll(); all[id] = record; return writeAll(all); },
      remove: function (id) { var all = readAll(); delete all[id]; return writeAll(all); }
    };
  }

  /* File storage. One file per case, plus an index of case ids. Each write goes
     to a temporary file first and is then moved into place, so a write that is
     interrupted leaves the previous version intact rather than half a file.
     This is the adapter that makes a durable record real on this machine. */
  function makeFileAdapter(options) {
    options = options || {};
    var dir = options.dir;
    if (!dir) throw new Error('makeFileAdapter needs a folder. Nothing was written.');
    if (typeof require !== 'function') {
      throw new Error('File storage is not available here. Use the browser adapter in a browser.');
    }
    var fs = require('fs');
    var path = require('path');
    var caseDir = path.join(dir, 'cases');

    function ensure() {
      fs.mkdirSync(caseDir, { recursive: true });
    }
    function casePath(id) {
      /* A case id becomes a file name, so it may not carry a path separator or
         climb out of the folder. */
      var safe = String(id).replace(/[^A-Za-z0-9._-]/g, '_');
      if (!safe || safe === '.' || safe === '..') throw new Error('Refusing an unusable case id: ' + id);
      return path.join(caseDir, safe + '.json');
    }
    function writeAtomic(target, object) {
      ensure();
      var tmp = target + '.tmp-' + process.pid + '-' + Date.now();
      fs.writeFileSync(tmp, JSON.stringify(object, null, 2), 'utf8');
      fs.renameSync(tmp, target);
    }
    return {
      dir: dir,
      describe: function () {
        return describeStorage('files', { folder: dir, index: path.join(dir, INDEX_NAME) });
      },
      readIndex: function () {
        ensure();
        var indexPath = path.join(dir, INDEX_NAME);
        if (!fs.existsSync(indexPath)) {
          /* Rebuild the index from the case files, so a missing index is not a
             lost case. */
          var found = fs.readdirSync(caseDir).filter(function (f) { return f.endsWith('.json'); })
            .map(function (f) { return f.slice(0, -5); });
          writeAtomic(indexPath, found);
          return found.sort();
        }
        return JSON.parse(fs.readFileSync(indexPath, 'utf8'));
      },
      load: function (id) {
        var p = casePath(id);
        if (!fs.existsSync(p)) return null;
        return JSON.parse(fs.readFileSync(p, 'utf8'));
      },
      loadAll: function () {
        var out = {};
        this.readIndex().forEach(function (id) {
          var r = null;
          try { r = JSON.parse(fs.readFileSync(path.join(caseDir, String(id).replace(/[^A-Za-z0-9._-]/g, '_') + '.json'), 'utf8')); }
          catch (e) { r = null; }
          if (r) out[id] = r;
        });
        return out;
      },
      save: function (id, record) {
        writeAtomic(casePath(id), record);
        var ids = this.readIndex();
        if (ids.indexOf(id) < 0) { ids.push(id); ids.sort(); }
        writeAtomic(path.join(dir, INDEX_NAME), ids);
        return { ok: true, durable: true };
      },
      remove: function (id) {
        var p = casePath(id);
        if (fs.existsSync(p)) fs.unlinkSync(p);
        var ids = this.readIndex().filter(function (x) { return x !== id; });
        writeAtomic(path.join(dir, INDEX_NAME), ids);
        return { ok: true };
      }
    };
  }

  /* ----------------------------------------------------------- the service -- */

  function reject(code, error, extra) {
    return Object.assign({ ok: false, code: code, error: error }, extra || {});
  }

  function makeCaseService(options) {
    options = options || {};
    var adapter = options.adapter;
    if (!adapter) throw new Error('makeCaseService needs a storage adapter.');
    var clock = options.now || function () { return new Date().toISOString(); };
    var caller = options.caller || 'unspecified';
    var devIdentityPrefix = options.identityMode === 'development-only' ? 'dev:' : '';

    var storage = adapter.describe();

    /* ------------------------------------------------------------- reads -- */

    function get(caseId) {
      if (!caseId) return null;
      return adapter.load(caseId);
    }

    function requireRecord(caseId) {
      var record = get(caseId);
      if (!record) return { error: reject('NO_SUCH_CASE', 'No case with id "' + caseId + '" is stored.') };
      var shape = schema.validate(record);
      if (!shape.ok) {
        return { error: reject('STORED_RECORD_INVALID',
          'The stored record for "' + caseId + '" does not satisfy the case schema: ' + shape.errors.join(' ')) };
      }
      return { record: record };
    }

    function list() {
      var ids = adapter.readIndex();
      return ids.map(function (id) {
        var r = adapter.load(id);
        if (!r) return null;
        return {
          case_id: r.case_id, version: r.version, state: r.state, stage: schema.stageOf(r.state),
          owner_role: r.owner_role, next_action: r.next_action, next_update_due: r.next_update_due,
          customer: r.customer, part_number: r.part_number,
          updated_at: r.updated_at, revisions: r.history.length,
          support_counted_eur: r.support ? r.support.support_eur : 0,
          outcome_recorded: !!r.outcome
        };
      }).filter(Boolean).sort(function (a, b) {
        return String(b.updated_at).localeCompare(String(a.updated_at));
      });
    }

    function history(caseId) {
      var found = requireRecord(caseId);
      if (found.error) return found.error;
      /* The whole log, including entries that were later corrected. A reader can
         see what was believed and when. */
      return found.record.history.map(function (h) { return schema.clone(h); });
    }

    /* What is open, who owes it and when (CASE-03). Overdue first. */
    function queue(asOfDate) {
      return list().map(function (row) {
        var record = adapter.load(row.case_id);
        return schema.openWork(record, asOfDate);
      }).filter(function (row) {
        return row && !row.closed && (row.next_action || row.next_update_due);
      }).sort(function (a, b) {
        if (a.overdue !== b.overdue) return a.overdue ? -1 : 1;
        return String(a.next_update_due || '9999-12-31').localeCompare(String(b.next_update_due || '9999-12-31'));
      });
    }

    /* Reopen the case as it was at a given version: the inputs, both results and
       what had been proposed, delivered and achieved at that point. Rebuilt from
       the log, so it is the case as it stood rather than a fresh calculation. */
    function reopen(caseId, version) {
      var found = requireRecord(caseId);
      if (found.error) return found.error;
      var record = found.record;
      var want = version === undefined || version === null ? record.version : version;
      if (want < 1 || want > record.version) {
        return reject('NO_SUCH_VERSION',
          'Version ' + want + ' does not exist on "' + caseId + '". The case is at version '
          + record.version + '.');
      }
      var rebuilt = schema.rebuildAt(record, want);
      if (!rebuilt) return reject('CANNOT_REBUILD', 'The log on "' + caseId + '" has nothing to rebuild from.');
      return {
        case_id: caseId,
        version: rebuilt.version,
        state: rebuilt.state,
        stage: schema.stageOf(rebuilt.state),
        scenario: rebuilt.scenario,
        result: rebuilt.result,
        review: rebuilt.review,
        support: rebuilt.support,
        outcome: rebuilt.outcome,
        approval_note: rebuilt.approval_note,
        next_action: rebuilt.next_action,
        next_update_due: rebuilt.next_update_due,
        as_at: rebuilt.updated_at,
        note: 'Rebuilt from the log at version ' + rebuilt.version + '. Not a recalculation.'
      };
    }

    /* ------------------------------------------------------------ writes -- */

    function guardSecrets(record) {
      var found = scanForSecrets(record, '');
      if (found.length) {
        return reject('SECRET_LIKE_FIELD',
          'This record carries what looks like a credential or a token: ' + found.join(', ')
          + '. Settings and secrets are kept outside the case store.');
      }
      return null;
    }

    function guardVersion(record, expectedVersion) {
      if (expectedVersion === undefined || expectedVersion === null) return null;
      if (record.version === expectedVersion) return null;
      return reject('STALE_WRITE',
        'Someone else changed this case after you opened it. You were working from version '
        + expectedVersion + ' and the stored record is at version ' + record.version
        + '. Nothing was written and nothing was overwritten. Reload the case and redo the change.',
        { expected_version: expectedVersion, actual_version: record.version });
    }

    /* Create a case. A second create on the same id is refused: it would make a
       second revision of someone else's decision. */
    function create(seed) {
      seed = Object.assign({}, seed, { by: devIdentityPrefix + (seed && seed.by ? seed.by : caller) });
      if (!seed.case_id) return reject('CASE_ID_REQUIRED', 'A case needs a stable id.');
      var existing = adapter.load(seed.case_id);
      if (existing) {
        return reject('CASE_ALREADY_EXISTS',
          'Case "' + seed.case_id + '" already exists at version ' + existing.version
          + '. Open it instead of starting a second one.');
      }
      var built = schema.emptyRecord(seed);
      if (!built.ok) return reject('INVALID_SEED', built.errors.join(' '));
      var secret = guardSecrets(built.record);
      if (secret) return secret;
      var written = adapter.save(seed.case_id, built.record);
      if (!written.ok) return reject('NOT_DURABLE', written.error || 'The store refused the write.');
      return { ok: true, record: built.record, storage: storage, durable: !!written.durable };
    }

    /* Write a whole record. Used by the case screen for a field edit as well as
       by a transition; the version guard and the duplicate guard are the same
       for both.

       An edit that changed something appends an entry to the log, naming the
       fields it set. That is what lets a reader rebuild the case at any earlier
       version instead of being told what it probably said. */
    function save(record, options2) {
      options2 = options2 || {};
      if (!record || !record.case_id) return reject('CASE_ID_REQUIRED', 'A case record needs its case_id.');
      var secret = guardSecrets(record);
      if (secret) return secret;
      var stored = adapter.load(record.case_id);
      if (!stored) {
        return reject('NO_SUCH_CASE',
          'No case "' + record.case_id + '" is stored. Create it before saving to it.');
      }
      var stale = guardVersion(stored, options2.expected_version);
      if (stale) return stale;

      var prepared = schema.clone(record);
      var at = clock();
      prepared.version = stored.version + 1;
      prepared.updated_at = at;
      prepared.updated_by = devIdentityPrefix + (options2.by || caller);

      /* The same content saved twice is refused, so a double click does not
         become a second revision that reads like a second decision. */
      if (schema.isDuplicateOf(stored, prepared)) {
        return reject('DUPLICATE_SUBMISSION',
          'That is the same content as version ' + stored.version + '. Nothing was saved and no new '
          + 'version was created. Change something, or close the case.');
      }

      /* What did this edit actually change? Recorded on the entry. */
      var changes = schema.diffFields(stored, prepared);
      var setFields = {};
      changes.forEach(function (c) { setFields[c.field] = prepared[c.field]; });
      var entry = {
        kind: 'edit',
        action: 'edit_case',
        from_state: stored.state,
        to_state: prepared.state,
        recorded_at: at,
        recorded_by: prepared.updated_by,
        role: options2.role || stored.owner_role,
        note: options2.note || ('Edited: ' + (changes.length ? changes.map(function (c) { return c.field; }).join(', ') : 'no field change')),
        commercial: false,
        event_id: null,
        correction_of: null,
        set_fields: setFields,
        stage: schema.stageOf(prepared.state),
        scenario: prepared.scenario || null,
        result: prepared.result || null,
        support: prepared.support || null,
        outcome: prepared.outcome || null,
        review: prepared.review || null,
        links: prepared.links || []
      };
      prepared.history = stored.history.concat([Object.assign({ seq: stored.history.length + 1 }, entry)]);

      var shape = schema.validate(prepared);
      if (!shape.ok) return reject('INVALID_RECORD', 'Refused: ' + shape.errors.join(' '));
      var written = adapter.save(record.case_id, prepared);
      if (!written.ok) return reject('NOT_DURABLE', written.error || 'The store refused the write.');
      return {
        ok: true, record: prepared, version: prepared.version,
        changed_fields: changes.map(function (c) { return c.field; }),
        storage: storage
      };
    }

    /* Move the case to its next state. The rule book is in schema.js; this
       wrapper adds the version guard, the clock and the caller's identity. */
    function transition(caseId, move, options2) {
      options2 = options2 || {};
      var found = requireRecord(caseId);
      if (found.error) return found.error;
      var stored = found.record;
      var stale = guardVersion(stored, options2.expected_version);
      if (stale) return stale;

      var fullMove = Object.assign({}, move, {
        at: clock(),
        by: devIdentityPrefix + (options2.by || move.by || caller)
      });
      var applied = schema.applyTransition(stored, fullMove);
      if (!applied.ok) return applied;

      var prepared = applied.record;
      if (schema.isDuplicateOf(stored, prepared)) {
        return reject('DUPLICATE_SUBMISSION',
          'That move would not change the record. Nothing was saved.');
      }
      var written = adapter.save(caseId, prepared);
      if (!written.ok) return reject('NOT_DURABLE', written.error || 'The store refused the write.');
      return {
        ok: true, record: prepared, version: prepared.version,
        action: applied.transition.action, state: prepared.state,
        stage: schema.stageOf(prepared.state), storage: storage
      };
    }

    /* A correction replaces its declared predecessor. The predecessor stays in
       the log, and the number of commercial occasions does not move. */
    function correct(caseId, correction, options2) {
      options2 = options2 || {};
      var found = requireRecord(caseId);
      if (found.error) return found.error;
      var stored = found.record;
      var stale = guardVersion(stored, options2.expected_version);
      if (stale) return stale;

      var fullCorrection = Object.assign({}, correction, {
        at: clock(),
        by: devIdentityPrefix + (correction && correction.by ? correction.by : caller)
      });
      var applied = schema.applyCorrection(stored, fullCorrection);
      if (!applied.ok) return applied;
      var written = adapter.save(caseId, applied.record);
      if (!written.ok) return reject('NOT_DURABLE', written.error || 'The store refused the write.');
      return {
        ok: true, record: applied.record, version: applied.record.version,
        corrected: correction.corrects_sequence,
        commercial_occasions: schema.commercialEventCount(applied.record),
        storage: storage
      };
    }

    /* ------------------------------------------------- case-to-case links -- */

    var LINK_RELATIONS = [
      'continues',     /* the same account and part, a later decision        */
      'replaces',      /* the earlier case is superseded by this one         */
      'migrates_to',   /* volume moved from another product to this one      */
      'split_from',    /* this case was carved out of a larger one           */
      'unrelated'      /* recorded so that a reader can see it was considered */
    ];

    function linkSpec(relation) {
      return schema.clone(LINK_RELATIONS.indexOf(relation) >= 0
        ? { relation: relation, counts_apart: relation !== 'migrates_to' && relation !== 'replaces',
            note: relation === 'migrates_to'
              ? 'One commercial occasion across two products. Not newly won business.'
              : relation === 'replaces'
                ? 'The same commercial question, restated. Counted once.'
                : 'Two separate decisions.' }
        : null);
    }

    /* Two cases are linked in both directions, in one step. Both sides are
       version-checked first: if either has moved, neither is written, so a link
       cannot be half-applied by this call. */
    function linkCases(firstId, secondId, relation, options2) {
      options2 = options2 || {};
      if (firstId === secondId) return reject('SELF_LINK', 'A case cannot be linked to itself.');
      if (LINK_RELATIONS.indexOf(relation) < 0) {
        return reject('UNKNOWN_RELATION', 'Unknown link relation "' + relation + '". Known: '
          + LINK_RELATIONS.join(', ') + '.');
      }
      var a = requireRecord(firstId);
      if (a.error) return a.error;
      var b = requireRecord(secondId);
      if (b.error) return b.error;
      var expected = options2.expected_versions || {};
      var staleA = guardVersion(a.record, expected[firstId]);
      if (staleA) return staleA;
      var staleB = guardVersion(b.record, expected[secondId]);
      if (staleB) return staleB;

      var at = clock();
      var by = devIdentityPrefix + (options2.by || caller);
      var spec = linkSpec(relation);
      var linkId = 'link:' + firstId + '<>' + secondId + ':' + relation;

      var preparedA = schema.applyLink(a.record, Object.assign({
        link_id: linkId, other_case_id: secondId, linked_at: at, linked_by: by
      }, spec), { at: at, by: by, role: schema.stageOf(a.record.state) ? a.record.owner_role : null });
      if (!preparedA.ok) return preparedA;
      var preparedB = schema.applyLink(b.record, Object.assign({
        link_id: linkId, other_case_id: firstId, linked_at: at, linked_by: by
      }, spec), { at: at, by: by, role: b.record.owner_role });
      if (!preparedB.ok) return preparedB;

      adapter.save(firstId, preparedA.record);
      adapter.save(secondId, preparedB.record);
      return {
        ok: true, relation: relation, spec: spec, link_id: linkId,
        records: [preparedA.record, preparedB.record],
        /* Stated plainly: two files are written, this is not a server
           transaction, and `linkIssues()` finds a half-written pair. */
        transactional: false,
        note: 'Recorded on both cases. This is not a server transaction; linkIssues() detects a half-written pair.'
      };
    }

    /* Is any link recorded on one side only? */
    function linkIssues() {
      var all = adapter.loadAll();
      var issues = [];
      Object.keys(all).forEach(function (id) {
        (all[id].links || []).forEach(function (link) {
          var other = all[link.other_case_id];
          if (!other) {
            issues.push({ case_id: id, link_id: link.link_id, problem: 'The other case is not in the store.' });
            return;
          }
          var mirrored = (other.links || []).some(function (l) { return l.link_id === link.link_id; });
          if (!mirrored) {
            issues.push({ case_id: id, link_id: link.link_id,
              problem: 'The link is recorded on ' + id + ' only; ' + link.other_case_id + ' does not carry it.' });
          }
        });
      });
      return { ok: issues.length === 0, issues: issues };
    }

    /* Write the missing half of any one-sided link. The repair goes in the log
       like any other change, so the case can still be rebuilt at any version. */
    function repairLinks(options2) {
      options2 = options2 || {};
      var found = linkIssues();
      var repaired = 0, unrepairable = [];
      found.issues.forEach(function (issue) {
        var all = adapter.loadAll();
        var owner = all[issue.case_id];
        if (!owner) return;
        var link = (owner.links || []).filter(function (l) { return l.link_id === issue.link_id; })[0];
        var other = all[link.other_case_id];
        if (!other) { unrepairable.push(issue); return; }
        var applied = schema.applyLink(other, Object.assign({}, link, {
          other_case_id: issue.case_id, linked_at: clock(), linked_by: 'link repair'
        }), { at: clock(), by: 'link repair', role: other.owner_role, note: 'Repaired a one-sided link' });
        if (!applied.ok) { unrepairable.push(Object.assign({}, issue, { error: applied.error })); return; }
        adapter.save(other.case_id, applied.record);
        repaired++;
      });
      return {
        ok: unrepairable.length === 0,
        repaired: repaired,
        unrepairable: unrepairable,
        remaining: linkIssues().issues.length
      };
    }

    /* --------------------------------------------------------- the rollup -- */

    /* CASE-05. One commercial occasion is counted once, across whichever cases
       and products it was recorded on. Volume migrated from another product is
       reported separately and is never added to newly won business. */
    function conservativeRollup(caseIds, asOfDate) {
      var ids = caseIds && caseIds.length ? caseIds : adapter.readIndex();
      var occasions = {};
      var migratedUnits = 0;
      var newBusinessUnits = 0;
      var unresolvedUnits = 0;
      var rows = [];

      ids.forEach(function (id) {
        var record = adapter.load(id);
        if (!record) return;
        var support = record.support ? record.support.support_eur : 0;
        var eventId = (record.support && record.support.event_id)
          || (record.outcome && record.outcome.event_id)
          || ('case:' + id);
        if (!occasions[eventId]) occasions[eventId] = { event_id: eventId, support_eur: 0, cases: [] };
        /* Support is added once per occasion, not once per case that names it. */
        if (!occasions[eventId].cases.length) occasions[eventId].support_eur += support;
        occasions[eventId].cases.push(id);

        var units = record.outcome && typeof record.outcome.quantity_after === 'number'
          ? record.outcome.quantity_after : null;
        if (units === null) {
          unresolvedUnits += 1;
        } else if (record.outcome.migration_from) {
          migratedUnits += units;
        } else if (record.outcome.counts_as_new_business === true) {
          newBusinessUnits += units;
        }
        rows.push({
          case_id: id, state: record.state, stage: schema.stageOf(record.state),
          occasion: eventId, support_eur: support,
          units: units,
          counted_as: units === null ? 'unresolved'
            : record.outcome.migration_from ? 'migrated from another product'
              : record.outcome.counts_as_new_business ? 'newly won' : 'not counted as new business'
        });
      });

      var occasionList = Object.keys(occasions).map(function (k) { return occasions[k]; });
      return {
        as_of: asOfDate || clock().slice(0, 10),
        cases: rows.length,
        distinct_commercial_occasions: occasionList.length,
        support_total_eur: occasionList.reduce(function (s, o) { return s + o.support_eur; }, 0),
        newly_won_units: newBusinessUnits,
        migrated_units_not_new_business: migratedUnits,
        cases_without_a_recorded_outcome: unresolvedUnits,
        occasions: occasionList,
        rows: rows,
        note: 'Support is counted once per commercial occasion. Volume migrated from another Isuzu '
          + 'product is reported on its own line and is not added to newly won business.'
      };
    }

    /* -------------------------------------------------- export and restore -- */

    function exportAll() {
      var all = adapter.loadAll();
      return {
        schema: 'isze-aim-cases',
        record_schema_version: schema.RECORD_SCHEMA_VERSION,
        exported_at: clock(),
        storage: storage,
        cases: all
      };
    }

    /* Restore from a bundle. An existing case is not silently replaced. */
    function importAll(bundle, options2) {
      options2 = options2 || {};
      if (!bundle || !bundle.cases) {
        return reject('NOT_A_BUNDLE', 'That is not a case bundle: it has no cases in it.');
      }
      var added = 0, skipped = [], refused = [];
      Object.keys(bundle.cases).forEach(function (id) {
        var candidate = bundle.cases[id];
        var shape = schema.validate(candidate);
        if (!shape.ok) { refused.push({ case_id: id, errors: shape.errors }); return; }
        var existing = adapter.load(id);
        if (existing) {
          if (!options2.overwrite) { skipped.push(id); return; }
          if (existing.version > candidate.version) {
            refused.push({ case_id: id, errors: ['The stored version ' + existing.version
              + ' is ahead of the bundle version ' + candidate.version + '. Not restoring.'] });
            return;
          }
        }
        adapter.save(id, candidate);
        added++;
      });
      return { ok: true, added: added, skipped: skipped, refused: refused,
        remaining: adapter.readIndex().length };
    }

    function remove(caseId, options2) {
      options2 = options2 || {};
      var found = requireRecord(caseId);
      if (found.error) return found.error;
      if (!options2.confirm_case_id || options2.confirm_case_id !== caseId) {
        return reject('DELETE_NEEDS_CONFIRMATION',
          'Deleting a case removes its history. Pass confirm_case_id as "' + caseId + '" to proceed.');
      }
      adapter.remove(caseId);
      return { ok: true, removed: caseId };
    }

    /* ------------------------------------------------ attachments (SAFE-06) -- */

    /* There is no server and no approved file store, so no attachment bytes are
       written anywhere by this component. What is implemented is the
       permission check and the record of the gap. */
    function attach(caseId, attachment, identity) {
      var found = requireRecord(caseId);
      if (found.error) return found.error;
      var output = outputModule();
      if (!output) {
        return reject('OUTPUT_MODULE_MISSING',
          'The permission check could not be loaded, so the attachment was not checked and was not stored.');
      }
      var permitted = output.canAttach(identity, attachment || {});
      var note = {
        case_id: caseId,
        declared_name: (attachment && attachment.name) || null,
        declared_restricted: !!(attachment && attachment.restricted),
        checked_at: clock(),
        permission: permitted.allowed ? 'permitted' : 'refused',
        reason: permitted.reason
      };
      if (!permitted.allowed) {
        return reject('ATTACHMENT_NOT_PERMITTED', permitted.error || permitted.reason, { check: note });
      }
      return {
        ok: true,
        stored: false,
        check: note,
        storage_gap: 'Attachment storage is not implemented. There is no approved file store or server for '
          + 'this component, so the bytes were not written and the case does not point at a file. The '
          + 'permission question was asked and answered; the storage question is recorded as unresolved.'
      };
    }

    return {
      storage: storage,
      describe: function () { return storage; },
      create: create,
      get: get,
      list: list,
      queue: queue,
      history: history,
      reopen: reopen,
      save: save,
      transition: transition,
      correct: correct,
      linkCases: linkCases,
      linkIssues: linkIssues,
      repairLinks: repairLinks,
      conservativeRollup: conservativeRollup,
      exportAll: exportAll,
      importAll: importAll,
      remove: remove,
      attach: attach,
      LINK_RELATIONS: LINK_RELATIONS,
      _adapter: adapter
    };
  }

  /* `attach` asks the output module whether a file may be attached. The same
     lookup the rest of the workspace uses, so this works both in Node and when
     the files are loaded as plain scripts in a browser. */
  function outputModule() {
    if (typeof module === 'object' && module.exports) return require('../output/recipients.js');
    return root.AIMOutput;
  }

  var API = {
    makeMemoryAdapter: makeMemoryAdapter,
    makeBrowserAdapter: makeBrowserAdapter,
    makeFileAdapter: makeFileAdapter,
    makeCaseService: makeCaseService,
    scanForSecrets: scanForSecrets,
    INDEX_NAME: INDEX_NAME
  };
  root.AIMCaseStore = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);