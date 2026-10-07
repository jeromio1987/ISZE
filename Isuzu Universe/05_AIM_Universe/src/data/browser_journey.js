/* ===========================================================================
   ACCEPT-02 helpers - complete browser journey reporting.

   Route continuity: each claimed step carries the same case context and result.
   A blocked browser environment is reported as untested, never converted into
   a passed restart/persistence result.

   The real file:// journey is driven by tests/accept/accept_02_journey.py.
   This module holds the reporting contract the node evidence lines call.
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

  function sameContext(a, b, keys) {
    a = a || {}; b = b || {};
    keys = Array.isArray(keys) ? keys : Object.keys(a);
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (JSON.stringify(a[k]) !== JSON.stringify(b[k])) return false;
    }
    return true;
  }

  /* E1: all claimed working routes complete with the same context and result. */
  function verifyRouteContinuity(steps, keys) {
    steps = Array.isArray(steps) ? steps : [];
    if (!steps.length) {
      return { ok: false, code: 'NO_STEPS', error: 'No journey steps were claimed.' };
    }
    var contextKeys = (keys && keys.context) || ['case_id', 'objective', 'scenario_id'];
    var resultKeys = (keys && keys.result) || ['revenue_after', 'gp_after'];
    var base = steps[0];
    var mismatches = [];
    for (var i = 0; i < steps.length; i++) {
      var s = steps[i] || {};
      if (!s.completed) {
        mismatches.push({ step: name(s.step) || ('step-' + i), reason: 'not completed' });
        continue;
      }
      if (!sameContext(base.context, s.context, contextKeys)) {
        mismatches.push({ step: name(s.step) || ('step-' + i), reason: 'context changed' });
      }
      if (!sameContext(base.result, s.result, resultKeys)) {
        mismatches.push({ step: name(s.step) || ('step-' + i), reason: 'result changed' });
      }
    }
    return {
      ok: mismatches.length === 0,
      steps_checked: steps.length,
      mismatches: mismatches,
      statement: mismatches.length === 0
        ? 'All claimed working routes completed with the same context and result at each step.'
        : 'Journey continuity failed at ' + mismatches.length + ' step(s).'
    };
  }

  /* E2: blocked browser -> UNTESTED, never a passed restart/persistence. */
  function reportBrowserEnvironment(env) {
    env = env || {};
    if (env.blocked) {
      return {
        status: 'UNTESTED',
        passed: false,
        restart_persistence_passed: false,
        blocked: true,
        reason: name(env.reason) || 'Browser environment blocked',
        statement: 'A blocked browser environment is reported as untested, not converted into a passed restart/persistence test.'
      };
    }
    if (env.started) {
      return {
        status: 'READY',
        passed: null,
        restart_persistence_passed: null,
        blocked: false,
        statement: 'Browser environment started; journey results are recorded separately.'
      };
    }
    return {
      status: 'UNTESTED',
      passed: false,
      restart_persistence_passed: false,
      blocked: true,
      reason: 'Browser did not start',
      statement: 'A blocked browser environment is reported as untested, not converted into a passed restart/persistence test.'
    };
  }

  var API = {
    verifyRouteContinuity: verifyRouteContinuity,
    reportBrowserEnvironment: reportBrowserEnvironment,
    sameContext: sameContext
  };
  root.AIMBrowserJourney = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
