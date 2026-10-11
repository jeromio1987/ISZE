# P03 — Feed status ledger and register refresh

> Read `00_START_HERE.md` first. Needs P02. Plan mode, then build.

## Goal
One authoritative table of what each distributor has **agreed**, what has **arrived**, and what is **missing**, so that the workspace register matches the field. Today the register lists feeds for ITUK, IUK, Ireland, UTI, Greece, Portugal and Romania, while the August 2026 sales-review minutes show that Germany sends monthly since May 2025 and that other feeds are agreed in principle.

## Read first
`05_memory/briefs/sales_reviews_Koen_2026-08-05_06.md`, `09_meetings/PORTUGAL_Sales_Review_2026/MINUTES_ISZE_Astara_Portugal_2026-07-29.md`, `01_data/DATA_MANIFEST.md` §05, `03_analytics/Isuzu/prism/data/dealer_sales/DEALER_SELL_OUT.md`, the ledger from P02.

## Build
- `04_tools/partner_intake/config/feeds_status.yaml`: one entry per distributor in scope (19; CIS excluded). Fields: `distributor_code`, `kickback` (yes/no), `status` (`receiving`, `agreed`, `asked`, `unknown`), `grain_expected` (`dealer_pn`, `network_pn`, `unknown`), `since`, `last_period_received` (filled by code from the ledger), `source_of_status` (file and date), `owner_role`, `next_step`.
- Seed it **only from documented sources** (the minutes, the manifest). Where nothing is documented write `unknown`. Never infer.
- A report command `feeds report` → Markdown table plus a CSV, showing agreed versus received and the gap in months.
- A proposed edit (as a diff, not applied) to `DATA_MANIFEST.md` §05 and `ISZE_OS_DATA_MAP.yaml` so the register reflects the field. **Do not apply the edit**; Jerome decides.

## Acceptance tests
1. Every one of the 19 distributors appears exactly once; CIS markets do not.
2. Germany shows `receiving`, source = the ISD minutes; Benelux, Sweden, Norway, UMI show `unknown`.
3. The report flags every distributor with `status in (receiving, agreed)` and no received month.
4. No status is set without a `source_of_status`.
5. The proposed manifest diff is produced but the manifest file is unchanged.

## Out of scope
Contacting distributors. Any mail. Editing the manifest.

## Return packet
The report, the list of `unknown` entries as questions for Jerome, the proposed diff.
