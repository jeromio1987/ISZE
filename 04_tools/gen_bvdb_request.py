"""Generate ISZE_BVDB_Data_Request_May2026.docx"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu\Divers\ISZE_BVDB_Data_Request_May2026.docx"

RED   = RGBColor(0xCC, 0x0E, 0x1E)
DARK  = RGBColor(0x1A, 0x1A, 0x1A)
GRAY  = RGBColor(0x5A, 0x5A, 0x5A)
AMBER = RGBColor(0xE3, 0xB3, 0x41)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLUE  = RGBColor(0x1E, 0x2A, 0x5E)

doc = Document()

for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

style = doc.styles["Normal"]
style.font.name = "Arial"
style.font.size = Pt(10)
style.font.color.rgb = DARK


def shd_cell(cell, hex_fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def border_cell(cell, color_hex):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    bdr = OxmlElement("w:tcBorders")
    for edge in ("top", "bottom", "left", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:color"), color_hex)
        bdr.append(el)
    tcPr.append(bdr)


def p_shd(para, hex_fill):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    pPr.append(shd)


def p_left_border(para, color_hex, size="12"):
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), size)
    left.set(qn("w:color"), color_hex)
    pBdr.append(left)
    pPr.append(pBdr)


def add_h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.left_indent  = Cm(0.3)
    p_shd(p, "CC0E1E")
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = WHITE
    run.font.name = "Arial Black"


def add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11.5)
    run.font.color.rgb = RED
    run.font.name = "Arial"
    # bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "4")
    bot.set(qn("w:color"), "CC0E1E")
    pBdr.append(bot)
    pPr.append(pBdr)


def add_h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(10.5)
    run.font.color.rgb = DARK
    run.font.name = "Arial"


def add_body(doc, text, bold=False, italic=False, color=None, sa=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run(text)
    r.bold   = bold
    r.italic = italic
    r.font.size = Pt(10)
    r.font.name = "Arial"
    if color:
        r.font.color.rgb = color
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(2)
    p.paragraph_format.left_indent  = Cm(0.6 + level * 0.5)
    r = p.add_run(u"•  " + text)
    r.font.size = Pt(10)
    r.font.name = "Arial"


def add_code(doc, lines):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.left_indent  = Cm(0.5)
    p_shd(p, "F5F5F5")
    for i, line in enumerate(lines):
        prefix = "" if i == 0 else "  "
        r = p.add_run(prefix + line)
        r.font.name = "Courier New"
        r.font.size = Pt(9)
        r.font.color.rgb = DARK
        if i < len(lines) - 1:
            r.add_break()


def add_callout(doc, label, text, fill_hex, border_hex):
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    cell = t.rows[0].cells[0]
    shd_cell(cell, fill_hex)
    border_cell(cell, border_hex)
    cell.paragraphs[0].paragraph_format.space_before = Pt(3)
    cell.paragraphs[0].paragraph_format.space_after  = Pt(3)
    p = cell.paragraphs[0]
    if label:
        r = p.add_run(label + "  ")
        r.bold = True
        r.font.size = Pt(10)
        r.font.name = "Arial"
    r2 = p.add_run(text)
    r2.font.size = Pt(10)
    r2.font.name = "Arial"
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def add_table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    hrow = t.rows[0].cells
    for i, h in enumerate(headers):
        shd_cell(hrow[i], "CC0E1E")
        p = hrow[i].paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.color.rgb = WHITE
        r.font.size = Pt(9)
        r.font.name = "Arial"
    for ri, row in enumerate(rows):
        cells = t.rows[ri + 1].cells
        fill = "FFFFFF" if ri % 2 == 0 else "F8F8F8"
        for ci, val in enumerate(row):
            shd_cell(cells[ci], fill)
            p = cells[ci].paragraphs[0]
            if isinstance(val, tuple):
                r = p.add_run(val[0])
                r.bold = val[1] if len(val) > 1 else False
                if len(val) > 2 and val[2]:
                    r.font.color.rgb = val[2]
            else:
                r = p.add_run(str(val))
            r.font.size = Pt(9)
            r.font.name = "Arial"
    if col_widths:
        for row2 in t.rows:
            for ci2, cell2 in enumerate(row2.cells):
                if ci2 < len(col_widths):
                    cell2.width = Cm(col_widths[ci2])
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(2)


# ================================================================
# DOCUMENT
# ================================================================

# Title block
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
r = p.add_run("ISZE — Data Request to BVDB")
r.bold = True
r.font.size = Pt(20)
r.font.color.rgb = RED
r.font.name = "Arial Black"

add_body(doc,
    "Two data extracts needed to correct the AIM model and improve sales demand analysis.",
    color=GRAY)
add_body(doc,
    "Author: Jerome Van der Pluym  |  VP Sales  |  May 2026  |  INTERNAL",
    italic=True, color=GRAY, sa=2)
doc.add_paragraph("─" * 85).paragraph_format.space_after = Pt(8)

# ── BACKGROUND ────────────────────────────────────────────────
add_h2(doc, "Background — Why these two extracts are needed")

add_body(doc,
    "The AIM model (Aftermarket Intelligence Model) is ISZE's internal tool for ranking parts "
    "by commercial importance, sizing distributor opportunities, and guiding pricing and campaign "
    "decisions. It currently runs on Qty x PR00 (standard list price) as its revenue input. "
    "This creates two specific, fixable problems:")

add_bullet(doc,
    "Problem 1 — Revenue figures are wrong for SPA customers. Israel (UTI and UMI) have "
    "Special Price Agreements. The ZPR1 surcharge inflates PR00 upward, but a separate SPA "
    "rebate reduces what ISZE actually receives. The field VKWRT in SAP contains the real "
    "net amount after all conditions. Without it, Israel distributors are likely mis-scored "
    "in AIM, and campaign budgets are based on a number that does not reflect actual revenue.")

add_bullet(doc,
    "Problem 2 — Sell-in is not demand. ISZE-to-distributor sell-in is systematically "
    "distorted by MOS policy cycles, year-end loading, and promotional buys. A distributor "
    "stock snapshot at two points in time (January + December) allows ISZE to calculate "
    "distributor sell-out = sell-in minus delta-stock. This converts existing data into a "
    "real demand signal, without any new data collection.")

add_callout(doc,
    "Both requests use data that already exists in SAP and Power BI.",
    " BVDB does not need to build anything new. These are standard extract requests.",
    "F2FBF3", "2E7D32")

# ================================================================
add_h1(doc, "Request 1 of 2  —  VKWRT Net Revenue Extract from SAP")
# ================================================================

add_h2(doc, "What this is")
add_body(doc,
    "A SAP billing extract (via transaction VF05N) covering CY2024 and CY2025, with one "
    "additional field included: VKWRT (SAP field VBRP-VKWRT). This field contains the net "
    "invoiced revenue after all pricing conditions have been applied — discounts, surcharges, "
    "and rebates. It is already calculated by SAP on every invoice line. No SAP reconfiguration "
    "is needed. BVDB just needs to include it in the extract.")

add_h2(doc, "Why not just use PR00?")
add_table(doc,
    ["", "PR00  (currently used)", "VKWRT  (requested)"],
    [
        ("What it represents",
         "Standard list price x quantity",
         "Actual net amount ISZE receives after ALL pricing conditions"),
        ("Israel — ZPR1 surcharge",
         ("Inflated upward — ZPR1 adds on top of PR00", False, RED),
         ("Correct — surcharge is part of the net calculation", False, GREEN)),
        ("Israel — SPA rebate",
         ("Ignored — rebate not captured in PR00", False, RED),
         ("Included — rebate reduces VKWRT to the real net", False, GREEN)),
        ("ITUK (no SPA)",
         "Accurate — no structural difference",
         "Same as PR00, no change expected"),
        ("Impact on AIM if unresolved",
         ("Israel may be over- or under-scored. Campaign priorities wrong.", False, AMBER),
         ("Scores reflect real ISZE net revenue. Decisions are grounded.", False, GREEN)),
    ],
    col_widths=[4.5, 5.5, 6.5]
)

add_h2(doc, "One question for BVDB before sending the extract")
add_callout(doc,
    "Ask BVDB:",
    '"For customers with SPA agreements (Israel: UTI and UMI), are the SPA rebates '
    'posted as adjustments to VKWRT on the invoice line itself — or do they come through '
    'as separate credit note documents (SAP billing type G2)?"\n\n'
    'If inline: F2 invoices only is sufficient for the extract.\n'
    'If credit notes: the extract must include F2 invoice lines AND G2 credit memo lines, '
    'joined by sold-to party and material number.',
    "FFF8E1", "E3B341")

add_h2(doc, "Exact SAP specification  —  forward this to BVDB")

add_h3(doc, "Transaction")
add_code(doc, [
    "VF05N  (billing document list)",
    "Alternative: SE16N on table VBRP joined to VBRK and KONV",
])

add_h3(doc, "Filters")
add_code(doc, [
    "Sales Organisation  :  ISZE  (IE40)",
    "Billing type        :  F2 only  (standard invoices)",
    "Exclude             :  RE (returns)  |  G2 (credit memos)  |  F5 (pro formas)",
    "Currency            :  EUR",
    "Period 1            :  01.01.2024 to 31.12.2024",
    "Period 2            :  01.01.2025 to 31.12.2025",
])

add_h3(doc, "Fields to include in the extract")
add_code(doc, [
    "billing_date        <-  VBRK-FKDAT             (date of invoice)",
    "sold_to             <-  VBRK-KUNRG             (distributor / customer code)",
    "material_number     <-  VBRP-MATNR             (part number)",
    "qty                 <-  VBRP-FKIMG             (billed quantity)",
    "pr00_eur            <-  KONV-KWERT  where KSCHL = 'PR00'",
    "zpr1_eur            <-  KONV-KWERT  where KSCHL = 'ZPR1'   (zero for non-Israel)",
    "vkwrt_eur           <-  VBRP-VKWRT             <<< THIS IS THE KEY FIELD",
])

add_h3(doc, "Output format")
add_code(doc, [
    "File format     :  Flat CSV, one row per invoice line item",
    "Separator       :  Semicolon  ( ; )",
    "Encoding        :  UTF-8",
    "File naming     :  VKWRT_CY2024.csv  and  VKWRT_CY2025.csv",
    "Expected rows   :  ~150,000 to 200,000 per year",
    "Expected size   :  ~15 to 25 MB per file",
])

add_h2(doc, "What ISZE will do with this data")
add_bullet(doc,
    "Join VKWRT to the AIM parts master on material number.")
add_bullet(doc,
    "For each distributor: calculate total PR00 revenue vs total VKWRT revenue. "
    "Flag any distributor where the gap exceeds 5%.")
add_bullet(doc,
    "Recompute AIM Strategic Scores using VKWRT as the revenue base instead of PR00.")
add_bullet(doc,
    "Add a SPA-adjusted toggle to AIM output — allowing side-by-side comparison of "
    "list-price scores vs net-revenue scores.")
add_bullet(doc,
    "Expected result: Israel (UTI + UMI) AIM scores shift. Campaign priorities and "
    "revenue benchmarks recalibrate to reflect what ISZE actually earns.")

add_h2(doc, "Priority summary")
add_table(doc,
    ["Item", "Detail"],
    [
        ("Priority",       ("HIGH — unblocks AIM SPA-adjusted scoring", True, RED)),
        ("Requested by",   "Jerome Van der Pluym, VP Sales"),
        ("Requested from", "BVDB"),
        ("Timeline",       "As soon as possible — no hard deadline but needed before next AIM review cycle"),
        ("Effort (BVDB)",  ("Low — standard VF05N extract with one additional field (VKWRT)", False, GREEN)),
        ("Sensitivity",    "Internal — do not share outside ISZE"),
    ],
    col_widths=[4.5, 12.0]
)

# ================================================================
add_h1(doc, "Request 2 of 2  —  Power BI CSV Exports  (3 Datasets)")
# ================================================================

add_h2(doc, "What this is")
add_body(doc,
    "A request for BVDB to export three Power BI datasets as CSV files on a recurring "
    "schedule. These datasets already exist in Power BI — this is not a new report build. "
    "The only change is delivery format: instead of ISZE manually downloading PBI views or "
    "taking screenshots, BVDB sends CSV exports by email or drops them to a shared folder.")

add_h2(doc, "Why this matters  —  the sell-in versus sell-out problem")
add_body(doc,
    "All of ISZE's current analysis is based on ISZE-to-distributor sell-in. "
    "Sell-in is a supply signal, not a demand signal. It is distorted by four structural factors:")

add_bullet(doc,
    "MOS policy cycles  —  distributors order in bulk when Minimum Order Size thresholds "
    "apply, concentrating purchases in specific weeks regardless of actual dealer demand.")
add_bullet(doc,
    "Year-end loading  —  distributors build stock in Q4 to hit annual targets, "
    "creating artificial Q4 spikes and Q1 troughs in ISZE sell-in data.")
add_bullet(doc,
    "Campaign loading  —  distributors buy ahead of promotional periods, "
    "inflating apparent demand in one period and deflating it in the next.")
add_bullet(doc,
    "Promotional buys  —  one-off large orders that look like demand increases "
    "in the data but are just inventory movements between ISZE and the distributor warehouse.")

add_body(doc, "")
add_callout(doc,
    "The fix requires only two data points:",
    " Distributor stock on hand at the start of the year, and at the end of the year.\n\n"
    "Distributor sell-out  =  ISZE sell-in  minus  change in distributor stock\n\n"
    "This converts existing sell-in data into a real demand signal. "
    "No new data collection. No dealer MOU. No IT integration.",
    "F5F7FF", "9FA8DA")

add_h2(doc, "The three datasets")

# ─ Dataset 1 ─
add_h3(doc, "Dataset 1  —  Monthly sell-in by part number by distributor")
add_body(doc,
    "Why needed: The current AIM model uses annual totals. Annual data hides two things that "
    "matter commercially: (1) seasonality — which parts spike in which months; (2) campaign "
    "loading — a part where 45% of annual volume lands in October is not genuinely in "
    "higher demand in October, the distributor is loading stock for a campaign. "
    "Monthly data makes this visible immediately.")
add_code(doc, [
    "Columns      :  year_month  |  distributor_code  |  material_number  |  qty_ordered  |  value_eur",
    "Period       :  Full CY2023 + CY2024 + CY2025  (3 years of history for trend analysis)",
    "Refresh      :  Monthly  —  1st working day of each month going forward",
    "File name    :  SellIn_Monthly_YYYYMM.csv",
    "Delivery     :  Email attachment  OR  SharePoint / Teams shared folder",
])

# ─ Dataset 2 ─
add_h3(doc, "Dataset 2  —  Distributor stock on hand by part number  (snapshot)")
add_body(doc,
    "Why needed: This is the core input for calculating distributor sell-out. "
    "Two snapshots per year (start + end of year) give one delta-inventory value per "
    "part per distributor. That single number transforms three years of existing sell-in "
    "data into sell-out estimates across the entire network. "
    "Without it, ISZE cannot distinguish genuine demand growth from a distributor "
    "stocking up ahead of a campaign or year-end.")
add_code(doc, [
    "Columns      :  snapshot_date  |  distributor_code  |  material_number  |  qty_on_hand",
    "Period       :  Snapshot at 01.01.2025 AND 31.12.2025  (retrospective first delivery)",
    "             :  Then ongoing: snapshot at 01.01 and 01.07 each year",
    "Refresh      :  Twice a year  (January + July)",
    "File name    :  Stock_Snapshot_YYYYMMDD.csv",
    "Note         :  If Power BI does not have a stock-by-PN view, BVDB may need to pull",
    "             :  this from SAP using transaction MB52 or the standard stock report.",
    "Delivery     :  Email attachment  OR  SharePoint / Teams shared folder",
])

# ─ Dataset 3 ─
add_h3(doc, "Dataset 3  —  Open backorders by part number  (current snapshot)")
add_body(doc,
    "Why needed: A part number that has been on backorder for 60 days has artificially "
    "suppressed sell-in — dealers could not order it even if they wanted to. "
    "AIM currently treats a backordered part as low demand. That is wrong. "
    "This dataset allows ISZE to flag AIM scores for backorder-affected parts "
    "and adjust scores to reflect what the real demand would have been.")
add_code(doc, [
    "Columns      :  material_number  |  total_open_qty  |  oldest_order_date  |  backorder_days",
    "Period       :  Current snapshot at time of extract",
    "Refresh      :  Monthly  (same delivery as Dataset 1)",
    "File name    :  Backorders_YYYYMM.csv",
    "Delivery     :  Email attachment  OR  same folder as Dataset 1",
])

add_h2(doc, "Summary of what BVDB needs to do for Request 2")
add_table(doc,
    ["Dataset", "Source in SAP / PBI", "Effort for BVDB", "Frequency"],
    [
        ("1. Monthly sell-in by PN",
         "Already in PBI as sales by customer and material",
         ("Low — export existing PBI report as CSV", False, GREEN),
         "Monthly"),
        ("2. Distributor stock snapshot",
         "PBI stock report or SAP MB52 if not in PBI",
         ("Low to Medium — depends on PBI coverage", False, AMBER),
         "Twice a year"),
        ("3. Open backorders by PN",
         "PBI backorder view or SAP MD04",
         ("Low — standard report export", False, GREEN),
         "Monthly"),
    ],
    col_widths=[4.5, 5.0, 5.5, 2.0]
)

add_callout(doc,
    "Format for all three datasets:",
    " Flat CSV file, semicolon ( ; ) separated, UTF-8 encoding. "
    "Email attachment is perfectly fine as a starting point. "
    "A shared Teams or SharePoint folder is also fine. "
    "No automation or API integration is needed — manual export on agreed dates is sufficient.",
    "F2FBF3", "2E7D32")

add_h2(doc, "What ISZE will do with this data")
add_bullet(doc,
    "Dataset 1: Replace annual AIM sell-in totals with month-level data. "
    "Detect campaign loading per part number per distributor. "
    "Build a seasonality index to improve demand forecasting.")
add_bullet(doc,
    "Dataset 2: Calculate delta-stock per distributor per part number. "
    "Compute sell-out = sell-in minus delta-stock. "
    "Update AIM to show sell-out alongside sell-in as a more accurate demand measure.")
add_bullet(doc,
    "Dataset 3: Flag AIM strategic scores for parts with more than 30 days backorder. "
    "Adjust scores to reflect suppressed demand rather than penalising a part "
    "that was genuinely in demand but unavailable.")
add_bullet(doc,
    "Combined effect: the AIM model shifts from measuring "
    "what distributors bought from ISZE to what dealers actually needed. "
    "This is a fundamentally more reliable signal for commercial decisions.")

add_h2(doc, "Priority summary")
add_table(doc,
    ["Item", "Detail"],
    [
        ("Priority",        ("HIGH for inventory snapshot  /  Medium for monthly sell-in and backorders", False, AMBER)),
        ("Requested by",    "Jerome Van der Pluym, VP Sales"),
        ("Requested from",  "BVDB"),
        ("Timeline",        "Inventory snapshot: before end of Q2 2026 (31.12.2025 data may still be available in SAP). Monthly exports: from June 2026 onward."),
        ("Effort (BVDB)",   ("Low — existing PBI reports, CSV export via report subscription or manual send", False, GREEN)),
        ("Sensitivity",     "Internal — do not share outside ISZE"),
    ],
    col_widths=[4.5, 12.0]
)

# ================================================================
add_h1(doc, "Summary  —  Two Requests in Plain Language")
# ================================================================

add_table(doc,
    ["", "Request 1: VKWRT extract", "Request 2: Power BI CSV exports"],
    [
        ("What",
         "SAP billing export with net revenue field (VKWRT) for CY2024 + CY2025",
         "3 CSV files: monthly sell-in, stock snapshots (Jan + Dec), open backorders"),
        ("The problem it solves",
         "PR00 overstates revenue for SPA customers. AIM scores and campaign priorities are based on a number that is not real for Israel.",
         "Sell-in is not demand. Stocking cycles, MOS, and campaign loading distort what looks like distributor demand."),
        ("Source",
         "SAP — transaction VF05N, table VBRP",
         "Power BI (+ SAP MB52 for stock snapshot if needed)"),
        ("Effort for BVDB",
         ("Low — standard extract with one additional field", False, GREEN),
         ("Low — export existing PBI reports as CSV", False, GREEN)),
        ("Frequency",
         "Once for CY2024 + CY2025. Annual refresh going forward.",
         "Monthly for sell-in and backorders. Twice a year for stock snapshots."),
        ("Impact on AIM",
         "Israel distributor scores corrected. Revenue baseline becomes real net revenue.",
         "All distributor demand analysis becomes sell-out based. Stocking distortion removed."),
        ("Priority",
         ("HIGH", True, RED),
         ("HIGH for snapshot  /  Medium for others", False, AMBER)),
    ],
    col_widths=[3.5, 7.0, 7.0]
)

doc.add_paragraph("")
add_body(doc,
    "Questions or clarifications: Jerome Van der Pluym  |  VP Sales  |  jvanderpluym@isze.eu",
    italic=True, color=GRAY)

doc.save(OUT)
print(f"Saved: {OUT}")
