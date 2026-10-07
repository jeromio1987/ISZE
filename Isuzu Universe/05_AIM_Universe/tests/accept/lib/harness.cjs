/* Shared harness for the independent acceptance suite (reviewer-owned).

   Loads the maintained modules directly and the frozen reference payload, so
   the checks judge the current source rather than a rebuilt artifact. Nothing
   here writes into src/, build/ or dist/.

   Every check records: the module file it loaded, and that file's SHA-256 at
   the moment it was loaded, so a report can say which revision was tested.
*/
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const OUT = path.join(ROOT, 'tests', 'accept', '_out');

const PATHS = {
  frozen: path.join(ROOT, 'reference', 'ISZE_AIM_Pricing_Decisions_v03_FROZEN.html'),
  contracts: path.join(ROOT, 'src', 'data', 'contracts.js'),
  engine: path.join(ROOT, 'src', 'engine', 'engine.js'),
  exportData: path.join(ROOT, 'src', 'data', 'export.js'),
  recipients: path.join(ROOT, 'src', 'output', 'recipients.js'),
  scenario: path.join(ROOT, 'src', 'data', 'scenario.js'),
  cases: path.join(ROOT, 'src', 'data', 'cases.js'),
  candidates: path.join(ROOT, 'src', 'data', 'candidates.js'),
  costbasis: path.join(ROOT, 'src', 'data', 'costbasis.js'),
  manifest: path.join(ROOT, 'src', 'data', 'manifest.js'),
  evidence: path.join(ROOT, 'src', 'data', 'evidence.js'),
  app: path.join(ROOT, 'src', 'ui', 'app.js'),
  build: path.join(ROOT, 'tools', 'build.py'),
  distHtml: path.join(ROOT, 'dist', 'ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html'),
  distReport: path.join(ROOT, 'dist', '_build_report.json'),
  syntheticPayload: path.join(ROOT, 'tests', 'fixtures', 'synthetic_payload.json')
};

function sha256(file) {
  if (!fs.existsSync(file)) return null;
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function exists(file) { return fs.existsSync(file); }

/* Pin the revision of every file this run touches. */
function pin(files) {
  const out = {};
  for (const f of files) out[path.relative(ROOT, f).replace(/\\/g, '/')] = sha256(f);
  return out;
}

/* The frozen case-data block, exactly as the supplied review reads it. */
function frozenPayload() {
  const html = fs.readFileSync(PATHS.frozen, 'utf8');
  const m = html.match(/<script\b[^>]*\bid=["']case-data["'][^>]*>([\s\S]*?)<\/script>/i);
  if (!m) throw new Error('the frozen reference has no case-data block');
  return JSON.parse(m[1]);
}

/* Run a browser-shaped module in a vm context that supplies only what the
   module asks for. `module.exports` is returned. */
function loadInVm(file, sandboxExtras) {
  const sandbox = Object.assign({ module: { exports: {} }, console: { log() {}, warn() {}, error() {} } },
    sandboxExtras || {});
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(file, 'utf8'), sandbox, { filename: file, timeout: 20000 });
  return sandbox.module.exports;
}

/* Node-native load of a module that uses module.exports + require. */
function requireModule(file) {
  delete require.cache[require.resolve(file)];
  return require(file);
}

/* ---------------------------------------------------------------- results -- */

function makeRun(id, title, notes) {
  return {
    check: id, title, notes: notes || null,
    review_date: new Date().toISOString(),
    node: process.version,
    environment: { platform: process.platform, cwd: process.cwd() },
    tested_files: {}, results: []
  };
}

function test(run, checkId, name, fn) {
  try {
    const evidence = fn();
    run.results.push({ id: checkId, name, status: 'PASS', evidence: evidence === undefined ? null : evidence });
  } catch (e) {
    run.results.push({ id: checkId, name, status: 'FAIL', evidence: String(e && e.message ? e.message : e) });
  }
}

function summary(run) {
  const findings = run.results.filter(r => r.known_finding);
  return {
    pass: run.results.filter(r => r.status === 'PASS').length,
    fail: run.results.filter(r => r.status === 'FAIL' && !r.known_finding).length,
    skipped: run.results.filter(r => r.status === 'SKIP' || r.status === 'UNTESTED').length,
    untested: run.results.filter(r => r.status === 'UNTESTED').length,
    known_findings: findings.length,
    total: run.results.length
  };
}

function write(run, filename) {
  fs.mkdirSync(OUT, { recursive: true });
  run.known_findings = run.results.filter(r => r.known_finding);
  run.summary = summary(run);
  const target = path.join(OUT, filename);
  fs.writeFileSync(target, JSON.stringify(run, null, 2) + '\n');
  for (const r of run.results) {
    if (r.known_finding) continue;
    console.log(`${r.status === 'PASS' ? 'PASS' : r.status === 'SKIP' ? 'SKIP' : r.status === 'UNTESTED' ? 'UNTESTED' : 'FAIL'} ${r.id}: ${r.name}`
      + (r.status === 'PASS' ? '' : ' -- ' + r.evidence));
  }
  if (run.known_findings.length) {
    console.log('KNOWN_FINDINGS');
    for (const r of run.known_findings) {
      console.log('FINDING ' + r.id + ': ' + r.name + ' -- ' + r.evidence
        + (r.reproduction ? ' | reproduction: ' + r.reproduction : ''));
    }
  }
  if (run.known_findings.length) console.log(run.known_findings.length + ' known findings open');
  console.log(JSON.stringify(run.summary));
  console.log('raw: ' + target);
  return run.summary;
}

/* Exit codes. A known finding is not an ordinary fail, but it is never exit 0:
   run_all.ps1 reads 3 as "known findings open" and 4 as "not run". */
const EXIT = { PASS: 0, FAIL: 1, KNOWN_FINDINGS: 3, NOT_RUN: 4 };
function exitCode(s) {
  if (s.fail) return EXIT.FAIL;
  if (s.untested || s.skipped) return EXIT.NOT_RUN;
  if (s.known_findings) return EXIT.KNOWN_FINDINGS;
  return EXIT.PASS;
}

/* deterministic assertion helper: reports the observed and expected values */
function approx(observed, expected, tol, label) {
  const t = tol === undefined ? 1e-8 : tol;
  const ok = Number.isFinite(observed) && Math.abs(observed - expected) <= t;
  if (!ok) throw new Error(`${label || 'value'}: observed ${observed}; expected ${expected} (tol ${t})`);
  return `${label || 'value'} = ${observed}`;
}
function isTrue(cond, message) { if (!cond) throw new Error(message || 'expected true'); return 'yes'; }
function eq(observed, expected, label) {
  if (observed !== expected) throw new Error(`${label || 'value'}: observed ${JSON.stringify(observed)}; expected ${JSON.stringify(expected)}`);
  return `${label || 'value'} = ${JSON.stringify(observed)}`;
}

module.exports = {
  ROOT, OUT, PATHS, sha256, exists, pin, frozenPayload, loadInVm, requireModule,
  makeRun, test, summary, write, approx, isTrue, eq, EXIT, exitCode
};
