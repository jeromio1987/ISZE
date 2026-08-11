# ISZE Pricing data — map for Spec v1 / engine enquiries

**Last updated:** 2026-08-10 (OEM street 15/22; readiness dashboard; Mode B status brief)  
**Spec:** `00_docs/ISZE_Pricing_Spec_v1.md` · **Engine:** `03_analytics/isze_pricing/`  
**Readiness dashboard (Mode A):** `02_dashboards/pricing/ISZE_Pricing_Engine_Readiness_Dashboard.html`  
**Dashboard data:** `01_data/14_dashboards/pricing_engine_readiness.json` · **Mode B notes:** `01_data/01_Pricing/PRICING_ENGINE_VS_CLASS_NOTES_B.md`

Raw Excel stays immutable under `_raw/`. Day-to-day work uses the **parquet** tables in `01_data/00_derived/`.

---

## What to use for what

| Need | Best source | Derived table |
|------|-------------|-----------------|
| **Price class + base price (BP_JPY) + Source + FOB + SP_EUR** | `Price_file_2026_full.xlsx` | `pricing_list_pn.parquet` |
| **Current vs New BP / class (IML revision, Layer 0 `IML_CORRECTION`)** | `CY2026_Price_Revision_PRICE_CD.xlsx` | `pricing_revision_cd.parquet` |
| **L12M qty weights (Laspeyres / allocation)** | `pricing_simulation_2026_5pct.xlsx` → `PR00 simulation` | `pricing_sim_pr00_l12m.parquet` |
| **IE40 PR00 list EUR (official condition)** | `Price_file_PR00_IE40_20260810.xlsx` ★ newest | `pricing_pr00_ie40.parquet` |
| **ZPR1 / CIS customer list prices** | `EXPORT_ZPR1_20260810.xlsx` ★ newest | `pricing_zpr1.parquet` |
| **ZPR1 customer dim** | same | `pricing_zpr1_customers.parquet` |
| **Key ZPR1 SPs wide (UMI/UTI/RUS/CBC…)** | same | `pricing_zpr1_key_wide.parquet` |
| **One join for chat / Spec checks** | — | `pricing_pn_enquiry.parquet` |
| **3-level AIM taxonomy on IE40** | `IE40 … PR00_3_level_classified_GPT.xlsx` | keep; no BP/class |
| **Calc book for Israel (older)** | `UTI_final_price_file.xlsx` | superseded for list SP by EXPORT_ZPR1 |

**IML formula (unchanged):** `FOB = BP_JPY / FX × source_discount` · `SP = FOB / class_factor`  
FX / discounts / class factors live in `03_analytics/isze_pricing/config.yaml` (FX 163.7 as of 2025-10-01).

---

## 2026-08-10 drop (go-live for Layer 4 lists)

| File | Role |
|------|------|
| `EXPORT_ZPR1.XLSX` → `_raw/EXPORT_ZPR1_20260810.xlsx` | Customer × PN ZPR1/CIS prices (~931k rows, 42 customers). Includes **UMI 1797**, **UTI 1799**, ISUZU RUS, CBC, … |
| `Price file 202610082026.XLSX` → `_raw/Price_file_PR00_IE40_20260810.xlsx` | IE40 **PR00** list EUR (~165k rows). Not the BP/Class calc book — SAP list with `Price Condition Type=PR00`. |

Keep using `Price_file_2026_full.xlsx` for **class + BP_JPY + FOB**.

---

## Folder layout

```
01_data/01_Pricing/
  PRICING_DATA.md
  Price_file_2026_full.xlsx              ← calc book (class/BP)
  Price_file_PR00_IE40_20260810.xlsx     ← newest IE40 PR00 list
  EXPORT_ZPR1_20260810.xlsx              ← newest ZPR1 export
  _raw/                                  ← immutable as-received
    CY2026_Price_Revision_PRICE_CD.xlsx
    Price_file_2026_full.xlsx
    Price_file_PR00_IE40_20260810.xlsx
    EXPORT_ZPR1_20260810.xlsx
    pricing_simulation_2026_5pct.xlsx
    …

01_data/00_derived/
  pricing_list_pn.parquet
  pricing_revision_cd.parquet
  pricing_sim_pr00_l12m.parquet
  pricing_pr00_ie40.parquet
  pricing_zpr1.parquet
  pricing_zpr1_customers.parquet|.csv
  pricing_zpr1_key_wide.parquet
  pricing_pn_enquiry.parquet
  pricing_pn_enquiry_active.csv
```

Rebuild:

```powershell
cd $env:ISZE_ROOT
python 01_data/91_build/build_pricing_enquiry_tables.py
```

---

## PRICE CD class codes

IML CD uses 2-character codes (`XC`, `XD`, `EV`, …). Spec `class_factor` uses one letter (`C`, `D`, `V`, …).

Derived tables keep `part_class_*_raw` and mapped `price_class_*`.  
For formula work prefer **`pricing_list_pn.price_class`**.

---

## OEM peer basket (Layer 1 street scaffold)

| File | Role |
|------|------|
| `03_analytics/isze_pricing/oem_peer_basket.csv` | Working PN × peer rows (**22** unique OE mapped; **15** with street → **22** priced basket rows) |
| `01_data/01_Pricing/_raw/oem_peer_basket_seed_20260810.csv` | Seed snapshot (2026-08-10) |
| `03_analytics/isze_pricing/OEM_PEERS.md` | Approved LCV + CV peers (incl. DAF); Israel pending |
| `03_analytics/isze_pricing/OEM_STREET_ARRANGE.md` | **Arrange package** — 22-OE fill → ingest → alloc |
| `03_analytics/isze_pricing/oem_peer_scrape_list.csv` | Street fill template (**15/22** filled; 7 not_found) |
| `03_analytics/isze_pricing/ingest_oem_peer_street.py` | Ingest filled street EUR into basket (propagates by OE) |
| `03_analytics/isze_pricing/premiums.py` | `OEM_PEERS` + `apply_oem_benchmark_to_config_block` |
| `00_derived/pricing_zpr1_pr00_diff_basket_20260810.csv` | Diagnostic: UMI/UTI ZPR1 vs PR00 % on basket Isuzu PNs (UTI≠UMI) |
| `00_derived/oem_peer_readiness_20260810.csv` / `.json` | Per-cat n priced / gap to `oem_benchmark` |
| `00_derived/oem_peer_street_vs_isze_20260810.csv` | Peer street vs Isuzu street (PR00×1.785) |
| `00_derived/eucon_comparable_oem_gap_20260810.csv` | All Eucon COMPARABLE OE rows + already_mapped flags |
| `01_Pricing/PRICING_STATUS_BRIEF_2026-08-10.md` | Mode B one-pager (where / blocked / next) |
| `02_dashboards/pricing/ISZE_Pricing_Engine_Readiness_Dashboard.html` | Mode A readiness + class-vs-engine comparison |
| `00_derived` ← `14_dashboards/pricing_engine_readiness.json` | JSON behind that dashboard |
| `01_Pricing/PRICING_ENGINE_VS_CLASS_NOTES_B.md` | Mode B blunt traps (engine vs uniform +3%) |

Re-seed / rebuild scrape list:

```powershell
python 03_analytics/isze_pricing/seed_oem_peer_basket.py
python 03_analytics/isze_pricing/_build_oem_peer_scrape_list.py
```

Do **not** invent OE PNs or peer street EUR. Live Autodoc/KS peer-OE scrape is blocked — use the arrange package (manual/browser fill + ingest). Until street filled (≥3 peers/cat), allocation stays on `iam_derived` (Eucon brand-tier %).

---

## Eucon / PartsPool (filed 2026-08-10)

| File | Role |
|------|------|
| `_raw/eucon_pricing_partspool_20260329.xlsx` | PartsPool batch 2026-03-29 (from `91_legacy/…/eucon_pricing.xlsx`) |
| `_raw/eucon_crossref_iam_20260329.csv` | **822** IAM crossref rows (45 Isuzu PN; 469 unique competitor PN pairs) |
| `_raw/Eucon_ISUZU_Europe_OEM_IAM_Benchmark_UK_IL_2021_V02_quotation.pdf` | 2021 OE-1196 quotation (methods/price levels) — not results |
| **`_raw/Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx`** | ★ **2023–24 UK OEM survey rawdata** (missing export recovered 2026-08-10) |
| **`_raw/Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx`** | ★ **2023–24 ITUK OEM survey rawdata** (DAF peer OE map) |
| **`_raw/Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx`** | ★ **2023–24 UK IAM survey rawdata** (LCV + HCV sheets) |
| `00_derived/eucon_price_gap.csv` | 44-PN summary (existing); **`Avg_Delta_pct` = vs IE40 list** |
| `00_derived/eucon_price_gap_street_qa.csv` | Same + `isze_street_eur = IE40×1.785` and street deltas |

**How it feeds the engine**

- **IAM / street compare:** `build_pricing_action_map.py` and `premiums.category_ceilings_from_eucon()` — street = PR00/IE40 × **1.785**. Ignore raw `Avg_Delta_pct` for street conclusions.
- **OEM peer / `oem_benchmark`:** 2023 OEM survey sheets have clear **Isuzu PN ↔ peer OE PN** columns (see peek below). Usable for next `oem_peer_basket` wire — **do not invent fills**; join only where COMPARABLE + approved peer brand. Survey `CompetitorPrice` / `ISZE price` are **list-side GBP** from Eucon — not PR00×1.785 street. Restate before street conclusions.

**Pricing-point QA:** probe deltas vs raw list are the wrong point for counter/street claims. Same caveat applies to 2023 survey list GBP. Detail + examples in `03_analytics/isze_pricing/OEM_PEERS.md` § Eucon.

### 2023 Price Survey peek (filed only — not wired)

| File | Sheets | Data rows | Key columns (OEM) |
|------|--------|-----------|-------------------|
| `Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx` | `Isuzu UK` (212), `Sheet1` (helper) | 212 | `CustomerPartNumber` ↔ `CompetitorPartNumber` + `CompetitorBrand`; `Comparability`; `ISZE price` / `CompetitorPrice` (GBP) |
| `Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx` | `Sheet1` | 138 | Same OEM map cols (no vehicle headers); all `CompetitorBrand=DAF` |
| `Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx` | `LCV` (66), `HCV` (170) | 236 | `Isuzu Part Number` ↔ IAM `Competitor Part Number` / brand; list + workshop purchase cols |

UK OEM brands: DAF 138 · Ford 37 · Toyota 37 — **179 COMPARABLE** with both PNs (129 unique Isuzu / 124 unique peer OE). ITUK: 109 COMPARABLE, 92 unique Isuzu / 53 peer OE (DAF only). IAM: competitor PN filled on 39/66 LCV and 92/170 HCV (rest “not available”).

**Hard QA (Mode B):** `_raw/Eucon_PriceSurvey_2023_QA.md` — **OE crossrefs safe; survey prices = list (not street).** Basket: **22** unique peer OEs mapped (market-aligned); **15** genuine street fills (ingest propagates → 22 priced rows). Eucon COMPARABLE expand exhausted for WANT cats (no new Isuzu PNs appended; 85 survey PNs fail strict filter/brake/clutch cat gate). `oem_benchmark` live for **air_filter** + **oil_filter** only.

---

## DB→DLR price response (ITUK + UTI only)

| File | Role |
|------|------|
| `00_derived/price_elasticity_db_dlr_ituk_uti.csv` | Category-level **proxy** rows + blocked YoY stubs |
| `01_Pricing/PRICE_ELASTICITY_DB_DLR_ITUK_UTI.md` | Method note (Mode B) |
| Builder | `01_data/91_build/build_price_elasticity_db_dlr_ituk_uti.py` |
| Engine soft join | `03_analytics/isze_pricing/db_dlr_response.py` via `paths.db_dlr_response` |

- **Volume** = sell-out qty CY2025 (ITUK dealer×PN → network; UTI network). True DB→DLR.
- **Price** = ISZE→DB ASP / PR00 list pass-through — **lasting basis for now**. Dealer invoice prices are **not a near-term ask**.
- **`measure_kind=proxy`** — true YoY arc elasticity blocked (one full CY). Do **not** claim ISZE→DB elasticity; leave `price_volume_elasticity.csv` as stocking-side.
- Israel = **UTI only** (never UMI).
- **Alloc soft signal:** diagnostic join + adverse flags on exact (db, PMS cat); **never** scales `delta` / +3% target. See method note § Engine plug-in.

```powershell
python 01_data/91_build/build_price_elasticity_db_dlr_ituk_uti.py
```

---

## Caveats (Spec-aligned)

- PRICE CD is one revision snapshot, not multi-year PR00 history.
- `EXPORT_ZPR1` is **customer-condition** list price (EUR), not BP_JPY. Restate vs PR00 before EU read-across (enquiry columns `zpr1_umi_vs_pr00` / `zpr1_uti_vs_pr00`).
- UTI ≠ UMI — never blend Israel IDS/GPS with UTI ZPR1 rows.
- ~15% billed revenue may still lack PR00 (`NO_LIST`).
- Supersession: use `newest_pn` / `is_superseded_row`.
