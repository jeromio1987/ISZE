"""Adversarial diagnostics on the IDS correlation scan. Read-only."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
j = pd.read_csv(D / "ids_corr_dealer_ituk_2026-08-10.csv")
t = pd.read_csv(D / "ids_corr_db_level_2026-08-10.csv")

print("=" * 70)
print("A. UK dealer group vs site disagreement — is the group result a size artefact?")
print("=" * 70)
print(j[["grp", "ids_total_pct", "ids_sites", "sell_sites", "total_eur"]]
      .sort_values("total_eur", ascending=False).to_string(index=False))

for a, b in [("ids_total_pct", "sell_sites"), ("ids_total_pct", "ids_sites")]:
    r, p = stats.spearmanr(j[a], j[b])
    print(f"\nrho({a}, {b}) = {r:.3f}  p={p:.4f}  n={len(j)}")


def partial(y, x, z):
    d = pd.DataFrame({"y": y, "x": x, "z": z}).dropna()
    ry = d["y"] - np.polyval(np.polyfit(d["z"], d["y"], 1), d["z"])
    rx = d["x"] - np.polyval(np.polyfit(d["z"], d["x"], 1), d["z"])
    r, p = stats.pearsonr(ry, rx)
    return r, p, len(d)


j["log_eur"] = np.log10(j["total_eur"].clip(lower=1))
r, p, n = partial(j["ids_total_pct"], j["log_eur"], j["sell_sites"])
print(f"\nPARTIAL IDS vs log(EUR) controlling for #sites: r={r:.3f} p={p:.4f} n={n}")

single = j[j["sell_sites"] == 1]
r2, p2 = stats.spearmanr(single["ids_total_pct"], single["log_eur"])
print(f"SINGLE-SITE groups only: rho={r2:.3f} p={p2:.4f} n={len(single)}")

# jackknife the group-level EUR correlation
base, _ = stats.spearmanr(j["ids_total_pct"], j["log_eur"])
jk = []
for i in range(len(j)):
    s = j.drop(j.index[i])
    rr, _ = stats.spearmanr(s["ids_total_pct"], s["log_eur"])
    jk.append((j.iloc[i]["grp"], rr))
jk.sort(key=lambda x: x[1])
print(f"\nJackknife IDS vs log(EUR): base rho={base:.3f}")
print("  most influential (drop -> rho):", [(g, round(v, 3)) for g, v in jk[:3]],
      "...", [(g, round(v, 3)) for g, v in jk[-3:]])

print("\n" + "=" * 70)
print("B. Leakage finding robustness")
print("=" * 70)
lk = pd.read_csv(D / "dealer_leakage_ituk.csv")
print("leakage rows per dealer:", lk.groupby("dealer_name").size().describe().to_dict())
print("categories:", sorted(lk["category"].unique()))
print("pct_mapped range:", lk["pct_mapped"].min(), lk["pct_mapped"].max())

print("\n" + "=" * 70)
print("C. DB level — leverage from 1-dealer 'countries'")
print("=" * 70)
print(t[["db", "dealers", "ids_total_avg", "gps_capture_vs_max", "genuine_share_eur",
         "pms_capture_total"]].sort_values("dealers").to_string(index=False))

pairs = [("ids_total_avg", "gps_capture_vs_max"), ("ids_D", "gps_capture_vs_max"),
         ("ids_total_avg", "genuine_share_eur"), ("ids_total_avg", "pms_capture_total")]
for xc, yc in pairs:
    d = t[[xc, yc, "db", "dealers"]].dropna()
    r0, p0 = stats.spearmanr(d[xc], d[yc])
    d5 = d[d["dealers"] >= 5]
    r5, p5 = stats.spearmanr(d5[xc], d5[yc]) if len(d5) >= 5 else (np.nan, np.nan)
    print(f"\n{xc} vs {yc}")
    print(f"   all DBs      rho={r0:.3f} p={p0:.4f} n={len(d)}")
    print(f"   >=5 dealers  rho={r5:.3f} p={p5:.4f} n={len(d5)}   (drops {sorted(set(d.db)-set(d5.db))})")
    jk = []
    for i in range(len(d)):
        s = d.drop(d.index[i])
        rr, _ = stats.spearmanr(s[xc], s[yc])
        jk.append((d.iloc[i]["db"], round(rr, 3)))
    jk.sort(key=lambda x: abs(x[1]))
    print(f"   jackknife rho range {min(v for _, v in jk):.3f}..{max(v for _, v in jk):.3f}; "
          f"weakest when dropping {jk[0][0]} -> {jk[0][1]}")

print("\n" + "=" * 70)
print("D. Multiple testing")
print("=" * 70)
res = pd.read_csv(D / "ids_corr_results_2026-08-10.csv")
db = res[(res["level"] == "DB") & (res["n"] >= 8)].dropna(subset=["spearman_p"])
print(f"DB-level tests run with n>=8: {len(db)}")
print(f"  p<0.05: {(db['spearman_p'] < 0.05).sum()}  | expected by chance at 5%: {0.05*len(db):.1f}")
ps = np.sort(db["spearman_p"].values)
m = len(ps)
bh = ps <= (np.arange(1, m + 1) / m) * 0.10
print(f"  survive Benjamini-Hochberg FDR 10%: {bh.sum()}")
print("  note: IDS sections inter-correlate rho 0.66-0.91, so these are NOT independent tests")

print("\n" + "=" * 70)
print("E. Is GPS-capture-vs-max just segment mix (CV vs LCV)?")
print("=" * 70)
g = pd.read_csv(D / "gps_spu_by_distributor.csv")
g = g[g["year"] == 2025]
m = t.merge(g[["distributor_code", "max_spend_eur", "spend_per_unit_eur", "region"]],
            left_on="db", right_on="distributor_code", how="left")
print(m[["db", "dealers", "ids_total_avg", "max_spend_eur", "spend_per_unit_eur",
         "gps_capture_vs_max", "region"]].sort_values("ids_total_avg", ascending=False).to_string(index=False))
d = m[["ids_total_avg", "max_spend_eur", "spend_per_unit_eur", "gps_capture_vs_max"]].dropna()
for c in ["max_spend_eur", "spend_per_unit_eur"]:
    r, p = stats.spearmanr(d["ids_total_avg"], d[c])
    print(f"rho(IDS total, {c}) = {r:.3f} p={p:.4f} n={len(d)}")
