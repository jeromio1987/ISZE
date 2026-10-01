"""Market-by-market pricing exercise: one page per market, decision matrix up front. Self-contained HTML (inline SVG).

Run after market_facts.py:  python build_market_exercise_20260930.py
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
F = json.loads((HERE / "market_facts_2026-09-30.json").read_text(encoding="utf-8"))
OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing")
OUT = OUT_DIR / "ISZE_Market_Pricing_Exercise_2026-09-30.html"
M = F["markets"]
NET_SHARE = F["network_service_share_2025"]
TOTAL_STEP, TOTAL_BASE = F["total_step"], F["total_base"]
UTI_LIGHTING_STEP = 8491.0   # UTI lighting EUR 133,712 x 6.35% proposed (19 Sep tier labels joined to the proposal)

NAME = {"IUK": "UK — IUK (D-Max)", "ITUK": "UK — ITUK (trucks)", "UTI": "Israel — UTI (trucks)", "UMI": "Israel — UMI (D-Max)",
        "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal", "NORWAY": "Norway", "SWEDEN": "Sweden",
        "IRELAND": "Ireland", "UKRAINE": "Ukraine", "GREECE": "Greece", "CYPRUS": "Cyprus", "HUNGARY": "Hungary",
        "FINLAND": "Finland", "ARMENIA": "Armenia (CIS)", "MALTA": "Malta", "ROMANIA": "Romania", "KAZAKHSTAN": "Kazakhstan (CIS)",
        "DENMARK": "Denmark", "ICELAND": "Iceland"}
DIST = {"IUK": "Isuzu UK", "ITUK": "Isuzu Truck UK", "UTI": "UTI", "UMI": "UMI", "GERMANY": "Isuzu Sales Deutschland",
        "BELGIUM": "Astara (Isuzu Benelux)", "PORTUGAL": "Astara Portugal (Imotors)", "NORWAY": "RSA", "SWEDEN": "Isuzu Sweden",
        "IRELAND": "Harris Group", "UKRAINE": "Ukraine distributor", "GREECE": "Petropoulos", "CYPRUS": "Loutsios & Sons",
        "HUNGARY": "AutoWallis", "FINLAND": "Nordic Auto", "ARMENIA": "GA", "MALTA": "GasanZammit Motors", "ROMANIA": "Romania distributor",
        "KAZAKHSTAN": "CBC", "DENMARK": "Isuzu Denmark", "ICELAND": "BL"}

# What is specific to each market, from minutes, market packs and research notes (sources in the footnote).
CTX = {
    "IUK": ["New D-Max demand has collapsed: the double-cab company-car tax change (April 2025) and the zero-emission rules; "
            "the pickup market was down 61% year on year in August 2026.",
            "Dealers say brake parts and wipers are too dear against the aftermarket and ask for a value range (review 6 Aug 2026).",
            "Only market where dealers measurably bought less of a part after its April 2026 price rise.",
            "Five-year warranty: aftertreatment parts that cannot be bought elsewhere sit at their class price, no higher."],
    "ITUK": ["Brake price is the number one dealer complaint (18 Aug 2026); N75 pad units fell 15.5% in two years — the pad kits are now held.",
             "Operator licensing gives the inspection appointment, not the sale: it does not require genuine parts.",
             "Dealers did not buy less after the April 2026 rise; UK truck dealer purchases were up 3.7% March-August.",
             "N75 air filter sits at about 20% cover — a fitment problem, not a price problem."],
    "UTI": ["1,700 trucks on five-year repair and maintenance contracts.",
            "Collision complaint: N/7.5 front package EUR 679 to EUR 2,144; bumper went from one part to four; grille +880%, rear light +1,228%.",
            "The Israeli total-loss rule was verified only up to 3.5 t; for UTI's trucks it is unverified.",
            "Already buys at 86% of list on stock orders (customer condition)."],
    "UMI": ["The pickup sits inside the verified total-loss rule (up to 3.5 t); lamps may be replaced by a part of 'similar description' under the policy.",
            "66% of pickups privately owned; leasing double cabs must use genuine parts for two years and run 34,443 km a year.",
            "Isuzu's share fell 34.6% to 27.6% against Chinese brands (IMIE, July 2026).",
            "Brake parts underperform on price against alternatives (review 12 Aug 2026)."],
    "GERMANY": ["Independent workshops buy a comparable brake rotor at about EUR 80 against about EUR 100 through Isuzu, and fuel filters at about EUR 5.90 (review 5 Aug 2026).",
                "Isuzu's new-vehicle share rose 5.3% to 7.0%, but small-business demand is weak (IMIE)."],
    "BELGIUM": ["Astara calls brake pricing 'a known structural issue' and wants a central fix, not piecemeal special prices (12 Aug 2026).",
                "Isuzu's new-vehicle share fell 11.2% to 3.3% with pre-registered stock weighing (IMIE)."],
    "PORTUGAL": ["Isuzu's share fell 28.6% to 18.7% in severe price competition (IMIE, June 2026).",
                 "Buyers chose the three-seat homologation to save tax; lowest mileage of the pickup markets (22,742 km a year).",
                 "A BVP 3.5 t brake pad about 30% cheaper was cited as a useful alternative (review 29 Jul 2026)."],
    "NORWAY": ["Combustion-engine pickup demand is shrinking fast; construction bankruptcies; Isuzu's share fell 35.7% to 13.1%; electric rivals strong (IMIE, July 2026).",
               "68% of Norway's D-Max parts turnover is outside the warranty limits — the highest of all markets."],
    "SWEDEN": ["Isuzu still first year to date but lost a month to Ford; a Toyota grey-import spike has faded (IMIE, July 2026)."],
    "IRELAND": ["Integrated importer: assembly plant, workshops, parts centre, 25 locations; registrations +41% in 2025; annual commercial test.",
                "Isuzu's share rose 8.2% to 11.6% (IMIE, June 2026). Harris will resend earlier pricing issues (review 6 Aug 2026)."],
    "UKRAINE": ["Wartime market. Nothing on file about pricing."],
    "GREECE": ["Collision work rising on higher-value jobs. No price complaint on file."],
    "CYPRUS": ["55% of all vehicle registrations January-July 2025 were used vehicles (17,144 of 31,200, Cyprus Statistical Service).",
               "Imported vehicles are not in our fleet count, so our service share here is overstated."],
    "HUNGARY": ["An aftermarket fuel filter sells at about 10% of the genuine price; the distributor mentioned up to about 30% discount for a brake special price (11 Aug 2026)."],
    "FINLAND": ["Nothing on file about pricing."],
    "ARMENIA": ["CIS pricing basis (class margins against a flat 60% margin) is your open decision — not touched here."],
    "MALTA": ["88% of used car imports in 2025 came from Japan: 4,639 cars against 665 from the UK (Transport Minister, March 2026).",
              "Imported vehicles are not in our fleet count, so our service share here is overstated."],
    "ROMANIA": ["Action agreed to review brake-rotor behaviour across the dealer network (25 Aug 2026); the distributor adds about 10% to maintenance prices to cover future increases."],
    "KAZAKHSTAN": ["CIS pricing basis (class margins against a flat 60% margin) is your open decision — not touched here."],
    "DENMARK": ["Nothing on file about pricing."],
    "ICELAND": ["Brake pad share 22.2% against 29.5% for the network; asks a tailor-made price benchmarked on Bosch and Textar; air-freighted rush orders carry a 3% surcharge (25 Aug 2026)."],
}
COMPLAINT_SERVICE = {"IUK", "GERMANY", "HUNGARY", "PORTUGAL", "ICELAND", "BELGIUM", "UMI"}
NOTE = {
    "UMI": "Against this: leasing double cabs must use genuine parts in their first two years and run the highest mileage of the pickup "
           "markets. If UMI's volume is mostly leasing fleets, its service parts could carry the factory move instead — UMI can tell us the split",
    "UTI": "Lighting only, not all body parts: the heavy-vehicle total-loss rule is unverified, and the bigger lever is the bumper and grille "
           "packaging, which is a question for IML, plus a paid-on-genuine-use arrangement with insurers",
    "ITUK": "The pad kits are already held (your call, 30 September)",
    "IRELAND": "A service share at or above 100% of the official fleet means the real fleet is bigger than counted — most likely used D-Max "
               "brought in from the UK; worth confirming with Harris",
}
IMPORTED = {"MALTA", "CYPRUS"}
CIS = {"ARMENIA", "KAZAKHSTAN"}


def pct(x, d=1, sign=False):
    if x is None:
        return "n/a"
    s = f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%"
    return s


def share_txt(x):
    if x is None:
        return 'n/a'
    return 'over 100%*' if x > 1.0 else ('100%*' if x >= 0.995 else f'{x * 100:.0f}%')


def eur(x):
    return "n/a" if x is None else f"EUR {x:,.0f}"


def decide(k, m):
    f = m.get("fleet", {})
    f23, f25, f26 = f.get("2023"), f.get("2025"), m.get("fleet_2026_corrected")
    fleet_chg = (f25 / f23 - 1) if f23 and f25 else None
    fwd = (f26 / f25 - 1) if f25 and f26 else None
    sh = m.get("service_share", {})
    s23, s25 = (sh.get("2023") or {}).get("total"), (sh.get("2025") or {}).get("total")
    share_chg = (s25 - s23) if s23 is not None and s25 is not None else None
    ageing = (fleet_chg is not None and fleet_chg <= 0.02) or (fwd is not None and fwd <= -0.03)
    weak = s25 is not None and (s25 < NET_SHARE or (share_chg is not None and share_chg < 0))
    dr = m.get("dealer_response")
    reacts = dr is not None and dr["beta"] + 1.96 * dr["se"] < 0
    reasons, hold = [], False
    ftxt = []
    if fleet_chg is not None:
        ftxt.append(f"fleet {fleet_chg * 100:+.0f}% 2023-25")
    if fwd is not None:
        ftxt.append(f"{fwd * 100:+.0f}% in the 2026 forecast")
    ftxt = " and ".join(ftxt) or "no fleet figure"
    stxt = ("no service-share measure" if s25 is None else
            f"service share {s25 * 100:.0f}% (network {NET_SHARE * 100:.0f}%)" +
            ("" if share_chg is None else f", {share_chg * 100:+.1f} pts since 2023"))
    if k in CIS:
        return {"service": "not touched", "body": "not touched", "reasons": ["CIS basis is an open decision"],
                "fleet_chg": fleet_chg, "fwd": fwd, "s23": s23, "s25": s25, "share_chg": share_chg, "ageing": ageing,
                "weak": weak, "reacts": reacts}
    if k in IMPORTED:
        hold = True
        reasons.append("vehicles outside our fleet count (imports) also buy here — shown by parts no other market buys"
                       + (" and by service shares above what the counted fleet needs" if (s25 or 0) >= 0.45 else "")
                       + "; keeping service parts where they are is how the distributor wins that work")
    if reacts:
        hold = True
        reasons.append(f"dealers measurably bought less of a part after its April rise ({dr['beta']:+.2f}, ±{1.96 * dr['se']:.2f})")
    if ageing and weak:
        hold = True
        reasons.append(f"ageing fleet ({ftxt}) and weak service position ({stxt})")
    if k in COMPLAINT_SERVICE and weak:
        hold = True
        reasons.append(f"documented price complaint on service parts, with {stxt}")
    if not hold:
        if ageing:
            reasons.append(f"fleet is ageing ({ftxt}), but the service position holds ({stxt}): no case to hold")
        if k in COMPLAINT_SERVICE:
            reasons.append(f"a complaint is on file, but {stxt}: answer it with BVP or a targeted special price, not the list")
        if not reasons:
            reasons.append(f"{ftxt}; {stxt}: the fleet is growing, so none of the hold rules applies")
    if k in NOTE:
        reasons.append(NOTE[k])
    body = "hold body, collision and lighting" if k == "UMI" else "hold lighting" if k == "UTI" else "factory move"
    return {"service": "hold at today's price" if hold else "factory move", "body": body, "reasons": reasons,
            "fleet_chg": fleet_chg, "fwd": fwd, "s23": s23, "s25": s25, "share_chg": share_chg, "ageing": ageing,
            "weak": weak, "reacts": reacts}


ORDER = sorted(M, key=lambda k: -(M[k]["billed"].get("2025") or 0))
DEC = {k: decide(k, M[k]) for k in ORDER}

# grid cost
held_step, held_base = 0.0, 0.0
for k in ORDER:
    p = M[k].get("proposal", {})
    if DEC[k]["service"].startswith("hold"):
        held_step += (p.get("service") or {}).get("step") or 0
        held_base += (p.get("service") or {}).get("billed") or 0
    if k == "UMI":
        held_step += (p.get("body") or {}).get("step") or 0
        held_base += (p.get("body") or {}).get("billed") or 0
held_step += UTI_LIGHTING_STEP
held_base += 133712.0
rest_base = TOTAL_BASE - held_base
rest_now = (TOTAL_STEP - held_step) / rest_base
rest_needed = TOTAL_STEP / rest_base
total_if_accept = (TOTAL_STEP - held_step) / TOTAL_BASE

OVER_NOTE = ("<p class='muted' style='font-size:8.5px;margin:0'>* More than the counted fleet should need: vehicles we do not count "
             "(imports, or a fleet figure that is too low) buy here. Not a real share.</p>")

# ------------------------------------------------------------------ SVG helpers
INK, GRID, MUTED = "#1a2b4a", "#e1e0d9", "#6b6256"
BLUE, LBLUE, GREY, RED, GREEN, AMBER, TERRA = "#2a78d6", "#85b7eb", "#888780", "#e24b4a", "#1d9e75", "#eda100", "#c0552d"


def svg_seg_bars(m, w=330, h=150):
    segs = [("service", "Service parts"), ("repair", "Repair parts"), ("body", "Body & lighting")]
    vals = [((m["segments"].get(s) or {}).get("2023") or 0, (m["segments"].get(s) or {}).get("2025") or 0) for s, _ in segs]
    mx = max(max(a, b) for a, b in vals) or 1
    x0, bw, gap = 104, (w - 150), 44
    out = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Parts billed by group, 2023 against 2025">']
    for i, ((s, lab), (a, b)) in enumerate(zip(segs, vals)):
        y = 14 + i * gap
        out.append(f'<text x="0" y="{y + 15}" font-size="10" fill="{INK}">{lab}</text>')
        wa, wb = bw * a / mx, bw * b / mx
        out.append(f'<rect x="{x0}" y="{y}" width="{wa:.1f}" height="11" fill="{LBLUE}"/>')
        out.append(f'<rect x="{x0}" y="{y + 13}" width="{wb:.1f}" height="11" fill="{BLUE}"/>')
        chg = (b / a - 1) if a else None
        col = GREEN if chg is not None and chg >= 0 else RED
        out.append(f'<text x="{x0 + wb + 4:.1f}" y="{y + 22}" font-size="9" fill="{col}">{"" if chg is None else f"{chg * 100:+.0f}%"}</text>')
        out.append(f'<text x="{x0 + wa + 4:.1f}" y="{y + 9}" font-size="8" fill="{MUTED}">{a / 1000:,.0f}k</text>')
    out.append(f'<rect x="{x0}" y="{h - 12}" width="9" height="8" fill="{LBLUE}"/><text x="{x0 + 12}" y="{h - 5}" font-size="8.5" fill="{MUTED}">2023</text>')
    out.append(f'<rect x="{x0 + 46}" y="{h - 12}" width="9" height="8" fill="{BLUE}"/><text x="{x0 + 58}" y="{h - 5}" font-size="8.5" fill="{MUTED}">2025 (change vs 2023)</text>')
    out.append("</svg>")
    return "".join(out)


def svg_category(m, w=330, h=None):
    rows = (m.get("category_share") or [])[:7]
    if not rows:
        return '<p class="muted">No service-share measure for this market.</p>'
    h = h or 26 + len(rows) * 19
    x0, bw, xl = 118, 120, 118 + 120 + 8          # bar area, then a fixed label column: no label crosses a bar or the line
    out = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Service share by category, 2025, with change since 2023">']
    nx = x0 + bw * NET_SHARE / 1.2
    out.append(f'<line x1="{nx:.1f}" y1="2" x2="{nx:.1f}" y2="{h - 14}" stroke="{TERRA}" stroke-dasharray="3,2"/>')
    for i, (lab, s25, chg) in enumerate(rows):
        y = 8 + i * 19
        s = min(s25 or 0, 1.0)
        col = RED if (chg or 0) < -0.03 else GREEN if (chg or 0) > 0.03 else GREY
        out.append(f'<text x="0" y="{y + 10}" font-size="9.5" fill="{INK}">{html.escape(lab[:22])}</text>')
        out.append(f'<rect x="{x0}" y="{y}" width="{max(bw * s / 1.2, 1):.1f}" height="12" fill="{col}" opacity="0.85"/>')
        out.append(f'<text x="{xl}" y="{y + 10}" font-size="9" fill="{INK}">{share_txt(s25 or 0)}'
                   f'<tspan fill="{col}"> {(chg or 0) * 100:+.0f} pts</tspan></text>')
    out.append(f'<text x="{nx + 2:.1f}" y="{h - 3}" font-size="8" fill="{TERRA}">network {NET_SHARE * 100:.0f}%</text>')
    out.append("</svg>")
    if any((r[1] or 0) >= 0.995 for r in rows):
        out.append(OVER_NOTE)
    return "".join(out)


def svg_network_share(w=700):
    rows = [(k, DEC[k]["s25"], DEC[k]["share_chg"], DEC[k]["fleet_chg"] is not None and DEC[k]["fleet_chg"] <= 0.02)
            for k in ORDER if DEC[k]["share_chg"] is not None]
    rows.sort(key=lambda r: r[2])
    h = 30 + len(rows) * 20
    x_mid, scale = 330, 9.0   # px per point
    out = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Change in service share 2023 to 2025 by market">']
    out.append(f'<line x1="{x_mid}" y1="4" x2="{x_mid}" y2="{h - 20}" stroke="{GRID}"/>')
    for i, (k, s25, chg, ageing) in enumerate(rows):
        y = 6 + i * 20
        col = AMBER if ageing else BLUE
        bw = chg * 100 * scale
        xs = x_mid if bw >= 0 else x_mid + bw
        out.append(f'<text x="0" y="{y + 11}" font-size="10" fill="{INK}">{html.escape(NAME[k])}</text>')
        out.append(f'<rect x="{xs:.1f}" y="{y}" width="{abs(bw):.1f}" height="13" fill="{col}"/>')
        tx = x_mid + bw + 4 if bw >= 0 else x_mid + bw - 4
        anc = "start" if bw >= 0 else "end"
        out.append(f'<text x="{tx:.1f}" y="{y + 11}" font-size="9" fill="{INK}" text-anchor="{anc}">{chg * 100:+.1f} pts (now {share_txt(s25)})</text>')
    out.append(f'<rect x="{x_mid - 150}" y="{h - 13}" width="9" height="8" fill="{AMBER}"/><text x="{x_mid - 138}" y="{h - 6}" font-size="9" fill="{MUTED}">fleet flat or shrinking 2023-25</text>')
    out.append(f'<rect x="{x_mid + 10}" y="{h - 13}" width="9" height="8" fill="{BLUE}"/><text x="{x_mid + 22}" y="{h - 6}" font-size="9" fill="{MUTED}">fleet growing</text>')
    out.append("</svg>")
    return "".join(out)


def cell(val, kind):
    colors = {"good": "#d7efe4", "mid": "#fbeccc", "bad": "#f7d6d5", "na": "#eeeeea", "rec_hold": "#e2ecfb", "rec_move": "#ffffff"}
    return f'<td style="background:{colors[kind]}">{val}</td>'


# ------------------------------------------------------------------ page
css = """
*{box-sizing:border-box}html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;background:#fff}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:10.3px;line-height:1.45}
h1,h2,h3,h4{font-family:Georgia,serif;color:#1a2b4a;margin:0}
@page{size:A4;margin:14mm 13mm 18mm 13mm}@page:first{margin:0}
.cover{height:296mm;width:210mm;margin:0;padding:26mm 22mm;background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%);color:#eef1f6;break-after:page}
.cover h1{color:#fff;font-size:38px;line-height:1.1}.cover .rule{width:54mm;height:3px;background:#c0552d;margin:9mm 0 8mm}
.cover p{font-size:13px;max-width:150mm;color:#dfe5ee}
h2.sec{font-size:17px;margin:2mm 0 2mm;padding-bottom:2mm;border-bottom:2px solid #1a2b4a}
h2.sec .no{color:#c0552d}
.page{break-before:page}
table{width:100%;border-collapse:collapse;margin:2mm 0 3mm;font-size:8.8px}
th{background:#1a2b4a;color:#fff;text-align:left;padding:1.6mm;font-size:8px;text-transform:uppercase;vertical-align:bottom}
td{padding:1.4mm 1.6mm;border-bottom:.5px solid #d9d3c8;vertical-align:top}
tr{break-inside:avoid}
.callout{border-left:3px solid #c0552d;background:#f7f4ee;padding:3mm 4mm;margin:2.5mm 0;break-inside:avoid}
.cards{display:flex;gap:2.5mm;margin:2mm 0 2.5mm}
.card{flex:1;background:#f7f4ee;border-radius:2mm;padding:2mm 2.5mm}
.card .l{font-size:8.5px;color:#6b6256}.card .v{font-size:15px;font-weight:600;color:#1a2b4a}.card .s{font-size:8.5px}
.two{display:flex;gap:5mm}.two>div{flex:1}
.pill{display:inline-block;border-radius:3mm;padding:.8mm 2.5mm;margin-right:1.5mm;font-size:9.5px;font-weight:600}
.hold{background:#e2ecfb;color:#1a4f9c;border:1px solid #2a78d6}.move{background:#f7f4ee;color:#1a2b4a;border:1px solid #d9d3c8}
.nt{background:#eeeeea;color:#555;border:1px solid #ccc}
.muted{color:#6b6256}.good{color:#2e7d54}.bad{color:#b23b3b}
ul{margin:1mm 0 1mm 4mm;padding:0}li{margin:.4mm 0}
h3{font-size:12px;margin:2mm 0 1mm}
.foot{font-size:8px;color:#6b6256;border-top:.5px solid #d9d3c8;padding-top:1.5mm;margin-top:4mm}
"""

H = [f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>Market Pricing Exercise</title><style>{css}</style></head><body>"]
H.append("<div class='cover'><div style='font-size:12px;letter-spacing:2px;color:#9fb0c8'>ISZE · PARTS PRICING · INTERNAL</div>"
         "<h1>Market by market:<br>where the +5% should land</h1><div class='rule'></div>"
         f"<p>Twenty-one markets, each read on the same evidence: what it buys, how its fleet moves, how much of its service work we win, "
         f"what it pays against our list, and what dealers and distributors say. The proposal stays one list price per part; "
         f"the market layer is a distributor condition, which SAP already carries.</p>"
         f"<p style='margin-top:10mm'>30 September 2026 · a proposal on paper — no price, list or condition changed.</p></div>")

# ---- page 1: the answer
nh = sum(1 for k in ORDER if DEC[k]["service"].startswith("hold"))
H.append("<h2 class='sec'><span class='no'>1</span> The answer</h2>")
H.append(f"<div class='callout'><b>Service parts are where markets differ; repair parts are not.</b> In {nh} of 21 markets the evidence says keep "
         f"service parts (filters, brakes, clutch) at today's price: the fleet is ageing and we are losing the service work, dealers measurably "
         f"react, or the market runs on imported vehicles we do not even count. Repair parts follow their factory move everywhere — "
         f"that is where older fleets spend more and have no alternative. Israel adds one more hold: collision and lighting, because of the insurance total-loss rule.</div>")
H.append("<table><thead><tr><th>Market</th><th>Parts billed 2025</th><th>Fleet 2023→25</th><th>Fleet 2026 forecast</th><th>Service share 2025</th><th>Change since 2023</th>"
         "<th>Pays vs list (stock)</th><th>Urgent orders</th><th>Service parts</th><th>Body & lighting</th></tr></thead><tbody>")
for k in ORDER:
    m, d = M[k], DEC[k]
    fc = d["fleet_chg"]
    fk = "na" if fc is None else ("bad" if fc <= 0 else "mid" if fc < 0.1 else "good")
    s25 = d["s25"]
    sk = "na" if s25 is None else ("bad" if s25 < NET_SHARE * 0.8 else "mid" if s25 < NET_SHARE * 1.2 else "good")
    ch = d["share_chg"]
    ck = "na" if ch is None else ("bad" if ch < 0 else "mid" if ch < 0.05 else "good")
    sor = (m.get("pays_pct_list") or {}).get("SOR")
    ur = m.get("urgent_share")
    uk = "na" if ur is None else ("bad" if ur > 0.3 else "mid" if ur > 0.15 else "good")
    H.append("<tr>" + f"<td><b>{html.escape(NAME[k])}</b></td><td>EUR {(m['billed'].get('2025') or 0) / 1e6:.2f}M</td>"
             + cell("n/a" if fc is None else pct(fc, 0, True), fk)
             + cell("n/a" if d["fwd"] is None else pct(d["fwd"], 0, True),
                    "na" if d["fwd"] is None else ("bad" if d["fwd"] <= -0.03 else "mid" if d["fwd"] < 0.03 else "good"))
             + cell(share_txt(s25), sk)
             + cell("n/a" if ch is None else f"{ch * 100:+.1f} pts", ck)
             + cell("n/a" if sor is None else f"{sor:.1f}%", "na")
             + cell("n/a" if ur is None else pct(ur, 0), uk)
             + cell(d["service"], "rec_hold" if d["service"].startswith("hold") else "rec_move" if d["service"] == "factory move" else "na")
             + cell(d["body"], "rec_hold" if d["body"].startswith("hold") else "rec_move" if d["body"] == "factory move" else "na") + "</tr>")
H.append("</tbody></table>")
H.append(f"<p class='muted'>Colours: fleet red = flat or shrinking; service share red = below 80% of the network's {NET_SHARE * 100:.0f}%; "
         f"change red = falling; urgent orders red = over 30% of the market's euro on rush or vehicle-off-road orders, which are billed above list. "
         f"Repair parts: factory move in every market.</p>")
H.append("<div class='page' style='break-inside:avoid'>")
H.append("<h3>What the market layer costs, and who carries it</h3>")
H.append(f"<div class='cards'><div class='card'><div class='l'>Extra euro in the current proposal</div><div class='v'>{eur(TOTAL_STEP)}</div><div class='s muted'>+5.00% on {eur(TOTAL_BASE)}</div></div>"
         f"<div class='card'><div class='l'>Given up by the holds</div><div class='v'>{eur(held_step)}</div><div class='s muted'>{held_step / TOTAL_STEP * 100:.1f}% of the extra euro</div></div>"
         f"<div class='card'><div class='l'>Either: other parts carry it</div><div class='v'>{rest_needed * 100:+.1f}%</div><div class='s muted'>instead of {rest_now * 100:+.1f}%, total stays +5.0%</div></div>"
         f"<div class='card'><div class='l'>Or: accept a lower total</div><div class='v'>{total_if_accept * 100:+.1f}%</div><div class='s muted'>on the whole book</div></div></div>")
H.append("<h3>Across all markets: flat or shrinking fleets win the least service work</h3>")
H.append(svg_network_share())
H.append("<p class='muted'>Service share = the service parts a market's distributor bought, against what its fleet should need at the service intervals. "
         "A growing fleet raises that yardstick, which works against it — and growing fleets still gained most. Across the 18 markets with a measure, "
         "the rank correlation between fleet change 2023-25 and share change is +0.49. The hold decisions also use the 2026 fleet forecast, "
         "which is why Belgium, Ireland and UMI can be read as ageing on their market pages.</p></div>")

# ---- market pages
for i, k in enumerate(ORDER, start=2):
    m, d = M[k], DEC[k]
    b = m["billed"]
    b23, b25 = b.get("2023"), b.get("2025")
    f = m.get("fleet", {})
    H.append(f"<div class='page'><h2 class='sec'><span class='no'>{i}</span> {html.escape(NAME[k])} <span class='muted' style='font-size:11px'>· {html.escape(DIST[k])}</span></h2>")
    sp = "hold" if d["service"].startswith("hold") else "nt" if d["service"] == "not touched" else "move"
    bp = "hold" if d["body"].startswith("hold") else "nt" if d["body"] == "not touched" else "move"
    rp = "nt" if k in CIS else "move"
    H.append(f"<div style='margin:1mm 0 2mm'><span class='pill {sp}'>Service parts: {d['service']}</span>"
             f"<span class='pill {rp}'>Repair parts: {'not touched' if k in CIS else 'factory move'}</span>"
             f"<span class='pill {bp}'>Body & lighting: {d['body']}</span></div>")
    sor = (m.get("pays_pct_list") or {})
    cards = [("Parts billed 2025", eur(b25), "" if not b23 else f"{(b25 / b23 - 1) * 100:+.0f}% vs 2023"),
             ("Official fleet 2025", "n/a" if not f.get("2025") else f"{f['2025']:,.0f}",
              ("" if d["fleet_chg"] is None else f"{d['fleet_chg'] * 100:+.0f}% vs 2023") + ("" if d["fwd"] is None else f"; 2026: {d['fwd'] * 100:+.0f}%")),
             ("Service share 2025", share_txt(d["s25"]),
              "" if d["share_chg"] is None else f"{d['share_chg'] * 100:+.1f} pts vs 2023 · network {NET_SHARE * 100:.0f}%"),
             ("Pays vs list, stock orders", "n/a" if not sor.get("SOR") else f"{sor['SOR']:.1f}%",
              ("" if not sor.get("VOR") else f"off-road orders {sor['VOR']:.0f}%") + ("" if m.get("urgent_share") is None else f" · urgent {m['urgent_share'] * 100:.0f}% of euro"))]
    H.append("<div class='cards'>" + "".join(f"<div class='card'><div class='l'>{a}</div><div class='v'>{v}</div><div class='s muted'>{s}</div></div>" for a, v, s in cards) + "</div>")
    H.append("<div class='two'><div><h3>What it buys, 2023 against 2025</h3>" + svg_seg_bars(m) + "</div>"
             "<div><h3>Service share by category, 2025</h3>" + svg_category(m) + "</div></div>")
    up = ", ".join(f"{a} +{v / 1000:,.0f}k" for a, v in (m.get("family_up") or []) if a not in ("Unknown", "Unclassified"))
    dn = ", ".join(f"{a} {v / 1000:,.0f}k" for a, v in (m.get("family_down") or []) if a not in ("Unknown", "Unclassified"))
    pe, ve = m.get("price_effect_23_25"), m.get("volume_effect_23_25")
    gen = (m["service_share"].get("2025") or {}) if m.get("service_share") else {}
    gshare = (gen.get("genuine") / gen.get("total")) if gen.get("total") else None
    H.append("<div class='two'><div><h3>What drives it</h3><ul>")
    if up:
        H.append(f"<li>Grew most: {html.escape(up)}.</li>")
    if dn:
        H.append(f"<li>Fell most: {html.escape(dn)}.</li>")
    if pe is not None:
        H.append(f"<li>On parts bought in both years: {'+' if ve >= 0 else ''}{ve / 1000:,.0f}k from quantity, {'+' if pe >= 0 else ''}{pe / 1000:,.0f}k from price.</li>")
    if gshare is not None:
        H.append(f"<li>Genuine is {gshare * 100:.0f}% of the service parts it buys; the rest is BVP.</li>")
    per_v = (m["pns_2025"] / f["2025"]) if f.get("2025") else None
    H.append(f"<li>{m['pns_2025']:,} different part numbers in 2025{'' if per_v is None else f' ({per_v:.2f} per official vehicle)'}; "
             f"{m['only_here_share_23_25'] * 100:.1f}% of 2023-25 billing on {m['only_here_pns']} part numbers no other market bought"
             f"{'' if not m.get('only_here_examples') else ' (e.g. ' + html.escape(', '.join(m['only_here_examples'][:3]).lower()) + ')'}.</li>")
    if m.get("dealer_response"):
        dr = m["dealer_response"]
        H.append(f"<li>Dealer response to the April 2026 increase: {dr['beta']:+.2f} (±{1.96 * dr['se']:.2f}); dealer units {dr['units_change'] * 100:+.1f}% "
                 f"over the same months.</li>")
    H.append("</ul></div><div><h3>What is specific here</h3><ul>" + "".join(f"<li>{html.escape(t)}</li>" for t in CTX.get(k, [])) + "</ul></div></div>")
    p = m.get("proposal", {})
    H.append("<h3>Why this recommendation, and what it does</h3><ul>" + "".join(f"<li>{html.escape(r)}.</li>" for r in d["reasons"]))
    rows = []
    for s, lab in (("service", "Service parts"), ("repair", "Repair parts"), ("body", "Body & lighting")):
        q = p.get(s)
        if q and q.get("billed"):
            rows.append(f"{lab}: {eur(q['billed'])} billed, factory move {pct(q['factory'], 1, True)}, proposal {pct(q['proposed'], 1, True)} = {eur(q['step'])}")
    if rows:
        H.append("<li>Today's proposal on this market: " + "; ".join(rows) + ".</li>")
    if d["service"].startswith("hold") and p.get("service"):
        H.append(f"<li>Holding service parts gives up {eur(p['service']['step'])} here.</li>")
    if (m.get("urgent_share") or 0) > 0.3:
        H.append(f"<li>Also: {m['urgent_share'] * 100:.0f}% of this market's euro goes through urgent orders billed at up to "
                 f"{max(v for v in sor.values()):.0f}% of list — a terms question worth as much as the list price.</li>")
    H.append("</ul></div>")

H.append("<div class='page'><h2 class='sec'><span class='no'>*</span> How to read this, and what it does not rest on</h2><ul>"
         "<li>The price list stays one price per part: every part follows its own factory base-price change, scaled so the book lands on +5%, with the pad kits held. "
         "A 'hold' here is applied as a distributor condition on that part group, the way stock-order and customer conditions already differ today "
         "(Norway pays 95.6% of list on stock orders, Germany 99.8%, UTI 86.0%).</li>"
         "<li>Service parts = the fourteen maintenance categories (filters, brakes, clutch) plus parts flagged as maintenance; body & lighting = accident and body parts; repair = everything else.</li>"
         "<li>Rules behind 'hold' on service parts: imported vehicles we do not count; or dealers measurably reacted to the April 2026 rise; "
         "or the fleet is flat/shrinking and our service share is below the network or falling; or a documented price complaint on service parts together with a low or falling share.</li>"
         "<li>Fleet figures are the planning estimates behind the service-share measure; only the UK D-Max fleet is a locked count. Fleet age by market is not on file "
         "(only the UK truck fleet has registrations by year). Imported-vehicle numbers for Malta and Cyprus are for all vehicles, not Isuzu.</li>"
         "<li>Figures cover parts only: transport charges, rebates, credits and lubricants are left out.</li></ul>"
         "<div class='foot'>Sources: SAP parts billing 2023–Aug 2026; the in-scope revision base behind the +5% proposal; dated PR00 price lists; the service-share measure by market and category; "
         "fleet planning estimates (July 2026, corrected 2026 column); sales-to-dealer files for the UK, Ireland and Portugal; distributor review minutes July–August 2026; "
         "IMIE monthly market packs (June/July 2026); pickup and pricing research notes (September 2026); Cyprus Statistical Service (registrations Jan–Jul 2025); "
         "Newsbook Malta, 4 March 2026 (used imports, from the Transport Minister). Indicative — a basis for decisions, not a price change.</div></div>")
H.append("</body></html>")
OUT.write_text("".join(H), encoding="utf-8")
(OUT_DIR / "OPEN_ISZE_Market_Pricing_Exercise_2026-09-30.cmd").write_text(
    '@echo off\r\nstart "" "%~dp0ISZE_Market_Pricing_Exercise_2026-09-30.html"\r\n', encoding="ascii")
summary = {k: {"service": DEC[k]["service"], "body": DEC[k]["body"], "reasons": DEC[k]["reasons"]} for k in ORDER}
(HERE / "market_exercise_decisions_2026-09-30.json").write_text(json.dumps({
    "held_step": held_step, "held_base": held_base, "rest_now": rest_now, "rest_needed": rest_needed,
    "total_if_accept": total_if_accept, "decisions": summary}, indent=1), encoding="utf-8")
print("written", OUT)
print(f"held step EUR {held_step:,.0f} ({held_step / TOTAL_STEP:.1%}); rest now {rest_now:.2%} needed {rest_needed:.2%}; total if accepted {total_if_accept:.2%}")
for k in ORDER:
    print(f"{k:11s} service={DEC[k]['service']:22s} body={DEC[k]['body']:34s} | " + "; ".join(DEC[k]["reasons"]))
