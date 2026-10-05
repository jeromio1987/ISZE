"""Does F-series have fewer PMS part numbers than N-series, or is that an artefact?

Jerome: "these are PMS parts there can't be less parts for an F series than for N series right?"

Three different counts, which are easily confused:
  A. catalogue breadth  - how many distinct service PNs exist per family
  B. billed breadth     - how many appear in the top 250 by EUR (a fleet-size effect)
  C. euro per vehicle   - whether F is under-billed against its fleet
"""

import json
from collections import Counter

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

print("=" * 100)
print("A. CATALOGUE BREADTH — distinct service part numbers per family (cross-reference)")
print("=" * 100)
xref = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", dtype=str, low_memory=False)
vm = xref["vehicle_model"].astype(str).str.upper()
pms = xref[xref.pms_category.notna()].copy()
pms["vm"] = vm


def is_f(s):
    return any(k in s for k in ("FRR", "FSR", "FTR", "FVR", "FVM", "FSS", "FTS", "FVZ", "F*"))


def is_n(s):
    return any(k in s for k in ("NPR", "NQR", "NMR", "NLR", "NKR", "NPS", "N*R", "NNR"))


f_only = pms[pms.vm.map(lambda s: is_f(s) and not is_n(s))]
n_only = pms[pms.vm.map(lambda s: is_n(s) and not is_f(s))]
shared = pms[pms.vm.map(lambda s: is_f(s) and is_n(s))]
print(f"  F-series only PNs : {f_only.genuine_pn.nunique()}")
print(f"  N-series only PNs : {n_only.genuine_pn.nunique()}")
print(f"  shared / both     : {shared.genuine_pn.nunique()}")
print()
print("  by category, F-only vs N-only:")
fc = f_only.groupby("pms_category").genuine_pn.nunique()
nc = n_only.groupby("pms_category").genuine_pn.nunique()
comp = pd.DataFrame({"F_only": fc, "N_only": nc}).fillna(0).astype(int)
print(comp.to_string())

print()
print("=" * 100)
print("B. BILLED BREADTH — the top 250 by euro, from the decode")
print("=" * 100)
dec = json.load(open(DER + r"\epc_decode_batch1_20260919.json", encoding="utf-8"))
print(f"  records in the decode: {len(dec)}")

f_pns, n_pns, lv_pns = set(), set(), set()
for r in dec:
    fams = " ".join(r.get("families") or []).upper()
    models = " ".join(r.get("models") or []).upper()
    tag = fams + " " + models
    pn = r["pn"]
    if "TRUCKS F&G" in fams or "TRUCKS C&E" in fams:
        f_pns.add(pn)
    if "TRUCKS N" in fams:
        n_pns.add(pn)
    if "PASSENGER" in fams and "TRUCKS" not in fams:
        lv_pns.add(pn)
print(f"  touch F&G / C&E (heavy)  : {len(f_pns)}")
print(f"  touch TRUCKS N           : {len(n_pns)}")
print(f"  light-vehicle only       : {len(lv_pns)}")

print()
print("=" * 100)
print("C. EURO PER VEHICLE — is F under-billed against its fleet, or does it have fewer parts?")
print("=" * 100)
sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
dim = pd.read_csv(DER + r"\distributor_dimension.csv")
sf["db"] = sf.sold_to_sap.map(dict(zip(dim.sold_to_sap, dim.distributor_code)))

f_e = sf[sf._pn.isin(f_pns)].net_sales_value.sum()
n_e = sf[sf._pn.isin(n_pns)].net_sales_value.sum()
lv_e = sf[sf._pn.isin(lv_pns)].net_sales_value.sum()

uio = pd.read_csv(ROOT + r"\03_analytics\Isuzu\prism\data\uio_by_model_bucket.csv")
cv = uio.cv_std_uio.sum()
fs = uio.f_series_uio.sum()
lcv = uio.lcv_uio.sum()

print(f"  {'group':28s} {'billed EUR':>14s} {'vehicles':>10s} {'EUR/vehicle':>12s}")
rows = [
    ("heavy (F&G, C&E) PNs in decode", f_e, fs),
    ("N-series PNs in decode", n_e, cv),
    ("light-vehicle PNs in decode", lv_e, lcv),
]
for label, eur, veh in rows:
    per = eur / veh if veh else float("nan")
    print(f"  {label:28s} {eur:14,.0f} {veh:10,.0f} {per:12,.0f}")
print()
print(f"  note: these are only the PNs that appear in the top-250 decode, so they understate")
print(f"  each group's total. The comparison that matters is the RATIO between groups.")
