/* ===========================================================================
   CONNECT-08 - Enable each service only when it returns supported work.

   Capability registry: unavailable | source-limited | internally usable |
   approved participant-facing. Same case/context across enabled services.
   Adapters use labelled synthetic fixtures. Connected badges or empty enabled
   tabs are not completed integration. AI is not a prerequisite.

   Synthetic fixtures only.
   =========================================================================== */
(function (root) {
  'use strict';

  var CAPABILITY_LEVELS = [
    'unavailable',
    'source_limited',
    'internally_usable',
    'approved_participant_facing'
  ];

  var OPTIONAL_INPUTS = ['ids', 'fleet', 'stock', 'tender'];

  function deepClone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function levelOf(v) {
    var s = name(v);
    return CAPABILITY_LEVELS.indexOf(s) >= 0 ? s : 'unavailable';
  }

  function makeRegistry(options) {
    options = options || {};
    var services = {};
    var caseContext = deepClone(options.case_context || null);

    function register(serviceId, spec) {
      spec = spec || {};
      var id = name(serviceId);
      if (!id) return { ok: false, error: 'A service needs an id.' };
      var level = levelOf(spec.capability);
      var source = name(spec.source);
      var route = name(spec.response_route);
      var adapterKind = name(spec.adapter_kind) || 'unknown';
      var developmentOnly = adapterKind === 'test' || adapterKind === 'development' ||
        spec.development_only === true;
      var returnsSupportedWork = spec.returns_supported_work === true;

      /* Enable only when supported work is returned and level is usable+. */
      var enabled = returnsSupportedWork &&
        (level === 'internally_usable' || level === 'approved_participant_facing');

      services[id] = {
        service_id: id,
        capability: level,
        enabled: enabled,
        returns_supported_work: returnsSupportedWork,
        source: source,
        response_route: route,
        adapter_kind: adapterKind,
        development_only: developmentOnly,
        connected_badge: false,
        empty_enabled_tab_as_complete: false,
        optional_inputs: Array.isArray(spec.optional_inputs)
          ? spec.optional_inputs.slice()
          : OPTIONAL_INPUTS.slice(),
        label: name(spec.label) || id
      };
      return { ok: true, service: deepClone(services[id]) };
    }

    function setCaseContext(ctx) {
      caseContext = deepClone(ctx || null);
      return { ok: true, case_context: deepClone(caseContext) };
    }

    function getCaseContext() {
      return deepClone(caseContext);
    }

    function listEnabled() {
      return Object.keys(services).filter(function (k) {
        return services[k].enabled;
      }).map(function (k) {
        return deepClone(services[k]);
      });
    }

    function describeEnabled() {
      return listEnabled().map(function (s) {
        return {
          service_id: s.service_id,
          source: s.source,
          response_route: s.response_route,
          development_only: s.development_only,
          adapter_kind: s.adapter_kind,
          capability: s.capability,
          connected_badge: false,
          statement: s.development_only
            ? 'Test adapter — development-only. Source ' + (s.source || 'unstated') +
              '; response route ' + (s.response_route || 'unstated') + '.'
            : 'Source ' + (s.source || 'unstated') +
              '; response route ' + (s.response_route || 'unstated') + '.'
        };
      });
    }

    /* Pricing/case journey with optional inputs missing must still work. */
    function runPricingCaseJourney(input) {
      input = input || {};
      var missing = [];
      OPTIONAL_INPUTS.forEach(function (key) {
        if (input[key] == null || input[key] === false || input[key] === '') {
          missing.push(key);
        }
      });

      var caseId = name(input.case_id) || (caseContext && name(caseContext.case_id)) || 'SYN-CASE';
      var part = name(input.part_number) || (caseContext && name(caseContext.part_number));
      if (!part) {
        return {
          ok: false,
          broken: true,
          error: 'Pricing/case journey needs a part number.',
          missing_optional_inputs: missing
        };
      }

      var result = {
        ok: true,
        broken: false,
        case_id: caseId,
        part_number: part,
        case_context: deepClone(caseContext),
        missing_optional_inputs: missing,
        optional_ids_present: missing.indexOf('ids') < 0,
        optional_fleet_present: missing.indexOf('fleet') < 0,
        optional_stock_present: missing.indexOf('stock') < 0,
        optional_tender_present: missing.indexOf('tender') < 0,
        pricing_journey_usable: true,
        enabled_services: listEnabled().map(function (s) { return s.service_id; }),
        statement: missing.length
          ? 'Pricing/case journey continues without optional inputs: ' + missing.join(', ') + '.'
          : 'Pricing/case journey has all optional inputs present.'
      };
      return result;
    }

    return {
      CAPABILITY_LEVELS: CAPABILITY_LEVELS.slice(),
      OPTIONAL_INPUTS: OPTIONAL_INPUTS.slice(),
      register: register,
      setCaseContext: setCaseContext,
      getCaseContext: getCaseContext,
      listEnabled: listEnabled,
      describeEnabled: describeEnabled,
      runPricingCaseJourney: runPricingCaseJourney,
      _services: function () { return deepClone(services); }
    };
  }

  var API = {
    CAPABILITY_LEVELS: CAPABILITY_LEVELS.slice(),
    OPTIONAL_INPUTS: OPTIONAL_INPUTS.slice(),
    makeRegistry: makeRegistry
  };

  root.AIMServiceCapability = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
