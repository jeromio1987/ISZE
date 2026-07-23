# -*- coding: utf-8 -*-
"""
UTI meeting draft — Jul 2026 (tightened narrative + speaker notes).
Output: UTI_presentation_DRAFT_Jul2026.pptx
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

RED = RGBColor(0xCC, 0x0E, 0x1E)
LIGHT_RED = RGBColor(0xDC, 0x60, 0x6E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
LGRAY = RGBColor(0xF0, 0xF0, 0xF0)
MGRAY = RGBColor(0xD9, 0xD9, 0xD9)
NAVY = RGBColor(0x1A, 0x2B, 0x4A)
GOLD = RGBColor(0xB0, 0x8D, 0x57)

SW, SH = Inches(13.33), Inches(7.5)
HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
TEMPLATE_CANDIDATES = [
    Path(r"c:\Users\jerom\Downloads\UTI_presentation.pptx"),
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu\isuzu-ppt-template\assets\template.pptx"),
]

# ── verified figures ───────────────────────────────────────────────────────
GPS_STRETCH = {
    "gps_fy26": 32.0,
    "gps_plan": 36.5,
    "gps_stretch": 38.3,
    "pp": 1.8,
    "bp_base_m": 3.10,
    "stretch_bp_m": 3.25,
    "stretch_eur_k": 153,
    "incentive_k": 25,
    "kickback_k": 36,
    "wallet_m": 8.49,
}

Q1 = {
    "sales_k": 1037,
    "budget_k": 752,
    "vs_budget_pct": 38,
    "vs_py_pct": 29,
    "apr_may_k": 201,
    "june_k": 635,
    "june_ex_spa_k": 358,
    "spa_doc_k": 277,
    "spa_share_pct": 27,
}

BP_APR_MAY = [
    ["FY27 (€K)", "Apr", "May", "YTD"],
    ["Sales", "211", "191", "402"],
    ["Budget", "247", "235", "482"],
    ["vs Budget", "−14%", "−19%", "−17%"],
    ["Prior year", "294", "286", "580"],
    ["vs Prior year", "−28%", "−33%", "−31%"],
    ["Order intake", "182", "238", "420"],
]

SPA_CATS = [
    ["Category", "SPA share", "Role in basket"],
    ["Other mechanical", "~51%", "NOx, high-value lines"],
    ["Filters", "~10%", "Volume-heavy — link to mix talk"],
    ["Body / lighting", "~9%", ""],
    ["Electronics", "~8%", ""],
    ["Clutch / drivetrain", "~7%", ""],
    ["Brakes", "~6%", ""],
    ["Cooling / EGR", "~4%", "Grey-import defence"],
    ["Fuel / injection", "~4%", ""],
]

FILTER_PEER = [
    ["Category", "UTI genuine", "ITUK genuine"],
    ["Fuel filter", "~0%", "~80%"],
    ["Air filter", "~0%", "~85%"],
    ["Oil filter", "~0%", "~71%"],
    ["Brake pad", "~100%", "~100%"],
]

PMS_FY25 = [
    ["Category", "FY2025 capture", "EUR gap (ceiling)"],
    ["Fuel filter", "75%", "€40K"],
    ["Air filter", "48%", "€102K"],
    ["Oil filter", "55%", "€48K"],
    ["Brake pad", "27%", "€116K"],
    ["Clutch (family)", "20%", "€218K"],
    ["Combined (shown)", "", "€555K"],
]

NOTES: list[str] = []


def pick_template() -> Presentation:
    for p in TEMPLATE_CANDIDATES:
        if p.is_file():
            prs = Presentation(str(p))
            while prs.slides:
                rId = prs.slides._sldIdLst[0].rId
                prs.part.drop_rel(rId)
                del prs.slides._sldIdLst[0]
            return prs
    return Presentation()


prs = pick_template()


def bg(s):
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = WHITE


def txt(
    s,
    t,
    l,
    top,
    w,
    h,
    size=14,
    bold=False,
    color=BLACK,
    align=PP_ALIGN.LEFT,
    font="Calibri",
    italic=False,
):
    b = s.shapes.add_textbox(l, top, w, h)
    tf = b.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(t.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = font
    return b


def rect(s, l, t, w, h, c, rounded=False):
    sh = s.shapes.add_shape(5 if rounded else 1, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = c
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def oval(s, l, t, w, h, c):
    sh = s.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = c
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def logo(s, l=Inches(0.28), t=Inches(6.80), size=18):
    txt(s, "ISUZU", l, t, Inches(2), Inches(0.55), size=size, bold=True, color=RED, font="Arial Black")


def footer(s):
    rect(s, 0, SH - Inches(0.13), SW, Inches(0.13), RED)


def slide_num(s, n: int, total: int = 16):
    txt(
        s,
        str(n),
        Inches(12.5),
        Inches(6.95),
        Inches(0.5),
        Inches(0.35),
        size=11,
        color=MGRAY,
        align=PP_ALIGN.RIGHT,
    )


def notes(s, text: str):
    ns = s.notes_slide
    tf = ns.notes_text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text


def cover(title, sub, note: str):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    oval(s, Inches(6.2), Inches(3.5), Inches(9.5), Inches(6.0), LIGHT_RED)
    oval(s, Inches(4.2), Inches(4.7), Inches(11.5), Inches(5.0), RED)
    footer(s)
    txt(s, "ISUZU", Inches(0.38), Inches(0.22), Inches(2), Inches(0.55), size=30, bold=True, color=RED, font="Arial Black")
    txt(s, title, Inches(0.45), Inches(2.45), Inches(8.5), Inches(2.0), size=38, bold=True, color=BLACK)
    txt(s, sub, Inches(0.45), Inches(5.30), Inches(10), Inches(0.8), size=15, color=GRAY)
    notes(s, note)
    return s


def content(title: str, note: str, num: int | None = None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    logo(s)
    footer(s)
    txt(s, title, Inches(0.28), Inches(0.30), Inches(12.77), Inches(0.72), size=28, bold=True, color=BLACK)
    rect(s, Inches(0.28), Inches(1.02), Inches(12.77), Emu(38100), RED)
    if num is not None:
        slide_num(s, num)
    notes(s, note)
    return s


def body(s, items, x=Inches(0.6), y=Inches(1.45), w=Inches(12.1), size=16, gap0=10):
    b = s.shapes.add_textbox(x, y, w, Inches(5.3))
    tf = b.text_frame
    tf.word_wrap = True
    for i, (lvl, lead, rest) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap0 if lvl == 0 else 4)
        mark = "—  " if lvl == 0 else "      ·  "
        sz = size if lvl == 0 else size - 2
        r0 = p.add_run()
        r0.text = mark
        r0.font.size = Pt(sz)
        r0.font.color.rgb = RED if lvl == 0 else GRAY
        r0.font.bold = lvl == 0
        r0.font.name = "Calibri"
        if lead:
            r1 = p.add_run()
            r1.text = lead + (" " if rest else "")
            r1.font.size = Pt(sz)
            r1.font.bold = True
            r1.font.color.rgb = BLACK
            r1.font.name = "Calibri"
        if rest:
            r2 = p.add_run()
            r2.text = rest
            r2.font.size = Pt(sz)
            r2.font.color.rgb = BLACK
            r2.font.name = "Calibri"
    return b


def scell(c, t, size=12, bold=False, color=BLACK, fill=WHITE, align=PP_ALIGN.LEFT):
    c.margin_top = Pt(3)
    c.margin_bottom = Pt(3)
    c.margin_left = Pt(7)
    c.margin_right = Pt(7)
    c.vertical_anchor = MSO_ANCHOR.MIDDLE
    c.fill.solid()
    c.fill.fore_color.rgb = fill
    tf = c.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = t
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Calibri"


def add_table(s, rows, x, y, w, col_w, bs=12, hs=12):
    nr, nc = len(rows), len(rows[0])
    g = s.shapes.add_table(nr, nc, x, y, w, Inches(0.38 * nr)).table
    for j, cw in enumerate(col_w):
        g.columns[j].width = cw
    g.first_row = False
    g.horz_banding = False
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = g.cell(i, j)
            al = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            if i == 0:
                scell(c, val, size=hs, bold=True, color=WHITE, fill=RED, align=al)
            else:
                tot = row[0].lower().startswith(("total", "combined"))
                scell(
                    c,
                    val,
                    size=bs,
                    bold=tot,
                    color=BLACK,
                    fill=MGRAY if tot else (LGRAY if i % 2 == 0 else WHITE),
                    align=al,
                )
    return g


def takeaway_box(s, lines: list[str], y=Inches(5.85)):
    rect(s, Inches(0.55), y, Inches(12.2), Inches(1.35), LGRAY, rounded=True)
    txt(s, "TAKEAWAYS", Inches(0.75), y + Inches(0.08), Inches(3), Inches(0.3), size=10, bold=True, color=RED)
    txt(s, "\n".join(f"—  {ln}" for ln in lines), Inches(0.75), y + Inches(0.32), Inches(11.8), Inches(0.95), size=11, color=BLACK)


def closing(note: str):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    txt(s, "Moving the World – for You", Inches(2.5), Inches(2.80), Inches(8.5), Inches(0.65), size=18, color=GRAY, align=PP_ALIGN.CENTER)
    txt(s, "ISUZU", Inches(1.5), Inches(3.20), Inches(10.5), Inches(2.1), size=100, bold=True, color=RED, align=PP_ALIGN.CENTER, font="Arial Black")
    notes(s, note)


# ═══════════════════════════════════════════════════════════════════════════
# 1 COVER
cover(
    "ISZE – UTI",
    "Israel aftersales · parts business  |  FY2026–2027  |  07 July 2026  |  DRAFT",
    "OPENING (2 min)\n"
    "Thank them for hosting. This is a working session — sales performance, GPS stretch for FY27, "
    "and a first PMS view we want to refine together.\n\n"
    "Set tone: collaborative, not audit. We bring data; they bring operational reality (fleet, workshops, UTI Parts).\n\n"
    "Agenda is on next slide — offer to reorder if they have burning topics.",
)

# 2 AGENDA
s = content(
    "Agenda",
    "Walk the agenda top to bottom unless they redirect.\n"
    "Commercial block (~20 min): BP, Q1, SPA, GPS stretch, service mix.\n"
    "Analytics block (~15 min): filter mix vs ITUK, PMS summary — stop for questions.\n"
    "Exploratory (~10 min): fleet R&M and UTI Parts — learning, not accusations.\n"
    "Close with concrete next steps and owners.",
    2,
)
body(
    s,
    [
        (0, "BP FY27 & Q1 sales", "— situation vs budget and prior year; June SPA uplift"),
        (0, "GPS stretch FY27", "— target path and incentive"),
        (0, "Order urgency & fill rate", "— SOR vs RUSH/VOR"),
        (0, "Filter mix vs ITUK", "— genuine/BVP inside the relationship"),
        (0, "PMS capture summary", "— directional gaps; assumptions flagged"),
        (0, "Fleet R&M & UTI Parts", "— mutual learning; win-back where we compete"),
        (0, "Next steps", ""),
    ],
    y=Inches(1.35),
    size=18,
    gap0=14,
)

# 3 BP FY27
s = content(
    "BP FY27 — where the year stands (Apr–May)",
    "CONTEXT before Q1: Apr–May were soft — don't let June SPA mask a weak H1 start.\n\n"
    "ASK: What is driving softness — market, stock, end-customer demand?\n"
    "May order intake €238K > Apr €182K — probe: pipeline recovering or timing?\n"
    "Full-year budget €3.1M vs prior €2.9M — recovery must build from here.\n\n"
    "If they push back on budget: this is their reviewed plan, not ISZE imposing targets.",
    3,
)
add_table(s, BP_APR_MAY, Inches(0.6), Inches(1.4), Inches(6.4), [Inches(2.5), Inches(1.3), Inches(1.3), Inches(1.3)], bs=13, hs=13)
body(
    s,
    [
        (0, "Soft start:", "YTD sales €402K — −17% vs budget, −31% vs last year."),
        (0, "Both months below plan", "(Apr −14%, May −19%)."),
        (0, "Order intake turning up:", "May €238K vs €182K in April."),
        (0, "Full-year budget €3.10M", "(prior year €2.9M)."),
    ],
    x=Inches(7.35),
    y=Inches(1.5),
    w=Inches(5.7),
    size=14,
)

# 4 Q1 BRIDGE
s = content(
    "Q1 sales bridge — June SPA drove +38% vs budget",
    "KEY MESSAGE: Q1 looks strong (+38% vs budget) but is SPA-concentrated.\n\n"
    "Apr–May ≈ €201K/mo baseline. June €635K incl. doc 364214 (€277K SPA = 27% of Q1).\n"
    "Even June ex-SPA (~€358K) is ~1.8× Apr–May — something else moved in June too; confirm with them.\n\n"
    "PAUSE for their read on June — was SPA pull-forward, stock build, or real demand?\n\n"
    "Do NOT present this as 'problem solved' — bridge to GPS stretch as the full-year lever.",
    4,
)
cd = CategoryChartData()
cd.categories = ["Apr", "May", "Jun ex-SPA", "Jun SPA", "Q1 total"]
cd.add_series("€K", (211, 191, 358, 277, 1037))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, Inches(0.55), Inches(1.35), Inches(7.0), Inches(4.2), cd)
ch = gf.chart
ch.has_legend = True
ch.legend.position = 2
ch.legend.include_in_layout = False
pl = ch.plots[0]
pl.gap_width = 80
for sr in pl.series:
    sr.format.fill.solid()
    sr.format.fill.fore_color.rgb = RED if sr.name == "€K" else LIGHT_RED
body(
    s,
    [
        (0, "Q1 sales €1,037K", "— +38% vs budget, +29% vs prior year."),
        (0, "SPA order (doc 364214)", "= €277K — 27% of Q1 sales."),
        (0, "June ex-SPA still €358K", "— ~1.8× the Apr–May run-rate."),
        (0, "Apr–May baseline", "≈ €201K/month."),
    ],
    x=Inches(7.8),
    y=Inches(1.45),
    w=Inches(5.2),
    size=14,
)

# 5 SPA BASKET
s = content(
    "June SPA basket — what drove the quarter",
    "SPA programme ~50 PNs, ~€2.08M committed (12-month). Doc 364214 is the June billing event.\n\n"
    "Filters ~10% of SPA € but volume-heavy — ties to filter-mix conversation later.\n"
    "Other mechanical ~51% — dominated by NOx; remind them we want joint warranty review before fixing NOx price.\n\n"
    "Flexibility offer: 6-month programme, line-by-line or basket total.\n\n"
    "ASK: Which lines can they confirm today? NOx parked until warranty volume reconciled?",
    5,
)
add_table(s, SPA_CATS, Inches(0.55), Inches(1.35), Inches(7.2), [Inches(2.4), Inches(1.3), Inches(3.5)], bs=11, hs=11)
body(
    s,
    [
        (0, "Doc 364214", "= €277K — first SPA order in Q1."),
        (0, "Filters + wear parts", "meaningful share — links to GPS stretch."),
        (0, "NOx sensor", "— largest line; review warranty vs retail before final price."),
        (0, "EGR cooler/valve", "— genuine-only; defends grey imports."),
    ],
    x=Inches(8.0),
    y=Inches(1.45),
    w=Inches(5.0),
    size=13,
)

# 6 GPS STRETCH
s = content(
    "FY27 GPS stretch proposal",
    "COMMERCIAL ASK — be clear and calm.\n\n"
    "Stretch = +1.8pp on plan (36.5% → 38.3%). Purchase uplift 1.8% × €8.49M wallet ≈ +€153K on BP.\n"
    "€25K bonus at FY close if stretch GPS OR stretch BP (€3.25M) reached. Regular kickback €36K unchanged.\n\n"
    "They may ask 'why stretch if Q1 is +38%?' — Answer: Q1 is one quarter, SPA-heavy; stretch is full-year GPS discipline.\n\n"
    "If pushback: discuss pilot on filter genuine mix as concrete path to GPS (next slides).",
    6,
)
g = GPS_STRETCH
add_table(
    s,
    [
        ["Step", "GPS %", "vs prior"],
        ["FY26 actual", f"{g['gps_fy26']:.1f}%", "Starting point"],
        ["FY27 plan (base)", f"{g['gps_plan']:.1f}%", "+4.5pp"],
        ["FY27 stretch", f"{g['gps_stretch']:.1f}%", f"+{g['pp']:.1f}pp on plan"],
    ],
    Inches(0.55),
    Inches(1.35),
    Inches(5.8),
    [Inches(2.2), Inches(1.8), Inches(1.8)],
    bs=13,
    hs=12,
)
add_table(
    s,
    [
        ["Item", "Amount", "Notes"],
        ["BP FY27 (base)", f"€{g['bp_base_m']:.2f}M", "Reviewed plan"],
        ["+ GPS stretch", f"+€{g['stretch_eur_k']}K", f"+{g['pp']:.1f}pp × wallet"],
        ["Stretch BP FY27", f"€{g['stretch_bp_m']:.2f}M", "+4.9% vs base"],
        ["Regular kickback", f"€{g['kickback_k']}K", "Unchanged"],
        ["GPS stretch bonus", f"€{g['incentive_k']}K", "FY close if stretch met"],
    ],
    Inches(6.6),
    Inches(1.35),
    Inches(6.5),
    [Inches(2.3), Inches(1.5), Inches(2.7)],
    bs=12,
    hs=12,
)
txt(
    s,
    f"Stretch adds +{g['pp']:.1f}pp on FY27 GPS plan. "
    f"Uplift ≈ {g['pp']:.1f}% × max-spend wallet (€{g['wallet_m']:.2f}M). "
    f"€{g['incentive_k']}K bonus paid at FY close if stretch GPS ({g['gps_stretch']:.1f}%) or stretch BP (€{g['stretch_bp_m']:.2f}M) is reached.",
    Inches(0.55),
    Inches(5.95),
    Inches(12.2),
    Inches(0.55),
    size=11,
    color=GRAY,
)

# 7 SOR / RUSH / VOR
s = content(
    "Order type split — routine vs urgent",
    "Back-order snapshot (Jul 2026): 96% of open BO qty is SOR — routine, planable.\n"
    "RUSH/VOR small by qty (1.5% / 2.2%) but disproportionate in service perception.\n"
    "81% of open BO qty sits on SPA PNs — set expectations on lead times post-June SPA pull.\n\n"
    "ASK: Are urgent lines concentrated in filters/chassis? (matches fill-rate slide.)\n\n"
    "Internal: link to stock positioning — VOR in filters is a lever.",
    7,
)
cd2 = CategoryChartData()
cd2.categories = ["SOR", "VOR", "RUSH"]
cd2.add_series("Open BO qty %", (96.3, 2.2, 1.5))
gf2 = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.55), Inches(1.4), Inches(6.5), Inches(3.8), cd2)
ch2 = gf2.chart
ch2.has_legend = False
pl2 = ch2.plots[0]
pl2.has_data_labels = True
pl2.data_labels.number_format = '0.0"%"'
pl2.data_labels.font.size = Pt(12)
for sr in pl2.series:
    sr.format.fill.solid()
    sr.format.fill.fore_color.rgb = RED
body(
    s,
    [
        (0, "SOR dominates", "— 96% of open back-order quantity (routine)."),
        (0, "RUSH / VOR", "— small share but high service sensitivity."),
        (0, "SPA overlap", "— 81% of open qty on SPA part numbers."),
        (0, "Implication", "— plan lead times; monitor urgent lines separately."),
    ],
    x=Inches(7.5),
    y=Inches(1.45),
    w=Inches(5.5),
    size=14,
)

# 8 FILL RATE
s = content(
    "Service intensity — urgent orders & fill rate",
    "RUSH median ~1 day order-to-invoice vs SOR ~11 days — use if they raise service complaints.\n"
    "Fill rate 76–86% (Jul'25–May'26 BI trend) — don't over-claim; monitor urgent separately.\n\n"
    "VOR concentrates filters & chassis — stock positioning conversation, not blame.\n\n"
    "If they cite June SPA delays: acknowledge, tie to SOR backlog on SPA lines.",
    8,
)
body(
    s,
    [
        (0, "RUSH fulfils faster", "(median ~1 day order-to-invoice) vs SOR ~11 days."),
        (0, "UTI fill rate 76–86%", "(Jul'25–May'26 BI trend) — track urgent lines separately."),
        (0, "VOR concentrates", "in filters & chassis families — stock positioning lever."),
        (0, "Link to prior slide", "— routine backlog vs urgent exceptions."),
    ],
    y=Inches(1.5),
    size=17,
    gap0=14,
)

# 9 GPS vs PMS BRIDGE
s = content(
    "GPS & PMS — in plain terms",
    "CRITICAL BRIDGE SLIDE — prevents mixed messages.\n\n"
    "GPS = broad wallet. PMS = interval wear parts. High filter cover = they buy from us; low genuine % = mix opportunity.\n"
    "Brake/clutch capture % needs their mileage data — not a simple price lever. Brakes already ~100% genuine from ISZE.\n\n"
    "If confused: 'We're not saying you fail on brakes — we're sizing total demand vs what flows through ISZE invoices.'\n\n"
    "FY2026 Q1 UTI billing anomaly (zero lines) — do NOT show FY26 PMS; stick to FY2025 actuals.",
    9,
)
rect(s, Inches(0.55), Inches(1.35), Inches(5.9), Inches(4.8), LGRAY, rounded=True)
txt(s, "GPS", Inches(0.75), Inches(1.5), Inches(5.5), Inches(0.4), size=16, bold=True, color=RED)
txt(
    s,
    "Genuine Parts Share\n\n"
    "Every genuine Isuzu PN sold vs what the market could buy genuine.\n"
    "Broad health check — full parts basket.",
    Inches(0.75),
    Inches(1.95),
    Inches(5.5),
    Inches(1.5),
    size=13,
)
rect(s, Inches(6.85), Inches(1.35), Inches(5.9), Inches(4.8), LGRAY, rounded=True)
txt(s, "PMS coverage", Inches(7.05), Inches(1.5), Inches(5.5), Inches(0.4), size=16, bold=True, color=RED)
txt(
    s,
    "Periodic maintenance capture\n\n"
    "Interval-driven items only — filters, brake pads, clutch kits.\n"
    "Focused diagnostic — where scheduled demand leaks away.",
    Inches(7.05),
    Inches(1.95),
    Inches(5.5),
    Inches(1.5),
    size=13,
)
txt(
    s,
    "High PMS cover on filters = you buy from us.  Low genuine % on those filters = opportunity inside the relationship.\n"
    "Brake/clutch gaps need your workshop data to size — not a price lever alone.",
    Inches(0.55),
    Inches(6.35),
    Inches(12.2),
    Inches(0.75),
    size=14,
    bold=True,
    color=NAVY,
)

# 10 FILTER PEER
s = content(
    "Filters — UTI buys BVP where ITUK buys genuine",
    "STRONGEST EVIDENCE-BASED COMMERCIAL SLIDE.\n\n"
    "UTI is 89% genuine overall — NOT a 'non-genuine account'. Conversation is filters inside BVP offer.\n"
    "Where BVP alternative exists, UTI takes BVP 82% vs ITUK 21%.\n\n"
    "Prize: fuel filter ~€54K + air ~€11K revenue if BVP volumes move to network genuine pricing (~€65K/yr).\n"
    "EXPLICITLY exclude oil filter — genuine element cheaper (~€5 vs BVP ~€10); converting loses ~€23K.\n\n"
    "ASK: Would they pilot genuine fuel + air on SPA for fleet/dealer channel?\n\n"
    "Source: CY2025 billing + BVP catalog crossref (authoritative). Do NOT cite old dimension-based figures.",
    10,
)
add_table(s, FILTER_PEER, Inches(0.55), Inches(1.45), Inches(6.0), [Inches(2.2), Inches(1.9), Inches(1.9)], bs=13, hs=12)
# simple peer bars
for i, (lab, uti, ituk) in enumerate([("Fuel", 0, 80), ("Air", 0, 85), ("Oil", 0, 71)]):
    yb = Inches(1.55) + i * Inches(1.15)
    txt(s, lab, Inches(7.0), yb, Inches(0.9), Inches(0.35), size=12, bold=True)
    rect(s, Inches(7.9), yb + Inches(0.08), Inches(2.0), Inches(0.22), MGRAY)
    rect(s, Inches(7.9), yb + Inches(0.08), Emu(int(Inches(2.0) * ituk / 100)), Inches(0.22), RED)
    txt(s, f"ITUK {ituk}%", Inches(10.0), yb, Inches(1.2), Inches(0.35), size=11, color=GRAY)
    rect(s, Inches(11.3), yb + Inches(0.08), Inches(1.5), Inches(0.22), MGRAY)
    txt(s, "UTI ~0%", Inches(11.3), yb + Inches(0.35), Inches(1.5), Inches(0.3), size=10, color=GRAY)
takeaway_box(
    s,
    [
        "Opportunity ≈ €65K/yr revenue on fuel + air (excl. oil).",
        "Brake pad already ~100% genuine — not the filter story.",
        "ITUK proves genuine filter sales hold in a comparable network.",
    ],
    y=Inches(5.75),
)

# 11 PMS SUMMARY
s = content(
    "PMS capture summary — FY2025 actuals",
    "Present as DIRECTIONAL. Intervals from IML v7 (50,000 km/yr assumed — not Israel-verified).\n\n"
    "Clutch = one family (20.3%) — kit PN for nearly every job; do NOT show 4 subcategories.\n"
    "€ gaps are CEILINGS to 100% modeled demand — not sales targets.\n\n"
    "ASK directly: Why did oil filter & clutch kit volumes fall in FY2026 while fuel/air grew?\n"
    "Possible answers: fleet channel, UTI Parts, stock, programme timing.\n\n"
    "Do not argue brake gap hard — pads are genuine; gap is model denominator.",
    11,
)
add_table(s, PMS_FY25, Inches(0.55), Inches(1.35), Inches(7.0), [Inches(2.5), Inches(2.2), Inches(2.3)], bs=12, hs=12)
body(
    s,
    [
        (0, "Capture range", "~20% (clutch family) to ~75% (fuel filter)."),
        (0, "Largest EUR gaps", "clutch family, brake pad, air filter."),
        (0, "Filters trend", "air & fuel improving; oil & clutch kit down in FY2026."),
        (0, "Assumptions", "mileage & clutch parc share — need UTI calibration."),
    ],
    x=Inches(7.8),
    y=Inches(1.45),
    w=Inches(5.2),
    size=13,
)
txt(
    s,
    "* Clutch scored as one family. FY2025 actuals. FY2026 Q1 billing anomaly — not shown.",
    Inches(0.55),
    Inches(6.55),
    Inches(12),
    Inches(0.35),
    size=9,
    color=MGRAY,
)

# 12 FLEET
s = content(
    "UTI fleet operations — mutual learning on R&M",
    "EXPLORATORY — not on the commercial hit list. Position as mutual learning.\n\n"
    "UTI fleet company may explain: better parc data, workshop sourcing (UTI Parts), FY2026 volume moves.\n\n"
    "Pick 4–5 questions live; rest in backup. Listen more than talk.\n\n"
    "Offer back: ITUK interval benchmarks once calibrated, SPA on wear lines tied to fleet commitment, "
    "joint capture view at workshop level if they share volumes.\n\n"
    "ISZE interest: how fleet R&M planning works — applicable to other distributors.",
    12,
)
body(
    s,
    [
        (0, "Parc & planning", ""),
        (1, "", "Fleet pool vs dealer-sold parc? Active vs registered?"),
        (1, "", "Km-based or calendar service? Typical km/year by segment?"),
        (0, "Parts sourcing", ""),
        (1, "", "Fleet workshops: genuine / BVP / UTI Parts split by category?"),
        (1, "", "What triggers non-Isuzu on wear items — price, lead time, policy?"),
        (0, "Data exchange", ""),
        (1, "", "Share anonymised service intervals to calibrate our PMS model?"),
        (1, "", "Can fleet volumes explain FY2026 oil filter & clutch kit movement?"),
    ],
    y=Inches(1.35),
    size=15,
    gap0=8,
)
txt(
    s,
    "Fleet parc  →  Workshop schedule  →  Parts source (Genuine / BVP / UTI Parts)\n"
    "ISZE visibility today: distributor billing only",
    Inches(0.55),
    Inches(5.9),
    Inches(12.2),
    Inches(0.7),
    size=12,
    color=NAVY,
    italic=True,
)

# 13 UTI PARTS
s = content(
    "UTI Parts — where we can compete",
    "Frame carefully: we only see ISZE invoices. UTI Parts + local sourcing sits outside our data.\n\n"
    "Win-back is conditional: delivered price (SPA) + lead time + MOQ.\n\n"
    "Oil: don't push genuine — compete on BVP service/convenience.\n"
    "Fuel/air: genuine at programme price if they trial.\n"
    "Brake/clutch: leakage may be non-ISZE — fleet disclosure helps.\n\n"
    "ASK: scope of UTI Parts (categories), share of maintenance spend, workshop-only vs dealer network?\n\n"
    "Tie to GPS stretch: migrating contestable volume to ISZE helps both sides.",
    13,
)
add_table(
    s,
    [
        ["Category", "ISZE today", "Win-back lever"],
        ["Fuel / air filters", "BVP from ISZE", "SPA + genuine mix like ITUK"],
        ["Oil filter", "BVP from ISZE", "Keep BVP — genuine price wrong"],
        ["Brake / clutch", "Genuine from ISZE", "Fleet/workshop disclosure + programme"],
        ["Fluids / small parts", "Unknown", "Lower priority"],
    ],
    Inches(0.55),
    Inches(1.4),
    Inches(12.2),
    [Inches(2.4), Inches(3.2), Inches(6.6)],
    bs=12,
    hs=12,
)
txt(
    s,
    "We see Genuine and BVP in billing. Help us size UTI Parts / other — if we are competitive, we want to earn the volume back.",
    Inches(0.55),
    Inches(5.85),
    Inches(12.2),
    Inches(0.55),
    size=13,
    color=BLACK,
)

# 14 NEXT STEPS
s = content(
    "Next steps",
    "Read each line aloud and confirm owner + date. Don't leave vague.\n\n"
    "UIO is gating item for every model — polite but firm on timing.\n"
    "SPA: confirm lines, NOx warranty joint review, 6 vs 12 months.\n"
    "Filters: propose pilot — genuine fuel + air at SPA; oil stays BVP.\n"
    "Fleet session: optional follow-up with fleet ops contact.\n\n"
    "Thank them. Offer to send deck + PMS appendix after meeting.",
    14,
)
body(
    s,
    [
        (0, "UIO", "— UTI active parc 31/12/2025 (N/F split) by agreed date"),
        (0, "SPA", "— confirm basket lines; joint NOx warranty review; 6- vs 12-month term"),
        (0, "Filter programme", "— pilot genuine fuel + air at programme price; oil stays BVP"),
        (0, "PMS calibration", "— share km/year, brake interval, in-service % for Israel"),
        (0, "Fleet / UTI Parts", "— follow-up session with fleet & parts leads if useful"),
    ],
    y=Inches(1.45),
    size=18,
    gap0=16,
)

# 15 APPENDIX DIVIDER
s = content(
    "Appendix — PMS detail (optional)",
    "Use only if they want depth or challenge the summary. Skip in a 45-min slot.\n\n"
    "Slide 16: filter trends. Slide 17: methodology assumptions.\n\n"
    "If they challenge €555K gap: repeat ceiling framing + assumption layer.",
    15,
)
txt(
    s,
    "Additional PMS charts available in UTI_PMS_Evolution.html (offline).\n"
    "Filters · brake & clutch · revenue by category · units sold — on request.",
    Inches(0.6),
    Inches(1.6),
    Inches(12),
    Inches(2),
    size=18,
    color=GRAY,
)

# 16 APPENDIX FILTERS
s = content(
    "Appendix — Filters (FY2024–FY2026)",
    "Air filter strongest trend: 36% → 48% → 58% cover.\n"
    "Fuel filter: 49% → 72% → 75%.\n"
    "Oil filter exception: peaked 55% FY2025, dropped to 31% FY2026 (6,976 → 4,046 units).\n\n"
    "ASK UTI: why oil alone reversed while fuel & air kept climbing?",
    16,
)
body(
    s,
    [
        (0, "Air filter", "— 36% → 48% → 58% cover; consistent improvement."),
        (0, "Fuel filter", "— 49% → 72% → 75%."),
        (0, "Oil filter", "— 55% FY2025 then 31% FY2026; volume −42%."),
        (0, "Model", "IML v7 — 40,000 km interval, 1.25 services/yr."),
    ],
    y=Inches(1.45),
    size=16,
)

# 17 APPENDIX METHODOLOGY
s = content(
    "Appendix — Methodology & assumptions",
    "Transparency builds trust. Wear-part factors NOT confirmed for Israel.\n"
    "50,000 km/yr and clutch parc share from another market — flagged, not hidden.\n\n"
    "Capture % directional until UTI confirms intervals.\n\n"
    "Underlying invoiced sales are solid — denominators are the assumption layer.",
    17,
)
body(
    s,
    [
        (0, "Wear-part factors", "not confirmed for Israel — sales actuals are solid."),
        (0, "50,000 km/yr mileage", "carried from ITUK convention — needs UTI input."),
        (0, "Clutch-equipped parc share", "assumed, not UTI-measured."),
        (0, "Read capture % as directional", "until service-interval ratios confirmed."),
    ],
    y=Inches(1.45),
    size=16,
    gap0=12,
)

# 18 CLOSE
closing(
    "CLOSING\n"
    "Thank you for the partnership. Summarise 3 commitments (UIO, SPA, filter pilot).\n"
    "Leave the room with dates, not intentions."
)

# ── save ───────────────────────────────────────────────────────────────────
OUT_NAMES = [
    OUT_DIR / "UTI_presentation_DRAFT_Jul2026.pptx",
    Path(r"c:\Users\jerom\Downloads\UTI_presentation_DRAFT_Jul2026.pptx"),
]
saved = []
for out in OUT_NAMES:
    try:
        prs.save(str(out))
        saved.append(str(out))
        print("saved", out)
    except PermissionError:
        alt = out.with_name(out.stem + "_NEW.pptx")
        prs.save(str(alt))
        saved.append(str(alt))
        print("LOCKED - saved", alt)

print(f"Slides: {len(prs.slides)}")
print("Speaker notes on every slide.")
