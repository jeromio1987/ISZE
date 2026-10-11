# Partner Intake, Phase 0 — technical specification

**Technical white paper for the developer and for Cursor** · internal draft v1 · 9 October 2026
Companion to `Excellence_Partner_White_Paper_2026-10-09` (the case) and `ROI model`. This document is the build brief: what to make, in what shape, with which rules, and how to know it works.

---

## 1. Purpose and scope

The Excellence Partner Program starts on 1 April 2027 (FY2028). It needs five things to exist by then, without a server, a sign-in or a platform: a way to **receive** monthly sales-to-dealer files, a **validator** that checks them against the data standard, a **ledger** that remembers what arrived and which version is active, an **eligibility job** that applies the gates every quarter, and a **monthly return** that goes back to each distributor. This is Phase 0. Everything runs on files, scripts and the existing PRISM data layer.

**Out of scope for Phase 0:** a web upload, sign-in, a hosted service, SAP posting (the job produces a proposal file; people post it), anything that handles prices, customer names or chassis numbers, and the value of air freight. **Never:** send mail, ship, deploy or overwrite a versioned deliverable without an explicit instruction (workspace rule `isze-no-ship-without-ok`).

Evidence labels used below: **[M]** measured in the workspace, **[P]** proposal, **[U]** unknown and to be decided.

## 2. Principles

1. **Reuse, do not rebuild.** The canonical long format, the adapters `01_data/91_build/normalize_dealer_sellout_*.py` and the loader `03_analytics/Isuzu/prism/modules/dealer_sales_loader.py` already exist **[M]**. New code produces files in that format and calls those loaders.
2. **Raw is immutable.** A received file is never edited. Corrections arrive as a new version.
3. **Absence is a source gap, never weak sales.** The validator and every report say so.
4. **Price-free by design.** A file that carries prices is rejected, not trimmed.
5. **Every state change is logged,** with who, when, what and why.
6. **Plain language to distributors.** Receipts and returns are shared documents: roles not names, "sales to dealer", no internal nicknames.
7. **Fiscal years.** FY2028 starts 1 April 2027.

## 3. Architecture

```
distributor ──► 01_data/90_INBOX/partner_intake/<DB>/            (drop; unsorted)
                    │  intake.py: identify, hash, copy
                    ▼
01_data/12_raw/dealer_sales/<DB>/<period>/<file>__v<n>           (immutable raw)
                    │  validator: rules V001…V018 → receipt
                    ▼
01_data/00_derived/partner_intake/ledger.parquet                 (state of every file)
01_data/00_derived/partner_intake/receipts/<DB>/<period>_v<n>.json|.md
                    │  accept: pass → normalise via adapter
                    ▼
01_data/00_derived/dealer_sellout_long_<DB>_CY<yyyy>.csv         (canonical long; existing)
                    │  reconcile.py / eligibility.py / returns.py / monitor.py
                    ▼
01_data/00_derived/partner_intake/eligibility_<FYQ>.csv, discount_proposal_<FYQ>.csv
09_meetings/…/returns/<DB>/<period>.html   (draft, not shipped)
```

Code lives in `04_tools/partner_intake/` (package, CLI, tests). Configuration lives in `04_tools/partner_intake/config/partner_program.yaml`. Folder names follow `paths.yaml`; use `04_tools/_shared/paths.py`, never hard-coded drive paths.

## 4. Data standard (the contract) [P]

One file per distributor per calendar month. CSV (UTF-8) or Excel (first sheet is data; an optional sheet `control` carries the coverage declaration). One row per dealer, site, part and period.

| Column | Required | Rule |
|---|---|---|
| `distributor_id` | yes | ISZE distributor code (PRISM `distributor_code`); must equal the drop folder |
| `dealer_id` | yes from quarter 3, else target | Stable code; never reused; `ALL` allowed only while per-dealer detail is not yet a condition |
| `site_id` | no | Where a dealer has several sites |
| `part_number` | yes | Isuzu part number as sold; normalised to 10 digits where numeric |
| `quantity` | yes | Units; negative for returns and corrections |
| `period` | yes | `YYYY-MM`; equals the file's reporting month |
| `transaction_date` | no | ISO date; must fall inside `period` |
| `transaction_type` | no | `sale`, `return`, `credit`, `correction` |
| `record_id` | no | Stable line id, for matching corrections |
| `file_version` | yes | Integer; a resubmission increments |

**Control record** (`<file>.control.json` or sheet `control`): `dealer_sites_included` (int), `known_exclusions` (text), `first_date`, `last_date`, `returns_included` (bool), `full_range` (bool), `changes_affecting_comparison` (text). A file without a complete control record fails V010.

**Forbidden content:** any column or value that is a selling price, margin, customer name, VIN or chassis number, person name or workshop order. Detected by name (V003) and by pattern (V018).

## 5. Validation rules

Severity: **E** error (file not accepted), **W** warning (accepted, flagged), **I** information.

| ID | Sev | Rule |
|---|---|---|
| V001 | E | File readable, UTF-8 (CSV) or valid workbook; at least one data row |
| V002 | E | All required columns present (header match is case-insensitive; the alias table in config maps known native names) |
| V003 | E | No forbidden column (price, prijs, preis, prix, margin, marge, customer, klant, vin, chassis, …); list in config |
| V004 | E | `period` is `YYYY-MM`, one value per file, equal to the month in the file name or control record |
| V005 | E / W | Invalid part numbers: share above 5% is E, any share above 0 is W; invalid rows are listed with row numbers; accessory or alphanumeric codes go to a sidecar and stay visible (as the Romania adapter does) |
| V006 | E | `quantity` numeric on every row. Zero rows W. Negative without `transaction_type` return/credit/correction W |
| V007 | E | No exact duplicate key (`dealer_id`, `site_id`, `part_number`, `period`, `record_id`) |
| V008 | W / E | `dealer_id` not in the distributor's dealer list: share above 0 W, above 10% E |
| V009 | E from Q3 | A current dealer list exists (updated in the last 12 months) |
| V010 | E | Control record present and complete |
| V011 | I | Timeliness: received within 10 working days after month-end (calendar of working days in config); result `ON_TIME` or `LATE` with days late |
| V012 | W | Total quantity deviates more than 50% from the mean of the previous three accepted months |
| V013 | W | Number of active dealers drops more than 20% against the previous month |
| V014 | I / E | Per-dealer detail present (`dealer_id` is not blank or `ALL`): I until quarter 3, E from quarter 3 |
| V015 | W | `transaction_date` outside `period` |
| V016 | E | `distributor_id` equals the drop folder; UTI and UMI are never merged; IUK and ITUK never merged |
| V017 | W | Mixed encodings, trailing blanks, leading-zero loss in `part_number` (the raw value is kept in `part_number_raw`) |
| V018 | E | Pattern check for hidden price columns: numeric column with currency-like decimals whose name is unknown, flagged for review and held |

Thresholds live in `partner_program.yaml`, not in code.

## 6. File lifecycle and the ledger

States: `RECEIVED → VALIDATED_PASS | VALIDATED_FAIL → ACCEPTED → SUPERSEDED`.

- A new version of the same distributor and period supersedes the previous accepted version. The original stays on disk and in the ledger; downstream results that changed are listed in the receipt.
- A `VALIDATED_FAIL` file never reaches the canonical long format.
- Identical re-imports (same SHA-256) add no activity and do not create a version.
- Annual control rows are never added to monthly rows, and national controls are never added to dealer detail (the loader already refuses; keep it that way).

Ledger columns (parquet): `file_id`, `distributor_code`, `period`, `version`, `sha256`, `received_at`, `state`, `ontime`, `days_late`, `n_rows`, `n_dealers`, `errors`, `warnings`, `accepted_at`, `superseded_by`, `source_path`, `canonical_path`, `note`.

## 7. Receipts

Every file gets a receipt, machine-readable (JSON) and readable (Markdown). The receipt is a **shared** document: it names roles, not people.

Content: file name and version, period, received date, `ON_TIME`/`LATE`, result (`ACCEPTED`, `ACCEPTED WITH WARNINGS`, `NOT ACCEPTED`), counts (rows, dealers, parts), each finding with rule id, plain-language message, row numbers, and **what to correct and how to resubmit**; and a coverage summary (what the declaration says, and what ISZE does not know).

## 8. Reconciliation with billing

Monthly, per distributor: sales-to-dealer quantity valued at ISZE's billed average price per part against ISZE billing for the same months, with **warranty shown apart** as the BI framework requires. Output: three lines (we billed, warranty, sales to dealer) and the stock movement after warranty, never read as lost sales. Tolerance configurable. Use `03_analytics/Isuzu/prism/scripts/build_billed_vs_std_warranty_fy.py` as the pattern **[M]**; parquet only, never raw billing extracts.

## 9. Quarterly eligibility

For each distributor in scope and each fiscal quarter, evaluate the gates and write `eligibility_<FY>Q<n>.csv` plus a Markdown evidence file.

| Gate | Test |
|---|---|
| G1 Sales to dealer on time | All three monthly files of the quarter accepted and `ON_TIME` (a single `LATE` file of up to 5 days is tolerated once per year [P]) |
| G2 Quality | No unresolved error; warning rate within threshold |
| G3 Dealer detail | `dealer_id` populated on at least the configured share of rows (from quarter 3 of the programme) |
| G4 Dealer list | Current within 12 months |
| G5 KPIs | Monthly KPI file received for all three months (the KPI intake is a separate source; this gate reads its status) |
| G6 IDS | If an IDS round was planned for the distributor: at least 70% of its dealers assessed. If none was planned: `NOT_APPLICABLE`, never a failure |
| G7 Training | From April 2027: mandatory trainings completed by the named staff (register read from a CSV maintained by ISZE) |

Result per distributor: `ELIGIBLE`, `NOT_ELIGIBLE` (with the failing gates), `MANUAL_REVIEW`, or `EXEMPT` with a written reason. A manual override file (`overrides.csv`: distributor, quarter, decision, reason, approver, date) is read last and is the only way to change a result. Nothing is posted anywhere.

## 10. Discount proposal (no posting)

For each `ELIGIBLE` distributor, compute the proposed credit for the quarter from billing parquet: discountable base = stock-order (SOR) lines of the quarter, warranty lines excluded **[U: confirm with SAP owners]**, capped at 120% of the trailing four-quarter average **[P]**. Rates and bands come from `partner_program.yaml`. The default design is "hybrid small": flat 0.5% (level 1) and 1.0% (level 2) on the base, plus a progressive bonus on stock-order growth against the same quarter last year: level 1 at 2%, 3%, 5% and level 2 at 4%, 6%, 10% for growth of 0–5%, 5–10% and above 10%, each rate on the stock orders inside its band **[P]**. Output `discount_proposal_<FY>Q<n>.csv` with the arithmetic shown per distributor. A credit note, not an invoice condition, is the recommended route **[P, decision open]**.

## 11. Monthly return

Per distributor, per month, a self-contained HTML page in the format of the existing one-pagers (`Isuzu Universe/02_Atlas/DISTRIBUTOR_ONE_PAGERS_2026-09/`): what ISZE billed and what was sold on, genuine and BVP mix in euros, maintenance-parts coverage, IDS position, and per dealer once detail exists. Own figures beside an anonymous network average. **No ranking** of distributors or dealers. No other distributor is named. Draft only; people send it.

## 12. Monitoring (internal)

One internal page: files due, received, late, invalid; share of distributors with per-dealer detail; quarter-end share of stock orders (31.8% in FY2026 against 25% if even **[M]**) as the forward-buying alarm; order-type shift (stock, rush, VOR) per distributor and quarter.

## 13. Dealer identity

A table `dealer_identity` with history: `dealer_id`, `distributor_code`, `name_in_sales_file`, `name_in_ids`, `sap_customer_no`, `site_id`, `valid_from`, `valid_to`, `status`, `match_method`, `match_score`, `approved_by`. Matching is proposed, never auto-approved. The ITUK 2025 file (64 dealer names) against the IDS list (44 names) is the first test: 16 match exactly, about 34 overlap strongly, about 20 have no plausible match **[M]**.

## 14. Security and privacy

Price-free and free of customer names, chassis numbers and personal data by construction. Dealer names are company names. Files are still commercially sensitive: encrypt in transit and at rest where the storage allows, keep the access list short, log access, never copy files into shared repositories, never commit raw files (`.gitignore` the drop and raw folders), never paste file contents into chat. Each distributor sees only its own files and returns.

## 15. Test strategy

- **Synthetic fixtures only** in the repository: small generated CSV/XLSX per rule (one passing file and one failing file for each rule), plus a three-distributor, twelve-month data set with known totals.
- **Golden receipts:** the exact receipt text for a failing fixture is a test.
- **Property tests:** re-importing the same file twice never changes the ledger; superseding keeps the original.
- **Reconciliation test:** a fixture where billing and sales to dealer are known; the three lines and the stock movement must match to the euro.
- **No real distributor data in tests.** A test that needs real data is skipped unless an environment variable points at the authorised folder.
- Run the existing PRISM suite before and after; it must stay green.

## 16. Build order

1. Schema, rules, validator and receipts (prompt P01).
2. Intake, ledger and versioning (P02).
3. Feed status ledger and register refresh (P03).
4. Reconciliation to billing (P04).
5. Eligibility and discount proposal (P05).
6. Monthly return (P06).
7. Monitoring page (P07).
8. Dealer identity (P08).

Items 1–3 are needed for the January–March 2027 no-discount trial; items 4–6 for the first quarterly check at the end of June 2027.

## 17. Open decisions [U]

| # | Decision | Needed from |
|---|---|---|
| 1 | Credit note or invoice condition | Finance |
| 2 | Is warranty inside stock-order lines, and is it excluded from the base | SAP owners |
| 3 | Meaning of order type PRD (11.6% of FY2026 billing) | SAP owners |
| 4 | Storage for the drop (shared folder, SFTP, other) and who holds the access list | IT |
| 5 | Which distributors already send files and in what shape; update the register | Sales review team |
| 6 | Where the KPI file lands and in what format (gate G5) | Jerome |
| 7 | Training register format and owner (gate G7) | IMG / ISZE |

## 18. Glossary

Sales to dealer: what a distributor sells on to its dealers (part, quantity, no prices). Stock order (SOR): the replenishment order type. Canonical long: the shared table format in `DEALER_SELL_OUT.md`. Receipt: the answer sent for every file. Gate: a yes/no condition for level 1. FY2028: 1 April 2027 – 31 March 2028.
