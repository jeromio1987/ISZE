#!/usr/bin/env python3
"""
Build the AIM master — AIM-led, catalogue as attribute, PMS flagged.

Design decisions (agreed with Jerome 2026-09-17):
  1. AIM Category is the GOVERNED spine (sales-analysis taxonomy, 23/105/197).
     Identity = part_number. The AIM workbook is description-keyed, so descriptions
     are attached from actual billing text, not from the workbook's own list.
  2. The price-list catalogue is an ATTRIBUTE, never the axis.
  3. Figure key (fig_no/key_no) is a column and a structural grouping aid.
     It is NEVER evidence of competition.
  4. "Body Exterior" is renamed "Accident & Body" (93.4% of it is accident/body damage).
  5. A PMS flag marks the genuinely competitive/PMS families (filters, brakes,
     clutch, suspension, steering, cooling, exhaust, belts, fuel & air system).

Outputs
-------
  01_data/00_derived/aim_master_v1.csv
  01_data/00_derived/aim_master_v1.meta.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
AIM_WB = ISZE / "91_legacy" / "Isuzu" / "AIM_CY2025_Analysis.xlsx"
PR00 = D / "pr00_classification.csv"
PRICING = D / "price_bp_weighted_compare_pn.csv"
SALES = D / "sales_fact.parquet"
OUT_CSV = D / "aim_master_v1.csv"
OUT_META = D / "aim_master_v1.meta.json"

RENAME_L1 = {"Body Exterior": "Accident & Body"}

# catalogue L2 families that are genuinely competitive / PMS
PMS_L2 = {
    "Filters", "Brake parts", "Clutch parts", "Suspension", "Steering",
    "Cooling", "Exhaust", "Belts", "Fuel system", "Air system",
    "Starter / alternator", "Injectors", "Turbo",
    "Hydraulic / mechanical", "Transmission parts", "Engine parts",
}


def norm(s: object) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().upper())


def main() -> int:
    # ---------------------------------------------------------------- AIM workbook
    pm = pd.read_excel(AIM_WB, sheet_name="Parts Master", header=1)
    pm.columns = [str(c).strip() for c in pm.columns]
    pm = pm.rename(columns={
        "Category L1": "aim_l1", "Category L2": "aim_l2", "Category L3": "aim_l3",
        "Demand Type": "aim_demand_type", "Core/NonCore": "aim_core_noncore",
    })
    for c in ("aim_l1", "aim_l2", "aim_l3", "aim_demand_type", "aim_core_noncore"):
        if c not in pm.columns:
            pm[c] = None
    extra = [c for c in ("Strategic Score", "Bucket", "Strategic Tags", "Pricing Risk",
                         "GP%", "Revenue (\u20ac)", "Qty", "Customers") if c in pm.columns]
    pm["desc_key"] = pm["Description"].map(norm)
    pm = pm[pm["desc_key"] != ""].drop_duplicates("desc_key", keep="first")
    aim_map = {
        r["desc_key"]: (
            r["aim_l1"], r["aim_l2"], r["aim_l3"],
            r["aim_demand_type"], r["aim_core_noncore"],
        )
        for _, r in pm.iterrows()
    }
    aim_extra = {r["desc_key"]: {c: r[c] for c in extra} for _, r in pm.iterrows()}

    # ---------------------------------------------------------------- PR00
    pr = pd.read_csv(PR00, dtype=str)
    pr["pn"] = pr["pn_norm"].astype(str).str.strip()
    pr = pr.drop_duplicates("pn", keep="first").set_index("pn")

    # ---------------------------------------------------------------- price class
    cls_map: dict[str, str] = {}
    if PRICING.is_file():
        s = pd.read_csv(PRICING, usecols=["part_number", "bp_new_class"], dtype=str)
        s["pn"] = s["part_number"].astype(str).str.strip()
        cls_map = dict(zip(s["pn"], s["bp_new_class"]))

    # ---------------------------------------------------------------- billed descriptions
    sf = pd.read_parquet(SALES, columns=["billing_date", "part_number", "description",
                                         "net_sales_value", "billed_qty"])
    sf["pn"] = sf["part_number"].astype(str).str.strip()
    sf["desc_key"] = sf["description"].map(norm)
    # most-billed description per part number = the identity description
    grp = (sf.groupby(["pn", "desc_key"])["net_sales_value"].sum()
             .reset_index().sort_values("net_sales_value", ascending=False)
             .drop_duplicates("pn"))
    desc_by_pn = dict(zip(grp["pn"], grp["desc_key"]))
    sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
    win = sf[sf["d"] >= "2025-01-01"]
    eur_by_pn = win.groupby("pn")["net_sales_value"].sum().to_dict()

    # ---------------------------------------------------------------- ambiguous descriptions
    dl = {}
    for k, v in aim_map.items():
        dl.setdefault(k, set()).add(v[0])
    ambiguous = {k for k, s in dl.items() if len(s) > 1}

    # ---------------------------------------------------------------- build rows
    pns = sorted(set(desc_by_pn) | set(pr.index) | set(cls_map))
    rows = []
    for pn in pns:
        dk = desc_by_pn.get(pn, "")
        a = aim_map.get(dk)
        pr_row = pr.loc[pn] if pn in pr.index else None
        cat1 = "" if pr_row is None else str(pr_row.get("family") or "").strip()
        cat2 = "" if pr_row is None else str(pr_row.get("group") or "").strip()
        cat3 = "" if pr_row is None else str(pr_row.get("level3_type") or "").strip()
        fig_key = "" if pr_row is None else str(pr_row.get("fig_key") or "").strip()
        fig_no = "" if pr_row is None else str(pr_row.get("fig_no") or "").strip()
        key_no = "" if pr_row is None else str(pr_row.get("key_no") or "").strip()

        if a:
            a1, a2, a3, dt_, core = a
        else:
            a1 = a2 = a3 = dt_ = core = ""
        if a1 in RENAME_L1:
            a1 = RENAME_L1[a1]

        has_aim = bool(str(a1).strip()) and str(a1).strip() not in ("Unknown", "Unknown Review")
        has_cat = cat1 not in ("", "Other / review")
        x = aim_extra.get(dk, {})

        rows.append({
            "part_number": pn,
            "description": dk,
            # governed AIM spine
            "aim_l1": str(a1 or "").strip(),
            "aim_l2": str(a2 or "").strip(),
            "aim_l3": str(a3 or "").strip(),
            "aim_demand_type": str(dt_ or "").strip(),
            "aim_core_noncore": str(core or "").strip(),
            # catalogue attribute (NOT the axis)
            "cat_l1": cat1,
            "cat_l2": cat2,
            "cat_l3": cat3,
            "cat_pms_flag": "1" if cat2 in PMS_L2 else "0",
            # structure
            "fig_key": fig_key,
            "fig_no": fig_no,
            "key_no": key_no,
            "price_class_iml": cls_map.get(pn, ""),
            # provenance / flags
            "aim_source": "aim_workbook" if a else "not_classified",
            "has_aim": "1" if has_aim else "0",
            "has_catalogue_node": "1" if has_cat else "0",
            "desc_ambiguous": "1" if dk in ambiguous else "0",
            "l12m_billed_eur": round(float(eur_by_pn.get(pn, 0.0)), 2),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    tot_eur = float(df["l12m_billed_eur"].sum())
    has_aim_eur = float(df.loc[df["has_aim"] == "1", "l12m_billed_eur"].sum())
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "built_by": "01_data/91_build/build_aim_master.py",
        "governed_axis": "aim_l1 / aim_l2 / aim_l3  (AIM Category, sales-analysis taxonomy)",
        "attribute_axis": "cat_l1 / cat_l2 / cat_l3  (price-list catalogue - attribute, never the axis)",
        "notes": [
            "AIM Category values are unchanged except Body Exterior -> Accident & Body.",
            "Figure key is structural grouping only and must never imply competition.",
            "AIM workbook is description-keyed; descriptions attached from billed text by euro.",
        ],
        "rows": len(df),
        "renames": RENAME_L1,
        "coverage": {
            "total_l12m_billed_eur": round(tot_eur, 2),
            "with_aim_pct_eur": round(100 * has_aim_eur / tot_eur, 2) if tot_eur else None,
            "with_catalogue_node_pct_eur": round(
                100 * float(df.loc[df["has_catalogue_node"] == "1", "l12m_billed_eur"].sum()) / tot_eur, 2
            ) if tot_eur else None,
            "pms_flagged_pct_eur": round(
                100 * float(df.loc[df["cat_pms_flag"] == "1", "l12m_billed_eur"].sum()) / tot_eur, 2
            ) if tot_eur else None,
        },
        "counts": {
            "aim_l1_values": int(df.loc[df["has_aim"] == "1", "aim_l1"].nunique()),
            "aim_l2_values": int(df.loc[df["has_aim"] == "1", "aim_l2"].nunique()),
            "aim_l3_values": int(df.loc[df["has_aim"] == "1", "aim_l3"].nunique()),
            "rows_desc_ambiguous": int((df["desc_ambiguous"] == "1").sum()),
            "rows_with_fig_key": int((df["fig_key"] != "").sum()),
            "rows_not_classified_aim": int((df["has_aim"] == "0").sum()),
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    print(f"rows                    {len(df):,}")
    print(f"AIM L1/L2/L3            {meta['counts']['aim_l1_values']}/{meta['counts']['aim_l2_values']}/{meta['counts']['aim_l3_values']}")
    print(f"with AIM        (eur)   {meta['coverage']['with_aim_pct_eur']}%")
    print(f"with cat node   (eur)   {meta['coverage']['with_catalogue_node_pct_eur']}%")
    print(f"PMS flagged     (eur)   {meta['coverage']['pms_flagged_pct_eur']}%")
    print(f"rows with fig_key       {meta['counts']['rows_with_fig_key']:,}")
    print(f"ambiguous desc rows     {meta['counts']['rows_desc_ambiguous']:,}")
    print(f"not classified (AIM)    {meta['counts']['rows_not_classified_aim']:,}")
    print(f"-> {OUT_CSV}")
    print(f"-> {OUT_META}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
