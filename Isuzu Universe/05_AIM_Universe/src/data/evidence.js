/* ===========================================================================
   Evidence model: references, periods, price levels and part relationships
   (DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07; MARKET-01 - MARKET-06).

   What was wrong in v0.3
     A dated competitor listing, an observed billing average and a list price
     were all described as "a price". A pair of part numbers was described as
     "related" without saying whether that meant a catalogue pairing, a
     supersession or an approved fitment. Billing lines that carried no part
     number were counted as rows but dropped from every comparison. There was no
     record of which import produced which figure, so a correction could not be
     traced and a re-import could double a quantity.

   What this does
     - One evidence reference in the shape the frozen contract already declares
       (reference_id, kind, title, period, source_file, source_pointer, status,
       basis, restricted). A reference with no period says so; it does not borrow
       one from a neighbour.
     - Three different price levels are named and never added together: a list
       price, an observed billing average and a competitor's advertised price.
     - A comparison is refused unless the period, the sales stage and the unit
       agree. These are checked before the arithmetic, not after it.
     - Billing that cannot be attributed to a part or an entity is reconciled and
       the remainder is left visible with its size in euro and in rows. Nothing
       is dropped to make a table look complete.
     - Repeated imports are idempotent: a keyed re-import replaces its own record,
       a correction replaces its declared predecessor, and a conservation check
       reports what moved. Nothing is multiplied by being imported twice.
     - A stage failure leaves the last accepted view in place and reports that
       the refresh did not complete, rather than showing a half-refreshed state.
   =========================================================================== */
(function (root) {
  'use strict';

  var manifest = (typeof module === 'object' && module.exports)
    ? require('./manifest.js') : root.AIMManifest;

  var SEP = '\u001f';

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
  function normName(v) { return String(v === null || v === undefined ? '' : v).trim(); }

  /* --------------------------------------------------------- the reference -- */

  /* One shape, the same nine fields the frozen Scenario contract already names.
     Nothing here is a new field, so a reference travels with the scenario. */
  function reference(input) {
    input = input || {};
    var period = describePeriod(input);
    return {
      reference_id: input.reference_id || null,
      kind: input.kind || null,
      title: input.title || null,
      period: period.value,
      source_file: input.source_file || input.file || null,
      source_pointer: input.source_pointer || input.pointer || null,
      status: input.status || 'declared, not independently approved',
      basis: input.basis || null,
      restricted: input.restricted === true,
      /* Beyond the frozen nine, always present, all of them about what is
         missing rather than about a value. */
      period_state: period.state,
      period_source: period.source,
      period_statement: period.statement,
      entity: manifest.normaliseEntity(input.entity),
      entity_label: input.entity ? manifest.entityLabel(input.entity) : null,
      sales_stage: input.sales_stage || null,
      unit: input.unit || null,
      as_of: input.as_of || null
    };
  }

  /* A period is declared, partial, or undeclared. Undeclared stays undeclared. */
  function describePeriod(input) {
    input = input || {};
    var declared = input.period !== undefined ? input.period : input.period_declared;
    if (!isBlank(declared)) {
      return { value: declared, state: 'declared', source: input.period_source || 'declared on the record',
        statement: 'The record states its own period.' };
    }
    var partial = input.period_partial;
    if (!isBlank(partial)) {
      return { value: partial, state: 'partial', source: input.period_source || 'partly declared',
        statement: 'Only part of the period is stated. The rest is unresolved and is not inferred.' };
    }
    return {
      value: null, state: 'undeclared', source: null,
      statement: 'No period is carried on this record. A missing period is not zero activity and '
        + 'none has been inferred from similar-looking values.'
    };
  }

  function periodOf(record) {
    return describePeriod(record || {});
  }

  /* ----------------------------------------------------------- price levels -- */

  var PRICE_LEVELS = {
    list: {
      level: 'list',
      label: 'List price',
      definition: 'a published or carried price list figure for a part',
      is_customer_specific: false,
      statement: 'A list price is a published figure. It is not what a customer was billed.'
    },
    observed_billing_average: {
      level: 'observed_billing_average',
      label: 'Observed billing average',
      definition: 'recorded billed euro divided by recorded billed quantity for a stated period',
      is_customer_specific: true,
      statement: 'An observed billing average is what was actually billed in a period, after any '
        + 'discount applied at the time. It is not a list price and it is not a competitor price.'
    },
    competitor_advertised: {
      level: 'competitor_advertised',
      label: 'Competitor advertised price',
      definition: 'a dated public listing by another seller',
      is_customer_specific: false,
      statement: 'A competitor advertised price is a dated observation by another seller. It is '
        + 'evidence, not truth, and its kit contents and tax basis may not be stated.'
    },
    reference_dealer: {
      level: 'reference_dealer',
      label: 'Reference dealer price',
      definition: 'a derived dealer-facing reference used for comparison only',
      is_customer_specific: false,
      statement: 'A reference dealer price is a comparison convention, not an actual transaction.'
    },
    supplier_cost: {
      level: 'supplier_cost',
      label: 'Parts purchase cost',
      definition: 'the supplier purchase cost of the part, restricted',
      is_customer_specific: false,
      statement: 'A parts purchase cost is what ISZE pays. It is not a selling price at any level.'
    }
  };

  function priceLevel(levelId) {
    return PRICE_LEVELS[levelId] || {
      level: levelId || null, label: 'Unnamed price level', definition: null,
      is_customer_specific: null,
      statement: 'This value does not declare which price level it belongs to, so it may not be '
        + 'compared with any other figure.'
    };
  }

  /* Three different things, never added. This is the check. */
  function assertSamePriceLevel(a, b) {
    var la = priceLevel(a && (a.price_level || a.level)).level;
    var lb = priceLevel(b && (b.price_level || b.level)).level;
    if (!la || !lb) {
      return { ok: false, comparable: false,
        statement: 'At least one value does not declare its price level, so the two cannot be '
          + 'compared or combined.' };
    }
    if (la !== lb) {
      return { ok: false, comparable: false,
        statement: 'A ' + priceLevel(la).label.toLowerCase() + ' and a '
          + priceLevel(lb).label.toLowerCase() + ' are different commercial price levels. They are '
          + 'shown side by side and never added together or averaged into one number.' };
    }
    return { ok: true, comparable: true, level: la,
      statement: 'Both values are on the same price level (' + la + ').' };
  }

  /* ------------------------------------------------------------ comparison -- */

  /* Period, sales stage and unit must agree before a comparison is allowed.
     A price computed on one sales stage or one unit is not comparable with
     another, and the refusal states which of the three disagreed. */
  function comparability(a, b) {
    a = a || {}; b = b || {};
    var findings = [];

    var pa = periodOf(a), pb = periodOf(b);
    if (pa.state === 'undeclared' || pb.state === 'undeclared') {
      findings.push('A period is not declared, so the two figures cannot be aligned'
        + (pa.state === 'undeclared' ? ' (the first carries none)' : '')
        + (pb.state === 'undeclared' ? ' (the second carries none)' : '') + '.');
    } else if (a.period !== b.period) {
      findings.push('Different periods: ' + pa.value + ' and ' + pb.value + '.');
    }

    if (normName(a.sales_stage).toLowerCase() !== normName(b.sales_stage).toLowerCase()) {
      findings.push('Different sales stages: ' + (a.sales_stage || 'not stated') + ' and '
        + (b.sales_stage || 'not stated') + '. A price billed to a distributor is not a price '
        + 'the dealer charged onward.');
    }

    if (normName(a.unit).toLowerCase() !== normName(b.unit).toLowerCase()) {
      findings.push('Different units: ' + (a.unit || 'not stated') + ' and '
        + (b.unit || 'not stated') + '. A kit is not a single unit and a set is not a litre.');
    }

    var ea = manifest.normaliseEntity(a.entity), eb = manifest.normaliseEntity(b.entity);
    if (manifest.isSeparatePair(ea.distributor, eb.distributor)) {
      findings.push(ea.distributor + ' and ' + eb.distributor + ' are separate entities and are '
        + 'never combined into one figure.');
    } else if (normName(ea.distributor) !== normName(eb.distributor)
        && !isBlank(ea.distributor) && !isBlank(eb.distributor)) {
      findings.push('Different distributors: ' + ea.distributor + ' and ' + eb.distributor
        + '. They are reported separately unless a deliberate network total is asked for.');
    }
    if (normName(ea.purchasing_account) !== normName(eb.purchasing_account)
        && !isBlank(ea.purchasing_account) && !isBlank(eb.purchasing_account)) {
      findings.push('Different purchasing accounts: ' + ea.purchasing_account + ' and '
        + eb.purchasing_account + '. An account is not a distributor.');
    }

    return {
      ok: findings.length === 0,
      comparable: findings.length === 0,
      findings: findings,
      period_a: pa, period_b: pb,
      statement: findings.length === 0
        ? 'Same period, sales stage, unit and entity, so the comparison is allowed.'
        : 'Comparison refused. ' + findings.join(' ')
    };
  }

  /* Price level plus comparability, for the price-specific case. */
  function priceComparability(a, b) {
    var level = assertSamePriceLevel(a, b);
    var base = comparability(a, b);
    var findings = base.findings.slice();
    if (!level.comparable) findings.push(level.statement);
    return {
      ok: findings.length === 0, comparable: findings.length === 0,
      findings: findings, level: level.level || null,
      statement: findings.length === 0 ? 'Comparable on period, stage, unit, entity and price level.'
        : 'Comparison refused. ' + findings.join(' ')
    };
  }

  /* ------------------------------------------------------- reconciliation -- */

  /* A price is stated for a unit. A unit is counted even when no price can be
     stated for it. The two populations are reconciled and the remainder is left
     visible with its size - in rows, in units and in euro - instead of being
     dropped so that the priced table looks complete. */
  function reconcile(rows, opts) {
    opts = opts || {};
    var list = rows || [];
    var priced = [], unpriced = [], counted = [];
    var unpricedByEntity = {}, countedByEntity = {};
    var unpricedQty = 0, unpricedRows = 0, countedQty = 0, countedRows = 0;
    var unpricedEurUnknown = 0;

    list.forEach(function (r) {
      r = r || {};
      var qty = toNumberOrNull(r.quantity);
      var price = toNumberOrNull(r.price !== undefined ? r.price : r.observed_unit_price);
      var eur = toNumberOrNull(r.revenue_eur !== undefined ? r.revenue_eur : r.observed_billing_eur);
      var key = r.entity ? manifest.entityKey(r.entity)
        : (r.distributor || 'unknown') + SEP + '(account not stated)' + SEP + '(site not stated)';
      var label = r.entity ? manifest.entityLabel(r.entity) : (r.distributor || 'unknown distributor');

      if (price !== null) {
        priced.push(r);
      } else {
        unpriced.push(r);
        unpricedRows += 1;
        if (qty !== null) unpricedQty += qty;
        unpricedEurUnknown += 1;
        if (!unpricedByEntity[key]) unpricedByEntity[key] = { entity_label: label, rows: 0, units: 0 };
        unpricedByEntity[key].rows += 1;
        if (qty !== null) unpricedByEntity[key].units += qty;
      }
      if (qty !== null) {
        counted.push(r);
        countedRows += 1;
        countedQty += qty;
        if (!countedByEntity[key]) countedByEntity[key] = { entity_label: label, rows: 0, units: 0 };
        countedByEntity[key].rows += 1;
        countedByEntity[key].units += qty;
      }
    });

    var remainderRows = countedRows - priced.length;
    var remainder = {
      visible: true,
      rows: remainderRows,
      units: round2(countedQty - priced.reduce(function (s, r) {
        var q = toNumberOrNull(r.quantity);
        return s + (q === null ? 0 : q);
      }, 0)),
      by_entity: Object.keys(unpricedByEntity).map(function (k) { return unpricedByEntity[k]; }),
      statement: remainderRows > 0
        ? remainderRows + ' counted row(s) carry no usable price and are excluded from every priced '
          + 'total. They stay visible here with their unit count. A row with no price is not a row '
          + 'with a price of zero, and it is not a confirmed absence of demand.'
        : 'Every counted row also carries a price, so there is no unpriced remainder on this view.'
    };

    var ok = list.length === priced.length + unpriced.length && counted.length === countedRows;
    return {
      rows_in: list.length,
      rows_priced: priced.length,
      rows_unpriced: unpriced.length,
      rows_counted: countedRows,
      units_counted: round2(countedQty),
      units_unpriced: round2(unpricedQty),
      unpriced_by_entity: remainder.by_entity,
      counted_by_entity: Object.keys(countedByEntity).map(function (k) { return countedByEntity[k]; }),
      unclassified_remainder: remainder,
      classified: ok,
      statement: 'Of ' + list.length + ' row(s) supplied, ' + priced.length + ' are priced and '
        + countedRows + ' are counted. The ' + remainderRows + ' row(s) that are counted but not '
        + 'priced are reported, not dropped.'
    };
  }

  /* The conservation rule that stops an unpriced row joining a priced quantity.
     Adding one unit to the other changes what the number means. */
  function conservationOfTotals(pricedRows, countedRows) {
    var p = pricedRows || [], c = countedRows || [];
    var pricedQty = p.reduce(function (s, r) { return s + (toNumberOrNull(r.quantity) || 0); }, 0);
    var countedQty = c.reduce(function (s, r) { return s + (toNumberOrNull(r.quantity) || 0); }, 0);
    var ok = Math.abs(pricedQty - countedQty) < 1e-9;
    return {
      ok: ok,
      priced_quantity: round2(pricedQty),
      counted_quantity: round2(countedQty),
      difference: round2(countedQty - pricedQty),
      statement: ok
        ? 'The priced quantity and the counted quantity agree.'
        : 'The priced quantity and the counted quantity differ by ' + round2(countedQty - pricedQty)
          + ' unit(s). The difference is the unpriced remainder. It must not be added to the priced '
          + 'quantity, and its value is not zero.'
    };
  }

  /* -------------------------------------------------------- part identity -- */

  /* Original references are preserved. A relationship is not an approval, and the
     three kinds are three different things. */
  var RELATIONSHIP_KINDS = {
    catalogue_pairing: {
      kind: 'catalogue_pairing',
      label: 'Catalogue pairing',
      means: 'the catalogue lists the two numbers beside each other, typically a Genuine number '
        + 'with a BVP alternative',
      implies_fitment_approval: false,
      statement: 'A catalogue pairing says the two numbers are listed together. It does not say '
        + 'one may be fitted in place of the other.'
    },
    supersession: {
      kind: 'supersession',
      label: 'Supersession',
      means: 'a newer number has replaced an older number',
      implies_fitment_approval: false,
      statement: 'A supersession says the newer number replaced the older one. Supersession alone '
        + 'is not an approved fitment statement for a specific vehicle.'
    },
    replacement: {
      kind: 'replacement',
      label: 'Replacement',
      means: 'one number is declared a replacement for another, by a stated source',
      implies_fitment_approval: false,
      statement: 'A declared replacement is a source statement. Approval to fit is recorded '
        + 'separately and is not inferred from it.'
    },
    declared_newest_number: {
      kind: 'declared_newest_number',
      label: 'Declared newest number',
      means: 'a price-file column names the newest number for this part',
      implies_fitment_approval: false,
      statement: 'A newest-number column names the newest available number for ordering. It is not '
        + 'technical approval and it is not a fitment decision.'
    },
    combined_account: {
      kind: 'combined_account',
      label: 'Combined-account change',
      means: 'purchasing moved because seller accounts were combined or remapped',
      implies_fitment_approval: false,
      statement: 'A combined-account change explains a drop on one account number and a rise on another. '
        + 'It is not a proven lost and new pair.'
    },
    unknown: {
      kind: 'unknown',
      label: 'Unclassified relationship',
      means: 'the source states a relationship but not which kind',
      implies_fitment_approval: false,
      statement: 'The relationship is not classified, so it is reported as unclassified rather than '
        + 'assumed to be a pairing or a supersession.'
    }
  };

  function relationshipKind(kindId) {
    return RELATIONSHIP_KINDS[kindId] || RELATIONSHIP_KINDS.unknown;
  }

  /* Classify a raw relationship row without inventing anything. The raw text is
     kept alongside the classification. */
  function classifyRelationship(raw) {
    raw = raw || {};
    var text = normName(raw.relationship_type).toLowerCase();
    var kind = 'unknown';
    if (text.indexOf('catalogue pairing') >= 0) kind = 'catalogue_pairing';
    else if (text.indexOf('supersession') >= 0) kind = 'supersession';
    else if (text.indexOf('replacement') >= 0) kind = 'replacement';
    else if (text.indexOf('newest') >= 0) kind = 'declared_newest_number';
    else if (text.indexOf('combined-account') >= 0 || text.indexOf('combined account') >= 0) kind = 'combined_account';
    return { kind: kind, raw_type: raw.relationship_type || null, classified: kind !== 'unknown' };
  }

  /* Fitment is read only from a field that states it. An absent field means the
     question is open, not answered. */
  function fitmentStatus(raw) {
    raw = raw || {};
    var v = raw.technical_fitment_approved;
    if (isBlank(v)) {
      return { status: 'unresolved', approved: null, stated: false,
        statement: 'No fitment decision is recorded on this relationship. Fitment is not inferred '
          + 'from the relationship existing.' };
    }
    var s = String(v).toLowerCase();
    if (s.indexOf('not applicable') >= 0) {
      return { status: 'not applicable', approved: null, stated: true,
        statement: 'The source states fitment is not applicable for this relationship.' };
    }
    if (s === 'true' || s === 'yes' || s === 'approved') {
      return { status: 'approved by the stated source', approved: true, stated: true,
        statement: 'The source states this fitment is approved. Source ownership of that approval '
          + 'is outside this component.' };
    }
    return { status: 'recorded as ' + v, approved: false, stated: true,
      statement: 'The source records fitment as "' + v + '".' };
  }

  /* ------------------------------------------ references and versions (DATA-03) -- */

  /* A transacted part reference is text, exactly as received: leading zeros,
     spaces, letters and separators are kept. The match key is a second field
     for lookups (trimmed, upper case, zeros kept); it never replaces the
     original. A value that arrived as a number has already lost any leading
     zeros upstream, and says so. */
  function partReference(raw) {
    var asNumber = typeof raw === 'number';
    var text = raw === null || raw === undefined ? '' : String(raw);
    return {
      original_reference: text,
      match_key: text.trim().toUpperCase(),
      received_as_number: asNumber,
      statement: asNumber
        ? 'The reference arrived as a number, so any leading zeros were lost before it reached this tool. It is kept as received.'
        : 'Kept as text, exactly as received.'
    };
  }

  /* Classification, successor and candidate BVP links are three typed
     relationships, each versioned with its source and effective dates. An update
     adds a version and marks the one it supersedes; it never edits a recorded
     version, so a decision saved against version 1 still reads version 1. */
  var VERSIONED_KINDS = ['classification', 'successor', 'candidate_bvp'];

  function makeRelationshipLedger() {
    var store = {}, byId = {}, seq = 0;
    function keyOf(reference, kind) { return kind + SEP + String(reference); }

    function record(input) {
      input = input || {};
      if (VERSIONED_KINDS.indexOf(input.kind) < 0) {
        return { ok: false, error: 'A relationship is one of ' + VERSIONED_KINDS.join(', ') + '; "'
          + input.kind + '" is not recorded.' };
      }
      if (isBlank(input.reference) || isBlank(input.source)) {
        return { ok: false, error: 'A relationship needs the original reference and a stated source.' };
      }
      var key = keyOf(input.reference, input.kind);
      var list = store[key] || (store[key] = []);
      var prior = list.length ? list[list.length - 1] : null;
      seq += 1;
      var entry = {
        relationship_id: 'REL-' + seq,
        kind: input.kind,
        reference: String(input.reference),
        value: input.value === undefined ? null : input.value,
        source: input.source,
        source_version: input.source_version || null,
        effective_from: input.effective_from || null,
        effective_to: input.effective_to || null,
        version: list.length + 1,
        supersedes: prior ? prior.relationship_id : null,
        superseded_by: null
      };
      if (prior) prior.superseded_by = entry.relationship_id;
      list.push(entry);
      byId[entry.relationship_id] = entry;
      return { ok: true, relationship: JSON.parse(JSON.stringify(entry)) };
    }

    function history(reference, kind) {
      return JSON.parse(JSON.stringify(store[keyOf(reference, kind)] || []));
    }

    function current(reference, kind, asOf) {
      var list = store[keyOf(reference, kind)] || [];
      var hit = null;
      list.forEach(function (r) {
        if (isBlank(asOf) || isBlank(r.effective_from) || String(r.effective_from) <= String(asOf)) {
          if (isBlank(r.effective_to) || isBlank(asOf) || String(r.effective_to) >= String(asOf)) hit = r;
        }
      });
      return hit ? JSON.parse(JSON.stringify(hit)) : null;
    }

    /* A saved decision is read as it was saved. Newer versions are named beside
       it, never written into it. */
    function decisionView(decision) {
      decision = decision || {};
      var used = (decision.relationships_used || []).map(function (id) {
        return byId[id] ? JSON.parse(JSON.stringify(byId[id])) : { relationship_id: id, missing: true };
      });
      var newer = used.filter(function (r) { return r.superseded_by; }).map(function (r) {
        var list = store[keyOf(r.reference, r.kind)] || [];
        return { kind: r.kind, saved_version: r.version, latest_version: list.length,
          latest_id: list[list.length - 1].relationship_id };
      });
      return { decision_id: decision.decision_id || null, part_reference: decision.part_reference || null,
        used: used, newer_versions: newer,
        statement: newer.length ? newer.length + ' relationship(s) used by this decision have a newer version. '
          + 'The decision stands as saved; review it against the newer version before reusing it.'
          : 'The relationships this decision used are still the latest versions.' };
    }

    /* References with no classification stay listed as unclassified. */
    function unclassified(references) {
      return (references || []).filter(function (r) {
        return !(store[keyOf(r, 'classification')] || []).length;
      });
    }

    return { record: record, history: history, current: current, decisionView: decisionView,
      unclassified: unclassified, KINDS: VERSIONED_KINDS.slice() };
  }

  function relationships(payload) {
    var out = [];
    (payload && payload.cases || []).forEach(function (c) {
      var rel = (c.packEvidence && c.packEvidence.relationships) || [];
      rel.forEach(function (r, i) {
        var cls = classifyRelationship(r);
        var fit = fitmentStatus(r);
        out.push({
          case_id: c.id || null,
          index: i,
          relationship_record_id: r.relationship_record_id || null,
          part_number_a: r.part_number_a || null,
          part_number_b: r.part_number_b || null,
          direction: r.direction || null,
          relationship_type: cls.kind,
          relationship_type_raw: cls.raw_type,
          relationship_label: relationshipKind(cls.kind).label,
          relationship_means: relationshipKind(cls.kind).means,
          validation_status: fit.status,
          fitment_approved: fit.approved,
          fitment_statement: fit.statement,
          source_type: r.source_type || null,
          source_document: r.source_document || null,
          application_vehicle: r.application_vehicle || null,
          application_engine: r.application_engine || null,
          country_of_origin: r.country_of_origin || null,
          original_reference_preserved: true,
          restricted: false
        });
      });
    });
    return out;
  }


  /* -------------------------------------------------------- RANGE-01 ledger -- */

  /* Pairing, supersession and fitment are three different typed relationships.
     A successor or supersession is never treated as an interchangeable Genuine/BVP
     pair. Price and cost present do not approve a candidate. Two types on the same
     pair stay two records. */
  var RANGE_RELATIONSHIP_TYPES = ['pairing', 'supersession', 'fitment'];

  function makeRangeRelationshipLedger() {
    var byId = {};
    var rows = [];
    var seq = 0;

    function pairKey(a, b) {
      var x = String(a || '');
      var y = String(b || '');
      return x <= y ? x + SEP + y : y + SEP + x;
    }

    function record(input) {
      input = input || {};
      if (RANGE_RELATIONSHIP_TYPES.indexOf(input.type) < 0) {
        return { ok: false, error: 'A range relationship is one of '
          + RANGE_RELATIONSHIP_TYPES.join(', ') + '; "' + input.type + '" is not recorded.' };
      }
      if (input.promoted_from === 'successor' || input.promoted_from === 'supersession') {
        return { ok: false, error: 'A successor or supersession cannot be recorded as a pairing. '
          + 'Record it as supersession, and keep pairing as its own typed relationship.' };
      }
      if (isBlank(input.part_a) || isBlank(input.part_b) || isBlank(input.source)) {
        return { ok: false, error: 'A range relationship needs part_a, part_b and a stated source.' };
      }
      var authority = String(input.authority || 'candidate').toLowerCase();
      if (authority !== 'approved' && authority !== 'candidate' && authority !== 'withdrawn') {
        authority = 'candidate';
      }
      seq += 1;
      var entry = {
        relationship_id: 'RREL-' + seq,
        type: input.type,
        part_a: String(input.part_a),
        part_b: String(input.part_b),
        source: input.source,
        source_version: input.source_version || null,
        authority: authority,
        conditions: input.conditions ? JSON.parse(JSON.stringify(input.conditions)) : {},
        version: 1,
        pair_key: pairKey(input.part_a, input.part_b)
      };
      rows.push(entry);
      byId[entry.relationship_id] = entry;
      return { ok: true, relationship: JSON.parse(JSON.stringify(entry)) };
    }

    function listForPair(a, b) {
      var key = pairKey(a, b);
      return rows.filter(function (r) { return r.pair_key === key; })
        .map(function (r) { return JSON.parse(JSON.stringify(r)); });
    }

    function listAll() {
      return rows.map(function (r) { return JSON.parse(JSON.stringify(r)); });
    }

    function getById(id) {
      var row = byId[id];
      return row ? JSON.parse(JSON.stringify(row)) : null;
    }

    function withdraw(id, meta) {
      meta = meta || {};
      var row = byId[id];
      if (!row) return { ok: false, error: 'No range relationship with id ' + id + '.' };
      if (!row.saved_evidence) {
        row.saved_evidence = {
          authority: row.authority,
          part_a: row.part_a,
          part_b: row.part_b,
          source: row.source,
          source_version: row.source_version,
          type: row.type,
          conditions: JSON.parse(JSON.stringify(row.conditions || {})),
          version: row.version
        };
      }
      row.authority = 'withdrawn';
      row.version = (row.version || 1) + 1;
      row.withdrawal = {
        reason: meta.reason || 'Relationship withdrawn by technical authority.',
        withdrawn_by: meta.withdrawn_by || null,
        withdrawn_at: meta.withdrawn_at || null
      };
      return { ok: true, relationship: JSON.parse(JSON.stringify(row)) };
    }

    return {
      record: record,
      listForPair: listForPair,
      listAll: listAll,
      getById: getById,
      withdraw: withdraw,
      TYPES: RANGE_RELATIONSHIP_TYPES.slice()
    };
  }

  function interchangeablePairStatus(relationship) {
    relationship = relationship || {};
    var type = relationship.type || relationship.relationship_type || null;
    var authority = String(relationship.authority || '').toLowerCase();
    if (type === 'pairing' && authority === 'approved') {
      return {
        interchangeable: true,
        type: type,
        authority: authority,
        statement: 'Approved pairing: the two numbers may be treated as an interchangeable '
          + 'Genuine/BVP pair for commercial review. Fitment remains a separate typed relationship.'
      };
    }
    if (type === 'supersession' || type === 'successor') {
      return {
        interchangeable: false,
        type: type,
        authority: authority || null,
        statement: 'A supersession or successor says one number replaced another. It is not an '
          + 'interchangeable Genuine/BVP pairing.'
      };
    }
    if (type === 'fitment') {
      return {
        interchangeable: false,
        type: type,
        authority: authority || null,
        statement: 'Fitment is technical suitability. It is not a commercial Genuine/BVP pairing.'
      };
    }
    return {
      interchangeable: false,
      type: type,
      authority: authority || null,
      statement: 'Not an interchangeable Genuine/BVP pair. Pairing requires type pairing and '
        + 'approved authority.'
    };
  }

  function rangeCommercialRole(relationship, opts) {
    relationship = relationship || {};
    opts = opts || {};
    var pricePresent = !!opts.price_present;
    var costPresent = !!opts.cost_present;
    var authority = String(relationship.authority || 'candidate').toLowerCase();
    var pair = interchangeablePairStatus(relationship);
    var role = 'candidate';
    if (authority === 'withdrawn') role = 'withdrawn';
    else if (authority === 'approved' && relationship.type === 'pairing') role = 'approved_pairing';
    else if (authority === 'approved') role = 'approved_' + String(relationship.type || 'relationship');
    else role = 'candidate';
    /* Price and cost never promote authority. Withdrawn stays withdrawn. */
    if (authority !== 'approved' && authority !== 'withdrawn') role = 'candidate';
    var statement;
    if (authority === 'withdrawn') {
      statement = 'This relationship is withdrawn. The earlier saved evidence is kept for history. '
        + 'A new action needs a fresh review; the withdrawn approval cannot be reused.';
    } else if (authority === 'approved') {
      statement = 'Authority is approved for this ' + (relationship.type || 'relationship')
        + '. Price and cost are reported beside it and do not change the authority.';
    } else {
      statement = 'Unapproved relationship stays a candidate even when price and cost are present. '
        + 'Price present: ' + (pricePresent ? 'yes' : 'no') + '; cost present: '
        + (costPresent ? 'yes' : 'no') + '.';
    }
    return {
      role: role,
      interchangeable: pair.interchangeable && authority === 'approved',
      authority: authority,
      type: relationship.type || null,
      price_present: pricePresent,
      cost_present: costPresent,
      statement: statement
    };
  }


  /* -------------------------------------------------------- RANGE-04 transfer -- */

  function rangeTransferSplit(input) {
    input = input || {};
    var from = input.from_line || {};
    var to = input.to_line || {};
    var transferred = toNumberOrNull(input.transferred_units);
    var newUnits = toNumberOrNull(input.new_units);
    if (transferred === null) transferred = 0;
    if (newUnits === null) newUnits = 0;
    if (transferred < 0) transferred = 0;
    if (newUnits < 0) newUnits = 0;

    var fromPrice = toNumberOrNull(from.price_eur);
    var fromCost = toNumberOrNull(from.cost_eur);
    var toPrice = toNumberOrNull(to.price_eur);
    var toCost = toNumberOrNull(to.cost_eur);

    var transferRevenue = (toPrice !== null) ? round2(transferred * toPrice) : null;
    var newGrossRevenue = (toPrice !== null) ? round2(newUnits * toPrice) : null;

    var displaced = null;
    if (fromPrice !== null && fromCost !== null) {
      displaced = round2(transferred * (fromPrice - fromCost));
    }
    var transferGain = null;
    if (toPrice !== null && toCost !== null) {
      transferGain = round2(transferred * (toPrice - toCost));
    }
    var newGain = null;
    if (toPrice !== null && toCost !== null) {
      newGain = round2(newUnits * (toPrice - toCost));
    }

    var net = null;
    if (displaced !== null && transferGain !== null && newGain !== null) {
      /* Displaced contribution is deducted exactly once. */
      net = round2(transferGain + newGain - displaced);
    }

    return {
      transferred_units: transferred,
      new_units: newUnits,
      transfer_revenue_eur: transferRevenue,
      new_gross_revenue_eur: newGrossRevenue,
      displaced_contribution_eur: displaced,
      displaced_deduction_count: 1,
      transfer_contribution_eur: transferGain,
      new_contribution_eur: newGain,
      net_contribution_change_eur: net,
      from_reference: from.original_reference || null,
      to_reference: to.original_reference || null,
      statement: newUnits === 0
        ? ('Pure one-for-one transfer of ' + transferred + ' unit(s): not counted as new units '
          + 'and not as new gross revenue equal to the receiving line\'s full sales. '
          + 'Transfer revenue is labelled separately. Displaced contribution is deducted once.')
        : ('Transferred units (' + transferred + ') stay apart from independently assumed new units ('
          + newUnits + '). New gross revenue uses only the new units. Displaced contribution '
          + 'from the original offer is deducted once in the baseline-versus-proposal basket.')
    };
  }

  /* -------------------------------------------------------- RANGE-03 basket -- */

  function rangeBasket(lines) {
    lines = Array.isArray(lines) ? lines : [];
    var outLines = [];
    var currencies = {};
    lines.forEach(function (raw, i) {
      raw = raw || {};
      var qty = toNumberOrNull(raw.quantity);
      var price = toNumberOrNull(raw.price_eur !== undefined ? raw.price_eur : raw.price);
      var cost = toNumberOrNull(raw.cost_eur !== undefined ? raw.cost_eur : raw.cost);
      var eligible = raw.eligible !== false;
      var currency = isBlank(raw.currency) ? null : String(raw.currency).toUpperCase();
      var revenue = (qty !== null && price !== null) ? round2(qty * price) : null;
      var profit = (qty !== null && price !== null && cost !== null) ? round2(qty * (price - cost)) : null;
      if (eligible && currency) currencies[currency] = 1;
      outLines.push({
        line_index: i,
        original_reference: raw.original_reference || raw.reference || null,
        quantity: qty,
        price_eur: price,
        cost_eur: cost,
        cost_basis: raw.cost_basis || null,
        eligible: eligible,
        currency: currency,
        revenue_eur: revenue,
        profit_eur: profit
      });
    });
    var currencyList = Object.keys(currencies).sort();
    if (currencyList.length > 1) {
      return {
        state: 'currency_mixed',
        profit_state: 'unresolved',
        currency: null,
        currencies_seen: currencyList,
        eligible_line_count: outLines.filter(function (l) { return l.eligible; }).length,
        excluded_line_count: outLines.filter(function (l) { return !l.eligible; }).length,
        revenue_eur: null,
        profit_eur: null,
        lines: outLines,
        statement: 'Basket totals are not mixed across currencies. Eligible lines use '
          + currencyList.join(' and ')
          + '. Keep each currency in its own basket; line facts above stay.'
      };
    }
    var eligible = outLines.filter(function (l) { return l.eligible; });
    var revenue = 0;
    var revenueOk = true;
    eligible.forEach(function (l) {
      if (l.revenue_eur === null) revenueOk = false;
      else revenue += l.revenue_eur;
    });
    var missingCost = eligible.some(function (l) { return l.cost_eur === null; });
    var profit = 0;
    var profitOk = !missingCost;
    if (profitOk) {
      eligible.forEach(function (l) {
        if (l.profit_eur === null) profitOk = false;
        else profit += l.profit_eur;
      });
    }
    return {
      state: missingCost ? 'partial' : 'complete',
      profit_state: missingCost ? 'partial' : 'complete',
      currency: currencyList[0] || null,
      currencies_seen: currencyList,
      eligible_line_count: eligible.length,
      excluded_line_count: outLines.length - eligible.length,
      revenue_eur: revenueOk ? round2(revenue) : null,
      profit_eur: profitOk ? round2(profit) : null,
      lines: outLines,
      statement: missingCost
        ? ('Basket profit is partial: at least one eligible material line is missing cost. '
          + 'Known line facts (reference, quantity, price, and any held cost) are preserved. '
          + 'Ineligible lines are excluded from the basket totals.')
        : ('Basket revenue and profit reconcile exactly to the eligible line results. '
          + 'Ineligible lines are excluded. Margin figures stay as margin, not a factor.')
    };
  }

  /* -------------------------------------------------------- RANGE-08 withdrawal -- */

  function withdrawRangeRelationship(ledger, relationshipId, meta) {
    if (!ledger || typeof ledger.withdraw !== 'function') {
      return { ok: false, error: 'A range relationship ledger with withdraw is required.' };
    }
    return ledger.withdraw(relationshipId, meta || {});
  }

  function rangeWithdrawalImpact(cases, relationship) {
    cases = cases || [];
    relationship = relationship || {};
    var a = String(relationship.part_a || relationship.part_number_a || '');
    var b = String(relationship.part_b || relationship.part_number_b || '');
    var affected = [];
    cases.forEach(function (c) {
      if (!c) return;
      var rels = ((c.packEvidence || {}).relationships) || [];
      var hit = false;
      rels.forEach(function (r) {
        var ra = String(r.part_number_a || r.part_a || '');
        var rb = String(r.part_number_b || r.part_b || '');
        if ((ra === a && rb === b) || (ra === b && rb === a)) hit = true;
      });
      var pn = String(c.pn || '');
      var g = (((c.parts || {}).genuine) || {}).pn;
      var v = (((c.parts || {}).bvp) || {}).pn;
      if (pn === a || pn === b || g === a || g === b || v === a || v === b) hit = true;
      if (hit) affected.push(c.id);
    });
    var uniq = [];
    affected.forEach(function (id) { if (uniq.indexOf(id) < 0) uniq.push(id); });
    return {
      affected_case_ids: uniq,
      requires_fresh_review: true,
      relationship_id: relationship.relationship_id || null,
      statement: 'Relationship withdrawn. Affected active case(s): '
        + (uniq.length ? uniq.join(', ') : 'none')
        + '. Original saved evidence is preserved. A fresh review is required before any new action.'
    };
  }

  function canReuseApplicationApproval(relationship) {
    relationship = relationship || {};
    var authority = String(relationship.authority || '').toLowerCase();
    if (authority === 'withdrawn') {
      return {
        allowed: false,
        statement: 'Cannot reuse a withdrawn application approval. Record a fresh review with a new '
          + 'approval before any new commercial scenario uses this pairing.'
      };
    }
    if (authority === 'approved' && (relationship.type === 'pairing'
        || relationship.relationship_type === 'catalogue_pairing'
        || relationship.relationship_type === 'catalogue pairing')) {
      return {
        allowed: true,
        statement: 'Approved pairing may be used for a commercial scenario that cites this relationship.'
      };
    }
    return {
      allowed: false,
      statement: 'No reusable application approval is held for this relationship.'
    };
  }

  /* -------------------------------------------------------- RANGE-02 view -- */

  function exactRangeComparison(caseObject, opts) {
    caseObject = caseObject || {};
    opts = opts || {};
    var audience = opts.audience === 'external' ? 'external' : 'internal';
    var labels = {
      reference_price: 'Reference price',
      actual_price: 'Actual price',
      application_status: 'Application status'
    };
    var parts = caseObject.parts || {};
    var genuine = parts.genuine || null;
    var bvp = parts.bvp || null;
    var rels = ((caseObject.packEvidence || {}).relationships) || [];
    var approvedPair = null;
    var withdrawnPair = null;
    rels.forEach(function (r) {
      var auth = String(r.authority || '').toLowerCase();
      var status = String(r.validation_status || '').toLowerCase();
      var cls = classifyRelationship(r);
      var fit = fitmentStatus(r);
      if (auth === 'withdrawn' || status === 'withdrawn') {
        if (cls.kind === 'catalogue_pairing') withdrawnPair = r;
        return;
      }
      if (cls.kind === 'catalogue_pairing' && fit.approved === true) approvedPair = r;
    });

    function side(src, fallbackPn) {
      src = src || {};
      var cost = audience === 'internal' && src.cost_eur !== undefined && src.cost_eur !== null
        ? src.cost_eur : null;
      return {
        reference: src.pn || fallbackPn || null,
        reference_price_eur: src.reference_price_eur !== undefined ? src.reference_price_eur : null,
        actual_price_eur: src.actual_price_eur !== undefined ? src.actual_price_eur : null,
        application_status: src.application_status || 'unresolved',
        cost_eur: cost
      };
    }

    if (genuine && bvp && genuine.pn && bvp.pn && String(genuine.pn) !== String(bvp.pn)) {
      return {
        state: 'exact',
        reference_a: String(genuine.pn),
        reference_b: String(bvp.pn),
        side_a: side(genuine, genuine.pn),
        side_b: side(bvp, bvp.pn),
        labels: labels,
        relationship_authority: withdrawnPair
          ? 'withdrawn pairing - fresh review required'
          : (approvedPair ? 'approved pairing' : 'pairing not approved on the held relationship'),
        cost_statement: audience === 'internal'
          ? 'Cost is shown in the internal view only.'
          : 'Cost is not shown outside the internal view.',
        statement: 'Exact comparison of two distinct references: ' + genuine.pn + ' and ' + bvp.pn
          + '. Reference price, actual price and application status are labelled separately.'
      };
    }

    var only = genuine || bvp || { pn: caseObject.pn || null };
    return {
      state: 'counterpart_unresolved',
      reference_a: only.pn ? String(only.pn) : (caseObject.pn || null),
      reference_b: null,
      side_a: side(only, caseObject.pn || null),
      side_b: null,
      labels: labels,
      relationship_authority: 'counterpart unresolved',
      cost_statement: audience === 'internal'
        ? 'Cost is shown in the internal view only.'
        : 'Cost is not shown outside the internal view.',
      statement: 'Counterpart unresolved: the comparison does not invent a second reference. '
        + 'Only ' + (only.pn || caseObject.pn || 'the held reference') + ' is named.'
    };
  }

  function relationshipSummary(payload) {
    var rows = relationships(payload);
    var byKind = {}, byFitment = {};
    rows.forEach(function (r) {
      byKind[r.relationship_type] = (byKind[r.relationship_type] || 0) + 1;
      byFitment[r.validation_status] = (byFitment[r.validation_status] || 0) + 1;
    });
    var approved = rows.filter(function (r) { return r.fitment_approved === true; }).length;
    return {
      total: rows.length,
      by_relationship_type: byKind,
      by_fitment_status: byFitment,
      fitment_approved_count: approved,
      statement: rows.length + ' relationship record(s): ' + Object.keys(byKind).map(function (k) {
        return byKind[k] + ' ' + relationshipKind(k).label.toLowerCase();
      }).join(', ') + '. Fitment is explicitly approved on ' + approved + ' of them. A relationship '
        + 'existing is not an approval to fit, and the two are reported separately.'
    };
  }

  /* --------------------------------------------------------- stage failure -- */

  /* A refresh either completes or it does not. A partial refresh never replaces
     the last accepted view. */
  function makeStageState(name) {
    var state = {
      stage: name || 'unnamed stage',
      accepted: null,
      accepted_at: null,
      accepted_revision: 0,
      pending: null,
      last_attempt_at: null,
      last_failure: null,
      refresh_state: 'no view accepted yet'
    };

    function begin(candidate) {
      state.pending = candidate === undefined ? null : candidate;
      state.last_attempt_at = new Date().toISOString();
      state.refresh_state = 'refresh in progress; the last accepted view stays visible';
      return state;
    }

    function commit(candidate) {
      var next = candidate === undefined ? state.pending : candidate;
      state.accepted = next === undefined ? null : next;
      state.accepted_at = new Date().toISOString();
      state.accepted_revision += 1;
      state.pending = null;
      state.last_failure = null;
      state.refresh_state = 'accepted revision ' + state.accepted_revision;
      return { ok: true, revision: state.accepted_revision, view: state.accepted };
    }

    function fail(reason) {
      var partial = state.pending;
      state.pending = null;
      state.last_failure = {
        at: new Date().toISOString(), reason: reason || 'unspecified failure',
        partial_result_discarded: partial !== null && partial !== undefined,
        partial_result: null      /* never handed back: it must not be shown */
      };
      state.refresh_state = state.accepted === null
        ? 'refresh failed and no view was ever accepted, so nothing is shown'
        : 'refresh failed; the last accepted view (revision ' + state.accepted_revision + ') is '
          + 'still the one on screen';
      return { ok: false, failed: true, reason: state.last_failure.reason,
        showing: state.accepted === null ? null : { revision: state.accepted_revision, view: state.accepted },
        statement: state.refresh_state };
    }

    function view() {
      return {
        stage: state.stage,
        showing_revision: state.accepted === null ? null : state.accepted_revision,
        view: state.accepted,
        refresh_state: state.refresh_state,
        last_failure: state.last_failure,
        partially_refreshed: state.accepted !== null && state.pending !== null,
        statement: state.accepted === null
          ? (state.last_failure ? 'No view is shown because the first refresh failed.' : 'No view has been accepted yet.')
          : state.refresh_state
      };
    }

    return { begin: begin, commit: commit, fail: fail, view: view, state: state };
  }

  /* ------------------------------------------------- ledger conservation -- */

  /* One conservation rule for every ledger in this layer.

     A row that is set aside was received once and classified once when it was
     taken in. Setting it aside is a later event: it moves the row out of the
     held set and keeps its quantity, its value and the reason it was taken out.
     The set-aside row therefore belongs to the SET-ASIDE BUCKET and to nothing
     else. It is never added back into the received total.

     The defect this replaces added the set-aside list to the received total a
     second time:

         accounted = added + replaced + unchanged + set_aside.length

     Every received row is already classified in exactly one of added, replaced,
     unchanged or folded, so that sum is `received + setAside` - once for the row
     and once for it having been set aside. The check then reported a difference
     whenever anything had been set aside, and reported balance whenever nothing
     had, whether or not a row had gone missing. It did not detect a loss; it
     detected the presence of a set-aside.

     Three identities are checked here, and each one can fail on its own:

         received   = added + replaced + unchanged + folded   (every receipt classified once)
         held       = the rows the key index still holds      (the store agrees with the index)
         keys_taken = held + set aside - set-aside re-imports (every key still pointable)

     The second and the third are what make a genuine loss detectable. A row that
     leaves the store without a stated reason breaks the store against the index;
     a key that is taken in and then dropped breaks the third. Either one refuses
     to be called balance. */
  function conservationOfLedger(ledger) {
    ledger = ledger || {};
    function count(v) { var x = toNumberOrNull(v); return x === null ? 0 : x; }

    var received = count(ledger.received);
    var added = count(ledger.added);
    var replaced = count(ledger.replaced);
    var unchanged = count(ledger.unchanged);
    var folded = count(ledger.folded);
    var held = count(ledger.held);
    var revisions = count(ledger.revisions);
    var corrections = count(ledger.corrections);

    var setAsideDetail = ledger.set_aside || [];
    var setAsideEvents = setAsideDetail.length;

    var keysSupplied = ledger.keys_held !== undefined || ledger.keys_taken !== undefined
      || ledger.keys_set_aside !== undefined;
    var keysHeld = ledger.keys_held === undefined ? null : count(ledger.keys_held);
    var keysSetAside = ledger.keys_set_aside === undefined ? null : count(ledger.keys_set_aside);
    var keysTaken = ledger.keys_taken === undefined ? null : count(ledger.keys_taken);
    if (keysTaken === null && keysHeld !== null && keysSetAside !== null) {
      keysTaken = keysHeld + keysSetAside;
    }

    /* A key that was set aside and later imported again starts a new
       registration, so its original receipt and its re-receipt both stand. The
       declared count keeps the registered-key check exact instead of reporting
       the re-import as a loss. Where the count is not stated, zero is assumed
       and any shortfall is still reported rather than absorbed. */
    var setAsideReimported = ledger.set_aside_reimported === undefined
      ? 0 : count(ledger.set_aside_reimported);

    var classified = added + replaced + unchanged + folded;
    var heldDifference = keysHeld === null ? null : round2(held - keysHeld);
    var difference = round2(received - classified);
    /* Distinct keys ever received, against the keys the ledger can still point
       at: the ones held plus the ones set aside. A key set aside and later
       imported again is in both, so it is taken out once here rather than
       counted as two rows. */
    var keysRegistered = (keysHeld === null || keysSetAside === null)
      ? null : keysHeld + keysSetAside - setAsideReimported;

    var findings = [];
    if (difference !== 0) {
      findings.push({
        code: 'UNCLASSIFIED_ROWS',
        difference: difference,
        statement: difference > 0
          ? difference + ' row(s) were received and are counted nowhere: they are not in the added, '
            + 'replaced, unchanged or folded buckets, so no total from this ledger includes them.'
          : Math.abs(difference) + ' row(s) are counted more often than they were received, so some '
            + 'activity is being counted twice and a total from this ledger would inflate it.'
      });
    }
    if (heldDifference !== null && heldDifference !== 0) {
      findings.push({
        code: 'STORE_DISAGREES_WITH_INDEX',
        difference: heldDifference,
        statement: heldDifference < 0
          ? Math.abs(heldDifference) + ' row(s) that the key index holds are not in the store. A row '
            + 'has gone missing without being set aside, and its quantity and value are counted nowhere.'
          : heldDifference + ' row(s) are in the store and not in the key index, so they would be '
            + 'counted in a total and traced to no import.'
      });
    }
    if (keysRegistered !== null && keysTaken !== null && keysRegistered !== keysTaken) {
      findings.push({
        code: 'UNREGISTERED_KEYS',
        difference: round2(keysTaken - keysRegistered),
        statement: (keysTaken - keysRegistered) + ' key(s) were taken into this ledger and are now '
          + 'neither held nor recorded as set aside with a reason. A row has been dropped without a '
          + 'stated reason, so the loss is reported rather than absorbed into a total.'
      });
    }

    var notes = [];
    if (!keysSupplied) {
      notes.push('This ledger did not supply its key counts, so the store was not cross-checked '
        + 'against the key index. The received total was still checked against its own buckets.');
    }

    var ok = findings.length === 0;
    return {
      ok: ok,
      identity: 'received plus any re-imported set-aside key = added + replaced + unchanged + '
        + 'folded + set aside, and held = the rows the key index still holds',
      revisions: revisions,
      corrections: corrections,
      rows_received: received,
      rows_added: added,
      rows_replaced: replaced,
      rows_unchanged: unchanged,
      rows_folded: folded,
      rows_received_classified: classified,
      rows_set_aside: setAsideEvents,
      rows_set_aside_distinct: keysSetAside,
      rows_set_aside_reimported: setAsideReimported,
      rows_accounted: classified,
      rows_held: held,
      keys_taken: keysTaken,
      keys_held: keysHeld,
      keys_set_aside: keysSetAside,
      keys_registered: keysRegistered,
      difference: difference,
      held_difference: heldDifference,
      findings: findings,
      notes: notes,
      statement: ok
        ? received + ' row(s) received across ' + revisions + ' revision(s): ' + added + ' added, '
          + replaced + ' replaced, ' + unchanged + ' folded as repeats'
          + (folded ? ', ' + folded + ' folded as a duplicate line inside one import' : '')
          + '. ' + setAsideEvents + ' row(s) set aside with a reason, each counted once and only in '
          + 'the set-aside bucket. ' + held + ' row(s) are held. Every received row is accounted for '
          + 'exactly once.'
        : 'Conservation does not balance, so no total is stated from it. '
          + findings.map(function (f) { return f.statement; }).join(' ')
          + ' A row that cannot be accounted for is reported, never absorbed into a total.'
    };
  }

  /* ------------------------------------------------- idempotent import (05) -- */

  /* A keyed upsert. Re-importing the same source section replaces its own records
     instead of adding a second copy of them. Every change is recorded against the
     source section that caused it, so a figure can be traced back to the import
     that produced it. */
  function makeImportLog(opts) {
    opts = opts || {};
    var keyOf = opts.key_of || function (r) {
      return [r.part_number, r.distributor, r.period].map(function (v) {
        return v === null || v === undefined ? '' : String(v);
      }).join(SEP);
    };
    var current = {};       /* key -> record            */
    var provenance = {};    /* key -> source section    */
    var history = [];
    var sections = {};
    var setAsideEntries = [];

    function upsert(sourceSection, records) {
      records = records || [];
      var section = {
        source_section: sourceSection,
        at: new Date().toISOString(),
        operation: 'upsert',
        inserts: [], replaced: [], untouched: [], duplicates_within_batch: []
      };
      var seenInBatch = {};
      var unchanged = 0;

      records.forEach(function (r) {
        var k = keyOf(r);
        if (seenInBatch[k]) {
          /* The same key twice in one file is a duplicate line, not extra
             quantity. It is folded, and the fold is reported. */
          section.duplicates_within_batch.push({ key: k,
            statement: 'The same key appears more than once in one import. The later line replaces '
              + 'the earlier one and the quantity is not added twice.' });
          replacedOrInsert(r, k, section, true);
          return;
        }
        seenInBatch[k] = true;
        if (current[k] === undefined) {
          insert(r, k, section);
        } else if (JSON.stringify(current[k]) !== JSON.stringify(r)) {
          replacedOrInsert(r, k, section, false);
        } else {
          unchanged += 1;
          section.untouched.push(k);
          /* Provenance is still the section that last supplied the record. */
          provenance[k] = provenance[k] || section.source_section;
        }
      });

      section.records_unchanged = unchanged;
      sections[sourceSection] = { last_upsert: section.at, records: records.length };
      history.push(section);
      return {
        ok: true, source_section: sourceSection,
        inserted: section.inserts.length,
        replaced: section.replaced.length,
        unchanged: unchanged,
        duplicates_folded: section.duplicates_within_batch.length,
        total_records: Object.keys(current).length,
        statement: 'Import of "' + sourceSection + '" added ' + section.inserts.length
          + ', replaced ' + section.replaced.length + ' and left ' + unchanged + ' record(s) '
          + 'untouched. Re-importing the same section does not add a second copy of anything.'
      };
    }

    function insert(r, k, section) {
      current[k] = r;
      provenance[k] = section.source_section;
      section.inserts.push(k);
    }

    function replacedOrInsert(r, k, section, fromDuplicate) {
      if (current[k] === undefined) {
        insert(r, k, section);
        return;
      }
      if (!fromDuplicate) {
        section.replaced.push({ key: k, supersedes_source_section: provenance[k] || null });
      }
      current[k] = r;
      provenance[k] = section.source_section;
    }

    /* A correction names the record it replaces. It replaces that record and does
       not multiply the activity the record described. */
    function correct(sourceSection, record, correction) {
      correction = correction || {};
      var k = correction.key || keyOf(record);
      var existing = current[k];
      if (!existing) {
        return { ok: false, error: 'No such record to correct. A correction must name a record '
          + 'that exists, so that the activity it corrects is not counted a second time.' };
      }
      var entry = {
        correction_id: correction.correction_id || ('COR-' + (history.length + 1)),
        corrects_key: k,
        corrects_source_section: provenance[k] || null,
        corrects_revision: correction.corrects_revision || null,
        reason: correction.reason || null,
        justified: !isBlank(correction.reason),
        replaces_values: existing,
        corrected_values: record,
        affected_keys: null,
        at: new Date().toISOString()
      };
      current[k] = record;
      provenance[k] = sourceSection;
      history.push({ source_section: sourceSection, at: entry.at, operation: 'correction',
        correction: entry, records: 1 });
      sections[sourceSection] = { last_upsert: entry.at, records: 1, corrections: 1 };
      return { ok: true, correction: entry, total_records: Object.keys(current).length,
        statement: 'Correction ' + entry.correction_id + ' replaced the record it names and kept '
          + 'the replaced values in the record. The corrected activity is counted once.' };
    }

    /* A row that must not stand in the accepted set is set aside rather than
       dropped. It is removed from the held set and kept in the set-aside bucket
       with its reason, its quantity and its value, so it is still reportable and
       is still counted - exactly once, in that bucket. */
    function setAside(key, reason, meta) {
      meta = meta || {};
      var existing = current[key];
      if (existing === undefined) {
        return { ok: false, error: 'No held record carries that key, so there is nothing to set '
          + 'aside. A row that was never taken in cannot be set aside.' };
      }
      var entry = {
        key: key,
        reason: isBlank(reason) ? 'no reason stated' : reason,
        stated_reason: !isBlank(reason),
        source_section: provenance[key] || null,
        revision_set_aside: meta.revision === undefined ? null : meta.revision,
        record: existing,
        quantity: toNumberOrNull(existing.quantity !== undefined ? existing.quantity : existing.billed_qty),
        value_eur: toNumberOrNull(existing.observed_billing_eur !== undefined
          ? existing.observed_billing_eur : existing.value_eur),
        at: meta.at || null
      };
      setAsideEntries.push(entry);
      delete current[key];
      delete provenance[key];
      history.push({ source_section: meta.source_section || '(set aside)', at: entry.at,
        operation: 'set_aside', set_aside: entry, records: 1 });
      return { ok: true, set_aside: setAsideEntries.length, entry: entry,
        rows_held: Object.keys(current).length,
        statement: 'The row was set aside with its reason and is reported in the set-aside bucket. '
          + 'It is no longer held and it is counted once, in that bucket only.' };
    }

    function conservation() {
      var corrections = history.filter(function (h) { return h.operation === 'correction'; });
      var inserts = history.reduce(function (s, h) { return s + (h.inserts ? h.inserts.length : 0); }, 0);
      var replaces = history.reduce(function (s, h) { return s + (h.replaced ? h.replaced.length : 0); }, 0);
      var untouched = history.reduce(function (s, h) { return s + (h.records_unchanged || 0); }, 0);
      var foldedInsideOneImport = history.reduce(function (s, h) {
        return s + (h.duplicates_within_batch ? h.duplicates_within_batch.length : 0);
      }, 0);
      var records = Object.keys(current).length;
      var setAsideKeys = {};
      setAsideEntries.forEach(function (e) { setAsideKeys[e.key] = true; });
      /* How many set-aside keys have since been imported again, so their receipt
         stands twice: once originally and once on the re-import. Without this the
         rule would read the second receipt as an unaccounted row. */
      var setAsideReimported = 0;
      Object.keys(current).forEach(function (k) { if (setAsideKeys[k]) setAsideReimported += 1; });
      var keysEverTaken = {};
      history.forEach(function (h) {
        (h.inserts || []).forEach(function (k) { keysEverTaken[k] = true; });
        (h.replaced || []).forEach(function (r) { keysEverTaken[r.key] = true; });
        (h.untouched || []).forEach(function (k) { keysEverTaken[k] = true; });
      });

      /* One rule, one place: the shared conservation check below owns the
         arithmetic. This function only supplies the counts, and the keys, so
         that a record which leaves the store without a stated reason is caught
         here as well as at the set level. */
      var result = conservationOfLedger({
        revisions: history.length,
        corrections: corrections.length,
        received: inserts + replaces + untouched + foldedInsideOneImport,
        added: inserts,
        replaced: replaces,
        unchanged: untouched,
        folded: foldedInsideOneImport,
        held: records,
        set_aside: setAsideEntries,
        set_aside_reimported: setAsideReimported,
        keys_held: records,
        keys_set_aside: Object.keys(setAsideKeys).length,
        keys_taken: Object.keys(keysEverTaken).length
      });
      result.records_held = records;
      result.records_inserted_total = inserts;
      result.records_replaced_total = replaces;
      result.records_untouched_total = untouched;
      result.identical_repeats_folded = foldedInsideOneImport;
      result.net = records - inserts + replaces;
      result.set_aside = setAsideEntries.slice();
      return result;
    }

    function get(key) { return current[key] === undefined ? null : current[key]; }
    function sum(selector) {
      var total = 0, missing = 0;
      Object.keys(current).forEach(function (k) {
        var v = selector ? selector(current[k]) : current[k].quantity;
        var n = toNumberOrNull(v);
        if (n === null) missing += 1; else total += n;
      });
      return { total: round2(total), records_without_a_value: missing,
        statement: missing ? missing + ' record(s) carry no value and are excluded from the total '
          + 'rather than counted as zero.' : 'Every held record carries a value.' };
    }
    function all() { return Object.keys(current).map(function (k) { return current[k]; }); }
    function provenanceOf(key) { return provenance[key] || null; }
    function traceability() {
      return {
        keys: Object.keys(current).length,
        with_provenance: Object.keys(provenance).filter(function (k) { return !!provenance[k]; }).length,
        sections: Object.keys(sections).map(function (k) {
          return { source_section: k, last_upsert: sections[k].last_upsert, records: sections[k].records };
        }),
        corrections: history.filter(function (h) { return h.operation === 'correction'; })
          .map(function (h) { return { correction_id: h.correction.correction_id,
            corrects_key: h.correction.corrects_key, justified: h.correction.justified,
            reason: h.correction.reason }; }),
        statement: 'Every held record names the source section that produced it, so a corrected '
          + 'figure can be traced to the import that set it and to the correction that changed it.'
      };
    }

    return { upsert: upsert, correct: correct, setAside: setAside, conservation: conservation,
      get: get, sum: sum, all: all, provenanceOf: provenanceOf, traceability: traceability,
      history: function () { return history.slice(); } };
  }

  /* --------------------------------------------------------------- market -- */

  /* A field can carry a value and still say nothing: "not stated", "unknown"
     and "n/a" are the same as an empty field, and are treated as one. */
  function statesNoValue(v) {
    if (isBlank(v)) return true;
    var s = String(v).trim().toLowerCase();
    return s === 'n/a' || s === 'na' || s === 'unknown' || s === 'not stated'
      || s === 'not declared' || s === 'not available' || s === 'none'
      || s === 'to be confirmed' || s === 'tbc' || s === '-';
  }

  /* MARKET-01: a dated competitor observation is evidence, not truth. */
  function evidenceStrength(observation, opts) {
    opts = opts || {};
    var o = observation || {};
    var findings = [];
    if (statesNoValue(o.retrieved)) findings.push('no retrieval date is recorded');
    if (statesNoValue(o.url) && statesNoValue(o.source_file)) {
      findings.push('no source location is recorded');
    }
    if (statesNoValue(o.tax)) findings.push('the tax basis is not stated');
    if (statesNoValue(o.match)) {
      findings.push('no match statement (exact number or equivalent) is recorded');
    }
    if (o.approvalReady !== true) findings.push('the observation is not marked ready for approval');
    var score = 5 - findings.length;
    return {
      strength: findings.length === 0 ? 'complete' : (findings.length <= 2 ? 'partial' : 'thin'),
      score: score,
      limitations: findings,
      evidence_not_truth: true,
      statement: 'A dated observation is evidence of what a seller advertised on a date. It is not '
        + 'a quotation and it is not a market price'
        + (findings.length ? '. Missing here: ' + findings.join(', ') + '.' : '.')
    };
  }

  /* MARKET-02: product equivalence and lexical similarity are different things.
     The words can be nearly identical while the contents differ, so similarity is
     reported as a number and equivalence stays unclaimed unless the source states
     it. */
  function lexicalSimilarity(descriptionA, descriptionB) {
    var tokenise = function (s) {
      return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ')
        .split(' ').filter(function (t) { return t && t.length > 1; });
    };
    var a = tokenise(descriptionA), b = tokenise(descriptionB);
    if (!a.length || !b.length) {
      return { ratio: null, shared: [], statement: 'One description is empty, so no similarity is '
        + 'stated.' };
    }
    var setA = {}, setB = {}, shared = [];
    a.forEach(function (t) { setA[t] = 1; });
    b.forEach(function (t) { setB[t] = 1; });
    Object.keys(setA).forEach(function (t) { if (setB[t]) shared.push(t); });
    var union = Object.keys(setA).length + Object.keys(setB).length - shared.length;
    var ratio = union ? shared.length / union : null;
    return {
      ratio: ratio, shared: shared.sort(),
      statement: 'The two descriptions share ' + shared.length + ' of ' + union + ' words ('
        + (ratio === null ? 'n/a' : Math.round(ratio * 100) + '%').replace('%', '%')
        + '). Similar wording is not product equivalence.'
    };
  }

  function productEquivalence(candidate) {
    candidate = candidate || {};
    var declared = candidate.equivalence_declared;
    var fitment = candidate.equivalence_declared_by || null;
    var similarity = candidate.similarity_ratio === undefined ? null : candidate.similarity_ratio;
    if (declared === true && fitment) {
      return { equivalent: true, basis: 'declared by ' + fitment, similarity: similarity,
        statement: 'Equivalence is declared by ' + fitment + '. The declaration is the basis; '
          + 'similar wording is not.' };
    }
    return {
      equivalent: null,
      basis: declared === true && !fitment ? 'a declaration with no owner named' : 'none',
      similarity: similarity,
      statement: 'Product equivalence is not established. A similar description is not equivalence, '
        + 'and an exact part number on a competitor listing is not proof of the same kit contents.'
    };
  }

  /* MARKET-03: pack and kit contents are normalised only where the source
     supports it. */
  function normalisePack(observation) {
    observation = observation || {};
    var contents = observation.contents || observation.kit_contents || null;
    var declaredUnit = observation.declared_unit || observation.unit_of_measure || null;
    var packQty = toNumberOrNull(observation.pack_quantity !== undefined
      ? observation.pack_quantity : observation.price_per_quantity);
    if (!contents || !contents.length) {
      return {
        normalised: false, unit: declaredUnit, pack_quantity: packQty, contents: null,
        unresolved: ['The contents of the pack or kit are not stated, so a per-piece figure cannot '
          + 'be derived.'],
        statement: 'Not normalised. A price per kit with unstated contents cannot be turned into a '
          + 'price per piece.'
      };
    }
    var pieces = 0, ok = true;
    contents.forEach(function (c) {
      var n = toNumberOrNull(c && (c.quantity !== undefined ? c.quantity : c.qty));
      if (n === null) ok = false; else pieces += n;
    });
    if (!ok || !pieces) {
      return {
        normalised: false, unit: declaredUnit, pack_quantity: packQty, contents: contents,
        unresolved: ['At least one content line carries no quantity, so the pack total is unknown.'],
        statement: 'Not normalised. An incomplete content list is not treated as a complete pack.'
      };
    }
    return {
      normalised: true, unit: declaredUnit, pack_quantity: packQty,
      contents: contents, pieces_per_pack: pieces,
      statement: 'The pack holds ' + pieces + ' piece(s) on the stated contents. The source states '
        + 'the contents, so the per-piece figure is derived from them and not from the part name.'
    };
  }

  function perPiecePrice(amount, pack) {
    var price = toNumberOrNull(amount);
    var p = pack || {};
    if (!p.normalised || !p.pieces_per_pack) {
      return { ok: false, amount_per_piece: null,
        statement: 'The pack is not normalised, so no per-piece price is stated.' };
    }
    if (price === null) {
      return { ok: false, amount_per_piece: null,
        statement: 'No amount was supplied, so no per-piece price is stated.' };
    }
    return { ok: true, amount_per_piece: round2(price / p.pieces_per_pack),
      pieces_per_pack: p.pieces_per_pack,
      statement: 'Derived from a stated pack of ' + p.pieces_per_pack + ' piece(s).' };
  }

  /* MARKET-04: currency, tax and delivery adjustments are auditable. Every step
     is a row, and a missing rate or basis leaves the figure unresolved.

     THE TAX RATE MUST ARRIVE WITH ITS UNIT - read this before calling
     ----------------------------------------------------------------
     A rate of 0.2 and a rate of 20 are the same digits two orders of magnitude
     apart. The difference between them is not a rounding difference: applied to
     an advertised price it is a real figure that overstates a competitor by
     about a fifth. So this rule never guesses the unit from the size of the
     number. `ctx.vat_rate` is the rate expressed as a PERCENTAGE (20 means 20%)
     and `ctx.vat_rate_unit` must say so. A caller holding a fraction multiplies
     it by 100 before calling; it does not pass 0.2 and hope.

     What this replaced: the rule used to compute `value / (1 + rate / 100)` while
     the payload stores the rate as a fraction (`vat: 0.2`). Handing 0.2 to that
     form divides by 1.002, removing 0.2% of tax instead of 20%. Take the payload's
     own `net` column as the witness: it proves the fraction reading on every row
     that has a rate at all, and the old form returned a figure about a fifth too
     high on the rows where the two readings differ. That direction
     makes a competitor look a fifth more expensive than it is, which is exactly
     the inference MARKET-05 exists to prevent.

     The unit is a FACT about the row and it is now carried, not inferred: the
     payload's own `net` column equals `price / (1 + vat)` on 5 of 5 rows that
     state price, vat and net, including all 3 rows where the two units would
     differ, so the payload's rate is a fraction and `src/data/comparable.js`
     converts it and declares the unit. It is `VAT_RATE_UNIT_NOT_STATED` on a row
     whose unit nobody declared - never an assumed one. Do not "helpfully" accept
     a bare 0.2 here: an accepted undeclared unit is the defect coming back. */
  var VAT_RATE_UNITS = ['percent'];

  function adjustToComparable(amount, ctx) {
    ctx = ctx || {};
    var steps = [];
    var value = toNumberOrNull(amount);
    var unresolved = [];

    if (value === null) {
      return { ok: false, value: null, steps: steps, unresolved: ['no amount was supplied'],
        statement: 'No amount was supplied.' };
    }

    var tax = isBlank(ctx.tax) ? 'not stated' : String(ctx.tax).toLowerCase();
    var vatInclusive = tax.indexOf('inclusive') >= 0 || tax.indexOf('incl') >= 0;
    var vatExclusive = tax.indexOf('exclusive') >= 0 || tax.indexOf('excl') >= 0;

    if (vatInclusive) {
      var rate = toNumberOrNull(ctx.vat_rate);
      var unit = isBlank(ctx.vat_rate_unit) ? null : String(ctx.vat_rate_unit).toLowerCase();
      if (rate === null) {
        unresolved.push('the observation is tax inclusive and the rate is not stated');
      } else if (VAT_RATE_UNITS.indexOf(unit) < 0) {
        /* The rate is present and its unit is not declared. It is not converted
           and it is not guessed: the row stays unresolved. A caller that knows
           the rate is a fraction states 'percent' after multiplying by 100. */
        unresolved.push(isBlank(unit)
          ? 'the observation carries a tax rate of ' + rate + ' but does not state whether that is '
            + 'a percentage or a fraction'
          : 'the observation states its tax rate unit as "' + unit + '", which is not one of the '
            + 'units this rule accepts (' + VAT_RATE_UNITS.join(', ') + ')');
      } else {
        var net = value / (1 + rate / 100);
        steps.push({ step: 'remove tax', from: value, to: round2(net),
          rate: rate, rate_unit: 'percent',
          rule: 'divide by 1 + the stated rate of ' + rate + '%, the rate being declared as a '
            + 'percentage on the observation' });
        value = net;
      }
    } else if (vatExclusive) {
      steps.push({ step: 'tax basis', from: value, to: round2(value),
        rule: 'the observation already states a tax-exclusive amount; no adjustment made' });
    } else {
      unresolved.push('the tax basis is not stated, so the amount is not comparable with a '
        + 'tax-exclusive list price');
    }

    var currency = isBlank(ctx.currency) ? null : String(ctx.currency).toUpperCase();
    if (currency && currency !== 'EUR') {
      var fx = toNumberOrNull(ctx.fx_to_eur);
      if (fx === null) {
        unresolved.push('the amount is in ' + currency + ' and no dated rate to EUR was supplied');
      } else if (isBlank(ctx.fx_date)) {
        unresolved.push('a rate to EUR was supplied without the date it was taken on');
      } else {
        var eur = value * fx;
        steps.push({ step: 'convert to EUR', from: round2(value), to: round2(eur),
          rule: 'multiply by the stated rate ' + fx + ' taken on ' + ctx.fx_date });
        value = eur;
      }
    } else if (currency === 'EUR') {
      steps.push({ step: 'currency', from: value, to: round2(value),
        rule: 'the amount is already stated in EUR' });
    } else {
      unresolved.push('the currency is not stated');
    }

    var delivery = isBlank(ctx.delivery_included) ? null : ctx.delivery_included;
    if (delivery === false) {
      var dcost = toNumberOrNull(ctx.delivery_cost_eur);
      if (dcost === null) {
        unresolved.push('the observation excludes delivery and no delivered cost was supplied');
      } else {
        steps.push({ step: 'add delivery', from: round2(value), to: round2(value + dcost),
          rule: 'add the stated delivered cost of ' + dcost + ' EUR' });
        value += dcost;
      }
    } else if (delivery === true) {
      steps.push({ step: 'delivery basis', from: round2(value), to: round2(value),
        rule: 'the observation states a delivered price; no delivery adjustment is made' });
    } else {
      unresolved.push('the delivery basis is not stated, so an undelivered price could be compared '
        + 'with a delivered one');
    }

    return {
      ok: unresolved.length === 0,
      value: unresolved.length === 0 ? round2(value) : null,
      value_before_adjustment: round2(toNumberOrNull(amount)),
      steps: steps,
      unresolved: unresolved,
      statement: unresolved.length === 0
        ? 'Adjusted to a comparable basis over ' + steps.length + ' recorded step(s). Each step and '
          + 'its rule is shown, so the adjustment can be checked.'
        : 'Left unresolved. ' + unresolved.join('; ') + '. An adjusted figure is not stated.'
    };
  }

  /* MARKET-05: outdated or conflicting observations stay visible. */
  function observationConflicts(observations, opts) {
    opts = opts || {};
    var asOf = opts.as_of || null;
    var staleDays = opts.stale_after_days === undefined ? 180 : opts.stale_after_days;
    var list = observations || [];
    var groups = {}, outdated = [];

    list.forEach(function (o) {
      var level = priceLevel((o && o.price_level) || 'competitor_advertised').level;
      var key = (o.part_number || o.part || 'no part') + SEP + level;
      if (!groups[key]) groups[key] = [];
      groups[key].push(o);
      if (asOf && o.retrieved) {
        var then = Date.parse(o.retrieved);
        var now = Date.parse(asOf);
        if (Number.isFinite(then) && Number.isFinite(now)) {
          var days = Math.round((now - then) / 86400000);
          if (days > staleDays) {
            outdated.push({ part_number: o.part_number || o.part || null, seller: o.seller || null,
              retrieved: o.retrieved, age_days: days,
              statement: 'Retrieved ' + days + ' day(s) before ' + asOf + ', past the '
                + staleDays + '-day review point. It stays visible and is labelled as old.' });
          }
        }
      }
    });

    var conflicts = [];
    Object.keys(groups).forEach(function (k) {
      var rows = groups[k];
      var amounts = rows.map(function (r) { return toNumberOrNull(r.price !== undefined ? r.price : r.amount); })
        .filter(function (v) { return v !== null; });
      var distinct = {};
      amounts.forEach(function (v) { distinct[String(v)] = 1; });
      if (Object.keys(distinct).length > 1) {
        conflicts.push({ group: k, amounts: Object.keys(distinct).map(Number).sort(function (a, b) { return a - b; }),
          observations: rows.length,
          statement: rows.length + ' observation(s) on the same price level carry '
            + Object.keys(distinct).length + ' different amounts. Both stay visible; none is '
            + 'selected as the correct one.' });
      }
    });

    return {
      observations: list.length,
      groups: Object.keys(groups).length,
      outdated: outdated,
      conflicts: conflicts,
      statement: list.length + ' observation(s) in ' + Object.keys(groups).length + ' group(s). '
        + outdated.length + ' are older than the ' + staleDays + '-day review point and '
        + conflicts.length + ' group(s) disagree. Old and conflicting observations remain visible '
        + 'rather than being replaced by the newest or the cheapest.'
    };
  }

  /* ------------------------------------------------------------- inventory -- */

  /* What is actually held for each evidence set, and what it cannot support. */
  function inventory() {
    return [
      {
        set: 'National monthly records',
        coverage: 'national monthly rows exist',
        cannot_support: 'submission completeness, channel coverage and the meaning of an absent row',
        statement: 'A chart from this set says no recorded line. It does not say confirmed zero '
          + 'customer demand.'
      },
      {
        set: 'Uploaded billing lines',
        coverage: 'positive net billed euro on exact part numbers, credit and return lines reported separately',
        cannot_support: 'a current net quotation, an approved concession, a contract',
        statement: 'Recorded billing is what was billed. It is not a price authority.'
      },
      {
        set: 'Dated competitor observations',
        coverage: 'seller, date, original amount and currency as retrieved',
        cannot_support: 'an approved net price index or a target price',
        statement: 'Seller-level evidence with its unknowns. One seller offering several brands is '
          + 'not several independent competitors.'
      },
      {
        set: 'Parts registry and relationships',
        coverage: 'catalogue pairings, declared newest numbers and one supersession map',
        cannot_support: 'technical fitment approval, a counted fleet per part, a recoverable loss',
        statement: 'Relationships are exposed with their provenance. Approval to fit is not inferred.'
      },
      {
        set: 'Terms and support register',
        coverage: 'historical terms recorded',
        cannot_support: 'current customer discount agreements, rebates, quantity bands or special '
          + 'price agreements',
        statement: 'Historical terms are not complete, so no concession expiry or valid quote is assumed.'
      }
    ];
  }


  /* REVIEW-04. Original references behind a selected purchasing movement.
     Related rows that match the selected comparison period are listed with the
     quantity and euro the source carries. The remainder is the selected
     movement minus those related deltas, attributed to the case part. A
     quantity-only related row never invents a euro. Descriptive status text is
     kept as the source states it; it is not labelled as missing dealer sales. */
  function periodMatchesComparison(related, compareKey) {
    var months = related && related.prior ? Number(related.prior.months) : null;
    if (compareKey === 'half') return months === 6;
    if (compareKey === 'annual') return months === 12;
    return false;
  }

  function movementContributors(caseObject, compareKey) {
    var cmp = caseObject && caseObject.comparisons ? caseObject.comparisons[compareKey] : null;
    if (!cmp || !cmp.prior || !cmp.current) {
      return {
        ok: false,
        compare: compareKey || null,
        statement: 'No comparison is held for the selected period.',
        movement: null,
        contributors: [],
        remainder: null
      };
    }
    var moveQ = Number(cmp.current.quantity) - Number(cmp.prior.quantity);
    var moveE = round2(Number(cmp.current.eur) - Number(cmp.prior.eur));
    var contributors = [];
    var related = caseObject.relatedEvidence || [];
    for (var i = 0; i < related.length; i++) {
      var r = related[i];
      if (!periodMatchesComparison(r, compareKey)) continue;
      var pq = r.prior && r.prior.quantity != null ? Number(r.prior.quantity) : 0;
      var cq = r.current && r.current.quantity != null ? Number(r.current.quantity) : 0;
      var priorEurHeld = r.prior && r.prior.eur !== null && r.prior.eur !== undefined;
      var currentEurHeld = r.current && r.current.eur !== null && r.current.eur !== undefined;
      var eurHeld = priorEurHeld && currentEurHeld;
      var row = {
        pn: r.pn,
        role: 'related',
        status: r.status || null,
        quantity_delta: cq - pq,
        eur_delta: eurHeld ? round2(Number(r.current.eur) - Number(r.prior.eur)) : null,
        eur_stated: eurHeld,
        period: compareKey,
        period_label: cmp.label,
        prior: { quantity: pq, eur: priorEurHeld ? Number(r.prior.eur) : null },
        current: { quantity: cq, eur: currentEurHeld ? Number(r.current.eur) : null }
      };
      contributors.push(row);
    }
    var sumQ = 0;
    var sumE = 0;
    for (var j = 0; j < contributors.length; j++) {
      sumQ += contributors[j].quantity_delta;
      if (contributors[j].eur_stated) sumE += contributors[j].eur_delta;
    }
    var remainder = {
      pn: caseObject.pn,
      role: 'own_part',
      status: caseObject.bvp || null,
      quantity_delta: moveQ - sumQ,
      eur_delta: round2(moveE - sumE),
      period: compareKey,
      period_label: cmp.label,
      statement: 'Remainder of the selected movement after the related references listed above. '
        + 'This is the case part share of the recorded purchasing movement. A descriptive status is not a claim about missing dealer sales.'
    };
    var quantityOk = (sumQ + remainder.quantity_delta) === moveQ;
    var eurOk = round2(sumE + remainder.eur_delta) === moveE;
    return {
      ok: quantityOk && eurOk,
      compare: compareKey,
      label: cmp.label,
      movement: { quantity: moveQ, eur: moveE, label: cmp.label },
      contributors: contributors,
      remainder: remainder,
      statement: quantityOk && eurOk
        ? 'Displayed contributors plus the stated remainder reproduce the selected movement.'
        : 'Contributors and remainder do not reproduce the selected movement.',
      forbidden_labels: ['missing dealer sales claim']
    };
  }

  /* ---------------------------------------------------- price / quantity / mix -- */

  /* REVIEW-05. Stated method (plain words, returned on every call).

     The compatible set is the case's own part reference plus every relatedEvidence
     reference that carries BOTH a quantity and an euro in BOTH periods of the
     selected comparison. Each such reference i has prior quantity q0i and euro r0i,
     current quantity q1i and euro r1i, and a unit revenue p0i = r0i / q0i and
     p1i = r1i / q1i. A reference with q0i = 0 and q1i > 0 is new; a reference with
     q0i > 0 and q1i = 0 is discontinued; each is shown on its own line with its
     euro and is never folded into the price effect.

     On the continuing references only (q0i > 0 and q1i > 0), with Q0 and Q1 the
     summed quantities and P0 = sum(r0i) / Q0 the prior average unit revenue:
       price effect    = sum over i of (p1i - p0i) x q1i
       quantity effect = (Q1 - Q0) x P0
       mix effect      = sum over i of p0i x (q1i - q0i) - quantity effect
     Those three add up to the continuing references' euro change exactly; the
     arithmetic is returned as continuing_check so the screen can state it.

     Returns are negative billing lines and are shown on their own line. The
     residual is the observed euro change of the selected case comparison minus
     (price + quantity + mix + new + discontinued + returns). It is printed even
     when it is 0. A non-zero residual is reported as not explained by the supplied
     references; it is never absorbed into a component.

     A reference with no quantity in either period, and a reference with no euro in
     either period, are excluded from the compatible set and listed as not
     decomposed with the reason. No euro and no quantity is ever invented for them.

     Label rule returned with every result: this is a unit-revenue change, never a
     list-price increase and never an elasticity. The list price change stays the
     separate offer / price-list field. Fewer than two compatible continuing
     references means the mix effect cannot be separated, and the result says so
     instead of producing a mix number. Margin only, never a factor. */
  var PRICE_QUANTITY_MIX_RULE =
    'The compatible set is the case part plus every related reference that carries both '
    + 'a quantity and an euro in both periods of the selected comparison. A reference with '
    + 'no prior quantity is new and one with no current quantity is discontinued; each is '
    + 'shown on its own line and never folded into price. On the continuing references, the '
    + 'price effect is each reference\'s own unit-revenue change at its current quantity, the '
    + 'quantity effect is the total volume change at the prior average unit revenue, and the '
    + 'mix effect is what is left after those two. The three add up to the continuing '
    + 'references\' euro change exactly, and that sum is shown. The residual is the observed '
    + 'euro change of the comparison minus every component above; it is printed even when it '
    + 'is zero, and a non-zero residual is not explained by the supplied references. This is a '
    + 'unit-revenue change: it is not a like-for-like list-price change and it is not an '
    + 'elasticity. The list price change stays the separate offer and price-list field. Margin '
    + 'only: no factor is used or shown.';

  function priceQuantityMix(caseObject, compareKey) {
    caseObject = caseObject || {};
    var cmp = caseObject.comparisons ? caseObject.comparisons[compareKey] : null;
    var held = !!(cmp && cmp.prior && cmp.current);
    var out = {
      ok: false,
      available: false,
      compare: compareKey || null,
      label: held ? cmp.label : null,
      method: PRICE_QUANTITY_MIX_RULE,
      label_rule: 'Unit-revenue change, not a list-price increase and not an elasticity. The list price change stays the separate offer and price-list field.',
      observed_change_eur: null,
      components: {
        price_eur: null,
        quantity_eur: null,
        mix_eur: null,
        new_eur: null,
        discontinued_eur: null,
        returns_eur: null,
        residual_eur: null
      },
      continuing: [],
      new_references: [],
      discontinued_references: [],
      returns: [],
      not_decomposed: [],
      continuing_count: 0,
      continuing_change_eur: null,
      continuing_check: null,
      mix_state: 'unavailable',
      statement: ''
    };
    if (!held) {
      out.statement = 'No comparison is held for the selected period.';
      return out;
    }

    /* The case's own observed movement for this comparison is the same figure
       REVIEW-04 calls the selected movement. */
    var observed = round2(Number(cmp.current.eur) - Number(cmp.prior.eur));
    out.observed_change_eur = observed;
    out.available = true;

    var refs = [];
    refs.push({
      pn: caseObject.pn, role: 'own_part', status: caseObject.bvp || null,
      prior: cmp.prior, current: cmp.current
    });
    var related = caseObject.relatedEvidence || [];
    for (var i = 0; i < related.length; i++) {
      var r = related[i];
      if (!periodMatchesComparison(r, compareKey)) continue;
      refs.push({ pn: r.pn, role: 'related', status: r.status || null, prior: r.prior || {}, current: r.current || {} });
    }

    var priceEffect = 0;
    var mixBase = 0;
    var Q0 = 0;
    var Q1 = 0;
    var R0 = 0;
    var R1 = 0;

    for (var k = 0; k < refs.length; k++) {
      var ref = refs[k];
      var q0 = toNumberOrNull(ref.prior.quantity);
      var q1 = toNumberOrNull(ref.current.quantity);
      var r0 = toNumberOrNull(ref.prior.eur);
      var r1 = toNumberOrNull(ref.current.eur);

      if (q0 === null || q1 === null) {
        out.not_decomposed.push({
          pn: ref.pn, role: ref.role, reason: 'not decomposed: no quantity in the source',
          quantity_prior: q0, quantity_current: q1
        });
        continue;
      }
      if (r0 === null || r1 === null) {
        out.not_decomposed.push({
          pn: ref.pn, role: ref.role, reason: 'not decomposed: no euro in the source',
          quantity_prior: q0, quantity_current: q1
        });
        continue;
      }
      if (r0 < 0 || r1 < 0) {
        out.returns.push({
          pn: ref.pn, role: ref.role, quantity_delta: q1 - q0, eur: round2(r1 - r0),
          statement: 'Return / negative billing line in the source; shown on its own'
        });
        continue;
      }
      if (q0 === 0 && q1 > 0) {
        out.new_references.push({
          pn: ref.pn, role: ref.role, quantity_prior: 0, quantity_current: q1,
          eur: round2(r1 - r0), statement: 'New reference: no quantity in the prior period'
        });
        continue;
      }
      if (q0 > 0 && q1 === 0) {
        out.discontinued_references.push({
          pn: ref.pn, role: ref.role, quantity_prior: q0, quantity_current: 0,
          eur: round2(r1 - r0), statement: 'Discontinued reference: no quantity in the current period'
        });
        continue;
      }
      if (q0 === 0 && q1 === 0) {
        out.not_decomposed.push({
          pn: ref.pn, role: ref.role, reason: 'not decomposed: no quantity in either period',
          quantity_prior: q0, quantity_current: q1
        });
        continue;
      }

      /* q0 > 0 and q1 > 0: a continuing reference. */
      var p0 = r0 / q0;
      var p1 = r1 / q1;
      priceEffect += (p1 - p0) * q1;
      mixBase += p0 * (q1 - q0);
      Q0 += q0;
      Q1 += q1;
      R0 += r0;
      R1 += r1;
      out.continuing.push({
        pn: ref.pn, role: ref.role, status: ref.status,
        prior_quantity: q0, current_quantity: q1,
        prior_eur: round2(r0), current_eur: round2(r1),
        prior_unit_revenue: round2(p0), current_unit_revenue: round2(p1),
        unit_revenue_change: round2(p1 - p0),
        quantity_delta: q1 - q0,
        eur_delta: round2(r1 - r0),
        price_effect_eur: round2((p1 - p0) * q1)
      });
    }

    out.continuing_count = out.continuing.length;

    var P0 = Q0 > 0 ? R0 / Q0 : 0;
    var quantityEffect = Q0 > 0 ? (Q1 - Q0) * P0 : 0;
    var mixEffect = out.continuing_count >= 2 ? mixBase - quantityEffect : null;
    out.mix_state = mixEffect === null
      ? (out.continuing_count === 1
        ? 'mix: unavailable, only one compatible reference'
        : 'mix: unavailable, no compatible continuing reference')
      : 'mix separated';

    var sum = function (list, key) {
      var t = 0;
      for (var x = 0; x < list.length; x++) t += list[x][key];
      return t;
    };
    var priceEur = round2(priceEffect);
    var quantityEur = round2(quantityEffect);
    var mixEur = mixEffect === null ? null : round2(mixEffect);
    var newEur = round2(sum(out.new_references, 'eur'));
    var discontinuedEur = round2(sum(out.discontinued_references, 'eur'));
    var returnsEur = round2(sum(out.returns, 'eur'));

    out.components = {
      price_eur: priceEur,
      quantity_eur: quantityEur,
      mix_eur: mixEur,
      new_eur: newEur,
      discontinued_eur: discontinuedEur,
      returns_eur: returnsEur,
      residual_eur: round2(observed - (priceEur + quantityEur
        + (mixEur === null ? 0 : mixEur) + newEur + discontinuedEur + returnsEur))
    };

    out.continuing_change_eur = round2(R1 - R0);
    out.continuing_check = round2(priceEur + quantityEur + (mixEur === null ? 0 : mixEur));
    out.continuing_reconciles = out.continuing_check === out.continuing_change_eur;

    var identity = out.components.price_eur + out.components.quantity_eur
      + (out.components.mix_eur === null ? 0 : out.components.mix_eur)
      + out.components.new_eur + out.components.discontinued_eur
      + out.components.returns_eur + out.components.residual_eur;
    out.ok = round2(identity) === observed;

    out.statement = (out.continuing_reconciles
      ? 'Price, quantity and mix add up to the continuing references\' euro change exactly. '
      : 'Price, quantity and mix do NOT reproduce the continuing references\' euro change. ')
      + out.continuing_count + ' compatible continuing reference(s). '
      + (mixEffect === null
        ? out.mix_state + '. '
        : '')
      + (out.components.residual_eur === 0
        ? 'Residual 0.00: every euro of the observed change is explained by the supplied references. '
        : 'Residual is ' + out.components.residual_eur.toFixed(2)
          + ' euro: not explained by the supplied references. ');
    return out;
  }

  /* ------------------------------------------------------------ purchasing activity -- */

  /* Stated rule (plain words, returned on every call):
     Covered months are those whose billingState is "recorded" or "no recorded line".
     Months marked "outside supplied period", and months absent from the series, are not
     covered: they are marked missing and never produce a lapsed flag. Descriptive flags
     only Ã¢â‚¬â€ no rating, no score, no 0-100.
     Regular: recorded activity in every covered month (or with gaps shorter than three).
     Intermittent: recorded months mixed with covered no-recorded-line gaps, not a clean
     terminal lapse of three or more covered months.
     New: the first recorded month appears after three or more covered no-recorded-line
     months at the start of the covered window.
     Lapsed: at least one earlier recorded month, then three or more consecutive covered
     no-recorded-line months at the end of the covered window. Outside / absent months
     never count toward that terminal run.
     A supersession, declared newest-number, or combined-account relationship that explains
     a drop on the case part and a rise on a related part is surfaced as an explanation;
     it does not become a false lost/new pair. */

  var PURCHASING_RULE =
    'Covered months are those with billingState "recorded" or "no recorded line". '
    + 'Months marked "outside supplied period", and months absent from the series, are '
    + 'marked missing and never produce a lapsed flag. Regular means recorded activity '
    + 'across the covered window without a terminal covered gap of three or more months. '
    + 'Intermittent means recorded months mixed with covered gaps that are not a clean '
    + 'terminal lapse. New means the first recorded month follows three or more covered '
    + 'no-recorded-line months at the start. Lapsed means earlier recorded activity then '
    + 'three or more consecutive covered no-recorded-line months at the end of the covered '
    + 'window. Flags are descriptive only: no rating and no score. '
    + 'Supersession, newest-number and combined-account changes are explanations, not a '
    + 'false lost/new pair.';

  function purchasingActivity(caseObject) {
    caseObject = caseObject || {};
    var series = Array.isArray(caseObject.series) ? caseObject.series.slice() : [];
    series.sort(function (a, b) {
      return String(a.period || '').localeCompare(String(b.period || ''));
    });

    var months = [];
    var number_changes = [];
    var prevCoveredQty = null;
    var coveredStates = [];

    for (var i = 0; i < series.length; i++) {
      var row = series[i] || {};
      var state = row.billingState || null;
      var covered = state === 'recorded' || state === 'no recorded line';
      var missing = !covered; /* outside supplied period, unknown, or absent-from-coverage */
      var qty = row.billingQuantity;
      var qtyNum = (qty === null || qty === undefined || qty === '') ? null : Number(qty);
      var flag = null;
      if (covered && state === 'no recorded line') flag = 'no_purchase_in_covered_month';
      if (covered && state === 'recorded') flag = 'recorded';
      if (!covered && state === 'outside supplied period') flag = 'outside_supplied_period';
      /* Never attach 'lapsed' to a non-covered month. */
      months.push({
        period: row.period || null,
        billingState: state,
        covered: covered,
        missing: missing,
        quantity: qtyNum,
        flag: flag
      });
      if (covered) {
        coveredStates.push(state);
        if (prevCoveredQty !== null && qtyNum !== null && qtyNum !== prevCoveredQty) {
          number_changes.push({
            period: row.period,
            from: prevCoveredQty,
            to: qtyNum,
            statement: 'Quantity changed from ' + prevCoveredQty + ' to ' + qtyNum
              + ' in covered month ' + row.period + '.'
          });
        }
        if (qtyNum !== null) prevCoveredQty = qtyNum;
        else if (state === 'no recorded line') prevCoveredQty = 0;
      }
    }

    /* Pattern from covered months only. */
    var pattern = null;
    var flags = [];
    if (coveredStates.length) {
      var firstRec = -1;
      var lastRec = -1;
      for (var c = 0; c < coveredStates.length; c++) {
        if (coveredStates[c] === 'recorded') {
          if (firstRec < 0) firstRec = c;
          lastRec = c;
        }
      }
      var leadingGaps = firstRec < 0 ? coveredStates.length : firstRec;
      var trailingGaps = 0;
      if (lastRec >= 0) {
        for (var t = coveredStates.length - 1; t > lastRec; t--) {
          if (coveredStates[t] === 'no recorded line') trailingGaps++;
          else break;
        }
      }
      var gapInside = false;
      if (firstRec >= 0) {
        for (var g = firstRec; g <= lastRec; g++) {
          if (coveredStates[g] === 'no recorded line') { gapInside = true; break; }
        }
      }

      if (firstRec < 0) {
        pattern = null;
        flags.push('no_recorded_activity_in_covered_window');
      } else if (leadingGaps >= 3 && trailingGaps < 3) {
        pattern = 'new';
        flags.push('new');
      } else if (trailingGaps >= 3) {
        pattern = 'lapsed';
        flags.push('lapsed');
      } else if (gapInside) {
        pattern = 'intermittent';
        flags.push('intermittent');
      } else {
        pattern = 'regular';
        flags.push('regular');
      }
    }

    /* Relationship explanations: supersession / newest / combined-account. */
    var explanations = [];
    var rels = (caseObject.packEvidence && caseObject.packEvidence.relationships) || [];
    var related = caseObject.relatedEvidence || [];
    var false_pair_avoided = false;

    for (var r = 0; r < rels.length; r++) {
      var raw = rels[r] || {};
      var cls = classifyRelationship(raw);
      var text = String(raw.relationship_type || '').toLowerCase();
      var isTransfer = cls.kind === 'supersession'
        || cls.kind === 'declared_newest_number'
        || cls.kind === 'combined_account'
        || text.indexOf('combined-account') >= 0
        || text.indexOf('combined account') >= 0
        || text.indexOf('newest') >= 0
        || text.indexOf('supersession') >= 0;
      if (!isTransfer) continue;

      var relatedPn = raw.part_number_b || raw.part_number_a || null;
      if (relatedPn && relatedPn === caseObject.pn) {
        relatedPn = raw.part_number_a === caseObject.pn ? raw.part_number_b : raw.part_number_a;
      }
      var relatedRow = null;
      for (var re = 0; re < related.length; re++) {
        if (related[re] && related[re].pn === relatedPn) { relatedRow = related[re]; break; }
      }
      var priorQ = relatedRow && relatedRow.prior ? Number(relatedRow.prior.quantity || 0) : 0;
      var currQ = relatedRow && relatedRow.current ? Number(relatedRow.current.quantity || 0) : 0;
      var ownHalf = caseObject.comparisons && caseObject.comparisons.half;
      var ownDrop = false;
      if (ownHalf && ownHalf.prior && ownHalf.current) {
        ownDrop = Number(ownHalf.current.quantity) < Number(ownHalf.prior.quantity);
      }
      var relatedRise = currQ > priorQ;

      var kindLabel = cls.kind === 'combined_account' ? 'combined-account change'
        : (cls.kind === 'declared_newest_number' || text.indexOf('newest') >= 0)
          ? 'declared newest-number / supersession'
          : (cls.kind === 'supersession' ? 'supersession' : cls.kind);

      if (text.indexOf('combined') >= 0) kindLabel = 'combined-account change';

      var statement = 'A ' + kindLabel + ' links ' + (caseObject.pn || 'the case part')
        + ' to ' + (relatedPn || 'a related part reference') + '. ';
      if (ownDrop && relatedRise) {
        statement += 'The case part quantity fell while the related reference rose in the same '
          + 'comparison window. That movement is explained by the relationship; it is not a '
          + 'false lost/new pair.';
        false_pair_avoided = true;
        /* Strip lost/new/lapsed flags that would form a false pair. */
        flags = flags.filter(function (f) {
          return f !== 'lost' && f !== 'new' && f !== 'lapsed';
        });
        if (pattern === 'lapsed' || pattern === 'new') pattern = 'intermittent';
        flags.push('relationship_explained_transfer');
      } else {
        statement += 'The relationship is held as an explanation alongside the covered monthly activity.';
        false_pair_avoided = true;
      }

      explanations.push({
        kind: kindLabel,
        related_pn: relatedPn,
        relationship_type: raw.relationship_type || null,
        statement: statement
      });
    }

    if (explanations.length && !false_pair_avoided) false_pair_avoided = true;

    return {
      rule: PURCHASING_RULE,
      pattern: pattern,
      flags: flags,
      months: months,
      number_changes: number_changes,
      explanations: explanations,
      false_pair_avoided: false_pair_avoided,
      rating: null,
      score: null
    };
  }


  /* ------------------------------------------------------------ next action plan -- */

  /* Routes a review question to the appropriate next action. Descriptive only.
     Routes: price_assessment, bvp_application_check, supply_timing_check,
     evidence_request, justified_no_action, purchasing_review.
     A supply explanation never produces a discount route. An unresolved price
     comparison still permits a scoped application or purchasing review.
     Competing explanations and unknown are retained. A family decline without
     linked evidence never becomes a precise reason. */

  function nextActionPlan(caseObject) {
    caseObject = caseObject || {};
    var explanations = Array.isArray(caseObject.reviewExplanations)
      ? caseObject.reviewExplanations.slice()
      : [];
    var routes = [];
    var competing = [];
    var unknown = [];
    var seen = {};

    function addRoute(id, label, why, kind) {
      if (seen[id]) return;
      seen[id] = true;
      routes.push({ id: id, label: label, why: why, kind: kind || id });
    }

    for (var i = 0; i < explanations.length; i++) {
      var ex = explanations[i] || {};
      var kind = String(ex.kind || '').toLowerCase();
      var status = String(ex.status || '').toLowerCase();
      var statement = ex.statement || '';
      var linked = Array.isArray(ex.linked_evidence) ? ex.linked_evidence : [];

      if (status === 'competing') {
        competing.push({ kind: kind, statement: statement, linked_evidence: linked });
      }
      if (status === 'unknown' || kind === 'unknown') {
        unknown.push({ kind: kind || 'unknown', statement: statement, linked_evidence: linked });
      }

      if (kind === 'supply' || kind === 'timing' || kind === 'supply_timing') {
        addRoute(
          'supply_timing_check',
          'Supply / timing check',
          'Relevant because a supply or timing explanation is held: ' + statement,
          'supply_timing_check'
        );
        /* Never a discount from supply. */
        continue;
      }

      if (kind === 'price_comparison' || kind === 'price') {
        addRoute(
          'price_assessment',
          'Price assessment',
          'Relevant because the price comparison is ' + (status || 'open') + ': ' + statement,
          'price_assessment'
        );
        if (status === 'unresolved') {
          addRoute(
            'purchasing_review',
            'Scoped purchasing review',
            'Relevant because an unresolved price comparison still permits a scoped purchasing review while the price source is settled.',
            'purchasing_review'
          );
        }
        continue;
      }

      if (kind === 'application' || kind === 'bvp' || kind === 'bvp_application') {
        addRoute(
          'bvp_application_check',
          'BVP / application check',
          'Relevant because an application or BVP question is held: ' + statement,
          'bvp_application_check'
        );
        continue;
      }

      if (kind === 'evidence_request' || (status === 'unknown' && linked.length === 0)) {
        addRoute(
          'evidence_request',
          'Evidence request',
          'Relevant because required evidence is not held: ' + (statement || 'unnamed gap'),
          'evidence_request'
        );
        continue;
      }

      if (kind === 'justified_no_action' || kind === 'no_action') {
        addRoute(
          'justified_no_action',
          'Justified no action',
          'Relevant because the held explanation does not justify a commercial change: ' + statement,
          'justified_no_action'
        );
        continue;
      }
    }

    /* Unresolved list conflict on the pack also opens price assessment + scoped review. */
    var pe = caseObject.packEvidence || {};
    if (pe.listConflict) {
      addRoute(
        'price_assessment',
        'Price assessment',
        'Relevant because the pack records a list conflict; the applicable customer net price is not settled.',
        'price_assessment'
      );
      addRoute(
        'purchasing_review',
        'Scoped purchasing review',
        'Relevant because an unresolved price comparison still permits a scoped purchasing review.',
        'purchasing_review'
      );
    }

    /* Catalogue pairing / BVP without fitment approval -> application check. */
    var rels = pe.relationships || [];
    for (var r = 0; r < rels.length; r++) {
      var cls = classifyRelationship(rels[r] || {});
      var fit = fitmentStatus(rels[r] || {});
      if (cls.kind === 'catalogue_pairing' || cls.kind === 'declared_newest_number' || cls.kind === 'supersession') {
        if (!fit || fit.approved !== true) {
          addRoute(
            'bvp_application_check',
            'BVP / application check',
            'Relevant because a ' + cls.kind.replace(/_/g, ' ')
              + ' is held without stated fitment approval.',
            'bvp_application_check'
          );
        }
      }
    }

    if (!routes.length) {
      addRoute(
        'evidence_request',
        'Evidence request',
        'Relevant because no explained next action is held on this case.',
        'evidence_request'
      );
    }

    /* Family decline: precise reason only with linked evidence. */
    var precise_family_decline = null;
    var fd = caseObject.familyDecline;
    if (fd && fd.precise_reason) {
      var fdLinked = Array.isArray(fd.linked_evidence) ? fd.linked_evidence : [];
      if (fdLinked.length > 0) {
        precise_family_decline = {
          reason: fd.precise_reason,
          linked_evidence: fdLinked
        };
      } else {
        unknown.push({
          kind: 'family_decline',
          statement: 'A precise family decline reason was offered without linked evidence and is not accepted.',
          linked_evidence: []
        });
        addRoute(
          'evidence_request',
          'Evidence request',
          'Relevant because a family-level decline was asserted without linked evidence.',
          'evidence_request'
        );
      }
    }

    /* Hard rule: supply explanation never yields a discount route. */
    var hasSupply = explanations.some(function (e) {
      var k = String((e && e.kind) || '').toLowerCase();
      return k === 'supply' || k === 'timing' || k === 'supply_timing';
    });
    if (hasSupply) {
      routes = routes.filter(function (r) {
        return r.id !== 'discount' && r.id !== 'automatic_discount'
          && !/\bdiscount\b/i.test(r.label || '')
          && !/\bdiscount\b/i.test(r.why || '');
      });
    }

    return {
      routes: routes,
      competing_explanations: competing,
      unknown: unknown,
      precise_family_decline: precise_family_decline,
      statement: 'Next actions are routed from the held explanations. Competing explanations and unknown are kept. A supply explanation never produces a discount.'
    };
  }

  var API = {
    reference: reference,
    describePeriod: describePeriod,
    periodOf: periodOf,
    PRICE_LEVELS: PRICE_LEVELS,
    priceLevel: priceLevel,
    assertSamePriceLevel: assertSamePriceLevel,
    comparability: comparability,
    priceComparability: priceComparability,
    reconcile: reconcile,
    conservationOfTotals: conservationOfTotals,
    conservationOfLedger: conservationOfLedger,
    RELATIONSHIP_KINDS: RELATIONSHIP_KINDS,
    relationshipKind: relationshipKind,
    classifyRelationship: classifyRelationship,
    fitmentStatus: fitmentStatus,
    relationships: relationships,
    relationshipSummary: relationshipSummary,
    makeRangeRelationshipLedger: makeRangeRelationshipLedger,
    interchangeablePairStatus: interchangeablePairStatus,
    rangeCommercialRole: rangeCommercialRole,
    RANGE_RELATIONSHIP_TYPES: RANGE_RELATIONSHIP_TYPES,
    exactRangeComparison: exactRangeComparison,
    rangeBasket: rangeBasket,
    rangeTransferSplit: rangeTransferSplit,
    withdrawRangeRelationship: withdrawRangeRelationship,
    rangeWithdrawalImpact: rangeWithdrawalImpact,
    canReuseApplicationApproval: canReuseApplicationApproval,
    partReference: partReference,
    makeRelationshipLedger: makeRelationshipLedger,
    makeStageState: makeStageState,
    makeImportLog: makeImportLog,
    evidenceStrength: evidenceStrength,
    lexicalSimilarity: lexicalSimilarity,
    productEquivalence: productEquivalence,
    normalisePack: normalisePack,
    perPiecePrice: perPiecePrice,
    adjustToComparable: adjustToComparable,
    statesNoValue: statesNoValue,
    observationConflicts: observationConflicts,
    inventory: inventory,
    movementContributors: movementContributors,
    priceQuantityMix: priceQuantityMix,
    purchasingActivity: purchasingActivity,
    nextActionPlan: nextActionPlan,
    periodMatchesComparison: periodMatchesComparison,
    SEP: SEP
  };

  root.AIMEvidence = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
