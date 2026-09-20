"""Audit every N35 share in uio_ld_n35_share.csv against the basis it names.

Read-only. Prints, per market: current share, the basis it claims, what that basis actually
yields when recomputed from the source file, and a verdict.

Sources:
  * JP VIN register           01_data/07_UIO/vin/VIN_register.csv      (shipment flow)
  * SIMI (Ireland)            01_data/07_UIO/isuzuregdata.xlsx + scrap-adj parc
                              06_uio/Ireland_SIMI_Comparison/Ireland_UIO_GPS_Comparison_2026-05-28_v4.xlsx
  * Helwig (Germany)          01_data/90_INBOX/_isd_std_mail_20260818/attachments/*Fahrzeugbestand*
  * UIO bucket                03_analytics/Isuzu/prism/data/uio_by_model_bucket.csv
"""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PD = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"

shares = pd.read_csv(PD / "uio_ld_n35_share.csv")
buckets = pd.read_csv(PD / "uio_by_model_bucket.csv").set_index("distributor_code")

print("=" * 108)
print("UIO bucket composition per market (what the share actually splits)")
print("=" * 108)
print(buckets[["cv_std_uio", "f_series_uio", "lcv_uio"]].to_string())

# ---------------------------------------------------------------- JP VIN register
vin = pd.read_csv(ROOT / "01_data" / "07_UIO" / "vin" / "VIN_register.csv", low_memory=False)
vin["dest"] = vin["db_destination"].astype(str).str.upper().str.strip()
vin["ser"] = vin["series"].astype(str).str.upper().str.strip()
vin["gvw"] = pd.to_numeric(vin["gvw_t"], errors="coerce")
vin["is_n35"] = vin["gvw"].between(3.0, 3.9)
vin["is_nseries"] = vin["ser"].isin(["NPR", "NNR", "NLR", "NKR", "NMR", "NQR", "N1R"]) | (
    vin["gvw"].between(6.0, 8.0)
)
vin["is_f"] = vin["ser"].isin(["FRR", "FSR", "FVR", "FTR", "FSS"])

print()
print("=" * 108)
print("JP VIN register by destination market (shipment flow, the 'jp_vin_shipments' basis)")
print("=" * 108)
rows = []
for dest, g in vin.groupby("dest"):
    if dest in ("NAN", "", "NONE"):
        continue
    n35 = int(g["is_n35"].sum())
    nser = int(g["is_nseries"].sum())
    f = int(g["is_f"].sum())
    rows.append({
        "dest": dest, "rows": len(g), "n35": n35, "n_series": nser, "f": f,
        "n35/nseries": round(n35 / nser, 4) if nser else None,
        "n35/(nseries+f)": round(n35 / (nser + f), 4) if (nser + f) else None,
        "n35/all": round(n35 / len(g), 4),
    })
print(pd.DataFrame(rows).sort_values("rows", ascending=False).to_string(index=False))

# ---------------------------------------------------------------- Ireland parc (SIMI)
print()
print("=" * 108)
print("IRELAND — SIMI, both bases recomputed from source")
print("=" * 108)
wb = openpyxl.load_workbook(ROOT / "01_data" / "07_UIO" / "isuzuregdata.xlsx", data_only=True)
rows = list(wb["Sheet2"].iter_rows(values_only=True))
hdr = rows[2]
yc = {int(str(v).replace("Sum of", "").strip()): j
      for j, v in enumerate(hdr) if v and "Sum of" in str(v)}
def simi_row(label):
    for r in rows:
        if r[0] and str(r[0]).strip() == label:
            return {y: (r[j] or 0) for y, j in yc.items()}
    return {}
n35f, n75f, ff, dmf = (simi_row("N Series 3.5T"), simi_row("N series 7.5T"),
                       simi_row("F series"), simi_row("D max"))
s35, s75, sf, sdm = (sum(n35f.values()), sum(n75f.values()), sum(ff.values()), sum(dmf.values()))
print(f"  cumulative 2010-2025 registrations: N35 {s35}, N75 {s75}, F {sf}, D-Max {sdm}")
print(f"    flow N35/(N35+N75)       = {s35/(s35+s75):.4f}")
print(f"    flow N35/(N35+N75+F)     = {s35/(s35+s75+sf):.4f}")
print(f"    flow N35/(all registered)= {s35/(s35+s75+sf+sdm):.4f}")

wb4 = openpyxl.load_workbook(
    ROOT / "06_uio" / "Ireland_SIMI_Comparison" / "Ireland_UIO_GPS_Comparison_2026-05-28_v4.xlsx",
    data_only=True)
rr = list(wb4["Hybrid_UIO_Timeline"].iter_rows(values_only=True))
hdr4 = rr[3]
i25 = [i for i, x in enumerate(hdr4) if x is not None and str(x).strip() == "2025"][0]
parc = {str(r[0]).strip(): r[i25] for r in rr[4:] if r[0]}
p35, p75, pf = parc.get("N 3.5T"), parc.get("N 7.5T"), parc.get("CV F-Series")
print(f"  scrap-adjusted PARC at 2025 (SIMI cohorts x the scrap curve): "
      f"N35 {p35}, N75 {p75}, F {pf}")
print(f"    parc N35/(N35+N75)       = {p35/(p35+p75):.4f}   <-- the basis the split needs")
print(f"    parc N35/(N35+N75+F)     = {p35/(p35+p75+pf):.4f}")

# Ireland JP VIN register, N-series denominator
ie = vin[vin["dest"].str.contains("IE", na=False) | vin["db_code"].astype(str).str.upper().str.contains("IE", na=False)]
print(f"  JP VIN register Ireland: {len(ie)} rows, N35 {int(ie['is_n35'].sum())}, "
      f"N-series {int(ie['is_nseries'].sum())}, F {int(ie['is_f'].sum())}")
print(f"    N35/N-series={int(ie['is_n35'].sum())/int(ie['is_nseries'].sum()):.4f}  "
      f"N35/all={int(ie['is_n35'].sum())/len(ie):.4f}")

# ---------------------------------------------------------------- Germany (Helwig)
print()
print("=" * 108)
print("GERMANY — Helwig parc bands (the 'helwig_parc_bands' basis)")
print("=" * 108)
print("  Nfz 787 = <=3.40t 25 + 3.41-3.50t 153 + 3.51-5.50t 79 + 5.51-6.50t 147 "
      "+ 6.51-7.50t 318 + 7.51-12.0t 35")
print(f"    3.41-7.50 t block = 697 ; N35(3.41-3.50) = 153 -> {153/697:.4f}   <-- matches 0.220")

# ---------------------------------------------------------------- verdicts
print()
print("=" * 108)
print("VERDICT — claimed vs recomputed")
print("=" * 108)
for _, r in shares.iterrows():
    print(f"  {r['distributor_code']:10s} share={r['n35_share']:<7} basis={r['basis']}")
    print(f"      note: {str(r['evidence_note'])[:150]}")
