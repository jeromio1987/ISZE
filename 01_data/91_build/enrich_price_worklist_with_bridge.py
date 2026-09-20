# -*- coding: utf-8 -*-
"""
Fill the worklist with what the multi-brand OE bridge already resolved.

Before this, price_collection_worklist.csv was a hand-collection sheet: 139 part
numbers, 58 with a named brand, every price column empty.

After the 2026-09-18 bridge test, 35 of those 58 have a competing part number AND
a price. This writes them in, with the tier and the caveats attached, so the sheet
Jerome works from shows what is settled and what is still open.

Run: python 01_data/91_build/enrich_price_worklist_with_bridge.py
Writes: 01_data/00_derived/price_collection_worklist_filled.csv
        01_data/00_derived/price_collection_worklist_filled.xlsx
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


def say(m=""):
    print(m)
    sys.stdout.flush()


wl = pd.read_csv(os.path.join(D, "price_collection_worklist.csv"), dtype={"pn": str})
wl["pn"] = wl["pn"].astype(str).str.strip().str.zfill(10)

br = pd.read_csv(os.path.join(D, "oe_bridge_coverage.csv"), dtype={"pn": str})
br["pn"] = br["pn"].astype(str).str.strip().str.zfill(10)
cards = json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw"
                       r"\spareto_all_cards_20260918.json", encoding="utf-8"))
cards = {str(k).strip().zfill(10): v for k, v in cards.items()}

bmap = br.set_index("pn").to_dict("index")

filled = wl.merge(br[["pn", "brands_with_price", "min_price_eur"]], on="pn", how="left",
                  suffixes=("", "_bridge"))

rows = []
for _, r in filled.iterrows():
    pn = r["pn"]
    got = pn in cards and bmap.get(pn, {}).get("brands_with_price", 0) > 0
    if got:
        pr = sorted([c for c in cards[pn] if c.get("price_eur") is not None],
                    key=lambda c: c["price_eur"])
        cheapest = pr[0]
        ref = r.get("our_reference_dealer_price_eur")
        idx = (ref / cheapest["price_eur"]) if (ref and cheapest["price_eur"]) else np.nan
        rows.append({
            "status": "resolved",
            "evidence_tier": "T6-bridge",
            "competitor_price_eur": round(float(cheapest["price_eur"]), 2),
            "competitor_brand_found": cheapest["brand"],
            "competing_part_number": cheapest.get("iam_pn"),
            "brands_available": int(len(pr)),
            "price_index_our_dealer_vs_competitor": round(float(idx), 2) if pd.notna(idx) else "",
            "source_url_or_note": "multi-brand OE lookup, 2026-09-18; "
                                  "provenance and redistribution licence NOT established",
            "data_as_of": "2026-09-18",
            "checked_by": "bridge test (automated)",
        })
    else:
        rows.append({
            "status": "open", "evidence_tier": "", "competitor_price_eur": "",
            "competitor_brand_found": "", "competing_part_number": "",
            "brands_available": "", "price_index_our_dealer_vs_competitor": "",
            "source_url_or_note": "", "data_as_of": "", "checked_by": "",
        })

add = pd.DataFrame(rows)
# drop the empty review columns the original sheet carried, so add supplies them
out = pd.concat([filled.reset_index(drop=True).drop(columns=add.columns.tolist(),
                                                    errors="ignore"),
                 add], axis=1)

say("=" * 84)
say("THE WORKLIST, FILLED WHERE THE BRIDGE RESOLVED IT")
say("=" * 84)
say(f"  rows                                     : {len(out)}")
say(f"  resolved (competing PN and price)        : {int((out['status'] == 'resolved').sum())}")
say(f"  still open                               : {int((out['status'] == 'open').sum())}")
say()
res = out[out["status"] == "resolved"]
say(f"  our revenue on the resolved rows         : EUR {res['billed_eur'].sum():,.0f}")
say(f"  median price index (our dealer / theirs) : "
    f"{pd.to_numeric(res['price_index_our_dealer_vs_competitor'], errors='coerce').median():.2f}x")
say()
say("  where we sit on the resolved rows, by index band:")
ix = pd.to_numeric(res["price_index_our_dealer_vs_competitor"], errors="coerce")
for lbl, m in (("below the competitor (<1.0x)", ix < 1.0),
               ("1.0 to 1.5x", (ix >= 1.0) & (ix < 1.5)),
               ("1.5 to 2.5x", (ix >= 1.5) & (ix < 2.5)),
               ("far above (>2.5x)", ix >= 2.5)):
    s = res[m]
    say(f"    {lbl:<32} {len(s):>3} PNs   EUR {s['billed_eur'].sum():>12,.0f}")
say()
say("  top 15 resolved, by our revenue:")
show = ["status", "pn", "description", "competing_brand", "competitor_brand_found",
        "competing_part_number", "competitor_price_eur",
        "price_index_our_dealer_vs_competitor", "our_reference_dealer_price_eur",
        "billed_eur"]
say(res.sort_values("billed_eur", ascending=False)[show].head(15).to_string(
    index=False, float_format=lambda v: f"{v:,.2f}"))

out.to_csv(os.path.join(D, "price_collection_worklist_filled.csv"), index=False)
try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "Worklist filled"
    ws.sheet_view.showGridLines = False
    ws["A1"] = ("Price-collection worklist - filled where a multi-brand OE bridge resolved it")
    ws["A1"].font = Font(bold=True, size=12, color="15233C")
    ws["A2"] = ("status=resolved means a competing part number AND a price are now on the row. "
                "status=open still needs a manual lookup. Bridge prices are a distributor list, "
                "NOT a market price, and are not comparable to our PR00 or reference dealer price. "
                "Provenance and redistribution licence of the bridge source are NOT established - "
                "keep internal.")
    ws["A2"].font = Font(italic=True, size=9, color="555555")
    HDR = PatternFill("solid", fgColor="15233C")
    HF = Font(bold=True, color="F7F4EE", size=10)
    for i, h in enumerate(out.columns, start=1):
        c = ws.cell(4, i, h)
        c.fill = HDR
        c.font = HF
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r, (_, row) in enumerate(out.iterrows(), start=5):
        for i, h in enumerate(out.columns, start=1):
            v = row[h]
            ws.cell(r, i, None if (isinstance(v, float) and not np.isfinite(v)) else v)
    widths = {"description": 40, "competing_brand": 18, "competitor_brand_found": 20,
              "source_url_or_note": 52, "criticality_meanings": 40,
              "competing_part_number": 20}
    for i, h in enumerate(out.columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(h, 14)
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(out.columns))}{4+len(out)}"
    wb.save(os.path.join(D, "price_collection_worklist_filled.xlsx"))
    say()
    say(f"  wrote price_collection_worklist_filled.xlsx")
except Exception as e:                                                   # noqa: BLE001
    say(f"  xlsx skipped: {e}")

say()
say(f"wrote price_collection_worklist_filled.csv ({len(out)} rows)")
say("BUILD_OK")
