"""Finalise the GPS workbook for sending: clean wording, one model, add 'UIO V19' and 'UIO V20' sheets.

Usage: python -I finalize.py <builder output.xlsx> <uio_by_market_type_year.csv> <UIO_V20_CHANGELOG.csv> <out.xlsx>
"""
import csv
import re
import sys

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import column_index_from_string as CI, get_column_letter as L

SRC, UIO_CSV, V20_CSV, OUT = sys.argv[1:5]
wb = openpyxl.load_workbook(SRC)

NAVY = PatternFill("solid", fgColor="1F3864")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
PALE = PatternFill("solid", fgColor="F2F2F2")
H = Font(bold=True, color="FFFFFF")
B = Font(bold=True)
BLUE = Font(color="0000FF")
NOTE = Font(italic=True, color="595959", size=9)
WRAP = Alignment(wrap_text=True, vertical="top")
NUM = "#,##0"
EUR = "#,##0"
PCT = "0.0%"

LCV = ["IUK", "UMI", "NORWAY", "SWEDEN", "HUNGARY", "FINLAND", "ROMANIA", "DENMARK", "ICELAND"]
MIX = ["GERMANY", "BELGIUM", "PORTUGAL", "IRELAND", "GREECE", "CYPRUS", "MALTA"]
TABS = LCV + MIX
D, D2, IN, CK, W = wb["Dashboard"], wb["Dashboard (2)"], wb["Inputs"], wb["Checks"], wb["Waterfall VP"]

# ===================================================================== 1. wording
TAB_REWRITE = {
    "A2": ("ISZE to distributor target is set here. Blue = input. FY2028-FY2031 in columns F:I. The dealer block at the bottom "
           "uses the IML method (ISZE stretch / (1 - distributor margin)) and is an amount only, never a share."),
}
for t in TABS:
    ws = wb[t]
    mixed = t in MIX
    ws["A2"] = TAB_REWRITE["A2"]
    ws["I6"] = None; ws["J6"] = None   # exchange-rate cell no longer used by any formula
    src_row = "A14" if mixed else "A11"
    ws[src_row] = ("Source: UIO V19. Fiscal year = calendar year + 1 (FY2027 uses the fleet of calendar 2026). "
                   "Compare with the UIO V20 spec on sheet 'UIO V20'.")
    ws["A26" if not mixed else "A32"] = "Source: ISZE billing to the distributor, GPS basis, lubricants included. FY2027 = budget reviewed April 2026."
    if not mixed:
        ws["A13"] = "Parts spend per vehicle (EUR)"
        ws["A14"] = "ISZE net EUR per pick-up"
        ws["A15"] = ("Pick-up rate EUR 250 per vehicle (FY2026, ISZE net), +5% in FY2027 = EUR 262.50, then + yearly price input "
                     "(Dashboard (2) T1). Replaces the earlier EUR 219.56.")
    else:
        ws["A17"] = "Light truck (LD) rate"; ws["A18"] = "Medium truck (MD) rate"; ws["A19"] = "F-Series rate"
        ws["A20"] = "Pick-up (D-Max) rate, EUR 250 base"
        ws["A21"] = ("Truck rates 739 / 887 and pick-up rate EUR 250 per vehicle (FY2026, ISZE net), +5% in FY2027, "
                     "then + yearly price input. All rates sit on the Inputs sheet.")
    hdr, act, mar, stc, note = (34, 36, 37, 38, 40) if mixed else (28, 30, 31, 32, 34)
    ws[f"A{hdr}"] = f"{t} to dealer level (distributor margin on the Inputs sheet... see B{mar})"
    ws[f"A{hdr}"] = f"{t} to dealer level"
    ws[f"A{act}"] = "Sales to dealers (actual, distributor KPI June 2026)"
    ws[f"A{mar}"] = "Distributor margin %"
    ws[f"A{stc}"] = "Stretch at dealer level (= ISZE stretch / (1 - margin))"
    ws[f"A{note}"] = ("Dealer level: the ISZE stretch is converted to dealer prices by dividing by (1 - 35% distributor margin). "
                      "FY2027 amount = FY2026 sales to dealers + that stretch. Amount only, never a share: the distributors' "
                      "reported sales to dealers run 2.2 to 3.7 times ISZE billing.")
    gap = 43 if mixed else 37
    ws[f"A{gap}"] = "Notes"
    if mixed:
        ws["A44"] = ("1. Truck rates 739 / 887 and pick-up rate EUR 250 per vehicle (FY2026, ISZE net), +5% in FY2027, "
                     "then + yearly price input.")
    else:
        ws["A38"] = "1. Pick-up rate EUR 250 per vehicle (FY2026, ISZE net), +5% in FY2027 = EUR 262.50. Replaces the earlier EUR 219.56."
for t, cell in (("NORWAY", "A39"), ("ROMANIA", "A39"), ("GERMANY", "A45"), ("GREECE", "A45")):
    wb[t][cell] = None
wb["UMI"]["A39"] = "2. UMI reports no sales to dealers, so the dealer target shows 'no KPI data'."
wb["FINLAND"]["A39"] = ("2. GPS share is above 100% on budget (104.9%); the stretch applies as for every distributor. "
                        "Discuss the amount with the distributor, not the %.")
wb["IRELAND"]["A45"] = ("2. GPS 98.4% on budget, 100.2% after stretch. Ireland's fleet is national registration data, so Ireland "
                        "buys more than the average spend per vehicle. Discuss the amount, not the %.")
wb["BELGIUM"]["A45"] = ("2. Isuzu Benelux also serves the Netherlands, Poland and Luxembourg; only Belgian vehicles are counted, "
                        "so the GPS share reads high.")

# Dashboards
D["A2"] = "ISZE to distributor level. Stretch inputs on Dashboard (2) row 1. Every number on this sheet is live."
D2["A2"] = D["A2"].value
D["A3"] = "ISZE to distributor (billing and GPS %)"
D["M3"] = "ISZE billing (reference)"
D["P3"] = "Distributor sales to dealers (distributor KPI)"
D["P4"] = "Sales to dealers FY25 (EUR)"; D["Q4"] = "Sales to dealers FY26 (EUR)"
D["V4"] = "Data coverage"
for r in range(4, 24):                      # earlier July dealer-target method: not part of this model
    for c in ("R", "S", "T", "U", "W"):
        D[f"{c}{r}"] = None
for r in range(5, 23):
    v = D[f"V{r}"].value
    if isinstance(v, str):
        v = (v.replace("KPI DB→DLR", "distributor KPI").replace("DB→DLR", "sales to dealers")
              .replace(" (see S2D Note)", "").replace("S2D", "sales to dealers"))
        D[f"V{r}"] = v
for r in (5, 6):
    D[f"P{r}"] = "Not used (ITUK / UTI as presented)"
D["J5"] = "Max spend on IML data (2026 vehicles, +5%); target as presented in July"
D["J6"] = D["J5"].value
D2["J6"] = D["J5"].value; D2["J10"] = D["J5"].value
D2["V1"] = ("Blue / yellow = input. Q1 = NO: the same stretch for every distributor. "
            "Q1 = YES: stretch capped so no GPS share passes 100%.")
WATCH = [
    "• Dealer level (販社): amounts only. The distributors' reported sales to dealers run 2.2 to 3.7 times ISZE billing, so a share "
    "would read above 100% for five distributors. FY2027 dealer target = FY2026 sales to dealers + ISZE stretch / 0.65; "
    "FY2028-FY2031 move with the ISZE target.",
    "• ITUK and UTI: targets and stretch as presented in July; maximum spend on IML data (2026 vehicles, +5%).",
    "• The same stretch for every distributor. Finland (104.9% on budget) and Ireland (100.2% after stretch) read above 100%: "
    "quote the amount, not the %. Ireland's fleet is national registration data.",
    "• Belgium: Isuzu Benelux also serves NL, PL and LU; only Belgian vehicles are counted.",
    "• Fleet: UIO V19 for all years. Sheets 'UIO V19' and 'UIO V20' explain the difference with the UIO V20 spec and its effect on FY2028-FY2031.",
    "• Blue numbers are inputs. Every other number is a formula; constants sit on the Inputs sheet or the distributor tabs.",
]
for i in range(6):
    D[f"A{30 + i}"] = WATCH[i]
    D2[f"A{51 + i}"] = WATCH[i]
D2["A57"] = None
W["U13"] = "-> ITUK  (as presented in July)"
W["U14"] = "-> UTI  (as presented in July)"
W["U10"] = "The remaining stretch is negative because the GPS stretch is larger than the gap: that amount is the surplus above the plan."
wb["Waterfall VP (original)"]["A1"] = "Original FY2027 plan waterfall (reference, unchanged)"
wb["Waterfall VP (original)"]["A2"] = "Reference copy of the original plan waterfall. Nothing added, nothing changed."

# Inputs
IN["C4"] = "pick-up rate per vehicle"
IN["C5"] = "truck rates, unchanged"
IN["A16"] = "GBP to EUR (as in the ITUK row)"
IN["A18"] = "Distributor margin (dealer level = ISZE / (1 - margin))"
IN["A25"] = "Fleet for ITUK and UTI (UIO V19)"
IN["A32"] = ("Other inputs: fleet and FY2025 / FY2026 billing on each distributor tab, stretch / cap / price on Dashboard (2) "
             "row 1-2, ITUK and UTI FY2027 figures as presented in July.")
IN["C36"] = "Default NO: the same stretch for every distributor; above 100% we quote the amount, not the %."
IN["A24"] = "Fleet year used (fiscal year = calendar year + 1)"
IN["A40"] = "UIO V19: share of the fleet leaving the road each year from 2026 (explanation on sheet 'UIO V19')"
IN["B40"] = 0.03; IN["B40"].number_format = "0.0%"; IN["B40"].font = BLUE; IN["B40"].fill = INPUT_FILL

# Checks
CK["B12"] = "ITUK max spend: Dashboard = Dashboard (2) (IML data)"
CK["B13"] = "UTI max spend: Dashboard = Dashboard (2) (IML data)"
for r in range(5, CK.max_row + 1):
    v = CK[f"B{r}"].value
    if isinstance(v, str) and "Masumi-san's" in v:
        CK[f"B{r}"] = "ITUK and UTI maximum spend use IML data on both dashboards (2026 vehicles, +5%); targets as presented in July."
    if isinstance(v, str) and "Not verifiable" in v:
        CK[f"B{r}"] = None

# Method sheet: rewritten in full
M = wb["Method"]
for row in M.iter_rows():
    for c in row:
        c.value = None
M.column_dimensions["A"].width = 150
method = [
    ("Method and assumptions", "title"),
    ("", None),
    ("1. Parts spend per vehicle (ISZE net, FY2026 base)", "h"),
    ("Pick-up (D-Max) EUR 250. Light truck (LD) EUR 739. Medium truck and F-Series EUR 887. FY2027 +5%, FY2028 to FY2031 +3% a year.", None),
    ("The pick-up rate replaces the earlier EUR 219.56.", None),
    ("", None),
    ("2. Vehicles in use", "h"),
    ("UIO V19, detail rows per distributor and segment. Fiscal year = calendar year + 1: FY2027 uses the fleet of calendar 2026, FY2031 the fleet of calendar 2030.", None),
    ("Sheets 'UIO V19' and 'UIO V20' explain the forecast after 2025 and show the effect of the UIO V20 spec.", None),
    ("", None),
    ("3. Maximum spend and GPS", "h"),
    ("Maximum spend = vehicles in use x parts spend per vehicle. GPS % = ISZE billing (FY2027: budget) / maximum spend.", None),
    ("", None),
    ("4. FY2027 extended target", "h"),
    ("Stretch = 1.8% of the maximum spend, the same for every distributor. Extended target = FY2027 budget + stretch.", None),
    ("Total stretch EUR 1,239,483 against the EUR 952,037 the plan waterfall needs: EUR 287,446 above the plan.", None),
    ("ITUK and UTI: targets and stretch as presented in July; maximum spend on IML data (2026 vehicles, +5%).", None),
    ("Finland and Ireland read above 100%: we discuss the amount, not the %. Optional cap: Dashboard (2) Q1 = YES.", None),
    ("", None),
    ("5. Outlook FY2028 to FY2031", "h"),
    ("GPS share + 1.0 point a year from the FY2027 level (input Dashboard (2) N2). Target = share x maximum spend of that year.", None),
    ("FY2027 stays at 1.8%: at 1.0% the stretch would not cover the EUR 952,037.", None),
    ("Customers outside the 18 (CIS, MIDI, KIMA, IMG) are held flat at their FY2027 budget, EUR 2.06M.", None),
    ("Network plan: FY2027 EUR 35.28M, FY2028 37.53M, FY2029 41.53M, FY2030 46.39M, FY2031 52.10M.", None),
    ("", None),
    ("6. Dealer level (販社)", "h"),
    ("Dealer spend per vehicle as in the ITUK row: GBP 400 / 1,000 / 1,200 x 1.12 = EUR 448 (pick-up), 1,120 (light truck), 1,344 (medium truck, F-Series).", None),
    ("FY2026 actual = distributor KPI sales to dealers. FY2027 target = FY2026 + ISZE stretch / (1 - 35% distributor margin). FY2028 to FY2031 move with the ISZE target.", None),
    ("Amounts only: reported sales to dealers run 2.2 to 3.7 times ISZE billing, so a share would read above 100% for several distributors.", None),
    ("", None),
    ("7. Inputs and checks", "h"),
    ("Every rate, price step, margin and plan figure sits on the Inputs sheet. The Checks sheet confirms that totals agree across all sheets (cell B2 must read ALL OK).", None),
    ("", None),
    ("Prepared October 2026.", "note"),
]
for i, (txt, kind) in enumerate(method, start=1):
    M[f"A{i}"] = txt or None
    if kind == "title":
        M[f"A{i}"].font = Font(bold=True, size=14)
    elif kind == "h":
        M[f"A{i}"].font = B
    elif kind == "note":
        M[f"A{i}"].font = NOTE

# ===================================================================== 2. UIO V19 / UIO V20 sheets
v20 = {}
for r in csv.DictReader(open(V20_CSV, encoding="utf-8-sig")):
    v20[(r["country"], r["model_type"], int(r["year"]))] = float(r["new_value_v20"])   # last pass wins
COUNTRY = {"IUK": "U KING", "UMI": "ISRAEL", "NORWAY": "NORWAY", "SWEDEN": "SWEDEN", "HUNGARY": "HUNGARY", "FINLAND": "FINLAND",
           "ROMANIA": "ROMANIA", "DENMARK": "DENMARK", "ICELAND": "ICELAND", "GERMANY": "GERMANY", "BELGIUM": "BELGIUM",
           "PORTUGAL": "PORTUGL", "IRELAND": "IRELAND", "GREECE": "GREECE", "CYPRUS": "CYPRUS", "MALTA": "MALTA"}
uio = {}
for r in csv.DictReader(open(UIO_CSV, encoding="utf-8-sig")):
    if 2025 <= int(r["year"]) <= 2030:
        mk = None if r["distributor_code"] != "BELGIUM" else r["market"]
        if r["distributor_code"] == "BELGIUM" and mk != "BELGIUM":
            continue
        k = (r["distributor_code"], r["model_type"], int(r["year"]))
        uio[k] = uio.get(k, 0) + float(r["uio_units"] or 0)

SEGNAME = {"LCV": "Pick-up (D-Max)", "LD": "Light truck", "MD": "Medium truck", "F-Series": "F-Series"}
RATE = {"LCV": "Inputs!$B$4", "LD": "Inputs!$B$5", "MD": "Inputs!$B$6", "F-Series": "Inputs!$B$7"}
MIXROW = {"LD": 9, "MD": 10, "F-Series": 11, "LCV": 12}
YEARS = list(range(2026, 2032))           # fiscal years
CYC = {fy: L(CI("C") + i) for i, fy in enumerate(YEARS)}   # C..H = FY26..FY31 (CY2025..CY2030)
TABCOL = {2026: "D", 2027: "E", 2028: "F", 2029: "G", 2030: "H", 2031: "I"}
INCOL = {2026: "C", 2027: "D", 2028: "E", 2029: "F", 2030: "G", 2031: "H"}
# segment rows: (distributor, segment, V19 formula builder)
segs = [("ITUK", "Light truck (N35 + N75)", lambda fy: f"=Inputs!{INCOL[fy]}26", "ITUK"),
        ("ITUK", "F-Series", lambda fy: f"=Inputs!{INCOL[fy]}27", "ITUK"),
        ("UTI", "Light truck", lambda fy: f"=Inputs!{INCOL[fy]}29", "UTI"),
        ("UTI", "Medium truck", lambda fy: f"=Inputs!{INCOL[fy]}30", "UTI")]
for t in LCV:
    segs.append((t, SEGNAME["LCV"], (lambda t: lambda fy: f"={t}!{TABCOL[fy]}9")(t), ("LCV", t)))
for t in MIX:
    for m in ("LD", "MD", "F-Series", "LCV"):
        if any(uio.get((t, m, y), 0) for y in range(2025, 2031)):
            segs.append((t, SEGNAME[m], (lambda t, r: lambda fy: f"={t}!{TABCOL[fy]}{r}")(t, MIXROW[m]), (m, t)))

ROW2 = {"ITUK": 9, "UTI": 10, "IUK": 11, "UMI": 12, "NORWAY": 13, "SWEDEN": 14, "HUNGARY": 15, "FINLAND": 16, "ROMANIA": 17,
        "DENMARK": 18, "ICELAND": 19, "GERMANY": 23, "BELGIUM": 26, "PORTUGAL": 30, "IRELAND": 34, "GREECE": 37, "CYPRUS": 40, "MALTA": 43}
BASE = {2026: "K", 2027: "U", 2028: "AE", 2029: "AO", 2030: "AY", 2031: "BI"}
ORDER = ["ITUK", "UTI"] + TABS


def d2(fy, off, r):
    return f"'Dashboard (2)'!{L(CI(BASE[fy]) + off)}{r}"


def header(ws, row, first, cols):
    ws.cell(row, 1, first)
    for j, h in enumerate(cols):
        ws.cell(row, 2 + j, h)
    for j in range(len(cols) + 1):
        c = ws.cell(row, 1 + j); c.font = H; c.fill = NAVY; c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    ws.row_dimensions[row].height = 30


def text_block(ws, start, lines):
    for i, (t, bold) in enumerate(lines):
        ws.merge_cells(start_row=start + i, start_column=1, end_row=start + i, end_column=10)
        c = ws.cell(start + i, 1, t); c.alignment = WRAP
        c.font = Font(bold=True, size=11) if bold else Font(size=11)
        ws.row_dimensions[start + i].height = 31 if len(t) > 110 else 16
    return start + len(lines)


YH = [f"FY{fy % 100} (CY{fy - 1})" for fy in YEARS]


def build(version):
    ws = wb.create_sheet(f"UIO {version}", 3 if version == "V19" else 4)
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 24
    for c in "CDEFGHIJ":
        ws.column_dimensions[c].width = 14
    ws["A1"] = ("UIO V19: vehicles in use in this model" if version == "V19"
                else "UIO V20 spec: the same fleet with the age curve also applied after 2025")
    ws["A1"].font = Font(bold=True, size=14)
    if version == "V19":
        lines = [
            ("What this sheet shows", True),
            ("The vehicles in use per distributor and segment that every other sheet in this file uses. "
             "Fiscal year = calendar year + 1: FY2027 uses the fleet of calendar 2026, FY2031 the fleet of calendar 2030.", False),
            ("How UIO V19 builds the fleet", True),
            ("Up to 2025: registrations of each year, with an age curve for how many vehicles are still on the road. "
             "On that curve a pick-up stays on the road about 8 years on average and a truck about 10 years.", False),
            ("From 2026: the forecast of new pick-up and truck sales is added each year, and only 3% of the fleet leaves the road "
             "each year. 3% a year means a vehicle stays on the road about 33 years, so the fleet keeps growing.", False),
            ("Result: the fleet of these 18 distributors grows about 26% from FY2026 to FY2031, and the parts potential grows with it.", False),
        ]
    else:
        lines = [
            ("What is different in the UIO V20 spec", True),
            ("Everything up to 2025 is the same as UIO V19, and the forecast of new pick-up and truck sales is the same. "
             "Only one thing changes: from 2026 vehicles leave the road on the same age curve as before 2026 "
             "(pick-up about 8 years, truck about 10 years) instead of 3% a year.", False),
            ("Effect: each year about 10,000 new pick-ups are added for these distributors, while about 13,000 to 15,000 older pick-ups "
             "leave the road. The pick-up fleet therefore goes down instead of up.", False),
            ("Medium trucks that UIO V19 shows from 2026 for Ireland, Portugal, Greece and Cyprus are planned vehicles, "
             "not registered vehicles; the UIO V20 spec leaves them out. ITUK and UTI are the same in both versions.", False),
            ("Our reading: UIO V19 keeps vehicles too long (about 33 years); the UIO V20 curve takes pick-ups off the road early "
             "(almost all gone by year 12 to 13). The real fleet is most likely between the two. The UIO V20 spec is not yet approved, so this "
             "file uses UIO V19; this sheet shows what changes if UIO V20 is adopted.", False),
            ("Targets on this sheet: FY2027 stays the same amount (budget + stretch). From FY2028 the same rule as the model: "
             "GPS share + the yearly stretch, applied to the smaller UIO V20 potential.", False),
        ]
    r = text_block(ws, 3, lines) + 1

    # ---- fleet table
    ws.cell(r, 1, f"Vehicles in use, {('UIO V19' if version == 'V19' else 'UIO V20 spec')}").font = B
    r += 1
    header(ws, r, "Distributor", ["Segment"] + YH + ["Change FY26 to FY31"])
    r += 1
    first = r
    fleet_cell = {}
    for dist, seg, f19, key in segs:
        ws.cell(r, 1, dist); ws.cell(r, 2, seg)
        for fy in YEARS:
            c = ws[f"{CYC[fy]}{r}"]
            if version == "V19" or fy == 2026 or key in ("ITUK", "UTI"):
                c.value = f"='UIO V19'!{CYC[fy]}{r}" if version == "V20" else f19(fy)
            else:
                m, t = key
                k = (COUNTRY[t], m, fy - 1)
                if k in v20:
                    c.value = int(round(v20[k])); c.font = BLUE; c.fill = INPUT_FILL
                else:
                    c.value = f"='UIO V19'!{CYC[fy]}{r}"
            c.number_format = NUM
        ws[f"I{r}"] = f'=IF(C{r}=0,"",H{r}/C{r}-1)'; ws[f"I{r}"].number_format = PCT
        fleet_cell[(dist, seg)] = r
        r += 1
    last = r - 1
    ws.cell(r, 1, "Total").font = B
    for fy in YEARS:
        c = ws[f"{CYC[fy]}{r}"]; c.value = f"=SUM({CYC[fy]}{first}:{CYC[fy]}{last})"; c.number_format = NUM; c.font = B
    ws[f"I{r}"] = f"=H{r}/C{r}-1"; ws[f"I{r}"].number_format = PCT; ws[f"I{r}"].font = B
    tot_row = r
    r += 1
    ws.cell(r, 1, "of which pick-ups")
    for fy in YEARS:
        c = ws[f"{CYC[fy]}{r}"]; c.value = f'=SUMIF($B${first}:$B${last},"{SEGNAME["LCV"]}",{CYC[fy]}{first}:{CYC[fy]}{last})'; c.number_format = NUM
    van_row = r
    r += 1
    ws.cell(r, 1, "of which trucks")
    for fy in YEARS:
        c = ws[f"{CYC[fy]}{r}"]; c.value = f"={CYC[fy]}{tot_row}-{CYC[fy]}{van_row}"; c.number_format = NUM
    r += 2
    if version == "V19":
        ws.cell(r, 1, "New pick-ups and pick-ups leaving the road per year (16 distributors and UMI, UIO V19)").font = B
        r += 1
        header(ws, r, "", [""] + YH + [""])
        r += 1
        ws.cell(r, 1, "Pick-ups in use"); van_ex = r
        for fy in YEARS:
            ws[f"{CYC[fy]}{r}"] = f"={CYC[fy]}{van_row}"; ws[f"{CYC[fy]}{r}"].number_format = NUM
        r += 1
        ws.cell(r, 1, "Pick-ups leaving the road (3% a year)")
        for fy in YEARS[1:]:
            p = L(CI(CYC[fy]) - 1)
            ws[f"{CYC[fy]}{r}"] = f"={p}{van_ex}*Inputs!$B$40"; ws[f"{CYC[fy]}{r}"].number_format = NUM
        leave = r
        r += 1
        ws.cell(r, 1, "New pick-ups in the forecast")
        for fy in YEARS[1:]:
            p = L(CI(CYC[fy]) - 1)
            ws[f"{CYC[fy]}{r}"] = f"={CYC[fy]}{van_ex}-{p}{van_ex}+{CYC[fy]}{leave}"; ws[f"{CYC[fy]}{r}"].number_format = NUM
        ws.cell(r + 1, 1, "New pick-ups = change in pick-ups in use + pick-ups leaving the road. The UIO V20 spec uses the same new pick-ups.").font = NOTE
        r += 3
    else:
        ws.cell(r, 1, "Difference with UIO V19").font = B
        r += 1
        header(ws, r, "", [""] + YH + [""])
        r += 1
        for lab, fn, fmt in (("Vehicles UIO V20 - UIO V19", lambda c: f"={c}{tot_row}-'UIO V19'!{c}{tot_row}", NUM),
                             ("in %", lambda c: f"={c}{tot_row}/'UIO V19'!{c}{tot_row}-1", PCT)):
            ws.cell(r, 1, lab)
            for fy in YEARS:
                ws[f"{CYC[fy]}{r}"] = fn(CYC[fy]); ws[f"{CYC[fy]}{r}"].number_format = fmt
            r += 1
        r += 1

    # ---- price index
    ws.cell(r, 1, "Price index (FY2026 = 1)").font = B
    pi = r
    for fy in YEARS:
        c = ws[f"{CYC[fy]}{r}"]
        if fy == 2026:
            c.value = 1
        elif fy == 2027:
            c.value = "=C{0}*(1+Inputs!$B$9)".format(r)
        else:
            c.value = f"={L(CI(CYC[fy]) - 1)}{r}*(1+'Dashboard (2)'!$T$1)"
        c.number_format = "0.0000"
    r += 2

    # ---- potential, share, target per distributor
    ws.cell(r, 1, "Parts potential (ISZE maximum spend, EUR)").font = B
    r += 1
    header(ws, r, "Distributor", [""] + YH + [""])
    r += 1
    pot = {}
    for dist in ORDER:
        ws.cell(r, 1, dist)
        for fy in YEARS:
            c = ws[f"{CYC[fy]}{r}"]
            if version == "V19" or dist in ("ITUK", "UTI"):
                c.value = f"={d2(fy, 3, ROW2[dist])}"
            else:
                rows = [fleet_cell[k] for k in fleet_cell if k[0] == dist]
                terms = []
                for rr in rows:
                    seg = ws.cell(rr, 2).value
                    m = [k for k, v in SEGNAME.items() if v == seg][0]
                    terms.append(f"{CYC[fy]}{rr}*{RATE[m]}")
                c.value = f"=({'+'.join(terms)})*{CYC[fy]}${pi}"
            c.number_format = EUR
        pot[dist] = r
        r += 1
    pot_tot = r
    ws.cell(r, 1, "Total").font = B
    for fy in YEARS:
        c = ws[f"{CYC[fy]}{r}"]; c.value = f"=SUM({CYC[fy]}{pot[ORDER[0]]}:{CYC[fy]}{r - 1})"; c.number_format = EUR; c.font = B
    r += 2

    ws.cell(r, 1, "GPS share (target)").font = B
    r += 1
    header(ws, r, "Distributor", [""] + YH + [""])
    r += 1
    share = {}
    for dist in ORDER:
        ws.cell(r, 1, dist)
        for fy in YEARS[1:]:
            c = ws[f"{CYC[fy]}{r}"]
            if version == "V19":
                c.value = f"={d2(fy, 4, ROW2[dist])}"
            elif fy == 2027:
                c.value = f"=IFERROR({d2(2027, 5, ROW2[dist])}/{CYC[fy]}{pot[dist]},0)"
            else:
                p = f"{L(CI(CYC[fy]) - 1)}{r}"
                c.value = f"=IF({p}>=Inputs!$B$38,{p},MIN({p}+'Dashboard (2)'!$N$2,Inputs!$B$38))"
            c.number_format = PCT
        share[dist] = r
        r += 1
    r += 1
    ws.cell(r, 1, "ISZE parts sales target (EUR)").font = B
    r += 1
    header(ws, r, "Distributor", [""] + YH + [""])
    r += 1
    tgt = {}
    for dist in ORDER:
        ws.cell(r, 1, dist)
        for fy in YEARS[1:]:
            c = ws[f"{CYC[fy]}{r}"]
            c.value = (f"={d2(fy, 5, ROW2[dist])}" if version == "V19"
                       else f"={CYC[fy]}{share[dist]}*{CYC[fy]}{pot[dist]}")
            c.number_format = EUR
        tgt[dist] = r
        r += 1
    t18 = r
    rows_out = [("Total 18 distributors", lambda c: f"=SUM({c}{tgt[ORDER[0]]}:{c}{r - 1})"),
                ("Customers outside the 18 (held flat)", lambda c: "=Inputs!$D$23"),
                ("Total ISZE", lambda c: f"={c}{t18}+{c}{t18 + 1}"),
                ("Network plan", lambda c: f"=Inputs!{INCOL[[k for k, v in CYC.items() if v == c][0]]}21"),
                ("Above (+) / below (-) plan", lambda c: f"={c}{t18 + 2}-{c}{t18 + 3}"),
                ("GPS share, 18 distributors", lambda c: f"={c}{t18}/{c}{pot_tot}")]
    for i, (lab, fn) in enumerate(rows_out):
        ws.cell(t18 + i, 1, lab).font = B if i in (0, 2, 4) else Font()
        for fy in YEARS[1:]:
            c = ws[f"{CYC[fy]}{t18 + i}"]; c.value = fn(CYC[fy])
            c.number_format = PCT if i == 5 else EUR
            if i in (0, 2, 4):
                c.font = B
    ws.freeze_panes = "C1"
    return {"tot": tot_row, "pot_tot": pot_tot, "t18": t18}


r19 = build("V19")
r20 = build("V20")

# side-by-side summary on the V20 sheet
ws = wb["UIO V20"]
r = ws.max_row + 2
ws.cell(r, 1, "Summary: UIO V19 (this model) against the UIO V20 spec").font = Font(bold=True, size=12)
r += 1
header(ws, r, "", [""] + YH + [""])
r += 1
summary = [
    ("Vehicles, UIO V19", "'UIO V19'!{c}%d" % r19["tot"], NUM),
    ("Vehicles, UIO V20", "{c}%d" % r20["tot"], NUM),
    ("Potential, UIO V19", "'UIO V19'!{c}%d" % r19["pot_tot"], EUR),
    ("Potential, UIO V20", "{c}%d" % r20["pot_tot"], EUR),
    ("Total ISZE target, UIO V19", "'UIO V19'!{c}%d" % (r19["t18"] + 2), EUR),
    ("Total ISZE target, UIO V20", "{c}%d" % (r20["t18"] + 2), EUR),
    ("Network plan", "Inputs!{p}21", EUR),
    ("Against plan, UIO V19", "'UIO V19'!{c}%d" % (r19["t18"] + 4), EUR),
    ("Against plan, UIO V20", "{c}%d" % (r20["t18"] + 4), EUR),
]
for lab, f, fmt in summary:
    ws.cell(r, 1, lab).font = B if "Against" in lab else Font()
    for fy in YEARS[1:]:
        c = ws[f"{CYC[fy]}{r}"]
        c.value = "=" + f.format(c=CYC[fy], p=INCOL[fy]); c.number_format = fmt
        if "Against" in lab:
            c.font = B
    r += 1

# extra live checks for the two new sheets
n = 5
while CK[f"F{n}"].value is not None:
    n += 1
extra = [
    ("UIO V19 sheet: total potential FY31 = Dashboard (2) total", f"='UIO V19'!H{r19['pot_tot']}", "='Dashboard (2)'!BL44"),
    ("UIO V19 sheet: total target FY31 = Dashboard (2) total", f"='UIO V19'!H{r19['t18']}", "='Dashboard (2)'!BN44"),
    ("UIO V20 sheet: FY27 target unchanged against the model", f"='UIO V20'!D{r20['t18']}", "='Dashboard (2)'!Z44"),
    ("UIO V20 sheet: ITUK and UTI potential FY31 unchanged", f"='UIO V20'!H{r20['pot_tot'] - 18}+'UIO V20'!H{r20['pot_tot'] - 17}",
     "='Dashboard (2)'!BL9+'Dashboard (2)'!BL10"),
]
# shift the note rows below the new checks
notes = [(rr, CK[f"A{rr}"].value, CK[f"B{rr}"].value, CK[f"C{rr}"].value, CK[f"F{rr}"].value) for rr in range(n, CK.max_row + 1)]
for rr, *_ in notes:
    for c in "ABCDEF":
        CK[f"{c}{rr}"] = None
for i, (lab, a, b) in enumerate(extra):
    rr = n + i
    CK[f"A{rr}"] = rr - 4; CK[f"B{rr}"] = lab; CK[f"C{rr}"] = a; CK[f"D{rr}"] = b
    CK[f"E{rr}"] = f"=C{rr}-D{rr}"; CK[f"F{rr}"] = f'=IF(ABS(E{rr})<1,"OK","CHECK")'
    for c in "CDE":
        CK[f"{c}{rr}"].number_format = "#,##0.00"
base = n + len(extra) + 1
for i, (rr, a, bb, cc, ff) in enumerate([x for x in notes if any(x[1:])]):
    CK[f"A{base + i}"] = a; CK[f"B{base + i}"] = bb; CK[f"C{base + i}"] = cc; CK[f"F{base + i}"] = ff
    CK[f"B{base + i}"].font = NOTE

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT, "V19 rows", r19, "V20 rows", r20)
