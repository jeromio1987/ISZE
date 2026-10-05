/* ===========================================================================
   Named cost bases, effective-date validity and source status (F04).

   What was wrong in v0.3
     One advertised unchanged-offer baseline carried several cost bases. The
     no-action rows for pads, the cabin filter and the oil filter were priced on
     the September basis while alternatives on the same screen were priced on the
     October basis, so their `gp_before` figures did not agree and the baseline
     card used a third default. Two smaller faults sat behind it:

       1. the date helper fell back to the default (October) whenever the date
          was invalid or fell outside every window, so an unusable date produced
          a confident cost instead of an unresolved one; and
       2. the October basis declared a start date and no end date, so its stated
          rate window (to 31 March 2027) was silently open ended.

   What this does
     - resolves an offer effective date to exactly one forward basis, and returns
       UNRESOLVED for an unknown date, an unparseable date, or a date outside
       every documented window. There is no fallback to October;
     - reconstructs a missing window end from the basis's own stated rate window,
       and reports that it was reconstructed rather than declared;
     - produces one authorised resolution for a case: one effective date, one
       accepted basis, applied identically to the unchanged offer and to the
       proposed offer, plus the list of bases each comparable row can actually be
       priced on, so a common basis is chosen from what exists;
     - holds any deliberate supplier-cost change as a separate, explicitly
       justified assumption. A cost change is a different deal, not a different
       hidden date;
     - refuses to apply a forward cost to a recorded historical quantity and let
       the result be labelled historical actual gross profit.

   Cost bases are never blended. HIST states history, SEP26 states an offer in
   force to 30 September 2026, OCT26 states an offer effective from 1 October
   2026. Three rates, three windows, three answers.
   =========================================================================== */
(function (root) {
  'use strict';

  var engine = (typeof module === 'object' && module.exports)
    ? require('../engine/engine.js') : root.AIMEngine;

  var MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
                 jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

  function isBlank(v) {
    return v === null || v === undefined || (typeof v === 'string' && v.trim() === '');
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function parseISODate(text) {
    if (typeof text !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(text)) return null;
    var p = text.split('-'), y = +p[0], m = +p[1], d = +p[2];
    if (m < 1 || m > 12 || d < 1 || d > 31) return null;
    var dt = new Date(Date.UTC(y, m - 1, d));
    if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d) return null;
    return text;
  }

  function isoFromHuman(text) {
    var m = String(text).match(/(\d{1,2})\s+(\w{3})\s+(\d{4})/);
    if (!m) return null;
    var mon = MONTHS[m[2].toLowerCase()];
    if (!mon) return null;
    return m[3] + '-' + pad(mon) + '-' + pad(+m[1]);
  }

  function bases(payload) {
    return ((payload || {}).meta || {}).costBases || [];
  }

  function basisById(payload, basisId) {
    return bases(payload).filter(function (b) { return b.basis_id === basisId; })[0] || null;
  }

  /* ------------------------------------------------------------- windows -- */

  /* The declared window, with a missing end reconstructed from the basis's own
     stated rate window. The reconstruction is reported: a window that was
     inferred is not the same claim as a window that was declared. */
  function windowOf(basis) {
    if (!basis) {
      return { basis_id: null, status: null, from: null, to: null,
        window_state: 'no basis', from_source: 'none', to_source: 'none',
        rate_window: null, statement: 'No such cost basis is declared.' };
    }
    var from = parseISODate(basis.offer_effective_from);
    var to = parseISODate(basis.offer_effective_to);
    var fromSource = from ? 'declared offer_effective_from' : 'not declared';
    var toSource = to ? 'declared offer_effective_to' : 'not declared';

    var rateWindow = isBlank(basis.rate_window) ? null : String(basis.rate_window);
    if (rateWindow) {
      var m = rateWindow.match(/(\d{1,2}\s+\w{3}\s+\d{4})\s*(?:to|-|until)\s*(\d{1,2}\s+\w{3}\s+\d{4})/i);
      if (!from && m) { from = parseISODate(isoFromHuman(m[1])); fromSource = 'reconstructed from rate_window'; }
      if (!to && m) { to = parseISODate(isoFromHuman(m[2])); toSource = 'reconstructed from rate_window'; }
    }

    var state;
    if (from && to) {
      state = toSource === 'declared offer_effective_to' ? 'closed - declared'
        : 'closed - end reconstructed from the stated rate window';
    } else if (from && !to) {
      state = 'open ended - no end is declared and none could be read from the rate window';
    } else {
      state = 'no usable window';
    }

    return {
      basis_id: basis.basis_id,
      status: basis.status || null,
      from: from, to: to,
      window_state: state,
      from_source: fromSource,
      to_source: toSource,
      rate_window: rateWindow,
      statement: basis.basis_id + ' (status ' + (basis.status || 'unstated') + ') is valid from '
        + (from || 'an unstated start') + ' to ' + (to || 'an unstated end') + '. '
        + (toSource === 'reconstructed from rate_window'
            ? 'The end date was not carried as a field; it was reconstructed from the stated rate '
              + 'window "' + rateWindow + '" and is reported as reconstructed.'
            : 'The window is declared in the source.')
    };
  }

  function allWindows(payload) {
    return bases(payload).map(windowOf);
  }

  function forwardWindows(payload) {
    return allWindows(payload).filter(function (w) { return w.status === 'forward'; });
  }

  /* Every window on this payload is inspectable, so a date that resolves nowhere
     can be told why. */
  function declaredWindowsText(payload) {
    return allWindows(payload).map(function (w) {
      return w.basis_id + ' ' + (w.from || '?') + ' to ' + (w.to || 'no usable end');
    }).join('; ');
  }

  /* ------------------------------------------------------------- resolve -- */

  /* Resolve one offer effective date to one forward basis.
     `resolved:false` is a real answer, not an error state to be papered over. */
  function resolveBasis(payload, effectiveDate, opts) {
    opts = opts || {};
    if (isBlank(effectiveDate)) {
      return {
        ok: false, resolved: false, basis_id: null, basis: null, window: null,
        effective_date: null, effective_date_state: 'missing',
        windows: allWindows(payload),
        error: 'An offer effective date is required. Without it no supplier purchase-cost basis '
          + 'can be selected, and September and October must not be mixed.',
        statement: 'Unresolved: no offer effective date was supplied.'
      };
    }
    if (!parseISODate(effectiveDate)) {
      return {
        ok: false, resolved: false, basis_id: null, basis: null, window: null,
        effective_date: effectiveDate, effective_date_state: 'not a usable calendar date',
        windows: allWindows(payload),
        error: 'The offer effective date "' + effectiveDate + '" is not a usable calendar date '
          + '(expected YYYY-MM-DD). No basis has been assumed and October is not used as a fallback.',
        statement: 'Unresolved: the effective date is not a date.'
      };
    }

    var pool = opts.include_historical
      ? allWindows(payload)
      : forwardWindows(payload);

    var match = null;
    var openEnded = [];
    for (var i = 0; i < pool.length; i++) {
      var w = pool[i];
      if (!w.from || !w.to) { openEnded.push(w); continue; }
      if (effectiveDate >= w.from && effectiveDate <= w.to) { match = w; break; }
    }

    if (!match) {
      var why = openEnded.length
        ? ' The following basis declares no usable end and therefore cannot accept any date: '
          + openEnded.map(function (w) { return w.basis_id; }).join(', ') + '.'
        : '';
      return {
        ok: false, resolved: false, basis_id: null, basis: null, window: null,
        effective_date: effectiveDate, effective_date_state: 'outside every documented window',
        windows: allWindows(payload),
        error: 'The offer effective date ' + effectiveDate + ' falls outside every documented '
          + 'supplier-cost window (' + declaredWindowsText(payload) + '). The applicable basis is '
          + 'unresolved' + why,
        statement: 'Unresolved. A default basis is never substituted for a date that matches nothing.'
      };
    }

    var basis = basisById(payload, match.basis_id);
    return {
      ok: true, resolved: true, basis_id: match.basis_id, basis: basis, window: match,
      effective_date: effectiveDate, effective_date_state: 'inside a documented window',
      windows: allWindows(payload),
      error: null,
      statement: 'Offer effective ' + effectiveDate + ' takes the ' + match.basis_id
        + ' basis, valid ' + match.from + ' to ' + match.to + '. '
        + (match.to_source === 'reconstructed from rate_window'
            ? 'Window end reconstructed from the stated rate window.' : '')
    };
  }

  /* Backwards-compatible name: the reviewed defect called this costForDate. */
  function costForDate(payload, partNumber, effectiveDate, opts) {
    var res = resolveBasis(payload, effectiveDate, opts);
    if (!res.resolved) {
      return { ok: false, resolved: false, basis_id: null, record: null, error: res.error,
        effective_date: res.effective_date, windows: res.windows };
    }
    var rec = engine && engine.costRecord ? engine.costRecord(payload, partNumber, res.basis_id) : null;
    if (!rec) {
      return { ok: false, resolved: false, basis_id: res.basis_id, record: null,
        effective_date: res.effective_date, windows: res.windows,
        error: 'No verified parts purchase cost is held for ' + partNumber + ' on the '
          + res.basis_id + ' basis. The cost stays unresolved.' };
    }
    return { ok: true, resolved: true, basis_id: res.basis_id, record: rec,
      effective_date: res.effective_date, window: res.window, windows: res.windows, error: null };
  }

  /* ------------------------------------------------- where a date comes from */

  /* A date may only be derived from something in the source that states one.
     The default basis id is not a date and is never converted into one. */
  function deriveEffectiveDate(payload) {
    var candidates = [];
    var t = (payload || {}).turboPriceResolution || {};
    var resolvedOn = parseISODate(t.resolved_on);
    if (resolvedOn) {
      candidates.push({ date: resolvedOn,
        source: 'turboPriceResolution.resolved_on - the date this pack states the turbo price '
          + 'question was resolved' });
    }
    var buildDate = parseISODate((payload || {}).meta && payload.meta.buildDate);
    if (buildDate) {
      var inForce = forwardWindows(payload).filter(function (w) {
        return w.from && w.to && buildDate >= w.from && buildDate <= w.to;
      });
      if (inForce.length === 1) {
        candidates.push({ date: buildDate,
          source: 'the single forward rate window in force on the pack build date '
            + buildDate + ' (' + inForce[0].basis_id + ')' });
      }
    }
    if (!candidates.length) {
      return { date: null, source: null,
        statement: 'No offer effective date is stated in this payload and none can be derived from '
          + 'its own dated fields. It is recorded as unresolved rather than assumed.' };
    }
    return { date: candidates[0].date, source: candidates[0].source,
      alternatives: candidates,
      statement: 'The offer effective date was not supplied with the case. It is taken from '
        + candidates[0].source + ' (' + candidates[0].date + '), which is a date the payload '
        + 'states, not a default basis converted into one.' };
  }

  /* ---------------------------------------------------- one basis per case -- */

  /* Every comparable row on one screen must be priced on one basis. This reports
     which basis each row can be priced on, and which single basis is available to
     all of them. It does not average, and it does not silently move a row. */
  function comparableBases(payload, partNumbers, opts) {
    opts = opts || {};
    var rows = [];
    (partNumbers || []).forEach(function (pn) {
      var rec = null;
      (payload.verifiedCosts || []).some(function (r) {
        if (r.part_number === pn) { rec = r; return true; }
        return false;
      });
      var available = rec ? Object.keys(rec.cost_bases || {}) : [];
      rows.push({
        part_number: pn,
        cost_record_held: !!rec,
        bases_available: available,
        bases_unavailable: bases(payload).map(function (b) { return b.basis_id; })
          .filter(function (b) { return available.indexOf(b) < 0; })
      });
    });
    var common = null;
    if (rows.length) {
      common = rows[0].bases_available.filter(function (b) {
        return rows.every(function (r) { return r.bases_available.indexOf(b) >= 0; });
      });
    }
    var missing = rows.filter(function (r) { return !r.cost_record_held; })
      .map(function (r) { return r.part_number; });
    return {
      rows: rows,
      bases_held_by_every_row: common,
      parts_without_any_cost_record: missing,
      statement: common && common.length
        ? 'One basis is held for every compared part number (' + common.join(', ')
          + '), so the comparison can be run on one basis.'
        : (missing.length
            ? 'No single basis is held for every compared part number, and no cost record exists '
              + 'for ' + missing.join(', ') + '. Profit may not be compared across these rows, '
              + 'and a missing cost is not a cost of zero.'
            : 'No single basis is held for every compared part number.')
    };
  }

  /* The cost record's own availability on one basis, with the restriction flag
     carried forward so a caller cannot leak a restricted value by accident. */
  function costOnBasis(payload, partNumber, basisId) {
    var rec = engine && engine.costRecord ? engine.costRecord(payload, partNumber, basisId) : null;
    if (!rec) {
      return { available: false, basis_id: basisId, cost_eur: null, restricted: null,
        part_number: partNumber,
        statement: 'No verified parts purchase cost is held for ' + partNumber + ' on the '
          + basisId + ' basis. Unresolved, never zero.' };
    }
    return {
      available: true, basis_id: basisId, cost_eur: rec.cost_eur, restricted: rec.restricted,
      part_number: partNumber, unit: rec.unit, list_eur: rec.list_eur,
      formula: rec.formula, includes: rec.includes,
      statement: 'Parts purchase cost on the ' + basisId + ' basis for ' + partNumber
        + ', per ' + (rec.unit || 'unit') + '.'
    };
  }

  /* ------------------------------------------------- the authorised answer -- */

  /* The one resolution the screen is allowed to advertise: one date, one basis,
     the same basis on the unchanged and the proposed offer, and any deliberate
     supplier-cost change held out as a separate assumption. */
  function authoriseOfferBasis(payload, opts) {
    opts = opts || {};
    var date = opts.offer_effective_date;
    var dateSource = 'supplied with the offer';
    var derived = null;

    if (isBlank(date)) {
      derived = deriveEffectiveDate(payload);
      if (derived.date) { date = derived.date; dateSource = derived.source; }
    }

    var resolution = resolveBasis(payload, date, opts);
    var unresolved = [];
    if (!resolution.resolved) unresolved.push(resolution.error);

    var unchanged = null, proposed = null;
    if (resolution.resolved && opts.part_number) {
      unchanged = costOnBasis(payload, opts.part_number, resolution.basis_id);
      proposed = costOnBasis(payload, opts.part_number, resolution.basis_id);
      if (!unchanged.available) unresolved.push(unchanged.statement);
    }

    /* A supplier-cost change is a separate deal. It is never smuggled in as a
       second effective date, and it cannot be assumed on someone else's behalf. */
    var change = {
      changed: false,
      requires_justification: false,
      justified: false,
      from_basis_id: resolution.basis_id,
      to_basis_id: resolution.basis_id,
      statement: 'One basis is applied to the unchanged offer and to the proposed offer.'
    };
    if (opts.cost_change_basis_id && opts.cost_change_basis_id !== resolution.basis_id) {
      change.changed = true;
      change.requires_justification = true;
      change.to_basis_id = opts.cost_change_basis_id;
      change.justification = opts.cost_change_justification || null;
      change.justified = !isBlank(opts.cost_change_justification);
      change.statement = 'The proposal assumes a supplier purchase cost on the '
        + opts.cost_change_basis_id + ' basis while the unchanged offer is priced on the '
        + resolution.basis_id + ' basis. That is a deliberate cost change, held as a separate '
        + 'assumption' + (change.justified
            ? ' with a stated justification: ' + opts.cost_change_justification
            : '. No justification has been supplied, so it stays unapproved');
      if (!change.justified) unresolved.push('A supplier-cost change from ' + resolution.basis_id
        + ' to ' + opts.cost_change_basis_id + ' is assumed without a stated justification.');
    }

    return {
      ok: resolution.resolved && unresolved.length === 0,
      resolved: resolution.resolved,
      effective_date: resolution.effective_date,
      effective_date_source: dateSource,
      date_derivation: derived,
      basis_id: resolution.basis_id,
      basis: resolution.basis,
      window: resolution.window,
      unchanged_offer: unchanged,
      proposed_offer: proposed,
      cost_change_assumption: change,
      windows: resolution.windows,
      unresolved: unresolved,
      statement: resolution.resolved
        ? 'One authorised resolution: offer effective ' + resolution.effective_date
          + ' on the ' + resolution.basis_id + ' basis, applied to the unchanged offer and to the '
          + 'proposed offer alike. The same-screen promise of one unchanged-offer baseline now '
          + 'holds for profit as well as for price.'
        : 'Unresolved: ' + (resolution.error || 'the offer basis could not be established.')
    };
  }

  /* ------------------------------------------------------- use guardrails -- */

  /* HIST states a historical actual. A forward basis states a forward scenario.
     Applying a forward cost to a recorded historical quantity and calling the
     result historical actual gross profit is the defect this refuses. */
  function guardBasisUse(input) {
    input = input || {};
    var basisId = input.cost_basis_id || null;
    var basis = basisId ? basisById(input.payload || {}, basisId)
      : (input.cost_basis || null);
    var status = basis ? basis.status : (input.cost_basis_status || null);
    var historicalQuantity = input.quantity_label === 'observed history';
    var periodState = input.evidence_period_state || (input.evidence_period ? 'declared' : 'undeclared');

    if (!basisId) {
      return { permitted: true, label: 'no basis named', status: status,
        statement: 'No cost basis is named on this scenario, so no forward cost is being presented '
          + 'as a historical actual.' };
    }
    if (status === 'historical') {
      return { permitted: true, label: 'historical actual', status: status,
        statement: 'The historical basis is the only basis on which a historical actual gross '
          + 'profit may be stated.' };
    }
    if (historicalQuantity && status === 'forward' && !input.explicit_forward_scenario) {
      return { permitted: false, label: 'refused', status: status,
        refuses: true,
        statement: 'Refused: the quantity is recorded history and the cost is a forward basis '
          + '(' + basisId + '). A forward cost must not be applied to a recorded historical '
          + 'quantity and labelled historical actual gross profit. Price the offer forward and '
          + 'label it a forward scenario, or state the historical actual on the historical basis.' };
    }
    if (historicalQuantity && status === 'forward') {
      return { permitted: true, label: 'forward scenario on a recorded quantity',
        status: status, refuses: false,
        statement: 'This figure is a forward scenario. Its quantity is recorded history on the '
          + 'period ' + (input.evidence_period || 'not stated') + ' and its cost is the forward '
          + 'basis ' + basisId + '. It is not a historical actual and must not be labelled as one.' };
    }
    return { permitted: true, label: 'forward scenario', status: status, refuses: false,
      statement: 'Forward basis ' + basisId + ' on a ' + (periodState === 'declared'
        ? 'stated period' : 'period that is not declared') + '.' };
  }

  /* A basis is only comparable when the period, the sales stage and the unit
     agree as well. This is the cost-side half of that check. */
  function basisCompatibility(a, b) {
    a = a || {}; b = b || {};
    var findings = [];
    if (a.cost_basis_id !== b.cost_basis_id) {
      findings.push('Different cost bases: ' + (a.cost_basis_id || 'not stated') + ' and '
        + (b.cost_basis_id || 'not stated') + '. Profit is not comparable across them.');
    }
    if (a.evidence_period !== b.evidence_period) {
      findings.push('Different evidence periods: ' + (a.evidence_period || 'not stated') + ' and '
        + (b.evidence_period || 'not stated') + '.');
    }
    if (a.sales_stage !== b.sales_stage) {
      findings.push('Different sales stages: ' + (a.sales_stage || 'not stated') + ' and '
        + (b.sales_stage || 'not stated') + '.');
    }
    if (a.unit !== b.unit) {
      findings.push('Different units: ' + (a.unit || 'not stated') + ' and '
        + (b.unit || 'not stated') + '. A kit is not a unit.');
    }
    var from = parseISODate(a.offer_effective_date), to = parseISODate(b.offer_effective_date);
    if (from && to && from !== to) {
      findings.push('Different offer effective dates: ' + from + ' and ' + to + '.');
    }
    return {
      ok: findings.length === 0,
      comparable: findings.length === 0,
      findings: findings,
      statement: findings.length === 0
        ? 'Same basis, period, sales stage, unit and effective date, so the two figures may be '
          + 'compared.'
        : 'Not comparable. ' + findings.join(' ')
    };
  }

  var API = {
    parseISODate: parseISODate,
    isoFromHuman: isoFromHuman,
    bases: bases,
    basisById: basisById,
    windowOf: windowOf,
    allWindows: allWindows,
    forwardWindows: forwardWindows,
    declaredWindowsText: declaredWindowsText,
    resolveBasis: resolveBasis,
    costForDate: costForDate,
    deriveEffectiveDate: deriveEffectiveDate,
    comparableBases: comparableBases,
    costOnBasis: costOnBasis,
    authoriseOfferBasis: authoriseOfferBasis,
    guardBasisUse: guardBasisUse,
    basisCompatibility: basisCompatibility
  };

  root.AIMCostBasis = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
