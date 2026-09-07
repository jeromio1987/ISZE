#!/usr/bin/env python3
"""Build prism/data/sap_sold_to_mapping.csv from CY raw exports + master mapping."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import RAW_SALES_DIR  # noqa: E402
from modules.data_prep import build_name_to_code_map, load_distributor_mapping  # noqa: E402

OUT = PRISM_ROOT / "data" / "sap_sold_to_mapping.csv"
CY_FILES = [
    RAW_SALES_DIR / "CY2023-2024.XLSX",
    RAW_SALES_DIR / "CY2025.XLSX",
]

MANUAL = [
    (2574, "I.M. PARTS & SERVICE Limited", "IUK", "AIM confirmed"),
    (2575, "ISUZU TRUCK (UK) LIMITED", "ITUK", "AIM confirmed"),
    (2194, "MIDI EUROPE S.R.L.", "MIDI", "SAP 2194; CY billing; EXCLUDED_CODES"),
    (146, "SERVICE FEE OUTSIDE EUROPE", "NON_PARTS", "CY2026 non-parts; EXCLUDED_CODES"),
    (373, "IMIO / SERVICE", "NON_PARTS", "CY2026 non-parts service; EXCLUDED_CODES"),
    (2970, "COST DEMURRAGE", "NON_PARTS", "CY2026 non-parts demurrage; EXCLUDED_CODES"),
    (2987, "COMPENSATIONS SALE E-CREDIT", "NON_PARTS", "CY2026 non-parts e-credit; EXCLUDED_CODES"),
]


def _billing_sheet(path: Path) -> str | int:
    xl = pd.ExcelFile(path, engine="openpyxl")
    for name in xl.sheet_names:
        hdr = pd.read_excel(path, sheet_name=name, nrows=0, engine="openpyxl")
        if "Billing Date" in hdr.columns:
            return name
    return 0


def extract_pairs(path: Path) -> pd.DataFrame:
    sheet = _billing_sheet(path)
    df = pd.read_excel(path, sheet_name=sheet, usecols=lambda c: True, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    if "Sold-to pt" not in df.columns:
        return pd.DataFrame(columns=["sap_sold_to_pt", "sold_to_name"])
    out = pd.DataFrame()
    out["sap_sold_to_pt"] = pd.to_numeric(df["Sold-to pt"], errors="coerce")
    out = out.dropna(subset=["sap_sold_to_pt"])
    out["sap_sold_to_pt"] = out["sap_sold_to_pt"].astype(int)
    if "DB" in df.columns:
        out["sold_to_name"] = df["DB"].astype(str).str.strip()
    else:
        out["sold_to_name"] = ""
    return out


def main() -> int:
    name_map = build_name_to_code_map(load_distributor_mapping(str(PRISM_ROOT / "data" / "distributor_master_mapping.csv")))
    rows = {sap: (name, code, note) for sap, name, code, note in MANUAL}

    for path in CY_FILES:
        if not path.exists():
            continue
        chunk = extract_pairs(path)
        for _, r in chunk.iterrows():
            sap = int(r["sap_sold_to_pt"])
            name = str(r["sold_to_name"]).strip()
            if name and name.lower() != "nan":
                code = name_map.get(name) or name_map.get(name.upper())
                if sap not in rows or not rows[sap][0]:
                    rows[sap] = (name, code or "", f"from {path.name}")
            elif sap not in rows:
                rows[sap] = ("", "", f"unmapped — {path.name}")

    df = pd.DataFrame(
        [
            {
                "sap_sold_to_pt": sap,
                "sold_to_name": tup[0],
                "distributor_code": tup[1],
                "notes": tup[2],
            }
            for sap, tup in sorted(rows.items())
        ]
    )
    df.to_csv(OUT, index=False)
    mapped = (df["distributor_code"] != "").sum()
    print(f"Wrote {len(df)} SAP sold-to rows -> {OUT} ({mapped} with distributor_code)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
