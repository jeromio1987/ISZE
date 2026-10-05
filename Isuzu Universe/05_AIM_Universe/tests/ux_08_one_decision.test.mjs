#!/usr/bin/env node
/* ===========================================================================
   UX-08 acceptance tests: make save, export and reopen preserve one decision.

   How to run
     node --test tests/ux_08_one_decision.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-08):
     E1  Select, edit, save, export, restart and reopen preserves the same
         assumptions, amounts and dates.
     E2  Older local notes migrate with an explicit legacy basis or remain
         view-only; missing fields are not invented.

   src/ui/app.js is loaded with the ux_06 harness copied into this file. The
   fixture is tests/fixtures/ux_08_one_decision.json, a synthetic payload with
   invented values. The restricted payload is never read.

   The known defect carried from U4 is covered inside E1: `collectReview` sends
   an empty next-update date as '' and the second save is refused with
   "next_update_due must be YYYY-MM-DD or null". E1 saves twice with a blank
   date and requires both saves to succeed, so the defect has a test line of its
   own.
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
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_08_one_decision.json'), 'utf8'));

/* ---------------------------------------------- harness, as in ux_06 -- */
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

function makeStorage(seed) {
  const data = Object.assign({}, seed || {});
  const storage = {
    getItem: (k) => (Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null),
    setItem: (k, v) => { if (storage.refuse) { const e = new Error('quota'); throw e; } data[k] = String(v); },
    removeItem: (k) => { delete data[k]; },
    clear: () => { Object.keys(data).forEach((k) => delete data[k]); },
    _data: data
  };
  return storage;
}

function appSource(opts) {
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
    'const repo=K.makeRepository({forceMemory:false});', 'case repository construction');
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

function loadApp(payload, opts) {
  opts = opts || {};
  const storage = makeStorage(opts.seed);
  globalThis.localStorage = storage;
  const doc = makeFakeDocument();
  const sandbox = {
    __payload: JSON.parse(JSON.stringify(payload)),
    __dom: { $: (sel) => doc.querySelector(sel), $$: (sel) => doc.querySelectorAll(sel) },
    document: doc, localStorage: storage, location: { hash: opts.hash || '' },
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

/* The latest binding only: the stub keeps one element per id across paints, so a
   click would otherwise run every handler ever bound. */
function clickLatest(session, id) {
  const el = session.doc.getElementById(id);
  const list = el._listeners.click || [];
  assert.ok(list.length, 'no click handler is bound to ' + id);
  list[list.length - 1]({ preventDefault() {} });
}

const CASE = FX.cases[0].id;
const ALT = 'SYNTH-INC';
const STORE_KEY = 'ISZE_AIM_CASES_V1';

test('UX-08 E1: select, edit, save, export, restart and reopen preserves the same decision', () => {
  const s = loadApp(FX);

  /* Select a ranked alternative, then edit a stated assumption. */
  go(s, CASE, 'objectives');
  const sel = s.doc.querySelector('[data-select]');
  assert.ok(sel, 'the objectives view offers no alternative to select');
  sel.dataset.select = ALT;
  fire(sel, 'click');
  settle(s);
  go(s, CASE, 'economics');
  const price = s.doc.getElementById('s-newP');
  price.value = '6.5';
  fire(price, 'input');
  const date = s.doc.getElementById('s-date');
  date.value = '2026-10-05';
  fire(date, 'change');
  const period = s.doc.getElementById('s-period');
  period.value = 'recorded H1';
  fire(period, 'input');

  const before = s.api.getScenario();
  const beforeResult = s.api.getResult();

  /* Export the internal record: the export must carry the same decision. */
  go(s, CASE, 'action');
  clickLatest(s, 'export-json');
  const exported = (() => { try { return JSON.parse(s.sandbox.__blobText()); } catch (e) { return null; } })();
  assert.ok(exported, 'the internal export did not produce readable JSON');

  /* ---- The known defect: two saves with a BLANK next-update date both succeed.
     `collectReview` sends '' for an empty date, and the second save used to be
     refused with "next_update_due must be YYYY-MM-DD or null". ---- */
  const val = (id) => s.doc.getElementById(id);
  const save = () => clickLatest(s, 'save-case');
  go(s, CASE, 'action');
  val('a-due').value = '';
  val('a-note').value = 'First save with no due date';
  save();
  const first = val('save-status').textContent;
  assert.match(first, /^Saved as revision 1/, 'the first blank-date save did not report revision 1');

  go(s, CASE, 'action');
  val('a-due').value = '';
  val('a-note').value = 'Second save with no due date';
  save();
  const second = val('save-status').textContent;
  assert.match(second, /^Saved as revision 2/,
    'a case with no next-update date could not be saved a second time: ' + second);

  /* ---- Restart: a brand new module scope, the same storage object. */
  const savedRaw = s.sandbox.localStorage.getItem(STORE_KEY);
  const restart = loadApp(FX, { seed: savedRaw ? { [STORE_KEY]: savedRaw } : undefined,
    hash: '#' + new URLSearchParams({ case: CASE, view: 'economics', compare: 'half' }).toString() });

  const after = restart.api.getScenario();
  const afterResult = restart.api.getResult();
  ['price_before', 'price_after', 'quantity_before', 'quantity_after', 'scope',
    'cost_eur', 'cost_basis_id', 'pack_size', 'support_eur', 'quantity_label',
    'evidence_period', 'offer_effective_date', 'selected_alternative_id']
    .forEach((k) => {
      assert.deepEqual(after[k], before[k], `reopen changed ${k}`);
    });
  assert.equal(afterResult.revenue_change, beforeResult.revenue_change,
    'reopen changed the revenue result');
  assert.equal(afterResult.gp_change, beforeResult.gp_change,
    'reopen changed the gross-profit result');

  /* The exported record carries the same decision and the same dates. */
  const flat = JSON.stringify(exported);
  assert.ok(flat.indexOf('2026-10-05') >= 0, 'the export lost the offer effective date');
  assert.ok(flat.indexOf('6.5') >= 0, 'the export lost the edited price');
  assert.ok(flat.indexOf('recorded H1') >= 0, 'the export lost the evidence period');
});

test('UX-08 E2: older local notes migrate with an explicit legacy basis, and no field is invented', () => {
  /* An older local shape: a scenario field does not exist in it, a note is in an
     older key, and the newer fields (schema/calculation/source versions) are
     absent. Nothing in it may be invented on the way in. */
  const legacyCase = {
    case_id: CASE,
    customer: FX.cases[0].customer,
    market: FX.cases[0].market,
    part_number: FX.cases[0].pn,
    legacy_note: 'An older note kept in an older key.',
    scenario: {
      price_after: 9.99,
      quantity_after: 77
      /* no price_before, no cost, no dates, no basis, no versions */
    }
  };
  const seed = { [STORE_KEY]: JSON.stringify({ [CASE]: legacyCase }) };
  const s = loadApp(FX, { seed });

  const migrated = s.api.migrateLegacyCases();
  assert.equal(migrated.ok, true, 'the migration was not reported as run');
  assert.equal(migrated.migrated.length, 1, 'the older record was not migrated');
  const m = migrated.migrated[0];
  assert.equal(m.case_id, CASE);

  /* An explicit legacy basis is stated, and the missing versions are named as
     unknown rather than filled with a current value. */
  assert.equal(m.legacy_basis, true, 'the migrated record does not state a legacy basis');
  assert.match(m.basis_statement, /legacy/i);
  assert.deepEqual(m.missing_versions.slice().sort(),
    ['calculation_version', 'contract_version', 'schema_version', 'source_version'].sort(),
    'the migration does not name which versions are missing');
  assert.equal(m.invented.length, 0, 'a missing field was invented');

  /* The older note is preserved, and its older key is named. */
  assert.match(m.preserved_notes.map((n) => n.key).join(','), /legacy_note/);
  assert.match(JSON.stringify(m.preserved_notes), /An older note kept in an older key/);

  /* The stored record carries the legacy basis and the older note, and nothing
     that it did not carry. */
  const stored = JSON.parse(s.sandbox.localStorage.getItem(STORE_KEY))[CASE];
  assert.equal(stored.legacy_basis, true);
  assert.equal(stored.legacy_note, 'An older note kept in an older key.');
  assert.equal(stored.scenario.price_after, 9.99);
  assert.equal(stored.scenario.quantity_after, 77);
  assert.ok(!('price_before' in stored.scenario) || stored.scenario.price_before === null,
    'the migration invented a price_before the older record did not carry');
});
