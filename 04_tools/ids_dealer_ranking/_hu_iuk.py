import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from build_ids_result_report import parse_dealer_workbook, _coerce_score, COL_MAX
from ids_report_extract import extract_result_report
import xlrd

# Hungary uniqueness check
hu = Path(r"..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_Hungary.xls")
c, recs, _, _ = extract_result_report(hu)
totals = sorted({(r.total, round(r.total_pct*100,2) if r.total_pct else None) for r in recs})
print("HUNGARY unique totals", totals, "n", len(recs))
print("top3", [(r.name, r.total, round(r.total_pct*100,1)) for r in sorted(recs, key=lambda x: -(x.total or 0))[:3]])
print("bot3", [(r.name, r.total, round(r.total_pct*100,1)) for r in sorted(recs, key=lambda x: (x.total or 0))[:3]])

# IUK missing names
iuk = Path(r"..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_IUK.xls")
c, recs, _, _ = extract_result_report(iuk)
print("\nIUK dealers", len(recs))
for r in recs:
    bad = (not r.name) or r.name.startswith("*") or "Write your" in r.name or r.name.strip()==""
    if bad or len(r.name)<3:
        print(" BAD NAME:", repr(r.name), "tot", r.total)
# also raw meta row
rb = xlrd.open_workbook(str(iuk))
sh = rb.sheet_by_index(0)
from build_ids_result_report import COL_FIRST_DEALER, ROW_META_START
print("IUK raw names:")
for col in range(COL_FIRST_DEALER, sh.ncols):
    name = sh.cell_value(ROW_META_START, col)
    if name=="" or name is None: break
    print(f"  {col}: {name!r}")

# Petros source: any score > max before cap?
pet = Path(r"..\..\01_data\90_INBOX\IDS_2026\Petros")
files = sorted(pet.rglob("*.xlsx"))
print("\nPetros files", len(files))
from build_ids_result_report import parse_dealer_workbook
over_dealers = []
for f in files[:40]:
    d = parse_dealer_workbook(f)
    # can't easily get max per question from parse - check raw later
print("parsed sample", files[0].name if files else None)
