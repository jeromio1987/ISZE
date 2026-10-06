/* ===========================================================================
   Shell routing and the failed-render state (F05, UX-06, UX-07, REVIEW-04).

   The defect this file owns. In v03, opening ITUK-TURBO and then Two objectives
   threw inside the view. The tab button became active, the content region was
   never replaced, and the previous view's HTML stayed on screen. A reader could
   then attribute the stale evidence to the tab they had just selected. Nothing on
   the page said anything had failed.

   The shell therefore never assumes a view worked. It does this, in order:

     1. clear the content region and mark it busy
     2. build the view inside a try/catch
     3. if it threw, render a failure card that names the view, the case and the
        error, and say explicitly that nothing from another view is being shown
     4. if it built, check the built HTML is a non-empty string and carries the
        exact part reference, then paint it
     5. run the banned-word guard over the built HTML before paint

   There is no path in which a new tab is active and the old content is still
   visible.
   =========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(root, require('./failure.js'), require('./views.js'),
      require('./scenario.js').makeScenarioContext, require('./viewmodel.js'),
      require('./candidates.js').makeCandidateWorkbench);
  } else {
    root.AIMUI = root.AIMUI || {};
    root.AIMUI.render = factory(root, root.AIMFailure, root.AIMUI.views, root.AIMUI.makeScenarioContext,
      root.AIMViewModel, root.AIMUI.makeCandidateWorkbench);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (root, failure, views, makeScenarioContext,
  viewModelFactory, makeCandidateWorkbench) {
  'use strict';

  var TAB_LABELS = {
    decision: 'Sales evidence',
    position: 'Price position',
    objectives: 'Two objectives',
    economics: 'Price & profit test',
    candidates: 'Candidates',
    action: 'Internal action'
  };

  function makeShell(options) {
    options = options || {};
    var payload = options.payload;
    var engine = options.engine;
    var data = options.data || {};
    var contracts = options.contracts;
    var caseModule = options.caseModule;

    var scenario = options.scenario || makeScenarioContext(payload, engine, {});
    var vmodel = options.vmodel || viewModelFactory.build(payload, engine);
    var workbench = options.workbench || makeCandidateWorkbench(payload.candidateScreen || []);

    var firstCase = (payload.cases || [])[0] || {};
    var state = {
      case_id: firstCase.id || null,
      view: 'decision',
      /* Derived from the case, never left null. A missing comparison period is the
         kind of unset that produced a stale-looking screen in v03. */
      compare: firstCase.defaultCompare || 'half',
      market: 'all',
      billing_metric: 'billingEUR',
      part_route: null,
      objective: null
    };
    /* Saved review notes and the one case store. Both survive a view failure. */
    var saved = options.saved || {};
    var cases = options.caseStore || (caseModule ? caseModule.makeRepository({
      forceMemory: !!(options.forceMemory)
    }) : null);
    var storageOK = options.storageOK !== false;
    var log = [];
    var listeners = [];

    /* ---------------------------------------------------------- case lookup -- */

    function caseById(id) {
      return (payload.cases || []).filter(function (c) { return c.id === id; })[0]
        || (payload.cases || [])[0];
    }
    function currentCase() { return caseById(state.case_id); }

    function visibleCases() {
      return (payload.cases || []).filter(function (c) {
        return state.market === 'all' || c.market === state.market;
      });
    }

    /* --------------------------------------------------------------- routing -- */

    function go(patch) {
      var next = Object.assign({}, state, patch || {});
      if (next.case_id && next.case_id !== state.case_id) {
        next.part_route = next.part_route || null;
        /* A case change resets the comparison to that case's declared default,
           so a period selected on one case never leaks into another. */
        next.compare = caseById(next.case_id).defaultCompare || 'half';
      }
      if (!next.compare) next.compare = currentCase().defaultCompare || 'half';
      state = next;
      return paint();
    }

    function setMarket(market) {
      var list = (payload.cases || []).filter(function (c) {
        return market === 'all' || c.market === market;
      });
      var patch = { market: market };
      if (!list.some(function (c) { return c.id === state.case_id; })) patch.case_id = list[0] ? list[0].id : null;
      return go(patch);
    }

    function setCompare(compare) {
      if (compare !== 'half' && compare !== 'annual') {
        throw new Error('Unknown comparison "' + compare + '".');
      }
      return go({ compare: compare });
    }

    function setObjective(objective) {
      if (objective !== 'revenue' && objective !== 'grossProfit') {
        throw new Error('Unknown objective "' + objective + '". Use revenue or grossProfit.');
      }
      scenario.setObjective(state.case_id, objective);
      state.objective = objective;
      return paint();
    }

    function setBillingMetric(metric) {
      if (metric !== 'billingEUR' && metric !== 'billingQuantity') {
        throw new Error('Unknown billing metric "' + metric + '".');
      }
      return go({ billing_metric: metric });
    }

    /* The candidate-to-review route (F10). */
    function openPart(partNumber) {
      var route = workbench.routeForPart(partNumber);
      if (!route.ok) return { ok: false, error: route.error, view: state.view };
      var worked = (payload.cases || []).filter(function (c) { return c.pn === partNumber; })[0];
      if (worked) return go({ case_id: worked.id, part_route: null, view: 'decision' });
      return go({ part_route: route, view: 'case' });
    }

    /* ------------------------------------------------------- the render gate -- */

    function context() {
      return {
        payload: payload,
        engine: engine,
        h: views.helpers(engine),
        state: state,
        scenario: scenario,
        vmodel: vmodel,
        candidates: workbench,
        saved: saved,
        storageOK: storageOK,
        contracts: contracts
      };
    }

    function build(viewId, caseObject) {
      var html;
      try {
        html = views.render(viewId, context(), caseObject);
      } catch (error) {
        return failure.report({
          view: viewId, case_id: state.case_id,
          case_name: caseObject ? caseObject.name : null,
          objective: state.objective, error: error,
          render_key: viewId + ':' + state.case_id,
          detail: state
        });
      }
      if (typeof html !== 'string' || !html.trim()) {
        return failure.report({
          view: viewId, case_id: state.case_id,
          case_name: caseObject ? caseObject.name : null,
          objective: state.objective,
          error: new Error('The view built an empty result. An empty view is treated as a failure, '
            + 'not as a blank screen.'),
          render_key: viewId + ':' + state.case_id, detail: state
        });
      }
      if (caseObject && html.indexOf(caseObject.pn) < 0) {
        return failure.report({
          view: viewId, case_id: state.case_id,
          case_name: caseObject ? caseObject.name : null,
          error: new Error('The built view does not carry the exact part reference '
            + caseObject.pn + ', so it is not shown.'),
          render_key: viewId + ':' + state.case_id, detail: state
        });
      }
      return { failed: false, html: html, view: viewId };
    }

    /* Every navigation writes one audit record, including failures. This is what
       the sweep test and the QA pass read. */
    function audit(entry) {
      log.push(Object.assign({ at: new Date().toISOString(), market: state.market }, entry));
      listeners.forEach(function (fn) { try { fn(entry); } catch (e) { /* a listener must not break a render */ } });
      return entry;
    }

    /* Required by the tests and the browser sweep: does a given case/tab paint? */
    function probe(caseId, viewId) {
      var caseObject = caseById(caseId);
      if (!caseObject) return { ok: false, case_id: caseId, view: viewId,
        error: 'No such case "' + caseId + '".' };
      var result = build(viewId, caseObject);
      if (result.failed) {
        return { ok: false, case_id: caseId, view: viewId, view_label: TAB_LABELS[viewId] || viewId,
          failed: true, error_name: result.error_name, error_message: result.error_message,
          statement: failure.statement(result) };
      }
      var banned = views.bannedWords(result.html);
      return { ok: banned.length === 0, case_id: caseId, view: viewId, view_label: TAB_LABELS[viewId] || viewId,
        failed: false, length: result.html.length, banned_words: banned,
        carries_part_reference: result.html.indexOf(caseObject.pn) >= 0 };
    }

    /* ------------------------------------------------------------ the paint -- */

    function parts() { return root.document || null; }

    function paint() {
      var doc = parts();
      var c = currentCase();
      var result = build(state.view, c);
      var record = audit({ kind: 'paint', view: state.view, case_id: state.case_id,
        ok: !result.failed, error: result.failed ? result.error_message : null });
      if (!doc) return { ok: !result.failed, record: record, html: result.failed ? null : result.html, failure: result.failed ? result : null };

      var content = doc.getElementById('content');
      /* Step 1: the old content is replaced before anything else, so a failure
         can never leave the previous view visible under a new active tab. */
      if (content) {
        content.setAttribute('data-render-state', 'building');
        content.innerHTML = '';
      }

      var banned = result.failed ? [] : views.bannedWords(result.html);
      if (!result.failed && banned.length) {
        result = failure.report({
          view: state.view, case_id: state.case_id, case_name: c ? c.name : null,
          error: new Error('The built view contains wording a reader must not see: '
            + banned.map(function (b) { return '"' + b.word + '" (' + b.why + ')'; }).join(', ') + '.'),
          render_key: state.view + ':' + state.case_id, detail: state
        });
        record.ok = false;
        record.error = result.error_message;
      }

      if (content) {
        content.innerHTML = result.failed ? failureCard(result) : result.html;
        content.setAttribute('data-render-state', result.failed ? 'failed' : 'built');
      }
      /* The surrounding chrome must never be able to undo the decision just made
         about the content region. If a card or a control fails, the content state
         still stands and the failure is recorded. */
      try {
        paintChrome(doc, c, result);
        bind(doc);
      } catch (chromeError) {
        record.ok = false;
        record.error = 'The page frame failed after the content was set: ' + chromeError.message;
        audit({ kind: 'chrome-failed', view: state.view, case_id: state.case_id, ok: false,
          error: chromeError.message });
      }
      return { ok: !result.failed, record: record, failure: result.failed ? result : null };
    }

    function failureCard(f) {
      return '<div class="render-failure" role="alert" data-failed-view="' + views.esc(f.view) + '">'
        + '<div class="eyebrow">This view failed to build</div>'
        + '<h2>' + views.esc(failure.labelFor(f.view)) + ' did not render</h2>'
        + '<p><b>' + views.esc(f.error_name) + ':</b> ' + views.esc(f.error_message) + '</p>'
        + '<p class="small">' + views.esc(failure.statement(f)) + '</p>'
        + '<div class="evidence-line"><span>Failing view</span><b>' + views.esc(f.view) + '</b></div>'
        + '<div class="evidence-line"><span>Case</span><b>' + views.esc(f.case_id || 'none')
        + (f.case_name ? ' &mdash; ' + views.esc(f.case_name) : '') + '</b></div>'
        + '<div class="evidence-line"><span>What kind of failure</span><b class="small">'
        + views.esc(f.error_kind) + '</b></div>'
        + '<div class="ruleline"><b>This is what you can do</b>'
        + '<p class="small">' + failure.recovery(f).map(function (r) { return views.esc(r.label); }).join(' &middot; ')
        + '</p></div>'
        + (f.stack ? '<details><summary>Technical detail for a developer</summary><pre class="small">'
            + views.esc(f.stack) + '</pre></details>' : '')
        + '</div>';
    }

    function paintChrome(doc, c, result) {
      var caseList = doc.getElementById('case-list');
      if (caseList) {
        caseList.innerHTML = visibleCases().map(function (x) {
          var h = views.helpers(engine);
          /* A case with no recorded comparison still gets a card. It shows that
             the comparison is absent rather than breaking the whole paint. */
          var cmpKey = (x.comparisons || {})[state.compare] ? state.compare : x.defaultCompare;
          var m = (x.comparisons || {})[cmpKey] || null;
          return '<button class="case-card' + (c && c.id === x.id ? ' active' : '') + '" data-case="' + views.esc(x.id)
            + '" aria-pressed="' + (c && c.id === x.id) + '">'
            + '<div class="card-meta"><span>' + views.esc(x.customer) + '</span><span>'
            + (cmpKey === 'annual' ? 'Full year' : 'Matched half year') + '</span></div>'
            + '<div class="case-name">' + views.esc(x.name) + '</div>'
            + '<div class="pn">' + views.esc(x.pn) + '</div>'
            + '<div class="case-amount ' + (m ? h.color(m.revenueDelta) : '') + '">'
            + (m ? h.signedEur(m.revenueDelta) : 'No comparison held') + '</div>'
            + '<div class="case-period">ISZE billing &middot; ' + views.esc(m ? m.label : 'not held')
            + '</div>'
            + '<div class="case-direction">' + views.esc(x.actionType) + '</div></button>';
        }).join('');
      }
      var header = doc.getElementById('case-header');
      if (header && c) {
        header.innerHTML = '<div class="head-line"><div>'
          + '<div class="eyebrow">' + views.esc(c.customer) + ' &middot; ' + views.esc(c.category)
          + ' &middot; ' + views.esc(c.pn) + '</div>'
          + '<span class="badge ' + (c.actionType === 'Protect the price' ? 'hold' : 'review') + '">'
          + views.esc(c.actionType) + '</span></div>'
          + '<div class="head-right"><button class="button secondary" id="export-review">Export case review</button>'
          + '</div></div><h2>' + views.esc(c.action) + '</h2><p>' + views.esc(c.verdict) + '</p>';
      }
      var strip = doc.getElementById('scope-strip');
      if (strip && c) {
        var cmp = (c.comparisons || {})[state.compare] || null;
        strip.innerHTML = '<div><span>Customer / scope</span>' + views.esc(c.customer)
          + ' &middot; distributor, not dealer</div>'
          + '<div><span>Selected comparison</span>'
          + views.esc(cmp ? cmp.label : 'not held for this case') + '</div>'
          + '<div><span>Basis / reporting clocks</span>ISZE net EUR; separate onward quantities</div>'
          + '<div><span>Historical fleet context</span>' + views.helpers(engine).num(c.fleet) + ' market '
          + (c.market === 'ITUK' ? 'trucks' : 'vehicles') + ', 2025 &middot; part fleet not known</div>';
      }
      var pack = doc.getElementById('pack-status');
      if (pack && c) {
        var st = vmodel.case_status(c.id);
        var comp = vmodel.completeness(st);
        pack.innerHTML = '<span><b>' + views.esc(vmodel.version.display) + '</b> &middot; '
          + views.esc(vmodel.price_rule.boundary) + '</span>'
          + '<span>Evidence: ' + views.esc(comp.statement) + '</span>'
          + '<span>Commercial priority: ' + views.esc(st.commercial_priority.label) + '</span>'
          + '<button class="sourcesbutton" data-sources>Evidence, selection and limitations</button>';
      }
      var tabs = doc.getElementById('tabs');
      if (tabs) {
        var order = views.VIEW_ORDER.slice();
        if (state.view === 'case') order = order.concat(['case']);
        tabs.innerHTML = order.map(function (k) {
          return '<button class="tab' + (state.view === k ? ' active' : '') + '" role="tab" aria-selected="'
            + (state.view === k) + '" data-view="' + views.esc(k) + '"'
            + (state.view === k ? ' aria-current="page"' : '') + '>' + views.esc(TAB_LABELS[k] || k) + '</button>';
        }).join('');
      }
      var market = doc.getElementById('market');
      if (market) market.value = state.market;
      var status = doc.getElementById('render-status');
      if (status) {
        status.textContent = result.failed
          ? 'The ' + failure.labelFor(result.view) + ' view failed to build. Nothing from another view is shown.'
          : TAB_LABELS[state.view] + ' built for ' + state.case_id + '.';
        status.setAttribute('data-failed', result.failed ? 'true' : 'false');
      }
    }

    /* --------------------------------------------------------------- binding -- */

    function bind(doc) {
      function all(sel) { return Array.prototype.slice.call(doc.querySelectorAll(sel)); }
      function on(sel, event, handler) {
        all(sel).forEach(function (el) { el.addEventListener(event, handler); });
      }

      on('[data-case]', 'click', function () { go({ case_id: this.getAttribute('data-case'), part_route: null }); });
      on('[data-view]', 'click', function () {
        var view = this.getAttribute('data-view');
        if (state.view === 'action') collectNote();
        go({ view: view, part_route: view === 'case' ? state.part_route : null });
      });
      on('[data-open-case]', 'click', function () {
        go({ case_id: this.getAttribute('data-open-case'), view: 'decision', part_route: null });
      });
      on('[data-open-part]', 'click', function () { openPart(this.getAttribute('data-open-part')); });
      on('[data-sources]', 'click', function () { sourcesModal(doc); });
      on('[data-billing-toggle]', 'click', function () {
        setBillingMetric(state.billing_metric === 'billingEUR' ? 'billingQuantity' : 'billingEUR');
      });
      on('[data-select-alternative]', 'click', function () {
        var id = this.getAttribute('data-select-alternative');
        var res = scenario.select(state.case_id, id);
        if (!res.ok) { toast(doc, res.error); return; }
        paint();
        toast(doc, res.migration_unresolved
          ? 'Selected. This alternative names a product migration and stays financially unresolved.'
          : 'Selected into the one scenario record. The price test and the export now carry it.');
      });
      on('#objective', 'change', function () { setObjective(this.value); });
      on('#comparison', 'change', function () { setCompare(this.value); });
      on('#market', 'change', function () { setMarket(this.value); });

      /* UX-07: the existing month cells already take a tabindex and answer Enter
         and Space. That pattern is kept, and the key handler is delegated so it
         survives a repaint. */
      all('.month-hit').forEach(function (el) {
        function read() {
          var target = doc.getElementById('readout-' + el.getAttribute('data-chart'));
          if (target) target.textContent = el.getAttribute('data-readout');
        }
        el.addEventListener('click', read);
        el.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') { e.preventDefault(); read(); }
        });
      });

      /* The candidate workbench controls (F10). */
      var search = doc.getElementById('candidate-search');
      if (search) {
        var commit = function () {
          workbench.setQuery(search.value);
          paint();
          var again = doc.getElementById('candidate-search');
          if (again) { again.focus(); again.setSelectionRange(again.value.length, again.value.length); }
        };
        search.addEventListener('change', commit);
        search.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); commit(); } });
      }
      on('#candidate-account', 'change', function () {
        workbench.setCriterion('distributor', this.value || null); paint();
      });
      on('#candidate-cost', 'change', function () {
        var value = this.value;
        /* Reset both sides before applying, so switching the filter never leaves
           the two flags contradicting each other. */
        workbench.setCriterion('with_cost', false);
        workbench.setCriterion('without_cost', false);
        if (value === 'with') workbench.setCriterion('with_cost', true);
        if (value === 'without') workbench.setCriterion('without_cost', true);
        paint();
      });
      on('#candidate-competitor', 'change', function () {
        workbench.setCriterion('with_competitor', this.value === 'held'); paint();
      });
      on('#candidate-pagesize', 'change', function () { workbench.setPageSize(Number(this.value)); paint(); });
      on('[data-page]', 'click', function () { workbench.setPage(Number(this.getAttribute('data-page'))); paint(); });
      on('[data-last-page]', 'click', function () {
        workbench.setPage(workbench.view().page.page_count); paint();
      });
      on('[data-sort]', 'click', function () {
        var key = this.getAttribute('data-sort');
        var dir = (workbench.view().sort.key === key && workbench.view().sort.direction === 'desc') ? 'asc' : 'desc';
        workbench.setSort(key, dir); paint();
      });
      on('[data-clear-filters]', 'click', function () { workbench.clearFilters(); paint(); });

      /* The scenario inputs (F01). Every edit writes the one record. */
      if (state.view === 'economics') {
        var MAP = {
          baseP: { field: 'price_before', numeric: true },
          newP: { field: 'price_after', numeric: true },
          baseQ: { field: 'quantity_before', numeric: true },
          quantityAfter: { field: 'quantity_after', numeric: true, blankAsNull: true },
          support: { field: 'support_eur', numeric: true },
          cost: { field: 'cost_eur', numeric: true, blankAsNull: true },
          scope: { field: 'scope', numeric: false },
          offerDate: { field: 'offer_effective_date', numeric: false, blankAsNull: true }
        };
        Object.keys(MAP).forEach(function (id) {
          var el = doc.getElementById(id);
          if (!el) return;
          var spec = MAP[id];
          var commit = function () {
            var raw = el.value;
            var value;
            if (spec.numeric) {
              value = (raw === '' && spec.blankAsNull) ? null : Number(raw);
              if (raw !== '' && !Number.isFinite(value)) { toast(doc, 'That is not a number. Nothing was written to the scenario.'); return; }
            } else {
              value = (raw === '' && spec.blankAsNull) ? null : raw;
            }
            var patch = {};
            patch[spec.field] = value;
            try {
              scenario.edit(state.case_id, patch);
            } catch (e) {
              toast(doc, e.message);
              return;
            }
            repaintResults(doc);
          };
          el.addEventListener('change', commit);
          if (spec.numeric) el.addEventListener('input', commit);
        });
        var costBasis = doc.getElementById('costBasisId');
        if (costBasis) {
          costBasis.addEventListener('change', function () {
            var basisId = this.value;
            var rec = engine.costRecord(payload, currentCase().pn, basisId);
            scenario.edit(state.case_id, {
              cost_basis_id: basisId,
              cost_eur: rec ? rec.cost_eur : null,
              cost_basis_source: rec ? 'verified record' : 'no verified cost held'
            });
            paint();
          });
        }
        on('#reset-scenario', 'click', function () { scenario.reset(state.case_id); paint(); });
      }

      on('#save-note', 'click', function () { saveNote(doc); });
      on('#delete-note', 'click', function () {
        delete saved[state.case_id];
        persist(doc);
        paint();
        toast(doc, 'Saved record deleted for this case.');
      });
      on('#export-json', 'click', function () { exportFile('json'); });
      on('#export-review', 'click', function () { exportFile('html'); });
      on('#export-review-body', 'click', function () { exportFile('html'); });
    }

    /* The results region alone is rebuilt on a keystroke, so typing does not move
       the reader's cursor out of the field they are in. */
    function repaintResults(doc) {
      var host = doc.getElementById('economic-results');
      if (!host) return;
      try {
        host.innerHTML = views.economicsResults(context(), currentCase());
      } catch (e) {
        var f = failure.report({ view: 'economics', case_id: state.case_id, error: e, detail: state });
        host.innerHTML = failureCard(f);
      }
      bind(doc);
    }

    function collectNote() {
      var doc = parts();
      if (!doc) return saved[state.case_id] || {};
      var existing = saved[state.case_id] || {};
      var read = function (id, fallback) {
        var el = doc.getElementById(id);
        return el ? el.value : fallback;
      };
      saved[state.case_id] = {
        owner: read('owner', existing.owner || (currentCase() || {}).owner),
        reviewDate: read('reviewDate', existing.reviewDate || ''),
        status: read('actionStatus', existing.status || 'Draft review'),
        explanation: read('explanation', existing.explanation || ''),
        note: read('decisionNote', existing.note || (currentCase() || {}).recommendation)
      };
      return saved[state.case_id];
    }

    function persist(doc) {
      try {
        if (root.localStorage) root.localStorage.setItem('ISZE_AIM_PRICING_UI_01', JSON.stringify(saved));
        storageOK = true;
      } catch (e) {
        storageOK = false;
        if (doc) toast(doc, 'Local storage refused the write. Export before closing.');
      }
    }

    /* The save path writes the scenario record the views are showing, and nothing
       else. That is the whole point of F01. */
    function saveNote(doc) {
      var note = collectNote();
      var pkg = scenario.exportPackage(state.case_id, { generated_at: new Date().toISOString() });
      var record = {
        scenario: pkg.scenario,
        result: pkg.result,
        review: note,
        part_number: pkg.part_number,
        case_id: pkg.case_id
      };
      if (!cases) {
        note.savedAt = new Date().toISOString();
        note.scenario_id = pkg.scenario_id;
        persist(doc);
        paint();
        toast(doc, 'Saved for this session. No case store is attached.');
        return { ok: true, session_only: true };
      }
      var res = cases.save(state.case_id, record, {
        state: 'draft',
        owner_role: note.owner,
        note: note.note,
        recorded_by: 'aim-ui',
        expected_version: undefined
      });
      if (!res.ok) {
        var msg = doc.getElementById('save-status');
        if (msg) msg.textContent = res.error;
        toast(doc, res.error);
        return res;
      }
      note.savedAt = new Date().toISOString();
      note.case_version = res.version;
      note.scenario_id = pkg.scenario_id;
      persist(doc);
      paint();
      var status = doc.getElementById('save-status');
      if (status) {
        status.textContent = 'Saved as case revision ' + res.version
          + '. No price is approved and nothing was submitted anywhere.';
      }
      toast(doc, 'Saved as case revision ' + res.version + '.');
      return res;
    }

    function exportFile(kind) {
      var doc = parts();
      var c = currentCase();
      var pkg = scenario.exportPackage(state.case_id, { generated_at: new Date().toISOString() });
      var text;
      var name;
      if (kind === 'html') {
        text = exportHtml(c, pkg);
        name = String(c.customer).replace(/ /g, '_') + '_' + c.pn + '_Pricing_Review.html';
      } else {
        text = JSON.stringify(pkg, null, 2);
        name = String(c.customer).replace(/ /g, '_') + '_' + c.pn + '_Review.json';
      }
      var bytes = new TextEncoder().encode(text);
      if (doc && typeof root.URL !== 'undefined' && root.URL.createObjectURL) {
        var blob = new root.Blob([bytes], { type: kind === 'html' ? 'text/html' : 'application/json' });
        var url = root.URL.createObjectURL(blob);
        var a = doc.createElement('a');
        a.href = url; a.download = name; a.click();
        setTimeout(function () { root.URL.revokeObjectURL(url); }, 1000);
      }
      if (doc) toast(doc, 'Exported ' + name + '. This case only.');
      return { name: name, text: text, bytes: bytes.length };
    }

    /* The readable export. It carries the scenario record, the result, the change
       journal and both objective orders, and it says which one it is. */
    function exportHtml(c, pkg) {
      var h = views.helpers(engine);
      var r = pkg.result;
      var cons = pkg.consistency;
      return '<!doctype html><html lang="en"><meta charset="utf-8">'
        + '<title>' + views.esc(c.customer) + ' - ' + views.esc(c.pn) + ' - internal pricing review</title>'
        + '<style>body{font:14px/1.5 Segoe UI,Arial,sans-serif;color:#15344b;max-width:1100px;margin:35px auto;'
        + 'padding:0 25px}h1{font-size:28px}h2{font-size:20px;margin-top:28px}table{border-collapse:collapse;'
        + 'width:100%;font-size:12px}th,td{padding:8px;border-bottom:1px solid #d8e1e8;text-align:left;'
        + 'vertical-align:top}th{background:#eff4f8}aside{background:#fff5e3;padding:15px}'
        + 'footer,.small{font-size:11px;color:#53697a}pre{white-space:pre-wrap;font:inherit}.n{text-align:right}'
        + '</style><body>'
        + '<p>ISZE INTERNAL ONLY | ' + views.esc(vmodel.version.version) + ' | '
        + views.esc(vmodel.version.build_date) + '</p>'
        + '<h1>' + views.esc(c.customer) + ' - ' + views.esc(c.name) + '</h1>'
        + '<p><b>' + views.esc(c.pn) + ' | ' + views.esc(c.category) + '</b></p>'
        + '<h2>' + views.esc(c.action) + '</h2><p>' + views.esc(c.verdict) + '</p>'
        + '<aside>No confirmed price-caused lost-sales amount and no approved customer net price. '
        + 'Manual inputs remain assumptions. ' + views.esc(vmodel.cost_rule.accounting_cost_statement) + '</aside>'
        + '<h2>One scenario record</h2>'
        + '<p>Scenario ' + views.esc(pkg.scenario_id) + ' (version ' + pkg.version + '), objective '
        + views.esc(pkg.objective) + ', selected alternative '
        + views.esc(pkg.selected_alternative_id || 'none') + '.</p>'
        + '<p>' + views.esc(cons.statement) + '</p>'
        + '<table><tr><th>Measure</th><th class="n">Unchanged offer</th><th class="n">Proposed offer</th>'
        + '<th class="n">Change</th></tr>'
        + (r.ok ? '<tr><td>Applicable net price</td><td class="n">' + h.eur(r.price_before, 2)
          + '</td><td class="n">' + h.eur(r.price_after, 2) + '</td><td class="n">'
          + h.pct(100 * (r.price_after / r.price_before - 1)) + '</td></tr>'
          + '<tr><td>Eligible quantity</td><td class="n">' + h.num(r.quantity_before, 0) + '</td><td class="n">'
          + h.num(r.quantity_after, 0) + '</td><td class="n">'
          + h.num(r.quantity_after - r.quantity_before, 0) + '</td></tr>'
          + '<tr><td>ISZE revenue</td><td class="n">' + h.eur(r.revenue_before) + '</td><td class="n">'
          + h.eur(r.revenue_after) + '</td><td class="n">' + h.signedEur(r.revenue_change) + '</td></tr>'
          + '<tr><td>Gross profit</td><td class="n">'
          + (r.gp_before === null ? 'Not calculated' : h.eur(r.gp_before)) + '</td><td class="n">'
          + (r.gp_after === null ? 'Not calculated' : h.eur(r.gp_after)) + '</td><td class="n">'
          + (r.gp_change === null ? 'Not calculated' : h.signedEur(r.gp_change)) + '</td></tr>'
          : '<tr><td colspan="4">The scenario is not a valid calculation: '
            + views.esc((r.errors || [r.error]).join(' ')) + '</td></tr>')
        + '</table>'
        + '<h2>Ranking under both objectives</h2>'
        + '<p>' + views.esc(pkg.both_objectives.assumption_check.statement) + '</p>'
        + '<p>Revenue order: ' + views.esc(pkg.both_objectives.revenue_order.join(', ')) + '<br>'
        + 'Gross-profit order: ' + views.esc(pkg.both_objectives.gross_profit_order.join(', ')) + '</p>'
        + '<h2>Change journal on this record</h2><ul>'
        + (pkg.journal.length ? pkg.journal.map(function (j) {
            return '<li>' + views.esc(j.kind) + (j.fields ? ': ' + views.esc(j.fields.join(', ')) : '')
              + (j.alternative_id ? ': ' + views.esc(j.alternative_id) : '')
              + ' (version ' + views.esc(j.version) + ')</li>';
          }).join('') : '<li>No change has been made to the default scenario.</li>')
        + '</ul>'
        + '<h2>Internal review note</h2>'
        + '<p>Owner/role: ' + views.esc(saved[state.case_id] ? saved[state.case_id].owner : c.owner)
        + '. Status: ' + views.esc(saved[state.case_id] ? saved[state.case_id].status : 'Draft review') + '.</p>'
        + '<pre>' + views.esc(saved[state.case_id] ? (saved[state.case_id].note || '') : c.recommendation) + '</pre>'
        + '<footer>This export contains the selected case only. No other case notes, no raw invoices, no full '
        + 'price list and no restricted supplier-cost table are included. It remains internal.</footer></body></html>';
    }

    /* ------------------------------------------------------------- sources -- */

    function sourcesModal(doc) {
      var a = payload.packAudit || {};
      var node = doc.createElement('div');
      node.className = 'screen-overlay';
      var h = views.helpers(engine);
      node.innerHTML = '<section class="modal" role="dialog" aria-modal="true" '
        + 'aria-label="Source and engine basis">'
        + '<div class="modal-head"><div><div class="eyebrow">' + views.esc(vmodel.version.version)
        + ' &middot; accepted in part, not blanket approval</div>'
        + '<h2>What the held evidence supports</h2></div>'
        + '<button class="button" id="close-modal">Close</button></div>'
        + '<div class="panel good"><b>Price history, selected competitor observations and catalogue '
        + 'relationships are connected.</b><p class="small">The five cases and their measured baseline remain. '
        + 'The cost input keeps its own status. An archive cross-reference is not promoted to a comparable '
        + 'quotation.</p></div>'
        + '<p class="small">' + views.esc(vmodel.price_rule.boundary) + '</p>'
        + '<p class="small">' + views.esc(vmodel.cost_rule.accounting_cost_statement) + '</p>'
        + '<p class="small"><b>' + h.num((a.offerScope || {}).rows, 0) + '</b> archive records were inspected; '
        + '<b>' + h.num((a.offerScope || {}).exactCaseRows, 0) + '</b> directly reference the five selected '
        + 'part numbers. Related or unrelated rows are not silently attached to a case.</p>'
        + '<p class="small">Accepted status: ' + views.esc(a.acceptedStatus || 'not declared') + '</p>'
        + '<p class="small">Excluded: ' + views.esc(a.excluded || 'not declared') + '</p>'
        + '<h3>Version</h3><p class="small">' + views.esc(vmodel.version.version)
        + (vmodel.version.supersedes ? ' &middot; supersedes ' + views.esc(vmodel.version.supersedes) : '')
        + '</p>'
        + '<h3>Source inventory</h3>'
        + (payload.sources || []).map(function (s) {
            return '<div class="source-row"><b>' + views.esc(s.title) + ' <span class="badge fact">'
              + views.esc(s.kind) + '</span></b><span class="small">' + views.esc(s.date) + '</span>'
              + '<p class="small">' + views.esc(s.basis) + '</p><code>' + views.esc(s.file) + '</code></div>';
          }).join('')
        + '<h3>Unchanged boundaries</h3><p class="small">A billing fall is not proof of price-caused lost '
        + 'sales. National purchasing does not identify a single dealer. No part-level fleet is manufactured, '
        + 'and no approved margin floor or cost is assumed. This internal file contains both pilots; filtering '
        + 'is not access control.</p></section>';
      doc.body.append(node);
      var close = doc.getElementById('close-modal');
      if (close) { close.onclick = function () { node.remove(); }; close.focus(); }
      node.onclick = function (e) { if (e.target === node) node.remove(); };
      node.onkeydown = function (e) { if (e.key === 'Escape') node.remove(); };
    }

    function toast(doc, text) {
      if (!doc) return;
      var n = doc.createElement('div');
      n.className = 'toast';
      n.textContent = text;
      doc.body.append(n);
      setTimeout(function () { n.remove(); }, 4000);
    }

    /* --------------------------------------------------------------- public -- */

    return {
      state: function () { return Object.assign({}, state); },
      go: go, paint: paint, probe: probe, build: build,
      setMarket: setMarket, setCompare: setCompare, setObjective: setObjective,
      setBillingMetric: setBillingMetric, openPart: openPart,
      scenario: scenario, workbench: workbench, vmodel: vmodel, cases: cases,
      saved: saved,
      auditLog: function () { return log.slice(); },
      onPaint: function (fn) { listeners.push(fn); },
      currentCase: currentCase,
      caseById: caseById,
      exportFile: exportFile,
      saveNote: saveNote,
      collectNote: collectNote,
      TAB_LABELS: TAB_LABELS
    };
  }

  return { makeShell: makeShell, TAB_LABELS: TAB_LABELS };
});
