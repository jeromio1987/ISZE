# PRISM — Parts Revenue Intelligence & Sales Monitor

## Start the app (Windows)

**Usual (MD-safe):** double-click **`run_prism.ps1`**. Then open **http://localhost:8503**.

(`run_prism.bat` is the older 8501 path — also MD-safe, but use the `.ps1` for the usual window.)

Attach, ITUK leakage, elasticity, the demand-flow Sankey, and aftermarket scrape stay off that window.

**Internal (those extra tabs):** double-click **`run_prism_internal.ps1`** (or `run_prism_internal.bat`). Same address **8503** — close the usual PRISM window first.

Or in PowerShell:

```powershell
$env:ISZE_ROOT = 'C:\Users\jerom\Desktop\claude\ISZE'  # or your local clone
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
.\run_prism.ps1
```

Then open **http://localhost:8503** if the browser does not open automatically.

### Do not run

- `python app.py` — that does not start Streamlit.
- `streamlit run` from the wrong folder — use **`03_analytics\Isuzu\prism`**, not the ISZE root alone.

### If it still fails

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Copy the error from the terminal window and share it.

## Data pipeline

```powershell
.\scripts\run_pipeline_and_verify.ps1
```

Refreshes derived CSVs, `isze_data.json` (Master dashboard JSON in `01_data/dashboards/`), and HTML overlays (Golden Window, Competitiveness).

**PMS capture intervals** — edit `data/pms_capture_assumptions.yaml`, then re-run `build_bvp_p0_p1.py`.

Derived files: `$env:ISZE_ROOT\01_data\derived\`

## Docs

- Metrics: `docs/metric_dictionary.md`
- Roadmap: `..\..\..\00_docs\ISZE_ROADMAP.md`
