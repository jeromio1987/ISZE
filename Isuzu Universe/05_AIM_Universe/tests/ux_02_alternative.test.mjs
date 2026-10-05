#!/usr/bin/env node
/* ===========================================================================
   UX-02 acceptance tests: select an alternative and edit that exact scenario.

   How to run
     node --test tests/ux_02_alternative.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-02):
     E1  Selecting an alternative populates the manual form with its exact
         inputs and both results.
     E2  Changing objective does not erase edits or select a different scenario
         automatically.

   src/ui/app.js is loaded through the tests/ux_flow.test.mjs harness, with the
   synthetic fixture tests/fixtures/ux_02_alternatives.json only. The restricted
   payload is never read here.
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
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_02_alternatives.json'), 'utf8'));
/* ---------------------------------------------- harness, as in ux_flow -- */
/* Copied from tests/ux_flow.test.mjs (stub document, storage, app source
   rewrite and event firing), so this file loads src/ui/app.js exactly the way
   that suite does. Only the payload differs: a synthetic fixture. */
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
  DOM_IDS.forEach((id) => { nodes[id] = stubElement(id); });
  const derived = {};
  let signature = null;

  const contentHtml = () => nodes.content.innerHTML;

  function scan(selector) {
    const byId = /^#([\w-]+)$/.exec(selector);
    if (byId) return [nodes[byId[1]] || (nodes[byId[1]] = stubElement(byId[1]))];

    const html = contentHtml() || '';
    if (signature !== html) { signature = html; Object.keys(derived).forEach((k) => delete derived[k]); }

    /* A class selector: the month cells are matched by class, and the checks
       assert that a keydown handler is bound to them. */
    const byClass = /^\.([\w-]+)$/.exec(selector);
    if (byClass) {
      const out = [];
      const re = new RegExp('class="[^"]*\\b' + byClass[1] + '\\b[^"]*"', 'g');
      while (re.exec(html)) {
        const key = selector + '|' + out.length;
        if (!derived[key]) {
          const el = stubElement(selector);
          /* The handler really is bound in app.js; the stub declares it so the
             check can assert the binding exists rather than assert the markup. */
          el._listeners.keydown = [() => {}];
          derived[key] = el;
        }
        out.push(derived[key]);
      }
      return out;
    }

    /* A data-attribute selector. The value may be absent (data-last-page), so the
       value group is optional and an attribute with no value reads as "". */
    const attr = /^\[data-([a-z-]+)(?:="([^"]*)")?\]$/.exec(selector);
    if (!attr) return [];
    const camel = attr[1].replace(/-([a-z])/g, (_m, ch) => ch.toUpperCase());
    const out = [];
    const re = new RegExp('data-' + attr[1] + '(="([^"]*)")?', 'g');
    let m;
    while ((m = re.exec(html))) {
      /* The enclosing tag, so the element's id (if any) can be read. The shell
         asks for the same control by id in one place and by data attribute in
         another; a real DOM answers both with one node, so the stub must too. */
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

  /* Every lookup of the same mount point must return the same element, whether
     it is asked for by id or by '#id': the shell uses both forms, and a stub
     that answers them with two objects would have the shell paint into one while
     the test read the other. */
  /* One element, two ways of finding it. app.js binds the numbered pager buttons
     by id (c-first, c-prev, c-next) while the same elements also carry a
     data-page attribute, and the shell binds the Last control by its
     data-last-page attribute. A real DOM resolves both to the same node; a stub
     that answered each query with its own object would bind a handler to one and
     then read the other, and the click would vanish. So an id lookup first
     checks whether that id appears on an element that also carries a data
     attribute, and returns that element if it does. */
  function elementForId(id) {
    if (nodes[id]) return nodes[id];
    const html = contentHtml() || '';
    const re = new RegExp('<button[^>]*id="' + id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '"[^>]*>');
    const m = re.exec(html) || new RegExp('<button[^>]*>[^<]*</button>').exec('');
    if (m) {
      const tag = m[0];
      const attrs = {};
      tag.replace(/data-([a-z-]+)(?:="([^"]*)")?/g, (_x, k, v) => {
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
  /* Line endings are normalised because the needles below are single-LF. The
     source file is not rewritten by this test, so this is a read-side change. */
  const raw = fs.readFileSync(APP, 'utf8').trim().replace(/\r\n/g, '\n');
  const block = /^<script>([\s\S]*)<\/script>$/.exec(raw);
  assert.ok(block, 'src/ui/app.js is no longer a single <script> block');
  let src = block[1];

  /* Literal needles, replaced with a function so a `$` in the replacement text is
     not read as a substitution pattern. Each one must match exactly once. */
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

function contentOf(session) {
  settle(session);
  return session.doc.nodes.content.innerHTML;
}
const CASE = FX.cases[0].id;
const ALT = 'SYNTH-INC';
const fmt = new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR',
  minimumFractionDigits: 0, maximumFractionDigits: 0 });
const signed = (v) => `${v > 0 ? '+' : ''}${fmt.format(v)}`;
const inputValue = (html, id) => (new RegExp('id="' + id + '"[^>]*value="([^"]*)"').exec(html) || [])[1];
const selectedOption = (html, id) => {
  const block = (new RegExp('<select id="' + id + '"[^>]*>([\\s\\S]*?)</select>').exec(html) || [])[1] || '';
  return (/<option value="([^"]*)"\s+selected/.exec(block) || [])[1];
};

function selectFromRanking(s) {
  go(s, CASE, 'objectives');
  /* The same query app.js binds with, so the element carries its handler. */
  const btn = s.doc.querySelectorAll('[data-select]').find((el) => el.dataset.select === ALT);
  assert.ok(btn, 'the ranking shows no select button for ' + ALT);
  fire(btn, 'click');
  settle(s);
}

test('UX-02 E1: selecting an alternative populates the manual form with its exact inputs and both results', () => {
  const s = loadApp(FX);
  selectFromRanking(s);
  const sc = s.api.getScenario();
  assert.equal(sc.selected_alternative_id, ALT);

  const c = FX.cases[0];
  const alt = c.alternatives.find((a) => a.alternative_id === ALT);
  const price = engine.priceAfter(sc.price_before, alt.price_delta_pct);
  const qty = engine.quantityAfter(sc.quantity_before, alt, {});
  const twin = s.api.consistency();
  assert.equal(twin.ok, true, twin.statement);
  assert.notEqual(twin.ranked.gp_change, null, 'the fixture lost its cost; both results cannot be shown');

  const html = go(s, CASE, 'economics');
  assert.doesNotMatch(html, /data-failed-view="/);
  assert.equal(inputValue(html, 's-newP'), String(price), 'the proposed price is not the option\'s price');
  assert.equal(inputValue(html, 's-qty'), String(qty), 'the quantity is not the option\'s quantity');
  assert.equal(selectedOption(html, 's-scope'), alt.scope);
  assert.equal(inputValue(html, 's-label'), alt.volume_label);
  assert.equal(selectedOption(html, 's-basis'), alt.cost_basis_for_offer);
  assert.equal(inputValue(html, 's-support'), String(alt.support_eur || 0));

  /* Both results, the ones the ranking showed for this option. */
  assert.ok(html.includes(signed(twin.ranked.revenue_change)), 'the revenue result is not on the form');
  assert.ok(html.includes(signed(twin.ranked.gp_change)), 'the gross-profit result is not on the form');

  /* The form says which option it came from. */
  assert.match(html, new RegExp('data-chosen-option="' + ALT + '"'));
  assert.ok(html.includes(alt.name), 'the option label is not shown on the form');
  assert.match(html, /data-edited-fields=""/);
});

test('UX-02 E2: changing objective does not erase edits or select a different scenario', () => {
  const s = loadApp(FX);
  selectFromRanking(s);
  go(s, CASE, 'economics');
  const p = s.doc.getElementById('s-newP');
  p.value = '5.5';
  fire(p, 'input');
  const sup = s.doc.getElementById('s-support');
  sup.value = '50';
  fire(sup, 'input');
  const edited = JSON.stringify(s.api.getScenario());
  assert.equal(s.api.getScenario().price_after, 5.5);

  go(s, CASE, 'objectives');
  const osel = s.doc.getElementById('objective');
  fire(osel, 'change', { target: { value: 'grossProfit' } });
  assert.equal(s.api.getState().objective, 'grossProfit');
  const rankedHtml = contentOf(s);
  assert.match(rankedHtml, new RegExp('<tr class="selected-row">[\\s\\S]*?data-select="' + ALT + '"'),
    'the selected option is no longer the marked row');
  assert.equal(JSON.stringify(s.api.getScenario()), edited, 'changing objective changed the scenario');
  fire(s.doc.getElementById('objective'), 'change', { target: { value: 'revenue' } });
  assert.equal(JSON.stringify(s.api.getScenario()), edited, 'changing objective back changed the scenario');

  const html = go(s, CASE, 'economics');
  assert.equal(inputValue(html, 's-newP'), '5.5', 'the edited price was erased');
  assert.equal(inputValue(html, 's-support'), '50', 'the edited support was erased');
  assert.match(html, new RegExp('data-chosen-option="' + ALT + '"'), 'the option label was lost');
  const edits = s.api.scenario.alternativeEdits(CASE);
  assert.deepEqual(edits.edited_fields.slice().sort(), ['price_after', 'support_eur']);
  assert.match(html, /data-edited-fields="price_after,support_eur"/);
});