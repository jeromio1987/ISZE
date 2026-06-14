# Derived data

Exports from Phase 1–3 (Power Query / Python). **Claude and Prism should read from here**, not from `raw/sales/*.XLSX`.

Expected files (create after Phase 1 build):

| File | Source |
|------|--------|
| `sales_fact.parquet` | Phase 1 Sales_Fact |
| `sales_fact_monthly.csv` | Monthly DB × category aggregate |
| `phase2_part_criticality.csv` | Phase 2 export |
| `phase2_customer_saty.csv` | Phase 2 export |
| `phase3_stocking_actions.csv` | Phase 3 export |
| `_verification_report.md` | Auto QA after `python scripts/verify_derived_pipeline.py` |
