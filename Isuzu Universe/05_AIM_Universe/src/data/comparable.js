/* ===========================================================================
   Comparable-price panel (MARKET-07) and the missing-evidence request
   (MARKET-08).

   Read this before wiring the panel to a screen.

   WHY THIS FILE COMPUTES AND DOES NOT DRAW
     The view layer is being changed while this was written, and two agents
     writing one concern is what damaged this project twice. So this file
     computes a panel and returns it; it renders nothing. Every field it returns
     is named in CONTRACT below, so a screen can be wired to it later without
     anyone having to decide again what a comparison is.

   WHAT IS REUSED, NOT REBUILT
     The market rules were already implemented in src/data/evidence.js
     (MARKET-01 to MARKET-06). This file calls them and does not repeat them:

       price level               -> evidence.priceLevel
       like-for-like check        -> evidence.assertSamePriceLevel
       pack contents              -> evidence.normalisePack
       price per piece            -> evidence.perPiecePrice
       currency, tax, delivery    -> evidence.adjustToComparable
       product equivalence        -> evidence.productEquivalence
       age and conflicting prices -> evidence.observationConflicts

     Where evidence.js does not yet name a price level that MARKET-05 requires,
     the level is declared here and listed in REQUESTED_SHARED_LEVELS so its
     owner can fold it in. A second copy of a level that already exists is not
     created: evidence.js answers first.

   WHAT THIS PANEL REFUSES TO DO
     - It does not choose an observation for you. With no approved selection
       rule, every comparable offer is returned on its own and
       selected_observation_id is null. The cheapest observation is not the
       right one; it is the first row of a list.
     - It does not summarise without an approved aggregation rule. No rule means
       no summary figure, not an invented average.
     - It does not drop an observation quietly. Anything that is not eligible
       comes back with a named reason and its own record intact.
     - It does not mix commercial price levels, and it does not treat an
       advertised retail price as proof that our own net terms are too high.
     - It does not carry a restricted cost field. Only named fields are copied.
     - It does not link a comparison into the scenario unless the comparison is
       supported. No price action is certified from an index.
   =========================================================================== */
(function (root) {
  'use strict';

  var evidence = (typeof module === 'object' && module.exports)
    ? require('./evidence.js') : root.AIMEvidence;

  /* --------------------------------------------------------------- helpers -- */

  function isBlank(v) {
    return v === null || v === undefined || (typeof v === 'string' && v.trim() === '');
  }
  function toNumberOrNull(v) {
    if (isBlank(v)) return null;
    var n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  function round2(x) { return x === null ? null : Math.round(x * 100) / 100; }
  function name(v) { return String(v === null || v === undefined ? '' : v).trim(); }
  function unique(list) {
    var seen = {}, out = [];
    (list || []).forEach(function (v) {
      if (isBlank(v)) return;
      if (!seen[v]) { seen[v] = 1; out.push(v); }
    });
    return out;
  }
  function median(values) {
    var v = (values || []).filter(function (x) { return x !== null && x !== undefined; }).slice();
    if (!v.length) return null;
    v.sort(function (a, b) { return a - b; });
    var mid = Math.floor(v.length / 2);
    return v.length % 2 ? v[mid] : round2((v[mid - 1] + v[mid]) / 2);
  }

  /* --------------------------------------------------------- price levels -- */

  /* The four commercial price levels MARKET-05 requires kept apart, plus the
     two halves of our own terms. A level is not a label: it decides what the
     figure may be read as and what it may be compared with. */
  var PANEL_LEVELS = {
    isze_net_distributor: {
      label: 'ISZE net distributor price',
      what_it_is: 'the net price on our own terms to a distributor',
      is_our_terms: true, is_actual_transaction: true,
      is_advertised_observation: false, is_derived_reference: false, restricted: false
    },
    isze_net_list: {
      label: 'ISZE net list price, from the carried price list',
      what_it_is: 'a carried list figure on our own terms; it is not a transaction',
      is_our_terms: true, is_actual_transaction: false,
      is_advertised_observation: false, is_derived_reference: false, restricted: false
    },
    distributor_dealer_transaction: {
      label: 'Distributor or dealer transaction price',
      what_it_is: 'a price that actually changed hands between a distributor and a dealer',
      is_our_terms: false, is_actual_transaction: true,
      is_advertised_observation: false, is_derived_reference: false, restricted: false
    },
    public_advertised_retail: {
      label: 'Public advertised retail price',
      what_it_is: 'a dated advertised price by another seller; the seller is a different party '
        + 'and the pack, tax and delivery basis may not be stated',
      is_our_terms: false, is_actual_transaction: false,
      is_advertised_observation: true, is_derived_reference: false, restricted: false
    },
    oem_peer_retail: {
      label: 'OEM peer retail price',
      what_it_is: 'a reference dealer price published by a peer manufacturer, used as a '
        + 'comparison convention only',
      is_our_terms: false, is_actual_transaction: false,
      is_advertised_observation: true, is_derived_reference: false, restricted: false
    }
  };

  /* Levels that evidence.js already names keep their attributes from there.
     Only the traits are restated here, next to the other levels, so the panel
     has one table to read. */
  var SHARED_LEVEL_TRAITS = {
    list: { is_our_terms: true, is_actual_transaction: false },
    observed_billing_average: { is_our_terms: true, is_actual_transaction: true },
    competitor_advertised: { is_advertised_observation: true, is_actual_transaction: false },
    reference_dealer: { is_derived_reference: true, is_actual_transaction: false },
    supplier_cost: { restricted: true, is_our_terms: false, is_actual_transaction: false }
  };

  /* Levels MARKET-05 needs that evidence.js does not name yet. Reported rather
     than assumed: the owner of evidence.js should add them to PRICE_LEVELS so
     there is one definition and not two. Until then this file supplies them. */
  var REQUESTED_SHARED_LEVELS = [
    'isze_net_distributor', 'isze_net_list', 'distributor_dealer_transaction',
    'public_advertised_retail', 'oem_peer_retail'
  ];

  function levelInfo(levelId) {
    var shared = evidence.priceLevel(levelId);
    var named = shared.label !== 'Unnamed price level';
    var own = PANEL_LEVELS[levelId] || null;
    var traits = SHARED_LEVEL_TRAITS[levelId] || own || null;

    if (!named && !own) {
      return {
        id: isBlank(levelId) ? null : String(levelId),
        label: 'Unnamed price level',
        named: false,
        what_it_is: null,
        is_our_terms: null, is_actual_transaction: null,
        is_advertised_observation: null, is_derived_reference: null,
        restricted: null,
        statement: shared.statement
      };
    }
    return {
      id: String(levelId),
      label: own ? own.label : shared.label,
      named: true,
      what_it_is: (own && own.what_it_is) || shared.definition || null,
      source: own ? 'declared here pending a shared definition' : 'evidence.js price levels',
      is_our_terms: !!(traits && traits.is_our_terms),
      is_actual_transaction: !!(traits && traits.is_actual_transaction),
      is_advertised_observation: !!(traits && traits.is_advertised_observation),
      is_derived_reference: !!(traits && traits.is_derived_reference),
      restricted: !!(traits && traits.restricted),
      statement: shared.statement
    };
  }

  /* MARKET-05, second required item. A derived reference figure is a comparison
     convention. It may not be shown as revenue that was actually earned, or as
     a dealer's actual margin, because it is neither. */
  var USES = ['competitiveness_comparison', 'dealer_revenue', 'dealer_margin', 'purchasing_cost'];

  function assertLevelUse(levelId, intendedUse) {
    var info = levelInfo(levelId);
    var use = name(intendedUse);
    if (USES.indexOf(use) < 0) {
      return { ok: false, refused: true,
        statement: 'The intended use "' + (use || 'not stated') + '" is not one of the declared uses '
          + '(' + USES.join(', ') + '), so nothing is stated about this figure.' };
    }
    if (!info.named) {
      return { ok: false, refused: true, level: info,
        statement: info.statement };
    }
    if (info.restricted) {
      return { ok: false, refused: true, level: info,
        statement: 'A parts purchase cost is what ISZE pays. It is not a selling price at any '
          + 'level, so it is refused for "' + use + '".' };
    }
    if (info.is_derived_reference && (use === 'dealer_revenue' || use === 'dealer_margin')) {
      return { ok: false, refused: true, level: info,
        statement: 'A ' + info.label.toLowerCase() + ' is a comparison convention, not a '
          + 'transaction. It cannot be shown as ' + (use === 'dealer_revenue'
            ? 'revenue that was actually earned' : 'a dealer\u2019s actual margin') + '.' };
    }
    if (info.is_advertised_observation && use === 'dealer_margin') {
      return { ok: false, refused: true, level: info,
        statement: 'An advertised price by another seller does not state what that seller paid, '
          + 'so it cannot be shown as a dealer margin.' };
    }
    if (use === 'purchasing_cost' && !info.restricted) {
      return { ok: false, refused: true, level: info,
        statement: 'A selling price at the ' + info.label.toLowerCase() + ' level is not a '
          + 'purchasing cost.' };
    }
    return { ok: true, refused: false, level: info,
      statement: 'A ' + info.label.toLowerCase() + ' may be used for "' + use + '".' };
  }

  /* --------------------------------------------------- named exclusion codes -- */

  /* Every reason an observation can be left out of the comparable set. A code in
     a returned panel always resolves here, so a reader is never shown a bare
     code. */
  var EXCLUSION_CODES = {
    NO_OBSERVATION_ID: 'excluded',
    OBSERVATION_FOR_ANOTHER_CASE: 'excluded',
    ROLE_NOT_STATED: 'excluded',
    NO_PRICE_LEVEL_DECLARED: 'excluded',
    RESTRICTED_COST_IS_NOT_A_SELLING_PRICE: 'excluded',
    LEVEL_NOT_LIKE_FOR_LIKE: 'excluded',
    NO_ACCEPTED_LEVEL_BRIDGE: 'excluded',
    PRODUCT_MATCH_REJECTED: 'excluded',
    PRODUCT_MATCH_UNRESOLVED: 'excluded',
    NO_PRODUCT_EQUIVALENCE_DECLARATION: 'excluded',
    KIT_CONTENTS_NOT_EQUIVALENT: 'excluded',
    UNIT_NOT_LIKE_FOR_LIKE: 'excluded',
    SUPERSEDED_OBSERVATION: 'excluded',
    NO_AMOUNT_RECORDED: 'excluded',
    CURRENCY_NOT_STATED: 'unresolved',
    VAT_RATE_UNIT_NOT_STATED: 'unresolved',
    NO_DATED_RATE_TO_EUR: 'unresolved',
    FX_DATE_NOT_STATED: 'unresolved',
    TAX_BASIS_NOT_STATED: 'unresolved',
    TAX_RATE_NOT_STATED: 'unresolved',
    DELIVERY_BASIS_NOT_STATED: 'unresolved',
    DELIVERY_COST_NOT_SUPPLIED: 'unresolved',
    PACK_CONTENTS_UNKNOWN: 'unresolved',
    ADJUSTMENT_NOT_AUDITABLE: 'unresolved',
    AGE_BEYOND_DECLARED_POLICY: 'excluded'
  };

  function explainExclusion(code) {
    var kind = EXCLUSION_CODES[code] || null;
    return {
      code: code,
      kind: kind,
      known: !!kind,
      statement: kind
        ? 'This observation is not in the comparable set. The reason is recorded on the row.'
        : 'This reason code is not declared here, so it is reported as unknown rather than '
          + 'presented as a reviewed reason.'
    };
  }

  /* The sentences evidence.js returns when an adjustment cannot be completed.
     Each one maps to a declared code, so a missing currency or tax is reported
     as a missing currency or tax and never as a zero. */
  var UNRESOLVED_CODE_MAP = [
    ['no amount was supplied', 'NO_AMOUNT_RECORDED'],
    ['tax inclusive and the rate is not stated', 'TAX_RATE_NOT_STATED'],
    ['tax basis is not stated', 'TAX_BASIS_NOT_STATED'],
    ['no dated rate to eur was supplied', 'NO_DATED_RATE_TO_EUR'],
    ['without the date it was taken on', 'FX_DATE_NOT_STATED'],
    ['currency is not stated', 'CURRENCY_NOT_STATED'],
    ['no delivered cost was supplied', 'DELIVERY_COST_NOT_SUPPLIED'],
    ['delivery basis is not stated', 'DELIVERY_BASIS_NOT_STATED']
  ];

  function codeForUnresolved(text) {
    /* Both sides are lowered: a code lookup that is case-sensitive is how a
       missing rate gets reported as some other kind of gap. */
    var t = name(text).toLowerCase();
    for (var i = 0; i < UNRESOLVED_CODE_MAP.length; i++) {
      if (t.indexOf(UNRESOLVED_CODE_MAP[i][0].toLowerCase()) >= 0) return UNRESOLVED_CODE_MAP[i][1];
    }
    /* A tax-inclusive amount with a rate the row does not describe. The rate is
       a percentage or an 0.20 fraction; guessing which is a hundred-fold error,
       so the row is unresolved instead. */
    if (t.indexOf('does not state whether that is a percentage or a fraction') >= 0) {
      return 'VAT_RATE_UNIT_NOT_STATED';
    }
    return 'ADJUSTMENT_NOT_AUDITABLE';
  }

  /* --------------------------------------------------------------- contract -- */

  var OBSERVATION_FIELDS = [
    'observation_id', 'role', 'level', 'seller', 'market', 'retrieved', 'source_reference',
    'part_number', 'case_id', 'amount', 'amount_scope', 'currency', 'unit',
    'pack', 'tax', 'vat_rate', 'vat_rate_unit', 'delivery_included', 'delivery_cost_eur',
    'fx_to_eur', 'fx_date', 'match', 'equivalence', 'supersedes', 'saved_comparison_id'
  ];

  var PANEL_FIELDS = [
    'contract', 'case', 'observations_in', 'raw_records_retained',
    'selected_basis', 'eligible_offers', 'ineligible_offers', 'aggregation',
    'flags', 'saved_comparisons', 'purchasing_movement', 'price_positioning',
    'scenario_link', 'price_action_certified', 'statement'
  ];

  var CONTRACT = {
    version: 1,
    audience: 'internal',
    purpose: 'Compute a comparable-price panel with named exclusions, and the request for the '
      + 'comparison evidence that is actually missing. Renders nothing.',
    observation: OBSERVATION_FIELDS,
    panel: PANEL_FIELDS,
    declared_roles: ['isze_terms', 'competitor'],
    declared_match_status: ['accepted', 'unresolved', 'rejected'],
    declared_match_basis: ['exact_part_number', 'declared_equivalence', 'cross_reference',
      'candidate', 'rejected'],
    excluded_field_names: [
      'cost', 'cost_eur', 'cost_basis_id', 'supplier_cost', 'unit_cost', 'fob',
      'margin', 'margin_after_pct', 'gp_after'
    ],
    excluded_field_note: 'These names are never copied into the panel. A restricted purchasing '
      + 'cost is not a selling price at any level and does not belong in a price comparison.',
    requested_shared_fields: REQUESTED_SHARED_LEVELS
  };

  /* ------------------------------------------------------ reading one observation -- */

  /* Only declared names are copied. Anything else is counted and left behind,
     so a restricted cost table cannot travel into a panel by accident. */
  function observationFrom(offer, declarations) {
    offer = offer || {};
    declarations = declarations || {};
    var kept = [], dropped = 0;
    var out = {};
    OBSERVATION_FIELDS.forEach(function (f) {
      if (Object.prototype.hasOwnProperty.call(offer, f)) { out[f] = offer[f]; kept.push(f); }
    });
    Object.keys(offer).forEach(function (k) {
      if (OBSERVATION_FIELDS.indexOf(k) < 0) dropped += 1;
    });

    var o = {
      observation_id: name(out.observation_id) || null,
      role: name(out.role) || null,
      level: name(out.level) || null,
      seller: name(out.seller) || null,
      market: name(out.market) || null,
      retrieved: name(out.retrieved) || null,
      source_reference: name(out.source_reference) || null,
      part_number: name(out.part_number) || null,
      case_id: name(out.case_id) || null,
      amount: toNumberOrNull(out.amount),
      amount_scope: name(out.amount_scope) || null,
      currency: name(out.currency) ? name(out.currency).toUpperCase() : null,
      unit: name(out.unit) || null,
      pack: out.pack || null,
      tax: name(out.tax) || null,
      vat_rate: toNumberOrNull(out.vat_rate),
      vat_rate_unit: name(out.vat_rate_unit) || null,
      delivery_included: out.delivery_included === undefined ? null : out.delivery_included,
      delivery_cost_eur: toNumberOrNull(out.delivery_cost_eur),
      fx_to_eur: toNumberOrNull(out.fx_to_eur),
      fx_date: name(out.fx_date) || null,
      match: out.match || null,
      equivalence: out.equivalence || null,
      supersedes: name(out.supersedes) || null,
      saved_comparison_id: name(out.saved_comparison_id) || null,
      fields_kept: kept,
      fields_left_behind: dropped,
      raw_unchanged: true
    };
    return o;
  }

  /* ----------------------------------------------------------------- basis -- */

  /* The comparison basis is named by the reviewer, not chosen by this file. The
     panel will list which levels are present, and stop there: choosing one is a
     commercial decision and there is no approved rule to make it here. */
  function candidateBases(observations) {
    var byLevel = {};
    (observations || []).forEach(function (o) {
      var id = name(o && o.level) || '(not stated)';
      if (!byLevel[id]) byLevel[id] = { level: id, offers: 0, units: {} };
      byLevel[id].offers += 1;
      var u = name(o && o.unit) || '(not stated)';
      byLevel[id].units[u] = (byLevel[id].units[u] || 0) + 1;
    });
    var rows = Object.keys(byLevel).map(function (k) {
      var info = levelInfo(k === '(not stated)' ? null : k);
      return {
        level: byLevel[k].level,
        level_label: info.label,
        offers: byLevel[k].offers,
        units: Object.keys(byLevel[k].units),
        eligible_only_if_named: true
      };
    });
    return {
      candidates: rows,
      named: null,
      statement: rows.length
        ? rows.length + ' price level(s) are present. This list is not a selection: the basis has to '
          + 'be named by a reviewer, because no approved rule chooses one.'
        : 'No observation carries a price level, so there is no candidate basis to name.'
    };
  }

  function bridgeCovers(bridge, from, to) {
    if (!bridge) return false;
    var a = name(bridge.from_level), b = name(bridge.to_level);
    if (isBlank(a) || isBlank(b)) return false;
    return (a === from && b === to) || (a === to && b === from);
  }

  function bridgeCheck(bridge, from, to) {
    if (!bridge) return { ok: false, supplied: false, statement: 'No accepted bridge is supplied.' };
    var missing = [];
    if (isBlank(bridge.bridge_id)) missing.push('no bridge identifier');
    if (isBlank(bridge.approved_by)) missing.push('no one is named as having accepted it');
    if (isBlank(bridge.statement)) missing.push('no statement of what the bridge does');
    if (missing.length) {
      return { ok: false, supplied: true,
        statement: 'A bridge was supplied but it is not accepted, because it has ' + missing.join(', ') + '.' };
    }
    if (!bridgeCovers(bridge, from, to)) {
      return { ok: false, supplied: true,
        statement: 'The supplied bridge is from ' + bridge.from_level + ' to ' + bridge.to_level
          + ', which does not cover ' + from + ' and ' + to + '.' };
    }
    return { ok: true, supplied: true, bridge_id: bridge.bridge_id, approved_by: bridge.approved_by,
      statement: 'An accepted bridge from ' + from + ' to ' + to + ' is supplied: ' + bridge.statement };
  }

  /* ------------------------------------------------------- one observation -- */

  function evaluateObservation(o, ctx) {
    var reasons = [];
    function refuse(code, text) {
      reasons.push({ code: code, kind: EXCLUSION_CODES[code] || 'excluded', statement: text });
    }

    /* A - can this row be traced at all. */
    if (isBlank(o.observation_id)) {
      refuse('NO_OBSERVATION_ID', 'The row carries no observation identifier, so there is nothing '
        + 'to trace a comparison back to. It is reported and not counted.');
    }
    if (!isBlank(o.case_id) && !isBlank(ctx.case_id) && o.case_id !== ctx.case_id) {
      refuse('OBSERVATION_FOR_ANOTHER_CASE', 'The row belongs to case ' + o.case_id
        + ', not to ' + ctx.case_id + '. A row for another case is not attached to this one.');
    }

    /* B - which commercial price level, and may it sit beside the basis. */
    var info = levelInfo(o.level);
    if (isBlank(o.role) || ctx.declared_roles.indexOf(o.role) < 0) {
      refuse('ROLE_NOT_STATED', 'The row does not state whether it is our own terms or an '
        + 'observation by another seller, so the reader cannot tell whose price it is.');
    }
    if (!info.named) {
      refuse('NO_PRICE_LEVEL_DECLARED', info.statement);
    } else if (info.restricted) {
      refuse('RESTRICTED_COST_IS_NOT_A_SELLING_PRICE', 'This row is a parts purchase cost. It is '
        + 'what ISZE pays, not a selling price, so it is not part of a price comparison.');
    }

    var bridge = { ok: false, supplied: false, statement: 'No basis was named, so no bridge was checked.' };
    if (ctx.basis) {
      var same = evidence.assertSamePriceLevel({ price_level: ctx.basis.level }, { price_level: o.level });
      if (!same.comparable && info.named && !info.restricted) {
        bridge = bridgeCheck(ctx.bridge, ctx.basis.level, info.id);
        if (bridge.ok) {
          o.bridge_applied = { bridge_id: bridge.bridge_id, approved_by: bridge.approved_by,
            from_level: ctx.basis.level, to_level: info.id };
        } else if (info.is_advertised_observation) {
          refuse('NO_ACCEPTED_LEVEL_BRIDGE', 'An advertised retail price is a dated observation by '
            + 'another seller, and the basis is ' + levelInfo(ctx.basis.level).label.toLowerCase()
            + '. The two are different commercial price levels. They are shown side by side and are '
            + 'not put into one index, and an advertised retail price is not proof that our own net '
            + 'terms are too high. ' + bridge.statement);
        } else {
          refuse('LEVEL_NOT_LIKE_FOR_LIKE', same.statement);
        }
      }
    }

    /* C - is it the same product. */
    var match = o.match || {};
    var matchStatus = name(match.status) || 'unresolved';
    var matchBasis = name(match.basis) || 'unresolved';
    var equivalence = { equivalent: null, statement: null };
    if (matchStatus === 'rejected' || matchBasis === 'rejected') {
      refuse('PRODUCT_MATCH_REJECTED', 'The source rejected this match'
        + (name(match.reason) ? ': ' + match.reason : '')
        + '. A rejected match stays visible and is kept out of the comparison.');
    } else if (matchBasis === 'exact_part_number') {
      equivalence = { equivalent: true, basis: 'the listing names the same part number',
        statement: 'The listing names the same part number. That identifies the product; it does '
          + 'not state the kit contents, which is a separate question.' };
    } else if (matchBasis === 'declared_equivalence') {
      equivalence = evidence.productEquivalence({
        equivalence_declared: o.equivalence && o.equivalence.declared,
        equivalence_declared_by: o.equivalence && o.equivalence.declared_by,
        similarity_ratio: o.equivalence && o.equivalence.similarity_ratio
      });
      if (equivalence.equivalent !== true) {
        refuse('NO_PRODUCT_EQUIVALENCE_DECLARATION', equivalence.statement);
      }
    } else {
      equivalence = evidence.productEquivalence({
        equivalence_declared: o.equivalence && o.equivalence.declared,
        equivalence_declared_by: o.equivalence && o.equivalence.declared_by,
        similarity_ratio: o.equivalence && o.equivalence.similarity_ratio
      });
      if (equivalence.equivalent !== true) {
        refuse('PRODUCT_MATCH_UNRESOLVED', 'The match is recorded as ' + matchStatus
          + ' on a basis of ' + matchBasis + '. A seller cross-reference, or a similar description, '
          + 'creates a candidate to inspect. It is not an approved equivalent and not approved '
          + 'fitment. ' + equivalence.statement);
      }
    }

    /* D - pack and unit. A price per pack is normalised only on stated contents. */
    var pack = evidence.normalisePack({
      contents: o.pack && o.pack.contents, kit_contents: o.pack && o.pack.kit_contents,
      declared_unit: o.unit, pack_quantity: o.amount_scope === 'per_pack' ? 1 : null
    });
    var scope = name(o.amount_scope);
    if (scope !== 'per_piece' && scope !== 'per_pack') {
      refuse('PACK_CONTENTS_UNKNOWN', 'The row does not state whether the quoted amount is for one '
        + 'piece or for a pack, so the quantity the price covers is unknown.');
    } else if (scope === 'per_pack' && !pack.normalised) {
      refuse('PACK_CONTENTS_UNKNOWN', pack.statement + ' The original observation is kept: only the '
        + 'derived per-piece figure is withheld.');
    }
    if (o.pack && o.pack.contents_equivalent === false) {
      refuse('KIT_CONTENTS_NOT_EQUIVALENT', 'The two packs do not hold equivalent contents. A '
        + 'housing and an element, or an incomplete kit and a full kit, are not the same product.');
    }
    var derivedUnit = pack.normalised ? 'piece' : (name(o.unit) || null);
    if (ctx.basis && !isBlank(ctx.basis.unit) && derivedUnit !== ctx.basis.unit) {
      refuse('UNIT_NOT_LIKE_FOR_LIKE', 'The basis counts in ' + ctx.basis.unit
        + ' and this row works out to ' + (derivedUnit || 'an unstated unit')
        + '. Prices per axle, per kit and per piece are not compared as if they were the same.');
    }

    /* E - money. The whole adjustment rule lives in evidence.js; this only
       labels the reason it could not finish. */
    var vatRate = toNumberOrNull(o.vat_rate);
    /* `ok: false` with no code means "no rate on this row at all", which the
       shared rule already reports in its own words as a missing rate. A code
       means "a rate is present but its unit is not stated", which is a
       different fault and needs its own reason. */
    var vatUnit = { ok: false, code: null };
    if (vatRate !== null) {
      if (o.vat_rate_unit === 'percent') vatUnit = { ok: true, value: vatRate };
      else if (o.vat_rate_unit === 'fraction') vatUnit = { ok: true, value: round2(vatRate * 100) };
      else {
        /* Never infer the unit from the size of the number: a rate of 0.2 and a
           rate of 20 are the same digits two orders of magnitude apart, and the
           difference between them is a real price error, not a rounding one. */
        vatUnit = { ok: false, code: 'VAT_RATE_UNIT_NOT_STATED' };
      }
    }

    var adjustment = evidence.adjustToComparable(o.amount, {
      tax: o.tax,
      /* The rate and its unit travel together. The row declares the unit and
         this file converts the fraction to the percentage the shared rule asks
         for; the rule is told which unit it is being given, so neither side has
         to infer it from the size of the number. A row that declares neither is
         passed a null rate with the unit 'not stated', and the shared rule
         reports that in its own words. */
      vat_rate: vatUnit.ok ? vatUnit.value : null,
      vat_rate_unit: vatUnit.ok ? 'percent' : 'not stated',
      currency: o.currency,
      fx_to_eur: o.fx_to_eur, fx_date: o.fx_date,
      delivery_included: o.delivery_included, delivery_cost_eur: o.delivery_cost_eur
    });
    if (!adjustment) {
      adjustment = { ok: false, value: null, value_before_adjustment: null, steps: [],
        unresolved: ['the shared adjustment rule returned nothing'] };
    }
    if (vatUnit.ok) {
      adjustment.vat_rate_used = { passed_to_the_rule: vatUnit.value,
        declared_by_the_row_as: o.vat_rate_unit, original_value: vatRate };
    } else if (o.tax === 'included' && vatUnit.code === 'VAT_RATE_UNIT_NOT_STATED') {
      /* A tax-inclusive amount with a rate whose unit nobody stated is exactly
         the case where a silent assumption produces a confident wrong number. */
      adjustment.ok = false;
      adjustment.value = null;
      adjustment.unresolved = adjustment.unresolved.concat([
        'the observation carries a tax rate of ' + vatRate + ' but does not state whether that is a '
        + 'percentage or a fraction, and the two differ by a factor of one hundred']);
    }
    if (!adjustment.ok) {
      adjustment.unresolved.forEach(function (u) { refuse(codeForUnresolved(u), u + '.'); });
    }

    /* The figure a comparison can be built on. A quoted per-piece amount is
       already on the basis unit. A quoted per-pack amount is divided by the
       stated contents, and only when the contents are stated. The adjusted
       amount itself is never thrown away by this: it stays on the row. */
    var perPiece = evidence.perPiecePrice(adjustment.value, pack);
    var comparableValue;
    if (scope === 'per_piece') {
      comparableValue = {
        value: adjustment.value,
        how: 'the quote is already for one ' + (o.unit || 'unit'),
        statement: adjustment.ok
          ? 'The quote is already for one ' + (o.unit || 'unit') + ', so no conversion is applied.'
          : 'The amount is not on a comparable basis yet, so no comparable figure is stated.'
      };
    } else if (scope === 'per_pack') {
      comparableValue = {
        value: perPiece.ok ? perPiece.amount_per_piece : null,
        how: perPiece.ok ? 'derived from the stated pack of ' + perPiece.pieces_per_pack + ' piece(s)'
          : 'blocked: the pack contents are not stated, or the amount is not yet comparable',
        statement: perPiece.ok
          ? 'Derived by dividing the adjusted pack price by the stated contents. The quoted pack '
            + 'price is kept beside it.'
          : 'No comparable figure is stated for this pack. ' + perPiece.statement
      };
    } else {
      comparableValue = {
        value: null, how: 'not stated',
        statement: 'The row does not state whether the quote is for a piece or for a pack, so no '
          + 'comparable figure is stated.'
      };
    }

    /* F - freshness. Without an approved policy this is a flag and a review
       request, not an expiry invented here. */
    var flags = [];
    var age = null;
    if (!isBlank(o.retrieved) && !isBlank(ctx.as_of)) {
      var then = Date.parse(o.retrieved), now = Date.parse(ctx.as_of);
      if (Number.isFinite(then) && Number.isFinite(now)) {
        age = Math.round((now - then) / 86400000);
        if (ctx.freshness_policy) {
          if (age > ctx.freshness_policy.max_age_days) {
            refuse('AGE_BEYOND_DECLARED_POLICY', 'The observation is ' + age + ' day(s) old and the '
              + 'declared policy "' + ctx.freshness_policy.policy_id + '" allows '
              + ctx.freshness_policy.max_age_days + ' day(s). The policy is named and dated, so this '
              + 'is the one case where age decides eligibility.');
          }
        } else if (age > ctx.review_point_days) {
          flags.push({ code: 'AGE_BEYOND_REVIEW_POINT', age_days: age,
            statement: 'The observation is ' + age + ' day(s) old and is past the '
              + ctx.review_point_days + '-day review point. No expiry policy is approved, so age '
              + 'does not decide eligibility here: the date is shown and a review is asked for.' });
        }
      }
    }
    if (!isBlank(o.supersedes)) {
      flags.push({ code: 'SUPERSEDED_SOMETHING', supersedes: o.supersedes,
        statement: 'This row states that it replaces observation ' + o.supersedes
          + '. The earlier observation is not removed by that statement.' });
    }

    return { reasons: reasons, flags: flags, pack: pack, adjustment: adjustment,
      equivalence: equivalence, age_days: age, derived_unit: derivedUnit, info: info,
      comparable_value: comparableValue,
      match: { status: matchStatus, basis: matchBasis } };
  }

  /* ------------------------------------------------------------------- panel -- */

  function panel(caseContext, observations, opts) {
    caseContext = caseContext || {}; opts = opts || {};
    var list = observations || [];

    var ctx = {
      case_id: name(caseContext.case_id) || null,
      declared_roles: CONTRACT.declared_roles,
      basis: (!isBlank(opts.basis_level) && !isBlank(opts.basis_unit))
        ? { level: name(opts.basis_level), unit: name(opts.basis_unit),
            named_by: name(opts.basis_named_by) || 'not stated' }
        : null,
      bridge: opts.level_bridge || null,
      as_of: name(opts.as_of) || null,
      review_point_days: toNumberOrNull(opts.review_point_days) === null
        ? 180 : toNumberOrNull(opts.review_point_days),
      freshness_policy: null
    };
    var policy = opts.freshness_policy;
    if (policy && !isBlank(policy.policy_id) && !isBlank(policy.approved_by)
        && toNumberOrNull(policy.max_age_days) !== null) {
      ctx.freshness_policy = policy;
    }

    /* Marked inputs are never written to. A caller holding the raw record keeps
       the raw record. */
    var snapshotBefore = JSON.stringify(list);
    var prepared = list.map(function (o) { return observationFrom(o, null); });

    var supersededBy = {};
    prepared.forEach(function (o) {
      if (!isBlank(o.supersedes)) supersededBy[o.supersedes] = o.observation_id;
    });

    var eligible = [], ineligible = [], allFlags = [];

    prepared.forEach(function (o) {
      var verdict = evaluateObservation(o, ctx);
      var reasons = verdict.reasons.slice();
      if (supersededBy[o.observation_id]) {
        reasons.push({ code: 'SUPERSEDED_OBSERVATION', kind: EXCLUSION_CODES.SUPERSEDED_OBSERVATION,
          statement: 'Observation ' + supersededBy[o.observation_id] + ' states that it replaces '
            + 'this one. This row stays visible; it is not the row to build a current comparison '
            + 'from, and any comparison already saved with it is left as it was.' });
      }

      var row = {
        observation_id: o.observation_id,
        role: o.role, level: o.level, level_label: verdict.info.label,
        seller: o.seller, market: o.market, retrieved: o.retrieved, age_days: verdict.age_days,
        quoted: {
          amount: o.amount, currency: o.currency, tax: o.tax, vat_rate: o.vat_rate,
          delivery_included: o.delivery_included, amount_scope: o.amount_scope,
          pack_contents: verdict.pack.contents || null
        },
        unit: verdict.derived_unit,
        match: verdict.match,
        equivalence: verdict.equivalence,
        adjustment: {
          ok: verdict.adjustment.ok,
          value_before_adjustment: verdict.adjustment.value_before_adjustment,
          value: verdict.adjustment.value,
          steps: verdict.adjustment.steps,
          vat_rate_used: verdict.adjustment.vat_rate_used || null,
          unresolved: verdict.adjustment.unresolved
        },
        saved_comparison_id: o.saved_comparison_id,
        flags: verdict.flags,
        raw: o,
        raw_unchanged: true,
        visible: true
      };

      allFlags = allFlags.concat(verdict.flags.map(function (f) {
        return { observation_id: o.observation_id, code: f.code, statement: f.statement };
      }));

      if (reasons.length) {
        row.reasons = reasons;
        row.reason_codes = reasons.map(function (r) { return r.code; });
        row.reason = reasons.map(function (r) { return r.statement; }).join(' ');
        row.exclusion_kind = reasons.some(function (r) { return r.kind === 'excluded'; })
          ? 'excluded' : 'unresolved';
        row.comparable_value = verdict.comparable_value;
        row.selected = false;
        row.selection = 'not selected: this observation is not in the comparable set';
        ineligible.push(row);
      } else {
        var quotedPiece = verdict.comparable_value.value;
        row.per_pack = {
          basis: 'the quoted amount for the stated pack or piece, adjusted',
          value: row.adjustment.value,
          pack_pieces: verdict.pack.normalised ? verdict.pack.pieces_per_pack : null
        };
        row.per_piece = {
          value: quotedPiece,
          basis: verdict.comparable_value.how,
          statement: verdict.comparable_value.statement
        };
        row.comparable_value = verdict.comparable_value;
        row.bases_shown = ['quoted', 'adjusted', 'per_piece'];
        row.selected = false;
        row.selected_observation_id = null;
        row.selection = 'not selected: no approved selection rule exists, so every comparable '
          + 'offer is shown on its own and the cheapest is not treated as the right one';
        eligible.push(row);
      }
    });

    if (!ctx.basis) {
      /* Not an exclusion of any row: it is the comparison that cannot be built. */
      allFlags.push({ observation_id: null, code: 'NO_BASIS_NAMED',
        statement: 'No like-for-like comparison basis is named, so no two observations have been '
          + 'put beside each other and no index is stated.' });
    }

    /* Conflicting prices between rows stay visible and none is chosen. */
    var conflicts = evidence.observationConflicts(prepared.map(function (o) {
      return { part_number: o.part_number, seller: o.seller, retrieved: o.retrieved,
        price_level: o.level, price: o.amount };
    }), { as_of: ctx.as_of });
    conflicts.conflicts.forEach(function (c) {
      allFlags.push({ observation_id: null, code: 'CONFLICTING_OBSERVATIONS', statement: c.statement });
    });

    /* Summarising needs a rule that somebody approved. There is no default. */
    var rule = opts.approved_aggregation_rule || null;
    var aggregation;
    if (!rule || isBlank(rule.rule_id) || isBlank(rule.approved_by) || isBlank(rule.statement)) {
      aggregation = {
        declared: false,
        approved_by: null,
        summary: null,
        offers_shown_individually: true,
        statement: 'No approved aggregation rule is declared, so no summary figure is stated. '
          + 'Every comparable offer is returned on its own.'
      };
    } else if (name(rule.method) !== 'median') {
      aggregation = {
        declared: false, rule_id: rule.rule_id, approved_by: rule.approved_by,
        summary: null, offers_shown_individually: true,
        statement: 'The declared rule asks for the method "' + name(rule.method) + '", which is not '
          + 'one of the methods this panel can compute (median). Nothing is summarised, because a '
          + 'summary computed another way would not be the rule that was approved.'
      };
    } else {
      var values = eligible.map(function (r) { return r.per_piece.value; })
        .filter(function (v) { return v !== null; });
      aggregation = {
        declared: true, rule_id: rule.rule_id, approved_by: rule.approved_by,
        method: 'median', on_basis: 'price per piece after the recorded adjustments',
        offers_used: values.length,
        summary: median(values),
        offers_shown_individually: true,
        statement: values.length
          ? 'Median of ' + values.length + ' comparable offer(s) on the recorded per-piece basis, '
            + 'under the approved rule "' + rule.rule_id + '". Every offer it was taken from is still '
            + 'returned separately, so the summary can be checked against them.'
          : 'The approved rule is declared but no comparable offer reached the per-piece basis, so '
            + 'no summary figure is stated.'
      };
    }

    /* A comparison already saved stays as it was, even when a newer price exists. */
    var saved = (opts.saved_comparisons || []).map(function (s) {
      var ids = s.observation_ids || [];
      var newer = [];
      ids.forEach(function (id) { if (supersededBy[id]) newer.push(supersededBy[id]); });
      return {
        comparison_id: s.comparison_id || null,
        observation_ids: ids.slice(),
        value: s.value === undefined ? null : s.value,
        basis: s.basis || null,
        saved_at: s.saved_at || null,
        superseded_by_observation_ids: unique(newer),
        rewritten: false,
        statement: newer.length
          ? 'A newer observation now exists on this comparison, and the comparison is not rewritten '
            + 'by it. The saved figure stands as the figure that was saved, and the newer price is '
            + 'shown beside it.'
          : 'No later observation replaces any row of this saved comparison. It stands unchanged.'
      };
    });

    /* Purchasing movement and price positioning are two outputs with two labels,
       so one cannot be read as proof of the other. */
    var own = opts.own_movement || null;
    var purchasing_movement = own
      ? {
        available: true,
        evidence_kind: 'our own recorded movement on this part, from our own billing records',
        label: name(own.label) || 'recorded movement, periods as stated',
        source_reference: name(own.source_reference) || null,
        periods: (own.periods || []).map(function (p) {
          return { label: p.label || null, quantity: toNumberOrNull(p.quantity),
            unit_price: toNumberOrNull(p.unit_price) };
        }),
        statement: 'This is what we bought and sold on this part over the stated periods. It is a '
          + 'separate set of evidence and it is not proof of where our price sits against another '
          + 'seller.',
        is_proof_of_price_positioning: false,
        must_not_be_read_as: ['proof that our price is too high', 'proof that our price is too low',
          'a comparison with another seller']
      }
      : {
        available: false,
        evidence_kind: 'our own recorded movement on this part, from our own billing records',
        periods: [],
        statement: 'No movement of our own volumes and realised prices was supplied for this case. '
          + 'Its absence is not a zero and it is not evidence about another seller.',
        is_proof_of_price_positioning: false,
        must_not_be_read_as: ['proof that our price is too high', 'proof that our price is too low',
          'a comparison with another seller']
      };

    /* Positioning is a statement about where our price sits against somebody
       else's. It therefore needs a named basis AND at least one observation
       that is not our own terms. Our own price on its own positions nothing. */
    var comparables = eligible.filter(function (r) {
      return !levelInfo(r.level).is_our_terms;
    });
    var indexAllowed = !!(ctx.basis && comparables.length);
    var price_positioning = {
      available: indexAllowed,
      evidence_kind: 'dated advertised or reference prices published by other sellers',
      basis: ctx.basis
        ? { level: ctx.basis.level, level_label: levelInfo(ctx.basis.level).label,
            unit: ctx.basis.unit, named_by: ctx.basis.named_by }
        : null,
      eligible_offers: eligible.length,
      comparable_offers_by_other_sellers: comparables.length,
      index_allowed: indexAllowed,
      index_stated: false,
      statement: indexAllowed
        ? 'Comparable offers are shown on the named basis. No index figure is certified as a price '
          + 'action, and a missing like-for-like observation stays explicit rather than being filled '
          + 'in.'
        : 'No price positioning is stated. ' + (ctx.basis
          ? (eligible.length
            ? 'Nothing on the named basis is an observation by another seller, so there is nothing to '
              + 'position our own terms against.'
            : 'No observation reached the comparable basis, so there is nothing to place beside our own '
              + 'terms.')
          : 'No like-for-like basis is named. A missing like-for-like observation stays missing and '
            + 'is not filled in with a real number.'),
      is_proof_that_our_terms_are_too_high: false,
      must_not_be_read_as: ['proof that ISZE net terms are too high',
        'an approved price action', 'a quotation from any seller']
    };

    var scenario_link = indexAllowed
      ? {
        linked: true,
        comparison_id: name(opts.comparison_id) || 'comparison-' + (caseContext.case_id || 'unnamed'),
        basis: { level: ctx.basis.level, unit: ctx.basis.unit },
        eligible_observation_ids: eligible.map(function (r) { return r.observation_id; }),
        excluded_observation_ids: ineligible.map(function (r) { return r.observation_id; }),
        statement: 'The supported comparison on the named basis is offered to the scenario. '
          + 'Observations that were not eligible for it are listed by identifier so the scenario '
          + 'does not carry them.'
      }
      : {
        linked: false,
        comparison_id: null,
        reason_code: ctx.basis ? 'NO_ELIGIBLE_COMPARABLE' : 'NO_BASIS_NAMED',
        statement: 'Nothing is linked into the scenario. ' + (ctx.basis
          ? 'No observation reached the named basis.'
          : 'No like-for-like basis is named, so there is no supported comparison to link.')
      };

    var rawUnchanged = JSON.stringify(list) === snapshotBefore;

    return {
      contract: CONTRACT,
      case: {
        case_id: ctx.case_id, part_number: name(caseContext.part_number) || null,
        market: name(caseContext.market) || null, unit: name(caseContext.unit) || null,
        customer: name(caseContext.customer) || null, as_of: ctx.as_of
      },
      observations_in: list.length,
      raw_records_retained: prepared.length,
      raw_input_unmodified: rawUnchanged,
      selected_basis: ctx.basis
        ? {
          level: ctx.basis.level, level_label: levelInfo(ctx.basis.level).label,
          unit: ctx.basis.unit, named_by: ctx.basis.named_by,
          statement: 'The comparison basis is named as ' + levelInfo(ctx.basis.level).label
            + ' in ' + ctx.basis.unit + '. Naming it is a review decision; this panel does not '
            + 'choose one.'
        }
        : null,
      candidate_bases: candidateBases(prepared),
      eligible_offers: eligible,
      ineligible_offers: ineligible,
      selected_observation_id: null,
      aggregation: aggregation,
      flags: allFlags,
      saved_comparisons: saved,
      purchasing_movement: purchasing_movement,
      price_positioning: price_positioning,
      scenario_link: scenario_link,
      price_action_certified: false,
      statement: list.length
        ? eligible.length + ' of ' + list.length + ' observation(s) are eligible on the '
          + (ctx.basis ? 'named basis' : 'undeclared basis') + ' and '
          + ineligible.length + ' are not, each with a named reason. '
          + 'No price action is certified from this panel.'
        : 'No observation was supplied, so no comparison is stated.',
      all_exclusion_codes_named: ineligible.every(function (r) {
        return (r.reason_codes || []).every(function (c) { return !!EXCLUSION_CODES[c]; });
      })
    };
  }

  /* ------------------------------------------------- MARKET-08: the request -- */

  var REQUEST_TOPICS = {
    name_the_basis: {
      kind: 'a decision',
      smallest: 1,
      ask: 'Name the like-for-like comparison basis: which commercial price level and which unit a '
        + 'comparison may be built on for this part.',
      use: 'It decides whether a competitor observation may be placed beside our own terms at all.',
      audience: 'the commercial owner of the price decision',
      response_offered: 'Once it is named, the observations we already hold are placed on it and the '
        + 'excluded ones are listed with their reasons.'
    },
    accepted_level_bridge: {
      kind: 'a decision',
      smallest: 2,
      ask: 'Confirm whether an accepted bridge exists between the price level we hold and the '
        + 'advertised level, and if so who accepted it.',
      use: 'Without an accepted bridge the two levels are shown side by side and are not put into one '
        + 'figure.',
      audience: 'the commercial owner of the price decision',
      response_offered: 'With an accepted bridge the two levels are compared on the named basis; '
        + 'without one they stay side by side, which is already a usable answer.'
    },
    tax_basis: {
      kind: 'a fact about one observation',
      smallest: 3,
      ask: 'State the tax treatment of the advertised price: whether it includes tax and, if so, at '
        + 'what rate.',
      use: 'A price that includes tax cannot be placed beside a tax-exclusive list figure until the '
        + 'rate is stated.',
      audience: 'the seller, or whoever holds the listing',
      response_offered: 'The observation is then adjusted and shown on the same basis, with the '
        + 'adjustment recorded step by step.'
    },
    dated_rate: {
      kind: 'a fact about one observation',
      smallest: 4,
      ask: 'State the dated exchange rate used for this observation, and the date it was taken on.',
      use: 'An amount in another currency cannot be placed beside a euro figure without a dated rate.',
      audience: 'whoever holds the listing',
      response_offered: 'The observation is then converted and shown beside the euro figure, with the '
        + 'rate and its date recorded.'
    },
    pack_contents: {
      kind: 'a fact about one observation',
      smallest: 5,
      ask: 'State what the quoted price covers: how many pieces are in the pack or kit, and what the '
        + 'pieces are.',
      use: 'A price per kit with unstated contents cannot be turned into a price per piece, and it '
        + 'cannot be compared with a single piece.',
      audience: 'the seller, or whoever holds the listing',
      response_offered: 'The price is then shown both per pack and per piece, with the original quote '
        + 'kept as it was.'
    },
    delivery_basis: {
      kind: 'a fact about one observation',
      smallest: 6,
      ask: 'State whether the quoted price includes delivery to the market in question.',
      use: 'An undelivered price placed beside a delivered one compares two different things.',
      audience: 'the seller, or whoever holds the listing',
      response_offered: 'The delivery treatment is then recorded on the observation and shown.'
    }
  };

  /* A request may never ask for these. A full price file, somebody else's
     customer list or another distributor's terms are not evidence we are
     entitled to, and asking for them would weaken the request rather than
     strengthen it. */
  var FORBIDDEN_ASKS = [
    'resale price', 'price list', 'price file', 'customer list', 'customer database',
    'dealer database', 'another distributor', 'confidential terms', 'supplier cost',
    'cost table', 'purchasing terms', 'whole catalogue', 'all prices'
  ];

  /* Whole-word matching, so "price list" does not fire on "price listing" and
     an honest sentence about what we already hold does not read as a request
     for a customer database. */
  function phraseHits(text, phrases) {
    var t = ' ' + name(text).toLowerCase().replace(/[^a-z0-9]+/g, ' ') + ' ';
    return phrases.filter(function (p) {
      var needle = ' ' + p.replace(/[^a-z0-9]+/g, ' ').trim() + ' ';
      return t.indexOf(needle) >= 0;
    });
  }

  /* `does_not_ask_for` is a statement of what is NOT asked for, so it is not
     scanned. Only the words that would go into a request are. */
  function requestIsClean(request) {
    request = request || {};
    var text = [request.smallest_missing_detail, request.use, request.response_offered, request.audience]
      .join(' ');
    var hits = phraseHits(text, FORBIDDEN_ASKS);
    return { clean: hits.length === 0, hits: hits };
  }

  /* What is actually missing for a decision, smallest first. Only the missing
     item is asked for; nothing else is added to the list to make it look
     thorough. */
  function missingEvidence(panelResult) {
    panelResult = panelResult || {};
    var gaps = {};
    (panelResult.ineligible_offers || []).forEach(function (r) {
      (r.reason_codes || []).forEach(function (c) { gaps[c] = (gaps[c] || 0) + 1; });
    });

    /* Several codes can point at one thing to ask for, so the list is merged by
       topic: two rows asking for the same thing is not one ask, it is the same
       ask written twice. */
    var raw = [];
    function want(topic, code, observations) {
      raw.push({ topic: topic, code: code, observations: observations });
    }
    if (!panelResult.selected_basis) want('name_the_basis', 'NO_BASIS_NAMED', 0);
    if (gaps.NO_ACCEPTED_LEVEL_BRIDGE) {
      want('accepted_level_bridge', 'NO_ACCEPTED_LEVEL_BRIDGE', gaps.NO_ACCEPTED_LEVEL_BRIDGE);
    }
    if (gaps.TAX_BASIS_NOT_STATED) want('tax_basis', 'TAX_BASIS_NOT_STATED', gaps.TAX_BASIS_NOT_STATED);
    if (gaps.TAX_RATE_NOT_STATED) want('tax_basis', 'TAX_RATE_NOT_STATED', gaps.TAX_RATE_NOT_STATED);
    if (gaps.NO_DATED_RATE_TO_EUR) want('dated_rate', 'NO_DATED_RATE_TO_EUR', gaps.NO_DATED_RATE_TO_EUR);
    if (gaps.FX_DATE_NOT_STATED) want('dated_rate', 'FX_DATE_NOT_STATED', gaps.FX_DATE_NOT_STATED);
    if (gaps.PACK_CONTENTS_UNKNOWN) {
      want('pack_contents', 'PACK_CONTENTS_UNKNOWN', gaps.PACK_CONTENTS_UNKNOWN);
    }
    if (gaps.DELIVERY_BASIS_NOT_STATED) {
      want('delivery_basis', 'DELIVERY_BASIS_NOT_STATED', gaps.DELIVERY_BASIS_NOT_STATED);
    }
    if (gaps.DELIVERY_COST_NOT_SUPPLIED) {
      want('delivery_basis', 'DELIVERY_COST_NOT_SUPPLIED', gaps.DELIVERY_COST_NOT_SUPPLIED);
    }

    var byTopic = {};
    raw.forEach(function (row) {
      if (!byTopic[row.topic]) {
        byTopic[row.topic] = { topic: row.topic, observations: 0, reasons: [] };
      }
      byTopic[row.topic].observations += row.observations;
      byTopic[row.topic].reasons.push(row.code);
    });
    var order = Object.keys(byTopic).map(function (t) { return byTopic[t]; })
      .sort(function (a, b) {
        return REQUEST_TOPICS[a.topic].smallest - REQUEST_TOPICS[b.topic].smallest;
      });

    return {
      gaps: Object.keys(gaps).map(function (c) {
        return { code: c, observations: gaps[c], known: !!EXCLUSION_CODES[c] };
      }),
      ordered: order,
      smallest: order.length ? order[0] : null,
      statement: order.length
        ? 'The comparison cannot be built yet. The smallest thing missing is: '
          + REQUEST_TOPICS[order[0].topic].ask
        : 'Nothing that this panel can ask for is missing: every observation is either in the '
          + 'comparable set or was left out for a reason this panel cannot resolve.'
    };
  }

  function missingEvidenceRequest(panelResult, caseContext, opts) {    caseContext = caseContext || {}; opts = opts || {};
    var missing = missingEvidence(panelResult);
    if (!missing.smallest) {
      return { ok: false, refused: true, error: missing.statement,
        reason_code: 'NOTHING_TO_ASK_FOR' };
    }
    var wanted = name(opts.topic);
    var topic = REQUEST_TOPICS[wanted] ? wanted : missing.smallest.topic;
    var declared = REQUEST_TOPICS[topic];

    if (name(opts.topic) && !REQUEST_TOPICS[name(opts.topic)]) {
      return { ok: false, refused: true,
        error: 'The topic "' + name(opts.topic) + '" is not a declared request topic, so nothing is '
          + 'composed. An undeclared ask is how a request for everything gets sent instead of a '
          + 'request for one thing.',
        reason_code: 'UNDECLARED_TOPIC', declared_topics: Object.keys(REQUEST_TOPICS) };
    }

    var held = (opts.context_held || []).map(function (h) { return name(h); }).filter(function (h) { return h; });

    var request = {
      ok: true,
      draft_only: true,
      sent: false,
      requested_case_state: 'evidence_requested',
      case_state_note: 'The case record owns its own state. This is the state being proposed, not a '
        + 'state change made here.',
      case_id: name(caseContext.case_id) || null,
      part_number: name(caseContext.part_number) || null,
      market: name(caseContext.market) || null,
      topic: topic,
      kind_of_thing_missing: declared.kind,
      smallest_missing_detail: declared.ask,
      use: declared.use,
      audience: declared.audience,
      response_offered: declared.response_offered,
      observations_affected: missing.smallest.observations,
      already_held: held,
      already_held_note: held.length
        ? 'These items are already held and are not asked for again.'
        : 'Nothing is listed as already held, so the request stands on its own.',
      asks_only_for_one_thing: true,
      does_not_ask_for: [
        'a full resale price file or price list',
        'a customer or dealer database',
        'another distributor\u2019s confidential terms',
        'a restricted purchasing cost table'
      ],
      other_gaps_not_asked_for: missing.ordered.slice(1).map(function (o) {
        return { topic: o.topic, observations: o.observations,
          note: 'Recorded, not asked for in this request.' };
      }),
      statement: 'One thing is asked for: ' + declared.ask + ' It goes to ' + declared.audience
        + '. The other gaps found are recorded and not asked for, and the request is a draft that '
        + 'nothing sends.'
    };

    var clean = requestIsClean(request);
    if (!clean.clean) {
      return { ok: false, refused: true,
        error: 'The composed request mentions something it may not ask for: ' + clean.hits.join(', ')
          + '. A request for a full price file or for somebody else\u2019s customer data is refused '
          + 'rather than softened.',
        reason_code: 'FORBIDDEN_ASK', hits: clean.hits };
    }
    return request;
  }

  /* Declining the optional competitor data removes the competitor price
     conclusion and nothing else. The purchasing review and the unrelated
     support do not depend on it. */
  function declineRequest(request, panelResult, opts) {
    request = request || {}; panelResult = panelResult || {}; opts = opts || {};
    var still = (opts.still_available || panelResult.purchasing_movement && panelResult.purchasing_movement.available
      ? ['the recorded movement of our own volumes and realised prices on this part']
      : ['the recorded movement of our own volumes and realised prices on this part']);
    (opts.unrelated_support || []).forEach(function (s) { still.push(name(s)); });

    return {
      declined: true,
      removed_only: ['the competitor price conclusion that this request was for'],
      unsupported_removed: 'price_positioning',
      price_positioning: {
        available: false,
        statement: 'With the requested evidence declined, no price positioning is stated. The gap '
          + 'stays a gap: it is not filled with a zero and it is not read as an approval of the '
          + 'current terms.'
      },
        still_available: unique(still),
      scenario_link: { linked: false,
        statement: 'Nothing from the competitor comparison is linked into the scenario.' },
      verdict_unchanged: true,
      statement: 'Declining the competitor evidence takes away the competitor price conclusion only. '
        + 'The purchasing review on this part and the support work that does not depend on it are '
        + 'still available, and nothing that is missing has been turned into a zero or an approval.'
    };
  }

  /* -------------------------------------------------- adapters for real rows -- */

  /* The payload carries prose in the fields that decide a comparison: kit
     contents are written as "not stated in the listing", and a documented rate
     is written as a sentence. Nothing here reads a rate or a pack out of a
     sentence, because that would be inventing a figure. The level, the unit, the
     scope of the quoted amount and the match basis are declarations a person
     makes; everything else is copied. */
  function observationFromOffer(offer, declarations) {
    offer = offer || {}; declarations = declarations || {};
    var taxText = name(offer.vat_included_excluded || offer.tax).toLowerCase();
    var tax = null;
    if (taxText.indexOf('included') >= 0 || taxText.indexOf('incl') >= 0) tax = 'included';
    else if (taxText.indexOf('exclusive') >= 0 || taxText.indexOf('excluded') >= 0
      || taxText.indexOf('excl') >= 0) tax = 'excluded';

    var rates = declarations.fx_rates || {};
    var cur = name(offer.currency_original || offer.currency).toUpperCase();
    var rate = rates[cur] || null;

    return observationFrom({
      observation_id: offer.observation_id || offer.id || null,
      role: declarations.role || (declarations.level && levelInfo(declarations.level).is_our_terms
        ? 'isze_terms' : 'competitor'),
      level: declarations.level || null,
      seller: offer.seller || null,
      market: offer.market || offer.delivery_market || offer.seller_country || null,
      retrieved: offer.observation_date || offer.retrieved || null,
      source_reference: offer.evidence_reference || offer.source_url || offer.url || null,
      part_number: offer.claimed_isuzu_cross_reference || offer.part
        || offer.manufacturer_part_number || null,
      case_id: declarations.case_id || offer.case_id || null,
      amount: offer.price_original === undefined || offer.price_original === ''
        ? offer.price : offer.price_original,
      amount_scope: declarations.amount_scope || null,
      currency: cur,
      unit: declarations.unit || null,
      pack: declarations.pack || null,
      tax: tax,
      /* A count of 1 or 0 means exactly that. Anything else is passed as the
         source states it, together with the unit the source used, so the rule
         sees the same number the reader sees. */
      vat_rate: offer.vat_rate === undefined ? offer.vat : offer.vat_rate,
      vat_rate_unit: declarations.vat_rate_unit || null,
      delivery_included: declarations.delivery_included === undefined
        ? null : declarations.delivery_included,
      delivery_cost_eur: declarations.delivery_cost_eur === undefined
        ? null : declarations.delivery_cost_eur,
      fx_to_eur: rate ? toNumberOrNull(rate.rate) : null,
      fx_date: rate ? rate.date : null,
      match: {
        status: offer.match_status || 'unresolved',
        basis: declarations.match_basis || null,
        reason: offer.match_reason || offer.use || null
      },
      equivalence: declarations.equivalence || null,
      supersedes: offer.supersedes || null,
      saved_comparison_id: offer.saved_comparison_id || null
    });
  }

  /* Our own recorded movement, taken from the comparison block the case already
     carries. Nothing is recomputed; the labels and the figures are passed
     through. */
  function movementFromComparison(comparison, label) {
    if (!comparison || !comparison.prior || !comparison.current) return null;
    return {
      label: label || comparison.label || 'recorded periods',
      source_reference: 'the comparison the case already carries',
      periods: [
        { label: String(comparison.prior.year || 'earlier'), quantity: toNumberOrNull(comparison.prior.quantity),
          unit_price: toNumberOrNull(comparison.prior.price) },
        { label: String(comparison.current.year || 'later'), quantity: toNumberOrNull(comparison.current.quantity),
          unit_price: toNumberOrNull(comparison.current.price) }
      ]
    };
  }

  var API = {
    panel: panel,
    missingEvidence: missingEvidence,
    missingEvidenceRequest: missingEvidenceRequest,
    declineRequest: declineRequest,
    observationFrom: observationFrom,
    observationFromOffer: observationFromOffer,
    movementFromComparison: movementFromComparison,
    candidateBases: candidateBases,
    levelInfo: levelInfo,
    assertLevelUse: assertLevelUse,
    bridgeCheck: bridgeCheck,
    explainExclusion: explainExclusion,
    codeForUnresolved: codeForUnresolved,
    requestIsClean: requestIsClean,
    EXCLUSION_CODES: EXCLUSION_CODES,
    UNRESOLVED_CODE_MAP: UNRESOLVED_CODE_MAP,
    REQUEST_TOPICS: REQUEST_TOPICS,
    FORBIDDEN_ASKS: FORBIDDEN_ASKS,
    PANEL_LEVELS: PANEL_LEVELS,
    REQUESTED_SHARED_LEVELS: REQUESTED_SHARED_LEVELS,
    CONTRACT: CONTRACT,
    USES: USES
  };

  root.AIMComparable = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
