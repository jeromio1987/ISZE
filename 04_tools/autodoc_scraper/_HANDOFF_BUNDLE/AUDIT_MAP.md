# ISZE file map (audit + navigation)

**Products (read `PRODUCT_LOGIC.md`):** PMS Intelligence = this bundle · IAM Lookup Lab = parent dashboard · Competitor scrape = parent `*_scraper.py` only.

**Config hub:** `sources.yaml` when data files change.

Last updated: May 2026

---

## 1. Root folder (historical name: `autodoc_scraper`)

The disk folder name is **legacy** — it holds three unrelated capabilities:

**`C:\Users\jerom\Desktop\claude\ISZE\Tools\autodoc_scraper`**

```
autodoc_scraper/                 ← monorepo (misleading name)
├── _HANDOFF_BUNDLE/             ← PRODUCT: ISZE PMS Intelligence
├── _html_previews/              ← HTML: PMS + IAM (separate files)
├── *_scraper.py + *_results.csv ← PRODUCT: competitor price scrape only
├── autodoc_dashboard.py         ← PRODUCT: ISZE IAM Lookup Lab (legacy 10-tab)
└── *.bat                        ← launchers (see DASHBOARD_MAP.md)
```

---

## 2. This folder — recommended BI stack (`_HANDOFF_BUNDLE`)

| Role | File | Purpose |
|------|------|--------|
| **Run BI** | `run_bi.bat` | Starts Streamlit dashboard |
| **Dashboard UI** | `bi_shell.py` | CY/FY, year, ITUK UIO basis, All distributors tab |
| **Calculations** | `engine.py` | PMS lost sales, UIO scope, multi-DB |
| **Data paths** | `sources.yaml` | **Edit when files upgrade** (v3, v17, PMS Calc, PRISM, dealer sales) |
| **Loaders** | `sources_loader.py` | Yaml, PRISM CSV, ITUK dealer sales, SMMT car park |
| **PMS parts override** | `pms_parts_config.yaml` | Optional interval overrides |
| **Contract** | `SPEC.md` | Engine contract + signed methodology decisions |
| **Model refinement** | `MODEL_REFINEMENT_TRACKER.xlsx` | Per-model checklist (regen: `scripts/build_model_refinement_sheet.py`) |
| **Docs** | `README.md` | Run + upgrade instructions |
| **This map** | `AUDIT_MAP.md` | File locations for audits |
| **Product logic** | `PRODUCT_LOGIC.md` | Why PMS / IAM / scraper are separate |
| **Dashboard map** | `DASHBOARD_MAP.md` | All Streamlit + HTML launchers |
| **Changelog** | `CHANGELOG.md` | Audit remediation log |
| **Audit status** | `AUDIT_STATUS.md` | Finding register + sign-off |
| **Scrapers (optional)** | `SCRAPE_OPTIONAL.md` | Not required for PMS |
| **Deps** | `requirements.txt` | Python packages |
| **v3 matrix (local)** | `ISZE_Parts_Intelligence_v3.xlsx` | PN price matrix copy |
| **Scrape results** | `autodoc_results.csv`, `ks_results.csv`, `mekonomen_results.csv` | Competitor prices |
| **Scrapers (copy)** | `autodoc_scraper.py`, `ks_scraper.py`, `mekonomen_scraper.py`, `scraper_pn_loader.py` | Re-run from bundle if needed |

### Run the live dashboard

```text
Double-click:  run_bi.bat
Or:            python -m streamlit run bi_shell.py
```

---

## 3. ITUK UIO — three bases (sidebar)

| Basis | ~Units | Source |
|-------|--------|--------|
| PMS Calc Step 2 | 11,900 | PMS Coverage Calculator — fleet exercise |
| **SMMT 2024 car park** | **22,389** | v17 sheet `4. ITUK UIO Projection` (`2024A`) — **same as PRISM All distributors ITUK** |
| v17 sheet 1 | ~121k | Survival cohort math — **not** SMMT car park |

Default in `sources.yaml`: `ituk_uio_source: smmt_car_park` (see `SPEC.md` § Decisions).

---

## 4. Parent folder — full IAM dashboard (10 Streamlit tabs)

**`C:\Users\jerom\Desktop\claude\ISZE\Tools\autodoc_scraper`** (one level up)

| File | Purpose |
|------|--------|
| `autodoc_dashboard.py` | Cockpit, PMS, Brand league, Threat map, PN deep dive, etc. |
| `run_dashboard.bat` | Launcher |
| `iam_scoring.py` | T (threat) / Q (quality), quadrants |
| `iam_brand_tiers.csv` | Brand quality lookup (editable) |
| `substitution_probability.csv` | P(sub) lookup (editable) |
| `pms_intervals.csv` | Legacy intervals (engine prefers PMS Calc / yaml) |
| `html_export.py` | Plotly/HTML helpers |
| `competitive_bi.py` | Older Streamlit reference |
| `run_competitive_bi.bat` | Launcher |

Use **handoff** for PMS + multi-DB + upgradeable sources. Use **parent** for IAM threat/quality on scraped PNs.

---

## 5. Executive HTML dashboards (static)

### Output (open in browser)

**`C:\Users\jerom\Desktop\claude\ISZE\Tools\autodoc_scraper\_html_previews\`**

| File | What it is |
|------|------------|
| **`isze_executive_pms.html`** | **Use for PMS** — engine + PRISM only |
| `isze_executive_iam.html` | IAM lookup lab (disclaimed) |
| `isze_executive_dashboard.html` | Combined — banners required |
| `iam_matrix_broadsheet.html` | Older 2-page threat matrix |
| `iam_matrix_plex.html` | Older threat matrix variant |

### Builder (parent folder)

| File | Purpose |
|------|--------|
| `build_executive_dashboard.py` | `--variant all` → three HTML files |
| `run_executive_html.bat` | Build all, open PMS HTML |

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\Tools\autodoc_scraper
python build_executive_dashboard.py
python build_executive_dashboard.py --ituk-uio smmt_car_park
python build_executive_dashboard.py --help
```

---

## 6. External ISZE data (paths in `sources.yaml`)

| Data | Path | Used for |
|------|------|----------|
| **v17 UIO** | `C:\Users\jerom\Desktop\claude\ISZE\UIO\_CURRENT\ISUZU_UIO_Overview_2026_v17.xlsx` | Distributors; sheet 4 = SMMT car park |
| **PMS Calc** | `C:\Users\jerom\Desktop\claude\ISZE\Isuzu\Divers\ISZE_PMS_Coverage_Calculator.xlsx` | Intervals; ITUK 11,900 pilot |
| **PRISM multi-DB** | `C:\Users\jerom\Desktop\claude\ISZE\Data\derived\pms_capture_by_db_year.csv` | All distributors (18 DBs) |
| **ITUK dealer sales** | `C:\Users\jerom\Desktop\claude\ISZE\Isuzu\Sales to Dealers_ITUK_CY2025.xlsx` | ITUK actuals (not pan-ISZE v3 qty) |
| **v3 matrix** | `ISZE_Parts_Intelligence_v3.xlsx` (this folder) | PN prices, CY qty columns |

### ISZE tree (wider audit)

```text
C:\Users\jerom\Desktop\claude\ISZE\
├── Tools\autodoc_scraper\     ← code + HTML previews
├── UIO\_CURRENT\              ← UIO workbooks
├── Isuzu\                     ← PMS Calc, Sales to Dealers_*.xlsx
├── Data\derived\              ← PRISM CSV
└── (other ISZE folders — not all wired to this BI)
```

### Upgrade checklist (no code change)

| You receive | Action |
|-------------|--------|
| New v3 | Replace bundle xlsx or update `paths.v3_pn_matrix` |
| New UIO (v18…) | Update `paths.uio_overview` |
| New PMS parts | Edit `pms_parts_config.yaml` or PMS Calc path |
| Distributor sales | `Sales to Dealers_{DB}_{CY\|FY}{year}.xlsx` under `sales_to_dealers_dir` |
| PRISM export | Replace `pms_capture_by_db_year.csv` |

Restart Streamlit after yaml path changes.

---

## 7. Scrapers (optional)

PMS does **not** need scraper reruns. See `SCRAPE_OPTIONAL.md`. Parent folder still has scraper scripts if you ever want AM price context for IAM.

---

## 8. How pieces connect

```
sources.yaml
    ↓
engine.py ← v3, v17, PMS Calc, PRISM CSV, dealer sales  (authoritative for PMS)
    ↓
bi_shell.py (Streamlit)     build_executive_dashboard.py → isze_executive_pms.html
    │
    └── optional: scraper CSVs → brand/competitor columns only
    └── parent only: iam_scoring.py → isze_executive_iam.html (lookup, disclaimed)
```

---

## 9. Audit quick reference

| Question | Look here |
|----------|-----------|
| Audit closed? | `AUDIT_STATUS.md` |
| Change data paths | `sources.yaml` |
| Live PMS / multi-DB | `bi_shell.py`, `run_bi.bat` |
| UIO / PMS formulas | `engine.py` |
| Executive HTML (PMS) | `..\ _html_previews\isze_executive_pms.html` |
| Rebuild HTML | `..\build_executive_dashboard.py --variant all` |
| IAM T/Q (lookup only) | `..\iam_scoring.py` · `isze_executive_iam.html` |

---

## 10. Production vs legacy

| **Use for audits / daily work** | **Legacy / optional** |
|--------------------------------|------------------------|
| `_HANDOFF_BUNDLE` + `AUDIT_STATUS.md` | `competitive_bi.py`, EU scrapers |
| `isze_executive_pms.html` | `iam_matrix_*.html` |
| Excel/CSV under `ISZE\` | Scraper automation |
| `autodoc_dashboard.py` (IAM tabs) | `isze_executive_dashboard.html` (combined; read banners) |

---

## 11. Agent chat history (Cursor)

Transcripts for this work may be under:

`C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude-ISZE-Tools-autodoc-scraper-HANDOFF-BUNDLE\agent-transcripts\`

(File names are UUIDs — search by date or keywords like “PMS”, “sources.yaml”, “executive”.)
