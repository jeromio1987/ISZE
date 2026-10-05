"""Part families and part-number keys.

Two jobs:
  1. normalise a part number so the catalogue, the billing file and a distributor's own file
     can be joined (they are written with and without leading zeros and trailing ".0");
  2. map a part number to the service family a deck talks about (oil filters, brake pads, ...).

The family rollup lives here and only here. No slide keeps its own copy.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from ..errors import BprError
from ..paths import CATALOG


def norm_pn(series: pd.Series) -> pd.Series:
    """Part numbers as comparable strings: no leading zeros, no trailing .0, no spaces."""
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.upper()
        .str.lstrip("0")
        .replace("", "0")
    )


# Families a deck shows, in a fixed order. The key is the prefix of the catalogue's own
# pms_category value, so "brake_pad" also catches "brake_pad_front".
FAMILIES: list[tuple[str, str]] = [
    ("oil_filter", "Oil filters"),
    ("fuel_filter", "Fuel filters"),
    ("air_filter", "Air filters"),
    ("brake_pad", "Brake pads"),
    ("brake_rotor", "Brake rotors"),
    ("brake_shoe", "Brake shoes"),
    ("clutch_kit", "Clutch kits"),
]
FAMILY_KEYS = [k for k, _ in FAMILIES]
FAMILY_LABEL = dict(FAMILIES)


def family_of(category: str | None) -> str | None:
    """Catalogue pms_category -> our family key, or None when it is not a family we show."""
    c = str(category or "").strip().lower()
    if not c:
        return None
    if c.startswith("brake_pad"):
        return "brake_pad"
    if c.startswith("brake_rotor") or c.startswith("brake_disc"):
        return "brake_rotor"
    if c.startswith("brake_shoe") or c.startswith("brake_lining"):
        return "brake_shoe"
    if c in ("oil_filter", "fuel_filter", "air_filter", "clutch_kit"):
        return c
    return None


@lru_cache(maxsize=1)
def load() -> pd.DataFrame:
    """part number key -> family. Empty frame if the catalogue is missing."""
    if not CATALOG.is_file():
        raise BprError("E102", "The parts catalogue is missing, so parts cannot be grouped into families.",
                       path=CATALOG, expected="01_data/00_derived/parts_catalog_dimension.csv")
    cat = pd.read_csv(CATALOG, dtype=str, usecols=["part_number", "pms_category"])
    cat["pn"] = norm_pn(cat.part_number)
    cat["family"] = cat.pms_category.map(family_of)
    cat = cat[cat.family.notna()][["pn", "family"]].drop_duplicates("pn")
    return cat.reset_index(drop=True)


def tag(frame: pd.DataFrame, pn_col: str = "pn") -> pd.DataFrame:
    """Add a 'family' column to a frame carrying part numbers. Unmatched parts get NaN."""
    cat = load()
    out = frame.copy()
    if pn_col not in out.columns:
        raise BprError("E202", f"The table has no '{pn_col}' column to group by.",
                       expected=pn_col, found=", ".join(map(str, out.columns))[:200])
    if pn_col != "pn":
        out = out.rename(columns={pn_col: "pn"})
    out["pn"] = norm_pn(out["pn"])
    return out.merge(cat, on="pn", how="left")


def family_units(frame: pd.DataFrame, value_col: str, kind: str = "sum") -> pd.DataFrame:
    """Units per family. Rows outside the seven families are dropped, not spread around."""
    tagged = tag(frame)
    tagged = tagged[tagged.family.notna()]
    if tagged.empty:
        return pd.DataFrame(columns=["family", value_col])
    grouped = tagged.groupby("family")[value_col].agg(kind).reset_index()
    grouped["family"] = pd.Categorical(grouped.family, categories=FAMILY_KEYS, ordered=True)
    return grouped.sort_values("family").reset_index(drop=True)
