# ISZE sales data — GPT-safe dictionary

**Scope:** Definitions only. Raw billing (~435k rows) stays local; do not upload `raw/sales/*`.

## Sales_Fact (canonical, when built)

| Field | Meaning |
|-------|---------|
| billing_date | SAP billing date |
| sold_to | Distributor / customer code |
| material | Part number |
| billed_qty | Quantity billed |
| net_sales_eur | Net value EUR |
| saty | Order type (SaTy) |
| saty_factor | Price/urgency factor from Order_Type_Master |
| dq_flag | Data quality flag from Phase 1 checks |

## Phases

1. **Phase 1** — Clean CY extracts → Sales_Fact  
2. **Phase 2** — Customer order behaviour, part criticality  
3. **Phase 3** — Demand, stocking, PRD candidates  

## Paths (local — not uploaded)

`01_data/raw/sales/`, `01_data/models/Phase*.xlsx`

## Upload to GPT

Only files in `gpt_safe/` and aggregated `dashboards/isze_data.json` (KPI level).
