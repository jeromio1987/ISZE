from pathlib import Path
import openpyxl
base=Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imotors_bo_compare_20261006")
print("==== FINDINGS ====")
print(base.joinpath("IMOTORS_BO_AIM_ANALYSIS_20261006","FINDINGS.md").read_text(encoding="utf-8-sig"))
print("==== SOURCE ====")
print(base.joinpath("SOURCE.md").read_text(encoding="utf-8"))
wb=openpyxl.load_workbook(base/"EXPORT_ISZE_Order_20261006.xlsx", read_only=True, data_only=True)
ws=wb[wb.sheetnames[0]]
rows=ws.iter_rows(values_only=True)
hdr=list(next(rows))
print("SHEET", wb.sheetnames[0], "NCOLS", len(hdr))
for i,h in enumerate(hdr):
    print(i, repr(h))
# find 519 rows and describe open qty fields
idx={str(h):i for i,h in enumerate(hdr)}
# guess sold-to
candidates=[h for h in hdr if h and any(x in str(h).lower() for x in ["sold","payer","customer","ship-to","sold-to"])]
print("CAND", candidates)
# scan a few 519 rows
count=0
open_like=[]
for r in rows:
    # try common sold-to positions
    vals=[str(v) if v is not None else "" for v in r]
    if "519" not in vals and "IMOTORS" not in " ".join(vals).upper() and "I-MOTORS" not in " ".join(vals).upper():
        continue
    count+=1
    if count<=3:
        d=dict(zip(hdr,r))
        for k,v in d.items():
            if v is None or v=="": continue
            ks=str(k).lower()
            if any(x in ks for x in ["sold","order","qty","open","status","create","doc","sa ty","saty","material","amount","net","customer","confirm","deliv","plant"]):
                print("R",count,k,"=>",v)
    if count>=5000:
        break
print("MATCHED_ROWS_SCANNED", count)
wb.close()

# KPI
kpi=Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_nuno_kpi_portugal_20261001")
for p in kpi.rglob("*"):
    if p.is_file():
        print("KPI_FILE", p.name)
xlsx=list(kpi.glob("*.xlsx"))[0]
wb=openpyxl.load_workbook(xlsx, data_only=True, read_only=True)
print("KPI sheets", wb.sheetnames)
for sn in wb.sheetnames:
    ws=wb[sn]
    print("---", sn)
    for i,row in enumerate(ws.iter_rows(values_only=True)):
        if i>55: break
        vals=[v for v in row if v is not None and str(v).strip()!=""]
        if vals:
            print(i, vals[:14])
wb.close()

# search BO files
root=Path(r"C:\Users\jerom\Desktop\claude\ISZE")
hits=[]
for folder in [root/"01_data"/"90_INBOX", root/"09_meetings"/"Imotors_Portugal_IDS_2026", root/"01_data"/"08_Distributor"]:
    if not folder.exists():
        continue
    for p in folder.rglob("*"):
        if not p.is_file():
            continue
        n=p.name.upper()
        if any(x in n for x in ["IMOTOR","PORTUGAL","ASTARA"]) and any(y in n for y in ["BO","BACK","ORDER","OVERVIEW","OPEN","KPI"]):
            hits.append(str(p))
print("HITS", len(hits))
for h in hits[:50]:
    print(h)
