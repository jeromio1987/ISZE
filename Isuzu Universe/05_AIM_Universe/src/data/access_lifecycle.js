/* ===========================================================================
   SAFE-07 - role changes, departure and record-use decisions.

   Applies revocation, role/account changes and optional-feed cessation to
   sessions, saved links and export access. Retention/deletion/export policy is
   recorded without inventing a universal period. Downloaded copies are not
   claimed to be remotely recallable.
   =========================================================================== */
(function (root) {
  'use strict';

  function reject(code, error, extra) {
    return Object.assign({ ok: false, code: code, error: error }, extra || {});
  }

  function makeAccessLifecycle(options) {
    options = options || {};
    var now = options.now || function () { return new Date().toISOString(); };
    var users = Object.create(null);
    var sessions = Object.create(null);
    var links = Object.create(null);
    var feeds = Object.create(null);
    var historicalResponses = [];

    function registerUser(user) {
      users[user.subject] = {
        subject: user.subject,
        role: user.role,
        tenant: user.tenant,
        active: true,
        revoked_at: null,
        role_history: [{ role: user.role, at: now(), reason: 'registered' }]
      };
      return { ok: true, user: users[user.subject] };
    }

    function openSession(subject) {
      var u = users[subject];
      if (!u || !u.active) {
        return reject('SESSION_REFUSED', 'No active user may open a session.');
      }
      var sid = 'sess-' + subject + '-' + Math.random().toString(36).slice(2, 8);
      sessions[sid] = {
        session_id: sid,
        subject: subject,
        opened_at: now(),
        revoked: false
      };
      return { ok: true, session: sessions[sid] };
    }

    function issueLink(subject, recordId) {
      var u = users[subject];
      if (!u || !u.active) {
        return reject('LINK_REFUSED', 'No active user may receive a protected link.');
      }
      var lid = 'link-' + Math.random().toString(36).slice(2, 10);
      links[lid] = {
        link_id: lid,
        subject: subject,
        record_id: recordId,
        issued_at: now(),
        revoked: false
      };
      return { ok: true, link: links[lid] };
    }

    function recordHistoricalResponse(entry) {
      historicalResponses.push({
        response_id: entry.response_id,
        feed_id: entry.feed_id || null,
        subject: entry.subject,
        body: entry.body,
        recorded_at: entry.recorded_at || now(),
        permitted: entry.permitted !== false
      });
      return { ok: true, count: historicalResponses.length };
    }

    function startOptionalFeed(feedId, subject) {
      feeds[feedId] = {
        feed_id: feedId,
        subject: subject,
        active: true,
        stopped_at: null
      };
      return { ok: true, feed: feeds[feedId] };
    }

    /* Approved effect of departure / revocation. Policy is recorded; no universal
       retention period is invented; downloads are not claimed recallable. */
    function revokeUser(subject, policy) {
      policy = policy || {};
      var u = users[subject];
      if (!u) return reject('UNKNOWN_USER', 'No such user to revoke.');
      u.active = false;
      u.revoked_at = now();
      u.revocation_policy = {
        sessions_invalidated: true,
        links_invalidated: true,
        export_access_removed: true,
        retention_note: policy.retention_note || 'Retention follows the responsible owner policy; no universal period is set here.',
        downloaded_copies_remotely_recallable: false,
        statement: 'Downloaded copies are not claimed to be remotely recallable.'
      };
      Object.keys(sessions).forEach(function (sid) {
        if (sessions[sid].subject === subject) sessions[sid].revoked = true;
      });
      Object.keys(links).forEach(function (lid) {
        if (links[lid].subject === subject) links[lid].revoked = true;
      });
      return {
        ok: true,
        subject: subject,
        revoked_at: u.revoked_at,
        policy: u.revocation_policy
      };
    }

    function changeRole(subject, newRole, reason) {
      var u = users[subject];
      if (!u || !u.active) return reject('ROLE_CHANGE_REFUSED', 'Role cannot change for an inactive or unknown user.');
      u.role_history.push({ role: newRole, at: now(), reason: reason || 'role_change' });
      u.role = newRole;
      return { ok: true, subject: subject, role: u.role, history: u.role_history.slice() };
    }

    function stopOptionalFeed(feedId) {
      var f = feeds[feedId];
      if (!f) return reject('UNKNOWN_FEED', 'No such optional feed.');
      f.active = false;
      f.stopped_at = now();
      /* Stopping a feed must not delete unrelated permitted historical responses. */
      var kept = historicalResponses.filter(function (r) {
        return r.permitted === true;
      });
      return {
        ok: true,
        feed_id: feedId,
        stopped_at: f.stopped_at,
        historical_responses_retained: kept.length,
        deleted_unrelated_historical_responses: false,
        retained: kept.slice()
      };
    }

    function retrieveThroughSession(sessionId, recordId) {
      var s = sessions[sessionId];
      if (!s || s.revoked) {
        return reject('SESSION_REVOKED',
          'Revoked users cannot retrieve protected records through an active session beyond the accepted policy.');
      }
      var u = users[s.subject];
      if (!u || !u.active) {
        return reject('USER_REVOKED',
          'Revoked users cannot retrieve protected records through an active session beyond the accepted policy.');
      }
      return { ok: true, record_id: recordId, subject: s.subject, via: 'session' };
    }

    function retrieveThroughLink(linkId) {
      var l = links[linkId];
      if (!l || l.revoked) {
        return reject('LINK_REVOKED',
          'Revoked users cannot retrieve protected records through an old link beyond the accepted policy.');
      }
      var u = users[l.subject];
      if (!u || !u.active) {
        return reject('USER_REVOKED',
          'Revoked users cannot retrieve protected records through an old link beyond the accepted policy.');
      }
      return { ok: true, record_id: l.record_id, subject: l.subject, via: 'link' };
    }

    return {
      registerUser: registerUser,
      openSession: openSession,
      issueLink: issueLink,
      recordHistoricalResponse: recordHistoricalResponse,
      startOptionalFeed: startOptionalFeed,
      revokeUser: revokeUser,
      changeRole: changeRole,
      stopOptionalFeed: stopOptionalFeed,
      retrieveThroughSession: retrieveThroughSession,
      retrieveThroughLink: retrieveThroughLink
    };
  }

  var API = { makeAccessLifecycle: makeAccessLifecycle };
  if (typeof module === 'object' && module.exports) module.exports = API;
  else root.AIMAccessLifecycle = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);