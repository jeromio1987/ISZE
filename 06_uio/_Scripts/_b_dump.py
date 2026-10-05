"""_b_dump.py -- full dump of the candidate registration sources."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

def dump(path, sheet, maxr=100, maxc=30, label=""):
    print("=" * 110)
    print("%s :: %s :: %s" % (label, path, sheet))
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet]
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=maxr, max_col=maxc, values_only=True), 1):
        cells = [("" if c is None else (("%g" % c) if isinstance(c, float) else str(c)))[:22] for c in row]
        while cells and cells[-1] == "":
            cells.pop()
        print("%3d | %s" % (i, " | ".join(cells)))
    wb.close()

PT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\08_Distributor\Imotors_Portugal_UIO_GPS_PMS_Study.xlsx"
dump(PT, "README", 60, 3, "PT README")
dump(PT, "SAP_Raw_Registrations", 30, 8, "PT SAP RAW")
UIO = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_SourceData\UIO.xlsx"
dump(UIO, "CV customers with scrap logic", 60, 20, "UIO CV customers")
