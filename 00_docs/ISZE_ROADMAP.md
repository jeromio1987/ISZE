# ISZE — Consolidated roadmap

**Last updated:** 2026-07-14  
**Domain detail:** [`roadmaps/`](roadmaps/) · **Registry:** [`MAP_REGISTRY.yaml`](MAP_REGISTRY.yaml)

> **Numbers:** `../FACTS.md` wins over any deck, memory, or GPT file. Pipeline: green `01_data/derived/_verification_report.json` → `metrics_snapshot.json`.

---

## Live now (PRISM + derived pipeline)

| Capability | Location |
|------------|----------|
| GPS spend per unit | PRISM `pages/2_GPS.py` · `gps_spu_by_distributor.csv` |
| PMS capture (registry + BVP catalogue) | `pages/3_PMS.py` · `pms_capture_by_db_year.csv` |
| Fig-key / PR00 catalogue | `parts_catalog_dimension.csv` · `gps_v2_fig_key.md` |
| GPS × PMS-capture quadrant | `pages/16_AIM_GPS_Matrix.py` · `aim_gps_matrix.csv` (x-axis was AIM pricing risk until 2026-07-17 — it never separated anyone, see `DECISIONS.md`) |
| Decision models | `pages/18_Decision_Models.py` · `wallet_waterfall.csv`, etc. |
| Pipeline verify | `scripts/run_pipeline_and_verify.ps1` |
| PMS assumptions (editable) | `prism/data/pms_capture_assumptions.yaml` |
| Static HTML refresh | `build_isze_dashboard_json.py` + `inject_dashboard_overlays.py` |
| Data integrity audit | `pages/10_Data_Integrity.py` · `mislabelled_sku_audit.csv` |

Run PRISM: `03_analytics/Isuzu/prism/run_prism.ps1` (port **8503**)

---

## Build now

| Item | Blocker | Domain |
|------|---------|--------|
| Interval-aware air vs oil capture | ⚠ shipped 2026-07-02 with **provisional 0.5 air factor** — IML ratio confirmation still open | PRISM |
| SAP fig key on `sales_fact` | ✅ done 2026-07-02 via `parts_catalog_dimension` join (98.9% coverage); SAP column auto-ingested when CY export adds it | Pipeline |
| 2025 UIO in capture | ✅ done — V19 (DVLA-based) confirmed wired 2026-07-03, `uio_proxy_used=False` on all 2025 rows | UIO |
| FY2025 completeness (Jan-Mar 2026 data) | ✅ done 2026-07-03 — `sales_2026tillApril.XLSX` wired in, FY2025 now a complete 12 months | Pipeline |
| CR/RE credit-note/return exclusion (flag H) | ✅ done 2026-07-03, judgment call not ERP-confirmed — see FACTS.md flag H | Pipeline |
| CY2026 AIM dashboard | AIM workbook | HTML |
| Supabase live Master KPIs | Schema + credentials | HTML V4 |
| Discount scraper refresh | Optional (personal promos) | [scrapers](roadmaps/scrapers.md) |
| Dashboard filename renames | Build scripts hardcode vN | [html](roadmaps/html.md) · [`CANONICAL.md`](CANONICAL.md) |
| Tender Monitor Task Scheduler | ✅ live `ISZE Tender Monitor` (verified 2026-07-26) | [scrapers](roadmaps/scrapers.md) |
| Competitive pricing refresh scheduler | ✅ live `ISZE_PMS_IAM_Refresh` — do **not** also import spare XML; manual refresh 2026-07-26 after interrupt | [scrapers](roadmaps/scrapers.md) |
| LCV bucket generation-aware interval split | Blocked — need D-Max generation/registration-year cutoffs (RG/RG21/RT56/RT88_93 → model year). 4 OEM Isuzu maintenance schedules read 2026-07-15: standard/older D-Max (4JJ3/RZ4E, incl. RT56="2013 TF series") = 20,000km oil interval, confirms current `lcv=1.0 svc/yr`. Newest gen (RG21, RZ4F-TC **with SCR**, Europe/Israel) = 15,000km → ~1.33 svc/yr. PDF metadata has no build-year (all "Print to PDF" today from Isuzu ETM); only RT56 self-labels a year. Need Jerome/IML to supply which years/chassis codes are SCR vs non-SCR before this can become a real registration-year-weighted bucket in `pms_capture_assumptions.yaml` (same mechanism as existing `country_overrides`) | PRISM / PMS |
| Brake front/rear split categories never get real actual sales | ✅ **Fixed 2026-07-16 — option (b), Jerome's call.** `brake_pad_front/rear` + `brake_shoe_front/rear` dropped from `wear_factor` (`pms_capture_assumptions.yaml`); parent `brake_pad`/`brake_shoe` retained and now restated explicitly in the YAML. The 2026-07-15 diagnosis understated it: the parents were **already** in `P1_CATEGORIES` via `_DEFAULT_WEAR` in `modules/pms_capture_config.py` (the YAML is merged **onto** that dict, not substituted for it), so brake demand was estimated **three times** over one parc (parent 0.5 + front 0.5 + rear 0.5) — the drag was phantom *expected* demand in the denominator, not the empty numerators. Option (a) was rejected on that basis: it would have filled the numerators while leaving the denominator tripled, converting a visible zero row into an invisible wrong rate. Rationale for (b): front/rear is not a unit of commercial action (there is no front-pad campaign), and the only market with real data (ITUK, IML slide 2026-07-14) has front+rear replaced together as one job — not independent wear cycles. Verified by re-run: P1 3,888 → 3,024 rows (864 = 4 cats × 72 × 3 line_types), all surviving actuals byte-identical, network expected-weighted capture CY2025 **23.8% → 32.0%** (`total` line_type; matches the 31.9% quoted 2026-07-15 within data drift), ITUK oil-filter anchors unchanged, 40/40 prism tests pass. | PRISM / PMS |
| `country_overrides.factors` is dead config for every bucketed distributor | **✅ FIXED 2026-07-21 — Jerome approved via "do all" on Safety&capital top-10.** `modules/pms_engine.expected_by_category_bucketed()` now reads `cfg["factor_overrides"]` before falling back to `LCV_BUCKET_FACTOR_OVERRIDES`/global factors (same override-replaces-default pattern as `scripts/build_bvp_p0_p1.py::_expected_qty_for_db()`); the legacy single-scope loop in `calculate_pms_capture()` got the identical fix since it never applied `factor_overrides` either. Verified on real data: ITUK brake_pad CY2025 expected 5,840.1 → **4,672.1** (0.5 → 0.4 denominator), capture **58.3% → 72.8%** (registry-only actuals 3,402 units). 61/61 prism tests pass. `country_overrides.services_per_year` was already live via `BUCKET_SERVICES_PER_YEAR_OVERRIDES` (UTI) — untouched. See `DECISIONS.md` 2026-07-21. The units question below (0.4 vs 0.8) is still open — this fix makes the *configured* 0.4 finally take effect, it does not resolve whether 0.4 is the right number. | PRISM / PMS |
| ITUK brake wear factor — is 0.4 or 0.8 the right basis? | **Open, never measured.** The ITUK 0.4 derives as an interval ratio (40,000/100,000 km), independent of axle count, so it carried over unchanged when the front/rear split was dropped. But the IML slide describes replacement as one paired "2item" job covering both axles — if a single `brake_pad` unit is one axle's set, the merged factor is arguably **0.8**, and ITUK brake capture currently reads ~2x optimistic. This is a units question about what one `brake_pad` unit represents; it needs IML confirmation, not a guess. Currently moot in the output — see the dead-config row above. | PRISM / PMS |

---

## Domain roadmaps

| Domain | File | Status |
|--------|------|--------|
| HTML dashboards | [`roadmaps/html.md`](roadmaps/html.md) | V3 overlay + V4 Supabase |
| Scrapers | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) | Tender path fixed; refresh scheduler XML ready; Autodoc retired from health check |
| GPS / fig-key / AIM | [`roadmaps/gps.md`](roadmaps/gps.md) | V2 enrichment in PRISM |
| Jarvis / tools | [`roadmaps/tools.md`](roadmaps/tools.md) | V2 data-out-of-code |

---

## Data integrity (do not quote externally until closed)

See `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md` — priority: interval-aware PMS (C), returns confirmation (H).

---

## Workspace cleanup

Open decisions (UI primary for external share, ISZE_Dashboard merge): [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md)
