# Stated fleet in captured notices — live totals

**Hero KPI:** **Stated fleet in captured notices (pickup/truck)** (`vehicles_pickup_truck`) — sum of extracted `fleet_size` units. **Not** annual market demand. **Not** sales potential. **Not** addressable market.

**Three layers (mandatory — never conflate):**

| Layer | Meaning | This snapshot (indicative) |
|---|---|---|
| **(a) Network sales scale** | Jerome / ISZE annual volumes | ~20k LCV / ~78k CV per year |
| **(b) CV tenders captured** | Pickup+truck opportunities in the feed (filter **CV**) | ~130 of 228 |
| **(c) Stated fleet units** | Sum of fleet counts printed on those notices we extract | **18** (8 notices) |

**18 ≠ 130 ≠ ~78k.** Tiny (c) while (a) is large → **coverage gap (P0)**, not a tiny Isuzu market.

**Why (c) looks tiny:** Country portal map (`_COUNTRY_TENDER_PORTALS_MAP.md`) — national **LIVE ~21%** of footprint countries; **~69%** TED-only for below-threshold. Most notices never publish a fleet count anyway. Wire order: **ES PLACSP → IT PNCP → DE open data → NO/FI keys**.

**Snapshot:** rebuilt 2026-08-25 from merged `isuzu_tenders_v3.xlsx` (FR BOAMP + PL BZP).  
**Engine:** `build_dashboard_v4.py` → `addressable_vehicle_stats()` / `meta.stats` in `isze_dashboard_v4_data.json`.

## Definitions (null ≠ 0)

| KPI | Formula |
|---|---|
| **Stated fleet (pickup/truck)** `vehicles_pickup_truck` | Sum of extracted `fleet_size` where `product_segment` ∈ `{pickup, truck}` — hero = layer (c) |
| **Stated fleet all segments** `vehicles_all_stated` | Sum of extracted `fleet_size` wherever present (incl van/LCV/weak) |
| **CV tenders** | Count of opportunities with segment pickup or truck (layer b) — product filter **CV** |

- Null / missing fleet rows are **omitted** from sums (not coerced to 0).
- Per-row Fleet shows extracted number or **—**.
- Independent of GPS €. Van/LCV in `vehicles_all_stated` only; GPS still product-fit gated.

## Live totals (this build)

| Metric | Value |
|---|---|
| Opportunities (post Isuzu gate) | **228** |
| **CV tenders (pickup+truck)** | **~130** (48 pickup + 82 truck) |
| **Stated fleet (pickup/truck)** | **18** (8 notices) — extract-subset |
| **Stated fleet all segments** | **156** (15 notices) |
| Addressable GPS € / year (sized only) | €1,488.22 (3 rows) |

### By country (stated fleets only)

| Market | Pickup/truck vehicles | Stated all segments | Rows with fleet |
|---|---:|---:|---:|
| Romania | 1 | 84 | 2 |
| Germany | 5 | 38 | 4 |
| Poland | 5 | 23 | 5 |
| France | 7 | 7 | 3 |
| Italy | 0 | 4 | 1 |

## UI (honesty)

- Hero: **Stated fleet in captured notices (pickup/truck)** + disclaimer + sanity chip (network ~20k/~78k).
- Banner: **18 stated fleet units ≠ N CV tenders ≠ ~78k CV/yr**.
- By market: Market · **Stated fleet (pickup/truck)** · Addressable GPS / yr.
- Preserve: six tabs, **CV** product filter + search CV → pickup+truck, Aftersales, IDS, product-fit.
- Criticality: `_CRITICALITY_PROTOCOL.md` · rule `isze-commercial-criticism.mdc` · portal map `_COUNTRY_TENDER_PORTALS_MAP.md`.
