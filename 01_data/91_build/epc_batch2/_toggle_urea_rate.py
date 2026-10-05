"""Flip the urea rate in pms_engine.py between the sourced value and 1.0, for the controlled pair.

usage: python _toggle_urea_rate.py sourced|baseline
"""
from __future__ import annotations

import sys
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\modules\pms_engine.py")
SOURCED_CV = 'cv_rate = factor_overrides.get("urea_filter", 0.2)'
BASELINE_CV = 'cv_rate = 1.0  # BASELINE RUN ONLY — restore to the sourced 0.2'
SOURCED_F = 'f_rate = factor_overrides.get("urea_filter", UREA_FILTER_F_SERIES)'
BASELINE_F = 'f_rate = 1.0  # BASELINE RUN ONLY — restore to the sourced UREA_FILTER_F_SERIES'


def main(mode: str) -> int:
    t = P.read_text(encoding="utf-8")
    if mode == "baseline":
        t = t.replace(SOURCED_CV, BASELINE_CV).replace(SOURCED_F, BASELINE_F)
    elif mode == "sourced":
        t = t.replace(BASELINE_CV, SOURCED_CV).replace(BASELINE_F, SOURCED_F)
    else:
        raise SystemExit("mode must be 'sourced' or 'baseline'")
    P.write_text(t, encoding="utf-8")
    print("mode:", mode)
    for line in t.splitlines():
        if "cv_rate =" in line or "f_rate =" in line:
            print("   ", line.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
