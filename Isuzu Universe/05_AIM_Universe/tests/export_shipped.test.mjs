#!/usr/bin/env node
/* ===========================================================================
   The SHIPPED export module, judged as bytes - D13 / S10c / S09b / S01c.

   Run:
     node --test tests/export_shipped.test.mjs

   Exit code is 0 only when every check passes.

   Why this file exists
   --------------------
   The strongest export test in the tree (tests/export_bytes.test.mjs) loads
   src/output/recipients.js. That module is RETIRED: tools/build.py assembles
   src/data/export.js into the artifact and deliberately leaves the other one
   out. So eleven green checks there guarded code the product does not run.

   This file loads the module the build actually ships, so the same questions
   are asked of the code a person downloads from.

   What is asserted here
     X01  D13  a restricted phrase typed into the request note is REFUSED
     X02  D13  a restricted figure written as text is refused, with no
               restricted word in it (the number is the disclosure)
     X03  D13  an FX rate written into a sentence is refused
     X04  D13  a margin written into a sentence is refused
     X05  D13  the refusal is visible as a refusal, not as a crash and not as an
               empty success, and it names the offending phrase and path
     X06  D13  the refusal produces no participant payload at all, and the
               sentence is not quietly deleted instead
     X07  D13  negative control: the allowlist alone carries that sentence, so
               the word check is what stops it
     X08  D13  the brief's own limit wording is not mistaken for a disclosure
     X09  D13  a restricted phrase in internal free text is carried, because the
               internal record is where it belongs
     X09b no internal section is trimmed to an empty object or dropped whole
     X10  S10c the internal record's limits block is not empty and states each
               limitation it declares
     X11  S10c the limits block is not empty in the WRITTEN bytes either
     X12  S09b a restricted word joined to another word is refused as an
               attachment name
     X12b S09b a restricted measure written as one word with no separator too
     X13  S09b the name check does not refuse an innocent name (no false alarm)
     X14  S01c the written brief states its schema and recipient at the top level
               of the file, beside the containers
     X15  the participant brief still carries the offer it exists to communicate
     X16  the mutation proof: moving the internal parts cost from 60 to 41.75
               leaves the member brief byte-identical - a construction, not a filter
     X17  the internal record still carries the cost, so X16 is not vacuous
     X18  a planted internal-only key is caught by the audit, so the audit is not
               vacuous
     X19  the ported phrase and pattern lists are the ones in use, not a private copy
     X20  the internal record is refused as a participant document
     X21  the shipped module answers the reviewer's own SAFE-05 inputs, which are
          pointed at the retired module
     X22  the interface acts on the refusal instead of writing the file
     X23  the module works on the load path the product actually uses, not only
          under require
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const require = createRequire(import.meta.url);

/* The module the build ships. Not the retired one. */
const X = require(path.join(ROOT, 'src', 'data', 'export.js'));
const contracts = require(path.join(ROOT, 'src', 'data', 'contracts.js'));

/* ---------------------------------------------------------- synthetic data --
   Invented values only. No real part, customer, price list or supplier cost. */

const caseObject = {
  case_id: 'CASE-SYNTH-1',
  customer: 'Synthetic participant',
  market: 'SYNTH',
  part_number: 'SYNTH-PART-A',
  unit: 'unit',
  description: 'Synthetic part A',
  title: 'Synthetic offer for the synthetic account',
  version: 4,
  state: 'ready_for_review',
  owner_role: 'case_owner'
};

const scenario = {
  scenario_id: 'CASE-SYNTH-1:v2',
  version: 2,
  case_id: 'CASE-SYNTH-1',
  part_number: 'SYNTH-PART-A',
  unit: 'unit',
  price_before: 100,
  price_after: 95,
  quantity_before: 1000,
  quantity_after: 1200,
  quantity_label: 'stated commitment',
  scope: 'incremental',
  support_eur: 500,
  support_direction: 'to_participant',
  evidence_period: 'synthetic half year',
  offer_effective_date: '2026-10-01',
  /* The restricted content, in the shapes that matter. */
  cost: 60,
  cost_eur: 60,
  margin_pp_change: -3.4,
  gp_change: -260,
  gp_before: 4000,
  gp_after: 3740,
  cost_basis_id: 'FWD_B',
  cost_basis_source: 'verified record',
  sources: []
};

/* A result carrying restricted values, as the engine would produce one. */
const result = {
  ok: true,
  price_before: 100,
  price_after: 95,
  quantity_before: 1000,
  quantity_after: 1200,
  quantity_label: 'stated commitment',
  revenue_change: -50,
  gp_before: 4000,
  gp_after: 3740,
  gp_change: -260,
  margin_before_pct: 40,
  margin_after_pct: 36.6,
  margin_pp_change: -3.4,
  cost: 60,
  cost_eur: 60,
  cost_basis_id: 'FWD_B',
  support_eur: 500
};

const CLEAN_NOTE = 'Please confirm the eligibility of the additional volume.';

/* Every restricted name that must not reach a participant brief. */
const RESTRICTED_NAMES = ['cost', 'cost_eur', 'margin_pp_change', 'gp_change', 'gp_before',
  'gp_after', 'jpy_per_eur', 'fx', 'fob', 'markup', 'cost_basis', 'supplier discount'];

/* Names the brief is entitled to carry that contain one of the words above.
   Listed so the byte check is precise rather than noisy. */
const ALLOWED_NAMES_THAT_LOOK_RESTRICTED = ['support_eur'];

function textOf(exported) { return X.toBytes(exported, false).text; }

function restrictedNamesIn(exported) {
  const lower = textOf(exported).toLowerCase();
  return RESTRICTED_NAMES.filter((n) => lower.includes(n)
    && !ALLOWED_NAMES_THAT_LOOK_RESTRICTED.includes(n));
}

function briefWith(note) {
  return X.memberBrief(caseObject, scenario, result,
    { exported_at: '2026-09-22T10:00:00.000Z', request_note: note });
}

/* The review section of an internal record, in both the shape this module's own
   checks use and the shape the UI's review form writes. */
const review = {
  owner: 'case_owner',
  status: 'Ready for review',
  explanation: 'The account asked for support on the additional volume.',
  note: 'Proposed at 95 EUR against a 100 EUR list.'
};

const uiReview = {
  owner_role: 'case_owner',
  state: 'ready_for_review',
  next_update_due: '2026-10-15',
  next_action: 'Support owner to confirm the eligibility of the additional volume',
  explanation: 'The account asked for support on the additional volume.',
  note: 'Proposed at 95 EUR against a 100 EUR list.',
  outcome: ''
};

/* ------------------------------------------------------------- harness -- */

const results = [];
let failures = 0;

function check(id, name, fn) {
  try {
    const evidence = fn();
    results.push({ id, name, status: 'PASS', evidence: evidence === undefined ? '' : String(evidence) });
  } catch (e) {
    failures++;
    results.push({ id, name, status: 'FAIL', evidence: e.message });
  }
}

/* =========================================================== D13: refusal == */

check('X01', 'D13 a restricted phrase typed into the request note is refused', () => {
  const note = 'Please confirm. Our parts cost of 60 EUR per unit applies to this offer.';
  const brief = briefWith(note);

  assert.equal(brief.ok, false, 'a sentence naming a parts cost was accepted');
  assert.equal(brief.refused, true, 'the refusal is not marked as a refusal');
  assert.equal(brief.code, 'RESTRICTED_WORD_IN_FREE_TEXT', 'refusal code');
  assert.ok(brief.words.findings.some((f) => /parts cost/.test(f.phrase)),
    'the finding does not name the phrase: ' + JSON.stringify(brief.words.findings));
  assert.ok(brief.words.findings.some((f) => /\.customers\.note/.test(f.path)),
    'the finding does not name the path: ' + JSON.stringify(brief.words.findings));

  return 'refused with ' + brief.code + '; name covers: '
    + brief.words.findings.map((f) => f.phrase).join(', ');
});

check('X02', 'D13 a restricted figure written as text is refused even with no restricted field name', () => {
  /* No "cost" field is anywhere near this. The number in the sentence is the
     disclosure, which is exactly what a field allowlist cannot see. */
  const note = 'For context, what we pay our supplier is 60 EUR for this item.';
  const brief = briefWith(note);

  assert.equal(brief.ok, false, 'a sentence stating what ISZE pays was accepted');
  assert.equal(brief.code, 'RESTRICTED_WORD_IN_FREE_TEXT');
  assert.ok(brief.words.findings.some((f) => /what ISZE pays written into text/.test(f.phrase)),
    'the finding does not name what it matched: ' + JSON.stringify(brief.words.findings));

  /* And the plain form of the same disclosure. */
  const plain = briefWith('The unit cost is 60 EUR.');
  assert.equal(plain.ok, false, 'a unit cost written into a sentence was accepted');
  assert.ok(plain.words.findings.some((f) => /cost figure written into text/.test(f.phrase)),
    JSON.stringify(plain.words.findings));

  return 'refused both "what we pay our supplier is 60 EUR" and "the unit cost is 60 EUR"';
});

check('X03', 'D13 an FX rate written into a sentence is refused', () => {
  const brief = briefWith('The FX rate is 150 JPY to the EUR this quarter.');
  assert.equal(brief.ok, false, 'an FX rate written into a sentence was accepted');
  assert.equal(brief.code, 'RESTRICTED_WORD_IN_FREE_TEXT');
  assert.ok(brief.words.findings.some((f) => /FX rate/.test(f.phrase)),
    'the finding does not name the FX rate: ' + JSON.stringify(brief.words.findings));

  const pair = briefWith('Rates moved: USD/EUR 0.92 at the cut-off.');
  assert.equal(pair.ok, false, 'a currency pair written into a sentence was accepted');

  return 'refused "the FX rate is 150 JPY to the EUR" and "USD/EUR 0.92"';
});

check('X04', 'D13 a margin written into a sentence is refused', () => {
  const brief = briefWith('The gross margin on this line is 30%.');
  assert.equal(brief.ok, false, 'a gross margin written into a sentence was accepted');
  assert.ok(brief.words.findings.some((f) => /gross margin/.test(f.phrase)),
    JSON.stringify(brief.words.findings));

  const generic = briefWith('A 30% margin is not achievable here.');
  assert.equal(generic.ok, false, 'a margin figure written into a sentence was accepted');

  return 'refused both "the gross margin ... is 30%" and "a 30% margin is not achievable"';
});

check('X05', 'D13 the refusal is visible as a refusal, names the phrase and path, and does not throw', () => {
  const note = 'Our parts cost is 60 EUR and the gross margin is 30%.';
  let brief = null;
  assert.doesNotThrow(() => { brief = briefWith(note); }, 'the refusal threw instead of returning');

  assert.equal(brief.ok, false);
  assert.equal(brief.refused, true);
  assert.equal(brief.code, 'RESTRICTED_WORD_IN_FREE_TEXT');
  assert.equal(brief.payload, null, 'a refused brief still produced a payload');
  assert.ok(typeof brief.error === 'string' && brief.error.length > 40,
    'the refusal carries no explanation a UI could show');
  assert.ok(brief.error.includes('parts cost') && brief.error.includes('.customers.note'),
    'the refusal does not name the phrase and the path: ' + brief.error);
  assert.ok(/Nothing was produced/i.test(brief.error), 'the refusal does not say nothing was produced');

  /* The caller that consults only `audit` before writing a file must also see
     the refusal. `audit.ok` is what the UI already reads. */
  assert.equal(brief.audit.ok, false, 'the audit reports a clean brief for a refused one');
  assert.equal(brief.audit.refused, true);
  assert.ok(brief.audit.findings.length > 0, 'the audit records no finding');

  /* A clean brief is distinguishable from this one at every one of those keys. */
  const clean = briefWith(CLEAN_NOTE);
  assert.equal(clean.ok, true, clean.error);
  assert.equal(clean.refused, undefined);
  assert.equal(clean.audit.ok, true);

  return 'ok=false, refused=true, payload=null, code=' + brief.code
    + '; a clean brief reports ok=true and audit.ok=true';
});

check('X06', 'D13 the refusal produces no participant payload, and the sentence is not silently deleted', () => {
  const note = 'Our parts cost is 60 EUR per unit.';
  const brief = briefWith(note);

  /* Nothing is produced, and nothing that names the measure can be written. */
  assert.equal(brief.payload, null);
  const written = textOf(brief);
  assert.ok(written.indexOf('parts cost') < 0, 'a refusal wrote the restricted phrase anyway');
  assert.equal(written, 'null', 'a refusal serialised something other than null: ' + written);

  /* This is the difference between the two faults. A silent deletion would have
     produced a brief with the sentence removed and a clean audit - an output
     that looks clean because nobody decided what belonged in it. The refusal
     instead names what it found. */
  assert.ok(brief.error.indexOf('parts cost') >= 0,
    'the restriction was not reported, so it was either ignored or silently removed');

  return 'payload null, ' + written.length + ' bytes written, the phrase named in the refusal rather '
    + 'than removed from a produced brief';
});

check('X07', 'D13 negative control: the allowlist alone carries that sentence, so the word check stops it', () => {
  const note = 'Our parts cost is 60 EUR per unit.';
  const keys = X.allowlistFor('member');

  /* The allowlist carries the container and the key, because a note is a
     permitted field. This is the gap the word check exists to close. */
  const carried = X.buildAllowed({ customers: { note: note } }, keys);
  assert.equal(carried.customers.note, note,
    'the allowlist did not carry the note, so this control proves nothing');

  const words = X.checkForRestrictedWords(carried);
  assert.equal(words.ok, false, 'the word check passed a sentence the allowlist carried');
  assert.ok(words.findings.some((f) => f.path === '.customers.note'), JSON.stringify(words.findings));

  /* And the same sentence placed somewhere the allowlist would drop entirely is
     still reported by the word check, so the check is on content and not on the
     field list. */
  const outside = X.checkForRestrictedWords({ undeclared: { text: note } });
  assert.equal(outside.ok, false, 'the word check only looks at permitted fields');

  return 'the allowlist carries .customers.note unchanged; checkForRestrictedWords refuses it';
});

check('X08', 'D13 the brief\'s own limit wording is not mistaken for a disclosure', () => {
  const brief = briefWith(CLEAN_NOTE);
  assert.equal(brief.ok, true, brief.error || JSON.stringify(brief.words.findings));
  assert.equal(brief.words.ok, true, JSON.stringify(brief.words.findings));

  const limits = brief.payload.limits;
  assert.ok(Array.isArray(limits) && limits.length >= 4, 'the brief states no limits');
  assert.ok(limits.some((l) => /no ISZE supplier purchase price and no ISZE margin/.test(l)),
    'the brief no longer states the cost exclusion');
  assert.ok(limits.some((l) => /not an approval/i.test(l)), 'the brief no longer says it is not an approval');

  /* The sentence in `limits` says "cost" and "margin" in the same breath as
     "no". Refusing on it would make every brief impossible. */
  const direct = X.checkForRestrictedWords({ limits: limits });
  assert.equal(direct.ok, true, 'the limit statements were counted as a disclosure: '
    + JSON.stringify(direct.findings));

  return 'a clean brief passes; the ' + limits.length + ' limit statements are excluded from the check';
});

check('X09', 'D13 a restricted phrase in internal free text is carried, because that is where it belongs', () => {
  const note = 'Our parts cost is 60 EUR per unit and the gross margin is 30%.';
  const record = X.internalRecord(caseObject, scenario, result, {
    exported_at: null,
    review: Object.assign({}, review, { explanation: note }),
    sources: [],
    history: []
  });

  assert.equal(record.ok, true, 'the internal record was refused, which it must not be');
  const written = textOf(record);
  assert.ok(written.indexOf('parts cost') >= 0,
    'the internal record dropped the cost note, so the check is being applied where it does not belong');

  /* Both halves of the review section have to survive. The explanation is the
     case owner's own words and is the most important free text in the record. */
  const parsed = JSON.parse(written);
  assert.equal(parsed.review.explanation, note,
    'the review section was trimmed to ' + JSON.stringify(parsed.review));
  assert.equal(parsed.review.owner, 'case_owner', 'the reviewer role was dropped');
  assert.equal(parsed.review.note, review.note, 'the review note was dropped');

  return 'the internal record carries the same sentence the participant brief refuses, and its '
    + 'review section keeps ' + Object.keys(parsed.review).length + ' keys';
});

check('X09b', 'no internal section is trimmed to an empty object or dropped whole', () => {
  /* The S10c fault was an allowlist silently emptying a declared section. This
     asks the same question of every section the internal record writes, so a
     rule that "states its limits" cannot be satisfied by an empty shell.

     The review section used the UI's own shape here, because that is the shape
     the product actually hands it. */
  const record = X.internalRecord(caseObject, scenario, result, {
    exported_at: '2026-09-22T10:00:00.000Z',
    review: uiReview,
    sources: [{ reference_id: 'S1', kind: 'recorded transactions', title: 'Synthetic source',
      period: 'synthetic half year', status: 'accepted in part', restricted: true }],
    history: [{ revision: 1, recorded_at: '2026-09-22T09:00:00.000Z', state: 'draft',
      supersedes: null, note: 'first save' }],
    links: []
  });
  const written = JSON.parse(textOf(record));

  const sections = ['scenario', 'result', 'review', 'limits'];
  sections.forEach((name) => {
    assert.ok(Object.prototype.hasOwnProperty.call(written, name),
      'the internal record dropped its "' + name + '" section: '
      + JSON.stringify(Object.keys(written)));
    const v = written[name];
    const empty = v !== null && typeof v === 'object'
      && Object.keys(v).length === 0;
    assert.equal(empty, false, 'the internal record states "' + name + '" as an empty object');
  });

  /* The review section is where a case owner's own words live. Every field the
     UI form fills in has to reach the file. */
  ['owner_role', 'state', 'next_action', 'next_update_due', 'explanation', 'note'].forEach((k) => {
    assert.ok(Object.prototype.hasOwnProperty.call(written.review, k),
      'the review section dropped "' + k + '": ' + JSON.stringify(written.review));
  });
  assert.equal(written.review.explanation, uiReview.explanation,
    'the case owner\'s explanation was dropped from the record');

  assert.equal(written.sources.length, 1, 'the sources section lost its records');
  assert.equal(written.sources[0].reference_id, 'S1', 'a source record was trimmed');
  assert.equal(written.history.length, 1, 'the history section lost its revisions');
  assert.equal(written.history[0].revision, 1, 'a history revision was trimmed');
  assert.equal(written.history[0].state, 'draft', 'a revision lost its state');
  assert.equal(written.history[0].note, 'first save', 'a revision lost its note');

  return sections.length + ' sections are non-empty, the review section keeps '
    + Object.keys(written.review).length + ' keys, plus ' + written.sources.length
    + ' source and ' + written.history.length + ' history record(s)';
});

/* ============================================================ S10c: limits == */

check('X10', 'S10c the internal record\'s limits block is not empty and states each limitation', () => {
  const record = X.internalRecord(caseObject, scenario, result, { exported_at: null });
  const limits = record.payload.limits;

  assert.notEqual(limits, undefined, 'the limits key is missing from the internal record');
  assert.ok(!(limits && typeof limits === 'object' && !Array.isArray(limits)
    && Object.keys(limits).length === 0),
  'the limits key survives as an empty object: a record that claims to state its limits '
  + 'and states none');

  const statements = Array.isArray(limits) ? limits : Object.values(limits || {});
  assert.ok(statements.length >= 5, 'only ' + statements.length + ' limit(s) are stated');
  const text = statements.join(' ').toLowerCase();

  /* Each limitation the record declares has to be readable in the written block. */
  assert.ok(/not approved|no price in this record is approved/.test(text),
    'the record does not state that no price is approved');
  assert.ok(/customer net price is unconfirmed/.test(text),
    'the record does not state that the current customer net price is unconfirmed');
  assert.ok(/parts purchase cost/.test(text) && /excluded/.test(text),
    'the record does not state the cost measure and what it excludes');
  assert.ok(/raw invoices/.test(text), 'the record does not state that no raw invoices are carried');
  assert.ok(/credentials/.test(text), 'the record does not state that no credentials are carried');

  return statements.length + ' stated limitations: ' + statements[0];
});

/* The five facts the internal record's limits must state, by content. */
const INTERNAL_LIMIT_FACTS = [
  /no price in this record is approved/i,
  /customer net price is unconfirmed/i,
  /purchase cost[\s\S]*excluded: freight, duty, overheads and distributor kickbacks/i,
  /no raw invoices/i,
  /no credentials/i
];
function assertLimitFacts(limits, label) {
  assert.ok(Array.isArray(limits), label + ': limits is not an array: ' + JSON.stringify(limits));
  INTERNAL_LIMIT_FACTS.forEach((re) => {
    assert.ok(limits.some((s) => re.test(String(s))), label + ': no limit statement matches ' + re);
  });
}

check('X11', 'S10c the limits block is not empty in the written bytes either', () => {
  const record = X.internalRecord(caseObject, scenario, result, { exported_at: null });
  const written = JSON.parse(textOf(record));

  assertLimitFacts(written.limits, 'written bytes');
  assert.deepEqual(written.limits, record.payload.limits, 'the written bytes differ from the built record');
  const statements = Array.isArray(written.limits) ? written.limits : Object.values(written.limits || {});
  assert.ok(statements.length >= 5,
    'the written record carries "limits": ' + JSON.stringify(written.limits));

  return 'the written record carries ' + statements.length + ' limit statements ('
    + JSON.stringify(written.limits).length + ' characters of limits)';
});

/* =========================================================== S09b: names == */

check('X12', 'S09b a restricted word joined to another word is refused as an attachment name', () => {
  const gluing = ['supplier_cost_list_2026.xlsx', 'gross_margin_report.xlsx',
    'my_cost_file.xlsx', 'parts_purchase_price.xlsx', 'invoices_2026.xlsx'];
  const accepted = gluing.filter((n) => X.checkAttachmentName(n).ok);
  assert.deepEqual(accepted, [],
    'these names describe restricted content and were accepted: ' + JSON.stringify(accepted));

  /* The same words joined with hyphens, and the words with no separator at all. */
  const more = ['supplier-cost-list.xlsx', 'grossmarginreport.xlsx', 'costing_2026.xlsx',
    'fx_rates.xlsx', 'rebate_schedule.xlsx', 'landedcost.xlsx'];
  const alsoAccepted = more.filter((n) => X.checkAttachmentName(n).ok);
  assert.deepEqual(alsoAccepted, [], 'accepted: ' + JSON.stringify(alsoAccepted));

  const refused = X.checkAttachmentName('supplier_cost_list_2026.xlsx');
  assert.equal(refused.code, 'ATTACHMENT_NAME_LOOKS_RESTRICTED');
  assert.ok(refused.matched.includes('cost'), JSON.stringify(refused.matched));

  return 'refused ' + (gluing.length + more.length) + ' compound names, e.g. '
    + gluing.join(', ');
});

check('X12b', 'S09b a restricted measure written as one word with no separator is refused too', () => {
  /* "grossmarginreport.xlsx" has no token inside it at all, so a token rule
     cannot see it and it is on the glued list instead. */
  const glued = ['grossmarginreport.xlsx', 'grossprofit2026.xlsx', 'unitcost.xlsx',
    'landedcost_summary.xlsx', 'pricelist.xlsx'];
  const accepted = glued.filter((n) => X.checkAttachmentName(n).ok);
  assert.deepEqual(accepted, [], 'accepted: ' + JSON.stringify(accepted));

  /* And a token that merely starts with those letters is not caught, so the
     glued list is not a blanket substring test on every word. */
  assert.equal(X.checkAttachmentName('costing_notes.xlsx').ok, false,
    '"costing_notes.xlsx" should be refused by the stem rule');
  assert.equal(X.checkAttachmentName('grossing_up.xlsx').ok, true,
    '"grossing_up.xlsx" is not a restricted measure and must not be refused');

  return 'refused ' + glued.length + ' one-word names; "grossing_up.xlsx" is not refused';
});

check('X13', 'S09b the name check does not refuse an innocent name', () => {
  /* A check that refuses everything is not a check. These are ordinary names,
     including ones that contain a restricted word's letters without the word. */
  const innocent = ['open question for the distributor.docx', 'synthetic-note.pdf',
    'gpx_export_2026.csv', 'dashboard_notes.md', 'pads_kit_photo.jpg', 'agenda.xlsx'];
  const refused = innocent.filter((n) => !X.checkAttachmentName(n).ok);
  assert.deepEqual(refused, [], 'these ordinary names were refused: ' + JSON.stringify(refused));

  /* A name is not a permission. An empty or missing name is still refused, and
     the module never claims to have stored anything. */
  assert.equal(X.checkAttachmentName('').ok, false);
  assert.equal(X.checkAttachmentName(null).ok, false);

  return innocent.length + ' ordinary names accepted; "gpx_export_2026.csv" is not mistaken for "gp"';
});

/* ============================================================ S01c: schema == */

check('X14', 'S01c the written brief states its schema and recipient at the top level of the file', () => {
  const brief = briefWith(CLEAN_NOTE);
  assert.equal(brief.ok, true, brief.error);

  /* Read what is actually written, not the object in memory. */
  const written = JSON.parse(textOf(brief));
  assert.equal(written.schema, 'isze-pricing-member-brief',
    'the written brief has schema ' + JSON.stringify(written.schema)
    + '; top-level keys are ' + JSON.stringify(Object.keys(written)));
  assert.equal(written.recipient, 'member', 'the written brief does not name its recipient');
  assert.equal(written.contract_version, contracts.CONTRACT_VERSION,
    'the written brief does not state the contract version it was built to');
  assert.ok(typeof written.audience === 'string' && written.audience.length > 0,
    'the written brief does not state its audience');
  assert.equal(written.exported_at, '2026-09-22T10:00:00.000Z');

  /* The container structure is unchanged, so this is an addition at the top
     level and not a rearrangement of the offer. */
  ['reference', 'offer', 'price', 'quantity', 'customers', 'limits'].forEach((k) => {
    assert.ok(Object.prototype.hasOwnProperty.call(written, k),
      'the container "' + k + '" was lost: ' + JSON.stringify(Object.keys(written)));
  });
  assert.equal(written.offer.part_number, 'SYNTH-PART-A');
  assert.equal(written.price.price_after, 95);

  return 'schema, contract_version, recipient and audience are readable at the top level, beside '
    + JSON.stringify(Object.keys(written).filter((k) => ['reference', 'offer', 'price', 'quantity',
      'customers', 'limits'].includes(k)));
});

check('X15', 'the participant brief still carries the offer it exists to communicate', () => {
  const brief = briefWith(CLEAN_NOTE);
  const written = JSON.parse(textOf(brief));

  assert.equal(written.offer.part_number, caseObject.part_number, 'the part number is missing');
  assert.equal(written.offer.price_before, 100);
  assert.equal(written.offer.price_after, 95);
  assert.equal(written.quantity.quantity_after, 1200);
  assert.equal(written.customers.support_eur, 500);
  /* The percentage is derived from the two prices the recipient is given, so it
     is compared with a tolerance rather than asserted on a binary floating-point
     division. 95/100 is not exactly representable. */
  assert.ok(Math.abs(written.price.change_pct - -5) < 1e-9,
    'the derived price change is missing or wrong: ' + JSON.stringify(written.price.change_pct));

  /* And nothing restricted came with it. */
  const leaked = restrictedNamesIn(brief);
  assert.deepEqual(leaked, [], 'restricted names reached the brief: ' + leaked.join(', '));
  assert.equal(brief.audit.ok, true, 'the audit flagged: ' + brief.audit.findings.join('; '));

  return textOf(brief).length + ' bytes; part number, both prices, the quantity, the stated support '
    + 'and the price change are present';
});

/* ==================================================== the mutation proof == */

check('X16', 'moving the internal parts cost from 60 to 41.75 leaves the member brief byte-identical', () => {
  const before = briefWith(CLEAN_NOTE);
  assert.equal(before.ok, true, before.error);

  /* Move the parts cost, the margin and the profit. A filter would let the
     change reach the brief; a construction cannot, because none of those values
     is ever copied across. */
  const movedScenario = Object.assign({}, scenario, {
    cost: 41.75, cost_eur: 41.75, margin_pp_change: -11.9, gp_change: -1234, gp_after: 1
  });
  const movedResult = Object.assign({}, result, {
    cost: 41.75, cost_eur: 41.75, margin_pp_change: -11.9, gp_change: -1234, gp_after: 1
  });
  const after = X.memberBrief(caseObject, movedScenario, movedResult,
    { exported_at: '2026-09-22T10:00:00.000Z', request_note: CLEAN_NOTE });

  assert.equal(after.ok, true, after.error);
  assert.equal(textOf(before), textOf(after),
    'the brief changed when only internal figures changed, so something internal is reaching it');
  assert.ok(textOf(after).indexOf('41.75') < 0, 'the new cost value reached the brief');
  assert.deepEqual(restrictedNamesIn(after), []);

  return 'brief bytes identical (' + textOf(after).length + ' bytes) before and after the internal '
    + 'cost moved from 60 to 41.75';
});

check('X17', 'the internal record still carries the cost, so X16 is not vacuous', () => {
  const record = X.internalRecord(caseObject, scenario, result, { exported_at: null });
  const written = textOf(record);

  assert.ok(written.indexOf('"cost"') >= 0 || written.indexOf('"cost_eur"') >= 0,
    'the internal record carries no cost, so the mutation proof proves nothing');
  assert.ok(written.indexOf('60') >= 0, 'the cost value is absent from the internal record');
  assert.ok(record.audit.ok, 'the internal record was audited as a participant document');

  return 'the internal record carries the parts cost and the whole scenario; '
    + written.length + ' bytes';
});

check('X18', 'a planted internal-only key is caught by the audit, so the audit is not vacuous', () => {
  const brief = briefWith(CLEAN_NOTE);
  assert.equal(brief.audit.ok, true, 'the honest brief failed its audit');

  const planted = JSON.parse(textOf(brief));
  planted.offer.cost_eur = 60;
  planted.offer.margin_pp_change = -3.4;
  planted.price.gp_change = -260;

  const audit = X.audit(planted, 'member');
  assert.equal(audit.ok, false, 'the audit passed a brief carrying a planted cost key');
  assert.ok(audit.findings.some((f) => /cost_eur/.test(f)), audit.findings.join('; '));
  assert.ok(audit.findings.some((f) => /margin_pp/.test(f)), audit.findings.join('; '));

  return 'planted keys caught: ' + audit.findings.join('; ');
});

check('X19', 'the ported phrase and pattern lists are the ones in use, not a private copy', () => {
  assert.ok(Array.isArray(X.RESTRICTED_PHRASES) && X.RESTRICTED_PHRASES.length >= 40,
    'the phrase list is missing or short');
  assert.ok(Array.isArray(X.RESTRICTED_PATTERNS) && X.RESTRICTED_PATTERNS.length >= 12,
    'the pattern list is missing or short');
  X.RESTRICTED_PATTERNS.forEach((p) => {
    assert.ok(p.name && p.re instanceof RegExp, 'a pattern has no name or is not a regular expression');
  });

  /* A field-name check and a figure check have to stay distinguishable, because
     the extension D13 asks for is about figures. */
  const phrase = X.checkForRestrictedWords({ t: 'our parts cost applies here' });
  const figure = X.checkForRestrictedWords({ t: 'what we pay is 60 EUR for this item' });
  assert.ok(phrase.findings.some((f) => f.rule === 'field name'));
  assert.ok(figure.findings.some((f) => f.rule === 'figure in text'));

  return X.RESTRICTED_PHRASES.length + ' phrases and ' + X.RESTRICTED_PATTERNS.length
    + ' patterns, each carrying the rule that matched it';
});

check('X20', 'the internal record is refused as a participant document', () => {
  const record = X.internalRecord(caseObject, scenario, result, { exported_at: null });
  const guard = X.assertInternalOnly(record);
  assert.equal(guard.ok, false, 'the internal record can be handed over without complaint');
  assert.equal(guard.code, 'INTERNAL_ONLY');
  assert.match(guard.error, /do not trim this one/);

  const brief = briefWith(CLEAN_NOTE);
  assert.equal(X.assertInternalOnly(brief).ok, true, 'a participant brief was refused by that guard');

  return guard.error.slice(0, 110) + '...';
});

check('X21', 'the shipped module answers the reviewer\'s own SAFE-05 inputs, which are pointed at the retired module', () => {
  /* tests/accept/accept_05_08_safety.cjs asks two of these questions of
     `recipients` (src/output/recipients.js), which tools/build.py does NOT
     assemble. The questions are asked here of the module the build does ship,
     using the same inputs, so the answer for the shipped code is on the record. */
  const ownersInputs = ['supplier_cost_list_2026.xlsx', 'gross_margin_report.xlsx',
    'my_cost_file.xlsx', 'parts_purchase_price.xlsx', 'invoices_2026.xlsx'];
  const accepted = ownersInputs.filter((n) => X.checkAttachmentName(n).ok);
  assert.deepEqual(accepted, [],
    'S09b: the shipped module accepted ' + JSON.stringify(accepted));

  const record = X.internalRecord(caseObject, scenario, result,
    { exported_at: null, review: null, sources: [], history: [] });
  assertLimitFacts(record.payload.limits, 'S10c: the shipped module');
  assert.ok(!(typeof record.payload.limits === 'object' && !Array.isArray(record.payload.limits)
    && Object.keys(record.payload.limits).length === 0),
  'S10c: the shipped module wrote an empty limits object: ' + JSON.stringify(record.payload.limits));
  assert.ok(Array.isArray(record.payload.limits) && record.payload.limits.length >= 5,
    'S10c: the shipped module states ' + JSON.stringify(record.payload.limits));

  return 'S09b all 5 refuse; S10c carries ' + record.payload.limits.length
    + ' statements in the shipped module (the same two checks still fail against '
    + 'src/output/recipients.js, which the build does not ship)';
});

check('X22', 'the interface acts on the refusal instead of writing the file', () => {
  /* The refusal is only worth having if the caller obeys it. The interface
     checks `audit.ok` before it downloads a brief, so the refusal has to land
     there as well as on `ok`. This reads the shipped view to confirm the guard
     is still present, and simulates the guard on a refused brief. */
  const app = fs.readFileSync(path.join(ROOT, 'src', 'ui', 'app.js'), 'utf8');

  assert.ok(/if\s*\(\s*!exported\.audit\.ok\s*\)/.test(app),
    'the interface no longer checks the brief audit before downloading it, so a refused brief '
    + 'would be written to disk');

  /* The guard as the interface runs it. */
  const refused = briefWith('Our parts cost is 60 EUR per unit.');
  const writeWouldHappen = refused.audit.ok;
  assert.equal(writeWouldHappen, false, 'the interface guard would let the refused brief through');

  /* And a clean brief still passes the same guard. */
  assert.equal(briefWith(CLEAN_NOTE).audit.ok, true, 'the guard would block a clean brief');

  return 'the interface guard (!exported.audit.ok) is present and would block the refused brief '
    + 'and allow the clean one';
});

check('X23', 'the module works on the load path the product actually uses, not only under require', () => {
  /* tools/build.py pastes each module into a <script> block, so the artifact
     loads export.js as a plain global with no CommonJS in scope. A test that
     only ever calls `require` is testing a different load path from the one the
     operator uses. */
  const vm = require('node:vm');
  const sandbox = { console: { log() { }, warn() { }, error() { } }, TextEncoder, TextDecoder, Uint8Array };
  vm.createContext(sandbox);
  for (const rel of ['src/data/contracts.js', 'src/data/export.js']) {
    vm.runInContext(fs.readFileSync(path.join(ROOT, rel), 'utf8'), sandbox, { filename: rel });
  }

  assert.equal(typeof sandbox.AIMExport, 'object', 'AIMExport is not a global after a script load');
  assert.equal(typeof sandbox.AIMContracts, 'object', 'AIMContracts is not a global after a script load');

  const brief = sandbox.AIMExport.memberBrief(caseObject, scenario, result,
    { exported_at: null, request_note: CLEAN_NOTE });
  assert.equal(brief.ok, true, 'a clean brief failed to build on the browser load path');
  assert.equal(brief.payload.schema, 'isze-pricing-member-brief');

  const refused = sandbox.AIMExport.memberBrief(caseObject, scenario, result,
    { exported_at: null, request_note: 'Our parts cost is 60 EUR per unit.' });
  assert.equal(refused.ok, false, 'the refusal did not fire on the browser load path');
  assert.equal(refused.payload, null);
  assert.equal(sandbox.AIMExport.toBytes(refused, false).length, 4, 'a refusal wrote more than null');

  assert.equal(sandbox.AIMExport.checkAttachmentName('supplier_cost_list_2026.xlsx').code,
    'ATTACHMENT_NAME_LOOKS_RESTRICTED');

  return 'loaded as a global script with no CommonJS: clean brief builds, refusal fires, '
    + 'compound name refused';
});

/* ---------------------------------------------------------------- report -- */

console.log('');
console.log('AIM shipped export module (src/data/export.js) - ' + results.length + ' checks');
console.log('='.repeat(96));
for (const r of results) {
  console.log(`${r.status === 'PASS' ? 'PASS' : 'FAIL'}  ${r.id}  ${r.name}`);
  if (r.evidence) console.log('      -> ' + r.evidence);
}
console.log('-'.repeat(96));
const passed = results.filter((r) => r.status === 'PASS').length;
console.log(`${passed} passed, ${failures} failed, of ${results.length}`);
console.log('');

process.exit(failures === 0 ? 0 : 1);
