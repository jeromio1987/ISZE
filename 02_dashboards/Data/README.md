# ISZE Data layer

**Manifest:** [DATA_MANIFEST.md](DATA_MANIFEST.md)  
**Pipeline memory:** `../memory/projects/sales-analytics-pipeline.md`

Quick start for PRISM:

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism
pip install -r requirements.txt
python scripts/build_sales_fact_from_cy.py
streamlit run app.py
```

New SAP exports → `_INBOX/` → file into `raw/sales/` → rebuild parquet.
