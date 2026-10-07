/* ===========================================================================
   RUN-05 - Show due actions without automatically sending messages.

   In-application due/overdue view tied to the responsible person and next
   update. Optional draft summaries only. External mail, messaging and
   schedules stay off. Reassignment must not reset waiting age.

   Synthetic fixtures only. Nothing is ever sent.
   =========================================================================== */
(function (root) {
  'use strict';

  function deepClone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function daysBetween(fromIso, toIso) {
    var a = Date.parse(String(fromIso || ''));
    var b = Date.parse(String(toIso || ''));
    if (!isFinite(a) || !isFinite(b)) return null;
    return Math.floor((b - a) / 86400000);
  }

  function makeDueActionBoard(options) {
    options = options || {};
    var outboundAttempts = [];
    var drafts = [];

    function listDue(items, asOfDate) {
      items = Array.isArray(items) ? items : [];
      var asOf = name(asOfDate) || null;
      return items.map(function (raw) {
        var item = deepClone(raw || {});
        var caseId = name(item.case_id);
        var obligation = name(item.obligation) || name(item.next_action);
        var owner = name(item.responsible_person) || name(item.owner);
        var due = name(item.next_update_due) || name(item.due_on);
        var waitingSince = name(item.waiting_since) || name(item.submitted_at);
        var overdue = !!(asOf && due && due < asOf);
        var waitingDays = daysBetween(waitingSince, asOf);
        return {
          case_id: caseId,
          obligation: obligation,
          responsible_person: owner,
          next_update_due: due,
          waiting_since: waitingSince,
          waiting_days: waitingDays,
          overdue: overdue,
          permitted: item.permitted !== false,
          case_link: caseId ? ('case://' + caseId) : null,
          statement: obligation
            ? ('Unresolved obligation: ' + obligation)
            : 'No unresolved obligation is recorded.'
        };
      }).filter(function (row) {
        return row.case_id && row.obligation && row.permitted;
      }).sort(function (a, b) {
        if (a.overdue !== b.overdue) return a.overdue ? -1 : 1;
        return String(a.next_update_due || '9999-12-31').localeCompare(String(b.next_update_due || '9999-12-31'));
      });
    }

    function openDueItem(item, cases) {
      item = item || {};
      cases = Array.isArray(cases) ? cases : [];
      var caseId = name(item.case_id);
      if (!caseId) {
        return { ok: false, code: 'CASE_REQUIRED', error: 'A due item needs a case_id.' };
      }
      if (item.permitted === false) {
        return { ok: false, code: 'NOT_PERMITTED', error: 'This case is not permitted for the caller.' };
      }
      var found = null;
      for (var i = 0; i < cases.length; i++) {
        if (name(cases[i].case_id) === caseId) {
          found = deepClone(cases[i]);
          break;
        }
      }
      if (!found) {
        return { ok: false, code: 'CASE_NOT_FOUND', error: 'The due item does not open a known permitted case.' };
      }
      return {
        ok: true,
        case_id: caseId,
        opened_case_id: found.case_id,
        obligation: name(item.obligation) || name(item.next_action),
        version: found.version == null ? null : found.version,
        statement: 'Opened the permitted case named by the due item.'
      };
    }

    function prepareDraftSummary(item, audience) {
      item = item || {};
      var draft = {
        draft_id: 'DRAFT-' + (drafts.length + 1),
        case_id: name(item.case_id),
        case_link: name(item.case_id) ? ('case://' + name(item.case_id)) : null,
        audience: name(audience) || 'internal',
        body: 'Draft only. Obligation: ' + (name(item.obligation) || 'unspecified') + '.',
        status: 'draft',
        sent: false,
        synthetic: true
      };
      drafts.push(deepClone(draft));
      return deepClone(draft);
    }

    /* External mail/messaging stays off. Development and tests never send. */
    function sendExternalNotification(payload) {
      var attempt = {
        at: name((payload || {}).at) || null,
        channel: name((payload || {}).channel) || 'email',
        case_id: name((payload || {}).case_id),
        sent: false,
        blocked: true,
        code: 'SEND_DISABLED',
        statement: 'No email or external notification is sent during development or a test run.'
      };
      outboundAttempts.push(deepClone(attempt));
      return deepClone(attempt);
    }

    function reassign(item, newOwner, asOfDate) {
      item = deepClone(item || {});
      var waitingSince = name(item.waiting_since) || name(item.submitted_at);
      var beforeDays = daysBetween(waitingSince, asOfDate);
      item.responsible_person = name(newOwner);
      item.owner = name(newOwner);
      /* Waiting age must not reset on reassignment. */
      item.waiting_since = waitingSince;
      var afterDays = daysBetween(item.waiting_since, asOfDate);
      return {
        ok: true,
        item: item,
        waiting_days_before: beforeDays,
        waiting_days_after: afterDays,
        waiting_age_reset: false,
        statement: 'Reassigned without resetting waiting age.'
      };
    }

    return {
      listDue: listDue,
      openDueItem: openDueItem,
      prepareDraftSummary: prepareDraftSummary,
      sendExternalNotification: sendExternalNotification,
      reassign: reassign,
      drafts: function () { return deepClone(drafts); },
      outboundAttempts: function () { return deepClone(outboundAttempts); },
      sentCount: function () {
        return outboundAttempts.filter(function (a) { return a.sent; }).length;
      }
    };
  }

  var API = { makeDueActionBoard: makeDueActionBoard };
  root.AIMDueActions = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));

