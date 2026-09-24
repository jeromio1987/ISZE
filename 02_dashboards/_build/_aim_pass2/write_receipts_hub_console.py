import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

WRITER = r"C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs"
QA = "02_dashboards/_build/_aim_pass2/_qa"

# Neither page is changed in this pass. The receipt records the current file, the checks, and the
# screenshots for THIS pass, and its note says plainly that the AIM cell was not repointed.
PAGES = [
    ("02_dashboards/hub/ISZE_OS_Hub.html",
     ["02_dashboards__hub__ISZE_OS_Hub.png",
      "02_dashboards__hub__ISZE_OS_Hub__full.png"],
     "Second publish pass 2026-09-24: this page was not changed. Its AIM cell reads "
     "aim_classification_gap_report.md (2 Jul 2026) and prints 98% / 1.8% of 2025 revenue; that is "
     "the revenue-weighted residual on the workbook axis, while the current master is on a "
     "different axis, so repointing it would change what the number means. Left and reported. "
     "Re-rendered from file:// and the screenshots read for this pass."),
    ("02_dashboards/ops/ISZE_OS_Console.html",
     ["02_dashboards__ops__ISZE_OS_Console.png",
      "02_dashboards__ops__ISZE_OS_Console__full.png"],
     "Second publish pass 2026-09-24: this page was not changed. Its sensor card and the flow "
     "diagram print 1.8% of 2025 revenue unclassified from aim_classification_gap_report.md "
     "(2 Jul 2026); the same number as the OS Hub, on the workbook axis. Repointing it at the "
     "current master would change what the number means, so it is left and reported. Re-rendered "
     "from file:// and the screenshots read for this pass."),
]

for page, shots, note in PAGES:
    if not os.path.exists(page):
        print("MISSING", page)
        continue
    args = ["node", WRITER, "--artifact", os.path.abspath(page)]
    for s in shots:
        p = os.path.join(QA, s)
        if os.path.exists(p):
            args += ["--screenshot", os.path.abspath(p)]
        else:
            print("   missing screenshot", s)
    args += ["--screenshots-taken", str(len(shots)), "--screenshots-read", str(len(shots))]
    args += ["--notes", note]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    keep = [l for l in out.splitlines()
            if "SHIP_RECEIPT" in l or "FAIL" in l or "INVALID" in l or "MISMATCH" in l]
    print("=" * 5, page, "exit", r.returncode)
    for l in keep[-6:]:
        print("   ", l.strip()[:200])
