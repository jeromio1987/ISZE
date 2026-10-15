"""v6 payload: payload5 plus
  - the monthly billing profile per distributor (sales_fact.parquet, Jul 2025 - Jun 2026, ties to the revision base to the cent),
  - the dealer reaction cases of the revision workbook (Summary rows 32-34),
  - the newest part numbers of every Power BI export on file (pbi_iszj_newest_export*.csv, newer file wins)."""
import json, sys, glob
from pathlib import Path
import numpy as np, pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); DER = ISZE / "01_data/00_derived"; H = Path(__file__).parent
sys.path.insert(0, str(ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29"))
from evidence_lib import load_base
D = json.loads((H / "payload5.json").read_text(encoding="utf-8"))
L = load_base(); L = L[L.movable].copy()
dd = pd.read_csv(DER / "distributor_dimension.csv", dtype=str)
db_of = dict(zip(dd.sold_to_sap, dd.distributor_code))
norm = lambda x: str(x).strip().replace(".0", "").lstrip("0")
L["k"] = L.customer_code.map(norm) + "|" + L.pn.map(norm)
L["db"] = L.customer_code.astype(str).map(db_of)
kdb = dict(zip(L.k, L.db))
s = pd.read_parquet(DER / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "net_sales_value"])
s["d"] = pd.to_datetime(s.billing_date)
w = s[(s.d >= "2025-07-01") & (s.d <= "2026-06-30")].copy()
w["k"] = w.sold_to_sap.map(norm) + "|" + w.part_number.map(norm)
m = w[w.k.isin(kdb)].copy(); m["db"] = m.k.map(kdb)
assert abs(m.net_sales_value.sum() - 32595852.63) < 0.01, m.net_sales_value.sum()
months = pd.period_range("2025-07", "2026-06", freq="M")
mat = m.groupby([m.db, m.d.dt.to_period("M")]).net_sales_value.sum().unstack(fill_value=0).reindex(columns=months, fill_value=0)
dix = {d: i for i, d in enumerate(D["dbs"])}
share = {}
for db, row in mat.iterrows():
    tot = row.sum()
    if tot > 0: share[str(dix[db])] = [round(float(v / tot), 8) for v in row.values]
book = mat.sum(); book = [round(float(v / book.sum()), 8) for v in book.values]
D["months"] = {"labels": [str(p) for p in months], "cal": [p.month for p in months], "share": share, "book": book}
D["react"] = [
    {"key": "none", "label": "No reaction", "e": 0.0, "src": "Dealers keep buying the same quantity. What the April 2026 increase showed on the UK truck network: volume up 3.7% March to August."},
    {"key": "central", "label": "Central", "e": -0.1584, "src": "Four markets pooled, April 2026 list change (UK trucks, UK D-Max, Ireland, Portugal). About -0.16: a 10% price rise costs about 1.6% of volume."},
    {"key": "stress", "label": "Stress", "e": -0.81, "src": "Lowest 95% bound across the pooled measurements: a pessimistic case, not a forecast."}]
D["react_src"] = "Revision workbook Oct 2026, Summary rows 32 to 34 (dealer response measured on sales-to-dealer data)"
# newest part numbers from every Power BI export on file, oldest first so a newer file wins
files = sorted(glob.glob(str(ISZE / "01_data/90_INBOX/pbi_iszj_newest_export*.csv")))
pbi = {}
for f in files:
    t = pd.read_csv(f, dtype=str)
    for a, b in zip(t.Material, t.NEWEST): pbi[str(a).strip()] = str(b).strip()
hit = 0
for p in D["parts"]:
    if p[0] in pbi: p[12] = pbi[p[0]]; hit += 1
D["pbi_n"] = len(pbi); D["pbi_files"] = [Path(f).name for f in files]
(H / "payload6.json").write_text(json.dumps(D, separators=(",", ":")), encoding="utf-8")
print("months ok, markets with a profile", len(share), "| book profile", book, "| PBI newest on file", len(pbi), "of which in the base", hit, "| files", D["pbi_files"])
