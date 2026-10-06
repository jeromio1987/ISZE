#!/usr/bin/env node
/* ===========================================================================
   REVIEW-05 acceptance tests: separate price, quantity and mix.

   How to run
     node --test tests/review_05_price_quantity_mix.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (REVIEW-05):
     E1  A pure mix shift is not reported as a list-price increase. It shows a zero
         price effect and a non-zero mix effect, the average unit revenue still
         rises, and the painted screen and the exported review say so as a
         unit-revenue change.
     E2  Components plus new, discontinued, returns and residual equal the observed
         euro change exactly, for a fixture with a new reference, a discontinued
         reference and a non-zero residual, and for each real case (the five case
         ids, in the real payload shape) at both comparisons.
     E3  A quantity-only reference never shows an invented euro and sits in the
         "not decomposed" list; a candidate shows no figure for a period.

   Pattern: tests/review_04_contributors.test.mjs for the evidence calls, and
   tests/review_03_comparison.test.mjs for the app harness that paints the screen.
   Fixtures are invented values only:
     tests/fixtures/review_05_mix_shift.json
     tests/fixtures/review_05_components.json
   The review_04 fixture supplies the five case ids in the real payload shape. No
   supplier cost, list price or observed billing figure is copied into this tracked
   file; the real-shape checks assert relationships, not figures.
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
const evidence = require(path.join(ROOT, 'src', 'data', 'evidence.js'));
const contracts = require(path.join(ROOT, 'src/data/contracts.js'));
const engine = require(path.join(ROOT, 'src/engine/engine.js'));
const caseModule = require(path.join(ROOT, 'src/data/cases.js'));
const candidateModule = require(path.join(ROOT, 'src/data/candidates.js'));
const scenarioModule = require(path.join(ROOT, 'src/data/scenario.js'));
const exportModule = require(path.join(ROOT, 'src/data/export.js'));
const comparableModule = require(path.join(ROOT, 'src/data/comparable.js'));
const APP = path.join(ROOT, 'src/ui/app.js');

const read = (name) => JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', name), 'utf8'));
const MIX = read('review_05_mix_shift.json');
const COMP = read('review_05_components.json');
const REAL_SHAPE = read('review_04_contributors.json');
const REAL_CASE_IDS = REAL_SHAPE.cases.map((c) => c.id);
const COMPARES = ['half', 'annual'];

function decompose(caseRec, compare) {
  assert.equal(typeof evidence.priceQuantityMix, 'function',
    'AIMEvidence.priceQuantityMix is missing');
  return evidence.priceQuantityMix(caseRec, compare);
}

/* Everything the screen and the export print for this block, as one string. */
function panelText(rec) {
  const bits = [];
  bits.push(rec.label_rule || '', rec.mix_state || '', rec.statement || '');
  Object.keys(rec.components || {}).forEach((k) => bits.push(k + ' ' + String(rec.components[k])));
  (rec.continuing || []).forEach((r) => bits.push(r.pn, String(r.price_effect_eur)));
  (rec.not_decomposed || []).forEach((r) => bits.push(r.pn, r.reason));
  (rec.new_references || []).forEach((r) => bits.push(r.pn, 'new', String(r.eur)));
  (rec.discontinued_references || []).forEach((r) => bits.push(r.pn, 'discontinued', String(r.eur)));
  (rec.returns || []).forEach((r) => bits.push(r.pn, 'return', String(r.eur)));
  return bits.join('\n');
}

/* ----------------------------------------------------------- app harness -- */
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
    AIMEvidence: evidence, AIMEngine: engine, AIMExport: exportModule, AIMCandidates: candidateModule,
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
  session.sandbox.location.hash = '#' + new URLSearchParams({ case: caseId, view, compare }).toString();
  settle(session);
}

/* ------------------------------------------------------------------ tests -- */

test('REVIEW-05 E1: a pure mix shift shows a zero price effect and a non-zero mix effect, and neither the screen nor the export calls it a price increase', () => {
  const c = MIX.cases[0];
  const rec = decompose(c, 'half');
  assert.equal(rec.available, true);
  assert.equal(rec.ok, true, rec.statement);

  /* Every compatible reference keeps its own unit revenue. */
  rec.continuing.forEach((r) => assert.equal(r.unit_revenue_change, 0,
    'a unit revenue moved in a pure mix shift'));
  assert.equal(rec.continuing.length, 3, 'expected the case part plus two compatible references');
  assert.equal(rec.continuing_count, 3);

  assert.equal(rec.components.price_eur, 0, 'a pure mix shift produced a price effect');
  assert.equal(rec.components.quantity_eur, 0, 'total quantity is unchanged, so the quantity effect must be 0');
  assert.notEqual(rec.components.mix_eur, 0, 'a pure mix shift produced no mix effect');
  assert.equal(rec.mix_state, 'mix separated');
  assert.notEqual(rec.components.residual_eur, null, 'the residual is not printed');

  const k = rec.components;
  assert.equal(
    Math.round((k.price_eur + k.quantity_eur + k.mix_eur + k.new_eur
      + k.discontinued_eur + k.returns_eur + k.residual_eur) * 100) / 100,
    rec.observed_change_eur,
    'components plus residual do not equal the observed change');

  /* The average unit revenue of the compatible set still rises, even though no
     single reference changed its own unit revenue. That rise is the mix effect,
     and the block must present it as a unit-revenue change, not as a price move. */
  const sum = (list, key) => list.reduce((t, r) => t + r[key], 0);
  const avg0 = sum(rec.continuing, 'prior_eur') / sum(rec.continuing, 'prior_quantity');
  const avg1 = sum(rec.continuing, 'current_eur') / sum(rec.continuing, 'current_quantity');
  assert.ok(avg1 > avg0, 'the fixture no longer raises the average unit revenue');
  assert.equal(sum(rec.continuing, 'prior_quantity'), sum(rec.continuing, 'current_quantity'),
    'the fixture no longer holds total quantity unchanged');

  /* The painted screen. */
  const session = loadApp(MIX);
  openCase(session, c.id, 'decision', 'half');
  const html = session.doc.nodes.content.innerHTML;
  assert.match(html, /data-price-quantity-mix="1"/, 'the review does not draw the price / quantity / mix block');
  assert.match(html, /data-pqm-compare="half"/, 'the block does not state the selected comparison');
  assert.match(html, /unit-revenue change/i, 'the block does not use the unit-revenue label');
  assert.equal(/price increase(?! )/i.test(html.replace(/not a list-price increase/gi, '')), false,
    'the screen says "price increase" for a pure mix shift');
  assert.equal(/list-price increase/i.test(html.replace(/not a list-price increase/gi, '')), false,
    'the screen says "list-price increase" for a pure mix shift');
  assert.equal(/measured elasticity|elasticity is|elasticity of/i.test(html), false,
    'the screen claims a measured elasticity');
  assert.equal(html.includes('NaN'), false, 'the screen printed NaN');
  /* The block is drawn next to the REVIEW-04 contributors, on the same comparison. */
  assert.match(html, /data-contributors-compare="half"/);
  assert.ok(html.indexOf('data-contributors-compare="half"') < html.indexOf('data-price-quantity-mix="1"'),
    'the mix block is not placed beside the contributors');

  /* The exported review states the same comparison and the same figures. */
  const exported = session.api.exportReviewText();
  const num = (attr) => Number((exported.match(new RegExp('data-export-pqm-' + attr + '="([^"]+)"')) || [])[1]);
  assert.equal((exported.match(/data-export-pqm-compare="([^"]+)"/) || [])[1], 'half');
  assert.equal(num('observed'), rec.observed_change_eur);
  assert.equal(num('price'), rec.components.price_eur);
  assert.equal(num('quantity'), rec.components.quantity_eur);
  assert.equal(num('mix'), rec.components.mix_eur);
  assert.equal(num('new'), rec.components.new_eur);
  assert.equal(num('discontinued'), rec.components.discontinued_eur);
  assert.equal(num('returns'), rec.components.returns_eur);
  assert.equal(num('residual'), rec.components.residual_eur);
  assert.match(exported, /unit-revenue change/i);
  assert.equal(/measured elasticity|elasticity is|elasticity of/i.test(exported), false);
});

test('REVIEW-05 E2: components plus new, discontinued, returns and residual equal the observed change, on fixtures and on each real case at both comparisons', () => {
  const c = COMP.cases[0];
  const rec = decompose(c, 'half');
  assert.equal(rec.available, true);
  assert.equal(rec.ok, true, rec.statement);

  const k = rec.components;
  assert.equal(rec.new_references.length, 1, 'the new reference is missing');
  assert.equal(rec.discontinued_references.length, 1, 'the discontinued reference is missing');
  assert.equal(rec.returns.length, 1, 'the return line is missing');
  assert.notEqual(k.residual_eur, 0, 'the fixture no longer has a non-zero residual');
  assert.notEqual(k.mix_eur, null, 'mix must be separable with three compatible continuing references');

  assert.equal(rec.new_references[0].eur, k.new_eur);
  assert.equal(rec.discontinued_references[0].eur, k.discontinued_eur);
  assert.equal(rec.returns[0].eur, k.returns_eur);

  const sum = Math.round((k.price_eur + k.quantity_eur + k.mix_eur + k.new_eur
    + k.discontinued_eur + k.returns_eur + k.residual_eur) * 100) / 100;
  assert.equal(sum, c.comparisons.half.revenueDelta, 'the identity does not hold on the fixture');
  assert.equal(sum, rec.observed_change_eur);

  /* The residual is printed with its value, and named as unexplained. */
  assert.match(panelText(rec), new RegExp(String(k.residual_eur).replace('.', '\\.')));
  assert.match(rec.statement, /residual/i);

  /* The continuing references' euro change is reproduced exactly, and stated. */
  assert.equal(rec.continuing_check, rec.continuing_change_eur);
  assert.equal(rec.continuing_reconciles, true);
  assert.match(rec.statement, /add up to the continuing references/i);

  /* Every real case, both comparisons: the same identity on the real payload shape. */
  assert.equal(REAL_CASE_IDS.length, 5);
  for (const caseId of REAL_CASE_IDS) {
    const caseRec = REAL_SHAPE.cases.find((x) => x.id === caseId);
    for (const compare of COMPARES) {
      const r = decompose(caseRec, compare);
      assert.equal(r.available, true, caseId + '/' + compare + ': the block is not available');
      assert.equal(r.ok, true, caseId + '/' + compare + ': ' + r.statement);
      const kk = r.components;
      const total = Math.round((kk.price_eur + kk.quantity_eur
        + (kk.mix_eur === null ? 0 : kk.mix_eur) + kk.new_eur + kk.discontinued_eur
        + kk.returns_eur + kk.residual_eur) * 100) / 100;
      const moved = Math.round((caseRec.comparisons[compare].current.eur
        - caseRec.comparisons[compare].prior.eur) * 100) / 100;
      assert.equal(total, moved,
        caseId + '/' + compare + ': components plus residual do not equal the observed change');
      assert.equal(r.observed_change_eur, moved);
      /* Fewer than two compatible continuing references: mix unavailable, not faked. */
      if (r.continuing_count < 2) {
        assert.equal(kk.mix_eur, null,
          caseId + '/' + compare + ': a mix number was produced without two compatible references');
        assert.match(r.mix_state, /unavailable/);
      }
    }
  }
});

test('REVIEW-05 E3: a quantity-only reference invents no euro and is listed as not decomposed; a candidate shows no figure', () => {
  const c = COMP.cases[0];
  const rec = decompose(c, 'half');
  const noEuro = rec.not_decomposed.find((r) => r.pn === 'SYN-COMP-NOEURO');
  assert.ok(noEuro, 'the quantity-only reference is not in the not-decomposed list');
  assert.match(noEuro.reason, /no euro in the source/);
  assert.equal(Object.prototype.hasOwnProperty.call(noEuro, 'eur'), false,
    'a quantity-only reference carries an invented euro');
  assert.equal(rec.continuing.some((r) => r.pn === 'SYN-COMP-NOEURO'), false,
    'a quantity-only reference reached the compatible set');
  assert.equal(rec.new_references.some((r) => r.pn === 'SYN-COMP-NOEURO'), false);
  assert.equal(rec.discontinued_references.some((r) => r.pn === 'SYN-COMP-NOEURO'), false);

  const excluded = rec.not_decomposed.map((r) => r.pn + ' ' + r.reason).join(' | ');
  assert.match(excluded, /SYN-COMP-NOEURO/);
  assert.match(excluded, /no euro in the source/);
  assert.equal(/\d/.test(excluded), false,
    'a figure is printed beside the quantity-only reference');

  /* The screen lists it as not decomposed, with no figure. */
  const session = loadApp(COMP);
  openCase(session, c.id, 'decision', 'half');
  const html = session.doc.nodes.content.innerHTML;
  const list = (html.match(/data-pqm-not-decomposed="1"[\s\S]*?<\/(ul|p)>/) || [''])[0];
  assert.match(list, /SYN-COMP-NOEURO/, 'the not-decomposed list is not on the screen');
  assert.match(list, /no euro in the source/);
  assert.equal(/SYN-COMP-NOEURO[\s\S]{0,60}\d/.test(list), false,
    'the screen prints a figure beside the quantity-only reference');

  /* A candidate carries no period, so it has no comparison and no figure at all. */
  const noPeriod = { id: 'SYN-CAND-NOPERIOD', pn: 'SYN-CAND-NOPERIOD', relatedEvidence: [] };
  const cand = decompose(noPeriod, 'half');
  assert.equal(cand.available, false);
  assert.equal(cand.ok, false);
  assert.equal(cand.components.price_eur, null);
  assert.equal(cand.components.quantity_eur, null);
  assert.equal(cand.components.mix_eur, null);
  assert.equal(cand.components.residual_eur, null);
  assert.equal(String(cand.observed_change_eur), 'null');
  assert.match(cand.statement, /No comparison is held/i);
  assert.equal(panelText(cand).includes('NaN'), false);
});
