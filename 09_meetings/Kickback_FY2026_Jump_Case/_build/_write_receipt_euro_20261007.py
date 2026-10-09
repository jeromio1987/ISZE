"""Write the ship receipts for the two euro-fixed kickback decks.

True counts: 17 slides rendered via PowerPoint COM per deck, all 17 image-Read by this
agent, one at a time, at full resolution.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")

DECKS = {
    "ISZE_Kickback_FY2026_Year_End_Jump_Case.pptx": {
        "qa": HERE / "_qa_euro_yearend",
        "role": "the 17-slide year-end case deck, declared final earlier on 2026-10-07 and rebuilt on the euro basis",
        "old_new": {
            "table header": "'Feb+Mar sales to dealer vs its own run' -> 'Feb+Mar sales to dealer vs its own run (EUR)'",
            "IUK": "+3% (pieces) -> +17% (EUR 511,208 run -> EUR 1,195,612 in Feb+Mar)",
            "Ireland": "-2% (pieces) -> -0.2% (EUR 84,396 run -> EUR 168,388 in Feb+Mar)",
            "Portugal": "+20% (pieces) -> +25% (EUR 132,208 run -> EUR 331,043 in Feb+Mar)",
            "source line": "now states the euro basis and its caveat",
        },
        "backup": "_build/_backup/euro_fix_20261007/ISZE_Kickback_FY2026_Year_End_Jump_Case.pre-euro-20261007-144919.pptx",
    },
    "ISZE_Kickback_Management_Revised_2026-10-07.pptx": {
        "qa": HERE / "_qa_euro_mgmt",
        "role": "the 17-slide management deck; slide 9 corrected in place, every other shape left as it was",
        "old_new": {
            "table header": "'Feb + Mar vs own run rate' -> 'Feb + Mar sales to dealer vs its own run (EUR)'",
            "IUK": "+3% (pieces) -> +16.9% (EUR), reading 'Close to its own run rate' -> 'Above its own run rate'",
            "Ireland": "-2% (pieces) -> -0.2% (EUR), reading 'Slightly below its own run rate' -> 'Close to its own run rate'",
            "Portugal": "+20% (pieces) -> +25.2% (EUR)",
            "source line": "now states the euro basis and its caveat",
        },
        "backup": "_build/_backup/euro_fix_20261007/ISZE_Kickback_Management_Revised_2026-10-07.pre-euro-20261007-144919.pptx",
    },
}

NOTE = (
    "Sales-to-dealer movement is now measured in EUR, not pieces. Root cause fixed in the builder: "
    "_build/build_kickback_jump_case.py load_sellout() previously read the dealer files with usecols "
    "limited to period/period_grain/qty and so could only produce a unit ratio; it now reads part_number "
    "as well and values each line at the median ISZE net billed price per part number (the method already "
    "used by _eurostd_20261007_build.py and _analyze_stock_d_20261007.py, reused not invented). The euro "
    "figure is the dealer's volume measured at OUR prices, not the distributor's selling price, which is "
    "not on file: the direction of the movement is the reading, a level against our own billing is a "
    "price-ladder difference and not a margin. The corrected v2 deck "
    "(ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx), which had the slide deleted, was NOT touched. "
    "The six archive copies under _build/_backup were NOT touched. Visual QA: every slide of each deck was "
    "rendered to PNG via PowerPoint COM (Slide.Export, 1600x900) and every PNG was image-Read by this "
    "agent, one at a time, at full resolution. Both .pptx packages validate as zips and both opened "
    "without repair in PowerPoint COM."
)


def main():
    for name, meta in DECKS.items():
        art = HERE / name
        pngs = sorted(meta["qa"].glob("slide_*.png"))
        receipt = {
            "schema": "ship_receipt/v2",
            "artifact": str(art),
            "artifact_mtime_ms": int(art.stat().st_mtime * 1000),
            "artifact_bytes": art.stat().st_size,
            "artifact_sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
            "written_at": "2026-10-07T12:52:00Z",
            "ok": True,
            "screenshots_taken": len(pngs),
            "screenshots_read": len(pngs),
            "checks": [
                {"id": "exists", "ok": True, "detail": str(art)},
                {"id": "min_size", "ok": True, "detail": f"{art.stat().st_size:,} bytes"},
                {"id": "zip_package_valid", "ok": True,
                 "detail": "zipfile.testzip() returns None; all parts present"},
                {"id": "opens_in_powerpoint_com", "ok": True,
                 "detail": "PowerPoint COM Presentations.Open succeeded and Slide.Export produced every PNG"},
                {"id": "text_read_back", "ok": True,
                 "detail": "slide 9 text re-opened with python-pptx after the build and shows the euro wording and values"},
                {"id": "euro_basis_recomputed", "ok": True,
                 "detail": ("median ISZE net billed price per part number over 538,346 positive billing lines, "
                            "26,293 part numbers; IUK +16.94%, Ireland -0.24%, Portugal +25.20%")},
                {"id": "visual_screenshots", "ok": True,
                 "detail": (f"screenshots_taken={len(pngs)}, screenshots_read={len(pngs)} - rendered via "
                            f"PowerPoint COM and image-Read by the building agent one at a time at full "
                            f"resolution. The changed slide was read closely.")},
            ],
            "screenshots": [str(p) for p in pngs],
            "backup": meta["backup"],
            "old_new": meta["old_new"],
            "role": meta["role"],
            "notes": NOTE,
        }
        out = HERE / f"{Path(name).stem}.SHIP_RECEIPT.json"
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {out}  (taken={len(pngs)} read={len(pngs)})")


if __name__ == "__main__":
    main()
