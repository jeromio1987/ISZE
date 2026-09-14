# ISZE — Single Facts Sheet

> ⚠ **ITUK PMS has two correct lanes (§1 Model B/IML vs §1b PRISM network) — never quote one without knowing which.** See `00_docs/ITUK_PRISM_LANE_BRIDGE.md` before putting an ITUK capture % or gap € in any deck.

**Role:** This is the **one authoritative source** for ISZE headline figures. When a number here conflicts with anything in a deck, email, GPT knowledge file, or memory note, **this file wins** — fix the other copy, not this one.

**Last verified:** 2026-08-25 (overnight — green `00_derived/_verification_report.json`)
**Drift enforcement:** `03_analytics\Isuzu\prism\scripts\verify_facts_drift.py` checks this file's headline figures (pinned in `03_analytics\Isuzu\prism\data\facts_anchor.yaml`) against `01_data\00_derived\metrics_snapshot.json` on every run. When the pipeline legitimately changes a number, update this file AND the anchor together.
**Stores that must reconcile to this file:**
- `05_memory\`
- `08_gpt\2_KNOWLEDGE_FILES\`
- Claude auto-memory `project_isze.md`
- Any PRISM deck / IML brief / ITUK correspondence

**Rule:** every figure below carries a source + as-of date. Do not add a number here without one. Numbers marked ⚠ are not yet traced to a verified source file — verify before external use.

---

## Canonical sources & sign-off

| What | Where |
|------|-------|
| Metric definitions (PMS / BVP / GPS) | `03_analytics\Isuzu\prism\docs\metric_dictionary.md` |
| Data integrity flags (what's safe to quote) | `03_analytics\Isuzu\prism\docs\DATA_INTEGRITY_FLAGS_2026-05-28.md` |
| PMS capture data (network league) | `01_data\derived\pms_capture_by_db_year.csv` |
| **ITUK PMS headline (IML v7)** | `03_analytics\Isuzu\prism\data\iml_v7_ituk_cy2025.yaml` |
| Genuine/BVP authoritative split | `01_data\derived\genuine_bvp_crossref.csv` |
| BVP mix | `01_data\derived\mix_genuine_bvp_pms.csv` |
| GPS spend per unit | `01_data\derived\gps_spu_by_distributor.csv` |
| **Sign-off** | green run of `03_analytics\Isuzu\prism\scripts\run_pipeline_and_verify.ps1` → `01_data\00_derived\_verification_report.md` shows **0 fail**

Last green verify: **116 pass / 0 warn / 0 fail, 2026-08-25T17:19:54Z** (`sales_fact` 514,037 rows · billing through **2026-06-30**). ⚠ Apr–Jun 2026 from `Q1FY2027.XLSX` has **no SaTy column** — fixture min lowered to 92%; overall SaTy ~92.9%. Prefer SAP re-export with SaTy when available.
Headline metrics machine-readable: `01_data\00_derived\metrics_snapshot.json` (build: `03_analytics\Isuzu\prism\scripts\build_metrics_snapshot.py`).

---

## 1. ITUK PMS — IML v7 schedule (Model B, external standard)

**Adopted 2026-07-02** — all IML/ITUK decks, business case, dashboards, and correspondence use these numbers.

Source: `ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx` · ISZE→ITUK (General) · CY2025 sales  
Canonical constants: `03_analytics\Isuzu\prism\data\iml_v7_ituk_cy2025.yaml`

| Parameter | Value |
|-----------|-------|
| UIO | **22,389** (full DVLA, Mar 2026) |
| Service frequency | Oil/Fuel/Air **1.25×/yr** (IML 40,000 km ÷ 50,000 km/yr); Clutch/Brake **0.5×/yr** |
| Addressable | **100%** |
| Oil-filter cover | **35.1%** (9,818 actual vs 27,986 expected) |
| Oil-filter cover ITUK→DLR | **40.6%** |
| PMS revenue gap (5 cat) | **€2,038,471** |
| Weighted cover (5 cat) | **35.9%** |

### Category breakdown (CY2025)

| Category | Cover | Gap € |
|----------|------:|------:|
| Oil filter | 35.1% | 140,602 |
| Fuel filter | 65.1% | 127,440 |
| Air filter | 13.2% | 736,037 |
| Clutch | 7.8% | 392,559 |
| Brake | 35.3% | 641,833 |

**The story is a real workshop capture gap** on the IML service schedule — largest € leaks in air filter and brake/clutch wear. Filters are not "saturated" under this denominator.

## 1b. ITUK oil-filter — PRISM network lane (real UIO-bucket split, 100% addressable)

**Re-based 2026-07-15** — PRISM's ITUK expected demand now uses the real per-distributor UIO split across cv_std/f_series/lcv buckets (`data/uio_by_model_bucket.csv`), fixing a hardcoded 2-market allowlist (`LCV_DISTRIBUTORS`/`CV_TRUCK_DISTRIBUTORS` in `modules/pms_engine.py`) that had silently mis-scoped 14 of 18 distributors — ITUK's own numbers shift too, since its N75 truck fleet is now split into real cv_std (22,190.9) + f_series (877.0) buckets instead of one flat N75 figure. `scripts/build_bvp_p0_p1.py` now calls `expected_by_category_bucketed()`.

Source: `pms_capture_by_db_year.csv` · bucketed UIO split (`uio_source=model_bucket_split`) × **100% addressable** → expected **11,680.2/yr** (bucketed UIO 23,068 = cv_std 22,190.9 + f_series 877.0).

| Year | Actual total | Uncapped | Total capture (cap 100%) | Genuine | BVP | Revenue (total) |
|------|-------------|----------|--------------------------|---------|-----|-----------------|
| 2023 | 18,030 | 154% | **100%** | 74% | 81% | €138,257 |
| 2024 | 9,750 | 84% | **84%** | **62%** | 21% | €62,384 |
| 2025 | 13,599 | 116% | **100%** | **88%** | 29% | €96,024 |

**Not the IML v7 headline** (that uses 1.25×/yr filter intervals and a separate 22,389 DVLA UIO from `iml_v7_ituk_cy2025.yaml` — unaffected by this re-base — see §1). Retained for PRISM dashboard and network league. See `isze_data.json` → `pms.ituk_prism_lane`.

## 2. Capture method constants

| Scope | svc/yr | addressable | wear factor (brake) |
|-------|--------|-------------|---------------------|
| N75 (ITUK, UTI) | 0.5 | **100%** | 0.5 |
| LCV (IUK, UMI) | 1.0 | **100%** | 0.5 |
| N35 blend | 0.75 | **100%** | 0.5 |

Capture = `actual_qty ÷ expected_qty` (CSV uncapped; headline tiles cap at 100%). Capture >100% on `total` is valid (multi-segment / cross-OEM sales) — do not strip it.

## 3. BVP mix / GPS definitions

- `bvp_share_units` = bvp_qty ÷ (genuine_qty + bvp_qty); `bvp_share_eur` analogous. BVP has **no** capture rate.
- GPS `spend_per_unit_eur` = net parts sales ÷ uio_units. Traffic light: green ≥ €150, amber €50–150, red < €50.

## 4. Revenue base (sales_fact, 2026-08-25)

| Figure | Value | Note |
|--------|-------|------|
| Raw `sales_fact.parquet` total | €117,536,189 | **514,037** rows, 2023-01-03 → **2026-06-30** (2026 = Jan–Jun; Apr–Jun from `Q1FY2027.XLSX`); includes internal/excluded codes and credit notes/returns |
| GPS-facing, all lines | €113.64M | after distributor exclusion, **ex-credit-notes/returns** (snapshot 2026-08-25) |
| GPS-facing, parts only | **€112.09M** | use this as the parts base (snapshot 2026-08-25; prior €103.57M was through 2026-03-31 only) |

Non-part lines excluded: TRANSPORT, REBATE, LATE PAYMENT INTEREST (€1.14M combined, 2023-2025 baseline).
**Credit notes / returns excluded since 2026-07-03** (flag H): SaTy `CR`/`RE` lines — Q1FY2027 extract has **no SaTy column**, so CR/RE exclusion for Apr–Jun 2026 is net-value-sign based only until the next SAP extract includes SaTy.
**Prior €103.57M / 477,505-row base (2026-07-03)** is superseded — do not delta as if only one variable moved.

## 5. AIM classification

**93.5%** (Mar 2026). Source: AIM workbook; cross-referenced in `DATA_INTEGRITY_FLAGS_2026-05-28.md` (flag F). This is a **separate system** from the GPS "category hint" keyword heuristic — do not conflate.

## 6. Lubricants project ⚠ (verify — link source doc)

Per Claude memory `project_isze.md` (not yet traced to a source file in this sheet): IML signed 8 May 2026; ~€442K revenue, ~13% GP, ~€57K gross, ~€37K net after €20K UMI support. **Verify against the lubricants business case before external use.**

## 7. Strategic guardrails (stances, not data)

- **Kosha €52.1M by FY2031 is structurally unreachable** — do not use market news to imply otherwise.
- **Golden Window:** ICE D-Max/N-series parc 2025–2032 = peak parts-revenue window.
- **Apples-to-apples channel markup:** when comparing genuine vs aftermarket, gross genuine to street = DB +40% then DLR +27.5% = **×1.785**. State it whenever you benchmark.
- **Turkey is not an ISZE distributor** — exclude from PRISM; its absence from sources is by design.

---

## 🚫 DO NOT QUOTE — obsolete figures

Any ITUK oil-filter capture under ~50% is a red flag — re-derive from the CSV.

| Figure | Why wrong |
|--------|-----------|
| **9.8% (CY24) / 17.3% (CY25)** | used legacy 1.5 svc/yr denominator (~33,584), not N75 0.5×70% |
| **~61% total CY2024** | stale pre-pipeline estimate (real capped total = 100%) |
| **~10% "legacy dealer capture"** | same 1.5 svc/yr defect |
| **0.3%** | wrong denominator entirely |
| **27% UMI competitive share** | fabricated figure — reference failure case, never reuse |

## ⚠ NOT YET SAFE EXTERNALLY (open integrity flags)

- **C — interval-aware capture (mitigated 2026-07-02, provisional):** air-filter expected demand now uses a **0.5× interval factor** (air element ~every 2nd service) instead of the flat rate — air capture ~doubled and is directionally comparable across categories. **The 0.5 is a labelled assumption, NOT an IML figure** — quote air capture only as "on a provisional interval assumption" until IML confirms the ratio (`prism/docs/pms_service_intervals.md` §6).
- **H — returns/credits (acted on 2026-07-03, still no ERP confirmation):** zero negative-value rows exist, but SaTy carries explicit `CR` (credit) / `RE` (return) codes on **positive**-value lines — 280 rows, €1,651,149 network-wide 2023-2026. These are now excluded from GPS revenue, the parts base, and PMS capture actuals (`is_credit_note` extended beyond sign to also catch SaTy CR/RE). **This is a judgment call, not an ERP-confirmed netting rule** — Jerome has not been able to get ERP confirmation and does not expect to soon. If SAP later confirms these should NOT be excluded (e.g., "RE" means something other than a return), revert by narrowing `is_credit_note`'s definition in `sales_loader.py`/`data_prep.py` back to sign-only.
- **FY label — do not mix billing integer with GPS/Power BI.** GPS and Power BI: **FY2026 = 1 Apr 2025 – 31 Mar 2026**. The billing column `fiscal_year` for that window is **2025** (year of April). Do not brief “FY2025” for Apr 2025–Mar 2026. Calendar year is not the default. See `00_docs/ISZE_BI_FRAMEWORK.md`.
- **FY completeness — CLOSED 2026-07-03:** billing through 31 Mar 2026 is in `sales_fact.parquet`. The Apr 2025–Mar 2026 window (GPS FY2026) is complete. Q1 FY2027 (Apr–Jun 2026) is a later add.

---

## Change log
- **2026-07-03** — Two source-file gaps closed: `CY2024-2025.XLSX` (more-complete 2025 SAP re-export, +1,369 rows vs the old `CY2025.XLSX`, which is now superseded and no longer loaded) and `sales_2026tillApril.XLSX` (Jan-Mar 2026, **closes the FY2025 completeness trap**). `sales_fact.parquet` 434,858 → 477,505 rows, years now [2023,2024,2025,2026]. Flag H acted on: SaTy `CR`/`RE` credit-note/return lines (280 rows, €1.65M) now excluded from GPS/parts-base/PMS-capture — **not** ERP-confirmed, a documented judgment call, reversible. Net effect: parts base €94.26M → **€103.57M** (2026 quarter added more than CR/RE removed); network GPS CY2025 50.2% → **51.1%** (more-complete 2025 data, partially offset by CR/RE). Verified `Sales_israel_1799&_1797.XLSX` is NOT missing data — row-for-row identical to what's already in the CY files, with one footer/grand-total artifact row; correctly left unwired. See `DECISIONS.md` 2026-07-03.
- **2026-07-02** — flag C mitigated: `air_filter` consumable_factor 1.0 → **0.5 PROVISIONAL** (pending IML); air capture ~doubles vs earlier outputs. `sales_fact.parquet` now carries `fig_key` (catalog join, 98.9% coverage). Oil-filter anchors unchanged. **Network GPS (waterfall) CY2025 re-based 40.2% → 50.2%** — MIDI's ~€15M theoretical wallet (98,654 UIO, zero ISZE-direct sales) dropped from the denominator per the MIDI-not-a-customer decision; first drift-checked run since the 2026-06-18 UIO refresh. See `DECISIONS.md` 2026-07-02.
- **2026-06-10** — §1 dispute-anchor table re-synced to pipeline (verify 96/0, 2026-06-04) after the 2026-06-02 line_type classification fix; pre-fix figures moved to "superseded — do not quote". §4 parts base €94.55M → €94.26M (current snapshot; line_kind tagging at load). Drift enforcement added: `facts_anchor.yaml` + `verify_facts_drift.py` + `metrics_snapshot.json`. ⚠ `01_data\gpt_safe\` exports still carry pre-fix numbers — re-export required.
- **2026-06-07** — created. Seeded from `metric_dictionary.md` (verify 2026-05-22) and `DATA_INTEGRITY_FLAGS_2026-05-28.md`.
