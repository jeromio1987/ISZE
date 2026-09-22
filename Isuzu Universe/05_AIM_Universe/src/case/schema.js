/* ===========================================================================
   AIM case record - the durable shape, the published states and the allowed
   moves (CASE-01 ... CASE-08, F12).

   Why this file exists
   --------------------
   v03 kept a case as one mutable object in browser storage. It had no version,
   no named owner, no append-only history, and one person saving silently
   overwrote another. A proposal, an approval, a delivery and an outcome were
   the same box with a different label on it, so closing an action could look
   like a second commercial event.

   What this file is
   -----------------
   A description of a case record and a rule book: which fields it may carry,
   which lifecycle states exist, which move is legal from which state, which
   role has to have made the move, and what the move has to supply before it is
   accepted. It performs no storage and no input/output. `store.js` persists
   what this file builds.

   Lifecycle stages (contracts.js CASE_STATES, unchanged)
   -----------------------------------------------------
   Each published state belongs to exactly one *stage*. The stages are what a
   reader has to be able to tell apart:

     prepare   draft, evidence_requested   - nothing has been asked of anyone yet
     proposal  ready_for_review            - an action is proposed, not accepted
     approval  approved                    - an owner accepted the stated action
     delivery  delivered                   - the agreed support was actually given
     outcome   outcome_recorded            - what the support achieved, once
     closed    rejected, no_change_recommended

   `stageOf()` is the single place that mapping lives. A test asserts that
   every state declared in `contracts.js` is mapped, so a new state added to
   the shared contract cannot appear here unnoticed.

   Reading a record
   ----------------
   `record.history` is append-only. Nothing in this module removes or rewrites
   an entry. A correction is appended and names the entry it replaces, so the
   decision taken on the earlier evidence stays visible instead of disappearing.
   =========================================================================== */
(function (root) {
  'use strict';

  var contracts = (typeof module === 'object' && module.exports)
    ? require('../data/contracts.js') : root.AIMContracts;

  /* Bumped when the stored shape changes in a way a reader must know about.
     Separate from the shared contract version in contracts.js. */
  var RECORD_SCHEMA_VERSION = 1;

  /* ------------------------------------------------------------- the shape -- */

  /* Everything a case record may carry. `store.js` refuses to persist a record
     with a key outside this list, so a caller cannot grow the stored shape by
     accident and a reader can enumerate what is held on a case. */
  var RECORD_FIELDS = [
    'case_id',            /* stable id; never reused for a different case      */
    'schema_version',     /* this file's shape version                         */
    'contract_version',   /* contracts.js version the record was written under  */
    'version',            /* increments on every accepted write                */
    'customer',           /* distributor or account the case is about          */
    'market',             /* reporting market, e.g. the country code           */
    'part_number',        /* the exact original part; never a rewritten one    */
    'description',
    'unit',
    'scope_note',         /* plain English: what this case does and does not cover */
    'evidence_period',    /* the recorded history period                       */
    'offer_effective_date', /* the date a proposed offer would take effect     */
    'state',              /* one of contracts.CASE_STATES                      */
    'owner_role',         /* the role that owes the next action                */
    'next_action',        /* plain English: what has to happen next            */
    'next_update_due',    /* YYYY-MM-DD; a date the reader can act on          */
    'evidence_requests',  /* what was asked for, of whom, due when             */
    'approval_note',      /* what an owner accepted, or why it was refused     */
    'support',            /* the support that was agreed and given, at most once */
    'outcome',            /* what the delivered support achieved, once          */
    'correction_of',      /* history entry this record's latest write replaces  */
    'scenario',           /* the proposed offer, per contracts.SCENARIO_FIELDS  */
    'result',             /* the calculated result, per contracts.RESULT_FIELDS */
    'review',             /* the reviewer's note and explanation               */
    'sources',            /* evidence references, per contracts.EVIDENCE_FIELDS */
    'links',              /* related cases, either direction, with the reason   */
    'created_at', 'created_by', 'created_in',
    'updated_at', 'updated_by',
    'history'             /* append-only log of every accepted move             */
  ];

  /* The sub-shape of one support delivery. Deliberately separate from the
     outcome: what was given, and what it achieved, are two different entries. */
  var SUPPORT_FIELDS = [
    'event_id',       /* identifies the one commercial occasion                */
    'support_eur',    /* one-off support, counted once                          */
    'delivered_on',   /* YYYY-MM-DD                                             */
    'what',           /* plain English description of what was given            */
    'by_role'         /* which role gave it                                     */
  ];

  /* The sub-shape of one recorded outcome. */
  var OUTCOME_FIELDS = [
    'event_id',                /* the same occasion the support belonged to     */
    'what',                    /* plain English: what the support achieved      */
    'observed_on',             /* YYYY-MM-DD                                    */
    'quantity_after',          /* observed volume, or null                      */
    'quantity_label',          /* observed history / stated commitment / manual */
    'migration_from',          /* the product migrated away from, or null       */
    'migration_to',            /* the product migrated to, or null              */
    'counts_as_new_business'   /* false when this is a migration                */
  ];

  /* The steps of the lifecycle that have their own recorded process, so that a
     proposal is not an approval, an approval is not a delivery, and a delivery
     is not an outcome. */
  var PROCESSES = [
    { stage: 'proposal', entered_by: 'submit_for_review', label: 'Action proposed for review' },
    { stage: 'approval', entered_by: 'approve', label: 'Action accepted by an owner' },
    { stage: 'delivery', entered_by: 'record_delivery', label: 'Agreed support given' },
    { stage: 'outcome', entered_by: 'record_outcome', label: 'Outcome recorded once' }
  ];

  /* ------------------------------------------------------------- the states -- */

  var STATE_STAGE = {
    draft: 'prepare',
    evidence_requested: 'prepare',
    ready_for_review: 'proposal',
    approved: 'approval',
    delivered: 'delivery',
    outcome_recorded: 'outcome',
    rejected: 'closed',
    no_change_recommended: 'closed'
  };

  var STAGES = ['prepare', 'proposal', 'approval', 'delivery', 'outcome', 'closed'];

  function stageOf(state) { return STATE_STAGE[state] || null; }

  /* States in which nothing further is owed to the case. */
  var TERMINAL_STATES = ['outcome_recorded', 'rejected', 'no_change_recommended'];

  function isTerminal(state) { return TERMINAL_STATES.indexOf(state) >= 0; }

  /* ------------------------------------------------------- the allowed moves -- */

  /* One row per legal move. `role` is the role that has to have made it: a
     reviewer cannot approve, and an approver cannot record a delivery. The
     named human identity behind a role is not decided here - see the export
     permission in `recipients.js` and the note at the end of this file. */
  var TRANSITIONS = [
    { action: 'request_evidence', from: 'draft', to: 'evidence_requested', role: 'reviewer',
      label: 'Evidence requested from a named role',
      requires: ['evidence_requests', 'next_action', 'next_update_due'] },
    { action: 'submit_for_review', from: 'draft', to: 'ready_for_review', role: 'case_owner',
      label: 'Action proposed for review',
      requires: ['scenario', 'next_action', 'next_update_due'] },
    { action: 'submit_for_review', from: 'evidence_requested', to: 'ready_for_review', role: 'case_owner',
      label: 'Action proposed for review',
      requires: ['scenario', 'next_action', 'next_update_due'] },
    { action: 'close_no_change', from: 'draft', to: 'no_change_recommended', role: 'reviewer',
      label: 'Closed with no change recommended', requires: ['approval_note'] },
    { action: 'close_no_change', from: 'evidence_requested', to: 'no_change_recommended', role: 'reviewer',
      label: 'Closed with no change recommended', requires: ['approval_note'] },

    /* The approval gap. Nothing reaches "approved" except an approver's move. */
    { action: 'approve', from: 'ready_for_review', to: 'approved', role: 'approver',
      label: 'Action accepted by an owner',
      requires: ['approval_note', 'next_action', 'next_update_due'] },
    { action: 'reject', from: 'ready_for_review', to: 'rejected', role: 'approver',
      label: 'Action refused by an owner', requires: ['approval_note'] },
    { action: 'return_for_more_work', from: 'ready_for_review', to: 'draft', role: 'reviewer',
      label: 'Returned to draft for more work', requires: ['approval_note'] },

    /* The delivery gap. Support is given once, against an approval. */
    { action: 'record_delivery', from: 'approved', to: 'delivered', role: 'support_owner',
      label: 'Agreed support given',
      requires: ['support', 'next_action', 'next_update_due'] },
    { action: 'withdraw_before_delivery', from: 'approved', to: 'rejected', role: 'approver',
      label: 'Approval withdrawn before any support was given', requires: ['approval_note'] },

    /* The outcome gap. The outcome is recorded after a delivery, not instead of
       one, and it is the same commercial occasion - not a second one. */
    { action: 'record_outcome', from: 'delivered', to: 'outcome_recorded', role: 'case_owner',
      label: 'Outcome recorded once', requires: ['outcome'] },

    { action: 'reopen_case', from: 'rejected', to: 'draft', role: 'case_owner',
      label: 'Closed case reopened for a new decision', requires: ['next_action'] },
    { action: 'reopen_case', from: 'no_change_recommended', to: 'draft', role: 'case_owner',
      label: 'Closed case reopened for a new decision', requires: ['next_action'] }
  ];

  /* A delivered-and-recorded case is finished. Reopening it is not offered,
     because that would let one occasion be run twice; a new case is the honest
     move and it gets its own commercial event. */
  var NO_REOPEN_FROM = ['outcome_recorded'];

  var ROLES = ['requester', 'case_owner', 'reviewer', 'approver', 'support_owner'];

  /* The fields a history entry may carry. Everything a move changed is recorded
     on the entry that changed it, so any earlier version of the case can be
     rebuilt exactly rather than approximately. */
  var ENTRY_FIELDS = [
    'seq', 'kind', 'action', 'from_state', 'to_state', 'recorded_at', 'recorded_by',
    'role', 'note', 'commercial', 'event_id', 'correction_of',
    'set_fields',          /* the field values this entry put on the record */
    'evidence_requests',   /* the request text as it stood after this entry */
    'approval_note',
    'support', 'outcome', 'review', 'links',
    'scenario', 'result'   /* carried or replaced by this entry, or null */
  ];

  /* A history entry carries a snapshot of the commercial content. Recorded on
     the entry so a reader can see exactly what was proposed, delivered and
     achieved at that step. */
  var ENTRY_SNAPSHOT_FIELDS = ['stage', 'scenario', 'result', 'support', 'outcome', 'review', 'links'];

  function transitionsFor(state, action) {
    return TRANSITIONS.filter(function (t) {
      return t.from === state && (!action || t.action === action);
    });
  }

  function findTransition(from, action) { return transitionsFor(from, action)[0] || null; }

  function nextActions(state) {
    return transitionsFor(state).map(function (t) {
      return { action: t.action, to: t.to, role: t.role, label: t.label, requires: t.requires.slice() };
    });
  }

  /* ------------------------------------------------------------- validation -- */

  var ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

  function isPlainObject(v) {
    return !!v && typeof v === 'object' && !Array.isArray(v)
      && Object.getPrototypeOf(v) === Object.prototype;
  }

  function isIsoDate(v) { return typeof v === 'string' && ISO_DATE.test(v) && !isNaN(Date.parse(v)); }

  /* A timestamp, not a date: ISO 8601 with a time part. */
  function isTimestamp(v) {
    return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(v) && !isNaN(Date.parse(v));
  }

  function isFiniteNumberOrNull(v) { return v === null || (typeof v === 'number' && Number.isFinite(v)); }

  function unknownFields(object, allowed) {
    var out = [];
    Object.keys(object || {}).forEach(function (k) {
      if (allowed.indexOf(k) < 0) out.push(k);
    });
    return out;
  }

  /* Structural check. Called by `store.js` before every write, so a bad record
     is refused at the boundary rather than persisted and discovered later. */
  function validate(record) {
    var errors = [];
    if (!isPlainObject(record)) return { ok: false, errors: ['A case record must be a plain object.'] };

    if (!record.case_id || typeof record.case_id !== 'string') errors.push('case_id is required.');
    if (typeof record.version !== 'number' || !Number.isInteger(record.version) || record.version < 1) {
      errors.push('version must be a whole number of at least 1.');
    }
    if (contracts.CASE_STATES.indexOf(record.state) < 0) {
      errors.push('Unknown state "' + record.state + '". State must be one of: '
        + contracts.CASE_STATES.join(', ') + '.');
    }
    if (!stageOf(record.state)) {
      errors.push('State "' + record.state + '" has no lifecycle stage. Add it to STATE_STAGE.');
    }
    if (!record.part_number || typeof record.part_number !== 'string') errors.push('part_number is required.');
    if (!record.customer || typeof record.customer !== 'string') errors.push('customer is required.');
    if (!record.owner_role || ROLES.indexOf(record.owner_role) < 0) {
      errors.push('owner_role must be one of: ' + ROLES.join(', ') + '.');
    }
    if (!isTimestamp(record.created_at)) errors.push('created_at must be an ISO timestamp.');
    if (!isTimestamp(record.updated_at)) errors.push('updated_at must be an ISO timestamp.');
    if (record.offer_effective_date !== null && record.offer_effective_date !== undefined
        && !isIsoDate(record.offer_effective_date)) {
      errors.push('offer_effective_date must be YYYY-MM-DD or null.');
    }
    if (record.next_update_due !== null && record.next_update_due !== undefined
        && !isIsoDate(record.next_update_due)) {
      errors.push('next_update_due must be YYYY-MM-DD or null.');
    }
    if (!Array.isArray(record.history) || record.history.length < 1) {
      errors.push('history must be a non-empty array: the record is its own log.');
    } else {
      var seenSeq = {};
      record.history.forEach(function (h, i) {
        if (h && h.seq !== i + 1) {
          errors.push('history entry ' + (i + 1) + ' carries seq ' + (h && h.seq)
            + '; the log must be gap-free and in order.');
        }
        if (h && seenSeq[h.seq]) errors.push('history seq ' + h.seq + ' appears twice.');
        if (h) seenSeq[h.seq] = 1;
      });
      /* One version, one log entry. Without this the version could climb while
         the log stood still, and "show me the case at version N" would have
         nothing to rebuild from. */
      if (typeof record.version === 'number' && record.history.length !== record.version) {
        errors.push('history holds ' + record.history.length + ' entries but the record is at version '
          + record.version + '. Every version is one entry; a change that does not say so is not recorded.');
      }
    }
    if (!isTerminal(record.state) && !record.next_action && record.state !== 'draft') {
      /* A case that is waiting on someone has to say what it is waiting for. */
      errors.push('An open case at "' + record.state + '" must state next_action.');
    }
    /* Explicitly null, never a silently accepted number. */
    if (record.support !== null && record.support !== undefined) {
      var supportProblems = unknownFields(record.support, SUPPORT_FIELDS);
      if (supportProblems.length) errors.push('support carries undeclared fields: ' + supportProblems.join(', ') + '.');
      if (!isFiniteNumberOrNull(record.support.support_eur) || record.support.support_eur === null) {
        errors.push('support.support_eur must be a finite number.');
      }
      if (record.support.support_eur < 0) errors.push('support.support_eur cannot be negative.');
      if (!isIsoDate(record.support.delivered_on)) errors.push('support.delivered_on must be YYYY-MM-DD.');
      if (!record.support.event_id) errors.push('support.event_id is required, so the occasion can be counted once.');
    }
    if (record.outcome !== null && record.outcome !== undefined) {
      var outcomeProblems = unknownFields(record.outcome, OUTCOME_FIELDS);
      if (outcomeProblems.length) errors.push('outcome carries undeclared fields: ' + outcomeProblems.join(', ') + '.');
      if (!record.outcome.event_id) errors.push('outcome.event_id is required; it ties the outcome to its delivery.');
      if (typeof record.outcome.counts_as_new_business !== 'boolean') {
        errors.push('outcome.counts_as_new_business must be true or false, never blank.');
      }
      if (record.outcome.migration_from && record.outcome.counts_as_new_business === true) {
        errors.push('An outcome that migrates from another product cannot count as newly won business.');
      }
    }
    /* The four stages must not be conflated in one record. */
    if (record.state === 'outcome_recorded' && !record.outcome) {
      errors.push('A case at outcome_recorded must carry its outcome.');
    }
    if (record.state === 'delivered' && !record.support) {
      errors.push('A case at delivered must carry the support that was given.');
    }
    if (record.state === 'approved' && record.support) {
      errors.push('A case at approved has not delivered its support yet; delivery is a separate move.');
    }
    var extra = unknownFields(record, RECORD_FIELDS);
    if (extra.length) {
      errors.push('Undeclared record fields refused: ' + extra.join(', ')
        + '. Add the field to RECORD_FIELDS first.');
    }
    return { ok: errors.length === 0, errors: errors };
  }

  /* --------------------------------------------------------------- building -- */

  function makeEventId(caseId, occasion) { return caseId + ':' + occasion; }

  function stamp(at) { return at || new Date().toISOString(); }

  function emptyRecord(seed) {
    seed = seed || {};
    var at = stamp(seed.at);
    var missing = ['case_id', 'customer', 'part_number', 'owner_role'].filter(function (k) {
      return !seed[k];
    });
    if (missing.length) {
      return { ok: false, errors: ['Cannot start a case without: ' + missing.join(', ') + '.'] };
    }
    if (ROLES.indexOf(seed.owner_role) < 0) {
      return { ok: false, errors: ['owner_role must be one of: ' + ROLES.join(', ') + '.'] };
    }
    var record = {
      case_id: seed.case_id,
      schema_version: RECORD_SCHEMA_VERSION,
      contract_version: contracts.CONTRACT_VERSION,
      version: 1,
      customer: seed.customer,
      market: seed.market || null,
      part_number: seed.part_number,
      description: seed.description || null,
      unit: seed.unit || 'unit',
      scope_note: seed.scope_note || null,
      evidence_period: seed.evidence_period || null,
      offer_effective_date: seed.offer_effective_date || null,
      state: 'draft',
      owner_role: seed.owner_role,
      next_action: seed.next_action || null,
      next_update_due: seed.next_update_due || null,
      evidence_requests: [],
      approval_note: null,
      support: null,
      outcome: null,
      correction_of: null,
      scenario: seed.scenario || null,
      result: seed.result || null,
      review: seed.review || null,
      sources: seed.sources || [],
      links: [],
      created_at: at,
      created_by: seed.by || 'unspecified',
      created_in: seed.created_in || 'unspecified',
      updated_at: at,
      updated_by: seed.by || 'unspecified',
      history: [{
        seq: 1, kind: 'created', action: 'create_case', from_state: null, to_state: 'draft',
        recorded_at: at, recorded_by: seed.by || 'unspecified', role: seed.owner_role,
        note: seed.note || null, commercial: false, event_id: null, correction_of: null,
        set_fields: null, evidence_requests: [], approval_note: null,
        stage: 'prepare', scenario: seed.scenario || null, result: seed.result || null,
        support: null, outcome: null, review: seed.review || null, links: []
      }]
    };
    var check = validate(record);
    return check.ok ? { ok: true, record: record } : { ok: false, errors: check.errors };
  }

  /* A link between two cases is a decision about them, so it goes in the log
     like any other change. Without this the version would climb while the log
     stayed still, and "rebuild the case at version N" would have nothing to
     rebuild from. */
  function applyLink(record, link, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var shape = validate(record);
    if (!shape.ok) return reject('INVALID_RECORD', 'The case record is not valid: ' + shape.errors.join(' '));
    if (!link || !link.link_id || !link.other_case_id) {
      return reject('LINK_NEEDS_ENDS', 'A link needs a link_id and the other case id.');
    }
    var at = stamp(meta.at);
    var next = clone(record);
    next.links = (record.links || []).filter(function (l) {
      return l.link_id !== link.link_id || l.other_case_id !== link.other_case_id;
    }).concat([clone(link)]);
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = meta.by || 'unspecified';

    next = appendEntry(next, {
      kind: 'link',
      action: 'link_case',
      from_state: record.state,
      to_state: record.state,
      recorded_at: at,
      recorded_by: meta.by || 'unspecified',
      role: meta.role || record.owner_role,
      note: meta.note || ('Linked to ' + link.other_case_id + ' as "' + link.relation + '"'),
      /* A link is not a commercial event: it changes how two cases read
         together, not what was delivered. */
      commercial: false,
      event_id: null,
      correction_of: null,
      set_fields: { links: next.links },
      stage: stageOf(next.state),
      scenario: next.scenario || null,
      result: next.result || null,
      support: next.support || null,
      outcome: next.outcome || null,
      review: next.review || null,
      links: next.links
    });

    var check = validate(next);
    if (!check.ok) return reject('LINK_WOULD_BE_INVALID', 'The link would leave an invalid record: ' + check.errors.join(' '));
    return { ok: true, record: next };
  }

  /* A copy with a fresh history array, so a caller cannot mutate a record that
     a store is holding. Cheap deep copy: records are small and JSON-safe by
     construction (validate refuses anything else). */
  function clone(record) { return record === null || record === undefined ? record : JSON.parse(JSON.stringify(record)); }

  /* ------------------------------------------------------------- the moves -- */

  function reject(code, error, extra) {
    return Object.assign({ ok: false, code: code, error: error }, extra || {});
  }

  function appendEntry(record, entry) {
    var next = clone(record);
    next.history.push(Object.assign({ seq: next.history.length + 1 }, entry));
    return next;
  }

  /* Has a commercial occasion already been recorded on this case? This is the
     guard that stops one delivery or one closure being counted twice. */
  function commercialEvents(record) {
    var byId = {};
    (record.history || []).forEach(function (h) {
      if (!h || !h.commercial || !h.event_id) return;
      if (!byId[h.event_id]) byId[h.event_id] = { event_id: h.event_id, entries: [], corrected: false };
      byId[h.event_id].entries.push(h.seq);
      if (h.correction_of) byId[h.event_id].corrected = true;
    });
    return Object.keys(byId).map(function (k) { return byId[k]; });
  }

  /* Count of distinct commercial occasions. One delivery plus a correction of
     that delivery is one occasion, not two. */
  function commercialEventCount(record) { return commercialEvents(record).length; }

  function requiredProblems(record, move, transition) {
    var problems = [];
    transition.requires.forEach(function (field) {
      var value = field in move ? move[field] : record[field];
      if (value === undefined || value === null || value === '') {
        problems.push('"' + transition.action + '" needs ' + field + '.');
      }
    });
    if (transition.requires.indexOf('evidence_requests') >= 0) {
      var reqs = (move.evidence_requests || record.evidence_requests || []);
      if (!Array.isArray(reqs) || !reqs.length) {
        problems.push('request_evidence needs at least one entry saying what was asked for, of whom, and when it is due.');
      } else {
        reqs.forEach(function (r, i) {
          if (!r || !r.what || !r.from_role || !isIsoDate(r.due)) {
            problems.push('evidence_requests[' + i + '] needs what, from_role and a due date in YYYY-MM-DD.');
          }
        });
      }
    }
    if (transition.action === 'record_delivery') {
      var s = move.support || record.support;
      if (!s) problems.push('record_delivery needs the support that was given.');
      else {
        if (typeof s.support_eur !== 'number' || !Number.isFinite(s.support_eur) || s.support_eur < 0) {
          problems.push('The delivered support needs a support_eur that is a finite number of zero or more.');
        }
        if (!isIsoDate(s.delivered_on)) problems.push('The delivered support needs delivered_on as YYYY-MM-DD.');
        if (!s.what) problems.push('The delivered support needs a plain English description of what was given.');
      }
    }
    if (transition.action === 'record_outcome') {
      var o = move.outcome || record.outcome;
      if (!o) problems.push('record_outcome needs the outcome.');
      else {
        if (!o.what) problems.push('The outcome needs a plain English description of what the support achieved.');
        if (!isIsoDate(o.observed_on)) problems.push('The outcome needs observed_on as YYYY-MM-DD.');
        if (typeof o.counts_as_new_business !== 'boolean') {
          problems.push('The outcome must state counts_as_new_business as true or false.');
        }
        if (o.migration_from && o.counts_as_new_business === true) {
          problems.push('Volume migrated from another product is not newly won business. '
            + 'Record counts_as_new_business as false, or leave the outcome unresolved.');
        }
      }
    }
    if (transition.requires.indexOf('next_update_due') >= 0) {
      var due = 'next_update_due' in move ? move.next_update_due : record.next_update_due;
      if (due !== undefined && due !== null && !isIsoDate(due)) {
        problems.push('next_update_due must be YYYY-MM-DD.');
      }
    }
    return problems;
  }

  /* Apply one move. Returns a new record; the input is never written to.
     Every rejection names what is wrong in plain words. */
  function applyTransition(record, move) {
    move = move || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var shape = validate(record);
    if (!shape.ok) return reject('INVALID_RECORD', 'The case record is not valid: ' + shape.errors.join(' '));

    /* The role is checked first. Whether a move is even available at this state
       is a separate question, and the answer to "who are you" should not depend
       on it: a reviewer that tries to approve is told it is not their move, not
       that the state does not offer it. */
    if (!move.action) return reject('NO_ACTION', 'A move needs an action.');
    var transition = findTransition(record.state, move.action);
    if (!transition) {
      if (NO_REOPEN_FROM.indexOf(record.state) >= 0) {
        return reject('CASE_IS_FINISHED',
          'This case is at "' + record.state + '". An outcome already recorded is the end of this case; '
          + 'start a new case for a new decision, so the same occasion is not run twice.');
      }
      var available = nextActions(record.state).map(function (t) { return t.action; });
      return reject('NOT_ALLOWED_FROM_STATE',
        '"' + move.action + '" is not allowed from "' + record.state + '". '
        + (available.length ? 'Allowed here: ' + available.join(', ') + '.' : 'Nothing further is allowed here.'));
    }
    if (!move.role || ROLES.indexOf(move.role) < 0) {
      return reject('ROLE_REQUIRED', '"' + transition.action + '" must be recorded by a role, one of: '
        + ROLES.join(', ') + '.');
    }
    if (move.role !== transition.role) {
      return reject('ROLE_NOT_PERMITTED',
        '"' + transition.action + '" is recorded by a ' + transition.role + ' role. '
        + 'A ' + move.role + ' cannot make this move.');
    }

    var problems = requiredProblems(record, move, transition);
    if (problems.length) return reject('MISSING_INPUT', problems.join(' '));

    /* Support is given once. A second delivery on the same case is refused
       rather than recorded, so the activity is not multiplied. Checked before
       the record is built, so the reason returned is the duplicate and not a
       downstream validation complaint. */
    if (transition.action === 'record_delivery' && commercialEventCount(record) > 0) {
      return reject('DUPLICATE_SUPPORT',
        'Support has already been recorded on this case as ' + commercialEvents(record)
          .map(function (e) { return e.event_id; }).join(', ')
        + '. A further support payment is a new decision, not a second delivery on this one.');
    }

    var at = stamp(move.at);
    var next = clone(record);
    next.state = transition.to;
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = move.by || 'unspecified';

    /* Exactly the fields this move set, and nothing else. The history entry
       below carries them, so the case can be rebuilt at any earlier version. */
    var setFields = { state: next.state };

    if (transition.action === 'request_evidence') {
      next.evidence_requests = (move.evidence_requests || []).map(function (r) {
        return { what: r.what, from_role: r.from_role, due: r.due, asked_at: at };
      });
      setFields.evidence_requests = next.evidence_requests;
    }
    if (transition.action === 'approve' || transition.action === 'reject'
        || transition.action === 'close_no_change' || transition.action === 'return_for_more_work'
        || transition.action === 'withdraw_before_delivery') {
      next.approval_note = move.approval_note;
      setFields.approval_note = next.approval_note;
    }
    if (transition.action === 'record_delivery') {
      var support = move.support || record.support;
      next.support = {
        event_id: support.event_id || makeEventId(record.case_id, 'delivery:' + (commercialEventCount(record) + 1)),
        support_eur: support.support_eur,
        delivered_on: support.delivered_on,
        what: support.what,
        by_role: support.by_role || move.role
      };
      setFields.support = next.support;
    }
    if (transition.action === 'record_outcome') {
      var outcome = move.outcome || record.outcome;
      next.outcome = {
        event_id: outcome.event_id || (record.support && record.support.event_id) || null,
        what: outcome.what,
        observed_on: outcome.observed_on,
        quantity_after: outcome.quantity_after === undefined ? null : outcome.quantity_after,
        quantity_label: outcome.quantity_label || null,
        migration_from: outcome.migration_from || null,
        migration_to: outcome.migration_to || null,
        counts_as_new_business: outcome.counts_as_new_business
      };
      setFields.outcome = next.outcome;
    }
    if (move.scenario !== undefined) { next.scenario = move.scenario; setFields.scenario = next.scenario; }
    if (move.result !== undefined) { next.result = move.result; setFields.result = next.result; }
    if (move.review !== undefined) { next.review = move.review; setFields.review = next.review; }
    if (move.next_action !== undefined) { next.next_action = move.next_action; setFields.next_action = next.next_action; }
    if (move.next_update_due !== undefined) { next.next_update_due = move.next_update_due; setFields.next_update_due = next.next_update_due; }
    if (move.owner_role !== undefined) { next.owner_role = move.owner_role; setFields.owner_role = next.owner_role; }
    if (move.evidence_period !== undefined) { next.evidence_period = move.evidence_period; setFields.evidence_period = next.evidence_period; }
    if (move.offer_effective_date !== undefined) { next.offer_effective_date = move.offer_effective_date; setFields.offer_effective_date = next.offer_effective_date; }

    /* A move that closes the case owes nothing further. */
    if (isTerminal(next.state)) {
      next.next_action = null;
      next.next_update_due = null;
      setFields.next_action = null;
      setFields.next_update_due = null;
    }

    next = appendEntry(next, {
      kind: 'transition',
      action: transition.action,
      from_state: record.state,
      to_state: next.state,
      recorded_at: at,
      recorded_by: move.by || 'unspecified',
      role: move.role,
      note: move.note || transition.label,
      commercial: transition.action === 'record_delivery',
      /* One occasion, one id. A later correction of this entry carries the same
         id, so dedupe keeps the count at one. */
      event_id: next.support ? next.support.event_id : null,
      correction_of: null,
      set_fields: setFields,
      /* The state of the commercial content after this move, so a rebuild at
         this version is exact and not a guess. */
      stage: stageOf(next.state),
      scenario: next.scenario || null,
      result: next.result || null,
      support: next.support || null,
      outcome: next.outcome || null,
      review: next.review || null,
      links: next.links || []
    });

    var check = validate(next);
    if (!check.ok) return reject('WOULD_BE_INVALID', 'That move would leave an invalid record: ' + check.errors.join(' '));
    return { ok: true, record: next, transition: transition };
  }

  /* A correction names the entry it replaces. It never deletes the earlier
     entry and it never adds a commercial occasion. */
  function applyCorrection(record, correction) {
    correction = correction || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var seq = correction.corrects_sequence;
    if (typeof seq !== 'number' || !Number.isInteger(seq)) {
      return reject('CORRECTION_NEEDS_TARGET',
        'A correction must name the history entry it replaces, by sequence number.');
    }
    if (!correction.role || ROLES.indexOf(correction.role) < 0) {
      return reject('ROLE_REQUIRED', 'A correction must be recorded by a role, one of: ' + ROLES.join(', ') + '.');
    }
    if (!correction.reason) {
      return reject('CORRECTION_NEEDS_REASON', 'A correction must say, in plain English, what it corrects and why.');
    }
    var target = (record.history || []).filter(function (h) { return h.seq === seq; })[0];
    if (!target) {
      return reject('NO_SUCH_HISTORY_ENTRY',
        'History entry ' + seq + ' is not on this case, so there is nothing to correct.');
    }
    if (target.correction_of) {
      return reject('TARGET_ALREADY_CORRECTED',
        'History entry ' + seq + ' is itself a correction of entry ' + target.correction_of
        + '. Correct the entry underneath it, or correct this correction by naming it.');
    }
    var alreadyCorrecting = (record.history || []).some(function (h) {
      return h.kind === 'correction' && h.correction_of === seq;
    });
    if (alreadyCorrecting) {
      return reject('TARGET_ALREADY_CORRECTED',
        'History entry ' + seq + ' has already been corrected. Correct the correction instead, '
        + 'so the trail stays a single line.');
    }

    var at = stamp(correction.at);
    var next = clone(record);
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = correction.by || 'unspecified';
    next.correction_of = seq;

    /* A correction may replace a stated value. It may not move the case: an
       outcome already recorded is not un-recorded by editing a word. The state
       check comes before anything is written to `next`, so a refused correction
       leaves no half-applied change behind. */
    var setFields = {};
    if (correction.replacement !== undefined) {
      var replacement = correction.replacement || {};
      if ('state' in replacement && replacement.state !== record.state) {
        return reject('CORRECTION_CANNOT_MOVE_STATE',
          'A correction fixes evidence; it does not move the case. '
          + 'The case is at "' + record.state + '" and you asked to make it "'
          + replacement.state + '". Use a transition for that.');
      }
      var refused = [];
      Object.keys(replacement).forEach(function (k) {
        if (RECORD_FIELDS.indexOf(k) < 0) { refused.push(k); return; }
        if (k === 'history' || k === 'version' || k === 'state' || k === 'case_id') return;
        next[k] = replacement[k];
        setFields[k] = replacement[k];
      });
      if (refused.length) {
        return reject('CORRECTION_NAMES_UNDECLARED_FIELDS',
          'A correction cannot write fields the record does not declare: ' + refused.join(', ') + '.');
      }
    }
    if (correction.review !== undefined) {
      next.review = Object.assign({}, record.review || {}, {
        correction: correction.reason,
        corrected_at: at,
        corrected_by: correction.by || 'unspecified'
      });
      setFields.review = next.review;
    }

    next = appendEntry(next, {
      kind: 'correction',
      action: 'correct_history_entry',
      from_state: record.state,
      to_state: record.state,
      recorded_at: at,
      recorded_by: correction.by || 'unspecified',
      role: correction.role,
      note: correction.reason,
      /* Carried through, so a corrected delivery is still the same occasion. */
      commercial: !!target.commercial,
      event_id: target.event_id || null,
      correction_of: seq,
      set_fields: setFields,
      stage: stageOf(next.state),
      scenario: next.scenario || null,
      result: next.result || null,
      support: next.support || null,
      outcome: next.outcome || null,
      review: next.review || null,
      links: next.links || []
    });

    var check = validate(next);
    if (!check.ok) return reject('WOULD_BE_INVALID', 'That correction would leave an invalid record: ' + check.errors.join(' '));
    return { ok: true, record: next };
  }

  /* Which top-level fields a write changed. Names and values, so an edit entry
     can say what it touched without carrying a second copy of the record. */
  function diffFields(before, after) {
    var changes = [];
    RECORD_FIELDS.forEach(function (k) {
      if (k === 'version' || k === 'updated_at' || k === 'updated_by' || k === 'history') return;
      var a = before ? before[k] : undefined;
      var b = after ? after[k] : undefined;
      if (JSON.stringify(a === undefined ? null : a) !== JSON.stringify(b === undefined ? null : b)) {
        changes.push({ field: k, from: a === undefined ? null : a, to: b === undefined ? null : b });
      }
    });
    return changes;
  }

  /* Build the case as it was after a given history entry. This is what makes
     "reopen the case at the version I saved" honest rather than approximate:
     every entry carries the fields it set and the commercial content as it
     stood, so nothing has to be guessed. */
  function rebuildAt(record, sequence) {
    if (!record) return null;
    var entries = record.history.slice(0, sequence);
    if (!entries.length) return null;
    var rebuilt = {
      case_id: record.case_id,
      schema_version: record.schema_version,
      contract_version: record.contract_version,
      version: entries[entries.length - 1].seq,
      customer: record.customer,
      market: record.market,
      part_number: record.part_number,
      description: record.description,
      unit: record.unit,
      scope_note: record.scope_note,
      evidence_period: null,
      offer_effective_date: null,
      state: 'draft',
      owner_role: record.owner_role,
      next_action: null,
      next_update_due: null,
      evidence_requests: [],
      approval_note: null,
      support: null,
      outcome: null,
      correction_of: null,
      scenario: null,
      result: null,
      review: null,
      sources: record.sources || [],
      links: [],
      created_at: record.created_at,
      created_by: record.created_by,
      created_in: record.created_in,
      updated_at: entries[entries.length - 1].recorded_at,
      updated_by: entries[entries.length - 1].recorded_by,
      history: entries
    };
    entries.forEach(function (entry) {
      var set = entry.set_fields || {};
      Object.keys(set).forEach(function (k) { rebuilt[k] = clone(set[k]); });
      /* Where an entry did not carry a field forward, fall back to the entry's
         own snapshot. */
      if (entry.to_state) rebuilt.state = entry.to_state;
      if (entry.stage) rebuilt.stage_at_entry = entry.stage;
      ['scenario', 'result', 'support', 'outcome', 'review', 'links'].forEach(function (k) {
        if (entry[k] !== null && entry[k] !== undefined) rebuilt[k] = clone(entry[k]);
      });
      if (entry.evidence_requests && entry.evidence_requests.length) {
        rebuilt.evidence_requests = clone(entry.evidence_requests);
      }
      if (entry.approval_note !== null && entry.approval_note !== undefined) {
        rebuilt.approval_note = entry.approval_note;
      }
    });
    delete rebuilt.stage_at_entry;
    return rebuilt;
  }

  /* A write that changes nothing is refused, so a double click cannot become a
     second revision that looks like a second decision. */
  function contentDigest(record) {
    var copy = clone(record) || {};
    delete copy.version;
    delete copy.updated_at;
    delete copy.updated_by;
    if (copy.history) copy.history = copy.history.map(function (h) {
      var c = clone(h);
      delete c.recorded_at;
      delete c.recorded_by;
      delete c.seq;
      return c;
    });
    var text = JSON.stringify(copy);
    /* Deterministic, synchronous, and the same in a browser and in Node, so the
       duplicate check cannot disagree with itself between the two. */
    var h = 0x811c9dc5;
    for (var i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
    }
    return ('0000000' + h.toString(16)).slice(-8);
  }

  function isDuplicateOf(previous, candidate) {
    if (!previous) return false;
    return contentDigest(previous) === contentDigest(candidate);
  }

  /* ------------------------------------------------------- what is owed now -- */

  /* CASE-03. A reader has to be able to see who owes the next action and when.
     Nothing here decides whether the work happened; it reports what the record
     says is due. */
  function openWork(record, asOfDate) {
    if (!record) return null;
    var today = asOfDate || new Date().toISOString().slice(0, 10);
    var due = record.next_update_due || null;
    return {
      case_id: record.case_id,
      state: record.state,
      stage: stageOf(record.state),
      closed: isTerminal(record.state),
      owner_role: record.owner_role,
      next_action: record.next_action,
      next_update_due: due,
      overdue: !!(due && !isTerminal(record.state) && due < today),
      due_today: !!(due && due === today),
      waiting_on: (record.evidence_requests || []).filter(function (r) {
        return r.due >= today;
      }).map(function (r) { return { what: r.what, from_role: r.from_role, due: r.due }; })
    };
  }

  /* The distinct stages a reader must be able to tell apart, in order. */
  function stageEvidence(record) {
    return {
      proposal_recorded: record.history.some(function (h) { return h.action === 'submit_for_review'; }),
      approval_recorded: record.history.some(function (h) { return h.action === 'approve'; }),
      delivery_recorded: record.history.some(function (h) { return h.action === 'record_delivery'; }),
      outcome_recorded: record.history.some(function (h) { return h.action === 'record_outcome'; }),
      commercial_occasions: commercialEventCount(record)
    };
  }

  var API = {
    RECORD_SCHEMA_VERSION: RECORD_SCHEMA_VERSION,
    RECORD_FIELDS: RECORD_FIELDS,
    SUPPORT_FIELDS: SUPPORT_FIELDS,
    OUTCOME_FIELDS: OUTCOME_FIELDS,
    ENTRY_FIELDS: ENTRY_FIELDS,
    ROLES: ROLES,
    STAGES: STAGES,
    STATE_STAGE: STATE_STAGE,
    TERMINAL_STATES: TERMINAL_STATES,
    PROCESSES: PROCESSES,
    TRANSITIONS: TRANSITIONS,
    stageOf: stageOf,
    isTerminal: isTerminal,
    transitionsFor: transitionsFor,
    findTransition: findTransition,
    nextActions: nextActions,
    unknownFields: unknownFields,
    validate: validate,
    emptyRecord: emptyRecord,
    clone: clone,
    contentDigest: contentDigest,
    isDuplicateOf: isDuplicateOf,
    applyTransition: applyTransition,
    applyCorrection: applyCorrection,
    applyLink: applyLink,
    rebuildAt: rebuildAt,
    diffFields: diffFields,
    commercialEvents: commercialEvents,
    commercialEventCount: commercialEventCount,
    openWork: openWork,
    stageEvidence: stageEvidence,
    isIsoDate: isIsoDate,
    isTimestamp: isTimestamp
  };

  root.AIMCaseSchema = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);

/* ---------------------------------------------------------------------------
   What this file deliberately does not decide

   `role` says which function made a move - a reviewer, an approver, a support
   owner. It does not say which human being is behind that role. Real identity,
   the tenant an identity belongs to, and revocation of an identity all need a
   server, and there is no approved server for this component yet. The export
   path carries the one permission check that can be unit-tested today; see
   `src/case/../output/recipients.js`.

   Where a role is checked here it is a rule about the record. It is not a
   security control, and it is not presented as one.
   ------------------------------------------------------------------------- */