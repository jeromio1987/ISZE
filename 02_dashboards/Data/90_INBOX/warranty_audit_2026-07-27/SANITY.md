# Warranty sanity — Jerome rule 2026-07-27 (Mode B)

**Verified:** 2026-07-27 · Raw Excels under `01_data/06_Warranty/` · Evidence: `sanity_results.json`, this note.

## Jerome’s rule (locked)

1. Sheet4 / PARTNBR `0` / `0000000000` → **SKIP** if no real PN (labour, not parts). Not a missing-country GPS gap.
2. Ireland / Portugal “incomplete prices” → **SAME**: skip labour / no-PN. Don’t chase price-map for non-parts.
3. If warranty data exists for the relevant DBs with **no big black periods** in dates → **no data missing**.

---

## A) €314K / PARTNBR `0000000000` — SKIP

| Check | Result |
|---|---|
| Grain | `Warranty_CV_2025.xlsx` → `DATA WITHOUT MIDI`, CY2025 |
| Blank-PN rows | **3.083** with PARTNBR = `0000000000` |
| PARTAMT sum | **€0,00** |
| LBRAMT sum | **€110.994,91** (labour) |
| Qty | `"00"` / 0 on blank rows |
| OPE samples | Wiring repair, turbo R&R, roof color coat, tachograph… |

**Sheet4 “orphan €314K” was a parse artifact**, not missing attribution:

- Pivot sorts PARTNBR `0` **before** real PNs under each country (e.g. UTI header → `0` count=274 → then real UTI parts).
- Old audit treated `0` as a **country** header and summed the following real part € into a fake bucket (**~€319.8K** buggy parse).
- Correct reading: zero-PN **parts € = €0**; valid-PN € stays under ITUK/UTI/IE/PT/….

**Verdict: YES, skippable.** Not a GPS parts-warranty country gap.

---

## B) Ireland / Portugal CV price-map — non-blocking

| | Ireland | Portugal |
|---|--:|--:|
| CY2025 rows | 17 | 139 |
| Blank PN (labour) | 2 (€522 LBR) | 25 (€1.452 LBR) |
| Valid PN | 15 | 114 |
| Priced via ITUK/UTI map | 14 (93%) | 72 (63%) |
| Unpriced **real** PNs | 1 | 42 |
| Priced € (lower bound) | €3.908 | €28.836 |

Unpriced samples are real part numbers (e.g. `1884055410`, `8976871550`) with PARTAMT — **valuation lower bound**, not missing claims / labour.

**Verdict: IE/PT still a problem? NO** for “data missing” / GPS parts gap. Optional price-map polish only.

---

## C) Date coverage (parts rows / claim activity)

### CV — `Warranty_CV_2025.xlsx` (`DATA WITHOUT MIDI`, valid PN only)

| DB | n CY2025 | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Note |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| ITUK | 1507 | 203 | 34 | 364 | 99 | 272 | 61 | 160 | 129 | 92 | 93 | 0* | 0* | Continuous Jan–Oct in this file |
| UTI | 758 | 113 | 48 | 64 | 69 | 78 | 121 | 75 | 103 | 25 | 62 | 0* | 0* | Continuous Jan–Oct |
| Ireland | 15 | 2 | 0 | 2 | 1 | 4 | 0 | 1 | 2 | 1 | 2 | 0* | 0* | Sparse volume; no 2+ consecutive hole |
| Portugal | 114 | 16 | 10 | 8 | 13 | 8 | 7 | 20 | 12 | 5 | 15 | 0* | 0* | Continuous Jan–Oct |
| ISD | 10 | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 2 | 1 | 1 | 0* | 0* | Only ~10 parts/year — quiet months = volume, not feed gap |

\*Nov–Dec = 0 in `Warranty_CV_2025.xlsx` because that extract ends ~Oct. **Sister files fill them:**

| File | Span | ITUK Nov/Dec | UTI Nov/Dec |
|---|---|--:|--:|
| `CV Warranty.xlsx` sheet `10_25-12_2025` | 2025-09-18 → 2025-12-17 | 106 / 103 | 249 / 61 |
| `CV warranty01_03_2026.xlsx` | 2025-12-19 → 2026-03-17 | (continues into 2026) | Dec56 + 2026 |

### LCV — `Warranty_LCV_2025.xlsx`

| DB | n CY2025 | Span | Big black hole (2+ mo)? |
|---|--:|---|---|
| IUK | 6423 | 2024-11 → 2025-11 | **No** |
| ISD | 642 | 2024-12 → 2025-11 | **No** (only May empty) |
| Ireland | 163 | 2024-12 → 2025-11 | **No** |
| Portugal | 527 | 2025-01 → 2025-11 | **No** |

### UMI — `UMI warranty data 202301 - 202605.xlsx`

| | |
|---|---|
| Span | 2022-12-18 → 2026-05-17 |
| CY2025 lines | 12.042 |
| CY2025 parts € (prior closed method) | **€1.791.020,28** |
| CY2025 months | Jan–Dec continuous |
| Full span black holes | **None** |

---

## D) Final — data missing for GPS CY2025 parts warranty?

**NO.**

- Files exist for ITUK, UTI, UMI, IUK, Ireland, Portugal, ISD (CV+LCV as applicable).
- No multi-month feed blackouts on the high-volume DBs.
- ISD CV / Ireland CV quiet months = low claim volume, not missing extracts.
- Nov–Dec CV lives in sister workbooks, not a hole in the source world.
- €314K + IE/PT “gaps” closed under Jerome’s labour / no-PN rule.

Machine JSON: [`sanity_results.json`](sanity_results.json) · script: [`sanity_jerome_rule.py`](sanity_jerome_rule.py)
