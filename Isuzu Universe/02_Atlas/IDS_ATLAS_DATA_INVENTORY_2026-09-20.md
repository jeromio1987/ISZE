# IDS network atlas — data inventory

**Prepared:** 2026-09-20 · **Internal / private** · **Read-only pass, nothing modified**
**Answers:** the inventory request at the end of `IDS_NETWORK_ATLAS_CONCEPT_2026-09-20.md`
**Scope checked:** `01_data/`, `02_dashboards/`, `03_analytics/`, `04_tools/`, `09_meetings/`, `06_uio/`

---

## Verdict

Most of what ChatGPT assumes we hold is on disk, but the two things its atlas depends on most are
not. There is no table linking a dealer to the distributor responsible for it — the `distributor`
column exists in the dealer file and is empty on all 564 rows — and there is no second IDS round, so
the "network time machine" has nothing to scrub through. The strongest ready-to-use material is the
distributor register, the ITUK dealer-level parts data, and the parts-family mapping; the biggest
surprise is that real backorder transactions with dates do exist, but only for Ireland.

---

## 1. Dashboard entry points and builders

**IDS family.** Page `02_dashboards\ids\IDS_2026_dealer_compare.html` (4,628,834 bytes, mtime
2026-09-17 17:09) with 19 per-country siblings `IDS_2026_dealer_compare_<Country>.html` in the same
folder. Launchers `OPEN_IDS_2026_dealer_compare.cmd` and one per country. Builders live in
`04_tools\ids_dealer_ranking\` — the current ones are `build_ids_country_packs_v13.py`,
`build_db_feedback_sheet.py`, `build_portugal_imotors_pack.py`, `build_ids_sales_market_eval_report.py`
and `_compute_ids_sales_eval.py` (all mtime 2026-09-17 17:08, matching the page). The template is
`ids_dashboard_template.html`; geography is `ids_dealer_geo.py` (59 KB); the gate is
`ids_dashboard_qa.py` and `ids_logic_check.py`. Receipt:
`02_dashboards\ids\_qa_map_triple\IDS_2026_dealer_compare.SHIP_RECEIPT.json` (ok, 2026-09-16, 521
pins, Leaflet inlined, offline basemap image and vector geography baked in, live tiles blocked on the
ISZE network).

**Sales / GPS / PMS / AIM families** (entry point → builder → receipt):

| Family | Page | Builder | Receipt |
|---|---|---|---|
| Exec aftersales paper | `sales\ISZE_Exec_Aftersales_Paper.html` | `_build\build_exec_aftersales_paper.py` | yes |
| KPI dashboard | `sales\ISZE_KPI_Dashboard.html` | `sales\_build\` | yes |
| PMS family compare | `sales\ISZE_PMS_Family_Compare.html` | `sales\_build\` | yes |
| PMS family evolution v2 | `sales\ISZE_PMS_Family_Evolution_v2.html` | `sales\_build\build_family_evolution_v2.py` | yes |
| Leakage cockpit | `sales\ISZE_Leakage_Cockpit.html` | `_build\leakage\build.mjs` | yes |
| Per-market reviews | `sales\leakage_packs\ISZE_Sales_Performance_Review_{ITUK,SWEDEN,BELGIUM}.html` | `_build\leakage\build.mjs` | yes |
| Replenishment | `sales\ISZE_DB_DLR_Replenishment_CY2025.html` | `sales\_build\build_db_dlr_replenishment_cy2025.py` | yes |
| Lost-sales model | `sales\ISZE_Lost_Sales_Model.html` | `sales\_build\lost_sales_model\build_lost_sales_model_html.py` | yes |
| Dealer sales to dealer | `sales\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | `prism\scripts\build_dealer_sellout_aim_gps.py` | yes |
| AIM classification paper | `sales\ISZE_AIM_Classification_Paper.html` | `01_data\91_build\rebuild_aim_classification_paper.py` | yes |
| Price revision pack | `pricing\ISZE_Pricing_Revision_AIM_Source.html` | `91_build\` | yes |
| Trucks in service | `fleet\ISZE_UIO_Car_Park_V19_V20.html` | `06_uio\` | yes |

**Not products, one line each.** `02_dashboards\_build\`, `_qa*`, `_audit\`, `_design\`, `_working\`,
`_composable\`, `_ui\`, `Data\` are working folders and shared assets. `_archive\` is retired pages.
`ids\IDS_all_dashboards_2026-08-19\` is an archived mirror of the live `ids\` pages — the same pages
twice. `sales\_gpt_review\` holds dated review copies. There are 33 distinct receipts under
`02_dashboards\` overall, most of them pricing.

*Join keys:* the page families join on `distributor_code`, `part_number` and `fig_key`.
*Limits:* only the IDS page and the exec paper are self-contained HTML for double-click; several
pricing pages ship with a launcher.

## 2. Distributor register

**Main register:** `01_data\00_derived\distributor_dimension.csv` — 32 rows, columns `sold_to_sap`,
`payer_code`, `distributor_code`, `gps_db_label`, `customer_name`, `scope`, `region`,
`network_role`, `in_pms_source`, `fy2026_net_sales_eur`, `non_parts_eur`, `note`. `scope` is the
vehicle split (CV / LCV / MIXED); `region` groups markets (UK, ISRAEL, WEST, NORDICS, SOUTH, CIS,
EAST, MIDDLE_EAST); `network_role` marks real customers as `network_db`. **Four rows carry no
`distributor_code` and no `region`, only a role**: `not_a_customer`, `excluded_non_parts`,
`direct_account`, `excluded_entity` — not real customers. Built by
`01_data\91_build\build_distributor_dimension.py`.

**Three more registers exist and they disagree in coverage.**

- `03_analytics\Isuzu\prism\data\distributor_master_mapping.csv` — 27 rows, columns
  `distributor_code`, `legal_entity`, `country`, `region`, `segment_lcv`, `segment_cv`, `uio_match`,
  `notes`. Legal entity names, and the LCV/CV split as two Yes/No columns. Carries
  `GERMANY_SERVICE` (excluded, service department only) and routes the four Benelux countries
  (Belgium, Netherlands, Luxembourg, Poland) to one entity, `ISUZU BENELUX NV`.
- `03_analytics\Isuzu\prism\data\distributor_geo.csv` — 23 rows: `distributor_code`, `country`,
  `lat`, `lon`, `territory_label`. A `UNMAPPED` row has no coordinates.
- `03_analytics\Isuzu\prism\data\sap_sold_to_mapping.csv` — 34 rows: `sap_sold_to_pt`,
  `sold_to_name`, `distributor_code`, `notes`. This is the bridge from the billing system to the
  code. It carries `NON_PARTS` for service fees, demurrage and e-compensation, and two SAP numbers
  for Germany (one main, one service) and two for Portugal.

**They disagree.** `distributor_master_mapping.csv` holds MIDI, TURKEY and `GERMANY_SERVICE`, which
`distributor_dimension.csv` does not. `distributor_dimension.csv` holds Ukraine, Armenia and
Kazakhstan as `network_db`, which `distributor_master_mapping.csv` does not. `distributor_geo.csv`
carries no Poland row, though Poland is a live IDS market with 23 scored dealers.

**Duplicates flagged:** Germany has two SAP numbers mapped to `GERMANY` (601 and 2516) plus a
separate `GERMANY_SERVICE`; Portugal has two (92 and 519); MIDI has two (88 and 2194) with 2194
marked as excluded; and the field name `sold_to_sap` in one file is `sap_sold_to_pt` in another.

*Join keys:* `distributor_code`, `sold_to_sap` ↔ `sap_sold_to_pt`.
*Limits:* three registers, no single authority, and Poland is missing from the geography file.

## 3. Headquarters and warehouse locations

**Warehouse and depot locations do not exist anywhere.** I looked for office, headquarters, warehouse,
depot and parts-centre coordinates across `01_data\08_Distributor\`, `01_data\07_UIO\`,
`03_analytics\Isuzu\prism\data\` and `02_dashboards\globe\`. The only distributor coordinates are in
`distributor_geo.csv`, and they are **country centres, not sites** — ITUK and IUK both sit at
`54.0, -2.0`, which is the middle of the United Kingdom, and UTI and UMI both sit at `31.05, 34.85`.

Dealer coordinates do exist (`ids_dealers_geo.csv`, 564 rows, complete on latitude and longitude),
but 145 of the 564 sit on a coordinate shared with another dealer, and the most repeated pairs are
city centres rather than real premises — five dealers on Bucharest centre, four on a Belgian point,
three on Aberdeen, three on Thessaloniki, three on Warsaw, three on Jerusalem and three on Tel Aviv.
The map work itself acknowledges this: the concept note records that the page uses approximate city
and country-centre placements.

*Join keys:* `distributor_code` in `distributor_geo.csv`.
*Limits:* **missing entirely for warehouses.** The atlas chapter that draws a distributor office and a
separate parts warehouse cannot be built from what we hold.

## 4. Dealer and site master, and the ID crosswalks

**Two dealer files, and they are not the same list.**

`01_data\00_derived\ids_dealer_network.csv` — 519 rows, columns `ids_tab`, `rank`, `dealer_name`,
`points_pct`, `city`, `address`, `source_file`. Verified: **519 rows, 514 distinct dealer names, no
blank names, no blank scores, and `city` is blank on 495 of 519 rows.** `address` is blank on all 519.
The tag `ids_tab` carries 19 values — Belgium 34, Cyprus 1, Denmark 20, France 84, Greece 34,
Hungary 19, Israel LCV 29, Italy 41, Luxembourg 1, Malta 1, Netherlands 9, Norway 38, Poland 23,
Portugal 16, Romania 15, Spain 45, Switzerland 22, UK CV 44, UK LCV 43. Four dealer names repeat
inside a tab (514 names over 519 rows). **There is no `distributor` column in this file at all.**

`01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\03_dealer_master_geo\ids_dealers_geo.csv` —
564 rows, columns `country`, `dealer_name`, `city`, `address`, `postcode`, `lat`, `lon`, `score`,
`rank`, `distributor`, `place`. Verified: **564 rows, and the `distributor` column is empty on all
564.** Country labels number 20 because the file carries **both a Benelux view (43 rows) and the
individual Belgium (34), Netherlands (9) and Luxembourg (1) views** — I compared the names: 41 of the
41 distinct Benelux names are already in the Belgium, Netherlands and Luxembourg rows, so the Benelux
block is a duplicate view rather than four extra dealers. Eight dealer names repeat inside a country
(for example three `Odyssey sp. z o. o.` rows in Poland, two `VANLEENDERT PLOMBIERES` rows in both
Belgium and Benelux). `city` is blank on 564 of 564 — the value sits in a column named `place`
instead, and `place` is filled on all 564. `rank` is blank on all 564 and `score` is blank on all
564, so **the geography file carries no scores at all.**

**A third file exists.** `01_data\90_INBOX\PPT_GPT_10csv_2026-09-19\06_dealer_master_geo.csv` —
columns `country`, `distributor`, `dealer_name`, `city`, `address`, `postcode`, `latitude`,
`longitude`, `ids_score`, `ids_rank`, `geo_source`, `country_code`, `note`. Different column names
from the other two (`latitude`/`longitude` not `lat`/`lon`, `ids_score` not `score`). It carries a
note warning that it is IDS participants only and that Israel means UMI only.

**Is there a crosswalk from a dealer name to a distributor or a billing account? No.** I searched
`04_tools\ids_dealer_ranking\`, `01_data\08_Distributor\IDS_2026\` and the sales-to-dealer work.
Nothing maps a dealer to a `sold_to` account, and nothing maps a dealer to a `distributor_code`. The
closest things are the `ids_tab` label (a round and a market, not a billing entity) and the
`db owner` idea in the Kaizen register, which turns out to be a column of blanks (see section 9).

**How bad is the name matching, counted.** Comparing the two main files by dealer name, normalised to
letters and digits: 514 distinct names each, **479 names appear in both**. That leaves 35 names in
the list that are not in the geography file and 35 the other way. Earlier in this session I compared
the 64 ITUK dealer names in the sales data against the geography file: **16 match exactly after
normalisation, 34 more reach a strong token overlap, and 20 have no plausible match** — the ITUK
sales names carry branch suffixes the geography file splits into separate rows, for example
`Aquila Truck (Gloucester)` in the sales file against `Aquila Truck Centres Ltd Gloucester` in the
geography file.

*Join keys:* dealer name only, and only informally — no identifier. `ids_tab` joins to the round.
*Limits:* the distributor link is empty, the geography file holds no scores, and roughly a third of
the ITUK sales names match only loosely.

## 5. Sales to dealer, including wholesale, and its coverage

This is the section that decides where the atlas drill-down stops, so I counted it file by file.

**The verification file first.** `01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\02_sales_to_dealer\sales_to_dealer_coverage.csv`
lists 15 source files and records `real_dealers = 64` on exactly one of them — ITUK calendar 2025.
Every other row is 0.

**The canonical long files** in `01_data\00_derived\`, all 13 columns
(`distributor_code`, `source_file`, `grain`, `year`, `period`, `part_number`, `dealer_name`, `qty`,
`flags` and three more):

| File | Rows | Grain | Dealer names | Year |
|---|---|---|---|---|
| `dealer_sellout_long_ITUK_CY2025.csv` | 101,341 | `dealer_pn` | **64** | 2025 |
| `dealer_sellout_long_ITUK_CY2023.csv` | 27,860 | `network_pn` | 0 (one "All" row) | 2023 |
| `dealer_sellout_long_ITUK_CY2024.csv` | 28,694 | `network_pn` | 0 | 2024 |
| `dealer_sellout_long_ITUK_network_CY2025.csv` | 28,483 | `network_pn` | 0 | 2025 |
| `dealer_sellout_long_ITUK_CY2026YTD.csv` | 21,102 | `network_pn` | 0 | 2026 |
| `dealer_sellout_long_GREECE_CY2025.csv` | 7,774 | `network_pn` | 0 | 2025 |
| `dealer_sellout_long_IUK_CY2025.csv` | 24,360 | `network_pn` | 0 | 2025 |
| `dealer_sellout_long_IUK_CY2026YTD.csv` | (present) | `network_pn` | 0 | 2026 |
| `dealer_sellout_long_IRELAND_CY2025.csv` | 19,244 | `network_pn` | 0 | 2025 |
| `dealer_sellout_long_IRELAND_CY2026YTD.csv` | (present) | `network_pn` | 0 | 2026 |
| `dealer_sellout_long_UTI_CY2025.csv` | 5,474 | `network_pn` | 0 | 2025 |
| `dealer_sellout_long_UTI_CY2026YTD.csv` | (present) | `network_pn` | 0 | 2026 |
| `dealer_sellout_long_PORTUGAL_CY2025.csv` | 21,636 | `network_pn` | 0 | 2025 |
| `dealer_sellout_long_PORTUGAL_CY2026YTD.csv` | (present) | `network_pn` | 0 | 2026 |
| `dealer_sellout_long_ROMANIA_CY2026YTD.csv` | 1,827 | `network_pn` | 0 | 2026 only |

**So exactly one market has real dealer names anywhere in the quarterly data: ITUK, and only
calendar 2025.** Seven distributors have some sales-to-dealer data (ITUK, IUK, IRELAND, GREECE,
PORTUGAL, ROMANIA, UTI). **Six of them have national volume per part number and nothing below it.**
Romania has 2026 only and no 2025, so it cannot enter any year-on-year comparison. ITUK's own 2023,
2024 and 2026 files are national aggregates even though the 2025 file is dealer-level, so a
per-dealer trend for ITUK does not exist either — one year, not a series.

**Wholesale versus retail.** Every one of these is what a distributor sold to its dealer network, so
they are wholesale by definition. Nothing in this workspace measures a dealer selling to an
end customer, and the coverage file says so in its own words. Do not read any of these as final
demand to the truck owner.

**Euro versus quantity.** The long files carry `qty` and no money column at all. The header notes
record `qty_only` as a flag on the Romania, Ireland, Portugal, IUK and Greece sources. Valuing them
is done downstream by applying the billing average selling price per part number, and lines with no
billing history stay at zero euro. The one dealer-level euro file is
`01_data\00_derived\dealer_sellout_gps_2025.csv` (69 rows: `entity`, `total_eur`, `bvp_eur`,
`genuine_contested_eur`, `genuine_only_eur`, `distributor_code`, `qty_year`, and a share of network).
`01_data\00_derived\dealer_sellout_aim_mix_2025.csv` is the same 69 rows with the same columns.

**Dealer counts by entity in that 69-row file** (*verify separately if you need the exact split*):
most rows are ITUK dealers, a block is UTI, and there is an ITUK network row. There is **no UMI row**
— so for Israel, only UTI has dealer-level parts value, and UMI has none.

**The rollups.** `...\02_sales_to_dealer\sales_to_dealer_by_dealer_year.csv` — 64 rows, one per ITUK
dealer, columns `distributor_code`, `dealer_name`, `year`, `qty_total`, `pn_line_count`,
`source_file`, `has_euro_in_source`. Quantities only, no euro.
`...\02_sales_to_dealer\sales_to_dealer_network_by_db_year.csv` — 14 rows, columns
`distributor_code`, `year`, `period_grain`, `qty_total`, `pn_line_count`, `grain`, `source_file`.

**The raw drops** are registered in `01_data\12_raw\dealer_sales\_registry.yaml`, which names the
person, the date and the email subject for each one, and states plainly for Romania that it is
national volume with no dealer column and no euro. Raw files sit under
`01_data\12_raw\dealer_sales\<DB>\`. The registry also records that UTI's calendar 2025 February to
July is **missing** after an Outlook hunt found nothing, with only the December year-to-date snapshot
usable for the annual figure.

*Join keys:* `distributor_code` and `part_number` everywhere; `dealer_name` on the ITUK 2025 file
only, matching the dealer master by name and only loosely.
*Limits:* one market with dealer names, one year; six markets national only; quantities without euro
in the source; no dealer-to-end-customer layer at all; no UMI dealer data.

## 6. Part number to parts family mapping

**The current spine is** `01_data\00_derived\aim_pn_classification_v2.csv` — **164,667 rows, 16
columns**: `part_number`, `description_norm`, `catalog_l1/l2/l3`, `catalog_node_present`,
`catalog_residual`, `workbook_l1/l2/l3`, `workbook_axis_kind`, `workbook_source`, `axis_conflict`,
`desc_ambiguous`, `fig_key`, `filter_part_role`. Written 2026-09-20 20:47.

**A newer dated file sits beside it.** `01_data\00_derived\aim_pn_classification_20260920.csv` —
**164,907 rows, 27 columns**, rebuilt on 2026-09-20 20:46 directly from `pr00_classification.csv` so
that the catalogue columns match their declared source. It adds `aim_l1_fixed` and the
`aim_source` field among its 27. Its gate is `aim_pn_classification_20260920.gate.json` and its
metadata is `aim_pn_classification_20260920.meta.json`. It exists precisely because the master's
catalogue columns had drifted; `01_data\00_derived\HANDOFF_AIR_FILTER_AND_FOCUS_CUT.md` and
`01_data\90_INBOX\AIM_V2_READINESS_2026-09-20.md` explain the history, and I summarise rather than
re-derive it: the master's tree columns are a stale one-time copy taken on 17 September, and about
2,728 part numbers have drifted from their source, including 132 air-cleaner elements worth
EUR 1,160,612 filed in the wrong family.

**The master** is `01_data\00_derived\aim_master_v2.csv` — **165,213 rows, 32 columns**, including
`aim_l1`, `aim_l2`, `aim_l3`, `aim_l1_fixed`, `aim_l2_fixed`, `cat_l1/l2/l3`, `cat_pms_flag`,
`fig_key`, `price_class_iml`, `l12m_billed_eur` and eight Japanese-code columns (`jp_zkk`, `jp_zuk`,
`jp_hkk`, `jp_eple`). It carries the billing weight per part number. Its own readiness note says it
is missing 14 of the 15 columns the classification file's consumer expects, so it cannot be copied
into a rebuilt classification.

**Coverage against the billed catalogue:** the classification files hold roughly 164,900 part
numbers; `aim_master_v2.csv` holds 165,213; the pricing source lines at
`01_data\00_derived\pricing_aim_source_lines.parquet` are built on the same spine. The readiness note
records AIM level 1 covering 80.3% of in-scope euro and source of supply held on 93.6%, with the
remainders as explicit buckets.

*Join keys:* `part_number` (zero-padded digits) and `fig_key`.
*Limits:* **three candidate files and no declared single authority today** — `_v2.csv` is what the
dashboards read, `_20260920.csv` is the corrected rebuild, and the master is stale in its catalogue
columns. I am not resolving that; it is an open decision. Also note the master's `description` is
filled on only 15.68% of rows, which is why `description_norm` cannot be regenerated from it.

## 7. Trucks in service (UIO) at its real geographic level

**The finest grain that exists is distributor × market × vehicle class × model type × year.**
`01_data\00_derived\uio_by_market_type_year.csv` — **1,279 rows, 13 columns**: `distributor_code`,
`market`, `vehicle_class`, `model_type`, `year`, `uio_units`, `is_actual`, `is_estimate`,
`is_forecast`, `basis`, `source_note`, `band_note`, `fleet_quality_note`. The `is_actual` /
`is_estimate` / `is_forecast` flags are worth respecting: the brief for the atlas says forward fleet
forecasts must not be quoted.

Supporting fleet files: `uio_by_model_bucket.csv` (coarse buckets), `nseries_tonnage_evolution.csv`
(147 KB), `vehicle_family_bands.csv`, `UIO_carpark_for_GPS_recalc_2026-07-30.csv` (8 KB),
`UIO_CY2026_by_DB_for_rebuild_2026-07-30.csv` (84 rows, one per country×model with a 2026 column
explicitly labelled **do not use**), all under
`01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\04_fleet_uio\`. The share file
`uio_ld_n35_share.csv` (9 rows: `distributor_code`, `market`, `n35_share`, `basis`, `units_2025e`,
`evidence_note`) splits the light class into true 3.5-tonne and heavier readings.

**Can fleet be attached to a dealer or a territory? No.** Every fleet file stops at market level
with a `distributor_code`, and the atlas needs a denominator below that. There is no dealer-level
fleet numerator or denominator anywhere.

**The one finer instance is a VIN register, not a fleet table.**
`01_data\07_UIO\vin\VIN_register.csv` (3,238 vehicles, built from
`raw\VIN_list_JP_20260727.xlsx`, as-of 2026-07-27). It is per-vehicle and its summary records the
split by distributor: Portugal 2,111, Ireland 647, Germany 183, Malta 130, Cyprus 114, Belgium 49,
Greece 4. It has no coordinates and no dealer field, and its `transmission` column is unknown on
every row. The other finer instance is `01_data\07_UIO\Matriculas Isuzu SAP.xlsx`, the Portuguese
registration register with per-VIN sheets by tonnage band — Portugal only.

*Join keys:* `distributor_code`, `market`, `vehicle_class`, `model_type`, `year`.
*Limits:* market is the floor. **No dealer or territory denominator exists**, so a per-dealer spend
ratio cannot be computed; the existing dealer pages divide by the whole national fleet and rank
intensity within the market, which is a different statement.

## 8. Inventory, backorder and lost-sales records

**Backorder transactions do exist, with dates and identifiers — for Ireland only.** Under
`01_data\92_archive\mail_hunts_20260813\_ireland_sales_mail_20260813\attachments\` there are **40
files named `*_IE_BO_OVERVIEW_-_ISUZU_IRELAND_*.xlsx`**, dated from 2025-10-30 to 2026-08-11 and
roughly weekly. I opened one (`2026-08-11`). Its first sheet is named `DATA` and carries a header of
`Sold-to nº`, `Customer`, `Sales Doc.`, `Customer Reference`, `Material`, `Material description`,
`SaTy`, `Req.Dlv.Dt`, `Open Qty`, `Transit qty`, `ETA`, `Priority`, `Next ETA Supplier`, `Tentative
future ETA ISZ`, `Confirmed Qty`. The rows are individual open order lines with a sales document
number, a required delivery date and free-text supplier notes. The second sheet is named
`PASTE DATA PO BACKLOG`. So this is genuine backorder transaction data: part number, quantity, due
date, age, and a reason where the supplier wrote one. It is **archived under a mail hunt and wired
into nothing.**

**Lost sales: the largest file on disk is the real source, and it is not in the derived folder.**
The outstanding item is
`01_data\92_archive\mail_hunts_20260813\_ireland_sales_mail_20260813\attachments\2025-12-11_IE_ireland_bo_s.xlsx`.
Every `lost_sales_*` file in `01_data\00_derived\` is **derived or modelled, not a transaction log**:

- `lost_sales_market.csv` — 54 rows, one per distributor per year, with `uio_units`,
  target-spend ceiling fields, `captured_total_eur`, `uncaptured_eur`, `actionable_gap_eur`. A model
  output; its own `assumption_note` says the addressable split is an assumption.
- `lost_sales_pn_action.csv` — 78 rows, one per part number, with competition, price class, billed
  euro, units, margin, our list price, competitor price and a recommended lever. An action list built
  from price comparison, not a record of a lost order.
- `lost_sales_model.csv`, `lost_sales_fiscal_year.csv`, `lost_sales_fiscal_q1.csv`,
  `lost_sales_competitor_coverage.csv`, `lost_sales_competitor_pn.csv` — same family, built by
  `03_analytics\Isuzu\prism\scripts\build_lost_sales_model.py` and
  `03_analytics\Isuzu\prism\modules\lost_sales_build.py`.

**Inventory and stock: nothing exists.** There is no file with a stock quantity, a stock value, a
turns figure or a standing-inventory measure anywhere in the workspace. The nearest thing is
`01_data\00_derived\replenishment_exceptions_cy2025.csv` — 1,934 rows, columns `distributor_code`,
`part_number`, `bill_qty`, `bill_eur`, `sellout_qty`, `sell_through_ratio`, `pipeline_signal`, `year`.
That is a comparison of what we billed against what the distributor passed on, with a derived
`pipeline_signal` label. It is a signal, not an inventory record. `replenishment_bridge_ituk_dealer.parquet`
carries the same idea at ITUK dealer level, and `01_data\13_models\Phase3_Demand_Stocking_Model.xlsx`
is a planning model, not a measurement.

**So the proposal's assumption about question D.2-15 fails as stated.** The IDS checklist asks
whether a dealer tracks lost sales caused by price or by backorder. That question tells us whether a
practice exists. When the answer is yes, the transactions still do not reach us: the only place we
hold backorder lines is Ireland, and we hold no lost-sales transaction log from any market.

*Join keys:* `part_number`, `distributor_code`; Ireland backorder rows also carry a sales document
number and the sold-to number 76.
*Limits:* backorder data is one market and sits unwired in an archive. **No inventory data at all.
No lost-sales transactions at all.**

## 9. Dated IDS assessments, evidence and action history

**Only the 2026 round exists.** There is no file matching `IDS_2025` or `IDS_2024` anywhere under
`01_data\` or `09_meetings\` — I searched both trees. The only history of any kind is dated *exports
of the same 2026 round* under `01_data\08_Distributor\IDS_2026\rankings\`: `B1_Business_Plan_ranking`
dated 2, 4, 8, 9 and 10 June and 23 and 27 July 2026, and `IDS_2026_TOTAL_ranking_all` dated 9 and 10
June 2026, plus several `_fromDownloads` copies. Those are the same scores re-exported, not a new
measurement.

**What is on disk.** Per-market folders under `01_data\08_Distributor\IDS_2026\` with workbook
counts: BE 35, Denmark 21, Hungary 20, Israel 29, ITUK 1, IUK 45, LUX 1, MIDI 3, NL 9, Petros 34,
Poland 23, Portugal 16, Romania 16, RSA 38, plus `rankings` 55, `reports` 554, `_EXPORT` 27 and two
`_INCOMING_2026-07-` folders. The folder names confirm the outside providers: **Gasanzammit (Malta),
Loutsios (Cyprus), Petros (Greece), MIDI (four countries), RSA (Norway)** — nine markets delivered
under a supplier's name rather than ISZE's own round.

**The checklist answers exist per dealer.** `04_tools\ids_dealer_ranking\_checklist_inspect_out.txt`
records what the inspector found: Hungary 19 dealer workbooks under `Hungary\IDS self evaluation
reports Hungary 2026`, each with 19 dealer-name cells on row 3 and a scoring block on rows 13 to 20;
Belgium 34 dealer workbooks and 34 names in the wide report; Netherlands 9; IUK 45 dealer workbooks
and 45 names; Romania 15 in the ranking sheet; MIDI's workbook `MIDI_FR.xlsx` with 196 questions per
dealer across 196 dealers per country division (`CodDiv` counts IT 7,644, FR 15,092, CH 4,116,
ES 8,624). The wide matrix reports exist as
`01_data\08_Distributor\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_<Market>.xls`
— 33 files. **Watch the duplicates in that folder:** the same report appears under two names —
`BE` and `Belgium` (identical size, 182,784 bytes), `NL` and `Netherlands`, `LUX` and `Luxembourg`,
`Israel` and `Israel LCV`, `ITUK` and `UK CV`, `IUK` and `UK LCV`, plus `Petros`, `RSA`, `Malta`,
`Cyprus`, `MIDI_CH/ES/FR/IT`. Counting those as 33 separate reports would double-count seven of them.

**Per-dealer assessment DATES: none exist.** Every date on disk is a file date or an export date. I
found no column anywhere that records when a given dealer was assessed. The concept note is right
that the build timestamp is not a substitute.

**Evidence attachments: none found** in the workspace — no photo, certificate or document store
attached to a checklist answer.

**Action history: there is a register, and it is empty of owners.** `01_data\08_Distributor\IDS_2026\reports\kaizen_ids\IDS_Kaizen_Full_Register.xlsx`
has five sheets (`Kaizen_Dealers`, `Country_Sections`, `Country_Ask_List`, `DB_Questions`,
`Gap_Detail`). `Kaizen_Dealers` holds **50 rows**, columns including `Country`, `Dealer`, `IDS total %`,
`Weakest section`, `Top Excel gaps`, `Totals only?`, `DB owner`, `Due`, `Status`. Counted: **`DB owner`
filled 0, `Due` filled 0, `Status` filled 50, and all 50 read "Open".** So it is a scaffold with no
dated actions closed — which matters, because the atlas wants to show action closure over time.
Two related registers exist: `reports\kaizen_db_posture\IDS_DB_Parts_Posture_Register.xlsx` (12 rows
on its main sheet, columns including `Country`, `PRISM DB`, `Archetype`, `Thesis`, `Ask 1`, `Ask 2`,
`Dealers scored`, `IDS D avg %`, `GPS €/UIO`) and `reports\kaizen_parts\IDS_Parts_Kaizen_Register.xlsx`.

**Two bookkeeping traps in this area.** First,
`01_data\08_Distributor\IDS_2026\reports\dealer_feedback\IDS_Dealer_Feedback_Register.xlsx` has a
header row and **zero data rows** — it is an empty shell, so anything quoting it as a register would
be quoting a header. Second, the awards workbook
`...\rankings\DB Evaluation for Awards 26.xlsx` does carry a real ownership column, and it is the
only place I found one: sheet `Awards`, columns `DB Name`, `Country`, `IMG/ISZE Responsible`,
`DLR#`, `Soll DLR`, `# Submission`, `in %`, `Submission by End March?`, with names in the owner
column (Jerome, Bart, Tomoe, Koen). That is submission ownership for the round, **not** Kaizen action
ownership, and the two should not be confused.

The distributor feedback packs under `09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\` are a real,
per-country, per-dealer set — 19 country folders plus a template, with a rollup workbook and HTML per
market and, inside each market, a folder per dealer holding a workbook, an executive summary and a
workshop pack. The same material is staged for sharing at
`09_meetings\IDS_2026_SharePoint_drop\IDS_dealer_sheets\`. That is the per-dealer pack the concept
note wants to link into.

*Join keys:* dealer name and market label; `DB owner` where filled (it is not).
*Limits:* **one round only, so no time series. No per-dealer assessment date. No evidence
attachments. The action register has no owner and no due date, and every row is still open.**

---

## Summary table

| Source | Path | Grain | Date range | Rows | Join keys | Coverage | Status |
|---|---|---|---|---|---|---|---|
| IDS dealer compare page | `02_dashboards\ids\IDS_2026_dealer_compare.html` | one page, whole network | built 2026-09-17 | 4.6 MB, 521 pins | dealer name | 19 markets | solid |
| Dealer list (scores) | `01_data\00_derived\ids_dealer_network.csv` | dealer | 2026 round | 519 | dealer name, ids_tab | 19 tabs, 514 names | partial |
| Dealer master with geography | `...\03_dealer_master_geo\ids_dealers_geo.csv` | dealer | 2026 round | 564 | dealer name, lat/lon | 20 country labels incl. Benelux duplicate | partial |
| Distributor register | `01_data\00_derived\distributor_dimension.csv` | distributor | FY2026 | 32 | distributor_code, sold_to_sap | 18 real customers + 4 non-customers | solid |
| Distributor master + legal entity | `prism\data\distributor_master_mapping.csv` | distributor | current | 27 | distributor_code | disagrees with the above | uncertain |
| Distributor country coordinates | `prism\data\distributor_geo.csv` | distributor | current | 23 | distributor_code | country centres only; no Poland | partial |
| SAP to distributor bridge | `prism\data\sap_sold_to_mapping.csv` | sold-to account | current | 34 | sold_to_sap | includes NON_PARTS | solid |
| Warehouse / depot locations | — | — | — | — | — | **none found** | missing |
| Dealer to distributor link | — | — | — | — | — | **column empty on all 564 rows** | missing |
| Sales to dealer, dealer level | `01_data\00_derived\dealer_sellout_long_ITUK_CY2025.csv` | dealer × part number × month | CY2025 | 101,341 | dealer name, part_number | **ITUK 2025 only, 64 dealers** | solid |
| Sales to dealer, national level | `dealer_sellout_long_{GREECE,IUK,IRELAND,UTI,PORTUGAL,ROMANIA}_CY*.csv` | market × part number × period | 2025–2026 | 1.8k–24k each | distributor_code, part_number | 6 markets, quantities only | partial |
| Dealer euros (sales to dealer valued) | `01_data\00_derived\dealer_sellout_gps_2025.csv` | dealer or network entity | 2025 | 69 | entity, distributor_code | ITUK dealers + UTI; **no UMI** | partial |
| Sales-to-dealer coverage check | `...\02_sales_to_dealer\sales_to_dealer_coverage.csv` | source file | 2025–2026 | 15 | source_file | states 64 dealers on one file | solid |
| Raw sales-to-dealer drops + registry | `01_data\12_raw\dealer_sales\` + `_registry.yaml` | file | 2023–2026 | 26 files | distributor_code | UTI 2025 Feb–Jul missing | partial |
| Part number to family (live) | `01_data\00_derived\aim_pn_classification_v2.csv` | part number | built 2026-09-20 | 164,667 | part_number, fig_key | ~80% of in-scope euro at level 1 | solid |
| Part number to family (rebuilt) | `01_data\00_derived\aim_pn_classification_20260920.csv` | part number | built 2026-09-20 | 164,907 | part_number, fig_key | reads source tree live | solid, not yet declared authoritative |
| Parts master with billing weight | `01_data\00_derived\aim_master_v2.csv` | part number | updated 2026-09-20 | 165,213 | part_number | catalogue columns stale on ~2,728 PNs | uncertain |
| Trucks in service | `01_data\00_derived\uio_by_market_type_year.csv` | distributor × market × class × model × year | multi-year | 1,279 | distributor_code, market, year | **market is the floor** | solid |
| Trucks in service, light-share | `prism\data\uio_ld_n35_share.csv` | distributor | 2025 estimate | 9 | distributor_code | 3.5 t share only | partial |
| Vehicle register (per VIN) | `01_data\07_UIO\vin\VIN_register.csv` | vehicle | 2020–2026 | 3,238 | VIN | 7 markets, PT-heavy; no coordinates | partial |
| Backorder transactions | `01_data\92_archive\mail_hunts_20260813\_ireland_sales_mail_20260813\attachments\*_IE_BO_OVERVIEW_*.xlsx` | open order line | 2025-10-30 → 2026-08-11 | 40 files | part_number, sales doc, sold-to 76 | **Ireland only, unwired** | partial |
| Inventory / stock | — | — | — | — | — | **none found** | missing |
| Lost-sales transactions | — | — | — | — | — | **none; only derived models** | missing |
| Replenishment signal | `01_data\00_derived\replenishment_exceptions_cy2025.csv` | distributor × part number | CY2025 | 1,934 | distributor_code, part_number | derived from billing vs shipments | partial |
| IDS wide result reports | `...\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_*.xls` | market × dealer × question | 2026 round | 33 files (7 duplicated) | dealer name | 19 markets | solid |
| IDS per-dealer workbooks | `...\IDS_2026\<Market>\*.xlsx` | dealer × question | 2026 round | 1–45 per market | dealer name | 196 questions | solid |
| Kaizen action register | `...\reports\kaizen_ids\IDS_Kaizen_Full_Register.xlsx` | dealer | 2026 | 50 | dealer, country | owner and due date 100% empty | partial |
| Dealer feedback register | `...\reports\dealer_feedback\IDS_Dealer_Feedback_Register.xlsx` | dealer | 2026 | **0 (header only)** | dealer | empty shell | missing |
| Round ownership | `...\rankings\DB Evaluation for Awards 26.xlsx` | distributor × country | 2026 round | ~34 rows | country, DB name | submission owner only | partial |
| Distributor feedback packs | `09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\<Market>\` | market, then dealer | v0.4 | 19 markets | dealer name | rollup + per-dealer packs | solid |
| Earlier IDS rounds | — | — | — | — | — | **none; 2026 only** | missing |

---

## What the atlas can show today, and what it cannot

It can show the dealer network with scores, because 519 scored dealers with a country label and
coordinates exist and already paint. It can show the distributor layer as a register with legal
entity, vehicle scope and region, and it can attach parts billing and trucks in service to that
register, because `distributor_code` is a clean key across the billing, fleet and parts-family files.
It can genuinely go one level deeper for the United Kingdom trucks: 64 named dealers with part-number
quantities for calendar 2025, the parts families behind those numbers, and — for Ireland — real
open-order lines with dates. What it cannot do is the step the whole concept rests on: selecting one
distributor and unfolding *its* dealers. No file links a dealer to the distributor responsible for
it, so a dealer cannot be attributed to a billing entity except by its market label, and that breaks
exactly where it matters most, in the two markets that hold more than one distributor. It also cannot
offer a time series, because there is one IDS round and no per-dealer assessment date, and it cannot
show per-dealer fleet, because trucks in service stop at market.

## Contradictions found

1. **564 dealer records against 521 map pins against 519 scored rows.** The geography file holds 564
   rows, the shipped map receipt records 521 pins, and the score file holds 519 rows. The 43-row gap
   between 564 and 521 is the Benelux block — I confirmed the Benelux names are already present in
   the Belgium, Netherlands and Luxembourg rows — but the remaining 2-row gap between 521 pins and
   519 scores is **not explained** and needs the builder to settle. Reported, not resolved.
2. **The geography file carries no scores.** `ids_dealers_geo.csv` has a `score` column and it is
   blank on all 564 rows, while `ids_dealer_network.csv` has `points_pct` filled on all 519. The two
   dealer files are complementary rather than overlapping, which is not obvious from either filename.
3. **`city` is blank on 495 of 519 rows, but a column named `place` is filled on all 564.** Two
   different files store the same idea under two different names, so any join or display that reads
   `city` from both will silently produce half-empty geography.
4. **Three dealer files with three different column sets** — `latitude`/`longitude` versus
   `lat`/`lon`, `ids_score` versus `score` — for what is the same underlying list.
5. **Three distributor registers that disagree on membership.** MIDI, TURKEY and `GERMANY_SERVICE`
   appear in one and not another; Ukraine, Armenia and Kazakhstan appear as real customers in one and
   not another; Poland is a live IDS market with 23 scored dealers and has no row in the geography
   file.
6. **Seven of the 33 IDS result reports are the same file under two names** (`BE`/`Belgium`,
   `NL`/`Netherlands`, `LUX`/`Luxembourg`, `Israel`/`Israel LCV`, `ITUK`/`UK CV`, `IUK`/`UK LCV`,
   and the byte-identical `BE`/`Belgium` pair is the one I checked directly).
7. **The coverage file understates what we hold in one direction and overstates it in another.**
   `sales_to_dealer_coverage.csv` records `real_dealers = 0` for the ITUK 2023, 2024, 2026 and
   network 2025 files, which is right — they are national aggregates. But the plain reading of the
   file, "only one source has dealer names", hides that the same market has a dealer-level file for
   2025 sitting beside four national ones, so a reader could wrongly conclude ITUK has one year of
   dealer data and no other ITUK sales-to-dealer information at all.
8. **The proposal's claim that the atlas can build the dealer X-ray and fingerprint wall "from the
   existing data immediately" is right about questions and wrong about the rest.** The 196-question
   per-dealer workbooks exist, but there is no per-dealer fleet, so any per-vehicle rate on a dealer
   page divides by the national fleet — the existing dealer pages do exactly this, and it is a
   different statement from a dealer-level rate.
9. **The proposal treats question D.2-15 as a hook into real lost-sales data. It is not.** The
   question records whether a practice exists; the transactions are absent.
10. **The distributor feedback register is an empty shell.** A file named
    `IDS_Dealer_Feedback_Register.xlsx`, listed as a register, contains a header and zero rows.
