"""RETIRED 2026-09-23 - this probe no longer computes a band and must not be run.

Its own series -> band dictionary is deleted. That dictionary had `NKR` on the 5.5 t band
against every sourced table, which is the error that made the 5.5 t band look populated when
almost all of the euro underneath it was really 3.5 t money.

The one authored mapping is now `03_analytics/Isuzu/prism/data/series_to_band.csv`, read
through `03_analytics/Isuzu/prism/modules/vehicle_bands.py`. Nothing keeps its own copy.
"""
# Quoted once, on the spot where the error used to live, so the reason for the retirement sits
# beside the thing that caused it:
#
#     SERIES_BAND = {"NLR": "3.5t", "NMR": "5.5t", "NPR": "7.5t", "NQR": "7.5t",
#                    "NNR": "7.5t", "NKR": "5.5t", "NHR": "3.5t"}
#                                   ^^^^^^^^^^^^^^^^^ wrong - NKR is the older N35 designation
#                                   and is 3.5 t, per the JP VIN register and every sourced table.
#
# One rule from the old file still stands: series were matched on ANCHORED tokens, never as a
# substring, because 'F*' also matched 'TF*' (the D-Max pickup) and inflated a heavy-truck
# figure by EUR 1.8M. The replacement builder keeps that anchoring rule.
from __future__ import annotations

from typing import NoReturn

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"

# Where the one authored mapping lives, the module that reads it, and the builder that replaced
# this probe. Repo-relative, matching how `verification_fixtures.yaml` names a builder.
CANONICAL_MAP = "03_analytics/Isuzu/prism/data/series_to_band.csv"
READER = "03_analytics/Isuzu/prism/modules/vehicle_bands.py"
REPLACEMENT = "01_data/91_build/pn_ammo_probe_20260918/_vehicle_band_applicability.py"

# Output paths, unchanged. This file no longer writes either of them - both are written by
# REPLACEMENT now - so they stay here only so the two paths this probe used to own remain
# visible and are not silently redirected somewhere else.
OUT_CATEGORIES = DER + r"\tonnage_capable_categories.csv"
OUT_PART_NUMBERS = DER + r"\tonnage_capable_part_numbers.csv"

MESSAGE = (
    "RETIRED 2026-09-23 - this probe is dead and maps nothing. Use "
    f"{REPLACEMENT}, which reads the authored map {CANONICAL_MAP} through {READER}."
)


def retired(*_args, **_kwargs) -> NoReturn:
    """Print the one line and stop with a non-zero exit, so no caller reads success."""
    print(MESSAGE)
    raise SystemExit(2)


def bands_in(text: str) -> NoReturn:
    """Retired with the dictionary it read. Kept as a name so an old import fails loudly."""
    retired(text)


# ---------------------------------------------------------------------------------------------
# Everything below is deliberately removed: the category table, the cross-reference and EPC
# evidence routes, the billing weighting and the two CSV writes. All of it fed off the deleted
# dictionary, so keeping any of it would keep the wrong `NKR` answer reachable. Both files this
# probe used to write are written today by REPLACEMENT, on the canonical map.
# ---------------------------------------------------------------------------------------------


if __name__ == "__main__":
    retired()
