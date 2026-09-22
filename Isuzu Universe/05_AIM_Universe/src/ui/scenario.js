/* ===========================================================================
   One scenario record for every view (F01, UX-01, UX-02, UX-03).

   What v03 did, and why this file exists: the Two objectives view read the new
   engine state (v03rank / v03run), while Price & profit test, Internal action
   and the case export read an older E.scenario / getScenario object. Selecting a
   ranked alternative on one screen therefore did not populate the scenario that
   was saved and exported on another. Two records, one case, no check.

   There is now exactly one record per case. It lives in
   src/data/scenario.js (the store all builders share). This module is the only
   thing the view layer talks to, and it adds the two pieces the store cannot know
   about by itself:

     - a journal of every change, so "what did I actually change?" is answerable
     - a change listener, so every open view repaints from the same record

   No arithmetic lives here. Every figure comes from the engine module.
   =========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('../data/scenario.js'), require('../data/contracts.js'));
  } else {
    root.AIMUI = root.AIMUI || {};
    /* Unwrapped: the browser shell wants the factory itself, while the module
       export is the object that carries it. */
    root.AIMUI.makeScenarioContext = factory(root.AIMScenario, root.AIMContracts).makeScenarioContext;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (scenarioModule, contracts) {
  'use strict';

  /* A listed alternative is described the way it will be written into the
     record. Kept in one place so a name shown in the ranking is the name saved
     in the case. */
  function alternativeSummary(alternative, result) {
    if (!alternative) return null;
    return {
      alternative_id: alternative.alternative_id,
      name: alternative.name,
      kind: alternative.kind,
      scope: alternative.scope,
      price_delta_pct: alternative.price_delta_pct,
      volume_assumption: alternative.volume_assumption,
      volume_label: alternative.volume_label,
      cost_basis_for_offer: alternative.cost_basis_for_offer || null,
      revenue_change: result && result.ok ? result.revenue_change : null,
      gp_change: result && result.ok ? result.gp_change : null
    };
  }

  function makeScenarioContext(payload, engine, options) {
    options = options || {};
    var store = options.store || scenarioModule.makeScenarioStore(payload, engine);
    var journal = {};        /* case_id -> [entry] */
    var listeners = [];

    function notify(caseId, kind) {
      listeners.forEach(function (fn) { fn(caseId, kind, get(caseId)); });
    }

    function record(caseId, kind, entry) {
      if (!journal[caseId]) journal[caseId] = [];
      journal[caseId].push(Object.assign({ kind: kind, at: entry && entry.at || null }, entry));
      notify(caseId, kind);
    }

    function get(caseId) {
      return store.get(caseId);
    }

    /* A manual edit updates the same record the ranking writes to. Anything not
       declared on the scenario contract is refused by the store, not silently
       kept in a view-local copy. */
    function edit(caseId, patch, meta) {
      var result = store.set(caseId, patch, meta);
      if (result.changes && result.changes.length) {
        record(caseId, 'edit', {
          at: (meta && meta.at) || null,
          fields: result.changes.map(function (c) { return c.field; }),
          version: result.scenario.version
        });
      }
      return result;
    }

    /* Selecting a ranked alternative keeps the objective and the record the same
       object, so the option ranked on the objectives view is the option the
       economics view tests and the export carries. */
    function select(caseId, alternativeId, meta) {
      var result = store.selectAlternative(caseId, alternativeId);
      if (!result.ok) return result;
      record(caseId, 'select', {
        at: (meta && meta.at) || null,
        alternative_id: alternativeId,
        version: result.scenario.version,
        migration_unresolved: !!result.migration_unresolved
      });
      return result;
    }

    function setObjective(caseId, objective) {
      if (objective !== 'revenue' && objective !== 'grossProfit') {
        throw new Error('Unknown objective "' + objective + '". Use revenue or grossProfit.');
      }
      /* The objective changes ordering only. It is written on the record so a
         saved case says which ranking it was read under, and on nothing else. */
      return edit(caseId, { objective: objective }, { at: null });
    }

    function calculate(caseId) {
      return store.calculate(caseId);
    }

    function consistency(caseId) {
      return store.consistency(caseId);
    }

    /* Ranked alternatives under one objective. Every row carries both measures,
       so the same scenario can be read under revenue and under gross profit
       without re-running the assumptions. */
    function ranked(caseObject, objective, opts) {
      var rk = engine.rankAlternatives(caseObject, objective, Object.assign({ payload: payload }, opts || {}));
      return {
        objective: objective,
        objective_label: rk.objective_label,
        baseline: rk.baseline,
        baseline_consistency: rk.baseline_consistency,
        offer_effective_date: rk.offer_effective_date,
        rows: rk.ranked.map(function (x) {
          return {
            rank: null,
            alternative: x.alternative,
            alternative_summary: alternativeSummary(x.alternative, x.result),
            result: x.result,
            cost_record: x.cost_record,
            price_after: x.price_after
          };
        })
      };
    }

    /* Both objectives for every alternative, on the same assumptions, so the
       ordering claim can be checked instead of asserted. */
    function bothObjectives(caseObject, opts) {
      var rev = ranked(caseObject, 'revenue', opts);
      var gp = ranked(caseObject, 'grossProfit', opts);
      var revOrder = rev.rows.map(function (r) { return r.alternative.alternative_id; });
      var gpOrder = gp.rows.map(function (r) { return r.alternative.alternative_id; });
      /* Compared by part-of-speech, not by position: the whole point is that the
         position may differ. What must not differ is any recorded value. */
      var canon = function (map) {
        return JSON.stringify(Object.keys(map).sort().map(function (k) { return [k, map[k]]; }));
      };
      /* The quantity for each alternative, keyed by the alternative, so the order
         the two rankings happen to be in cannot make identical assumptions look
         different. */
      var revQty = {}, gpQty = {};
      rev.rows.forEach(function (r) {
        revQty[r.alternative.alternative_id] = r.result.ok ? r.result.quantity_after : null;
      });
      gp.rows.forEach(function (r) {
        gpQty[r.alternative.alternative_id] = r.result.ok ? r.result.quantity_after : null;
      });
      var assumes = {
        same_baseline: JSON.stringify(rev.baseline) === JSON.stringify(gp.baseline),
        same_quantities: canon(revQty) === canon(gpQty),
        same_offer_effective_date: rev.offer_effective_date === gp.offer_effective_date
      };
      assumes.ordering_only = assumes.same_baseline && assumes.same_quantities
        && assumes.same_offer_effective_date;
      assumes.statement = assumes.ordering_only
        ? 'Changing the objective changed the order of the rows and nothing else: the baseline, the '
          + 'offer effective date and every alternative quantity are identical under both objectives.'
        : 'The two objectives did not run on identical assumptions. This must not be presented as a '
          + 'ranking of the same scenario.';
      return {
        revenue: rev, grossProfit: gp,
        orders_differ: JSON.stringify(revOrder) !== JSON.stringify(gpOrder),
        assumptions: assumes
      };
    }

    /* What the export writes. Both objectives present, the record present, the
       ranked source named. Built from the code paths the views use. */
    function exportPackage(caseId, extra) {
      extra = extra || {};
      var s = get(caseId);
      var c = store.caseById(caseId);
      var result = calculate(caseId);
      var cons = consistency(caseId);
      var twin = bothObjectives(c);
      return {
        scenario_id: s.scenario_id,
        version: s.version,
        case_id: caseId,
        part_number: s.part_number,
        objective: s.objective,
        selected_alternative_id: s.selected_alternative_id,
        selected_alternative: alternativeSummary(
          (c.alternatives || []).filter(function (a) { return a.alternative_id === s.selected_alternative_id; })[0],
          result),
        scenario: s,
        result: result,
        consistency: cons,
        both_objectives: {
          assumption_check: twin.assumptions,
          revenue_order: twin.revenue.rows.map(function (r) { return r.alternative.alternative_id; }),
          gross_profit_order: twin.grossProfit.rows.map(function (r) { return r.alternative.alternative_id; })
        },
        journal: journalFor(caseId),
        generated_by: extra.generated_by || 'aim-ui scenario context',
        generated_at: extra.generated_at || null
      };
    }

    function journalFor(caseId) {
      return (journal[caseId] || []).slice();
    }

    function onChange(fn) { listeners.push(fn); }

    function reset(caseId) {
      var d = store.defaults(caseId);
      store.set(caseId, d);
      /* set() refuses to change a field to an identical value, so a reset that
         genuinely moves the record is written as an explicit edit set. */
      var target = {};
      Object.keys(d).forEach(function (k) {
        if (contracts.SCENARIO_FIELDS.indexOf(k) >= 0) target[k] = d[k];
      });
      var after = store.set(caseId, target);
      journal[caseId] = [{ kind: 'reset', fields: after.changes.map(function (c2) { return c2.field; }),
        version: after.scenario.version }];
      notify(caseId, 'reset');
      return after.scenario;
    }

    return {
      store: store,
      get: get,
      edit: edit,
      select: select,
      setObjective: setObjective,
      calculate: calculate,
      consistency: consistency,
      ranked: ranked,
      bothObjectives: bothObjectives,
      exportPackage: exportPackage,
      journal: journalFor,
      onChange: onChange,
      reset: reset,
      _all: function () { return store._all(); }
    };
  }

  return { makeScenarioContext: makeScenarioContext, alternativeSummary: alternativeSummary };
});
