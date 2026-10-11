"""Decision board (A3) and decision cards (A6, four to an A4 sheet) for the Plan B white paper.

Everything on them comes from Plan_B_Universe_White_Paper_2026-10-09.md; figures are asserted against planb_numbers.json.
Output: Plan_B_Decision_Board_A3_2026-10-10.pdf, Plan_B_Decision_Cards_A6_2026-10-10.pdf (+ _qa_board/ page images).

Run from the ISZE root:  python 09_meetings/Excellence_Partner_Program_2026/_build/build_decision_board.py
"""
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
QA = PACK / "_qa_board"
N = json.loads((PACK / "planb_numbers.json").read_text(encoding="utf-8"))

# the figures printed on the board and cards must be the ones in the numbers file
assert f"{N['kickback_share_billed']*100:.1f}" == "71.7" and f"{N['ituk_share']*100:.1f}" == "21.4"
assert N["rebate_total"] == 430030 and N["kickback_rebate_credit"] == 288030 and N["kickback_20pct"] == 57606
assert f"{N['with_file_share']*100:.1f}" == "55.3" and N["with_file_n"] == 5 and N["kickback_without_file_n"] == 6

NAVY, TERRA, PAPER, INK, GREY, LINE, GREEN, AMBER = "#15233c", "#c0552d", "#f7f4ee", "#222", "#6b7585", "#d9d2c3", "#3f8f6b", "#c98f1f"

BASE_CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:#fff;font-family:"Segoe UI",Arial,sans-serif;color:{INK};-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.g{{font-family:Georgia,serif}}
.box{{display:inline-block;width:4.2mm;height:4.2mm;border:.45mm solid {NAVY};border-radius:.6mm;vertical-align:-.9mm;margin:0 1.2mm 0 0}}
b{{font-weight:700}}
"""

# --------------------------------------------------------------------------------------------------------------- board
STATIONS = [  # key, x (mm), side, kind, label html
    ("s0", 44, "b", "m", "<b>Oct 2026</b><br>This paper goes to management."),
    ("d1", 74, "a", "d", "<b>Decision 1.</b> Approve the Universe route as the base route for FY2028, at no new cash."),
    ("m1", 104, "b", "m", "<b>Oct to Nov 2026. Move 1.</b> Find out what the kickback condition has already delivered. Get the contract text and the incentive sheet."),
    ("d5", 134, "a", "d", "<b>Decision 5.</b> Name the people who answer: monthly return, corrections, distributor questions."),
    ("d2", 164, "b", "d", "<b>Decision 2.</b> Rewrite the data condition in the kickback for FY2028. Needs the contract and Japan."),
    ("d3", 194, "a", "d", "<b>Decision 3.</b> Recognise distributors that meet the standard, without a discount and without a ranking."),
    ("tr", 224, "b", "m", "<b>Jan to Mar 2027. The trial.</b> Three or four distributors, no discount. Do clean per-dealer files arrive monthly?"),
    ("go", 254, "a", "m", "<b>1 Apr 2027.</b> The route starts (FY2028)."),
    ("ck", 284, "b", "m", "<b>End Jun 2027.</b> First quarterly check of the data condition."),
]
ABOVE_Y, BELOW_Y, TRACK_Y, BW, BH = 98, 164, 150, 58, 38


def board_html():
    svg = [f'<svg viewBox="0 0 420 297" width="420mm" height="297mm" style="position:absolute;left:0;top:0">']
    # zones
    for x0, x1, name in ((10, 149, "1  DECIDE"), (149, 239, "2  BUILD AND PROVE"), (239, 336, "3  RUN")):
        svg.append(f'<rect x="{x0}" y="62" width="{x1-x0-2}" height="150" rx="3" fill="{PAPER}"/>')
        svg.append(f'<text x="{x0+4}" y="69" font-size="4.2" font-weight="700" fill="{GREY}" letter-spacing=".5">{name}</text>')
    # track
    svg.append(f'<line x1="30" y1="{TRACK_Y}" x2="318" y2="{TRACK_Y}" stroke="{NAVY}" stroke-width="2.2" stroke-linecap="round"/>')
    # fork
    svg.append(f'<path d="M318 {TRACK_Y} C332 {TRACK_Y}, 332 112, 346 112" fill="none" stroke="{GREEN}" stroke-width="2.2" stroke-linecap="round"/>')
    svg.append(f'<path d="M318 {TRACK_Y} C332 {TRACK_Y}, 332 190, 346 190" fill="none" stroke="{TERRA}" stroke-width="2.2" stroke-linecap="round"/>')
    svg.append(f'<circle cx="318" cy="{TRACK_Y}" r="4.6" fill="#fff" stroke="{NAVY}" stroke-width="1.2"/>')
    svg.append(f'<text x="318" y="{TRACK_Y+1.4}" font-size="3.6" font-weight="700" text-anchor="middle" fill="{NAVY}">?</text>')
    # stations
    for key, x, side, kind, _ in STATIONS:
        if kind == "d":
            svg.append(f'<circle cx="{x}" cy="{TRACK_Y}" r="7.4" fill="{TERRA}" stroke="#fff" stroke-width="1.2"/>')
            svg.append(f'<text x="{x}" y="{TRACK_Y+3.4}" font-size="9.5" font-weight="700" fill="#fff" text-anchor="middle" font-family="Georgia,serif">{key[1]}</text>')
        else:
            svg.append(f'<circle cx="{x}" cy="{TRACK_Y}" r="3.6" fill="{NAVY}" stroke="#fff" stroke-width="1"/>')
        y0, y1 = (ABOVE_Y + BH, TRACK_Y - 8) if side == "a" else (TRACK_Y + 8, BELOW_Y)
        svg.append(f'<line x1="{x}" y1="{y0 if side=="a" else y0}" x2="{x}" y2="{y1 if side=="a" else y1}" stroke="{LINE}" stroke-width=".5"/>')
    # siding for decision 4
    svg.append(f'<path d="M300 {TRACK_Y} C300 134, 304 126, 316 126 L322 126" fill="none" stroke="{AMBER}" stroke-width="1.6" stroke-dasharray="3 2"/>')
    svg.append(f'<circle cx="322" cy="126" r="7.4" fill="{AMBER}" stroke="#fff" stroke-width="1.2"/>')
    svg.append(f'<text x="322" y="129.4" font-size="9.5" font-weight="700" fill="#fff" text-anchor="middle" font-family="Georgia,serif">4</text>')
    svg.append("</svg>")

    divs = []
    for key, x, side, kind, label in STATIONS:
        y = ABOVE_Y if side == "a" else BELOW_Y
        extra = ""
        if kind == "d":
            extra = (f'<div class="tick"><span class="box"></span>Yes <span class="box"></span>Not yet <span class="box"></span>No</div>'
                     f'<div class="ol">Owner ____________ Date _________</div>')
        divs.append(f'<div class="st {"dec" if kind=="d" else ""}" style="left:{x-BW/2}mm;top:{y}mm;width:{BW}mm;height:{BH}mm">{label}{extra}</div>')
    # decision 4 label (siding)
    divs.append(f'<div class="st dec amber" style="left:{283}mm;top:{64}mm;width:{54}mm;height:{52}mm"><b>Decision 4. Parked.</b> Do not fund the &euro;100,000 Universe route yet. Revisit after the trial, when distributors take part and a named campaign meets the size filter.'
                 f'<div class="tick"><span class="box"></span>Yes <span class="box"></span>Not yet <span class="box"></span>No</div><div class="ol">Owner ____________ Date _________</div></div>')
    # fork ends
    divs.append(f'<div class="end up" style="left:349mm;top:70mm;width:61mm;height:72mm"><div class="eh">Carry on</div>After two eligible quarters at least half of the first distributors send clean files, and a participant can name a decision the data changed.<br><br><b>The discount is not needed for data. The question disappears.</b></div>')
    divs.append(f'<div class="end dn" style="left:349mm;top:160mm;width:61mm;height:56mm"><div class="eh">Back to the discount question</div>Distributors send the minimum, or the ten without a kickback do not answer a formal request.<br><br><b>Management then decides with a measured result in hand, not a forecast.</b></div>')
    divs.append(f'<div class="lab" style="left:290mm;top:{TRACK_Y+4}mm;width:26mm;text-align:center"><b>Autumn 2027</b><br>Review</div>')

    # header
    head = (f'<div class="g title" style="left:12mm;top:9mm">Isuzu Universe without a discount</div>'
            f'<div class="sub" style="left:12mm;top:25mm;width:300mm">Decision board. The route if management does not approve the Excellence Partner discount. '
            f'Walk the line from left to right, take the decision cards in order, and tick each decision on the board.</div>'
            f'<div class="legend" style="left:12mm;top:41mm;width:320mm"><span class="dot big"></span> a decision (card with the same number) '
            f'<span class="dot"></span> a milestone <span class="box"></span> tick one box per decision, then write an owner and a date. '
            f'&nbsp; Kickback = the yearly rebate on parts purchases. FY2028 = 1 April 2027 to 31 March 2028.</div>')

    # bottom panels
    panels = (
        f'<div class="panel" style="left:12mm;top:222mm;width:126mm;height:64mm"><div class="ph">Six numbers behind the decisions (FY2026)</div>'
        f'<table><tr><td>&euro;31.78M</td><td>parts billed to the 19 distributors; &euro;22.38M of it stock orders</td></tr>'
        f'<tr><td>71.7%</td><td>of billing sits with the nine distributors that have a kickback</td></tr>'
        f'<tr><td>&euro;430,030</td><td>rebate credits; &euro;288,030 to eight kickback distributors, &euro;142,000 to Isuzu Truck UK (no kickback)</td></tr>'
        f'<tr><td>~&euro;57,600</td><td>a year at risk for data, at the 20% share Jerome confirmed (&euro;3,400 to &euro;19,000 per distributor)</td></tr>'
        f'<tr><td>5 of 19</td><td>have a sales-to-dealer file for FY2026, 55.3% of billing; only 3 of the 9 kickback distributors</td></tr>'
        f'<tr><td>55 / 45</td><td>Universe&rsquo;s own score out of 100 that a distributor / a dealer joins as designed</td></tr></table></div>'
        f'<div class="panel" style="left:143mm;top:222mm;width:126mm;height:64mm"><div class="ph">What the route is</div>'
        f'Ask for three things: one price-free file a month (dealer, part number, period, quantity), a list that links each dealer name to a customer account, once, and one agreed action per review. '
        f'Give back a monthly review of the distributor&rsquo;s own business, its dealers&rsquo; standards results, and written rules on what ISZE will not do with the data. '
        f'<b>Cash: &euro;0 new.</b> The team&rsquo;s own time is not counted in any figure.</div>'
        f'<div class="panel" style="left:274mm;top:222mm;width:134mm;height:64mm"><div class="ph">What is not known</div>'
        f'No measured sales uplift from data sharing exists in the workspace. The kickback contract text is not in the workspace; how the 20% divides between the KPI submission and the sales-to-dealer file is unknown. '
        f'Universe has no hosted service and no real sign-in, and its tests with real people are parked. No legal review has been done. '
        f'<b>Stop rule:</b> if after two eligible cycles nobody can name a decision the data changed, or fewer than half of the first distributors deliver clean files, the route stops or goes back to the discount question.</div>')

    css = BASE_CSS + f"""
@page{{size:420mm 297mm;margin:0}}
body{{width:420mm;height:297mm;position:relative;overflow:hidden}}
.title{{position:absolute;font-size:13mm;font-weight:700;color:{NAVY};letter-spacing:-.2mm;white-space:nowrap}}
.sub{{position:absolute;font-size:4.1mm;color:{INK};line-height:1.35}}
.legend{{position:absolute;font-size:3.4mm;color:{GREY}}}
.dot{{display:inline-block;width:3mm;height:3mm;border-radius:50%;background:{NAVY};margin:0 1mm 0 3mm;vertical-align:-.3mm}}
.dot.big{{background:{TERRA};width:4.4mm;height:4.4mm;margin-left:0}}
.st{{position:absolute;font-size:3.35mm;line-height:1.28;padding:2mm 2.4mm;background:#fff;border:.3mm solid {LINE};border-radius:1.6mm;overflow:hidden}}
.st.dec{{border-color:{TERRA};border-width:.5mm}}
.st.amber{{border-color:{AMBER};background:#fffaf0}}
.tick{{margin-top:1.6mm;font-size:3.5mm;font-weight:700;color:{NAVY}}}
.ol{{margin-top:1.8mm;font-size:3mm;color:{GREY};white-space:nowrap}}
.end{{position:absolute;font-size:3.55mm;line-height:1.32;padding:3mm 3.4mm;border-radius:2mm}}
.end.up{{border:.6mm solid {GREEN};background:#f1f8f4}}
.end.dn{{border:.6mm solid {TERRA};background:#fbf2ee}}
.eh{{font-family:Georgia,serif;font-size:5mm;font-weight:700;margin-bottom:1.6mm;color:{NAVY}}}
.lab{{position:absolute;font-size:3.2mm;line-height:1.25;color:{NAVY}}}
.panel{{position:absolute;font-size:3.35mm;line-height:1.34;padding:3mm 3.6mm;border:.3mm solid {LINE};border-radius:1.6mm;overflow:hidden}}
.ph{{font-family:Georgia,serif;font-size:4.3mm;font-weight:700;color:{NAVY};margin-bottom:1.4mm}}
.panel table{{border-collapse:collapse;width:100%}}
.panel td{{padding:.6mm 0;vertical-align:top;font-size:3.2mm;line-height:1.25}}
.panel td:first-child{{font-weight:700;color:{TERRA};width:21mm;white-space:nowrap}}
.foot{{position:absolute;left:12mm;top:289mm;font-size:2.8mm;color:{GREY}}}
"""
    foot = '<div class="foot">Source: white paper Isuzu Universe without a discount, 9 October 2026 (chapters 4 to 12). Figures: FY2026 = 1 April 2025 to 31 March 2026. Proposals, not agreed.</div>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Decision board</title><style>{css}</style></head><body>{"".join(svg)}{head}{"".join(divs)}{panels}{foot}</body></html>'


# --------------------------------------------------------------------------------------------------------------- cards
def card(kind, num, title, fields):
    rows = "".join(f'<div class="f"><div class="fl">{l}</div><div class="fv">{v}</div></div>' for l, v in fields)
    return f'<div class="card {kind}"><div class="ch"><span class="no">{num}</span><span class="ct">{title}</span></div><div class="cb">{rows}</div></div>'


def back(kind, num, rows, decision=True):
    r = "".join(f'<div class="f"><div class="fl">{l}</div><div class="fv">{v}</div></div>' for l, v in rows)
    d = ('<div class="dec"><div class="fl">Our decision</div><div class="tickrow"><span class="box"></span>Yes <span class="box"></span>Not yet <span class="box"></span>No</div>'
         '<div class="line">If &ldquo;not yet&rdquo;, what is missing: ______________________________</div><div class="line">Owner ______________________ Date ______________</div></div>') if decision else ""
    return f'<div class="card back {kind}"><div class="ch"><span class="no">{num}</span><span class="ct">Back</span></div><div class="cb">{r}</div>{d}</div>'


CARDS = [
    ("dcard", "1", "Approve the Universe route as the base route for FY2028",
     [("What it does", "Commits ISZE to ask for one price-free file a month per distributor, return a monthly review, and recognise those who take part. No new discount."),
      ("Why", "It lets ISZE start in April 2027 whatever happens to the discount."),
      ("Euro effect", "No new cash. The credits already paid (&euro;430,030 in FY2026) continue."),
      ("We recommend", "<b>Yes</b>, and run the January to March 2027 trial under it.")],
     [("If yes", "Expect lower and thinner participation than a payment would buy: Universe scores 55 out of 100 for distributors and 45 for dealers. The team&rsquo;s own time is not counted."),
      ("If no", "ISZE has no route to start from in April 2027 other than the discount."),
      ("Needs", "Management.")]),
    ("dcard", "2", "Rewrite the data condition in the kickback for FY2028",
     [("What it does", "Ties the 20% data share of the kickback to a written standard, checked every quarter. It covers the KPI submission and the sales-to-dealer file."),
      ("Why", "Today the condition buys a file, not a good file."),
      ("Euro effect", "None on the amount. About &euro;57,600 a year is at stake in total: &euro;3,400 to &euro;19,000 per distributor, eight distributors."),
      ("We recommend", "<b>Yes</b>, once Move 1 shows what the current condition has delivered.")],
     [("If yes", "Risk of conflict with the contract or with Japan. A competition-law check is needed: likelihood low to medium, not yet assessed."),
      ("If no", "The condition keeps buying the minimum file. It never reaches Isuzu Truck UK (21.4% of billing) or the ten distributors without a kickback."),
      ("Needs", "The contract text, the incentive budget sheet, Japan&rsquo;s agreement, legal review.")]),
    ("dcard", "3", "Recognise distributors that meet the standard, without a discount",
     [("What it does", "Names the distributors that meet the data standard for two quarters in a row, at the European aftersales meeting. No ranking. No prize for the largest."),
      ("Why", "It is the only reward available at no cash cost."),
      ("Euro effect", "&euro;0 in cash. It costs time, with IMG in support."),
      ("We recommend", "<b>Yes</b>, with IMG.")],
     [("If yes", "It must never become a league table. Whether recognition moves a distributor is not known."),
      ("If no", "The ten distributors without a kickback get a request and the monthly return, and nothing else."),
      ("Needs", "IMG.")]),
    ("dcard", "4", "Do not fund the &euro;100,000 Universe route yet",
     [("What it does", "Leaves campaign support (&euro;60,000 to &euro;90,000), dealer enablement (&euro;15,000 to &euro;25,000) and independent evaluation (&euro;10,000 to &euro;15,000) unfunded until the trial."),
      ("Why", "Universe needs 24 to 36 qualifying actions to cover the campaign line, and nothing yet shows that qualifying campaigns exist."),
      ("Euro effect", "&euro;60,000 to &euro;90,000 not spent now."),
      ("We recommend", "<b>Hold</b>. Revisit after the trial.")],
     [("If funded later", "A campaign needs at least &euro;150,000 of eligible billing. The whole &euro;100,000 needs about 40 qualifying actions at &euro;2,500 each to break even. Universe says no realised return is evidenced."),
      ("If funded now", "Money is spent before there is any evidence of take-up."),
      ("Needs", "Management, after the trial.")]),
    ("dcard", "5", "Name the people who answer",
     [("What it does", "Gives the monthly return, the corrections and the distributors&rsquo; questions an owner and time."),
      ("Why", "The mileage question to Isuzu Truck UK was drafted on 18 September 2026 and, as of 21 September, had still not been sent. That is a response gap, not a data gap."),
      ("Euro effect", "Time, not cash. Not counted in any figure."),
      ("We recommend", "Decide <b>before the trial starts</b>.")],
     [("If yes", "The route can start. The monthly return and corrections have a name next to them."),
      ("If no", "The route does not start. Universe fails on the response, not on the data."),
      ("Also needed", "Someone sends the drafted request to IT for real sign-in (drafted 7 October, not sent)."),
      ("Needs", "Management names the people.")]),
]

STOP = ("rule", "&#9632;", "The stop rule, agreed in advance",
        [("The route stops, or goes back to the discount question, if after two eligible cycles", "no participant can name a decision the data changed, <b>or</b> fewer than half of the first distributors deliver clean files, <b>or</b> a confidentiality or legal weakness appears that cannot be closed."),
         ("What it does not do", "It does not broaden the group to look for a better result, and it does not add a report."),
         ("Source", "Universe 3.0, 9.3; white paper 10.2.")],
        [("Indicators, every quarter", "Distributors with three clean monthly files in a row: at least half of the first group after two quarters. Per-dealer detail: at least four distributors by end FY2028. Decisions taken on the data and logged: at least two per participating distributor. Share of stock orders placed at quarter end: 31.8% in FY2026 against 25% if even; no rise."),
         ("Status", "All thresholds are proposals to be agreed.")])

HOW = ("rule", "&#9654;", "How to use the board and the cards",
       [("1", "Lay the A3 board flat. Read the line from left to right."),
        ("2", "Take card 1. Read the front aloud, then turn it over. Decide: Yes, Not yet or No."),
        ("3", "Tick the same box on the board. Write an owner and a date. &ldquo;Not yet&rdquo; needs the name of what is missing."),
        ("4", "Then take card 5, 2, 3 and 4 in the order the board shows."),
        ("5", "Last, read the stop rule card. It is agreed now so that it cannot be argued later.")],
       [("What the cards are", "Each front says what the decision does, why, what it costs in euros and what we recommend. The back says what happens on yes, what happens on no, and who has to be involved."),
        ("Not in the room?", "The board and cards carry the same text as the white paper. Chapter numbers: 4 the lever, 6 the design, 7 cost, 10 stop rule, 12 decisions.")])

NUM = ("rule", "&euro;", "Six numbers",
       [("&euro;31.78M", "parts billed to the 19 distributors in FY2026; &euro;22.38M of it stock orders (70.4%)."),
        ("71.7%", "of billing sits with the nine distributors that have a kickback (74.1% of stock orders)."),
        ("&euro;430,030", "rebate credits booked: &euro;288,030 to eight kickback distributors, &euro;142,000 to Isuzu Truck UK, which has no kickback."),
        ("~&euro;57,600", "a year tied to data at a 20% share. 0.18% of billing."),
        ("5 of 19", "distributors have a sales-to-dealer file for FY2026 (55.3% of billing). Six of the nine kickback distributors have none in the workspace."),
        ("55 / 45", "Universe&rsquo;s own score out of 100 that a distributor / a dealer joins as designed.")],
       [("What this means", "The condition we have is real but small. It reaches the distributors that hold 72% of billing and averages about &euro;7,000 per distributor a year. That is enough to get a file, not a good one. Isuzu Truck UK and ten others have no condition at all. The route therefore rests on what the distributor gets back each month."),
        ("Source", "White paper chapter 1 and 4; FY2026 = 1 April 2025 to 31 March 2026.")])


def special(c, backside=False):
    kind, num, title, front, back_rows = c
    if not backside:
        return card("rule", num, title, front)
    return back("rule", num, back_rows, decision=False)


def cards_html():
    fronts = [card(k, n, t, f) for k, n, t, f, _ in CARDS] + [special(STOP), special(HOW), special(NUM)]
    backs = [back(k, n, b) for k, n, t, f, b in CARDS] + [special(STOP, True), special(HOW, True), special(NUM, True)]

    def sheet(items, mirror):
        items = items + [""] * (4 - len(items))
        if mirror:  # duplex, flip on the long edge: mirror each row
            items = [items[1], items[0], items[3], items[2]]
        return '<section class="sheet">' + "".join(f'<div class="slot">{i}</div>' for i in items) + "</section>"

    pages = [sheet(fronts[0:4], False), sheet(backs[0:4], True), sheet(fronts[4:8], False), sheet(backs[4:8], True)]
    css = BASE_CSS + f"""
@page{{size:210mm 297mm;margin:0}}
.sheet{{width:210mm;height:297mm;display:grid;grid-template-columns:105mm 105mm;grid-template-rows:148.5mm 148.5mm;page-break-after:always;position:relative}}
.slot{{width:105mm;height:148.5mm;padding:4mm;position:relative;border:.2mm dashed #b9b2a3}}
.card{{width:100%;height:100%;border:.5mm solid {NAVY};border-radius:3mm;overflow:hidden;display:flex;flex-direction:column;background:#fff}}
.ch{{background:{NAVY};color:{PAPER};padding:3mm 3.6mm;display:flex;gap:3mm;align-items:center}}
.card.rule .ch{{background:{TERRA}}}
.no{{font-family:Georgia,serif;font-weight:700;font-size:9mm;line-height:1;color:{PAPER};min-width:8mm;text-align:center}}
.ct{{font-family:Georgia,serif;font-weight:700;font-size:5mm;line-height:1.18}}
.cb{{padding:3.2mm 3.8mm 2mm;flex:1}}
.f{{margin-bottom:3.4mm}}
.fl{{font-size:3mm;font-weight:700;letter-spacing:.35mm;text-transform:uppercase;color:{TERRA};margin-bottom:.4mm}}
.card.rule .fl{{color:{NAVY}}}
.fv{{font-size:4.05mm;line-height:1.32}}
.dec{{border-top:.3mm solid {LINE};padding:2.6mm 3.8mm 3.2mm;background:#faf8f3}}
.tickrow{{font-size:4.2mm;font-weight:700;color:{NAVY};margin:1mm 0 2mm}}
.line{{font-size:3mm;color:{GREY};margin-top:2mm;white-space:nowrap;overflow:hidden}}
.back .ch{{background:{GREY}}}
"""
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Decision cards</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'


# --------------------------------------------------------------------------------------------------------------- output
def to_pdf(html_text, name, tmp_name):
    h = PACK / tmp_name
    h.write_text(html_text, encoding="utf-8")
    pdf = PACK / name
    try:
        pdf.unlink(missing_ok=True)
    except PermissionError:
        pdf = PACK / name.replace(".pdf", ".NEW.pdf")
        pdf.unlink(missing_ok=True)
        print("old PDF is open in a viewer; writing", pdf.name)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={tempfile.mkdtemp(prefix='chrome_board_')}",
                    f"--print-to-pdf={pdf}", h.as_uri()], check=True, capture_output=True, timeout=120)
    assert pdf.exists(), "Chrome wrote no PDF"
    h.unlink()
    return pdf


if __name__ == "__main__":
    import fitz

    QA.mkdir(exist_ok=True)
    for f in QA.glob("*.png"):
        f.unlink()
    b = to_pdf(board_html(), "Plan_B_Decision_Board_A3_2026-10-10.pdf", "_tmp_board.html")
    c = to_pdf(cards_html(), "Plan_B_Decision_Cards_A6_2026-10-10.pdf", "_tmp_cards.html")
    for pdf, tag, dpi in ((b, "board", 100), (c, "cards", 90)):
        d = fitz.open(pdf)
        print(pdf.name, d.page_count, "pages", d[0].rect.width / 72 * 25.4, "x", d[0].rect.height / 72 * 25.4, "mm")
        for n, pg in enumerate(d, 1):
            pg.get_pixmap(dpi=dpi).save(QA / f"{tag}_{n}.png")
