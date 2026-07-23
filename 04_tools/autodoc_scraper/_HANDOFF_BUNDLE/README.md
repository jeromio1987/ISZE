# ISZE PMS Intelligence — Handoff Bundle

**Product:** PMS analytics (UIO, lost sales, PRISM multi-DB) — **not** the Autodoc scraper and **not** IAM scoring.

**Naming logic:** `PRODUCT_LOGIC.md` · **where to click:** `DASHBOARD_MAP.md`

**Authoritative for PMS:** this folder (`bi_shell.py` + `engine.py` + `sources.yaml`).  
**IAM lookup lab:** parent `run_dashboard.bat` · **scraping only:** parent `autodoc_scraper.py` etc.

---

## What's in this bundle

### BI engine + shell (use these for PMS claims)
- `bi_shell.py` + `bi_display.py` — Streamlit BI (slim tables, charts; PRISM ranked view)
- `engine.py` — PMS lost sales, UIO scope, category allocation
- `sources.yaml` + `sources_loader.py` — all data paths and FX rates
- `pms_parts_config.yaml` — optional PMS interval overrides
- `run_bi.bat` — launcher

### Reference docs
- `PRODUCT_LOGIC.md` — **PMS vs IAM vs scraper (read first)**
- `pms_validation.py` — run before trusting KPIs: `python pms_validation.py`
- `DASHBOARD_MAP.md` — Streamlit + HTML launchers
- `AUDIT_STATUS.md` — audit sign-off register
- `AUDIT_MAP.md` — file locations
- `CHANGELOG.md` — code change log
- `SPEC.md` — PMS engine contract + decisions
- `MODEL_REFINEMENT_TRACKER.xlsx` — per-model refinement checklist (regen: `python scripts/build_model_refinement_sheet.py`)
- `SCRAPE_OPTIONAL.md` — scraper CSVs are **not required** for PMS

### Optional (scrapers — do not need to run for PMS)
- Copied scraper scripts/CSVs if you want competitor price context; `sync_scrape_results.bat` only if you re-scrape in parent

### Source data
- `ISZE_Parts_Intelligence_v3.xlsx` (local copy)
- External paths in `sources.yaml`: v17 UIO, PMS Calc, PRISM CSV, dealer sales

---

## Bundle vs parent folder (important)

| Location | Role |
|----------|------|
| **`_HANDOFF_BUNDLE/`** | PMS engine — numbers safe for leakage analysis **if you respect scope banners** |
| **`../` (parent)** | Legacy IAM stack still on disk: `iam_scoring.py`, `iam_brand_tiers.csv`, `substitution_probability.csv`, `autodoc_dashboard.py`, `html_export.py`, `competitive_bi.py` |

The parent files were **removed from this bundle** to avoid mixing methodologies. They were **not deleted from disk**. Executive HTML can still load them for **lookup / exploration only**.

---

## ITUK UIO policy (default)

| Basis | ~Units | When to use |
|-------|--------|-------------|
| **Car park (default)** | **22,389** | PRISM alignment, external / ITUK narrative (`smmt_car_park`) |
| PMS Calc Step 2 | 11,900 | Internal fleet exercise only (`pms_calc`) |
| v17 sheet 1 | ~121k | Diagnostic only — not car park |

PRISM `uio_source` (e.g. `ituk_dvla_2026`) is shown verbatim — confirm with PRISM owner vs v17 sheet 4 text.

---

## PRISM vs ITUK tab (do not compare)

- **ITUK tab:** `potential_units` = UIO × PMS Calc frequency (whole-fleet assumptions).
- **All distributors:** `expected_qty` from PRISM — usually **`N75_only`**.
- Same category can differ by ~15× (e.g. oil filter). UI shows warnings; see Deloitte audit in `CHANGELOG.md`.

---

## Executive HTML (parent folder)

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper
python build_executive_dashboard.py --variant all
```

| Output | Use |
|--------|-----|
| `_html_previews/isze_executive_pms.html` | **PMS only** — engine + PRISM |
| `_html_previews/isze_executive_iam.html` | IAM lookup lab (disclaimed) |
| `_html_previews/isze_executive_dashboard.html` | Combined — read banners first |

Or: `run_executive_html.bat` (opens PMS HTML by default).

---

## How to run Streamlit

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper\_HANDOFF_BUNDLE
run_bi.bat
```

Scraper CSVs are optional — see `SCRAPE_OPTIONAL.md`.

---

## Upgrading data

Edit `sources.yaml` only, then restart `run_bi.bat`. See `AUDIT_MAP.md` for path list.

---

## Confirmed dead scrapers (parent only)

Autodoc EU/DE, Oscaro — **Cloudflare Turnstile blocks every request** (100% no_results, 200-328/200-328 PNs); a playwright-stealth retry (`diagnose_stealth.py`) was already tried and still blocked. This is not a coverage gap — the sites were never actually queried. Mister Auto returns an empty response body (different failure mode, not confirmed as bot-blocking). Evidence in parent `_diag/` and `_diag_stealth/`.
