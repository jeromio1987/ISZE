# Next deepen briefs (SPAR lock · 2026-09-07)

**Role:** Map of three deepen-only lanes inside existing homes. Not a build.  
**Lane pick:** map-first · **H4** · **P4** · **H2/H3**. **H1 Pricing skipped.**  
**Gate:** no HTML / pipeline mutation until a later message says `rebuild` or `ship` and names **one** lane.

Live map: [`BI_FULL_AUDIT_AND_STRUCTURE_2026-09-06.md`](BI_FULL_AUDIT_AND_STRUCTURE_2026-09-06.md) · ops: [`ISZE_BI_OPTIMIZATION_FRAMEWORK.md`](ISZE_BI_OPTIMIZATION_FRAMEWORK.md) · open list: [`STATE_PACKET.md`](STATE_PACKET.md)  
V2 status: [`GPS_PMS_V2_SPEC.md`](GPS_PMS_V2_SPEC.md)  
Aug hub (stale “Build now”): [`../ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) — do not treat as the queue.

**Do not treat as next builds:** PRISM IA · INTERNAL_MODE · fig-key on sales_fact · list-to-pocket A8 · Book B review HTML · Action Ledger v1 · AIM score · fitted oil-filter λ · Monday Command · H1 deepen.

**Human-blocked (do not chase in BUILD):** Duncan dealer × PN × month · ROMANIA LCV vs mixed · IMIT SCR cutoffs · V20 applied to live UIO · IUK SMMT/DVLA · more EQ-HIT pulls · ITUK brake 0.4 vs 0.8.

---

## Lane B — H4 GPS/PMS V2 (Mode B tab only)

**Purpose:** *This page exists so Jerome can decide whether V1 capture is lying about an LCV market, using mileage-true expected that refreshes when the V2 shadow CSVs refresh.*

**Allowed later (rebuild/ship):** deepen the existing Command Center tab **GPS/PMS V2 LCV** from CSVs already on disk. No new HTML.

| Touch | Path |
|-------|------|
| Builder | `02_dashboards/_build/build_aftermarket_bi_command_center.py` |
| HTML | `02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html` |
| Open | `02_dashboards/sales/OPEN_Aftermarket_BI_Command_Center.cmd` |
| Capture | `01_data/00_derived/pms_capture_by_db_year_v2_mileage.csv` |
| Opt1 sensitivity | `01_data/00_derived/pms_v2_lcv_opt1_sensitivity.csv` |
| Opt2/3 skeleton | `01_data/00_derived/pms_v2_lcv_opt_skeleton.csv` (Portugal + Ireland only) |
| EQ-HIT gap | `01_data/00_derived/pms_v2_eqhit_category_gap_cy2025.csv` |
| Coverage | `01_data/00_derived/pms_v2_eqhit_fitment_coverage.csv` |
| Claims | [`GPS_PMS_V2_CLAIM_FRAMEWORK.md`](GPS_PMS_V2_CLAIM_FRAMEWORK.md) |

**On screen always:** car park still **V19**; IUK **44,926** is the only locked V20 number; extract = **37 seed PNs**; PMS headline = **total** capture.

**Forbidden this lane:** apply V20 to the live workbook · invent SCR 15k/20k · more EQ-HIT catalogue pulls · V1 cutover · new H4 HTML.

**This turn (rebuild 2026-09-07):** V2 tab has V19 / IUK 44,926 / 37 seed PNs / Grade D on screen. Same HTML filename.

---

## Lane C — P4 who went quiet

**Purpose:** *This surface exists so Jerome can decide which distributors went quiet this cycle, using mail timestamps and dated promises that refresh when the interaction collector runs.*

Builder is done. Calibration is not. Spec: [`../P4_DETERMINISTIC_SIGNALS.md`](../P4_DETERMINISTIC_SIGNALS.md).

**Your 1-day gate (task 4.9):** lock amber/red on these eight draft signals — latency · met-rate · signal→order · churn · escalation · topic · volume drop · overdue. Until then: **not a KPI**.

| Touch (after 4.9) | Path |
|-------------------|------|
| Builder | `04_tools/interactions/build_account_health.py` |
| Parquet (gitignored) | `01_data/17_interactions/account_health.parquet` |
| Calibration CSV | `01_data/17_interactions/account_health_calibration.csv` |
| Triage (draft) | `01_data/17_interactions/ACCOUNT_HEALTH_OPS_TRIAGE_20260819.md` |

**Allowed later:** Mode B triage + internal PRISM shelf. Not a fifth BI home. Not Mode A. Not H1.

**Forbidden:** treating draft NONE/AMBER/RED as a meeting number · LLM mail (P2b/P3 still blocked) · new account-health HTML home.

**This turn (rebuild 2026-09-07):** 4.9 still not locked — no widget. Mode B triage stays `ACCOUNT_HEALTH_OPS_TRIAGE_20260819.md`.

---

## Lane D — H2/H3 sales to dealer (no Duncan file)

**H2 purpose:** *This pack exists so Jerome can decide which distributor to take into a sales-to-dealer meeting, using AIM/GPS for every DB that has files (2025 snapshot).*

**H3 purpose:** *This pack exists so Jerome can decide where bill vs dealer sales breaks by layer in one meeting, using the six-DB cuts already on disk (2025 snapshot).*

StD stays meeting packs, not a weekly home. DBs: ITUK · UTI · IRELAND · IUK · GREECE · PORTUGAL.

| Touch | Path |
|-------|------|
| H2 builder | `03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py` |
| H2 HTML | `02_dashboards/sales/Dealer_Sellout_AIM_GPS_Sales_to_Dealer_2025.html` |
| H2 open | `02_dashboards/sales/OPEN_Dealer_Sellout_AIM_GPS.cmd` |
| H3 builder | `03_analytics/Isuzu/prism/scripts/build_next_analyses_std.py` |
| H3 HTML | `02_dashboards/sales/Next_Analyses_Sales_to_Dealer_SixDB.html` |
| H3 open | `02_dashboards/sales/OPEN_Next_Analyses_Sales_to_Dealer_SixDB.cmd` |
| Findings | `01_data/00_derived/next_analyses_findings.md` |

**Story already computed (do not rediscover):** UTI BVP capture **92.5%** vs IUK **8.5%**; UTI billing vs StD **−36%**; ITUK dealer spread; GREECE amber when peer missing. PMS headline = **total**.

**Forbidden:** waiting on Duncan as if the pack cannot exist · ITUK/UTI-only titles · Monday StD command center · blending UTI into IDS Israel · new StD filename.

**This turn (rebuild 2026-09-07):** H2 hero = 6 networks / UTI 92.3% / IUK 8.5%. H3 hero = UTI 92.5% / IUK 8.5% / UTI −35.7%. GREECE+ITUK 2026 amber on H3. Chart.js inlined on H2.

---

## If a later message says rebuild / ship

One lane per message. `OPEN: cmd-only`. Ship-gate on the existing HTML, not a new filename. No INDEX rewrite. P4 also needs 4.9 locked in that same thread.
