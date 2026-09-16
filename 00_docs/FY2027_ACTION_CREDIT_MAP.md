# FY2027 action credit map

**Purpose:** hang finished ISZE work on a named action in the FY2027 VPACC action plan and close it there, instead of closing it in a chat.
**Prepared:** 2026-09-16 · **Owner:** Jerome · **Status:** mapping document only, nothing in the plan has been changed by this file.
**Reading order:** §1 field guide → §2 mapped deliveries → §4 deliveries with no home → §3 how to close.

**Sources this document is built from**

| What | Path | State at 2026-09-16 |
|---|---|---|
| Action plan pointer (canonical pointers, field meaning) | `ISZE/05_memory/projects/action-plan-fy2027.md` | read |
| Action rows, stream, owner initials, status | `ISZE/01_data/00_derived/vpacc_fy2027_action_plan_july.parquet` | read, 121 rows |
| Workbook behind the derived file (July) | `ISZE/01_data/11_planning/Action plan FY2027 VPACC_July update.xlsx` | on disk, not re-read row by row |
| Workbook, one month later (August) | `ISZE/01_data/11_planning/Action plan FY2027 VPACC_August update.xlsx` | read read-only for status only |
| Delivered work list | `ISZE/00_docs/ISZE_ROADMAP.md` §4 | read |
| Recurring and one-off jobs | `ISZE/00_docs/AUTOMATION_REGISTER.md` | read |

**What I could not verify, stated up front**

- The pointer file names a metadata file `01_data/00_derived/vpacc_fy2027_action_plan_july.meta.json` and a builder `01_data/91_build/build_vpacc_fy2027_action_plan.py`. **Neither exists at that path.** The working copies live under `ISZE/02_dashboards/Data/` (`00_derived/vpacc_fy2027_action_plan_july.meta.json`, `91_build/build_vpacc_fy2027_action_plan.py`). The week-to-week builder therefore sits in a folder that is not the canonical data folder — worth fixing, but not by me here.
- The pointer also names a folder map `01_data/11_planning/README.md`. **That file does not exist.**
- The derived parquet is the **July** update. An **August** workbook is on disk but has not been rebuilt into `01_data/00_derived/`. Everything below that quotes a status is quoted from the derived July file, with the August workbook used only as a cross-check and labelled as such.
- Row numbers are the Excel row numbers in the workbook (`excel_row` in the parquet). I verified they line up between the July derived file and the August workbook for the rows I cite.

---

## 1. The fields you are joining against

The plan is one workbook with **two sheets that matter**, one per stream: `Action Plan VP` and `Action Plan ACC`. Both flatten to the same 121 rows in `vpacc_fy2027_action_plan_july.parquet`.

| Field in the parquet | What it actually is |
|---|---|
| `stream` | **VP** = vehicle parts, 68 rows. **ACC** = accessories, 53 rows. This is the primary split and it matches the sheet the row came from. |
| `fy` | `FY2027` on all 121 rows. The file is an FY2027 plan regardless of the update month. |
| `update_month` | `July` on all rows — it is the label of the workbook edition, not a per-row date. |
| `excel_row` | The row number in the source sheet. This is the stable key for talking about a specific action. |
| `dm_report` | A section or report marker, sparse in the sheet and forward-filled by the builder. Values include a section symbol (`○`) on all 68 VP rows and text headings on ACC: `SALES OBJECTIVES`, `IAS COLLABORATION`, `LOCALISATION  NEW IDEAS`, `SALES SUPPORTING`, `Local`, and single letters `S L T E A I P D` — the letters are the first characters of a step list that was typed one letter per row, so that column is partly a data-entry artefact. Do not use it as a theme. |
| `objective` | **This is the usable theme column.** VP has ten objectives; ACC has 25. | 
| `action_point` | The action itself, one line. This is the text that decides whether a match is defensible. |
| `pic` | **The owner column.** Initials, or a role pair where ownership is shared: `JVDP` (48 rows across both streams), `DW/HT`, `DW`, `Sales / IMG`, `JVDP/KM`, `BS`, `KM`, `SZ`, `IMG`, plus combinations. 15 rows have **no owner at all**. The pointer calls this "initials, e.g. JVDP, KM, DW". |
| `progress_filled` | 0–4, derived from the tick boxes. **NaN on 59 of 121 rows** — no mark in the cell. |
| `progress_status` | The same thing in words. It runs, in order: `not_started_or_blank` (0) → `plan_made` (1) → `started` (2) → `started_and_in_progress` (3) → `completed_and_eval` (4). |
| `deadline` | **ACC only.** VP has no deadline column and all 68 VP rows are empty here. And on ACC the column is not a usable date series: 25 rows read `Apr - Mar`, one group reads `Q3 2022` / `Q4 2022` / `Q4 2021`, and 10 rows contain a comment fragment instead of a date (`Reason`, `Full model change`, `Many DB approached ISZE`, …). Treat "deadline" as a free-text note on ACC rows, not a due date. |

VP objectives and their row counts, because this is where the gaps show:

| VP objective | Rows |
|---|---|
| Genuine parts share | 18 |
| ISZE's own incentive / campaigns | 15 |
| Support DB's to introduce R&M / service contract program | 13 |
| Parts competition | 7 |
| IDS | 6 |
| DB training | 4 |
| KPI | 2 |
| External Sales | 1 |
| **Pricing** | **1** |
| Lubricant business | 1 |

**Read that list again.** There is no VP objective for analytics, dashboards, data quality, catalogue maintenance, automation, or governance. The whole `Pricing` objective is a single row. That is the structural reason your analytical work does not appear in this plan — it is not that you forgot to log it. One row out of 121 is the only VP place where analysis is named.

**And nothing in the plan is currently recorded as closed.** Highest status anywhere is `started_and_in_progress` (3 VP rows). Zero rows sit at `completed_and_eval`, in the July derived file and in the August workbook alike. So "closeable" below is my judgement from the delivered evidence, not a status already written down.

---

## 2. Deliveries that map to a named action

Six. Each one is matched only where the action's own wording supports it; the row number is quoted so you can open the sheet and check.

| # | Work delivered | Where the evidence is | Action it maps to | Closeable now? |
|---|---|---|---|---|
| M1 | **Sales-to-dealer dataset and the analysis on it.** Dealer-level sales for 5 distributors re-emitted; used as the demand view behind capture and replenishment. | `ISZE/01_data/00_derived/sellout_aim_network_mix_2025.csv` · `ISZE/01_data/00_derived/sellout_aim_by_subgroup_2025.csv` · builder `ISZE/01_data/91_build/normalize_dealer_sellout_iuk.py` (+ `_ituk_duncan`, `_petros`, `_portugal`, `_ireland`) · stated as shipped in `ISZE/00_docs/ISZE_ROADMAP.md` §4, 2026-08-25 | **VP row 22** — `Do sales analysis based on DB to DLR sales data` · objective `Pricing` · owner `JVDP` · status `□□□□` not started | **Yes, on the analysis.** The action asks for exactly this analysis and the data now exists for 5 entities. The gap is that the row was never marked. Note the wider limit: 5 of 18 markets have the data, which is roughly half the parts-billed book — say that when you close it, so the closure does not read as network-wide. |
| M2 | **Cover-ratio and spend targets recalculated for every distributor**, then extended into the FY2027 target model with a stretch per distributor. | `ISZE/01_data/02_GPS/HANDOVER_GPS_Extended_Target_FY27.md` · `ISZE/01_data/02_GPS/ISZE_GPS_Extended_Target_FY27.xlsx` · `ISZE/01_data/00_derived/gps_spu_by_distributor.csv` · `ISZE/01_data/00_derived/pms_capture_by_db_year.csv` · August workbook comment on the same row: GPS recalculated for all customers (GPS Extended Target FY27 V3.1) | **VP row 34** — `Set target (incl cover ratio)` · objective `Genuine parts share` · owner `Sales / IMG` · status `■■□□` started | **Partly.** The ISZE side of the action — set the target including the cover ratio — is done and the comment on the row already says so. The next row, **VP row 35** `Agree on target with DB's`, is separate and is **not** done. Do not close 34 and 35 together; that would book the distributor agreement you have not got. |
| M3 | **KPI collection brought to a working state, with the sales-to-dealer view added to the KPI ask.** KPI master file current; requests automated step started. | `ISZE/01_data/11_planning/KPI Master File august 2026.xlsx` · `ISZE/01_data/11_planning/ISZE_DB_KPI_Targets_FY2627_v1.xlsx` · August workbook comment on the same row (KPIs received from most distributors; several August meetings to push; SharePoint auto-receiving about half done) | **VP row 52** — `Collect KPI (matrix)` · objective `KPI` · owner `Sales / IMG` · status `■■■□` in progress | **No.** The row is explicitly still in progress, and the KPI request automation is about half built. This one is a candidate for the monthly update rather than for closure. |
| M4 | **Price position for brake and clutch parts measured against reference dealer prices, and the matching brake proposal put into the distributor's own format.** This is the work behind the brake campaign. | `ISZE/02_dashboards/sales/ISZE_Competitiveness_Dashboard.html` (canonical; chain factor corrected 2026-07-27) · `ISZE/01_data/00_derived/eucon_price_gap.csv` · `ISZE/01_data/00_derived/competitiveness_autodoc_risk.csv` · brake proposal situation and review `ISZE/01_data/90_INBOX/_ituk_brake_spa_20260915/` · August workbook comment on the same row (a tailor-made six-month brake proposal approved) | **VP row 15** — `Brake parts campaign` · objective `ISZE's own incentive / campaigns` · owner `JVDP` · status `□□□□` not started | **No.** The action is a campaign and no campaign has run. What is finished is the price analysis and the proposal, which is the input to the campaign, not the campaign. The closest honest wording when you touch the row is "the proposal is approved; the campaign has not started". Also relevant: parts that carry the highest measured gap are clutch and brake, and the review of the exec aftersales paper recommends leading with those rather than with filters. |
| M5 | **Filter capture and service-interval model built**, including the interval-aware air factor and corrected consumable factors, plus the catalogue key that makes filter part numbers joinable. | `ISZE/01_data/00_derived/pms_capture_by_db_year.csv` · `ISZE/01_data/03_PMS/service_schedules/` · `ISZE/03_analytics/Isuzu/prism/data/pms_capture_assumptions.yaml` · `ISZE/01_data/00_derived/parts_catalog_dimension` key (98.9% coverage, `ISZE/00_docs/ISZE_ROADMAP.md` §4, 2026-07-02) · interval and factor decisions in `ISZE/05_memory/projects/pms-coverage.md` | **VP row 16** — `Filters (oil, air, cabin, fuel) campaign` · objective `ISZE's own incentive / campaigns` · owner `JVDP` · status `□□□□` not started | **No.** Same shape as M4 — the measurement is done, the campaign is not. Worth noting when you close it: the exec paper review puts oil filter at about 1.8% of the measured component gap, so the analysis exists but is not the biggest euro. Do not present this row as the main capture win. |
| M6 | **Distributor audit programme run as a dealer-feedback pack**, one pack per distributor, with the average scoring rule locked for one market. | `ISZE/09_meetings/IDS_2026_DB_Feedback_Sheet_v0.4/` · `ISZE/01_data/08_Distributor/IDS_2026/` · `ISZE/04_tools/ids_dealer_ranking/` · `ISZE/05_memory/projects/ids-db-leverage-os.md` · `ISZE/00_docs/ISZE_ROADMAP.md` §4, 2026-08-11 (IDS 2026 v1.4 packs, scoring rule locked) | **VP rows 67–72** — objective `IDS`: `Create audit schedule` (row 67, owner `IMG`, `■■■□`) · `Join DLR visits with IMG & IML` (68) · `Review of submitted IDS` (69) · `Award` (70) · `Planning of DLR improvement activities` (71) · `Review improvement activities` (72) — all owner `Sales / IMG` | **No, and only row 67 is closeable in part.** Row 67 says the schedule is agreed, which your comment already records. The other five are the audit cycle itself and it is live — the August workbook notes the schedule was moved and that visited distributors must verify their improvement activity by end November. Closing 68–72 now would claim an audit cycle that has not finished. |

### Two things to keep straight when you use this table

**VP and ACC are separate streams, and only one of them has deadlines.** Everything above is VP. If you close an ACC action, the row also asks for the `deadline` cell, which as §1 shows is not a real date on that sheet.

**The plan is not dealer-keyed.** The pointer is explicit: joins happen on theme, owner initials and stream, never on a dealer code. So M1 and M2 are joined to the plan by the *theme* they serve (sales analysis, cover-ratio targets), not because a distributor appears in a row.

---

## 3. How to close an action

Four steps. The order matters because the workbook is versioned and the derived file is rebuilt from it.

**Step 1 — put the mark and the evidence line in the next monthly workbook.**
File: the next edition of `ISZE/01_data/11_planning/Action plan FY2027 VPACC_<month> update.xlsx`.
Cells: on `Action Plan VP` the progress mark is column **R** and the comment column is **S** ("Comments"); the owner is column **E**. On `Action Plan ACC` the progress mark is column **S**, the report column is the one headed for that month, and the owner is column **F**.
What goes in the comment: one line, the deliverable, and the **absolute path** to its evidence. One line per action, matching the style already used in the workbook — the existing entries are terse and dated.
Do it through the helper that produced the August edition, `ISZE/01_data/91_build/_fill_vpacc_action_plan_august.py`, rather than by hand. That script carries two rules you would otherwise break: it never writes into a cell that already contains someone else's text, and it never touches a row whose owner initials contain `BS`. Hand-editing bypasses both. Copy the script and change the source and output file names for the new month; do not edit the August copy in place.
Never write a status you cannot point to. If the evidence is a chat conclusion, it is not evidence.

**Step 2 — log the closure outside the plan.**
`ISZE/DECISIONS.md` — new line at the top, dated, with the reason and the evidence path. Append-only, newest first.
`ISZE/CHANGELOG.md` — one line under `## [Unreleased]`.
These two are the record that survives the workbook. The plan alone is a spreadsheet that gets emailed around; the decision log is the thing a later session reads.

**Step 3 — update the shipped list.**
`ISZE/00_docs/ISZE_ROADMAP.md` §4, one dated line. Same date and wording as the decision log entry so the three cannot drift.

**Step 4 — rebuild the derived file so the analytical surfaces agree.**
Run the builder that turns the workbook into `ISZE/01_data/00_derived/vpacc_fy2027_action_plan_july.parquet` so PRISM page 24 (`ISZE/03_analytics/Isuzu/prism/pages/24_VPACC.py`) and the plan status both read the new mark. **The builder is not at the path the pointer claims** — it is at `ISZE/02_dashboards/Data/91_build/build_vpacc_fy2027_action_plan.py`. Confirm which copy you are running before you run it, and note that its output file name contains `july`, so a later edition either needs the name changed or a second derived file. Decide that once, not per month.

**Who confirms.** Confirmation sits with the owner recorded in the row's owner column, and for the `JVDP` rows that is you. Where the owner is a role pair (`Sales / IMG`, `IMG`, `DW/HT`) the row is jointly owned and the other named party confirms — a closure you write alone on a jointly owned row is a claim, not a closure.

**Gap worth naming:** there is no approval step recorded anywhere in the workspace for closing a plan action — no sign-off file, no meeting minute path, no counter. I am not inventing one. Until one exists, the confirmation above is by role and is not evidenced, and that is a weakness of the routine rather than of this document.

---

## 4. Deliveries with no action to hang on

These are the ones that stay invisible. Each is listed with the evidence path and the reason it could not be mapped honestly.

| # | Delivery | Evidence path | Why no match |
|---|---|---|---|
| N1 | **Price revision pack** — 6,326 part numbers, built and unsigned since 2026-08-19 | `ISZE/01_data/00_derived/book_b_bucket_summary.csv` · `ISZE/01_data/91_build/build_revision_book_b_pack.py` · decision framing in `ISZE/00_docs/ISZE_ROADMAP.md` §2 | **No action exists.** The whole `Pricing` objective is one row (row 22, general sales analysis). A price adjustment is also a decision, not an action — it sits in §2 as an open decision, where only you can close it. |
| N2 | **Account-health signals and the early-warning call list** — built, thresholds still draft | `ISZE/01_data/17_interactions/account_health.meta.json` · `ISZE/04_tools/interactions/P4_CALIBRATION_RUNBOOK.md` · `ISZE/00_docs/P4_DETERMINISTIC_SIGNALS.md` | **No action exists.** No VP or ACC objective covers dealer health signals. The blocking decision is calibration, which again is a §2 item. |
| N3 | **Action ledger** — nine sources consolidated into opportunity rows, with its own ops page | `ISZE/01_data/00_derived/action_ledger.parquet` · `ISZE/02_dashboards/ops/ISZE_Action_Ledger.html` · builder `ISZE/01_data/91_build/build_action_ledger.py` · register entry in `ISZE/00_docs/AUTOMATION_REGISTER.md` | **No action exists.** Entered the register as a recurring pipeline, which is a job record, not a plan action. |
| N4 | **Monthly refresh pipeline and its verification spine** — 116 checks, 0 fail, billing through 2026-06-30 | `ISZE/03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1` · `ISZE/01_data/00_derived/_verification_report.json` · `ISZE/04_tools/workspace/isze_monthly_refresh.ps1` · `ISZE/00_docs/RUNBOOK_MONTHLY_REFRESH.md` | **No action exists.** No objective covers the data spine. This is the most load-bearing thing in the list and the plan has no row for it. |
| N5 | **The analytical surface itself** — the internal set of analysis pages over the derived data | `ISZE/03_analytics/Isuzu/prism/run_prism.ps1` · page list in `ISZE/00_docs/ISZE_ROADMAP.md` §3 | **No action exists.** The one ACC tooling row (`Tool`, Power BI for accessory procurement) is a different tool for a different stream, so matching it would be a stretch. |
| N6 | **Tender pipeline and the national portal coverage analysis** — live feed, 14 portals reporting | `ISZE/01_data/14_dashboards/tender_data.json` · `ISZE/04_tools/ISZE_Tender_Monitor_Install/` · coverage analysis `ISZE/00_docs/roadmaps/scrapers.md` | **No action exists.** Named as an open queue item in `ISZE_ROADMAP.md` §1 item 4, not as a plan action. |
| N7 | **Competitive-price scraper fleet and its health automation** — five price sources refreshed weekly, with an allowlist for automatic fixes | `ISZE/04_tools/autodoc_scraper/` · `ISZE/04_tools/scraper_health_report.md` · policy in `ISZE/DECISIONS.md` 2026-07-24 | **No action exists.** The related action rows are campaign rows; a scraper is the input to a price comparison, not the campaign. |
| N8 | **The register of recurring jobs plus the weekly drift audit** — five live Windows tasks, twelve scheduled skills, one audit that reports drift and never closes it | `ISZE/00_docs/AUTOMATION_REGISTER.md` · `ISZE/04_tools/workspace/isze_live_state_audit.ps1` · `ISZE/05_memory/briefs/automation_drift_*.md` | **No action exists.** This is infrastructure. It is also the subject of the companion handover runbook. |
| N9 | **Warranty expense by distributor and year** | `ISZE/01_data/00_derived/warranty_by_db_year.csv` · `ISZE/01_data/00_derived/distributor_warranty_expense_fiscal.csv` · builder `ISZE/01_data/91_build/build_warranty_canonical.py` | **Theme only, too vague to close.** The R&M rows (54–66) are about signing distributors to service contracts and incentives. Warranty claim expense is not the same subject, so mapping it would misstate the action. |
| N10 | **Dated price-list history and the part numbers with no usable list price** | `ISZE/01_data/01_Pricing/history/` · `ISZE/02_dashboards/pricing/pricing_history_findings.json` · builder `ISZE/01_data/91_build/build_pricing_history_findings.py` · `ISZE/00_docs/ISZE_ROADMAP.md` §4, 2026-08-11 | **Theme only.** Row 22 is general sales analysis; a no-list-price measurement is a pricing-governance gap, and the plan has no governance row. |
| N11 | **Catalogue key and supersession work** — part number key at 98.9% coverage; catalogue list-price coverage raised to 98.2% | `ISZE/01_data/00_derived/parts_catalog_dimension` · `ISZE/01_data/91_build/build_supersession_delta.py` · `ISZE/00_docs/ISZE_ROADMAP.md` §4, 2026-07-02 and 2026-08-11 | **Theme only.** Feeds the cover-ratio row indirectly, but the action text for row 34 is about targets, not about the catalogue. |
| N12 | **List-to-pocket validation and the leakage measurement** | `ISZE/01_data/00_derived/list_to_pocket_validation_2023_2025.csv` · builder `ISZE/01_data/91_build/build_list_to_pocket_validation.py` · `ISZE/00_docs/ISZE_ROADMAP.md` §1 item 2 | **No action exists**, and the euro figures are held internal until a written sign-off — another decision, not an action. |
| N13 | **GPS reconciliation** — one entry point that reconciles the two billing bases and fails when the payer map is incomplete | `ISZE/04_tools/gps_reconcile.py` · `ISZE/01_data/00_derived/gps_reconciliation_report.json` · lessons in `ISZE/05_memory/projects/gps-reconciliation.md` | **No action exists.** Pure integrity infrastructure. |
| N14 | **Vehicle population data handling** — the current register is canonical, and the rebuild specification for the forecast columns is drafted | `ISZE/06_uio/_CURRENT/` · `ISZE/06_uio/_CURRENT/V20_SPEC.md` · `ISZE/05_memory/projects/uio.md` | **No action exists.** Feeds many rows; is itself nobody's plan row. |
| N15 | **Parts classification** — the classification layer brought to the point where the residual unclassified share is small | `ISZE/03_analytics/Isuzu/prism/modules/aim_pn_classifier.py` · `ISZE/03_analytics/Isuzu/prism/docs/aim_classification_gap_report.md` · `ISZE/05_memory/projects/aftermarket-intelligence.md` | **Theme only.** A data-quality layer under the cover-ratio and campaign rows, but no row names classification. |
| N16 | **Interaction layer** — company text turned into a structured record of interactions, commitments and stakeholders, running locally | `ISZE/03_analytics/Isuzu/prism/` interaction tables · `ISZE/00_docs/ISZE_ROADMAP.md` §4, 2026-08-12 · scope note `ISZE/00_docs/G0A_LOCAL_MAIL_SCOPE.md` | **No action exists.** The closest ACC rows are about improving market intelligence from distributors, which is a different activity from a local text pipeline. |
| N17 | **The exec aftersales paper and its critical review** | `ISZE/02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` · `ISZE/00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` · brief `ISZE/00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md` | **No action exists.** This is the clearest example of the problem: a full paper with a scored review, and no plan row to attach it to. The review's own conclusion is that it produced no signed outcome. |
| N18 | **Monthly sales and order tracking for vehicle parts** | `ISZE/01_data/04_sales/(VP) Monthly report 2026-06.pdf` · `ISZE/01_data/00_derived/q1fy2027_billing_tagged.csv` · `ISZE/05_memory/projects/monthly-sales-report-fy2027.md` | **No matching action.** The nearest ACC rows (6 and 7) set accessory sales and target objectives — a different product line. Matching them would book accessory targets against vehicle parts reporting. |
| N19 | **Decision memo for the price adjustment ambition** | `ISZE/01_data/01_Pricing/DECISION_MEMO_PRICE_ADJUSTMENT_20260916.md` | **No action exists.** A memo that asks for a signature is a decision instrument; the plan has no row for it and probably should not have one. |

**Net position: 6 deliveries map to a named action, 19 do not.** Of the 19: **fourteen have no action in the plan at all**, **four have only a theme too vague to close without misstating the action**, and **one** (N18) has a nearby action that belongs to a different product line, so matching it would book accessory targets against vehicle-parts reporting. The pattern is not random — it is that the plan is a commercial action list, and the analytical and integrity layer underneath it is invisible to it by construction.

---

## 5. What to do with this

The shortest useful move is to close the one row where the case is clean and uncontested: **VP row 22**, the sales analysis on distributor-to-dealer data. It is a `JVDP` row, the action text asks for it by name, and the evidence is a dated entry in the shipped list. Closing it also forces Step 4 above, which is where the pointer-to-builder path problem gets fixed.

The second move is a decision, not a closure, and only you can make it: for each of the fourteen deliveries in §4 with no action at all, either add a row to the plan in the next monthly edition, or accept in writing that it stays outside the plan. Both answers are legitimate. Leaving it unanswered is what keeps it landing in chat.

---

*Footnote — two on-disk file names quoted above contain words the workspace language rules forbid in prose. They are the literal names of files and are not rewritten here: the `sellout_*` derived files in M1, and the price-revision builder in N1.*
