# GPS dashboard — roadmap

**Last updated:** 2026-09-22
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) — open items also appear in the hub queue (§1 items 5–8)
**Live app:** PRISM `pages/2_GPS.py` (port 8503, canonical) · `03_analytics/Isuzu/gps_dashboard/` legacy Dash — **frozen, do not build on it**

**Open here:** interval-aware air factor still provisional (hub item 5) · LCV generation split blocked on chassis/reg-year cutoffs (hub item 7). **Fig-key V2 remainder (hub item 8) — 2026-09-14 slice done** (IE40 fill 158 empty keys; Part Explorer already wired; no Mode A rebuild).

---

## UIO V21 — spend-per-unit data quality (HOLD — Jerome 2026-09-22)

**Decision:** Jerome chose to **hold V21 until UIO V20 is promoted** — one thing at a time. Do not start the
V21 spec, do not rebuild the GPS denominator, and do not re-point `gps_spu_by_distributor.csv` until V20 is
the live workbook. This section exists so the findings are not rediscovered.

**Why V21 is needed at all (Jerome's own read, 2026-09-22):** *"I think we need better spend per unit data."*
Confirmed — the measure is currently weaker than its name.

### What the live measure actually is

`spend_per_unit_eur = total_sales_eur ÷ uio_units` in
[`01_data/00_derived/gps_spu_by_distributor.csv`](../../01_data/00_derived/gps_spu_by_distributor.csv) —
**what ISZE invoices the distributor**, not what the market spent per truck. True market spend needs dealer
sell-out, and the workspace holds that for **UTI only** (`01_data/05_Dealer_sellout/UTIPartSalesCY2024.xlsx`,
`CY2025.xlsx`). The label promises more than the numerator supports.

### Five defects proven on 2026-09-22 (parent check, not a subagent claim)

| # | Defect | Evidence |
|---|---|---|
| 1 | Fleet is **v18**-era, not current | `uio_source` on the 88 rows: **68 `v18_actual`, 16 `v18_proxy_2025`, 4 `ituk_dvla_2026`** |
| 2 | The **proxy flag is inert/false** | `uio_proxy` is **False on all 88 rows** while 16 carry source `v18_proxy_2025` — the flag cannot be trusted to separate measured from proxied |
| 3 | **Two published fleets disagree per market** | 2025 GPS vs wallet: **IRELAND 3,056 vs 2,161 = +41.4%**, PORTUGAL +13.4%, GERMANY −6.7%; network totals (163,459 vs 163,198) hide it. Ireland is the known 2013/14 splice (row drops 2,390 → 12 → 190) |
| 4 | **Four markets bill parts with zero fleet** | UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE — `uio_units = 0`, `traffic_light = unknown`; any €/truck for them would be invented |
| 5 | **The 3.5 t rate is never applied outside ITUK** | `01_data/91_build/gps_v9_loaders.py::max_spend_from_buckets()` returns `buckets["LD"] * RATE_N75` for every non-ITUK market; `RATE_N35` appears only in the ITUK branch. `uio_v19_gps.json` already carries `rates.N35 = 296`, so the two GPS paths disagree. **Not fixed — it moves a published ceiling** |

### Where the accuracy actually is

Not in new sources — in the **band mix**. Wallet rates span 3× (€296 / €739 / €887) and the 3.5 t share of a
market runs **22% (Germany) to 63.6% (Portugal)**, so a whole per-truck figure moves **20–30%** on the mix alone.
The rate is currently applied to a lumped `LD` row, so the mix is an assumption. The four-band set is now locked
(see `STATE_PACKET.md`), which makes per-band denominators buildable for the first time.

### Draft V21 scope (recorded, NOT authorised)

1. Rename or re-scope the measure — "parts billed by us per truck" is honest; "market spend per truck" needs sell-out we do not have.
2. One fleet, one source: bind GPS and wallet to a single per-market fleet table with a vintage stamp, plus a gate that fails when the two disagree beyond tolerance.
3. Per-band denominators, using the locked four bands.
4. Per-market coverage flags — measured / estimated / no denominator — reusing `01_data/90_INBOX/UIO_DATA_INVENTORY_*`.
5. State the warranty position (both columns exist; pick the headline).
6. Explicit exclusions: MIDI, the four zero-fleet markets, credit notes, and the service-fee / demurrage leak closed 2026-09-03.
7. Do not treat 2025 as a baseline — it is the P700 changeover trough, and shipments lag registrations by ~2 years.

**Dependency:** all seven ride on the V20 denominator. Building them on the current fleet would move the error,
not reduce it. Also useful before V21: the Irish 2013/14 splice needs a decision, since it is the largest
single per-market denominator defect.

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
