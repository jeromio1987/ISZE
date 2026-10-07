#!/usr/bin/env node
/* U19: feed ledger-mapped offers through market_observation + comparable (unchanged). */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const market = require(path.join(ROOT, 'Isuzu Universe', '05_AIM_Universe', 'src', 'data', 'market_observation.js'));
const comparable = require(path.join(ROOT, 'Isuzu Universe', '05_AIM_Universe', 'src', 'data', 'comparable.js'));

const stagePath = process.argv[2];
const outPath = process.argv[3];
if (!stagePath || !outPath) {
  console.error('usage: node run_u19_ledger_through_evidence.mjs <stage.json> <out.json>');
  process.exit(2);
}

const stage = JSON.parse(fs.readFileSync(stagePath, 'utf8'));
const offersIn = stage.offers || [];
const asOf = '2026-10-07';

const groups = new Map();
for (const raw of offersIn) {
  const key = raw.case_id || (raw.market + '-' + raw.part_number);
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(raw);
}

const rows = [];
for (const [caseId, list] of groups.entries()) {
  const panelOffers = [];
  const ledgerById = {};
  for (const raw of list) {
    const ledger = raw._ledger || null;
    delete raw._ledger;
    const record = market.buildRecord(raw);
    const offer = market.toPanelOffer(record);
    panelOffers.push(offer);
    ledgerById[offer.observation_id] = ledger;
  }
  const partNumber = list[0].part_number;
  const marketCode = list[0].market;
  const panel = comparable.panel(
    { case_id: caseId, part_number: partNumber, market: marketCode, unit: 'piece' },
    panelOffers,
    { basis_level: 'public_advertised_retail', basis_unit: 'piece', as_of: asOf }
  );
  const all = (panel.eligible_offers || []).concat(panel.ineligible_offers || []);
  for (const r of all) {
    rows.push({
      observation_id: r.observation_id,
      case_id: caseId,
      part_number: partNumber,
      market: marketCode,
      eligible: (panel.eligible_offers || []).some((e) => e.observation_id === r.observation_id),
      reason_codes: (r.reasons || []).map((x) => x.code),
      reason_kinds: (r.reasons || []).map((x) => x.kind),
      ledger: ledgerById[r.observation_id] || null,
      eligible_offers_in_case: (panel.eligible_offers || []).length,
      ineligible_offers_in_case: (panel.ineligible_offers || []).length
    });
  }
}

fs.writeFileSync(outPath, JSON.stringify({ rows, offer_count: offersIn.length, case_count: groups.size }, null, 2), 'utf8');
console.log(JSON.stringify({ offer_count: offersIn.length, case_count: groups.size, result_rows: rows.length }));
