# ISZE — programme roadmap (hub)

**Last updated:** 2026-09-19 · **Domain detail:** [`roadmaps/`](roadmaps/) · **Registry:** [`MAP_REGISTRY.yaml`](MAP_REGISTRY.yaml)

> **Numbers rule:** green [`01_data/00_derived/_verification_report.json`](../01_data/00_derived/_verification_report.json) → `metrics_snapshot.json` → [`FACTS.md`](../FACTS.md). That order wins over any deck, memory file, or GPT answer.
> **Pipeline state 2026-08-25:** verify **116 pass / 0 warn / 0 fail** · `sales_fact` billed through **2026-06-30** · SaTy coverage min 92% (Q1 hole documented).

**How to read this file**

| Section | Use it for |
|---|---|
| [1. Open queue](#1-open-queue) | What is actually being built next — the only list that is work |
| [2. Waiting on Jerome](#2-waiting-on-jerome) | Decisions, not effort. Nothing here moves without an answer |
| [3. Live now](#3-live-now) | What already runs, and where it lives |
| [4. Shipped](#4-shipped) | Dated ledger of what closed — one line each, rationale lives in `DECISIONS.md` |
| [5. Closed — do not reopen](#5-closed--do-not-reopen) | Dead ends. Re-proposing one of these costs credibility |
| [6. Domain roadmaps](#6-domain-roadmaps) | Depth per domain |

Rationale, evidence and numbers for every closed item live in [`DECISIONS.md`](../DECISIONS.md) (append-only, newest first) and [`CHANGELOG.md`](../CHANGELOG.md). This hub stays short on purpose — it is a queue, not an archive.

---

## 1. Open queue

Ordered. `Blocked on` names the single thing that unblocks the item — if it says *nothing*, it is buildable today.

| # | Item | State | Blocked on | Detail |
|---|------|-------|------------|--------|
| 1 | **P4 account-health calibration** (task 4.9) | Builder live `p4-v1`; draft thresholds fire on 10 RED / 6 AMBER of 17 DBs — not yet a call list | **Jerome** — amber/red thresholds (B5) | [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) |
| 2 | **List-to-pocket sign-off** | Validation ran 2026-08-19 (`list_to_pocket_validation_2023_2025.csv`); leakage € stays **internal** until year-matched PR00/ZPR1→net joins are signed in writing | **Jerome** — written sign-off | `DECISIONS.md` 2026-08-25 |
| 3 | **P5 forecast go-live (G1)** | P5.2 + P5.6 built — 548 series, median WAPE 49.4%, `pages/19_Forecast.py` live as a surface | **Jerome** — sign G1 on 98.2% catalogue (B6/D6) + override policy (B7/D4) | [`P5_FORECAST_BUILD_PLAN.md`](P5_FORECAST_BUILD_PLAN.md) |
| 4 | **National tender portal coverage** | **ES PLACSP LIVE 2026-09-14** (Atom OK, 2 keyword / 0 gated this window). IT PNCP + DE OV already LIVE 2026-08-25. National LIVE **17/29**. | nothing — next DARK without a human key (HU/IE/SE/SK; EE RHR still HTTP 500) | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) · `_ES_PLACSP_LIVE_20260914.md` |
| 5 | **Interval-aware air vs oil capture** (integrity flag C) | Shipped 2026-07-02 on a **provisional 0.5 air factor** | IML ratio confirmation | [`roadmaps/gps.md`](roadmaps/gps.md) · PRISM `pms_capture_assumptions.yaml` |
| 6 | **ITUK brake wear factor — 0.4 or 0.8** | 0.4 in force and now actually applied (fix 2026-07-21). Do not quote ITUK brake capture as locked | ITUK data (expected since 2026-08-11) | `DECISIONS.md` 2026-07-21 |
| 7 | **LCV generation-aware interval split** | Schedules on disk: RG21 RZ4F-TC **with SCR** = 15k km, without / older = 20k | chassis + registration-year cutoffs — PDFs alone do not map UIO years to SCR vs non-SCR | `01_data/03_PMS/service_schedules/` |
| 8 | **Fig-key V2 remainder** | IE40 parquet fill **158** empty `fig_key` on existing PR00 rows (2026-09-14). Catalog `fig_key` **161,325 / 164,969** (97.8%). Overrides file header-only — EPC basket JSON is edition/family, Snap-on blocks bulk BVP. Part Explorer already wired. | nothing remaining on this slice | [`roadmaps/gps.md`](roadmaps/gps.md) |
| 9 | **Residual PR00 gaps** | FY2026 leftover: **21 parts / €67,318.49** billed with no list (almost all UTI; two UMI; one Kazakhstan). Calendar-2025 €67,182.04 / 24 parts is **do not quote**. Shell `5500*` parked. No %GM. Pieces are not the KPI. Supersession 925 PN / €2.48M: EPC **`BLOCKED_NO_EPC_EXPORT`** | EPC export in `90_INBOX` | [`ISZE_BI_FRAMEWORK.md`](ISZE_BI_FRAMEWORK.md) L3 · [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §6 · `NO_PR00_HARDWARE_FY2026.md` |
| 10 | **P2b / P3 / P6 (LLM on mail text)** | Specced, zero code. P2a runs local and deterministic | **B1b** approved LLM route named, then **G0b** (DPIA, LIA, works council) | [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §4 |
| 11 | **Supabase live Master KPIs** (HTML V4) | Not started | schema + credentials | [`roadmaps/html.md`](roadmaps/html.md) |
| 12 | **Dashboard filename renames** | Blocked by design — build scripts hardcode `vN` | rename plan in [`CANONICAL.md`](CANONICAL.md) | [`roadmaps/html.md`](roadmaps/html.md) |
| 13 | **Scraper quality V2** | **Done 2026-09-14** — `relevance_score_1to5` + export “Relevance Score” (pass ≥3, **no drop**); `scrape_error` on KS/Mekonomen + category crawlers; RSS entity sanitize + recover; UK Find a Tender honors Retry-After / records LAST_FETCH_ERRORS; Lidl `a10051271` is 404, live URL is search `aanbieding` | nothing | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) |
| 14 | **Workspace cleanup decisions** | **Both halves already decided in writing** — see below, not waiting on Jerome | — nothing — | [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md) · [`UI_STACK.md`](UI_STACK.md) |
| 15 | **AIM attribute layer** (size / position / duty on leaves) | **On hold (roadmap)** — Jerome 2026-09-17; do not build; not “proceed” | deferred / later — not this week | `DECISIONS.md` 2026-09-17 · audit `CLASSIFICATION_FULL_AUDIT_20260917.md` §8 item 10 · paper §08–§09 |
| 16 | **Pricing programme** — the measured weighted increase, the industrial-engine discount rate, the 3% vs 5.96% reconciliation, the override rows, competitor-evidence funding, class assignment | Live 2026-09-19. The weighted increase of all prices is **+5.9616%** whole book, **+6.2081% Japan**, **+6.3088% Thailand**; per market PR00 +5.92%, UTI +5.58%, UMI +5.64%, CIS +4.85% — all inside 4–6% | **Jerome** — items 2.2–2.8 | [`roadmaps/pricing.md`](roadmaps/pricing.md) |

**Not on this list on purpose:** anything in §5. Also: no new 0–100 score on any surface, and no Dash / Evidence work — Streamlit :8503 is the product. The AIM **two-axes** lock (identity + commercial score beside it) stays live; only the **attribute layer** is deferred.

**Item 14 came off the waiting list on 2026-09-16, on written evidence only.** Both halves were already decided on paper: external share is HTML / GitHub Pages (`UI_STACK.md`, decided 2026-06-13) and the ISZE_Dashboard ops sandbox is closed indefinitely with no merge timeline (`ISZE_Cleanup_Plan.md` Phase 3, closed 2026-07-26). No cleanup work remains in this item. Reconciled in [`DECISION_RECONCILE_20260916.md`](DECISION_RECONCILE_20260916.md).

---

## 2. Waiting on Jerome

One answer each. Build effort is already sunk or trivial; these are the actual bottleneck. Source: [`AFTERMARKET_BI_BUILD_MENU_20260819.md`](AFTERMARKET_BI_BUILD_MENU_20260819.md) Tier B + the AI-sales gates.

**How this list gets shorter:** [`DECISION_DISCIPLINE.md`](DECISION_DISCIPLINE.md) — a weekly 45-minute slot, one list only, and every item ends as decided / killed / delegated. A decision only counts once it is in this file, in [`DECISIONS.md`](../DECISIONS.md), and as `status: decided` in the build file that was waiting. Items reconciled against written evidence: [`DECISION_RECONCILE_20260916.md`](DECISION_RECONCILE_20260916.md).
**One sitting (2026-09-14):** recommended ticks are in [`DECISION_PACK_20260914.md`](DECISION_PACK_20260914.md). Until a row is ticked, do not apply it in code. Same-pass engineering (Monday seed, tenders, fig-key/EPC, scraper quality) does not wait.

| Ref | Decision | Consequence of no answer |
|-----|----------|--------------------------|
| B1 | the price adjustment ambition — +4% / +5% / launch-only. **CLOSED 2026-09-22 — do not re-ask** (see the note under this table) | Nothing. The question is closed and its last output (the +5% flat simulation) is on disk |
| B2 | **Seed €** for 9,591 no-L12M PNs — IML BOM vs UTI placeholders | Those PNs stay out of every € ranking |
| B3 | **Growth-factor sign-off** — keep 1.24 / 1.25 / ×1.25 UTI table? | Forecast and alloc inherit an unsigned assumption |
| B4 | **Guardrail policy** — auto-HOLD on IAM-undercut + proxy-adverse? | Every exception is manual |
| B5 | **P4 calibration** — amber/red thresholds | Queue item 1 blocked |
| B6 / D6 | **G1** — sign 98.2% catalogue coverage, or wait for P1.4 / P1.5? | Queue item 3 blocked |
| B7 / D4 | **P5 override policy** — who may delta a forecast, audit trail | Forecast cannot go live even after G1 |
| B8 | **Book A +3% alloc** | Explicit rebuild only — no default |
| B9 | **ITUK brake wear factor** 0.4 vs 0.8 | Queue item 6 blocked |
| B10 | **Competitor vintage labels (shared)** | shared keeps mixed-vintage files unlabelled in the UI |
| B1b | **Approved LLM route** for company text (Cowork or other) | P2b / P3 / P6 die; P1 + P2a + P4 + P5 still run |
| B11 | **ITUK mileage** — draft mail to Duncan Young asks for the average annual mileage of the N-series parc (N35/N75 split if wanted). Measured UK is 16,688 km/yr all classes, 35,478 for N75, against a 50,000 assumption. **Draft only, not sent** — Jerome sends | UK capture stays presented on a 3× and 1.4× overstated demand base |
| B1c | Shared `Sales` / `Parts` mailboxes — works-council step | Mail corpus stays halved |
| B4-gov | DPO for ISZE, or via IML legal | P0 governance is 2 weeks or 8 |

**Never put back on a waiting list:** Nordics tender API keys. They are **DONE** (verify ALL OK, Doffin + HILMA healthy) — `DECISIONS.md` 2026-08-25.

**B1 — the price adjustment ambition — is CLOSED, permanently, 2026-09-22.** Jerome, verbatim: *"delete price ambition I will come when it's done for now do a simulation on 5% increase and than never ask again."* The +5% flat simulation was produced the same day and is its last output. **No agent asks this question again in any form** - not +4% vs +5%, not a band, not "open on launch families only". He comes back to it himself when it is done. Full record: [`PRICE_AMBITION_CLOSED_2026-09-22.md`](PRICE_AMBITION_CLOSED_2026-09-22.md). The wording in `DECISION_RECONCILE_20260916.md` B1 and B8, and the "blocked on ambition" lines in the Book B files, is stale as a *question*; nothing was rebuilt and no file was rewritten. This closes the **ambition** question only - the other pricing items (section 1 item 16, `roadmaps/pricing.md` section 2.2 to 2.8) are untouched.

### Answered 2026-09-19 — six items decided, three still open

Six items were answered in conversation on 2026-09-19 and are recorded in full in [`DECISIONS.md`](../DECISIONS.md) under the same date: **D01, D02, D03, D08, D13 and D15**. **D03 and D15 were answered differently from the wording they previously carried** — D03 moves from the multiplier chain to the **margins reading**, D15 moves from leaving the configuration at a 20% margin to fixing it to the **40% margin** the price file charges — and in both cases the earlier wording is retained in [`DECISIONS.md`](../DECISIONS.md) and marked as superseded. **D05 was asked about and left open, with no decision recorded**, and in a later pass the same day he directed that these questions stop without answering it, so it stays open and unanswered. In that later pass **D25 and D26 were decided** and **D24 received a factual correction** from him — parc evidence for Portugal exists — which answers the evidence half and does **not** authorise the ceiling rebuild, so **D24 stays open**.

Register: `01_data/90_INBOX/DECISIONS_AWAITING_JEROME_2026-09-19.json` (and its generated `.md` twin). **The register was reopened by a concurrent check at about 20:55 on 2026-09-19, and that reopening was a false negative.** The check selected rows by string-matching `decision_source == "Jerome, chat, 2026-09-19"` and inferred from that vague wording that the closures rested on a conversational remark; it never read the session. Each of the six was in fact put to Jerome as a **structured multiple-choice question card** and he **selected an option**, which a transcript-only check cannot see because session transcript rows carry only assistant text and tool_use blocks — no `tool_result` and no selection field. The citations on the six now name the card and the selected option, and **all three places agreed again at that point**: the register then read **20 open · 0 blocking · 3 high · 17 normal · 6 decided**. **That count is superseded by the late pass of the same day (next paragraph): 18 open · 0 blocking · 2 high · 16 normal · 8 decided.** [`00_docs/DECISION_DISCIPLINE.md`](DECISION_DISCIPLINE.md) is the rule that says all three must agree before an item closes. **D05 is the one item from this set that genuinely was not answered** — he asked what it was about — and it stays open.

**Late pass, same day — four further directions, and a standing instruction on pricing.** **Pricing does not move through this register.** Jerome, verbatim: *"dont change anything from pricing via these questions"*. No pricing value, band, threshold, label or price file is changed on the strength of an answer to a register question; pricing changes are his to start directly. The instruction governs every pricing entry here, not only D25, and is recorded at register level so it cannot be read as an answer to one item. The register now reads **18 open · 0 blocking · 2 high · 16 normal · 8 decided**, with its `counts` block recomputed from the actual status fields. The two high items are D24 and D05.

| Ref | Decision | What it unblocks |
|---|---|---|
| **D01** | **Decided — urgency high.** Yes to both halves. The two action labels in the revision exception builder are to be **swapped**, so "room to raise" means the parts where we are genuinely cheaper than the independent market; and the raise / no-raise band widens to **0.80 / 1.10** with **brakes** named as the first category to examine. The label swap **supersedes the earlier wording**, which had recorded it as not authorised. **Not executed** | Regenerating the exception queue and its downstream pack (Monday stand-up, GPS tab, action ledger, review workbook). **Authorised but not run** — the regeneration is a separate piece of work |
| **D02** | **Decided — urgency high.** Yes. Widen the raise and no-raise band to **0.80 / 1.10**, leaving the middle inconclusive on this evidence. Recorded as its own decision, not as a rider on D01. Pairs with D01 and lands with the same rebuild. **Not run** | The same exception-queue rebuild as D01. The separate question of a label for the 0.60–0.95 rows is **D25** and stays open |
| **D03** | **Decided — blocking closed.** The **margins reading**: a **37% margin** at one step and **25–27.5%** at the next, a combined price multiple of about **2.15–2.19**. The multiplier chain (1.40 to the distributor, then 1.275 to the dealer) is **not adopted**. He was told the consequence before answering — the reference dealer price rises **22.6%**, about **€12.4M** on the CY2025 billed base, none of it ISZE revenue, and both the paper and the analysis recommend the chain instead — and confirmed the margins reading anyway. **This supersedes the chain wording previously recorded here.** Recorded as a deliberate, informed decision; not re-opened. **Not executed** — no shared pack has been rebuilt. **Consequence, stated once:** every pack that names a tier is rewritten to the margins reading, and any figure measured against the reference dealer price moves by the same 22.6% |
| **D08** | **Decided — urgency high.** Yes. Rebuild the five live dashboards, the AIM truck catalogue and the Business Performance Review deck from their builders, so the fleet reads **163,198** and the **€198 per truck** slide becomes a matched rate (**€188.16** for the 18-market billed total over the 163,459 fleet, **€188.46** for the same euro over the 163,198 target-spend fleet). **Caveat he was given, and the limit on his yes:** the engine no longer reproduces the published ceiling — re-running it yields **€54,323,455** against the published **€55,253,312** — so the rebuild re-bases the ceiling and every rate dividing by it. His yes approves the **rebuild**, not the re-based ceiling; the new ceiling value may need its own look. **Executed 2026-09-22**, including the ceiling rebuild Jerome separately authorised that evening: ceiling **€54,375,729**, cover **56.6%**, uncaptured **€23,950,221**. The €54,323,455 quoted in this row was already stale when written (it needs Portugal at 0.6899, replaced 2026-09-20 by 0.6364). Backup and write-up: `01_data\91_build\_backsafe_20260922_ceiling\MANIFEST.md` |
| **D13** | **Decided — urgency high. Executed, in two named parts.** (1) A bare **`.bak`** ignore rule added to `.gitignore` (line 205). Checked before adding: **exactly four** untracked files ended in a bare `.bak` and the rule closes all four; the three files ending `.bak` that are tracked **on purpose** are untouched, because an ignore rule does not untrack an already-tracked file. (2) The **nine files under `JEROME_ONLY/`** untracked with `git rm --cached`; all nine verified still on disk at their original sizes, the existing `**/JEROME_ONLY/` rule keeps them out of future commits, and `git check-ignore` and `git status` confirm it. **Nothing was committed and nothing was pushed** — the removals and the `.gitignore` line sit staged in the working tree. The other drafted ignore rules on the sheet were **not** applied |
| **D15** | **Decided — blocking closed. Executed.** **Fix the configuration to the 40% margin** the price file actually charges: `class_factor.T` in `03_analytics/isze_pricing/config.yaml` changed from `0.80` to `0.60`, and **nothing else in that file was touched**. **This supersedes the wording previously recorded here**, which kept the configuration at a 20% margin and treated the mismatch as deferred. The instruction to leave the **live price list** alone still stands — the value is a configuration input, not a price. **Consequence, stated once:** any margin-based figure touching those roughly one hundred class-T part numbers now assumes **40%** rather than 20%, and figures produced before the change assumed the lower margin |
| **D24** | **Closed 2026-09-22 — rebuild authorised and executed.** Evidence half answered 2026-09-19; the rebuild was authorised the evening of 2026-09-22 and run. Ceiling **€54,375,729** on CY2025 (−€877,583 from €55,253,312), cover **56.6%**, uncaptured **€23,950,221** on the per-market floored definition. Six markets moved — Portugal, Ireland, Germany, Belgium, Malta and Cyprus — and every one of them was **stale, not wrong** (the file was faithful to the code of 2026-09-17, when only ITUK had the vehicle-class split). Parts billed unchanged at **€30,756,772**. Original entry text: That corrects our own record — `uio_ld_n35_share.csv` carries Portugal on a JP **shipment** mix and states no parc-band source exists, and both statements are wrong. **Located:** `01_data/07_UIO/Matriculas Isuzu SAP.xlsx`, the I-Motors Portuguese registration register (per-VIN sheets `2005-2019` and `2019-2026` with explicit tonnage bands, plus a `SUM` sheet by band and year; registrations 2005 to June 2026; on disk since 14 July 2026). The split is settled by the second file, `01_data/08_Distributor/Imotors_Portugal_UIO_GPS_PMS_Study.xlsx` (on disk since 14 July 2026), which convolves that history against the survival curve copied from UIO V19 `Assumptions & Mapping` rows 16-33 — the curve already in use. On the **2025 basis the Portuguese N-series parc is N35 1,521.31 and N75/N50/N62 869.00 vehicles in service, so the light share is 1,521.31 / 2,390.31 = 0.6364 (63.6% light)**; 2024 gives 0.6386. **It does not give 0.690**, which is a JP shipment mix, not a parc share: at 0.6364 the parc-derived share sits **5.4 points below** it, so adopting it would reduce the €674,246 Portuguese ceiling movement rather than leave it as it stands. What it does not settle is whether the rebuilt fleet base (CV LD 2,390 in 2025 against V19's 2,206) replaces the current one — that is D09's question, not this item's. **His sentence does not authorise the rebuild:** the corrected shares are not accepted, the Portuguese share is not replaced, no ceiling is re-based, no coverage figure is recomputed and no builder was run. **Item stays open** because the register's vocabulary is `open` or `decided` with no third value and nothing here is a decision either way | The whole ceiling rebuild chain — the ceiling, coverage %, uncaptured value, the flat-€250-per-vehicle placeholder share, metrics snapshot, console tiles, hub, BPR deck, map snapshot and exec paper. The rebuild authority sits with D08, which is approved but **not run**, and D08 does not authorise a re-based ceiling. What closes this is one line from him: accept a named Portuguese light/heavy share, or hold |
| **D25** | **Decided — no change, and pricing is out of this register.** No pricing value, band, threshold, label or price file is changed through these questions. The rows where the peer shop is up to 20% cheaper than us are **not** given a new label; the bands stay as they are and the **0.80** threshold recorded under D02 stands as the last pricing change this register captured. D01 and D02 remain recorded as decided — the instruction governs execution, not those records — so whether the label swap and the band widening are applied, and when, is now his direct call. The brake finding on the entry is a finding and is unaffected | Nothing, on the pricing side. The guardrail action list keeps the labels it already has. The brake exposure — 38 rows below 0.80 worth **€722,257**, five part numbers around €696,000 — remains a finding for the brake review and needs no pricing change to stand |
| **D26** | **Decided — the retirement stands. The gate update is OUTSTANDING and was not made.** The Aftermarket BI Command Center stays retired and is **not** restored from `HEAD` (b88b9e8); the suite-map stub is the page by design. Accepting the retirement means the tier-A ship gate must stop expecting the retired page: the command-center entry in `02_dashboards/_build/verify_tier_a_html_json.py` (lines 34-43) still demands a hero string and at least 20 server-rendered bar-rows, neither of which a 12 KB stub can carry, so the gate still fails for the whole tier-A set. It is not a one-line string fix — the entry has to be dropped or replaced outright. **No verifier and no ship-gate script was modified while recording this**; that change needs a deliberate pass of its own | The tier-A ship gate for the whole tier-A set. Also still open: whether the hero-tile repair in `02_dashboards/_build/aftermarket_bi_data.py` is kept as dead code or removed |

The register's three high items were D24, D25 and D26. After the late pass **D25 and D26 are decided**, and **D24 stays open** — his correction answers the evidence question, not the rebuild. **D05 also stays open and unanswered**, with the question flow directed to stop. **Nothing is blocking**: the register's two former blocking items, D03 and D15, are both answered above. One honest limit on stopping the questions: the register's own hook reads this file at the end of the first agent turn and selects strictly on `status == "open"`, so an open item will keep surfacing until the question flow itself is dealt with as a separate piece of work. That hook was not changed.

**One matter is not yet a decision and is recorded so it is not lost:** eight files under `09_meetings/Preparation Meetings/IML_ITUK_PMS/outlook_extracts/` are tracked in `HEAD` — five markdown files, a probe script and two small JSON captures. **Three of the five markdown files are the ones named in the stopped-push finding:** `DEEP_ANALYSIS_WrapUp_Target_Attrition_N75.md`, `Duncan_WrapUp_thread_verbatim_2026-04.md` and `Masumi_Suzuki_Hadi_IMG_IMIT_digest_2026-07-26.md`. The other two markdown files — the `Duncan_PMS_thread_digest` and `Rene_GIDSS_intervals` digests — are the same kind of file with the same exposure. All five sit **outside** the `JEROME_ONLY` marker, and each is **byte-identical** to its `mp/JEROME_ONLY/outlook_extracts/` copy that the D13 action untracked, so identical content is now ignored in one folder and still tracked in the other. The `**/outlook_extracts/**` rule covers the whole tree, but an ignore rule does not untrack a file already in `HEAD`, so any of them would be silently re-added by a bulk commit. He has not decided on them, so nothing was done.

Recording a decision is not executing the build it authorises: the revision-queue regeneration (D01, D02), the fleet-figure rebuild (D08) and the shared-layer tier wording (D03) are all authorised and **none has been run**. One value in `03_analytics/isze_pricing/config.yaml` and one line in `.gitignore` were the only file changes made, plus the nine index removals.

---

## 3. Live now

### PRISM — Streamlit, port 8503 (canonical analytical surface)

Run: `03_analytics/Isuzu/prism/run_prism.ps1` (Mode-A safe) · `run_prism_internal.ps1` (internal shelf: leakage, attach, elasticity, scrape).

| Page | Capability | Primary data |
|------|-----------|--------------|
| `0_Early_Warning.py` | This-cycle call list | `early_warning.csv`, `defection_alerts.csv` |
| `1_UIO.py` | Parc | UIO v19 (DVLA-based), `06_uio/_CURRENT/` |
| `2_GPS.py` | GPS spend per unit | `gps_spu_by_distributor.csv` |
| `3_PMS.py` | PMS capture (registry + BVP catalogue) | `pms_capture_by_db_year.csv` |
| `4_BVP.py` | BVP mix | `mix_genuine_bvp_pms.csv` |
| `9_Review_Pack.py` | Review pack export | derived |
| `10_Data_Integrity.py` | Integrity audit | `mislabelled_sku_audit.csv` |
| `14_Tender_Pipeline.py` | Tender pipeline | `01_data/14_dashboards/tender_data.json` |
| `18_Decision_Models.py` | Waterfall, runway, defection, attach | `wallet_waterfall.csv` et al. |
| `19_Forecast.py` | P5 forecast surface (**pre-G1**) | `forecast_final_2026_08.csv` + `forecast_final.parquet` (gitignored) |
| `20_Warranty.py` | Warranty expense per DB / FY | `distributor_warranty_expense_fiscal.csv` |
| `21_Realization.py` | List→pocket + ZPR1 gap (**internal**) | `pr00_realization_*_cy.csv`, `zpr1_vs_pr00_by_payer_year.csv` |
| `22_Parc_Cohort.py` | JP cohort (not UIO v19) | `07_UIO/vin/VIN_register.csv` |
| `23_Dealer_Sellout.py` | Multi-DB sell-out mix + SPU | `sellout_aim_network_mix_2025.csv` |
| `24_VPACC.py` | FY2027 VPACC action plan (121 items) | `vpacc_fy2027_action_plan_july.parquet` |
| `network_intelligence.py` · `ituk.py` · `internal_shelf.py` · `tools_marketing_calendar.py` | IA phases 3–8 result (2026-08-20) | see `prism/docs/DASHBOARD_IA.md` §8 |

The AIM × GPS quadrant is now a tab inside `network_intelligence.py` (merged 2026-08-20; source archived to `pages/_archive/16_AIM_GPS_Matrix.py`), on `aim_gps_matrix.csv` with **GPS × PMS total capture** axes. The pricing-risk axis is gone (§5). Everything under `pages/_archive/` is retired — do not link it as live.

### Derived spine + ledger

| Surface | Where |
|---|---|
| Quantitative spine | `01_data/00_derived/` (alias `01_data/derived/` is an NTFS junction — prefer numbered paths) |
| **P8 Action Ledger** | `action_ledger*.parquet/csv` + `02_dashboards/ops/ISZE_Action_Ledger.html` — 23,236 opportunities, €22.1M **mixed-basis source cells, not one wallet** |
| Pipeline verify | `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1` |
| PMS assumptions (editable) | `prism/data/pms_capture_assumptions.yaml` |

### HTML (shared unless flagged)

`02_dashboards/` is the single source of truth; `07_deploy/` is generated. Build → `_build/ship_gate_check.ps1` → `sync_to_deploys.ps1`.

| Pack | File |
|---|---|
| Master hub | `hub/MASTER_DASHBOARD.html` |
| Aftermarket BI Command Center | `sales/ISZE_Aftermarket_BI_Command_Center.html` |
| DB→DLR replenishment | `sales/ISZE_DB_DLR_Replenishment_CY2025.html` |
| Pricing full analysis pack | `pricing/ISZE_Pricing_Full_Analysis_Pack.html` (integrity weak — internal QA) |
| Pricing history findings | `pricing/ISZE_Pricing_History_Findings_Dashboard.html` (**provisional**) |
| Static PRISM twins | `bi/` (4 self-contained snapshots) |
| OS data map | `ops/ISZE_OS_Data_Map.html` |
| IDS 2026 packs | `ids/` (v1.4 — Baumann MIDI average rule locked) |

Full inventory: [`roadmaps/html.md`](roadmaps/html.md).

### Automation

Live scheduled tasks and their SSOT: [`AUTOMATION_REGISTER.md`](AUTOMATION_REGISTER.md). Tender Monitor (Mon 07:30) and `ISZE_PMS_IAM_Refresh` (Mon 07:00) are the two ISZE-core jobs — do **not** import the spare refresh XML (double-run).

---

## 4. Shipped

Newest first. One line each; the reasoning is in `DECISIONS.md` under the same date.

| Date | Shipped |
|------|---------|
| 2026-10-06 | **Automation register matches live Task Scheduler** — eight ISZE tasks checked against the register (state, script, last run); PriceLedger now points at the windowless launcher; last-run stamps carry the real run date instead of the check date; the Monday failures of 28 Sep and 5 Oct are recorded (PR #34, #35, #36 and #38, merge `01e7cc6` for the first three) |
| 2026-10-06 | **PriceLedger weekly repaired** — `ISZE_PriceLedger_Weekly` had failed at step 3 of 6 with exit `3221225786` (`0xC000013A`) since 2026-09-28, because the task ran only when the user was logged on, so a terminal window opened and closing it killed the step; it now starts the windowless `04_tools/delegation/run_price_ledger_hidden.pyw` through `pythonw.exe`, step 3 of `04_tools/price_ledger/build_scraped_observations.py` logs progress every 100 pages and the ks page parse in `04_tools/delegation/parsers/site_ks.py` is faster with identical output on all 938 saved pages, and the step 4 input `02_dashboards/Data/01_Pricing/_raw/eucon_crossref_iam_20260329.csv` was restored from `91156f6`. First full pass 2026-10-06, `LastTaskResult = 0`, log ends `EXIT 0 - all six steps completed.` (PR #30, merge `379f08d`) |
| 2026-08-25 | **P8 Action Ledger** — nine adapters → `action_ledger*.parquet/csv` + ops HTML; `BILLING_HORIZON` now reads `max(sales_fact.billing_date)` |
| 2026-08-25 | Overnight process audit — verify green 116/0/0, junctions restored, Nordics keys closed as an ask |
| 2026-08-25 | `sales_fact` extended with `Q1FY2027.XLSX` (Apr–Jun 2026); dealer sell-out CSVs re-emitted for 5 DBs |
| 2026-08-20 | **PRISM IA phases 3–8** — Network Intelligence merged (7 tabs), Mix absorbed DB-mix-split, ITUK hub, Tools re-cut, sources archived. 71 tests green |
| 2026-08-19 | **Aftermarket BI Tier A** — 14 of 15 builds done: P5.2 + P5.6 forecast, replenishment dashboard, Book B review, GREECE as 5th DB, supersession delta, list-to-pocket validation, account-health ops pack, portfolio triage, PMS BVP regain, pricing history pack |
| 2026-08-18 | PRISM `INTERNAL_MODE` launcher split (MD-safe default) + duplicate tabs dropped by cross-link |
| 2026-08-18 | `capture_trajectory` partial-year guard — 33 declining alerts → 5, zero real declines hidden |
| 2026-08-18 | P4 account-health builder `p4-v1` (draft flags, gitignored parquet — **not** a KPI) |
| 2026-08-12 | P2a interaction layer complete — 3 tables, 24-month run (9,490 interactions, 926 commitments, 203 stakeholders), local + deterministic under G0a |
| 2026-08-11 | **Dated price-list history** PR00 + ZPR1 2023/2024/2025 + current 2026 under `01_data/01_Pricing/history/` |
| 2026-08-11 | CY2026 AIM dashboard on billing only — dual CY + FY windows in `aim_billing_windows.json` |
| 2026-08-11 | Spec C4 SAP pull closed 220 PN / €4.36M of the no-PR00 gap — catalogue PR00 coverage **98.2%** (was €4.96M / 15.1% at 2026-08-01) |
| 2026-08-11 | IDS 2026 v1.4 packs — Baumann MIDI average rule applied |
| 2026-07-26 | Tender Monitor + competitive-pricing refresh confirmed live as scheduled tasks |
| 2026-07-21 | `country_overrides.factors` fixed on the bucketed PMS path — ITUK brake capture 58.3% → 72.8% at the configured 0.4 |
| 2026-07-16 | Front/rear brake split dropped from `wear_factor` — network capture CY2025 23.8% → 32.0% (phantom tripled denominator removed) |
| 2026-07-03 | FY2025 completeness (Jan–Mar 2026 wired) · CR/RE credit-note exclusion (flag H) · 2025 UIO V19 in capture |
| 2026-07-02 | SAP fig key on `sales_fact` via `parts_catalog_dimension` join (98.9% coverage) |

---

## 5. Closed — do not reopen

No new data, no new proposal. Each of these was tested and failed, or was answered by Jerome.

| Closed | Date | Why |
|--------|------|-----|
| **Gross / SPA / condition columns on the billing extract** | 2026-08-11 | Not available. `sales_fact` is **net-only forever**. Discount vs SPA vs mix cannot be decomposed from billing — design around net + dated lists. **Do not re-ask.** |
| **AIM pricing-risk as a decision surface** | 2026-07-17 · 2026-08-18 | 0.12 gate never fired; fitted replacements failed the 2024→2025 holdout; persistence ρ = 0.92 GPS / 0.75 PMS. No new 0–100 on any surface |
| `db_aftersales_risk` as the replacement | 2026-08-18 | Same genus — hand-weighted 0–100 on a mislabelled 44-PN file. Parked, not promoted |
| Fitted oil-filter service frequency | 2026-08-18 | Null. All-DB OLS wins MAE only by absorbing under-capture into λ. Flat bucketed constants stay |
| `price_volume_elasticity.csv` (ISZE→DB) | 2026-08-11 | Deferred — DB→DLR only. Resume when dealer sell-out coverage grows |
| Brake front/rear split categories | 2026-07-16 | Front/rear is not a unit of commercial action; the only market with real data replaces both in one job |
| **Nordics tender API keys** | 2026-08-25 | DONE — verify ALL OK, Doffin + HILMA healthy, NO/FI merged. Never put on a waiting-on-Jerome list again |
| Autodoc / Oscaro scraping | 2026-07-14 | Cloudflare Turnstile blocks 100% of requests. Frozen CSV kept |
| Auto365 as a PN price index | — | No OEM part-number join |
| Telematics / VIN usage as the next ask | — | Data we do not have |
| External "healthy capture %" (J.D. Power / NADA / DataMac) as an ISZE target | — | Three different metrics; none of them is ours |

---

## 6. Domain roadmaps

| Domain | File | Status |
|--------|------|--------|
| AIM + PRISM after scoring failed | [`roadmaps/aim_prism_reinvention.md`](roadmaps/aim_prism_reinvention.md) | **Active** — the programme after the score kill: P4, PN prices, Streamlit surface |
| AI sales intelligence (mail → action, account health, forecast) | [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) | **Active** — Track A running; Track B stops at B1b/G0b |
| Aftermarket BI execution menu | [`AFTERMARKET_BI_BUILD_MENU_20260819.md`](AFTERMARKET_BI_BUILD_MENU_20260819.md) | **Active** — Tier A 14/15 done; Tier B is §2 above |
| GPS / fig-key | [`roadmaps/gps.md`](roadmaps/gps.md) | V2 enrichment in PRISM; V3 scoring **superseded** |
| HTML dashboards | [`roadmaps/html.md`](roadmaps/html.md) | V3 overlay shipped; V4 Supabase blocked on credentials |
| Scrapers / tenders | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) | Both core tasks live; national portal coverage is the open P0 |
| Jarvis / isze-tools | [`roadmaps/tools.md`](roadmaps/tools.md) | V2 data-out-of-code done; V2.2 onward unstarted |
| Specs feeding the queue | [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) · [`P5_FORECAST_BUILD_PLAN.md`](P5_FORECAST_BUILD_PLAN.md) · [`PROMPT_ACTION_LEDGER_P8.md`](PROMPT_ACTION_LEDGER_P8.md) | Build specs, not status |

---

## 7. Integrity and hygiene

- **Do not quote externally until closed:** `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md` — live priorities are interval-aware PMS (flag C, queue item 5) and returns confirmation (flag H, judgment call not ERP-confirmed).
- **internal only:** leakage / list-to-pocket euros, pricing history findings, action-ledger stakes. shared needs the §2 sign-off.
- **Language:** shared never uses internal nicknames or personal names — see `AGENTS.md` § External IML / meeting language.
- **Workspace cleanup:** open items in [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md).
