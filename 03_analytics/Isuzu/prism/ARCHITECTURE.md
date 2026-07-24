# PRISM — Architecture & Data Hierarchy

**Parts Revenue Intelligence & Sales Monitor**
Owner: Jerome Van der Pluym, VP Sales, ISZE (Isuzu Motors Europe, Belgian hub)
Purpose: Three-lens analytics platform for commercial vehicle parts revenue

---

## Data Hierarchy

```
LEVEL 0 — THE FLEET (source of truth: IML vehicle registration data)
│
│   Everything in PRISM is denominated against the fleet.
│   Without knowing how many trucks exist, no metric means anything.
│
└── LEVEL 1 — UIO  (Units in Operation)
    │
    │   What it is: surviving parc by distributor / model / registration year
    │   Source: IML-provided data (official, annual, highest authority)
    │   Key distinction: surviving 10-year parc ≠ total registrations
    │     N75: 8,515 surviving of 12,228 total (28.5% attrition)
    │     N35: 9,818 surviving of 10,919 total (9.4% attrition)
    │
    ├── LEVEL 2A — GPS  (Genuine Parts Share / Spend per Unit)
    │   │
    │   │   Formula: Net Sales EUR ÷ UIO = EUR per truck per year
    │   │   Question it answers: "How much of the parts wallet are we capturing?"
    │   │   Granularity: distributor × year (macro view)
    │   │   Thresholds: >€150 healthy / €50–€150 at risk / <€50 critical
    │   │   Source: ISZE net sales data (ERP/SAP, monthly)
    │   │
    │   └── Depends on: UIO (denominator)
    │
    └── LEVEL 2B — PMS  (Preventive Maintenance Service coverage)
        │
        │   Formula: Actual PNs sold ÷ Expected demand = Capture Rate %
        │   Question it answers: "Are we getting the specific service jobs?"
        │   Granularity: distributor × model × PN category (micro view)
        │
        │   Expected demand formula:
        │     Addressable parc (S2+S3) × Service frequency × Parts per service
        │     Service frequency: 40,000 km interval ÷ ~20,000 km avg annual = 0.5/yr
        │     (Previous assumption of 1.5/yr was WRONG — do not reuse)
        │
        │   Phase 1 scope: N75 only (NPR75/4HK1 + NPR88/4JZ1)
        │   Phase 2: N35 (NLR87/RZ4E + NLR88/4JZ1) — follows N75 pilot
        │
        │   Source: ISZE sales data tagged against confirmed PN registry
        │   PN authority: ITUK PMS guidance (Apr 2026) — 55 confirmed PNs
        │
        └── Depends on: UIO (surviving parc denominator)
```

GPS and PMS are siblings — both divide sales against UIO but at different levels of granularity.
GPS = all parts, all distributors, EUR/truck.
PMS = specific maintenance PNs, capture rate %, opportunity gap.

---

## Data Sources

| Layer | Dataset | Source | Cadence | Authority |
|-------|---------|--------|---------|-----------|
| Level 1 | UIO — Units in Operation | IML vehicle registration data | Annual | Highest — ground truth for fleet size |
| Level 2A | Net Sales EUR | ISZE ERP/SAP export | Monthly | Official |
| Level 2B | PN Registry | ITUK PMS guidance (Apr 2026) | Static (update on new guidance) | Confirmed |

---

## Key Numbers

| Metric | Value | Notes |
|--------|-------|-------|
| N75 surviving parc | **8,515** | Of 12,228 total registered — 28.5% attrition |
| N35 surviving parc | **9,818** | Of 10,919 total registered — 9.4% attrition |
| Service frequency | **0.5 / year** | 40,000 km interval ÷ ~20,000 km avg annual mileage |
| Addressable parc default | **70%** | S2+S3 proportion of surviving parc |

> **Warning:** A previous assumption of 1.5 services/year was incorrect. Use 0.5/yr.

---

## Dependency Matrix

|  | **UIO** | **GPS** | **PMS** |
|--|---------|---------|---------|
| **UIO** | — | UIO is the denominator for GPS (EUR / truck) | UIO is the denominator for expected demand |
| **GPS** | Requires UIO to produce any meaningful figure | — | Independent (different granularity) |
| **PMS** | Requires UIO (surviving parc) to calculate expected demand | Independent (different granularity) | — |

Reading the matrix: row "requires" column. UIO has no upstream dependencies. GPS and PMS both depend on UIO. GPS and PMS do not depend on each other.

---

## How to Update Data

### UIO update protocol

UIO files follow beta versioning. See `data/README.md` for the full protocol. The short version:

1. Place the new IML-provided file in `data/` following the naming convention in `data/README.md`.
2. Set `PRISM_BETA=true` (PowerShell: `$env:PRISM_BETA="true"`) to run against the beta file.
3. Validate: confirm N75 and N35 surviving parc totals match expected IML figures.
4. Promote to production by updating `config.py` once validated.

The beta / production toggle is controlled in `config.py`. Pages read `st.session_state["beta_mode"]` at runtime.

### Sales data refresh

Sales data (for GPS and PMS) is sourced from ISZE ERP/SAP. Monthly refresh cadence. Place updated exports in the path configured in `config.py`. The GPS engine expects columns: `distributor_code`, `net_sales_value`, `billed_qty`, `year`, `month`, `part_number`, `description`.

### PN registry changes

The PMS PN registry lives in `modules/pms_engine.py` as `PMS_PN_REGISTRY` (ITUK pilot authority). **Capture actuals** also include every PMS-flagged row in `BVP PARTS CATALOG.xlsx` via `bvp_pn_dimension` (`CAPTURE_FILL_CATALOG_PMS` in `build_bvp_p0_p1.py`). Registry changes require ITUK guidance; catalog changes follow the Excel refresh.

1. New ITUK guidance → update `PMS_PN_REGISTRY` / `_MULTI_MODEL`.
2. Catalog sheet changes → re-run `build_bvp_p0_p1.py`.
3. Re-run PMS capture — historical figures shift when PNs are added to either source.

---

## Module Map

| File | Layer | Role |
|------|-------|------|
| `modules/uio_loader.py` | Level 1 | Loads and normalises UIO Excel file |
| `modules/gps_engine.py` | Level 2A | GPS calculations — spend per unit, trends, KPIs |
| `modules/pms_engine.py` | Level 2B | PMS registry, classification, capture rate, opportunity |
| `pages/1_UIO.py` | Level 1 | Streamlit page — fleet size explorer |
| `pages/2_GPS.py` | Level 2A | Streamlit page — spend per unit dashboard |
| `pages/3_PMS.py` | Level 2B | Streamlit page — PMS capture rate dashboard |
| `app.py` | Entry point | Streamlit multi-page app shell |
| `config.py` | Config | File paths, beta mode flag |
