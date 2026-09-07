#!/usr/bin/env python3
"""EQ-HIT pull priority from CY2025 PMS gaps + top billed PNs."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import ISZE_ROOT  # noqa: E402
from modules.pms_engine import classify_pms_sales  # noqa: E402

DERIVED = ISZE_ROOT / "01_data" / "00_derived"


def main() -> int:
    sf = pd.read_parquet(DERIVED / "sales_fact.parquet")
    sf = sf[sf["year"] == 2025].copy()
    c = classify_pms_sales(sf)
    c = c[c["is_pms"] == True]  # noqa: E712

    cat = c.groupby("pms_category", as_index=False).agg(
        qty=("billed_qty", "sum"),
        eur=("net_sales_value", "sum"),
        pn_n=("part_number", "nunique"),
    )
    v2 = pd.read_csv(DERIVED / "pms_capture_by_db_year_v2_mileage.csv")
    exp = (
        v2[(v2["year"] == 2025) & (v2["line_type"] == "total")]
        .groupby("pms_category", as_index=False)
        .agg(
            expected=("expected_qty_v2", "sum"),
            actual_cap=("actual_qty", "sum"),
            gap_eur=("revenue_gap_v2_eur", "sum"),
        )
    )
    m = cat.merge(exp, on="pms_category", how="outer")
    m["gap_qty"] = (m["expected"] - m["actual_cap"]).fillna(0)
    m["capture"] = m["actual_cap"] / m["expected"]
    m = m.sort_values("gap_eur", ascending=False)
    m["eqhit_priority"] = range(1, len(m) + 1)

    tops = []
    for catn, g in c.groupby("pms_category"):
        t = (
            g.groupby(["part_number", "description"], as_index=False)
            .agg(qty=("billed_qty", "sum"), eur=("net_sales_value", "sum"))
            .sort_values("eur", ascending=False)
            .head(8)
        )
        t["pms_category"] = catn
        tops.append(t)
    top = pd.concat(tops, ignore_index=True)

    out = m[
        [
            "eqhit_priority",
            "pms_category",
            "gap_eur",
            "gap_qty",
            "expected",
            "actual_cap",
            "capture",
            "qty",
            "eur",
            "pn_n",
        ]
    ].copy()
    out.to_csv(DERIVED / "eqhit_priority_ranking_cy2025.csv", index=False)
    top.to_csv(DERIVED / "eqhit_priority_top_pns_cy2025.csv", index=False)

    lines = [
        "# EQ-HIT pull priority (CY2025)",
        "",
        "**Mode B** · attack order by V2 **EUR revenue gap** (largest unpaid expected demand first).",
        "Full EQ-HIT catalogue accepted (Jerome) — this ranking is the **sequence**, not a top-20 cut.",
        "",
        "| Rank | Category | EUR gap | Capture | Gap qty | Example PNs (top billed EUR) |",
        "|-----:|----------|--------:|--------:|--------:|------------------------------|",
    ]
    for _, r in out.iterrows():
        t5 = top[top["pms_category"] == r["pms_category"]].head(3)
        pn = ", ".join(str(x) for x in t5["part_number"].tolist())
        cap = 100.0 * float(r["capture"]) if pd.notna(r["capture"]) else 0.0
        gap = float(r["gap_eur"]) if pd.notna(r["gap_eur"]) else 0.0
        gq = float(r["gap_qty"]) if pd.notna(r["gap_qty"]) else 0.0
        lines.append(
            f"| {int(r['eqhit_priority'])} | {r['pms_category']} | {gap:,.0f} | "
            f"{cap:.1f}% | {gq:,.0f} | {pn} |"
        )
    lines += [
        "",
        "Sources: `pms_capture_by_db_year_v2_mileage.csv` + PMS-classified `sales_fact` CY2025.",
        "PN detail: `eqhit_priority_top_pns_cy2025.csv`.",
        "",
        "Trooper interval lock: same as D-Max RT (see `gps_pms_v2_config.yaml`).",
        "",
    ]
    (DERIVED / "eqhit_priority_ranking_cy2025.md").write_text("\n".join(lines), encoding="utf-8")
    print(out[["eqhit_priority", "pms_category", "gap_eur"]].to_string(index=False))
    print("OK", DERIVED / "eqhit_priority_ranking_cy2025.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
