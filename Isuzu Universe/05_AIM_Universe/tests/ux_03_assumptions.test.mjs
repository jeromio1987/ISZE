#!/usr/bin/env node
/* ===========================================================================
   UX-03 acceptance tests: make assumptions explicit and quick to change.

   How to run
     node --test tests/ux_03_assumptions.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-03):
     E1  Each visible financial result can be traced to the exact edited inputs.
     E2  Invalid inputs have field-specific errors; zero, blank and unknown have
         different behaviour.

   src/ui/app.js is loaded through a stub shell copied from tests/ux_02_alternative
   .test.mjs (the harness that already paints the Price & profit test). The
   fixture is tests/fixtures/ux_03_assumptions.json, a synthetic payload with
   invented values. The restricted payload is never read.

   The two controls under test are:
     window.AIMPricing.assumptions()
       The one working record expressed as the inputs that produced the results:
       a fingerprint over the exact edited inputs, the inputs themselves, and the
       two visible results, plus whether this is a manual scenario or a stated
       commitment. The same object is written onto the painted view as
       data-trace="<fingerprint>", so the reader and the test read one record.
     window.AIMPricing.fieldIssues()
       A per-field verdict drawn from the engine's own validation: value, zero,
       unknown or invalid, each with a field-specific sentence. A blank is not a
       zero, and neither is an error.
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
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_03_assumptions.json'), 'utf8'));

/* ---------------------------------------------- harness, as in ux_02 -- */
/* Copied from tests/ux_02_alternative.test.mjs (stub document, storage, app
   source rewrite and event firing), so this file loads src/ui/app.js exactly
   the way that suite does. Only the payload differs: a synthetic fixture. */
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
      derived[key].disabled = /disabled/.test(tag);
      out.push(derived[key]);
    }
    return out;
  }

  function elementForId(id) {
    if (nodes[id]) return nodes[id];
    const html = contentHtml() || '';
    const re = new RegExp('<button[^>]*id="' + id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '"[^>]*>');
    const m = re.exec(html);
    if (m) {
      const attrs = {};
      m[0].replace(/data-([a-z-]+)(?:="([^"]*)")?/g, (_x, k, v) => {
        attrs[k.replace(/-([a-z])/g, (_m2, ch) => ch.toUpperCase())] = v === undefined ? '' : v;
        return '';
      });
      if (Object.keys(attrs).length) {
        const key = '#attr:' + id;
        if (!derived[key]) { derived[key] = stubElement(id); derived[key].dataset = {}; }
        Object.assign(derived[key].dataset, attrs);
        nodes[id] = derived[key];
      }
    }
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
  assert.ok(list.length || direct, `no ${type} handler is bound to ${el.id || el.selector || 'the element'}`);
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
const traceOf = (html) => (new RegExp('data-trace="([^"]*)"').exec(html) || [])[1];

test('UX-03 E1: each visible financial result can be traced to the exact edited inputs', () => {
  const s = loadApp(FX);
  const html = go(s, CASE, 'economics');

  const t = s.api.assumptions();
  assert.ok(t && typeof t.fingerprint === 'string' && t.fingerprint.length > 0,
    'the view does not expose an assumptions trace');

  /* The trace is the one working record, not a second copy: every input it
     names equals the scenario the calculation used. */
  const sc = s.api.getScenario();
  Object.keys(t.inputs).forEach((k) => {
    assert.deepEqual(t.inputs[k], sc[k] === undefined ? null : sc[k],
      `the trace input ${k} does not match the working record`);
  });
  assert.equal(t.results.revenue_change, s.api.getResult().revenue_change,
    'the trace does not carry the revenue result the view shows');
  assert.equal(t.results.gp_change, s.api.getResult().gp_change,
    'the trace does not carry the gross-profit result the view shows');

  /* The painted view carries the same fingerprint, so a reader sees which
     record the numbers came from. */
  const painted = traceOf(html);
  assert.ok(painted, 'the Price & profit test does not carry data-trace');
  assert.equal(painted, t.fingerprint, 'the painted fingerprint is not the trace fingerprint');

  /* Editing one input moves the fingerprint and the result it drives. */
  const p = s.doc.getElementById('s-newP');
  const before = t.fingerprint;
  const revBefore = t.results.revenue_change;
  p.value = String(Number(sc.price_before) + 1);
  fire(p, 'input');

  const t2 = s.api.assumptions();
  assert.notEqual(t2.fingerprint, before, 'the fingerprint did not move after an edit');
  assert.equal(t2.inputs.price_after, Number(sc.price_before) + 1,
    'the trace does not name the edited price');
  assert.notEqual(t2.results.revenue_change, revBefore,
    'the revenue result did not follow the edited price');
  const html2 = go(s, CASE, 'economics');
  s.api.render();
  const html3 = s.doc.nodes.content.innerHTML;
  assert.equal(traceOf(html3), t2.fingerprint,
    'the repainted view does not carry the new fingerprint');

  /* A manual scenario is distinguished from a recorded commitment. */
  assert.equal(t.commitment.is_commitment, true,
    'a recorded volume basis was reported as a manual scenario');
  assert.match(t.commitment.statement, /recorded/i);
  const label = s.doc.getElementById('s-label');
  label.value = 'manual scenario';
  fire(label, 'input');
  const t3 = s.api.assumptions();
  assert.equal(t3.commitment.is_commitment, false, 'a manual label still read as a commitment');
  assert.match(t3.commitment.statement, /manual/i);
});

test('UX-03 E2: invalid inputs have field-specific errors, and zero, blank and unknown differ', () => {
  const s = loadApp(FX);
  go(s, CASE, 'economics');

  /* The untouched scenario: no field is in error, and the cost reads as a
     stated unknown rather than a value of zero. */
  let issues = s.api.fieldIssues();
  const byField = (id) => issues.fields.find((f) => f.field === id);
  assert.equal(issues.ok, true, 'a valid scenario was reported as having errors');
  assert.equal(byField('s-newP').state, 'value');
  assert.equal(byField('s-cost').state, 'unknown');
  assert.equal(s.api.getResult().gp_change, null);

  /* A stated cost is a value: gross profit follows it. */
  const cost = s.doc.getElementById('s-cost');
  cost.value = '2';
  fire(cost, 'input');
  issues = s.api.fieldIssues();
  assert.equal(byField('s-cost').state, 'value', 'a stated cost was not read as a value');
  assert.notEqual(s.api.getResult().gp_change, null,
    'a stated cost did not produce a gross-profit figure');

  /* A blank is unknown, not zero: gross profit stops being calculated, and the
     field says which one and what would supply it. */
  cost.value = '';
  fire(cost, 'input');
  issues = s.api.fieldIssues();
  const unknown = issues.fields.find((f) => f.field === 's-cost');
  assert.equal(unknown.state, 'unknown');
  assert.match(unknown.text, /not calculated|not a cost of zero|unknown/i);
  assert.notEqual(unknown.state, 'zero');
  assert.equal(s.api.getResult().gp_change, null,
    'a blank cost still produced a gross-profit figure');

  /* Zero is its own, different behaviour: a stated value, and for the proposed
     quantity a withdrawal rather than a price scenario. */
  const support = s.doc.getElementById('s-support');
  support.value = '0';
  fire(support, 'input');
  issues = s.api.fieldIssues();
  const sZero = issues.fields.find((f) => f.field === 's-support');
  assert.equal(sZero.state, 'zero', 'a stated zero is its own state');
  assert.match(sZero.text, /zero/i);
  assert.notEqual(sZero.state, 'unknown');

  const qty = s.doc.getElementById('s-qty');
  qty.value = '0';
  fire(qty, 'input');
  issues = s.api.fieldIssues();
  const q = issues.fields.find((f) => f.field === 's-qty');
  assert.equal(q.state, 'zero');
  assert.match(q.text, /withdraw/i);

  /* Back to blank: unknown again, and the behaviour differs from zero. */
  qty.value = '';
  fire(qty, 'input');
  issues = s.api.fieldIssues();
  assert.equal(issues.fields.find((f) => f.field === 's-qty').state, 'unknown');

  /* An invalid entry gets its own field and its own sentence, and the whole
     scenario is refused rather than silently clamped. */
  const price = s.doc.getElementById('s-newP');
  price.value = '-5';
  fire(price, 'input');
  issues = s.api.fieldIssues();
  assert.equal(issues.ok, false, 'an invalid price was accepted');
  const invalid = issues.fields.find((f) => f.field === 's-newP');
  assert.equal(invalid.state, 'invalid');
  assert.match(invalid.text, /price/i);
  assert.notEqual(invalid.state, 'unknown');
  assert.equal(s.api.getResult().ok, false, 'an invalid scenario still calculated a result');

  /* The three behaviours are three different states, not one. */
  const states = new Set(issues.fields.map((f) => f.state));
  assert.ok(states.has('invalid'), 'no invalid state was reported');
  assert.ok(states.has('unknown'), 'no unknown state was reported');
  assert.ok(states.has('value'), 'no value state was reported');
});
