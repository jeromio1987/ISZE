#!/usr/bin/env node
/* ===========================================================================
   The separate-process half of CASE-07 in tests/behavioural_base_and_case.test.mjs.

   Why a real second process
   -------------------------
   "Two writers must not lose a write" cannot be tested with two adapters in one
   process: they share a require cache and a module-level object, so a lock that
   only exists in memory would pass. This is a real `node` process. It shares
   exactly one thing with the others: the folder named on the command line.

     node tests/case07_child.cjs <root> <folder> <caller> create
     node tests/case07_child.cjs <root> <folder> <caller> write <expected_version>
     node tests/case07_child.cjs <root> <folder> <caller> read

   Each mode prints one line of JSON on stdout and exits 0 for a completed
   attempt (including a refused one), so the parent judges the RESULT rather than
   an exit code. An unexpected throw is printed as JSON with code OS_REFUSED
   instead of a stack trace, so a real operating-system refusal is visible rather
   than lost in noise.

   Synthetic records in a disposable temp folder only.
   =========================================================================== */
'use strict';
const path = require('node:path');

const [root, dir, caller, mode, expected] = process.argv.slice(2);
const out = (o) => process.stdout.write(JSON.stringify(o));

if (!root || !dir || !caller || !mode) {
  console.error('usage: node tests/case07_child.cjs <root> <folder> <caller> create|write|read [expected_version]');
  process.exit(2);
}

const store = require(path.join(root, 'src', 'case', 'store.js'));
const service = store.makeCaseService({
  adapter: store.makeFileAdapter({ dir }),
  caller,
  identityMode: 'development-only'
});

try {
  if (mode === 'create') {
    const created = service.create({
      case_id: 'SYN-C07', customer: 'Synthetic customer', part_number: 'SYN-P-C07',
      owner_role: 'case_owner', by: caller
    });
    out({ pid: process.pid, ok: created.ok, version: created.record && created.record.version,
          error: created.error || null });
  } else if (mode === 'write') {
    /* Read first, then write against the version that was read. This is what a
       second person does: they open the case, then act on it. */
    const loaded = service.load('SYN-C07');
    const moved = service.transition('SYN-C07', {
      action: 'submit',
      role: 'case_owner',
      at: '2026-10-07T09:00:00.000Z',
      next_action: 'Dealer to confirm the counter stock position',
      next_update_due: '2026-10-14'
    }, { expected_version: expected == null ? undefined : Number(expected), by: caller });
    out({ pid: process.pid, loaded_version: loaded && loaded.version,
          ok: moved.ok, code: moved.code || null,
          version: moved.record && moved.record.version, error: moved.error || null });
  } else {
    const record = service.load('SYN-C07');
    out({ pid: process.pid, version: record && record.version, state: record && record.state,
          entries: record && record.history && record.history.length });
  }
  process.exit(0);
} catch (err) {
  out({ pid: process.pid, ok: false, code: 'OS_REFUSED', error: String(err && err.message || err) });
  process.exit(0);
}
