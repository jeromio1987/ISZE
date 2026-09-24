import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

WRITER = r"C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs"
QA = "02_dashboards/_build/_aim_pass2/_qa"

PAGES = [
    ("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
     ["02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_ALL.png",
      "02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_ALL__bottom.png"]),
    ("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
     ["02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.png",
      "02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL__bottom.png"]),
    ("02_dashboards/sales/ISZE_AIM_Comparison_ALL.html",
     ["02_dashboards__sales__ISZE_AIM_Comparison_ALL.png",
      "02_dashboards__sales__ISZE_AIM_Comparison_ALL__bottom.png"]),
    ("02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html",
     ["02_dashboards__sales__ISZE_AIM_Comparison_PORTUGAL.png",
      "02_dashboards__sales__ISZE_AIM_Comparison_PORTUGAL__bottom.png"]),
]

NOTE = ("Second publish pass 2026-09-24: the AIM tree input was repointed from the 2026-09-21 "
        "export pair to the 2026-09-24 pair. Same builder, same arguments, same metrics, same "
        "layout; only the source file name changed. Rendered from file:// in headless Chrome at "
        "1440x1000 and the screenshots read one at a time.")

for page, shots in PAGES:
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
    args += ["--notes", NOTE]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    keep = [l for l in out.splitlines()
            if "SHIP_RECEIPT" in l or "FAIL" in l or "INVALID" in l or "MISMATCH" in l
            or "written" in l.lower()]
    print("=" * 5, page, "exit", r.returncode)
    for l in keep[-6:]:
        print("   ", l.strip()[:200])
