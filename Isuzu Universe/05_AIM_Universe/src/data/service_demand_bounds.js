/* ===========================================================================
   CONNECT-04 - Enforce service-demand and shared-applicability boundaries.

   Reuses accepted service-demand results with separate external/internal
   methods. Switching basis changes the labelled method; the two are never
   averaged. Shared parts stay pooled. Repeated market actuals are not summed
   by band to invent a band-level service cover. Restricted euro aggregates stay
   out of external views. Series codes become bands only through AIMVehicleBands
   (series_to_band.csv), never through a second dictionary.

   Synthetic fixtures only.
   =========================================================================== */
(function (root) {
  'use strict';

  function bandsApi() {
    if (root && root.AIMVehicleBands) return root.AIMVehicleBands;
    if (typeof module === 'object' && typeof require === 'function') {
      try { return require('./vehicle_bands.js'); } catch (e) { return null; }
    }
    return null;
  }

  function clone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }

  var METHOD_INTERNAL = 'internal_service_basis';
  var METHOD_EXTERNAL = 'external_service_basis';

  /* Switching basis changes the labelled method. Never average the two. */
  function selectServiceBasis(results, basis) {
    results = results || {};
    var label = basis === 'external' ? METHOD_EXTERNAL
      : basis === 'internal' ? METHOD_INTERNAL
      : null;
    if (!label) {
      return { ok: false, error: 'basis must be internal or external', method_label: null };
    }
    var internal = results.internal || null;
    var external = results.external || null;
    var chosen = basis === 'external' ? external : internal;
    if (chosen == null) {
      return {
        ok: false,
        error: 'No accepted result for the ' + basis + ' service basis.',
        method_label: label,
        value: null,
        averaged: false
      };
    }
    return {
      ok: true,
      method_label: label,
      basis: basis,
      value: clone(chosen),
      averaged: false,
      statement: 'Using the ' + label + ' only. Internal and external bases are not averaged.'
    };
  }

  /* Refuse band-level service cover made by dividing repeated market purchasing
     by a band expectation. */
  function bandServiceCover(input) {
    input = input || {};
    if (input.derive_by_dividing_repeated_market_by_band_expectation === true
        || input.method === 'repeated_market_over_band_expectation') {
      return {
        ok: false,
        cover: null,
        refused: true,
        statement: 'No band-level service cover is derived by dividing repeated market purchasing by a band expectation.'
      };
    }
    if (input.exclusive_purchasing != null && input.modelled_demand != null
        && input.applicability === 'exclusive') {
      return {
        ok: true,
        cover: {
          purchasing: input.exclusive_purchasing,
          modelled_demand: input.modelled_demand,
          applicability: 'exclusive',
          method_label: input.method_label || null
        },
        refused: false,
        statement: 'Exclusive-applicability purchasing kept beside modelled demand; market actuals stay separate.'
      };
    }
    return {
      ok: false,
      cover: null,
      refused: true,
      statement: 'Band service cover needs an accepted exclusive-applicability method, not a market/band division.'
    };
  }

  /* Shared parts stay pooled (one bucket), not split into exclusive classes. */
  function poolSharedParts(parts) {
    var shared = [];
    var exclusive = [];
    (parts || []).forEach(function (p) {
      if (!p) return;
      if (p.shared === true || p.applicability === 'shared') shared.push(clone(p));
      else exclusive.push(clone(p));
    });
    var pooledQty = 0;
    var pooledEur = 0;
    shared.forEach(function (p) {
      if (p.qty != null) pooledQty += Number(p.qty) || 0;
      if (p.eur != null) pooledEur += Number(p.eur) || 0;
    });
    return {
      shared_pool: {
        parts: shared,
        qty: pooledQty,
        eur: pooledEur,
        pooled: true
      },
      exclusive: exclusive,
      statement: 'Shared parts stay pooled; they are not split across exclusive classes.'
    };
  }

  /* Restricted euro aggregates stay out of external views. */
  function externalView(aggregates, options) {
    options = options || {};
    var restrictedKeys = options.restricted_keys || [
      'cost_eur', 'gp_eur', 'margin_pct', 'restricted_euro', 'internal_cost'
    ];
    var out = {};
    var stripped = [];
    Object.keys(aggregates || {}).forEach(function (k) {
      if (restrictedKeys.indexOf(k) >= 0) {
        stripped.push(k);
        return;
      }
      out[k] = clone(aggregates[k]);
    });
    return {
      ok: true,
      view: out,
      audience: 'external',
      stripped_keys: stripped,
      statement: stripped.length
        ? ('Stripped restricted euro aggregates from the external view: ' + stripped.join(', '))
        : 'External view carries no restricted euro aggregates.'
    };
  }

  /* Resolve series codes to bands via the authored CSV only. */
  function bandsForSeries(codes, csvPath) {
    var B = bandsApi();
    if (!B || typeof B.bandFor !== 'function') {
      return { ok: false, error: 'AIMVehicleBands.bandFor unavailable', bands: null };
    }
    var bands = (codes || []).map(function (c) {
      return { code: c, tonnage_band: B.bandFor(c, csvPath) };
    });
    return { ok: true, bands: bands, statement: 'Bands from series_to_band.csv via bandFor only.' };
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderTwoMethods(view) {
    view = view || {};
    var left = view.internal || {};
    var right = view.external || {};
    return '<section class="service-demand-bounds" data-connect-04="panel">'
      + '<h2>Service-demand methods (not averaged)</h2>'
      + '<div class="ids-row">'
      + '<article class="ids-card" data-basis="internal">'
      + '<h3>' + escapeHtml(left.method_label || METHOD_INTERNAL) + '</h3>'
      + '<p>Value: <strong>' + escapeHtml(left.value != null ? left.value : left.cover_pct) + '</strong></p>'
      + '</article>'
      + '<article class="ids-card" data-basis="external">'
      + '<h3>' + escapeHtml(right.method_label || METHOD_EXTERNAL) + '</h3>'
      + '<p>Value: <strong>' + escapeHtml(right.value != null ? right.value : right.cover_pct) + '</strong></p>'
      + '</article>'
      + '</div>'
      + '<p class="note">Switching basis changes the labelled method. The two are never averaged.</p>'
      + '</section>';
  }

  var API = {
    METHOD_INTERNAL: METHOD_INTERNAL,
    METHOD_EXTERNAL: METHOD_EXTERNAL,
    selectServiceBasis: selectServiceBasis,
    bandServiceCover: bandServiceCover,
    poolSharedParts: poolSharedParts,
    externalView: externalView,
    bandsForSeries: bandsForSeries,
    renderTwoMethods: renderTwoMethods
  };

  root.AIMServiceDemandBounds = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
