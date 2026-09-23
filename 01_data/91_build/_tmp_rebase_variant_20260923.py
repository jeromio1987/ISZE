"""Which three-rung rule produces the movement the brief describes?

Variant A - parked codes kept out of the band list (the corrected table's `n_series_bands`).
Variant B - parked codes counted on their interim band (what the frozen file effectively did).

Prints the single-band count and the per-family placeable verdict for both, so the rule that
produces "230" and the three family flips is identified rather than assumed.
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


def view(frame: pd.DataFrame, catcol: str, tag: str) -> dict:
    frame = frame.copy()
    frame["nb"] = frame.band_list.map(lambda v: len([b for b in str(v).split("|") if b]))
    single = frame[frame.nb == 1]
    print(f"{tag}")
    print(f"   rows {len(frame):,}   single-band {len(single):,}   "
          f"multi-band {int((frame.nb > 1).sum()):,}")
    deg = {}
    for cat, g in frame.groupby(catcol):
        if not str(cat).strip():
            continue
        deg[cat] = {"pns": int(len(g)), "single": int((g.nb == 1).sum()),
                    "placeable": bool((g.nb == 1).any())}
    for c in sorted(deg):
        d = deg[c]
        print(f"      {c:24s} pns {d['pns']:4d} single {d['single']:4d} placeable {d['placeable']}")
    print()
    return {"single": set(single.pn), "degree": deg}


def main() -> int:
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    ap["k"] = ap.pn.map(n)

    # ── Variant A: the corrected table's own three-rung answer, parked codes kept out
    va = ap[ap.n_series_bands != ""].copy()
    va["band_list"] = va.n_series_bands
    A = view(va, "pms_category", "VARIANT A - parked codes kept out (the corrected table's own read)")

    # ── Variant B: parked codes also count their interim band
    rows = []
    for r in ap.itertuples():
        bands = {b for b in str(r.n_series_bands).split("|") if b}
        for c in str(r.parked_codes).split(";"):
            c = c.strip()
            if not c:
                continue
            b = band_for(c)
            if b not in (UNRESOLVED, NOT_IN_SCOPE) and b in N_SERIES_BANDS:
                bands.add(b)
        if bands:
            rows.append({"pn": r.pn, "pms_category": r.pms_category,
                         "band_list": "|".join(sorted(bands))})
    vb = pd.DataFrame(rows)
    B = view(vb, "pms_category", "VARIANT B - parked codes counted on their interim band")

    print("=" * 96)
    print("WHAT DIFFERS BETWEEN THE TWO")
    print("=" * 96)
    print(f"  single-band part numbers   A {len(A['single']):,}   B {len(B['single']):,}")
    flips = sorted({c for c in set(A["degree"]) | set(B["degree"])
                    if A["degree"].get(c, {}).get("placeable")
                    != B["degree"].get(c, {}).get("placeable")})
    print(f"  families whose placeable verdict differs: {flips or 'none'}")
    target = {c for c, d in A["degree"].items() if d["placeable"]}
    for c in ("air_filter", "brake_rotor", "brake_shoe"):
        print(f"    {c:16s} A placeable {A['degree'].get(c, {}).get('placeable')}   "
              f"B placeable {B['degree'].get(c, {}).get('placeable')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
