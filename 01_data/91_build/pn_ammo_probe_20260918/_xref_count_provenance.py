"""Where do the brief's 95 / 45 / 13 cross-reference counts come from?

Also: what is the true F-series-only value once the cross-reference's wildcard tokens are allowed
to name more than one family, and once the D-Max token TF* is not read as an F-series token.
"""
from __future__ import annotations

import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

FTOK = ("FRR", "FSR", "FTR", "FVR", "FVM", "FSS", "FTS", "FVZ", "GVR", "FV*", "FS*", "F*")
NTOK = ("NPR", "NQR", "NMR", "NLR", "NKR", "NPS", "N*R", "NNR")
LTOK = ("TF*", "TFR", "TFS", "UC*", "UCR", "UCS", "UB*", "UBS")

raw = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", dtype=str, low_memory=False)


def tag(df: pd.DataFrame, label: str) -> None:
    d = df.copy()
    d["vm"] = d.vehicle_model.fillna("").str.upper()
    d["f"] = d.vm.map(lambda s: any(k in s for k in FTOK))
    d["n"] = d.vm.map(lambda s: any(k in s for k in NTOK))
    d["l"] = d.vm.map(lambda s: any(k in s for k in LTOK))
    fo, no, bo = d[d.f & ~d.n], d[d.n & ~d.f], d[d.f & d.n]
    print(f"--- {label}  ({len(d)} rows)")
    print(f"    rows   : F-only {len(fo):5d}   N-only {len(no):5d}   both {len(bo):5d}")
    print(f"    genuine: F-only {fo.genuine_pn.map(norm).nunique():5d}   "
          f"N-only {no.genuine_pn.map(norm).nunique():5d}   "
          f"both {bo.genuine_pn.map(norm).nunique():5d}")
    print(f"    pairs  : F-only {fo.drop_duplicates(['genuine_pn', 'bvp_pn']).shape[0]:5d}   "
          f"N-only {no.drop_duplicates(['genuine_pn', 'bvp_pn']).shape[0]:5d}   "
          f"both {bo.drop_duplicates(['genuine_pn', 'bvp_pn']).shape[0]:5d}")
    hs = d[d.f & ~d.n & ~d.l]
    print(f"    F-only, never co-occurring with a light token: "
          f"{hs.genuine_pn.map(norm).nunique():5d} genuine PNs")


tag(raw, "all 544 rows, blanks kept as a value")
tag(raw[raw.pms_category.notna()], "319 rows with a service category")

print()
sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["pn"] = sf.part_number.map(norm)
d = raw.copy()
d["vm"] = d.vehicle_model.fillna("").str.upper()
d["f"] = d.vm.map(lambda s: any(k in s for k in FTOK))
d["n"] = d.vm.map(lambda s: any(k in s for k in NTOK))
d["l"] = d.vm.map(lambda s: any(k in s for k in LTOK))
for label, sel in (("F-only rows", d.f & ~d.n),
                   ("F-only, no light token", d.f & ~d.n & ~d.l)):
    pns = {v for v in d.loc[sel, "genuine_pn"].map(norm) if v != "nan"}
    e = sf[sf.pn.isin(pns)].net_sales_value.sum()
    print(f"  {label:26s} {len(pns):4d} PNs  EUR {e:12,.0f} (all billed years, all markets)")
