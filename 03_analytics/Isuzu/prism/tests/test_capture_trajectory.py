"""Partial-year guard on Contract 7 capture trajectory.

The 2026-07-17 Early Warning build found 29 of 35 declining alerts were
artifacts of regressing through a Q1-only year. These tests lock that guard
without touching sales_fact.
"""

from __future__ import annotations

import pandas as pd

from modules.strategic_build import build_capture_trajectory


def _pms_rows(dist: str, cat: str, years: dict[int, float]) -> list[dict]:
    return [
        {
            "distributor_code": dist,
            "pms_category": cat,
            "year": year,
            "line_type": "total",
            "capture_rate": cap,
        }
        for year, cap in years.items()
    ]


def _alert_pairs(df: pd.DataFrame) -> set[tuple[str, str]]:
    hist = df.loc[~df["is_projected"]]
    flagged = hist.loc[hist["alert_declining"], ["distributor_code", "pms_category"]]
    return set(map(tuple, flagged.drop_duplicates().itertuples(index=False, name=None)))


def test_partial_year_cliff_does_not_flag() -> None:
    """Stable 2023–25 + a truncated 2026 must not fire alert_declining."""
    pms = pd.DataFrame(
        _pms_rows("NORWAY", "oil_filter", {2023: 0.10, 2024: 0.11, 2025: 0.10, 2026: 0.02})
    )
    out = build_capture_trajectory(pms, is_partial_year=lambda y: y == 2026)
    assert _alert_pairs(out) == set()
    actual_2026 = out.loc[(~out["is_projected"]) & (out["year"] == 2026)]
    assert len(actual_2026) == 1
    assert actual_2026["capture_rate"].iloc[0] == 0.02


def test_real_complete_year_decline_still_flags() -> None:
    """A steep complete-year decline must still alert, even with a partial year present."""
    pms = pd.DataFrame(
        _pms_rows("UTI", "lubricants", {2023: 0.40, 2024: 0.28, 2025: 0.14, 2026: 0.02})
    )
    out = build_capture_trajectory(pms, is_partial_year=lambda y: y == 2026)
    assert ("UTI", "lubricants") in _alert_pairs(out)
    slope = float(out.loc[~out["is_projected"], "trend_slope_pp_per_year"].iloc[0])
    assert slope < -0.05


def test_partial_year_makes_slope_more_negative() -> None:
    """Control: including 2026 as complete steepens the slope (the contamination)."""
    pms = pd.DataFrame(
        _pms_rows("NORWAY", "oil_filter", {2023: 0.10, 2024: 0.11, 2025: 0.10, 2026: 0.02})
    )
    unguarded = build_capture_trajectory(pms, is_partial_year=lambda _y: False)
    guarded = build_capture_trajectory(pms, is_partial_year=lambda y: y == 2026)
    s_u = float(unguarded["trend_slope_pp_per_year"].iloc[0])
    s_g = float(guarded["trend_slope_pp_per_year"].iloc[0])
    assert s_u < s_g
    assert ("NORWAY", "oil_filter") not in _alert_pairs(guarded)
