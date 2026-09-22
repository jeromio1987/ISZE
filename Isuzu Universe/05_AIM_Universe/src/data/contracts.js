/* ===========================================================================
   Shared records (BASE-03).

   One small set of versioned records is used by every builder: the scenario,
   the calculation result, an evidence reference, a case and a recipient brief.
   A field name is decided once here. Builders must not invent a private copy.

   Contract version history
     1  initial freeze, 2026-09-22
     2  2026-09-22  amended by the integration owner. Three changes, recorded
                    here rather than made silently:
                    + bridge_* result fields, so the profit bridge reconciles
                      (FIN-04) and a printed margin can be checked against it
                    + scenario.support_direction, so support GIVEN to a
                      participant is never confused with support SOUGHT FROM a
                      supplier - they are opposite commercial things
                    + a written decision on support_eur in a participant brief,
                      see RECIPIENTS below. The question was raised by the
                      workflow developer against version 1 and is answered
                      here so it is not relitigated per builder.
     3  2026-09-22  amended by the integration owner. SECTION_FIELDS added, and
                    declaredFields() now folds section contents in. Raised by
                    the export agent, which had to carry three sections in forms
                    the contract happened to allow rather than the forms they
                    were meant to have. The fault was structural, not clerical:
                    a flat name list cannot declare what is inside a section, so
                    the internal builder silently gutted three of them - the
                    limits block became {}, the review lost the owner's own
                    explanation and note, and a saved revision log became [].
                    An empty section reads as "nothing to report", which is the
                    worst way for a strip to fail.
     4  2026-09-22  amended by the integration owner, before the durable case
                    work started. CASE_STATES replaced with the vocabulary the
                    plan's CASE-02 names, because the old one described a
                    proposal going one way while a case here is a two-way
                    exchange that has to show whose turn it is. CASE_TIMESTAMPS
                    added so the separate clocks CASE-03 requires cannot be
                    collapsed into one "updated at". The remaining CASE fields
                    are declared so the sections CASE-03..06 need survive the
                    internal builder, which is the v3 fault applied in advance
                    rather than discovered again.
   =========================================================================== */
(function (root) {
  'use strict';

  var CONTRACT_VERSION = 4;

  /* Every field a scenario may carry. Anything outside this list does not
     travel with the decision, so a screen cannot silently invent state. */
  var SCENARIO_FIELDS = [
    'scenario_id',        /* stable id, so a saved case can be matched to a run */
    'version',            /* increments when a saved scenario is changed     */
    'case_id',            /* which case (original part + customer) this is   */
    'part_number',        /* original part reference, never a rewritten one  */
    'unit',               /* what one unit is ('unit', 'set', ...)           */

    'price_before',       /* applicable net selling price, unchanged offer    */
    'price_after',        /* proposed applicable net selling price            */
    'quantity_before',    /* eligible base quantity                           */
    'quantity_after',     /* total quantity under the proposal                */
    'quantity_label',     /* observed history / stated commitment / manual    */

    'scope',              /* 'all' or 'incremental'                           */
    'volume_is_observed', /* true only for a recorded quantity                */
    'pack_size',          /* discrete pack multiple for required quantities   */

    'cost_eur',           /* parts purchase cost, per unit, or null           */
    'cost_basis_id',      /* HIST / SEP26 / OCT26 - named, never inferred     */
    'cost_basis_source',  /* 'verified record' or 'stated assumption'         */
    'support_eur',        /* one-off support, counted once                    */
    'support_direction',  /* 'to_participant' = an offer term, shareable.
                             'from_supplier'  = a cost concession, internal.   */

    'evidence_period',    /* the recorded history period (explicit field)      */
    'offer_effective_date',/* the date the proposed offer takes effect         */
    'sources',            /* evidence references (see EVIDENCE_FIELDS)        */

    'selected_alternative_id', /* the ranked option this scenario came from   */
    'objective'           /* 'revenue' or 'grossProfit' - ranking only        */
  ];

  /* Fields a calculation result always carries. Both revenue and gross profit
     are never collapsed into one invented score. */
  var RESULT_FIELDS = [
    'ok', 'error', 'errors', 'resolved', 'migration_status',
    'price_before', 'price_after', 'scope', 'pack_size',
    'quantity_before', 'quantity_after', 'quantity_label', 'volume_is_observed',
    'extra_quantity',
    'revenue_before', 'revenue_after', 'revenue_change', 'revenue_pct',
    'gp_before', 'gp_after', 'gp_change', 'gp_pct',
    'margin_before_pct', 'margin_after_pct', 'margin_unit_after_pct',
    'margin_pp_change',
    'qty_preserve_revenue', 'qty_preserve_gp',
    'extra_qty_to_preserve_revenue', 'extra_qty_to_preserve_gp',
    'extra_qty_to_exceed_revenue', 'extra_qty_to_exceed_gp',
    'qty_preserve_revenue_label', 'qty_preserve_gp_label',
    'extra_qty_exceed_revenue_label', 'extra_qty_exceed_gp_label',
    'tolerable_volume_loss_pct', 'tolerable_loss_revenue_pct', 'tolerable_loss_gp_pct',
    'discount_on_existing_volume_eur',
    'bridge_revenue_change', 'bridge_cost_change', 'bridge_support_eur', 'bridge_reconciles',
    'cost', 'cost_basis_id', 'cost_is_zero', 'cost_missing_not_zero',
    'support_eur', 'support_counted_once',
    'evidence_period', 'offer_effective_date',
    'flags', 'conditional'
  ];

  var EVIDENCE_FIELDS = [
    'reference_id', 'kind', 'title', 'period', 'source_file', 'source_pointer',
    'status', 'basis', 'restricted'
  ];

  var CASE_FIELDS = [
    'case_id', 'version', 'part_number', 'customer', 'market', 'scope_note',
    'evidence_period', 'owner_role', 'state', 'scenario', 'result',
    'created_at', 'updated_at', 'history',
    /* The section names themselves. A section has to be a declared name before
       its contents can be, or the internal builder drops the whole block and the
       reader sees a record that never mentions the subject. */
    'limits', 'review',
    /* CASE-03: who owes the next action, when, and the separate clocks. */
    'owner', 'assigned_to', 'deputy_role', 'escalation_route', 'next_update_due',
    'submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at',
    'action_identifier',
    /* CASE-04: the proposed terms and whether anyone approved them. */
    'proposal',
    /* CASE-05: support actually delivered, distinct from support promised. */
    'support',
    /* CASE-06: what a contributor said, kept in their own words. */
    'explanations'
  ];

  /* ---- sections and their declared contents (contract version 3) -----------

     The export agent found this the hard way: declaredFields() returns a flat
     list of top-level names, so a section named in CASE_FIELDS does not declare
     anything INSIDE it. Anything nested was therefore stripped by the internal
     builder, and the failure was silent - a section that exists and is empty
     reads as "nothing to report" rather than "we dropped it".

     Measured before this block existed: the internal record's limits block was
     `{}`, the review section lost the owner's own explanation and note, and the
     revision log was `[]` even with revisions saved. Three sections quietly
     gutted by one missing declaration. */

  var SECTION_FIELDS = {
    /* The record must be able to state what it is, at its own top level, so a
       reader of the saved file does not have to infer it from context. */
    record: [
      'schema', 'contract_version', 'recipient', 'audience', 'exported_at',
      'case_id', 'customer', 'market', 'part_number', 'unit', 'version',
      'state', 'owner_role', 'evidence_period', 'offer_effective_date',
      'selected_alternative_id', 'objective', 'not_approved_statement'
    ],
    /* What the record explicitly does NOT establish. An empty limits block is
       worse than no block: it claims the question was considered. */
    limits: [
      'price_approved', 'current_customer_net_price', 'supplier_cost',
      'no_raw_invoices', 'no_credentials'
    ],
    /* The owner's own words about this decision, kept as evidence. */
    review: [
      'owner', 'owner_role', 'review_date', 'status', 'state',
      'explanation', 'note', 'saved_at'
    ],
    /* The revision log. `revision` and `recorded_at` are the minimum that makes
       a history diffable; `supersedes` is what makes a correction traceable to
       its declared predecessor. */
    history: [
      'revision', 'recorded_at', 'at', 'supersedes', 'corrects_revision',
      'state', 'previous_state', 'actor_role', 'note', 'change'
    ],
    evidence: [
      'reference_id', 'kind', 'title', 'period', 'source_file',
      'source_pointer', 'status', 'basis', 'restricted'
    ],
    flags: ['code', 'severity', 'text', 'amount']
  };

  /* Case lifecycle (contract version 4).

     IN FORCE since 2026-09-22: the nine states the plan's CASE-02 names, adopted
     together with the transition table and every reference in one change. A case
     here is a two-way exchange between a dealer or distributor and ISZE, so the
     states have to show whose turn it is - which the earlier proposal vocabulary
     (approved, rejected, delivered, outcome_recorded) did not.

     Two properties worth keeping in view:
       - `closed_outcome_unknown` is a REAL, permitted end state. A case can
         finish without anyone knowing the result, and that is not a failure to be
         smoothed over by inferring one.
       - none of these states carries a monetary value. `response_issued` is not
         delivered support, `action_agreed` is not a won outcome, and closing a
         case creates no benefit. CASE-02 requires exactly that.

     History: the pre-migration vocabulary was draft, evidence_requested,
     ready_for_review, approved, rejected, delivered, outcome_recorded,
     no_change_recommended. The old-to-new mapping is in tests/case_store.test.mjs's
     header so the two runs can be diffed. */
  var CASE_STATES = [
    'draft',                  /* being prepared; nothing asked of anyone yet   */
    'submitted',              /* sent to the responsible function              */
    'assessment',             /* being looked at; no answer owed yet           */
    'awaiting_input',         /* waiting on the dealer, distributor or ISZE    */
    'response_issued',        /* an answer was given; support has NOT followed */
    'action_agreed',          /* an action was agreed; it has NOT been done    */
    'resolved',               /* the matter is settled                         */
    'withdrawn',              /* taken back by whoever raised it               */
    'closed_outcome_unknown'  /* finished, and nobody knows the result          */
  ];

  /* Kept as an alias so callers written against the migration can still name it.
     It is the same list; there is no second vocabulary any more. */
  var CASE_STATES_TARGET = CASE_STATES;

  /* A dealer waiting on ISZE guidance is awaiting it, not inactive and not at
     fault. These are the separate clocks CASE-03 requires; they are deliberately
     not collapsed into one "updated at". */
  var CASE_TIMESTAMPS = [
    'submitted_at', 'assigned_at', 'acknowledged_at', 'answered_at', 'resolved_at'
  ];

  var RECIPIENTS = {
    member: {
      label: 'Distributor or dealer participant brief',
      /* Constructed from this list only. Never the internal record with parts
         deleted afterwards. */
      permits: [
        'reference', 'offer', 'price', 'quantity', 'customers', 'limits'
      ],
      /* DECISION, contract version 2, raised by the workflow developer against
         version 1. support_eur STAYS in a participant brief, and
         support_direction now travels beside it.

         The reasoning: support that ISZE gives to a participant is a term of
         the offer being put to that participant. A brief that asks someone to
         respond to a proposal has to state the proposal. Removing it would be
         the mirror image of the blacklist defect - an output that looks clean
         because nobody had to decide what belonged in it.

         What matters is direction, not the word "support":
           support_direction 'to_participant' -> an offer term. Shareable.
           support_direction 'from_supplier'  -> a concession on what ISZE pays
                                                its supplier. That is a cost
                                                input, it is internal, and it
                                                must never reach a brief.

         So a brief never carries a cost basis id, parts cost, gross profit,
         margin, or inbound supplier support - but it does carry the support
         being offered to the person reading it. */
      leaf_fields: [
        'price_before', 'price_after', 'quantity_before', 'quantity_after',
        'quantity_label', 'unit', 'part_number', 'description',
        'revenue_before', 'revenue_after', 'revenue_change', 'revenue_pct',
        'scope', 'support_eur', 'support_direction', 'evidence_period',
        'offer_effective_date',
        'case_id', 'customer', 'title', 'note', 'limits', 'status',
        'code', 'severity', 'text'
      ]
    },
    internal: {
      label: 'ISZE internal record',
      permits: [
        'reference', 'offer', 'price', 'quantity', 'customers', 'limits',
        'result', 'scenario', 'case', 'review', 'sources', 'basis', 'cost'
      ],
      leaf_fields: null /* null means: everything already declared in this file */
    }
  };

  function declaredFields() {
    var all = SCENARIO_FIELDS.concat(RESULT_FIELDS, EVIDENCE_FIELDS, CASE_FIELDS);
    var seen = {}, out = [];
    for (var i = 0; i < all.length; i++) {
      if (!seen[all[i]]) { seen[all[i]] = 1; out.push(all[i]); }
    }
    /* Section contents count as declared fields. Without this the internal
       builder strips them, because it can only carry a name it has been told
       about - see the note on SECTION_FIELDS above. */
    Object.keys(SECTION_FIELDS).forEach(function (section) {
      SECTION_FIELDS[section].forEach(function (k) {
        if (!seen[k]) { seen[k] = 1; out.push(k); }
      });
    });
    return out;
  }

  /* Every declared name inside one section, for a builder that wants to be
     explicit about what a section may carry. */
  function sectionFields(section) {
    return (SECTION_FIELDS[section] || []).slice();
  }

  /* Returns the difference between two record versions, so a version bump can
     be reviewed instead of happening invisibly. */
  function diff(previous, current) {
    var changes = [], keys = {}, k;
    previous = previous || {}; current = current || {};
    for (k in previous) { if (!Object.prototype.hasOwnProperty.call(current, k)) keys[k] = 1; }
    for (k in current) { keys[k] = 1; }
    for (k in keys) {
      var before = previous[k], after = current[k];
      if (JSON.stringify(before) !== JSON.stringify(after)) {
        changes.push({ field: k, from: before === undefined ? null : before, to: after === undefined ? null : after });
      }
    }
    return changes;
  }

  root.AIMContracts = {
    CONTRACT_VERSION: CONTRACT_VERSION,
    SCENARIO_FIELDS: SCENARIO_FIELDS,
    RESULT_FIELDS: RESULT_FIELDS,
    EVIDENCE_FIELDS: EVIDENCE_FIELDS,
    CASE_FIELDS: CASE_FIELDS,
    SECTION_FIELDS: SECTION_FIELDS,
    CASE_STATES: CASE_STATES,
    CASE_STATES_TARGET: CASE_STATES_TARGET,
    CASE_TIMESTAMPS: CASE_TIMESTAMPS,
    RECIPIENTS: RECIPIENTS,
    declaredFields: declaredFields,
    sectionFields: sectionFields,
    diff: diff
  };

  if (typeof module === 'object' && module.exports) module.exports = root.AIMContracts;
})(typeof globalThis !== 'undefined' ? globalThis : this);
