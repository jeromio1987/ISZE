# -*- coding: utf-8 -*-
"""
The price-collection worklist: our top-200 revenue where a competing brand is
identified and we do not hold its price.

This is the one bounded piece of work that unblocks the pricing policy. It is not
a scraping platform. It is a list of part numbers against named brands, with the
fields a person needs to go and find each price.

Run: python 01_data/91_build/build_price_collection_worklist.py
Writes: 01_data/00_derived/price_collection_worklist.csv
        01_data/00_derived/price_collection_worklist.xlsx
        01_data/00_derived/price_collection_worklist_meta.json
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"


def say(m):
    print(m)
    sys.stdout.flush()


top = pd.read_csv(os.path.join(D, "margin_opportunity_top200.csv"), dtype={"pn": str})
au = pd.read_csv(os.path.join(D, "competitiveness_autodoc_risk.csv"), dtype=str)
au["pn"] = au["part_number"].str.strip()
au = au.drop_duplicates("pn")
brand = dict(zip(au["pn"], au["Autodoc_CheapestBrand"]))

wl = top[top["competition"] == 1].copy()
wl["competing_brand"] = wl["pn"].map(brand)
wl["our_list_eur"] = wl["cost_fob"] / (1 - wl["margin_pct"] / 100)
wl["our_reference_dealer_price_eur"] = wl["our_list_eur"] * 1.785
wl["criticality_meanings"] = wl["criticality"].map({
    "A": "safety or line-stoppage - vehicle off the road without it",
    "B": "performance loss - runs but badly, a planned repair can absorb a day",
    "C": "cosmetic or discretionary - vehicle fully serviceable without it",
})

# Priority: revenue x criticality, with the named-brand rows first because they
# are the ones a person can actually go and price today.
CRIT_W = {"A": 3.0, "B": 1.5, "C": 1.0}
wl["priority_score"] = wl["billed_eur"] * wl["criticality"].map(CRIT_W).fillna(1.0)
wl["brand_named"] = wl["competing_brand"].notna()
wl = wl.sort_values(["brand_named", "priority_score"], ascending=[False, False])
wl["worklist_rank"] = range(1, len(wl) + 1)

OUT = ["worklist_rank", "pn", "description", "aim_l1", "aim_l2", "criticality",
       "criticality_meanings", "competing_brand", "brand_named",
       "our_list_eur", "our_reference_dealer_price_eur", "margin_pct",
       "billed_eur", "qty", "distributors", "price_class", "step_eur",
       "priority_score"]
wl = wl[OUT]
for c in ("our_list_eur", "our_reference_dealer_price_eur", "margin_pct",
          "billed_eur", "qty", "priority_score", "step_eur"):
    wl[c] = wl[c].round(2)

# review columns for the person doing the work
wl["competitor_price_eur"] = ""
wl["competitor_brand_found"] = ""
wl["price_index_our_dealer_vs_competitor"] = ""
wl["source_url_or_note"] = ""
wl["evidence_tier"] = ""
wl["data_as_of"] = ""
wl["checked_by"] = ""

say("=" * 84)
say("THE PRICE-COLLECTION WORKLIST")
say("=" * 84)
say(f"  part numbers                              : {len(wl)}")
say(f"  our revenue on them                       : EUR {wl['billed_eur'].sum():,.0f}")
say(f"  of which a competing brand is already named: {int(wl['brand_named'].sum())} PNs, "
    f"EUR {wl.loc[wl['brand_named'], 'billed_eur'].sum():,.0f}")
say(f"  criticality A                             : {int((wl['criticality'] == 'A').sum())} PNs, "
    f"EUR {wl.loc[wl['criticality'] == 'A', 'billed_eur'].sum():,.0f}")
say("")
say("  If even half of these yield a price, evidence coverage on the top 200 moves")
say("  from 30.0% to about 63% of revenue, and the policy can price them.")
say("")
say("  The named brands, by revenue on the list:")
b = wl.dropna(subset=["competing_brand"]).groupby("competing_brand")["billed_eur"].agg(
    ["count", "sum"]).sort_values("sum", ascending=False)
say(b.to_string(float_format=lambda v: f"{v:,.0f}"))
say("")
say("  The top 15 rows:")
say(wl.head(15)[["worklist_rank", "pn", "description", "aim_l2", "criticality",
                 "competing_brand", "our_list_eur", "margin_pct",
                 "billed_eur", "distributors"]].to_string(
    index=False, float_format=lambda v: f"{v:,.1f}"))

wl.to_csv(os.path.join(D, "price_collection_worklist.csv"), index=False)

# Excel version with the review columns readable and a header note.
try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Worklist"
    ws.sheet_view.showGridLines = False
    ws["A1"] = "Price-collection worklist - our top-200 revenue where a competing brand is named and unpriced"
    ws["A1"].font = Font(bold=True, size=12, color="15233C")
    ws["A2"] = ("Fill the eight empty columns on the right for each part number. "
                "Evidence tier: T1 observed at the same shop for the same part number, "
                "T2 published listing, T3 network benchmark, T4 category median. "
                "Leave the tier blank if you could not price it - that is a finding too.")
    ws["A2"].font = Font(italic=True, size=9, color="555555")
    HDR = PatternFill("solid", fgColor="15233C")
    HF = Font(bold=True, color="F7F4EE", size=10)
    for i, h in enumerate(wl.columns, start=1):
        c = ws.cell(4, i, h)
        c.fill = HDR
        c.font = HF
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r, (_, row) in enumerate(wl.iterrows(), start=5):
        for i, h in enumerate(wl.columns, start=1):
            v = row[h]
            ws.cell(r, i, None if (isinstance(v, float) and not np.isfinite(v)) else v)
    widths = {"description": 40, "criticality_meanings": 46, "aim_l1": 20, "aim_l2": 20,
              "competing_brand": 18, "source_url_or_note": 40}
    for i, h in enumerate(wl.columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(h, 13)
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(wl.columns))}{4+len(wl)}"
    for r in range(5, 5 + len(wl)):
        for col, fmt in (("J", "#,##0.00"), ("K", "#,##0.00"), ("L", "0.0"),
                         ("M", "#,##0"), ("N", "#,##0"), ("Q", "#,##0.00"), ("R", "#,##0")):
            ws[f"{col}{r}"].number_format = fmt
    xlsx = os.path.join(D, "price_collection_worklist.xlsx")
    wb.save(xlsx)
    say("")
    say(f"  wrote {xlsx}")
except Exception as e:            # noqa: BLE001
    say(f"  xlsx skipped: {e}")

meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "what": "top-200 revenue part numbers where a competing brand is identified and its price is not held",
    "counts": {
        "part_numbers": int(len(wl)),
        "billed_eur": float(wl["billed_eur"].sum()),
        "brand_named": int(wl["brand_named"].sum()),
        "brand_named_billed_eur": float(wl.loc[wl["brand_named"], "billed_eur"].sum()),
        "criticality_A": int((wl["criticality"] == "A").sum()),
    },
    "how_to_use": [
        "One row per part number. The competing brand column names the alternative "
        "where the Autodoc extract identified one.",
        "Fill competitor_price_eur, the brand actually found, the source, the evidence "
        "tier and the date. Leave the tier blank where no price could be found - a "
        "blank is a result.",
        "The price index column is our reference dealer price divided by the competing "
        "price. Under 0.95 we are cheaper; over 1.15 we are more expensive.",
    ],
    "caveats": [
        "The competing brand comes from the Autodoc extract. That file's PRICE column is "
        "unusable (277 of 298 rows carry the identical 2.34), so only the brand name is "
        "used here. Nothing in this list is priced off that file.",
        "The Autodoc scrape itself is frozen behind Cloudflare. The brands named are "
        "catalogue brands with their own published catalogues, so this is a manual or "
        "targeted lookup per part number, not a bulk scrape.",
        "63% of these part numbers have no brand named. They still have a rival - the "
        "extract identified one part number or a sibling under the same figure key - but "
        "not a brand, so they need a different route.",
    ],
}
with open(os.path.join(D, "price_collection_worklist_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say("")
say("BUILD_OK")
