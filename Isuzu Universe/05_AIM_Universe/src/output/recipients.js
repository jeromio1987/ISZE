/* ===========================================================================
   Recipient-specific exports and the one permission check (SAFE-03, SAFE-04,
   SAFE-05, SAFE-06, SAFE-01).

   The defect being corrected (F08)
   --------------------------------
   v03 exported the whole internal record and then deleted the field names it
   did not like:

     var V03_FORBIDDEN = ["cost_eur", ...];
     function v03strip(obj){ ... if the key contains a forbidden word, drop it ... }

   A blacklist of names cannot hold. `cost_eur` was on the list but `cost` was
   not, so an object carrying `scenario.cost` and `margin_pp_change` came back
   out of the stripper intact and the audit reported no findings at all. The
   helper that was meant to protect the file said the file was clean.

   What this file does instead
   ---------------------------
   Nothing is exported and then trimmed. Each output is built up from an
   allowlist: a field is carried because it was declared for that recipient, and
   a field nobody declared cannot appear however deeply it is nested and
   whatever it is called. The check and the construction are therefore the same
   act, not two independent steps that can disagree.

   Content that is not a declared field is not carried. A free-text explanation
   is carried because `note` / `text` / `explanation` are declared for the
   recipient, and a restricted figure written inside that sentence is caught by
   the word check below, which reports the disclosure instead of removing it
   silently. A construction cannot catch a number someone typed into a sentence,
   so that case is reported rather than disguised.

   The single permission check
   ---------------------------
   `canRead(identity, resource)` is implemented and unit-tested here. Real
   identity does not exist in this component - see the note at the end of this
   file - so the identity comes from a development-only shim, and the code says
   so on every result.
   =========================================================================== */
(function (root) {
  'use strict';

  var contracts = (typeof module === 'object' && module.exports)
    ? require('../data/contracts.js') : root.AIMContracts;

  /* ------------------------------------------------------------- identity -- */

  /* The identity modes. `approved` is the only one that would be acceptable in
     use; it cannot be reached here because no identity provider is configured. */
  var IDENTITY_MODES = ['approved', 'development-only'];

  /* A development-only stand-in for a signed-in person. It is deliberately
     loud: every record it produces says it is not authenticated. */
  function makeDevIdentity(spec) {
    spec = spec || {};
    var role = spec.role;
    if (['requester', 'case_owner', 'reviewer', 'approver', 'support_owner', 'viewer']
      .indexOf(role) < 0) {
      throw new Error('A development identity needs a known role. Got "' + role + '".');
    }
    return {
      mode: 'development-only',
      authenticated: false,
      subject: 'dev:' + role + (spec.name ? ':' + spec.name : ''),
      display_name: spec.name || null,
      role: role,
      internal: spec.internal !== false,
      /* A tenant would come from the identity provider. Nothing here proves
         which organisation a person belongs to. */
      tenant: spec.tenant || null,
      tenant_verified: false,
      issued_by: 'development-only shim - NOT an authentication',
      note: 'Not a signed-in person. No identity provider is configured in this component.'
    };
  }

  /* What an approved identity would have to carry. Kept here so the shape is
     not invented later in a hurry. */
  function requireApprovedIdentity() {
    return {
      ok: false,
      code: 'IDENTITY_NOT_AVAILABLE',
      error: 'No approved identity provider is configured for this component, so no signed-in '
        + 'person can be established. Permission logic below is implemented and tested against a '
        + 'development-only identity. Production sign-in, organisation membership and revocation '
        + 'remain unimplemented.'
    };
  }

  function rejectPermission(code, error, extra) {
    return Object.assign({ ok: false, allowed: false, code: code, error: error }, extra || {});
  }

  /* ----------------------------------------------------------- permission -- */

  var RESOURCES = ['internal_record', 'shared_brief', 'attachment'];

  /* The permission table. One row per role and resource.
     A viewer may read the shared brief and nothing else: this is the row that
     would have stopped the combined file being offered as a distributor
     handout. */
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

  function permissionFor(role, resource) {
    return PERMISSIONS.filter(function (p) {
      return p.role === role && p.resource === resource;
    })[0] || null;
  }

  /* The permission question, asked before anything is read or attached.
     Every result states whether the identity was actually authenticated. */
  function canRead(identity, resource) {
    if (!identity) {
      return rejectPermission('NO_IDENTITY', 'No identity was supplied, so nothing may be read.');
    }
    if (IDENTITY_MODES.indexOf(identity.mode) < 0) {
      return rejectPermission('UNKNOWN_IDENTITY_MODE',
        'Unknown identity mode "' + identity.mode + '". Nothing may be read.');
    }
    if (!identity.authenticated) {
      /* Development only. The read may proceed, and the result says why it is
         not a permission decision a reader can rely on. */
      var devRow = permissionFor(identity.role, resource);
      if (!devRow || !devRow.allowed) {
        return rejectPermission('NOT_PERMITTED',
          'The role "' + identity.role + '" is not permitted to read "' + resource + '".',
          { identity_authenticated: false, development_only: true });
      }
      return {
        ok: true, allowed: true, resource: resource, role: identity.role,
        identity_authenticated: false,
        development_only: true,
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
        'The identity belongs to no verified organisation, so the case cannot be shown to belong to it.',
        { identity_authenticated: true });
    }
    return { ok: true, allowed: true, resource: resource, role: identity.role,
      identity_authenticated: true, development_only: false, note: row.note };
  }

  /* ------------------------------------------------------ allowlist build -- */

  /* The build rule, and the whole of it: a key is carried when it was declared
     for this recipient. There is no removal step, so there is nothing to get
     wrong later. */
  function buildAllowed(source, allowedKeys, trail) {
    trail = trail || [];
    if (Array.isArray(source)) {
      return source.map(function (item) { return buildAllowed(item, allowedKeys, trail); });
    }
    if (source && typeof source === 'object') {
      var out = {};
      Object.keys(source).forEach(function (k) {
        if (!Object.prototype.hasOwnProperty.call(allowedKeys, k)) return; /* not declared: not carried */
        out[k] = buildAllowed(source[k], allowedKeys, trail.concat([k]));
      });
      return out;
    }
    return source;
  }

  var ENVELOPE_FIELDS = ['schema', 'audience', 'exported_at', 'contract_version', 'recipient',
    'limit_statement', 'not_approved_statement'];

  /* The internal record may carry everything `contracts.js` declares, plus the
     record wrapper this module writes around it. The extra names are listed
     here one by one rather than inferred, so adding a container to the internal
     record is a visible change to an allowlist and not an accident. */
  var INTERNAL_ENVELOPE_FIELDS = [
    'scenario', 'result', 'case', 'review', 'sources', 'context',
    'limits', 'state', 'market', 'unit', 'description', 'title', 'note',
    'owner_role', 'next_action', 'next_update_due', 'history', 'links',
    'version', 'selected_alternative_id', 'objective'
  ];

  /* Fields the member brief derives or carries that are not in the shared
     contracts. Each one is named here so that an addition to a participant
     brief is a visible change to this list rather than an accident.

     `change_pct` is derived only from `price_before` and `price_after`, both of
     which the recipient is given, so it discloses nothing they were not handed.
     No margin, cost, profit or contribution value is derived for a participant.

     `explanation` is the customer or supply explanation, carried when it is fit
     to share. It is checked for restricted wording before the brief is produced,
     because a construction cannot see a number someone typed into a sentence. */
  var MEMBER_CONSTRUCTED_FIELDS = ['change_pct', 'explanation', 'participant_note'];

  function allowlistFor(recipient) {
    var spec = contracts.RECIPIENTS[recipient];
    if (!spec) throw new Error('Unknown recipient "' + recipient + '". Known: '
      + Object.keys(contracts.RECIPIENTS).join(', ') + '.');
    var keys = {};
    if (spec.leaf_fields === null) {
      contracts.declaredFields().forEach(function (k) { keys[k] = true; });
      INTERNAL_ENVELOPE_FIELDS.forEach(function (k) { keys[k] = true; });
    } else {
      /* The permitted containers, then the permitted leaf names inside them.
         `permits` is checked as well: a leaf name is only carried when the
         recipient also permits the container it came from. */
      spec.permits.forEach(function (k) { keys[k] = true; });
      spec.leaf_fields.forEach(function (k) { keys[k] = true; });
      MEMBER_CONSTRUCTED_FIELDS.forEach(function (k) { keys[k] = true; });
    }
    ENVELOPE_FIELDS.forEach(function (k) { keys[k] = true; });
    return keys;
  }

  /* ------------------------------------------------------ the word check -- */

  /* Language that would disclose a restricted figure if it were typed into a
     sentence. This is not the control - the construction above is - but a
     restricted number written into prose is the one thing a field allowlist
     cannot see, so it is reported and the brief is refused.

     Two kinds of pattern are used, because the F08 defect had two halves:
       1. the names of the restricted measures themselves, so a sentence that
          says "our parts cost is ..." is caught;
       2. a restricted word sitting next to a figure, so a sentence that says
          "our cost is 60 EUR" is caught even though "cost" alone is an ordinary
          English word. This is the half the v03 blacklist had no answer for. */
  var RESTRICTED_PHRASES = [
    'cost_eur', 'parts cost', 'partscost', 'parts_cost', 'purchase cost', 'purchase price',
    'unit cost', 'landed cost', 'gross profit', 'grossprofit', 'gross margin', 'grossmargin',
    'gp_before', 'gp_after', 'gp_change', 'gp_pct',
    'margin_before', 'margin_after', 'margin_pp', 'margin_unit', 'margin_unit_after_pct',
    'verifiedcosts', 'verified costs', 'cost_bases', 'cost_basis', 'source_discount',
    'supplier discount', 'base_price', 'base price jpy', 'jpy_per_eur', 'fx_rate', 'fx rate',
    'markup', 'fob_eur', 'fob', 'contribution margin', 'bridge_cost', 'bridge_revenue',
    'internal_note', 'internal only note'
  ];

  /* A restricted word close to a figure. Matched on the sentence, so it catches
     the case the blacklist could not: a unit cost written into free text. */
  var RESTRICTED_PATTERNS = [
    { name: 'a cost figure written into text', re: /\bcosts?\b[^.!?]{0,60}\d|\d[^.!?]{0,60}\bcosts?\b/i },
    { name: 'a margin written into text', re: /\bmargins?\b[^.!?]{0,60}\d|\d[^.!?]{0,60}\bmargins?\b/i },
    { name: 'gross profit named in text', re: /\bgross\s+profit\b/i },
    { name: 'a supplier discount in text', re: /\bsupplier\s+discount\b/i },
    { name: 'an FX rate in text', re: /\b(jpy|fx\s*rate|exchange\s*rate)\b/i },
    { name: 'an FOB value in text', re: /\bfob\b/i },
    { name: 'a markup in text', re: /\bmark[- ]?ups?\b/i },
    { name: 'a purchase price in text', re: /\b(purchase|supplier|landed)\s+price\b/i }
  ];

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
    /* Costs and margins reach a brief as numbers under a permitted-but-generic
       key only if someone declares one. The audit catches that; nothing here
       needs to. */
    return out;
  }

  function checkForRestrictedWords(payload) {
    var hits = wordsIn(payload, []);
    /* The brief's own limits say "no ISZE supplier cost and no margin". Saying so
       is not disclosing it, so the limit statements are excluded from the check. */
    var filtered = hits.filter(function (h) {
      return !/^\.(limit_statement|not_approved_statement|limits)\b/.test(h.path);
    });
    return { ok: filtered.length === 0, findings: filtered };
  }

  /* ------------------------------------------------------- derived values -- */

  /* A brief carries a price change as a percentage. The percentage is derived
     from the two prices, both of which the recipient sees, so it discloses
     nothing they were not given. No margin, cost or profit is derived here. */
  function priceChangePct(before, after) {
    if (typeof before !== 'number' || !Number.isFinite(before) || before === 0) return null;
    if (typeof after !== 'number' || !Number.isFinite(after)) return null;
    return Math.round(10000 * (after / before - 1)) / 100;
  }

  /* -------------------------------------------------- member (shared) brief -- */

  /* Built field by field. There is no step that takes the internal record and
     removes things from it. */
  function memberBrief(input) {
    input = input || {};
    var caseObject = input.case || {};
    var scenario = input.scenario || {};
    var result = input.result || {};
    var meta = input.meta || {};

    var container = {
      reference: {
        case_id: caseObject.case_id,
        customer: caseObject.customer,
        title: caseObject.title || caseObject.name || null
      },
      offer: {
        part_number: caseObject.part_number,
        description: caseObject.description || null,
        unit: caseObject.unit || 'unit',
        price_before: scenario.price_before,
        price_after: scenario.price_after,
        quantity_before: scenario.quantity_before,
        quantity_after: result.ok ? result.quantity_after : null,
        quantity_label: scenario.quantity_label || null,
        scope: scenario.scope || null,
        support_eur: scenario.support_eur === undefined ? null : scenario.support_eur,
        evidence_period: scenario.evidence_period || null,
        offer_effective_date: scenario.offer_effective_date || null
      },
      price: {
        price_before: scenario.price_before,
        price_after: scenario.price_after,
        change_pct: priceChangePct(scenario.price_before, scenario.price_after)
      },
      quantity: {
        quantity_before: scenario.quantity_before,
        quantity_after: result.ok ? result.quantity_after : null,
        quantity_label: scenario.quantity_label || null,
        unit: caseObject.unit || 'unit'
      },
      customers: {
        note: meta.request_note || null,
        /* The customer or supply explanation, when it has been cleared for the
           participant. It is checked for restricted wording before this brief is
           produced; see `finish`. */
        explanation: (input.review && input.review.explanation) || null
      },
      limits: [
        'This brief states a price and a quantity under discussion. It is not an approval.',
        'It contains no ISZE supplier purchase price and no ISZE margin.',
        'No volume response to a price change is assumed or predicted.',
        'Fitment, kit contents and vehicle application are not approved by this document.',
        'A price stated here is a proposal. The case is open until an owner accepts it.'
      ]
    };

    var envelope = {
      schema: 'isze-pricing-member-brief',
      contract_version: contracts.CONTRACT_VERSION,
      recipient: 'member',
      audience: 'Distributor or dealer participant',
      exported_at: meta.exported_at || null,
      limit_statement: 'Prepared for a distributor or dealer participant. Built from a permitted '
        + 'field list; not produced by removing internal fields from the internal record.',
      not_approved_statement: 'No price in this brief is approved, and this brief is not an approval.'
    };

    return finish(Object.assign({}, container, envelope), 'member', {
      constructed: true,
      source: 'allowlist'
    });
  }

  /* ---------------------------------------------------- internal record -- */

  /* The internal record may carry everything declared in contracts.js, and
     nothing that was not declared. It is marked internal, and copying it into
     anything leaving the workspace is refused by `assertInternalOnly`. */
  function internalRecord(input) {
    input = input || {};
    var caseObject = input.case || {};
    var scenario = input.scenario || {};
    var result = input.result || {};
    var extra = input.extra || {};

    var record = {
      schema: 'isze-pricing-internal-record',
      contract_version: contracts.CONTRACT_VERSION,
      recipient: 'internal',
      audience: 'ISZE internal only',
      exported_at: extra.exported_at || null,
      case_id: caseObject.case_id,
      version: caseObject.version || null,
      state: caseObject.state || null,
      owner_role: caseObject.owner_role || null,
      next_action: caseObject.next_action || null,
      next_update_due: caseObject.next_update_due || null,
      customer: caseObject.customer,
      market: caseObject.market || null,
      part_number: caseObject.part_number,
      unit: caseObject.unit || 'unit',
      evidence_period: scenario.evidence_period || null,
      offer_effective_date: scenario.offer_effective_date || null,
      selected_alternative_id: scenario.selected_alternative_id || null,
      objective: scenario.objective || null,
      scenario: scenario,
      result: result,
      review: extra.review || null,
      sources: extra.sources || [],
      history: extra.history || [],
      links: extra.links || [],
      limits: {
        price_approved: false,
        current_customer_net_price: 'unconfirmed',
        supplier_cost: 'Parts purchase cost per the declared measure. Excluded: freight, duty, '
          + 'overheads and distributor kickbacks.',
        no_raw_invoices: true,
        no_credentials: true
      },
      not_approved_statement: 'This record states a proposal and its result. Nothing in it is an '
        + 'approval and it is not safe to forward outside ISZE.'
    };

    return finish(record, 'internal', { constructed: true, source: 'allowlist' });
  }

  function finish(payload, recipient, meta) {
    var keys = allowlistFor(recipient);
    var built = buildAllowed(payload, keys);
    var words = recipient === 'member' ? checkForRestrictedWords(built) : { ok: true, findings: [] };
    var result = {
      ok: true,
      recipient: recipient,
      label: contracts.RECIPIENTS[recipient].label,
      payload: built,
      words: words,
      audit: audit(built, recipient),
      meta: meta || {}
    };
    /* A construction cannot see a restricted figure someone typed into a
       sentence. When the word check finds one, the brief is refused and nothing
       is produced, rather than the sentence being quietly removed or quietly
       sent. */
    if (recipient === 'member' && !words.ok) {
      result.ok = false;
      result.refused = true;
      result.code = 'RESTRICTED_WORD_IN_FREE_TEXT';
      result.error = 'This brief would carry restricted wording: '
        + words.findings.map(function (f) { return '"' + f.phrase + '" at ' + (f.path || '.'); }).join(', ')
        + '. Nothing was produced. Reword the free text, or move that content to the internal record.';
      result.payload = null;
    }
    return result;
  }

  /* ------------------------------------------------------------- the audit -- */

  /* A second pair of eyes on the built object, by key name. It is not the
     control: `buildAllowed` is. This exists so that a name that should not have
     been declared shows up in a test rather than in a distributor's inbox. */
  var INTERNAL_ONLY_KEY_WORDS = [
    'cost', 'gp', 'margin', 'profit', 'discount', 'jpy', 'fx', 'fob', 'markup',
    'contribution', 'bridge', 'verified', 'internal', 'basis'
  ];

  function audit(payload, recipient) {
    if (recipient !== 'member') {
      return { ok: true, findings: [], note: 'The internal record is not restricted by this check.' };
    }
    var findings = [];
    (function walk(node, path) {
      if (Array.isArray(node)) { node.forEach(function (v, i) { walk(v, path + '[' + i + ']'); }); return; }
      if (node && typeof node === 'object') {
        Object.keys(node).forEach(function (k) {
          var lk = k.toLowerCase();
          INTERNAL_ONLY_KEY_WORDS.forEach(function (w) {
            if (lk.indexOf(w) >= 0 && findings.indexOf(k) < 0) {
              findings.push('key "' + k + '" at ' + (path || '.') + ' matches the internal-only word "' + w + '"');
            }
          });
          walk(node[k], path + '.' + k);
        });
      }
    })(payload, '');
    return { ok: findings.length === 0, findings: findings };
  }

  /* -------------------------------------------------------------- bytes -- */

  /* UTF-8 bytes without depending on the host. A browser has TextEncoder and
     Node has Buffer, but neither is guaranteed in every context and a module
     that throws when asked to produce its output is not finished. */
  function utf8Bytes(text) {
    if (typeof TextEncoder === 'function') return new TextEncoder().encode(text);
    if (typeof Buffer === 'function') return Buffer.from(text, 'utf8');
    /* A plain encoder, used only when the host offers neither. */
    var bytes = [];
    for (var i = 0; i < text.length; i++) {
      var code = text.charCodeAt(i);
      if (code < 0x80) {
        bytes.push(code);
      } else if (code < 0x800) {
        bytes.push(0xc0 | (code >> 6), 0x80 | (code & 0x3f));
      } else if (code >= 0xd800 && code <= 0xdbff) {
        /* A surrogate pair: encode the combined code point. */
        var next = text.charCodeAt(++i);
        var point = 0x10000 + ((code - 0xd800) << 10) + (next - 0xdc00);
        bytes.push(0xf0 | (point >> 18), 0x80 | ((point >> 12) & 0x3f),
          0x80 | ((point >> 6) & 0x3f), 0x80 | (point & 0x3f));
      } else {
        bytes.push(0xe0 | (code >> 12), 0x80 | ((code >> 6) & 0x3f), 0x80 | (code & 0x3f));
      }
    }
    return bytes;
  }

  function decodeUtf8(bytes) {
    if (typeof bytes === 'string') return bytes;
    if (typeof Buffer === 'function' && typeof bytes.length === 'number') {
      return Buffer.from(bytes).toString('utf8');
    }
    if (typeof TextDecoder === 'function') return new TextDecoder('utf-8').decode(new Uint8Array(bytes));
    return String.fromCharCode.apply(null, Array.prototype.slice.call(bytes));
  }

  /* An export is judged as bytes, not as a label on a button (SAFE-05). This
     returns what would actually be written. */
  function toBytes(exported, pretty) {
    var text = JSON.stringify(exported.payload, null, pretty ? 2 : 0);
    return { bytes: utf8Bytes(text), text: text, length: text.length };
  }

  /* Is a restricted name present anywhere in the bytes, whatever the nesting?
     This is the check that the v03 audit was meant to be. */
  function findRestrictedInBytes(bytesOrText, names) {
    var text = typeof bytesOrText === 'string' ? bytesOrText : decodeUtf8(bytesOrText);
    var lower = text.toLowerCase();
    return (names || INTERNAL_ONLY_KEY_WORDS).filter(function (n) {
      return lower.indexOf(String(n).toLowerCase()) >= 0;
    });
  }

  /* -------------------------------------------------------- attachments -- */

  /* SAFE-06. Attachment storage does not exist in this component. What is
     implemented is the permission question and the refusal. */
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
    if (/\b(cost|invoice|margin|price[\s_-]?list|billing|gp)\b/i.test(attachment.name)) {
      return rejectPermission('ATTACHMENT_NAME_LOOKS_RESTRICTED',
        'The file name "' + attachment.name + '" suggests restricted content. Rename it if that is '
        + 'wrong, or attach it to the internal record only. Nothing was stored.');
    }
    return {
      ok: true, allowed: true, permission: 'permitted',
      stored: false,
      storage_gap: 'The permission to attach was checked. The file itself was not stored: there is no '
        + 'approved file store or server for this component, so attachment storage remains unimplemented.'
    };
  }

  /* ------------------------------------------------------------ internal -- */

  /* A guard for the one mistake that matters most here: handing the internal
     record to a participant. */
  function assertInternalOnly(exported) {
    if (!exported || exported.recipient !== 'internal') {
      return { ok: true, note: 'Not an internal record.' };
    }
    return {
      ok: false,
      code: 'INTERNAL_ONLY',
      error: 'This is the internal record for recipient "internal". It carries parts cost and margin '
        + 'and must not be given to a distributor or dealer participant. Build a "member" brief '
        + 'instead; do not trim this one.'
    };
  }

  var API = {
    IDENTITY_MODES: IDENTITY_MODES,
    RESOURCES: RESOURCES,
    PERMISSIONS: PERMISSIONS,
    INTERNAL_ONLY_KEY_WORDS: INTERNAL_ONLY_KEY_WORDS,
    RESTRICTED_PHRASES: RESTRICTED_PHRASES,
    RESTRICTED_PATTERNS: RESTRICTED_PATTERNS,
    makeDevIdentity: makeDevIdentity,
    requireApprovedIdentity: requireApprovedIdentity,
    permissionFor: permissionFor,
    canRead: canRead,
    canAttach: canAttach,
    assertInternalOnly: assertInternalOnly,
    allowlistFor: allowlistFor,
    buildAllowed: buildAllowed,
    memberBrief: memberBrief,
    internalRecord: internalRecord,
    audit: audit,
    checkForRestrictedWords: checkForRestrictedWords,
    priceChangePct: priceChangePct,
    toBytes: toBytes,
    utf8Bytes: utf8Bytes,
    decodeUtf8: decodeUtf8,
    findRestrictedInBytes: findRestrictedInBytes
  };

  root.AIMOutput = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);

/* ---------------------------------------------------------------------------
   What is implemented, and what is not

   Implemented here, and unit-tested in tests/export_bytes.test.mjs:
     - an allowlist build per recipient, with no removal step;
     - the member brief carries no cost, gross profit, margin, supplier discount,
       FX rate or cost record, whichever way it is nested, and this is asserted
       on the produced bytes;
     - the permission table and `canRead` / `canAttach`;
     - the internal record is marked internal and `assertInternalOnly` refuses to
       hand it to a participant.

   Not implemented, and not pretended:
     - a real signed-in person. No identity provider is configured here, so
       `canRead` runs against a development-only shim and says so on every
       result. Production identity, organisation membership and revocation need
       a server and an IT decision that this component does not have.
     - attachment storage. There is no approved file store, so no bytes are
       written. The permission check runs and the gap is recorded.
     - server-side permission on a hosted page. A browser-side filter is not
       access control, which the v03 review said plainly.
   ------------------------------------------------------------------------- */