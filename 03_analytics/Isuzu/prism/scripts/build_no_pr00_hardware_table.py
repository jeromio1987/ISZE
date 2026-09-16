#!/usr/bin/env python3
"""Leftover billed parts with no list price — GPS FY grain, euros only.

Do not lead with pieces. Sales-to-dealer qty is not a KPI. Shell 5500* stays parked.
No %GM — there is no PR00 list price. Billed ZPR1 is not a list price.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR, SALES_FACT_PARQUET, resolve_mapping_path  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import normalize_pn  # noqa: E402
from modules.fiscal import gps_fy_dates, sales_fiscal_from_gps_fy  # noqa: E402
from modules.sales_loader import _finish_sales_frame  # noqa: E402

GPS_FY = 2026
SRC = DERIVED_DIR / "no_pr00_gap_remaining_zpr1_check_20260812.csv"
OUT_CSV = DERIVED_DIR / "no_pr00_hardware_fy2026.csv"
OUT_MD = DERIVED_DIR / "NO_PR00_HARDWARE_FY2026.md"
OUT_YTD_CSV = DERIVED_DIR / "no_pr00_hardware_fy2027_ytd.csv"
SHELL_PREFIX = "5500"

DB_NAMES = {
    "UTI": "UTI",
    "UMI": "UMI",
    "KAZAKHSTAN": "Kazakhstan",
    "PORTUGAL": "Portugal",
    "IUK": "Isuzu UK pickup",
    "ITUK": "Isuzu Truck UK",
    "IRELAND": "Ireland",
    "GREECE": "Greece",
}

PLAIN_WORDS = {
    "CAB ASM; SERVICE,WO/ELEC": "Cab assembly, service, without electrics",
    "STEERING UNIT": "Steering unit",
    "HYDRAULIC UNIT; ANTI LOCK BRK": "ABS hydraulic unit",
    "TRANSMISSION ASM; MANUAL": "Manual transmission",
    "CAMERA ASM": "Camera",
    "PUMP ASM; OIL": "Oil pump",
    "LID; FRT OUTER": "Front outer lid",
    "TRANSFER ASM": "Transfer assembly",
    "PUMP ASM; DEF,DCM SPLY": "DEF supply pump",
    "SENSOR; DISTANCE": "Distance sensor",
    "LID; FRT INNER": "Front inner lid",
    "CONVERTER": "Converter",
    "CLUTCH ASM": "Clutch",
    "CONTROLLER; ABS": "ABS controller",
    "PANEL; COWL UPR": "Upper cowl panel",
    "TAIL GATE ASSIST SET": "Tail-gate assist",
    "HARNESS KIT;F145": "F145 harness kit",
    "HANDLE; OUTSIDE,BACK DOOR": "Rear door outside handle",
    "HARNESS": "Harness",
    "SWITCH&HARN;PUSH,24V": "24V push switch and harness",
    "1DIN SWITCH;STORAGE BOX": "Storage-box switch",
}

FAMILY_RULES = (
    ("CAB ASM", "Cab assemblies"),
    ("STEERING", "Steering units"),
    ("HYDRAULIC UNIT", "ABS hydraulic units"),
    ("ANTI LOCK", "ABS hydraulic units"),
    ("CONTROLLER; ABS", "ABS controllers"),
    ("TRANSMISSION ASM", "Manual transmissions"),
    ("CAMERA", "Cameras"),
    ("PUMP ASM; OIL", "Oil pumps"),
    ("LID; FRT", "Front lids"),
    ("TRANSFER ASM", "Transfers"),
    ("PUMP ASM; DEF", "DEF pumps"),
    ("SENSOR; DISTANCE", "Distance sensors"),
    ("CONVERTER", "Converters"),
    ("CLUTCH ASM", "Clutches"),
    ("PANEL; COWL", "Cowl panels"),
    ("TAIL GATE", "Tail-gate assists"),
    ("HARNESS", "Harnesses"),
    ("SWITCH", "Switches"),
    ("HANDLE", "Door handles"),
)


def words_for(description: str) -> str:
    key = str(description).strip()
    return PLAIN_WORDS.get(key, key)


def family_of(description: str) -> str:
    text = str(description).upper()
    for needle, label in FAMILY_RULES:
        if needle in text:
            return label
    return str(description).strip() or "Other"


def db_label(code: str) -> str:
    return DB_NAMES.get(str(code), str(code))


def billed_who(part_df: pd.DataFrame) -> str:
    bits = []
    g = (
        part_df.groupby("distributor_code", as_index=False)["net_sales_value"]
        .sum()
        .sort_values("net_sales_value", ascending=False)
    )
    for code, eur in g.itertuples(index=False, name=None):
        bits.append(f"{db_label(code)} €{eur:,.0f}")
    return "; ".join(bits) if bits else "unmapped"


def aggregate_no_list(sales: pd.DataFrame, residual: pd.DataFrame, sales_fiscal: int) -> pd.DataFrame:
    pns = set(residual["part_number"])
    desc = dict(zip(residual["part_number"], residual["description"]))
    hit = sales[
        sales["part_number"].isin(pns) & (sales["fiscal_year"] == int(sales_fiscal))
    ].copy()
    if hit.empty:
        return pd.DataFrame(
            columns=[
                "part_number",
                "description",
                "part_in_words",
                "family",
                "billed_eur",
                "billed_to",
            ]
        )
    rows = []
    for pn, part_df in hit.groupby("part_number"):
        description = desc.get(pn, "")
        rows.append(
            {
                "part_number": pn,
                "description": description,
                "part_in_words": words_for(description),
                "family": family_of(description),
                "billed_eur": round(float(part_df["net_sales_value"].sum()), 2),
                "billed_to": billed_who(part_df),
            }
        )
    out = pd.DataFrame(rows).sort_values("billed_eur", ascending=False).reset_index(drop=True)
    return out


def _load_sales() -> pd.DataFrame:
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    sales = _finish_sales_frame(sales, mapping)
    sales["part_number"] = sales["part_number"].map(normalize_pn)
    return sales


def _load_residual() -> pd.DataFrame:
    residual = pd.read_csv(SRC, dtype={"part_number": str})
    residual["part_number"] = residual["part_number"].map(normalize_pn)
    residual = residual[~residual["part_number"].astype(str).str.startswith(SHELL_PREFIX)].copy()
    return residual


def _md_table(df: pd.DataFrame) -> list[str]:
    lines = [
        "| part | we billed € | billed to | number |",
        "|------|-------------|-----------|--------|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['part_in_words']} | {r['billed_eur']:,.2f} | {r['billed_to']} | {r['part_number']} |"
        )
    return lines


def _family_table(df: pd.DataFrame) -> list[str]:
    fam = (
        df.groupby("family", as_index=False)["billed_eur"]
        .sum()
        .sort_values("billed_eur", ascending=False)
    )
    lines = [
        "| family | we billed € |",
        "|--------|-------------|",
    ]
    for _, r in fam.iterrows():
        lines.append(f"| {r['family']} | {r['billed_eur']:,.2f} |")
    return lines


def write_md(
    fy_df: pd.DataFrame,
    ytd_df: pd.DataFrame,
    db_fy: pd.Series,
    missing_fy: list[str],
    desc: dict[str, str],
) -> None:
    start, end = gps_fy_dates(GPS_FY)
    fy_total = float(fy_df["billed_eur"].sum()) if not fy_df.empty else 0.0
    ytd_total = float(ytd_df["billed_eur"].sum()) if not ytd_df.empty else 0.0
    db_bits = "; ".join(f"{db_label(c)} €{v:,.0f}" for c, v in db_fy.items())
    missing_words = (
        ", ".join(words_for(desc.get(p, p)) for p in missing_fy) if missing_fy else "none"
    )

    lines = [
        "# Parts we billed with no list price — FY2026",
        "",
        "These are billed parts with **no list price**, so **%GM cannot be set**. They are not a stock story and not a piece count. Billed ZPR1 is not a list. Shell oils stayed out.",
        "",
        f"**FY2026 = {start} to {end}.** We billed **€{fy_total:,.2f}** across **{len(fy_df)} parts**. {db_bits}.",
        "",
        "Money first, parts in words. Piece counts are not in this table on purpose.",
        "",
        "## FY2026 by family",
        "",
        *_family_table(fy_df),
        "",
        "## FY2026 by part",
        "",
        *_md_table(fy_df),
        "",
        f"Not in FY2026 (billed only in Jan–Mar 2025, that is FY2025): {missing_words}.",
        "",
        "## FY2027 year-to-date (1 Apr 2026 – 30 Jun 2026) on the same leftover set",
        "",
        f"We billed **€{ytd_total:,.2f}** across **{len(ytd_df)} parts**. Still no list. Still no %GM.",
        "",
    ]
    if ytd_df.empty:
        lines.append("(none)")
    else:
        lines.extend(_md_table(ytd_df))
    lines += [
        "",
        "Parked — Shell lubricants, not this leftover: 550047337, 550047252, 550071985, 550070445, 550070643, 550070645, 550065935.",
        "",
        "Do not quote the calendar-2025 leftover table. That cut mixed two fiscal years and led with pieces.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    residual = _load_residual()
    sales = _load_sales()
    fy_int = sales_fiscal_from_gps_fy(GPS_FY)
    ytd_int = sales_fiscal_from_gps_fy(GPS_FY + 1)
    fy_df = aggregate_no_list(sales, residual, fy_int)
    ytd_df = aggregate_no_list(sales, residual, ytd_int)

    pns = set(residual["part_number"])
    desc = dict(zip(residual["part_number"], residual["description"]))
    missing_fy = sorted(pns - set(fy_df["part_number"]))

    hit_fy = sales[(sales["part_number"].isin(pns)) & (sales["fiscal_year"] == fy_int)]
    db_fy = (
        hit_fy.groupby("distributor_code")["net_sales_value"]
        .sum()
        .sort_values(ascending=False)
    )

    fy_df.to_csv(OUT_CSV, index=False)
    ytd_df.to_csv(OUT_YTD_CSV, index=False)
    write_md(fy_df, ytd_df, db_fy, missing_fy, desc)
    total = float(fy_df["billed_eur"].sum())
    print(f"Wrote {OUT_CSV} and {OUT_MD} ({len(fy_df)} PN, €{total:,.2f} FY{GPS_FY})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
