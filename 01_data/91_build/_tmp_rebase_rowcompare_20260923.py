"""Compare the frozen legacy bands with the corrected mapping, row by row, on the overlap.

Uses the legacy file's own `bands` column (`3.5t+5.5t`), which cannot be mis-parsed, and asks for
each of the 297 rows the frozen file carries:
  frozen        what the shipped page reads today
  corrected     the corrected mapping's three-rung answer, quarantined codes contributing nothing
  +interim      the same with a quarantined code's interim rung counted as well

Then it counts how many rows each rule explains, and lists the ones that match the corrected
answer but not the frozen one - the movement the brief is asking for.
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
    N_SERIES_BANDS, UNRESOLVED, band_for,
)

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}
ORDER = ["3.5t", "5.5t", "7.5t"]
srt = lambda s: sorted(s, key=ORDER.index)  # noqa: E731


def main() -> int:
    frozen = pd.read_csv(ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv",
                         dtype=str, low_memory=False).fillna("")
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    frozen["k"] = frozen.pn.map(n)
    ap["k"] = ap.pn.map(n)
    A = ap.set_index("k")

    rows = []
    for r in frozen.itertuples():
        a = A.loc[r.k]
        settled = {SHORT[b] for b in str(a.n_series_bands).split("|") if b}
        interim = set(settled)
        for c in str(a.parked_codes).split(";"):
            c = c.strip()
            b = band_for(c) if c else UNRESOLVED
            if b in N_SERIES_BANDS:
                interim.add(SHORT[b])
        rows.append({
            "pn": r.k, "cat": a.pms_category,
            "frozen": srt({b for b in str(r.bands).split("+") if b}),
            "settled": srt(settled), "interim": srt(interim),
            "parked": str(a.parked_codes),
        })
    d = pd.DataFrame(rows)
    d["f_nb"] = d.frozen.map(len)
    d["s_nb"] = d.settled.map(len)
    d["i_nb"] = d.interim.map(len)
    same_fs = d.frozen == d.settled
    same_fi = d.frozen == d.interim
    same_si = d.settled == d.interim
    print("=" * 98)
    print("THE 297 ROWS THE FROZEN FILE CARRIES")
    print("=" * 98)
    print(f"  frozen bands == corrected (settled only)   : {int(same_fs.sum()):3d} / {len(d)}")
    print(f"  frozen bands == corrected + NMR interim    : {int(same_fi.sum()):3d} / {len(d)}")
    print(f"  corrected == corrected + NMR interim       : {int(same_si.sum()):3d} / {len(d)}")
    print(f"  rows the frozen file calls single-band     : {int((d.f_nb == 1).sum()):3d}")
    print(f"  rows the corrected map calls single-band   : {int((d.s_nb == 1).sum()):3d}")
    print(f"  rows that NEED the NMR interim rung to agree with frozen: "
          f"{int((~same_fs & same_fi).sum()):3d}")
    print()
    print("  frozen single-band rows whose corrected answer is NOT single-band:")
    for r in d[(d.f_nb == 1) & (d.s_nb != 1)].itertuples():
        print(f"      {r.pn:>12s} frozen {str(r.frozen):16s} corrected {str(r.settled):26s}"
              f" parked {r.parked}")
    print()
    print("  corrected single-band rows the frozen file called shared:")
    for r in d[(d.f_nb != 1) & (d.s_nb == 1)].head(15).itertuples():
        print(f"      {r.pn:>12s} frozen {str(r.frozen):26s} corrected {str(r.settled):16s}"
              f" parked {r.parked}")
    print()
    only_park = d[(d.s_nb == 1) & (d.i_nb > 1)]
    print(f"  corrected single-band ONLY because a parked NMR rung is left out: {len(only_park)}")
    print("      what the frozen file says for those rows:")
    print("      " + str({str(tuple(r.frozen)): 0 for r in only_park}).replace("{", "").replace("}", ""))
    vc = {}
    for r in only_park.itertuples():
        k = "+".join(r.frozen) or "(none)"
        vc[k] = vc.get(k, 0) + 1
    for k in sorted(vc):
        print(f"          frozen '{k}' : {vc[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
