#!/usr/bin/env node
/* ===========================================================================
   Audit fix G (U27): tests/run_all.ps1 runs every *.test.mjs / *.test.cjs on
   disk, judges each on its exit code, and reads no unset variable.

   How to run
     node --test tests/audit_g_runner_coverage.test.mjs
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync, readdirSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ps = readFileSync(join(HERE, process.env.AIM_RUNNER || 'run_all.ps1'), 'utf8');

test('audit G: the runner lists test files from disk instead of naming them one by one', () => {
  assert.match(ps, /Get-ChildItem -Path \$PSScriptRoot -File/);
  assert.match(ps, /\\.test\\.\(mjs\|cjs\)\$/);
  const onDisk = readdirSync(HERE).filter((f) => /\.test\.(mjs|cjs)$/.test(f));
  assert.ok(onDisk.length >= 72, 'expected at least the 72 audited files, found ' + onDisk.length);
  const named = onDisk.filter((f) => ps.includes(f));
  assert.deepEqual(named, [], 'no file is named by hand, so none can be forgotten');
});

test('audit G: a unit file passes only on exit code 0, and the runner reads no unset $Root', () => {
  assert.match(ps, /\$code -eq 0/);
  assert.equal(/-match "pass\s\+\d"/.test(ps), false, 'no pass-count text matching decides a result');
  assert.equal(/\$Root\b/.test(ps), false, '$Root is never set in this file');
});
