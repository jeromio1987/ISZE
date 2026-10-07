#!/usr/bin/env node
/* ===========================================================================
   U28 task 3 (UX-01..08): one browser-level check per UX screen, on the real
   built layout at a narrow and a wide viewport.

   How to run
     node --test tests/ux_screens_browser.test.mjs

   Why this file exists
   --------------------
   UX-01..08 were covered by tests that render into a stub document. A stub
   evaluates no @media query and paints no real shell, so it cannot answer "does
   this screen exist on the page a person opens". This file drives the REAL built
   artifact in real Chrome, at 1440x900 and at 1280x820, and asserts that each of
   the eight screens paints its own content with no blank region, no NaN and no
   "undefined", and that the working context and the exact part reference travel
   with it.

   It does not replace the stub-level checks in tests/ux_0N_*.test.mjs, which
   still ask the finer questions (assumption trace, sensitivity grid, field
   verdicts). It closes the gap those files cannot: the layout the product
   actually serves.

   The reading is produced by tests/accept/ux_screens_wide_narrow.py. This file
   asserts the structure that makes that reading meaningful (the artifact is not
   older than its own source, the run is timestamped after the artifact) and then
   reads the measured result, so a stale screenshot cannot pass as a current one.

   Sufficiency: the artifact is built from the synthesic fixture by tools/build.py,
   which is what the run uses. No restricted payload is read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const ARTIFACT = path.join(ROOT, 'dist', 'ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html');
const READING = path.join(ROOT, 'tests', 'accept', '_out', 'ux_screens_wide_narrow.json');
const RUNNER = path.join(ROOT, 'tests', 'accept', 'ux_screens_wide_narrow.py');

const SCREENS = [
  ['UX-01', 'decision', 'Sales evidence'],
  ['UX-02', 'objectives', 'Two objectives'],
  ['UX-03', 'economics', 'Price & profit test'],
  ['UX-04', 'economics', 'Price & profit test'],
  ['UX-05', 'decision', 'Sales evidence'],
  ['UX-06', 'decision', 'Sales evidence'],
  ['UX-07', 'position', 'Price position'],
  ['UX-08', 'action', 'Internal action']
];

function reading() {
  assert.ok(fs.existsSync(RUNNER),
    'tests/accept/ux_screens_wide_narrow.py is missing, so the layout was never measured');
  const appSource = path.join(ROOT, 'src', 'ui', 'app.js');
  assert.ok(fs.existsSync(ARTIFACT), 'the built artifact is missing; run python tools/build.py');
  assert.ok(fs.existsSync(READING),
    'no reading at ' + READING + '; run python tests/accept/ux_screens_wide_narrow.py');
  const data = JSON.parse(fs.readFileSync(READING, 'utf8'));
  const artifactMtime = fs.statSync(ARTIFACT).mtimeMs;
  const sourceMtime = fs.statSync(appSource).mtimeMs;
  assert.ok(artifactMtime >= sourceMtime - 1000,
    'the artifact is older than src/ui/app.js, so it is not the layout that ships');
  const readingMs = Date.parse(data.generated_at);
  assert.ok(readingMs >= artifactMtime,
    'the reading is older than the artifact: reading ' + data.generated_at
    + ', artifact ' + new Date(artifactMtime).toISOString());
  return data;
}

test('UX-01..08 E1: every screen paints on the real built layout, narrow and wide', () => {
  const data = reading();
  const missing = [];
  for (const [task, view, label] of SCREENS) {
    for (const vp of data.viewports) {
      const row = (data.screens || []).find((s) => s.view === view && s.viewport === vp.label);
      if (!row) { missing.push(task + '/' + vp.label); continue; }
      if (!row.painted || row.defects.length) {
        missing.push(task + '/' + vp.label + ' ' + JSON.stringify(row.defects));
      }
    }
    assert.ok((data.screens || []).some((s) => s.view === view),
      'no reading for the ' + label + ' screen (' + view + '), so ' + task + ' was not measured');
  }
  assert.deepEqual(missing, [],
    'these screens did not paint cleanly on the real layout: ' + JSON.stringify(missing));
  assert.equal(data.viewports.length, 2, 'the measurement must cover a narrow and a wide viewport');
  /* The controls a reader needs must be visible on every screen, not only the
     content: a screen with no reachable control is a picture, not a workspace. */
  for (const row of data.screens) {
    assert.ok(row.visible_controls > 0 || row.all_controls === 0,
      row.view + ' at ' + row.viewport + ' has controls but none is visible');
    assert.equal(row.hidden_essential_controls, 0,
      row.view + ' at ' + row.viewport + ' hides an essential control');
  }
});

test('UX-01 E1: the same working context and part reference travel with every screen', () => {
  const data = reading();
  const keys = new Set((data.screens || []).map((s) => s.view + '/' + s.viewport));
  assert.ok(keys.size >= 8, 'the run covered ' + keys.size + ' view/viewport pairs, not 8');
  for (const row of data.screens) {
    assert.ok(row.part_reference_carried,
      row.view + ' at ' + row.viewport + ' does not carry the exact part reference');
    assert.ok(row.context_carried,
      row.view + ' at ' + row.viewport + ' does not carry the working context strip');
  }
});

test('UX-06 E1: an absent optional source paints a labelled narrower review, not a blank panel', () => {
  const data = reading();
  const row = (data.screens || []).find((s) => s.absent_source_state !== undefined
    && s.absent_source_state !== null);
  assert.ok(row, 'the run never removed an optional source, so UX-06 was not measured');
  assert.equal(row.absent_source_state.panel_present, true,
    'removing an optional source left no labelled narrower review');
  assert.equal(row.absent_source_state.blank, false,
    'removing an optional source left a blank panel');
  assert.equal(row.absent_source_state.billing_still_shown, true,
    'the supported billing evidence is no longer shown after an optional source is removed');
  assert.equal(row.absent_source_state.defect, false,
    'removing an optional source produced NaN, undefined or a failure card');
  assert.ok(row.absent_source_state.label,
    'the narrower review carries no label naming what was removed');
});
