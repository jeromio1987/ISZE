"""Wire the AdBlue (urea) filter interval into the PMS demand model, per vehicle class.

The interval is a property of the model, not the market:
  N-series 4HK1 (N75)          200,000 km   Rene Paul, GIDSS N_MY24 p4, row "AdBlue filter"
  F-series 4HK1-TCH             80,000 km   Rene Paul, GIDSS F_MY24 p1, row "AdBlue filter
                                             (4HK1-TCH engine model)"
  D-Max / LCV                   not in sources  -> keeps the current factor

The pipeline's convention is one service visit per 40,000 km for N75 (pms_capture_assumptions.yaml,
n75_parc_assumptions.service_visit_interval_km) and one per 20,000 km for the LCV bucket
(BUCKET_SERVICES_PER_YEAR.lcv, D-Max owner's handbook), so:

  urea_filter factor = visit interval / part interval
    N-series (cv_std):  40,000 / 200,000 = 0.20
    F-series:           30,000 /  80,000 = 0.375   (30,000 km is the provisional F-series visit
                                                    interval already in BUCKET_SERVICES_PER_YEAR)
    LCV:                unchanged (no sourced AdBlue interval for D-Max)

Idempotent: it rewrites the two known lines from any prior state.

usage: python _apply_urea_factor.py [--revert]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
CFG = PRISM / "modules" / "pms_capture_config.py"
YAML = PRISM / "data" / "pms_capture_assumptions.yaml"

YAML_LINE = (
    "  urea_filter: 1.0   # AdBlue filter. 1.0 = one per service visit, which was WRONG: Rene "
    "Paul's GIDSS schedules give the filter at\n"
    "                     #   200,000 km on N-series (N_MY24 p4, NPR75 / 4HK1) and 80,000 km on "
    "F-series 4HK1-TCH (F_MY24 p1). One\n"
    "                     #   visit covers 40,000 km on N75, so the N-series share of a visit is "
    "0.20 — not 1.0. The network\n"
    "                     #   scalar stays 1.0 because this file cannot express a vehicle class; "
    "modules/pms_capture_config.py\n"
    "                     #   splits it per class. See _apply_urea_factor.py.\n"
    "  urea_filter_cv_std: 0.2     # 40,000 km visit / 200,000 km AdBlue filter (GIDSS N_MY24 p4)\n"
    "  urea_filter_f_series: 0.375 # 30,000 km visit / 80,000 km AdBlue filter, 4HK1-TCH "
    "(GIDSS F_MY24 p1)\n"
)

PY_BLOCK = '''
# ─── AdBlue / urea filter interval, per vehicle class (2026-09-19) ───────────────
# The pipeline carried urea_filter = 1.0 — one AdBlue filter per service visit, the same rate as
# an oil filter. That is wrong by the sources, which give the interval, not "every visit":
#
#   N-series, NPR75 / 4HK1      200,000 km   Rene Paul, GIDSS N_MY24 p4, row "AdBlue filter"
#                                            (the row above "PM sensor"; the F-series sheet names
#                                            the equivalent row "AdBlue filter (4HK1-TCH engine
#                                            model)"). It is the filter element, not the tank.
#   F-series, 4HK1-TCH           80,000 km   Rene Paul, GIDSS F_MY24 p1
#   D-Max / LCV                  not in the sources -> factor unchanged
#
# One visit covers 40,000 km for the N75 (pms_capture_assumptions.yaml,
# n75_parc_assumptions.service_visit_interval_km) and 30,000 km for the F-series
# (BUCKET_SERVICES_PER_YEAR.f_series, provisional), so the share of a visit that is an AdBlue
# filter replacement is 40,000/200,000 = 0.20 on N-series and 30,000/80,000 = 0.375 on F-series.
#
# A single scalar cannot express this: the two series differ by 1.875x, so the class split has to
# happen where the classes are known. This does NOT re-base any mileage assumption.
UREA_FILTER_CV_STD = 40_000 / 200_000    # 0.20 — N-series 4HK1, GIDSS N_MY24 p4
UREA_FILTER_F_SERIES = 30_000 / 80_000   # 0.375 — F-series 4HK1-TCH, GIDSS F_MY24 p1
'''

APPLIED_MARK = "expected[cat] = _urea_split(cat, base_cv, base_f, base_l, factor_overrides)"


def apply_yaml(revert: bool) -> None:
    text = YAML.read_text(encoding="utf-8")
    # strip any previously applied block
    text = re.sub(
        r"  urea_filter: 1\.0.*?\n(?=  blower_filter)",
        "",
        text,
        flags=re.S,
    )
    if revert:
        text = text.replace(
            "  air_filter: 0.5",
            "  urea_filter: 1.0\n  air_filter: 0.5",
            1,
        )
    else:
        text = text.replace("  air_filter: 0.5", YAML_LINE + "  air_filter: 0.5", 1)
    YAML.write_text(text, encoding="utf-8")
    print("yaml:", "reverted" if revert else "urea factors written")


def apply_py(revert: bool) -> None:
    text = CFG.read_text(encoding="utf-8")
    text = re.sub(r"\n# ─── AdBlue / urea filter interval.*?UREA_FILTER_F_SERIES = .*?\n", "\n", text, flags=re.S)
    text = text.replace("    if " + APPLIED_MARK + ":\n        pass\n", "")

    if revert:
        text = re.sub(
            r"    for cat, fac in all_factors\.items\(\):\n.*?\n    return expected\n",
            "    for cat, fac in all_factors.items():\n"
            "        fac = factor_overrides.get(cat, fac)\n"
            "        fac_lcv = LCV_BUCKET_FACTOR_OVERRIDES.get(cat, fac)\n"
            "        expected[cat] = {\"qty\": base_cv * fac + base_f * fac + base_l * fac_lcv}\n"
            "    return expected\n",
            text,
            flags=re.S,
        )
        CFG.write_text(text, encoding="utf-8")
        print("py: reverted")
        return

    # insert the constants before the UIO bucket loader
    anchor = "_UIO_BUCKET_PATH = "
    text = text.replace(anchor, PY_BLOCK.lstrip("\n") + "\n" + anchor, 1)

    # rewrite the item loop so urea is split by class
    old_loop = re.search(
        r"    for cat, fac in all_factors\.items\(\):\n"
        r"        fac = factor_overrides\.get\(cat, fac\)\n"
        r"        fac_lcv = LCV_BUCKET_FACTOR_OVERRIDES\.get\(cat, fac\)\n"
        r"        expected\[cat\] = \{\"qty\": base_cv \* fac \+ base_f \* fac \+ base_l \* fac_lcv\}\n",
        text,
    )
    if not old_loop:
        sys.exit("could not find the expected-demand loop in pms_capture_config.py")

    new_loop = (
        "    def _urea_split(cat, bcv, bf, bl, overrides):\n"
        "        \"\"\"AdBlue filter only: different interval per vehicle class (2026-09-19).\"\"\"\n"
        "        if cat != \"urea_filter\":\n"
        "            fac = overrides.get(cat, all_factors.get(cat, 1.0))\n"
        "            return bcv * fac + bf * fac + bl * LCV_BUCKET_FACTOR_OVERRIDES.get(cat, fac)\n"
        "        return bcv * UREA_FILTER_CV_STD + bf * UREA_FILTER_F_SERIES + bl * 1.0\n"
        "\n"
        "    for cat, fac in all_factors.items():\n"
        "        if " + APPLIED_MARK + ":\n"
        "            pass\n"
        "        else:\n"
        "            expected[cat] = {\"qty\": _urea_split(cat, base_cv, base_f, base_l,\n"
        "                                                 factor_overrides)}\n"
    )
    # the `if <call>:` form does not work; assign first
    new_loop = new_loop.replace(
        "        if " + APPLIED_MARK + ":\n        pass\n        else:\n",
        "",
    )
    new_loop = (
        "    def _urea_split(cat, bcv, bf, bl, overrides):\n"
        "        \"\"\"AdBlue filter only: the interval differs by vehicle class (2026-09-19).\"\"\"\n"
        "        if cat != \"urea_filter\":\n"
        "            fac = overrides.get(cat, all_factors.get(cat, 1.0))\n"
        "            return bcv * fac + bf * fac + bl * LCV_BUCKET_FACTOR_OVERRIDES.get(cat, fac)\n"
        "        return bcv * UREA_FILTER_CV_STD + bf * UREA_FILTER_F_SERIES + bl * 1.0\n"
        "\n"
        "    for cat, fac in all_factors.items():\n"
        "        expected[cat] = {\"qty\": _urea_split(cat, base_cv, base_f, base_l,\n"
        "                                             factor_overrides)}\n"
    )
    text = text[: old_loop.start()] + new_loop + text[old_loop.end():]
    CFG.write_text(text, encoding="utf-8")
    print("py: urea split wired")


if __name__ == "__main__":
    rev = "--revert" in sys.argv
    apply_yaml(rev)
    apply_py(rev)
