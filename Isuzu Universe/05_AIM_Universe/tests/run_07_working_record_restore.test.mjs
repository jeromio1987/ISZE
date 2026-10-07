#!/usr/bin/env node
/* ===========================================================================
   RUN-07 acceptance tests: Back up and restore the full permitted working
   record.

   How to run
     node --test tests/run_07_backup_restore.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A restored case includes its evidence, original scenario/version and
         change history, not just a database row.
     E2  Recovery tests record actual steps/results; an untested provider
         backup feature is not marked recovery accepted.

   Synthetic fixtures only. Restore into a disposable folder only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'backup_restore.js'));

test('RUN-07 E1: A restored case includes its evidence, original scenario/version and change history, not just a database row.', () => {
  const svc = mod.makeBackupService({ app_version: 'v04-synthetic' });
  const bak = svc.createBackup({
    case_id: 'SYN-BAK-1',
    version: 4,
    at: '2026-10-06T12:00:00Z',
    scenario: { scenario_id: 'SYN-BAK-1:v4', price_after: 10, quantity_after: 5 },
    change_history: [{ at: '2026-10-01', by: 'tester', action: 'submit' }],
    evidence: [{ reference_id: 'SYN-EV-1', title: 'Synthetic attachment' }],
    config_refs: ['identity.development-only']
  });
  assert.equal(bak.ok, true);
  const out = svc.restore(bak.archive_id, { isolated: true, folder: 'C:/tmp/aim-restore-disposable' });
  assert.equal(out.ok, true, out.error);
  assert.equal(out.restored.case_id, 'SYN-BAK-1');
  assert.equal(out.restored.version, 4);
  assert.deepEqual(out.restored.scenario, { scenario_id: 'SYN-BAK-1:v4', price_after: 10, quantity_after: 5 });
  assert.equal(out.restored.change_history.length, 1);
  assert.equal(out.restored.evidence.length, 1);
  assert.equal(out.restored.database_row_only, false);
  assert.equal(out.restored.folder, 'C:/tmp/aim-restore-disposable');
});

test('RUN-07 E2: Recovery tests record actual steps/results; an untested provider backup feature is not marked recovery accepted.', () => {
  const svc = mod.makeBackupService();
  const bak = svc.createBackup({
    case_id: 'SYN-BAK-2', version: 1,
    scenario: { scenario_id: 'SYN-BAK-2:v1' },
    change_history: [], evidence: []
  });
  const out = svc.restore(bak.archive_id, { isolated: true, folder: 'disposable-restore' });
  assert.equal(out.ok, true);
  assert.ok(Array.isArray(out.steps) && out.steps.length >= 4);
  assert.equal(out.recovery_tested, true);
  assert.equal(out.recovery_accepted, false);
  assert.equal(svc.recoveryLog().length, 1);

  const untested = svc.markProviderFeature('cloud-vendor-one-click-backup', false);
  assert.equal(untested.tested, false);
  assert.equal(untested.recovery_accepted, false);
  assert.match(untested.statement, /not marked recovery accepted/);
});
