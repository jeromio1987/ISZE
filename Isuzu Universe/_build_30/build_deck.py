# -*- coding: utf-8 -*-
r"""Talk deck for ISUZU / UNIVERSE 3.0.

This is a talk deck, not a re-render of the paper. One idea per slide, few words on the slide,
and the argument carried in the speaker notes. The charts are the same images the paper uses, so
the two documents cannot disagree.

Run from the Isuzu Universe folder:  python _build_30\build_deck.py
"""
import os
import sys

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIGDIR = os.path.join(HERE, "figures")
OUT = os.environ.get("UNIVERSE_DECK_OUT",
                     os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_DECK_2026-09-23.pptx"))

sys.stdout.reconfigure(encoding="utf-8")

NAVY = RGBColor(0x15, 0x23, 0x3C)
NAVY2 = RGBColor(0x1A, 0x2B, 0x4A)
TERR = RGBColor(0xC0, 0x55, 0x2D)
PAPER = RGBColor(0xF7, 0xF4, 0xEE)
INK = RGBColor(0x22, 0x22, 0x22)
GREY = RGBColor(0x5B, 0x64, 0x72)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINEC = RGBColor(0xD8, 0xD2, 0xC8)

W, H = Inches(13.333), Inches(7.5)


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(slide, x, y, w, h, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
    sh.shadow.inherit = False
    return sh


def text(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    first = True
    for txt, size, color, bold, font, space in runs:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.bold = bold
        r.font.name = font
    return tb


def notes(slide, body):
    slide.notes_slide.notes_text_frame.text = body


def title_slide(prs, eyebrow, title, strap, foot):
    s = blank(prs)
    rect(s, 0, 0, W, H, NAVY)
    rect(s, Inches(0.9), Inches(1.35), Inches(1.6), Pt(4), TERR)
    text(s, Inches(0.9), Inches(0.85), Inches(11), Inches(0.4),
         [(eyebrow, 13, RGBColor(0xC9, 0xD2, 0xDE), True, "Arial", 0)])
    text(s, Inches(0.9), Inches(1.85), Inches(11.4), Inches(2.2),
         [(title, 52, WHITE, True, "Georgia", 0)])
    text(s, Inches(0.9), Inches(3.7), Inches(10.6), Inches(1.4),
         [(strap, 20, RGBColor(0xD9, 0xDF, 0xE7), False, "Georgia", 0)])
    rect(s, Inches(0.9), Inches(6.05), Inches(3.2), Pt(3), TERR)
    text(s, Inches(0.9), Inches(6.3), Inches(11.4), Inches(0.6),
         [(foot, 12, RGBColor(0x9F, 0xB0, 0xC6), False, "Arial", 0)])
    notes(s, "This deck follows the 25-page paper ISUZU / UNIVERSE 3.0 dated 23 September 2026. "
             "It carries the same numbers and the same recommendations. Use it to talk from, not "
             "to read. Three decisions are being asked for: campaign support with a size floor, "
             "ten dealer invitations, and which two capabilities to build first.")
    return s


def statement(prs, kicker, big, support, note):
    s = blank(prs)
    rect(s, 0, 0, W, H, PAPER)
    rect(s, 0, 0, W, Inches(0.16), NAVY)
    text(s, Inches(0.9), Inches(0.85), Inches(11), Inches(0.4),
         [(kicker.upper(), 12, TERR, True, "Arial", 0)])
    text(s, Inches(0.9), Inches(1.45), Inches(11.4), Inches(3.0),
         [(big, 40, NAVY, True, "Georgia", 0)])
    if support:
        text(s, Inches(0.9), Inches(4.6), Inches(10.6), Inches(2.2),
             [(support, 17, INK, False, "Arial", 8)])
    notes(s, note)
    return s


def chart_slide(prs, kicker, takeaway, img, caption, note):
    s = blank(prs)
    rect(s, 0, 0, W, H, WHITE)
    rect(s, 0, 0, W, Inches(0.16), NAVY)
    text(s, Inches(0.8), Inches(0.55), Inches(11.7), Inches(0.4),
         [(kicker.upper(), 11.5, TERR, True, "Arial", 0)])
    text(s, Inches(0.8), Inches(0.98), Inches(11.7), Inches(0.9),
         [(takeaway, 27, NAVY, True, "Georgia", 0)])
    path = os.path.join(FIGDIR, img)
    from PIL import Image
    with Image.open(path) as im:
        ar = im.width / im.height
    # fit the chart into the content band, then centre it and hang the caption right under it
    band_top, band_h = Inches(1.95), Inches(4.55)
    box_w = Inches(11.7)
    box_h = box_w / ar
    if box_h > band_h:
        box_h = band_h
        box_w = box_h * ar
    top = band_top + (band_h - box_h) / 2
    s.shapes.add_picture(path, int((W - box_w) / 2), int(top), width=int(box_w))
    cap_y = top + box_h + Inches(0.16)
    if cap_y > Inches(6.70):
        cap_y = Inches(6.70)
    text(s, Inches(0.8), int(cap_y), Inches(11.7), Inches(0.6),
         [(caption, 11, GREY, False, "Arial", 0)])
    notes(s, note)
    return s


def table_slide(prs, kicker, title, rows, widths, note):
    s = blank(prs)
    rect(s, 0, 0, W, H, WHITE)
    rect(s, 0, 0, W, Inches(0.16), NAVY)
    text(s, Inches(0.8), Inches(0.55), Inches(11.7), Inches(0.4),
         [(kicker.upper(), 11.5, TERR, True, "Arial", 0)])
    text(s, Inches(0.8), Inches(0.98), Inches(11.7), Inches(0.9),
         [(title, 27, NAVY, True, "Georgia", 0)])
    nrows, ncols = len(rows), len(rows[0])
    top = Inches(2.05)
    shape = s.shapes.add_table(nrows, ncols, Inches(0.8), top,
                               Inches(11.7), Inches(0.42) * nrows)
    tbl = shape.table
    total = sum(widths)
    for i, wd in enumerate(widths):
        tbl.columns[i].width = Emu(int(Inches(11.7) * wd / total))
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(0.42 if r else 0.34)
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = str(val)
            cell.margin_left = Inches(0.10)
            cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = NAVY
            else:
                cell.fill.fore_color.rgb = WHITE if r % 2 else RGBColor(0xFA, 0xF8, 0xF3)
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(12 if r else 11.5)
                    run.font.name = "Arial"
                    run.font.bold = (r == 0) or (c == 0 and r > 0)
                    run.font.color.rgb = WHITE if r == 0 else INK
    notes(s, note)
    return s


def closing(prs, title, lines, note):
    s = blank(prs)
    rect(s, 0, 0, W, H, NAVY)
    rect(s, Inches(0.9), Inches(1.0), Inches(1.6), Pt(4), TERR)
    text(s, Inches(0.9), Inches(1.5), Inches(11.4), Inches(1.2),
         [(title, 40, WHITE, True, "Georgia", 0)])
    runs = []
    for i, ln in enumerate(lines):
        runs.append((ln, 17, RGBColor(0xD9, 0xDF, 0xE7), False, "Arial", 14))
    text(s, Inches(0.9), Inches(3.0), Inches(10.6), Inches(3.4), runs)
    notes(s, note)
    return s


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    title_slide(
        prs, "ISUZU / PARTS EUROPE  ·  COMMERCIAL VISION",
        "Universe 3.0",
        "Give distributors and dealers tools worth using.<br>Earn the information that makes those tools better.",
        "Version 3.0  ·  23 September 2026  ·  proposed product and participation  ·  for discussion")

    statement(
        prs, "the three decisions",
        "Three things to decide.",
        "Campaign support, with a size floor.  |  Ten dealer invitations.  |  Which two capabilities to build first.",
        "Everything else in the paper supports these three. Section 4 of the paper is the money. "
        "Section 8 is what dealers and distributors actually do. Section 9 is the sequence and the "
        "stop condition. If the room only has twenty minutes, those three pages carry the case.")

    statement(
        prs, "the scope boundary",
        "Routine service is not the product.",
        "Availability enquiries, ordinary part and BVP lookups, day-to-day quotations and support "
        "administration stay in the existing business. They are not rewards for participation and "
        "not a bargaining instrument for more data.",
        "This is the single sentence that changes how a distributor's parts manager reads the "
        "approach. The programme has asked for information for years with insufficient visible "
        "value returned. The boundary is what makes this request different: nothing in the existing "
        "support service gets better or worse depending on what a participant sends us. Evidence "
        "from normal operations may inform an agreed analysis. Its workflow does not become a module.")

    chart_slide(
        prs, "the portfolio",
        "Four foundations. Five tools. One class of decision.",
        "f03_portfolio.png",
        "Figure 3 of the paper. Each tool uses only the evidence relevant to its own question.",
        "The four foundations are product structure from AIM, declared practices from IDS, market "
        "and fleet context from PRISM, and the parts business itself. The five tools are the Atlas, "
        "the IDS studio, the range and campaign planner, the pricing and margin lab, and market "
        "intelligence. A participant usually starts with one of them, which is why this is a "
        "portfolio and not a single application. A monolithic product would force every user "
        "through the same opening screen.")

    chart_slide(
        prs, "why product detail",
        "Value fell 13.0%. Volume fell 25.4%.",
        "f01_ituk_value_vs_volume.png",
        "Figure 1 of the paper. ITUK brake-pad source category, full calendar 2024 and 2025. Measured.",
        "This is the whole commercial argument on one chart. Isuzu Truck UK's brake-pad billing fell "
        "from 347,389 to 302,366 euro, a reduction of 45,023 euro or 13.0 per cent. Recorded quantity "
        "fell from 4,562 to 3,402 units, which is 25.4 per cent. Value fell less than volume. A "
        "revenue-only view would suggest a demand problem. A quantity-only view would suggest a "
        "pricing problem. Neither alone tells a distributor where to look. The contextual fleet is "
        "22,389 trucks and it is not the eligible population for every pad reference.")

    chart_slide(
        prs, "concentration",
        "One product form carries 95.7% of it.",
        "f04_brake_split.png",
        "Figure 4 of the paper. Three selected ITUK source categories, CY2025 against CY2024. Measured.",
        "Across brake pads, rotors and shoes the combined reduction is 47,069 euro, and pads account "
        "for 45,023 of it. That moves the starting decision from 'braking products are down' to "
        "'brake pads are down'. It does not support one remedy across every braking product, and it "
        "does not make the reduction recoverable revenue. The next step is the contributing "
        "references, not a discount.")

    chart_slide(
        prs, "the trap this prevents",
        "The combined offer grew while Genuine fell.",
        "f05_portugal_clutch.png",
        "Figure 5 of the paper. I Motors, Portugal, clutch-kit source category. Measured.",
        "Combined clutch-kit billing in Portugal rose 5.8 per cent, from 29,960 to 31,702 euro. "
        "Genuine fell from 2,902 to 2,058 while BVP rose from 27,058 to 29,645. Quantity was almost "
        "unchanged: 462 kits to 461. A Genuine-only view would have launched a recovery campaign for "
        "a line whose total business grew. The tool exists to prevent that mistake as much as to "
        "find opportunities.")

    chart_slide(
        prs, "where the money sits",
        "The deepest concession is in the smallest markets.",
        "f06_concession_by_db.png",
        "Figure 6 of the paper. PMS lines carrying a reference price, 24 distributors, 2025. Measured.",
        "Of 6.65 million euro of PMS billing in 2025, 8.4 per cent sat at least 20 per cent under the "
        "reference price, down from 13.0 per cent in 2024. That decline is favourable. But look at "
        "where the deep discount sits: Ukraine 28.2 per cent of 203 thousand, Portugal 20.2 per cent "
        "of 338 thousand, IUK 16.9 per cent of 1.27 million, Germany 16.6 per cent of 416 thousand. "
        "A programme that pays per campaign without a size floor would spend itself in the small "
        "markets. That is the reason for the floor in the next slide.")

    chart_slide(
        prs, "by product family",
        "Two families carry the deep discount. Two carry almost none.",
        "f07_concession_by_family.png",
        "Figure 7 of the paper. Eight largest PMS families by 2025 billing. Measured.",
        "Brake-pad-front runs 36 per cent deep discount on 423 thousand euro, and blower filter 25.2 "
        "per cent on 374 thousand. Those are modest bases with high shares, which is the shape of a "
        "handful of large deals rather than a broad pricing position. Brake rotors run 3.4 per cent "
        "on 1.3 million and oil filters 1.5 per cent on 557 thousand. Their pricing is settled, so "
        "their opportunity, if there is one, is not price.")

    table_slide(
        prs, "the denominator",
        "What the money is measured against.",
        [["Basis", "Value"],
         ["Network parts billed to distributors, calendar 2025", "32,381,312 euro"],
         ["The 18 markets carrying a fleet figure", "30,756,772 euro"],
         ["The 100,000 euro route as a share of one year", "0.31 per cent"],
         ["The 300,000 euro route on the same basis", "0.93 per cent"]],
        [3.0, 1.0],
        "The programme is proposing to spend between three-tenths of one per cent and nine-tenths of "
        "one per cent of a single year's parts billing. That is the right size for a pilot and the "
        "wrong size for a platform build. It also means the programme does not need to move the whole "
        "business to justify itself, and it must not be presented as though it will. Measured from "
        "the GPS distributor file, 2025 rows.")

    chart_slide(
        prs, "the hurdle",
        "Forty qualifying actions is the break-even.",
        "f08_hurdle.png",
        "Figure 8 of the paper. Hypothetical arithmetic on stated inputs, not a forecast.",
        "At 500 euro of contribution per beneficial action, 100,000 euro needs 200 of them. At 2,500 "
        "euro per action it needs forty. At 5,000 it needs twenty. Two consequences. First, a "
        "ten-campaign pilot is evidence, not a return: ten campaigns at 2,500 euro is 25,000 against "
        "a 100,000 envelope. Second, the honest break-even is forty qualifying actions, and that "
        "number belongs in the funding discussion rather than in a footnote after approval. The "
        "hurdle rises further once internal effort sits outside the envelope.")

    chart_slide(
        prs, "the mechanism",
        "500 euro of gross profit turns on scope alone.",
        "f09_scope_effect.png",
        "Figure 9 of the paper. 100-unit baseline at 100 euro net and 70 euro parts cost, 20 extra units, 5% concession.",
        "On a 100-unit baseline, a 5 per cent concession applied to all 120 units produces 3,000 euro "
        "of parts gross profit. Applied only to the 20 additional units, with the baseline keeping "
        "its original price, it produces 3,500. The 500 euro difference is scope and nothing else, "
        "and it assumes no demand response at all. That is why an additional-only structure is the "
        "one to test first, and why a blanket concession should not become the standard.")

    table_slide(
        prs, "the recommendation",
        "What to fund, and the floor.",
        [["Line", "Amount", "What has to be demonstrated"],
         ["Campaign support", "35,000 to 50,000", "8 to 12 campaigns against the size floor"],
         ["Dealer enablement", "15,000 to 25,000", "25 to 40 accepted setup tasks at 600 euro"],
         ["Independent evaluation", "10,000 to 15,000", "Two waves at 90 and 180 days, including returns"],
         ["Total campaign cash", "60,000 to 90,000", "Inside the existing 100,000 euro route"],
         ["Minimum campaign size", "150,000 eligible", "Below this the campaign cannot pay for its own preparation"]],
        [1.5, 1.3, 3.4],
        "This is a recommendation inside the existing zero, one hundred thousand and three hundred "
        "thousand euro planning envelopes. It is not a new budget request and not an approved "
        "expenditure. The minimum campaign size of 150,000 euro of eligible billing is the load-"
        "bearing number: below it, the contribution a single campaign can produce at our own hurdle "
        "does not cover the analytical preparation it costs. Campaign support also has to be a named "
        "line rather than a note. Saying it needs its own commercial treatment is a control, not an "
        "answer.")

    chart_slide(
        prs, "the dealer",
        "The dealer's first session must be its own data.",
        "f15_ids_scores.png",
        "Figure 15 of the paper. Dealer network file, 20 September 2026. Measured.",
        "490 of the 519 dealers in our network file carry a recorded Dealer Standards score, minimum "
        "above zero, maximum 100, average 79.3. A further 29 recorded no answers at all and are held "
        "apart from the distribution, because no score exists for them. That is almost all of the known "
        "already on file, and it is the only place in this programme where ISZE holds something a "
        "dealer will want to look at and cannot easily assemble itself. So the IDS profile should be "
        "the opening offer, not a later step. Right now the design brings a review to the dealer "
        "first, which reads as a supplier's opinion of its business.")

    chart_slide(
        prs, "the dealer, step by step",
        "Arrive prepared. Ask for a correction, not for data.",
        "f14_dealer_join.png",
        "Figure 14 of the paper. Proposed participant journey. No dealer has been invited.",
        "The distributor chooses the invitation; ISZE never approaches a dealer directly. The first "
        "item opened is a review built from information already held, so there is no form, no portal "
        "registration and no upload in the first session. The dealer confirms or corrects one "
        "interpretation. 'Your reading is wrong' and 'no action is needed' are both successful "
        "outcomes. Then the IDS profile, then the plan, then the next eligible task rather than the "
        "next report.")

    table_slide(
        prs, "will they join",
        "Where the design holds and where it breaks.",
        [["Step", "Score", "Why"],
         ["Dealer accepts the first prepared review", "55", "Ten minutes, and it arrives finished"],
         ["Dealer corrects the interpretation", "70", "Low cost and self-interested"],
         ["Dealer uses its own IDS profile", "65", "The strongest hook in the programme"],
         ["Dealer returns for a second task", "30", "No cash, no visibility gain, no trigger"],
         ["Dealer shares beyond a correction", "20", "Nothing in the design creates the reason"],
         ["Distributor accepts the opening", "75", "Cheap, no new reporting burden"],
         ["Distributor uses the review internally", "45", "Depends on answering a question it already had"]],
        [2.6, 0.7, 2.6],
        "These are judgements on the design, not measurements, and they are here so the design can be "
        "argued with. The dealer position is credible in its first three steps and unproven after "
        "them. Three changes would raise it, in order of effect: make the IDS profile the opening "
        "rather than a later step; fund a bounded setup task so the dealer's time has a price; and "
        "make the follow-through visible, because invisible follow-through is what ended the previous "
        "data requests. On the distributor side, the gap between 75 for accepting and 45 for using is "
        "the whole problem.")

    statement(
        prs, "the base rate",
        "519 assessments exist because an obligation was attached.",
        "That is what this network produces when a dealer-facing requirement is enforced. Anything in "
        "this programme that scores below that needs a reason the participant can feel, and there are "
        "only two available: money, and a visible improvement in its own business.",
        "This is the calibration for the whole participation discussion. We have 519 dealer self-"
        "assessments across 19 networks today. France 84, Spain 45, UK CV 44, UK LCV 43, Italy 41, "
        "Norway 38, Belgium 34, Greece 34, Israel LCV 29, Poland 23, Switzerland 22, Denmark 20, "
        "Hungary 19, Portugal 16, Romania 15, Netherlands 9, plus one each in Malta, Cyprus and "
        "Luxembourg. That is the base rate, and goodwill alone has never beaten it.")

    table_slide(
        prs, "the price of a dealer",
        "15,000 euro is a gesture or a programme.",
        [["Dealer basis", "Count", "Consequence for the enablement line"],
         ["Dealers with a recorded IDS assessment", "519", "28.90 euro each, if spread across the estate"],
         ["Portugal only", "16", "937.50 euro each, inside the pilot market"],
         ["ITUK and Portugal together", "60", "250.00 euro each"]],
        [2.4, 0.7, 3.0],
        "This table decides whether dealer enablement is a programme or a gesture. Fifteen thousand "
        "euro spread across 519 dealers buys nothing that survives contact with a dealer principal. "
        "The same money spent as twenty-five accepted setup tasks at 600 euro in two pilot markets "
        "buys twenty-five completed onboarding experiences. The recommendation is the second, and it "
        "means the enablement line is spent as accepted tasks rather than as a per-dealer entitlement.")

    chart_slide(
        prs, "the distributor",
        "The gap between accepting and using is the problem.",
        "f16_exchange.png",
        "Figure 16 of the paper. Proposed participation design. Payment for data volume is excluded.",
        "The distributor's position is stronger than the dealer's and simpler. It already has an "
        "obligation to report and already has a rebate linked to reporting, so the change being "
        "proposed is what comes back. Accepting scores 75 because it is cheap and adds no reporting "
        "burden. Using the review scores 45, because a review that is merely available is a review "
        "that is not read. Two changes close that gap: answer a question the distributor already had, "
        "and make its own dealer development the visible output, so the review serves its commercial "
        "interest rather than ours.")

    statement(
        prs, "what not to do",
        "Six things that would kill it.",
        "Never pay per submitted record or per disclosed field. Never make ordinary service "
        "conditional on a contribution. Never build a public dealer league table. Never ask for "
        "dealer resale prices by default. Never approach a dealer directly. Never count logins or "
        "uploads as participation.",
        "Each of these is tempting and each one destroys the premise. Paying per record rewards "
        "disclosure volume rather than useful work. Conditioning ordinary service turns a normal "
        "service into a bargaining instrument. A league table cannot be compared across business "
        "sizes because turnover favours the large and self-assessment scores have different coverage. "
        "Resale prices are the most sensitive item on the list and the core review does not need them.")

    table_slide(
        prs, "the sequence",
        "Prove usefulness before broadening anything.",
        [["Stage", "Result", "Evidence to move on"],
         ["Agree the scope and portfolio", "Five tools, routine service excluded", "Paper, deck and showcase say the same thing"],
         ["Pin the classification release", "One named file, version and date", "Reproduce a family and product-form view"],
         ["Open two prepared views", "Atlas view and IDS profile", "A participant finds it clearer than the existing review"],
         ["Run the dealer sample", "Ten dealers in two markets", "Correction, output, effort and reasons for non-use"],
         ["Run the campaign line", "Two qualifying campaigns", "Contribution measured on the same scope before and after"],
         ["Evaluate, then extend or narrow", "A stated result, favourable or not", "Real later evidence, not a rendered screen"]],
        [1.6, 1.7, 2.4],
        "No elapsed-week estimate from the earlier support-centred roadmap is inherited as a promise. "
        "The first stage is nearly free and it is the one that unblocks everything else: the paper, "
        "the deck and the showcase have to tell the same story, because at the moment two documents "
        "on disk describe two different product ranges. Stage two is a day of work and it is the only "
        "blocker ISZE can close entirely on its own.")

    statement(
        prs, "the stop condition",
        "It stops. It does not pause.",
        "If, after two eligible cycles, no participant can name a decision the tool changed, or if a "
        "confidentiality or identity weakness cannot be closed, the programme stops. It does not add "
        "a report, and it does not broaden the participant population to look for a better sample.",
        "The honest test is simple. If the incentive that currently produces the file were removed "
        "tomorrow, would anyone open the tool anyway? That question is the difference between a "
        "programme and a compliance exercise. The go condition is equally specific: a real "
        "participant completed a real analytical task, the output was correct on its source, and the "
        "participant can name the decision it changed. A rendered screen is not evidence.")

    statement(
        prs, "the boundaries",
        "What this paper does not claim.",
        "No realised return. No approved budget. No forecast of incremental sales. No participant has "
        "accepted anything. There is no backend, no shared case service and no production identity on "
        "this machine, and a browser-side allowlist is not access control.",
        "Three competition and copyright rules are proposed as standing constraints, and legal should "
        "review them before any shared output reaches a participant. No exclusivity in exchange for "
        "information. No price coordination between distributors: the tool compares a distributor to "
        "its own history and to permitted aggregate context, and never transmits one distributor's "
        "terms or intentions to another. No resale-price instruction. The European motor-vehicle "
        "block exemption regime runs to 31 May 2028 and nothing in this paper is a legal "
        "determination.")

    closing(
        prs, "Three decisions. Two weeks.",
        ["1  Fund campaign support as a named line of 60,000 to 90,000 euro inside the 100,000 euro route, with a 150,000 euro minimum campaign size.",
         "2  Approve ten dealer invitations in two markets, approached as designed: prepared review, correction, IDS profile, plan.",
         "3  Build the AIM Commercial Atlas and the IDS Development Studio first, once the classification release is pinned to one named file."],
        "That is the ask. The paper is 25 pages and the design annex is separate, so the funding case "
        "does not have a specification in the middle of it. On the numbers: the pilot will not reach "
        "the forty-action break-even. It will produce the first real measurement of the qualifying "
        "rate, and that rate is the number on which any expansion should be decided.")

    prs.save(OUT)
    return OUT


def check(prs_path):
    """A talk deck must not be a screenshot of the paper. Check words per slide and notes."""
    prs = Presentation(prs_path)
    pics = tbls = 0
    on_slide = []
    noted = 0
    for s in prs.slides:
        words = 0
        for sh in s.shapes:
            if sh.shape_type == 13:
                pics += 1
            if sh.has_table:
                tbls += 1
                for r in sh.table.rows:
                    for c in r.cells:
                        words += len(c.text.split())
            if sh.has_text_frame:
                words += len(sh.text_frame.text.split())
        on_slide.append(words)
        nt = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        if len(nt.split()) >= 25:
            noted += 1
    return {"slides": len(prs.slides), "pictures": pics, "tables": tbls,
            "with_notes": noted, "max_words_on_slide": max(on_slide),
            "mean_words_on_slide": round(sum(on_slide) / len(on_slide), 1)}


if __name__ == "__main__":
    p = build()
    print(f"deck: {p}  ({os.path.getsize(p):,} bytes)")
    r = check(p)
    print(f"slides={r['slides']} pictures={r['pictures']} tables={r['tables']} "
          f"slides_with_notes={r['with_notes']}")
    print(f"words on slide: mean {r['mean_words_on_slide']}, max {r['max_words_on_slide']}")
