# -*- coding: utf-8 -*-
"""Colleague pack: merge all sales-to-dealer long files into one folder + Excel.

Writes under 01_data/15_gpt_safe/Sales_to_Dealer_colleagues_20260924/
Does not touch raw billing. Does not rebuild dashboards.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "15_gpt_safe" / "Sales_to_Dealer_colleagues_20260924"

# Network rollup of ITUK CY2025 — same year as dealer-level ITUK_CY2025. Do not add both.
EXCLUDE_FROM_MERGE = {
    "dealer_sellout_long_ITUK_network_CY2025.csv",
}

DISPLAY = {
    "IUK": "Isuzu UK pickup (D-Max)",
    "ITUK": "Isuzu Truck UK",
    "IRELAND": "Isuzu Ireland",
    "UTI": "UTI Israel",
    "GREECE": "Greece (Petros)",
    "PORTUGAL": "Portugal",
    "ROMANIA": "Romania",
}

COL_ORDER = [
    "distributor_name",
    "distributor_code",
    "year",
    "period",
    "period_grain",
    "part_number",
    "part_number_raw",
    "description",
    "qty",
    "dealer_name",
    "grain",
    "vehicle_scope",
    "flags",
    "source_file",
    "merge_source_file",
]


def _load_long_files() -> tuple[pd.DataFrame, list[dict]]:
    files = sorted(DERIVED.glob("dealer_sellout_long_*.csv"))
    if not files:
        raise FileNotFoundError("no dealer_sellout_long_*.csv")

    frames: list[pd.DataFrame] = []
    inventory: list[dict] = []
    for f in files:
        part = pd.read_csv(f, low_memory=False)
        rows = int(len(part))
        included = f.name not in EXCLUDE_FROM_MERGE
        inventory.append(
            {
                "file": f.name,
                "rows": rows,
                "mb": round(f.stat().st_size / 1e6, 2),
                "included_in_merge": "yes" if included else "no — network rollup of ITUK CY2025 (dealer-level file already included)",
            }
        )
        if not included:
            continue
        part.insert(0, "merge_source_file", f.name)
        frames.append(part)

    merged = pd.concat(frames, ignore_index=True, sort=False)
    code = merged["distributor_code"].astype(str).str.strip().str.upper()
    merged.insert(0, "distributor_name", code.map(DISPLAY).fillna(code))
    # Stable column order; keep any extras at the end
    front = [c for c in COL_ORDER if c in merged.columns]
    rest = [c for c in merged.columns if c not in front]
    merged = merged[front + rest]
    return merged, inventory


def _coverage(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby(
            ["distributor_name", "distributor_code", "year", "period_grain", "grain"],
            dropna=False,
        )
        .agg(
            rows=("qty", "size"),
            qty_sum=("qty", "sum"),
            part_numbers=("part_number", "nunique"),
            dealers=("dealer_name", lambda s: s.dropna().astype(str).str.strip().ne("").sum()),
            periods=("period", "nunique"),
        )
        .reset_index()
        .sort_values(["distributor_code", "year", "period_grain", "grain"])
    )
    return g


def _readme_rows(built_utc: str, n_rows: int, n_files: int) -> pd.DataFrame:
    lines = [
        ("Title", "Sales to dealer — merged extract for colleagues"),
        ("Built (UTC)", built_utc),
        ("Folder", str(OUT)),
        ("", ""),
        ("What this is", "Parts sold by the distributor into their dealer network (distributor → dealer)."),
        ("What this is not", "Not ISZE billing to the distributor. Not warranty. Not a full network — coverage is partial."),
        ("", ""),
        ("Distributors included", "; ".join(DISPLAY[k] for k in ("IUK", "ITUK", "IRELAND", "UTI", "GREECE", "PORTUGAL", "ROMANIA"))),
        ("Source files merged", str(n_files)),
        ("Detail rows", f"{n_rows:,}"),
        ("", ""),
        (
            "IMPORTANT — do not double-count",
            "The detail sheet has both monthly rows and year / YTD rollup rows (see period_grain). "
            "Never add year rows on top of month rows for the same distributor and year.",
        ),
        (
            "IMPORTANT — quantity vs euro",
            "Most sources are quantity only (pieces). A gasket and a cab are both one unit. "
            "Do not rank markets or parts on pieces alone.",
        ),
        (
            "IMPORTANT — entities",
            "Isuzu UK pickup (IUK) is not Isuzu Truck UK (ITUK). "
            "UTI Israel is not UMI. Isuzu Ireland is not IUK.",
        ),
        (
            "Greece",
            "CY2025 only; typically Apr–Dec in the source (partial calendar year).",
        ),
        (
            "Romania",
            "CY2026 Jan–Aug only. No CY2025 file. Accessory / non-10-digit codes are on a separate sheet.",
        ),
        (
            "ITUK network file",
            "dealer_sellout_long_ITUK_network_CY2025.csv is excluded from the merge "
            "(network rollup of the same year already present at dealer grain).",
        ),
        ("", ""),
        ("Sheets in the workbook", ""),
        ("00_Read_me", "This note"),
        ("01_Coverage", "Row / qty / part-number counts by distributor, year, and period grain"),
        ("02_All_detail", "Full merged table (use filters; respect period_grain)"),
        ("03_By_distributor", "Same detail, one sheet per distributor (easier to mail)"),
        ("Romania_unmapped", "Accessory codes that are not 10-digit Isuzu part numbers"),
    ]
    return pd.DataFrame(lines, columns=["Topic", "Detail"])


def _write_workbook(df: pd.DataFrame, coverage: pd.DataFrame, inventory: list[dict], built_utc: str) -> Path:
    path = OUT / "Sales_to_Dealer_merged.xlsx"
    readme = _readme_rows(built_utc, len(df), sum(1 for i in inventory if i["included_in_merge"].startswith("yes")))
    inv = pd.DataFrame(inventory)

    unmapped_path = DERIVED / "dealer_sellout_unmapped_codes_ROMANIA_CY2026YTD.csv"
    unmapped = pd.read_csv(unmapped_path) if unmapped_path.exists() else None

    # xlsxwriter is much faster for 300k+ rows than openpyxl default
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        readme.to_excel(writer, sheet_name="00_Read_me", index=False)
        coverage.to_excel(writer, sheet_name="01_Coverage", index=False)
        inv.to_excel(writer, sheet_name="01b_Source_files", index=False)
        df.to_excel(writer, sheet_name="02_All_detail", index=False)

        for code, name in DISPLAY.items():
            sub = df[df["distributor_code"].astype(str).str.upper() == code]
            if sub.empty:
                continue
            # Excel sheet names max 31 chars
            sheet = {
                "IUK": "IUK_pickup",
                "ITUK": "ITUK_truck",
                "IRELAND": "Ireland",
                "UTI": "UTI_Israel",
                "GREECE": "Greece",
                "PORTUGAL": "Portugal",
                "ROMANIA": "Romania",
            }[code]
            sub.to_excel(writer, sheet_name=sheet, index=False)

        if unmapped is not None and not unmapped.empty:
            unmapped.to_excel(writer, sheet_name="Romania_unmapped", index=False)

        for sheet_name, worksheet in writer.sheets.items():
            worksheet.freeze_panes(1, 0)
            if sheet_name != "00_Read_me":
                last_row = max(getattr(worksheet, "dim_rowmax", None) or 0, 0)
                last_col = max(getattr(worksheet, "dim_colmax", None) or 0, 0)
                if last_row > 0 or last_col > 0:
                    worksheet.autofilter(0, 0, last_row, last_col)

        for sn, widths in {
            "00_Read_me": [28, 90],
            "01_Coverage": [28, 14, 8, 12, 12, 10, 12, 12, 10, 10],
            "01b_Source_files": [48, 10, 8, 70],
        }.items():
            ws = writer.sheets[sn]
            for i, w in enumerate(widths):
                ws.set_column(i, i, w)

        for sn in ["02_All_detail"] + [
            "IUK_pickup",
            "ITUK_truck",
            "Ireland",
            "UTI_Israel",
            "Greece",
            "Portugal",
            "Romania",
            "Romania_unmapped",
        ]:
            if sn not in writer.sheets:
                continue
            ws = writer.sheets[sn]
            ws.set_column(0, 0, 26)  # distributor_name
            ws.set_column(1, 1, 12)
            ws.set_column(5, 6, 14)  # part numbers
            ws.set_column(7, 7, 36)  # description
            ws.set_column(9, 9, 28)  # dealer

    return path


def _write_readme_txt(built_utc: str, xlsx_name: str, n_rows: int) -> Path:
    path = OUT / "README.txt"
    text = f"""Sales to dealer — merged extract for colleagues
Built (UTC): {built_utc}

Open: {xlsx_name}

What this is
  Parts sold by the distributor into their dealer network (distributor to dealer).

What this is not
  Not ISZE billing to the distributor. Not warranty claims.
  Coverage is only the distributors below — not the full ISZE network.

Distributors in this pack
  - Isuzu UK pickup / D-Max (IUK)
  - Isuzu Truck UK (ITUK)
  - Isuzu Ireland
  - UTI Israel (not UMI)
  - Greece (Petros)
  - Portugal
  - Romania (2026 Jan–Aug only)

Detail rows: {n_rows:,}

Do not double-count
  The detail has monthly rows and year / YTD rollup rows (column period_grain).
  Never add year rows on top of month rows for the same distributor and year.

Quantity is not a ranking
  Most lines are pieces only. A gasket and a cab are both one unit.
  Use euros from billing when you need commercial weight.

Entities that must stay separate
  IUK is not ITUK. UTI is not UMI. Ireland is not IUK.
"""
    path.write_text(text, encoding="utf-8", newline="\r\n")
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    built_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    df, inventory = _load_long_files()
    coverage = _coverage(df)

    # Full CSV beside Excel (same merge; useful if Excel is slow)
    csv_path = OUT / "Sales_to_Dealer_merged.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")

    xlsx_path = _write_workbook(df, coverage, inventory, built_utc)
    _write_readme_txt(built_utc, xlsx_path.name, len(df))

    meta = {
        "built_utc": built_utc,
        "folder": str(OUT),
        "rows": int(len(df)),
        "xlsx_mb": round(xlsx_path.stat().st_size / 1e6, 2),
        "csv_mb": round(csv_path.stat().st_size / 1e6, 2),
        "distributors": sorted(df["distributor_code"].astype(str).str.upper().unique().tolist()),
        "excluded": sorted(EXCLUDE_FROM_MERGE),
    }
    (OUT / "_build_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("OK", xlsx_path)
    print("rows", len(df), "xlsx_mb", meta["xlsx_mb"], "csv_mb", meta["csv_mb"])
    print("distributors", meta["distributors"])


if __name__ == "__main__":
    main()
