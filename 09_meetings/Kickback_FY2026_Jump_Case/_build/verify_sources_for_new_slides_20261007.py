"""Verify every figure that will go on the new slides, from the source files.

Prints ONLY what the files say, so the slide text can be checked against it.
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_stock_insights_20261007")

print("=" * 90)
print("1. PORTUGAL FAMILY STOCK BUILD - portugal_family_stock_build.csv")
fb = pd.read_csv(D / "portugal_family_stock_build.csv")
fb["build"] = pd.to_numeric(fb["build"])
print("   rows:", len(fb), " sum of build:", round(fb["build"].sum(), 2))
top = fb.sort_values("build", ascending=False).head(8)
for _, r in top.iterrows():
    print("   %-26s %12s  billed %8.0f  sold %8.0f  sold-billed %+8.0f"
          % (r["family"], round(r["build"], 2), r["billed_qty"], r["sold_qty"],
             r["sold_qty"] - r["billed_qty"]))
three = fb[fb["family"].isin(["Brakes", "Accident & Body", "Electrical"])]["build"].sum()
print("   Brakes + Accident & Body + Electrical =", round(three, 2))
maint = fb[fb["family"] == "Maintenance Service"].iloc[0]
print("   Maintenance Service: build %s  billed %s  sold %s"
      % (round(maint["build"], 2), maint["billed_qty"], maint["sold_qty"]))
print("   6th family by value:",
      fb.sort_values("build", ascending=False).iloc[5]["family"],
      round(fb.sort_values("build", ascending=False).iloc[5]["build"], 2))

print("=" * 90)
print("2. PORTUGAL PART-LEVEL - portugal_pn_stock_build.csv")
pn = pd.read_csv(D / "portugal_pn_stock_build.csv")
print("   columns:", list(pn.columns))
print("   rows:", len(pn))
num = [c for c in pn.columns if pn[c].dtype.kind in "if"]
print("   numeric cols:", num)

print("=" * 90)
print("3. FAMILY BILLING FY - family_billing_imotors.csv")
fbi = pd.read_csv(D / "family_billing_imotors.csv")
print("   columns:", list(fbi.columns))
for fam in ["Maintenance Service", "Brakes", "Accident & Body", "Electrical"]:
    row = fbi[fbi["family"] == fam]
    if len(row):
        r = row.iloc[0]
        print("   %-22s 2025 %12.2f 2026 %12.2f FY26vsFY25 %s%%  abs change %+.2f"
              % (fam, r["2025"], r["2026"], r["FY26_vs_FY25_%"], r["2026"] - r["2025"]))

print("=" * 90)
print("4. PORTUGAL FAMILY FY - portugal_family_fy.csv")
pfy = pd.read_csv(D / "portugal_family_fy.csv")
r = pfy[pfy["family"] == "Maintenance Service"].iloc[0]
print("   Maintenance Service: 2025 %s  2026 %s  FY26_vs_FY25 %s"
      % (r["2025"], r["2026"], r["FY26_vs_FY25"]))
print("   abs change:", round(r["2026"] - r["2025"], 2),
      " pct:", round((r["2026"] / r["2025"] - 1) * 100, 2))

print("=" * 90)
print("5. MONTHLY SERIES - portugal_reference_case_monthly.csv")
mon = pd.read_csv(D / "portugal_reference_case_monthly.csv")
st = mon.dropna(subset=["stock_days"])
print("   stock_days present:", len(st), "from", int(st["ym_int"].min()), "to", int(st["ym_int"].max()))
print("   stock min/max:", st["stock_days"].min(), st["stock_days"].max())
print("   billing months:", len(mon), "from", int(mon["ym_int"].min()), "to", int(mon["ym_int"].max()))
print("   backorder/fill from:",
      int(mon.dropna(subset=["backorder_lines"])["ym_int"].min()),
      "to", int(mon.dropna(subset=["fill"])["ym_int"].max()))
print("   peak stock days:", int(st.loc[st["stock_days"].idxmax(), "ym_int"]),
      st["stock_days"].max(), "; peak stock EUR:", round(st["stock_eur"].max(), 0),
      "at", int(st.loc[st["stock_eur"].idxmax(), "ym_int"]))
print("   Aug 2025 stock:", float(st[st["ym_int"] == 202508]["stock_days"].iloc[0]) if 202508 in set(st["ym_int"]) else "n/a")

print("=" * 90)
print("6. BILLING vs SALES TO DEALER - portugal_billing_vs_sales_to_dealer.csv")
b = pd.read_csv(D / "portugal_billing_vs_sales_to_dealer.csv")
b.columns = ["ym", "billed", "std", "gap", "pct"]
b["billed"] = pd.to_numeric(b["billed"])
b["std"] = pd.to_numeric(b["std"])
print("   months:", len(b), b["ym"].tolist())
print("   billed total:", round(b["billed"].sum(), 2), " sales-to-dealer total:", round(b["std"].sum(), 2))
tot = b.sum(numeric_only=True)
print("   gap total:", round(tot["gap"], 2), " billed as % of dealer:", round(tot["billed"] / tot["std"] * 100, 1))

print("=" * 90)
print("7. IBX STOCK DAYS - stock_days_monthly_pivot.csv")
piv = pd.read_csv(D / "stock_days_monthly_pivot.csv")
ibx = piv[["ym", "IBX (Benelux)"]].dropna()
print(ibx.to_string(index=False))

print("=" * 90)
print("8. KOSHA + PROGRAMME PLAN - from the deck's own slide 3 figures (cross-check file)")
print("   programme plan FY2026 29.19M / FY2027 31.82M: budget_per_DB_reviewed_24042026.xlsx 'Incentive FY27'")
print("   Kosha path FY2024 29.6M .. FY2031 52.1M: Year-End Review 'Kosha Gap & FY2027'")

print("=" * 90)
print("9. PRICING INDEX - room_to_raise_summary_2026-10-02.json")
RS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_5pct_proposal_2026-09-29\room_to_raise_2026-10-02\room_to_raise_summary_2026-10-02.json")
d = json.loads(RS.read_text(encoding="utf-8"))
am = d["index_distribution"]["aftermarket_street"]
print("   aftermarket_street:", am)
print("   suff aftermarket:", d["sufficiency"]["1_outside_prices_aftermarket_street_any_date"])
print("   suff competitor:", d["sufficiency"]["2_competitor_number_confirmed_likely"])

print("=" * 90)
print("10. PORTUGAL COMPETITIVE COVERAGE - summary.json")
SJ = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\_competitive_price_overlap_20261006\summary.json")
s = json.loads(SJ.read_text(encoding="utf-8"))
print("   sold_to:", s["sold_to"], s["distributor"])
print("   coverage:", json.dumps(s["coverage"], indent=1))
print("   reference_dealer_price:", s["reference_dealer_price"])
