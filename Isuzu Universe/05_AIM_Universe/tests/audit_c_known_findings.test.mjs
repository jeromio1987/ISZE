#!/usr/bin/env node
/* ===========================================================================
   Audit fix C (U27): a known finding or a check that did not run never exits 0,
   and the runner never prints "every check ran and returned zero" while a step
   was skipped.

   How to run
     node --test tests/audit_c_known_findings.test.mjs
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const H = require(join(ROOT, 'tests', 'accept', 'lib', 'harness.cjs'));

const base = { pass: 5, fail: 0, skipped: 0, untested: 0, known_findings: 0, total: 5 };

test('audit C: harness exit code is 3 while a known finding is open, 1 on a fail, 4 when not run', () => {
  assert.equal(H.exitCode(base), 0);
  assert.equal(H.exitCode({ ...base, known_findings: 1 }), 3);
  assert.equal(H.exitCode({ ...base, fail: 1, known_findings: 1 }), 1);
  assert.equal(H.exitCode({ ...base, untested: 1 }), 4);
  const run = H.makeRun('SYN-C', 'synthetic');
  run.results.push({ id: 'K1', name: 'synthetic open finding', status: 'FAIL', known_finding: true, evidence: 'x' });
  run.known_findings = run.results.filter(r => r.known_finding);
  assert.equal(H.exitCode(H.summary(run)), 3);
});

test('audit C: the browser journey exits 3 on a known finding and 4 when the browser does not start', () => {
  const py = [
    'import importlib.util, sys',
    `spec = importlib.util.spec_from_file_location("j", r"${join(ROOT, 'tests', 'accept', 'accept_02_journey.py')}")`,
    'm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)',
    'base = {"pass": 3, "fail": 0, "untested": 0, "known_findings": 0, "total": 3}',
    'print(m._exit_code(base), m._exit_code({**base, "known_findings": 1}), m._exit_code({**base, "untested": 1}), m._exit_code({**base, "fail": 1}))'
  ].join('\n');
  const r = spawnSync('python', ['-c', py], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  assert.equal(r.stdout.trim(), '0 3 4 1');
});

test('audit C: run_all.ps1 only says every check returned zero when nothing failed, was open or was skipped', () => {
  const ps = readFileSync(join(ROOT, 'tests', 'accept', 'run_all.ps1'), 'utf8');
  const i = ps.indexOf('every check ran and returned zero');
  assert.ok(i > 0, 'the all-clear line exists');
  const guard = ps.slice(ps.lastIndexOf('if (', i), i);
  assert.match(guard, /\$script:Failed -eq 0/);
  assert.match(guard, /\$script:KnownOpen\.Count -eq 0/);
  assert.match(guard, /\$script:NotRun\.Count -eq 0/);
  const skips = ps.match(/\$script:Skipped\+\+/g) || [];
  const helper = ps.slice(ps.indexOf('function Add-NotRun'), ps.indexOf('function Add-NotRun') + 200);
  assert.equal(skips.length, 1, 'every skip goes through Add-NotRun so it is named');
  assert.ok(helper.includes('$script:Skipped++'));
});
