#!/usr/bin/env python3
"""
Re-derive derived/bvp_downtrade_gp.csv — genuine-vs-BVP GP gap by PMS category.

Why this script exists
----------------------
The original one-off builder for this file was lost; only readers remain
(Preparation Meetings/UTI/_build/*). The file blends two things:

  * qty/rev splits per pms_category — REAL sales, classified genuine vs BVP.
    These were corrupted by the broken bvp_pn_dimension line_type (genuine
    catalog PNs tagged "bvp"), so they must be rebuilt from the authoritative
    genuine_bvp_crossref.csv.
  * genuine_gp_pct / bvp_gp_pct per category — MARGIN ASSUMPTIONS. There is no
    cost column in sales_fact, so these cannot be re-derived. They are NOT
    affected by the classification bug, so we PRESERVE them verbatim from the
    existing file and only recompute the quantities that depend on them.

Scope: CY2025, all mapped distributors (matches the original file).
Classification: a PN in crossref bvp_pn is BVP; a PN in genuine_pn is genuine.

downtrade_gp_gap_eur = qty_bvp * (genuine_gp_per_unit - bvp_gp_per_unit)
  i.e. GP forgone because those BVP units were not sold as genuine.

Run from prism/ after build_bvp_p0_p1.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    resolve_mapping_path,
)
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_CSV = DERIVED_DIR / "bvp_downtrade_gp.csv"
YEAR = 2025


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def main() -> int:
    if not OUT_CSV.exists():
        print(f"  {OUT_CSV.name} missing — cannot recover margin assumptions; abort")
        return 1

    # Margin assumptions (genuine_gp_pct / bvp_gp_pct) are preserved from the
    # existing file; everything else is recomputed from corrected classification.
    old = pd.read_csv(OUT_CSV)
    margins = old.set_index("pms_category")[["genuine_gp_pct", "bvp_gp_pct"]]

    xref = pd.read_csv(
        GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str}
    )
    gcat = xref.dropna(subset=["genuine_pn"]).assign(_pn=lambda d: _norm(d["genuine_pn"]))
    bcat = xref.dropna(subset=["bvp_pn"]).assign(_pn=lambda d: _norm(d["bvp_pn"]))
    cat_map = (
        pd.concat([gcat[["_pn", "pms_category"]], bcat[["_pn", "pms_category"]]])
        .loc[lambda d: d["pms_category"].astype(str).ne("") & d["pms_category"].notna()]
        .drop_duplicates("_pn")
        .set_index("_pn")["pms_category"]
    )
    gen_pns = set(gcat["_pn"])
    bvp_pns = set(bcat["_pn"])

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df, src = load_prism_sales(df_map)
    print(f"downtrade: {len(df):,} sales rows from {src}")

    df = df[df["year"] == YEAR].copy()
    df = df[~df["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    df["_pn"] = _norm(df["part_number"])
    df["cat"] = df["_pn"].map(cat_map)
    df = df[df["cat"].notna()].copy()
    df["cls"] = df["_pn"].map(
        lambda p: "genuine" if p in gen_pns else ("bvp" if p in bvp_pns else None)
    )
    df = df[df["cls"].notna()]

    rows: list[dict] = []
    for cat, sub in df.groupby("cat"):
        if cat not in margins.index:
            continue  # no margin assumption on record for this category
        g = sub[sub["cls"] == "genuine"]
        b = sub[sub["cls"] == "bvp"]
        qty_g = float(g["billed_qty"].sum())
        qty_b = float(b["billed_qty"].sum())
        rev_g = float(g["net_sales_value"].sum())
        rev_b = float(b["net_sales_value"].sum())
        if qty_b <= 0 or qty_g <= 0:
            continue
        gen_pct = float(margins.loc[cat, "genuine_gp_pct"])
        bvp_pct = float(margins.loc[cat, "bvp_gp_pct"])
        gen_sp = rev_g / qty_g
        bvp_sp = rev_b / qty_b
        gen_gpu = gen_sp * gen_pct
        bvp_gpu = bvp_sp * bvp_pct
        rows.append(
            {
                "pms_category": cat,
                "qty_bvp": round(qty_b, 1),
                "qty_genuine": round(qty_g, 1),
                "rev_bvp": round(rev_b, 2),
                "rev_genuine": round(rev_g, 2),
                "gp_bvp": round(bvp_gpu * qty_b, 2),
                "gp_genuine": round(gen_gpu * qty_g, 2),
                "genuine_gp_per_unit": round(gen_gpu, 2),
                "genuine_gp_pct": gen_pct,
                "bvp_gp_per_unit": round(bvp_gpu, 2),
                "bvp_gp_pct": bvp_pct,
                "downtrade_gp_gap_eur": round(qty_b * (gen_gpu - bvp_gpu), 0),
            }
        )

    out = pd.DataFrame(rows).sort_values("pms_category").reset_index(drop=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"  -> {len(out)} categories -> {OUT_CSV}")
    print(out[["pms_category", "qty_genuine", "qty_bvp", "downtrade_gp_gap_eur"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
