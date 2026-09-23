"""Did the frozen legacy file count NMR's interim band, or not?

For the 297 rows the frozen file carries, compare three answers to "which truck rungs does this
part number fit":
  frozen        - what the shipped page reads today
  settled only  - the corrected table's rule (a quarantined code contributes no band)
  settled+NMR   - the corrected table's rule with the quarantined code's interim band counted

If `frozen` equals `settled+NMR` row for row, then re-basing on `settled only` removes a rung from
every NMR-bearing part number, and that has to be reported before the write rather than after.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import (  # noqa: E402
    N_SERIES_BANDS, NOT_IN_SCOPE, UNRESOLVED, band_for,
)

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}


def main() -> int:
    frozen = pd.read_csv(ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv",
                         dtype=str, low_memory=False).fillna("")
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    frozen["k"] = frozen.pn.map(n)
    ap["k"] = ap.pn.map(n)
    ap = ap.set_index("k")

    rows = []
    for r in frozen.itertuples():
        a = ap.loc[r.k]
        settled = sorted({b for b in str(a.n_series_bands).split("|") if b})
        with_nmr = {b for b in settled}
        for c in str(a.parked_codes).split(";"):
            c = c.strip()
            if not c:
                continue
            b = band_for(c)
            if b in N_SERIES_BANDS:
                with_nmr.add(b)
        rows.append({
            "pn": r.k, "cat": a.pms_category,
            "frozen": sorted({SHORT[b] for b in str(r.band_list).strip("[]'").split("', '")
                              if b in SHORT}),
            "settled": sorted({SHORT[b] for b in settled}),
            "with_nmr": sorted({SHORT[b] for b in with_nmr}),
            "parked": str(a.parked_codes),
        })
    d = pd.DataFrame(rows)
    eq_frozen_settled = sum(1 for r in d.itertuples() if r.frozen == r.settled)
    eq_frozen_with = sum(1 for r in d.itertuples() if r.frozen == r.with_nmr)
    eq_withmr_settled = sum(1 for r in d.itertuples() if r.with_nmr == r.settled)
    print("=" * 96)
    print("THE FROZEN FILE'S OWN RULE, ON THE 297 ROWS IT CARRIES")
    print("=" * 96)
    print(f"  rows where frozen == settled only            : {eq_frozen_settled:3d} / {len(d)}")
    print(f"  rows where frozen == settled + NMR interim   : {eq_frozen_with:3d} / {len(d)}")
    print(f"  rows where settled == settled + NMR interim  : {eq_withmr_settled:3d} / {len(d)}")
    print()
    only_nmr = d[(d.with_nmr != d.settled)]
    print(f"  rows where a parked NMR code adds a rung: {len(only_nmr)}")
    print(f"      of those the frozen file has the NMR rung too: "
          f"{sum(1 for r in only_nmr.itertuples() if r.frozen == r.with_nmr)}")
    print(f"      of those the frozen file does NOT      : "
          f"{sum(1 for r in only_nmr.itertuples() if r.frozen != r.with_nmr)}")
    print()
    for r in only_nmr.head(12).itertuples():
        print(f"   {r.pn:>12s} frozen {str(r.frozen):22s} settled {str(r.settled):16s}"
              f" +NMR {str(r.with_nmr):22s} parked {r.parked}")
    print()
    bad = d[(d.frozen != d.settled) & (d.frozen != d.with_nmr)]
    print(f"  rows matching NEITHER rule: {len(bad)}")
    for r in bad.head(12).itertuples():
        print(f"   {r.pn:>12s} frozen {str(r.frozen):22s} settled {str(r.settled):16s}"
              f" +NMR {str(r.with_nmr):22s} parked {r.parked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
