"""Parts classification management presentation, charcoal look (11 Oct 2026). Every figure comes from aim_numbers.json.

Output: 05_AIM_classification/ISZE_Parts_Classification_Management_CHARCOAL_2026-10-11.pptx
Stance of the deck: Jerome informs management that he uses our parts classification. It asks for no decision. Spoken name: parts classification — never AIM.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from charcoal_lib import *  # noqa: E402,F401,F403

N = json.loads((HERE / "aim_numbers.json").read_text(encoding="utf-8"))
import os
OUT = Path(os.environ.get("DECK_OUT") or (HERE.parents[1] / "05_AIM_classification" / "ISZE_Parts_Classification_Management_CHARCOAL_2026-10-11.pptx"))
A = HERE / "assets"

LIGHT = rgb("DADADA")
BOOK = N["base"]["billed_eur"]
comp_n = N["composition"]
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
st = N["steering"]
L = N["levels"]["aim"]
NICE = {"Intake Exhaust Emission": "Intake, exhaust & emission", "Accident & Body": "Accident & body",
        "Maintenance Service": "Maintenance service", "Wheels Hub": "Wheels & hubs", "Fuel System": "Fuel system",
        "Cabin Interior": "Cabin interior", "Driveline Axle": "Driveline & axle", "Chassis Frame": "Chassis frame"}
nice = lambda s: NICE.get(s, s)  # noqa: E731
NONPART = comp_n["non_part_eur"]

prs = new_deck()
page = [0]


def nxt():
    page[0] += 1
    return page[0]


# =====================================================================================
# 1  Cover (no photo)
nxt()
s = cover(prs, "ISZE  ·  VEHICLE PARTS & ACCESSORIES  ·  MANAGEMENT PRESENTATION",
          ["Parts classification"],
          "A single product view of the parts we bill to our distributors, used for sales analysis and price revisions.",
          "October 2026  ·  For information, no decision requested")
notes(s, "The money first: we bill about €35 million "
         "a year to our distributors (the price revision base, July 2025 – June 2026, 15,872 part numbers). "
         f"{eur_m(NONPART, 2)} of that is rebate, transport and lubricants, so the parts alone are about "
         f"€{(BOOK - NONPART) / 1e6:.1f}M. The question this presentation answers: what are those parts, and what can we "
         "do once we know?")

# =====================================================================================
# 2  The old top level
s = blank(prs)
order_old = ["Competitive parts", "Repair parts", "Accident parts", "High value repair", "Other / review",
             "Comfort parts", "Hardware & consumables"]
top10 = N["aim_l1"][:10]
frame(s, "The problem", "The old price list filed steering units as “Competitive parts”",
      "Nobody else makes a steering unit. That label mixed captive parts with wear parts under one commercial opinion.",
      source=f"Base: €{BOOK / 1e6:.1f}M billed July 2025 – June 2026 ({N['base']['part_numbers']:,} part numbers), "
             f"including {eur_m(NONPART, 2)} rebate, transport and lubricants. Old: price-list labels. "
             "New: parts classification, release of 7 October 2026.",
      page=nxt(), panel=[
          ("The old top level mixed views on competition with product names. You could not ask “how are brakes "
           "selling?” from it.", RED),
          (f"The new top level names what the part is: {L[0]} families, from brakes to lighting.", AMBER),
          ("Purpose: one product view of everything we bill, so sales and prices can be read per product.", AMBER)])
text(s, 0.25, 1.98, 4.5, 0.3, "Old “Competitive” label: biggest part types", size=12, bold=True)
top5 = N["old_competitive_top_l3"][:5]
hbar(s, 0.25, 2.3, 4.5, 3.25, [d["l3"] for d in top5], [d["eur"] for d in top5], [RED] + [BAR] * 4,
     lambda v: f"€{v / 1e6:.2f}M", "chart_old", vmax=1.65e6, size=10.5)
text(s, 5.0, 1.98, 4.65, 0.3, f"New top level: the ten largest of {L[0]} families", size=12, bold=True)
hbar(s, 5.0, 2.3, 4.65, 3.25, [nice(d["label"]) for d in top10], [d["pct"] for d in top10], [LIGHT] * 10,
     lambda v: f"{v:.1f}%", "chart_aim", vmax=23, size=10, gap=40)
band(s, 0.25, 5.8, 9.4, 0.95, [[(f"{eur_m(comp['eur'])} sat under one commercial label — not a measure of competition. ",
                                  {"bold": True}),
                                 (f"Steering units alone are {eur_m(st['eur_under_competitive'], 2)} of that pile; they are captive, not competitive.", {})]], size=12.5)
notes(s, f"The old tree had {N['levels']['old'][0]} top-level labels. Five describe a commercial opinion (competitive, "
         f"repair, accident, high value repair, comfort), not a product. {eur_m(comp['eur'], 2)} of what we billed "
         "sat in 'Competitive parts'. Inside it, by part type: " +
      ", ".join(f"{d['l3']} {eur_m(d['eur'], 2)}" for d in N["old_competitive_top_l3"][:5]) +
      f". The new classification has {L[0]} families, {L[1]} product groups and {L[2]} part types on this basis; the old tree had "
      f"{N['levels']['old'][0]} / {N['levels']['old'][1]} / {N['levels']['old'][2]}.")

# =====================================================================================
# 3  Parts in the wrong family
s = blank(prs)
mis_total = N["misfiled_total_eur"]
acl = mis[0]
frame(s, "The problem", f"{eur_m(mis_total)} a year sat in the wrong family",
      "The old rule read only the price-list text. It could not know that “ACL” means air cleaner.",
      source="Old placements: classification audit of 20 September 2026, each confirmed against Isuzu's parts catalogue "
             "figures. Euro: price revision base, July 2025 – June 2026.",
      page=nxt(), panel=[
          ("A report on air filters, steering or bumpers was wrong by the amounts in this table before anyone looked at "
           "a price.", RED),
          ("The classification reads five facts per part (page 5), so “FILTER; ACL” is an air cleaner element, not air "
           "conditioning.", AMBER),
          ("Purpose: get the family right first. Sales analysis and pricing follow from it.", AMBER)])
cols = [(0.45, 2.15, "PART"), (2.7, 1.9, "WHAT WE BILLED"), (4.75, 2.35, "OLD RULE FILED IT AS"),
        (7.2, 2.4, "NEW PLACES IT")]
for cx, cw, lab in cols:
    text(s, cx, 2.0, cw, 0.22, lab, size=8.5, bold=True, color=SUB, name=f"th_{lab[:6]}")
aim_short = {"Engine air cleaner elements": "Maintenance service › Air filter",
             "King pin kits": "Steering › Knuckle & king pin", "Steering drag links": "Steering › Linkage",
             "Front and rear bumper bars": "Accident & body › Bumper",
             "Suspension ball joints": "Suspension › Suspension arm"}
names = {"Front and rear bumper bars": "Bumper bars", "Suspension ball joints": "Ball joints"}
rmax = max(m["eur"] for m in mis)
for i, m in enumerate(mis):
    ry = 2.3 + i * 0.7
    rect(s, 0.25, ry, 9.4, 0.62, fill=CARD, name=f"row_bg{i}")
    text(s, 0.45, ry, 2.2, 0.62, names.get(m["name"], m["name"]), size=12, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         name=f"row_name{i}")
    bw = max(0.08, 1.15 * m["eur"] / rmax)
    rect(s, 2.7, ry + 0.2, bw, 0.22, fill=RED if i == 0 else BAR, name=f"row_bar{i}")
    text(s, 2.7 + bw + 0.1, ry, 0.8, 0.62, eur_k(m["eur"]), size=11.5, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         name=f"row_eur{i}")
    text(s, 4.75, ry, 2.35, 0.62, [[(m["old"].replace(" > ", " › "), {"strike": True})]], size=10.5, color=SUB,
         anchor=MSO_ANCHOR.MIDDLE, name=f"row_old{i}")
    text(s, 7.2, ry, 2.4, 0.62, aim_short[m["name"]], size=10.5, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         name=f"row_aim{i}")
text(s, 0.45, 5.85, 5, 0.3, [[("Total ", {}), (f"{eur_m(mis_total, 2)} a year", {"bold": True})]], size=12.5,
     name="row_total")
band(s, 0.25, 6.25, 9.4, 0.65, [[("Ask “how are our air filters selling?” and the old tree missed ", {}),
                                  (f"{eur_m(acl['eur'], 2)} of the {eur_m(N['air_cleaner_filter_total_eur'], 2)} answer.",
                                   {"bold": True})]], size=12.5)
notes(s, "Five classes where the price-list text names the system beyond argument and the old rule still filed the "
         "part somewhere physically unrelated. Euro on this basis: " +
      "; ".join(f"{m['name']} {eur_k(m['eur'])} ({m['pn']} part numbers)" for m in mis) +
      ". The old placements and their check against Isuzu catalogue figures (1-30 Air Cleaner, 4-10 Front Axle) are in "
      "the classification audit of 20 September 2026. Air cleaner elements under the classification today: "
      f"{eur_m(N['air_cleaner_filter_total_eur'], 2)}, of which FILTER; ACL lines {eur_m(acl['eur'], 2)}.")

# =====================================================================================
# 4  The competitive label, tested both ways
s = blank(prs)
frame(s, "The problem", "The old “Competitive” label was a weak guide to where independent brands compete",
      "Tested on 302 parts we checked against independent-brand prices. A pointer, not a measurement.",
      source="Classification audit, 17 September 2026: 302 parts checked against Autodoc, KS and Mekonomen prices, not a "
             "random sample. Steering: parts billed July 2025 – June 2026; competitive price file, 6 October 2026.",
      page=nxt(), panel=[
          ("For a price revision the label is right about half the time, and wrong in both directions.", RED),
          ("Raise a “repair part” and you may raise it where the customer already has a cheaper choice. Hold a "
           "“competitive part” and you may give margin away where nobody competes.", AMBER),
          ("Purpose: let price evidence, per product and per market, decide where we compete. Our parts classification gives that evidence a "
           "product to attach to.", AMBER)])
rect(s, 0.25, 1.98, 4.6, 4.15, fill=CARD, line=BORDER, name="cardL_bg")
text(s, 0.45, 2.12, 4.2, 0.22, "HOW OFTEN THE LABEL MATCHED THE EVIDENCE", size=8.5, bold=True, color=RED)
text(s, 0.45, 2.4, 4.2, 0.4, "Parts with an independent-brand match, by old label", size=11, color=SUB)
hbar(s, 0.35, 2.85, 4.4, 1.35, ["Labelled “Competitive” (66 of 119)", "Labelled anything else (71 of 183)"],
     [55.5, 38.8], [RED, BAR], lambda v: f"{v:.1f}%", "chart_hit", vmax=82, size=10.5, gap=50)
text(s, 0.45, 4.4, 1.6, 0.8, "48%", size=40, bold=True, color=RED, name="stat48")
text(s, 2.1, 4.45, 2.6, 1.55, "of the 137 parts with a confirmed independent-brand alternative carried the "
                              "“Competitive” label. The other 52% were filed as repair, accident, comfort or hardware.",
     size=11, name="stat48_t")
rect(s, 5.05, 1.98, 4.6, 4.15, fill=CARD, line=BORDER, name="cardR_bg")
text(s, 5.25, 2.12, 4.2, 0.22, "THE OTHER WAY: A LABEL WITHOUT EVIDENCE", size=8.5, bold=True, color=RED)
text(s, 5.25, 2.5, 4.2, 0.6, eur_m(st["eur_under_competitive"], 2), size=36, bold=True, color=RED, name="statsteer")
text(s, 5.25, 3.25, 4.2, 0.5, "of steering units billed, filed under “Competitive parts”", size=12, bold=True)
text(s, 5.25, 3.85, 4.2, 2.2, [
    f"{st['pn_under_competitive']} of the {st['pn']} steering unit part numbers we billed carried that label. One part "
    f"number, {st['top_pn']}, is {st['top_pn_share_pct']:.0f}% of the euro.",
    f"None of the {st['price_file_pn']} steering part numbers in our competitive price file has an "
    "independent-brand price. Prices exist for "
    f"{st['competitive_eur_with_independent_price_pct']:.0f}% of the euro under that label, so this is a pointer, "
    "not proof."], size=11, spacing=8, name="steer_t")
band(s, 0.25, 6.3, 9.4, 0.6, [[("A label cannot tell us where we compete. Price evidence can, ", {}),
                                ("and it needs a real product to attach to. That is what the classification provides.", {"bold": True})]],
     size=12)
notes(s, "Measured in the classification audit against our own independent-brand price scrapes (302 parts, not drawn "
         "at random, Competitive parts over-represented). Labelled Competitive: 66 of 119 had an independent-brand match "
         "(55.5%); labelled anything else: 71 of 183 (38.8%); lift 1.43. Turned round: of the 137 parts with a confirmed "
         "alternative, 48.2% sat in Competitive parts. Treat as direction, not measurement. Competition depends on the "
         "market, not on the part's name; the classification fixes the product and the competition check sits beside it per market. "
         f"Steering units: {st['pn_under_competitive']} of {st['pn']} part numbers billed are under Competitive parts "
         f"({eur_m(st['eur_under_competitive'], 2)}); {st['price_file_pn']} steering part numbers in the competitive "
         f"price file, {st['price_file_pn_with_independent_price']} with an independent-brand price. An "
         f"independent-brand price exists for {st['competitive_eur_with_independent_price_pct']:.1f}% of the euro under "
         "Competitive parts, so absence of a price is not proof of absence of competition.")

# =====================================================================================
# 5  What the classification is
s = blank(prs)
path = N["path"]
cov = N["coverage"]
frame(s, "The answer", "Our parts classification gives every part a family, a product group and a part type",
      "It reads five facts about each part together, not just its name.",
      source="Billed July 2025 – June 2026, price revision base. Coverage: share of billed euro with a family, product "
             "group and part type.",
      page=nxt(), panel=[
          ("One part number now carries a family, a product group and a part type, each with its euro.", RED),
          ("Five facts are read together. Where they disagree, the part goes to review instead of being guessed.", AMBER),
          ("Purpose: any question about sales or prices starts from a product and drills down to the part number.", AMBER)])
steps = [("FAMILY", "Brakes", path["l1"][1], rgb("1F1F1F"), TXT),
         ("PRODUCT GROUP", "Pads & shoes", path["l2"][1], rgb("3A3A3A"), TXT),
         ("PART TYPE", "Brake pad kit", path["l3"][1], rgb("565656"), TXT),
         (f"PART NUMBER {path['pn'][0]}", "Front disc brake pad kit", path["pn"][2], RED, WHITE)]
for i, (lab, nm, v, fill, fc) in enumerate(steps):
    x0, y0 = 0.25 + i * 0.25, 2.0 + i * 0.88
    rect(s, x0, y0, 4.4, 0.74, fill=fill, line=BORDER if i == 0 else None, name=f"lvl{i}")
    text(s, x0 + 0.18, y0 + 0.07, 3.0, 0.2, lab, size=8.5, bold=True, color=SUB if fill != RED else WHITE, name=f"lvl{i}_k")
    text(s, x0 + 0.18, y0 + 0.3, 3.0, 0.36, nm, size=14, bold=True, color=fc, name=f"lvl{i}_n")
    text(s, x0 + 3.2, y0 + 0.07, 1.05, 0.6, eur_m(v, 2), size=14, bold=True, color=fc, align=PP_ALIGN.RIGHT,
         anchor=MSO_ANCHOR.MIDDLE, name=f"lvl{i}_v")
text(s, 0.25, 5.62, 5.2, 0.25, "Billed July 2025 – June 2026, price revision base.", size=9.5, color=MUTE)
facts = [("Part number", "links sales, prices and the catalogue"), ("Description", "what the price list calls the part"),
         ("Catalogue figure", "where Isuzu draws it on the vehicle"),
         ("Customs code", "an independent check on the product"),
         ("Price", f"separates a €{el['avg']:.0f} element from a €{asm['avg']:.0f} housing")]
text(s, 5.75, 1.98, 3.9, 0.3, "Five facts, read together", size=13, bold=True)
for i, (a_, b_) in enumerate(facts):
    fy = 2.4 + i * 0.58
    rect(s, 5.75, fy + 0.05, 0.34, 0.34, fill=RED, shape=MSO_SHAPE.OVAL, name=f"fact_dot{i}")
    text(s, 5.75, fy + 0.05, 0.34, 0.34, str(i + 1), size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, name=f"fact_n{i}")
    text(s, 6.25, fy, 3.4, 0.46, [[(a_ + "  ", {"bold": True}), (b_, {"color": SUB})]], size=11, anchor=MSO_ANCHOR.MIDDLE,
         name=f"fact{i}")
text(s, 6.25, 5.3, 3.4, 0.4, [[("+ Japan's code  ", {"bold": True}), ("kept on every part (page 7)", {"color": SUB})]],
     size=11, anchor=MSO_ANCHOR.MIDDLE, name="fact_jp")
kp = [(f"{cov['pct_l1']:.0f}%", "of what we bill has a family, group and part type"),
      (f"{L[0]} · {L[1]} · {L[2]}", "families · product groups · part types"),
      ("7 Oct 2026", "release these figures use, kept by Vehicle Parts Sales")]
for i, (big, small) in enumerate(kp):
    kx = 0.25 + i * 3.15
    rect(s, kx, 6.05, 3.05, 0.85, fill=CARD, line=BORDER, name=f"kpi_bg{i}")
    text(s, kx + 0.15, 6.05, 2.8, 0.85, [[(big, {"bold": True, "color": RED, "size": 15})], [(small, {"size": 9.5, "color": SUB})]],
         anchor=MSO_ANCHOR.MIDDLE, name=f"kpi{i}")
notes(s, "Our parts classification gives three levels: family, product group, part type. Example path with "
         f"billed euro: Brakes {eur_m(path['l1'][1], 2)} > Pads & shoes {eur_m(path['l2'][1], 2)} > Brake pad kit "
         f"{eur_m(path['l3'][1], 2)} > part {path['pn'][0]} ({path['pn'][1]}) {eur_m(path['pn'][2], 2)}. The five facts "
         "are read together; where they disagree the part goes to review instead of being guessed. Coverage on this "
         f"basis: {cov['pct_l1']:.2f}% of billed euro ({cov['pct_l1_parts_only']:.2f}% of parts alone); "
         f"{cov['pn_open']:,} part numbers ({eur_k(cov['eur_open'])}) still open, of which €{cov['eur_open_parts_only'] / 1e3:,.0f}k "
         "is parts (the rest is the rebate line). Approved releases: 4 and 7 October 2026. A hotfix release of 11 October (119 parts, about €0.2M) is not in these figures; it does not change a headline.")

# =====================================================================================
# 6  Element versus housing
s = blank(prs)
ratio = asm["avg"] / el["avg"]
frame(s, "Precision", "An element and a housing share a family, not a price",
      "The classification keeps them apart, so every price and sales comparison is like for like.",
      source="Billed July 2025 – June 2026, price revision base, all filter part numbers marked element or housing / "
             "assembly in the classification. Photos: dealer and supplier listings, product form only.",
      page=nxt(), panel=[
          (f"Averaged together, a “filter” costs €{N['filter_roles_blended_avg']:.2f} per unit, a price that describes "
           "neither product.", RED),
          ("An element is bought at every service. A housing is bought after damage or failure. They belong in "
           "different parts of a sales review.", AMBER),
          ("Purpose: compare distributors and years like for like.", AMBER)])
cards = [(0.25, "element.jpg", "FILTER ELEMENTS", el, "Replaced at every service. A routine purchase, bought again and again."),
         (5.1, "housing.jpg", "FILTER HOUSINGS AND ASSEMBLIES", asm,
          "Replaced after damage or failure. A repair purchase, not a service one.")]
for i, (cx, img, lab, d, desc) in enumerate(cards):
    rect(s, cx, 2.0, 4.55, 3.75, fill=CARD, line=BORDER, name=f"card{i}")
    rect(s, cx + 0.15, 2.15, 2.0, 2.0, fill=WHITE, name=f"card_imgbg{i}")
    picture(s, A / img, cx + 0.17, 2.17, 1.96, 1.96, name=f"card_img{i}")
    text(s, cx + 0.15, 4.2, 2.0, 0.3, "Product form only; not a specific part number.", size=8, color=MUTE, name=f"card_c{i}")
    text(s, cx + 2.3, 2.15, 2.1, 0.5, lab, size=9, bold=True, color=RED, name=f"card_k{i}")
    text(s, cx + 2.3, 2.7, 2.1, 0.55, f"€{d['avg']:.2f}", size=26, bold=True, name=f"card_v{i}")
    text(s, cx + 2.3, 3.28, 2.1, 0.25, "average per unit", size=10, color=SUB, name=f"card_u{i}")
    text(s, cx + 2.3, 3.65, 2.1, 0.5, [f"{eur_m(d['eur'], 2)} billed", f"{d['pn']} part numbers"], size=10, color=SUB,
         name=f"card_m{i}")
    text(s, cx + 0.15, 4.75, 4.25, 0.9, desc, size=11, name=f"card_d{i}")
rect(s, 4.3, 3.3, 0.75, 0.75, fill=RED, shape=MSO_SHAPE.OVAL, name="ratio_dot")
text(s, 4.3, 3.3, 0.75, 0.75, f"{ratio:.0f}×", size=17, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
     anchor=MSO_ANCHOR.MIDDLE, name="ratio")
band(s, 0.25, 6.0, 9.4, 0.8, [[("Averaged together, a “filter” costs ", {}),
                                (f"€{N['filter_roles_blended_avg']:.2f} per unit", {"bold": True}),
                                (", a price that describes neither product.", {})]], size=13)
notes(s, f"Filter elements: {eur_m(el['eur'], 2)} billed, {el['qty']:,.0f} units, {el['pn']} part numbers, "
         f"€{el['avg']:.2f} per unit. Housings and assemblies: {eur_m(asm['eur'], 2)}, {asm['qty']:,.0f} units, "
         f"{asm['pn']} part numbers, €{asm['avg']:.2f} per unit, {ratio:.1f} times the element. Blended: "
         f"€{N['filter_roles_blended_avg']:.2f}. The element photo is an Isuzu Best Value element in its box; the housing "
         "photo is a supplier listing. Both show product form only. These are the only photos in the presentation.")

# =====================================================================================
# 7  Japan's catalogue code
s = blank(prs)
tb = z["top_code_by_l1"][:7]
frame(s, "Japan's code", "Japan's code stays on every part, but it cannot replace our parts classification",
      "The code says where Japan files a part. Our classification says what the part is. We need both.",
      source="Japan's catalogue code (ZKK) from Japan's parts-code file of 12 September 2025. Euro: price revision base, "
             "July 2025 – June 2026.",
      page=nxt(), panel=[
          (f"One Japan code holds {z['top_code_pct']:.0f}% of what we bill, across {z['top_code_aim_l3_types']} part "
           "types. A sales chart by Japan code cannot separate brakes from body panels.", RED),
          ("Every classification result can be translated back to Japan's own code, so a conversation with Japan can use their "
           "terms.", AMBER),
          ("Purpose: we analyse with our parts classification and talk to Japan in their code. Neither replaces the other.", AMBER)])
text(s, 0.25, 1.98, 5.2, 0.55, [[("One Japan code, many products", {"bold": True, "size": 13})],
                                [(f"Code {z['top_code']}: {z['top_code_pct']:.0f}% of what we bill, by family",
                                  {"color": SUB, "size": 10.5})]], name="z_left_t")
hbar(s, 0.25, 2.6, 5.3, 2.7, [nice(d["l1"]) for d in tb], [d["eur"] / 1e6 for d in tb], [LIGHT] * len(tb),
     lambda v: f"€{v:.1f}M", "chart_zkk", size=10, vmax=4.2, gap=40)
text(s, 5.85, 1.98, 3.8, 0.55, [[("One product, many Japan codes", {"bold": True, "size": 13})],
                                [("Different Japan codes on the same part type", {"color": SUB, "size": 10.5})]],
     name="z_right_t")
cp = z["codes_per_type"]
for i, (t_, lab) in enumerate([("Brake Pad Kit", "brake pad kits"), ("Air Cleaner Filter", "air cleaner elements"),
                               ("Door", "doors")]):
    yy = 2.6 + i * 0.85
    rect(s, 5.85, yy, 3.8, 0.72, fill=CARD, name=f"zc_bg{i}")
    text(s, 6.0, yy, 0.9, 0.72, str(cp[t_]), size=24, bold=True, color=RED, anchor=MSO_ANCHOR.MIDDLE, name=f"zc_n{i}")
    text(s, 6.9, yy, 2.65, 0.72, f"Japan codes for {lab}", size=11.5, anchor=MSO_ANCHOR.MIDDLE, name=f"zc_t{i}")
rect(s, 0.25, 5.6, 9.4, 1.25, fill=CARD, line=BORDER, name="reinf_bg")
text(s, 0.45, 5.72, 2.1, 1.0, "How the code reinforces the classification", size=12, bold=True, color=RED, name="reinf_t")
text(s, 2.7, 5.72, 2.8, 1.05, [[("A bridge to Japan. ", {"bold": True}),
                                ("Every classification result translates back into Japan's own codes.", {})]], size=10.5,
     name="reinf1")
text(s, 5.7, 5.72, 3.85, 1.05, [[("A completeness check. ", {"bold": True}),
                                (f"{z['pct_with_code']:.0f}% of what we bill carries a Japan code. Of the other "
                                 f"{eur_m(z['eur_without_code'])}: {eur_m(z['without_code_nonpart_eur'])} is rebate, "
                                 f"transport and lubricants, {eur_m(z['without_code_steering_eur'])} is "
                                 f"{z['without_code_steering_pn']} steering unit part numbers, "
                                 f"{eur_m(z['without_code_other_eur'])} other parts. Questions for Japan, "
                                 "not gaps in the classification.", {})]], size=10.5, name="reinf2")
notes(s, f"ZKK is Japan's catalogue code: three characters, carried on {z['pct_with_code']:.1f}% of billed euro "
         f"({z['pct_with_code_parts_only']:.1f}% of parts alone). Code {z['top_code']} alone holds "
         f"{eur_m(z['top_code_eur'], 2)} ({z['top_code_pct']:.1f}%) across {z['top_code_aim_l3_types']} part types. "
         "The other way round, one part type sits under many codes: " +
      ", ".join(f"{k} {v}" for k, v in cp.items()) +
      f". Without a Japan code: {eur_m(z['eur_without_code'], 2)}, of which rebate, transport and lubricants "
      f"{eur_m(z['without_code_nonpart_eur'], 2)}, {z['without_code_steering_pn']} steering unit part numbers "
      f"{eur_m(z['without_code_steering_eur'], 2)}, other parts {eur_m(z['without_code_other_eur'], 2)}.")

# =====================================================================================
# 8  Norway versus Sweden
s = blank(prs)
fg = {d["l1"]: d["gap_pv"] for d in nv["family_gap_pv"]}
show_pos = ["Steering", "Brakes", "Maintenance Service", "Suspension", "Wheels Hub"]
show_neg = ["Fuel System", "Cabin Interior", "Accident & Body"]
other = gap_total - sum(fg[k] for k in show_pos + show_neg)
cats = [nice(k) for k in show_pos] + ["All other families"] + [nice(k) for k in show_neg]
vals = [fg[k] for k in show_pos] + [other] + [fg[k] for k in show_neg]
colors = [RED, RED] + [BAR] * 7
su_no, su_se = det[("Steering Unit", "Norway")], det[("Steering Unit", "Sverige")]
pk_no, pk_se = det[("Brake Pad Kit", "Norway")], det[("Brake Pad Kit", "Sverige")]
frame(s, "Sales analysis", f"Norway brings in €{gap_total:.0f} more per vehicle than Sweden. The classification traces it to two products",
      f"Similar light-commercial fleets: {nv['fleet']['Norway']:,} vehicles in service in Norway, "
      f"{nv['fleet']['Sverige']:,} in Sweden.",
      source="Parts billed July 2025 – June 2026, price revision base. Vehicles in service: 2025 estimates for both "
             "markets.",
      page=nxt(), panel=[
          (f"Two similar fleets, two different parts bills: €{pv_no:.0f} against €{pv_se:.0f} per vehicle.", RED),
          ("Steering units and brake pad kits explain most of it. Both are questions for the distributor, not "
           "conclusions.", AMBER),
          ("Purpose: turn a gap between two distributors into a question about a named product.", AMBER)])
text(s, 0.25, 1.98, 5.4, 0.55, [[(f"€{pv_no:.0f} against €{pv_se:.0f} per vehicle", {"bold": True, "size": 13})],
                               [("Difference by family, Norway minus Sweden, € per vehicle", {"color": SUB, "size": 10.5})]],
     name="nv_t")
hbar(s, 0.25, 2.6, 5.45, 3.35, cats, vals, colors, lambda v: f"+€{v:.1f}" if v >= 0 else f"−€{-v:.1f}",
     "chart_nordic", size=10.5, vmax=24, vmin=-12, low_labels=True, gap=40)
fcards = [("STEERING UNITS", f"€{su_no['eur_pv']:.2f} vs €{su_se['eur_pv']:.2f} per vehicle",
           f"Norway bought {su_no['qty']:.0f}, 81 of them one part number. Sweden bought "
           f"{su_se['qty']:.0f}. A repair pattern in Norway, or demand Sweden is not getting?"),
          ("BRAKE PAD KITS", f"€{pk_no['eur_pv']:.2f} vs €{pk_se['eur_pv']:.2f} per vehicle",
           f"Norway buys {pk_no['qty_per_100']:.0f} kits per 100 vehicles a year, Sweden {pk_se['qty_per_100']:.0f}. "
           "Where do Swedish owners buy their brake pads?")]
for i, (k, big, body) in enumerate(fcards):
    yy = 1.98 + i * 2.0
    rect(s, 5.9, yy, 3.75, 1.85, fill=CARD, line=BORDER, name=f"nf_bg{i}")
    text(s, 6.1, yy + 0.12, 3.4, 0.22, k, size=8.5, bold=True, color=RED, name=f"nf_k{i}")
    text(s, 6.1, yy + 0.38, 3.4, 0.35, big, size=14, bold=True, name=f"nf_v{i}")
    text(s, 6.1, yy + 0.8, 3.4, 1.0, body, size=10.5, color=SUB, name=f"nf_b{i}")
band(s, 0.25, 6.15, 9.4, 0.75, [[(f"Without families this is one number: Norway is {pv_no / pv_se * 100 - 100:.0f}% ahead. ", {}),
                                  ("With the classification it is two concrete distributor conversations.", {"bold": True})]], size=12.5)
notes(s, f"Norway {eur_m(nv['eur']['Norway'], 2)} on {nv['fleet']['Norway']:,} vehicles = €{pv_no:.1f}; Sweden "
         f"{eur_m(nv['eur']['Sverige'], 2)} on {nv['fleet']['Sverige']:,} = €{pv_se:.1f}. Steering: Norway "
         f"{su_no['qty']:.0f} steering units ({eur_k(su_no['eur'])}, {su_no['pn']} part numbers; 81 of them part "
         f"7552348290) against Sweden {su_se['qty']:.0f} "
         f"({eur_k(su_se['eur'])}, 7 of them the same part number). Brake pad kits: Norway {pk_no['qty']:.0f} ({eur_k(pk_no['eur'])}), Sweden "
         f"{pk_se['qty']:.0f} ({eur_k(pk_se['eur'])}). Both fleets are light commercial vehicles; the 2025 fleet counts "
         "are estimates. These are questions to take to the two distributors, not conclusions.")

# =====================================================================================
# 9  The factory increase by product group
s = blank(prs)
it = N["increase_total"]
pick = [("Steering Gear", "Steering gear"), ("Air Filter", "Air filters"), ("Fuel Filter", "Fuel filters"),
        ("Injection Pump", "Injection pumps"), ("Fuel Control", "Fuel control"), ("Lamps", "Lamps"),
        ("Oil Filter", "Oil filters"), ("Discs & Drums", "Brake discs & drums"), ("Wheel Rim", "Wheel rims"),
        ("Sensors", "Emission sensors"), ("EGR", "EGR"), ("Panels", "Body panels"), ("Pads & Shoes", "Brake pads & shoes")]
rows = [(lab, inc[k]["pct"]) for k, lab in pick]
rows.insert(7, ("All parts, average", it["pct"]))
lo, hi = inc["Steering Gear"]["pct"], inc["Pads & Shoes"]["pct"]
f_air, f_fuel = inc["Air Filter"]["pct"], inc["Fuel Filter"]["pct"]
flat = round(it["pct"])
frame(s, "Price revisions", f"The factory raised base prices {it['pct']:.1f}% on average. By product group it ran from "
                            f"{lo:.1f}% to {hi:.1f}%",
      "IML and IMIT base prices, September 2026 against September 2025, weighted on what we billed July 2025 – June 2026.",
      source=f"Factory base-price move on billed quantities, not a forecast: {eur_m(it['step_eur'], 2)} at last year's volumes in yen prices "
             "(our list at 6.0%: €1.96M). Groups with at least €0.5M billed.",
      page=nxt(), panel=[
          ([("Steering gear +%.1f%%. " % lo, {"bold": True}),
            (f"One flat {flat}% would lift our price about ten times more than the factory cost moved.", {})], RED),
          ([(f"Air and fuel filters +{f_air:.1f}% to +{f_fuel:.1f}%. ", {"bold": True}),
            (f"A flat {flat}% makes the most frequent service parts dearer than the cost requires.", {})], AMBER),
          ([(f"Brake pads and shoes +{hi:.1f}%. ", {"bold": True}),
            ("Independent brands compete here. The pricing revision keeps the 29 brake pad kits at today's price.", {})],
           AMBER),
          ("Purpose: a price decision per product group instead of one network percentage.", AMBER)])
pcols =[(WHITE if c == "All parts, average" else (RED if c in ("Steering gear", "Brake pads & shoes") else BAR))
         for c, _ in rows]
hbar(s, 0.25, 1.95, 9.4, 4.95, [r[0] for r in rows], [r[1] for r in rows], pcols, lambda v: f"+{v:.1f}%",
     "chart_increase", size=11, vmax=12.5, gap=35)
notes(s, f"Weighted base-price increase {it['pct']:.2f}% on the price revision basis (priced lines "
         f"{eur_m(it['priced_eur'], 2)}), worth {eur_m(it['step_eur'], 2)} on last year's quantities. By product "
         "group (groups with at least €0.5M billed): " + "; ".join(f"{d['l2']} +{d['pct']:.2f}%" for d in N["increase_l2"]) +
      ". This is a base-price move on billed quantities, not revenue, margin or demand response. The euro figure is the factory's "
      "yen base-price move on last year's quantities, converted to euro; the same 6.0% applied to our own list prices, "
      "weighted on what we billed, is €1.96M (pricing revision presentation). What ISZE does with it is in the pricing revision presentation: our "
      "list rises 5.0% on average, each part follows its own factory increase, and the 29 brake pad kits stay at today's "
      "price (decided, pricing policy paper of 2 October 2026).")

# =====================================================================================
# 10  The purposes
s = blank(prs)
frame(s, "What I use our parts classification for", "Four things I use our parts classification for, and the evidence behind each",
      "Each use is shown with real numbers earlier in this presentation.", wide=True,
      source="Figures from pages 5 to 9. Billed July 2025 – June 2026, price revision base.", page=nxt())
uses = [
    ("Explain sales down to the part",
     "Compare distributors in euro per vehicle in service, by family and part type, and trace a gap to a named part number.",
     "A gap between two markets becomes a question to one distributor about one product, not an average to argue over.",
     f"Norway against Sweden: €{gap_total:.0f} per vehicle, traced to steering units and brake pad kits (page 8)."),
    ("Set price revisions per product group",
     "Read the factory increase and our own price decisions per family, product group and part type.",
     "The factory increase ran from +%.1f%% on steering gear to +%.1f%% on brake pads. One average hides where we "
     "compete and where we do not." % (lo, hi),
     f"{it['pct']:.1f}% on average, {lo:.1f}% to {hi:.1f}% by product group (page 9)."),
    ("Compare like with like",
     "Keep an element, a housing and a kit apart inside one family.",
     f"A blended filter price of €{N['filter_roles_blended_avg']:.2f} describes neither a €{el['avg']:.0f} element nor a "
     f"€{asm['avg']:.0f} housing.",
     f"{ratio:.0f} times the price between two products that used to share one average (page 6)."),
    ("One language, with Japan's code kept",
     f"The same {L[0]} families, {L[1]} product groups and {L[2]} part types for every distributor. Japan's catalogue code "
     "stays on every part.",
     "Distributor reviews, price revisions and talks with Japan refer to the same product.",
     f"{z['pct_with_code']:.0f}% of billed euro already linked to Japan's code (pages 5 and 7)."),
]
for i, (h_, what, why, shown) in enumerate(uses):
    cx = 0.25 + i * 3.2
    rect(s, cx, 1.98, 3.05, 4.3, fill=CARD, line=BORDER, name=f"use_bg{i}")
    rect(s, cx + 0.2, 2.15, 0.42, 0.42, fill=RED, shape=MSO_SHAPE.OVAL, name=f"use_dot{i}")
    text(s, cx + 0.2, 2.15, 0.42, 0.42, str(i + 1), size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, name=f"use_n{i}")
    text(s, cx + 0.75, 2.1, 2.2, 0.55, h_, size=12, bold=True, anchor=MSO_ANCHOR.MIDDLE, name=f"use_h{i}")
    text(s, cx + 0.2, 2.8, 2.7, 3.4, [
        [("WHAT IT DOES", {"size": 8, "bold": True, "color": RED})], what,
        [("WHY IT MATTERS", {"size": 8, "bold": True, "color": RED})], why,
        [("SHOWN IN THIS PRESENTATION", {"size": 8, "bold": True, "color": RED})], [(shown, {"bold": True})]],
         size=11, spacing=[0, 3, 10, 3, 10, 3], name=f"use_t{i}")
band(s, 0.25, 6.4, 12.83, 0.5, [[("Next: ", {"bold": True}),
                                  ("link old and new part numbers, so a superseded part no longer looks like lost "
                                   "business.", {})]], size=12)
notes(s, f"Four uses, each tied to a page: 1 Norway against Sweden (page 8); 2 base-price increase by product group (page "
         f"9); 3 element against housing (page 6); 4 one structure for every market ({L[0]}/{L[1]}/{L[2]}) and Japan's code "
         "kept on every part (pages 5 and 7). Next step: interchangeability, linking superseded part numbers to their "
         "replacements once the source file is supplied.")

# =====================================================================================
# 11  How I use it from now on (no ask)
nxt()
s = blank(prs)
rect(s, 0, 0, 0.1, H, fill=RED, name="end_bar")
text(s, 0.45, 0.32, 8, 0.2, "HOW I USE THE CLASSIFICATION FROM NOW ON", size=8, bold=True, name="end_kicker")
text(s, 0.45, 1.6, 6.0, 3.2, ["From a label", "to a product.", "From a product", "to a decision."], size=36, bold=True,
     line=0.95, name="end_title")
dec = [("USE", "Our parts classification is the product language in my distributor sales reviews and in the price revisions."),
       ("KEEP", "Vehicle Parts Sales maintains it through approved, dated releases (these figures use the release of 7 October 2026). Japan's "
                "code stays on every part."),
       ("CHECK", "I take the two Nordic findings into the next distributor reviews and report what comes back.")]
for i, (k, t_) in enumerate(dec):
    yy = 1.3 + i * 1.5
    rect(s, 7.0, yy, 5.8, 1.3, fill=CARD, line=BORDER, name=f"dec_bg{i}")
    text(s, 7.25, yy, 1.3, 1.3, k, size=18, bold=True, color=RED, anchor=MSO_ANCHOR.MIDDLE, name=f"dec_k{i}")
    text(s, 8.5, yy, 4.1, 1.3, t_, size=12.5, anchor=MSO_ANCHOR.MIDDLE, name=f"dec_t{i}")
text(s, 0.45, 5.35, 6.0, 0.6, "One parts classification for sales analysis and price revisions. For information; "
                              "no decision is requested.", size=11, color=SUB, name="end_tag")
logo(s, 0.45, 6.6)
text(s, 12.55, 7.23, 0.53, 0.2, str(page[0]), size=8, color=SUB, align=PP_ALIGN.RIGHT, name="page")
notes(s, "This slide informs; it does not ask. I use our parts classification as the product language for my sales reviews and price "
         "revisions; Vehicle Parts Sales keeps it current through approved, dated releases; and I take the two "
         "Nordic findings from page 8 (steering units in Norway, brake pad kits in Sweden) into the next distributor "
         "reviews and report back. No catalogue-wide automatic price change is implied.")

prs.save(OUT)
print("saved", OUT)
