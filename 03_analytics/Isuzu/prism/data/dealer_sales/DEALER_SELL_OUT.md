# Dealer sell-out / sales-to-dealer (DB → DLR layer)

**Authority path:** `01_data/12_raw/dealer_sales/`  
**Registry:** `_registry.yaml`  
**Intake:** drop in `01_data/90_INBOX/` → file under `<DB>/` → register in `_registry.yaml`

---

## Layer map

| Layer | Direction | AIM | GPS |
|-------|-----------|-----|-----|
| **Billing** (layer 1) | ISZE → distributor (DB) | `db_parts_mix_classification.csv` | `gps_spu_by_distributor.csv` |
| **Sell-out** (layer 2 / **second layer**) | DB → dealer (DLR) | `dealer_sellout_aim_mix_2025.csv` + `sellout_aim_network_mix_2025.csv` | `dealer_sellout_gps_2025.csv` |

**Dashboard / JSON for second layer:**  
`02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`  
`01_data/14_dashboards/dealer_sellout_aim_gps.json`  
(Builder auto-includes every DB with a CY long CSV + native ITUK/UTI.)

Sell-out files are **quantity** from distributor reports. EUR (when valued) uses **CY billing ASP** per distributor×PN from `sales_fact` (median unit price). Lines without billing history are qty-only (EUR = 0).

---

## Standing rule (Jerome 2026-08-13)

**Every time sell-out / sales-to-dealer data is ingested → normalize → always wire the second layer.**

Pipeline (do not stop after long CSV):

1. Drop → `01_data/90_INBOX/` → file under `12_raw/dealer_sales/<DB>/`
2. Register in `_registry.yaml` (+ short `SOURCE.md` if new layout)
3. Normalize → `01_data/00_derived/dealer_sellout_long_<DB>_CY{year}.csv` (adapter)
4. **Wire second layer** → rebuild AIM/GPS:

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
python scripts/build_dealer_sellout_aim_gps.py
```

Optional pairwise UTI↔ITUK deep dive (unchanged): `python scripts/build_dealer_sellout_dashboard.py`

Do **not** leave a new long CSV “filed but unwired”. Deploy sync (`sync_to_deploys.ps1`) still needs an explicit ship ask.

---

## Folder layout (multi-DB)

Raw drops stay immutable. One folder per **PRISM distributor_code** (not free-text brand names).

```
01_data/12_raw/dealer_sales/
  _registry.yaml          # catalog of every drop + caveats
  DEALER_SELL_OUT.md      # this file
  ITUK/                   # UK CV trucks
  IUK/                    # UK LCV D-Max (≠ ITUK)
  IRELAND/                # Harris / Isuzu Ireland (≠ IUK, ≠ IMIE)
  UTI/
  GREECE/                 # Petros
  <NEXT_DB>/
```

Topic copies / working notes may also sit in `01_data/05_Dealer_sellout/` — **canonical raw = `12_raw/dealer_sales/`**.

---

## Canonical long schema (target for all sources)

Every DB export is different (ITUK dealer pivot, UTI PartSales, Petros monthly qty).  
**Do not force DBs to send one Excel layout.** Instead, each adapter maps into this long table:

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| `distributor_code` | text | yes | `ITUK`, `UTI`, `GREECE`, … |
| `source_file` | text | yes | filename as filed |
| `grain` | text | yes | `dealer_pn` or `network_pn` |
| `year` | int | yes | calendar year of report |
| `period` | text | yes | `YYYY` or `YYYY-MM` |
| `period_grain` | text | yes | `year` / `month` / `ytd` |
| `part_number` | text | yes | 10-digit zero-padded digits |
| `part_number_raw` | text | yes | as received (preserve leading zeros) |
| `description` | text | no | if supplied |
| `qty` | float | yes | units sold in that period |
| `dealer_name` | text | no | only when `grain=dealer_pn` |
| `vehicle_scope` | text | no | e.g. `D-MAX`, `all`, `unknown` |
| `flags` | text | no | pipe-separated; see flags below |

**Normalized example (Petros CY2025):**  
`01_data/00_derived/dealer_sellout_long_GREECE_CY2025.csv`

### Standard flags

| Flag | Meaning |
|------|---------|
| `pn_newest_rollup` | Column A (or equivalent) is usually the **newest** P/No; older superseded codes may be rolled into it and are not visible as separate rows |
| `qty_only` | No EUR / price in source |
| `partial_year` | Not a full Jan–Dec calendar |

---

## Source shapes we already know

| DB | Typical file | Grain | Periods | Special |
|----|--------------|-------|---------|---------|
| **ITUK** | `Sales to Dealers_ITUK_CY{year}.xlsx` | dealer × PN | month names | Dealer dimension — **SSOT for AIM/GPS dealer grain** |
| **ITUK (Duncan)** | `ITUK_Dealer_Purchases_by_PN_2023_2026YTD_Aug.xlsx` | network PN | 2023-01…2026-08 | Companion only (`*_network_CY2025.csv` + CY2023/24/26YTD). Never replaces dealer SSOT. |
| **IUK** | `IUK_Monthly_Demand_*_July.xlsx` | network PN | JAN…DEC + Total | LCV D-Max; ≠ ITUK; **qty-only by design** (no € from IUK — UK value = ITUK only); 2026 may be YTD (`partial_year`) |
| **UTI** | `UTIPartSales_{year}-{mm}.xlsx` / `*_YTD.xlsx` | network PN | month + YTD cols | No dealer |
| **GREECE (Petros)** | `Petros_Parts_Sold_Qties_{year}.xlsx` | network PN | `YYYY-Mon` cols + `SUM` | D-MAX scope; **`pn_newest_rollup`** |
| **IRELAND (Harris)** | `IRELAND_Sales_to_Dealer_*_Jul.xlsx` | network PN (agg) | invoice line → month | Qty supplied; PN = Item supplied; **qty_only**; ≠ IUK ≠ IMIE |

When a new DB arrives with yet another layout: keep the raw Excel, add a row in `_registry.yaml`, write a short `SOURCE.md` in that DB folder, then map to the canonical long schema (adapter script or one-off). Dashboards/loaders consume the **long** table, not the native Excel.

---

## AIM (sell-out)

Same three buckets as billing (`build_db_parts_classification.py`):

- **bvp** — PN in `genuine_bvp_crossref.bvp_pn`
- **genuine_contested** — genuine PN with a catalogue BVP pair
- **genuine_only** — all other valued lines

**Contested BVP capture** = `bvp_eur / (bvp_eur + genuine_contested_eur)`.

## GPS (sell-out)

**Sell-out SPU** = `total_valued_eur ÷ UIO` (national parc, not per-dealer fleet).  
UIO comes from `gps_spu_by_distributor.csv` for the CY (builder falls back to ITUK **22,389** DVLA / UTI **10,668** if a row is missing).

ITUK dealers share the **same UIO denominator**; dealer rows rank **downstream wallet intensity** (EUR per truck in market), not per-dealer parc GPS.

## UTI vs ITUK (existing)

- **ITUK**: dealer dimension in `Sales to Dealers_ITUK_CY2025.xlsx` (~64 dealers).
- **UTI**: `UTIPartSales` is **PN-only** (no dealer). Network row: `UTI (network aggregate)`.
  SAP sold-to **1799** (never blend with UMI **1797**). Monthly job mails
  `UTIPartSales was executed at 01/MM/YYYY` on the 1st; report month in the sheet
  is **previous calendar month**. Outlook hunt 2026-08-13 filed Aug–Nov 2025 +
  Jan–Jun 2026. **Still missing CY2025 Feb–Jul** (not in Inbox/Sent/Archive).
  Jul 2026 (Aug-1 job) also not in mailbox. Do not replace
  `UTIPartSales_2025-12_YTD.xlsx` with the smaller 2026-01-01 mail copy.
- **YoY elasticity gate:** only **CY2025** full-year sell-out is filed for both.  
  `01_data/05_Dealer_sellout/UTIPartSalesCY2024.xlsx` is a **Jan-2025 YTD** snapshot  
  (same family as `UTIPartSales_2025-01.xlsx`), **not** CY2024 — do not use as YoY t0.  
  DB→DLR response track: `01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv`  
  (+ method `01_data/01_Pricing/PRICE_ELASTICITY_DB_DLR_ITUK_UTI.md`).

## Rebuild (second layer — run after every new/updated long CSV)

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
python scripts/build_dealer_sellout_aim_gps.py
# optional: UTI vs ITUK PMS deep dive
python scripts/build_dealer_sellout_dashboard.py
```

Outputs:

| Artefact | Path |
|----------|------|
| Network AIM mix | `01_data/00_derived/sellout_aim_network_mix_2025.csv` |
| Entity AIM / GPS | `01_data/00_derived/dealer_sellout_aim_mix_2025.csv`, `dealer_sellout_gps_2025.csv` |
| PMS / subgroup / top PN | `01_data/00_derived/sellout_aim_by_*_2025.csv` |
| JSON | `01_data/14_dashboards/dealer_sellout_aim_gps.json` |
| HTML (embedded JSON; openable `file://`) | `02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` |

**Wired CY2025 networks (2026-08-13):** ITUK, UTI, IRELAND, IUK, GREECE.  
Long CSVs auto-discovered as `dealer_sellout_long_<DB>_CY2025.csv`.

**IUK ≠ ITUK:** IUK = UK LCV (D-Max) Monthly Demand **qty only**; ITUK = UK CV dealer×PN sell-out (can include / support **€**). Never blend. Do not chase EUR from IUK.  
**IRELAND ≠ IUK ≠ IMIE.**
