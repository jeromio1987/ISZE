"""_b_iml.py -- hunt for a Greek (and Cyprus) registration series."""
import io, sys, zipfile, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

IML = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\IML calculation (1).xlsx"
MAT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\07_UIO\Matriculas Isuzu SAP.xlsx"

wb = openpyxl.load_workbook(IML, data_only=True)
print("IML SHEETS:", wb.sheetnames)
for sn in wb.sheetnames:
    ws = wb[sn]
    print("\n---- IML :: %s  (%s) ----" % (sn, ws.calculate_dimension()))
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=min(ws.max_row, 45),
                                         max_col=min(ws.max_column, 26), values_only=True), 1):
        cells = [("" if c is None else (("%g" % c) if isinstance(c, float) else str(c)))[:24] for c in row]
        while cells and cells[-1] == "":
            cells.pop()
        if cells:
            print("%3d| %s" % (i, " | ".join(cells)))
wb.close()

wb = openpyxl.load_workbook(MAT, data_only=True)
ws = wb["SUM"]
print("\n#### Matriculas SUM full ####")
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=40, max_col=40, values_only=True), 1):
    cells = [("" if c is None else (("%g" % c) if isinstance(c, float) else str(c)))[:16] for c in row]
    while cells and cells[-1] == "":
        cells.pop()
    if cells:
        print("%3d| %s" % (i, " | ".join(cells)))
wb.close()

# grep anything that looks like a Greek/Cyprus registration series in the workbook xml
import glob, os
print("\n#### string hunt for GREECE / GR / PETROS across xlsx in 01_data + 06_uio ####")
pats = re.compile(r"(?i)(greece|petros|greek|Ελλ|κύπρ|cyprus|loutsios)", re.UNICODE)
root = r"C:\Users\jerom\Desktop\claude\ISZE"
hits = 0
for base in (root + r"\01_data\07_UIO", root + r"\06_uio\_SourceData", root + r"\01_data\08_Distributor"):
    for dp, dn, fn in os.walk(base):
        for f in fn:
            if not f.lower().endswith((".xlsx", ".xlsm", ".xls")):
                continue
            p = os.path.join(dp, f)
            try:
                z = zipfile.ZipFile(p)
                blob = b""
                for n in z.namelist():
                    if n.endswith(".xml") or n.endswith(".rels"):
                        blob += z.read(n)[:400000]
                txt = blob.decode("utf-8", "ignore")
                m = pats.findall(txt)
                if m:
                    from collections import Counter
                    print("  HIT %s :: %s" % (os.path.basename(p), Counter(x.lower() for x in m).most_common(6)))
                    hits += 1
            except Exception:
                pass
print("files with hits:", hits)
