# Isuzu mapping integrity — full pass

**Date:** 2026-09-03  
**Ask:** full data integrity + clean of Isuzu mapping stack  
**Pipeline:** `_verification_report.json` was green (116/0) *before* this mapping edit. Mapping CSVs changed; **derived parquet was not rebuilt** (no rebuild/ship ask).

---

## Scope (identity / crosswalk stack)

| Layer | Path | Role |
|---|---|---|
| Distributor master | `03_analytics/Isuzu/prism/data/distributor_master_mapping.csv` | PRISM country/DB identity |
| SAP sold-to | `03_analytics/Isuzu/prism/data/sap_sold_to_mapping.csv` | `sold_to_sap` → `distributor_code` |
| Loader exclusions | `03_analytics/Isuzu/prism/modules/data_prep.py` (`EXCLUDED_CODES`, `EXTRA_DISTRIBUTORS`) | GPS/PMS drop list |
| Dashboard dimension | `01_data/00_derived/distributor_dimension.csv` | Canonical sold-to grain for composable dashboards |
| Tender country map | `04_tools/ISZE_Tender_Monitor_Install/country_distributor_map.yaml` | Country → GPS DB (null = no SPU) |
| SaTy buckets | `03_analytics/Isuzu/prism/modules/saty_mapping.py` | VOR / urgent / standard (order type, not DB identity) |
| OS data map | `00_docs/ISZE_OS_DATA_MAP.yaml` | Capability catalogue (not DB codes) |
| Map registry | `00_docs/MAP_REGISTRY.yaml` | Navigation index |
| UIO Assumptions | `06_uio/_CURRENT/` sheet *Assumptions & Mapping* | Series / LCV distributor → country |

---

## What was dirty

| Issue | Severity | Evidence |
|---|---|---|
| **ROMANIA missing from master CSV** | High | Present in SAP (396), GPS derived, `db_profiles.yaml`, UIO builder — only patched via `EXTRA_DISTRIBUTORS` (and that path always concat’d → duplicate risk once CSV caught up) |
| **GERMANY `segment_cv=No` stale** | Medium | UIO LD+MD; dimension + GPS scope = MIXED; `db_profiles.yaml` watch already flagged |
| **CY2026 non-parts → `UNMAPPED`** | Medium | sold-to **146 / 373 / 2970 / 2987** = €226,781 (all SERVICE / demurrage / e-credit). Showed as ghost `UNMAPPED` in `gps_spu_by_distributor.csv` |
| **Broken gps_dashboard junctions** | Medium | Pointed at dead WSL path `/sessions/.../claude/Isuzu/data/...` |
| Benelux NL/LUX/PL in master, not as SAP sold-tos | Low / by design | Bill under Benelux entity (SAP 90 → BELGIUM); NL/LUX already in `EXCLUDED_CODES` |
| Israel UTI≠UMI | OK | Master + SAP correctly split 1797=UMI / 1799=UTI. Tender yaml uses Israel→UTI as GPS primary (documented) |
| `country_distributor_map.yaml` FR/IT/ES/PL/NL null | OK | No SPU row — do not invent |

---

## What was cleaned (this pass)

1. **`distributor_master_mapping.csv`**
   - Added **ROMANIA** (ISUZU ROM AUTO SRL, CEE, LCV Yes / CV No, sap 396).
   - Fixed **GERMANY** `segment_cv` No → **Yes**; notes updated to Mixed.
   - Added **NON_PARTS** exclusion identity row.

2. **`sap_sold_to_mapping.csv`**
   - Mapped **146, 373, 2970, 2987** → `NON_PARTS`.
   - Re-check after apply: **UNMAPPED rows = 0** (€0).

3. **`data_prep.py`**
   - Added `NON_PARTS` to `EXCLUDED_CODES`.
   - Cleared `EXTRA_DISTRIBUTORS` ROMANIA entry (now in CSV).
   - `load_distributor_mapping` skips extras already present (no silent dupes).

4. **`build_sap_sold_to_mapping.py`**
   - MANUAL list updated so a rebuild does not drop the NON_PARTS sold-tos.

5. **`gps_dashboard/data/distributor_master_mapping.csv`**
   - Broken junction replaced with symlink → prism SSOT (readable).

---

## Post-clean checks

| Check | Result |
|---|---|
| Duplicate `distributor_code` in master | none |
| Blank keys | none |
| SAP codes not in master | none |
| Master codes not in SAP | LUXEMBOURG, NETHERLANDS, POLAND (Benelux — expected) |
| UTI / UMI blend in SAP | none (1797≠1799) |
| Apply map on `sales_fact` → UNMAPPED | **0** |
| NON_PARTS € | 226,781.43 (excluded from GPS when EXCLUDED_CODES applied) |

---

## Left for Jerome (decisions / not auto-fixed)

1. **Rebuild derived?** Mapping is clean on disk; `sales_fact` / `gps_spu_*` still carry the old UNMAPPED row until an authorized pipeline rebuild.
2. **ROMANIA segment:** GPS scope = LCV; `db_profiles.yaml` says `segment: mixed` with LD/MD UIO rows. Master now follows GPS LCV. Confirm if CV should flip to Yes.
3. **SAP 2929 (ISUZU MOTORS SWEDEN AB)** still maps to **SWEDEN** in sap CSV; dimension marks it `excluded_entity` (dormant). Prefer keep mapped + exclude elsewhere, or remap to an exclusion code?
4. **BELGIUM Benelux scope:** master still notes BE/NL/PL/LUX under one entity; GPS max-spend uses Belgium parc only (known ceiling bug — not touched).
5. **OS data map HTML** not regenerated (needs rebuild/ship ask).

---

## Absolute paths touched

- `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\distributor_master_mapping.csv`
- `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\sap_sold_to_mapping.csv`
- `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\modules\data_prep.py`
- `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\scripts\build_sap_sold_to_mapping.py`
- `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\gps_dashboard\data\distributor_master_mapping.csv` (symlink)
- This report: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_mapping_integrity_report_2026-09-03.md`
