# -*- coding: utf-8 -*-
"""
Build ISZE_PMS_Coverage_2026-09-21.pptx

Structure and message take the ISZE conference presentation
(ISZE_GPS_PMS_Conf26_v3.pptx: the invisible market, GPS and PMS, how we measure,
FY27 rollout, what you get, assumptions and open questions).

Slide treatment takes the IML team-meeting slides
(GPS_PMS.pptx: What it is / Why it matters / What we are doing / Status,
PMS as a joint ISZE-IML project, FY27 new projects).

Deliberately NO results numbers: no coverage %, no euro gaps, no market tables.
Only the working replacement intervals that are already in the conference deck,
and the five-step measure.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_PMS_Coverage_2026-09-21.pptx")

NAVY = RGBColor(0x15, 0x23, 0x3C)
TERRA = RGBColor(0xC0, 0x55, 0x2D)
PAPER = RGBColor(0xF7, 0xF4, 0xEE)
INK = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x6B, 0x62, 0x56)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xD9, 0xD3, 0xC8)
PALEBLUE = RGBColor(0xB9, 0xC4, 0xD6)
GREEN = RGBColor(0x1D, 0x9E, 0x75)

HEAD_FONT = "Georgia"
BODY_FONT = "Segoe UI"

W = Inches(13.333)
H = Inches(7.5)
M = Inches(0.62)
CW = W - 2 * M

prs = Presentation()
prs.slide_width = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]


def _rect(slide, x, y, w, h, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    return sh


def _text(slide, x, y, w, h, runs=None, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
          space_after=5, line_spacing=1.0):
    # Convenience: when the height is omitted and the runs are passed in its place,
    # detect that and estimate a height that fits, so no box is sized blindly.
    if runs is None and isinstance(h, (list, str)):
        runs, h = h, None
    if h is None:
        probe = runs if isinstance(runs, list) else [(runs, 12, False, INK, BODY_FONT, 0)]
        est_lines = 0.0
        for item in probe:
            txt = item[0]
            size = item[1]
            chars_per_line = max(12.0, (w / 914400.0) * 96.0 / (size * 0.52))
            est_lines += max(1.0, -(-len(txt) // chars_per_line))
        h = Emu(int((est_lines * 1.32 * 12 + 8) * 12700))
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    if isinstance(runs, str):
        runs = [(runs, 12, False, INK, BODY_FONT, 0)]
    first = True
    for item in runs:
        text, size, bold, colour, font, level = item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        p.level = level
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = colour
        r.font.name = font
    return tb


def _header(slide, kicker, title, subtitle=None):
    band_h = Inches(1.02)
    _rect(slide, 0, 0, W, band_h, NAVY)
    _rect(slide, 0, band_h, W, Inches(0.045), TERRA)
    _text(slide, M, Inches(0.14), CW, Inches(0.9),
          [(kicker.upper(), 9.5, True, PALEBLUE, BODY_FONT, 0),
           (title, 22, False, WHITE, HEAD_FONT, 0)], space_after=2)
    if subtitle:
        _text(slide, M, band_h + Inches(0.16), CW, Inches(0.4),
              [(subtitle, 12, False, MUTED, BODY_FONT, 0)], line_spacing=1.05)
        return band_h + Inches(0.72)
    return band_h + Inches(0.3)


def _footer(slide, text):
    _rect(slide, M, H - Inches(0.5), CW, Emu(9525), LINE)
    _text(slide, M, H - Inches(0.43), CW, Inches(0.3),
          [(text, 8.5, False, MUTED, BODY_FONT, 0)])


def add():
    return prs.slides.add_slide(BLANK)


# ------------------------------------------------------------------ slides
def s_cover():
    s = add()
    _rect(s, 0, 0, W, H, NAVY)
    _rect(s, 0, Inches(3.35), Inches(1.6), Inches(0.06), TERRA)
    _text(s, M, Inches(1.55), Inches(11.0),
          [("ISUZU MOTORS EUROPE \u00b7 PARTS", 11, True, PALEBLUE, BODY_FONT, 0)])
    _text(s, M, Inches(2.05), Inches(11.4),
          [("Genuine Parts Share & PMS", 40, False, WHITE, HEAD_FONT, 0)])
    _text(s, M, Inches(2.6), Inches(10.6),
          [("Making the opportunity visible \u2014 together with our distributors",
            16, False, RGBColor(0xDD, 0xE4, 0xEF), BODY_FONT, 0)])
    _text(s, M, Inches(3.8), Inches(11.4), [
        ("A joint ISZE \u2013 IML exercise to identify and capture untapped", 12, False, RGBColor(0xC9, 0xD4, 0xE3), BODY_FONT, 0),
        ("Periodic Maintenance Service parts sales potential.", 12, False, RGBColor(0xC9, 0xD4, 0xE3), BODY_FONT, 0),
        ("PMS parts: oil, fuel and air filters, clutch, brake.", 12, False, RGBColor(0xC9, 0xD4, 0xE3), BODY_FONT, 0),
    ], space_after=6)
    _text(s, M, Inches(6.35), Inches(11.4),
          [("September 2026  \u00b7  for discussion with IML and the distributor network",
            9.5, False, RGBColor(0x93, 0xA3, 0xB8), BODY_FONT, 0)])


def s_invisible():
    s = add()
    y = _header(s, "Why we are doing this", "The invisible market")
    lines = [
        ("Every Isuzu in operation generates predictable parts demand.", 20, WHITE, HEAD_FONT),
        ("Today, neither ISZE nor our distributors can see how much of that demand we actually capture.", 20, WHITE, HEAD_FONT),
        ("This is our first attempt to make it visible \u2014 and an invitation to refine it together.", 20, TERRA, HEAD_FONT),
    ]
    yy = y + Inches(0.5)
    for txt, size, colour, font in lines:
        _rect(s, M, yy, Inches(0.055), Inches(1.0), TERRA if colour == TERRA else PALEBLUE)
        _text(s, M + Inches(0.32), yy + Inches(0.06), Inches(11.0), Inches(0.95),
              [(txt, size, False, NAVY if colour == WHITE else colour, font, 0)],
              line_spacing=1.1)
        yy += Inches(1.32)
    _text(s, M, yy + Inches(0.15), Inches(11.4),
          [("The demand is already there. What is missing is the visibility \u2014 and the shared method to act on it.",
            12.5, False, MUTED, BODY_FONT, 0)])
    _footer(s, "No figure is quoted on this page on purpose. The exercise starts by agreeing the method before anyone is measured on it.")


def s_two_questions():
    s = add()
    y = _header(s, "Definitions", "GPS and PMS \u2014 what we measure, and why we start with PMS",
                "Two questions, one objective. The broad question is the destination; the narrow one is where we can start measuring today.")
    colw = (CW - Inches(0.34)) / 2
    blocks = [
        ("Genuine Parts Share (GPS)", NAVY, "The strategic question",
         "Of the total parts spend an Isuzu vehicle generates over its life, how much goes to ISZE versus the aftermarket?",
         "Hard to measure directly \u2014 we do not see aftermarket sales.",
         None),
        ("PMS Coverage", TERRA, "The tactical sub-question",
         "Of the predictable PMS demand each vehicle generates every year \u2014 oil, fuel filter, air filter, brake, clutch \u2014 how much do we capture?",
         "Measurable from our own data: units in operation \u00d7 replacement frequency against invoiced sales.",
         None),
    ]
    for i, (title, colour, tag, q, why, extra) in enumerate(blocks):
        x = M + i * (colw + Inches(0.34))
        _rect(s, x, y, colw, Inches(2.85), PAPER)
        _rect(s, x, y, Inches(0.06), Inches(2.85), colour)
        _text(s, x + Inches(0.26), y + Inches(0.18), colw - Inches(0.5), Inches(0.28),
              [(tag.upper(), 9.5, True, colour, BODY_FONT, 0)])
        _text(s, x + Inches(0.26), y + Inches(0.5), colw - Inches(0.5), Inches(0.34),
              [(title, 16, True, colour, HEAD_FONT, 0)])
        _text(s, x + Inches(0.26), y + Inches(0.98), colw - Inches(0.5), Inches(1.0),
              [(q, 12, False, INK, BODY_FONT, 0)], line_spacing=1.1)
        _text(s, x + Inches(0.26), y + Inches(2.08), colw - Inches(0.5), Inches(0.65),
              [(why, 11, False, MUTED, BODY_FONT, 0)], line_spacing=1.08)

    y2 = y + Inches(3.1)
    _rect(s, M, y2, CW, Inches(0.95), PAPER)
    _rect(s, M, y2, Inches(0.06), Inches(0.95), GREEN)
    _text(s, M + Inches(0.26), y2 + Inches(0.15), CW - Inches(0.55), Inches(0.7), [
        ("PMS is the entry point that lets us approximate GPS.", 13, True, GREEN, BODY_FONT, 0),
        ("Start measurable, learn, then extend the lens to the wider parts basket.", 11.5, False, INK, BODY_FONT, 0),
    ], space_after=5, line_spacing=1.05)
    _footer(s, "GPS is a direction of travel rather than a number we can produce today. PMS is the part of it we can measure from our own invoicing.")


def s_how():
    s = add()
    y = _header(s, "Method", "How we measure \u2014 five steps, no black box",
                "Each step is written down, so a distributor can challenge any of them. That is the point of the exercise.")
    steps = [
        ("1", "Units in\noperation", "The parc,\nby market"),
        ("2", "Active\nunits", "The share of the\nparc actually in\nservice"),
        ("3", "Potential\ndemand", "\u00d7 replacement\nfrequency"),
        ("4", "Actual\ndemand", "What we\ninvoiced"),
        ("5", "Coverage", "Actual \u00f7\npotential"),
    ]
    sw = (CW - Inches(0.5)) / 5
    for i, (num, head, sub) in enumerate(steps):
        x = M + i * (sw + Inches(0.125))
        fill = NAVY if i == 4 else PAPER
        _rect(s, x, y, sw, Inches(2.05), fill)
        _rect(s, x, y, sw, Inches(0.05), TERRA)
        _text(s, x + Inches(0.18), y + Inches(0.18), sw - Inches(0.36), Inches(0.3),
              [(num, 15, True, TERRA, HEAD_FONT, 0)])
        _text(s, x + Inches(0.18), y + Inches(0.56), sw - Inches(0.36), Inches(0.6),
              [(head, 13, True, WHITE if i == 4 else NAVY, HEAD_FONT, 0)], line_spacing=1.0)
        _text(s, x + Inches(0.18), y + Inches(1.24), sw - Inches(0.36), Inches(0.7),
              [(sub, 10.5, False, RGBColor(0xD8, 0xDF, 0xEA) if i == 4 else MUTED, BODY_FONT, 0)],
              line_spacing=1.05)
        if i < 4:
            _text(s, x + sw - Inches(0.02), y + Inches(0.8), Inches(0.16), Inches(0.3),
                  [("\u203a", 14, True, TERRA, BODY_FONT, 0)], align=PP_ALIGN.CENTER)

    y2 = y + Inches(2.35)
    _text(s, M, y2, CW, [("Working replacement frequencies \u2014 IML reference", 13, True, NAVY, HEAD_FONT, 0)])
    freqs = [
        ("Oil filter", "every 20,000 km"),
        ("Fuel and air filter", "every 40,000 km"),
        ("Clutch and brake", "every 100,000 km"),
    ]
    cw = (CW - Inches(0.3)) / 3
    for i, (fam, iv) in enumerate(freqs):
        x = M + i * (cw + Inches(0.15))
        _rect(s, x, y2 + Inches(0.42), cw, Inches(0.85), PAPER)
        _rect(s, x, y2 + Inches(0.42), Inches(0.05), Inches(0.85), TERRA)
        _text(s, x + Inches(0.2), y2 + Inches(0.55), cw - Inches(0.4), Inches(0.26),
              [(fam, 11.5, True, NAVY, BODY_FONT, 0)])
        _text(s, x + Inches(0.2), y2 + Inches(0.84), cw - Inches(0.4), Inches(0.3),
              [(iv, 11.5, False, TERRA, BODY_FONT, 0)])
    _text(s, M, y2 + Inches(1.42), CW,
          [("One of several possible approaches. Every input is a working assumption, listed openly on the final page \u2014 annual mileage is the single biggest swing factor.",
            11, False, MUTED, BODY_FONT, 0)])
    _footer(s, "Nothing here is a result. These are the inputs, shown so they can be argued with before any percentage is produced.")


def s_what_pms():
    s = add()
    y = _header(s, "The subject", "Periodic Maintenance Service \u2014 what it is",
                "The IML framing, kept as it was written: a joint project, a clear definition, and a measurable opportunity.")
    items = [
        ("What it is", NAVY,
         "A joint ISZE \u2013 IML project to identify and capture untapped PMS parts sales potential. PMS parts are the oil, fuel and air filters, clutch and brake."),
        ("The opportunity", TERRA,
         "PMS parts are the most frequent and predictable maintenance need across the car parc. The analysis shows how much of that theoretical potential ISZE is capturing today."),
        ("Why it matters", GREEN,
         "These parts come back on a known rhythm. If the vehicle stays with the network, the demand is secured. If it does not, the same part is bought outside \u2014 and we never see it."),
    ]
    row_h = Inches(1.62)
    for i, (head, colour, body) in enumerate(items):
        yy = y + i * (row_h + Inches(0.22))
        _rect(s, M, yy, CW, row_h, PAPER)
        _rect(s, M, yy, Inches(0.06), row_h, colour)
        _text(s, M + Inches(0.3), yy + Inches(0.22), Inches(2.6), Inches(0.3),
              [(head, 14, True, colour, HEAD_FONT, 0)])
        _text(s, M + Inches(3.1), yy + Inches(0.2), CW - Inches(3.5), row_h - Inches(0.35),
              [(body, 12.5, False, INK, BODY_FONT, 0)], line_spacing=1.12)
    _footer(s, "Wording follows the IML framing of PMS as an FY27 project, so the same language is used on both sides of the table.")


def s_why_care():
    s = add()
    y = _header(s, "The commercial case", "Why this is worth doing \u2014 in plain terms",
                "No percentages on this page. These are the reasons the exercise exists, and they are the same for ISZE and for a distributor.")
    cards = [
        ("Predictable demand", "A vehicle in service needs the same parts on the same rhythm. That is a demand we can plan for, not chase."),
        ("Scale effect", "A small improvement in retention per vehicle repeats across every vehicle in the parc. The same effort, multiplied."),
        ("The workshop is the gate", "The scheduled service is the moment the vehicle is with us. If the right parts are not fitted then, they are bought elsewhere."),
        ("Dealer value", "Boarding gives the dealer a reason to keep the vehicle on the schedule \u2014 and a reason to use the network's parts."),
        ("Protects the base", "Retention on maintenance parts protects the aftersales base that funds everything else."),
        ("One method for all", "Agreed inputs mean a market can compare itself with a peer and know the comparison is fair."),
    ]
    cw = (CW - Inches(0.45)) / 3
    ch = Inches(1.68)
    for i, (head, body) in enumerate(cards):
        x = M + (i % 3) * (cw + Inches(0.225))
        yy = y + (i // 3) * (ch + Inches(0.26))
        _rect(s, x, yy, cw, ch, PAPER)
        _rect(s, x, yy, cw, Inches(0.05), TERRA if i in (2, 4) else NAVY)
        _text(s, x + Inches(0.2), yy + Inches(0.2), cw - Inches(0.4), Inches(0.32),
              [(head, 12.5, True, NAVY, HEAD_FONT, 0)])
        _text(s, x + Inches(0.2), yy + Inches(0.6), cw - Inches(0.4), Inches(1.0),
              [(body, 10.5, False, INK, BODY_FONT, 0)], line_spacing=1.08)
    _footer(s, "The argument is the same in every market: the demand is already generated by vehicles we have already sold.")


def s_lenses():
    s = add()
    y = _header(s, "How it is used", "Two lenses, per market \u2014 and the second one is the reason to join",
                "The exercise produces one method and two ways of reading it. The second lens only exists if markets take part.")
    colw = (CW - Inches(0.34)) / 2
    blocks = [
        ("Lens 1 \u2014 PMS items compared", NAVY, GREEN,
         "Within your own market: why is one category captured at twice the rate of another?",
         "Points straight at where promotion, bundling and dealer focus actually move the needle.",
         ["Filters", "Brake", "Clutch", "Urea and other scheduled items"]),
        ("Lens 2 \u2014 markets compared", TERRA, TERRA,
         "Anonymised peer view: comparable parc size, different coverage.",
         "Shows what the higher-coverage markets are doing differently \u2014 diagnostic for management, positional for the business.",
         ["Similar parc, different result", "Peer comparison stays anonymous", "Best practice travels"]),
    ]
    for i, (title, colour, accent, lead, body, bullets) in enumerate(blocks):
        x = M + i * (colw + Inches(0.34))
        _rect(s, x, y, colw, Inches(3.05), PAPER)
        _rect(s, x, y, Inches(0.06), Inches(3.05), colour)
        _text(s, x + Inches(0.26), y + Inches(0.22), colw - Inches(0.5), Inches(0.34),
              [(title, 15, True, colour, HEAD_FONT, 0)])
        _text(s, x + Inches(0.26), y + Inches(0.68), colw - Inches(0.5), Inches(0.7),
              [(lead, 12, False, INK, BODY_FONT, 0)], line_spacing=1.1)
        _text(s, x + Inches(0.26), y + Inches(1.42), colw - Inches(0.5), Inches(0.85),
              [(body, 11, False, MUTED, BODY_FONT, 0)], line_spacing=1.08)
        runs = [("\u2013   " + b, 10.5, False, INK, BODY_FONT, 0) for b in bullets]
        _text(s, x + Inches(0.26), y + Inches(2.24), colw - Inches(0.5), Inches(0.7),
              runs, space_after=4)
    _footer(s, "The peer lens cannot be built by a single distributor alone \u2014 that is why participation is the ask, not a favour.")


def s_rollout():
    s = add()
    y = _header(s, "Plan", "FY27 rollout \u2014 every ISZE market, one common model",
                "The exercise only works if every market participates. The method is fixed first; the market action follows.")
    quarters = [
        ("Q1", "Align", "Data collection and methodology alignment, market by market.", NAVY),
        ("Q2", "Calculate", "Coverage calculation and the first analyses.", NAVY),
        ("Q3", "Prioritise", "Market action plans from the findings.", TERRA),
        ("Q4", "Act and refine", "Implementation, and the feedback loop back into the model.", TERRA),
    ]
    cw = (CW - Inches(0.45)) / 4
    for i, (q, head, body, colour) in enumerate(quarters):
        x = M + i * (cw + Inches(0.15))
        _rect(s, x, y, cw, Inches(2.15), PAPER)
        _rect(s, x, y, cw, Inches(0.05), colour)
        _text(s, x + Inches(0.2), y + Inches(0.2), cw - Inches(0.4), Inches(0.32),
              [(q, 20, False, colour, HEAD_FONT, 0)])
        _text(s, x + Inches(0.2), y + Inches(0.68), cw - Inches(0.4), Inches(0.3),
              [(head, 13, True, NAVY, HEAD_FONT, 0)])
        _text(s, x + Inches(0.2), y + Inches(1.08), cw - Inches(0.4), Inches(0.95),
              [(body, 10.5, False, INK, BODY_FONT, 0)], line_spacing=1.08)

    y2 = y + Inches(2.45)
    _rect(s, M, y2, CW, Inches(1.05), PAPER)
    _rect(s, M, y2, Inches(0.06), Inches(1.05), GREEN)
    _text(s, M + Inches(0.28), y2 + Inches(0.18), CW - Inches(0.6), Inches(0.75), [
        ("The exercise only works if every market participates \u2014 that is the ask.", 13, True, GREEN, BODY_FONT, 0),
        ("A market that joins early helps shape the model every other market will eventually be measured against.", 11, False, INK, BODY_FONT, 0),
    ], space_after=5, line_spacing=1.05)
    _footer(s, "FY27 phasing as presented at the conference. Nothing is measured market by market until Q1 alignment is complete.")


def s_benefits():
    s = add()
    y = _header(s, "For distributors", "What you get from joining the exercise",
                "Four returns, and one of them is influence over the method itself.")
    blocks = [
        ("Visibility", "Your own parc and capture rate, in one place. A permanent business intelligence capability that today no single distributor can build alone."),
        ("Lost sales, by category", "Which categories are most under-captured, so promotion, bundling and contract design are aimed at the actual gap rather than a gut feeling."),
        ("Anonymised peer benchmark", "Where you stand against comparable distributors. Diagnostic for management, positional for the business."),
        ("Influence on the method", "Early movers help shape the model that everyone else will eventually be measured against. The partner incentive structure is being developed with IML."),
    ]
    cw = (CW - Inches(0.3)) / 2
    ch = Inches(1.72)
    for i, (head, body) in enumerate(blocks):
        x = M + (i % 2) * (cw + Inches(0.3))
        yy = y + (i // 2) * (ch + Inches(0.28))
        _rect(s, x, yy, cw, ch, PAPER)
        _rect(s, x, yy, cw, Inches(0.05), TERRA if i in (1, 2) else NAVY)
        _text(s, x + Inches(0.24), yy + Inches(0.2), cw - Inches(0.48), Inches(0.34),
              [(head, 14, True, NAVY, HEAD_FONT, 0)])
        _text(s, x + Inches(0.24), yy + Inches(0.64), cw - Inches(0.48), Inches(1.0),
              [(body, 11, False, INK, BODY_FONT, 0)], line_spacing=1.1)
    _footer(s, "The returns are the same for every participant. The peer benchmark is what makes joining worth more than watching from outside.")


def s_roles():
    s = add()
    y = _header(s, "Working together", "Who does what",
                "The division of labour is simple: IML sets the schedule, ISZE builds the model, the distributor supplies the market reality.")
    rows = [
        ("IML", "Owns the service schedule and the reference intervals. Confirms the replacement frequencies used in the model.", NAVY),
        ("ISZE", "Builds and runs the model for every market. Provides the analysis, the benchmarks and the commercial support route.", TERRA),
        ("Distributor", "Supplies its own parc and sales reality \u2014 units in service and what it actually sold. Challenges the assumptions where they do not match its market.", GREEN),
    ]
    row_h = Inches(1.35)
    for i, (who, what, colour) in enumerate(rows):
        yy = y + i * (row_h + Inches(0.22))
        _rect(s, M, yy, CW, row_h, WHITE, LINE)
        _rect(s, M, yy, Inches(2.3), row_h, colour)
        _text(s, M + Inches(0.26), yy + Inches(0.5), Inches(1.9), Inches(0.34),
              [(who, 15, True, WHITE, HEAD_FONT, 0)])
        _text(s, M + Inches(2.62), yy + Inches(0.28), CW - Inches(2.95), Inches(0.9),
              [(what, 12, False, INK, BODY_FONT, 0)], line_spacing=1.1)
    _footer(s, "Nothing in the model is ownerless: every input has a named source and a named owner.")


def s_assumptions():
    s = add()
    y = _header(s, "Honesty page", "Assumptions and open questions",
                "Every line below is open for distributor input. That is the exercise \u2014 not a finished answer being presented.")
    items = [
        ("Annual mileage assumption", "Varies per market, and it is the single biggest swing factor \u2014 two recent reference studies used different annual distances. A large change here moves every category."),
        ("Active share of the parc", "The share of units in operation that is genuinely in service. Reference studies range widely, so the ratio is stated rather than assumed."),
        ("The parc base", "Built from registration and VIN data. Grey imports and older units may be missing from it."),
        ("Replacement frequency per category", "The reference intervals are a starting point. Real intervals depend on duty cycle, segment and regulation."),
        ("Basket scope", "Five categories today. Adding items widens the addressable demand and changes the picture."),
        ("Cross-fitment", "Not in the model today. It is the likely explanation for any market that reads above full capture, and it needs resolving before that reading is treated as fact."),
    ]
    cw = (CW - Inches(0.3)) / 2
    ch = Inches(1.44)
    for i, (head, body) in enumerate(items):
        x = M + (i % 2) * (cw + Inches(0.3))
        yy = y + (i // 2) * (ch + Inches(0.2))
        _rect(s, x, yy, cw, ch, PAPER)
        _rect(s, x, yy, Inches(0.05), ch, TERRA)
        _text(s, x + Inches(0.22), yy + Inches(0.16), cw - Inches(0.44), Inches(0.3),
              [(head, 11.5, True, NAVY, BODY_FONT, 0)])
        _text(s, x + Inches(0.22), yy + Inches(0.5), cw - Inches(0.44), Inches(0.9),
              [(body, 10, False, INK, BODY_FONT, 0)], line_spacing=1.06)
    _footer(s, "If an assumption is wrong, the model changes. That is why the assumptions are shown before any result is quoted.")


def s_close():
    s = add()
    _rect(s, 0, 0, W, H, NAVY)
    _rect(s, 0, Inches(1.5), W, Inches(0.05), TERRA)
    _text(s, M, Inches(0.8), CW, [("The ask", 11, True, PALEBLUE, BODY_FONT, 0)])
    _text(s, M, Inches(1.85), Inches(11.6),
          [("Join the exercise, and bring your market reality", 30, False, WHITE, HEAD_FONT, 0)])
    items = [
        "Confirm the replacement frequencies and the annual mileage basis for your market.",
        "Provide units in service and your own parts sales, so the comparison is built on your data rather than a model of it.",
        "Challenge any assumption that does not match what you see \u2014 that is what the exercise is for.",
        "Take part in the peer comparison. It only exists if markets are in it.",
    ]
    yy = Inches(3.05)
    for txt in items:
        _rect(s, M, yy + Inches(0.06), Inches(0.16), Inches(0.16), TERRA)
        _text(s, M + Inches(0.4), yy, Inches(11.1), Inches(0.6),
              [(txt, 12.5, False, RGBColor(0xE6, 0xEB, 0xF3), BODY_FONT, 0)], line_spacing=1.08)
        yy += Inches(0.72)
    _text(s, M, Inches(6.35), Inches(11.6),
          [("This is not a one-time analysis. It is the start of one shared parts opportunity model \u2014 improved with every market that joins.",
            11, False, RGBColor(0xA9, 0xB7, 0xCB), BODY_FONT, 0)])


s_cover()
s_invisible()
s_two_questions()
s_how()
s_what_pms()
s_why_care()
s_lenses()
s_rollout()
s_benefits()
s_roles()
s_assumptions()
s_close()

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print("saved:", OUT)
print("slides:", len(prs.slides._sldIdLst))
