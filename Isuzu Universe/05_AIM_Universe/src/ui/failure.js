/* ===========================================================================
   Failed and unavailable states (F05, UX-06).

   The v03 defect this file exists to prevent: the Two objectives view threw
   `ReferenceError: v03fmtPct is not defined`, the tab became active, and the
   previous view's HTML stayed on screen underneath. A reader could then believe
   the stale evidence belonged to the tab they had just selected. That is worse
   than an error, because nothing on the page says anything is wrong.

   So every view render either produces content or produces a failure record that
   names the view, the case and the error. The shell renders that record and
   clears the content region. There is no third outcome.
   =========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.AIMFailure = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var VIEW_LABELS = {
    decision: 'Sales evidence',
    position: 'Price position',
    objectives: 'Two objectives',
    economics: 'Price & profit test',
    candidates: 'Candidates',
    action: 'Internal action',
    case: 'Selected part review'
  };

  function labelFor(viewId) {
    return VIEW_LABELS[viewId] || String(viewId || 'unknown view');
  }

  /* One place builds a failure record, so the shell, the tests and any export
     agree on what a failure looks like. */
  function report(options) {
    options = options || {};
    var err = options.error;
    var name = (err && (err.name || err.constructor && err.constructor.name)) || 'Error';
    var message = (err && err.message) || String(err || 'The view produced no content.');
    var stack = (err && err.stack) ? String(err.stack).split('\n').slice(0, 6).join('\n') : null;
    return {
      failed: true,
      view: options.view || null,
      view_label: labelFor(options.view),
      case_id: options.case_id || null,
      case_name: options.case_name || null,
      objective: options.objective || null,
      error_name: name,
      error_message: message,
      /* Named on the card itself: the formatter ReferenceError in v03 was a
         missing module-level function, not an unknown-anything failure. */
      error_kind: kindOf(name, message),
      detail: options.detail || null,
      stack: stack,
      at: options.at || null,
      render_key: options.render_key || null
    };
  }

  function kindOf(name, message) {
    if (/ReferenceError/.test(name)) return 'a name the view referenced does not exist in scope';
    if (/TypeError/.test(name)) return 'a value the view used was not the shape it expected';
    if (/SyntaxError/.test(name)) return 'the view source could not be parsed';
    if (/is not a function/.test(message)) return 'a helper the view called is not available in this build';
    return 'the view stopped with an error';
  }

  /* What the reader is told. Short, specific, no invented cause. */
  function statement(f) {
    if (!f) return null;
    return 'The ' + labelFor(f.view) + ' view for ' + (f.case_id || 'this case') +
      ' could not be built. ' + f.error_name + ': ' + f.error_message +
      '. Nothing from another view is being shown in its place.';
  }

  /* What can be done about it. Every route is a real control in the shell, so a
     reader is never told to do something that does not exist. */
  function recovery(f) {
    var out = [
      { id: 'retry', label: 'Build this view again' },
      { id: 'other-view', label: 'Open a different view for the same case' },
      { id: 'other-case', label: 'Open a different case' }
    ];
    if (f && f.detail) out.unshift({ id: 'detail', label: 'Read the technical detail' });
    return out;
  }

  /* The amber unavailable state. Used where a quantity is simply absent. It is
     never a blank panel: the reason and the source gap are printed. */
  function unavailable(options) {
    options = options || {};
    return {
      state: 'unavailable',
      title: options.title || 'Not available',
      reason: options.reason || 'No source value is held.',
      required: options.required || null,
      scope: options.scope || null,
      as_of: options.as_of || null
    };
  }

  function isUnavailable(v) {
    return !!(v && v.state === 'unavailable');
  }

  return {
    VIEW_LABELS: VIEW_LABELS,
    labelFor: labelFor,
    report: report,
    statement: statement,
    recovery: recovery,
    unavailable: unavailable,
    isUnavailable: isUnavailable
  };
});
