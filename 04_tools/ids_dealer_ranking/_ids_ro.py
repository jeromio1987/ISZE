import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import xlrd
from build_ids_result_report import COL_FIRST_DEALER, ROW_META_START, ROW_SCORE_ORIG, ROW_SCORE_PCT
from ids_report_extract import extract_result_report

# Compare Romania_tb vs our Romania report
ours = Path(r"..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_Romania.xls")
tb = Path(r"C:\Users\jerom\Downloads\2026 IDS Evaluation Result Report_Romania_tb.xls")
print("ours exists", ours.exists(), "tb", tb.exists())

for label, path in [("OURS", ours), ("TB", tb)]:
    if not path.exists():
        print(label, "missing"); continue
    country, recs, _, _ = extract_result_report(path)
    print(f"\n=== {label} country={country} n={len(recs)} ===")
    for r in sorted(recs, key=lambda x: x.name.lower()):
        print(f"  {r.name[:40]:40} tot={r.total} pct={None if r.total_pct is None else round(r.total_pct*100,2)}")
