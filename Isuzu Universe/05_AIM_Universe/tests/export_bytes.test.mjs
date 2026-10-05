#!/usr/bin/env node
/* ===========================================================================
   Recipient exports judged as real bytes - F08 / SAFE-03 / SAFE-04 / SAFE-05.

   Run:
     node tests/export_bytes.test.mjs

   Exit code is 0 only when every check passes.

   The defect being reproduced
   ---------------------------
   v03 shipped an export helper that removed restricted field names from the
   whole internal record and then audited what was left:

     var V03_FORBIDDEN = ["cost_eur", "parts cost", ...];
     function v03strip(obj){ drop any key whose name contains a forbidden word }
     function v03audit(obj){ return V03_FORBIDDEN.filter(f => text includes f) }

   `cost_eur` was on the list. `cost` was not. So a nested object carrying
   `scenario.cost` and `margin_pp_change` came out of the stripper untouched and
   the audit reported no problem at all. This file reproduces that helper
   verbatim, in a form whose result does not depend on the engine block in the
   HTML, and shows it failing on the same data the corrected code handles.

   What is asserted here
   ----------------------
     E01  the old blacklist removes `cost_eur` and leaves `cost` behind
     E02  the old audit therefore reports nothing wrong on that same object
     E03  the old blacklist leaves a nested cost and a margin inside a
          free-text note, and still reports clean
     E04  the same data, through the recipient allowlist: the member brief is
          refused or carries neither, asserted on the produced BYTES
     E05  the member brief carries no parts cost, gross profit, margin, supplier
          discount, FX rate or cost record - in a plain field, a nested object,
          a free-text note and a derived value
     E06  the internal record is marked internal and is refused as a participant
          document
     E07  changing an internal figure does not change the brief, which is the
          test that the brief is constructed rather than filtered
     E08  the permission table: a participant may not read the internal record
     E09  production identity is not available, and the code says so
     E10  a restricted attachment is refused and the storage gap is named
     E11  a negative-control check on the harness itself: the assertion used
          above does catch a planted restricted field
   =========================================================================== */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));

const contracts = (await import(new URL('../src/data/contracts.js', import.meta.url))).default;
const engine = (await import(new URL('../src/engine/engine.js', import.meta.url))).default;
const output = (await import(new URL('../src/output/recipients.js', import.meta.url))).default;

/* ------------------------------------------------------------- harness -- */

const results = [];
let failures = 0;

function check(id, name, fn) {
  try {
    const evidence = fn();
    results.push({ id, name, status: 'PASS', evidence: evidence === undefined ? '' : String(evidence) });
  } catch (e) {
    failures++;
    const frame = String(e.stack || '').split('\n')
      .find(line => line.includes('export_bytes.test.mjs:') && !line.includes('check ('));
    results.push({
      id, name, status: 'FAIL',
      evidence: frame ? `${e.message}  [${frame.trim().replace(/^at\s+/, '')}]` : e.message
    });
  }
}

/* --------------------------------------------------------- the v03 helper -- */

/* Copied from the frozen reference HTML, lines 179306-179328, with only the
   container changed so it can run here. The field list and the matching rule are
   exactly the ones that shipped. */
const V03_FORBIDDEN = ['cost_eur', 'parts cost', 'parts_cost', 'gross profit', 'grossprofit',
  'grossmargin', 'gp_before', 'gp_after', 'gp_change', 'margin_before', 'margin_after',
  'verifiedcosts', 'cost_bases', 'cost_basis', 'source_discount', 'base_price_jpy',
  'costrecord', 'jpy_per_eur', 'markup', 'fob_eur'];

function v03strip(obj, depth) {
  depth = depth || 0;
  if (depth > 12) return null;
  if (Array.isArray(obj)) return obj.map(function (x) { return v03strip(x, depth + 1); });
  if (obj && typeof obj === 'object') {
    const out = {};
    Object.keys(obj).forEach(function (k) {
      const lk = k.toLowerCase();
      const bad = V03_FORBIDDEN.some(function (f) { return lk.indexOf(f) >= 0; });
      if (bad) return;
      out[k] = v03strip(obj[k], depth + 1);
    });
    return out;
  }
  return obj;
}

function v03audit(obj) {
  const text = JSON.stringify(obj).toLowerCase();
  return V03_FORBIDDEN.filter(function (f) { return text.indexOf(f) >= 0; });
}

/* ------------------------------------------------------------ test data -- */

/* A synthetic case that carries every shape the defect is about: a plain cost,
   a nested cost, a margin beside it, a free-text note with a figure written into
   the sentence, and a derived disclosure. No real part, customer or price. */
const internalCase = {
  case_id: 'CASE-SYNTH-1',
  version: 7,
  state: 'approved',
  owner_role: 'approver',
  next_action: 'Support owner to give the agreed support',
  next_update_due: '2026-10-15',
  customer: 'Synthetic customer',
  market: 'SYNTH',
  part_number: 'SYNTH-PART-A',
  description: 'Synthetic part A',
  unit: 'unit',
  title: 'Synthetic offer for the synthetic account',
  evidence_period: 'synthetic half year',
  offer_effective_date: '2026-10-01',
  selected_alternative_id: 'SYNTH-INC',
  objective: 'revenue'
};

const internalScenario = {
  scenario_id: 'CASE-SYNTH-1:v4', version: 4, case_id: 'CASE-SYNTH-1',
  part_number: 'SYNTH-PART-A', unit: 'unit',
  price_before: 100, price_after: 95,
  quantity_before: 100, quantity_after: 120,
  quantity_label: 'manual scenario', scope: 'incremental',
  volume_is_observed: false, pack_size: 1,
  /* The restricted content, in the shapes that matter. */
  cost: 60,                                   /* the name the blacklist missed  */
  cost_eur: 60,                               /* the name the blacklist caught  */
  margin_pp_change: -3.4,                     /* a margin sitting beside it     */
  gp_change: -260, gp_before: 4000, gp_after: 3740,
  cost_basis_id: 'FWD_B', cost_basis_source: 'verified record',
  support_eur: 500,
  sources: []
};

const internalResult = engine.calculate({
  price_before: 100, price_after: 95, quantity_before: 100, quantity_after: 120,
  cost_eur: 60, support_eur: 500, scope: 'incremental',
  quantity_label: 'manual scenario', pack_size: 1,
  evidence_period: 'synthetic half year', offer_effective_date: '2026-10-01'
});

const review = {
  owner: 'approver role',
  status: 'Ready for human review',
  explanation: 'The account asked for launch support on the additional volume.',
  note: 'Proposed at 95 EUR against a 100 EUR list.'
};

/* The free-text note that names a unit cost. This is the case the blacklist
   could not see, and the corrected code refuses rather than editing the
   sentence. */
const leakingReview = {
  owner: 'approver role',
  status: 'Ready for human review',
  explanation: 'The account asked for support. Our cost on this item is 60 EUR per unit, '
    + 'which the participant has not been given and must not be given.',
  note: 'Proposed at 95 EUR against a 100 EUR list.'
};

/* The whole internal record, as `internalRecord` would build it. The F08 defect
   is reproduced against this, because a field helper is only ever handed one
   record at a time. */
const wholeInternal = {
  schema: 'isze-pricing-internal-record',
  case_id: 'CASE-SYNTH-1',
  state: 'approved',
  scenario: internalScenario,
  result: internalResult,
  review: review,
  sources: []
};

/* Every restricted thing that must not reach a participant, and the path it
   lives at, so a failure names the field rather than only a count. */
const RESTRICTED_NAMES = [
  'cost', 'cost_eur', 'margin_pp_change', 'gp_change', 'gp_before', 'gp_after',
  'supplier discount', 'jpy_per_eur', 'fx', 'fob', 'markup', 'cost_basis'
];

/* The names the participant brief is permitted to carry, and which contain one
   of the words above. Listed so the byte check is precise: a brief carrying
   "support_eur" says nothing about the parts cost, and a check that cannot tell
   those apart would be noise rather than a control. */
const ALLOWED_NAMES_THAT_LOOK_RESTRICTED = ['support_eur'];

function bytesOf(exported) {
  return output.toBytes(exported).text;
}

/* Which restricted names appear in these bytes, ignoring the names the
   participant is entitled to see. */
function restrictedNamesIn(exported) {
  const lower = bytesOf(exported).toLowerCase();
  return RESTRICTED_NAMES.filter(n => lower.includes(n) && !ALLOWED_NAMES_THAT_LOOK_RESTRICTED.includes(n));
}

/* ------------------------------------------------------------------------ */

check('E01', 'The old blacklist removes cost_eur and leaves cost behind (F08)', () => {
  const stripped = v03strip(wholeInternal);

  /* What it did catch. */
  assert.equal('cost_eur' in stripped.scenario, false,
    'cost_eur should have been removed, and it was not');
  assert.equal('cost_basis_id' in stripped.scenario, false,
    'cost_basis_id should have been removed, and it was not');

  /* What it missed, in the very object it just "cleaned". This is the defect:
     the name `cost` is not on the list, so the unit cost walks straight
     through. */
  assert.equal('cost' in stripped.scenario, true,
    'FAILING-AS-EXPECTED: the blacklist should leave `cost` behind, and it did not');
  assert.equal(stripped.scenario.cost, 60, 'the unit parts cost survived stripping');
  assert.equal('margin_pp_change' in stripped.scenario, true,
    'the blacklist should leave margin_pp_change behind, and it did not');
  assert.equal(stripped.scenario.margin_pp_change, -3.4, 'the margin change survived stripping');

  /* Its coverage is arbitrary rather than reasoned. It removed
     `margin_after_pct` only because that name happens to contain the listed
     substring `margin_after`, while it left the sibling `margin_pp_change`
     because that name does not. Two margins, treated opposite ways, by
     accident. */
  assert.equal('margin_after_pct' in stripped.result, false,
    'margin_after_pct was removed by substring accident');
  assert.equal('margin_pp_change' in stripped.scenario, true,
    'margin_pp_change was kept by substring accident');

  return 'after stripping: scenario.cost=' + stripped.scenario.cost
    + ', scenario.margin_pp_change=' + stripped.scenario.margin_pp_change
    + ', result.margin_after_pct removed; cost_eur removed and cost not';
});

check('E02', 'The old audit does not report the unit cost it just failed to remove (F08)', () => {
  const stripped = v03strip(wholeInternal);
  const findings = v03audit(stripped);

  /* The audit searches the serialised text for the blacklist names. The names it
     knows are gone, so it cannot report them - while the unit cost and the
     margin sit in the object under names it was never told about.

     It is not silent, which is worth being precise about: it reports "gross
     profit" here only because one of the engine's own flag messages happens to
     contain that phrase in prose. That is an incidental description, not the
     figure. The two things that would matter are not reported at all. */
  assert.equal(findings.includes('cost'), false,
    'the audit cannot see the unit cost, because `cost` was never on its list');
  assert.equal(findings.includes('cost_eur'), false,
    'the audit cannot see cost_eur either: the stripper already removed it, so the text no longer has it');
  assert.equal(findings.includes('margin_pp_change'), false,
    'the margin change is not on the list, so it is not reported');

  /* And the things it cannot report are still there. */
  assert.equal(stripped.scenario.cost, 60, 'the unit cost is still there');
  assert.equal(stripped.scenario.margin_pp_change, -3.4, 'the margin is still there');

  return 'v03audit returned ' + JSON.stringify(findings) + ' - an incidental mention of the phrase '
    + '"gross profit" in a flag message - while scenario.cost=60 and '
    + 'scenario.margin_pp_change=-3.4 remained in the same object unreported';
});

check('E03', 'The old blacklist also misses a unit cost written inside a sentence (F08)', () => {
  const whole = { review: leakingReview, scenario: internalScenario };
  const stripped = v03strip(whole);
  const findings = v03audit(stripped);

  /* The sentence survives intact. A field-name filter cannot see inside a
     string, and the audit looks for the same field names, so it sees nothing. */
  assert.match(stripped.review.explanation, /Our cost on this item is 60 EUR per unit/);
  assert.deepEqual(findings, [],
    'FAILING-AS-EXPECTED: the v03 audit should not notice the sentence, and it reported '
    + JSON.stringify(findings));

  /* The sentence is the one the corrected code refuses to put in a brief. */
  const brief = output.memberBrief({
    case: internalCase, scenario: internalScenario, result: internalResult,
    review: leakingReview, meta: { request_note: 'Please review the attached proposal.' }
  });
  assert.equal(brief.ok, false, 'the corrected code must refuse this brief');
  assert.equal(brief.code, 'RESTRICTED_WORD_IN_FREE_TEXT');
  assert.equal(brief.payload, null, 'a refused brief must produce no payload at all');
  assert.ok(brief.words.findings.some(f => f.path === '.customers.explanation'),
    'the finding should name the sentence: ' + JSON.stringify(brief.words.findings));

  return 'the sentence "Our cost on this item is 60 EUR per unit" survived v03 stripping with no '
    + 'finding; the corrected code refuses the brief with ' + brief.code;
});

check('E04', 'The member brief is constructed, and both leaks are refused rather than edited', () => {
  /* Leak one: the unit cost written into free text. */
  const inFreeText = output.memberBrief({
    case: internalCase, scenario: internalScenario, result: internalResult,
    review: leakingReview, meta: { request_note: 'Please review.' }
  });
  assert.equal(inFreeText.ok, false, 'the free-text leak should be refused');
  assert.equal(inFreeText.code, 'RESTRICTED_WORD_IN_FREE_TEXT');
  assert.ok(inFreeText.words.findings.length >= 1);
  assert.ok(inFreeText.error.includes('Nothing was produced'));

  /* Leak two: the same kind of figure arriving through a declared free-text
     field rather than through a field name. A construction cannot catch this,
     so it is reported rather than disguised. */
  const inADeclaredKey = output.memberBrief({
    case: internalCase, scenario: internalScenario,
    result: internalResult, review: review,
    meta: { request_note: 'Support requested. Our cost is 60 EUR per unit.' }
  });
  assert.equal(inADeclaredKey.ok, false, 'a cost written into a declared text field should be refused');
  assert.equal(inADeclaredKey.code, 'RESTRICTED_WORD_IN_FREE_TEXT');
  assert.ok(inADeclaredKey.words.findings.some(f => /cost figure written into text/.test(f.phrase)),
    'the finding should name what it matched: ' + JSON.stringify(inADeclaredKey.words.findings));

  /* The clean case is produced, and the brief's own limit wording is not
     mistaken for a disclosure. */
  const clean = output.memberBrief({
    case: internalCase, scenario: internalScenario, result: internalResult,
    review: review, meta: { request_note: 'Please review the attached proposal.' }
  });
  assert.equal(clean.ok, true, clean.error || JSON.stringify(clean.words.findings));
  assert.equal(clean.words.findings.some(f => /limits/.test(f.path)), false,
    'the brief limit statements must not be counted as a disclosure');
  assert.ok(clean.payload.limits.some(l => /no ISZE supplier purchase price and no ISZE margin/.test(l)));

  return 'refused with ' + inFreeText.code + ': ' + inFreeText.error.slice(0, 120) + '...';
});

check('E05', 'A member brief carries no cost, profit, margin, discount or FX - asserted on the bytes', () => {
  const brief = output.memberBrief({
    case: internalCase, scenario: internalScenario, result: internalResult,
    review: review, meta: { request_note: 'Please review the attached proposal.' }
  });
  assert.equal(brief.ok, true, brief.error || 'the brief should have been produced');

  const bytes = output.toBytes(brief);
  const text = bytes.text;
  const lower = text.toLowerCase();

  const leaked = restrictedNamesIn(brief);
  assert.deepEqual(leaked, [], 'these restricted names reached the brief bytes: ' + leaked.join(', '));

  /* And by shape, in case a value survived under a harmless name. */
  assert.ok(!/"cost"\s*:/.test(lower), 'a "cost" key reached the brief');
  assert.ok(!/"cost_eur"\s*:/.test(lower), 'a "cost_eur" key reached the brief');
  assert.ok(!/"margin_pp_change"\s*:/.test(lower), 'a margin key reached the brief');
  assert.ok(!/"margin_(before|after|unit)/.test(lower), 'a margin key reached the brief');
  assert.ok(!/"gp_(before|after|change)"\s*:/.test(lower), 'a gross-profit key reached the brief');
  assert.ok(!/\bfob\b/i.test(text), 'an FOB value reached the brief');
  assert.ok(!/\bjpy\b/i.test(text), 'an FX rate reached the brief');
  assert.ok(!/\bmarkup\b/i.test(text), 'a markup reached the brief');

  /* Not the values either, wherever they might be hiding. 60 is the unit parts
     cost; 41.75 is the moved one used in the next check. */
  assert.ok(!text.includes('"cost":60') && !text.includes('"cost": 60'), 'the unit cost value reached the brief');

  /* What is supposed to be there, so this cannot pass by carrying nothing. */
  assert.ok(text.includes('"price_before":100'), 'the given price should be in the brief');
  assert.ok(text.includes('"price_after":95'), 'the proposed price should be in the brief');
  assert.ok(text.includes('SYNTH-PART-A'), 'the part number should be in the brief');
  assert.ok(text.includes('"support_eur":500'), 'the stated support should be in the brief');
  /* The derived percentage is allowed: it comes only from the two prices the
     recipient is given. No margin, cost or profit is derived. */
  assert.ok(text.includes('"change_pct":-5'), 'the price change percentage should be in the brief');

  assert.equal(brief.audit.ok, true, 'the brief audit flagged: ' + brief.audit.findings.join('; '));
  return `${bytes.length} bytes; restricted names found: none; carried: price_before, price_after, `
    + 'part_number, support_eur, change_pct';
});

check('E06', 'The internal record is marked internal and is refused as a participant document', () => {
  const record = output.internalRecord({
    case: internalCase, scenario: internalScenario, result: internalResult,
    extra: { review: review, sources: [], exported_at: '2026-09-22T10:00:00.000Z' }
  });
  assert.equal(record.recipient, 'internal');
  const bytes = output.toBytes(record).text;
  assert.ok(bytes.includes('ISZE internal only'), 'the internal record must say it is internal');

  /* The cost is meant to be here: this record is for ISZE. */
  assert.ok(/"cost"\s*:/.test(bytes), 'the internal record should carry the parts cost');

  /* And handing it to a participant is refused by name. */
  const refused = output.assertInternalOnly(record);
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'INTERNAL_ONLY');
  assert.match(refused.error, /must not be given to a distributor or dealer participant/);
  assert.match(refused.error, /do not trim this one/);

  /* A member brief passes that guard. */
  const brief = output.memberBrief({ case: internalCase, scenario: internalScenario, result: internalResult });
  assert.equal(output.assertInternalOnly(brief).ok, true);
  return refused.error;
});

check('E07', 'Changing an internal figure does not change the brief: it is built, not filtered', () => {
  const args = {
    case: internalCase, scenario: internalScenario, result: internalResult,
    review: review, meta: { request_note: 'Please review.' }
  };
  const before = output.memberBrief(args);

  /* Move the parts cost and the margin. A filter would leak the change; a
     construction cannot, because neither value is ever copied across. */
  const moved = Object.assign({}, internalScenario, {
    cost: 41.75, cost_eur: 41.75, margin_pp_change: -11.9, gp_change: -1234, gp_after: 1
  });
  const after = output.memberBrief(Object.assign({}, args, { scenario: moved }));

  assert.equal(before.ok, true, before.error);
  assert.equal(after.ok, true, after.error);
  assert.equal(bytesOf(before), bytesOf(after),
    'the brief changed when only internal figures changed, so something internal is reaching it');
  assert.ok(!bytesOf(after).includes('41.75'), 'the new cost value reached the brief');
  assert.deepEqual(restrictedNamesIn(after), []);
  return 'brief bytes identical before and after the internal cost moved from 60 to 41.75';
});

check('E08', 'A participant may not read the internal record', () => {
  const participant = output.makeDevIdentity({ role: 'viewer', name: 'synthetic participant' });
  const owner = output.makeDevIdentity({ role: 'case_owner', name: 'synthetic owner' });

  const shared = output.canRead(participant, 'shared_brief');
  assert.equal(shared.allowed, true);
  assert.equal(shared.identity_authenticated, false, 'the shim must not claim authentication');
  assert.equal(shared.development_only, true);

  const internal = output.canRead(participant, 'internal_record');
  assert.equal(internal.allowed, false);
  assert.equal(internal.code, 'NOT_PERMITTED');

  const ownerInternal = output.canRead(owner, 'internal_record');
  assert.equal(ownerInternal.allowed, true);

  /* The support owner may deliver, and may not read parts cost or margin. */
  const support = output.makeDevIdentity({ role: 'support_owner' });
  assert.equal(output.canRead(support, 'internal_record').allowed, false);
  assert.equal(output.canRead(support, 'shared_brief').allowed, true);

  /* No identity at all reads nothing. */
  const nobody = output.canRead(null, 'shared_brief');
  assert.equal(nobody.allowed, false);
  assert.equal(nobody.code, 'NO_IDENTITY');

  /* An unknown role cannot be constructed, so it cannot be granted anything. */
  assert.throws(() => output.makeDevIdentity({ role: 'administrator' }), /known role/);
  return `viewer: brief ${shared.allowed} / internal ${internal.allowed} / `
    + `support_owner: internal ${output.canRead(support, 'internal_record').allowed}`;
});

check('E09', 'Production identity is not available, and the code says so', () => {
  const notAvailable = output.requireApprovedIdentity();
  assert.equal(notAvailable.ok, false);
  assert.equal(notAvailable.code, 'IDENTITY_NOT_AVAILABLE');
  assert.match(notAvailable.error, /remain unimplemented/);

  /* An identity that claims to be approved but carries no verified organisation
     is refused rather than trusted. */
  const unverifiedTenant = output.canRead({
    mode: 'approved', authenticated: true, role: 'case_owner',
    subject: 'someone', tenant: 'somewhere', tenant_verified: false
  }, 'internal_record');
  assert.equal(unverifiedTenant.allowed, false);
  assert.equal(unverifiedTenant.code, 'TENANT_NOT_VERIFIED');

  /* An identity claiming an unknown mode reads nothing. */
  const unknownMode = output.canRead({ mode: 'trust-me', authenticated: true, role: 'case_owner' },
    'internal_record');
  assert.equal(unknownMode.allowed, false);
  assert.equal(unknownMode.code, 'UNKNOWN_IDENTITY_MODE');
  return notAvailable.error;
});

check('E10', 'A restricted attachment is refused and the storage gap is named (SAFE-06)', () => {
  const owner = output.makeDevIdentity({ role: 'case_owner' });
  const participant = output.makeDevIdentity({ role: 'viewer' });

  const restricted = output.canAttach(owner, { name: 'pack.zip', restricted: true });
  assert.equal(restricted.allowed, false);
  assert.equal(restricted.code, 'ATTACHMENT_IS_RESTRICTED');

  const suggestive = output.canAttach(owner, { name: 'supplier-cost-detail.xlsx' });
  assert.equal(suggestive.allowed, false);
  assert.equal(suggestive.code, 'ATTACHMENT_NAME_LOOKS_RESTRICTED');

  const fromParticipant = output.canAttach(participant, { name: 'note.pdf' });
  assert.equal(fromParticipant.allowed, false);

  /* A clean file is permitted, and the answer says plainly that nothing was
     stored, because there is no file store to store it in. */
  const clean = output.canAttach(owner, { name: 'synthetic-note.pdf' });
  assert.equal(clean.allowed, true);
  assert.equal(clean.stored, false);
  assert.match(clean.storage_gap, /remains unimplemented/);
  assert.match(clean.storage_gap, /no approved file store/);
  return clean.storage_gap;
});

check('E11', 'Negative control: the byte check does catch a planted restricted field', () => {
  /* If this check passes, the assertion used in E05 is not vacuous. A helper is
     deliberately broken so a cost reaches the brief, and the same finder that
     reported "none" above is required to find it now. */
  const cleanMeta = { request_note: 'Please review.' };
  const honest = output.memberBrief({
    case: internalCase, scenario: internalScenario, result: internalResult,
    review: review, meta: cleanMeta
  });
  assert.deepEqual(restrictedNamesIn(honest), [],
    'the honest brief should be clean');

  /* Now plant the defect in the delivered structure by hand, the way a future
     edit to the allowlist would. */
  const planted = JSON.parse(JSON.stringify(honest.payload));
  planted.offer.cost = 60;
  planted.offer.margin_pp_change = -3.4;
  const plantedText = JSON.stringify(planted).toLowerCase();
  const found = RESTRICTED_NAMES.filter(n => plantedText.includes(n));
  assert.ok(found.includes('cost'), 'the finder must catch a planted cost');
  assert.ok(found.includes('margin_pp_change'), 'the finder must catch a planted margin');

  /* And the brief audit itself must flag the planted keys. */
  const audit = output.audit(planted, 'member');
  assert.equal(audit.ok, false, 'the audit must flag a planted internal-only key');
  assert.ok(audit.findings.some(f => /cost/.test(f)), 'the audit should name the cost: '
    + audit.findings.join('; '));

  /* The old blacklist, given the same planted object, is the contrast: it
     removes nothing here because the names are not on its list. */
  const v03 = v03strip(planted);
  assert.equal('cost' in v03.offer, true, 'the old helper left the planted cost');
  assert.equal(v03audit(v03).includes('cost_eur'), false);
  return `planted keys caught by the allowlist audit (${found.join(', ')}); `
    + 'the v03 helper left both planted keys in place';
});

/* ---------------------------------------------------------------- report -- */

const width = Math.max(...results.map(r => r.id.length + r.name.length)) + 4;
console.log('');
console.log('AIM recipient exports as bytes - ' + results.length + ' checks');
console.log('='.repeat(Math.min(width + 20, 100)));
for (const r of results) {
  console.log(`${r.status === 'PASS' ? 'PASS' : 'FAIL'}  ${r.id}  ${r.name}`);
  if (r.evidence) console.log('      -> ' + r.evidence);
}
console.log('-'.repeat(Math.min(width + 20, 100)));
const passed = results.filter(r => r.status === 'PASS').length;
console.log(`${passed} passed, ${failures} failed, of ${results.length}`);
console.log('');

process.exit(failures === 0 ? 0 : 1);