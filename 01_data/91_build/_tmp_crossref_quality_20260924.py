"""Read-only probe 8: crossref quality. Does one IAM number map to several Isuzu numbers?
That is the yellow flag Opus named ("one aftermarket number maps to several brand numbers").
"""
import pandas as pd

pd.set_option("display.width", 260)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = z(t["part_no"])
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, pd.to_numeric(t.billed_eur_t12m)))

e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
e["bl"] = e.Brand.fillna("").str.strip().str.upper()
e["cn"] = e["Part Number"].fillna("").str.strip().str.upper()
e = e[(e.bl != "") & (e.cn != "")]

x = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
x["pn"] = z(x["isze_pn"])
x["bl"] = x.Competitor_Brand.fillna("").str.strip().str.upper()
x["cn"] = x.competitor_pn.fillna("").str.strip().str.upper()

for label, d in [("Eucon Online 2025-07", e), ("Eucon crossref 2026-03", x)]:
    print("=" * 90)
    print(label, "rows %d" % len(d))
    # one IAM number under how many Isuzu PNs?
    g = d.groupby("cn").pn.nunique()
    print("   IAM numbers total: %d" % len(g))
    print("   under exactly 1 Isuzu PN : %d (%.0f%%)" % ((g == 1).sum(), 100 * (g == 1).mean()))
    print("   under 2 Isuzu PNs        : %d" % (g == 2).sum())
    print("   under 3+ Isuzu PNs       : %d" % (g >= 3).sum())
    multi = g[g >= 3].sort_values(ascending=False).head(4)
    print("   worst collisions:")
    for cn, n in multi.items():
        pns = sorted(d[d.cn == cn].pn.unique())
        print("      %-22s %d Isuzu numbers: %s" % (cn, n, ", ".join(pns[:6])))
    # same IAM number under two different IAM brands?
    g2 = d.groupby("cn").bl.nunique()
    print("   IAM numbers under more than one BRAND: %d" % (g2 > 1).sum())

# the 1-to-many question from the other side: our own duplicate PNs
print("=" * 90)
s = pd.read_parquet(ROOT + r"\01_data\00_derived\sales_with_crossref.parquet",
                    columns=["part_number", "xref_genuine_pn", "xref_bvp_pn"])
s["pn"] = z(s.part_number)
print("sales_with_crossref: one Isuzu part_number per BVP pair?")
g = s.groupby("pn").xref_bvp_pn.nunique()
print("   part numbers with more than one crossref target: %d of %d" % ((g > 1).sum(), len(g)))
print("   worst:")
print(g.sort_values(ascending=False).head(6).to_string())

# what the 2026 crossref says about our own list price vs online
print("=" * 90)
print("Eucon 2026-03 crossref: online EUR vs our IE40 list, per Isuzu number")
x["med"] = pd.to_numeric(x.med_online_eur, errors="coerce")
x["our"] = pd.to_numeric(x.isze_ie40_eur, errors="coerce")
agg = x.groupby("pn").agg(our=("our", "first"), n_brands=("cn", "nunique"),
                          lo=("med", "min"), hi=("med", "max"), mid=("med", "median"),
                          countries=("Country", lambda s: "|".join(sorted(set(s)))))
agg["ratio_mid"] = agg.mid / agg.our
print("   parts: %d. median competitor/our-list ratio: %.2f" % (len(agg), agg.ratio_mid.median()))
print("   parts where the cheapest online is below our list: %d of %d"
      % ((agg.lo < agg.our).sum(), len(agg)))
print(agg.sort_values("ratio_mid").head(10).round(2).to_string())
