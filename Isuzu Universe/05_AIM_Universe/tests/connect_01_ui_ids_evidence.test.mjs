#!/usr/bin/env node
/* ===========================================================================
   CONNECT-01 UI: IDS evidence panel painted in the product case view.

   How to run
     node --test tests/connect_01_ui_ids_evidence.test.mjs

   Titles start CONNECT-01 UI. Synthetic dealers and a synthetic IDS sheet only.
   Real IDS workbooks are never read. The panel must use AIMIdsEvidence output;
   it must not recompute answers in the view.
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
const ids = require(path.join(ROOT, 'src/data/ids_evidence.js'));
const APP = path.join(ROOT, 'src/ui/app.js');

const SHEET = {
  rows: [
    {
      dealer_id: 'SYN-UMI-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-UMI',
      local_question_code: 'Q12',
      question_text: 'Synthetic parts handling readiness',
      answer_state: 'answered',
      answer: 'good',
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UMI-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-UMI',
      local_question_code: 'Q13',
      question_text: 'Synthetic workshop capacity',
      answer_state: 'answered',
      answer: 'fair',
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UNVAL-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-UMI',
      local_question_code: 'Q12',
      question_text: 'Hidden until identity is validated',
      answer_state: 'answered',
      answer: 'hidden',
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UTI-LOOKALIKE',
      distributor: 'UTI',
      questionnaire_version: 'IDS-2026-FAKE',
      local_question_code: 'Q12',
      question_text: 'Should never surface for UTI in 2026',
      answer_state: 'answered',
      answer: 'should-not-appear',
      date_or_round: '2026-R1'
    }
  ]
};

const VALIDATED_UMI = {
  dealer_id: 'SYN-UMI-01',
  distributor: 'UMI',
  display_name: 'Synthetic UMI Dealer',
  validated: true
};
const UNVALIDATED = {
  dealer_id: 'SYN-UNVAL-01',
  distributor: 'UMI',
  display_name: 'Synthetic Unvalidated Dealer',
  validated: false
};
const UTI_DEALER = {
  dealer_id: 'SYN-UTI-LOOKALIKE',
  distributor: 'UTI',
  display_name: 'Synthetic UTI Look-alike',
  validated: true
};
const UNKNOWN = { unknown: true };

function basePayload() {
  return JSON.parse(fs.readFileSync(
    path.join(HERE, 'fixtures', 'review_05_mix_shift.json'), 'utf8'));
}

function cloneCase(src, id, identity) {
  const c = JSON.parse(JSON.stringify(src));
  c.id = id;
  c.ids_identity = identity;
  return c;
}

function payloadForIds() {
  const p = basePayload();
  const proto = p.cases[0];
  p.ids_sheet = SHEET;
  p.cases = [
    cloneCase(proto, 'ITUK-PADS', VALIDATED_UMI),
    cloneCase(proto, 'IMOTORS-CABIN', UNVALIDATED),
    cloneCase(proto, 'ITUK-TURBO', UTI_DEALER),
    cloneCase(proto, 'ITUK-DISCS', UNKNOWN)
  ];
  return p;
}

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
    AIMComparable: comparableModule, AIMIdsEvidence: ids
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

function panelHtml(session) {
  return session.doc.nodes.content.innerHTML || '';
}

function answerLis(html) {
  const section = /data-connect-01="panel"[\s\S]*?<\/section>/.exec(html);
  if (!section) return [];
  const lis = [...section[0].matchAll(/<li\b[^>]*>([\s\S]*?)<\/li>/g)].map((m) => m[1]);
  return lis;
}

test('CONNECT-01 UI: validated dealer shows its answers in the rendered case view', () => {
  const session = loadApp(payloadForIds());
  openCase(session, 'ITUK-PADS', 'decision', 'half');
  const html = panelHtml(session);
  assert.match(html, /data-connect-01="panel"/, 'IDS panel missing from the decision view');
  assert.match(html, /Synthetic UMI Dealer/);
  assert.match(html, /data-identity-state="validated"/);
  const lis = answerLis(html);
  assert.ok(lis.length >= 2, `expected answer rows, got ${lis.length}`);
  assert.ok(lis.some((t) => /Synthetic parts handling readiness/.test(t) && /good/.test(t)));
  assert.equal(html.includes('should-not-appear'), false);
});

test('CONNECT-01 UI: unvalidated dealer shows identity not validated and zero answer rows', () => {
  const session = loadApp(payloadForIds());
  openCase(session, 'IMOTORS-CABIN', 'decision', 'half');
  const html = panelHtml(session);
  assert.match(html, /data-connect-01="panel"/);
  assert.match(html, /identity not validated/i);
  assert.match(html, /data-identity-state="not_validated"/);
  assert.equal(answerLis(html).length, 0, 'unvalidated dealer must show zero answer rows');
  assert.equal(html.includes('hidden'), false);
});

test('CONNECT-01 UI: a UMI case never renders a UTI answer and a UTI case renders none from the IDS sheet', () => {
  const session = loadApp(payloadForIds());
  openCase(session, 'ITUK-PADS', 'decision', 'half');
  const umi = panelHtml(session);
  assert.match(umi, /data-identity-state="validated"/);
  assert.equal(umi.includes('should-not-appear'), false);
  assert.equal(umi.includes('SYN-UTI-LOOKALIKE'), false);

  openCase(session, 'ITUK-TURBO', 'decision', 'half');
  const uti = panelHtml(session);
  assert.match(uti, /data-connect-01="panel"/);
  assert.match(uti, /data-identity-state="excluded_from_population"/);
  assert.equal(answerLis(uti).length, 0);
  assert.equal(uti.includes('should-not-appear'), false);
  assert.equal(uti.includes('Synthetic parts handling readiness'), false);
});

test('CONNECT-01 UI: unknown identity stays unknown and does not reuse the previous case panel', () => {
  const session = loadApp(payloadForIds());
  openCase(session, 'ITUK-PADS', 'decision', 'half');
  const first = panelHtml(session);
  assert.match(first, /Synthetic UMI Dealer/);
  assert.ok(answerLis(first).length >= 2);

  openCase(session, 'ITUK-DISCS', 'decision', 'half');
  const second = panelHtml(session);
  assert.match(second, /data-connect-01="panel"/);
  assert.match(second, /data-identity-state="unknown"/);
  assert.match(second, /identity unknown/i);
  assert.equal(answerLis(second).length, 0);
  assert.equal(second.includes('Synthetic UMI Dealer'), false);
  assert.equal(second.includes('Synthetic parts handling readiness'), false);
  assert.equal(second.includes('good'), false);
});
