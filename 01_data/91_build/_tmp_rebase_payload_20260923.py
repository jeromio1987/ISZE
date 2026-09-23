"""Read the page's embedded payload and report the blocks the re-base touches.

Reports, from the built HTML rather than from the builder:
  * whether `degree` exists and which service families it carries
  * the two comparable families' verdicts on both clocks
  * whether the literal '?' string is rendered, and where

Also reports, from the source file, what `degree` would contain now.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
BEFORE = (ROOT / "02_dashboards" / "sales" / "_qa_family_evolution"
          / "before_rebase_20260923" / "ISZE_PMS_Family_Evolution_v2.before_rebase_20260923.html")


def payload(path: Path) -> dict:
    h = path.read_text(encoding="utf-8")
    m = re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>', h, re.S)
    return json.loads(m.group(1)) if m else {}


def main() -> int:
    for tag, path in (("LIVE PAGE (pre-rebuild)", HTML), ("VERIFIER BEFORE-IMAGE", BEFORE)):
        print("=" * 98)
        print(tag, "|", path.name, "|", path.stat().st_size, "bytes")
        print("=" * 98)
        if not path.is_file():
            print("   (absent)")
            continue
        d = payload(path)
        print(f"   payload keys      : {len(d)}")
        deg = d.get("degree")
        print(f"   degree present    : {deg is not None}")
        if isinstance(deg, dict):
            print(f"   degree families   : {sorted(deg)}")
            for c in sorted(deg):
                g = deg[c]
                print(f"       {c:24s} pns {g.get('pns')} singleBand {g.get('singleBand')}"
                      f" multiBand {g.get('multiBand')} placeable {g.get('placeable')}")
        for clock in ("CY", "FY"):
            comp = (d.get("comparability") or {}).get(clock) or {}
            print(f"   comparability {clock}:")
            for c in ("air_filter", "brake_rotor", "brake_shoe", "oil_filter"):
                v = comp.get(c)
                if v is None:
                    print(f"       {c:14s} (absent)")
                else:
                    print(f"       {c:14s} verdict {v.get('verdict'):8s} pns {v.get('pns')}"
                          f" singleBandPns {v.get('singleBandPns')} shareShared {v.get('shareShared')}"
                          f" euro {v.get('euro')}")
                    if v.get("why"):
                        print(f"           why: {v['why']}")
        print()
        print("   '?' occurrences in the built HTML (literal question mark in text):")
        h = path.read_text(encoding="utf-8")
        for m in re.finditer(r"[^<>\n]{0,90}\?[^<>\n]{0,60}", h):
            seg = m.group(0)
            if "carry no vehicle reference" in seg or "unattributed" in seg:
                print("       ...", seg.strip()[:160])
        print()

    print("=" * 98)
    print("WHAT `degree` WOULD CONTAIN FROM THE FILE ON DISK NOW")
    print("=" * 98)
    cap = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", low_memory=False)
    print(f"   rows {len(cap):,}   blank category rows {int(cap.category.isna().sum())}")
    for cat, g in cap.groupby("category"):
        print(f"       {str(cat):24s} pns {len(g):3d} singleBand "
              f"{int((g.n_bands == 1).sum()):3d} placeable {bool((g.n_bands == 1).any())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
