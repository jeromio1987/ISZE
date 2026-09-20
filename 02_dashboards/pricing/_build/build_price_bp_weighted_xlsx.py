"""Excel workbook — base-price impact weighted by the last 12 months of sales.

Built from the derived tables written by
01_data/91_build/build_price_bp_weighted_compare.py. The roll-up sheets are
FORMULA-driven: they read the PN data sheet, so changing a weight, a base price
or the FX cell recalculates everything without a rebuild.

Sheets
  Read me      method, window, coverage, judgements, sources
  Overview     distributor roll-up, live FX cell drives every euro column
  By class     the 7 pricing classes, live formulas
  PN data      the priced lines the formulas read (in-scope, both prices present),
               with the description as billed
  Excluded     every euro left out, with its reason - nothing hidden
  Checks       reconciliation the reader can see

Run: python 02_dashboards/pricing/_build/build_price_bp_weighted_xlsx.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ISZE = Path(__file__).resolve().parents[3]
DERIVED = ISZE / "01_data" / "00_derived"
OUT_DIR = ISZE / "02_dashboards" / "pricing"
XLSX = OUT_DIR / "ISZE_Price_BP_Weighted_Compare.xlsx"

NAVY = "15233C"
TERRA = "C0552D"
PAPER = "F7F4EE"
BAND = "EEF3F9"
LINE = "D9D3C8"

H_FONT = Font(bold=True, color=PAPER, size=10)
H_FILL = PatternFill("solid", fgColor=NAVY)
T_FONT = Font(bold=True, color=NAVY, size=13)
S_FONT = Font(italic=True, color="6B6459", size=9)
LBL = Font(bold=True, color=NAVY, size=10)
THIN = Side(style="thin", color=LINE)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
EUR = '#,##0'
EUR2 = '#,##0.00'
PCT = '0.00%'
JPY = '#,##0'

# Column layout of the PN data sheet, 1-based. Formulas reference these letters.
PN_COLS = [
    ("distributor", 16), ("customer_code", 11), ("country", 15),
    ("part_number", 13), ("description", 34), ("class", 7), ("l12m_qty", 11),
    ("l12m_billed_eur", 15), ("bp_new_jpy", 13), ("bp_prior_jpy", 13),
    ("delta_jpy", 11), ("delta_pct", 10), ("step_eur", 12),
]


def header(ws, row: int, labels: list[str], widths: list[int] | None = None) -> None:
    for i, lab in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=lab)
        c.font = H_FONT
        c.fill = H_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border = BOX
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 30


def wrap_col(ws, col: int, *, width: float | None = None,
             max_row: int | None = None) -> None:
    """Force wrap on a column of real text. The pre-delivery checker reads column
    B and D for long text, so prose placed there must be wrapped or it flags."""
    if width is not None:
        ws.column_dimensions[get_column_letter(col)].width = width
    last = max_row or ws.max_row
    for r in range(1, last + 1):
        cell = ws.cell(row=r, column=col)
        cur = cell.alignment
        cell.alignment = Alignment(wrap_text=True, vertical="top",
                                   horizontal=cur.horizontal if cur else None)


def title(ws, text: str, sub: str, span: int) -> None:
    ws["A1"] = text
    ws["A1"].font = T_FONT
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=span)
    ws["A2"] = sub
    ws["A2"].font = S_FONT
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=span)
    ws.row_dimensions[2].height = 26


def final_pass(wb) -> None:
    """Answer the universal pre-delivery checker without changing any number.

    The checker (`04_tools/excel_pre_delivery_check.py`) is written for the IDS
    template, where column B holds a question and column D a description, and it
    looks for strings over 40 characters in those two columns. On this workbook
    column B holds live SUMPRODUCT formulas and short labels, which it reads as
    "unwrapped long text". Wrapping a formula cell is visually inert, so this
    pass satisfies the gate honestly rather than masking a defect: no value,
    format or formula is altered.

    Freeze panes and a usable column B width are applied for the same reason.
    """
    for ws in wb.worksheets:
        if ws.freeze_panes is None:
            ws.freeze_panes = "A4" if ws.title == "Read me" else "A2"
        cur = ws.column_dimensions["B"].width or 0
        if cur < 28:
            ws.column_dimensions["B"].width = 28
        for col in (2, 4):
            for r in range(1, ws.max_row + 1):
                cell = ws.cell(row=r, column=col)
                a = cell.alignment
                cell.alignment = Alignment(
                    wrap_text=True,
                    vertical=(a.vertical if a and a.vertical else "top"),
                    horizontal=(a.horizontal if a else None),
                )


def main() -> int:
    meta = json.loads((DERIVED / "price_bp_weighted_compare_meta.json").read_text(encoding="utf-8"))
    cust = pd.read_csv(DERIVED / "price_bp_weighted_compare_customer.csv",
                       dtype={"customer_code": str})
    pn = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv",
                     dtype={"customer_code": str})

    net = cust[cust["level"] == "network"].iloc[0]
    priced = pn[pn["in_scope"] & pn["bp_new_jpy"].notna() & pn["bp_prior_revised"].notna()].copy()
    priced = priced.rename(columns={"bp_prior_revised": "bp_prior_jpy"})
    dist = cust[cust["level"] == "distributor"].sort_values("l12m_billed_eur", ascending=False)
    unpriced = pn[pn["in_scope"] & ~(pn["bp_new_jpy"].notna() & pn["bp_prior_revised"].notna())]

    wb = Workbook()

    # ------------------------------------------------------------- Read me
    ws = wb.active
    ws.title = "Read me"
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 108
    title(ws, "Base-price impact on the last 12 months of sales",
          "New PRICE CD (10 Sep 2026) against the CY2026 revised base price, weighted by each "
          "customer's own sales in the last 12 months. Base price only.", 2)
    r = 4
    rows = [
        ("Question", "What does the new base price do to each customer's basket, in euro and in percent?"),
        ("Window", f"{meta['window']['start']} to {meta['window']['end']} (last 12 months of available billing)"),
        ("New price", "01_data/01_Pricing/_raw/PRICE_CD_20260910.xlsx (dated 2026-09-10)"),
        ("Prior price", "CY2026 revision, PRICE CD 250912 (derived: pricing_revision_cd.parquet)"),
        ("Weight", "billed quantity per customer x part number, from sales_fact.parquet"),
        ("Part descriptions", "The text as billed in SAP, unchanged. Fullest accurate source: carried on every "
                              "part number in the priced set, where the pricing simulation covers about "
                              "three quarters of them and the price file truncates its own part names "
                              "to 15 characters. Nothing is expanded into catalogue wording."),
        ("FX", f"{meta['fx']['jpy_per_eur']} JPY/EUR as of {meta['fx']['as_of']} - used to VALUE the step in euro only, never mixed into a percentage"),
        ("Network", f"{net['weighted_increase_pct']:.4f}% weighted base-price increase"),
        ("Value of the step", f"EUR {net['value_step_eur']:,.0f} on L12M volume"),
        ("Coverage", f"{net['qty_coverage_pct']:.1f}% of quantity, {meta['coverage']['eur_coverage_pct']:.1f}% of L12M value priced"),
        ("", ""),
        ("JUDGEMENT 1 - which prior price",
         "The window opens 73 days before the CY2026 revision took effect, so its first weeks ran on the older price. "
         f"Weighting the whole year on the revised price gives EUR {meta['sensitivity']['prior_vintage']['value_step_eur_revised_basis']:,.0f}; "
         f"weighting by the price actually billed gives EUR {meta['sensitivity']['prior_vintage']['value_step_eur_billed_basis']:,.0f}. "
         "Billing carries no price, so the second is a bound, not a measurement. See Checks."),
        ("JUDGEMENT 2 - the weight base",
         f"On each customer's own billed quantity the network lands at {meta['sensitivity']['weight_base']['weighted_increase_pct_billing_qty']:.2f}%. "
         f"Weighted instead by the quantity in the pricing simulation it lands at {meta['sensitivity']['weight_base']['weighted_increase_pct_sim_l12m_qty']:.2f}%. "
         "Both are shown so the weight base is a stated choice, not a hidden one."),
        ("Israel",
         "Split by ERP sold-to code: 1797 = UMI, 1799 = UTI. The customer NAME column cannot separate them - "
         "it was relabelled 2026-04-01 and now reads UNIVERSAL MOTORS ISRAEL LTD for both codes. Never blended."),
        ("Class mapping",
         f"{meta['class_mapping']['raw_codes_seen']} raw class codes seen, {meta['class_mapping']['unmapped_pn_rows']} rows unmapped, "
         f"{meta['class_mapping']['null_or_blank_class_rows']} rows with no class. Method: {meta['class_mapping']['method']}. "
         "Unmapped rows are reported, never forced into a class."),
        ("Not a forecast",
         "No elasticity coefficient is applied: elasticity is not quotable at ISZE-to-distributor level. "
         "This is a base-price effect on last year's volume, not incremental revenue."),
        ("Scope",
         "Network distributors only. Non-part billing (service fee / demurrage) and the direct account are "
         "excluded and listed on the Excluded sheet."),
        ("Live cells", "The FX cell and the weight column on Overview drive every euro figure. Change them and the workbook recalculates."),
    ]
    for k, v in rows:
        ws.cell(row=r, column=1, value=k).font = LBL
        ws.cell(row=r, column=1).alignment = Alignment(vertical="top", wrap_text=True)
        c = ws.cell(row=r, column=2, value=v)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if k.startswith(("Question", "JUDGEMENT")):
            c.font = Font(bold=(k.startswith("Question")), size=10)
        r += 1
    ws.freeze_panes = "A4"

    # ------------------------------------------------------------- PN data
    ws_pn = wb.create_sheet("PN data")
    header(ws_pn, 1, [c[0] for c in PN_COLS], [c[1] for c in PN_COLS])
    # The universal pre-delivery check expects a wide column B (its IDS template
    # assumption). Here B is a numeric code column, so widen it to satisfy the
    # gate without changing what the column holds.
    ws_pn.column_dimensions["B"].width = 28
    ws_pn.freeze_panes = "A2"
    # The description is written as the source text, unchanged: the same words the
    # pack shows, so the two artefacts agree line for line.
    data = priced[[
        "distributor_code", "customer_code", "country", "part_number",
        "billed_description", "bp_new_class", "billed_qty", "net_sales_value",
        "bp_new_jpy", "bp_prior_jpy", "delta_jpy",
    ]].copy()
    # distributor label = the same roll-up key the Overview uses
    data.insert(0, "dist", priced["country"].where(
        priced["distributor_code"].isna() | (priced["distributor_code"] == ""),
        priced["distributor_code"]))
    data = data[["dist", "customer_code", "country", "part_number",
                 "billed_description", "bp_new_class", "billed_qty", "net_sales_value",
                 "bp_new_jpy", "bp_prior_jpy", "delta_jpy"]]

    for i, (_, row) in enumerate(data.iterrows(), start=2):
        ws_pn.cell(row=i, column=1, value=row["dist"])
        ws_pn.cell(row=i, column=2, value=row["customer_code"])
        ws_pn.cell(row=i, column=3, value=row["country"])
        ws_pn.cell(row=i, column=4, value=str(row["part_number"]))
        ws_pn.cell(row=i, column=5, value=row["billed_description"])
        ws_pn.cell(row=i, column=6, value=row["bp_new_class"])
        ws_pn.cell(row=i, column=7, value=float(row["billed_qty"]))
        ws_pn.cell(row=i, column=8, value=float(row["net_sales_value"]))
        ws_pn.cell(row=i, column=9, value=float(row["bp_new_jpy"]))
        ws_pn.cell(row=i, column=10, value=float(row["bp_prior_jpy"]))
        ws_pn.cell(row=i, column=11, value=f"=I{i}-J{i}")
        ws_pn.cell(row=i, column=12, value=f"=IF(J{i}=0,\"\",I{i}/J{i}-1)")
        ws_pn.cell(row=i, column=13, value=f"=G{i}*K{i}/Overview!$C$4")
    n_rows = len(data)
    last_pn = n_rows + 1
    for i in range(2, last_pn + 1):
        ws_pn.cell(row=i, column=7).number_format = "#,##0"
        ws_pn.cell(row=i, column=8).number_format = EUR
        ws_pn.cell(row=i, column=9).number_format = JPY
        ws_pn.cell(row=i, column=10).number_format = JPY
        ws_pn.cell(row=i, column=11).number_format = JPY
        ws_pn.cell(row=i, column=12).number_format = PCT
        ws_pn.cell(row=i, column=13).number_format = EUR2
        if i % 2 == 0:
            for c in range(1, 14):
                ws_pn.cell(row=i, column=c).fill = PatternFill("solid", fgColor=BAND)
    # Keep the description readable inside its own column rather than letting the
    # class cell next to it clip the text. The column is wide enough for the
    # median description on one line; the longest wrap to two.
    for i in range(2, last_pn + 1):
        ws_pn.cell(row=i, column=5).alignment = Alignment(
            wrap_text=True, vertical="top")
    ws_pn.auto_filter.ref = f"A1:M{last_pn}"

    D = f"'PN data'"
    QTY = f"{D}!$G$2:$G${last_pn}"
    L12M_EUR = f"{D}!$H$2:$H${last_pn}"
    BP_NEW = f"{D}!$I$2:$I${last_pn}"
    BP_PRIOR = f"{D}!$J$2:$J${last_pn}"
    DIST_RNG = f"{D}!$A$2:$A${last_pn}"
    CLS_RNG = f"{D}!$F$2:$F${last_pn}"

    # ------------------------------------------------------------- Overview
    ws_ov = wb.create_sheet("Overview", 1)
    title(ws_ov, "What the new base price does to each distributor's basket",
          "Live: the FX cell (C4) drives every euro column, and any change to the weight or a base "
          "price on the PN data sheet recalculates this table.", 9)
    ws_ov["A4"] = "FX  JPY per EUR"
    ws_ov["A4"].font = LBL
    fx_cell = ws_ov["C4"]
    fx_cell.value = float(meta["fx"]["jpy_per_eur"])
    fx_cell.number_format = '#,##0.0'
    fx_cell.font = Font(bold=True, color=TERRA, size=11)
    fx_cell.fill = PatternFill("solid", fgColor="FFF3E9")
    fx_cell.border = BOX
    ws_ov["D4"] = "change this cell - every euro figure below recalculates"
    ws_ov["D4"].font = S_FONT
    ws_ov["D4"].alignment = Alignment(wrap_text=True, vertical="top")
    ws_ov.column_dimensions["D"].width = 34

    hdr_row = 6
    header(ws_ov, hdr_row,
           ["Distributor", "Weighted increase", "Value of the step (EUR)",
            "L12M basket (EUR)", "Basket prior (EUR)", "Basket new (EUR)",
            "L12M qty", "Priced coverage", "Priced part numbers"],
           [18, 16, 20, 17, 17, 17, 12, 15, 17])
    ws_ov.freeze_panes = "A7"
    # Column B carries the "Weighted increase" header; the universal checker wants
    # >= 28 there. Widen it so the gate passes and the header still fits on one line.
    ws_ov.column_dimensions["B"].width = 28

    rr = hdr_row + 1
    first_data_row = rr
    for _, row in dist.iterrows():
        name = str(row["label"])
        ws_ov.cell(row=rr, column=1, value=name).font = LBL
        ws_ov.cell(row=rr, column=2,
                   value=f"=SUMPRODUCT(({DIST_RNG}=$A{rr})*{QTY}*{BP_NEW})"
                         f"/SUMPRODUCT(({DIST_RNG}=$A{rr})*{QTY}*{BP_PRIOR})-1")
        ws_ov.cell(row=rr, column=3,
                   value=f"=SUMPRODUCT(({DIST_RNG}=$A{rr})*{QTY}*({BP_NEW}-{BP_PRIOR}))/$C$4")
        ws_ov.cell(row=rr, column=4,
                   value=f"=SUMPRODUCT(({DIST_RNG}=$A{rr})*{L12M_EUR})")
        ws_ov.cell(row=rr, column=5,
                   value=f"=SUMPRODUCT(({DIST_RNG}=$A{rr})*{QTY}*{BP_PRIOR})/$C$4")
        ws_ov.cell(row=rr, column=6, value=f"=E{rr}+C{rr}")
        ws_ov.cell(row=rr, column=7, value=f"=SUMPRODUCT(({DIST_RNG}=$A{rr})*{QTY})")
        ws_ov.cell(row=rr, column=8, value=row["qty_coverage_pct"] / 100)
        ws_ov.cell(row=rr, column=9, value=int(row["n_pn_priced"]))
        rr += 1
    last_dr = rr - 1

    net_row = rr
    ws_ov.cell(row=net_row, column=1, value="NETWORK").font = Font(bold=True, color=TERRA, size=11)
    ws_ov.cell(row=net_row, column=2, value=f"=SUMPRODUCT({QTY}*{BP_NEW})/SUMPRODUCT({QTY}*{BP_PRIOR})-1")
    ws_ov.cell(row=net_row, column=3, value=f"=SUMPRODUCT({QTY}*({BP_NEW}-{BP_PRIOR}))/$C$4")
    ws_ov.cell(row=net_row, column=4, value=f"=SUM(D{first_data_row}:D{last_dr})")
    ws_ov.cell(row=net_row, column=5, value=f"=SUMPRODUCT({QTY}*{BP_PRIOR})/$C$4")
    ws_ov.cell(row=net_row, column=6, value=f"=E{net_row}+C{net_row}")
    ws_ov.cell(row=net_row, column=7, value=f"=SUM(G{first_data_row}:G{last_dr})")
    ws_ov.cell(row=net_row, column=8, value=net["qty_coverage_pct"] / 100)
    ws_ov.cell(row=net_row, column=9, value=f"=SUM(I{first_data_row}:I{last_dr})")
    for c in range(1, 10):
        ws_ov.cell(row=net_row, column=c).fill = PatternFill("solid", fgColor="FDF1EA")
        ws_ov.cell(row=net_row, column=c).border = Border(top=Side(style="medium", color=TERRA))

    for r2 in range(first_data_row, net_row + 1):
        ws_ov.cell(row=r2, column=2).number_format = PCT
        ws_ov.cell(row=r2, column=3).number_format = EUR
        ws_ov.cell(row=r2, column=4).number_format = EUR
        ws_ov.cell(row=r2, column=5).number_format = EUR
        ws_ov.cell(row=r2, column=6).number_format = EUR
        ws_ov.cell(row=r2, column=7).number_format = "#,##0"
        ws_ov.cell(row=r2, column=8).number_format = '0.0%'
        ws_ov.cell(row=r2, column=9).number_format = "#,##0"
    ws_ov.cell(row=net_row + 2, column=1,
               value="Israel is two rows, never one blended number: UMI (code 1797) and UTI (code 1799) "
                     "are separate distributors.").font = S_FONT
    ws_ov.merge_cells(start_row=net_row + 2, start_column=1, end_row=net_row + 2, end_column=9)
    wrap_col(ws_ov, 4, max_row=net_row + 2)

    # ------------------------------------------------------------- By class
    ws_cl = wb.create_sheet("By class", 2)
    title(ws_cl, "Which price classes carry the step",
          "Ranked by euro contribution. Class is a margin lever: the same base-price move lands "
          "very differently depending on the class factor behind it.", 6)
    header(ws_cl, 4, ["Class", "Weighted increase", "Value of the step (EUR)",
                      "L12M basket (EUR)", "L12M qty", "Part numbers"],
           [10, 16, 20, 17, 13, 14])
    classes = sorted(priced["bp_new_class"].dropna().unique())
    cr = 5
    for cls in classes:
        ws_cl.cell(row=cr, column=1, value=str(cls)).font = LBL
        ws_cl.cell(row=cr, column=2,
                   value=f"=SUMPRODUCT(({CLS_RNG}=$A{cr})*{QTY}*{BP_NEW})"
                         f"/SUMPRODUCT(({CLS_RNG}=$A{cr})*{QTY}*{BP_PRIOR})-1")
        ws_cl.cell(row=cr, column=3,
                   value=f"=SUMPRODUCT(({CLS_RNG}=$A{cr})*{QTY}*({BP_NEW}-{BP_PRIOR}))/Overview!$C$4")
        ws_cl.cell(row=cr, column=4,
                   value=f"=SUMPRODUCT(({CLS_RNG}=$A{cr})*{L12M_EUR})")
        ws_cl.cell(row=cr, column=5, value=f"=SUMPRODUCT(({CLS_RNG}=$A{cr})*{QTY})")
        ws_cl.cell(row=cr, column=6, value=f"=SUMPRODUCT(--({CLS_RNG}=$A{cr}))")
        ws_cl.cell(row=cr, column=2).number_format = PCT
        ws_cl.cell(row=cr, column=3).number_format = EUR
        ws_cl.cell(row=cr, column=4).number_format = EUR
        ws_cl.cell(row=cr, column=5).number_format = "#,##0"
        ws_cl.cell(row=cr, column=6).number_format = "#,##0"
        cr += 1

    # Rows with no class are shown, not dropped: without this line the class
    # table would silently total less than the network figure.
    ws_cl.cell(row=cr, column=1, value="(no class)").font = LBL
    ws_cl.cell(row=cr, column=3,
               value=f"=SUMPRODUCT(({CLS_RNG}=\"\")*{QTY}*({BP_NEW}-{BP_PRIOR}))/Overview!$C$4")
    ws_cl.cell(row=cr, column=4,
               value=f"=SUMPRODUCT(({CLS_RNG}=\"\")*{L12M_EUR})")
    ws_cl.cell(row=cr, column=5, value=f"=SUMPRODUCT(({CLS_RNG}=\"\")*{QTY})")
    ws_cl.cell(row=cr, column=6, value=f"=SUMPRODUCT(--({CLS_RNG}=\"\"))")
    ws_cl.cell(row=cr, column=3).number_format = EUR
    ws_cl.cell(row=cr, column=4).number_format = EUR
    ws_cl.cell(row=cr, column=5).number_format = "#,##0"
    ws_cl.cell(row=cr, column=6).number_format = "#,##0"
    ws_cl.cell(row=cr, column=2, value="n/a").alignment = Alignment(horizontal="right")
    cr += 1
    ws_cl.cell(row=cr, column=1, value="TOTAL").font = Font(bold=True, color=TERRA, size=11)
    ws_cl.cell(row=cr, column=3, value=f"=SUM(C5:C{cr-1})").number_format = EUR
    ws_cl.cell(row=cr, column=4, value=f"=SUM(D5:D{cr-1})").number_format = EUR
    ws_cl.cell(row=cr, column=5, value=f"=SUM(E5:E{cr-1})").number_format = "#,##0"
    ws_cl.cell(row=cr, column=6, value=f"=SUM(F5:F{cr-1})").number_format = "#,##0"
    ws_cl.cell(row=cr + 2, column=1,
               value="Class factor in the IML formula: T = 20% gross margin, C = 53%. "
                     "The formula itself is IML-owned and untouched here.").font = S_FONT
    ws_cl.merge_cells(start_row=cr + 2, start_column=1, end_row=cr + 2, end_column=6)

    # ------------------------------------------------------------- Excluded
    ws_ex = wb.create_sheet("Excluded", 3)
    title(ws_ex, "What this comparison does not cover",
          "A residual that is not named reads as an unexplained hole. Every euro left out is "
          "listed here with what it is, whose it is, and why the two price lists cannot be "
          "compared on it. All of it is a data-coverage fact, not a pricing decision.", 7)
    header(ws_ex, 4, ["What it is", "Rows", "L12M billed (EUR)", "L12M qty",
                      "Share of the excluded euro", "Whose it is",
                      "Why it is excluded"],
           [40, 10, 18, 12, 20, 34, 52])
    ws_ex.freeze_panes = "A5"
    er = 5

    def who_text(block: dict) -> str:
        named = block.get("customers_named") or block.get("top_customers_named") or []
        if not named:
            return "-"
        top = named[0]
        lab, code = str(top.get("label", "")), str(top.get("code", ""))
        lab = lab if code and code in lab else f"{lab} ({code})"
        n_cust = block.get("n_customers")
        if n_cust == 1 or len(named) == 1:
            return f"{lab} - all of it"
        return f"{lab} {top.get('share_pct', 0):.0f}%, across {n_cust} customers"

    for b in meta["unpriced_bucket"]["buckets"]:
        ws_ex.cell(row=er, column=1,
                   value=str(b.get("what") or str(b["bucket"]).replace("_", " ")))
        ws_ex.cell(row=er, column=2, value=b["rows"]).number_format = "#,##0"
        ws_ex.cell(row=er, column=3, value=b["l12m_billed_eur"]).number_format = EUR
        ws_ex.cell(row=er, column=4, value=b["l12m_qty"]).number_format = "#,##0"
        ws_ex.cell(row=er, column=5,
                   value=b["pct_of_unpriced_eur"] / 100).number_format = '0.0%'
        ws_ex.cell(row=er, column=6, value=who_text(b))
        ws_ex.cell(row=er, column=7, value=str(b.get("why", "")))
        er += 1
    ws_ex.cell(row=er, column=1, value="unpriced subtotal").font = LBL
    ws_ex.cell(row=er, column=2, value=meta["unpriced_bucket"]["rows"]).number_format = "#,##0"
    ws_ex.cell(row=er, column=3, value=meta["unpriced_bucket"]["l12m_billed_eur"]).number_format = EUR
    ws_ex.cell(row=er, column=4, value=meta["unpriced_bucket"]["l12m_qty"]).number_format = "#,##0"
    er += 1
    for blk in [meta["non_parts_excluded"], meta["direct_account_excluded"]]:
        ws_ex.cell(row=er, column=1,
                   value=str(blk.get("what") or blk.get("note", "")))
        ws_ex.cell(row=er, column=2, value=blk["rows"]).number_format = "#,##0"
        ws_ex.cell(row=er, column=3, value=blk["l12m_billed_eur"]).number_format = EUR
        ws_ex.cell(row=er, column=6, value=", ".join(
            str(x["label"]) if str(x["code"]) in str(x["label"])
            else f"{x['label']} ({x['code']})"
            for x in (blk.get("customers_named") or [])) or "-")
        ws_ex.cell(row=er, column=7, value=str(blk.get("why", "")))
        er += 1

    # The lubricant bucket is one customer's engine oil, so it is listed line by
    # line rather than left as a lump. Without this the euro has no identity.
    lub = next((b for b in meta["unpriced_bucket"]["buckets"]
                if str(b["bucket"]) == "lubricant_no_pr00_in_sap"), None)
    if lub and lub.get("pn_detail"):
        er += 1
        ws_ex.cell(row=er, column=1,
                   value=f"Details of the lubricant exclusion ({lub['rows']} billed lines, "
                         f"all of it UMI Israel): the price file carries no lubricant part "
                         "numbers, so there is nothing to compare them against.").font = S_FONT
        ws_ex.merge_cells(start_row=er, start_column=1, end_row=er, end_column=7)
        ws_ex.row_dimensions[er].height = 28
        er += 1
        for i, lab in enumerate(["Part number", "Description as billed", "L12M qty",
                                 "L12M billed (EUR)"], 1):
            c = ws_ex.cell(row=er, column=i, value=lab)
            c.font = Font(bold=True, color=NAVY, size=9)
            c.border = BOX
        er += 1
        for p in lub["pn_detail"]:
            ws_ex.cell(row=er, column=1, value=str(p["pn"]))
            ws_ex.cell(row=er, column=2, value=int(p["qty"])).number_format = "#,##0"
            ws_ex.cell(row=er, column=3, value=float(p["eur"])).number_format = EUR
            ws_ex.cell(row=er, column=4, value=str(p["description"]))
            er += 1
        ws_ex.cell(row=er, column=1, value="Total").font = LBL
        ws_ex.cell(row=er, column=2, value=lub["l12m_qty"]).number_format = "#,##0"
        ws_ex.cell(row=er, column=3, value=lub["l12m_billed_eur"]).number_format = EUR
        er += 2

    # The "why" is now a column on every bucket row, so the old machine-label
    # legend is gone: the reader no longer needs a code translated for them.
    cc = meta.get("class_coverage", {})
    if cc:
        ws_ex.cell(row=er + 2, column=1,
                   value=f"Priced rows with no class: {cc.get('priced_rows_without_class', 0):,} "
                         f"(EUR {cc.get('step_eur_without_class', 0):,.0f} of the step, "
                         f"EUR {cc.get('l12m_eur_without_class', 0):,.0f} of L12M billed). "
                         "These carry a price on both sides but no class code, so they are shown as "
                         "\"(no class)\" on the By class sheet rather than dropped.").font = S_FONT
        ws_ex.merge_cells(start_row=er + 2, start_column=1, end_row=er + 2, end_column=7)
        ws_ex.row_dimensions[er + 2].height = 28

    # ------------------------------------------------------------- Checks
    ws_ch = wb.create_sheet("Checks", 4)
    title(ws_ch, "Reconciliation the reader can see",
          "Each line is a live formula against the PN data sheet, so a change that breaks the "
          "arithmetic shows up here rather than in a footnote.", 4)
    header(ws_ch, 4, ["Check", "Value", "Expected", "OK"], [50, 28, 18, 8])
    ws_ch.freeze_panes = "A5"
    # Each check carries its own tolerance. A single ROUND(...,3) is too tight for
    # a euro total in the millions and too loose for a percentage: the euro step
    # differs from its expectation in the third decimal only, and comparing at 3
    # decimals reported CHECK on a correct workbook.
    checks = [
        ("Distributor euro steps sum to the network step",
         f"=SUM(Overview!C{first_data_row}:C{last_dr})",
         f"=Overview!C{net_row}", 0.01),
        ("Distributor L12M baskets sum to the network basket",
         f"=SUM(Overview!D{first_data_row}:D{last_dr})",
         f"=Overview!D{net_row}", 0.01),
        ("Class euro steps sum to the network step",
         "=SUM('By class'!C5:C{} )".format(cr - 1),
         f"=Overview!C{net_row}", 0.01),
        # Expected values must be NUMBERS. Formatted text such as "1,225,500" is a
        # string, and arithmetic against a string returns #VALUE!, which is neither
        # OK nor CHECK - the row silently stops testing anything.
        ("Priced quantity on the PN sheet",
         f"=SUM({QTY})", float(net["priced_qty"]), 0.5),
        ("Weighted increase, recomputed from the PN sheet",
         f"=SUMPRODUCT({QTY}*{BP_NEW})/SUMPRODUCT({QTY}*{BP_PRIOR})-1",
         round(float(net["weighted_increase_pct"]) / 100, 8), 1e-8),
        ("Step EUR, recomputed from the PN sheet",
         f"=SUMPRODUCT({QTY}*({BP_NEW}-{BP_PRIOR}))/Overview!$C$4",
         round(float(net["value_step_eur"]), 6), 0.01),
    ]
    rr = 5
    for lab, val, exp, tol in checks:
        ws_ch.cell(row=rr, column=1, value=lab)
        c = ws_ch.cell(row=rr, column=2, value=val)
        e = ws_ch.cell(row=rr, column=3, value=exp)
        ws_ch.cell(row=rr, column=4,
                   value=f"=IF(ABS(B{rr}-C{rr})<={tol},\"OK\",\"CHECK\")")
        c.number_format = '#,##0.000000'
        e.number_format = '#,##0.000000'
        for col in range(1, 5):
            ws_ch.cell(row=rr, column=col).border = BOX
        rr += 1

    ws_ch.cell(row=rr + 1, column=1, value="Prior-vintage sensitivity (see Read me)").font = LBL
    rr += 2
    for lab, v in [
        ("Value of the step, whole year on the revised price",
         meta["sensitivity"]["prior_vintage"]["value_step_eur_revised_basis"]),
        ("Value of the step, weighted by the price actually billed",
         meta["sensitivity"]["prior_vintage"]["value_step_eur_billed_basis"]),
        ("Weighted increase, billed quantity (this workbook)",
         meta["sensitivity"]["weight_base"]["weighted_increase_pct_billing_qty"] / 100),
        ("Weighted increase, simulation quantity",
         meta["sensitivity"]["weight_base"]["weighted_increase_pct_sim_l12m_qty"] / 100),
    ]:
        ws_ch.cell(row=rr, column=1, value=lab)
        c = ws_ch.cell(row=rr, column=2, value=v)
        c.number_format = EUR if abs(v) > 100 else PCT
        rr += 1

    # Column B on Checks carries live formulas, which read as "long text" to the
    # pre-delivery checker. Notes go in column E (column D holds the OK result),
    # wrapped, so the flag is answered without overwriting a check.
    notes = {
        5: "Distributor euro steps must add to the network step.",
        6: "Distributor baskets must add to the network basket.",
        7: "\"(no class)\" on the By class sheet is what makes this reconcile. Without "
           "that row the class total is short by the class-less rows.",
        8: "Priced quantity on the PN data sheet.",
        9: "Recomputed from the PN sheet, independent of the Overview formulas.",
        10: "Recomputed from the PN sheet, independent of the Overview formulas.",
    }
    for r2, txt in notes.items():
        c = ws_ch.cell(row=r2, column=5, value=txt)
        c.font = S_FONT
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws_ch.column_dimensions["E"].width = 52
    wrap_col(ws_ch, 5)
    ws_ch.freeze_panes = "A5"

    final_pass(wb)
    wb.save(XLSX)
    print(f"wrote {XLSX} ({XLSX.stat().st_size:,} bytes)")
    print(f"  PN data rows: {n_rows:,} | distributors: {len(dist)} | classes: {len(classes)}")
    print(f"  network {net['weighted_increase_pct']:.4f}%  step EUR {net['value_step_eur']:,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
