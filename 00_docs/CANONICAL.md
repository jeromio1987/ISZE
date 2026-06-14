# ISZE — Canonical File Manifest

**Last updated:** 2026-06-13
**Convention:** No version numbers in canonical filenames. Version lives inside the file (Changelog sheet / header). Old versions go to `_archive/` or `_Archive/` with a date stamp.

**Map index:** `00_docs/MAP_REGISTRY.yaml` · `00_docs/MAPS.md`

---

## Canonical files

| Artifact | Canonical path | Version tracked | Archive location |
|----------|---------------|-----------------|-----------------|
| **UIO workbook** | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` | Changelog sheet inside workbook | `06_uio/_Archive/` |
| **UIO (PRISM copy)** | `03_analytics/Isuzu/prism/data/UIO.xlsx` | Same workbook | n/a (regenerated from `_CURRENT`) |
| **GPS Calculator** | `01_data/ISZE_GPS_Calculator.xlsx` | Changelog sheet inside workbook | `01_data/_archive/` |
| **GPS Dashboard** | `02_dashboards/fleet/ISZE_GPS_Dashboard.html` ⚠ pending rename | Built by `02_dashboards/_build/build_gps_dashboards.py` | `02_dashboards/_archive/` |
| **UIO Dashboard** | `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` ⚠ pending rename | Built by `02_dashboards/_build/` | `02_dashboards/_archive/` |
| **BVP Parts Catalog** | `01_data/raw/reference/BVP PARTS CATALOG.xlsx` | Date stamp on save | `01_data/raw/reference/_archive/` |
| **KPI Master** | `01_data/planning/KPI Master File.xlsx` | Date in header row | `01_data/planning/_archive/` |
| **Action Plan (VPACC)** | `01_data/planning/Action plan FY2027 VPACC.xlsx` | Date in header row | `01_data/planning/_archive/` |
| **SAP billing (current year)** | `01_data/raw/sales/CY2025.XLSX` | Year in filename (exception: year IS meaningful) | `01_data/raw/sales/` (all years kept) |
| **PRISM build script** | `03_analytics/Isuzu/prism/` (Python files) | Git history | Git |
| **Weekly / analyst briefs** | `05_memory/briefs/` | Date in filename | n/a |
| **PMS pilot workspace** | `03_analytics/Isuzu/pms-pilot/` | Project files | `_archive/` when closed |
| **Distributor mapping CSV** | `03_analytics/Isuzu/prism/data/distributor_master_mapping.csv` | Git | n/a |

---

## Pending renames (not yet done — internal paths need updating first)

| Current name | Target canonical name | Blocker |
|-------------|----------------------|---------|
| `02_dashboards/_archive/ISUZU_UIO_Dashboard_2026_v18.html` | `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` | Build script `build_uio_dashboard_v18.py` hardcodes output filename |
| `02_dashboards/fleet/ISZE_GPS_Dashboard_v9.html` | `02_dashboards/fleet/ISZE_GPS_Dashboard.html` | `build_gps_dashboards.py` docstring + title hardcode `v9` |
| `01_data/_build/gps_v9_snapshot.json` | `01_data/_build/gps_snapshot.json` | Build script reads by versioned name |
| `01_data/_build/uio_v18_gps.json` | `01_data/_build/uio_gps.json` | Build script reads by versioned name |

---

## Exception: year-in-filename is allowed

SAP billing files use the year as a meaningful differentiator, not a version number: `CY2023-2024.XLSX`, `CY2025.XLSX`. These are kept as-is — every year is a distinct dataset.

---

## Convention going forward

1. **Overwrite**, don't save-as to a new version name
2. **Archive** before overwriting: `name_archived_YYYY-MM-DD.ext` → `_archive/`
3. **Log the change** on the Changelog sheet inside the file
4. **Never** increment `_vN` in a filename — that is how sprawl starts
