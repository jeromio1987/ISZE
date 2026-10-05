"""Measure both-stage coverage per distributor: intersection months and contiguous runs.

Recomputes from the derived source files (no raw billing), applying the same rules the
build uses, so the contiguity claim can be checked rather than inferred.
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


def month_axis():
    out, y, m = [], 2023, 1
    while (y, m) <= (2026, 8):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def runs(flags):
    """contiguous runs of True, as (start_index, length)."""
    out, i = [], 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j + 1 < len(flags) and flags[j + 1]:
                j += 1
            out.append((i, j - i + 1))
            i = j + 1
        else:
            i += 1
    return out


def main():
    ax = month_axis()
    idx = {m: i for i, m in enumerate(ax)}

    sf = pd.read_parquet(D + r"\sales_fact.parquet",
                         columns=["billing_date", "sold_to_sap", "saty"])
    sf["db"] = sf["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True).map(SAP2DB)
    sf = sf[sf.db.notna() & ~sf.saty.isin(EXCL) & sf.saty.notna()]
    sf["month"] = sf.billing_date.dt.strftime("%Y-%m")

    bil = {}
    for db, g in sf.groupby("db"):
        f = [False] * len(ax)
        for m in g.month.unique():
            if m in idx:
                f[idx[m]] = True
        bil[db] = f

    sol = {}
    for db, stems in USE.items():
        f = [False] * len(ax)
        for s in stems:
            d = pd.read_csv(D + rf"\dealer_sellout_long{s}.csv",
                            dtype=str, usecols=["period", "period_grain", "qty"],
                            low_memory=False)
            d = d[d.period_grain == "month"]
            d["q"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
            for m in d.loc[d.q > 0, "period"].unique():
                if m in idx:
                    f[idx[m]] = True
        sol[db] = f

    print(f"{'distributor':<10} {'billed':>7} {'sold':>6} {'both':>6} "
          f"{'longest run':>11}  {'that run covers':<24} {'12 vs 12 needs 24':>17}")
    print("-" * 96)
    rows = []
    for db in USE:
        b, s = bil[db], sol[db]
        both = [x and y for x, y in zip(b, s)]
        rr = runs(both)
        longest = max((n for _, n in rr), default=0)
        span = "-"
        if rr:
            st, n = max(rr, key=lambda t: t[1])
            span = f"{ax[st]} to {ax[st + n - 1]}"
        ok = "YES" if longest >= 24 else "no"
        print(f"{db:<10} {sum(b):>7} {sum(s):>6} {sum(both):>6} {longest:>11}  {span:<24} {ok:>17}")
        rows.append((db, sum(b), sum(s), sum(both), longest, span, ok, len(rr)))

    print("\nall contiguous both-stage runs, longest first:")
    for db, *_ , nr in rows:
        both = [x and y for x, y in zip(bil[db], sol[db])]
        rr = sorted(runs(both), key=lambda t: -t[1])
        txt = ", ".join(f"{ax[st]}..{ax[st+n-1]} ({n}m)" for st, n in rr[:5])
        print(f"  {db:<10} {len(rr)} run(s): {txt}")


if __name__ == "__main__":
    main()
