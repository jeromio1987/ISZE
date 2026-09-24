"""The hub / console AIM cell, recomputed.

The cell reads 98% and its tooltip says: unclassified revenue / parts revenue in scope, 1.6% CY2024
and 1.8% CY2025, source aim_classification_gap_report.md of 2 Jul 2026.

This probe recomputes that same definition on the base population the report used (sales_fact, part
lines only, document types excluded) for four candidate sources, so it can be seen whether swapping
the source is a refresh or a change of meaning:

  aim_pn_classification.csv            the fused file the OS Hub links today
  aim_pn_classification_20260920.csv   the dated overlay the export pair is built from
  aim_master_v2.csv aim_l1             the master's old column
  aim_master_v2.csv aim_l1_fixed       the master's current column

A part number is "unclassified" when its family is blank or one of the workbook placeholders
Unknown / Unknown Review / Other / review, case-insensitive - the rule the gap report states.
"""
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

DER = r"01_data\00_derived"
PLACE = {"", "nan", "none", "null", "unknown", "unknown review", "other / review", "other/review"}

EXCLUDE_SATY = {"CR", "RE", "DR", "ZDR", "FD"}


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


sf = pd.read_parquet(os.path.join(DER, "sales_fact.parquet"),
                     columns=["billing_date", "part_number", "billed_qty",
                              "net_sales_value", "saty"])
sf["cy"] = sf["billing_date"].dt.year
sf = sf[~sf["saty"].isin(EXCLUDE_SATY) & sf["saty"].notna()]
sf["pn"] = norm(sf["part_number"])
print(f"sales_fact rows kept (document types excluded): {len(sf):,}")
print(sf.groupby("cy")["net_sales_value"].sum().round(0).to_string())

sources = []

cls = pd.read_csv(os.path.join(DER, "aim_pn_classification.csv"), dtype=str, low_memory=False)
cls["pn"] = norm(cls["part_number"])
sources.append(("aim_pn_classification.csv  aim_l1", cls.drop_duplicates("pn")
                .set_index("pn")["aim_l1"]))

old = pd.read_csv(os.path.join(DER, "aim_pn_classification_20260920.csv"), dtype=str,
                  low_memory=False)
old["pn"] = norm(old["part_number"])
old = old.drop_duplicates("pn").set_index("pn")
sources.append(("aim_pn_classification_20260920.csv  workbook_l1", old["workbook_l1"]))
sources.append(("aim_pn_classification_20260920.csv  aim_l1_fixed", old["aim_l1_fixed"]))
sources.append(("aim_pn_classification_20260920.csv  catalog_l1", old["catalog_l1"]))

mst = pd.read_csv(os.path.join(DER, "aim_master_v2.csv"), dtype=str, low_memory=False,
                  usecols=["part_number", "aim_l1", "aim_l1_fixed"])
mst["pn"] = norm(mst["part_number"])
mst = mst.drop_duplicates("pn").set_index("pn")
sources.append(("aim_master_v2.csv  aim_l1", mst["aim_l1"]))
sources.append(("aim_master_v2.csv  aim_l1_fixed", mst["aim_l1_fixed"]))

print("\n%-44s %-6s %14s %14s %9s" % ("source", "year", "parts revenue", "unclassified",
                                      "share"))
for label, fam in sources:
    for cy in (2024, 2025):
        g = sf[sf["cy"] == cy]
        valued = pd.to_numeric(g["net_sales_value"], errors="coerce").fillna(0.0)
        f = g["pn"].map(fam)
        f = f.fillna("").astype(str).str.strip().str.lower()
        tot = float(valued.sum())
        bad = float(valued[f.isin(PLACE)].sum())
        print("%-44s %-6d %14s %14s %8.2f%%" % (label, cy, f"{tot:,.0f}", f"{bad:,.0f}",
                                                100 * bad / tot if tot else 0))
    # the pure-blank share, to separate "no row at all" from "workbook placeholder"
    for cy in (2025,):
        g = sf[sf["cy"] == cy]
        valued = pd.to_numeric(g["net_sales_value"], errors="coerce").fillna(0.0)
        f = g["pn"].map(fam).fillna("").astype(str).str.strip()
        tot = float(valued.sum())
        blank = float(valued[f.eq("")].sum())
        print("%-44s %-6d %14s %14s %8.2f%%   (blank only)"
              % ("", cy, f"{tot:,.0f}", f"{blank:,.0f}", 100 * blank / tot if tot else 0))
    print()
