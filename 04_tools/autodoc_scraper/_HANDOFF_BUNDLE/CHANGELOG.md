# Changelog — ISZE Competitive BI (`_HANDOFF_BUNDLE`)

All notable changes to the handoff bundle and linked executive HTML builder.

## [2026-05-21] — Dealer sales qty bug + KPI validation

- **Critical fix:** `load_ituk_dealer_sales` no longer sums the **PN column** as quantity (caused capture % in billions).
- **`pms_validation.py`** — sanity checks; Streamlit + HTML show **⚠ data error** if capture > 200%.
- Run checks: `python pms_validation.py`

## [2026-05-21] — v3 AIM_Category fix (air intake)

- **17 PNs** in `ISZE_Parts_Intelligence_v3.xlsx`: `Fluids Chemicals` → `Maintenance Service` (filters/elements) or `Intake Exhaust Emission` (hoses/gaskets).
- Backup: `ISZE_Parts_Intelligence_v3.backup_*.xlsx` in bundle folder.
- Refreshed `AIM_Category` in bundle `autodoc_results.csv`, `ks_results.csv`, `mekonomen_results.csv` for overlapping PNs.
- Script: `scripts/fix_v3_aim_air_filters.py` (re-runnable; only touches Fluids + air-intake descriptions).

## [2026-05-20] — Methodology sign-off + model tracker

- **SPEC.md:** Signed decisions (brake qty, Pan-EU scope, PRISM N75_only, per-model PMS path).
- **MODEL_REFINEMENT_TRACKER.xlsx** + `scripts/build_model_refinement_sheet.py`.

## [2026-05-21] — Deloitte audit remediation (complete)

### Second pass (documentation + HTML split)
- **H-4:** `README.md` rewritten — bundle vs parent, no false "removed from disk"
- **H-2:** `SPEC.md` — Decisions table; regex policy documented
- **H-5:** `build_executive_dashboard.py --variant all` → `isze_executive_pms.html`, `isze_executive_iam.html`, `isze_executive_dashboard.html`
- **AUDIT_STATUS.md** — full Deloitte finding register
- **AUDIT_MAP.md** updated for three HTML outputs

### Scraper scope reduced (your direction)
- Removed `SCRAPE_SCHEDULE.md` (no monthly/Task Scheduler push)
- Added `SCRAPE_OPTIONAL.md` — PMS does not depend on scrapers
- Streamlit scrape tab: informational only, no “re-run scrapers” warning

---

## [2026-05-21] — Deloitte audit remediation (code)

### Critical (C-1, C-2)
- **C-1:** ITUK engine tab and **All distributors** PRISM tab now show explicit warnings that `potential_units` (PMS Calc) and `expected_qty` (PRISM, typically `N75_only`) must not be compared (e.g. oil filter ~15× gap).
- PRISM loader exposes `prism_scope`, `prism_uio_source`, and per-row `data_source` from CSV fields.
- **C-2:** Removed hardcoded “SMMT” labels when PRISM says `ituk_dvla_2026`. Renamed `parse_ituk_car_park_uio()` (alias `parse_ituk_smmt_car_park`). UI cites workbook + `uio_source` from file.

### High (H-1 – H-6)
- **H-1:** Default ITUK UIO = `smmt_car_park` in `sources.yaml`. Sidebar: car park vs 11,900 exercise; sheet 1 cohort under Diagnostic expander only.
- **H-2:** `SPEC.md` § Decisions documents description-regex for brake front/rear (SPEC no longer claims AIM-only).
- **H-3:** FX rates moved to `sources.yaml` → `load_fx_rates()`; engine uses yaml FX for scrape normalization.
- **H-4:** `README.md` corrected — legacy IAM files live in **parent** folder; bundle is PMS-authoritative.
- **H-5:** Executive HTML builds **`isze_executive_pms.html`** (engine only) plus combined dashboard with IAM **LOOKUP** disclaimer; see parent `build_executive_dashboard.py`.
- **H-6:** Scrape freshness check in Streamlit (`scrape_freshness()`); stale warning if older than `scrape_max_age_days`.

### Medium / Low
- **M-1:** Car park parser uses sheet 4 §G `2024A` column (removed fragile 15k–35k heuristic fallback except PRISM).
- **M-2:** `over_capture_units` on category view when actual > potential.
- **M-3:** `mileage_source` on KPIs when PMS Calc row missing (defaults flagged).
- **M-4:** `bi_shell` loaders use `sources.yaml` paths only (removed parallel hardcoded `SOURCES` dict).
- **M-6:** Central `normalize_pn()` / `sanitize_scrape_frame()` in `sources_loader.py`.
- **M-7:** Scrape reads sanitize `Status=no_results` and prices &lt; 3 → NaN (legacy CSV 2.0 sentinels).
- **M-8:** `sync_scrape_results.bat` copies parent CSVs into bundle.
- **M-9:** SPEC open questions split into **Decisions** vs still-open items.
- **L:** `.gitignore` for `__pycache__`; `AUDIT_MAP.md` updated; `CHANGELOG.md` added.

### Files touched (bundle)
- `engine.py`, `sources_loader.py`, `sources.yaml`, `bi_shell.py`
- `SPEC.md`, `README.md`, `AUDIT_MAP.md`
- `sync_scrape_results.bat`, `.gitignore`

### Files touched (parent)
- `build_executive_dashboard.py` — `--variant all` writes PMS / IAM / combined HTML; FX from yaml; PRISM banners
- `run_executive_html.bat` — builds all variants, opens `isze_executive_pms.html`

### Documentation completed (same release)
- `README.md` — honest bundle vs parent split (H-4)
- `SPEC.md` — Decisions section + regex policy (H-2)
- `SCRAPE_SCHEDULE.md` — Task Scheduler template (H-6)
- `AUDIT_MAP.md` — three HTML outputs

---

## Prior work (summary)
- Upgradeable `sources.yaml`, multi-DB PRISM tab, CY/FY, ITUK UIO toggles, dealer sales loader, `AUDIT_MAP.md`.
