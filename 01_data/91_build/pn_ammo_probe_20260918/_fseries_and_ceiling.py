"""Do F-series trucks use different PMS part numbers, or the same ones as N-series?

And: which ceiling, and what is the EUR 1.43M actually made of?
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"

x = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", low_memory=False)
x["vm"] = x.vehicle_model.astype(str).str.strip().str.upper()
x["pn"] = x.genuine_pn.astype(str).str.strip()

def band(vm: str) -> str:
    if vm in ("", "NAN", "NONE"):
        return "unknown"
    if any(k in vm for k in ("F*", "FS", "FR", "FT", "FV", "FVZ", "GIGA", "MD")):
        return "F_series_heavy"
    if "N*R" in vm or "NPR" in vm or "NQR" in vm or "NMR" in vm or "NLR" in vm or "NKR" in vm:
        return "N_series_truck"
    if "TF" in vm or "UC" in vm or "TFR" in vm:
        return "D_max_LCV"
    return "other"

x["band"] = x.vm.map(band)

print("=" * 100)
print("1. PMS PART NUMBERS BY TONNAGE BAND — are they the same parts or different parts?")
print("=" * 100)
pms = x[x.pms_category.notna()].copy()
tab = pms.pivot_table(index="pms_category", columns="band", values="pn",
                      aggfunc=lambda s: len(set(s)), fill_value=0)
print("distinct genuine part numbers per service category per band:")
print(tab.to_string())
print()

# The real test: overlap. Same PN on both a truck band and the heavy band = shared part.
print("Do heavy and truck bands SHARE part numbers, or use different ones?")
for cat in sorted(pms.pms_category.unique()):
    g = pms[pms.pms_category == cat]
    n = set(g[g.band == "N_series_truck"].pn)
    f = set(g[g.band == "F_series_heavy"].pn)
    if not n and not f:
        continue
    shared = n & f
    verdict = ("SHARED - same part numbers" if shared
               else "SEPARATE - heavy has its own" if (n and f) else "only one band present")
    print(f"  {cat:24s} N-series {len(n):3d}  heavy {len(f):3d}  shared {len(shared):3d}   {verdict}")
    if shared:
        print(f"      shared: {sorted(shared)[:6]}")

print()
print("Heavy-band part numbers that are NOT used on N-series (heavy-only parts), by category:")
heavy_only = pms[(pms.band == "F_series_heavy")].pn.unique()
n_all = set(pms[pms.band == "N_series_truck"].pn)
ho = [p for p in heavy_only if p not in n_all]
print(f"  total heavy PN rows {len(heavy_only)}, heavy-only {len(ho)}")
if ho:
    print(pms[pms.pn.isin(ho)][["pn", "pms_category", "vm", "engine_type"]]
          .drop_duplicates("pn").to_string(index=False))

print()
print("=" * 100)
print("2. THE CEILING — which one, and what the gap is made of")
print("=" * 100)
w = pd.read_csv(DER + r"\wallet_waterfall.csv")
w25 = w[w.year == 2025].copy()
b = pd.read_csv(PD + r"\uio_by_model_bucket.csv").set_index("distributor_code")
R = pd.read_csv(PD + r"\gps_model_targets.csv").set_index("model_group")["target_eur_per_vehicle"]
R_N35, R_N75, R_F, R_LCV = (float(R["N35_Grafter"]), float(R["N75_N50_N62"]),
                            float(R["F_Series_MD"]), float(R["LCV_D_Max"]))

sh = pd.read_csv(PD + r"\uio_ld_n35_share.csv")
share = dict(zip(sh.distributor_code, sh.n35_share))

print("The file says, per row, what the ceiling is meant to be:")
print("  ", str(w25.assumption_note.iloc[0])[:150])
print()
print("So the ceiling should equal UIO x the rate card. Where it does not, the fleet composition")
print("the ceiling build used differs from uio_by_model_bucket.csv. Solving for the heavy share")
print("the published ceiling implies:")
print()
rows = []
for _, r in w25.iterrows():
    db = r.distributor_code
    if db not in b.index:
        continue
    cv = float(b.loc[db, "cv_std_uio"]); fs = float(b.loc[db, "f_series_uio"])
    lcv = float(b.loc[db, "lcv_uio"]); uio = cv + fs + lcv
    if uio <= 0:
        continue
    implied = float(r.theoretical_wallet_eur) / uio
    s = share.get(db, 0.0)
    # If heavy share were h of the CV block, the blended rate would be:
    # s*(1-h)*N35 + (1-s)*(1-h)*N75 + h*F   ... solve for h
    # base (h=0): s*N35 + (1-s)*N75 on all CV; each heavy vehicle swaps N75 -> F
    base_cv_rate = s * R_N35 + (1 - s) * R_N75
    if cv > 0:
        h = ((implied * uio) - (cv * base_cv_rate) - (lcv * R_LCV)) / (cv * (R_F - base_cv_rate)) \
            if (R_F - base_cv_rate) != 0 else float("nan")
    else:
        h = float("nan")
    rows.append({"market": db, "uio": round(uio), "implied_rate": round(implied, 2),
                 "implied_heavy_share_of_trucks": round(h, 3) if h == h else None})
d = pd.DataFrame(rows).sort_values("implied_heavy_share_of_trucks", ascending=False)
print(d.to_string(index=False))
