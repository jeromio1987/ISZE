# GPS & PMS DASHBOARD FRAMEWORK SPECIFICATION
## For Cowork Implementation - Token-Efficient & Expandable Design

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER (Minimal)                     │
├─────────────────────────────────────────────────────────────┤
│  1. Sales data (348k rows) → Aggregated to monthly/PN       │
│  2. UIO data (30 rows) → Static reference                   │
│  3. Part classification (500 PNs) → Lookup table            │
│  4. Distributor mapping (28 entities) → Lookup table        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  CALCULATION ENGINE (Python)                 │
├─────────────────────────────────────────────────────────────┤
│  Module 1: Data Prep (clean, map, filter)                   │
│  Module 2: GPS Calculator (spend/UIO, capture rate)         │
│  Module 3: PMS Analyzer (filter coverage, trends)           │
│  Module 4: Export Engine (Excel/CSV outputs)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER (Streamlit)                  │
├─────────────────────────────────────────────────────────────┤
│  Dashboard 1: GPS Overview (market rankings, gaps)          │
│  Dashboard 2: PMS Deep Dive (oil/air/fuel/AdBlue)          │
│  Dashboard 3: Spend per Unit Trends (time series)          │
│  Export: Excel workbooks for Yoshimoto/Board               │
└─────────────────────────────────────────────────────────────┘
```

---

## MODULE 1: DATA PREP (Foundation)

### File: `data_prep.py`

**Purpose:** Clean and standardize inputs once, use everywhere

**Functions:**

```python
def load_sales_data(filepath: str) -> pd.DataFrame:
    """
    Load sales CSV, standardize columns, filter exclusions
    Returns: cleaned sales with distributor_code mapped
    """
    # 1. Read CSV
    # 2. Map sold_to → distributor_code (via lookup)
    # 3. Filter out MIDI, Germany service dept
    # 4. Add month, quarter columns
    # 5. Validate part_numbers (10-digit format)
    return df_sales_clean

def load_uio_data(filepath: str) -> pd.DataFrame:
    """
    Load UIO CSV, map distributor names to codes
    Returns: UIO by distributor_code
    """
    # 1. Read CSV
    # 2. Map distributor → distributor_code
    # 3. Filter out CV/LCV/CV-LCV junk codes
    # 4. Exclude ITALY (MIDI)
    return df_uio_clean

def load_part_classification(filepath: str) -> pd.DataFrame:
    """
    Load part classification lookup
    Returns: PN → category (PMS/Wear/Accessory) + subcategory (oil filter, etc.)
    """
    # Initial version: manually curated ~500 PNs
    # Expansion: add classification logic for new PNs
    return df_parts_class

def load_distributor_mapping(filepath: str) -> pd.DataFrame:
    """
    Load distributor master mapping
    Returns: sold_to → distributor_code, country, region, segment flags
    """
    return df_dist_map

def get_fiscal_year_dates(fiscal_year: int) -> tuple:
    """
    Convert fiscal year to date range
    
    ISZE Fiscal Year = April to March
    
    Example:
    - FY2024 → ('2024-04-01', '2025-03-31')
    - FY2025 → ('2025-04-01', '2026-03-31')
    
    Returns: (start_date, end_date) as strings
    """
    start_date = f"{fiscal_year}-04-01"
    end_date = f"{fiscal_year + 1}-03-31"
    return start_date, end_date

def filter_by_fiscal_year(df: pd.DataFrame, fiscal_year: int, date_column: str = 'billing_date') -> pd.DataFrame:
    """
    Filter DataFrame by ISZE fiscal year (Apr-Mar)
    
    Args:
    - df: DataFrame with date column
    - fiscal_year: e.g., 2024 for FY2024
    - date_column: name of date column to filter on
    
    Returns: filtered DataFrame
    """
    start_date, end_date = get_fiscal_year_dates(fiscal_year)
    df[date_column] = pd.to_datetime(df[date_column])
    mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
    return df[mask]
```

**Token Efficiency:**
- Loads data ONCE per session
- Caches cleaned DataFrames in memory
- No repeated file reads

---

## MODULE 2: GPS CALCULATOR (Core Analytics)

### File: `gps_calculator.py`

**Purpose:** Calculate GPS and spend/unit metrics

**Functions:**

```python
def calculate_spend_per_unit(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    part_category: str = 'ALL',  # or 'PMS', 'OIL_FILTER', etc.
    fiscal_year: int = 2024,  # FY2024 = Apr 2024 - Mar 2025
    use_fiscal_year: bool = True  # True = Apr-Mar, False = Jan-Dec
) -> pd.DataFrame:
    """
    Calculate spend per unit by distributor
    
    Formula: Spend/Unit = Total Net Sales / UIO
    
    Fiscal Year Logic:
    - FY2024 = billing_date between 2024-04-01 and 2025-03-31
    - Calendar Year = billing_date between 2024-01-01 and 2024-12-31
    
    Returns:
    - distributor_code
    - total_sales_eur
    - uio_units
    - spend_per_unit_eur
    - part_category
    - fiscal_year (or calendar_year)
    """
    # 1. Filter sales by fiscal/calendar year, category
    # 2. Aggregate: SUM(net_sales) by distributor
    # 3. Join with UIO (use UIO from fiscal year end, e.g., Mar 2025 for FY2024)
    # 4. Calculate spend/unit
    # 5. Rank distributors
    return df_spend_per_unit

def calculate_gps(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    part_number: str,
    service_interval_km: int,
    avg_annual_km: int = 60000,
    price_per_unit: float = None
) -> pd.DataFrame:
    """
    Calculate Genuine Parts Share for specific part
    
    Methodology:
    1. Calculate serviceable cohort (UIO × service_frequency)
    2. Calculate expected demand (cohort × 1 replacement/interval)
    3. Calculate actual sales (from df_sales)
    4. GPS = actual / expected
    
    Returns:
    - distributor_code
    - part_number
    - expected_units
    - actual_units
    - gps_pct
    - uncaptured_units
    - uncaptured_revenue_eur
    """
    # Use AdBlue filter methodology as template
    # Serviceable cohort = UIO × (annual_km / interval_km)
    return df_gps

def calculate_pms_basket_gps(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_parts: pd.DataFrame,
    year: int = 2024
) -> pd.DataFrame:
    """
    Calculate GPS for entire PMS basket (oil, air, fuel, AdBlue filters)
    
    Returns GPS by:
    - distributor_code
    - pms_category (oil_filter, air_filter, etc.)
    - gps_pct
    - traffic_light (red <30%, amber 30-60%, green >60%)
    """
    # Aggregate across multiple PNs in each category
    # Weight by expected demand
    return df_pms_gps
```

**Token Efficiency:**
- Functions are single-purpose, reusable
- No hard-coded values (parameters for flexibility)
- Returns clean DataFrames for chaining

---

## MODULE 3: PMS ANALYZER (PMS-Specific Deep Dive)

### File: `pms_analyzer.py`

**Purpose:** PMS-specific analysis (trends, coverage, pricing)

**Functions:**

```python
def get_pms_trends_by_month(
    df_sales: pd.DataFrame,
    df_parts: pd.DataFrame,
    distributor_code: str = None,  # None = all distributors
    pms_category: str = None  # 'oil_filter', 'air_filter', etc.
) -> pd.DataFrame:
    """
    Monthly PMS sales trends
    Returns: month × distributor × category → sales, units, avg_price
    """
    return df_pms_trends

def calculate_pms_coverage_rate(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_parts: pd.DataFrame,
    year: int = 2024
) -> pd.DataFrame:
    """
    PMS coverage rate = % of parc serviced with ISZE parts
    
    Similar to ITUK Coverage Dashboard logic
    Returns: distributor × pms_category → coverage_pct, gap_units
    """
    return df_coverage

def flag_pricing_outliers(
    df_sales: pd.DataFrame,
    threshold_pct: float = 0.50  # Flag if >50% above/below median
) -> pd.DataFrame:
    """
    Identify parts with pricing anomalies
    
    Compare avg selling price vs median across distributors
    Returns: part_number, distributor, avg_price, median_price, variance_pct, flag
    """
    return df_pricing_flags
```

---

## MODULE 4: EXPORT ENGINE (Output Generation)

### File: `export_engine.py`

**Purpose:** Generate Excel/CSV outputs for Yoshimoto/Board

**Functions:**

```python
def export_gps_dashboard_excel(
    df_gps: pd.DataFrame,
    df_spend_per_unit: pd.DataFrame,
    df_pms_trends: pd.DataFrame,
    output_path: str
) -> None:
    """
    Generate Excel workbook with multiple sheets:
    
    Sheet 1: Executive Summary
    - GPS by market (table + traffic light)
    - Spend/unit ranking
    - Top 5 uncaptured revenue opportunities
    
    Sheet 2: GPS Detail
    - Full GPS table by distributor × part
    
    Sheet 3: Spend per Unit
    - Trend chart (2022-2025)
    - Distributor comparison
    
    Sheet 4: PMS Analysis
    - Coverage rates by category
    - Monthly trends
    
    Sheet 5: Data Sources
    - Metadata (export date, row counts, filters applied)
    """
    # Use openpyxl for formatting
    # Add ISZE branding (if template available)
    # Traffic light conditional formatting
    pass

def export_gps_dashboard_csv(
    df_gps: pd.DataFrame,
    df_spend_per_unit: pd.DataFrame,
    df_pms_trends: pd.DataFrame,
    output_dir: str
) -> None:
    """
    Generate CSV files for Power BI ingestion
    
    Files:
    - gps_summary.csv (executive summary table)
    - gps_detail.csv (full GPS by distributor × part)
    - spend_per_unit.csv (time series data)
    - pms_trends.csv (monthly PMS data)
    - metadata.csv (export info, filters, data quality flags)
    
    All CSVs use UTF-8 encoding, comma delimiter, no quotes unless necessary
    """
    pass

def export_pms_deep_dive_excel(
    df_pms_gps: pd.DataFrame,
    df_pms_trends: pd.DataFrame,
    df_coverage: pd.DataFrame,
    output_path: str
) -> None:
    """
    PMS-focused workbook for operational review
    
    Sheet 1: PMS GPS Heatmap (distributor × category)
    Sheet 2: Monthly Trends (line charts)
    Sheet 3: Coverage Gaps (sorted by uncaptured revenue)
    Sheet 4: Pricing Outliers (flagged PNs)
    """
    pass
```

---

## STREAMLIT DASHBOARD STRUCTURE

### File: `app.py`

```python
import streamlit as st
from data_prep import *
from gps_calculator import *
from pms_analyzer import *
from export_engine import *

# Page config
st.set_page_config(page_title="ISZE GPS & PMS Dashboard", layout="wide")

# Sidebar: Data Upload & Filters
with st.sidebar:
    st.header("Data Upload")
    sales_file = st.file_uploader("Upload Sales Data", type=['csv'])
    uio_file = st.file_uploader("Upload UIO Data", type=['csv'])
    parts_file = st.file_uploader("Upload Part Classification", type=['csv'])
    
    st.header("Filters")
    year_mode = st.radio("Year Type", ['Fiscal Year (Apr-Mar)', 'Calendar Year (Jan-Dec)'])
    selected_year = st.selectbox("Year", [2022, 2024, 2025])
    selected_distributors = st.multiselect("Distributors", options=all_distributors)
    selected_category = st.selectbox("Category", ['ALL', 'PMS', 'WEAR', 'ACCESSORIES'])

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["GPS Overview", "PMS Deep Dive", "Spend per Unit", "Export"])

with tab1:
    st.header("Genuine Parts Share Overview")
    # Display GPS by distributor (table + chart)
    # Traffic light indicators
    # Top 5 uncaptured revenue opportunities

with tab2:
    st.header("PMS Analysis")
    # PMS category breakdown (oil, air, fuel, AdBlue)
    # Coverage rates
    # Monthly trends
    # Pricing outliers

with tab3:
    st.header("Spend per Unit Trends")
    # Time series chart (2022-2025)
    # Distributor comparison
    # Segment split (LCV vs CV if available)

with tab4:
    st.header("Export Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Excel Export")
        # Button: Generate Excel (GPS Dashboard)
        # Button: Generate Excel (PMS Deep Dive)
        # Download links with ISZE branding, charts, formatting
    
    with col2:
        st.subheader("CSV Export (Power BI)")
        # Button: Generate CSV bundle (5 files zipped)
        # Download link for zip file
        # Preview: show file list and row counts
```

---

## INITIAL PART CLASSIFICATION APPROACH

**Phase 1: Manual Curation (500 PNs)**

Focus on high-volume PMS parts:
- Oil filters (20 PNs)
- Air filters (15 PNs)
- Fuel filters (12 PNs)
- AdBlue filters (8 PNs)
- Brake pads (25 PNs)
- Wiper blades (10 PNs)

**Phase 2: Semi-Automated Expansion**

Use `description` field keywords:
- "FILTER" + "OIL" → oil_filter
- "FILTER" + "AIR" → air_filter
- "FILTER" + "FUEL" → fuel_filter
- "PAD; BRAKE" → brake_pad
- "BLADE; WIPER" → wiper_blade

**Phase 3: Full Classification (Future)**

- ML model trained on curated set
- Predict category for all 10k+ unique PNs
- Human validation on edge cases

---

## TOKEN EFFICIENCY STRATEGY

### 1. Data Aggregation
- Don't process 348k rows every time
- Pre-aggregate to monthly summaries (reduces to ~1,500 rows)
- Cache in session state

### 2. Modular Loading
- Only load functions needed for current view
- Don't import all modules upfront

### 3. Incremental Expansion
- Start with GPS Overview (Module 1 + 2)
- Add PMS Deep Dive (Module 3) in Phase 2
- Add Export Engine (Module 4) in Phase 3

### 4. Smart Caching
```python
@st.cache_data
def load_and_prep_sales(filepath):
    # Cached after first load
    return cleaned_df
```

---

## IMPLEMENTATION ROADMAP FOR COWORK

### Sprint 1: Foundation (Week 1)
- [ ] Build Module 1 (data_prep.py)
- [ ] Create distributor mapping lookup
- [ ] Create initial part classification (100 PMS PNs)
- [ ] Test: Load sales, UIO, map distributors

### Sprint 2: GPS Core (Week 2)
- [ ] Build Module 2 (gps_calculator.py)
- [ ] Implement spend_per_unit function
- [ ] Implement single-part GPS function (test with AdBlue filters)
- [ ] Test: Calculate GPS for ITUK, Israel

### Sprint 3: Dashboard UI (Week 3)
- [ ] Build Streamlit app skeleton
- [ ] Implement GPS Overview tab
- [ ] Add basic charts (Plotly)
- [ ] Test: Upload files, view GPS table

### Sprint 4: PMS Layer (Week 4)
- [ ] Build Module 3 (pms_analyzer.py)
- [ ] Implement PMS trends
- [ ] Implement coverage rate calculation
- [ ] Add PMS Deep Dive tab

### Sprint 5: Export & Polish (Week 5)
- [ ] Build Module 4 (export_engine.py)
- [ ] Generate Excel outputs
- [ ] Add ISZE branding/formatting
- [ ] Test: Generate report for Yoshimoto review

---

## FILE STRUCTURE

```
/isze_gps_dashboard/
├── app.py                          # Streamlit main app
├── modules/
│   ├── data_prep.py               # Module 1
│   ├── gps_calculator.py          # Module 2
│   ├── pms_analyzer.py            # Module 3
│   └── export_engine.py           # Module 4
├── data/
│   ├── sales_detailed.csv         # Your upload (348k rows)
│   ├── uio_distributor.csv        # UIO data
│   ├── part_classification.csv    # PN → category lookup
│   └── distributor_mapping.csv    # Sold_to → code mapping
├── outputs/
│   ├── gps_dashboard_YYYYMMDD.xlsx
│   └── pms_deep_dive_YYYYMMDD.xlsx
├── requirements.txt
└── README.md
```

---

## QUESTIONS FOR YOU BEFORE COWORK STARTS:

1. **Do you want Cowork to start with Sprint 1 (foundation) or should I first build the part classification table for you?**

2. **For the initial PMS part list**: Should I extract the top 100 filter PNs from your sales file (by volume), or do you have a preferred list?

3. **UIO limitation**: You only have 2024 UIO data. For 2022/2025 GPS calculations, should we:
   - Use 2024 UIO as proxy (assumes stable parc)?
   - Flag 2022/2025 as "estimated" until you get multi-year UIO?

4. **Export format preference**: 
   - Excel workbooks (formatted, charts, traffic lights)?
   - Or CSV exports for Power BI ingestion?

5. **Access control**: Is this dashboard for:
   - Just you (local Streamlit)?
   - ISZE team (deployed on internal server)?
   - Yoshimoto/Board (generate Excel, email)?

This framework is designed to minimize token usage while staying expandable. Cowork can build incrementally without needing full context every time.

**Ready to proceed?**
