# GPS V2 — Fig-key catalogue layer

**Status:** 2026-09-14 — `pr00_classification.csv` empty `fig_key` filled from IE40 parquet (**158** PNs). `parts_catalog_dimension` **161,325 / 164,969** with fig_key (97.8%). Overrides file is header-only.

PRISM already ships **GPS (spend/unit)** and **PMS capture** via the 55-PN registry and BVP catalog.
GPS roadmap “V2” in `gps_dashboard/GPS_Dashboard_Roadmap.md` assumed PMS did not exist yet — this doc
describes the **fig-key enrichment** that sits on top.

---

## What “fig key” means

Isuzu EPC groups parts under **FIG-KEY** codes (e.g. `050-002` oil filter, `041-002` fuel filter).
Power BI (`FIG KEY CLASSIFICATION`) uses the same taxonomy.

| Fig key | PMS category | BVP sheet |
|---------|--------------|-----------|
| 050-002 | oil_filter | OIL FILTER |
| 041-002 | fuel_filter | FUEL FILTER |
| 130-006 | air_filter | AIR FILTER |
| 873-042 | urea_filter | UREA FILTER |

---

## Data layers (do not conflate)

| Layer | File | Question |
|-------|------|----------|
| **Fleet (UIO)** | UIO Excel / DVLA | How many vehicles? (N35 + N75 + F-series …) |
| **GPS** | `gps_spu_by_distributor.csv` | € parts sales per vehicle in parc |
| **PMS capture** | `pms_capture_by_db_year.csv` | Registry qty vs **N75 pilot** expected demand |
| **Fig-key catalogue** | `parts_catalog_dimension.csv` | PN → fig key + PR00 family/group |

ITUK sells PMS to **other OEMs** (e.g. DAF) and **multiple segments** — billing stays in actuals;
capture above 100% vs the N75 UIO denominator is an **interpretation flag**, not a reason to drop sales.

---

## Build pipeline

Included in `scripts/run_pipeline_and_verify.ps1` after P0:

```powershell
cd Projects\Isuzu\prism
python scripts\build_pr00_classification.py    # needs IE40 PR00 xlsx when refreshed
python scripts\build_bvp_p0_p1.py
python scripts\build_fig_key_dimension.py
python scripts\build_sales_by_fig_key.py
```

**PRISM GPS → Part Explorer** — **done** in `pages/2_GPS.py` (Fig Key + PMS Category from `parts_catalog_dimension`). No Mode A rebuild.

When `sales_by_db_fig_key_year.csv` exists, a per-distributor fig-key rollup table appears below the top parts list.

**Outputs:** `01_data/derived/parts_catalog_dimension.csv`

**Inputs:**

| Source | Role |
|--------|------|
| `pr00_classification.csv` | ~165k PNs → PR00 family/group |
| `bvp_pn_dimension.csv` | BVP catalog + PMS flags |
| `PMS_PN_REGISTRY` | 55-PN pilot |
| `data/fig_key_taxonomy.yaml` | Fig key ↔ PMS category |
| `data/fig_key_pn_overrides.csv` | EPC hand basket (wins over defaults) |

---

## Next steps (V2 backlog)

1. **Expand overrides** — still blocked: EPC JSON is edition/family not fig-key; Snap-on blocks bulk BVP (`pms-pilot/BVP_FINDING.md`). Header-only `fig_key_pn_overrides.csv` is in place; do not invent rows.
2. ~~**Ingest SAP/PBI fig key**~~ — **done 2026-07-02**: `sales_fact` now carries `fig_key` + `fig_key_source` (`build_sales_fact_from_cy.py`). CY export `FIG KEY CLASSIFICATION` is ingested directly when present (`fig_key_source = sap`); current exports lack the column, so fig_key is joined from `parts_catalog_dimension` (`fig_key_source = catalog`, 98.9% row coverage). Verified by `sales_fact.fig_key` check (min 90%).
3. **IE40 empty-key fill** — **done 2026-09-14**: 158 existing PR00 rows; catalog rebuild fills from parquet if CSV is stale.
4. **GPS Part Explorer** — **done** (wired; do not Mode A rebuild).
5. **Sales by fig key** — `sales_by_db_fig_key_year.csv` (GPS Part Explorer, single distributor).
6. **AIM × GPS matrix** — `aim_gps_matrix.csv` · Network Intelligence tab (page 16 archived).

---

## Related

- `scripts/build_pr00_classification.py` — PR00 + Fig No./Key No. → fig_key
- `pages/2_GPS.py` — Part Explorer (PR00 + registry + keywords)
- `docs/metric_dictionary.md` — capture vs fleet scope
