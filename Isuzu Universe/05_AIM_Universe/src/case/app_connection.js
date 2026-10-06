/* ===========================================================================
   RUN-02 - Connect cases and scenarios to the maintained application.

   Wire the UI to the reusable case service with loading / error / retry.
   Persist the canonical snapshot (scenario + result + review.engine_version)
   and validate or recompute the financial result in the trusted internal
   service before accepting a consequential record.

   One pricing entry point: AIMEngine.calculate (CONTRACT_VERSION).
   Synthetic fixtures only.
   =========================================================================== */
(function (root) {
  'use strict';

  function deepClone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function requireDeps(options) {
    options = options || {};
    var store = options.store;
    var engine = options.engine;
    if (!store || typeof store.makeCaseService !== 'function') {
      throw new Error('RUN-02 app connection needs AIMCaseStore (makeCaseService).');
    }
    if (!engine || typeof engine.calculate !== 'function') {
      throw new Error('RUN-02 app connection needs AIMEngine.calculate.');
    }
    return { store: store, engine: engine };
  }

  function makeAppConnection(options) {
    options = options || {};
    var deps = requireDeps(options);
    var adapter = options.adapter || deps.store.makeMemoryAdapter();
    var service = deps.store.makeCaseService({ adapter: adapter, now: options.now });
    var engine = deps.engine;
    var engineVersion = engine.CONTRACT_VERSION;
    var maxRetries = options.maxRetries == null ? 2 : Number(options.maxRetries);

    var ui = {
      status: 'idle',
      loading: false,
      error: null,
      retries: 0,
      last_action: null
    };

    function setUi(patch) {
      Object.keys(patch).forEach(function (k) { ui[k] = patch[k]; });
      return deepClone(ui);
    }

    function computeTrusted(inputs) {
      var result = engine.calculate(deepClone(inputs));
      return {
        engine_version: engineVersion,
        inputs: deepClone(inputs),
        result: deepClone(result),
        profit_eur: result && result.gp_after != null ? result.gp_after : null,
        revenue_eur: result && result.revenue_after != null ? result.revenue_after : null
      };
    }

    function snapshotFromRecord(record) {
      if (!record) return null;
      var review = record.review || {};
      return {
        engine_version: review.engine_version,
        inputs: deepClone(record.scenario),
        stored_result: deepClone(record.result),
        consequential: !!(record.review && record.review.consequential_accepted)
      };
    }

    function saveScenario(caseMeta, scenarioInputs) {
      setUi({ status: 'loading', loading: true, error: null, last_action: 'save' });
      try {
        var trusted = computeTrusted(scenarioInputs);
        var created = service.create(Object.assign({}, caseMeta || {}, {
          part_number: (caseMeta && caseMeta.part_number) || 'SYN-PN-RUN02',
          customer: (caseMeta && caseMeta.customer) || 'Synthetic RUN-02 customer',
          by: (caseMeta && caseMeta.by) || 'run-02-ui'
        }));
        if (!created.ok) {
          setUi({ status: 'error', loading: false, error: created.error || 'create failed' });
          return { ok: false, ui: deepClone(ui), error: created.error };
        }

        var nextRecord = Object.assign({}, created.record, {
          scenario: trusted.inputs,
          result: trusted.result,
          review: {
            engine_version: trusted.engine_version,
            kind: 'canonical_scenario_snapshot',
            immutable: true,
            synthetic: true,
            profit_eur: trusted.profit_eur
          }
        });

        var saved = service.saveRecord(nextRecord, {
          by: 'run-02-ui-save',
          expected_version: created.record.version
        });

        if (!saved.ok) {
          setUi({ status: 'error', loading: false, error: saved.error || 'save failed' });
          return { ok: false, ui: deepClone(ui), error: saved.error, code: saved.code };
        }

        var snapshot = snapshotFromRecord(saved.record);
        setUi({ status: 'ready', loading: false, error: null, retries: 0 });
        return {
          ok: true,
          ui: deepClone(ui),
          case_id: saved.record.case_id,
          version: saved.record.version,
          snapshot: snapshot,
          record: saved.record
        };
      } catch (e) {
        setUi({ status: 'error', loading: false, error: String(e && e.message || e) });
        return { ok: false, ui: deepClone(ui), error: String(e && e.message || e) };
      }
    }

    function reopenScenario(caseId, version) {
      setUi({ status: 'loading', loading: true, error: null, last_action: 'reopen' });
      try {
        var opened = service.reopen(caseId, version);
        /* reopen returns the rebuilt view directly; errors carry ok:false. */
        if (opened && opened.ok === false) {
          setUi({ status: 'error', loading: false, error: opened.error || 'reopen failed' });
          return { ok: false, ui: deepClone(ui), error: opened.error };
        }
        var record = {
          case_id: opened.case_id,
          version: opened.version,
          scenario: opened.scenario,
          result: opened.result,
          review: opened.review
        };
        var snap = snapshotFromRecord(record);
        if (!snap || snap.engine_version == null || !snap.inputs || !snap.stored_result) {
          setUi({ status: 'error', loading: false, error: 'No canonical scenario snapshot on case.' });
          return { ok: false, ui: deepClone(ui), error: 'missing snapshot', opened: opened };
        }
        var match = {
          engine_version_match: snap.engine_version === engineVersion,
          inputs_match: JSON.stringify(snap.inputs) === JSON.stringify(record.scenario),
          stored_result_present: !!snap.stored_result
        };
        var ok = match.engine_version_match && match.inputs_match && match.stored_result_present;
        setUi({ status: ok ? 'ready' : 'error', loading: false, error: ok ? null : 'snapshot mismatch' });
        return {
          ok: ok,
          ui: deepClone(ui),
          case_id: record.case_id,
          version: record.version,
          engine_version: snap.engine_version,
          inputs: deepClone(snap.inputs),
          stored_result: deepClone(snap.stored_result),
          match: match,
          record: record
        };
      } catch (e) {
        setUi({ status: 'error', loading: false, error: String(e && e.message || e) });
        return { ok: false, ui: deepClone(ui), error: String(e && e.message || e) };
      }
    }

    function retryLast(actionFn) {
      if (ui.retries >= maxRetries) {
        return { ok: false, ui: deepClone(ui), error: 'Retry limit reached.' };
      }
      setUi({ retries: ui.retries + 1, status: 'loading', loading: true, error: null, last_action: 'retry' });
      return actionFn();
    }

    function acceptConsequentialRecord(submission) {
      submission = submission || {};
      setUi({ status: 'loading', loading: true, error: null, last_action: 'accept' });

      var inputs = submission.inputs;
      if (!inputs || typeof inputs !== 'object') {
        setUi({ status: 'error', loading: false, error: 'Consequential accept needs scenario inputs.' });
        return { ok: false, accepted: false, code: 'INPUTS_REQUIRED', ui: deepClone(ui) };
      }

      var trusted = computeTrusted(inputs);
      var clientProfit = submission.client_profit_eur;
      var clientResult = submission.client_result;

      if (clientProfit !== undefined && clientProfit !== null) {
        if (!(Number.isFinite(Number(clientProfit)) && Number(clientProfit) === Number(trusted.profit_eur))) {
          setUi({ status: 'error', loading: false, error: 'Client profit does not match trusted recompute.' });
          return {
            ok: false,
            accepted: false,
            code: 'CLIENT_PROFIT_TAMPER_REJECTED',
            ui: deepClone(ui),
            trusted_profit_eur: trusted.profit_eur,
            client_profit_eur: clientProfit,
            statement: 'Tampered client-submitted profit did not create an accepted server-side record.'
          };
        }
      }
      if (clientResult !== undefined && clientResult !== null) {
        var clientGp = clientResult.gp_after != null ? clientResult.gp_after : clientResult.gross_profit_after;
        if (clientGp !== undefined && clientGp !== null &&
            Number(clientGp) !== Number(trusted.profit_eur)) {
          setUi({ status: 'error', loading: false, error: 'Client result does not match trusted recompute.' });
          return {
            ok: false,
            accepted: false,
            code: 'CLIENT_RESULT_TAMPER_REJECTED',
            ui: deepClone(ui),
            statement: 'Tampered client-submitted result did not create an accepted server-side record.'
          };
        }
      }

      var caseId = name(submission.case_id);
      var record;
      if (caseId) {
        var opened = service.reopen(caseId);
        if (opened && opened.ok === false) {
          setUi({ status: 'error', loading: false, error: opened.error || 'case missing' });
          return { ok: false, accepted: false, code: 'NO_SUCH_CASE', ui: deepClone(ui) };
        }
        var loaded = service.load(caseId);
        if (!loaded || !loaded.case_id) {
          setUi({ status: 'error', loading: false, error: 'case missing' });
          return { ok: false, accepted: false, code: 'NO_SUCH_CASE', ui: deepClone(ui) };
        }
        record = loaded;
      } else {
        var created = service.create({
          case_id: name(submission.new_case_id) || undefined,
          part_number: name(submission.part_number) || 'SYN-PN-RUN02',
          customer: 'Synthetic RUN-02 accept',
          by: 'run-02-accept'
        });
        if (!created.ok) {
          setUi({ status: 'error', loading: false, error: created.error });
          return { ok: false, accepted: false, ui: deepClone(ui) };
        }
        record = created.record;
      }

      var saved = service.saveRecord(Object.assign({}, record, {
        scenario: trusted.inputs,
        result: trusted.result,
        review: {
          engine_version: trusted.engine_version,
          kind: 'canonical_scenario_snapshot',
          consequential_accepted: true,
          immutable: true,
          synthetic: true,
          profit_eur: trusted.profit_eur,
          client_fields_ignored_for_authority: true
        }
      }), { by: 'run-02-trusted-accept', expected_version: record.version });

      if (!saved.ok) {
        setUi({ status: 'error', loading: false, error: saved.error });
        return { ok: false, accepted: false, ui: deepClone(ui), error: saved.error };
      }

      setUi({ status: 'ready', loading: false, error: null, retries: 0 });
      return {
        ok: true,
        accepted: true,
        ui: deepClone(ui),
        case_id: saved.record.case_id,
        version: saved.record.version,
        engine_version: trusted.engine_version,
        profit_eur: trusted.profit_eur,
        record: saved.record,
        statement: 'Consequential record accepted only after trusted internal recompute.'
      };
    }

    return {
      engineVersion: function () { return engineVersion; },
      uiState: function () { return deepClone(ui); },
      saveScenario: saveScenario,
      reopenScenario: reopenScenario,
      retryLast: retryLast,
      acceptConsequentialRecord: acceptConsequentialRecord,
      service: service,
      computeTrusted: computeTrusted
    };
  }

  var API = {
    makeAppConnection: makeAppConnection
  };

  root.AIMAppConnection = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
