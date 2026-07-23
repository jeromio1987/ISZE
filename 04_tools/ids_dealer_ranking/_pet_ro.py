import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from openpyxl import load_workbook
from build_ids_result_report import parse_dealer_workbook, QUESTION_RE, _open_eval_rows, _parse_eval_rows, find_eval_sheet

# Petros: find source values > max
pet = Path(r"..\..\01_data\90_INBOX\IDS_2026\Petros")
files = sorted([p for p in pet.rglob("*.xlsx") if not p.name.startswith("~$")])
print("petros files", len(files))
overs = []
for f in files:
    sheetnames, eval_sheet, rows_iter, err = _open_eval_rows(f)
    if err: continue
    for row in rows_iter():
        if not row or len(row)<8: continue
        no = row[1] if len(row)>1 else None
        if not no: continue
        ref = str(no).strip()
        if not QUESTION_RE.match(ref): continue
        mx = row[6] if len(row)>6 else None
        if not isinstance(mx,(int,float)): continue
        # self-eval often col 11
        raw = row[11] if len(row)>11 else None
        if isinstance(raw,(int,float)) and float(raw) > float(mx):
            overs.append((f.name[:40], ref, raw, mx))
print("over-max raw self-eval cells", len(overs))
for o in overs[:20]:
    print(o)

# Romania: compare source sum vs report for ANVELO
from ids_report_extract import extract_result_report
ro_rep = Path(r"..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_Romania.xls")
_, recs, _ = extract_result_report(ro_rep)
by = {r.name: r for r in recs}
ro = Path(r"..\..\01_data\90_INBOX\IDS_2026\Romania")
for f in sorted(ro.glob("*.xlsx")):
    if "ANVELO" in f.name.upper() or "SIMODE" in f.name.upper() or "RODAV" in f.name.upper():
        d = parse_dealer_workbook(f)
        s = sum(d.question_scores.values())
        # match name
        print(f.name[:50], "parsed_sum", s, "nQ", len(d.question_scores), "err", d.error, "name", d.name)
