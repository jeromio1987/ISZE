/* ===========================================================================
   RUN-01 - repeatable SQLite migrations for the shared local case backend.

   Applies numbered *.sql files under migrations/ in name order. Re-running
   against the same database is a no-op for already-applied names. Clean
   disposable storage (a new file) always yields the same applied set.
   =========================================================================== */
(function (root) {
  'use strict';

  var fs = require('fs');
  var path = require('path');
  var DatabaseSync = require('node:sqlite').DatabaseSync;

  var MIGRATIONS_DIR = path.join(__dirname, 'migrations');

  function listMigrationFiles() {
    return fs.readdirSync(MIGRATIONS_DIR)
      .filter(function (f) { return /^\d+_.*\.sql$/i.test(f); })
      .sort();
  }

  function openDb(dbPath) {
    if (!dbPath) throw new Error('applyMigrations needs a database file path.');
    var dir = path.dirname(dbPath);
    fs.mkdirSync(dir, { recursive: true });
    return new DatabaseSync(dbPath);
  }

  function ensureMigrationsTable(db) {
    db.exec(
      'CREATE TABLE IF NOT EXISTS schema_migrations ('
      + ' id INTEGER PRIMARY KEY,'
      + ' name TEXT NOT NULL UNIQUE,'
      + ' applied_at TEXT NOT NULL'
      + ');'
    );
  }

  function appliedNames(db) {
    ensureMigrationsTable(db);
    return db.prepare('SELECT name FROM schema_migrations ORDER BY name').all()
      .map(function (row) { return row.name; });
  }

  function applyMigrations(dbPath, options) {
    options = options || {};
    var clock = options.now || function () { return new Date().toISOString(); };
    var db = openDb(dbPath);
    try {
      ensureMigrationsTable(db);
      var already = {};
      appliedNames(db).forEach(function (n) { already[n] = true; });
      var appliedThisRun = [];
      listMigrationFiles().forEach(function (name) {
        if (already[name]) return;
        var sql = fs.readFileSync(path.join(MIGRATIONS_DIR, name), 'utf8');
        db.exec('BEGIN');
        try {
          db.exec(sql);
          db.prepare(
            'INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)'
          ).run(name, clock());
          db.exec('COMMIT');
        } catch (e) {
          try { db.exec('ROLLBACK'); } catch (e2) { /* ignore */ }
          throw e;
        }
        appliedThisRun.push(name);
        already[name] = true;
      });
      var all = appliedNames(db);
      return {
        ok: true,
        dbPath: dbPath,
        applied_this_run: appliedThisRun,
        applied: all,
        migrations_dir: MIGRATIONS_DIR
      };
    } finally {
      db.close();
    }
  }

  function migrationFingerprint(dbPath) {
    var db = openDb(dbPath);
    try {
      ensureMigrationsTable(db);
      var rows = db.prepare(
        'SELECT name FROM schema_migrations ORDER BY name'
      ).all().map(function (r) { return r.name; });
      var tables = db.prepare(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
      ).all().map(function (r) { return r.name; });
      return { migrations: rows, tables: tables };
    } finally {
      db.close();
    }
  }

  var API = {
    applyMigrations: applyMigrations,
    listMigrationFiles: listMigrationFiles,
    migrationFingerprint: migrationFingerprint,
    MIGRATIONS_DIR: MIGRATIONS_DIR
  };

  if (typeof module === 'object' && module.exports) module.exports = API;
  else root.AIMCaseMigrate = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
