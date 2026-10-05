#!/usr/bin/env node
/* ===========================================================================
   UX-06 acceptance tests: partial, failed and empty states are recoverable.

   How to run
     node --test tests/ux_06_states.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-06):
     E1  Removing an optional source leaves a correctly labelled narrower
         review.
     E2  A save failure preserves the unsaved form and never displays a false
         saved confirmation.

   src/ui/app.js is loaded through the tests/ux_flow.test.mjs harness, with the
   synthetic fixture tests/fixtures/ux_06_sources.json only. The restricted
   payload is never read here. For E2 the case repository is built over the
   stub storage instead of memory, so a write can be refused on purpose.
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
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_06_sources.json'), 'utf8'));
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
  const storage = {
    refuse: false,
    getItem: (k) => (Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null),
    setItem: (k, v) => {
      if (storage.refuse && k !== '__t') throw new Error('synthetic quota exceeded');
      data[k] = String(v);
    },
    removeItem: (k) => { delete data[k]; },
    clear: () => { Object.keys(data).forEach((k) => delete data[k]); },
    _data: data
  };
  return storage;
}

function appSource(opts) {
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
    (opts && opts.storage ? 'const repo=K.makeRepository({forceMemory:false});' : 'const repo=K.makeRepository({forceMemory:true});'), 'case repository construction');
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


function loadApp(payload, opts) {
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
  vm.runInContext(appSource(opts), sandbox, { filename: APP, timeout: 30000 });
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
const HELD = 'SYNTH-STD-HELD';
const REMOVED = 'SYNTH-STD-REMOVED';
const failedView = (html) => /data-failed-view/.test(html);

test('UX-06 E1: removing an optional source leaves a correctly labelled narrower review', () => {
  const s = loadApp(FX);

  const full = go(s, HELD, 'decision');
  assert.ok(!failedView(full), 'the decision view failed with sales to dealer held');
  assert.match(full, /What the distributor supplied to dealers/, 'the held sales-to-dealer chart is not drawn');
  assert.doesNotMatch(full, /data-review-scope="narrower"/, 'a full review is labelled narrower');
  assert.doesNotMatch(full, /data-source-missing=/, 'a held source is labelled missing');

  const narrow = go(s, REMOVED, 'decision');
  assert.ok(!failedView(narrow), 'removing an optional source failed the whole review');
  assert.match(narrow, /What ISZE billed/, 'the supported billing evidence is no longer shown');
  assert.match(narrow, /data-review-scope="narrower"[^>]*>[^<]*covers what ISZE billed only/,
    'the review does not say it is narrower and what it still covers');
  assert.match(narrow, /data-unavailable="sales to dealer"/, 'the removed source has no labelled unavailable state');
  assert.match(narrow, /No sales-to-dealer record is held for this case/);
  assert.match(narrow, /not zero sales to dealers/, 'a missing source is not told apart from a confirmed zero');
  assert.doesNotMatch(narrow, /What the distributor supplied to dealers/, 'an empty sales-to-dealer chart is still drawn');
  assert.match(narrow, /data-source-missing="sales to dealer"[\s\S]*?Not held/, 'the change tile does not say the source is not held');
});

test('UX-06 E2: a save failure preserves the unsaved form and never displays a false saved confirmation', () => {
  const s = loadApp(FX, { storage: true });
  const val = (id) => s.doc.querySelector('#' + id);
  /* The stub keeps one element per id across paints, so each paint adds a
     listener. A real paint replaces the button; only the latest binding runs. */
  const save = () => {
    const bound = val('save-case')._listeners.click || [];
    assert.ok(bound.length, 'no click handler is bound to the save button');
    bound[bound.length - 1]({ preventDefault() {} });
  };

  go(s, HELD, 'action');
  /* A dated next update, so the record itself is valid and only storage can refuse it. */
  val('a-due').value = '2026-11-02';
  val('a-note').value = 'First saved note';
  save();
  assert.match(val('save-status').textContent, /^Saved as revision 1\. Nothing was overwritten\./, 'the first, accepted save did not report revision 1');

  s.sandbox.localStorage.refuse = true;
  go(s, HELD, 'action');
  val('a-note').value = 'UNSAVED edit after revision 1';
  save();
  const status = val('save-status').textContent;
  assert.match(status, /^Not saved\. storage refused the write/, 'a refused write is not reported as not saved');
  assert.doesNotMatch(status, /Saved as revision/);

  go(s, HELD, 'decision');
  const back = go(s, HELD, 'action');
  assert.ok(!failedView(back), 'the record view failed after a refused save');
  assert.match(back, /<textarea id="a-note">UNSAVED edit after revision 1<\/textarea>/, 'the unsaved entry was lost on the next paint');
  assert.match(back, /id="save-status">Not saved\. The form holds your unsaved entries; the last saved revision is 1\./,
    'the record view does not say the entries are unsaved');
  assert.doesNotMatch(back, /Case at revision 2|last saved revision is 2|Revision 2 saved/, 'the refused revision is reported as saved');

  save();
  assert.match(val('save-status').textContent, /^Saved as revision 2 for this session only\./,
    'a retry into session memory is reported as a durable save');
});