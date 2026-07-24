"""
CY2025 warranty-parts EUR per GPS distributor (ex-warranty GPS adjustment).

Authoritative values: prism/data/gps_warranty_cy2025.json (synced from Data/Warranty_CY2025_by_DB.md).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

PRISM_ROOT = Path(__file__).resolve().parent.parent
WARRANTY_JSON = PRISM_ROOT / "data" / "gps_warranty_cy2025.json"
WARRANTY_YEAR = 2025


@lru_cache(maxsize=1)
def _load_payload() -> dict[str, Any]:
    if not WARRANTY_JSON.exists():
        return {"warranty_eur": {}, "data_gaps": [], "notes": {}}
    return json.loads(WARRANTY_JSON.read_text(encoding="utf-8"))


def warranty_table() -> dict[str, float]:
    return {k: float(v) for k, v in _load_payload().get("warranty_eur", {}).items()}


def warranty_data_gaps() -> set[str]:
    return set(_load_payload().get("data_gaps", []))


def warranty_notes() -> dict[str, str]:
    return dict(_load_payload().get("notes", {}))


def warranty_eur_for_db_year(distributor_code: str, year: int) -> float | None:
    """Return warranty EUR for CY2025 GPS base DBs; None if year != 2025 or DB not in table."""
    if int(year) != WARRANTY_YEAR:
        return None
    db = str(distributor_code).strip().upper()
    table = warranty_table()
    if db not in table:
        return None
    return float(table[db])


def apply_warranty_to_spu_frame(df) -> Any:
    """Add ex-warranty columns to a gps_spu_by_distributor-shaped DataFrame."""
    import pandas as pd

    out = df.copy()
    warr: list[float | None] = []
    for _, row in out.iterrows():
        warr.append(warranty_eur_for_db_year(str(row["distributor_code"]), int(row["year"])))
    out["warranty_parts_eur"] = warr
    has_w = out["warranty_parts_eur"].notna()
    out["sales_ex_warranty_eur"] = np.where(
        has_w,
        out["total_sales_eur"] - out["warranty_parts_eur"],
        np.nan,
    )
    out["spend_per_unit_ex_warranty_eur"] = np.where(
        has_w & (out["uio_units"] > 0),
        out["sales_ex_warranty_eur"] / out["uio_units"],
        np.nan,
    )
    gaps = warranty_data_gaps()
    out["warranty_data_gap"] = out["distributor_code"].isin(gaps) & (out["year"] == WARRANTY_YEAR)
    return out
