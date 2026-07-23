"""DEPRECATED — do not use for planning. See 91_build/GPS_FILE_LINEAGE.md.

ISZE_GPS_v6.xlsx was a mistaken fork of ISZE_GPS_Calculator_v9.xlsx.
Planning updates belong in 04_tools/build_gps_v5.py → ISZE_GPS_v5.xlsx.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MSG = """
ERROR: build_gps_v6.py is deprecated (2026-07-03).

  Planning workbook:  04_tools/build_gps_v5.py  →  01_data/ISZE_GPS_v5.xlsx
  Stretch proposal:   91_build/build_gps_kickback_proposal.py
  Lineage / rules:    01_data/91_build/GPS_FILE_LINEAGE.md

v6 cloned the v9 calculator — that is the wrong lineage for network GPS planning.
"""


def main() -> None:
    print(MSG.strip())
    raise SystemExit(1)


if __name__ == "__main__":
    main()
