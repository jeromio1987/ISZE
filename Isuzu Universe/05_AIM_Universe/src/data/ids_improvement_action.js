/* ===========================================================================
   CONNECT-02 - Connect an IDS answer to a separate improvement action.

   A relevant recorded self-assessment answer can open an agreed action on the
   same case record. Dealer work stays separate from support owed by others.
   Closing the action records evidence without changing the assessment answer
   or score. An unresolved IDS link does not switch off the purchasing review;
   new action work can stay independent. No sentence claims that the answer
   caused a historical purchasing movement.

   Synthetic dealers and synthetic IDS answers only.
   =========================================================================== */
(function (root) {
  'use strict';

  var CAUSAL_BANNED = [
    /answer caus(?:ed|es)/i,
    /caused a (?:past |historical )?purchasing/i,
    /ids answer (?:drove|drove the|led to) (?:the )?(?:past |historical )?purchas/i,
    /self-assessment caused/i
  ];

  function deepFreezeClone(value) {
    return JSON.parse(JSON.stringify(value == null ? null : value));
  }

  function snapshotAnswer(answer) {
    if (!answer) return null;
    return deepFreezeClone({
      scoped_question_id: answer.scoped_question_id,
      local_question_code: answer.local_question_code,
      questionnaire_version: answer.questionnaire_version,
      question_text: answer.question_text,
      answer_state: answer.answer_state,
      answer: answer.answer,
      date_or_round: answer.date_or_round != null ? answer.date_or_round : null,
      score: answer.score != null ? answer.score : null
    });
  }

  function assertNoCausalClaim(text) {
    var s = text == null ? '' : String(text);
    for (var i = 0; i < CAUSAL_BANNED.length; i++) {
      if (CAUSAL_BANNED[i].test(s)) {
        return {
          ok: false,
          statement: 'Refused: no sentence may claim that an IDS answer caused a historical purchasing movement.'
        };
      }
    }
    return { ok: true, statement: 'No causal purchasing claim.' };
  }

  /* Open an improvement action from a recorded IDS answer. The answer is
     snapshotted; later action work cannot rewrite it. */
  function openFromIdsAnswer(caseRecord, idsAnswer, options) {
    options = options || {};
    caseRecord = caseRecord || {};
    var check = assertNoCausalClaim(options.note || options.rationale || '');
    if (!check.ok) {
      return { ok: false, error: check.statement, case_record: caseRecord };
    }

    var snap = snapshotAnswer(idsAnswer);
    if (!snap || !snap.scoped_question_id) {
      return {
        ok: false,
        error: 'An improvement action needs a recorded IDS answer with a scoped question id.',
        case_record: caseRecord,
        ids_link_resolved: false
      };
    }

    var actions = Array.isArray(caseRecord.improvement_actions)
      ? caseRecord.improvement_actions.slice()
      : [];
    var actionId = options.action_id || ('IMP-' + (actions.length + 1));
    var action = {
      action_id: actionId,
      state: 'open',
      owner: options.owner || 'dealer',
      support_owed_by: options.support_owed_by || null,
      opened_at: options.opened_at || '2026-10-06',
      note: options.note || null,
      ids_answer_snapshot: snap,
      completion_evidence: null,
      independent_of_ids_link: false
    };
    actions.push(action);

    var answers = Array.isArray(caseRecord.ids_answers)
      ? caseRecord.ids_answers.map(snapshotAnswer)
      : [];
    var found = false;
    for (var i = 0; i < answers.length; i++) {
      if (answers[i] && answers[i].scoped_question_id === snap.scoped_question_id) {
        answers[i] = snap;
        found = true;
        break;
      }
    }
    if (!found) answers.push(snap);

    var next = Object.assign({}, caseRecord, {
      ids_answers: answers,
      ids_score: caseRecord.ids_score,
      improvement_actions: actions,
      purchasing_review: Object.assign(
        { enabled: true, independent: true },
        caseRecord.purchasing_review || {}
      )
    });

    return {
      ok: true,
      action: action,
      case_record: next,
      ids_link_resolved: true,
      statement: 'Improvement action opened beside a recorded IDS answer; the answer is snapshotted and separate.'
    };
  }

  /* Closing records evidence only. Original answer text and score stay as they were. */
  function closeImprovement(caseRecord, actionId, evidence) {
    caseRecord = caseRecord || {};
    var actions = Array.isArray(caseRecord.improvement_actions)
      ? caseRecord.improvement_actions.map(function (a) { return Object.assign({}, a); })
      : [];
    var hit = null;
    for (var i = 0; i < actions.length; i++) {
      if (actions[i].action_id === actionId) {
        hit = actions[i];
        hit.state = 'closed';
        hit.completion_evidence = evidence == null ? null : deepFreezeClone(evidence);
        hit.closed_at = (evidence && evidence.closed_at) || '2026-10-06';
        break;
      }
    }
    if (!hit) {
      return { ok: false, error: 'Unknown improvement action: ' + actionId, case_record: caseRecord };
    }

    var next = Object.assign({}, caseRecord, {
      improvement_actions: actions,
      ids_answers: (caseRecord.ids_answers || []).map(snapshotAnswer),
      ids_score: caseRecord.ids_score
    });

    return {
      ok: true,
      action: hit,
      case_record: next,
      answer_unchanged: true,
      score_unchanged: true,
      statement: 'Improvement closed with evidence; original IDS answer and score unchanged.'
    };
  }

  /* An unresolved IDS link must not disable the purchasing review. New action
     work can remain independent of the IDS link. */
  function purchasingReviewWithIdsLink(caseRecord, idsLink) {
    caseRecord = caseRecord || {};
    var resolved = !!(idsLink && idsLink.resolved === true && idsLink.scoped_question_id);
    var review = Object.assign(
      { enabled: true, independent: true },
      caseRecord.purchasing_review || {}
    );
    if (!resolved) {
      review.enabled = true;
      review.disabled_by_ids_link = false;
      review.ids_link_state = 'unresolved';
    } else {
      review.ids_link_state = 'resolved';
      review.disabled_by_ids_link = false;
    }

    var actions = Array.isArray(caseRecord.improvement_actions)
      ? caseRecord.improvement_actions.slice()
      : [];
    if (idsLink && idsLink.open_independent_action) {
      actions.push({
        action_id: idsLink.action_id || ('IMP-IND-' + (actions.length + 1)),
        state: 'open',
        owner: idsLink.owner || 'dealer',
        independent_of_ids_link: true,
        ids_answer_snapshot: null,
        note: idsLink.note || 'Independent action work; IDS link unresolved.'
      });
    }

    return {
      ok: true,
      purchasing_review: review,
      improvement_actions: actions,
      ids_link_resolved: resolved,
      statement: resolved
        ? 'IDS link resolved; purchasing review stays available.'
        : 'IDS link unresolved; purchasing review stays enabled and new action work can remain independent.'
    };
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* Action beside an unchanged answer (synthetic). */
  function renderActionBesideAnswer(view) {
    view = view || {};
    var answer = view.answer || {};
    var action = view.action || {};
    return '<section class="ids-improvement" data-connect-02="panel">'
      + '<h2>Improvement action beside recorded IDS answer</h2>'
      + '<div class="ids-row">'
      + '<article class="ids-card" data-role="answer">'
      + '<h3>Recorded answer (unchanged)</h3>'
      + '<p><code>' + escapeHtml(answer.scoped_question_id) + '</code></p>'
      + '<p>' + escapeHtml(answer.question_text) + '</p>'
      + '<p>Answer: <strong>' + escapeHtml(answer.answer) + '</strong></p>'
      + '<p>Score: <strong>' + escapeHtml(answer.score) + '</strong></p>'
      + '</article>'
      + '<article class="ids-card" data-role="action">'
      + '<h3>Improvement action</h3>'
      + '<p>Id: <code>' + escapeHtml(action.action_id) + '</code></p>'
      + '<p>State: <strong>' + escapeHtml(action.state) + '</strong></p>'
      + '<p>' + escapeHtml(action.completion_evidence
        ? ('Evidence: ' + (action.completion_evidence.note || 'recorded'))
        : (action.note || 'Open')) + '</p>'
      + '</article>'
      + '</div></section>';
  }

  var API = {
    openFromIdsAnswer: openFromIdsAnswer,
    closeImprovement: closeImprovement,
    purchasingReviewWithIdsLink: purchasingReviewWithIdsLink,
    assertNoCausalClaim: assertNoCausalClaim,
    snapshotAnswer: snapshotAnswer,
    renderActionBesideAnswer: renderActionBesideAnswer
  };

  root.AIMIdsImprovementAction = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
