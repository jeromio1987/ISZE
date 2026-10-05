# -*- coding: utf-8 -*-
"""Inline-SVG charts for the Isuzu Universe white paper (final edition).

Every chart reads its numbers from the derived source files at build time.
Palette: charcoal + Isuzu red. Red always marks the figure the text is about.
"""
import csv
import os
from html import escape

DERIVED = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
TENDERS = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json"

CHAR = "#24282C"
RED = "#D71920"
MID = "#6B7078"
LIGHT = "#B9BDC3"
GRID = "#E4E5E7"
INK = "#1E2124"
FONT = "Arial, Helvetica, sans-serif"
W = 680


def load(name):
    with open(os.path.join(DERIVED, name), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def eur(v, dec=0):
    return "€" + f"{v:,.{dec}f}"


def eurk(v):
    if v >= 1e6:
        return f"€{v / 1e6:.2f}M"
    return f"€{v / 1e3:,.0f}k"


def t(x, y, s, size=11, fill=INK, anchor="start", weight="normal", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" {extra}>{escape(str(s))}</text>')


def svg(h, body, label):
    return (f'<svg viewBox="0 0 {W} {h}" width="100%" role="img" aria-label="{escape(label)}" '
            f'xmlns="http://www.w3.org/2000/svg" style="display:block">{body}</svg>')


def nice_max(v):
    for step in (1, 2, 2.5, 5):
        for mag in range(0, 10):
            m = step * 10 ** mag
            if m >= v:
                return m
    return v


# ------------------------------------------------------------------ data
def ituk_portugal_iuk():
    out = {}
    for r in load("pms_genuine_bvp_vs_price_2024_2025.csv"):
        key = (r["distributor_code"], r["product_subgroup"])
        out[key] = r
    return out


def concession_db(year):
    return [r for r in load("pms_campaign_suspect_by_db_2024_2025.csv") if r["year"] == year]


def concession_family(year):
    return [r for r in load("pms_campaign_suspect_by_family_2024_2025.csv") if r["year"] == year]


def concession_db_family(db, fam):
    return {r["year"]: r for r in load("pms_campaign_suspect_by_db_family_2024_2025.csv")
            if r["distributor_code"] == db and r["pms_category"] == fam}


def ids_rows():
    return load("ids_dealer_network_cleaned_2026-09-20.csv")


def gps_2025():
    return [r for r in load("gps_spu_by_distributor.csv") if r["year"] == "2025"]


def elasticity():
    return {r["family"]: r for r in load("pms_price_volume_response_2024_2025.csv")}


def tender_stats():
    import json
    m = json.load(open(TENDERS, encoding="utf-8"))["meta"]
    return m["stats"], m["decision_counts"], m["outcomes_summary"]


# ------------------------------------------------------------------ primitives
def paired_bars(panels, h=250, dark=False):
    """panels: list of (title, v2024, v2025, fmt). Two-bar small multiples, 2025 in red."""
    ink = "#E9EAEC" if dark else INK
    sub = "#A9AEB5" if dark else MID
    base = "#5A6068" if dark else LIGHT
    n = len(panels)
    pw = W / n
    body = []
    top, bottom = 58, h - 34
    for i, (title, a, b, fmt) in enumerate(panels):
        x0 = i * pw
        mx = max(a, b) * 1.12
        body.append(t(x0 + 20, 20, title, 12, sub, weight="bold"))
        pct = (b - a) / a * 100
        body.append(t(x0 + pw - 24, 22, f"{pct:+.1f}%", 22, RED, "end", "bold"))
        bw = 84
        for j, (lab, v, col) in enumerate((("2024", a, base), ("2025", b, RED))):
            cx = x0 + 60 + j * 130
            bh = (bottom - top) * v / mx
            body.append(f'<rect x="{cx:.1f}" y="{bottom - bh:.1f}" width="{bw}" height="{bh:.1f}" fill="{col}" rx="2"/>')
            body.append(t(cx + bw / 2, bottom - bh - 7, fmt(v), 12, ink, "middle", "bold"))
            body.append(t(cx + bw / 2, bottom + 18, lab, 11, sub, "middle"))
        body.append(f'<line x1="{x0 + 40}" y1="{bottom}" x2="{x0 + pw - 30}" y2="{bottom}" stroke="{sub}" stroke-width="0.8"/>')
    return svg(h, "".join(body), " / ".join(p[0] for p in panels))


def hbars(items, fmt, h=None, label_w=190, value_w=150, title=None, maxv=None, note_fn=None):
    """items: list of (label, value, highlight_bool). Horizontal ranked bars."""
    row = 28
    top = 34 if title else 8
    h = h or top + row * len(items) + 16
    mx = maxv or nice_max(max(v for _, v, _ in items) * 1.05)
    plot_w = W - label_w - value_w
    body = []
    if title:
        body.append(t(0, 16, title, 12, MID, weight="bold"))
    for i, (lab, v, hi) in enumerate(items):
        y = top + i * row
        bw = max(plot_w * v / mx, 1.5)
        body.append(t(label_w - 10, y + 15, lab, 11.5, INK, "end", "bold" if hi else "normal"))
        body.append(f'<rect x="{label_w}" y="{y + 3}" width="{bw:.1f}" height="18" fill="{RED if hi else LIGHT}" rx="2"/>')
        txt = fmt(v) + (("   " + note_fn(lab, v)) if note_fn else "")
        body.append(t(label_w + bw + 8, y + 16, txt, 11, INK if hi else MID, weight="bold" if hi else "normal"))
    return svg(h, "".join(body), title or "ranked bars")


# ------------------------------------------------------------------ figures
def cover_argument():
    d = ituk_portugal_iuk()[("ITUK", "brake_pad")]
    return paired_bars([
        ("Parts billed", float(d["total_eur_2024"]), float(d["total_eur_2025"]), lambda v: eur(v)),
        ("Units", float(d["total_qty_2024"]), float(d["total_qty_2025"]), lambda v: f"{v:,.0f}"),
    ], h=240, dark=True)


def fig_brake_pads():
    d = ituk_portugal_iuk()[("ITUK", "brake_pad")]
    return paired_bars([
        ("Parts billed (EUR)", float(d["total_eur_2024"]), float(d["total_eur_2025"]), lambda v: eur(v)),
        ("Units billed", float(d["total_qty_2024"]), float(d["total_qty_2025"]), lambda v: f"{v:,.0f}"),
    ], h=250)


def brake_split_values():
    d = ituk_portugal_iuk()
    out = []
    for sub, lab in (("brake_pad", "Brake pads"), ("brake_rotor", "Brake rotors"), ("brake_shoe", "Brake shoes")):
        r = d[("ITUK", sub)]
        out.append((lab, float(r["total_eur_2024"]) - float(r["total_eur_2025"])))
    return out


def fig_brake_split():
    vals = brake_split_values()
    items = [(lab, v, i == 0) for i, (lab, v) in enumerate(vals)]
    return hbars(items, lambda v: eur(v), label_w=130, value_w=120, maxv=50000,
                 title="Reduction in parts billed, 2025 against 2024")


def portugal_values():
    r = ituk_portugal_iuk()[("PORTUGAL", "clutch_kit")]
    return {k: float(r[k]) for k in ("genuine_eur_2024", "genuine_eur_2025", "bvp_eur_2024", "bvp_eur_2025",
                                     "total_eur_2024", "total_eur_2025", "total_qty_2024", "total_qty_2025")}


def fig_portugal():
    p = portugal_values()
    h, top, bottom = 250, 40, 205
    mx = 36000
    body = [t(0, 16, "Clutch kits billed to the Portuguese distributor (EUR)", 12, MID, weight="bold")]
    for j, (yr, g, b, q) in enumerate((("2024", p["genuine_eur_2024"], p["bvp_eur_2024"], p["total_qty_2024"]),
                                      ("2025", p["genuine_eur_2025"], p["bvp_eur_2025"], p["total_qty_2025"]))):
        cx = 150 + j * 200
        gh = (bottom - top) * g / mx
        bh = (bottom - top) * b / mx
        body.append(f'<rect x="{cx}" y="{bottom - gh:.1f}" width="96" height="{gh:.1f}" fill="{RED}"/>')
        body.append(f'<rect x="{cx}" y="{bottom - gh - bh:.1f}" width="96" height="{bh:.1f}" fill="{LIGHT}"/>')
        body.append(t(cx + 48, bottom - gh - bh - 8, eur(g + b), 12, INK, "middle", "bold"))
        body.append(t(cx + 48, bottom - gh - bh / 2 + 4, f"Best Value {eurk(b)}", 10.5, INK, "middle"))
        body.append(t(cx + 110, bottom - gh / 2 + 4, f"Genuine {eurk(g)}", 10.5, RED, "start", "bold"))
        body.append(t(cx + 48, bottom + 18, f"{yr}  ·  {q:,.0f} kits", 11, MID, "middle"))
    pct = (p["total_eur_2025"] - p["total_eur_2024"]) / p["total_eur_2024"] * 100
    gp = (p["genuine_eur_2025"] - p["genuine_eur_2024"]) / p["genuine_eur_2024"] * 100
    body.append(t(W - 4, 70, f"Total {pct:+.1f}%", 20, INK, "end", "bold"))
    body.append(t(W - 4, 96, f"Genuine {gp:+.1f}%", 20, RED, "end", "bold"))
    body.append(f'<line x1="120" y1="{bottom}" x2="{W - 150}" y2="{bottom}" stroke="{MID}" stroke-width="0.8"/>')
    return svg(h, "".join(body), "Portugal clutch kits genuine and best value")


def fig_family_ranked():
    rows = sorted(concession_family("2025"), key=lambda r: -float(r["billed_eur"]))[:10]
    label = {"brake_rotor": "Brake rotors", "fuel_filter": "Fuel filters", "air_filter": "Air filters",
             "brake_pad": "Brake pads", "oil_filter": "Oil filters", "brake_pad_front": "Brake pads, front",
             "blower_filter": "Blower filters", "leaf_spring": "Leaf springs", "clutch_kit": "Clutch kits",
             "clutch_disc": "Clutch discs"}
    row, top, lw = 30, 44, 150
    h = top + row * len(rows) + 10
    bill_w = 265
    mx = 1400000
    body = [t(0, 16, "2025 billing (bars) and share billed at least 20% under the reference price (dots)", 12, MID, weight="bold"),
            t(lw + bill_w + 40, 36, "0%", 10, MID, "middle"), t(lw + bill_w + 40 + 150, 36, "40%", 10, MID, "middle")]
    sx0, sw = lw + bill_w + 40, 150
    body.append(f'<line x1="{sx0}" y1="{top - 2}" x2="{sx0}" y2="{h - 8}" stroke="{GRID}"/>')
    body.append(f'<line x1="{sx0 + sw * 0.5}" y1="{top - 2}" x2="{sx0 + sw * 0.5}" y2="{h - 8}" stroke="{GRID}"/>')
    body.append(f'<line x1="{sx0 + sw}" y1="{top - 2}" x2="{sx0 + sw}" y2="{h - 8}" stroke="{GRID}"/>')
    for i, r in enumerate(rows):
        y = top + i * row
        b = float(r["billed_eur"])
        s = float(r["pct_eur_ge20_under_ref"])
        hi = s >= 20
        bw = bill_w * b / mx
        body.append(t(lw - 10, y + 15, label.get(r["pms_category"], r["pms_category"]), 11.5, INK, "end", "bold" if hi else "normal"))
        body.append(f'<rect x="{lw}" y="{y + 4}" width="{bw:.1f}" height="17" fill="{CHAR if not hi else RED}" rx="2" opacity="{0.85 if not hi else 1}"/>')
        body.append(t(lw + bw + 6, y + 16, eurk(b), 10.5, MID))
        cx = sx0 + sw * min(s, 40) / 40
        body.append(f'<line x1="{sx0}" y1="{y + 12}" x2="{cx:.1f}" y2="{y + 12}" stroke="{LIGHT}" stroke-width="1.5"/>')
        body.append(f'<circle cx="{cx:.1f}" cy="{y + 12}" r="6" fill="{RED if hi else MID}"/>')
        body.append(t(sx0 + sw + 14, y + 16, f"{s:.1f}%", 11, RED if hi else MID, weight="bold" if hi else "normal"))
    return svg(h, "".join(body), "Ranked PMS families 2025")


NAMES = {"UKRAINE": "Ukraine", "PORTUGAL": "Portugal", "IUK": "Isuzu UK", "GERMANY": "Germany", "SWEDEN": "Sweden",
         "IRELAND": "Ireland", "DENMARK": "Denmark", "MIDI": "Midi", "CYPRUS": "Cyprus", "NORWAY": "Norway",
         "PALESTINE": "Palestine", "ITUK": "Isuzu Truck UK", "GREECE": "Greece", "ICELAND": "Iceland",
         "BELGIUM": "Belgium", "MALTA": "Malta", "FINLAND": "Finland", "UMI": "Israel (UMI)",
         "KAZAKHSTAN": "Kazakhstan", "ARMENIA": "Armenia", "HUNGARY": "Hungary", "ROMANIA": "Romania",
         "UTI": "Israel (UTI)", "GERMANY_SERVICE": "Germany (service)"}


def fig_concession_db():
    rows = sorted(concession_db("2025"), key=lambda r: -float(r["pct_eur_ge20_under_ref"]))[:12]
    items = [(NAMES.get(r["distributor_code"], r["distributor_code"]), float(r["pct_eur_ge20_under_ref"]),
              float(r["billed_eur"]) < 500000 and float(r["pct_eur_ge20_under_ref"]) >= 15) for r in rows]
    billed = {NAMES.get(r["distributor_code"], r["distributor_code"]): float(r["billed_eur"]) for r in rows}
    return hbars(items, lambda v: f"{v:.1f}%", label_w=140, value_w=190, maxv=30,
                 title="Share of 2025 maintenance-parts billing at least 20% under the reference price",
                 note_fn=lambda lab, v: f"of {eurk(billed[lab])} billed")


def concession_totals(year):
    rows = concession_db(year)
    tot = sum(float(r["billed_eur"]) for r in rows)
    g20 = sum(float(r["billed_eur"]) * float(r["pct_eur_ge20_under_ref"]) / 100 for r in rows)
    g30 = sum(float(r["billed_eur"]) * float(r["pct_eur_ge30_under_ref"]) / 100 for r in rows)
    return {"n": len(rows), "billed": tot, "ge20": g20, "ge20_pct": g20 / tot * 100, "ge30_pct": g30 / tot * 100}


def iuk_air():
    d = concession_db_family("IUK", "air_filter")
    return {y: (float(d[y]["billed_eur"]), float(d[y]["pct_eur_ge20_under_ref"])) for y in ("2024", "2025")}


def fig_iuk_air():
    d = iuk_air()
    return paired_bars([
        ("Air filters billed to Isuzu UK", d["2024"][0], d["2025"][0], lambda v: eurk(v)),
        ("Share at least 20% under reference", d["2024"][1], d["2025"][1], lambda v: f"{v:.1f}%"),
    ], h=240)


def fig_scope_effect():
    items = [("Unchanged offer: 100 units at €100", 3000, MID),
             ("Deal of the Day, 5% off all 120 units", 3000, LIGHT),
             ("Deal of the Day, 5% off the 20 extra units only", 3500, RED)]
    h, lw = 150, 300
    body = [t(0, 16, "Parts gross profit on the same 120 units (EUR)", 12, MID, weight="bold")]
    for i, (lab, v, col) in enumerate(items):
        y = 32 + i * 38
        bw = 300 * v / 3600
        body.append(t(lw - 10, y + 18, lab, 11.5, INK, "end", "bold" if col == RED else "normal"))
        body.append(f'<rect x="{lw}" y="{y + 3}" width="{bw:.1f}" height="24" fill="{col}" rx="2"/>')
        body.append(t(lw + bw + 8, y + 20, eur(v), 13, RED if col == RED else INK, weight="bold"))
    return svg(h, "".join(body), "Scope effect of the concession")


def uplift_needed(base, support, gp_after=0.25):
    return support / (base * gp_after) * 100


def fig_size_floor():
    """Uplift needed for one Deal of the Day to pay back its own support cost."""
    h, l, r, top, bottom = 300, 64, 150, 36, 250
    xs = [50000, 100000, 150000, 200000, 300000, 400000]
    xmin, xmax, ymax = 50000, 400000, 40
    def px(x):
        return l + (W - l - r) * (x - xmin) / (xmax - xmin)
    def py(y):
        return bottom - (bottom - top) * y / ymax
    body = [t(0, 16, "Extra sales needed to pay back the support, as % of the eligible billing base", 12, MID, weight="bold")]
    for yv in (0, 10, 20, 30, 40):
        body.append(f'<line x1="{l}" y1="{py(yv):.1f}" x2="{W - r}" y2="{py(yv):.1f}" stroke="{GRID}"/>')
        body.append(t(l - 8, py(yv) + 4, f"{yv}%", 10.5, MID, "end"))
    for xv in (50000, 100000, 150000, 200000, 300000, 400000):
        body.append(t(px(xv), bottom + 18, f"€{xv // 1000}k", 10.5, MID, "middle"))
    body.append(t((l + W - r) / 2, bottom + 40, "Eligible billing base of one Deal of the Day", 11, MID, "middle"))
    fl = px(150000)
    body.append(f'<rect x="{fl:.1f}" y="{top}" width="{W - r - fl:.1f}" height="{bottom - top}" fill="{RED}" opacity="0.06"/>')
    body.append(f'<line x1="{fl:.1f}" y1="{top}" x2="{fl:.1f}" y2="{bottom}" stroke="{RED}" stroke-width="1.5" stroke-dasharray="4 3"/>')
    body.append(t(fl + 6, top + 14, "proposed floor €150k", 11, RED, weight="bold"))
    import math
    for support, col in ((5000, CHAR), (2500, RED)):
        pts = []
        x = xmin
        while x <= xmax:
            pts.append(f"{px(x):.1f},{py(min(uplift_needed(x, support), ymax)):.1f}")
            x += 5000
        body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        yend = uplift_needed(xmax, support)
        body.append(t(W - r + 8, py(yend) + 4, f"{eur(support)} support", 11, col, weight="bold"))
        v150 = uplift_needed(150000, support)
        body.append(f'<circle cx="{fl:.1f}" cy="{py(v150):.1f}" r="4.5" fill="{col}"/>')
        body.append(t(fl + 9, py(v150) - 8, f"{v150:.1f}%", 11.5, col, "start", "bold"))
    return svg(h, "".join(body), "Size floor for a Deal of the Day")


def fig_network_billing():
    rows = sorted(gps_2025(), key=lambda r: -float(r["total_sales_eur"] or 0))
    items = [(NAMES.get(r["distributor_code"], r["distributor_code"].title()), float(r["total_sales_eur"]), i < 3)
             for i, r in enumerate(rows)]
    return hbars(items, eurk, label_w=140, value_w=80, maxv=7000000,
                 title="Parts billed to each distributor, calendar 2025")


def network_total():
    rows = gps_2025()
    return len(rows), sum(float(r["total_sales_eur"] or 0) for r in rows)


def fig_denominator():
    n, tot = network_total()
    items = [("€100,000 route", 100000), ("€300,000 route", 300000),
             ("Don't Lose the Deal, 3 markets", 90000), ("Don't Lose the Deal, 19 markets", 570000)]
    items = sorted(items, key=lambda x: x[1])
    row, top, lw = 34, 36, 230
    h = top + row * len(items) + 30
    plot = W - lw - 90
    mx = 2.0
    body = [t(0, 16, f"Each envelope as a share of {eur(tot / 1e6, 1).replace('€', '€')}M parts billed in 2025", 12, MID, weight="bold")]
    for xv in (0, 0.5, 1.0, 1.5, 2.0):
        x = lw + plot * xv / mx
        body.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - 26}" stroke="{GRID}"/>')
        body.append(t(x, h - 10, f"{xv:.1f}%", 10.5, MID, "middle"))
    for i, (lab, v) in enumerate(items):
        y = top + i * row
        pct = v / tot * 100
        hi = "route" in lab
        bw = plot * pct / mx
        body.append(t(lw - 10, y + 17, lab, 11.5, INK, "end", "bold" if hi else "normal"))
        body.append(f'<rect x="{lw}" y="{y + 4}" width="{bw:.1f}" height="20" fill="{RED if hi else LIGHT}" rx="2"/>')
        body.append(t(lw + bw + 8, y + 19, f"{pct:.2f}%", 12, RED if hi else MID, weight="bold"))
    return svg(h, "".join(body), "Envelopes against parts billed")


def fig_hurdle():
    contribs = [500, 1000, 2500, 5000]
    h, l, top, bottom = 280, 60, 40, 232
    ymax = 600
    gw = (W - l - 20) / len(contribs)
    body = [t(0, 16, "Beneficial actions needed to earn back each envelope", 12, MID, weight="bold")]
    for yv in (0, 200, 400, 600):
        y = bottom - (bottom - top) * yv / ymax
        body.append(f'<line x1="{l}" y1="{y:.1f}" x2="{W - 10}" y2="{y:.1f}" stroke="{GRID}"/>')
        body.append(t(l - 8, y + 4, str(yv), 10.5, MID, "end"))
    for i, c in enumerate(contribs):
        gx = l + i * gw + gw / 2
        for j, (env, col) in enumerate(((100000, RED if c == 2500 else CHAR), (300000, LIGHT))):
            v = env / c
            bh = (bottom - top) * v / ymax
            x = gx - 46 + j * 48
            body.append(f'<rect x="{x:.1f}" y="{bottom - bh:.1f}" width="44" height="{bh:.1f}" fill="{col}" rx="2"/>')
            body.append(t(x + 22, bottom - bh - 6, f"{v:,.0f}", 12, RED if col == RED else INK, "middle", "bold"))
        body.append(t(gx, bottom + 18, f"{eur(c)} per action", 11, INK if c != 2500 else RED, "middle",
                      "bold" if c == 2500 else "normal"))
    body.append(f'<rect x="{W - 250}" y="30" width="12" height="12" fill="{CHAR}"/>')
    body.append(t(W - 232, 40, "€100,000 route", 10.5, INK))
    body.append(f'<rect x="{W - 140}" y="30" width="12" height="12" fill="{LIGHT}"/>')
    body.append(t(W - 122, 40, "€300,000 route", 10.5, INK))
    return svg(h, "".join(body), "Hurdle actions")


def fig_price_of_dealer():
    per = [("Spread over all 519 dealers", 15000 / 519, False), ("Isuzu Truck UK + Portugal (60 dealers)", 15000 / 60, False),
           ("Portugal only (16 dealers)", 15000 / 16, False), ("25 accepted setup tasks", 600, True)]
    return hbars(per, lambda v: eur(v, 2) if v < 100 else eur(v), label_w=260, value_w=90, maxv=1000,
                 title="What €15,000 of dealer enablement buys, per dealer")


def ids_stats():
    """A score of zero means the 195-question assessment was never carried out, so it is not a low
    score. Those records are counted separately and excluded from the average and the distribution."""
    rows = ids_rows()
    scored = [float(r["points_pct"]) for r in rows if r["points_pct"].strip()]
    vals = [v for v in scored if v > 0]
    nets = {}
    for r in rows:
        k = r["ids_tab"]
        a = nets.setdefault(k, [0, 0, 0])
        a[0] += 1
        if r["points_pct"].strip():
            if float(r["points_pct"]) > 0:
                a[1] += 1
            else:
                a[2] += 1
    return {"rows": len(rows), "names": len(set(r["dealer_name"] for r in rows)),
            "scored": len(vals), "unassessed": len(scored) - len(vals),
            "avg": sum(vals) / len(vals), "min": min(vals), "max": max(vals),
            "scores": vals, "nets": nets}


def fig_ids_hist():
    s = ids_stats()["scores"]
    bins = [0] * 10
    for v in s:
        bins[min(int(v // 10), 9)] += 1
    h, l, top, bottom = 250, 50, 36, 206
    ymax = 120
    bw = (W - l - 20) / 10
    body = [t(0, 16, "Dealers by recorded Dealer Standards score", 12, MID, weight="bold")]
    for yv in (0, 40, 80, 120):
        y = bottom - (bottom - top) * yv / ymax
        body.append(f'<line x1="{l}" y1="{y:.1f}" x2="{W - 10}" y2="{y:.1f}" stroke="{GRID}"/>')
        body.append(t(l - 8, y + 4, str(yv), 10.5, MID, "end"))
    for i, c in enumerate(bins):
        bh = (bottom - top) * c / ymax
        x = l + i * bw + 4
        col = RED if i >= 7 else LIGHT
        body.append(f'<rect x="{x:.1f}" y="{bottom - bh:.1f}" width="{bw - 8:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
        body.append(t(x + (bw - 8) / 2, bottom - bh - 5, str(c), 11, INK, "middle", "bold"))
        body.append(t(x + (bw - 8) / 2, bottom + 17, f"{i * 10}–{i * 10 + 9 if i < 9 else 100}", 10, MID, "middle"))
    avg = sum(s) / len(s)
    ax = l + (W - l - 20) * avg / 100
    body.append(f'<line x1="{ax:.1f}" y1="{top}" x2="{ax:.1f}" y2="{bottom}" stroke="{CHAR}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    body.append(t(ax - 6, top + 10, f"average {avg:.1f}", 11, CHAR, "end", "bold"))
    return svg(h, "".join(body), "Dealer Standards score distribution")


def fig_ids_networks():
    nets = ids_stats()["nets"]
    order = sorted(nets.items(), key=lambda kv: -kv[1][0])
    big = [kv for kv in order if kv[1][0] > 1]
    small = [kv for kv in order if kv[1][0] == 1]
    rows = big + [("Cyprus, Luxembourg, Malta", [sum(v[0] for _, v in small), sum(v[1] for _, v in small)])]
    row, top, lw = 22, 40, 170
    h = top + row * len(rows) + 10
    plot = W - lw - 120
    mx = 90
    body = [t(0, 16, "Dealers per Dealer Standards network: scored (red) and listed without a score (grey)", 12, MID, weight="bold")]
    for i, (k, (n, s)) in enumerate(rows):
        y = top + i * row
        sw = plot * s / mx
        uw = plot * (n - s) / mx
        body.append(t(lw - 10, y + 13, k, 11, INK, "end"))
        body.append(f'<rect x="{lw}" y="{y + 3}" width="{sw:.1f}" height="14" fill="{RED}"/>')
        body.append(f'<rect x="{lw + sw:.1f}" y="{y + 3}" width="{uw:.1f}" height="14" fill="{LIGHT}"/>')
        body.append(t(lw + sw + uw + 6, y + 14, f"{s} of {n}", 10.5, INK if s else MID))
    return svg(h, "".join(body), "Dealer Standards networks")


def fig_tender_funnel():
    st, dc, oc = tender_stats()
    stages = [("Public notices collected", st["raw_notices"]), ("Distinct opportunities", st["opportunities"]),
              ("With an aftersales signal", st["aftersales_tagged"]), ("In the action queue", st["action_queue"]),
              ("Due within 14 days", st["due_14d"]), ("Outcomes recorded", oc["recorded"])]
    row, top, lw = 34, 30, 200
    h = top + row * len(stages) + 6
    plot = W - lw - 70
    mx = 700
    body = [t(0, 16, "The public-tender feed on 22 September 2026", 12, MID, weight="bold")]
    for i, (lab, v) in enumerate(stages):
        y = top + i * row
        bw = max(plot * v / mx, 2)
        hi = v == 0
        body.append(t(lw - 10, y + 18, lab, 11.5, RED if hi else INK, "end", "bold" if hi else "normal"))
        x0 = lw + (plot - bw) / 2
        body.append(f'<rect x="{x0:.1f}" y="{y + 4}" width="{bw:.1f}" height="22" fill="{RED if hi else CHAR}" opacity="{1 if hi else 0.35 + 0.65 * (len(stages) - i) / len(stages):.2f}" rx="2"/>')
        body.append(t(lw + plot + 10, y + 20, f"{v:,}", 13, RED if hi else INK, weight="bold"))
    return svg(h, "".join(body), "Tender funnel")


def fig_dlod_credits():
    items = [("Jun 2023", 14421.73), ("Sep 2023", 10273.90), ("Jan 2024", 5304.37), ("Feb 2025", 30000.0), ("Mar 2026", 30000.0)]
    h, l, top, bottom = 240, 50, 36, 190
    ymax = 40000
    n = len(items)
    gw = (W - l - 200) / n
    body = [t(0, 16, "Incentive credits booked to Isuzu Truck UK under the programme name (EUR)", 12, MID, weight="bold")]
    for yv in (0, 10000, 20000, 30000, 40000):
        y = bottom - (bottom - top) * yv / ymax
        body.append(f'<line x1="{l}" y1="{y:.1f}" x2="{l + gw * n}" y2="{y:.1f}" stroke="{GRID}"/>')
        body.append(t(l - 8, y + 4, f"{yv // 1000}k", 10.5, MID, "end"))
    for i, (lab, v) in enumerate(items):
        x = l + i * gw + gw * 0.18
        bh = (bottom - top) * v / ymax
        col = MID if i < 3 else CHAR
        body.append(f'<rect x="{x:.1f}" y="{bottom - bh:.1f}" width="{gw * 0.64:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
        body.append(t(x + gw * 0.32, bottom - bh - 6, eurk(v) if v < 29000 else "€30k", 11.5, INK, "middle", "bold"))
        body.append(t(x + gw * 0.32, bottom + 18, lab, 10.5, MID, "middle"))
    body.append(f'<line x1="{l + gw * 0.15:.1f}" y1="{bottom + 30}" x2="{l + gw * 2.85:.1f}" y2="{bottom + 30}" stroke="{MID}"/>')
    body.append(t(l + gw * 1.5, bottom + 45, "three credits for 2023: €30,000 together", 10.5, MID, "middle"))
    cx = l + gw * n + 30
    body.append(f'<rect x="{cx}" y="{top}" width="165" height="{bottom - top}" fill="{RED}" rx="3"/>')
    body.append(t(cx + 82, top + 62, "0", 54, "#FFFFFF", "middle", "bold"))
    body.append(t(cx + 82, top + 92, "cases recorded", 12.5, "#FFFFFF", "middle", "bold"))
    body.append(t(cx + 82, top + 110, "part, dealer, competitor", 10, "#FFE3E4", "middle"))
    body.append(t(cx + 82, top + 124, "quote or outcome", 10, "#FFE3E4", "middle"))
    return svg(h, "".join(body), "Don't Lose the Deal credits")


def s2d_coverage():
    """Which distributors send sales-to-dealer data, from the long files on disk."""
    files = [f for f in os.listdir(DERIVED) if f.startswith("dealer_sellout_long_") and f.endswith(".csv")]
    dbs = lambda fs: sorted({f.replace("dealer_sellout_long_", "").split("_CY")[0].replace("_network", "") for f in fs})  # noqa: E731
    any_db = dbs(files)
    y25 = dbs([f for f in files if "CY2025" in f])
    billed = {r["distributor_code"]: float(r["total_sales_eur"] or 0) for r in gps_2025()}
    tot = sum(billed.values())
    named = ["ITUK"]
    return {"n_db": len(billed), "billed": tot, "any": any_db, "y25": y25,
            "y25_eur": sum(billed.get(d, 0) for d in y25), "named": named,
            "named_eur": sum(billed[d] for d in named)}


def fig_visibility(dark=False):
    c = s2d_coverage()
    ink = "#E9EAEC" if dark else INK
    sub = "#A9AEB5" if dark else MID
    base = "#5A6068" if dark else LIGHT
    rows = [("Parts billed to distributors", f"all {c['n_db']} distributors", c["billed"], False),
            ("Sales to dealer, any detail, 2025", f"{len(c['y25'])} of {c['n_db']}", c["y25_eur"], False),
            ("Sales to named dealers", f"1 of {c['n_db']}, one year", c["named_eur"], True),
            ("Dealer to end customer", "none", 0, True),
            ("Workshop and maintenance records", "one dealer, once", 0, True)]
    row, top, lw = 38, 10, 250
    h = top + row * len(rows) + 6
    plot = W - lw - 120
    body = []
    for i, (lab, who, v, hi) in enumerate(rows):
        y = top + i * row
        pct = v / c["billed"] * 100
        bw = max(plot * pct / 100, 3)
        body.append(t(lw - 12, y + 15, lab, 12, ink, "end", "bold"))
        body.append(t(lw - 12, y + 30, who, 10.5, sub, "end"))
        body.append(f'<rect x="{lw}" y="{y + 6}" width="{plot}" height="22" fill="{base}" opacity="0.25" rx="2"/>')
        body.append(f'<rect x="{lw}" y="{y + 6}" width="{bw:.1f}" height="22" fill="{RED if hi else base}" rx="2"/>')
        body.append(t(lw + plot + 10, y + 23, f"{pct:.1f}%" if v else "0%", 15, RED if hi else ink, weight="bold"))
    return svg(h, "".join(body), "What ISZE can see of its own aftermarket")


def pms_capture_2025():
    rows = [r for r in load("pms_capture_by_db_year.csv") if r["year"] == "2025" and r["line_type"] == "total"]
    ok = [r for r in rows if float(r["capture_rate"]) <= 1]
    exp_ok = sum(float(r["expected_qty"]) * float(r["avg_sp_eur"]) for r in ok)
    act_ok = sum(float(r["actual_rev_eur"]) for r in ok)
    return {"rows": len(rows), "excluded": len(rows) - len(ok), "dbs": len({r["distributor_code"] for r in rows}),
            "families": len({r["pms_category"] for r in rows}), "modelled": exp_ok, "actual": act_ok,
            "capture": act_ok / exp_ok * 100, "point": exp_ok / 100}


def fig_oil_capture():
    rows = [r for r in load("pms_capture_by_db_year.csv")
            if r["year"] == "2025" and r["line_type"] == "total" and r["pms_category"] == "oil_filter"]
    ok = sorted([r for r in rows if float(r["capture_rate"]) <= 1], key=lambda r: float(r["capture_rate"]))
    items = [(NAMES.get(r["distributor_code"], r["distributor_code"].title()), float(r["capture_rate"]) * 100,
              float(r["capture_rate"]) < 0.5) for r in ok]
    uio = {NAMES.get(r["distributor_code"], r["distributor_code"].title()): float(r["uio_units"]) for r in ok}
    return hbars(items, lambda v: f"{v:.0f}%", label_w=140, value_w=190, maxv=100,
                 title="Oil filters supplied by ISZE as a share of modelled service need, 2025",
                 note_fn=lambda lab, v: f"{uio[lab]:,.0f} trucks in service")


def ituk_dealers():
    rows = [r for r in load("dealer_sellout_gps_2025.csv") if r["distributor_code"] == "ITUK"]
    return sorted((float(r["total_eur"]) for r in rows), reverse=True)


def fig_ituk_dealers():
    v = ituk_dealers()
    h, l, top, bottom = 250, 56, 30, 210
    ymax = 400000
    bw = (W - l - 10) / len(v)
    body = [t(0, 16, f"Parts bought by each of the {len(v)} Isuzu Truck UK dealers from their distributor, 2025 (EUR)", 12, MID, weight="bold")]
    for yv in (0, 100000, 200000, 300000, 400000):
        y = bottom - (bottom - top) * yv / ymax
        body.append(f'<line x1="{l}" y1="{y:.1f}" x2="{W - 10}" y2="{y:.1f}" stroke="{GRID}"/>')
        body.append(t(l - 8, y + 4, f"€{yv // 1000}k", 10.5, MID, "end"))
    med = v[len(v) // 2]
    for i, x in enumerate(v):
        bh = (bottom - top) * x / ymax
        body.append(f'<rect x="{l + i * bw + 1:.1f}" y="{bottom - bh:.1f}" width="{bw - 2:.1f}" height="{bh:.1f}" fill="{RED if i < 10 else CHAR}" opacity="{1 if i < 10 else 0.55}"/>')
    ym = bottom - (bottom - top) * med / ymax
    body.append(f'<line x1="{l}" y1="{ym:.1f}" x2="{W - 10}" y2="{ym:.1f}" stroke="{CHAR}" stroke-dasharray="4 3"/>')
    body.append(t(W - 12, ym - 6, f"median dealer {eurk(med)}", 11, CHAR, "end", "bold"))
    body.append(t(l + 5 * bw, top + 10, f"top 10 dealers: {sum(v[:10]) / sum(v) * 100:.1f}% of the total", 11, RED, "start", "bold"))
    body.append(t(l, bottom + 18, "dealers, ranked", 10.5, MID))
    return svg(h, "".join(body), "Isuzu Truck UK dealer purchases")


def fig_capture_points():
    p = pms_capture_2025()["point"]
    margins = [0.2, 0.3, 0.4]
    h, l, top, bottom = 250, 60, 40, 200
    ymax = 8
    gw = (W - l - 20) / len(margins)
    body = [t(0, 16, "Points of maintenance-parts capture needed to earn back each route, network-wide", 12, MID, weight="bold")]
    for yv in (0, 2, 4, 6, 8):
        y = bottom - (bottom - top) * yv / ymax
        body.append(f'<line x1="{l}" y1="{y:.1f}" x2="{W - 10}" y2="{y:.1f}" stroke="{GRID}"/>')
        body.append(t(l - 8, y + 4, f"{yv}", 10.5, MID, "end"))
    for i, m in enumerate(margins):
        gx = l + i * gw + gw / 2
        for j, (env, col) in enumerate(((100000, RED), (300000, CHAR))):
            v = env / m / p
            bh = (bottom - top) * min(v, ymax) / ymax
            x = gx - 50 + j * 54
            body.append(f'<rect x="{x:.1f}" y="{bottom - bh:.1f}" width="48" height="{bh:.1f}" fill="{col}" rx="2"/>')
            body.append(t(x + 24, bottom - bh - 6, f"{v:.1f}", 12, col, "middle", "bold"))
        body.append(t(gx, bottom + 18, f"at {m * 100:.0f}% gross margin", 11, INK, "middle"))
    body.append(f'<rect x="{W - 250}" y="30" width="12" height="12" fill="{RED}"/>')
    body.append(t(W - 232, 40, "€100,000 route", 10.5, INK))
    body.append(f'<rect x="{W - 140}" y="30" width="12" height="12" fill="{CHAR}"/>')
    body.append(t(W - 122, 40, "€300,000 route", 10.5, INK))
    return svg(h, "".join(body), "Capture points needed")


def dlod_ituk_share():
    rows = {r["distributor_code"]: float(r["total_sales_eur"]) for r in gps_2025()}
    return rows["ITUK"], 30000 / rows["ITUK"] * 100
