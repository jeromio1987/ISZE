"""Portugal, month by month: which stage has data, to show where the run breaks."""
import pandas as pd

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
EXCL = ["CR", "RE", "DR", "ZDR", "FD"]

axis, y, m = [], 2025, 1
while (y, m) <= (2026, 8):
    axis.append(f"{y:04d}-{m:02d}")
    m += 1
    if m == 13:
        y, m = y + 1, 1

sf = pd.read_parquet(D + r"\sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "saty", "billed_qty"])
b = sf[sf.sold_to_sap.isin([519, 92]) & ~sf.saty.isin(EXCL) & sf.saty.notna()].copy()
b["month"] = b.billing_date.dt.strftime("%Y-%m")
billed = {a: float(b.loc[b.month == a, "billed_qty"].sum()) for a in axis}

so = pd.concat([pd.read_csv(D + rf"\dealer_sellout_long_PORTUGAL_{p}.csv",
                            dtype=str, usecols=["period", "period_grain", "qty"],
                            low_memory=False) for p in ("CY2025", "CY2026YTD")])
so = so[so.period_grain == "month"]
so["q"] = pd.to_numeric(so["qty"], errors="coerce").fillna(0)
sold = {a: float(so.loc[so.period == a, "q"].sum()) for a in axis}

print(f"{'month':<9} {'billed units':>13} {'sold units':>11}   both?")
print("-" * 52)
run, best = 0, (0, None)
for a in axis:
    bu, su = billed[a], sold[a]
    both = bu > 0 and su > 0
    if both:
        run += 1
        if run > best[0]:
            best = (run, a)
    else:
        run = 0
    flag = "yes" if both else ("BILLING EMPTY" if su > 0 else "no sold data")
    print(f"{a:<9} {bu:>13,.0f} {su:>11,.0f}   {flag}")

print(f"\nlongest unbroken run: {best[0]} months, ending {best[1]}")
print(f"months with both     : {sum(1 for a in axis if billed[a] and sold[a])} of {len(axis)}")
print(f"months with sold data: {sum(1 for a in axis if sold[a])} of {len(axis)}")
print(f"months with billing  : {sum(1 for a in axis if billed[a])} of {len(axis)}")
