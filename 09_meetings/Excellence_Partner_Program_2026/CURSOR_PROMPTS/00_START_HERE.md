# Cursor prompts — Partner Intake, Phase 0

**How to use.** Open the ISZE workspace in Cursor. For each task: start a new chat in **Plan mode**, paste the whole prompt file (they are self-contained), let Cursor write its plan, read the plan, then switch to agent mode. Do the prompts **in order** (P01 → P08); each lists what it needs from the one before. After each prompt, run the review prompt `R01_review.md` in a fresh chat before moving on.

**What this builds.** The early, file-based part of the Excellence Partner Program: receive monthly sales-to-dealer files, validate them against a data standard, keep a ledger, reconcile with billing, check eligibility every quarter, and return a monthly one-pager to each distributor. No server, no sign-in, no SAP posting.

**Read once before any prompt (they are short):**
- `09_meetings/Excellence_Partner_Program_2026/TECH_SPEC_Partner_Intake_Phase0_2026-10-09.md` — the specification. It wins over anything below if they disagree; tell Jerome about the conflict.
- `09_meetings/Excellence_Partner_Program_2026/Excellence_Partner_White_Paper_2026-10-09.md` — why the programme exists (chapters 5, 9 and appendix A and E matter most).
- `INDEX.md`, `AGENTS.md`, `00_docs/ROUTING.yaml`, `03_analytics/Isuzu/prism/data/dealer_sales/DEALER_SELL_OUT.md` (the canonical long schema).

## Rules that apply to every prompt

1. **Where code goes:** `04_tools/partner_intake/` (package, CLI, tests, config). Paths via `04_tools/_shared/paths.py`; never hard-code a drive path. New or unsorted data goes to `01_data/90_INBOX/` first.
2. **Reuse:** the canonical long format, `01_data/91_build/normalize_dealer_sellout_*.py` and `03_analytics/Isuzu/prism/modules/dealer_sales_loader.py`. Do not write a second loader or a second calculation of the same number.
3. **Never load raw billing** (`01_data/raw/sales/*.XLSX` or any line-level extract). Use `01_data/00_derived/sales_fact.parquet` and derived CSVs.
4. **No real distributor data in the repository or in tests.** Synthetic fixtures only. Raw drop and raw folders are git-ignored; keep it that way. Never paste file contents into chat.
5. **Never send, ship, deploy, sync or publish.** Mail is draft-only. Do not run `02_dashboards/sync_to_deploys.ps1`. Do not edit `07_deploy/`. Do not edit `.cursor/rules/`. Do not bump versions of existing deliverables.
6. **Numbers:** green `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md`. Fiscal years (FY2028 = 1 Apr 2027 – 31 Mar 2028). Euros, not pieces, in anything a person reads. UTI is never merged with UMI; IUK (UK pickup) is never merged with ITUK (UK truck); Ireland is not IUK.
7. **Language in anything a distributor sees** (receipts, monthly returns): shared language. "Sales to dealer", not "sell-out". No personal names, no internal nicknames, no mention of other distributors by name. Plain business English.
8. **Quality gates:** run the new tests and the existing PRISM suite (`03_analytics/Isuzu/prism/tests`) before and after; both must pass. A passing exit code is not "done": open the output and read it.
9. **Ask, don't guess,** where the spec marks a decision as open [U]. Write the question in the return packet and build the safe default behind a config switch.
10. **Return packet** at the end of every task: files added or changed, commands run with results, what was verified by reading the output, open questions, anything you did not do and why.

## Order and dependencies

| Prompt | Builds | Needs |
|---|---|---|
| P01 | Schema, rules, validator, receipts | — |
| P02 | Intake, ledger, versioning, canonical normalisation | P01 |
| P03 | Feed status ledger and register refresh | P02 |
| P04 | Reconciliation with billing | P02 |
| P05 | Quarterly eligibility and discount proposal | P02, P04 |
| P06 | Monthly return per distributor | P02, P04 |
| P07 | Internal monitoring page | P02, P04 |
| P08 | Dealer identity table | P02 |
| R01 | Independent review of any of the above | the prompt under review |

P01–P03 are needed for the January–March 2027 no-discount trial; P04–P06 for the first quarterly check at the end of June 2027.
