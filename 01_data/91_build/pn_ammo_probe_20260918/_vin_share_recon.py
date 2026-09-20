"""Recompute the jp_vin_shipments N35 share per market from the VIN register, and test whether
the same denominator reproduces the share now in uio_ld_n35_share.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
v = pd.read_csv(ROOT / "01_data" / "07_UIO" / "vin" / "VIN_register.csv", low_memory=False)
v["code"] = v["db_code"].astype(str).str.upper().str.strip()
v["dest"] = v["db_destination"].astype(str).str.upper().str.strip()
v["ser"] = v["series"].astype(str).str.upper().str.strip()
v["gvw"] = pd.to_numeric(v["gvw_t"], errors="coerce")
NS = ["NPR", "NNR", "NLR", "NKR", "NMR", "NQR", "N1R"]
v["is_n"] = v["ser"].isin(NS)
v["is_n35"] = v["gvw"].between(3.0, 3.9)
v["is_f"] = v["ser"].isin(["FRR", "FSR", "FVR", "FTR"])

print("register db_code counts:", v["code"].value_counts().to_dict())
print()
hdr = f"{'code':6s} {'all':>5s} {'Nser':>5s} {'N35':>5s} {'F':>4s} {'N35/Nser':>9s} {'N35/all':>8s}"
print(hdr)
for c, g in v.groupby("code"):
    a, n, n35, f = len(g), int(g.is_n.sum()), int(g.is_n35.sum()), int(g.is_f.sum())
    print(f"{c:6s} {a:5d} {n:5d} {n35:5d} {f:4d} "
          f"{n35 / n if n else 0:9.4f} {n35 / a if a else 0:8.4f}")

print()
print("Current CSV shares for comparison:")
cur = pd.read_csv(ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "uio_ld_n35_share.csv")
for _, r in cur.iterrows():
    print(f"  {r['distributor_code']:10s} {r['n35_share']:<7} {r['basis']}")
