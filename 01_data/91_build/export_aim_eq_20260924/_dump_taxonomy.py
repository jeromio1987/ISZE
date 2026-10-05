"""Dump the AIM family/level-2 vocabulary actually in use on the master."""
import pandas as pd

m = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv",
                dtype=str, low_memory=False)


def real(s):
    v = s.fillna("")
    return (v != "") & (~v.str.lower().str.startswith("unknown"))


k = m[real(m["aim_l1"])]
print("rows with a real AIM family:", len(k))
for l1, g in k.groupby("aim_l1"):
    l2s = sorted({x for x in g["aim_l2"].dropna() if x.strip()})
    print(f"{l1:24s} {len(g):6d}  " + " | ".join(l2s))
