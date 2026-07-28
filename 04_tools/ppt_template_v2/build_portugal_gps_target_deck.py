"""
Portugal FY2027 GPS/parts target — I-Motors meeting deck, 29 July 2026.
Source: Matriculas Isuzu SAP.xlsx (real registrations) cohort-decayed on the
IMIT survival curve; ISZE_GPS_Extended_Target_FY27_V3.1.xlsx (rates, FY26
actuals, target formula). See memory project_uio_v20.md for full derivation.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import isze_chart_theme as ct
import isze_deck_builder as db
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ct.FONT_FAMILY = "Calibri"

CHART_DIR = os.path.join(HERE, "charts_out", "portugal_gps_target")
os.makedirs(CHART_DIR, exist_ok=True)


def cp(name):
    return os.path.join(CHART_DIR, name)


YEARS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
TRUCKS  = [1586.9, 1701.2, 1949.1, 2187.0, 2464.4, 2661.3, 2666.6, 2940.9]
PICKUPS = [3148.0, 3140.8, 3183.7, 3287.9, 3635.0, 4281.2, 4568.8, 4968.0]

ct.trend_line(
    YEARS,
    {"Pickups": PICKUPS, "Trucks": TRUCKS},
    cp("uio_trend.png"),
    title="Portugal fleet, built from your own registration records — 4,735 (2019) to 7,909 (2026)",
    value_fmt="{:,.0f}",
)

prs = db.new_presentation()

db.build_cover(
    prs,
    title="Portugal FY2027\nParts Target",
    subtitle="I-Motors  ·  Fleet-based target review  ·  29 July 2026",
    eyebrow="ISZE  ·  PORTUGAL  ·  I-MOTORS",
)

db.build_two_col(
    prs,
    title="Fleet has grown steadily since 2019 — +9.3% into 2026",
    chart_path=cp("uio_trend.png"),
    eyebrow="Executive summary",
    page_no=2,
    takeaway_heading="What this means for FY2027",
    takeaways=[
        "Built directly from your vehicle registration records (2005-2026), not a top-down estimate.",
        "Fleet growth into 2026: +9.3% — a moderate, sustainable rate after a stronger 2023-2024.",
        "FY2027 target basis: fleet size + 5% price increase + 1.8% additional growth.",
        "Fully traceable: registrations aged on the published 12-year survival curve, nothing else assumed.",
    ],
)

# ---- Slide 3: target table -------------------------------------------------
s = db.build_content(prs, "How the FY2027 target is built", eyebrow="The proposal", page_no=3)

rows_data = [
    ["", "FY2026", "FY2027", "Change"],
    ["Portugal fleet (units)", "7,235", "7,909", "+9.3%"],
    ["ISZE-net rate / unit", "base", "+5%", "+5.0%"],
    ["Additional growth (stretch)", "—", "+1.8%", "+1.8%"],
    ["Sales-to-Dealer target", "€4,047,903", "€4,147,949", "+2.5%"],
]
n_rows, n_cols = len(rows_data), len(rows_data[0])
tbl_left, tbl_top, tbl_w, tbl_h = Inches(0.32), Inches(1.35), Inches(9.4), Inches(2.6)
gtable = s.shapes.add_table(n_rows, n_cols, tbl_left, tbl_top, tbl_w, tbl_h).table
gtable.columns[0].width = Inches(3.8)
for c in range(1, n_cols):
    gtable.columns[c].width = Inches((9.4 - 3.8) / (n_cols - 1))

RED = RGBColor(0xCC, 0x0E, 0x1E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY_BG = RGBColor(0xEC, 0xEC, 0xEC)

for r in range(n_rows):
    for c in range(n_cols):
        cell = gtable.cell(r, c)
        cell.text = rows_data[r][c] if rows_data[r][c] else " "
        para = cell.text_frame.paragraphs[0]
        if not para.runs:
            para.add_run().text = ""
        run = para.runs[0]
        run.font.size = Pt(13)
        run.font.name = "Calibri"
        para.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
        cell.vertical_anchor = 3  # middle
        cell.margin_left = Inches(0.1)
        cell.margin_right = Inches(0.1)
        if r == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RED
            run.font.bold = True
            run.font.color.rgb = WHITE
        else:
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r % 2 == 1 else GRAY_BG
            run.font.bold = (c == n_cols - 1) or (r == n_rows - 1)
            run.font.color.rgb = RED if (r == n_rows - 1 and c == n_cols - 1) else BLACK

db.bullet_list(
    s,
    ["Fleet size, price and stretch combine through the target model — the +2.5% "
     "Sales-to-Dealer change is the net effect, not a simple sum of the inputs above.",
     "FY2026 actual and the +5% rate are the same basis used across all ISZE markets this year."],
    Inches(0.32), Inches(4.25), Inches(12.7), Inches(1.4), size=13,
)

# ---- Slide 4: data request --------------------------------------------------
s = db.build_content(prs, "Ask: Sales-to-Dealer data, direct from I-Motors", eyebrow="Data request", page_no=4)
db.bullet_list(
    s,
    [
        "We're asking I-Motors to share Sales-to-Dealer data directly, from 01/01/2025 onward.",
        "Today's dealer-level figure is drawn from an internal KPI file that isn't always current.",
        "Direct data means faster, more accurate joint target-setting every year — for both sides.",
        "Same principle as the fleet number on the previous slide: your own records replace a modeled estimate.",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(3.5), size=15,
)

# ---- Slide 5: next steps -----------------------------------------------------
s = db.build_content(prs, "Next steps", eyebrow="Summary", page_no=5)
db.bullet_list(
    s,
    [
        "Confirm FY2027 target: €4,147,949 Sales-to-Dealer (+2.5% vs FY2026 actual).",
        "Agree Sales-to-Dealer data-sharing arrangement, effective 01/01/2025.",
        "Genuine parts share and parts sales target — detail to follow per the standing agenda.",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(3.0), size=15,
)

db.build_closing(prs)

out_path = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "ISZE_Portugal_GPS_Target_FY2027_Jul2026.pptx",
)
prs.save(out_path)
print("Saved:", out_path)
