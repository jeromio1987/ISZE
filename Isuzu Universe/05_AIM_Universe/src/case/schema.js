/* ===========================================================================
   AIM case record - the durable shape, the states now in force and the allowed
   moves (CASE-01 ... CASE-08, F12).

   Why this file exists
   --------------------
   v03 kept a case as one mutable object in browser storage. It had no version,
   no named owner, no append-only history, and one person saving silently
   overwrote another. A proposal, an approval, a delivery and an outcome were
    10|   the same box with a different label on it, so closing an action could look
   like a second commercial event.

   What this file is
   -----------------
   A description of a case record and a rule book: which fields it may carry,
   which lifecycle states exist, which move is legal from which state, which
   responding function has to have made the move, and what the move has to
   supply before it is accepted. It performs no storage and no input/output.
   `store.js` persists what this file builds.

   The state vocabulary (contracts.js version 4, CASE_STATES_TARGET)
    20|   -----------------------------------------------------------------
   A case here is a two-way exchange with a dealer or distributor, not a
   proposal travelling one way. The nine states are the ones the plan's CASE-02
   names, and this file is where they came into force. Every one of them is in
   contracts.CASE_STATES, which the shared contract publishes; this file checks
   that at load time so the two cannot drift apart.

     draft                  being prepared. Nothing is owed by anyone yet.
     submitted              sent. The clock CASE-03 measures starts here.
     assessment             the responsible function is working on it.
     awaiting_input         waiting on someone else, and on a stated thing.
     response_issued        an answer has gone back. NOT support, NOT a result.
     action_agreed          the parties agreed an action. Nothing is delivered.
     resolved               finished, and the outcome is known.
     withdrawn              taken back by the side that raised it.
     closed_outcome_unknown finished, and nobody knows what came of it.

   Two properties of that set matter and are asserted by tests, not just
   documented:

     * `closed_outcome_unknown` is a real permitted end state. A case can finish
       without anyone knowing the result, and this file refuses to infer one.
     * NO STATE CARRIES A MONETARY VALUE. Issuing a response is not delivered
       support, agreeing an action is not a won outcome, and closing a case
       creates no benefit. `monetaryWeightOf()` returns zero for every state and
       a test asserts it, so a later state cannot quietly acquire a euro value.

   Lifecycle stages
   ----------------
   Each state belongs to exactly one *stage*. The stages are what a reader has
    50|   to be able to tell apart:

     prepare     draft                      - nothing asked of anyone yet
     submitted   submitted                  - sent, not yet picked up
     assessment  assessment, awaiting_input - being worked, or waiting on input
     response    response_issued            - an answer, with nothing delivered
     agreed      action_agreed              - an action agreed, nothing delivered
     closed      resolved, withdrawn, closed_outcome_unknown

   `stageOf()` is the single place that mapping lives, and a test asserts that
   every state in contracts.CASE_STATES is mapped, so a new shared state cannot
   appear here unnoticed.

   Four steps that are NOT states
   ------------------------------
   Evidence, support, customer outcome and the recorded explanation each have
  60|   their own move and their own log entry, and none of them is a lifecycle
   state. That is deliberate. A support payment recorded after the case closed
   must not move the case, and an outcome recorded months later must not reopen
   it. They are recorded, dated, attributed and counted, and the case stays
   where it was.

   Reading a record
   ----------------
   `record.history` is append-only. Nothing in this module removes or rewrites
   an entry. A correction is appended and names the entry it replaces, so the
   decision taken on the earlier evidence stays visible instead of disappearing.

   What this file deliberately does not claim
    70|   -----------------------------------------
   The log is append-only *within this module*. It is not tamper-proof
   certification: there is no server, no signature and no trusted clock, and a
   person with write access to the file can edit it. `appendOnlyStatement()`
   says so in plain words and the store publishes it. Nothing here should be
   read as an audit control.
   =========================================================================== */
(function (root) {
  'use strict';

  var contracts = (typeof module === 'object' && module.exports)
    ? require('../data/contracts.js') : root.AIMContracts;

  /* Bumped when the stored shape changes in a way a reader must know about.
     Version 2 is the 2026-09-22 change that brought the plan's nine states into
     force and added the separate evidence, support and outcome records.
     Separate from the shared contract version in contracts.js. */
  var RECORD_SCHEMA_VERSION = 2;

  /* ------------------------------------------------------------- the shape -- */

  /* Everything a case record may carry. `store.js` refuses to persist a record
     with a key outside this list, so a caller cannot grow the stored shape by
     accident and a reader can enumerate what is held on a case.

     Fields marked `declared:` are also named in contracts.CASE_FIELDS. The few
     that are not are listed in `UNDECLARED_IN_CONTRACTS` below and reported to
     the contract's owner rather than added here silently - see the note there
     for what it costs today. */
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
    'owner_role',         /* the responding function that owns the case, declared */
    'owner',              /* the named owner, declared                          */
    'assigned_to',        /* who at that function is answering, declared        */
    'deputy_role',        /* who answers when the owner does not, declared      */
    'escalation_route',   /* where it goes if the owner does not answer, declared */
    'next_action',        /* plain English: what has to happen next            */
    'next_update_due',    /* YYYY-MM-DD; a date the reader can act on, declared */
    /* The separate clocks CASE-03 requires. Declared in contracts as
       CASE_TIMESTAMPS. They are NOT collapsed into one "updated at": the
       difference between them is the whole point - how long the dealer waited,
       and how long ISZE took, are different numbers. */
    'submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at',
    'action_identifier',  /* the stable id one action keeps in every module    */
    'assessment',         /* what was assessed, on what basis                  */
    'response',           /* the answer issued to the dealer, separate from support */
    'evidence_requests',  /* what was asked, of whom, due when                 */
    'approval_note',      /* what an owner accepted, or why it was refused     */
    'proposal',           /* the versioned proposal section                    */
    'support',            /* the support actually delivered, at most once      */
    'outcome',            /* what the delivered support achieved, once         */
    'explanations',       /* CASE-06: what a contributor said, in their words  */
    'correction_of',      /* history entry this record's latest write replaces */
    'scenario',           /* the proposed offer, per contracts.SCENARIO_FIELDS */
    'result',             /* the calculated result, per contracts.RESULT_FIELDS */
    'review',             /* the reviewer's note and explanation               */
    'sources',            /* evidence references, per contracts.EVIDENCE_FIELDS */
    'links',              /* related cases, either direction, with the reason   */
    'created_at', 'created_by', 'created_in',
    'updated_at', 'updated_by',
    'history'             /* append-only log of every accepted move             */
  ];

  /* Fields this file needs that version 4 of the shared contract does not
     declare. Reported to the contract's owner; not added here by the workflow
     developer, because editing contracts.js is not this task's to do.

     What it costs today: `src/data/export.js` builds the internal record's
     allowlist from `contracts.declaredFields()` plus its own three envelope
     names, so a stored case record carrying one of these would have it trimmed
     out of an exported record - the same silent-empty-section fault that
     contract version 3 was written to close. Measured today, no live path is
     affected: `src/ui/app.js` builds the export object from the payload case,
     not from the stored case record, so none of these fields reaches the
     export. It becomes a real gap the moment an export reads a stored case.

     `evidence_requests` is in the same position and is already used by the
     shipping lifecycle. */
  var UNDECLARED_IN_CONTRACTS = [
    'assessment', 'response', 'evidence_requests', 'proposal.versions[].terms.currency',
    'support.net_terms_basis', 'support.credit_reference', 'support.beneficiary',
    'support.comparison', 'support.period', 'outcome.evidence', 'outcome.measures',
    'outcome.unresolved_reason', 'action_identifier'
  ];

  /* The sub-shape of one support delivery. Deliberately separate from the
     outcome: what was given, and what it achieved, are two different entries.

     `action_identifier` is what stops one result being counted twice. The same
     commercial action is referred to by AIM, IDS, PRISM and SPA; they all carry
     the same identifier, and the benefit account counts the identifier once. */
  var SUPPORT_FIELDS = [
    'action_identifier',   /* the stable id of the action this support pays for */
    'support_eur',         /* one-off support, already in net terms, counted once */
    'net_terms_basis',     /* 'net of credit already given' or 'gross, credit not yet applied' */
    'credit_reference',    /* the credit note, or null. A credit is not profit. */
    'order_reference',     /* the order this relates to, or null                */
    'delivery_reference',  /* the delivery this relates to, or null             */
    'beneficiary',         /* who received it                                    */
    'comparison',          /* what it is measured against, or null              */
    'period',              /* the period the support covers                     */
    'delivered_on',        /* YYYY-MM-DD                                        */
    'what',                /* plain English description of what was given        */
    'by_role'              /* which responding function gave it                  */
  ];

  /* The sub-shape of one recorded outcome.

     `measures` keeps the four things apart that must never be added together:
     the difference in purchase cost, the gross profit, the capacity released,
     and what the programme itself spent. A reader gets four lines, not one
     score. The benefit account below returns them separately and refuses to
     total them. */
  var OUTCOME_FIELDS = [
    'action_identifier',       /* the same action the support belonged to       */
    'what',                    /* plain English: what the support achieved      */
    'observed_on',             /* YYYY-MM-DD                                    */
    'quantity_before',         /* observed volume before, or null               */
    'quantity_after',          /* observed volume after, or null                */
    'quantity_label',          /* observed history / stated commitment / manual */
    'migration_from',          /* the product migrated away from, or null       */
    'migration_to',            /* the product migrated to, or null              */
    'counts_as_new_business',  /* false when this is a migration                */
    'evidence',                /* what the outcome is based on, listed          */
    'measures',                /* the four measures, kept apart                 */
    'unresolved_reason'        /* why the outcome is unknown, when it is         */
  ];

  var MEASURE_FIELDS = [
    'purchase_cost_difference_eur',
    'gross_profit_eur',
    'capacity_released_units',
    'programme_expenditure_eur'
  ];

  /* CASE-05: the outcome's own evidence. */
  var OUTCOME_EVIDENCE_FIELDS = ['kind', 'reference', 'observed_on', 'value', 'note'];

  /* CASE-04: the proposed terms, and how far they got.

     A proposal is versioned. An amendment carries the version it amends, so the
     former terms stay readable rather than being overwritten - the fault that
     made "what did we offer in August?" unanswerable in v03. */
  var PROPOSAL_FIELDS = [
    'proposal_version',
    'proposed_on',             /* YYYY-MM-DD                                    */
    'proposal_state',          /* draft | proposed | amended | accepted: the approval fact */
    /* Whether the version can still be used. Deliberately SEPARATE from
       proposal_state. An approved offer that lapses was still approved - the
       decision was taken and the record of it must not be rewritten - so
       expiring one sets `availability` and leaves the approval where it is. A
       reader then sees both facts: it was accepted, and it is no longer
       available. Collapsing the two would either lose the approval or leave an
       expired offer usable. */
    'availability',            /* available | expired                           */
    'terms',                   /* the proposed terms, per PROPOSAL_TERM_FIELDS */
    'offered_by_role',
    'note',
    'amends_proposal_version', /* the version this one replaces, or null        */
    'expires_on',              /* YYYY-MM-DD, or null for no expiry             */
    'expired_on',              /* the date it was stopped being offered         */
    'expiry_decision',         /* what was decided when it expired, in plain words */
    'approval_route',          /* who has to approve this, in plain words       */
    'approval_note',           /* what the approver said, when one did          */
    'approval_reference',      /* the genuine approval reference, only when supplied */
    'approved_by_role',
    'approved_on',
    'synthetic_approval',      /* true only for a clearly-labelled local exercise */
    'candidate_keys'           /* what it was derived from, so ranking is inspectable */
  ];

  var PROPOSAL_TERM_FIELDS = [
    'unit', 'price_before', 'price_after', 'quantity_before', 'quantity_after',
    'quantity_label', 'currency', 'conditions', 'eligible_reference',
    'offer_effective_date', 'support_eur', 'support_direction'
  ];

  /* CASE-02: the assessment, kept separate from the response. An assessment is
     internal thinking; a response is what the dealer was told. */
  var ASSESSMENT_FIELDS = ['what', 'basis', 'by_role', 'on', 'findings'];

  /* CASE-02: the response issued to the dealer.

     `commitment` is the field that stops a response being read as support. It is
     'none' for a position statement and 'support' only when the response itself
     commits support - and support may not be recorded unless it does. */
  var RESPONSE_FIELDS = ['what', 'issued_on', 'by_role', 'reference', 'commitment'];

  /* ------------------------------------------------------------- the states -- */

  /* IN FORCE. The nine states the plan's CASE-02 names, taken from the
     vocabulary the shared contract declares for this component.

     Why the in-force list is built here rather than read from
     `contracts.CASE_STATES`: version 4 of the shared contract still publishes
     the RETIRED eight (`draft, evidence_requested, ready_for_review, approved,
     rejected, delivered, outcome_recorded, no_change_recommended`) in
     `CASE_STATES`, and publishes these nine in `CASE_STATES_TARGET` marked "not
     yet in force". The swap belongs in `contracts.js`, which this work does not
     own. So the list that `validate`, `TRANSITIONS` and `STATE_STAGE` actually
     enforce is built from the target, and the divergence from
     `contracts.CASE_STATES` is measured and published as
     `CONTRACT_VOCABULARY_STALE` rather than hidden. See docs/CASE_service.md,
     "What is open", item 1 - it is a one-line change in a file this developer
     must not edit, and it is the only thing standing between this file and the
     shared contract being in step. */
  var CASE_STATES = (contracts.CASE_STATES_TARGET || contracts.CASE_STATES).slice();

  /* The retired list, kept so the divergence can be named and counted instead of
     asserted away. */
  var CASE_STATES_RETIRED = contracts.CASE_STATES.slice();

  var CONTRACT_VOCABULARY_STALE = CASE_STATES_RETIRED.length !== CASE_STATES.length
    || CASE_STATES_RETIRED.some(function (s, i) { return s !== CASE_STATES[i]; });

  var STATE_STAGE = {
    draft: 'prepare',
    submitted: 'submitted',
    assessment: 'assessment',
    awaiting_input: 'assessment',
    response_issued: 'response',
    action_agreed: 'agreed',
    resolved: 'closed',
    withdrawn: 'closed',
    closed_outcome_unknown: 'closed'
  };

  var STAGES = ['prepare', 'submitted', 'assessment', 'response', 'agreed', 'closed'];

  function stageOf(state) { return STATE_STAGE[state] || null; }

  /* States in which nothing further is owed to the case. */
  var TERMINAL_STATES = ['resolved', 'withdrawn', 'closed_outcome_unknown'];

  function isTerminal(state) { return TERMINAL_STATES.indexOf(state) >= 0; }

  /* States where nothing is owed to anyone, so an empty next_action is honest
     rather than an omission. Every other state has to say what is owed. */
  var NO_NEXT_ACTION_STATES = ['draft', 'awaiting_input'];

  /* States in which the case does not yet have a responding function. A draft
     may be an unrouted note; once it is submitted, somebody owes the answer. */
  var NO_OWNER_REQUIRED_STATES = ['draft'];

  /* CASE-02, asserted rather than asserted-about: no state is worth money. A
     case that issues a response has not delivered support; one that agrees an
     action has not won anything; one that closes has created no benefit. If a
     later state were to acquire a euro value, a reader would start summing
     states, and that is the double count this whole component exists to stop. */
  var STATE_MONETARY_WEIGHT = {};
  CASE_STATES.forEach(function (s) { STATE_MONETARY_WEIGHT[s] = 0; });

  function monetaryWeightOf(state) {
    if (!Object.prototype.hasOwnProperty.call(STATE_MONETARY_WEIGHT, state)) return null;
    return STATE_MONETARY_WEIGHT[state];
  }

  /* ------------------------------------------------------- the allowed moves -- */

  /* One row per legal move. `role` is the responding function that has to have
     made it. The named human identity behind a function is not decided here -
     see the note at the end of this file.

     Reading the list: nothing reaches `action_agreed` except an approver's own
     move on a named proposal version, and nothing reaches `resolved` except a
     recorded outcome. Those two edges are the ones the plan's acceptance
     criteria name, and they cannot be reached by saving. */
  var TRANSITIONS = [
    /* -- getting in ------------------------------------------------------- */
    { action: 'submit', from: 'draft', to: 'submitted', role: 'case_owner',
      label: 'Sent to the responsible function',
      requires: ['next_action', 'next_update_due'] },
    { action: 'withdraw', from: 'draft', to: 'withdrawn', role: 'requester',
      label: 'Withdrawn by the side that raised it', requires: ['approval_note'] },

    /* -- assessment ------------------------------------------------------- */
    { action: 'begin_assessment', from: 'submitted', to: 'assessment', role: 'reviewer',
      label: 'Assessment started by the responsible function',
      requires: ['next_action', 'next_update_due'] },
    { action: 'request_input', from: 'submitted', to: 'awaiting_input', role: 'reviewer',
      label: 'Input requested from a named function', requires: ['evidence_requests'] },
    { action: 'request_input', from: 'assessment', to: 'awaiting_input', role: 'reviewer',
      label: 'Input requested from a named function', requires: ['evidence_requests'] },
    { action: 'provide_input', from: 'awaiting_input', to: 'assessment', role: 'case_owner',
      label: 'Input supplied; assessment continues',
      requires: ['next_action', 'next_update_due'] },
    /* The dealer pulling its own question back, while it is being assessed. */
    { action: 'withdraw', from: 'submitted', to: 'withdrawn', role: 'requester',
      label: 'Withdrawn by the side that raised it', requires: ['approval_note'] },
    { action: 'withdraw', from: 'assessment', to: 'withdrawn', role: 'requester',
      label: 'Withdrawn by the side that raised it', requires: ['approval_note'] },
    { action: 'withdraw', from: 'awaiting_input', to: 'withdrawn', role: 'requester',
      label: 'Withdrawn by the side that raised it', requires: ['approval_note'] },

    /* -- the response. An answer, not a delivery. ------------------------- */
    { action: 'issue_response', from: 'assessment', to: 'response_issued', role: 'case_owner',
      label: 'An answer has been sent to the dealer',
      requires: ['response', 'next_action', 'next_update_due'] },
    { action: 'issue_response', from: 'awaiting_input', to: 'response_issued', role: 'case_owner',
      label: 'An answer has been sent to the dealer',
      requires: ['response', 'next_action', 'next_update_due'] },

    /* -- the agreed action, and how a case ends --------------------------- */
    { action: 'accept_proposal', from: 'response_issued', to: 'action_agreed', role: 'approver',
      label: 'The proposed action was accepted by an approver',
      requires: ['proposal', 'approval_note', 'next_action', 'next_update_due'] },
    { action: 'terminal_no_change', from: 'response_issued', to: 'closed_outcome_unknown',
      role: 'case_owner',
      label: 'Answered, considered, and no action taken. The commercial outcome is not known.',
      requires: ['approval_note'] },
    { action: 'withdraw', from: 'response_issued', to: 'withdrawn', role: 'requester',
      label: 'Withdrawn by the side that raised it', requires: ['approval_note'] },
    /* An agreed action that is then dropped. The outcome of the dropped action
       is not known, and this state says so rather than calling it a loss or a
       gain. */
    { action: 'terminal_no_change', from: 'action_agreed', to: 'closed_outcome_unknown',
      role: 'case_owner',
      label: 'Agreed action not taken. The commercial outcome is not known.',
      requires: ['approval_note'] },
    { action: 'withdraw', from: 'action_agreed', to: 'withdrawn', role: 'requester',
      label: 'Withdrawn by the side that raised it', requires: ['approval_note'] },

    /* The one edge into `resolved`. Support and outcome are recorded by their own
       moves first; this closes a case that has an outcome. It carries no euro
       value, because the outcome already carries the outcome. */
    { action: 'close_resolved', from: 'action_agreed', to: 'resolved', role: 'case_owner',
      label: 'Closed with the outcome recorded', requires: ['outcome'] }
  ];

  /* A case that reached an end is not reopened here. Reopening would let one
     commercial action be run twice; a new case, linked to the first, is the
     honest move and it gets its own action identifier. */
  var NO_REOPEN_FROM = TERMINAL_STATES.slice();

  /* The responding functions. Who owes the next action is answered with one of
     these. `dealer` is in the list on purpose: a dealer commitment is also an
     obligation, and CASE-03 requires it to be readable separately from ISZE's
     own. */
  var ROLES = ['requester', 'dealer', 'case_owner', 'reviewer', 'approver',
    'support_owner', 'finance', 'product', 'supply'];

  /* The function that has to own the case at each state. A submitted case always
     has somebody whose turn it is; there is no state where the answer is
     "nobody". Draft is absent because a draft may be unrouted. */
  var OWNER_BY_STATE = {
    submitted: 'reviewer',
    assessment: 'reviewer',
    awaiting_input: 'reviewer',
    response_issued: 'case_owner',
    action_agreed: 'case_owner',
    resolved: 'case_owner',
    withdrawn: 'case_owner',
    closed_outcome_unknown: 'case_owner'
  };

  /* The fields a history entry may carry. Everything a move changed is recorded
     on the entry that changed it, so any earlier version of the case can be
     rebuilt exactly rather than approximately. */
  var ENTRY_FIELDS = [
    'seq', 'kind', 'action', 'from_state', 'to_state', 'recorded_at', 'recorded_by',
    'role', 'note', 'commercial', 'event_id', 'correction_of',
    'set_fields',          /* the field values this entry put on the record */
    'evidence_requests',   /* the request text as it stood after this entry */
    'approval_note',
    'assessment', 'response', 'proposal', 'support', 'outcome', 'review', 'links',
    'scenario', 'result'   /* carried or replaced by this entry, or null */
  ];

  /* A history entry carries a snapshot of the commercial content. Recorded on
     the entry so a reader can see exactly what was proposed, delivered and
     achieved at that step. */
  var ENTRY_SNAPSHOT_FIELDS = ['stage', 'scenario', 'result', 'assessment', 'response',
    'proposal', 'support', 'outcome', 'review', 'links'];

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
    if (CASE_STATES.indexOf(record.state) < 0) {
      errors.push('Unknown state "' + record.state + '". State must be one of: '
        + CASE_STATES.join(', ') + '.');
    }
    if (!stageOf(record.state)) {
      errors.push('State "' + record.state + '" has no lifecycle stage. Add it to STATE_STAGE.');
    }
    if (!record.part_number || typeof record.part_number !== 'string') errors.push('part_number is required.');
    if (!record.customer || typeof record.customer !== 'string') errors.push('customer is required.');

    /* Who owes the next action. A case that is with somebody must name the
       function, not leave it to the reader to infer from the state. */
    if (NO_OWNER_REQUIRED_STATES.indexOf(record.state) < 0) {
      if (!record.owner_role || ROLES.indexOf(record.owner_role) < 0) {
        errors.push('owner_role must be one of: ' + ROLES.join(', ') + '. The case is at "'
          + record.state + '", so a responding function has to be named.');
      }
    } else if (record.owner_role && ROLES.indexOf(record.owner_role) < 0) {
      errors.push('owner_role must be one of: ' + ROLES.join(', ') + '.');
    }
    ['deputy_role'].forEach(function (k) {
      if (record[k] !== null && record[k] !== undefined && ROLES.indexOf(record[k]) < 0) {
        errors.push(k + ' must be one of: ' + ROLES.join(', ') + ', or null.');
      }
    });

    /* The stable action identifier. One action, one id, whatever module refers
       to it - that is what stops it being counted twice. */
    if (record.action_identifier !== null && record.action_identifier !== undefined
        && !isActionIdentifier(record.action_identifier)) {
      errors.push('action_identifier must be a stable identifier such as "ACT:CASE-1" or '
        + '"ACT-2026-001". Got: ' + JSON.stringify(record.action_identifier) + '.');
    }

    if (!isTimestamp(record.created_at)) errors.push('created_at must be an ISO timestamp.');
    if (!isTimestamp(record.updated_at)) errors.push('updated_at must be an ISO timestamp.');

    /* The separate clocks stay separate. Each is checked for the shape it claims
       to be, and each is checked for order, because a clock that runs backwards
       is a data fault a reader would otherwise have to notice. */
    var clocks = (contracts.CASE_TIMESTAMPS || []).slice();
    clocks.forEach(function (k) {
      var v = record[k];
      if (v === null || v === undefined) return;
      if (!isTimestamp(v)) { errors.push(k + ' must be an ISO timestamp or null.'); return; }
      if (Date.parse(v) < Date.parse(record.created_at)) {
        errors.push(k + ' is earlier than the case was created, so it cannot be right.');
      }
    });
    ['submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at'].reduce(function (prev, k) {
      var v = record[k];
      if (v === null || v === undefined) return prev;
      if (prev && Date.parse(v) < Date.parse(prev.at)) {
        errors.push(k + ' (' + v + ') is earlier than ' + prev.k + ' (' + prev.at
          + '). The clocks are separate but they cannot run backwards.');
      }
      return { k: k, at: v };
    }, null);

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
    if (NO_NEXT_ACTION_STATES.indexOf(record.state) < 0 && !isTerminal(record.state)
        && !record.next_action) {
      /* A case that is with somebody has to say what they owe. `awaiting_input`
         is exempt because the thing owed is the requested input, which is listed
         under evidence_requests, and repeating it as next_action would give two
         sources for one obligation. */
      errors.push('An open case at "' + record.state + '" must state next_action.');
    }
    if (record.state === 'awaiting_input'
        && (!Array.isArray(record.evidence_requests) || !record.evidence_requests.length)) {
      errors.push('A case at awaiting_input must say what was asked for, of whom, and when it is due.');
    }

    /* Evidence requests, including the dealer's own commitments. */
    if (record.evidence_requests !== undefined && record.evidence_requests !== null) {
      if (!Array.isArray(record.evidence_requests)) {
        errors.push('evidence_requests must be an array.');
      } else {
        record.evidence_requests.forEach(function (r, i) {
          if (!r || !r.what) errors.push('evidence_requests[' + i + '] needs what was asked for.');
          if (r && r.from_role && ROLES.indexOf(r.from_role) < 0) {
            errors.push('evidence_requests[' + i + '].from_role must be one of: ' + ROLES.join(', ') + '.');
          }
        });
      }
    }

    /* The assessment, the response and the support are three different records.
       Each says what it is and refuses to carry the next one's meaning. */
    if (record.assessment !== null && record.assessment !== undefined) {
      var ap = unknownFields(record.assessment, ASSESSMENT_FIELDS);
      if (ap.length) errors.push('assessment carries undeclared fields: ' + ap.join(', ') + '.');
      if (!record.assessment.what) errors.push('assessment.what is required: say what was assessed.');
      if (!record.assessment.by_role || ROLES.indexOf(record.assessment.by_role) < 0) {
        errors.push('assessment.by_role must name the responding function that assessed it.');
      }
    }
    if (record.response !== null && record.response !== undefined) {
      var rp = unknownFields(record.response, RESPONSE_FIELDS);
      if (rp.length) errors.push('response carries undeclared fields: ' + rp.join(', ') + '.');
      if (!record.response.what) errors.push('response.what is required: say what the answer was.');
      if (!isIsoDate(record.response.issued_on)) errors.push('response.issued_on must be YYYY-MM-DD.');
      if (['none', 'support'].indexOf(record.response.commitment) < 0) {
        errors.push('response.commitment must be "none" or "support": a response that does not say '
          + 'whether it commits support cannot be told apart from one that does.');
      }
    }
    if (record.support !== null && record.support !== undefined) {
      var supportProblems = unknownFields(record.support, SUPPORT_FIELDS);
      if (supportProblems.length) errors.push('support carries undeclared fields: ' + supportProblems.join(', ') + '.');
      if (!isFiniteNumberOrNull(record.support.support_eur) || record.support.support_eur === null) {
        errors.push('support.support_eur must be a finite number.');
      }
      if (record.support.support_eur < 0) errors.push('support.support_eur cannot be negative.');
      if (!isIsoDate(record.support.delivered_on)) errors.push('support.delivered_on must be YYYY-MM-DD.');
      if (!isActionIdentifier(record.support.action_identifier)) {
        errors.push('support.action_identifier is required and must be a stable identifier, so the same '
          + 'action is counted once across AIM, IDS, PRISM and SPA.');
      }
      if (['net', 'gross'].indexOf(record.support.net_terms_basis) < 0) {
        errors.push('support.net_terms_basis must be "net" or "gross". Whether a credit has already '
          + 'been taken off the support figure is not something a reader should have to guess.');
      }
      /* A response that commits no support cannot be followed by a payment
         recorded against it. That is what keeps "we answered the question" and
         "we paid money" two different events. */
      if (record.response && record.response.commitment === 'none') {
        errors.push('Support cannot be recorded on a case whose response stated no support commitment. '
          + 'A response that gives a position is not a payment.');
      }
    }
    if (record.outcome !== null && record.outcome !== undefined) {
      var outcomeProblems = unknownFields(record.outcome, OUTCOME_FIELDS);
      if (outcomeProblems.length) errors.push('outcome carries undeclared fields: ' + outcomeProblems.join(', ') + '.');
      if (!isActionIdentifier(record.outcome.action_identifier)) {
        errors.push('outcome.action_identifier is required; it ties the outcome to the one action '
          + 'it measures rather than creating a second one.');
      }
      if (!record.outcome.what) errors.push('The outcome needs a plain English description of what the support achieved.');
      if (!isIsoDate(record.outcome.observed_on)) errors.push('The outcome needs observed_on as YYYY-MM-DD.');
      if (typeof record.outcome.counts_as_new_business !== 'boolean') {
        errors.push('outcome.counts_as_new_business must be true or false, never blank.');
      }
      if (record.outcome.migration_from && record.outcome.counts_as_new_business === true) {
        errors.push('An outcome that migrates from another product cannot count as newly won business.');
      }
      if (record.outcome.evidence !== null && record.outcome.evidence !== undefined) {
        if (!Array.isArray(record.outcome.evidence)) errors.push('outcome.evidence must be an array.');
        else record.outcome.evidence.forEach(function (ev, i) {
          var ep = unknownFields(ev, OUTCOME_EVIDENCE_FIELDS);
          if (ep.length) errors.push('outcome.evidence[' + i + '] carries undeclared fields: ' + ep.join(', ') + '.');
          if (!ev || !ev.kind) errors.push('outcome.evidence[' + i + '].kind is required.');
          if (!ev || !ev.reference) errors.push('outcome.evidence[' + i + '].reference is required.');
          if (ev && ev.observed_on !== null && ev.observed_on !== undefined && !isIsoDate(ev.observed_on)) {
            errors.push('outcome.evidence[' + i + '].observed_on must be YYYY-MM-DD or null.');
          }
        });
      }
      if (record.outcome.measures !== null && record.outcome.measures !== undefined) {
        if (!isPlainObject(record.outcome.measures)) {
          errors.push('outcome.measures must be an object listing the four measures, or absent.');
        } else {
          var mp = unknownFields(record.outcome.measures, MEASURE_FIELDS);
          if (mp.length) errors.push('outcome.measures carries undeclared measures: ' + mp.join(', ')
            + '. The four measures are kept separate; a fifth would need naming.');
          MEASURE_FIELDS.forEach(function (k) {
            if (!isFiniteNumberOrNull(record.outcome.measures[k])) {
              errors.push('outcome.measures.' + k + ' must be a finite number or null. '
                + 'A missing measure is not zero.');
            }
          });
        }
      }
      /* Unknown stays unknown. A case may be closed with no outcome, but a case
         that presents itself as resolved has to carry one. */
      if (record.state === 'resolved' && !record.outcome) {
        errors.push('A case at resolved must carry its outcome. If the result is not known, '
          + 'closed_outcome_unknown is the honest state.');
      }
    }
    if (record.state === 'resolved' && !record.outcome) {
      errors.push('A case at resolved must carry its outcome.');
    }

    /* The proposal section, and the two edges it guards. */
    var proposalProblems = checkProposals(record);
    proposalProblems.forEach(function (p) { errors.push(p); });

    if (record.support !== null && record.support !== undefined && record.state === 'action_agreed'
        && !acceptedProposal(record)) {
      errors.push('A case carrying delivered support has to carry the accepted proposal it was given against.');
    }

    var extra = unknownFields(record, RECORD_FIELDS);
    if (extra.length) {
      errors.push('Undeclared record fields refused: ' + extra.join(', ')
        + '. Add the field to RECORD_FIELDS first.');
    }
    return { ok: errors.length === 0, errors: errors };
  }

  /* The stable action identifier. Any of these shapes is accepted; what matters
     is that it is a plain string the same in every module, not a value
     re-derived per screen. */
  var ACTION_ID = /^(ACT[:_.-][A-Za-z0-9][A-Za-z0-9._:-]*)$/;

  function isActionIdentifier(v) {
    return typeof v === 'string' && ACTION_ID.test(v);
  }

  function makeActionIdentifier(caseId) {
    return 'ACT:' + String(caseId);
  }

  function checkProposals(record) {
    var problems = [];
    var p = record.proposal;
    if (p === null || p === undefined) {
      if (record.state === 'action_agreed' || record.state === 'resolved') {
        problems.push('A case at "' + record.state + '" has to carry the proposal that was accepted.');
      }
      return problems;
    }
    if (!isPlainObject(p)) return ['proposal must be an object carrying its versions.'];
    var envelope = unknownFields(p, ['versions', 'active_proposal_version']);
    if (envelope.length) problems.push('proposal carries undeclared fields: ' + envelope.join(', ') + '.');
    if (!Array.isArray(p.versions)) return problems.concat(['proposal.versions must be an array.']);

    var accepted = 0;
    p.versions.forEach(function (v, i) {
      var label = 'proposal.versions[' + i + ']';
      if (!isPlainObject(v)) { problems.push(label + ' must be an object.'); return; }
      var up = unknownFields(v, PROPOSAL_FIELDS);
      if (up.length) problems.push(label + ' carries undeclared fields: ' + up.join(', ') + '.');
      if (typeof v.proposal_version !== 'number' || v.proposal_version !== i + 1) {
        problems.push(label + '.proposal_version must be ' + (i + 1)
          + ', the versions being numbered in the order they were proposed.');
      }
      if (['draft', 'proposed', 'amended', 'accepted'].indexOf(v.proposal_state) < 0) {
        problems.push(label + '.proposal_state must be draft, proposed, amended or accepted.');
      }
      if (['available', 'expired'].indexOf(v.availability) < 0) {
        problems.push(label + '.availability must be available or expired. It is a separate field '
          + 'from proposal_state, because an approved offer that lapses was still approved.');
      }
      if (v.availability === 'expired' && !v.expiry_decision) {
        problems.push(label + ' is marked expired but does not say what was decided when it lapsed.');
      }
      if (v.proposal_state === 'accepted') {
        accepted++;
        if (!v.approval_reference && v.synthetic_approval !== true) {
          problems.push(label + ' is accepted but carries no approval reference. An approval that '
            + 'cannot be pointed at is not an approval; a local exercise must set synthetic_approval '
            + 'to true and say so.');
        }
        if (!v.approved_by_role || ROLES.indexOf(v.approved_by_role) < 0) {
          problems.push(label + ' is accepted but does not say which function accepted it.');
        }
        if (v.synthetic_approval === true && !/synthetic|simulat|not a real approval/i.test(String(v.approval_note || ''))) {
          problems.push(label + ' is a synthetic approval but its note does not say so. A local '
            + 'simulation must be labelled where a reader will see it.');
        }
      }
      if (v.terms !== null && v.terms !== undefined) {
        if (!isPlainObject(v.terms)) { problems.push(label + '.terms must be an object.'); return; }
        var tp = unknownFields(v.terms, PROPOSAL_TERM_FIELDS);
        if (tp.length) problems.push(label + '.terms carries undeclared terms: ' + tp.join(', ') + '.');
        if (v.terms.currency !== null && v.terms.currency !== undefined
            && !/^[A-Z]{3}$/.test(String(v.terms.currency))) {
          problems.push(label + '.terms.currency must be a three-letter code such as "EUR", or null.');
        }
        if (v.terms.quantity_after !== null && v.terms.quantity_after !== undefined
            && !(typeof v.terms.quantity_after === 'number' && Number.isFinite(v.terms.quantity_after))
            && !(isPlainObject(v.terms.quantity_after))) {
          problems.push(label + '.terms.quantity_after must be a number, a stated quantity, or null.');
        }
        ['price_before', 'price_after', 'support_eur', 'quantity_before'].forEach(function (k) {
          var val = v.terms[k];
          if (val === null || val === undefined) return;
          if (typeof val !== 'number' || !Number.isFinite(val)) {
            problems.push(label + '.terms.' + k + ' must be a finite number or null.');
          }
        });
        if (v.terms.offer_effective_date !== null && v.terms.offer_effective_date !== undefined
            && !isIsoDate(v.terms.offer_effective_date)) {
          problems.push(label + '.terms.offer_effective_date must be YYYY-MM-DD or null.');
        }
      }
      if (v.expires_on !== null && v.expires_on !== undefined && !isIsoDate(v.expires_on)) {
        problems.push(label + '.expires_on must be YYYY-MM-DD or null.');
      }
    });
    if (accepted > 1) {
      problems.push(accepted + ' proposal versions are marked accepted. One action has one accepted '
        + 'version; a later change is a new version that names the one it amends.');
    }
    if ((record.state === 'action_agreed' || record.state === 'resolved') && accepted !== 1) {
      problems.push('A case at "' + record.state + '" has to carry exactly one accepted proposal version.');
    }
    if (p.active_proposal_version !== null && p.active_proposal_version !== undefined) {
      var found = p.versions.some(function (v) { return v.proposal_version === p.active_proposal_version; });
      if (!found) problems.push('proposal.active_proposal_version names a version that is not there.');
    }
    return problems;
  }

  function acceptedProposal(record) {
    var p = record && record.proposal;
    if (!p || !Array.isArray(p.versions)) return null;
    return p.versions.filter(function (v) { return v.proposal_state === 'accepted'; })[0] || null;
  }

  /* Is the proposed support still available on a given day? Uses the proposal's
     own expiry, never a network-wide rule - there is no such rule and this
     component does not invent one. */
  function proposalAvailability(record, asOfDate) {
    var accepted = acceptedProposal(record);
    if (!accepted) return { available: false, reason: 'No proposal has been accepted on this case.' };
    var today = asOfDate || new Date().toISOString().slice(0, 10);
    var expired = accepted.availability === 'expired'
      || (accepted.expires_on && accepted.expires_on < today);
    if (expired) {
      return {
        available: false,
        reason: 'The accepted proposal expired on ' + (accepted.expires_on || accepted.expired_on
          || 'a date not recorded') + '. It is not presented as available.'
          + (accepted.proposal_state === 'accepted'
            ? ' It was approved, and it lapsed: both facts stay on the record.' : ''),
        expired_on: accepted.expired_on || accepted.expires_on || null,
        decision: accepted.expiry_decision || null,
        was_approved: accepted.proposal_state === 'accepted'
      };
    }
    return { available: true, version: accepted.proposal_version, expires_on: accepted.expires_on || null };
  }

  /* --------------------------------------------------------------- building -- */

  function stamp(at) { return at || new Date().toISOString(); }

  function emptyRecord(seed) {
    seed = seed || {};
    var at = stamp(seed.at);
    var missing = ['case_id', 'customer', 'part_number'].filter(function (k) { return !seed[k]; });
    if (missing.length) {
      return { ok: false, errors: ['Cannot start a case without: ' + missing.join(', ') + '.'] };
    }
    if (seed.owner_role && ROLES.indexOf(seed.owner_role) < 0) {
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
      owner_role: seed.owner_role || null,
      owner: seed.owner || null,
      assigned_to: seed.assigned_to || null,
      deputy_role: seed.deputy_role || null,
      escalation_route: seed.escalation_route || null,
      next_action: seed.next_action || null,
      next_update_due: seed.next_update_due || null,
      submitted_at: null,
      assigned_at: null,
      acknowledged_at: null,
      answered_at: null,
      resolved_at: null,
      action_identifier: seed.action_identifier || makeActionIdentifier(seed.case_id),
      assessment: null,
      response: null,
      evidence_requests: [],
      approval_note: null,
      proposal: { versions: [], active_proposal_version: null },
      support: null,
      outcome: null,
      explanations: seed.explanations || [],
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
        recorded_at: at, recorded_by: seed.by || 'unspecified', role: seed.owner_role || null,
        note: seed.note || null, commercial: false, event_id: null, correction_of: null,
        set_fields: null, evidence_requests: [], approval_note: null,
        stage: 'prepare', scenario: seed.scenario || null, result: seed.result || null,
        assessment: null, response: null,
        proposal: { versions: [], active_proposal_version: null },
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
      assessment: next.assessment || null,
      response: next.response || null,
      proposal: next.proposal || null,
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

  /* Has a commercial occasion already been recorded on this case? One action,
     one occasion: the identifier is what makes that true even when the same
     action is referred to by several cases. */
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

  function commercialEventCount(record) { return commercialEvents(record).length; }

  function requiredProblems(record, move, transition) {
    var problems = [];
    transition.requires.forEach(function (field) {
      /* A field the move supplies directly, or one already on the record. A
         field that a *builder* below constructs (response, proposal, outcome)
         is checked in its own block rather than here, so the refusal names the
         real problem and not "you did not pass an object". */
      if (field === 'response' || field === 'proposal' || field === 'outcome') return;
      var value = field in move ? move[field] : record[field];
      if (value === undefined || value === null || value === '') {
        problems.push('"' + transition.action + '" needs ' + field + '.');
      }
    });
    if (transition.requires.indexOf('evidence_requests') >= 0) {
      var reqs = (move.evidence_requests || record.evidence_requests || []);
      if (!Array.isArray(reqs) || !reqs.length) {
        problems.push('request_input needs at least one entry saying what was asked for, of whom, and when it is due.');
      } else {
        reqs.forEach(function (r, i) {
          if (!r || !r.what || !r.from_role || !isIsoDate(r.due)) {
            problems.push('evidence_requests[' + i + '] needs what, from_role and a due date in YYYY-MM-DD.');
          }
        });
      }
    }
    if (transition.requires.indexOf('response') >= 0) {
      var r = move.response || record.response;
      if (!isPlainObject(r)) problems.push('issue_response needs the response that was sent.');
      else {
        if (!r.what) problems.push('The response needs a plain English description of what was sent.');
        if (!isIsoDate(r.issued_on)) problems.push('The response needs issued_on as YYYY-MM-DD.');
        if (['none', 'support'].indexOf(r.commitment) < 0) {
          problems.push('The response must state commitment as "none" or "support". A response that '
            + 'does not say whether it commits support cannot be told apart from one that does.');
        }
      }
    }
    if (transition.requires.indexOf('proposal') >= 0) {
      var accepted = acceptedProposal(record) || (move.proposal_accept || null);
      if (!accepted) {
        problems.push('accept_proposal needs the proposal version being accepted. An approval has to '
          + 'point at the terms it approves.');
      }
    }
    if (transition.action === 'accept_proposal') {
      var accept = move.proposal_accept || {};
      if (typeof accept.proposal_version !== 'number') {
        problems.push('accept_proposal needs proposal_accept.proposal_version, the version being accepted.');
      }
      var stored = proposalVersion(record, accept.proposal_version);
      if (!stored) {
        problems.push('Proposal version ' + accept.proposal_version + ' is not on this case, so there is '
          + 'nothing to accept.');
      } else if (stored.availability === 'expired') {
        problems.push('Proposal version ' + accept.proposal_version + ' has expired. An expired proposal '
          + 'is not available to accept; a new version is the honest move.');
      }
      if (!accept.approval_reference && accept.synthetic_approval !== true) {
        problems.push('accept_proposal needs the genuine approval reference. A local exercise with no '
          + 'reference must set synthetic_approval to true and label itself synthetic.');
      }
      if (accept.synthetic_approval === true
          && !/synthetic|simulat|not a real approval/i.test(String(move.approval_note || accept.note || ''))) {
        problems.push('A synthetic approval has to be labelled synthetic where a reader will see it, '
          + 'in the approval note.');
      }
      if (accept.approval_route !== undefined && accept.approval_route !== null
          && stored && stored.approval_route && accept.approval_route !== stored.approval_route) {
        problems.push('The approval route on this proposal is "' + stored.approval_route
          + '". It is not changed by accepting: a different route is a different proposal.');
      }
    }
    if (transition.action === 'record_support') {
      var s = move.support || record.support;
      if (!s) problems.push('record_support needs the support that was given.');
      else {
        if (typeof s.support_eur !== 'number' || !Number.isFinite(s.support_eur) || s.support_eur < 0) {
          problems.push('The delivered support needs a support_eur that is a finite number of zero or more.');
        }
        if (!isIsoDate(s.delivered_on)) problems.push('The delivered support needs delivered_on as YYYY-MM-DD.');
        if (!s.what) problems.push('The delivered support needs a plain English description of what was given.');
        if (!isActionIdentifier(s.action_identifier || record.action_identifier)) {
          problems.push('The delivered support needs a stable action_identifier, so the same action is '
            + 'not counted again under another module.');
        }
        if (['net', 'gross'].indexOf(s.net_terms_basis) < 0) {
          problems.push('The delivered support must state net_terms_basis as "net" or "gross": whether the '
            + 'figure has a credit already taken off it.');
        }
      }
      var av = proposalAvailability(record, move.at ? String(move.at).slice(0, 10) : null);
      if (!av.available) {
        problems.push('Support cannot be recorded: ' + av.reason);
      }
      if (record.response && record.response.commitment === 'none') {
        problems.push('Support cannot be recorded on a case whose response stated no support commitment. '
          + 'Issuing an answer is not giving support.');
      }
    }
    if (transition.action === 'record_outcome' || transition.action === 'record_outcome_evidence') {
      var o = move.outcome || record.outcome;
      if (transition.action === 'record_outcome') {
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
          if (!isActionIdentifier(o.action_identifier || record.action_identifier)) {
            problems.push('The outcome needs a stable action_identifier, the same one the support carries, '
              + 'so the result is not counted as a second action.');
          }
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

  function proposalVersion(record, version) {
    var p = record && record.proposal;
    if (!p || !Array.isArray(p.versions)) return null;
    return p.versions.filter(function (v) { return v.proposal_version === version; })[0] || null;
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
          'This case is at "' + record.state + '". A finished case is not reopened here; start a new '
          + 'case and link it, so the same action is not run twice.');
      }
      var available = nextActions(record.state).map(function (t) { return t.action; });
      return reject('NOT_ALLOWED_FROM_STATE',
        '"' + move.action + '" is not allowed from "' + record.state + '". '
        + (available.length ? 'Allowed here: ' + available.join(', ') + '.' : 'Nothing further is allowed here.'));
    }
    if (!move.role || ROLES.indexOf(move.role) < 0) {
      return reject('ROLE_REQUIRED', '"' + transition.action + '" must be recorded by a responding function, one of: '
        + ROLES.join(', ') + '.');
    }
    if (move.role !== transition.role) {
      return reject('ROLE_NOT_PERMITTED',
        '"' + transition.action + '" is recorded by the ' + transition.role + ' function. '
        + 'A ' + move.role + ' cannot make this move.');
    }

    var problems = requiredProblems(record, move, transition);
    if (problems.length) return reject('MISSING_INPUT', problems.join(' '));

    /* Support is given once, against one action. A second payment on the same
       case is refused rather than recorded, so the activity is not multiplied.
       Checked before the record is built, so the reason returned is the
       duplicate and not a downstream validation complaint. */
    if (transition.action === 'record_support' && commercialEventCount(record) > 0) {
      return reject('DUPLICATE_SUPPORT',
        'Support has already been recorded on this case as ' + commercialEvents(record)
          .map(function (e) { return e.event_id; }).join(', ')
        + '. A further support payment is a new decision, not a second delivery on this one.');
    }

    var at = stamp(move.at);
    var next = clone(record);
    var setFields = {};

    if (move.scenario !== undefined) { next.scenario = move.scenario; setFields.scenario = next.scenario; }
    if (move.result !== undefined) { next.result = move.result; setFields.result = next.result; }
    if (move.review !== undefined) { next.review = move.review; setFields.review = next.review; }
    if (move.next_action !== undefined) { next.next_action = move.next_action; setFields.next_action = next.next_action; }
    if (move.next_update_due !== undefined) { next.next_update_due = move.next_update_due; setFields.next_update_due = next.next_update_due; }
    if (move.owner_role !== undefined) { next.owner_role = move.owner_role; setFields.owner_role = next.owner_role; }
    if (move.owner !== undefined) { next.owner = move.owner; setFields.owner = next.owner; }
    if (move.evidence_period !== undefined) { next.evidence_period = move.evidence_period; setFields.evidence_period = next.evidence_period; }
    if (move.offer_effective_date !== undefined) { next.offer_effective_date = move.offer_effective_date; setFields.offer_effective_date = next.offer_effective_date; }
    if (move.deputy_role !== undefined) { next.deputy_role = move.deputy_role; setFields.deputy_role = next.deputy_role; }
    if (move.escalation_route !== undefined) { next.escalation_route = move.escalation_route; setFields.escalation_route = next.escalation_route; }

    if (transition.action === 'request_input') {
      next.evidence_requests = (move.evidence_requests || []).map(function (r) {
        return { what: r.what, from_role: r.from_role, due: r.due, asked_at: at };
      });
      setFields.evidence_requests = next.evidence_requests;
    }
    if (transition.action === 'issue_response') {
      var resp = move.response || record.response;
      next.response = {
        what: resp.what,
        issued_on: resp.issued_on,
        by_role: resp.by_role || move.role,
        reference: resp.reference || null,
        commitment: resp.commitment
      };
      setFields.response = next.response;
      /* The dealer's clock stops when the answer leaves, not when the case ends.
         CASE-03 keeps the two separate so "we answered in four days" cannot be
         confused with "the case took four months". */
      next.answered_at = move.answered_at || at;
      setFields.answered_at = next.answered_at;
      next.acknowledged_at = next.acknowledged_at || at;
      setFields.acknowledged_at = next.acknowledged_at;
    }
    if (transition.action === 'submit') {
      next.submitted_at = move.submitted_at || at;
      setFields.submitted_at = next.submitted_at;
    }
    if (transition.action === 'begin_assessment' || transition.action === 'provide_input') {
      next.assigned_at = next.assigned_at || at;
      next.acknowledged_at = next.acknowledged_at || at;
      setFields.assigned_at = next.assigned_at;
      setFields.acknowledged_at = next.acknowledged_at;
    }
    if (transition.action === 'withdraw' || transition.action === 'terminal_no_change'
        || transition.action === 'close_resolved') {
      next.resolved_at = move.resolved_at || at;
      setFields.resolved_at = next.resolved_at;
    }
    if (transition.action === 'accept_proposal') {
      var accept = move.proposal_accept || {};
      var versions = (next.proposal.versions || []).map(function (v) {
        if (v.proposal_version !== accept.proposal_version) return v;
        var out = clone(v);
        out.proposal_state = 'accepted';
        out.approval_note = move.approval_note || accept.note || null;
        out.approval_reference = accept.approval_reference || null;
        out.approved_by_role = move.role;
        out.approved_on = accept.approved_on || String(at).slice(0, 10);
        out.synthetic_approval = accept.synthetic_approval === true;
        return out;
      });
      next.proposal = { versions: versions, active_proposal_version: accept.proposal_version };
      setFields.proposal = next.proposal;
      next.approval_note = move.approval_note;
      setFields.approval_note = next.approval_note;
    }
    if (transition.action === 'reject'
        || transition.action === 'withdraw' || transition.action === 'terminal_no_change'
        || transition.action === 'return_for_more_work') {
      next.approval_note = move.approval_note;
      setFields.approval_note = next.approval_note;
    }
    if (transition.action === 'record_support') {
      var support = move.support || record.support;
      next.support = {
        action_identifier: support.action_identifier || record.action_identifier,
        support_eur: support.support_eur,
        net_terms_basis: support.net_terms_basis,
        credit_reference: support.credit_reference || null,
        order_reference: support.order_reference || null,
        delivery_reference: support.delivery_reference || null,
        beneficiary: support.beneficiary || null,
        comparison: support.comparison || null,
        period: support.period || null,
        delivered_on: support.delivered_on,
        what: support.what,
        by_role: support.by_role || move.role
      };
      setFields.support = next.support;
    }
    if (transition.action === 'record_outcome') {
      var outcome = move.outcome || record.outcome;
      next.outcome = normaliseOutcome(outcome, record);
      setFields.outcome = next.outcome;
    }
    if (transition.action === 'record_outcome_evidence') {
      next.outcome = normaliseOutcome(Object.assign({}, next.outcome, {
        evidence: (next.outcome.evidence || []).concat([move.evidence || {}])
      }), record);
      setFields.outcome = next.outcome;
    }

    /* A move that closes the case owes nothing further. The clocks it filled are
       kept: closing does not clear how long the dealer waited. */
    var closed = isTerminal(transition.to);
    if (closed) {
      next.next_action = null;
      next.next_update_due = null;
      setFields.next_action = null;
      setFields.next_update_due = null;
      if (!next.resolved_at) {
        next.resolved_at = at;
        setFields.resolved_at = next.resolved_at;
      }
    }

    /* A move that changes state moves the case to the function that owes the
       next step, unless the caller named one explicitly. Whoever the move
       belongs to now owns the case. */
    if (transition.to !== record.state && move.owner_role === undefined) {
      var owed = OWNER_BY_STATE[transition.to];
      if (owed && next.owner_role !== owed) {
        next.owner_role = owed;
        setFields.owner_role = owed;
      }
    }

    next.state = transition.to;
    setFields.state = next.state;
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = move.by || 'unspecified';

    next = appendEntry(next, {
      kind: 'transition',
      action: transition.action,
      from_state: record.state,
      to_state: next.state,
      recorded_at: at,
      recorded_by: move.by || 'unspecified',
      role: move.role,
      note: move.note || transition.label,
      /* One payment, one occasion. The identifier travels onto the entry so a
         later correction of this entry keeps the count at one. */
      commercial: transition.action === 'record_support',
      event_id: next.support ? next.support.action_identifier : null,
      correction_of: null,
      set_fields: setFields,
      stage: stageOf(next.state),
      scenario: next.scenario || null,
      result: next.result || null,
      assessment: next.assessment || null,
      response: next.response || null,
      proposal: next.proposal || null,
      support: next.support || null,
      outcome: next.outcome || null,
      review: next.review || null,
      links: next.links || []
    });

    var check = validate(next);
    if (!check.ok) return reject('WOULD_BE_INVALID', 'That move would leave an invalid record: ' + check.errors.join(' '));
    return { ok: true, record: next, transition: transition };
  }

  function normaliseOutcome(outcome, record) {
    outcome = outcome || {};
    return {
      action_identifier: outcome.action_identifier || record.action_identifier || null,
      what: outcome.what || null,
      observed_on: outcome.observed_on || null,
      quantity_before: outcome.quantity_before === undefined ? null : outcome.quantity_before,
      quantity_after: outcome.quantity_after === undefined ? null : outcome.quantity_after,
      quantity_label: outcome.quantity_label || null,
      migration_from: outcome.migration_from || null,
      migration_to: outcome.migration_to || null,
      counts_as_new_business: outcome.counts_as_new_business,
      evidence: (outcome.evidence || []).map(function (ev) {
        return {
          kind: ev.kind, reference: ev.reference,
          observed_on: ev.observed_on || null,
          value: ev.value === undefined ? null : ev.value,
          note: ev.note || null
        };
      }),
      measures: outcome.measures === undefined || outcome.measures === null ? null : {
        purchase_cost_difference_eur: numOrNull(outcome.measures.purchase_cost_difference_eur),
        gross_profit_eur: numOrNull(outcome.measures.gross_profit_eur),
        capacity_released_units: numOrNull(outcome.measures.capacity_released_units),
        programme_expenditure_eur: numOrNull(outcome.measures.programme_expenditure_eur)
      },
      unresolved_reason: outcome.unresolved_reason || null
    };
  }

  function numOrNull(v) { return v === undefined || v === null ? null : v; }

  /* -- the four moves that are not states. Each appends one entry, dates it,
        attributes it, and leaves the lifecycle state exactly where it was. ----- */

  function appendProcess(record, kind, action, role, note, fields, at, by, extra) {
    var next = clone(record);
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = by || 'unspecified';
    Object.keys(fields).forEach(function (k) { next[k] = fields[k]; });
    next = appendEntry(next, Object.assign({
      kind: kind,
      action: action,
      from_state: record.state,
      /* The state does not move. A payment recorded after the case closed is
         still recorded, and the case stays closed. */
      to_state: record.state,
      recorded_at: at,
      recorded_by: by || 'unspecified',
      role: role,
      note: note,
      commercial: false,
      event_id: null,
      correction_of: null,
      set_fields: fields,
      stage: stageOf(next.state),
      scenario: next.scenario || null,
      result: next.result || null,
      assessment: next.assessment || null,
      response: next.response || null,
      proposal: next.proposal || null,
      support: next.support || null,
      outcome: next.outcome || null,
      review: next.review || null,
      links: next.links || []
    }, extra || {}));
    var check = validate(next);
    if (!check.ok) return reject('WOULD_BE_INVALID', 'That record would be invalid: ' + check.errors.join(' '));
    return { ok: true, record: next };
  }

  function requireRole(role) {
    if (!role || ROLES.indexOf(role) < 0) {
      return reject('ROLE_REQUIRED', 'This has to be recorded by a responding function, one of: '
        + ROLES.join(', ') + '.');
    }
    return null;
  }

  /* Which responding function has to have made each of the moves that are not
     states. Kept in one table for the same reason the transition table has one:
     a proposal is not an approval and an approver does not pay the money. */
  var MOVE_ROLES = {
    recordAssessment: ['reviewer'],
    proposeTerms: ['case_owner'],
    expireProposal: ['case_owner', 'reviewer'],
    recordSupport: ['support_owner'],
    recordOutcome: ['case_owner', 'reviewer'],
    /* Anyone taking part may explain; the words are theirs, not the reviewer's. */
    recordExplanation: ['requester', 'dealer', 'case_owner', 'reviewer', 'approver',
      'support_owner', 'finance', 'product', 'supply']
  };

  function requireMoveRole(move, role) {
    var bad = requireRole(role);
    if (bad) return bad;
    var allowed = MOVE_ROLES[move];
    if (allowed.indexOf(role) < 0) {
      return reject('ROLE_NOT_PERMITTED',
        '"' + move + '" is recorded by the ' + allowed.join(' or ') + ' function. '
        + 'A ' + role + ' cannot make this move.');
    }
    return null;
  }

  /* CASE-02: record the assessment. Internal thinking, dated and attributed, and
     deliberately not the response the dealer was given. */
  function recordAssessment(record, assessment, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var bad = requireMoveRole('recordAssessment', meta.role || (assessment && assessment.by_role));
    if (bad) return bad;
    if (!assessment || !assessment.what) {
      return reject('ASSESSMENT_NEEDS_CONTENT', 'An assessment has to say, in plain English, what was assessed.');
    }
    var at = stamp(meta.at);
    return appendProcess(record, 'assessment', 'record_assessment',
      assessment.by_role || meta.role,
      meta.note || 'Assessment recorded',
      { assessment: {
        what: assessment.what, basis: assessment.basis || null,
        by_role: assessment.by_role || meta.role, on: assessment.on || String(at).slice(0, 10),
        findings: assessment.findings || []
      } }, at, meta.by);
  }

  /* CASE-04: propose terms. Versioned, and an amendment names the version it
     replaces so the former terms stay readable. */
  function proposeTerms(record, proposal, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var bad = requireMoveRole('proposeTerms', meta.role || (proposal && proposal.offered_by_role));
    if (bad) return bad;
    if (isTerminal(record.state)) {
      return reject('CASE_IS_FINISHED', 'This case is at "' + record.state
        + '". Terms proposed now would belong to a new case, linked to this one.');
    }
    if (!proposal || !proposal.terms) {
      return reject('PROPOSAL_NEEDS_TERMS', 'A proposal has to carry its terms.');
    }
    var at = stamp(meta.at);
    var envelope = record.proposal || { versions: [], active_proposal_version: null };
    var existing = envelope.versions || [];
    var version = existing.length + 1;
    var amends = proposal.amends_proposal_version === undefined || proposal.amends_proposal_version === null
      ? (existing.length ? existing[existing.length - 1].proposal_version : null)
      : proposal.amends_proposal_version;
    if (amends !== null && !existing.some(function (v) { return v.proposal_version === amends; })) {
      return reject('NO_SUCH_PROPOSAL_VERSION', 'Proposal version ' + amends
        + ' is not on this case, so there is nothing to amend.');
    }
    var entry = {
      proposal_version: version,
      proposed_on: proposal.proposed_on || String(at).slice(0, 10),
      proposal_state: amends === null ? 'proposed' : 'amended',
      availability: 'available',
      terms: clone(proposal.terms),
      offered_by_role: proposal.offered_by_role || meta.role,
      note: proposal.note || null,
      amends_proposal_version: amends,
      expires_on: proposal.expires_on || null,
      expired_on: null,
      expiry_decision: null,
      /* The route is stated, not assumed. There is no standing price authority
         in this component and no network-wide rule to appeal to. */
      approval_route: proposal.approval_route || null,
      approval_note: null,
      approval_reference: null,
      approved_by_role: null,
      approved_on: null,
      synthetic_approval: false,
      candidate_keys: proposal.candidate_keys || null
    };
    /* The version it amends is marked, not deleted. That is what makes "what did
       we offer in August?" answerable after the terms moved. */
    var versions = existing.map(function (v) {
      if (amends !== null && v.proposal_version === amends) {
        return Object.assign(clone(v), { proposal_state: v.proposal_state === 'accepted' ? 'accepted' : 'amended' });
      }
      return v;
    }).concat([entry]);
    var next = appendProcess(record, 'proposal', 'propose_terms',
      entry.offered_by_role,
      meta.note || ('Proposal version ' + version + (amends ? ', amending version ' + amends : '')),
      { proposal: { versions: versions, active_proposal_version: version } }, at, meta.by);
    return next;
  }

  /* CASE-04: stop offering a version, and say what was decided when it stopped.
     An expired proposal is not available, and this is the only place that is
     recorded. */
  function expireProposal(record, expiry, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    expiry = expiry || {};
    var bad = requireMoveRole('expireProposal', meta.role || expiry.role);
    if (bad) return bad;
    var version = proposalVersion(record, expiry.proposal_version);
    if (!version) {
      return reject('NO_SUCH_PROPOSAL_VERSION', 'Proposal version ' + expiry.proposal_version
        + ' is not on this case, so there is nothing to expire.');
    }
    if (version.availability === 'expired') {
      return reject('ALREADY_EXPIRED',
        'Proposal version ' + expiry.proposal_version + ' is already expired'
        + (version.expired_on ? ' as of ' + version.expired_on : '')
        + '. Nothing was written. A second expiry would add a decision to the record without a '
        + 'decision having been taken.');
    }
    if (version.proposal_state === 'accepted' && !expiry.after_acceptance) {
      return reject('ACCEPTED_PROPOSAL_IS_NOT_EXPIRED',
        'Proposal version ' + expiry.proposal_version + ' was accepted. An accepted action that is no '
        + 'longer going ahead is closed with a reason, not expired as though no one had agreed to it. '
        + 'Pass after_acceptance with the reason if that is really what happened.');
    }
    if (!expiry.reason) {
      return reject('EXPIRY_NEEDS_REASON', 'An expiry has to say, in plain English, why it is no longer '
        + 'on offer and what was decided.');
    }
    var at = stamp(meta.at);
    var versions = (record.proposal.versions || []).map(function (v) {
      if (v.proposal_version !== expiry.proposal_version) return v;
      var out = clone(v);
      /* The approval, if there was one, stays. Expiring says the offer is no
         longer available; it does not unsay the decision that was taken. */
      out.availability = 'expired';
      out.expired_on = expiry.expired_on || String(at).slice(0, 10);
      out.expiry_decision = expiry.reason;
      return out;
    });
    return appendProcess(record, 'proposal', 'expire_proposal', meta.role,
      expiry.reason,
      { proposal: { versions: versions, active_proposal_version: expiry.proposal_version } },
      at, meta.by);
  }

  /* CASE-05 / CASE-02: the support actually delivered. Its own move, its own
     entry, its own stable action identifier. It does not move the case. */
  function recordSupport(record, support, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var bad = requireMoveRole('recordSupport', meta.role || (support && support.by_role));
    if (bad) return bad;
    if (!record.proposal || !acceptedProposal(record)) {
      return reject('SUPPORT_NEEDS_AN_ACCEPTED_PROPOSAL',
        'Support is given against an accepted proposal. Nothing has been accepted on this case, so '
        + 'there is nothing to give support against.');
    }
    var av = proposalAvailability(record, meta.at ? String(meta.at).slice(0, 10) : null);
    if (!av.available) return reject('SUPPORT_NOT_AVAILABLE', 'Support cannot be recorded: ' + av.reason);

    /* Routed through the lifecycle rule book so the version, the log entry, the
       duplicate guard and the validation are the same ones a transition uses.
       The state is carried through unchanged. */
    var applied = appendProcess(record, 'support', 'record_support',
      (support && support.by_role) || meta.role,
      meta.note || 'Support delivered',
      {}, stamp(meta.at), meta.by);
    if (!applied.ok) return applied;

    /* The state does not move, so the transition table is not the way in. The
       record is built here and validated by `validate`, which is where the
       "support is given once" and "no support against a response that committed
       none" rules live. */
    return finaliseSupport(record, support, meta);
  }

  function finaliseSupport(record, support, meta) {
    support = support || {};
    if (commercialEventCount(record) > 0) {
      return reject('DUPLICATE_SUPPORT',
        'Support has already been recorded on this case as ' + commercialEvents(record)
          .map(function (e) { return e.event_id; }).join(', ')
        + '. A further payment is a new decision, not a second delivery on this one.');
    }
    var problems = [];
    if (typeof support.support_eur !== 'number' || !Number.isFinite(support.support_eur) || support.support_eur < 0) {
      problems.push('The delivered support needs a support_eur that is a finite number of zero or more.');
    }
    if (!isIsoDate(support.delivered_on)) problems.push('The delivered support needs delivered_on as YYYY-MM-DD.');
    if (!support.what) problems.push('The delivered support needs a plain English description of what was given.');
    if (['net', 'gross'].indexOf(support.net_terms_basis) < 0) {
      problems.push('The delivered support must state net_terms_basis as "net" or "gross": whether the figure '
        + 'has a credit already taken off it.');
    }
    if (!isActionIdentifier(support.action_identifier || record.action_identifier)) {
      problems.push('The delivered support needs a stable action_identifier.');
    }
    if (record.response && record.response.commitment === 'none') {
      problems.push('Support cannot be recorded on a case whose response stated no support commitment. '
        + 'Issuing an answer is not giving support.');
    }
    if (problems.length) return reject('MISSING_INPUT', problems.join(' '));

    var at = stamp(meta.at);
    var delivered = {
      action_identifier: support.action_identifier || record.action_identifier,
      support_eur: support.support_eur,
      net_terms_basis: support.net_terms_basis,
      credit_reference: support.credit_reference || null,
      order_reference: support.order_reference || null,
      delivery_reference: support.delivery_reference || null,
      beneficiary: support.beneficiary || null,
      comparison: support.comparison || null,
      period: support.period || null,
      delivered_on: support.delivered_on,
      what: support.what,
      by_role: support.by_role || meta.role
    };
    var next = clone(record);
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = meta.by || 'unspecified';
    next.support = delivered;
    next = appendEntry(next, {
      kind: 'support', action: 'record_support',
      from_state: record.state, to_state: record.state,
      recorded_at: at, recorded_by: meta.by || 'unspecified', role: delivered.by_role,
      note: meta.note || 'Support delivered',
      commercial: true,
      event_id: delivered.action_identifier,
      correction_of: null,
      set_fields: { support: delivered },
      stage: stageOf(next.state),
      scenario: next.scenario || null, result: next.result || null,
      assessment: next.assessment || null, response: next.response || null,
      proposal: next.proposal || null,
      support: delivered, outcome: next.outcome || null,
      review: next.review || null, links: next.links || []
    });
    var check = validate(next);
    if (!check.ok) return reject('WOULD_BE_INVALID', 'That support would leave an invalid record: ' + check.errors.join(' '));
    return { ok: true, record: next };
  }

  /* CASE-05: the outcome, with its own evidence and its four separate measures.
     It does not move the case either - recording the result of a payment is not
     a lifecycle step. An outcome that is not known is recorded as not known. */
  function recordOutcome(record, outcome, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var bad = requireMoveRole('recordOutcome', meta.role || (outcome && outcome.by_role));
    if (bad) return bad;
    if (!record.support) {
      return reject('OUTCOME_NEEDS_SUPPORT',
        'An outcome measures a delivered action. Nothing has been delivered on this case, so there is '
        + 'nothing to measure. A case can still close with the outcome unknown.');
    }
    var problems = [];
    outcome = outcome || {};
    if (!outcome.what) problems.push('The outcome needs a plain English description of what the support achieved.');
    if (!isIsoDate(outcome.observed_on)) problems.push('The outcome needs observed_on as YYYY-MM-DD.');
    if (typeof outcome.counts_as_new_business !== 'boolean') {
      problems.push('The outcome must state counts_as_new_business as true or false.');
    }
    if (outcome.migration_from && outcome.counts_as_new_business === true) {
      problems.push('Volume migrated from another product is not newly won business.');
    }
    if (problems.length) return reject('MISSING_INPUT', problems.join(' '));

    var at = stamp(meta.at);
    var next = clone(record);
    next.version = record.version + 1;
    next.updated_at = at;
    next.updated_by = meta.by || 'unspecified';
    next.outcome = normaliseOutcome(Object.assign({}, outcome, {
      /* The outcome measures the action the support paid for, unless the caller
         names a different one on purpose. */
      action_identifier: outcome.action_identifier || record.support.action_identifier
    }), next);
    next = appendEntry(next, {
      kind: 'outcome', action: 'record_outcome',
      from_state: record.state, to_state: record.state,
      recorded_at: at, recorded_by: meta.by || 'unspecified', role: meta.role || outcome.by_role,
      note: meta.note || 'Outcome recorded',
      /* A recorded result is not a second payment. The action keeps one id and
         one occasion. */
      commercial: false, event_id: null, correction_of: null,
      set_fields: { outcome: next.outcome },
      stage: stageOf(next.state),
      scenario: next.scenario || null, result: next.result || null,
      assessment: next.assessment || null, response: next.response || null,
      proposal: next.proposal || null,
      support: next.support || null, outcome: next.outcome,
      review: next.review || null, links: next.links || []
    });
    var check = validate(next);
    if (!check.ok) return reject('WOULD_BE_INVALID', 'That outcome would leave an invalid record: ' + check.errors.join(' '));
    return { ok: true, record: next };
  }

  /* CASE-06. What a contributor said, kept in their own words and as separate
     evidence. An explanation names one or more factors (or "unknown") and may
     say that no action is wanted. Later evidence is one of three different
     things, and each names the explanation it answers: a source correction (the
     source itself was wrong), a later recollection (the person remembers it
     differently) or a disagreement with the interpretation. None of them
     rewrites the original; each is appended beside it. A reported reason names
     a factor; it does not measure that factor's share of a change. */
  var EXPLANATION_KINDS = ['explanation', 'source_correction', 'later_recollection',
    'interpretation_disagreement'];
  var EXPLANATION_FACTORS = ['availability', 'price', 'competition', 'demand', 'fleet',
    'quality', 'terms', 'other', 'unknown'];
  var EXPLANATION_COMPARED_FIELDS = ['words', 'scope', 'reported_period', 'source', 'audience',
    'factors', 'no_action'];

  function findExplanation(record, id) {
    return ((record && record.explanations) || []).filter(function (e) {
      return e && e.explanation_id === id;
    })[0] || null;
  }

  function recordExplanation(record, explanation, meta) {
    meta = meta || {};
    if (!isPlainObject(record)) return reject('NOT_A_RECORD', 'A case record is required.');
    var role = meta.role || (explanation && explanation.by_role);
    var bad = requireMoveRole('recordExplanation', role);
    if (bad) return bad;
    explanation = explanation || {};
    var kind = explanation.kind || 'explanation';
    var problems = [];
    if (EXPLANATION_KINDS.indexOf(kind) < 0) {
      problems.push('kind must be one of: ' + EXPLANATION_KINDS.join(', ') + '.');
    }
    ['words', 'scope', 'source', 'audience'].forEach(function (f) {
      if (typeof explanation[f] !== 'string' || !explanation[f].trim()) {
        problems.push('The explanation needs ' + f + ', as the contributor gave it.');
      }
    });
    var factors = Array.isArray(explanation.factors) ? explanation.factors.slice() : [];
    if (!factors.length) problems.push('Name at least one factor, or "unknown". None is assumed.');
    factors.forEach(function (f) {
      if (EXPLANATION_FACTORS.indexOf(f) < 0) problems.push('"' + f + '" is not a declared factor.');
    });
    if (typeof explanation.no_action !== 'boolean') {
      problems.push('State no_action as true or false.');
    }
    var corrects = explanation.corrects || null;
    if (kind !== 'explanation') {
      if (!corrects || !findExplanation(record, corrects)) {
        problems.push('A ' + kind.replace(/_/g, ' ') + ' must name the explanation it answers, '
          + 'by an explanation_id already on this case.');
      }
    } else if (corrects) {
      problems.push('A first explanation does not correct anything. Use a correction kind.');
    }
    if (problems.length) return reject('MISSING_INPUT', problems.join(' '));

    var at = stamp(meta.at);
    var list = (record.explanations || []).slice();
    var entry = {
      explanation_id: 'EXP-' + (list.length + 1),
      kind: kind,
      words: explanation.words,
      contributor_role: role,
      contributor: meta.by || 'unspecified',
      scope: explanation.scope,
      reported_period: isBlankValue(explanation.reported_period) ? null : explanation.reported_period,
      recorded_date: String(at).slice(0, 10),
      recorded_at: at,
      recorded_seq: record.history.length + 1,
      source: explanation.source,
      audience: explanation.audience,
      factors: factors,
      no_action: explanation.no_action,
      corrects: corrects
    };
    list.push(entry);
    var applied = appendProcess(record, 'explanation', 'record_explanation', role,
      meta.note || ('Explanation recorded: ' + kind.replace(/_/g, ' ')),
      { explanations: list }, at, meta.by);
    if (!applied.ok) return applied;
    return { ok: true, record: applied.record, explanation: entry };
  }

  function isBlankValue(v) {
    return v === null || v === undefined || (typeof v === 'string' && !v.trim());
  }

  /* A family change set beside the reasons given for it. The reasons are listed;
     no euro is moved onto any of them, because a reported reason is not a
     measured share. The whole change stays unallocated until a measurement
     supplies a share. */
  function declineAttribution(record, change) {
    change = change || {};
    var total = Number(change.amount_eur);
    var factors = [];
    ((record && record.explanations) || []).forEach(function (e) {
      (e.factors || []).forEach(function (f) { if (factors.indexOf(f) < 0) factors.push(f); });
    });
    var allocated = {};
    factors.forEach(function (f) { allocated[f] = null; });
    var allocatedSum = 0;
    Object.keys(allocated).forEach(function (f) {
      if (allocated[f] !== null) allocatedSum += allocated[f];
    });
    return {
      family: change.family || null,
      total_change_eur: Number.isFinite(total) ? total : null,
      factors_reported: factors,
      allocated_eur: allocated,
      unallocated_eur: Number.isFinite(total) ? total - allocatedSum : null,
      allocation_state: allocatedSum === 0 ? 'not allocated' : 'partly allocated',
      statement: factors.length
        ? 'Reported reasons: ' + factors.join(', ') + '. A reported reason does not measure its '
          + 'share of the change, so none of it is allocated to any one factor.'
        : 'No reason has been reported. The change is not allocated.'
    };
  }

  /* A correction, recollection or disagreement set beside the explanation it
     answers, with the fields that differ and the decisions recorded while the
     original stood. */
  function compareCorrection(record, explanationId) {
    var later = findExplanation(record, explanationId);
    if (!later) return reject('NO_SUCH_EXPLANATION', 'No explanation "' + explanationId + '" on this case.');
    if (!later.corrects) {
      return reject('NOT_A_CORRECTION', 'Explanation ' + explanationId + ' does not answer an earlier one.');
    }
    var original = findExplanation(record, later.corrects);
    if (!original) return reject('ORIGINAL_MISSING', 'The explanation it answers is not on this case.');
    var changed = EXPLANATION_COMPARED_FIELDS.filter(function (f) {
      return JSON.stringify(original[f]) !== JSON.stringify(later[f]);
    });
    var affected = (record.history || []).filter(function (h) {
      return h.seq > original.recorded_seq && h.seq < later.recorded_seq
        && ['created', 'explanation', 'correction'].indexOf(h.kind) < 0;
    }).map(function (h) {
      return { seq: h.seq, kind: h.kind, action: h.action, recorded_at: h.recorded_at,
        from_state: h.from_state, to_state: h.to_state };
    });
    return {
      ok: true,
      kind: later.kind,
      original: clone(original),
      corrected: clone(later),
      changed_fields: changed,
      affected_decisions: affected,
      statement: affected.length
        ? affected.length + ' decision(s) were recorded while the original evidence stood. They are '
          + 'listed for review; none is rewritten.'
        : 'No decision was recorded while the original evidence stood.'
    };
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
      return reject('ROLE_REQUIRED', 'A correction must be recorded by a responding function, one of: ' + ROLES.join(', ') + '.');
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
      /* Carried through, so a corrected payment is still the same occasion. */
      commercial: !!target.commercial,
      event_id: target.event_id || null,
      correction_of: seq,
      set_fields: setFields,
      stage: stageOf(next.state),
      scenario: next.scenario || null,
      result: next.result || null,
      assessment: next.assessment || null,
      response: next.response || null,
      proposal: next.proposal || null,
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
   820|     "reopen the case at the version I saved" honest rather than approximate:
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
      owner_role: null,
      owner: null,
      assigned_to: null,
      deputy_role: null,
      escalation_route: null,
      next_action: null,
      next_update_due: null,
      submitted_at: null,
      assigned_at: null,
      acknowledged_at: null,
      answered_at: null,
      resolved_at: null,
      action_identifier: record.action_identifier,
      assessment: null,
      response: null,
      evidence_requests: [],
      approval_note: null,
      proposal: null,
      support: null,
      outcome: null,
      explanations: record.explanations || [],
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
      ['scenario', 'result', 'assessment', 'response', 'proposal',
        'support', 'outcome', 'review', 'links'].forEach(function (k) {
        if (entry[k] !== null && entry[k] !== undefined) rebuilt[k] = clone(entry[k]);
      });
      if (entry.evidence_requests && entry.evidence_requests.length) {
        rebuilt.evidence_requests = clone(entry.evidence_requests);
      }
      if (entry.approval_note !== null && entry.approval_note !== undefined) {
        rebuilt.approval_note = entry.approval_note;
      }
      /* The clocks are recovered from the entry that set them, so a reopened
         case knows when it was answered even if that entry is not the latest. */
      ['submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at'].forEach(function (k) {
        if (entry.recorded_at && !rebuilt[k]
            && (entry.action === 'submit' && k === 'submitted_at'
              || k === 'answered_at' && entry.action === 'issue_response'
              || k === 'resolved_at' && /^close_resolved$|^withdraw$|^terminal_no_change$/.test(entry.action))) {
          rebuilt[k] = entry.recorded_at;
        }
      });
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

  var DAY_MS = 86400000;

  function daysBetween(from, to) {
    if (!from || !to) return null;
    var a = Date.parse(from), b = Date.parse(to);
    if (isNaN(a) || isNaN(b) || b < a) return null;
    return Math.round(((b - a) / DAY_MS) * 1000) / 1000;
  }

  /* CASE-03. A reader has to be able to see who owes the next action and when,
     and how long the dealer has been waiting - which is not the same question as
     how long the case has existed.

     The waiting clock runs from `submitted_at`. Reassigning the case, changing
     the deputy or escalating it does NOT restart it and does NOT reset the total:
     `total_waiting_days` is measured from the submission, not from the last edit.
     A reassignment adds time to the new owner without taking it off the dealer. */
  function openWork(record, asOf) {
    if (!record) return null;
    var today = (asOf && String(asOf).length > 10) ? String(asOf).slice(0, 10)
      : (asOf || new Date().toISOString().slice(0, 10));
    var nowStamp = (asOf && String(asOf).length > 10) ? String(asOf) : (asOf ? asOf + 'T23:59:59.000Z' : new Date().toISOString());
    var due = record.next_update_due || null;
    var closed = isTerminal(record.state);
    var reqs = record.evidence_requests || [];

    /* What the dealer owes, and what ISZE owes, read separately. */
    var dealerOwes = reqs.filter(function (r) { return r.from_role === 'dealer'; });
    var iszeOwes = reqs.filter(function (r) { return r.from_role !== 'dealer'; });

    var stop = record.resolved_at || (record.answered_at && closed ? record.answered_at : null) || nowStamp;

    return {
      case_id: record.case_id,
      state: record.state,
      stage: stageOf(record.state),
      closed: closed,
      version: record.version,
      part_number: record.part_number || null,
      customer: record.customer || null,
      owner_role: record.owner_role,
      owner: record.owner || null,
      assigned_to: record.assigned_to || null,
      deputy_role: record.deputy_role || null,
      escalation_route: record.escalation_route || null,
      next_action: record.next_action,
      next_update_due: due,
      overdue: !!(due && !closed && due < today),
      due_today: !!(due && due === today),
      /* The separate clocks, kept separate. */
      submitted_at: record.submitted_at || null,
      assigned_at: record.assigned_at || null,
      acknowledged_at: record.acknowledged_at || null,
      answered_at: record.answered_at || null,
      resolved_at: record.resolved_at || null,
      /* How long the dealer has been waiting for an answer, and for how long in
         total. A reassignment moves the owner, not these two numbers. */
      total_waiting_days: daysBetween(record.submitted_at, record.resolved_at || nowStamp),
      not_yet_answered_days: record.answered_at
        ? daysBetween(record.submitted_at, record.answered_at)
        : daysBetween(record.submitted_at, nowStamp),
      /* Whose turn it is, in plain words. */
      awaiting: closed ? null
        : record.state === 'awaiting_input'
          ? (dealerOwes.length ? 'the dealer' : 'another ISZE or distributor function')
          : (record.owner_role || null),
      dealer_commitments: dealerOwes.map(function (r) {
        return { what: r.what, due: r.due, asked_at: r.asked_at || null };
      }),
      isze_commitments: iszeOwes.map(function (r) {
        return { what: r.what, from_role: r.from_role, due: r.due, asked_at: r.asked_at || null };
      })
    };
  }

  /* One sentence a screen can print without a reader having to work out who is
     late. A dealer waiting on ISZE is shown as waiting on ISZE: not idle, not at
     fault, and not in the same bucket as a case ISZE is waiting on the dealer
     for. */
  function obligationStatement(record, asOf) {
    var work = openWork(record, asOf);
    if (!work) return 'No case.';
    if (work.closed) return 'This case is at "' + work.state + '". Nothing further is owed.';
    if (work.state === 'awaiting_input') {
      if (work.dealer_commitments.length) {
        return 'Waiting on the dealer for: '
          + work.dealer_commitments.map(function (c) { return c.what + ' (due ' + c.due + ')'; }).join('; ')
          + '. Nothing is overdue on our side' + (work.overdue ? ' on this obligation' : '') + '.';
      }
      return 'Waiting on an ISZE or distributor function for: '
        + work.isze_commitments.map(function (c) { return c.what + ' (' + c.from_role + ', due ' + c.due + ')'; }).join('; ')
        + '. The dealer has supplied what was asked of it.';
    }
    if (work.state === 'draft' || !work.owner_role) {
      return 'Not yet with anybody. A draft owes nothing until it is submitted.';
    }
    return 'With the ' + work.owner_role + ' function'
      + (work.assigned_to ? ' (' + work.assigned_to + ')' : '')
      + ', who owes: ' + (work.next_action || 'the next action, not stated')
      + (work.next_update_due ? ', by ' + work.next_update_due : '')
      + '.';
  }

  /* The distinct steps a reader must be able to tell apart, in order. Read from
     the log, so a case that was never assessed cannot claim it was. */
  function stageEvidence(record) {
    var has = function (action) {
      return (record.history || []).some(function (h) { return h.action === action; });
    };
    return {
      assessment_recorded: has('record_assessment'),
      response_recorded: has('issue_response'),
      proposal_recorded: has('propose_terms'),
      approval_recorded: has('accept_proposal'),
      delivery_recorded: has('record_support'),
      outcome_recorded: has('record_outcome'),
      commercial_occasions: commercialEventCount(record)
    };
  }

  /* ------------------------------------------------------- the benefit account -- */

  var MEASURES = {
    purchase_cost_difference_eur: { unit: 'EUR', label: 'Difference in parts purchase cost' },
    gross_profit_eur: { unit: 'EUR', label: 'Gross profit' },
    capacity_released_units: { unit: 'units', label: 'Capacity released' },
    programme_expenditure_eur: { unit: 'EUR', label: 'Programme expenditure' }
  };

  /* CASE-05. One action is counted once, whichever module recorded it.

     Three things this refuses to do:
       * add the four measures into one benefit figure - they are four different
         quantities on four different bases, and a total would be meaningless;
       * let one action appear twice because AIM, IDS, PRISM and SPA each named
         it - `benefitAccountsFor` groups by `action_identifier` and lists the
         modules instead of counting them;
       * turn a paid credit into profit. A credit is a payment the programme
         made, and it is reported as an expenditure; nothing here moves it into
         the gross-profit line. */
  function benefitAccount(records, asOfDate) {
    var list = records || [];
    var byAction = {};
    var lines = [];

    list.forEach(function (record) {
      if (!record) return;
      var actionId = (record.support && record.support.action_identifier)
        || record.action_identifier
        || ('ACT:' + record.case_id);
      if (!byAction[actionId]) {
        byAction[actionId] = {
          action_identifier: actionId,
          case_ids: [],
          modules: [],
          support_eur: null,
          support_basis: null,
          outcome_state: 'unknown',
          measures: {},
          units: null,
          counted_as: 'unresolved'
        };
      }
      var bucket = byAction[actionId];
      bucket.case_ids.push(record.case_id);

      /* Money that was actually paid, counted once for the action - not once per
         case that names it. */
      if (record.support && bucket.support_eur === null) {
        bucket.support_eur = record.support.support_eur;
        bucket.support_basis = record.support.net_terms_basis;
      }

      /* Which modules referred to it. Recorded so a reader can see four modules
         and one action, rather than four contributions. */
      var modules = record.modules || (record.review && record.review.modules) || null;
      if (Array.isArray(modules)) {
        modules.forEach(function (m) { if (bucket.modules.indexOf(m) < 0) bucket.modules.push(m); });
      } else if (bucket.modules.indexOf('AIM') < 0) {
        bucket.modules.push('AIM');
      }

      if (record.outcome) {
        bucket.outcome_state = 'recorded';
        var m = record.outcome.measures || {};
        Object.keys(MEASURES).forEach(function (k) {
          if (m[k] === null || m[k] === undefined) return;
          /* One action, one value per measure. A second case naming the same
             action does not add to it. */
          if (bucket.measures[k] === undefined) bucket.measures[k] = m[k];
        });
        /* Volume, on the same rule: recorded once per action, and a migration is
           not newly won business. */
        var units = record.outcome.quantity_after;
        if (bucket.units === null) {
          bucket.units = (typeof units === 'number' && Number.isFinite(units)) ? units
            : (units === null || units === undefined ? null : units);
          bucket.counted_as = bucket.units === null ? 'unresolved'
            : record.outcome.migration_from ? 'migrated from another product'
              : record.outcome.counts_as_new_business === true ? 'newly won'
                : 'not counted as new business';
        }
      }
    });

    Object.keys(byAction).forEach(function (id) {
      var bucket = byAction[id];
      Object.keys(MEASURES).forEach(function (k) {
        var spec = MEASURES[k];
        lines.push({
          action_identifier: id,
          measure: k,
          label: spec.label,
          unit: spec.unit,
          amount: bucket.measures[k] === undefined ? null : bucket.measures[k],
          /* Stated on the line rather than left to the reader. */
          known: bucket.measures[k] !== undefined
        });
      });
    });

    var knownActions = Object.keys(byAction).map(function (k) { return { action_identifier: k,
      case_ids: byAction[k].case_ids, modules: byAction[k].modules,
      support_eur: byAction[k].support_eur, support_basis: byAction[k].support_basis,
      outcome_state: byAction[k].outcome_state,
      units: byAction[k].units, counted_as: byAction[k].counted_as }; });
    var casesWithoutOutcome = list.filter(function (r) { return r && !r.outcome; }).length;

    return {
      as_of: asOfDate || new Date().toISOString().slice(0, 10),
      cases: list.length,
      distinct_actions: knownActions.length,
      support_total_eur: knownActions.reduce(function (s, a) { return s + (a.support_eur || 0); }, 0),
      newly_won_units: knownActions.reduce(function (s, a) {
        return s + (a.counted_as === 'newly won' && typeof a.units === 'number' ? a.units : 0);
      }, 0),
      migrated_units_not_new_business: knownActions.reduce(function (s, a) {
        return s + (a.counted_as === 'migrated from another product' && typeof a.units === 'number' ? a.units : 0);
      }, 0),
      cases_without_a_recorded_outcome: casesWithoutOutcome,
      actions: knownActions,
      lines: lines,
      /* Deliberately null. There is no single benefit figure, and printing one
         would invite exactly the double count this function prevents. */
      total_benefit_eur: null,
      statement: 'One action is counted once, whichever of AIM, IDS, PRISM and SPA referred to it. '
        + 'The four measures are reported separately and are not added together: they are different '
        + 'quantities on different bases. Volume migrated from another Isuzu product is reported on '
        + 'its own line and is not added to newly won business. ' + casesWithoutOutcome
        + ' case(s) have no recorded outcome, and an unknown outcome stays unknown.'
    };
  }

  /* The honest statement about what the history is. Published by the store and
     printed where a reader will see it, so nobody has to infer it. */
  function appendOnlyStatement() {
    return 'The change history is append-only inside this component: nothing here rewrites or removes '
      + 'an entry, and a correction names the entry it replaces. It is NOT tamper-proof certification. '
      + 'There is no server, no signature and no trusted clock, and anyone with write access to the '
      + 'stored file can edit it. Read it as a record of what was decided, not as an audit control.';
  }

  var API = {
    RECORD_SCHEMA_VERSION: RECORD_SCHEMA_VERSION,
    RECORD_FIELDS: RECORD_FIELDS,
    SUPPORT_FIELDS: SUPPORT_FIELDS,
    OUTCOME_FIELDS: OUTCOME_FIELDS,
    OUTCOME_EVIDENCE_FIELDS: OUTCOME_EVIDENCE_FIELDS,
    MEASURE_FIELDS: MEASURE_FIELDS,
    MEASURES: MEASURES,
    PROPOSAL_FIELDS: PROPOSAL_FIELDS,
    PROPOSAL_TERM_FIELDS: PROPOSAL_TERM_FIELDS,
    ASSESSMENT_FIELDS: ASSESSMENT_FIELDS,
    RESPONSE_FIELDS: RESPONSE_FIELDS,
    ENTRY_FIELDS: ENTRY_FIELDS,
    ENTRY_SNAPSHOT_FIELDS: ENTRY_SNAPSHOT_FIELDS,
    UNDECLARED_IN_CONTRACTS: UNDECLARED_IN_CONTRACTS,
    ROLES: ROLES,
    STAGES: STAGES,
    STATE_STAGE: STATE_STAGE,
    TERMINAL_STATES: TERMINAL_STATES,
    NO_REOPEN_FROM: NO_REOPEN_FROM,
    NO_NEXT_ACTION_STATES: NO_NEXT_ACTION_STATES,
    NO_OWNER_REQUIRED_STATES: NO_OWNER_REQUIRED_STATES,
    OWNER_BY_STATE: OWNER_BY_STATE,
    CASE_STATES: CASE_STATES,
    CASE_STATES_PLANNED: (contracts.CASE_STATES_TARGET || []).slice(),
    CASE_STATES_RETIRED: CASE_STATES_RETIRED,
    CONTRACT_VOCABULARY_STALE: CONTRACT_VOCABULARY_STALE,
    TRANSITIONS: TRANSITIONS,
    stageOf: stageOf,
    isTerminal: isTerminal,
    monetaryWeightOf: monetaryWeightOf,
    transitionsFor: transitionsFor,
    findTransition: findTransition,
    nextActions: nextActions,
    unknownFields: unknownFields,
    validate: validate,
    emptyRecord: emptyRecord,
    MOVE_ROLES: MOVE_ROLES,
    requireMoveRole: requireMoveRole,
    clone: clone,
    contentDigest: contentDigest,
    isDuplicateOf: isDuplicateOf,
    applyTransition: applyTransition,
    applyCorrection: applyCorrection,
    recordExplanation: recordExplanation,
    declineAttribution: declineAttribution,
    compareCorrection: compareCorrection,
    EXPLANATION_KINDS: EXPLANATION_KINDS,
    EXPLANATION_FACTORS: EXPLANATION_FACTORS,
    applyLink: applyLink,
    rebuildAt: rebuildAt,
    diffFields: diffFields,
    commercialEvents: commercialEvents,
    commercialEventCount: commercialEventCount,
    openWork: openWork,
    obligationStatement: obligationStatement,
    stageEvidence: stageEvidence,
    recordAssessment: recordAssessment,
    proposeTerms: proposeTerms,
    expireProposal: expireProposal,
    recordSupport: recordSupport,
    recordOutcome: recordOutcome,
    acceptedProposal: acceptedProposal,
    proposalVersion: proposalVersion,
    proposalAvailability: proposalAvailability,
    benefitAccount: benefitAccount,
    makeActionIdentifier: makeActionIdentifier,
    isActionIdentifier: isActionIdentifier,
    appendOnlyStatement: appendOnlyStatement,
    daysBetween: daysBetween,
    isIsoDate: isIsoDate,
    isTimestamp: isTimestamp
  };

  /* The vocabulary has to match the shared contract. Measured at load time,
     because a silent divergence here is the fault this migration exists to
     close: no state would have a stage, and eight states would arrive with no
     rule book. Until `contracts.CASE_STATES` is swapped to the target, the
     divergence is published rather than hidden. */
  var vocabMismatch = [];
  (contracts.CASE_STATES_TARGET || []).forEach(function (s) {
    if (CASE_STATES.indexOf(s) < 0) vocabMismatch.push(s);
  });
  API.CASE_STATES_PLANNED = (contracts.CASE_STATES_TARGET || []).slice();
  API.CASE_STATES_RETIRED = CASE_STATES_RETIRED;
  API.CONTRACT_VOCABULARY_STALE = CONTRACT_VOCABULARY_STALE;
  API.VOCABULARY_IN_SYNC = vocabMismatch.length === 0;
  if (!API.VOCABULARY_IN_SYNC) API.VOCABULARY_MISMATCH = vocabMismatch;

  root.AIMCaseSchema = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);

/* ---------------------------------------------------------------------------
   What this file deliberately does not decide
   ---------------------------------------------------------------------------
   `role` says which function made a move - a reviewer, an approver, a support
   owner. It does not say which human being is behind that function, and it is
   not an access control. Real identity, the tenant an identity belongs to, and
   revocation of an identity all need a server, and there is no approved server
   for this component. `src/output/recipients.js` carries the one permission
   check that can be unit-tested today.

   There is also no service guarantee here. A `next_update_due` is the date
   somebody wrote down for this case; it is not an SLA, and no network-wide
   response promise is declared anywhere in this file. If ISZE publishes one,
   it belongs in a decision record, not in a date field.
   ------------------------------------------------------------------------- */