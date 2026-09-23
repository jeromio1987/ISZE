"""Tie out every headline number the page shows against the source parquet.

Nothing here reads the page or its embedded data: it recomputes from
pricing_aim_source_lines.parquet (the file the pipeline writes) so the page
cannot agree with itself while disagreeing with the source.
"""
import numpy as np
import pandas as pd

L = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pricing_aim_source_lines.parquet"
df = pd.read_parquet(L)
pr = df[df["priced_both"]].copy()
pr["pn"] = pr["part_number"].astype(str)

ok = []


def check(label, got, want, tol=0.01, fmt="{:.4f}"):
    good = abs(float(got) - float(want)) <= tol
    ok.append(good)
    print("  %-58s %-16s want %-16s %s"
          % (label, fmt.format(got), fmt.format(want), "OK" if good else "MISMATCH"))


def counts(vals):
    v = np.sort(np.asarray(vals, dtype=float))[::-1]
    c = np.cumsum(v)
    T = float(v.sum())
    return len(v), round(T, 2), int(np.argmax(c >= 0.5 * T) + 1), int(np.argmax(c >= 0.8 * T) + 1)


print("BRAKE FAMILY - NETWORK")
b = pr[pr["aim_l1"] == "Brakes"]
check("weighted move %", 100 * (b["new_eur"].sum() / b["prior_eur"].sum() - 1), 7.8352)
check("step eur", b["step_eur"].sum(), 229506.42)
check("prior base eur", b["prior_eur"].sum(), 2929172.19)
check("priced rows", len(b), 1617, fmt="{:.0f}")
check("part numbers", b["pn"].nunique(), 527, fmt="{:.0f}")
check("parts billed (all in scope)", df[df["aim_l1"] == "Brakes"]["billed_eur"].sum(), 3347821.75)

print("BRAKE FAMILY - ITUK")
i = pr[(pr["db"] == "ITUK") & (pr["aim_l1"] == "Brakes")]
check("weighted move %", 100 * (i["new_eur"].sum() / i["prior_eur"].sum() - 1), 12.1247)
check("step eur", i["step_eur"].sum(), 89542.27)
check("prior base eur", i["prior_eur"].sum(), 738510.72)
check("priced rows", len(i), 175, fmt="{:.0f}")
w = pr[pr["db"] == "ITUK"]
check("whole book weighted %", 100 * (w["new_eur"].sum() / w["prior_eur"].sum() - 1), 6.6695)
check("whole book prior eur", w["prior_eur"].sum(), 5334676.67)
check("whole book step eur", w["step_eur"].sum(), 355797.80)

print("THE HEADLINE PART NUMBER")
h = pr[(pr["pn"] == "8982447940")]
check("network step eur", h["step_eur"].sum(), 81934.18)
hi = h[h["db"] == "ITUK"]
check("ITUK step eur", hi["step_eur"].sum(), 52113.12)
check("prior base JPY", hi["prior_base_jpy"].iloc[0], 12940, tol=0.5, fmt="{:.0f}")
check("new base JPY", hi["new_base_jpy"].iloc[0], 16158, tol=0.5, fmt="{:.0f}")
check("price move %", 100 * (hi["new_base_jpy"].iloc[0] / hi["prior_base_jpy"].iloc[0] - 1),
      24.8686)
check("markets carrying it", h["db"].nunique(), 13, fmt="{:.0f}")
check("ITUK brake share %", 100 * hi["step_eur"].sum() / i["step_eur"].sum(), 58.20, tol=0.05)

print("BRAKE LEVEL 2 - NETWORK (what the table shows)")
l2 = b.groupby("aim_l2").agg(step=("step_eur", "sum"), prior=("prior_eur", "sum"),
                             new=("new_eur", "sum"), priced_rows=("billed_eur", "size"),
                             billed=("billed_eur", "sum"))
for name, want_step, want_prior, want_priced in (
    ("Pads & Shoes", 113830.20, 1102445.70, 555),
    ("Discs & Drums", 81265.26, 1293713.41, 276),
    ("Caliper", 13588.16, 189218.33, 366),
):
    r = l2.loc[name]
    check(f"{name} step eur", r["step"], want_step)
    check(f"{name} prior eur", r["prior"], want_prior)
    check(f"{name} priced lines", r["priced_rows"], want_priced, fmt="{:.0f}")
    check(f"{name} weighted %", 100 * (r["new"] / r["prior"] - 1),
          100 * (want_step / want_prior + 1) - 100, tol=0.01)

print("BRAKE LEVEL 2 - ITUK")
i2 = i.groupby("aim_l2").agg(step=("step_eur", "sum"), prior=("prior_eur", "sum"),
                             priced_rows=("billed_eur", "size"))
r = i2.loc["Pads & Shoes"]
check("ITUK Pads & Shoes step eur", r["step"], 64590.19, tol=0.05)
check("ITUK Pads & Shoes prior eur", r["prior"], 366405.79, tol=0.05)
check("ITUK Pads & Shoes priced lines", r["priced_rows"], 51, fmt="{:.0f}")
print("  share of ITUK brake step pct: {:.1f}  (page shows 72.1)".format(
      100 * r["step"] / i["step_eur"].sum()))

print("CONCENTRATION - NETWORK, ALL FAMILIES")
n, T, half, eight = counts(pr[pr["step_eur"] > 0].groupby("pn")["step_eur"].sum().values)
check("half count", half, 162, fmt="{:.0f}")
check("eighty count", eight, 1068, fmt="{:.0f}")
print("  part numbers with a step: %d" % n)
pos = pr[pr["step_eur"] > 0]
check("part numbers that moved up", pos["pn"].nunique(), 15093, fmt="{:.0f}")

print("CONCENTRATION - NETWORK, BRAKES ONLY")
n2, T2, half2, eight2 = counts(
    pos[pos["aim_l1"] == "Brakes"].groupby("pn")["step_eur"].sum().values)
check("half count", half2, 2, fmt="{:.0f}")
check("eighty count", eight2, 18, fmt="{:.0f}")
print("  part numbers with a step: %d  (page shows 478)" % n2)

print("CONCENTRATION - ITUK")
n3, T3, half3, eight3 = counts(pos[pos["db"] == "ITUK"].groupby("pn")["step_eur"].sum().values)
check("half count", half3, 46, fmt="{:.0f}")
check("eighty count", eight3, 271, fmt="{:.0f}")
print("  part numbers with a step: %d  (page shows 4,031)" % n3)
n4, T4, half4, eight4 = counts(
    pos[(pos["db"] == "ITUK") & (pos["aim_l1"] == "Brakes")].groupby("pn")["step_eur"].sum().values)
check("brake half count", half4, 1, fmt="{:.0f}")
check("brake eighty count", eight4, 5, fmt="{:.0f}")
print("  brake part numbers with a step: %d  (page shows 158)" % n4)

print("TAXONOMY BASIS")
v2 = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv",
                 dtype=str, low_memory=False)
br2 = set(v2.loc[v2["aim_l1_fixed"].astype(str).str.strip() == "Brakes", "part_number"]
          .astype(str).str.zfill(10))
v1 = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v1.csv",
                 dtype=str, low_memory=False)
br1 = set(v1.loc[v1["aim_l1"].astype(str).str.strip() == "Brakes", "part_number"]
          .astype(str).str.zfill(10))
m2 = pr[pr["pn"].isin(br2)]
m1 = pr[pr["pn"].isin(br1)]
print("  v2 (aim_l1_fixed, what the page uses): %d part numbers, step %.2f" % (m2["pn"].nunique(), m2["step_eur"].sum()))
print("  v1 (what the policy paper used)      : %d part numbers, step %.2f" % (m1["pn"].nunique(), m1["step_eur"].sum()))
print("  the page's 527 / 229,506.42 matches v2:", m2["pn"].nunique() == 527 and abs(m2["step_eur"].sum() - 229506.42) < 0.01)
print("  bogus mixed pairing present anywhere in the page's basis?",
      abs(m2["step_eur"].sum() / m2["prior_eur"].sum() * 100 - (100 + 7.36)) < 1)

print()
print("RESULT:", "ALL TIE-OUTS OK" if all(ok) else "FAILURES PRESENT",
      "(%d/%d checks)" % (sum(ok), len(ok)))
