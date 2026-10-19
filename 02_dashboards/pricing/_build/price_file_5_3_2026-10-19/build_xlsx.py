"""Build the 4-tab price file at +5.3% for Masumi (19 Oct 2026). Reads result.json + parts.pkl from compute.py."""
import json
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

H = Path(__file__).parent
ISZE = H.parents[3]
import os
OUT = Path(os.environ["OUT_XLSX"]) if os.environ.get("OUT_XLSX") else ISZE / "01_data/01_Pricing/ISZE_Price_Revision_5.3pct_2026-10-19.xlsx"
R = json.loads((H / "result_v2_all_brakes.json").read_text(encoding="utf-8"))
parts = pd.read_pickle(H / "parts_v2_all_brakes.pkl")
F, G, V = R["facts"], R["gap"], R["V"]

NAVY, TERRA, PAPER, YELLOW, GREY = "15233C", "C0552D", "F7F4EE", "FFF2B3", "E6E2DA"
fill = lambda c: PatternFill("solid", fgColor=c)
thin = Side(style="thin", color="C9C3B8")
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
EUR, EUR2, PCT, PCT2, INT = '#,##0', '#,##0.00', '0.0%', '0.00%', '#,##0'
M = lambda x: "EUR %.2fM" % (x / 1e6)
K = lambda x: "EUR %sK" % format(round(x / 1e3), ",")
P1 = lambda x: ("%.1f%%" % (x * 100))
P2 = lambda x: ("%.2f%%" % (x * 100))

wb = Workbook()


def title(ws, text, sub=None):
    ws["A1"] = text; ws["A1"].font = Font(name="Georgia", size=16, bold=True, color=NAVY)
    if sub:
        ws["A2"] = sub; ws["A2"].font = Font(italic=True, color="555555")
    ws.sheet_view.showGridLines = False


def head(ws, r, text):
    ws.cell(r, 1, text).font = Font(name="Georgia", size=12, bold=True, color=TERRA)
    return r + 1


def para(ws, r, text, width_cols=8, height=None, bold=False):
    c = ws.cell(r, 1, text); c.alignment = Alignment(wrap_text=True, vertical="top"); c.font = Font(bold=bold)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=width_cols)
    ws.row_dimensions[r].height = height or max(15, 15 * (len(text) // 120 + 1))
    return r + 1


def table(ws, r, header, rows, fmts, widths=None, merge_to=None, rowh=None):
    for j, h in enumerate(header, 1):
        c = ws.cell(r, j, h); c.font = Font(bold=True, color="FFFFFF"); c.fill = fill(NAVY)
        c.alignment = Alignment(wrap_text=True, vertical="center"); c.border = BOX
    ws.row_dimensions[r].height = 30
    for row in rows:
        r += 1
        for j, v in enumerate(row, 1):
            c = ws.cell(r, j, v); c.border = BOX; c.alignment = Alignment(wrap_text=True, vertical="top")
            if fmts[j - 1]: c.number_format = fmts[j - 1]
        if merge_to:
            ws.merge_cells(start_row=r, start_column=len(header), end_row=r, end_column=merge_to)
        if rowh: ws.row_dimensions[r].height = rowh
    if merge_to:
        ws.merge_cells(start_row=r - len(rows), start_column=len(header), end_row=r - len(rows), end_column=merge_to)
    return r + 2


# ---------------------------------------------------------------- 1 Summary
ws = wb.active; ws.title = "1 Summary"
title(ws, "Parts price revision: proposal at +5.3% weighted",
      "Draft for discussion, 19 October 2026. Nothing has been changed in SAP. All figures are on what distributors bought from July 2025 to June 2026.")
for col, w in zip("ABCDEFGH", [58, 18, 18, 18, 18, 18, 18, 18]): ws.column_dimensions[col].width = w
r = 4
r = head(ws, r, "The answer in short")
AP = "'3 All parts'!"
ws.cell(r, 1, "Billed to distributors in the 12 months, at today's list prices"); ws.cell(r, 2, f"=SUM({AP}AE:AE)").number_format = EUR; r += 1
ws.cell(r, 1, "Extra per year on the same volume after this proposal"); ws.cell(r, 2, f"=SUM({AP}AF:AF)").number_format = EUR; r += 1
ws.cell(r, 1, "Weighted increase (extra divided by billed)"); c = ws.cell(r, 2, "=B6/B5"); c.number_format = PCT2; c.font = Font(bold=True, color=TERRA); r += 1
ws.cell(r, 1, "Part numbers in the file"); ws.cell(r, 2, f"=COUNTA({AP}A:A)-1").number_format = INT; r += 1
for rr in range(5, 9): ws.cell(rr, 2).font = Font(bold=True)
r += 1
r = para(ws, r, (
    f"Each part follows its own base price increase from Japan (IML) or Thailand (IMIT). Because the base price increase weighted over our "
    f"purchases is {P2(G['bp_w'])} and the target is 5.3%, every part is scaled to {F['scale']*100:.1f}% of its own increase. "
    f"A typical part goes up {P1(F['median_move'])}. A part whose base price did not move, or went down, stays at today's price."))
r = para(ws, r, "Five exceptions:")
r = para(ws, r, f"1. Brake pad kits stay at today's price, as decided on 30 September 2026: {F['pad_n']} part numbers, {M(F['pad_b'])} billed.")
r = para(ws, r, f"2. Steering units go up 5.3%, the same as the general increase. The large steering units have no base price increase this year, but they are parts only Isuzu supplies: {F['steer_n']} part numbers, {M(F['steer_b'])} billed.")
r = para(ws, r, (f"3. Brake parts stay at today's price in the eight markets where service parts are held ({', '.join(F['disc_by_db'])}): "
                 f"{M(F['disc_held_b'])} billed there. On PR00 this is a customer condition for those distributors, because PR00 is one list for all of Europe and the UK; "
                 "UMI has its own list, so there the brake prices simply stay. In the other markets brake parts follow their base price."))
r = para(ws, r, f"4. On PR00, parts where our price to the end customer is already more than 60% above the UK online shop KS International stay at today's price: {F['far_n']} part numbers, {M(F['far_b'])} billed. This was switch A8 in the earlier file. The Israel and other own lists follow the base price on these parts.")
r = para(ws, r, "5. The small extra on five parts where KS International sells above our end-customer price (switch A7 in the earlier file) is no longer used. It was worth about EUR 35K and made the file harder to follow.")
r += 1
r = head(ws, r, "Your question of 12 October: the gap between 6.0% and 5.3%")
r = para(ws, r, (
    f"In yen, the base price rises {P2(G['bp_w'])} on what ISZE buys and our list rises 5.3%. On paper that is a difference of {K(G['gap_sales'])} a year. "
    "In euros there is no gap. The yen has weakened from 172.6 to 178.5 per euro, the rate in our pricing set-up for October 2026 to March 2027, "
    f"so in euros our purchase cost rises only {G['cost_up']/G['cost0']*100:.1f}%, while our sales rise 5.3%. Gross profit goes up and the margin goes up. "
    "The rate after March 2027 is not known yet."), height=60)
r = table(ws, r, ["On the same 12-month volume", "At the rate of Apr-Sep 2026 (172.6)", "At the live rate (178.5)"], [
    ["Our purchase cost goes up by", G["cost_up_samefx"], G["cost_up"]],
    ["Our sales go up by (+5.3%)", G["extra"], G["extra"]],
    ["Gross profit, before (EUR)", G["gm0"], G["gm0"]],
    ["Gross profit, after (EUR)", G["gm1_samefx"], G["gm1"]],
    ["Gross margin, before", G["gm0"] / G["base"], G["gm0"] / G["base"]],
    ["Gross margin, after", G["gm1_samefx"] / (G["base"] + G["extra"]), G["gm1"] / (G["base"] + G["extra"])],
], [None, EUR, EUR])
for rr in (r - 3, r - 2):
    for cc in (2, 3): ws.cell(rr, cc).number_format = PCT
r += 1
r = head(ws, r, "What if dealers buy less after the increase")
r = table(ws, r, ["Case", "Dealer reaction", "Extra per year after reaction", "Where the reaction figure comes from"],
          [[x["label"], x["e"], x["x"], x["src"]] for x in R["react"]], [None, '0.00', EUR, None], merge_to=8, rowh=32)
ws.column_dimensions["D"].width = 18
r = para(ws, r, "Dealer reaction = the % change in what dealers buy for every +1% on our price. Central case: a 10% price rise costs about 1.6% of volume. The stress case is a pessimistic bound, not a forecast.")
r += 1
r = head(ws, r, "How to read this file")
for t in [
    "Tab 1 Summary: this page. The four figures at the top add up from tab 3, so they follow any change you make there.",
    "Tab 2 By market and family: the same proposal split by price list, distributor, where the part is made and parts family.",
    "Tab 3 All parts: one row per part number with today's price, the proposed increase and the new price on each price list. "
    "The increase is in a yellow column. If you change it, the new price, the extra euros and tab 1 recalculate.",
]: r = para(ws, r, t)
r += 1
r = head(ws, r, "Words used in this file")
r = table(ws, r, ["Word", "What it means"], [
    ["Base price", "The yen price IML (Japan) or IMIT (Thailand) charges for a part, before the purchase discount. The new base price list came in September 2026."],
    ["Weighted increase", "The increase on each part multiplied by what was bought of it, added up and divided by the total. Big-selling parts count more than small ones."],
    ["PR00", "Our list price for the distributors in Europe and the UK. One price per part for all of them."],
    ["UTI 1799 / UMI 1797", "The two Israel distributors each have their own price list: UTI (trucks) and UMI (D-Max). They are kept apart."],
    ["Armenia and Kazakhstan", "Own price lists. They move by the same percentage on their own current price; no price is shown here."],
    ["End-customer price (reference dealer price)", "Our list price walked up to what a customer pays at the dealer: a projected average distributor margin of 37%, then a dealer margin of 27.5%."],
    ["KS International", "A UK online parts shop. We use it because you can search it by our own Isuzu part number and it shows a public end-customer price. "
     "We checked it in September 2026. Other sources were not usable: Eucon does not say clearly whether a price is trade or retail, other sites only give category averages."],
    ["Switch A8 (earlier file)", "Hold a part at today's price when our end-customer price is more than 1.6 times the KS International price for the same part number. "
     "The thought: the customer already pays far more than at the shop, so a further increase pushes him to the aftermarket. Kept in this file."],
    ["Switch A7 (earlier file)", "Give a small extra increase when KS International sells the same part number above our end-customer price. Dropped in this file."],
    ["Parts family", "The new parts classification of October 2026, in three levels (for example Brakes > Brake Pad > Brake Pad Kit)."],
    ["Brake pad kits held", "Decided 30 September 2026: pad kits keep today's price on every list."],
    ["Eight markets", "The markets where service parts were held in the exercise of 30 September 2026: " + ", ".join(F["service8_dbs"]) + ". Brake parts keep today's price there."],
], [None, None], merge_to=8, rowh=32)
r = para(ws, r, "Sources: billing July 2025 - June 2026 (EUR 32,595,853 on parts with a base price on both lists); new and previous base price lists; "
         "today's list prices from the SAP export of 10 August 2026; KS International prices checked 22 September 2026; dealer reaction measured on the April 2026 change in four markets.")

# ---------------------------------------------------------------- 2 By market and family
t = wb.create_sheet("2 By market and family")
title(t, "The proposal by price list, distributor, origin and parts family", "Values as proposed. Base price change = the yen change on the same parts, weighted the same way.")
for col, w in zip("ABCDE", [40, 18, 18, 18, 18]): t.column_dimensions[col].width = w
hdrs = ["", "Billed 12 months (EUR)", "Base price change", "Proposed increase", "Extra per year (EUR)"]
fm = [None, EUR, PCT, PCT, EUR]
row = lambda x, name: [name, x["b"], x["bpx"] / x["b"], x["x"] / x["b"], x["x"]]
r = 4
for name, key, sortkey in [("By price list", "by_list", None), ("By distributor", "by_db", "b"), ("By where the part is made", "by_src", "b")]:
    r = head(t, r, name)
    data = R[key] if not sortkey else sorted(R[key], key=lambda x: -x[sortkey])
    r = table(t, r, hdrs, [row(x, x["name"]) for x in data], fm)
r = head(t, r, "By parts family (level 1)")
fam = sorted(R["by_l1"], key=lambda x: -x["b"])
r = table(t, r, hdrs, [row(x, x["name"]) for x in fam if x["b"] > 0], fm)
tot = {"b": G["base"], "x": G["extra"], "bpx": sum(x["bpx"] for x in R["by_l1"])}
r = table(t, r, hdrs, [row(tot, "All")], fm)

# ---------------------------------------------------------------- 3 All parts
a = wb.create_sheet("3 All parts")
cols = [("Part number", 13), ("Newer part number in Power BI", 14), ("Description", 28), ("Family level 1", 22), ("Family level 2", 22),
        ("Family level 3", 20), ("Made in", 14), ("Base price before (yen)", 12), ("Base price after (yen)", 12), ("Base price change", 10),
        ("Why this increase", 95),
        ("PR00 billed (EUR)", 12), ("PR00 price today (EUR)", 11), ("PR00 increase", 9), ("PR00 new price (EUR)", 11),
        ("PR00 billed in the 8 markets kept at today's price (EUR)", 16), ("PR00 extra (EUR)", 11),
        ("UTI billed (EUR)", 11), ("UTI price today (EUR)", 11), ("UTI increase", 9), ("UTI new price (EUR)", 11), ("UTI extra (EUR)", 11),
        ("UMI billed (EUR)", 11), ("UMI price today (EUR)", 11), ("UMI increase", 9), ("UMI new price (EUR)", 11), ("UMI extra (EUR)", 11),
        ("Armenia + Kazakhstan billed (EUR)", 12), ("Armenia + Kazakhstan increase", 10), ("Armenia + Kazakhstan extra (EUR)", 11),
        ("Total billed (EUR)", 12), ("Total extra (EUR)", 12), ("Total increase", 9), ("KS International lowest price (EUR)", 12)]
for j, (h, w) in enumerate(cols, 1):
    c = a.cell(1, j, h); c.font = Font(bold=True, color="FFFFFF"); c.fill = fill(NAVY)
    c.alignment = Alignment(wrap_text=True, vertical="center"); a.column_dimensions[get_column_letter(j)].width = w
a.row_dimensions[1].height = 60
YF = fill(YELLOW)
nz = lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else v
CL = get_column_letter
assert CL(31) == "AE" and CL(32) == "AF"
for i, x in enumerate(parts.itertuples(index=False), 2):
    vals = [x.pn, x.newest or None, x.desc, x.l1, x.l2, x.l3, x.src, nz(x.bp0), nz(x.bp1), x.bp_step, x.reason]
    for j, v in enumerate(vals, 1): a.cell(i, j, v)
    # PR00: 12 billed, 13 price, 14 increase, 15 new price, 16 held billed, 17 extra
    a.cell(i, 12, round(x.pr00_b, 2)); a.cell(i, 13, nz(x.pr00_p)); a.cell(i, 14, round(x.pr00_m, 6)).fill = YF
    a.cell(i, 15, f'=IF(M{i}="","",ROUND(M{i}*(1+N{i}),2))')
    a.cell(i, 16, round(x.pr00_hb, 2) if x.pr00_hb else None)
    a.cell(i, 17, f"=(L{i}-P{i})*N{i}")
    for c0, nm in ((18, "uti"), (23, "umi")):
        Lc, Pc, Mc = CL(c0), CL(c0 + 1), CL(c0 + 2)
        a.cell(i, c0, round(getattr(x, nm + "_b"), 2)); a.cell(i, c0 + 1, nz(getattr(x, nm + "_p")))
        a.cell(i, c0 + 2, round(getattr(x, nm + "_m"), 6)).fill = YF
        a.cell(i, c0 + 3, f'=IF({Pc}{i}="","",ROUND({Pc}{i}*(1+{Mc}{i}),2))')
        a.cell(i, c0 + 4, f"={Lc}{i}*{Mc}{i}")
    a.cell(i, 28, round(x.oth_b, 2)); a.cell(i, 29, round(x.oth_m, 6)).fill = YF; a.cell(i, 30, f"=AB{i}*AC{i}")
    a.cell(i, 31, f"=L{i}+R{i}+W{i}+AB{i}"); a.cell(i, 32, f"=Q{i}+V{i}+AA{i}+AD{i}"); a.cell(i, 33, f'=IF(AE{i}=0,"",AF{i}/AE{i})')
    a.cell(i, 34, nz(x.ks_eur))
n = len(parts) + 1
fmts = {8: INT, 9: INT, 10: PCT, 12: EUR, 13: EUR2, 14: PCT, 15: EUR2, 16: EUR, 17: EUR, 18: EUR, 19: EUR2, 20: PCT, 21: EUR2, 22: EUR,
        23: EUR, 24: EUR2, 25: PCT, 26: EUR2, 27: EUR, 28: EUR, 29: PCT, 30: EUR, 31: EUR, 32: EUR, 33: PCT, 34: EUR2}
for j, f_ in fmts.items():
    for rr in range(2, n + 1): a.cell(rr, j).number_format = f_
a.freeze_panes = "B2"; a.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{n}"

wb.calculation.fullCalcOnLoad = True
OUT.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
print("saved", OUT, "rows", len(parts))
