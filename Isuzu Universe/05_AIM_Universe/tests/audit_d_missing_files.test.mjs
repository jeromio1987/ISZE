#!/usr/bin/env node
/* ===========================================================================
   Audit fix D (U27): a missing series_to_band.csv and a truncated case file
   are refused with a clear message instead of throwing.

   How to run
     node --test tests/audit_d_missing_files.test.mjs

   Synthetic fixtures only. Every file is written to a fresh temp folder.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdtempSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const bounds = require(join(ROOT, 'src', 'data', 'service_demand_bounds.js'));
const bands = require(join(ROOT, 'src', 'data', 'vehicle_bands.js'));
const store = require(join(ROOT, 'src', 'case', 'store.js'));

test('CONNECT-04 audit D: a deleted series_to_band.csv returns ok:false, not a throw', () => {
  const dir = mkdtempSync(join(tmpdir(), 'aim-d-csv-'));
  const csv = join(dir, 'series_to_band.csv');
  writeFileSync(csv, 'code,tonnage_band\nSYNA,3.5t\n', 'utf8');
  bands.resetCache();
  const good = bounds.bandsForSeries(['SYNA'], csv);
  assert.equal(good.ok, true, 'control: the file is read when present');
  assert.equal(good.bands[0].tonnage_band, '3.5t');

  rmSync(csv);
  bands.resetCache();
  let out;
  assert.doesNotThrow(() => { out = bounds.bandsForSeries(['SYNA'], csv); });
  assert.equal(out.ok, false);
  assert.equal(out.bands, null);
  assert.match(out.error, /series_to_band/);
  rmSync(dir, { recursive: true, force: true });
});

test('SAFE audit D: a truncated case file is refused clearly by the file adapter and the service', () => {
  const dir = mkdtempSync(join(tmpdir(), 'aim-d-case-'));
  const adapter = store.makeFileAdapter({ dir });
  const service = store.makeCaseService({ adapter });
  const made = service.create({ case_id: 'SYN-D-1', part_number: 'SYN-PN-D', customer: 'Synthetic D', by: 'synthetic' });
  assert.equal(made.ok, true);
  const file = join(dir, 'cases', 'SYN-D-1.json');
  const text = readFileSync(file, 'utf8');
  writeFileSync(file, text.slice(0, Math.floor(text.length / 2)), 'utf8');

  let raw;
  assert.doesNotThrow(() => { raw = adapter.load('SYN-D-1'); });
  assert.equal(raw, null);
  const checked = adapter.loadChecked('SYN-D-1');
  assert.equal(checked.ok, false);
  assert.equal(checked.code, 'STORED_RECORD_UNREADABLE');

  let opened;
  assert.doesNotThrow(() => { opened = service.reopen('SYN-D-1'); });
  assert.equal(opened.ok, false);
  assert.equal(opened.code, 'STORED_RECORD_UNREADABLE');
  assert.match(opened.error, /SYN-D-1/);
  rmSync(dir, { recursive: true, force: true });
});
