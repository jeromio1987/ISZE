"""The shape of a parsed KPI Master File block.

Kept separate from the reader so slides can be written and tested against a plain
object without opening Excel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# Values that mean "no number here". Anything else non-numeric is a marker we report.
NULL_TOKENS = {"n/d", "n/a", "na", "-", "--", "", "none", "null", "tbd"}


def coerce_value(value) -> tuple[float | None, str | None]:
    """Return (number, None) or (None, marker_text).

    Handles the mixed formats the KPI Master File actually contains:
      0.85 -> 0.85
      67   -> 67.0
      '80,5%' -> 0.805          (European decimal comma, written as a percentage)
      '78,52%' -> 0.7852
      'N/D' / 'N/A' / 'IBX' / 'Internal only' -> (None, marker)
    """
    if value is None:
        return None, None
    if isinstance(value, bool):
        return (1.0 if value else 0.0), None
    if isinstance(value, (int, float)):
        number = float(value)
        # an empty formula cell arrives as NaN, which is not a reported month
        if number != number:
            return None, None
        return number, None

    text = str(value).strip()
    if text.lower() in NULL_TOKENS:
        return None, None

    is_pct = text.endswith("%")
    body = text[:-1].strip() if is_pct else text
    body = body.replace(" ", "")
    if "," in body and "." not in body:
        body = body.replace(",", ".")
    else:
        body = body.replace(",", "")
    try:
        number = float(body)
    except ValueError:
        return None, text
    if is_pct:
        number = number / 100 if number > 1.5 else number
    return number, None


@dataclass
class KpiBlock:
    """One titled block from the 'Parts Handling' sheet."""

    name: str                        # block title as written in the file
    key: str                         # our short key, e.g. "sales_to_dealer_eur"
    unit: str                        # "EUR" | "ratio" | "months" | "lines" | "days"
    header_row: int                  # row in the sheet holding 'Distributor' and the month labels
    rows: dict[str, int]             # distributor label in file -> sheet row
    frame: pd.DataFrame              # index = month (Timestamp), columns = distributor label
    months: pd.DatetimeIndex = field(default_factory=lambda: pd.DatetimeIndex([]))
    markers: dict[str, list[str]] = field(default_factory=dict)
    # markers: distributor label -> list of non-numeric cell values found ("N/A", "N/D", "IBX", ...)

    # ------------------------------------------------------------------ lookups
    def series(self, label: str) -> pd.Series:
        """One distributor's monthly series, numeric only, index sorted."""
        if label not in self.frame.columns:
            return pd.Series(dtype="float64")
        values: dict[pd.Timestamp, float] = {}
        for month, value in self.frame[label].items():
            number, _marker = coerce_value(value)
            if number is not None:
                values[pd.Timestamp(month)] = number
        if not values:
            return pd.Series(dtype="float64")
        s = pd.Series(values, dtype="float64").sort_index()
        s.name = label
        return s

    def latest(self, label: str) -> tuple[pd.Timestamp, float] | None:
        """Most recent (month, value) for a distributor, or None when they never reported."""
        s = self.series(label)
        if s.empty:
            return None
        return s.index[-1], float(s.iloc[-1])

    def window(self, label: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        s = self.series(label)
        return s[(s.index >= pd.Timestamp(start)) & (s.index <= pd.Timestamp(end))]

    def has_label(self, label: str) -> bool:
        return label in self.frame.columns

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "key": self.key,
            "unit": self.unit,
            "months": [str(m.date()) for m in self.months],
            "distributors": sorted(self.frame.columns.tolist()),
            "markers": self.markers,
        }
