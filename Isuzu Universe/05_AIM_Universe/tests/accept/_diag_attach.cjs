#!/usr/bin/env node
'use strict';
/* Diagnostic: which attachment file names does the name check refuse?

Nothing here is an acceptance check. It exists to establish exactly where the
name check does and does not apply, because that decides whether a finding is a
defect or a bad test.
*/
const H = require('./lib/harness.cjs');
const recipients = H.requireModule(H.PATHS.recipients);

const owner = recipients.makeDevIdentity({ role: 'case_owner' });
const names = [
  'supplier_cost_list_2026.xlsx',
  'supplier cost list 2026.xlsx',
  'cost.xlsx',
  'costs.xlsx',
  'my_cost_file.xlsx',
  'invoices_2026.xlsx',
  'gross_margin_report.xlsx',
  'price_list_2026.xlsx',
  'pricelist.xlsx',
  'parts_purchase_price.xlsx',
  'cheap_offer.xlsx',
  'price_question.docx'
];
for (const name of names) {
  const res = recipients.canAttach(owner, { name });
  console.log(`${res.ok ? 'ACCEPTED' : 'refused '} ${String(res.ok ? '' : res.code).padEnd(34)} ${name}`);
}
