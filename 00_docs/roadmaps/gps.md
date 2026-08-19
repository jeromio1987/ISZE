# GPS dashboard — roadmap

**Last updated:** 2026-08-18  
**Hub:** [`ISZE_ROADMAP.md`](../../ISZE_ROADMAP.md)  
**Live app:** PRISM `pages/2_GPS.py` · `03_analytics/Isuzu/gps_dashboard/` (legacy Dash)

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

- Bulk PN → fig key from SAP / IE40 PR00 column
- EPC basket rows into overrides
- Wire Part Explorer to `parts_catalog_dimension`
- Optional rollups by `fig_key` × distributor × year

**PMS capture (PRISM — do not use 1.5 svc/yr):**

- Expected: **UIO × 0.5 svc/yr × 70%**
- ITUK UIO override: **22,389** (DVLA Mar 2026)
- Capture **>100%** allowed (cross-OEM, multi-segment PNs)

---

## V3 — AIM integration & strategic scoring — **superseded 2026-08-18**

**Do not build this.** The scoring layer (Strategic Score, Pricing Risk Map, AIM×GPS as a risk axis) failed in production (2026-07-17) and again as a fitted model (2026-08-18). Classification stays; the quadrant stays as **GPS × PMS total capture**.

Replacement programme: [`aim_prism_reinvention.md`](aim_prism_reinvention.md).

---

## V2.5 — Lubricants module (optional)

Lubricant spend/unit metric if IML go-ahead + volume data available.

---

## Notes

- PMS is highest-priority V2 feature (ITUK pilot, oil filter capture gap)
- Fig-key master is gating dependency for V2 enrichment
- Power BI CSV export available from V1
