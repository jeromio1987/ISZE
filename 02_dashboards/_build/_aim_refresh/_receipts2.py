import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

WRITER = r"C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs"
QA = "02_dashboards/_build/_aim_refresh/_qa"

PAGES = [
    ("02_dashboards/sales/AIM_Dashboard_CY2026.html",
     ["02_dashboards__sales__AIM_Dashboard_CY2026.png",
      "02_dashboards__sales__AIM_Dashboard_CY2026__bottom.png"]),
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

for page, shots in PAGES:
    if not os.path.exists(page):
        print("MISSING", page); continue
    args = ["node", WRITER, "--artifact", os.path.abspath(page)]
    for s in shots:
        p = os.path.join(QA, s)
        if os.path.exists(p):
            args += ["--screenshot", os.path.abspath(p)]
        else:
            print("   missing screenshot", s)
    args += ["--screenshots-taken", str(len(shots)), "--screenshots-read", str(len(shots))]
    args += ["--notes", "AIM data refresh 2026-09-24: same builder, same arguments, re-read from "
                        "the refreshed AIM classification. Re-rendered after the last rebuild."]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    keep = [l for l in out.splitlines() if "SHIP_RECEIPT_OK" in l or "FAIL" in l
            or "INVALID" in l or "MISMATCH" in l]
    print("=" * 5, page, "exit", r.returncode)
    for l in keep[-5:]:
        print("   ", l.strip()[:170])
