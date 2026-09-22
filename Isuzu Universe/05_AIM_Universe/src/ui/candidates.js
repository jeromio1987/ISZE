/* ===========================================================================
   Candidate workbench view state (F10, REVIEW-01, REVIEW-02).

   The searching, filtering, counting and paging live in src/data/candidates.js —
   the module another agent owns and the regression suite exercises, so the screen
   and the tests cannot drift apart. This file holds the screen's state and
   presents one shape to the view layer.

   What v03 did that this exists to prevent: it printed the first 300 of 10,543
   records, with no search, no paging and no way to act on a row. It called the
   rows "screened", which they were, and "decision-ready on cost coverage", which
   they were not. It counted 15 customer-part rows as 15 parts.

   The shape returned by view() is deliberately flat and stable, because the view
   templates and the UX tests both read it:

     basis            the declared reporting basis, or the statement that it is
                      undeclared. Never an inferred period.
     coverage         the underlying coverage record, including cost_and_list_coverage
     counts           row counts and distinct part counts, as two different numbers
     approval         why completeness is not approval
     priority         commercial priority, stated as a separate axis
     entities         which distributors and accounts are in the set
     readiness        evidence readiness, kept out of the priority statement
     page             the current page and what part of the set it covers
     empty_state      an amber state when a search matches nothing, else null
   =========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('../data/candidates.js'), require('./failure.js'));
  } else {
    root.AIMUI = root.AIMUI || {};
    root.AIMUI.makeCandidateWorkbench = factory(root.AIMCandidates, root.AIMFailure).makeCandidateWorkbench;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (candidates, failure) {
  'use strict';

  var DEFAULT_PAGE_SIZE = 25;
  /* One full sweep must be able to reach every record. The real screen holds
     10,543 rows and the browser must not try to paint them all at once. */
  var PAGE_SIZE_CHOICES = [10, 25, 50, 100, 250];

  var DEFAULT_CRITERIA = {
    distributor: null,
    with_cost: false,
    without_cost: false,
    with_competitor: false,
    base_price_moved: false,
    min_billing: null
  };

  function makeCandidateWorkbench(allRows, options) {
    options = options || {};
    var rows = allRows || [];
    var state = {
      query: options.query || '',
      page: options.page || 1,
      page_size: options.page_size || DEFAULT_PAGE_SIZE,
      sort_key: options.sort_key || 'observed_billing_eur',
      sort_direction: options.sort_direction || 'desc',
      /* Commercial priority and evidence completeness are separate filters on
         purpose. A row can be high priority with no cost, and the screen must be
         able to show exactly that set. */
      criteria: Object.assign({}, DEFAULT_CRITERIA, options.criteria || {})
    };

    function run() {
      return candidates.workbench(rows, {
        query: state.query,
        criteria: cleanCriteria(state.criteria),
        sort_key: state.sort_key,
        sort_direction: state.sort_direction,
        page: state.page,
        page_size: state.page_size
      });
    }

    /* A tiny per-row priority label, derived from the row's own recorded billing.
       It is shown beside the row and is not merged into any completeness count. */
    function priorityLabel(row) {
      var p = candidates.monetaryPriority([row], { top_n: 1 });
      return p.rows_with_a_billing_value ? { band: band(p.largest_observed_billing_eur),
        basis: 'recorded billed amount on this row' } : { band: null, basis: 'no recorded billing on this row' };
    }
    function band(value) {
      if (value === null || value === undefined) return null;
      if (value >= 100000) return 'High';
      if (value >= 10000) return 'Medium';
      return 'Low';
    }

    function view() {
      var wb = run();
      var p = wb.page;
      var cov = wb.coverage;
      /* The screen's own page window, normalised so the pager cannot read past
         the end of the set. The underlying module clamps too; this is the value
         the buttons and the counter use. */
      var pageCount = p.page_count;
      state.page = p.page;
      return {
        state: { query: state.query, page: state.page, page_size: state.page_size,
          sort_key: state.sort_key, sort_direction: state.sort_direction,
          criteria: Object.assign({}, state.criteria) },
        basis: wb.basis,
        rule: wb.rule || null,
        coverage: cov,
        approval: wb.approval,
        priority: wb.priority,
        entities: wb.entities,
        readiness: wb.readiness,
        /* Row counts and distinct part counts are two different numbers, always,
           and the statement says so in words as well as in numbers. */
        counts: {
          rows_total: cov.rows_total,
          rows_matching: cov.rows_matching,
          rows_on_this_page: p.rows.length,
          distinct_part_numbers_matching: cov.unique_parts,
          distinct_part_numbers_total: candidates.uniqueParts(rows).length,
          statement: cov.rows_vs_parts_short
            || (cov.rows_matching + ' matching rows for ' + cov.unique_parts
              + ' distinct part numbers, from ' + cov.rows_total + ' screened rows in total. '
              + 'A row is a customer-part record, not a part.')
        },
        page: {
          rows: p.rows, page: p.page, page_size: p.page_size, page_count: pageCount,
          total: p.total, first_row: p.first_row, last_row: p.last_row,
          has_previous: p.page > 1, has_next: p.page < pageCount
        },
        sort: { key: wb.sort_key, direction: wb.sort_direction },
        /* Where the reader got to, so paging is checkable rather than felt. */
        reached: {
          first: p.first_row, last: p.last_row, of: p.total,
          covered_pct: p.total ? Math.round(1000 * p.last_row / p.total) / 10 : 0
        },
        empty_state: p.total === 0 ? failure.unavailable({
          title: 'No candidate row matches this search',
          reason: 'The search ran over all ' + cov.rows_total
            + ' screened rows and none matched. The rows are not missing; the filter excluded them.',
          required: 'a different search term, or clearing the cost and competitor filters',
          scope: 'candidate screen, both pilot accounts',
          as_of: null
        }) : null
      };
    }

    function setQuery(q) {
      state.query = q === null || q === undefined ? '' : String(q);
      state.page = 1;
      return view();
    }
    function setPage(n) {
      var wanted = Number(n);
      var current = view();
      state.page = Math.min(Math.max(1, Number.isFinite(wanted) ? Math.round(wanted) : 1),
        current.page.page_count);
      return view();
    }
    function setPageSize(n) {
      var size = Number(n);
      state.page_size = Number.isFinite(size) && size > 0 ? Math.min(Math.round(size), 5000) : DEFAULT_PAGE_SIZE;
      state.page = 1;
      return view();
    }
    function nextPage() { return setPage(view().page.page + 1); }
    function previousPage() { return setPage(view().page.page - 1); }
    function setSort(key, direction) {
      state.sort_key = key || state.sort_key;
      state.sort_direction = direction === 'asc' ? 'asc' : 'desc';
      state.page = 1;
      return view();
    }
    function setCriterion(name, value) {
      if (Object.prototype.hasOwnProperty.call(state.criteria, name)) state.criteria[name] = value;
      state.page = 1;
      return view();
    }
    function clearFilters() {
      state.criteria = Object.assign({}, DEFAULT_CRITERIA);
      state.query = '';
      state.page = 1;
      return view();
    }

    /* A search that reaches a record the first screen never showed. Used by the
       reach test and by the shell when a case is opened from a candidate row. */
    function findPart(partNumber) {
      return candidates.search(rows, String(partNumber)).filter(function (r) {
        return r.part_number === partNumber;
      });
    }

    /* The route from a candidate into its own review. It names the exact part
       reference and the accounts it came from, and it says plainly that no case is
       created until the reader asks for one. */
    function routeForPart(partNumber) {
      var found = findPart(partNumber);
      if (!found.length) {
        return { ok: false, error: 'No screened record carries part number ' + partNumber + '.' };
      }
      var priority = candidates.monetaryPriority(found, { top_n: found.length });
      var entities = candidates.distinctEntities(found);
      var blockers = typeof candidates.promotionBlockers === 'function'
        ? candidates.promotionBlockers(found) : null;
      return {
        ok: true,
        part_number: partNumber,
        description: found[0].description,
        rows: found.length,
        distributors: entities.distributors,
        accounts: entities.purchasing_accounts,
        /* The exact original reference travels with the row. It is never
           rewritten into a private or derived number. */
        exact_part_reference: partNumber,
        observed_billing_eur: priority.total_observed_billing_eur,
        rows_without_a_billing_value: priority.rows_without_a_billing_value,
        /* What would be needed before this could become a case. Stated, not
           guessed at, and never created silently. */
        promotion_blockers: blockers,
        target: { view: 'case', part_number: partNumber }
      };
    }

    return {
      view: view,
      setQuery: setQuery,
      setPage: setPage,
      setPageSize: setPageSize,
      nextPage: nextPage,
      previousPage: previousPage,
      setSort: setSort,
      setCriterion: setCriterion,
      clearFilters: clearFilters,
      routeForPart: routeForPart,
      findPart: findPart,
      priorityLabel: priorityLabel,
      page_size_choices: PAGE_SIZE_CHOICES.slice(),
      _state: function () { return Object.assign({}, state, { criteria: Object.assign({}, state.criteria) }); },
      _rows: function () { return rows; }
    };
  }

  function cleanCriteria(criteria) {
    var out = {};
    Object.keys(criteria).forEach(function (k) {
      var v = criteria[k];
      if (v === null || v === undefined || v === false || v === '') return;
      out[k] = v;
    });
    return out;
  }

  return { makeCandidateWorkbench: makeCandidateWorkbench, DEFAULT_PAGE_SIZE: DEFAULT_PAGE_SIZE,
    PAGE_SIZE_CHOICES: PAGE_SIZE_CHOICES };
});
