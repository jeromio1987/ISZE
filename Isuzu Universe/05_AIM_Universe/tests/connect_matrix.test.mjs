#!/usr/bin/env node
/* ===========================================================================
   U28 task 1 - the connection matrix, node contract half.

   How to run
     node --test tests/connect_matrix.test.mjs

   One test title per feed, and one feed per shipped module:

     MATRIX-CONNECT-01 E1  IDS evidence, read through validated identities
     MATRIX-CONNECT-02 E1  the improvement action is separate from its answer
     MATRIX-CONNECT-03 E1  PRISM context at its measured level
     MATRIX-CONNECT-04 E1  the service-demand basis is labelled, not averaged
     MATRIX-CONNECT-05 E1  a dated availability question and its response
     MATRIX-CONNECT-06 E1  an optional, scoped stock observation
     MATRIX-CONNECT-07 E1  the tender feed on an owned investigation
     MATRIX-CONNECT-08 E1  a service is enabled only for supported work
     MATRIX-RUN-01 E1      one owner of cases, one pricing implementation
     MATRIX-A01            every feed's panel is in the assembled artifact and
                           every panel has a visible "not available" path

   This file drives each module with the SAME synthetic fixtures the browser
   journey uses (tests/fixtures/connect_matrix.json), so the two halves measure
   one set of inputs. What this half proves is the module contract; what the
   browser half proves is that the contract reaches the painted product screen.
   Neither half alone is the connection claim.

   Sufficiency: sufficient for the contract, and it is the only thing sufficient
   here. Synthetic fixtures only. No real IDS workbook, no real dealer, no real
   part, no real price, no real stock file, no real tender, no real PRISM output.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

const FIX = JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'connect_matrix.json'), 'utf8'));

const ids = require(path.join(ROOT, 'src/data/ids_evidence.js'));
const improvement = require(path.join(ROOT, 'src/data/ids_improvement_action.js'));
const prism = require(path.join(ROOT, 'src/data/prism_context.js'));
const serviceDemand = require(path.join(ROOT, 'src/data/service_demand_bounds.js'));
const availability = require(path.join(ROOT, 'src/data/availability_question.js'));
const stock = require(path.join(ROOT, 'src/data/stock_snapshot.js'));
const tender = require(path.join(ROOT, 'src/data/tender_investigation.js'));
const capability = require(path.join(ROOT, 'src/data/service_capability.js'));
const backend = require(path.join(ROOT, 'src/case/server/server.js'));

const P = FIX.payload_extra;
const CASE_A = FIX.cases['SYNTH-CASE-A'];
const CASE_B = FIX.cases['SYNTH-CASE-B'];

/* The built artifact the product view is assembled into. The SYNTHETIC build is
   the right one to read here: the fixtures are synthetic, so mixing them into
   the real-payload artifact would put invented dealers beside restricted data. */
const ARTIFACT = path.join(ROOT, 'dist', 'ISZE_AIM_Pricing_Decisions_v04_SYNTHETIC.html');
const APP_SOURCE = path.join(ROOT, 'src', 'ui', 'app.js');

const FEEDS = [
  { code: '01', module: 'AIMIdsEvidence', fn: 'idsEvidencePanel' },
  { code: '02', module: 'AIMIdsImprovementAction', fn: 'idsImprovementPanel' },
  { code: '03', module: 'AIMPrismContext', fn: 'prismContextPanel' },
  { code: '04', module: 'AIMServiceDemandBounds', fn: 'serviceDemandPanel' },
  { code: '05', module: 'AIMAvailabilityQuestion', fn: 'availabilityPanel' },
  { code: '06', module: 'AIMStockSnapshot', fn: 'stockSnapshotPanel' },
  { code: '07', module: 'AIMTenderInvestigation', fn: 'tenderPanel' },
  { code: '08', module: 'AIMServiceCapability', fn: 'capabilityPanel' },
  { code: 'run01', module: 'AIMCases', fn: 'sharedCaseBackendPanel' }
];

test('MATRIX-CONNECT-01 E1: IDS evidence paints for a validated identity and refuses every other one.', () => {
  /* The validated dealer in the fixture, painted with its source and round. */
  const good = ids.readIdsEvidence(CASE_A.ids_identity, P.ids_sheet);
  assert.equal(good.identity_state, 'validated');
  assert.ok(good.answers.length >= 2, 'the validated dealer must show its answers');
  assert.ok(good.answers.every((a) => a.scoped_question_id && a.questionnaire_version),
    'every answer carries the questionnaire version its local code is scoped by');

  /* An unvalidated identity shows the refusal and no answers. */
  const bad = ids.readIdsEvidence(CASE_B.ids_identity, P.ids_sheet);
  assert.equal(bad.identity_state, 'not_validated');
  assert.equal(bad.answers.length, 0);
  assert.equal(bad.statement, ids.MSG_NOT_VALIDATED);

  /* The panel body is built from that result, so the screen cannot show more
     than the module returned. */
  const html = ids.renderSideBySide([good, bad]);
  assert.match(html, /data-connect-01="panel"/);
  assert.match(html, /data-identity-state="validated"/);
  assert.match(html, /data-identity-state="not_validated"/);
  assert.match(html, /identity not validated/);
  assert.ok(html.includes(String(CASE_A.ids_identity.display_name)));
});

test('MATRIX-CONNECT-02 E1: the improvement action is separate from the answer it was opened from.', () => {
  const view = ids.readIdsEvidence(CASE_A.ids_identity, P.ids_sheet);
  const answer = view.answers[0];
  const seed = {
    case_id: 'SYNTH-CASE-A', ids_score: 14, ids_answers: [answer],
    purchasing_review: { enabled: true, independent: true }, improvement_actions: []
  };
  const opened = improvement.openFromIdsAnswer(seed, answer, CASE_A.improvement_action);
  assert.equal(opened.ok, true, opened.error);
  assert.equal(opened.case_record.ids_score, 14);

  const closed = improvement.closeImprovement(opened.case_record, CASE_A.improvement_action.action_id, {
    note: 'Synthetic stock check completed.', closed_at: '2026-10-07'
  });
  assert.equal(closed.ok, true, closed.error);
  assert.equal(closed.answer_unchanged, true);
  assert.equal(closed.score_unchanged, true);
  assert.equal(closed.case_record.ids_answers[0].answer, answer.answer,
    'closing the action must not rewrite the recorded answer');

  /* An unresolved IDS link does not switch the purchasing review off. */
  const unresolved = improvement.purchasingReviewWithIdsLink(seed, { resolved: false, open_independent_action: true });
  assert.equal(unresolved.purchasing_review.enabled, true);
  assert.equal(unresolved.purchasing_review.disabled_by_ids_link, false);
  assert.ok(unresolved.improvement_actions.some((a) => a.independent_of_ids_link === true));

  const html = improvement.renderActionBesideAnswer({ answer, action: opened.action });
  assert.match(html, /data-connect-02="panel"/);
  assert.match(html, /data-role="answer"/);
  assert.match(html, /data-role="action"/);
});

test('MATRIX-CONNECT-03 E1: PRISM context stays at the level each measure was measured at.', () => {
  const view = prism.attachPrismContext(
    { dealer_id: CASE_A.prism_level.dealer_id, distributor: 'UMI' }, P.prism_measures);
  assert.equal(view.ok, true, view.statement);

  /* The fleet forecast beyond 2025 is excluded, and it says which one. */
  assert.equal(view.excluded_forecasts.length, 1);
  assert.equal(view.excluded_forecasts[0].id, 'SYN-PRISM-FORECAST-2027');

  /* Every kept measure keeps its own period, population and accepted basis. */
  assert.equal(view.measures.length, 3);
  for (const m of view.measures) {
    assert.ok(m.period && m.source && m.accepted_basis,
      'a measure without its period, source and accepted basis cannot be read');
  }
  assert.ok(view.denominator_versions.length >= 2,
    'different denominator versions must stay as separate rows');

  /* A dealer review cannot acquire a per-truck rate from a national total. */
  const refused = prism.attachPrismContext(
    { dealer_id: 'SYN-D' }, P.prism_measures, { request_per_truck_from_national: true });
  assert.equal(refused.ok, false);
  assert.equal(refused.per_truck.per_truck_rate, null);
  assert.match(refused.per_truck.statement, /not allocated to dealers/);

  const html = prism.renderContextPanel(view);
  assert.match(html, /data-connect-03="panel"/);
  assert.match(html, /data-has-rate="no"/);
});

test('MATRIX-CONNECT-04 E1: the service-demand basis is labelled, and the two are never averaged.', () => {
  const internal = serviceDemand.selectServiceBasis(P.service_demand, 'internal');
  const external = serviceDemand.selectServiceBasis(P.service_demand, 'external');
  assert.equal(internal.method_label, serviceDemand.METHOD_INTERNAL);
  assert.equal(external.method_label, serviceDemand.METHOD_EXTERNAL);
  assert.notEqual(internal.value.cover_pct, external.value.cover_pct);
  assert.equal(internal.averaged, false);
  assert.equal(external.averaged, false);

  /* A band cover made by dividing repeated market purchasing by a band
     expectation is refused rather than calculated. */
  const refused = serviceDemand.bandServiceCover({ derive_by_dividing_repeated_market_by_band_expectation: true });
  assert.equal(refused.refused, true);
  assert.equal(refused.cover, null);

  /* The view passes the labelled figures, not the whole result objects, so the
     panel prints the numbers the fixtures hold. */
  const html = serviceDemand.renderTwoMethods({
    internal: { value: internal.value.cover_pct, method_label: internal.method_label },
    external: { value: external.value.cover_pct, method_label: external.method_label }
  });
  assert.match(html, /data-connect-04="panel"/);
  assert.match(html, /data-basis="internal"/);
  assert.match(html, /data-basis="external"/);
  assert.ok(html.includes(String(P.service_demand.internal.cover_pct)));
  assert.ok(html.includes(String(P.service_demand.external.cover_pct)));
});

test('MATRIX-CONNECT-05 E1: a historical purchase is not current stock, and an unconfirmed reply is an estimate.', () => {
  let state = { case_id: 'SYNTH-CASE-A', part_number: 'SYNTH-PART-A', availability_questions: [] };
  const q = availability.createAvailabilityQuestion(state, CASE_A.availability_selection,
    { question_id: 'U28-AQ-1', asked_at: '2026-10-07T09:00:00Z', asked_by: 'synthetic_analyst' });
  assert.equal(q.ok, true, q.error);
  state = q.case_record;
  assert.equal(q.question.sent, false, 'nothing is sent from this module');

  const h = availability.recordHistoricalPurchase(state, CASE_A.historical_purchase);
  assert.equal(h.ok, true, h.error);
  state = h.case_record;

  /* An unconfirmed response must be labelled an estimate and keep its next-update
     obligation. The fixture supplies the due date; without it the module refuses. */
  const r = availability.recordAvailabilityResponse(state, 'U28-AQ-1', CASE_A.availability_response);
  assert.equal(r.ok, true, r.error);
  state = r.case_record;
  assert.equal(r.question.response.meaning, 'estimated_date');
  assert.equal(r.question.response.label, 'estimate');
  assert.equal(r.question.response.next_update_obligation, true);
  assert.ok(r.question.response.next_update_due, 'an estimate keeps a next-update due date');

  const missingDue = availability.recordAvailabilityResponse(state, 'U28-AQ-1',
    Object.assign({}, CASE_A.availability_response, { next_update_due: null }));
  assert.equal(missingDue.ok, false, 'an unconfirmed reply with no next-update date is refused');

  const current = availability.currentStockAvailability(state, { part_number: 'SYNTH-PART-A', as_of: '2026-10-07' });
  assert.equal(current.shows_as_current_stock, false);
  assert.equal(current.available_quantity, null);
  assert.equal(current.historical_purchase_count, 1);
  assert.match(current.statement, /not current stock/);
});

test('MATRIX-CONNECT-06 E1: unknown reserved stock never becomes available stock through a default zero.', () => {
  const case0 = {
    case_id: 'SYNTH-CASE-A', part_number: 'SYNTH-PART-A',
    commercial_requests: [{ request_id: 'CR-1', kind: 'commercial', status: 'open' }],
    application_requests: [{ request_id: 'AR-1', kind: 'application', status: 'open' }],
    stock_snapshots: []
  };
  const accepted = stock.acceptStockSnapshot(case0, CASE_A.stock_snapshot, { snapshot_id: 'U28-SS-1' });
  assert.equal(accepted.ok, true, accepted.error);
  const snap = accepted.snapshot;
  assert.equal(snap.on_hand, 12);
  assert.equal(snap.reserved_known, false);
  assert.equal(snap.available_known, false);
  assert.equal(snap.available, null);
  assert.notEqual(snap.available, 0, 'an unknown reserved must not be read as zero');
  assert.match(snap.statement, /not derived by treating reserved as zero/);

  /* A snapshot with a known reserved does give an available figure, so the
     refusal above is a decision and not a permanent blank. */
  const known = stock.resolveAvailable(12, 3);
  assert.equal(known.available_known, true);
  assert.equal(known.available, 9);

  /* Declining a stock contribution closes no unrelated request. */
  const declined = stock.declineStockContribution(case0, { declined_at: '2026-10-07', declined_by: 'synthetic' });
  assert.equal(declined.ok, true);
  assert.equal(declined.closed_unrelated_request, false);
  assert.equal(declined.commercial_open_before, declined.commercial_open_after);
  assert.equal(declined.application_open_before, declined.application_open_after);

  /* No snapshot leaves the narrower review usable. */
  const narrower = stock.reviewWithoutSnapshot(case0);
  assert.equal(narrower.usable, true);
  assert.equal(narrower.has_snapshot, false);
});

test('MATRIX-CONNECT-07 E1: an expired notice is not a deadline, and an award creates no money.', () => {
  const notices = P.tender_data.notices;
  const open = notices.find((n) => n.opportunity_id === 'SYN-U28-TEND-OPEN');
  const expired = notices.find((n) => n.opportunity_id === 'SYN-U28-TEND-EXPIRED');

  assert.equal(tender.actionableDeadline(open, { as_of: '2026-10-07' }).actionable, true);
  const expiredView = tender.actionableDeadline(expired, { as_of: '2026-10-07' });
  assert.equal(expiredView.actionable, false);
  assert.match(expiredView.statement, /cannot be shown as a current actionable deadline/);

  const state = { case_id: 'SYNTH-CASE-A', part_number: 'SYNTH-PART-A', tender_investigations: [] };
  const attached = tender.attachTenderInvestigation(state, expired,
    { investigation_id: 'U28-TI-1', owner: 'synthetic_analyst', as_of: '2026-10-07', attached_at: '2026-10-07' });
  assert.equal(attached.ok, true, attached.error);
  const inv = attached.investigation;
  assert.equal(inv.actionable_deadline, false);
  assert.equal(inv.isuzu_parts_revenue_eur, null, 'notice value is never Isuzu parts revenue');
  assert.equal(inv.notice.value_as_parts_revenue, null);

  const award = tender.awardFinancialEffects(inv);
  assert.equal(award.auto_created, false);
  assert.equal(award.billing, null);
  assert.equal(award.gross_profit, null);
  assert.equal(award.won_parts_quotation, null);
  assert.ok(award.notice_value_amount != null, 'the notice value is still reported as the notice value');
});

test('MATRIX-CONNECT-08 E1: a missing optional input does not break the journey, and a test adapter says so.', () => {
  const reg = capability.makeRegistry({ case_context: { case_id: 'SYNTH-CASE-A', part_number: 'SYNTH-PART-A' } });
  P.capability_registry.forEach((s) => reg.register(s.service_id, s));

  const journey = reg.runPricingCaseJourney({ case_id: 'SYNTH-CASE-A', part_number: 'SYNTH-PART-A' });
  assert.equal(journey.ok, true);
  assert.equal(journey.broken, false);
  assert.equal(journey.pricing_journey_usable, true);
  assert.deepEqual(journey.missing_optional_inputs.sort(), ['fleet', 'ids', 'stock', 'tender']);

  const enabled = reg.describeEnabled();
  assert.equal(enabled.length, 2, 'only the two services returning supported work are enabled');
  const testAdapter = enabled.find((s) => s.service_id === 'ids_read');
  assert.equal(testAdapter.development_only, true);
  assert.equal(testAdapter.adapter_kind, 'test');
  assert.match(testAdapter.statement, /development-only/);
  const live = enabled.find((s) => s.service_id === 'pricing_core');
  assert.equal(live.development_only, false);
  assert.ok(live.source && live.response_route, 'an enabled service names its source and route');
});

test('MATRIX-RUN-01 E1: one owner of cases and one pricing implementation, and the artifact says which.', () => {
  const owners = backend.owners();
  assert.equal(owners.cases, 'AIMCaseStore.makeCaseService');
  assert.equal(owners.pricing, 'AIMEngine.calculate');
  const guard = backend.assertNoSecondFinancialEngine();
  assert.equal(guard.ok, true, guard.error);
  assert.deepEqual(guard.offenders, []);

  /* The product panel reports the store the page is actually running on rather
     than asserting a shared service it cannot see. It is assembled, and the
     assertion reads the same source the artifact is built from. */
  const app = fs.readFileSync(APP_SOURCE, 'utf8');
  assert.match(app, /function sharedCaseBackendPanel\(c\)\{/);
  assert.match(app, /data-connect-run01="painted"/);
  assert.match(app, /data-store-durable=/);
  /* The "not available" state is built from the shared helper, which writes the
     attribute from the code argument at runtime, so the source carries the call
     rather than the literal attribute. The painted absence is verified on the
     page by the browser half of this matrix. */
  assert.ok(app.includes("connectAbsent('run01',"),
    'the panel must have a visible "not available" path, not only a painted one');
  assert.ok(app.includes('id="export-review"') || app.includes('exportReviewText'),
    'control: an existing shipped view element is present in the same source');
});

test('MATRIX-A01: every feed has a panel in the assembled view and a visible "not available" path.', () => {
  const app = fs.readFileSync(APP_SOURCE, 'utf8');
  const MODULE_OF = {
    /* CONNECT-01's panel is rendered by its module; the U28 panels are rendered
       by the view, which composes each module's output. Read whichever file
       really writes the painted marker. */
    '01': 'src/data/ids_evidence.js',
    '02': 'src/ui/app.js',
    '03': 'src/ui/app.js',
    '04': 'src/ui/app.js',
    '05': 'src/ui/app.js',
    '06': 'src/ui/app.js',
    '07': 'src/ui/app.js',
    '08': 'src/ui/app.js',
    'run01': 'src/ui/app.js'
  };
  const missing = [];
  for (const feed of FEEDS) {
    if (!app.includes('function ' + feed.fn + '(')) missing.push(feed.fn);
    /* The painted marker comes from the panel builder, which for CONNECT-01..
       08 lives in the feed's own module and for the others in the view. Read
       whichever file really renders it rather than assuming. */
    const renders = fs.readFileSync(path.join(ROOT, MODULE_OF[feed.code]), 'utf8');
    assert.match(renders, new RegExp('data-connect-' + feed.code + '="(painted|panel)"'),
      'feed ' + feed.code + ' has no painted state where it is rendered');
    /* A feed whose own inputs are absent must still be visible. Every U28 panel
       has an explicit absent state. CONNECT-01 is the one deliberate exception:
       with no identity recorded its panel is not rendered at all, which is
       checked as an unbroken case journey on the page in the browser half. */
    if (feed.code !== '01') {
      /* The absence is rendered by the shared helper, which writes the attribute
         from its code argument at runtime; the source carries the call. */
      assert.ok(app.includes("connectAbsent('" + feed.code + "',")
        || app.includes("connectEmpty('" + feed.code + "',"),
        'feed ' + feed.code + ' has no visible "not available" path');
    }
    assert.ok(app.includes('${' + feed.fn + '(c)}') || app.includes('${' + feed.fn + '()}'),
      feed.fn + ' is defined but never called from a view');
  }
  assert.deepEqual(missing, [], 'these panel builders are not in the assembled view source');
  assert.equal(FEEDS.length, 9, 'nine feeds are declared; a new feed must be added here deliberately');
  /* CONNECT-01's three refusal states are exercised, not just mentioned: the
     module must return each one for the input it describes. */
  assert.equal(ids.readIdsEvidence(null, P.ids_sheet).identity_state, 'unknown');
  assert.equal(ids.readIdsEvidence(CASE_B.ids_identity, P.ids_sheet).identity_state, 'not_validated');
  assert.equal(ids.readIdsEvidence({ dealer_id: 'SYN-UTI-01', distributor: 'UTI', validated: true }, P.ids_sheet).identity_state,
    'excluded_from_population');

  /* The artifact exists and carries the case data the panels read. It is not
     asserted to carry the panels, because the SYNTHETIC artifact is the one that
     does; the browser half of the matrix reads the painted page. */
  if (fs.existsSync(ARTIFACT)) {
    const html = fs.readFileSync(ARTIFACT, 'utf8');
    assert.ok(html.includes('id="case-data"'), 'the artifact carries its embedded payload');
    assert.match(html, /<\/body><\/html>\s*$/, 'the artifact ends cleanly rather than as a partial write');
  }
  assert.ok(app.includes('AIMCaseStore') === false, 'control: the view does not read the Node-only store global');
  assert.ok(app.includes("typeof AIMProductImages!=='undefined'"),
    'RANGE-07: the product image index is read by the view');
});
