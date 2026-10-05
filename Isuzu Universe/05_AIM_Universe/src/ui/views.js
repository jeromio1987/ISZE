/* ===========================================================================
   The six working views (F05, F10, F11, UX-06, REVIEW-02, REVIEW-04).

   Rules this file follows, because v03 broke them:

   1. Every number comes from the engine module (src/engine/engine.js) or from the
      embedded payload. The view layer formats; it does not calculate. The v03
      turbo crash was a view calling a formatter that only exists inside the
      engine's closure, so all formatting here goes through the engine's exported
      helpers.

   2. Cost and price status are read from the view model, never typed as prose.
      That is why the page no longer says "Decision component 0.2", no longer asks
      a reader to settle a resolved turbo price conflict, and no longer demands an
      accounting cost the declared rule has dropped.

   3. A view returns HTML or an exactly-formed structure. It never returns nothing
      and leaves the previous view on screen — the shell in render.js owns that.

   4. Where the payload cannot support a number, the view prints the quantity
      required and the test, in an amber unavailable block. It never prints a
      blank panel and it never invents a figure.
   =========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./failure.js'));
  } else {
    root.AIMUI = root.AIMUI || {};
    root.AIMUI.views = factory(root.AIMFailure);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (failure) {
  'use strict';

  /* ------------------------------------------------------------- formatting -- */

  function esc(v) {
    return String(v === null || v === undefined ? '' : v)
      .replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
  }

  /* Formatting calls the engine's own exported helpers where one exists, because
     a second formatter is how the two screens drifted apart in v03. */
  function helpers(engine) {
    var fmtNum = (engine && engine.fmtNum) || function (x, d) {
      if (x === null || x === undefined || !Number.isFinite(Number(x))) return '-';
      return Number(x).toLocaleString('en-GB', { minimumFractionDigits: d, maximumFractionDigits: d });
    };
    var fmtPct = (engine && engine.fmtPct) || function (x) {
      if (x === null || x === undefined || !Number.isFinite(Number(x))) return '-';
      return (x > 0 ? '+' : '') + Number(x).toFixed(1) + '%';
    };
    return {
      num: function (x, d) {
        return (x === null || x === undefined || !Number.isFinite(Number(x))) ? 'Not supplied' : fmtNum(x, d);
      },
      numOr: function (x, d, fallback) {
        return (x === null || x === undefined || !Number.isFinite(Number(x))) ? fallback : fmtNum(x, d);
      },
      pct: function (x) { return (x === null || x === undefined) ? 'Not comparable' : fmtPct(x); },
      pctOr: function (x, fallback) { return (x === null || x === undefined) ? fallback : fmtPct(x); },
      eur: function (x, d) {
        if (x === null || x === undefined || !Number.isFinite(Number(x))) return 'Not calculated';
        return new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR',
          minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }).format(x);
      },
      eurOr: function (x, d, fallback) {
        if (x === null || x === undefined || !Number.isFinite(Number(x))) return fallback;
        return new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR',
          minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }).format(x);
      },
      signedEur: function (x, d) {
        if (x === null || x === undefined || !Number.isFinite(Number(x))) return 'Not calculated';
        return (x > 0 ? '+' : '') + this.eur(x, d);
      },
      color: function (v) { return v < 0 ? 'neg' : v > 0 ? 'pos' : ''; }
    };
  }

  var BANNED = [
    { re: /\bMode\s*[AB]\b/i, why: 'audience label' },
    { re: /\bwallet\b/i, why: 'wallet wording' },
    { re: /\bstreet\b/i, why: 'street wording' },
    { re: /sell-?out/i, why: 'say sales to dealer' },
    { re: /\bBook\s*B\b/i, why: 'say the price list' },
    { re: /\bclass\s*factor\b/i, why: 'talk in margins, not factors' }
  ];

  /* A guard, not a promise. The shell runs it over the built HTML before paint,
     so a banned word cannot reach a reader even if a template later slips. */
  function bannedWords(html) {
    var findings = [];
    BANNED.forEach(function (b) {
      var m = String(html).match(b.re);
      if (m) findings.push({ word: m[0], why: b.why });
    });
    return findings;
  }

  /* --------------------------------------------------- shared small blocks -- */

  function unavailableBlock(u) {
    if (!u) return '';
    return '<div class="panel unavailable" role="status"><div class="eyebrow">Unavailable</div>'
      + '<h3>' + esc(u.title) + '</h3>'
      + '<p class="small">' + esc(u.reason) + '</p>'
      + (u.required ? '<div class="evidence-line"><span>What is required</span><b>'
          + esc(u.required) + '</b></div>' : '')
      + (u.scope ? '<div class="evidence-line"><span>Scope</span><b>' + esc(u.scope) + '</b></div>' : '')
      + '</div>';
  }

  /* REVIEW-04: the exact original part references stay visible on every view. */
  function partStrip(c, ctx) {
    var related = (c.related || []).slice();
    return '<div class="part-strip" aria-label="Exact part references">'
      + '<span class="part-strip-label">Exact part references</span>'
      + '<span class="pn pn-strong">' + esc(c.pn) + '</span>'
      + '<span class="small">' + esc(c.name) + ' &middot; ' + esc(c.tier || '') + ' &middot; unit: ' + esc(c.unit) + '</span>'
      + (related.length ? '<span class="part-strip-related">Related numbers recorded: '
          + related.map(function (pn) { return '<span class="pn">' + esc(pn) + '</span>'; }).join(' ') + '</span>' : '')
      + '</div>';
  }

  function statusGrid(vm) {
    var rows = (vm.rows || []).map(function (r) {
      return '<div class="status-row status-' + esc(r.status) + '">'
        + '<span class="badge ' + (r.status === 'held' ? 'fact' : r.status === 'partial' ? 'assumption' : 'review') + '">'
        + esc(r.status_label) + '</span>'
        + '<div><b>' + esc(r.label) + '</b><p class="small">' + esc(r.detail) + '</p>'
        + '<code class="small">' + esc(r.pointer) + '</code>'
        + (r.required ? '<p class="small">Required: ' + esc(r.required) + '</p>' : '')
        + '</div></div>';
    }).join('');
    return '<div class="panel"><div class="eyebrow">Status, read from the payload</div>'
      + '<h3>What is held and what is not</h3>'
      + '<p class="small">Each line names where it was read from. A record existing is not the same as a '
      + 'status being verified. Commercial priority is shown separately, below.</p>'
      + '<div class="status-grid">' + rows + '</div></div>';
  }

  /* REVIEW-02: coverage is not a cleared decision, and priority is a separate
     axis from completeness. Both are printed as separate blocks. */
  function coverageAndPriority(c, ctx) {
    var vm = ctx.vmodel.case_status(c.id);
    var comp = ctx.vmodel.completeness(vm);
    var pri = vm.commercial_priority || { label: 'Not established', basis: 'no comparison held' };
    return '<div class="grid2">'
      + '<div class="panel"><div class="eyebrow">Commercial priority</div>'
      + '<h3>' + esc(pri.label) + '</h3><p class="small">' + esc(pri.basis) + '</p>'
      + '<p class="small">This says how much money is at stake. It does not say how much of the '
      + 'evidence is held, and it is not a recommendation.</p></div>'
      + '<div class="panel"><div class="eyebrow">Evidence completeness</div>'
      + '<h3>' + esc(comp.statement) + '</h3><p class="small">' + esc(comp.basis) + '</p>'
      + '<p class="small">Coverage is coverage. A price and cost record being held is not a cleared '
      + 'price decision.</p></div></div>';
  }

  function notSaidPanel(c, ctx) {
    var rules = (ctx.payload.meta && ctx.payload.meta.confirmedRules) || {};
    return '<div class="panel dark"><h3>What this does not say</h3>'
      + '<p>No minimum gross margin and no acceptable profit sacrifice are confirmed, so both approval '
      + 'controls are deliberately unset. That absence does not block these calculations; it blocks approval.</p>'
      + '<div class="evidence-line"><span>Minimum gross margin control</span><b>'
      + esc(rules.minMarginStatus || 'not declared') + '</b></div>'
      + '<div class="evidence-line"><span>Acceptable profit sacrifice control</span><b>'
      + esc(rules.maxProfitSacrificeStatus || 'not declared') + '</b></div>'
      + '<p class="small">No optimum price, no elasticity, no volume response and no measured benefit are '
      + 'stated anywhere in this component. Where a number cannot be supported, the quantity required and '
      + 'the test are printed instead.</p>'
      + '<p class="small">' + esc(c.counter || '') + '</p></div>';
  }

  /* ------------------------------------------------------------- view: price -- */

  function stats(c, state, h) {
    var x = c.comparisons[state.compare], a = x.prior, z = x.current;
    return '<div class="stats">'
      + '<div class="stat"><div class="label">Change in recorded ISZE billing</div>'
      + '<strong class="' + h.color(x.revenueDelta) + '">' + h.signedEur(x.revenueDelta) + '</strong>'
      + '<div class="detail">' + h.eur(a.eur) + ' to ' + h.eur(z.eur)
      + '<br>Measured billing for this exact part. Not a price-caused loss.</div></div>'
      + '<div class="stat"><div class="label">Observed net unit price</div><strong>' + h.eur(z.price, 2) + '</strong>'
      + '<div class="detail">' + h.eur(a.price, 2) + ' before &middot; ' + h.pct(x.priceChangePct)
      + '<br>Includes order and commercial-term mix.</div></div>'
      + '<div class="stat"><div class="label">ISZE quantity change</div>'
      + '<strong class="' + h.color(x.quantityChangePct) + '">' + h.pct(x.quantityChangePct) + '</strong>'
      + '<div class="detail">' + h.num(a.quantity) + ' to ' + h.num(z.quantity) + ' ' + esc(c.unit)
      + 's<br>Purchases from ISZE.</div></div>'
      + '<div class="stat"><div class="label">Sales-to-dealer change</div>'
      + '<strong class="' + h.color(x.onwardChangePct) + '">'
      + h.pctOr(x.onwardChangePct, 'Not comparable') + '</strong>'
      + '<div class="detail">' + h.num(a.salesToDealer) + ' to ' + h.num(z.salesToDealer) + ' ' + esc(c.unit)
      + 's<br>Separate national wholesale flow.</div></div></div>';
  }

  function chart(c, state, h, key, title, line) {
    var cmp = c.comparisons[state.compare];
    var years = [cmp.prior.year, cmp.current.year];
    var months = cmp.current.months;
    var a = [], b = [];
    for (var i = 0; i < months; i++) {
      a.push(c.series.find(function (r) { return r.year === years[0] && r.month === i + 1; }));
      b.push(c.series.find(function (r) { return r.year === years[1] && r.month === i + 1; }));
    }
    var vals = a.concat(b).map(function (r) { return r ? r[key] : null; })
      .filter(function (v) { return v !== null && v !== undefined; });
    var width = 500, height = 215, left = 42, top = 17, bottom = 36, right = 14;
    var plotH = height - top - bottom, plotW = width - left - right;
    var max = Math.max(1, Math.max.apply(null, vals.length ? vals : [1]));
    var min = Math.min(0, Math.min.apply(null, vals.length ? vals : [0]));
    max *= 1.13;
    if (min < 0) min *= 1.13;
    var yy = function (v) { return top + (max - v) / (max - min) * plotH; };
    var slot = plotW / months;
    var xx = function (i) { return left + slot * (i + 0.5); };
    var barw = Math.min(16, slot * 0.31);
    var svg = '<svg class="chart" viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="'
      + esc(title) + '; ' + years.join(' compared with ') + '">';
    for (var g = 0; g <= 3; g++) {
      var gv = min + (max - min) * g / 3, gy = yy(gv);
      svg += '<line x1="' + left + '" x2="' + (width - right) + '" y1="' + gy + '" y2="' + gy + '" stroke="#e4ebf0"/>'
        + '<text x="' + (left - 6) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="10" fill="#6b7c8c">'
        + (key === 'billingEUR' && Math.abs(gv) >= 1000 ? h.num(gv / 1000, 1) + 'k' : h.num(gv, 0)) + '</text>';
    }
    var names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    [a, b].forEach(function (series, si) {
      var fill = si === 0 ? '#193d58' : '#008374';
      var segment = [];
      function endSeg() {
        if (segment.length > 1) {
          svg += '<polyline points="' + segment.join(' ') + '" fill="none" stroke="' + fill + '" stroke-width="2.5"/>';
        }
        segment = [];
      }
      series.forEach(function (r, i) {
        var v = r ? r[key] : null;
        if (v === null || v === undefined) { endSeg(); return; }
        if (line) {
          segment.push(xx(i) + ',' + yy(v));
          svg += '<circle cx="' + xx(i) + '" cy="' + yy(v) + '" r="3.8" fill="' + fill
            + '"><title>' + names[i] + ' ' + years[si] + ': ' + h.eur(v, 2) + '</title></circle>';
        } else {
          var bx = xx(i) + (si === 0 ? -barw - 1 : 1), by = yy(v), zero = yy(0);
          svg += '<rect x="' + bx + '" y="' + Math.min(by, zero) + '" width="' + barw + '" height="'
            + Math.max(1.3, Math.abs(zero - by)) + '" rx="2" fill="' + fill + '"' + (v === 0 ? ' opacity=".24"' : '')
            + '><title>' + names[i] + ' ' + years[si] + ': ' + h.num(v) + (v === 0 ? ' (no recorded line)' : '')
            + '</title></rect>';
        }
      });
      endSeg();
    });
    a.forEach(function (r, i) {
      var vals2 = [a[i] ? a[i][key] : null, b[i] ? b[i][key] : null];
      var money = key === 'price' || key === 'billingEUR';
      var description = names[i] + ': ' + years[0] + ' '
        + (money ? h.eurOr(vals2[0], 2, 'no recorded line') : h.numOr(vals2[0], 0, 'no recorded line'))
        + '; ' + years[1] + ' '
        + (money ? h.eurOr(vals2[1], 2, 'no recorded line') : h.numOr(vals2[1], 0, 'no recorded line'));
      svg += '<g class="month-hit" tabindex="0" role="button" aria-label="' + esc(description)
        + '" data-readout="' + esc(description) + '" data-chart="' + esc(key) + '">'
        + '<rect class="hit" x="' + (left + slot * i) + '" y="' + top + '" width="' + slot + '" height="'
        + (plotH + 27) + '" fill="transparent"/>'
        + '<text x="' + xx(i) + '" y="' + (height - 12) + '" text-anchor="middle" fill="#6b7c8c" font-size="10">'
        + names[i] + '</text></g>';
    });
    svg += '</svg>';
    var note = key === 'price'
      ? 'Price = positive billed EUR / positive billed quantity. A gap means no observed price, not a zero price.'
      : key === 'onwardQuantity'
        ? 'National monthly rows only, signed quantities. No dealer attribution and no end-customer consumption is inferred.'
        : 'Positive ISZE billing. A zero-height bar means no recorded line, not proven zero demand.';
    return '<div class="panel"><div class="chart-title"><h3>' + esc(title) + '</h3><span class="small">'
      + (key === 'price' ? 'EUR per unit' : key === 'billingEUR' ? 'Recorded EUR' : 'Recorded units')
      + (key.indexOf('billing') === 0 ? ' &middot; <button class="linkbutton" data-billing-toggle>'
          + (key === 'billingEUR' ? 'Show units' : 'Show EUR') + '</button>' : '')
      + '</span></div><div class="legend"><span><i></i>' + years[0] + '</span><span><i class="new"></i>'
      + years[1] + '</span></div>' + svg + '<div class="chart-note">' + note + '</div>'
      + '<div class="month-readout" id="readout-' + esc(key) + '">Select a month to inspect its values.</div></div>';
  }

  function termsTable(c) {
    var rows = '';
    [['2024 full year', c.annual['2024']], ['2025 full year', c.annual['2025']],
      ['2026 Jan-Jun', c.half['2026']]].forEach(function (pair) {
      var obj = pair[1];
      if (!obj) return;
      (obj.orderTypes || []).forEach(function (r) {
        rows += '<tr><td>' + esc(pair[0]) + '</td><td>' + esc(r.type) + '</td><td class="n">'
          + r.quantity + '</td><td class="n">' + (r.price === null ? '-' : Number(r.price).toFixed(2)) + '</td></tr>';
      });
    });
    return '<details><summary>Separate order terms from a price-list change</summary>'
      + '<p>Prices below are measured effective billing averages within the recorded order type. The source '
      + 'order-type code is shown as recorded; its contractual conditions are not reconstructed. A blank 2026 '
      + 'type is not assumed to be SOR.</p><div class="tablewrap"><table><thead><tr><th>Period</th>'
      + '<th>Recorded type</th><th class="n">Units</th><th class="n">EUR / unit</th></tr></thead><tbody>'
      + rows + '</tbody></table></div></details>';
  }

  function sourceButton() {
    return '<button class="sourcesbutton" data-sources>Source and calculation basis</button>';
  }

  function viewDecision(ctx, c) {
    var h = ctx.h, state = ctx.state;
    var cmp = c.comparisons[state.compare];
    var e = c.packEvidence;
    var vm = ctx.vmodel.case_status(c.id);
    return '<div class="compare-row"><div><span class="eyebrow">Measured record</span>'
      + '<div class="small">' + sourceButton() + ' &middot; no forecast and no lost-sales attribution</div></div>'
      + '<select id="comparison" aria-label="Comparison period">'
      + '<option value="half"' + (state.compare === 'half' ? ' selected' : '') + '>January-June 2026 vs 2025</option>'
      + '<option value="annual"' + (state.compare === 'annual' ? ' selected' : '') + '>Calendar 2025 vs 2024</option>'
      + '</select></div>'
      + stats(c, state, h)
      + '<div class="panel ' + (e.listConflict ? 'warn' : 'callout') + ' imported-callout">'
      + '<div class="eyebrow">Recorded list prices for this exact part</div>'
      + '<h3>' + (e.listConflict ? 'Two recorded list amounts are held' : 'Recorded list is consistent') + '</h3>'
      + (e.listConflict ? '<p><b>' + e.recordedListCandidates.map(function (v) { return h.eur(v, 2); }).join(' and ')
          + '</b> are both held. Neither is a confirmed customer net price, and the reader is not asked to '
          + 'settle them here: the resolution and its precedence rule are stated on the price position view.</p>' : '')
      + '<p>' + esc(c.verdict) + '</p>'
      + '<div class="readiness-chips">' + vm.rows.map(function (r) {
          return '<span class="badge ' + (r.status === 'held' ? 'fact' : r.status === 'partial' ? 'assumption' : 'review')
            + '">' + esc(r.label) + ': ' + esc(r.status_label) + '</span>';
        }).join('') + '</div>'
      + '<div class="rowactions"><button class="linkbutton" data-view="position">Read the price history '
      + 'and offers &rarr;</button><button class="linkbutton" data-sources>What passed the source review?</button>'
      + '</div></div>'
      + '<div class="grid2">'
      + chart(c, state, h, state.billing_metric,
          state.billing_metric === 'billingEUR' ? 'What ISZE billed' : 'What ISZE supplied')
      + chart(c, state, h, 'onwardQuantity', 'What the distributor supplied to dealers') + '</div>'
      + '<div class="grid2"><div class="panel"><span class="badge fact">Evidence supporting review</span>'
      + '<p style="margin-top:12px">' + esc(c.reason) + '</p></div>'
      + '<div class="panel warn"><span class="badge review">Evidence against a simple price story</span>'
      + '<p style="margin-top:12px">' + esc(c.counter) + '</p></div></div>'
      + '<div class="grid2">' + chart(c, state, h, 'price', 'Observed ISZE unit price', true)
      + '<div class="panel"><div class="eyebrow">Reconcile the euro movement</div>'
      + '<h3>' + h.signedEur(cmp.revenueDelta) + ' in recorded billing</h3>'
      + '<div class="evidence-line"><span>Quantity effect, at the prior price</span><b class="'
      + h.color(cmp.volumeEffect) + '">' + h.signedEur(cmp.volumeEffect) + '</b></div>'
      + '<div class="evidence-line"><span>Effective price and terms effect</span><b class="'
      + h.color(cmp.effectivePriceEffect) + '">' + h.signedEur(cmp.effectivePriceEffect) + '</b></div>'
      + '<div class="ruleline small">Exact identity: (new quantity &minus; old quantity) &times; old price '
      + '+ new quantity &times; (new price &minus; old price). The second term includes mix of order '
      + 'conditions. It is not causal price elasticity and not a measured price-list effect.</div>'
      + '<div class="scopebox"><b>' + h.num(c.fleet) + ' ' + (c.market === 'ITUK' ? 'trucks' : 'vehicles')
      + ' &middot; 2025 market reference</b><br>' + esc(c.application)
      + ' No part-level demand gap and no dealer rate is computed.</div></div></div>'
      + coverageAndPriority(c, ctx)
      + termsTable(c)
      + '<div class="panel callout"><h3>The next commercial action</h3><p>' + esc(c.next) + '</p>'
      + '<div class="rowactions"><button class="button primary" data-view="economics">Test price and gross '
      + 'profit</button><button class="button" data-view="action">Prepare the internal review</button>'
      + '</div></div>'
      + notSaidPanel(c, ctx);
  }

  /* ---------------------------------------------------------- view: position -- */

  function offerTable(offers, h) {
    if (!offers.length) {
      return unavailableBlock(failure.unavailable({
        title: 'No priced exact-number record is held',
        reason: 'No dated advertised record for this exact part number is in the held evidence. That is a '
          + 'gap in the file, not a statement that no competing offer exists.',
        required: 'a dated quotation naming the part number, its contents, its tax basis and its delivery charge',
        scope: 'held competitor observations'
      }));
    }
    return '<div class="tablewrap"><table class="offers-table"><thead><tr>'
      + '<th>Seller / manufacturer part</th><th>Advertised amount</th><th>Tax / contents</th>'
      + '<th>Use and provenance</th></tr></thead><tbody>'
      + offers.map(function (o) {
          return '<tr><td><b>' + esc(o.brand || 'Not supplied') + '</b><br><span class="pn">'
            + esc(o.manufacturer_part_number || 'Not supplied') + '</span><br>' + esc(o.seller) + '</td>'
            + '<td class="n">' + (o.price_original ? esc(o.currency_original) + ' '
              + h.num(Number(o.price_original), 2) : 'No usable price')
            + '<br><span class="small">' + esc(o.observation_date) + '</span></td>'
            + '<td>' + esc(o.vat_included_excluded) + '<br><span class="small">' + esc(o.pack_quantity)
            + '; ' + esc(o.kit_contents) + '</span></td>'
            + '<td><b>' + esc(o.use) + '</b><br><span class="small">' + esc(o.match_reason) + '<br>'
            + esc(o.historical_label) + '</span></td></tr>';
        }).join('') + '</tbody></table></div>';
  }

  function viewPosition(ctx, c) {
    var h = ctx.h;
    var e = c.packEvidence;
    var leads = (e.offers || []).filter(function (o) { return o.independent_offer; });
    var other = (e.offers || []).filter(function (o) { return !o.independent_offer; });
    var priceRule = ctx.vmodel.price_rule;
    var turbo = c.id === 'ITUK-TURBO' ? ctx.vmodel.turbo : null;

    var snapshotPoints = (e.snapshots || []).map(function (r) {
      return { label: String(r.list_version).replace('snapshot ', ''), price: h.eur(r.amount, 2) };
    });
    snapshotPoints.push({ label: '2026 recorded list', price: (e.recordedListCandidates || [])
      .map(function (v) { return h.eur(v, 2); }).join(' / ') });

    return (turbo ? '<div class="panel callout"><div class="eyebrow">Resolved before this screen</div>'
      + '<h3>The turbo list-price conflict is already settled. It is not a question for the reader.</h3>'
      + '<p>' + esc(turbo.statement) + '</p>'
      + '<div class="evidence-line"><span>Applicable list price for billing</span><b>'
      + h.eur(turbo.resolved_billable_list, 2) + '</b></div>'
      + '<div class="evidence-line"><span>Second observation, kept as a sensitivity</span><b>'
      + turbo.sensitivity_range.map(function (v) { return h.eur(v, 2); }).join(' / ') + '</b></div>'
      + '<div class="evidence-line"><span>Resolved by</span><b class="small">' + esc(turbo.resolved_by) + '</b></div>'
      + '<p class="small">' + esc(turbo.observed_billing_note || '') + '</p>'
      + '<p class="small"><b>Still open:</b> ' + esc(turbo.open_statement || '') + '</p></div>' : '')

      + '<div class="panel"><div class="eyebrow">Price levels kept separate</div>'
      + '<h3>List snapshots are not the prices invoiced to this customer.</h3>'
      + '<div class="snapshot-grid">' + snapshotPoints.map(function (p, i) {
          return '<div class="snapshot' + (i === snapshotPoints.length - 1 && e.listConflict
            ? ' snapshot-conflict' : '') + '"><span>' + esc(p.label) + '</span><strong>' + p.price
            + '</strong><small>EUR per supplied price unit; tax excluded</small></div>';
        }).join('') + '</div>'
      + '<p class="small">A dated list movement and a weighted billing movement are not interchangeable. No '
      + 'list snapshot is applied backwards to reprice historic sales. ' + esc(priceRule.boundary) + '</p>'
      + '<details><summary>Every recorded price source and validity field</summary>'
      + '<div class="tablewrap"><table><thead><tr><th>Observation</th><th>EUR / price unit</th>'
      + '<th>Recorded validity</th><th>Source and trace</th></tr></thead><tbody>'
      + (e.prices || []).map(function (r) {
          return '<tr><td>' + esc(r.list_version) + '<br><span class="small">' + esc(r.observation_type)
            + '</span></td><td class="n">' + h.eur(r.amount, 2) + '</td><td>' + esc(r.valid_from) + ' &rarr; '
            + esc(r.valid_to) + '</td><td>' + esc(r.source_reference) + '<br><span class="small">'
            + esc(r.pointer) + '</span></td></tr>';
        }).join('') + '</tbody></table></div>'
      + '<p class="small">Open-ended and overlapping fields are carried as source values. They are not '
      + 'interpreted as an authoritative continuous price history, and duplicate sources do not become '
      + 'independent prices.</p></details></div>'

      + (turbo ? '' : '<div class="panel"><div class="compare-row"><div>'
        + '<div class="eyebrow">Held archive &middot; exact part ' + esc(c.pn) + '</div>'
        + '<h3>' + (leads.length ? leads.length + ' advertised record(s) held'
          : 'No priced lead in the held evidence for the exact number') + '</h3></div>'
        + '<span class="badge review">No approved comparable quotation</span></div>'
        + '<p class="small">These are dated advertised observations, not current customer quotations. An '
        + 'accepted seller cross-reference is not approval of fitment, kit contents, a delivered price or a '
        + 'tax-normalised comparison. No fresh web validation was performed for this revision.</p>'
        + offerTable(leads, h)
        + (other.length ? '<details><summary>' + other.length + ' unresolved, rejected or derived record(s) '
            + 'kept out of the price decision</summary>' + offerTable(other, h) + '</details>' : '')
        + '</div>')

      + statusGrid(ctx.vmodel.case_status(c.id))
      + '<div class="panel warn"><h3>What remains unresolved for this case</h3><div class="acceptance-grid">'
      + (e.readiness || []).map(function (r) {
          return '<div><b>' + esc(r.name) + '</b><p class="small">' + esc(r.status) + '</p></div>';
        }).join('') + '</div>'
      + '<p class="small">' + esc(ctx.vmodel.cost_rule.accounting_cost_statement)
      + ' ' + esc(priceRule.boundary) + '</p>'
      + '<button class="button primary" data-view="economics">Test a stated price, not an inferred optimum</button>'
      + '</div>'
      + notSaidPanel(c, ctx);
  }

  /* -------------------------------------------------------- view: objectives -- */

  function objectiveRows(twin, objective, h, scenario, caseId) {
    var rows = twin[objective].rows;
    if (!rows.length) {
      return unavailableBlock(failure.unavailable({
        title: 'No alternative is recorded for this case',
        reason: 'The payload holds no priced alternative for this exact part, so there is nothing to rank. '
          + 'The ranking is not empty because the view failed.',
        required: 'at least one stated alternative for this case',
        scope: 'case alternatives'
      }));
    }
    return '<div class="tablewrap"><table><thead><tr><th>Rank</th><th>Alternative</th><th class="n">Price</th>'
      + '<th class="n">Revenue change</th><th class="n">Gross-profit change</th><th class="n">Margin after</th>'
      + '<th>Volume basis</th><th>Flags</th></tr></thead><tbody>'
      + rows.map(function (row, i) {
          var r = row.result;
          var selected = scenario.get(caseId).selected_alternative_id === row.alternative.alternative_id;
          return '<tr' + (selected ? ' class="row-selected"' : '') + '><td class="n">' + (i + 1) + '</td>'
            + '<td><b>' + esc(row.alternative.name) + '</b><div class="small">'
            + esc(row.alternative.eligibility || '') + '</div>'
            + (row.alternative.evidence ? '<div class="small">' + esc(row.alternative.evidence) + '</div>' : '')
            + '<div class="rowactions" style="margin-top:6px">'
            + '<button class="linkbutton" data-select-alternative="' + esc(row.alternative.alternative_id)
            + '"' + (selected ? ' aria-pressed="true"' : '') + '>'
            + (selected ? 'Selected into the scenario' : 'Use this option in the scenario') + '</button></div></td>'
            + '<td class="n">' + (r.ok ? h.eur(r.price_after, 2) : (r.migration_status === 'unresolved'
              ? '<span class="badge review">Unresolved</span>' : 'error')) + '</td>'
            + '<td class="n ' + (r.ok ? h.color(r.revenue_change) : '') + '">'
            + (r.ok ? h.signedEur(r.revenue_change) : '-') + '</td>'
            + '<td class="n ' + (r.ok ? h.color(r.gp_change) : '') + '">'
            + (!r.ok ? '-' : r.gp_change === null ? 'Cost required' : h.signedEur(r.gp_change)) + '</td>'
            + '<td class="n">' + (r.ok && r.margin_after_pct !== null ? h.num(r.margin_after_pct, 1) + '%' : '-')
            + '</td>'
            + '<td class="small">' + esc(row.alternative.volume_label || '') + '</td>'
            + '<td>' + flags(r) + '</td></tr>';
        }).join('') + '</tbody></table></div>';
  }

  function flags(r) {
    if (!r || !r.ok) return r && r.migration_status === 'unresolved'
      ? '<span class="badge review">Not priced as a single part</span>' : '';
    if (!r.flags || !r.flags.length) return '<span class="badge hold">No trade-off flagged</span>';
    return r.flags.map(function (f) {
      return '<span class="badge ' + (f.severity === 'high' ? 'review' : 'assumption') + '">'
        + esc(f.text) + '</span>';
    }).join(' ');
  }

  function stateTable(r, c, h) {
    if (!r.ok) {
      return '<div class="panel warn error-msg"><h3>This alternative is not priced as a single part</h3>'
        + '<p>' + esc(r.error) + '</p>'
        + '<p class="small">No figure is substituted for it. Business moved between Genuine and BVP is not '
        + 'new business, and it is reported separately when it is measured.</p></div>';
    }
    var gp = r.gp_change === null;
    var unavailable = failure.unavailable({});
    function gpCell(v, d) {
      return gp ? unavailableBlock(Object.assign({}, unavailable, {
        title: 'Gross profit not calculated',
        reason: 'No verified parts purchase cost is held for this exact part, so gross profit and gross '
          + 'margin are not calculated. Revenue still is.',
        required: 'the parts purchase cost for this part, per the declared supplier cost measure'
      })) : h.eurOr(v, d, 'Not calculated');
    }
    return '<div class="tablewrap"><table><thead><tr><th>Measure</th><th class="n">Unchanged offer</th>'
      + '<th class="n">Proposed offer</th><th class="n">Change</th></tr></thead><tbody>'
      + '<tr><td>Applicable net price, EUR/' + esc(c.unit) + '</td><td class="n">' + h.eur(r.price_before, 2)
      + '</td><td class="n">' + h.eur(r.price_after, 2) + '</td><td class="n '
      + h.color(r.price_after - r.price_before) + '">'
      + h.pct(100 * (r.price_after / r.price_before - 1)) + '</td></tr>'
      + '<tr><td>Eligible quantity</td><td class="n">' + h.num(r.quantity_before, 0) + '</td><td class="n">'
      + h.num(r.quantity_after, 0) + '</td><td class="n">' + h.num(r.quantity_after - r.quantity_before, 0)
      + '</td></tr>'
      + '<tr><td>ISZE revenue</td><td class="n">' + h.eur(r.revenue_before) + '</td><td class="n">'
      + h.eur(r.revenue_after) + '</td><td class="n ' + h.color(r.revenue_change) + '">'
      + h.signedEur(r.revenue_change) + '</td></tr>'
      + '<tr><td>Parts purchase cost applied</td><td class="n" colspan="2">'
      + (r.cost === null ? '<span class="danger-line">No verified cost held</span>'
        : h.eur(r.cost, 2) + ' / ' + esc(c.unit)) + '</td><td class="n">'
      + (r.cost === null ? 'gross profit not calculated' : 'parts purchase cost only') + '</td></tr>'
      + '<tr><td>Gross profit</td><td class="n">' + gpCell(r.gp_before) + '</td><td class="n">'
      + gpCell(r.gp_after) + '</td><td class="n ' + (gp ? '' : h.color(r.gp_change)) + '">'
      + (gp ? '<span class="badge review">Cost required</span>' : h.signedEur(r.gp_change)) + '</td></tr>'
      + '<tr><td>Gross margin</td><td class="n">' + (gp ? '-' : h.num(r.margin_before_pct, 1) + '%') + '</td>'
      + '<td class="n">' + (gp ? '-' : h.num(r.margin_after_pct, 1) + '%') + '</td><td class="n '
      + (gp ? '' : h.color(r.margin_pp_change)) + '">'
      + (gp ? '-' : h.pct(r.margin_pp_change) + ' pp') + '</td></tr>'
      + '<tr><td>Discount given away on volume already buying</td><td class="n" colspan="2">'
      + esc(r.scope === 'all' ? 'applies to all eligible volume' : 'incremental units only') + '</td>'
      + '<td class="n ' + (r.discount_on_existing_volume_eur > 0 ? 'danger-line' : '') + '">'
      + h.eur(r.discount_on_existing_volume_eur) + '</td></tr>'
      + '</tbody></table></div>'
      + '<p class="small ruleline">Quantity basis: <b>' + esc(r.quantity_label)
      + '</b>. No volume response to a price change is assumed.</p>'
      + (r.conditional && r.conditional.length
        ? '<div class="panel warn" style="margin-top:12px"><h3>What remains conditional</h3>'
          + r.conditional.map(function (t) { return '<p class="small">' + esc(t) + '</p>'; }).join('')
          + '</div>' : '');
  }

  function breakEvenTable(r, ctx, h) {
    if (!r.ok) return '';
    var gp = r.gp_change === null;
    var rows = [
      { test: 'Preserve revenue', total: r.qty_preserve_revenue, extra: r.extra_qty_to_preserve_revenue,
        label: r.qty_preserve_revenue_label, cost: false },
      { test: 'Preserve gross profit', total: r.qty_preserve_gp, extra: r.extra_qty_to_preserve_gp,
        label: r.qty_preserve_gp_label, cost: gp },
      { test: 'Exceed revenue', total: (r.qty_preserve_revenue === null ? null
          : r.qty_preserve_revenue + r.extra_qty_to_exceed_revenue), extra: r.extra_qty_to_exceed_revenue,
        label: r.extra_qty_exceed_revenue_label, cost: false },
      { test: 'Exceed gross profit', total: (r.qty_preserve_gp === null ? null
          : r.qty_preserve_gp + r.extra_qty_to_exceed_gp), extra: r.extra_qty_to_exceed_gp,
        label: r.extra_qty_exceed_gp_label, cost: gp }
    ];
    return '<div class="panel"><h3>The volume each measure needs</h3>'
      + '<p class="small">Both break-even quantities are stated as quantities you can order, not as a '
      + 'threshold plus a rounding cent.</p><div class="tablewrap"><table><thead><tr><th>Test</th>'
      + '<th class="n">Required total quantity</th><th class="n">Additional quantity</th>'
      + '<th>What the quantity means</th></tr></thead><tbody>'
      + rows.map(function (row) {
          return '<tr><td>' + esc(row.test) + '</td><td class="n">'
            + (row.cost ? '<span class="badge review">Cost required</span>'
              : row.total === null ? '<span class="danger-line">Not attainable at this price</span>'
              : h.num(row.total, 0)) + '</td><td class="n">'
            + (row.cost || row.extra === null ? (row.cost ? '-' : '<span class="danger-line">Not attainable</span>')
              : h.num(row.extra, 0)) + '</td><td class="small">' + esc(row.label || '') + '</td></tr>';
        }).join('')
      + (r.price_after > r.price_before ? '<tr><td><b>Tolerable volume loss</b></td>'
          + '<td class="n" colspan="3">Before revenue falls: <b>'
          + (r.tolerable_loss_revenue_pct === null ? '-' : h.pct(r.tolerable_loss_revenue_pct))
          + '</b> &middot; before gross profit falls: <b>'
          + (r.tolerable_loss_gp_pct === null ? '-' : h.pct(r.tolerable_loss_gp_pct))
          + '</b> &middot; binding limit <b>'
          + (r.tolerable_volume_loss_pct === null ? '-' : h.pct(r.tolerable_volume_loss_pct)) + '</b>'
          + '<br><span class="small">This is the loss that would be tolerable at the stated price. It is not '
          + 'a forecast and not an expected loss.</span></td></tr>' : '')
      + '</tbody></table></div>'
      + '<p class="small ruleline">Where the evidence cannot predict volume, this states the quantity required '
      + 'and the test instead. It is not a recommended price. A movement must come from a stated commitment or a '
      + 'labelled assumption.</p>'
      + (ctxConditional(ctx, r))
      + '</div>';
  }

  function ctxConditional(ctx, r) {
    if (!ctx.engine.conditionalTest) return '';
    return (ctx.engine.conditionalTest(r) || [])
      .map(function (t) { return '<p class="small"><b>The test:</b> ' + esc(t) + '</p>'; }).join('');
  }

  function viewObjectives(ctx, c) {
    var h = ctx.h;
    var objective = ctx.scenario.get(c.id).objective || 'revenue';
    var twin = ctx.scenario.bothObjectives(c);
    var best = twin[objective].rows.length ? twin[objective].rows[0] : null;
    var anyTradeOff = twin[objective].rows.some(function (row) {
      return row.result.ok && row.result.flags.some(function (f) {
        return f.code === 'REV_UP_GP_DOWN' || f.code === 'GP_UP_REV_DOWN';
      });
    });

    return '<div class="inputsnote"><b>Two objectives, one engine, one scenario record.</b> Revenue growth is '
      + 'the default view. Changing the objective re-orders the alternatives; it does not change the baseline, '
      + 'the eligible quantity, the offer effective date or the volume assumption. Every row shows both '
      + 'revenue and gross profit, so the same scenario can be seen under both.</div>'
      + '<div class="compare-row"><div><span class="eyebrow">Ranking objective</span>'
      + '<div class="small">' + esc(twin[objective].objective_label) + ' &middot; compared with the unchanged '
      + 'offer over ' + esc(twin[objective].baseline.period) + '</div></div>'
      + '<select id="objective" aria-label="Ranking objective">'
      + '<option value="revenue"' + (objective === 'revenue' ? ' selected' : '')
      + '>Revenue growth &mdash; additional ISZE revenue (default)</option>'
      + '<option value="grossProfit"' + (objective === 'grossProfit' ? ' selected' : '')
      + '>Gross-profit growth &mdash; additional gross profit in EUR</option>'
      + '</select></div>'
      + '<div class="panel ' + (twin.assumptions.ordering_only ? 'good' : 'warn') + '">'
      + '<span class="badge ' + (twin.assumptions.ordering_only ? 'hold' : 'review') + '">'
      + (twin.assumptions.ordering_only ? 'Ordering only' : 'Assumptions differ') + '</span>'
      + '<p style="margin-top:12px">' + esc(twin.assumptions.statement) + '</p>'
      + '<p class="small">' + (twin.orders_differ
        ? 'The two objectives put the alternatives in a different order for this case.'
        : 'Both objectives put the alternatives in the same order for this case; the two measures still differ per row.')
      + '</p></div>'
      + (anyTradeOff ? '<div class="panel warn"><span class="badge review">Trade-off present</span>'
          + '<p style="margin-top:12px">At least one alternative moves revenue and gross profit in opposite '
          + 'directions. A revenue increase with a gross-profit reduction, or the reverse, is flagged and is '
          + 'not automatically approved.</p></div>' : '')
      + '<div class="grid3">'
      + '<div class="panel"><span class="eyebrow">Baseline</span><h3>Unchanged offer</h3>'
      + '<div class="evidence-line"><span>Applicable net price</span><b>'
      + h.eur(twin.revenue.baseline.price, 2) + '</b></div>'
      + '<div class="evidence-line"><span>Eligible quantity</span><b>'
      + h.num(twin.revenue.baseline.quantity, 0) + '</b></div>'
      + '<div class="evidence-line"><span>Revenue</span><b>' + h.eur(twin.revenue.baseline.revenue) + '</b></div>'
      + '<div class="evidence-line"><span>Gross profit</span><b>'
      + (twin.revenue.baseline_consistency.consistent ? 'One cost basis across the ranked rows'
        : twin.revenue.baseline_consistency.distinct_gross_profit_baselines
          + ' distinct gross-profit baselines across the ranked rows')
      + '</b></div>'
      + '<p class="small">' + esc(twin.revenue.baseline.basis_statement) + '</p>'
      + (twin.revenue.baseline_consistency.consistent ? '' :
          '<p class="small">The alternatives do not all declare the same cost basis. The spread is reported '
          + 'rather than hidden behind one advertised baseline.</p>')
      + '</div>'
      + topOptionPanel('Objective 1', 'Revenue-growth option', twin.revenue, objective === 'revenue', h,
          'revenue_change', 'gp_change')
      + topOptionPanel('Objective 2', 'Gross-profit-growth option', twin.grossProfit, objective === 'grossProfit',
          h, 'gp_change', 'revenue_change')
      + '</div>'
      + '<div class="panel"><h3>Ranked under ' + esc(twin[objective].objective_label) + '</h3>'
      + '<p class="small"><b>Showing order:</b> ' + esc(objective === 'grossProfit'
          ? 'gross-profit growth (objective 2)' : 'revenue growth (objective 1 default)')
      + '. Same customer, same period, same eligible quantity and same product population for '
      + 'every row. The ranked option can be written into the one scenario record and is then the option the '
      + 'price test and the export carry.</p>'
      + objectiveRows(twin, objective, h, ctx.scenario, c.id)
      + '<p class="small ruleline">This ranks by the selected objective and does not use an invented composite '
      + 'score. A mathematically profitable scenario is not an approved offer and is not a forecast.</p></div>'
      + (best ? '<div class="panel"><h3>Worked detail: ' + esc(best.alternative.name) + '</h3>'
          + stateTable(best.result, c, h) + '</div>' + breakEvenTable(best.result, ctx, h) : '')
      + notSaidPanel(c, ctx);
  }

  function topOptionPanel(eyebrow, title, side, isActive, h, primaryKey, secondaryKey) {
    var top = side.rows.length ? side.rows[0] : null;
    if (!top || !top.result.ok || top.result[primaryKey] === null) {
      return '<div class="panel' + (isActive ? ' callout' : '') + '"><span class="eyebrow">' + esc(eyebrow)
        + (isActive ? ' &middot; selected' : '') + '</span><h3>' + esc(title) + '</h3>'
        + unavailableBlock(failure.unavailable({
          title: 'Not available for this case',
          reason: 'No recorded alternative produces a ' + (primaryKey === 'gp_change' ? 'gross-profit' : 'revenue')
            + ' change here, so none is ranked. Nothing is substituted for it.',
          required: primaryKey === 'gp_change'
            ? 'a verified parts purchase cost for this exact part, so gross profit can be calculated'
            : 'a stated alternative with a recorded price movement',
          scope: 'case alternatives'
        })) + '</div>';
    }
    return '<div class="panel' + (isActive ? ' callout' : '') + '"><span class="eyebrow">' + esc(eyebrow)
      + (isActive ? ' &middot; selected' : '') + '</span><h3>' + esc(title) + '</h3>'
      + '<div class="resultbig ' + h.color(top.result[primaryKey]) + '">'
      + h.signedEur(top.result[primaryKey]) + '</div>'
      + '<div class="small">' + esc(top.alternative.name) + '</div>'
      + '<div class="evidence-line"><span>Other objective</span><b class="'
      + (top.result[secondaryKey] === null ? '' : h.color(top.result[secondaryKey])) + '">'
      + (top.result[secondaryKey] === null ? 'Cost required' : h.signedEur(top.result[secondaryKey]))
      + '</b></div>'
      + '<div class="evidence-line"><span>Gross margin after</span><b>'
      + (top.result.margin_after_pct === null ? 'Cost required' : h.num(top.result.margin_after_pct, 1) + '%')
      + '</b></div></div>';
  }

  /* --------------------------------------------------------- view: economics -- */

  function economicResults(ctx, c) {
    var h = ctx.h;
    var r = ctx.scenario.calculate(c.id);
    var s = ctx.scenario.get(c.id);
    var cons = ctx.scenario.consistency(c.id);
    if (!r.ok) {
      return '<div class="panel warn"><h3>This scenario is not a valid calculation</h3>'
        + (r.errors || [r.error]).map(function (e) { return '<p class="small error-msg">' + esc(e) + '</p>'; }).join('')
        + '<p class="small">The scenario is not silently corrected. Adjust the input or leave it blank.</p></div>';
    }
    var gp = r.gp_change === null;
    return '<div class="grid2">'
      + '<div class="panel"><div class="result-label">Revenue change in this scenario</div>'
      + '<div class="resultbig ' + h.color(r.revenue_change) + '">' + h.signedEur(r.revenue_change) + '</div>'
      + '<div class="small">' + h.num(r.quantity_after, 1) + ' ' + esc(c.unit) + 's &middot; '
      + h.eur(r.price_after, 2) + ' proposed net price<br>Against ' + h.eur(r.revenue_before)
      + ' at the recorded baseline price.</div></div>'
      + '<div class="panel ' + (gp ? 'warn' : r.gp_change < 0 ? 'warn' : 'good') + '">'
      + '<div class="result-label">Gross-profit change in this scenario</div>'
      + '<div class="resultbig ' + (gp ? '' : h.color(r.gp_change)) + '">'
      + (gp ? 'Not calculated' : h.signedEur(r.gp_change)) + '</div>'
      + '<div class="small">' + (gp
        ? esc(ctx.vmodel.cost_rule.accounting_cost_statement)
        : 'After ' + h.eur(r.support_eur) + ' of one-off support, counted once. The cost applied is the '
          + 'parts purchase cost per the declared measure' + (r.cost_basis_id ? ' (basis ' + esc(r.cost_basis_id) + ')' : ''))
      + '</div></div></div>'
      + '<div class="panel ' + (cons.ok ? 'good' : 'warn') + '"><div class="eyebrow">One scenario record</div>'
      + '<h3>' + (cons.ok ? 'The ranked option and the working record agree' : 'The ranked option and the working '
        + 'record disagree') + '</h3>'
      + '<p class="small">' + esc(cons.statement) + '</p>'
      + '<div class="evidence-line"><span>Selected alternative</span><b>'
      + esc(s.selected_alternative_id || 'none') + '</b></div>'
      + '<div class="evidence-line"><span>Scenario record</span><b class="small">'
      + esc(s.scenario_id) + ' &middot; version ' + s.version + '</b></div>'
      + '<div class="evidence-line"><span>Offer effective date</span><b>'
      + (s.offer_effective_date ? esc(s.offer_effective_date)
        : '<span class="danger-line">Not set</span>') + '</b></div>'
      + '<div class="evidence-line"><span>Objective on the record</span><b>' + esc(s.objective) + '</b></div>'
      + '</div>'
      + (gp ? unavailableBlock(failure.unavailable({
          title: 'Gross profit and gross margin are not calculated',
          reason: 'No parts purchase cost is held or entered for this exact part, so gross profit cannot be '
            + 'stated. Revenue and the revenue break-even still are. The figures are not estimated and no '
            + 'cost is defaulted.',
          required: 'the parts purchase cost for ' + c.pn + ' per the declared supplier purchase-cost '
            + 'calculation, or a manually entered cost labelled as an assumption',
          scope: 'this scenario'
        })) : stateTable(r, c, h))
      + breakEvenTable(r, ctx, h)
      + notSaidPanel(c, ctx);
  }

  function viewEconomics(ctx, c) {
    var h = ctx.h;
    var s = ctx.scenario.get(c.id);
    var e = c.packEvidence;
    var costRule = ctx.vmodel.cost_rule;
    var turbo = c.id === 'ITUK-TURBO' ? ctx.vmodel.turbo : null;
    var bases = (ctx.payload.meta.costBases || []);
    var basisOptions = bases.map(function (b) {
      var w = ctx.engine.basisWindow(b);
      return '<option value="' + esc(b.basis_id) + '"' + (s.cost_basis_id === b.basis_id ? ' selected' : '')
        + '>' + esc(b.name) + ' (' + esc(b.basis_id) + ', ' + esc(w.from || '?') + ' to '
        + esc(w.to || 'no declared end') + ')</option>';
    }).join('');

    return '<div class="inputsnote"><b>Scenario only; no automatic price move.</b> A manual price or cost does '
      + 'not approve a customer quotation, a cost basis or a margin floor. Every figure below comes from the '
      + 'pricing engine; this screen only collects the inputs.</div>'
      + (turbo ? '<div class="panel callout"><h3>The turbo list price is already resolved</h3>'
          + '<p class="small">' + esc(turbo.statement) + ' ' + esc(turbo.open_statement || '') + '</p></div>' : '')
      + '<div class="split"><div class="panel scenario-controls"><h3>Define the offer being tested</h3>'
      + '<div class="field"><label for="baseP">Scenario base price, EUR / ' + esc(c.unit) + '</label>'
      + '<input id="baseP" type="number" min=".01" step=".01" value="' + s.price_before + '">'
      + '<small>Changing this price changes the scenario base, not historical recorded billing.</small></div>'
      + '<div class="field"><label for="newP">Proposed ISZE net price, EUR / ' + esc(c.unit) + '</label>'
      + '<input id="newP" type="number" step=".01" min=".01" value="' + s.price_after + '">'
      + '<small>Starts unchanged. A recorded list value used here is a sensitivity, not an approved net offer.</small></div>'
      + '<div class="field"><label for="scope">Which volume receives the new price?</label>'
      + '<select id="scope"><option value="all"' + (s.scope === 'all' ? ' selected' : '')
      + '>All eligible volume</option><option value="incremental"' + (s.scope === 'incremental' ? ' selected' : '')
      + '>Incremental units only</option></select>'
      + '<small>Incremental-only keeps the existing units at their current price.</small></div>'
      + '<div class="field"><label for="baseQ">Eligible historical base quantity</label>'
      + '<input id="baseQ" type="number" min="1" step="1" value="' + s.quantity_before + '">'
      + '<small>Loaded: ' + h.num(c.half['2026'].quantity) + ' ' + esc(c.unit)
      + 's, January-June 2026. No annualisation.</small></div>'
      + '<div class="field"><label for="offerDate">Offer effective date</label>'
      + '<input id="offerDate" type="date" value="' + esc(s.offer_effective_date || '') + '">'
      + '<small>Required. The date selects which supplier-cost basis applies. September and October are held '
      + 'separately and are never blended or defaulted.</small></div>'
      + '<div class="field"><label for="quantityAfter">Proposed quantity, if it differs</label>'
      + '<input id="quantityAfter" type="number" min="1" step="1" value="'
      + (s.quantity_after === null ? '' : s.quantity_after) + '" placeholder="Blank means the base quantity">'
      + '<small>Leave blank to use the base quantity. A blank is not a zero.</small></div>'
      + '<div class="field"><label for="support">One-off support cost, EUR</label>'
      + '<input id="support" type="number" min="0" step="1" value="' + s.support_eur + '">'
      + '<small>Zero is a scenario assumption, not proof that no support exists.</small></div>'
      + '<div class="field"><label for="costBasisId">Supplier-cost basis</label>'
      + '<select id="costBasisId">' + basisOptions + '</select>'
      + '<small>' + esc(costRule.accounting_cost_statement) + '</small></div>'
      + '<div class="field"><label for="cost">Unit parts purchase cost, EUR &mdash; manual entry</label>'
      + '<input id="cost" type="number" min="0" step=".01" placeholder="No verified cost held for this part" value="'
      + (s.cost_eur === null ? '' : s.cost_eur) + '">'
      + '<small>' + (e.costRecordPresent
        ? 'A supplier purchase-cost record is held for this exact part. Selecting a basis above loads it. '
          + 'A value typed here is an assumption.'
        : 'No cost record is held for this exact part, so gross profit is not calculated until one is entered. '
          + 'Entering a value here is an assumption, not verification.') + '</small></div>'
      + '<div class="rowactions"><button class="button" id="reset-scenario">Reset to the unchanged offer</button>'
      + '<button class="button primary" data-view="action">Carry this scenario into a review</button></div></div>'
      + '<div id="economic-results">' + economicResults(ctx, c) + '</div></div>';
  }

  /* -------------------------------------------------------- view: candidates -- */

  function viewCandidates(ctx, c) {
    var h = ctx.h;
    var wb = ctx.candidates;
    var v = wb.view();
    var cov = v.coverage;
    var approval = v.approval;
    var priority = v.priority;
    var entities = v.entities;
    var readiness = v.readiness;
    var sortArrow = function (key) {
      if (v.sort.key !== key) return '';
      return v.sort.direction === 'desc' ? ' &darr;' : ' &uarr;';
    };
    var sortButton = function (key, label) {
      return '<button class="linkbutton sort-button" data-sort="' + esc(key) + '">' + esc(label) + sortArrow(key)
        + '</button>';
    };

    return '<div class="inputsnote"><b>Candidate workbench.</b> This screen searches and pages the whole '
      + 'permitted set, not a first slice of it. The costing, filtering, counting and paging come from the '
      + 'shared candidate module, so the counts on screen and the counts in the tests cannot drift apart.</div>'
      + '<div class="stats">'
      + '<div class="stat"><div class="label">Screened rows in total</div><strong>'
      + h.num(cov.rows_total, 0) + '</strong><div class="detail">'
      + h.num(cov.unique_parts, 0) + ' distinct part numbers &middot; a row is not a part</div></div>'
      + '<div class="stat"><div class="label">Rows matching this search</div><strong>'
      + h.num(cov.rows_matching, 0) + '</strong><div class="detail">'
      + h.num(v.page.page_count, 0) + ' page(s) at ' + h.num(v.page.page_size, 0) + ' rows</div></div>'
      + '<div class="stat"><div class="label">Rows with a price and a cost record</div><strong>'
      + h.num(cov.rows_with_cost_and_list, 0) + '</strong><div class="detail">'
      + h.num(cov.unique_parts_with_cost_and_list, 0)
      + ' distinct part numbers &middot; coverage, not approval</div></div>'
      + '<div class="stat"><div class="label">Rows with competitor evidence</div><strong>'
      + h.num(cov.rows_with_competitor_evidence, 0) + '</strong><div class="detail">'
      + h.num(cov.unique_parts_with_competitor_evidence, 0)
      + ' distinct part numbers &middot; the rest state it was not located</div></div>'
      + '</div>'
      + '<div class="panel warn"><h3>Read the coverage before the ranking</h3>'
      + '<p class="small">' + esc(cov.cost_and_list_coverage) + '</p>'
      + '<p class="small">' + esc(cov.rows_vs_parts) + '</p>'
      + '<p class="small">' + esc(cov.not_approval) + '</p>'
      + '<p class="small">' + esc(approval.statement) + '</p>'
      + '<p class="small">' + esc(cov.cost_column_statement) + '</p>'
      + '<p class="small">' + esc(readiness.statement) + '</p></div>'
      + '<div class="grid2">'
      + '<div class="panel"><div class="eyebrow">Commercial priority</div>'
      + '<h3>' + h.eur(priority.total_observed_billing_eur)
      + ' of observed billing across the matching rows</h3>'
      + '<p class="small">' + esc(priority.statement) + '</p>'
      + '<p class="small">This says how much money is at stake. It is a separate axis from how much evidence '
      + 'is held, and it is not a recommendation.</p></div>'
      + '<div class="panel"><div class="eyebrow">Who is in this set</div>'
      + '<h3>' + h.num(entities.distributors.length, 0) + ' distributor(s)</h3>'
      + '<p class="small">' + esc(entities.statement) + '</p>'
      + (entities.separate_entity_pairs_present.length
        ? entities.separate_entity_pairs_present.map(function (p) {
            return '<p class="small"><b>Kept as two rows:</b> ' + esc(p.statement) + '</p>';
          }).join('')
        : '<p class="small">No pair in this set is recorded as two separate entities.</p>')
      + '</div></div>'
      + '<div class="panel ' + (v.basis.declared || v.basis.period_state !== 'undeclared' ? 'good' : 'warn')
      + '"><h3>Reporting basis of the candidate rows</h3>'
      + '<p class="small">' + esc(v.basis.statement) + '</p>'
      + (v.basis.screen_period_note ? '<p class="small">' + esc(v.basis.screen_period_note) + '</p>' : '')
      + '<p class="small">The screened rows keep their own completeness statement, separate from the worked '
      + 'cases, which use their own explicitly stated periods.</p></div>'
      + '<div class="panel"><h3>Search the whole permitted set</h3>'
      + '<div class="search-row">'
      + '<div class="field"><label for="candidate-search">Search part number, description, account or reason</label>'
      + '<input id="candidate-search" type="search" value="' + esc(v.state.query) + '" '
      + 'placeholder="e.g. a part number, a family word, an account"><small>Every term must match. The search '
      + 'runs over all ' + h.num(cov.rows_total, 0) + ' rows, not the page you are looking at.</small></div>'
      + '<div class="field"><label for="candidate-account">Account</label>'
      + '<select id="candidate-account"><option value="">Both accounts</option>'
      + (entities.distributors.length
        ? entities.distributors.map(function (d) {
            return '<option value="' + esc(d) + '"' + (v.state.criteria.distributor === d ? ' selected' : '')
              + '>' + esc(d) + '</option>';
          }).join('')
        : '<option value="ITUK"' + (v.state.criteria.distributor === 'ITUK' ? ' selected' : '')
          + '>ITUK &mdash; UK trucks</option><option value="PORTUGAL"'
          + (v.state.criteria.distributor === 'PORTUGAL' ? ' selected' : '')
          + '>I Motors &mdash; Portugal</option>')
      + '</select></div>'
      + '<div class="field"><label for="candidate-cost">Cost record</label>'
      + '<select id="candidate-cost"><option value="">Any</option>'
      + '<option value="with"' + (v.state.criteria.with_cost ? ' selected' : '')
      + '>Cost record held &mdash; coverage filter</option>'
      + '<option value="without"' + (v.state.criteria.without_cost ? ' selected' : '')
      + '>No cost record held &mdash; the gap, not a smaller file</option></select></div>'
      + '<div class="field"><label for="candidate-competitor">Competitor evidence</label>'
      + '<select id="candidate-competitor"><option value="">Any</option>'
      + '<option value="held"' + (v.state.criteria.with_competitor ? ' selected' : '')
      + '>Held</option></select></div>'
      + '<div class="field"><label for="candidate-pagesize">Rows per page</label>'
      + '<select id="candidate-pagesize">' + wb.page_size_choices.map(function (n) {
          return '<option value="' + n + '"' + (v.page.page_size === n ? ' selected' : '') + '>' + n + '</option>';
        }).join('') + '</select></div>'
      + '<div class="rowactions"><button class="button" data-clear-filters>Clear search and filters</button></div>'
      + '</div></div>'
      + (v.empty_state ? unavailableBlock(v.empty_state) : '')
      + '<div class="panel"><h3>Screened rows under the current search</h3>'
      + '<p class="small">' + esc(v.counts.statement) + '</p>'
      + '<div class="tablewrap"><table><thead><tr>'
      + '<th>' + sortButton('distributor', 'Customer') + '</th>'
      + '<th>' + sortButton('part_number', 'Part') + '</th><th>Description</th>'
      + '<th class="n">' + sortButton('billed_qty', 'Billed qty') + '</th>'
      + '<th class="n">' + sortButton('observed_billing_eur', 'Observed billing') + '</th>'
      + '<th class="n">' + sortButton('observed_unit_price', 'Observed unit price') + '</th>'
      + '<th class="n">' + sortButton('list_eur', 'List') + '</th>'
      + '<th class="n">' + sortButton('verified_cost_eur_oct26', 'Parts purchase cost') + '</th>'
      + '<th>Selection reason</th><th>Unresolved</th><th>Competitor</th><th>Review</th>'
      + '</tr></thead><tbody>'
      + v.page.rows.map(function (r) {
          var band = wb.priorityLabel(r);
          return '<tr><td>' + esc(r.distributor) + '<div class="small">'
            + (band.band ? esc(band.band) + ' priority' : 'no billing recorded') + '</div></td>'
            + '<td class="pn">' + esc(r.part_number) + '</td><td class="small">' + esc(r.description || '') + '</td>'
            + '<td class="n">' + h.num(r.billed_qty, 0) + '</td>'
            + '<td class="n">' + h.eur(r.observed_billing_eur) + '</td>'
            + '<td class="n">' + h.eurOr(r.observed_unit_price, 2, '-') + '</td>'
            + '<td class="n">' + h.eurOr(r.list_eur, 2, '-') + '</td>'
            + '<td class="n">' + (r.verified_cost_eur_oct26 === null
              ? '<span class="danger-line">not held</span>' : h.eur(r.verified_cost_eur_oct26, 2)) + '</td>'
            + '<td class="small">' + esc(r.selection_reasons) + '</td>'
            + '<td class="small">' + esc(r.unresolved_inputs || '') + '</td>'
            + '<td class="small">' + esc(r.competitor_evidence) + '</td>'
            + '<td><button class="linkbutton" data-open-part="' + esc(r.part_number) + '">Review '
            + esc(r.part_number) + '</button></td></tr>';
        }).join('')
      + '</tbody></table></div>'
      + '<div class="pagination">'
      + '<button class="button small" data-page="' + (v.page.page - 1) + '"'
      + (v.page.has_previous ? '' : ' disabled') + '>Previous</button>'
      /* A reversed range such as "Rows 1 to 0 of 0" reads as nonsense, so an
         empty result states that it is empty instead of printing one. */
      + (v.page.total === 0
        ? '<span class="small">No rows match the current search.</span>'
        : '<span class="small">Rows <b>' + h.num(v.reached.first, 0) + '</b> to <b>'
          + h.num(v.reached.last, 0) + '</b> of <b>' + h.num(v.reached.of, 0) + '</b> matching &middot; page <b>'
          + v.page.page + '</b> of <b>' + v.page.page_count + '</b> &middot; ' + v.reached.covered_pct
          + '% of the matching rows reached</span>')
      + '<button class="button small" data-page="' + (v.page.page + 1) + '"'
      + (v.page.has_next ? '' : ' disabled') + '>Next</button>'
      + '<button class="button small" data-last-page="1"' + (v.page.total === 0 ? ' disabled' : '')
      + '>Last page</button>'
      + '</div>'
      + '<p class="small ruleline">Observed unit price is recorded billing divided by recorded quantity. It is '
      + 'not a list price, and a movement in it is not automatically a price-list change. A row with a cost and '
      + 'a list is a candidate for review, not a cleared price decision.</p></div>'
      + '<div class="panel"><h3>The confirmed measure</h3>'
      + '<p class="small"><b>Revenue</b> = ' + esc((ctx.payload.meta.confirmedRules || {}).revenue || '')
      + '. <b>Gross profit</b> = ' + esc((ctx.payload.meta.confirmedRules || {}).grossProfit || '')
      + '. <b>Gross margin</b> = ' + esc((ctx.payload.meta.confirmedRules || {}).grossMargin || '') + '.</p>'
      + '<p class="small">' + esc(ctx.vmodel.cost_rule.accounting_cost_statement) + '</p>'
      + '<p class="small">Excluded from the measure: '
      + esc((ctx.vmodel.cost_rule.excluded_from_measure || []).join(', ')) + '. '
      + esc(ctx.vmodel.cost_rule.double_deduction || '') + '</p>'
      + '<p class="small">' + esc(ctx.vmodel.cost_rule.class_margin_warning || '') + '</p></div>';
  }

  /* ------------------------------------------------ view: selected part (F10) -- */

  /* The route from a candidate row to its own review. If the part is one of the
     worked cases, the reader is taken to that case. If it is not, a review is
     opened for that exact part and the screen says plainly that no case record
     exists yet and what would be needed to make one. */
  function viewCase(ctx, c) {
    var h = ctx.h;
    var route = ctx.state.part_route;
    if (!route) {
      return unavailableBlock(failure.unavailable({
        title: 'No part selected',
        reason: 'Open a row from the candidates view to review that exact part. Nothing is shown here '
          + 'because nothing was selected.',
        required: 'a part number selected from the candidate workbench',
        scope: 'selected part review'
      }));
    }
    var worked = (ctx.payload.cases || []).filter(function (x) { return x.pn === route.part_number; })[0];
    var rows = ctx.candidates.findPart(route.part_number);
    var live = ctx.candidates.routeForPart(route.part_number);
    var accounts = rows.reduce(function (m, r) { m[r.distributor] = (m[r.distributor] || 0) + 1; return m; }, {});
    var blockers = (live.ok && live.promotion_blockers) ? live.promotion_blockers : null;

    return '<div class="panel callout"><div class="eyebrow">Selected part review</div>'
      + '<h3>' + esc(route.part_number) + ' &mdash; ' + esc(rows.length ? rows[0].description : '') + '</h3>'
      + '<div class="evidence-line"><span>Exact original part reference</span><b class="pn">'
      + esc(route.part_number) + '</b></div>'
      + '<div class="evidence-line"><span>Screened rows covering it</span><b>' + h.num(rows.length, 0) + '</b></div>'
      + '<div class="evidence-line"><span>Accounts it was billed to</span><b>'
      + esc(Object.keys(accounts).map(function (k) { return k + ' (' + accounts[k] + ' row(s))'; }).join(', '))
      + '</b></div>'
      + '<div class="evidence-line"><span>Recorded billing across those rows</span><b>'
      + h.eur(live.ok ? live.observed_billing_eur : null) + '</b></div>'
      + (live.ok && live.rows_without_a_billing_value
        ? '<p class="small">' + live.rows_without_a_billing_value + ' of these rows carry no billing value. '
          + 'They are excluded from that total rather than counted as zero.</p>' : '')
      + '</div>'
      + (worked
        ? '<div class="panel good"><h3>This part is one of the worked cases</h3>'
          + '<p class="small">Open the case ' + esc(worked.id) + ' to test price and gross profit against its '
          + 'recorded evidence. The case carries the same exact part reference ' + esc(worked.pn) + '.</p>'
          + '<button class="button primary" data-open-case="' + esc(worked.id) + '">Open case '
          + esc(worked.id) + '</button></div>'
        : '<div class="panel warn"><h3>No case record exists for this exact part yet</h3>'
          + '<p class="small">A screened row is a candidate for review. It is not a case, and nothing on this '
          + 'screen creates one. The row carries recorded billing, a list value and, where held, a parts '
          + 'purchase cost.</p>'
          + (blockers && blockers.length
            ? '<div class="ruleline"><b>What would have to exist before this could become a case</b>'
              + blockers.map(function (b) {
                  var text = typeof b === 'string' ? b : (b.text || b.blocker || b.reason || '');
                  var item = typeof b === 'string' ? null : (b.field || b.item || null);
                  return '<div class="evidence-line"><span>' + esc(item || 'Required') + '</span><b class="small">'
                    + esc(text) + '</b></div>';
                }).join('') + '</div>'
            : '<p class="small">The row does not state the current customer net price, the applicable cost basis '
              + 'and effective date, or a stated alternative to test. None of those three are inferred from the '
              + 'screened row, because the row shows what was billed, not what was offered.</p>')
          + '</div>')
      + '<div class="panel"><h3>The screened rows for this exact part</h3>'
      + '<div class="tablewrap"><table><thead><tr><th>Account</th><th class="n">Billed qty</th>'
      + '<th class="n">Observed billing</th><th class="n">Observed unit price</th><th class="n">List</th>'
      + '<th class="n">Parts purchase cost</th><th>Selection reason</th><th>Unresolved</th></tr></thead><tbody>'
      + rows.slice(0, 50).map(function (r) {
          return '<tr><td>' + esc(r.distributor) + '</td><td class="n">' + h.num(r.billed_qty, 0) + '</td>'
            + '<td class="n">' + h.eur(r.observed_billing_eur) + '</td><td class="n">'
            + h.eurOr(r.observed_unit_price, 2, '-') + '</td><td class="n">' + h.eurOr(r.list_eur, 2, '-')
            + '</td><td class="n">' + (r.verified_cost_eur_oct26 === null
              ? '<span class="danger-line">not held</span>' : h.eur(r.verified_cost_eur_oct26, 2)) + '</td>'
            + '<td class="small">' + esc(r.selection_reasons) + '</td><td class="small">'
            + esc(r.unresolved_inputs || '') + '</td></tr>';
        }).join('') + '</tbody></table></div>'
      + (rows.length > 50 ? '<p class="small">Showing the first 50 rows for this part of ' + rows.length
        + ' held.</p>' : '')
      + '</div>'
      + '<div class="rowactions"><button class="button" data-view="candidates">Back to the candidate '
      + 'workbench</button></div>';
  }

  /* ------------------------------------------------------------ view: action -- */

  function viewAction(ctx, c) {
    var h = ctx.h;
    var s = ctx.scenario.get(c.id);
    var pkg = ctx.scenario.exportPackage(c.id);
    var saved = ctx.saved[c.id] || {};
    var blockers = (ctx.engine.assess ? ctx.engine.assess(c).blockers : []) || [];
    var cons = pkg.consistency;

    return '<div class="grid2"><div class="panel"><div class="eyebrow">Prospective internal record</div>'
      + '<h3>One decision, with its evidence already attached</h3><p>' + esc(c.next) + '</p>'
      + '<div class="field"><label for="owner">Review owner / role</label>'
      + '<input id="owner" value="' + esc(saved.owner || c.owner) + '">'
      + '<small>A suggested role is not a person\'s acceptance of ownership.</small></div>'
      + '<div class="formrow"><div class="field"><label for="reviewDate">Proposed review date</label>'
      + '<input id="reviewDate" type="date" value="' + esc(saved.reviewDate || '') + '"></div>'
      + '<div class="field"><label for="actionStatus">Internal status</label><select id="actionStatus">'
      + ['Draft review', 'Evidence requested', 'Ready for human review', 'No change recommended', 'Test proposed']
          .map(function (a) {
            return '<option' + (a === (saved.status || 'Draft review') ? ' selected' : '') + '>' + a + '</option>';
          }).join('') + '</select></div></div>'
      + '<div class="field"><label for="explanation">Customer / supply explanation (leave unknown if not received)</label>'
      + '<textarea id="explanation" placeholder="Unknown. Record who said what, when, and which parts it covers.">'
      + esc(saved.explanation || '') + '</textarea></div>'
      + '<div class="field"><label for="decisionNote">Proposed action and test conditions</label>'
      + '<textarea id="decisionNote">' + esc(saved.note || c.recommendation) + '</textarea></div>'
      + '<div class="rowactions"><button class="button primary" id="save-note">Save the case record</button>'
      + '<button class="button" id="export-json">Export this case JSON</button>'
      + '<button class="button danger" id="delete-note">Delete the saved record</button></div>'
      + '<div class="status-msg" id="save-status">' + (saved.savedAt
        ? 'Saved: ' + esc(saved.savedAt) : ctx.storageOK ? 'No record saved yet.'
        : 'Storage is unavailable; export before closing.') + '</div></div>'
      + '<div><div class="panel warn"><h3>Approval checks are still outstanding</h3>'
      + '<p class="small">The held records do not clear these approval checks. A saved record does not '
      + 'approve a price, apply a discount, or submit a case to another system.</p>'
      + '<div class="checks">' + blockers.map(function (b) {
          return '<div class="small">&square; ' + esc(b) + '</div>';
        }).join('') + '</div>'
      + '<div class="ruleline"><b>Required result of the test</b>'
      + '<p class="small">A comparable-price offer, a defined eligible volume and period, a cost-supported '
      + 'gross-profit case, a review point and a rollback rule. Business moved between Genuine and BVP is '
      + 'counted separately from sales won from competitors.</p></div></div>'
      + '<div class="panel ' + (cons.ok ? 'good' : 'warn') + '"><h3>Scenario travelling with this review</h3>'
      + '<div class="evidence-line"><span>Scenario record</span><b class="small">' + esc(pkg.scenario_id)
      + ' &middot; version ' + pkg.version + '</b></div>'
      + '<div class="evidence-line"><span>Selected alternative</span><b>'
      + esc(pkg.selected_alternative_id || 'none') + '</b></div>'
      + '<div class="evidence-line"><span>Proposed net price</span><b>' + h.eur(s.price_after, 2) + '</b></div>'
      + '<div class="evidence-line"><span>Assumed quantity</span><b>'
      + h.num(pkg.result.ok ? pkg.result.quantity_after : null, 1) + '</b></div>'
      + '<div class="evidence-line"><span>Revenue change</span><b class="'
      + (pkg.result.ok ? h.color(pkg.result.revenue_change) : '') + '">'
      + (pkg.result.ok ? h.signedEur(pkg.result.revenue_change) : 'Not calculated') + '</b></div>'
      + '<div class="evidence-line"><span>Gross-profit change</span><b>'
      + (!pkg.result.ok ? 'Not calculated'
        : pkg.result.gp_change === null ? 'Not calculated &mdash; no cost held' : h.signedEur(pkg.result.gp_change))
      + '</b></div>'
      + '<div class="evidence-line"><span>Objective on the record</span><b>' + esc(pkg.objective) + '</b></div>'
      + '<p class="small">' + esc(cons.statement) + '</p>'
      + '<p class="small">The export carries this one record: the scenario, the result, the selected option, '
      + 'the change journal and both objective orders. It does not carry a second, older scenario.</p></div>'
      + '<div class="panel"><h3>Scope-safe export</h3>'
      + '<p class="small">The export contains this case, its scenario record and this case\'s note only. It '
      + 'does not export another customer\'s cases or notes.</p>'
      + '<button class="button" id="export-review-body">Export a readable case review</button></div>'
      + '</div></div>';
  }

  /* ------------------------------------------------------------------ exports -- */

  function render(viewId, ctx, c) {
    var body;
    switch (viewId) {
      case 'decision': body = viewDecision(ctx, c); break;
      case 'position': body = viewPosition(ctx, c); break;
      case 'objectives': body = viewObjectives(ctx, c); break;
      case 'economics': body = viewEconomics(ctx, c); break;
      case 'candidates': body = viewCandidates(ctx, c); break;
      case 'case': body = viewCase(ctx, c); break;
      case 'action': body = viewAction(ctx, c); break;
      default:
        throw new Error('Unknown view "' + viewId + '". The shell declares which views exist.');
    }
    /* REVIEW-04: the exact original part reference stays visible on every view. */
    return partStrip(c, ctx) + body;
  }

  var VIEW_ORDER = ['decision', 'position', 'objectives', 'economics', 'candidates', 'action'];

  return {
    render: render,
    economicsResults: economicResults,
    VIEW_ORDER: VIEW_ORDER,
    helpers: helpers,
    esc: esc,
    bannedWords: bannedWords,
    partStrip: partStrip,
    unavailableBlock: unavailableBlock,
    statusGrid: statusGrid,
    notSaidPanel: notSaidPanel,
    BANNED: BANNED
  };
});
