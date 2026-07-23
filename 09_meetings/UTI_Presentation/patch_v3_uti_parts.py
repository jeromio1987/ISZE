# -*- coding: utf-8 -*-
"""Patch V3.1: UTI Parts / market visibility / win-back slides + speaker guide."""
from __future__ import annotations

import subprocess
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\UTI_Presentation")
PPTX_IN = BASE / "UTI_presentation_V3.1.pptx"
PPTX = PPTX_IN
GUIDE_HTML = BASE / "UTI_Meeting_Speaker_Guide.html"
GUIDE_PDF = BASE / "UTI_Meeting_Speaker_Guide.pdf"

RED = RGBColor(0xCC, 0x0E, 0x1E)
NAVY = RGBColor(0x1A, 0x2B, 0x4A)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY = RGBColor(0xF0, 0xF0, 0xF0)

AGENDA_EXTRA = (
    "\n—  Dealer sell-out vs billing — market visibility & UTI Parts blind spot\n"
    "—  Filter mix vs ITUK — where genuine/BVP share can move\n"
    "—  UTI Parts & win-back — pricing discovery + fleet/R&M follow-up"
)

SLIDE20 = {
    "section": "MARKET VISIBILITY",
    "title": "What we see vs. what leaves the network",
    "takeaways": (
        "—  CY2025: ISZE→UTI billing 125K lines vs UTI dealer sell-out 93K — gap reflects stock, timing, "
        "fleet/workshop channel, or sourcing outside ISZE invoices.\n"
        "—  UTI is ~88% genuine on ISZE billing — not a 'non-genuine account'; the conversation is mix "
        "inside the relationship plus channels we cannot see.\n"
        "—  UTI Parts, local sourcing, and fleet workshops sit outside our data until you share scope and volumes.\n"
        "—  PMS capture gaps (oil filter, clutch FY26) may partly reflect that blind spot — not price alone."
    ),
    "note": (
        "MARKET VISIBILITY (4 min)\n"
        "Frame as data boundary, not accusation. We only see ISZE→UTI billing.\n"
        "CY2025: billing 124,728 qty vs sell-out 92,660 (Dealer_Sellout dashboard).\n"
        "88% genuine-only on billing — overall account is genuine-heavy.\n"
        "ASK: what explains the billing vs sell-out gap? Stock build? Fleet workshops? UTI Parts?\n"
        "Bridge: even with strong billing, PMS denominators suggest demand we do not invoice — size UTI Parts with them."
    ),
}

SLIDE21 = {
    "section": "GENUINE / BVP MIX",
    "title": "Filters — UTI leans BVP where ITUK leans genuine (dealer sell-out CY2025)",
    "table": [
        ["PMS category", "UTI BVP", "ITUK BVP", "UTI − ITUK"],
        ["Oil filter", "56%", "29%", "+27 pp"],
        ["Fuel filter", "49%", "15%", "+33 pp"],
        ["Air filter", "59%", "10%", "+49 pp"],
        ["Brake pad", "~0%", "~0%", "—"],
        ["Clutch kit", "98%", "52%", "+46 pp"],
    ],
    "takeaways": (
        "—  Where a BVP catalogue pair exists, UTI dealer sell-out is far more BVP-heavy than ITUK on filters "
        "(+27 to +49 pp) — mix opportunity inside the relationship, not account disloyalty.\n"
        "—  Fuel + air: pilot genuine at SPA/programme price — ~€65K/yr revenue ceiling if mix moves like ITUK "
        "(excludes oil — genuine element is cheaper at list).\n"
        "—  Clutch kit 98% BVP at sell-out aligns with PMS family capture halving FY25→FY26 — needs workshop/fleet context.\n"
        "—  Source: UTI PartSales YTD + ITUK dealer pivot, AIM buckets, CY2025."
    ),
    "note": (
        "FILTER MIX (4 min)\n"
        "STRONGEST evidence-based commercial slide after visibility.\n"
        "Do NOT say UTI is non-genuine — 88% genuine on billing overall.\n"
        "Conversation: inside BVP-offer categories, UTI picks BVP more than ITUK.\n"
        "Oil filter: do NOT push genuine conversion — BVP element ~€10 vs genuine ~€5 at list; margin loss.\n"
        "Fuel + air: ASK pilot on SPA — ITUK proves genuine filter sales hold in comparable network.\n"
        "Clutch: link to PMS slide — 98% BVP sell-out vs 52% ITUK."
    ),
}

SLIDE22 = {
    "section": "UTI PARTS",
    "title": "UTI Parts — where we can compete (pricing to confirm)",
    "table": [
        ["Category", "ISZE today", "Win-back lever"],
        ["Fuel / air filters", "BVP from ISZE", "SPA + genuine mix like ITUK"],
        ["Oil filter", "BVP from ISZE", "Keep BVP — lead time & service"],
        ["Brake / clutch", "Genuine from ISZE", "Fleet disclosure + programme"],
        ["UTI Parts line", "Unknown to ISZE", "Share price list / sample invoices"],
    ],
    "takeaways": (
        "—  ISZE does not hold UTI Parts prices — we need your catalogue or sample invoices on top maintenance PNs "
        "to compare delivered cost vs ISZE genuine/BVP landed.\n"
        "—  Win-back is conditional: delivered price (SPA) + ~3-week lead time + MOQ — same frame as voorraadbeheer.\n"
        "—  If we are competitive on delivered cost, we want the volume back — supports GPS stretch for both sides.\n"
        "—  Offer: follow-up with fleet & parts leads; joint capture view if they share workshop volumes."
    ),
    "note": (
        "UTI PARTS (5 min)\n"
        "CRITICAL: we cannot quote their UTI Parts prices — discovery, not presentation of facts.\n"
        "ASK directly:\n"
        "• UTI Parts scope — which categories? Dealer network only or fleet workshops too?\n"
        "• Share of maintenance spend on UTI Parts vs ISZE genuine/BVP?\n"
        "• Sample invoices on top 10 filter/brake/clutch PNs — compare delivered street price.\n"
        "• Who owns UTI Parts pricing — can we run a basket benchmark?\n"
        "Win-back levers by category (table on slide).\n"
        "Close loop: if price + lead time work, pilot fuel/air genuine on SPA; keep oil BVP.\n"
        "Schedule fleet/R&M follow-up if appetite (see speaker guide question bank)."
    ),
}

# Prior speaker notes (slides 1–19) — keep in sync with patch_v3_saty_notes.py
SPEAKER_NOTES_BASE: dict[int, str] = {
    1: (
        "OPENING (1 min)\n"
        "Thank them for the time. Frame as joint review: Q1 performance, GPS path, service mix, PMS trends — "
        "and learning how their fleet/R&M and UTI Parts work.\n"
        "Tone: partnership, not audit."
    ),
    2: (
        "AGENDA (1 min)\n"
        "Walk top to bottom; offer to reorder if they have burning topics.\n"
        "Commercial block: sales/BP, GPS, order mix, fill rate.\n"
        "New: market visibility, filter mix, UTI Parts win-back.\n"
        "Analytics: PMS capture (directional — assumptions flagged).\n"
        "Close: fleet/R&M learning + next steps."
    ),
    3: (
        "SALES TABLE (3 min)\n"
        "Let the table speak. Budget and Original BP were identical — one line is correct.\n"
        "ASK if anything looks off vs their internal figures.\n"
        "Bridge to next slide: June is the story."
    ),
    4: (
        "Q1 SALES BRIDGE (4 min)\n"
        "KEY: +38% vs budget is real but SPA-heavy.\n"
        "Apr–May ≈ €201K/mo baseline. June €635K incl. SPA doc 364214 (€277K = 27% of Q1).\n"
        "Even June ex-SPA (~€358K) ≈ 1.8× Apr–May — confirm with them: pull-forward, stock build, or demand?\n"
        "Do NOT say 'problem solved' — full-year GPS discipline still matters.\n"
        "PAUSE for their read on June."
    ),
    5: (
        "GPS EVOLUTION (3 min)\n"
        "DEFINITIONS if asked:\n"
        "• Bars = ISZE parts billing (transport/rebates/credits excluded).\n"
        "• GPS % = NET of warranty: (billing − warranty) ÷ max-spend wallet.\n"
        "• FY24–26 complete fiscal years; FY27 = plan target.\n"
        "Do not name internal planning tools in the room.\n"
        "FY25 warranty €292K depressed net GPS — mention if challenged.\n"
        "Bridge: plan 35.1% → commercial stretch 38.3% (+1.8pp)."
    ),
    6: (
        "FILL RATE (2 min)\n"
        "Chart from internal BI Jul'25–Jun'26. Range 76–86%.\n"
        "Do not over-claim precision. Tie to next slides: planning + order type.\n"
        "ASK: do they track fill rate by order type (SOR vs urgent) internally?"
    ),
    7: (
        "ORDER TYPE / SATY (4 min)\n"
        "Lead with the benchmark table — this is the voorraadbeheer story.\n"
        "~3 weeks sea freight to Israel → high SOR % = ordering ahead, not weak service.\n"
        "UTI 88% SOR / 12% urgent vs CV peers 80%/17% and network 78%/20%.\n"
        "Footnote if asked: SaTy joined on 82% of UTI Q1 € (sales doc join).\n"
        "ASK: does their planning horizon match 3-week lead time? Safety stock rules?"
    ),
    8: (
        "FILL RATE & URGENCY (3 min)\n"
        "Connect low urgent share to fill rate — they plan routine lines forward.\n"
        "RUSH ~1 day vs SOR ~11 days median order-to-invoice (internal SAP).\n"
        "VOR small in € but concentrated in filters/chassis — stock conversation, not blame.\n"
        "Compliment the routine-heavy profile before discussing exceptions."
    ),
    9: "PMS SECTION BREAK (30 sec)\nTransition: shift from billing performance to maintenance-parts capture.\nPMS = interval-driven competitive parts only — not full GPS basket.",
    10: "GPS vs PMS EXPLAINER (2 min)\nGPS = whole genuine basket health. PMS = diagnostic on filters/brakes/clutch.\nUse only if they look lost — otherwise skip quickly.",
    11: "METHODOLOGY VISUAL (1 min)\nParc → interval → potential → capture %. Same logic GPS vs PMS, different scope.\nOptional — skip if time short.",
    12: (
        "PMS ASSUMPTIONS (2 min)\n"
        "Be transparent: actual sales solid; denominators are assumptions.\n"
        "50,000 km/yr and clutch parc share from IML/ITUK convention — not Israel-verified.\n"
        "ASK: can they help calibrate intervals? (Links to R&M section in speaker guide.)\n"
        "Capture % is directional until they confirm service practice."
    ),
    13: (
        "PMS REVENUE (3 min)\n"
        "€426K FY25 peak, €365K FY26 — pullback in oil filter + clutch, not whole basket.\n"
        "Cover 31% → 41% → 38% on 8 active categories.\n"
        "Fuel + air still growing — good news to balance the oil/clutch story."
    ),
    14: (
        "FILTERS (3 min)\n"
        "Air filter star performer: 36→48→58% cover.\n"
        "Oil filter reversed FY26 — ASK why (fleet mix? UTI Parts? interval change?).\n"
        "Do not accuse — genuine curiosity. Bridge to filter-mix slide later."
    ),
    15: (
        "BRAKE & CLUTCH (3 min)\n"
        "Wear whitespace vs filters.\n"
        "Clutch family 39%→20% capture; revenue €110K→€55K — discuss together.\n"
        "Kit-only % >100% is artifact — always say family-level 20.3% FY26.\n"
        "ASK: fleet age shift? UTI Parts clutch? stocking?"
    ),
    16: (
        "CLUTCH REVIEW (2 min)\n"
        "Family blend 35.4% → 38.7% → 20.3% — FY25→FY26 drop is real in billing.\n"
        "Open question slide — let them talk."
    ),
    17: "REVENUE BY CATEGORY (2 min)\nAir filter now #1 line. Clutch family halved.\nUse to prioritise conversation topics with them.",
    18: (
        "OPPORTUNITY GAPS (2 min)\n"
        "CEILING figures — not sales targets.\n"
        "Clutch family gap ~€88–90K/yr stable while revenue fell — model still sees demand.\n"
        "Air filter gap shrinking = real progress."
    ),
    19: "PMS CHART (2 min)\nFY2025 snapshot chart. Clutch as one family.\nOffer detailed appendix after meeting if wanted.",
}

RM_QUESTIONS_HTML = """
<h2 id="rm">Fleet &amp; R&amp;M discovery — questions for UTI</h2>
<p class="lead">Exploratory block (~10 min). Position as <strong>mutual learning</strong> — ISZE wants more distributors on structured R&amp;M; their answers calibrate our models and programmes.</p>

<h3>A. Fleet parc &amp; R&amp;M scope</h3>
<ul>
<li>Do you operate a <strong>UTI-owned fleet</strong> or R&amp;M contract pool separate from dealer-retail parc? How many units?</li>
<li>What share of the Israeli Isuzu CV parc is under <strong>your R&amp;M programme</strong> vs customer-maintained vs dealer-only?</li>
<li>Active vs registered parc — which do you use for planning? How often is parc data refreshed?</li>
<li>Are any major customers on <strong>full-service R&amp;M contracts</strong> (parts + labour bundled)? Who holds the contract — UTI, the fleet customer, or a third party?</li>
<li>Typical <strong>fleet age profile</strong> — concentration in 3–5 yr or 5–8 yr bands? Any wave of replacements coming?</li>
</ul>

<h3>B. Service planning &amp; intervals</h3>
<ul>
<li>Maintenance planning: <strong>km-based, calendar-based, or mixed</strong>? Typical km/year by segment (distribution, construction, municipal)?</li>
<li>Do workshop schedules follow <strong>Isuzu/IML intervals</strong> or local overrides?</li>
<li>How far ahead are service events planned — does that match the <strong>~3-week parts lead time</strong> from IE?</li>
<li>Any <strong>telematics / predictive maintenance</strong> influencing parts demand?</li>
<li>Clutch and brake jobs — triggered at fixed km, inspection, or failure?</li>
</ul>

<h3>C. Parts sourcing &amp; workshop behaviour</h3>
<ul>
<li>For fleet workshops: split of <strong>genuine Isuzu / BVP / UTI Parts / other</strong> by category (filters, brakes, clutch)?</li>
<li>What triggers <strong>non-Isuzu</strong> on wear items — price, lead time, contract policy, stock availability?</li>
<li>Scope of <strong>UTI Parts</strong> — which categories, dealer network only or fleet workshops too?</li>
<li>On oil filters specifically — why did FY26 volume drop while fuel/air grew? Fleet sourcing change?</li>
<li>Are R&amp;M contracts priced with <strong>fixed parts allowances</strong> (absorbing ISZE price moves) or pass-through?</li>
</ul>

<h3>D. R&amp;M programme &amp; ISZE collaboration</h3>
<ul>
<li>Interest in <strong>expanding R&amp;M coverage</strong> with Isuzu — more models, more customers, longer contract windows?</li>
<li>Would they share <strong>anonymised service volumes or intervals</strong> to calibrate PMS/GPS models for Israel?</li>
<li>Can fleet/R&amp;M volumes explain <strong>FY26 clutch and oil-filter movement</strong>?</li>
<li>Appetite for <strong>SPA/programme pricing</strong> tied to fleet commitment on wear lines?</li>
<li>Who is the right counterpart for a <strong>follow-up fleet ops session</strong> (name/role)?</li>
</ul>

<h3>E. What we can offer back</h3>
<ul>
<li>Benchmark intervals from other CV markets (once calibrated — not ITUK assumptions verbatim).</li>
<li>Joint view of capture at workshop level if they share volumes.</li>
<li>Programme pricing on filters where genuine mix is the goal; BVP where price-sensitive.</li>
</ul>
"""

UTI_PARTS_PRICING_HTML = """
<h2 id="uti-parts">UTI Parts — pricing discovery (we do not have their price list)</h2>
<p class="lead">Use on <strong>slide 22</strong>. ISZE only sees Genuine and BVP on invoices — UTI Parts landed cost is unknown until UTI shares it.</p>

<h3>Questions to ask in the room</h3>
<ul>
<li><strong>Scope</strong> — Which categories does UTI Parts cover today? Filters only, or brakes/clutch/fluids too? Dealer network, fleet workshops, or both?</li>
<li><strong>Volume</strong> — Rough share of maintenance spend on UTI Parts vs ISZE genuine/BVP by category?</li>
<li><strong>Price list</strong> — Can you share the UTI Parts catalogue or list price for top 10 PNs (oil/fuel/air filter, brake pad, clutch kit)?</li>
<li><strong>Delivered cost</strong> — Sample invoices showing what the <em>workshop</em> pays after markup — compare to ISZE SPA landed (incl. ~3-week lead time).</li>
<li><strong>Decision rule</strong> — What triggers UTI Parts vs ISZE order — price, MOQ, lead time, contract policy, stock on hand?</li>
<li><strong>Win-back test</strong> — If ISZE matches delivered cost on fuel + air genuine at programme price, would they pilot on fleet/dealer channel?</li>
<li><strong>Owner</strong> — Who sets UTI Parts pricing? Can we run a joint basket benchmark after the meeting?</li>
</ul>

<h3>How to frame win-back (honest)</h3>
<ul>
<li><strong>Yes, share is recoverable</strong> where ISZE is already in the mix (filters BVP-heavy) and delivered price + lead time are competitive.</li>
<li><strong>Conditional</strong> — not a promise; needs UTI Parts prices and fleet/workshop split.</li>
<li><strong>Oil filter</strong> — keep BVP; do not push genuine (list economics favour BVP element).</li>
<li><strong>Fuel + air</strong> — best pilot for genuine at SPA (~€65K/yr revenue ceiling if mix moves toward ITUK pattern).</li>
<li><strong>Clutch / brake leakage</strong> — may be UTI Parts or non-ISZE; PMS gaps need their workshop data.</li>
</ul>

<table class="bench">
<tr><th>Metric</th><th>UTI</th><th>ITUK (peer)</th></tr>
<tr><td>Dealer sell-out qty CY2025</td><td>92,660</td><td>223,897</td></tr>
<tr><td>ISZE→DB billing qty CY2025</td><td>124,728</td><td>204,852</td></tr>
<tr><td>BVP % of sell-out (proxy €)</td><td>13.5%</td><td>2.6%</td></tr>
<tr><td>Genuine-only % on billing</td><td>~88%</td><td>~87%</td></tr>
</table>
"""


def duplicate_slide(prs: Presentation, index: int):
    source = prs.slides[index]
    new_slide = prs.slides.add_slide(prs.slide_layouts[6])
    for sh in source.shapes:
        new_slide.shapes._spTree.insert_element_before(deepcopy(sh.element), "p:extLst")
    return new_slide


def insert_slides_before(prs: Presentation, before_idx: int, count: int) -> None:
    sld_id_lst = prs.slides._sldIdLst
    total = len(sld_id_lst)
    elems = [sld_id_lst[i] for i in range(total - count, total)]
    for el in elems:
        sld_id_lst.remove(el)
    for i, el in enumerate(elems):
        sld_id_lst.insert(before_idx + i, el)


def set_shape_text(shape, text: str) -> None:
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text


def find_takeaways_shape(slide):
    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip().startswith("—"):
            return shape
    return None


def find_page_num_shape(slide):
    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip().isdigit() and len(shape.text.strip()) <= 2:
            return shape
    return None


def scell(cell, text, size=11, bold=False, color=BLACK, fill=WHITE, align=PP_ALIGN.LEFT):
    cell.margin_top = Pt(3)
    cell.margin_bottom = Pt(3)
    cell.margin_left = Pt(6)
    cell.margin_right = Pt(6)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Calibri"


def add_table(slide, rows, left, top, width, col_widths, body_size=11, header_size=10):
    nr, nc = len(rows), len(rows[0])
    height = Inches(0.36 * nr)
    tbl = slide.shapes.add_table(nr, nc, left, top, width, height).table
    for j, cw in enumerate(col_widths):
        tbl.columns[j].width = cw
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            align = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            if i == 0:
                scell(c, val, size=header_size, bold=True, color=WHITE, fill=NAVY, align=align)
            else:
                scell(
                    c,
                    val,
                    size=body_size,
                    color=BLACK,
                    fill=LGRAY if i % 2 == 0 else WHITE,
                    align=align,
                )
    return tbl


def configure_content_slide(slide, section: str, title: str, num: int, takeaways: str, table_rows=None):
    shapes_by_text = {}
    for shape in slide.shapes:
        if not hasattr(shape, "text"):
            continue
        t = shape.text.strip()
        if t:
            shapes_by_text.setdefault(t[:40], shape)

    for shape in slide.shapes:
        if not hasattr(shape, "text"):
            continue
        t = shape.text.strip()
        if t in ("METHODOLOGY & ASSUMPTIONS", "FILL RATE & URGENCY", "FILTERS", "PMS REVENUE", "MARKET VISIBILITY", "GENUINE / BVP MIX", "UTI PARTS"):
            set_shape_text(shape, section)
        elif "PMS modeling" in t or "Forward planning" in t or "Filters are the strongest" in t or "Revenue grew" in t:
            set_shape_text(shape, title)
        elif t == "TAKEAWAYS":
            pass
        elif t.startswith("—"):
            set_shape_text(shape, takeaways)

    pg = find_page_num_shape(slide)
    if pg:
        set_shape_text(pg, str(num))

    if table_rows:
        nc = len(table_rows[0])
        if nc == 4:
            col_widths = [Inches(1.55), Inches(0.95), Inches(0.95), Inches(1.1)]
            width = Inches(4.55)
        else:
            col_widths = [Inches(1.65), Inches(2.0), Inches(2.9)]
            width = Inches(6.55)
        add_table(slide, table_rows, Inches(0.35), Inches(1.25), width, col_widths)


def renumber_all_slides(prs: Presentation) -> None:
    for i, slide in enumerate(prs.slides, 1):
        pg = find_page_num_shape(slide)
        if pg:
            set_shape_text(pg, str(i))


def patch_agenda(slide) -> None:
    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip().startswith("—  Sales FY2026"):
            if "UTI Parts" not in shape.text:
                set_shape_text(shape, shape.text.rstrip() + AGENDA_EXTRA)
            return


def build_speaker_notes() -> dict[int, str]:
    notes = dict(SPEAKER_NOTES_BASE)
    notes[20] = SLIDE20["note"]
    notes[21] = SLIDE21["note"]
    notes[22] = SLIDE22["note"]
    notes[23] = (
        "CLOSE (1 min)\n"
        "Thank you. Confirm next steps:\n"
        "• UIO active parc by agreed date\n"
        "• SPA basket + NOx warranty review\n"
        "• Filter pilot: genuine fuel + air at programme price; oil stays BVP\n"
        "• UTI Parts: share price list / sample invoices for benchmark\n"
        "• Fleet/R&M follow-up with fleet & parts leads if useful\n"
        "Offer deck + PMS appendix after meeting."
    )
    return notes


def patch_pptx() -> Path:
    prs = Presentation(str(PPTX_IN))
    template_idx = 7  # slide 8 — text + takeaways layout

    for _ in range(3):
        duplicate_slide(prs, template_idx)

    insert_slides_before(prs, before_idx=19, count=3)

    slides = list(prs.slides)
    configure_content_slide(slides[19], **{k: SLIDE20[k] for k in ("section", "title", "takeaways")}, num=20)
    configure_content_slide(
        slides[20],
        **{k: SLIDE21[k] for k in ("section", "title", "takeaways")},
        num=21,
        table_rows=SLIDE21["table"],
    )
    configure_content_slide(
        slides[21],
        **{k: SLIDE22[k] for k in ("section", "title", "takeaways")},
        num=22,
        table_rows=SLIDE22["table"],
    )

    patch_agenda(slides[1])
    renumber_all_slides(prs)

    speaker_notes = build_speaker_notes()
    for i, slide in enumerate(prs.slides, 1):
        note = speaker_notes.get(i, "")
        if note:
            slide.notes_slide.notes_text_frame.text = note

    try:
        prs.save(str(PPTX))
        print("Saved pptx:", PPTX)
        return PPTX
    except PermissionError:
        alt = BASE / "UTI_presentation_V3.2.pptx"
        prs.save(str(alt))
        print("Locked — saved:", alt)
        return alt


def build_guide_html() -> None:
    titles = [
        "Cover", "Agenda", "Sales & BP Q1", "Q1 sales bridge", "GPS evolution",
        "Fill rate", "Order type (SaTy)", "Fill rate & urgency", "PMS section cover",
        "GPS vs PMS explainer", "How we measure", "PMS assumptions", "PMS revenue",
        "Filters", "Brake & clutch", "Clutch review", "Revenue by category",
        "EUR opportunity", "PMS chart",
        "Market visibility", "Filter mix vs ITUK", "UTI Parts & win-back", "Closing",
    ]
    speaker_notes = build_speaker_notes()
    slide_sections = []
    for i in range(1, 24):
        slide_sections.append(
            f'<section class="slide-block"><h2>Slide {i} — {titles[i - 1]}</h2>'
            f'<pre class="notes">{speaker_notes.get(i, "(visual / transition — see deck)")}</pre></section>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>UTI Meeting — Speaker Guide</title>
<style>
@page {{ size: A4; margin: 14mm; }}
body {{ font-family: 'Segoe UI', Calibri, sans-serif; color: #1a1a1a; line-height: 1.45; max-width: 210mm; margin: 0 auto; padding: 12mm; }}
header {{ border-bottom: 4px solid #CC0E1E; padding-bottom: 10px; margin-bottom: 18px; }}
h1 {{ color: #1a2b4a; margin: 0 0 4px; font-size: 22px; }}
.sub {{ color: #5a5a5a; font-size: 13px; }}
h2 {{ color: #CC0E1E; font-size: 15px; margin-top: 18px; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px; }}
h3 {{ color: #1a2b4a; font-size: 13px; margin: 14px 0 6px; }}
.slide-block {{ page-break-inside: avoid; margin-bottom: 12px; }}
.notes {{ white-space: pre-wrap; font-family: Calibri, sans-serif; font-size: 11px; background: #f8f8f8; border-left: 3px solid #1a2b4a; padding: 8px 10px; margin: 0; }}
.lead {{ font-size: 12px; }}
ul {{ margin: 6px 0 10px 18px; font-size: 11px; }}
li {{ margin-bottom: 4px; }}
table.bench {{ border-collapse: collapse; font-size: 11px; margin: 10px 0; }}
table.bench th {{ background: #1a2b4a; color: #fff; padding: 6px 10px; }}
table.bench td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: center; }}
.foot {{ font-size: 9px; color: #888; margin-top: 24px; border-top: 1px solid #ddd; padding-top: 8px; }}
</style></head><body>
<header>
<h1>ISZE – UTI Meeting | Speaker Guide</h1>
<p class="sub">FY2026–2027 review · July 2026 · Internal use — not for distribution to UTI</p>
</header>

<p class="lead">Use alongside <strong>UTI_presentation_V3.1.pptx</strong> (or V3.2 if locked). Speaker notes embedded in PowerPoint (View → Notes). Tone: partnership, facts first, assumptions flagged.</p>

<h2>SaTy benchmark — quick reference (slide 7)</h2>
<table class="bench"><tr><th></th><th>SOR (routine)</th><th>Urgent (RUSH+VOR)</th></tr>
<tr><td><strong>UTI</strong></td><td>88%</td><td>12%</td></tr>
<tr><td><strong>CV peers (avg)</strong></td><td>80%</td><td>17%</td></tr>
<tr><td><strong>ISZE network (avg)</strong></td><td>78%</td><td>20%</td></tr></table>
<p class="lead">CV peers = ITUK, Imotors (PT), Norway RSA, Ireland. Network = 8 large distributors with SaTy match ≥60%. ~3 weeks inbound lead time to Israel — high SOR = forward planning (voorraadbeheer).</p>

{UTI_PARTS_PRICING_HTML}

<h2>Slide-by-slide talking points</h2>
{''.join(slide_sections)}

{RM_QUESTIONS_HTML}

<div class="foot">Generated 2026-07-07 · Source: sellout_aim_by_pms_2025.csv, Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html, UTI_PMS_Score_by_PN.xlsx</div>
</body></html>"""
    GUIDE_HTML.write_text(html, encoding="utf-8")
    print("Wrote", GUIDE_HTML)


def build_guide_pdf() -> None:
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    browser = next((p for p in chrome_paths if Path(p).is_file()), None)
    if not browser:
        print("No Chrome/Edge — skip PDF")
        return
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        f"--print-to-pdf={GUIDE_PDF}",
        GUIDE_HTML.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print("Wrote", GUIDE_PDF)


if __name__ == "__main__":
    saved = patch_pptx()
    build_guide_html()
    build_guide_pdf()
    print("Done:", saved)
