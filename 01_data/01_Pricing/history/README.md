# Pricing list history (dated snapshots)

**Purpose:** year-matched list prices so list-to-pocket / realization is not polluted by applying a 2026 list backwards.

| File | Vintage | Role |
|------|---------|------|
| `ZPR1_2023-01-03.xlsx` | 2023 | ZPR1 customer sheets from mixed `2023.xlsx` (no PR00 tab) |
| `ZPR1_2024-01-03.xlsx` | 2024 | ZPR1 upload layout — customer × PN |
| `ZPR1_2025-02-01.xlsx` | 2025 | ZPR1 upload layout — customer × PN |
| `IE40_PR00_2023-12-31.xlsx` | 2023 | PR00 Material + EUR (from mixed `2023.xlsx` tab `PR00`) |
| `IE40_PR00_2024-12-31.xlsx` | 2024 sheet | PR00 Material + EUR (from `PR00.xlsx` tab `2024`) |
| `IE40_PR00_2025-12-31.xlsx` | 2025 sheet | PR00 Material + EUR (from `PR00.xlsx` tab `2025`) |
| `IE40_PR00_2024_and_2025.xlsx` | both tabs | Combined source copy of Downloads `PR00.xlsx` |

**As-received:** `../_raw/2023.xlsx` (mixed PR00+ZPR1), `../_raw/PR00_2024_2025.xlsx`, `ZPR1_UPLOAD_LAYOUT_2024.xlsx`, `ZPR1_UPLOAD_LAYOUT_2025.xlsx`  
**Current (2026) lists:** `../_raw/EXPORT_ZPR1_20260810.xlsx`, `../_raw/Price_file_PR00_IE40_20260810.xlsx`

### 2023 mixed workbook (`../_raw/2023.xlsx`)

Source tabs: `1799`, `1797`, `PR00`, `2372`, `2733`, `2734`. Split into separate history files (PR00 vs ZPR1).

| Sheet | Kind | Data rows | Valid From / year signal |
|-------|------|-----------|--------------------------|
| `1799` | ZPR1 (UTI) | 115,434 | `2023-01-03` |
| `1797` | ZPR1 (UMI) | 117,137 | `2023-03-01` |
| `2372` | ZPR1 | 117,137 | `2023-03-01` |
| `2733` | ZPR1 | 1,216 | `2023-03-01` |
| `2734` | ZPR1 | 1,215 | `2023-03-01` |
| `PR00` | IE40 PR00 | 607,096 | no Valid From; year from filename / sheet label `2023` |

ZPR1 filename stamp follows earliest Valid From (`2023-01-03`, customer 1799); other ZPR1 sheets are `2023-03-01`.  
PR00 source tab had **no header** (Material, Price only); history file adds `Material` / `Price_EUR` and sheet name `2023`. Seven source `#VALUE!` prices nullified in history/parquet.

**Cheap remote extracts** (allowlist `!01_data/00_derived/pricing_*.parquet`):

| Year | PR00 | ZPR1 | Builder |
|------|------|------|---------|
| 2023 | `pricing_pr00_ie40_2023.parquet` | `pricing_zpr1_2023.parquet` | `91_build/build_pricing_history_year_parquets.py` |
| 2024 | `pricing_pr00_ie40_2024.parquet` | `pricing_zpr1_2024.parquet` | same |
| 2025 | `pricing_pr00_ie40_2025.parquet` | `pricing_zpr1_2025.parquet` | same |
| 2026 (current) | `pricing_pr00_ie40.parquet` | `pricing_zpr1.parquet` | `build_pricing_enquiry_tables.py` |

Meta: `01_data/00_derived/pricing_history_years.meta.json`. Not engine-wired yet — do not quote list-to-pocket until year-matched joins are validated.

### Quoting rules

- **PR00** year sheets unlock year-matched list-to-pocket vs billing (use sheet year = billing year) — **validate joins before quoting**.
- **ZPR1** = customer-condition list EUR — not network PR00; UTI ≠ UMI.
- Date stamps `YYYY-12-31` are conventional year labels for PR00 history (2024/2025 source tabs named by year; 2023 from mixed workbook tab `PR00`).
- Excel stays local (gitignore `*.xlsx`); derive parquet when remote clones need it.
