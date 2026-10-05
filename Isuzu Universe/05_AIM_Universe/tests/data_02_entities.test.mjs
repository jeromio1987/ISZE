#!/usr/bin/env node
/* ===========================================================================
   DATA-02 acceptance tests: distributors, purchasing accounts and sites stay
   distinct.

   How to run
     node --test tests/data_02_entities.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (DATA-02):
     E1  Cross-country/shared-name fixtures cannot silently merge distinct
         entities.
     E2  An account covering multiple sites remains combined until a genuine
         split is supported; national plus included dealer records cannot be
         added.

   src/data/manifest.js is loaded as data_contracts.test.mjs loads it. Every
   entity, account, site and quantity below is invented. The restricted payload
   is never read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifest = require(path.join(ROOT, 'src/data/manifest.js'));

const ROWS = [
  { country: 'United Kingdom', distributor: 'ITUK', purchasing_account: 'SYN-100', quantity: 10 },
  { country: 'United Kingdom', distributor: 'IUK', purchasing_account: 'SYN-100', quantity: 5 },
  { country: 'Portugal', distributor: 'Synthetic Motors', purchasing_account: 'SYN-519', quantity: 7 },
  { country: 'Spain', distributor: 'Synthetic Motors', purchasing_account: 'SYN-519', quantity: 3 },
  { country: 'Israel', distributor: 'UMI', purchasing_account: 'SYN-1797', quantity: 4 },
  { country: 'Israel', distributor: 'UTI', purchasing_account: 'SYN-1799', quantity: 6 },
  { country: 'Portugal', distributor: null, raw_name: 'Synthetic Unmatched Trading', quantity: 2 }
];

test('DATA-02 E1: cross-country and shared-name fixtures cannot silently merge distinct entities', () => {
  const id = (r) => manifest.sourceEntityId(r);
  assert.notEqual(id(ROWS[2]), id(ROWS[3]), 'the same name and account in two countries share one identifier');
  assert.notEqual(id(ROWS[0]), id(ROWS[1]), 'ITUK and IUK share one identifier');
  assert.equal(id(ROWS[2]), id(Object.assign({}, ROWS[2], { quantity: 99 })), 'the identifier is not stable');

  const out = manifest.combineEntities(ROWS);
  assert.equal(out.groups.length, 7, 'distinct entities were merged into fewer groups');
  const total = (country, name) => out.groups.find((g) => g.country === country && g.distributor === name).quantity;
  assert.equal(total('Portugal', 'Synthetic Motors'), 7);
  assert.equal(total('Spain', 'Synthetic Motors'), 3);
  assert.equal(total('United Kingdom', 'ITUK'), 10);
  assert.equal(total('United Kingdom', 'IUK'), 5);
  const unmatched = out.groups.filter((g) => g.unmatched);
  assert.equal(unmatched.length, 1, 'the unmatched name was dropped or folded into a matched entity');
  assert.equal(unmatched[0].name_as_received, 'Synthetic Unmatched Trading');
  assert.equal(unmatched[0].quantity, 2);

  const shared = manifest.canMerge(ROWS[2], ROWS[3]);
  assert.equal(shared.ok, false, 'two entities that share only a name were merged without a stated source');
  assert.match(shared.statement, /not merged/);
  const pair = manifest.canMerge(ROWS[4], ROWS[5], { source: 'Synthetic declaration', declared_on: '2026-01-01' });
  assert.equal(pair.ok, false, 'UMI and UTI were merged because a declaration was supplied');
  assert.equal(pair.separate_entities, true);
});

test('DATA-02 E2: an account covering several sites stays combined until a genuine split is supported, and national plus included dealer records are not added', () => {
  const rows = [
    { country: 'United Kingdom', distributor: 'ITUK', purchasing_account: 'SYN-200', site: null, quantity: 12 }
  ];
  const sites = ['SYN-SITE-A', 'SYN-SITE-B'];
  const asOf = '2026-03-01';
  const sourced = sites.map((s) => ({ purchasing_account: 'SYN-200', site: s, effective_from: '2026-01-01',
    effective_to: null, source: 'Synthetic site register' }));

  const none = manifest.splitAccount(rows, 'SYN-200', [], asOf);
  assert.equal(none.ok, false);
  assert.equal(none.combined, true, 'an account with no site link is not kept combined');
  assert.deepEqual(none.rows, rows, 'the combined account rows were changed by a refused split');

  const unsourced = manifest.splitAccount(rows, 'SYN-200', sourced.map((l) => Object.assign({}, l, { source: null })), asOf);
  assert.equal(unsourced.ok, false, 'a split was accepted from links that state no source');
  const future = manifest.splitAccount(rows, 'SYN-200', sourced.map((l) => Object.assign({}, l, { effective_from: '2026-06-01' })), asOf);
  assert.equal(future.ok, false, 'a split was accepted from links not yet in effect');
  const single = manifest.splitAccount(rows, 'SYN-200', sourced.slice(0, 1), asOf);
  assert.equal(single.ok, false, 'one site link was read as a split of the account');

  const split = manifest.splitAccount(rows, 'SYN-200', sourced, asOf);
  assert.equal(split.ok, true, 'a supported split is refused');
  assert.deepEqual(split.sites.slice().sort(), sites);
  assert.equal(split.combined, false);
  assert.equal(split.quantity_apportioned, false, 'quantities were apportioned to sites that the source does not split');
  assert.deepEqual(split.rows, rows, 'the recorded account rows were rewritten by the split');

  const national = { country: 'Portugal', distributor: 'Synthetic Motors', scope: 'national', period: '2026-H1',
    includes_dealers: true, quantity: 40 };
  const dealer = { country: 'Portugal', distributor: 'Synthetic Motors', scope: 'dealer', site: 'SYN-DEALER-1',
    period: '2026-H1', quantity: 9 };
  const added = manifest.addRecords(national, dealer);
  assert.equal(added.ok, false, 'a national record and a dealer record it includes were added');
  assert.equal(added.total, null, 'a total was produced for a double count');
  const dealers = manifest.dealersOf(national, []);
  assert.deepEqual(dealers.dealers, [], 'national information acquired dealers no record states');
  assert.match(dealers.statement, /no dealer record/i);
});