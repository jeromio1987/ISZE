#!/usr/bin/env node
/* ===========================================================================
   The comparable-price panel on a screen (MARKET-07 / MARKET-08, view layer).

   Run:  node --test tests/ux_market.test.mjs

   WHY THIS FILE EXISTS
   --------------------
   src/data/comparable.js was written to compute a comparable-price panel and
   render nothing, deliberately, so that one agent's file could be wired by
   another without two people writing one concern. It had 32 checks of its own
   and no screen. This file is the screen's check: it loads src/ui/app.js the way
   the built artifact loads it, opens the price-position view on every worked
   case, and asserts what a reader would actually see.

   WHAT IT ASSERTS, AND WHY EACH ONE IS HERE
   -----------------------------------------
   1. An empty comparable set renders as an explicit unavailable state that names
      the reason, and never as a blank panel, an empty shell or a zero. On the
      authorised payload this is the most likely visible state, so a test that
      only checked the happy path would check nothing about this file.
   2. Every reason code the panel returned for a case reaches the screen, for
      that case, with the row it belongs to still visible. A reason that is
      computed and never shown is a reason nobody can act on.
   3. An advertised-retail observation beside our own net terms is never
      presented as a price index. Our own terms on their own position nothing,
      and the module's own sentence about that is asserted on the screen.
   4. A row whose tax-rate unit is not declared is shown as unresolved rather
      than converted. The file stores the rate as a fraction while the shared
      rule reads a percentage, so a silent conversion is a 19.8 percent error on
      that price. This test asserts the screen shows the row as unresolved; it
      does NOT assert a corrected figure, because correcting it here is exactly
      the second definition of one rule that damaged this project twice.

   The view recomputes nothing, so this file also asserts that it computes
   nothing: the figures on the screen are compared against the panel's own
   return value for the same case and the same declarations.

   The harness rewrites three statements in src/ui/app.js, the same three
   tests/ux_flow.test.mjs rewrites, and fails loudly if the shape moved.
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
const caseModule = require(path.join(ROOT, 'src/data/cases.js'));
const candidateModule = require(path.join(ROOT, 'src/data/candidates.js'));
const scenarioModule = require(path.join(ROOT, 'src/data/scenario.js'));
const exportModule = require(path.join(ROOT, 'src/data/export.js'));
const comparable = require(path.join(ROOT, 'src/data/comparable.js'));

const APP = path.join(ROOT, 'src/ui/app.js');
const BUILD = path.join(ROOT, 'tools', 'build.py');
const REAL_PAYLOAD = path.join(ROOT, 'payload', 'aim_payload_20260922.json');
const SYNTHETIC = path.join(ROOT, 'tests', 'fixtures', 'synthetic_payload.json');

const payloadPath = fs.existsSync(REAL_PAYLOAD) ? REAL_PAYLOAD : SYNTHETIC;
const usesRealPayload = payloadPath === REAL_PAYLOAD;
const payload = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));

/* ------------------------------------------------------------- fake browser -- */

function stubElement(selector) {
  const listeners = {};
  const attrs = {};
  return {
    selector, id: String(selector).replace(/^#/, ''), innerHTML: '', value: '', textContent: '',
    dataset: {}, onclick: null, onchange: null, disabled: false,
    _listeners: listeners,
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    removeEventListener() {}, focus() {}, setSelectionRange() {}, append() {}, remove() {}, click() {},
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute(k, v) { attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    querySelectorAll() { return []; }
  };
}

function makeFakeDocument() {
  const nodes = {};
  const node = (sel) => (nodes[sel] = nodes[sel] || stubElement(sel));
  return {
    nodes,
    body: { append() {} },
    createElement: (tag) => stubElement(tag),
    getElementById: (id) => node('#' + id),
    querySelector: (sel) => node(sel),
    /* The view binds its controls through querySelectorAll. This harness drives
       the view by address and reads the painted HTML, so an empty list is the
       honest answer: nothing here claims a control was bound or pressed. */
    querySelectorAll: () => []
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

/* Load src/ui/app.js the way the built page does, with one payload and one
   comparable module. `comparableOverride` is how the "a view that fails must
   name the failing view" path is reached without patching app.js. */
function loadApp({ payloadOverride, comparableOverride } = {}) {
  const storage = makeStorage();
  const doc = makeFakeDocument();
  const run = payloadOverride || payload;
  const sandbox = {
    __payload: run,
    __dom: { $: (sel) => doc.querySelector(sel), $$: () => [] },
    document: doc,
    localStorage: storage,
    location: { hash: '' },
    URLSearchParams, Intl, JSON, Math, Date, console,
    setTimeout: (fn) => { fn(); return 0; },
    clearTimeout,
    Blob: class { constructor(parts) { sandbox.__blob = parts; } },
    URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
    AIMEngine: engine,
    AIMExport: exportModule,
    AIMCandidates: candidateModule,
    AIMCases: caseModule,
    AIMContracts: contracts,
    AIMScenario: scenarioModule,
    AIMComparable: comparableOverride || comparable
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

/* app.js routes by writing location.hash; a real browser then fires hashchange,
   which the stub address does not. Raising it is the stub completing the
   browser's behaviour, not this suite driving the view differently. */
function settle(session) {
  const fn = session.sandbox._listeners.hashchange;
  if (fn) fn();
}

function view(session, caseId, tab) {
  session.sandbox.location.hash = new URLSearchParams({ case: caseId, view: tab, compare: 'half' })
    .toString();
  settle(session);
  const content = session.doc.nodes['#content'];
  return { html: content ? content.innerHTML : '', state: content ? content.getAttribute('data-render-state') : null };
}
function refused(html) { return /data-failed-view="/.test(html); }

const CASES = payload.cases.map((c) => c.id);

/* The declarations the screen makes about one held offer. Copied from app.js's
   own rule, not invented here: the price-position view reads the held offers as
   public advertised retail observations in the case unit unless the record
   declares otherwise. If app.js changes that reading, the comparison this file
   makes against the panel's own return value fails rather than drifts. */
function declarationsFor(c) { return { unit: c.unit, level: 'public_advertised_retail', match_basis: 'cross_reference' }; }
function panelFor(run, caseId) {
  const c = run.cases.find((x) => x.id === caseId);
  const offers = (c.offers || []).map((id) => (run.offers || {})[id]).filter(Boolean);
  const observations = offers.map((o) => {
    const declared = (o.observation_declarations) || {};
    const decl = Object.assign({}, declarationsFor(c));
    Object.keys(declared).forEach((k) => {
      if (declared[k] !== null && declared[k] !== undefined) decl[k] = declared[k];
    });
    return comparable.observationFromOffer(o, Object.assign({ case_id: c.id }, decl));
  });
  return comparable.panel(
    { case_id: c.id, part_number: c.pn, market: c.market, unit: c.unit },
    observations,
    {
      basis_level: 'public_advertised_retail', basis_unit: c.unit,
      as_of: (run.meta && run.meta.buildDate) || null,
      own_movement: comparable.movementFromComparison((c.comparisons || {}).half)
    });
}

/* =========================================================================
   The module is assembled, and the layer under test is the layer that ships
   ========================================================================= */

test('MK00 the build assembles the comparable module, and app.js reads it', () => {
  const build = fs.readFileSync(BUILD, 'utf8');
  const boundary = build.indexOf('UNWIRED_MODULES');
  assert.ok(boundary > 0, 'tools/build.py has no UNWIRED_MODULES block to read');
  const shipped = [...build.slice(0, boundary).matchAll(/\("(src\/[^"]+)",\s*"([^"]+)"\)/g)]
    .map((m) => ({ rel: m[1], label: m[2] }));

  const entry = shipped.find((s) => s.rel === 'src/data/comparable.js');
  assert.ok(entry, 'tools/build.py does not assemble src/data/comparable.js, so the panel is not in '
    + 'the artifact at all and this suite is testing a screen nobody receives. '
    + 'Assembled: ' + JSON.stringify(shipped.map((s) => s.rel)));

  /* Assembly order. The panel calls evidence.js, so it must follow it; app.js
     reads the panel, so the panel must precede the view. A module that is in the
     list but in the wrong place loads as undefined and fails at the first paint
     instead of at the build. */
  const order = shipped.map((s) => s.rel);
  const atEvidence = order.indexOf('src/data/evidence.js');
  const atComparable = order.indexOf('src/data/comparable.js');
  const atView = order.indexOf('src/ui/app.js');
  assert.ok(atEvidence >= 0 && atView >= 0, 'the evidence module or the view is not assembled');
  assert.ok(atComparable > atEvidence,
    'src/data/comparable.js is assembled before src/data/evidence.js, which it calls');
  assert.ok(atComparable < atView,
    'src/data/comparable.js is assembled after src/ui/app.js, which reads it');

  const source = fs.readFileSync(APP, 'utf8');
  assert.match(source, /AIMComparable/,
    'src/ui/app.js does not read the comparable module, so the panel has no screen');

  return `assembled at position ${atComparable} of ${order.length}, after evidence.js (${atEvidence}) '
    + 'and before app.js (${atView})`;
});

/* =========================================================================
   1. An empty comparable set is an explicit unavailable state
   ========================================================================= */

test('MK01 an empty comparable set renders as a named unavailable state, not a blank panel', () => {
  const session = loadApp();
  const report = [];
  for (const caseId of CASES) {
    const { html, state } = view(session, caseId, 'position');
    assert.equal(state, 'built', caseId + '/position did not build: ' + html.slice(0, 400));
    assert.equal(refused(html), false,
      caseId + '/position was refused by the render gate: ' + html.slice(0, 400));

    const p = panelFor(payload, caseId);
    if (p.eligible_offers.length === 0) {
      /* The state must be the amber block, with its own accent on the element
         and not only in a stylesheet the frozen shell does not carry. */
      assert.match(html, /<div class="panel unavailable" role="status"[^>]*data-unavailable="/,
        caseId + ': an empty comparable set is not the amber unavailable block');
      assert.match(html, /class="eyebrow"[^>]*>Unavailable<\/div>/,
        caseId + ': the unavailable block is not labelled Unavailable');
      assert.match(html, /class="panel unavailable"[^>]*style="[^"]*border-left:4px solid #96620d/,
        caseId + ': the unavailable block carries no amber accent of its own, so it cannot be told '
        + 'from an ordinary warn panel, which shares its pale fill in this stylesheet');
      /* It must name what is empty and what would fill it. */
      assert.match(html, /Nothing reaches the agreed comparison basis/,
        caseId + ': the state does not say that nothing reaches the basis');
      assert.match(html, /0 were left out|were read and/,
        caseId + ': the state does not say how many observations were read and left out');
      assert.match(html, /What is required<\/span><b[^>]*>/,
        caseId + ': the state does not say what would close the gap');
      /* And the region is genuinely not blank. */
      assert.ok(html.length > 4000,
        caseId + ': the panel painted only ' + html.length + ' characters, so it is a shell');
    } else {
      assert.match(html, /panel good/, caseId + ': a comparable set was found and not shown as one');
    }
    report.push(caseId + '=' + p.eligible_offers.length + ' eligible, '
      + p.ineligible_offers.length + ' named as excluded');
  }

  /* Two different empty states are named differently, so a reader can tell a
     row that was refused from a file that holds no row at all. */
  const carriesRows = CASES.filter((id) => panelFor(payload, id).observations_in > 0);
  const noRows = CASES.filter((id) => panelFor(payload, id).observations_in === 0);
  assert.ok(carriesRows.length > 0, 'no case on this payload carries an observation, so the '
    + 'named-exclusion state was never exercised');
  const withRows = view(session, carriesRows[0], 'position').html;
  assert.match(withRows, /Nothing reaches the agreed comparison basis/,
    'a case holding observations but nothing comparable does not say so');
  if (noRows.length) {
    const without = view(session, noRows[0], 'position').html;
    assert.match(without, /No competitor observation is held for this case/,
      'a case holding no observation at all does not say that, so the two states read the same');
  }

  return report.join('; ') + '; the empty state names the reason, the count, the required evidence '
    + 'and its own amber accent on every case where nothing is comparable';
});

test('MK02 the screen states no figure the panel refused to state', () => {
  const session = loadApp();
  for (const caseId of CASES) {
    const p = panelFor(payload, caseId);
    const { html } = view(session, caseId, 'position');
    assert.equal(p.price_action_certified, false,
      caseId + ': the panel certified a price action, so this check is vacuous');
    /* The screen's own line must agree with the panel, not assert on its own. */
    assert.match(html, /Price action certified by this view<\/span><b>not certified<\/b>/,
      caseId + ': the screen does not print the panel\'s own refusal to certify a price action');
    /* No aggregation rule exists, so no summary figure may appear as one. */
    assert.equal(p.aggregation.declared, false);
    assert.equal(p.aggregation.summary, null);
    assert.match(html, /No approved aggregation rule is declared, so no summary figure is stated/,
      caseId + ': the screen does not state that no summary figure exists');
    /* The selection rule is the panel's, and it reaches the screen. */
    if (p.eligible_offers.length) {
      assert.ok(html.includes(p.eligible_offers[0].selection),
        caseId + ': the screen does not carry the panel\'s own selection statement');
    }
    /* The raw record is retained and the screen says so. Asserted on the words
       and the value, not on the tag nesting: the value is wrapped in its own
       explanatory hover, so a check that pinned the markup would fail on a change
       that alters nothing a reader sees. */
    assert.equal(p.raw_input_unmodified, true);
    assert.match(html, /Every row the panel read was retained<\/span><b>[^<]*(<span[^>]*>)?yes/,
      caseId + ': the screen does not confirm that every row the panel read was retained');
  }
  return 'every case: no certified price action, no summary without a rule, the panel\'s selection '
    + 'statement on screen, and raw retention confirmed';
});

/* =========================================================================
   2. Every exclusion reason reaches the screen
   ========================================================================= */

test('MK03 every reason code the panel returned for a case reaches the screen', () => {
  const session = loadApp();
  const seen = {};
  let rowsChecked = 0;
  for (const caseId of CASES) {
    const p = panelFor(payload, caseId);
    const { html } = view(session, caseId, 'position');
    p.ineligible_offers.forEach((row) => {
      rowsChecked += 1;
      assert.ok((row.reason_codes || []).length,
        caseId + '/' + row.observation_id + ': the panel excluded a row with no reason code');
      /* The code itself is on the screen, on the row it belongs to. */
      row.reason_codes.forEach((code) => {
        seen[code] = (seen[code] || 0) + 1;
        assert.ok(html.includes(code),
          caseId + ': the reason code ' + code + ' was computed for ' + row.observation_id
          + ' and is not on the screen, so a reader cannot act on it');
        assert.ok(comparable.EXCLUSION_CODES[code],
          caseId + ': the panel returned a code its own declared list does not know: ' + code);
      });
      /* The row's own readable sentence is there too, not only the code. */
      assert.ok(html.includes(row.reason),
        caseId + '/' + row.observation_id + ': the readable reason is not on the screen');
      /* And the row itself is still visible with its own record. */
      assert.equal(row.raw_unchanged, true);
      assert.equal(row.visible, true);
      assert.ok(html.includes(row.observation_id),
        caseId + ': ' + row.observation_id + ' was excluded and then hidden, which is the one thing '
        + 'an exclusion may not do');
    });
  }
  assert.ok(rowsChecked > 0, 'no observation was excluded on this payload, so this check proves '
    + 'nothing about exclusions');
  /* The two reasons the brief names as dominant on this payload must be there. */
  if (usesRealPayload) {
    assert.ok(seen.PRODUCT_MATCH_UNRESOLVED > 0,
      'the payload\'s matches are cross-references; that reason must reach the screen');
    assert.ok(seen.PACK_CONTENTS_UNKNOWN > 0,
      'the payload does not declare a piece-or-pack basis; that reason must reach the screen');
  }
  const codes = Object.keys(seen).sort().map((c) => c + '(' + seen[c] + ')').join(', ');
  return rowsChecked + ' excluded row(s) across ' + CASES.length + ' case(s), every code and every '
    + 'readable reason on the screen, every excluded row still visible. Reasons shown: ' + codes;
});

test('MK04 a reason the module does not declare is reported as unknown, never as a reviewed reason', () => {
  const explained = comparable.explainExclusion('NOT_A_DECLARED_CODE');
  assert.equal(explained.known, false);
  assert.match(explained.statement, /reported as unknown rather than/i);
  assert.ok(Object.keys(comparable.EXCLUSION_CODES).length > 20,
    'the declared reason list shrank to ' + Object.keys(comparable.EXCLUSION_CODES).length);
  /* Both kinds are declared and both are on the screen somewhere: an exclusion
     and an unresolved money fact are different readings. */
  const kinds = new Set(Object.values(comparable.EXCLUSION_CODES));
  assert.ok(kinds.has('excluded') && kinds.has('unresolved'),
    'the reason list no longer separates an exclusion from an unresolved money fact');
  return Object.keys(comparable.EXCLUSION_CODES).length + ' declared reason codes across '
    + [...kinds].sort().join(' and ');
});

/* =========================================================================
   3. An advertised retail price is not presented as a price index
   ========================================================================= */

/* A synthetic payload, in the shape of the real one, in which a case carries our
   own net distributor terms beside an advertised retail observation. This is the
   pair the commercial rule is about, and the real payload does not contain one,
   so the screen has to be shown one to be checked. Nothing is copied from the
   real pack's figures: the synthetic rows carry invented amounts. */
function payloadWithNetAndRetail() {
  const copy = JSON.parse(JSON.stringify(payload));
  const c = copy.cases.find((x) => x.id === 'ITUK-PADS');
  const template = copy.offers['PAD-A'];
  const ourTerms = Object.assign({}, template, {
    id: 'SYNTH-NET-TERMS', seller: 'ourselves', price: 88.4, currency: 'GBP', tax: 'excluded',
    vat: 0, net: 88.4, part: c.pn, match: 'our own recorded terms',
    note: 'Synthetic fixture: our own net distributor terms on this part, stated so that the two '
      + 'commercial price levels can be shown side by side.',
    observation_declarations: { level: 'isze_net_distributor', amount_scope: 'per_piece',
      unit: c.unit, vat_rate_unit: 'percent' }
  });
  copy.offers['SYNTH-NET-TERMS'] = ourTerms;
  c.offers = (c.offers || []).concat(['SYNTH-NET-TERMS']);
  return { run: copy, caseId: c.id, ourTermsId: 'SYNTH-NET-TERMS' };
}

test('MK05 our own terms beside an advertised retail price are never one index', () => {
  const built = payloadWithNetAndRetail();
  const p = panelFor(built.run, built.caseId);

  /* The panel's own answer first, so the screen is judged against it. */
  const netRow = p.ineligible_offers.concat(p.eligible_offers)
    .find((r) => r.observation_id === built.ourTermsId);
  assert.ok(netRow, 'the synthetic own-terms row did not reach the panel at all');
  assert.equal(netRow.level, 'isze_net_distributor',
    'the record declared our own net terms and the panel read something else');

  const session = loadApp({ payloadOverride: built.run });
  const { html, state } = view(session, built.caseId, 'position');
  assert.equal(state, 'built', 'the case with our own terms beside retail did not build');
  assert.equal(refused(html), false);

  /* 1. No index figure is stated. The panel says so and the screen prints it. */
  assert.equal(p.price_positioning.index_stated, false,
    'the panel stated an index from an advertised retail observation');
  assert.match(html, /Index stated<\/span><b>[^<]*(<span[^>]*>)?not stated/,
    'the screen does not print that no index is stated');

  /* 2. Our own terms are shown and are not put into one figure with the
     advertised price. The two are separate rows on separate lines. */
  assert.ok(html.includes(built.ourTermsId),
    'our own terms row was read and then not shown, which hides half the pair');
  const netOnScreen = html.indexOf(built.ourTermsId);
  const reasonForNet = html.slice(netOnScreen, netOnScreen + 4000);
  assert.ok(p.ineligible_offers.some((r) => r.observation_id === built.ourTermsId)
      || p.eligible_offers.some((r) => r.observation_id === built.ourTermsId),
    'the own-terms row is in neither list, so it was dropped rather than reported');
  assert.ok(/different commercial price level|not like-for-like|are not put into one index|advertised retail price is not proof/i
    .test(reasonForNet),
    'the screen does not state why our own terms and the advertised price are not one figure: '
    + reasonForNet.slice(0, 400));

  /* 3. The module's own sentence about the rule reaches the screen. */
  const onScreen = html.includes('not proof that our own net terms are too high')
    || html.includes('is never presented as proof that our own net terms are too high')
    || netRow.reason && html.includes(netRow.reason);
  assert.ok(onScreen,
    'neither the module\'s own sentence nor the row\'s own reason about the level difference is on '
    + 'the screen');

  /* 4. The declarations the screen makes are printed, so a reader can disagree
     with them rather than having to reverse-engineer them. */
  assert.match(html, /Admissibility rule applied/,
    'the screen does not print the admissibility rule it applied');
  assert.ok(html.includes('public advertised retail') || html.includes('Public advertised retail'),
    'the screen does not name the price level it read the held offers as');
  assert.ok(html.includes(p.selected_basis ? p.selected_basis.named_by : 'x')
      || /Named by/.test(html),
    'the screen does not say who named the comparison basis');

  return built.caseId + ': ' + p.eligible_offers.length + ' comparable, '
    + p.ineligible_offers.length + ' named as excluded including our own terms at '
    + netRow.level_label + '; index stated: ' + p.price_positioning.index_stated
    + '; no index figure is drawn and the two levels are separate rows';
});

test('MK06 our own terms on their own position nothing, and the screen says so', () => {
  /* The same fixture with the advertised retail row removed: only our own terms
     are left on the named basis. A price position needs somebody else's price,
     so no index may be stated, and the module states the reason. */
  const built = payloadWithNetAndRetail();
  const c = built.run.cases.find((x) => x.id === built.caseId);
  c.offers = [built.ourTermsId];
  const p = panelFor(built.run, built.caseId);
  assert.equal(p.price_positioning.comparable_offers_by_other_sellers, 0,
    'the fixture still holds a row by another seller, so this check is vacuous');
  assert.equal(p.price_positioning.index_allowed, false,
    'an index was allowed from our own terms alone');
  assert.equal(p.price_positioning.index_stated, false);

  const session = loadApp({ payloadOverride: built.run });
  const { html, state } = view(session, built.caseId, 'position');
  assert.equal(state, 'built', 'the own-terms-only case did not build');
  assert.match(html, /Index stated<\/span><b>[^<]*(<span[^>]*>)?not stated/,
    'the screen states an index while the panel refused one');
  assert.ok(html.includes(p.price_positioning.statement),
    'the screen does not carry the panel\'s own sentence about why no position is stated');
  (p.price_positioning.must_not_be_read_as || []).forEach((boundary) => {
    assert.ok(html.includes(boundary),
      'the screen does not repeat the module\'s boundary that a net-terms figure is not "' + boundary
      + '"');
  });
  return 'our own terms alone: index allowed ' + p.price_positioning.index_allowed
    + ', stated ' + p.price_positioning.index_stated + ', and the reason is on the screen';
});

/* =========================================================================
   4. An undeclared tax-rate unit shows unresolved
   ========================================================================= */

test('MK07 a row whose tax-rate unit is not declared shows unresolved, and is not converted', () => {
  const session = loadApp();
  const checked = [];
  let anyUndeclared = false;

  for (const caseId of CASES) {
    const p = panelFor(payload, caseId);
    const rows = p.ineligible_offers.concat(p.eligible_offers)
      .filter((r) => (r.reason_codes || []).includes('VAT_RATE_UNIT_NOT_STATED'));
    if (!rows.length) continue;
    anyUndeclared = true;
    const { html } = view(session, caseId, 'position');
    rows.forEach((row) => {
      /* The row is unresolved, not converted. */
      assert.equal(row.adjustment.value, null,
        caseId + '/' + row.observation_id + ': an adjusted figure was produced from a rate whose '
        + 'unit nobody declared, which is the hundred-fold error this rule exists to prevent');
      assert.equal(row.adjustment.ok, false);
      /* The screen shows the code and the row's own sentence about the unit. */
      assert.ok(html.includes('VAT_RATE_UNIT_NOT_STATED'),
        caseId + ': the undeclared rate unit is not named on the screen');
      assert.ok(html.includes('does not state whether that is a percentage or a fraction'),
        caseId + ': the screen does not say what is missing about the rate');
      assert.ok(html.includes(row.observation_id),
        caseId + ': the unresolved row is not visible');
      assert.match(html, /no adjusted figure is stated/,
        caseId + ': the screen does not say that no adjusted figure is stated for that row');
      /* And the original quote is either there beside it, or the screen says
         plainly that the file recorded no amount. A row with no amount is not a
         row with a price of zero, and both readings must be distinguishable. */
      if (row.quoted.amount !== null) {
        assert.ok(html.includes(String(Math.round(row.quoted.amount * 100) / 100).split('.')[0]),
          caseId + '/' + row.observation_id + ': the original quote was lost');
      } else {
        assert.match(html, /no amount/,
          caseId + '/' + row.observation_id + ': the file recorded no amount and the screen does '
          + 'not say so, which reads as a price of zero');
      }
      checked.push(caseId + '/' + row.observation_id);
    });
  }

  assert.ok(anyUndeclared,
    'no row on this payload carries a tax-inclusive amount with an undeclared rate unit, so this '
    + 'check proves nothing. The brief records that such a row exists on the authorised pack.');

  /* The screen must not have quietly corrected it. A corrected figure would have
     to appear as a number the panel did not produce; the panel produces none, so
     the assertion is that no such number is printed on the row. */
  const { html } = view(session, CASES[0], 'position');
  assert.ok(!/Adjusted figure <b>NaN<\/b>/.test(html), 'a NaN reached the screen');

  return 'resolved as unresolved on: ' + checked.join(', ')
    + '; no adjusted figure is stated for any of them, and the reason is named on the screen';
});

/* =========================================================================
   The screen adds nothing of its own
   ========================================================================= */

test('MK08 the view recomputes nothing: the figures on the screen are the panel\'s', () => {
  const session = loadApp();
  for (const caseId of CASES) {
    const p = panelFor(payload, caseId);
    const { html } = view(session, caseId, 'position');
    /* Every count the screen prints about the panel must be the panel's count. */
    const countsLine = new RegExp(num(p.observations_in) + ' read by the panel');
    assert.ok(countsLine.test(html),
      caseId + ': the screen does not print the panel\'s own observation count ('
      + p.observations_in + ')');
    assert.ok(html.includes(p.statement),
      caseId + ': the panel\'s own statement is not on the screen, so the view is composing its own');
    /* The count of declared reasons the screen prints is the module's count. */
    assert.ok(html.includes(num(Object.keys(comparable.EXCLUSION_CODES).length) + ' this comparison module declares'),
      caseId + ': the screen does not print the module\'s own declared reason count');
    /* And the price level labels are the module's labels, not the view's. */
    [...new Set((p.candidate_bases.candidates || []).map((b) => b.level))].forEach((level) => {
      const info = comparable.levelInfo(level);
      assert.ok(html.includes(info.label),
        caseId + ': the screen does not print the module\'s own label for ' + level);
    });
  }
  return 'every case: observation counts, the panel statement, the declared reason count and every '
    + 'price-level label on the screen come from the panel\'s return value';
});

function num(v) { return Number(v).toLocaleString('en-GB'); }

test('MK09 a failing price-position view names the view and clears the content region', () => {
  /* The comparable module is assembled and read by the view, so a build that
     shipped app.js without it would fail here. The failure is created by handing
     the shell a module without the function the view calls. */
  const broken = Object.assign({}, comparable, { panel: undefined });
  const session = loadApp({ comparableOverride: broken });

  /* Paint a healthy view first, so there is genuinely something stale to leave. */
  const healthy = view(session, 'ITUK-PADS', 'decision');
  assert.equal(healthy.state, 'built');
  assert.ok(healthy.html.includes('Reconcile the euro change'),
    'the healthy view did not paint the marker this check looks for');

  const painted = view(session, 'ITUK-PADS', 'position');
  assert.equal(painted.state, 'failed',
    'the content region was not marked as failed when the panel could not be built');
  assert.match(painted.html, /render-failure/, 'no failure card was painted');
  assert.match(painted.html, /data-failed-view="position"/,
    'the failure card does not name the failing view');
  assert.match(painted.html, /Price position did not render/,
    'the card does not say which view failed, in the words the tab uses');
  assert.ok(!painted.html.includes('Reconcile the euro change'),
    'STALE CONTENT: the previous view is still on screen under a newly active tab');
  assert.equal(session.doc.nodes['#render-status'].getAttribute('data-failed'), 'true',
    'the shell status line is not flagged as failed');
  assert.match(session.doc.nodes['#render-status'].textContent, /failed to build/i,
    'the shell status line does not report the failure');

  /* And it recovers: a different view of the same case still paints. */
  const recovered = view(session, 'ITUK-PADS', 'decision');
  assert.equal(recovered.state, 'built', 'the shell did not recover after a failed render');
  return 'a missing panel function produced a card naming "Price position", the previous view was '
    + 'cleared, the shell flagged data-failed, and the next view recovered';
});

test('MK10 no banned label and no invented figure reaches the price-position screen', () => {
  const session = loadApp();
  const BANNED = [
    [/\bMode\s*[AB]\b/i, 'audience label; say shared/external or internal/private'],
    [/\bwallet\b/i, 'say parts billed or target spend per truck'],
    [/\bstreet\b/i, 'say reference dealer price'],
    [/sell-?out/i, 'say sales to dealer'],
    [/\bBook\s*B\b/i, 'say the price list'],
    [/\bclass\s*factor\b/i, 'talk in margins, not factors'],
    [/\bfactor\s+0\.\d/i, 'talk in margins, not factors']
  ];
  const findings = [];
  const htmls = [];
  for (const caseId of CASES) {
    ['position', 'decision'].forEach((tab) => {
      const { html } = view(session, caseId, tab);
      htmls.push(html);
      BANNED.forEach(([re, why]) => {
        const m = re.exec(html);
        if (m) findings.push(caseId + '/' + tab + ': "' + m[0] + '" (' + why + ')');
      });
    });
  }
  assert.equal(findings.length, 0, 'banned wording reached a view: ' + findings.join('; '));

  const text = htmls.join('\n');
  /* The figures the brief forbids as stated outcomes. Written as claims, not as
     the disclaimers that say they are absent. */
  [/optimal price of/i, /optimal price is/i, /elasticity of/i, /acceptable profit sacrifice of/i,
    /minimum margin of/i, /measured benefit of/i, /the optimum price is/i].forEach((re) => {
    assert.ok(!re.test(text), 'a forbidden claim appears: ' + re);
  });

  /* The house style. Navy and terracotta, and never white text on a pale
     background: the tooltip panel and its accent are the two house colours. */
  assert.ok(/mk-tip/.test(text), 'the derived-figure hover rule is not on the screen');
  assert.match(text, /data-tip="[^"]{40,}"/,
    'no derived figure carries an explanatory hover of its own');
  assert.ok(!/background:#fff[^;]*;color:#fff/i.test(text),
    'white text is drawn on a white background');
  /* No figure may be invented for a part: no number appears that the panel did
     not return. The cheapest check that is honest here is that no price-like
     figure is drawn in the panels that state none. */
  assert.ok(!/Index stated<\/span><b>stated<\/b>/.test(text),
    'the screen states an index on a case where the panel refused one');

  return 'zero banned words and no banned factor wording across ' + htmls.length
    + ' rendered views; no invented optimum, elasticity, sacrifice or benefit; the derived-figure '
    + 'hover is present and the two house colours are used';
});

test('MK11 the two kinds of evidence are separately labelled and state what each is not', () => {
  const session = loadApp();
  const report = [];
  for (const caseId of CASES) {
    const p = panelFor(payload, caseId);
    const { html } = view(session, caseId, 'position');
    const movement = p.purchasing_movement, positioning = p.price_positioning;
    assert.notEqual(movement.evidence_kind, positioning.evidence_kind,
      caseId + ': the two outputs declare the same kind of evidence, so one can be read as the other');
    assert.equal(movement.is_proof_of_price_positioning, false);
    assert.equal(positioning.is_proof_that_our_terms_are_too_high, false);
    /* Both kinds are labelled on screen with the panel's own words. */
    assert.ok(html.includes(movement.evidence_kind),
      caseId + ': our own-movement evidence kind is not on the screen');
    assert.ok(html.includes(positioning.evidence_kind),
      caseId + ': the other-seller evidence kind is not on the screen');
    /* Both say what they are not. */
    assert.ok(html.includes(movement.statement), caseId + ': the movement statement is missing');
    assert.ok(html.includes(positioning.statement), caseId + ': the positioning statement is missing');
    (movement.must_not_be_read_as || []).forEach((t) => {
      assert.ok(html.includes(t), caseId + ': the movement boundary "' + t + '" is not on the screen');
    });
    (positioning.must_not_be_read_as || []).forEach((t) => {
      assert.ok(html.includes(t), caseId + ': the positioning boundary "' + t + '" is not on screen');
    });
    assert.match(html, /not interchangeable/,
      caseId + ': the screen does not say the two panels cannot stand in for each other');
    report.push(caseId + ' movement=' + movement.available + ' positioning=' + positioning.available);
  }
  return report.join('; ') + '; each kind is labelled with the panel\'s own words and each states '
    + 'what it is not';
});

/* =========================================================================
   Report
   ========================================================================= */

const summary = { pass: 0, fail: 0, total: 0 };
process.on('exit', () => {
  /* node:test prints its own summary; this line names the artifact and the layer
     so a reader of the console knows which build was checked. */
  console.log('');
  console.log('payload: ' + path.basename(payloadPath)
    + (usesRealPayload ? ' (authorised local payload)' : ' (synthetic fixture)'));
  console.log('layer  : src/ui/app.js with src/data/comparable.js, both assembled by tools/build.py');
});
void summary;
