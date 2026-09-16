# ISZE derived pipeline verification

**Generated:** 2026-08-18T15:12:22Z
**Data root:** `C:\Users\jerom\Desktop\claude\ISZE\01_data`

| Pass | Warn | Fail |
|------|------|------|
| 108 | 0 | 0 |

## Checks

- ✅ **raw.raw/sales/CY2023-2024.XLSX** — Found raw/sales/CY2023-2024.XLSX
- ✅ **raw.raw/sales/CY2024-2025.XLSX** — Found raw/sales/CY2024-2025.XLSX
- ✅ **raw.raw/sales/sales_2026tillApril.XLSX** — Found raw/sales/sales_2026tillApril.XLSX
- ✅ **raw.raw/reference/BVP PARTS CATALOG.xlsx** — Found raw/reference/BVP PARTS CATALOG.xlsx
- ✅ **derived.sales_fact.parquet** — Found sales_fact.parquet
- ✅ **derived.bvp_pn_dimension.csv** — Found bvp_pn_dimension.csv
- ✅ **derived.genuine_bvp_crossref.csv** — Found genuine_bvp_crossref.csv
- ✅ **derived.sales_with_crossref.parquet** — Found sales_with_crossref.parquet
- ✅ **derived.substitution_by_pair_year.csv** — Found substitution_by_pair_year.csv
- ✅ **derived.substitution_by_db_year.csv** — Found substitution_by_db_year.csv
- ✅ **derived.pms_capture_by_db_year.csv** — Found pms_capture_by_db_year.csv
- ✅ **derived.mix_genuine_bvp_by_family.csv** — Found mix_genuine_bvp_by_family.csv
- ✅ **derived.mix_genuine_bvp_pms.csv** — Found mix_genuine_bvp_pms.csv
- ✅ **derived.db_benchmark_mix.csv** — Found db_benchmark_mix.csv
- ✅ **derived.gps_spu_by_distributor.csv** — Found gps_spu_by_distributor.csv
- ✅ **derived.pms_summary_by_db.csv** — Found pms_summary_by_db.csv
- ✅ **derived.gps_spu_by_family.csv** — Found gps_spu_by_family.csv
- ✅ **derived.gps_spu_pms.csv** — Found gps_spu_pms.csv
- ✅ **derived.aim_exposure_by_db_year.csv** — Found aim_exposure_by_db_year.csv
- ✅ **derived.aim_bvp_family_risk.csv** — Found aim_bvp_family_risk.csv
- ✅ **derived.pms_opportunity_matrix.csv** — Found pms_opportunity_matrix.csv
- ✅ **derived.network_percentile.csv** — Found network_percentile.csv
- ✅ **derived.vor_airfreight_risk.csv** — Found vor_airfreight_risk.csv
- ✅ **derived.vor_seasonality.csv** — Found vor_seasonality.csv
- ✅ **derived.vor_profile.csv** — Found vor_profile.csv
- ✅ **derived.capture_trajectory.csv** — Found capture_trajectory.csv
- ✅ **derived.part_lifecycle.csv** — Found part_lifecycle.csv
- ✅ **derived.revenue_concentration.csv** — Found revenue_concentration.csv
- ✅ **derived.revenue_waterfall.csv** — Found revenue_waterfall.csv
- ✅ **derived.price_premium.csv** — Found price_premium.csv
- ✅ **derived.basket_correlation.csv** — Found basket_correlation.csv
- ✅ **derived.substitution_timeline.csv** — Found substitution_timeline.csv
- ✅ **derived.capture_recovery_model.csv** — Found capture_recovery_model.csv
- ✅ **derived.bvp_addressable_basket.csv** — Found bvp_addressable_basket.csv
- ✅ **derived.ituk_pms_pn_audit.csv** — Found ituk_pms_pn_audit.csv
- ✅ **derived.parts_catalog_dimension.csv** — Found parts_catalog_dimension.csv
- ✅ **derived.sales_by_db_fig_key_year.csv** — Found sales_by_db_fig_key_year.csv
- ✅ **derived.aim_gps_matrix.csv** — Found aim_gps_matrix.csv
- ✅ **config.data_status** — Core data_status OK
- ✅ **config.bvp_catalog** — BVP catalog at BVP PARTS CATALOG.xlsx
- ✅ **sales_fact.row_count** — Row count 477,505 (expected ~477,505, Δ 0.00%)
- ✅ **sales_fact.schema** — Schema OK
- ✅ **sales_fact.years** — Years present: [2023, 2024, 2025, 2026]
- ✅ **sales_fact.saty** — SaTy populated on 100.0% of rows (min 95.0%)
- ✅ **sales_fact.fig_key** — fig_key populated on 98.6% of rows (min 90.0%)
- ✅ **sales_fact.unmapped** — UNMAPPED 4 (0.00%) after distributor map
- ✅ **p0.rows** — Dimension 919 PNs
- ✅ **p0.pms_flagged** — PMS-flagged 496
- ✅ **p0.line_type** — line_type values OK
- ✅ **p0b.rows** — Crossref 544 pairs
- ✅ **p0b.pair_source** — pair_source OK
- ✅ **p0b.catalog_pairs** — Catalog-derived pairs 517
- ✅ **p0b.unique_pairs** — Duplicate (genuine,bvp) keys: 0
- ✅ **bvp_addr.rows** — Addressable basket 2,272 rows
- ✅ **bvp_addr.schema** — Schema OK
- ✅ **bvp_addr.distributors** — 22 distributors (min 20)
- ✅ **bvp_addr.subgroups** — 29 product subgroups (min 22)
- ✅ **bvp_addr.ituk_penetration** — ITUK BVP penetration 73/134 (54%)
- ✅ **p1.rows** — PMS capture 3,024 rows
- ✅ **p1.schema** — Schema OK
- ✅ **p1.line_type** — line_type OK
- ✅ **p1.capture_cap** — All total capture_rate ≤ 10.0
- ✅ **p1.ituk.uio** — ITUK uio_units [np.int64(23068)] (expected 23068)
- ✅ **p1.ituk.oil_filter.2024** — ITUK oil_filter 2024 capture 83.5% (band 82%–92%)
- ✅ **p1.ituk.oil_filter.2025** — ITUK oil_filter 2025 capture 116.4% (band 115%–128%)
- ✅ **p1.distributor_count** — PMS capture 18 distributors @ complete 2025 (min 18)
- ✅ **pms.summary.rows** — pms_summary_by_db 18 distributors (min 18)
- ✅ **pms.summary.complete_year** — pms_summary_by_db year [2025] == complete 2025
- ✅ **pms.summary.not_partial** — pms_summary_by_db is a complete billing year
- ✅ **pms.summary.schema** — PMS summary schema OK
- ✅ **gps.warranty.schema** — GPS warranty columns OK
- ✅ **gps.warranty.coverage** — CY2025 warranty on 18 DBs (min 17)
- ✅ **gps.warranty.sales_bounds** — ex-warranty sales ≤ total
- ✅ **contract3.rows** — PMS opportunity matrix 1,008 rows
- ✅ **contract3.schema** — Schema OK
- ✅ **contract3.capture_cap** — All capture_rate_total ≤ 10.0
- ✅ **contract3.tam_eur** — tam_eur ≥ 1.0 where avg_sp_eur > 0
- ✅ **contract10.rows** — Network percentile 409 rows
- ✅ **contract10.schema** — Schema OK
- ✅ **contract10.metrics** — All metrics present
- ✅ **contract10.percentile_range** — percentile_rank in [0, 100] (actual 0.0–100.0)
- ✅ **contract16.rows** — ITUK PMS PN audit 274 rows
- ✅ **contract16.schema** — Schema OK
- ✅ **contract16.distributor** — All rows ITUK
- ✅ **contract16.oil_filter.2023** — ITUK oil_filter 2023: 11 PNs (min 3)
- ✅ **contract16.oil_filter.2024** — ITUK oil_filter 2024: 10 PNs (min 3)
- ✅ **contract16.oil_filter.2025** — ITUK oil_filter 2025: 7 PNs (min 3)
- ✅ **contract16.oil_filter.2026** — ITUK oil_filter 2026: 6 PNs (min 3)
- ✅ **figkey.catalog.rows** — parts_catalog_dimension 164,969 rows
- ✅ **figkey.catalog.coverage** — PNs with fig_key: 161,191 (97.7%, min 95%)
- ✅ **figkey.catalog.registry_fig** — Registry PNs with fig_key: 65 (min 35)
- ✅ **figkey.sales.rows** — sales_by_db_fig_key_year 75,781 rows
- ✅ **figkey.sales.mapped** — Mapped fig_key rows: 75316 (min 10)
- ✅ **aim_gps.rows** — AIM×GPS matrix 89 rows
- ✅ **aim_gps.quadrants** — Quadrant values OK
- ✅ **contract.vor_airfreight_risk** — vor_airfreight_risk 502 rows
- ✅ **contract.vor_seasonality** — vor_seasonality 3,127 rows
- ✅ **contract.vor_profile** — vor_profile 228 rows
- ✅ **contract.capture_trajectory** — capture_trajectory 1,460 rows
- ✅ **contract.part_lifecycle** — part_lifecycle 505 rows
- ✅ **contract.revenue_concentration** — revenue_concentration 260 rows
- ✅ **contract.revenue_waterfall** — revenue_waterfall 228 rows
- ✅ **contract.price_premium** — price_premium 419 rows
- ✅ **contract.basket_correlation** — basket_correlation 2,123 rows
- ✅ **contract.substitution_timeline** — substitution_timeline 502 rows
- ✅ **contract.capture_recovery_model** — capture_recovery_model 252 rows
- ✅ **contract.distributor_geo** — distributor_geo 23 rows
- ✅ **prism.bvp_bundle** — BVP dashboard bundle ready

## Claude / Cursor workflow

1. Agent runs builds (`run_pipeline_and_verify.ps1` or individual `build_*.py`).
2. This script runs automatically at the end.
3. **Claude reads** `_verification_report.md` before claiming success.
4. On any ❌, fix and re-run — do not present numbers from a failed build.
