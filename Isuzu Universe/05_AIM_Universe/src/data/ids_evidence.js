/* ===========================================================================
   CONNECT-01 - Read IDS evidence through validated identities.

   Synthetic dealers and a synthetic IDS sheet only. Reuses AIMManifest's
   separate-entity check so UMI and UTI never merge. A dealer answer is shown
   only when that dealer's identity is validated; otherwise the view states
   "identity not validated" and carries no answers. An unknown identity stays
   unknown and does not borrow the previous row.

   Local question codes are scoped by questionnaire version so the same code in
   two questionnaires cannot collide. UTI is outside the 2026 IDS population;
   no distributor audit score is created for it (or invented for anyone).
   =========================================================================== */
(function (root) {
  'use strict';

  var IDS_YEAR_2026 = 2026;
  var MSG_NOT_VALIDATED = 'identity not validated';
  var MSG_UNKNOWN = 'identity unknown';
  var ANSWER_STATES = {
    answered: 'answered',
    missing: 'missing',
    not_applicable: 'not_applicable',
    unanswered: 'unanswered'
  };

  function manifestApi() {
    if (root && root.AIMManifest) return root.AIMManifest;
    if (typeof module === 'object' && typeof require === 'function') {
      try { return require('./manifest.js'); } catch (e) { return null; }
    }
    return null;
  }

  function upper(v) {
    return v == null ? '' : String(v).toUpperCase();
  }

  function scopedQuestionId(questionnaireVersion, localQuestionCode) {
    return String(questionnaireVersion) + '::' + String(localQuestionCode);
  }

  function isUnknownIdentity(identity) {
    if (!identity) return true;
    if (identity.unknown === true) return true;
    if (identity.dealer_id == null || identity.dealer_id === '') return true;
    if (identity.distributor == null || identity.distributor === '') return true;
    return false;
  }

  function isValidatedIdentity(identity) {
    return !isUnknownIdentity(identity) && identity.validated === true;
  }

  function normalizeAnswerState(row) {
    var state = row && row.answer_state;
    if (state === ANSWER_STATES.missing || state === ANSWER_STATES.not_applicable
        || state === ANSWER_STATES.unanswered || state === ANSWER_STATES.answered) {
      return state;
    }
    if (row && row.answer != null && row.answer !== '') return ANSWER_STATES.answered;
    return ANSWER_STATES.unanswered;
  }

  function emptyResult(identityState, statement, identity) {
    return {
      identity_state: identityState,
      identity: identity || null,
      in_ids_population: false,
      answers: [],
      distributor_audit_score: null,
      statement: statement
    };
  }

  /* One dealer identity, one synthetic sheet. Fresh result every call. */
  function readIdsEvidence(identity, sheet, options) {
    options = options || {};
    var year = options.ids_year != null ? options.ids_year : IDS_YEAR_2026;

    if (isUnknownIdentity(identity)) {
      return emptyResult('unknown', MSG_UNKNOWN, null);
    }

    var idSnap = {
      dealer_id: identity.dealer_id,
      distributor: identity.distributor,
      display_name: identity.display_name || null,
      validated: identity.validated === true
    };

    if (upper(identity.distributor) === 'UTI' && year === IDS_YEAR_2026) {
      return {
        identity_state: 'excluded_from_population',
        identity: idSnap,
        in_ids_population: false,
        answers: [],
        distributor_audit_score: null,
        statement: 'UTI is not included in the 2026 IDS population; no distributor audit score is created.'
      };
    }

    if (!isValidatedIdentity(identity)) {
      return {
        identity_state: 'not_validated',
        identity: idSnap,
        in_ids_population: true,
        answers: [],
        distributor_audit_score: null,
        statement: MSG_NOT_VALIDATED
      };
    }

    var rows = [];
    if (sheet && Array.isArray(sheet.rows)) rows = sheet.rows;
    else if (Array.isArray(sheet)) rows = sheet;

    var answers = [];
    rows.forEach(function (row) {
      if (!row) return;
      if (String(row.dealer_id) !== String(identity.dealer_id)) return;
      if (upper(row.distributor) !== upper(identity.distributor)) return;

      var state = normalizeAnswerState(row);
      answers.push({
        scoped_question_id: scopedQuestionId(row.questionnaire_version, row.local_question_code),
        local_question_code: row.local_question_code,
        questionnaire_version: row.questionnaire_version,
        question_text: row.question_text,
        answer_state: state,
        answer: state === ANSWER_STATES.answered ? row.answer : null,
        date_or_round: row.date_or_round != null ? row.date_or_round : null
      });
    });

    return {
      identity_state: 'validated',
      identity: idSnap,
      in_ids_population: true,
      answers: answers,
      distributor_audit_score: null,
      statement: 'IDS evidence for a validated identity; ' + answers.length + ' answer row(s).'
    };
  }

  /* 2026 IDS population: UTI never included; no distributor audit scores. */
  function idsPopulation2026(identities) {
    var included = [];
    var excluded = [];
    (identities || []).forEach(function (id) {
      if (!id || isUnknownIdentity(id)) return;
      if (upper(id.distributor) === 'UTI') {
        excluded.push({
          dealer_id: id.dealer_id,
          distributor: id.distributor,
          reason: 'UTI is not included in the 2026 IDS population'
        });
        return;
      }
      included.push({
        dealer_id: id.dealer_id,
        distributor: id.distributor,
        display_name: id.display_name || null,
        validated: id.validated === true
      });
    });
    return {
      year: IDS_YEAR_2026,
      included: included,
      excluded: excluded,
      distributor_audit_scores: null,
      statement: 'UTI is not included in the 2026 IDS population; no distributor audit score is created.'
    };
  }

  /* Refuse to blend two distributors' IDS answers into one list. */
  function refuseBlend(a, b) {
    var left = a && a.distributor;
    var right = b && b.distributor;
    var M = manifestApi();
    if (M && typeof M.assertNoBlend === 'function') {
      var check = M.assertNoBlend(left, right);
      if (!check.ok) {
        return {
          ok: false,
          blended: false,
          answers: null,
          distributor_audit_score: null,
          statement: check.statement
        };
      }
    } else if ((upper(left) === 'UMI' && upper(right) === 'UTI')
        || (upper(left) === 'UTI' && upper(right) === 'UMI')) {
      return {
        ok: false,
        blended: false,
        answers: null,
        distributor_audit_score: null,
        statement: 'UMI and UTI are separate entities. They are reported as two rows and are never combined into one number.'
      };
    }
    if (upper(left) && upper(right) && upper(left) !== upper(right)) {
      return {
        ok: false,
        blended: false,
        answers: null,
        distributor_audit_score: null,
        statement: left + ' and ' + right + ' stay on separate IDS rows; answers are not merged across distributors.'
      };
    }
    return { ok: true, blended: false, statement: 'Same distributor; blend check not required.' };
  }

  /* Each identity is read independently. An unknown row cannot inherit answers. */
  function readMany(identities, sheet, options) {
    return (identities || []).map(function (identity) {
      return readIdsEvidence(identity, sheet, options);
    });
  }

  /* Same five characters as esc in src/ui/app.js, the single quote included. */
  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* Side-by-side panel for a validated and an unvalidated dealer (synthetic). */
  function renderSideBySide(views) {
    views = views || [];
    var cards = views.map(function (v) {
      var title = (v.identity && (v.identity.display_name || v.identity.dealer_id)) || 'Unknown dealer';
      var dist = (v.identity && v.identity.distributor) || '-';
      var state = v.identity_state || 'unknown';
      var body;
      if (state === 'validated' && v.answers && v.answers.length) {
        body = '<ul>' + v.answers.map(function (a) {
          return '<li><code>' + escapeHtml(a.scoped_question_id) + '</code> '
            + escapeHtml(a.question_text) + ' - '
            + (a.answer_state === 'answered' ? escapeHtml(a.answer) : escapeHtml(a.answer_state))
            + '</li>';
        }).join('') + '</ul>';
      } else if (state === 'not_validated') {
        body = '<p class="ids-gate">' + escapeHtml(MSG_NOT_VALIDATED) + '</p><p>No answers shown.</p>';
      } else if (state === 'unknown') {
        body = '<p class="ids-gate">' + escapeHtml(MSG_UNKNOWN) + '</p><p>No answers shown.</p>';
      } else if (state === 'excluded_from_population') {
        body = '<p class="ids-gate">' + escapeHtml(v.statement) + '</p>';
      } else {
        body = '<p>' + escapeHtml(v.statement || '') + '</p>';
      }
      return '<article class="ids-card" data-identity-state="' + escapeHtml(state) + '">'
        + '<h3>' + escapeHtml(title) + '</h3>'
        + '<p class="small">Distributor: ' + escapeHtml(dist) + ' · state: ' + escapeHtml(state) + '</p>'
        + body + '</article>';
    }).join('');
    return '<section class="ids-side-by-side" data-connect-01="panel">'
      + '<h2>Dealer Standards evidence (validated identities only)</h2>'
      + '<div class="ids-row">' + cards + '</div></section>';
  }

  var API = {
    escapeHtml: escapeHtml,
    scopedQuestionId: scopedQuestionId,
    readIdsEvidence: readIdsEvidence,
    idsPopulation2026: idsPopulation2026,
    refuseBlend: refuseBlend,
    readMany: readMany,
    renderSideBySide: renderSideBySide,
    MSG_NOT_VALIDATED: MSG_NOT_VALIDATED,
    MSG_UNKNOWN: MSG_UNKNOWN,
    ANSWER_STATES: ANSWER_STATES,
    IDS_YEAR_2026: IDS_YEAR_2026
  };

  root.AIMIdsEvidence = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
