#!/usr/bin/env node
/* ===========================================================================
   The separate-process half of check C08 in tests/case_service.test.mjs.

   Why this file exists at all
   ---------------------------
   "A created draft survives a process restart" cannot be tested by building a
   second service object in the same process. The module is already loaded, the
   require cache is warm, and nothing on disk has to be parsed again - so the
   check would pass even if the adapter kept everything in a module-level object.

   This is therefore a real second `node` process. It shares exactly one thing
   with the process that ran the assertions: the folder named on the command
   line. It opens that folder, reads one case back, and prints what it found as
   a single line of JSON on stdout. It writes nothing.

   Usage:
     node tests/case_restart_child.cjs <storage-folder> <case-id>

   Exit code is 0 when the case was read. Non-zero when it was not, so a failure
   is visible even if the JSON line is missed.

   `.cjs`, not `.mjs`: this file uses `require`, because it is run directly with
   `node <path>` and the workspace has no `package.json` type field. The sibling
   suite is `.mjs` because it is a module; this one is a script.
   =========================================================================== */
'use strict';
const path = require('node:path');

const dir = process.argv[2];
const caseId = process.argv[3];

if (!dir || !caseId) {
  console.error('usage: node tests/case_restart_child.mjs <storage-folder> <case-id>');
  process.exit(2);
}

const root = path.join(__dirname, '..');
const store = require(path.join(root, 'src', 'case', 'store.js'));
const schema = require(path.join(root, 'src', 'case', 'schema.js'));

/* A fresh service over the folder. Nothing is imported from the parent process,
   because there is no parent process state to import: this is a new node. */
const adapter = store.makeFileAdapter({ dir });
const service = store.makeCaseService({
  adapter,
  caller: 'restart-child',
  identityMode: 'development-only'
});

const record = service.get(caseId);

if (!record) {
  console.error('the child process found no case "' + caseId + '" in ' + dir);
  console.log(JSON.stringify({ ok: false, error: 'not found', dir, case_id: caseId }));
  process.exit(1);
}

/* Read the file straight off the disk as well, so the answer is not only what
   the adapter's own parser said. */
const fs = require('node:fs');
const raw = fs.readFileSync(path.join(dir, 'cases', caseId + '.json'), 'utf8');
const fromDisk = JSON.parse(raw);

const shape = schema.validate(record);

console.log(JSON.stringify({
  ok: true,
  pid: process.pid,
  case_id: record.case_id,
  state: record.state,
  version: record.version,
  next_action: record.next_action,
  owner_role: record.owner_role,
  history_entries: record.history.length,
  schema_version: record.schema_version,
  record_schema_version: schema.RECORD_SCHEMA_VERSION,
  contract_version: record.contract_version,
  /* Read independently of the adapter, so a parser bug cannot make a missing
     record look present. */
  from_disk_state: fromDisk.state,
  from_disk_version: fromDisk.version,
  from_disk_bytes: raw.length,
  /* The vocabulary the child is enforcing, so the migration is visible from
     outside the parent process too. */
  states_in_force: schema.CASE_STATES,
  valid: shape.ok
}));

process.exit(0);
