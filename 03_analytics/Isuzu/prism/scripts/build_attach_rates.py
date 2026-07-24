#!/usr/bin/env python3
"""
Attach rates — co-purchase lift between service categories at ITUK dealer level.

Tests cross-sell structure (incl. the lubricants gateway thesis) on observed
CY2025 dealer sell-out instead of asserting it:

    lift(A -> B) = P(dealer buys B | dealer buys A) / P(dealer buys B)

Categories: PMS categories from genuine_bvp_crossref + a `lubricants` bucket
detected by description keywords (viscosity grades / LUBE / GREASE / COOLANT)
— the lubricants tag is a KEYWORD HEURISTIC, flagged in the output.

This is CO-PURCHASE within one year, n = ITUK dealers — association, not
causality. Cells with fewer than `min_dealers_per_cell` base dealers are
suppressed.

Output: Data/derived/attach_rates.csv
Run from prism/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import AIM_PN_CLASSIFICATION_CSV, DERIVED_DIR, GENUINE_BVP_CROSSREF_CSV  # noqa: E402
from modules.dealer_sales_loader import load_ituk_dealer_sales  # noqa: E402

OUT_CSV = DERIVED_DIR / "attach_rates.csv"
ASSUMPTIONS = PRISM_ROOT / "data" / "decision_model_assumptions.yaml"

LUBE_RE = re.compile(r"(\b\d{1,2}W\d{2}\b|15W40|10W40|5W30|0W20|LUBE|GREASE|COOLANT|ANTIFREEZE)", re.I)


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def main() -> int:
    cfg = yaml.safe_load(ASSUMPTIONS.read_text(encoding="utf-8"))["attach_rates"]
    min_n = int(cfg["min_dealers_per_cell"])

    df = load_ituk_dealer_sales(2025)
    if df.empty:
        print("ERROR: ITUK dealer sell-out file not found")
        return 1
    df = df[df["qty_year"] > 0].copy()
    df["_pn"] = _norm(df["part_number"])

    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    cat_map: dict[str, str] = {}
    for col in ("genuine_pn", "bvp_pn"):
        sub = xref.dropna(subset=[col, "pms_category"])
        cat_map.update(dict(zip(_norm(sub[col]), sub["pms_category"])))

    desc = pd.read_csv(
        AIM_PN_CLASSIFICATION_CSV, usecols=["part_number", "description_norm"], dtype=str
    )
    desc["_pn"] = _norm(desc["part_number"])
    lube_pns = set(desc[desc["description_norm"].fillna("").str.contains(LUBE_RE)]["_pn"])

    df["category"] = df["_pn"].map(cat_map)
    df.loc[df["_pn"].isin(lube_pns), "category"] = "lubricants"
    tagged = df.dropna(subset=["category"])

    bought = tagged.groupby(["dealer_name", "category"])["qty_year"].sum().reset_index()
    basket = bought.pivot_table(
        index="dealer_name", columns="category", values="qty_year", aggfunc="sum"
    ).notna()

    # Baseline population = dealers with ≥1 mapped-category purchase.
    # Using all sell-out dealers (incl. unmapped-only) understates P(B) and
    # inflates every lift by ~dealers_all / basket_n.
    dealers_all = int(basket.shape[0])
    cats = sorted(basket.columns)
    rows = []
    for a in cats:
        n_a = int(basket[a].sum())
        for b in cats:
            if a == b:
                continue
            n_b = int(basket[b].sum())
            p_b = n_b / dealers_all
            if n_a < min_n or p_b <= 0:
                continue
            n_ab = int((basket[a] & basket[b]).sum())
            p_b_given_a = n_ab / n_a
            rows.append(
                {
                    "distributor_code": "ITUK",
                    "year": 2025,
                    "category_a": a,
                    "category_b": b,
                    "dealers_total": dealers_all,
                    "dealers_with_a": n_a,
                    "dealers_with_both": n_ab,
                    "p_b_given_a": round(p_b_given_a, 3),
                    "p_b_baseline": round(p_b, 3),
                    "attach_lift": round(p_b_given_a / p_b, 2),
                    "method_note": (
                        "co-purchase within CY2025, dealer level; association not "
                        "causality; lubricants = keyword heuristic"
                    ),
                }
            )

    out = pd.DataFrame(rows).sort_values("attach_lift", ascending=False)
    out.to_csv(OUT_CSV, index=False)
    n_lube = len(out[out["category_a"] == "lubricants"])
    print(
        f"attach: {len(out)} pairs -> {OUT_CSV.name} | {dealers_all} dealers | "
        f"{n_lube} lubricants->X pairs"
    )
    if n_lube:
        top = out[out["category_a"] == "lubricants"].head(3)
        for _, r in top.iterrows():
            print(
                f"  lube -> {r['category_b']}: P={r['p_b_given_a']:.0%} vs base "
                f"{r['p_b_baseline']:.0%} (lift {r['attach_lift']}x, n_a={r['dealers_with_a']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
