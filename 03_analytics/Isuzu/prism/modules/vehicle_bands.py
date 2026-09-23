"""The ONE place a vehicle code is turned into a band, a group and a GVW.

There is a single authored source: `03_analytics/Isuzu/prism/data/series_to_band.csv`,
one row per vehicle code. Edit that CSV to change a mapping. Nothing downstream keeps its
own dictionary of NMR / NLR / NPR / TFR / FRR.

Why it is a module and not a convention: before 2026-09-23 three files each held their own
series -> band dictionary and they disagreed - the retired probe had `NKR` at 5.5 t, and the
model-code table had `NMR` on the 7.5 t band while its own weight label on the same row read
5.5 t. A reader could get a different weight for the same truck depending on which file they
opened.

Vocabulary
----------
`vehicle_group` is what kind of vehicle a code names: an N-series truck, a D-Max pickup/SUV
(`light_vehicle`), a heavy F&G / C&E truck, or something outside the four shipped bands.
`tonnage_band` is the rung of the weight ladder. The two are separate on purpose: a D-Max is
a vehicle we model, but it is not a rung on the truck tonnage ladder, so it must never be
written as one.

Two codes are deliberately not settled and are marked `pending_ruling`:
`NMR` (5.5 t or 7.5 t - evidence note in `01_data/90_INBOX/`) and nothing else. The interim
band is whatever the shipped pipeline already used, so a build does not move a number before
the ruling. `band_for()` returns it; `is_pending_ruling()` tells a caller that it is interim.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
MAP_CSV = DATA / "series_to_band.csv"

# ── the four bands the workspace ships, in the order the pages read them ────────────────────
BAND_LCV = "LCV_D-Max"
BAND_N35 = "3.5t_N35"
BAND_N50 = "5.5t_N50_N55"
BAND_N75 = "7.5t_N50_N62_N75"
BAND_F = "F_series_MD_heavy"

BAND_ORDER = [BAND_LCV, BAND_N35, BAND_N75, BAND_F]
BAND_LABEL = {
    BAND_LCV: "LCV / D-Max",
    BAND_N35: "3.5 t (N35 Grafter)",
    BAND_N50: "5.5 t (N50 / N55)",
    BAND_N75: "7.5 t (N75 / N50 / N62)",
    BAND_F: "F-series / MD (heavy)",
}
# The three rungs of the truck tonnage ladder. The D-Max class is NOT one of them.
N_SERIES_BANDS = [BAND_N35, BAND_N50, BAND_N75]

GROUP_N_SERIES = "n_series_truck"
GROUP_LIGHT = "light_vehicle"
GROUP_HEAVY = "heavy_truck"
GROUP_OUT_OF_SCOPE = "out_of_scope"
GROUP_UNRESOLVED = "unresolved"

GROUP_LABEL = {
    GROUP_N_SERIES: "N-series truck",
    GROUP_LIGHT: "Light vehicle (D-Max pickup and SUV)",
    GROUP_HEAVY: "Heavy truck (F-series and C&E)",
    GROUP_OUT_OF_SCOPE: "Outside the four vehicle bands",
    GROUP_UNRESOLVED: "No vehicle named by any source",
}

BAND_TO_GROUP = {
    BAND_LCV: GROUP_LIGHT,
    BAND_N35: GROUP_N_SERIES,
    BAND_N50: GROUP_N_SERIES,
    BAND_N75: GROUP_N_SERIES,
    BAND_F: GROUP_HEAVY,
}

UNRESOLVED = "unresolved"
NOT_IN_SCOPE = "not_in_scope"
PENDING_RULING = "pending_ruling"


@lru_cache(maxsize=1)
def load_map() -> dict[str, dict[str, str]]:
    """{code: row}. Read once per process."""
    with open(MAP_CSV, encoding="utf-8-sig", newline="") as fh:
        return {(r["code"] or "").strip().upper(): r for r in csv.DictReader(fh)}


def _row(code: str) -> dict[str, str] | None:
    return load_map().get(str(code or "").strip().upper())


def band_for(code: str) -> str:
    """The band this code sits on, or the sentinel `unresolved`."""
    r = _row(code)
    if not r:
        return UNRESOLVED
    b = (r.get("tonnage_band") or "").strip()
    return b or UNRESOLVED


def group_for(code: str) -> str:
    """What kind of vehicle the code names."""
    r = _row(code)
    if not r:
        return GROUP_UNRESOLVED
    return (r.get("vehicle_group") or "").strip() or GROUP_UNRESOLVED


def gvw_t_for(code: str) -> float | None:
    """The nominal GVW in tonnes, or None where no source states one.

    None is a real answer and must stay None: filling it would invent a weight. The numeric
    value is the code's own, not its band's, because a band can span two weights (NNR is 6.5 t
    and NPR 7.5 t, and both are on the 7.5 t band).
    """
    r = _row(code)
    if not r:
        return None
    v = (r.get("gvw_t") or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def is_pending_ruling(code: str) -> bool:
    r = _row(code)
    return bool(r) and (r.get("status") or "").strip() == PENDING_RULING


def pending_ruling_codes() -> list[str]:
    return [c for c, r in load_map().items() if (r.get("status") or "").strip() == PENDING_RULING]


def quarantine_candidates(code: str) -> list[str]:
    """The bands a pending-ruling code could sit on. Empty for a settled code."""
    r = _row(code)
    if not r:
        return []
    return [b for b in (r.get("quarantine_candidates") or "").split("|") if b]


def bands_for_tokens(tokens, *, n_series_only: bool = False) -> list[str]:
    """Every band a set of codes fits. Sorted, deduplicated.

    `n_series_only=True` restricts the answer to the three truck-tonnage rungs, which is what
    the N-series band file needs. The default returns all four, which is what a page that also
    shows the D-Max class and the heavy F&G class needs.
    """
    out: set[str] = set()
    for t in tokens or []:
        b = band_for(t)
        if b in (UNRESOLVED, NOT_IN_SCOPE):
            continue
        if n_series_only and b not in N_SERIES_BANDS:
            continue
        out.add(b)
    return sorted(out)


def unresolved_tokens(tokens) -> list[str]:
    return sorted({str(t).strip().upper() for t in (tokens or [])
                   if band_for(str(t).strip().upper()) == UNRESOLVED})
