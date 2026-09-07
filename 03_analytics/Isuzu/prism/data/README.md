# PRISM — Data Folder

## GPS model targets

**`gps_model_targets.csv`** — maximum spend per unit per model (€/vehicle/year, GPS workbook).

| Group | Models | Max €/veh/yr |
|-------|--------|--------------|
| `N75_N50_N62` | N75, N50, N62, LD, NPR | 1,120 |
| `F_Series_MD` | F-Series, MD | 1,344 |
| `LCV_D_Max` | LCV, D-Max, NLR, N35 | 250 |

PRISM **GPS % evolution** (GPS → Trends):

`GPS % = total sales ÷ Σ(UIO per model × max target for that model) × 100`

100% = sales match the model-weighted maximum wallet. Edit the CSV when the GPS file is updated.

---

## UIO Files

### Production file
**`UIO_v17.xlsx`** — the live file used by colleagues.

- **Never overwrite or rename this file.**
- It is the source of truth for all shared reporting until a version is formally promoted.
- `config.py` points to this file by default (`BETA_MODE = False`).

### Beta file
**`UIO_v18_beta.xlsx`** — local testing only.

- Place this file here when you are evaluating a new UIO version.
- It is `.gitignored` and **must not be committed or sent to colleagues**.
- Only active when `PRISM_BETA=true` is set in the environment.

---

## How to toggle beta mode

**Windows Command Prompt:**
```cmd
set PRISM_BETA=true
streamlit run app.py
```

**PowerShell:**
```powershell
$env:PRISM_BETA = "true"
streamlit run app.py
```

**Single-line (CMD):**
```cmd
set PRISM_BETA=true && streamlit run app.py
```

To return to production mode, close the terminal (environment variable does not persist)
or explicitly set `PRISM_BETA=false`.

---

## Promoting beta to production

When you are satisfied that `UIO_v18_beta.xlsx` is correct and ready to share:

1. Rename `UIO_v18_beta.xlsx` to `UIO_v18.xlsx` (or the agreed versioned name).
2. Update `config.py`:
   - Set `UIO_FILE_PROD = "data/UIO_v18.xlsx"`
   - Bump the version string in `app.py` if needed (e.g. `"v2.1"`)
3. Archive the old production file (rename to `UIO_v17_archived.xlsx`) rather than deleting.
4. Notify the team before pushing so nobody is mid-session on the old file.

---

## Sales data (canonical)

PRISM prefers **`ISZE/Data/derived/sales_fact.parquet`** (not this folder).

Build from raw CY billing:

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism
pip install -r requirements.txt
python scripts/build_sales_fact_from_cy.py
```

Sources: `ISZE/Data/raw/sales/CY2023-2024.XLSX`, `CY2025.XLSX`.

Legacy fallback: `sales_detailed_for_claude_full_fixed.tsv` in this `data/` folder.

See `ISZE/Data/DATA_MANIFEST.md` and `config.py` for all resolved paths.

## Other data files

- `distributor_master_mapping.csv` — required under `03_analytics/Isuzu/prism/data/` (legacy `Projects/Isuzu/data/` path removed 2026-07-16)
- UIO: production file here, or auto-resolve from `ISZE/UIO/_CURRENT/`
