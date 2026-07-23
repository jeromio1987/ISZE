# ISZE — Canonical File Manifest

**Last updated:** 2026-07-16
**Convention:** No version numbers in canonical filenames. Version lives inside the file (Changelog sheet / header). Old versions go to `_archive/` / `92_archive/` with a date stamp.

> **2026-07-16 dedupe:** older duplicates archived to `01_data/92_archive/dedupe_2026-07-16/` (KPI april, PL plan "- Copy", root budget-per-DB dup, kickback V3, ITUK study `(1)` + prior canonical, stretch-pilot older versions). Newest of each kept as canonical.
> **GPS Calculator resolved 2026-07-16:** the "missing canonical" was a stale doc — `build_gps_v9.py` emits `ISZE_GPS_Calculator_v9.xlsx` and no code reads an unversioned name. `_v9` is now declared canonical below (versioned-name exception).

**Map index:** `00_docs/MAP_REGISTRY.yaml` · `00_docs/MAPS.md`

---

## Canonical files

| Artifact | Canonical path | Version tracked | Archive location |
|----------|---------------|-----------------|-----------------|
| **UIO workbook** | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` | Changelog sheet inside workbook | `06_uio/_Archive/` |
| **UIO (PRISM copy)** | `03_analytics/Isuzu/prism/data/UIO.xlsx` | Same workbook | n/a (regenerated from `_CURRENT`) |
| **GPS Calculator** | `01_data/ISZE_GPS_Calculator_v9.xlsx` (**build output of `91_build/build_gps_v9.py`** — versioned name is intentional, like SAP files; no unversioned copy exists or is read by any code) | Changelog sheet inside workbook + `91_build/GPS_FILE_LINEAGE.md` | `01_data/92_archive/` (v7/v8/v9_new) |
| **GPS planning workbook** | `01_data/ISZE_GPS_v5.xlsx` | Method & Assumptions §5 changelog | `01_data/_archive/` |
| **GPS file lineage (agents)** | `01_data/91_build/GPS_FILE_LINEAGE.md` | Git | n/a |
| **GPS Dashboard** | `02_dashboards/fleet/ISZE_GPS_Dashboard.html` | ✅ canonical · built by `_build/build_gps_dashboards.py` | `_v9.html` = thin redirect |
| **UIO Dashboard** | `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` | ✅ renamed 2026-07-16 (static HTML; no builder) | `…_v18.html` = thin redirect |
| **BVP Parts Catalog** | `01_data/raw/reference/BVP PARTS CATALOG.xlsx` | Date stamp on save | `01_data/raw/reference/_archive/` |
| **KPI Master** | `01_data/planning/KPI Master File.xlsx` | Date in header row | `01_data/planning/_archive/` |
| **Action Plan (VPACC)** | `01_data/planning/Action plan FY2027 VPACC.xlsx` | Date in header row | `01_data/planning/_archive/` |
| **SAP billing (current year)** | `01_data/raw/sales/CY2025.XLSX` | Year in filename (exception: year IS meaningful) | `01_data/raw/sales/` (all years kept) |
| **PRISM build script** | `03_analytics/Isuzu/prism/` (Python files) | Git history | Git |
| **Weekly / analyst briefs** | `05_memory/briefs/` | Date in filename | n/a |
| **PMS pilot workspace** | `03_analytics/Isuzu/pms-pilot/` | Project files | `_archive/` when closed |
| **Distributor mapping CSV** | `03_analytics/Isuzu/prism/data/distributor_master_mapping.csv` | Git | n/a |

---

## Pending renames (pipeline JSON — do not rename until builders + gps_reconcile updated together)

| Current name | Target canonical name | Blocker |
|-------------|----------------------|---------|
| `01_data/91_build/gps_v9_snapshot.json` | `01_data/91_build/gps_snapshot.json` (primary write) | `build_gps_v9.py` still emits `_v9`; `gps_reconcile.py` compares both — see sequenced plan in `ISZE_Cleanup_Plan.md` |
| `01_data/91_build/uio_v18_gps.json` | retire alias | `gps_v9_loaders.py` already writes `uio_v19_gps.json` + legacy alias; stop alias after callers read v19/uio_gps only |

**Done 2026-07-16 (HTML layer):** UIO + GPS dashboard filenames canonical; `gps/ISZE_GPS_Dashboard_v9.html` orphan archived; hubs/nav point at canonical.

---

## Exception: year-in-filename is allowed

SAP billing files use the year as a meaningful differentiator, not a version number: `CY2023-2024.XLSX`, `CY2025.XLSX`. These are kept as-is — every year is a distinct dataset.

---

## Convention going forward

1. **Overwrite**, don't save-as to a new version name
2. **Archive** before overwriting: `name_archived_YYYY-MM-DD.ext` → `_archive/`
3. **Log the change** on the Changelog sheet inside the file
4. **Never** increment `_vN` in a filename — that is how sprawl starts
5. **GPS planning** = `ISZE_GPS_v5.xlsx` only. Do **not** fork `ISZE_GPS_Calculator_v9` into `ISZE_GPS_v6` — see `01_data/91_build/GPS_FILE_LINEAGE.md`
