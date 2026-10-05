/* ===========================================================================
   Recipient-specific exports (SAFE-03, SAFE-04, SAFE-05, F08, D13, S09b, S01c).

   The v03 helper exported the whole internal record and then deleted field
   names it did not like. A blacklist always loses: a nested "cost" survived it,
   and the audit then reported nothing wrong. This module does the opposite. It
   builds each output from a declared allowlist, so a field that nobody declared
   cannot appear, however it is nested.

   What sits on top of the allowlist, and why
   ------------------------------------------
   An allowlist stops a restricted FIELD. It cannot stop a restricted FIGURE
   typed into a sentence, and it cannot see a restricted word hidden inside a
   file name. Those gaps are closed here, by porting the hardened reference
   implementation (src/output/recipients.js) rather than inventing a second
   scheme:

     D13  checkForRestrictedWords - restricted wording in free text is REFUSED,
          not quietly deleted. A silently emptied sentence is the same fault as
          the blacklist it replaced: the output looks clean because nobody ever
          decided what belonged in it. The refusal names the phrase and the path
          and produces no participant payload at all.
     S10c the internal record's own limits block is stated in full. See the
          note beside `internalRecord` for why it is an array of statements.
     S09b checkAttachmentName - a restricted word joined to another word by an
          underscore, a hyphen or nothing at all is still caught.
     S01c the written brief is self-describing: its schema marker and its
          recipient label sit at the top level of the file that is actually
          written, beside the containers and not inside one of them.

   What this is not
   ----------------
   A content check inside a JSON builder is not access control. A browser-side
   filter is not a server-side permission, and nothing in this module should be
   read as one. Production sign-in, organisation membership and revocation need
   a server, which this component does not have.
   =========================================================================== */
(function (root) {
  'use strict';

  var contracts = (typeof module === 'object' && module.exports)
    ? require('../data/contracts.js') : root.AIMContracts;

  /* A leaf value is only carried when its key was declared for this recipient. */
  function buildAllowed(source, allowedKeys, path) {
    path = path || '';
    if (Array.isArray(source)) {
      return source.map(function (item, i) { return buildAllowed(item, allowedKeys, path + '[' + i + ']'); });
    }
    if (source && typeof source === 'object') {
      var out = {};
      Object.keys(source).forEach(function (k) {
        if (allowedKeys[k] === undefined) return;       /* not declared -> not carried */
        out[k] = buildAllowed(source[k], allowedKeys, path + '.' + k);
      });
      return out;
    }
    return source;
  }

  /* The wrapper this module writes around an export. These names are listed once
     rather than inferred, so the top level of a written file is a visible
     decision and not an accident. `schema` and `recipient` are here because a
     reader of the file has to be able to tell what they are holding without
     reading this module (S01c). */
  var ENVELOPE_FIELDS = ['schema', 'contract_version', 'recipient', 'audience', 'exported_at'];

  /* The internal record may carry anything `contracts.js` declares, plus the
     wrapper above, plus the sections this module states in its own words. Each
     name is listed rather than inferred, so adding a section to the internal
     record is a visible change to an allowlist and not an accident.

     `review` and `not_approved_statement` are here because `review` is a case
     section, not a scenario or result field, so `declaredFields()` does not
     cover it - without it the record survives with `review: {}` and the case
     owner's own explanation of the proposal is silently dropped, which is the
     same fault as the empty limits block. */
  var INTERNAL_ENVELOPE_FIELDS = ['limits', 'not_approved_statement', 'review'];

  /* The review section of an internal record, listed key by key. It is only
     ever written into the internal record, never into a participant brief. The
     first four names are already declared in contracts.js (the UI's review form
     writes them); the rest are this section's own. */
  var INTERNAL_REVIEW_FIELDS = ['owner_role', 'state', 'next_action', 'next_update_due',
    'owner', 'status', 'explanation', 'note', 'outcome',
    'reviewed_at', 'review_date', 'raised_by', 'evidence_requested'];

  /* The revision log of an internal record, listed key by key. A revision is the
     case's own history, and contracts.js declares none of these names, so
     without this list the log survives as `[{}, {}]` - a record that states its
     history and states none. The names are the ones the case store hands over. */
  var INTERNAL_HISTORY_FIELDS = ['revision', 'recorded_at', 'supersedes', 'recorded_by',
    'note', 'state', 'version', 'updated_at', 'outcome'];

  /* UX-05. The current-metadata block of an internal record, listed key by key.
     The interface derives it once and paints the same block on the header, the
     cost results and the scenario panel, so the file states what the screen
     stated when it was exported. */
  var INTERNAL_METADATA_FIELDS = ['metadata', 'payload_version', 'build_date', 'list_price_status',
    'cost_status', 'cost_basis_id', 'offer_effective_date'];

  /* Fields the member brief derives or carries that are not in the shared
     contracts. Each one is named here, so an addition to a participant brief is
     a visible change to this list rather than an accident.

     `change_pct` is derived only from `price_before` and `price_after`, both of
     which the recipient is given, so it discloses nothing they were not handed.
     No margin, cost, profit or contribution value is derived for a participant.

     `explanation` is the customer or supply explanation, and `participant_note`
     the note for the reader. Both are free text, so both are checked for
     restricted wording before a brief is produced: a construction cannot see a
     figure someone typed into a sentence. */
  var MEMBER_CONSTRUCTED_FIELDS = ['change_pct', 'explanation', 'participant_note'];

  function allowlistFor(recipient) {
    var spec = contracts.RECIPIENTS[recipient];
    if (!spec) throw new Error('Unknown recipient "' + recipient + '"');
    var keys = {};
    if (spec.leaf_fields === null) {
      /* The internal record may carry anything already declared in the contracts
         file. An undeclared key is still refused, so the internal export cannot
         grow a field that no contract knows about. */
      contracts.declaredFields().forEach(function (k) { keys[k] = true; });
      INTERNAL_ENVELOPE_FIELDS.forEach(function (k) { keys[k] = true; });
      /* The review section's own keys, so the case owner's explanation of the
         proposal is written out instead of being trimmed to an empty object. */
      INTERNAL_REVIEW_FIELDS.forEach(function (k) { keys[k] = true; });
      /* And the revision log's keys, so the history is written out rather than
         surviving as an array of empty objects. */
      INTERNAL_HISTORY_FIELDS.forEach(function (k) { keys[k] = true; });
      INTERNAL_METADATA_FIELDS.forEach(function (k) { keys[k] = true; });
    } else {
      spec.leaf_fields.forEach(function (k) { keys[k] = true; });
      MEMBER_CONSTRUCTED_FIELDS.forEach(function (k) { keys[k] = true; });
    }
    /* The permitted CONTAINERS must be on the allowlist as well as the leaf
       names. Without this the builder drops every declared container - the
       field-name allowlist alone survives only for those whose names happen to
       be leaf names - and a participant receives a brief with no part number, no
       price and no quantity. That is the same class of fault as the blacklist it
       replaced: the output looks clean and carries nothing usable. The container
       is permitted; its contents are still filtered by the leaf allowlist, so
       this widens nothing. */
    (spec.permits || []).forEach(function (k) { keys[k] = true; });
    ENVELOPE_FIELDS.forEach(function (k) { keys[k] = true; });
    return keys;
  }

  /* ------------------------------------------- restricted wording in text -- */

  /* Names of the restricted measures themselves. A sentence that says "our
     parts cost is ..." is caught here. Ported from the hardened reference, with
     the additions at the end marked as such. */
  var RESTRICTED_PHRASES = [
    'cost_eur', 'parts cost', 'partscost', 'parts_cost', 'purchase cost', 'purchase price',
    'unit cost', 'unitcost', 'landed cost', 'landedcost',
    'gross profit', 'grossprofit', 'gross margin', 'grossmargin',
    'gp_before', 'gp_after', 'gp_change', 'gp_pct',
    'margin_before', 'margin_after', 'margin_pp', 'margin_unit', 'margin_unit_after_pct',
    'verifiedcosts', 'verified costs', 'cost_bases', 'cost_basis', 'cost basis',
    'source_discount', 'source discount', 'supplier discount', 'supplier rebate',
    'base_price', 'base price', 'jpy_per_eur', 'fx_rate', 'fx rate', 'exchange rate',
    'markup', 'mark-up', 'fob_eur', 'fob', 'contribution margin',
    'bridge_cost', 'bridge_revenue',
    'internal_note', 'internal note', 'internal only note',
    /* Extensions: the same disclosure, written the way a person would type it. */
    'net margin', 'net profit', 'profit margin',
    'buying price', 'cost price', 'net cost', 'our cost', 'supplier cost',
    'purchase discount'
  ];

  /* A restricted word next to a FIGURE. This is the half a field allowlist
     cannot see: a cost, a margin or an FX rate someone typed into a sentence.
     The first group is the hardened reference's list; the second group is the
     extension D13 asks for, because a figure written as text does not always
     put the restricted word first, and does not always use the word "cost". */
  var RESTRICTED_PATTERNS = [
    { name: 'a cost figure written into text',
      re: /\bcosts?\b[^.!?]{0,80}\d|\d[^.!?]{0,80}\bcosts?\b/i },
    { name: 'a margin figure written into text',
      re: /\bmargins?\b[^.!?]{0,80}\d|\d[^.!?]{0,80}\bmargins?\b/i },
    { name: 'gross profit named in text', re: /\bgross\s+profit\b/i },
    { name: 'a supplier discount in text',
      re: /\b(supplier|source|inbound|purchase)\s+(discount|rebate|kickback)\b/i },
    { name: 'an FX rate in text', re: /\b(jpy|forex|fx|yen|exchange\s+rate)\b/i },
    { name: 'an FOB value in text', re: /\bfob\b/i },
    { name: 'a markup in text', re: /\bmark[- ]?ups?\b/i },
    { name: 'a price ISZE pays written into text',
      re: /\b(purchase|supplier|landed|buying)\s+price\b/i },
    /* Extensions (D13). */
    { name: 'a profit figure written into text',
      re: /\bprofits?\b[^.!?]{0,80}\d|\d[^.!?]{0,80}\bprofits?\b/i },
    { name: 'what ISZE pays written into text',
      re: /\b(what\s+we\s+pay|what\s+isze\s+pays?|cost\s+us|we\s+paid|we\s+pay)\b/i },
    { name: 'a cost or margin written per unit',
      re: /\b(cost|margin|profit)\b[^.!?]{0,40}\bper\s+(unit|piece|set|kit)\b|\bper\s+(unit|piece|set|kit)\b[^.!?]{0,40}\b(cost|margin|profit)\b/i },
    { name: 'a currency rate written as a pair',
      re: /\b(usd|gbp|jpy|eur|cny|thb|inr|chf)\s*[\/=]\s*(usd|gbp|jpy|eur|cny|thb|inr|chf)\b/i },
    { name: 'a cost basis named in text',
      re: /\bcost\s+basis\b|\bverified\s+cost|\bcost\s+record\b/i }
  ];

  /* The brief's own limit statements say "no ISZE supplier purchase price and no
     margin". Saying so is not disclosing it, so those sentences are excluded
     from the check by their path rather than by weakening the patterns. */
  var LIMIT_TEXT_PATH = /^\.(limits|limit_statement|not_approved_statement)\b/;

  function wordsIn(value, out, path) {
    path = path || '';
    if (value === null || value === undefined) return out;
    if (Array.isArray(value)) {
      value.forEach(function (v, i) { wordsIn(v, out, path + '[' + i + ']'); });
      return out;
    }
    if (typeof value === 'object') {
      Object.keys(value).forEach(function (k) { wordsIn(value[k], out, path + '.' + k); });
      return out;
    }
    if (typeof value === 'string') {
      var lower = value.toLowerCase();
      RESTRICTED_PHRASES.forEach(function (p) {
        if (lower.indexOf(p.toLowerCase()) >= 0) out.push({ path: path, phrase: p, rule: 'field name' });
      });
      RESTRICTED_PATTERNS.forEach(function (p) {
        if (p.re.test(value)) out.push({ path: path, phrase: p.name, rule: 'figure in text' });
      });
      return out;
    }
    return out;
  }

  /* Every restricted word or figure sitting in free text, with the path it was
     found at. Reported, never removed: see `finish`. */
  function checkForRestrictedWords(payload) {
    var hits = wordsIn(payload, []);
    var filtered = hits.filter(function (h) { return !LIMIT_TEXT_PATH.test(h.path); });
    return { ok: filtered.length === 0, findings: filtered };
  }

  /* ------------------------------------------------------- attachment names -- */

  /* S09b. A restricted word joined to another word by an underscore, a hyphen
     or nothing at all ("supplier_cost_list_2026.xlsx", "invoices_2026.xlsx")
     must still be seen. Matching a whole word with a word boundary cannot do
     that, because no boundary falls inside the joined token.

     A word that is a distinctive stem ("cost", "invoice", "margin", "purchase")
     is matched at the start of a token, so "invoices", "costing" and "my_cost"
     are all caught. A two-letter word ("gp", "fx") is matched on the whole token
     only, so "gpx" is not mistaken for it.

     This is a convenience, not the control. The control is the recipient
     allowlist above, and - in a deployed system - the permission decision, which
     needs a server this component does not have. */
  var RESTRICTED_ATTACHMENT_STEMS = ['cost', 'invoice', 'margin', 'markup', 'profit',
    'discount', 'rebate', 'billing', 'purchase', 'landed', 'supplier', 'kickback',
    /* Two-word measures written as one word with an underscore: these are the
       head word, so "supplier_cost_list" is caught by "cost" and
       "parts_purchase_price" by "purchase". "supplier" also catches a file that
       names the supplier without naming the measure. */
    'supplier', 'price'];
  var RESTRICTED_ATTACHMENT_TOKENS = ['gp', 'fx', 'fob', 'jpy'];
  var RESTRICTED_ATTACHMENT_COMPOUNDS = [/\bprices?\s*list\b/, /\bsupplier\s+cost\b/,
    /\bgross\s+margin\b/, /\bcost\s+price\b/, /\blist\s+price\b/, /\bnet\s+cost\b/];

  /* A name written with no separator at all is one word, not two, so there is no
     token to match. The glued forms are listed separately rather than pretending
     a token rule can see them. */
  var RESTRICTED_ATTACHMENT_GLUED = ['grossmargin', 'grossprofit', 'netmargin',
    'partscost', 'unitcost', 'landedcost', 'costprice', 'netcost', 'pricelist',
    'suppliercost', 'unitprice', 'netprofit', 'sourcecost'];

  function checkAttachmentName(name) {
    if (typeof name !== 'string' || !name.trim()) {
      return { ok: false, code: 'ATTACHMENT_NEEDS_A_NAME', error: 'An attachment needs a name.' };
    }
    /* Underscores, hyphens and dots join words into one token, so they are
       flattened to spaces before anything is looked at. A name written with no
       separator at all keeps its single token, which is why the glued list below
       exists as well. */
    var flat = name.toLowerCase().replace(/[_\-.,]+/g, ' ');
    var tokens = flat.split(/[^a-z0-9]+/).filter(Boolean);
    var found = [];

    tokens.forEach(function (token) {
      RESTRICTED_ATTACHMENT_STEMS.forEach(function (stem) {
        if (token.indexOf(stem) === 0 && found.indexOf(stem) < 0) found.push(stem);
      });
      RESTRICTED_ATTACHMENT_TOKENS.forEach(function (word) {
        if (token === word && found.indexOf(word) < 0) found.push(word);
      });
      RESTRICTED_ATTACHMENT_GLUED.forEach(function (glued) {
        if (token.indexOf(glued) >= 0 && found.indexOf(glued) < 0) found.push(glued);
      });
    });
    RESTRICTED_ATTACHMENT_COMPOUNDS.forEach(function (re) {
      var m = flat.match(re);
      if (m && found.indexOf(m[0].trim()) < 0) found.push(m[0].trim());
    });

    if (found.length) {
      return {
        ok: false,
        code: 'ATTACHMENT_NAME_LOOKS_RESTRICTED',
        matched: found,
        error: 'The file name "' + name + '" describes restricted content (' + found.join(', ')
          + '). A name is a convenience check, not the control, so this refuses rather than '
          + 'guessing. Rename it if that is wrong, or attach it to the internal record only. '
          + 'Nothing was stored.'
      };
    }
    return { ok: true, code: 'ATTACHMENT_NAME_CLEAR', matched: [] };
  }

  /* ---------------------------------------------------------------- guard -- */

  /* The one hand-over that matters most: the internal record given to a
     participant. It is refused by name, and the refusal says what to build
     instead rather than inviting a trim. */
  function assertInternalOnly(exported) {
    if (!exported || exported.recipient !== 'internal') {
      return { ok: true, note: 'Not an internal record.' };
    }
    return {
      ok: false,
      code: 'INTERNAL_ONLY',
      error: 'This is the internal record for recipient "internal". It carries parts cost and '
        + 'margin and must not be given to a distributor or dealer participant. Build a "member" '
        + 'brief instead; do not trim this one.'
    };
  }

  /* ------------------------------------------------------ member brief -- */

  /* Deliberately assembled field by field. Everything a distributor participant
     needs to answer the question, and no ISZE cost, margin or internal note. */
  function memberBrief(caseObject, scenario, result, meta) {
    meta = meta || {};
    var offer = {
      part_number: caseObject.part_number,
      description: (caseObject.description || null),
      unit: caseObject.unit || 'unit',
      price_before: scenario.price_before,
      price_after: scenario.price_after,
      quantity_before: scenario.quantity_before,
      quantity_after: result.ok ? result.quantity_after : null,
      quantity_label: scenario.quantity_label,
      scope: scenario.scope,
      evidence_period: scenario.evidence_period,
      offer_effective_date: scenario.offer_effective_date
    };
    /* S01c. The schema marker, the contract version, the recipient and the
       recipient label are written at the TOP LEVEL of the file, beside the
       containers. A reader who opens the saved brief can tell what it is without
       knowing this module; the container structure below is unchanged. */
    var envelope = {
      schema: 'isze-pricing-member-brief',
      contract_version: contracts.CONTRACT_VERSION,
      recipient: 'member',
      audience: contracts.RECIPIENTS.member.label,
      exported_at: meta.exported_at || null
    };
    var brief = Object.assign({}, envelope, {
      reference: {
        case_id: caseObject.case_id,
        customer: caseObject.customer,
        title: caseObject.title || null
      },
      offer: offer,
      price: {
        price_before: scenario.price_before,
        price_after: scenario.price_after,
        change_pct: (scenario.price_before
          ? 100 * (scenario.price_after / scenario.price_before - 1) : null)
      },
      quantity: {
        quantity_before: scenario.quantity_before,
        quantity_after: result.ok ? result.quantity_after : null,
        quantity_label: scenario.quantity_label,
        unit: caseObject.unit || 'unit'
      },
      customers: {
        support_eur: scenario.support_eur,
        note: meta.request_note || null
      },
      limits: [
        'This brief states a price and a quantity under discussion. It is not an approval.',
        'It contains no ISZE supplier purchase price and no ISZE margin.',
        'No volume response to a price change is assumed or predicted.',
        'Fitment, kit contents and vehicle application are not approved by this document.',
        'A price stated here is a proposal. The case is open until an owner accepts it.'
      ]
    });
    return finish(brief, 'member');
  }

  /* --------------------------------------------------- internal record -- */

  function internalRecord(caseObject, scenario, result, extra) {
    extra = extra || {};
    var record = {
      schema: 'isze-pricing-internal-record',
      contract_version: contracts.CONTRACT_VERSION,
      recipient: 'internal',
      audience: 'ISZE internal only',
      exported_at: extra.exported_at || null,
      case_id: caseObject.case_id,
      version: caseObject.version || 1,
      customer: caseObject.customer,
      market: caseObject.market || null,
      part_number: caseObject.part_number,
      unit: caseObject.unit || 'unit',
      evidence_period: scenario.evidence_period,
      offer_effective_date: scenario.offer_effective_date,
      selected_alternative_id: scenario.selected_alternative_id || null,
      objective: scenario.objective || null,
      scenario: scenario,
      result: result,
      review: extra.review || null,
      sources: extra.sources || [],
      state: caseObject.state || 'draft',
      owner_role: caseObject.owner_role || null,
      /* The revision history is handed over in `extra` by the interface, which
         reads it from the case store. This read `caseObject.history`, a key the
         case object does not carry, so the section was written as `[]` even when
         revisions existed - the record stated a history and stated none. The
         declared field is the same either way; only the source was wrong. */
      history: extra.history || caseObject.history || [],
      metadata: extra.metadata || null,
      not_approved_statement: 'This record states a proposal and its result. Nothing in it is an '
        + 'approval and it is not safe to forward outside ISZE.',
      /* S10c. This block used to be an object, and the allowlist then dropped
         every value inside it because none of those five leaf names is declared
         in contracts.js. The record survived with `limits: {}` - a record that
         claims to state its limits and states none, which is worse than omitting
         the section.

         Until contracts.js declares the five leaf names (price_approved,
         current_customer_net_price, supplier_cost, no_raw_invoices,
         no_credentials), the block is carried in the form the contract already
         declares: an array of statements under the permitted `limits` key. An
         array of strings is not filtered by the allowlist, so the limits are
         actually written out. The five facts are all in the statements below. */
      limits: [
        'No price in this record is approved.',
        'The current customer net price is unconfirmed.',
        'Parts purchase cost is carried on the declared measure only. Excluded: freight, duty, '
          + 'overheads and distributor kickbacks.',
        'No raw invoices are carried in this record.',
        'No credentials are carried in this record.'
      ]
    };
    return finish(record, 'internal');
  }

  function finish(payload, recipient) {
    var keys = allowlistFor(recipient);
    var built = buildAllowed(payload, keys);
    var words = recipient === 'member'
      ? checkForRestrictedWords(built)
      : { ok: true, findings: [] };
    var content = audit(built, recipient);

    /* Keep the declared nested containers whole for the member brief: the
       allowlist governs leaf names, so a permitted container survives with only
       its permitted contents. */
    var result = {
      ok: true,
      recipient: recipient,
      label: contracts.RECIPIENTS[recipient].label,
      payload: built,
      words: words,
      audit: content
    };

    /* D13. A construction cannot see a restricted figure someone typed into a
       sentence. When the word check finds one the brief is REFUSED: no payload
       is produced, and the offending phrase and path are named in the error.
       The sentence is not quietly emptied, because an output that looks clean
       only because nobody decided what belonged in it is the blacklist fault
       again. The refusal also lands on `audit`, which is what a caller consults
       before writing a file - so a caller that only knows about `audit` still
       refuses to write it. */
    if (recipient === 'member' && !words.ok) {
      result.ok = false;
      result.refused = true;
      result.code = 'RESTRICTED_WORD_IN_FREE_TEXT';
      result.error = 'This brief was refused because it would carry restricted wording: '
        + words.findings.map(function (f) {
          return '"' + f.phrase + '" (' + f.rule + ') at ' + (f.path || '.');
        }).join(', ')
        + '. Nothing was produced and no participant payload exists. Reword the free text, or move '
        + 'that content to the internal record.';
      result.payload = null;
      result.audit = {
        ok: false,
        refused: true,
        code: 'RESTRICTED_WORD_IN_FREE_TEXT',
        findings: content.findings.concat(words.findings.map(function (f) {
          return 'restricted wording "' + f.phrase + '" (' + f.rule + ') at ' + (f.path || '.');
        }))
      };
    }
    return result;
  }

  /* --------------------------------------------------------------- audit -- */

  /* A restricted field name must never reach a participant. This is checked on
     the structure, not on the rendered text: a sentence that says a brief
     contains no supplier cost is not itself a supplier cost, and an audit that
     cannot tell those apart is the reason the old helper was rejected. */
  var MEMBER_FORBIDDEN_KEYS = [
    'cost_eur', 'parts_cost', 'partscost', 'purchasecost', 'purchase_price',
    'unitcost', 'landedcost', 'grossprofit', 'grossmargin',
    'gp_before', 'gp_after', 'gp_change', 'gp_pct',
    'margin_before', 'margin_after', 'margin_pp', 'margin_unit',
    'verifiedcosts', 'cost_bases', 'cost_basis', 'costrecord', 'cost_record',
    'source_discount', 'base_price', 'jpy_per_eur', 'markup', 'fob_eur',
    'contribution', 'bridge_revenue', 'bridge_cost', 'bridge_support',
    'internal_note', 'internalonly'
  ];

  /* Numeric fields a member brief must not carry. Kept short and explicit: the
     construction is the control, this is a second pair of eyes. */
  var MEMBER_FORBIDDEN_NUMERIC = ['cost', 'cost_eur', 'gp_change', 'gp_before', 'gp_after',
    'margin_after_pct', 'margin_before_pct', 'margin_unit_after_pct'];

  function audit(payload, recipient) {
    if (recipient !== 'member') return { ok: true, findings: [] };
    var findings = [];

    (function walk(node, path) {
      if (Array.isArray(node)) { node.forEach(function (v, i) { walk(v, path + '[' + i + ']'); }); return; }
      if (node && typeof node === 'object') {
        Object.keys(node).forEach(function (k) {
          var lk = k.toLowerCase().replace(/[^a-z0-9_]/g, '');
          MEMBER_FORBIDDEN_KEYS.forEach(function (f) {
            var ff = f.replace(/[^a-z0-9_]/g, '');
            if (lk.indexOf(ff) >= 0 && findings.indexOf(f) < 0) {
              findings.push(f + ' (key ' + path + '.' + k + ')');
            }
          });
          walk(node[k], path + '.' + k);
        });
      }
    })(payload, '');

    /* A numeric field that names a cost or a margin is refused outright. */
    MEMBER_FORBIDDEN_NUMERIC.forEach(function (f) {
      var text = JSON.stringify(payload);
      if (new RegExp('"' + f + '"\\s*:\\s*-?[0-9]').test(text) && findings.indexOf(f) < 0) {
        findings.push(f + ' (numeric value present)');
      }
    });

    return { ok: findings.length === 0, findings: findings };
  }

  /* Export as real bytes and inspect them (SAFE-05). A UI label is not evidence.
     Only `payload` is serialised: a refused brief carries its explanation on the
     envelope, so the refusal wording - which names the offending phrase - can
     never be written into a file by this function. */
  function toBytes(exported, pretty) {
    var payload = (exported && typeof exported === 'object'
      && Object.prototype.hasOwnProperty.call(exported, 'payload'))
      ? exported.payload : null;
    var text = JSON.stringify(payload === undefined ? null : payload, null, pretty ? 2 : 0);
    if (typeof TextEncoder === 'function') {
      return { bytes: new TextEncoder().encode(text), text: text, length: text.length };
    }
    var buf = Buffer.from(text, 'utf8');
    return { bytes: buf, text: text, length: text.length };
  }

  /* ------------------------------------------------- identity and permission --

     Ported from the hardened reference so the SHIPPED builder carries them, not
     just the retired copy. This closes the access-control half of F08 that only
     ever existed in src/output/recipients.js.

     What this is NOT: an authentication. There is no backend on this machine, so
     a development identity is a declaration, and every result it produces says so
     in its own words. A browser-side check is not server-side access control and
     must never be described as one. */

  var IDENTITY_MODES = ['approved', 'development-only'];

  /* The role table, and the whole of it. `viewer` is a participant: it may read
     the brief prepared for it and nothing else. `support_owner` delivers support
     and deliberately cannot read parts cost or margin. */
  var PERMISSIONS = [
    { role: 'viewer', resource: 'shared_brief', allowed: true,
      note: 'A participant may read the brief prepared for them.' },
    { role: 'viewer', resource: 'internal_record', allowed: false,
      note: 'A participant never reads the internal record.' },
    { role: 'viewer', resource: 'attachment', allowed: false,
      note: 'A participant cannot fetch an attachment through this component.' },
    { role: 'requester', resource: 'shared_brief', allowed: true, note: 'May read the brief.' },
    { role: 'requester', resource: 'internal_record', allowed: false,
      note: 'A requester does not read the internal record.' },
    { role: 'requester', resource: 'attachment', allowed: true,
      note: 'May attach a file that carries no restricted content.' },
    { role: 'case_owner', resource: 'shared_brief', allowed: true, note: 'May read the brief.' },
    { role: 'case_owner', resource: 'internal_record', allowed: true, note: 'Owns the case.' },
    { role: 'case_owner', resource: 'attachment', allowed: true,
      note: 'May attach a file that carries no restricted content.' },
    { role: 'reviewer', resource: 'shared_brief', allowed: true, note: 'May read the brief.' },
    { role: 'reviewer', resource: 'internal_record', allowed: true, note: 'Reviews the case.' },
    { role: 'reviewer', resource: 'attachment', allowed: false,
      note: 'A reviewer reads, and does not add attachments.' },
    { role: 'approver', resource: 'shared_brief', allowed: true, note: 'May read the brief.' },
    { role: 'approver', resource: 'internal_record', allowed: true, note: 'Approves the case.' },
    { role: 'approver', resource: 'attachment', allowed: false,
      note: 'An approver reads, and does not add attachments.' },
    { role: 'support_owner', resource: 'shared_brief', allowed: true, note: 'May read the brief.' },
    { role: 'support_owner', resource: 'internal_record', allowed: false,
      note: 'Delivers the support; does not read parts cost or margin.' },
    { role: 'support_owner', resource: 'attachment', allowed: true,
      note: 'May attach a file that carries no restricted content.' }
  ];

  function rejectPermission(code, message, extra) {
    var out = { ok: false, allowed: false, code: code, error: message };
    if (extra) { Object.keys(extra).forEach(function (k) { out[k] = extra[k]; }); }
    return out;
  }

  function permissionFor(role, resource) {
    return PERMISSIONS.filter(function (p) {
      return p.role === role && p.resource === resource;
    })[0] || null;
  }

  /* The permission question, asked before anything is read or attached. Every
     result states whether the identity was actually authenticated. */
  function canRead(identity, resource) {
    if (!identity) {
      return rejectPermission('NO_IDENTITY', 'No identity was supplied, so nothing may be read.');
    }
    if (IDENTITY_MODES.indexOf(identity.mode) < 0) {
      return rejectPermission('UNKNOWN_IDENTITY_MODE',
        'Unknown identity mode "' + identity.mode + '". Nothing may be read.');
    }
    if (!identity.authenticated) {
      var devRow = permissionFor(identity.role, resource);
      if (!devRow || !devRow.allowed) {
        return rejectPermission('NOT_PERMITTED',
          'The role "' + identity.role + '" is not permitted to read "' + resource + '".',
          { identity_authenticated: false, development_only: true });
      }
      return {
        ok: true, allowed: true, resource: resource, role: identity.role,
        identity_authenticated: false, development_only: true,
        reason: 'Permitted by the development-only shim. This is not an authentication and not a '
          + 'tenant policy decision.'
      };
    }
    var row = permissionFor(identity.role, resource);
    if (!row || !row.allowed) {
      return rejectPermission('NOT_PERMITTED',
        'The role "' + identity.role + '" is not permitted to read "' + resource + '".',
        { identity_authenticated: true });
    }
    if (!identity.tenant || !identity.tenant_verified) {
      return rejectPermission('TENANT_NOT_VERIFIED',
        'The identity belongs to no verified organisation, so the case cannot be shown to belong '
        + 'to it.', { identity_authenticated: true });
    }
    return { ok: true, allowed: true, resource: resource, role: identity.role,
      identity_authenticated: true, development_only: false, note: row.note };
  }

  function canAttach(identity, attachment) {
    var permission = canRead(identity, 'attachment');
    if (!permission.allowed) return permission;
    if (!attachment || !attachment.name) {
      return rejectPermission('ATTACHMENT_NEEDS_A_NAME', 'An attachment needs a name.');
    }
    if (attachment.restricted) {
      return rejectPermission('ATTACHMENT_IS_RESTRICTED',
        'A file marked as carrying restricted content cannot be attached to a case that is '
        + 'prepared for a participant. Nothing was stored.');
    }
    var checked = checkAttachmentName(attachment.name);
    if (!checked.ok) return checked;
    return { ok: true, allowed: true, resource: 'attachment', role: identity.role,
      identity_authenticated: !!identity.authenticated,
      development_only: !identity.authenticated,
      note: 'The name and the restriction flag were checked. The file itself is not stored by '
        + 'this component.' };
  }

  /* A declared identity for development. It says on its face that it is not an
     authentication, and it throws rather than inventing a role. */
  function makeDevIdentity(spec) {
    spec = spec || {};
    var role = spec.role;
    if (['requester', 'case_owner', 'reviewer', 'approver', 'support_owner', 'viewer']
      .indexOf(role) < 0) {
      throw new Error('A development identity needs a known role. Got "' + role + '".');
    }
    return {
      mode: 'development-only', authenticated: false,
      subject: 'dev:' + role + (spec.name ? ':' + spec.name : ''),
      role: role, tenant: spec.tenant || null, tenant_verified: false,
      statement: 'Not an authentication. A development-only identity for local work.'
    };
  }

  /* An authenticated identity is REFUSED here rather than accepted: there is no
     approved issuer on this machine, so accepting one would be inventing
     authority. This is the honest form of the gap, not a placeholder. */
  function requireApprovedIdentity() {
    return rejectPermission('NO_APPROVED_IDENTITY_SOURCE',
      'There is no approved identity provider configured for this component, so no authenticated '
      + 'identity can be accepted. Development identities are available and are labelled as such.');
  }

  var API = {
    memberBrief: memberBrief,
    internalRecord: internalRecord,
    audit: audit,
    allowlistFor: allowlistFor,
    toBytes: toBytes,
    buildAllowed: buildAllowed,
    /* Ported from the hardened reference so the shipped module carries the same
       checks rather than a private copy of them. */
    checkForRestrictedWords: checkForRestrictedWords,
    checkAttachmentName: checkAttachmentName,
    assertInternalOnly: assertInternalOnly,
    /* Identity and permission, ported 2026-09-22 so the shipped builder can answer
       the attachment question src/case/store.js asks it. */
    IDENTITY_MODES: IDENTITY_MODES,
    PERMISSIONS: PERMISSIONS,
    permissionFor: permissionFor,
    canRead: canRead,
    canAttach: canAttach,
    makeDevIdentity: makeDevIdentity,
    requireApprovedIdentity: requireApprovedIdentity,
    RESTRICTED_PHRASES: RESTRICTED_PHRASES,
    RESTRICTED_PATTERNS: RESTRICTED_PATTERNS,
    RESTRICTED_ATTACHMENT_STEMS: RESTRICTED_ATTACHMENT_STEMS,
    RESTRICTED_ATTACHMENT_TOKENS: RESTRICTED_ATTACHMENT_TOKENS,
    ENVELOPE_FIELDS: ENVELOPE_FIELDS,
    INTERNAL_ENVELOPE_FIELDS: INTERNAL_ENVELOPE_FIELDS
  };
  root.AIMExport = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
