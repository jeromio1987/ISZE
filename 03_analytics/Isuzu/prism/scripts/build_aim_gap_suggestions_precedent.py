#!/usr/bin/env python3
"""
Build a new aim_gap_suggestions_<date>.csv for residual (placeholder-classified) PNs
using description precedent: inherit the workbook class of already-classified PNs
that share the same normalized description (exact desc first, then the root
before ';'). Only emits a suggestion when the precedent pool is dominated by a
single L1 (>=70% by EUR) with minimum support — no keyword guessing.

Merges the previous aim_gap_suggestions_*.csv rows (kept verbatim) so the
classifier, which reads only the newest file, does not lose them. On PN
conflict the precedent row wins.

  python scripts/build_aim_gap_suggestions_precedent.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR, resolve_mapping_path  # noqa: E402
from modules.aim_pn_classifier import PLACEHOLDER_L1, load_aim_pn_classification  # noqa: E402
from modules.bvp_analytics import normalize_pn_value  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

DOMINANCE_MIN = 0.70
SUPPORT_MIN_EUR = 2000.0
SUPPORT_MIN_PNS = 2
CONFIDENCE_BASE = 3.0  # classifier applies suggestions at confidence >= 3.0


def _is_placeholder(val: object) -> bool:
    s = "" if val is None or pd.isna(val) else str(val).strip().lower()
    return s in ("", "nan") or s in PLACEHOLDER_L1


def _desc_root(desc: str) -> str:
    return desc.split(";")[0].strip()


def main() -> int:
    cls = load_aim_pn_classification()
    if cls.empty:
        print("ERROR: aim_pn_classification.csv missing — run build_aim_pn_classification.py")
        return 1

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _src = load_prism_sales(df_map)
    sales = sales[sales["line_kind"] == "part"].copy()
    sales = sales[sales["year"].isin([2024, 2025])]
    sales["_pn"] = sales["part_number"].map(lambda x: normalize_pn_value(x) or "")

    rev = sales.groupby("_pn").agg(
        revenue_24_25=("net_sales_value", "sum"),
        description=("description", "first"),
    )
    rev = rev[rev["revenue_24_25"] > 0]
    rev["desc_norm"] = rev["description"].fillna("").astype(str).str.strip().str.upper()

    joined = rev.join(cls[["aim_l1", "aim_l2", "catalog_l1", "aim_source"]], how="left")

    # Residual = workbook AND catalog both placeholder (post-fallback still open)
    residual = joined[
        joined["aim_l1"].map(_is_placeholder) & joined["catalog_l1"].map(_is_placeholder)
    ].copy()

    # Precedent pool = PNs with a real workbook class, weighted by EUR
    pool = joined[
        (joined["aim_source"] == "aim_workbook") & ~joined["aim_l1"].map(_is_placeholder)
    ].copy()
    pool["desc_root"] = pool["desc_norm"].map(_desc_root)

    def precedent_for(keys: pd.Series, key_col: str) -> pd.DataFrame:
        """Majority L1/L2 by EUR per key with dominance + support stats."""
        p = pool[pool[key_col].isin(set(keys))]
        if p.empty:
            return pd.DataFrame()
        g = p.groupby([key_col, "aim_l1", "aim_l2"])["revenue_24_25"].sum().reset_index()
        tot = g.groupby(key_col)["revenue_24_25"].sum().rename("key_total")
        npns = p.groupby(key_col)["_pn"].nunique().rename("support_pns") if "_pn" in p.columns else (
            p.groupby(key_col).size().rename("support_pns")
        )
        top = g.sort_values("revenue_24_25", ascending=False).drop_duplicates(key_col)
        top = top.join(tot, on=key_col).join(npns, on=key_col)
        top["dominance"] = top["revenue_24_25"] / top["key_total"]
        return top.set_index(key_col)

    pool = pool.reset_index()
    residual["desc_root"] = residual["desc_norm"].map(_desc_root)

    prec_exact = precedent_for(residual["desc_norm"], "desc_norm")
    prec_root = precedent_for(residual["desc_root"], "desc_root")

    rows = []
    for pn, r in residual.sort_values("revenue_24_25", ascending=False).iterrows():
        hit, method = None, None
        if not prec_exact.empty and r["desc_norm"] in prec_exact.index:
            hit, method = prec_exact.loc[r["desc_norm"]], "desc_exact"
        elif not prec_root.empty and r["desc_root"] and r["desc_root"] in prec_root.index:
            hit, method = prec_root.loc[r["desc_root"]], "desc_root"
        if hit is None:
            continue
        if hit["dominance"] < DOMINANCE_MIN:
            continue
        if hit["key_total"] < SUPPORT_MIN_EUR and hit["support_pns"] < SUPPORT_MIN_PNS:
            continue
        rows.append(
            {
                "pn": pn,
                "description": r["description"],
                "price_eur": "",
                "revenue_cy25_eur": round(float(r["revenue_24_25"]), 2),
                "current_l1": r["aim_l1"] if pd.notna(r["aim_l1"]) else "",
                "sug1_l1": hit["aim_l1"],
                "sug1_l2": hit["aim_l2"],
                "sug1_desc": f"precedent:{method} dom={hit['dominance']:.2f} "
                f"pool_eur={hit['key_total']:.0f} pool_pns={int(hit['support_pns'])}",
                "sug1_price": "",
                "sug1_combined": round(float(hit["dominance"]), 4),
                "confidence": round(CONFIDENCE_BASE + float(hit["dominance"]), 2),
                "eq_hit": "",
                "validated": f"precedent_desc_{date.today():%Y%m%d}",
            }
        )

    new = pd.DataFrame(rows)
    print(f"Precedent suggestions: {len(new)} PNs, EUR {new['revenue_cy25_eur'].sum():,.0f} (2024+2025)"
          if not new.empty else "Precedent suggestions: none")

    # merge previous file (rows kept verbatim; precedent wins on conflict)
    prev_files = sorted(DERIVED_DIR.glob("aim_gap_suggestions_*.csv"))
    out_path = DERIVED_DIR / f"aim_gap_suggestions_{date.today():%Y%m%d}.csv"
    prev = pd.read_csv(prev_files[-1], dtype=str) if prev_files and prev_files[-1] != out_path else pd.DataFrame()
    if not prev.empty:
        prev["_pn"] = prev["pn"].map(lambda x: normalize_pn_value(x) or "")
        new_keys = set(new["pn"]) if not new.empty else set()
        prev = prev[~prev["_pn"].isin(new_keys)].drop(columns=["_pn"])
        merged = pd.concat([new, prev], ignore_index=True)
    else:
        merged = new

    merged.to_csv(out_path, index=False)
    print(f"  -> {len(merged):,} rows -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
