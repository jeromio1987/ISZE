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

A code whose weight is not settled is marked `pending_ruling` and carries an interim band;
`band_for()` returns it and `is_pending_ruling()` tells a caller that it is interim. `NMR` and
`NMR85` were the pending codes until 2026-09-23, when Jerome ruled them onto the 5.5 t rung for
the European N55 class (evidence in the map rows and in
`01_data/90_INBOX/TONNAGE_FINISH_REPORT_2026-09-23.md`). No code is pending after that ruling,
so `pending_ruling_codes()` currently returns an empty list. The marker and `is_pending_ruling()`
are kept: a future code can be parked, and a caller must still be able to ask.

Wildcard series tokens (`TF*`, `N*`, `N*R`) are not codes at all. A token that contains an
asterisk is never looked up in the map and never converted into a band; `is_wildcard_token()` is
the one recogniser for both the prefix shape (`TF*`) and the infix shape (`N*R`), and it is a
recogniser only - it does not and must not feed a band.
"""
from __future__ import annotations

import csv
import re
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


# ── the one recogniser for a wildcard series token. Two shapes occur in the evidence and both
#    are wildcards, neither is a code:
#
#      prefix form   TF*   F*   N*   NQ*     the asterisk closes the token
#      infix form    N*R   N*S   F*R   C*Z    the asterisk stands inside it, the letters after
#                                             it being the suffix the family shares
#
#    The prefix form alone was recognised until 2026-09-24, so a `N*R` token fell through to the
#    series lookup, matched nothing, and was recorded neither as a code nor as a wildcard - which
#    made a part number whose only vehicle evidence was `N*R` read as though no vehicle were named
#    at all.
#
#    This is a RECOGNISER, not a converter. A wildcard stands for a whole family at several
#    weights, so it can never name one rung, and nothing here feeds `band_for()`. The guard that
#    keeps a wildcard off a band is the `*` test at the call site; widening this pattern therefore
#    cannot widen what reaches a band.
WILDCARD_PREFIX_RE = re.compile(r"^[A-Z]{1,4}\d{0,3}\*$")
WILDCARD_INFIX_RE = re.compile(r"^[A-Z]{1,4}\d{0,3}\*[A-Z]{0,4}$")


def is_wildcard_token(token: str) -> bool:
    """True for `TF*` and for `N*R`. A recogniser only - a wildcard never becomes a band."""
    t = str(token or "").strip().upper()
    if not t:
        return False
    return (WILDCARD_PREFIX_RE.match(t) is not None
            or WILDCARD_INFIX_RE.match(t) is not None
            or t.endswith("*"))


def assert_no_wildcard_bands() -> None:
    """Nothing in the map may carry a band while its code contains an asterisk.

    A wildcard stands for a family at several weights; if one ever acquired a `tonnage_band`,
    every reader would start placing those parts on a single rung. Cheap, and it turns a silent
    mis-mapping into a startup error.
    """
    bad = {c: band_for(c) for c in load_map()
           if "*" in c and band_for(c) not in (UNRESOLVED, NOT_IN_SCOPE)}
    if bad:
        raise AssertionError(f"a wildcard code carries a band: {bad}")


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


# ── the machine-readable outcome of a code. `status` already carries this, but it is a raw
#    label with no stated vocabulary; `outcome` is the same fact written for a reader that has
#    to branch on it. The two can never disagree - `status` is what decides - and `status` is
#    left in place beside it.
#
#      resolved             a source names the code and gives it a band
#      pending_ruling       parked: a band is carried but nobody has settled it
#      out_of_scope         real, but outside the four bands (a bus, a C&E truck, an export name)
#      wildcard_fragment    a `CODE*` stem in the evidence, not a code any source names
#      unresolved_no_source no source names it and it is not a wildcard fragment
#
#    The distinction that matters is the last two against each other: a wildcard fragment is a
#    part of a name, while unresolved_no_source is a whole code that nobody has spoken for.
#    They were previously indistinguishable without reading the evidence sentence.
OUTCOME_RESOLVED = "resolved"
OUTCOME_PENDING = PENDING_RULING            # 'pending_ruling', same spelling as `status`
OUTCOME_OUT_OF_SCOPE = "out_of_scope"
OUTCOME_WILDCARD_FRAGMENT = "wildcard_fragment"
OUTCOME_NO_SOURCE = "unresolved_no_source"
OUTCOME_ORDER = [OUTCOME_RESOLVED, OUTCOME_PENDING, OUTCOME_OUT_OF_SCOPE,
                 OUTCOME_WILDCARD_FRAGMENT, OUTCOME_NO_SOURCE]


def outcome_for(code: str) -> str:
    """The machine-readable outcome for a code, or `unresolved_no_source` if it is unknown."""
    r = _row(code)
    if not r:
        return OUTCOME_NO_SOURCE
    o = (r.get("outcome") or "").strip()
    if o:
        return o
    # fall back to `status`, so a map row written before the column existed still answers
    st = (r.get("status") or "").strip()
    if st == "resolved":
        return OUTCOME_RESOLVED
    if st == PENDING_RULING:
        return OUTCOME_PENDING
    if st == "out_of_scope" or (r.get("tonnage_band") or "").strip() == NOT_IN_SCOPE:
        return OUTCOME_OUT_OF_SCOPE
    return OUTCOME_NO_SOURCE


def outcome_counts() -> dict[str, int]:
    """How many codes carry each outcome. Read this rather than counting prose."""
    out = {o: 0 for o in OUTCOME_ORDER}
    for c in load_map():
        out[outcome_for(c)] = out.get(outcome_for(c), 0) + 1
    return out


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
