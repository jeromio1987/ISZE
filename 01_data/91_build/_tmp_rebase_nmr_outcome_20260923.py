"""The NMR question, decided by the mapping's own two recorded candidates.

For every part number whose corrected three-rung list is a single rung ONLY because a quarantined
NMR / NMR85 code was left out, this asks: can that row be single-band under EITHER recorded NMR
candidate (5.5 t or 7.5 t)? A row is only safely "placeable" if at least one candidate leaves it on
one rung.
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
    N_SERIES_BANDS, UNRESOLVED, band_for, quarantine_candidates,
)

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}


def main() -> int:
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    ap["k"] = ap.pn.map(n)
    scope = ap[ap.n_series_bands != ""].copy()
    scope["nb"] = scope.n_series_bands.str.count(r"\|") + 1
    scope["eur_f"] = pd.to_numeric(scope.eur, errors="coerce").fillna(0.0)

    rows = []
    for r in scope.itertuples():
        kept = {SHORT[b] for b in str(r.n_series_bands).split("|") if b}
        parked = [c.strip() for c in str(r.parked_codes).split(";") if c.strip()]
        adds = set()
        for c in parked:
            b = band_for(c)
            if b in N_SERIES_BANDS:
                adds.add(SHORT[b])
        if r.nb == 1 and adds:
            cands = sorted({SHORT[x] for c in parked for x in quarantine_candidates(c)})
            safe = [c for c in cands if c in kept]
            rows.append({"pn": r.pn, "cat": r.pms_category or "(blank)", "kept": sorted(kept)[0],
                         "parked": ";".join(parked), "adds": sorted(adds), "cands": cands,
                         "safe_under": safe, "eur": r.eur_f})
    d = pd.DataFrame(rows)
    print("=" * 100)
    print("PART NUMBERS THAT LOOK SINGLE-BAND ONLY BECAUSE A QUARANTINED CODE WAS LEFT OUT")
    print("=" * 100)
    print(f"  affected part numbers : {len(d):,}")
    print(f"  billed euro on them   : EUR {d.eur.sum():,.2f}  (all markets, all years, corrected table)")
    print()
    print("  the rung the row would be placed on:")
    for k, v in d.kept.value_counts().items():
        print(f"      {k:6s} {v:3d} rows   EUR {d[d.kept == k].eur.sum():>14,.2f}")
    print()
    print("  NMR's two recorded candidate rungs:")
    for k, v in d.cands.map(lambda c: "+".join(c)).value_counts().items():
        print(f"      {k:14s} {v:3d} rows")
    print()
    both_bad = d[d.safe_under.map(len) == 0]
    one_bad = d[d.safe_under.map(len) == 1]
    print(f"  NOT single-band under EITHER NMR candidate : {len(both_bad):3d} rows"
          f"   EUR {both_bad.eur.sum():>14,.2f}")
    print(f"  single-band under ONE candidate only       : {len(one_bad):3d} rows"
          f"   EUR {one_bad.eur.sum():>14,.2f}")
    print()
    print("  the 'not single-band under either candidate' rows, by service family:")
    for k, v in both_bad.groupby("cat").eur.agg(["size", "sum"]).sort_values("sum", ascending=False).iterrows():
        print(f"      {k:24s} {int(v['size']):3d} rows   EUR {v['sum']:>14,.2f}")
    print()
    print("  all handled correctly by the corrected table? "
          "exclusivity_established on those rows:")
    print("      " + str(d.groupby("pn").size().pipe(lambda s: len(s)) and
                         ap[ap.k.isin(set(both_bad.pn))].exclusivity_established
                         .value_counts().to_dict()))
    print()
    print(f"  if NMR keeps its interim rung (no code moved) the scope's single-band count is 180;")
    print(f"  if the parked rung is dropped it is 230, of which {len(d)} rows depend on that drop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
