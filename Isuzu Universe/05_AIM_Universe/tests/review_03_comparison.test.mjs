#!/usr/bin/env node
/* ===========================================================================
   REVIEW-03 acceptance tests: selectable comparison visible everywhere.

   How to run
     node --test tests/review_03_comparison.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (REVIEW-03):
     E1  Changing period updates the observed comparison but never silently
         changes offer-date assumptions.
     E2  No case exports a different comparison from the one selected.

   Pattern: tests/ux_01_context.test.mjs and tests/ux_02_alternative.test.mjs.
   Data: tests/fixtures/review_03_five_cases.json (invented values only).
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
const APP = path.join(ROOT, 'src/ui/app.js');

const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_03_five_cases.json'), 'utf8'));
const CASE_IDS = FX.cases.map((c) => c.id);
const COMPARES = ['half', 'annual'];

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

function offerDateFingerprint(session) {
  const s = session.api.getScenario();
  const st = session.api.getState();
  const meta = session.api.currentMetadata
    ? session.api.currentMetadata(session.api.data.cases.find((c) => c.id === st.caseId))
    : null;
  return JSON.stringify({
    scenario_offer: s.offer_effective_date,
    state_offer: st.offerDate,
    meta_offer: meta ? meta.offer_effective_date : null,
    html_offer_bits: [
      session.doc.nodes.content.innerHTML.match(/Offer effective date[\s\S]{0,120}/)?.[0] || '',
      session.doc.nodes.content.innerHTML.match(/offer from [^<]*/)?.[0] || '',
      session.doc.nodes.content.innerHTML.match(/id="s-date"[^>]*/)?.[0] || '',
      session.doc.nodes.content.innerHTML.match(/id="offerDate"[^>]*/)?.[0] || ''
    ]
  });
}

function observedFigures(session) {
  assert.equal(typeof session.api.getObservedComparison, 'function',
    'AIMPricing.getObservedComparison is missing');
  return session.api.getObservedComparison();
}

function exportText(session) {
  assert.equal(typeof session.api.exportReviewText, 'function',
    'AIMPricing.exportReviewText is missing');
  return session.api.exportReviewText();
}

test('REVIEW-03 E1: changing period updates observed figures and leaves every offer-date field byte-identical', () => {
  const session = loadApp();
  assert.equal(CASE_IDS.length, 5);

  for (const caseId of CASE_IDS) {
    const caseRec = FX.cases.find((c) => c.id === caseId);
    openCase(session, caseId, 'decision', 'half');
    session.api.setScenario({ offer_effective_date: '2026-11-15' });
    settle(session);
    openCase(session, caseId, 'economics', 'half');

    const offerHalf = offerDateFingerprint(session);
    const figHalf = observedFigures(session);
    assert.equal(figHalf.compare, 'half');
    assert.equal(figHalf.label, caseRec.comparisons.half.label);
    assert.equal(figHalf.prior.eur, caseRec.comparisons.half.prior.eur);
    assert.equal(figHalf.current.eur, caseRec.comparisons.half.current.eur);
    assert.equal(figHalf.revenueDelta, caseRec.comparisons.half.revenueDelta);

    openCase(session, caseId, 'economics', 'annual');
    const offerAnnual = offerDateFingerprint(session);
    const figAnnual = observedFigures(session);
    assert.equal(figAnnual.compare, 'annual');
    assert.equal(figAnnual.label, caseRec.comparisons.annual.label);
    assert.equal(figAnnual.prior.eur, caseRec.comparisons.annual.prior.eur);
    assert.equal(figAnnual.current.eur, caseRec.comparisons.annual.current.eur);
    assert.equal(figAnnual.revenueDelta, caseRec.comparisons.annual.revenueDelta);

    assert.notEqual(figHalf.revenueDelta, figAnnual.revenueDelta,
      caseId + ': half and annual revenue deltas are identical, so the period switch is not observable');
    assert.notDeepEqual(
      { p: figHalf.prior.quantity, c: figHalf.current.quantity },
      { p: figAnnual.prior.quantity, c: figAnnual.current.quantity },
      caseId + ': quantity figures did not change with the period');
    assert.equal(offerAnnual, offerHalf,
      caseId + ': an offer-date field moved when only the comparison period changed');

    /* Case cards and scope strip follow the selected comparison, not the hidden default. */
    assert.match(session.doc.nodes['scope-strip'].innerHTML, new RegExp(figAnnual.label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    assert.match(session.doc.nodes['case-list'].innerHTML, /Calendar 2025 vs 2024|Full year/);
  }

  /* Candidate / original-part review: no period is inferred. */
  const opened = session.api.openPart('SYN-CAND-NOPERIOD');
  assert.equal(opened.ok, true);
  settle(session);
  const html = session.doc.nodes.content.innerHTML;
  assert.match(html, /unavailable:\s*the candidate records carry no period/i);
  assert.doesNotMatch(html, /January-June 2026 vs 2025/);
  assert.doesNotMatch(html, /Calendar 2025 vs 2024/);
});

test('REVIEW-03 E2: exported review states the same comparison and the same figures as the screen', () => {
  const session = loadApp();

  for (const caseId of CASE_IDS) {
    for (const compare of COMPARES) {
      const caseRec = FX.cases.find((c) => c.id === caseId);
      const expected = caseRec.comparisons[compare];
      openCase(session, caseId, 'decision', compare);
      const screen = observedFigures(session);
      assert.equal(screen.compare, compare);
      assert.equal(screen.label, expected.label);
      assert.equal(screen.prior.eur, expected.prior.eur);
      assert.equal(screen.current.eur, expected.current.eur);
      assert.equal(screen.revenueDelta, expected.revenueDelta);

      const text = exportText(session);
      assert.match(text, /data-export-compare="/);
      const exportedCompare = (text.match(/data-export-compare="([^"]+)"/) || [])[1];
      const exportedLabel = (text.match(/data-export-label="([^"]+)"/) || [])[1];
      const exportedPrior = Number((text.match(/data-export-prior-eur="([^"]+)"/) || [])[1]);
      const exportedCurrent = Number((text.match(/data-export-current-eur="([^"]+)"/) || [])[1]);
      const exportedDelta = Number((text.match(/data-export-revenue-delta="([^"]+)"/) || [])[1]);

      assert.equal(exportedCompare, screen.compare, caseId + '/' + compare + ': export compare differs');
      assert.equal(exportedLabel, screen.label, caseId + '/' + compare + ': export label differs');
      assert.equal(exportedPrior, screen.prior.eur, caseId + '/' + compare + ': export prior eur differs');
      assert.equal(exportedCurrent, screen.current.eur, caseId + '/' + compare + ': export current eur differs');
      assert.equal(exportedDelta, screen.revenueDelta, caseId + '/' + compare + ': export delta differs');

      /* Must not dump the other comparison's label as a measured row. */
      const other = compare === 'half' ? 'annual' : 'half';
      const otherLabel = caseRec.comparisons[other].label;
      assert.equal(text.includes(otherLabel), false,
        caseId + '/' + compare + ': export still contains the unselected comparison label');
    }
  }
});
