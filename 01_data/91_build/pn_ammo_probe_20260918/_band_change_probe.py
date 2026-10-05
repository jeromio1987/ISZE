"""Exactly which rows I would change, and where the third band actually exists."""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"

R = pd.read_csv(PD + r"\gps_model_targets.csv").set_index("model_group")["target_eur_per_vehicle"]
R_N35, R_N75, R_F, R_LCV = (float(R["N35_Grafter"]), float(R["N75_N50_N62"]),
                            float(R["F_Series_MD"]), float(R["LCV_D_Max"]))
shares = pd.read_csv(PD + r"\uio_ld_n35_share.csv")
share = dict(zip(shares.distributor_code, shares.n35_share))
buckets = pd.read_csv(PD + r"\uio_by_model_bucket.csv").set_index("distributor_code")
w = pd.read_csv(DER + r"\wallet_waterfall.csv")

print("=" * 108)
print("THE THIRD BAND — F-series / MD (heavy). Where it exists at all.")
print("=" * 108)
b = buckets.copy()
b["total_cv"] = b.cv_std_uio + b.f_series_uio
b["f_share_of_cv"] = (
    b.f_series_uio / b.total_cv.where(b.total_cv > 0) * 100
).astype("float64").round(1)
show = b[["cv_std_uio", "f_series_uio", "lcv_uio", "f_share_of_cv"]].sort_values(
    "f_series_uio", ascending=False)
show.index.name = "market"
print(show.to_string())
nz = int((b.f_series_uio > 0).sum())
print(f"\n  markets with any heavy band : {nz} of {len(b)}")
print(f"  total heavy-band vehicles   : {b.f_series_uio.sum():,.0f}")
print(f"  heavy as share of all trucks: "
      f"{100*b.f_series_uio.sum()/(b.cv_std_uio.sum()+b.f_series_uio.sum()):.1f}%")
print("  Per-vehicle target, heavy   : EUR", R_F, "vs EUR", R_N75, "at 7.5 t")

print()
print("=" * 108)
print("WHAT I WOULD CHANGE — 2025 rows only, market by market")
print("=" * 108)
rows = []
for _, r in w[w.year == 2025].iterrows():
    db = r.distributor_code
    if db not in buckets.index:
        continue
    cv = float(buckets.loc[db, "cv_std_uio"])
    fs = float(buckets.loc[db, "f_series_uio"])
    lcv = float(buckets.loc[db, "lcv_uio"])
    units = cv + fs + lcv
    if units <= 0:
        continue
    published = float(r.theoretical_wallet_eur)
    implied = published / units
    s = share.get(db, 0.0)
    band = cv * s * R_N35 + cv * (1 - s) * R_N75 + fs * R_F + lcv * R_LCV
    rows.append({
        "market": db, "uio": units, "published": published,
        "implied_rate": round(implied, 2), "band_rate": round(band / units, 2),
        "corrected": round(band),
        "delta_eur": round(band - published),
        "n35_share": s,
        "on_unsplit_739": abs(implied - R_N75) < 1.0,
    })
d = pd.DataFrame(rows).sort_values("delta_eur")
d["delta_pct"] = (100 * (d.corrected / d.published - 1)).round(2)
pd.set_option("display.width", 200)
print(d[["market", "uio", "published", "implied_rate", "band_rate", "corrected",
         "delta_eur", "delta_pct", "n35_share", "on_unsplit_739"]].to_string(index=False))

unsplit = d[d.on_unsplit_739 & (d.n35_share > 0)]
print()
print("Markets still priced as if every truck were 7.5 t, despite a measured 3.5 t fleet:")
print(unsplit[["market", "n35_share", "delta_eur", "delta_pct"]].to_string(index=False))
print(f"\n  total correction on these rows : EUR {unsplit.delta_eur.sum():,.0f}")
print(f"  network ceiling 2025           : EUR {d.published.sum():,.0f} -> "
      f"EUR {d.corrected.sum():,.0f}")

# What it does to cover, which is the number Jerome reads.
cap = w[w.year == 2025].set_index("distributor_code")["captured_total_eur"]
d = d.merge(cap.rename("captured"), left_on="market", right_index=True)
d["cover_now"] = (100 * d.captured / d.published).round(1)
d["cover_after"] = (100 * d.captured / d.corrected).round(1)
d["cover_move_pp"] = (d.cover_after - d.cover_now).round(1)
print()
print("Cover of the target spend, before and after:")
print(d[["market", "cover_now", "cover_after", "cover_move_pp"]].sort_values(
    "cover_move_pp", ascending=False).to_string(index=False))
print()
print(f"  network cover now   : {100*d.captured.sum()/d.published.sum():.1f}%")
print(f"  network cover after : {100*d.captured.sum()/d.corrected.sum():.1f}%")
