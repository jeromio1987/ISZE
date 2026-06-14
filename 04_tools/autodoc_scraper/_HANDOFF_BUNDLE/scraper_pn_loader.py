"""Load top PNs for scrapers from v3 Excel or autodoc_results.csv fallback."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent


def find_v3() -> Path | None:
    candidates = [
        SCRIPT_DIR / "ISZE_Parts_Intelligence_v3.xlsx",
        SCRIPT_DIR.parent.parent / "Isuzu" / "data" / "ISZE_Parts_Intelligence_v3.xlsx",
    ]
    for p in candidates:
        if p.exists():
            return p
    for root, _, files in os.walk(Path(__file__).resolve().parents[3]):
        if "ISZE_Parts_Intelligence_v3.xlsx" in files:
            return Path(root) / "ISZE_Parts_Intelligence_v3.xlsx"
    return None


def load_top_pns(n: int) -> pd.DataFrame:
    """Top revenue PNs with Description, PR00_EUR, Rev_CY2025_EUR."""
    fpath = find_v3()
    if fpath:
        df = pd.read_excel(fpath, sheet_name="PN_Price_Matrix", dtype={"PN": str})
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        df["Rev_CY2025_EUR"] = pd.to_numeric(df.get("Rev_CY2025_EUR", 0), errors="coerce").fillna(0)
        cols = [c for c in ["PN", "Description", "PR00_EUR", "Rev_CY2025_EUR"] if c in df.columns]
        return (
            df[df["Rev_CY2025_EUR"] > 0]
            .sort_values("Rev_CY2025_EUR", ascending=False)
            .head(n)[cols]
            .reset_index(drop=True)
        )

    uk = SCRIPT_DIR / "autodoc_results.csv"
    if not uk.is_file():
        raise FileNotFoundError(
            "No ISZE_Parts_Intelligence_v3.xlsx and no autodoc_results.csv for PN list"
        )
    df = pd.read_csv(uk, dtype={"PN": str})
    df["PN"] = df["PN"].astype(str).str.zfill(10)
    df["Rev_CY2025_EUR"] = pd.to_numeric(df.get("Rev_CY2025_EUR", 0), errors="coerce").fillna(0)
    df["PR00_EUR"] = pd.to_numeric(df.get("PR00_EUR", 0), errors="coerce")
    cols = [c for c in ["PN", "Description", "PR00_EUR", "Rev_CY2025_EUR"] if c in df.columns]
    out = df.sort_values("Rev_CY2025_EUR", ascending=False).head(n)[cols].reset_index(drop=True)
    return out
