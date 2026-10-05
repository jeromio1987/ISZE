#!/usr/bin/env node
/* ===========================================================================
   Reopen the saved case, directly (F01, UX-08, J10).

   The browser journey in tests/accept/accept_02_journey.py proves this against a
   real file:// URL and a real Chrome restart. That check is the acceptance
   evidence. This file is the developer test beside it: it drives the same load
   sequence in Node, in a browser-shaped sandbox, so the restore path can be
   asserted field by field and a regression is caught before the browser run.

     node --test tests/ux_reopen.test.mjs

   What it drives
   --------------
   src/ui/app.js is loaded twice against one shared storage object. The first
   load is the working session: select a ranked alternative, edit an assumption,
   save a revision. The second load is the reopen: a brand new module scope, an
   empty working record, and the same case record read back from storage. That
   is the same thing the browser does across a restart, minus the process.

   The compared key list is the one ACCEPT-02 uses, copied rather than
   paraphrased, so the two cannot drift apart:

     scenario_id, case_id, part_number, price_before, price_after,
     quantity_before, quantity_after, scope, support_eur, cost_eur,
     cost_basis_id, pack_size, quantity_label, evidence_period,
     offer_effective_date, selected_alternative_id, objective

   The engine, the case store, the scenario store, the contracts and the export
   module are the shipped ones; none of them is stubbed. Only the browser shell
   (the document, the address and the storage object) is supplied by this file,
   and it says so if app.js no longer has the shape it rewrites.
   =========================================================================== */
import { test } from 'node:test';
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
const scenarioModule = require(path.join(ROOT, 'src/data/scenario.js'));
const caseModule = require(path.join(ROOT, 'src/data/cases.js'));
const exportModule = require(path.join(ROOT, 'src/data/export.js'));
const comparableModule = require(path.join(ROOT, 'src/data/comparable.js'));
const candidatesModule = require(path.join(ROOT, 'src/data/candidates.js'));

const APP = path.join(ROOT, 'src/ui/app.js');

/* The reviewer's comparison list from accept_02_journey.py, kept identical. */
const COMPARED_KEYS = ['scenario_id', 'case_id', 'part_number', 'price_before', 'price_after',
  'quantity_before', 'quantity_after', 'scope', 'support_eur', 'cost_eur',
  'cost_basis_id', 'pack_size', 'quantity_label', 'evidence_period',
  'offer_effective_date', 'selected_alternative_id', 'objective'];

const RESULT_KEYS = ['revenue_before', 'revenue_after', 'revenue_change', 'gp_before', 'gp_after',
  'gp_change', 'margin_after_pct', 'quantity_after', 'ok'];

/* --------------------------------------------------------------- payload -- */

/* The authorised pack when it is on this machine, because the reopen defect and
   the derived quantity both need the real alternatives. The synthetic fixture
   otherwise. Read, never written. */
const REAL_PAYLOAD = path.join(ROOT, 'payload', 'aim_payload_20260922.json');
const SYNTHETIC = path.join(ROOT, 'tests', 'fixtures', 'synthetic_payload.json');
const payloadPath = fs.existsSync(REAL_PAYLOAD) ? REAL_PAYLOAD : SYNTHETIC;
const payloadUsesRealPack = payloadPath === REAL_PAYLOAD;
const payload = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));

/* ------------------------------------------------ the browser-shaped shell -- */

function stubElement(id) {
  return {
    id, innerHTML: '', value: '', textContent: '', dataset: {},
    onclick: null, onchange: null,
    addEventListener() {}, removeEventListener() {}, focus() {}, setSelectionRange() {},
    remove() {}, append() {},
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute() {}, getAttribute() { return null; }, querySelectorAll() { return []; }
  };
}

function stubDocument() {
  const nodes = {};
  return {
    getElementById: (id) => (nodes[id] = nodes[id] || stubElement(id)),
    querySelector: (sel) => (nodes[sel] = nodes[sel] || stubElement(String(sel).replace(/^#/, ''))),
    querySelectorAll: () => [],
    createElement: (tag) => stubElement(tag),
    body: { append() {} },
    _nodes: nodes
  };
}

/* A Web Storage object backed by an object, so the shipped case store writes and
   reads through its own code instead of a test double for the repository. Two
   page loads share it; a fresh one per test keeps tests independent. */
function makeStorage(seed) {
  const data = Object.assign({}, seed || {});
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
  const once = (needle, replacement, label) => {
    const count = src.split(needle).length - 1;
    assert.equal(count, 1,
      `expected exactly one ${label} in src/ui/app.js; found ${count}. `
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

/* Load src/ui/app.js the way the built page does: run it, then read the
   AIMPricing surface it publishes. `hash` is the address the page was opened at. */
function loadApp({ storage, hash, caseId }) {
  /* The shipped case store reads its storage object off the global it was loaded
     with. Under Node that is this process's global, not the sandbox, because the
     module is required rather than run inside the context. So the storage is
     handed over on both, which is what a browser does by having one window. */
  globalThis.localStorage = storage;
  const sandbox = {
    __payload: payload,
    __dom: {
      $: (sel) => sandbox.document.querySelector(sel),
      $$: () => []
    },
    document: stubDocument(),
    localStorage: storage,
    location: { hash: hash || '' },
    URLSearchParams, Intl, JSON, Math, Date, console,
    setTimeout, clearTimeout,
    Blob: class { constructor() {} },
    URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
    AIMEngine: engine,
    AIMExport: exportModule,
    AIMCandidates: candidatesModule,
    AIMCases: caseModule,
    AIMContracts: contracts,
    AIMScenario: scenarioModule,
    /* Assembled by tools/build.py beside the modules above, and read by
       src/ui/app.js for the price-position view. */
    AIMComparable: comparableModule
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  /* The page shell subscribes to two events. Neither is under test here; this
     records them so the listener can be driven if a later check needs to. */
  sandbox._listeners = {};
  sandbox.addEventListener = (name, fn) => { sandbox._listeners[name] = fn; };
  sandbox.removeEventListener = (name) => { delete sandbox._listeners[name]; };
  vm.createContext(sandbox);
  vm.runInContext(appSource(), sandbox, { filename: APP, timeout: 30000 });
  const api = sandbox.window.AIMPricing;
  assert.ok(api, 'app.js did not publish window.AIMPricing');
  return api;
}

const hashFor = (caseId, view) => new URLSearchParams({ case: caseId, view, compare: 'half' }).toString();
const pick = (record, keys) => {
  const out = {};
  keys.forEach((k) => { out[k] = record ? record[k] : undefined; });
  return out;
};
const same = (a, b, keys) => JSON.stringify(pick(a, keys)) === JSON.stringify(pick(b, keys));
const describeDiff = (a, b, keys) => keys.filter((k) => JSON.stringify(a ? a[k] : undefined)
  !== JSON.stringify(b ? b[k] : undefined)).map((k) => `${k}: ${JSON.stringify(a && a[k])} -> ${JSON.stringify(b && b[k])}`);

const CASES = payload.cases.map((c) => c.id);

/* ======================================================================== */

test('a saved revision reopens into the live scenario, on every compared key', () => {
  for (const caseId of CASES) {
    const storage = makeStorage();
    const session = loadApp({ storage, hash: hashFor(caseId, 'objectives') });

    /* One working session: pick the ranked alternative that actually moves the
       eligible quantity, edit an assumption, save the revision. */
    const caseObject = payload.cases.find((c) => c.id === caseId);
    const ranking = engine.rankAlternatives(caseObject, 'revenue',
      { payload, pack_size: session.getScenario().pack_size });
    const chosen = ranking.ranked.filter((x) => x.result.ok).sort((a, b) =>
      Number(!!b.alternative.volume_assumption) - Number(!!a.alternative.volume_assumption))[0];
    assert.ok(chosen, `${caseId}: no priced alternative to select`);

    const selected = session.selectAlternative(chosen.alternative.alternative_id);
    assert.equal(selected.ok, true, `${caseId}: selection refused - ${selected.error}`);
    session.setScenario({ evidence_period: 'Reopen regression period', support_eur: 0 });
    if (payloadUsesRealPack) {
      session.setScenario({ selected_alternative_id: chosen.alternative.alternative_id });
    }

    const beforeSave = {
      scenario: JSON.parse(JSON.stringify(session.getScenario())),
      result: JSON.parse(JSON.stringify(session.getResult()))
    };
    assert.ok(beforeSave.scenario.selected_alternative_id,
      `${caseId}: the working session has no selected alternative, so the reopen comparison is vacuous`);

    const saved = session.cases.save(caseId,
      { scenario: beforeSave.scenario, result: beforeSave.result, part_number: caseObject.pn },
      { expected_version: 0, state: 'ready_for_review', owner_role: 'case_owner',
        next_action: 'confirm after reopen', recorded_by: 'ux_reopen' });
    assert.equal(saved.ok, true, `${caseId}: save refused - ${saved.error}`);

    /* The reopen: a new module scope, an empty working record, the same case
       record read back from storage. Nothing from the session above carries over
       except the bytes in storage. */
    const reopened = loadApp({ storage, hash: hashFor(caseId, 'action') });
    const live = reopened.getScenario();
    const onDisk = reopened.cases.load(caseId).revisions.slice(-1)[0].record.scenario;
    const fresh = reopened.scenario.defaults(caseId);

    const diff = describeDiff(live, onDisk, COMPARED_KEYS);
    assert.equal(diff.length, 0,
      `${caseId}: the reopened page does not show the saved revision. Differences: ${diff.join('; ')}`);

    assert.equal(same(live, fresh, COMPARED_KEYS), false,
      `${caseId}: the reopened page is indistinguishable from a fresh default, so this proves nothing`);

    /* Both results, from the reopened record, must equal what was saved. */
    assert.equal(same(reopened.getResult(), beforeSave.result, RESULT_KEYS), true,
      `${caseId}: the reopened record does not reproduce the saved result. Differences: `
      + `${describeDiff(reopened.getResult(), beforeSave.result, RESULT_KEYS).join('; ')}`);
  }
});

test('the reopened record keeps the saved version and record id instead of treating a restore as an edit', () => {
  for (const caseId of CASES) {
    const storage = makeStorage();
    const session = loadApp({ storage, hash: hashFor(caseId, 'objectives') });
    const caseObject = payload.cases.find((c) => c.id === caseId);
    const top = engine.rankAlternatives(caseObject, 'revenue', { payload })
      .ranked.filter((x) => x.result.ok)[0];
    session.selectAlternative(top.alternative.alternative_id);
    session.setScenario({ evidence_period: 'Reopen regression period' });
    const savedScenario = JSON.parse(JSON.stringify(session.getScenario()));
    session.cases.save(caseId,
      { scenario: savedScenario, result: session.getResult(), part_number: caseObject.pn },
      { expected_version: 0, state: 'ready_for_review', recorded_by: 'ux_reopen' });

    const reopened = loadApp({ storage, hash: hashFor(caseId, 'action') });
    const live = reopened.getScenario();

    /* The measured fault: the restore went through store.set(), which is an edit
       path. It diffed the patch, bumped the version and re-derived the record id,
       so the reopened page reported <case>:v2 while the revision on disk was v3. */
    assert.equal(live.version, savedScenario.version,
      `${caseId}: the reopen bumped the scenario version (${savedScenario.version} on disk, `
      + `${live.version} live). A restore is not an edit.`);
    assert.equal(live.scenario_id, savedScenario.scenario_id,
      `${caseId}: the reopen re-derived the record id (${savedScenario.scenario_id} on disk, `
      + `${live.scenario_id} live)`);
    assert.equal(live.scenario_id, `${caseId}:v${live.version}`,
      `${caseId}: the record id and version disagree with each other`);
  }
});

test('a quantity derived from the selected alternative survives the reopen as a value, not as a re-derivation', () => {
  /* The likely casualty named in the brief. Selecting an alternative that carries
     a volume assumption derives quantity_after; a fresh default holds null. If the
     reopen re-selected the alternative, or dropped the derived value, the live
     quantity would differ from the saved one while the saved record stayed right.
     So this check needs a case whose default really is null and whose selection
     really is not. */
  const checked = [];
  for (const caseId of CASES) {
    const caseObject = payload.cases.find((c) => c.id === caseId);
    const defaults = scenarioModule.makeScenarioStore(payload, engine).defaults(caseId);
    if (defaults.quantity_after !== null) continue;

    const withVolume = caseObject.alternatives.filter((a) => a.volume_assumption);
    if (!withVolume.length) continue;

    const storage = makeStorage();
    const session = loadApp({ storage, hash: hashFor(caseId, 'objectives') });
    const rendered = engine.rankAlternatives(caseObject, 'revenue', { payload })
      .ranked.find((x) => x.alternative.alternative_id === withVolume[0].alternative_id);
    assert.ok(rendered && rendered.result.ok, `${caseId}: the volume alternative is not priced`);
    const derived = rendered.result.quantity_after;
    assert.notEqual(derived, defaults.quantity_after,
      `${caseId}: the derived quantity equals the default, so this check is vacuous`);

    session.selectAlternative(withVolume[0].alternative_id);
    const savedScenario = JSON.parse(JSON.stringify(session.getScenario()));
    assert.equal(savedScenario.quantity_after, derived,
      `${caseId}: the selection did not carry the derived quantity onto the record`);
    session.cases.save(caseId,
      { scenario: savedScenario, result: session.getResult(), part_number: caseObject.pn },
      { expected_version: 0, state: 'ready_for_review', recorded_by: 'ux_reopen' });

    const reopened = loadApp({ storage, hash: hashFor(caseId, 'action') });
    const live = reopened.getScenario();
    assert.equal(live.quantity_after, derived,
      `${caseId}: quantity_after did not survive the reopen `
      + `(saved ${derived}, live ${JSON.stringify(live.quantity_after)})`);
    assert.equal(live.selected_alternative_id, withVolume[0].alternative_id,
      `${caseId}: selected_alternative_id did not survive the reopen`);
    assert.equal(live.objective, savedScenario.objective,
      `${caseId}: objective did not survive the reopen`);
    assert.equal(reopened.getResult().quantity_after, derived,
      `${caseId}: the reopened calculation does not use the saved quantity`);
    checked.push(`${caseId}=${derived} (default ${JSON.stringify(defaults.quantity_after)})`);
  }
  assert.ok(checked.length > 0,
    'no case in this payload has both a null default quantity and a volume alternative, '
    + 'so the derived-quantity reopen path was not exercised');
});

test('a case with no saved revision still opens on its fresh default', () => {
  /* The negative control. A restore that ran for every case, or that wrote a
     partial record, would break the first-run experience. */
  for (const caseId of CASES) {
    const storage = makeStorage();
    const first = loadApp({ storage, hash: hashFor(caseId, 'action') });
    const fresh = first.scenario.defaults(caseId);
    assert.equal(same(first.getScenario(), fresh, COMPARED_KEYS), true,
      `${caseId}: a case with nothing saved did not open on its default. Differences: `
      + `${describeDiff(first.getScenario(), fresh, COMPARED_KEYS).join('; ')}`);
  }
});

test('the restore carries only declared scenario fields, and never an undeclared one', () => {
  const caseId = CASES[0];
  const storage = makeStorage();
  const session = loadApp({ storage, hash: hashFor(caseId, 'objectives') });
  const caseObject = payload.cases.find((c) => c.id === caseId);
  const top = engine.rankAlternatives(caseObject, 'revenue', { payload })
    .ranked.filter((x) => x.result.ok)[0];
  session.selectAlternative(top.alternative.alternative_id);
  /* A field that is not on the scenario contract, saved the way a hostile or
     older record could carry one. */
  const poisoned = JSON.parse(JSON.stringify(session.getScenario()));
  poisoned.support_direction_smuggled = 'from_supplier';
  poisoned.discount_percent = 7.5;
  session.cases.save(caseId,
    { scenario: poisoned, result: session.getResult(), part_number: caseObject.pn },
    { expected_version: 0, state: 'ready_for_review', recorded_by: 'ux_reopen' });

  const reopened = loadApp({ storage, hash: hashFor(caseId, 'action') });
  const live = reopened.getScenario();
  assert.equal(Object.prototype.hasOwnProperty.call(live, 'support_direction_smuggled'), false,
    'an undeclared field was carried from the saved revision into the working record');
  assert.equal(Object.prototype.hasOwnProperty.call(live, 'discount_percent'), false,
    'an undeclared field was carried from the saved revision into the working record');
  Object.keys(live).forEach((k) => {
    assert.ok(contracts.SCENARIO_FIELDS.indexOf(k) >= 0,
      `the working record carries "${k}", which the scenario contract does not declare`);
  });
  assert.equal(live.selected_alternative_id, top.alternative.alternative_id,
    'the declared part of the same revision was not restored');
});

test('only the reopened case is restored; the other cases keep their own defaults', () => {
  const [first, second] = CASES;
  const storage = makeStorage();
  const session = loadApp({ storage, hash: hashFor(first, 'objectives') });
  const caseObject = payload.cases.find((c) => c.id === first);
  const top = engine.rankAlternatives(caseObject, 'revenue', { payload })
    .ranked.filter((x) => x.result.ok)[0];
  session.selectAlternative(top.alternative.alternative_id);
  session.setScenario({ evidence_period: 'Reopen regression period' });
  const savedScenario = JSON.parse(JSON.stringify(session.getScenario()));
  session.cases.save(first,
    { scenario: savedScenario, result: session.getResult(), part_number: caseObject.pn },
    { expected_version: 0, state: 'ready_for_review', recorded_by: 'ux_reopen' });

  const reopened = loadApp({ storage, hash: hashFor(first, 'action') });
  assert.equal(same(reopened.getScenario(), savedScenario, COMPARED_KEYS), true,
    `${first}: not restored`);

  /* Naming the other case in a live session is a case switch, not a reopen. It
     must not be handed the first case's revision, and the first case's saved
     revision must still be on disk untouched. */
  const otherDefault = reopened.scenario.defaults(second);
  assert.equal(same(reopened.scenario.get(second), otherDefault, COMPARED_KEYS), true,
    `${second}: an untouched case did not show its own default`);
  assert.equal(JSON.stringify(reopened.cases.load(first).revisions.slice(-1)[0].record.scenario),
    JSON.stringify(savedScenario), `${first}: the saved revision changed underneath the reopen`);
});

test('the reopened page reports the same consistency verdict as the saved revision', () => {
  const caseId = CASES[0];
  const storage = makeStorage();
  const session = loadApp({ storage, hash: hashFor(caseId, 'objectives') });
  const caseObject = payload.cases.find((c) => c.id === caseId);
  const top = engine.rankAlternatives(caseObject, 'revenue', { payload })
    .ranked.filter((x) => x.result.ok)[0];
  session.selectAlternative(top.alternative.alternative_id);
  session.setScenario({ evidence_period: 'Reopen regression period' });
  const savedScenario = JSON.parse(JSON.stringify(session.getScenario()));
  session.cases.save(caseId,
    { scenario: savedScenario, result: session.getResult(), part_number: caseObject.pn },
    { expected_version: 0, state: 'ready_for_review', recorded_by: 'ux_reopen' });

  const reopened = loadApp({ storage, hash: hashFor(caseId, 'action') });
  const live = reopened.getScenario();
  const original = scenarioModule.makeScenarioStore(payload, engine);
  Object.keys(savedScenario).forEach((k) => {
    if (contracts.SCENARIO_FIELDS.indexOf(k) >= 0) original.get(caseId)[k] = savedScenario[k];
  });
  const expected = original.consistency(caseId);
  const observed = reopened.consistency();
  assert.equal(observed.ok, expected.ok,
    `the reopened consistency verdict differs from the saved record's: `
    + `${JSON.stringify(observed)} vs ${JSON.stringify(expected)}`);
  assert.equal(observed.ok, true,
    'the reopened record says the ranked option and the working record disagree, so the case would '
    + 'not be saveable after a reopen');
  assert.equal(live.scenario_id, savedScenario.scenario_id, 'record id moved on reopen');
});
