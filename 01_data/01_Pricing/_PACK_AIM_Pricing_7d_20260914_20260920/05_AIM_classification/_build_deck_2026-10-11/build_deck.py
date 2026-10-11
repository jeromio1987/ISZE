"""Build the AIM management presentation (11 Oct 2026) from deck_numbers.json.

Output: ../ISZE_AIM_Parts_Classification_Management_2026-10-11.pptx
Every figure on a slide comes from deck_numbers.json (see deck_numbers.py for the sources).
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from PIL import ImageFont

HERE = Path(__file__).resolve().parent
N = json.loads((HERE / "deck_numbers.json").read_text(encoding="utf-8"))
OUT = HERE.parent / "ISZE_AIM_Parts_Classification_Management_2026-10-11.pptx"
A = HERE / "assets"

INK = RGBColor(0x24, 0x28, 0x2C)
GREY = RGBColor(0x62, 0x6A, 0x71)
MID = RGBColor(0x9A, 0xA1, 0xA6)
LIGHT = RGBColor(0xCC, 0xD1, 0xD2)
RULE = RGBColor(0xD9, 0xDC, 0xDA)
PAPER = RGBColor(0xF5, 0xF4, 0xF1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xD7, 0x19, 0x20)
PALE = RGBColor(0xFA, 0xEA, 0xE8)
CHAR2 = RGBColor(0x35, 0x3B, 0x3E)
FONT = "Arial"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
_TF = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 270)


def title_lines(t, width_in=12.1):
    """Lines a 27pt bold Arial title needs in a box this wide (greedy wrap, 3% safety)."""
    lines, cur = 1, ""
    for w in t.split():
        trial = (cur + " " + w).strip()
        if _TF.getlength(trial) > width_in * 720 * 0.99 and cur:
            lines, cur = lines + 1, w
        else:
            cur = trial
    return lines


def eur_m(v, d=1):
    return f"€{v / 1e6:.{d}f}M"


def eur_k(v):
    return f"€{v / 1e3:,.0f}k"


# ---------- primitives ----------
def text(slide, x, y, w, h, paras, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, name=None, spacing=None, margin=0.0, line=None):
    """paras: str | list of paragraphs; a paragraph is str or list of (text, opts) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(margin))
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        sp = spacing[i] if isinstance(spacing, (list, tuple)) else spacing
        if sp is not None and i > 0:
            p.space_before = Pt(sp)
        if line:
            p.line_spacing = line
        runs = [(para, {})] if isinstance(para, str) else para
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = o.get("color", color)
            if o.get("strike"):
                r.font._rPr.set("strike", "sngStrike")
    return tb


def box(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, name=None, line=None, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def picture(slide, path, x, y, w, h, name=None):
    p = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        p.name = name
    return p


def background(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def header(slide, kicker, title, subtitle=None):
    """Title is bottom-aligned on a fixed line, so subtitle and content sit at the same height on every slide."""
    n = title_lines(title)
    ty = 0.72 + (2 - n) * 0.43
    text(slide, 0.6, ty - 0.32, 12.1, 0.28, kicker, size=11, color=RED, bold=True, name="kicker")
    text(slide, 0.6, ty, 12.1, n * 0.43 + 0.12, title, size=27, bold=True, name="title", anchor=MSO_ANCHOR.TOP,
         line=0.95)
    if subtitle:
        text(slide, 0.6, 1.76, 12.1, 0.4, subtitle, size=15, color=GREY, name="subtitle")


def footer(slide, section, page, dark=False):
    text(slide, 0.6, 7.02, 0.9, 0.25, "ISUZU", size=10, bold=True, color=RED, name="ft_brand")
    text(slide, 1.45, 7.03, 8.0, 0.25, f"EUROPE  /  AIM  /  {section}", size=9,
         color=LIGHT if dark else GREY, name="ft_section")
    text(slide, 11.93, 7.02, 0.8, 0.25, f"{page:02d}", size=10, bold=True, color=WHITE if dark else INK,
         align=PP_ALIGN.RIGHT, name="ft_page")


def source(slide, s):
    text(slide, 0.6, 6.66, 12.1, 0.3, s, size=9, color=GREY, name="source")


def band(slide, y, h, paras, size=15, name="band"):
    box(slide, 0.6, y, 12.13, h, PALE, name=name + "_bg")
    text(slide, 0.85, y, 11.65, h, paras, size=size, anchor=MSO_ANCHOR.MIDDLE, name=name)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def bar_chart(slide, x, y, w, h, cats, vals, colors, fmt, name, size=11, vmax=None, vmin=None,
              gap=55, low_labels=False):
    """fmt is a python callable turning a value into its label text (keeps '.' decimals on any locale)."""
    cd = CategoryChartData()
    cd.categories = list(reversed(cats))
    cd.add_series("v", list(reversed(vals)))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = name
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    ch.font.name = FONT
    ch.font.size = Pt(size)
    ch.font.color.rgb = INK
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.vary_by_categories = False
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(size)
    dl.font.name = FONT
    dl.font.bold = True
    dl.font.color.rgb = INK
    va = ch.value_axis
    va.has_major_gridlines = False
    va.has_minor_gridlines = False
    va.visible = False
    if vmax is not None:
        va.maximum_scale = vmax
    if vmin is not None:
        va.minimum_scale = vmin
    ca = ch.category_axis
    ca.has_major_gridlines = False
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.format.line.color.rgb = RULE
    ca.tick_labels.font.size = Pt(size)
    ca.tick_labels.font.name = FONT
    ca.tick_labels.font.color.rgb = INK
    if low_labels:
        ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    ser = plot.series[0]
    ser.invert_if_negative = False
    for i, (c, v) in enumerate(zip(reversed(colors), reversed(vals))):
        pt = ser.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c
        pt.format.line.fill.background()
        # each data point needs its own invertIfNegative=0, or PowerPoint paints negative bars white
        dpt = ser._element.xpath(f"./c:dPt[c:idx/@val='{i}']")[0]
        if not dpt.xpath("./c:invertIfNegative"):
            inv = dpt.makeelement(qn("c:invertIfNegative"), {"val": "0"})
            dpt.find(qn("c:idx")).addnext(inv)
        lab = pt.data_label
        lab.position = XL_LABEL_POSITION.OUTSIDE_END
        tf = lab.text_frame
        tf.text = fmt(v)
        for r in tf.paragraphs[0].runs:
            r.font.size = Pt(size)
            r.font.bold = True
            r.font.name = FONT
            r.font.color.rgb = INK
    return gf


# ---------- numbers used on several slides ----------
BOOK = N["base"]["billed_eur"]
old = {d["label"]: d for d in N["old_l1"]}
comp = old["Competitive parts"]
nv = N["nordic"]
pv_no, pv_se = nv["per_vehicle"]["Norway"], nv["per_vehicle"]["Sverige"]
gap_total = pv_no - pv_se
det = {(d["l3"], d["db"]): d for d in nv["detail"]}
inc = {d["l2"]: d for d in N["increase_l2"]}
fr = N["filter_roles"]
el, asm = fr["element"], fr["assembly"]
z = N["zkk"]
mis = N["misfiled"]
NICE = {"Intake Exhaust Emission": "Intake, exhaust & emission", "Accident & Body": "Accident & body",
        "Maintenance Service": "Maintenance service", "Wheels Hub": "Wheels & hubs", "Fuel System": "Fuel system",
        "Cabin Interior": "Cabin interior", "Driveline Axle": "Driveline & axle", "Chassis Frame": "Chassis frame"}
nice = lambda s: NICE.get(s, s)  # noqa: E731

# =====================================================================================
# 1  Cover
s = prs.slides.add_slide(BLANK)
background(s, INK)
picture(s, A / "cover_shelf.jpg", 7.55, 0, 5.783, 7.5, name="cover_photo")
text(s, 0.7, 0.62, 6.4, 0.3, "ISUZU EUROPE  ·  AFTERSALES  ·  MANAGEMENT PRESENTATION", size=11, bold=True,
     color=LIGHT, name="cover_kicker")
text(s, 0.7, 1.35, 6.5, 2.75, [
    [("We bill ", {}), (f"€{BOOK / 1e6:.0f} million", {"color": RGBColor(0xF2, 0x96, 0x9B)}),
     (" of parts a year.", {})],
    "Now we can see what they are."], size=38, bold=True, color=WHITE, name="cover_title", line=0.95,
     spacing=10)
text(s, 0.7, 4.35, 6.3, 1.0,
     "AIM, our new parts classification, shows what is selling, where it is selling, and how each "
     "product range should be priced.", size=17, color=LIGHT, name="cover_sub")
text(s, 0.7, 5.85, 6.3, 0.3, "October 2026", size=13, bold=True, color=WHITE, name="cover_date")
text(s, 0.7, 6.55, 6.4, 0.5,
     f"€{BOOK / 1e6:.1f}M = parts billed to our distributors, July 2025 – June 2026. "
     "Photo: Isuzu Genuine Parts, Isuzu Truck (UK) Ltd.", size=9, color=MID, name="cover_note")
text(s, 0.7, 7.02, 0.9, 0.25, "ISUZU", size=10, bold=True, color=RED, name="ft_brand")
notes(s, "Open with the money, not the method. We bill about €35 million of parts a year to our distributors "
         "(the price revision basis, July 2025 – June 2026, 15,872 part numbers). The question this presentation "
         "answers: what are those parts, and what can we do once we know?\n"
         "Photo credit: Isuzu Genuine Parts shelf, Isuzu Truck (UK) Ltd website; internal use.")

# =====================================================================================
# 2  The old top level
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
header(s, "THE PROBLEM", f"Our old classification sorted €{BOOK / 1e6:.0f} million of parts by how we thought "
                         "they compete, not by what they are",
       "Five of its seven top-level labels were commercial opinions. None of them named a product.")
order_old = ["Competitive parts", "Repair parts", "Accident parts", "High value repair", "Other / review",
             "Comfort parts", "Hardware & consumables"]
text(s, 0.6, 2.4, 5.9, 0.3, "Old top level: share of what we billed", size=13, bold=True, name="c1_title")
bar_chart(s, 0.6, 2.75, 5.9, 3.05, order_old, [old[k]["pct"] for k in order_old],
          [RED] + [MID] * 6, lambda v: f"{v:.1f}%", "chart_old", vmax=52)
top10 = N["aim_l1"][:10]
text(s, 6.85, 2.4, 5.9, 0.3, f"AIM top level: the ten largest of {N['levels']['aim'][0]} families", size=13,
     bold=True, name="c2_title")
bar_chart(s, 6.85, 2.75, 5.9, 3.05, [nice(d["label"]) for d in top10], [d["pct"] for d in top10],
          [INK] * 10, lambda v: f"{v:.1f}%", "chart_aim", vmax=21, size=10, gap=45)
band(s, 5.95, 0.62, [[(f"{eur_m(comp['eur'])}, {comp["pct"]:.0f}% of what we billed, sat under one label. ",
                       {"bold": True}),
                      ("Steering units, brake discs, brake pads, air filters and EGR valves all read "
                       "“Competitive parts”.", {})]], size=14)
source(s, f"Base: parts billed to distributors used for the 2026 price revision, July 2025 – June 2026 "
          f"(€{BOOK / 1e6:.1f}M, {N['base']['part_numbers']:,} part numbers). Old top level: price-list "
          "classification. AIM: approved release of 7 October 2026.")
footer(s, "THE PROBLEM", 2)
notes(s, "The old tree had 7 top-level labels. Five of them describe a commercial opinion (competitive, "
         "repair, accident, high value repair, comfort), not a product. "
         f"{comp['pct']:.1f}% of what we billed ({eur_m(comp['eur'], 2)}) sat in 'Competitive parts'. Inside it, by AIM "
         "part type: " + ", ".join(f"{d['l3']} {eur_m(d['eur'], 2)}" for d in N['old_competitive_top_l3'][:5]) +
      f". AIM has {N['levels']['aim'][0]} families, {N['levels']['aim'][1]} product groups and "
      f"{N['levels']['aim'][2]} part types on this basis; the old tree had {N['levels']['old'][0]} / "
      f"{N['levels']['old'][1]} / {N['levels']['old'][2]}.")

# =====================================================================================
# 3  Parts in the wrong family
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
mis_total = N["misfiled_total_eur"]
acl = mis[0]
header(s, "THE PROBLEM", f"{eur_m(mis_total)} a year sat in families the parts have nothing to do with",
       "The old rule read only the price-list text. It could not know that “ACL” means air cleaner.")
box(s, 0.6, 2.4, 3.3, 3.3, WHITE, name="photo_frame")
picture(s, A / "filter_acl.jpg", 0.75, 2.55, 3.0, 3.0, name="photo_acl")
text(s, 0.6, 5.8, 3.3, 0.85, [[("Price list: FILTER; ACL. ", {"bold": True}),
                                ("An engine air cleaner element, filed under air conditioning.", {})]],
     size=11, color=INK, name="photo_caption")
cols = [(4.3, 2.35, "PART"), (6.75, 1.75, "WHAT WE BILLED"), (8.6, 2.0, "OLD RULE FILED IT AS"),
        (10.7, 2.03, "AIM PLACES IT")]
for cx, cw, lab in cols:
    text(s, cx, 2.42, cw, 0.25, lab, size=9, bold=True, color=GREY, name=f"th_{lab[:6]}")
aim_short = {
    "Engine air cleaner elements": "Maintenance service › Air filter",
    "King pin kits": "Steering › Knuckle & king pin",
    "Steering drag links": "Steering › Linkage",
    "Front and rear bumper bars": "Accident & body › Bumper",
    "Suspension ball joints": "Suspension › Suspension arm",
}
names = {"Front and rear bumper bars": "Bumper bars", "Suspension ball joints": "Ball joints"}
rmax = max(m["eur"] for m in mis)
for i, m in enumerate(mis):
    ry = 2.78 + i * 0.6
    box(s, 4.3, ry - 0.04, 8.43, 0.52, WHITE, name=f"row_bg{i}")
    text(s, 4.45, ry, 2.25, 0.44, names.get(m["name"], m["name"]), size=13, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         name=f"row_name{i}")
    bw = max(0.08, 1.0 * m["eur"] / rmax)
    box(s, 6.75, ry + 0.12, bw, 0.2, RED if i == 0 else MID, name=f"row_bar{i}")
    text(s, 6.75 + bw + 0.08, ry, 0.75, 0.44, eur_k(m["eur"]), size=12, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         name=f"row_eur{i}")
    text(s, 8.6, ry, 2.0, 0.44, [[(m["old"].replace(" > ", " › "), {"strike": True})]], size=11, color=GREY,
         anchor=MSO_ANCHOR.MIDDLE, name=f"row_old{i}")
    text(s, 10.7, ry, 1.98, 0.44, aim_short[m["name"]], size=11, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         name=f"row_aim{i}")
text(s, 4.45, 5.83, 4.0, 0.3, [[("Total ", {}), (f"{eur_m(mis_total, 2)} a year", {"bold": True})]], size=13,
     name="row_total")
box(s, 4.3, 6.17, 8.43, 0.45, PALE, name="acl_band_bg")
text(s, 4.45, 6.17, 8.2, 0.45,
     [[("Ask “how are our air filters selling?” and the old tree missed ", {}),
       (f"{eur_m(acl['eur'], 2)} of the {eur_m(N['air_cleaner_filter_total_eur'], 2)} answer.", {"bold": True})]],
     size=13, anchor=MSO_ANCHOR.MIDDLE, name="acl_band")
source(s, "Old placements: classification audit of 20 September 2026, each confirmed against Isuzu's parts "
          "catalogue figures. Euro: price revision basis, July 2025 – June 2026. Photo: Isuzu Truck UK dealer listing.")
footer(s, "THE PROBLEM", 3)
notes(s, "Five classes where the price-list text names the system beyond argument and the old rule still filed "
         "the part somewhere physically unrelated. Euro on this basis: " +
      "; ".join(f"{m['name']} {eur_k(m['eur'])} ({m['pn']} part numbers)" for m in mis) +
      ". The old placements and their check against Isuzu catalogue figures (1-30 Air Cleaner, 4-10 Front Axle) "
      "are in the classification audit of 20 September 2026. Air cleaner elements under AIM today: "
      f"{eur_m(N['air_cleaner_filter_total_eur'], 2)}, of which FILTER; ACL lines {eur_m(acl['eur'], 2)}.")

# =====================================================================================
# 4  The competitive label
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
header(s, "THE PROBLEM", "For pricing, the old “Competitive” label was wrong half the time",
       "We tested it against the independent-brand prices we collect ourselves.")
sq, gp = 0.22, 0.05
for i in range(100):
    r, c = divmod(i, 10)
    box(s, 0.6 + c * (sq + gp), 2.45 + r * (sq + gp), sq, sq, RED if i < 48 else LIGHT, name=f"w{i}")
ly = 2.45 + 10 * (sq + gp) + 0.08
box(s, 0.6, ly + 0.05, 0.16, 0.16, RED, name="lg1")
text(s, 0.84, ly, 3.4, 0.26, "labelled “Competitive”", size=11, name="lg1_t")
box(s, 0.6, ly + 0.33, 0.16, 0.16, LIGHT, name="lg2")
text(s, 0.84, ly + 0.28, 3.6, 0.26, "labelled repair, accident, comfort or hardware", size=11, name="lg2_t")
text(s, 4.0, 2.3, 3.9, 1.1, "48%", size=66, bold=True, color=RED, name="stat48")
text(s, 4.0, 3.45, 3.9, 1.85,
     "Of every 100 parts where we found an independent-brand alternative, only 48 carried the “Competitive” "
     "label. The other 52 were filed as something else.", size=15, name="stat48_t")
box(s, 8.4, 2.4, 4.33, 3.45, WHITE, name="impl_bg")
text(s, 8.65, 2.55, 3.9, 3.15, [
    [("What that does to a price revision", {"bold": True, "size": 16})],
    [("Raise a “repair part” ", {"bold": True}),
     ("and you may be raising it where the customer already has a cheaper choice.", {})],
    [("Hold a “competitive part” ", {"bold": True}),
     ("and you may be giving away margin where nobody competes.", {})]], size=15, spacing=16, name="impl",
     anchor=MSO_ANCHOR.MIDDLE)
band(s, 5.95, 0.62, [[("A label cannot tell us where we compete. Price evidence can, ", {}),
                      ("and it needs a real product to attach to. That is what AIM provides.", {"bold": True})]],
     size=14)
source(s, "Classification audit, 20 September 2026: share of part numbers with a confirmed independent-brand "
          "alternative in our own price checks that carried the old “Competitive parts” label (48.2%).")
footer(s, "THE PROBLEM", 4)
notes(s, "Measured in the classification audit of 20 September 2026 against our own independent-brand price "
         "scrapes: parts labelled Competitive were 1.43 times more likely to have an aftermarket rival, but of the "
         "parts where a rival was confirmed only 48.2% carried the Competitive label. Counted on part numbers. "
         "Competition depends on the market, not on the part's name; AIM fixes the product, and the competition "
         "check sits beside it per market.")

# =====================================================================================
# 5  What AIM is
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
L = N["levels"]["aim"]
header(s, "THE ANSWER", "AIM gives every part a family, a product group and a part type",
       "It reads five facts about each part together, not just its name.")
path = N["path"]
steps = [("FAMILY", "Brakes", path["l1"][1], INK, WHITE),
         ("PRODUCT GROUP", "Pads & shoes", path["l2"][1], CHAR2, WHITE),
         ("PART TYPE", "Brake pad kit", path["l3"][1], GREY, WHITE),
         ("PART NUMBER", f"{path['pn'][0]}  ·  front disc brake pad kit", path["pn"][2], WHITE, INK)]
for i, (lab, nm, v, fill, fc) in enumerate(steps):
    x0, y0 = 0.6 + i * 0.35, 2.4 + i * 0.86
    box(s, x0, y0, 5.6, 0.72, fill, name=f"lvl{i}", line=RULE if fill == WHITE else None)
    text(s, x0 + 0.2, y0 + 0.06, 3.8, 0.22, lab, size=9, bold=True, color=LIGHT if fc == WHITE else GREY,
         name=f"lvl{i}_k")
    text(s, x0 + 0.2, y0 + 0.28, 4.1, 0.38, nm, size=15, bold=True, color=fc, name=f"lvl{i}_n")
    text(s, x0 + 4.2, y0 + 0.06, 1.25, 0.6, eur_m(v, 2), size=15, bold=True, color=fc, align=PP_ALIGN.RIGHT,
         anchor=MSO_ANCHOR.MIDDLE, name=f"lvl{i}_v")
text(s, 0.6, 5.85, 6.6, 0.3, "Billed July 2025 – June 2026, price revision basis.", size=10, color=GREY,
     name="lvl_note")
facts = [("Part number", "links sales, prices and the catalogue"),
         ("Description", "what the price list calls the part"),
         ("Catalogue figure", "where Isuzu draws it on the vehicle"),
         ("Customs code", "an independent check on the product"),
         ("Price", f"separates a €{el['avg']:.0f} element from a €{asm['avg']:.0f} housing")]
text(s, 7.75, 2.4, 5.0, 0.3, "Five facts, read together", size=15, bold=True, name="facts_t")
for i, (a, b_) in enumerate(facts):
    fy = 2.85 + i * 0.56
    box(s, 7.75, fy + 0.04, 0.36, 0.36, RED, shape=MSO_SHAPE.OVAL, name=f"fact_dot{i}")
    text(s, 7.75, fy + 0.04, 0.36, 0.36, str(i + 1), size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, name=f"fact_n{i}")
    text(s, 8.25, fy, 4.48, 0.46, [[(a + "  ", {"bold": True}), (b_, {"color": GREY})]], size=13,
         anchor=MSO_ANCHOR.MIDDLE, name=f"fact{i}")
text(s, 8.25, 5.66, 4.48, 0.46, [[("+ Japan's code  ", {"bold": True}),
                                  ("kept on every part (next page)", {"color": GREY})]], size=13,
     anchor=MSO_ANCHOR.MIDDLE, name="fact_jp")
kp = [(f"{N['coverage']['pct_l1']:.0f}%", "of what we bill has a family, group and part type"),
      (f"{L[0]} · {L[1]} · {L[2]}", "families · product groups · part types"),
      ("7 Oct 2026", "latest approved release, maintained by Vehicle Parts Sales")]
for i, (big, small) in enumerate(kp):
    kx = 0.6 + i * 4.11
    box(s, kx, 6.17, 3.91, 0.45, WHITE, name=f"kpi_bg{i}")
    text(s, kx + 0.15, 6.17, 3.7, 0.45, [[(big + "  ", {"bold": True, "color": RED, "size": 14}),
                                          (small, {"size": 10.5})]], anchor=MSO_ANCHOR.MIDDLE, name=f"kpi{i}")
footer(s, "THE ANSWER", 5)
notes(s, "AIM (our parts classification) gives three levels: family, product group, part type. Example path with "
         f"billed euro: Brakes {eur_m(path['l1'][1], 2)} > Pads & shoes {eur_m(path['l2'][1], 2)} > Brake pad kit "
         f"{eur_m(path['l3'][1], 2)} > part {path['pn'][0]} ({path['pn'][1]}) {eur_m(path['pn'][2], 2)}. "
         "The five facts are read together; where they disagree the part goes to review instead of being guessed. "
         f"Coverage on this basis: {N['coverage']['pct_l1']:.2f}% of billed euro; {N['coverage']['pn_open']:,} part "
         f"numbers ({eur_k(N['coverage']['eur_open'])}) still open. Approved releases: 4 and 7 October 2026.")

# =====================================================================================
# 6  Element versus housing
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
ratio = asm["avg"] / el["avg"]
header(s, "PRECISION", "An element and a housing share a family, not a price",
       "AIM keeps them apart, so every price and sales comparison is like for like.")
cards = [(0.6, "element.jpg", "FILTER ELEMENTS", el, "Replaced at every service. A routine purchase, "
                                                     "bought again and again."),
         (7.18, "housing.jpg", "FILTER HOUSINGS AND ASSEMBLIES", asm, "Replaced after damage or failure. "
                                                                       "A repair purchase, not a service one.")]
for i, (cx, img, lab, d, desc) in enumerate(cards):
    box(s, cx, 2.4, 5.55, 3.45, WHITE, name=f"card{i}")
    picture(s, A / img, cx + 0.15, 2.55, 2.85, 2.85, name=f"card_img{i}")
    text(s, cx + 3.2, 2.6, 2.2, 0.5, lab, size=10, bold=True, color=RED, name=f"card_k{i}")
    text(s, cx + 3.2, 3.12, 2.2, 0.95, [[(f"€{d['avg']:.2f}", {"size": 30, "bold": True})],
                                        [("average per unit", {"size": 11, "color": GREY})]], name=f"card_v{i}")
    text(s, cx + 3.2, 4.15, 2.2, 0.55, [f"{eur_m(d['eur'], 2)} billed", f"{d['pn']} part numbers"], size=11,
         color=GREY, name=f"card_m{i}")
    text(s, cx + 3.2, 4.8, 2.2, 1.0, desc, size=12, name=f"card_d{i}")
    text(s, cx + 0.15, 5.47, 2.85, 0.3, "Product form only; not a specific part number.", size=8.5,
         color=MID, name=f"card_c{i}")
box(s, 6.24, 3.62, 0.86, 0.86, RED, shape=MSO_SHAPE.OVAL, name="ratio_dot")
text(s, 6.2, 3.62, 0.94, 0.86, f"{ratio:.0f}×", size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
     anchor=MSO_ANCHOR.MIDDLE, name="ratio")
band(s, 5.98, 0.62, [[("Averaged together, a “filter” costs ", {}),
                      (f"€{N['filter_roles_blended_avg']:.2f} per unit", {"bold": True}),
                      (", a price that describes neither product.", {})]], size=15)
source(s, "Billed July 2025 – June 2026, price revision basis, all filter part numbers marked element or housing / "
          "assembly in AIM. Photos: dealer and supplier listings, product form only.")
footer(s, "PRECISION", 6)
notes(s, f"Filter elements: {eur_m(el['eur'], 2)} billed, {el['qty']:,.0f} units, {el['pn']} part numbers, "
         f"€{el['avg']:.2f} per unit. Housings and assemblies: {eur_m(asm['eur'], 2)}, {asm['qty']:,.0f} units, "
         f"{asm['pn']} part numbers, €{asm['avg']:.2f} per unit, {ratio:.1f} times the element. Blended: "
         f"€{N['filter_roles_blended_avg']:.2f}. The element photo is an Isuzu Best Value element in its box; the "
         "housing photo is a supplier listing. Both show product form only.")

# =====================================================================================
# 7  Japan's catalogue code
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
header(s, "JAPAN'S CODE", "Japan's code stays on every part, but it cannot replace AIM",
       "The code says where Japan files a part. AIM says what the part is. We need both.")
text(s, 0.6, 2.4, 6.6, 0.62, [[("One Japan code, many products", {"bold": True, "size": 15})],
                              [(f"Code {z['top_code']} holds {z['top_code_pct']:.0f}% of what we bill, across "
                                f"{z['top_code_aim_l3_types']} different part types", {"color": GREY,
                                                                                         "size": 12})]],
     name="z_left_t")
tb = z["top_code_by_l1"][:7]
bar_chart(s, 0.6, 3.08, 6.6, 2.2, [nice(d["l1"]) for d in tb], [d["eur"] / 1e6 for d in tb], [INK] * len(tb),
          lambda v: f"€{v:.1f}M", "chart_zkk", size=10, vmax=3.9, gap=40)
text(s, 7.75, 2.4, 4.98, 0.62, [[("One product, many Japan codes", {"bold": True, "size": 15})],
                                [("Number of different Japan codes on the same part type", {"color": GREY,
                                                                                             "size": 12})]],
     name="z_right_t")
cp = z["codes_per_type"]
for i, (t, lab) in enumerate([("Brake Pad Kit", "brake pad kits"), ("Air Cleaner Filter", "air cleaner elements"),
                              ("Door", "doors")]):
    yy = 3.15 + i * 0.7
    box(s, 7.75, yy, 4.98, 0.6, WHITE, name=f"zc_bg{i}")
    text(s, 7.95, yy, 1.1, 0.6, str(cp[t]), size=26, bold=True, color=RED, anchor=MSO_ANCHOR.MIDDLE,
         name=f"zc_n{i}")
    text(s, 9.0, yy, 3.6, 0.6, f"Japan codes for {lab}", size=14, anchor=MSO_ANCHOR.MIDDLE, name=f"zc_t{i}")
box(s, 0.6, 5.45, 12.13, 1.05, WHITE, name="reinf_bg")
text(s, 0.85, 5.55, 2.4, 0.9, "How the code reinforces AIM", size=14, bold=True, color=RED, name="reinf_t")
text(s, 3.35, 5.55, 4.45, 0.95, [[("A bridge to Japan. ", {"bold": True}),
                                  ("Every AIM result translates back into Japan's own codes, so we can discuss "
                                   "it with Japan in their terms.", {})]], size=12, name="reinf1")
text(s, 8.1, 5.55, 4.45, 0.95, [[("A completeness check. ", {"bold": True}),
                                 (f"{z['pct_with_code']:.0f}% of what we bill carries a Japan code. The other "
                                  f"{eur_m(z['eur_without_code'])} is missing from Japan's file: a question for "
                                  "Japan, not a gap in AIM.", {})]], size=12, name="reinf2")
source(s, "Japan's catalogue code (ZKK) from Japan's parts-code file of 12 September 2025. Euro: price revision "
          "basis, July 2025 – June 2026.")
footer(s, "JAPAN'S CODE", 7)
notes(s, f"ZKK is Japan's catalogue code: three characters, carried on {z['pct_with_code']:.1f}% of billed euro in "
         f"this basis. Code {z['top_code']} alone holds {eur_m(z['top_code_eur'], 2)} ({z['top_code_pct']:.1f}%) "
         f"across {z['top_code_aim_l3_types']} AIM part types, so a sales chart by Japan code cannot separate "
         "brakes from body panels. The other way round, one AIM part type sits under many codes: " +
      ", ".join(f"{k} {v}" for k, v in cp.items()) +
      ". So we keep Japan's code as a reference on every part (traceability to Japan, completeness check) and "
      "use AIM for analysis. Settled position on the Japan codes: 90_INBOX/SETTLED_POSITION_JP_CODES_2026-09-20.md.")

# =====================================================================================
# 8  Norway versus Sweden
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
fg = {d["l1"]: d["gap_pv"] for d in nv["family_gap_pv"]}
show_pos = ["Steering", "Brakes", "Maintenance Service", "Suspension", "Wheels Hub"]
show_neg = ["Fuel System", "Cabin Interior", "Accident & Body"]
other = gap_total - sum(fg[k] for k in show_pos + show_neg)
cats = [nice(k) for k in show_pos] + ["All other families"] + [nice(k) for k in show_neg]
vals = [fg[k] for k in show_pos] + [other] + [fg[k] for k in show_neg]
colors = [RED, RED] + [MID] * 7
header(s, "SALES ANALYSIS", f"Norway brings in €{gap_total:.0f} more per vehicle than Sweden. AIM traces it "
                            "to two products",
       f"Similar light-commercial fleets: {nv['fleet']['Norway']:,} vehicles in service in Norway, "
       f"{nv['fleet']['Sverige']:,} in Sweden.")
text(s, 0.6, 2.4, 6.5, 0.62, [[(f"€{pv_no:.0f} against €{pv_se:.0f} per vehicle", {"bold": True, "size": 15})],
                              [("Difference by family, Norway minus Sweden, € per vehicle", {"color": GREY,
                                                                                            "size": 12})]],
     name="nv_t")
bar_chart(s, 0.6, 3.05, 6.5, 2.85, cats, vals, colors, lambda v: f"+€{v:.1f}" if v >= 0 else f"−€{-v:.1f}", "chart_nordic", size=11, vmax=23,
          vmin=-11, low_labels=True, gap=40)
su_no, su_se = det[("Steering Unit", "Norway")], det[("Steering Unit", "Sverige")]
pk_no, pk_se = det[("Brake Pad Kit", "Norway")], det[("Brake Pad Kit", "Sverige")]
fcards = [("STEERING UNITS", f"€{su_no['eur_pv']:.2f} vs €{su_se['eur_pv']:.2f} per vehicle",
           f"Norway bought {su_no['qty']:.0f}, almost all one part number on stock orders every two months. "
           f"Sweden bought {su_se['qty']:.0f}. A repair pattern in Norway, or demand Sweden is not getting?"),
          ("BRAKE PAD KITS", f"€{pk_no['eur_pv']:.2f} vs €{pk_se['eur_pv']:.2f} per vehicle",
           f"Norway buys {pk_no['qty_per_100']:.0f} kits per 100 vehicles a year, Sweden "
           f"{pk_se['qty_per_100']:.0f}. Where do Swedish owners buy their brake pads?")]
for i, (k, big, body) in enumerate(fcards):
    yy = 2.4 + i * 1.78
    box(s, 7.45, yy, 5.28, 1.62, WHITE, name=f"nf_bg{i}")
    text(s, 7.7, yy + 0.12, 4.9, 0.25, k, size=10, bold=True, color=RED, name=f"nf_k{i}")
    text(s, 7.7, yy + 0.38, 4.9, 0.4, big, size=18, bold=True, name=f"nf_v{i}")
    text(s, 7.7, yy + 0.82, 4.9, 0.75, body, size=12, name=f"nf_b{i}")
band(s, 5.98, 0.62, [[(f"Without families this is one number: Norway is {pv_no / pv_se * 100 - 100:.0f}% ahead. ",
                       {}), ("With AIM it is two concrete distributor conversations.", {"bold": True})]], size=15)
source(s, "Parts billed July 2025 – June 2026, price revision basis. Vehicles in service: 2025 estimates for both "
          "markets.")
footer(s, "SALES ANALYSIS", 8)
notes(s, f"Norway {eur_m(nv['eur']['Norway'], 2)} on {nv['fleet']['Norway']:,} vehicles = €{pv_no:.1f}; Sweden "
         f"{eur_m(nv['eur']['Sverige'], 2)} on {nv['fleet']['Sverige']:,} = €{pv_se:.1f}. Steering: Norway "
         f"{su_no['qty']:.0f} steering units ({eur_k(su_no['eur'])}, {su_no['pn']} part numbers; 81 of them part "
         f"7552348290 on stock orders of 15 to 20 every two months) against Sweden {su_se['qty']:.0f} "
         f"({eur_k(su_se['eur'])}). Brake pad kits: Norway {pk_no['qty']:.0f} ({eur_k(pk_no['eur'])}), Sweden "
         f"{pk_se['qty']:.0f} ({eur_k(pk_se['eur'])}). Both fleets are light commercial vehicles; the 2025 fleet "
         "counts are estimates. These are questions to take to the two distributors, not conclusions.")

# =====================================================================================
# 9  Price revision by product group
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
it = N["increase_total"]
pick = [("Steering Gear", "Steering gear"), ("Air Filter", "Air filters"), ("Fuel Filter", "Fuel filters"),
        ("Injection Pump", "Injection pumps"), ("Fuel Control", "Fuel control"), ("Lamps", "Lamps"),
        ("Oil Filter", "Oil filters"), ("Discs & Drums", "Brake discs & drums"), ("Wheel Rim", "Wheel rims"),
        ("Sensors", "Emission sensors"), ("EGR", "EGR"), ("Panels", "Body panels"),
        ("Pads & Shoes", "Brake pads & shoes")]
rows = [(lab, inc[k]["pct"]) for k, lab in pick]
rows.insert(7, ("All parts, average", it["pct"]))
pc_cats = [r[0] for r in rows]
pc_vals = [r[1] for r in rows]
pc_cols = [INK if c == "All parts, average" else (RED if c in ("Steering gear", "Brake pads & shoes") else MID)
           for c in pc_cats]
lo, hi = inc["Steering Gear"]["pct"], inc["Pads & Shoes"]["pct"]
header(s, "PRICE REVISIONS", f"The 2026 base-price increase averages {it['pct']:.1f}%. By product group it runs "
                             f"from {lo:.1f}% to {hi:.1f}%",
       "IML and IMIT base prices, weighted on what we billed July 2025 – June 2026.")
bar_chart(s, 0.6, 2.35, 7.0, 4.2, pc_cats, pc_vals, pc_cols, lambda v: f"+{v:.1f}%", "chart_increase", size=11, vmax=12,
          gap=35)
box(s, 7.95, 2.4, 4.78, 4.12, WHITE, name="flat_bg")
f_air, f_fuel = inc["Air Filter"]["pct"], inc["Fuel Filter"]["pct"]
flat = round(it["pct"])
text(s, 8.2, 2.5, 4.33, 3.9, [
    [("What one flat increase would do", {"bold": True, "size": 15})],
    [(f"Steering gear: base price +{lo:.1f}%", {"bold": True})],
    [(f"A flat {flat}% lifts our price about ten times more than our cost moved.", {})],
    [(f"Air and fuel filters: +{f_air:.1f} to +{f_fuel:.1f}%", {"bold": True})],
    [(f"A flat {flat}% makes the most frequent service parts dearer than the cost requires.", {})],
    [(f"Brake pads and shoes: +{hi:.1f}%", {"bold": True})],
    [(f"A flat {flat}% leaves four points unrecovered. The full {hi:.0f}% lands on a wear part where "
      "independent brands compete.", {})],
    [("AIM turns one network percentage into a decision per product group.", {"bold": True, "color": RED})]],
     size=12.5, spacing=[0, 12, 2, 10, 2, 10, 2, 14], name="flat", anchor=MSO_ANCHOR.MIDDLE)
source(s, f"Base-price move weighted on billed quantities, not a revenue or margin forecast. Worth "
          f"{eur_m(it['step_eur'], 2)} at last year's volumes. Product groups with at least €0.5M billed.")
footer(s, "PRICE REVISIONS", 9)
notes(s, f"Weighted base-price increase {it['pct']:.2f}% on the price revision basis (priced lines "
         f"{eur_m(it['priced_eur'], 2)}), worth {eur_m(it['step_eur'], 2)} on last year's quantities. By AIM product "
         "group (groups with at least €0.5M billed): " +
      "; ".join(f"{d['l2']} +{d['pct']:.2f}%" for d in N["increase_l2"]) +
      ". This is a base-price move on billed quantities, not revenue, margin or demand response. Same basis as the "
      "price revision workbook (5.9616%, €1,652,140.71).")

# =====================================================================================
# 10  What AIM gives us
s = prs.slides.add_slide(BLANK)
background(s, PAPER)
header(s, "WHAT AIM GIVES US", "Six things we can do now that we could not do before",
       "Each one is shown with real numbers earlier in this presentation.")
adv = [("Explain sales to the part",
        f"Norway against Sweden: a {pv_no / pv_se * 100 - 100:.0f}% gap traced to one steering unit and to brake pads."),
       ("Price per product group",
        f"Base-price increases from {lo:.1f}% to {hi:.1f}%, instead of one {it['pct']:.1f}% average."),
       ("Compare like with like",
        f"A €{el['avg']:.0f} filter element is no longer averaged with a €{asm['avg']:.0f} housing."),
       ("See every product range",
        f"{eur_m(mis_total)} a year back in the family it belongs to. Air filters are complete again."),
       ("One language for every distributor",
        f"{L[0]} families, {L[1]} product groups and {L[2]} part types, the same in every market."),
       ("Talk to Japan in its own codes",
        f"Japan's catalogue code is kept on every part. {z['pct_with_code']:.0f}% of billed euro is already linked.")]
for i, (h_, b_) in enumerate(adv):
    r, c = divmod(i, 3)
    cx, cy = 0.6 + c * 4.11, 2.4 + r * 1.95
    box(s, cx, cy, 3.91, 1.78, WHITE, name=f"adv_bg{i}")
    box(s, cx + 0.22, cy + 0.22, 0.46, 0.46, RED, shape=MSO_SHAPE.OVAL, name=f"adv_dot{i}")
    text(s, cx + 0.22, cy + 0.22, 0.46, 0.46, str(i + 1), size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, name=f"adv_n{i}")
    text(s, cx + 0.85, cy + 0.2, 2.9, 0.5, h_, size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE, name=f"adv_h{i}")
    text(s, cx + 0.22, cy + 0.82, 3.5, 0.9, b_, size=12.5, color=GREY, name=f"adv_b{i}")
band(s, 6.33, 0.5, [[("Next: ", {"bold": True}),
                     ("link old and new part numbers, so a superseded part no longer looks like lost business.",
                      {})]], size=14)
footer(s, "WHAT AIM GIVES US", 10)
notes(s, "The six advantages, each tied to a page: 1 Norway against Sweden (page 8); 2 base-price increase by "
         "product group (page 9); 3 element against housing (page 6); 4 parts back in the right family (page 3); "
         f"5 one structure for every market ({L[0]}/{L[1]}/{L[2]}); 6 Japan's code kept on every part (page 7). "
         "Next step: interchangeability, linking superseded part numbers to their replacements once the source "
         "file is supplied.")

# =====================================================================================
# 11  The decision
s = prs.slides.add_slide(BLANK)
background(s, INK)
text(s, 0.7, 0.62, 6.0, 0.3, "THE DECISION WE ASK FOR", size=11, bold=True, color=LIGHT, name="d_kicker")
text(s, 0.7, 1.35, 5.6, 3.2, ["From a label", "to a product.", "From a product", "to a decision."], size=38,
     bold=True, color=WHITE, name="d_title", line=0.95)
dec = [("USE", "AIM as the one product language for distributor sales reviews and price revisions."),
       ("OWN", "Maintenance stays in Vehicle Parts Sales, through approved releases."),
       ("PROVE", "Take the two Nordic findings into the next distributor reviews and report the outcome.")]
for i, (k, t) in enumerate(dec):
    yy = 1.4 + i * 1.45
    box(s, 6.95, yy, 5.78, 1.25, CHAR2, name=f"dec_bg{i}")
    text(s, 7.2, yy, 1.3, 1.25, k, size=18, bold=True, color=RGBColor(0xF2, 0x96, 0x9B),
         anchor=MSO_ANCHOR.MIDDLE, name=f"dec_k{i}")
    text(s, 8.5, yy, 4.05, 1.25, t, size=15, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, name=f"dec_t{i}")
text(s, 0.7, 5.6, 5.6, 0.6, "AIM: one parts classification for sales analysis and price revisions.", size=13,
     color=LIGHT, name="d_tag")
footer(s, "THE DECISION", 11, dark=True)
notes(s, "Management is asked to endorse three things: use AIM as the one product language for sales reviews and "
         "price revisions; keep maintenance local in Vehicle Parts Sales through approved, dated releases; and prove "
         "it on two real cases from page 8 (steering units in Norway, brake pad kits in Sweden). No catalogue-wide "
         "automatic price change is proposed.")

prs.save(OUT)
print("saved", OUT)
