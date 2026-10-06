/* ===========================================================================
   CONNECT-05 - Create a dated availability question and response.

   Carry selected part, application where established, quantity and required date
   into a supply question through the distributor. Store source, observation time
   and meaning of any response. Separate estimated date, confirmed commitment,
   allocated, dispatched and delivered. Existing urgent procedures are unchanged.

   A historical purchase is recorded as its own meaning and is never displayed as
   current stock availability. A response without confirmation is always labelled
   an estimate and keeps a next-update obligation.

   Synthetic fixtures only. No send, no real stock file, no invented dealer stock.
   =========================================================================== */
(function (root) {
  'use strict';

  var RESPONSE_MEANINGS = [
    'estimated_date',
    'confirmed_commitment',
    'allocated',
    'dispatched',
    'delivered'
  ];

  function deepClone(value) {
    return JSON.parse(JSON.stringify(value == null ? null : value));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function questionsOf(caseRecord) {
    return Array.isArray(caseRecord && caseRecord.availability_questions)
      ? caseRecord.availability_questions.map(function (q) { return deepClone(q); })
      : [];
  }

  function purchasesOf(caseRecord) {
    return Array.isArray(caseRecord && caseRecord.historical_purchases)
      ? caseRecord.historical_purchases.map(function (p) { return deepClone(p); })
      : [];
  }

  /* Open a dated supply question on the case. Nothing is sent. */
  function createAvailabilityQuestion(caseRecord, selection, options) {
    caseRecord = caseRecord || {};
    selection = selection || {};
    options = options || {};

    var part = name(selection.part_number);
    var qty = selection.quantity;
    var required = name(selection.required_date);
    if (!part) {
      return { ok: false, error: 'A supply question needs a selected part.', case_record: caseRecord };
    }
    if (qty == null || !(Number(qty) > 0)) {
      return { ok: false, error: 'A supply question needs a positive quantity.', case_record: caseRecord };
    }
    if (!required) {
      return { ok: false, error: 'A supply question needs a required date.', case_record: caseRecord };
    }

    var list = questionsOf(caseRecord);
    var questionId = name(options.question_id) || ('AQ-' + (list.length + 1));
    var question = {
      question_id: questionId,
      part_number: part,
      application: name(selection.application),
      quantity: Number(qty),
      required_date: required,
      distributor_route: name(selection.distributor_route),
      asked_at: name(options.asked_at) || null,
      asked_by: name(options.asked_by) || null,
      response: null,
      sent: false
    };
    list.push(question);

    var next = Object.assign({}, caseRecord, {
      availability_questions: list,
      historical_purchases: purchasesOf(caseRecord)
    });

    return {
      ok: true,
      question: question,
      case_record: next,
      statement: 'Dated availability question recorded on the case. Nothing was sent.'
    };
  }

  /* Historical purchase is its own meaning. It is never current stock. */
  function recordHistoricalPurchase(caseRecord, purchase) {
    caseRecord = caseRecord || {};
    purchase = purchase || {};
    var part = name(purchase.part_number);
    if (!part) {
      return { ok: false, error: 'Historical purchase needs a part number.', case_record: caseRecord };
    }

    var list = purchasesOf(caseRecord);
    var row = {
      purchase_id: name(purchase.purchase_id) || ('HP-' + (list.length + 1)),
      part_number: part,
      purchased_on: name(purchase.purchased_on),
      quantity: purchase.quantity == null ? null : Number(purchase.quantity),
      source: name(purchase.source),
      observation_time: name(purchase.observation_time),
      meaning: 'historical_purchase',
      displayed_as_current_stock: false
    };
    list.push(row);

    var next = Object.assign({}, caseRecord, {
      historical_purchases: list,
      availability_questions: questionsOf(caseRecord)
    });

    return {
      ok: true,
      purchase: row,
      case_record: next,
      statement: 'Historical purchase recorded. It is not current stock availability.'
    };
  }

  /* Current stock view: historical purchases never count as available stock. */
  function currentStockAvailability(caseRecord, options) {
    options = options || {};
    caseRecord = caseRecord || {};
    var part = name(options.part_number);
    var purchases = purchasesOf(caseRecord).filter(function (p) {
      return !part || p.part_number === part;
    });

    var stockRows = [];
    var histCount = 0;
    purchases.forEach(function (p) {
      if (p.meaning === 'historical_purchase') {
        histCount += 1;
        stockRows.push(Object.assign({}, p, { displayed_as_current_stock: false }));
      }
    });

    /* Only responses with allocated/dispatched/delivered meanings can feed
       a current-stock reading. Historical purchases never do. Confirmed
       commitment and estimates are dates, not stock on hand. */
    var questions = questionsOf(caseRecord);
    var availableQty = null;
    questions.forEach(function (q) {
      if (part && q.part_number !== part) return;
      if (!q.response) return;
      var m = q.response.meaning;
      if (m === 'allocated' || m === 'dispatched' || m === 'delivered') {
        if (availableQty == null) availableQty = 0;
        /* Still not invented stock: only the response's stated quantity, if any. */
        if (q.response.quantity != null && Number.isFinite(Number(q.response.quantity))) {
          availableQty += Number(q.response.quantity);
        }
      }
    });

    var shows = availableQty != null && availableQty > 0;
    var statement;
    if (histCount > 0 && !shows) {
      statement = 'A historical purchase is on record. It is not current stock availability.';
    } else if (!shows) {
      statement = 'No current stock availability is recorded for this part.';
    } else {
      statement = 'Current stock availability is taken only from confirmed allocation or later response meanings.';
    }

    return {
      ok: true,
      shows_as_current_stock: shows,
      available_quantity: shows ? availableQty : null,
      historical_purchase_count: histCount,
      rows: stockRows,
      as_of: name(options.as_of),
      statement: statement
    };
  }

  /* Record a distributor response. Unconfirmed answers are estimates and keep
     a next-update obligation. Meanings stay separate. */
  function recordAvailabilityResponse(caseRecord, questionId, response) {
    caseRecord = caseRecord || {};
    response = response || {};
    var list = questionsOf(caseRecord);
    var hit = null;
    for (var i = 0; i < list.length; i++) {
      if (list[i].question_id === questionId) {
        hit = list[i];
        break;
      }
    }
    if (!hit) {
      return { ok: false, error: 'Unknown availability question: ' + questionId, case_record: caseRecord };
    }

    var source = name(response.source);
    var observed = name(response.observation_time);
    if (!source || !observed) {
      return {
        ok: false,
        error: 'A response needs source and observation time.',
        case_record: caseRecord
      };
    }

    var confirmed = response.confirmed === true;
    var meaning;
    var label;
    var nextDue = name(response.next_update_due);
    var obligation;

    if (!confirmed) {
      meaning = 'estimated_date';
      label = 'estimate';
      obligation = true;
      if (!nextDue) {
        return {
          ok: false,
          error: 'An unconfirmed response is an estimate and must carry a next-update due date.',
          case_record: caseRecord
        };
      }
    } else {
      meaning = name(response.claimed_meaning) || name(response.meaning) || 'confirmed_commitment';
      if (RESPONSE_MEANINGS.indexOf(meaning) < 0 || meaning === 'estimated_date') {
        meaning = 'confirmed_commitment';
      }
      label = meaning === 'confirmed_commitment' ? 'confirmed commitment'
        : meaning === 'allocated' ? 'allocated'
        : meaning === 'dispatched' ? 'dispatched'
        : meaning === 'delivered' ? 'delivered'
        : meaning;
      obligation = false;
      nextDue = nextDue || null;
    }

    hit.response = {
      meaning: meaning,
      label: label,
      confirmed: confirmed,
      date_value: name(response.date_value),
      quantity: response.quantity == null ? null : Number(response.quantity),
      source: source,
      observation_time: observed,
      next_update_due: nextDue,
      next_update_obligation: obligation
    };

    var next = Object.assign({}, caseRecord, {
      availability_questions: list,
      historical_purchases: purchasesOf(caseRecord)
    });

    return {
      ok: true,
      question: hit,
      case_record: next,
      statement: confirmed
        ? 'Confirmed availability response recorded with meaning ' + meaning + '.'
        : 'Unconfirmed response labelled estimate; next-update obligation retained.'
    };
  }

  var API = {
    RESPONSE_MEANINGS: RESPONSE_MEANINGS.slice(),
    createAvailabilityQuestion: createAvailabilityQuestion,
    recordHistoricalPurchase: recordHistoricalPurchase,
    currentStockAvailability: currentStockAvailability,
    recordAvailabilityResponse: recordAvailabilityResponse
  };

  root.AIMAvailabilityQuestion = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
