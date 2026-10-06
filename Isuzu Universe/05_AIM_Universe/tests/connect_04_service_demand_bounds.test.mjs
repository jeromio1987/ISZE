#!/usr/bin/env node
/* ===========================================================================
   CONNECT-04 acceptance tests: Enforce service-demand and shared-applicability
   boundaries.

   How to run
     node --test tests/connect_04_service_demand_bounds.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (CONNECT-04):
     E1  Changing from internal to external service basis changes the labelled
         method rather than averaging them.
     E2  No band-level service cover is derived by dividing repeated market
         purchasing by a band expectation.

   Also checks: shared parts stay pooled; restricted euro aggregates stay out
   of external views; series codes become bands only through bandFor on
   series_to_band.csv.

   Synthetic fixtures only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CSV = path.resolve(__dirname, '../../../03_analytics/Isuzu/prism/data/series_to_band.csv');

const bands = (await import(new URL('../src/data/vehicle_bands.js', import.meta.url))).default;
const mod = (await import(new URL('../src/data/service_demand_bounds.js', import.meta.url))).default;

const RESULTS = {
  internal: { cover_pct: 62, method: 'internal_iml' },
  external: { cover_pct: 48, method: 'external_schedule' }
};

test('CONNECT-04 E1: Changing from internal to external service basis changes the labelled method rather than averaging them.', () => {
  const internal = mod.selectServiceBasis(RESULTS, 'internal');
  assert.equal(internal.ok, true);
  assert.equal(internal.method_label, mod.METHOD_INTERNAL);
  assert.equal(internal.value.cover_pct, 62);
  assert.equal(internal.averaged, false);

  const external = mod.selectServiceBasis(RESULTS, 'external');
  assert.equal(external.ok, true);
  assert.equal(external.method_label, mod.METHOD_EXTERNAL);
  assert.equal(external.value.cover_pct, 48);
  assert.equal(external.averaged, false);
  assert.notEqual(internal.method_label, external.method_label);
  assert.notEqual(
    (internal.value.cover_pct + external.value.cover_pct) / 2,
    external.value.cover_pct,
    'external result must not be an average'
  );

  // Shared parts pooled; restricted euros out of external view.
  const pooled = mod.poolSharedParts([
    { pn: 'S1', shared: true, qty: 3, eur: 30 },
    { pn: 'S2', applicability: 'shared', qty: 2, eur: 20 },
    { pn: 'E1', applicability: 'exclusive', qty: 1, eur: 10 }
  ]);
  assert.equal(pooled.shared_pool.pooled, true);
  assert.equal(pooled.shared_pool.qty, 5);
  assert.equal(pooled.shared_pool.eur, 50);
  assert.equal(pooled.exclusive.length, 1);

  const ext = mod.externalView({
    qty: 5,
    billed_eur: 100,
    cost_eur: 40,
    margin_pct: 35,
    restricted_euro: 9
  });
  assert.equal(ext.view.billed_eur, 100);
  assert.equal(ext.view.cost_eur, undefined);
  assert.equal(ext.view.margin_pct, undefined);
  assert.ok(ext.stripped_keys.includes('cost_eur'));

  const bf = bands.bandFor('NPR', CSV);
  assert.notEqual(bf, bands.UNRESOLVED);
  const via = mod.bandsForSeries(['NPR', 'N*'], CSV);
  assert.equal(via.ok, true);
  assert.equal(via.bands[0].tonnage_band, bf);
  assert.equal(via.bands[1].tonnage_band, bands.UNRESOLVED);
});

test('CONNECT-04 E2: No band-level service cover is derived by dividing repeated market purchasing by a band expectation.', () => {
  const refused = mod.bandServiceCover({
    derive_by_dividing_repeated_market_by_band_expectation: true,
    repeated_market_purchasing: 1000,
    band_expectation: 200
  });
  assert.equal(refused.ok, false);
  assert.equal(refused.cover, null);
  assert.equal(refused.refused, true);
  assert.match(refused.statement, /dividing repeated market purchasing/i);

  const also = mod.bandServiceCover({
    method: 'repeated_market_over_band_expectation',
    repeated_market_purchasing: 1000,
    band_expectation: 200
  });
  assert.equal(also.ok, false);

  const exclusive = mod.bandServiceCover({
    applicability: 'exclusive',
    exclusive_purchasing: 80,
    modelled_demand: 100,
    method_label: mod.METHOD_INTERNAL
  });
  assert.equal(exclusive.ok, true);
  assert.equal(exclusive.cover.purchasing, 80);
  assert.equal(exclusive.cover.modelled_demand, 100);
});
