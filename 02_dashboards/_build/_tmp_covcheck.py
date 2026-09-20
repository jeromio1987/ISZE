"""Throwaway: measure the dealer-sales coverage each way, so the choice between
'year rollup only' and 'year rollup + months' is made on evidence, not on the
verifier's inference."""
import os
import re
import sys

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ROOT, "01_data", "00_derived")
if os.path.join(ROOT, "03_analytics", "Isuzu", "prism") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "03_analytics", "Isuzu", "prism"))

FILES = {
    "IUK": ["dealer_sellout_long_IUK_CY2025.csv"],
    "ITUK": ["dealer_sellout_long_ITUK_CY2025.csv"],
    "IRELAND": ["dealer_sellout_long_IRELAND_CY2025.csv"],
    "GREECE": ["dealer_sellout_long_GREECE_CY2025.csv"],
    "UTI": ["dealer_sellout_long_UTI_CY2025.csv"],
}

for db, files in FILES.items():
    d = pd.read_csv(os.path.join(D, files[0]), usecols=["period_grain", "qty"])
    gr = d.groupby("period_grain").qty.sum()
    month, year = float(gr.get("month", 0)), float(gr.get("year", 0))
    print(f"{db:9s} month={month:12,.0f}  year={year:12,.0f}  year/month={year / month:.4f}")
