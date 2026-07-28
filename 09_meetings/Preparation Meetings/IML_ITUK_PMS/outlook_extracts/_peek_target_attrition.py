# Peek Target Study + Attrition and compare to N75 PMS study
from openpyxl import load_workbook
from pathlib import Path
import json

out_dir = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Preparation Meetings\IML_ITUK_PMS\outlook_extracts"
)
target = out_dir / "ITUK_Parts_Sales_Target_Study_20260409.xlsx"
# also check Downloads for Attrition after download
dl = Path(r"C:\Users\jerom\Downloads")

def peek(path, max_rows=40, max_cols=14):
    wb = load_workbook(path, data_only=True)
    result = {"file": path.name, "sheets": {}}
    for s in wb.sheetnames:
        ws = wb[s]
        rows = []
        for i, row in enumerate(ws.iter_rows(max_row=max_rows, max_col=max_cols, values_only=True), 1):
            if any(c is not None and str(c).strip() != "" for c in row):
                cleaned = []
                for c in row:
                    if c is None:
                        cleaned.append(None)
                    elif isinstance(c, float):
                        cleaned.append(round(c, 4))
                    else:
                        cleaned.append(str(c)[:80])
                rows.append({"r": i, "v": cleaned})
        result["sheets"][s] = rows
    return result

print("TARGET sheets", load_workbook(target).sheetnames)
t = peek(target, max_rows=50, max_cols=16)
(out_dir / "peek_Target_Study.json").write_text(json.dumps(t, indent=1, ensure_ascii=True), encoding="utf-8")
print("wrote peek_Target_Study.json")

# Attrition candidates
cands = list(dl.glob("*ttrit*")) + list(dl.glob("*Attrit*")) + list(out_dir.glob("*ttrit*"))
print("attrition cands", [str(p) for p in cands])
for p in cands:
    dest = out_dir / "Attrition_Rate.xlsx"
    if p.resolve() != dest.resolve():
        dest.write_bytes(p.read_bytes())
    a = peek(dest, max_rows=40, max_cols=12)
    (out_dir / "peek_Attrition_Rate.json").write_text(json.dumps(a, indent=1, ensure_ascii=True), encoding="utf-8")
    print("wrote attrition peek", dest)
    break
