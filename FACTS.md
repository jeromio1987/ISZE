# ISZE — Single Facts Sheet

**Role:** This is the **one authoritative source** for ISZE headline figures. When a number here conflicts with anything in a deck, email, GPT knowledge file, or memory note, **this file wins** — fix the other copy, not this one.

**Last verified:** 2026-06-10 (re-synced to pipeline after 2026-06-02 line_type classification fix)
**Drift enforcement:** `03_analytics\Isuzu\prism\scripts\verify_facts_drift.py` checks this file's headline figures (pinned in `03_analytics\Isuzu\prism\data\facts_anchor.yaml`) against `01_data\derived\metrics_snapshot.json` on every run. When the pipeline legitimately changes a number, update this file AND the anchor together.
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
| PMS capture data | `01_data\derived\pms_capture_by_db_year.csv` |
| Genuine/BVP authoritative split | `01_data\derived\genuine_bvp_crossref.csv` |
| BVP mix | `01_data\derived\mix_genuine_bvp_pms.csv` |
| GPS spend per unit | `01_data\derived\gps_spu_by_distributor.csv` |
| **Sign-off** | green run of `03_analytics\Isuzu\prism\scripts\run_pipeline_and_verify.ps1` → `01_data\derived\_verification_report.md` shows **0 fail** |

Last green verify: **96 pass / 0 fail, 2026-06-04**.
Headline metrics machine-readable: `01_data\derived\metrics_snapshot.json` (build: `03_analytics\Isuzu\prism\scripts\build_metrics_snapshot.py`).

---

## 1. ITUK oil-filter capture — the dispute anchor

Source: `pms_capture_by_db_year.csv`, rebuilt 2026-06-04 (verify 96/0) after the
2026-06-02 line_type classification fix — actuals/rates moved up vs the 2026-05-22
table (genuine PNs previously mislabelled BVP; capture PN set realigned to crossref).
Inputs (constant): UIO **22,389** (DVLA Mar 2026) · 0.5 svc/yr (N75) · 70% addressable → expected oil-filter qty **7,836.1/yr**.

| Year | Actual total | Uncapped | Total capture (cap 100%) | Genuine | BVP | Revenue (total) |
|------|-------------|----------|--------------------------|---------|-----|-----------------|
| 2023 | 17,009 | 217% | **100%** | 97% | 120% | €124,485 |
| 2024 | 9,475 | 121% | **100%** | **89%** | 31% | €58,819 |
| 2025 | 12,705 | 162% | **100%** | **120%** | 42% | €84,779 |

**The story is mix (genuine vs BVP), NOT a capture deficit.** ITUK already saturates N75 oil-filter demand on the combined line. 2025 uses 2024 fleet as proxy (flag D).
⚠ External-use caution: uncapped totals far above 100% reflect actuals beyond the
N75-only denominator (multi-segment + cross-OEM PNs). Quote the capped figure, or
use an N75-fitment-scoped variant, when this leaves the building.
Superseded (2026-05-22 pre-fix): 13,214/169%/64%/105% · 8,004/102%/79%/23% · 11,074/141%/103%/38% — do not quote.

## 2. Capture method constants

| Scope | svc/yr | addressable | wear factor (brake) |
|-------|--------|-------------|---------------------|
| N75 (ITUK, UTI) | 0.5 | 70% | 0.5 |
| LCV (IUK, UMI) | 1.0 | 70% | 0.5 |
| N35 blend | 0.75 | 70% | 0.5 |

Capture = `actual_qty ÷ expected_qty` (CSV uncapped; headline tiles cap at 100%). Capture >100% on `total` is valid (multi-segment / cross-OEM sales) — do not strip it.

## 3. BVP mix / GPS definitions

- `bvp_share_units` = bvp_qty ÷ (genuine_qty + bvp_qty); `bvp_share_eur` analogous. BVP has **no** capture rate.
- GPS `spend_per_unit_eur` = net parts sales ÷ uio_units. Traffic light: green ≥ €150, amber €50–150, red < €50.

## 4. Revenue base (sales_fact, 2026-05-28)

| Figure | Value | Note |
|--------|-------|------|
| Raw `sales_fact.parquet` total | €97,429,989 | 434,858 rows; includes internal/excluded codes |
| GPS-facing, all lines | €95.68M | after distributor exclusion (snapshot 2026-06-10) |
| GPS-facing, parts only | **€94.26M** | use this as the parts base (snapshot 2026-06-10; prior €94.55M was the 2026-05-28 cut) |

Non-part lines now excluded: TRANSPORT, REBATE, LATE PAYMENT INTEREST (€1.14M combined).

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

- **C — interval-aware capture (partial):** expected demand uses a flat service rate; **air-filter capture is artificially deflated and capture rates are NOT cross-category comparable.** Air vs oil interval ratio still needed from IML.
- **H — returns/credits (verify):** zero negative rows in sales_fact; confirm returns are pre-netted before treating revenue as final.
- **FY2025 trap:** ISZE FY = Apr–Mar. FY2025 (Apr 2025–Mar 2026) needs data through 31 Mar 2026 to be complete; CY2025 is complete. Don't publish a partial FY as full-year.

---

## Change log
- **2026-06-10** — §1 dispute-anchor table re-synced to pipeline (verify 96/0, 2026-06-04) after the 2026-06-02 line_type classification fix; pre-fix figures moved to "superseded — do not quote". §4 parts base €94.55M → €94.26M (current snapshot; line_kind tagging at load). Drift enforcement added: `facts_anchor.yaml` + `verify_facts_drift.py` + `metrics_snapshot.json`. ⚠ `01_data\gpt_safe\` exports still carry pre-fix numbers — re-export required.
- **2026-06-07** — created. Seeded from `metric_dictionary.md` (verify 2026-05-22) and `DATA_INTEGRITY_FLAGS_2026-05-28.md`.
