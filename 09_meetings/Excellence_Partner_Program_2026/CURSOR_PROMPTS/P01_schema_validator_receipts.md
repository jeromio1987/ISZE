# P01 — Schema, validation rules, validator CLI, receipts

> Read `00_START_HERE.md` first. Use Plan mode, then build.

## Goal
Build the validator for monthly sales-to-dealer files: a schema, the rule catalogue V001–V018 from the specification §5, a command-line tool, and a receipt (JSON and readable Markdown) for every file.

## Why
Distributors are independent and multi-brand. ISZE cannot force data, so the first thing a distributor sees after sending a file must be a clear, fair, fast answer: accepted, accepted with warnings, or not accepted and exactly what to correct. A file that satisfies the format but carries no information must not pass.

## Read first
- `TECH_SPEC_Partner_Intake_Phase0_2026-10-09.md` §4 (data standard), §5 (rules), §7 (receipts).
- `03_analytics/Isuzu/prism/data/dealer_sales/DEALER_SELL_OUT.md` and `03_analytics/Isuzu/prism/modules/dealer_sales_loader.py` (`normalize_pn`).
- One existing adapter, for the part-number and sidecar handling: `01_data/91_build/normalize_dealer_sellout_romania.py`.

## Build
```
04_tools/partner_intake/
  __init__.py
  config/partner_program.yaml      thresholds, forbidden-column list, alias table, working-day calendar, rule severities
  schema.py                        column spec, aliases, types, control-record spec
  rules.py                         one function per rule, each returns findings (rule id, severity, message, row numbers)
  validator.py                     validate(path, distributor_code, period, received_at, context) -> ValidationResult
  receipts.py                      render JSON and Markdown from a ValidationResult
  cli.py                           python -m partner_intake validate <file> --distributor X --period YYYY-MM [--received 2026-02-12]
  tests/                           pytest; synthetic fixtures generated in conftest or a fixtures/ builder
```
- CSV (UTF-8) and Excel (first sheet is data; optional sheet `control`). Control record also accepted as `<file>.control.json`.
- Every rule reads its thresholds from `partner_program.yaml`. No magic numbers in code.
- Part numbers: keep `part_number_raw`; normalise to ten digits where numeric; alphanumeric accessory codes go to a sidecar list and stay visible in the receipt.
- Timeliness (V011) uses a working-day calendar in config; month-end plus ten working days.
- V016: distributor id must equal the one given on the command line; refuse to merge UTI/UMI or IUK/ITUK.
- V018: hidden price detection — numeric column, unknown name, currency-like decimals. Hold for review, do not guess.
- Receipt text is a **shared** document: roles, not names; plain English; each finding says what to correct and how to resubmit.

## Acceptance tests (all must exist and pass)
1. For every rule V001–V018: one fixture that passes and one that fails, with the exact rule id and severity asserted.
2. A file with a column `selling_price` is **rejected** (V003) and the receipt says price data is not accepted and why. A file with a column `Prijs` and one named `unit_net` holding currency-like decimals is rejected or held (V003/V018).
3. `ALL` as `dealer_id` passes in quarter 1–2 mode with an information finding (V014) and fails in quarter-3 mode.
4. A file received 12 working days after month-end reports `LATE` with `days_late = 2`; a file on day 10 reports `ON_TIME`.
5. Golden receipt: the full Markdown receipt of one failing fixture is compared to a stored expected text.
6. Alias mapping: a file using the native Romania layout headers (part number, quantity) is accepted through the alias table with no code change.
7. No test touches real data. `pytest 04_tools/partner_intake` and the PRISM suite both pass.

## Constraints
Add a `conftest.py` that puts `04_tools` on `sys.path` so `import partner_intake` works (same pattern as `03_analytics/Isuzu/prism/tests/conftest.py`). No network access. No pandas-only logic that cannot run on a 200,000-row file in a few seconds (check with a generated large fixture). Do not read or write outside `04_tools/partner_intake/` and a temp dir, except the receipt output path given on the command line.

## Out of scope
Ledger, versions and normalisation to the canonical long format (P02). Reconciliation (P04).

## Return packet
Files, rule table with severities as implemented, test output, a sample receipt (synthetic) pasted in full, and any rule where the spec was ambiguous with your chosen default.
