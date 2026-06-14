"""Load top PNs for scrapers from v3 Excel or autodoc_results.csv fallback."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import AUTODOC_SCRAPER_DIR, resolve_v3_workbook

SCRIPT_DIR = Path(__file__).parent

BASE_COLS = ["PN", "Description", "PR00_EUR", "Rev_CY2025_EUR"]
EXTRA_COLS = ["Qty_CY2025", "Source", "Class", "AIM_Category"]


def load_top_pns(n: int, *, extra_columns: bool = False) -> pd.DataFrame:
    """Top revenue PNs with Description, PR00_EUR, Rev_CY2025_EUR."""
    fpath = resolve_v3_workbook()
    if fpath:
        df = pd.read_excel(fpath, sheet_name="PN_Price_Matrix", dtype={"PN": str})
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        df["Rev_CY2025_EUR"] = pd.to_numeric(df.get("Rev_CY2025_EUR", 0), errors="coerce").fillna(0)
        want = BASE_COLS + (EXTRA_COLS if extra_columns else [])
        cols = [c for c in want if c in df.columns]
        return (
            df[df["Rev_CY2025_EUR"] > 0]
            .sort_values("Rev_CY2025_EUR", ascending=False)
            .head(n)[cols]
            .reset_index(drop=True)
        )

    uk = AUTODOC_SCRAPER_DIR / "autodoc_results.csv"
    if not uk.is_file():
        raise FileNotFoundError(
            "No ISZE_Parts_Intelligence_v3.xlsx and no autodoc_results.csv for PN list"
        )
    df = pd.read_csv(uk, dtype={"PN": str})
    df["PN"] = df["PN"].astype(str).str.zfill(10)
    df["Rev_CY2025_EUR"] = pd.to_numeric(df.get("Rev_CY2025_EUR", 0), errors="coerce").fillna(0)
    df["PR00_EUR"] = pd.to_numeric(df.get("PR00_EUR", 0), errors="coerce")
    want = BASE_COLS + (EXTRA_COLS if extra_columns else [])
    cols = [c for c in want if c in df.columns]
    return df.sort_values("Rev_CY2025_EUR", ascending=False).head(n)[cols].reset_index(drop=True)
