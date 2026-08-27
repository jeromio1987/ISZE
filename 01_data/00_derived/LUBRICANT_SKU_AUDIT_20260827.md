# Wider lubricant-SKU audit — 2026-08-27

**Mode B · internal.** Read-only. **No GPS percentage was computed or restated.**
**Reproduce:** `python 01_data/91_build/audit_lubricant_skus.py`
**Evidence:** `lubricant_sku_audit.json` · `lubricant_sku_audit.meta.json` · `lubricant_sku_audit_uncovered.csv` (15 SKUs)
**Follow-up to:** `DATA_INTEGRITY_FLAGS_2026-05-28.md` flag B — *"wider lubricant-SKU audit still advisable"*, open since 2026-05-28.

---

## The rule that was audited

GPS excludes lubricants by **part-number prefix**: `55004*` / `55007*` (Shell Rimula). That rule was written around the Israel case, and the mislabelled-SKU audit that supports it lists **3 part numbers**.

A prefix rule cannot see a fluid sold under a different part-number family. So this audit works from the **description** instead — fluid markers (BESCO, RIMULA, ATF, COOLANT, LLC, GREASE, BRAKE FLUID, ENGINE/GEAR OIL, WSI, an SAE viscosity grade) minus hardware nouns, because a part *about* oil is not oil. Without the hardware filter the sweep returns 30,814 rows dominated by `ELEMENT; OIL FILTER` and `NIPPLE; GREASE`.

## Finding — €400,159 of fluid sits outside the rule

| | Part numbers | EUR |
|---|---:|---:|
| Fluids found in `sales_fact` | 17 | 698,032 |
| Covered by the `55004*/55007*` rule | 2 | 297,872 |
| **Not covered** | **15** | **400,159** |

Largest uncovered SKUs: `1884058030` BESCO CLEAN SUPER (200L) €189,804 · `5877030010` ISUZU ATF WSI 4L €72,597 · `1884059120` BESCO ATF3 OIL (4L) €45,582 · `1884057860` GEAR OIL LSD €36,334 · `1884059040` GEAR OIL 20L €26,123. Full list in the CSV.

These are the **BESCO / ISUZU ATF genuine-fluid family** — Isuzu's own lubricant brand, not Shell.

## The assumption that breaks

The exclusion rule treats lubricants as an Israel/UMI phenomenon. They are not:

| Distributor | EUR |
|---|---:|
| **ARMENIA** | **189,804** |
| UMI | 67,013 |
| ITUK | 58,454 |
| NORWAY | 30,132 |
| PORTUGAL | 26,058 |
| HUNGARY | 18,921 |
| GERMANY · FINLAND · ROMANIA · BELGIUM · GREECE · DENMARK | 9,665 combined |

**13 distributors**, and the largest single lubricant exposure in the book is **Armenia**, not Israel. Steady over time: €86.7k (2023) · €125.9k (2024) · €111.2k (2025) · €76.4k (2026 through June).

## What this does and does not touch

- **GPS parts base:** these euros sit inside it today. The exclusion rule was written to keep fluids out of parts GPS so the metric stays comparable to competitor and Eucon benchmarks; €400k over four years is currently inside the numerator for 13 DBs.
- **PMS capture:** **clean.** 0 of the 15 SKUs appear in `parts_catalog_dimension` with a PMS category, so capture actuals are unaffected.
- **Order of magnitude:** ~0.34% of the €117.5M billed across the four years. Small in aggregate, concentrated per DB — for Armenia it is the dominant lubricant line.

## Two things found on the way

**1. The GPS-auditor skill's "known inconsistency" is out of date.** It states CY2025 contains no transport, lubricants or CR while 2023–24 do, and instructs agents to caveat every multi-year GPS trend with *"CY2024 overstated by ~€1.4M vs CY2025"*. On the current parquet all four years carry these items:

| Year | Lubricant 550xxx | Transport | CR/RE |
|---|---:|---:|---:|
| 2023 | 274,694 | 299,081 | 116,240 |
| 2024 | 577,281 | 362,489 | 523,429 |
| 2025 | **524,096** | **343,187** | **509,348** |
| 2026 | 194,285 | 197,071 | 502,132 |

The asymmetry was real in June 2026; the parquet has been rebuilt since (it now runs to 2026-06-30). Applying that caveat today would misstate the trend in the opposite direction. Exclusions are applied downstream at load via `line_kind` (flag A), so presence in the parquet is expected — the point is that it is now **consistent across years**.

**2. `sold_to` carries two representations.** The same distributor appears as a numeric code (`1797.0`) and as a name (`UNIVERSAL MOTORS ISRAEL LTD`) in the same column — 366 vs 2 rows for Israel's lubricant lines alone. Any group-by on `sold_to` splits that DB in two. This audit joins on `sold_to_sap` via `distributor_dimension.csv`, per the canonical rule, and is unaffected.

## What was deliberately not done

- **No exclusion applied.** Extending the rule from a prefix to a description-based or curated-SKU test is a pipeline change: it moves GPS numbers for 13 DBs and needs `run_pipeline_and_verify.ps1`. That is Jerome's call.
- **No GPS figure restated.** Nothing here is quotable as a GPS%.
- **Detection is description-based** — a fluid whose description carries no fluid marker is not caught. Treat €400,159 as a floor, not a closed count.

## Suggested next step

Decide whether the lubricant exclusion becomes a **curated SKU list** (the 17 found here, reviewed and extended by Jerome) instead of a prefix rule. That is a one-file change to the loader plus a verify run — but it moves published GPS numbers, so it is a decision before it is a build.
