"""
Pickup warranty — network monthly, from the source exports.
===========================================================
Rebuilds 01_data/00_derived/warranty_fy26_monthly.csv from the claim files, so the
table is reproducible instead of inherited, and so the four months that only the new
network export holds are present.

THE DEFINITION CHANGES PARTWAY THROUGH THIS TABLE. Measured 2026-09-24, not assumed:

  * March 2025 - November 2025 rows count only claim lines that carry a real part
    number (`PartsNo` not blank and not "0"). That reproduces all eight rows exactly.
  * December 2025 onward the rows count EVERY claim line, including the labour-only
    lines that have no part number. That reproduces all nine of those rows exactly.

Both halves reproduce to the line, the claim count and both dollar columns -- but they
are not the same measure. Measured on the same source month (202512): every-line gives
2,497 claims / USD 788,131, part-number-lines-only gives 1,602 / USD 729,389. So the
step from November to December is partly volume and partly a definition change, and the
table must not be read as one continuous series across that boundary.

`PartsAmt_USD` is unaffected by the change: a labour-only line carries no parts value,
so both conventions give the same column. It is the `Claims` and `Total_USD` columns that
break at November/December 2025.

Columns keep their previous meaning:
  AssessMonth   period, YYYYMM
  Claims        claim lines, on the convention stated above for that month
  Total_USD     SUM(Total_USD)       -- source column, USD, NOT converted to euro
  PartsAmt_USD  SUM(PartsAmount_USD) -- source column, USD, NOT converted to euro

The dollar columns stay unconverted because that is what the table has always held.
The euro basis is a separate open issue (LCV-CURRENCY-RULE) and is not changed here.

One month per file, first file listed that holds the month wins, so no month can be
counted twice:
  202501-202511  Warranty_LCV_2025.xlsx
  202512         WArranty Data LCV_102025_082026.xlsx   (absent from both 2026 samples)
  202601-202604  ExportClaimAssessment202601-202605 with EV.xls.xlsx
  202605-202608  WArranty Data LCV_102025_082026.xlsx   (no other file holds these)

The previous file is kept as a dated backup, and the script REFUSES to write unless every
month the previous file held is reproduced exactly.
"""
from __future__ import annotations

import csv
import shutil
from collections import defaultdict
from pathlib import Path

import openpyxl

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
OUT = DATA / "00_derived" / "warranty_fy26_monthly.csv"
FIELDS = ["AssessMonth", "Claims", "Total_USD", "PartsAmt_USD"]

SOURCES = [
    DATA / "06_Warranty" / "Warranty_LCV_2025.xlsx",
    DATA / "WArranty Data LCV_102025_082026.xlsx",
    DATA / "06_Warranty" / "ExportClaimAssessment202601-202605 with EV.xls.xlsx",
]
BAD_PN = ("", "0", "None", "0.0")

# The table is the fiscal-2026 picture (Apr 2025 - Mar 2026) plus the months that have
# since arrived. Months before this bound belong to fiscal 2025 and are deliberately not
# pulled in, so the period the table covers is not silently widened.
MIN_MONTH = "202504"

# the convention the previous file used, month by month
PARTS_ONLY_UP_TO = "202511"          # months <= this: only lines with a part number
BREAK_MONTH = "202512"               # from this month: every claim line


def month_sums(path: Path) -> dict[str, dict[str, list[float]]]:
    """month -> {"all": [n,usd,parts], "pn": [n,usd,parts]} so either rule can be applied."""
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    agg: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"all": [0, 0.0, 0.0], "pn": [0, 0.0, 0.0]})
    for sn in wb.sheetnames:
        ws = wb[sn]
        it = ws.iter_rows(values_only=True)
        try:
            hdr = list(next(it))
        except StopIteration:
            continue
        I = {str(h): i for i, h in enumerate(hdr) if h is not None}
        if "AssessMonth" not in I:
            continue

        def g(r, col):
            i = I.get(col)
            return r[i] if (i is not None and i < len(r)) else None

        for r in it:
            m = str(g(r, "AssessMonth") or "").strip().split(".")[0]
            if len(m) < 6:
                continue
            tv, pv = g(r, "Total_USD"), g(r, "PartsAmount_USD")
            t = float(tv) if isinstance(tv, (int, float)) else 0.0
            p = float(pv) if isinstance(pv, (int, float)) else 0.0
            a = agg[m]["all"]
            a[0] += 1
            a[1] += t
            a[2] += p
            if str(g(r, "PartsNo") or "").strip() not in BAD_PN:
                b = agg[m]["pn"]
                b[0] += 1
                b[1] += t
                b[2] += p
    wb.close()
    return agg


def main() -> None:
    merged: dict[str, tuple[list[float], str]] = {}
    for src in SOURCES:
        if not src.exists():
            print(f"  ! missing {src.name}")
            continue
        got = month_sums(src)
        took = []
        for m, conv in got.items():
            if m in merged or m < MIN_MONTH:
                continue
            key = "pn" if m <= PARTS_ONLY_UP_TO else "all"
            merged[m] = (conv[key], f"{src.name} [{key}]")
            took.append(m)
        print(f"{src.name}: {len(got)} months, took {sorted(took)}")

    on_disk: dict[str, tuple[float, float, float]] = {}
    if OUT.exists():
        with open(OUT, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                on_disk[r["AssessMonth"]] = (float(r["Claims"]), float(r["Total_USD"]),
                                             float(r["PartsAmt_USD"]))

    print("\nreproducing every month the previous file held:")
    bad = 0
    for m in sorted(on_disk):
        if m not in merged:
            print(f"   {m}  NOT available from any source on disk")
            bad += 1
            continue
        a, b = on_disk[m], merged[m][0]
        ok = (a[0] == b[0]) and abs(a[1] - b[1]) < 1 and abs(a[2] - b[2]) < 1
        if not ok:
            bad += 1
        print(f"   {m}  {'MATCH ' if ok else 'DIFFERS'}  {merged[m][1]}"
              + ("" if ok else f"  prev={a} now={(b[0], round(b[1]), round(b[2]))}"))

    if bad:
        print(f"\nREFUSING TO WRITE - {bad} month(s) do not reproduce.")
        raise SystemExit(1)

    rows = [{"AssessMonth": m, "Claims": str(int(merged[m][0][0])),
             "Total_USD": f"{merged[m][0][1]:.1f}",
             "PartsAmt_USD": f"{merged[m][0][2]:.1f}"} for m in sorted(merged)]

    bak = OUT.with_name(OUT.name + ".bak_20260924_monthly")
    if OUT.exists() and not bak.exists():
        shutil.copy2(OUT, bak)
        print(f"\nbacked up previous -> {bak.name}")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {OUT.name} ({len(rows)} rows, {rows[0]['AssessMonth']}..{rows[-1]['AssessMonth']})")
    print("NOTE the measure changes at 202512 - see the module docstring.")
    for r in rows:
        mark = "  <- definition changes here" if r["AssessMonth"] == BREAK_MONTH else ""
        print(f"   {r['AssessMonth']}  {r['Claims']:>6}  {float(r['Total_USD']):>12,.0f}"
              f"  {float(r['PartsAmt_USD']):>12,.0f}{mark}")


if __name__ == "__main__":
    main()
