"""The 46 rows the frozen file does not explain, even with NMR on its interim band.

Lists frozen bands against the corrected mapping under both rules, with the parked codes and the
series the corrected table names, so the cause of each disagreement is visible rather than guessed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import N_SERIES_BANDS, UNRESOLVED, band_for  # noqa: E402

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
        interim = {SHORT[b] for b in str(a.n_series_bands).split("|") if b}
        for c in str(a.parked_codes).split(";"):
            c = c.strip()
            if not c:
                continue
            b = band_for(c)
            if b in N_SERIES_BANDS:
                interim.add(SHORT[b])
        rows.append({"pn": r.k, "cat": a.pms_category,
                     "frozen": srt({b for b in str(r.bands).split("+") if b}),
                     "settled": srt(settled), "interim": srt(interim),
                     "parked": str(a.parked_codes),
                     "named": str(a.codes_named), "wild": str(a.wildcards_named)})
    d = pd.DataFrame(rows)
    bad = d[(d.frozen != d.settled) & (d.frozen != d.interim)]
    print(f"rows where frozen matches NEITHER rule: {len(bad)} of {len(d)}")
    print(f"  of which frozen is single-band: {int((bad.frozen.map(len) == 1).sum())}")
    print(f"  of which both rules agree with each other: "
          f"{int((bad.settled == bad.interim).sum())}")
    print()
    for r in bad.itertuples():
        print(f"  {r.pn:>12s} frozen {str(r.frozen):26s} settled {str(r.settled):26s}"
              f" +NMR {str(r.interim):26s} parked {r.parked!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
