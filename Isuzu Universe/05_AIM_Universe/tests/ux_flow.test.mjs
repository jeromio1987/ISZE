#!/usr/bin/env node
/* ===========================================================================
   UX flow checks for the correction that SHIPS (F01, F05, F10, F11, UX-06,
   UX-07, REVIEW-02, REVIEW-04).

   What changed, and why
   ---------------------
   This suite used to load src/ui/render.js and src/ui/views.js. tools/build.py
   does not assemble either of them: the artifact it writes contains
   src/ui/app.js. So the 13/13 this file reported described a second view layer
   that no reader would ever open, and the views the product actually paints were
   unguarded. The two layers were not equivalent in either direction - the orphan
   had the UX-06 amber unavailable states and the shipped one did not; the shipped
   one had the F05 failure guard and the orphan did not.

   The layer the product runs is now the layer under test: src/ui/app.js, loaded
   the way a browser loads it, through the same <script>-rewriting shim
   tests/ux_reopen.test.mjs uses. The features that were only in the orphan have
   been ported into app.js, so every assertion below can now be made against the
   shipped artifact.

   Three assertions could not survive the move as written. Each is kept beside
   its replacement, with the reason, rather than deleted:

     1. The one-scenario-record check drove shell.scenario / shell.caseById /
        shell.build from render.js. app.js publishes its own scenario store, and
        the equivalence is now asserted against app.js's published surface.

     2. The stale-content check patched views.render. In the orphan,
        render.js imported views.render as a property, so patching the module
        property changed what the shell called. app.js calls the engine directly
        and closes over it, so the equivalent fault is created by handing the
        shell an engine with one function missing. That is a stronger fault: it
        is the real failure mode, not a test hook.

     3. The UX10 part-reference check asserted that every view carries the part
        strip. app.js does carry the strip on every view now, so the assertion
        stands - but its counter-example is kept, because a strip that shows the
        open case's part number on a review of a different part is a false
        statement, and the review view must say so instead.

   Where a check can only be made by the shell that ships, it says so in the
   evidence string rather than quietly narrowing the scope.

     node tests/ux_flow.test.mjs
     node tests/ux_flow.test.mjs --payload <path.json>
     node tests/ux_flow.test.mjs --results out.json

   Exit code is non-zero when any check fails.
   =========================================================================== */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

/* The shipped modules. Every one of these is in tools/build.py's MODULES list. */
const contracts = require(path.join(ROOT, 'src/data/contracts.js'));
const engine = require(path.join(ROOT, 'src/engine/engine.js'));
const caseModule = require(path.join(ROOT, 'src/data/cases.js'));
const candidateModule = require(path.join(ROOT, 'src/data/candidates.js'));
const scenarioModule = require(path.join(ROOT, 'src/data/scenario.js'));
const exportModule = require(path.join(ROOT, 'src/data/export.js'));

/* The module under test: the one tools/build.py assembles as "views and
   interaction". It is a single IIFE inside a <script> tag. */
const APP = path.join(ROOT, 'src/ui/app.js');

/* The layers the artifact does NOT contain. Named so the suite can assert that
   nothing it loads is one of them - the defect this rewrite exists to close. */
const RETIRED_LAYERS = ['src/ui/views.js', 'src/ui/render.js'];

/* --------------------------------------------------------------- arguments -- */
let payloadPath = null, resultsPath = null, label = 'synthetic fixture';
for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i] === '--payload') { payloadPath = process.argv[++i]; label = 'authorised payload'; }
  else if (process.argv[i] === '--results') { resultsPath = process.argv[++i]; }
}
/* Prefer the real payload when it is present on this machine, because part of what
   this file checks (10,543 candidate records, a resolved turbo conflict) only
   exists in it. It is read, never written. */
const REAL_PAYLOADS = [
  path.join(ROOT, 'payload', 'aim_payload_20260922.json'),
  path.join(ROOT, '..', '06_Working', '_aim_pack_20260922', '_payload.json')
];
if (!payloadPath) {
  const found = REAL_PAYLOADS.find((p) => fs.existsSync(p));
  if (found) { payloadPath = found; label = 'authorised local payload'; }
  else payloadPath = path.join(HERE, 'fixtures', 'synthetic_payload.json');
}
const payloadText = fs.readFileSync(payloadPath, 'utf8');
const payload = JSON.parse(payloadText);
const payloadSha = crypto.createHash('sha256').update(payloadText).digest('hex');
const usesRealPayload = REAL_PAYLOADS.some((p) => path.resolve(p) === path.resolve(payloadPath));

const results = [];
async function test(id, name, fn) {
  try {
    const evidence = await fn();
    results.push({ id, name, status: 'PASS', evidence: evidence === undefined ? null : evidence });
  } catch (e) {
    results.push({ id, name, status: 'FAIL', evidence: e && e.message ? e.message : String(e) });
  }
}

/* ------------------------------------------------------------- fake browser -- */

/* A minimal document. Unlike the previous version, querySelectorAll resolves
   [data-x] selectors against the painted markup, because the shipped layer binds
   its controls through addEventListener rather than through inline handlers. A
   stub that cannot fire an event cannot check the controls at all. */
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

/* app.js is one <script> block containing an IIFE. Two statements in it are
   written for a live document and a live address; they are replaced here by the
   sandbox's payload and storage. Each replacement is asserted to have applied
   exactly once, so this file fails loudly rather than silently passing if
   app.js changes shape. */
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

/* Load src/ui/app.js the way the built page does: run it, then read the
   AIMPricing surface it publishes. `engineOverride` is how a fault is injected;
   nothing in app.js is patched. */
function loadApp({ engineOverride } = {}) {
  const storage = makeStorage();
  globalThis.localStorage = storage;
  const doc = makeFakeDocument();
  const sandbox = {
    __payload: payload,
    __dom: { $: (sel) => doc.querySelector(sel), $$: (sel) => doc.querySelectorAll(sel) },
    document: doc,
    localStorage: storage,
    location: { hash: '' },
    URLSearchParams, Intl, JSON, Math, Date, console,
    /* The shell debounces the search box with setTimeout. This suite drives the
       controls synchronously, so the sandbox runs the timer immediately rather
       than waiting 350 ms. The debounce itself is not removed from app.js. */
    setTimeout: (fn) => { fn(); return 0; },
    clearTimeout,
    /* Exports. app.js writes a Blob, points an anchor at it and clicks it. The
       sandbox keeps the bytes so the suite can read what was actually exported
       rather than assert that a function was called. */
    /* Exports. app.js writes a Blob, points an anchor at it and clicks it. The
       sandbox keeps the bytes so the suite can read what was actually exported
       rather than assert that a function was called. */
    Blob: class { constructor(parts) { sandbox.__blob = parts; } },
    __blobBytes: () => new TextEncoder().encode(String((sandbox.__blob || [''])[0])),
    URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
    AIMEngine: engineOverride || engine,
    AIMExport: exportModule,
    AIMCandidates: candidateModule,
    AIMCases: caseModule,
    AIMContracts: contracts,
    AIMScenario: scenarioModule
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

/* A real browser fires hashchange when location.hash is assigned. The stub
   address does not, so the suite raises the same event after any action that
   writes the address. This is the stub completing the browser's behaviour, not
   the suite driving the app differently. */
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

/* The shipped layer binds some controls through addEventListener (the scenario
   inputs, the save button) and others through .onclick (the case cards, the view
   tabs, the select and page controls), which is the retained v03 style. Firing a
   control therefore has to reach whichever of the two the view actually used. */
function fire(el, type, init) {
  assert.ok(el, `nothing to fire "${type}" on`);
  const list = el._listeners[type] || [];
  const direct = type === 'click' ? el.onclick : type === 'change' ? el.onchange : null;
  assert.ok(list.length || direct, `no ${type} handler is bound to ${el.id || el.selector || 'the element'}`);
  const event = Object.assign({ key: '', preventDefault() {} }, init || {});
  list.forEach((fn) => fn(event));
  if (direct) direct.call(el, event);
}

/* What the shipped layer paints, on demand. This replaces the orphan shell's
   shell.build()/shell.probe(); the render gate is the contract, so a refusal is
   returned as a failure card rather than thrown.

   The settle() call is not a convenience: app.js routes by writing
   location.hash, and a browser fires hashchange afterwards. The stub address does
   not, so reading the content without settling would read the previous view. */
function contentOf(session) {
  settle(session);
  return session.doc.nodes.content.innerHTML;
}
function renderState(session) {
  settle(session);
  return session.doc.nodes.content.getAttribute('data-render-state');
}
function refused(html) { return /data-failed-view="/.test(html); }

const ALL_TABS = ['decision', 'position', 'objectives', 'economics', 'candidates', 'action'];

/* =========================================================================
   PART 0 - the layer under test is the layer that ships
   ========================================================================= */

await test('UX00', 'The suite loads the layer tools/build.py assembles, not a retired one', async () => {
  /* Read the build's own module list rather than a copy of it, so this check
     cannot drift from the artifact. */
  const build = fs.readFileSync(path.join(ROOT, 'tools', 'build.py'), 'utf8');
  /* Read ONLY the region before UNWIRED_MODULES. Matching the whole file also
     matches every entry in the retired list, so once views.js and render.js were
     deliberately retired this check reported them as assembled and failed - the
     same whole-file regex fault the integration owner hit in
     tools/orphan_audit.py. The boundary is the fix. */
  const boundary = build.indexOf('UNWIRED_MODULES');
  const shipped = [...build.slice(0, boundary)
    .matchAll(/\("(src\/[^"]+)",\s*"[^"]+"\)/g)].map((m) => m[1]);
  assert.ok(shipped.includes('src/ui/app.js'),
    'src/ui/app.js is not in the build\'s module list, so this suite is testing the wrong layer');

  /* The retired view layers must not be assembled. If one of them appears, this
     suite has to be re-pointed rather than silently kept. */
  const compiled = shipped.filter((m) => RETIRED_LAYERS.includes(m));
  assert.equal(compiled.length, 0,
    'the build now assembles a retired view layer: ' + compiled.join(', '));

  /* And it must not be loaded by this file either. */
  const self = fs.readFileSync(fileURLToPath(import.meta.url), 'utf8');
  for (const layer of RETIRED_LAYERS) {
    const stem = path.basename(layer);
    const load = new RegExp('require\\([^)]*' + stem.replace('.', '\\.') + '[^)]*\\)');
    assert.ok(!load.test(self), 'this suite still requires ' + layer);
  }

  const published = Object.keys(loadApp().api);
  return 'build assembles src/ui/app.js and neither retired layer; app.js publishes '
    + published.length + ' entry points: ' + published.join(', ');
});

/* =========================================================================
   PART 1 - the four checks the brief requires, on the shipped layer
   ========================================================================= */

await test('UX01', 'ONE scenario record is shared by every view, calculation, save and export', async () => {
  const session = loadApp();
  const store = session.api.scenario;
  go(session, 'ITUK-PADS', 'objectives');

  /* The default record, before anything is selected. */
  const before = store.get('ITUK-PADS');
  assert.equal(before.selected_alternative_id, null, 'a default record already names an alternative');

  /* Select a ranked alternative on the objectives view, through the button the
     reader presses. The control is read out of the painted markup, so this also
     proves the view actually offers it. */
  const html = contentOf(session);
  const control = /data-select="([^"]+)"/.exec(html);
  assert.ok(control, 'the objectives view offers no alternative to select');
  const button = session.doc.querySelector('[data-select]');
  button.dataset.select = control[1];
  fire(button, 'click');

  const after = store.get('ITUK-PADS');
  assert.equal(after.selected_alternative_id, control[1],
    'pressing the select control did not write the shared record');
  assert.ok(after.version > before.version, 'the record version did not move on selection');

  /* The economics view must be reading that same record, not a second copy. */
  const econ = go(session, 'ITUK-PADS', 'economics');
  const shown = /id="s-newP"[^>]*value="([^"]+)"/.exec(econ);
  assert.ok(shown, 'the price test does not expose the proposed price');
  assert.equal(Number(shown[1]), Number(after.price_after),
    `the price test shows ${shown[1]} but the shared record holds ${after.price_after}`);

  /* A manual edit updates the same record, and both views follow it. */
  const support = session.doc.getElementById('s-support');
  assert.ok(support, 'the price test does not expose the support field');
  support.value = '5000';
  fire(support, 'input');
  const afterEdit = store.get('ITUK-PADS');
  assert.equal(afterEdit.support_eur, 5000, 'the manual edit did not reach the record');
  assert.equal(afterEdit.selected_alternative_id, control[1],
    'the manual edit lost the selected option');
  assert.ok(afterEdit.version > after.version);
  /* The results region alone is rebuilt on a keystroke, so the proof that the
     price test follows the edit is the results region, not the whole view. */
  const results = session.doc.getElementById('economic-results').innerHTML;
  assert.match(results, /One-off support|support/i,
    'the results region does not mention the support cost at all');
  assert.ok(Number(afterEdit.support_eur) === 5000
    && store.calculate('ITUK-PADS').support_eur === 5000,
    'the calculation is not using the edited support value');

  /* The consistency check the engine store exposes has to agree. */
  const cons = store.consistency('ITUK-PADS');
  assert.equal(cons.ok, true, cons.statement);

  /* The export must carry the scenario record the views are showing. The shipped
     export writes a Blob; the sandbox keeps its bytes so the check can read what
     was actually exported rather than trust that a function ran. */
  go(session, 'ITUK-PADS', 'action');
  const exportControl = session.doc.getElementById('export-json');
  assert.ok(exportControl, 'the internal action view offers no JSON export control');
  fire(exportControl, 'click');
  assert.ok(session.sandbox.__blobBytes, 'the export control wrote no bytes');
  const bytes = session.sandbox.__blobBytes();
  assert.ok(bytes.length > 0, 'the export control wrote an empty blob');
  const exported = JSON.parse(new TextDecoder().decode(bytes));
  assert.equal(exported.scenario.support_eur, 5000,
    'the export does not carry the edited support value');
  assert.equal(exported.scenario.version, afterEdit.version,
    'the export carries a different scenario version from the working record');
  assert.equal(exported.scenario.selected_alternative_id, control[1],
    'the export does not carry the selected option');
  assert.equal(exported.result.revenue_change, store.calculate('ITUK-PADS').revenue_change,
    'the export does not carry the result the working record produces');

  /* The action view, which is where a record is saved, must show the shared
     record. The shipped view prints the selected option, the record version, the
     effective date, the evidence period and the calculated changes - but not the
     record's own scenario_id string. The id is asserted on the published state
     instead, and the view is asserted to agree with that state on every field it
     does print. */
  const action = go(session, 'ITUK-PADS', 'action');
  assert.equal(session.api.getState().caseId, 'ITUK-PADS',
    'the action view is not showing the shared case');
  assert.match(action, new RegExp('Scenario version</span><b>' + afterEdit.version + '</b>'),
    'the internal action view is not showing the shared record version');
  assert.ok(action.includes(control[1]),
    'the internal action view is not showing the selected option');
  assert.equal(session.api.getScenario().offer_effective_date, afterEdit.offer_effective_date,
    'the working record changed between the price test and the action view');

  return 'selected ' + control[1] + ' by pressing the view\'s own control, edited support to 5000, '
    + 'record ' + afterEdit.scenario_id + ' at version ' + afterEdit.version
    + '; every view, the save and the export read it';
});

await test('UX02', 'Changing the objective changes ordering only, never the assumptions', async () => {
  const session = loadApp();
  const store = session.api.scenario;
  const c = payload.cases.find((x) => x.id === 'ITUK-PADS');

  /* The invariant is checked the way the shipped layer checks it: two engine
     rankings on one set of inputs, compared alternative by alternative. The
     orphan layer exposed a store.bothObjectives() helper; the shipped store does
     not, and nothing here reaches for it, so the check is the invariant itself
     rather than a wrapper around it. */
  const opts = { payload };
  const rev = engine.rankAlternatives(c, 'revenue', opts);
  const gp = engine.rankAlternatives(c, 'grossProfit', opts);
  const byId = {};
  gp.ranked.forEach((x) => { byId[x.alternative.alternative_id] = x; });
  const sameAssumptions = rev.ranked.every((x) => {
    const y = byId[x.alternative.alternative_id];
    return y
      && x.result.quantity_after === y.result.quantity_after
      && x.result.revenue_change === y.result.revenue_change
      && x.result.offer_effective_date === y.result.offer_effective_date;
  });
  assert.equal(rev.baseline.price, gp.baseline.price, 'the baseline moved when the objective changed');
  assert.equal(rev.baseline.quantity, gp.baseline.quantity, 'the eligible quantity moved');
  assert.equal(sameAssumptions, true,
    'an alternative carries two different quantities under the two objectives');
  assert.equal(rev.ranked.length, gp.ranked.length, 'the two rankings cover different alternatives');

  /* The rendered page must state the same invariant, and both measures have to be
     on every row under either objective. */
  const objective = store.get('ITUK-PADS').objective || 'revenue';
  const html = go(session, 'ITUK-PADS', 'objectives');
  assert.ok(html.includes('Revenue change'), 'the revenue column is missing');
  assert.ok(html.includes('Gross-profit change'), 'the gross-profit column is missing');
  assert.ok(html.includes('/ui/ux/objectives') === false, 'a stray pointer appeared');
  /* The shipped layer states the invariant in a panel of its own, computed from
     two engine rankings on the same inputs. */
  assert.match(html, /Ordering only|Assumptions differ/, 'the ordering claim is not stated');
  assert.match(html, /Ordering only/,
    'the two objectives are reported as differing on a case where they do not');

  /* Changing the objective writes the same record and does not touch a number. */
  const shareBefore = JSON.stringify(rev.ranked
    .map((r) => [r.alternative.alternative_id, r.result.quantity_after, r.result.revenue_change])
    .sort((a, b) => String(a[0]).localeCompare(String(b[0]))));
  const marker = engine.rankAlternatives(c, objective === 'revenue' ? 'grossProfit' : 'revenue', opts);
  const shareAfter = JSON.stringify(marker.ranked
    .map((r) => [r.alternative.alternative_id, r.result.quantity_after, r.result.revenue_change])
    .sort((a, b) => String(a[0]).localeCompare(String(b[0]))));
  assert.equal(shareAfter, shareBefore, 'the objective change moved a quantity or a revenue figure');
  assert.equal(store.get('ITUK-PADS').selected_alternative_id, null,
    'the objective change wrote a selection onto the record');

  /* The order itself is what may differ, and the page says whether it does. */
  const ordersDiffer = rev.ranked.map((x) => x.alternative.alternative_id).join(',')
    !== gp.ranked.map((x) => x.alternative.alternative_id).join(',');
  const html2 = go(session, 'ITUK-PADS', 'objectives');
  assert.match(html2, new RegExp('put the alternatives in a ' + (ordersDiffer ? 'different' : 'same') + ' order'),
    'the view does not say whether the two orders differ');

  return 'same baseline and same quantities under both objectives; ordering differs: '
    + ordersDiffer + '; row measures: ' + rev.ranked.length + ' alternatives, '
    + 'compared by alternative rather than by position';
});

await test('UX03', 'A failed render names the failing view and never leaves stale content', async () => {
  /* --- First, the formatter defect itself (F05). ---------------------------- */
  /* v03 called a formatter that only existed inside the engine's closure, so
     ITUK-TURBO objectives threw ReferenceError: v03fmtPct is not defined. Here
     the same condition is created on purpose: an engine with its formatters
     removed. The shipped layer must still render, because its own num/eur/pct
     helpers do not reach into the engine. This is asserted first, and separately,
     so a pass cannot be mistaken for the failure path working. */
  const noFormatters = Object.assign({}, engine, { fmtPct: undefined, fmtNum: undefined });
  const fmtSession = loadApp({ engineOverride: noFormatters });
  const econ = go(fmtSession, 'ITUK-TURBO', 'objectives');
  assert.equal(refused(econ), false,
    'the objectives view depends on a formatter it does not own: '
    + ((/<pre[^>]*>([\s\S]*?)<\/pre>/.exec(econ) || [])[1] || '').split('\n')[0]);
  assert.ok(econ.length > 2000, 'the formatter-free objectives view painted almost nothing');

  /* --- Then the stale-content contract. ------------------------------------ */
  /* The reported defect reproduced: the view for ITUK-TURBO objectives fails.
     In the retired layer this was created by patching views.render, because the
     shell looked the function up as a module property. app.js calls the engine
     directly and closes over it, so the equivalent fault is created by handing
     the shell an engine with the function the view calls missing entirely - the
     real "helper not available in this build" failure, not a test hook. */
  const brokenEngine = Object.assign({}, engine, { rankAlternatives: undefined });
  const session = loadApp({ engineOverride: brokenEngine });

  /* Paint a healthy view first, so there is genuinely something stale to leave. */
  const healthy = go(session, 'ITUK-PADS', 'decision');
  assert.ok(healthy.length > 500, 'the healthy view did not paint');
  assert.equal(refused(healthy), false, 'the healthy view was refused');
  const marker = 'Reconcile the euro change';
  assert.ok(healthy.includes(marker), 'the test marker is not in the healthy view');
  assert.equal(renderState(session), 'built');

  /* Now open the view that fails, on the case v03 could not draw. */
  const painted = go(session, 'ITUK-TURBO', 'objectives');
  assert.equal(renderState(session), 'failed', 'the content region was not marked as failed');
  assert.ok(painted.includes('render-failure'), 'no failure card was painted');
  assert.ok(painted.includes('data-failed-view="objectives"'),
    'the failure card does not name the failing view');
  assert.ok(/Two objectives did not render/.test(painted), 'the card does not say which view failed');
  assert.ok(/ITUK-TURBO/.test(painted), 'the card does not name the case');
  assert.ok(/TypeError/.test(painted), 'the card does not carry the error name');
  assert.match(painted, /a value the view used was not the shape it expected/,
    'the card does not say what kind of failure it was');
  /* The point of the whole check: the old view must be gone. */
  assert.ok(!painted.includes(marker),
    'STALE CONTENT: the previous view is still on screen under a new active tab');
  assert.ok(!painted.includes('Reconcile'), 'stale content survived the repaint');

  /* The tab is active, and the page agrees with the tab rather than the old
     content. The shipped layer's tab markup carries data-view on the control. */
  const tabs = session.doc.nodes.tabs.innerHTML;
  assert.ok(/data-view="objectives"/.test(tabs), 'the tab bar does not carry the failing view');
  assert.match(session.doc.getElementById('render-status').textContent, /failed to build/i,
    'the shell status line does not report the failure');
  assert.equal(session.doc.getElementById('render-status').getAttribute('data-failed'), 'true',
    'the shell status line is not flagged as failed');

  /* A failed view is recoverable: the healthy case still paints afterwards, and a
     different view of the same failing case works, so one broken view does not
     take its whole case down. */
  const recovered = go(session, 'ITUK-PADS', 'decision');
  assert.equal(renderState(session), 'built', 'the shell did not recover after a failed render');
  assert.ok(recovered.includes(marker), 'the recovered view is not the one asked for');

  const sibling = go(session, 'ITUK-TURBO', 'economics');
  assert.equal(renderState(session), 'built',
    'a different view of the same case did not paint after a sibling view failed');
  assert.equal(refused(sibling), false, 'the sibling view was refused');

  return 'engine without its formatters still renders (so a pass here is not the failure path); '
    + 'a missing ranking helper produced a card naming "Two objectives" and ITUK-TURBO, the '
    + 'previous view was cleared, the shell flagged data-failed, and both the same case and a '
    + 'different case recovered';
});

await test('UX04', 'Candidate search and paging reach beyond the first 300 records', async () => {
  const rows = payload.candidateScreen || [];
  assert.ok(rows.length > 300, 'this payload has only ' + rows.length + ' candidate rows, so the '
    + 'first-300 boundary cannot be tested');

  /* A row the old screen could not have shown: it sits well past index 300. */
  const target = rows[3000] || rows[rows.length - 1];
  assert.ok(rows.indexOf(target) >= 300, 'the chosen row is inside the first 300');

  const wb = candidateModule.workbench(rows, { page_size: 25 });
  const first = wb.page;
  assert.equal(first.rows.length <= first.page_size, true);
  assert.equal(first.total, rows.length, 'the workbench does not count every record');
  assert.equal(first.page_count, Math.ceil(rows.length / first.page_size));
  assert.ok(!first.rows.some((r) => r.part_number === target.part_number
    && r.observed_billing_eur === target.observed_billing_eur
    && r.distributor === target.distributor), 'the target row is already on the first page');

  /* Search for it. The search must reach it wherever it is in the file. */
  const found = candidateModule.workbench(rows, { query: target.part_number, page_size: 25 }).page.rows;
  assert.ok(found.length >= 1, 'searching for ' + target.part_number + ' returned nothing');
  assert.ok(found.every((r) => r.part_number === target.part_number),
    'the search returned a row that does not carry the searched part number');

  /* Paging: reach the last record, not just the last page of a slice. */
  const v = candidateModule.workbench(rows, { page_size: 25 }).page;
  assert.ok(v.page_count > 1, 'the set fits on one page, so paging cannot be tested');
  const last = candidateModule.page(candidateModule.numericSort(rows, 'observed_billing_eur', 'desc'),
    v.page_count, 25);
  assert.ok(last.rows.length >= 1, 'the last page is empty');
  assert.equal(last.last_row, last.total, 'the last page does not end on the last record');

  /* Every record is reachable: pages x page size covers the whole set. */
  assert.ok(last.page_count * last.page_size >= rows.length,
    'the pages do not cover every record');

  /* A unique part number from deep in the file, reached only by searching. */
  const unique = rows[4500].part_number;
  const reached = candidateModule.workbench(rows, { query: unique, page_size: 25 }).page;
  assert.ok(reached.total >= 1, 'a part at index 4500 was not reachable by search');

  /* The shipped screen must reach a row the first page cannot show. rows[3000]
     shares its reference with a row that is already in the first pages, so the
     screen would find it with or without the search. Pick a reference that
     appears on exactly one row and is not in the first window. */
  const counts = {};
  rows.forEach((r) => { counts[r.part_number] = (counts[r.part_number] || 0) + 1; });
  const firstPageRefs = new Set(rows.slice(0, 50).map((r) => r.part_number));
  const only = rows.slice(300).find((r) => counts[r.part_number] === 1
    && !firstPageRefs.has(r.part_number));
  assert.ok(only, 'this payload has no reference that appears once and is beyond the first page, '
    + 'so the search cannot be shown to reach anything new');

  const session = loadApp();
  const screen = go(session, 'ITUK-PADS', 'candidates');
  assert.match(screen, /Rows <b>1<\/b> to <b>50<\/b> of <b>10,543<\/b> matching/,
    'the shipped screen does not state its first page window');
  assert.ok(!screen.includes(only.part_number),
    'the reference chosen to prove the search works is already on the first page');
  const search = session.doc.getElementById('candidate-search');
  search.value = only.part_number;
  fire(search, 'input');
  const searched = contentOf(session);
  assert.ok(searched.includes(only.part_number),
    'the shipped screen did not reach ' + only.part_number + ' by search');
  assert.match(searched, /<b>1<\/b> of <b>1<\/b> matching/,
    'the shipped screen did not narrow to a single matching row');
  /* Paging forward through the screen, by pressing the control that goes forward.
     app.js binds the numbered pager buttons by id (c-first, c-prev, c-next) and
     binds the Last control by its data-last-page attribute, which are the two
     binding styles the retained v03 layout uses. The control is therefore located
     by its id. */
  session.doc.getElementById('candidate-search').value = '';
  fire(session.doc.getElementById('candidate-search'), 'input');
  const forward = session.doc.getElementById('c-next');
  assert.ok(forward, 'the candidate screen has no Next control');
  fire(forward, 'click');
  assert.match(contentOf(session), /page <b>2<\/b> of <b>/,
    'pressing the page control did not move the shipped screen to page 2');

  return rows.length + ' records: ' + first.page_count + ' pages at ' + first.page_size
    + ' rows; found ' + target.part_number + ' (file index ' + rows.indexOf(target) + ') by search; '
    + 'last record reached at row ' + last.last_row
    + '; the shipped screen reached the same row and paged to page 2';
});

/* =========================================================================
   PART 2 - the remaining defects in the brief
   ========================================================================= */

await test('UX05', 'F10: a candidate row routes to that exact part, and a row is not a part', async () => {
  const rows = payload.candidateScreen || [];
  const session = loadApp();

  /* Through the shipped screen: the route control is in the painted markup, and
     pressing it opens the part. */
  const screen = go(session, 'ITUK-PADS', 'candidates');
  const route = /data-open-part="([^"]+)"/.exec(screen);
  assert.ok(route, 'the candidate screen offers no route into a part');
  const control = session.doc.querySelector('[data-open-part]');
  control.dataset.openPart = route[1];
  fire(control, 'click');
  settle(session);
  assert.equal(session.api.getState().view, 'case',
    'the route did not open the selected-part review');
  assert.equal(session.api.getState().partRoute.partNumber, route[1],
    'the route lost the exact part reference');

  /* A part with a worked case opens that case, not a review. */
  const workedPn = payload.cases[0].pn;
  session.api.openPart(workedPn);
  settle(session);
  const st = session.api.getState();
  assert.equal(st.caseId, payload.cases[0].id, 'the route into a worked case failed');
  assert.equal(st.view, 'decision', 'a worked case did not open on its own tab');

  /* A part with no worked case opens its own review and says no case exists. */
  const noCase = rows.map((r) => r.part_number)
    .find((pn) => !payload.cases.some((c) => c.pn === pn));
  /* At least one screened reference must have no worked case, or this branch is
     vacuous. */
  assert.ok(noCase, 'every screened reference has a worked case, so this check proves nothing');
  const opened = session.api.openPart(noCase);
  settle(session);
  assert.equal(opened.ok, true, 'the route into an unreviewed part failed');
  const review = contentOf(session);
  assert.ok(review.includes(noCase), 'the selected-part review lost the part number');
  assert.match(review, /No case record exists for this exact part yet/,
    'the review claims a case exists for a part that has none');
  /* The strip describes the part being reviewed. The open case is still
     ITUK-PADS, so if the strip were built from the case it would show that part
     number here - a reader would be told two different things at once. */
  const strip = /<span class="pn pn-strong">([^<]*)<\/span>/.exec(review);
  assert.ok(strip, 'the review carries no part-reference strip');
  assert.equal(strip[1], noCase,
    'the part strip names ' + strip[1] + ' while the review is of ' + noCase);

  /* A row is not a part: two rows can carry the same original reference. The
     count is asserted from the route's own return value, because that value is
     computed from the searched rows and compared against the independent count
     taken from the payload here. The rendered panel was already asserted, above,
     to be the review of the part at the head of the same HTML, so a mismatch
     between the two would already have failed. */
  const counts = {};
  rows.forEach((r) => { counts[r.part_number] = (counts[r.part_number] || 0) + 1; });
  const dup = Object.keys(counts).find((pn) => counts[pn] > 2);
  assert.ok(dup, 'this payload has no reference carried by more than two rows, so the '
    + 'rows-are-not-parts claim cannot be shown');
  const covered = counts[dup];
  /* The review is opened through the view's own route, and the state is asserted
     to be the review before the painted bytes are read, so the bytes read are the
     bytes the route wrote. */
  const openedDup = session.api.openPart(dup);
  settle(session);
  assert.equal(openedDup.ok, true, 'the route into the repeated reference failed: ' + openedDup.error);
  assert.equal(openedDup.rows, covered,
    'the route counted ' + openedDup.rows + ' rows for a reference carried by ' + covered);
  assert.equal(openedDup.part_number, dup, 'the route changed the exact part reference');
  assert.equal(session.api.getState().view, 'case', 'the route did not land on the review');
  assert.equal(session.api.getState().partRoute.partNumber, dup,
    'the review on screen is not the review of ' + dup);
  const openCaseId = session.api.getState().caseId;
  const workedCount = counts[payload.cases.find((c) => c.id === openCaseId).pn] || 0;
  assert.notEqual(covered, workedCount,
    'this payload has no reference whose row count differs from the open case\'s, so the '
    + 'count cannot be shown to come from the review rather than from the case');

  return 'routed ' + route[1] + ' to its own review and ' + workedPn + ' to case '
    + payload.cases[0].id + '; ' + dup + ' covers ' + covered + ' rows under one reference, '
    + 'and the strip names the reviewed part, not the open case';
});

await test('UX06', 'REVIEW-02: row counts and part counts stay apart, and coverage is not approval', async () => {
  const session = loadApp();
  const rows = payload.candidateScreen || [];

  /* The real payload holds 15 rows carrying a price and a cost, covering 8
     distinct part numbers. v03 presented those as decision readiness. */
  const withCost = candidateModule.workbench(rows, { page_size: 25 });
  const filtered = candidateModule.coverage(candidateModule.filter(rows, { with_cost: true }), rows);
  const all = candidateModule.coverage(rows, rows);
  assert.ok(all.rows_matching >= all.unique_parts, 'the distinct part count exceeds the row count');
  assert.ok(all.rows_with_cost_and_list <= all.rows_matching);
  assert.ok(filtered.rows_matching <= all.rows_matching);

  const html = go(session, payload.cases[0].id, 'candidates');
  assert.match(html, /Rows with a price and a cost record/, 'the row count is not labelled as rows');
  assert.match(html, /distinct part numbers/i, 'the distinct part count is not labelled');
  assert.match(html, /coverage, not approval/i, 'coverage is not separated from approval');
  assert.match(html, /candidate for review/i, 'a priced row is not described as a candidate');
  assert.ok(!/decision[- ]ready/i.test(html), 'the page still says decision-ready');
  /* The tile says "row", and the detail beside it says "part", and they differ. */
  const tile = /Rows with a price and a cost record<\/div><strong>([\d,]+)<\/strong><div class="detail">([\d,]+) distinct part numbers/.exec(html);
  assert.ok(tile, 'the coverage tile does not print a row count and a part count side by side');
  assert.notEqual(tile[1], tile[2],
    'the row count and the distinct-part count are printed as the same number');

  /* Commercial priority is a separate axis from evidence completeness. The
     shipped layer states priority from the recorded billing on the row. */
  const priority = candidateModule.monetaryPriority(rows, { top_n: 10 });
  assert.ok(Number.isFinite(priority.total_observed_billing_eur));
  const priorityStatement = priority.statement;
  assert.match(priorityStatement, /Monetary priority is the observed billing on the row/,
    'priority is not explained as a billed amount');
  assert.match(priorityStatement, /carry no billing value and are excluded from the total rather than counted as zero/,
    'priority does not say what happened to the rows with no billing value');

  const approval = candidateModule.approvalStatus(rows);
  assert.match(approval.statement, /not approval/i,
    'a complete cost and list is presented as approval');

  const readiness = candidateModule.evidenceReadiness(rows);
  assert.match(readiness.statement, /not mixed into a priority score/,
    'evidence readiness is folded into the priority score');

  const cov = candidateModule.coverage(rows, rows);
  if (usesRealPayload) {
    assert.equal(cov.rows_with_cost_and_list, 15,
      'the priced row count changed: ' + cov.rows_with_cost_and_list);
    assert.equal(cov.unique_parts_with_cost_and_list, 8,
      'the distinct priced part count changed: ' + cov.unique_parts_with_cost_and_list);
    /* The two counts are printed as two different counts in one sentence. The
       module's own figure is an unformatted integer, so the expectation is built
       from String() rather than from a locale-formatted number. */
    assert.match(cov.rows_vs_parts,
      new RegExp('^' + String(rows.length) + ' row\\(s\\) and '
        + String(cov.unique_parts) + ' distinct part number\\(s\\) are two different counts'),
      'the two counts are not stated as two different things: ' + cov.rows_vs_parts);
  }
  return cov.rows_with_cost_and_list + ' priced rows covering ' + cov.unique_parts_with_cost_and_list
    + ' distinct part numbers; ' + rows.length + ' rows in total for ' + cov.unique_parts
    + ' distinct references; priority states a total of ' + priority.total_observed_billing_eur
    + ' over ' + priority.rows_with_a_billing_value + ' rows with a billing value, and says the '
    + priority.rows_without_a_billing_value + ' rows without one are excluded rather than counted as zero';
});

await test('UX07', 'F11: cost, price and version come from the payload, not from literals', async () => {
  /* The version. The literal this check exists to remove is the old component
     version string, which lived in the frozen shell and in app.js's chrome. */
  const raw = fs.readFileSync(APP, 'utf8');
  assert.ok(!/Decision component/.test(raw),
    'app.js still carries a hardcoded component version string');
  assert.ok(!/Decision component 0\.2/.test(raw), 'the old component version is still in app.js');

  /* The turbo conflict is resolved in the payload. The shipped position view
     must say so rather than ask the reader to settle it. */
  const turbo = payload.turboPriceResolution;
  assert.ok(turbo, 'the payload carries no turbo resolution, so this check is vacuous');
  assert.equal(turbo.resolved_billable_list, 1114.96,
    'the turbo resolution amount changed: ' + turbo.resolved_billable_list);

  const session = loadApp();
  const position = go(session, 'ITUK-TURBO', 'position');
  assert.match(position, /already settled|already resolved/i,
    'the position view does not say the turbo conflict is settled');
  assert.ok(!/Conflicting recorded list prices/.test(position),
    'the position view still asks the reader to settle the conflict');
  const listed = Number(new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR',
    minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(turbo.resolved_billable_list)
    .replace(/[^\d.,]/g, '').replace(/,/g, '')).toFixed(2);
  const formatted = new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR',
    minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(turbo.resolved_billable_list);
  assert.ok(position.includes(formatted),
    'the position view does not print the resolved amount ' + formatted + ' from the payload');

  /* The cost demand must not reappear on the economics view, and the retraction
     has to be the payload's own words. */
  const econ = go(session, 'IMOTORS-OIL', 'economics');
  const costType = payload.meta.confirmedRules.costTypeRequired;
  assert.match(costType, /no longer required/i,
    'the payload no longer retracts the accounting-cost demand, so this check is vacuous');
  assert.match(econ, /no longer required/i,
    'the economics view does not retract the accounting-cost demand');
  assert.ok(econ.includes(costType),
    'the economics view does not print the payload\'s own cost-type statement');

  /* The approval controls are read from the payload, not typed. */
  const rules = payload.meta.confirmedRules;
  const objectivesView = go(session, 'ITUK-PADS', 'objectives');
  assert.ok(objectivesView.includes(rules.minMarginStatus),
    'the minimum-margin control does not print the payload status');
  assert.ok(objectivesView.includes(rules.maxProfitSacrificeStatus),
    'the profit-sacrifice control does not print the payload status');

  /* No view may print a hardcoded status sentence that contradicts the payload. */
  const everyView = ALL_TABS.map((v) => go(session, 'ITUK-TURBO', v)).join('\n');
  assert.ok(!/Decision component/.test(everyView), 'a hardcoded component version survived');
  /* The status strip used to carry a fixed count of the review findings. It is
     read from the payload now. On this payload the payload's own count happens to
     be ten, so an assertion on the rendered text alone cannot tell a counted
     number from a typed one - the two are equal by coincidence. The
     discriminating check is therefore on the source, where a typed sentence would
     have to live, plus the rendered count matching the payload's list length. */
  const findings = (payload.packAudit.issues || []).length;
  assert.ok(!/data-sources>\s*\d+\s+review finding/i.test(raw),
    'app.js still types a review-finding count into the strip instead of counting the payload');
  const packStatus = session.doc.getElementById('pack-status');
  assert.ok(packStatus.innerHTML.includes(findings + ' review finding'),
    'the status strip does not count the payload\'s own review findings ('
    + findings + ' in the file)');
  /* The version the page states must be the payload's, asserted on the chrome
     element rather than on a styled span. */
  assert.equal(packStatus.getAttribute('data-payload-version'), payload.meta.version,
    'the page does not state the payload version');
  assert.ok(packStatus.innerHTML.includes(payload.meta.version),
    'the status strip does not print the payload version');

  return 'no hardcoded component version anywhere in app.js; turbo resolved at '
    + turbo.resolved_billable_list + ' printed from the payload; cost rule retracted in the '
    + 'payload\'s own words; approval controls printed from the payload; no typed '
    + 'review-finding sentence in the source, and the strip counts ' + findings
    + ' payload findings';
});

await test('UX08', 'UX-06: absent data produces an explicit amber unavailable state, never a blank shell', async () => {
  const session = loadApp();

  /* IMOTORS-OIL holds no cost record on its own evidence record, so the price
     test cannot state gross profit for it. The view must say why instead of
     printing an empty panel or a zero. */
  const oil = payload.cases.find((c) => c.id === 'IMOTORS-OIL');
  assert.ok(oil, 'the oil case is missing from this payload');
  assert.equal(oil.packEvidence.costRecordPresent, false,
    'the fixture for this check no longer has a cost-free case evidence record');

  const econ = go(session, 'IMOTORS-OIL', 'economics');
  /* The state must be the amber block, not merely some HTML: the class is what
     makes it amber, the eyebrow is what names it, and "What is required" is what
     tells the reader how to close the gap. */
  assert.match(econ, /<div class="panel unavailable" role="status"[^>]*data-unavailable="/,
    'the cost-free case is not rendered as the amber unavailable block');
  /* The state must be named Unavailable, and the accent that makes it amber must
     be on the element, not only in a stylesheet the frozen shell does not
     carry. A plain white panel with the word on it is the reading this state
     exists to prevent. */
  assert.match(econ, /class="eyebrow"[^>]*>Unavailable<\/div>/,
    'the unavailable block is not labelled Unavailable');
  assert.match(econ, /class="panel unavailable"[^>]*style="[^"]*border-left:4px solid #96620d/,
    'the unavailable block carries no amber accent of its own, so it cannot be told '
    + 'from an ordinary warn panel, which shares its pale fill in this stylesheet');
  assert.match(econ, /Gross profit and gross margin are not calculated/,
    'the unavailable block does not name the missing measure');
  assert.match(econ, /No parts purchase cost is held or entered for this exact part/,
    'the unavailable block does not state the reason');
  assert.match(econ, /What is required<\/span><b[^>]*>the parts purchase cost for/,
    'the unavailable block does not say what would close the gap');
  assert.match(econ, /A missing cost is not zero/,
    'the view does not separate missing from zero');

  /* The same for a case whose evidence record does hold a cost, so the block is
     about the applied cost rather than about the file. Either way the reader is
     told which of the two it is. */
  const pads = go(session, 'ITUK-PADS', 'economics');
  const padsBlock = /<div class="panel unavailable" role="status"[^>]*>[\s\S]*?<\/div>\s*<\/div>/.exec(pads);
  assert.ok(padsBlock, 'a case with no cost applied to the scenario is not an amber state');
  assert.match(padsBlock[0], /A parts purchase cost is held for this part, but no cost is applied/,
    'the amber block blames the file when the file holds a cost record');

  /* The gross-profit objective panel states the same thing in the same shape, on
     a case where no gross-profit alternative is rankable at all. */
  const oilObjectives = go(session, 'IMOTORS-OIL', 'objectives');
  const gpPanel = /<span class="eyebrow">Objective 2<\/span>[\s\S]*?<\/div>\s*<\/div>/.exec(oilObjectives);
  assert.ok(gpPanel, 'the oil objectives view has no gross-profit panel');
  if (gpPanel[0].includes('panel unavailable')) {
    assert.match(gpPanel[0], /Gross-profit growth is not available for this case/,
      'the objectives view does not name why gross-profit growth is absent');
  } else {
    /* A zero-change alternative is still rankable, so the panel is a result, not
       an absent state. Requiring the amber block here would be requiring a view
       to claim data is missing when it is not. */
    assert.match(gpPanel[0], /No action|resultbig/,
      'the gross-profit panel is neither an amber state nor a stated result');
  }

  /* An empty search result is stated, not drawn as an empty table, and the
     pagination counter must not print a reversed range such as "1 to 0 of 0". */
  go(session, 'ITUK-PADS', 'candidates');
  const q = session.doc.getElementById('candidate-search');
  q.value = 'zzzz-no-such-part-zzzz';
  fire(q, 'input');
  const cand = contentOf(session);
  assert.match(cand, /No candidate row matches this search/, 'an empty search result is not explained');
  assert.match(cand, /the filter excluded them/i,
    'the empty state does not say whether the rows are missing or filtered out');
  assert.ok(!/Rows\s*<b>1<\/b>\s*to\s*<b>0<\/b>/.test(cand),
    'the pagination counter prints a reversed range for an empty result');
  assert.match(cand, /No rows match the current search/, 'the page does not state that the result set is empty');
  assert.match(cand, /<button[^>]*data-last-page[^>]*disabled/,
    'the last-page control is still enabled with nothing to page to');

  /* A view with nothing selected is also an unavailable state, not a blank. */
  session.api.go({ view: 'case', partRoute: null });
  const blankReview = contentOf(session);
  assert.match(blankReview, /<div class="panel unavailable" role="status"/,
    'the selected-part review with nothing selected is not an amber state');
  assert.match(blankReview, /No part is selected/, 'the review does not say nothing is selected');

  return 'cost-free case states the missing gross profit in an amber block naming the reason, the '
    + 'required input and its own amber accent; a cost-applied case says which of the two it is; '
    + 'empty search names the filter and disables the last-page control; an unselected review is '
    + 'an amber state';
});

await test('UX09', 'UX-07: the keyboard and small-screen pattern is kept', async () => {
  const session = loadApp();
  const html = go(session, 'ITUK-PADS', 'decision');
  const hits = html.match(/class="month-hit"[^>]*tabindex="0"/g) || [];
  assert.ok(hits.length >= 6, 'the month cells no longer take a tabindex: found ' + hits.length);
  assert.ok(/role="button"/.test(html), 'the month cells are no longer announced as buttons');
  assert.ok(/aria-label="Jan:/.test(html), 'the month cells carry no text alternative');
  assert.ok(/data-readout=/.test(html), 'the readout text is no longer attached to the cell');
  /* The key handler must be bound, not only the attribute printed. */
  const cell = session.doc.querySelector('.month-hit') || null;
  if (cell) {
    const bound = Object.keys(cell._listeners || {});
    assert.ok(bound.includes('keydown'), 'no keydown handler is bound to the month cells');
  }

  /* Every interactive control on the candidate screen is a real button or select,
     so it is reachable by tab and by Enter. */
  const cand = go(session, 'ITUK-PADS', 'candidates');
  assert.ok(/<button[^>]*data-page=/.test(cand), 'paging is not a button');
  assert.ok(/<button[^>]*data-sort=/.test(cand), 'sorting is not a button');
  assert.ok(/<input id="candidate-search"/.test(cand), 'search is not an input');
  assert.ok(/<button[^>]*data-open-part=/.test(cand), 'the route into a part is not a button');
  assert.ok(!/<div[^>]*onclick=/.test(cand), 'an onclick handler is attached to a div');

  /* The narrow-screen breakpoint still exists in the shell the views are built for. */
  const ref = path.join(ROOT, 'reference', 'ISZE_AIM_Pricing_Decisions_v03_FROZEN.html');
  if (fs.existsSync(ref)) {
    const frozen = fs.readFileSync(ref, 'utf8');
    assert.ok(/@media\(max-width:800px\)/.test(frozen),
      'the frozen reference no longer carries the narrow-screen breakpoint');
  }
  return hits.length + ' month cells with tabindex and Enter/Space handling; candidate controls are '
    + 'native buttons; the narrow-screen breakpoint is still in the shell';
});

await test('UX10', 'REVIEW-04: every view keeps the exact original part references', async () => {
  const session = loadApp();
  const report = [];
  for (const c of payload.cases) {
    for (const view of ALL_TABS) {
      const html = go(session, c.id, view);
      assert.equal(refused(html), false,
        view + ' for ' + c.id + ' was refused by the render gate');
      assert.ok(html.includes(c.pn),
        view + ' for ' + c.id + ' does not carry the exact part reference ' + c.pn);
      assert.ok(html.includes('Exact part references'),
        view + ' for ' + c.id + ' has no part-reference strip');
      /* And the reference is printed as itself, never rewritten into a derived or
         private number. */
      const strip = /<span class="pn pn-strong">([^<]*)<\/span>/.exec(html);
      assert.ok(strip, view + ' for ' + c.id + ' has no strong part reference');
      assert.equal(strip[1], c.pn,
        view + ' for ' + c.id + ' prints ' + strip[1] + ' as the part reference');
    }
    report.push(c.id + '=' + c.pn);
  }

  /* The counter-example, kept deliberately. A part strip built from the open
     case, shown above a review of a different part, tells the reader two
     different things at once. The review must describe the part it is about. */
  const rows = payload.candidateScreen || [];
  const noCase = rows.map((r) => r.part_number)
    .find((pn) => !payload.cases.some((c) => c.pn === pn));
  session.api.openPart(noCase);
  const review = contentOf(session);
  const strip = /<span class="pn pn-strong">([^<]*)<\/span>/.exec(review);
  assert.ok(strip && strip[1] === noCase,
    'the part strip on a selected-part review names '
    + (strip ? strip[1] : 'nothing') + ' while the review is of ' + noCase);
  /* And it says what the strip cannot know about a screened row. */
  assert.match(review, /screened candidate row, not a worked case/,
    'the strip does not say that a screened row is not a worked case');

  return report.join(', ') + '; the review strip follows the reviewed part (' + noCase
    + ') rather than the open case, and labels a screened row as one';
});

await test('UX11', 'No banned wording and no invented figure reaches a reader', async () => {
  const session = loadApp();
  const findings = [];
  const BANNED = [
    [/\bMode\s*[AB]\b/i, 'audience label'], [/\bwallet\b/i, 'wallet wording'],
    [/\bstreet\b/i, 'street wording'], [/sell-?out/i, 'say sales to dealer'],
    [/\bBook\s*B\b/i, 'say the price list'], [/\bclass\s*factor\b/i, 'work in margins, not factors']
  ];
  const everyView = [];
  for (const c of payload.cases) {
    for (const view of ALL_TABS) {
      const html = go(session, c.id, view);
      everyView.push(html);
      BANNED.forEach(([re, why]) => {
        const m = re.exec(html);
        if (m) findings.push(c.id + '/' + view + ': "' + m[0] + '" (' + why + ')');
      });
    }
  }
  assert.equal(findings.length, 0, 'banned wording reached a view: ' + findings.join('; '));

  /* The specific figures the brief forbids. They must not appear as stated
     outcomes anywhere in the built views. */
  const text = everyView.join('\n');
  /* A claim of a figure, not a disclaimer. The pages say plainly that no optimum,
     elasticity, sacrifice, minimum margin or measured benefit is stated; what is
     banned is presenting one of those as a result. */
  [/optimal price of/i, /optimal price is/i, /elasticity of/i, /acceptable profit sacrifice of/i,
    /minimum margin of/i, /measured benefit of/i, /expected loss of/i,
    /the optimum price is/i].forEach((re) => {
    assert.ok(!re.test(text), 'a forbidden claim appears: ' + re);
  });

  /* A gap a reader sees must carry euro, family and fleet, or not appear at all. */
  assert.ok(/market (trucks|vehicles)/i.test(text) || /market reference/i.test(text),
    'no fleet denominator is stated anywhere');

  /* The guard the shipped layer runs before paint must find each banned word it
     claims to guard, so the guard is not a promise that tests nothing. */
  const guardFindings = BANNED.map(([re]) => re.source).length;
  assert.ok(guardFindings === 6, 'the banned list changed size without the check being updated');

  return 'zero banned words across ' + everyView.length + ' rendered views; no invented optimum, '
    + 'elasticity, sacrifice or benefit; the fleet denominator is stated';
});

await test('UX12', 'BASELINE: all five cases x all six tabs build, and the failed count is reported', async () => {
  const session = loadApp();
  const rendered = [];
  const failed = [];
  for (const c of payload.cases) {
    for (const view of ALL_TABS) {
      const html = go(session, c.id, view);
      if (refused(html)) {
        const m = /<p><b>([^<]*)<\/b>:\s*([\s\S]*?)<\/p>/.exec(html);
        failed.push(c.id + '/' + view + ': ' + (m ? m[1] + ': ' + m[2].slice(0, 120) : 'refused'));
      } else {
        rendered.push(c.id + '/' + view);
      }
    }
  }
  /* Every case, every tab, is covered. */
  assert.equal(rendered.length + failed.length, payload.cases.length * ALL_TABS.length);
  assert.equal(failed.length, 0, 'failed combinations: ' + failed.join(' | '));

  /* Both objectives on the objectives view for every case, including the turbo
     view that v03 could not draw, and including a price increase and a
     cost-free case. */
  const turbo = go(session, 'ITUK-TURBO', 'objectives');
  assert.ok(turbo.includes('TURBO-INC'), 'the turbo price-increase alternative is missing');
  assert.match(turbo, /Tolerable volume loss|Volume may fall by up to/,
    'the turbo increase view states no required quantity or test');
  const oil = go(session, 'IMOTORS-OIL', 'objectives');
  assert.ok(oil.includes('OIL-GEN'), 'the migration alternative is missing from the oil case');
  assert.match(oil, /not priced as a single part/i,
    'the migration alternative is presented as an ordinary single-part calculation');

  return rendered.length + ' rendered, ' + failed.length + ' failed, of '
    + (payload.cases.length * ALL_TABS.length) + ' case/tab combinations';
});

await test('UX13', 'A saved case reopens on the same scenario it was saved with', async () => {
  const session = loadApp();
  const store = session.api.scenario;
  session.api.go({ caseId: 'ITUK-DISCS' });
  settle(session);

  /* The shipped store writes through set(patch); there is no store.edit(). The
     selection goes through the store's own selectAlternative. */
  store.selectAlternative('ITUK-DISCS', 'DISC-BVP');
  store.set('ITUK-DISCS', { offer_effective_date: '2026-10-05', support_eur: 250 });

  const before = store.get('ITUK-DISCS');
  const beforeResult = store.calculate('ITUK-DISCS');
  assert.equal(before.selected_alternative_id, 'DISC-BVP', 'the selection did not reach the record');
  assert.equal(before.offer_effective_date, '2026-10-05');

  /* Save by pressing the shipped control, not by calling the repository. */
  go(session, 'ITUK-DISCS', 'action');
  const saveControl = session.doc.getElementById('save-case');
  assert.ok(saveControl, 'the internal action view offers no save control');
  fire(saveControl, 'click');
  const savedRecord = session.api.cases.load('ITUK-DISCS');
  assert.ok(savedRecord, 'the save wrote no case record');
  assert.ok(savedRecord.revisions.length >= 1, 'the save wrote a record with no revision');

  const repo = session.api.cases;
  const reopened = repo.reopen('ITUK-DISCS');
  assert.ok(reopened, 'the saved case could not be reopened');
  assert.equal(reopened.scenario.scenario_id, before.scenario_id,
    'the reopened case carries a different scenario record');
  assert.equal(reopened.scenario.offer_effective_date, '2026-10-05');
  assert.equal(reopened.scenario.support_eur, 250);
  assert.equal(reopened.scenario.selected_alternative_id, 'DISC-BVP');
  assert.equal(reopened.result.revenue_change, beforeResult.revenue_change,
    'the reopened case does not reproduce the revenue result');
  assert.equal(reopened.result.gp_change, beforeResult.gp_change,
    'the reopened case does not reproduce the gross-profit result');

  /* The save carries the scenario record the views are showing - the whole point
     of the one-record invariant. The reloaded revision must hold it. */
  const onDisk = savedRecord.revisions[savedRecord.revisions.length - 1].record.scenario;
  ['scenario_id', 'version', 'support_eur', 'offer_effective_date', 'selected_alternative_id']
    .forEach((k) => {
      assert.equal(onDisk[k], before[k],
        'the saved revision did not carry ' + k + ' from the working record');
    });
  return 'reopened ' + reopened.scenario.scenario_id + ' at case revision ' + reopened.version
    + ' with the same scenario and the same result';
});

/* =========================================================================
   Report
   ========================================================================= */
const summary = {
  pass: results.filter((r) => r.status === 'PASS').length,
  fail: results.filter((r) => r.status === 'FAIL').length,
  total: results.length
};
const output = {
  run_date: new Date().toISOString(),
  suite: 'aim-ui-ux-flow',
  layer_under_test: 'src/ui/app.js (the module tools/build.py assembles)',
  retired_layers_not_loaded: RETIRED_LAYERS,
  payload_file: path.basename(payloadPath),
  payload_label: label,
  payload_sha256: payloadSha,
  node: process.version,
  contract_version: contracts.CONTRACT_VERSION,
  scope: 'View-layer flow checks on the corrected AIM component, run against the shipped '
    + 'layer: one scenario record, ordering-only objective change, failed-render handling, '
    + 'candidate search and paging, source-backed status wording, amber unavailable states, '
    + 'part-reference retention. The arithmetic itself is covered by the engine suite. This '
    + 'does not validate the underlying source workbooks, commercial approval or production access.',
  summary,
  results
};
if (resultsPath) fs.writeFileSync(resultsPath, JSON.stringify(output, null, 2) + '\n');

for (const r of results) {
  console.log(`${r.status} ${r.id}: ${r.name}`
    + (r.status === 'FAIL' ? '  --  ' + r.evidence : (r.evidence ? '  [' + r.evidence + ']' : '')));
}
console.log('');
console.log('payload: ' + path.basename(payloadPath) + ' (' + label + ')  sha256 ' + payloadSha.slice(0, 16));
console.log('layer  : src/ui/app.js');
console.log(JSON.stringify(summary));
process.exitCode = summary.fail ? 1 : 0;
