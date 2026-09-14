#!/usr/bin/env python3
"""Jerome-facing table: 24 hardware PNs with CY2025 billed and no PR00 list price.

Shell 5500* stays parked. No list price invented. Sales-to-dealer qty only where
a year-grain file exists (IUK, ITUK, Ireland, UTI, Greece).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR, SALES_FACT_PARQUET, resolve_mapping_path  # noqa: E402
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import load_sellout_long_pn, normalize_pn  # noqa: E402

YEAR = 2025
SRC = DERIVED_DIR / "no_pr00_gap_remaining_zpr1_check_20260812.csv"
OUT_CSV = DERIVED_DIR / "no_pr00_hardware_cy2025_billed_vs_std.csv"
OUT_MD = DERIVED_DIR / "NO_PR00_HARDWARE_CY2025.md"
STD_DISTS = ("IUK", "ITUK", "IRELAND", "UTI", "GREECE")


def _billed() -> pd.DataFrame:
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[sales["year"] == YEAR].copy()
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    g = s.groupby(["part_number", "distributor_code"], as_index=False).agg(
        billed_qty=("billed_qty", "sum"),
        billed_eur=("net_sales_value", "sum"),
    )
    return g


def _std() -> pd.DataFrame:
    frames = []
    for dist in STD_DISTS:
        df = load_sellout_long_pn(dist, YEAR, DERIVED_DIR)
        if df.empty:
            continue
        df = df.copy()
        df["distributor_code"] = dist
        df = df.rename(columns={"qty_year": "std_qty"})
        frames.append(df[["distributor_code", "part_number", "std_qty"]])
    if not frames:
        return pd.DataFrame(columns=["distributor_code", "part_number", "std_qty"])
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    residual = pd.read_csv(SRC, dtype={"part_number": str})
    residual["part_number"] = residual["part_number"].map(normalize_pn)
    billed = _billed()
    std = _std()

    rows = []
    for _, r in residual.iterrows():
        pn = r["part_number"]
        b = billed[billed["part_number"] == pn]
        billed_eur = float(b["billed_eur"].sum()) if not b.empty else float(r["cy2025_eur"])
        billed_qty = float(b["billed_qty"].sum()) if not b.empty else None
        by_db = (
            "; ".join(
                f"{d}: {q:g} pcs / €{e:,.0f}"
                for d, q, e in b[["distributor_code", "billed_qty", "billed_eur"]].itertuples(
                    index=False, name=None
                )
            )
            if not b.empty
            else "we billed this; account split not mapped"
        )
        s = std[std["part_number"] == pn]
        std_qty = float(s["std_qty"].sum()) if not s.empty else None
        std_by = (
            "; ".join(
                f"{d}: {q:g} pcs"
                for d, q in s[["distributor_code", "std_qty"]].itertuples(index=False, name=None)
            )
            if not s.empty
            else "we do not have their sales to dealer"
        )
        stock = None
        if billed_qty is not None and std_qty is not None:
            stock = std_qty - billed_qty
        rows.append(
            {
                "rank": r["rank"],
                "part_number": pn,
                "description": r["description"],
                "billed_eur": round(billed_eur, 2),
                "billed_qty": billed_qty,
                "billed_by": by_db,
                "std_qty": std_qty,
                "std_by": std_by,
                "stock_pcs": stock,
                "has_zpr1": r["has_zpr1"],
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    total = float(out["billed_eur"].sum())
    lines = [
        "# Hardware with CY2025 billed and no list price",
        "",
        f"24 part numbers. We billed **€{total:,.2f}** in calendar 2025. There is no PR00 list price on these. Billed ZPR1 is not a list price. Shell oils (`5500*`) are not in this list.",
        "",
        "Sales to dealer exists only for Isuzu UK pickup, Isuzu Truck UK, Ireland, UTI, and Greece. For everyone else the sales-to-dealer column is blank. Difference in pieces is stock movement (destock / restock), not lost sales and not a list-price reason. %GM is not shown — there is no list price.",
        "",
        "| part | description | we billed € | we billed pcs | billed to | sales to dealer pcs | sales to dealer where | stock pcs (StD − billed) |",
        "|------|-------------|-------------|---------------|-----------|---------------------|----------------------|--------------------------|",
    ]
    for _, r in out.iterrows():
        bq = "—" if r["billed_qty"] is None or pd.isna(r["billed_qty"]) else f"{r['billed_qty']:g}"
        sq = "—" if r["std_qty"] is None or pd.isna(r["std_qty"]) else f"{r['std_qty']:g}"
        st = "—" if r["stock_pcs"] is None or pd.isna(r["stock_pcs"]) else f"{r['stock_pcs']:g}"
        lines.append(
            f"| {r['part_number']} | {r['description']} | {r['billed_eur']:,.2f} | {bq} | {r['billed_by']} | {sq} | {r['std_by']} | {st} |"
        )
    lines += [
        "",
        "Parked — Shell lubricants, not hardware: 550047337, 550047252, 550071985, 550070445, 550070643, 550070645, 550065935.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_CSV} and {OUT_MD} ({len(out)} PN, €{total:,.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
