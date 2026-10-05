"""Batch 2 result, and the light-vehicle versus truck split, computed the same way on both batches.

The classification is by the EPC's own vehicle-family label, not by inference:
  * light-vehicle only  -> every family is a PASSENGER VEHICLE family
  * touches a truck or bus -> at least one family is TRUCKS / BUSES / COMPONENT / INDUSTRIAL ENGINE
  * no family returned  -> the read returned no rows (reported separately, never folded in)
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")


def classify(rows: list[dict]) -> dict:
    lv, truck, none, notfound, err = [], [], [], [], []
    for r in rows:
        if r.get("error"):
            err.append(r["pn"])
        fams = [f.upper() for f in (r.get("families") or [])]
        if not fams:
            if not r.get("found"):
                notfound.append(r["pn"])
            else:
                none.append(r["pn"])
            continue
        light = any("PASSENGER" in f for f in fams)
        heavy = any(k in f for f in fams
                    for k in ("TRUCK", "BUS", "COMPONENT", "INDUSTRIAL", "MARINE"))
        if light and not heavy:
            lv.append(r["pn"])
        elif heavy:
            truck.append(r["pn"])
        else:
            none.append(r["pn"])
    return {"rows": len(rows), "light_vehicle_only": len(lv), "touches_truck_or_bus": len(truck),
            "read_returned_no_rows": len(none), "not_found_total_zero": len(notfound),
            "errors": len(err), "error_pns": err, "no_rows_pns": none}


def main() -> int:
    b1 = json.loads((DER / "epc_decode_batch1_20260919.json").read_text(encoding="utf-8"))
    b2 = json.loads((DER / "epc_decode_batch2_20260919.json").read_text(encoding="utf-8"))

    c1, c2 = classify(b1), classify(b2)
    print("=" * 96)
    print("LIGHT-VEHICLE vs TRUCK SPLIT — same method on both batches")
    print("=" * 96)
    for tag, c in (("batch 1", c1), ("batch 2", c2)):
        print(f"  {tag}: {c['rows']} part numbers | light-vehicle only {c['light_vehicle_only']} | "
              f"touches a truck or bus {c['touches_truck_or_bus']} | "
              f"no family returned {c['read_returned_no_rows']} | "
              f"not found {c['not_found_total_zero']} | errors {c['errors']}")

    tot_rows = c1["rows"] + c2["rows"]
    tot_lv = c1["light_vehicle_only"] + c2["light_vehicle_only"]
    tot_tr = c1["touches_truck_or_bus"] + c2["touches_truck_or_bus"]
    print()
    print(f"  combined: {tot_rows} part numbers | light-vehicle only {tot_lv} "
          f"({100*tot_lv/tot_rows:.1f}%) | touches a truck or bus {tot_tr} "
          f"({100*tot_tr/tot_rows:.1f}%)")

    print()
    print("=" * 96)
    print("BATCH 2 — families seen, and the boundaries worth naming")
    print("=" * 96)
    fams = Counter(f for r in b2 for f in (r.get("families") or []))
    for f, n in fams.most_common():
        print(f"  {n:4d}  {f}")

    # a part number that touches both a truck and a light vehicle is the interesting middle
    both = [r["pn"] for r in b2
            if any("PASSENGER" in f.upper() for f in (r.get("families") or []))
            and any(("TRUCK" in f.upper() or "BUS" in f.upper())
                    for f in (r.get("families") or []))]
    print(f"\n  part numbers touching BOTH a light vehicle and a truck/bus: {len(both)}")
    print(f"  {both[:15]}")

    print()
    print("=" * 96)
    print("BATCH 2 — errors and reads that returned no rows (reported, not folded in)")
    print("=" * 96)
    print(f"  errors ({c2['errors']}): {c2['error_pns']}")
    print(f"  found but read returned 0 rows ({c2['read_returned_no_rows']}): {c2['no_rows_pns']}")
    print(f"  search returned total=0 ({c2['not_found_total_zero']}): {c2['not_found_total_zero']} pns")

    print()
    print("=" * 96)
    print("BATCH 2 — euro covered (from the batch worklist)")
    print("=" * 96)
    wl = DER / "epc_decode_worklist.csv"
    if wl.is_file():
        import pandas as pd
        w = pd.read_csv(wl)
        d = w[w.batch == 2]
        print(f"  rows {len(d)} | euro EUR {d.eur_all.sum():,.0f} | "
              f"LN-first {int(d.single_year.sum())} single-year part numbers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
