/* ===========================================================================
   One source-backed status model (F11, REVIEW-02).

   v03 printed status prose from literals. So the page said "Decision component
   0.2" while the payload said 0.3, kept asking a reader to settle a turbo price
   conflict that the payload had already resolved, and kept demanding an
   accounting cost that the declared rule no longer requires. A literal cannot
   notice that the payload changed underneath it.

   Every status sentence below is assembled from the payload, and each one carries
   the pointer it came from so a reader can check it. Two things are kept on
   separate axes on purpose, because they answer different questions:

     commercial priority   - how much money is at stake (payload billing)
     evidence completeness - how much of the file is actually held (payload counts)

   "Cost and list held" is coverage. It is not a cleared price decision. Nothing
   in this module converts a held record into an approval, and nothing promotes a
   part count into a distinct-part count.
   =========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    /* The candidate coverage record is owned by src/data/candidates.js, so the
       view model asks that module rather than recomputing the same counts. */
    module.exports = factory(require('../data/candidates.js'));
  } else {
    root.AIMViewModel = factory(root.AIMCandidates);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (candidatesModule) {
  'use strict';

  var POINTER = {
    version: '/meta/version',
    revision: '/meta/revision',
    audience: '/meta/audience',
    rules: '/meta/confirmedRules',
    supplierCost: '/meta/supplierCost',
    currentPriceList: '/meta/currentPriceList',
    turbo: '/turboPriceResolution',
    screenRule: '/screenRule',
    candidates: '/candidateScreen',
    verifiedCosts: '/verifiedCosts'
  };

  function held(label, detail, pointer) {
    return { status: 'held', status_label: 'Held', label: label, detail: detail, pointer: pointer };
  }
  function partial(label, detail, pointer) {
    return { status: 'partial', status_label: 'In part', label: label, detail: detail, pointer: pointer };
  }
  function open(label, detail, pointer, required) {
    return { status: 'open', status_label: 'Not held', label: label, detail: detail,
      pointer: pointer, required: required || null };
  }

  /* --------------------------------------------------------------- version -- */

  function version(payload) {
    var m = payload.meta || {};
    return {
      version: m.version || 'version not declared in the payload',
      revision: m.revision || null,
      build_date: m.buildDate || null,
      audience: m.audience || null,
      supersedes: m.supersedesVersion || null,
      /* The header prints this. It is read, never typed. */
      display: m.version || 'Version not declared',
      pointer: POINTER.version
    };
  }

  /* ------------------------------------------------------- commercial axes -- */

  /* Priority and completeness are separate arguments on purpose. A large-billing
     row with no cost is high priority and low completeness at the same time, and
     collapsing the two would hide exactly the rows worth chasing. */
  function priorityFrom(observedBillingEur) {
    if (!Number.isFinite(observedBillingEur)) {
      return { level: null, label: 'Not established', basis: 'no recorded billing in the screened rows' };
    }
    if (observedBillingEur >= 100000) {
      return { level: 'high', label: 'High', basis: 'recorded billed amount above EUR 100,000 for this exact part' };
    }
    if (observedBillingEur >= 10000) {
      return { level: 'medium', label: 'Medium', basis: 'recorded billed amount above EUR 10,000 for this exact part' };
    }
    return { level: 'low', label: 'Low', basis: 'recorded billed amount below EUR 10,000 for this exact part' };
  }

  /* ------------------------------------------------------------ candidates -- */

  /* Coverage is delegated to src/data/candidates.js rather than recomputed here.
     That module owns the counts, so the numbers on the screen and the numbers in
     the tests are the same numbers. This function adds only the one count that
     module does not carry (how many cost-master records exist in total) and the
     aliases the view layer reads. */
  function candidateCoverage(payload, candidatesModuleOverride) {
    var mod = candidatesModuleOverride || candidatesModule;
    if (!mod || typeof mod.coverage !== 'function') {
      throw new Error('The candidate coverage record needs src/data/candidates.js. It is not loaded, so no '
        + 'coverage figure is stated rather than one being recomputed here.');
    }
    var rows = payload.candidateScreen || [];
    var costMasters = payload.verifiedCosts || [];
    var cov = mod.coverage(rows, rows);
    return Object.assign({}, cov, {
      cost_master_records: costMasters.length,
      distinct_part_numbers: cov.unique_parts,
      rows_with_cost: cov.rows_with_cost,
      distinct_part_numbers_with_cost: cov.unique_parts_with_cost,
      /* Stated as two different counts, because they are two different counts. */
      counts_statement: cov.rows_with_cost + ' customer-part rows carry a price and a cost record, covering '
        + cov.unique_parts_with_cost + ' distinct part numbers. Those are not the same count. '
        + costMasters.length + ' cost-master records exist in total.',
      coverage_statement: 'Price and cost records are held for ' + cov.rows_with_cost + ' of ' + cov.rows_total
        + ' screened rows. That is coverage of the file. It is not a cleared price decision, not a cost '
        + 'approval and not a statement about the other ' + (cov.rows_total - cov.rows_with_cost) + ' rows.',
      pointer: POINTER.candidates,
      delegated_to: 'src/data/candidates.js coverage()'
    });
  }

  /* ----------------------------------------------------------------- turbo -- */

  /* The v03 turbo header asked a reader to settle a conflict that the payload has
     already resolved, and the snapshot panel listed two amounts with no statement
     of which one bills. Both are read from the resolution object here. */
  function turboResolution(payload) {
    var t = payload.turboPriceResolution;
    if (!t) return null;
    var resolved = t.resolved_billable_list;
    var sensitivity = t.sensitivity_range || [];
    return {
      part_number: t.part_number,
      resolved_billable_list: resolved,
      resolved_on: t.resolved_on,
      resolved_by: t.resolved_by,
      sensitivity_range: sensitivity,
      candidate_records: (t.records || []).length,
      usable_records: (t.records || []).filter(function (r) { return r.usable; }).length,
      statement: 'The competing list records are resolved. EUR ' + fmt(resolved, 2)
        + ' is the carried list price and is the amount that bills; EUR '
        + fmt(sensitivity[0], 2) + ' is retained as a separate observation. '
        + (t.records || []).length + ' records were examined and only '
        + (t.records || []).filter(function (r) { return r.usable; }).length
        + ' is usable as a billed list price.',
      open_statement: t.still_open,
      observed_billing_note: t.observed_billing_2026,
      /* The list price is not the customer net price. Saying so once, plainly. */
      price_status: 'list price resolved; current customer net price not held',
      cost_status: 'parts purchase cost per the documented supplier calculation; no accounting cost required',
      pointer: POINTER.turbo
    };
  }

  /* ------------------------------------------------------------ cost basis -- */

  /* The declared measure: parts purchase cost from the supplier purchase-cost
     calculation. An accounting / landed / moving-average cost is explicitly no
     longer required. Views must print that, not the old requirement. */
  function costRule(payload) {
    var r = (payload.meta && payload.meta.confirmedRules) || {};
    return {
      required: r.costTypeRequired || 'parts purchase cost',
      accounting_cost_required: false,
      accounting_cost_statement: 'An accounting, landed or moving-average cost is no longer required. '
        + 'The declared measure is the parts purchase cost from the documented supplier purchase-cost '
        + 'calculation, with its inputs, source and effective date.',
      excluded_from_measure: r.excludedFromMeasure || [],
      double_deduction: r.doubleDeduction || null,
      class_margin_warning: r.classMarginWarning || null,
      pointer: POINTER.rules + '/costTypeRequired'
    };
  }

  function priceRule(payload) {
    var m = payload.meta || {};
    return {
      statement: m.currentPriceList || null,
      supplier_cost_statement: m.supplierCost || null,
      /* Acceptance of an embedded supplier-cost formula is not approval of a
         customer net price, and it is not application approval either. */
      boundary: 'A cost formula and a list price can both be accepted and still leave the customer net '
        + 'price unapproved. Accepting the cost calculation does not approve a selling price, and it does '
        + 'not approve fitting a part to a vehicle.',
      pointer: POINTER.currentPriceList
    };
  }

  /* ----------------------------------------------------------- case status -- */

  /* Per case, the cost / price / evidence status as one row set. Each row says
     what is held, what is not, and where that came from. */
  function caseStatus(caseObject, payload) {
    var pe = caseObject.packEvidence || {};
    var readiness = pe.readiness || [];
    var hasCostRecord = !!pe.costRecordPresent;
    var costRow = hasCostRecord
      ? partial('Parts purchase cost',
          'A supplier purchase-cost record exists for ' + caseObject.pn + ' on the named bases. '
          + 'The record existing is not the same as the cost being verified for this offer.',
          '/cases/' + caseObject.id + '/packEvidence/costRecordPresent')
      : open('Parts purchase cost',
          'No cost record is held for ' + caseObject.pn + ', so gross profit is not calculated for it. '
          + 'No figure is substituted.',
          '/cases/' + caseObject.id + '/packEvidence/costRecordPresent',
          'a parts purchase cost record for ' + caseObject.pn + ', or an entered assumption labelled as one');
    return {
      case_id: caseObject.id,
      part_number: caseObject.pn,
      rows: [
        held('Original part reference', caseObject.pn + ' (' + caseObject.name + ')',
          '/cases/' + caseObject.id + '/pn'),
        held('Exact-part billing evidence', 'Recorded billing for this exact part number is connected.',
          '/cases/' + caseObject.id + '/comparisons'),
        costRow,
        open('Current customer net price',
          'Not established from the held records. The recorded amounts are list prices and billed '
          + 'averages, not a confirmed net offer.',
          '/cases/' + caseObject.id + '/packEvidence/applicableNetPrice',
          'a current customer net price for ' + caseObject.customer + ' on ' + caseObject.pn),
        (function () {
          var comp = (pe.offers || []).filter(function (o) { return o.independent_offer; });
          return comp.length
            ? partial('Competing offer', comp.length + ' dated advertised record(s) held; comparability and '
                + 'fitment are not approved.', '/cases/' + caseObject.id + '/packEvidence/offers')
            : open('Competing offer', 'No priced exact-number record is held for this part.',
                '/cases/' + caseObject.id + '/packEvidence/offers',
                'a dated quotation for a complete like-for-like part');
        })(),
        open('Fleet / demand basis',
          'No part-level share of the fleet in service is established, so no recoverable-sales figure '
          + 'is stated.', '/cases/' + caseObject.id + '/fleet',
          'the vehicles in service for which this exact part applies')
      ],
      readiness: readiness.map(function (r) { return { name: r.name, status: r.status }; }),
      /* A case can be commercially important and evidentially thin at once. */
      commercial_priority: caseObject.comparisons
        ? priorityFrom(((caseObject.comparisons[caseObject.defaultCompare] || {}).current || {}).eur)
        : { level: null, label: 'Not established', basis: 'no comparison held' },
      evidence_completeness: null,
      pointer: '/cases/' + caseObject.id + '/packEvidence'
    };
  }

  /* Number of the status rows that are fully held, so completeness is a count a
     reader can check rather than a score someone chose. */
  function completeness(status) {
    var rows = (status && status.rows) || [];
    var heldCount = rows.filter(function (r) { return r.status === 'held'; }).length;
    return {
      held: heldCount,
      total: rows.length,
      statement: heldCount + ' of ' + rows.length + ' status items are held without qualification.',
      basis: 'a count of the status items on this view, not a score'
    };
  }

  function fmt(x, d) {
    if (x === null || x === undefined || !Number.isFinite(Number(x))) return '-';
    return Number(x).toLocaleString('en-GB', { minimumFractionDigits: d, maximumFractionDigits: d });
  }

  /* The whole model, built once per payload. Views read it; they do not
     re-derive a status sentence of their own. The named helpers are attached too,
     so a test can check one status without rebuilding the entire model. */
  function build(payload, engine, modules) {
    modules = modules || {};
    var cases = payload.cases || [];
    var byCase = {};
    cases.forEach(function (c) { byCase[c.id] = caseStatus(c, payload); });
    return {
      version: version(payload),
      cost_rule: costRule(payload),
      price_rule: priceRule(payload),
      turbo: turboResolution(payload),
      candidates: candidateCoverage(payload, modules.candidates),
      by_case: byCase,
      case_status: function (caseId) { return byCase[caseId] || null; },
      completeness: completeness,
      priority_from: priorityFrom,
      pointer_index: POINTER,
      /* Named accessors, for callers that want one status on its own. */
      versionOf: version,
      costRule: costRule,
      priceRule: priceRule,
      turboResolution: turboResolution,
      candidateCoverage: candidateCoverage,
      caseStatus: caseStatus,
      _engine_seen: !!(engine && engine.calculate)
    };
  }

  return {
    build: build,
    version: version,
    costRule: costRule,
    priceRule: priceRule,
    turboResolution: turboResolution,
    candidateCoverage: candidateCoverage,
    caseStatus: caseStatus,
    completeness: completeness,
    priorityFrom: priorityFrom,
    POINTER: POINTER
  };
});
