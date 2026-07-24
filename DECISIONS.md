# ISZE decision log (append-only)

**Format:** Newest at top. Do not edit past entries — supersede with a new entry referencing the superseded date.

**Related:** [CHANGELOG.md](CHANGELOG.md) · [00_docs/AUTOMATION_REGISTER.md](00_docs/AUTOMATION_REGISTER.md) · [AGENTS.md](AGENTS.md)

---

## 2026-07-21 — `country_overrides.factors` fixed on the bucketed PMS path; revenue_gap_eur quotable-KPI firewall added

**Status:** Accepted — Jerome approved via "do all" on Safety&capital top-10. Fixes the "`country_overrides.factors` is dead config" roadmap row (found 2026-07-16, not fixed pending sign-off) and acts on the "Not done — `revenue_gap_eur` is still unsafe" note from the 2026-07-17 entry below.

**Fix 1 — dead config.** `modules/pms_engine.expected_by_category_bucketed()` built its per-category factors from `{**CONSUMABLE_FACTOR, **WEAR_FACTOR}` + `LCV_BUCKET_FACTOR_OVERRIDES` and never read `cfg["factor_overrides"]` (the per-distributor `country_overrides.factors` block resolved by `parc_config_for_distributor()`). Turned out the legacy single-scope loop inside `calculate_pms_capture()` had the **same bug** — neither path in `pms_engine.py` applied it; only `scripts/build_bvp_p0_p1.py::_expected_qty_for_db()` (the fallback used for distributors with no `uio_by_model_bucket.csv` entry) did. Both `pms_engine.py` paths now apply `factor_overrides` with the same override-replaces-default precedence as `_expected_qty_for_db()`, checked before the `LCV_BUCKET_FACTOR_OVERRIDES` bucket-component fallback. `scripts/build_bvp_p0_p1.py` needed no change — it calls `expected_by_category_bucketed()` directly and inherits the fix.

**Verified on real data (registry-only actuals, no catalog fill):** ITUK brake_pad CY2025 — expected 5,840.1 → **4,672.1** (denominator now uses the confirmed 0.4 interval ratio, not the global 0.5), actual 3,402 units unchanged, capture **58.3% → 72.8%** (roadmap's 2026-07-16 estimate of ~58.3%→~72.9% confirmed within rounding). ITUK oil-filter anchors unaffected (override is brake-only). 61/61 `pytest tests/` pass.

**Still open, unresolved by this fix:** whether ITUK's merged brake factor should be 0.4 or 0.8 — see the roadmap row immediately below this one. This fix makes the *configured* 0.4 finally take effect; it does not adjudicate whether 0.4 is correct. If IML confirms 0.8, ITUK brake capture reads ~2x optimistic even after this fix (~36.4% real vs the 72.8% now shown).

**Fix 2 — `revenue_gap_eur` quotable-KPI firewall.** `avg_sp = act_rev/act_qty if act_qty>0 else 0.0` means a distributor with **zero actual sales** in a category books a **€0 gap** — the worst real outcome scores as the smallest (best-looking) gap, unsafe for € league-table ranking (flagged 2026-07-17 below, `pms_engine.py:610-612`, and identically present in `scripts/build_bvp_p0_p1.py`'s P1 build). Considered a network-median unit-price fallback per the ask, but `calculate_pms_capture()` runs one distributor at a time with no visibility into other distributors' prices, and `build_bvp_p0_p1.py`'s `revenue_gap_eur` sum feeds `pms_summary_by_db.csv` / `pms_opportunity_matrix.csv` / `aim_gps_matrix.csv` (the €17.09M CY2025 network gap quoted 2026-07-17) with no pinned exact-value drift check to safely re-baseline against — judged too invasive to silently reprice without a separate sign-off on the new target numbers. **Decision: additive firewall, not a value change.** Both `pms_engine.py` (`calculate_pms_capture` → `summary_df['revenue_gap_quotable']`, dict key `revenue_gap_quotable`, plus `total_opportunity_eur_quotable` excluding non-quotable categories) and `scripts/build_bvp_p0_p1.py` (`revenue_gap_eur` output rows → new `revenue_gap_quotable` column) now flag `False` whenever `act_qty==0` for that category/row. No existing `revenue_gap_eur` value changed. Callers must filter `revenue_gap_quotable==False` out of any € ranking; this has not yet been retrofitted into `pages/16_AIM_GPS_Matrix.py` or the opportunity-matrix pages — follow-up needed before the €17.09M figure is re-quoted.

**Files updated:** `03_analytics/Isuzu/prism/modules/pms_engine.py` (`expected_by_category_bucketed()`, legacy loop in `calculate_pms_capture()`, `revenue_gap_quotable` firewall), `03_analytics/Isuzu/prism/scripts/build_bvp_p0_p1.py` (`revenue_gap_quotable` column + firewall comment), `00_docs/ISZE_ROADMAP.md` (row marked fixed), `00_docs/ITUK_PRISM_LANE_BRIDGE.md` (new — Model B/IML external lane vs PRISM internal network lane, when to quote which), `FACTS.md` (pointer to bridge doc added). Derived CSVs **not regenerated** in this pass (no full pipeline run) — `pms_capture_by_db_year.csv` on disk still reflects the pre-fix ITUK brake numbers and the `revenue_gap_quotable` column will only appear after the next `run_pipeline_and_verify.ps1`.

---

## 2026-07-17 — Quadrant page 16: AIM pricing-risk axis retired, replaced by PMS capture; partial-year defaults fixed

**Status:** Accepted — Jerome's call this session ("replace the AIM axis" + "fix the defects"). Triggered by a request for a distributor action list off the AIM × GPS quadrant, which could not be produced from the artifact as it stood.

**Context — the AIM axis never fired.** `build_aim_gps_matrix.py` gated the x-axis at a hardcoded `RISK_HIGH_PCT = 0.12`. The metric it gates, `aim_high_risk_pct`, has an all-time max of **0.0487** (Norway 2023) and a CY2025 network level of **0.0099** (€316,409 high-risk on €31.96M AIM-matched). **Zero of 88 rows had ever crossed 0.12.** So `aim_low_risk` was `True` for every real distributor in every year and the quadrant collapsed into a 1-D restatement of `gps_high`: `margin_risk` had **0 rows ever**, `priority_target` had **1** — the `UNMAPPED` null row, manufactured by `aim_high_risk_pct.fillna(1.0)` turning missing data into a fake 100%-risk "priority target". The metric itself is sound and correctly denominated on AIM-matched revenue (verified 82/82 rows against `build_bvp_p4_p5.py:290-296`); the threshold was simply never calibrated against it. **AIM pricing risk does not separate this network** — it is retained as a context column, not an axis.

**Decision: x = PMS total capture** (`pms_capture_by_db_year.csv`, `line_type='total'`, sum(actual)/sum(expected) per contract 9). It has real spread and populates all four corners. New quadrants: **defend** (high GPS · high capture), **attach_gap** (high GPS · low capture — spending but not servicing), **wallet_gap** (low GPS · high capture), **priority_target** (both below median), **insufficient_data**.

**Three defects fixed in the same pass:**
1. **Partial-year default.** `pages/16` used `index=len(years)-1` and `build_isze_dashboard_json.py` used `df["year"].max()` — both silently switched from a complete CY2025 to a quarter of CY2026 when `sales_2026tillApril.XLSX` landed on 2026-07-03. `isze_data.json` has been publishing `gps.year: 2026` with `network_median_spu_eur` ≈ **€48** (a Q1 total) as the headline annual figure, while its own `methodology` string still read "CY2025". Now `latest_complete_year()` → 2025, median **€191.4**. New shared module `modules/year_coverage.py` reads real coverage from `sales_fact` (2023=99%, 2024=100%, 2025=100%, **2026=25%**).
2. **Pooled cross-year median.** `med_spu` was one constant (€160.72) computed over all years *including* the Q1-2026 rows, then applied to every year — the "high GPS" bar sat ~€30/unit too low. Now a **per-year** median (2025 = €191.45), which also keeps a partial year internally comparable since every distributor is truncated by the same window.
3. **`fillna` coercion onto axes.** `gps_spu.fillna(0)` scored the four no-UIO markets (Armenia, Kazakhstan, Palestine, **Ukraine — €1.16M CY2025**) as "low GPS · grow_capture" on a denominator that does not exist, while their `gps_traffic_light` read `unknown`. They are now `insufficient_data`, excluded from the plot and from the medians.

**Verified:** all four quadrants populate (CY2025: defend 6 / priority_target 6 / attach_gap 3 / wallet_gap 3 / insufficient_data 4). ITUK oil-filter anchors unchanged and still reconcile to `FACTS.md` §1b (expected 11,680.2 / actual 13,599 / 116% uncapped / €96,024). Page data path replayed headless — defaults to CY2025, no partial banner, 18 plotted / 4 excluded. **Axis is robust to category scope:** no CY2025 distributor changes quadrant between `--scope all` (14 categories) and `--scope filters` (oil/fuel/air), so the urea_filter and clutch_booster denominator doubts shift the absolute capture level but not the ranking.

**Not done — `revenue_gap_eur` is still unsafe as a € ranking column.** `modules/pms_engine.py:610-612` computes `avg_sp = act_rev/act_qty if act_qty > 0 else 0.0`, then `gap = gap_qty * avg_sp` — so **a distributor selling zero in a category books a €0 gap**, and the worst case scores best (ITUK `blower_filter`: 2,920 expected, 0 actual, €0 gap). Compounding it: `urea_filter` expected demand equals `oil_filter` expected exactly (152,141.8 network — every unit assumed SCR-equipped), and `clutch_booster` runs 0.21% capture on a €137 price sampled from 2 ITUK units. The €17.09M network CY2025 "gap" is not quotable, consistent with the standing part-master flag that gaps overstate. Needs a network-median price fallback and a denominator review before any € league is ranked off it.

**Files updated:** `03_analytics/Isuzu/prism/scripts/build_aim_gps_matrix.py` (rewritten), `pages/16_AIM_GPS_Matrix.py` (rewritten), `scripts/build_isze_dashboard_json.py` (2 call sites), `modules/year_coverage.py` (new), `00_docs/ISZE_ROADMAP.md`. Regenerated: `01_data/00_derived/aim_gps_matrix.csv` + `.parquet`. **`isze_data.json` deliberately NOT regenerated** — the year/median correction should go through `run_pipeline_and_verify.ps1` and the drift gate, not a side-effect write.

---

## 2026-07-16 — Brakes are one category per part type: front/rear split dropped from PMS capture (option b)

**Status:** Accepted — Jerome's call this session. Resolves the "Brake front/rear split" roadmap row open since 2026-07-15.

**Context:** `brake_pad_front/rear` + `brake_shoe_front/rear` carried real `wear_factor` config and real catalog PNs but 0 actuals in `bvp_pn_dimension.csv`, because `modules/bvp_catalog_io.SHEET_MAP` is flat (one "BRAKE PAD KIT" sheet → `brake_pad`). The 2026-07-15 diagnosis framed this as empty numerators. **The re-run shows that understated it:** parent `brake_pad`/`brake_shoe` were *already* live in `P1_CATEGORIES` via `_DEFAULT_WEAR` in `modules/pms_capture_config.py` — the YAML `wear_factor` is merged **onto** that dict, not substituted for it — so brake demand was estimated **three times** over one parc (parent 0.5 + front 0.5 + rear 0.5). The capture drag was phantom *expected* demand in the denominator, not the zero numerators.

**Decision: option (b)** — drop the 4 split categories, keep the parents. Option (a) (inherit the front/rear split from `parts_catalog_dimension.csv`) was rejected: the split PNs do carry real sales (~€1.44M `brake_pad_front`), but the split is only partial (22 pad + 84 shoe PNs have no front/rear class and carry 38,036 + 18,085 units), so the parents could not then be removed — (a) would have filled the numerators while leaving the denominator tripled, converting a visible zero row into an invisible wrong rate. Commercial rationale: front/rear is not a unit of commercial action (there is no front-pad campaign), and the only market with real data (ITUK, IML slide 2026-07-14) has front+rear replaced **together as one job**, not as independent wear cycles. Keeping the split would oblige a per-axle wear factor per market that nobody has measured. (b) also matches what is already published — `FACTS.md` §2 states one brake wear factor of 0.5 per scope — and what the newer bucketed path already assumes (`LCV_BUCKET_FACTOR_OVERRIDES` is parent-only).

**ITUK kept market-specific** (Jerome: "keep ITUK as it's a separate market"). Its 0.4 is an interval ratio (40,000/100,000 km), derived independently of axle count, so it transfers to the merged categories unchanged.

**Verified by pipeline re-run:** P1 3,888 → 3,024 rows (864 removed = 4 cats × 72 × 3 line_types); all surviving actuals identical (brake_pad 57,314 / brake_shoe 21,907 / brake_rotor 66,699); network expected-weighted capture CY2025 (`total`) **23.8% → 32.0%**, matching the 31.9% quoted 2026-07-15 within data drift; ITUK oil-filter anchors unchanged (154%/84%/116%, still consistent with `FACTS.md` §1b); 40/40 prism tests pass.

**Two things this surfaced, both still open — see the new roadmap rows:**
1. **`country_overrides.factors` is dead config for every bucketed distributor.** `expected_by_category_bucketed()` never reads `cfg["factor_overrides"]`, so ITUK's brake override resolves correctly into the parc config but the applied factor is the global 0.5, not 0.4 — it has never taken effect since 2026-07-15. Not fixed here: it moves ITUK brake capture ~58.3% → ~72.9%, which needs sign-off.
2. **Is ITUK's merged brake factor 0.4 or 0.8?** If one paired "2item" job consumes a pad set per axle, 0.8 is the right basis and ITUK brake capture reads ~2x optimistic. A units question about what one `brake_pad` unit represents — needs IML, not a guess. Currently moot in the output because of (1).

**Files updated:** `03_analytics/Isuzu/prism/data/pms_capture_assumptions.yaml` (wear_factor + ITUK override; parents now restated explicitly so they are visible to anyone editing the YAML). Regenerated: `01_data/00_derived/pms_capture_by_db_year.csv` + `.parquet`, `pms_summary_by_db.csv`. `bvp_pn_dimension.csv` unchanged by design — option (b) is a config decision, `SHEET_MAP` stays flat.

---

## 2026-07-06 — UTI PMS deck: clutch reported as one family (20.3%), not four subcategories; FY-label bug fixed (FY2026→FY2025)

**Status:** Accepted — corrects `UTI_Performance_Review_FY2027Q1_DRAFT.pptx` slides 8–9 (PMS Capture Rate table + chart)
**Context:** Jerome flagged that an earlier session this morning used a deprecated model (`ITUK_UTI_PMS_Study.pdf`, built on a broken `bvp_pn_dimension.csv` mislabeling 414/431 genuine PNs as BVP) instead of the reconciled one — `UTI_Questions_and_Assumptions.docx` explicitly deprecates that PDF. Corrected model = `_build/uti_iml_fy_engine.py` — IML v7 intervals (filters 1.25×/yr, wear parts 0.5×/yr @ 50,000 km/yr assumed mileage, carried over unverified from the ITUK workbook), 100% addressable, current UIO 10,336 (FY2025). This entry is based on an independent re-run of that engine against `sales_fact.parquet` + `bvp_pn_dimension.csv` this session, not on the prior session's stated figures.

**Two findings from the re-run:**

1. **Clutch subcategory split is a broken weighting assumption, not a data error.** `CLUTCH_W` allocates only ~17% of clutch-job demand to the "kit" PN, assuming components are bought separately. UTI's actual FY2025 sales (disc 4.3%, pressure plate 4.8%, kit 108.9%, booster 1.1%) show UTI buys the all-in-one kit PN for nearly every clutch job — the 108.9%/109% single-category read is an artifact of scoring kit sales against its artificially small allocated slice, not a real overshoot. **Decision: report clutch as one rolled-up family (20.3% capture, EUR55,388 revenue, EUR217,624 gap) instead of 4 separate subcategory rows.** Do not hard-cap at 100% anywhere in the pipeline — only the HTML bar-width rendering (`build_uti_pms_capped_study.py` `cap_pct()`) caps for chart legibility; the underlying number stays uncapped everywhere else.
2. **The two PMS slides were labeled "FY2026" but the data is actually FY2025 actuals.** FY2026 Q1 UTI billing extract shows zero lines (a separate, already-flagged, unresolved anomaly — see the 2026-07-06 finding in `UTI_PerformanceReview_Jul2026_updated_draft.pptx`, slide 3). Until that's resolved, FY2026 has no real PMS capture numbers to show. **Decision: label these two slides FY2025, not FY2026, and do not present FY2026 PMS figures until the zero-billing anomaly is resolved.**

**Revised FY2025 headline (UTI, IML v7 intervals):** Oil Filter 31.3% / Fuel Filter 74.8% / Air Filter 58.1% / Brake Pad 26.7% / Clutch (family) 20.3%. Combined gap across all 5: **EUR554,647** (previously reported EUR427,519 — that figure excluded clutch kit entirely and lost the family view of the true clutch gap).

**Caveat carried forward, unresolved:** the 50,000 km/yr mileage assumption behind both the filter (40,000km interval) and wear-part (100,000km clutch interval) factors is copied from the ITUK IML v7 workbook, not separately verified for Israeli duty cycles — open question for UTI, same status as the existing brake-mileage question in `UTI_Questions_and_Assumptions.docx`.

**Files updated:** `09_meetings/Preparation Meetings/UTI/UTI_Performance_Review_FY2027Q1_PMS_CLUTCHFAMILY_CORRECTED.pptx` (new file — original `_DRAFT.pptx` left untouched). Verification run + full per-category detail (FY2024–2026, all 8 subcategories): `03_analytics/Isuzu/pms-pilot/uti_iml_v7_results_2026-07-06.json`.

---

## 2026-07-02 — ITUK PMS standard switched to Model B (IML v7 schedule) for all IML/external use

**Status:** Accepted — supersedes the ITUK headline figures in the PMS audit entry below (same date)  
**Context:** Jerome confirmed: adopt **Model B** (`ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx`) as the single ITUK/IML headline everywhere — dashboards, FACTS.md, briefs, studies, `isze_data.json`. This aligns workspace outputs with the business case v3 and Apr 2026 trip report already used with IML.

**Decision — ITUK headline numbers (CY2025, ISZE→ITUK):**
| Metric | Value |
|---|---|
| Oil-filter cover | **35.1%** (40.6% ITUK→DLR) |
| PMS revenue gap | **€2.04M** (5 categories: oil, fuel, air, clutch, brake) |
| Service frequency | Oil/Fuel/Air **1.25×/yr**; Clutch/Brake **0.5×/yr** |
| Denominator | UIO **22,389** full DVLA |
| Addressable | **100%** (no discount) |
| Source | `prism/data/iml_v7_ituk_cy2025.yaml` ← v7 workbook |

**PRISM lane retained for:** network league (other 17 DBs), `pms_capture_by_db_year.csv` pipeline, internal cross-check. Exposed in `isze_data.json` as `pms.ituk_prism_lane` — not for IML headlines.

**Consequences:** All ITUK-facing docs, MASTER_DASHBOARD, ops HTML, weekly briefs, scratch studies updated to Model B. Do not quote PRISM 100%/173% oil filter or €870K/€457K gap as ITUK headline anymore.

**Docs updated:** `FACTS.md` §1, `pms-coverage.md`, `build_isze_dashboard_json.py`, `pms_briefs/ITUK_pms_capture.md`, dashboard HTML, scratch studies.

---

## 2026-07-02 — PMS study audit: six live, mutually contradictory ITUK PMS figures; PRISM/FACTS.md confirmed SSOT, others flagged as unreconciled

**Status:** Superseded for ITUK headlines by Model B adoption entry above — PRISM remains internal network SSOT  
**Context:** Full audit of every PMS-related document in the workspace (requested by Jerome, scope = "everything PMS-related"). Found six independently-built ITUK PMS studies, each with its own service-frequency, denominator, and addressability assumptions, none formally reconciled against `pms_capture_by_db_year.csv`/`FACTS.md` since the latter became the designated "quantitative spine" (2026-06-13 decision). Same underlying sales data, wildly different headline numbers depending on which file is open:

| Source | Date | Oil-filter capture (ITUK, 2025) | ITUK PMS revenue gap | Service freq. | Denominator | Addressable |
|---|---|---|---|---|---|---|
| **FACTS.md / PRISM (SSOT)** | rebuilt 2026-06-15 | **173% uncapped / 100% capped** (genuine 131%, BVP 42%) | not a single published figure — "story is mix, not deficit" | 0.5 svc/yr (N75-blended) | UIO 22,389, N75-scoped | 70% |
| `pms-pilot/ITUK_PMS_Analysis_Apr2026_v7` (active — feeds trip report/business case) | May 2026 | 35.1% (ISZE→ITUK) / 40.6% (ITUK→DLR) | ≈€2.04M (sum of 5-category revenue gap, ISZE→ITUK sheet) | 1.25 svc/yr (IML 40,000km interval ÷ 50,000km/yr) | UIO 22,389 full fleet | 100% (none) |
| `pms-pilot/ISZE_EU_PMS_Model_Apr2026_v1` (Old_vs_New tab) | Apr 2026 | n/a (EU-interval based) | **€0.51M–€1.58M band, mid-case €0.75M** — own annotation: *"HONEST TAKE: realistic ITUK PMS gap = €0.5M–€1.6M (not €10M, not €3.5M)"* | EU manual km-intervals (scenario-dependent) | Addressable UIO | 55% |
| `pms-pilot/ISZE_ITUK_DataPack_v1` (`Kosha_Gap_OneNumber`, built from PRISM's own derived data) | May 2026 | n/a | **€456,963** (45.4% of €1.01M TAM); network total €5.07M | inherits PRISM | inherits PRISM | inherits PRISM |
| `pms-pilot/_archive/ISZE_PMS_Coverage_Analysis_Mar2026_v2` (superseded, itself a correction of an earlier v1) | Mar 2026 | 94.5% vs ITUK's own 12,010-vehicle car park (1×/yr); 50.7% vs full DVLA (1×/yr); 23.9% vs full DVLA at 2.12 svc/yr | reframed away from a single €3.5M figure — "gap is 10,379 vehicles outside ITUK network, not workshop failure" | 1× or 2.12× (mileage-derived) | 12,010 (ITUK car park) or 22,389 (DVLA) | 100% (none) |
| `01_data/03_PMS/…BusinessCase_Apr2026_v3.docx` (the document actually driving the IML approval ask) | Apr 2026 | quotes "Full DVLA cover rate 13–33%" as a third, separate denominator logic | not a single figure — layered £265/veh/yr and £186/veh/yr assumptions on top | mileage-derived, per category | 12,010 (in-warranty) vs 22,389 (full DVLA) split | 100% (none) |
| Global memory quick-reference (top-level CLAUDE.md) + several weekly briefs (15/16 Mar, 27 Apr) | still live | **"0.3%"** | **"~€3.5M+"** | 1.5 svc/yr (legacy) | ~31,751 expected | n/a |

The last row is the most urgent: **FACTS.md's own "DO NOT QUOTE — obsolete figures" table already blacklists 0.3%** ("wrong denominator entirely — legacy 1.5 svc/yr defect"), and no FACTS.md-traced source ever adopted €3.5M — that figure's lineage runs through a Mar 2026 "€3.5M from ITUK workshop failure" claim that the archived Coverage_Analysis_Mar2026_v2 workbook *itself* already reframed and retracted, then resurfaced anyway in weekly briefs and the global memory snapshot. Secondary finding: `prism/docs/metric_dictionary.md`'s own worked example (lines ~117–128) still shows the **pre-2026-06-15-supplement** 2025 figures (162%/120%/42%, €84,779) instead of FACTS.md's current post-supplement figures (173%/131%/42%, €95,706) — minor drift inside the spine's own documentation, not just the external studies.

**Decision:** `FACTS.md` + `01_data/derived/pms_capture_by_db_year.csv` remain the sole source of truth for capture-rate and PMS-gap figures, per the existing 2026-06-13 "quantitative spine" and "verify-before-quote" decisions — this audit found no reason to change that. None of the six study documents above should be quoted externally (to ITUK/IML) or relied on for a headline capture %/gap € without re-deriving from PRISM first. However, the disagreement between PRISM and the ITUK-specific studies (v7, EU model, business case v3) is **not**, in most cases, a data error — it is a genuine three-way methodology fork that has never been put to IML for resolution:
1. **Service frequency** — PRISM's flat 0.5 svc/yr (N75-blended) vs v7's IML-schedule-derived 1.25 svc/yr vs archived v2's mileage-derived 2.12 svc/yr vs the EU model's km-interval scenarios. Roughly a 4× spread on the single biggest driver of "expected demand."
2. **Denominator** — N75-only-scoped UIO (PRISM) vs full DVLA fleet 22,389 (v7, archived v2, business case) vs ITUK's own 12,010-vehicle warranty car park (business case v3, archived v2). Up to ~1.9× spread.
3. **Addressability discount** — PRISM 70%, EU model 55%, all others 100% (none applied).

Until (1)–(3) are agreed with IML (open item already logged in `05_memory/projects/pms-coverage.md`: "EQ-HIT mapping for PN → service schedule — ITUK validation pending"; "CY2025 full PMS basket gap revalidation pending"), any headline PMS gap figure is presentation-dependent, not fact-dependent — swapping which document you open changes the answer by 20×+ (€0.45M to €10.2M) without touching the underlying sales data.

**Consequences:**
- Stop citing "0.3% capture" / "~€3.5M+ gap" anywhere — scrub `05_memory/projects/pms-coverage.md`, weekly briefs, and the top-level global CLAUDE.md quick-reference (outside this repo — flagged to Jerome separately, not edited here). Replace with either the FACTS.md capped figure (100%, "mix not deficit") or an explicit range with a "methodology not reconciled" caveat — never a single unqualified number.
- **External risk:** `ITUK_PMS_BusinessCase_Apr2026_v3.docx` and the Apr 2026 trip report — the documents actually used with ITUK/IML — are built on the v5–v7 working file + WS2025 + a bespoke warranty-fleet framing, **not** on PRISM/FACTS.md. If IML or ITUK cross-checks ISZE's PRISM dashboard (capture ~100%, "mix not deficit") against the business case's own denominator logic (implying far lower capture), the inconsistency is visible from the outside. This should be resolved or explicitly bridged before the next ITUK/IML pricing or PMS round — do not let this surface for the first time in a live negotiation.
- **Fixed in this pass:** `metric_dictionary.md`'s stale pre-supplement worked example (162%/120%/42%/€84,779 → 173%/131%/42%/€95,706) now matches FACTS.md.
- `pms-pilot/_archive/*` and the top-level `ISZE_PMS_Coverage_Analysis_Mar2026_v2.xlsx` are correctly archived (superseded) — no action needed beyond not resurrecting their numbers.

**Alternatives considered:** Treat each study as answering a genuinely different question (partially true — the EU model, WS2025 cover-ratio workbook, and business case v3 do serve distinct purposes) and take no reconciliation action. Rejected for the headline oil-filter capture %/gap € specifically — those get quoted interchangeably across documents as if they were the same metric, which is where the actual risk sits, even though the underlying analyses have legitimate reasons to differ in scope.

**Docs updated:** This entry; `05_memory/projects/pms-coverage.md` (audit trail + open-questions update, same date); `prism/docs/metric_dictionary.md` (worked example resynced to post-supplement FACTS.md figures).

---

## 2026-07-03 — Credit notes/returns (SaTy CR/RE) excluded from revenue metrics without ERP confirmation

**Status:** Accepted — reversible judgment call, not ERP-confirmed
**Context:** Flag H noted zero negative-value rows in `sales_fact` and asked to confirm returns are pre-netted. Jerome flagged that SaTy carries explicit `CR`/`RE` codes and said he "might have excluded" these before, and confirmed no ERP confirmation is coming soon. Investigation found 280 rows / €1,651,149 (network-wide, 2023-2026) tagged SaTy CR or RE, all positive-value (BillT=RE is a strict subset, adds nothing). `saty_mapping.py` already bucketed CR/RE as "standard" order type, but that's a different axis (VOR/urgent/backorder segmentation) and doesn't speak to revenue inclusion. A dormant `is_credit_note` flag already existed (`net_sales_value < 0`) and was already wired as a GPS exclusion filter (`gps_engine.py:130`) but had never fired, since no negative rows exist.
**Decision:** Extend `is_credit_note` to also catch SaTy CR/RE (`sales_loader.py`, `data_prep.py`), and wire the same exclusion into the parts base (`build_metrics_snapshot.py`) and PMS capture actuals (`build_bvp_p0_p1.py`) — mirroring the existing TRANSPORT/REBATE exclusion pattern (flag A), not inventing a new mechanism.
**Alternatives considered:** Wait for ERP confirmation (rejected — Jerome does not expect this soon, and leaving flag H as a vague "verify" note provides false comfort while €1.65M of unverified return/credit revenue sits in every headline number); silently drop with no documentation (rejected — violates the labelled-assumption pattern used throughout this pipeline).
**Consequences:** Parts base and PMS capture actuals both shift down slightly from this exclusion (partially masked by the same-day sales-file rebuild, which added more than it removed — net effect is an increase). If SAP later says CR/RE should NOT be excluded, revert by narrowing `is_credit_note`'s definition back to sign-only — one line in each of two files.
**Docs updated:** `FACTS.md` flag H, `modules/sales_loader.py`, `modules/data_prep.py`, `scripts/build_metrics_snapshot.py`, `scripts/build_bvp_p0_p1.py`.

---

## 2026-07-03 — Wire in Jan-Mar 2026 + more-complete 2025 re-export; leave dedicated Israel extract unwired

**Status:** Accepted
**Context:** `sales_2026tillApril.XLSX` and `CY2024-2025.XLSX` had sat in `01_data/` root since 2026-06-16 — over two weeks before this work started — undiscovered by two prior audit passes despite a directory listing surfacing both filenames. `CY2024-2025.XLSX`'s 2024 rows are verified byte-identical to the currently-loaded `CY2023-2024.XLSX` (154,519 rows, full Bill.Doc. match); its 2025 rows are a more-complete re-export (148,778 vs 147,409, +1,369). `sales_2026tillApril.XLSX` is Jan 5–Mar 31 2026, non-overlapping, and closes the FY2025 (Apr–Mar) completeness trap flagged since 2026-05-28.
**Decision:** Copy both into `01_data/12_raw/sales/`. Give `build_sales_fact_from_cy.py` an explicit per-file year-ownership map (`CY_FILE_YEARS`) so each source file owns only the years it uniquely/best covers — `CY2023-2024.XLSX` → 2023 only, `CY2024-2025.XLSX` → 2024+2025 (supersedes the old `CY2025.XLSX`, no longer loaded), `sales_2026tillApril.XLSX` → 2026. This avoids double-counting 2024 without deleting any source file. Separately investigated `Sales_israel_1799&_1797.XLSX` (flagged by another session as part of "raw SAP billing") — confirmed row-for-row and euro-for-euro identical to what the three CY files already contain, with one no-date footer/grand-total row (€21.7M, exactly the sum of its real rows — same defect class already handled for the main CY files). **Not wired in** — it is a redundant, customer-filtered export, not missing data; adding it would double-count UMI/Israel billing.
**Consequences:** `sales_fact.parquet` grew 434,858 → 477,505 rows. `verification_fixtures.yaml` row_count/years/required_raw updated to match. FACTS.md parts base and GPS% anchors both drifted (legitimately) and were reconciled in the same-day 2026-07-03 entry above.
**Docs updated:** `build_sales_fact_from_cy.py`, `verification_fixtures.yaml`, `FACTS.md`, `05_memory/projects/pms-coverage.md`.

---

## 2026-07-02 — Network GPS (waterfall) CY2025 re-based 40.2% → 50.2% (MIDI out of the denominator)

**Status:** Accepted  
**Context:** FACTS anchor `waterfall.network.gps_pct_2025` was seeded 2026-06-10 at 40.2% with MIDI's ~€15M theoretical wallet (98,654 UIO) in the denominator and zero ISZE-direct sales in the numerator. The MIDI-not-a-customer decision (exclude from GPS/Projection tables) flowed through the 2026-06-18 UIO refresh; 2026-07-02 was the first drift-checked full gate since, and it flagged the anchor.  
**Decision:** Pipeline side is correct — anchor updated to **50.2%** (ex-MIDI), FACTS.md change log updated in the same pass per the drift-reconcile protocol. Verified: current waterfall wallet €60.2M / captured €30.2M = 50.2%; adding MIDI's wallet back reproduces 40.2% exactly.  
**Consequences:** Any deck or note quoting "network GPS ~40%" is on the old MIDI-inclusive basis — restate as 50.2% ex-MIDI. Not caused by the same-day air-filter change (oil/mix/parts-base anchors all 0.00% drift).  
**Docs updated:** `facts_anchor.yaml`, `FACTS.md`, `05_memory` GPS references.

---

## 2026-07-02 — Air-filter capture goes interval-aware on a PROVISIONAL 0.5 factor (flag C)

**Status:** Accepted — provisional, pending IML  
**Context:** Integrity flag C: flat consumable factors (air = oil = 1.0) overstated air-filter expected demand — air capture deflated ~2× and not comparable across categories. No IML service-interval ratio exists anywhere in the workspace (SPA campaign packs are price-only; Apr 2026 ITUK trip report keeps intervals as assumptions until R&M data lands).  
**Decision:** Set `air_filter` consumable_factor to **0.5** (air element ~every 2nd service vs oil every service) in `pms_capture_assumptions.yaml` + `pms_capture_config.py` defaults. Labelled PROVISIONAL in YAML, code, `pms_service_intervals.md` §3, `metric_dictionary.md`, and the PMS page caveat — same treatment as the `brake_rotor: 0.25` precedent (2026-06-15).  
**Alternatives considered:** Keep flat 1.0 until IML answers (rejected — flag C stays open indefinitely and air capture stays unusable); 0.35 from the YAML header example (rejected — no engineering rationale vs "every 2nd service").  
**Consequences:** All air-filter capture %, gaps, and weighted totals roughly double vs pre-2026-07-02 outputs — do not compare air capture across that date without noting the factor change. One IML number replaces the assumption (conversion formula: `pms_service_intervals.md` §6). **Open on Jerome/IML:** genuine service interval per category + avg annual km per distributor.  
**Docs updated:** `pms_capture_assumptions.yaml`, `pms_capture_config.py`, `pms_service_intervals.md`, `metric_dictionary.md`, `DATA_INTEGRITY_FLAGS_2026-05-28.md`, `3_PMS.py`, `ISZE_ROADMAP.md`, `CHANGELOG.md`.

---

## 2026-06-13 — ISZE root .gitignore policy approved

**Status:** Accepted  
**Context:** Root `.gitignore` was a placeholder (md-only). Git versioning implementation plan (`audit-export/git-versioning-implementation-plan.md`) defined tier-0 exclusions (raw billing, models, deploy mirror, archives).  
**Decision:** Replace placeholder with the full root `.gitignore` from the implementation plan §3. Track docs, code, governance artifacts, and verification JSON only. Never track `01_data/raw/**`, Excel living models, `07_deploy/**`, `90_archive/**`, `91_legacy/**`.  
**Alternatives considered:** Track derived parquet/CSVs (rejected — regenerable, large, PN-level detail).  
**Consequences:** Run `04_tools/workspace/git_preflight.ps1` before first commit; optional pre-commit hook.  
**Docs updated:** `.gitignore`, `04_tools/workspace/git_preflight.ps1`, `CHANGELOG.md`.

---

## 2026-06-13 — PRISM stays a git submodule (not monorepo merge)

**Status:** Superseded 2026-07-24  
**Context:** `03_analytics/Isuzu/prism/` was a nested repo (`jeromio1987/prism`). Archived duplicate `isze-prism-analytics` lives in `90_archive/`.  
**Decision (original):** Keep PRISM as a git submodule.  
**Superseded by:** [2026-07-24 — PRISM folded into ISZE monorepo](#2026-07-24--prism-folded-into-isze-monorepo-holiday-single-clone).

---

## 2026-07-24 — PRISM folded into ISZE monorepo (holiday single-clone)

**Status:** Accepted  
**Context:** GitHub is used as private holiday/laptop backup, not a publish surface. A plain `git clone` of ISZE did not include PRISM file contents without submodule init. Separate remotes (`jarvis-isze`, `isze-dashboard`, standalone `PRISM`) added friction.  
**Decision:** Absorb `03_analytics/Isuzu/prism/` as **normal tracked files** in `jeromio1987/ISZE`. Remove `.gitmodules` and nested `prism/.git`. Day-to-day clone = ISZE only. Archive standalone `PRISM` / `jarvis-isze` / `isze-dashboard` on GitHub (do not delete yet).  
**Alternatives considered:** Keep submodule (rejected — two-step clone); merge personal repos into ISZE (rejected — different sensitivity).  
**Consequences:** `git clone https://github.com/jeromio1987/ISZE.git` is enough for work+PRISM+Jarvis app. See `00_docs/HOLIDAY_LAPTOP.md`.  
**Docs updated:** `DECISIONS.md`, `00_docs/HOLIDAY_LAPTOP.md`, `00_docs/README.md`, `00_docs/RUNBOOK_MONTHLY_REFRESH.md`, `INDEX.md`.

---

## 2026-06-13 — Deploy repo visibility check (manual confirmation pending)

**Status:** Open — agent pre-check done  
**Context:** `07_deploy/Master Dashboard/` → `jeromio1987/isze-dashboard.git`. Secrets sweep flagged aggregate JSON on GitHub Pages as potential public exposure.  
**Agent check (2026-06-13):** Unauthenticated GitHub API returns **404** for `jeromio1987/isze-dashboard` and `jeromio1987/prism`; default `*.github.io` URLs also **404**. Consistent with **private repos** and/or Pages not enabled at default paths — not proof of privacy.  
**Decision:** Treat deploy repo as **separate publish surface** — fully gitignored at ISZE root. Jerome must confirm visibility in GitHub → Settings → Danger Zone / Pages before assuming data exposure level.  
**Manual action:** Revoke old PAT in `90_archive/root_files/` (see `audit-export/secrets-sweep-report.md`) — agent scan found **no token patterns** in non-archive ISZE paths.  
**Docs updated:** This entry.

---

## 2026-06-13 — Unattended scraper auto-fix is propose-only

**Status:** Accepted  
**Context:** `isze-scraper-healthcheck-autofix` runs unattended on a schedule. Auto-applying code patches to scrapers without human review risks breaking production ingest or publishing stale data.  
**Decision:** The healthcheck job may **detect** staleness and **propose** patches (diff/report only). It must **never** auto-apply edits to scraper scripts or publish outputs without Jerome review.  
**Alternatives considered:** Full auto-fix with rollback; manual-only checks with no scheduled job.  
**Consequences:** Scheduled job output is `04_tools/scraper_health_report.md` (+ optional diff). Jerome reviews before any patch is applied. Path preflight aborts if required scripts missing.  
**Docs updated:** [00_docs/AUTOMATION_REGISTER.md](00_docs/AUTOMATION_REGISTER.md), [00_docs/agent/NOTES.md](00_docs/agent/NOTES.md), audit-export `scheduled-path-fix-report.md`.

---

## 2026-06-13 — Deploy-side Data/ paths are compatibility paths (for now)

**Status:** Accepted  
**Context:** GitHub Pages HTML uses `fetch('../Data/...')` and deploy-side `Projects/` URLs. Local source moved to numbered folders (`01_data/`, `03_analytics/`). `sync_to_deploys.ps1` rewrites paths on publish.  
**Decision:** Deploy-side `Data/` and `Projects/` remain **compatibility paths** for published runtime URLs. Agents and local edits use numbered canonical paths only. Never edit `07_deploy/` as source.  
**Alternatives considered:** Rewrite all HTML fetch URLs to numbered paths (deferred — breaks live URLs without coordinated deploy).  
**Consequences:** Document both local source (`01_data/dashboards/`) and deploy fetch target when describing dashboard JSON. Path consolidation Batch 2 preserved deploy rewrites.  
**Docs updated:** [AGENTS.md](AGENTS.md), [00_docs/UI_STACK.md](00_docs/UI_STACK.md), [CHANGELOG.md](CHANGELOG.md) § 2026-06-13.

---

## 2026-06-13 — 07_deploy is generated mirror only

**Status:** Accepted  
**Context:** `07_deploy/Master Dashboard/` and `publish-site/` are synced from `02_dashboards/` and whitelist context docs. Agents were reading deploy-side context mirror and treating it as editable source.  
**Decision:** `07_deploy/` is **generated only**. Edit `02_dashboards/` + run `sync_to_deploys.ps1`; edit bootstrap/numbered MD + run `sync_context_to_github.ps1`. Never hand-edit `07_deploy/Master Dashboard/context/`.  
**Alternatives considered:** Make deploy repo the source of truth (rejected — splits edit workflow).  
**Consequences:** `.cursorignore` hides deploy context from Cursor index. Weekly intel brief must not write to `07_deploy/` (publish risk).  
**Docs updated:** [INDEX.md](INDEX.md), [AGENTS.md](AGENTS.md), [00_docs/ROUTING.yaml](00_docs/ROUTING.yaml) global_ignore.

---

## 2026-06-13 — Verify-before-quote is mandatory

**Status:** Accepted  
**Context:** KPIs appear in HTML, memory, GPT pack, and correspondence. Legacy PMS denominators and pre-PRISM captures persist in archived docs.  
**Decision:** No agent or human may quote capture %, GPS, BVP mix, or headline figures without green `01_data/derived/_verification_report.json` → `01_data/derived/metrics_snapshot.json` → [FACTS.md](FACTS.md). Formulas: `03_analytics/Isuzu/prism/docs/metric_dictionary.md`.  
**Alternatives considered:** Trust memory or GPT pack as KPI source (rejected).  
**Consequences:** Pipeline changes require `isze-verify-pipeline` skill or `run_pipeline_and_verify.ps1` before citing numbers. Memory and `08_gpt/` are views — never override KPIs.  
**Docs updated:** [AGENTS.md](AGENTS.md), [INDEX.md](INDEX.md).

---

## 2026-06-13 — 01_data/derived is the quantitative spine

**Status:** Accepted  
**Context:** Multiple UIs (PRISM, Evidence, Dash, HTML) and JSON builders consume analytics outputs. A single derived layer prevents divergent KPI definitions.  
**Decision:** `01_data/derived/` (CSVs, parquet, verification artifacts) is the **quantitative spine**. All UIs read derived outputs; UI choice is presentation only (`00_docs/UI_STACK.md`).  
**Alternatives considered:** Per-UI derived caches (rejected — drift risk).  
**Consequences:** Build scripts write to `01_data/derived/`; dashboard JSON in `01_data/dashboards/`; HTML reads JSON via deploy compatibility paths.  
**Docs updated:** [00_docs/UI_STACK.md](00_docs/UI_STACK.md), [03_analytics/Isuzu/prism/ARCHITECTURE.md](03_analytics/Isuzu/prism/ARCHITECTURE.md).

---

## 2026-06-13 — paths.yaml is the folder contract

**Status:** Accepted  
**Context:** Pre-reorg layout used inconsistent names (`Data/`, `Projects/`, `Tools/`, `memory/`). Hardcoded paths broke after reorg.  
**Decision:** [`paths.yaml`](paths.yaml) at ISZE root is the **folder contract**. PRISM reads via `config.py`; non-PRISM Python uses `04_tools/_shared/paths.py` or `04_tools/workspace/isze_paths.py`; PowerShell uses `04_tools/workspace/isze_root.ps1`. Use `$env:ISZE_ROOT` + numbered folders in new docs and skills.  
**Alternatives considered:** Environment-only path config (rejected — not self-documenting in repo).  
**Consequences:** New folders require `paths.yaml` update + `INDEX.md` + `CHANGELOG.md` entry.  
**Docs updated:** [paths.yaml](paths.yaml), [INDEX.md](INDEX.md), [CHANGELOG.md](CHANGELOG.md).

---

## 2026-06-13 — Numbered folder layout is canonical

**Status:** Accepted  
**Context:** 2026-06-13 workspace reorg consolidated top-level sprawl into numbered folders (`00_docs/` … `09_meetings/`, `90_archive/`, `91_legacy/`).  
**Decision:** Numbered folders are the **canonical local layout**. Legacy names (`Data/`, `Dashboards/`, `Projects/`, `Tools/`, `memory/`, `UIO/`, `GPT_Enterprise/`) are deprecated for local edits; deploy-side `Data/` remains a compatibility exception (see above).  
**Alternatives considered:** Keep semantic names without numbers (rejected — sort order and agent routing benefit).  
**Consequences:** Tier-1 docs, skills, and scripts use numbered paths. Path consolidation Batches 1–3 completed 2026-06-13.  
**Docs updated:** [INDEX.md](INDEX.md), [CHANGELOG.md](CHANGELOG.md), audit-export path-consolidation reports.

---

## 2026-06-13 — ISZE remains local-first file-based analytics monolith

**Status:** Accepted  
**Context:** ISZE is a solo-operator analytics workspace: Excel Power Query → parquet → PRISM Python → derived CSVs → HTML/PRISM/Evidence. No central database or multi-tenant service.  
**Decision:** ISZE stays a **local-first, file-based analytics monolith** on Jerome's machine. GitHub Pages publishes selected HTML/JSON; scheduled Claude jobs live outside the repo under `Documents\Claude\Scheduled\`.  
**Alternatives considered:** Cloud warehouse + BI tool (deferred); full git monorepo (open — see documentation-rebuild-plan open questions).  
**Consequences:** Monthly refresh is file-copy + script driven. Automation register indexes external scheduled skills. Raw billing never leaves `01_data/raw/sales/` into chat or GPT.  
**Docs updated:** [00_docs/REFERENCE.md](00_docs/REFERENCE.md), [01_data/DATA_MANIFEST.md](01_data/DATA_MANIFEST.md).

---

## 2026-06-13 — Primary external UI is HTML (GitHub Pages)

**Status:** Accepted  
**Source:** [00_docs/UI_STACK.md](00_docs/UI_STACK.md)  
**Decision:** Static HTML (`02_dashboards/` → sync → GitHub Pages) is the default external share surface. PRISM is day-to-day analysis; Evidence is internal SQL boards; Dash is sandbox only.  
**Consequences:** Do not rebuild the same KPI in HTML and Evidence unless HTML is the published export of that view.

---

## 2026-06-02 — PMS service frequency 0.5/yr (not 1.5)

**Status:** Accepted  
**Source:** `03_analytics/Isuzu/prism/docs/metric_dictionary.md`, `ARCHITECTURE.md`  
**Decision:** PMS expected-quantity denominator uses **0.5 services/year** per UIO, not legacy 1.5× multiplier.  
**Consequences:** Do not cite legacy single-PN / 1.5×UIO denominators from old HTML or `91_legacy/` without PRISM check.

---

## 2026-07-16 — INBOX dump-then-sort + `01_data/` root-clean contract

**Status:** Accepted
**Source:** `01_data/DATA_MANIFEST.md` §0, `INDEX.md`, `00_docs/CLAUDE_DESKTOP_ONBOARDING.md`
**Decision:** All new/unsorted data files land in `01_data/90_INBOX/` first, then get sorted into the numbered topic folder (DATA_MANIFEST §1). The root of `01_data/` is reserved for script-wired working files (§3) + docs — it is not a drop zone. Duplicates: **keep newest as canonical, archive older** to `92_archive/`.
**Consequences:** A non-empty `90_INBOX/` = "sorting owed." Loose files appearing in `01_data/` root are treated as a bug to re-file. Both Cursor and Claude Desktop boot from `INDEX.md` + maps so neither "loses" relocated files.

---

## 2026-07-16 — GitHub upload token moved to environment variable

**Status:** Accepted (⚠ action required: revoke old PAT)
**Source:** `04_tools/github_upload/upload_gps_data.py`, `upload_ids_data.py`
**Decision:** The upload scripts no longer hardcode a GitHub PAT; they read `$ISZE_GH_TOKEN` and exit with instructions if unset. Scripts moved from ISZE root to `04_tools/github_upload/`.
**Consequences:** Set `setx ISZE_GH_TOKEN "ghp_…"` once. The previously hardcoded token (`ghp_5Ar8…`, plaintext on disk) must be **revoked in GitHub** — treat as exposed. Not git-tracked, so not in commit history.

---

## 2026-07-14 — Autodoc/Oscaro retired from scraper health check

**Status:** Accepted  
**Source:** `04_tools/autodoc_scraper/_HANDOFF_BUNDLE/README.md`, `refresh_and_check_drift.py`, `manual_review_required.md` Item 6  
**Decision:** Autodoc EU/DE and Oscaro are **permanently Cloudflare-blocked** (stealth retry confirmed). Drop them from `isze-scraper-healthcheck-autofix` scope and retire `autodoc-monthly-refresh`. Competitive pricing is covered by KS, Tranzparts, TMC, Mekonomen, Auto365 via `refresh_and_check_drift.py`.  
**Consequences:** Health check monitors Tender + competitive-pricing pipeline only. `autodoc_results.csv` is frozen reference data.  
**Docs updated:** `00_docs/AUTOMATION_REGISTER.md`, `00_docs/roadmaps/scrapers.md`, `Documents/Claude/Scheduled/isze-scraper-healthcheck-autofix/SKILL.md`, `autodoc-monthly-refresh/SKILL.md`.

---

## 2026-07-14 — Task Scheduler XMLs for tender + competitive pricing refresh

**Status:** Accepted (XML patched/created; **Jerome must re-import in Task Scheduler**)  
**Source:** `proposed_patch.diff` Hunk 1, `manual_review_required.md` Items 1 and 5  
**Decision:** Fix dead post-reorg path in `ISZE_TenderMonitor_WeeklyTask.xml`. Add `ISZE_ScraperRefresh_WeeklyTask.xml` for weekly `run_refresh_scheduled.bat` (Sun 21:00, before health check).  
**Consequences:** Tender data stale since 2026-05-29 until task re-imported and run once. KS/Mekonomen stale until refresh task imported.  
**Docs updated:** `00_docs/ISZE_ROADMAP.md`, `00_docs/roadmaps/scrapers.md`, `00_docs/AUTOMATION_REGISTER.md`.

---

## Open — ISZE_Dashboard merge timeline

**Status:** Open  
**Source:** [00_docs/UI_STACK.md](00_docs/UI_STACK.md), [00_docs/ISZE_Cleanup_Plan.md](00_docs/ISZE_Cleanup_Plan.md)  
**Question:** Timeline to fold legacy Streamlit ops sandbox into PRISM, or keep indefinitely?

---

## Open — latest_weekly_brief.txt publish target

**Status:** Open  
**Source:** audit-export `scheduled-path-fix-report.md`  
**Question:** Internal `05_memory/briefs/latest_weekly_brief.txt` vs disabled output vs deploy path? Writing to `07_deploy/` would publish internal intel to GitHub Pages.

---

## 2026-07-14 — PMS pilot Success Criteria retired; no replacement target set

**Status:** Accepted
**Context:** The May 2026 Pilot Success Criteria doc locked a CY2025 oil-filter
capture baseline of 17.3% (DVLA) using a flat 1.5 svc/yr assumption and a
single-PN scope. Model B (adopted 2026-07-02) recomputes the same CY2025 year
at 35.1% using IML's schedule-derived 1.25×/yr frequency and a corrected
multi-PN genuine oil-filter set. Both numbers were live simultaneously,
creating a same-year, same-data discrepancy risk with IML/ITUK.
**Decision:** Success Criteria baseline superseded — CY2025 oil-filter
capture is 35.1% (DVLA) under Model B. Jerome declined to set a new formal
Tier-1/Tier-2 numeric target (no general target) — this is a deliberate
scope decision, not an open item.
**Alternatives considered:** Option A (44.6%, relative-ambition-preserving)
and Option B (11,393 units, absolute-ask-preserving) — both drafted in
`05_memory/briefs/PMS_Baseline_Reconciliation_2026-07.md`, neither adopted.
Keeping the two baseline documents on separate methodologies was rejected
(same-year comparison risk with IML/ITUK).
**Consequences:** `91_legacy/.../ISZE_ITUK_PMS_Pilot_Success_Criteria.md`
marked superseded, no replacement numeric target. Pilot tracked on Model B
methodology without a go/no-go percentage threshold.
**Docs updated:** `05_memory/projects/pms-coverage.md`,
`05_memory/briefs/PMS_Baseline_Reconciliation_2026-07.md`.

---

## 2026-07-14 — Canonical price file confirmed: 164k-row classified file, not the 674k-row full file

**Status:** Accepted
**Context:** Two files with the same "current price list" role coexisted since 16 June
2026: `01_data/01_Pricing/IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx`
(164,381 rows, mod 2026-04-15, taxonomy-classified) and `01_data/01_Pricing/Price file
2026_full.xlsx` (674,119 rows, mod 2026-06-16, raw Base price/Class/Source/FOB/GM columns,
no taxonomy). Neither had been reconciled; one spot-checked PN matched between them but the
full row-count gap was never explained.
**Decision:** The 164k-row classified file is canonical — these are the active parts.
`Price file 2026_full.xlsx` is not used for pricing/basket work going forward.
**Consequences:** `pricing-basket-2026.md` updated to name the canonical file explicitly.
The 674k file is left in place (not deleted, not moved) but should not be opened for
pricing figures — if it turns out to be needed for something else, that's a separate call.
**Docs updated:** `05_memory/projects/pricing-basket-2026.md`.

---

## 2026-07-14 — UK Find a Tender 429s: lengthen backoff instead of API key or accepting partial coverage

**Status:** Accepted
**Context:** `tender_scraper_v3.py`'s UK Find a Tender fetch intermittently gets HTTP 429
(rate limited) — 20 results in one run, 0 in another — after exhausting a 4-retry,
5→10→15→20s backoff. Contracts Finder (the lower-value UK source) is unaffected. Three
options were on the table: longer backoff, register a free FaT API key, or accept
CF-only coverage as a permanent partial loss.
**Decision:** Longer backoff. `get_with_retry`/`post_with_retry` now use 6 retries on a
30→60→90→120→180→240s schedule (was 4 retries, 5→10→15→20s).
**Consequences:** A run that hits 429 repeatedly can take several extra minutes to
finish. No new dependency (API key) introduced. If this still isn't reliable enough
after a few weekly runs, the API-key option is still on the table.
**Docs updated:** `04_tools/manual_review_required.md` Item 4,
`04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py`.
