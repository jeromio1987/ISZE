#!/usr/bin/env node
/* ===========================================================================
   UX-04 acceptance tests: visualise revenue, profit and break-even without a
   forecast claim.

   How to run
     node --test tests/ux_04_sensitivity.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-04):
     E1  Each plotted point matches the calculation for its stated synthetic or
         user-supplied assumptions.
     E2  Missing costs suppress only profit-based output; revenue and the reason
         for the narrower view remain usable.

   src/ui/app.js is loaded with the ux_04 harness copied from
   tests/ux_02_alternative.test.mjs. Two synthetic fixtures are used:
     tests/fixtures/ux_04_sensitivity.json          - a cost is held
     tests/fixtures/ux_04_no_cost.json              - no cost is held
   The restricted payload is never read.

   The control under test is window.AIMPricing.sensitivity(): a grid of points,
   each one an engine.calculate() call with the inputs it states. The test
   recomputes each point with the engine and requires the two to agree.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
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
const APP = path.join(ROOT, 'src/ui/app.js');
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_04_sensitivity.json'), 'utf8'));
const FX_NO_COST = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_04_no_cost.json'), 'utf8'));

/* ---------------------------------------------- harness, as in ux_02 -- */
function stubElement(id) {
  const listeners = {};
  const attrs = {};
  return {
    id, innerHTML: '', value: '', textContent: '', dataset: {},
    _listeners: listeners, _attrs: attrs,
    onclick: null, onchange: null,
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    removeEventListener() {}, focus() {}, setSelectionRange() {},
    append() {}, remove() {}, click() {},
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute(k, v) { attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    querySelectorAll() { return []; }
  };
}

const DOM_IDS = ['content', 'case-list', 'case-header', 'scope-strip', 'pack-status', 'tabs',
  'market', 'render-status', 'close-modal', 'candidate-search', 'export-review'];

function makeFakeDocument() {
  const nodes = {};
  const derived = {};
  let signature = null;
  DOM_IDS.forEach((id) => { nodes[id] = stubElement(id); });
  const contentHtml = () => nodes.content.innerHTML;

  function scan(selector) {
    const byId = /^#([\w-]+)$/.exec(selector);
    if (byId) return [nodes[byId[1]] || (nodes[byId[1]] = stubElement(byId[1]))];
    const html = contentHtml() || '';
    if (signature !== html) { signature = html; Object.keys(derived).forEach((k) => delete derived[k]); }
    const attr = /^\[data-([a-z-]+)(?:="([^"]*)")?\]$/.exec(selector);
    if (!attr) return [];
    const camel = attr[1].replace(/-([a-z])/g, (_m, ch) => ch.toUpperCase());
    const out = [];
    const re = new RegExp('data-' + attr[1] + '(="([^"]*)")?', 'g');
    let m;
    while ((m = re.exec(html))) {
      const tagStart = html.lastIndexOf('<', m.index);
      const tagEnd = html.indexOf('>', m.index);
      const tag = html.slice(tagStart, tagEnd + 1);
      const tagId = (/id="([^"]+)"/.exec(tag) || [])[1] || null;
      const key = tagId ? '#id:' + tagId : selector + '|' + out.length;
      if (!derived[key]) { derived[key] = stubElement(tagId || selector); derived[key].dataset = {}; }
      derived[key].dataset[camel] = m[2] === undefined ? '' : m[2];
      if (tagId) nodes[tagId] = derived[key];
      out.push(derived[key]);
    }
    return out;
  }

  function elementForId(id) {
    if (nodes[id]) return nodes[id];
    return (nodes[id] = nodes[id] || stubElement(id));
  }

  return {
    nodes, scan,
    body: { append() {} },
    createElement: (tag) => stubElement(tag),
    getElementById: (id) => elementForId(id),
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
    clear: () => { Object.keys(data).forEach((k) => delete data[k]); },
    _data: data
  };
}

function appSource() {
  const raw = fs.readFileSync(APP, 'utf8').trim().replace(/\r\n/g, '\n');
  const block = /^<script>([\s\S]*)<\/script>$/.exec(raw);
  assert.ok(block, 'src/ui/app.js is no longer a single <script> block');
  let src = block[1];
  const once = (needle, replacement, what) => {
    const count = src.split(needle).length - 1;
    assert.equal(count, 1,
      `expected exactly one ${what} in src/ui/app.js; found ${count}. `
      + 'This test rewrites that statement, so it must be updated with app.js.');
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

function fire(el, type, init) {
  assert.ok(el, `nothing to fire "${type}" on`);
  const list = el._listeners[type] || [];
  const direct = type === 'click' ? el.onclick : type === 'change' ? el.onchange : null;
  const event = Object.assign({ key: '', preventDefault() {} }, init || {});
  list.forEach((fn) => fn(event));
  if (direct) direct.call(el, event);
}

function loadApp(payload) {
  const storage = makeStorage();
  globalThis.localStorage = storage;
  const doc = makeFakeDocument();
  const sandbox = {
    __payload: JSON.parse(JSON.stringify(payload)),
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
  engine.setPayload(sandbox.__payload);
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

function go(session, caseId, view) {
  session.sandbox.location.hash = '#' + new URLSearchParams({ case: caseId, view, compare: 'half' }).toString();
  settle(session);
  return session.doc.nodes.content.innerHTML;
}

const CASE = FX.cases[0].id;
const CASE_NO_COST = FX_NO_COST.cases[0].id;

/* Recompute a sensitivity point from the inputs it states, with the same engine
   and the same payload the application used. */
function recompute(payload, point) {
  const input = Object.assign({}, point.input);
  return engine.calculate(input, { payload: payload });
}

test('UX-04 E1: each plotted point matches the calculation for its stated assumptions', () => {
  const s = loadApp(FX);
  go(s, CASE, 'economics');
  /* A user-supplied assumption: enter a parts cost so both measures are
     produced, then require every point to match that stated input. */
  const cost = s.doc.getElementById('s-cost');
  cost.value = '2';
  fire(cost, 'input');
  const sens = s.api.sensitivity();

  const all = sens.price_points.concat(sens.volume_points);
  assert.ok(all.length >= 4, 'the sensitivity view has no points');
  assert.equal(sens.engine_entry_point, 'engine.calculate',
    'the points are not attributed to the one engine');

  /* Every point is the engine's own result for the inputs it states. */
  all.forEach((p) => {
    const r = recompute(FX, p);
    assert.equal(p.ok, r.ok, `point ${p.label}: ok does not match the engine`);
    if (!r.ok) return;
    assert.equal(p.revenue_change, r.revenue_change,
      `point ${p.label}: revenue change does not match the engine`);
    assert.equal(p.gp_change, r.gp_change,
      `point ${p.label}: gross-profit change does not match the engine`);
  });

  /* The zero step is the working record, so it matches the view's own result. */
  const zero = sens.price_points.find((p) => p.label.indexOf('0%') === 0);
  assert.ok(zero, 'no zero-step point');
  const live = s.api.getResult();
  assert.equal(zero.revenue_change, live.revenue_change,
    'the zero-step point does not equal the working scenario result');

  /* The baseline is the unchanged offer, not the proposal. */
  assert.equal(sens.baseline.revenue_change, 0,
    'the unchanged offer does not report a zero revenue change');

  /* No forecast claim is present on the view. */
  assert.match(sens.no_forecast, /no elasticity/i);
  assert.match(sens.no_forecast, /no best-price prediction/i);

  /* The numeric table is on the painted page, so the chart is not the only
     carrier of the numbers. */
  const html = go(s, CASE, 'economics');
  assert.match(html, /data-sens="/, 'the sensitivity table is not on the page');
  assert.match(html, /Sensitivity to the proposed price/i);
});

test('UX-04 E2: a missing cost suppresses only profit, and revenue and the reason stay usable', () => {
  const s = loadApp(FX_NO_COST);
  go(s, CASE_NO_COST, 'economics');
  const sens = s.api.sensitivity();
  const all = sens.price_points.concat(sens.volume_points);

  assert.equal(sens.missing_cost, true, 'the fixture is meant to have no cost');
  assert.equal(sens.profit_suppressed, true, 'suppressed profit is not reported');
  assert.match(sens.statement, /suppressed/i);

  all.forEach((p) => {
    assert.equal(p.gp_change, null, `point ${p.label}: a profit figure was produced with no cost`);
    assert.equal(p.profit_state, 'suppressed', `point ${p.label}: profit is not marked suppressed`);
    assert.match(p.profit_reason, /not a cost of zero/i,
      `point ${p.label}: the reason for the narrower view is not stated`);
    if (p.ok) {
      assert.notEqual(p.revenue_change, null,
        `point ${p.label}: revenue was suppressed along with profit`);
    }
  });

  /* The reason reaches the reader, not just the API. */
  const html = go(s, CASE, 'economics');
  assert.match(html, /data-profit-state="suppressed"/,
    'the painted view does not mark the suppressed profit points');
  assert.match(html, /No parts purchase cost is applied/i,
    'the painted view does not state why profit is not shown');
});
