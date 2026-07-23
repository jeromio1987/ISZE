# Dealer sell-out (DB→DLR layer)

## Layer map

| Layer | Direction | AIM | GPS |
|-------|-----------|-----|-----|
| **Billing** | ISZE → distributor (DB) | `db_parts_mix_classification.csv` | `gps_spu_by_distributor.csv` |
| **Sell-out** | DB → dealer (DLR) | `dealer_sellout_aim_mix_2025.csv` | `dealer_sellout_gps_2025.csv` |

Sell-out files are **quantity** from distributor reports. EUR uses **CY2025 billing ASP** per distributor×PN from `sales_fact` (median unit price). Lines without billing history are qty-only (EUR = 0).

## AIM (sell-out)

Same three buckets as billing (`build_db_parts_classification.py`):

- **bvp** — PN in `genuine_bvp_crossref.bvp_pn`
- **genuine_contested** — genuine PN with a catalogue BVP pair
- **genuine_only** — all other valued lines

**Contested BVP capture** = `bvp_eur / (bvp_eur + genuine_contested_eur)`.

## GPS (sell-out)

**Sell-out SPU** = `total_valued_eur ÷ UIO` (national parc, not per-dealer fleet):

- ITUK: **22,389** (DVLA override, same as billing GPS)
- UTI: **10,668** (V13 proxy year for CY2025)

ITUK dealers share the **same UIO denominator**; dealer rows rank **downstream wallet intensity** (EUR per truck in market), not per-dealer parc GPS.

## UTI vs ITUK

- **ITUK**: dealer dimension in `Sales to Dealers_ITUK_CY2025.xlsx` (~64 dealers).
- **UTI**: `UTIPartSales` is **PN-only** (no dealer). Network row: `UTI (network aggregate)`.

## Rebuild

```powershell
cd Projects/Isuzu/prism
python scripts/build_dealer_sellout_aim_gps.py
python scripts/build_dealer_sellout_dashboard.py
```

Outputs: `Data/derived/dealer_sellout_*`, `Data/dashboards/dealer_sellout_aim_gps.json`, `Dashboards/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`.
