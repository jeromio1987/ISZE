"""What we billed a distributor, straight from sales_fact.parquet.

The sold-to codes come from the PRISM mapping (prism/data/sap_sold_to_mapping.csv), so a
distributor with two codes (Portugal is 92 and 519) is read correctly rather than silently
half-read, which is the Israel UMI/UTI trap in another form.

Credit notes and returns are removed: SaTy CR and RE, and any negative amount, exactly as the
PRISM loader and the study generators do. Warranty is NOT removed here; a block that needs to
exclude warranty says so itself, because hiding it by default is how warranty goes missing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..errors import BprError, BprWarn
from ..paths import PRISM_DIR, SALES_FACT

CREDIT_SATY = {"CR", "RE"}
_MAPPING = PRISM_DIR / "data" / "sap_sold_to_mapping.csv"

_CACHE: dict[str, pd.DataFrame] = {}


@dataclass
class Billing:
    db_key: str
    sold_to_codes: list[float]
    frame: pd.DataFrame          # billing_date, part_number, billed_qty, net_sales_value, saty
    total_eur: float
    lines: int

    def window(self, start, end) -> pd.DataFrame:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        return self.frame[(self.frame.billing_date >= start) & (self.frame.billing_date <= end)]

    def eur(self, start, end) -> float:
        return float(self.window(start, end).net_sales_value.sum())

    def qty(self, start, end) -> float:
        return float(self.window(start, end).billed_qty.sum())

    def monthly(self, start=None, end=None) -> pd.Series:
        df = self.frame if start is None else self.window(start, end)
        if df.empty:
            return pd.Series(dtype="float64")
        s = df.groupby(df.billing_date.dt.to_period("M")).net_sales_value.sum()
        s.index = s.index.to_timestamp()
        return s.sort_index()


def sold_to_codes(db_key: str) -> list[float]:
    """Every SAP sold-to code that belongs to this distributor, from the PRISM map."""
    if not _MAPPING.is_file():
        raise BprError("E102", "The SAP sold-to mapping is missing.",
                       path=_MAPPING, expected="prism/data/sap_sold_to_mapping.csv")
    m = pd.read_csv(_MAPPING)
    m["distributor_code"] = m.distributor_code.astype(str).str.strip().str.upper()
    rows = m[m.distributor_code == db_key.strip().upper()]
    codes: list[float] = []
    for value in rows.sap_sold_to_pt.tolist():
        try:
            codes.append(float(value))
        except (TypeError, ValueError):
            continue
    return codes


def load(db_key: str, *, code: str | None = None, exclude_credits: bool = True) -> Billing:
    """Billing for one distributor.

    `code` lets a caller pass the distributor's code in a different naming system (the billing
    map calls Benelux BELGIUM, Germany GERMANY and Germany's service arm GERMANY_SERVICE).
    """
    codes = sold_to_codes(code or db_key)
    if not codes:
        raise BprError("E302", f"No SAP sold-to code is mapped to {code or db_key}, so we cannot find their billing.",
                       db=db_key, path=_MAPPING, expected="a row for this distributor",
                       found="no matching row")

    key = f"{code or db_key}:{exclude_credits}"
    if key in _CACHE:
        return _CACHE[key]

    if not SALES_FACT.is_file():
        raise BprError("E102", "The billing file is missing, so nothing can be compared to it.",
                       path=SALES_FACT, expected="01_data/00_derived/sales_fact.parquet")

    cols = ["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "saty"]
    df = pd.read_parquet(SALES_FACT, columns=cols)
    df = df[df.sold_to_sap.isin(codes)].copy()
    df["billing_date"] = pd.to_datetime(df.billing_date)
    if exclude_credits:
        df = df[~df.saty.isin(CREDIT_SATY) & (df.net_sales_value >= 0)].copy()
    df = df.sort_values("billing_date")

    if df.empty:
        raise BprError("E302", f"No billing rows at all for {db_key}.", db=db_key,
                       expected=f"rows for sold-to {codes}", found="0 rows")

    result = Billing(
        db_key=db_key,
        sold_to_codes=codes,
        frame=df.reset_index(drop=True),
        total_eur=float(df.net_sales_value.sum()),
        lines=len(df),
    )
    _CACHE[key] = result
    return result


def probe(db_key: str, code: str | None = None) -> list[BprWarn]:
    """Plain notes about this distributor's billing, for the run log and preflight."""
    out: list[BprWarn] = []
    try:
        b = load(db_key, code=code)
    except BprError as exc:
        return [BprWarn(exc.message, path=exc.path)]
    first, last = b.frame.billing_date.min(), b.frame.billing_date.max()
    out.append(BprWarn(
        f"billing for {db_key}: {b.lines:,} rows, EUR {b.total_eur:,.0f}, "
        f"{first:%b %Y} to {last:%b %Y}, sold-to {[int(c) for c in b.sold_to_codes]}"
    ))
    return out


def monthly_qty_by_part(billing: Billing, start, end) -> pd.DataFrame:
    """Billed units per part per month, for the stock-movement block."""
    df = billing.window(start, end)
    if df.empty:
        return pd.DataFrame(columns=["pn", "month", "billed_qty"])
    out = df.assign(month=df.billing_date.dt.to_period("M")).groupby(
        ["part_number", "month"], as_index=False
    ).billed_qty.sum()
    out = out.rename(columns={"part_number": "pn"})
    return out
