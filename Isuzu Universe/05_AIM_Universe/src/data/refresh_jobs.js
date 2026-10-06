/* ===========================================================================
   RUN-03 - Run selected refresh jobs without duplication or partial state.

   Integrate approved source refresh with locks, explicit versions, retry limits
   and failure records. Manual execution remains available. Disposable jobs only
   — do not touch the scheduled-job registry or Windows tasks.

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

  function makeRefreshRunner(options) {
    options = options || {};
    var maxRetries = options.maxRetries == null ? 2 : Number(options.maxRetries);
    var locks = Object.create(null);
    var sources = Object.create(null); /* source_id -> { version, accepted_at, evidence_date, payload } */
    var failures = [];
    var activityLog = [];

    function getSource(sourceId) {
      return sources[sourceId] ? deepClone(sources[sourceId]) : null;
    }

    function acceptSource(sourceId, version, meta) {
      meta = meta || {};
      sources[sourceId] = {
        source_id: sourceId,
        version: version,
        accepted_at: name(meta.accepted_at) || null,
        evidence_date: name(meta.evidence_date) || null,
        payload: deepClone(meta.payload || null),
        synthetic: true
      };
      return deepClone(sources[sourceId]);
    }

    function runJob(job) {
      job = job || {};
      var jobId = name(job.job_id) || ('JOB-' + (activityLog.length + 1));
      var sourceId = name(job.source_id);
      if (!sourceId) {
        return { ok: false, code: 'SOURCE_REQUIRED', error: 'A refresh job needs a source_id.' };
      }
      var version = name(job.version) || String(job.version || '');
      if (!version) {
        return { ok: false, code: 'VERSION_REQUIRED', error: 'A refresh job needs an explicit version.' };
      }

      /* Lock: two simultaneous runs do not accept duplicate activity. */
      if (locks[sourceId]) {
        var dup = {
          ok: false,
          accepted: false,
          duplicate: true,
          code: 'LOCK_HELD',
          job_id: jobId,
          source_id: sourceId,
          statement: 'A refresh is already running for this source. Duplicate activity was not accepted.'
        };
        activityLog.push(Object.assign({ at: name(job.at) || null, kind: 'duplicate_refused' }, dup));
        return dup;
      }

      locks[sourceId] = { job_id: jobId, held_at: name(job.at) || null };
      try {
        if (job.interrupt) {
          var fail = {
            ok: false,
            accepted: false,
            interrupted: true,
            code: 'INTERRUPTED',
            job_id: jobId,
            source_id: sourceId,
            failed_step: name(job.fail_at) || 'apply',
            last_accepted: getSource(sourceId),
            statement: 'Job interrupted. Last accepted source retained; unrelated evidence dates unchanged.'
          };
          failures.push(deepClone(fail));
          activityLog.push(Object.assign({ at: name(job.at) || null, kind: 'interrupted' }, fail));
          return fail;
        }

        var retries = 0;
        var applied = false;
        var lastErr = null;
        while (retries <= maxRetries && !applied) {
          if (job.fail_times && retries < Number(job.fail_times)) {
            lastErr = 'synthetic_transient_failure';
            retries += 1;
            continue;
          }
          acceptSource(sourceId, version, {
            accepted_at: name(job.at) || null,
            evidence_date: name(job.evidence_date) || null,
            payload: job.payload || { label: 'synthetic_refresh', version: version }
          });
          applied = true;
        }

        if (!applied) {
          var exhausted = {
            ok: false,
            accepted: false,
            code: 'RETRY_EXHAUSTED',
            job_id: jobId,
            source_id: sourceId,
            retries: retries,
            error: lastErr,
            last_accepted: getSource(sourceId),
            statement: 'Retry limit reached. Last accepted source retained.'
          };
          failures.push(deepClone(exhausted));
          activityLog.push(Object.assign({ at: name(job.at) || null, kind: 'retry_exhausted' }, exhausted));
          return exhausted;
        }

        var ok = {
          ok: true,
          accepted: true,
          duplicate: false,
          job_id: jobId,
          source_id: sourceId,
          version: version,
          source: getSource(sourceId),
          retries: retries,
          statement: 'Refresh accepted for source ' + sourceId + ' at version ' + version + '.'
        };
        activityLog.push(Object.assign({ at: name(job.at) || null, kind: 'accepted' }, ok));
        return ok;
      } finally {
        delete locks[sourceId];
      }
    }

    /* Run two jobs as if simultaneous: second must see the lock. */
    function runSimultaneous(jobA, jobB) {
      jobA = Object.assign({}, jobA);
      jobB = Object.assign({}, jobB);
      var sourceId = name(jobA.source_id) || name(jobB.source_id);
      locks[sourceId] = { job_id: name(jobA.job_id) || 'JOB-A', held_at: name(jobA.at) || null };
      var first;
      try {
        /* First holds lock and completes inside. */
        delete locks[sourceId];
        first = runJob(jobA);
        /* Re-hold to simulate overlap for the second call. */
        locks[sourceId] = { job_id: first.job_id || 'JOB-A', held_at: name(jobA.at) || null };
        var second = runJob(jobB);
        return { first: first, second: second };
      } finally {
        delete locks[sourceId];
      }
    }

    function evidenceDates() {
      var out = {};
      Object.keys(sources).forEach(function (k) {
        out[k] = sources[k].evidence_date;
      });
      return out;
    }

    return {
      runJob: runJob,
      runSimultaneous: runSimultaneous,
      getSource: getSource,
      acceptSource: acceptSource,
      evidenceDates: evidenceDates,
      failures: function () { return deepClone(failures); },
      activityLog: function () { return deepClone(activityLog); },
      isLocked: function (sourceId) { return !!locks[sourceId]; }
    };
  }

  var API = { makeRefreshRunner: makeRefreshRunner };
  root.AIMRefreshJobs = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
