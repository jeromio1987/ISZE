#!/usr/bin/env python3
"""Clean the three non-AIM versioned deliverable sets. DRY-RUN BY DEFAULT.

Jerome, 2026-09-20: "start with the 3 non-AIM deliverables ... then clean those".

WHAT "CLEAN" MEANS HERE - and what it does not
---------------------------------------------
  * MOVES superseded revisions and exact duplicates into 92_archive, so the live file
    is unambiguous. Nothing is deleted.
  * Never edits the CONTENT of any deliverable. The live file is untouched.
  * Leaves 90_INBOX alone: that folder holds what was actually sent and received, which
    is evidence, not clutter.

The live file in each set was determined by byte hash + date, not by the version number.
See which_is_live.py output: in set 1 the version numbers are actively misleading.

Usage
    python clean_versioned_deliverables.py            # dry run
    python clean_versioned_deliverables.py --apply    # do it
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import sys
from datetime import datetime, timezone

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
ARCHIVE_ROOT = os.path.join(ISZE, "01_data", "92_archive", "versioned_cleanup_20260920")

# (relative path to move, set it belongs to, why)
MOVES = [
    # ---- SET 1: IUK Sales Share Stretch -------------------------------------------
    # Live = the 16 KB file, newest (17 Jul) and the one actually emailed to Masumi.
    # v4-v7 are 7 KB drafts from 16 Jul morning, superseded. The version NUMBERS are
    # misleading: " v2" is later than "_v7".
    (r"01_data\ISZE_IUK_Sales_Share_Stretch_TESTCASE_v5.xlsx", "IUK_stretch",
     "superseded draft, 16 Jul 10:00, superseded by the 16 KB file sent to Masumi"),
    (r"01_data\ISZE_IUK_Sales_Share_Stretch_TESTCASE_v6.xlsx", "IUK_stretch",
     "superseded draft, 16 Jul 10:08"),
    (r"01_data\ISZE_IUK_Sales_Share_Stretch_TESTCASE_v7.xlsx", "IUK_stretch",
     "superseded draft, 16 Jul 10:13 - the highest version number, but NOT the latest file"),
    (r"01_data\ISZE_IUK_Sales_Share_Stretch_TESTCASE v2.xlsx", "IUK_stretch",
     "exact byte copy of the live file; the live one sits in 01_data\02_GPS"),
    (r"01_data\02_GPS\ISZE_IUK_Sales_Share_Stretch_TESTCASE v2 (1).xlsx", "IUK_stretch",
     "exact byte copy with a browser-download suffix; live file is the clean-named sibling"),

    # ---- SET 2: PMS Parts Support -------------------------------------------------
    # Live = ISZE_PMS_Parts_Support_20260818_FINAL.pptx (largest, named FINAL, 19 Aug).
    (r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_rev2.pptx", "PMS_parts_support",
     "superseded revision of the 18 Aug deck"),
    (r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_rev3.pptx", "PMS_parts_support",
     "superseded revision of the 18 Aug deck"),
    (r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_rev4.pptx", "PMS_parts_support",
     "superseded revision of the 18 Aug deck"),
    (r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_rev5.pptx", "PMS_parts_support",
     "superseded revision of the 18 Aug deck"),
    (r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_rev6.pptx", "PMS_parts_support",
     "superseded revision of the 18 Aug deck"),
    (r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_rev7.pptx", "PMS_parts_support",
     "superseded revision of the 18 Aug deck"),
    (r"09_meetings\ISZE_PMS_Parts_Support_20260817.pptx", "PMS_parts_support",
     "previous day's deck, superseded by the 18 Aug FINAL"),
    (r"09_meetings\ISZE_PMS_Parts_Support_20260817_s11.pptx", "PMS_parts_support",
     "17 Aug working cut, superseded"),
    (r"09_meetings\ISZE_PMS_Parts_Support_20260817_how_pct.pptx", "PMS_parts_support",
     "17 Aug working cut, superseded"),
    (r"09_meetings\ISZE_PMS_Parts_Support_SHORT_20260817.pptx", "PMS_parts_support",
     "17 Aug short cut, superseded"),
    (r"09_meetings\ISZE_PMS_Parts_Support_SHORT_20260817_how_pct.pptx", "PMS_parts_support",
     "17 Aug short cut, superseded"),
    (r"09_meetings\OPEN_PMS_Parts_Support_how_pct.cmd", "PMS_parts_support",
     "launcher for the superseded 17 Aug cut; archived WITH it so no launcher points at a moved file"),
    # stray copies in the repo root
    (r"ISZE_PMS_Parts_Support_20260817.pptx", "PMS_parts_support", "stray root copy of the 17 Aug deck"),
    (r"ISZE_PMS_Parts_Support_20260817_s11.pptx", "PMS_parts_support", "stray root copy"),
    (r"ISZE_PMS_Parts_Support_20260817_how_pct.pptx", "PMS_parts_support", "stray root copy"),
    (r"ISZE_PMS_Parts_Support_SHORT_20260817.pptx", "PMS_parts_support", "stray root copy"),
    (r"ISZE_PMS_Parts_Support_SHORT_20260817_how_pct.pptx", "PMS_parts_support", "stray root copy"),

    # ---- SET 3: Tender StrategyBrief ----------------------------------------------
    # Live = v8 (newest and largest, 26 Aug 17:57).
    (r"01_data\10_Tender\ISZE_TenderIntelligence_StrategyBrief_v6.pdf", "Tender_brief",
     "March version, a much shorter document; superseded"),
    (r"01_data\10_Tender\ISZE_TenderIntelligence_StrategyBrief_v7.pdf", "Tender_brief",
     "superseded by v8, same timestamp, 843 bytes smaller"),
    (r"01_data\10_Tender\OPEN_StrategyBrief_v7.cmd", "Tender_brief",
     "launcher for the superseded v7; two launchers existed, so the open path was ambiguous"),
]

KEEP = {
    "IUK_stretch": r"01_data\02_GPS\ISZE_IUK_Sales_Share_Stretch_TESTCASE v2.xlsx",
    "PMS_parts_support": r"01_data\03_PMS\ISZE_PMS_Parts_Support_20260818_FINAL.pptx",
    "Tender_brief": r"01_data\10_Tender\ISZE_TenderIntelligence_StrategyBrief_v8.pdf",
    "Tender_brief_launcher": r"01_data\10_Tender\OPEN_StrategyBrief_v8.cmd",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    print("=" * 88)
    print("versioned deliverable cleanup - %s" % ("APPLY" if args.apply else "DRY RUN (nothing changes)"))
    print("=" * 88)

    print("\nLIVE file per set (this is the one to read or send):")
    for k, v in KEEP.items():
        p = os.path.join(ISZE, v)
        print("  %-22s %s  [%s]" % (k, v, "present" if os.path.isfile(p) else "MISSING"))

    print("\nto move to archive (%d files):" % len(MOVES))
    missing = []
    for rel, group, why in MOVES:
        p = os.path.join(ISZE, rel)
        ok = os.path.isfile(p)
        if not ok:
            missing.append(rel)
        print("  [%s] %-72s" % ("x" if ok else " ", rel[:72]))
        print("        %s" % why)
    if missing:
        print("\n  %d listed file(s) are not on disk and will be skipped:" % len(missing))
        for m in missing:
            print("     %s" % m)

    if not args.apply:
        print("\nDRY RUN. Re-run with --apply to move them.")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = []
    print("\nmoving:")
    for rel, group, why in MOVES:
        src = os.path.join(ISZE, rel)
        if not os.path.isfile(src):
            continue
        dst_dir = os.path.join(ARCHIVE_ROOT, group)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(src))
        n = 1
        while os.path.exists(dst):
            stem, ext = os.path.splitext(os.path.basename(src))
            dst = os.path.join(dst_dir, f"{stem}__{n}{ext}")
            n += 1
        shutil.move(src, dst)
        manifest.append(f"{rel}\t->\t{os.path.relpath(dst, ISZE)}\t{why}")
        print("  %-72s -> %s" % (rel[:72], group))

    mf = os.path.join(ARCHIVE_ROOT, f"_CLEANUP_MANIFEST_{stamp}.txt")
    io.open(mf, "w", encoding="utf-8").write(
        "Versioned deliverable cleanup, %s\n\n" % stamp +
        "LIVE files kept:\n" + "\n".join(f"  {k}: {v}" for k, v in KEEP.items()) +
        "\n\nMOVED (nothing deleted):\n" + "\n".join(manifest) + "\n")
    print("\nmanifest: %s" % mf)
    print("\nNow check the live launcher still resolves:")
    print("  %s" % KEEP["Tender_brief_launcher"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
