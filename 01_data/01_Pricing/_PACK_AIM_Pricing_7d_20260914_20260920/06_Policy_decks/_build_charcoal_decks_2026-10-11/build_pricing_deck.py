"""Parts price revision presentation, charcoal look (11 Oct 2026).

Content = the pricing analysis of 2 October 2026, written as a proposal to management (nothing is shown as decided). Figures come from pricing_numbers.json (recomputed from the +5% workbook with the market
layer where marked) or from the paper (reported, not recomputed). Shared wording: 'parts category', never the
internal classification name; no personal names; no factors, only margin points and euro.

Output: 06_Policy_decks/ISZE_Pricing_Revision_Management_CHARCOAL_2026-10-11.pptx
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from charcoal_lib import *  # noqa: E402,F401,F403

N = json.loads((HERE / "pricing_numbers.json").read_text(encoding="utf-8"))
import os
OUT = Path(os.environ.get("DECK_OUT") or (HERE.parent / "ISZE_Pricing_Revision_Management_CHARCOAL_2026-10-11.pptx"))
SM, REC, HELD, GA, MA = N["summary"], N["reconciliation"], N["held"], N["group_avg"], N["market_avg"]
P = N["paper"]
DR = N["dealer_response"]
MT = {m["code"]: m for m in N["market_table"]}
HB = N["held_by_market"]
BASE = REC["base"]
GRAY = rgb("7A7A7A")
SRC = "ISZE pricing analysis, 2 October 2026; +5% workbook with the market layer, version of 11 October 2026."
UMI_SVC_HELD = HB["UMI"]["service"]
UMI_SVC_BILLED = N["matrix"]["UMI"]["service"]["billed"]
HELD_MKTS = {c for c, v in HB.items() if v["service"] > 0}

prs = new_deck()
page = [0]


def nxt():
    page[0] += 1
    return page[0]


def k(v):
    return f"€{v / 1e3:,.0f}k"


def m_(v, d=2):
    return f"€{v / 1e6:.{d}f}M"


# =====================================================================================
# 1  Cover
nxt()
s = cover(prs, "ISZE  ·  VEHICLE PARTS & ACCESSORIES  ·  PARTS PRICING",
          ["Parts price revision"],
          "How our price list follows the increase from IML and IMIT, and the exceptions we propose.",
          "October 2026  ·  Draft for review",
          "Status: a proposal. Nothing in this presentation changes a price, the price list or a distributor condition.")
notes(s, "Source: the pricing analysis of 2 October 2026 and the +5% workbook with the market layer, version of 11 October "
         "2026 (filters follow the factory increase). Everything here is a proposal for management; page 12 sets out the "
         "position on three part categories that sit inside the held service parts.")

# =====================================================================================
# 2  The proposal
s = blank(prs)
frame(s, "The proposal", "Proposal: our price list follows the IML and IMIT increase, at +5.0% on average",
      "Weighted by what we billed July 2025 – June 2026: €32.6M of parts billed, 15,273 part numbers.",
      source=SRC, page=nxt(), panel_label="WHAT WE PROPOSE", panel=[
          ("Each part follows its own IML/IMIT increase, scaled so that the total is +5.0%.", RED),
          ("Prices stay at today's level where a rise would cost us business: brake pad kits (dealers already say "
           "brakes are too dear), service parts in eight markets, and body and lighting parts at the Israel D-Max "
           "distributor.", AMBER),
          (f"The market holds give up {k(REC['given_up'])}. They come on top of the pad kits and a few lost categories "
           "(page 5). The holds are recovered on repair and body parts for which we found no aftermarket alternative, "
           "so the total stays at +5.0%.", AMBER)])
rows = [["Part group", "What it covers", "Billed", "IML/IMIT increase to us", "Proposed increase on our list"],
        ["Service parts", "What a workshop buys for servicing and wear: brakes, filters, clutch, steering, fuel system",
         m_(GA["service"]["billed"], 1), f"{P['iml_imit']['service']:.1f}%", f"{GA['service']['decided'] * 100:.1f}%"],
        ["Repair parts", "What is bought after damage or failure: electrical, lighting, intake and exhaust, cabin, engine",
         m_(GA["repair"]["billed"], 1), f"{P['iml_imit']['repair']:.1f}%", f"{GA['repair']['decided'] * 100:.1f}%"],
        ["Body and collision parts", "What is replaced after a collision: panels, bumpers, glass, mirrors",
         m_(GA["body"]["billed"], 1), f"{P['iml_imit']['body']:.1f}%", f"{GA['body']['decided'] * 100:.1f}%"],
        ["All parts", "", m_(BASE, 1), f"{P['iml_imit']['all']:.1f}%", "5.0%"]]
table(s, 0.25, 2.0, 9.4, rows, [2.0, 3.9, 0.95, 1.3, 1.45], row_h=0.78, head_h=0.55, size=10.5, head_size=8.5,
      aligns=["l", "l", "r", "r", "r"], name="table_proposal")
band(s, 0.25, 5.85, 9.4, 1.0, [[("In euro: ", {"bold": True}),
                                 (f"passing on the full 6.0% would raise our list by €1.96M a year. We propose "
                                  f"{m_(SM['step_eur'])}, which is +5.0%. Service parts rise least because the price "
                                  "exceptions sit on them; repair and body parts carry the recovery.", {})]], size=11.5)
notes(s, f"IML/IMIT increase 6.0% weighted by parts billed (6.01%; 5.96% on IML's own basis, quantity times yen base price); "
         "by group service 5.5%, repair 6.6%, body and collision 7.0% (as in the pricing analysis of 2 October 2026). Proposed increase "
         "= average over all lines of the group, including lines kept at today's price, billed-weighted, from the workbook "
         f"line-by-line sheet: service {GA['service']['decided'] * 100:.2f}%, repair {GA['repair']['decided'] * 100:.2f}%, body "
         f"{GA['body']['decided'] * 100:.2f}%. Total +5.00% = €{SM['step_eur']:,.0f} on €{BASE:,.0f}. Kept at today's price "
         f"€{REC['given_up']:,.0f}; recovery €{REC['recovered']:,.0f}, {REC['pn_extra_off']:,} part numbers (the analysis says "
         "8,447: it also counts one part kept at today's price). The three groups add to the €32.6M.")

# =====================================================================================
# 3  How parts are grouped
s = blank(prs)
GC = N["group_content"]
frame(s, "How we group parts", "Every part sits in one of three groups, and the groups price differently", wide=True,
      subtitle="Used throughout this presentation. Parts billed July 2025 – June 2026.",
      source="Part groups from our new parts categories (release of 7 October 2026, presented separately) and the "
             "scheduled-service categories. Euro: +5% workbook with the market layer.",
      page=nxt())


def ex(cat, n=5):
    out = []
    for a, v in GC[cat][:n]:
        nm = "intake and exhaust" if a == "Intake Exhaust Emission" else a.lower()
        out.append(f"{nm} {m_(v, 1)}")
    return ", ".join(out)


cols = [("SERVICE PARTS", m_(GA["service"]["billed"], 1),
         "Parts that belong to a scheduled-service category: what a workshop buys for servicing and wear. Aftermarket "
         "brands sell many of them.",
         "Largest product groups: " + ex("service", 5)),
        ("REPAIR PARTS", m_(GA["repair"]["billed"], 1),
         "All other parts that are not body parts: bought after damage or failure, not at a service. Lighting sits here.",
         "Largest product groups: " + ex("repair", 5)),
        ("BODY AND COLLISION PARTS", m_(GA["body"]["billed"], 1),
         "Parts of the family Accident & Body: what is replaced after a collision.",
         "Largest product groups: panels €2.8M, bumpers €0.6M, glass €0.4M, mirrors €0.3M")]
for i, (kk, big, body_, exs) in enumerate(cols):
    x = 0.25 + i * 4.3
    rect(s, x, 2.0, 4.23, 3.75, fill=CARD, line=BORDER, name=f"grp{i}_bg")
    text(s, x + 0.25, 2.18, 3.8, 0.22, kk, size=9, bold=True, color=RED, name=f"grp{i}_k")
    text(s, x + 0.25, 2.5, 3.8, 0.6, big, size=30, bold=True, name=f"grp{i}_v")
    text(s, x + 0.25, 3.15, 3.8, 0.3, "billed", size=10, color=SUB, name=f"grp{i}_u")
    text(s, x + 0.25, 3.55, 3.75, 1.0, body_, size=12, name=f"grp{i}_b")
    text(s, x + 0.25, 4.7, 3.75, 0.95, exs, size=10.5, color=SUB, name=f"grp{i}_e")
band(s, 0.25, 5.95, 12.83, 0.9, [[("Why it matters here: ", {"bold": True}),
                                   ("the groups follow different logic. Service parts have aftermarket alternatives and "
                                    "carry most of the price exceptions; repair and body parts mostly have none we found "
                                    "and carry the recovery. A part is in exactly one group. Intake and exhaust appears "
                                    "under both service and repair because some of those parts are on the service schedule "
                                    "and some are not.", {})]], size=11.5)
notes(s, "Service = scheduled-service parts (BVP cross-reference service categories and the master service flag); body = "
         "family Accident and Body; repair = the rest, including lighting. Checked on 4 October against the approved release "
         "2026-10-02: 0 of 15,273 parts change between groups. Product group euro are from the parts category release of 7 October 2026 "
         "joined to the +5% workbook (each part counted once, in its group). If the parts-categories presentation is shown "
         "first, this slide is a reminder; if not, this is the only place the grouping is explained.")

# =====================================================================================
# 3  What IML and IMIT changed
s = blank(prs)
im = P["iml_imit"]
frame(s, "What IML and IMIT changed", "IML and IMIT raised their prices to us by 6.0% in September 2026, about twice the "
                                      "3.2% of a year earlier",
      "Average increase to ISZE, September 2026 against September 2025, in yen, weighted by parts billed.",
      source="IML and IMIT base prices per part (Sept 2025, Sept 2026), SAP parts billing July 2025 – June 2026; analysis "
             "section 2. Japan and Thailand shares re-checked in the +5% workbook (6.19% and 6.34%).",
      page=nxt(), panel=[
          ("Our price is built from IML's or IMIT's yen base price, the exchange rate, our purchase discount and a class "
           "margin set by IML. Nothing about competition enters that formula.", RED),
          ("Since 5 January 2026 the purchase discount on Japan-sourced parts fell from 38.0% to 32.7%. The weaker yen "
           "largely offsets it.", AMBER),
          ("From the factory move alone, our margin falls about 0.5 points, because our list rises less than our cost. "
           "The exchange rate and the purchase discount are held where they are in that figure.", AMBER)])
cats = ["All parts billed", "Service parts", "Repair parts", "Body and collision parts", "Supplied from Japan (IML)",
        "Supplied from Thailand (IMIT)"]
vals = [im["all"], im["service"], im["repair"], im["body"], im["japan"], im["thailand"]]
hbar(s, 0.25, 2.0, 5.9, 3.6, cats, vals, [WHITE] + [BAR] * 5, lambda v: f"{v:.1f}%", "chart_factory", size=11.5, vmax=8.5,
     gap=40)
kpi(s, 6.45, 2.1, 3.1, "3.2%", "the previous revision, September 2025 (weighted by quantity billed)", big_size=30)
kpi(s, 6.45, 3.55, 3.1, "5.96%", "same September 2026 rise, IML's own weighting — not last year", big_size=30)
band(s, 0.25, 5.85, 9.4, 1.0, [[("Parts billed: ", {"bold": True}),
                                 (f"service €{im['billed_service_m']}M, repair €{im['billed_repair_m']}M, body and "
                                  f"collision €{im['billed_body_m']}M. From Japan €15.9M, from Thailand €15.1M. 82 part "
                                  "numbers (€1.6M) carry no source of supply and average 1.0%.", {})]], size=11.5)
notes(s, "6.0% = weighted by parts billed (6.01%); on IML's own basis (quantity times yen base price) 5.96%. Service parts "
         "5.5%, repair 6.6%, body and collision 7.0% (as in the pricing analysis of 2 October 2026). The previous revision, September "
         "2025, was about 3.2% weighted by quantity billed and fed the April 2026 list. Purchase terms and exchange rate: "
         "supplier notice of 22 December 2025 and the corporate rate notifications. The exchange rate moves the euro "
         "price and the euro gross profit; it never moves the margin percentage.")

# =====================================================================================
# 5  From 6.0% to +5%
s = blank(prs)
full, scaled = SM["full_factory_eur"], SM["scaled_eur"]
wk = P["waterfall_to_5pct_k"]
steps = [("Full IML/IMIT increase", full, "total", BAR),
         ("Pass on 90.5% of each part's increase", scaled - full, "delta", GRAY),
         ("Pad kits stay", wk["pad_kits"] * 1e3, "delta", GRAY),
         ("Lost categories stay", wk["categories_lost"] * 1e3, "delta", GRAY),
         ("Web-shop extra", wk["uk_web_shops"] * 1e3, "delta", GREEN),
         ("Proposed: +5.00%", SM["step_eur"], "total", RED)]
frame(s, "From 6.0% to +5%", "Passing on 90.5% of each part's own increase, with a few exceptions, gives +5.00% in total",
      "From the full IML/IMIT increase to our proposed list increase, on what we billed July 2025 – June 2026, € a year.",
      source=SRC + " Pad kits, lost categories and web-shop extra from analysis section 2; totals re-checked in the workbook.",
      page=nxt(), panel=[
          ("The same 90.5% applies to every part, so parts IML and IMIT raised more go up more and parts with no "
           "increase stay flat (180 part numbers). 90.5% is the share that, after the exceptions, lands on +5.00%.", RED),
          ("The 29 brake pad kits stay at today's price (€109k): they compete with aftermarket brands, the main front "
           "kit would otherwise have risen about 17%, and eight distributors we spoke to this summer said brake parts "
           "are too expensive.", AMBER),
          (f"Categories a distributor already loses also stay flat (5 parts, €56k; three of them filters). A small extra applies where UK web shops sell "
           f"dearer. A typical part rises 6.4%; {SM['parts_at_zero']} parts ({m_(SM['eur_at_zero'])} billed) stay at "
           "today's price.", AMBER)])
waterfall(s, 0.25, 2.0, 9.4, 4.0,
          steps,
          lambda v, kind: (f"€{v / 1e6:.2f}M" if kind == "total" else (f"+€{v / 1e3:.0f}k" if v > 0 else f"−€{abs(v) / 1e3:.0f}k")),
          "chart_waterfall1", size=10, vmax=2.3e6)
band(s, 0.25, 6.2, 9.4, 0.65, [[("Passing on the full 6.0% would raise our list by €1.96M. ", {}),
                                 ("The +5.00% is €1,629,793 on €32,595,853 of parts billed.", {"bold": True})]], size=12)
notes(s, f"Full IML/IMIT increase on every part: €{full:,.0f} (6.0% of parts billed). 90.5% of each part's own increase "
         f"(scaling {SM['k']:.4f}) = €{scaled:,.0f}. Pad kits -€109k, categories where the distributor sells under 45% of "
         f"what its vehicles need -€56k, small extra where UK web shops sell dearer +€21k; result €{SM['step_eur']:,.0f}. "
         f"Median part +6.4% (workbook {SM['median_move'] * 100:.2f}%), 90th percentile {SM['p90_move'] * 100:.1f}%, largest "
         f"single increase {SM['max_move'] * 100:.0f}% (99 parts above 15%, reviewed one by one). Class margin falls "
         f"{abs(SM['margin_pts_proposal']) * 100:.1f} points.")

# =====================================================================================
# 6  Where we increase, and by how much
s = blank(prs)
MX = N["matrix"]
order = ["ITUK", "IUK", "UTI", "GERMANY", "UMI", "BELGIUM", "PORTUGAL", "NORWAY", "SWEDEN", "IRELAND", "CYPRUS",
         "HUNGARY", "MALTA"]
names = {"ITUK": "Isuzu Truck UK", "IUK": "Isuzu UK (D-Max)", "UTI": "Israel trucks distributor", "GERMANY": "Germany",
         "UMI": "Israel D-Max distributor", "BELGIUM": "Belgium", "PORTUGAL": "Portugal", "NORWAY": "Norway",
         "SWEDEN": "Sweden", "IRELAND": "Ireland", "CYPRUS": "Cyprus", "HUNGARY": "Hungary", "MALTA": "Malta"}
others = ["UKRAINE", "GREECE", "FINLAND", "ROMANIA", "DENMARK", "ICELAND", "PALESTINE"]
left_out = ["ARMENIA", "KAZAKHSTAN"]
assert set(order) | set(others) | set(left_out) == set(MX), set(MX) ^ (set(order) | set(others) | set(left_out))


def agg(codes):
    out, tot_b, tot_i = {}, 0.0, 0.0
    for gk in ("service", "repair", "body"):
        b_ = sum(MX[c][gk]["billed"] for c in codes if gk in MX[c])
        i_ = sum(MX[c][gk]["billed"] * MX[c][gk]["decided"] for c in codes if gk in MX[c])
        out[gk] = (b_, i_ / b_ if b_ else None)
        tot_b += b_
        tot_i += i_
    out["all"] = (tot_b, tot_i / tot_b)
    return out


def pct(v):
    return "–" if v is None else ("Today's price" if v < 0.0005 else f"{v * 100:.1f}%")


rows = [["Market", "Parts billed", "Service parts", "Repair parts", "Body and collision parts", "All parts"]]
colors = {}
lines = [(names[c], agg([c])) for c in order] + [("Seven other markets", agg(others)),
                                                  ("Armenia, Kazakhstan: own increase only", agg(left_out)),
                                                  ("All markets", agg(list(MX)))]
for i, (nm, a) in enumerate(lines, start=1):
    code = ([c for c in order if names[c] == nm] or [None])[0]
    svc_held = code in HELD_MKTS
    rows.append([nm, m_(a["all"][0]), (f"{a['service'][1] * 100:.1f}%" if svc_held else pct(a["service"][1])),
                 pct(a["repair"][1]), pct(a["body"][1]), pct(a["all"][1])])
    for j, gk in enumerate(("service", "repair", "body"), start=2):
        v = a[gk][1]
        if (v is not None and v < 0.0005) or (gk == "service" and svc_held):
            colors[(i, j)] = AMBER
frame(s, "Where we increase, and by how much",
      "Where our price list rises, and by how much: market by market and by part group", wide=True,
      subtitle="Proposed average increase per market and part group. Amber: service parts held at today's price, "
               "filters excepted.",
      source="ISZE pricing analysis and +5% workbook (11 Oct 2026). Billed-weighted, including lines kept at today's price. "
             "Lighting is a repair part.",
      page=nxt())
table(s, 0.25, 1.95, 12.83, rows, [3.4, 1.4, 1.7, 1.7, 2.2, 1.4], row_h=0.285, head_h=0.45, size=10, head_size=8.5,
      aligns=["l", "r", "r", "r", "r", "r"], colors=colors, name="table_matrix")
notes(s, "One view of where the list rises and by how much (it replaces the earlier market table and part-group page). Each "
         "cell is the billed-weighted average increase of that group in that market after the proposed exceptions (holds and "
         "recovery). Amber service cells = service parts kept at today's price in that market (eight markets), except "
         "filters, which follow the factory increase, so those cells are above zero. "
         "In the Israel D-Max distributor row the repair and body figures are lower because lighting, body and collision "
         "parts are kept at today's price. 'Seven other markets' = Ukraine, Greece, Finland, Romania, Denmark, Iceland, "
         "Palestine. Armenia and Kazakhstan are left out of the market decisions and take their own increase only.")

# =====================================================================================
# 7  Where service parts stay at today's price
s = blank(prs)
um = HB["UMI"]
items = [("Isuzu UK (D-Max): service parts", HB["IUK"]["service"], RED),
         ("Israel D-Max distributor: service parts", um["service"], BAR),
         ("Germany: service parts", HB["GERMANY"]["service"], BAR),
         ("Belgium: service parts", HB["BELGIUM"]["service"], BAR),
         ("Norway: service parts", HB["NORWAY"]["service"], BAR),
         ("Israel D-Max distributor: body and collision", um["body_collision"], AMBER),
         ("Cyprus: service parts", HB["CYPRUS"]["service"], BAR),
         ("Israel trucks distributor: lighting", HB["UTI"]["lighting"], AMBER),
         ("Hungary: service parts", HB["HUNGARY"]["service"], BAR),
         ("Israel D-Max distributor: lighting", um["lighting"], AMBER),
         ("Malta: service parts", HB["MALTA"]["service"], BAR)]
frame(s, "Where prices stay", f"We propose to keep prices at today's level where a rise would cost us business. This gives up {k(REC['given_up'])}",
      "Increase not taken, € a year, by market and part group. Amber: the Israel insurance rule (page 10).",
      source=SRC + " Euro per market and line from the workbook (7,396 part and market lines still held). Distributor "
             "reviews July–August 2026.",
      page=nxt())
right_panel(s, [
          ("Brake parts are the loudest complaint: eight distributors this summer said they are too expensive. "
           "Pad kits stay flat network-wide. Discs stay flat in the eight service-hold markets, which are chosen on "
           "service share and fleet, not on who complained (page 12).", RED),
          ("Service parts also stay flat when vehicles we do not count buy there, dealers reacted after April, "
           "or the fleet is flat while our service share is below 28%. Filters are the exception: they follow the "
           "factory increase.", AMBER),
          ("Israel body, collision and lighting follow the insurance rule (page 10). A hold in one market is a "
           "distributor condition on that category.", AMBER)],
             size=10.5)
hbar(s, 0.25, 2.0, 9.4, 4.85, [i[0] for i in items], [i[1] for i in items], [i[2] for i in items], k, "chart_held",
     size=10.5, vmax=185e3, gap=35)
notes(s, f"Total given up €{REC['given_up']:,.0f}. Twenty-one markets were read one by one on what each buys, how its fleet "
         "moves, how much of its service work we win (service share), what it pays against list and what dealers and "
         "distributors say. Service parts at Isuzu UK (D-Max) alone are the largest single item. The Israel D-Max lighting "
         "proposal (€4,435) is included. Brake complaint register from July–August 2026 reviews: Isuzu UK pickup "
         "(6 Aug), Isuzu Truck UK (18 Aug), Israel D-Max (12 Aug), Germany (5 Aug), Belgium (12 Aug), Portugal "
         "(29 Jul), Hungary (11 Aug), Iceland (25 Aug). The written register names these eight; it does not record "
         "how many distributors were asked. Armenia and Kazakhstan are left out of "
         "the market decisions.")

# =====================================================================================
# 8  Recovery
s = blank(prs)
tw = P["three_ways_k"]
frame(s, f"How the {k(REC['given_up'])} is recovered",
      f"We keep {k(REC['given_up'])} of increase off some parts. To stay at +5.00% overall, we put that euro back elsewhere",
      "Three options, all still €1,629,793. We propose the middle one: only repair and body with no aftermarket rival.",
      source=SRC + " Proposed option from the workbook; the other two as calculated on 2 October, before filters were "
             "released from the hold.",
      page=nxt(), panel=[
          ("Service parts (filters, pads, discs, clutch) already have aftermarket brands. We put no extra on them. "
           "Spreading the extra over every remaining part would put €137k back on service.", RED),
          ("Outside shop prices cover only 21% of parts billed, so weighting the extra by those prices is a guess, "
           "not a measurement.", AMBER),
          ("Spreading over every remaining part also hits the biggest factory rises hardest: 56 parts would hit the "
           "ceiling (own increase + 5 points). Under our proposal, only 5 parts hit that ceiling.", AMBER)])
text(s, 0.25, 1.98, 4.6, 0.3, "The total stays +5.00%, € million", size=11, bold=True)
waterfall(s, 0.25, 2.3, 4.55, 4.55,
          # own_total is the proposed +5.00% euro (€1.63M), not the full IML/IMIT increase (€1.96M).
          [("Proposed list increase (+5.00%)", REC["own_total"], "total", BAR),
           ("Kept at today's price", -REC["given_up"], "delta", AMBER),
           ("Ceiling: 5 parts", -REC["ceiling_cut"], "delta", GRAY),
           ("Put back on repair and body", REC["recovered"], "delta", GREEN),
           ("Result: still +5.00%", REC["own_total"], "total", RED)],
          lambda v, kind: (f"€{v / 1e6:.2f}M" if kind == "total" else (f"+€{v / 1e3:.0f}k" if v > 0 else f"−€{abs(v) / 1e3:.0f}k")),
          "chart_waterfall2", size=9.5, vmax=2.0e6, gap=30)
text(s, 5.05, 1.98, 4.6, 0.3, "Where the extra lands, € thousand", size=11, bold=True)
clustered(s, 5.05, 2.3, 4.6, 4.55, ["Service", "Repair", "Body and collision"],
          [("Spread over every remaining part",
            [tw["a_spread"]["service"], tw["a_spread"]["repair"], tw["a_spread"]["body"]], BAR),
           ("Proposed: only repair and body, no rival found",
            [REC["rec_service"] / 1e3, REC["rec_repair_off"] / 1e3, REC["rec_body_off"] / 1e3], RED),
           ("Weighted by outside shop prices",
            [tw["c_weighted"]["service"], tw["c_weighted"]["repair"], tw["c_weighted"]["body"]], GRAY)],
          lambda v: f"{v:.0f}", "chart_ways", size=9.5, vmax=300, gap=50, overlap=-8)
notes(s, f"Kept at today's price -€{REC['given_up']:,.0f}; ceiling cut -€{REC['ceiling_cut']:,.0f} (5 parts that would rise "
         f"more than 5 points above their own IML/IMIT increase; the cut is recovered as well); recovery +€{REC['recovered']:,.0f}: "
         f"repair €{REC['rec_repair_off']:,.0f}, body €{REC['rec_body_off']:,.0f}, service nil. Extra "
         f"{REC['t_off'] * 100:.2f} points on {REC['pn_extra_off']:,} parts. No aftermarket rival found = no confirmed or "
         "likely competitor number, no aftermarket price observed, no cheaper Best Value alternative, not in the "
         "competitive-parts family, and not a category the distributor is measured to lose. Mostly this means none was "
         "found, not that none exists (page 11).")

# =====================================================================================
# 9  Isuzu UK exemption
s = blank(prs)
sel = ["IUK", "ITUK", "UTI", "GERMANY", "UMI", "BELGIUM", "PORTUGAL", "NORWAY"]
short = {"IUK": "Isuzu UK (D-Max)", "ITUK": "Isuzu Truck UK", "UTI": "Israel trucks", "GERMANY": "Germany",
         "UMI": "Israel D-Max", "BELGIUM": "Belgium", "PORTUGAL": "Portugal", "NORWAY": "Norway"}
frame(s, "For decision", "Isuzu UK (D-Max) bought less after the April 2026 rise. Should it also carry the recovery extra?",
      "Average list increase by market, %: before the holds, as proposed now, and if UK pickup is left out of the extra.",
      source="Sales to dealer files, April–July 2025 against 2026 (analysis sections 4 and 7); averages from the +5% "
             "workbook (11 October).",
      page=nxt(), panel=[
          (f"From sales to dealer: when a part rose 1% more than similar parts, dealers bought about 1% fewer "
           f"({DR['iuk_beta']:.2f} ± {DR['iuk_ci95']:.2f}). Dealer pieces fell "
           f"{abs(DR['iuk_units_change']) * 100:.1f}% against the same months of 2025.".replace("-", "−"), RED),
          (f"The recovery extra puts {k(REC['rec_iuk_off'])} on its repair and body parts. Leaving it out moves that "
           f"euro to the other markets (+{REC['t_on'] * 100:.1f} points instead of +{REC['t_off'] * 100:.1f}). "
           "The network total stays €1,629,793.", AMBER),
          ("Ask: leave Isuzu UK (D-Max) out of the recovery extra, or not. We suggest leaving it out.", AMBER)])
clustered(s, 0.25, 2.0, 9.4, 4.85, [short[c] for c in sel],
          [("Before the holds", [MA[c]["own"] * 100 for c in sel], BAR),
           ("Proposal now (UK pickup carries extra)", [MA[c]["decided"] * 100 for c in sel], RED),
           ("If UK pickup is left out of the extra", [MA[c]["exempt"] * 100 for c in sel], GREEN)],
          lambda v: f"{v:.1f}", "chart_exempt", size=10, vmax=9, gap=45, overlap=-5, label_size=9.5)
notes(s, f"Sales to dealer response = percentage change in dealer purchases for +1% on our price within the same part "
         f"family, measured on the April 2026 list change (price sensitivity / elasticity — the plain sentence is enough "
         f"for the slide). Isuzu UK (D-Max) {DR['iuk_beta']:.2f} (standard error {DR['iuk_se']:.2f}, 95% interval "
         f"±{DR['iuk_ci95']:.2f}). Pooled over Isuzu Truck UK, Isuzu UK (D-Max), Ireland and Portugal: "
         f"{DR['pooled']['beta_dlp']:.2f} (standard error {DR['pooled']['se_dlp']:.2f}), statistically indistinguishable "
         "from no reaction; used only for volume scenarios. Before the market holds the €1.63M becomes about "
         f"€{SM['revenue_central'] / 1e6:.2f}M if the pooled reaction applies, and €{SM['revenue_stress'] / 1e6:.2f}M in a "
         f"pessimistic case (a stress test, not a forecast). With the exemption Isuzu UK (D-Max) averages "
         f"{MA['IUK']['exempt'] * 100:.1f}% instead of {MA['IUK']['decided'] * 100:.1f}%.")

# =====================================================================================
# 10  Israel
s = blank(prs)
il = P["israel"]
frame(s, "Israel", "Israel: two distributors, two different problems", wide=True,
      subtitle="Each proposal follows the reason we lose sales at that distributor.",
      source="Analysis sections 9 and 10: Israeli motor policy wordings for vehicles up to 3.5 tonnes; distributor "
             "correspondence and back-order lists, weeks 2–40 of 2026; SAP parts billing. Figures as in the pricing analysis of 2 October 2026.",
      page=nxt())
rect(s, 0.25, 1.98, 6.3, 4.1, fill=CARD, line=BORDER, name="isr_L_bg")
text(s, 0.5, 2.12, 5.8, 0.22, "ISRAEL D-MAX DISTRIBUTOR: INSURANCE TOTAL-LOSS RULE", size=8.5, bold=True, color=RED)
text(s, 0.5, 2.45, 5.8, 0.65, f"{il['total_loss_pct']}%", size=38, bold=True, color=AMBER)
text(s, 0.5, 3.25, 5.8, 0.55, "of pre-accident value is the total-loss limit in Israel; insurers may settle as a total "
                              "loss from 50 to 55%. The repair estimate is built from our parts list prices.", size=11.5, bold=True)
text(s, 0.5, 4.0, 5.8, 2.0, [
    "Why we keep the list flat here: the insurer's estimate uses our list prices. A higher body or lighting line can tip "
    "a repairable D-Max over the 50–60% band. Then we lose the whole repair, not only that part.",
    f"So we propose to keep body, collision and lighting at today's price (€{il['dmax_body_light_given_up_k']}k of "
    "increase given up). Verified in the policy wordings up to 3.5 tonnes, which covers the D-Max.",
    f"Separately, its service parts also stay at today's price ({k(UMI_SVC_HELD)}, filters excepted) — same market "
    "hold as the other seven service-hold markets (page 7), not the insurance rule."],
     size=10.5, color=SUB, spacing=6)
rect(s, 6.75, 1.98, 6.33, 4.1, fill=CARD, line=BORDER, name="isr_R_bg")
text(s, 7.0, 2.12, 5.8, 0.22, "ISRAEL TRUCKS DISTRIBUTOR: DELIVERY TIMES, NOT PRICE", size=8.5, bold=True, color=RED)
text(s, 7.0, 2.45, 5.8, 0.65, f"{il['panels_change_pct']:.1f}%".replace("-", "−"), size=38, bold=True, color=AMBER)
text(s, 7.0, 3.25, 5.8, 0.55, f"truck body panel billing January–August 2026 against 2025 (€{il['panels_billed_jan_aug_2025'] / 1e3:.0f}k "
                              f"to €{il['panels_billed_jan_aug_2026'] / 1e3:.0f}k), while units rose.", size=11.5, bold=True)
text(s, 7.0, 4.1, 5.8, 1.9, [
    f"This distributor loses panel sales mainly to back orders of {il['backorder_weeks']} weeks (median "
    f"{il['backorder_median_weeks']}), not to price. Its panels take the normal increase (€{il['panels_increase_kept_eur']:,} "
    "of increase kept). The answer is availability: a stocking plan for new N-Series (P700) panels against the "
    "distributor's forecast.",
    f"Lighting parts stay at today's price (€{il['trucks_lighting_given_up_k']}k), on the same insurance rule. For vehicles "
    "heavier than 3.5 tonnes the clause was not found, so this exposure is unverified."], size=11, color=SUB, spacing=8)
band(s, 0.25, 6.3, 12.83, 0.55, [[("In both cases the proposal follows the evidence on why we lose sales: ", {}),
                                   ("an insurer's limit at one distributor, delivery times at the other.", {"bold": True})]], size=12)
notes(s, "The two distributors are always shown separately. A vehicle is declared a "
         "total loss at 60% of pre-accident value; the insurer may settle as a constructive total loss from 50-55% (two "
         "policy readings differ). Verified for vehicles up to 3.5 tonnes (the D-Max). The D-Max distributor also keeps "
         f"service parts at today's price ({k(UMI_SVC_HELD)}), with the leasing share still open (page 13). Panels: back orders 4 to 16 "
         "weeks, median 13; open panel lines averaged 22 a week in weeks 2-13, 29 in weeks 14-26 and 19 in weeks 27-40. Part "
         "of the euro drop is a single F-Series grille from a 2025 stock build. On the panels bought in both periods units "
         "rose 9.5% and euro fell 5.3%. Limits: lost jobs are not visible in our data; only the distributor can supply them.")

# =====================================================================================
# 11  Outside price evidence
s = blank(prs)
ev = P["evidence_pct"]
op = P["outside_prices"]
frame(s, "Outside price evidence",
      "We do not have enough outside prices to set each part one by one. What we have mostly says where to hold",
      "Share of parts billed with each kind of evidence. Aftermarket shops mostly cheaper; outside genuine mostly dearer.",
      source="Analysis section 8: web-shop and brand prices as of 2 October 2026 (VAT removed, median per part). "
             "Figures as in the pricing analysis of 2 October 2026.",
      page=nxt(), panel=[
          ("“No aftermarket rival found” mostly means we did not find one — not that none exists. Only 294 parts have "
           "any competitor evidence at all.", RED),
          (f"Where we do have aftermarket shop prices, they sit at about {op['aftermarket_median_index']:.2f}× the "
           f"dealer price we build from our list (median of {op['aftermarket_parts']} parts). That points to parts to "
           "keep at today's price, not parts to raise.", AMBER),
          ("We do not have real distributor or dealer resale prices. The dealer price used for the comparison is "
           "built from our list on a provisional basis.", AMBER)])
cats = [e[0] for e in ev]
vals = [e[1] for e in ev]
cols = [GREEN2, GREEN2, BAR, BAR, RED, BAR, RED]
hbar(s, 0.25, 2.2, 6.2, 4.0, cats, vals, cols, lambda v: f"{v:.1f}%", "chart_evidence", size=10.5, vmax=118, gap=40)
kpi(s, 6.75, 2.3, 2.9, f"{op['aftermarket_median_index']:.2f}×",
    f"aftermarket shop ÷ dealer price we build from our list, median of {op['aftermarket_parts']} parts", big_size=28)
kpi(s, 6.75, 3.95, 2.9, f"{op['genuine_outside_median_index']:.2f}×",
    f"genuine Isuzu sold outside our network, median of {op['genuine_outside_parts']:,} parts; "
    f"{op['genuine_outside_main_source']:,} rest on one exporter", big_size=28)
text(s, 0.25, 6.3, 9.4, 0.5, "Green: solid evidence. Grey: partial. Red: too thin to prove there is no rival.", size=10, color=SUB)
notes(s, "Index = outside price without VAT divided by the dealer price we build from our list; below 1.0 the outside "
         "seller is cheaper. That built dealer price is provisional (set 2 October 2026); September papers used a "
         "different one, so ratios are not comparable with September. 182 aftermarket parts (€6.0M billed) sit below 0.8; "
         "only 46 parts (€0.45M) have a rival dearer than us. 71% of parts (46% of parts billed) pass the 'no aftermarket "
         "rival found' test. Body parts look almost entirely without a rival, but non-genuine body parts have not "
         "been searched: a price check on pattern parts for the top 50 body parts is a next action.")

# =====================================================================================
# 12  Three part categories inside the held service parts
s = blank(prs)
frame(s, "Held service parts: three categories", "Inside the held service parts, filters follow the factory increase and brake discs stay at today's price",
      wide=True,
      subtitle="Service parts are kept at today's price in eight markets. Three categories inside them were looked at "
               "separately. The figures in this presentation include these positions.",
      source="Euro per category from the workbook (what each hold is worth; 7,396 part and market lines still held, "
             f"{k(REC['given_up'])}). Filters: {k(HELD['filters_eur'])}, released from the hold.",
      page=nxt())
rows = [["Part category", "Proposal", "Why", "In the figures"],
        ["Filters", "Follow the factory (IML/IMIT) increase, like other parts.",
         "Filters are not a critical price point, so they follow the supplier's increase like other parts. Three filter "
         "lines a distributor already loses stay flat (page 5).",
         f"{k(HELD['filters_eur'])} is no longer held. The held total is {k(REC['given_up'])} instead of "
         f"{k(HELD['all_if_held_eur'])}, and the extra on repair and body parts falls from +{REC['t_off_2oct'] * 100:.1f} to "
         f"+{REC['t_off'] * 100:.1f} points."],
        ["Brake discs and drums", "Stay at today's price in the eight markets, like the 29 pad kits.",
         "Aftermarket alternatives, and brake parts were the loudest complaint in this summer's distributor reviews, "
         "so discs follow the same logic as the pad kits (Germany already quotes a rotor at about €80 against about "
         "€100 through us).",
         f"{k(HELD['discs_drums_eur'])}, held, inside the {k(REC['given_up'])}."],
        ["Intake, exhaust and emission parts", "Open: we have no proposal yet. For decision (page 13).",
         "Particulate filter assemblies, turbochargers, EGR valves and exhaust pipes. Held in the figures until decided.",
         f"{k(HELD['intake_exhaust_emission_eur'])}, held, inside the {k(REC['given_up'])}."]]
colors = {(1, 1): AMBER, (2, 1): AMBER, (3, 1): AMBER}
table(s, 0.25, 2.15, 12.83, rows, [2.3, 3.0, 4.2, 3.3], row_h=1.12, head_h=0.38, size=10.5, head_size=8.5,
      aligns=["l", "l", "l", "l"], colors=colors, name="table_changes")
band(s, 0.25, 6.05, 12.83, 0.75, [[("What does not change: ", {"bold": True}),
                                  ("the +5.0% target; the 29 pad kits at today's price (€109k, main front kit would "
                                   "otherwise rise about 17%); the Israel proposals; and the recovery on repair and body "
                                   "parts with no alternative found.", {})]], size=11)
notes(s, f"Worth of each hold from the workbook's table 'What each hold is worth': filters €{HELD['filters_eur']:,.0f} (now "
         f"released), brake discs and drums €{HELD['discs_drums_eur']:,.0f}, intake, exhaust and emission "
         f"€{HELD['intake_exhaust_emission_eur']:,.0f}. All holds if filters were held as well: €{HELD['all_if_held_eur']:,.0f}; "
         f"now €{HELD['given_up_eur']:,.0f}. With filters released the extra falls from "
         f"{REC['t_off_2oct'] * 100:.2f} to {REC['t_off'] * 100:.2f} points and the recovery from €396,568 to "
         f"€{REC['recovered']:,.0f}; the total stays €{SM['step_eur']:,.0f} (+5.00%). The filter and "
         "brake-disc positions were settled on 11 October; to management they are proposals. Pad-kit rationale: the pricing analysis of 2 October, section 4; "
         "summer brake complaints as on page 7. The comparison of three recovery options on page 8 for the two options "
         "not proposed is as calculated on 2 October, with filters held.")

# =====================================================================================
# 13  Decisions and next actions
s = blank(prs)
tx, ns = P["terms_outside_list"], P["n_series"]
frame(s, "Decisions and next actions", "Two points need a decision from management, and one more is open",
      "Two further items sit outside this revision.",
      source=SRC + " Terms outside the list: calendar 2025 order lines at the 2025 list (analysis section 11).",
      page=nxt(), panel_label="NEXT ACTIONS", panel=[
          ("Decide the Isuzu UK (D-Max) exemption and the intake, exhaust and emission position.", RED),
          ("Set up the exceptions and the recovery as distributor conditions per parts category (not built yet). "
           "Agree the N-Series panel stocking plan.", AMBER),
          ("Before the body share of the recovery is fixed: price check on non-genuine body parts (top 50), and confirm "
           "the reference dealer price basis.", AMBER),
          ("Take discounts and surcharges into the distributor negotiations as a separate item. Prepare first prices for "
           "the new N-Series parts.", AMBER)])
rows = [["Point", "Status", "What is open", "At stake"],
        ["Isuzu UK (D-Max) exemption", "For decision", "Its repair and body parts keep their own increase, without a share "
                                                    "of the recovery. We suggest exempting it (page 9).",
         f"{k(REC['rec_iuk_off'])} moves between markets."],
        ["Intake, exhaust and emission parts", "For decision", "Whether these parts stay at today's price (page 12).",
         k(HELD["intake_exhaust_emission_eur"])],
        ["Israel D-Max distributor: leasing share", "Open",
         "If leasing fleets are most of its volume, its service parts could take the normal increase. The share is not "
         "being requested now.",
         f"{k(UMI_SVC_HELD)} of increase kept off, on {m_(UMI_SVC_BILLED)} of service parts billed."],
        ["Discounts and surcharges outside the list", "Separate item",
         "Stock-order discount, distributors paying below list, surcharge on urgent orders. A commercial term per "
         "distributor, not part of the +5%.",
         f"Halving each market's gap to list on stock orders €{tx['halve_gap_stock_k']}k; 1 point less stock-order "
         f"discount €{tx['one_point_stock_discount_k']}k; urgent surcharge +1 point €{tx['urgent_plus1_k']}k."],
        ["New N-Series (P700) first prices", "Next price list",
         f"{ns['part_numbers']} part numbers hardly billed yet ({ns['in_base']} parts, €{ns['in_base_eur']} in this "
         "year's base). They need a well-set first price, not an increase.", "None this year."]]
colors = {(1, 1): AMBER, (2, 1): AMBER, (3, 1): SUB, (4, 1): SUB, (5, 1): SUB}
table(s, 0.25, 1.95, 9.4, rows, [2.3, 1.3, 3.5, 2.6], row_h=0.88, head_h=0.38, size=9.5, head_size=8.5,
      aligns=["l", "l", "l", "l"], colors=colors, name="table_open")
notes(s, "Open in this revision: the Israel D-Max distributor leasing share (leased double cabs must use genuine parts in the "
         "first two years and run the highest mileage of the pickup markets), the Isuzu UK (D-Max) exemption and the "
         "intake, exhaust and emission position. Discounts and surcharges are valued on calendar-2025 order lines at the "
         "2025 list; Armenia and Kazakhstan left out. New N-Series: 826 part numbers on the provisional new-parts list, 135 "
         "ever billed (€0.25M), 14 in this year's base (€660).")

prs.save(OUT)
print("saved", OUT)
