"""Hygiene rules for IDS Kaizen / Parts stats.

- Drop Benelux rollup dealers (already counted under BE + NL).
- Drop unscored 0% shells (common in MIDI empty workbooks) from averages.
- Keep ITUK totals_only rows when they have a real total %.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

ROLLUP_COUNTRIES = frozenset({"BENELUX"})
SECTION_IDS = ("A", "B", "C", "D", "E")


def is_rollup_country(country: str) -> bool:
    return (country or "").strip().upper() in ROLLUP_COUNTRIES


def is_scored_dealer(d: dict[str, Any]) -> bool:
    """True when the dealer has a usable total % (> 0)."""
    pct = d.get("total_pct")
    if pct is None:
        return False
    try:
        return float(pct) > 0.0
    except (TypeError, ValueError):
        return False


def dealers_for_stats(
    payload: dict[str, Any],
    *,
    drop_rollups: bool = True,
    drop_zero_shells: bool = True,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for d in payload.get("dealers") or []:
        if drop_rollups and is_rollup_country(str(d.get("country") or "")):
            continue
        if drop_zero_shells and not is_scored_dealer(d):
            continue
        out.append(d)
    return out


def section_pct(d: dict[str, Any], section: str) -> float | None:
    block = (d.get("sections") or {}).get(section) or {}
    v = block.get("pct")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def profile_dealers(dealers: list[dict[str, Any]]) -> dict[str, Any]:
    sec_pct: dict[str, float | None] = {}
    for sid in SECTION_IDS:
        vals = [v for d in dealers if (v := section_pct(d, sid)) is not None]
        sec_pct[sid] = mean(vals) if vals else None
    tvals = [float(d["total_pct"]) for d in dealers if d.get("total_pct") is not None]
    return {
        "dealer_count": len(dealers),
        "total_pct": mean(tvals) if tvals else None,
        "sections_pct": sec_pct,
    }


def hygienic_country_profiles(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Per-country profiles excluding rollups and 0% shells."""
    by_c: dict[str, list[dict[str, Any]]] = {}
    for d in dealers_for_stats(payload):
        by_c.setdefault(str(d["country"]), []).append(d)
    return {c: profile_dealers(rows) for c, rows in sorted(by_c.items())}


def hygienic_network(payload: dict[str, Any]) -> dict[str, Any]:
    return profile_dealers(dealers_for_stats(payload))
