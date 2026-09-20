"""Test each hypothesis for the EUR 1.43M exactly, instead of reasoning about it.

Three candidate defects. Each is tested on its own and must reproduce the published ceiling
to the euro, or it is not the explanation.
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"

R = pd.read_csv(PD + r"\gps_model_targets.csv").set_index("model_group")["target_eur_per_vehicle"]
N35, N75, F, LCV = (float(R["N35_Grafter"]), float(R["N75_N50_N62"]),
                    float(R["F_Series_MD"]), float(R["LCV_D_Max"]))
b = pd.read_csv(PD + r"\uio_by_model_bucket.csv").set_index("distributor_code")
sh = pd.read_csv(PD + r"\uio_ld_n35_share.csv")
share = dict(zip(sh.distributor_code, sh.n35_share))
w = pd.read_csv(DER + r"\wallet_waterfall.csv")
w25 = w[w.year == 2025].set_index("distributor_code")

print("=" * 104)
print("PER MARKET: which exact formula reproduces the published ceiling?")
print("=" * 104)
print(f"rates: N35 {N35} | N75 {N75} | F-series {F} | LCV {LCV}")
print()
hdr = (f"{'market':10s} {'published':>12s} {'A split':>12s} {'B flat739':>12s} "
       f"{'C F added':>12s}  verdict")
print(hdr)
print("-" * 104)

findings = []
for db in b.index:
    if db not in w25.index:
        continue
    pub = float(w25.loc[db, "theoretical_wallet_eur"])
    cv = float(b.loc[db, "cv_std_uio"]); fs = float(b.loc[db, "f_series_uio"])
    lcv = float(b.loc[db, "lcv_uio"])
    s = share.get(db, 0.0)

    a = cv * s * N35 + cv * (1 - s) * N75 + fs * F + lcv * LCV          # correct split
    bb = (cv + fs) * N75 + lcv * LCV                                     # every truck at 739
    c = (cv + fs) * N75 + fs * F + lcv * LCV                             # F added on top = double count

    def near(x):
        return abs(x - pub) < 1.0
    if near(a):
        verdict = "A - already correct"
    elif near(bb):
        verdict = "B - UNSPLIT: whole truck fleet at 739"
    elif near(c):
        verdict = "C - F-SERIES DOUBLE-COUNTED"
    else:
        verdict = f"? residual EUR {pub - a:,.0f}"
    print(f"{db:10s} {pub:12,.0f} {a:12,.0f} {bb:12,.0f} {c:12,.0f}  {verdict}")
    findings.append({"db": db, "published": pub, "split": a, "flat739": bb,
                     "f_added": c, "verdict": verdict})

f = pd.DataFrame(findings)
print()
print("=" * 104)
print("THE THREE DEFECTS, EACH CONFIRMED TO THE EURO")
print("=" * 104)
unsplit = f[f.verdict.str.startswith("B")]
dbl = f[f.verdict.str.startswith("C")]
other = f[~f.verdict.str.startswith(("A", "B", "C"))]

for name, grp in (("B  truck fleet never split (still at the 7.5t rate)", unsplit),
                  ("C  F-series added on top of a truck row that already contains them", dbl),
                  ("?  unexplained", other)):
    if grp.empty:
        continue
    print(f"\n{name}:")
    for _, r in grp.iterrows():
        print(f"   {r['db']:10s} published {r['published']:12,.0f}   correct {r['split']:12,.0f}"
              f"   overstated by {r['published'] - r['split']:10,.0f}")

print()
print(f"  published network 2025 : EUR {f.published.sum():,.0f}")
print(f"  corrected network 2025 : EUR {f.split.sum():,.0f}")
print(f"  total overstatement    : EUR {f.published.sum() - f.split.sum():,.0f} "
      f"({100*(f.published.sum()/f.split.sum()-1):.2f}%)")

print()
print("=" * 104)
print("WHAT IT DOES TO COVER")
print("=" * 104)
cap = w25["captured_total_eur"]
f = f.merge(cap.rename("captured"), left_on="db", right_index=True)
f["now"] = (100 * f.captured / f.published).round(1)
f["after"] = (100 * f.captured / f.split).round(1)
f["move"] = (f.after - f.now).round(1)
print(f[["db", "now", "after", "move"]].sort_values("move", ascending=False).to_string(index=False))
print()
print(f"  network cover now   : {100*f.captured.sum()/f.published.sum():.1f}%")
print(f"  network cover after : {100*f.captured.sum()/f.split.sum():.1f}%")
