# BVDB Power BI data pack — how to load

**Meeting:** BVDB x Jerome — Power BI enrichment
**Pack date:** 2026-09-22
**What this is:** trucks in service (UIO) plus GPS, PMS and AIM tables that hang off your existing SAP sales / order / pricing model.
**What this is not:** no SAP line billing dump, no order detail, no price-list or pricing-simulation files. You already have those from SAP.

---

### Hard caveat — the 2026 rows are a part year

Every 2026 row in this pack covers **January to August only** — eight months, not twelve. The last
billing date in the source data is 2026-08-31. This applies to GPS (`02_GPS/`), PMS (`03_PMS/`) and
AIM (`04_AIM/`).

- **Do not compare a 2026 figure with a full-year 2025 figure.** Eight months against twelve reads
  as a decline that did not happen.
- `gps_spu_by_distributor.csv` now carries `period_basis` (`full_year` or `partial_year`) and
  `coverage_note`. Filter on `period_basis` rather than on the year alone. (The UIO files do not
  carry `period_basis`; they mark the same thing with `is_actual` / `is_estimate` / `is_forecast` —
  see section 4.)
- On the 2026 rows, `gps_capture_vs_max` and `gps_capture_ex_warranty_vs_max` are intentionally
  **empty** and `traffic_light_v9` reads `unknown`: a part-year figure divided by the full-year
  target is not a capture rate, so we do not show one.
- `max_spend_eur` (the target), `total_sales_eur`, `uio_units` and `spend_per_unit_eur` are
  unchanged. The per-truck figure is correct for the eight months it covers; it is the comparison
  with a full year that is not.

For a like-for-like read, compare 2026 with **January–August 2025**.

### What the GPS rows exclude

`gps_spu_by_distributor.csv` covers **parts billing only**. Non-parts payments — service fees and
demurrage — are excluded at source: about **EUR 178,453** of 2026 billing across a handful of
lines. Those Sold-to accounts are flagged `network_role = excluded_non_parts` in
`01_UIO/dim_distributor.csv`, so you can see the exclusion rather than having to infer it.

This is deliberate, and it does not flatter any market: no distributor's figure is increased by
the exclusion, and no row is withheld.

---

## 1. Load order (Get Data → Text / CSV)

1. `01_UIO/dim_distributor.csv` — bridge from SAP **Sold-to** (`sold_to_sap`) to `distributor_code`
2. `01_UIO/fact_uio_by_distributor_year.csv` — start here for euro-per-truck measures
3. `01_UIO/fact_uio_by_market_type_year.csv` — detail when you need class / market split
4. `01_UIO/uio_overrides_known.csv` — **apply before publishing IUK 2026**
5. Then GPS (`02_GPS/`), PMS (`03_PMS/`), AIM (`04_AIM/`)

Encoding is UTF-8 with BOM. First row = headers.

Optional (documentation only, do not put in the model relationship path):
- `fact_uio_notes_optional.csv`
- `uio_ld_n35_share_notes_optional.csv`

---

## 2. Relationships (star)

| From | To | Keys |
|------|-----|------|
| Your SAP sales (already in PBI) | `dim_distributor` | Sold-to → `sold_to_sap` |
| `dim_distributor` | all pack facts | `distributor_code` |
| UIO / GPS / PMS / AIM facts | each other | `distributor_code` + `year` |
| PMS / GPS PMS / AIM mix PMS | `dim_pms_category` | `pms_category` |

**Before you join on `year`, filter on `period_basis`.** The pack's 2026 rows cover January–August
only, so `year` alone will line eight months up against twelve (see the caveat at the top).

Cardinality tip: `fact_uio_by_distributor_year` is one row per distributor x year — safe many-to-one from sales if you aggregate sales to the same grain first.

---

## 3. Entity rules (do not blend)

- **UTI ≠ UMI** — two Israel distributors. Separate `distributor_code`, separate Sold-to (1799 vs 1797). Never average into one "Israel".
- **IUK ≠ ITUK** — LCV vs CV UK. Separate fleets, separate sales.
- **IBX / BELGIUM** — Sold-to 90 maps to `BELGIUM` in this pack; GPS label may say IBX.

---

## 4. UIO — what you did not have

**UIO = trucks in service** (parc / units in operation), not registrations alone.

- Source extract: ISZE UIO workbook v19 → derived `uio_by_market_type_year`
- Years: 1990–2030. Use `basis` / `is_actual` / `is_estimate` / `is_forecast` to filter.
- `uio_ld_n35_share.csv` — share of ~3.5 t trucks inside LD fleets (matters for spend-per-truck rates).

### Hard caveat — IUK 2026

| | Value |
|--|------:|
| Value in the fact CSV (V19 forecast) | **49,280** |
| Jerome locked figure (V20, 2026-07-30) | **44,926** |

Until the workbook is rebuilt, for IUK x 2026 use `uio_overrides_known.csv` (`locked_value`). Do not publish 49,280 as the official IUK 2026 fleet.

### Hard caveat — all forecast years 2026-2030 (added 2026-09-22)

The 2026-2030 rows in `fact_uio*` inherit the V19 forecast rule, which **overstates the fleet** by roughly **8-9% in 2026 rising to 38-46% by 2030**. The rule step was changed in June 2026 to a flat 3%-per-year scrappage, contradicting the survival curve the same workbook uses for 1990-2025 (it implies an average truck life near 33 years against ~9.8-10.2 years everywhere else). A rebuild is in progress and an independent verification harness has already convicted the current file on **7 of 10 checks**, including 14 rows that switch method mid-series and 15 rows still carrying the 3% signature.

**Two independent recomputes disagree at the top end** (7.8%→37.7% in the original spec, 9.0%→45.7% from the harness, the difference being the per-year plan profile, which is not recoverable from the value-only forecast cells). Quote the range, not a single figure, until the rebuild settles it.

- **Safe to use as-is:** 1990-2025 rows (filter `is_actual` / `is_estimate`).
- **Use with the caveat or wait:** 2026-2030 rows (filter `is_forecast`).
- **Never use** a forecast-year fleet as a denominator for spend per truck, coverage or capture without saying it is pre-rebuild.
- `uio_overrides_known.csv` carries the locked IUK 2026 value and is the approved override mechanism.

Do not publish any forecast-year UIO figure from this pack until the rebuilt workbook is released.

---

## 5. GPS — labels for the model

In Power BI **display names**, use:

| Prefer | Avoid |
|--------|--------|
| trucks in service / UIO | — |
| parts billed (€) | wallet |
| target spend per truck / target spend ceiling | wallet € |
| price index / reference dealer price | street |

File `02_GPS/target_spend_waterfall.csv` still has technical column names like `theoretical_wallet_eur` for lineage. Friendly copies are also present (`target_spend_ceiling_eur`, `parts_billed_total_eur`, …). Hide the technical names in the report view.

Primary GPS grain: `gps_spu_by_distributor.csv`
`spend_per_unit_eur` = parts billed ÷ UIO for that year.

**2026 at a glance:** the 2026 rows are eight months. Use `period_basis` to tell a part year from a
full year, keep `max_spend_eur` as the target, and do not read `gps_capture_vs_max` or
`traffic_light_v9` on a `partial_year` row (see the caveat at the top of this file).

---

## 6. PMS — total first

- **Primary:** `line_type = total` (or `capture_rate_total_wtd` on the summary).
- **Secondary:** genuine share / genuine capture — mix quality, not a substitute for total volume.
- `pms_opportunity_matrix.csv` ranks category euro gaps.

---

## 7. AIM — enrichment only

AIM tables here are **coverage and mix** at distributor / family / group level.
There is **no** full AIM master PN dump (that file is ~12 MB and is a parts catalogue, not a PBI fact for this meeting).

Use:
- `aim_gps_matrix` — how much billed euro has AIM class attached
- `mix_genuine_bvp_*` — genuine vs BVP mix
- `dim_pms_category` — slim category list

---

## 8. Starter measures (DAX sketch)

Assuming you have a sales measure `[Parts billed €]` already, and UIO on `fact_uio_by_distributor_year[uio_units]`:

```
UIO trucks :=
SUM ( fact_uio_by_distributor_year[uio_units] )

// After override table applied for IUK 2026 — or use a calculated column that prefers locked_value

Euro per truck :=
DIVIDE ( [Parts billed €], [UIO trucks] )

GPS pct vs target :=
DIVIDE ( [Parts billed €], SUM ( target_spend_waterfall[target_spend_ceiling_eur] ) )

PMS total capture :=
AVERAGE ( pms_summary_by_db[capture_rate_total_wtd] )
// or better: weighted by expected euro if you bring expected into the model
```

**Restrict the year measure, or the comparison is not like-for-like.** The two files carry the year
basis in different columns: `02_GPS/gps_spu_by_distributor.csv` uses `period_basis`
(`full_year` / `partial_year`), while `01_UIO/fact_uio_by_distributor_year.csv` uses
`is_actual` / `is_estimate` / `is_forecast`, as described in section 4.

```
Full years only :=
CALCULATE ( [UIO trucks], fact_uio_by_distributor_year[is_forecast] = FALSE() )
```

Prefer importing GPS/PMS pre-aggregated files for the first dashboard; add custom DAX later.

---

## 9. Suggested first visuals for the meeting

1. UIO by distributor, CY2025 (and CY2024) — stacked CV vs LCV from `fact_uio_by_class_year`
2. Parts billed € / UIO vs prior year — join your SAP sales to UIO rollup. **Compare 2026 with
   January–August 2025, not with full-year 2025**: the 2026 rows are eight months, so a full-year
   comparator shows a fall of about a third that is entirely the missing four months.
3. PMS total capture by distributor — `pms_summary_by_db`
4. Top category gaps — `pms_opportunity_matrix` filtered to one year
5. Genuine vs BVP mix — `mix_genuine_bvp_by_family`

---

## 10. Refresh

These CSVs are a **point-in-time export** (2026-09-22), billed to 2026-08-31. They are not a live SAP feed. When ISZE refreshes derived tables, ask for a new dated pack rather than editing cells by hand (except the IUK 2026 override, which is intentional).

---

## Folder map

| Folder | Contents |
|--------|----------|
| `00_START_HERE` | This file + MANIFEST.csv |
| `01_UIO` | Fleet / trucks in service + Sold-to bridge |
| `02_GPS` | Spend per truck and target-spend waterfall. Parts billing only — non-parts payments are excluded (see the note above) |
| `03_PMS` | Service capture and opportunity gaps |
| `04_AIM` | Classification coverage and genuine/BVP mix |
