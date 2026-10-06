/* ===========================================================================
   Candidate set: reporting basis, coverage vs approval, line of descent
   (F10, DATA-02, DATA-05, DATA-06, DATA-08; and RANGE-01).

   What was wrong in v0.3
     The screen rendered the first 300 of 10,543 records with no search and no
     paging, so a sample wore the word "screened". It counted 15 customer-part
     rows and called them 15 parts. It called cost-and-list completeness
     "decision-ready". It gave no period for the records at all. And the only
     cost column it carries is a forward October basis, on records that state no
     period at all - so a forward cost was being shown beside unperiodised
     quantities without saying so.

   What this does
     - searches and pages the whole permitted set;
     - declares the reporting basis, and records the missing period as unresolved
       instead of inferring one from similar-looking values;
     - reports row counts and distinct part numbers as two different numbers;
     - reports cost/list completeness as completeness, separately from approval,
       and names the basis the cost column is on;
     - keeps commercial priority and evidence readiness apart, and never merges
       them into one score;
     - keeps distributor, purchasing account and site distinct, and never blends
       ITUK with IUK or UMI with UTI;
     - carries a line of descent for the set, so a correction can be traced and a
       repeated import cannot multiply it;
     - refuses to promote a candidate to a review case while the source cannot
       support it, and says which item is missing.
   =========================================================================== */
(function (root) {
  'use strict';

  var fs = null;
  try { fs = require('node:fs'); } catch (e) { fs = null; }
  var pathMod = null;
  try { pathMod = require('node:path'); } catch (e) { pathMod = null; }

  var evidence = (typeof module === 'object' && module.exports)
    ? require('./evidence.js') : root.AIMEvidence;
  var manifest = (typeof module === 'object' && module.exports)
    ? require('./manifest.js') : root.AIMManifest;

  var SEP = '\u001f';

  /* The cost column the candidate records actually carry. Named once, with its
     basis, so it cannot be mistaken for a historical or accounting cost. */
  var COST_COLUMN = 'verified_cost_eur_oct26';
  var COST_COLUMN_BASIS = 'OCT26';
  var COST_COLUMN_STATEMENT = 'The only cost column on these records is on the October 2026 '
    + 'forward basis. The records state no period, so a forward cost is being shown beside '
    + 'quantities that are not periodised. It is a forward reference figure, not a historical or '
    + 'accounting cost.';

  function norm(v) { return v === null || v === undefined ? '' : String(v).toLowerCase(); }
  function isBlank(v) {
    return v === null || v === undefined || (typeof v === 'string' && v.trim() === '');
  }
  function toNumberOrNull(v) {
    if (isBlank(v)) return null;
    var n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  function round2(x) { return x === null ? null : Math.round(x * 100) / 100; }

  /* ------------------------------------------------------------- sorting -- */

  function numericSort(rows, key, direction) {
    var dir = direction === 'asc' ? 1 : -1;
    return rows.slice().sort(function (a, b) {
      var av = a[key], bv = b[key];
      var an = (av === null || av === undefined || !Number.isFinite(Number(av)));
      var bn = (bv === null || bv === undefined || !Number.isFinite(Number(bv)));
      if (an && bn) return 0;
      if (an) return 1;              /* an absent value sorts last, never as zero */
      if (bn) return -1;
      if (Number(bv) !== Number(av)) return dir * (Number(bv) - Number(av));
      return String(a.part_number).localeCompare(String(b.part_number));
    });
  }

  /* ---------------------------------------------------------- recognised -- */

  /* Where a period could live, if the source ever carries one. The list is a
     check, not a guess: if none of these fields exists, the basis is undeclared. */
  var PERIOD_FIELDS = ['period', 'reporting_period', 'reporting_period_start',
    'period_start', 'period_end', 'date_from', 'date_to', 'year', 'half',
    'billing_period'];

  function periodFieldScan(rows) {
    var found = PERIOD_FIELDS.filter(function (f) {
      return (rows || []).some(function (r) { return r && r[f] !== undefined && r[f] !== null; });
    });
    return found;
  }

  /* The reporting basis of the set. Undeclared stays undeclared. */
  function reportingBasis(rows) {
    rows = rows || [];
    if (!rows.length) {
      return {
        declared: false, fields: [], values: [], row_count: 0,
        period: null, period_state: 'undeclared',
        screen_period_count: 0, screen_period_note: null,
        statement: 'The candidate set is empty, so it declares no reporting period and none has '
          + 'been inferred.'
      };
    }
    var found = periodFieldScan(rows);
    if (found.length) {
      var values = {};
      rows.forEach(function (r) {
        found.forEach(function (f) {
          if (r && r[f] !== undefined && r[f] !== null) values[f + '=' + r[f]] = 1;
        });
      });
      return {
        declared: true, fields: found, values: Object.keys(values),
        row_count: rows.length,
        period: Object.keys(values).length === 1 ? Object.keys(values)[0] : null,
        period_state: Object.keys(values).length === 1 ? 'declared' : 'declared per row',
        screen_period_count: 0, screen_period_note: null,
        statement: 'The candidate records declare their own reporting period on '
          + found.join(', ') + '.'
      };
    }
    return {
      declared: false, fields: [], values: [],
      row_count: rows.length,
      period: null, period_state: 'undeclared',
      screen_period_count: 0,
      screen_period_note:
        'The screen rule is described as running separately on CY2025/CY2024 and on H1 2026/H1 2025, '
        + 'but the exported rows carry none of those period values. The window is described and not '
        + 'carried, so the records cannot be assigned to either comparison.',
      statement: 'The candidate records do not carry a reporting period. The screening basis is '
        + 'therefore undeclared, and no period has been inferred from similar-looking values. '
        + 'The worked cases use their own explicitly stated periods and are not interchangeable '
        + 'with this screen. This is recorded as unresolved, not guessed.'
    };
  }

  /* The screen rule that produced the rows, with its provenance and its limits. */
  function screenRule(rule, rows) {
    rule = rule || {};
    rows = rows || [];
    var mismatch = null;
    var m = String(rule.coverage || '').match(/(\d[\d,]*)\s+part numbers/i);
    var declaredParts = m ? Number(m[1].replace(/,/g, '')) : null;
    var actualParts = uniqueParts(rows.filter(function (r) {
      return !isBlank(r[COST_COLUMN]);
    })).count;
    if (declaredParts !== null && actualParts !== declaredParts) {
      mismatch = {
        declared: declaredParts, observed: actualParts,
        statement: 'The screen rule states cost is held for ' + declaredParts + ' part number(s). '
          + 'The exported rows hold a cost for ' + actualParts + '. The difference is reported and '
          + 'neither figure is preferred.'
      };
    }
    return {
      what: rule.what || null,
      coverage: rule.coverage || null,
      competitor_gap: rule.competitorGap || null,
      not_what: rule.notA || null,
      declared_part_numbers_with_cost: declaredParts,
      observed_part_numbers_with_cost: actualParts,
      observed_rows_with_a_cost: rows.filter(function (r) { return !isBlank(r[COST_COLUMN]); }).length,
      mismatch: mismatch,
      status: 'proposed screening rule, not an approved commercial threshold',
      statement: 'The screen is a proposed rule. It selects candidates for review; it does not '
        + 'approve a price, a cost or a target.'
    };
  }

  /* ------------------------------------------------------------ coverage -- */

  function uniqueParts(rows) {
    var seen = {}, examples = [];
    (rows || []).forEach(function (r) {
      if (!r || isBlank(r.part_number)) return;
      if (!seen[r.part_number]) { seen[r.part_number] = 1; examples.push(r.part_number); }
    });
    return { count: examples.length, part_numbers: examples.sort() };
  }

  function uniqueValues(rows, field) {
    var seen = {};
    (rows || []).forEach(function (r) {
      if (!r) return;
      var v = r[field];
      if (!isBlank(v)) seen[String(v)] = 1;
    });
    return Object.keys(seen).sort();
  }

  /* The cost record list, so a coverage count can say whether every screened
     part with a cost is also in the cost register, and the other way round. */
  function verifiedCostPartNumbers(payload) {
    return uniqueParts(((payload || {}).verifiedCosts || []).map(function (r) {
      return { part_number: r.part_number };
    })).part_numbers;
  }

  /* Cost/list completeness, described for what it is. Never "decision ready". */
  function coverage(rows, allRows, opts) {
    opts = opts || {};
    rows = rows || [];
    var withCost = rows.filter(function (r) { return !isBlank(r[COST_COLUMN]); });
    var withList = rows.filter(function (r) { return !isBlank(r.list_eur); });
    var both = rows.filter(function (r) {
      return !isBlank(r[COST_COLUMN]) && !isBlank(r.list_eur);
    });
    var costParts = uniqueParts(withCost);
    var listParts = uniqueParts(withList);
    var bothParts = uniqueParts(both);
    var allParts = uniqueParts(rows);
    var competitorRows = rows.filter(function (r) { return r.competitor_evidence === 'held'; });
    var competitorParts = uniqueParts(competitorRows);
    var unidentified = rows.filter(function (r) { return isBlank(r.part_number); });

    var register = opts.payload ? verifiedCostPartNumbers(opts.payload) : null;
    var crossCheck = null;
    if (register) {
      var screenedWithCost = costParts.part_numbers;
      crossCheck = {
        cost_register_parts: register.length,
        screened_parts_with_a_cost: screenedWithCost.length,
        in_register_not_screened: register.filter(function (p) { return screenedWithCost.indexOf(p) < 0; }),
        screened_not_in_register: screenedWithCost.filter(function (p) { return register.indexOf(p) < 0; }),
        statement: 'The cost register holds ' + register.length + ' part record(s) and the screen '
          + 'carries a cost on ' + screenedWithCost.length + '. The two lists are compared rather '
          + 'than assumed equal.'
      };
    }

    return {
      rows_total: (allRows || rows).length,
      rows_matching: rows.length,
      rows_eligible: rows.filter(function (r) { return r.eligible !== false; }).length,
      rows_unidentified: unidentified.length,
      eligible_gap: unidentified.length,
      unidentified_rows: unidentified.length
        ? unidentified.length + ' matching row(s) carry no part reference on the source line and '
          + 'therefore cannot be counted as a part. They stay in the row count and are excluded from '
          + 'every unique-part count, because a row without a part reference is not a part.'
        : 'Every matching row carries a part reference.',
      unique_parts: allParts.count,
      rows_with_cost_and_list: both.length,
      rows_with_cost: withCost.length,
      rows_with_list: withList.length,
      unique_parts_with_cost: costParts.count,
      unique_parts_with_list: listParts.count,
      unique_parts_with_cost_and_list: bothParts.count,
      rows_with_competitor_evidence: competitorRows.length,
      unique_parts_with_competitor_evidence: competitorParts.count,
      cost_column: COST_COLUMN,
      cost_column_basis: COST_COLUMN_BASIS,
      cost_column_statement: COST_COLUMN_STATEMENT,
      cost_register_cross_check: crossCheck,
      coverage_pct: rows.length ? 100 * withCost.length / rows.length : null,
      /* Deliberately named for what it measures. */
      cost_and_list_coverage: 'price and cost records are held for ' + both.length
        + ' of ' + rows.length + ' matching rows, which is '
        + bothParts.count + ' distinct part numbers. That is coverage, '
        + 'not approval of a price or of a cost.',
      rows_vs_parts: rows.length + ' row(s) and ' + allParts.count + ' distinct part number(s) are '
        + 'two different counts. Cost coverage is held on ' + costParts.count + ' distinct part '
        + 'number(s), not on ' + withCost.length + ' unique parts.'
        + (unidentified.length ? ' ' + unidentified.length + ' row(s) carry no part reference and '
          + 'are in neither part count.' : ''),
      not_approval: 'A row with a cost and a list is a candidate for review. It is not a cleared '
        + 'price decision, and it is not evidence that a competitor quotation exists.'
    };
  }

  /* Cost and list completeness, separately from approval. There is no approval
     field on a candidate record, so approval is not claimed for any of them. */
  function approvalStatus(rows) {
    rows = rows || [];
    var withFlag = rows.filter(function (r) { return !isBlank(r.approved) || !isBlank(r.approval); });
    var completeness = rows.filter(function (r) {
      return !isBlank(r[COST_COLUMN]) || !isBlank(r.list_eur);
    });
    return {
      approval_field_present: withFlag.length > 0,
      approval_field: withFlag.length ? (rows[0].approved !== undefined ? 'approved' : 'approval') : null,
      rows_with_an_approval_state: withFlag.length,
      rows_with_complete_cost_or_list: completeness.length,
      rows_approved: rows.filter(function (r) { return r.approved === true || r.approval === true; }).length,
      statement: 'Cost and list completeness is held on ' + completeness.length + ' row(s). '
        + 'Approval is held on ' + withFlag.length + ' row(s), because these records carry no '
        + 'approval field. Completeness is not approval, and no price decision is cleared by a '
        + 'row carrying a cost.'
    };
  }

  /* Commercial priority and evidence readiness, kept apart and never scored into
     one number. */
  function evidenceReadiness(rows) {
    rows = rows || [];
    var held = rows.filter(function (r) { return !isBlank(r[COST_COLUMN]) && !isBlank(r.list_eur); });
    var competitor = rows.filter(function (r) { return r.competitor_evidence === 'held'; });
    var unresolved = rows.filter(function (r) { return !isBlank(r.unresolved_inputs); });
    return {
      rows_with_cost_and_list: held.length,
      rows_with_competitor_evidence: competitor.length,
      rows_with_open_inputs: unresolved.length,
      open_input_examples: uniqueValues(unresolved, 'unresolved_inputs').slice(0, 8),
      statement: 'Evidence readiness is counted here and is not mixed into a priority score. '
        + held.length + ' row(s) carry a cost and a list, ' + competitor.length
        + ' carry competitor evidence, and ' + unresolved.length + ' state an open input. '
        + 'Two distinct part numbers with competitor evidence do not establish an approved '
        + 'like-for-like quotation.'
    };
  }

  function monetaryPriority(rows, opts) {
    opts = opts || {};
    var list = rows || [];
    var values = list.map(function (r) { return toNumberOrNull(r.observed_billing_eur); })
      .filter(function (v) { return v !== null; });
    var missing = list.length - values.length;
    var total = values.reduce(function (s, v) { return s + v; }, 0);
    var sorted = values.slice().sort(function (a, b) { return b - a; });
    var topN = opts.top_n === undefined ? 10 : opts.top_n;
    return {
      total_observed_billing_eur: round2(total),
      rows_with_a_billing_value: values.length,
      rows_without_a_billing_value: missing,
      top_n: topN,
      top_n_share_pct: sorted.length && total
        ? round2(100 * sorted.slice(0, topN).reduce(function (s, v) { return s + v; }, 0) / total) : null,
      largest_observed_billing_eur: sorted.length ? round2(sorted[0]) : null,
      statement: 'Monetary priority is the observed billing on the row, for a period these records '
        + 'do not state. ' + missing + ' row(s) carry no billing value and are excluded from the '
        + 'total rather than counted as zero. The largest ' + topN + ' row(s) are '
        + (sorted.length && total
            ? round2(100 * sorted.slice(0, topN).reduce(function (s, v) { return s + v; }, 0) / total) + '%'
            : 'n/a') + ' of the recorded value.'
    };
  }

  /* DATA-02: distributor, purchasing account and site, kept distinct. */
  function distinctEntities(rows) {
    var distributors = uniqueValues(rows, 'distributor');
    var accounts = uniqueValues(rows, 'purchasing_account');
    var sites = uniqueValues(rows, 'site');
    var blends = [];
    for (var i = 0; i < distributors.length; i++) {
      for (var j = i + 1; j < distributors.length; j++) {
        if (manifest.isSeparatePair(distributors[i], distributors[j])) {
          blends.push({ a: distributors[i], b: distributors[j],
            statement: distributors[i] + ' and ' + distributors[j] + ' appear in the same set and '
              + 'are separate entities. Every total keeps them as two rows.' });
        }
      }
    }
    return {
      distributors: distributors,
      purchasing_accounts: accounts,
      sites: sites,
      account_field_present: accounts.length > 0,
      site_field_present: sites.length > 0,
      separate_entity_pairs_present: blends,
      statement: distributors.length + ' distributor(s), '
        + (accounts.length ? accounts.length + ' purchasing account(s)' : 'no purchasing account field')
        + ', ' + (sites.length ? sites.length + ' site(s)' : 'no site field')
        + '. A distributor is not an account and an account is not a site, so the three are '
        + 'counted and reported separately.'
        + (blends.length ? ' ' + blends.length + ' separate-entity pair(s) are present in one set and '
          + 'are never combined.' : '')
    };
  }

  /* ------------------------------------------------- search, filter, page -- */

  function search(rows, query) {
    var q = norm(query).trim();
    if (!q) return rows.slice();
    var terms = q.split(/\s+/).filter(Boolean);
    return rows.filter(function (r) {
      var haystack = norm(r.distributor) + ' ' + norm(r.part_number) + ' ' + norm(r.description)
        + ' ' + norm(r.selection_reasons) + ' ' + norm(r.unresolved_inputs)
        + ' ' + norm(r.competitor_evidence);
      return terms.every(function (t) { return haystack.indexOf(t) >= 0; });
    });
  }

  function filter(rows, criteria) {
    criteria = criteria || {};
    return rows.filter(function (r) {
      if (criteria.distributor && r.distributor !== criteria.distributor) return false;
      if (criteria.with_cost && isBlank(r[COST_COLUMN])) return false;
      if (criteria.without_cost && !isBlank(r[COST_COLUMN])) return false;
      if (criteria.with_competitor && r.competitor_evidence !== 'held') return false;
      if (criteria.base_price_moved && !(Number(r.base_price_move_pct) > 0)) return false;
      if (criteria.unresolved_only && isBlank(r.unresolved_inputs)) return false;
      if (criteria.part_number && r.part_number !== criteria.part_number) return false;
      if (criteria.exact_part && !criteria.include_related
          && String(r.part_number).indexOf(String(criteria.exact_part)) < 0) return false;
      if (criteria.min_billing !== undefined && criteria.min_billing !== null
          && !(Number(r.observed_billing_eur) >= Number(criteria.min_billing))) return false;
      return true;
    });
  }

  function page(rows, pageNumber, pageSize) {
    var size = Math.max(1, pageSize || 50);
    var total = rows.length;
    var pageCount = Math.max(1, Math.ceil(total / size));
    var current = Math.min(Math.max(1, pageNumber || 1), pageCount);
    var start = (current - 1) * size;
    return {
      rows: rows.slice(start, start + size),
      page: current, page_size: size, page_count: pageCount, total: total,
      first_row: total ? start + 1 : 0,
      last_row: Math.min(start + size, total)
    };
  }

  /* One call that the view uses, so filtering, counting and paging cannot drift
     apart between screens. */
  function workbench(allRows, options) {
    options = options || {};
    var all = allRows || [];
    var filtered = filter(search(all, options.query), options.criteria);
    var sorted = numericSort(filtered, options.sort_key || 'observed_billing_eur',
      options.sort_direction || 'desc');
    var pageResult = page(sorted, options.page, options.page_size);
    return {
      basis: reportingBasis(all),
      rule: options.screen_rule ? screenRule(options.screen_rule, all) : null,
      coverage: coverage(filtered, all, { payload: options.payload }),
      approval: approvalStatus(filtered),
      readiness: evidenceReadiness(filtered),
      priority: monetaryPriority(filtered, options),
      entities: distinctEntities(filtered),
      sort_key: options.sort_key || 'observed_billing_eur',
      sort_direction: options.sort_direction || 'desc',
      criteria: options.criteria || {},
      query: options.query || '',
      page: pageResult,
      matched: sorted
    };
  }

  /* -------------------------------------------------- line of descent (06) -- */

  /* One accepted set, with the origin and revision of every record in it. A
     repeated import of the same section replaces its own records; a correction
     names the revision it replaces. The row count is conserved: rows in equals
     rows out, and anything set aside is reported with its reason. */
  function makeDataset(name, opts) {
    opts = opts || {};
    var rows = [];
    var byKey = {};
    var revisions = [];
    var setAside = [];
    var keysEverTaken = {};

    function keyOf(r, ordinal, sourceSection) {
      if (opts.key_of) return opts.key_of(r, ordinal, sourceSection);
      /* The natural key is the declared source section, distributor, original
         part reference, and position of the row inside that section. Two rows
         can legitimately share a distributor and a part number - an unpriced
         line beside a priced one, or the same part on two different invoices -
         and neither may overwrite the other. The section name scopes the key,
         so a repeated import of the same section reproduces the same keys
         while a second invoice section keeps its own rows. */
      return [sourceSection, r.distributor, r.part_number, ordinal].join(SEP);
    }

    function upsert(sourceSection, incoming, meta) {
      meta = meta || {};
      incoming = incoming || [];
      var rev = { revision: revisions.length + 1, source_section: sourceSection,
        at: meta.at || null, operation: 'upsert',
        counts: { received: incoming.length, added: 0, replaced: 0, set_aside: 0, unchanged: 0 } };
      incoming.forEach(function (r, ordinal) {
        var k = keyOf(r, ordinal, sourceSection);
        keysEverTaken[k] = true;
        var record = { key: k, source_section: sourceSection, revision: rev.revision,
          origin: meta.origin || null, accepted_at: meta.at || null, restricted: meta.restricted === true,
          record: r };
        if (byKey[k] === undefined) {
          byKey[k] = record; rows.push(record); rev.counts.added += 1;
        } else if (JSON.stringify(byKey[k].record) === JSON.stringify(r)) {
          rev.counts.unchanged += 1;
        } else {
          byKey[k].record = r;
          byKey[k].revision = rev.revision;
          byKey[k].source_section = sourceSection;
          byKey[k].keys_added = null;
          rev.counts.replaced += 1;
        }
      });
      revisions.push(rev);
      return { ok: true, revision: rev.revision, counts: rev.counts, rows_held: rows.length,
        statement: 'Section "' + sourceSection + '" added ' + rev.counts.added + ', replaced '
          + rev.counts.replaced + ', folded ' + rev.counts.unchanged + ' repeated row(s). '
          + 'Re-importing the same section does not multiply the set.' };
    }

    /* A correction replaces its declared predecessor. The predecessor stays
       readable, and the corrected activity is not counted twice. */
    function correct(sourceSection, key, replacement, correction) {
      correction = correction || {};
      var rec = byKey[key];
      if (!rec) {
        return { ok: false, error: 'No row with that key is held, so there is nothing to correct. '
          + 'A correction names a declared predecessor.' };
      }
      var predecessorRevision = rec.revision;
      var declared = correction.corrects_revision;
      if (declared !== undefined && declared !== null && declared !== predecessorRevision) {
        return { ok: false, error: 'The correction declares it replaces revision ' + declared
          + ' and the held row is at revision ' + predecessorRevision + '. Refused rather than '
          + 'replacing the wrong record.', conflict: true };
      }
      rec.record = replacement;
      rec.revision = revisions.length + 1;
      rec.source_section = sourceSection;
      rec.corrected_from_revision = predecessorRevision;
      rec.correction_id = correction.correction_id || ('COR-' + (revisions.length + 1));
      rec.correction_reason = correction.reason || null;
      revisions.push({ revision: rec.revision, source_section: sourceSection,
        at: correction.at || null, operation: 'correction',
        counts: { received: 1, added: 0, replaced: 1, set_aside: 0, unchanged: 0 },
        correction: { correction_id: rec.correction_id, corrects_revision: predecessorRevision,
          reason: correction.reason || null, justified: !isBlank(correction.reason) } });
      return { ok: true, correction_id: rec.correction_id, corrects_revision: predecessorRevision,
        row: rec, rows_held: rows.length,
        statement: 'Correction ' + rec.correction_id + ' replaced revision ' + predecessorRevision
          + ' and kept it readable. The corrected quantity is counted once.' };
    }

    function setAsideRow(key, reason) {
      var rec = byKey[key];
      if (!rec) return { ok: false, error: 'No such row.' };
      setAside.push({ key: key, reason: reason || 'no reason stated',
        quantity: rec.record ? toNumberOrNull(rec.record.billed_qty) : null,
        revenue_eur: rec.record ? toNumberOrNull(rec.record.observed_billing_eur) : null });
      delete byKey[key];
      rows = rows.filter(function (r) { return r.key !== key; });
      return { ok: true, set_aside: setAside.length,
        statement: 'The row was set aside with a stated reason and is reported, not deleted quietly.' };
    }

    /* Rows in equals rows out. The arithmetic is the shared conservation rule in
       the evidence layer, so this set and the import log cannot drift apart.

       The defect fixed here: this function used to add `setAside.length` to the
       received total as well as to the buckets, so a row that was set aside was
       counted twice - once as added and once as set aside. `ok` was always false
       the moment anything was set aside, and true whenever nothing was, so the
       check reported a difference that was not there and could not have reported
       a row that really had gone missing. A set-aside row now belongs to the
       set-aside bucket and to nothing else.

       The store is cross-checked against the key index and the revision log as
       well, so a row that leaves the store without a stated reason still fails. */
    function conservation() {
      var received = revisions.reduce(function (s, r) { return s + r.counts.received; }, 0);
      var added = revisions.reduce(function (s, r) { return s + r.counts.added; }, 0);
      var replaced = revisions.reduce(function (s, r) { return s + r.counts.replaced; }, 0);
      var unchanged = revisions.reduce(function (s, r) { return s + r.counts.unchanged; }, 0);
      var corrections = revisions.filter(function (r) { return r.operation === 'correction'; }).length;
      var setAsideKeys = {};
      setAside.forEach(function (e) { setAsideKeys[e.key] = true; });
      /* A key that was set aside and later imported again. */
      var setAsideReimported = 0;
      Object.keys(byKey).forEach(function (k) { if (setAsideKeys[k]) setAsideReimported += 1; });

      var result = evidence.conservationOfLedger({
        revisions: revisions.length,
        corrections: corrections,
        received: received,
        added: added,
        replaced: replaced,
        unchanged: unchanged,
        folded: 0,
        held: rows.length,
        set_aside: setAside,
        set_aside_reimported: setAsideReimported,
        keys_held: Object.keys(byKey).length,
        keys_set_aside: Object.keys(setAsideKeys).length,
        keys_taken: Object.keys(keysEverTaken).length
      });
      result.rows_set_aside_detail = setAside.slice();
      return result;
    }

    function acceptedView() {
      return {
        name: name,
        accepted_revision: revisions.length,
        rows: rows.map(function (r) {
          return { key: r.key, revision: r.revision, source_section: r.source_section,
            origin: r.origin, restricted: r.restricted,
            corrected_from_revision: r.corrected_from_revision || null,
            correction_id: r.correction_id || null, record: r.record };
        }),
        revisions: revisions.slice()
      };
    }

    function trace(key) {
      var rec = byKey[key];
      if (!rec) return null;
      var trail = revisions.filter(function (r) {
        return r.source_section === rec.source_section || (r.correction && r.revision === rec.revision)
          || r.revision === rec.revision;
      });
      return {
        key: key, current_revision: rec.revision, source_section: rec.source_section,
        corrected_from_revision: rec.corrected_from_revision || null,
        correction_id: rec.correction_id || null,
        trail: trail.slice(),
        statement: 'The held row came from "' + rec.source_section + '" at revision ' + rec.revision
          + (rec.corrected_from_revision
              ? ', correcting revision ' + rec.corrected_from_revision + '.' : '.')
      };
    }

    return { upsert: upsert, correct: correct, setAside: setAsideRow,
      conservation: conservation, acceptedView: acceptedView, trace: trace,
      all: function () { return rows.slice(); } };
  }

  /* ------------------------------------------------------- promotion gate -- */

  /* A candidate becomes a review case only when the source supports it. Each
     blocker names the missing item. The reporting basis is passed in by the
     caller: this function will not derive a period from the candidate rows, and
     it will not accept one that the rows do not carry. */
  function promotionBlockers(row, payload, opts) {
    row = row || {};
    opts = opts || {};
    var blockers = [];
    if (isBlank(row[COST_COLUMN])) {
      blockers.push({ code: 'COST_MISSING', text: 'No verified parts purchase cost is held. A '
        + 'missing cost is not a cost of zero, so profit cannot be stated for this part.' });
    }
    if (isBlank(row.list_eur)) {
      blockers.push({ code: 'LIST_MISSING', text: 'No list price is held for this part.' });
    }
    if (row.competitor_evidence !== 'held') {
      blockers.push({ code: 'NO_COMPETITOR_EVIDENCE', text: 'No competitor evidence is held, so no '
        + 'like-for-like competitive question can be tested yet.' });
    }
    if (isBlank(row.billed_qty)) {
      blockers.push({ code: 'NO_OBSERVED_QUANTITY', text: 'No billed quantity is recorded, so there '
        + 'is no observed volume to price.' });
    }
    if (isBlank(row.part_number)) {
      blockers.push({ code: 'NO_PART_REFERENCE', text: 'The source line carries no part reference, '
        + 'so there is no original part to open a case against.' });
    }
    var basis = opts.basis || reportingBasis(
      payload && payload.candidateScreen ? payload.candidateScreen : [row]);
    if (!basis.declared) {
      blockers.push({ code: 'PERIOD_UNDECLARED', text: 'The candidate records carry no reporting '
        + 'period, so the evidence period of a case built from this row would be unresolved. The '
        + 'period is not guessed to make the row promotable.' });
    }
    return {
      promotable: blockers.length === 0,
      basis: basis,
      blockers: blockers,
      statement: blockers.length === 0
        ? 'The row carries a cost, a list, a recorded quantity, a part reference and a stated '
          + 'period, so a case can be opened. The cost is still not an approved accounting cost and '
          + 'the competitor row is still not an approved quotation.'
        : 'Not promotable yet: ' + blockers.length + ' item(s) are missing. '
          + blockers.map(function (b) { return b.code; }).join(', ') + '.'
    };
  }

  /* A period the reviewer typed. It is never written back onto the candidate
     row and never treated as source data. */
  function reviewerStatedBasis(period) {
    var text = (period === null || period === undefined) ? '' : String(period).trim();
    if (!text) {
      return {
        declared: false, period: null, period_state: 'undeclared',
        fields: [], values: [], row_count: 0,
        screen_period_count: 0, screen_period_note: null,
        statement: 'No evidence period was stated by the reviewer.'
      };
    }
    return {
      declared: true, period: text, period_state: 'stated by reviewer',
      fields: [], values: [text], row_count: 0,
      screen_period_count: 0, screen_period_note: null,
      statement: 'The evidence period was stated by the reviewer. It is not carried as '
        + 'source data on the candidate row.'
    };
  }

  function promoteToCase(row, payload, opts) {
    opts = opts || {};
    var check = promotionBlockers(row, payload, opts);
    if (!check.promotable) {
      return { ok: false, created: false, blockers: check.blockers, statement: check.statement };
    }
    var entity = opts.entity || manifest.normaliseEntity(row);
    return {
      ok: true, created: true,
      case: {
        case_id: opts.case_id || ('CAND-' + row.distributor + '-' + row.part_number),
        part_number: row.part_number,              /* original reference, never rewritten */
        customer: row.distributor,
        entity: entity,
        entity_label: typeof entity.distributor === 'string'
          ? manifest.entityLabel(entity) : row.distributor,
        unit: opts.unit || null,
        evidence_period: check.basis.period,       /* only ever a caller-stated period */
        evidence_period_state: check.basis.period_state,
        offer_effective_date: null,
        cost_basis_id: null,
        state: 'evidence_requested',
        source_row: { distributor: row.distributor, part_number: row.part_number,
          description: row.description, sales_stage: 'ISZE to distributor' }
      },
      blockers: [],
      statement: 'A draft case was opened from the candidate row. The evidence period is the one '
        + 'supplied with the request, and the offer effective date is left unresolved because the '
        + 'source states none.'
    };
  }

  var API = {
    COST_COLUMN: COST_COLUMN,
    COST_COLUMN_BASIS: COST_COLUMN_BASIS,
    PERIOD_FIELDS: PERIOD_FIELDS,
    periodFieldScan: periodFieldScan,
    reportingBasis: reportingBasis,
    screenRule: screenRule,
    uniqueParts: uniqueParts,
    uniqueValues: uniqueValues,
    verifiedCostPartNumbers: verifiedCostPartNumbers,
    coverage: coverage,
    approvalStatus: approvalStatus,
    evidenceReadiness: evidenceReadiness,
    monetaryPriority: monetaryPriority,
    distinctEntities: distinctEntities,
    search: search,
    filter: filter,
    page: page,
    workbench: workbench,
    makeDataset: makeDataset,
    promotionBlockers: promotionBlockers,
    reviewerStatedBasis: reviewerStatedBasis,
    promoteToCase: promoteToCase,
    numericSort: numericSort,
    evidenceInventory: evidence ? evidence.inventory : null
  };

  root.AIMCandidates = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
