#!/usr/bin/env node
/* ===========================================================================
   UX-05 acceptance tests: a clear decision summary with deeper evidence
   underneath.

   How to run
     node --test tests/ux_05_summary.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-05):
     E1  The turbo header, cost panels, scenario and export use consistent
         current metadata.
     E2  The reader can distinguish evidence completeness, technical authority
         and commercial approval.

   src/ui/app.js is loaded through the tests/ux_flow.test.mjs harness, with the
   synthetic fixture tests/fixtures/ux_05_summary.json only. The restricted
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
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_05_summary.json'), 'utf8'));
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
const TURBO = 'SYNTH-TURBO';
const NOCOST = 'SYNTH-NOCOST';
const failedView = (html) => /data-failed-view/.test(html);
const unesc = (v) => v.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const metaIn = (html, where) => {
  const found = [...html.matchAll(/data-metadata="([^"]*)"/g)].map((m) => JSON.parse(unesc(m[1])));
  assert.ok(found.length, where + ' carries no current-metadata block');
  return found;
};
const statusLine = (html, key) => {
  const m = new RegExp('data-status="' + key + '"><span>[^<]*</span><b[^>]*>([^<]*)</b>').exec(html);
  assert.ok(m, 'the decision summary has no "' + key + '" line');
  return unesc(m[1]);
};

test('UX-05 E1: the turbo header, cost panels, scenario and export use consistent current metadata', () => {
  const s = loadApp(FX);
  const position = go(s, TURBO, 'position');
  assert.ok(!failedView(position), 'the price position view failed');
  const header = s.doc.getElementById('pack-status');
  const headerMeta = JSON.parse(header.getAttribute('data-metadata') || 'null');
  assert.ok(headerMeta, 'the header carries no current-metadata block');

  assert.equal(headerMeta.payload_version, FX.meta.version);
  assert.equal(headerMeta.build_date, FX.meta.buildDate);
  assert.equal(headerMeta.list_price_status, 'list conflict resolved from the payload on ' + FX.turboPriceResolution.resolved_on);
  assert.equal(headerMeta.cost_basis_id, s.api.scenario.get(TURBO).cost_basis_id, 'the header names a different cost basis from the scenario');
  assert.match(header.innerHTML, new RegExp('Cost: ' + headerMeta.cost_status.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')),
    'the header prints a cost status other than the one it carries');
  assert.doesNotMatch(header.innerHTML, /approved cost: not held/, 'the header still prints its fixed cost sentence');

  const views = {
    'the turbo panel': metaIn(position, 'the turbo panel'),
    'the decision summary': metaIn(go(s, TURBO, 'decision'), 'the decision summary'),
    'the cost panel': metaIn(go(s, TURBO, 'economics'), 'the cost panel'),
    'the scenario panel': metaIn(go(s, TURBO, 'action'), 'the scenario panel')
  };
  const exportBtn = s.doc.querySelector('#export-json');
  fire(exportBtn, 'click');
  const exported = JSON.parse(s.sandbox.__blobText());
  views['the export'] = [exported.metadata];
  Object.entries(views).forEach(([where, list]) => list.forEach((m) => {
    assert.deepEqual(m, headerMeta, where + ' states different metadata from the header');
  }));
});

test('UX-05 E2: the reader can distinguish evidence completeness, technical authority and commercial approval', () => {
  const s = loadApp(FX);
  const held = go(s, TURBO, 'decision');
  assert.ok(!failedView(held), 'the decision view failed');
  const at = held.indexOf('data-decision-summary');
  assert.ok(at >= 0, 'no decision summary is shown');
  assert.ok(at < held.indexOf('<svg') && (held.indexOf('<table') < 0 || at < held.indexOf('<table')),
    'the decision summary is not shown before the detailed charts and tables');

  const a = { completeness: statusLine(held, 'evidence-completeness'),
    technical: statusLine(held, 'technical-authority'), commercial: statusLine(held, 'commercial-approval') };
  assert.equal(new Set(Object.values(a)).size, 3, 'two of the three questions are answered with the same words');
  assert.match(a.completeness, /^Incomplete\. Not held: .*current customer net price/);
  assert.doesNotMatch(a.completeness, /parts purchase cost/, 'a held parts purchase cost is reported missing');
  assert.match(a.technical, /technically checked record/);
  assert.match(a.technical, /developer checks/);
  assert.match(a.commercial, /^Not approved\./, 'commercial approval is not stated as absent');

  const none = go(s, NOCOST, 'decision');
  const b = { completeness: statusLine(none, 'evidence-completeness'),
    technical: statusLine(none, 'technical-authority'), commercial: statusLine(none, 'commercial-approval') };
  assert.match(b.completeness, /Not held: parts purchase cost/, 'a missing parts purchase cost is not counted against completeness');
  assert.match(b.technical, /^No technically checked parts purchase cost is held/);
  assert.equal(b.commercial, a.commercial, 'commercial approval moved with the evidence, so the two are not independent');
  assert.notEqual(b.technical, a.technical, 'technical authority did not move with the cost record');
});