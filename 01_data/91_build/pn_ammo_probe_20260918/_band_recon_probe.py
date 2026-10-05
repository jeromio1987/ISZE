"""Probe: does a tonnage-band reconstruction of the fleet reproduce the published ceiling?

If the band split (N35 / N75-class / F-series / LCV) times the per-vehicle target rate reproduces
wallet_waterfall's theoretical wallet per market, the band layer is safe to build on.
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"

shares = pd.read_csv(PD + r"\uio_ld_n35_share.csv")
buckets = pd.read_csv(PD + r"\uio_by_model_bucket.csv")
rates = pd.read_csv(PD + r"\gps_model_targets.csv").set_index("model_group")[
    "target_eur_per_vehicle"
]
wallet = pd.read_csv(DER + r"\wallet_waterfall.csv")

R_N35 = float(rates["N35_Grafter"])
R_N75 = float(rates["N75_N50_N62"])
R_F = float(rates["F_Series_MD"])
R_LCV = float(rates["LCV_D_Max"])

share = dict(zip(shares.distributor_code, shares.n35_share))
basis = dict(zip(shares.distributor_code, shares.basis))
b = buckets.set_index("distributor_code")

rows = []
for _, w in wallet[wallet.year == 2025].iterrows():
    db = w.distributor_code
    total = float(w.uio_units)
    if db not in b.index:
        rows.append({"db": db, "published": w.theoretical_wallet_eur, "band": None,
                     "basis": "no bucket split"})
        continue
    cv = float(b.loc[db, "cv_std_uio"])
    fs = float(b.loc[db, "f_series_uio"])
    lcv = float(b.loc[db, "lcv_uio"])
    s = share.get(db)
    if s is None:
        # No measured 3.5t presence: the whole CV row stays one band (all N75-class).
        s = 0.0
        bs = "unmeasured - whole CV at 7.5t"
    else:
        bs = basis.get(db, "")
    n35 = cv * s
    n75 = cv * (1 - s)
    band = n35 * R_N35 + n75 * R_N75 + fs * R_F + lcv * R_LCV
    rows.append({"db": db, "published": float(w.theoretical_wallet_eur), "band": band,
                 "basis": bs, "n35": round(n35), "n75": round(n75), "f": round(fs),
                 "lcv": round(lcv), "bucket_total": cv + fs + lcv, "uio": total})

out = pd.DataFrame(rows)
out = out[out.band.notna()].copy()
out["delta"] = (out.band - out.published).round(0)
out["delta_pct"] = (100 * (out.band / out.published - 1)).round(2)
print("2025, published ceiling vs a tonnage-band reconstruction:")
print(out[["db", "published", "band", "delta", "delta_pct", "uio", "bucket_total",
           "n35", "n75", "f", "lcv"]].to_string(index=False))
print()
print("network published:", round(out.published.sum()))
print("network band     :", round(out.band.sum()))
print("difference       :", round(out.band.sum() - out.published.sum()),
      f"({100*(out.band.sum()/out.published.sum()-1):.2f}%)")
print()
print("biggest disagreements:")
print(out.reindex(out.delta_pct.abs().sort_values(ascending=False).index)
      [["db", "published", "band", "delta_pct", "basis"]].head(10).to_string(index=False))
