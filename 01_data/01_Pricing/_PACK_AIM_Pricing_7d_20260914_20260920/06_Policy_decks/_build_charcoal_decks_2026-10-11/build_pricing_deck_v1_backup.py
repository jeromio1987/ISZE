"""Parts price revision presentation, charcoal look (11 Oct 2026).

Content = the pricing policy paper of 2 October 2026 (decided positions), with the two changes decided on 11 October
flagged on their own page. Figures come from pricing_numbers.json (recomputed from the +5% workbook with the market
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
OUT = HERE.parent / "ISZE_Pricing_Revision_Management_CHARCOAL_2026-10-11.pptx"
SM, REC, HELD, GA, MA = N["summary"], N["reconciliation"], N["held"], N["group_avg"], N["market_avg"]
P = N["paper"]
DR = N["dealer_response"]
MT = {m["code"]: m for m in N["market_table"]}
HB = N["held_by_market"]
BASE = REC["base"]
GRAY = rgb("7A7A7A")
SRC = "Pricing policy paper, 2 October 2026; +5% workbook with the market layer (4 October 2026), reproduced on 11 October."

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
          "October 2026  ·  Draft for review  ·  Decisions recorded up to 2 October 2026; changes since on page 13",
          "Status: a proposal on paper. Nothing in this presentation changes a price, the price list or a distributor "
          "condition.")
notes(s, "Source: pricing policy paper of 2 October 2026 (replaces the papers of 17 and 19 September and the earlier "
         "management decks) and the +5% workbook with the market layer. Two changes decided on 11 October are on page 13; "
         "the euro figures elsewhere are those of the paper.")

# =====================================================================================
# 2  Summary
s = blank(prs)
frame(s, "Summary", "IML and IMIT raise their prices by 6.0%. Our price list rises by +5.0%, with exceptions where a rise "
                    "would cost us business",
      "Weighted by what we billed July 2025 – June 2026: €32.6M of parts billed, 15,273 part numbers.",
      source=SRC, page=nxt(), panel=[
          ("Each part follows its own IML/IMIT increase, so parts IML and IMIT raised more go up more.", RED),
          ("Where a rise would cost us business (brake pads, service parts in eight markets, body and lighting in "
           "Israel) the price stays where it is today.", AMBER),
          ("New: prices can now be set per parts category (filters, brake pads, body panels, lighting). Every exception "
           "here was made that way.", AMBER)])
cards = [("IML/IMIT INCREASE TO US", "6.0%", "average, weighted by parts billed (service 5.5%, repair 6.6%, body and "
                                           "collision 7.0%)", TXT),
         ("OUR PRICE LIST", "+5.0%", f"{m_(SM['step_eur'])} a year on {m_(BASE, 1)} of parts billed", TXT),
         ("KEPT AT TODAY'S PRICE", k(REC["given_up"]), "service parts in eight markets; body and lighting in Israel", AMBER),
         ("RECOVERED ELSEWHERE", f"+{REC['t_off'] * 100:.1f} pts",
          f"on {REC['pn_extra_off']:,} repair and body parts with no aftermarket alternative found", RED)]
for i, (kk, big, body, col) in enumerate(cards):
    card(s, 0.25 + i * 2.38, 2.0, 2.26, 2.95, kk, big, body, big_color=col, big_size=27, body_size=12, name=f"kpi{i}")
band(s, 0.25, 5.2, 9.4, 1.65, [
    [("In short. ", {"bold": True}),
     ("IML and IMIT raise their prices to us; this presentation sets how our price list follows. The list rises by 5% on "
      "average, worth €1.63M a year. Where a price rise would cost us business the price stays, and what that gives up "
      f"({k(REC['given_up'])}) is recovered elsewhere on the list, so the total stays at +5%.", {})]], size=12.5)
notes(s, f"IML/IMIT increase 6.0% weighted by parts billed (6.01%; 5.96% on IML's own basis, quantity times yen base price). "
         f"Our list: +5.00% = €{SM['step_eur']:,.0f} on €{BASE:,.0f} (workbook Summary, reproduced). Kept at today's price "
         f"€{REC['given_up']:,.0f} (workbook, 7,833 part and market lines). Recovery €{REC['recovered']:,.0f}, "
         f"{REC['t_off'] * 100:.2f} points on top of own increase, {REC['pn_extra_off']:,} part numbers (the paper says "
         "8,447: it also counts one part kept at today's price).")

# =====================================================================================
# 3  What IML and IMIT changed
s = blank(prs)
im = P["iml_imit"]
frame(s, "What IML and IMIT changed", "IML and IMIT raised their prices to us by 6.0% in September 2026, about twice the "
                                      "3.2% of a year earlier",
      "Average increase to ISZE, September 2026 against September 2025, in yen, weighted by parts billed.",
      source="IML and IMIT base prices per part (Sept 2025, Sept 2026), SAP parts billing July 2025 – June 2026; paper "
             "section 2. Japan and Thailand shares re-checked in the +5% workbook (6.19% and 6.34%).",
      page=nxt(), panel=[
          ("Our price is built from IML's or IMIT's yen base price, the exchange rate, our purchase discount and a class "
           "margin set by IML. Nothing about competition enters that formula.", RED),
          ("Since 5 January 2026 the purchase discount on Japan-sourced parts fell from 38.0% to 32.7%. The weaker yen "
           "largely offsets it.", AMBER),
          ("Our margin falls about 0.5 points, because our list rises less than our cost.", AMBER)])
cats = ["All parts billed", "Service parts", "Repair parts", "Body and collision parts", "Supplied from Japan (IML)",
        "Supplied from Thailand (IMIT)"]
vals = [im["all"], im["service"], im["repair"], im["body"], im["japan"], im["thailand"]]
hbar(s, 0.25, 2.0, 5.9, 3.6, cats, vals, [WHITE] + [BAR] * 5, lambda v: f"{v:.1f}%", "chart_factory", size=11.5, vmax=8.5,
     gap=40)
kpi(s, 6.45, 2.1, 3.1, "3.2%", "the previous revision, September 2025 (weighted by quantity billed)", big_size=30)
kpi(s, 6.45, 3.55, 3.1, "5.96%", "the same revision on IML's own basis: quantity times yen base price", big_size=30)
band(s, 0.25, 5.85, 9.4, 1.0, [[("Parts billed: ", {"bold": True}),
                                 (f"service €{im['billed_service_m']}M, repair €{im['billed_repair_m']}M, body and "
                                  f"collision €{im['billed_body_m']}M. From Japan €15.9M, from Thailand €15.1M. 82 part "
                                  "numbers (€1.6M) carry no source of supply and average 1.0%.", {})]], size=11.5)
notes(s, "6.0% = weighted by parts billed (6.01%); on IML's own basis (quantity times yen base price) 5.96%. Service parts "
         "5.5%, repair 6.6%, body and collision 7.0% (paper section 2, not recomputed). The previous revision, September "
         "2025, was about 3.2% weighted by quantity billed and fed the April 2026 list. Purchase terms and exchange rate: "
         "supplier notice of 22 December 2025 and the corporate rate notifications. The exchange rate moves the euro "
         "price and the euro gross profit; it never moves the margin percentage.")

# =====================================================================================
# 4  From 6.0% to +5%
s = blank(prs)
full, scaled = SM["full_factory_eur"], SM["scaled_eur"]
wk = P["waterfall_to_5pct_k"]
steps = [("Full IML/IMIT increase on every part", full, "total", BAR),
         ("Each part passes on 90.5% of its own increase", scaled - full, "delta", GRAY),
         ("29 brake pad kits at today's price", wk["pad_kits"] * 1e3, "delta", GRAY),
         ("Categories a distributor already loses at today's price", wk["categories_lost"] * 1e3, "delta", GRAY),
         ("Small extra where UK web shops sell dearer", wk["uk_web_shops"] * 1e3, "delta", GREEN),
         ("Result: +5.00% on parts billed", SM["step_eur"], "total", RED)]
frame(s, "From 6.0% to +5%", "Every part passes on 90.5% of its own increase, and the total lands on exactly +5.00%",
      f"Increase on what we billed July 2025 – June 2026, € million a year.",
      source=SRC + " Pad kits, lost categories and web-shop extra from paper section 2; totals re-checked in the workbook.",
      page=nxt(), panel=[
          ("The same 90.5% applies to every part, so parts IML and IMIT raised more go up more and parts with no "
           "increase stay flat (180 part numbers).", RED),
          ("The 29 pad kits and the categories a distributor already loses stay at today's price. A small extra applies "
           "where UK web shops sell the same part dearer than us.", AMBER),
          (f"A typical part rises 6.4%; 9 in 10 rise 7.3% or less. {SM['parts_at_zero']} parts "
           f"({m_(SM['eur_at_zero'])} billed) stay at today's price.", AMBER)])
waterfall(s, 0.25, 2.0, 9.4, 4.0,
          steps,
          lambda v, kind: (f"€{v / 1e6:.2f}M" if kind == "total" else (f"+€{v / 1e3:.0f}k" if v > 0 else f"−€{abs(v) / 1e3:.0f}k")),
          "chart_waterfall1", size=10.5, vmax=2.3e6)
band(s, 0.25, 6.2, 9.4, 0.65, [[("Passing on the full 6.0% would raise our list by €1.96M. ", {}),
                                 ("The +5.00% is €1,629,793 on €32,595,853 of parts billed.", {"bold": True})]], size=12)
notes(s, f"Full IML/IMIT increase on every part: €{full:,.0f} (6.0% of parts billed). 90.5% of each part's own increase "
         f"(scaling {SM['k']:.4f}) = €{scaled:,.0f}. Pad kits -€109k, categories where the distributor sells under 45% of "
         f"what its vehicles need -€56k, small extra where UK web shops sell dearer +€21k; result €{SM['step_eur']:,.0f}. "
         f"Median part +6.4% (workbook {SM['median_move'] * 100:.2f}%), 90th percentile {SM['p90_move'] * 100:.1f}%, largest "
         f"single increase {SM['max_move'] * 100:.0f}% (99 parts above 15%, reviewed one by one). Class margin falls "
         f"{abs(SM['margin_pts_proposal']) * 100:.1f} points.")

# =====================================================================================
# 5  The decisions
s = blank(prs)
frame(s, "The decisions", "What each decision does, why, and what it is worth", wide=True,
      subtitle="Status as recorded up to 2 October 2026. Euro effects are a year of volume, before any change in what "
               "dealers buy.",
      source=SRC, page=nxt())
rows = [["Status", "What it does", "Why", "Effect in euro a year"],
        ["Decided", "Prices rise 5% on average. Each part follows its own IML/IMIT increase, scaled so that every part "
                    "passes on 90.5% of it and the total is exactly +5%. 180 part numbers (6.5% of parts billed) have no "
                    "increase and stay flat.",
         "IML and IMIT raise their prices to us by 6.0% on average. Following each part's own cost keeps every price tied "
         "to its cost. +5% is the target for this revision.",
         "+€1.63M on €32.6M of parts billed. Passing on the full 6.0% would be €1.96M."],
        ["Decided", "The 29 brake pad kits stay at today's price (€1.18M billed).",
         "Brake pads compete directly with aftermarket brands. The main front pad kit would otherwise have risen 17%.",
         "€109k of increase not taken, absorbed within the +5%."],
        ["Decided", "Service parts stay at today's price in eight markets: Isuzu UK (D-Max), Israel D-Max distributor, "
                    "Germany, Belgium, Norway, Cyprus, Hungary, Malta. In Israel, body, collision and lighting parts "
                    "also stay (D-Max distributor), and lighting (trucks distributor).",
         "Ageing fleets, a small service share and documented price complaints. Isuzu UK: dealers measurably bought less "
         "after the April 2026 rise. Israel: the insurance total-loss rule.",
         f"Gives up €{REC['given_up']:,.0f}, 24% of the +5%."],
        ["Decided", f"The €389k is recovered on repair and body parts with no aftermarket alternative found: about "
                    f"+{REC['t_off'] * 100:.1f} points on top of their own increase, on {REC['pn_extra_off']:,} parts. "
                    "Service parts get nothing extra.",
         "Service parts are where the alternatives, the complaints and the market decisions are. Outside price data is "
         "too thin to weight part by part.",
         f"+{k(REC['recovered'])}: repair {k(REC['rec_repair_off'])}, body {k(REC['rec_body_off'])}, service nil. The "
         "total stays +5.00%."],
        ["Suggested", "Exempt Isuzu UK (D-Max) from that extra. Its repair and body parts keep their own IML/IMIT-based "
                      "increase.",
         "The only market where dealers measurably bought less after the April 2026 change.",
         f"{k(REC['rec_iuk_off'])} moves to the other markets, which carry +{REC['t_on'] * 100:.1f} points instead of "
         f"+{REC['t_off'] * 100:.1f}. Total unchanged."]]
colors = {(r, 0): (GREEN2 if rows[r][0] == "Decided" else AMBER) for r in range(1, len(rows))}
table(s, 0.25, 1.95, 12.83, rows, [0.95, 4.7, 4.1, 3.1], row_h=0.88, head_h=0.38, size=10, head_size=8.5,
      aligns=["l", "l", "l", "l"], colors=colors, name="table_decisions")
notes(s, "Decided = management decision taken. Suggested, not decided = recommended, awaiting a decision. Euro effects are "
         "the effect of a price change on the volume billed in the last twelve months, before any change in what dealers "
         "buy. Ukraine takes the normal increase (€1.02M billed, average +5.8%) and Israel truck body panels take the "
         "normal increase (€13,795 of increase kept): both decided 2 October. Open point: the Israel D-Max distributor "
         "leasing share (page 14).")

# =====================================================================================
# 6  Where service parts stay at today's price
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
frame(s, "Where prices stay", f"Keeping prices at today's level gives up {k(REC['given_up'])} of the +5%, mostly on "
                              "service parts in four markets",
      "Increase not taken, € a year, by market and part group. Amber: the Israel insurance rule.",
      source=SRC + " Euro per market and line re-checked in the workbook (7,833 part and market lines).",
      page=nxt(), panel=[
          ("Service parts stay at today's price when vehicles we do not count buy in the market, or dealers measurably "
           "reacted, or the fleet is flat or shrinking while our service share is below the network's 28%.", RED),
          ("Repair parts follow IML/IMIT in every market. Israel adds body, collision and lighting because of the "
           "insurance total-loss rule (page 12).", AMBER),
          ("The list stays one price per part. A category kept at today's price in one market is a distributor "
           "condition on that category.", AMBER)])
hbar(s, 0.25, 2.0, 9.4, 4.85, [i[0] for i in items], [i[1] for i in items], [i[2] for i in items], k, "chart_held",
     size=10.5, vmax=185e3, gap=35)
notes(s, f"Total given up €{REC['given_up']:,.0f}. Twenty-one markets were read one by one on what each buys, how its fleet "
         "moves, how much of its service work we win (service share), what it pays against list and what dealers and "
         "distributors say. Service parts at Isuzu UK (D-Max) alone are the largest single item. The Israel D-Max lighting "
         "decision (€4,435) is included. Armenia and Kazakhstan are left out of the market decisions.")

# =====================================================================================
# 7  Markets table
s = blank(prs)
order = ["ITUK", "IUK", "UTI", "GERMANY", "UMI", "BELGIUM", "PORTUGAL", "NORWAY", "SWEDEN", "IRELAND", "CYPRUS",
         "HUNGARY", "MALTA"]
names = {"ITUK": "Isuzu Truck UK", "IUK": "Isuzu UK (D-Max)", "UTI": "Israel trucks distributor", "GERMANY": "Germany",
         "UMI": "Israel D-Max distributor", "BELGIUM": "Belgium", "PORTUGAL": "Portugal", "NORWAY": "Norway",
         "SWEDEN": "Sweden", "IRELAND": "Ireland", "CYPRUS": "Cyprus", "HUNGARY": "Hungary", "MALTA": "Malta"}
svc_hold = {"IUK", "UMI", "GERMANY", "BELGIUM", "NORWAY", "CYPRUS", "HUNGARY", "MALTA"}
body = {"UTI": "Lighting at today's price", "UMI": "Body, collision, lighting at today's price"}
ss = P["service_share_2025_pct"]
rows = [["Market", "Parts billed", "Service share 2025", "Service parts", "Body and lighting", "Increase given up",
         "Average increase after decisions"]]
colors = {}
for i, c in enumerate(order, start=1):
    mt = MT[c]
    rows.append([names[c], m_(mt["billed"]), (f"{ss[c]}%" if "*" not in str(ss[c]) else f"{str(ss[c]).replace('*', '')}%*"),
                 "Today's price" if c in svc_hold else "Follows IML/IMIT",
                 body.get(c, "Follows IML/IMIT"), k(mt["given_up"]) if mt["given_up"] else "–", f"{mt['decided'] * 100:.1f}%"])
    if c in svc_hold:
        colors[(i, 3)] = AMBER
    if c in body:
        colors[(i, 4)] = AMBER
frame(s, "Market by market", "In eight markets service parts stay at today's price; in the other markets they follow "
                             "IML/IMIT", wide=True,
      subtitle="The thirteen markets where something is held, or that are among the largest. Parts billed July 2025 – June "
               "2026.",
      source=SRC + " Service share: paper section 5. * Ireland: more than the counted fleet should need; not a real share.",
      page=nxt())
table(s, 0.25, 1.95, 12.83, rows, [2.6, 1.3, 1.45, 1.8, 2.8, 1.4, 1.8], row_h=0.3, head_h=0.5, size=10.5, head_size=8.5,
      aligns=["l", "r", "r", "l", "l", "r", "r"], colors=colors, name="table_markets")
band(s, 0.25, 6.55, 12.83, 0.52, [[("Not shown: ", {"bold": True}),
                                  ("Ukraine, Greece, Finland, Romania, Denmark, Iceland and Palestine follow IML/IMIT "
                                   "(+5.3% to +7.3% after decisions). Armenia and Kazakhstan are left out of the market "
                                   "decisions and take their own increase only (3.4%).", {})]], size=10.5)
notes(s, "Service share = service parts a market's distributor bought, against what its fleet should need at the service "
         "intervals; network 28% in 2025 (paper section 5, not recomputed). Average increase after decisions includes the "
         "lines kept at today's price at 0%, which is why those markets sit below +5%. The paper's fleet 2026 forecast "
         "column is not shown here: for two markets (Ireland, Germany) it mixes two fleet bases.")

# =====================================================================================
# 8  Recovery
s = blank(prs)
tw = P["three_ways_k"]
frame(s, "How the €389k is recovered", "The €389k is recovered on repair and body parts with no aftermarket alternative "
                                       "found",
      "Three ways were compared. All three land on exactly €1,629,793. The decided way is the middle one.",
      source=SRC + " Decided way re-checked in the workbook; ways (a) and (c) from paper section 6.",
      page=nxt(), panel=[
          ("Service parts have alternatives: filters, pads, discs and clutches are sold by aftermarket brands. The decided "
           "way puts nothing extra on them; way (a) would put €137k back.", RED),
          ("Outside price data is too thin to weight part by part: an aftermarket price exists for 21% of parts billed. "
           "Way (c) is a choice of weights, not a measurement.", AMBER),
          ("Way (a) pushes hardest on the parts IML and IMIT raised most: 56 parts reach the ceiling of their own increase "
           "plus 5 points, against 5 under the decided way.", AMBER)])
text(s, 0.25, 1.98, 4.6, 0.3, "The total stays +5.00%, € million", size=11, bold=True)
waterfall(s, 0.25, 2.3, 4.55, 4.55,
          [("+5% following IML/IMIT, all markets", REC["own_total"], "total", BAR),
           ("Kept at today's price", -REC["given_up"], "delta", AMBER),
           ("Ceiling: 5 parts", -REC["ceiling_cut"], "delta", GRAY),
           ("Recovered on repair and body", REC["recovered"], "delta", GREEN),
           ("Result", REC["own_total"], "total", RED)],
          lambda v, kind: (f"€{v / 1e6:.2f}M" if kind == "total" else (f"+€{v / 1e3:.0f}k" if v > 0 else f"−€{abs(v) / 1e3:.0f}k")),
          "chart_waterfall2", size=9.5, vmax=2.0e6, gap=30)
text(s, 5.05, 1.98, 4.6, 0.3, "Extra by part group under each way, € thousand", size=11, bold=True)
clustered(s, 5.05, 2.3, 4.6, 4.55, ["Service", "Repair", "Body and collision"],
          [("(a) spread over all remaining parts", [tw["a_spread"]["service"], tw["a_spread"]["repair"], tw["a_spread"]["body"]], BAR),
           ("Decided: only repair and body, no alternative found",
            [REC["rec_service"] / 1e3, REC["rec_repair_off"] / 1e3, REC["rec_body_off"] / 1e3], RED),
           ("(c) weighted part by part on outside prices",
            [tw["c_weighted"]["service"], tw["c_weighted"]["repair"], tw["c_weighted"]["body"]], GRAY)],
          lambda v: f"{v:.0f}", "chart_ways", size=9.5, vmax=300, gap=50, overlap=-8)
notes(s, f"Kept at today's price -€{REC['given_up']:,.0f}; ceiling cut -€{REC['ceiling_cut']:,.0f} (5 parts that would rise "
         f"more than 5 points above their own IML/IMIT increase; the cut is recovered as well); recovery +€{REC['recovered']:,.0f}: "
         f"repair €{REC['rec_repair_off']:,.0f}, body €{REC['rec_body_off']:,.0f}, service nil. Extra "
         f"{REC['t_off'] * 100:.2f} points on {REC['pn_extra_off']:,} parts. No aftermarket alternative found = no confirmed or "
         "likely competitor number, no aftermarket price observed, no cheaper Best Value alternative, not in the "
         "competitive-parts family, and not a category the distributor is measured to lose. Mostly this means none was "
         "found, not that none exists (page 11).")

# =====================================================================================
# 9  Effect by part group
s = blank(prs)
tp = P["typical_extra_part"]
frame(s, "What it does to each part group", "Service parts rise 2.3% on average, repair parts 8.7% and body and collision "
                                            "parts 9.2%",
      "Average increase over all lines, including those kept at today's price. Parts billed July 2025 – June 2026.",
      source=SRC + " Averages recomputed from the workbook's line-by-line sheet.",
      page=nxt(), panel=[
          ("Service parts fall from 4.2% to 2.3% because they carry the market decisions and nothing extra.", RED),
          (f"A typical repair or body part with no aftermarket alternative found rises about {tp['decided_pct']}% instead "
           f"of about {tp['before_pct']}%.", AMBER),
          (f"Market decisions sit mostly on D-Max markets: D-Max parts average {tp['dmax_avg_pct']}% and truck parts "
           f"{tp['truck_avg_pct']}% (before the decisions {tp['dmax_before_pct']}% and {tp['truck_before_pct']}%).", AMBER)])
gcat = [("Service parts", "service"), ("Repair parts", "repair"), ("Body and collision parts", "body")]
clustered(s, 0.25, 2.0, 9.4, 4.85,
          [f"{lab} ({m_(GA[key]['billed'], 1)} billed)" for lab, key in gcat],
          [("Before market decisions", [GA[key]["own"] * 100 for _, key in gcat], BAR),
           ("Decided", [GA[key]["decided"] * 100 for _, key in gcat], RED)],
          lambda v: f"{v:.1f}%", "chart_groups", size=11.5, vmax=11, gap=70, overlap=-10)
notes(s, "Before market decisions = each part's own increase (the +5% before holds and recovery). Decided = after the "
         "holds and the recovery. Service parts " + f"{GA['service']['own'] * 100:.2f}% to {GA['service']['decided'] * 100:.2f}%, "
         f"repair {GA['repair']['own'] * 100:.2f}% to {GA['repair']['decided'] * 100:.2f}%, body and collision "
         f"{GA['body']['own'] * 100:.2f}% to {GA['body']['decided'] * 100:.2f}% (workbook, billed-weighted). The typical-part "
         "figures and the D-Max and truck split are from paper section 6. Service = parts used in scheduled maintenance; "
         "body = the Accident and body family; repair = everything else, including lighting.")

# =====================================================================================
# 10  Isuzu UK exemption
s = blank(prs)
sel = ["IUK", "ITUK", "UTI", "GERMANY", "UMI", "BELGIUM", "PORTUGAL", "NORWAY"]
short = {"IUK": "Isuzu UK (D-Max)", "ITUK": "Isuzu Truck UK", "UTI": "Israel trucks", "GERMANY": "Germany",
         "UMI": "Israel D-Max", "BELGIUM": "Belgium", "PORTUGAL": "Portugal", "NORWAY": "Norway"}
frame(s, "Open decision", "Isuzu UK (D-Max) bought measurably less after the April 2026 rise. Should it carry the extra?",
      "Average increase by market, %: before the market decisions, as decided, and with Isuzu UK (D-Max) exempted.",
      source="Paper sections 4 and 7: dealer response from sales-to-dealer files, April–July 2025 against 2026; averages "
             "recomputed from the +5% workbook (11 October).",
      page=nxt(), panel=[
          (f"Isuzu UK (D-Max) dealers bought less after the April 2026 rise: {DR['iuk_beta']:.2f} (±{DR['iuk_ci95']:.2f}). ".replace("-", "−") +
           "For every 1% a part rose more than similar parts, they bought about 1% fewer. Dealer units fell "
           f"{abs(DR['iuk_units_change']) * 100:.1f}% against the same months of 2025.", RED),
          (f"The extra puts {k(REC['rec_iuk_off'])} on its repair and body parts. Exempting it moves that to the other "
           f"markets, which then carry +{REC['t_on'] * 100:.1f} points instead of +{REC['t_off'] * 100:.1f}. The total "
           "stays €1,629,793.", AMBER),
          ("Decision: exempt Isuzu UK (D-Max) from the recovery extra, or not. Suggested, not decided.", AMBER)])
clustered(s, 0.25, 2.0, 9.4, 4.85, [short[c] for c in sel],
          [("Before market decisions", [MA[c]["own"] * 100 for c in sel], BAR),
           ("As decided: Isuzu UK carries the extra", [MA[c]["decided"] * 100 for c in sel], RED),
           ("Isuzu UK (D-Max) exempted", [MA[c]["exempt"] * 100 for c in sel], GREEN)],
          lambda v: f"{v:.1f}", "chart_exempt", size=10, vmax=9, gap=45, overlap=-5, label_size=9.5)
notes(s, f"Dealer response = percentage change in dealer purchases for +1% on our price within the same part family, "
         f"measured on the April 2026 list change. Isuzu UK (D-Max) {DR['iuk_beta']:.2f} (standard error "
         f"{DR['iuk_se']:.2f}, 95% interval ±{DR['iuk_ci95']:.2f}). Pooled over Isuzu Truck UK, Isuzu UK (D-Max), Ireland "
         f"and Portugal: {DR['pooled']['beta_dlp']:.2f} (standard error {DR['pooled']['se_dlp']:.2f}), statistically "
         "indistinguishable from no reaction; it is used only for volume scenarios. Before the market decisions the "
         f"€1.63M becomes about €{SM['revenue_central'] / 1e6:.2f}M if the pooled reaction applies, and "
         f"€{SM['revenue_stress'] / 1e6:.2f}M in a pessimistic case (a stress test, not a forecast). With the exemption "
         f"Isuzu UK (D-Max) averages {MA['IUK']['exempt'] * 100:.1f}% instead of {MA['IUK']['decided'] * 100:.1f}%.")

# =====================================================================================
# 11  Outside price evidence
s = blank(prs)
ev = P["evidence_pct"]
op = P["outside_prices"]
frame(s, "Outside price evidence", "Outside prices cover too few parts to set prices part by part. They mostly say where "
                                   "to hold",
      "Share of parts billed with each kind of evidence. Aftermarket brands are mostly cheaper than us, outside genuine "
      "parts dearer.",
      source="Paper section 8: price observations as of 2 October 2026 (aftermarket web shops, brand recommended retail "
             "prices, genuine parts sold outside the network; VAT removed, median per part). Reported, not recomputed.",
      page=nxt(), panel=[
          ("“No aftermarket alternative found” mostly means none was found, not that none exists. Only 294 parts have any "
           "competitor evidence at all.", RED),
          (f"Where we do have aftermarket prices they sit at a median {op['aftermarket_median_index']:.2f} times our "
           f"reference dealer price (weighted by parts billed {op['aftermarket_weighted_index']:.2f}). The data mostly "
           "names parts to keep at today's price, not parts to raise.", AMBER),
          ("We do not have distributor or dealer resale prices. The reference dealer price is a construction on a "
           "provisional basis.", AMBER)])
cats = [e[0] for e in ev]
vals = [e[1] for e in ev]
cols = [GREEN2, GREEN2, BAR, BAR, RED, BAR, RED]
hbar(s, 0.25, 2.2, 6.2, 4.0, cats, vals, cols, lambda v: f"{v:.1f}%", "chart_evidence", size=10.5, vmax=118, gap=40)
kpi(s, 6.75, 2.3, 2.9, f"{op['aftermarket_median_index']:.2f}×",
    f"aftermarket shop price against our reference dealer price, median of {op['aftermarket_parts']} parts", big_size=28)
kpi(s, 6.75, 3.95, 2.9, f"{op['genuine_outside_median_index']:.2f}×",
    f"genuine Isuzu parts sold outside our network, median of {op['genuine_outside_parts']:,} parts; "
    f"{op['genuine_outside_main_source']:,} rest on one exporter", big_size=28)
text(s, 0.25, 6.3, 9.4, 0.5, "Green: sound. Grey: partial. Red: too thin to prove that no alternative exists.", size=10, color=SUB)
notes(s, "Index = outside price without VAT divided by our reference dealer price; below 1.0 the outside seller is cheaper. "
         "The reference dealer price is on a provisional basis (set 2 October 2026) and the September papers used a "
         "different one, so ratios are not comparable with September. 182 aftermarket parts (€6.0M billed) sit below 0.8; "
         "only 46 parts (€0.45M) have a rival dearer than us. 71% of parts (46% of parts billed) pass the 'no aftermarket "
         "alternative found' test. Body parts look almost entirely without alternative, but non-genuine body parts have not "
         "been searched: a price check on pattern parts for the top 50 body parts is a next action.")

# =====================================================================================
# 12  Israel
s = blank(prs)
il = P["israel"]
frame(s, "Israel", "Israel: one decision for an insurance rule, one for delivery times", wide=True,
      subtitle="Decided 2 October 2026.",
      source="Paper sections 9 and 10: Israeli motor policy wordings for vehicles up to 3.5 tonnes; distributor "
             "correspondence and back-order lists, weeks 2–40 of 2026; SAP parts billing. Reported, not recomputed.",
      page=nxt())
rect(s, 0.25, 1.98, 6.3, 4.1, fill=CARD, line=BORDER, name="isr_L_bg")
text(s, 0.5, 2.12, 5.8, 0.22, "BODY, COLLISION AND LIGHTING: INSURANCE TOTAL-LOSS RULE", size=8.5, bold=True, color=RED)
text(s, 0.5, 2.45, 5.8, 0.65, f"{il['total_loss_pct']}%", size=38, bold=True, color=AMBER)
text(s, 0.5, 3.25, 5.8, 0.55, "of pre-accident value is the total-loss limit in Israel; insurers may settle as a total "
                              "loss from 50 to 55%. The repair estimate is built from our parts list prices.", size=11.5, bold=True)
text(s, 0.5, 4.1, 5.8, 1.9, [
    "A high parts line can push a repairable vehicle over that limit, and we lose the whole repair. So the Israel D-Max "
    f"distributor keeps body, collision and lighting at today's price (€{il['dmax_body_light_given_up_k']}k of increase "
    f"given up), and the Israel trucks distributor keeps lighting (€{il['trucks_lighting_given_up_k']}k).",
    "The limits were verified in the policy for vehicles up to 3.5 tonnes. For heavier vehicles the clause was not found, "
    "so the trucks distributor's exposure is unverified."], size=11, color=SUB, spacing=8)
rect(s, 6.75, 1.98, 6.33, 4.1, fill=CARD, line=BORDER, name="isr_R_bg")
text(s, 7.0, 2.12, 5.8, 0.22, "TRUCK BODY PANELS: DELIVERY TIMES, NOT PRICE", size=8.5, bold=True, color=RED)
text(s, 7.0, 2.45, 5.8, 0.65, f"{il['panels_change_pct']:.1f}%".replace("-", "−"), size=38, bold=True, color=AMBER)
text(s, 7.0, 3.25, 5.8, 0.55, f"panel billing January–August 2026 against 2025 (€{il['panels_billed_jan_aug_2025'] / 1e3:.0f}k "
                              f"to €{il['panels_billed_jan_aug_2026'] / 1e3:.0f}k), while units rose.", size=11.5, bold=True)
text(s, 7.0, 4.1, 5.8, 1.9, [
    f"The Israel trucks distributor loses panel sales mainly to back orders of {il['backorder_weeks']} weeks (median "
    f"{il['backorder_median_weeks']}), not to price. Its panels take the normal increase (€{il['panels_increase_kept_eur']:,} "
    "of increase kept).",
    "The answer is availability: agree a stocking plan for new N-Series (P700) panels against the distributor's forecast."],
     size=11, color=SUB, spacing=8)
band(s, 0.25, 6.3, 12.83, 0.55, [[("In both cases the decision follows the evidence on why we lose sales: ", {}),
                                   ("an insurer's limit in one, delivery in the other.", {"bold": True})]], size=12)
notes(s, "Israel: a vehicle is declared a total loss at 60% of pre-accident value; the insurer may settle as a constructive "
         "total loss from 50-55% (two policy readings differ). Verified for vehicles up to 3.5 tonnes (the D-Max). Panels: "
         "back orders 4 to 16 weeks, median 13; open panel lines averaged 22 a week in weeks 2-13, 29 in weeks 14-26 and 19 "
         "in weeks 27-40. Part of the euro drop is a single F-Series grille from a 2025 stock build. On the panels bought "
         "in both periods units rose 9.5% and euro fell 5.3%. Limits: lost jobs are not visible in our data; only the "
         "distributor can supply them.")

# =====================================================================================
# 13  Changes since the paper
s = blank(prs)
frame(s, "Changes since the paper", "Since the paper: filters follow the factory increase, and one hold is still open", wide=True,
      subtitle="The euro figures in this presentation are those of the paper. A new workbook will recalculate them with "
               "these changes.",
      source="Paper of 2 October 2026; decisions of 11 October 2026; held euro per parts category recomputed from the "
             "workbook's line-by-line sheet (7,833 part and market lines, €388,914).",
      page=nxt())
rows = [["Item", "In the paper of 2 October", "Now", "Euro"],
        ["Filters", "Held at today's price in the eight markets, as service parts",
         "Follow the factory increase. Decided 11 October.",
         f"{k(HELD['filters_eur'])} of the {k(REC['given_up'])} returns to the list. The extra falls from about 3.7 to "
         "about 3.5 points (estimate)."],
        ["Brake discs and drums", "Held at today's price in the eight markets, as service parts",
         "Stay at today's price, the same logic as the pad kits. Decided 11 October.",
         f"{k(HELD['discs_drums_eur'])}, already inside the {k(REC['given_up'])}."],
        ["Intake, exhaust and emission parts", "Held at today's price in the eight markets (particulate filter assemblies, "
                                              "turbochargers, EGR valves, exhaust pipes)",
         "Open. The paper's position stands until this is decided.",
         f"{k(HELD['intake_exhaust_emission_eur'])}, inside the {k(REC['given_up'])}."]]
colors = {(1, 2): GREEN2, (2, 2): GREEN2, (3, 2): AMBER}
table(s, 0.25, 2.1, 12.83, rows, [2.3, 3.8, 3.2, 3.5], row_h=1.0, head_h=0.4, size=11, head_size=8.5,
      aligns=["l", "l", "l", "l"], colors=colors, name="table_changes")
band(s, 0.25, 5.9, 12.83, 0.8, [[("What does not change: ", {"bold": True}),
                                  ("the +5.00% target, the 29 pad kits at today's price, the Israel decisions and "
                                   "the recovery on repair and body parts with no alternative found.", {})]], size=12)
notes(s, f"Held euro by parts category, from the workbook's 7,833 held part and market lines: filters "
         f"€{HELD['filters_eur']:,.0f}, brake discs and drums €{HELD['discs_drums_eur']:,.0f}, intake, exhaust and emission "
         f"€{HELD['intake_exhaust_emission_eur']:,.0f}, out of €{HELD['given_up_eur']:,.0f}. Letting filters follow returns "
         "€26k to the list, so the recovery the extra has to deliver falls by about that amount; spread over the same "
         f"€10.6M of billed parts the extra moves from {REC['t_off'] * 100:.2f} to about 3.5 points. This is an "
         "estimate until the new workbook solves it.")

# =====================================================================================
# 14  Open points and next actions
s = blank(prs)
tx, ns = P["terms_outside_list"], P["n_series"]
frame(s, "Open points and next actions", "Three decisions are still open",
      "Two items sit outside this revision. Status up to 2 October 2026; the exhaust point is from 11 October.",
      source=SRC + " Terms outside the list: calendar 2025 order lines at the 2025 list (paper section 11).",
      page=nxt(), panel_label="NEXT ACTIONS", panel=[
          ("Decide the Isuzu UK (D-Max) exemption.", RED),
          ("Set up the market decisions and the recovery as distributor conditions per parts category (not built yet). "
           "Agree the N-Series panel stocking plan.", AMBER),
          ("Before the body share of the recovery is fixed: price check on non-genuine body parts (top 50), and confirm "
           "the reference dealer price basis.", AMBER),
          ("Take discounts and surcharges into the distributor negotiations as a separate item. Prepare first prices for "
           "the new N-Series parts.", AMBER)])
rows = [["Point", "Status", "What is open", "At stake"],
        ["Isuzu UK (D-Max) exemption", "Suggested", "Its repair and body parts keep their own increase, without a share "
                                                  "of the recovery.",
         f"{k(REC['rec_iuk_off'])} moves between markets."],
        ["Israel D-Max distributor: leasing share", "Open",
         "If leasing fleets are most of its volume, its service parts could take the normal increase. The share is not "
         "being requested now.",
         f"€{P['leasing_open']['increase_at_stake_k']}k of increase, on €{P['leasing_open']['service_billed_m']}M of service "
         "parts billed."],
        ["Intake, exhaust and emission hold", "Open", "Whether these parts stay at today's price (page 13).",
         k(HELD["intake_exhaust_emission_eur"])],
        ["Discounts and surcharges outside the list", "Negotiation topic",
         "Stock-order discount, distributors paying below list, surcharge on urgent orders. A commercial term per "
         "distributor, not part of the +5%.",
         f"Halving each market's gap to list on stock orders €{tx['halve_gap_stock_k']}k; 1 point less stock-order "
         f"discount €{tx['one_point_stock_discount_k']}k; urgent surcharge +1 point €{tx['urgent_plus1_k']}k."],
        ["New N-Series (P700) first prices", "Next price list",
         f"{ns['part_numbers']} part numbers hardly billed yet ({ns['in_base']} parts, €{ns['in_base_eur']} in this "
         "year's base). They need a well-set first price, not an increase.", "None this year."]]
colors = {(1, 1): AMBER, (2, 1): RED, (3, 1): RED, (4, 1): SUB, (5, 1): SUB}
table(s, 0.25, 1.95, 9.4, rows, [2.3, 1.3, 3.5, 2.6], row_h=0.88, head_h=0.38, size=9.5, head_size=8.5,
      aligns=["l", "l", "l", "l"], colors=colors, name="table_open")
notes(s, "Open in this revision: the Israel D-Max distributor leasing share (leased double cabs must use genuine parts in the "
         "first two years and run the highest mileage of the pickup markets) and the suggested Isuzu UK (D-Max) exemption. "
         "Discounts and surcharges are valued on calendar-2025 order lines at the 2025 list; Armenia and Kazakhstan left "
         "out. New N-Series: 826 part numbers on the provisional new-parts list, 135 ever billed (€0.25M), 14 in this "
         "year's base (€660).")

prs.save(OUT)
print("saved", OUT)
