"""Family splittability from the page's own payloads, and whether the repair moves it.

Reads the before-image payload and the live (rebuilt) payload, and reports per clock which families
the page will split by tonnage and which it refuses.

Then asks the material question: the repair changed four rows from one band to two. Does any family
verdict or count in the live payload now disagree with the repaired file? Nothing is written and the
page is not touched.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
BEFORE = (ROOT / "02_dashboards" / "sales" / "_qa_family_evolution"
          / "before_rebase_20260923" / "ISZE_PMS_Family_Evolution_v2.before_rebase_20260923.html")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def payload(p: Path) -> dict:
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                p.read_text(encoding="utf-8"), re.S).group(1))


def main() -> int:
    before, after = payload(BEFORE), payload(HTML)
    labels = {c["key"]: c["label"] for c in after.get("cats", [])}
    for clock in ("CY", "FY"):
        print("=" * 100)
        print(f"{clock} CLOCK - family splittability by tonnage, from the page payload")
        print("=" * 100)
        for tag, d in (("BEFORE the re-base", before), ("AFTER  the re-base", after)):
            comp = (d.get("comparability") or {}).get(clock) or {}
            live = {k: v for k, v in comp.items() if v.get("verdict") != "none"}
            split = sorted(k for k, v in live.items() if v.get("verdict") in ("ok", "thin"))
            refused = sorted(k for k, v in live.items() if v.get("verdict") == "pooled")
            print(f"  {tag}: {len(live)} families carry euro | SPLIT {len(split)} | "
                  f"REFUSED {len(refused)}")
            for k in sorted(live):
                v = live[k]
                mark = "SPLIT  " if v.get("verdict") in ("ok", "thin") else "refused"
                print(f"      {mark} {labels.get(k, k):24s} {v.get('verdict'):7s} "
                      f"singleBandPns {v.get('singleBandPns'):>3}")
        print()

    print("=" * 100)
    print("DOES THE REPAIR CHANGE ANY OF THIS?  (the page reads the file that was repaired)")
    print("=" * 100)
    leg = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    leg["k"] = leg.pn.map(n)
    deg_now = {}
    for cat, g in leg.groupby("category"):
        if not str(cat).strip():
            continue
        deg_now[cat] = {"pns": int(len(g)),
                        "singleBand": int((g.n_bands.astype(int) == 1).sum()),
                        "placeable": bool((g.n_bands.astype(int) == 1).any())}
    pdeg = after.get("degree") or {}
    print(f"  families in the payload's degree block : {len(pdeg)}")
    print(f"  families in the repaired file's degree : {len(deg_now)}")
    moved = []
    for cat in sorted(set(pdeg) | set(deg_now)):
        a, b = pdeg.get(cat), deg_now.get(cat)
        if a is None or b is None:
            moved.append((cat, a, b, "family present in only one"))
            continue
        for f in ("pns", "singleBand", "placeable"):
            if a.get(f) != b.get(f):
                moved.append((cat, f"{f}={a.get(f)}", f"{f}={b.get(f)}", "value differs"))
    print(f"  differences between the page's payload and the repaired file: {len(moved)}")
    for cat, a, b, why in moved:
        print(f"      {cat:24s} payload {str(a):28s} file {str(b):28s} {why}")
    print()
    print("  the four rows the repair moved from one band to two, and their families:")
    for k in ("5876103260", "5878320470", "8983320620", "8983615742"):
        r = leg[leg.k == k]
        if len(r):
            print(f"      {k:>12s} cat {r.category.iloc[0]!r:16s} bands {r.bands.iloc[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
