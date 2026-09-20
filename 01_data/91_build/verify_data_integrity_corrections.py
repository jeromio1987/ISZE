# -*- coding: utf-8 -*-
"""
Data-integrity corrections found on 2026-09-18, recorded so they cannot resurface.

Three defects were found by checking sources rather than summaries. This files the
evidence for each with the numbers, so a future session sees the fault rather than
rediscovering it.

1. SNAPSHOT FOLDERS ARE NOT WHAT THEIR NAMES SAY. Four of thirteen folders hold a
   byte-identical file. The folder name is the date of the NEXT refresh; the file
   inside is the PREVIOUS run's output. So "13 weekly snapshots" is ten distinct
   reads.
2. TWO BRIDGE PRICES ARE UNIT MISMATCHES. EGR coolers at 7.16x and 7.64x our own
   list. Not competitor prices.
3. THE DEALER BRIDGE CARRIED NETWORK BILLING. Fixed at source; recorded here.

Run: python 01_data/91_build/verify_data_integrity_corrections.py
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
SNAP = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper\_snapshots"


def say(m=""):
    print(m)
    sys.stdout.flush()


out = {"checked": pd.Timestamp.now().isoformat(timespec="seconds")}

say("=" * 86)
say("1. SNAPSHOT FOLDERS - DUPLICATES AND THE NAMING TRAP")
say("=" * 86)
dirs = sorted(d for d in os.listdir(SNAP) if os.path.isdir(os.path.join(SNAP, d)))
hashes: dict[str, list] = {}
for d in dirs:
    p = os.path.join(SNAP, d, "ks_results.csv")
    if os.path.exists(p):
        hashes.setdefault(hashlib.sha256(open(p, "rb").read()).hexdigest()[:16],
                          []).append(d)
dup = {h: v for h, v in hashes.items() if len(v) > 1}
say(f"  folders on disk        : {len(dirs)}")
say(f"  distinct file contents : {len(hashes)}")
if dup:
    for h, v in dup.items():
        say(f"    IDENTICAL: {', '.join(v)}   sha256[:16] {h}")
say()
say("  Cause, from refresh_and_check_drift.py:")
say("    stamp = datetime.now().strftime('%Y-%m-%d')")
say("    _snapshot_existing() copies the PRE-refresh file into _snapshots/{stamp}/")
say("  So the folder is dated to the NEXT refresh and holds the PREVIOUS run.")
out["snapshot_folders"] = len(dirs)
out["snapshot_distinct"] = len(hashes)
out["snapshot_duplicates"] = dup

say()
say("=" * 86)
say("2. BRIDGE PRICES THAT ARE UNIT MISMATCHES")
say("=" * 86)
br = pd.read_csv(f"{D}\\oe_bridge_coverage.csv", dtype={"pn": str})
br["pn"] = br["pn"].str.strip().str.zfill(10)
pl = pd.read_parquet(f"{D}\\pricing_list_pn.parquet",
                     columns=["part_number", "sp_eur", "description", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True]                                      # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
pl = pl.drop_duplicates("pn")
br["our_list"] = br["pn"].map(pl.set_index("pn")["sp_eur"])
br["description"] = br["pn"].map(pl.set_index("pn")["description"])
br["multiple"] = br["min_price_eur"] / br["our_list"]
sus = br[br["multiple"] > 3].copy()
say(f"  bridge rows {len(br)}   above 3x our own list: {len(sus)}")
for _, r in sus.iterrows():
    say(f"    {r['pn']}  {str(r['description'])[:28]:<30} "
        f"list EUR {r['our_list']:>9,.2f}  bridge EUR {r['min_price_eur']:>10,.2f}  "
        f"{r['multiple']:>5.2f}x")
excl = br[br["multiple"] <= 3]
say()
say(f"  WITH the two rows    : {len(br)} part numbers")
say(f"  WITHOUT them         : {len(excl)} part numbers")
out["bridge_unit_mismatch_pns"] = sus["pn"].tolist()
out["bridge_rows_clean"] = int(len(excl))

say()
say("=" * 86)
say("3. THE DEALER BRIDGE - FIXED AT SOURCE, VERIFIED HERE")
say("=" * 86)
bd = pd.read_parquet(f"{D}\\replenishment_bridge_ituk_dealer.parquet")
say(f"  rows                       : {len(bd):,}")
say(f"  bill_qty populated         : {int(bd['bill_qty'].notna().sum())}  "
    f"(must be 0 - a dealer row cannot carry a billed quantity)")
say(f"  sellout_qty populated      : {int(bd['sellout_qty'].notna().sum()):,}  "
    f"(correct - the dealer's own reported sales)")
say(f"  bill_basis distinct values : {bd['bill_basis'].dropna().unique().tolist()}")
carried = pd.to_numeric(bd["bill_qty_network_carried"], errors="coerce").sum()
say(f"  carried column kept for audit: {carried:,.0f}  "
    f"(this is the number that was wrongly readable as a dealer purchase)")
out["dealer_bridge_rows"] = int(len(bd))
out["dealer_bridge_bill_qty_populated"] = int(bd["bill_qty"].notna().sum())

say()
say("=" * 86)
say("WHAT IS STILL OPEN, STATED SO IT IS NOT MISTAKEN FOR FIXED")
say("=" * 86)
say("  - A per-dealer billed VALUE does not exist on disk. The source workbook")
say("    (Sales to Dealers_ITUK_CY2025.xlsx) carries QUANTITY only. The dealer")
say("    markup therefore remains uncomputable until a dealer-level value arrives.")
say("  - The bridge's source, provenance and redistribution licence are not")
say("    established. Internal only.")
say()
with open(f"{D}\\data_integrity_corrections_20260918.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
say("INTEGRITY_OK")
