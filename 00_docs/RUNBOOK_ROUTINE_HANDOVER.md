# Runbook — handing over the recurring jobs

**Purpose:** the recurring jobs currently run because one person runs them. This document says what each one produces, which ones break completely if that person is away, and what a second person needs in order to take one over.
**Prepared:** 2026-09-16 · **Owner today:** Jerome · **Status:** proposal and procedure. Nothing here has been delegated, and no job, task or XML file was changed to write it.

**Sources**

| What | Path |
|---|---|
| Job register (cadence, tier, inputs, outputs, path checks) | `ISZE/00_docs/AUTOMATION_REGISTER.md` |
| The monthly refresh procedure | `ISZE/00_docs/RUNBOOK_MONTHLY_REFRESH.md` |
| Monthly refresh, as one command with fail-closed gates | `ISZE/04_tools/workspace/isze_monthly_refresh.ps1` |
| Paper review that states the same problem in commercial language | `ISZE/00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` |
| Job definitions for the scheduled skills | `C:\Users\jerom\Documents\Claude\Scheduled\<job-name>\SKILL.md` |
| Prior handover material that already exists | `ISZE/04_tools/ISZE_Tender_Monitor_Install/01_OPERATOR_RUNBOOK.md` · `ISZE/01_data/02_GPS/HANDOVER_GPS_Extended_Target_FY27.md` · `ISZE/00_docs/HUMAN_ONBOARDING.md` |
| Working from a second machine | `ISZE/00_docs/HOLIDAY_LAPTOP.md` |

**What I could not verify, stated up front**

- Register says last audited 2026-08-25; live Windows task state read 2026-09-16. The two agree on which tasks exist and I found no drift.
- The register's sheet says no job stores a copy of its own report. That matches the skill definitions, and it is the reason §5 below describes recovery from log files rather than from job output.
- I did not run any job, any scraper, or any task. Everything below is read from the job definitions and from files already on disk.

---

## 1. The jobs, and what each one actually produces

**Windows scheduled tasks** — these run without anyone present. Live state read 2026-09-16, all five registered and all showing last result 0.

| Job | Runs | What it produces, in one line | Output path |
|---|---|---|---|
| `ISZE Tender Monitor` | Mon 07:30 | Refreshes the tender feed: opportunities and notices from the EU, UK, Israel, Norway and Finland, scored for relevance, and republishes it | `ISZE/01_data/14_dashboards/tender_data.json` |
| `ISZE_PMS_IAM_Refresh` | Mon 07:00 | Refreshes competitive part prices from five aftermarket sources, then checks for unexpected movement | `ISZE/04_tools/autodoc_scraper/ks_results.csv` and the sibling source files |
| `ISZE_LiveStateAudit_Weekly` | Mon 08:00 | Compares this register against what actually exists and writes the mismatches as a numbered waiting-on-Jerome list | `ISZE/05_memory/briefs/automation_drift_*.md` |
| `ISZE_CursorWeekDigest_Weekly` | Sun 20:00 | Summarises the week's local editor sessions so the weekly review can see work done here | `ISZE/05_memory/briefs/cursor_week_*.md` |
| `ISZE_DiscountScanner_Weekly` | Thu 07:00 | Personal promotional-price scan. Not part of any commercial quote or figure | `ISZE/04_tools/` scraper output |

**Scheduled skills** — these are instruction files an agent executes on a cadence. They are not Windows tasks, so nothing fires them if the scheduler side is not running.

| Job | Cadence | What it produces, in one line | Output path |
|---|---|---|---|
| `isze-weekly-tender-scrape` | Weekly | Runs the tender scraper and republishes the feed to the live monitor and the analysis pages. **This is the instruction file behind the `ISZE Tender Monitor` task above** — same output, two records of it | `ISZE/01_data/14_dashboards/tender_data.json` |
| `isze-weekly-open-loops` | Monday | One merged digest replacing four separate reports, listing what still needs a decision | `ISZE/05_memory/briefs/open_loops_YYYY-MM-DD.md` |
| `isze-memory-review` | Weekly | Checks project memory against the verified figures; fixes stale dates and statuses, suggests the rest | `ISZE/05_memory/briefs/memory_review_W<week>_<year>.txt` |
| `isze-scraper-healthcheck-autofix` | Sun 22:00 | Diagnoses staleness in the scraper fleet; fixes only an allowlisted set of price scrapers, proposes everything else | `ISZE/04_tools/scraper_health_report.md`, `proposed_patch.diff`, `manual_review_required.md` |
| `isze-dashboard-freshness-check` | Monday | Age report over the dashboards and their data feeds, with a staleness band per file | Report only, printed not stored |
| `isze-weekly-intelligence-brief` | Weekly | External market intelligence summary | `ISZE/05_memory/briefs/latest_weekly_brief.txt` |
| `isze-uio-staleness-alert` | 1st of month | Age check on the vehicle population file, and a search for a newer copy that should be promoted | Report only, printed not stored |
| `isze-pricing-basket-monitor` | 1st of month | Checks the price list for a new edition and reports movement against confirmed figures | Report only, printed not stored |
| `isze-aim-classification-refresh` | Monthly | Checks the parts classification layer for drift | Report only, printed not stored |
| `isze-mailbox-intake` | 1st of month | **Not built.** The register records it as a stub with no implementation | — |
| `zondag-checkin-traject` | Sunday | Personal, outside ISZE | personal |
| `feedback` | Ad hoc | Agent usage notes, outside ISZE | — |

The register also lists two job folders that were deleted on 2026-07-24 (an empty duplicate intelligence brief and a tender refresh superseded by the scrape above) and two jobs recorded as retired or superseded (the old competitive-price scrape, replaced by the refresh task; and the Autodoc refresh, permanently blocked at source). They are not live work.

**One bookkeeping point that matters for a handover.** The tender job appears twice in the records — once as a Windows task and once as an instruction file — because the task runs a batch file and the instruction file describes the same run. That is one job producing one output, not two. Anyone taking it over should change both records together or neither.

**The monthly refresh** is the big one and it is **manual, not scheduled**. It is a runbook plus a partly automated orchestrator.

| Piece | What it produces | Path |
|---|---|---|
| Ingestion of the new billing export | `sales_fact` rebuilt from the raw monthly files | `ISZE/01_data/00_derived/sales_fact.parquet` |
| Full analytical rebuild and verification | All derived files, plus the check report that decides whether anything may be quoted | `ISZE/01_data/00_derived/` and `ISZE/01_data/00_derived/_verification_report.json` |
| GPS reconciliation | One report reconciling the two billing bases and the payer mapping | `ISZE/01_data/00_derived/gps_reconciliation_report.json` |
| Dashboard feed | The JSON the published pages read | `ISZE/01_data/14_dashboards/isze_data.json` |
| Orchestrator run record | Which stages ran and whether the run finished green or stopped | `ISZE/01_data/00_derived/_monthly_refresh_run.json` |

Current state of the last full run, read today: verify green at **116 pass / 0 warn / 0 fail**, generated 2026-08-25, billing through **2026-06-30**. The orchestrator's own run record is older — last green **2026-07-26**.

---

## 2. Where the single-person dependency actually sits

Split into two kinds, because they fail differently.

### 2a. Hard stop — nothing runs at all if Jerome is away

| Job | What breaks | Why |
|---|---|---|
| **The monthly refresh** | Nothing happens. No new billing enters the spine, verify is not re-run, the dashboard feed does not move, and every figure in every page ages. | The orchestrator does the rebuild and verify, but it deliberately refuses to do the front end. Its own closing message lists five things still manual: move the SAP export into the raw sales folder and update the manifest, refresh the accessory workbooks if a meeting needs them, update the headline figures file together with its anchor, publish, and rebuild the small external slice. All five are Jerome. |
| **`ISZE_PMS_IAM_Refresh`** (the competitive-price refresh) | Competitive prices go stale silently. Nothing downstream looks wrong; the price comparison just quietly gets older. | The task runs, but its history includes a run that died part way (last result 0xC000013A, interrupted) and was only recovered by a manual refresh. Nothing in the chain escalates a stale price file. The register's own open-item list and the scraper job both treat this as something Jerome watches. |
| **Key registration for the Nordic sources** | Two national tender feeds go quiet. | Closed as an ask in `DECISIONS.md` 2026-08-25, but the key material is held by one person. |
| **Anything requiring a decision** | The whole downstream stops. | Roadmap §2 lists thirteen items that wait on an answer, not on work. A second operator can run jobs and cannot clear these. |

### 2b. Degraded — it still runs, but the validation stops

This is the more dangerous category, because the output keeps appearing and looks normal.

| Job | What degrades | Why |
|---|---|---|
| **The drift audit** | It still writes its report. The report is never acted on. | By design it reports drift and never closes it — the register says so explicitly. With nobody reading it, drift accumulates silently and the register and reality separate. |
| **The scraper health job** | It keeps diagnosing and keeps applying its allowlisted fixes. Nobody sees the proposed patches or the manual-review file. | Its allowed output includes a proposed patch file and a manual-review file, both of which are addressed to a human. |
| **`isze-weekly-open-loops`** | It keeps writing the Monday digest. The digest is unread. | The digest is explicitly a list of things needing a decision, capped at ten open loops and five questions. |
| **`isze-memory-review`** | It keeps applying its high-confidence fixes to project memory. Nobody reviews what it changed. | It may edit project memory files directly and appends to an applied log. The log is the only record of what changed and it is only read by a person. |
| **The freshness and staleness reports** | They print and disappear. | The register says these are report-only, and the job definitions confirm no file is written. If nobody is in the session, the report is lost. |
| **`ISZE_DiscountScanner_Weekly`** | Runs, unread. | Low impact, listed for completeness. |

### 2c. The honest summary

Of the recurring work, **one job is a hard stop that silently costs data freshness** (the monthly refresh), **one hard stop that silently costs price freshness** (the competitive refresh), and **six that keep producing output nobody consumes**. The second group is worse than the first, because a stopped job is visible and a job whose output is ignored is not.

This is the same finding the exec paper review reaches from the commercial side: a strong body of diagnostics with no signed outcomes. Here it is a strong body of automations with no reader.

---

## 3. What a second person needs to take one over

Written for the one candidate in §4, but the same five blocks apply to any of them.

**Step 1 — the procedure, in order**

For a monthly billing refresh:

1. Set the workspace root environment variable, or accept the default path. Everything else resolves from it.
2. Look in the staging folder `ISZE/01_data/_INBOX/`. Any file sitting there is an un-ingested delivery. The orchestrator prints a note about this but does not act on it.
3. Move the new billing file from staging into `ISZE/01_data/12_raw/sales/`, keeping the existing naming pattern. Update the last-refreshed row in `ISZE/01_data/DATA_MANIFEST.md`.
4. Run the orchestrator: `ISZE/04_tools/workspace/isze_monthly_refresh.ps1`.
5. Read `ISZE/01_data/00_derived/_monthly_refresh_run.json` to see the run outcome, then read `ISZE/01_data/00_derived/_verification_report.md`.
6. If the run stopped, fix the cause and re-run. **Do not update the headline figures file while a gate is red.**
7. Only for intentional changes, update `ISZE/FACTS.md` and `ISZE/03_analytics/Isuzu/prism/data/facts_anchor.yaml` **together**.
8. Publish from the source folder `ISZE/02_dashboards/`. Never edit `ISZE/07_deploy/` by hand.

Use `-DryRun` first on a machine you have not run it on: it evaluates the gates against the existing reports and builds nothing.

**Step 2 — access and credentials**

| Need | Detail |
|---|---|
| Machine access | A clone of the ISZE repository at the same root, or the same machine. The repository is `github.com/jeromio1987/ISZE`. |
| What is **not** in the clone | Raw billing and sales spreadsheets, the living planning workbooks, secret files, and the published mirror. There is no way to run this job without the raw billing files, so a handover on a different machine is not a real handover until those are arranged. |
| Python | On the path. The orchestrator checks for it and stops if it is missing. |
| Environment variable | The workspace root. Optional, but it must be set consistently or paths resolve differently between jobs. |
| Secret material | None for the monthly refresh. The Nordic tender keys are separate and belong to the tender job, not this one. |

**Step 3 — the check that must pass first**

Every job in the register starts with a **path preflight**, and the policy is abort, not repair:

1. Confirm every required input path exists.
2. Confirm the output parent folder exists.
3. On any miss, print an abort line naming the missing path and **stop** — without creating folders, without running scrapers, without fixing code.

The orchestrator applies the same idea to the data itself: a gate it cannot prove green is treated as red, and a report that was not written during the current run counts as not proven. There is a separate read-only checker for the scheduled paths, `ISZE/04_tools/workspace/verify_scheduled_paths.ps1`, and the register records that a folder reorganisation in June 2026 broke several jobs' paths. Run the preflight and mean it.

**Step 4 — where the output lands**

| Stage | Landed file |
|---|---|
| Rebuilt billing spine | `ISZE/01_data/00_derived/sales_fact.parquet` |
| All derived files | `ISZE/01_data/00_derived/` |
| Verification verdict | `ISZE/01_data/00_derived/_verification_report.json` and `.md` |
| GPS reconciliation verdict | `ISZE/01_data/00_derived/gps_reconciliation_report.json` |
| Dashboard feed | `ISZE/01_data/14_dashboards/isze_data.json` |
| Run outcome | `ISZE/01_data/00_derived/_monthly_refresh_run.json` |

**Step 5 — how failure shows up, and it is not a red screen**

| Symptom | What it means | What to check |
|---|---|---|
| The orchestrator prints a stop block and a red reason, exit code 1 | A gate failed. Expected failure, nothing downstream ran. | The reason line names the gate. Read the verification report. |
| No run record, or a run record whose timestamp did not move | The job never started. | Python on the path; the scripts the preflight checks. |
| Run record says green but the dashboard feed has an old timestamp | The feed was skipped or a step silently did not move. | The orchestrator itself fails on a feed that does not move, so treat a green record with a stale feed as evidence something outside the orchestrator touched the file. |
| **Verify still green, figures still old** | The most likely real failure. The pipeline ran, the gates passed, and the new billing was never ingested because it is still sitting in the staging folder. | Days since the billing cut-off in the verification report versus today. Current state at 2026-09-16 is **2026-06-30** — check that before trusting any figure. |
| A stale report | Treated as not proven, not as a pass. | The report's own timestamp against the run start. |

**One structural trap worth knowing.** The register's audit table says the live competitive-price task is the real refresh and warns that a spare task definition file on disk is a duplicate that would double-run if imported. If your second person ever imports task definitions, that warning matters. Editing a task definition file on disk does **not** change the running task; the task has to be re-registered.

---

## 4. The first one to hand over

**Recommended: the monthly billing refresh, run as a supervised pairing for two cycles.**

### Why this one and not another

**It fails worst if nobody runs it.** Competitive prices going stale is bad. The billing spine going stale is worse: every figure in every page, every capture percentage, and the whole verification chain is downstream of it. At 2026-09-16 the spine ends at 2026-06-30. That is the exposure.

**It is already built to fail closed.** The orchestrator stops on the first gate it cannot prove. That is exactly the property you want in a first handover, because it means an inexperienced operator cannot quietly produce wrong numbers — the failure mode is a stopped run with a named reason, not a plausible-looking bad figure. Most of the other jobs have the opposite property: they produce output whether or not the run was sound.

**The hard part is small and specific.** Steps 3 and 7 are the human ones — move the file, and update the headline figures only for intentional changes. Those are checkable. Step 4 is one command. This is a much smaller surface to hand over than, say, the competitive refresh, whose history already shows a run that died part way.

**It has a written procedure already.** `ISZE/00_docs/RUNBOOK_MONTHLY_REFRESH.md` plus the orchestrator's own closing instructions. What is missing is not the procedure; it is a second person and a rehearsal.

**It is not commercially sensitive.** Nothing here talks to a distributor, sends mail, or changes a price. Handing it over carries no external risk, so it is a safe first delegation that builds the habit before you hand over anything that faces outward.

**Why not the competitive refresh instead:** no existing graded procedure at the same level, and its failure is silent. **Why not the freshness or staleness reports:** they are cheap to hand over and they prove nothing, because they change no data. Start where the handover actually removes a single point of failure.

### The first test, concretely

**What the second person runs.** The orchestrator in dry-run mode first, then a real run.

```
powershell -File "C:\Users\jerom\Desktop\claude\ISZE\04_tools\workspace\isze_monthly_refresh.ps1" -DryRun
```

Then, once the dry run reports its preconditions and gates cleanly, the real run without the flag. Run it on the same machine the first time, with Jerome present but not touching the keyboard.

**What the second person produces for the test.** A one-page note with the run record path, the outcome value, the verification counts, the billing cut-off date from the verification report, and the timestamp on the dashboard feed.

**How Jerome verifies the result independently, without re-running anything.** Four checks, all read-only, none of which accept the operator's own summary as evidence:

1. **Read the run record directly.** `ISZE/01_data/00_derived/_monthly_refresh_run.json` — confirm the outcome field and the stage list. A stage list with a skipped or missing stage is not a green run.
2. **Read the verification report's own summary.** `ISZE/01_data/00_derived/_verification_report.json` — the fail count must be zero and the generation timestamp must fall inside the run window. A verdict written before the run started is not proof of this run.
3. **Check the billing cut-off moved.** The billing date inside the verification output is the single number that proves the new data actually entered. If it did not move, the run may be green and the point of the job is unmet.
4. **Check the feed timestamp.** `ISZE/01_data/14_dashboards/isze_data.json` modification time must be inside the run window.

If all four pass, the handover worked for that cycle. Two clean cycles in a row, then the second person runs it alone and Jerome checks the same four items afterwards. If a cycle fails, that is useful — the second person should be able to point at the named gate without asking.

**One thing to decide before the test.** The orchestrator's rebuild writes into `ISZE/01_data/00_derived/`, which is the spine every published figure reads from. There is no separate practice space, and the rollback policy in the runbook still carries a `[TODO]` for the backup location. Either settle a backup location first, or accept that the rehearsal runs against a repository clone rather than the live spine.

---

## 5. What must not be delegated

Five items. Each with the reason on one line.

| Not delegated | Reason |
|---|---|
| **Anything that goes to a distributor** | The relationship is Jerome's, and a message sent in his name by someone else is not the same message even when the words are identical. |
| **Anything that sends mail** | Draft-only is a rule in this workspace and there is no drafted-then-reviewed path for a second person to use; the risk is a send that cannot be recalled. |
| **Anything that changes a price** | A price move is a signed decision by a named person, and the price revision pack has been sitting unsigned since 2026-08-19 precisely because that signature has not been given. |
| **Headline figure changes** | Updating `ISZE/FACTS.md` and its anchor file is what makes a number quotable outside the workspace. It is the point at which an error stops being internal. |
| **Publishing to the published mirror** | The mirror is outward-facing. Syncing from the source folder is a one-way action that cannot be walked back once a page has been read. |

Everything else in §1 is a candidate for handover. The line is not "technical versus commercial" — it is **anything that reaches another party, or that an error can no longer be contained within the workspace.**

---

## 6. What would make this real

Three things are missing, and none of them is analysis.

1. **A named second person.** Every job in §1 is currently owned in the register by the same name. Until a second name appears against at least one job, the ceiling stands.
2. **A backup location for the spine.** The runbook's rollback table still reads `[TODO]`. Without it, a bad run has no defined way back, which is exactly why a second operator is currently hard to justify.
3. **A reader for the reports that are already produced.** Six jobs in §2b write to a human who is not there. Handing over a job is the second problem; nobody reading the output is the first one.

---

*Companion document: `ISZE/00_docs/FY2027_ACTION_CREDIT_MAP.md` covers the other half of the same problem — work that has no named action to be credited to.*
