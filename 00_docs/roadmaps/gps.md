# GPS dashboard — roadmap

**Last updated:** 2026-09-14
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) — open items also appear in the hub queue (§1 items 5–8)
**Live app:** PRISM `pages/2_GPS.py` (port 8503, canonical) · `03_analytics/Isuzu/gps_dashboard/` legacy Dash — **frozen, do not build on it**

**Open here:** interval-aware air factor still provisional (hub item 5) · LCV generation split blocked on chassis/reg-year cutoffs (hub item 7). **Fig-key V2 remainder (hub item 8) — 2026-09-14 slice done** (IE40 fill 158 empty keys; Part Explorer already wired; no Mode A rebuild).

---

## V1 (delivered Apr 2026)

GPS / Spend per Unit baseline dashboard:

- Sales aggregation 2022–2026 YTD across ~23 ISZE distributors
- Spend per Unit = Net Sales EUR / UIO (year-matched)
- ITUK/IUK and UTI/UMI split by CV/LCV segment
- Traffic light thresholds: >€150 / €50–€150 / <€50
- Excel + CSV export for Power BI

---

## V2 — Fig-key catalogue + PRISM integration

**Status (Jun 2026):** PMS capture + GPS live in **PRISM**. V2 here means **fig-key enrichment**.

**Implemented:**

- `build_fig_key_dimension.py` → `parts_catalog_dimension.csv`
- `fig_key_taxonomy.yaml` + `fig_key_pn_overrides.csv`
- `build_pr00_classification.py` → `pr00_classification.csv`
- Spec: `prism/docs/gps_v2_fig_key.md`

**Still to add:**

- ~~Bulk PN → fig key from SAP / IE40 PR00 column~~ — **done 2026-09-14**: filled **158** empty `fig_key` on existing `pr00_classification.csv` rows from `pricing_pr00_ie40.parquet` (`fig_no`/`key_no`). Family/group kept. No flood of new PNs. Same fill is wired into `fig_key_catalog.build_parts_catalog_dimension` so a catalog rebuild is self-contained.
- ~~EPC basket rows into overrides~~ — **header only.** `data/fig_key_pn_overrides.csv` exists with `part_number,fig_key,source`. EPC basket JSON (`pms-pilot/epc_results_merged.json`) has edition/family, not fig-key. Snap-on blocks bulk BVP (`pms-pilot/BVP_FINDING.md`). Do not invent override rows.
- ~~Wire Part Explorer to `parts_catalog_dimension`~~ — **done** in `pages/2_GPS.py` (Fig Key / PMS Category columns + fig-key rollup). No Mode A rebuild.
- Optional rollups by `fig_key` × distributor × year — `sales_by_db_fig_key_year.csv` already exists for a single distributor in Part Explorer.

**PMS capture (PRISM — do not use 1.5 svc/yr):**

- Expected: **UIO × 0.5 svc/yr × 70%** (N75 0.5 / LCV 1.0 — bucketed)
- **ITUK UIO: two lanes, never blend them.** PRISM capture lane = **23,068** (`verification_fixtures.yaml` + `facts_anchor.yaml`, confirmed 2026-07-17). The IML / `iml_v7_ituk_cy2025.yaml` lane keeps **22,389** (DVLA Mar 2026). Do not "fix" one to match the other — `DECISIONS.md` 2026-07-17, `DATA_MANIFEST.md` §7
- Capture **>100%** allowed (cross-OEM, multi-segment PNs)
- Headline is **total** capture, not per-category

---

## V3 — AIM integration & strategic scoring — **superseded 2026-08-18**

**Do not build this.** The scoring layer (Strategic Score, Pricing Risk Map, AIM×GPS as a risk axis) failed in production (2026-07-17) and again as a fitted model (2026-08-18). Classification stays; the quadrant stays as **GPS × PMS total capture** and now lives as a tab in `pages/network_intelligence.py` (source archived to `pages/_archive/16_AIM_GPS_Matrix.py`, 2026-08-20).

Replacement programme: [`aim_prism_reinvention.md`](aim_prism_reinvention.md).

---

## V2.5 — Lubricants module (optional)

Lubricant spend/unit metric if IML go-ahead + volume data available.

---

## Notes

- PMS is highest-priority V2 feature (ITUK pilot, oil filter capture gap)
- Fig-key master is gating dependency for V2 enrichment
- Power BI CSV export available from V1
