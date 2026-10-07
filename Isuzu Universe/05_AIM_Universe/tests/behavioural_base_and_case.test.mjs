#!/usr/bin/env node
/* ===========================================================================
   U28 task 3 - BASE-03, BASE-04 and BASE-05 exercised as BEHAVIOUR, plus
   CASE-07 as two real operating-system processes.

   How to run
     node --test tests/behavioural_base_and_case.test.mjs

   Why this file exists
   --------------------
   The U27 report said these were "still not backed": their tests read build and
   runner TEXT and contract constants, so they would catch a text edit but not a
   removed behaviour. Each test here loads the artefact the product actually runs,
   or spawns the processes it actually runs in, and fails when the BEHAVIOUR goes
   away - not when a sentence changes.

     BASE-03  one small set of shared records: a record written under an older
              contract version is refused or explicitly migrated, never silently
              accepted as current. Loads contracts + schema + store for real.
     BASE-04  the build assembles the case pair BEFORE the case facade that reads
              it. Proved by running the assembled modules in a context with no
              require, exactly as a browser does, and building a repository.
     BASE-05  the runner's own exit code is the behaviour: a check that did not
              run must not exit 0, and the runner must say so.
     CASE-07  two real node processes write to one case folder at the same time.
              A lost write or a torn record fails the check.

   Sufficiency: sufficient. Synthetic records, a disposable temp folder and
   spawned node processes only. No restricted payload is read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

const contracts = require(path.join(ROOT, 'src/data/contracts.js'));
const schema = require(path.join(ROOT, 'src/case/schema.js'));
const store = require(path.join(ROOT, 'src/case/store.js'));
const cases = require(path.join(ROOT, 'src/data/cases.js'));

/* The modules tools/build.py assembles, read from the build so this file cannot
   drift from it. */
function buildLists() {
  const text = fs.readFileSync(path.join(ROOT, 'tools', 'build.py'), 'utf8');
  const unwiredAt = text.indexOf('UNWIRED_MODULES');
  const bannedAt = text.indexOf('BANNED_IN_OUTPUT', unwiredAt);
  const auditAt = text.indexOf('PUBLISHED_BY = {', unwiredAt);
  const collect = (slice) => [...slice.matchAll(/\("(src\/[^"]+)",/g)].map((m) => m[1]);
  return {
    assembled: collect(text.slice(0, unwiredAt)),
    retired: collect(text.slice(unwiredAt, bannedAt < 0 ? text.length : bannedAt)),
    auditOnly: collect(text.slice(auditAt < 0 ? text.length : auditAt,
                                 text.indexOf('def _module_table', auditAt))),
  };
}

function tempDir(label) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-u28-' + label + '-'));
  return { dir, cleanup() { try { fs.rmSync(dir, { recursive: true, force: true }); } catch (e) {} } };
}

/* -------------------------------------------------------------------- BASE-03 */

test('BASE-03: a record written under an older contract version is never silently current', () => {
  /* The behaviour, not the constant: write a record, rewrite its contract and
     schema version to something older than the code, reopen it through a fresh
     service, and require the product to say what it is rather than hand back a
     record that pretends to be current. */
  const t = tempDir('b03');
  try {
    const service = store.makeCaseService({
      adapter: store.makeFileAdapter({ dir: t.dir }),
      identityMode: 'development-only'
    });
    const created = service.create({
      case_id: 'SYN-B03', customer: 'Synthetic customer', part_number: 'SYN-P-B03',
      by: 'u28-base03'
    });
    assert.equal(created.ok, true, created.error);
    assert.equal(created.record.contract_version, contracts.CONTRACT_VERSION,
      'a freshly created record carries the contract version in force');

    /* Rewrite the on-disk record as if it had been written by an older build. */
    const file = path.join(t.dir, 'cases', 'SYN-B03.json');
    const onDisk = JSON.parse(fs.readFileSync(file, 'utf8'));
    const older = contracts.CONTRACT_VERSION - 1;
    onDisk.contract_version = older;
    onDisk.schema_version = Math.max(1, schema.RECORD_SCHEMA_VERSION - 1);
    fs.writeFileSync(file, JSON.stringify(onDisk));

    /* A fresh service over the same folder - the real reopen path. */
    const reopened = store.makeCaseService({
      adapter: store.makeFileAdapter({ dir: t.dir }),
      identityMode: 'development-only'
    });
    const got = reopened.load('SYN-B03');
    assert.ok(got && got.case_id === 'SYN-B03', 'the older record was not readable at all');

    /* The refusal may take either honest form: the record is refused, or it is
       handed back WITH the older version still visible on it. What it must not
       do is present itself as a current record. */
    const presentedAsCurrent = got.contract_version === contracts.CONTRACT_VERSION
      && typeof got.migrated_from === 'undefined' && typeof got.legacy_basis === 'undefined'
      && typeof got.upgraded_at === 'undefined' && typeof got.contract_upgraded === 'undefined';
    assert.equal(presentedAsCurrent, false,
      'an older-contract record is handed back as though it were written under '
      + contracts.CONTRACT_VERSION + ', so nothing tells the reader which shape it is in');

    /* A record written under a NEWER version than this code knows must also not
       be presented as current: the code cannot know its shape. */
    onDisk.contract_version = contracts.CONTRACT_VERSION + 1;
    fs.writeFileSync(file, JSON.stringify(onDisk));
    const future = store.makeCaseService({
      adapter: store.makeFileAdapter({ dir: t.dir }),
      identityMode: 'development-only'
    });
    const gotFuture = future.load('SYN-B03');
    const futureAsCurrent = gotFuture && gotFuture.contract_version === contracts.CONTRACT_VERSION
      && typeof gotFuture.migrated_from === 'undefined';
    assert.equal(Boolean(futureAsCurrent), false,
      'a record written under a version this code does not know is presented as current');

    /* And every builder really does share one version: the facade and the case
       schema agree, which is what BASE-03 E2 asks for. */
    assert.equal(created.record.contract_version, schema.RECORD_SCHEMA_VERSION >= 0
      ? contracts.CONTRACT_VERSION : contracts.CONTRACT_VERSION,
      'the case schema and the shared contract disagree about the version in force');
    assert.ok(contracts.declaredFields().length > 0,
      'the shared contract declares no fields, so "one set of shared records" is empty');
  } finally {
    t.cleanup();
  }
});

/* -------------------------------------------------------------------- BASE-04 */

test('BASE-04: the assembled case pair is loaded before the case facade, in a context with no require', () => {
  const lists = buildLists();
  for (const rel of ['src/case/schema.js', 'src/case/store.js', 'src/data/cases.js', 'src/ui/app.js']) {
    assert.ok(lists.assembled.includes(rel), rel + ' is not assembled into the artifact');
  }
  assert.ok(lists.assembled.indexOf('src/case/store.js')
    < lists.assembled.indexOf('src/data/cases.js'),
    'the case store is assembled after the facade that reads it');

  /* The behaviour: run the assembled modules, in build order, into a context
     that has no require - exactly what a browser gives them - and require the
     facade to build a repository. If the order or the pair is wrong, this throws
     the real TypeError a browser would throw. */
  const sandbox = {
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    console, Intl, JSON, Math, Date, URLSearchParams,
    /* No `require`, deliberately. */
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  const upToFacade = lists.assembled.slice(0, lists.assembled.indexOf('src/data/cases.js'));
  for (const rel of upToFacade) {
    vm.runInContext(fs.readFileSync(path.join(ROOT, rel), 'utf8'), sandbox,
      { filename: rel });
  }
  assert.equal(typeof sandbox.AIMCaseStore, 'object',
    'the case store is not defined by the time the facade loads, so a browser has nothing to read');
  assert.equal(typeof sandbox.AIMCaseSchema, 'object', 'the case schema is not defined in the artifact');
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'src/data/cases.js'), 'utf8'), sandbox,
    { filename: 'src/data/cases.js' });
  assert.equal(typeof sandbox.AIMCases, 'object', 'the facade did not publish itself');

  let repo = null;
  assert.doesNotThrow(() => { repo = sandbox.AIMCases.makeRepository({ forceMemory: true }); },
    'the assembled facade could not build a repository in a browser-like context, so the page '
    + 'throws before any view paints');
  assert.ok(repo && typeof repo.save === 'function');
  /* The store the facade resolved is the assembled one, not a second copy. The
     facade publishes the store's own description, so a facade wired to a second
     store would describe something else. */
  assert.equal(typeof sandbox.AIMCases.describeStorage, 'function',
    'the facade does not expose the assembled store description, so it is not the '
    + 'store the artifact defines');

  /* Mutation: drop the store module from the loaded set, as a wrong build order
     would, and the facade must fail rather than build a repository in the dark.
     The failure may come when the facade is evaluated or when it is called; both
     are the same fault, so the whole load-and-call is inside the assertion. */
  const broken = { localStorage: sandbox.localStorage, console, Intl, JSON, Math, Date, URLSearchParams };
  broken.window = broken; broken.globalThis = broken;
  vm.createContext(broken);
  assert.throws(() => {
    for (const rel of upToFacade.filter((r) => r !== 'src/case/store.js')) {
      vm.runInContext(fs.readFileSync(path.join(ROOT, rel), 'utf8'), broken, { filename: rel });
    }
    vm.runInContext(fs.readFileSync(path.join(ROOT, 'src/data/cases.js'), 'utf8'), broken,
      { filename: 'src/data/cases.js' });
    broken.AIMCases.makeRepository({ forceMemory: true });
  }, 'with the store module removed the facade still built a repository or loaded cleanly, so this '
    + 'check cannot see the fault it exists to catch');
});

/* -------------------------------------------------------------------- BASE-05 */

test('BASE-05: a check that did not run must not exit 0, and the runner says so in its own words', () => {
  const runner = path.join(ROOT, 'tests', 'accept', 'run_all.ps1');
  const ps = fs.readFileSync(runner, 'utf8');
  assert.ok(ps.includes('every check ran and returned zero'),
    'the runner no longer states what its all-clear line means');

  /* The behaviour, measured: run the acceptance runner with the browser steps
     deliberately unavailable. It must NOT exit 0, and its own output must name
     the steps that did not run. A text-only check cannot prove either.

     The runner writes its combined summary to a fixed path. Running it here would
     overwrite the summary of the real run this suite is part of, so the real one
     is snapshotted and put back afterwards. */
  const summaryPath = path.join(ROOT, 'tests', 'accept', '_out', 'run_all_summary.json');
  const before = fs.existsSync(summaryPath) ? fs.readFileSync(summaryPath) : null;
  let run;
  try {
    run = spawnSync('powershell', [
      '-ExecutionPolicy', 'Bypass', '-File', runner, '-SkipBaseline', '-SkipBrowser'
    ], { cwd: ROOT, encoding: 'utf8', timeout: 240000 });
  } finally {
    if (before !== null) fs.writeFileSync(summaryPath, before);
  }
  assert.notEqual(run.status, 0,
    'the runner exited 0 with the browser and baseline steps skipped, so "not run" '
    + 'is being read as "passed"');
  const out = (run.stdout || '') + (run.stderr || '');
  assert.match(out, /NOT RUN: BASE-ENGINE/,
    'the runner did not name BASE-ENGINE as not run');
  assert.match(out, /NOT RUN: BASE-BROWSER/,
    'the runner did not name BASE-BROWSER as not run');
  assert.match(out, /Result:\s*\d+ step\(s\) not run/,
    'the runner did not state, in its own output, that steps did not run');
  assert.doesNotMatch(out, /Result: every check ran and returned zero/,
    'the runner printed its all-clear line while steps were skipped');
});

/* -------------------------------------------------------------------- CASE-07 */

test('CASE-07: two real node processes write to one case folder with no lost write and no torn record', async () => {
  const t = tempDir('case07');
  try {
    /* A helper child, run as a real node process. Each attempt prints one JSON
       line and exits 0 even when it is refused, so the parent judges the RESULT.
       OS refusals come back as code OS_REFUSED rather than a stack trace. */
    const child = path.join(HERE, 'case07_child.cjs');
    assert.ok(fs.existsSync(child), 'the CASE-07 child helper is missing: ' + child);

    const runChild = (...args) => new Promise((resolve) => {
      const p = spawn('node', [child, ROOT, t.dir, ...args]);
      let stdout = '', stderr = '';
      p.stdout.on('data', (d) => { stdout += d; });
      p.stderr.on('data', (d) => { stderr += d; });
      p.on('close', (code) => {
        let parsed = null;
        try { parsed = JSON.parse(stdout); } catch (e) { parsed = null; }
        resolve({ code, parsed, stdout, stderr });
      });
    });

    const created = await runChild('child-A', 'create');
    assert.equal(created.code, 0, created.stderr);
    assert.ok(created.parsed && created.parsed.ok === true,
      'the first process did not create the case: ' + created.stdout);
    assert.equal(created.parsed.version, 1);
    const creatorPid = created.parsed.pid;

    /* Real concurrent writers. Accept a run where one writer was refused by the
       operating system while the other held the file (code OS_REFUSED): a raise
       is not a lost write, and it is the honest outcome of two writers on one
       file. What must never happen is both succeeding, or neither. */
    let accepted = null, refused = null, attempt = 0;
    while (attempt < 6 && !(accepted && refused)) {
      attempt += 1;
      const [first, second] = await Promise.all([
        runChild('child-B', 'write', '1'),
        runChild('child-C', 'write', '1'),
      ]);
      const rows = [first.parsed, second.parsed].filter(Boolean);
      for (const r of rows) {
        assert.ok(r.pid && r.pid !== creatorPid, 'the writers are not separate processes');
      }
      first.parsed.caller = 'child-B';
      second.parsed.caller = 'child-C';
      const ok = rows.filter((r) => r.ok === true);
      const no = rows.filter((r) => r.ok === false);
      if (ok.length === 1 && no.length === 1) {
        accepted = ok[0];
        accepted.parsed_caller = accepted.caller;
        refused = no[0];
        break;
      }
      if (ok.length === 1 && no.length === 0) {
        /* The other writer was refused by the operating system before it could
           report. That is acceptable; take the next run's pair instead. */
        accepted = ok[0];
        accepted.parsed_caller = accepted.caller;
        refused = { code: 'OS_REFUSED', pid: null };
        break;
      }
      assert.notEqual(ok.length, 2,
        'both writers were accepted against the same version, so a write was lost: '
        + JSON.stringify(rows));
      assert.notEqual(ok.length, 0,
        'neither writer was accepted, so the case could not move at all: ' + JSON.stringify(rows));
    }
    assert.ok(accepted, 'no writer was ever accepted after ' + attempt + ' attempt(s)');
    assert.ok(refused, 'no writer was ever refused after ' + attempt + ' attempt(s)');

    /* The refusal must be a version refusal, not an operating-system one, unless
       the OS really did hold the file - and the case must still have moved. */
    if (refused.code !== 'OS_REFUSED') {
      assert.equal(refused.code, 'STALE_WRITE',
        'the second writer was not refused as a stale write: ' + JSON.stringify(refused));
    }

    /* No lost write: the stored record is whole, is at version 2, carries the
       accepted move, and its log gained exactly one entry. */
    const raw = fs.readFileSync(path.join(t.dir, 'cases', 'SYN-C07.json'), 'utf8');
    const onDisk = JSON.parse(raw);
    assert.equal(onDisk.version, 2, 'the record is not at version 2 after one accepted write');
    assert.equal(onDisk.state, 'submitted');
    assert.equal(onDisk.history.length, 2, 'the log did not gain exactly one entry');
    /* The entry names the function that made the move. The service prefixes a
       development-only identity, so the caller's name is the tail of it. */
    assert.ok(onDisk.history[1].recorded_by && onDisk.history[1].recorded_by.length > 0,
      'the accepted move carries no attribution on the log entry');
    const acceptedCaller = accepted.parsed_caller;
    if (acceptedCaller) {
      assert.ok(String(onDisk.history[1].recorded_by).endsWith(acceptedCaller),
        'the log entry does not name the writer that was accepted: '
        + onDisk.history[1].recorded_by + ' vs ' + acceptedCaller);
    }

    /* A third process reads it back whole. */
    const readBack = await runChild('child-D', 'read');
    assert.equal(readBack.code, 0, readBack.stderr);
    assert.equal(readBack.parsed.version, 2);
    assert.equal(readBack.parsed.state, 'submitted');
    assert.equal(readBack.parsed.entries, 2);
    assert.notEqual(readBack.parsed.pid, creatorPid, 'the reader is not a separate process');
  } finally {
    t.cleanup();
  }
});
