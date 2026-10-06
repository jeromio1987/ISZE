#!/usr/bin/env node
/* ===========================================================================
   REVIEW-08 acceptance tests: supported new reviews beyond the five examples.

   How to run
     node --test tests/review_08_new_review.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (REVIEW-08):
     E1  A supported part outside the five worked examples opens a review and
         then a linked draft case (period stated by the reviewer).
     E2  An incomplete candidate opens a visibly narrower review and never
         borrows another case's cost, fleet, application or competitors.

   Pattern: tests/case_08_queue.test.mjs (draft / identity) plus the app harness
   shape from tests/review_03_comparison.test.mjs.
   Data: tests/fixtures/review_08_new_review.json (five cases retained; candidate
   rows only). The restricted payload is never read here.
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

const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'review_08_new_review.json'), 'utf8'));
const CASE_IDS = FX.cases.map((c) => c.id);
const SUPPORTED = FX.candidateScreen.find((r) =>
  r.distributor === 'PORTUGAL' && r.part_number === '8982447940');
const INCOMPLETE = FX.candidateScreen.find((r) =>
  r.distributor === 'PORTUGAL' && r.part_number === 'SYN-PN-INCOMPLETE-08');

assert.ok(SUPPORTED, 'fixture is missing the supported PORTUGAL pads candidate');
assert.ok(INCOMPLETE, 'fixture is missing the incomplete PORTUGAL candidate');
assert.equal(CASE_IDS.includes('PORTUGAL-8982447940'), false);
assert.equal(CASE_IDS.some((id) => id.startsWith('CAND-PORTUGAL-')), false);

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

function fiveCaseBorrowTokens() {
  const tokens = [];
  for (const c of FX.cases) {
    tokens.push('FLEET-MARKER-' + c.id);
    tokens.push('APP-MARKER-' + c.id);
    tokens.push('COMP-MARKER-' + c.id);
    tokens.push('COST-MARKER-' + c.id);
    const cost = (c.costParts && c.costParts[0] && c.costParts[0].cost_eur);
    if (cost !== undefined && cost !== null) tokens.push(String(cost));
    if (c.fleet && c.fleet.uio !== undefined) tokens.push(String(c.fleet.uio));
    if (c.application) tokens.push(String(c.application));
  }
  return tokens;
}

test('REVIEW-08 E1: a supported candidate outside the five cases opens a review and a linked draft case with a reviewer-stated period', () => {
  const session = loadApp();
  assert.equal(CASE_IDS.length, 5, 'the five cases must remain as regression examples');
  assert.deepEqual(session.api.data.cases.map((c) => c.id).sort(), [...CASE_IDS].sort());

  assert.equal(typeof session.api.openCandidateRow, 'function',
    'AIMPricing.openCandidateRow is missing');
  assert.equal(typeof session.api.promoteCandidateToCase, 'function',
    'AIMPricing.promoteCandidateToCase is missing');

  /* Same part number as ITUK-PADS, different distributor — must not steal the case. */
  const opened = session.api.openCandidateRow('PORTUGAL', '8982447940');
  settle(session);
  assert.equal(opened.ok, true, opened.error || 'openCandidateRow failed');
  assert.equal(opened.view, 'case');
  assert.equal(opened.distributor, 'PORTUGAL');
  assert.equal(opened.part_number, '8982447940');
  assert.notEqual(session.api.getState().caseId, 'ITUK-PADS',
    'opening the PORTUGAL pads candidate stole the ITUK-PADS case');
  assert.equal(session.api.getState().view, 'case');
  const reviewHtml = session.doc.nodes.content.innerHTML;
  assert.match(reviewHtml, /PORTUGAL/);
  assert.match(reviewHtml, /8982447940/);
  assert.doesNotMatch(reviewHtml, /Open case ITUK-PADS/,
    'the PORTUGAL candidate review offered the ITUK worked case');

  const check = candidateModule.promotionBlockers(SUPPORTED, FX, {
    basis: candidateModule.reviewerStatedBasis
      ? candidateModule.reviewerStatedBasis('H1 2026 (stated for the test)')
      : { declared: true, period: 'H1 2026 (stated for the test)', period_state: 'stated by reviewer' }
  });
  assert.equal(check.promotable, true, check.statement);

  const promoted = session.api.promoteCandidateToCase({
    distributor: 'PORTUGAL',
    part_number: '8982447940',
    evidence_period: 'H1 2026 (stated for the test)'
  });
  settle(session);
  assert.equal(promoted.ok, true, promoted.error || promoted.statement || 'promote failed');
  assert.equal(promoted.created, true);
  assert.ok(promoted.case_id, 'no draft case id was returned');
  assert.equal(CASE_IDS.includes(promoted.case_id), false,
    'the draft reused a worked case id');
  assert.equal(promoted.evidence_period, 'H1 2026 (stated for the test)');
  assert.equal(promoted.evidence_period_state, 'stated by reviewer');
  assert.match(String(promoted.evidence_period_label || promoted.evidence_period_state || ''),
    /stated by reviewer/i);

  const linkedHtml = session.doc.nodes.content.innerHTML;
  assert.match(linkedHtml, new RegExp(promoted.case_id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  assert.match(linkedHtml, /stated by reviewer/i);
  assert.match(linkedHtml, /Period basis[\s\S]*stated by reviewer/i);
  assert.match(linkedHtml, /unavailable: the candidate records carry no period/i);

  const stored = session.api.cases.load(promoted.case_id);
  assert.ok(stored, 'the linked draft case was not stored');
  assert.equal(stored.part_number, '8982447940');
  assert.equal(stored.customer, 'PORTUGAL');
  assert.equal(stored.evidence_period, 'H1 2026 (stated for the test)');

  /* Five cases remain untouched. */
  assert.deepEqual(session.api.data.cases.map((c) => c.id).sort(), [...CASE_IDS].sort());
});

test('REVIEW-08 E2: an incomplete candidate opens a narrower review and never borrows another case\'s cost, fleet, application or competitors', () => {
  const session = loadApp();
  assert.equal(typeof session.api.openCandidateRow, 'function',
    'AIMPricing.openCandidateRow is missing');

  const opened = session.api.openCandidateRow('PORTUGAL', 'SYN-PN-INCOMPLETE-08');
  settle(session);
  assert.equal(opened.ok, true, opened.error || 'openCandidateRow failed');
  assert.equal(opened.view, 'case');
  assert.equal(session.api.getState().view, 'case');

  const html = session.doc.nodes.content.innerHTML;
  assert.match(html, /narrower|incomplete|not promotable|missing/i,
    'the incomplete review does not say it is narrower or incomplete');
  assert.match(html, /SYN-PN-INCOMPLETE-08/);
  assert.match(html, /PORTUGAL/);
  assert.match(html, /NO_COMPETITOR_EVIDENCE|competitor evidence/i);

  const blocked = session.api.promoteCandidateToCase({
    distributor: 'PORTUGAL',
    part_number: 'SYN-PN-INCOMPLETE-08',
    evidence_period: 'H1 2026 (stated for the test)'
  });
  assert.equal(blocked.ok, false, 'an incomplete candidate created a draft case');
  assert.equal(blocked.created, false);

  const tokens = fiveCaseBorrowTokens();
  for (const token of tokens) {
    assert.equal(html.includes(token), false,
      'incomplete review borrowed another case value: ' + token);
  }
  for (const c of FX.cases) {
    assert.doesNotMatch(html, new RegExp('Open case ' + c.id));
  }
});
