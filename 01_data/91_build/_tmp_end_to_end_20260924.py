"""End-to-end consistency check of everything this session touched."""
import csv
import json
from pathlib import Path
import pandas as pd

R = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = R / "01_data" / "00_derived"
ok = True

def chk(label, cond, detail=""):
    global ok
    print(f"{'PASS' if cond else 'FAIL'}  {label}{('  ' + detail) if detail else ''}")
    if not cond:
        ok = False

print("=== grain ===")
g = pd.read_csv(D / "warranty_raw_grain.csv", low_memory=False)
g["assess_month"] = g["assess_month"].astype(str)
chk("grain rows = 63,763", len(g) == 63763, f"got {len(g)}")
lcv = g[(g.segment == "LCV") & (g.assess_month >= "202605") & (g.db_name != "UMI")]
chk("May-Aug 2026 from the new export = 5,048", len(lcv) == 5048, f"got {len(lcv)}")
chk("no 202609+ rows (file ends Aug 2026)", (g.assess_month > "202608").sum() == 0)

print("\n=== extension file ===")
e = pd.read_csv(D / "warranty_lcv_extension_202510_202608.csv", low_memory=False)
chk("extension holds 14,105 lines", len(e) == 14105, f"got {len(e)}")
chk("extension months 202510..202608",
    e.assess_month.astype(str).min() == "202510" and e.assess_month.astype(str).max() == "202608")

print("\n=== FY file ===")
with open(D / "distributor_warranty_expense_fiscal.csv", encoding="utf-8") as f:
    fy = list(csv.DictReader(f))
hdr = list(fy[0].keys())
chk("FY header unchanged for old readers",
    hdr[:4] == ["db", "warr_FY2024", "warr_FY2025", "warr_FY2026"], str(hdr))
chk("FY2027_partial column appended", "warr_FY2027_partial" in hdr)
t = {c: sum(int(r[c]) for r in fy) for c in ["warr_FY2024", "warr_FY2025", "warr_FY2026"]}
chk("FY2024 total unchanged 3,394,685", t["warr_FY2024"] == 3394685, str(t["warr_FY2024"]))
chk("FY2025 total unchanged 3,521,957", t["warr_FY2025"] == 3521957, str(t["warr_FY2025"]))
chk("FY2026 total unchanged 5,664,684", t["warr_FY2026"] == 5664684, str(t["warr_FY2026"]))
fy27 = sum(int(r["warr_FY2027_partial"]) for r in fy)
chk("FY2027 part-year populated", fy27 > 0, f"{fy27:,}")

print("\n=== monthly file ===")
with open(D / "warranty_fy26_monthly.csv", encoding="utf-8") as f:
    mo = list(csv.DictReader(f))
months = [r["AssessMonth"] for r in mo]
chk("no month missing 202504..202608",
    months == [f"2025{m:02d}" for m in range(4, 13)] + [f"2026{m:02d}" for m in range(1, 9)],
    f"{len(months)} rows")
chk("Dec-2025 present", "202512" in months)
chk("previous rows unchanged (202504-202511)",
    all(float(next(r for r in mo if r["AssessMonth"] == m)["Total_USD"]) == v
        for m, v in [("202504", 675207.0), ("202511", 626946.0)]))

print("\n=== register ===")
reg = (D / "_data_integrity_open_issues.md").read_text(encoding="utf-8")
chk("register is the full version", len(reg.splitlines()) > 150, f"{len(reg.splitlines())} lines")
chk("LCV-DEC closed", "CLOSED 2026-09-24" in reg)
chk("LCV-EXT logged", "LCV-EXT" in reg)
chk("currency rule logged", "LCV-CURRENCY-RULE" in reg)
chk("MIDI logged", "MIDI-WARR" in reg)
chk("no stale 'one month short' open claim", "incomplete by one month at the end. GPS CY2025 used the extract as-is. | Next" not in reg)

print("\n=== pages ===")
hub = (R / "02_dashboards" / "hub" / "ISZE_OS_Hub.html").read_text(encoding="utf-8")
con = (R / "02_dashboards" / "ops" / "ISZE_OS_Console.html").read_text(encoding="utf-8")
chk("hub has LCV-EXT", "LCV-EXT" in hub)
chk("hub has 1.08M", "EUR 1.08M" in hub)
chk("console has new pickup item", "Pickup warranty is only read to April 2026" in con)
chk("console no longer says next export is the blocker", "Next light-commercial claim export" not in con)

print("\n=== module ===")
m = (R / "02_dashboards" / "_composable" / "modules" / "warranty_monthly.mjs").read_text(encoding="utf-8")
chk("module no longer says Dec-2025 missing", "Dec-2025 is missing from the source" not in m)
chk("module warns about the definition change", "changes what it counts" in m)

print("\n" + ("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED"))
