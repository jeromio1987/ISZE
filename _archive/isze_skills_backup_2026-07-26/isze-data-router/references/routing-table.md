# ISZE Data Routing Table

All paths relative to `C:\Users\jerom\Desktop\claude\ISZE\`

## Naming convention (enforced Jun 2026)

**No version numbers in canonical filenames.** Version goes inside the file (Changelog sheet, document properties, or header comment).

- ✅ `ISUZU_UIO_Overview_2026.xlsx`
- ✅ `ISZE_GPS_Calculator.xlsx`
- ❌ `ISUZU_UIO_Overview_2026_v18.xlsx`
- ❌ `ISZE_GPS_Calculator_v9.xlsx`

When a new version of a canonical file arrives:
1. Archive the existing canonical with a date stamp: `name_archived_YYYY-MM-DD.ext`
2. File the new file under the canonical name (overwrite / move)
3. Never increment the filename version — update the Changelog sheet instead

---

## How to use this table

Match the uploaded filename (case-insensitive) against the **Filename pattern** column. Use the **Destination** and **Notes** columns to determine the full action. Patterns use `*` as wildcard.

---

## Routing table

| Category | Filename pattern(s) | Destination | Version handling | Notes |
|----------|--------------------|-----------|--------------------|-------|
| **UIO workbook** | `*UIO_Overview*.xlsx`, `*ISUZU_UIO_Overview*.xlsx` | `UIO/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` | **Overwrite canonical** — no version in filename. Archive the previous copy to `_Archive/ISUZU_UIO_Overview_2026_archived_YYYY-MM-DD.xlsx` first. Also copy to `Projects/Isuzu/prism/data/UIO.xlsx`. Update `UIO/_CURRENT/README.md` (last updated date). | Canonical has no version suffix. Version is tracked on the Changelog sheet inside the workbook. See side-effect rules in SKILL.md. |
| **LCV UIO Study (IMIT)** | `*LCV UIO*`, `*IMIT*study*`, `*CV_FY20*mid-term*` | `UIO/_SourceData/` | No versioning — overwrite. | Source data for the UIO model. |
| **Ireland / SIMI** | `*Ireland*SIMI*`, `*SIMI_Comparison*`, `*Ireland*GPS*` | `UIO/Ireland_SIMI_Comparison/` | Keep latest live; move previous to `UIO/Ireland_SIMI_Comparison/_archive/`. | Build scripts for SIMI live in the same folder. |
| **SAP billing extract** | `CY20*.XLSX`, `CY20*billing*.xlsx`, `*SAP*billing*` | `Data/_INBOX/` → `Data/raw/sales/` | If same year already exists in `raw/sales/`, pause and confirm before overwriting. Otherwise move directly. | Large files (10–30 MB). Do NOT load into context — reference parquet/CSV derivatives instead. |
| **ITUK sell-out / Parts Sales** | `*ITUK*PartSales*`, `*ITUK*pivot*`, `*Parts_Sales_Calculation*FY*` | `Data/raw/dealer_sales/ITUK/` | Append date stamp to filename if same name exists. | `Parts_Sales_Calculation_FY26.xlsx` also has a copy in `UIO/_SourceData/` — place both. |
| **UTI sell-out** | `*UTI*PartSales*`, `*UTI*Parts*`, `*UTI*sell*` | `Data/raw/dealer_sales/UTI/` | Keep all — append `_YYYY-MM` date if filename doesn't include it. | Monthly cadence. |
| **Generic dealer sell-out** | `*dealer_sell*`, `*sell_out*`, `*sellout*` | `Data/raw/dealer_sales/` | No versioning. | |
| **PR00 / IE40 price list** | `*PR00*`, `*IE40*`, `*price list*EUR*`, `*price_list*`, `*ISZE*price*` | `Data/raw/reference/` | Keep previous — rename old with date suffix before filing new. | Core pricing reference. |
| **BP / JPY pricing** | `*BP_JPY*`, `*BP FY*`, `*Base Price*FY*`, `*IML*price*FY*` | `Data/raw/reference/` | Date-stamp old version before filing new. | IML-sourced annually. |
| **BVP / Parts catalog** | `*BVP*`, `*PARTS CATALOG*`, `*BVP PARTS*`, `*parts catalog*` | `Data/raw/reference/` | Keep versioned copies — do not overwrite, rename old with date. | Large file (~350 KB). Do not load into context; use category summary in `gpt_safe/`. |
| **Margin analysis** | `*Margin analysis*`, `*margin bridge*`, `*margin report*` | `Data/raw/reference/` | Date-stamp old before filing new. | Customer-level data — internal only, no GPT upload. |
| **Customer order sales / FY scenarios** | `*Customer order sales*`, `*order simulator*`, `*FY2?_scenarios*` | `Data/raw/reference/` | No versioning — overwrite. | Feeds FY27 order simulation in Phase 1 model. |
| **Phase model (1/2/3)** | `*Phase1*`, `*Phase2*`, `*Phase3*`, `*Sales_Clean_Model*`, `*Order_Behaviour_Model*`, `*Demand_Stocking*` | `Data/models/` | No versioning — overwrite in place. | Living models. Do not archive old versions. |
| **KPI Master** | `*KPI Master*`, `*KPI_Master*` | `Data/planning/` | Move existing → `Data/planning/_archive/` before filing new. | 2.3 MB. Not in ETL pipeline. |
| **Action Plan (VPACC/FY)** | `*Action plan*VPACC*`, `*VPACC*action*`, `*Action_Plan_FY*` | `Data/planning/` | Move existing → `Data/planning/_archive/` before filing new. | |
| **IML/Kosha plan** | `*Kosha*`, `*PL Plan*FY*`, `*IML*plan*FY*`, `*FY2026 2027 2028*` | `Data/planning/` | Date-stamp old before filing new. | Internal planning — never share externally. |
| **GPS calculator** | `*GPS*Calculator*`, `*ISZE_GPS_Calculator*` | `Data/ISZE_GPS_Calculator.xlsx` | **Overwrite canonical** — no version suffix. Archive previous to `Data/_archive/ISZE_GPS_Calculator_archived_YYYY-MM-DD.xlsx`. | Canonical has no version suffix. Previous versions (v7–v9) are in `Data/_archive/`. |
| **GPS network / competitor data** | `*GPS*network*`, `*GPS*data*`, `*IDS*GPS*` | `Projects/Isuzu/gps_dashboard/data/` | Keep all — date-stamp. | If folder doesn't exist, create it. |
| **Eucon competitor pricing** | `*Eucon*`, `*eucon*`, `*competitor*pricing*`, `*IDS*pricing*` | `Data/raw/reference/` | Date-stamp old before filing new. | Used in Competitiveness Dashboard and ITUK pricing dispute. |
| **AIM classification** | `*AIM*classif*`, `*aftermarket*classif*`, `*VKWRT*`, `*AIM_data*` | `Projects/Isuzu/prism/data/` | Keep versioned — append date if filename doesn't include it. | 93.5% classification as of Mar 2026. |
| **PRISM pipeline input** | `*prism*`, `*PRISM*`, `*sales_fact*`, `*phase2_*`, `*phase3_*` | `Projects/Isuzu/prism/data/` | No versioning — overwrite parquet/CSV in place. | |
| **Tender scraper output** | `*isuzu_tenders*`, `*tender_scraper*`, `*tenders_output*` | `Tools/ISZE_Tender_Monitor_Install/` | Overwrite. | Dashboard reads from `Data/dashboards/tender_data.json` — that is a separate build step. |
| **Autodoc / KS scraper output** | `*autodoc_results*`, `*ks_results*`, `*autodoc_progress*`, `*competitor_price*` | `Tools/autodoc_scraper/` | Overwrite. | |
| **Lubricant / BESCO data** | `*lubricant*`, `*BESCO*`, `*lube*vol*`, `*oil_demand*`, `*lube_BC*` | `Projects/Isuzu/lubricants/` | Date-stamp old before filing. | If folder doesn't exist, create it. |
| **PMS coverage / filter data** | `*PMS*gap*`, `*PMS*coverage*`, `*filter*capture*`, `*PMS_ITUK*` | `Projects/Isuzu/pms_coverage/` | Date-stamp old before filing. | If folder doesn't exist, create it. |
| **DataIntegrity / pricing audit** | `*DataIntegrity*`, `*Class_0*`, `*pricing_audit*`, `*basket_impact*` | `Projects/Isuzu/pricing/` | Date-stamp old before filing. | If folder doesn't exist, create it. |
| **Competitiveness dashboard data** | `*Competitiveness*`, `*compete_data*`, `*ISZE_Compete*` | `Dashboards/` or `Data/dashboards/` | Overwrite. | |
| **Derived / export files** | `*sales_fact.parquet`, `*_clean.csv`, `derived_*.csv` | `Data/derived/` | Overwrite — machine-generated, rebuildable. | |
| **Dashboard JSON** | `*isze_data.json`, `*tender_data.json`, `*dealer_sellout*.json` | `Data/dashboards/` | Overwrite. | |

---

## Ambiguous cases

If the filename matches none of the above:

1. Read the file's firs