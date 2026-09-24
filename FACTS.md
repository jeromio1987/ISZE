# ISZE — Single Facts Sheet

> ⚠ **ITUK PMS has two correct lanes (§1 Model B/IML vs §1b PRISM network) — never quote one without knowing which.** See `00_docs/ITUK_PRISM_LANE_BRIDGE.md` before putting an ITUK capture % or gap € in any deck.

**Role:** This is the **one authoritative source** for ISZE headline figures. When a number here conflicts with anything in a deck, email, GPT knowledge file, or memory note, **this file wins** — fix the other copy, not this one.

**Last verified:** 2026-09-24 (green `00_derived/_verification_report.json`, 164 pass / 1 warn / 0 fail; facts-drift aligned)
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

Last green verify: **153 pass / 1 warn / 0 fail, 2026-09-19T13:00:24Z** (`sales_fact` 514,037 rows · billing through **2026-06-30**). The single warning is the known historical gap in the Danish fleet series (DENMARK 2012–2013, left unfilled rather than filled). ⚠ Apr–Jun 2026 from `Q1FY2027.XLSX` has **no SaTy column** — fixture min lowered to 92%; overall SaTy ~92.9%. Prefer SAP re-export with SaTy when available.
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

Source: `pms_capture_by_db_year.csv` · bucketed UIO split (`uio_source=model_bucket_split`) × **100% addressable** → expected **17,285.6/yr** (bucketed UIO 23,068 = cv_std 22,190.9 + f_series 877.0; the cv_std rate is **0.5 × (1 + 0.5051) = 0.7526** visits a year because the ITUK N35 share runs the 20,000 km interval — rule in `modules/pms_capture_config.py` since 2026-09-19; F-series 0.667).

**Re-anchored 2026-09-24** — the figures below were on the 0.5 flat rate (expected 11,680.2) until this date. The pipeline had moved to the N35 interval rule on 2026-09-19 and FACTS had not followed; the drift gate flagged it on every run since 2026-09-22. **Any ITUK oil-filter capture quoted from the old table is superseded.**

| Year | Actual total | Uncapped | Total capture (cap 100%) | Genuine | BVP | Revenue (total) |
|------|-------------|----------|--------------------------|---------|-----|-----------------|
| 2023 | 18,030 | not stated as a rate | not stated as a rate | 50% | 54% | €138,257 |
| 2024 | 9,750 | 56% | **56%** | **42%** | 14% | €62,384 |
| 2025 | 13,599 | 79% | **79%** | **59%** | 19% | €96,024 |

**2023 is not given as a capture rate:** billed 18,030 exceeds the modelled 17,285.6, which says the fleet or interval basis is short for that year, not that capture beat demand. The machine anchor `ituk.oil_filter.2023.total.capture_uncapped_pct` still tracks the raw ratio for drift only; do not quote it.

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

## 4. Revenue base (sales_fact, 2026-09-20)

| Figure | Value | Note |
|--------|-------|------|
| Raw `sales_fact.parquet` total | €123,327,056 | **538,346** rows, 2023-01-03 → **2026-08-31** (2026 = Jan–Aug; Apr–Jun from `Q1FY2027.XLSX`, Jul–Aug from `CY2025till31082026.XLSX`); includes internal/excluded codes and credit notes/returns |
| GPS-facing, all lines | **€119,222,616** | after distributor exclusion, **ex-credit-notes/returns** (recomputed 2026-09-20) |
| GPS-facing, parts only | **€117,600,501** | use this as the parts base (recomputed 2026-09-20; prior €112,089,307 was through 2026-06-30 only) |

### 4.1 Parts base bridge — three published values, one method

`€103,573,715` / `€112,089,307` / `€117,600,501` are **the same series at three
cut-off dates**, not competing definitions. All three are reproduced by the pipeline:

| Step | € | Rows | Basis |
|------|---|------|-------|
| Parts base through **2026-03-31** | **103,573,715** | 465,343 | published 2026-07-03 |
| + 2026 Apr–Jun billing (`Q1FY2027.XLSX`, wired 2026-08-25) | +8,515,592 | 35,550 | |
| = Parts base through **2026-06-30** | **112,089,307** | 500,893 | published 2026-08-25 |
| + 2026 Jul–Aug billing (`CY2025till31082026.XLSX`, wired 2026-09-20) | +5,511,195 | 23,776 | Jul 2,959,698 + Aug 2,551,497 |
| = Parts base through **2026-08-31** | **117,600,501** | 524,669 | published 2026-09-20 |

**The 2026-09-20 move is a billing-horizon move and nothing else.** No fleet number, no
target-spend rate and no ceiling moved with it. The CY2025 rows of `wallet_waterfall.csv`
and the 55.7% coverage figure are **unchanged** — the coverage denominator is
vehicles-in-service × a target rate per truck and contains no billing at all, so a new
2026 billing month cannot move it. The ceiling rebuild is separately held by decision **D24**
(the Portugal/Malta light-vs-heavy truck shares) and was not run.

Both figures are now **derived, not recalled**: `sales.parts_base_eur` carries
`sales.parts_base_data_through`, and `sales.parts_base_through_prior_quarter_eur`
is the same method cut at the prior quarter end. A period movement therefore can
no longer be read as a method movement.

**Open check after the 2026-09-20 load — read this before the next publish.**
`lost_sales.billed_ties_to_parts_base` now fails: the lost-sales model still shows
€112,089,306.89 billed against a parts base of €117,600,501.42, a delta of exactly the
two new months. That model's billed figure was already stale by the same €5.51M **before**
this load (it stood at the 2026-06-30 cut while the base had moved to the live one), and
rebuilding it is not billing-only work: `lost_sales_model.csv` is built on
`wallet_waterfall.csv` and carries the ceiling at market level
(`ceilings_are_market_level=True`). It is therefore held with the ceiling under D24 and was
deliberately **not** rebuilt. Until D24 is answered, that one verification failure stands and
is a known, explained gap rather than a regression.

**Defect found and fixed 2026-09-17 (the €180,715 leak).** Between two
publications a third, undocumented movement occurred. On 2026-09-03
`sap_sold_to_mapping.csv` remapped four non-part entities from `UNMAPPED` to a new
code `NON_PARTS`, which was **not** in `EXCLUDED_CODES`. Nine rows / **€180,715.11**
(service fees, demurrage, e-credit — all CY2026) consequently entered the parts base
through the `line_kind == "part"` filter, lifting a live recompute to €112,270,022
against the published €112,089,307. Fixed in `data_prep.EXCLUDED_CODES` (+`NON_PARTS`)
and `sales_loader.NON_PART_LINE_KIND` (+ the four placeholder PNs). A fresh recompute
now lands on €112,089,307.0 exactly. CY2025 was unaffected — €0 of the leak fell in
2025 — so the GPS anchor held at 51.1% at that date (it moved later the same day for an
unrelated reason — see §5 entry dated 2026-09-17 on the N35 split).

Non-part lines excluded: TRANSPORT, REBATE, LATE PAYMENT INTEREST (€1.14M combined, 2023-2025 baseline); plus SERVICE, SERVICE FEE OUTSIDE EUROPE, COST DEMURRAGE, COMPENSATIONS SALE E-CREDIT (€180,715, CY2026 only).
**Credit notes / returns excluded since 2026-07-03** (flag H): SaTy `CR`/`RE` lines — Q1FY2027 extract has **no SaTy column**, so CR/RE exclusion for Apr–Jun 2026 is net-value-sign based only until the next SAP extract includes SaTy.
**Prior €103.57M / 477,505-row base (2026-07-03)** is the same method cut at 2026-03-31 — see the bridge in §4.1. Do not delta as if only one variable moved.

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
- **FY2025 trap — CLOSED 2026-07-03:** ISZE FY = Apr–Mar. FY2025 (Apr 2025–Mar 2026) needed data through 31 Mar 2026; `sales_2026tillApril.XLSX` (Jan 5–Mar 31 2026) now lands in `sales_fact.parquet`. FY2025 is complete — safe to report as a full fiscal year for the first time.

---

## Change log
- **2026-09-24** — **NMR ruled 5.5 t; Malta and Cyprus 3.5 t shares corrected to 0; FACTS re-anchored to the pipeline.**
  Jerome ruled `NMR` / `NMR85` onto the 5.5 t rung for the European N55 class on 2026-09-23 (DECISIONS.md;
  Isuzu Sales Deutschland data sheet NMR88L 5,500 kg). The Malta (0.369) and Cyprus (0.053) "3.5 t shares" in
  `uio_ld_n35_share.csv` were their NMR counts read as N35 (JP VIN register: zero NLR in either market) and are now
  **0**; their NMR sit on the 5.5 t rung (`uio_n55_share.csv`). The 2026-09-18 entry's "NMR88 is a 9.5 t truck" is
  retired — no source ever stated it. Pipeline re-run (all P0–P5 steps except the `sales_fact` rebuild, which the
  change does not touch): **verify 164 pass / 1 warn (Denmark 2012-13 workbook holes, pre-existing) / 0 fail**. Moved, and only in these two markets: 2025 target wallet
  **Malta €338,957 → €378,827** (GPS 60.9% → 54.5%), **Cyprus €671,394 → €676,267** (63.8% → 63.4%); network wallet
  €54,375,729 → **€54,420,472**, parts billed unchanged €30,756,771.61, **network GPS 56.56% → 56.52% (56.5%)**.
  PMS capture moved for Malta and Cyprus only (lower expected truck demand: the 3.5 t interval doubling no longer
  applies). Two anchors had been drifting since 2026-09-22 for reasons unrelated to this change and are re-anchored in
  the same pass: **ITUK oil-filter PRISM lane** (§1b, expected 11,680.2 → 17,285.6 under the 2026-09-19 N35 interval
  rule; 2025 capture now 79%) and **parts base through the prior quarter** (€103,573,715 → **€112,089,307**, the
  prior quarter end having rolled from 2026-03-31 to 2026-06-30 — both values were already in §4.1). Tonnage band
  files, both PMS pages and the modelled 5.5 t band rebuilt the same day; see
  `01_data/90_INBOX/TONNAGE_FINISH_REPORT_2026-09-23.md`.
- **2026-09-18** — **Warranty commercial datasets published, and a currency error in the same day's
  note corrected.** New: `01_data/00_derived/warranty_commercial/` — 13 CSVs plus a 13-sheet
  workbook, one file per commercial question with every market inside the file, regenerable from
  `01_data/91_build/build_warranty_commercial_datasets.py`; Excel pre-delivery check OK, issues=0.
  **The correction matters more than the folder.** The truck claim file's `CRNCY` column carries two
  tokens: **`EUR GBP` = pounds** (UK, 11,956 lines, the largest book in the file) and **`JPY EUR` =
  yen** (Italy, Spain, France, Switzerland and others). Summing that column raw mixes three
  currencies. Corrected truck figures: parts turnover **€4,655,881** (not €2,826,045), emissions
  **€2,838,570 = 61%** (not €1,819,033 = 64%), power steering gear **~€1.15M** (not €800,191). The
  D-Max figures in this change log were already normalised per line and are unaffected. Normalisation
  is now explicit and auditable: `warranty_cv_currency_audit.csv` carries local amount, EUR amount,
  the JPY-equivalent the file itself states, and the rate applied, for every market.
- **2026-09-18 (later)** — **Two N35 shares were read from the wrong file and two from a misread
  chassis code; corrected, and the whole share file audited against its own stated basis.** Every row
  of `uio_ld_n35_share.csv` was recomputed from the source it names. **IRELAND 0.063 → 0.3089** — the
  row said `simi_bands` but carried the JP VIN register figure (36/570); the SIMI parc basis is
  **464 of 1,502** at 2025 (SIMI registrations 2010-2025, scrap-adjusted), with the flow basis at
  663/1,963 = 0.3377 for reference. **BELGIUM 0.918 → 0.8571** (NLR 42 of 49, not 45). **PORTUGAL
  0.620 → 0.6899** (1,299 of 1,883 **N-series**; the old row divided by all 2,111 rows including 228
  F-series). **MALTA and CYPRUS → `unmeasured`, rates held**: both rested on reading **NMR88 as an
  N35**, but NMR88 is a 9.5 t truck and Cyprus holds zero 3.5 t in the register. *[Corrected 2026-09-24: NMR / NMR88 is the 5.5 t European N55 (ruled 2026-09-23, DECISIONS.md); no source ever stated 9.5 t. Malta and Cyprus 3.5 t shares are now 0, their NMR sit on the 5.5 t rung.]* GERMANY (153/697 =
  0.2195), GREECE (no 3.5 t), ITUK (live workbook 10,900/21,584) and UTI (zero NLR in 2,360 claim
  VINs) all confirmed sound. Expected-demand effect on the cv slice only: ITUK unchanged, **Ireland
  +6.5%**, Portugal +12.8%, Malta +4.9%, Belgium +0.5% — the whole-figure scaling bug did not
  reappear. Locked `wallet_waterfall.csv` **not** rebuilt; the computed effect would be Ireland
  €935,912 → €856,281, Portugal €2,446,187 → €2,377,877, network −0.46%. The stale
  `pms_capture_by_db_year.parquet` (1,176 rows behind the CSV) was re-synced. **Verifier 143 pass /
  0 warn / 0 fail**; Lost Sales page rebuilt and screenshot-read. Audit:
  `01_data/00_derived/n35_share_audit_20260918.csv`.
- **2026-09-18** — **The `LD` label split applied to every measured market; Israel confirmed
  unchanged.** *[Superseded later the same day for Ireland, Belgium and Portugal — see the entry
  above. The shares named in this entry as 6.3% / 91.8% / 62.0% are now 30.9% / 85.7% / 69.0%, and
  Malta and Cyprus are marked `unmeasured`.]* Yesterday's ITUK fix treated `LD` as one thing. It is not: the token means 6.5/7.5 t
  in Israel and 3.5 t in most of Europe, and both were priced at the N75 rate. `data_prep` now
  splits the row per market from `prism/data/uio_ld_n35_share.csv`, whose rows name their source —
  the workbook's own Helwig parc bands (Germany 22.0%), SIMI bands (Ireland 6.3%), the workbook's
  section 2.B read live (ITUK 50.5%), CV claim VINs plus the ministry table (Israel 0%), and the JP
  VIN register shipment mix elsewhere (Portugal 62.0%, Malta 36.9%, Belgium 91.8%, Cyprus 5.3%).
  Measured 2025E target-wallet effect: **Portugal ×0.801, Malta ×0.895, Ireland ×0.979,
  Belgium ×0.981, Germany ×0.982, Cyprus ×0.993.** **Israel's ceiling does not move** — the market
  operates no 3.5 t Isuzu truck (2,360 CV claim VINs: NPR75/FRR90/FSR90, zero NLR; the Ministry of
  Transport band table starts at 6.5–7.5 t), so €739 was already the right rate and the defect was
  the label. V20_SPEC's table had Germany and Malta at "0% — no change"; both were wrong. Also
  corrected: the JP VIN register took the number inside a chassis code as a tonnage, so NLR 3.5 t
  trucks read 8.5–8.8 t and both FRR90 (11–12 t) and FSR90 (13.5 t) read 9.0 t — rebuilt, the
  register now reads **19,545 t over 3,238 trucks (6.04 t average)** against 26,689 t / 8.24 t.
  PRISM suite 71 passed. Nothing published, no price moved.
- **2026-09-17** — **ITUK N35/N75 split applied; GPS anchor 51.1% → 55.7%.** ITUK's CV truck row
  in the UIO workbook is labelled a single `LD` line, and the GPS rate mapper priced all of it at
  the N75 rate (€739) when 10,900 of those trucks are N35 Grafter (€296). The workbook already
  carries the split in a sheet nothing read — `2. Vehicle Volume` section B ("ITUK UK Car Par[k]",
  sourced from `UIO.xlsx — ITUK sheet`) — and `data_prep._split_collapsed_ld_rows()` now reads it
  and emits explicit N35 / N75 rows before the mapper sees them. Effect: ITUK ceiling
  €17.18M → **€12.21M**, ITUK GPS **32.4% → 45.6%**, network wallet €60.22M → **€55.25M**,
  network GPS **51.1% → 55.7%**. **Only ITUK moved** — the other 17 markets have no N35 fleet and
  are byte-identical. This also converged the last of the two contradictory ITUK GPS percentages:
  the ceiling route now reads 45.6% against the upper-reference route's 47.0%, the residual being
  fleet vintage (2025E vs 2024), not method. Two further mapper defects fixed in the same change:
  an explicit `N35` row was being routed to the LCV D-Max rate (€250, the wrong vehicle class), and
  a fallback hardcoded the same unsourced €1,120 the docstring carried.
- **2026-09-17** — **Parts base bridge documented; €180,715 non-part leak fixed.** `€103.57M` (2026-07-03) and `€112.09M` (2026-08-25) are confirmed to be the *same method at two cut-off dates* (§4.1). Chasing that produced a live defect: on 2026-09-03 `sap_sold_to_mapping.csv` remapped four non-part entities (`SERVICE FEE OUTSIDE EUROPE`, `SERVICE`, `COST DEMURRAGE`, `COMPENSATIONS SALE E-CREDIT`) from `UNMAPPED` to a new code `NON_PARTS`, which was not in `EXCLUDED_CODES`; nine CY2026 rows / **€180,715.11** then entered the parts base through the `line_kind == "part"` filter. Fixed in `data_prep.EXCLUDED_CODES` (+`NON_PARTS`) and `sales_loader.NON_PART_LINE_KIND` (+ four placeholder PNs). Recompute now returns €112,089,307.0 exactly (was €112,270,022). Pipeline verify 116 pass / 0 warn / 0 fail; facts-drift ALIGNED. New derived keys `sales.parts_base_data_through` and `sales.parts_base_through_prior_quarter_eur` make the bridge machine-checkable. CY2025 untouched — €0 of the leak fell in 2025, so the 51.1% GPS anchor never moved.
- **2026-07-03** — Two source-file gaps closed: `CY2024-2025.XLSX` (more-complete 2025 SAP re-export, +1,369 rows vs the old `CY2025.XLSX`, which is now superseded and no longer loaded) and `sales_2026tillApril.XLSX` (Jan-Mar 2026, **closes the FY2025 completeness trap**). `sales_fact.parquet` 434,858 → 477,505 rows, years now [2023,2024,2025,2026]. Flag H acted on: SaTy `CR`/`RE` credit-note/return lines (280 rows, €1.65M) now excluded from GPS/parts-base/PMS-capture — **not** ERP-confirmed, a documented judgment call, reversible. Net effect: parts base €94.26M → **€103.57M** (2026 quarter added more than CR/RE removed); network GPS CY2025 50.2% → **51.1%** (more-complete 2025 data, partially offset by CR/RE). Verified `Sales_israel_1799&_1797.XLSX` is NOT missing data — row-for-row identical to what's already in the CY files, with one footer/grand-total artifact row; correctly left unwired. See `DECISIONS.md` 2026-07-03.
- **2026-07-02** — flag C mitigated: `air_filter` consumable_factor 1.0 → **0.5 PROVISIONAL** (pending IML); air capture ~doubles vs earlier outputs. `sales_fact.parquet` now carries `fig_key` (catalog join, 98.9% coverage). Oil-filter anchors unchanged. **Network GPS (waterfall) CY2025 re-based 40.2% → 50.2%** — MIDI's ~€15M theoretical wallet (98,654 UIO, zero ISZE-direct sales) dropped from the denominator per the MIDI-not-a-customer decision; first drift-checked run since the 2026-06-18 UIO refresh. See `DECISIONS.md` 2026-07-02.
- **2026-06-10** — §1 dispute-anchor table re-synced to pipeline (verify 96/0, 2026-06-04) after the 2026-06-02 line_type classification fix; pre-fix figures moved to "superseded — do not quote". §4 parts base €94.55M → €94.26M (current snapshot; line_kind tagging at load). Drift enforcement added: `facts_anchor.yaml` + `verify_facts_drift.py` + `metrics_snapshot.json`. ⚠ `01_data\gpt_safe\` exports still carry pre-fix numbers — re-export required.
- **2026-06-07** — created. Seeded from `metric_dictionary.md` (verify 2026-05-22) and `DATA_INTEGRITY_FLAGS_2026-05-28.md`.
