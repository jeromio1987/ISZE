"""Prove the Ireland + Belgium corrections landed, and show the realised expected-demand move."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PD = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"

sh = pd.read_csv(PD / "uio_ld_n35_share.csv")
b = pd.read_csv(PD / "uio_by_model_bucket.csv").set_index("distributor_code")
print("=== corrected share file (Ireland / Belgium / Portugal) ===")
print(sh[sh.distributor_code.isin(["IRELAND", "BELGIUM", "PORTUGAL", "MALTA", "CYPRUS"])]
      [["distributor_code", "n35_share", "basis", "units_2025e"]].to_string(index=False))

print()
print("=== realised expected-demand move, 2025, all line_type=total ===")
live = pd.read_csv(DER / "pms_capture_by_db_year.csv")
bak = pd.read_csv(DER / "pms_capture_by_db_year.csv.bak_pre_n35_ratio_20260918")
k = ["distributor_code", "pms_category", "year", "line_type"]
m = live[live.line_type == "total"].merge(bak[bak.line_type == "total"], on=k, suffixes=("_L", "_B"))
rows = []
for db, g in m.groupby("distributor_code"):
    eb, ea = g.expected_qty_B.sum(), g.expected_qty_L.sum()
    cb = (g.actual_qty_B.sum() / eb * 100) if eb else 0
    ca = (g.actual_qty_B.sum() / ea * 100) if ea else 0
    rows.append({"market": db, "exp_before": round(eb), "exp_after": round(ea),
                 "move_pct": round(100 * (ea / eb - 1), 2) if eb else 0,
                 "cover_before_pct": round(cb, 1), "cover_after_pct": round(ca, 1),
                 "move_pp": round(ca - cb, 1)})
d = pd.DataFrame(rows).sort_values("move_pct", ascending=False)
print(d.to_string(index=False))

print()
print("=== IRELAND, category by category (2025) ===")
ie = m[(m.distributor_code == "IRELAND") & (m.year == 2025)].copy()
ie["cap_before_pct"] = (100 * ie.actual_qty_B / ie.expected_qty_B).round(1)
ie["cap_after_pct"] = (100 * ie.actual_qty_B / ie.expected_qty_L).round(1)
ie["exp_pct"] = (100 * (ie.expected_qty_L / ie.expected_qty_B - 1)).round(2)
print(ie[["pms_category", "expected_qty_B", "expected_qty_L", "exp_pct",
          "cap_before_pct", "cap_after_pct"]].to_string(index=False))

print()
print("=== BELGIUM, category by category (2025) — the market that exposed the whole-figure bug ===")
bz = m[(m.distributor_code == "BELGIUM") & (m.year == 2025)].copy()
bz["cap_before_pct"] = (100 * bz.actual_qty_B / bz.expected_qty_B).round(1)
bz["cap_after_pct"] = (100 * bz.actual_qty_B / bz.expected_qty_L).round(1)
bz["exp_pct"] = (100 * (bz.expected_qty_L / bz.expected_qty_B - 1)).round(2)
print(bz[["pms_category", "expected_qty_B", "expected_qty_L", "exp_pct",
          "cap_before_pct", "cap_after_pct"]].to_string(index=False))
print()
print("Belgium LCV check — the LCV block must NOT have moved:")
print("  uio bucket:", b.loc["BELGIUM", ["cv_std_uio", "lcv_uio"]].to_dict())
print("  LCV expected demand is lcv_uio x rate x factor and is outside this change by construction.")

print()
print("=== tonnage model: Ireland bands ===")
tm = pd.read_csv(DER / "pms_tonnage_model.csv")
ies = tm[tm.distributor_code == "IRELAND"]
cols = [c for c in ["distributor_code", "band", "pms_category", "services_per_year",
                    "expected_units", "actual_units"] if c in ies.columns]
print(ies[cols].head(20).to_string(index=False))
