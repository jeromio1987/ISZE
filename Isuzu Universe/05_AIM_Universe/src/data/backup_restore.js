/* ===========================================================================
   RUN-07 - Back up and restore the full permitted working record.

   Backup scope: database rows, allowed evidence attachments, configuration
   references and application versions. Restore into an isolated environment
   using synthetic data. Untested provider backup features are not recovery
   accepted.

   Synthetic fixtures only. Restore targets a disposable folder only.
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

  function makeBackupService(options) {
    options = options || {};
    var appVersion = name(options.app_version) || 'v04-synthetic';
    var archives = [];
    var recoveryLog = [];

    function createBackup(record) {
      record = record || {};
      var caseId = name(record.case_id);
      if (!caseId) {
        return { ok: false, code: 'CASE_REQUIRED', error: 'Backup needs a case_id.' };
      }
      var archive = {
        archive_id: 'BAK-' + (archives.length + 1),
        app_version: appVersion,
        case: {
          case_id: caseId,
          version: record.version == null ? null : record.version,
          scenario: deepClone(record.scenario || null),
          change_history: deepClone(record.change_history || []),
          evidence: deepClone(record.evidence || [])
        },
        config_refs: deepClone(record.config_refs || []),
        synthetic: true,
        created_at: name(record.at) || null
      };
      archives.push(deepClone(archive));
      return { ok: true, archive_id: archive.archive_id, archive: deepClone(archive) };
    }

    function restore(archiveId, dest) {
      dest = dest || {};
      var isolated = dest.isolated === true || name(dest.folder) != null;
      if (!isolated) {
        return {
          ok: false,
          code: 'ISOLATED_DEST_REQUIRED',
          error: 'Restore must target an isolated disposable folder.',
          recovery_accepted: false
        };
      }
      var archive = null;
      for (var i = 0; i < archives.length; i++) {
        if (archives[i].archive_id === archiveId) { archive = archives[i]; break; }
      }
      if (!archive) {
        return { ok: false, code: 'ARCHIVE_NOT_FOUND', recovery_accepted: false };
      }
      var restored = {
        folder: name(dest.folder) || 'disposable-restore',
        case_id: archive.case.case_id,
        version: archive.case.version,
        scenario: deepClone(archive.case.scenario),
        change_history: deepClone(archive.case.change_history),
        evidence: deepClone(archive.case.evidence),
        config_refs: deepClone(archive.config_refs),
        app_version: archive.app_version,
        database_row_only: false
      };
      var steps = [
        'locate archive ' + archiveId,
        'open isolated folder ' + restored.folder,
        'restore case scenario and version',
        'restore evidence attachments',
        'restore change history',
        'restore configuration references'
      ];
      var result = {
        ok: true,
        restored: restored,
        steps: steps,
        recovery_tested: true,
        recovery_accepted: false, /* human/operator acceptance is separate */
        statement: 'Restored case includes evidence, original scenario/version and change history, not just a database row.'
      };
      recoveryLog.push({ archive_id: archiveId, steps: steps.slice(), ok: true });
      return deepClone(result);
    }

    function markProviderFeature(nameStr, tested) {
      return {
        feature: name(nameStr),
        tested: !!tested,
        recovery_accepted: false,
        statement: tested
          ? 'Recovery tests recorded actual steps/results; operator acceptance remains separate.'
          : 'An untested provider backup feature is not marked recovery accepted.'
      };
    }

    return {
      createBackup: createBackup,
      restore: restore,
      markProviderFeature: markProviderFeature,
      archives: function () { return deepClone(archives); },
      recoveryLog: function () { return deepClone(recoveryLog); }
    };
  }

  var API = { makeBackupService: makeBackupService };
  root.AIMBackupRestore = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
