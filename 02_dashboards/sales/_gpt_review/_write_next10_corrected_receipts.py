# -*- coding: utf-8 -*-
"""Write honest ship receipts for the corrected next10 pack.

The copied receipts from the previous pass point at the OLD folder and assert that live originals
were overwritten. Both statements are now false for this pack, so they are replaced rather than left
in place. These receipts record exactly the checks that ran here, and name what did not run.
"""
import io, json, os, sys
from datetime import datetime, timezone

D = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
QA = os.path.join(D, "_qa")
NOW = datetime.now(timezone.utc).isoformat()

FILES = [
    ("01_ISZE_Exec_Aftersales_Paper.html", "P0"),
    ("02_ISZE_Leakage_Cockpit.html", "P0"),
    ("03_Warranty_Commercial_Review.html", "P0"),
    ("04_ISZE_AIM_Classification_Paper.html", "P1"),
    ("05_ISZE_AIM_vs_Price_Class_Case.html", "P0"),
    ("06_ISZE_Pricing_Policy_Paper_REV3.html", "P0"),
    ("07_ISZE_Pricing_Revision_AIM_Source.html", "P1"),
    ("08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html", "P0"),
    ("09_ISZE_Competitiveness_Dashboard.html", "P0"),
    ("10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html", "P1"),
]

COMMON_CHECKS = {
    "inline_js_parse": "node --check on every inline <script> block: 0 failures",
    "markup_element_ids_unique": "0 duplicate ids in markup (script and style content excluded)",
    "visible_banned_language_sweep": "scanned visible text for wallet / sell-out / street / parc / Mode A-B / Book B / IML v7 / Model B / agent vocabulary / internal file names",
    "first_viewport_rendered": "headless Chrome 1440x900, screenshot taken and read at full resolution",
    "blank_page_check": "ink coverage and rows-with-ink measured per screenshot; no blank or near-blank page",
}

NOT_RUN = [
    "interaction: distributor / account / source / family / period / measure toggles not clicked through",
    "reset, deep drill-down and drill-back not exercised",
    "keyboard navigation, focus visibility, zoom and narrow-screen layout not tested",
    "print / A4 output not inspected for the paper-style files",
    "heatmap hover versus global table-hover colour behaviour not tested",
    "cross-artefact numeric reconciliation not run",
]

written = []
for fn, prio in FILES:
    path = os.path.join(D, fn)
    mtime = datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat()
    png = os.path.join(QA, os.path.splitext(fn)[0] + "_viewport.png")
    rec = {
        "ok": True,
        "scope": "corrected working copy for review — NOT copied to a live 02_dashboards path, NOT an approved shared version",
        "artifact": path,
        "priority_in_brief": prio,
        "mtime_utc": mtime,
        "generated_utc": NOW,
        "checks": dict(COMMON_CHECKS),
        "screenshot": {
            "path": png,
            "exists": os.path.exists(png),
            "taken": 1,
            "read": 1,
            "reader": "agent image Read at full resolution",
        },
        "not_run": NOT_RUN,
        "supersedes": "the receipt copied from 2026-09-19_next10_fixed, which described an earlier "
                      "file version and asserted live originals were overwritten",
        "notes": "Corrections applied against ISZE_Ten_File_Review_and_Fix_Brief_2026-09-19.md. "
                 "See COMPLETION_REPORT.md for per-file detail and the unresolved items.",
    }
    out = os.path.join(D, os.path.splitext(fn)[0] + ".SHIP_RECEIPT.json")
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, ensure_ascii=False)
    written.append(os.path.basename(out))

suite = {
    "ok": True,
    "suite": "2026-09-19_next10_brief_corrected",
    "brief": r"C:\Users\jerom\Desktop\claude\ISZE_Ten_File_Review_and_Fix_Brief_2026-09-19.md",
    "generated_utc": NOW,
    "files": [f for f, _ in FILES],
    "screenshots_taken": 10,
    "screenshots_read": 10,
    "screenshots_reader": "agent image Read at full resolution",
    "live_originals_updated": [],
    "no_live_path_touched": True,
    "no_price_changed": True,
    "no_mail_created": True,
    "not_run": NOT_RUN,
    "reports": ["COMPLETION_REPORT.md", "CHANGES.md", "INDEX.md"],
}
with io.open(os.path.join(D, "SUITE.SHIP_RECEIPT.json"), "w", encoding="utf-8") as fh:
    json.dump(suite, fh, indent=2, ensure_ascii=False)

print("\n".join(written))
print("SUITE.SHIP_RECEIPT.json")
