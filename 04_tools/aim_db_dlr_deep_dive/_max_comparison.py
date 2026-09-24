"""For each distributor: the longest X-vs-X comparison the data can support, under two rules.

Rule A: sales to dealer months only   (the run Jerome is asking about)
Rule B: both stages in the same month (what the page's comparison currently needs)

A comparison of two N-month windows needs 2N contiguous months under the rule in question.
"""
import pandas as pd

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
EXCL = ["CR", "RE", "DR", "ZDR", "FD"]
USE = {
    "PORTUGAL": ["_PORTUGAL_CY2025", "_PORTUGAL_CY2026YTD"],
    "IRELAND": ["_IRELAND_CY2025", "_IRELAND_CY2026YTD"],
    "ITUK": ["_ITUK_CY2023", "_ITUK_CY2024", "_ITUK_network_CY2025", "_ITUK_CY2026YTD"],
    "IUK": ["_IUK_CY2025", "_IUK_CY2026YTD"],
    "UTI": ["_UTI_CY2025", "_UTI_CY2026YTD"],
    "GREECE": ["_GREECE_CY2025"],
}
SAP2DB = {"519": "PORTUGAL", "92": "PORTUGAL", "76": "IRELAND", "2575": "ITUK",
          "2574": "IUK", "1799": "UTI", "66": "GREECE"}

axis, y, m = [], 2023, 1
while (y, m) <= (2026, 8):
    axis.append(f"{y:04d}-{m:02d}")
    m += 1
    if m == 13:
        y, m = y + 1, 1
idx = {a: i for i, a in enumerate(axis)}


def longest(flags):
    best = run = 0
    end = None
    for i, f in enumerate(flags):
        run = run + 1 if f else 0
        if run > best:
            best, end = run, i
    return best, end


def maxcmp(n):
    """largest even 2N that fits inside a run of n months"""
    return (n // 2) if n >= 2 else 0


sf = pd.read_parquet(D + r"\sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "saty"])
sf["db"] = sf["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True).map(SAP2DB)
sf = sf[sf.db.notna() & ~sf.saty.isin(EXCL) & sf.saty.notna()]
sf["month"] = sf.billing_date.dt.strftime("%Y-%m")
bil = {}
for db, g in sf.groupby("db"):
    f = [False] * len(axis)
    for a in g.month.unique():
        if a in idx:
            f[idx[a]] = True
    bil[db] = f

print(f"{'distributor':<10} {'sold-only run':>13} {'X vs X':>7}   {'both-stage run':>15} {'X vs X':>7}")
print("-" * 68)
for db, stems in USE.items():
    s = [False] * len(axis)
    for stem in stems:
        d = pd.read_csv(D + rf"\dealer_sellout_long{stem}.csv", dtype=str,
                        usecols=["period", "period_grain", "qty"], low_memory=False)
        d = d[d.period_grain == "month"]
        d["q"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
        for a in d.loc[d.q > 0, "period"].unique():
            if a in idx:
                s[idx[a]] = True
    b = bil.get(db, [False] * len(axis))
    both = [x and y for x, y in zip(b, s)]
    ns, es = longest(s)
    nb, eb = longest(both)
    print(f"{db:<10} {ns:>13} {maxcmp(ns):>3} vs {maxcmp(ns):<3} {nb:>15} "
          f"{maxcmp(nb):>3} vs {maxcmp(nb):<3}")
