"""Find where vehicle / model / tonnage evidence actually lives, per part number."""

import glob
import os

import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
KEYS = ("model", "vehicle", "tonn", "weight", "gvw", "series", "chassis", "engine")

rows = []
for p in sorted(glob.glob(os.path.join(DER, "*.csv"))):
    name = os.path.basename(p)
    if os.path.getsize(p) < 2000:
        continue
    try:
        cols = pd.read_csv(p, nrows=3, low_memory=False).columns
    except Exception:
        continue
    hits = [c for c in cols if any(k in c.lower() for k in KEYS)]
    if hits:
        rows.append((name, round(os.path.getsize(p) / 1024), hits))

print(f"{'file':44s} {'KB':>7s}  vehicle-ish columns")
print("-" * 110)
for n, kb, h in rows:
    print(f"{n:44s} {kb:7d}  {h}")

print()
print("=" * 110)
print("THE THIN ONE, IN FULL — the only file that maps a part number to a vehicle")
print("=" * 110)
x = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", low_memory=False)
x["vm"] = x.vehicle_model.astype(str).str.strip()
x["en"] = x.engine_type.astype(str).str.strip()
filled = x[(x.vm.ne("") & x.vm.ne("nan") & x.vm.ne("-"))].copy()
print(f"rows {len(x)}, with a vehicle model {len(filled)}, distinct models "
      f"{filled.vm.nunique()}")
print()
# Normalise the free-text model field into a band.
def band(vm, en):
    t = f"{vm} {en}".upper()
    heavy = any(k in t for k in ("FRR", "FSR", "FTR", "FVR", "FVM", "FSS", "FTS", "FVZ",
                                 "FXZ", "GVR", "FRS", "FV*", "FS*", "FR*", "FT*", "F*",
                                 "6HK1", "6HH1", "6HE1", "6SD1", "6WG1", "6WF1", "6UZ1",
                                 "EXZ", "CX*", "CVR", "CHR"))
    dm = any(k in t for k in ("TFR", "TFS", "UCR", "UCS", "UBS", "UES", "UC*", "TF*",
                              "RZ4E", "4JJ3", "C22", "6VE1"))
    nseries = any(k in t for k in ("NPR", "NQR", "NMR", "NLR", "NKR", "NPS", "N*R", "N*S",
                                   "PHR", "QKR", "4HK1", "4HG1", "4HF1", "4HE1"))
    if heavy and not (dm or nseries):
        return "F_series_heavy"
    if dm and not (heavy or nseries):
        return "LCV_D_max"
    if nseries and not (heavy or dm):
        return "N_series_truck"
    if heavy and (dm or nseries):
        return "SPANS_bands_real"
    return "unknown"

filled["band"] = [band(v, e) for v, e in zip(filled.vm, filled.en)]
print("bands, on the part numbers that carry a vehicle at all:")
print(filled.band.value_counts().to_string())
print()
print("the SPANS rows (genuinely used on more than one band) — these cannot be banded:")
sp = filled[filled.band == "SPANS_bands_real"][["genuine_pn", "pms_category", "vm", "en"]]
print(sp.drop_duplicates("genuine_pn").head(20).to_string(index=False))
print(f"  distinct part numbers spanning bands: {sp.genuine_pn.nunique()}")
print()
print("sample of cleanly-banded part numbers:")
for bnd in ("F_series_heavy", "N_series_truck", "LCV_D_max"):
    g = filled[filled.band == bnd]
    print(f"  {bnd:18s} {g.genuine_pn.nunique():3d} PNs, e.g. "
          f"{list(g.genuine_pn.astype(str).unique()[:4])}")
