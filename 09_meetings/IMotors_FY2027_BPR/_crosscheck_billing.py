from pathlib import Path
import openpyxl
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from lxml import etree

# KPI sales to dealer
kpi = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_nuno_kpi_portugal_20261001\09 - Set_KPI Check Sheet Monthly 26_Portugal.xlsx")
wb = openpyxl.load_workbook(kpi, data_only=True, read_only=True)
ws = wb["Checklist"]
std = fill = mos = bo = None
for row in ws.iter_rows(values_only=True):
    if not row or not row[1]: continue
    lab = str(row[1])
    if "Sales Distributor to all Dealers" in lab:
        std = [float(x) for x in row[2:11]]
    if "First Fill Rate" in lab:
        fill = [float(x) for x in row[2:11]]
    if "Months of parts in stock" in lab or "Days or Months" in lab:
        mos = [float(x) for x in row[2:11]]
    if "B/O Lines" in lab:
        bo = [int(x) for x in row[2:11]]
wb.close()
print("STD Jan-Sep", std)
print("STD Apr-Sep", std[3:9], sum(std[3:9]))
print("FILL", fill)
print("MOS", mos)
print("BO", bo)

# Invoice export Sep for sold-to 519? and find prior month billing from parquet/derived if available
# From charcoal builder: budget Apr-Sep [138,150,151,145,162,178]
# Need actual billing Apr-Aug from deck / prior calcs
calcs = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imotors_bpr_calcs_2026-09-24")
if calcs.exists():
    for p in calcs.rglob("*"):
        if p.is_file() and p.suffix in {".json",".csv",".md",".txt"}:
            print("CALC", p.name)

# Read slide 4 series via XML without namespaces kw
prs = Presentation(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx")

def chart_series(slide):
    out=[]
    for sh in slide.shapes:
        if not sh.has_chart: continue
        xml = etree.tostring(sh.chart._chartSpace)
        root = etree.fromstring(xml)
        ns = {"c":"http://schemas.openxmlformats.org/drawingml/2006/chart"}
        cats = [n.text for n in root.xpath(".//c:cat//c:pt/c:v", namespaces=ns)]
        sers=[]
        for ser in root.xpath(".//c:ser", namespaces=ns):
            nm = ser.xpath("./c:tx//c:v/text()", namespaces=ns)
            nm = nm[0] if nm else "?"
            vals = [float(n) for n in ser.xpath("./c:val//c:pt/c:v/text()", namespaces=ns)]
            sers.append((nm, vals))
        out.append((sh.name, cats, sers))
    return out

for i in [3,4,7,15,16]:
    print(f"\nSLIDE {i+1}")
    for name, cats, sers in chart_series(prs.slides[i]):
        print(name, "cats", cats[:20], "len", len(cats))
        for nm, vals in sers:
            print(" ", nm, vals)
