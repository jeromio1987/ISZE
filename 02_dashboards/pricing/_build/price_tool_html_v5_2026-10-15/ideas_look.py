import json
from pathlib import Path
import pandas as pd, pyarrow.parquet as pq
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); DER = ISZE / "01_data/00_derived"; H = Path(__file__).parent
D = json.loads((H / "payload5.json").read_text(encoding="utf-8"))
bill = {}
for l in D["lines"]: bill[l[0]] = bill.get(l[0], 0) + l[3]
pn = {p[0]: i for i, p in enumerate(D["parts"])}; tot = sum(bill.values())
ks = pd.read_csv(DER / "iam_ks_price_gap.csv", dtype={"pn": str}); ks["pn"] = ks.pn.str.strip()
inb = ks[ks.pn.isin(pn)]
print("KS price gap file rows", len(ks), "distinct pn", ks.pn.nunique(), "| in the base:", inb.pn.nunique(), "parts, billed EUR %.0f = %.1f%% of book" % (sum(bill[pn[p]] for p in inb.pn.unique()), 100 * sum(bill[pn[p]] for p in inb.pn.unique()) / tot))
print("columns", list(ks.columns)[:14])
f = DER / "sales_fact.parquet"
if f.exists():
    s = pq.ParquetFile(f); print("\nsales_fact columns:", s.schema.names[:40], "rows", s.metadata.num_rows)
for name in ["price_bp_weighted_compare_pn.csv"]:
    print(name, list(pd.read_csv(DER / name, nrows=2).columns)[:30])
