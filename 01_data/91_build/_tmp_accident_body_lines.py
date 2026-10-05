import pandas as pd

from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
m = pd.read_csv(D / "aim_master_v1.csv", dtype=str, low_memory=False)
m["eur"] = pd.to_numeric(m["l12m_billed_eur"], errors="coerce").fillna(0)

ab = m[m["aim_l1"] == "Accident & Body"].copy()
tot = m["eur"].sum()
print("=== ACCIDENT & BODY ===")
print("rows", len(ab), "| PNs", ab["part_number"].nunique(),
      "| EUR", round(ab["eur"].sum()), "|", round(100 * ab["eur"].sum() / tot, 2), "% of network")
print()
print("--- AIM L2 inside it ---")
g = ab.groupby("aim_l2").agg(rows=("part_number", "size"), eur=("eur", "sum")).sort_values("eur", ascending=False)
g["eur"] = g["eur"].round(0)
g["share_%"] = (100 * g["eur"] / ab["eur"].sum()).round(1)
print(g.to_string())

print()
print("--- what the CATALOGUE says these are (cat_l2) ---")
g2 = ab.groupby("cat_l2").agg(rows=("part_number", "size"), eur=("eur", "sum")).sort_values("eur", ascending=False)
g2["eur"] = g2["eur"].round(0)
print(g2.head(12).to_string())

print()
print("--- TOP 30 part lines by billed euro ---")
t = ab.sort_values("eur", ascending=False).head(30)
for _, r in t.iterrows():
    print("%-12s %11s | %-40s | AIM %s / %s | CAT %s / %s" % (
        r["part_number"], round(r["eur"]), str(r["description"])[:40],
        str(r["aim_l2"])[:16], str(r["aim_l3"])[:20],
        str(r["cat_l1"])[:14], str(r["cat_l2"])[:16]))

print()
print("--- concentration ---")
s = ab["eur"].sort_values(ascending=False)
for n in (10, 25, 50, 100, 250, 500):
    if n <= len(s):
        print(f"  top {n:>4} lines = {round(100*s.head(n).sum()/s.sum(),1)}% of Accident & Body")
