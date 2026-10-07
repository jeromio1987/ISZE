#!/usr/bin/env node
'use strict';
/* ===========================================================================
   ACCEPT-04 + SAFE-05 - the participant-facing output, judged on the bytes.

   A UI label is not evidence. This check reads the files that the product's own
   download route actually wrote (saved by ACCEPT-02), parses them, and inspects
   their structure and their text.

   It also runs the same questions against the module directly, so a route that
   writes nothing still gets judged, and it uses sentinel values so that a
   "restricted value survived" finding cannot be a coincidence.

   Restricted, for the purposes of this check:
     parts purchase cost, gross profit, gross margin, supplier discount,
     FX rate, another participant's records.
   =========================================================================== */
const H = require('./lib/harness.cjs');
const fs = require('node:fs');
const path = require('node:path');

const data = H.frozenPayload();
const engine = H.requireModule(H.PATHS.engine);
const exportRoute = H.requireModule(H.PATHS.exportData);       /* the module the UI uses */
// RETIRED-MODULE-USE: src/output/recipients.js - it is the only module that exposes the
// permission table, the development identity and the attachment-storage gap (S06-S08,
// S11 in SAFE-05/08), for which no shipped counterpart exists. The participant-brief
// and limits questions (D06, D10, D13, S09b, S10c) are asserted against
// src/data/export.js, the module tools/build.py assembles; this load keeps the
// retired module's answer available as a recorded comparison rather than deleting it.
const recipients = H.requireModule(H.PATHS.recipients);        /* the newer hardened module */

const run = H.makeRun('ACCEPT-04', 'Participant-facing output: no restricted field survives',
  ['Judged on actual exported bytes and on the module, not on UI labels.',
   'Sentinels are synthetic values, so a leak finding cannot be coincidence.']);
run.tested_files = H.pin([H.PATHS.exportData, H.PATHS.recipients, H.PATHS.contracts,
  H.PATHS.engine, H.PATHS.distHtml, H.PATHS.distReport, H.PATHS.frozen]);

/* The build assembles these modules; the UI's globals are bound to them. */
run.build_module_list = (() => {
  try {
    const r = JSON.parse(fs.readFileSync(H.PATHS.distReport, 'utf8'));
    return r.modules || null;
  } catch (e) { return null; }
})();
run.recipients_module_is_shipped = !!(run.build_module_list || [])
  .some(m => /output\/recipients\.js$/.test(m));
run.export_module_is_shipped = !!(run.build_module_list || [])
  .some(m => /data\/export\.js$/.test(m));

/* ------------------------------------------------------ real exported bytes */

const EXPORT_DIR = path.join(H.OUT, 'exports');
const RESTRICTED_KEYS = ['cost', 'cost_eur', 'cost_is_zero', 'cost_basis_id',
  'cost_missing_not_zero', 'cost_basis_source', 'cost_records', 'costrecord',
  'gp_before', 'gp_after', 'gp_change', 'gp_pct',
  'margin_before_pct', 'margin_after_pct', 'margin_unit_after_pct', 'margin_pp_change',
  'source_discount', 'jpy_per_eur', 'fx_rate', 'fob_eur', 'verifiedcosts',
  'cost_bases', 'list_eur', 'markup', 'all_bases', 'rate_window'];

function walkKeys(node, path, out) {
  if (Array.isArray(node)) { node.forEach((v, i) => walkKeys(v, `${path}[${i}]`, out)); return out; }
  if (node && typeof node === 'object') {
    Object.keys(node).forEach(k => { out.push({ key: k, path: path || '.' }); walkKeys(node[k], `${path}.${k}`, out); });
    return out;
  }
  return out;
}

function restrictedKeysPresent(obj) {
  return walkKeys(obj, '', []).filter(k => RESTRICTED_KEYS.indexOf(k.key.toLowerCase()) >= 0);
}

const shipped = fs.existsSync(EXPORT_DIR)
  ? fs.readdirSync(EXPORT_DIR).filter(f => f.endsWith('.out')) : [];
run.exported_files = { dir: EXPORT_DIR, count: shipped.length, names: shipped };

H.test(run, 'D01', 'The product\'s own participant download carries no restricted field, at any depth', () => {
  H.isTrue(shipped.filter(f => f.endsWith('participant_brief.out')).length > 0,
    'no participant brief was produced by the product download route, so nothing was judged. '
    + 'Run tests/accept/accept_02_journey.py first.');
  const findings = [];
  let checked = 0;
  for (const f of shipped.filter(x => x.endsWith('participant_brief.out'))) {
    const raw = fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8');
    let parsed;
    try { parsed = JSON.parse(raw); }
    catch (e) { findings.push(`${f} is not JSON: ${e.message}`); continue; }
    checked += 1;
    restrictedKeysPresent(parsed).forEach(hit =>
      findings.push(`${f} carries key "${hit.key}" at ${hit.path}`));
  }
  H.eq(findings.length, 0, 'restricted keys in a participant brief: ' + JSON.stringify(findings));
  return `${checked} participant brief(s) written by the download route, no restricted key at any depth`;
});

H.test(run, 'D02', 'The internal record does carry them, so the participant check is not vacuous', () => {
  const files = shipped.filter(x => x.endsWith('internal_record.out'));
  H.isTrue(files.length > 0, 'no internal record was produced by the download route');
  const found = {};
  for (const f of files) {
    const parsed = JSON.parse(fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8'));
    found[f] = restrictedKeysPresent(parsed).map(h => h.key);
  }
  const anyPresent = Object.values(found).some(list => list.length > 0);
  H.isTrue(anyPresent, 'the internal record carries no restricted key either, so D01 proves nothing: '
    + JSON.stringify(found));
  const sample = Object.values(found).find(l => l.length);
  return `the internal record carries ${sample.length} restricted key(s), e.g. ${[...new Set(sample)].slice(0, 6).join(', ')}`;
});

H.test(run, 'D03', 'A participant brief carries no other participant\'s records', () => {
  /* SUPERSEDED COMPARISON, kept and recorded rather than deleted.

     The original comparison flagged a brief whenever it contained ANY other
     case's customer name, without asking whether that name was the brief's own
     customer. It therefore fired for every pair of cases that share a customer:
     five cases, two customers, so eight hits - and all eight were a brief of
     ITUK containing "ITUK", or a brief of I Motors containing "I Motors".
     "ITUK-DISCS contains the customer of ITUK-PADS" is true and harmless: both
     are ITUK. Reproduced 2026-09-22: no other case's id and no other case's part
     number appears in any brief; only the shared customer name did.

     A check that cannot tell a repeated customer from a leaked participant does
     not measure disclosure. Left as it was, it would either block a legitimate
     release or teach a reader to ignore it, so the detection is corrected and
     the original result is recorded beside it under
     run.d03_superseded_comparison.

     What is still asserted, unchanged in intent: a brief must not carry another
     case's id, another case's part number, or a customer that belongs to a
     different participant. The assertion was not relaxed; the comparison was
     made specific. */
  const briefs = shipped.filter(x => x.endsWith('participant_brief.out'));
  H.isTrue(briefs.length > 0, 'no participant brief to check');
  const others = {};
  data.cases.forEach(c => { others[c.id] = { customer: c.customer, pn: c.pn, name: c.name }; });
  const customersOf = id => String((others[id] || {}).customer || '').trim();

  /* --- the original comparison, reproduced and recorded, not asserted ------- */
  const originalFindings = [];
  for (const f of briefs) {
    const raw = fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8');
    const own = Object.keys(others).find(id => f.startsWith(id));
    for (const [id, rec] of Object.entries(others)) {
      if (id === own) continue;
      if (rec.customer && raw.indexOf(rec.customer) >= 0) {
        originalFindings.push(`${f} contains the customer of ${id}`);
      }
      if (rec.pn && raw.indexOf(rec.pn) >= 0) originalFindings.push(`${f} contains the part number of ${id}`);
    }
  }
  run.d03_superseded_comparison = {
    original_rule: 'a brief carries another case\'s customer, part number or case id (customer name matched with no test of whose customer it is)',
    original_findings_count: originalFindings.length,
    original_findings: originalFindings,
    why_superseded: 'the customer name repeats legitimately; five cases share two customers, so every pair '
      + 'of cases sharing a customer produced a hit. None of the hits was a disclosure.',
    replacement_rule: 'a brief carries another case\'s id, another case\'s part number, or a customer that '
      + 'belongs to a different participant'
  };

  /* --- the corrected detection, which is what D03 now asserts --------------- */
  const findings = [];
  for (const f of briefs) {
    const raw = fs.readFileSync(path.join(EXPORT_DIR, f), 'utf8');
    const own = Object.keys(others).find(id => f.startsWith(id));
    const ownCustomer = customersOf(own);
    H.isTrue(!!own, `${f} does not name a case in the payload, so the brief cannot be attributed to a participant`);
    for (const [id, rec] of Object.entries(others)) {
      if (id === own) continue;
      /* A case id is a participant identifier, not a word in a sentence. */
      if (raw.indexOf(id) >= 0) {
        findings.push(`${f} contains the case id of ${id}`);
      }
      if (rec.pn && raw.indexOf(rec.pn) >= 0) {
        findings.push(`${f} contains the part number of ${id}`);
      }
      /* A customer name is only a disclosure when it is a DIFFERENT customer.
         The same customer on two cases is one participant with two decisions. */
      const sharedCustomer = rec.customer && String(rec.customer).trim() === ownCustomer;
      if (rec.customer && raw.indexOf(rec.customer) >= 0 && !sharedCustomer) {
        findings.push(`${f} (customer ${JSON.stringify(ownCustomer)}) contains the customer `
          + `${JSON.stringify(rec.customer)} of ${id}`);
      }
    }
  }
  H.eq(findings.length, 0, 'cross-participant content: ' + JSON.stringify(findings));
  const distinctCustomers = [...new Set(Object.keys(others).map(customersOf))];
  return `${briefs.length} brief(s) checked for another case's id, another case's part number and a `
    + `distinct customer (own customer excluded). ${Object.keys(others).length} case(s), `
    + `${distinctCustomers.length} distinct customer(s). Superseded comparison would have reported `
    + `${originalFindings.length} hit(s); all were the brief's own customer.`;
});

/* -------------------------------------------------------- module level ---- */

const SENTINEL_COST = 987654.4321;
const SENTINEL_FX = 123456.7891;
const SENTINEL_NOTE = 'Please confirm. Our parts cost of 987654.4321 EUR and the gross margin of 41.7% '
  + 'cannot be shared, and the FX rate of 123456.7891 applies.';

const caseObject = {
  case_id: 'SYNTH-CASE', customer: 'Synthetic participant', market: 'SYNTH',
  part_number: 'SYNTH-PART-A', unit: 'unit', title: 'Synthetic case', version: 1, state: 'draft'
};
const scenario = {
  price_before: 100, price_after: 94, quantity_before: 1000, quantity_after: 1200,
  quantity_label: 'manual scenario', scope: 'all', support_eur: 500,
  cost_eur: SENTINEL_COST, cost_basis_id: 'FWD_B', jpy_per_eur: SENTINEL_FX,
  evidence_period: 'synthetic period', offer_effective_date: '2025-10-01',
  sources: [{ reference_id: 'S1', title: 'synthetic' }],
  nested: { deeper: { cost_eur: SENTINEL_COST, gp_change: SENTINEL_COST } }
};
const result = engine.calculate({
  price_before: 100, price_after: 94, quantity_before: 1000, quantity_after: 1200,
  scope: 'all', support_eur: 500, cost_eur: SENTINEL_COST, quantity_label: 'manual scenario'
});

H.test(run, 'D04', 'A nested restricted object set is not carried into a participant brief', () => {
  const built = exportRoute.memberBrief(caseObject, scenario, result, { exported_at: null });
  const bytes = exportRoute.toBytes(built, false);
  const hits = restrictedKeysPresent(built.payload);
  H.eq(hits.length, 0, 'restricted keys survived in the participant payload: ' + JSON.stringify(hits));
  H.isTrue(bytes.text.indexOf(String(SENTINEL_COST)) < 0,
    'the sentinel cost value is present in the participant bytes');
  H.isTrue(bytes.text.indexOf(String(SENTINEL_FX)) < 0,
    'the sentinel FX value is present in the participant bytes');
  return `${bytes.length} bytes, no restricted key, neither sentinel value present`;
});

H.test(run, 'D05', 'The same nested object is present in the internal record, so D04 is not vacuous', () => {
  const built = exportRoute.internalRecord(caseObject, scenario, result,
    { review: null, sources: [], history: [] });
  const bytes = exportRoute.toBytes(built, false);
  H.isTrue(bytes.text.indexOf(String(SENTINEL_COST)) >= 0, 'the sentinel cost is absent from the internal record');
  return `${bytes.length} bytes, sentinel cost and FX present as expected`;
});

H.test(run, 'D06', 'The participant brief contains the offer it is meant to communicate', () => {
  /* DEFECT (reported to the implementer, not fixed here).
     src/data/export.js is the module the built artifact uses. Its
     `allowlistFor(recipient)` adds `spec.leaf_fields` but never adds
     `spec.permits`. The brief is built out of containers named `reference`,
     `offer`, `price`, `quantity` and `customers`, so every one of them is
     treated as an undeclared key and dropped. What is left is the `limits`
     array, which is a leaf field. The file the download route writes therefore
     contains four sentences of boilerplate and no part number, no price and no
     quantity.
     The newer src/output/recipients.js adds `spec.permits` and produces the
     intended brief, but the build does not include that module.
  */
  const built = exportRoute.memberBrief(caseObject, scenario, result, { exported_at: null });
  const bytes = exportRoute.toBytes(built, false);
  const present = Object.keys(built.payload);
  const wanted = ['reference', 'offer', 'price', 'quantity'];
  const missing = wanted.filter(k => present.indexOf(k) < 0);
  H.eq(missing.length, 0,
    `the participant brief is missing ${JSON.stringify(missing)}; it contains only `
    + `${JSON.stringify(present)}. It carries no part number and no price, so the recipient cannot `
    + `read the offer from it. ${bytes.length} bytes written.`);
  return `brief carries ${JSON.stringify(present)}`;
});

H.test(run, 'D11', 'The brief\'s own content check does not pass a brief that is missing its subject', () => {
  const built = exportRoute.memberBrief(caseObject, scenario, result, { exported_at: null });
  const present = Object.keys(built.payload);
  const hasOffer = present.indexOf('offer') >= 0 && present.indexOf('price') >= 0;
  H.isTrue(!(built.audit.ok === true && !hasOffer),
    'the brief reports a clean content check while containing no offer: audit ok='
    + `${built.audit.ok}, payload keys ${JSON.stringify(present)}. The UI suppresses the download on a `
    + 'failed audit, so this brief is downloaded and the operator is told the check was clean.');
  return 'a brief with no offer is not reported as clean';
});

H.test(run, 'D12', 'The participant brief is not an empty shell for the recipient', () => {
  /* The rule this check exists for: an empty shell where data is simply absent
     is a FAIL, not a pass. */
  const built = exportRoute.memberBrief(caseObject, scenario, result, { exported_at: null });
  const offer = built.payload.offer || {};
  const price = built.payload.price || {};
  H.isTrue(offer.part_number === caseObject.part_number,
    `the brief does not state the part number (offer.part_number=${JSON.stringify(offer.part_number)})`);
  H.isTrue(price.price_before === scenario.price_before && price.price_after === scenario.price_after,
    `the brief does not state both prices (price=${JSON.stringify(price)})`);
  return 'the brief states the part and both prices';
});

H.test(run, 'D13', 'A restricted phrase typed into the note is not written to the shipped participant file', () => {
  /* Kept as its own check because it is a genuine requirement.
     RE-POINTED 2026-09-22: the assertion is on the SHIPPED module
     (src/data/export.js). The earlier wording of this check recorded that the
     route failed it "for the wrong reason" - the note was dropped along with the
     container holding it, so nothing leaked and nothing was disclosed either.
     The shipped builder now carries the containers and checks the free text, so
     the same requirement is asserted against the module the product uses.
     The retired module's answer is recorded, not asserted. */
  const noteMeta = { exported_at: null, request_note: SENTINEL_NOTE };
  const shippedRoute = exportRoute.memberBrief(caseObject, scenario, result, noteMeta);
  const shippedBytes = shippedRoute.payload === null
    ? { text: '', length: 0 } : exportRoute.toBytes(shippedRoute, false);

  const hardened = recipients.memberBrief({
    case: caseObject, scenario, result, meta: noteMeta
  });

  run.free_text_note_evidence = {
    asserted_against_module: 'src/data/export.js (shipped)',
    shipped_route_audit_ok: shippedRoute.audit.ok,
    shipped_route_refused: !!shippedRoute.refused,
    shipped_route_audit_findings: shippedRoute.audit.findings,
    shipped_route_carries_the_phrase: shippedBytes.text.indexOf('parts cost') >= 0,
    shipped_route_carries_the_cost_figure: shippedBytes.text.indexOf(String(SENTINEL_COST)) >= 0,
    retired_module: 'src/output/recipients.js',
    retired_module_reports_words: (hardened.words || {}).ok === false,
    retired_module_findings: (hardened.words || {}).findings || null
  };

  /* The requirement: the restricted phrase must not reach the file a participant
     receives. Either carrying it as a refusal or rewording it away satisfies
     that; writing it out does not. */
  H.isTrue(shippedBytes.text.indexOf('parts cost') < 0,
    'a restricted phrase typed into the note reached the SHIPPED participant file: '
    + JSON.stringify(run.free_text_note_evidence));
  H.isTrue(shippedBytes.text.indexOf(String(SENTINEL_COST)) < 0,
    'the sentinel cost figure typed into the note reached the SHIPPED participant file: '
    + JSON.stringify(run.free_text_note_evidence));
  /* And it must not have been stripped silently: a brief that quietly loses its
     note is the blacklist fault again. The refusal must be reported. */
  H.isTrue(shippedRoute.audit.ok === false || shippedRoute.refused === true,
    'the shipped builder dropped the restricted note without reporting it, so the output looks clean '
    + 'because nobody decided what belonged in it: ' + JSON.stringify(run.free_text_note_evidence));
  return `shipped builder refuses the restricted note (audit ok=${shippedRoute.audit.ok}, `
    + `refused=${!!shippedRoute.refused}) and writes no restricted phrase or figure; `
    + `retired module recorded at run.free_text_note_evidence`;
});

H.test(run, 'D07', 'The hardened participant route reports a restricted phrase rather than passing it', () => {
  const hardened = recipients.memberBrief({
    case: caseObject, scenario, result, meta: { exported_at: null, request_note: SENTINEL_NOTE }
  });
  H.eq(hardened.words.ok, false, 'the word check passed a sentence naming a parts cost and a margin');
  H.isTrue(hardened.words.findings.length > 0, 'no finding was recorded');
  return `reported ${hardened.words.findings.length} phrase(s) instead of removing them silently`;
});

H.test(run, 'D08', 'The internal record refuses to be passed off as a participant document', () => {
  const internal = recipients.internalRecord({
    case: caseObject, scenario, result, extra: { review: null, sources: [], history: [] }
  });
  const guard = recipients.assertInternalOnly(internal);
  H.eq(guard.ok, false, 'the internal record can be handed over without complaint');
  H.eq(guard.code, 'INTERNAL_ONLY', 'code');
  return guard.error.slice(0, 120) + '...';
});

H.test(run, 'D09', 'The participant brief states its own limits and that it is not an approval', () => {
  const built = exportRoute.memberBrief(caseObject, scenario, result, { exported_at: null });
  const limits = built.payload.limits;
  H.isTrue(Array.isArray(limits) && limits.length > 0, 'no limits are stated on the brief');
  const text = JSON.stringify(built.payload);
  H.isTrue(/not an approval/i.test(text), 'the brief does not say it is not an approval');
  H.isTrue(/no ISZE supplier purchase price/i.test(text), 'the brief does not state the cost exclusion');
  return `${limits.length} stated limits, including the cost exclusion and the non-approval statement`;
});

/* ------------------------------------- what the shipped artifact contains -- */

H.test(run, 'D10', 'Record which export module the shipped artifact actually uses', () => {
  /* Reported, not asserted as a pass: the build ships data/export.js and not
     output/recipients.js, so the hardened permission and word checks are not
     reachable from the product. The number is recorded so a later build can be
     compared against it. */
  const list = run.build_module_list;
  if (!list) throw new Error('the build report was not readable, so this could not be established');
  H.isTrue(list.some(m => /data\/export\.js$/.test(m)), 'the UI export module is not in the build');
  return `build ships: ${list.join(', ')} | output/recipients.js present: ${run.recipients_module_is_shipped}`;
});

const s = H.write(run, 'accept_04_participant.json');
process.exitCode = H.exitCode(s);
