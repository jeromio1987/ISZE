"""Frozen pre-Pass-1 builder. Writes ORIGINAL.pptx only. Never write DRAFT.pptx."""
from __future__ import annotations

import os
import sys

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE"),
                   r"04_tools\ppt_template_v2")
sys.path.insert(0, TPL)

import isze_chart_theme as ct  # noqa: E402
import isze_deck_builder as db  # noqa: E402

OUT = os.path.join(
    os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE"),
    r"09_meetings\ISZE_PMS_How_We_Proceed_ORIGINAL.pptx",
)
CHART_DIR = os.path.join(HERE, "_charts")
os.makedirs(CHART_DIR, exist_ok=True)

NAVY = RGBColor(0x15, 0x23, 0x3C)
PAPER = RGBColor(0xF7, 0xF4, 0xEE)
GREEN = RGBColor(0x1D, 0x9E, 0x75)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
WHITE = db.WHITE
BLACK = db.BLACK
GRAY = db.GRAY
RED = db.RED
GRAY_BG = db.GRAY_BG


def bullets(slide, items, left, top, width, height, size=15):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        p.line_spacing = 1.15
        mark = p.add_run()
        mark.text = "- "
        mark.font.size = Pt(size)
        mark.font.bold = True
        mark.font.color.rgb = RED
        mark.font.name = "Calibri"
        body = p.add_run()
        body.text = item
        body.font.size = Pt(size)
        body.font.color.rgb = BLACK
        body.font.name = "Calibri"
    return box


def card(slide, left, top, width, height, fill, title, body, title_color=WHITE, body_color=WHITE):
    db.rect(slide, left, top, width, height, fill)
    db.txt(slide, title, left + Inches(0.16), top + Inches(0.12), width - Inches(0.28),
           Inches(0.38), size=16, bold=True, color=title_color)
    db.txt(slide, body, left + Inches(0.16), top + Inches(0.50), width - Inches(0.28),
           height - Inches(0.62), size=13, color=body_color)


def kpi(slide, left, top, width, height, label, value, sub, accent=RED):
    db.rect(slide, left, top, width, Inches(0.08), accent)
    db.rect(slide, left, top + Inches(0.08), width, height - Inches(0.08), PAPER)
    db.txt(slide, label, left + Inches(0.14), top + Inches(0.16), width - Inches(0.24),
           Inches(0.28), size=11, bold=True, color=GRAY)
    db.txt(slide, value, left + Inches(0.14), top + Inches(0.42), width - Inches(0.24),
           Inches(0.55), size=32, bold=True, color=accent)
    db.txt(slide, sub, left + Inches(0.14), top + Inches(0.98), width - Inches(0.24),
           Inches(0.40), size=12, color=GRAY)


def fill_table(slide, data, left, top, width, height, col_w=None):
    rows, cols = len(data), len(data[0])
    tbl = slide.shapes.add_table(rows, cols, left, top, width, height).table
    if col_w:
        for i, w in enumerate(col_w):
            tbl.columns[i].width = w
    else:
        each = int(width / cols)
        for i in range(cols):
            tbl.columns[i].width = each
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = str(val)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.font.size = Pt(10 if r == 0 else 12)
            p.font.bold = r == 0
            p.font.name = "Calibri"
            p.font.color.rgb = WHITE if r == 0 else BLACK
            p.alignment = PP_ALIGN.LEFT if c < 3 else PP_ALIGN.RIGHT
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = NAVY
            elif r % 2:
                cell.fill.fore_color.rgb = PAPER
            else:
                cell.fill.fore_color.rgb = WHITE
    return tbl


def lead(slide, text):
    db.rect(slide, Inches(0.32), Inches(1.22), Inches(12.70), Inches(0.72), NAVY)
    db.txt(slide, text, Inches(0.48), Inches(1.28), Inches(12.40), Inches(0.60),
           size=15, color=WHITE)


def cover_bar(cats, vals, path):
    """Horizontal bars. Air is the red miss."""
    import matplotlib.pyplot as plt

    colors = []
    for c in cats:
        if c == "Air":
            colors.append(ct.RED)
        elif c == "Fuel":
            colors.append(ct.CHARCOAL)
        else:
            colors.append(ct.GRAY_MED)
    fig, ax = plt.subplots(figsize=(10.4, 4.4), dpi=200)
    fig.patch.set_facecolor(ct.WHITE)
    ax.set_facecolor(ct.WHITE)
    y = list(range(len(cats)))[::-1]
    ax.barh(y, vals[::-1], color=list(reversed(colors)), height=0.62, zorder=3)
    for yi, v in zip(y, vals[::-1]):
        ax.annotate(f"{v:.0f}%", (v, yi), xytext=(6, 0), textcoords="offset points",
                    va="center", ha="left", fontsize=11, color=ct.CHARCOAL, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(list(reversed(cats)), fontsize=12, color=ct.CHARCOAL)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Cover %  (CY2025, N75, IML service schedule)", fontsize=10, color=ct.GRAY)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(ct.GRAY_LIGHT)
    ax.tick_params(axis="x", colors=ct.GRAY, length=0)
    ax.xaxis.grid(True, color=ct.GRAY_BG, linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("N75 cover vs expected demand", fontsize=13, color=ct.CHARCOAL,
                 loc="left", fontweight="bold", pad=10)
    fig.tight_layout(pad=0.6)
    fig.savefig(path, dpi=200, facecolor=ct.WHITE)
    plt.close(fig)


def build():
    chart = os.path.join(CHART_DIR, "n75_cover.png")
    cover_bar(["Fuel", "Brake", "Oil", "Air", "Clutch"], [94, 62, 40, 19, 11], chart)

    prs = db.new_presentation()

    # 1 cover
    db.build_cover(
        prs,
        title="How we proceed on PMS\nfrom the parts side",
        subtitle="Draft  ·  complements the ITUK operating model  ·  N75  ·  18 August 2026",
        eyebrow="ISZE  ·  VEHICLE PARTS  ·  DRAFT",
    )

    # 2 opening
    s = db.build_content(prs, "Your model stays the head story", eyebrow="Opening", page_no=2)
    lead(s, "Uptime is the customer story. Parts attaches the right set on a visit that already happens.")
    card(s, Inches(0.32), Inches(2.14), Inches(6.15), Inches(4.10), NAVY,
         "ITUK already said",
         "N75 events. Oil + fuel + air on the job. Inspect brakes. Conversion and fill, not discount as the KPI. N35 later. Connected later.")
    card(s, Inches(6.70), Inches(2.14), Inches(6.32), Inches(4.10), PAPER,
         "What parts Europe adds",
         "Cover %. Filter pack. BVP promotion from August. SPA we price now. Clutch stays in at 47% manuals. If ISZE and ITUK cannot close the discount, IML can join.",
         title_color=NAVY, body_color=BLACK)

    # 3 timeline
    s = db.build_content(prs, "How we got here", eyebrow="Path", page_no=3)
    lead(s, "March to August is one programme. This week we have both halves.")
    steps = [
        ("Mar", "Kick-off. Frequencies and target items. VIN format not available. UIO, CBU and R&M instead."),
        ("Apr", "UK visit. N75 first. Air and brake as headlines. Oil and fuel as the 40,000 km pack. Parc 9,359."),
        ("Jun", "EU conference. SPA discussion. Sales prices requested so a SPA can be priced."),
        ("Jul", "Japan hour locked. ISZE to take the parts lead on Tuesday."),
        ("13 Aug", "Your pack plus three ISZE options. You asked for this draft in Japan."),
    ]
    w = Inches(2.40)
    for i, (when, what) in enumerate(steps):
        left = Inches(0.32) + i * Inches(2.56)
        db.rect(s, left, Inches(2.16), w, Inches(0.08), RED)
        db.rect(s, left, Inches(2.24), w, Inches(4.00), PAPER)
        db.txt(s, when, left + Inches(0.12), Inches(2.36), w - Inches(0.20), Inches(0.36),
               size=14, bold=True, color=RED)
        db.txt(s, what, left + Inches(0.12), Inches(2.78), w - Inches(0.20), Inches(3.30),
               size=13, color=BLACK)

    # 4 cover %
    s = db.build_content(prs, "N75 cover %  ·  clutch stays in", eyebrow="Where the miss is", page_no=4)
    kpi(s, Inches(0.32), Inches(1.22), Inches(4.10), Inches(1.50), "AIR  THE MISS", "19%", "2,226 / 11,699 expected")
    kpi(s, Inches(4.62), Inches(1.22), Inches(4.10), Inches(1.50), "CLUTCH  47% MANUALS", "11%", "243 / 2,199 expected", accent=NAVY)
    kpi(s, Inches(8.92), Inches(1.22), Inches(4.10), Inches(1.50), "BRAKE  CONVERT", "62%", "2,902 / 4,680 expected", accent=NAVY)
    db.add_picture_fit(s, chart, Inches(0.32), Inches(2.88), Inches(8.10), Inches(3.75))
    db.rect(s, Inches(8.60), Inches(2.88), Inches(4.42), Inches(3.75), PAPER)
    db.txt(s, "What this means", Inches(8.78), Inches(3.00), Inches(4.06), Inches(0.32),
           size=13, bold=True, color=RED)
    bullets(s, [
        "Air is the miss. Put it on the same visit as oil and fuel.",
        "Fuel is already 94%. Keep it in the pack.",
        "Brake: inspect and convert. R90 pad 8982447940 is orderable.",
        "Oil stays in the pack. Not the campaign KPI.",
        "Clutch stays in at 47% manuals for this round.",
    ], Inches(8.78), Inches(3.36), Inches(4.06), Inches(3.10), size=13)

    # 5 part numbers + % + qty
    s = db.build_content(prs, "N75 lines  ·  cover %, qty, list price", eyebrow="CY2025 ISZE to ITUK", page_no=5)
    lead(s, "Same IML schedule as the cover bars. Qty is what we billed. List is ISZE list EUR.")
    fill_table(
        s,
        [
            ["Item", "Cover", "Genuine PN", "2025 qty", "List EUR", "BVP PN", "2025 qty", "List EUR"],
            ["Oil", "40%", "8983282070", "371", "14.45", "1876102890", "2,909", "9.96"],
            ["Fuel", "94%", "8975425400", "2,005", "12.56", "1876102860", "0", "8.05"],
            ["Air", "19%", "8981772710", "1,403", "31.36", "5876102500", "0", "17.49"],
            ["Brake pad", "62%", "8982447940", "2,282", "89.11", "no twin", "-", "-"],
            ["Clutch disc 4HK1", "11% family", "8981649171", "47", "84.47", "see kit mix", "-", "-"],
            ["Clutch PP 4HK1", "11% family", "8970388314", "54", "120.75", "5876101040", "14", "89.22"],
        ],
        Inches(0.32), Inches(2.10), Inches(12.70), Inches(3.55),
        col_w=[Inches(1.70), Inches(1.20), Inches(1.55), Inches(1.10), Inches(1.15),
               Inches(1.70), Inches(1.15), Inches(1.15)],
    )
    db.txt(
        s,
        "Oil BVP already outsells genuine (2,909 vs 371). Fuel BVP and air BVP did not move in 2025. Brake pad 8982447940 is orderable. Clutch % uses 47% manuals (expected 2,199 kits).",
        Inches(0.32), Inches(5.80), Inches(12.70), Inches(0.70), size=13, color=GRAY,
    )

    # 6 one visit in euros
    s = db.build_content(prs, "One 40,000 km visit, in euros", eyebrow="Filter pack at ISZE list", page_no=6)
    lead(s, "This is the pack on the job card. Not a discount number. Three ways to price the same three filters.")
    card(s, Inches(0.32), Inches(2.14), Inches(4.10), Inches(3.35), NAVY,
         "Genuine pack  EUR 58.37",
         "Oil 8983282070 at 14.45. Fuel 8975425400 at 12.56. Air 8981772710 at 31.36. Fuel already attaches. Air is the miss on this set.")
    card(s, Inches(4.62), Inches(2.14), Inches(4.10), Inches(3.35), GREEN,
         "Oil BVP today  EUR 53.88",
         "Oil 1876102890 at 9.96 (already selling). Fuel genuine 12.56. Air genuine 31.36. August move: keep promoting the oil BVP that already moves.")
    card(s, Inches(8.92), Inches(2.14), Inches(4.10), Inches(3.35), BLUE,
         "If ITUK orders BVP  EUR 35.50",
         "Oil 9.96 + fuel 1876102860 at 8.05 (qty 0) + air 5876102500 at 17.49 (qty 0). 39% below genuine. Only if they stock the zeros.")
    db.txt(
        s,
        "Brake on the same visit: pad 8982447940 list 89.11 EUR (2,282 billed in 2025). If genuine still needs more discount after BVP, that is the SPA. If ITUK and ISZE cannot close it, IML can join.",
        Inches(0.32), Inches(5.65), Inches(12.70), Inches(0.70), size=14, color=BLACK,
    )

    # 7 three levers
    s = db.build_content(prs, "Three levers  ·  BVP this month, SPA now", eyebrow="Parts Europe", page_no=7)
    lead(s, "We do not wait for October to start pricing.")
    card(s, Inches(0.32), Inches(2.14), Inches(4.10), Inches(4.10), GREEN,
         "1  BVP  ·  August",
         "Where a twin exists, promote it now. Live oil BVP 1876102890 already moves. Catalogue twins with zero UK sales only go on the poster if ITUK orders them.")
    card(s, Inches(4.62), Inches(2.14), Inches(4.10), Inches(4.10), BLUE,
         "2  SPA  ·  now",
         "Genuine air and brake, and clutch if we keep it in. We price with ITUK now, not after Japan. If the level is not enough, IML can join.")
    card(s, Inches(8.92), Inches(2.14), Inches(4.10), Inches(4.10), NAVY,
         "3  Filter pack",
         "One N75 kit: oil + fuel + air. Fuel 94%, air 19%. That is how air rides on an event that already exists. R90 pad 8982447940 on the brake side.")

    # 6 price ladder
    s = db.build_content(prs, "How we get the price down", eyebrow="Discount ladder", page_no=8)
    lead(s, "BVP first. Then SPA with ITUK. If we cannot agree the level, IML joins and we share it three ways.")
    db.rect(s, Inches(0.32), Inches(2.12), Inches(12.70), Inches(0.70), NAVY)
    db.txt(s, "Need more price on this job? Walk the ladder. Do not start with a three-party SPA.",
           Inches(0.50), Inches(2.22), Inches(12.34), Inches(0.50), size=16, color=WHITE)
    card(s, Inches(0.32), Inches(3.00), Inches(6.15), Inches(1.55), GREEN,
         "BVP twin exists",
         "Promote BVP. That is the August move. No extra SPA until the twin is on the shelf.")
    card(s, Inches(6.87), Inches(3.00), Inches(6.15), Inches(1.55), BLUE,
         "Genuine needs SPA",
         "ISZE prices it with ITUK now. Dealer quotes the set on the event.")
    db.rect(s, Inches(0.32), Inches(4.72), Inches(12.70), Inches(0.70), RED)
    db.txt(s, "If ITUK and ISZE cannot close the level: IML joins. Three wallets, one conversion.",
           Inches(0.50), Inches(4.82), Inches(12.34), Inches(0.50), size=16, color=WHITE)
    w = Inches(3.90)
    parties = [
        ("ISZE", "Europe parts", "SPA wallet + pack BOM"),
        ("ITUK", "UK distributor", "Dealer price + stock"),
        ("IML", "If still short", "Third share of the discount"),
    ]
    for i, (nm, who, what) in enumerate(parties):
        left = Inches(0.32) + i * Inches(4.32)
        db.rect(s, left, Inches(5.58), w, Inches(0.92), PAPER)
        db.txt(s, nm, left + Inches(0.14), Inches(5.62), w - Inches(0.24), Inches(0.32),
               size=16, bold=True, color=NAVY)
        db.txt(s, f"{who}. {what}", left + Inches(0.14), Inches(5.94), w - Inches(0.24),
               Inches(0.48), size=12, color=GRAY)

    # 7 proceed
    s = db.build_content(prs, "How we proceed", eyebrow="Timeline", page_no=9)
    lead(s, "Mark this up in Japan. Lock the ladder on Tuesday. BVP already this month.")
    times = [
        ("August", "Promote live BVP. Start SPA numbers with ITUK."),
        ("Tue 18 Aug", "Lock pack, SPA lines, BVP order or leave, IML-join rule, clutch on 47%."),
        ("September", "Pack BOM, SPA paper, R90 pad order, bulletin, stock rule."),
        ("October", "N75 uptime campaign. Pack on the visit. Brake convert. Clutch in the model."),
        ("Nov to Dec", "Air attach %, brake accept, clutch kits vs 2,199, pack fill. Then N35."),
    ]
    w = Inches(2.40)
    for i, (when, what) in enumerate(times):
        left = Inches(0.32) + i * Inches(2.56)
        db.rect(s, left, Inches(2.16), w, Inches(0.08), RED)
        db.rect(s, left, Inches(2.24), w, Inches(3.55), PAPER)
        db.txt(s, when, left + Inches(0.12), Inches(2.36), w - Inches(0.20), Inches(0.40),
               size=14, bold=True, color=RED)
        db.txt(s, what, left + Inches(0.12), Inches(2.82), w - Inches(0.20), Inches(2.80),
               size=13, color=BLACK)
    db.txt(s, "Not this round: N35 as the launch, connected / odometer, oil as the headline KPI.",
           Inches(0.32), Inches(5.95), Inches(12.70), Inches(0.40), size=13, color=GRAY)

    # 8 asks
    s = db.build_content(prs, "Five answers so the hour can close", eyebrow="Tuesday", page_no=10)
    lead(s, "If we leave with these, September has a job.")
    asks = [
        "BVP now. Promote live oil BVP from August. Zero-sales twins (air 5876102500, fuel 1876102860): order, or leave off the poster?",
        "SPA now. Which genuine air / brake / clutch lines do we price with ITUK this month?",
        "IML join rule. If ITUK and ISZE cannot agree the SPA level, IML can share the discount. Yes?",
        "Pack. One N75 kit (oil + fuel + air) on existing events. R90 pad 8982447940 is orderable.",
        "Clutch. Keep it in at 47% manuals (expected 2,199). VIN later only refines the %.",
    ]
    for i, line in enumerate(asks):
        top = Inches(2.12) + i * Inches(0.78)
        db.rect(s, Inches(0.32), top, Inches(0.55), Inches(0.68), RED)
        db.txt(s, str(i + 1), Inches(0.32), top + Inches(0.12), Inches(0.55), Inches(0.46),
               size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        db.rect(s, Inches(0.95), top, Inches(12.07), Inches(0.68), PAPER)
        db.txt(s, line, Inches(1.12), top + Inches(0.10), Inches(11.75), Inches(0.50),
               size=15, color=BLACK)

    db.build_closing(prs)
    prs.save(OUT)
    root_copy = os.path.join(
        os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE"),
        "ISZE_PMS_How_We_Proceed_ORIGINAL.pptx",
    )
    try:
        import shutil
        shutil.copy2(OUT, root_copy)
        print("copied", root_copy)
    except OSError as e:
        print("root copy skipped:", e)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
