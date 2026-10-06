#!/usr/bin/env node
/* ===========================================================================
   REVIEW-07 acceptance tests: turn each question into the appropriate next
   action.

   How to run
     node --test tests/review_07_next_action.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (REVIEW-07):
     E1  A supply explanation never produces a discount.
     E2  An unresolved price comparison still allows a scoped application or
         purchasing review.

   Pattern: tests/ux_05_summary.test.mjs (app harness) plus the evidence module.
   Data: tests/fixtures/review_07_next_action.json (invented values only).
   The restricted payload is never read here.
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
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));
const APP = path.join(ROOT, 'src/ui/app.js');

const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_07_next_action.json'), 'utf8'));

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
    URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
    AIMEngine: engine, AIMExport: exportModule, AIMCandidates: candidateModule,
    AIMCases: caseModule, AIMContracts: contracts, AIMScenario: scenarioModule,
    AIMComparable: comparableModule, AIMEvidence: evidence
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

function fireLatest(el, type) {
  const list = (el && el._listeners && el._listeners[type]) || [];
  const fn = list.length ? list[list.length - 1] : (type === 'click' ? el.onclick : el.onchange);
  if (typeof fn === 'function') fn({ preventDefault() {}, target: el, currentTarget: el });
}

function selectCase(session, caseId) {
  session.sandbox.location.hash = '#case/' + caseId + '/decision';
  const hashFn = session.sandbox._listeners.hashchange;
  if (typeof hashFn === 'function') hashFn();
  else if (session.api && typeof session.api.showCase === 'function') session.api.showCase(caseId);
  return session.doc.getElementById('content').innerHTML || '';
}

function routeIds(plan) {
  return (plan.routes || []).map((r) => r.id);
}

function routeText(plan) {
  return (plan.routes || []).map((r) => [r.id, r.label, r.why, r.kind].join(' ')).join('\n').toLowerCase();
}

test('REVIEW-07 E1: a supply explanation never produces a discount', () => {
  assert.equal(typeof evidence.nextActionPlan, 'function',
    'AIMEvidence.nextActionPlan is missing');

  const supply = FX.unit_cases.find((c) => c.id === 'REVIEW07-SUPPLY');
  const plan = evidence.nextActionPlan(supply);
  assert.ok(plan, 'nextActionPlan returned nothing');
  const ids = routeIds(plan);
  assert.ok(ids.includes('supply_timing_check'), 'supply/timing check route missing');
  assert.ok(ids.includes('evidence_request') || ids.includes('justified_no_action') || ids.includes('price_assessment')
    || ids.includes('bvp_application_check'),
    'no additional legitimate route alongside supply');
  assert.equal(ids.includes('discount'), false, 'a discount route was produced from a supply explanation');
  assert.equal(ids.includes('automatic_discount'), false, 'an automatic discount route was produced');
  const text = routeText(plan);
  assert.doesNotMatch(text, /\bdiscount\b/, 'route text mentions a discount for a supply explanation');
  assert.ok((plan.competing_explanations || []).length >= 1
    || (plan.unknown || []).length >= 1
    || (supply.reviewExplanations || []).some((e) => e.status === 'unknown'),
    'competing explanations / unknown were dropped');
  /* Family decline without linked evidence must not become a precise reason. */
  const family = FX.unit_cases.find((c) => c.id === 'REVIEW07-FAMILY');
  const famPlan = evidence.nextActionPlan(family);
  assert.equal(famPlan.precise_family_decline, null,
    'a family decline without linked evidence was given a precise reason');
  assert.ok((famPlan.unknown || []).length >= 1 || (famPlan.routes || []).some((r) => r.id === 'evidence_request'),
    'unknown / evidence request missing when family decline lacks evidence');

  /* Paint path: supply case under ITUK-PADS must not show a discount recommendation. */
  const payload = { meta: FX.meta || {}, cases: FX.app_cases, offers: [], sources: [], alternatives: [] };
  const session = loadApp(payload);
  assert.equal(typeof session.api.getNextActionPlan, 'function',
    'AIMPricing.getNextActionPlan is missing');
  session.api.getNextActionPlan(); /* warm */
  const html = selectCase(session, 'ITUK-PADS').toLowerCase();
  assert.match(html, /data-next-action-plan|supply|timing/,
    'next-action panel did not paint for the supply case');
  assert.doesNotMatch(html, /automatic discount|grant a discount|discount route/,
    'painted supply case offers a discount');
});

test('REVIEW-07 E2: an unresolved price comparison still allows a scoped application or purchasing review', () => {
  assert.equal(typeof evidence.nextActionPlan, 'function',
    'AIMEvidence.nextActionPlan is missing');

  const price = FX.unit_cases.find((c) => c.id === 'REVIEW07-PRICE');
  const plan = evidence.nextActionPlan(price);
  assert.ok(plan, 'nextActionPlan returned nothing');
  const ids = routeIds(plan);
  assert.ok(ids.includes('price_assessment'), 'price assessment route missing while price is unresolved');
  const hasScoped = ids.includes('bvp_application_check') || ids.includes('purchasing_review');
  assert.ok(hasScoped,
    'unresolved price comparison blocked scoped application / purchasing review');
  const scoped = (plan.routes || []).find((r) =>
    r.id === 'bvp_application_check' || r.id === 'purchasing_review');
  assert.ok(scoped && scoped.why && /relevant|because|application|purchasing|fitment|catalogue/i.test(scoped.why),
    'scoped route does not say why it is relevant');
  assert.ok((plan.competing_explanations || []).length >= 1
    || (price.reviewExplanations || []).some((e) => e.status === 'competing' || e.status === 'unresolved'),
    'competing / unresolved explanations were dropped');

  const payload = { meta: FX.meta || {}, cases: FX.app_cases, offers: [], sources: [], alternatives: [] };
  const session = loadApp(payload);
  const painted = session.api.getNextActionPlan('ITUK-TURBO');
  assert.ok(painted, 'getNextActionPlan returned nothing for the turbo case');
  const pIds = routeIds(painted);
  assert.ok(pIds.includes('price_assessment'), 'API price assessment missing');
  assert.ok(pIds.includes('bvp_application_check') || pIds.includes('purchasing_review'),
    'API scoped application/purchasing review missing');
  const html = selectCase(session, 'ITUK-TURBO').toLowerCase();
  assert.match(html, /data-next-action-plan/, 'next-action panel missing on unresolved price case');
  assert.match(html, /application|purchasing review|bvp/,
    'painted unresolved-price case omits scoped application or purchasing review');
  assert.doesNotMatch(html, /proven lost sales|largest opportunity/,
    'forbidden opportunity wording appeared');
});
