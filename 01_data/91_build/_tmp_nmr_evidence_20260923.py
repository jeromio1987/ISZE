"""Collect every on-disk record that speaks to NMR's weight, so the evidence note can cite rows.

Two questions:
  A. what states 5.5 t, and what does each of those records actually rest on?
  B. what states 7.5 t, and is there any weight evidence behind it at all?
"""
import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"


def n(s):
    return str(s).strip().lstrip("0") or "0"


print("=" * 96)
print("A1. THE JP VIN REGISTER's OWN series -> GVW TABLE (model_dimension.csv)")
print("=" * 96)
md = pd.read_csv(ROOT / "01_data" / "07_UIO" / "vin" / "model_dimension.csv", dtype=str).fillna("")
nmr = md[md.series == "NMR"]
print(f"  NMR rows: {len(nmr)}   VINs: {int(pd.to_numeric(nmr.vin_count).sum())}")
print(nmr[["iszj_model_name", "series", "gvw_code", "gvw_t", "vin_count"]].to_string(index=False))
others = md[~md.series.isin(["NMR"])].groupby("series").agg(
    rows=("series", "size"), vin=("vin_count", lambda s: int(pd.to_numeric(s).sum())),
    gvw=("gvw_t", "first"))
print()
print(others.to_string())

print()
print("=" * 96)
print("A2. WHERE THAT gvw_t COLUMN COMES FROM (build_vin_register.py)")
print("=" * 96)
bv = (ROOT / "01_data" / "07_UIO" / "vin" / "build_vin_register.py").read_text(encoding="utf-8")
for i, line in enumerate(bv.splitlines(), 1):
    if "gvw_t_source" in line or "_load_series_gvw" in line or "SERIES_GVW_T = " in line:
        print(f"  {i}: {line.strip()[:150]}")

reg = pd.read_csv(ROOT / "01_data" / "07_UIO" / "vin" / "VIN_register.csv", dtype=str).fillna("")
print(f"  VIN_register rows: {len(reg):,}")
print(f"  gvw_t_source value counts: {reg.gvw_t_source.value_counts().to_dict()}")
print(f"  NMR rows in the register: {int((reg.series == 'NMR').sum())}")

print()
print("=" * 96)
print("B1. THE ONLY INTERNAL PLACE THAT PUTS NMR ON 7.5 t")
print("=" * 96)
mc = pd.read_csv(PRISM / "data" / "model_code_to_tonnage.csv", encoding="utf-8-sig", dtype=str).fillna("")
sel = mc[mc.model_code.isin(["NMR", "NMR85"])]
for r in sel.itertuples():
    print(f"  {r.model_code:8s} band={r.tonnage_band:20s} label={r.weight_class_label}")
    print(f"           confidence={r.confidence}")
    print(f"           quote={r.evidence_quote[:210]}")

print()
print("=" * 96)
print("B2. DOES ANY SOURCE STATE 7,500 kg FOR ANY NMR? search every file that names NMR")
print("=" * 96)
hits = []
for p in list(DER.glob("*.csv")) + list(DER.glob("*.json")) + list(PRISM.glob("data/*.csv")):
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    if "NMR" not in txt:
        continue
    for ln in txt.splitlines():
        if "NMR" in ln and ("7.5" in ln or "7500" in ln or "7,5" in ln):
            hits.append((p.name, ln.strip()[:220]))
for name, ln in hits:
    print(f"  {name}: {ln}")
print(f"  total lines pairing NMR with 7.5 / 7500: {len(hits)}")

print()
print("=" * 96)
print("C. WHAT THE SHIPPED BANDER ACTUALLY DOES WITH NMR TODAY")
print("=" * 96)
banded = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str, low_memory=False).fillna("")
nmr_rows = banded[banded.series_all.str.contains("NMR", na=False)]
print(f"  banded rows naming NMR: {len(nmr_rows)}")
print(f"  by band_status: {nmr_rows.band_status.value_counts().to_dict()}")
print(f"  by tonnage_band: {nmr_rows.tonnage_band.value_counts().to_dict()}")
print(f"  the lone NMR-only-code rows on 5.5t: "
      f"{int((nmr_rows.tonnage_band == '5.5t_N50_N55').sum())}")
s = pd.read_csv(DER / "series_to_tonnage.csv", encoding="utf-8-sig", dtype=str).fillna("")
row = s[s.series == "NMR"].iloc[0]
print()
print(f"  series_to_tonnage.csv NMR row: band={row.tonnage_band} label={row.weight_label}")
print(f"    source={row.evidence_source[:120]}")
print(f"    confidence={row.confidence}")
