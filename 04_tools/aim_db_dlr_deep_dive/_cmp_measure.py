"""Measure the sales-to-dealer month coverage per distributor, and the period pairs it supports.

Read-only. Derived files only. Prints:
  - month rows vs total rows per file
  - which months carry units, contiguous runs
  - the longest equal split, and the candidate pairs
  - the common run across all six distributors
"""
from pathlib import Path
import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

SELLOUT = {
    "PORTUGAL": ["_PORTUGAL_CY2025", "_PORTUGAL_CY2026YTD"],
    "IRELAND": ["_IRELAND_CY2025", "_IRELAND_CY2026YTD"],
    "ITUK": ["_ITUK_CY2023", "_ITUK_CY2024", "_ITUK_network_CY2025", "_ITUK_CY2026YTD"],
    "IUK": ["_IUK_CY2025", "_IUK_CY2026YTD"],
    "UTI": ["_UTI_CY2025", "_UTI_CY2026YTD"],
    "GREECE": ["_GREECE_CY2025"],
}


def axis():
    out, y, m = [], 2023, 1
    while (y, m) <= (2026, 8):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


AX = axis()
IDX = {a: i for i, a in enumerate(AX)}


def runs(flags):
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
    print(f"{'file':<52} {'month qty':>12} {'total qty':>12} {'delta':>12}")
    print("-" * 92)
    pres = {}
    for db, stems in SELLOUT.items():
        flags = [False] * len(AX)
        months_seen = set()
        for stem in stems:
            f = DER / f"dealer_sellout_long{stem}.csv"
            df = pd.read_csv(f, dtype=str, low_memory=False)
            df["q"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0.0)
            mo = df[df["period_grain"] == "month"]
            to = df[df["period_grain"].isin(["year", "ytd"])]
            print(f"{f.name:<52} {mo['q'].sum():>12,.0f} {to['q'].sum():>12,.0f} "
                  f"{mo['q'].sum() - to['q'].sum():>12,.0f}")
            for m in mo.loc[mo["q"] > 0, "period"].unique():
                months_seen.add(str(m).strip())
                if m in IDX:
                    flags[IDX[m]] = True
        pres[db] = flags
        rr = sorted(runs(flags), key=lambda t: -t[1])
        print(f"  {db}: {sum(flags)} months with units; runs:")
        for st, n in rr[:6]:
            print(f"     {AX[st]} .. {AX[st+n-1]}  ({n} months)")
        if rr:
            st, n = rr[0]
            N = n // 2
            print(f"     longest run {n} -> longest equal split {N} vs {N}; "
                  f"latest pair A {AX[st+n-2*N]}..{AX[st+n-N-1]}  B {AX[st+n-N]}..{AX[st+n-1]}")
            if n - 2 * N:
                print(f"     alternative alignment: A {AX[st]}..{AX[st+N-1]}  "
                      f"B {AX[st+N]}..{AX[st+2*N-1]}")
        print()

    print("common months across all six:", end=" ")
    common = [all(pres[db][i] for db in pres) for i in range(len(AX))]
    rr = sorted(runs(common), key=lambda t: -t[1])
    for st, n in rr[:6]:
        print(f"{AX[st]}..{AX[st+n-1]} ({n}m)", end="  ")
    print()


if __name__ == "__main__":
    main()
