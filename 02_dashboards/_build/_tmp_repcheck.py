import os

import pandas as pd

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
f = "dealer_sellout_long_IUK_CY2025.csv"
d = pd.read_csv(os.path.join(D, f), usecols=["period", "period_grain", "part_number", "qty"])
print("all rows", len(d))
print("grain counts", d.period_grain.value_counts().to_dict())
m = d[d.period_grain == "month"].copy()
print("month rows", len(m), "unique periods", sorted(m.period.astype(str).unique())[:15])
m["month"] = m.period
sel = m[m.month.astype(str).str.startswith("2025")]
print("startswith 2025 rows", len(sel), "qty", float(sel.qty.sum()))
print("str accessor type:", type(m.month.astype(str).str))
print("first value repr:", repr(m.month.iloc[0]), "type", type(m.month.iloc[0]))
