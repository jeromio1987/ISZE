# ISZE — GPT Enterprise Deep Dive Briefing
**Date:** 15 May 2026  
**Author:** Jerome Van der Pluym, VP Sales ISZE  
**Purpose:** Single briefing to upload **with your ~45 context MD files** so Enterprise GPT can explore every product, dashboard, and analytics possibility grounded in what was actually built today.

---

## How to use this file

1. Upload this file to your Custom GPT Knowledge (or attach in a new project chat).
2. Keep your existing **45 MD context pack** uploaded — this briefing **does not replace** them; it **adds** today's pipeline outputs, verification results, and opportunity framing.
3. Optionally upload these **aggregated CSVs** from `ISZE/Data/derived/` (safe — no payer-level billing):
   - `pms_capture_by_db_year.csv` (1,134 rows)
   - `gps_spu_by_distributor.csv` (71 rows)
   - `mix_genuine_bvp_pms.csv` (426 rows)
   - `aim_bvp_family_risk.csv` (385 rows)
   - `db_benchmark_mix.csv`
4. **Never upload:** `raw/sales/CY*.XLSX`, `sales_fact.parquet`, margin reports, or customer-level files.

### Suggested opening prompt for GPT

> You have the ISZE context pack (~45 MD files) plus `GPT_DEEP_DIVE_BRIEFING_2026-05-15.md` and optional derived CSVs.  
> Task: Produce a **ranked portfolio** of 25+ analytics products, tools, campaigns, and dashboards we could build in the next 12 months. For each: (a) business question answered, (b) data required (available / partial / missing), (c) effort S/M/L, (d) owner (ISZE / ITUK joint / IML), (e) revenue or retention hypothesis, (f) dependency on PRISM vs HTML vs Excel vs Power BI.  
> Challenge assumptions. Flag where old docs contradict today's verified numbers. Separate **ITUK pilot** from **network rollout**.

---

## Executive summary — what was built today (15 May 2026)

### 1. Canonical data layer (`ISZE/Data/`)

- Migrated **10 Excel files** from `new files/` into structured folders (`raw/`, `models/`, `planning/`, `derived/`, `dashboards/`).
- **434,861 billing lines** consolidated into `derived/sales_fact.parquet` (CY2023–2025).
- Created `DATA_MANIFEST.md`, ingest `_INBOX/`, and GPT-safe dictionary.

### 2. PRISM analytics pipeline (P0–P5)

Python builds under `Projects/Isuzu/prism/scripts/` now produce **verified derived tables**:

| Build | Output | Rows | What it measures |
|-------|--------|------|------------------|
| **Sales fact** | `sales_fact.parquet` | 434,861 | Canonical billing (date, sold_to, material, qty, EUR) |
| **P0** | `bvp_pn_dimension.csv` | 918 PNs | PN → family, genuine/BVP, PMS flag (325 PMS-flagged) |
| **P1** | `pms_capture_by_db_year.csv` | 1,134 | Capture % + € gap by DB × year × PMS category × line_type |
| **P2** | `mix_genuine_bvp_*.csv`, `db_benchmark_mix*.csv` | 426+ | BVP vs genuine mix, YoY, network benchmark |
| **P4** | `gps_spu_*.csv` | 71 / 975 / 1,062 | Spend per unit (GPS) by distributor, family, PMS |
| **P5** | `aim_*.csv` | 69 / 385 | Aftermarket intelligence exposure × BVP family |

**Verification:** 43/43 checks passed (`_verification_report.md`, 2026-05-15T16:41:29Z). Pipeline is green.

### 3. PRISM v2 application scaffold

- Streamlit multi-page app: UIO → GPS → PMS (15 files, smoke-tested).
- Reads `ISZE/Data/derived/` first; `gps_dashboard/` remains production until promotion.
- Architecture doc defines 3-level hierarchy: Fleet → UIO → GPS / PMS siblings.

### 4. Documentation sync

- `isuzu-docs` GitHub repo cloned; memory + Data docs aligned for agent/GPT use.

---

## Golden numbers (verified 15 May 2026 — use these over older docs)

| Metric | Value | Source |
|--------|-------|--------|
| Sales_Fact rows | **434,861** | CY2023-24 + CY2025 |
| ITUK UIO (N75 pilot denominator) | **22,389** | DVLA / Parts Sales Calc FY26 — **not** Hasegawa |
| PMS PN registry | **55 PNs**, 4 model lines | ITUK guidance Apr 2026 |
| Service frequency (PMS demand) | **0.5 / year** | 40k km ÷ ~20k km/yr — **not** 1.5/yr |
| ITUK oil filter capture 2024 | **61.1%** | P1 verification band 55–70% |
| ITUK oil filter capture 2025 | **80.7%** | P1 verification band 75–90% |
| ITUK GPS spend/unit 2024 | **€302** | `gps_spu_by_distributor.csv` |
| ITUK GPS spend/unit 2025 | **€249** | (UIO proxy flag true in 2025 row) |
| N75 surviving parc | **8,515** of 12,228 | PRISM architecture |
| N35 surviving parc | **9,818** of 10,919 | PRISM architecture |

⚠️ **Doc drift warning:** `memory/projects/pms-coverage.md` still mentions 1.5 services/yr and old 9.8% capture — **superseded** by today's P1 build for network analytics. Keep narrative docs for business context; use derived CSVs for numbers.

---

## Data architecture (4 tiers)

```
TIER 0 — SAP / Power BI / ISZE network (never to GPT)
    ↓ manual export
TIER 1 — C:\Users\jerom\Desktop\claude\ISZE\Data\
    raw/sales, models (Phase 1-3 Excel), derived/, planning/
    ↓ aggregates only
TIER 2 — GPT Enterprise Knowledge (MD + small CSV + this briefing)
    ↓ deploy
TIER 3 — GitHub Pages HTML dashboards (MASTER_DASHBOARD, etc.)
```

**Claude/Cursor** reads Tier 1 live. **GPT Enterprise** reads Tier 2 only. You are the bridge.

---

## Derived datasets — schemas & business meaning

### `sales_fact.parquet` (not for GPT upload)

| Column | Meaning |
|--------|---------|
| billing_date | SAP billing date |
| sold_to | Distributor code |
| material | Part number |
| billed_qty | Quantity |
| net_sales_eur | Net value EUR |

### `bvp_pn_dimension.csv` (918 rows)

Maps every catalog PN to **product_family**, **product_subgroup**, **line_type** (`genuine` | `bvp`), **pms_flag**, **pms_category**. Foundation for all P1–P5 cuts.

### `pms_capture_by_db_year.csv` (1,134 rows)

| Column | Meaning |
|--------|---------|
| year, distributor_code | Time × market |
| pms_category, line_type | oil_filter, fuel_filter, … × genuine/bvp/total |
| uio_units | Denominator (ITUK = 22,389 from DVLA) |
| expected_qty, actual_qty | Demand model vs sales |
| capture_rate | actual / expected |
| revenue_gap_eur | € opportunity |
| scope | Currently `N75_only` |

**ITUK oil filter example (total line):**

| Year | Capture | Actual qty | Revenue EUR |
|------|---------|------------|-------------|
| 2023 | 100%* | 12,983 | 105,215 |
| 2024 | 61.1% | 4,791 | 36,460 |
| 2025 | 80.7% | 6,322 | 54,335 |

\*2023 total >100% indicates demand formula tuning needed for early year — treat 2024–2025 as pilot trend years.

### `gps_spu_by_distributor.csv` (71 rows)

**Formula:** total_sales_eur ÷ uio_units = spend_per_unit_eur  
**Traffic lights:** green >€150, amber €50–150, red <€50

**ITUK GPS trend:**

| Year | Sales EUR | UIO | SPU EUR | Light |
|------|-----------|-----|---------|-------|
| 2023 | 5.84M | 20,204 | 289 | green |
| 2024 | 6.77M | 22,389 | 302 | green |
| 2025 | 5.58M | 22,389 | 249 | green |

### `mix_genuine_bvp_pms.csv` (426 rows)

BVP vs genuine **unit and EUR share** by DB × PMS subgroup with YoY pp change and `substitution_flag` when genuine collapses as BVP rises.

### `aim_bvp_family_risk.csv` (385 rows)

Cross-reference BVP catalog sales with **AIM (aftermarket intelligence)** high-risk revenue by family — prioritises pricing / campaign response.

### `db_benchmark_mix.csv`

Each distributor's BVP EUR share vs **network median** — peer pressure narrative for sales visits.

---

## PRISM — product state

**Name:** Parts Revenue Intelligence & Sales Monitor  
**Location:** `ISZE/Projects/Isuzu/prism/`  
**Status:** v2 scaffold built; **not yet production** (GPS dashboard v1 still live)

| Page | Layer | Capability |
|------|-------|------------|
| UIO | 1 | Fleet parc by DB, model, year; IML surviving parc banner |
| GPS | 2A | SPU, trends, region, part explorer, Excel export |
| PMS | 2B | Capture rates, ITUK incentive tiers, 2026 campaign calendar |

**Beta rule:** UIO changes require `PRISM_BETA=true` until Jerome signs off — v17 is company-wide production.

---

## ITUK commercial context (from Parts Sales Calc / pilot work)

**FY26–FY30 framing (internal Excel logic, May 2026):**

| Year | ITUK parc (units) | Parts potential EUR | Actual parts EUR | Share of potential |
|------|-------------------|---------------------|------------------|-------------------|
| 2024 | 22,389 | 16.0M | 12.3M | 77.0% |
| 2025 | 23,068 | 16.4M | 12.9M | 78.6% |
| 2026 | 24,173 | 17.0M | 13.1M | 77.4% |
| 2027 | 25,390 | 17.7M | 13.8M | 78.1% |

**Stretch scenario (FY26–27):** +3% / +7% on potential → share rises to ~80% / ~85%.

**ISZE → ITUK supply capture** (~66% × 1.12 margin bridge): actual capture of ISZE supply vs theoretical ~36–57% — **major upside** if PMS + distribution improve.

**Strategic framing (from `ISZE_Strategic_Position_2026.md`):**

- ITUK pricing = commercial pass-through of IML formula; not existential.
- Kosha EUR 52.1M target likely unreachable; build **credible execution record** via PMS, lubricants, documented KPIs.
- PMS filters competitively priced vs IAM at ASC; brakes exposed.

---

## 3-phase Excel pipeline (parallel track)

Still active in `Data/models/`:

1. **Phase 1** — Sales_Fact clean, DQ, SaTy → should reconcile to parquet row counts.
2. **Phase 2** — Customer order behaviour, part criticality, action engine.
3. **Phase 3** — Demand, stocking, PRD candidates + BVP catalog.

**Not yet exported:** `phase2_*.csv`, `phase3_*.csv`, `sales_fact_monthly.csv` — high-value GPT opportunities once built.

---

## Existing tools & dashboards (from context pack — not rebuilt today)

| Asset | Status | Deep-dive angle |
|-------|--------|-----------------|
| MASTER_DASHBOARD.html (7 tabs) | Live | Unify KPIs with PRISM derived feeds |
| GPS Dashboard Streamlit v1 | Production Apr 2026 | Merge into PRISM |
| Competitiveness Dashboard HTML | v1 Mar 2026 | Link heatmap gaps to `aim_*` + PMS capture |
| SPA Optimizer / Tender Monitor / scrapers | Built | Automate AIM + tender → derived |
| 11 HTML dashboards | Live | JSON refresh from `Data/dashboards/` |
| Phase 1–3 Excel models | Migrated | Power Query automation vs Python |
| GPT_Enterprise context pack (6 MDs) | Apr 2026 | Sync with this briefing monthly |

---

## Documentation index (~53 MD files in ISZE — your ~45 upload set)

Grouped for GPT retrieval. Paths relative to `ISZE/`.

### Data & pipeline

| File | One-line purpose |
|------|------------------|
| `Data/DATA_MANIFEST.md` | Registry, GPT flags, refresh protocol |
| `Data/README.md` | Folder overview |
| `Data/derived/README.md` | P0–P5 output definitions |
| `Data/derived/_verification_report.md` | QA sign-off (today) |
| `Data/gpt_safe/DATA_DICTIONARY.md` | Field definitions for GPT |
| `Data/_INBOX/README.md` | Ingest staging rules |
| `memory/projects/sales-analytics-pipeline.md` | Agent canonical paths + build commands |

### PRISM & GPS

| File | One-line purpose |
|------|------------------|
| `Projects/Isuzu/prism/ARCHITECTURE.md` | UIO → GPS / PMS hierarchy |
| `Projects/Isuzu/prism/CHANGELOG.md` | v2 build log (today) |
| `Projects/Isuzu/prism/data/README.md` | UIO beta/production rules |
| `Projects/Isuzu/prism/NAME_CANDIDATES.md` | Rejected product names |
| `Projects/Isuzu/gps_dashboard/GPS_Dashboard_Roadmap.md` | v1 GPS scope |
| `Projects/Isuzu/data/sales_export_specification.md` | SAP export columns |
| `Projects/Isuzu/data/gps_pms_framework_spec.md` | GPS+PMS framework |
| `Projects/Isuzu/gps_dashboard/sales_export_specification.md` | GPS export spec (dup path) |

### Strategy & company

| File | One-line purpose |
|------|------------------|
| `AI_Stack_Architecture_Apr2026.md` | Claude vs GPT routing, 4 tiers |
| `Isuzu/ISZE_Strategic_Position_2026.md` | Pricing, Kosha, ITUK framing |
| `Isuzu/ISZE_DealerData_Initiative_FY2027.md` | Dealer data programme |
| `Isuzu/Divers/ISZE_Analytics_Strategy_Mar2026.md` | Analytics roadmap |
| `Isuzu/Divers/pricing_logic_2026.md` | 2026 price round logic |
| `Isuzu/isze-company-context.md` | Org, markets, roles |
| `Isuzu/isze-working-style.md` | How Jerome works with AI |
| `Isuzu/isze-excel-conventions.md` | Excel formatting rules |
| `Isuzu/isze-pptx-conventions.md` | PowerPoint rules |
| `Isuzu/isuzu-ppt-template/SKILL.md` | PPT template skill |

### ITUK / PMS / specs

| File | One-line purpose |
|------|------------------|
| `Isuzu/Divers/ISZE_ITUK_PMS_Pilot_Success_Criteria.md` | Pilot KPIs |
| `Isuzu/Divers/ISZE_PN_Service_Mapping_Spec.md` | PN → service mapping |
| `Isuzu/Divers/ISZE_VKWRT_Extraction_Spec.md` | VKWRT data extraction |
| `memory/projects/pms-coverage.md` | PMS project narrative (check dates) |
| `memory/projects/competitiveness.md` | Competitiveness dashboard findings |
| `memory/projects/uio.md` | UIO data rules |
| `memory/projects/lubricants.md` | Lubricants growth programme |
| `memory/projects/aftermarket-intelligence.md` | AIM programme |
| `Projects/Isuzu/ISZE_Lubricants_Potential_Cowork.md` | Lubricants quant case |

### Action plans & roadmaps

| File | One-line purpose |
|------|------------------|
| `memory/projects/action-plan-fy2026.md` | FY26 campaigns |
| `memory/projects/action-plan-fy2027.md` | FY27 VPACC alignment |
| `Dashboards/ROADMAP.md` | HTML dashboard plan |
| `Tools/SCRAPERS_ROADMAP.md` | Scraper automation plan |
| `UIO_Cleanup_Proposal_Apr2026.md` | UIO file hygiene |

### People & memory

| File | One-line purpose |
|------|------------------|
| `memory/context/isuzu.md` | Company context |
| `memory/glossary.md` | Terms (SaTy, BVP, PMS, …) |
| `memory/people/jerome.md` | Role, priorities |
| `memory/people/jerome-evaluations.md` | Performance context |
| `UIO/_CURRENT/README.md` | Active UIO file pointer |

### Pricing engine & misc

| File | One-line purpose |
|------|------------------|
| `isuzu pricing engine/ISZE_SPA_Optimizer_ITUK_README.md` | SPA optimizer |
| `Isuzu/JARVIS/files/README.md` | JARVIS file index |
| `README.md` | ISZE repo entry |
| `.cursor/skills/isze-verify-pipeline/SKILL.md` | Verify-after-build skill |

### Duplicate skill-update copies (`Isuzu/_SKILL_UPDATE/`)

Mirror of company-context, excel/pptx conventions, working-style — use **non-underscore** paths as canonical.

---

## Deep-dive opportunity buckets (for GPT to expand)

Ask GPT to elaborate each bucket into **concrete deliverables** with the table schema above.

### A. ITUK pilot (next 6 months)

- Dealer-level PMS drill-down (`get_dealer_capture_detail` spec in PRISM)
- Incentive tier tracker vs 2030 stretch (already in PMS page design)
- Campaign calendar × seasonal weights × capture projection
- Genuine vs BVP split dashboards per filter category
- Parts Sales Calc reconciliation (parc growth × €/vehicle × share)

### B. Network rollout (12–24 months)

- Clone PMS engine to N35 phase 2 (RZ4E, 4JZ1 registries)
- DB benchmark league tables (`db_benchmark_mix`)
- Region packs (UK/IE, MENA, Nordics, CEE) from GPS SPU
- CIS markets with UIO proxy fixes (Ukraine, Kazakhstan zero-UIO rows)

### C. Pricing & competitiveness

- Link AIM high-risk families to SPA / price actions
- Brake category exposure vs PMS filter strength (competitiveness HTML)
- FX / BP_JPY scenario narrators for IML conversations
- Slow-mover PN class differentiation (strategic position doc)

### D. Phase 2–3 Excel + automation

- Part criticality → stocking actions export
- Customer SaTy financial impact
- PRD candidate generator from demand model
- Power Query → parquet scheduled refresh

### E. Executive & joint (ISZJ / IML)

- PMS joint presentation refresh with **verified** capture curves
- GPS “wallet share” storyline by segment (CV/LCV split)
- Kosha-aligned KPI tree with honest gap commentary
- Lubricants cross-sell potential model

### F. AI product layer

- PRISM promotion checklist vs gps_dashboard
- MASTER_DASHBOARD tab fed from `derived/*.csv`
- GPT-safe monthly `pms_capture_summary.csv` auto-generation
- Cowork scheduled verify + brief generation

---

## Privacy & compliance guardrails

| OK for GPT | Never for GPT |
|------------|---------------|
| This briefing | `raw/sales/CY*.XLSX` (payer-level) |
| Context pack MDs | `sales_fact.parquet` full file |
| Aggregated derived CSVs | Margin analysis (customer-level) |
| `dashboards/isze_data.json` | Personnel evaluations detail |
| Strategic framing docs | Kosha internal-only sections marked “not for external” |

---

## Gaps & next builds (honest)

- [ ] Phase 1 Power Query export validated vs parquet (row-level reconcile)
- [ ] `gpt_safe/pms_capture_summary.csv` — DB-year aggregates for smaller upload
- [ ] Phase 2/3 derived exports
- [ ] PRISM production promotion + UIO v18 beta test
- [ ] Fix 2023 capture >100% anomalies (demand formula calibration)
- [ ] N35 PMS registry expansion
- [ ] Dealer-level entity split (Cust 2574 IUK vs 2575 ITUK) in pipeline
- [ ] Context pack sync — retire outdated capture-rate references in older MDs

---

## Build commands (reference — Claude executes, not GPT)

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism
python scripts/build_sales_fact_from_cy.py
python scripts/build_bvp_p0_p1.py
python scripts/build_bvp_p2_mix.py
python scripts/build_bvp_p4_p5.py
python scripts/verify_derived_pipeline.py
# or: .\scripts\run_pipeline_and_verify.ps1
```

---

## Version

| Item | Value |
|------|-------|
| Briefing version | 1.0 |
| Data snapshot | 2026-05-15 |
| Verification | 43 pass / 0 fail |
| Compatible with | isuzu-docs context pack + Enterprise GPT May 2026 |

---

*End of briefing. Upload alongside your 45 MD files and optional derived CSVs for deep-dive analysis.*
