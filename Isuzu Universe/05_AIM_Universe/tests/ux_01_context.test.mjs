#!/usr/bin/env node
/* ===========================================================================
   UX-01 acceptance tests: one context across every working view.

   How to run
     node --test tests/ux_01_context.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-01):
     E1  Review, evidence, financial test and case show the same context after
         forward/back navigation. The four views are the shipped tabs
         "Sales evidence" (decision), "Price position" (position), "Price &
         profit test" (economics) and "Internal action" (action, where the case
         is saved).
     E2  A national Portuguese review never inherits an ITUK dealer selector or
         fleet denominator.

   The shipped layer, src/ui/app.js, is loaded the way tests/ux_flow.test.mjs
   loads it: one <script> block run in a vm sandbox with a stub document and a
   stub address. Data: tests/fixtures/ux_01_two_markets.json, invented values
   only. The restricted payload is never read here.
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

const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_01_two_markets.json'), 'utf8'));
const ITUK = 'SYNTH-ITUK-DEALER';
const PT = 'SYNTH-PT-NATIONAL';

/* ------------------------------------------------------------- fake browser -- */
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

function loadApp() {
  const storage = makeStorage();
  const doc = makeFakeDocument();
  const sandbox = {
    __payload: JSON.parse(JSON.stringify(FX)),
    __dom: { $: (sel) => doc.querySelector(sel), $$: (sel) => doc.querySelectorAll(sel) },
    document: doc, localStorage: storage, location: { hash: '' },
    URLSearchParams, Intl, JSON, Math, Date, console,
    setTimeout: (fn) => { fn(); return 0; }, clearTimeout,
    Blob: class { constructor(parts) { sandbox.__blob = parts; } },
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
  return { api, doc, sandbox, history: [] };
}

/* A real browser fires hashchange when the address changes; the stub does not.
   Addresses carry the leading '#' a browser reports, because app.js compares
   location.hash.slice(1) with the address it would write. */
function settle(s) {
  const want = s.sandbox.location.hash;
  if (s._lastHash === want) return;
  s._lastHash = want;
  const fn = s.sandbox._listeners.hashchange;
  if (fn) fn();
}

/* Forward navigation pushes an address; back pops to the previous one, exactly as
   the browser's own history would. */
function forward(s, caseId, view) {
  const hash = new URLSearchParams({ case: caseId, view, compare: 'half' }).toString();
  s.history.push('#' + hash);
  s.sandbox.location.hash = '#' + hash;
  settle(s);
  return s.doc.nodes.content.innerHTML;
}
function back(s) {
  s.history.pop();
  s.sandbox.location.hash = s.history[s.history.length - 1];
  settle(s);
  return s.doc.nodes.content.innerHTML;
}

const contextAttr = (html) => (/data-context="([^"]*)"/.exec(html) || [])[1] || null;
const unescape = (v) => String(v).replace(/&quot;/g, '"').replace(/&#39;/g, "'")
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');

test('UX-01 E1: review, evidence, financial test and case show the same context after forward and back navigation', () => {
  const s = loadApp();
  const caseRec = FX.cases.find((c) => c.id === ITUK);
  const expected = scenarioModule.contextFor(FX, caseRec, { compare: 'half' });
  const key = scenarioModule.contextKey(expected);
  assert.equal(expected.original_part, caseRec.pn);
  assert.equal(expected.family, caseRec.category);
  assert.equal(expected.distributor, 'ITUK');
  assert.equal(expected.source_version, FX.meta.version);
  assert.equal(expected.period, caseRec.comparisons.half.label);

  const VIEWS = ['decision', 'position', 'economics', 'action'];
  const seen = [];
  const check = (html, view, step) => {
    assert.doesNotMatch(html, /data-failed-view="/, `${view} refused to paint on ${step}`);
    const attr = contextAttr(html);
    assert.ok(attr, `${view} carries no context strip on ${step}`);
    assert.equal(unescape(attr), key, `${view} shows a different context on ${step}`);
    assert.deepEqual(JSON.parse(JSON.stringify(s.api.getContext())), JSON.parse(JSON.stringify(expected)),
      `the published context moved on ${view} (${step})`);
    seen.push(view + ':' + step);
  };

  VIEWS.forEach((v) => check(forward(s, ITUK, v), v, 'forward'));
  /* Leave for another case, then come back with the browser's back button. */
  forward(s, PT, 'decision');
  check(back(s), 'action', 'back from another case');
  for (let i = VIEWS.length - 2; i >= 0; i--) check(back(s), VIEWS[i], 'back');
  assert.equal(seen.length, 8);
});

test('UX-01 E2: a national Portuguese review never inherits an ITUK dealer selector or fleet denominator', () => {
  const s = loadApp();
  forward(s, ITUK, 'decision');
  s.api.go({ dealer: 'SYNTH-DEALER-1' });
  settle(s);
  const itukCtx = s.api.getContext();
  /* Control: on the ITUK dealer case the selector and the fleet are present, so
     their absence below is a property of the Portuguese review. */
  assert.equal(itukCtx.scope, 'dealer');
  assert.deepEqual([...itukCtx.dealer_selector], ['SYNTH-DEALER-1', 'SYNTH-DEALER-2']);
  assert.equal(itukCtx.selected_dealer, 'SYNTH-DEALER-1');
  assert.equal(itukCtx.fleet_denominator.value, 4321);
  assert.match(s.doc.nodes['scope-strip'].innerHTML, /SYNTH-DEALER-1/);

  s.api.openCase(PT);
  settle(s);
  ['decision', 'position', 'economics', 'action'].forEach((view) => {
    const html = forward(s, PT, view);
    const ctx = s.api.getContext();
    assert.equal(ctx.case_id, PT);
    assert.equal(ctx.country, 'Portugal');
    assert.equal(ctx.scope, 'national', `${view}: the Portuguese review is not national`);
    assert.equal(ctx.dealer_selector, null, `${view}: an ITUK dealer selector was inherited`);
    assert.equal(ctx.selected_dealer, null, `${view}: an ITUK dealer selection was inherited`);
    assert.equal(ctx.fleet_denominator, null, `${view}: an ITUK fleet denominator was inherited`);
    const strip = s.doc.nodes['scope-strip'].innerHTML;
    [html, strip].forEach((text) => {
      assert.doesNotMatch(text, /SYNTH-DEALER/, `${view}: a dealer name leaked into the Portuguese review`);
      assert.doesNotMatch(text, /4,321|4321/, `${view}: the ITUK fleet leaked into the Portuguese review`);
    });
  });
  /* The dealer selection is private working state; it is not written into the
     shareable address. */
  assert.doesNotMatch(s.sandbox.location.hash, /dealer/i);
});