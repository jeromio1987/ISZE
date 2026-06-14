# Audit remediation status (Deloitte review — 2026-05-21)

Sign-off register for the handoff bundle. **PMS BI is the product; scrapers are optional context only.**

| ID | Finding | Status | Evidence |
|----|---------|--------|----------|
| **C-1** | Engine vs PRISM potential units incomparable (~15×) | **Fixed (UI)** | Warnings on ITUK + All distributors tabs; `prism_scope` / `prism_uio_source` columns; `engine.ENGINE_METHODOLOGY_NOTE` |
| **C-2** | SMMT label vs PRISM `ituk_dvla_2026` | **Fixed (labels)** | `parse_ituk_car_park_uio()`; `data_source` from CSV; no hardcoded SMMT |
| **H-1** | Three UIO bases, no policy | **Fixed** | Default `smmt_car_park` in yaml; `SPEC.md` § Decisions; sidebar policy text |
| **H-2** | Regex vs SPEC | **Fixed** | SPEC documents regex for brake front/rear only |
| **H-3** | FX hardcoded | **Fixed** | `sources.yaml` → `fx_rates`; `load_fx_rates()` |
| **H-4** | README “removed” but parent files exist | **Fixed** | `README.md` bundle vs parent table |
| **H-5** | Two BI surfaces | **Fixed** | `isze_executive_pms.html` (authoritative PMS); IAM split + disclaimers |
| **H-6** | Scrape freshness / automation | **Closed (minimal)** | Optional CSV age caption only — **no scheduled scrape push** (see `SCRAPE_OPTIONAL.md`) |
| **M-1** | Sheet 4 parse heuristic | **Fixed** | Named column `2024A` / `Total ITUK` row |
| **M-2** | Lost units clip hides over-capture | **Fixed** | `over_capture_units` column |
| **M-3** | Mileage default unflagged | **Fixed** | `mileage_source` on KPIs |
| **M-4** | Duplicate hardcoded paths in shell | **Fixed** | Loaders use `sources.yaml` only |
| **M-5** | Deferred imports in engine | **Accepted** | Avoid circular imports; not blocking |
| **M-6** | PN normalize duplicated | **Fixed** | `sources_loader.normalize_pn()` |
| **M-7** | Scrape 2.0 sentinel | **Fixed** | `sanitize_scrape_frame()` on read |
| **M-8** | Stale CSV copies | **Optional** | `sync_scrape_results.bat` — manual only if you re-scrape |
| **M-9** | SPEC open questions | **Partial** | Decisions table added; 5 items still for Jerome |
| **L-1** | `__pycache__` in bundle | **Fixed** | `.gitignore`; not shipped in docs |
| **L-2** | Mixed Python versions | **Documented** | `requirements.txt` note |
| **L-3** | Loose requirements | **Documented** | Lower bounds only; pin when you freeze an environment |
| **L-4** | Scraper ToS risk | **Accepted** | Known; scrapers deprioritised |
| **L-5** | Absolute Windows paths | **Accepted** | `sources.yaml` is the portability surface |
| **L-6** | PR00 in CSV sensitivity | **Accepted** | `.gitignore` pattern note in README |

---

## Safe to use today (PMS)

- Streamlit `run_bi.bat` — **Engine output** and **All distributors** with banners read.
- HTML `isze_executive_pms.html` after `build_executive_dashboard.py --variant all`.
- ITUK external narrative: **car park UIO ~22,389** (`smmt_car_park`), PRISM row for capture — **not** engine ITUK tab potential for the same category comparison.

## Not safe for external claims without your sign-off

| Topic | Owner action |
|-------|----------------|
| PRISM `uio_source` naming (DVLA vs SMMT) | Confirm with PRISM pipeline owner |
| `N75_only` vs whole-fleet export | **Signed:** use N75_only for capture (SPEC) |
| Brake-pad qty interpretation | **Signed:** 1 qty = 1 pad (SPEC) |
| Per-model PMS / mileage | `MODEL_REFINEMENT_TRACKER.xlsx` |
| IAM T/Q / expected loss | Lookup only — `isze_executive_iam.html` |

## Explicitly out of scope (per your direction)

- Expanding scraper coverage, schedules, or automation.
- Rebuilding EU/MA/Oscaro scrapers.

---

## Files to read (in order)

1. `CHANGELOG.md` — what changed in code  
2. `AUDIT_STATUS.md` — this register  
3. `SPEC.md` — decisions + remaining questions  
4. `AUDIT_MAP.md` — where files live  
