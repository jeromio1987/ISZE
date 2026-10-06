/* ===========================================================================
   RUN-01 - SQLite storage adapter for AIMCaseStore.makeCaseService.

   Same adapter surface as the file/memory/browser adapters in store.js
   (describe / readIndex / load / loadAll / save / remove). The case contract
   stays in schema.js + store.js; this file only persists JSON rows.
   Local disposable development database only.
   =========================================================================== */
(function (root) {
  'use strict';

  var DatabaseSync = require('node:sqlite').DatabaseSync;
  var migrate = require('./migrate.js');

  function makeSqliteAdapter(options) {
    options = options || {};
    var dbPath = options.dbPath;
    if (!dbPath) throw new Error('makeSqliteAdapter needs a dbPath. Nothing was written.');

    if (options.applyMigrations !== false) {
      migrate.applyMigrations(dbPath, { now: options.now });
    }

    var db = new DatabaseSync(dbPath);

    function describe() {
      return {
        kind: 'sqlite',
        durable: true,
        shared: true,
        statement: 'Held in a local SQLite file served on 127.0.0.1. Survives a process restart. '
          + 'Shared across local processes that use this service; not a multi-machine host and not '
          + 'an identity provider.',
        dbPath: dbPath
      };
    }

    return {
      dbPath: dbPath,
      describe: describe,
      readIndex: function () {
        return db.prepare('SELECT case_id FROM cases ORDER BY case_id').all()
          .map(function (r) { return r.case_id; });
      },
      load: function (id) {
        if (!id) return null;
        var row = db.prepare('SELECT record_json FROM cases WHERE case_id = ?').get(String(id));
        if (!row) return null;
        return JSON.parse(row.record_json);
      },
      loadAll: function () {
        var out = {};
        db.prepare('SELECT case_id, record_json FROM cases').all().forEach(function (row) {
          out[row.case_id] = JSON.parse(row.record_json);
        });
        return out;
      },
      save: function (id, record) {
        var json = JSON.stringify(record);
        var updated = (record && record.updated_at) || new Date().toISOString();
        db.prepare(
          'INSERT INTO cases (case_id, record_json, updated_at) VALUES (?, ?, ?) '
          + 'ON CONFLICT(case_id) DO UPDATE SET record_json = excluded.record_json, '
          + 'updated_at = excluded.updated_at'
        ).run(String(id), json, String(updated));
        return { ok: true, durable: true };
      },
      remove: function (id) {
        db.prepare('DELETE FROM cases WHERE case_id = ?').run(String(id));
        return { ok: true };
      },
      close: function () {
        db.close();
      }
    };
  }

  var API = { makeSqliteAdapter: makeSqliteAdapter };
  if (typeof module === 'object' && module.exports) module.exports = API;
  else root.AIMCaseSqliteAdapter = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
