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
     is a row, and a missing rate or basis leaves the figure unresolved. */
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
      if (rate === null) {
        unresolved.push('the observation is tax inclusive and the rate is not stated');
      } else {
        var net = value / (1 + rate / 100);
        steps.push({ step: 'remove tax', from: value, to: round2(net),
          rule: 'divide by 1 + the stated rate of ' + rate + '%' });
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
    SEP: SEP
  };

  root.AIMEvidence = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
