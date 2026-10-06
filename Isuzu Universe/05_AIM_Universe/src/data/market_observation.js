/* ===========================================================================
   MARKET evidence record (MARKET-01 and later MARKET-02..06 helpers).

   WHY THIS FILE EXISTS
     Competitor quotes arrive as loose rows. Before any panel compares them, each
     row must become a dated evidence record that keeps source, date, references,
     seller, market, currency, tax, pack, channel and availability meaning as
     separate fields. Missing values stay missing. Nothing here scrapes, invents
     a competitor price, or fills MARKET-DATA-GAP.

   WHAT IT DOES NOT DO
     It does not draw a screen. It does not certify a price action. It does not
     borrow a previous row's currency or reference when the current row is blank.
   =========================================================================== */
(function (root) {
  'use strict';

  var RECORD_FIELDS = [
    'observation_id',
    'source',
    'observed_date',
    'original_reference',
    'alternative_reference',
    'seller',
    'market',
    'currency',
    'tax',
    'pack',
    'channel',
    'availability_meaning',
    'role',
    'level',
    'part_number',
    'case_id',
    'amount',
    'amount_scope',
    'unit',
    'vat_rate',
    'vat_rate_unit',
    'delivery_included',
    'delivery_cost_eur',
    'fx_to_eur',
    'fx_date',
    'match',
    'equivalence',
    'supersedes',
    'saved_comparison_id'
  ];

  function isBlank(v) {
    return v === undefined || v === null || (typeof v === 'string' && String(v).trim() === '');
  }

  function name(v) {
    if (isBlank(v)) return null;
    return String(v).trim();
  }

  function toNumberOrNull(v) {
    if (v === undefined || v === null || v === '') return null;
    var n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  function copyPack(pack) {
    if (pack === undefined || pack === null) return null;
    if (typeof pack !== 'object') return pack;
    try { return JSON.parse(JSON.stringify(pack)); }
    catch (e) { return null; }
  }

  function copyMatch(match) {
    if (match === undefined || match === null) return null;
    if (typeof match !== 'object') return null;
    try { return JSON.parse(JSON.stringify(match)); }
    catch (e) { return null; }
  }

  /* Read one field from THIS input only. Aliases never look at another row. */
  function fromInput(input, primary, aliases) {
    if (!input || typeof input !== 'object') return null;
    if (Object.prototype.hasOwnProperty.call(input, primary) && !isBlank(input[primary])) {
      return input[primary];
    }
    var list = aliases || [];
    for (var i = 0; i < list.length; i++) {
      var key = list[i];
      if (Object.prototype.hasOwnProperty.call(input, key) && !isBlank(input[key])) {
        return input[key];
      }
    }
    if (Object.prototype.hasOwnProperty.call(input, primary)) return null;
    return null;
  }

  function unknownFieldsOf(record) {
    var out = [];
    [
      'source', 'observed_date', 'original_reference', 'alternative_reference',
      'seller', 'market', 'currency', 'tax', 'pack', 'channel', 'availability_meaning'
    ].forEach(function (k) {
      if (record[k] === null || record[k] === undefined) out.push(k);
    });
    return out;
  }

  /**
   * Build one competitor observation as evidence, not truth.
   * Every named field is present. Unknowns are null, never borrowed.
   */
  function buildRecord(input) {
    input = input || {};

    var source = name(fromInput(input, 'source', ['source_reference']));
    var observedDate = name(fromInput(input, 'observed_date', ['retrieved', 'observation_date']));
    var originalRef = name(fromInput(input, 'original_reference', ['part_number', 'reference']));
    var altRef = name(fromInput(input, 'alternative_reference', ['alt_reference', 'cross_reference']));
    var seller = name(fromInput(input, 'seller', []));
    var market = name(fromInput(input, 'market', []));
    var currency = name(fromInput(input, 'currency', []));
    if (currency) currency = currency.toUpperCase();
    var tax = name(fromInput(input, 'tax', []));
    var pack = copyPack(fromInput(input, 'pack', []));
    var channel = name(fromInput(input, 'channel', []));
    var availability = name(fromInput(input, 'availability_meaning', ['availability']));

    var record = {
      observation_id: name(fromInput(input, 'observation_id', ['id'])) || null,
      source: source,
      observed_date: observedDate,
      original_reference: originalRef,
      alternative_reference: altRef,
      seller: seller,
      market: market,
      currency: currency,
      tax: tax,
      pack: pack,
      channel: channel,
      availability_meaning: availability,
      role: name(fromInput(input, 'role', [])) || null,
      level: name(fromInput(input, 'level', ['price_level'])) || null,
      part_number: name(fromInput(input, 'part_number', [])) || originalRef,
      case_id: name(fromInput(input, 'case_id', [])) || null,
      amount: toNumberOrNull(fromInput(input, 'amount', ['price'])),
      amount_scope: name(fromInput(input, 'amount_scope', [])) || null,
      unit: name(fromInput(input, 'unit', [])) || null,
      vat_rate: toNumberOrNull(fromInput(input, 'vat_rate', [])),
      vat_rate_unit: name(fromInput(input, 'vat_rate_unit', [])) || null,
      delivery_included: (function () {
        if (!Object.prototype.hasOwnProperty.call(input, 'delivery_included')) return null;
        if (input.delivery_included === null) return null;
        return !!input.delivery_included;
      })(),
      delivery_cost_eur: toNumberOrNull(fromInput(input, 'delivery_cost_eur', [])),
      fx_to_eur: toNumberOrNull(fromInput(input, 'fx_to_eur', [])),
      fx_date: name(fromInput(input, 'fx_date', [])) || null,
      match: copyMatch(fromInput(input, 'match', [])),
      equivalence: copyMatch(fromInput(input, 'equivalence', [])),
      supersedes: name(fromInput(input, 'supersedes', [])) || null,
      saved_comparison_id: name(fromInput(input, 'saved_comparison_id', [])) || null,
      field_state: {},
      review: null,
      saved_case: null
    };

    RECORD_FIELDS.forEach(function (k) {
      if (!Object.prototype.hasOwnProperty.call(record, k)) record[k] = null;
    });

    record.unknown_fields = unknownFieldsOf(record);
    record.field_state = {
      source_known: record.source !== null,
      observed_date_known: record.observed_date !== null,
      currency_known: record.currency !== null,
      original_reference_known: record.original_reference !== null,
      channel_known: record.channel !== null,
      availability_known: record.availability_meaning !== null
    };
    record.as_evidence = true;
    record.as_truth = false;
    return record;
  }

  /**
   * Build many records. Each row is independent: a blank currency or reference
   * on row N never inherits the value from row N-1.
   */
  function buildRecords(inputs) {
    var list = inputs || [];
    var out = [];
    for (var i = 0; i < list.length; i++) {
      out.push(buildRecord(list[i]));
    }
    return out;
  }

  /**
   * Carry the same observation through a review step without rewriting source
   * or observed date.
   */
  function retainThroughReview(record, review) {
    record = record || {};
    review = review || {};
    var copy = JSON.parse(JSON.stringify(record));
    copy.review = {
      review_id: name(review.review_id) || null,
      reviewed_at: name(review.reviewed_at) || null,
      reviewer: name(review.reviewer) || null,
      note: name(review.note) || null
    };
    copy.source = record.source;
    copy.observed_date = record.observed_date;
    copy.source_retained = true;
    copy.observed_date_retained = true;
    return copy;
  }

  /**
   * Attach the observation to a saved case. Source and date stay the ones that
   * were observed; the case link is additive.
   */
  function attachToSavedCase(record, savedCase) {
    record = record || {};
    savedCase = savedCase || {};
    var copy = JSON.parse(JSON.stringify(record));
    copy.saved_case = {
      case_id: name(savedCase.case_id) || null,
      saved_at: name(savedCase.saved_at) || null,
      revision: toNumberOrNull(savedCase.revision)
    };
    if (copy.saved_case.case_id && !copy.case_id) copy.case_id = copy.saved_case.case_id;
    copy.source = record.source;
    copy.observed_date = record.observed_date;
    copy.source_retained = true;
    copy.observed_date_retained = true;
    return copy;
  }

  /** Map a record onto the offer shape that comparable.panel already accepts. */
  function toPanelOffer(record) {
    record = record || {};
    return {
      observation_id: record.observation_id,
      role: record.role,
      level: record.level,
      seller: record.seller,
      market: record.market,
      retrieved: record.observed_date,
      source_reference: record.source,
      part_number: record.part_number || record.original_reference,
      case_id: record.case_id,
      amount: record.amount,
      amount_scope: record.amount_scope,
      currency: record.currency,
      unit: record.unit,
      pack: record.pack,
      tax: record.tax,
      vat_rate: record.vat_rate,
      vat_rate_unit: record.vat_rate_unit,
      delivery_included: record.delivery_included,
      delivery_cost_eur: record.delivery_cost_eur,
      fx_to_eur: record.fx_to_eur,
      fx_date: record.fx_date,
      match: record.match,
      equivalence: record.equivalence,
      supersedes: record.supersedes,
      saved_comparison_id: record.saved_comparison_id,
      channel: record.channel,
      availability_meaning: record.availability_meaning,
      alternative_reference: record.alternative_reference
    };
  }

  /* ----- MARKET-06: outdated / conflicting observations stay visible ----- */

  function savedComparisonView(args) {
    args = args || {};
    var panel = args.panel || {};
    var savedIn = args.saved || null;
    var list = panel.saved_comparisons || [];
    var saved = null;
    if (savedIn && savedIn.comparison_id) {
      for (var i = 0; i < list.length; i++) {
        if (list[i].comparison_id === savedIn.comparison_id) { saved = list[i]; break; }
      }
    }
    if (!saved && list.length) saved = list[0];
    if (!saved && savedIn) {
      saved = {
        comparison_id: savedIn.comparison_id || null,
        observation_ids: savedIn.observation_ids || [],
        value: savedIn.value,
        basis: savedIn.basis || null,
        saved_at: savedIn.saved_at || null,
        rewritten: false,
        superseded_by_observation_ids: [],
        statement: 'No panel saved-comparison row was returned.'
      };
    }
    return {
      saved: saved,
      newer_rewrote_saved: !!(saved && saved.rewritten),
      panel: panel
    };
  }

  function conflictVisibilityView(args) {
    args = args || {};
    var panel = args.panel || {};
    var rows = (panel.eligible_offers || []).concat(panel.ineligible_offers || []);
    var visible = [];
    var dates = {};
    var sources = {};
    rows.forEach(function (r) {
      if (!r) return;
      if (r.visible === false) return;
      visible.push(r.observation_id);
      var raw = r.raw || {};
      dates[r.observation_id] = raw.retrieved || null;
      sources[r.observation_id] = raw.source_reference || null;
    });

    var amounts = [];
    (panel.eligible_offers || []).forEach(function (r) {
      if (r && r.raw && typeof r.raw.amount === 'number') {
        amounts.push({ id: r.observation_id, amount: r.raw.amount });
      }
    });
    amounts.sort(function (a, b) { return a.amount - b.amount; });
    var cheapestId = amounts.length ? amounts[0].id : null;
    var selected = panel.selected_observation_id || panel.decision_observation_id || null;
    var autoChose = !!(selected && cheapestId && selected === cheapestId);

    return {
      visible_observation_ids: visible,
      dates: dates,
      sources: sources,
      cheapest_observation_id: cheapestId,
      cheapest_auto_selected: autoChose,
      auto_chose_cheapest: autoChose,
      offers_shown_individually: !!(panel.aggregation && panel.aggregation.offers_shown_individually),
      panel: panel
    };
  }

  /* ----- MARKET-02: product match separate from lexical similarity ----- */

  function productMatchGate(offer) {
    offer = offer || {};
    var match = offer.match || {};
    var status = (match.status || '').toLowerCase();
    var pack = offer.pack || {};
    var reasons = [];

    if (pack && pack.contents_equivalent === false) {
      reasons.push('KIT_CONTENTS_NOT_EQUIVALENT');
    }
    if (pack && pack.declared_complete_kit === false) {
      reasons.push('INCOMPLETE_KIT');
    }
    if (status === 'unresolved' || status === '') {
      reasons.push('PRODUCT_MATCH_UNRESOLVED');
    }
    if (status === 'rejected') {
      reasons.push('PRODUCT_MATCH_REJECTED');
    }

    var accepted = (status === 'accepted')
      && reasons.indexOf('KIT_CONTENTS_NOT_EQUIVALENT') < 0
      && reasons.indexOf('INCOMPLETE_KIT') < 0
      && reasons.indexOf('PRODUCT_MATCH_UNRESOLVED') < 0
      && reasons.indexOf('PRODUCT_MATCH_REJECTED') < 0;

    return {
      accepted_price_comparison: accepted,
      match_status: status || 'unresolved',
      reason_codes: reasons,
      traceable: true,
      statement: accepted
        ? 'Product match is accepted on a named basis.'
        : 'Product match is not accepted for a price comparison; the observation stays traceable.'
    };
  }

  function matchTraceView(args) {
    args = args || {};
    var panel = args.panel || {};
    var eligible = (panel.eligible_offers || []).map(function (r) { return r.observation_id; });
    var ineligible = (panel.ineligible_offers || []);
    var excluded = ineligible.map(function (r) { return r.observation_id; });
    return {
      eligible_ids: eligible,
      excluded_ids: excluded,
      traceable_ids: eligible.concat(excluded),
      panel: panel
    };
  }


  /* ----- MARKET-03: packs only when contents are known ----- */

  function packCompareView(args) {
    args = args || {};
    var panel = args.panel || {};
    var packOffer = args.pack_offer || {};
    var pieceOffer = args.piece_offer || {};
    var packRow = null;
    var pieceRow = null;
    (panel.eligible_offers || []).concat(panel.ineligible_offers || []).forEach(function (r) {
      if (r.observation_id === packOffer.observation_id) packRow = r;
      if (r.observation_id === pieceOffer.observation_id) pieceRow = r;
    });
    var packUnit = packRow && packRow.comparable_value ? packRow.comparable_value.value : null;
    var pieceUnit = pieceRow && pieceRow.comparable_value ? pieceRow.comparable_value.value : null;
    var eq = !!(packOffer.pack && packOffer.pack.contents_equivalent === true);
    return {
      equivalence_accepted: eq,
      pack_unit_price: packUnit,
      piece_unit_price: pieceUnit,
      comparable: eq && packUnit !== null && pieceUnit !== null && packUnit === pieceUnit,
      panel: panel
    };
  }

  function packUnknownView(args) {
    args = args || {};
    var panel = args.panel || {};
    var offer = args.offer || {};
    var row = null;
    (panel.eligible_offers || []).concat(panel.ineligible_offers || []).forEach(function (r) {
      if (r.observation_id === offer.observation_id) row = r;
    });
    var derived = row && row.comparable_value ? row.comparable_value.value : null;
    var original = row && row.raw ? row.raw.amount : offer.amount;
    return {
      derived_unit_price: derived,
      original_amount: original,
      original_amount_retained: original !== null && original !== undefined,
      panel: panel
    };
  }


  /* ----- MARKET-04: currency / tax / delivery adjustments auditable ----- */

  function adjustmentAuditView(args) {
    args = args || {};
    var panel = args.panel || {};
    var offer = args.offer || {};
    var row = null;
    (panel.eligible_offers || []).concat(panel.ineligible_offers || []).forEach(function (r) {
      if (r.observation_id === offer.observation_id) row = r;
    });
    var adj = row && row.adjustment ? row.adjustment : { steps: [], value: null, ok: false };
    var steps = (adj.steps || []).map(function (s) {
      return {
        kind: s.step || s.kind || null,
        from: s.from,
        to: s.to,
        rule: s.rule || null,
        input_date: offer.fx_date || null
      };
    });
    return {
      original: {
        amount: offer.amount,
        currency: offer.currency
      },
      steps: steps,
      converted_value: adj.value,
      reproducible: !!(adj.ok && steps.length && offer.amount != null),
      retained_original: offer.amount !== null && offer.amount !== undefined,
      panel: panel
    };
  }

  function unknownAdjustmentView(args) {
    args = args || {};
    var panel = args.panel || {};
    var unknown = args.unknown || {};
    var row = null;
    (panel.eligible_offers || []).concat(panel.ineligible_offers || []).forEach(function (r) {
      if (r.observation_id === unknown.observation_id) row = r;
    });
    var codes = row && row.reasons ? row.reasons.map(function (r) { return r.code; }) : [];
    return {
      assumed_equal: false,
      unknown_codes: codes,
      panel: panel
    };
  }


  /* ----- MARKET-05: commercial price levels stay separate ----- */

  function levelBridgeView(args) {
    args = args || {};
    var without = args.panel_without_bridge || {};
    var withB = args.panel_with_bridge || {};
    var excluded = (without.ineligible_offers || []).map(function (r) { return r.observation_id; });
    var indexAllowedWithout = !!(without.price_positioning && without.price_positioning.index_allowed);
    var indexAllowedWith = (withB.ineligible_offers || []).length === 0;
    return {
      direct_index_allowed_without_bridge: indexAllowedWithout,
      direct_index_allowed_with_bridge: indexAllowedWith,
      excluded_without_bridge: excluded,
      panel_without_bridge: without,
      panel_with_bridge: withB
    };
  }

  function referenceValuationView(args) {
    args = args || {};
    var comparableApi = null;
    try {
      if (typeof require === 'function') {
        comparableApi = require('./comparable.js');
      }
    } catch (e) { comparableApi = null; }
    if (!comparableApi && root.AIMComparable) comparableApi = root.AIMComparable;

    var asRevenue = comparableApi
      ? comparableApi.assertLevelUse('reference_dealer', 'dealer_revenue')
      : { ok: false, statement: 'comparable module unavailable' };
    var asMargin = comparableApi
      ? comparableApi.assertLevelUse('reference_dealer', 'dealer_margin')
      : { ok: false, statement: 'comparable module unavailable' };

    return {
      shown_as_actual_revenue: !!(asRevenue && asRevenue.ok),
      shown_as_dealer_margin: !!(asMargin && asMargin.ok),
      forbidden_labels: ['actual downstream revenue', 'dealer margin earned'],
      display_labels: ['reference dealer price', 'comparison convention'],
      statement: (asRevenue && asRevenue.statement) || '',
      panel: args.panel || null
    };
  }

  var API = {
    RECORD_FIELDS: RECORD_FIELDS,
    buildRecord: buildRecord,
    buildRecords: buildRecords,
    retainThroughReview: retainThroughReview,
    attachToSavedCase: attachToSavedCase,
    toPanelOffer: toPanelOffer,
    savedComparisonView: savedComparisonView,
    conflictVisibilityView: conflictVisibilityView,
    productMatchGate: productMatchGate,
    matchTraceView: matchTraceView,
    packCompareView: packCompareView,
    packUnknownView: packUnknownView,
    adjustmentAuditView: adjustmentAuditView,
    unknownAdjustmentView: unknownAdjustmentView,
    levelBridgeView: levelBridgeView,
    referenceValuationView: referenceValuationView
  };

  root.AIMMarketObservation = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
