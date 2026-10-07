/* ===========================================================================
   RUN-08 - Package an internal release and a recoverable deployment route.

   Versioned local build/start/test instructions, release notes of actual
   changes, dependency lock, rollback and troubleshooting. External deployment
   stays disabled. Do not call the task plan a completed release.

   Synthetic packaging only. No upload, publish or production deploy.
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

  function makeReleasePackager(options) {
    options = options || {};
    var packages = [];

    function buildPackage(spec) {
      spec = spec || {};
      var version = name(spec.version) || '0.0.0-internal';
      var files = Array.isArray(spec.files) ? spec.files : [];
      var privateHits = [];
      files.forEach(function (f) {
        var content = String((f && f.content) || '').toLowerCase();
        if (content.indexOf('participant_private') >= 0 || content.indexOf('restricted_cost') >= 0) {
          privateHits.push(name(f.path) || 'unknown');
        }
      });
      if (privateHits.length) {
        return {
          ok: false,
          code: 'PRIVATE_DATA_IN_PACKAGE',
          error: 'Delivered source package must omit private data.',
          private_paths: privateHits,
          published: false,
          deployed: false
        };
      }
      var notes = Array.isArray(spec.actual_changes) ? spec.actual_changes.slice() : [];
      if (spec.call_task_plan_a_release) {
        return {
          ok: false,
          code: 'TASK_PLAN_IS_NOT_A_RELEASE',
          error: 'Do not call the supplied new task plan a completed release.',
          published: false,
          deployed: false
        };
      }
      var pkg = {
        ok: true,
        version: version,
        instructions: {
          build: 'python tools/build.py',
          start: 'double-click dist/OPEN_AIM_Pricing_Decisions_v04.cmd',
          test: 'node --test && node tests/run_tests.cjs'
        },
        release_notes: notes,
        dependency_lock: name(spec.dependency_lock) || 'package-lock.json',
        rollback: name(spec.rollback) || ('git checkout ' + version + ' && python tools/build.py'),
        troubleshooting: [
          'If the page is blank, rebuild with tools/build.py and reopen the launcher.',
          'Restricted_value_sweep must stay CLEAN before sharing internally.'
        ],
        restrictions: {
          external_deployment_disabled: true,
          unverified_live_use: true,
          public_publishing: false,
          statement: 'Internal release candidate only. No public publishing. Live-use remains unverified.'
        },
        published: false,
        deployed: false,
        synthetic: true
      };
      packages.push(deepClone(pkg));
      return deepClone(pkg);
    }

    function startReleaseCandidate(pkg, runner) {
      pkg = pkg || {};
      runner = runner || {};
      if (!pkg.ok) {
        return { ok: false, code: 'PACKAGE_INVALID', started: false };
      }
      if (pkg.deployed || pkg.published) {
        return { ok: false, code: 'EXTERNAL_DISABLED', started: false };
      }
      var journey = Array.isArray(runner.journey_steps) ? runner.journey_steps : [];
      var reproduced = journey.length > 0 && journey.every(function (s) { return s && s.ok; });
      return {
        ok: reproduced,
        started: true,
        deployed: false,
        published: false,
        journey_reproduced: reproduced,
        statement: reproduced
          ? 'Second developer can start the release candidate and reproduce the selected internal journey from the instructions.'
          : 'Release candidate started but the selected internal journey was not reproduced.'
      };
    }

    function deployExternal() {
      return {
        ok: false,
        deployed: false,
        published: false,
        code: 'EXTERNAL_DEPLOY_DISABLED',
        statement: 'External deployment disabled pending access, recovery and audience acceptance.'
      };
    }

    return {
      buildPackage: buildPackage,
      startReleaseCandidate: startReleaseCandidate,
      deployExternal: deployExternal,
      packages: function () { return deepClone(packages); }
    };
  }

  var API = { makeReleasePackager: makeReleasePackager };
  root.AIMReleasePackage = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
