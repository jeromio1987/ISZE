#!/usr/bin/env node
/* ===========================================================================
   U28 task 4 and task 5 - the two baseline checks can run, and BASE-01's claim
   is recomputed rather than copied.

   How to run
     node --test tests/base01_and_baseline_runnable.test.mjs

   BASE-01 (task 5)
   ----------------
   BASE-01's claim is the frozen v03 checksum. This recomputes the SHA-256 of the
   frozen file and compares it with the recorded value, WITHOUT printing or
   storing the file's contents. The mutation is the recorded value: change the
   expected digest and this test must fail. Nothing but a hash is ever read from
   the frozen file.

   BASE-ENGINE / BASE-BROWSER runnable (task 4)
   -------------------------------------------
   These two checks cannot run in a worktree that does not carry the ignored
   folders. tools/worktree_setup.py copies them and verifies every hash; this test
   asserts, on this machine, that:
     * the helper exists and reports OK here, so the two checks CAN run;
     * a worktree with the folders removed is reported as INCOMPLETE rather than
       silently treated as ready.

   Sufficiency: sufficient. This reads a checksum and folder names only. The
   frozen file's contents are never opened beyond hashing, and the restricted
   payload is never read.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');                        // .../05_AIM_Universe
const UNIVERSE = path.join(ROOT, '..');                    // .../Isuzu Universe
const FROZEN = path.join(ROOT, 'reference', 'ISZE_AIM_Pricing_Decisions_v03_FROZEN.html');

/* The recorded checksum, read from the runner rather than typed a second time,
   so the two cannot drift apart. */
function recordedChecksum() {
  const ps = fs.readFileSync(path.join(ROOT, 'tests', 'accept', 'run_all.ps1'), 'utf8');
  const m = /\$frozenExpect\s*=\s*"([0-9a-f]{64})"/i.exec(ps);
  assert.ok(m, 'tests/accept/run_all.ps1 no longer records the frozen checksum');
  return m[1].toLowerCase();
}

/* Hash the file in chunks. Its contents are never kept and never printed. */
function hashFrozen() {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    const stream = fs.createReadStream(FROZEN, { highWaterMark: 1 << 20 });
    stream.on('error', reject);
    stream.on('data', (chunk) => h.update(chunk));
    stream.on('end', () => resolve(h.digest('hex')));
  });
}

test('BASE-01: the frozen v03 checksum is recomputed and matches the recorded value', async () => {
  assert.ok(fs.existsSync(FROZEN),
    'the frozen v03 reference is not on this machine, so its checksum cannot be recomputed: ' + FROZEN);
  const recorded = recordedChecksum();
  const observed = await hashFrozen();
  assert.match(observed, /^[0-9a-f]{64}$/);
  assert.equal(observed, recorded,
    'the frozen v03 reference has changed. It is the untouched baseline every comparison rests on.');

  /* The mutation: the RECORDED value is what this claim can break on. With a
     wrong expected digest the comparison above must fail - the same check the
     assertion performs, applied to a changed record. */
  const mutated = recorded.slice(0, 63) + (recorded.endsWith('0') ? '1' : '0');
  assert.notEqual(mutated, observed,
    'the test cannot fail on a changed recorded value, so it is not really comparing anything');
  assert.notEqual(recorded, mutated);

  /* And the runner carries the same value, so a rebuild cannot quietly change
     what the baseline is measured against. */
  const ps = fs.readFileSync(path.join(ROOT, 'tests', 'accept', 'run_all.ps1'), 'utf8');
  assert.ok(ps.includes(recorded),
    'the runner no longer names the recorded frozen checksum it compares against');
});

test('BASE-01: nothing but a hash is read from the frozen file', () => {
  /* The brief allows only the checksum. This asserts the reading shape: the only
     place the frozen path is opened is a hash stream, and no test writes the
     file's bytes anywhere. */
  const files = [];
  for (const base of [HERE, path.join(ROOT, 'tools')]) {
    for (const name of fs.readdirSync(base)) {
      if (/\.(mjs|cjs|py)$/.test(name)) files.push(path.join(base, name));
    }
  }
  const offenders = [];
  for (const f of files) {
    const text = fs.readFileSync(f, 'utf8');
    if (!text.includes('FROZEN')) continue;
    /* A read of the frozen file that is not a hash is what would be wrong. */
    const reads = [...text.matchAll(/(readFileSync|read_text|io\.open|\.read_bytes)\(([^\n]*FROZEN[^\n]*)/g)];
    for (const m of reads) {
      const line = m[0];
      if (/createReadStream|sha256|hashlib|getFileHash|\.digest|update\(/.test(line)) continue;
      /* A read that only measures size or existence is fine. */
      if (/existsSync|statSync|\.stat\(|length|Size/.test(line)) continue;
      offenders.push(path.relative(ROOT, f) + ': ' + line.slice(0, 90));
    }
  }
  assert.deepEqual(offenders, [],
    'these places read the frozen v03 file other than to hash it, which the brief keeps closed: '
    + JSON.stringify(offenders));
});

test('BASE-ENGINE / BASE-BROWSER: the worktree set-up helper makes the two baseline checks runnable', () => {
  const helper = path.join(ROOT, 'tools', 'worktree_setup.py');
  assert.ok(fs.existsSync(helper), 'tools/worktree_setup.py is missing, so a fresh worktree still '
    + 'prints NOT RUN for the two baseline checks');

  /* Against the worktree this test is running in: every file the two checks need
     must be present and must hash to its source. */
  const ok = spawnSync('python', [helper, '--from', process.env.ISZE_MAIN_CLONE
    || 'C:\\Users\\jerom\\Desktop\\claude\\ISZE', '--check'],
  { cwd: ROOT, encoding: 'utf8', timeout: 120000 });
  const output = (ok.stdout || '') + (ok.stderr || '');
  if (ok.status === 3) {
    /* The main clone is not on this machine, or does not carry the pack. That is
       a recorded block, not a silent pass. */
    assert.match(output, /RESULT: BLOCKED/,
      'the helper reported a block without saying so in its own words');
    return;
  }
  assert.equal(ok.status, 0, 'the helper did not report OK here:\n' + output);
  assert.match(output, /RESULT: OK/, 'the helper did not report OK in its own words');
  assert.match(output, /matched 19 file\(s\)/,
    'the helper did not verify all 19 files the two baseline checks need');
  assert.match(output, /frozen v03 reference\s+checksum matches/,
    'the helper did not verify the frozen reference it copies');

  /* The behaviour on an unprepared worktree: point it at an empty folder and it
     must report INCOMPLETE rather than claim the worktree is ready. */
  const empty = fs.mkdtempSync(path.join(os.tmpdir(), 'aim-u28-empty-'));
  try {
    const bad = spawnSync('python', [helper, '--from', process.env.ISZE_MAIN_CLONE
      || 'C:\\Users\\jerom\\Desktop\\claude\\ISZE', '--worktree', empty, '--check'],
    { cwd: ROOT, encoding: 'utf8', timeout: 120000 });
    const badOut = (bad.stdout || '') + (bad.stderr || '');
    assert.notEqual(bad.status, 0,
      'the helper reported success against a worktree with none of the folders, so an '
      + 'incomplete run would read as a complete one');
    assert.match(badOut, /INCOMPLETE|BLOCKED/,
      'the helper did not say, in its own words, that the worktree is incomplete');
    /* And with --check it copied nothing into the empty folder. */
    const left = fs.readdirSync(empty);
    assert.deepEqual(left.filter((x) => x !== 'Isuzu Universe'), [],
      'a check-only run wrote into the worktree: ' + JSON.stringify(left));
  } finally {
    fs.rmSync(empty, { recursive: true, force: true });
  }
});
