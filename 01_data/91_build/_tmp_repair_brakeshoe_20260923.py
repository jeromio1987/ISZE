"""The material question, answered from facts rather than a model.

The repair moved two brake_shoe part numbers from one band to two. The page's payload still shows
brake_shoe as `ok` with one band each. This reports:

  * brake_shoe in the payload: verdict, shareShared, and the euro it covers
  * brake_shoe in the repaired file: rows and single-band count
  * the euro in the page's frame on the two rows that moved
  * whether that euro is large enough to push the family's shareShared over the 15% line that
    separates `ok` from `thin`

The page is not touched and nothing is rebuilt.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BUILD = ROOT / "02_dashboards" / "sales" / "_build"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def payload(p: Path) -> dict:
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                p.read_text(encoding="utf-8"), re.S).group(1))


def main() -> int:
    pay = payload(HTML)
    print("=" * 100)
    print("brake_shoe IN THE PAGE'S OWN PAYLOAD, BOTH CLOCKS")
    print("=" * 100)
    for clk in ("CY", "FY"):
        b = pay["comparability"][clk]["brake_shoe"]
        print(f"  {clk}: verdict {b['verdict']:8s} shareShared {b['shareShared']:<8} "
              f"euro {b['euro']:>10,}  pns {b['pns']:>3}  singleBandPns {b['singleBandPns']:>3}")
        print(f"      why: {b['why'] or '(no caveat)'}")
    print()
    print(f"  degree.brake_shoe: {pay['degree'].get('brake_shoe')}")
    print()

    leg = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    leg["k"] = leg.pn.map(n)
    s = leg[leg.category == "brake_shoe"]
    print("=" * 100)
    print("brake_shoe IN THE REPAIRED FILE")
    print("=" * 100)
    print(f"  rows {len(s)}   single-band {int((s.n_bands.astype(int) == 1).sum())}   "
          f"multi-band {int((s.n_bands.astype(int) > 1).sum())}")
    for r in s.itertuples():
        print(f"      {r.k:>12s} bands {r.bands:20s} n_bands {r.n_bands}  parked {r.parked_codes!r}")
    print()

    # the rows the repair moved, in the page's own billing frame
    cache = pd.read_parquet(BUILD / "_deep_billing_cache.parquet")
    cache["pn"] = cache.pn.astype(str).map(n)
    print("=" * 100)
    print("THE FOUR ROWS THE REPAIR MOVED, IN THE PAGE'S BILLING CACHE")
    print("=" * 100)
    moved = ("5876103260", "5878320470", "8983320620", "8983615742")
    for k in moved:
        cy = cache[(cache.pn == k) & (cache.y == 2025)]
        fy = cache[(cache.pn == k) & (cache.fy == 2026)]
        fam = leg[leg.k == k]
        print(f"      {k:>12s} family {str(fam.category.iloc[0]) if len(fam) else '?':14s} "
              f"CY2025 euro {float(cy.net_sales_value.sum()):>10,.2f}   "
              f"FY2026 euro {float(fy.net_sales_value.sum()):>10,.2f}")

    bcy = pay["comparability"]["CY"]["brake_shoe"]
    moved_cy = float(cache[(cache.pn.isin(moved)) & (cache.y == 2025)
                           & (cache.pn.isin(set(s.k)))].net_sales_value.sum())
    print()
    print("  the two brake_shoe rows among them, euro in CY2025: "
          f"{moved_cy:,.2f} against the family's CY2025 euro of {bcy['euro']:,}")
    if bcy["euro"]:
        print(f"  as a share of the family's euro: {100 * moved_cy / bcy['euro']:.2f}%")
    print()
    print("  the page's rule: shareShared > 0.15 reads 'thin' (a caveat), > 0.50 reads 'pooled'.")
    print("  So if those rows carry more than 15% of brake_shoe's euro, a rebuild would move the")
    print("  verdict from 'ok' to 'thin' - both of which the page treats as SPLITTABLE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
