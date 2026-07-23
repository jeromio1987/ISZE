# -*- coding: utf-8 -*-
"""Patch V3.1: SaTy benchmarks, Kosha fix, speaker notes. Build speaker guide HTML."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\UTI_Presentation")
PPTX = BASE / "UTI_presentation_V3.1.pptx"
GUIDE_HTML = BASE / "UTI_Meeting_Speaker_Guide.html"

RED = RGBColor(0xCC, 0x0E, 0x1E)
NAVY = RGBColor(0x1A, 0x2B, 0x4A)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE7_BULLETS = (
    "—  With ~3 weeks inbound lead time, a high routine (SOR) share reflects forward stock planning — strong voorraadbeheer.\n"
    "—  UTI: 88% SOR / 12% urgent vs CV peers 80% / 17% and network 78% / 20% (Q1 matched billing).\n"
    "—  Lower urgent share supports fill-rate performance — fewer panic lines through a long supply chain."
)

SLIDE8_TITLE = "Forward planning supports service performance"
SLIDE8_BULLETS = (
    "—  RUSH lines fulfil faster (median ~1 day order-to-invoice) vs SOR ~11 days — but SOR dominates UTI value.\n"
    "—  UTI fill rate 76–86% (Jul'25–May'26 BI trend) — consistent with planning ahead given ~3-week inbound lead time.\n"
    "—  VOR concentrates in filters & chassis — the small urgent slice; worth reviewing stock on those families.\n"
    "—  Message: UTI runs a more routine-heavy order profile than most CV peers — that is a strength, not under-service."
)

SPEAKER_NOTES: dict[int, str] = {
    1: (
        "OPENING (1 min)\n"
        "Thank them for the time. Frame as joint review: Q1 performance, GPS path, service mix, PMS trends — and learning how their fleet/R&M works.\n"
        "Tone: partnership, not audit."
    ),
    2: (
        "AGENDA (1 min)\n"
        "Walk top to bottom; offer to reorder if they have burning topics.\n"
        "Commercial block: sales/BP, GPS, order mix, fill rate.\n"
        "Analytics: PMS capture (directional — assumptions flagged).\n"
        "Close: fleet/R&M learning + next steps.\n"
        "PMS = Periodic Maintenance Service (filters, brakes, clutch on interval)."
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
    9: (
        "PMS SECTION BREAK (30 sec)\n"
        "Transition: shift from billing performance to maintenance-parts capture.\n"
        "PMS = interval-driven competitive parts only — not full GPS basket."
    ),
    10: (
        "GPS vs PMS EXPLAINER (2 min)\n"
        "GPS = whole genuine basket health. PMS = diagnostic on filters/brakes/clutch.\n"
        "Use only if they look lost — otherwise skip quickly."
    ),
    11: (
        "METHODOLOGY VISUAL (1 min)\n"
        "Parc → interval → potential → capture %. Same logic GPS vs PMS, different scope.\n"
        "Optional — skip if time short."
    ),
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
        "Oil filter reversed FY26 — ASK why (fleet mix? sourcing? interval change?).\n"
        "Do not accuse — genuine curiosity."
    ),
    15: (
        "BRAKE & CLUTCH (3 min)\n"
        "Wear whitespace vs filters.\n"
        "Clutch family 39%→20% capture; revenue €110K→€55K — discuss together.\n"
        "Kit-only % >100% is artifact — always say family-level 20.3% FY26.\n"
        "ASK: fleet age shift? competitor clutch? stocking?"
    ),
    16: (
        "CLUTCH REVIEW (2 min)\n"
        "Family blend 35.4% → 38.7% → 20.3% — FY25→FY26 drop is real in billing.\n"
        "Open question slide — let them talk."
    ),
    17: (
        "REVENUE BY CATEGORY (2 min)\n"
        "Air filter now #1 line. Clutch family halved.\n"
        "Use to prioritise conversation topics with them."
    ),
    18: (
        "OPPORTUNITY GAPS (2 min)\n"
        "CEILING figures — not sales targets.\n"
        "Clutch family gap ~€88–90K/yr stable while revenue fell — model still sees demand.\n"
        "Air filter gap shrinking = real progress."
    ),
    19: (
        "PMS CHART (2 min)\n"
        "FY2025 snapshot chart. Clutch as one family.\n"
        "Offer detailed appendix after meeting if wanted."
    ),
    20: (
        "CLOSE (1 min)\n"
        "Thank you. Confirm next steps owners/dates.\n"
        "Offer speaker guide + data appendix.\n"
        "Schedule fleet/R&M follow-up if appetite."
    ),
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


def add_textbox(slide, left, top, width, height, text, font_size=11, bold=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = BLACK
    p.font.name = "Calibri"
    return tb


def add_benchmark_table(slide):
    rows, cols = 4, 3
    tbl = slide.shapes.add_table(rows, cols, Inches(0.35), Inches(1.28), Inches(2.35), Inches(1.35)).table
    data = [
        ["", "SOR", "Urgent"],
        ["UTI", "88%", "12%"],
        ["CV peers (avg)", "80%", "17%"],
        ["ISZE network (avg)", "78%", "20%"],
    ]
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            cell.text = data[r][c]
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for par in cell.text_frame.paragraphs:
                par.alignment = PP_ALIGN.CENTER if r == 0 or c > 0 else PP_ALIGN.LEFT
                par.font.size = Pt(10 if r else 10)
                par.font.bold = r == 0 or c == 0
                par.font.name = "Calibri"
                par.font.color.rgb = WHITE if r == 0 else BLACK
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
    add_textbox(slide, Inches(0.35), Inches(2.75), Inches(2.45), Inches(3.6), SLIDE7_BULLETS, font_size=10)
    foot = add_textbox(slide, Inches(0.35), Inches(6.35), Inches(2.45), Inches(0.55),
                       "Q1 FY27 matched billing · CV peers = ITUK, Imotors, Norway, Ireland", font_size=8)
    foot.text_frame.paragraphs[0].font.color.rgb = GRAY


def patch_pptx() -> None:
    prs = Presentation(str(PPTX))
    slides = list(prs.slides)

    # Slide 5 — remove Kosha from visible takeaway
    for shape in slides[4].shapes:
        if hasattr(shape, "text") and "Kosha" in shape.text:
            set_shape_text(shape, shape.text.replace("FY27 Kosha base 35.1%", "FY27 plan base 35.1%"))

    # Slide 7 — benchmark table + bullets
    add_benchmark_table(slides[6])

    # Slide 8 — title + takeaways
    for shape in slides[7].shapes:
        if hasattr(shape, "text") and "urgent orders remain" in shape.text:
            set_shape_text(shape, SLIDE8_TITLE)
    tk = find_takeaways_shape(slides[7])
    if tk:
        set_shape_text(tk, SLIDE8_BULLETS)

    # Speaker notes all slides
    for i, slide in enumerate(slides, 1):
        note = SPEAKER_NOTES.get(i, "")
        if note:
            slide.notes_slide.notes_text_frame.text = note

    try:
        prs.save(str(PPTX))
        print("Saved pptx:", PPTX)
    except PermissionError:
        alt = BASE / "UTI_presentation_V3.2.pptx"
        prs.save(str(alt))
        print("Locked — saved:", alt)


def build_guide_html() -> None:
    slide_sections = []
    titles = [
        "Cover", "Agenda", "Sales & BP Q1", "Q1 sales bridge", "GPS evolution",
        "Fill rate", "Order type (SaTy)", "Fill rate & urgency", "PMS section cover",
        "GPS vs PMS explainer", "How we measure", "PMS assumptions", "PMS revenue",
        "Filters", "Brake & clutch", "Clutch review", "Revenue by category",
        "EUR opportunity", "PMS chart", "Closing",
    ]
    for i in range(1, 21):
        slide_sections.append(
            f"<section class=\"slide-block\"><h2>Slide {i} — {titles[i-1]}</h2>"
            f"<pre class=\"notes\">{SPEAKER_NOTES.get(i, '(visual / transition — see deck)')}</pre></section>"
        )

    html = f"""<!DOCTYPE html>
<html lang=\"en\"><head><meta charset=\"utf-8\"/>
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
<p class=\"sub\">FY2026–2027 review · July 2026 · Internal use — not for distribution to UTI</p>
</header>

<p class=\"lead\">Use this alongside <strong>UTI_presentation_V3.1.pptx</strong>. Speaker notes are also embedded in the PowerPoint (View → Notes). Tone: partnership, facts first, assumptions flagged.</p>

<h2>SaTy benchmark — quick reference (slide 7)</h2>
<table class=\"bench\"><tr><th></th><th>SOR (routine)</th><th>Urgent (RUSH+VOR)</th></tr>
<tr><td><strong>UTI</strong></td><td>88%</td><td>12%</td></tr>
<tr><td><strong>CV peers (avg)</strong></td><td>80%</td><td>17%</td></tr>
<tr><td><strong>ISZE network (avg)</strong></td><td>78%</td><td>20%</td></tr></table>
<p class=\"lead\">CV peers = ITUK, Imotors (PT), Norway RSA, Ireland. Network = 8 large distributors with SaTy match ≥60%. ~3 weeks inbound lead time to Israel — high SOR = forward planning (voorraadbeheer).</p>

<h2>Slide-by-slide talking points</h2>
{''.join(slide_sections)}

{RM_QUESTIONS_HTML}

<div class=\"foot\">Generated 2026-07-07 · Source: q1fy2027_export_with_saty.csv, UTI_PMS_Score_by_PN.xlsx, VP Monthly Report Jun-2026</div>
</body></html>"""
    GUIDE_HTML.write_text(html, encoding="utf-8")
    print("Wrote", GUIDE_HTML)


if __name__ == "__main__":
    patch_pptx()
    build_guide_html()
