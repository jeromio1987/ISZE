#!/usr/bin/env python3
"""
AIM taxonomy fixes + corrected master + PRIORITY LIST for the sales-analysis agent.

Defects found by full review (2026-09-17) and how each is handled.

  FIXED (structural, safe, reversible via the mapping table):
    F1  Brakes: "Disc & Drum" and "Discs & Drums" are the same concept.
        -> merge "Disc & Drum" into "Discs & Drums".
    F2  Maintenance Service: "Filters" (EUR1.57M) reads as a parent total while
        its own children (Air/Oil/Fuel Filter) sit beside it. It is NOT a total.
        -> rename to "Filters (unspecified)" so no reader sums it as the parent.
    F3  Electrical: "Sensors" and "Sensors & Switches" are the same concept.
        -> merge "Sensors" into "Sensors & Switches".
    F4  Electrical: "Starting & Charging" and "Charging" overlap.
        -> merge "Starting & Charging" into "Charging".
    F5  Lighting was split across Accident & Body > Lamps and Electrical > Lighting,
        and lamps are a service business, not crash damage.
        -> new L1 "Lighting" holding both (EUR 2.59M). Accident & Body drops to EUR 6.34M.
    F6  Brakes: "Friction" is AIM jargon for pads, shoes and linings.
        -> rename to "Pads & Shoes" (Jerome 2026-09-17 — common English).

  FLAGGED, NOT FORCED (needs description rules - doing it blind would invent):
    Q1  Bumpers: L2 "Bumpers" plus bumper lines inside "Panels".
    Q2  Lubricants: "Fluids Chemicals > Lubricants" vs the separate "Lubrication" L1.
    Q3  Filters appear under four L1s (Maintenance, Fuel System > Filtration,
        Cabin Interior > HVAC Filters, Lubrication > Oil Filter System).

Outputs
-------
  01_data/00_derived/aim_taxonomy_fixes_v1.csv     the mapping, auditable
  01_data/00_derived/aim_master_v2.csv             corrected master
  02_dashboards/pricing/AIM_PRIORITY_LIST.csv      the priority list (flat)
  02_dashboards/pricing/AIM_PRIORITY_LIST.xlsx     the priority list (workbook)
  01_data/00_derived/aim_master_v2.meta.json       coverage + fix log
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
PRICING_DIR = ISZE / "02_dashboards" / "pricing"

FIX_CSV = D / "aim_taxonomy_fixes_v1.csv"
MASTER_V2 = D / "aim_master_v2.csv"
META_V2 = D / "aim_master_v2.meta.json"
PRIO_CSV = PRICING_DIR / "AIM_PRIORITY_LIST.csv"
PRIO_XLSX = PRICING_DIR / "AIM_PRIORITY_LIST.xlsx"

# L2 renames/merges: (level, old_L1, old_L2) -> new_L1, new_L2
L2_FIXES = {
    ("Brakes", "Disc & Drum"): ("Brakes", "Discs & Drums"),
    ("Brakes", "Friction"): ("Brakes", "Pads & Shoes"),
    ("Maintenance Service", "Filters"): ("Maintenance Service", "Filters (unspecified)"),
    ("Electrical", "Sensors"): ("Electrical", "Sensors & Switches"),
    ("Electrical", "Starting & Charging"): ("Electrical", "Charging"),
}
# L2s to relocate to a new L1 (Lighting consolidation)
MOVE_TO_LIGHTING = {
    ("Accident & Body", "Lamps"): ("Lighting", "Lamps"),
    ("Electrical", "Lighting"): ("Lighting", "Lighting"),
}


def clean(s: object) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def main() -> int:
    m = pd.read_csv(D / "aim_master_v1.csv", dtype=str, low_memory=False)
    m["eur"] = pd.to_numeric(m["l12m_billed_eur"], errors="coerce").fillna(0)
    m["aim_l1"] = m["aim_l1"].map(clean)
    m["aim_l2"] = m["aim_l2"].map(clean)
    m["aim_l3"] = m["aim_l3"].map(clean)

    # ------------------------------------------------------------ apply fixes
    fix_rows: list[dict] = []
    before = m[m["has_aim"] == "1"].groupby("aim_l1")["eur"].sum().to_dict()

    new_l1, new_l2 = [], []
    for _, r in m.iterrows():
        a1, a2 = r["aim_l1"], r["aim_l2"]
        key = (a1, a2)
        if key in L2_FIXES:
            n1, n2 = L2_FIXES[key]
            new_l1.append(n1); new_l2.append(n2)
            fix_rows.append({"fix": "L2_MERGE", "from_l1": a1, "from_l2": a2,
                             "to_l1": n1, "to_l2": n2, "part_number": r["part_number"],
                             "eur": r["eur"],
                             "reason": ("AIM jargon -> common English"
                                        if a2 == "Friction"
                                        else "duplicate / parent-as-sibling")})
        elif key in MOVE_TO_LIGHTING:
            n1, n2 = MOVE_TO_LIGHTING[key]
            new_l1.append(n1); new_l2.append(n2)
            fix_rows.append({"fix": "L1_SPLIT", "from_l1": a1, "from_l2": a2,
                             "to_l1": n1, "to_l2": n2, "part_number": r["part_number"],
                             "eur": r["eur"], "reason": "service lighting out of crash class"})
        else:
            new_l1.append(a1); new_l2.append(a2)

    m["aim_l1_fixed"] = new_l1
    m["aim_l2_fixed"] = new_l2
    m["aim_changed"] = [
        "1" if (a != b or c != d) else "0"
        for a, b, c, d in zip(m["aim_l1"], m["aim_l1_fixed"], m["aim_l2"], m["aim_l2_fixed"])
    ]
    # Keep the raw workbook column aligned on the Friction rename so the old
    # jargon does not linger in exports that still read aim_l2.
    m.loc[m["aim_l2"] == "Friction", "aim_l2"] = "Pads & Shoes"
    m.to_csv(MASTER_V2, index=False)

    fixes = pd.DataFrame(fix_rows)
    if len(fixes):
        summary = (fixes.groupby(["fix", "from_l1", "from_l2", "to_l1", "to_l2", "reason"])
                   .agg(rows=("part_number", "size"), eur=("eur", "sum")).reset_index())
        summary.to_csv(FIX_CSV, index=False)
        print("FIXES APPLIED")
        print(summary.round(0).to_string(index=False))
    print()

    after = m[m["has_aim"] == "1"].groupby("aim_l1_fixed")["eur"].sum().to_dict()
    print("L1 BEFORE -> AFTER (EUR)")
    for k in sorted(set(before) | set(after), key=lambda x: -after.get(x, 0)):
        b, a = before.get(k, 0), after.get(k, 0)
        mark = "  <== changed" if abs(b - a) > 1 else ""
        print(f"  {k:<26} {b:>12,.0f} -> {a:>12,.0f}{mark}")
    print()

    # ------------------------------------------------------------ priority list
    wb = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
    p = wb[wb["in_scope"].astype(str).str.lower().isin(["true", "1"])].copy()
    p["pn"] = p["part_number"].str.strip()
    for c in ("net_sales_value", "billed_qty", "value_eur_step", "bp_new_jpy",
              "bp_prior_revised", "delta_pct"):
        p[c] = pd.to_numeric(p[c], errors="coerce")

    mm = m.drop_duplicates("part_number").set_index("part_number")
    g = p.groupby("pn").agg(
        billed_description=("billed_description", "first"),
        distributors=("distributor_code", "nunique"),
        l12m_qty=("billed_qty", "sum"),
        l12m_billed_eur=("net_sales_value", "sum"),
        bp_new_jpy=("bp_new_jpy", "median"),
        bp_prior_jpy=("bp_prior_revised", "median"),
        step_eur=("value_eur_step", "sum"),
    ).reset_index().rename(columns={"pn": "part_number"})

    for src, dst in [("aim_l1_fixed", "aim_l1"), ("aim_l2_fixed", "aim_l2"), ("aim_l3", "aim_l3"),
                     ("cat_l1", "cat_l1"), ("cat_l2", "cat_l2"), ("cat_l3", "cat_l3"),
                     ("cat_pms_flag", "pms_flag"), ("fig_key", "fig_key"),
                     ("price_class_iml", "price_class_iml"), ("aim_changed", "aim_changed")]:
        g[dst] = g["part_number"].map(mm[src])

    g["delta_pct"] = [
        (100 * (n / o - 1)) if (pd.notna(n) and pd.notna(o) and o) else None
        for n, o in zip(g["bp_new_jpy"], g["bp_prior_jpy"])
    ]
    g["step_per_1k_billed"] = (1000 * g["step_eur"] / g["l12m_billed_eur"]).round(2)

    # A placeholder is NOT a class. Label it plainly so nobody charts it as one.
    PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None"}
    g["on_aim_spine"] = [
        "0" if str(v).strip() in PLACEHOLDER else "1" for v in g["aim_l1"]
    ]
    g.loc[g["on_aim_spine"] == "0", "aim_l1"] = "UNCLASSIFIED (not on AIM spine)"
    g.loc[g["on_aim_spine"] == "0", "aim_l2"] = ""
    g.loc[g["on_aim_spine"] == "0", "aim_l3"] = ""

    g = g.sort_values("step_eur", ascending=False).reset_index(drop=True)
    g.insert(0, "priority_rank", range(1, len(g) + 1))
    g["cum_step_share_pct"] = (100 * g["step_eur"].cumsum() / g["step_eur"].sum()).round(2)

    cols = ["priority_rank", "part_number", "billed_description",
            "aim_l1", "aim_l2", "aim_l3", "on_aim_spine",
            "cat_l1", "cat_l2", "cat_l3", "pms_flag",
            "price_class_iml", "fig_key",
            "l12m_qty", "l12m_billed_eur", "bp_prior_jpy", "bp_new_jpy",
            "delta_pct", "step_eur", "step_per_1k_billed", "cum_step_share_pct",
            "distributors", "aim_changed"]
    g = g[cols]
    g.to_csv(PRIO_CSV, index=False)

    # workbook for the sales-analysis agent
    by_l1 = (g.groupby(["aim_l1", "aim_l2"], dropna=False)
             .agg(pn=("part_number", "size"), qty=("l12m_qty", "sum"),
                  billed_eur=("l12m_billed_eur", "sum"), step_eur=("step_eur", "sum"))
             .reset_index().sort_values("step_eur", ascending=False))
    by_l1["billed_share_pct"] = (100 * by_l1["billed_eur"] / g["l12m_billed_eur"].sum()).round(2)
    by_l1["step_share_pct"] = (100 * by_l1["step_eur"] / g["step_eur"].sum()).round(2)
    by_db = (g.assign(**{"dist": None}) if False else None)
    head = (g.head(250)[["priority_rank", "part_number", "billed_description", "aim_l1", "aim_l2",
                         "aim_l3", "l12m_qty", "l12m_billed_eur", "delta_pct", "step_eur",
                         "cum_step_share_pct"]])

    with pd.ExcelWriter(PRIO_XLSX, engine="openpyxl") as xl:
        g.to_excel(xl, sheet_name="Priority list", index=False)
        head.to_excel(xl, sheet_name="Top 250 by step", index=False)
        by_l1.to_excel(xl, sheet_name="AIM L1-L2 rollup", index=False)
        if len(fixes):
            summary.to_excel(xl, sheet_name="Taxonomy fixes", index=False)
        pd.DataFrame([
            ["basis", "pricing revision weight base, in_scope == True"],
            ["window", "2025-07-01 .. 2026-06-30 (L12M)"],
            ["rows priced", int(len(g))],
            ["total billed EUR", round(float(g["l12m_billed_eur"].sum()), 2)],
            ["total step EUR", round(float(g["step_eur"].sum()), 2)],
            ["weighted increase", "5.9616% (ties the published revision)"],
            ["aim_l1", "corrected AIM Category (see Taxonomy fixes sheet)"],
            ["cat_l1", "price-list catalogue - attribute, NOT the axis"],
            ["pms_flag", "1 = catalogue family is a PMS/competitive family"],
            ["note", "one basis only. Do not mix with the 18-month audit window."],
        ], columns=["item", "value"]).to_excel(xl, sheet_name="Read me", index=False)

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "basis": {"file": "price_bp_weighted_compare_pn.csv", "filter": "in_scope == True",
                  "window": ["2025-07-01", "2026-06-30"]},
        "priority_rows": int(len(g)),
        "step_eur_total": round(float(g["step_eur"].sum()), 2),
        "billed_eur_total": round(float(g["l12m_billed_eur"].sum()), 2),
        "fixes_applied": int((m["aim_changed"] == "1").sum()),
        "l1_before": {k: round(v, 0) for k, v in before.items()},
        "l1_after": {k: round(v, 0) for k, v in after.items()},
        "flagged_not_forced": [
            "Bumpers split across L2 Bumpers and Panels",
            "Lubricants under Fluids Chemicals vs separate Lubrication L1",
            "Filters appear under four L1s",
        ],
    }
    META_V2.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    print("PRIORITY LIST")
    print(f"  rows                 {len(g):,}")
    print(f"  billed EUR           {g['l12m_billed_eur'].sum():,.2f}")
    print(f"  step EUR             {g['step_eur'].sum():,.2f}")
    print(f"  top 100 lines =      {g.iloc[99]['cum_step_share_pct']:.1f}% of the step")
    print(f"  top 250 lines =      {g.iloc[min(249, len(g)-1)]['cum_step_share_pct']:.1f}% of the step")
    print(f"-> {PRIO_CSV}")
    print(f"-> {PRIO_XLSX}")
    print(f"-> {MASTER_V2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
