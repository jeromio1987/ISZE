/* ===========================================================================
   Source manifest for every analytical input (DATA-01 / FIN-02).

   What was wrong in v0.3
     There was no single place that said where a number came from. `inputManifest`
     listed six files with a checksum and nothing else - no period, no basis, no
     restricted flag, no pointer into the payload. `packAudit` described the
     acceptance of the source pack in prose. Two half-descriptions of the same
     thing lived in two shapes, and neither could be read by the rest of the app.

   What this does
     One record per analytical input, in one shape, with the six things the
     brief asks for on every record: file, pointer, period, basis, status and
     whether the record is restricted. `inputManifest` and `packAudit` are
     reconciled into it rather than kept beside it, and the reconciliation is
     itself reported, so a record that exists in one description and not the
     other shows up as a gap instead of being silently merged away.

   What it deliberately refuses to do
     It will not invent a period. A record whose source states no period carries
     period_state 'undeclared' and a note saying so. Missing is not zero.

   Restricted handling
     A restricted input is listed here by name, pointer, checksum and shape.
     Its values - supplier purchase costs, live price-list cells, source billing
     lines - are never copied into a manifest record. The manifest is safe to
     version; the payload is not, and payload/*.json is already excluded in
     .gitignore. Reading a restricted file to fingerprint it is opt-in and
     happens only when a caller asks for hashes.

   Entities (DATA-02)
     Distributor, purchasing account and site are three different things and are
     carried as three separate fields. A campaign key is built from all three
     plus the part number, so ITUK and IUK cannot be added together by accident,
     and a site cannot be folded into its distributor.
   =========================================================================== */
(function (root) {
  'use strict';

  var fs = null, crypto = null;
  try { fs = require('node:fs'); } catch (e) { fs = null; }
  try { crypto = require('node:crypto'); } catch (e) { crypto = null; }

  var SEP = '\u001f';   /* unit separator: never appears in a part number or an account */

  /* ---------------------------------------------------------------- helpers -- */

  function isBlank(v) {
    return v === null || v === undefined || (typeof v === 'string' && v.trim() === '');
  }
  function firstDefined() {
    for (var i = 0; i < arguments.length; i++) {
      if (!isBlank(arguments[i])) return arguments[i];
    }
    return null;
  }
  function basename(p) {
    if (typeof p !== 'string' || !p) return null;
    var parts = p.split(/[\\/]/);
    return parts[parts.length - 1];
  }

  /* SHA-256 of a file, or null with a reason. Never throws at the caller. */
  function hashFileSync(filePath) {
    if (!fs || !crypto) {
      return { ok: false, sha256: null, bytes: null,
        error: 'No filesystem in this runtime, so the file could not be fingerprinted.' };
    }
    try {
      var buf = fs.readFileSync(filePath);
      return {
        ok: true, sha256: crypto.createHash('sha256').update(buf).digest('hex'),
        bytes: buf.length, error: null
      };
    } catch (e) {
      return { ok: false, sha256: null, bytes: null,
        error: 'Not readable here: ' + e.message + '. Fingerprint left unresolved rather than guessed.' };
    }
  }

  /* ----------------------------------------------------------------- entity -- */

  /* Three fields, three meanings. A distributor is not an account; an account is
     not a site. ITUK and IUK are separate legal and operational entities and are
     never summed. The same holds for UMI and UTI in Israel: the IDS Israel pack
     is the UMI network and UTI did not participate, so any Israel analysis is
     UMI-only. */
  var ENTITY_SEPARATE_PAIRS = [
    ['ITUK', 'IUK'], ['UMI', 'UTI']
  ];

  function normaliseEntity(entity) {
    entity = entity || {};
    return {
      distributor: firstDefined(entity.distributor, entity.market),
      purchasing_account: firstDefined(entity.purchasing_account, entity.account_key,
        entity.account, entity.sold_to),
      site: firstDefined(entity.site, entity.dealer_site, entity.ship_to)
    };
  }

  function entityKey(entity) {
    var e = normaliseEntity(entity);
    return [e.distributor || '?', e.purchasing_account || '(account not stated)',
      e.site || '(site not stated)'].join(SEP);
  }

  function entityLabel(entity) {
    var e = normaliseEntity(entity);
    return (e.distributor || 'unknown distributor')
      + ' / account ' + (e.purchasing_account || 'not stated')
      + ' / site ' + (e.site || 'not stated');
  }

  /* True when two names are a pair that must never be added together. */
  function isSeparatePair(a, b) {
    if (isBlank(a) || isBlank(b)) return false;
    var x = String(a).toUpperCase(), y = String(b).toUpperCase();
    return ENTITY_SEPARATE_PAIRS.some(function (p) {
      return (p[0] === x && p[1] === y) || (p[0] === y && p[1] === x);
    });
  }

  /* The check every join and every total has to pass before it is allowed. */
  function assertNoBlend(a, b) {
    if (isSeparatePair(a, b)) {
      return { ok: false, separate_entities: true,
        statement: a + ' and ' + b + ' are separate entities. They are reported as two rows and '
          + 'are never combined into one number.' };
    }
    return { ok: true, separate_entities: false,
      statement: 'The two names are not a known separate-entity pair.' };
  }

  /* The unit a comparison is allowed to add up. Different sales stage or
     different unit means a different population, not a bigger one. */
  function campaignKey(parts) {
    parts = parts || {};
    return [
      parts.distributor || '?',
      parts.purchasing_account || '(account not stated)',
      parts.site || '(site not stated)',
      parts.part_number || '(part not stated)',
      parts.unit || '(unit not stated)',
      parts.sales_stage || '(stage not stated)'
    ].join(SEP);
  }

  /* ------------------------------------------------- source entities (DATA-02) -- */

  /* A stable identifier for a source entity: country, distributor and purchasing
     account together. A name alone identifies nothing - the same trading name
     and even the same account number occur in two countries - so two records
     share an identifier only when all three agree. A source's own entity id,
     when it states one, is carried beside the composite, never instead of it. */
  function sourceEntityId(entity) {
    entity = entity || {};
    var e = normaliseEntity(entity);
    return ['entity', firstDefined(entity.country) || '(country not stated)',
      e.distributor || '(distributor not matched)',
      e.purchasing_account || '(account not stated)'].join(SEP);
  }

  /* Group rows by source entity and site. Distinct entities are never added
     together, and a row whose distributor is not matched keeps the name it
     arrived with as its own group rather than being folded into a matched one. */
  function combineEntities(rows) {
    var groups = {}, order = [];
    (rows || []).forEach(function (r) {
      var e = normaliseEntity(r);
      var unmatched = isBlank(e.distributor);
      var key = sourceEntityId(r) + SEP + (e.site || '(site not stated)')
        + (unmatched ? SEP + 'unmatched' + SEP + String(r.raw_name || r.name || '(no name)') : '');
      if (!groups[key]) {
        groups[key] = { entity_id: sourceEntityId(r), country: r.country || null,
          distributor: e.distributor, purchasing_account: e.purchasing_account, site: e.site,
          unmatched: unmatched, name_as_received: unmatched ? (r.raw_name || r.name || null) : null,
          rows: 0, quantity: 0 };
        order.push(key);
      }
      groups[key].rows += 1;
      var q = Number(r.quantity);
      if (Number.isFinite(q)) groups[key].quantity += q;
    });
    var out = order.map(function (k) { return groups[k]; });
    return { groups: out,
      statement: out.length + ' source entit' + (out.length === 1 ? 'y' : 'ies') + ' kept apart. '
        + 'Records are added together only when country, distributor and purchasing account agree; '
        + 'an unmatched name stays a row of its own.' };
  }

  /* Two entities are merged only on a stated source, and a separate-entity pair
     is never merged even then. Sharing a name is not a reason. */
  function canMerge(a, b, declaration) {
    var x = normaliseEntity(a), y = normaliseEntity(b);
    if (isSeparatePair(x.distributor, y.distributor)) {
      return { ok: false, separate_entities: true,
        statement: x.distributor + ' and ' + y.distributor + ' are separate entities and are not merged, '
          + 'whatever a declaration says.' };
    }
    if (sourceEntityId(a) === sourceEntityId(b)) {
      return { ok: true, separate_entities: false, statement: 'The two records are the same source entity.' };
    }
    if (!declaration || isBlank(declaration.source)) {
      return { ok: false, separate_entities: false,
        statement: entityLabel(a) + ' (' + ((a && a.country) || 'country not stated') + ') and '
          + entityLabel(b) + ' (' + ((b && b.country) || 'country not stated') + ') are not merged: '
          + 'no source states they are one entity. A shared name is not that statement.' };
    }
    return { ok: true, separate_entities: false, declared_by: declaration.source,
      declared_on: declaration.declared_on || null,
      statement: 'Merged on the stated source "' + declaration.source + '".' };
  }

  function linkInEffect(link, asOf) {
    if (!link || isBlank(link.source) || isBlank(link.site)) return false;
    if (!isBlank(link.effective_from) && (isBlank(asOf) || String(link.effective_from) > String(asOf))) return false;
    if (!isBlank(link.effective_to) && !isBlank(asOf) && String(link.effective_to) < String(asOf)) return false;
    return true;
  }

  /* An account covering several sites stays combined until effective-dated site
     links, each naming its source, split it into at least two sites. A split
     names the sites; it does not apportion the recorded quantities, because no
     link says how the account's volume divides. */
  function splitAccount(rows, account, links, asOf) {
    var held = (links || []).filter(function (l) {
      return l && String(l.purchasing_account) === String(account) && linkInEffect(l, asOf);
    });
    var sites = [];
    held.forEach(function (l) { if (sites.indexOf(l.site) < 0) sites.push(l.site); });
    if (sites.length < 2) {
      return { ok: false, combined: true, rows: rows, sites: [],
        statement: 'Account ' + account + ' stays combined: '
          + (sites.length ? 'one sourced site link in effect is not a split.'
            : 'no sourced site link in effect on ' + (asOf || 'the stated date') + ' supports a split.') };
    }
    return { ok: true, combined: false, rows: rows, sites: sites, quantity_apportioned: false,
      links: held,
      statement: 'Account ' + account + ' covers ' + sites.length + ' sites on the stated links. The recorded '
        + 'quantities stay on the account; no link states how they divide between the sites.' };
  }

  /* A national record that includes its dealers and a dealer record inside it
     are the same volume twice, so they are never added. */
  function addRecords(a, b) {
    a = a || {}; b = b || {};
    var nat = a.scope === 'national' ? a : b.scope === 'national' ? b : null;
    var dlr = nat === a ? b : a;
    if (nat && dlr.scope === 'dealer' && nat.includes_dealers !== false
      && String(nat.distributor) === String(dlr.distributor) && String(nat.country) === String(dlr.country)
      && String(nat.period) === String(dlr.period)) {
      return { ok: false, total: null,
        statement: 'Not added: the national record for ' + nat.distributor + ' already includes its dealer '
          + 'records, so adding a dealer record counts the same volume twice.' };
    }
    if (sourceEntityId(a) !== sourceEntityId(b) || (a.scope || null) !== (b.scope || null)) {
      return { ok: false, total: null,
        statement: 'Not added: the two records are different entities or different scopes.' };
    }
    return { ok: true, total: Number(a.quantity) + Number(b.quantity),
      statement: 'Added: same entity, same scope.' };
  }

  /* The dealers a national record covers are only those dealer records that
     exist. None is made up from the national figure. */
  function dealersOf(national, dealerRecords) {
    national = national || {};
    var found = (dealerRecords || []).filter(function (d) {
      return d && d.scope === 'dealer' && String(d.distributor) === String(national.distributor)
        && String(d.country) === String(national.country);
    });
    return { dealers: found,
      statement: found.length ? found.length + ' dealer record(s) are held for this national record.'
        : 'No dealer record is held for ' + (national.distributor || 'this distributor') + ' in '
          + (national.country || 'this country') + '. The national figure is not divided into dealers.' };
  }

  /* -------------------------------------------------------------- registry -- */

  /* Every analytical input the component reads. `input_pointer` is where the
     derived input sits in this repository; `payload_pointer` is where the
     resulting records sit in the extracted payload. */
  var INPUTS = [
    {
      reference_id: 'MAN-01',
      title: 'Uploaded ISZE billing to distributor',
      input_file: '01_all_sales_isze_to_distributor.csv',
      manifest_file: '01_all_sales_isze_to_distributor.csv',
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: '/cases[*].series, /cases[*].annual, /cases[*].half',
      record_kind: 'recorded transaction lines, aggregated',
      period: 'Business events 3 January 2023 to 30 June 2026',
      period_state: 'declared',
      basis: 'positive quantities and positive net billed EUR on exact part numbers; '
        + 'credit and return lines excluded and reported separately',
      status: 'accepted for internal review',
      restricted: true,
      restricted_note: 'Source billing lines are restricted. Only aggregates reach a view. '
        + 'Raw line-level billing is never pasted into a shared file or a chat.',
      currency: 'EUR',
      tax_basis: 'net, exclusive of tax',
      sales_stage: 'ISZE to distributor (sell-in)',
      unit: 'part unit (each, kit or set as recorded)',
      entity: { distributor: 'ITUK', purchasing_account: '2575' },
      unresolved: ['July and August 2026 lines exist in the source but are outside the '
        + 'default comparison window, which stays January to June.']
    },
    {
      reference_id: 'MAN-02',
      title: 'Uploaded national sales to dealer',
      input_file: '03_all_sales_to_dealer.csv',
      manifest_file: '03_all_sales_to_dealer.csv',
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: '/cases[*].series[*].onwardQuantity, /cases[*].comparisons[*].current.salesToDealer',
      record_kind: 'recorded wholesale quantities',
      period: 'ITUK: 2023 to August 2026. I Motors: 2025 to August 2026.',
      period_state: 'declared',
      basis: 'network_pn and month rows only; annual control rows and named-dealer rows are '
        + 'not added; signed quantities are retained',
      status: 'accepted for internal review',
      restricted: false,
      restricted_note: null,
      currency: null,
      tax_basis: null,
      sales_stage: 'distributor to dealer, quantities only',
      unit: 'part unit',
      entity: { distributor: 'ITUK / I Motors' },
      unresolved: ['No dealer prices, so no sales-to-dealer value is stated from this input.']
    },
    {
      reference_id: 'MAN-03',
      title: 'Historical market fleet reference',
      input_file: '02_spend_per_truck_by_market.csv',
      manifest_file: '02_spend_per_truck_by_market.csv',
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: '/cases[*].fleet',
      record_kind: 'market context',
      period: 'Calendar 2025 reference',
      period_state: 'declared',
      basis: 'published spend-per-truck basis; ITUK 22,389 trucks and I Motors 8,176 vehicles. '
        + 'These are market totals and are not the applicable fleet for any one part.',
      status: 'context only, not an allocation',
      restricted: false,
      restricted_note: null,
      currency: null,
      tax_basis: null,
      sales_stage: null,
      unit: 'vehicles in service',
      entity: { distributor: 'ITUK / I Motors' },
      unresolved: ['No fleet is allocated to a part, and no 2026 forecast is used.']
    },
    {
      reference_id: 'MAN-04',
      title: 'Supplied Portugal service-category summary',
      input_file: '03_DATA_TABLES.md',
      manifest_file: '03_DATA_TABLES.md',
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: 'referenced by /cases[1].packEvidence',
      record_kind: 'partial classification context',
      period: 'Calendar 2025',
      period_state: 'declared',
      basis: 'supplied summary; blower-filter value is classified as BVP in that summary',
      status: 'partial, does not substitute for an approved part master',
      restricted: false,
      restricted_note: null,
      currency: 'EUR',
      tax_basis: null,
      sales_stage: 'distributor to dealer',
      unit: 'not stated in the summary',
      entity: { distributor: 'I Motors', purchasing_account: '519, 92' },
      unresolved: ['Exact-part analyses are not complete AIM-family totals.']
    },
    {
      reference_id: 'MAN-05',
      title: 'ISUZU and ISZE business context',
      input_file: '01_ISUZU_AND_ISZE_BUSINESS.md',
      manifest_file: '01_ISUZU_AND_ISZE_BUSINESS.md',
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: '/sources[id=CHAIN]',
      record_kind: 'historical method record',
      period: 'Supplied context dated 19 September 2026',
      period_state: 'declared',
      generated_date: '2026-09-19',
      basis: 'the earlier generic reference-chain convention. Removed from price targets in '
        + 'v0.2 because local resale prices, terms and a comparable quotation are not established.',
      status: 'superseded as a method, retained as context',
      restricted: false,
      restricted_note: null,
      currency: null,
      tax_basis: null,
      sales_stage: null,
      unit: null,
      entity: null,
      unresolved: ['No price ceiling is calculated from this convention.']
    },
    {
      reference_id: 'MAN-06',
      title: 'Universe delivery roadmap and pilot operating plan',
      input_file: 'ISUZU_UNIVERSE_DELIVERY_ROADMAP_AND_PILOT_OPERATING_PLAN_2026-09-21.pdf',
      manifest_file: 'ISUZU_UNIVERSE_DELIVERY_ROADMAP_AND_PILOT_OPERATING_PLAN_2026-09-21.pdf',
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: '/sources[id=ROADMAP]',
      record_kind: 'source constraints and product requirements',
      period: '21 September 2026',
      period_state: 'declared',
      generated_date: '2026-09-21',
      basis: 'pages 25-31 retain context and distinguish missing states; page 41 requires dated '
        + 'seller evidence with currency, tax, pack and match status',
      status: 'instruction, not data',
      restricted: false,
      restricted_note: null,
      currency: null,
      tax_basis: null,
      sales_stage: null,
      unit: null,
      entity: null,
      unresolved: ['The later billing extract described in this paper is not the extract attached here.']
    },
    {
      reference_id: 'MAN-07',
      title: 'ISZE AIM pricing decision pack, accepted subset',
      input_file: 'ISZE_AIM_PRICING_DECISION_PACK_2026-09-22.json',
      manifest_file: null,      /* comes from packAudit */
      input_pointer: '01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/',
      payload_pointer: '/packAudit',
      record_kind: 'source pack, accepted in part',
      period: 'Pack dated 22 September 2026; billing reference 30 June 2026',
      period_state: 'declared',
      generated_date: '2026-09-22',
      basis: 'the pack header declares ' + '' + 'rows; the tables hold a different number. '
        + 'The variation is reported below rather than resolved by preferring one figure.',
      status: 'accepted in part for internal review; not price approval',
      restricted: true,
      restricted_note: 'The pack combines restricted cost information with source billing lines. '
        + 'One shared flag on a table is not authority to distribute the whole file.',
      currency: 'EUR',
      tax_basis: 'mixed',
      sales_stage: 'mixed',
      unit: 'mixed',
      entity: null,
      unresolved: ['Header row count and table row count disagree.',
        'Restricted model-cost records, the source invoice line, unverified year-by-order '
        + 'summaries, unrelated dealer rows and automatic derived price floors are excluded.']
    },
    {
      reference_id: 'MAN-08',
      title: 'Verified parts purchase cost, three named bases',
      input_file: null,          /* embedded in the pack, no separate file */
      manifest_file: null,
      input_pointer: null,
      payload_pointer: '/verifiedCosts, /meta/costBases, /costReconciliation',
      record_kind: 'derived supplier purchase cost, restricted',
      period: 'Three bases: historical 1 Oct 2025 to 31 Mar 2026; September 2026 forward '
        + '1 Apr 2026 to 30 Sep 2026; October 2026 forward 1 Oct 2026 to 31 Mar 2027',
      period_state: 'declared',
      basis: 'base price in JPY divided by JPY per EUR and multiplied by the source discount. '
        + 'Parts purchase cost only: freight, duty, overheads and distributor kickbacks are '
        + 'excluded and the invoice discount is not deducted twice. This is not an accounting, '
        + 'landed or moving-average cost.',
      status: 'verified record, not an approved accounting cost',
      restricted: true,
      restricted_note: 'Supplier purchase costs are restricted. The manifest names the fields '
        + 'and never carries a cost value.',
      currency: 'EUR per unit, converted from a JPY base price',
      tax_basis: null,
      sales_stage: null,
      unit: 'part unit as recorded in the cost record',
      entity: null,
      unresolved: ['Two part numbers have no price-file FOB value, so their reconciliation '
        + 'difference is null. A null difference is not a match.',
        'The October 2026 basis carried no end date, so its stated rate window ends 31 March 2027 '
        + 'and is now resolved from that window.']
    },
    {
      reference_id: 'MAN-09',
      title: 'Candidate screen over both pilot ranges',
      input_file: null,
      manifest_file: null,
      input_pointer: null,
      payload_pointer: '/candidateScreen',
      record_kind: 'derived screening rows',
      period: null,
      period_state: 'undeclared',
      basis: 'proposed screen: at least EUR 1,000 observed billing reduction, positive billed '
        + 'quantities in both periods, a higher weighted unit price and a lower quantity, run '
        + 'separately on CY2025/CY2024 and H1 2026/H1 2025. It is a proposed rule and not an '
        + 'approved commercial threshold.',
      status: 'screening rows, not approved decisions',
      restricted: true,
      restricted_note: 'The rows carry a restricted cost column. Coverage figures may be shown; '
        + 'the cost values may not leave the internal area.',
      currency: 'EUR',
      tax_basis: null,
      sales_stage: 'ISZE to distributor',
      unit: 'part unit',
      entity: { distributor: 'ITUK / I Motors' },
      unresolved: ['The records carry no reporting period, and none has been inferred from '
        + 'similar-looking values.',
        'The screen totals are not comparable with the worked case periods.']
    },
    {
      reference_id: 'MAN-10',
      title: 'Dated competitor and retailer observations',
      input_file: null,
      manifest_file: null,
      input_pointer: null,
      payload_pointer: '/offers',
      record_kind: 'dated external price observations',
      period: 'Retrieval dates recorded per observation; pack dated 22 September 2026',
      period_state: 'partial',
      basis: 'public listings as retrieved, each with its own match statement, currency, tax '
        + 'status and freshness note. These are evidence and not truth.',
      status: 'evidence only. No current quotation, no approved net price index.',
      restricted: false,
      restricted_note: null,
      currency: 'as recorded per observation (EUR and GBP appear)',
      tax_basis: 'not declared on some observations; null where it is not stated',
      sales_stage: 'retail or advertised price, a different price level from a list price '
        + 'and from an observed billing average',
      unit: 'as recorded per observation (kit, each)',
      entity: null,
      unresolved: ['Kit contents are unverified, so product equivalence is not established.',
        'One seller offering several brands is not several independent competitors.']
    },
    {
      reference_id: 'MAN-11',
      title: 'Part relationships, catalogue pairing and supersession',
      input_file: 'pn_supersession_map.csv',
      manifest_file: null,
      additional_files: ['price_file_2026_pn_newest.csv'],
      input_pointer: '01_data/01_Pricing/',
      payload_pointer: '/cases[*].packEvidence.relationships',
      record_kind: 'part relationship records',
      period: 'Current price file revision, 2026',
      period_state: 'declared',
      basis: 'declared catalogue pairing and declared newest number. Technical approval to fit '
        + 'is a separate field and is not established by a relationship existing. A supersession '
        + 'map states which number replaced which; it is not a fitment decision.',
      status: 'provenance exposed, fitment not approved',
      restricted: false,
      restricted_note: null,
      currency: null,
      tax_basis: null,
      sales_stage: null,
      unit: null,
      entity: null,
      unresolved: ['No fitment approval is claimed for any pair.',
        'The disc predecessor is recorded in a newest-number field, which is not technical approval.']
    }
  ];

  /* Which payload array feeds records this component may not fingerprint from
     disk, and how many records it holds. */
  var RESTRICTED_FILES = ['payload/*.json', 'reference/*.html'];

  /* ---------------------------------------------------------------- clocks -- */

  /* Three clocks, never merged: when the source was generated, which period it
     observes, and the date an offer would take effect. A missing clock stays
     missing; none is filled from another. */
  function clocksFor(rec, opts) {
    opts = opts || {};
    return {
      generated_date: isBlank(rec.generated_date) ? null : rec.generated_date,
      observation_period: isBlank(rec.period) ? null : rec.period,
      observation_period_state: rec.period_state || 'undeclared',
      offer_date: isBlank(opts.offer_effective_date) ? null : opts.offer_effective_date,
      statement: 'Generation date, observation period and offer date are separate. '
        + 'A missing one is left empty and is not taken from another.'
    };
  }

  function periodDeclared(rec) {
    return !!rec && rec.period_state === 'declared' && !isBlank(rec.period);
  }

  /* What a manifest record may be used for. Any record can be inspected; only a
     record with a declared period can support a dated change claim. */
  function claimSupport(rec, claim) {
    if (!rec) {
      return { claim: claim, allowed: false, code: 'NO_RECORD', validation_state: null,
        statement: 'There is no manifest record, so nothing can be claimed from it.' };
    }
    var declared = periodDeclared(rec);
    var validation = declared ? 'period declared' : 'unvalidated';
    if (claim === 'inspect') {
      return { claim: claim, allowed: true, code: null, validation_state: validation,
        statement: declared ? 'The source can be inspected; its period is declared.'
          : 'The source can be inspected as unvalidated data. It states no period.' };
    }
    if (claim === 'dated_change') {
      if (declared) {
        return { claim: claim, allowed: true, code: null, validation_state: validation,
          statement: 'The source declares its period, so it can support a dated change claim.' };
      }
      return { claim: claim, allowed: false, code: 'PERIOD_UNDECLARED', validation_state: validation,
        statement: 'The source states no period, so it cannot support a dated change claim. '
          + 'No period is inferred from similar totals.' };
    }
    return { claim: claim, allowed: false, code: 'UNKNOWN_CLAIM', validation_state: validation,
      statement: 'This claim type is not one the manifest can support.' };
  }

  /* ------------------------------------------------------------- reconcile -- */

  function build(payload, opts) {
    opts = opts || {};
    payload = payload || {};
    var meta = payload.meta || {};
    var audit = payload.packAudit || {};
    var declared = payload.inputManifest || [];

    var records = INPUTS.map(function (base) {
      var rec = {};
      Object.keys(base).forEach(function (k) { rec[k] = base[k]; });
      rec.source_file = firstDefined(base.source_file, base.manifest_file, base.input_file);
      rec.file = basename(rec.source_file);
      rec.additional_files = (base.additional_files || []).slice();
      rec.sha256 = null;
      rec.bytes = null;
      rec.hash_status = 'not fingerprinted';
      rec.hash_source = null;
      rec.record_count = null;
      rec.declared_count = null;
      rec.count_variance = null;
      rec.count_state = 'not applicable';
      rec.supersedes = null;
      rec.superseded_by = null;
      rec.unresolved = (base.unresolved || []).slice();
      rec.reconciliation = [];
      rec.merge_status = 'manifest only';
      rec.generated_date = isBlank(base.generated_date) ? null : base.generated_date;
      rec.supplying_entity = firstDefined(base.supplying_entity,
        base.entity ? entityLabel(base.entity) : null);
      rec.source_meaning = firstDefined(base.source_meaning, base.record_kind);
      rec.version = firstDefined(base.version);
      rec.coverage = firstDefined(base.coverage);
      rec.exclusions = firstDefined(base.exclusions);
      rec.controls = firstDefined(base.controls);
      rec.permitted_use = firstDefined(base.permitted_use, base.status);
      return rec;
    });

    function byFile(name) {
      return records.filter(function (r) {
        return r.file && name && r.file.toLowerCase() === String(name).toLowerCase();
      })[0] || null;
    }

    /* Join the declared input manifest onto the records, by file name. */
    declared.forEach(function (d) {
      var rec = byFile(d.file);
      if (!rec) {
        records.push({
          reference_id: 'MAN-EXT-' + records.length,
          title: 'Declared input with no analytical record',
          input_file: d.file, manifest_file: d.file, source_file: d.file,
          file: basename(d.file),
          input_pointer: null, payload_pointer: null,
          record_kind: 'declared only',
          period: null, period_state: 'undeclared',
          basis: null,
          status: 'declared in inputManifest and not reconciled to any analytical record',
          restricted: RESTRICTED_FILES.some(function (p) { return String(d.file).indexOf('payload') >= 0; }),
          restricted_note: null,
          currency: null, tax_basis: null, sales_stage: null, unit: null, entity: null,
          sha256: d.sha256 || null, bytes: d.bytes || null,
          hash_status: d.sha256 ? 'declared checksum' : 'not fingerprinted',
          hash_source: 'inputManifest',
          record_count: null, declared_count: null, count_variance: null,
          count_state: 'not applicable',
          supersedes: null, superseded_by: null,
          unresolved: ['This file is declared as an input but no record in the manifest consumes it.'],
          reconciliation: [],
          merge_status: 'declared only - not consumed'
        });
        return;
      }
      rec.declared_count = null;
      if (d.sha256) {
        rec.sha256 = d.sha256;
        rec.bytes = d.bytes || null;
        rec.hash_status = 'declared checksum';
        rec.hash_source = 'inputManifest';
      }
      rec.reconciliation.push('Matched on file name to an inputManifest entry of '
        + (d.bytes || 'unknown') + ' bytes.');
      rec.merge_status = 'reconciled';
    });

    /* The pack audit is a 12th input: the accepted subset itself. */
    var packRec = byFile(audit.inputFile);
    if (packRec) {
      packRec.record_count = audit.actualRows === undefined ? null : audit.actualRows;
      packRec.declared_count = audit.declaredRows === undefined ? null : audit.declaredRows;
      if (packRec.record_count !== null && packRec.declared_count !== null) {
        packRec.count_variance = packRec.record_count - packRec.declared_count;
        packRec.count_state = packRec.count_variance === 0 ? 'agrees'
          : 'disagrees - reported, not reconciled away';
      }
      if (audit.inputSHA256) {
        packRec.sha256 = audit.inputSHA256;
        packRec.hash_status = 'declared checksum';
        packRec.hash_source = 'packAudit';
      }
      packRec.record_kind = audit.acceptedStatus || packRec.record_kind;
      packRec.reconciliation.push('packAudit declares ' + (audit.declaredRows === undefined ? '?' : audit.declaredRows)
        + ' rows; the twelve tables hold ' + (audit.actualRows === undefined ? '?' : audit.actualRows)
        + '. The difference is reported and the header figure is not preferred.');
      packRec.basis = String(packRec.basis).replace('the pack header declares rows;',
        'the pack header declares ' + (audit.declaredRows === undefined ? 'an unstated number of' : audit.declaredRows) + ' rows;');
      packRec.merge_status = 'reconciled';
    }

    /* Table-level counts, so a record count is never guessed. */
    var counts = audit.counts || {};
    var countTotal = 0;
    Object.keys(counts).forEach(function (k) {
      if (Number.isFinite(Number(counts[k]))) countTotal += Number(counts[k]);
    });

    /* Per-input record counts that the payload can actually be counted from. */
    var countedFromPayload = [
      ['MAN-08', (payload.verifiedCosts || []).length],
      ['MAN-09', (payload.candidateScreen || []).length],
      ['MAN-10', Object.keys(payload.offers || {}).length],
      ['MAN-11', totalRelationships(payload)]
    ];
    countedFromPayload.forEach(function (pair) {
      var rec = records.filter(function (r) { return r.reference_id === pair[0]; })[0];
      if (!rec) return;
      rec.record_count = pair[1];
      rec.count_state = 'counted from the payload';
    });

    records.forEach(function (r) {
      r.validation_state = periodDeclared(r) ? 'period declared' : 'unvalidated';
      r.clocks = clocksFor(r, opts);
    });

    var manifest = {
      manifest_version: 1,
      built_at: opts.built_at || null,
      payload_version: meta.version || null,
      payload_build_date: meta.buildDate || null,
      audience: meta.audience || null,
      pack_date: audit.packDate || null,
      record_count: records.length,
      restricted_record_count: records.filter(function (r) { return r.restricted === true; }).length,
      records: records,
      reconciliation: {
        inputs_declared: declared.length,
        analytical_records: INPUTS.length + 1,
        reconciled: records.filter(function (r) { return r.merge_status === 'reconciled'; }).length,
        manifest_only: records.filter(function (r) { return r.merge_status === 'manifest only'; }).length,
        declared_only: records.filter(function (r) { return r.merge_status === 'declared only - not consumed'; }).length,
        pack_tables: Object.keys(counts).length,
        pack_rows_counted: countTotal,
        pack_rows_declared: audit.declaredRows === undefined ? null : audit.declaredRows,
        pack_rows_actual: audit.actualRows === undefined ? null : audit.actualRows,
        pack_row_variance: (audit.declaredRows === undefined || audit.actualRows === undefined)
          ? null : audit.actualRows - audit.declaredRows,
        statement: 'One manifest now describes every analytical input. `inputManifest` and '
          + '`packAudit` have been reconciled into it, and the differences between them are '
          + 'reported as differences rather than resolved by preferring one figure.'
      },
      restricted_handling: {
        rule: 'A restricted input is listed by file, pointer, checksum and shape. Its values are '
          + 'never copied into the manifest.',
        excluded_paths: RESTRICTED_FILES,
        versioned_reason: 'payload/*.json and reference/*.html are the only files that carry '
          + 'supplier purchase costs and live price-list cells, and both are already excluded '
          + 'from version control by .gitignore.'
      },
      entities: {
        rule: 'Distributor, purchasing account and site are three separate fields. A campaign '
          + 'key is built from all three plus the part number, unit and sales stage.',
        separate_pairs: ENTITY_SEPARATE_PAIRS.map(function (p) { return p.slice(); }),
        known_entities: knownEntities(payload),
        naming_as_it_appears: distributorNaming(payload)
      }
    };

    return manifest;
  }

  function totalRelationships(payload) {
    var n = 0;
    (payload.cases || []).forEach(function (c) {
      var rel = (c.packEvidence && c.packEvidence.relationships) || [];
      n += rel.length;
    });
    return n;
  }

  function knownEntities(payload) {
    var seen = {};
    (payload.cases || []).forEach(function (c) {
      if (c.market) seen[c.market] = true;
      if (c.customer) seen[c.customer] = true;
    });
    (payload.candidateScreen || []).forEach(function (r) {
      if (r.distributor) seen[r.distributor] = true;
    });
    return Object.keys(seen).sort();
  }

  /* The payload names one distributor in more than one way, and uses a country
     name where a distributor name is expected. None of that is merged away
     here. The names are listed as they appear, with where they appear and what
     the field is being used for, so a reader can see the inconsistency instead of
     inheriting it. Nothing is renamed: a rename would be an invention, and a
     silent merge would blend two different populations. */
  function distributorNaming(payload) {
    payload = payload || {};
    var labels = {};

    function note(label, where, field) {
      if (isBlank(label)) return;
      if (!labels[label]) labels[label] = { label: label, appears_as: [], fields: [] };
      if (labels[label].appears_as.indexOf(where) < 0) labels[label].appears_as.push(where);
      if (labels[label].fields.indexOf(field) < 0) labels[label].fields.push(field);
    }

    (payload.cases || []).forEach(function (c) {
      note(c.market, 'a case market', 'market');
      note(c.customer, 'a case customer', 'customer');
    });
    (payload.alternatives && typeof payload.alternatives === 'object'
      ? Object.keys(payload.alternatives) : []).forEach(function (k) {
      var m = String(k).match(/^([A-Z]+)-/);
      if (m) note(m[1], 'an alternative id prefix', 'alternative_id');
    });
    (payload.candidateScreen || []).forEach(function (r) {
      note(r.distributor, 'a candidate screen row', 'distributor');
    });

    var names = Object.keys(labels).map(function (k) { return labels[k]; }).sort();
    var pairs = [];
    for (var i = 0; i < names.length; i++) {
      for (var j = i + 1; j < names.length; j++) {
        if (isSeparatePair(names[i].label, names[j].label)) {
          pairs.push({ a: names[i].label, b: names[j].label,
            statement: names[i].label + ' and ' + names[j].label + ' are separate entities and are '
              + 'never summed into one figure.' });
        }
      }
    }
    var countryAsDistributor = names.filter(function (n) {
      return n.appears_as.indexOf('a candidate screen row') >= 0
        && n.appears_as.some(function (w) { return w.indexOf('case market') >= 0; });
    }).map(function (n) { return n.label; });

    return {
      names_as_they_appear: names,
      separate_entity_pairs: pairs,
      country_name_used_where_a_distributor_is_expected: countryAsDistributor,
      statement: names.length + ' distributor or market label(s) appear in this payload: '
        + names.map(function (n) { return n.label + ' (' + n.fields.join(', ') + ')'; }).join('; ')
        + '. They are carried as the source states them and are never merged. '
        + (pairs.length ? pairs.length + ' separate-entity pair(s) present. ' : '')
        + (countryAsDistributor.length
            ? 'The candidate rows name ' + countryAsDistributor.join(', ') + ' as the distributor, '
              + 'which is a country name where a distributor name is expected. It is reported, not '
              + 'silently rewritten, because the source does not state which legal entity that is.'
            : '')
    };
  }

  /* -------------------------------------------------------- safe to share -- */

  /* A manifest record is safe to move around: it describes data, it does not
     contain restricted values. The check exists so that "safe" is a claim the
     code makes, not one the reader assumes. */
  function restrictedRecords(manifest) {
    return (manifest.records || []).filter(function (r) { return r.restricted === true; });
  }

  function assertShippable(manifest, opts) {
    opts = opts || {};
    var findings = [];
    (manifest.records || []).forEach(function (r) {
      if (!r.restricted) return;
      ['cost_eur', 'price', 'amount', 'billing_eur', 'jpy_per_eur'].forEach(function (f) {
        if (r[f] !== undefined && r[f] !== null) {
          findings.push('Restricted record ' + r.reference_id + ' carries a value in field "' + f + '".');
        }
      });
    });
    return {
      ok: findings.length === 0,
      findings: findings,
      statement: findings.length === 0
        ? 'The manifest describes restricted inputs without carrying their values.'
        : 'The manifest carries values from a restricted input and must not be shared.'
    };
  }

  /* --------------------------------------------------------------- loading -- */

  /* Fingerprint the files named by the manifest that are readable here. Off by
     default: a fingerprint of a restricted file is allowed, a read of its
     content into a view is not. */
  function fingerprintFiles(manifest, basePath, opts) {
    opts = opts || {};
    var out = { attempted: 0, fingerprinted: 0, unresolved: [] };
    (manifest.records || []).forEach(function (r) {
      if (!r.file) return;
      if (r.restricted) {
        r.reconciliation.push('Not fingerprinted: this input is restricted, so reading it to take '
          + 'a hash is left as an explicit opt-in rather than done by default.');
        if (!(opts.include_restricted && opts.restricted_base_path)) return;
        var rres = hashFileSync(require$pathJoin(opts.restricted_base_path, r.file));
        if (rres.ok) {
          r.sha256 = rres.sha256; r.bytes = rres.bytes;
          r.hash_status = 'fingerprinted on this machine under an explicit restricted opt-in';
          out.attempted += 1; out.fingerprinted += 1;
        } else {
          out.attempted += 1;
          out.unresolved.push({ reference_id: r.reference_id, file: r.file, reason: rres.error });
        }
        return;
      }
      out.attempted += 1;
      var res = hashFileSync(basePath ? require$pathJoin(basePath, r.file) : r.file);
      if (res.ok) {
        r.sha256 = res.sha256;
        r.bytes = res.bytes;
        r.hash_status = 'fingerprinted on this machine';
        r.hash_source = 'local file';
        out.fingerprinted += 1;
      } else {
        r.hash_status = 'unresolved';
        r.reconciliation.push(res.error);
        out.unresolved.push({ reference_id: r.reference_id, file: r.file, reason: res.error });
      }
    });
    return out;
  }

  function require$pathJoin(base, file) {
    if (/[\\/]$/.test(base)) return base + file;
    return base + (base.indexOf('\\') >= 0 ? '\\' : '/') + file;
  }

  function find(manifest, referenceId) {
    return (manifest.records || []).filter(function (r) {
      return r.reference_id === referenceId;
    })[0] || null;
  }

  /* A conservation check for the manifest itself: every declared input is
     accounted for, and no record silently disappeared in the merge. */
  function conservation(manifest) {
    var rec = manifest.reconciliation || {};
    var findings = [];
    var accounted = (rec.reconciled || 0) + (rec.manifest_only || 0) + (rec.declared_only || 0);
    if (accounted !== (manifest.records || []).length) {
      findings.push('Manifest merge lost or duplicated a record: ' + accounted
        + ' accounted for against ' + (manifest.records || []).length + ' present.');
    }
    if (rec.pack_rows_declared !== null && rec.pack_rows_declared !== undefined
        && rec.pack_rows_counted !== null && rec.pack_rows_counted !== rec.pack_rows_declared) {
      findings.push('The pack header declares ' + rec.pack_rows_declared + ' rows and the tables '
        + 'hold ' + rec.pack_rows_counted + ' rows. Reported, not reconciled.');
    }
    return {
      ok: findings.length === 0,
      findings: findings,
      totals: { records: (manifest.records || []).length, accounted_for: accounted,
        restricted: manifest.restricted_record_count || 0 },
      statement: findings.length === 0
        ? 'Every declared input is accounted for in the manifest.'
        : 'The manifest reports ' + findings.length + ' difference(s) rather than hiding them.'
    };
  }

  var API = {
    INPUTS: INPUTS,
    build: build,
    find: find,
    claimSupport: claimSupport,
    clocksFor: clocksFor,
    conservation: conservation,
    restrictedRecords: restrictedRecords,
    assertShippable: assertShippable,
    fingerprintFiles: fingerprintFiles,
    hashFileSync: hashFileSync,
    normaliseEntity: normaliseEntity,
    entityKey: entityKey,
    entityLabel: entityLabel,
    isSeparatePair: isSeparatePair,
    assertNoBlend: assertNoBlend,
    campaignKey: campaignKey,
    sourceEntityId: sourceEntityId,
    combineEntities: combineEntities,
    canMerge: canMerge,
    splitAccount: splitAccount,
    addRecords: addRecords,
    dealersOf: dealersOf,
    knownEntities: knownEntities,
    distributorNaming: distributorNaming,
    SEP: SEP
  };

  root.AIMManifest = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
