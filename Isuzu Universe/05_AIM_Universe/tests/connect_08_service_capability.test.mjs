#!/usr/bin/env node
/* ===========================================================================
   CONNECT-08 acceptance tests: Enable each service only when it returns
   supported work.

   How to run
     node --test tests/connect_08_service_capability.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  Missing optional IDS, fleet, stock or tender input does not break the
         working pricing/case journey.
     E2  Each enabled service shows its real source and response route; a test
         adapter is visibly development-only.

   Synthetic fixtures only.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'service_capability.js'));

test('CONNECT-08 E1: Missing optional IDS, fleet, stock or tender input does not break the working pricing/case journey.', () => {
  const reg = mod.makeRegistry({
    case_context: { case_id: 'SYN-CASE-CAP-01', part_number: 'SYN-PN-CAP' }
  });
  reg.register('pricing_core', {
    capability: 'internally_usable',
    returns_supported_work: true,
    source: 'synthetic_pricing_engine',
    response_route: 'internal_calculate',
    adapter_kind: 'internal'
  });

  const journey = reg.runPricingCaseJourney({
    case_id: 'SYN-CASE-CAP-01',
    part_number: 'SYN-PN-CAP'
    /* ids, fleet, stock, tender intentionally omitted */
  });

  assert.equal(journey.ok, true);
  assert.equal(journey.broken, false);
  assert.equal(journey.pricing_journey_usable, true);
  assert.deepEqual(journey.missing_optional_inputs.sort(), ['fleet', 'ids', 'stock', 'tender']);
  assert.ok((journey.statement || '').toLowerCase().includes('without optional'));
});

test('CONNECT-08 E2: Each enabled service shows its real source and response route; a test adapter is visibly development-only.', () => {
  const reg = mod.makeRegistry({
    case_context: { case_id: 'SYN-CASE-CAP-02', part_number: 'SYN-PN-CAP' }
  });
  reg.register('ids_read', {
    capability: 'internally_usable',
    returns_supported_work: true,
    source: 'synthetic_ids_fixture',
    response_route: 'ids_evidence_panel',
    adapter_kind: 'test',
    development_only: true,
    label: 'IDS read (test adapter)'
  });
  reg.register('unavailable_fleet', {
    capability: 'unavailable',
    returns_supported_work: false,
    source: null,
    response_route: null,
    adapter_kind: 'none'
  });

  const enabled = reg.describeEnabled();
  assert.equal(enabled.length, 1);
  assert.equal(enabled[0].service_id, 'ids_read');
  assert.equal(enabled[0].source, 'synthetic_ids_fixture');
  assert.equal(enabled[0].response_route, 'ids_evidence_panel');
  assert.equal(enabled[0].development_only, true);
  assert.equal(enabled[0].adapter_kind, 'test');
  assert.ok(
    (enabled[0].statement || '').toLowerCase().includes('development-only') ||
      (enabled[0].statement || '').toLowerCase().includes('test adapter'),
    'test adapter must be visibly development-only'
  );
  assert.equal(enabled[0].connected_badge, false);
});

test('CONNECT-08 E3: services declared in a hand-written fixture are enabled exactly as the fixture expects.', () => {
  /* The fixture is written by hand, so the module is judged against
     expectations it did not produce. */
  const fx = JSON.parse(readFileSync(join(ROOT, 'tests', 'fixtures', 'connect_08_services.json'), 'utf8'));
  const reg = mod.makeRegistry({ case_context: { case_id: 'SYN-CASE-CAP-03', part_number: 'SYN-PN-CAP' } });
  fx.services.forEach((row) => assert.equal(reg.register(row.id, row.spec).ok, true, row.id));

  const enabled = reg.describeEnabled();
  const want = fx.services.filter((r) => r.expect.enabled).map((r) => r.id).sort();
  assert.deepEqual(enabled.map((e) => e.service_id).sort(), want);

  enabled.forEach((e) => {
    const row = fx.services.find((r) => r.id === e.service_id);
    assert.equal(e.source, row.spec.source, e.service_id + ' source');
    assert.equal(e.response_route, row.spec.response_route, e.service_id + ' route');
    assert.equal(e.development_only, row.expect.development_only, e.service_id + ': ' + row.expect.why);
    assert.equal(e.connected_badge, false);
    assert.equal(/development-only/i.test(e.statement), row.expect.development_only,
      e.service_id + ' statement must say development-only exactly when it is');
  });
});
