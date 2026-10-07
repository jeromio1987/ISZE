#!/usr/bin/env node
/* ===========================================================================
   Audit fix H (U27): one named test for each task that was marked
   "technically verified" while no test line named it.

   How to run
     node --test tests/audit_h_named_tasks.test.mjs

   Synthetic inputs only. BASE-01 is not here: its claim is a checksum of the
   frozen v03 file, which this brief keeps closed. It is left below
   "technically verified" in progress.json and the reason is recorded there.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

const contracts = require(path.join(ROOT, 'src/data/contracts.js'));
const engine = require(path.join(ROOT, 'src/engine/engine.js'));
const caseModule = require(path.join(ROOT, 'src/data/cases.js'));
const candidateModule = require(path.join(ROOT, 'src/data/candidates.js'));
const scenarioModule = require(path.join(ROOT, 'src/data/scenario.js'));
const exportModule = require(path.join(ROOT, 'src/data/export.js'));
const comparableModule = require(path.join(ROOT, 'src/data/comparable.js'));
const store = require(path.join(ROOT, 'src/case/store.js'));
const ops = require(path.join(ROOT, 'src/data/ops_measurements.js'));
const APP = path.join(ROOT, 'src/ui/app.js');
engine.setPayload(JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'synthetic_payload.json'), 'utf8')));

const BASE = { price_before: 100, price_after: 80, quantity_before: 100, quantity_after: null,
  cost_eur: 60, support_eur: 200, scope: 'all', quantity_label: 'manual scenario', pack_size: 1 };
const RESTRICTED_KEYS = ['cost_eur', 'cost', 'margin', 'margin_pct', 'gross_profit', 'gp_before', 'gp_after',
  'gp_change', 'margin_after_pct', 'margin_before_pct', 'unit_cost'];
function restrictedPaths(v, p = []) {
  if (Array.isArray(v)) return v.flatMap((x, i) => restrictedPaths(x, p.concat(String(i))));
  if (v && typeof v === 'object') {
    return Object.keys(v).flatMap((k) => (RESTRICTED_KEYS.includes(k) ? [p.concat(k).join('.')] : [])
      .concat(restrictedPaths(v[k], p.concat(k))));
  }
  return [];
}
const CASE = { case_id: 'SYN-H', customer: 'Synthetic H', market: 'SYN', part_number: 'SYN-PN-H', unit: 'unit',
  description: 'Synthetic part', title: 'Synthetic offer', version: 1, state: 'draft', owner_role: 'case_owner' };
const SCEN = { ...BASE, case_id: 'SYN-H', part_number: 'SYN-PN-H', unit: 'unit', version: 1, scenario_id: 'SYN-H:v1' };

function stubElement(id) {
  const listeners = {};
  const attrs = {};
  return {
    id, innerHTML: '', value: '', textContent: '', dataset: {},
    _listeners: listeners, _attrs: attrs, onclick: null, onchange: null,
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    removeEventListener() {}, focus() {}, setSelectionRange() {},
    append() {}, remove() {}, click() {},
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute(k, v) { attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    querySelectorAll() { return []; }
  };
}

function makeFakeDocument() {
  const nodes = {};
  ['content', 'case-list', 'case-header', 'scope-strip', 'pack-status', 'tabs', 'market',
    'render-status', 'close-modal', 'candidate-search', 'export-review'].forEach((id) => {
    nodes[id] = stubElement(id);
  });
  function scan(selector) {
    const byId = /^#([\w-]+)$/.exec(selector);
    if (byId) return [nodes[byId[1]] || (nodes[byId[1]] = stubElement(byId[1]))];
    return [];
  }
  return {
    nodes, scan,
    body: { append() {} },
    createElement: (tag) => stubElement(tag),
    getElementById: (id) => (nodes[id] = nodes[id] || stubElement(id)),
    querySelector: (sel) => scan(sel)[0],
    querySelectorAll: (sel) => scan(sel)
  };
}

function makeStorage() {
  const data = {};
  return {
    getItem: (k) => (Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; },
    clear: () => { Object.keys(data).forEach((k) => delete data[k]); }
  };
}

function appSource() {
  const raw = fs.readFileSync(APP, 'utf8').trim().replace(/\r\n/g, '\n');
  const block = /^<script>([\s\S]*)<\/script>$/.exec(raw);
  assert.ok(block, 'src/ui/app.js is no longer a single <script> block');
  let src = block[1];
  const once = (needle, replacement, what) => {
    const count = src.split(needle).length - 1;
    assert.equal(count, 1, `expected exactly one ${what} in src/ui/app.js; found ${count}`);
    src = src.replace(needle, () => replacement);
  };
  once("const D=JSON.parse(document.getElementById('case-data').textContent);",
    'const D=__payload;', 'payload read');
  once("const repo=K.makeRepository({\n  forceMemory: !(function(){try{root.localStorage.setItem('__t','1');root.localStorage.removeItem('__t');return true;}catch(e){return false;}})()\n});",
    'const repo=K.makeRepository({forceMemory:true});', 'case repository construction');
  once("const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];",
    'const $=__dom.$, $$=__dom.$$;', 'document lookup helpers');
  return src;
}

function loadApp(fx) {
  const storage = makeStorage();
  const doc = makeFakeDocument();
  const sandbox = {
    __payload: JSON.parse(JSON.stringify(fx)),
    __dom: { $: (sel) => doc.querySelector(sel), $$: (sel) => doc.querySelectorAll(sel) },
    document: doc, localStorage: storage, location: { hash: '' },
    URLSearchParams, Intl, JSON, Math, Date, console,
    setTimeout: (fn) => { fn(); return 0; }, clearTimeout,
    Blob: class { constructor(parts) { sandbox.__blob = parts; } },
    __blobText: () => String((sandbox.__blob || [''])[0]),
    URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
    AIMEngine: engine, AIMExport: exportModule, AIMCandidates: candidateModule,
    AIMCases: caseModule, AIMContracts: contracts, AIMScenario: scenarioModule,
    AIMComparable: comparableModule
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  sandbox._listeners = {};
  sandbox.addEventListener = (name, fn) => { sandbox._listeners[name] = fn; };
  sandbox.removeEventListener = (name) => { delete sandbox._listeners[name]; };
  vm.createContext(sandbox);
  vm.runInContext(appSource(), sandbox, { filename: APP, timeout: 30000 });
  const api = sandbox.window.AIMPricing;
  assert.ok(api, 'src/ui/app.js did not publish window.AIMPricing');
  return { api, doc, sandbox };
}

function settle(session) {
  const want = session.sandbox.location.hash;
  if (session._lastHash === want) return;
  session._lastHash = want;
  const fn = session.sandbox._listeners.hashchange;
  if (fn) fn();
}

function openCase(session, caseId, view, compare) {
  const hash = new URLSearchParams({ case: caseId, view, compare }).toString();
  session.sandbox.location.hash = '#' + hash;
  settle(session);
}



/* ------------------------------------------------------------------ FIN -- */

test('FIN-01: invalid proposed prices are refused, and a zero cost is not an unknown cost', () => {
  for (const bad of ['abc', -5, Infinity, NaN, '']) {
    const r = engine.calculate({ ...BASE, price_after: bad });
    assert.equal(r.ok, false, 'price_after ' + String(bad) + ' was accepted');
  }
  const zero = engine.calculate({ ...BASE, cost_eur: 0 });
  const unknown = engine.calculate({ ...BASE, cost_eur: null });
  assert.equal(zero.ok, true);
  assert.equal(zero.gp_after, 100 * 80 - 200, 'a zero cost is a known cost');
  assert.equal(unknown.ok, true);
  assert.equal(unknown.gp_after, null, 'an unknown cost is not calculated as zero');
});

test('FIN-05: break-even quantities follow the eligibility rule', () => {
  /* 100 units at EUR 100, cost 60, cut to 80, support 200.
     All volume: revenue 10000/80 = 125; profit (4000+200)/(80-60) = 210.
     Incremental only: existing units hold revenue (100); profit 100 + 200/20 = 110. */
  const all = engine.calculate({ ...BASE, scope: 'all' });
  const inc = engine.calculate({ ...BASE, scope: 'incremental' });
  assert.equal(all.qty_preserve_revenue, 125);
  assert.equal(all.qty_preserve_gp, 210);
  assert.equal(inc.qty_preserve_revenue, 100);
  assert.equal(inc.qty_preserve_gp, 110);
  const noSupport = engine.calculate({ ...BASE, support_eur: 0, scope: 'all' });
  assert.equal(noSupport.qty_preserve_gp, 200);
  const rise = engine.calculate({ ...BASE, price_after: 125, support_eur: 0, scope: 'all' });
  assert.equal(rise.qty_preserve_revenue, 80, 'on a rise the figure is a volume floor');
  assert.match(rise.qty_preserve_revenue_label, /volume floor/);
});

/* ----------------------------------------------------------------- CASE -- */

test('CASE-07: two writers on the same case folder; the stale one is refused', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-h-case07-'));
  const a = store.makeCaseService({ adapter: store.makeFileAdapter({ dir }) });
  const b = store.makeCaseService({ adapter: store.makeFileAdapter({ dir }) });
  const made = a.create({ case_id: 'SYN-H-07', part_number: 'SYN-PN', customer: 'Synthetic', by: 'writer-a' });
  assert.equal(made.ok, true);
  const seenByA = a.load('SYN-H-07');
  const seenByB = b.load('SYN-H-07');
  assert.equal(seenByA.version, seenByB.version);
  const first = a.saveRecord({ ...seenByA, customer: 'writer A' }, { by: 'writer-a', expected_version: seenByA.version });
  assert.equal(first.ok, true, first.error);
  const second = b.saveRecord({ ...seenByB, customer: 'writer B' }, { by: 'writer-b', expected_version: seenByB.version });
  assert.equal(second.ok, false);
  assert.equal(second.code, 'STALE_WRITE');
  assert.equal(second.actual_version, first.record.version);
  assert.equal(b.load('SYN-H-07').customer, 'writer A', 'the loser did not overwrite the winner');
  fs.rmSync(dir, { recursive: true, force: true });
});

/* ----------------------------------------------------------------- SAFE -- */

test('SAFE-03: no restricted field reaches the participant brief or an operations log', () => {
  const r = engine.calculate(BASE);
  const member = exportModule.memberBrief(CASE, SCEN, r, {});
  assert.equal(member.recipient, 'member');
  assert.deepEqual(restrictedPaths(member.payload), []);
  assert.equal(JSON.stringify(member.payload).includes(String(r.gp_after)), false, 'the gross profit figure is absent');
  const internal = exportModule.internalRecord(CASE, SCEN, r, { exported_at: null });
  assert.ok(restrictedPaths(internal.payload).length > 0, 'control: the internal record does carry them');
  const row = ops.makeOpsRecorder({ now: () => 1 }).recordFailure({ context: { nested: { cost_eur: 60, margin: 0.4 } } });
  assert.deepEqual(ops.findConfidential(row), []);
});

test('SAFE-04: both outputs in one run; the internal one is refused as a participant document', () => {
  const r = engine.calculate(BASE);
  const member = exportModule.memberBrief(CASE, SCEN, r, {});
  const internal = exportModule.internalRecord(CASE, SCEN, r, { exported_at: null });
  assert.equal(member.recipient, 'member');
  assert.equal(internal.recipient, 'internal');
  assert.equal(exportModule.assertInternalOnly(member).ok, true);
  const refused = exportModule.assertInternalOnly(internal);
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'INTERNAL_ONLY');
});

/* --------------------------------------------------------------- REVIEW -- */

test('REVIEW-01: search and paging reach the whole set, beyond the first 300 rows', () => {
  const rows = Array.from({ length: 1234 }, (_, i) => ({
    distributor: 'SYN-DB-' + (i % 7), part_number: 'SYN-PN-' + String(i).padStart(5, '0'),
    description: i === 1201 ? 'synthetic needle part' : 'synthetic part', selection_reasons: '',
    unresolved_inputs: '', competitor_evidence: '' }));
  const hit = candidateModule.search(rows, 'needle');
  assert.equal(hit.length, 1);
  assert.equal(hit[0].part_number, 'SYN-PN-01201');
  const last = candidateModule.page(rows, 999, 50);
  assert.equal(last.total, 1234);
  assert.equal(last.page_count, 25);
  assert.equal(last.page, 25);
  assert.equal(last.first_row, 1201);
  assert.equal(last.last_row, 1234);
  assert.equal(last.rows[last.rows.length - 1].part_number, 'SYN-PN-01233');
});

/* ----------------------------------------------------------------- BASE -- */

test('BASE-02: restricted inputs, built pages and test output are kept out of version control', () => {
  for (const rel of ['payload/any_payload.json', 'dist/ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html',
    'tests/accept/_out/any.json']) {
    const r = spawnSync('git', ['check-ignore', '-q', rel], { cwd: ROOT });
    assert.equal(r.status, 0, rel + ' is not ignored by git');
  }
  const src = spawnSync('git', ['check-ignore', '-q', 'src/engine/engine.js'], { cwd: ROOT });
  assert.equal(src.status, 1, 'control: source is tracked');
});

test('BASE-03: one small set of shared records, versioned', () => {
  assert.equal(contracts.CONTRACT_VERSION, 4);
  const member = exportModule.memberBrief(CASE, SCEN, engine.calculate(BASE), {});
  assert.equal(member.payload.contract_version, contracts.CONTRACT_VERSION, 'exports carry the shared version');
  assert.ok(Object.keys(contracts.SECTION_FIELDS || {}).length > 0, 'sections declare their contents');
  for (const name of ['SCENARIO_FIELDS', 'RESULT_FIELDS', 'EVIDENCE_FIELDS', 'CASE_FIELDS']) {
    assert.ok(Array.isArray(contracts[name]) && contracts[name].length > 0, name);
  }
});

test('BASE-04: the build assembles the case pair before the case facade that reads it', () => {
  const build = fs.readFileSync(path.join(ROOT, 'tools', 'build.py'), 'utf8');
  const shipped = build.slice(0, build.indexOf('UNWIRED_MODULES'));
  const order = [...shipped.matchAll(/\("(src\/[^"]+)",/g)].map((m) => m[1]);
  for (const m of ['src/case/schema.js', 'src/case/store.js', 'src/data/cases.js', 'src/ui/app.js']) {
    assert.ok(order.includes(m), m + ' is not assembled');
  }
  assert.ok(order.indexOf('src/case/store.js') < order.indexOf('src/data/cases.js'));
  assert.equal(order[order.length - 1], 'src/ui/app.js', 'the app is assembled last');
});

test('BASE-05: the runner states that exit 0 is not acceptance and records file checksums', () => {
  const ps = fs.readFileSync(path.join(HERE, 'accept', 'run_all.ps1'), 'utf8');
  assert.match(ps, /That is not an acceptance/);
  assert.match(ps, /Get-FileHash -Algorithm SHA256/);
});

test('BASE-06: a view that throws paints a named failure, not stale or blank content', () => {
  const fx = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_03_five_cases.json'), 'utf8'));
  const session = loadApp(fx);
  const target = fx.cases[0];
  openCase(session, target.id, 'decision', 'half');
  const before = session.doc.nodes.content.innerHTML;
  assert.ok(before.length > 0, 'control: the decision view paints');
  delete session.api.data.cases.find((c) => c.id === target.id).packEvidence;
  openCase(session, target.id, 'position', 'half');
  const after = session.doc.nodes.content.innerHTML;
  assert.notEqual(after, before, 'the previous view was left on screen');
  assert.match(after, /data-failed-view="position"/);
  assert.match(after, /did not render/);
  assert.equal(/NaN/.test(after), false);
});

test('BASE-07: the synthetic build is repeatable from one command', () => {
  const run = () => spawnSync('python', [path.join(ROOT, 'tools', 'build.py')], { cwd: ROOT, encoding: 'utf8' });
  const one = run();
  assert.equal(one.status, 0, one.stderr || one.stdout);
  const hash1 = /sha256\s*:\s*([0-9a-f]{64})/.exec(one.stdout);
  const two = run();
  const hash2 = /sha256\s*:\s*([0-9a-f]{64})/.exec(two.stdout);
  assert.ok(hash1 && hash2, 'the builder prints the artifact checksum');
  assert.equal(hash1[1], hash2[1], 'two builds of the same source give the same bytes');
  assert.match(one.stdout, /SYNTHETIC/);
});

test('BASE-08: the progress record is single, machine-capped, and every verified task is named by a test', () => {
  const rec = JSON.parse(fs.readFileSync(path.join(ROOT, 'progress', 'progress.json'), 'utf8'));
  assert.equal(rec.tasks.length, 96);
  assert.equal(rec.tasks.some((t) => t.state === 'human accepted'), false, 'a machine never writes human accepted');
  const named = rec.tested_by || {};
  for (const t of rec.tasks.filter((x) => x.state === 'technically verified')) {
    assert.ok((named[t.id] || []).length > 0, t.id + ' is verified with no test line naming it');
  }
});
