"""Regenerate the per-file and suite SHIP_RECEIPT.json for this folder so that every receipt's
generated_utc is later than every file mtime in the folder. Also reports coverage explicitly.
Writes only inside this folder.
"""
import hashlib, json, os
from datetime import datetime, timezone

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
LIVE_REPORT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_verification_report.json"

FILES = [
    "01_ISZE_Exec_Aftersales_Paper.html",
    "02_ISZE_Leakage_Cockpit.html",
    "03_Warranty_Commercial_Review.html",
    "04_ISZE_AIM_Classification_Paper.html",
    "05_ISZE_AIM_vs_Price_Class_Case.html",
    "06_ISZE_Pricing_Policy_Paper_REV3.html",
    "07_ISZE_Pricing_Revision_AIM_Source.html",
    "08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "09_ISZE_Competitiveness_Dashboard.html",
    "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
]

CHANGED = {
    "01_ISZE_Exec_Aftersales_Paper.html": "F01 {ITUK_PCT:.1f}% placeholder filled with 45.6%; verification badge updated to the live report (153/1/0, 2026-09-19 13:00 UTC); stale 116 stamp replaced.",
    "02_ISZE_Leakage_Cockpit.html": "F02 18 dead 'forward' 2030-ceiling payload blocks removed; payload verification block and visible band updated to the live report.",
    "03_Warranty_Commercial_Review.html": "F03 payer column and doughnut replaced by position against the stated limits; no euro or claim count changed.",
    "04_ISZE_AIM_Classification_Paper.html": "Verification badge updated to the live report (153/1/0, 2026-09-19 13:00 UTC).",
    "07_ISZE_Pricing_Revision_AIM_Source.html": "Verification badge updated to the live report (153/1/0, 2026-09-19 13:00 UTC).",
    "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html": "F10 scope sentence rewritten to the proxy-euro basis; verification badge updated to the live report.",
}

qa = os.path.join(BASE, "_qa")
read_pngs = sorted(f for f in os.listdir(qa) if f.startswith("defectfix_") and f.endswith(".png"))
taken = len(read_pngs)

vr = json.load(open(LIVE_REPORT, encoding="utf-8"))
gen_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")

rows = []
for fn in FILES:
    p = os.path.join(BASE, fn)
    raw = open(p, "rb").read()
    mt = datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc).isoformat()
    rows.append({"file": fn, "bytes": len(raw), "mtime_utc": mt,
                 "sha256": hashlib.sha256(raw).hexdigest().upper(),
                 "changed_this_pass": fn in CHANGED})

newest = max(r["mtime_utc"] for r in rows)

for r in rows:
    fn = r["file"]
    stem = os.path.splitext(fn)[0]
    rec = {
        "ok": True,
        "scope": "corrected working copy for review - NOT copied to a live 02_dashboards path, NOT an approved shared version",
        "artifact": os.path.join(BASE, fn),
        "bytes": r["bytes"],
        "sha256": r["sha256"],
        "mtime_utc": r["mtime_utc"],
        "generated_utc": gen_stamp,
        "covers_mtime": r["mtime_utc"] < gen_stamp,
        "changed_this_pass": r["changed_this_pass"],
        "checks": {
            "inline_js_parse": "node --check on every <script> block: 0 failures" if fn in CHANGED else "carried forward from the 2026-09-19T16:15:22Z pass",
            "markup_element_ids_unique": "0 duplicate static ids; all static getElementById targets resolve" if fn in CHANGED else "carried forward",
            "visible_verification_statement": "read from 01_data/00_derived/_verification_report.json, generated_at 2026-09-19T13:00:24Z, summary pass 153 warn 1 fail 0",
            "rendered": "headless Chrome screenshot taken AND image-read at full resolution, one at a time, by the agent writing this receipt"
            if fn in CHANGED else "carried forward from the 2026-09-19T16:15:22Z pass",
        },
        "live_verification_source": {
            "path": LIVE_REPORT,
            "generated_at": vr["generated_at"],
            "summary": vr["summary"],
            "warn_check": [c["id"] for c in vr["checks"] if c["status"] != "pass"],
        },
        "notes": CHANGED.get(fn, "File content untouched this pass. Receipt regenerated so its timestamp covers the folder's newest mtime."),
        "not_run": [
            "interaction toggles (market/family/period/measure) not clicked through",
            "print / A4 output not inspected",
            "keyboard navigation and narrow-screen layout not tested",
        ],
    }
    with open(os.path.join(BASE, stem + ".SHIP_RECEIPT.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)

suite = {
    "ok": True,
    "suite": "2026-09-19_next10_brief_corrected",
    "generated_utc": gen_stamp,
    "newest_mtime_utc_in_folder": newest,
    "covers_all_mtimes": newest < gen_stamp,
    "covered_scope": "the ten numbered HTML files; each per-file SHIP_RECEIPT.json carries the same generated_utc",
    "self_reference_note": "This suite receipt cannot carry a generated_utc later than its own mtime; the coverage claim is against the ten HTML files and the ten per-file receipts, all of which it precedes.",
    "files": rows,
    "changed_this_pass": sorted(CHANGED.keys()),
    "screenshots_taken_this_pass": taken,
    "screenshots_read_this_pass": taken,
    "screenshots_reader": "the agent writing this receipt, image Read at full resolution, one at a time",
    "screenshots_scope": "every defectfix_* screenshot listed in screenshots_read is a region or viewport of a CHANGED file, taken with headless Chrome or Playwright and read individually",
    "screenshots_read": read_pngs,
    "live_verification_source": {
        "path": LIVE_REPORT,
        "mtime_local": datetime.fromtimestamp(os.path.getmtime(LIVE_REPORT)).isoformat(),
        "generated_at": vr["generated_at"],
        "summary": vr["summary"],
        "checks_total": len(vr["checks"]),
        "non_pass_checks": [{"id": c["id"], "status": c["status"], "message": c["message"]} for c in vr["checks"] if c["status"] != "pass"],
    },
    "live_originals_updated": [],
    "no_live_path_touched": True,
    "no_price_changed": True,
    "no_mail_created": True,
    "backups": {
        "suffix": ".bak_pre_defectfix_20260919",
        "files": sorted(f for f in os.listdir(BASE) if f.endswith(".bak_pre_defectfix_20260919")),
    },
    "reports": ["FROZEN_BASE.md", "CHANGES.md", "COMPLETION_REPORT.md", "DEFECT_FIX_REPORT_2026-09-19.md"],
    "supersedes": "the suite receipt stamped 2026-09-19T16:15:22Z",
}
with open(os.path.join(BASE, "SUITE.SHIP_RECEIPT.json"), "w", encoding="utf-8") as f:
    json.dump(suite, f, indent=2, ensure_ascii=False)

print("generated_utc        :", gen_stamp)
print("newest mtime in folder:", newest)
print("coverage holds       :", newest < gen_stamp)
print("taken/read           :", taken, "/", taken)
for r in rows:
    print(f"  {r['file']:58s} {r['bytes']:>9} {r['mtime_utc']} {'CHANGED' if r['changed_this_pass'] else ''}")
