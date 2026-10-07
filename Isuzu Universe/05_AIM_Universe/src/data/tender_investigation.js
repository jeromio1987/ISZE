/* ===========================================================================
   CONNECT-07 - Connect the existing tender feed to an owned investigation.

   Read an authorised tender-feed entry (source, date, known deadline, relevance)
   and link it to a case investigation. States: reviewed, pursue, decline,
   support_requested, support_decided, bid_submitted, known_outcome.

   An expired or cancelled notice is never a current actionable deadline. An
   award never automatically creates billing, gross profit or a won parts
   quotation. Notice value is never translated into Isuzu parts revenue.

   Synthetic fixtures in tests. Live feed path is read-only and never written
   from this module. Nordics tender API keys are closed and not asked about.
   =========================================================================== */
(function (root) {
  'use strict';

  var INVESTIGATION_STATES = [
    'reviewed',
    'pursue',
    'decline',
    'support_requested',
    'support_decided',
    'bid_submitted',
    'known_outcome'
  ];

  var NON_ACTIONABLE_LIFECYCLES = {
    expired: true,
    cancelled: true,
    canceled: true,
    withdrawn: true
  };

  function deepClone(value) {
    return JSON.parse(JSON.stringify(value == null ? null : value));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function lower(v) {
    var s = name(v);
    return s ? s.toLowerCase() : '';
  }

  function investigationsOf(caseRecord) {
    return Array.isArray(caseRecord && caseRecord.tender_investigations)
      ? caseRecord.tender_investigations.map(function (x) { return deepClone(x); })
      : [];
  }

  function snapshotNotice(notice) {
    notice = notice || {};
    return {
      opportunity_id: name(notice.opportunity_id),
      title: name(notice.title),
      buyer: name(notice.buyer),
      country: name(notice.country),
      deadline_date: name(notice.deadline_date),
      published_latest: name(notice.published_latest) || name(notice.published_first),
      lifecycle: name(notice.lifecycle),
      notice_type: name(notice.notice_type),
      outcome: name(notice.outcome),
      value_amount: notice.value_amount == null ? null : Number(notice.value_amount),
      currency: name(notice.currency),
      source: name(notice.source) || 'tender_feed',
      url: name(notice.url),
      /* Explicit: notice money is not Isuzu parts revenue. */
      value_as_parts_revenue: null
    };
  }

  function isNonActionable(notice, asOf) {
    var life = lower(notice && notice.lifecycle);
    if (NON_ACTIONABLE_LIFECYCLES[life]) {
      return { non_actionable: true, reason: 'lifecycle:' + life };
    }
    var outcome = lower(notice && notice.outcome);
    if (outcome === 'cancelled' || outcome === 'canceled' || outcome === 'expired') {
      return { non_actionable: true, reason: 'outcome:' + outcome };
    }
    var deadline = name(notice && notice.deadline_date);
    var day = name(asOf);
    if (deadline && day && deadline < day && (life === 'expired' || life === '' || life === 'unknown')) {
      /* Past deadline alone is not enough when lifecycle still says competition;
         only treat as expired when lifecycle already says so, or when caller
         marked expired. Past dates with active competition stay actionable until
         marked expired/cancelled. */
    }
    if (deadline && day && life === 'expired') {
      return { non_actionable: true, reason: 'lifecycle:expired' };
    }
    return { non_actionable: false, reason: null };
  }

  /* Current actionable deadline view for one notice. */
  function actionableDeadline(notice, options) {
    options = options || {};
    notice = notice || {};
    var asOf = name(options.as_of);
    var check = isNonActionable(notice, asOf);
    if (check.non_actionable) {
      return {
        ok: true,
        actionable: false,
        deadline_date: name(notice.deadline_date),
        lifecycle: name(notice.lifecycle),
        as_of: asOf,
        statement: 'An expired/cancelled notice cannot be shown as a current actionable deadline.'
      };
    }
    return {
      ok: true,
      actionable: true,
      deadline_date: name(notice.deadline_date),
      lifecycle: name(notice.lifecycle),
      as_of: asOf,
      statement: 'Deadline remains actionable on the recorded notice.'
    };
  }

  /* Attach a tender-feed entry to an owned investigation on the case. */
  function attachTenderInvestigation(caseRecord, notice, options) {
    caseRecord = caseRecord || {};
    options = options || {};
    var snap = snapshotNotice(notice);
    if (!snap.opportunity_id) {
      return {
        ok: false,
        error: 'A tender investigation needs an opportunity_id from the feed.',
        case_record: caseRecord
      };
    }

    var state = name(options.state) || 'reviewed';
    if (INVESTIGATION_STATES.indexOf(state) < 0) {
      return {
        ok: false,
        error: 'Unknown investigation state "' + state + '". Known: ' + INVESTIGATION_STATES.join(', ') + '.',
        case_record: caseRecord
      };
    }

    var asOf = name(options.as_of) || (name(options.attached_at) || '').slice(0, 10) || null;
    var deadline = actionableDeadline(snap, { as_of: asOf });

    var list = investigationsOf(caseRecord);
    var investigation = {
      investigation_id: name(options.investigation_id) || ('TI-' + (list.length + 1)),
      owner: name(options.owner) || null,
      state: state,
      attached_at: name(options.attached_at),
      known_outcome: name(options.known_outcome),
      support_requested: options.support_requested === true,
      support_decided: options.support_decided === true,
      bid_submitted: options.bid_submitted === true || state === 'bid_submitted',
      notice: snap,
      actionable_deadline: deadline.actionable === true,
      /* Never invent Isuzu parts revenue from notice value. */
      isuzu_parts_revenue_eur: null,
      relevance: name(options.relevance),
      source_date: snap.published_latest,
      known_deadline: snap.deadline_date
    };
    list.push(investigation);

    var next = Object.assign({}, caseRecord, {
      tender_investigations: list
    });
    /* Do not write isuzu_parts_revenue_eur onto the case from notice value. */

    return {
      ok: true,
      investigation: investigation,
      case_record: next,
      statement: 'Tender notice attached to an owned investigation. Notice value is not Isuzu parts revenue.'
    };
  }

  /* An award record does not create billing, GP or a won quotation by itself. */
  function awardFinancialEffects(investigation) {
    investigation = investigation || {};
    var notice = investigation.notice || {};
    return {
      ok: true,
      auto_created: false,
      billing: null,
      gross_profit: null,
      won_parts_quotation: null,
      isuzu_parts_revenue_eur: null,
      notice_value_amount: notice.value_amount == null ? null : notice.value_amount,
      notice_currency: notice.currency || null,
      statement: 'An award cannot automatically create billing, gross profit or a won parts quotation.'
    };
  }

  var API = {
    INVESTIGATION_STATES: INVESTIGATION_STATES.slice(),
    actionableDeadline: actionableDeadline,
    attachTenderInvestigation: attachTenderInvestigation,
    awardFinancialEffects: awardFinancialEffects,
    snapshotNotice: snapshotNotice
  };

  root.AIMTenderInvestigation = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
