/* ===========================================================================
   CONNECT-03 - Add read-only PRISM context at its actual market level.

   Consumes accepted PRISM-shaped fixtures (synthetic in tests). Shows historical
   trucks in service, measured spend and modelled target context with source,
   period and population. Intentionally different denominator versions stay
   separate. A national total is never allocated to dealers, and a dealer review
   cannot acquire a per-truck performance rate from a national total. The fleet
   forecast beyond 2025 is excluded.

   Synthetic PRISM-shaped fixtures only. No real PRISM outputs.
   =========================================================================== */
(function (root) {
  'use strict';

  var FORECAST_CUTOFF_YEAR = 2025;

  function clone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }

  function yearOf(measure) {
    if (!measure) return null;
    if (measure.year != null) return Number(measure.year);
    if (measure.period) {
      var m = String(measure.period).match(/(20\d{2})/);
      if (m) return Number(m[1]);
    }
    return null;
  }

  function isFleetForecastBeyond2025(measure) {
    if (!measure) return false;
    var kind = String(measure.kind || measure.measure_kind || '').toLowerCase();
    var isFleet = kind.indexOf('fleet') >= 0 || kind.indexOf('uio') >= 0
      || kind.indexOf('trucks_in_service') >= 0;
    var isForecast = measure.forecast === true
      || String(measure.basis || '').toLowerCase().indexOf('forecast') >= 0
      || kind.indexOf('forecast') >= 0;
    if (!(isFleet && isForecast)) return false;
    var y = yearOf(measure);
    return y != null && y > FORECAST_CUTOFF_YEAR;
  }

  /* Drop unusable fleet forecast beyond 2025. Keep every historical measure
     with its own source, period, population and accepted basis. */
  function filterMeasures(measures) {
    var kept = [];
    var excluded = [];
    (measures || []).forEach(function (m) {
      if (isFleetForecastBeyond2025(m)) {
        excluded.push({
          id: m.id || null,
          reason: 'Fleet forecast beyond 2025 is excluded',
          period: m.period || null,
          year: yearOf(m)
        });
        return;
      }
      kept.push(clone(m));
    });
    return {
      kept: kept,
      excluded: excluded,
      statement: excluded.length
        ? ('Excluded ' + excluded.length + ' fleet forecast measure(s) beyond 2025.')
        : 'No fleet forecast beyond 2025 present.'
    };
  }

  function denominatorKey(measure) {
    return [
      measure.denominator_version || measure.denominator || 'unspecified',
      measure.population || 'unspecified',
      measure.accepted_basis || measure.basis || 'unspecified'
    ].join('|');
  }

  /* Keep different denominator versions as separate rows; never merge them. */
  function separateDenominatorVersions(measures) {
    var groups = {};
    (measures || []).forEach(function (m) {
      var k = denominatorKey(m);
      if (!groups[k]) groups[k] = [];
      groups[k].push(clone(m));
    });
    return {
      versions: Object.keys(groups).map(function (k) {
        return { key: k, measures: groups[k] };
      }),
      statement: 'Different denominator versions stay separate; they are not averaged.'
    };
  }

  /* A dealer review must not acquire a per-truck rate from a national total. */
  function attachPrismContext(dealerReview, prismMeasures, options) {
    options = options || {};
    dealerReview = dealerReview || {};
    var filtered = filterMeasures(prismMeasures);
    var versions = separateDenominatorVersions(filtered.kept);

    var national = filtered.kept.filter(function (m) {
      return String(m.population || m.level || '').toLowerCase() === 'national'
        || String(m.scope || '').toLowerCase() === 'national';
    });
    var dealerLevel = filtered.kept.filter(function (m) {
      return String(m.population || m.level || m.scope || '').toLowerCase() === 'dealer';
    });

    var perTruck = null;
    var refused = null;
    if (options.request_per_truck_from_national === true || options.allocate_national_to_dealer === true) {
      refused = {
        ok: false,
        per_truck_rate: null,
        statement: 'A dealer review cannot acquire a per-truck performance rate from a national total. The national fleet is not allocated to dealers.'
      };
    } else if (dealerLevel.length && dealerLevel.some(function (m) {
      return m.per_truck_rate != null || m.spend_per_truck != null;
    })) {
      var hit = dealerLevel.filter(function (m) {
        return m.per_truck_rate != null || m.spend_per_truck != null;
      })[0];
      perTruck = {
        ok: true,
        per_truck_rate: hit.per_truck_rate != null ? hit.per_truck_rate : hit.spend_per_truck,
        source: hit.source,
        period: hit.period,
        population: hit.population || hit.level || 'dealer',
        accepted_basis: hit.accepted_basis || hit.basis,
        statement: 'Per-truck rate taken from a dealer-level accepted measure only.'
      };
    } else {
      perTruck = {
        ok: false,
        per_truck_rate: null,
        statement: 'No dealer-level per-truck measure is available. A national total is not divided.'
      };
    }

    return {
      ok: refused ? false : true,
      dealer_id: dealerReview.dealer_id || null,
      distributor: dealerReview.distributor || null,
      measures: filtered.kept.map(function (m) {
        return {
          id: m.id || null,
          kind: m.kind || m.measure_kind || null,
          value: m.value != null ? m.value : null,
          unit: m.unit || null,
          source: m.source || null,
          period: m.period || null,
          population: m.population || m.level || m.scope || null,
          accepted_basis: m.accepted_basis || m.basis || null,
          denominator_version: m.denominator_version || m.denominator || null
        };
      }),
      excluded_forecasts: filtered.excluded,
      denominator_versions: versions.versions,
      national_totals: national.map(function (m) {
        return { id: m.id, value: m.value, unit: m.unit, period: m.period, source: m.source };
      }),
      per_truck: refused || perTruck,
      statement: refused
        ? refused.statement
        : 'Read-only PRISM context at the level each measure was actually measured.'
    };
  }

  /* Same five characters as esc in src/ui/app.js, the single quote included. */
  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function renderContextPanel(view) {
    view = view || {};
    var rows = (view.measures || []).map(function (m) {
      return '<tr>'
        + '<td>' + escapeHtml(m.kind) + '</td>'
        + '<td>' + escapeHtml(m.value) + ' ' + escapeHtml(m.unit) + '</td>'
        + '<td>' + escapeHtml(m.population) + '</td>'
        + '<td>' + escapeHtml(m.period) + '</td>'
        + '<td>' + escapeHtml(m.source) + '</td>'
        + '<td>' + escapeHtml(m.accepted_basis) + '</td>'
        + '</tr>';
    }).join('');
    var per = view.per_truck || {};
    var perLine = per.per_truck_rate != null
      ? ('Per-truck rate: ' + per.per_truck_rate + ' (' + (per.population || '') + ')')
      : (per.statement || 'No per-truck rate from a national total.');
    return '<section class="prism-context" data-connect-03="panel">'
      + '<h2>PRISM context (read-only, measured level)</h2>'
      + '<p class="dealer">Dealer: ' + escapeHtml(view.dealer_id) + ' / '
      + escapeHtml(view.distributor) + '</p>'
      + '<p class="per-truck" data-has-rate="' + (per.per_truck_rate != null ? 'yes' : 'no') + '">'
      + escapeHtml(perLine) + '</p>'
      + '<table><thead><tr><th>Kind</th><th>Value</th><th>Population</th>'
      + '<th>Period</th><th>Source</th><th>Accepted basis</th></tr></thead>'
      + '<tbody>' + rows + '</tbody></table>'
      + '</section>';
  }

  var API = {
    escapeHtml: escapeHtml,
    FORECAST_CUTOFF_YEAR: FORECAST_CUTOFF_YEAR,
    filterMeasures: filterMeasures,
    separateDenominatorVersions: separateDenominatorVersions,
    attachPrismContext: attachPrismContext,
    isFleetForecastBeyond2025: isFleetForecastBeyond2025,
    renderContextPanel: renderContextPanel
  };

  root.AIMPrismContext = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
