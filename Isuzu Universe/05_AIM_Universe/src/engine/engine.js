/* ===========================================================================
   Corrected AIM pricing engine  -  FIN-02, FIN-03, FIN-04, FIN-06, FIN-07,
   FIN-08, FIN-09 and the arithmetic half of FIN-04-date (F04).

   One calculation path. Manual price testing, the ranking, the both-objective
   view, a saved case and every export all call calculate() below, so the same
   alternative cannot produce two different answers.

   Declared measure - kept exactly as v03 declared it, not redefined:
     revenue      = applicable ISZE net parts selling price x quantity
     gross profit = revenue - parts purchase cost of the quantities sold
     gross margin = gross profit / revenue
   Parts purchase cost only. Freight, duty, overheads and distributor kickbacks
   stay out of the measure, and the invoice discount is not deducted twice.

   What was wrong in v03 and what this file does instead
   ---------------------------------------------------------------------------
   F02  v03 reported margin_after_pct as 1 - cost / proposed_price. That is the
        margin on one discounted unit, not the margin on the offer. A combined
        offer of 100 units at 100 plus 20 at 80 on a 60 cost earns 4,400 on
        11,600, which is 37.931%, and v03 reported 25%. v03 also reported 40%
        on a case whose own printed profit was 3,500 on 10,000 (35%) because it
        ignored the support it had already deducted.
        Here: margin_after_pct = reported gross profit / reported revenue, and
        the unit margin is reported separately as margin_unit_after_pct.

   F03  v03 priced unchanged units at the reduced price in an incremental-only
        offer, so its break-even was too high (125 where 100 is right, 200 where
        100 is right, 210 where 110 is right). Here: all-volume and incremental
        use separate equations, and a required orderable quantity is rounded up
        to a real pack rather than a threshold plus a hundredth rounded away.

   F06  v03 validated quantity_before but not quantity_after, so negative, NaN
        and infinite proposed quantities were accepted, and an invalid support
        string quietly became zero. Here: strict finite validation, every reason
        returned, and zero / unknown / returns / invalid kept as four different
        states. A missing cost suppresses profit, never revenue.

   F07  v03 called the Genuine/BVP migration a move and then priced the original
        BVP reference unchanged, so it returned a fabricated zero. Here: with no
        two-product inputs the result is migration_status 'unresolved' with
        revenue_change and gp_change null, and the unchanged-offer side is still
        reported so the row is comparable. Migration is not new business.

   F09  v03rank applied the alternative's volume assumption and v03both ignored
        it unless an override was passed, so PADS-VOL was 1,400 through one
        entry point and 1,750 through the other. Here: one normalisation
        (quantityAfter) and one calculation (calculate), used by both.

   F04  v03costForDate fell back to OCT26 for an invalid or out-of-window date.
        Here: an unusable date resolves to nothing, with a reason. The declared
        default basis is used only when no date was supplied at all, and the
        ranking then uses that one basis for every comparable row so that one
        unchanged offer is compared with one cost.

   The exported names v03run, v03rank, v03both, v03baseline, v03costForDate,
   v03costRecord, v03priceAfter, v03quantityAfter, v03fmtNum and v03fmtPct are
   kept as aliases so the existing UI can keep calling them.

   Loads as module.exports under Node and as root.PricingEngine / root.AIMEngine
   in a browser.
   =========================================================================== */
(function (root) {
  'use strict';

  /* ------------------------------------------------------------- numbers -- */

  function isFiniteNumber(x) {
    return typeof x === 'number' && Number.isFinite(x);
  }
  function round2(x) {
    return Math.round(x * 100) / 100;
  }
  function money(x) {
    return Math.round((x + Number.EPSILON) * 100) / 100;
  }
  function change(previous, current) {
    return (isFiniteNumber(previous) && isFiniteNumber(current) && previous !== 0)
      ? 100 * (current / previous - 1) : null;
  }
  function isBlank(v) {
    return v === null || v === undefined
      || (typeof v === 'string' && v.trim() === '');
  }

  /* A blank means "no value supplied" and never becomes zero. Booleans, arrays
     and objects are refused rather than coerced: Number([]) is 0 and Number(true)
     is 1, and neither is a quantity an operator meant to type. */
  function toNumberOrNull(v) {
    if (isBlank(v)) return null;
    // Only numbers and numeric text are supported. Symbol must not throw and
    // BigInt must not be silently narrowed; both are invalid at this boundary.
    if (typeof v !== 'number' && typeof v !== 'string') return null;
    var n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  function numOr(v, d) {
    var n = toNumberOrNull(v);
    return n === null ? d : n;
  }

  function fmtNum(x, d) {
    if (!isFiniteNumber(x)) return '-';
    return Number(x).toLocaleString('en-GB',
      { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function fmtPct(x) {
    if (!isFiniteNumber(x)) return '-';
    return (x > 0 ? '+' : '') + Number(x).toFixed(1) + '%';
  }

  /* ------------------------------------------------------- payload state -- */

  /* The engine holds no embedded business data. A caller hands it the payload
     once (setPayload) and the ranking helpers use it; calculate() itself never
     reads a payload, which is why the arithmetic can be tested on fixtures. */
  var configuredPayload = null;
  function setPayload(payload) {
    configuredPayload = payload || null;
    return configuredPayload;
  }
  function getPayload() {
    return configuredPayload;
  }
  function isPayloadLike(x) {
    return !!x && typeof x === 'object' && !Array.isArray(x)
      && (Object.prototype.hasOwnProperty.call(x, 'verifiedCosts')
        || Object.prototype.hasOwnProperty.call(x, 'cases')
        || Object.prototype.hasOwnProperty.call(x, 'meta'));
  }

  /* -------------------------------------------------------- named bases -- */

  var MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
                 jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

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
    return m[3] + '-' + (mon < 10 ? '0' : '') + mon + '-' + (m[1].length < 2 ? '0' : '') + m[1];
  }

  /* The window a basis is valid for. A basis that declares no window at all is
     not treated as open ended; it is reported as having no declared window. */
  function basisWindow(basis) {
    basis = basis || {};
    var from = parseISODate(basis.offer_effective_from) || null;
    var to = parseISODate(basis.offer_effective_to) || null;
    if (!from || !to) {
      var m = String(basis.rate_window || '').match(
        /(\d{1,2}\s+\w{3}\s+\d{4})\s*(?:to|-|until)\s*(\d{1,2}\s+\w{3}\s+\d{4})/i);
      if (m) {
        if (!from) from = parseISODate(isoFromHuman(m[1]));
        if (!to) to = parseISODate(isoFromHuman(m[2]));
      }
    }
    return { from: from, to: to };
  }

  function basisList(payload) {
    return ((payload && payload.meta && payload.meta.costBases) || []);
  }
  function basisById(payload, id) {
    var list = basisList(payload);
    for (var i = 0; i < list.length; i++) {
      if (list[i].basis_id === id) return list[i];
    }
    return null;
  }
  function defaultForwardBasisId(payload) {
    return (payload && payload.meta && payload.meta.defaultForwardBasis) || null;
  }
  function forwardBases(payload) {
    return basisList(payload).filter(function (b) { return b.status === 'forward'; });
  }

  /* The effective-date rule, made executable. An unusable date resolves to
     nothing and says why. It never falls back to the nearest forward basis. */
  function basisForDate(payload, effectiveDate) {
    if (isBlank(effectiveDate)) {
      return { ok: false, resolved: false, basis_id: null, source: 'none',
        error: 'An offer effective date is required. Without it the applicable supplier '
             + 'purchase-cost basis cannot be selected, and September and October must not be mixed.' };
    }
    if (!parseISODate(effectiveDate)) {
      return { ok: false, resolved: false, basis_id: null, source: 'none',
        error: 'The offer effective date "' + effectiveDate + '" is not a usable calendar date '
             + '(expected YYYY-MM-DD). No cost basis has been assumed.' };
    }

    var fwd = forwardBases(payload), match = null, matches = [], undated = [], declared = [];
    for (var i = 0; i < fwd.length; i++) {
      var w = basisWindow(fwd[i]);
      declared.push(fwd[i].basis_id + ' (' + (w.from || '?') + ' to ' + (w.to || 'no declared end') + ')');
      if (!w.from || !w.to) { undated.push(fwd[i].basis_id); continue; }
      if (effectiveDate >= w.from && effectiveDate <= w.to) { matches.push(fwd[i]); }
    }
    if (matches.length > 1) {
      return { ok: false, resolved: false, basis_id: null, source: 'none',
        error: 'Multiple forward cost windows overlap on ' + effectiveDate + ': '
          + matches.map(function (b) { return b.basis_id; }).join(', ')
          + '. The source owner must resolve the ambiguity; array order is not a cost rule.' };
    }
    match = matches.length === 1 ? matches[0] : null;
    if (!match) {
      return { ok: false, resolved: false, basis_id: null, source: 'none',
        error: 'The offer effective date ' + effectiveDate + ' falls outside every declared '
             + 'supplier-cost window (' + declared.join(', ') + '). The applicable basis is unresolved.'
             + (undated.length
                ? ' ' + undated.join(', ') + ' declares no usable window and was not assumed.'
                : '') };
    }
    return { ok: true, resolved: true, basis_id: match.basis_id,
      source: 'offer effective date ' + effectiveDate,
      window: basisWindow(match) };
  }

  /* The one basis a comparison is run on. A supplied date decides it. With no
     date at all the payload's declared default is used and named as such; that
     is a declared default, not a fallback from an unusable date. */
  function resolveOfferBasis(payload, offerDate) {
    if (!isBlank(offerDate)) return basisForDate(payload, offerDate);
    var id = defaultForwardBasisId(payload);
    if (!id) {
      return { ok: false, resolved: false, basis_id: null, source: 'none',
        error: 'No offer effective date was supplied and no default forward cost basis is '
             + 'declared, so the comparison basis is unresolved.' };
    }
    if (!basisById(payload, id)) {
      return { ok: false, resolved: false, basis_id: null, source: 'none',
        error: 'No offer effective date was supplied and the declared default basis "' + id
             + '" is not present in the cost bases, so the comparison basis is unresolved.' };
    }
    return { ok: true, resolved: true, basis_id: id,
      source: 'declared default forward basis "' + id + '" (no offer effective date was '
            + 'supplied). One basis is used for every comparable row.' };
  }

  /* Verified parts purchase cost for a part on a named basis. The basis must be
     named: an unnamed cost basis is not silently filled in. */
  function costRecord(a, b, c) {
    var payload, partNumber, basisId;
    if (isPayloadLike(a)) { payload = a; partNumber = b; basisId = c; }
    else { payload = getPayload(); partNumber = a; basisId = b; }

    if (isBlank(basisId)) return null;
    var rows = ((payload && payload.verifiedCosts) || []).filter(function (r) {
      return r.part_number === partNumber;
    });
    if (!rows.length) return null;
    var r = rows[0];
    var cell = (r.cost_bases || {})[basisId];
    if (!cell) return null;
    return {
      part_number: r.part_number, description: r.description, unit: r.unit,
      basis_id: basisId, basis_name: cell.name, cost_eur: cell.cost_eur,
      jpy_per_eur: cell.jpy_per_eur, rate_window: cell.rate_window,
      source_discount: cell.source_discount, status: cell.status,
      cost_type: r.cost_type, formula: r.formula, list_eur: r.list_eur,
      includes: r.includes, restricted: r.restricted,
      base_price_source: r.base_price_source, list_source: r.list_source,
      list_valid_from: r.list_valid_from, gap: r.cost_gap_note,
      all_bases: r.cost_bases
    };
  }

  /* Accepts either (payload, part_number, effective_date) or the v03 shape
     (part_number, effective_date) with the payload supplied once by setPayload. */
  function costForDate(a, b, c) {
    var payload, pn, date;
    if (isPayloadLike(a)) { payload = a; pn = b; date = c; }
    else { payload = getPayload(); pn = a; date = b; }

    var basis = basisForDate(payload, date);
    if (!basis.ok) {
      return { ok: false, resolved: false, basis_id: null,
        error: basis.error, source: basis.source };
    }
    if (isBlank(pn)) {
      return { ok: true, resolved: true, basis_id: basis.basis_id, record: null,
        source: basis.source };
    }
    var rec = costRecord(payload, pn, basis.basis_id);
    if (!rec) {
      return { ok: false, resolved: false, basis_id: basis.basis_id,
        error: 'No verified parts purchase cost is held for ' + pn + ' on the '
             + basis.basis_id + ' basis. The cost stays unresolved.' };
    }
    return { ok: true, resolved: true, basis_id: basis.basis_id, record: rec, source: basis.source };
  }

  /* ------------------------------------------------- price and quantity -- */

  /* The prices used in a scenario are the ones a customer would actually be
     quoted, so they are held to two decimals. A zero move returns the baseline
     price unchanged rather than a phantom move on a four-decimal average. */
  function priceAfter(baselinePrice, deltaPct) {
    var baselineNumber = toNumberOrNull(baselinePrice);
    var delta = isBlank(deltaPct) ? 0 : toNumberOrNull(deltaPct);
    if (baselineNumber === null || delta === null) return NaN;
    return round2(round2(baselineNumber) * (1 + delta / 100));
  }

  /* A nonblank but invalid input must reach calculate() as invalid, not null.
     Null means 'no value supplied' there and would silently restore the baseline.
     NaN is a validation signal only; it is never returned in a financial result. */
  function quantityAfter(baseQuantity, alternative, opts) {
    opts = opts || {};
    if (!isBlank(opts.quantity_after)) {
      var explicit = toNumberOrNull(opts.quantity_after);
      return explicit === null ? NaN : explicit;
    }
    var v = alternative && alternative.volume_assumption;
    if (!isBlank(v)) {
      var movement = toNumberOrNull(v);
      return movement === null ? NaN : baseQuantity * (1 + movement / 100);
    }
    return baseQuantity;
  }

  /* A required quantity that has to be ordered is rounded up to a whole pack. */
  function roundToPack(quantity, packSize) {
    if (!isFiniteNumber(quantity)) return null;
    var pack = (isFiniteNumber(packSize) && packSize > 0) ? packSize : 1;
    return Math.ceil(quantity / pack) * pack;
  }

  /* The smallest whole pack strictly above a threshold. "Just over" has to be a
     real orderable quantity, not a displayed threshold plus a hundredth. */
  function smallestPackAbove(threshold, packSize) {
    if (!isFiniteNumber(threshold)) return null;
    var pack = (isFiniteNumber(packSize) && packSize > 0) ? packSize : 1;
    if (threshold < 0) return 0;
    return Math.floor(threshold / pack) * pack + pack;
  }

  /* ------------------------------------------------------------ inputs -- */

  var TITLE_WITHDRAWAL = 'A proposed quantity of zero is a full withdrawal, not a pricing '
    + 'scenario. Record it as a decision to stop supplying this part.';

  /* Strict validation. Zero, unknown, a return and an invalid entry are four
     different states, and every reason for a refusal is returned so an operator
     is not sent round the form four times. */
  function validateScenario(s) {
    s = s || {};
    var errors = [];
    var states = {};

    var p0 = toNumberOrNull(s.price_before);
    var p1 = toNumberOrNull(s.price_after);
    var q0 = toNumberOrNull(s.quantity_before);
    var label = (typeof s.quantity_label === 'string' && s.quantity_label.trim() !== '')
      ? s.quantity_label : 'manual scenario';
    var returnDeclared = /return|credit note|goods back|take-?back/i.test(label);

    states.price_before = (p0 !== null && p0 > 0) ? 'value' : (isBlank(s.price_before) ? 'unknown' : 'invalid');
    states.price_after = (p1 !== null && p1 > 0) ? 'value' : (isBlank(s.price_after) ? 'unknown' : 'invalid');
    states.quantity_before = (q0 !== null && q0 > 0) ? 'value' : (isBlank(s.quantity_before) ? 'unknown' : 'invalid');

    if (p0 === null || p0 <= 0) errors.push('The starting price must be a number above zero.');
    if (p1 === null || p1 <= 0) errors.push('The proposed price must be a number above zero.');
    if (q0 === null || q0 <= 0) errors.push('The starting quantity must be a number above zero.');

    /* quantity_after is optional: blank means "the starting quantity stands", and
       that is an unknown, not a zero. A supplied value must be a real finite
       quantity. Zero is a withdrawal. A negative quantity is a return, and only
       when the scenario says so. */
    var q1 = null, q1supplied = !isBlank(s.quantity_after);
    if (q1supplied) {
      q1 = toNumberOrNull(s.quantity_after);
      if (q1 === null) {
        states.quantity_after = 'invalid';
        errors.push('The proposed quantity is not a number. Leave it blank to use the starting '
          + 'quantity, or enter a whole number of units.');
      } else if (q1 === 0) {
        states.quantity_after = 'zero';
        errors.push(TITLE_WITHDRAWAL);
      } else if (q1 < 0) {
        if (returnDeclared) {
          states.quantity_after = 'return';
        } else {
          states.quantity_after = 'invalid';
          errors.push('The proposed quantity cannot be negative. Net-negative activity is a '
            + 'return: label the scenario as a return of goods to state it deliberately.');
        }
      } else {
        states.quantity_after = 'value';
      }
    } else {
      states.quantity_after = 'unknown';
    }

    var support = 0, supportSupplied = !isBlank(s.support_eur);
    if (supportSupplied) {
      var sv = toNumberOrNull(s.support_eur);
      if (sv === null) {
        states.support = 'invalid';
        errors.push('The support amount is not a number. Enter 0 if no support exists, or leave it blank.');
      } else if (sv < 0) {
        states.support = 'invalid';
        errors.push('Support cannot be a negative amount.');
      } else {
        states.support = (sv === 0) ? 'zero' : 'value';
        support = sv;
      }
    } else {
      states.support = 'unknown';
    }

    var cost = null, costSupplied = !isBlank(s.cost_eur);
    if (costSupplied) {
      var cv = toNumberOrNull(s.cost_eur);
      if (cv === null) {
        states.cost = 'invalid';
        errors.push('The parts cost is not a number. Leave it blank if no verified cost exists.');
      } else if (cv < 0) {
        states.cost = 'invalid';
        errors.push('A parts cost cannot be negative.');
      } else {
        states.cost = (cv === 0) ? 'zero' : 'value';
        cost = cv;
      }
    } else {
      states.cost = 'unknown';
    }

    var scope = s.scope || 'all';
    if (scope !== 'all' && scope !== 'incremental') {
      errors.push('The eligibility scope must be all eligible volume or incremental units only.');
    }

    /* In an incremental-only offer the proposed quantity is the total, so it can
       never fall below the quantity that already exists. v03 clamped it silently,
       which turned an impossible assumption into a valid-looking result. */
    if (scope === 'incremental' && q1 !== null && q1 >= 0 && q0 !== null && q1 < q0) {
      errors.push('Incremental-only cannot propose fewer units than the ' + fmtNum(q0, 0)
        + ' already buying. Choose all eligible volume to model a volume reduction.');
    }
    if (scope === 'incremental' && states.quantity_after === 'return') {
      errors.push('A return of goods is not an incremental-only offer. Choose all eligible volume.');
    }

    var pack = 1;
    if (!isBlank(s.pack_size)) {
      var pv = toNumberOrNull(s.pack_size);
      if (pv === null || pv <= 0 || Math.floor(pv) !== pv) {
        errors.push('The pack size must be a positive whole number of units.');
      } else {
        pack = pv;
      }
    }

    return {
      ok: errors.length === 0,
      errors: errors,
      states: states,
      values: {
        price_before: p0, price_after: p1,
        quantity_before: q0,
        quantity_after: q1,
        quantity_after_supplied: q1supplied,
        quantity_is_return: states.quantity_after === 'return',
        quantity_label: label,
        cost: cost,
        cost_supplied: costSupplied,
        support: support,
        support_supplied: supportSupplied,
        scope: scope,
        pack_size: pack
      }
    };
  }

  /* ------------------------------------------------------ result shape -- */

  /* Every key here is declared in src/data/contracts.js RESULT_FIELDS. The four
     input states are surfaced through quantity_label, flags and conditional
     rather than a new field, so the shared contract does not have to grow. */
  function blankResult() {
    return {
      ok: false, error: null, errors: [], resolved: false, migration_status: null,
      price_before: null, price_after: null, scope: 'all', pack_size: 1,
      quantity_before: null, quantity_after: null, quantity_label: 'manual scenario',
      volume_is_observed: false, extra_quantity: null,
      revenue_before: null, revenue_after: null, revenue_change: null, revenue_pct: null,
      gp_before: null, gp_after: null, gp_change: null, gp_pct: null,
      margin_before_pct: null, margin_after_pct: null, margin_unit_after_pct: null,
      margin_pp_change: null,
      qty_preserve_revenue: null, qty_preserve_gp: null,
      extra_qty_to_preserve_revenue: null, extra_qty_to_preserve_gp: null,
      extra_qty_to_exceed_revenue: null, extra_qty_to_exceed_gp: null,
      qty_preserve_revenue_label: null, qty_preserve_gp_label: null,
      extra_qty_exceed_revenue_label: null, extra_qty_exceed_gp_label: null,
      tolerable_volume_loss_pct: null, tolerable_loss_revenue_pct: null,
      tolerable_loss_gp_pct: null, discount_on_existing_volume_eur: null,
      bridge_revenue_change: null, bridge_cost_change: null,
      bridge_support_eur: null, bridge_reconciles: null,
      cost: null, cost_basis_id: null, cost_is_zero: false, cost_missing_not_zero: false,
      support_eur: 0, support_counted_once: true,
      evidence_period: null, offer_effective_date: null,
      flags: [], conditional: []
    };
  }

  /* --------------------------------------------------------- calculate -- */

  /* Finite inputs can still overflow when multiplied. An invalid financial
     result must not be marked usable, and JSON must not disguise Infinity/NaN
     as null while leaving ok:true. Refuse the whole computed result. */
  function finalizeResult(result) {
    var invalidPaths = [], seen = new Set();
    function visit(value, path) {
      if (typeof value === 'number') {
        if (!Number.isFinite(value)) invalidPaths.push(path);
      } else if (value && typeof value === 'object' && !seen.has(value)) {
        seen.add(value);
        Object.keys(value).forEach(function (key) { visit(value[key], path ? path + '.' + key : key); });
      }
    }
    visit(result, '');
    if (!invalidPaths.length) return result;
    var refused = blankResult();
    ['evidence_period', 'offer_effective_date', 'cost_basis_id', 'quantity_label'].forEach(function (key) {
      if (typeof result[key] === 'string') refused[key] = result[key];
    });
    if (result.migration_status) refused.migration_status = 'unresolved';
    refused.error = 'The calculation exceeds the finite numeric range in: '
      + invalidPaths.join(', ') + '. Check the stated units and inputs; no financial result is available.';
    refused.errors = [refused.error];
    refused.flags.push({ code: 'NUMERIC_RANGE_EXCEEDED', severity: 'high',
      text: 'Arithmetic overflow: no financial result is available.', amount: null });
    return refused;
  }

  function calculate(scenario) {
    var R = blankResult();
    var input = scenario || {};
    var v = validateScenario(input);

    R.evidence_period = input.evidence_period || null;
    R.offer_effective_date = input.offer_effective_date || null;
    R.cost_basis_id = input.cost_basis_id || null;
    R.quantity_label = v.values.quantity_label;
    R.volume_is_observed = v.values.quantity_label === 'observed history';

    if (!v.ok) {
      R.error = v.errors[0];
      R.errors = v.errors;
      return finalizeResult(R);
    }

    var x = v.values;
    var p0 = x.price_before, p1 = x.price_after, q0 = x.quantity_before;
    var cost = x.cost, support = x.support, scope = x.scope, pack = x.pack_size;

    R.price_before = p0; R.price_after = p1;
    R.quantity_before = q0; R.scope = scope; R.pack_size = pack;
    R.qty_preserve_revenue_label = null;

    if (cost !== null) {
      R.cost = cost;
      R.cost_is_zero = (cost === 0);
      R.cost_missing_not_zero = false;
      if (cost === 0) {
        R.conditional.push('A parts cost of zero was entered. That is a value, not a missing '
          + 'field, and it makes gross margin equal the price. Confirm it.');
      }
    } else {
      R.cost_missing_not_zero = true;
      R.conditional.push('No verified parts purchase cost is held for this part, so gross profit '
        + 'and gross margin are not calculated. Revenue and the revenue break-even still are. '
        + 'A verified parts purchase cost completes the comparison.');
    }
    R.support_eur = support;
    R.support_counted_once = true;

    /* ---- the unchanged offer. Reported even when the proposal is unresolved,
       so one row is never silently incomparable with the rest. ---- */
    R.revenue_before = p0 * q0;
    if (cost !== null) {
      R.gp_before = q0 * (p0 - cost);
      R.margin_before_pct = R.revenue_before ? 100 * R.gp_before / R.revenue_before : null;
    }

    /* ---- a Genuine/BVP migration is a two-product move, not a single-part
       price step (F07). It is never reported as a fabricated zero. ---- */
    if (input.kind === 'migration') {
      return migrationResult(R, input, x);
    }

    /* ---- quantity and eligibility ---- */
    var qAll, qDisc, extra = 0;
    if (scope === 'all') {
      qAll = x.quantity_after_supplied ? x.quantity_after : q0;
      qDisc = qAll;
      extra = qAll - q0;
    } else {
      extra = x.quantity_after_supplied ? Math.max(0, x.quantity_after - q0) : 0;
      qAll = q0 + extra;
      qDisc = extra;
    }
    R.quantity_after = qAll;
    R.extra_quantity = scope === 'all' ? (qAll - q0) : extra;

    if (x.quantity_is_return) {
      R.flags.push({ code: 'NET_NEGATIVE_RETURN', severity: 'high',
        text: 'Net activity on the proposal is negative: this is a return of goods, not a sale. '
            + 'It is reported as its own case and is not a pricing offer.',
        amount: null });
      R.conditional.push('The proposed quantity is negative and the scenario is labelled as a '
        + 'return, so the revenue and cost figures are a credit-note movement. No price is being '
        + 'proposed.');
    } else if (!x.quantity_after_supplied) {
      R.conditional.push('No proposed quantity was supplied, so the starting quantity is used '
        + 'unchanged. That is an unknown volume, not a volume of zero.');
    }

    /* ---- revenue ---- */
    R.revenue_after = (scope === 'all') ? p1 * qAll : p0 * q0 + p1 * qDisc;
    R.revenue_change = R.revenue_after - R.revenue_before;
    R.revenue_pct = R.revenue_before ? 100 * R.revenue_change / R.revenue_before : null;
    R.discount_on_existing_volume_eur = (scope === 'all' ? q0 : 0) * (p0 - p1);

    /* ---- gross profit, with the exact bridge (FIN-04) ---- */
    if (cost !== null) {
      var costOfGoodsBefore = q0 * cost;
      var costOfGoodsAfter = (scope === 'all') ? qAll * cost : q0 * cost + qDisc * cost;
      var gpGross = R.revenue_after - costOfGoodsAfter;
      R.gp_after = gpGross - support;                 /* support counted exactly once */
      R.gp_change = R.gp_after - R.gp_before;
      R.gp_pct = R.gp_before ? 100 * R.gp_change / Math.abs(R.gp_before) : null;

      R.bridge_revenue_change = R.revenue_change;
      R.bridge_cost_change = costOfGoodsAfter - costOfGoodsBefore;
      R.bridge_support_eur = support;
      R.bridge_reconciles = Math.abs(
        (R.bridge_revenue_change - R.bridge_cost_change - R.bridge_support_eur)
        - R.gp_change) < 1e-9;

      /* F02: the margin that reconciles to what the engine itself printed. The
         unit margin is a different measure and is reported under its own name. */
      R.margin_after_pct = R.revenue_after ? 100 * R.gp_after / R.revenue_after : null;
      R.margin_unit_after_pct = (p1 > 0) ? 100 * (1 - cost / p1) : null;
      R.margin_pp_change = (R.margin_before_pct === null || R.margin_after_pct === null)
        ? null : R.margin_after_pct - R.margin_before_pct;
    }

    /* ---- break-even, split by eligibility (F03) ---- */
    var revRaw = null, gpRaw = null;
    if (scope === 'all') {
      revRaw = p1 > 0 ? R.revenue_before / p1 : null;
      R.qty_preserve_revenue_label = 'all eligible units would need this price';
      if (cost !== null) {
        if (p1 > cost) {
          gpRaw = (R.gp_before + support) / (p1 - cost);
          R.qty_preserve_gp_label = 'all eligible units would need this price';
        } else {
          R.qty_preserve_gp_label = 'not attainable: the proposed price does not exceed the parts '
            + 'cost, so no quantity restores gross profit';
        }
      }
    } else {
      /* Existing units keep the current price, so the business that is already
         there already holds its revenue and its gross profit. Only the
         additional units have to recover the support. */
      revRaw = q0;
      R.qty_preserve_revenue_label = 'the existing units already hold revenue at the current price';
      if (cost !== null) {
        if (p1 > cost) {
          gpRaw = q0 + support / (p1 - cost);
          R.qty_preserve_gp_label = 'existing units plus the additional units needed to recover '
            + 'the support at their incremental contribution';
        } else if (support === 0) {
          gpRaw = q0;
          R.qty_preserve_gp_label = 'the existing units already hold gross profit, and no '
            + 'support has to be recovered';
        } else {
          R.qty_preserve_gp_label = 'not attainable: the proposed price does not exceed the parts '
            + 'cost, so no additional unit recovers the support';
        }
      }
    }
    R.qty_preserve_revenue = revRaw;
    R.qty_preserve_gp = gpRaw;

    /* A quantity that has to be ordered is a whole pack, rounded up. "More than"
       is the smallest real orderable quantity above the threshold, not a
       threshold plus a hundredth that rounds away. */
    R.extra_qty_to_preserve_revenue = (revRaw === null) ? null
      : Math.max(0, roundToPack(revRaw - q0, pack));
    R.extra_qty_to_preserve_gp = (gpRaw === null) ? null
      : Math.max(0, roundToPack(gpRaw - q0, pack));
    R.extra_qty_to_exceed_revenue = (revRaw === null) ? null
      : Math.max(0, smallestPackAbove(revRaw, pack) - q0);
    R.extra_qty_to_exceed_gp = (gpRaw === null) ? null
      : Math.max(0, smallestPackAbove(gpRaw, pack) - q0);
    R.extra_qty_exceed_revenue_label = 'the smallest orderable quantity above the unchanged '
      + 'offer\'s revenue' + (pack > 1 ? ', rounded up to whole packs of ' + pack : '');
    R.extra_qty_exceed_gp_label = 'the smallest orderable quantity above the unchanged '
      + 'offer\'s gross profit' + (pack > 1 ? ', rounded up to whole packs of ' + pack : '');

    /* ---- tolerable volume loss, against the quantity actually assumed ---- */
    if (p1 > p0) {
      var lr = (revRaw !== null && R.quantity_after)
        ? 100 * (1 - revRaw / R.quantity_after) : null;
      var lg = null;
      if (cost !== null && p1 > cost && R.gp_before !== null && R.quantity_after) {
        lg = gpRaw === null ? null : 100 * (1 - gpRaw / R.quantity_after);
      }
      R.tolerable_loss_revenue_pct = lr === null ? null : round2(lr);
      R.tolerable_loss_gp_pct = lg === null ? null : round2(lg);
      R.tolerable_volume_loss_pct = (lr === null) ? null
        : (lg === null ? round2(lr) : round2(Math.min(lr, lg)));
    }

    /* ---- trade-off flags. Reported, never resolved into one score (FIN-08). */
    if (R.revenue_change > 0 && R.gp_change !== null && R.gp_change < 0) {
      R.flags.push({ code: 'REV_UP_GP_DOWN', severity: 'high',
        text: 'Revenue rises while gross profit falls. This is a trade-off and is not '
            + 'automatically approved.',
        revenue_change: R.revenue_change, gp_change: R.gp_change });
    }
    if (R.gp_change !== null && R.gp_change > 0 && R.revenue_change < 0) {
      R.flags.push({ code: 'GP_UP_REV_DOWN', severity: 'high',
        text: 'Gross profit rises while revenue falls. This is a trade-off and is not '
            + 'automatically approved.',
        revenue_change: R.revenue_change, gp_change: R.gp_change });
    }
    if (scope === 'all' && p1 < p0 && Math.abs(p0 - p1) > 0.0049) {
      R.flags.push({ code: 'DISCOUNT_ON_EXISTING', severity: 'medium',
        text: 'The reduction applies to all eligible volume, so '
            + Math.abs(R.discount_on_existing_volume_eur).toFixed(2)
            + ' EUR of discount is given away on units that were already buying.',
        amount: R.discount_on_existing_volume_eur });
    }
    if (cost !== null && p1 <= cost) {
      R.flags.push({ code: 'PRICE_AT_OR_BELOW_COST', severity: 'high',
        text: 'The proposed price does not exceed the parts cost, so every unit sold reduces '
            + 'gross profit.', amount: null });
    }
    if (R.bridge_reconciles === false) {
      R.flags.push({ code: 'BRIDGE_FAILS', severity: 'high',
        text: 'The revenue, cost and support movement does not reconcile to the reported gross '
            + 'profit change. This result must not be used.', amount: null });
    }

    /* ---- stated conditions ---- */
    if (R.quantity_label !== 'observed history' && R.quantity_label !== 'stated commitment') {
      R.conditional.push("The volume movement is labelled '" + R.quantity_label
        + "'. No elasticity is assumed and this is not a forecast.");
    }
    if (scope === 'incremental') {
      R.conditional.push('Incremental-only pricing keeps existing units at the current price. '
        + 'Movement from another Isuzu product is migration, not new business.');
    }
    if (R.volume_is_observed === false && R.quantity_after === q0) {
      R.conditional.push('The proposed quantity is the recorded quantity. Any increase therefore '
        + 'has to come from a stated commitment, not from this model.');
    }

    R.ok = true;
    R.resolved = true;
    return finalizeResult(R);
  }

  /* --------------------------------------------------------- migration -- */

  /* F07. A move between two Isuzu product lines is priced as two product lines,
     not as a label on one of them. Without the two lines' prices and costs and a
     stated transferred quantity there is no financial result, and v03's
     fabricated zero is never returned. */
  function migrationResult(R, input, x) {
    var mig = input.migration || {};
    var from = mig.from || null, to = mig.to || null;
    var moved = toNumberOrNull(mig.quantity_transferred);
    var fromP = from ? toNumberOrNull(from.price) : null;
    var fromC = from ? toNumberOrNull(from.cost) : null;
    var toP = to ? toNumberOrNull(to.price) : null;
    var toC = to ? toNumberOrNull(to.cost) : null;
    var migrationErrors = [];
    if (!from || !to) migrationErrors.push('Both product lines must be supplied.');
    if (moved === null || moved <= 0) migrationErrors.push('The transferred quantity must be finite and above zero.');
    if (moved !== null && moved > x.quantity_before) {
      migrationErrors.push('The transferred quantity exceeds the source population.');
    }
    if (fromP === null || fromP <= 0 || toP === null || toP <= 0) {
      migrationErrors.push('Both product selling prices must be finite and above zero.');
    }
    if (fromC === null || fromC < 0 || toC === null || toC < 0) {
      migrationErrors.push('Both product costs must be finite and non-negative.');
    }
    if (x.cost === null) {
      migrationErrors.push('The unchanged-offer cost is missing. A missing baseline profit cannot be treated as zero.');
    }
    // The existing record represents one source-product population. A different
    // source price/cost would mix two baselines; a broader range needs its own
    // explicit record rather than silently inheriting this single-part total.
    function sameBasisNumber(a, b) {
      return a !== null && b !== null
        && Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
    }
    if (fromP !== null && !sameBasisNumber(fromP, x.price_before)) {
      migrationErrors.push('The source product price differs from the unchanged-offer price.');
    }
    if (fromC !== null && x.cost !== null && !sameBasisNumber(fromC, x.cost)) {
      migrationErrors.push('The source product cost differs from the unchanged-offer cost.');
    }
    if (x.scope !== 'all') {
      migrationErrors.push('A product migration is not an incremental-volume offer.');
    }
    if (x.quantity_after_supplied && x.quantity_after !== x.quantity_before) {
      migrationErrors.push('This one-for-one migration keeps the total population unchanged; model new or lost volume separately.');
    }
    var complete = migrationErrors.length === 0;
    R.migration_status = complete ? 'modelled' : 'unresolved';

    if (!complete) {
      R.ok = false;
      R.resolved = false;
      R.error = 'A move between two Isuzu product lines is not priced as a single part. Supply the '
        + 'transferred quantity, and the applicable price and parts cost of both the product being '
        + 'left and the product being taken up. Business moved between Genuine and BVP is not new '
        + 'business and is reported separately when it is measured.';
      R.error += ' ' + migrationErrors.join(' ');
      R.errors = migrationErrors.length ? migrationErrors : [R.error];
      R.conditional.push('This alternative names a product migration. No financial result is '
        + 'stated for it until both product lines and the transferred quantity are supplied. The '
        + 'unchanged-offer figures beside it are the baseline, not the effect of the migration.');
      R.flags.push({ code: 'MIGRATION_UNRESOLVED', severity: 'high',
        text: 'The migration is unresolved: no revenue change and no gross profit change are '
            + 'reported. A zero here would be a fabricated answer, not a measured one.',
        amount: null });
      return finalizeResult(R);
    }

    var support = x.support;
    var lostContribution = moved * (fromP - fromC);
    var gainedContribution = moved * (toP - toC);
    var revenueChange = moved * (toP - fromP);
    var costChange = moved * (toC - fromC);

    R.quantity_after = x.quantity_before;
    R.extra_quantity = 0;
    R.revenue_after = R.revenue_before + revenueChange;
    R.revenue_change = revenueChange;
    R.revenue_pct = R.revenue_before ? 100 * revenueChange / R.revenue_before : null;
    R.gp_after = R.gp_before + (gainedContribution - lostContribution) - support;
    R.gp_change = R.gp_after - R.gp_before;
    R.gp_pct = R.gp_before ? 100 * R.gp_change / Math.abs(R.gp_before) : null;
    R.margin_after_pct = R.revenue_after ? 100 * R.gp_after / R.revenue_after : null;
    R.margin_unit_after_pct = null;
    R.margin_pp_change = (R.margin_before_pct === null || R.margin_after_pct === null)
      ? null : R.margin_after_pct - R.margin_before_pct;
    R.bridge_revenue_change = revenueChange;
    R.bridge_cost_change = costChange;
    R.bridge_support_eur = support;
    R.bridge_reconciles = Math.abs((revenueChange - costChange - support) - R.gp_change) < 1e-9;
    R.discount_on_existing_volume_eur = 0;
    R.flags.push({ code: 'MIGRATION_NOT_NEW_BUSINESS', severity: 'high',
      text: 'Volume moved between two Isuzu product lines. The gross profit change is the '
          + 'contribution taken up less the contribution displaced, and it is not new business.',
      amount: R.gp_change });
    R.conditional.push('Modelled on the supplied two-product inputs: ' + fmtNum(moved, 0)
      + ' units moved, at the stated price and parts cost of each line. The transferred quantity '
      + 'is a stated assumption, not a forecast.');
    R.ok = true;
    R.resolved = true;
    return finalizeResult(R);
  }

  /* ----------------------------------------------------------- baseline -- */

  /* The unchanged offer for the same customer, period, quantity and population.
     A recorded amount is never rebuilt by rounding an average price and then
     labelled as recorded history (F04). */
  function baseline(caseObject, opts) {
    opts = opts || {};
    var c = caseObject || {};
    var bd = c.baselineDefined || {};
    var qty = (opts.quantity !== undefined) ? toNumberOrNull(opts.quantity)
      : toNumberOrNull(bd.quantity);
    var observedBilling = toNumberOrNull(bd.observed_billing_eur);
    var price = (opts.price !== undefined) ? round2(toNumberOrNull(opts.price))
      : round2(toNumberOrNull(bd.observed_unit_price));
    var reconstructed = (qty !== null && price !== null) ? qty * price : null;
    var reconciles = (observedBilling !== null && reconstructed !== null)
      ? Math.abs(reconstructed - observedBilling) < 0.005 : null;

    var statement = 'Recorded history for ' + (bd.period || 'the recorded period')
      + '. Not annualised; last year\'s volume is not assumed to recur.';
    if (reconciles === false) {
      statement = 'Forward scenario built on the rounded price ' + price.toFixed(2)
        + ' EUR per unit. It does not reproduce the recorded billing of '
        + observedBilling.toFixed(2) + ' EUR for this period, so it is labelled a rounded '
        + 'scenario and not recorded history.';
    }

    return {
      period: bd.period || 'recorded period',
      quantity: qty,
      price: price,
      quantity_label: bd.quantity_label || 'observed history',
      revenue: reconstructed,
      recorded_billing_eur: observedBilling,
      reconciles_to_recorded: reconciles,
      is_rounded_scenario: reconciles === false,
      onward_quantity: bd.onward_quantity,
      basis_statement: statement
    };
  }

  /* One advertised baseline demands one cost basis across every comparable row
     (F04). The spread is reported rather than asserted. */
  function baselineConsistency(ranked) {
    var values = {}, ids = [];
    (ranked || []).forEach(function (row) {
      if (!row.result || row.result.gp_before === null) return;
      var key = String(row.result.gp_before);
      if (!values[key]) { values[key] = []; ids.push(key); }
      values[key].push(row.alternative.alternative_id);
    });
    return {
      consistent: ids.length <= 1,
      distinct_gross_profit_baselines: ids.length,
      groups: values
    };
  }

  /* ----------------------------------------------- the one cost lookup -- */

  function comparisonCost(payload, caseObject, opts) {
    var offerDate = (opts && opts.offer_effective_date)
      || caseObject.offer_effective_date || null;
    var basis = resolveOfferBasis(payload, offerDate);
    var rec = basis.ok ? costRecord(payload, caseObject.pn, basis.basis_id) : null;
    return {
      basis: basis,
      basis_id: basis.ok ? basis.basis_id : null,
      source: basis.source,
      offer_effective_date: offerDate || null,
      record: rec,
      cost: rec ? rec.cost_eur : null
    };
  }

  /* A basis named on an alternative that differs from the comparison basis is a
     separate assumption. It is reported, not applied silently to the numbers. */
  function noteBasisDifference(result, alternative, comparison) {
    if (!result || !alternative) return;
    var declared = alternative.cost_basis_for_offer;
    if (isBlank(declared) || !comparison.basis_id) return;
    if (String(declared) === String(comparison.basis_id)) return;
    result.conditional.push('This alternative names the ' + declared + ' cost basis, while every '
      + 'row in this comparison is priced on the ' + comparison.basis_id + ' basis ('
      + comparison.source + '). The difference was not applied: a supplier-cost change has to be '
      + 'raised as its own stated assumption so that one unchanged offer is compared with one cost.');
    result.flags.push({ code: 'COST_BASIS_DIFFERENCE', severity: 'medium',
      text: 'A different cost basis is named on this alternative (' + declared + ') and the '
          + 'comparison uses ' + comparison.basis_id + '. Stated, not silently applied.',
      amount: null });
  }

  /* ------------------------------------------------------------ ranking -- */

  function rankAlternatives(caseObject, objective, opts) {
    opts = opts || {};
    var c = caseObject || {};
    var obj = objective || 'revenue';
    var payload = opts.payload || getPayload() || { verifiedCosts: c.costRecords || [] };
    var b = baseline(c, opts);
    var comparison = comparisonCost(payload, c, opts);

    var list = (c.alternatives || []).map(function (alternative, index) {
      var p1 = priceAfter(b.price, alternative.price_delta_pct);
      var q1 = quantityAfter(b.quantity, alternative, opts);
      var r = calculate({
        price_before: b.price, price_after: p1,
        quantity_before: b.quantity, quantity_after: q1,
        scope: alternative.scope,
        support_eur: isBlank(alternative.support_eur) ? 0 : alternative.support_eur,
        cost_eur: comparison.cost,
        cost_basis_id: comparison.basis_id,
        quantity_label: alternative.volume_label,
        kind: alternative.kind,
        migration: alternative.migration,
        pack_size: opts.pack_size !== undefined ? opts.pack_size
          : (alternative.pack_size_units !== undefined ? alternative.pack_size_units : 1),
        evidence_period: b.period,
        offer_effective_date: comparison.offer_effective_date
      });
      noteBasisDifference(r, alternative, comparison);
      return { alternative: alternative, result: r, cost_record: comparison.record,
        price_after: p1, order: index };
    });

    /* Deterministic order (FIN-08): by the selected objective, then by the lowest
       proposed price, then by the alternative id. Revenue and gross profit stay
       two separate objectives and are never collapsed into one invented score. */
    var key = (obj === 'grossProfit') ? 'gp_change' : 'revenue_change';
    list.sort(function (x, y) {
      var xv = x.result.ok ? x.result[key] : null;
      var yv = y.result.ok ? y.result[key] : null;
      if (xv === null && yv === null) return x.order - y.order;
      if (xv === null) return 1;
      if (yv === null) return -1;
      if (yv !== xv) return yv - xv;
      if (x.price_after !== y.price_after) return x.price_after - y.price_after;
      return String(x.alternative.alternative_id)
        .localeCompare(String(y.alternative.alternative_id));
    });

    return {
      baseline: b, ranked: list, objective: obj,
      objective_label: (obj === 'grossProfit') ? 'additional gross profit in euro'
                                               : 'additional ISZE revenue',
      comparison_basis_id: comparison.basis_id,
      comparison_basis_source: comparison.source,
      comparison_cost_resolved: comparison.cost !== null,
      offer_effective_date: comparison.offer_effective_date,
      baseline_consistency: baselineConsistency(list)
    };
  }

  /* Both objectives for one alternative, on identical assumptions and through
     the same volume normalisation as the ranking (F09). An explicit override
     still wins, so this can replay the working scenario. */
  function bothObjectives(caseObject, alternative, opts) {
    opts = opts || {};
    var c = caseObject || {};
    alternative = alternative || {};
    var payload = opts.payload || getPayload() || { verifiedCosts: c.costRecords || [] };
    var b = baseline(c, opts);
    var comparison = comparisonCost(payload, c, opts);

    var p1 = (opts.price_after !== undefined) ? opts.price_after
      : priceAfter(b.price, alternative.price_delta_pct);
    var q1 = quantityAfter(b.quantity, alternative, opts);
    var cost = (opts.cost_eur !== undefined) ? opts.cost_eur : comparison.cost;

    var r = calculate({
      price_before: (opts.price_before !== undefined) ? opts.price_before : b.price,
      price_after: p1,
      quantity_before: (opts.quantity_before !== undefined) ? opts.quantity_before : b.quantity,
      quantity_after: q1,
      scope: (opts.scope !== undefined) ? opts.scope : alternative.scope,
      support_eur: (opts.support_eur !== undefined) ? opts.support_eur
        : (isBlank(alternative.support_eur) ? 0 : alternative.support_eur),
      cost_eur: cost,
      cost_basis_id: comparison.basis_id,
      quantity_label: opts.quantity_label || alternative.volume_label,
      kind: alternative.kind,
      migration: alternative.migration,
      pack_size: opts.pack_size !== undefined ? opts.pack_size
          : (alternative.pack_size_units !== undefined ? alternative.pack_size_units : 1),
      evidence_period: b.period,
      offer_effective_date: comparison.offer_effective_date
    });
    noteBasisDifference(r, alternative, comparison);
    return { baseline: b, result: r, cost_record: comparison.record, price_after: p1,
      comparison_basis_id: comparison.basis_id };
  }

  /* ------------------------------------------------------------ wordings -- */

  function conditionalTest(r) {
    if (!r) return [];
    if (!r.resolved) return r.error ? [r.error] : [];
    var out = [];
    if (r.scope === 'incremental') {
      if (r.price_after < r.price_before) {
        out.push('Only additional units take the reduced price, so the existing units keep both '
          + 'their revenue and their gross profit. The offer needs '
          + fmtNum(r.qty_preserve_gp, 0) + ' units in total to hold gross profit'
          + (r.support_eur ? ' including the ' + fmtNum(r.support_eur, 0) + ' EUR of support to be '
             + 'recovered at ' + fmtNum(r.price_after - r.cost, 2) + ' EUR of contribution per '
             + 'additional unit' : '') + '.');
      } else if (r.price_after > r.price_before) {
        out.push('Only additional units take the higher price, so an increase applies to new '
          + 'volume and not to the existing units.');
      } else {
        out.push(r.support_eur
          ? 'The price is unchanged and ' + fmtNum(r.support_eur, 0) + ' EUR of support is to be '
            + 'recovered, so ' + fmtNum((r.qty_preserve_gp === null ? r.quantity_before
              : r.qty_preserve_gp) - r.quantity_before, 0)
            + ' additional units are required to hold gross profit.'
          : 'The price is unchanged and no support is added, so no volume response is required to '
            + 'hold either measure.');
      }
      return out;
    }
    if (r.price_after < r.price_before) {
      out.push('The customer would have to commit to at least ' + fmtNum(r.qty_preserve_revenue, 0)
        + ' units at ' + fmtNum(r.price_after, 2) + ' EUR to hold revenue'
        + (r.qty_preserve_gp === null ? '' : ', and at least ' + fmtNum(r.qty_preserve_gp, 0)
           + ' units to hold gross profit')
        + '. A commitment between the two holds revenue but loses gross profit.');
    } else if (r.price_after > r.price_before) {
      out.push('Volume may fall by up to ' + fmtPct(r.tolerable_loss_revenue_pct)
        + ' before revenue falls below the unchanged offer'
        + (r.tolerable_loss_gp_pct === null ? '' : ', and by up to '
           + fmtPct(r.tolerable_loss_gp_pct) + ' before gross profit does')
        + '. The binding limit is ' + fmtPct(r.tolerable_volume_loss_pct) + '.');
    } else if (r.support_eur) {
      out.push('The price is unchanged and ' + fmtNum(r.support_eur, 0) + ' EUR of support is '
        + 'added, so the unchanged volume does not by itself hold gross profit.');
    } else {
      out.push('The price is unchanged and no support is added, so no volume response is required '
        + 'to hold either measure.');
    }
    return out;
  }

  /* ===========================================================================
     Compatibility shim for the supplied review's distributor-strip checks.

     R25 and R26 in the supplied suite call strip/audit on an engine result. This
     is deliberately NOT the production control: the member brief is built from a
     recipient-specific allowlist in src/data/export.js (F08, a separate owner),
     which is a stronger rule than deleting names from a finished record. The shim
     exists so the supplied assertions can be evaluated against this module
     without being deleted. It removes the restricted leaf names and keeps the
     structure, and it detects a nested restricted field.
     =========================================================================== */
  var RESTRICTED_NAMES = ['cost', 'cost_eur', 'parts_cost', 'purchasecost', 'purchase_price',
    'unitcost', 'landedcost', 'grossprofit', 'grossmargin', 'gp_before', 'gp_after', 'gp_change',
    'gp_pct', 'margin_before', 'margin_after', 'margin_pp', 'margin_unit', 'verifiedcosts',
    'cost_bases', 'cost_basis', 'costrecord', 'cost_record', 'source_discount', 'base_price',
    'jpy_per_eur', 'markup', 'fob_eur', 'contribution', 'bridge_cost', 'bridge_support'];

  function isRestrictedName(key) {
    var k = String(key).toLowerCase().replace(/[^a-z0-9_]/g, '');
    for (var i = 0; i < RESTRICTED_NAMES.length; i++) {
      var f = RESTRICTED_NAMES[i].replace(/[^a-z0-9_]/g, '');
      if (f && k.indexOf(f) >= 0) return RESTRICTED_NAMES[i];
    }
    return null;
  }

  function strip(obj, depth) {
    depth = depth || 0;
    if (depth > 12) return null;
    if (Array.isArray(obj)) return obj.map(function (x) { return strip(x, depth + 1); });
    if (obj && typeof obj === 'object') {
      var out = {};
      Object.keys(obj).forEach(function (k) {
        if (isRestrictedName(k)) return;
        out[k] = strip(obj[k], depth + 1);
      });
      return out;
    }
    return obj;
  }

  function audit(obj) {
    var findings = [];
    (function walk(node, path) {
      if (Array.isArray(node)) {
        node.forEach(function (v, i) { walk(v, path + '[' + i + ']'); });
        return;
      }
      if (node && typeof node === 'object') {
        Object.keys(node).forEach(function (k) {
          var hit = isRestrictedName(k);
          if (hit && findings.indexOf(hit) < 0) {
            findings.push(hit + ' (key ' + path + '.' + k + ')');
          }
          walk(node[k], path + '.' + k);
        });
      }
    })(obj, '');
    return findings;
  }

  /* ----------------------------------------------------------------- API -- */

  function v03meta() { return (getPayload() && getPayload().meta) || {}; }
  function v03bases() { return v03meta().costBases || []; }
  function v03defaultBasis() { return v03meta().defaultForwardBasis || null; }
  function v03basisById(id) { return basisById(getPayload(), id); }

  var API = {
    CONTRACT_VERSION: 1,

    /* payload binding */
    setPayload: setPayload, configure: setPayload, getPayload: getPayload,

    /* inputs, dates, costs */
    validateScenario: validateScenario,
    basisWindow: basisWindow,
    basisById: function (payload, id) {
      return isPayloadLike(payload) ? basisById(payload, id) : basisById(getPayload(), payload);
    },
    resolveOfferBasis: resolveOfferBasis,
    basisForDate: basisForDate,
    costForDate: costForDate,
    costRecord: costRecord,

    /* price and quantity normalisation */
    priceAfter: priceAfter,
    quantityAfter: quantityAfter,
    roundToPack: roundToPack,
    smallestPackAbove: smallestPackAbove,

    /* the one calculation, and the views over it */
    calculate: calculate,
    baseline: baseline,
    baselineConsistency: baselineConsistency,
    rankAlternatives: rankAlternatives,
    bothObjectives: bothObjectives,
    conditionalTest: conditionalTest,

    /* wording and arithmetic helpers */
    fmtNum: fmtNum, fmtPct: fmtPct, round2: round2, money: money, change: change,
    isFiniteNumber: isFiniteNumber,

    /* recipient strip shim (see the note above) */
    strip: strip, audit: audit,

    /* v03 names, kept so the existing callers keep working */
    v03run: calculate,
    v03rank: rankAlternatives,
    v03both: bothObjectives,
    v03baseline: baseline,
    v03conditionalTest: conditionalTest,
    v03costForDate: costForDate,
    v03costRecord: costRecord,
    v03priceAfter: priceAfter,
    v03quantityAfter: quantityAfter,
    v03fmtNum: fmtNum,
    v03fmtPct: fmtPct,
    v03round2: round2,
    v03numOr: numOr,
    v03meta: v03meta,
    v03bases: v03bases,
    v03defaultBasis: v03defaultBasis,
    v03basisById: v03basisById,
    v03strip: strip,
    v03audit: audit
  };

  root.AIMEngine = API;
  root.PricingEngine = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
