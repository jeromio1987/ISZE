# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import shutil
from lxml import etree
from pptx import Presentation
import openpyxl

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PPTX = ROOT / "09_meetings/IMotors_FY2027_BPR/I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx"
BAK = ROOT / "09_meetings/IMotors_FY2027_BPR/_bak_pre_sep_sales_fix.pptx"

SEP_BILL_K = 134.5
STD_2026 = [297.1, 489.8, 379.8, 393.5, 303.8, 416.8]
PLAN = [138.2, 149.5, 151.3, 145.3, 162.5, 177.7]
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"

def q(tag):
    return f"{{{C_NS}}}{tag}"

def as_etree(chart_space):
    return etree.fromstring(etree.tostring(chart_space))

def write_back(chart_space, root):
    # replace chart space children
    parent = chart_space
    # Clear and copy - better: replace element in place
    new_el = etree.fromstring(etree.tostring(root))
    parent.clear()
    for k, v in new_el.attrib.items():
        parent.set(k, v)
    parent.tag = new_el.tag
    for child in new_el:
        parent.append(child)
    # actually BaseOxmlElement may need different approach
    # Use: chart_space.getparent().replace
    pass

def read_series_xml(xml_bytes):
    root = etree.fromstring(xml_bytes)
    cats = [n.text for n in root.findall(".//" + q("cat") + "//" + q("pt") + "/" + q("v"))]
    # dedupe sequential doubles poorly - keep first ser length later
    sers = []
    for ser in root.findall(".//" + q("ser")):
        nm_el = ser.find(".//" + q("tx") + "//" + q("v"))
        nm = nm_el.text if nm_el is not None else "?"
        vals = [float(n.text) for n in ser.findall("./" + q("val") + "//" + q("pt") + "/" + q("v"))]
        sers.append((nm, vals))
    return root, cats, sers

def set_cats(root, cats):
    for cat in root.findall(".//" + q("cat")):
        for child in list(cat):
            cat.remove(child)
        strLit = etree.SubElement(cat, q("strLit"))
        ptCount = etree.SubElement(strLit, q("ptCount"))
        ptCount.set("val", str(len(cats)))
        for i, c in enumerate(cats):
            pt = etree.SubElement(strLit, q("pt"))
            pt.set("idx", str(i))
            v = etree.SubElement(pt, q("v"))
            v.text = str(c)

def set_vals(root, ser_index, values):
    sers = root.findall(".//" + q("ser"))
    ser = sers[ser_index]
    val = ser.find("./" + q("val"))
    if val is None:
        return
    for child in list(val):
        val.remove(child)
    numCache = etree.SubElement(val, q("numCache"))
    fmt = etree.SubElement(numCache, q("formatCode"))
    fmt.text = "General"
    ptCount = etree.SubElement(numCache, q("ptCount"))
    ptCount.set("val", str(len(values)))
    for i, v in enumerate(values):
        pt = etree.SubElement(numCache, q("pt"))
        pt.set("idx", str(i))
        ve = etree.SubElement(pt, q("v"))
        ve.text = str(v)

def replace_chart_xml(shape, root):
    """Replace the chart part blob."""
    chart_part = shape.chart.part
    chart_part._element = etree.fromstring(etree.tostring(root))
    # python-pptx Chart uses chart_part.chart_workspace - need assign properly
    # Official way: chart.replace_data
    pass

def replace_text(slide, old, new):
    n = 0
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for run in para.runs:
                if old in run.text:
                    run.text = run.text.replace(old, new)
                    n += 1
    return n

# Use chart.replace_data which is the supported API
from pptx.chart.data import CategoryChartData

if not BAK.exists():
    shutil.copy2(PPTX, BAK)
else:
    # restore from bak if previous failed mid-way - use current
    pass

prs = Presentation(str(PPTX))

# Discover series via tostring
def inspect(slide):
    out = []
    for sh in slide.shapes:
        if not sh.has_chart:
            continue
        root, cats, sers = read_series_xml(etree.tostring(sh.chart._chartSpace))
        # unique cats: take length of first series
        n = len(sers[0][1]) if sers else 0
        uniq_cats = cats[:n] if n and len(cats) >= n else cats
        out.append((sh, uniq_cats, sers))
    return out

print("=== S4 ===")
for sh, cats, sers in inspect(prs.slides[3]):
    print(cats, sers)
    # identify sales vs budget
    cd = CategoryChartData()
    cd.categories = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    sales = None
    budget = None
    for nm, vals in sers:
        if "budget" in nm.lower() or "Current" in nm or "plan" in nm.lower() or "BP" in nm:
            budget = PLAN
        else:
            sales = list(vals)
            if len(sales) == 5:
                sales.append(SEP_BILL_K)
            else:
                sales = sales[:5] + [SEP_BILL_K]
    if sales is None:
        sales = [0]*5 + [SEP_BILL_K]
    if budget is None:
        budget = PLAN
    # preserve series order from chart
    for nm, vals in sers:
        if "budget" in nm.lower() or "Current" in nm or "plan" in nm.lower() or "BP" in nm:
            cd.add_series(nm, budget)
        else:
            cd.add_series(nm, sales)
    sh.chart.replace_data(cd)
    print("S4 replaced", sales, budget)

print("=== S5 ===")
# Get sales from what we set
apr_sep = None
for sh, cats, sers in inspect(prs.slides[3]):
    for nm, vals in sers:
        if "budget" not in nm.lower() and "Current" not in nm:
            apr_sep = vals
print("apr_sep", apr_sep)
ytd = sum(apr_sep)
pace = ytd * 12 / 6 / 1858 * 100

for sh, cats, sers in inspect(prs.slides[4]):
    print("S5", cats, [(n,v) for n,v in sers])
    cd = CategoryChartData()
    # Keep categories as in chart if 12+ months
    n = max(len(v) for _, v in sers)
    # Build categories
    if n >= 12:
        # FY months Apr-Mar style
        base_cats = cats if len(cats) >= n else (["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"][:n])
        cd.categories = base_cats[:n]
        for nm, vals in sers:
            if "2027" in nm or "FY27" in nm or (len([x for x in vals if x]) <= 8 and max(vals) < 400):
                # pad FY27 to n with None/0 for future months
                newv = list(apr_sep) + [None] * (n - 6)
                # replace_data may not like None - use 0 or omit - CategoryChartData wants numbers
                # Better shorten chart to show Apr-Sep only for clarity? Keep FY26 full and FY27 as 6 points with nulls as empty
                # python-pptx: use 0 for missing? That plots zeros. 
                # Replace with only 6 categories for both if FY26 also truncated - BAD
                # Instead: FY27 values for first 6 months, rest leave as existing if longer
                merged = list(vals)
                for i, v in enumerate(apr_sep):
                    if i < len(merged):
                        merged[i] = v
                    else:
                        merged.append(v)
                if len(merged) < n:
                    merged += [0] * (n - len(merged))
                # zero future months after Sep for FY27
                for i in range(6, n):
                    merged[i] = 0
                cd.add_series(nm, merged[:n])
            else:
                cd.add_series(nm, (vals + [0]*n)[:n])
        sh.chart.replace_data(cd)
        print("S5 replaced FY27 with Sep")
    else:
        cd.categories = ["Apr","May","Jun","Jul","Aug","Sep"]
        for nm, vals in sers:
            if "2026" in nm and "2027" not in nm:
                cd.add_series(nm, (vals + [0]*6)[:6])
            else:
                cd.add_series(nm, apr_sep)
        sh.chart.replace_data(cd)

s5 = prs.slides[4]
replace_text(s5, "April-August billing is flat on last year; a straight-line full year gives 90.5% of target",
             f"April–September billing totals €{ytd:.0f}K; straight-line full year is about {pace:.1f}% of the €1.858M target")
replace_text(s5, "pace chart still April–August", "through September 2026 closed")
replace_text(s5, "April-August 2026", "April–September 2026")
replace_text(s5, "€701K", f"€{ytd:.0f}K")
replace_text(s5, "90.5%", f"{pace:.1f}%")

print("=== S8 sales to dealer ===")
# 2025 Apr-Sep from Nuno file or approximate from slide 9
# Compute from long csv if exists
std_long = list(ROOT.glob("01_data/**/dealer_sellout_long_PORTUGAL*.csv"))
print("std_long", std_long[:5])
std_2025 = None
# Try monthly rollup from KPI prior year - not available
# From BAK slide 8 if 5 months, get Sep 2025 from portugal sales file
xlsx = ROOT / "01_data/90_INBOX/nuno_machado_sales_to_dealer_20260903/PORTUGAL_Sales_to_Dealer_2025-26_from_NunoMachado_20260903_1258.xlsx"
if xlsx.exists():
    wb = openpyxl.load_workbook(xlsx, data_only=True, read_only=True)
    print("sheets", wb.sheetnames)
    ws = wb[wb.sheetnames[0]]
    hdr = None
    # sum euros by year-month for 2025 Apr-Sep
    from collections import defaultdict
    # peek columns
    rows = ws.iter_rows(values_only=True)
    hdr = next(rows)
    print("hdr", hdr)
    # find date and eur cols
    h = [str(x).lower() if x else "" for x in hdr]
    print("hlower", h)

# Fallback: use values from slide 9 narrative / known prior deck
# APR-SEP 2025 total often ~ €1.7M something - read slide 8 text boxes for totals
for sh in prs.slides[7].shapes:
    if sh.has_text_frame:
        t = sh.text_frame.text
        if "2025" in t or "EUR" in t or "€" in t:
            print("S8T", t.replace("\n"," | ")[:150])

for sh, cats, sers in inspect(prs.slides[7]):
    print("S8 chart", cats, sers)
    cd = CategoryChartData()
    cd.categories = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    for nm, vals in sers:
        if len(vals) >= 5 and (vals[0] > 200 or "2026" in nm):
            # 2026
            cd.add_series(nm if nm != "?" else "2026", STD_2026)
        else:
            # 2025 - extend with Sep from file later
            if len(vals) == 5:
                # temporary: will fix after computing
                std_2025_guess = list(vals)
            else:
                std_2025_guess = list(vals)[:6]
            cd.add_series(nm if nm != "?" else "2025", std_2025_guess + ([0] if len(std_2025_guess)==5 else []))
    # Don't replace yet until 2025 Sep known

# Compute 2025 from sellout long
cand = list((ROOT/"01_data").glob("**/dealer_sellout*PORTUGAL*"))
cand += list((ROOT/"01_data").glob("**/*Portugal*sell*"))
print("cands", cand[:20])

prs.save(str(PPTX))
print("partial save YTD", ytd, pace)
