# IDS dealer module — commercial MAP for tender opportunities

**Updated:** 2026-08-25  
**Code:** `ids_dealer_linkage.py`  
**Wired into:** `gps_pms_linkage.enrich_payload` → v4 rebuild (`build_dashboard_v4.py`)

## Intent

When we talk GPS / MAP, also answer: **which Isuzu distributor / IDS dealer owns this geography?**  
Not abstract € alone — actionable for sales (tender → country → distributor → dealer).

## Sources on disk (real — never invented)

| Role | Absolute path | Schema |
|---|---|---|
| Country → GPS distributor | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\country_distributor_map.yaml` | `country_to_distributor`, `iso3_to_country` |
| Distributor commercial labels | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_dimension.csv` | `distributor_code`, `customer_name`, `gps_db_label`, … |
| **IDS dealer network (primary)** | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\rankings\IDS_2026_all_country_rankings.xlsx` | Per-country sheets: `Rank`, `Name`, `Points achieved %`, `Items scored %` |
| Per-country ranking files | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\rankings\*_dealer_ranking.xlsx` | Same columns; rolled into the all-country workbook |
| Derived flat export | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ids_dealer_network.csv` | `ids_tab,rank,dealer_name,points_pct,city,address,source_file` |
| Evaluation reports (addresses often empty) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\reports\evaluation_result\*.xls` | Dealer Name + Address meta row — many countries have **blank** Address |

### IDS tabs present (2026 rankings Index)

Belgium, Netherlands, Luxembourg, Denmark, Poland, Greece, Norway, UK LCV, UK CV, France, Italy, Switzerland, Spain, Israel LCV, Romania, Portugal, Hungary, Malta, Cyprus.

### Not on IDS dealer map (dealer-level BLOCKED)

Markets with a GPS yaml distributor but **no IDS dealer sheet** — notably **Germany** (`GERMANY` / ISD).  
Until Jerome drops e.g. `Germany_dealer_ranking.xlsx` (or a DE tab in the all-country workbook), dealer fields stay `unmapped`. Distributor from yaml still shows.

Israel UTI outlet list with street addresses also exists at  
`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UTI_PartSales_mail_20260813\2026-02-11_IDS_-_dealer_list.xlsx`  
— Israel-only; not used as a Europe-wide map (IDS rankings remain canonical).

## Fields added (do not rename existing GPS fields)

| Field | Meaning |
|---|---|
| `ids_distributor` | From `country_distributor_map.yaml` (same codes as GPS) |
| `ids_distributor_label` | `customer_name` / `gps_db_label` from distributor dimension |
| `ids_dealer_name` | IDS ranking `Name` (or null) |
| `ids_dealer_city` | City token already present in dealer name / address (or null) |
| `ids_dealer_rank` | IDS rank integer |
| `ids_tab` | Workbook tab used |
| `ids_match_method` | `country_primary` \| `geo_nearest` \| `unmapped` |
| `ids_match_confidence` | 0–1 float, or null when unmapped |

### Match method

1. **geo_nearest** — buyer / title / city text hits a dealer name or city token already in the IDS Name (confidence ≥ 0.75). No lat/lon file on disk → not haversine; token match only.
2. **country_primary** — no geo hit → IDS **rank #1** for that country’s preferred tab.
3. **unmapped** — no yaml distributor **or** no IDS dealers for that country.

## Hard rules

- Never invent dealers or GPS €.
- `null ≠ 0`.
- No expected / forecast revenue wording.
- Extend yaml + IDS rankings — do not invent a parallel fantasy network.

## If IDS file missing

Module sets `meta.ids_dealer.blocked_note` and writes `_ids_dealer_status.json`.  
Dashboard still shows **distributor-from-yaml** so MAP is not commercially empty.

**Drop file:** `IDS_2026_all_country_rankings.xlsx` into  
`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\rankings\`

## Smoke

```bat
cd C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install
python ids_dealer_linkage.py
python build_dashboard_v4.py
```

Examples: Romania → `ROMANIA` + rank-1 `RODAV` (or geo hit); Germany → `GERMANY` distributor, dealer `unmapped`.

## Live snapshot alignment (2026-08-25)

Same authoritative figures as the exec one-pager / hub — this module does **not** change GPS €:

| Figure | Value |
|---|---:|
| Notices / opportunities | **211 / 186** |
| GPS floor € / yr | **€1,488.22** (3 sized pickup/truck) |
| Nordics | **AWAITING_KEY** until keys in `nordics_api_keys.env` |
| IDS dealers in rankings | **519** |
| Opps with IDS dealer | **113** (`country_primary` 72 · `geo_nearest` 41) |
| Opps dealer-unmapped | **73** |

Product-fit and market “Why blank” chips are preserved — van/LCV GPS stays null.
