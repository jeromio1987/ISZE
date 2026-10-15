import json, re
from pathlib import Path
import pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); H = Path(__file__).parent; DER = ISZE / "01_data/00_derived"
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 60)
D = json.loads((H / "payload4.json").read_text(encoding="utf-8"))
pn = {p[0] for p in D["parts"]}
fb = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str); print("family file rows", len(fb), "distinct pn", fb.pn.nunique())
fb = fb[fb.pn.isin(pn)]; print("in base", fb.pn.nunique(), "| dup pn rows", int(fb.pn.duplicated().sum()))
print(fb.groupby(["family", "resolution"], dropna=False).size().to_string())
va = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str); va = va[va.pn.isin(fb.pn)]
print("\nband file rows for these pn:", len(va), "distinct", va.pn.nunique())
print(va.groupby("band_status", dropna=False).size().to_string())
print(va.vehicle_bands.value_counts(dropna=False).head(14).to_string())
cap = pd.read_csv(DER / "pms_capture_by_db_year.csv"); print("\ncapture columns", list(cap.columns), "years", sorted(cap.year.unique()), "line_types", cap.line_type.unique())
c = cap[(cap.year == 2025) & (cap.line_type == "total")]; print("categories in capture 2025 total:", sorted(c.pms_category.unique())); print("categories in family file (base):", sorted(fb.pms_category.unique()))
t = (ISZE / "02_dashboards/pricing/ISZE_Parts_Price_Intelligence.html").read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r"(location\.hash|URLSearchParams)", t):
    s = max(0, m.start() - 160); print("\n...", re.sub(r"\s+", " ", t[s:m.start() + 260])); break
print("\nPPI hash handling snippets:")
for m in list(re.finditer(r"location\.hash", t))[:3]:
    print("  >", re.sub(r"\s+", " ", t[max(0, m.start() - 100):m.start() + 220]))
for m in list(re.finditer(r"params\.get\(['\"](\w+)['\"]\)|\.get\(['\"](\w+)['\"]\)", t))[:8]:
    print("  param:", m.group(0))
