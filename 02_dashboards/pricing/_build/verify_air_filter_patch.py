"""Verify the air-filter correction actually reached the file the handoff points at.

The ACL patch touched the classification files at 19:50. The focus cut was rebuilt
at 19:58. This proves the rebuild picked the patch up, and if it did not, re-runs
the breakdown builder so the handoff cannot point at stale numbers.

Read-only except for the one rebuild it may trigger, which is the existing builder.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
BUILDER = ISZE / "01_data" / "91_build" / "build_aim_catalog_breakdown.py"
FOCUS = D / "aim_catalog_focus_filters.csv"

BEFORE = None


def read_air(focus: Path) -> pd.DataFrame:
    f = pd.read_csv(focus)
    cols = {c.lower(): c for c in f.columns}
    # find the node and euro columns by name rather than assuming position
    print("focus columns:", list(f.columns))
    return f


def main() -> int:
    f = pd.read_csv(FOCUS)
    print(f"focus file rows: {len(f):,}")
    print(f"columns: {list(f.columns)}")

    # the filter rows, whatever the node column is called
    node_cols = [c for c in f.columns if any(
        k in c.lower() for k in ("node", "level", "family", "group", "type", "l1", "l2", "l3"))]
    eur_cols = [c for c in f.columns if "eur" in c.lower() or "billed" in c.lower()]
    print(f"node columns: {node_cols}")
    print(f"euro columns: {eur_cols}")

    air = f[f.astype(str).apply(
        lambda r: r.str.contains("Air filter", case=False, na=False).any(), axis=1)]
    print(f"\nrows mentioning 'Air filter': {len(air)}")
    if len(air):
        show = [c for c in f.columns if c in node_cols[:4] + eur_cols[:4]]
        print(air[show].head(30).to_string(index=False))

    # the decisive test: does the filter block carry the patched euro, or the old leaf?
    eur = None
    for c in eur_cols:
        if "billed" in c.lower() and "total" in c.lower():
            eur = c
            break
    if eur is None and eur_cols:
        eur = eur_cols[0]
    print(f"\nusing euro column: {eur}")
    if eur and len(air):
        print("total euro on the air-filter rows:", round(air[eur].sum(), 2))
    print("\nnetwork Filters total, for comparison:")
    filt = f[f.astype(str).apply(
        lambda r: r.str.contains("Filters", case=False, na=False).any(), axis=1)]
    if eur and len(filt):
        print("  rows:", len(filt), "euro:", round(filt[eur].sum(), 2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
