#!/usr/bin/env node
/* ===========================================================================
   UX-07 acceptance tests: make the complete task work on keyboard and small
   screens.

   How to run
     node --test tests/ux_07_keyboard_small.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (UX-07):

     E1  The selected question can be reviewed and a draft saved using the
         keyboard.
     E2  On the agreed small-screen layout, prices, units, scope and limitations
         remain readable without hidden essential controls.

   How the two are proved, and why they are proved differently
   -----------------------------------------------------------
   E1 is exercised twice. The synthetic test below drives the shipped layer
   through a stub document, which is enough to prove the controls are native
   elements, are labelled, are reachable in order, and that Enter on the save
   control writes the draft. The painted part of E1 - the order a real browser
   produces, and that the draft comes back after a reload - is measured in
   headless Chrome by tests/accept/ux_07_narrow.py, whose result this file reads.

   E2 is a layout verdict, and a layout cannot be judged from a stub: the rules
   that matter are @media queries, and a fake document evaluates none of them.
   The measurement is therefore made on the painted page by
   tests/accept/ux_07_narrow.py at 390 x 844 and 768 x 1024, against a real
   file:// URL in real Chrome. This file asserts the structure that makes the
   measurement meaningful (the maintained stylesheet is assembled, after the
   frozen styles, and the frozen reference is byte-for-byte the file the brief
   names) and then reads the measured result.

   The result is timestamped in that file; this test requires it to be newer than
   the artifact it describes, so a stale reading cannot pass as a current one.

   The fixture is tests/fixtures/ux_01_two_markets.json, the synthetic payload the
   other UX suites use. It already carries every control under test, so no second
   fixture is invented; the values are the invented ones it already holds. No
   restricted payload is read.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';
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
const FX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'ux_01_two_markets.json'), 'utf8'));

/* The artifact the measurement describes, and the measured result itself. */
const ARTIFACT = path.join(ROOT, 'dist', 'ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html');
const MEASURED = path.join(HERE, 'accept', '_out', 'ux_07_narrow.json');
const FROZEN = path.join(ROOT, 'reference', 'ISZE_AIM_Pricing_Decisions_v03_FROZEN.html');
const SHELL_NARROW = path.join(ROOT, 'src', 'shell', 'shell_narrow.css');

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

    /* A class selector. The UX-07 check asks for .tab and .case-card inside the
       painted markup, so the stub resolves a class against the shell it built. */
    const byClass = /^\.([\w-]+)$/.exec(selector);
    if (byClass) {
      const out = [];
      const re = new RegExp('class="[^"]*\\b' + byClass[1] + '\\b[^"]*"', 'g');
      while (re.exec(html)) {
        const key = selector + '|' + out.length;
        if (!derived[key]) derived[key] = stubElement(selector);
        out.push(derived[key]);
      }
      return out;
    }

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

/* The same read-side rewrites the other UX suites use. Each needle must match
   exactly once, so app.js changing shape fails this file loudly rather than
   silently testing nothing. */
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
  globalThis.localStorage = storage;
  const doc = makeFakeDocument();
  const sandbox = {
    __payload: FX,
    __dom: { $: (sel) => doc.querySelector(sel), $$: (sel) => doc.querySelectorAll(sel) },
    document: doc,
    localStorage: storage,
    location: { hash: '' },
    URLSearchParams, Intl, JSON, Math, Date, console,
    setTimeout: (fn) => { fn(); return 0; },
    clearTimeout,
    Blob: class { constructor(parts) { sandbox.__blob = parts; } },
    __blobBytes: () => new TextEncoder().encode(String((sandbox.__blob || [''])[0])),
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
  session.sandbox.location.hash = new URLSearchParams({ case: caseId, view, compare: 'half' }).toString();
  settle(session);
  return session.doc.nodes.content.innerHTML;
}

/* Fire one control, once. The stub keeps one element per id across renders, so
   addEventListener stacks a listener per paint and firing them all would run the
   handler several times - the trap the other UX suites record. Only the latest
   binding is the live one, so only it is called. */
function fire(el, type, init) {
  assert.ok(el, `nothing to fire "${type}" on`);
  const list = el._listeners[type] || [];
  const direct = type === 'click' ? el.onclick : type === 'change' ? el.onchange : null;
  assert.ok(list.length || direct, `no ${type} handler is bound to ${el.id || 'the element'}`);
  const event = Object.assign({ key: '', preventDefault() {} }, init || {});
  if (direct) direct.call(el, event);
  else list[list.length - 1](event);
}

const CASES = FX.cases.map((c) => c.id);
const ALL_TABS = ['decision', 'position', 'objectives', 'economics', 'candidates', 'action'];

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

/* The result of the painted measurement, or null when it has not been made. */
function measured() {
  if (!fs.existsSync(MEASURED)) return null;
  return JSON.parse(fs.readFileSync(MEASURED, 'utf8'));
}

/* =========================================================================
   E1 - the keyboard
   ========================================================================= */
test('UX-07 E1: the selected question can be reviewed and a draft saved using the keyboard', () => {
  const session = loadApp();
  const caseId = CASES[0];

  /* The controls UX-07 names are native elements a browser already knows how to
     reach and operate. A div with a click handler is not one of them. */
  const candidates = go(session, caseId, 'candidates');
  assert.ok(/<input[^>]*id="candidate-search"/.test(candidates),
    'the candidate search is not a native input');
  assert.ok(/<button[^>]*data-page=/.test(candidates), 'paging is not a native button');
  assert.ok(/<button[^>]*data-open-part=/.test(candidates),
    'the route from a row into its own part is not a native button');

  /* A table wider than its column scrolls sideways. For a keyboard reader that
     scroll box has to be reachable and has to say what it is; a wide table inside
     a wrapper the keyboard cannot enter is a control the reader does not have. */
  const everyView = ALL_TABS.map((v) => go(session, caseId, v)).join('\n');
  const wrappers = everyView.match(/class="tablewrap"[^>]*/g) || [];
  assert.ok(wrappers.length > 0, 'no table wrapper is painted on any view');
  for (const w of wrappers) {
    assert.ok(/tabindex="0"/.test(w), `a table wrapper is not in the tab order: ${w.slice(0, 80)}`);
    assert.ok(/aria-label="[^"]+"/.test(w), `a table wrapper has no accessible name: ${w.slice(0, 80)}`);
  }

  const decision = go(session, caseId, 'decision');
  assert.ok(/<select[^>]*id="comparison"/.test(decision),
    'the comparison period is not a native select');
  assert.ok(/<button[^>]*data-view=/.test(decision),
    'the route from a summary into another view is not a native button');

  const action = go(session, caseId, 'action');
  /* Every control the review needs, each a native element with a label bound by
     for=, so a screen reader announces what it is. */
  const needed = [['a-owner', 'input'], ['a-due', 'input'], ['a-status', 'select'],
                  ['a-next', 'input'], ['a-explanation', 'textarea'], ['a-note', 'textarea'],
                  ['a-outcome', 'textarea'], ['save-case', 'button'], ['export-json', 'button']];
  for (const [id, tag] of needed) {
    assert.ok(new RegExp(`<${tag}[^>]*id="${id}"`).test(action),
      `#${id} is not a native <${tag}> in the internal action view`);
  }
  for (const id of ['a-owner', 'a-due', 'a-status', 'a-next', 'a-explanation', 'a-note', 'a-outcome']) {
    assert.ok(new RegExp(`<label[^>]*for="${id}"`).test(action),
      `#${id} has no programmatic label`);
  }
  assert.ok(!/<div[^>]*onclick=/.test(action), 'a div carries an inline click handler');
  assert.ok(!/<span[^>]*onclick=/.test(action), 'a span carries an inline click handler');

  /* Tab order: the markup order of the controls a keyboard reader walks matches
     the order the review is read in. Measured, not assumed. */
  const order = needed.map(([id]) => action.indexOf(`id="${id}"`));
  assert.ok(order.every((p) => p >= 0), 'a control is missing from the markup');
  for (let i = 1; i < order.length; i++) {
    assert.ok(order[i] > order[i - 1],
      `the markup order puts ${needed[i][0]} before ${needed[i - 1][0]}`);
  }

  /* Space or Enter on a focused control does what a click does. The save control
     is a button, so the browser's own activation sends a click; this fires the
     same event the browser would and requires the draft to be written.

     The count is read before and after, because a case may already carry a
     revision: a save that wrote nothing must not pass as one that did. The entry
     is made distinctive for the same reason. */
  const before = session.api.cases.load(caseId);
  const beforeCount = before ? before.revisions.length : 0;
  const marker = 'UX-07 E1: reviewed and saved from the keyboard, ' + Date.now();
  session.doc.querySelector('#a-next').value = marker;
  session.doc.querySelector('#a-note').value = marker;
  const save = session.doc.querySelector('#save-case');
  fire(save, 'click');
  const rec = session.api.cases.load(caseId);
  assert.ok(rec, 'the draft was not written by activating the save control');
  assert.equal(rec.revisions.length, beforeCount + 1,
    `activating the save control recorded ${rec.revisions.length - beforeCount} revision(s), not one`);
  const lastSaved = rec.revisions[rec.revisions.length - 1].record;
  assert.equal((lastSaved.review || {}).next_action, marker,
    'the revision that was written does not carry what the keyboard typed');

  /* The outcome is carried by text, not by colour alone: the status line says in
     words what happened, and it names the revision. */
  const status = session.doc.querySelector('#save-status');
  assert.ok(status && /revision/i.test(status.textContent),
    'the save status does not state the outcome in words: ' + JSON.stringify(status && status.textContent));

  /* The tabs are native buttons too, so a keyboard reader reaches every view. */
  const tabsBar = session.doc.nodes.tabs.innerHTML;
  /* The bar paints the six worked views plus the selected-part review, so the
     count is asserted as a floor: seven is expected here and six is the minimum
     a keyboard reader is entitled to. */
  const tabCount = (tabsBar.match(/<button[^>]*class="tab/g) || []).length;
  assert.ok(tabCount >= ALL_TABS.length,
    `the tab bar paints ${tabCount} native buttons, fewer than the ${ALL_TABS.length} views`);

  return `${needed.length} review controls are native and labelled; activation writes revision `
    + `${rec.revisions.length} (from ${beforeCount}); the status line states it in words; `
    + `${tabCount} tabs are buttons; `
    + `${wrappers.length} scrolling table wrapper(s) are in the tab order and named`;
});

/* =========================================================================
   E2 - the agreed small-screen layout
   ========================================================================= */
test('UX-07 E2: on the small-screen layout prices, units, scope and limitations stay readable with no hidden essential controls', () => {
  /* 1. The maintained stylesheet is assembled, and after the frozen styles. */
  assert.ok(fs.existsSync(SHELL_NARROW), 'src/shell/shell_narrow.css is missing');
  assert.ok(fs.existsSync(ARTIFACT), 'the built artifact is missing; run tools/build.py first');
  const built = fs.readFileSync(ARTIFACT, 'utf8');
  const frozenAt = built.indexOf('</head>');
  const narrowAt = built.indexOf('<style id="shell-narrow">');
  assert.ok(narrowAt >= 0, 'the artifact carries no <style id="shell-narrow"> block');
  assert.ok(narrowAt < frozenAt, 'the shell-narrow block is not inside <head>');
  const frozenStylesEnd = built.lastIndexOf('</style>', narrowAt);
  assert.ok(frozenStylesEnd >= 0 && frozenStylesEnd < narrowAt,
    'the shell-narrow block does not come after the frozen styles');
  const build = fs.readFileSync(path.join(ROOT, 'tools', 'build.py'), 'utf8');
  assert.ok(build.includes('SHELL_NARROW') && build.includes('shell_narrow_sha256'),
    'tools/build.py no longer assembles the narrow stylesheet or reports its hash');
  const report = JSON.parse(fs.readFileSync(path.join(ROOT, 'dist', '_build_report.json'), 'utf8'));
  assert.equal(report.shell_narrow_sha256, sha256(SHELL_NARROW),
    'the build report does not carry the hash of the stylesheet that was assembled');

  /* 2. The frozen reference is byte-for-byte the file the brief names. */
  const frozenSha = sha256(FROZEN).toUpperCase();
  assert.equal(frozenSha, '7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14',
    'the frozen v03 reference is no longer byte-for-byte the original artifact');

  /* 3. The measured result: no failure at either agreed viewport, and no reading
        older than the artifact it describes. */
  const measuredNow = measured();
  assert.ok(measuredNow, 'tests/accept/ux_07_narrow.py has not been run; there is no reading to read');
  const artifactStat = fs.statSync(ARTIFACT).mtimeMs;
  assert.ok(measuredNow.artifact_mtime && (measuredNow.artifact_mtime || '') !== '',
    'the reading does not record which artifact it measured');
  const readThrough = Date.parse(measuredNow.artifact_mtime);
  assert.ok(readThrough >= artifactStat - 2000,
    `the reading is older than the artifact: reading ${measuredNow.artifact_mtime}, artifact `
    + `${new Date(artifactStat).toISOString()}`);
  assert.equal(measuredNow.artifact_sha256, sha256(ARTIFACT),
    'the reading describes a different artifact than the one on disk');

  const byCheck = measuredNow.by_check || {};
  assert.deepEqual(Object.keys(byCheck).sort(), ['a', 'b', 'c', 'd', 'e1'],
    'the reading does not carry all four narrow checks and the keyboard walk');
  for (const key of ['a', 'b', 'c', 'd', 'e1']) {
    assert.equal(byCheck[key].fail, 0,
      `check ${key} reports ${byCheck[key].fail} failure(s) at the agreed viewports`);
  }
  assert.equal(measuredNow.summary.fail, 0, 'the reading reports failures');
  assert.ok(byCheck.a.pass > 0 && byCheck.b.pass > 0 && byCheck.c.pass > 0 && byCheck.d.pass > 0,
    'a check reports no measurement at all, which is not a pass');

  const widths = (measuredNow.viewports || []).filter((v) => ['phone', 'tablet'].includes(v.label))
    .map((v) => v.width);
  assert.deepEqual(widths.sort((x, y) => x - y), [390, 768],
    'the reading was not taken at the two agreed widths');

  /* 4. The essential controls were each actually found, at both widths. */
  const seen = new Set();
  for (const r of measuredNow.results || []) {
    if (!['phone', 'tablet'].includes(r.viewport)) continue;
    for (const e of r.essentials || []) {
      if (e.status !== 'FAIL') seen.add(e.name);
    }
  }
  for (const name of ['customer selector', 'case list', 'case card', 'tab', 'export button',
                      'sources button', 'save draft', 'recalculate: proposed net price',
                      'recalculate: reset control']) {
    assert.ok(seen.has(name), `the measurement never found an essential control: ${name}`);
  }

  /* 5. Nothing was hidden to make it fit. */
  const hidden = (measuredNow.superset || []).filter((s) => s.status === 'FAIL');
  assert.equal(hidden.length, 0,
    'a fact the wide page carries is missing at a narrow width: ' + JSON.stringify(hidden.slice(0, 2)));

  return `stylesheet sha256 ${report.shell_narrow_sha256.slice(0, 16)} assembled after the frozen styles; `
    + `frozen reference ${frozenSha.slice(0, 16)} unchanged; the reading at 390 and 768 reports `
    + `${measuredNow.summary.pass} pass / 0 fail across checks a-d and the keyboard walk`;
});
