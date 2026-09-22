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
    var listeners = [];

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

    function onChange(fn) { listeners.push(fn); }

    return {
      defaults: defaults, get: get, set: set, calculate: calculate,
      selectAlternative: selectAlternative, consistency: consistency,
      onChange: onChange, caseById: caseById,
      _all: function () { return byCase; }
    };
  }

  var API = { makeScenarioStore: makeScenarioStore };
  root.AIMScenario = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
