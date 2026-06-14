# SALES DATA EXPORT SPECIFICATION FOR GPS ANALYSIS
## Required for: Genuine Parts Share (GPS) & Spend per Unit Dashboard

---

## EXPORT REQUIREMENTS

### Time Period:
- **2022-01-01 to 2026-12-31** (full years + current YTD)
- Include billing_date as actual date, not just year

### Required Columns:

```
Column Name          | Description                                    | Format/Example
---------------------|------------------------------------------------|---------------------------
sold_to_code         | Customer SAP code                              | 0012563000
sold_to_name         | Customer/distributor name                      | ISUZU TRUCK (UK) LIMITED
distributor_code     | Standardized code (map via lookup)             | ITUK
country              | Country of distributor                         | United Kingdom
billing_date         | Actual invoice date                            | 2024-03-15
part_number          | DB part number (ISZE/IML format)               | 8983507161
description          | Part description                               | AdBlue Filter Element
billed_qty           | Quantity sold                                  | 12
net_sales_eur        | Net sales value in EUR (after all discounts)   | 846.36
list_price_eur       | Standard list price (PR00 or your base level)  | 70.53
discount_pct         | Discount percentage granted                    | 0.15
year                 | Billing year (for quick filtering)             | 2024
month                | Billing month                                  | 3
segment              | Vehicle segment (if available in SAP)          | CV or LCV or blank
```

### Critical Notes:

1. **Sold_to mapping**: Your export MUST include either:
   - `distributor_code` directly, OR
   - `sold_to_code` + separate mapping table (sold_to → distributor)

2. **Net sales EUR**: After ALL discounts (SPAs, volume rebates, promotional, etc.)
   - This is what goes into spend/unit calculation
   - Must be actual realized revenue to ISZE

3. **Segment field**: Optional but VERY useful for:
   - Israel split (UTI LCV vs UTI_CV)
   - Analysis by vehicle type
   - If not in SAP, we'll classify by part number

4. **Exclusions**: Your export should EXCLUDE:
   - Germany service dept sales (Isuzu Motors Germany GmbH)
   - MIDI sales (if they appear in your SAP - you said no data, but verify)
   - Any internal transfers or non-distributor customers

---

## WHY THESE FIELDS MATTER:

### For GPS Calculation:
```
GPS = (ISZE Parts Sales to Distributor) / (Total Addressable Market)

Where:
- Numerator = SUM(net_sales_eur) for PMS parts by distributor
- Denominator = UIO × Service Frequency × Average Basket × Price Index
```

### For Spend per Unit:
```
Spend/Unit = (ISZE Parts Sales) / (Serviceable Cohort UIO)

Where:
- Serviceable Cohort = vehicles that have reached service interval threshold
- NOT total UIO (this was the 3.3% vs 11.7% error in AdBlue study)
```

We need `part_number` + `description` to classify which parts are:
- PMS (oil filter, air filter, fuel filter, AdBlue filter)
- Wear items (brake pads, wiper blades, belts)
- Accessories (floor mats, mud flaps, etc.)

We need `billing_date` to:
- Calculate monthly/quarterly trends
- Build vintage cohorts (which year's vehicles are being serviced)
- Align with UIO snapshots

We need `net_sales_eur` AND `list_price_eur` to:
- Calculate realized price index
- Measure discount discipline
- Compare ISZE pricing vs IAM/OEM competitors

---

## CURRENT vs REQUIRED:

### What you uploaded:
```
sold_to,year,billed_qty
0012563000,2024,1.0
0015583000,2024,1.0
```

### What we need:
```
sold_to_code,sold_to_name,distributor_code,country,billing_date,part_number,description,billed_qty,net_sales_eur,list_price_eur,discount_pct,year,month
0012563000,ISUZU TRUCK (UK) LIMITED,ITUK,United Kingdom,2024-03-15,8983507161,AdBlue Filter Element,12,846.36,70.53,0.00,2024,3
0012563000,ISUZU TRUCK (UK) LIMITED,ITUK,United Kingdom,2024-03-22,1876102341,AdBlue Filter Housing,8,245.76,30.72,0.00,2024,3
```

---

## RECOMMENDED EXPORT METHOD:

### Option A: SAP Standard Report (if available)
- Use VA05 (List of Sales Orders) or VF05 (List of Billing Documents)
- Filter: Material type = FERT (finished goods), Date range 2022-2026
- Layout: Include all fields above

### Option B: Custom SQL Query (if you have HANA/BW access)
```sql
SELECT 
    vbak.kunnr AS sold_to_code,
    kna1.name1 AS sold_to_name,
    vbrk.fkdat AS billing_date,
    vbrp.matnr AS part_number,
    makt.maktx AS description,
    vbrp.fkimg AS billed_qty,
    vbrp.netwr AS net_sales_eur,
    -- add list price lookup
FROM vbrk  -- Billing header
JOIN vbrp ON vbrk.vbeln = vbrp.vbeln  -- Billing items
JOIN vbak ON vbrp.aubel = vbak.vbeln  -- Sales order
JOIN kna1 ON vbak.kunnr = kna1.kunnr  -- Customer master
JOIN makt ON vbrp.matnr = makt.matnr  -- Material description
WHERE vbrk.fkdat BETWEEN '2022-01-01' AND '2026-12-31'
  AND vbrp.fkimg > 0  -- Exclude credit memos initially
```

### Option C: Excel Pivot Export
- If your system doesn't allow direct export, work with BVDB
- He has Power BI access to sales data
- Can he pull this view for you?

---

## DATA VALIDATION CHECKLIST:

Before you send me the export, verify:

☐ Row count makes sense (your current file has 33k rows for 2024-2025, full export should be ~150k-200k rows for 2022-2026)
☐ Part numbers are actual DB PNs (8-10 digit codes), not internal SAP material numbers
☐ Net sales EUR totals reconcile to your management reports (within 1-2% tolerance)
☐ No MIDI sales included (Italy distributor)
☐ No Germany service dept sales
☐ Sold_to codes map to known distributors (check against mapping table)
☐ At least these fields present: sold_to, billing_date, part_number, qty, net_sales_eur

---

## ONCE YOU HAVE THE DATA:

I will build:

1. **GPS Dashboard** (Excel workbook):
   - Sheet 1: Sales raw data (import your export)
   - Sheet 2: UIO data (import your UIO file)
   - Sheet 3: Part classification (PMS vs wear vs accessories)
   - Sheet 4: Serviceable cohort model (vintage fleet calculation)
   - Sheet 5: GPS by market (table + charts)
   - Sheet 6: Spend per unit by market
   - Sheet 7: Executive summary (traffic light, gaps, actions)

2. **PMS Dashboard** (separate workbook):
   - Focus on oil/air/fuel/AdBlue filters only
   - Monthly trend by market
   - Coverage rate vs DVLA/registration data (where available)
   - Price competitiveness vs IAM

Then Cowork can productionize into Streamlit/web app if you want.

---

## QUESTIONS BEFORE YOU EXPORT:

1. Do you have access to pull this yourself, or do you need BVDB/Hadi to extract it?
2. Do you want me to draft the email request to BVDB if he needs to pull it?
3. Should we start with ONE distributor (e.g., ITUK) to validate the model, then scale to all markets?
4. Do you have the PMS parts classification table, or do we build it from scratch?

Let me know and I'll adjust the spec.
