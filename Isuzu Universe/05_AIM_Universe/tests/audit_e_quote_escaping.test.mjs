#!/usr/bin/env node
/* ===========================================================================
   Audit fix E (U27): every HTML escaper handles all five characters, and a
   hostile customer name and part number export as inert text.

   How to run
     node --test tests/audit_e_quote_escaping.test.mjs

   The app loader is the one in tests/review_03_comparison.test.mjs, copied so
   this file stands alone. Data: tests/fixtures/review_03_five_cases.json with
   the customer and part number replaced by synthetic hostile strings.
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

const HOSTILE = 'O\'Brien"><script>alert(1)</script>';
const HOSTILE_PN = 'SYN"><img src=x onerror=alert(2)>';
const ESCAPED = 'O&#39;Brien&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;';

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


const MODULES = ['ids_evidence', 'ids_improvement_action', 'prism_context', 'service_demand_bounds'];

for (const name of MODULES) {
  test(`audit E: ${name} escapes all five characters, the single quote included`, () => {
    const mod = require(path.join(ROOT, 'src', 'data', name + '.js'));
    assert.equal(typeof mod.escapeHtml, 'function');
    assert.equal(mod.escapeHtml(HOSTILE), ESCAPED);
    assert.equal(mod.escapeHtml('a&b'), 'a&amp;b');
  });
}

test('audit E: a hostile customer name and part number export as inert text', () => {
  const fx = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_03_five_cases.json'), 'utf8'));
  const target = fx.cases[0];
  target.customer = HOSTILE;
  target.pn = HOSTILE_PN;
  const session = loadApp(fx);
  openCase(session, target.id, 'economics', 'half');
  const html = session.api.exportReviewText();
  assert.ok(html.includes(ESCAPED), 'the customer name appears escaped');
  assert.ok(html.includes('SYN&quot;&gt;&lt;img src=x onerror=alert(2)&gt;'), 'the part number appears escaped');
  assert.equal(html.includes('<script>alert(1)'), false, 'no live script tag');
  assert.equal(html.includes('<img src=x'), false, 'no live image tag');
  assert.equal(html.includes("O'Brien"), false, 'no raw single quote from case text');

  for (const view of ['decision', 'position', 'economics', 'candidates', 'case', 'action']) {
    openCase(session, target.id, view, 'half');
    for (const id of ['case-list', 'case-header', 'content', 'scope-strip']) {
      const painted = session.doc.nodes[id] ? session.doc.nodes[id].innerHTML : '';
      assert.equal(painted.includes('<img src=x'), false, `${view}/#${id}: live image tag from the part number`);
      assert.equal(painted.includes('<script>alert(1)'), false, `${view}/#${id}: live script tag from the customer`);
    }
  }
});
