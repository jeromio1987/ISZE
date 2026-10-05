"""Launchers and receipts for the two pricing deliverables.

- writes sibling OPEN_*.cmd (CRLF) for the HTML and the workbook
- prints the QA screenshot inventory with wall-clock mtimes so the receipt can be
  checked against the artifact as it stands now
- removes the temporary probe scripts this session left behind

Run: python 02_dashboards/pricing/_build/_finalise_pricing_deliverables.py
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRICING = ISZE / "01_data" / "01_Pricing"
DASH = ISZE / "02_dashboards" / "pricing"
QA = DASH / "_qa"
BUILD = DASH / "_build"

HTML = DASH / "ISZE_Pricing_Revision_AIM_Source.html"
XLSX = PRICING / "Pricing_Revision_AIM_Source_Analysis.xlsx"

LAUNCHERS = [
    (HTML, DASH / "OPEN_Pricing_Revision_AIM_Source.cmd"),
    (XLSX, PRICING / "OPEN_Pricing_Revision_AIM_Source_Analysis.cmd"),
]

TIDY = ["_com_probe.ps1", "_tmp_make_big.py", "_tmp_make_variants.py",
        "_tmp_make_variants2.py", "_tmp_bisect.py", "_tmp_inspect_dom.py",
        "_tmp_patch_qa.py", "_tmp_patch_qa2.py", "_tmp_debug_select.py"]


def main() -> int:
    for target, cmd in LAUNCHERS:
        cmd.write_bytes(
            ("@echo off\r\n"
             f'start "" "%~dp0{target.name}"\r\n').encode("ascii"))
        print(f"launcher {cmd.name}  -> {target.name}  ({cmd.stat().st_size} bytes)")

    print("\nartifacts")
    for f in (HTML, XLSX):
        st = f.stat()
        print(f"  {f.name:52} {st.st_size/1024:9,.0f} KB   "
              f"{datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}")

    shots = sorted(QA.glob("*.png"))
    print(f"\nscreenshots for the receipt ({len(shots)})")
    for s in shots:
        print(f"  {s.name:34} {s.stat().st_size/1024:7,.0f} KB   "
              f"{datetime.fromtimestamp(s.stat().st_mtime):%H:%M:%S}")

    print("\ntidying temporary probes")
    for name in TIDY:
        p = BUILD / name
        if p.exists():
            p.unlink()
            print(f"  removed {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
