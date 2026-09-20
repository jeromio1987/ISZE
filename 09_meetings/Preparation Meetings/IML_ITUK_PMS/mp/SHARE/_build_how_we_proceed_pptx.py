"""Build ISZE PMS complementary draft PPTX. No DAF. shared language. Never write ORIGINAL.pptx."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
TPL = os.path.join(ROOT, r"04_tools\ppt_template_v2")
sys.path.insert(0, TPL)

import isze_chart_theme as ct  # noqa: E402
import isze_deck_builder as db  # noqa: E402

OUT = os.path.join(ROOT, r"09_meetings\ISZE_PMS_How_We_Proceed_DRAFT.pptx")
OUT_ROOT = os.path.join(ROOT, "ISZE_PMS_How_We_Proceed_DRAFT.pptx")
CHART_DIR = os.path.join(HERE, "_charts")
os.makedirs(CHART_DIR, exist_ok=True)
PPT_EXE = r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"
PHOTO_SRC = os.path.join(HERE, "assets", "P700_Isuzu_Motors_Nseries_2023.jpg")

WHITE = db.WHITE
BLACK = db.BLACK
RED = db.RED
CHARCOAL = BLACK
NAVY = RGBColor(0x15, 0x23, 0x3C)
INK = RGBColor(0x22, 0x22, 0x22)
GRAY_DK = RGBColor(0x5A, 0x5A, 0x5A)
GRAY_MID = RGBColor(0x8C, 0x8C, 0x8C)

# Locked 1% on all ITUK PMS parts, ITUK to dealer, calendar 2025.
# Valued euro = dealer qty x ISZE ASP to ITUK. Not a dealer invoice.
ONE_PCT_UNITS = 368
ONE_PCT_EUR = 7530
TOTAL_UNITS = 36843
TOTAL_EUR = 752982

SLIDE_COUNT = 12
# Working assumption for draft back slides only: ITUK price to dealers = buy-in x 1.40.
ITUK_MARKUP = 1.40

# Locked list / aftermarket euros. Do not invent. Projected = ISZE x 1.40.
OIL_G, FUEL_G, AIR_G = 14.45, 12.56, 31.36
OIL_B, FUEL_B, AIR_B = 9.96, 8.05, 17.49
SET_G, SET_TODAY, SET_B = 58.37, 53.88, 35.50
PAD_ISZE, PAD_AM = 89.11, 46.12
CLUTCH_DISC_ISZE, CLUTCH_DISC_AM = 84.47, 284.0
KIT_ISZE, GEN_PIECE_ISZE = 194.69, 282.08


def eur(n, decimals=2):
    return f"EUR {n:,.{decimals}f}"


def proj(n):
    return round(n * ITUK_MARKUP, 2)


def outline(slide, mso, left, top, width, height, color=CHARCOAL, weight=1.5):
    sh = slide.shapes.add_shape(mso, left, top, width, height)
    sh.fill.background()
    sh.line.color.rgb = color
    sh.line.width = Pt(weight)
    return sh


def filled(slide, mso, left, top, width, height, color):
    sh = slide.shapes.add_shape(mso, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


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
        mark.font.color.rgb = CHARCOAL
        mark.font.name = "Calibri"
        body = p.add_run()
        body.text = item
        body.font.size = Pt(size)
        body.font.color.rgb = BLACK
        body.font.name = "Calibri"
    return box


def card(slide, left, top, width, height, title, body, body_size=14):
    """White card. Charcoal rule. No grey wash."""
    db.rect(slide, left, top, width, Inches(0.06), CHARCOAL)
    outline(slide, MSO_SHAPE.RECTANGLE, left, top + Inches(0.06), width, height - Inches(0.06), CHARCOAL, 0.75)
    db.txt(
        slide, title, left + Inches(0.18), top + Inches(0.16), width - Inches(0.32),
        Inches(0.40), size=15, bold=True, color=CHARCOAL,
    )
    db.txt(
        slide, body, left + Inches(0.18), top + Inches(0.56), width - Inches(0.32),
        height - Inches(0.72), size=body_size, color=BLACK,
    )


def content_slide(prs, title, eyebrow, page_no, draft=False):
    s = db.blank_slide(prs)
    db.set_white_bg(s)
    db.add_logo(s)
    db.add_footer_bar(s)
    label = ("DRAFT  ·  " + eyebrow) if draft else eyebrow
    db.txt(s, label.upper(), Inches(0.32), Inches(0.22), Inches(10.4), Inches(0.28),
           size=11, bold=True, color=CHARCOAL)
    if draft:
        db.txt(
            s, "DRAFT", Inches(11.10), Inches(0.20), Inches(1.90), Inches(0.30),
            size=12, bold=True, color=RED, align=PP_ALIGN.RIGHT,
        )
    db.txt(s, title, Inches(0.32), Inches(0.50), Inches(12.7), Inches(0.62),
           size=24, bold=True, color=BLACK)
    db.rect(s, Inches(0.32), Inches(1.10), Inches(12.7), Inches(0.015), CHARCOAL)
    db.add_page_number(s, page_no)
    return s


def hbars(slide, rows, left, top, width, row_h, vmax, label_w=None):
    """Horizontal charcoal bars. rows: (label, value, display). No grid."""
    if label_w is None:
        label_w = Inches(3.55)
    val_w = Inches(1.55)
    bar_max = width - label_w - val_w - Inches(0.16)
    for i, (label, value, display) in enumerate(rows):
        y = top + i * row_h
        db.txt(
            slide, label, left, y, label_w, row_h,
            size=13, color=CHARCOAL, anchor=MSO_ANCHOR.MIDDLE,
        )
        bw = bar_max * (float(value) / vmax) if vmax else 0
        if bw > Inches(0.05):
            filled(
                slide, MSO_SHAPE.RECTANGLE,
                left + label_w + Inches(0.08), y + Inches(0.10),
                bw, row_h - Inches(0.20), CHARCOAL,
            )
        db.txt(
            slide, display, left + width - val_w, y, val_w, row_h,
            size=13, bold=True, color=CHARCOAL, align=PP_ALIGN.RIGHT,
            anchor=MSO_ANCHOR.MIDDLE,
        )


def hbars_pair(slide, rows, left, top, width, row_h, vmax, label_w=None):
    """Paired bars. rows: (label, value, display, color)."""
    if label_w is None:
        label_w = Inches(3.55)
    val_w = Inches(1.55)
    bar_max = width - label_w - val_w - Inches(0.16)
    for i, (label, value, display, color) in enumerate(rows):
        y = top + i * row_h
        db.txt(
            slide, label, left, y, label_w, row_h,
            size=13, color=CHARCOAL, anchor=MSO_ANCHOR.MIDDLE,
        )
        bw = bar_max * (float(value) / vmax) if vmax else 0
        if bw > Inches(0.05):
            filled(
                slide, MSO_SHAPE.RECTANGLE,
                left + label_w + Inches(0.08), y + Inches(0.10),
                bw, row_h - Inches(0.20), color,
            )
        db.txt(
            slide, display, left + width - val_w, y, val_w, row_h,
            size=13, bold=True, color=CHARCOAL, align=PP_ALIGN.RIGHT,
            anchor=MSO_ANCHOR.MIDDLE,
        )


def stacked_set(slide, left, top, width, height, segments):
    """One service as oil + fuel + air. segments: (label, euro, share, fill, text)."""
    x = left
    for i, (label, euro, share, fill, tcol) in enumerate(segments):
        w = width * share
        gap = Inches(0.04) if i < len(segments) - 1 else Inches(0)
        filled(slide, MSO_SHAPE.RECTANGLE, x, top, w - gap, height, fill)
        db.txt(
            slide, label, x + Inches(0.10), top + Inches(0.06),
            w - gap - Inches(0.16), Inches(0.28),
            size=12, bold=True, color=tcol,
        )
        db.txt(
            slide, euro, x + Inches(0.10), top + Inches(0.34),
            w - gap - Inches(0.16), Inches(0.30),
            size=14, bold=True, color=tcol,
        )
        x += w


def chip(slide, left, top, width, height, title, body):
    """Outlined read chip. Not a floating KPI tile."""
    outline(slide, MSO_SHAPE.RECTANGLE, left, top, width, height, CHARCOAL, 0.75)
    db.txt(
        slide, title, left + Inches(0.16), top + Inches(0.12),
        width - Inches(0.32), Inches(0.32),
        size=14, bold=True, color=CHARCOAL,
    )
    db.txt(
        slide, body, left + Inches(0.16), top + Inches(0.46),
        width - Inches(0.32), height - Inches(0.58),
        size=13, color=BLACK,
    )


def parts_board(slide, rows, left, top, width):
    """Genuine / BVP strips. Two quantity columns: ITUK to dealer, then ISZE to ITUK.
    No discs or circles in front of the filter names."""
    col_w = [
        Inches(1.70), Inches(1.20),
        Inches(1.40), Inches(1.20), Inches(1.15), Inches(0.80),
        Inches(1.40), Inches(1.20), Inches(1.15), Inches(0.80),
    ]
    headers = [
        "Item", "Cover N75",
        "PN", "ITUK to dealer", "ISZE to ITUK", "List EUR",
        "PN", "ITUK to dealer", "ISZE to ITUK", "List EUR",
    ]
    group_h = Inches(0.28)
    head_h = Inches(0.48)
    row_h = Inches(0.62)
    g_left = left + col_w[0] + col_w[1]
    g_w = col_w[2] + col_w[3] + col_w[4] + col_w[5]
    b_left = g_left + g_w
    b_w = col_w[6] + col_w[7] + col_w[8] + col_w[9]

    db.rect(slide, g_left, top, g_w - Inches(0.06), group_h, CHARCOAL)
    db.txt(
        slide, "GENUINE", g_left, top, g_w - Inches(0.06), group_h,
        size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
    )
    db.rect(slide, b_left + Inches(0.06), top, b_w - Inches(0.06), group_h, CHARCOAL)
    db.txt(
        slide, "BVP", b_left + Inches(0.06), top, b_w - Inches(0.06), group_h,
        size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
    )

    hy = top + group_h + Inches(0.04)
    x = left
    for i, (label, w) in enumerate(zip(headers, col_w)):
        align = PP_ALIGN.LEFT if i in (0, 2, 6) else PP_ALIGN.RIGHT
        db.txt(
            slide, label, x, hy, w - Inches(0.06), head_h,
            size=10, bold=True, color=CHARCOAL, align=align, anchor=MSO_ANCHOR.MIDDLE,
        )
        x += w
    db.rect(slide, left, hy + head_h, width, Inches(0.012), CHARCOAL)

    y = hy + head_h + Inches(0.06)
    for r, row in enumerate(rows):
        item, cover, g_pn, g_dlr, g_isze, g_eur, b_pn, b_dlr, b_isze, b_eur, quiet = row
        if r > 0:
            db.rect(slide, left, y, width, Inches(0.01), CHARCOAL)
        vals = [item, cover, g_pn, g_dlr, g_isze, g_eur, b_pn, b_dlr, b_isze, b_eur]
        x = left
        color = INK if quiet else CHARCOAL
        for i, (val, w) in enumerate(zip(vals, col_w)):
            align = PP_ALIGN.LEFT if i in (0, 2, 6) else PP_ALIGN.RIGHT
            bold = i in (0, 1) and not quiet
            db.txt(
                slide, val, x + Inches(0.04), y, w - Inches(0.10), row_h,
                size=12, bold=bold, color=color, align=align, anchor=MSO_ANCHOR.MIDDLE,
            )
            x += w
        y += row_h
    return y


def cover_ituk_dealer(path):
    """ITUK to dealer only. Three bars: oil, fuel, air. No second series."""
    import matplotlib.pyplot as plt

    cats = ["Oil filter", "Fuel filter", "Air filter"]
    vals = [46.2, 95.2, 19.6]
    colors = [ct.CHARCOAL, ct.CHARCOAL, ct.CHARCOAL]

    fig, ax = plt.subplots(figsize=(12.4, 2.55), dpi=200)
    fig.patch.set_facecolor(ct.WHITE)
    ax.set_facecolor(ct.WHITE)
    x = range(len(cats))
    bars = ax.bar(x, vals, width=0.48, color=colors, zorder=3)
    for bar, val in zip(bars, vals):
        ax.annotate(
            f"{val:.1f}%",
            (bar.get_x() + bar.get_width() / 2, val),
            xytext=(0, 8), textcoords="offset points",
            ha="center", va="bottom", fontsize=13, color=ct.CHARCOAL, fontweight="bold",
        )
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, fontsize=13, color=ct.CHARCOAL)
    ax.set_ylim(0, 118)
    ax.set_yticks([])
    for spine in ("top", "right", "left", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="x", length=0, pad=6)
    fig.tight_layout(pad=0.35)
    fig.savefig(path, dpi=200, facecolor=ct.WHITE)
    plt.close(fig)


def coverage_table(slide, left, top, width):
    """Both layers. Same type weight on every cell."""
    headers = ["Category", "Expected", "ITUK to dealer", "%", "ISZE to ITUK", "%"]
    rows = [
        ["Oil filter", "11,699", "5,404", "46.2%", "4,673", "39.9%"],
        ["Fuel filter", "11,699", "11,139", "95.2%", "11,021", "94.2%"],
        ["Air filter", "11,699", "2,289", "19.6%", "2,226", "19.0%"],
    ]
    col_w = [
        Inches(2.20), Inches(1.90), Inches(2.40), Inches(1.70), Inches(2.40), Inches(1.70),
    ]
    head_h = Inches(0.36)
    row_h = Inches(0.36)
    db.rect(slide, left, top, width, head_h, NAVY)
    x = left
    for label, w in zip(headers, col_w):
        align = PP_ALIGN.LEFT if label == "Category" else PP_ALIGN.RIGHT
        db.txt(
            slide, label, x + Inches(0.08), top, w - Inches(0.16), head_h,
            size=11, bold=True, color=WHITE, align=align, anchor=MSO_ANCHOR.MIDDLE,
        )
        x += w
    y = top + head_h
    for row in rows:
        db.rect(slide, left, y, width, Inches(0.01), CHARCOAL)
        x = left
        for i, (val, w) in enumerate(zip(row, col_w)):
            align = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.RIGHT
            db.txt(
                slide, val, x + Inches(0.08), y, w - Inches(0.16), row_h,
                size=12, bold=False, color=CHARCOAL, align=align, anchor=MSO_ANCHOR.MIDDLE,
            )
            x += w
        y += row_h
    db.rect(slide, left, y, width, Inches(0.01), CHARCOAL)
    return y


def simple_table(slide, headers, rows, left, top, width, col_w):
    """Hairline table. Same type weight on body cells."""
    head_h = Inches(0.34)
    row_h = Inches(0.34)
    db.rect(slide, left, top, width, head_h, CHARCOAL)
    x = left
    for i, (label, w) in enumerate(zip(headers, col_w)):
        align = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.RIGHT
        db.txt(
            slide, label, x + Inches(0.08), top, w - Inches(0.16), head_h,
            size=11, bold=True, color=WHITE, align=align, anchor=MSO_ANCHOR.MIDDLE,
        )
        x += w
    y = top + head_h
    for row in rows:
        db.rect(slide, left, y, width, Inches(0.01), CHARCOAL)
        x = left
        for i, (val, w) in enumerate(zip(row, col_w)):
            align = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.RIGHT
            db.txt(
                slide, val, x + Inches(0.08), y, w - Inches(0.16), row_h,
                size=13, color=CHARCOAL, align=align, anchor=MSO_ANCHOR.MIDDLE,
            )
            x += w
        y += row_h
    db.rect(slide, left, y, width, Inches(0.01), CHARCOAL)
    return y


def build_opener(prs):
    """Slide 1. Charcoal on white. No light grey bar."""
    s = db.blank_slide(prs)
    db.set_white_bg(s)
    db.txt(
        s, "IML  ·  ITUK  ·  ISZE", Inches(0.55), Inches(1.70),
        Inches(12.23), Inches(0.36), size=16, bold=True, color=CHARCOAL, align=PP_ALIGN.CENTER,
    )
    s.shapes.add_picture(db.LOGO_RED, (db.SW - Inches(3.2)) // 2, Inches(2.20), width=Inches(3.2))
    db.txt(
        s, "Operational kick-off, 18 August 2026",
        Inches(0.55), Inches(3.70), Inches(12.23), Inches(0.46),
        size=24, bold=True, color=BLACK, align=PP_ALIGN.CENTER,
    )
    db.txt(
        s,
        "Targeted actions: BVP availability, SPA where required, "
        "and a complete filter set for scheduled PMS.",
        Inches(1.20), Inches(4.30), Inches(10.90), Inches(0.80),
        size=16, color=INK, align=PP_ALIGN.CENTER,
    )
    db.add_footer_bar(s)
    return s


def build_close(prs, photo):
    """Quiet close. October. N75 first. Official P700 photograph if held."""
    s = db.blank_slide(prs)
    db.set_white_bg(s)
    s.shapes.add_picture(db.LOGO_RED, (db.SW - Inches(3.2)) // 2, Inches(0.95), width=Inches(3.2))
    db.txt(
        s, "October. N75 first.",
        Inches(0.70), Inches(1.90), Inches(11.90), Inches(0.50),
        size=28, bold=True, color=BLACK, align=PP_ALIGN.CENTER,
    )
    if photo and os.path.isfile(photo):
        db.add_picture_fit(s, photo, Inches(3.40), Inches(2.50), Inches(6.50), Inches(3.55))
        db.txt(
            s, "P700",
            Inches(0.70), Inches(6.15), Inches(11.90), Inches(0.32),
            size=14, color=INK, align=PP_ALIGN.CENTER,
        )
    db.add_footer_bar(s)
    return s


def close_locked_pptx(paths):
    """Save and close matching decks in a running PowerPoint so we can overwrite."""
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("win32com not available; skip COM close")
        return
    try:
        app = win32com.client.GetActiveObject("PowerPoint.Application")
    except Exception:
        return
    wanted = {os.path.normcase(os.path.abspath(p)) for p in paths}
    names = {os.path.normcase(os.path.basename(p)) for p in paths}
    closed = 0
    for pres in list(app.Presentations):
        try:
            fn = os.path.normcase(os.path.abspath(pres.FullName))
            base = os.path.normcase(os.path.basename(pres.FullName))
        except Exception:
            continue
        if fn in wanted or base in names:
            try:
                pres.Save()
            except Exception:
                pass
            try:
                pres.Close()
                closed += 1
            except Exception as e:
                print("COM close failed:", e)
    print("COM closed", closed, "presentation(s)")
    time.sleep(0.8)


def copy_both():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    try:
        shutil.copy2(OUT, OUT_ROOT)
        print("copied", OUT_ROOT)
    except OSError as e:
        print("root copy skipped:", e)


def open_in_powerpoint(path):
    if not os.path.isfile(PPT_EXE):
        print("POWERPNT.EXE missing:", PPT_EXE)
        return False
    subprocess.Popen([PPT_EXE, path])
    path_n = os.path.normcase(os.path.abspath(path))
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("opened via POWERPNT.EXE (no COM verify)")
        return True
    for _ in range(18):
        time.sleep(1)
        try:
            app = win32com.client.GetActiveObject("PowerPoint.Application")
            app.Visible = True
            for pres in app.Presentations:
                try:
                    fn = os.path.normcase(os.path.abspath(pres.FullName))
                except Exception:
                    continue
                if fn == path_n:
                    print("PowerPoint showing", pres.FullName)
                    return True
        except Exception:
            pass
    print("POWERPNT.EXE launched; COM did not confirm the file yet")
    return False


def build():
    chart = os.path.join(CHART_DIR, "n75_cover.png")
    cover_ituk_dealer(chart)
    photo = PHOTO_SRC if os.path.isfile(PHOTO_SRC) else None

    prs = db.new_presentation()

    # 1 opener
    build_opener(prs)

    # 2 goal. Path / kick-off timeline removed. No personal name.
    s = content_slide(
        prs, "Goal and three actions",
        eyebrow="Goal", page_no=2,
    )
    db.txt(
        s,
        "The goal is one additional percentage point on all ITUK PMS parts at ITUK sales to dealers.",
        Inches(0.32), Inches(1.18), Inches(12.70), Inches(0.36),
        size=16, color=INK,
    )
    db.rect(s, Inches(0.32), Inches(1.60), Inches(12.70), Inches(1.28), NAVY)
    db.txt(
        s, "368 additional units  /  about EUR 7,530 valued",
        Inches(0.50), Inches(1.70), Inches(12.34), Inches(0.42),
        size=22, bold=True, color=WHITE,
    )
    db.txt(
        s,
        "That is 1 percent of calendar 2025 ITUK sales to dealers on the ITUK parts list "
        f"({TOTAL_UNITS:,} units / EUR {TOTAL_EUR:,} valued), at the same mix. "
        "The euro figure is valued at the ISZE average selling price to ITUK. It is not a dealer invoice.",
        Inches(0.50), Inches(2.14), Inches(12.34), Inches(0.64),
        size=14, color=WHITE,
    )
    actions = [
        "Offer BVP where genuine volume is low.",
        "Use a Special Price Agreement only if price remains the barrier.",
        "Complete the filter set when attach is the barrier.",
    ]
    y = Inches(3.12)
    for i, sentence in enumerate(actions, start=1):
        db.txt(
            s, str(i), Inches(0.32), y, Inches(0.50), Inches(0.70),
            size=22, bold=True, color=CHARCOAL, anchor=MSO_ANCHOR.MIDDLE,
        )
        db.txt(
            s, sentence, Inches(0.90), y, Inches(12.10), Inches(0.70),
            size=20, color=BLACK, anchor=MSO_ANCHOR.MIDDLE,
        )
        y += Inches(0.92)

    # 3 coverage. Rewritten short. Chart + both-layer table kept.
    s = content_slide(
        prs, "N75 filter coverage, calendar 2025",
        eyebrow="Coverage", page_no=3,
    )
    db.txt(
        s,
        "How much of the expected N75 service volume was sold, ITUK to dealers and ISZE to ITUK.",
        Inches(0.32), Inches(1.18), Inches(12.70), Inches(0.36),
        size=16, color=INK,
    )
    db.add_picture_fit(s, chart, Inches(0.32), Inches(1.58), Inches(12.70), Inches(2.55))
    coverage_table(s, Inches(0.32), Inches(4.22), Inches(12.70))
    db.txt(
        s,
        "Fuel is already at the N75 service level. Air is not.",
        Inches(0.32), Inches(5.72), Inches(12.70), Inches(0.36),
        size=14, color=INK,
    )

    # 4 parts board
    s = content_slide(
        prs, "Part numbers and 2025 quantity",
        eyebrow="Parts", page_no=4,
    )
    db.txt(
        s,
        "The primary quantity column is ITUK to dealer. ISZE to ITUK is shown beside it. "
        "List prices are ISZE list euro. Cover percentages are N75 only, ISZE then dealer. "
        "The oil filter is set contents.",
        Inches(0.32), Inches(1.18), Inches(12.70), Inches(0.52),
        size=14, color=INK,
    )
    parts_board(
        s,
        [
            (
                "Oil filter", "39.9% / 46.2%",
                "8983282070", "348", "371", "14.45",
                "1876102890", "2,161", "2,909", "9.96",
                True,
            ),
            (
                "Fuel filter", "94.2% / 95.2%",
                "8975425400", "3,605", "2,005", "12.56",
                "1876102860", "0", "0", "8.05",
                False,
            ),
            (
                "Air filter", "19.0% / 19.6%",
                "8981772710", "1,513", "1,403", "31.36",
                "5876102500", "0", "0", "17.49",
                False,
            ),
        ],
        Inches(0.42), Inches(1.82), Inches(12.50),
    )

    # 5 BVP (action 1). Filled page. Not two floating cards. Not the filter-set slide.
    s = content_slide(
        prs, "BVP where genuine volume is low",
        eyebrow="BVP", page_no=5,
    )
    db.txt(
        s,
        "The request is to offer BVP for the fuel and air filters on the scheduled PMS set. "
        "Genuine remains first. BVP is the alternative when genuine volume stays low.",
        Inches(0.32), Inches(1.18), Inches(12.70), Inches(0.44),
        size=15, color=INK,
    )
    part_w = Inches(1.20)
    g_w = Inches(5.50)
    b_w = Inches(6.00)
    db.rect(s, Inches(0.32) + part_w, Inches(1.70), g_w - Inches(0.06), Inches(0.28), CHARCOAL)
    db.txt(
        s, "GENUINE", Inches(0.32) + part_w, Inches(1.70), g_w - Inches(0.06), Inches(0.28),
        size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
    )
    db.rect(s, Inches(0.32) + part_w + g_w + Inches(0.06), Inches(1.70), b_w - Inches(0.06), Inches(0.28), CHARCOAL)
    db.txt(
        s, "BVP", Inches(0.32) + part_w + g_w + Inches(0.06), Inches(1.70), b_w - Inches(0.06), Inches(0.28),
        size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
    )
    simple_table(
        s,
        ["Part", "PN", "ISZE to ITUK", "Projected to dealers",
         "PN", "ISZE to ITUK", "Projected to dealers"],
        [
            ["Fuel", "8975425400", eur(FUEL_G), eur(proj(FUEL_G)),
             "1876102860", eur(FUEL_B), eur(proj(FUEL_B))],
            ["Air", "8981772710", eur(AIR_G), eur(proj(AIR_G)),
             "5876102500", eur(AIR_B), eur(proj(AIR_B))],
        ],
        Inches(0.32), Inches(2.02), Inches(12.70),
        [part_w, Inches(1.80), Inches(1.80), Inches(1.90),
         Inches(1.80), Inches(1.80), Inches(2.40)],
    )
    db.txt(
        s,
        "Projected ITUK price to dealers. Genuine versus BVP. Same 1.40 step as the aftermarket slide.",
        Inches(0.32), Inches(3.12), Inches(12.70), Inches(0.28),
        size=14, color=INK,
    )
    hbars_pair(
        s,
        [
            ("Fuel, genuine", proj(FUEL_G), eur(proj(FUEL_G)), CHARCOAL),
            ("Fuel, BVP", proj(FUEL_B), eur(proj(FUEL_B)), GRAY_MID),
            ("Air, genuine", proj(AIR_G), eur(proj(AIR_G)), CHARCOAL),
            ("Air, BVP", proj(AIR_B), eur(proj(AIR_B)), GRAY_MID),
        ],
        Inches(0.32), Inches(3.40), Inches(12.70), Inches(0.40),
        vmax=proj(AIR_G), label_w=Inches(2.60),
    )
    db.txt(
        s,
        "ITUK to dealer cover against expected N75 volume. Fuel is already at the service level. Air is the hole. Oil BVP is already supplied.",
        Inches(0.32), Inches(5.04), Inches(12.70), Inches(0.32),
        size=14, color=INK,
    )
    hbars(
        s,
        [
            ("Oil filter", 46.2, "46.2%"),
            ("Fuel filter", 95.2, "95.2%"),
            ("Air filter", 19.6, "19.6%"),
        ],
        Inches(0.32), Inches(5.36), Inches(12.70), Inches(0.38),
        vmax=100, label_w=Inches(2.60),
    )

    # 6 SPA (action 2). Last-resort line same colour and weight. Not highlighted.
    s = content_slide(
        prs, "Special Price Agreement",
        eyebrow="SPA", page_no=6,
    )
    db.txt(
        s,
        "If price remains the barrier after BVP, a targeted discount may be used "
        "where it increases PMS take-up.",
        Inches(0.32), Inches(1.28), Inches(12.70), Inches(0.70),
        size=18, color=BLACK,
    )
    bullets(
        s,
        [
            "The request concerns fuel and air filters, and genuine lines where volume is low.",
            "A Special Price Agreement is requested only if the BVP alternative is not sufficient for scheduled PMS.",
            "If ITUK and ISZE cannot agree the required discount, IML can assist as a last resort.",
        ],
        Inches(0.32), Inches(2.10), Inches(12.70), Inches(2.40), size=18,
    )

    # 7 filter set (action 3). One service. Genuine first. Both euro steps. Not three cards.
    s = content_slide(
        prs, "Parts required for one scheduled PMS (N75)",
        eyebrow="Filter set", page_no=7,
    )
    db.txt(
        s,
        "One scheduled service is oil, fuel, and air. Offer the genuine set first. "
        "Use BVP only if the genuine set does not take. Air is the attach hole.",
        Inches(0.32), Inches(1.16), Inches(12.70), Inches(0.44),
        size=15, color=INK,
    )
    oil_s, fuel_s, air_s = OIL_G / SET_G, FUEL_G / SET_G, AIR_G / SET_G
    segs = [
        ("Oil", eur(OIL_G), oil_s, GRAY_MID, WHITE),
        ("Fuel", eur(FUEL_G), fuel_s, GRAY_DK, WHITE),
        ("Air, attach hole", eur(AIR_G), air_s, CHARCOAL, WHITE),
    ]
    segs_p = [
        ("Oil", eur(proj(OIL_G)), oil_s, GRAY_MID, WHITE),
        ("Fuel", eur(proj(FUEL_G)), fuel_s, GRAY_DK, WHITE),
        ("Air, attach hole", eur(proj(AIR_G)), air_s, CHARCOAL, WHITE),
    ]
    db.txt(
        s, "ISZE to ITUK",
        Inches(0.32), Inches(1.64), Inches(9.40), Inches(0.26),
        size=12, bold=True, color=CHARCOAL,
    )
    db.txt(
        s, eur(SET_G),
        Inches(9.80), Inches(1.64), Inches(3.22), Inches(0.26),
        size=14, bold=True, color=CHARCOAL, align=PP_ALIGN.RIGHT,
    )
    stacked_set(s, Inches(0.32), Inches(1.92), Inches(12.70), Inches(0.72), segs)
    db.txt(
        s, "Projected ITUK to dealers (x 1.40)",
        Inches(0.32), Inches(2.72), Inches(9.40), Inches(0.26),
        size=12, bold=True, color=CHARCOAL,
    )
    db.txt(
        s, eur(proj(SET_G)),
        Inches(9.80), Inches(2.72), Inches(3.22), Inches(0.26),
        size=14, bold=True, color=CHARCOAL, align=PP_ALIGN.RIGHT,
    )
    stacked_set(s, Inches(0.32), Inches(3.00), Inches(12.70), Inches(0.72), segs_p)
    simple_table(
        s,
        ["Part", "ISZE to ITUK", "Projected ITUK to dealers", "Why it is in the set"],
        [
            ["Oil filter", eur(OIL_G), eur(proj(OIL_G)), "Set contents"],
            ["Fuel filter", eur(FUEL_G), eur(proj(FUEL_G)), "Already at the service level"],
            ["Air filter", eur(AIR_G), eur(proj(AIR_G)), "Attach hole. Complete the set."],
        ],
        Inches(0.32), Inches(3.86), Inches(12.70),
        [Inches(2.40), Inches(2.50), Inches(3.40), Inches(4.40)],
    )
    db.txt(
        s,
        f"Today, oil BVP is already in the set: {eur(SET_TODAY)} to ITUK, and {eur(proj(SET_TODAY))} projected to dealers. "
        f"The BVP set is a last resort only: {eur(SET_B)} to ITUK, and {eur(proj(SET_B))} projected to dealers.",
        Inches(0.32), Inches(5.56), Inches(12.70), Inches(0.58),
        size=14, color=INK,
    )

    # 8 brakes (DRAFT). Price steps fill the page. Not two floating cards.
    s = content_slide(
        prs, "Brake pad and discs",
        eyebrow="Brakes", page_no=8, draft=True,
    )
    db.txt(
        s,
        "The scheduled wear item is the pad. Discs are the aftermarket hole. "
        "There is no BVP twin for the R90 pad. A Special Price Agreement is the commercial route.",
        Inches(0.32), Inches(1.16), Inches(12.70), Inches(0.40),
        size=15, color=INK,
    )
    db.txt(
        s,
        "Pad  8982447940. Cover is about 51 percent (2,367 ITUK to dealer / 2,282 ISZE to ITUK, "
        "against 9,359 vehicles at 0.5 events).",
        Inches(0.32), Inches(1.56), Inches(12.70), Inches(0.32),
        size=14, color=INK,
    )
    hbars(
        s,
        [
            ("ISZE to ITUK", PAD_ISZE, eur(PAD_ISZE)),
            ("Projected ITUK to dealers", proj(PAD_ISZE), eur(proj(PAD_ISZE))),
            ("Aftermarket workshop", PAD_AM, eur(PAD_AM)),
        ],
        Inches(0.32), Inches(1.90), Inches(12.70), Inches(0.40),
        vmax=proj(PAD_ISZE), label_w=Inches(3.70),
    )
    db.txt(
        s,
        "Read the last two bars. Same step: projected ITUK price to dealers versus what a workshop pays for the aftermarket pad.",
        Inches(0.32), Inches(3.12), Inches(12.70), Inches(0.28),
        size=14, color=INK,
    )
    db.txt(
        s, "Pad cover against expected N75 events",
        Inches(0.32), Inches(3.40), Inches(12.70), Inches(0.24),
        size=13, bold=True, color=CHARCOAL,
    )
    hbars(
        s,
        [("Cover", 51, "about 51%")],
        Inches(0.32), Inches(3.62), Inches(12.70), Inches(0.38),
        vmax=100, label_w=Inches(3.70),
    )
    db.txt(
        s, "Discs that are selling. Not on the ITUK PMS list.",
        Inches(0.32), Inches(4.08), Inches(12.70), Inches(0.26),
        size=14, bold=True, color=CHARCOAL,
    )
    simple_table(
        s,
        ["Axle", "PN", "ITUK to dealer", "ISZE to ITUK", "Cover"],
        [
            ["Rear", "8981919560", "487", "521", "about 10%"],
            ["Front", "8982488951", "393", "520", "about 8%"],
        ],
        Inches(0.32), Inches(4.36), Inches(12.70),
        [Inches(2.00), Inches(2.70), Inches(2.70), Inches(2.70), Inches(2.60)],
    )
    db.txt(
        s,
        "Cover uses 0.25 axle-sets per year (200,000 km, two pad lives). "
        "These discs fit N75 NPR and carry over to P700.",
        Inches(0.32), Inches(5.72), Inches(12.70), Inches(0.40),
        size=14, color=INK,
    )

    # 9 clutch. Kit first. Piece table second. Price steps fill the lower white.
    s = content_slide(
        prs, "Clutch kit, manual vehicles only",
        eyebrow="Clutch", page_no=9, draft=True,
    )
    db.txt(
        s,
        "Until a transmission file exists, the planning assumption is that 47 percent of the N75 parc is manual.",
        Inches(0.32), Inches(1.18), Inches(12.70), Inches(0.36),
        size=15, color=INK,
    )
    outline(s, MSO_SHAPE.RECTANGLE, Inches(0.32), Inches(1.64), Inches(7.55), Inches(2.05), CHARCOAL, 1.0)
    db.txt(
        s, "BVP kit  5876102320",
        Inches(0.52), Inches(1.76), Inches(7.15), Inches(0.30),
        size=15, bold=True, color=CHARCOAL,
    )
    db.txt(
        s, "ISZE to ITUK EUR 194.69. Projected ITUK to dealers about EUR 273.",
        Inches(0.52), Inches(2.10), Inches(7.15), Inches(0.70),
        size=16, bold=True, color=CHARCOAL,
    )
    db.txt(
        s, "63 ITUK to dealer.  78 ISZE to ITUK.",
        Inches(0.52), Inches(2.68), Inches(7.15), Inches(0.36),
        size=15, color=BLACK,
    )
    outline(s, MSO_SHAPE.RECTANGLE, Inches(8.07), Inches(1.64), Inches(4.95), Inches(2.05), CHARCOAL, 0.75)
    db.txt(
        s, "Genuine piece sum",
        Inches(8.25), Inches(1.76), Inches(4.60), Inches(0.30),
        size=14, bold=True, color=CHARCOAL,
    )
    db.txt(
        s, "ISZE to ITUK EUR 282.08. About EUR 395 projected to dealers.",
        Inches(8.25), Inches(2.10), Inches(4.60), Inches(0.55),
        size=14, bold=True, color=CHARCOAL,
    )
    db.txt(
        s, "8981649171 + 8970388314 + 1313100120. Do not mix 8981649181.",
        Inches(8.25), Inches(2.58), Inches(4.60), Inches(0.70),
        size=13, color=BLACK,
    )
    simple_table(
        s,
        ["Piece", "PN", "ITUK to dealer", "ISZE to ITUK"],
        [
            ["Disc", "8981649171", "50", "47"],
            ["Pressure plate", "8970388314", "9", "54"],
            ["Release bearing", "1313100120", "38", "21"],
        ],
        Inches(0.32), Inches(3.78), Inches(12.70),
        [Inches(3.40), Inches(3.10), Inches(3.10), Inches(3.10)],
    )
    hbars_pair(
        s,
        [
            ("BVP kit, ISZE to ITUK", KIT_ISZE, eur(KIT_ISZE), CHARCOAL),
            ("BVP kit, projected to dealers", 273, "about EUR 273", GRAY_MID),
            ("Genuine pieces, ISZE to ITUK", GEN_PIECE_ISZE, eur(GEN_PIECE_ISZE), CHARCOAL),
            ("Genuine pieces, projected to dealers", 395, "about EUR 395", GRAY_MID),
        ],
        Inches(0.32), Inches(5.20), Inches(12.70), Inches(0.36),
        vmax=395, label_w=Inches(4.20),
    )

    # 10 urea. Factual. Not on the ITUK parts list.
    s = content_slide(
        prs, "Urea filter kit",
        eyebrow="Urea", page_no=10, draft=True,
    )
    db.txt(
        s,
        "Urea is not in the ITUK parts list of 56 part numbers. It is a separate line. "
        "The item on the parts file is the DEF pump filter kit, not bulk fluid.",
        Inches(0.32), Inches(1.18), Inches(12.70), Inches(0.58),
        size=15, color=INK,
    )
    card(
        s, Inches(0.32), Inches(1.88), Inches(6.20), Inches(2.85),
        "Genuine  8983507161",
        "FILTER KIT; PUMP ASM,DEF DCM S. "
        "ITUK to dealer 541. ISZE to ITUK 506. "
        "ISZE to ITUK EUR 70.53. Projected ITUK to dealers about EUR 99 (x 1.40).",
        body_size=16,
    )
    card(
        s, Inches(6.80), Inches(1.88), Inches(6.20), Inches(2.85),
        "BVP  1876102341",
        "Same kit, BVP number. "
        "ITUK to dealer 34. ISZE to ITUK 46. "
        "ISZE to ITUK EUR 30.72. Projected ITUK to dealers about EUR 43 (x 1.40).",
        body_size=16,
    )
    db.txt(
        s,
        "No AdBlue fluid part number was found on the ITUK dealer file for calendar 2025. "
        "Earlier kit numbers also appear: 8983507160 (132 to dealers) and 1876102340 (77 to dealers, 59 ISZE to ITUK).",
        Inches(0.32), Inches(4.90), Inches(12.70), Inches(0.70),
        size=14, color=INK,
    )

    # 11 aftermarket (DRAFT). Spoken headline. Sign only at projected ITUK vs workshop.
    s = content_slide(
        prs, "The pad is well above aftermarket at the dealer step",
        eyebrow="Aftermarket", page_no=11, draft=True,
    )
    db.txt(
        s,
        "Filters are close. The clutch is not the problem.",
        Inches(0.32), Inches(1.16), Inches(12.70), Inches(0.28),
        size=16, bold=True, color=CHARCOAL,
    )
    db.txt(
        s,
        "We compare the projected ITUK price to dealers with what a workshop pays for the aftermarket part. Same step.",
        Inches(0.32), Inches(1.44), Inches(12.70), Inches(0.28),
        size=14, color=INK,
    )
    simple_table(
        s,
        ["Part", "ISZE to ITUK", "Projected ITUK to dealers", "Aftermarket workshop", "Read"],
        [
            ["Oil filter", eur(OIL_G), eur(proj(OIL_G)), "EUR 15.10", "Above"],
            ["Fuel filter", eur(FUEL_G), eur(proj(FUEL_G)), "EUR 14.45", "Above"],
            ["Air filter", eur(AIR_G), eur(proj(AIR_G)), "EUR 47.05", "In line"],
            ["Brake pad", eur(PAD_ISZE), eur(proj(PAD_ISZE)), eur(PAD_AM), "Well above"],
            ["Clutch disc", eur(CLUTCH_DISC_ISZE), eur(proj(CLUTCH_DISC_ISZE)), "EUR 284", "Below"],
        ],
        Inches(0.32), Inches(1.76), Inches(12.70),
        [Inches(2.30), Inches(2.20), Inches(3.00), Inches(2.80), Inches(2.40)],
    )
    chip(
        s, Inches(0.32), Inches(3.92), Inches(4.10), Inches(2.05),
        "Above",
        "Oil and fuel sit above aftermarket at the dealer step, and close.",
    )
    chip(
        s, Inches(4.62), Inches(3.92), Inches(4.10), Inches(2.05),
        "In line",
        "Air is in line with aftermarket at the same step.",
    )
    chip(
        s, Inches(8.92), Inches(3.92), Inches(4.10), Inches(2.05),
        "Well above",
        "The pad is well above aftermarket. That is the line to discuss.",
    )
    db.txt(
        s,
        "ISZE to ITUK is shown so the buy-in is visible. The read uses only projected ITUK to dealers versus aftermarket. "
        "Projected is ISZE to ITUK times 1.40.",
        Inches(0.32), Inches(6.10), Inches(12.70), Inches(0.40),
        size=13, color=INK,
    )

    # 13 close
    build_close(prs, photo)

    assert "ORIGINAL" not in os.path.basename(OUT)
    assert "ORIGINAL" not in os.path.basename(OUT_ROOT)
    assert len(prs.slides) == SLIDE_COUNT
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prs.save(OUT)
    print("wrote", OUT)
    print("slides_built", len(prs.slides))
    print("photo", photo if photo else "NONE")
    print(
        "cadrage",
        f"units={ONE_PCT_UNITS}",
        f"valued_eur={ONE_PCT_EUR}",
        f"total_units={TOTAL_UNITS}",
        f"total_eur={TOTAL_EUR}",
        "ituk_dealer_eur=valued_isze_asp_not_invoice",
    )
    copy_both()
    return prs


if __name__ == "__main__":
    close_locked_pptx([OUT, OUT_ROOT])
    build()
    showed = open_in_powerpoint(OUT)
    print("powerpoint_showed", showed)
    print("slides", SLIDE_COUNT)
