"""Build the CV PMS coverage workbook: every customer with a truck fleet, by country.

Expected PMS demand is a live Excel formula on UIO:
    expected pieces = trucks in service (UIO) x service visits a year x replacement rate
Billed pieces / euros are pasted values from the verified PMS files. Coverage and gap are formulas.

Inputs (all aggregated, no line-level billing written to the workbook except a
part-number summary of genuine PMS parts with no BVP):
    01_data/00_derived/uio_by_market_type_year.csv      UIO by market, class, model type, year
    01_data/00_derived/pms_capture_by_family.csv        visits, rates, billed per family
    01_data/00_derived/pms_capture_by_db_year.csv       genuine / BVP billed per customer
    01_data/00_derived/sales_fact.parquet               FY2026 genuine PMS parts with no BVP
    01_data/00_derived/genuine_bvp_crossref.csv, bvp_pn_dimension.csv
    03_analytics/Isuzu/prism/data/fig_key_taxonomy.yaml, distributor_master_mapping.csv,
    sap_sold_to_mapping.csv

Run from anywhere:  python build_cv_pms_coverage_workbook.py
Then recalculate (LibreOffice / Excel) before reading values.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[3]
DER = ROOT / "01_data" / "00_derived"
PDATA = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
OUT = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1 else "ISZE_CV_PMS_Coverage_by_Customer_2026-10-30.xlsx")

YEARS = [2024, 2025]
MIN_CV_UIO = 10  # Denmark has 1 truck in service: left out
FAMILIES = {"n_series_truck": "N-series truck", "heavy_truck": "Heavy truck (F-series)"}
CATS = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "blower_filter": "Cabin (blower) filter", "urea_filter": "AdBlue filter",
    "brake_pad": "Brake pad", "brake_shoe": "Brake shoe", "brake_rotor": "Brake disc (rotor)",
    "clutch_kit": "Clutch kit", "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate", "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing", "clutch_booster": "Clutch booster",
}
NAMES = {
    "ITUK": "Isuzu Truck UK", "UTI": "UTI (Universal Trucks Israel)", "PORTUGAL": "I Motors Portugal",
    "IRELAND": "Isuzu Ireland", "GERMANY": "Isuzu Sales Deutschland", "BELGIUM": "Isuzu Benelux",
    "MALTA": "Gasan Zammit Motors", "CYPRUS": "Loutsios & Sons", "GREECE": "Petros Petropoulos",
}

# ---------- styles ----------
F = "Arial"
H_FILL = PatternFill("solid", fgColor="1F3864")
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
IN_FILL = PatternFill("solid", fgColor="FFF2CC")
BLUE = Font(name=F, size=10, color="0000FF")
GREEN = Font(name=F, size=10, color="008000")
BLACK = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
HFONT = Font(name=F, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=F, size=14, bold=True, color="1F3864")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
EUR = '€#,##0;(€#,##0);"-"'
PCS = '#,##0;(#,##0);"-"'
PCS1 = '#,##0.0;(#,##0.0);"-"'
PCT = '0.0%;(0.0%);"-"'
RATE = "0.00"


def header(ws, row, cols, widths=None):
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font, cell.fill, cell.border = HFONT, H_FILL, BOX
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[row].height = 45
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=row + 1, column=1)
    ws.auto_filter.ref = f"A{row}:{get_column_letter(len(cols))}{row}"


def put(ws, r, c, v, font=BLACK, fmt=None, fill=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font, cell.border = font, BOX
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    return cell


# ---------- data ----------
uio = pd.read_csv(DER / "uio_by_market_type_year.csv")
uio = uio[uio.year.isin(YEARS)]
piv = uio.pivot_table(index=["distributor_code", "year"], columns="model_type", values="uio_units", aggfunc="sum", fill_value=0)
for c in ["LD", "MD", "F-Series", "LCV"]:
    if c not in piv:
        piv[c] = 0
piv["cv"] = piv.LD + piv.MD + piv["F-Series"]
cv_codes = sorted(piv[piv.cv >= MIN_CV_UIO].reset_index().distributor_code.unique())

fam = pd.read_csv(DER / "pms_capture_by_family.csv")
fam = fam[fam.year.isin(YEARS) & fam.distributor_code.isin(cv_codes)]
dbm = pd.read_csv(PDATA / "distributor_master_mapping.csv").drop_duplicates("distributor_code").set_index("distributor_code")
country = {c: (dbm.country.get(c, c.title())) for c in cv_codes}
cust_order = sorted(cv_codes, key=lambda c: (country[c], c))

visits = fam[fam.family.isin(FAMILIES)].groupby(["distributor_code", "year", "family"]).visits_per_year.first()
rates = fam[fam.family.isin(FAMILIES)].groupby(["distributor_code", "pms_category", "family"]).category_factor.first()

# tie-out guard: family split must add up to the customer total
tot = pd.read_csv(DER / "pms_capture_by_db_year.csv")
a = pd.read_csv(DER / "pms_capture_by_family.csv").groupby(["distributor_code", "year", "pms_category"]).billed_eur.sum()
b = tot[tot.line_type == "total"].set_index(["distributor_code", "year", "pms_category"]).actual_rev_eur
diff = (a - b).abs().dropna()
assert diff.max() < 1, f"family billed does not tie to customer total: {diff.max()}"

# ---------- workbook ----------
wb = Workbook()
rd = wb.active
rd.title = "Read me"

# ===== UIO sheet =====
wu = wb.create_sheet("UIO")
put(wu, 1, 1, "Trucks in service (UIO) by customer and year — inputs", TITLE).border = Border()
put(wu, 2, 1, "Blue = input. Source: Isuzu UIO Overview 2026 (by market, model type). Visits a year: service visits per truck a year used in the PMS coverage model.", BLACK).border = Border()
cols = ["Key", "Customer code", "Customer", "Country", "Year", "N-series light duty (LD)", "N-series medium duty (MD)",
        "N-series trucks total", "Heavy truck F-series", "Trucks total (CV)", "Pickup / LCV (info)",
        "Truck share of fleet", "Service visits a year — N-series", "Service visits a year — heavy truck"]
header(wu, 4, cols, [16, 12, 30, 15, 7, 13, 13, 13, 13, 13, 13, 11, 14, 14])
r = 5
uio_rows = {}
for c in cust_order:
    for y in YEARS:
        p = piv.loc[(c, y)] if (c, y) in piv.index else None
        put(wu, r, 1, f'=B{r}&"|"&E{r}')
        put(wu, r, 2, c)
        put(wu, r, 3, NAMES.get(c, dbm.legal_entity.get(c, c)))
        put(wu, r, 4, country[c])
        put(wu, r, 5, y)
        for col, key in [(6, "LD"), (7, "MD"), (9, "F-Series"), (11, "LCV")]:
            put(wu, r, col, float(p[key]) if p is not None else 0, BLUE, PCS1, IN_FILL)
        put(wu, r, 8, f"=F{r}+G{r}", fmt=PCS1)
        put(wu, r, 10, f"=H{r}+I{r}", fmt=PCS1)
        put(wu, r, 12, f"=IFERROR(J{r}/(J{r}+K{r}),0)", fmt=PCT)
        put(wu, r, 13, float(visits.get((c, y, "n_series_truck"), 0.5)), BLUE, RATE, IN_FILL)
        put(wu, r, 14, float(visits.get((c, y, "heavy_truck"), 0.6667)), BLUE, RATE, IN_FILL)
        uio_rows[(c, y)] = r
        r += 1
UIO_LAST = r - 1
wu.cell(row=5, column=13).comment = Comment(
    "Service visits per truck per year. N-series: per-market figure from mileage and service interval; "
    "Isuzu Truck UK uses the IML service schedule. Heavy truck: 0.6667 everywhere (one visit every 18 months).", "ISZE")
put(wu, r + 1, 1, "Denmark (1 truck in service) and LCV-only customers are not in this file.", Font(name=F, size=9, italic=True)).border = Border()

# ===== Rates sheet =====
wr = wb.create_sheet("Replacement rates")
put(wr, 1, 1, "Replacement rate per service visit — inputs", TITLE).border = Border()
put(wr, 2, 1, "Share of service visits at which the part is replaced (1.0 = every visit). Blue = input; change here and every sheet follows.", BLACK).border = Border()
header(wr, 4, ["Key", "Part", "Part code", "Truck family", "Rate — all customers", "Rate — Isuzu Truck UK (if different)", "Note"],
       [30, 24, 22, 22, 13, 15, 70])
notes = {
    "air_filter": "Air element about every 2nd service — provisional, waiting for IML confirmation.",
    "urea_filter": "AdBlue filter: long interval, provisional.",
    "brake_rotor": "About every 2nd pad change — provisional, not confirmed by IML.",
    "brake_pad": "Isuzu Truck UK uses the IML service schedule rate (0.4).",
    "brake_shoe": "Isuzu Truck UK uses the IML service schedule rate (0.4).",
}
r = 5
for cat, lab in CATS.items():
    for fk, fl in FAMILIES.items():
        non_ituk = rates.drop("ITUK", level=0, errors="ignore")
        base = non_ituk.xs((cat, fk), level=(1, 2)).mode()
        base = float(base.iloc[0]) if len(base) else None
        ituk = rates.get(("ITUK", cat, fk))
        put(wr, r, 1, f'=C{r}&"|"&D{r}')
        put(wr, r, 2, lab)
        put(wr, r, 3, cat)
        put(wr, r, 4, fk)
        put(wr, r, 5, base, BLUE, RATE, IN_FILL)
        put(wr, r, 6, float(ituk) if ituk is not None and base is not None and abs(ituk - base) > 1e-9 else None, BLUE, RATE, IN_FILL)
        put(wr, r, 7, notes.get(cat, ""))
        r += 1
RATE_LAST = r - 1

# ===== Detail sheet (customer x year x part x family) =====
wd = wb.create_sheet("Detail by truck family")
put(wd, 1, 1, "PMS expected demand from UIO vs billed — by customer, year, part and truck family", TITLE).border = Border()
put(wd, 2, 1, "Expected pieces = UIO × visits a year × replacement rate. Billed = parts that fit only this truck family (genuine + BVP). "
    "Parts fitting more than one family, or with no vehicle reference, are on the 'Coverage by customer' sheet.", BLACK).border = Border()
dcols = ["Customer code", "Customer", "Country", "Year", "Part", "Part code", "Truck family", "Family code",
         "UIO (trucks)", "Visits a year", "Replacement rate", "Expected pieces", "Average price € (billed)",
         "Expected €", "Billed pieces (this family only)", "Billed €", "Coverage % (pieces)", "Gap € at billed price"]
header(wd, 4, dcols, [11, 26, 13, 7, 20, 18, 20, 14, 10, 9, 10, 11, 11, 12, 12, 12, 10, 12])
r = 5
for c in cust_order:
    for y in YEARS:
        ur = uio_rows[(c, y)]
        for cat, lab in CATS.items():
            for fk, fl in FAMILIES.items():
                row = fam[(fam.distributor_code == c) & (fam.year == y) & (fam.pms_category == cat) & (fam.family == fk)]
                bu = float(row.billed_units.iloc[0]) if len(row) else 0.0
                be = float(row.billed_eur.iloc[0]) if len(row) else 0.0
                asp = float(row.avg_selling_price_eur.iloc[0]) if len(row) and pd.notna(row.avg_selling_price_eur.iloc[0]) else None
                put(wd, r, 1, c)
                put(wd, r, 2, f"=UIO!C{ur}", GREEN)
                put(wd, r, 3, f"=UIO!D{ur}", GREEN)
                put(wd, r, 4, y)
                put(wd, r, 5, lab)
                put(wd, r, 6, cat)
                put(wd, r, 7, fl)
                put(wd, r, 8, fk)
                ucol = "H" if fk == "n_series_truck" else "I"
                vcol = "M" if fk == "n_series_truck" else "N"
                put(wd, r, 9, f"=UIO!{ucol}{ur}", GREEN, PCS1)
                put(wd, r, 10, f"=UIO!{vcol}{ur}", GREEN, RATE)
                key = f'F{r}&"|"&H{r}'
                put(wd, r, 11, f"=IF(AND(A{r}=\"ITUK\",INDEX('Replacement rates'!$F$5:$F${RATE_LAST},MATCH({key},'Replacement rates'!$A$5:$A${RATE_LAST},0))<>\"\"),"
                               f"INDEX('Replacement rates'!$F$5:$F${RATE_LAST},MATCH({key},'Replacement rates'!$A$5:$A${RATE_LAST},0)),"
                               f"INDEX('Replacement rates'!$E$5:$E${RATE_LAST},MATCH({key},'Replacement rates'!$A$5:$A${RATE_LAST},0)))", GREEN, RATE)
                put(wd, r, 12, f"=I{r}*J{r}*K{r}", fmt=PCS1)
                put(wd, r, 13, asp, BLUE, '€#,##0.00;(€#,##0.00);"-"', IN_FILL)
                put(wd, r, 14, f"=L{r}*N(M{r})", fmt=EUR)
                put(wd, r, 15, bu, BLUE, PCS, IN_FILL)
                put(wd, r, 16, be, BLUE, EUR, IN_FILL)
                put(wd, r, 17, f'=IF(L{r}>0,O{r}/L{r},"")', fmt=PCT)
                put(wd, r, 18, f"=MAX(0,L{r}-O{r})*N(M{r})", fmt=EUR)
                r += 1
DET_LAST = r - 1
wd.cell(row=4, column=13).comment = Comment("Average billed price per piece for this customer and part (this family and year where billed; otherwise this customer's average over all families or years).", "ISZE")

# ===== Coverage by customer (customer x year x part) =====
wc = wb.create_sheet("Coverage by customer")
put(wc, 1, 1, "PMS coverage by customer, year and part — trucks only", TITLE).border = Border()
put(wc, 2, 1, "Low = only parts that fit trucks alone. High = also counts parts shared with other vehicles and parts with no vehicle reference. "
    "For truck-only customers (Isuzu Truck UK, UTI) the high figure is the right one; for mixed customers the truth sits between low and high.", BLACK).border = Border()
ccols = ["Customer code", "Customer", "Country", "Year", "Part", "Part code", "Truck share of fleet",
         "Expected pieces (trucks)", "Expected € (trucks)", "Billed pieces — truck-only parts", "Billed pieces — shared parts",
         "Billed pieces — no vehicle reference", "Billed € — truck-only parts", "Billed € — shared + no reference",
         "Coverage % LOW", "Coverage % HIGH", "Average price €", "Gap € LOW coverage", "Gap € HIGH coverage"]
header(wc, 4, ccols, [11, 26, 13, 7, 20, 18, 10, 12, 12, 12, 12, 12, 12, 12, 10, 10, 10, 12, 12])
r = 5
cov_rows = {}
D = "'Detail by truck family'!"
for c in cust_order:
    for y in YEARS:
        ur = uio_rows[(c, y)]
        for cat, lab in CATS.items():
            sh = fam[(fam.distributor_code == c) & (fam.year == y) & (fam.pms_category == cat) & (fam.family == "shared_across_families")]
            un = fam[(fam.distributor_code == c) & (fam.year == y) & (fam.pms_category == cat) & (fam.family == "unattributed")]
            su = float(sh.billed_units.sum()); se = float(sh.billed_eur.sum())
            uu = float(un.billed_units.sum()); ue = float(un.billed_eur.sum())
            crit = f'{D}$A$5:$A${DET_LAST},A{r},{D}$D$5:$D${DET_LAST},D{r},{D}$F$5:$F${DET_LAST},F{r}'
            put(wc, r, 1, c)
            put(wc, r, 2, f"=UIO!C{ur}", GREEN)
            put(wc, r, 3, f"=UIO!D{ur}", GREEN)
            put(wc, r, 4, y)
            put(wc, r, 5, lab)
            put(wc, r, 6, cat)
            put(wc, r, 7, f"=UIO!L{ur}", GREEN, PCT)
            put(wc, r, 8, f"=SUMIFS({D}$L$5:$L${DET_LAST},{crit})", GREEN, PCS)
            put(wc, r, 9, f"=SUMIFS({D}$N$5:$N${DET_LAST},{crit})", GREEN, EUR)
            put(wc, r, 10, f"=SUMIFS({D}$O$5:$O${DET_LAST},{crit})", GREEN, PCS)
            put(wc, r, 11, su, BLUE, PCS, IN_FILL)
            put(wc, r, 12, uu, BLUE, PCS, IN_FILL)
            put(wc, r, 13, f"=SUMIFS({D}$P$5:$P${DET_LAST},{crit})", GREEN, EUR)
            put(wc, r, 14, se + ue, BLUE, EUR, IN_FILL)
            put(wc, r, 15, f'=IF(H{r}>0,J{r}/H{r},"")', fmt=PCT)
            put(wc, r, 16, f'=IF(H{r}>0,(J{r}+K{r}+L{r})/H{r},"")', fmt=PCT)
            put(wc, r, 17, f'=IF(H{r}>0,I{r}/H{r},"")', fmt='€#,##0.00;(€#,##0.00);"-"')
            put(wc, r, 18, f"=MAX(0,H{r}-J{r})*N(Q{r})", fmt=EUR)
            put(wc, r, 19, f"=MAX(0,H{r}-J{r}-K{r}-L{r})*N(Q{r})", fmt=EUR)
            cov_rows[(c, y, cat)] = r
            r += 1
COV_LAST = r - 1
wc.cell(row=4, column=11).comment = Comment("Parts that fit more than one vehicle family (for mixed customers this can include pickup volume). Billed at customer level, never split by family.", "ISZE")
wc.cell(row=4, column=12).comment = Comment("Billed PMS parts with no vehicle reference in the catalogue. Could be truck or pickup.", "ISZE")
wc.conditional_formatting.add(f"O5:P{COV_LAST}", ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                                                                  mid_type="num", mid_value=0.5, mid_color="FFEB84",
                                                                  end_type="num", end_value=1, end_color="63BE7B"))

# ===== Overview (pick year) =====
wo = wb.create_sheet("Overview by country", 1)
put(wo, 1, 1, "PMS coverage — trucks, by country and customer", TITLE).border = Border()
put(wo, 3, 1, "Year", BOLD)
put(wo, 3, 2, 2025, BLUE, None, IN_FILL)
dv = DataValidation(type="list", formula1='"2024,2025"', allow_blank=False)
wo.add_data_validation(dv)
dv.add("B3")
put(wo, 3, 3, "Coverage view", BOLD)
put(wo, 3, 4, "AUTO", BLUE, None, IN_FILL)
dv2 = DataValidation(type="list", formula1='"AUTO,LOW,HIGH"', allow_blank=False)
wo.add_data_validation(dv2)
dv2.add("D3")
put(wo, 4, 1, "Calendar year (the coverage model runs on calendar years). LOW = truck-only parts. HIGH = also shared parts and parts with no vehicle reference. AUTO = HIGH for customers with 90%+ trucks in the fleet, LOW for the others.",
    Font(name=F, size=9, italic=True)).border = Border()
for cc in (1, 3):
    wo.cell(row=3, column=cc).border = Border()
cats = list(CATS.items())
top = ["Country", "Customer", "Trucks in service (UIO)", "Truck share of fleet"] + [lab for _, lab in cats] + ["All PMS — expected €", "All PMS — gap €"]
for i, t in enumerate(top, 1):
    cell = wo.cell(row=6, column=i, value=t)
    cell.font, cell.fill, cell.border = HFONT, H_FILL, BOX
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
wo.row_dimensions[6].height = 45
wo.column_dimensions["A"].width = 15
wo.column_dimensions["B"].width = 28
wo.column_dimensions["C"].width = 11
wo.column_dimensions["D"].width = 10
for i in range(5, 5 + len(cats)):
    wo.column_dimensions[get_column_letter(i)].width = 10
wo.column_dimensions[get_column_letter(5 + len(cats))].width = 13
wo.column_dimensions[get_column_letter(6 + len(cats))].width = 13
C = "'Coverage by customer'!"
r = 7
for c in cust_order:
    ur = uio_rows[(c, YEARS[-1])]
    put(wo, r, 1, country[c])
    put(wo, r, 2, NAMES.get(c, c))
    put(wo, r, 3, f'=SUMIFS(UIO!$J$5:$J${UIO_LAST},UIO!$B$5:$B${UIO_LAST},"{c}",UIO!$E$5:$E${UIO_LAST},$B$3)', GREEN, PCS)
    put(wo, r, 4, f'=SUMIFS(UIO!$J$5:$J${UIO_LAST},UIO!$B$5:$B${UIO_LAST},"{c}",UIO!$E$5:$E${UIO_LAST},$B$3)/'
                  f'(SUMIFS(UIO!$J$5:$J${UIO_LAST},UIO!$B$5:$B${UIO_LAST},"{c}",UIO!$E$5:$E${UIO_LAST},$B$3)+SUMIFS(UIO!$K$5:$K${UIO_LAST},UIO!$B$5:$B${UIO_LAST},"{c}",UIO!$E$5:$E${UIO_LAST},$B$3))', GREEN, PCT)
    for j, (cat, lab) in enumerate(cats):
        crit = f'{C}$A$5:$A${COV_LAST},"{c}",{C}$D$5:$D${COV_LAST},$B$3,{C}$F$5:$F${COV_LAST},"{cat}"'
        exp = f"SUMIFS({C}$H$5:$H${COV_LAST},{crit})"
        lo = f"SUMIFS({C}$J$5:$J${COV_LAST},{crit})"
        hi = f"(SUMIFS({C}$J$5:$J${COV_LAST},{crit})+SUMIFS({C}$K$5:$K${COV_LAST},{crit})+SUMIFS({C}$L$5:$L${COV_LAST},{crit}))"
        put(wo, r, 5 + j, f'=IF({exp}>0,IF(OR($D$3="HIGH",AND($D$3="AUTO",$D{r}>=0.9)),{hi},{lo})/{exp},"")', GREEN, PCT)
    critc = f'{C}$A$5:$A${COV_LAST},"{c}",{C}$D$5:$D${COV_LAST},$B$3'
    put(wo, r, 5 + len(cats), f"=SUMIFS({C}$I$5:$I${COV_LAST},{critc})", GREEN, EUR)
    put(wo, r, 6 + len(cats), f'=IF(OR($D$3="HIGH",AND($D$3="AUTO",$D{r}>=0.9)),SUMIFS({C}$S$5:$S${COV_LAST},{critc}),SUMIFS({C}$R$5:$R${COV_LAST},{critc}))', GREEN, EUR)
    r += 1
OV_LAST = r - 1
put(wo, r, 1, "All truck customers", BOLD)
put(wo, r, 2, "")
put(wo, r, 3, f"=SUM(C7:C{OV_LAST})", BOLD, PCS)
put(wo, r, 4, "")
for j, (cat, lab) in enumerate(cats):
    crit = f'{C}$D$5:$D${COV_LAST},$B$3,{C}$F$5:$F${COV_LAST},"{cat}"'
    exp = f"SUMIFS({C}$H$5:$H${COV_LAST},{crit})"
    terms = []
    for i, c in enumerate(cust_order):
        ci = f'{C}$A$5:$A${COV_LAST},"{c}",{crit}'
        lo = f"SUMIFS({C}$J$5:$J${COV_LAST},{ci})"
        hi = f"SUMIFS({C}$J$5:$J${COV_LAST},{ci})+SUMIFS({C}$K$5:$K${COV_LAST},{ci})+SUMIFS({C}$L$5:$L${COV_LAST},{ci})"
        terms.append(f'IF(OR($D$3="HIGH",AND($D$3="AUTO",$D{7 + i}>=0.9)),{hi},{lo})')
    put(wo, r, 5 + j, f'=IF({exp}>0,({"+".join(terms)})/{exp},"")', BOLD, PCT)
ecol, gcol = get_column_letter(5 + len(cats)), get_column_letter(6 + len(cats))
put(wo, r, 5 + len(cats), f"=SUM({ecol}7:{ecol}{OV_LAST})", BOLD, EUR)
put(wo, r, 6 + len(cats), f"=SUM({gcol}7:{gcol}{OV_LAST})", BOLD, EUR)
for cc in range(1, 7 + len(cats)):
    wo.cell(row=r, column=cc).fill = SUB_FILL
wo.conditional_formatting.add(f"E7:{get_column_letter(4 + len(cats))}{r}",
                              ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                                             mid_type="num", mid_value=0.5, mid_color="FFEB84",
                                             end_type="num", end_value=1, end_color="63BE7B"))
wo.freeze_panes = "C7"
put(wo, r + 2, 1, "Coverage above 100% is possible: billed parts also go to vehicles outside the UIO count (for mixed customers, pickups using shared parts).",
    Font(name=F, size=9, italic=True)).border = Border()

# ===== Genuine vs BVP (whole customer) =====
wg = wb.create_sheet("Genuine vs BVP")
put(wg, 1, 1, "PMS parts billed — genuine vs BVP, by customer, year and part (whole customer: trucks and pickups)", TITLE).border = Border()
put(wg, 2, 1, "Billed values from ISZE parts billing after credit notes and returns are removed. Calendar year.", BLACK).border = Border()
gcols = ["Customer code", "Customer", "Country", "Year", "Part", "Part code", "Genuine pieces", "BVP pieces",
         "Genuine €", "BVP €", "Total €", "BVP share of €", "BVP share of pieces"]
header(wg, 4, gcols, [11, 26, 13, 7, 20, 18, 11, 11, 12, 12, 12, 10, 10])
r = 5
for c in cust_order:
    for y in YEARS:
        ur = uio_rows[(c, y)]
        for cat, lab in CATS.items():
            g = tot[(tot.distributor_code == c) & (tot.year == y) & (tot.pms_category == cat)]
            gl = g[g.line_type == "genuine"]; bl = g[g.line_type == "bvp"]
            put(wg, r, 1, c); put(wg, r, 2, f"=UIO!C{ur}", GREEN); put(wg, r, 3, f"=UIO!D{ur}", GREEN)
            put(wg, r, 4, y); put(wg, r, 5, lab); put(wg, r, 6, cat)
            put(wg, r, 7, float(gl.actual_qty.sum()), BLUE, PCS, IN_FILL)
            put(wg, r, 8, float(bl.actual_qty.sum()), BLUE, PCS, IN_FILL)
            put(wg, r, 9, float(gl.actual_rev_eur.sum()), BLUE, EUR, IN_FILL)
            put(wg, r, 10, float(bl.actual_rev_eur.sum()), BLUE, EUR, IN_FILL)
            put(wg, r, 11, f"=I{r}+J{r}", fmt=EUR)
            put(wg, r, 12, f'=IF(K{r}>0,J{r}/K{r},"")', fmt=PCT)
            put(wg, r, 13, f'=IF(G{r}+H{r}>0,H{r}/(G{r}+H{r}),"")', fmt=PCT)
            r += 1

# ===== Genuine PMS parts with no BVP, FY2026 =====
wn = wb.create_sheet("Genuine no BVP FY2026")
put(wn, 1, 1, "Genuine PMS parts with no BVP alternative — billed FY2026 (1 Apr 2025 – 31 Mar 2026), truck customers", TITLE).border = Border()
put(wn, 2, 1, "No BVP = genuine part number not paired with a BVP part in the BVP catalogue cross-reference. Part numbers that look like BVP numbers (5876… / 1876…) are left out.", BLACK).border = Border()
tax = yaml.safe_load(open(PDATA / "fig_key_taxonomy.yaml"))["pms_fig_keys"]


def _norm(cat):
    for p in ("brake_pad", "brake_shoe", "brake_lining"):
        if cat.startswith(p):
            return p
    return cat


fk = {k: _norm(v["pms_category"]) for k, v in tax.items()}
s = pd.read_parquet(DER / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "description", "billed_qty", "net_sales_value", "saty", "fig_key"])
s = s[(s.billing_date >= "2025-04-01") & (s.billing_date < "2026-04-01") & ~s.saty.isin(["CR", "RE"]) & (s.net_sales_value > 0)]
s["part_number"] = s.part_number.astype(str)
dim = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str)
cx = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str)
bvp_pns = set(dim[dim.line_type == "bvp"].part_number) | set(cx.bvp_pn)
reg = dim[dim.pms_flag == "True"].set_index("part_number").pms_category
s["cat"] = s.part_number.map(reg).fillna(s.fig_key.map(fk))
s = s[s.cat.notna() & ~s.part_number.isin(bvp_pns) & ~s.part_number.isin(cx.genuine_pn) & ~s.part_number.str[:4].isin(["5876", "1876"])]
smap = pd.read_csv(PDATA / "sap_sold_to_mapping.csv", dtype=str).drop_duplicates("sap_sold_to_pt").set_index("sap_sold_to_pt").distributor_code
s["dist"] = s.sold_to_sap.astype(str).str.replace(r"\.0$", "", regex=True).map(smap)
s = s[s.dist.isin(cv_codes)]
pfm = pd.read_csv(DER / "pms_family_part_number_map.csv", dtype=str).drop_duplicates("pn").set_index("pn").family
famlab = {**FAMILIES, "light_vehicle": "Pickup (D-Max)", "shared_across_families": "Fits more than one family"}
g = s.groupby(["dist", "cat", "part_number"]).agg(desc=("description", "first"), qty=("billed_qty", "sum"), eur=("net_sales_value", "sum")).reset_index()
g["country"] = g.dist.map(country)
g = g.sort_values(["country", "dist", "eur"], ascending=[True, True, False])
header(wn, 4, ["Country", "Customer", "Part", "Part number", "Description", "Fits", "Billed pieces FY2026", "Billed € FY2026", "Average price €"],
       [13, 28, 20, 13, 32, 22, 12, 13, 11])
r = 5
for _, x in g.iterrows():
    put(wn, r, 1, x.country); put(wn, r, 2, NAMES.get(x.dist, x.dist)); put(wn, r, 3, CATS.get(x["cat"], x["cat"].replace("_", " ").capitalize()))
    put(wn, r, 4, x.part_number); put(wn, r, 5, x.desc); put(wn, r, 6, famlab.get(pfm.get(x.part_number), "No vehicle reference"))
    put(wn, r, 7, float(x.qty), BLUE, PCS); put(wn, r, 8, float(x.eur), BLUE, EUR)
    put(wn, r, 9, f'=IF(G{r}>0,H{r}/G{r},"")', fmt='€#,##0.00;(€#,##0.00);"-"')
    r += 1
put(wn, r, 7, "Total", BOLD); put(wn, r, 8, f"=SUBTOTAL(9,H5:H{r - 1})", BOLD, EUR)

# ===== Read me =====
rd.column_dimensions["A"].width = 30
rd.column_dimensions["B"].width = 110
lines = [
    ("PMS coverage — truck (CV) customers by country", None),
    ("", None),
    ("What this is", "Expected PMS parts demand from trucks in service (UIO), against what ISZE billed, per customer, part and year. "
                     "Same calculation as the ISZE PMS coverage model; every expected figure is a live formula on the UIO and rate sheets."),
    ("Customers", "Every ISZE customer with trucks in service (N-series or F-series): " + ", ".join(f"{NAMES.get(c, c)} ({country[c]})" for c in cust_order) +
                  ". Denmark (1 truck) and LCV-only customers are not included."),
    ("Formula", "Expected pieces = UIO (trucks) × service visits a year × replacement rate.   Coverage % = billed pieces ÷ expected pieces.   "
                "Gap € = (expected − billed pieces) × average billed price, never below zero."),
    ("Period", "Coverage: calendar years 2024 and 2025 (the coverage model and UIO run on calendar years). "
               "Genuine parts with no BVP: FY2026 (1 Apr 2025 – 31 Mar 2026)."),
    ("Billed", "ISZE parts billing, genuine + BVP, credit notes and returns removed. Billed pieces and euros are pasted values (blue)."),
    ("LOW vs HIGH coverage", "Parts that fit more than one vehicle family, or have no vehicle reference, cannot be split between trucks and pickups. "
                             "LOW counts only truck-only parts; HIGH adds the shared and unreferenced parts. For truck-only customers (Isuzu Truck UK, UTI) use HIGH. The overview default AUTO does this: HIGH where trucks are 90%+ of the fleet, LOW elsewhere. "
                             "For mixed customers (e.g. Isuzu Benelux, Germany: mostly pickups) HIGH can overstate — the true figure is between the two."),
    ("Sheets", "Overview by country — pick the year and LOW/HIGH; coverage per part and total gap €.\n"
               "Coverage by customer — customer × year × part, both views.\n"
               "Detail by truck family — N-series and heavy truck split, where the UIO formula sits.\n"
               "UIO — trucks in service and service visits a year (inputs).\n"
               "Replacement rates — share of visits where the part is replaced (inputs).\n"
               "Genuine vs BVP — billed mix per customer (whole customer, trucks and pickups).\n"
               "Genuine no BVP FY2026 — genuine PMS parts billed with no BVP alternative."),
    ("Colours", "Blue text on yellow = input (change it and the file recalculates). Black = formula. Green = formula linking to another sheet."),
    ("Caveats", "1) Replacement rates for air filter, AdBlue filter, brake disc, brake pads and clutch parts are provisional and not confirmed by IML — use the gap € for ranking, not as a quotable figure.\n"
                "2) Isuzu Truck UK uses the IML service schedule rates (service visits and brake rates); its coverage here can differ from the IML headline, which uses its own part scope.\n"
                "3) Clutch disc and pressure plate are often replaced as a clutch kit, so their own coverage looks lower than reality.\n"
                "4) Brake disc (rotor) has no catalogue figure key; only listed part numbers are counted.\n"
                "5) Coverage above 100% is possible where billed parts go to vehicles outside the truck UIO.\n"
                "6) 2025 ties exactly to the ISZE PMS coverage model. For 2024 this file uses the 2024 UIO; the coverage model reuses the 2025 fleet for 2024, so 2024 expected demand here is a few % different."),
    ("Built", "2026-10-30 by 03_analytics/Isuzu/pms-pilot/build_cv_pms_coverage_workbook.py from the verified PMS files (data check green 2026-09-24)."),
]
for i, (k, v) in enumerate(lines, 1):
    a_ = rd.cell(row=i, column=1, value=k)
    a_.font = TITLE if i == 1 else BOLD
    a_.alignment = Alignment(vertical="top")
    if v:
        b_ = rd.cell(row=i, column=2, value=v)
        b_.font = BLACK
        b_.alignment = Alignment(wrap_text=True, vertical="top")
        rd.row_dimensions[i].height = max(15, 15 * (v.count("\n") + 1 + len(v) // 120))

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    if ws.column_dimensions["B"].width < 28:
        ws.column_dimensions["B"].width = 28
rd.freeze_panes = "A2"
for row in wo.iter_rows(min_row=7, max_row=OV_LAST + 1, min_col=3, max_col=6 + len(cats)):
    for cell in row:
        cell.alignment = Alignment(wrap_text=True, horizontal="right")
wb.active = 1
wb.save(OUT)
print(OUT)
