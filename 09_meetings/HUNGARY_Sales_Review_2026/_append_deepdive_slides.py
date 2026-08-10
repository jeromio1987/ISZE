import sys
sys.path.insert(0, "/home/user/ISZE/04_tools/ppt_template_v2")
sys.path.insert(0, "/home/user/ISZE/04_tools/db_sales_review")

import isze_chart_theme as ct
import isze_deck_builder as db
import build_deck as BD
from pptx import Presentation
from pptx.util import Inches, Pt

ct.FONT_FAMILY = "Calibri"

PPTX = "/home/user/ISZE/09_meetings/HUNGARY_Sales_Review_2026/ISZE_HUNGARY_Sales_Review_FY2027.pptx"
CHART_DIR = "/home/user/ISZE/09_meetings/HUNGARY_Sales_Review_2026/charts_out"

prs = Presentation(PPTX)
sldIdLst = prs.slides._sldIdLst
closing_elem = sldIdLst[-1]  # current last slide = "Moving the World" closer

# ---------------------------------------------------------------- chart --
ct.bar_chart(
    ["CY2022", "CY2023", "CY2024", "CY2025", "FY2026"],
    {"GPS %": [29.8, 37.4, 41.9, 34.5, 37.1]},
    f"{CHART_DIR}/gps_history.png",
    title="Hungary GPS since 2022 — peaked 2024, easing back since",
    ylabel="GPS %", value_fmt="{:.1f}%")

# ------------------------------------------------------------- slide A --
takeaways_a = [
    "GPS rose from about 30% in 2022 to a peak of 41.9% in 2024, then eased back to "
    "34.5% in 2025 and sits at 37.1% today (FY2026) — two years of erosion, not a "
    "straight climb.",
    "BVP held 12-18% share through 2024, but 2025's decline is entirely Genuine "
    "(-EUR 71K) while BVP grew (+EUR 4K) — a Genuine-parts problem, not a BVP one.",
    "2022's apparent mismatch against the previously computed series is resolved: "
    "that figure was a Jan-Sep YTD cut (99.96% match through 5 Sep 2022), not the "
    "full year — CY2022 here is the complete twelve months.",
    "The FY2027 base is disputed: corrected-survival shrinks the parc to 3,645 "
    "(-2.4%); UIO V19 grows it to 3,992 (+6.9%) — worth agreeing which.",
]
db.build_two_col(
    prs, title="GPS since 2022: peaked at 42%, now easing back to 37%",
    chart_path=f"{CHART_DIR}/gps_history.png",
    takeaways=takeaways_a, eyebrow="Deep Dive — GPS History", page_no=19,
    takeaway_heading="Takeaways")

# ------------------------------------------------------------- slide C --
ct.bar_chart(
    ["2020", "2021", "2022", "2023", "2024", "2025"],
    {"Genuine": [284645, 261754, 219907, 307321, 341055, 269922],
     "BVP": [60456, 49649, 41054, 48276, 47898, 51951]},
    f"{CHART_DIR}/bvp_genuine.png",
    title="Hungary — Genuine vs BVP billing by year (EUR)",
    ylabel="EUR", value_fmt="{:,.0f}")

takeaways_c = [
    "2025 is the only year since 2020 where Genuine and BVP move in opposite "
    "directions: Genuine EUR 341K → EUR 270K (-71K); BVP EUR 48K → EUR 52K (+4K). "
    "Every prior year they moved together.",
    "Not just a pricing effect: Genuine volume also fell (9,216 → 7,372 units) and "
    "breadth contracted (1,160 → 930 distinct genuine part numbers sold, -20%).",
    "BVP held up on every measure over the same year — units flat (4,036 → 4,052), "
    "SKU breadth grew (37 → 43) — so this isn't distributor-wide destocking, it's "
    "specific to Genuine.",
    "Worth cutting the 2025 genuine drop by category together before assuming it's "
    "competitive leakage — a concentrated cause (e.g. one model, one dealer) reads "
    "very differently from a broad-based one.",
]
db.build_two_col(
    prs, title="Genuine vs BVP: 2025 breaks the pattern",
    chart_path=f"{CHART_DIR}/bvp_genuine.png",
    takeaways=takeaways_c, eyebrow="Deep Dive — Genuine vs BVP", page_no=20,
    takeaway_heading="Takeaways")

# ------------------------------------------------------------- slide B --
s2 = db.build_content(
    prs, title="Where the gap is: competitive parts leaking to the aftermarket",
    eyebrow="Deep Dive — Competitive Capture", page_no=21)

rows = [["Category", "2023", "2024", "2025", "Network (2025)"]]
data = [
    ("Oil filter", 44.6, 46.3, 45.0, 60.9),
    ("Fuel filter", 12.4, 12.7, 18.8, 47.3),
    ("Air filter", 42.4, 40.0, 45.9, 52.4),
    ("Brake pad", 11.7, 11.1, 15.6, 29.8),
    ("Brake rotor", 22.4, 25.4, 36.1, 54.9),
]
for cat, y23, y24, y25, net25 in data:
    rows.append([cat, f"{y23:.1f}%", f"{y24:.1f}%", f"{y25:.1f}%", f"{net25:.1f}%"])

BD.styled_table(
    s2, rows, Inches(0.32), Inches(1.20), Inches(12.7), Inches(1.95),
    [Inches(3.5), Inches(2.3), Inches(2.3), Inches(2.3), Inches(2.3)],
    bold_last=False, size=12)

db.bullet_list(s2, [
    "The gap isn't new — Hungary has sat 15-35 points below network on brake pad, "
    "brake rotor and fuel filter capture in every one of the last three full years. "
    "Air filter is the one category near parity.",
    "Warranty claims (separate claims-system data, not part of the billing above) "
    "jumped from near-zero (FY2024: EUR 225) to EUR 102,418 (FY2026) — right where "
    "GPS started easing back. Worth checking if that's a genuine quality trend, a "
    "claims-logging change, or a campaign.",
], Inches(0.32), Inches(3.30), Inches(12.7), Inches(1.15), size=12, line_spacing=1.1)

db.txt(s2, "QUESTIONS FOR US TO WORK THROUGH TOGETHER", Inches(0.32), Inches(4.55),
       Inches(12), Inches(0.32), size=13, bold=True, color=BD.RED)
db.bullet_list(s2, [
    "Brake pad/rotor capture has trailed the network by 15-35 points for three "
    "straight years — what's routing that work to independent garages?",
    "Warranty claims went from near-zero to over EUR 100K in two fiscal years — "
    "quality issue, claims-logging change, or a specific campaign?",
    "Which fleet number should FY2027 use — the ~4,000-unit growing view or the "
    "~3,645-unit corrected-survival view?",
    "Genuine parts fell EUR 71K in 2025 while BVP grew EUR 4K — is genuine business "
    "moving to the aftermarket, or are dealers trading down within our own catalog?",
], Inches(0.32), Inches(4.90), Inches(12.7), Inches(1.75), size=12, line_spacing=1.05)

# ------------------------------------------------- move closer back to the end --
sldIdLst.remove(closing_elem)
sldIdLst.append(closing_elem)

prs.save(PPTX)
print("saved", PPTX, "total slides:", len(prs.slides))
