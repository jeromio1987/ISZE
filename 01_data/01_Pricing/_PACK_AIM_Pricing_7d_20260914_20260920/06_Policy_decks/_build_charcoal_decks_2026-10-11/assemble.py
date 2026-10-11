import json
head = open('_head.txt', encoding='utf-8').read()
b = json.load(open('_blocks.json', encoding='utf-8'))
SEP = '# =====================================================================================\n'


def rep(t, pairs):
    for a, c in pairs:
        assert a in t, a[:70]
        t = t.replace(a, c)
    return t


cover = SEP + '''# 1  Cover
nxt()
s = cover(prs, "ISZE  ·  VEHICLE PARTS & ACCESSORIES  ·  PARTS PRICING",
          ["Parts price revision"],
          "How our price list follows the increase from IML and IMIT, and the exceptions we propose.",
          "October 2026  ·  Draft for review",
          "Status: a proposal. Nothing in this presentation changes a price, the price list or a distributor condition.")
notes(s, "Source: the pricing analysis of 2 October 2026 and the +5% workbook with the market layer. Everything here is a "
         "proposal for management; the figures are those of that analysis (page 12 lists three adjustments that are not yet "
         "in the figures).")

'''

summary = SEP + '''# 2  The proposal
s = blank(prs)
frame(s, "The proposal", "Proposal: our price list follows the IML and IMIT increase, at +5.0% on average",
      "Weighted by what we billed July 2025 – June 2026: €32.6M of parts billed, 15,273 part numbers.",
      source=SRC, page=nxt(), panel_label="WHAT WE PROPOSE", panel=[
          ("Each part follows its own IML/IMIT increase, scaled so that the total is +5.0%.", RED),
          ("Prices stay at today's level where a rise would cost us business: brake pad kits, service parts in eight "
           "markets, and some body and lighting parts in Israel.", AMBER),
          (f"What that gives up ({k(REC['given_up'])}) is recovered on repair and body parts for which we found no "
           "aftermarket alternative, so the total stays at +5.0%.", AMBER)])
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
         "by group service 5.5%, repair 6.6%, body and collision 7.0% (analysis section 2, not recomputed). Proposed increase "
         "= average over all lines of the group, including lines kept at today's price, billed-weighted, from the workbook "
         f"line-by-line sheet: service {GA['service']['decided'] * 100:.2f}%, repair {GA['repair']['decided'] * 100:.2f}%, body "
         f"{GA['body']['decided'] * 100:.2f}%. Total +5.00% = €{SM['step_eur']:,.0f} on €{BASE:,.0f}. Kept at today's price "
         f"€{REC['given_up']:,.0f}; recovery €{REC['recovered']:,.0f}, {REC['pn_extra_off']:,} part numbers (the analysis says "
         "8,447: it also counts one part kept at today's price). The three groups add to the €32.6M.")

'''

groups = SEP + '''# 3  How parts are grouped
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
                                    "and carry the recovery. A part is in exactly one group.", {})]], size=12)
notes(s, "Service = scheduled-service parts (BVP cross-reference service categories and the master service flag); body = "
         "family Accident and Body; repair = the rest, including lighting. Checked on 4 October against the approved release "
         "2026-10-02: 0 of 15,273 parts change between groups. Product group euro are from the parts category release of 7 October 2026 "
         "joined to the +5% workbook (each part counted once, in its group). MH has not seen the new parts categories: if their management "
         "presentation is shown first this slide can be read as a reminder; if not, this is the only place the grouping is "
         "explained.")

'''

iml = SEP + b['iml']
walk = SEP + b['walk']
walk = rep(walk, [
    ('# 4  From 6.0% to +5%', '# 5  From 6.0% to +5%'),
    ('steps = [("Full IML/IMIT increase on every part", full, "total", BAR),\n'
     '         ("Each part passes on 90.5% of its own increase", scaled - full, "delta", GRAY),\n'
     '         ("29 brake pad kits at today\'s price", wk["pad_kits"] * 1e3, "delta", GRAY),\n'
     '         ("Categories a distributor already loses at today\'s price", wk["categories_lost"] * 1e3, "delta", GRAY),\n'
     '         ("Small extra where UK web shops sell dearer", wk["uk_web_shops"] * 1e3, "delta", GREEN),\n'
     '         ("Result: +5.00% on parts billed", SM["step_eur"], "total", RED)]',
     'steps = [("Full IML/IMIT increase", full, "total", BAR),\n'
     '         ("Pass on 90.5% of each part\'s increase", scaled - full, "delta", GRAY),\n'
     '         ("Pad kits stay", wk["pad_kits"] * 1e3, "delta", GRAY),\n'
     '         ("Lost categories stay", wk["categories_lost"] * 1e3, "delta", GRAY),\n'
     '         ("Web-shop extra", wk["uk_web_shops"] * 1e3, "delta", GREEN),\n'
     '         ("Proposed: +5.00%", SM["step_eur"], "total", RED)]'),
    ('"Every part passes on 90.5% of its own increase, and the total lands on exactly +5.00%"',
     '"Passing on 90.5% of each part\'s own increase, with a few exceptions, gives +5.00% in total"'),
    ('f"Increase on what we billed July 2025 – June 2026, € million a year."',
     '"From the full IML/IMIT increase to our proposed list increase, on what we billed July 2025 – June 2026, € a year."'),
    ('"increase stay flat (180 part numbers).", RED)',
     '"increase stay flat (180 part numbers). 90.5% is the share that, after the exceptions, lands on +5.00%.", RED)'),
    ('"chart_waterfall1", size=10.5, vmax=2.3e6)', '"chart_waterfall1", size=10, vmax=2.3e6)'),
])

matrix = SEP + '''# 6  Where we increase, and by how much
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
    rows.append([nm, m_(a["all"][0]), pct(a["service"][1]), pct(a["repair"][1]), pct(a["body"][1]), pct(a["all"][1])])
    for j, gk in enumerate(("service", "repair", "body"), start=2):
        v = a[gk][1]
        if v is not None and v < 0.0005:
            colors[(i, j)] = AMBER
frame(s, "Where we increase, and by how much",
      "Where our price list rises, and by how much: market by market and by part group", wide=True,
      subtitle="Proposed average increase on our price list, per market and part group. Today's price = no increase. "
               "Parts billed July 2025 – June 2026.",
      source="ISZE pricing analysis and +5% workbook (4 Oct 2026). Billed-weighted, including lines kept at today's price; "
             "before the adjustments on page 12. Lighting is a repair part.",
      page=nxt())
table(s, 0.25, 1.95, 12.83, rows, [3.4, 1.4, 1.7, 1.7, 2.2, 1.4], row_h=0.285, head_h=0.45, size=10, head_size=8.5,
      aligns=["l", "r", "r", "r", "r", "r"], colors=colors, name="table_matrix")
notes(s, "One view of where the list rises and by how much (it replaces the earlier market table and part-group page). Each "
         "cell is the billed-weighted average increase of that group in that market after the proposed exceptions (holds and "
         "recovery). 'Today's price' = the group is kept at today's price in that market (service parts in eight markets). "
         "In the Israel D-Max distributor row the repair and body figures are lower because lighting, body and collision "
         "parts are kept at today's price. 'Seven other markets' = Ukraine, Greece, Finland, Romania, Denmark, Iceland, "
         "Palestine. Armenia and Kazakhstan are left out of the market decisions and take their own increase only.")

'''

held = SEP + b['held']
held = rep(held, [
    ('# 6  Where service parts stay at today', '# 7  Where service parts stay at today'),
    ('f"Keeping prices at today\'s level gives up {k(REC[\'given_up\'])} of the +5%, mostly on "\n'
     '                              "service parts in four markets"',
     'f"We propose to keep prices at today\'s level where a rise would cost us business. This gives up {k(REC[\'given_up\'])}"'),
    ('"Increase not taken, € a year, by market and part group. Amber: the Israel insurance rule."',
     '"Increase not taken, € a year, by market and part group. Amber: the Israel insurance rule (page 10)."'),
    ('insurance total-loss rule (page 12).', 'insurance total-loss rule (page 10).'),
    ('"The list stays one price per part. A category kept at today\'s price in one market is a distributor "\n'
     '           "condition on that category."',
     '"The list stays one price per part. A category kept at today\'s price in one market is a distributor "\n'
     '           "condition on that category. The 29 pad kits (€109k) also stay at today\'s price in every market."'),
])
rec = SEP + b['rec']
rec = rep(rec, [
    ('("+5% following IML/IMIT, all markets", REC["own_total"], "total", BAR)', '("Own increase, all parts", REC["own_total"], "total", BAR)'),
    ('"Three ways were compared. All three land on exactly €1,629,793. The decided way is the middle one."',
     '"Three ways were compared. All three land on exactly €1,629,793. The proposed way is the middle one."'),
    ('The decided "\n           "way puts nothing extra on them', 'The proposed "\n           "way puts nothing extra on them'),
    ('against 5 under the decided way.', 'against 5 under the proposed way.'),
    ('("Decided: only repair and body, no alternative found",', '("Proposed: only repair and body, no alternative found",'),
    ('Decided way re-checked in the workbook; ways (a) and (c) from paper section 6.',
     'Proposed way re-checked in the workbook; ways (a) and (c) from paper section 6.'),
    ('frame(s, "How the €389k is recovered", "The €389k is recovered on repair and body parts with no aftermarket alternative "\n'
     '                                       "found",',
     'frame(s, "How the €389k is recovered", "We propose to recover the €389k on repair and body parts with no aftermarket "\n'
     '                                       "alternative found",'),
])
uk = SEP + b['uk']
uk = rep(uk, [
    ('# 10  Isuzu UK exemption', '# 9  Isuzu UK exemption'),
    ('frame(s, "Open decision",', 'frame(s, "For decision",'),
    ('"As decided: Isuzu UK carries the extra"', '"Current proposal: Isuzu UK carries the extra"'),
    ('"Average increase by market, %: before the market decisions, as decided, and with Isuzu UK (D-Max) exempted."',
     '"Average increase by market, %: before the market exceptions, as currently proposed, and with Isuzu UK (D-Max) exempted."'),
    ('("Decision: exempt Isuzu UK (D-Max) from the recovery extra, or not. Suggested, not decided.", AMBER)',
     '("For decision: exempt Isuzu UK (D-Max) from the recovery extra, or not. We suggest exempting it.", AMBER)'),
    ('("Before market decisions", [MA[c]["own"] * 100 for c in sel], BAR)',
     '("Before market exceptions", [MA[c]["own"] * 100 for c in sel], BAR)'),
])
ev = SEP + b['ev']

israel = SEP + '''# 10  Israel
s = blank(prs)
il = P["israel"]
frame(s, "Israel", "Israel: two distributors, two different problems", wide=True,
      subtitle="Each proposal follows the reason we lose sales at that distributor.",
      source="Paper sections 9 and 10: Israeli motor policy wordings for vehicles up to 3.5 tonnes; distributor "
             "correspondence and back-order lists, weeks 2–40 of 2026; SAP parts billing. Reported, not recomputed.",
      page=nxt())
rect(s, 0.25, 1.98, 6.3, 4.1, fill=CARD, line=BORDER, name="isr_L_bg")
text(s, 0.5, 2.12, 5.8, 0.22, "ISRAEL D-MAX DISTRIBUTOR: INSURANCE TOTAL-LOSS RULE", size=8.5, bold=True, color=RED)
text(s, 0.5, 2.45, 5.8, 0.65, f"{il['total_loss_pct']}%", size=38, bold=True, color=AMBER)
text(s, 0.5, 3.25, 5.8, 0.55, "of pre-accident value is the total-loss limit in Israel; insurers may settle as a total "
                              "loss from 50 to 55%. The repair estimate is built from our parts list prices.", size=11.5, bold=True)
text(s, 0.5, 4.1, 5.8, 1.9, [
    "A high parts line can push a repairable vehicle over that limit, and we lose the whole repair. So we propose to keep "
    f"body, collision and lighting parts at today's price for the D-Max distributor (€{il['dmax_body_light_given_up_k']}k of "
    "increase given up).",
    "The limits were verified in the policy wordings for vehicles up to 3.5 tonnes, which covers the D-Max."],
     size=11, color=SUB, spacing=8)
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
         "service parts at today's price (€65k), with the leasing share still open (page 13). Panels: back orders 4 to 16 "
         "weeks, median 13; open panel lines averaged 22 a week in weeks 2-13, 29 in weeks 14-26 and 19 in weeks 27-40. Part "
         "of the euro drop is a single F-Series grille from a 2025 stock build. On the panels bought in both periods units "
         "rose 9.5% and euro fell 5.3%. Limits: lost jobs are not visible in our data; only the distributor can supply them.")

'''

adjust = SEP + '''# 12  Three part categories inside the held service parts
s = blank(prs)
frame(s, "Adjustments to part categories", "Three part categories need a position before the figures are final", wide=True,
      subtitle="Service parts are kept at today's price in eight markets. For three categories inside them we propose the "
               "following. The figures in this presentation are before these adjustments.",
      source="Held euro per parts category recomputed from the workbook's line-by-line sheet (7,833 part and market lines, "
             "€388,914). A new workbook will recalculate every figure with the adjustments.",
      page=nxt())
rows = [["Part category", "In the figures of this presentation", "Proposal", "Euro"],
        ["Filters", "Kept at today's price in the eight markets, as service parts",
         "Follow the factory (IML/IMIT) increase, like other parts.",
         f"{k(HELD['filters_eur'])} of the {k(REC['given_up'])} returns to the list. The recovery on repair and body parts "
         "then falls from about 3.7 to about 3.5 points (estimate)."],
        ["Brake discs and drums", "Kept at today's price in the eight markets, as service parts",
         "Stay at today's price, the same logic as the pad kits.",
         f"{k(HELD['discs_drums_eur'])}, already inside the {k(REC['given_up'])}. No change to the figures."],
        ["Intake, exhaust and emission parts", "Kept at today's price in the eight markets (particulate filter "
                                              "assemblies, turbochargers, EGR valves, exhaust pipes)",
         "Open: we have no proposal yet. For decision (page 13).",
         f"{k(HELD['intake_exhaust_emission_eur'])}, inside the {k(REC['given_up'])}."]]
colors = {(1, 2): AMBER, (2, 2): AMBER, (3, 2): AMBER}
table(s, 0.25, 2.25, 12.83, rows, [2.4, 3.6, 3.2, 3.6], row_h=1.05, head_h=0.4, size=11, head_size=8.5,
      aligns=["l", "l", "l", "l"], colors=colors, name="table_changes")
band(s, 0.25, 6.0, 12.83, 0.8, [[("What does not change: ", {"bold": True}),
                                  ("the +5.0% target, the 29 pad kits at today's price, the Israel proposals and "
                                   "the recovery on repair and body parts with no alternative found.", {})]], size=12)
notes(s, f"Held euro by parts category, from the workbook's 7,833 held part and market lines: filters "
         f"€{HELD['filters_eur']:,.0f}, brake discs and drums €{HELD['discs_drums_eur']:,.0f}, intake, exhaust and emission "
         f"€{HELD['intake_exhaust_emission_eur']:,.0f}, out of €{HELD['given_up_eur']:,.0f}. Letting filters follow returns "
         "€26k to the list, so the recovery the extra has to deliver falls by about that amount; spread over the same "
         f"€10.6M of billed parts the extra moves from {REC['t_off'] * 100:.2f} to about 3.5 points. This is an "
         "estimate until the new workbook solves it. Jerome settled the filter and brake-disc positions on 11 October; "
         "to management they are proposals.")

'''

openp = SEP + '''# 13  Decisions and next actions
s = blank(prs)
tx, ns = P["terms_outside_list"], P["n_series"]
frame(s, "Decisions and next actions", "Two points need a decision from management, and one more is open",
      "Two further items sit outside this revision.",
      source=SRC + " Terms outside the list: calendar 2025 order lines at the 2025 list (paper section 11).",
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
         f"€{P['leasing_open']['increase_at_stake_k']}k of increase, on €{P['leasing_open']['service_billed_m']}M of service "
         "parts billed."],
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
'''

out = head + cover + summary + groups + iml + walk + matrix + held + rec + uk + israel + ev + adjust + openp
import re
out = out.replace("; paper \"", "; analysis \"")
out = out.replace('paper section', 'analysis section').replace('Paper section', 'Analysis section')
out = out.replace('Paper sections', 'Analysis sections')
open('build_pricing_deck.py', 'w', encoding='utf-8').write(out)
print('written', len(out))
