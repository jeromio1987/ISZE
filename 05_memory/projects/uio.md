# Project: UIO (Units In Operation) Tool

_Last validated: 2026-07-06 (v19 canonical — `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`)_

## Status: Active — **v19 canonical** · JSON extract `01_data/91_build/uio_2026.json` · Dashboard HTML v18 (rebuild pending)

## What
Excel + Python tool calculating Isuzu vehicle population in service (UIO) by country, distributor, model type.
Dual methodology:
- **IML backbone** (Hasegawa-style shipment × survival convolution) — used for every distributor except ITUK
- **ITUK exception** — actual SMMT/DVLA registered car park 2008–2024 + cohort × model-specific survival projection 2025–2030 (Niguri FY25/26–FY27/28 new registrations, flat 2,446/yr thereafter)
- **Russia excluded** from all calculations

## Files (CANONICAL)
- `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` — **canonical working file (v19)**
- `01_data/91_build/uio_2026.json` — distributor extract for slides/UTI (`extract_uio_warranty2.py`)
- `01_data/91_build/uio_v19_gps.json` — GPS max-spend package (`gps_v9_loaders.py`)

## v17 workbook structure (9 sheets)
1. **Cover** — scope, assumptions, FY→CY mapping, March 2026 build stamp
2. **1.UIO Overview** — main pivot: 40+ distributor × model-type rows × 1990–2030 columns. Row 2 Grand Total (SUMPRODUCT), row 3 Growth YoY, row 4 MIDI Filter toggle (B4 = "Include" / "Exclude MIDI"), row 5 MIDI contribution subtotal. **v17: U KING rows 22 (CV LD) and 24 (F-Series), cols AP-AU (2025-2030), now live-linked to sheet 4 Section C** (previously hardcoded v11-era numbers). Historical cols G-AO (1990-2024) unchanged.
3. **2. Vehicle Volume** — underlying volume data
4. **3. UIO Calculation** — roll-forward worksheet
5. **4. ITUK UIO Projection** — cohort × survival-rate model; Sections A (SMMT actuals) / B / C (2025–30 projection) / D (assumptions) / E (survival curves by model) / F (Niguri registrations)
6. **Charts** — Chart 1 (survival curve comparison), Chart 2 (ITUK registrations)
7. **Assumptions & Mapping** — 8 sections, 4 embedded charts
8. **Data Sources** — source file registry + distributor-to-source mapping + methodology notes
9. **Changelog** — v11→v17 audit trail

## Key figures — SUPERSEDED 2026-07-09, kept below for history only

The v17 (20 Apr 2026) table that used to be here, including the "−3.7% 2026F dip", is **wrong as of the current v19 workbook**. Changelog V18-16→V18-20 (2026-06-11) replaced the pure-decay 2026-2030 forecast with one driven by real IMIT/CV-plan new-registration inputs — the dip is gone, replaced by steady growth. See `06_uio/_CURRENT/README.md` (updated 2026-07-09) for the current, live-pulled Grand Total table (incl. and ex-MIDI) and the correct explanation. Do not use the old dip narrative externally.

Also flagged 2026-07-09: Sheet 1 B4 (MIDI toggle) is currently set to **"Include"**, not the policy default of "Exclude MIDI" — check before quoting the Grand Total raw off Sheet 1.

ITUK figures (22,389 → 23,068 → 24,173 → ... → 28,209) are unaffected and still correct — Sheet 4 "4. ITUK UIO Projection" has not been touched since v15/v17 (confirmed via Changelog), it just still carries an internal "V15" header, which is a labeling lag, not stale data.

<details><summary>Old v17 table (2026-04-20) — do not use, kept for traceability</summary>

| Year | UIO | YoY | MIDI contribution |
|------|-----|-----|-------------------|
| 2024 | 254,117 | +3.9% | 92,585 |
| 2025E | 260,449 | +2.5% | (unchanged) |
| 2026F | 250,718 | **−3.7%** | (unchanged) |
| 2027F | 253,228 | +1.0% | (unchanged) |
| 2028F | 256,011 | +1.1% | (unchanged) |
| 2029F | 259,165 | +1.2% | (unchanged) |
| 2030F | 262,559 | +1.3% | (unchanged) |

</details>

### ITUK car park (SMMT/DVLA actual, 2024)
- **Total: 22,389 vehicles** (re-confirmed in v12+ cohort model, matches memory from 15 Mar)
- Cohort breakout in Section A, sheet 4 (row 14 "Total ITUK")
- **ITUK UIO projection v17 (sheet 4 row 28):** 2025: 23,068 · 2026: **24,173** · 2027: **25,392** · 2028: **26,435** · 2029: **27,363** · 2030: **28,209**
- Pre-2008/2008/2009/2010 cohorts: **90% survival / 10% scrap — held flat every forecast year 2025–2030** (v17 fix; v16b formulas had broken INDEX(4:6,…) refs evaluating to 0 in 2026/2027 and no override at all in 2028–2030, silently dropping ~2,371 units from 2026 onwards)
- Survival curves: N35 & N75 from "Parts Sales vs Model Mix_attrition rate_ITUK.pptx"; N50/55 & N62/65 use N75 curve; F-series uses IML CV Advanced Economy

## Version history (disk vs promoted)
| Ver | Date | Key change |
|-----|------|------------|
| v9 | 2026-04-12 | Prior "canonical" per old memory — superseded |
| v10_ | 2026-04-12 | — |
| v11 | 2026-04-12 | MIDI toggle, SUMPRODUCT Grand Total (fixed +0.9–1.5% overstatement), Data Sources sheet, Changelog |
| v12 | 2026-04-14 | **ITUK step-function → cohort × survival model**; Sections E+F added; Niguri + PPTX sources ingested |
| v13 | 2026-04-14 | — |
| v14 | 2026-04-16 | — |
| v15 | 2026-04-16 | Owner-operator scrap bug fix (was ×9, corrected to ×0.9) |
| v15_2 | 2026-04-17 | — |
| v16 | 2026-04-17 | Chart 1 + Chart 2 corrections |
| v16b | 2026-04-17 | Chart 1 further fix (orange floor above N35/N75 at age 15+); Section E survival notes confirmed. **Bug carried over**: 90% override only in 2025 formulas; 2026/2027 had broken INDEX(4:6,…) refs; 2028–2030 had no override at all. File corrupted on disk (re-uploaded 20 Apr). |
| **v17** | **2026-04-20** | (1) 90% owner-operator override applied uniformly across 2025–2030 for Pre-2008/2008/2009/2010 cohorts — flat hold, no compounding. Broken INDEX(4:6,…) refs removed. (2) Sheet 1 U KING rows 22 (CV LD) + 24 (F-Series), cols AP-AU, converted from hardcoded v11-era values to live formulas linking sheet 4 Section C. (3) B17/B29 notes rewritten. Total: ~2,371 units restored 2026–2030 on sheet 4; Grand Total +1,914 to +2,400 across 2025–2030. |

## ITUK cohort model impact vs v11 step-function
- 2025: 21,154 (v11) → 23,068 (v12/v16b/v17 — same, 90% override already working in 2025)
- 2026: 24,559 (v11) → 21,803 (v16b, buggy) → **24,173 (v17 fixed)**
- 2027: 26,769 (v11) → 23,021 (v16b, buggy) → **25,392 (v17 fixed)**
- 2030: 32,587 (v11) → 25,839 (v16b, buggy) → **28,209 (v17 fixed)**
- v17 long-run is still ~14% below v11 flat step-function (28,209 vs 32,587 in 2030) — cohort model with ITUK-specific curves retires more vehicles; owner-operator override offsets only partially. This is the correct picture.

## Data sources (v17 — unchanged from v16b)
- IML calculation.xlsx — backbone (all countries 1990–2026)
- LCV UIO (November 2025)_EU_Study_Imit.xlsx — IMIT Thailand LCV survival + forecasts
- UIO.xlsx → ITUK sheet — SMMT/DVLA car park 2008–2024
- UIO.xlsx → scrap-adjusted 2025 (BE/CY/DE/DK/GR/IE/MT/PT)
- ISZE CV FY2025–FY2030 mid-term plan & 12RS.xlsx — ISZE new-sales forecast
- **Niguri FY25.26 Extract 20260413_ITUK.xlsx** — ITUK internal forecast (added v12)
- **Parts Sales vs Model Mix_attrition rate_ITUK.pptx** — N35/N75 attrition curves (added v12)

## Connections
→ Feeds PMS coverage project — capture sizing on the 22,389 DVLA base
→ Feeds Lubricants project (UIO × service interval = lube demand)
→ Feeds Action Plan KPIs (UIO = market size denominator)
→ Feeds AIM Opportunity Engine (Parc × Age Factor × Category Factor = Spend Index)

## Known open items
1. ✅ **MIDI toggle default** — Policy set May 2026: default = "Exclude MIDI" for ISZE KPI reporting. Include for lubricants/synergy analysis. Set manually in Excel B4 each session.
2. ✅ **2026F −3.7% dip** — explanation written in dashboard v17 changelog and README. Non-ITUK backbone roll-forward; ITUK +4.8% in same period.
3. **Israel 2027–30** extrapolation via trend CAGR from IML 2023–26 — IML only provides to 2026. Flag if Israel is ever debated in isolation.
4. ✅ **Dashboard rebuilt** — v17 HTML created May 2026 at `ISZE/Dashboards/ISUZU_UIO_Dashboard_2026_v17.html`
5. ✅ **File sprawl resolved** — v8–v16b archived to `ISZE/UIO/_Archive/`. Canonical structure in `_CURRENT/`, `_Scripts/`, `_SourceData/`.
6. **MIDI contribution (sheet 1 row 5)** not verified after v17 — SUMPRODUCT may still point at old hardcoded ITUK cells. Recheck before quoting MIDI numbers from v17 externally. (~92,585 units 2024 — treat as estimate until verified)
7. **Build script `build_isuzu_uio.py`** not updated for v17 — treat v17 as manually-patched. Do not regenerate from script.
8. **Model-level ITUK table rows** in v17 dashboard carry v11 step-function basis (totals are v17-correct; model sub-rows need refresh from Sheet 4 Section C).

## Next refresh
- FY2026 actuals roll-in (when ISZE year-end closes, ~May–Jun 2026)
- Request updated SMMT/DVLA extract from ITUK (annual, ~Mar 2027 for CY2026 car park)
- Refresh Niguri extract when ITUK releases next internal FY forecast
