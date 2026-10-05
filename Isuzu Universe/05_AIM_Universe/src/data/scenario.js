/* ===========================================================================
   One scenario, everywhere (F01, F09, UX-01, UX-02, UX-03, UX-08).

   In v03 the "Two objectives" page used the new functions while "Price & profit
   test", "Internal action" and the export still read an older state object. A
   ranked option could therefore be shown on one screen and a different scenario
   saved on another, and nothing detected it.

   Here there is exactly one scenario per case. Selecting a ranked alternative
   fills it in, editing a field updates the same record, and every view, the
   save and every export read that one record.
   =========================================================================== */
(function (root) {
  'use strict';

  var contracts = (typeof module === 'object' && module.exports)
    ? require('./contracts.js') : root.AIMContracts;

  function makeScenarioStore(payload, engine) {
    var byCase = {};        /* case_id -> scenario */
    var selections = {};    /* case_id -> the inputs a selected alternative wrote */
    var listeners = [];

    /* UX-02. The inputs an alternative writes, compared after later edits. */
    var SELECTION_TRACKED = ['price_before', 'price_after', 'quantity_before', 'quantity_after',
      'quantity_label', 'scope', 'support_eur', 'cost_eur', 'cost_basis_id', 'pack_size'];

    function notify(caseId) {
      listeners.forEach(function (fn) { fn(caseId, byCase[caseId]); });
    }

    function caseById(caseId) {
      return (payload.cases || []).filter(function (c) { return c.id === caseId; })[0]
        || (payload.cases || [])[0];
    }

    /* The default scenario for a case. Everything the calculation needs is named
       here, including the two dates that v03 left implicit. */
    function defaults(caseId) {
      var c = caseById(caseId);
      var bd = c.baselineDefined || {};
      var basisId = defaultBasisId();
      return {
        scenario_id: caseId + ':v1',
        version: 1,
        case_id: c.id,
        part_number: c.pn,
        unit: c.unit || 'unit',

        price_before: engine.round2(Number(bd.observed_unit_price) || 0),
        price_after: engine.round2(Number(bd.observed_unit_price) || 0),
        quantity_before: Number(bd.quantity) || 0,
        quantity_after: null,          /* null means "same as the base quantity" */
        quantity_label: bd.quantity_label || 'observed history',

        scope: 'all',
        volume_is_observed: true,
        pack_size: 1,

        cost_eur: null,
        cost_basis_id: basisId,
        cost_basis_source: 'verified record',
        support_eur: 0,

        /* Two separate clocks (F04, FIN-02). Never conflated again. */
        evidence_period: bd.period || null,
        offer_effective_date: null,

        sources: (payload.sources || []).slice(0, 3).map(function (s) {
          return { reference_id: s.id, kind: s.kind || null, title: s.title,
            period: s.date || null, source_file: s.file || null,
            source_pointer: null, status: 'declared', basis: s.basis || null,
            restricted: false };
        }),

        selected_alternative_id: null,
        objective: 'revenue'
      };
    }

    function defaultBasisId() {
      return (payload.meta && payload.meta.defaultForwardBasis) || null;
    }

    function get(caseId) {
      if (!byCase[caseId]) byCase[caseId] = defaults(caseId);
      return byCase[caseId];
    }

    function set(caseId, patch, meta) {
      var current = get(caseId);
      var next = {};
      Object.keys(current).forEach(function (k) { next[k] = current[k]; });
      Object.keys(patch || {}).forEach(function (k) {
        if (contracts.SCENARIO_FIELDS.indexOf(k) < 0) {
          throw new Error('Refusing to set undeclared scenario field "' + k
            + '". Add it to the Scenario contract first.');
        }
        next[k] = patch[k];
      });
      var changes = contracts.diff(current, next);
      if (changes.length) {
        next.version = current.version + 1;
        next.scenario_id = caseId + ':v' + next.version;
      }
      byCase[caseId] = next;
      notify(caseId);
      return { scenario: next, changes: changes };
    }

    /* Selecting a ranked alternative populates the same record, so the option
       that was ranked is the option that gets saved. */
    function selectAlternative(caseId, alternativeId) {
      var c = caseById(caseId);
      var alt = (c.alternatives || []).filter(function (a) {
        return a.alternative_id === alternativeId;
      })[0];
      if (!alt) return { ok: false, error: 'No such alternative "' + alternativeId + '".' };

      var current = get(caseId);
      var basisId = alt.cost_basis_for_offer || current.cost_basis_id || defaultBasisId();
      var rec = engine.costRecord(payload, c.pn, basisId);
      var price = engine.priceAfter(current.price_before, alt.price_delta_pct);
      var qty = engine.quantityAfter(current.quantity_before, alt, {});

      var result = set(caseId, {
        price_after: price,
        quantity_after: (qty === current.quantity_before && !alt.volume_assumption) ? null : qty,
        quantity_label: alt.volume_label || current.quantity_label,
        scope: alt.scope || 'all',
        support_eur: alt.support_eur || 0,
        cost_eur: rec ? rec.cost_eur : null,
        cost_basis_id: basisId,
        cost_basis_source: rec ? 'verified record' : 'no verified cost held',
        selected_alternative_id: alternativeId
      });

      var inputs = {};
      SELECTION_TRACKED.forEach(function (k) { inputs[k] = result.scenario[k]; });
      selections[caseId] = { alternative_id: alternativeId, label: alt.name || alternativeId,
        inputs: inputs };

      /* A migration is carried as selected, and stays financially unresolved. */
      return {
        ok: true, scenario: result.scenario, changes: result.changes,
        alternative: alt,
        migration_unresolved: alt.kind === 'migration'
      };
    }

    function calculate(caseId) {
      var s = get(caseId);
      var c = caseById(caseId);
      var rec = s.cost_basis_id ? engine.costRecord(payload, c.pn, s.cost_basis_id) : null;
      var alt = (c.alternatives || []).filter(function (a) {
        return a.alternative_id === s.selected_alternative_id;
      })[0];
      return engine.calculate({
        price_before: s.price_before,
        price_after: s.price_after,
        quantity_before: s.quantity_before,
        quantity_after: s.quantity_after,
        scope: s.scope,
        support_eur: s.support_eur,
        cost_eur: s.cost_eur,
        cost_basis_id: s.cost_basis_id,
        quantity_label: s.quantity_label,
        pack_size: s.pack_size,
        kind: alt ? alt.kind : null,
        evidence_period: s.evidence_period,
        offer_effective_date: s.offer_effective_date
      });
    }

    /* Proves the invariant that v03 could not: the scenario that was ranked is
       the scenario that is saved, exported and reopened - including after the
       manual inputs have been changed. */
    function consistency(caseId) {
      var s = get(caseId);
      var c = caseById(caseId);
      var result = calculate(caseId);
      var alt = (c.alternatives || []).filter(function (a) {
        return a.alternative_id === s.selected_alternative_id;
      })[0];
      if (!alt) return { ok: true, selected: null, statement: 'No ranked option is selected.' };
      /* Replay the working scenario through the ranking path, with the current
         inputs, and require the two to agree. */
      var twin = engine.bothObjectives(c, alt, {
        payload: payload,
        price_before: s.price_before,
        price_after: s.price_after,
        quantity_before: s.quantity_before,
        quantity_after: s.quantity_after === null ? undefined : s.quantity_after,
        scope: s.scope,
        support_eur: s.support_eur,
        cost_eur: s.cost_eur,
        quantity_label: s.quantity_label,
        pack_size: s.pack_size,
        offer_effective_date: s.offer_effective_date
      });
      var close = function (a, b) {
        if (a === null && b === null) return true;
        if (a === null || b === null) return false;
        return Math.abs(a - b) < 1e-9;
      };
      var matches = twin.result.ok === result.ok
        && close(twin.result.revenue_change, result.revenue_change)
        && close(twin.result.gp_change, result.gp_change)
        && close(twin.result.quantity_after, result.quantity_after);
      return {
        ok: matches,
        selected: s.selected_alternative_id,
        statement: matches
          ? 'The selected option, the manual inputs and the saved record use one scenario.'
          : 'The ranked option and the working record disagree. This must not be saved.',
        ranked: { revenue_change: twin.result.revenue_change, gp_change: twin.result.gp_change },
        working: { revenue_change: result.revenue_change, gp_change: result.gp_change }
      };
    }

    /* UX-02. Which alternative the working record started from, and which of its
       inputs have been edited by hand since. After a reopen the selection
       snapshot is not held, so the edits are reported as not known rather than
       as none. */
    function alternativeEdits(caseId) {
      var s = get(caseId);
      if (!s.selected_alternative_id) {
        return { selected: null, label: null, edited_fields: [], known: true,
          statement: 'No ranked alternative is selected.' };
      }
      var c = caseById(caseId);
      var alt = (c.alternatives || []).filter(function (a) {
        return a.alternative_id === s.selected_alternative_id;
      })[0];
      var label = alt ? (alt.name || alt.alternative_id) : s.selected_alternative_id;
      var sel = selections[caseId];
      if (!sel || sel.alternative_id !== s.selected_alternative_id) {
        return { selected: s.selected_alternative_id, label: label, edited_fields: null, known: false,
          statement: 'Whether a value was edited after selection is not known for this record.' };
      }
      var edited = SELECTION_TRACKED.filter(function (k) {
        return JSON.stringify(sel.inputs[k]) !== JSON.stringify(s[k]);
      });
      return { selected: s.selected_alternative_id, label: label, edited_fields: edited, known: true,
        statement: edited.length ? 'Edited by hand since selection: ' + edited.join(', ') + '.'
          : 'No value has been edited since selection.' };
    }

    /* UX-04. A small sensitivity grid, computed by the SAME engine entry point
       as every other result (engine.calculate). Each plotted point is one call,
       and each call states its own inputs, so a point can be matched to the
       calculation that produced it rather than being read off a chart.

       Two directions are shown, and neither invents a forecast:
         - price sensitivity: the proposed price is moved in stated steps
           around the working record, with the volume basis unchanged;
         - volume sensitivity: the proposed quantity is moved in stated steps,
           with the price unchanged.
       Where no verified parts cost is applied, the engine returns no gross
       profit for a point. That is preserved as null - the profit series is
       suppressed for the point and the revenue series remains usable - rather
       than being drawn as zero. */
    function sensitivity(caseId, opts) {
      opts = opts || {};
      var s = get(caseId);
      var c = caseById(caseId);
      var alt = (c.alternatives || []).filter(function (a) {
        return a.alternative_id === s.selected_alternative_id;
      })[0];
      var kind = alt ? alt.kind : null;
      var base = {
        quantity_before: s.quantity_before,
        scope: s.scope,
        support_eur: s.support_eur,
        cost_eur: s.cost_eur,
        cost_basis_id: s.cost_basis_id,
        quantity_label: s.quantity_label,
        pack_size: s.pack_size,
        evidence_period: s.evidence_period,
        offer_effective_date: s.offer_effective_date,
        kind: kind
      };

      function point(label, overrides) {
        var input = {};
        Object.keys(base).forEach(function (k) { input[k] = base[k]; });
        Object.keys(overrides || {}).forEach(function (k) { input[k] = overrides[k]; });
        var r = engine.calculate(input);
        return {
          label: label,
          price_after: input.price_after === undefined ? null : input.price_after,
          quantity_after: input.quantity_after === undefined ? null : input.quantity_after,
          input: input,
          ok: r.ok,
          revenue_change: r.ok ? r.revenue_change : null,
          revenue_after: r.ok ? r.revenue_after : null,
          gp_change: (r.ok && r.gp_change !== null) ? r.gp_change : null,
          profit_state: r.ok ? (r.gp_change === null ? 'suppressed' : 'calculated') : 'not_calculated',
          profit_reason: (r.ok && r.gp_change === null)
            ? 'No parts purchase cost is applied to this scenario, so profit-based output is '
              + 'suppressed for this point. A missing cost is not a cost of zero.'
            : (r.ok ? null : r.error),
          error: r.ok ? null : r.error
        };
      }

      /* Price steps as percentages of the current proposed price: -10%..+10%. */
      var priceSteps = opts.price_steps ||
        [-10, -5, -2.5, 0, 2.5, 5, 10];
      var pricePoints = priceSteps.map(function (pctStep) {
        var price = engine.round2(s.price_after * (1 + pctStep / 100));
        return point(signedPct(pctStep) + ' price', {
          price_before: s.price_before, price_after: price,
          quantity_after: s.quantity_after
        });
      });

      /* Volume steps as percentages of the stated total quantity. When no new
         quantity is stated the base quantity is used, so the steps move around
         the quantity the record actually holds. */
      var qtyBase = (s.quantity_after === null || s.quantity_after === undefined)
        ? s.quantity_before : s.quantity_after;
      var volumeSteps = opts.volume_steps ||
        (s.scope === 'all' ? [-10, -5, 0, 5, 10] : [0, 10, 25, 50, 100]);
      var volumePoints = volumeSteps.map(function (pctStep) {
        var qty = s.scope === 'incremental'
          ? engine.round2(s.quantity_before * (1 + pctStep / 100))
          : engine.round2(qtyBase * (1 + pctStep / 100));
        return point(signedPct(pctStep) + ' volume', {
          price_before: s.price_before, price_after: s.price_after,
          quantity_after: ((s.scope === 'incremental' && pctStep === 0) ? null : qty)
        });
      });

      var baselinePoint = point('unchanged offer', {
        price_before: s.price_before, price_after: s.price_before,
        quantity_after: s.quantity_before
      });

      var profitSuppressed = pricePoints.concat(volumePoints).some(function (p) {
        return p.profit_state === 'suppressed';
      });
      var missingCost = s.cost_eur === null || s.cost_eur === undefined;

      return {
        case_id: caseId,
        engine_entry_point: 'engine.calculate',
        price_points: pricePoints,
        volume_points: volumePoints,
        baseline: baselinePoint,
        profit_suppressed: profitSuppressed,
        missing_cost: missingCost,
        no_forecast: 'Each point is the arithmetic of the inputs it states. No elasticity, no '
          + 'confidence band and no best-price prediction is computed or implied.',
        statement: profitSuppressed
          ? 'No parts purchase cost is applied, so the profit series is suppressed on every point '
            + 'and the revenue series remains usable. The reason is stated on each suppressed point.'
          : 'Every point states its own inputs and was produced by the one calculation engine.'
      };
    }

    function onChange(fn) { listeners.push(fn); }

    return {
      defaults: defaults, get: get, set: set, calculate: calculate,
      selectAlternative: selectAlternative, consistency: consistency, alternativeEdits: alternativeEdits,
      sensitivity: sensitivity,
      onChange: onChange, caseById: caseById,
      _all: function () { return byCase; }
    };
  }

  /* A short, signed percentage label for a step. */
  function signedPct(v) {
    var n = Math.round(v * 100) / 100;
    return (n > 0 ? '+' : '') + String(n) + '%';
  }

  /* UX-01. One working context per view: distributor, purchasing account or
     national scope, original part, family, source version and selected period.
     It is built from the open case and the address only, never from the case
     that was open before, so a national review cannot inherit a dealer selector
     or a fleet denominator from another market. */
  var CONTEXT_FIELDS = ['case_id', 'distributor', 'purchasing_account', 'country', 'scope',
    'original_part', 'family', 'source_version', 'compare', 'period',
    'dealer_selector', 'selected_dealer', 'fleet_denominator'];

  function contextFor(payload, c, opts) {
    payload = payload || {};
    c = c || {};
    opts = opts || {};
    var cmp = (c.comparisons || {})[opts.compare] || null;
    var dealerScope = c.scope === 'dealer';
    var dealers = dealerScope && Array.isArray(c.dealers) ? c.dealers.slice() : null;
    var hasFleet = c.fleet !== null && c.fleet !== undefined && Number.isFinite(Number(c.fleet));
    return {
      case_id: c.id || null,
      distributor: c.market || null,
      purchasing_account: c.customer || null,
      country: c.country || null,
      scope: dealerScope ? 'dealer' : 'national',
      original_part: c.pn || null,
      family: c.category || null,
      source_version: (payload.meta && payload.meta.version) || null,
      compare: cmp ? opts.compare : null,
      period: cmp ? (cmp.label || null) : null,
      dealer_selector: dealers,
      selected_dealer: dealers && dealers.indexOf(opts.dealer) >= 0 ? opts.dealer : null,
      fleet_denominator: hasFleet ? { value: Number(c.fleet), market: c.market || null } : null
    };
  }

  /* One string per context, so two views can be compared for exact equality. */
  function contextKey(ctx) {
    ctx = ctx || {};
    return CONTEXT_FIELDS.map(function (k) {
      var v = ctx[k];
      if (v === null || v === undefined) return '';
      return typeof v === 'object' ? JSON.stringify(v) : String(v);
    }).join('|');
  }

  var API = { makeScenarioStore: makeScenarioStore, contextFor: contextFor,
    contextKey: contextKey, CONTEXT_FIELDS: CONTEXT_FIELDS };
  root.AIMScenario = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
