import sys
from pathlib import Path
import numpy as np, pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); DER = ISZE / "01_data/00_derived"
sys.path.insert(0, str(ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29"))
from evidence_lib import load_base
L = load_base(); L = L[L.movable].copy()
print("base lines", len(L), "billed", round(L.net_sales_value.sum(), 2), "| customer_code sample", L.customer_code.astype(str).head(3).tolist(), "pn sample", L.pn.head(3).tolist())
s = pd.read_parquet(DER / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "net_sales_value", "billed_qty"])
s["d"] = pd.to_datetime(s.billing_date)
w = s[(s.d >= "2025-07-01") & (s.d <= "2026-06-30")].copy()
print("sales_fact window rows", len(w), "billed", round(w.net_sales_value.sum(), 2), "| sample sold_to", w.sold_to_sap.astype(str).head(3).tolist(), "pn", w.part_number.astype(str).head(3).tolist())
norm = lambda x: str(x).strip().replace(".0", "").lstrip("0")
L["k"] = L.customer_code.map(norm) + "|" + L.pn.map(norm)
w["k"] = w.sold_to_sap.map(norm) + "|" + w.part_number.map(norm)
m = w[w.k.isin(set(L.k))]
print("matched rows", len(m), "billed", round(m.net_sales_value.sum(), 2), "vs base", round(L.net_sales_value.sum(), 2), "diff", round(m.net_sales_value.sum() - L.net_sales_value.sum(), 2))
mm = m.groupby(m.d.dt.to_period("M")).net_sales_value.sum()
print((mm / mm.sum()).round(4).to_string())
