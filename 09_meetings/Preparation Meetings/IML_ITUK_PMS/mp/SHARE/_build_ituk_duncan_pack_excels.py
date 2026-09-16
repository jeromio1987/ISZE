"""Two Mode A workbooks for Duncan: coverage/1% and aftermarket compare.

ISZE to ITUK is shown. Projected ITUK to dealers = ISZE x mark-up (yellow).
Aftermarket = UK workshop purchase. Sign only at ITUK-to-dealers vs aftermarket.
Never Outlook Send. Does not write ORIGINAL.pptx.
"""
from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SHARE = ROOT / "09_meetings" / "Preparation Meetings" / "IML_ITUK_PMS" / "mp" / "SHARE"
MEET = ROOT / "09_meetings"

PR00 = ROOT / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"
EUCON = ROOT / "01_data" / "01_Pricing" / "_raw" / "Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx"
KS_CSV = ROOT / "04_tools" / "autodoc_scraper" / "ks_results.csv"

NAVY = PatternFill("solid", fgColor="1A2B4A")
PAPER = PatternFill("solid", fgColor="F7F4EE")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
GREEN = PatternFill("solid", fgColor="E6F5EF")
RED_SOFT = PatternFill("solid", fgColor="F8E4E3")
GREY = PatternFill("solid", fgColor="E7E6E6")
WHITE = PatternFill("solid", fgColor="FFFFFF")

FONT_TITLE = Font(name="Calibri", size=16, bold=True, color="1A2B4A")
FONT_SEC = Font(name="Calibri", size=12, bold=True, color="1A2B4A")
FONT_HDR = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
FONT_BODY = Font(name="Calibri", size=10, color="222222")
FONT_MUTED = Font(name="Calibri", size=9, color="6B6256")
FONT_WARN = Font(name="Calibri", size=10, bold=True, color="C0552D")
FONT_INPUT = Font(name="Calibri", size=10, bold=True, color="222222")

THIN = Border(
    left=Side(style="thin", color="D9D3C8"),
    right=Side(style="thin", color="D9D3C8"),
    top=Side(style="thin", color="D9D3C8"),
    bottom=Side(style="thin", color="D9D3C8"),
)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_C = Alignment(wrap_text=True, vertical="center")
WRAP_CC = Alignment(wrap_text=True, vertical="center", horizontal="center")
WRAP_R = Alignment(wrap_text=True, vertical="center", horizontal="right")

EUR = '#,##0.00'
PCT = "0%"
NUM0 = "#,##0"
NUM1 = "#,##0.0"
NUM2 = "#,##0.00"

FX_GBP_EUR = 1.17
BAND = 0.10
MARKUP = 1.40

# Locked ITUK to dealer calendar 2025, ITUK PMS part list (56 PNs).
FAMILIES = [
    # name, qty, isze_valued_eur
    ("Oil filter", 11216, 77405),
    ("Fuel filter", 17975, 220657),
    ("Air filter", 3606, 106174),
    ("Brake", 3638, 317717),
    ("Clutch", 408, 31028),
]

COVER = [
    # name, expected, dlr_qty, isze_qty
    ("Oil filter", 11698.75, 5404, 4673),
    ("Fuel filter", 11698.75, 11139, 11021),
    ("Air filter", 11698.75, 2289, 2226),
]


def z10(v) -> str:
    s = str(v).replace(".0", "").strip()
    return s.zfill(10) if s.isdigit() else s


def widths(ws, pairs):
    for col, w in pairs.items():
        ws.column_dimensions[col].width = w


def paint(cell, fill=None, font=None, fmt=None, align=None):
    if fill is not None:
        cell.fill = fill
    cell.font = font or FONT_BODY
    cell.alignment = align or WRAP
    cell.border = THIN
    if fmt:
        cell.number_format = fmt


def header_row(ws, row, n_cols, height=28):
    ws.row_dimensions[row].height = height
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = FONT_HDR
        cell.alignment = WRAP_CC
        cell.border = THIN


def page_setup(ws, title):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6)
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.left.text = title
    ws.oddFooter.left.text = "ITUK PMS working paper  |  DRAFT  |  confirm mark-up before IML"
    ws.oddFooter.right.text = "Page &P of &N"
    ws.sheet_view.showGridLines = False


def load_pr00() -> dict[str, float]:
    df = pd.read_parquet(PR00)
    df["part_number"] = df["part_number"].astype(str).map(z10)
    df = df[df["price_condition"] == "PR00"].copy()
    out = {}
    for _, r in df.iterrows():
        if pd.notna(r["sp_eur"]):
            out[r["part_number"]] = float(r["sp_eur"])
    return out


def load_eucon() -> pd.DataFrame:
    df = pd.read_excel(EUCON, sheet_name="HCV", dtype={"Isuzu Part Number": str})
    df["pn"] = df["Isuzu Part Number"].astype(str).map(z10)
    df["brand"] = df["Manufacturer Brand"].astype(str).str.strip()
    df["comp_pn"] = df["Competitor Part Number"].astype(str).str.strip()
    df["ws_gbp"] = pd.to_numeric(df["Workshop Purchase Price"], errors="coerce")
    df["quality"] = df["Comparability Quality"].astype(str)
    return df


def brand_median(eu: pd.DataFrame, pn: str) -> tuple[str, float | None]:
    sub = eu[(eu["pn"] == pn) & eu["ws_gbp"].notna()].copy()
    if sub.empty:
        return "no price found", None
    oe = sub[sub["quality"].str.contains("OE comparable", case=False, na=False)]
    use = oe if len(oe) else sub
    brands = ", ".join(sorted(use["brand"].dropna().unique()))
    med = float(use["ws_gbp"].median() * FX_GBP_EUR)
    return brands, med


def save_both(wb: Workbook, name: str) -> Path:
    a = MEET / name
    b = ROOT / name
    a.parent.mkdir(parents=True, exist_ok=True)
    wb.save(a)
    shutil.copy2(a, b)
    print("wrote", a)
    return a


def build_coverage() -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    widths(ws, {"A": 28, "B": 100})
    ws.merge_cells("A1:B1")
    ws["A1"] = "ITUK PMS coverage and 1 percent  |  DRAFT"
    ws["A1"].font = FONT_TITLE
    ws.merge_cells("A2:B2")
    ws["A2"] = (
        f"Built {date.today().isoformat()}. "
        "We compare the projected ITUK price to dealers with aftermarket workshop purchase on the sister file. "
        "Same step in the chain. This file is volume and value only."
    )
    ws["A2"].font = FONT_MUTED
    ws["A2"].alignment = WRAP
    ws.row_dimensions[2].height = 36
    header_row(ws, 4, 2)
    ws.cell(4, 1, "Topic")
    ws.cell(4, 2, "Note")
    notes = [
        ("Price levels",
         "ISZE to ITUK = sales price to ITUK. Projected ITUK to dealers = ISZE to ITUK x the yellow mark-up (1.40 = 40 percent). Aftermarket sits on the other workbook."),
        ("1 percent",
         "1.00 percentage point of calendar 2025 ITUK sales to dealers on the ITUK PMS part list (56 part numbers). Quantity and value. Value is shown at ISZE to ITUK and at projected ITUK to dealers."),
        ("Coverage",
         "N75 filter coverage = actual quantity / expected from the IML service schedule (9,359 vehicles, 1.25 services per year). Fuel 94 percent is N75 only."),
        ("What to confirm",
         "The yellow mark-up. If ITUK margin is not 40 percent, change Inputs!B4. All projected values are formulas."),
    ]
    r = 5
    for t, n in notes:
        ws.row_dimensions[r].height = 44
        paint(ws.cell(r, 1, t), PAPER, FONT_SEC)
        paint(ws.cell(r, 2, n), WHITE)
        r += 1
    page_setup(ws, "Read me")
    ws.freeze_panes = "A5"

    wi = wb.create_sheet("Inputs")
    widths(wi, {"A": 40, "B": 16, "C": 70})
    wi["A1"] = "Yellow cells are inputs. Other sheets read them."
    wi["A1"].font = FONT_TITLE
    wi.merge_cells("A1:C1")
    header_row(wi, 3, 3)
    wi.cell(3, 1, "Input")
    wi.cell(3, 2, "Value")
    wi.cell(3, 3, "Used for")
    paint(wi.cell(4, 1, "ITUK mark-up on ISZE to ITUK"), PAPER)
    paint(wi.cell(4, 2, MARKUP), YELLOW, FONT_INPUT, NUM2, WRAP_R)
    paint(wi.cell(4, 3, "Projected ITUK to dealers = ISZE to ITUK x this. 1.40 = 40 percent."), WHITE)
    paint(wi.cell(5, 1, "1 percentage point"), PAPER)
    paint(wi.cell(5, 2, 0.01), YELLOW, FONT_INPUT, PCT, WRAP_R)
    paint(wi.cell(5, 3, "1.00 point of actual ITUK to dealer quantity and value."), WHITE)
    wi["A7"] = "Inputs!B4 = mark-up. Inputs!B5 = 1 percent."
    wi["A7"].font = FONT_MUTED
    wi.freeze_panes = "A4"
    page_setup(wi, "Inputs")

    wc = wb.create_sheet("N75_filter_coverage")
    widths(wc, {get_column_letter(i): w for i, w in enumerate([22, 14, 18, 14, 16, 14], 1)})
    wc.merge_cells("A1:F1")
    wc["A1"] = "N75 filter coverage, calendar 2025"
    wc["A1"].font = FONT_TITLE
    wc.merge_cells("A2:F2")
    wc["A2"] = (
        "Coverage is actual quantity sold divided by the quantity expected from the IML service schedule "
        "(N75, 9,359 vehicles, 1.25 services per year). Fuel 94 percent is N75 only, not the complete United Kingdom parc."
    )
    wc["A2"].font = FONT_MUTED
    wc["A2"].alignment = WRAP
    wc.row_dimensions[2].height = 32
    header_row(wc, 4, 6)
    for i, h in enumerate(
        ["Filter", "Expected", "ITUK to dealer", "Dealer cover", "ISZE to ITUK", "ISZE cover"], 1
    ):
        wc.cell(4, i, h)
    for i, (name, exp, dlr, isze) in enumerate(COVER, 5):
        wc.row_dimensions[i].height = 22
        paint(wc.cell(i, 1, name), WHITE)
        paint(wc.cell(i, 2, exp), WHITE, FONT_BODY, NUM2, WRAP_R)
        paint(wc.cell(i, 3, dlr), WHITE, FONT_BODY, NUM0, WRAP_R)
        c = wc.cell(i, 4)
        c.value = f"=C{i}/B{i}"
        paint(c, WHITE, FONT_BODY, PCT, WRAP_CC)
        paint(wc.cell(i, 5, isze), WHITE, FONT_BODY, NUM0, WRAP_R)
        c = wc.cell(i, 6)
        c.value = f"=E{i}/B{i}"
        paint(c, WHITE, FONT_BODY, PCT, WRAP_CC)
    page_setup(wc, "N75 coverage")
    wc.freeze_panes = "A5"

    wf = wb.create_sheet("One_pct_all_PMS")
    widths(wf, {get_column_letter(i): w for i, w in enumerate([18, 16, 22, 22, 16, 22, 26], 1)})
    wf.merge_cells("A1:G1")
    wf["A1"] = "1.00 percentage point on all ITUK PMS parts  |  ITUK to dealers, calendar 2025"
    wf["A1"].font = FONT_TITLE
    wf.merge_cells("A2:G2")
    wf["A2"] = (
        "56 part numbers on the ITUK PMS list. Quantity is ITUK sales to dealers. "
        "ISZE to ITUK value uses the 2025 average sales price to ITUK. "
        "Projected ITUK to dealers = ISZE to ITUK value x Inputs!B4."
    )
    wf["A2"].font = FONT_MUTED
    wf["A2"].alignment = WRAP
    wf.row_dimensions[2].height = 36
    header_row(wf, 4, 7)
    for i, h in enumerate(
        [
            "Family",
            "Dealer qty",
            "ISZE to ITUK EUR",
            "Projected ITUK to dealers EUR",
            "1% qty",
            "1% ISZE to ITUK EUR",
            "1% projected ITUK to dealers EUR",
        ],
        1,
    ):
        wf.cell(4, i, h)
    for i, (name, qty, isze_eur) in enumerate(FAMILIES, 5):
        wf.row_dimensions[i].height = 22
        paint(wf.cell(i, 1, name), WHITE)
        paint(wf.cell(i, 2, qty), WHITE, FONT_BODY, NUM0, WRAP_R)
        paint(wf.cell(i, 3, isze_eur), WHITE, FONT_BODY, EUR, WRAP_R)
        c = wf.cell(i, 4)
        c.value = f"=C{i}*Inputs!$B$4"
        paint(c, WHITE, FONT_BODY, EUR, WRAP_R)
        c = wf.cell(i, 5)
        c.value = f"=B{i}*Inputs!$B$5"
        paint(c, WHITE, FONT_BODY, NUM1, WRAP_R)
        c = wf.cell(i, 6)
        c.value = f"=C{i}*Inputs!$B$5"
        paint(c, WHITE, FONT_BODY, EUR, WRAP_R)
        c = wf.cell(i, 7)
        c.value = f"=D{i}*Inputs!$B$5"
        paint(c, WHITE, FONT_BODY, EUR, WRAP_R)
    tot = 5 + len(FAMILIES)
    paint(wf.cell(tot, 1, "TOTAL"), PAPER, FONT_SEC)
    for col, letter in [(2, "B"), (3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G")]:
        c = wf.cell(tot, col)
        c.value = f"=SUM({letter}5:{letter}{tot - 1})"
        fmt = NUM0 if col == 2 else (NUM1 if col == 5 else EUR)
        paint(c, PAPER, FONT_SEC, fmt, WRAP_R)
    wf.row_dimensions[tot].height = 24
    wf.cell(tot + 2, 1, "Change Inputs!B4 if the ITUK mark-up is not 40 percent. Projected columns are formulas.")
    wf.merge_cells(start_row=tot + 2, start_column=1, end_row=tot + 2, end_column=7)
    wf.cell(tot + 2, 1).font = FONT_MUTED
    page_setup(wf, "1 percent")
    wf.freeze_panes = "A5"
    return save_both(wb, "ITUK_PMS_Coverage_1pct_DRAFT.xlsx")


def build_aftermarket() -> Path:
    pr00 = load_pr00()
    eu = load_eucon()
    ks_ok = KS_CSV.exists()

    focus = [
        ("Oil filter", "8983282070"),
        ("Fuel filter", "8975425400"),
        ("Air filter", "8981772710"),
        ("Brake pad", "8982447940"),
        ("Clutch disc", "8981649171"),
        ("Clutch pressure plate", "8970388314"),
        ("Clutch release bearing", "1313100120"),
        ("Clutch kit (BVP)", "5876102320"),
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    widths(ws, {"A": 28, "B": 100})
    ws.merge_cells("A1:B1")
    ws["A1"] = "ITUK PMS aftermarket compare  |  DRAFT"
    ws["A1"].font = FONT_TITLE
    ws.merge_cells("A2:B2")
    ws["A2"] = (
        f"Built {date.today().isoformat()}. "
        "We compare the projected ITUK price to dealers with aftermarket workshop purchase. Same step in the chain."
    )
    ws["A2"].font = FONT_SEC
    ws["A2"].alignment = WRAP
    ws.row_dimensions[2].height = 32
    header_row(ws, 4, 2)
    ws.cell(4, 1, "Topic")
    ws.cell(4, 2, "Note")
    notes = [
        ("ISZE to ITUK",
         "Sales price to ITUK (list). Duncan may see this. It is one step earlier than a workshop buy."),
        ("Projected ITUK to dealers",
         "ISZE to ITUK x Inputs!B4. Working mark-up 1.40 (40 percent). Change the yellow cell if the mark-up is different."),
        ("Aftermarket workshop",
         "United Kingdom workshop purchase, Eucon IAM survey 2023, HCV sheet, OE-comparable where marked. Converted at Inputs!B5. Same commercial step as a dealer or workshop buy."),
        ("The compare",
         "Sign and percent use projected ITUK to dealers versus aftermarket workshop only. Do not read ISZE to ITUK against aftermarket. That mixes a distributor buy with a workshop buy."),
        ("KS International",
         "Searched on these part numbers in August 2026. No price found."),
        ("What is out",
         "DAF and other OEM peer prices are not physical fitment. They are not on this sheet."),
    ]
    r = 5
    for t, n in notes:
        ws.row_dimensions[r].height = 40
        paint(ws.cell(r, 1, t), PAPER, FONT_SEC)
        paint(ws.cell(r, 2, n), WHITE)
        r += 1
    page_setup(ws, "Read me")
    ws.freeze_panes = "A5"

    wi = wb.create_sheet("Inputs")
    widths(wi, {"A": 40, "B": 16, "C": 72})
    wi["A1"] = "Yellow cells are inputs."
    wi["A1"].font = FONT_TITLE
    header_row(wi, 3, 3)
    wi.cell(3, 1, "Input")
    wi.cell(3, 2, "Value")
    wi.cell(3, 3, "Used for")
    paint(wi.cell(4, 1, "ITUK mark-up on ISZE to ITUK"), PAPER)
    paint(wi.cell(4, 2, MARKUP), YELLOW, FONT_INPUT, NUM2, WRAP_R)
    paint(wi.cell(4, 3, "Projected ITUK to dealers = ISZE to ITUK x this."), WHITE)
    paint(wi.cell(5, 1, "GBP to EUR"), PAPER)
    paint(wi.cell(5, 2, FX_GBP_EUR), YELLOW, FONT_INPUT, NUM2, WRAP_R)
    paint(wi.cell(5, 3, "Converts 2023 United Kingdom workshop GBP to EUR."), WHITE)
    paint(wi.cell(6, 1, "In-line band"), PAPER)
    paint(wi.cell(6, 2, BAND), YELLOW, FONT_INPUT, PCT, WRAP_R)
    paint(wi.cell(6, 3, "Absolute gap inside this band = in line."), WHITE)
    wi.freeze_panes = "A4"
    page_setup(wi, "Inputs")

    wt = wb.create_sheet("Compare")
    wt.sheet_properties.tabColor = "C0552D"
    tcols = [
        "Part",
        "PN",
        "ISZE to ITUK EUR",
        "Projected ITUK to dealers EUR",
        "Aftermarket workshop EUR",
        "Aftermarket brands",
        "Sign (ITUK to dealers vs aftermarket)",
        "% projected ITUK vs aftermarket",
        "KS International",
    ]
    widths(wt, {get_column_letter(i): w for i, w in enumerate(
        [24, 16, 16, 22, 20, 36, 28, 20, 22], 1)})
    wt.merge_cells("A1:I1")
    wt["A1"] = "Three price levels. Compare only the last two."
    wt["A1"].font = FONT_TITLE
    wt.merge_cells("A2:I2")
    wt["A2"] = (
        "We compare the projected ITUK price to dealers with aftermarket workshop purchase. Same step in the chain. "
        "Column D = C x Inputs!B4. Sign and percent use D versus E. KS International: no price found."
    )
    wt["A2"].font = FONT_SEC
    wt["A2"].alignment = WRAP
    wt.row_dimensions[2].height = 36
    header_row(wt, 4, 9)
    for i, h in enumerate(tcols, 1):
        wt.cell(4, i, h)

    for i, (fn, pn) in enumerate(focus, 5):
        isze = pr00.get(pn)
        brands, med = brand_median(eu, pn)
        if fn.startswith("Clutch kit"):
            brands, med = "no price found", None
        wt.row_dimensions[i].height = 28
        paint(wt.cell(i, 1, fn), WHITE)
        paint(wt.cell(i, 2, pn), WHITE, FONT_BODY, None, WRAP_CC)
        if isze is None:
            paint(wt.cell(i, 3, "no price found"), GREY, FONT_MUTED, None, WRAP_CC)
            paint(wt.cell(i, 4, "no price found"), GREY, FONT_MUTED, None, WRAP_CC)
        else:
            paint(wt.cell(i, 3, isze), WHITE, FONT_BODY, EUR, WRAP_R)
            c = wt.cell(i, 4)
            c.value = f"=C{i}*Inputs!$B$4"
            paint(c, WHITE, FONT_BODY, EUR, WRAP_R)
        if med is None:
            paint(wt.cell(i, 5, "no price found"), GREY, FONT_MUTED, None, WRAP_CC)
            paint(wt.cell(i, 6, brands), GREY, FONT_MUTED)
            paint(wt.cell(i, 7, "no price found"), GREY, FONT_MUTED, None, WRAP_CC)
            paint(wt.cell(i, 8, "no price found"), GREY, FONT_MUTED, None, WRAP_CC)
        else:
            paint(wt.cell(i, 5, med), WHITE, FONT_BODY, EUR, WRAP_R)
            paint(wt.cell(i, 6, brands), WHITE)
            sign = wt.cell(i, 7)
            sign.value = (
                f'=IF(OR(E{i}="",E{i}="no price found",NOT(ISNUMBER(D{i})),NOT(ISNUMBER(E{i}))),"no price found",'
                f'IF((D{i}/E{i}-1)>Inputs!$B$6,"above aftermarket",'
                f'IF((D{i}/E{i}-1)<-Inputs!$B$6,"below aftermarket","in line")))'
            )
            paint(sign, WHITE, FONT_BODY, None, WRAP_CC)
            pct = wt.cell(i, 8)
            pct.value = (
                f'=IF(OR(E{i}="",E{i}="no price found",NOT(ISNUMBER(D{i})),NOT(ISNUMBER(E{i}))),'
                f'"no price found",D{i}/E{i}-1)'
            )
            paint(pct, WHITE, FONT_BODY, PCT, WRAP_CC)
        paint(wt.cell(i, 9, "no price found"), GREY, FONT_MUTED, None, WRAP_CC)

    last = 4 + len(focus)
    # Colour signs after Excel would calc; apply a static hint for pad row
    for i, (fn, _pn) in enumerate(focus, 5):
        if fn == "Brake pad":
            for c in range(1, 10):
                wt.cell(i, c).fill = RED_SOFT
            wt.cell(i, 7).font = FONT_WARN

    wt.cell(last + 2, 1,
            "The pad is the line where projected ITUK to dealers sits well above aftermarket workshop. "
            "Filters are close. Clutch disc sits below. KS International: no price found.")
    wt.merge_cells(start_row=last + 2, start_column=1, end_row=last + 2, end_column=9)
    wt.cell(last + 2, 1).font = FONT_SEC
    wt.cell(last + 2, 1).alignment = WRAP
    wt.row_dimensions[last + 2].height = 32
    wt.auto_filter.ref = f"A4:I{last}"
    wt.freeze_panes = "A5"
    page_setup(wt, "Compare")

    wb_p = wb.create_sheet("Brand_prices")
    bcols = [
        "Part", "PN", "ISZE to ITUK EUR", "Projected ITUK to dealers EUR",
        "Brand", "Brand PN", "Workshop GBP", "Aftermarket workshop EUR",
        "Sign (ITUK to dealers vs this brand)", "% projected ITUK vs this brand",
    ]
    widths(wb_p, {get_column_letter(i): w for i, w in enumerate(
        [20, 14, 16, 22, 16, 18, 14, 20, 28, 20], 1)})
    wb_p.merge_cells("A1:J1")
    wb_p["A1"] = "One row per aftermarket brand quote"
    wb_p["A1"].font = FONT_TITLE
    wb_p.merge_cells("A2:J2")
    wb_p["A2"] = (
        "We compare the projected ITUK price to dealers with aftermarket workshop purchase. Same step in the chain. "
        "Workshop EUR = GBP x Inputs!B5. Sign uses D versus H."
    )
    wb_p["A2"].font = FONT_MUTED
    wb_p["A2"].alignment = WRAP
    header_row(wb_p, 4, 10)
    for i, h in enumerate(bcols, 1):
        wb_p.cell(4, i, h)

    fn_by_pn = {pn: fn for fn, pn in focus if not fn.startswith("Clutch kit")}
    sub = eu[eu["pn"].isin(fn_by_pn) & eu["ws_gbp"].notna()].copy()
    sub = sub.sort_values(["pn", "brand", "ws_gbp"])
    r = 5
    for _, row in sub.iterrows():
        pn = row["pn"]
        isze = pr00.get(pn)
        wb_p.row_dimensions[r].height = 20
        paint(wb_p.cell(r, 1, fn_by_pn[pn]), WHITE)
        paint(wb_p.cell(r, 2, pn), WHITE, FONT_BODY, None, WRAP_CC)
        paint(wb_p.cell(r, 3, isze if isze is not None else "no price found"), WHITE, FONT_BODY, EUR if isze else None, WRAP_R)
        c = wb_p.cell(r, 4)
        c.value = f'=IF(ISNUMBER(C{r}),C{r}*Inputs!$B$4,"no price found")'
        paint(c, WHITE, FONT_BODY, EUR, WRAP_R)
        paint(wb_p.cell(r, 5, row["brand"]), WHITE)
        paint(wb_p.cell(r, 6, row["comp_pn"]), WHITE)
        paint(wb_p.cell(r, 7, float(row["ws_gbp"])), WHITE, FONT_BODY, NUM2, WRAP_R)
        c = wb_p.cell(r, 8)
        c.value = f"=G{r}*Inputs!$B$5"
        paint(c, WHITE, FONT_BODY, EUR, WRAP_R)
        sign = wb_p.cell(r, 9)
        sign.value = (
            f'=IF(OR(H{r}="",H{r}=0,NOT(ISNUMBER(D{r}))),"no price found",'
            f'IF((D{r}/H{r}-1)>Inputs!$B$6,"above aftermarket",'
            f'IF((D{r}/H{r}-1)<-Inputs!$B$6,"below aftermarket","in line")))'
        )
        paint(sign, WHITE, FONT_BODY, None, WRAP_CC)
        pct = wb_p.cell(r, 10)
        pct.value = f'=IF(OR(H{r}="",H{r}=0,NOT(ISNUMBER(D{r}))),"no price found",D{r}/H{r}-1)'
        paint(pct, WHITE, FONT_BODY, PCT, WRAP_CC)
        r += 1
    last_b = r - 1
    if last_b >= 5:
        wb_p.auto_filter.ref = f"A4:J{last_b}"
    wb_p.freeze_panes = "A5"
    page_setup(wb_p, "Brand prices")

    ws_s = wb.create_sheet("Sources")
    widths(ws_s, {"A": 28, "B": 100})
    ws_s["A1"] = "Sources"
    ws_s["A1"].font = FONT_TITLE
    header_row(ws_s, 3, 2)
    ws_s.cell(3, 1, "Item")
    ws_s.cell(3, 2, "Path / note")
    sources = [
        ("ISZE to ITUK", str(PR00) + "  |  PR00 list, euro, ex VAT"),
        ("Aftermarket", str(EUCON) + "  |  HCV  |  workshop purchase GBP 2023"),
        ("KS International", str(KS_CSV) + "  |  searched August 2026  |  no price found"),
        ("Mark-up", "Working 1.40 (40 percent). Yellow on Inputs. Confirmed house channel step 30 Mar 2026."),
        ("KS status file present", "yes" if ks_ok else "file missing"),
    ]
    for i, (a, b) in enumerate(sources, 4):
        ws_s.row_dimensions[i].height = 28
        paint(ws_s.cell(i, 1, a), PAPER, FONT_SEC)
        paint(ws_s.cell(i, 2, b), WHITE)
    ws_s.freeze_panes = "A4"
    page_setup(ws_s, "Sources")
    return save_both(wb, "ITUK_PMS_Aftermarket_Compare_DRAFT.xlsx")


def main() -> int:
    p1 = build_coverage()
    p2 = build_aftermarket()
    print("coverage", p1)
    print("aftermarket", p2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
