/* AIM range economics prototype. Internal calculations only; no approval or exports.
 * One distributor, one service family, one period and one forward cost basis.
 * All volume uses the stated proposal price. Transfers are one-for-one service units.
 * Prices/costs/support are exact cents; quantities are whole declared packs.
 * No elasticity, competitor-price inference, fleet forecast or automatic recovery rate.
 */
(function (root) {
  'use strict';
  const VERSION = 'range-prototype-1';
  const MAX = Number.MAX_SAFE_INTEGER;
  class InputError extends Error {
    constructor(code, path, message) { super(message); this.code = code; this.path = path; }
  }
  const fail = (code, path, message) => { throw new InputError(code, path, message); };
  const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  function shape(obj, required, optional, path) {
    if (obj === null || typeof obj !== 'object' || Array.isArray(obj))
      fail('INVALID_OBJECT', path, 'A named object is required.');
    const allowed = new Set(required.concat(optional || []));
    for (const key of required) if (!own(obj, key))
      fail('MISSING_INPUT', path + '.' + key, 'This input must be supplied explicitly.');
    for (const key of Object.keys(obj)) if (!allowed.has(key))
      fail('UNSUPPORTED_INPUT', path + '.' + key, 'This input is not supported by this prototype.');
  }
  function text(value, path) {
    if (typeof value !== 'string' || !value.trim() || value.trim() !== value)
      fail('INVALID_TEXT', path, 'A nonblank text value without outer whitespace is required.');
    return value;
  }
  function integer(value, path, minimum = 0) {
    if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < minimum)
      fail('INVALID_QUANTITY', path, 'A nonnegative safe whole number is required.');
    return value;
  }
  function cents(value, path, minimum = 0) {
    if (typeof value !== 'number' || !Number.isFinite(value))
      fail('INVALID_MONEY', path, 'An explicit finite numeric EUR amount is required.');
    const amount = Math.round(value * 100);
    if (!Number.isSafeInteger(amount) || amount / 100 !== value || amount < minimum)
      fail('INVALID_MONEY', path, 'Use an amount with at most two decimal places within the exact range.');
    return amount;
  }
  function safe(value, path) {
    if (!Number.isSafeInteger(value))
      fail('ARITHMETIC_RANGE', path, 'The calculation exceeds exact integer-cent or quantity arithmetic.');
    return value;
  }
  const add = (a, b, path) => safe(a + b, path);
  const mul = (a, b, path) => safe(a * b, path);
  const sum = (values, path) => values.reduce((a, b) => add(a, b, path), 0);
  const eur = value => value / 100;
  function date(value, path) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value))
      fail('INVALID_DATE', path, 'Use a real ISO calendar date.');
    const d = new Date(value + 'T00:00:00Z');
    if (!Number.isFinite(d.getTime()) || d.toISOString().slice(0, 10) !== value)
      fail('INVALID_DATE', path, 'Use a real ISO calendar date.');
    return d.getTime();
  }
  function period(obj, path) {
    shape(obj, ['from', 'to'], [], path);
    const from = date(obj.from, path + '.from'), to = date(obj.to, path + '.to');
    if (to < from) fail('INVALID_PERIOD', path, 'The end must not precede the start.');
    return (to - from) / 86400000 + 1;
  }
  function list(value, path, nonempty = false) {
    if (!Array.isArray(value) || (nonempty && !value.length))
      fail('INVALID_ARRAY', path, 'An explicit array is required.');
    return value;
  }
  function pack(quantity, size, path) {
    if (quantity % size !== 0)
      fail('PACK_MISMATCH', path, 'The quantity must be a whole multiple of its declared pack size.');
  }
  function parse(input) {
    shape(input, ['schema_version', 'scenario_id', 'title', 'context', 'scope', 'lines', 'transfers', 'support_eur'], [], 'scenario');
    if (input.schema_version !== 1) fail('VERSION', 'schema_version', 'Only schema version 1 is supported.');
    text(input.scenario_id, 'scenario_id'); text(input.title, 'title');
    if (input.scope !== 'all_volume') fail('UNSUPPORTED_SCOPE', 'scope', 'This range comparison supports all-volume prices only.');
    const c = input.context;
    shape(c, ['synthetic', 'as_of', 'distributor_id', 'family', 'currency', 'price_basis',
      'reference_period', 'scenario_period', 'baseline_volume_basis', 'source_ref', 'cost_basis', 'fleet'], [], 'context');
    if (typeof c.synthetic !== 'boolean') fail('SYNTHETIC_DECLARATION', 'context.synthetic', 'Declare whether the case is synthetic.');
    date(c.as_of, 'context.as_of'); text(c.distributor_id, 'context.distributor_id');
    if (['uk', 'united kingdom', 'israel'].includes(c.distributor_id.toLowerCase()))
      fail('AMBIGUOUS_DISTRIBUTOR', 'context.distributor_id', 'Name the distributor, not a blended UK or Israel population.');
    text(c.family, 'context.family'); text(c.source_ref, 'context.source_ref');
    if (c.currency !== 'EUR' || c.price_basis !== 'ISZE_to_distributor_net_ex_VAT')
      fail('PRICE_BASIS', 'context.price_basis', 'Use ISZE-to-distributor net selling prices, excluding VAT, in EUR.');
    if (c.baseline_volume_basis !== 'replayed_reference_quantities')
      fail('BASELINE_BASIS', 'context.baseline_volume_basis', 'Declare reference quantities replayed as the unchanged-offer assumption.');
    const referenceDays = period(c.reference_period, 'context.reference_period');
    const scenarioDays = period(c.scenario_period, 'context.scenario_period');
    if (referenceDays !== scenarioDays)
      fail('PERIOD_LENGTH_MISMATCH', 'context.scenario_period', 'Unequal-length periods cannot be compared without a separately justified quantity basis.');
    if (c.reference_period.to > c.as_of)
      fail('FUTURE_REFERENCE', 'context.reference_period', 'Historical reference quantities cannot end after the source as-of date.');
    const cb = c.cost_basis;
    shape(cb, ['id', 'source_ref', 'valid_from', 'valid_to'], [], 'context.cost_basis');
    text(cb.id, 'context.cost_basis.id'); text(cb.source_ref, 'context.cost_basis.source_ref');
    period({from: cb.valid_from, to: cb.valid_to}, 'context.cost_basis');
    if (cb.valid_from > c.scenario_period.from || cb.valid_to < c.scenario_period.to)
      fail('COST_PERIOD_UNCOVERED', 'context.cost_basis', 'One stated cost basis must cover the whole scenario period.');
    shape(c.fleet, ['vehicles', 'as_of', 'basis', 'source_ref', 'description'], [], 'context.fleet');
    integer(c.fleet.vehicles, 'context.fleet.vehicles', 1); date(c.fleet.as_of, 'context.fleet.as_of');
    text(c.fleet.source_ref, 'context.fleet.source_ref'); text(c.fleet.description, 'context.fleet.description');
    if (c.fleet.basis !== 'historical_snapshot' || c.fleet.as_of > c.as_of)
      fail('FLEET_BASIS', 'context.fleet', 'Supply historical fleet context, not a future fleet forecast.');
    const lines = list(input.lines, 'lines', true).map((line, i) => {
      const path = 'lines[' + i + ']';
      shape(line, ['id', 'tier', 'unit_basis', 'pack_size', 'baseline_quantity', 'baseline_net_price_eur',
        'scenario_net_price_eur', 'unit_cost_eur', 'lost_quantity', 'recovered_quantity'], [], path);
      text(line.id, path + '.id'); text(line.unit_basis, path + '.unit_basis');
      if (!['Genuine', 'BVP'].includes(line.tier)) fail('TIER', path + '.tier', 'Use Genuine or BVP.');
      const size = integer(line.pack_size, path + '.pack_size', 1);
      const q = integer(line.baseline_quantity, path + '.baseline_quantity');
      const lost = integer(line.lost_quantity, path + '.lost_quantity');
      const recovered = integer(line.recovered_quantity, path + '.recovered_quantity');
      pack(q, size, path + '.baseline_quantity'); pack(lost, size, path + '.lost_quantity');
      pack(recovered, size, path + '.recovered_quantity');
      return {id: line.id, tier: line.tier, unit_basis: line.unit_basis, size, q, lost, recovered,
        p0: cents(line.baseline_net_price_eur, path + '.baseline_net_price_eur', 1),
        p1: cents(line.scenario_net_price_eur, path + '.scenario_net_price_eur', 1),
        cost: cents(line.unit_cost_eur, path + '.unit_cost_eur'), incoming: 0, outgoing: 0};
    });
    const byId = new Map();
    for (const line of lines) {
      if (byId.has(line.id)) fail('DUPLICATE_LINE', 'lines', 'Each product line must be unique.');
      byId.set(line.id, line);
    }
    if (new Set(lines.map(x => x.unit_basis)).size !== 1)
      fail('MIXED_UNITS', 'lines', 'Use one declared service-unit basis; kits and individual pieces are not interchangeable.');
    const pairs = new Set();
    const transfers = list(input.transfers, 'transfers').map((t, i) => {
      const path = 'transfers[' + i + ']';
      shape(t, ['from_line_id', 'to_line_id', 'quantity', 'equivalence_basis', 'equivalence_ref'], [], path);
      text(t.from_line_id, path + '.from_line_id'); text(t.to_line_id, path + '.to_line_id');
      text(t.equivalence_ref, path + '.equivalence_ref');
      const from = byId.get(t.from_line_id), to = byId.get(t.to_line_id);
      if (!from || !to || from === to)
        fail('INVALID_TRANSFER', path, 'A transfer needs two different declared product lines.');
      if (t.equivalence_basis !== 'documented_one_for_one_service_unit')
        fail('EQUIVALENCE_REQUIRED', path, 'Declare the documented one-for-one service-unit basis; no fitment is inferred.');
      const pair = JSON.stringify([from.id, to.id]);
      if (pairs.has(pair)) fail('DUPLICATE_TRANSFER', path, 'Combine repeated movements into one explicit transfer.');
      pairs.add(pair);
      const q = integer(t.quantity, path + '.quantity', 1);
      pack(q, from.size, path + '.quantity'); pack(q, to.size, path + '.quantity');
      from.outgoing = add(from.outgoing, q, path); to.incoming = add(to.incoming, q, path);
      return {from, to, q};
    });
    for (const line of lines) {
      if (line.incoming && line.outgoing)
        fail('TRANSFER_CHAIN', 'lines.' + line.id, 'Incoming or recovered business cannot fund another transfer in the same scenario.');
      if (add(line.lost, line.outgoing, line.id) > line.q)
        fail('SOURCE_VOLUME_EXCEEDED', 'lines.' + line.id, 'Losses plus transfers exceed the starting business.');
      line.after = sum([line.q, -line.lost, -line.outgoing, line.incoming, line.recovered], line.id);
      pack(line.after, line.size, line.id);
    }
    if (sum(lines.map(x => x.q), 'baseline_quantity') <= 0)
      fail('NO_BASELINE', 'lines', 'At least one starting quantity is required for this comparison.');
    return {input, c, lines, byId, transfers, support: cents(input.support_eur, 'support_eur')};
  }
  function core(s) {
    const rows = s.lines.map(l => {
      const r0 = mul(l.q, l.p0, l.id), r1 = mul(l.after, l.p1, l.id);
      const c0 = mul(l.q, l.cost, l.id), c1 = mul(l.after, l.cost, l.id);
      const g0 = add(r0, -c0, l.id), g1 = add(r1, -c1, l.id);
      return {l, r0, r1, c0, c1, g0, g1};
    });
    const total = key => sum(rows.map(r => r[key]), key);
    const r0 = total('r0'), r1 = total('r1'), c0 = total('c0'), c1 = total('c1');
    const g0 = add(r0, -c0, 'profit_before');
    const g1 = sum([r1, -c1, -s.support], 'profit_after');
    const dr = add(r1, -r0, 'revenue_change'), dg = add(g1, -g0, 'profit_change');
    const price = sum(s.lines.map(l => mul(l.q, l.p1 - l.p0, l.id)), 'price_effect');
    const lostRevenue = -sum(s.lines.map(l => mul(l.lost, l.p1, l.id)), 'lost_revenue');
    const lostProfit = -sum(s.lines.map(l => mul(l.lost, l.p1 - l.cost, l.id)), 'lost_profit');
    const recoveredRevenue = sum(s.lines.map(l => mul(l.recovered, l.p1, l.id)), 'recovered_revenue');
    const recoveredProfit = sum(s.lines.map(l => mul(l.recovered, l.p1 - l.cost, l.id)), 'recovered_profit');
    const transferRevenue = sum(s.transfers.map(t => mul(t.q, t.to.p1 - t.from.p1, 'transfer')), 'transfer_revenue');
    const transferProfit = sum(s.transfers.map(t => mul(t.q,
      (t.to.p1 - t.to.cost) - (t.from.p1 - t.from.cost), 'transfer')), 'transfer_profit');
    const revenueBridge = sum([price, lostRevenue, transferRevenue, recoveredRevenue], 'revenue_bridge');
    const profitBridge = sum([price, lostProfit, transferProfit, recoveredProfit, -s.support], 'profit_bridge');
    if (revenueBridge !== dr || profitBridge !== dg)
      fail('RECONCILIATION', 'bridge', 'The independent movement calculation does not reconcile.');
    return {rows, r0, r1, c0, c1, g0, g1, dr, dg, price, lostRevenue, lostProfit,
      recoveredRevenue, recoveredProfit, transferRevenue, transferProfit};
  }
  function refusal(err) {
    if (!(err instanceof InputError)) throw err;
    return {ok: false, version: VERSION, status: 'refused', error: {code: err.code, path: err.path, message: err.message},
      baseline: null, proposal: null, change: null, approval: 'not_evaluated'};
  }
  function attempt(fn) { try { return fn(); } catch (err) { return refusal(err); } }
  function report(s, a) {
    const amount = (revenue, cost, profit, support) => ({revenue_eur: eur(revenue),
      parts_cost_eur: eur(cost), support_eur: eur(support), gross_profit_eur: eur(profit),
      gross_margin_pct: revenue === 0 ? null : 100 * profit / revenue});
    const bridge = (lost, transfers, recovered, support) => ({existing_price_effect_eur: eur(a.price),
      lost_business_effect_eur: eur(lost), internal_transfer_effect_eur: eur(transfers),
      assumed_recovery_effect_eur: eur(recovered), support_effect_eur: eur(support),
      reconciles_exactly_in_cents: true});
    return {ok: true, version: VERSION, scenario_id: s.input.scenario_id, title: s.input.title,
      status: 'conditional_calculation', synthetic: s.c.synthetic,
      context: JSON.parse(JSON.stringify(s.c)),
      baseline: amount(a.r0, a.c0, a.g0, 0), proposal: amount(a.r1, a.c1, a.g1, s.support),
      change: {revenue_eur: eur(a.dr), gross_profit_eur: eur(a.dg),
        revenue_nonnegative: a.dr >= 0, gross_profit_nonnegative: a.dg >= 0,
        both_nonnegative: a.dr >= 0 && a.dg >= 0},
      revenue_bridge: bridge(a.lostRevenue, a.transferRevenue, a.recoveredRevenue, 0),
      profit_bridge: bridge(a.lostProfit, a.transferProfit, a.recoveredProfit, -s.support),
      lines: a.rows.map(({l, r0, r1, g0, g1}) => ({id: l.id, tier: l.tier,
        baseline_quantity: l.q, lost_quantity: l.lost, transferred_out: l.outgoing,
        transferred_in: l.incoming, assumed_recovered_quantity: l.recovered, scenario_quantity: l.after,
        baseline_revenue_eur: eur(r0), scenario_revenue_eur: eur(r1),
        baseline_contribution_eur: eur(g0), scenario_contribution_before_support_eur: eur(g1)})),
      quantity_check: {baseline: sum(s.lines.map(l => l.q), 'quantity'),
        scenario: sum(s.lines.map(l => l.after), 'quantity'),
        assumed_recovered: sum(s.lines.map(l => l.recovered), 'quantity'),
        assumed_lost: sum(s.lines.map(l => l.lost), 'quantity'),
        internally_transferred: sum(s.transfers.map(t => t.q), 'quantity'),
        transfers_are_new_business: false},
      historical_fleet_context: {vehicles: s.c.fleet.vehicles, as_of: s.c.fleet.as_of,
        scenario_revenue_change_per_historical_vehicle_eur: eur(a.dr) / s.c.fleet.vehicles,
        scenario_profit_change_per_historical_vehicle_eur: eur(a.dg) / s.c.fleet.vehicles,
        is_scenario_fleet_forecast: false},
      approval: 'not_evaluated', price_causality: 'not_established',
      cautions: ['This is a conditional calculation, not measured demand or a recovery forecast.',
        'The unchanged offer replays the reference quantities using the same forward cost basis as the proposal; it is not historical reported profit.',
        'ISZE-to-distributor purchasing does not establish end-customer demand.',
        'The bridge reprices starting quantities before losses, transfers and recoveries; it is an arithmetic decomposition, not causal evidence.',
        'Recovery and loss quantities are supplied assumptions, not inferred from competitor offers or service-demand gaps.',
        'Declared source references and service equivalence are not verified by this module.',
        'Support is deducted once at range level, not allocated to product lines.',
        'Internal output includes costs and profit. Do not send it to distributors or connect it to a shared export without an approved audience-specific implementation.']};
  }
  function evaluateRange(input) { return attempt(() => { const s = parse(input); return report(s, core(s)); }); }
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
    return JSON.stringify(value);
  }
  function signature(s) {
    return canonical({context: s.c, scope: s.input.scope, lines: s.lines.map(l => ({id:l.id,
      tier:l.tier, unit_basis:l.unit_basis, size:l.size, q:l.q, p0:l.p0, cost:l.cost}))
      .sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0)});
  }
  function compareRanges(inputs, objective) {
    return attempt(() => {
      list(inputs, 'scenarios', true);
      if (!['revenue', 'gross_profit'].includes(objective))
        fail('OBJECTIVE', 'objective', 'Choose revenue or gross_profit explicitly; there is no combined score.');
      const states = inputs.map(parse), seen = new Set(), base = signature(states[0]);
      for (const s of states) {
        if (seen.has(s.input.scenario_id)) fail('DUPLICATE_SCENARIO', 'scenarios', 'Scenario identifiers must be unique.');
        seen.add(s.input.scenario_id);
        if (signature(s) !== base)
          fail('INCOMPARABLE_SCENARIOS', 'scenarios', 'Distributor, periods, source basis, fleet context, starting lines, prices and costs must match.');
      }
      const rows = states.map(s => report(s, core(s)));
      const key = objective === 'revenue' ? 'revenue_eur' : 'gross_profit_eur';
      rows.sort((a,b) => b.change[key] - a.change[key] || (a.scenario_id < b.scenario_id ? -1 : a.scenario_id > b.scenario_id ? 1 : 0));
      return {ok:true, version:VERSION, objective, status:'conditional_comparison', rows,
        recommended_scenario_id:null, approval:'not_evaluated'};
    });
  }
  function needed(deficit, contribution) {
    return deficit <= 0 ? 0n : (BigInt(deficit) + BigInt(contribution) - 1n) / BigInt(contribution);
  }
  function wholeNumber(value, path) {
    if (value < 0n || value > BigInt(MAX)) fail('ARITHMETIC_RANGE', path, 'The required quantity exceeds exact arithmetic.');
    return Number(value);
  }
  function recoveryThreshold(input, options) {
    return attempt(() => {
      shape(options, ['line_id', 'maximum_additional_quantity'], [], 'options');
      text(options.line_id, 'options.line_id');
      if (options.maximum_additional_quantity !== null)
        integer(options.maximum_additional_quantity, 'options.maximum_additional_quantity');
      const s = parse(input), a = core(s), l = s.byId.get(options.line_id);
      if (!l) fail('UNKNOWN_LINE', 'options.line_id', 'Select an existing product line.');
      let lower = needed(-a.dr, l.p1), upper = null;
      const contribution = l.p1 - l.cost;
      let impossibleReason = null;
      if (contribution > 0) lower = lower > needed(-a.dg, contribution) ? lower : needed(-a.dg, contribution);
      else if (a.dg < 0) impossibleReason = 'Additional units on this line cannot restore gross profit because their contribution is not positive.';
      else if (contribution < 0) upper = BigInt(a.dg) / BigInt(-contribution);
      if (options.maximum_additional_quantity !== null) {
        const cap = BigInt(options.maximum_additional_quantity);
        upper = upper === null || cap < upper ? cap : upper;
      }
      const size = BigInt(l.size); lower = ((lower + size - 1n) / size) * size;
      if (upper !== null) upper = (upper / size) * size;
      if (upper !== null && lower > upper) impossibleReason = 'No whole-pack quantity preserves both objectives within the stated limits.';
      const common = {ok:true, version:VERSION, status: impossibleReason ? 'not_attainable' : 'conditional_threshold',
        scenario_id:input.scenario_id, line_id:l.id, pack_size:l.size,
        additional_recovery_cap:options.maximum_additional_quantity,
        market_capacity_verified:false, is_demand_forecast:false, approval:'not_evaluated'};
      if (impossibleReason) return {...common, minimum_additional_quantity:null,
        maximum_additional_quantity:null, result_at_minimum:null, reason:impossibleReason};
      const minimum = wholeNumber(lower, 'threshold');
      const maximum = upper === null ? null : wholeNumber(upper, 'threshold');
      const changed = JSON.parse(JSON.stringify(input));
      changed.lines.find(x => x.id === l.id).recovered_quantity = add(l.recovered, minimum, 'recovery_threshold');
      const replay = evaluateRange(changed);
      if (!replay.ok) fail(replay.error.code, replay.error.path, replay.error.message);
      if (!replay.change.both_nonnegative) fail('THRESHOLD_REPLAY', 'threshold', 'The threshold failed its forward calculation.');
      return {...common, minimum_additional_quantity:minimum, maximum_additional_quantity:maximum,
        total_assumed_recovered_quantity_on_line:add(l.recovered, minimum, 'recovery_threshold'),
        result_at_minimum:replay.change,
        boundary_verified_by_forward_calculation:true,
        note:'All other quantities, prices, costs, transfers and support are held fixed. A null maximum means no finite mathematical upper bound, not unlimited market demand.'};
    });
  }
  function recoverySensitivity(input, options) {
    return attempt(() => {
      shape(options, ['line_id', 'additional_quantities'], [], 'options');
      text(options.line_id, 'options.line_id'); list(options.additional_quantities, 'options.additional_quantities', true);
      const s = parse(input), l = s.byId.get(options.line_id);
      if (!l) fail('UNKNOWN_LINE', 'options.line_id', 'Select an existing product line.');
      const seen = new Set();
      const rows = options.additional_quantities.map(q => {
        integer(q, 'options.additional_quantities'); pack(q, l.size, 'options.additional_quantities');
        if (seen.has(q)) fail('DUPLICATE_SENSITIVITY', 'options.additional_quantities', 'Each additional quantity must be unique.');
        seen.add(q);
        const changed = JSON.parse(JSON.stringify(input));
        changed.lines.find(x => x.id === l.id).recovered_quantity = add(l.recovered, q, 'sensitivity');
        const r = evaluateRange(changed);
        if (!r.ok) fail(r.error.code, r.error.path, r.error.message);
        return {additional_assumed_recovered_quantity:q, change:r.change, proposal:r.proposal};
      });
      return {ok:true, version:VERSION, scenario_id:input.scenario_id, line_id:l.id,
        status:'explicit_assumption_sensitivity', is_demand_forecast:false, rows, approval:'not_evaluated'};
    });
  }
  const api = Object.freeze({VERSION, evaluateRange, compareRanges, recoveryThreshold, recoverySensitivity});
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AIMRangeEngine = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
