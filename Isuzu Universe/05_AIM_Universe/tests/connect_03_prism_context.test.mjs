#!/usr/bin/env node
/* ===========================================================================
   CONNECT-03 acceptance tests: Add read-only PRISM context at its actual
   market level.

   How to run
     node --test tests/connect_03_prism_context.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (CONNECT-03):
     E1  A dealer review cannot acquire a per-truck performance rate from a
         national total.
     E2  The unusable fleet forecast beyond 2025 is excluded; each historical
         measure retains its own accepted basis.

   Synthetic PRISM-shaped fixtures only. No real PRISM outputs.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';

const mod = (await import(new URL('../src/data/prism_context.js', import.meta.url))).default;

const DEALER = { dealer_id: 'SYNTH-D1', distributor: 'UMI', market: 'IL' };

const FIXTURES = [
  {
    id: 'M-NAT-UIO-2024',
    kind: 'trucks_in_service',
    value: 12000,
    unit: 'vehicles',
    source: 'synthetic PRISM UIO table',
    period: 'CY2024',
    year: 2024,
    population: 'national',
    accepted_basis: 'historical_uio_v1',
    denominator_version: 'uio_v1'
  },
  {
    id: 'M-NAT-SPEND-2024',
    kind: 'measured_spend',
    value: 4800000,
    unit: 'EUR',
    source: 'synthetic PRISM spend',
    period: 'CY2024',
    year: 2024,
    population: 'national',
    accepted_basis: 'billed_eur_v2',
    denominator_version: 'spend_v2'
  },
  {
    id: 'M-FLEET-FORECAST-2027',
    kind: 'fleet_forecast',
    value: 15000,
    unit: 'vehicles',
    source: 'synthetic PRISM forecast',
    period: 'CY2027',
    year: 2027,
    population: 'national',
    accepted_basis: 'forecast_v0',
    forecast: true,
    denominator_version: 'forecast_v0'
  },
  {
    id: 'M-TARGET-2024',
    kind: 'modelled_target',
    value: 5200000,
    unit: 'EUR',
    source: 'synthetic PRISM target',
    period: 'CY2024',
    year: 2024,
    population: 'national',
    accepted_basis: 'target_wallet_v3',
    denominator_version: 'target_v3'
  }
];

test('CONNECT-03 E1: A dealer review cannot acquire a per-truck performance rate from a national total.', () => {
  const refused = mod.attachPrismContext(DEALER, FIXTURES, {
    request_per_truck_from_national: true
  });
  assert.equal(refused.ok, false);
  assert.equal(refused.per_truck.per_truck_rate, null);
  assert.match(refused.per_truck.statement, /cannot acquire a per-truck/i);

  const allocated = mod.attachPrismContext(DEALER, FIXTURES, {
    allocate_national_to_dealer: true
  });
  assert.equal(allocated.ok, false);
  assert.equal(allocated.per_truck.per_truck_rate, null);

  const plain = mod.attachPrismContext(DEALER, FIXTURES);
  assert.equal(plain.per_truck.per_truck_rate, null,
    'national totals alone must not become a dealer per-truck rate');
  assert.ok(plain.national_totals.length >= 1);
  assert.match(plain.per_truck.statement, /national total is not divided|No dealer-level/i);
});

test('CONNECT-03 E2: The unusable fleet forecast beyond 2025 is excluded; each historical measure retains its own accepted basis.', () => {
  const ctx = mod.attachPrismContext(DEALER, FIXTURES);
  const ids = ctx.measures.map((m) => m.id);
  assert.ok(!ids.includes('M-FLEET-FORECAST-2027'), '2027 fleet forecast must be excluded');
  assert.equal(ctx.excluded_forecasts.length, 1);
  assert.equal(ctx.excluded_forecasts[0].year, 2027);

  const historical = ctx.measures.filter((m) => m.id !== 'M-FLEET-FORECAST-2027');
  assert.ok(historical.length >= 3);
  const bases = new Set(historical.map((m) => m.accepted_basis));
  assert.ok(bases.has('historical_uio_v1'));
  assert.ok(bases.has('billed_eur_v2'));
  assert.ok(bases.has('target_wallet_v3'));
  assert.equal(bases.size, historical.length,
    'each historical measure keeps its own accepted basis');

  const versions = ctx.denominator_versions;
  assert.ok(versions.length >= 3, 'different denominator versions stay separate');
  versions.forEach((v) => {
    assert.ok(v.key.length > 0);
    assert.ok(v.measures.length >= 1);
  });
});
