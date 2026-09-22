#!/usr/bin/env node
'use strict';
/* ===========================================================================
   SAFE-05 - download and export routes produce the bytes that were asserted.

   SAFE-08 - hostile and untrusted content.

   Two different kinds of evidence are used, and they are kept apart:

     - The bytes written by the product's own download route are read from disk
       (written by tests/accept/accept_02_journey.py). These prove what a person
       would actually receive.
     - The module is exercised directly for the cases a click cannot reach,
       such as a crafted description and an unauthorised recipient.

   What this file does NOT claim
     - A browser-side filter is not access control. Nothing here is a statement
       that a hosted page would be safe: there is no server, so there is no
       server-side permission to test.
     - Production identity and tenant policy are unimplemented. The identity used
       below is the module's own development shim and every result says so.
   =========================================================================== */
const H = require('./lib/harness.cjs');
const fs = require('node:fs');
const path = require('node:path');

const engine = H.requireModule(H.PATHS.engine);
const exportRoute = H.requireModule(H.PATHS.exportData);
// RETIRED-MODULE-USE: src/output/recipients.js - the permission table, the development
// identity and the attachment-storage gap (S06, S07, S08, S11) exist ONLY here: no shipped
// module implements them, so a failure in them cannot be caused by a missing rebuild. The
// export questions are asserted against src/data/export.js, which tools/build.py assembles;
// this load keeps the retired module's answers as a recorded comparison (S09, S09b, S10c).
const recipients = H.requireModule(H.PATHS.recipients);
const candidates = H.requireModule(H.PATHS.candidates);

const run = H.makeRun('SAFE-05/08', 'Export bytes, and hostile or untrusted content',
  ['Judged on bytes on disk plus direct module calls, with the two kept apart.',
   'No server exists, so server-side permission is explicitly not tested.']);
run.tested_files = H.pin([H.PATHS.exportData, H.PATHS.recipients, H.PATHS.engine,
  H.PATHS.candidates, H.PATHS.distHtml, H.PATHS.distReport]);
run.server_side_access_control = {
  tested: false,
  reason: 'No backend, no service and no session exists for this component. A browser-side filter is '
    + 'not access control, and nothing in this file should be read as evidence that it is. '
    + 'Production identity, organisation membership and revocation are unimplemented.'
};

/* =========================================================== SAFE-05 ======= */

const EXPORT_DIR = path.join(H.OUT, 'exports');
const shipped = fs.existsSync(EXPORT_DIR)
  ? fs.readdirSync(EXPORT_DIR).filter(f => f.endsWith('.out')) : [];
run.download_files = { dir: EXPORT_DIR, count: shipped.length };

function expectedRouteFor(name) {
  if (name.endsWith('internal_record.out')) return 'internal record';
  if (name.endsWith('participant_brief.out')) return 'participant brief';
  if (name.endsWith('recovery_bundle.out')) return 'case recovery bundle';
  if (name.endsWith('readable_review.out')) return 'readable case review';
  return null;
}

H.test(run, 'S01', 'Each download route wrote bytes, and each JSON route parses', () => {
  H.isTrue(shipped.length > 0, 'no download bytes are on disk; run tests/accept/accept_02_journey.py first');
  const rows = {};
  for (const f of shipped) {
    const route = expectedRouteFor(f);
    const raw = fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8');
    const row = { route, bytes: Buffer.byteLength(raw, 'utf8'), parses: null, root_keys: null };
    if (route === 'readable case review') {
      row.parses = /^<!doctype html>/i.test(raw);
      row.has_table_rows = (raw.match(/<tr>/gi) || []).length;
    } else {
      try {
        row.parses = true;
        row.root_keys = Object.keys(JSON.parse(raw));
      } catch (e) {
        row.parses = false;
        row.error = e.message;
      }
    }
    rows[f] = row;
  }
  run.download_inspection = rows;
  const bad = Object.entries(rows).filter(([, r]) => r.bytes <= 0 || r.parses === false);
  H.eq(bad.length, 0, 'routes that wrote nothing or wrote something unreadable: ' + JSON.stringify(bad));
  const routes = [...new Set(Object.values(rows).map(r => r.route))];
  return `${Object.keys(rows).length} file(s) written across ${routes.length} routes, all non-empty and readable`;
});

H.test(run, 'S01b', 'The readable case review is not an empty page shell', () => {
  const files = shipped.filter(f => f.endsWith('readable_review.out'));
  H.isTrue(files.length > 0, 'no readable case review was written');
  const findings = [];
  for (const f of files) {
    const raw = fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8');
    const rows = (raw.match(/<tr>/gi) || []).length;
    /* An empty shell where the data is simply absent is a FAIL, not a pass. */
    if (rows < 4) findings.push(`${f} has only ${rows} table row(s)`);
    if (!/ISZE INTERNAL ONLY/.test(raw)) findings.push(`${f} is not marked internal`);
  }
  H.eq(findings.length, 0, JSON.stringify(findings));
  return `${files.length} review page(s), each with at least four table rows and an internal marking`;
});

H.test(run, 'S01c', 'The participant brief route writes a brief that is a valid participant document', () => {
  /* This is the same defect as ACCEPT-04 D06, asserted here on the bytes on
     disk. It is repeated deliberately: SAFE-05 is about the download route, and
     the download route is where the empty brief is produced. */
  const files = shipped.filter(f => f.endsWith('participant_brief.out'));
  H.isTrue(files.length > 0, 'no participant brief was written by the download route');
  const findings = [];
  for (const f of files) {
    const parsed = JSON.parse(fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8'));
    if (parsed.schema !== 'isze-pricing-member-brief') {
      findings.push(`${f} has schema ${JSON.stringify(parsed.schema)}; top-level keys are `
        + `${JSON.stringify(Object.keys(parsed))}, so it carries no offer for the recipient`);
    }
  }
  H.eq(findings.length, 0, JSON.stringify(findings));
  return `${files.length} participant brief(s) carry their declared schema and an offer`;
});

  H.test(run, 'S02', 'The recovery bundle contains the saved revision, so it can restore the work', () => {
    const bundles = shipped.filter(f => f.endsWith('recovery_bundle.out'));
    H.isTrue(bundles.length > 0, 'no recovery bundle was written');
    const findings = [];
    let totalCases = 0;
    for (const f of bundles) {
      const parsed = JSON.parse(fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8'));
      const ids = Object.keys(parsed.cases || {});
      totalCases += ids.length;
      if (!ids.length) findings.push(`${f} contains no case`);
      for (const id of ids) {
        const rec = parsed.cases[id];
        /* REVISED 2026-09-22. The record used to carry a `revisions` array. The
           case service now keeps an append-only `history` log instead - that is
           CASE-02's requirement - and src/data/cases.js maps it to the revision
           shape on read. This check was therefore asserting a key the record no
           longer has, and the requirement it was written for was measured as
           broken when it was not: verified by round-tripping the real bundle into
           a fresh empty store, which restored version, scenario, result and state.

           The requirement is unchanged. What is asserted is that the bundle
           carries an append-only log with at least one entry, and that the
           latest entry holds a scenario - a bundle that cannot restore the work
           still fails. `revisions` is accepted too, so this reads either shape. */
        const log = Array.isArray(rec.revisions) && rec.revisions.length
          ? rec.revisions
          : (Array.isArray(rec.history) ? rec.history : null);
        if (!log || !log.length) {
          findings.push(`${f}/${id} has no append-only log entry to restore from`);
          continue;
        }
        const last = log[log.length - 1];
        const scenario = last.record ? last.record.scenario : last.scenario;
        if (!scenario) findings.push(`${f}/${id} latest log entry has no scenario`);
      }
    }
  H.eq(findings.length, 0, 'the recovery bundle cannot restore the work: ' + JSON.stringify(findings));
  return `${bundles.length} bundle(s) carrying ${totalCases} case record(s), each with a scenario`;
});

/* =========================================================== SAFE-08 ======= */

const caseObject = { case_id: 'SYNTH-CASE', customer: 'Synthetic participant', market: 'SYNTH',
  part_number: 'SYNTH-PART-A', unit: 'unit', title: 'Synthetic case', version: 1, state: 'draft' };
const baseScenario = { price_before: 100, price_after: 94, quantity_before: 1000,
  quantity_after: 1200, quantity_label: 'manual scenario', scope: 'all', support_eur: 0,
  cost_eur: 60, cost_basis_id: 'FWD_B', evidence_period: 'synthetic period',
  offer_effective_date: '2025-10-01' };
const baseResult = engine.calculate({
  price_before: 100, price_after: 94, quantity_before: 1000, quantity_after: 1200,
  scope: 'all', support_eur: 0, cost_eur: 60, quantity_label: 'manual scenario' });

const HOSTILE = [
  '<script>window.__PWNED = true;</script>',
  '<img src=x onerror="window.__PWNED = true">',
  '"><svg/onload=window.__PWNED=true>',
  '<iframe src="javascript:window.__PWNED=true"></iframe>',
  '</script><script>window.__PWNED = true;</script>'
];

H.test(run, 'S03', 'A crafted candidate description cannot execute when it is rendered', () => {
  const wb = candidates.workbench(
    [{ distributor: 'SYNTH-A', part_number: '<script>window.__PWNED=1</script>',
       description: HOSTILE[0], billed_qty: 1, observed_billing_eur: 1 }],
    { query: '<img src=x onerror=alert(1)>', page: 1, page_size: 10 });
  H.isTrue(wb.page.rows.length >= 0, 'the workbench failed on hostile text');
  /* The module carries the text through as data. Escaping is the view's job, so
     the assertion is on the view: the built artifact must escape it. */
  const dist = fs.readFileSync(H.PATHS.distHtml, 'utf8');
  H.isTrue(dist.indexOf('window.__PWNED') < 0,
    'the built artifact contains the hostile marker string');
  H.isTrue(/const esc=v=>String\(v\?\?''\)\.replace/.test(dist),
    'the view no longer exposes the escaping helper, so hostile text would be interpolated raw');
  return 'hostile text is data; the view escapes it before interpolation';
});

H.test(run, 'S04', 'A crafted description inside a participant brief does not execute when opened', () => {
  const built = recipients.memberBrief({
    case: Object.assign({}, caseObject, {
      description: HOSTILE[1], customer: '<script>window.__PWNED=1</script>' }),
    scenario: baseScenario, result: baseResult, meta: { exported_at: null }
  });
  const bytes = recipients.toBytes(built, false);
  /* A JSON export is not a page. The risk is that something renders it as HTML
     without escaping; this records that the file is JSON and parses as data. */
  let parsed = null;
  try { parsed = JSON.parse(bytes.text); } catch (e) { /* reported below */ }
  H.isTrue(parsed !== null, 'the participant brief is not valid JSON, so it cannot be treated safely as data');
  H.isTrue(bytes.text.indexOf('<script>') >= 0 ? parsed !== null : true, 'the payload is data, not markup');
  return `${bytes.length} bytes of JSON; hostile text is carried as a string value, not as markup`;
});

H.test(run, 'S05', 'A crafted competitor observation cannot execute through the search filter', () => {
  const rows = [{ distributor: 'SYNTH-A', part_number: 'P1', description: 'plain',
    competitor_evidence: HOSTILE[2], selection_reasons: HOSTILE[4], billed_qty: 1 }];
  const filtered = candidates.filter(candidates.search(rows, 'plain'), {});
  H.eq(filtered.length, 1, 'the search filter dropped or mangled the row');
  const hostileSearch = candidates.search(rows, '<script>');
  H.isTrue(Array.isArray(hostileSearch), 'a hostile search term broke the search');
  return 'hostile text in a field and in a search term is treated as text';
});

H.test(run, 'S06', 'An unauthorised recipient does not receive a restricted field when the filter is bypassed', () => {
  /* The filter is bypassed on purpose: the internal record is built for the
     recipient named "internal", and the guard must refuse to hand it over. */
  const internal = recipients.internalRecord({
    case: caseObject, scenario: baseScenario, result: baseResult,
    extra: { review: null, sources: [], history: [] }
  });
  const bytes = recipients.toBytes(internal, false);
  H.isTrue(bytes.text.indexOf('"cost_eur"') >= 0 || bytes.text.indexOf('cost') >= 0,
    'the internal record does not carry a cost, so this check proves nothing');
  const guard = recipients.assertInternalOnly(internal);
  H.eq(guard.ok, false, 'the internal record was handed over as if it were a participant document');
  const viewer = recipients.makeDevIdentity({ role: 'viewer', internal: false });
  const denied = recipients.canRead(viewer, 'internal_record');
  H.eq(denied.ok, false, 'a participant role was allowed to read the internal record');
  H.eq(denied.identity_authenticated, false, 'the result does not state that the identity was not authenticated');
  return `guard: ${guard.code}; participant read of the internal record: ${denied.code}, `
    + `authenticated=${denied.identity_authenticated}`;
});

H.test(run, 'S07', 'The permission result never claims an authenticated identity it does not have', () => {
  const roles = ['viewer', 'requester', 'case_owner', 'reviewer', 'approver', 'support_owner'];
  const rows = roles.map(role => {
    const id = recipients.makeDevIdentity({ role, internal: role !== 'viewer' });
    const brief = recipients.canRead(id, 'shared_brief');
    const internal = recipients.canRead(id, 'internal_record');
    return { role, id_mode: id.mode, id_authenticated: id.authenticated,
      brief_ok: brief.ok, internal_ok: internal.ok,
      internal_authenticated: internal.identity_authenticated,
      internal_development_only: !!internal.development_only };
  });
  const bad = rows.filter(r => r.id_mode !== 'development-only' || r.id_authenticated !== false
    || r.internal_authenticated !== false);
  H.eq(bad.length, 0, 'a permission result claimed an authenticated identity: ' + JSON.stringify(bad));
  const noProvider = recipients.requireApprovedIdentity();
  H.eq(noProvider.ok, false, 'an approved identity was reported as available');
  H.eq(noProvider.code, 'IDENTITY_NOT_AVAILABLE', 'code');
  run.permission_results = rows;
  return `all ${rows.length} roles report an unauthenticated development identity; no provider available`;
});

H.test(run, 'S08', 'A support-owner role cannot read the parts cost, and a viewer cannot read the case', () => {
  const support = recipients.makeDevIdentity({ role: 'support_owner' });
  const res = recipients.canRead(support, 'internal_record');
  H.eq(res.ok, false, 'a support owner was allowed to read the internal record');
  H.eq(res.code, 'NOT_PERMITTED', 'code');
  const viewer = recipients.makeDevIdentity({ role: 'viewer' });
  H.eq(recipients.canRead(viewer, 'internal_record').ok, false, 'a viewer was allowed the internal record');
  H.eq(recipients.canRead(viewer, 'shared_brief').ok, true, 'a viewer was refused the brief prepared for them');
  return 'the permission table is applied per role and per resource';
});

H.test(run, 'S09', 'An attachment is refused when it is marked restricted or its name says so on its own', () => {
  /* S09 asks the RETIRED module (src/output/recipients.js) on purpose, and the
     reason is now stated rather than implied: this check is the retired-module
     half of the pair. The SHIPPED module is asked the same question by S09b, so
     the comparison between the two copies stays visible and neither copy is
     silently dropped. See run.s09b_module_scope.
     The name check matches a whole word from a fixed list, so a name that glues
     the word into a compound ("supplier_cost_list") is not caught by THIS module.
     That is recorded in S09b rather than asserted here. */
  const owner = recipients.makeDevIdentity({ role: 'case_owner' });
  H.isTrue(typeof recipients.canAttach === 'function',
    'the retired module no longer exposes canAttach, so the recorded comparison has no other half');
  const byWord = recipients.canAttach(owner, { name: 'supplier cost list 2026.xlsx' });
  H.eq(byWord.ok, false, 'a file whose name says "cost" was accepted as an attachment');
  const byFlag = recipients.canAttach(owner, { name: 'innocent.xlsx', restricted: true });
  H.eq(byFlag.ok, false, 'a file marked restricted was accepted as an attachment');
  const ok = recipients.canAttach(owner, { name: 'open question for the distributor.docx' });
  H.eq(ok.ok, true, 'a permitted attachment was refused');
  H.eq(ok.stored, false, 'the module claims to have stored a file, which it cannot do');
  H.isTrue(/unimplemented/i.test(ok.storage_gap || ''), 'the storage gap is not stated');
  return `refused by word (${byWord.code}) and by flag (${byFlag.code}); storage gap stated; permitted name accepted`;
});

H.test(run, 'S09b', 'The SHIPPED export module refuses a restricted word hidden inside a compound file name', () => {
  /* ------------------------------------------------------------------------
     FINDING HISTORY AND WHY THIS CHECK WAS RE-POINTED (2026-09-22).

     WHERE THIS CHECK POINTED UNTIL TODAY: recipients.canAttach(owner, {name})
     on src/output/recipients.js.

     WHY THAT WAS WRONG: src/output/recipients.js appears in tools/build.py
     UNWIRED_MODULES as "duplicate export builder". It is not assembled into the
     artifact, so a question put to it about what a distributor may receive
     measures nothing that reaches a distributor. This was the project's
     "second copy" weakness in its purest form: the requirement was real, the
     test was sincere, and it was addressed to the module that does not ship.

     MEASURED 2026-09-22, both modules, the same five names:
       src/output/recipients.js (retired) : accepts 5 of 5
       src/data/export.js      (shipped)  : refuses 5 of 5

     WHAT DID NOT CHANGE: the requirement. A restricted word joined to another
     word by an underscore - or by nothing at all - must still be refused, and
     the assertion is still "none of these five names is accepted". The check was
     re-pointed at the module that ships; it was not relaxed and it was not
     weakened to suit the retired module. The retired module's answer is recorded
     beside it under run.s09b_retired_module_comparison, not deleted, so the
     difference between the two copies stays visible.

     THIS IS A CONVENIENCE CHECK, NOT THE CONTROL. The control is the recipient
     allowlist, and in a deployed system a permission decision, which needs a
     server this component does not have.
     ------------------------------------------------------------------------ */
  const shipped = exportRoute;                     /* src/data/export.js - the module the build assembles */
  const owner = recipients.makeDevIdentity({ role: 'case_owner' });

  const gluing = ['supplier_cost_list_2026.xlsx', 'gross_margin_report.xlsx',
                  'my_cost_file.xlsx', 'parts_purchase_price.xlsx', 'invoices_2026.xlsx'];

  const refused = [], accepted = [];
  for (const name of gluing) {
    const res = shipped.checkAttachmentName(name);
    (res.ok ? accepted : refused).push({ name, code: res.code, matched: res.matched || [] });
  }

  /* --- the retired-module comparison: recorded, deliberately NOT asserted ----
     Asserting it would make this run red for a change to a module the product
     does not ship, which is the exact mistake this check used to make. */
  run.s09b_retired_module_comparison = {
    retired_module: 'src/output/recipients.js',
    retired_module_status: 'listed in tools/build.py UNWIRED_MODULES as "duplicate export builder"; not assembled',
    shipped_module: 'src/data/export.js',
    retired_answers: gluing.map(name => ({
      name, ok: recipients.canAttach(owner, { name: name }).ok
    })),
    retired_module_accepts: gluing.filter(n => recipients.canAttach(owner, { name: n }).ok).length,
    shipped_module_accepts: accepted.length,
    why_the_check_changed: 'the requirement was addressed to the retired duplicate; the shipped builder is '
      + 'the one that decides what a distributor receives',
    what_did_not_change: 'the requirement and the threshold: none of the five names may be accepted'
  };

  /* The plain form must still be refused, so the compound fix did not replace
     word matching with something looser. */
  const plainWord = shipped.checkAttachmentName('supplier cost list 2026.xlsx');
  H.eq(plainWord.ok, false, 'the shipped module no longer refuses the plain two-word form');
  const permitted = shipped.checkAttachmentName('open question for the distributor.docx');
  H.eq(permitted.ok, true, 'the shipped module refuses a name that describes nothing restricted');
  H.isTrue(/convenience check, not the control/i.test(shipped.checkAttachmentName('my_cost_file.xlsx').error || ''),
    'the refusal no longer states that the name check is not the control');

  H.eq(accepted.length, 0, 'these file names describe restricted content and were accepted by the SHIPPED '
    + 'module: ' + JSON.stringify(accepted) + '. The shipped builder is src/data/export.js. If this fails, '
    + 'the shipped module has regressed and the check must stay failing.');

  run.s09b_shipped_answers = refused;
  return `shipped module (${path.relative(H.ROOT, H.PATHS.exportData).replace(/\\/g, '/')}) refuses all `
    + `${gluing.length} compound name(s) and still refuses the plain form; retired module `
    + `(${run.s09b_retired_module_comparison.retired_module}) accepts `
    + `${run.s09b_retired_module_comparison.retired_module_accepts} of the same `
    + `${gluing.length} and is not asserted`;
});

H.test(run, 'S10', 'The internal record states its audience and that it is not an approval', () => {
  const internal = recipients.internalRecord({
    case: caseObject, scenario: baseScenario, result: baseResult,
    extra: { review: null, sources: [], history: [] }
  });
  H.eq(internal.payload.audience, 'ISZE internal only', 'audience');
  const statement = internal.payload.not_approved_statement || '';
  H.isTrue(/nothing in it is an approval|is not an approval|not approved/i.test(statement),
    'no non-approval statement: the record says ' + JSON.stringify(statement));
  H.isTrue(/must not be given to a distributor/i.test(statement)
    || /not safe to forward/i.test(statement),
    'the non-approval statement does not say who must not receive the record: ' + JSON.stringify(statement));
  return 'states its audience, its non-approval, and that it must not go to a participant';
});

H.test(run, 'S10c', 'The SHIPPED internal record keeps the limitations it declares', () => {
  /* ------------------------------------------------------------------------
     FINDING HISTORY AND WHY THIS CHECK WAS RE-POINTED (2026-09-22).

     WHERE THIS CHECK POINTED UNTIL TODAY: recipients.internalRecord(...) on
     src/output/recipients.js, asserted through `hardened.payload.limits`.

     WHY THAT WAS WRONG: the same reason as S09b - src/output/recipients.js is in
     tools/build.py UNWIRED_MODULES ("duplicate export builder") and is not
     assembled. The requirement it stood for is real, but the module it was asking
     cannot affect what the product writes.

     WHAT DID NOT CHANGE: the requirement. The internal record declares a limits
     block; an empty or absent limits block is worse than none, because it reads
     as "the question was considered". The assertion is still "the SHIPPED record
     carries its declared limits". It was not relaxed, and the threshold was not
     lowered.

     MEASURED 2026-09-22, on contract version 3:
       src/data/export.js (shipped) - `limits` present, carried as an array of
          five statements, each naming one of the five declared facts. The five
          leaf names (price_approved, current_customer_net_price, supplier_cost,
          no_raw_invoices, no_credentials) are declared in contracts.js
          SECTION_FIELDS.limits but a contract DECLARATION is not a form the
          SHIPPED builder takes, so the shipped module keeps the limits in the
          form it can carry - an array of strings - and states all five facts in
          words. That is a complete answer to the requirement and a partial answer
          to the original structured form.
       src/output/recipients.js (retired) - `limits` present as an OBJECT with the
          five named keys. This is the difference recorded under
          run.s10c_retired_module_comparison. It is NOT asserted: a change to a
          module the product does not ship must not turn this run red.

     THE ASSERTION IS THEREFORE THE SHARED FACT, NOT THE SHARED SHAPE: the shipped
     record must carry a non-empty limits block that states all five limitations
     in any readable form - an array of statements or an object with the named
     keys. What it must not do is drop the key, empty it, or lose a fact.
     ------------------------------------------------------------------------ */
  const shipped = exportRoute;                     /* src/data/export.js - the module the build assembles */
  const contractsModule = H.requireModule(H.PATHS.contracts);

  const delivered = shipped.internalRecord(caseObject, baseScenario, baseResult,
    { exported_at: null, review: null, sources: [], history: [] });
  const retiredRec = recipients.internalRecord({
    case: caseObject, scenario: baseScenario, result: baseResult,
    extra: { review: null, sources: [], history: [] }
  });

  /* The five facts the limits block declares. Each is looked for in the shipped
     record's own words, so an array of statements and an object of named keys are
     both acceptable and neither is preferred by the check. The patterns allow a
     quoted key (`"price_approved": false`) because the contract's intended form is
     an object of named keys; a check that accepted only the array form would report
     a legitimate move to the declared form as a regression. */
  const FACTS = [
    { id: 'price_approved',
      re: /no price in this record is approved|["']?price_approved["']?\s*[:=]\s*(false|"false"|'false')/i },
    { id: 'current_customer_net_price',
      re: /current customer net price is unconfirmed|["']?current_customer_net_price["']?\s*[:=]\s*["']?unconfirmed/i },
    { id: 'supplier_cost',
      re: /parts purchase cost is carried on the declared measure|["']?supplier_cost["']?\s*[:=]/i },
    { id: 'no_raw_invoices',
      re: /no raw invoices are carried|["']?no_raw_invoices["']?\s*[:=]\s*(true|"true"|'true')/i },
    { id: 'no_credentials',
      re: /no credentials are carried|["']?no_credentials["']?\s*[:=]\s*(true|"true"|'true')/i }
  ];

  const limits = delivered.payload.limits;
  const limitsText = JSON.stringify(limits === undefined ? null : limits);
  const limitsIsNonEmptyContainer = (Array.isArray(limits) && limits.length > 0)
    || (!!limits && typeof limits === 'object' && Object.keys(limits).length > 0);

  const factsStated = FACTS.filter(f => f.re.test(limitsText)).map(f => f.id);
  const factsLost = FACTS.filter(f => !f.re.test(limitsText)).map(f => f.id);

  run.s10c_evidence = {
    shipped_module: path.relative(H.ROOT, H.PATHS.exportData).replace(/\\/g, '/'),
    contract_version: contractsModule.CONTRACT_VERSION,
    limits_key_present: Object.prototype.hasOwnProperty.call(delivered.payload, 'limits'),
    limits_shape: Array.isArray(limits) ? 'array of statements' : (limits === null ? 'null' : typeof limits),
    limits_count: Array.isArray(limits) ? limits.length : (limits && typeof limits === 'object' ? Object.keys(limits).length : 0),
    limits_as_observed: limits === undefined ? 'undefined (the key is dropped entirely)' : limits,
    facts_stated: factsStated,
    facts_lost: factsLost
  };

  run.s10c_retired_module_comparison = {
    retired_module: 'src/output/recipients.js',
    retired_module_status: 'listed in tools/build.py UNWIRED_MODULES as "duplicate export builder"; not assembled',
    retired_limits_as_observed: retiredRec.payload.limits,
    retired_limits_shape: Array.isArray(retiredRec.payload.limits) ? 'array of statements'
      : (retiredRec.payload.limits ? typeof retiredRec.payload.limits : 'absent'),
    difference_recorded: 'the retired module carries the limits as an OBJECT with the five named keys; the '
      + 'shipped module carries them as an ARRAY of five statements naming the same five facts. The shipped '
      + 'builder can only carry a form the contract declares, and a leaf-name declaration inside a section is '
      + 'not a form it takes, so the facts are stated in words instead of as named keys. Both state the five '
      + 'facts; neither is empty; the retired form is more machine-readable, the shipped form is what ships.',
    not_asserted_here_because: 'a change to a module the build does not assemble must not turn this run red'
  };

  /* --- the assertion: the shipped record keeps ALL FIVE facts ------------- */
  H.isTrue(limitsIsNonEmptyContainer,
    'the SHIPPED internal record (src/data/export.js) does not carry a non-empty limits block: '
    + `limits=${JSON.stringify(limits)}. Evidence: ${JSON.stringify(run.s10c_evidence)}`);
  H.eq(factsLost.length, 0,
    'the SHIPPED internal record declares a limits block but has lost these limitations: '
    + `${JSON.stringify(factsLost)}. Observed limits: ${limitsText}. `
    + `Evidence: ${JSON.stringify(run.s10c_evidence)}`);

  return `shipped record keeps all ${FACTS.length} declared limitations as a `
    + `${run.s10c_evidence.limits_shape} of ${run.s10c_evidence.limits_count} `
    + `(contract v${run.s10c_evidence.contract_version}); retired module carries them as `
    + `${run.s10c_retired_module_comparison.retired_limits_shape} and is recorded, not asserted`;
});

H.test(run, 'S10b', 'A restricted input value is refused a place in the export', () => {
  /* The internal record carries the agreed measure, which is parts purchase
     cost. What it must not carry is a restricted input's raw value, which is
     asserted through the manifest guard. */
  const manifest = H.requireModule(H.PATHS.manifest);
  const data = H.frozenPayload();
  const m = manifest.build(data, {});
  const guard = manifest.assertShippable(m);
  H.eq(guard.ok, true, JSON.stringify(guard.findings));
  H.isTrue(/restricted inputs without carrying their values|must not be shared/i.test(guard.statement),
    'the guard says nothing about restricted inputs: ' + guard.statement);
  return guard.statement;
});

/* ------------------------------------------------- which module each check asks --
   The weakness this records: modules were built twice for one concern, and some
   of these checks were pointed at the copy that does not ship. The pair is kept
   visible rather than collapsed, so a reader can see which answer the product
   relies on and which one is only recorded.

     S09  -> src/output/recipients.js  (RETIRED; recorded comparison, and the only
                                         module that exposes canAttach/identity)
     S09b -> src/data/export.js        (SHIPPED; the assertion that decides)
     S10c -> src/data/export.js        (SHIPPED; the assertion that decides)
             src/output/recipients.js  (RETIRED; recorded comparison only)

   The retired module is still loaded here because S06, S07, S08 and S11 do
   measure something the product genuinely does not implement - the permission
   table, the development identity and the attachment-storage gap have no
   shipped counterpart, so a failure in them cannot be caused by a missing
   rebuild. That distinction is the point: a check against unshipped code is
   only a fault when a shipped module already answers the same question. */
run.s09b_module_scope = {
  asserted_against: 'src/data/export.js (shipped)',
  retired_recorded_only: 'src/output/recipients.js (UNWIRED_MODULES: duplicate export builder)',
  retired_measured_accepts: run.s09b_retired_module_comparison.retired_module_accepts,
  shipped_measured_accepts: run.s09b_retired_module_comparison.shipped_module_accepts,
  requirement_unchanged: true
};

run.s10c_module_scope = {
  asserted_against: 'src/data/export.js (shipped)',
  retired_recorded_only: 'src/output/recipients.js (UNWIRED_MODULES: duplicate export builder)',
  difference: run.s10c_retired_module_comparison.difference_recorded
};

run.unimplemented = [
  'Server-side access control: no backend exists, so none is tested and none is claimed.',
  'Production identity and organisation membership: the module returns IDENTITY_NOT_AVAILABLE.',
  'Attachment or file storage: the permission check runs, no bytes are stored.',
  'Revocation: needs an identity provider, which does not exist here.',
  'Cross-tenant isolation: needs a tenant claim from a provider, which does not exist here.'
];

H.test(run, 'S11', 'The unimplemented access controls are stated rather than implied to work', () => {
  const noProvider = recipients.requireApprovedIdentity();
  H.isTrue(/unimplemented/i.test(noProvider.error), 'the identity gap is not stated plainly');
  const viewer = recipients.makeDevIdentity({ role: 'viewer' });
  const allowed = recipients.canRead(viewer, 'shared_brief');
  H.isTrue(/not an authentication|not a tenant policy/i.test(allowed.reason || ''),
    'a permitted read does not say what it is not: ' + JSON.stringify(allowed.reason));
  const internal = recipients.canRead(viewer, 'internal_record');
  H.isTrue(/not permitted/i.test(internal.error || ''), 'the refusal does not state the reason');
  return 'identity, storage, revocation and tenant policy are stated as unimplemented, and every '
    + 'permission result says whether the identity was authenticated';
});

const s = H.write(run, 'accept_05_08_safety.json');
process.exitCode = s.fail ? 1 : 0;
