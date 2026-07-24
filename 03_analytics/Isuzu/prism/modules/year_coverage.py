"""How much of each calendar year the billing data actually covers.

Why this exists
---------------
`sales_fact` gained a partial CY2026 (Jan-Mar) on 2026-07-03. Anything that
picked its reporting year with `df["year"].max()` silently switched from a
complete CY2025 to a quarter of CY2026 on that date, and started comparing
part-year totals against full-year benchmarks. Use `latest_complete_year()`
to pick a default reporting year, and `is_partial()` to decide whether an
absolute figure may be quoted as an annual number.

A partial year is still internally comparable — every distributor is truncated
by the same window — so it is fine to rank *within* it. It is not fine to read
its absolute € or to benchmark it against a full year.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache

import pandas as pd

from config import SALES_FACT_PARQUET

# Billing data must cover this much of a calendar year before the year counts
# as complete. Allows for the last few days of December not yet being invoiced.
COMPLETE_YEAR_COVERAGE = 0.95


@lru_cache(maxsize=1)
def year_coverage() -> dict[int, float]:
    """{year: fraction of that calendar year covered by billing data}."""
    try:
        s = pd.read_parquet(SALES_FACT_PARQUET, columns=["billing_date"])["billing_date"]
        s = pd.to_datetime(s, errors="coerce").dropna()
        out: dict[int, float] = {}
        for yr, grp in s.groupby(s.dt.year):
            days_in_year = pd.Timestamp(int(yr), 12, 31).dayofyear
            out[int(yr)] = round(grp.max().dayofyear / days_in_year, 4)
        return out
    except Exception:
        # No parquet: fall back to the calendar. A year that has not ended
        # cannot be complete, which is the case this guards in practice.
        today = date.today()
        return {today.year: round(today.timetuple().tm_yday / 365, 4)}


def is_partial(year: int) -> bool:
    """True if `year` is not covered to COMPLETE_YEAR_COVERAGE by billing data."""
    return year_coverage().get(int(year), 0.0) < COMPLETE_YEAR_COVERAGE


def latest_complete_year(years: list[int] | None = None) -> int:
    """Newest year whose billing data is complete.

    Falls back to the newest year available if none qualify, so a caller never
    ends up with nothing to report.
    """
    cov = year_coverage()
    pool = sorted(int(y) for y in (years if years is not None else cov.keys()))
    if not pool:
        raise ValueError("no years available")
    complete = [y for y in pool if not is_partial(y)]
    return (complete or pool)[-1]
