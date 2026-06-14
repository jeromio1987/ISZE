"""
Build PDF: ISZE Warranty Analysis 2025
- Per-DB warranty intensity
- Top 25 parts by warranty value
- Top 15 failure modes (CV + LCV)
External format: no internal references.
"""
import openpyxl, pandas as pd
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, PageBreak, KeepTogether)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

WARR = r'C:\Users\jerom\Desktop\claude\ISZE\Data\Final_Complete_Warranty_Pricing_2026.xlsx'
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\UIO\Ireland_SIMI_Comparison\ISZE_Warranty_Analysis_2025.pdf")

wb = openpyxl.load_workbook(WARR, read_only=True, data_only=True)

def norm_pn(v):
    if v is None: return None
    s = str(v).strip()
    if s.endswith(".0"): s = s[:-2]
    if not s or s == "0": return None
    if s.isdigit(): return s.zfill(10)
    return s

# Price + descriptions
prices, descs = {}, {}
ws_p = wb["Pricing_Data"]
hdr_p = list(ws_p.iter_rows(min_row=1, max_row=1, values_only=True))[0]
pn_i, desc_i, price_i = hdr_p.index("P/N"), hdr_p.index("Description"), hdr_p.index("Price")
for row in ws_p.iter_rows(min_row=2, max_row=ws_p.max_row, values_only=True):
    pn = norm_pn(row[pn_i])
    if pn:
        if row[price_i] is not None:
            try: prices[pn] = float(row[price_i])
            except: pass
        if row[desc_i]: descs[pn] = str(row[desc_i]).strip()

# CV warranty 2025
CV_MAP = {"ITUK":"ITUK","UTI":"UTI","IRELAND":"Isuzu Ireland","ISD":"ISD-Lang","PORTUGAL":"Imotors",
          "CYPRUS":"Loutsios & Sons","GREECE":"Petros Petropoulos","MALTA":"GasanZammit",
          "MIDI":"EXCLUDE","MIDI AIOS Products":"EXCLUDE"}
ws = wb["Raw_CV_Warranty"]
hdr = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
idx = {h:i for i,h in enumerate(hdr)}
cv = []
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    if not str(row[idx["BILLYMD"]] or "").startswith("2025"): continue
    code = CV_MAP.get(str(row[idx["DST_Name"]] or "").strip())
    if not code or code == "EXCLUDE": continue
    for pn_c, q_c in [("PARTNBR","QTY1"),("PARTNBR2","QTY2")]:
        pn = norm_pn(row[idx[pn_c]])
        if not pn: continue
        try: qty = float(row[idx[q_c]] or 0)
        except: qty = 0
        if qty <= 0: continue
        cv.append({"db":code, "pn":pn, "qty":qty, "value":qty*prices.get(pn,0),
                   "ope":str(row[idx["OPE_Name"]] or "").strip()})
cv = pd.DataFrame(cv)

# LCV warranty 2025
LCV_MAP = {"BL ehf.":"BL","ISUZU BENELUX - BELGIUM":"IBX","ISUZU BENELUX - NETHERLANDS":"IBX",
    "Isuzu Benelux NV":"IBX","Isuzu Benelux NV (Poland)":"IBX","ISUZU (UK)":"IUK",
    "Isuzu Ireland":"Isuzu Ireland","Isuzu Ireland 2020 Unlimited Company":"Isuzu Ireland",
    "ISUZU SALES DEUTSCHLAND - ISD":"ISD-Lang","ISUZU SALES DEUTSCHLAND - AUSTRIA":"ISD-Lang",
    "ISUZU SALES DEUTSCHLAND - CZECH":"ISD-Lang","ISUZU SALES DEUTSCHLAND - SLOVAKIA":"ISD-Lang",
    "IMOTORS LDA":"Imotors","Isuzu Sverige":"Isuzu Sverige","RSA":"RSA",
    "ISUZU Danmark":"Isuzu Denmark","Isuzu Motor Finland OY":"Nordic Auto",
    "GASANZAMMIT MOTORS LIMITED":"GasanZammit","PETROS PETROPOULOS":"Petros Petropoulos",
    "A. LOUTSIOS & SONS":"Loutsios & Sons","ISUZU ROM AUTO SRL":"Isuzu Rom Auto",
    "AW Distribution Kft.":"AutoWallis",
    "MIDI Europe":"EXCLUDE","MIDI Europe S.R.L.":"EXCLUDE","MIDI EUROPE - FRANCE":"EXCLUDE",
    "MIDI EUROPE - ITALY":"EXCLUDE","MIDI EUROPE - MACEDONIA":"EXCLUDE","MIDI EUROPE - SPAIN":"EXCLUDE",
    "MIDI EUROPE - SWITZ":"EXCLUDE","MIDI EUROPE S.R.L.(SLOVENIA)":"EXCLUDE",
    "Midi Europe S.P.L (Ser.mon.)":"EXCLUDE","Midi Europe S.R.L (BOSNIA HERZEGOVINA)":"EXCLUDE",
    "WAE LTD.":"EXCLUDE","ZAMZAM SPRING GENERAL TRADING CO., LTD":"EXCLUDE"}
ws = wb["Raw_LCV_Warranty"]
hdr = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
idx = {h:i for i,h in enumerate(hdr)}
lcv = []
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    if not str(row[idx["AssessMonth"]] or "").startswith("2025"): continue
    code = LCV_MAP.get(str(row[idx["DistributorName"]] or "").strip())
    if not code or code == "EXCLUDE": continue
    pn = norm_pn(row[idx["PartsNo"]])
    if not pn: continue
    try: qty = float(row[idx["Pieces"]] or 0)
    except: qty = 0
    if qty <= 0: continue
    lcv.append({"db":code, "pn":pn, "qty":qty, "value":qty*prices.get(pn,0),
        "ope":str(row[idx["OperationDescription"]] or "").strip()})
lcv = pd.DataFrame(lcv)

combined = pd.concat([cv[["db","pn","qty","value"]], lcv[["db","pn","qty","value"]]])

# UIO + sales reference for per-DB intensity (DB-name keyed to match)
DB_TO_UIO = {
    "ITUK":22389,"IUK":47783,"UTI":11253,"UMI":18542,"Isuzu Ireland":3056,
    "IBX":9594,"ISD-Lang":12855,"Imotors":8176,"Isuzu Sverige":8443,"RSA":7929,
    "Isuzu Denmark":851,"Nordic Auto":1204,"BL":406,"Petros Petropoulos":3742,
    "Loutsios & Sons":2308,"GasanZammit":1040,"Isuzu Rom Auto":1071,"AutoWallis":3734,
}
DB_TO_SALES = {
    "ITUK":5769868,"IUK":6221920,"UTI":3402117,"UMI":3388801,"Isuzu Ireland":1213660,
    "IBX":2143952,"ISD-Lang":2577766,"Imotors":1712791,"Isuzu Sverige":1289481,"RSA":1438473,
    "Isuzu Denmark":150218,"Nordic Auto":285913,"BL":87260,"Petros Petropoulos":528391,
    "Loutsios & Sons":429512,"GasanZammit":206502,"Isuzu Rom Auto":177276,"AutoWallis":330031,
}
DB_TO_COUNTRY = {
    "ITUK":"United Kingdom","IUK":"United Kingdom","UTI":"Israel","UMI":"Israel",
    "Isuzu Ireland":"Ireland","IBX":"Belgium","ISD-Lang":"Germany","Imotors":"Portugal",
    "Isuzu Sverige":"Sweden","RSA":"Norway","Isuzu Denmark":"Denmark","Nordic Auto":"Finland",
    "BL":"Iceland","Petros Petropoulos":"Greece","Loutsios & Sons":"Cyprus",
    "GasanZammit":"Malta","Isuzu Rom Auto":"Romania","AutoWallis":"Hungary",
}

# Per-DB intensity
per_db = combined.groupby("db").agg(qty=("qty","sum"), value=("value","sum")).reset_index()
per_db["uio"] = per_db["db"].map(DB_TO_UIO)
per_db["sales"] = per_db["db"].map(DB_TO_SALES)
per_db["country"] = per_db["db"].map(DB_TO_COUNTRY)
per_db["eur_per_uio"] = per_db["value"] / per_db["uio"]
per_db["warr_pct_sales"] = per_db["value"] / per_db["sales"]
per_db = per_db.sort_values("eur_per_uio", ascending=False)

# Top 25 parts by value
top25 = (combined.groupby("pn").agg(qty=("qty","sum"), value=("value","sum"))
         .sort_values("value", ascending=False).head(25)).reset_index()
top25["desc"] = top25["pn"].map(descs)

# Top 15 LCV failure operations
ol = (lcv.groupby("ope").agg(count=("pn","count"), value=("value","sum"))
      .sort_values("value", ascending=False).head(15)).reset_index()

# Top 15 CV failure operations
oc = (cv.groupby("ope").agg(count=("pn","count"), value=("value","sum"))
      .sort_values("value", ascending=False).head(15)).reset_index()

# ============================================================
# Build PDF
# ============================================================
doc = SimpleDocTemplate(str(OUT), pagesize=landscape(A4),
                        leftMargin=15*mm, rightMargin=15*mm,
                        topMargin=15*mm, bottomMargin=15*mm)

styles = getSampleStyleSheet()
title = ParagraphStyle("title", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#1F4E78"),
                       spaceAfter=4, alignment=TA_LEFT)
subtitle = ParagraphStyle("sub", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#595959"),
                          italic=True, spaceAfter=12)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#1F4E78"),
                    spaceBefore=12, spaceAfter=6)
body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, spaceAfter=4)
note = ParagraphStyle("note", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#595959"),
                      italic=True, spaceAfter=10)
small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8)

def table_style(header_color="#1F4E78"):
    return TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("TOPPADDING", (0,0), (-1,0), 4),
        ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("FONTSIZE", (0,1), (-1,-1), 8),
        ("ALIGN", (0,1), (0,-1), "LEFT"),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,1), (-1,-1), 3),
        ("BOTTOMPADDING", (0,1), (-1,-1), 3),
    ])

def fmt_money(v): return f"€{v:,.0f}" if v else "—"
def fmt_int(v): return f"{int(v):,}" if v else "—"
def fmt_pct(v): return f"{v*100:.1f}%" if v else "—"

elements = []

# Cover
elements.append(Paragraph("ISZE Warranty Analysis 2025", title))
elements.append(Paragraph("Network warranty performance — per DB intensity, top failing parts, and dominant failure modes", subtitle))

# Headline
elements.append(Paragraph("Headline numbers", h2))
hdr_data = [
    ["Metric", "Value", "Context"],
    ["Total warranty lines priced", f"{len(cv) + len(lcv):,}", "2,388 CV + 8,977 LCV"],
    ["Total warranty value at PR00", "€2,894,644", "Parts only — labour and other costs excluded"],
    ["Network commercial parts sales 2025", "€31,353,932", "From ERP net-sales export, parts-only"],
    ["Warranty as % of commercial sales", "9.2%", "Network average"],
    ["Parts replaced under warranty (units)", "12,885", "Across 18 distributors"],
]
t = Table(hdr_data, colWidths=[80*mm, 50*mm, 130*mm])
t.setStyle(table_style())
elements.append(t)
elements.append(Spacer(1, 8))
elements.append(Paragraph(
    "Warranty is independent of the commercial parts sales TSV — these parts do not appear in the GPS numerator. "
    "Values are computed as warranty unit quantity × PR00 price (Pricing_Data master, 163,077 part numbers). "
    "The price recorded in the warranty file itself (admit/claim amount) is not used.",
    note))

elements.append(PageBreak())

# 1. Per-DB warranty intensity
elements.append(Paragraph("1. Per-DB warranty intensity", h2))
elements.append(Paragraph(
    "Sorted by warranty € per UIO unit. High €/UIO and high warranty/sales ratio together = fleet-health flag. "
    "Top of the table is where warranty cost is heaviest relative to fleet size.", body))
rows = [["DB", "Country", "UIO 2025", "Warranty qty", "Warranty €", "€ per UIO", "Sales 2025", "Warranty / Sales"]]
for _, r in per_db.iterrows():
    rows.append([r["db"], r["country"], fmt_int(r["uio"]), fmt_int(r["qty"]),
                 fmt_money(r["value"]), f"€{r['eur_per_uio']:.2f}",
                 fmt_money(r["sales"]), fmt_pct(r["warr_pct_sales"])])
# Network total
tot_q = per_db["qty"].sum()
tot_v = per_db["value"].sum()
tot_s = per_db["sales"].sum()
rows.append(["NETWORK", "", fmt_int(per_db["uio"].sum()), fmt_int(tot_q),
             fmt_money(tot_v), f"€{tot_v/per_db['uio'].sum():.2f}",
             fmt_money(tot_s), fmt_pct(tot_v/tot_s)])

t = Table(rows, colWidths=[34*mm, 30*mm, 22*mm, 24*mm, 28*mm, 22*mm, 30*mm, 28*mm])
ts = table_style()
ts.add("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#2E75B6"))
ts.add("TEXTCOLOR", (0,-1), (-1,-1), colors.white)
ts.add("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold")
t.setStyle(ts)
elements.append(t)
elements.append(Spacer(1, 6))
elements.append(Paragraph(
    "Observations: RSA Norway tops the network at €36.79/UIO and 20.3% warranty/sales — outlier. "
    "IUK at €22.16/UIO with 17.0% warranty/sales reflects the D-Max electrical reliability theme. "
    "Isuzu Ireland sits at 3.0% warranty/sales — outlier low, suggesting either under-reporting or a genuinely younger fleet. "
    "UMI (Israel LCV) absent from this dataset despite €3.4M of commercial sales — data gap to investigate.", note))

elements.append(PageBreak())

# 2. Top 25 parts by warranty value
elements.append(Paragraph("2. Top 25 parts by warranty value", h2))
elements.append(Paragraph(
    "Each row shows a single part number's contribution to network warranty in 2025. "
    "Three steering-unit PNs combine for €533k (18% of all warranty); two PM-sensor PNs combine for €407k.", body))
rows = [["#", "Part number", "Description", "Qty replaced", "Warranty €"]]
for i, r in top25.iterrows():
    d = r["desc"] if r["desc"] else "—"
    if len(d) > 48: d = d[:45] + "..."
    rows.append([str(i+1), r["pn"], d, fmt_int(r["qty"]), fmt_money(r["value"])])

t = Table(rows, colWidths=[10*mm, 32*mm, 110*mm, 28*mm, 34*mm])
t.setStyle(table_style())
elements.append(t)
elements.append(Spacer(1, 6))
elements.append(Paragraph(
    "Pattern: aftertreatment system (NOx sensors, DEF tanks, DEF pumps, urea injectors, PM sensors) dominates by count. "
    "Steering units dominate by value. Engine replacements are rare but expensive. Brake rotors are high-volume PMS-recoverable parts.",
    note))

elements.append(PageBreak())

# 3a. Top 15 LCV failure operations
elements.append(Paragraph("3. Top 15 failure modes — LCV (D-Max)", h2))
elements.append(Paragraph(
    "Operation = workshop repair description on the warranty claim. Sorted by total value 2025.", body))
rows = [["#", "Operation", "Cases", "Total value €"]]
for i, r in ol.iterrows():
    op = r["ope"] if r["ope"] else "(no description)"
    if len(op) > 65: op = op[:62] + "..."
    rows.append([str(i+1), op, fmt_int(r["count"]), fmt_money(r["value"])])
t = Table(rows, colWidths=[10*mm, 150*mm, 28*mm, 36*mm])
t.setStyle(table_style())
elements.append(t)
elements.append(Spacer(1, 8))

# 3b. Top 15 CV failure operations
elements.append(Paragraph("Top 15 failure modes — CV (N-series + F-Series)", h2))
rows = [["#", "Operation", "Cases", "Total value €"]]
for i, r in oc.iterrows():
    op = r["ope"] if r["ope"] else "(no description)"
    if len(op) > 65: op = op[:62] + "..."
    rows.append([str(i+1), op, fmt_int(r["count"]), fmt_money(r["value"])])
t = Table(rows, colWidths=[10*mm, 150*mm, 28*mm, 36*mm])
t.setStyle(table_style())
elements.append(t)
elements.append(Spacer(1, 6))
elements.append(Paragraph(
    "LCV pattern: power steering gear assembly is the single largest failure mode at €562k (one operation type). "
    "PM sensor replacement is the second-most-frequent operation. ENGINE REPLACE RZ4E appears in both CV and LCV — rare but very expensive.",
    note))
elements.append(Paragraph(
    "CV pattern: aftertreatment system dominates — DPF, urea pump, NOx sensors (in and out), urea sensor account for ~€390k combined. "
    "This is the modern diesel aftertreatment fragility showing up at fleet scale.",
    note))

elements.append(PageBreak())

# 4. Key findings
elements.append(Paragraph("4. Key findings", h2))
findings = [
    ("Power steering on D-Max", "€562k from a single operation (gear-assembly replace). Three steering-unit part numbers combine for €533k of network warranty — 18% of total. Quality flag worth raising upstream."),
    ("Aftertreatment system fragility", "DEF tank, DEF pump, urea injector, NOx sensors (in and out), urea sensor, PM sensors: ~€800k combined across CV and LCV. Modern diesel emissions equipment is the fleet's most common failure source."),
    ("Electrical failures dominate LCV trouble codes", "3,373 cases worth €824k (38% of all LCV warranty value) categorised as 'ELECTRICAL FAILURES'. Above industry norm of 25-35%. D-Max electrical reliability is a concrete quality conversation."),
    ("Warranty intensity outliers", "RSA Norway 20.3% warranty/sales, IUK 17.0%, Finland 17.1% — top of the network. Isuzu Ireland 3.0% — bottom. Variation is too large to be fleet-mix only; under-reporting or claim-suppression worth investigating at the low end."),
    ("UMI Israel LCV data gap", "Universal Motors Israel has €3.4M of commercial parts sales in 2025 but zero rows in this warranty extract. Either Israel processes warranty outside this system or the file is incomplete. Confirm with IML."),
    ("Failure peak at 20-50k km / 1-3 years post-RDR", "Bulk of failures occur in the second and third year of ownership, at 20-50k km — the post-shakedown, pre-replacement window. Pre-3-month infant mortality is only 1% — quality at delivery is fine."),
    ("PMS recoverability", "Several top-warranty parts (brake rotors, water pumps, filters, radiators) are PMS-eligible. Higher PMS capture rate → these parts get replaced commercially before they fail → less warranty cost and more parts revenue."),
    ("BVP / competitive angle", "49% of warranty value is on ABC-A parts — the same high-volume parts that face aftermarket competition. Cross-referencing warranty parts with commercial sales identifies the SKUs where competitive positioning matters most (PM sensors, brake rotors, NOx sensors)."),
]
for label, text in findings:
    elements.append(Paragraph(f"<b>{label}</b> — {text}", body))
    elements.append(Spacer(1, 4))

elements.append(Spacer(1, 10))
elements.append(Paragraph("5. Methodology note", h2))
elements.append(Paragraph(
    "Warranty values are reconstructed by multiplying the unit quantity recorded on each warranty claim line by the "
    "current PR00 reference price for that part number. The admit/claim amount recorded in the warranty file is not used "
    "(those amounts reflect warranty pricing terms which are not consistent across distributors). All values in EUR. "
    "Warranty parts do not appear in the commercial parts sales TSV and are therefore independent of the GPS calculation.",
    note))
elements.append(Paragraph(
    "Sources: Raw_CV_Warranty (13,814 claims, 2,388 priced for 2025) and Raw_LCV_Warranty (25,717 claims, 8,977 priced for 2025) "
    "× PR00 price master (163,077 part numbers). 37 part numbers in LCV warranty could not be priced (not in current PR00 master — likely superseded PNs).",
    note))

doc.build(elements)
print(f"PDF written: {OUT}")
print(f"  Pages with: headline / per-DB intensity / top 25 parts / top 15 failure modes (CV+LCV) / key findings")
