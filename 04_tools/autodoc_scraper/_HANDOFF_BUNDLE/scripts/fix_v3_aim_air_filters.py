"""
Correct v3 AIM_Category for air-intake parts mis-tagged as Fluids Chemicals.

Also refreshes bundle scraper CSVs (AIM_Category column) for affected PNs.

Run from _HANDOFF_BUNDLE:
    python scripts/fix_v3_aim_air_filters.py
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "ISZE_Parts_Intelligence_v3.xlsx"
SHEET = "PN_Price_Matrix"
SCRAPE_CSVS = ("autodoc_results.csv", "ks_results.csv", "mekonomen_results.csv")


def aim_correction(description: str) -> str | None:
    if not isinstance(description, str):
        return None
    d = description.upper()
    if re.search(
        r"FILTER.*AIR|ELEMENT.*AIR\s+CLEANER|ELEMENT\s+ASM.*AIR\s+CLEANER",
        d,
    ):
        return "Maintenance Service"
    if "HOSE" in d and "AIR CLEANER" in d:
        return "Intake Exhaust Emission"
    if "GASKET" in d and "AIR CLEANER" in d:
        return "Intake Exhaust Emission"
    return None


def fix_v3() -> pd.DataFrame:
    if not V3.exists():
        raise FileNotFoundError(V3)
    backup = V3.with_name(
        f"ISZE_Parts_Intelligence_v3.backup_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    )
    shutil.copy2(V3, backup)
    print(f"Backup: {backup}")

    df = pd.read_excel(V3, sheet_name=SHEET, dtype={"PN": str})
    df["PN"] = df["PN"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)

    changes: list[dict] = []
    for idx, row in df.iterrows():
        if str(row.get("AIM_Category", "")) != "Fluids Chemicals":
            continue
        new_aim = aim_correction(str(row.get("Description", "")))
        if not new_aim:
            continue
        changes.append(
            {
                "PN": row["PN"],
                "Description": row["Description"],
                "old_AIM_Category": row["AIM_Category"],
                "new_AIM_Category": new_aim,
            }
        )
        df.at[idx, "AIM_Category"] = new_aim

    if not changes:
        print("No Fluids Chemicals air-intake rows to fix.")
        return pd.DataFrame()

    # Preserve other sheets
    all_sheets = pd.read_excel(V3, sheet_name=None, dtype={"PN": str})
    all_sheets[SHEET] = df
    with pd.ExcelWriter(V3, engine="openpyxl") as w:
        for name, sheet_df in all_sheets.items():
            sheet_df.to_excel(w, sheet_name=name, index=False)

    chg = pd.DataFrame(changes)
    print(f"Updated {len(chg)} rows in {V3.name}")
    print(chg.to_string(index=False))
    return chg


def fix_scrape_csvs(pns: set[str]) -> None:
    for fname in SCRAPE_CSVS:
        fp = ROOT / fname
        if not fp.exists():
            continue
        df = pd.read_csv(fp, dtype={"PN": str}, low_memory=False)
        df["PN"] = df["PN"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
        mask = df["PN"].isin(pns)
        if not mask.any():
            continue
        v3 = pd.read_excel(V3, sheet_name=SHEET, dtype={"PN": str})
        v3["PN"] = v3["PN"].astype(str).str.zfill(10)
        aim = v3.set_index("PN")["AIM_Category"]
        df.loc[mask, "AIM_Category"] = df.loc[mask, "PN"].map(aim)
        df.to_csv(fp, index=False)
        print(f"Refreshed AIM_Category in {fname} ({mask.sum()} rows)")


def main() -> None:
    chg = fix_v3()
    if not chg.empty:
        fix_scrape_csvs(set(chg["PN"].astype(str)))


if __name__ == "__main__":
    main()
