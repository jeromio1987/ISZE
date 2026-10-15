import json, re
from pathlib import Path
import pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); H = Path(__file__).parent; DER = ISZE / "01_data/00_derived"
pd.set_option("display.width", 220)
P = pd.read_pickle(H / "_pms_parts.pkl")
fb = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str)
fb = fb.drop_duplicates("pn")[["pn", "pms_category", "family"]]
m = P.merge(fb, on="pn", how="left", suffixes=("", "_fb"))
g = m[m.pms_category.notna()].groupby("pms_category").apply(lambda d: pd.Series({"parts": len(d), "billed": d.b.sum(), "extra": d.x.sum(), "move": d.x.sum() / d.b.sum(), "own_step": (d.b * d.cp).sum() / d.b.sum()}), include_groups=False).sort_values("billed", ascending=False)
print("PMS categories in vehicle_family_bands joined to the revision base:"); print(g.round(4).to_string())
print("total", len(m[m.pms_category.notna()]), "parts, EUR", round(m.b[m.pms_category.notna()].sum()), "billed; extra", round(m.x[m.pms_category.notna()].sum()), "move", round(m.x[m.pms_category.notna()].sum() / m.b[m.pms_category.notna()].sum(), 4))
D = json.loads((H / "payload4.json").read_text(encoding="utf-8"))
LN = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits"])
LN["pn"] = [D["parts"][i][0] for i in LN.pi]
LN["cat"] = LN.pn.map(P.set_index("pn").cat)
f = LN[LN.cat.isin(["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"])]
print("\nfilter lines billed", round(f.b.sum()), "| in the under-45% capture hold", round(f.b[(f.bits & 16) > 0].sum()), "| in the service hold of the 8 markets", round(f.b[(f.bits & 1) > 0].sum()))
for fn in ["ISZE_PMS_Price_Response_Brief_2026-09-22.html", "ISZE_PMS_Campaign_Impact_Review_2026-09-23.html", "ISZE_IAM_Price_vs_Billed_PN.html", "ISZE_Parts_Price_Intelligence.html", "ISZE_IAM_Quality_Positioning_Overview.html"]:
    p = ISZE / "02_dashboards/pricing" / fn
    if not p.exists(): print("missing", fn); continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    title = re.search(r"<title>(.*?)</title>", t, re.S); hs = re.findall(r"<h[12][^>]*>(.*?)</h[12]>", t, re.S)[:6]
    print("\n", fn, len(t) // 1000, "KB | title:", title.group(1).strip()[:90] if title else None, "| location.hash used:", "location.hash" in t, "| search param:", "URLSearchParams" in t)
    print("   headings:", [re.sub("<.*?>", "", h).strip()[:70] for h in hs])
