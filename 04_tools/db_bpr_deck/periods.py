"""Period handling.

The default is the ISZE fiscal year: April to March. FY2027 = 1 April 2026 to 31 March 2027.
Calendar years are supported because some distributor files and some KPI reporting are kept
that way, but the deck labels which one it used on every slide that involves a date.

Formatting helpers live here too, so a euro or a percentage is written the same way everywhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

FY_MONTHS = 12


@dataclass(frozen=True)
class Period:
    basis: str                     # "fiscal" | "calendar"
    label: str                     # what goes on the slide, e.g. "FY2026"
    start: pd.Timestamp
    end: pd.Timestamp

    @property
    def months(self) -> pd.DatetimeIndex:
        return pd.date_range(self.start, self.end, freq="MS")

    @property
    def month_count(self) -> int:
        return len(self.months)

    @property
    def is_partial(self) -> bool:
        return self.month_count < FY_MONTHS

    @property
    def through(self) -> str:
        return f"{self.end:%b %Y}"

    def contains(self, stamp) -> bool:
        return self.start <= pd.Timestamp(stamp) <= self.end


def fiscal_year_of(when) -> int:
    stamp = pd.Timestamp(when)
    return stamp.year + (1 if stamp.month >= 4 else 0)


def fiscal(fy: int, through_month: int | None = None) -> Period:
    """FY2026 -> 1 Apr 2025 to 31 Mar 2026. `through_month` truncates it for a year in progress."""
    start = pd.Timestamp(year=fy - 1, month=4, day=1)
    if through_month:
        year = fy if through_month <= 3 else fy - 1
        end = pd.Timestamp(year=year, month=int(through_month), day=1) + pd.offsets.MonthEnd(0)
        label = f"FY{fy} to {end:%b %Y}"
    else:
        end = pd.Timestamp(year=fy, month=3, day=31)
        label = f"FY{fy}"
    return Period("fiscal", label, start, min(end, pd.Timestamp(year=fy, month=3, day=31)))


def calendar(year: int, through_month: int | None = None) -> Period:
    start = pd.Timestamp(year=year, month=1, day=1)
    if through_month:
        end = pd.Timestamp(year=year, month=int(through_month), day=1) + pd.offsets.MonthEnd(0)
        label = f"CY{year} to {end:%b}"
    else:
        end = pd.Timestamp(year=year, month=12, day=31)
        label = f"CY{year}"
    return Period("calendar", label, start, end)


def build(basis: str, year: int, through_month: int | None = None) -> Period:
    return fiscal(year, through_month) if basis == "fiscal" else calendar(year, through_month)


def prior_year(period: Period) -> Period:
    """The same window one year earlier, for a year-on-year comparison."""
    if period.basis == "fiscal":
        fy = fiscal_year_of(period.start)
        through = period.end.month if period.is_partial else None
        return fiscal(fy - 1, through)
    return calendar(period.start.year - 1, period.end.month if period.is_partial else None)


def current_fy() -> int:
    return fiscal_year_of(pd.Timestamp(date.today()))


# ------------------------------------------------------------------ formatting

def eur(value, *, dp: int = 0) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"EUR {value:,.{dp}f}"


def eur_compact(value) -> str:
    """EUR 1.86M / EUR 774K / EUR 842 - the form the decks use."""
    if value is None or pd.isna(value):
        return "n/a"
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}EUR {value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}EUR {value / 1_000:.0f}K"
    return f"{sign}EUR {value:,.0f}"


def pct(value, *, dp: int = 1, from_ratio: bool = True) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    ratio = float(value) if from_ratio else float(value) / 100.0
    return f"{ratio * 100:.{dp}f}%"


def ratio(value, *, dp: int = 2) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{dp}f}x"


def signed(value, *, dp: int = 1, from_ratio: bool = True) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    ratio_value = float(value) if from_ratio else float(value) / 100.0
    return f"{ratio_value * 100:+.{dp}f}%"


def qty(value) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):,.0f}"
