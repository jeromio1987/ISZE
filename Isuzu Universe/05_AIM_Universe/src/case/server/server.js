/* ===========================================================================
   RUN-01 - smallest shared local case service (node:http on 127.0.0.1).

   One owner of cases: AIMCaseStore.makeCaseService over the SQLite adapter.
   One pricing implementation/contract: AIMEngine.calculate in src/engine/engine.js.
   This process does not compute prices and must not grow a second financial engine.
   Synthetic seed only. No identity provider (SAFE-01 is later).
   =========================================================================== */
(function (root) {
  'use strict';

  var http = require('node:http');
  var fs = require('fs');
  var path = require('path');
  var store = require('../store.js');
  var migrate = require('./migrate.js');
  var sqlite = require('./sqlite_adapter.js');

  var CASE_OWNER = 'AIMCaseStore.makeCaseService';
  var PRICING_OWNER = 'AIMEngine.calculate';

  function owners() {
    return {
      cases: CASE_OWNER,
      pricing: PRICING_OWNER,
      statement: 'Cases are owned by makeCaseService. Prices are owned by engine.calculate. '
        + 'This shared backend persists cases only; it does not introduce a second financial engine.'
    };
  }

  function assertNoSecondFinancialEngine(serverDir) {
    serverDir = serverDir || __dirname;
    var offenders = [];
    fs.readdirSync(serverDir).forEach(function (name) {
      if (!/\.js$/i.test(name)) return;
      var text = fs.readFileSync(path.join(serverDir, name), 'utf8');
      /* Real definitions only. The detector's own source strings are not a hit. */
      var hasCalc = /(^|\n)\s*function\s+calculate\s*\(/.test(text);
      var hasFake = /(^|\n)\s*function\s+(fakePricingEngine|secondFinancialEngine)\s*\(/.test(text)
        || /(^|\n)\s*var\s+priceEngine\s*=/.test(text);
      if (hasCalc || hasFake) {
        offenders.push(name);
      }
    });
    if (offenders.length) {
      return {
        ok: false,
        error: 'A second financial engine appeared under src/case/server/: ' + offenders.join(', '),
        offenders: offenders,
        owners: owners()
      };
    }
    return { ok: true, offenders: [], owners: owners() };
  }

  function seedSynthetic(service) {
    return service.create({
      case_id: 'SYNTH-RUN01-SEED',
      customer: 'Synthetic customer',
      market: 'SYNTH',
      part_number: 'SYNTH-PART-RUN01',
      description: 'Synthetic RUN-01 seed part',
      owner_role: 'case_owner',
      scope_note: 'Synthetic. No real part, customer or price appears in this seed.',
      by: 'run-01-seed'
    });
  }

  function readJson(req, cb) {
    var chunks = [];
    req.on('data', function (c) { chunks.push(c); });
    req.on('end', function () {
      if (!chunks.length) return cb(null, {});
      try { cb(null, JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch (e) { cb(e); }
    });
  }

  function send(res, code, body) {
    var payload = JSON.stringify(body);
    res.writeHead(code, {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Length': Buffer.byteLength(payload)
    });
    res.end(payload);
  }

  function startSharedBackend(options) {
    options = options || {};
    var dbPath = options.dbPath;
    if (!dbPath) throw new Error('startSharedBackend needs a dbPath.');
    var host = options.host || '127.0.0.1';
    if (host !== '127.0.0.1') {
      throw new Error('RUN-01 binds only to 127.0.0.1 (local development).');
    }
    var port = options.port == null ? 0 : Number(options.port);

    var mig = migrate.applyMigrations(dbPath, { now: options.now });
    var adapter = sqlite.makeSqliteAdapter({
      dbPath: dbPath,
      applyMigrations: false,
      now: options.now
    });
    var service = store.makeCaseService({
      adapter: adapter,
      now: options.now,
      caller: options.caller || 'shared-backend',
      identityMode: 'development-only'
    });

    var seedResult = null;
    if (options.seed !== false) {
      var existingSeed = service.get('SYNTH-RUN01-SEED');
      if (existingSeed) {
        seedResult = { ok: true, record: existingSeed, already: true };
      } else {
        seedResult = seedSynthetic(service);
      }
    }

    var engineCheck = assertNoSecondFinancialEngine(__dirname);
    if (!engineCheck.ok) {
      adapter.close();
      throw new Error(engineCheck.error);
    }

    var server = http.createServer(function (req, res) {
      var url = req.url || '/';
      var method = req.method || 'GET';

      if (method === 'GET' && url === '/health') {
        return send(res, 200, {
          ok: true,
          host: host,
          storage: adapter.describe(),
          migrations: mig,
          fingerprint: migrate.migrationFingerprint(dbPath),
          owners: owners()
        });
      }

      if (method === 'GET' && url === '/owners') {
        return send(res, 200, Object.assign({ ok: true }, assertNoSecondFinancialEngine(__dirname)));
      }

      if (method === 'GET' && url === '/cases') {
        return send(res, 200, { ok: true, cases: service.list() });
      }

      var one = url.match(/^\/cases\/([^/?#]+)$/);
      if (method === 'GET' && one) {
        var record = service.get(decodeURIComponent(one[1]));
        if (!record) return send(res, 404, { ok: false, code: 'NO_SUCH_CASE' });
        return send(res, 200, { ok: true, record: record });
      }

      if (method === 'POST' && url === '/cases') {
        return readJson(req, function (err, body) {
          if (err) return send(res, 400, { ok: false, code: 'BAD_JSON', error: String(err.message || err) });
          var created = service.create(body || {});
          return send(res, created.ok ? 201 : 400, created);
        });
      }

      return send(res, 404, { ok: false, code: 'NOT_FOUND' });
    });

    var listening = new Promise(function (resolve, reject) {
      server.once('error', reject);
      server.listen(port, host, function () {
        var addr = server.address();
        resolve({
          host: host,
          port: addr.port,
          url: 'http://' + host + ':' + addr.port
        });
      });
    });

    function close() {
      return new Promise(function (resolve) {
        server.close(function () {
          try { adapter.close(); } catch (e) { /* ignore */ }
          resolve();
        });
      });
    }

    return {
      ready: listening,
      close: close,
      service: service,
      adapter: adapter,
      migrations: mig,
      seed: seedResult,
      owners: owners,
      assertNoSecondFinancialEngine: assertNoSecondFinancialEngine,
      server: server
    };
  }

  var API = {
    startSharedBackend: startSharedBackend,
    applyMigrations: migrate.applyMigrations,
    migrationFingerprint: migrate.migrationFingerprint,
    makeSqliteAdapter: sqlite.makeSqliteAdapter,
    seedSynthetic: seedSynthetic,
    owners: owners,
    assertNoSecondFinancialEngine: assertNoSecondFinancialEngine,
    CASE_OWNER: CASE_OWNER,
    PRICING_OWNER: PRICING_OWNER
  };

  if (typeof module === 'object' && module.exports) module.exports = API;
  else root.AIMCaseSharedBackend = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
