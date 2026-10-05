"""Check every AIM triple the classifier can emit against the live master vocabulary.

A triple that is not already a spine leaf would mean the classifier invented a label.
Nothing may be written to the master until this passes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classify import RULES  # noqa: E402

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")


def main() -> None:
    m = pd.read_csv(D / "aim_master_v2.csv", dtype=str, low_memory=False)
    m["l1"] = m["aim_l1"].fillna("").str.strip()
    m["l2"] = m["aim_l2"].fillna("").str.strip()
    m["l3"] = m["aim_l3"].fillna("").str.strip()
    live = {
        (a, b, c)
        for a, b, c in zip(m["l1"], m["l2"], m["l3"])
        if a and not a.lower().startswith("unknown")
    }
    live_l1 = {t[0] for t in live}
    live_l1l2 = {(t[0], t[1]) for t in live}
    live_l3_by_l1l2: dict[tuple[str, str], set[str]] = {}
    for a, b, c in live:
        live_l3_by_l1l2.setdefault((a, b), set()).add(c)

    exactly, l1l2_only, bad = [], [], []
    for phrase, l1, l2, l3 in RULES:
        if (l1, l2, l3) in live:
            exactly.append((phrase, l1, l2, l3))
        elif (l1, l2) in live_l1l2:
            l1l2_only.append((phrase, l1, l2, l3))
        else:
            bad.append((phrase, l1, l2, l3, l1 in live_l1))

    print(f"rules: {len(RULES)}")
    print(f"  triple already a live spine leaf : {len(exactly)}")
    print(f"  L1+L2 live, L3 needs aligning    : {len(l1l2_only)}")
    print(f"  L1/L2 not on the spine           : {len(bad)}")
    if l1l2_only:
        print("\n-- L3 to align --")
        for phrase, l1, l2, l3 in l1l2_only:
            print(f"  {phrase!r:34s} {l1} > {l2} > {l3!r}   live L3s: {sorted(live_l3_by_l1l2[(l1, l2)])}")
    if bad:
        print("\n-- not on the spine --")
        for phrase, l1, l2, l3, l1ok in bad:
            print(f"  {phrase!r:34s} {l1} > {l2} > {l3!r}   L1 on spine: {l1ok}")


if __name__ == "__main__":
    main()
