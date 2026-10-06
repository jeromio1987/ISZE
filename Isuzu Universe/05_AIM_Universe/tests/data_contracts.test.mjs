#!/usr/bin/env node
/* ===========================================================================
   Data-contract tests for the AIM corrective build.

   Owner: the data layer. These tests cover the source manifest, the cost-basis
   resolver, the evidence model and the candidate model - the four defects
   F04, DATA-01 to DATA-08, F10 and MARKET-01 to MARKET-06 that this layer owns.

   How to run
     node --test tests/data_contracts.test.mjs

   What is asserted, and why each one matters
     - An invalid date is unresolved and does not become October. A date outside
       every documented window is unresolved. 2026-09-22 resolves SEP26 and
       2026-10-01 resolves OCT26. Without these three, one screen can advertise a
       single unchanged-offer baseline while carrying two cost bases.
     - The October basis has no declared end; the end is reconstructed from its
       stated rate window and the reconstruction is reported.
     - A duplicate import does not double a quantity. A correction replaces its
       declared predecessor rather than adding to it.
     - The unclassified remainder stays visible and its size is reported.
     - Row counts and unique-part counts are reported as two different numbers.
     - A forward cost is never applied to a recorded historical quantity and
       labelled historical actual gross profit.
     - A comparison is refused when the period, the sales stage or the unit
       disagree, and a list price is never combined with a billing average or a
       competitor's advertised price.
     - ITUK is not IUK and UMI is not UTI.
     - A relationship is not an approval to fit.

   Data
     Two fixtures are used. A RESTRICTED-SHAPED fixture with invented values is
     generated on the fly and is the one asserted against fixed values. It carries
     shape and arithmetic relationships only: no real part number, description,
     cost, billing figure, quantity or rate from the payload appears anywhere in
     this file, because a tracked file is versioned forever. Its two copies are
     written under payload/, which .gitignore excludes, and are marked restricted.

     If the authorised pack payload is present on this machine it is read
     read-only for the structural checks. Those checks assert counts and
     relationships, never a restricted figure, and an identifier read from the
     payload is compared in memory rather than printed into this file.

   Nothing here weakens an assertion to obtain a green result. Where a source
   fact is unresolved, the test asserts that it is unresolved.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const require = createRequire(import.meta.url);

const manifest = require(path.join(ROOT, 'src', 'data', 'manifest.js'));
const costbasis = require(path.join(ROOT, 'src', 'data', 'costbasis.js'));
const evidence = require(path.join(ROOT, 'src', 'data', 'evidence.js'));
const candidates = require(path.join(ROOT, 'src', 'data', 'candidates.js'));
const engine = require(path.join(ROOT, 'src', 'engine', 'engine.js'));

/* The pack payload sits beside this module's project, under the same working
   area: 05_AIM_Universe/../06_Working/_aim_pack_20260922/_payload.json. */
const AUTHORISED_PAYLOAD = path.resolve(ROOT, '..', '06_Working', '_aim_pack_20260922',
  '_payload.json');

/* How the authorised-payload checks are written. A COUNT is pinned: the payload's
   row count is a scale figure, not a cost, and it is already cited in the progress
   record. A restricted FIGURE is not: no supplier cost, list price, observed
   billing amount or unit price is copied out of the payload into this tracked
   file. Where such a value matters, the check asserts a relationship between two
   things read from the payload in memory rather than a literal copied from it. */
const AUTHORISED_ROWS = 10543;

/* ------------------------------------------------------------- fixtures -- */

const SEP = '\u001f';

/* A small restricted-SHAPED fixture. Every value below is invented and rounded:
   the rates, the source discounts, the costs, the billing, the quantities and the
   part references. It keeps the shape and the arithmetic relationships the tests
   depend on, so the same code is exercised, and it quotes no figure the payload
   holds. Written under payload/, which .gitignore excludes, and marked restricted
   so nobody mistakes it for shareable. */
function restrictedFixture() {
  const bases = [
    { basis_id: 'HIST', name: 'Historical', jpy_per_eur: 160.0, status: 'historical',
      rate_window: '1 Oct 2025 to 31 Mar 2026', discount: { J: 0.70 },
      offer_effective_from: '', use: 'historical actual only' },
    { basis_id: 'SEP26', name: 'September 2026 forward', jpy_per_eur: 170.0, status: 'forward',
      rate_window: '1 Apr 2026 to 30 Sep 2026', discount: { J: 0.75 },
      offer_effective_from: '2026-04-01', offer_effective_to: '2026-09-30',
      use: 'cost for an offer effective on or before 30 Sep 2026' },
    { basis_id: 'OCT26', name: 'October 2026 forward', jpy_per_eur: 180.0, status: 'forward',
      rate_window: '1 Oct 2026 to 31 Mar 2027', discount: { J: 0.75 },
      offer_effective_from: '2026-10-01',
      use: 'cost for an offer effective on or after 1 Oct 2026' }
  ];
  const cellSet = (hist, sep, oct) => ({
    HIST: { name: 'Historical', jpy_per_eur: 160.0, rate_window: '1 Oct 2025 to 31 Mar 2026',
      source_discount: 0.70, cost_eur: hist, status: 'historical' },
    SEP26: { name: 'September 2026 forward', jpy_per_eur: 170.0,
      rate_window: '1 Apr 2026 to 30 Sep 2026', source_discount: 0.75, cost_eur: sep,
      status: 'forward' },
    OCT26: { name: 'October 2026 forward', jpy_per_eur: 180.0,
      rate_window: '1 Oct 2026 to 31 Mar 2027', source_discount: 0.75, cost_eur: oct,
      status: 'forward' }
  });
  const costRecord = (pn, description, unit, values) => ({
    part_number: pn, description, tier: 'Genuine', unit, currency: 'EUR',
    cost_type: 'parts purchase cost (supplier purchase cost)',
    formula: 'Base price (JPY) / JPY per EUR x source discount',
    inputs: { base_price_jpy: 10000, price_class: 'V', origin_code: 'J' },
    cost_bases: cellSet(values[0], values[1], values[2]),
    default_forward_basis: 'OCT26', default_forward_cost_eur: values[2],
    historical_cost_eur: values[0],
    base_price_source: 'restricted test fixture - invented value',
    discount_source: 'restricted test fixture - invented value',
    fx_source: 'restricted test fixture - invented value',
    includes: { freight: false, duty: false, overheads: false, distributor_kickbacks: false,
      other_operating_costs: false, invoice_discount_deducted_twice: false },
    exclusion_note: 'Parts purchase cost only. Freight, duty, overheads and distributor '
      + 'kickbacks are excluded and the invoice discount is not deducted twice.',
    restricted: 'INTERNAL ONLY - must not appear in a distributor export',
    list_eur: 90.0, list_source: 'restricted test fixture - invented value',
    list_valid_from: '2026-03-13', base_price_note: null, cost_gap_note: null, status: 'verified'
  });
  const candidate = (distributor, pn, description, qty, billing, unitPrice, list, cost, reasons,
    competitor, unresolvedInputs, decisionReady) => ({
    distributor, part_number: pn, description, billed_qty: qty, observed_billing_eur: billing,
    observed_unit_price: unitPrice, list_eur: list,
    verified_cost_eur_oct26: cost, base_price_move_jpy: 2500, base_price_move_pct: 20.0,
    selection_reasons: reasons, competitor_evidence: competitor,
    unresolved_inputs: unresolvedInputs, decision_ready: decisionReady
  });

  const caseA = {
    id: 'TEST-PADS', market: 'TESTUK', customer: 'TESTUK', country: 'UK trucks',
    pn: 'SYNTH-PN-A', name: 'Front brake-pad kit', category: 'Brake pads', unit: 'kit',
    tier: 'Genuine', offers: ['T-PAD-G', 'T-PAD-A'],
    baselineDefined: { period: 'January-June 2026, matched against January-June 2025',
      quantity: 1000, quantity_label: 'observed history', observed_billing_eur: 86100.0,
      observed_unit_price: 86.0, onward_quantity: 1200,
      note: 'Neither half-year is doubled and last year\'s volume is not assumed to recur.' },
    alternatives: [
      { alternative_id: 'T-NONE', name: 'No action', kind: 'no-price', price_delta_pct: 0,
        scope: 'all', eligibility: 'unchanged', volume_assumption: 0,
        volume_label: 'observed history', cost_basis_for_offer: 'SEP26', flags: [] },
      { alternative_id: 'T-TGT', name: 'Targeted 5%', kind: 'reduction', price_delta_pct: -5,
        scope: 'incremental', eligibility: 'units confirmed at risk', volume_assumption: 0,
        volume_label: 'stated commitment required', cost_basis_for_offer: 'OCT26', flags: [] },
      { alternative_id: 'T-MIG', name: 'Move to another product line', kind: 'migration',
        price_delta_pct: 0, scope: 'all', eligibility: 'unchanged', volume_assumption: 0,
        volume_label: 'observed history', cost_basis_for_offer: 'OCT26', flags: [] }
    ],
    packEvidence: { relationships: [
      { relationship_record_id: '9001', part_number_a: 'SYNTH-PN-E', part_number_b: 'SYNTH-PN-D',
        relationship_type: 'catalogue pairing (Genuine listed beside BVP alternative)',
        direction: 'genuine -> bvp', source_type: 'catalog_paired',
        source_document: 'BLOWER UNIT FILTER', application_vehicle: 'TF*,UC*',
        application_engine: '4J*', country_of_origin: 'THAILAND',
        technical_fitment_approved: '' },
      { relationship_record_id: '', part_number_a: 'SYNTH-PN-F', part_number_b: 'SYNTH-PN-G',
        relationship_type: 'supersession (old number replaced by new)', direction: 'old -> current',
        source_type: 'supersession map', source_document: 'pn_supersession_map.csv',
        application_vehicle: '', application_engine: '', country_of_origin: '',
        technical_fitment_approved: 'not applicable' }
    ] }
  };

  return {
    _note: 'RESTRICTED LOCAL TEST FIXTURE. Invented values in the shape of the authorised pack. '
      + 'Excluded from version control by the payload/*.json ignore rule. Not for sharing.',
    meta: {
      buildDate: '2026-09-22', version: 'Data contract fixture 1', audience: 'ISZE INTERNAL ONLY',
      billingCutoff: '2026-06-30', defaultForwardBasis: 'OCT26',
      costBases: bases,
      effectiveDateRule: 'the chosen offer effective date selects the cost basis; September and '
        + 'October are never blended'
    },
    sources: [
      { id: 'BILL', title: 'Billing extract', file: '01_all_sales_isze_to_distributor.csv',
        date: '3 January 2023 to 30 June 2026', kind: 'Recorded transactions',
        basis: 'positive quantities and positive net billed EUR on exact part numbers' }
    ],
    offers: {
      'T-PAD-G': { id: 'T-PAD-G', seller: 'Test seller', market: 'UK', part: 'SYNTH-PN-A',
        price: 120.0, currency: 'GBP', tax: 'not stated', vat: null, net: null,
        url: 'https://example.invalid/listing', retrieved: '2026-09-22',
        freshness: 'Index reports last week; the tax basis is not declared.',
        match: 'Exact Genuine part number', approvalReady: false,
        note: 'Axle kit: four pads, backing set and clip set. Listed in stock.',
        kind: 'Genuine',
        verification: 'public listing, not a firm quotation' },
      'T-PAD-A': { id: 'T-PAD-A', seller: 'Test seller', market: 'UK', part: 'SYNTH-PN-A',
        price: 110.0, currency: 'GBP', tax: 'inclusive', vat: 20, net: null,
        url: 'https://example.invalid/listing2', retrieved: '2025-11-01',
        match: 'Equivalent description only', note: 'Contents not stated.',
        kind: 'Alternative', approvalReady: false }
    },
    cases: [caseA],
    validation: [],
    inputManifest: [
      { file: '01_all_sales_isze_to_distributor.csv', sha256: 'a'.repeat(64), bytes: 50000000 },
      { file: '03_all_sales_to_dealer.csv', sha256: 'b'.repeat(64), bytes: 60000000 },
      { file: '02_spend_per_truck_by_market.csv', sha256: 'c'.repeat(64), bytes: 20000 },
      { file: 'declared_but_unconsumed.csv', sha256: 'd'.repeat(64), bytes: 100 }
    ],
    packAudit: {
      inputFile: 'ISZE_AIM_PRICING_DECISION_PACK_2026-09-22.json',
      inputSHA256: 'e'.repeat(64), inputZip: 'pack.zip', packDate: '2026-09-22',
      actualRows: 1000, declaredRows: 1234,
    counts: { case_scope_and_accounts: 5, price_observations: 113, sales_to_dealer: 3043,
      parts_registry: 27, part_relationships: 39, COST_MARGIN_AND_RULES_RESTRICTED: 16 },      issues: [], billingReference: '30 June 2026 - reference retained',
      offerScope: { rows: 51, exactCaseRows: 37 },
      acceptedStatus: 'Accepted in part for internal review; not price approval',
      excluded: 'Restricted model-cost records, the source invoice line and unapproved summaries.'
    },
    verifiedCosts: [
      costRecord('SYNTH-PN-A', 'SYNTHETIC BRAKE PAD KIT', 'kit', [50.0, 52.0, 50.0]),
      costRecord('SYNTH-PN-B', 'SYNTHETIC BRAKE PAD KIT', 'kit', [50.0, 52.0, 50.0]),
      costRecord('SYNTH-PN-C', 'SYNTHETIC BRAKE DISC', 'disc', [75.0, 78.0, 75.0])
    ],
    costReconciliation: [
      { part_number: 'SYNTH-PN-A', price_file_fob_eur: 49.99, historical_basis_eur: 50.0,
        difference: -0.01 },
      { part_number: 'SYNTH-PN-B', price_file_fob_eur: null, historical_basis_eur: 50.0,
        difference: null }
    ],
    turboPriceResolution: { part_number: 'SYNTH-PN-E', resolved_on: '2026-09-22',
      resolved_billable_list: null, still_open: [] },
    alternatives: { 'TEST-PADS': caseA.alternatives },
    candidateScreen: [
      candidate('TESTUK', 'SYNTH-PN-A', 'SYNTHETIC BRAKE PAD KIT', 2000, 200000.0, 100.0,
        120.0, 50.0, 'base price moved 20%; cost and list held', 'held', '', true),
      candidate('TESTUK', 'SYNTH-PN-A', 'SYNTHETIC BRAKE PAD KIT', 2000, 200000.0, 100.0,
        120.0, 50.0, 'base price moved 20%; cost and list held', 'held', '', true),
      candidate('TESTUK', 'SYNTH-PN-C', 'SYNTHETIC BRAKE DISC', 400, 60000.0, 150.0,
        190.0, 75.0, 'base price moved 5%; cost and list held', 'held', '', true),
      candidate('IMOTORS', 'SYNTH-PN-B', 'SYNTHETIC BRAKE PAD KIT', 2, 200.0, 100.0,
        120.0, 50.0, 'base price moved 20%; cost and list held', 'not held',
        'current net terms not established', false),
      candidate('IMOTORS', 'SYNTH-PN-D', 'SYNTHETIC BLOWER FILTER', 300, 4800.0, 16.0,
        16.0, null, 'no cost held', 'not held', 'no verified cost', false),
      candidate('IMOTORS', '', '', 12, 400.0, null, null, null,
        'part number absent on the source line', 'not held', 'part reference missing', false)
    ],
    screenRule: {
      what: 'every part number with recorded billing in the two pilot accounts, carrying its list '
        + 'price, its verified parts cost where one exists, the base-price movement, a selection '
        + 'reason and its unresolved inputs',
      coverage: 'verified parts cost is held for 3 part numbers, which are the scope parts.',
      competitorGap: 'competitor evidence is held only for SYNTH-PN-A and SYNTH-PN-C.',
      notA: 'not a target number of price cuts or increases, and not an approved commercial threshold'
    }
  };
}

function writeRestrictedFixture() {
  const dir = path.join(ROOT, 'payload');
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, 'data_contracts_restricted.local.json');
  const fixture = restrictedFixture();
  const text = JSON.stringify(fixture, null, 1) + '\n';
  fs.writeFileSync(file, text, 'utf8');
  /* A second copy under the pack's own name, so the restricted opt-in path for
     the source pack can actually be exercised. Both copies live in payload/,
     which .gitignore excludes. */
  fs.writeFileSync(path.join(dir, 'ISUZE_AIM_PRICING_DECISION_PACK_2026-09-22.json')
    .replace('ISUZE_', 'ISZE_'), text, 'utf8');
  return { file, fixture };
}

const { file: FIXTURE_FILE, fixture: FX } = writeRestrictedFixture();

/* The eligible candidate rows for the fixture: one row legitimately carries no
   part reference, so it belongs in the row count and not in any part count. */
const UNIDENTIFIED_ROW = { distributor: 'IMOTORS', part_number: '', description: '',
  billed_qty: 12, observed_billing_eur: 400.0, observed_unit_price: null, list_eur: null,
  verified_cost_eur_oct26: null, base_price_move_jpy: null, base_price_move_pct: null,
  selection_reasons: 'part number absent on the source line', competitor_evidence: 'not held',
  unresolved_inputs: 'part reference missing', decision_ready: false };

/* The authorised payload is read read-only, and only if it is present. */
let authorised = null;
if (fs.existsSync(AUTHORISED_PAYLOAD)) {
  try { authorised = JSON.parse(fs.readFileSync(AUTHORISED_PAYLOAD, 'utf8')); } catch (e) { authorised = null; }
}

/* ---------------------------------------------------------------- helpers -- */

function partNumbersOf(rows, field) {
  const seen = new Set();
  rows.forEach((r) => { if (r && r[field] != null && r[field] !== '') seen.add(r[field]); });
  return seen.size;
}

/* =========================================================== F04: date ==== */

test('F04 an invalid date is unresolved and is not defaulted to October', () => {
  const r = costbasis.resolveBasis(FX, 'not-a-date');
  assert.equal(r.resolved, false, 'an unusable date resolved to a basis');
  assert.equal(r.basis_id, null, 'an unusable date selected ' + r.basis_id);
  assert.notEqual(r.basis_id, FX.meta.defaultForwardBasis);
  assert.match(r.error, /not a usable calendar date/i);
  assert.equal(r.effective_date_state, 'not a usable calendar date');
});

test('F04 a date outside every documented window is unresolved', () => {
  for (const d of ['2035-01-01', '2026-03-31', '2020-06-15', '2027-04-01']) {
    const r = costbasis.resolveBasis(FX, d);
    assert.equal(r.resolved, false, d + ' resolved to ' + r.basis_id);
    assert.equal(r.basis_id, null);
    assert.match(r.error, /outside every documented/i);
  }
});

test('F04 a missing effective date is unresolved, not a default basis', () => {
  const r = costbasis.resolveBasis(FX, null);
  assert.equal(r.resolved, false);
  assert.equal(r.basis_id, null);
  assert.match(r.error, /effective date is required/i);
});

test('F04 2026-09-22 resolves SEP26 and 2026-10-01 resolves OCT26', () => {
  const sep = costbasis.resolveBasis(FX, '2026-09-22');
  const oct = costbasis.resolveBasis(FX, '2026-10-01');
  assert.equal(sep.resolved, true, sep.error || '');
  assert.equal(sep.basis_id, 'SEP26');
  assert.equal(oct.resolved, true, oct.error || '');
  assert.equal(oct.basis_id, 'OCT26');
  assert.notEqual(sep.basis_id, oct.basis_id);
});

test('F04 window boundaries resolve to exactly one basis each', () => {
  assert.equal(costbasis.resolveBasis(FX, '2026-04-01').basis_id, 'SEP26');
  assert.equal(costbasis.resolveBasis(FX, '2026-09-30').basis_id, 'SEP26');
  assert.equal(costbasis.resolveBasis(FX, '2026-10-01').basis_id, 'OCT26');
  assert.equal(costbasis.resolveBasis(FX, '2027-03-31').basis_id, 'OCT26');
});

test('F04 the October end date is reconstructed from its stated rate window, and reported', () => {
  const oct = costbasis.basisById(FX, 'OCT26');
  assert.equal(oct.offer_effective_to, undefined, 'the fixture no longer reproduces the open end');
  const w = costbasis.windowOf(oct);
  assert.equal(w.to, '2027-03-31', 'the stated rate window was not used to close the basis');
  assert.equal(w.to_source, 'reconstructed from rate_window');
  assert.match(w.statement, /reconstructed/i);
  assert.equal(costbasis.windowOf(costbasis.basisById(FX, 'SEP26')).to_source,
    'declared offer_effective_to');
});

test('F04 a basis with no usable window cannot accept a date, and says which one', () => {
  const broken = { meta: { costBases: [
    { basis_id: 'OPEN', status: 'forward', rate_window: 'sometime next year',
      offer_effective_from: '' }
  ] } };
  const r = costbasis.resolveBasis(broken, '2026-10-01');
  assert.equal(r.resolved, false);
  assert.match(r.error, /OPEN/);
});

test('F04 one authorised resolution applies one basis to the unchanged and proposed offer', () => {
  const a = costbasis.authoriseOfferBasis(FX, {
    part_number: 'SYNTH-PN-A', offer_effective_date: '2026-09-22'
  });
  assert.equal(a.resolved, true, a.statement);
  assert.equal(a.basis_id, 'SEP26');
  assert.equal(a.unchanged_offer.basis_id, a.basis_id);
  assert.equal(a.proposed_offer.basis_id, a.basis_id);
  assert.equal(a.cost_change_assumption.changed, false);
  assert.match(a.statement, /applied to the unchanged offer and to the proposed offer/i);
});

test('F04 a supplier-cost change is held as a separate, unjustified-until-justified assumption', () => {
  const a = costbasis.authoriseOfferBasis(FX, {
    part_number: 'SYNTH-PN-A', offer_effective_date: '2026-09-22',
    cost_change_basis_id: 'OCT26'
  });
  assert.equal(a.cost_change_assumption.changed, true);
  assert.equal(a.cost_change_assumption.requires_justification, true);
  assert.equal(a.cost_change_assumption.justified, false);
  assert.equal(a.ok, false, 'an unjustified cost change was accepted');
  assert.equal(a.unchanged_offer.basis_id, 'SEP26');
  const justified = costbasis.authoriseOfferBasis(FX, {
    part_number: 'SYNTH-PN-A', offer_effective_date: '2026-09-22',
    cost_change_basis_id: 'OCT26',
    cost_change_justification: 'supplier notified a rate revision effective 1 October'
  });
  assert.equal(justified.cost_change_assumption.justified, true);
});

test('F04 comparable rows on one screen expose which single basis they all hold', () => {
  const c = costbasis.comparableBases(FX, ['SYNTH-PN-A', 'SYNTH-PN-C']);
  assert.deepEqual(c.bases_held_by_every_row,
    ['HIST', 'SEP26', 'OCT26'], 'a common basis was not found');
  const missing = costbasis.comparableBases(FX, ['SYNTH-PN-A', 'SYNTH-PN-D']);
  assert.deepEqual(missing.parts_without_any_cost_record, ['SYNTH-PN-D']);
  assert.match(missing.statement, /a missing cost is not a cost of zero/i);
});

test('F04 a forward cost is refused on a recorded historical quantity labelled historical', () => {
  const refused = costbasis.guardBasisUse({
    payload: FX, cost_basis_id: 'OCT26', quantity_label: 'observed history',
    evidence_period: 'January-June 2026' });
  assert.equal(refused.permitted, false, 'a forward cost was allowed to stand as a historical actual');
  assert.equal(refused.refuses, true);
  assert.match(refused.statement, /Refused/i);

  const historical = costbasis.guardBasisUse({
    payload: FX, cost_basis_id: 'HIST', quantity_label: 'observed history' });
  assert.equal(historical.permitted, true);
  assert.equal(historical.label, 'historical actual');

  const forward = costbasis.guardBasisUse({
    payload: FX, cost_basis_id: 'OCT26', quantity_label: 'observed history',
    explicit_forward_scenario: true });
  assert.equal(forward.permitted, true);
  assert.match(forward.statement, /forward scenario/i);
});

test('F04 recorded billing stays intact and separate from a rounded forward price', () => {
  const c = FX.cases[0];
  const b = engine.baseline(c);
  assert.equal(b.recorded_billing_eur, c.baselineDefined.observed_billing_eur,
    'the recorded billing was replaced by a reconstructed figure');
  assert.notEqual(b.revenue, b.recorded_billing_eur, 'the fixture no longer reproduces the rounding');
  assert.equal(b.is_rounded_scenario, true);
  assert.equal(b.reconciles_to_recorded, false);
  assert.match(b.basis_statement, /labelled a rounded scenario and not recorded history/i);
});

test('F04 a basis, period, stage or unit that disagrees blocks the comparison', () => {
  const same = costbasis.basisCompatibility(
    { cost_basis_id: 'SEP26', evidence_period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit',
      offer_effective_date: '2026-09-22' },
    { cost_basis_id: 'SEP26', evidence_period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit',
      offer_effective_date: '2026-09-22' });
  assert.equal(same.comparable, true);
  const mixed = costbasis.basisCompatibility(
    { cost_basis_id: 'SEP26', evidence_period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit' },
    { cost_basis_id: 'OCT26', evidence_period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit' });
  assert.equal(mixed.comparable, false);
  assert.match(mixed.statement, /Different cost bases/);
});

/* ==================================================== DATA-01: manifest === */

test('DATA-01 every analytical input carries file, pointer, period, basis, status and restriction', () => {
  const m = manifest.build(FX);
  const required = ['reference_id', 'file', 'period', 'period_state', 'basis', 'status',
    'restricted', 'payload_pointer', 'input_pointer'];
  assert.ok(m.records.length >= 11, 'only ' + m.records.length + ' inputs are described');
  m.records.forEach((r) => {
    required.forEach((f) => {
      assert.ok(Object.prototype.hasOwnProperty.call(r, f),
        r.reference_id + ' is missing the field "' + f + '"');
    });
    assert.ok(r.period !== undefined, r.reference_id + ' has no period field at all');
    if (r.period === null) {
      assert.equal(r.period_state, 'undeclared',
        r.reference_id + ' carries no period and does not say so');
    }
  });
  const undeclared = m.records.filter((r) => r.period_state === 'undeclared');
  assert.ok(undeclared.length >= 1, 'the candidate screen no longer declares an undeclared period');
});

test('DATA-01 inputManifest and packAudit are reconciled into one manifest, differences reported', () => {
  const m = manifest.build(FX);
  const rec = m.reconciliation;
  assert.equal(rec.inputs_declared, FX.inputManifest.length);
  assert.equal(rec.reconciled, 4, 'declared inputs were not matched to analytical records');
  assert.equal(rec.declared_only, 1, 'the unconsumed declared file was not reported');
  assert.equal(rec.manifest_only, 7, 'manifest-only inputs were not counted');
  assert.equal(rec.reconciled + rec.manifest_only + rec.declared_only, m.records.length,
    'the manifest merge does not account for every record');
  assert.equal(rec.pack_rows_declared, 1234);
  assert.equal(rec.pack_rows_actual, 1000);
  assert.equal(rec.pack_row_variance, -234);
  const pack = manifest.find(m, 'MAN-07');
  assert.equal(pack.count_state, 'disagrees - reported, not reconciled away');
  assert.ok(pack.reconciliation.join(' ').length > 0);
});

test('DATA-01 a manifest record for a restricted input carries no value', () => {
  const m = manifest.build(FX);
  const restricted = manifest.restrictedRecords(m);
  assert.ok(restricted.length >= 3, 'restricted inputs are not marked');
  const check = manifest.assertShippable(m);
  assert.equal(check.ok, true, check.findings.join('; '));
  assert.match(check.statement, /without carrying their values/i);
});

test('DATA-01 the manifest conserves every record it merged', () => {
  const m = manifest.build(FX);
  const c = manifest.conservation(m);
  assert.equal(c.totals.records, m.records.length);
  assert.equal(c.totals.accounted_for, m.records.length, 'the merge lost or duplicated a record');
  assert.equal(c.ok, false, 'the declared-versus-actual row difference was not raised');
  assert.ok(c.findings.some((f) => /declares 1234 rows/.test(f)));
});

test('DATA-01 a restricted input is not fingerprinted unless the caller opts in', () => {
  const m = manifest.build(FX);
  const out = manifest.fingerprintFiles(m, path.join(ROOT, 'payload'));
  /* The pack itself is restricted, so by default its hash is left as the declared
     checksum. The opt-in extends the read to it. */
  const inLoop = manifest.build(FX);
  manifest.fingerprintFiles(inLoop, path.join(ROOT, 'payload'));
  const declaredOnly = manifest.find(inLoop, 'MAN-07');
  assert.equal(declaredOnly.hash_status, 'declared checksum',
    'the restricted pack hash was replaced without being asked for');
  assert.match(declaredOnly.reconciliation.join(' '), /restricted/i);
  assert.ok(out.attempted < m.records.length,
    'every record including the restricted ones was read');
  assert.ok(out.attempted > 0);
  assert.equal(inLoop.records.filter((r) => r.restricted
    && r.hash_status === 'fingerprinted on this machine').length, 0);
  const optedIn = manifest.build(FX);
  const optOut = manifest.fingerprintFiles(optedIn, path.join(ROOT, 'payload'),
    { include_restricted: true, restricted_base_path: path.join(ROOT, 'payload') });
  assert.equal(manifest.find(optedIn, 'MAN-07').hash_status,
    'fingerprinted on this machine under an explicit restricted opt-in');
  assert.ok(optOut.attempted > out.attempted,
    'the explicit opt-in did not extend the fingerprint to the restricted input');
});

test('DATA-01 a fingerprint that cannot be taken is reported, never fabricated', () => {
  const m = manifest.build(FX);
  const out = manifest.fingerprintFiles(m, path.join(ROOT, 'payload'));
  const missing = out.unresolved.length;
  assert.equal(out.fingerprinted + missing, out.attempted);
  if (missing) {
    const rec = manifest.find(m, out.unresolved[0].reference_id);
    assert.equal(rec.hash_status, 'unresolved');
    assert.match(out.unresolved[0].reason, /unresolved rather than guessed/i);
  }
});

/* ==================================================== DATA-02: entities === */

test('DATA-02 ITUK is not IUK and UMI is not UTI', () => {
  assert.equal(manifest.isSeparatePair('ITUK', 'IUK'), true);
  assert.equal(manifest.isSeparatePair('UMI', 'UTI'), true);
  const bad = manifest.assertNoBlend('ITUK', 'IUK');
  assert.equal(bad.ok, false);
  assert.match(bad.statement, /never combined/i);
  const fine = manifest.assertNoBlend('ITUK', 'IMOTORS');
  assert.equal(fine.ok, true);
});

test('DATA-02 distributor, purchasing account and site are three separate fields', () => {
  const e = manifest.normaliseEntity({ distributor: 'ITUK', purchasing_account: '2575',
    site: 'Avonmouth' });
  assert.equal(e.distributor, 'ITUK');
  assert.equal(e.purchasing_account, '2575');
  assert.equal(e.site, 'Avonmouth');
  const partial = manifest.normaliseEntity({ distributor: 'ITUK' });
  assert.equal(partial.purchasing_account, null);
  assert.equal(partial.site, null);
  assert.match(manifest.entityLabel(partial), /account not stated/);
  assert.notEqual(manifest.entityKey(e), manifest.entityKey(partial),
    'an unstated account was folded into a stated one');
});

test('DATA-02 a campaign key cannot merge two entities or two sales stages', () => {
  const k1 = manifest.campaignKey({ distributor: 'ITUK', purchasing_account: '2575',
    part_number: 'SYNTH-PN-A', unit: 'kit', sales_stage: 'sell-in' });
  const k2 = manifest.campaignKey({ distributor: 'IUK', purchasing_account: '2575',
    part_number: 'SYNTH-PN-A', unit: 'kit', sales_stage: 'sell-in' });
  const k3 = manifest.campaignKey({ distributor: 'ITUK', purchasing_account: '2575',
    part_number: 'SYNTH-PN-A', unit: 'kit', sales_stage: 'sell-out' });
  assert.notEqual(k1, k2);
  assert.notEqual(k1, k3);
});

test('DATA-02 two separate entities present in one set are called out', () => {
  const rows = [{ distributor: 'ITUK' }, { distributor: 'IUK' }, { distributor: 'IMOTORS' }];
  const d = candidates.distinctEntities(rows);
  assert.equal(d.separate_entity_pairs_present.length, 1);
  assert.equal(d.account_field_present, false);
  assert.match(d.statement, /never combined/);
});

test('DATA-02 a country name where a distributor is expected is reported, not rewritten', () => {
  const naming = manifest.distributorNaming({
    cases: [{ market: 'PORTUGAL', customer: 'I Motors' }],
    alternatives: { 'IMOTORS-OIL': {} },
    candidateScreen: [{ distributor: 'PORTUGAL' }]
  });
  const labels = naming.names_as_they_appear.map((n) => n.label);
  assert.ok(labels.indexOf('PORTUGAL') >= 0);
  assert.ok(labels.indexOf('I Motors') >= 0);
  assert.ok(labels.indexOf('IMOTORS') >= 0);
  assert.deepEqual(naming.country_name_used_where_a_distributor_is_expected, ['PORTUGAL']);
  assert.match(naming.statement, /reported, not silently rewritten/i);
  const portugal = naming.names_as_they_appear.find((n) => n.label === 'PORTUGAL');
  assert.ok(portugal.fields.indexOf('distributor') >= 0);
  assert.ok(portugal.fields.indexOf('market') >= 0);
});

/* ==================================================== DATA-03: identity === */

test('DATA-03 relationship type and validation status are represented separately', () => {
  const rows = evidence.relationships(FX);
  assert.ok(rows.length >= 2, 'no relationship rows were read');
  rows.forEach((r) => {
    assert.ok(Object.prototype.hasOwnProperty.call(r, 'relationship_type'));
    assert.ok(Object.prototype.hasOwnProperty.call(r, 'validation_status'));
    assert.equal(r.original_reference_preserved, true);
  });
  const pairing = rows.find((r) => r.relationship_type === 'catalogue_pairing');
  const supersession = rows.find((r) => r.relationship_type === 'supersession');
  assert.ok(pairing, 'the catalogue pairing was not classified');
  assert.ok(supersession, 'the supersession was not classified');
  assert.equal(pairing.validation_status, 'unresolved',
    'an absent fitment field was turned into an approval');
  assert.equal(pairing.fitment_approved, null);
  assert.equal(supersession.validation_status, 'not applicable');
});

test('DATA-03 a relationship is not an approval to fit', () => {
  const kinds = evidence.RELATIONSHIP_KINDS;
  ['catalogue_pairing', 'supersession', 'replacement', 'declared_newest_number'].forEach((k) => {
    assert.equal(kinds[k].implies_fitment_approval, false, k + ' claims to imply fitment');
  });
  const summary = evidence.relationshipSummary(FX);
  assert.equal(summary.fitment_approved_count, 0);
  assert.match(summary.statement, /not an approval to fit/i);
  assert.ok(summary.by_relationship_type.catalogue_pairing >= 1);
  assert.ok(summary.by_relationship_type.supersession >= 1);
});

test('DATA-03 an unclassified relationship stays unclassified', () => {
  const cls = evidence.classifyRelationship({ relationship_type: 'seller says these go together' });
  assert.equal(cls.kind, 'unknown');
  assert.equal(cls.classified, false);
  assert.equal(evidence.relationshipKind('unknown').implies_fitment_approval, false);
});

/* ==================================================== DATA-04: compare === */

test('DATA-04 a different sales stage or unit refuses the comparison', () => {
  const base = { period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit',
    entity: { distributor: 'ITUK' } };
  const same = evidence.comparability(base, Object.assign({}, base));
  assert.equal(same.comparable, true);
  const stage = evidence.comparability(base, Object.assign({}, base, { sales_stage: 'sell-out' }));
  assert.equal(stage.comparable, false);
  assert.match(stage.statement, /Different sales stages/);
  const unit = evidence.comparability(base, Object.assign({}, base, { unit: 'unit' }));
  assert.equal(unit.comparable, false);
  assert.match(unit.statement, /A kit is not a single unit/);
});

test('DATA-04 an undeclared period refuses the comparison instead of assuming one', () => {
  const a = { sales_stage: 'sell-in', unit: 'kit' };
  const b = { period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit' };
  const r = evidence.comparability(a, b);
  assert.equal(r.comparable, false);
  assert.match(r.statement, /A period is not declared/);
});

test('DATA-04 a list price, a billing average and a competitor price are three things', () => {
  const list = { price_level: 'list', period: 'H1 2026', sales_stage: 'sell-in', unit: 'kit' };
  const billing = { price_level: 'observed_billing_average', period: 'H1 2026',
    sales_stage: 'sell-in', unit: 'kit' };
  const competitor = { price_level: 'competitor_advertised', period: 'H1 2026',
    sales_stage: 'sell-in', unit: 'kit' };
  assert.equal(evidence.assertSamePriceLevel(list, billing).comparable, false);
  assert.equal(evidence.assertSamePriceLevel(list, competitor).comparable, false);
  assert.match(evidence.assertSamePriceLevel(list, billing).statement,
    /never added together|different commercial price levels/i);
  assert.equal(evidence.assertSamePriceLevel(list, Object.assign({}, list)).comparable, true);
  const undeclared = evidence.assertSamePriceLevel(list, { period: 'x' });
  assert.equal(undeclared.comparable, false);
  assert.match(undeclared.statement, /does not declare its price level/);
});

/* ================================================ DATA-05/06: repeated ==== */

test('DATA-05 a duplicate import does not double a quantity', () => {
  const log = evidence.makeImportLog({});
  const rows = [
    { part_number: 'P1', distributor: 'TESTUK', period: 'H1 2026', quantity: 100 },
    { part_number: 'P2', distributor: 'TESTUK', period: 'H1 2026', quantity: 50 }
  ];
  const first = log.upsert('billing-2026-06', rows);
  assert.equal(first.inserted, 2);
  assert.equal(log.sum((r) => r.quantity).total, 150);

  const second = log.upsert('billing-2026-06', rows);
  assert.equal(second.inserted, 0, 'the same import was inserted twice');
  assert.equal(second.unchanged, 2);
  assert.equal(log.sum((r) => r.quantity).total, 150, 'the quantity doubled on re-import');

  /* The same key twice inside one file is a duplicate line, not extra volume. */
  const third = log.upsert('billing-2026-07', [
    { part_number: 'P3', distributor: 'TESTUK', period: 'H1 2026', quantity: 10 },
    { part_number: 'P3', distributor: 'TESTUK', period: 'H1 2026', quantity: 10 }
  ]);
  assert.equal(third.duplicates_folded, 1);
  assert.equal(log.sum((r) => r.quantity).total, 160);
});

test('DATA-05 a correction replaces its declared predecessor and does not add to it', () => {
  const log = evidence.makeImportLog({});
  log.upsert('billing-2026-06', [
    { part_number: 'P1', distributor: 'TESTUK', period: 'H1 2026', quantity: 100 }
  ]);
  const before = log.sum((r) => r.quantity).total;
  const key = ['P1', 'TESTUK', 'H1 2026'].join(SEP);
  const corrected = log.correct('billing-correction', 
    { part_number: 'P1', distributor: 'TESTUK', period: 'H1 2026', quantity: 60 },
    { key, corrects_revision: 1, reason: 'credit line was excluded in error',
      correction_id: 'COR-1' });
  assert.equal(corrected.ok, true, corrected.error || '');
  assert.equal(corrected.correction.corrects_key, key);
  assert.equal(corrected.correction.justified, true);
  const after = log.sum((r) => r.quantity).total;
  assert.equal(before, 100);
  assert.equal(after, 60, 'the correction added to the activity instead of replacing it');
  const cons = log.conservation();
  assert.equal(cons.records_held, 1, 'the correction multiplied the records');
  assert.equal(cons.corrections, 1);
});

test('DATA-05 a correction that names a record which does not exist is refused', () => {
  const log = evidence.makeImportLog({});
  const r = log.correct('x', { part_number: 'NOPE', quantity: 1 }, { key: 'NOPE' + SEP + SEP });
  assert.equal(r.ok, false);
  assert.match(r.error, /must name a record that exists/i);
});

test('DATA-06 a repeated import is traceable to the section that produced each record', () => {
  const log = evidence.makeImportLog({});
  log.upsert('section-A', [{ part_number: 'P1', distributor: 'TESTUK', period: 'H1 2026',
    quantity: 10 }]);
  log.upsert('section-B', [{ part_number: 'P2', distributor: 'TESTUK', period: 'H1 2026',
    quantity: 20 }]);
  const key = ['P1', 'TESTUK', 'H1 2026'].join(SEP);
  assert.equal(log.provenanceOf(key), 'section-A');
  log.correct('section-C', { part_number: 'P1', distributor: 'TESTUK', period: 'H1 2026',
    quantity: 8 }, { key, reason: 'returned units removed' });
  assert.equal(log.provenanceOf(key), 'section-C');
  const t = log.traceability();
  assert.equal(t.with_provenance, t.keys, 'a held record has no provenance');
  assert.equal(t.corrections.length, 1);
  assert.equal(t.corrections[0].corrects_key, key);
  assert.equal(t.corrections[0].justified, true);
});

test('DATA-06 a correction without a stated reason is visible as unjustified', () => {
  const log = evidence.makeImportLog({});
  log.upsert('s', [{ part_number: 'P1', distributor: 'T', period: 'H1 2026', quantity: 10 }]);
  const key = ['P1', 'T', 'H1 2026'].join(SEP);
  const r = log.correct('s2', { part_number: 'P1', distributor: 'T', period: 'H1 2026',
    quantity: 9 }, { key });
  assert.equal(r.ok, true);
  assert.equal(r.correction.justified, false);
});

test('DATA-06 the candidate dataset conserves every received row across revisions', () => {
  const ds = candidates.makeDataset('candidate set');
  const first = ds.upsert('screen-2026-09', JSON.parse(JSON.stringify(FX.candidateScreen)),
    { origin: 'accepted pack 2026-09-22', at: '2026-09-22T00:00:00Z', restricted: true });
  assert.equal(first.counts.added, 6, 'unexpected add count: ' + JSON.stringify(first.counts));
  const again = ds.upsert('screen-2026-09', JSON.parse(JSON.stringify(FX.candidateScreen)),
    { origin: 'accepted pack 2026-09-22', at: '2026-09-22T00:00:00Z', restricted: true });
  assert.equal(again.counts.added, 0, 'a repeated import added rows');
  assert.equal(again.counts.unchanged, 6);
  const cons = ds.conservation();
  assert.equal(cons.ok, true, cons.statement);
  assert.equal(cons.rows_held, 6);
  assert.equal(cons.rows_received, cons.rows_added + cons.rows_replaced + cons.rows_unchanged
    + cons.rows_set_aside);
});

test('DATA-06 a correction on a candidate row replaces its declared predecessor', () => {
  const ds = candidates.makeDataset('candidate set');
  ds.upsert('screen-2026-09', [{ distributor: 'TESTUK', part_number: 'SYNTH-PN-A',
    billed_qty: 2000, observed_billing_eur: 200000.0 }], { restricted: true });
  /* Key is scoped to the source section (C18); take it from the held row. */
  const key = ds.all()[0].key;
  const r = ds.correct('correction-2026-10', key,
    { distributor: 'TESTUK', part_number: 'SYNTH-PN-A', billed_qty: 2500,
      observed_billing_eur: 215000 },
    { corrects_revision: 1, reason: 'credit notes were missing from the first import' });
  assert.equal(r.ok, true, r.error || '');
  assert.equal(r.corrects_revision, 1);
  assert.equal(ds.all().length, 1, 'the correction multiplied the set');
  const wrong = ds.correct('correction-2', key, { distributor: 'TESTUK',
    part_number: 'SYNTH-PN-A', billed_qty: 1 },
    { corrects_revision: 1, reason: 'x' });
  assert.equal(wrong.ok, false);
  assert.equal(wrong.conflict, true);
  assert.match(wrong.error, /Refused rather than replacing the wrong record/i);
});

/* ====================================== conservation of received rows ===== */
/* The check that decides whether the row accounting balances, and the two
   buckets a row can leave by. A row is received once and classified once. A row
   that is set aside is classified once, in the set-aside bucket, and is not
   added back into the received total. A row that leaves without a reason is a
   loss and must fail the check. */

const SYNTHETIC = [
  { distributor: 'SYNTH-A', part_number: 'SYNTH-P1', billed_qty: 100 },
  { distributor: 'SYNTH-A', part_number: 'SYNTH-P2', billed_qty: 50 },
  { distributor: 'SYNTH-B', part_number: 'SYNTH-P1', billed_qty: 20 }
];

function setAsideDataset() {
  const ds = candidates.makeDataset('synthetic');
  ds.upsert('alpha', JSON.parse(JSON.stringify(SYNTHETIC)), {});
  const keyOf = (distributor, partNumber) => {
    const row = ds.all().find((r) => r.record.distributor === distributor
      && r.record.part_number === partNumber);
    assert.ok(row, 'no held row for ' + distributor + '/' + partNumber);
    return row.key;
  };
  return { ds, keyOf };
}

test('DATA-06 a set-aside row is counted once, in the set-aside bucket', () => {
  const { ds, keyOf } = setAsideDataset();
  const result = ds.setAside(keyOf('SYNTH-A', 'SYNTH-P2'), 'withdrawn by the distributor');
  assert.equal(result.ok, true, result.error || '');

  const c = ds.conservation();
  /* The row was received once and added once. Setting it aside is a later move
     of that same row, not a second receipt of it. */
  assert.equal(c.rows_received, 3, 'the set-aside row was counted as received twice');
  assert.equal(c.rows_added, 3);
  assert.equal(c.rows_replaced, 0);
  assert.equal(c.rows_unchanged, 0);
  assert.equal(c.rows_set_aside, 1);
  assert.equal(c.rows_received_classified, c.rows_received,
    'the classified rows no longer add up to the rows received');
  assert.notEqual(c.rows_received_classified + c.rows_set_aside, c.rows_received,
    'the set-aside row is being added to the receipt total a second time');
  /* Held rows are the rows taken in less the rows moved out with a reason. */
  assert.equal(c.rows_held, c.rows_added + c.rows_replaced - c.rows_set_aside);
  assert.equal(c.rows_held, 2);
  assert.equal(c.difference, 0);
  assert.equal(c.ok, true, c.statement);
  /* The reason, the quantity and the value travel with the row. */
  assert.equal(c.rows_set_aside_detail.length, 1);
  assert.match(c.rows_set_aside_detail[0].reason, /withdrawn/);
  assert.equal(c.rows_set_aside_detail[0].quantity, 50);
  assert.match(c.statement, /set aside with a reason/);
});

test('DATA-06 conservation fails when a row leaves the store with no reason given', () => {
  /* The same shape as the set-aside case, except one row is missing from the
     store and no set-aside record explains it. A check that cannot fail here is
     useless: this is the state a lost row produces. */
  const lost = evidence.conservationOfLedger({
    revisions: 1, corrections: 0,
    received: 3, added: 3, replaced: 0, unchanged: 0, folded: 0,
    held: 2, set_aside: [],
    keys_held: 3, keys_set_aside: 0, keys_taken: 3
  });
  assert.equal(lost.ok, false, 'a lost row was reported as balance');
  assert.equal(lost.held_difference, -1, 'the missing row was not located');
  assert.ok(lost.findings.some((f) => f.code === 'STORE_DISAGREES_WITH_INDEX'),
    'the loss was not named: ' + JSON.stringify(lost.findings));
  assert.match(lost.statement, /gone missing/i);
  assert.match(lost.statement, /never absorbed into a total/i);
  /* The bucket identity alone would have passed here, which is exactly why the
     store is cross-checked against the key index. */
  assert.equal(lost.rows_received_classified, lost.rows_received);
});

test('DATA-06 conservation fails when a received row is written into no bucket', () => {
  const unclassified = evidence.conservationOfLedger({
    revisions: 1, corrections: 0,
    received: 4, added: 3, replaced: 0, unchanged: 0, folded: 0,
    held: 3, set_aside: [],
    keys_held: 3, keys_set_aside: 0, keys_taken: 4
  });
  assert.equal(unclassified.ok, false, 'an unclassified received row was reported as balance');
  assert.equal(unclassified.difference, 1, 'the unclassified row was not counted');
  assert.ok(unclassified.findings.some((f) => f.code === 'UNCLASSIFIED_ROWS'));
  assert.match(unclassified.statement, /counted nowhere/i);
});

test('DATA-06 conservation fails when a row is counted twice', () => {
  /* The direction the reported defect ran in: a bucket carrying a row that the
     receipt total does not. The check must catch the inflation, not hide it. */
  const doubled = evidence.conservationOfLedger({
    revisions: 1, corrections: 0,
    received: 3, added: 4, replaced: 0, unchanged: 0, folded: 0,
    held: 4, set_aside: [],
    keys_held: 4, keys_set_aside: 0, keys_taken: 4
  });
  assert.equal(doubled.ok, false, 'a double-counted row was reported as balance');
  assert.equal(doubled.difference, -1);
  assert.ok(doubled.findings.some((f) => f.code === 'UNCLASSIFIED_ROWS'));
  assert.match(doubled.statement, /counted twice/i);
});

test('DATA-06 a set-aside row that is imported again is still counted once per receipt', () => {
  const { ds, keyOf } = setAsideDataset();
  ds.setAside(keyOf('SYNTH-A', 'SYNTH-P2'), 'withdrawn by the distributor');
  /* The section comes back with the row on it, so the row is taken in a second
     time. That second receipt is a receipt; the first one still stands. */
  ds.upsert('alpha', JSON.parse(JSON.stringify(SYNTHETIC)), {});

  const c = ds.conservation();
  assert.equal(c.rows_received, 6, 'the re-imported row was not counted as received again');
  assert.equal(c.rows_added, 4, 'the three original rows plus the one re-imported row');
  assert.equal(c.rows_unchanged, 2);
  assert.equal(c.rows_set_aside, 1, 'the distinct set-aside keys');
  assert.equal(c.rows_set_aside_reimported, 1);
  assert.equal(c.rows_held, 3);
  assert.equal(c.keys_taken, 3);
  assert.equal(c.keys_registered, 3, 'a key set aside and re-imported was counted twice');
  assert.equal(c.difference, 0);
  assert.equal(c.ok, true, c.statement);
});

test('DATA-06 the import log can set a row aside, and the accounting still balances', () => {
  const log = evidence.makeImportLog({});
  log.upsert('s1', [{ part_number: 'P1', distributor: 'T', period: 'H1', quantity: 10 }]);
  const key = ['P1', 'T', 'H1'].join(SEP);

  const taken = log.conservation();
  assert.equal(taken.ok, true, taken.statement);
  assert.equal(taken.records_held, 1);

  const aside = log.setAside(key, 'the distributor withdrew the line from the return');
  assert.equal(aside.ok, true, aside.error || '');
  assert.equal(log.all().length, 0, 'the set-aside row is still in the held set');

  const after = log.conservation();
  assert.equal(after.rows_received, 1);
  assert.equal(after.rows_set_aside, 1);
  assert.equal(after.records_held, 0);
  assert.equal(after.ok, true, after.statement);
  assert.equal(after.set_aside[0].reason.indexOf('withdrew') >= 0, true,
    'the set-aside reason was not carried');

  /* A later import of the same key is a new receipt and does not double the
     original one. */
  log.upsert('s2', [{ part_number: 'P1', distributor: 'T', period: 'H1', quantity: 10 }]);
  const back = log.conservation();
  assert.equal(back.rows_received, 2);
  assert.equal(back.records_held, 1);
  assert.equal(back.ok, true, back.statement);
});

test('DATA-06 the import log refuses to set aside a row it never took in', () => {
  const log = evidence.makeImportLog({});
  const r = log.setAside('NOT-A-KEY', 'x');
  assert.equal(r.ok, false);
  assert.match(r.error, /never taken in cannot be set aside/i);
});

test('DATA-06 fixing the set-aside count does not weaken the correction path', () => {
  /* A correction replaces its declared predecessor. Adding a set-aside row must
     not disturb that, and the received total must still hold both events. */
  const { ds, keyOf } = setAsideDataset();
  const corrected = ds.correct('correction-2026-10', keyOf('SYNTH-A', 'SYNTH-P1'),
    Object.assign({}, SYNTHETIC[0], { billed_qty: 90 }),
    { corrects_revision: 1, reason: 'the first import double-counted one delivery' });
  assert.equal(corrected.ok, true, corrected.error || '');
  const aside = ds.setAside(keyOf('SYNTH-A', 'SYNTH-P2'), 'withdrawn by the distributor');
  assert.equal(aside.ok, true, aside.error || '');

  const c = ds.conservation();
  assert.equal(c.rows_received, 4, 'three rows received plus the one correction revision');
  assert.equal(c.rows_added, 3);
  assert.equal(c.rows_replaced, 1, 'the correction was not counted as a replacement');
  assert.equal(c.rows_set_aside, 1);
  assert.equal(c.rows_received_classified, c.rows_received);
  assert.equal(c.rows_held, 2);
  /* A correction replaces a predecessor that was already one of the received
     rows, so it adds a revision and no row. The held set is therefore the
     distinct rows taken in less the distinct rows set aside. */
  assert.equal(c.rows_held, c.keys_taken - c.keys_set_aside,
    'held rows are not the distinct rows taken in less the rows set aside');
  assert.equal(c.rows_added + c.rows_replaced - c.rows_set_aside, 3,
    'with a correction present, added plus replaced overstates the rows taken in');
  assert.equal(c.difference, 0);
  assert.equal(c.ok, true, c.statement);
  /* The corrected row is still one row, still carrying its predecessor. */
  assert.equal(ds.all().length, 2);
  assert.equal(ds.trace(keyOf('SYNTH-A', 'SYNTH-P1')).corrected_from_revision, 1);
});

test('DATA-06 conservation with no set-aside row still balances, as before', () => {
  /* The ordinary path must not have been changed by the fix. */
  const { ds } = setAsideDataset();
  const first = ds.conservation();
  assert.equal(first.ok, true, first.statement);
  assert.equal(first.rows_received, 3);
  assert.equal(first.rows_set_aside, 0);
  assert.equal(first.difference, 0);
  assert.equal(first.rows_received_classified, first.rows_received);

  ds.upsert('alpha', JSON.parse(JSON.stringify(SYNTHETIC)), {});
  const repeat = ds.conservation();
  assert.equal(repeat.ok, true, repeat.statement);
  assert.equal(repeat.rows_received, 6);
  assert.equal(repeat.rows_added, 3);
  assert.equal(repeat.rows_unchanged, 3);
});

/* ==================================================== DATA-07: remainder == */

test('DATA-07 the unclassified remainder stays visible and its size is reported', () => {
  const rows = FX.candidateScreen;
  const rec = evidence.reconcile(rows.map((r) => ({
    quantity: r.billed_qty,
    price: r.observed_unit_price,
    revenue_eur: r.observed_billing_eur,
    entity: { distributor: r.distributor },
    part_number: r.part_number
  })));
  assert.equal(rec.rows_in, rows.length);
  assert.equal(rec.rows_priced + rec.rows_unpriced, rec.rows_in, 'a row went missing');
  assert.ok(rec.unclassified_remainder.visible === true);
  assert.equal(rec.unclassified_remainder.rows, rec.rows_unpriced);
  assert.ok(rec.unclassified_remainder.rows >= 1, 'the fixture no longer has an unpriced row');
  assert.match(rec.unclassified_remainder.statement, /not a row with a price of zero/i);
  assert.ok(rec.unclassified_remainder.by_entity.length >= 1,
    'the remainder is not broken down by distributor and account');
  assert.equal(rec.classified, true, 'the rows do not add up');
  assert.match(rec.statement, /reported, not dropped/);
});

test('DATA-07 an unpriced quantity is never added to a priced quantity', () => {
  const priced = [{ quantity: 100 }, { quantity: 50 }];
  const counted = [{ quantity: 100 }, { quantity: 50 }, { quantity: 12 }];
  const c = evidence.conservationOfTotals(priced, counted);
  assert.equal(c.ok, false);
  assert.equal(c.difference, 12);
  assert.equal(c.priced_quantity, 150);
  assert.match(c.statement, /must not be added to the priced quantity/);
});

/* ==================================================== DATA-08: staging === */

test('DATA-08 a failed refresh leaves the last accepted view in place', () => {
  const stage = evidence.makeStageState('candidate screen');
  assert.equal(stage.view().showing_revision, null);
  stage.begin({ rows: 12345, basis: 'undeclared' });
  const committed = stage.commit();
  assert.equal(committed.ok, true);
  assert.equal(committed.revision, 1);
  assert.equal(stage.view().view.rows, 12345);

  stage.begin({ rows: 0, basis: 'undeclared' });
  const failed = stage.fail('the import returned no rows');
  assert.equal(failed.ok, false);
  assert.equal(failed.showing.revision, 1, 'the failed refresh replaced the accepted view');
  assert.equal(failed.showing.view.rows, 12345);
  const v = stage.view();
  assert.equal(v.view.rows, 12345, 'a partially refreshed state is on screen');
  assert.equal(v.partially_refreshed, false);
  assert.match(v.refresh_state, /last accepted view/i);
  assert.equal(stage.state.last_failure.partial_result, null,
    'the partial result was handed back and could be shown');
});

test('DATA-08 a stage that never succeeded shows nothing rather than a partial view', () => {
  const stage = evidence.makeStageState('first run');
  stage.begin({ rows: 3 });
  stage.fail('source unreadable');
  const v = stage.view();
  assert.equal(v.view, null);
  assert.match(v.statement, /first refresh failed/i);
});

/* ========================================================= F10: screen === */
test('F10 the candidate reporting basis is declared as undeclared, not guessed', () => {
  const rows = FX.candidateScreen;
  const basis = candidates.reportingBasis(rows);
  assert.equal(basis.declared, false, 'a period was inferred for the candidate records');
  assert.equal(basis.period, null);
  assert.equal(basis.period_state, 'undeclared');
  assert.match(basis.statement, /do not carry a reporting period/i);
  assert.match(basis.statement, /no period has been inferred/i);
  assert.match(basis.screen_period_note, /described and not carried/i);

  /* The screen rule names two comparison windows. Neither is on the rows. */
  const scanned = candidates.periodFieldScan(rows);
  assert.deepEqual(scanned, []);
});

test('F10 row counts and unique part counts are reported as two different numbers', () => {
  const rows = FX.candidateScreen;
  const cov = candidates.coverage(rows, rows, { payload: FX });
  assert.equal(cov.rows_matching, 6);
  assert.equal(cov.unique_parts, 4, 'a row without a part reference was invented into a part number');
  assert.equal(cov.rows_with_cost, 4);
  assert.equal(cov.unique_parts_with_cost, 3,
    'four costed rows were reported as four unique parts');
  assert.equal(cov.unique_parts_with_competitor_evidence, 2);
  assert.notEqual(cov.rows_matching, cov.unique_parts);
  assert.match(cov.rows_vs_parts, /two different counts/);
  assert.match(cov.cost_and_list_coverage, /coverage/);
  assert.ok(!/decision.ready/i.test(cov.cost_and_list_coverage));
  /* A row with no part reference is not a part and is not hidden either. */
  assert.equal(cov.eligible_gap, 1);
  assert.match(cov.unidentified_rows, /carry no part reference/i);
});

test('F10 cost coverage is described on the basis the cost column is actually on', () => {
  const cov = candidates.coverage(FX.candidateScreen, FX.candidateScreen, { payload: FX });
  assert.equal(cov.cost_column, 'verified_cost_eur_oct26');
  assert.equal(cov.cost_column_basis, 'OCT26');
  assert.match(cov.cost_column_statement, /forward basis/i);
  assert.match(cov.cost_column_statement, /not a historical or accounting cost/i);
  assert.ok(cov.cost_register_cross_check, 'the cost register was not compared with the screen');
  assert.equal(cov.cost_register_cross_check.cost_register_parts, 3);
});

test('F10 cost and list completeness is reported separately from approval', () => {
  const a = candidates.approvalStatus(FX.candidateScreen);
  assert.equal(a.approval_field_present, false, 'an approval state was found where none exists');
  assert.equal(a.rows_with_an_approval_state, 0);
  assert.equal(a.rows_with_complete_cost_or_list, 5);
  assert.equal(a.rows_approved, 0);
  assert.match(a.statement, /Completeness is not approval/);
});

test('F10 commercial priority is not merged into evidence readiness', () => {
  const wb = candidates.workbench(FX.candidateScreen, { page: 1, page_size: 2, payload: FX,
    screen_rule: FX.screenRule });
  assert.equal(wb.page.total, 6, 'the workbench does not reach every row');
  assert.equal(wb.page.page_count, 3);
  assert.equal(wb.page.rows.length, 2);
  assert.ok(wb.priority.total_observed_billing_eur > 0);
  assert.equal(wb.priority.rows_without_a_billing_value, 0);
  assert.notEqual(Object.keys(wb.readiness).length, 0);
  assert.ok(!Object.prototype.hasOwnProperty.call(wb.readiness, 'priority_score'),
    'readiness carries a combined priority score');
  assert.match(wb.readiness.statement, /not mixed into a priority score/i);
});

test('F10 search and paging reach the whole permitted set, and paging clamps', () => {
  const rows = FX.candidateScreen;
  const last = candidates.workbench(rows, { page: 99, page_size: 2 });
  assert.equal(last.page.page, 3);
  assert.equal(last.page.rows.length, 2);
  const found = candidates.search(rows, 'DISC');
  assert.equal(found.length, 1);
  const byPart = candidates.filter(rows, { part_number: 'SYNTH-PN-A' });
  assert.equal(byPart.length, 2);
  const unresolved = candidates.filter(rows, { unresolved_only: true });
  assert.equal(unresolved.length, 3);
});

test('F10 the screen rule states its own coverage and the difference is reported', () => {
  const r = candidates.screenRule(FX.screenRule, FX.candidateScreen);
  assert.equal(r.declared_part_numbers_with_cost, 3);
  assert.equal(r.observed_part_numbers_with_cost, 3);
  assert.equal(r.observed_rows_with_a_cost, 4);
  assert.equal(r.mismatch, null, 'a matching coverage statement was reported as a mismatch');
  assert.equal(r.status, 'proposed screening rule, not an approved commercial threshold');

  const wrong = candidates.screenRule(
    Object.assign({}, FX.screenRule, { coverage: 'verified parts cost is held for 15 part numbers' }),
    FX.candidateScreen);
  assert.equal(wrong.mismatch.declared, 15);
  assert.equal(wrong.mismatch.observed, 3);
  assert.match(wrong.mismatch.statement, /neither figure is preferred/i);
  /* The row count is reported beside the part count and is a different number. */
  assert.equal(wrong.observed_rows_with_a_cost, 4);
  assert.notEqual(wrong.observed_rows_with_a_cost, wrong.observed_part_numbers_with_cost);
});

test('F10 a candidate without a cost cannot become a case, and the blocker is named', () => {
  const row = FX.candidateScreen.find((r) => r.part_number === 'SYNTH-PN-D');
  const check = candidates.promotionBlockers(row, FX);
  assert.equal(check.promotable, false);
  const codes = check.blockers.map((b) => b.code);
  assert.ok(codes.indexOf('COST_MISSING') >= 0, 'the missing cost was not named');
  assert.ok(codes.indexOf('PERIOD_UNDECLARED') >= 0, 'the undeclared period was not named');
  const promoted = candidates.promoteToCase(row, FX);
  assert.equal(promoted.created, false);
  assert.match(promoted.statement, /Not promotable yet/);
});

test('F10 a supported candidate still cannot become a case while the period is undeclared', () => {
  const row = FX.candidateScreen.find((r) => r.part_number === 'SYNTH-PN-A');
  const rowEntity = manifest.normaliseEntity(row);
  const rowBasis = candidates.reportingBasis(FX.candidateScreen);
  const check = candidates.promotionBlockers(row, FX, { basis: rowBasis });
  assert.equal(check.promotable, false);
  assert.deepEqual(check.blockers.map((b) => b.code), ['PERIOD_UNDECLARED'],
    'unexpected blockers: ' + JSON.stringify(check.blockers));
  const promoted = candidates.promoteToCase(row, FX, { basis: rowBasis, entity: rowEntity });
  assert.equal(promoted.created, false);
  assert.match(promoted.statement, /Not promotable yet/);

  /* The same row is promotable only when a caller supplies an explicitly stated
     period. The component never supplies one itself. */
  const stated = candidates.promoteToCase(row, FX, {
    basis: { declared: true, period: 'January-June 2026', period_state: 'declared' },
    entity: rowEntity, case_id: 'CASE-FROM-CANDIDATE' });
  assert.equal(stated.created, true, stated.statement);
  assert.equal(stated.case.part_number, 'SYNTH-PN-A',
    'the original part reference was rewritten');
  assert.equal(stated.case.evidence_period, 'January-June 2026');
  assert.equal(stated.case.offer_effective_date, null);
  assert.equal(stated.case.state, 'evidence_requested');
});

/* ==================================================== MARKET-01 ... 06 === */

test('MARKET-01 a dated observation is evidence, and its limitations are listed', () => {
  const observed = evidence.evidenceStrength(FX.offers['T-PAD-G']);
  assert.equal(observed.evidence_not_truth, true);
  assert.ok(observed.limitations.length > 0);
  assert.ok(observed.limitations.some((l) => /tax basis/i.test(l)),
    'the listing tax basis was not flagged: ' + observed.limitations.join('; '));
  assert.match(observed.statement, /evidence of what a seller advertised on a date/i);
  assert.equal(observed.strength, 'partial');
  assert.equal(observed.limitations.length, 2);

  /* An observation with no date and no location is thinner still. */
  const bare = evidence.evidenceStrength({ price: 10 });
  assert.ok(bare.score < observed.score);
  assert.ok(bare.limitations.some((l) => /no retrieval date/i.test(l)));
});

test('MARKET-01 an incomplete observation is reported as incomplete, not as strong', () => {
  const complete = evidence.evidenceStrength({ retrieved: '2026-09-22',
    url: 'https://example.invalid/x', tax: 'net, exclusive of tax',
    match: 'Exact Genuine part number', approvalReady: true });
  assert.equal(complete.strength, 'complete');
  assert.deepEqual(complete.limitations, []);

  /* One unmet condition is "partial", and adding an unmet "not stated" field is
     the same as leaving it out, so the count does not move. */
  const oneMissing = evidence.evidenceStrength({ retrieved: '2026-09-22',
    url: 'https://example.invalid/x', tax: 'net, exclusive of tax',
    match: 'Exact Genuine part number' });
  assert.equal(oneMissing.strength, 'partial');
  assert.equal(oneMissing.limitations.length, 1);

  const twoMissing = evidence.evidenceStrength({ retrieved: '2026-09-22',
    url: 'https://example.invalid/x', tax: 'net, exclusive of tax' });
  assert.equal(twoMissing.strength, 'partial');
  assert.equal(twoMissing.limitations.length, 2);

  const threeMissing = evidence.evidenceStrength({ retrieved: '2026-09-22',
    url: 'https://example.invalid/x', tax: 'not stated' });
  assert.equal(threeMissing.strength, 'thin');
  assert.equal(threeMissing.limitations.length, 3);

  /* "Not stated" and an empty field are the same thing. */
  assert.equal(evidence.statesNoValue('not stated'), true);
  assert.equal(evidence.statesNoValue('n/a'), true);
  assert.equal(evidence.statesNoValue(''), true);
  assert.equal(evidence.statesNoValue(null), true);
  assert.equal(evidence.statesNoValue('net, exclusive of tax'), false);
});

test('MARKET-02 product equivalence is separate from lexical similarity', () => {
  const sim = evidence.lexicalSimilarity('SYNTH PAD KIT CALIPER DISC BRAKE FRONT',
    'SYNTH PAD KIT CALIPER DISC BRAKE FRONT');
  assert.ok(sim.ratio > 0.8, 'identical wording did not score high');
  assert.match(sim.statement, /not product equivalence/i);

  const eq = evidence.productEquivalence({ similarity_ratio: sim.ratio });
  assert.equal(eq.equivalent, null, 'a similar description was declared equivalent');
  assert.match(eq.statement, /not established/i);

  const declared = evidence.productEquivalence({ equivalence_declared: true,
    equivalence_declared_by: 'the technical source' });
  assert.equal(declared.equivalent, true);
  assert.match(declared.statement, /declaration is the basis/i);
});

test('MARKET-03 a pack is normalised only where the source states its contents', () => {
  const unknown = evidence.normalisePack({ declared_unit: 'kit' });
  assert.equal(unknown.normalised, false);
  assert.match(unknown.statement, /unstated contents/i);
  assert.equal(evidence.perPiecePrice(120.0, unknown).ok, false);

  const stated = evidence.normalisePack({ declared_unit: 'kit',
    contents: [{ name: 'pad', quantity: 4 }, { name: 'clip set', quantity: 1 }] });
  assert.equal(stated.normalised, true);
  assert.equal(stated.pieces_per_pack, 5);
  const per = evidence.perPiecePrice(120.0, stated);
  assert.equal(per.ok, true);
  assert.equal(per.amount_per_piece, 24.0,
    'the per-piece figure is the price divided by the declared pieces per pack');
});

test('MARKET-04 currency, tax and delivery adjustments are auditable and unresolved when unknown', () => {
  const unknownTax = evidence.adjustToComparable(120.0, { currency: 'EUR', tax: 'not stated' });
  assert.equal(unknownTax.ok, false);
  assert.equal(unknownTax.value, null);
  assert.ok(unknownTax.unresolved.some((u) => /tax basis is not stated/i.test(u)));

  /* RE-POINTED 2026-09-22 (VAT unit correction). These two calls used to pass a
     bare `vat_rate: 20` with no unit. The rule now requires the unit to be
     declared, because a rate of 0.2 and a rate of 20 are the same digits two
     orders of magnitude apart and a rule that guesses between them overstates a
     competitor by about a fifth. The expected figures are unchanged: 20 as a
     declared percentage was, and is, 20%. What changed is that the unit is now
     stated rather than inferred from the magnitude. */
  const unknownFx = evidence.adjustToComparable(120.0, { currency: 'GBP',
    tax: 'inclusive', vat_rate: 20, vat_rate_unit: 'percent' });
  assert.equal(unknownFx.ok, false);
  assert.equal(unknownFx.value, null);
  assert.ok(unknownFx.unresolved.some((u) => /no dated rate to EUR/i.test(u)));
  assert.ok(unknownFx.unresolved.some((u) => /delivery basis is not stated/i.test(u)));
  assert.equal(unknownFx.steps.length, 1, 'the tax step should still be recorded before the failure');

  const done = evidence.adjustToComparable(120.0, { currency: 'GBP', tax: 'inclusive',
    vat_rate: 20, vat_rate_unit: 'percent', fx_to_eur: 1.17, fx_date: '2026-09-22',
    delivery_included: true });
  assert.equal(done.ok, true, done.unresolved.join('; '));
  assert.equal(done.steps.length, 3, 'the delivery step should be recorded too');
  assert.equal(done.steps[0].step, 'remove tax');
  assert.equal(done.steps[0].rate_unit, 'percent', 'the recorded tax step states the unit it used');
  assert.equal(done.steps[1].step, 'convert to EUR');
  assert.equal(done.steps[2].step, 'delivery basis');
  assert.match(done.statement, /each step and its rule is shown/i);
  assert.ok(done.value < 120.0, 'a gross GBP figure was not reduced by tax and conversion');

  const fxWithoutADate = evidence.adjustToComparable(120.0, { currency: 'GBP', tax: 'exclusive',
    fx_to_eur: 1.17, delivery_included: true });
  assert.equal(fxWithoutADate.ok, false);
  assert.equal(fxWithoutADate.steps.length, 2,
    'a conversion without a dated rate was recorded as though it had been applied');
  assert.equal(fxWithoutADate.steps.filter((s) => s.step === 'convert to EUR').length, 0);
  assert.ok(fxWithoutADate.unresolved.some((u) => /without the date/i.test(u)));
  assert.equal(fxWithoutADate.value, null, 'an unconverted figure was still returned as comparable');
});

/* ===========================================================================
   The tax-rate unit (added 2026-09-22)

   The defect these four checks exist for: the rule computed `value / (1 + rate /
   100)` while the payload stores its rate as a fraction (`vat: 0.2`). Handing
   0.2 to that form divides by 1.002 and removes 0.2% of tax instead of 20%,
   which makes a competitor look about a fifth more expensive than it is. The
   figures below are synthetic round numbers, not a real seller's prices.
   =========================================================================== */

test('MARKET-04a a tax rate whose unit is not declared leaves the amount unresolved, never guessed', () => {
  /* Both of these are the same digits two orders of magnitude apart, and neither
     states which it is. There is no default: a default is the defect. The tax
     basis, currency and delivery are all stated, so the unit is the ONLY thing
     left undone - the refusal is about the rate and nothing else. */
  for (const rate of [0.2, 20]) {
    const r = evidence.adjustToComparable(120, { currency: 'EUR', tax: 'inclusive',
      vat_rate: rate, delivery_included: true });
    assert.equal(r.ok, false, 'a bare rate of ' + rate + ' was accepted without a declared unit');
    assert.equal(r.value, null, 'a figure was produced from a rate whose unit nobody stated');
    assert.equal(r.steps.filter((s) => s.step === 'remove tax').length, 0,
      'no tax step may be recorded when the unit is unknown, so no tax was removed: '
      + JSON.stringify(r.steps));
    assert.ok(r.steps.every((s) => s.to === s.from),
      'no step recorded for an unknown rate may have moved the value: ' + JSON.stringify(r.steps));
    assert.ok(r.unresolved.some((u) => /does not state whether that is a percentage or a fraction/i.test(u)),
      'the refusal must name the ambiguity: ' + r.unresolved.join('; '));
    assert.equal(r.unresolved.length, 1,
      'the unit must be the only thing missing here, so nothing else is being blamed: '
      + r.unresolved.join('; '));
  }

  /* And with the unit declared, the same numbers resolve. */
  const declared = evidence.adjustToComparable(120, { currency: 'EUR', tax: 'inclusive',
    vat_rate: 20, vat_rate_unit: 'percent', delivery_included: true });
  assert.equal(declared.ok, true, declared.unresolved.join('; '));
  assert.equal(declared.value, 100, '120 including 20% is 100 net');
});

test('MARKET-04b the digits do not decide the unit: 0.2 and 20 declared as percentages differ', () => {
  /* The regression guard. A rule that "helpfully" treats a small number as a
     fraction would return the same net for both of these. It must not: declared
     as percentages they are 0.2% and 20%, and the answers differ by nearly 20
     euro on a 120 euro inclusive amount. */
  const asTwentyPercent = evidence.adjustToComparable(120, { currency: 'EUR', tax: 'inclusive',
    vat_rate: 20, vat_rate_unit: 'percent', delivery_included: true });
  const asZeroPointTwoPercent = evidence.adjustToComparable(120, { currency: 'EUR', tax: 'inclusive',
    vat_rate: 0.2, vat_rate_unit: 'percent', delivery_included: true });

  assert.equal(asTwentyPercent.value, 100);
  assert.equal(asZeroPointTwoPercent.value, 119.76,
    'a declared 0.2 percent rate removes 0.2 percent, not 20');
  assert.notEqual(asTwentyPercent.value, asZeroPointTwoPercent.value,
    'the two declarations were collapsed into one answer, so something is guessing from the magnitude');

  /* A fraction is converted by the caller, and the rule records the unit it used. */
  assert.equal(asTwentyPercent.steps[0].rate_unit, 'percent');
  assert.equal(asTwentyPercent.steps[0].rate, 20);
});

test('MARKET-04c a rate unit that is not a declared unit is refused rather than coerced', () => {
  const unknown = evidence.adjustToComparable(120, { currency: 'EUR', tax: 'inclusive',
    vat_rate: 20, vat_rate_unit: 'twenty percent', delivery_included: true });
  assert.equal(unknown.ok, false);
  assert.equal(unknown.value, null);
  assert.ok(unknown.unresolved.some((u) => /not one of the units this rule accepts/i.test(u)),
    'an unrecognised unit must be named, not silently treated as a percentage: '
    + unknown.unresolved.join('; '));
});

test('MARKET-04d a declared fraction is converted before the call, and the old wrong answer is not returned', () => {
  /* The payload's own documented shape: a rate held as a fraction on the row and
     converted by the caller to the percentage the rule asks for. A synthetic
     inclusive amount of 120 at a documented rate of 1.5 gives 150.
     The defect this replaces returned 179.64 here - it kept 99.8% of the tax. */
  const convertedByTheCaller = evidence.adjustToComparable(120, {
    currency: 'GBP', tax: 'inclusive', vat_rate: 20, vat_rate_unit: 'percent',
    fx_to_eur: 1.5, fx_date: '2026-09-22', delivery_included: true
  });
  assert.equal(convertedByTheCaller.ok, true, convertedByTheCaller.unresolved.join('; '));
  assert.equal(convertedByTheCaller.value, 150);
  assert.notEqual(convertedByTheCaller.value, 179.64,
    'the divide-by-1.002 answer was returned, so the rate was read at the wrong magnitude');

  /* And the same inputs without the declaration are refused outright, not
     quietly computed at whichever magnitude the number happens to look like. */
  const undeclared = evidence.adjustToComparable(120, {
    currency: 'GBP', tax: 'inclusive', vat_rate: 0.2,
    fx_to_eur: 1.5, fx_date: '2026-09-22', delivery_included: true
  });
  assert.equal(undeclared.ok, false);
  assert.equal(undeclared.value, null);
});

test('MARKET-05 old and conflicting observations stay visible', () => {
  const rows = Object.values(FX.offers);
  const r = evidence.observationConflicts(rows, { as_of: '2026-09-22', stale_after_days: 180 });
  assert.equal(r.observations, rows.length);
  assert.equal(r.outdated.length, 1, 'the 2025 observation was not flagged as old');
  assert.equal(r.outdated[0].retrieved, '2025-11-01');
  assert.equal(r.conflicts.length, 1, 'the two different amounts were not reported as a conflict');
  assert.equal(r.conflicts[0].amounts.length, 2);
  assert.match(r.conflicts[0].statement, /none is selected as the correct one/i);
  assert.match(r.statement, /remain visible/i);
});

test('MARKET-06 the evidence inventory states what each set cannot support', () => {
  const inv = evidence.inventory();
  assert.ok(inv.length >= 5);
  inv.forEach((i) => {
    assert.ok(i.cannot_support, i.set + ' does not state a limit');
    assert.ok(i.statement);
  });
  assert.ok(inv.some((i) => /no recorded line/i.test(i.statement)));
  assert.ok(inv.some((i) => /not several independent competitors/i.test(i.statement)));
});

/* ================================================== cross-cutting rules === */

test('a missing period, cost or difference is never reported as zero or as a match', () => {
  const basis = candidates.reportingBasis(FX.candidateScreen);
  assert.equal(basis.period, null);
  assert.notEqual(basis.period, 0);

  const cov = candidates.coverage(FX.candidateScreen, FX.candidateScreen, { payload: FX });
  assert.equal(cov.unique_parts_with_cost, 3);
  assert.notEqual(cov.unique_parts_with_cost, 4, 'unpriced rows were counted as costed rows');
  assert.equal(cov.rows_unidentified, 1);
  assert.equal(cov.unique_parts, 4);

  const nulls = FX.costReconciliation.filter((r) => r.price_file_fob_eur === null);
  assert.ok(nulls.length >= 1);
  nulls.forEach((r) => {
    assert.equal(r.difference, null);
    assert.notEqual(r.difference, 0, 'a null reconciliation difference was reported as a match');
  });
});

test('the data layer does not invent a period, a rate, a fitment or an equivalence', () => {
  const src = ['manifest.js', 'costbasis.js', 'evidence.js', 'candidates.js']
    .map((f) => fs.readFileSync(path.join(ROOT, 'src', 'data', f), 'utf8')).join('\n');
  assert.ok(src.indexOf('163.7') < 0 && src.indexOf('172.6') < 0 && src.indexOf('178.5') < 0,
    'a foreign-exchange rate was hardcoded in the data layer');
  assert.ok(!/jpy_per_eur\s*[:=]\s*\d/.test(src), 'a rate literal is set in the data layer');
});

/* ------------------------------------------------- authorised payload ---- */

test('the authorised payload, when present, satisfies the same dates and counts', () => {
  if (!authorised) {
    assert.ok(fs.existsSync(FIXTURE_FILE),
      'neither the authorised payload nor the local fixture is present');
    return;
  }
  const sep = costbasis.resolveBasis(authorised, '2026-09-22');
  const oct = costbasis.resolveBasis(authorised, '2026-10-01');
  assert.equal(sep.basis_id, 'SEP26');
  assert.equal(oct.basis_id, 'OCT26');
  assert.equal(costbasis.resolveBasis(authorised, 'nonsense').resolved, false);
  assert.equal(costbasis.resolveBasis(authorised, '2035-01-01').resolved, false);

  const w = costbasis.windowOf(costbasis.basisById(authorised, 'OCT26'));
  assert.equal(w.to, '2027-03-31', 'the October window was left open ended');

  const rows = authorised.candidateScreen || [];
  const cov = candidates.coverage(rows, rows, { payload: authorised });
  assert.equal(cov.rows_matching, AUTHORISED_ROWS);
  assert.equal(cov.rows_with_cost, 15);
  assert.equal(cov.unique_parts_with_cost, 8,
    'the cost coverage was reported as a unique part count');
  assert.equal(cov.unique_parts_with_competitor_evidence, 2);
  assert.equal(cov.rows_matching !== cov.unique_parts_with_cost, true);

  const basis = candidates.reportingBasis(rows);
  assert.equal(basis.declared, false);

  /* The screen rule's own coverage figure does not match the exported rows. */
  const rule = candidates.screenRule(authorised.screenRule, rows);
  assert.equal(rule.declared_part_numbers_with_cost, 15);
  assert.equal(rule.observed_part_numbers_with_cost, 8);
  assert.equal(rule.observed_rows_with_a_cost, 15);
  assert.ok(rule.mismatch, 'the screen coverage difference was not reported');

  /* The candidate records carry no approval field at all. */
  const approval = candidates.approvalStatus(rows);
  assert.equal(approval.rows_with_an_approval_state, 0);
  assert.equal(approval.rows_approved, 0);

  /* The two null reconciliation differences are reported, not treated as matches. */
  const nulls = (authorised.costReconciliation || [])
    .filter((r) => r.price_file_fob_eur === null);
  assert.equal(nulls.length, 2);
  nulls.forEach((r) => assert.equal(r.difference, null));

  const m = manifest.build(authorised);
  assert.equal(m.reconciliation.pack_rows_declared, 3945);
  assert.equal(m.reconciliation.pack_rows_actual, 3856);
  assert.equal(manifest.assertShippable(m).ok, true);

  /* One cost-register part is not on the screen at all, and the manifest says so
     rather than reporting a screen coverage figure as if it were the register.
     Its identifier is read from the payload in memory and compared, not written
     here: the payload is excluded from version control and this file is not. */
  const crossCheck = cov.cost_register_cross_check;
  const registerParts = (authorised.verifiedCosts || []).map((r) => String(r.part_number));
  const screened = new Set(rows.map((r) => String(r.part_number)));
  const inRegisterNotScreened = registerParts.filter((p) => !screened.has(p));
  assert.equal(inRegisterNotScreened.length, 1,
    'the fixture no longer carries exactly one cost-register part that the screen omits');
  assert.deepEqual(crossCheck.in_register_not_screened, inRegisterNotScreened,
    'the cross-check does not report the register part the screen omits');
});

test('the restricted fixture is excluded from version control and marked restricted', () => {
  const ignore = fs.readFileSync(path.join(ROOT, '.gitignore'), 'utf8');
  assert.match(ignore, /payload\/\*\.json/, 'the payload folder is not ignored');
  assert.ok(FIXTURE_FILE.indexOf(path.join('05_AIM_Universe', 'payload')) >= 0,
    'the fixture is not inside the ignored payload folder');
  const written = JSON.parse(fs.readFileSync(FIXTURE_FILE, 'utf8'));
  assert.match(written._note, /RESTRICTED LOCAL TEST FIXTURE/);
});
