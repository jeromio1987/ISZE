#!/usr/bin/env python3
"""RETIRED 2026-09-24 - this generator no longer authors the band map and must not be run.

History, so a reader can see why it is here
-------------------------------------------
This was the ORIGINAL authoring generator for the one canonical series -> band mapping. It wrote
`03_analytics/Isuzu/prism/data/series_to_band.csv`, one row per vehicle code, from three files
that each held their own dictionary: the bander (`build_nseries_tonnage_bands.py`, dict `TABLE`),
the retired probe (`pn_ammo_probe_20260918/_tonnage_capable.py`, dict `SERIES_BAND`) and the
model-code builder (`build_model_code_to_tonnage.py`, a list of `add()` calls). It was written
because those three disagreed - the probe had `NKR -> 5.5t`, and the model-code table had `NMR`
on band 7.5 t while its own weight label on the same row read 5.5 t.

It deliberately left the two `NMR` rows open, and that is the reason it is now retired:

* it wrote `status = "pending_ruling"` for `NMR` and `NMR85`,
* it wrote the weight label `"5.5 t GVW (N50 / N55) - INTERIM, NOT SETTLED"` for `NMR`,
* it recorded both candidate bands in the `quarantine_candidates` column, and
* it appended a `QUARANTINED PENDING RULING:` sentence to those rows' evidence quote.

`NMR` was ruled on 2026-09-23: it sits on the 5.5 t band, scoped to the European N55 class, and
both rows now read `status = "resolved"` with an empty `quarantine_candidates`. Re-running this
script would silently revert that ruling and overwrite the authored map, so it refuses to run.

The map is hand-authored source now - edit the CSV to change a mapping. It is read through
`03_analytics/Isuzu/prism/modules/vehicle_bands.py` (`band_for`, `group_for`, `gvw_t_for`), and
nothing keeps its own copy of the series codes.

Run: python 01_data/91_build/_tmp_build_canonical_band_map_20260923.py  -> prints one line, exits 2.
"""
from __future__ import annotations

from typing import NoReturn

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
PRISM = ROOT + r"\03_analytics\Isuzu\prism"

# Output path, unchanged. This script no longer writes it, so it stays here only so the one path
# it used to own remains visible and is not silently redirected somewhere else.
OUT = PRISM + r"\data\series_to_band.csv"

# The map it used to author, the module that reads it, and the three files it used to copy from.
# Repo-relative, matching how `verification_fixtures.yaml` names a builder.
CANONICAL_MAP = "03_analytics/Isuzu/prism/data/series_to_band.csv"
READER = "03_analytics/Isuzu/prism/modules/vehicle_bands.py"

MESSAGE = (
    "RETIRED 2026-09-24 - this generator is dead and writes nothing. Running it would revert the "
    "settled NMR ruling and overwrite the hand-authored map "
    f"{CANONICAL_MAP}. The map is hand-authored now and is read through {READER}."
)


def retired(*_args, **_kwargs) -> NoReturn:
    """Print the one line and stop with a non-zero exit, so no caller reads success."""
    print(MESSAGE)
    raise SystemExit(2)


def main() -> NoReturn:
    """Retired with the authoring pass it ran. Kept as a name so an old entry point fails loudly."""
    retired()


# ---------------------------------------------------------------------------------------------
# Everything below is deliberately removed: the loaders over the bander table, the family groups,
# the VIN register and the model-code table, and the `csv.DictWriter` block that wrote OUT. All of
# it existed to produce the `pending_ruling` state the NMR ruling has since replaced, so keeping
# any of it would keep a way to write the map again. The map is written by hand now.
# ---------------------------------------------------------------------------------------------


if __name__ == "__main__":
    retired()
