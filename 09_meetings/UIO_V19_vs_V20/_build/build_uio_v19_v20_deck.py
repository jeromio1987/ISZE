"""Build ISZE_UIO_V19_vs_V20.html - charcoal HTML presentation (I Motors BPR style).

Input : uio_v19_v20_data.json (from extract_uio_v19_v20.py)
Output: ..\\ISZE_UIO_V19_vs_V20.html (self-contained, logo embedded)
Every number on the slides is computed here from the JSON; nothing is typed in by hand
except the verification counts (independent check reports of 18 and 22 Sep 2026) and the
fixed method parameters (curves, locked UK pickup value).
"""
import base64, json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "ISZE_UIO_V19_vs_V20.html")
LOGO = os.path.join(HERE, "isuzu_logo.png")
D = json.load(open(os.path.join(HERE, "uio_v19_v20_data.json"), encoding="utf-8"))

# ---- palette (from the charcoal I Motors deck) ----
BG, CARD, CARD2, LINE, LINE2 = "#262626", "#2E2E2E", "#303030", "#575757", "#3A3A3A"
INK, INK2, MUTED = "#F2F2F2", "#BDBDBD", "#8C8C8C"
RED, AMBER, GREEN, GREY = "#E30613", "#F5A000", "#55C271", "#9A9A9A"


def yv(s, y):
    return s[str(y)] if str(y) in s else s[y]


def f0(x):
    return f"{round(x):,}"


def pct(x, d=1):
    return f"{x*100:+.{d}f}%".replace("+-", "−").replace("-", "−")


T19, T20 = D["total"]["v19"], D["total"]["v20"]
M19, M20 = D["midi"]["v19"], D["midi"]["v20"]
X19 = {y: yv(T19, y) - yv(M19, y) for y in range(1990, 2031)}
X20 = {y: yv(T20, y) - yv(M20, y) for y in range(1990, 2031)}
t25, t19_26, t20_26, t19_30, t20_30 = (yv(T19, 2025), yv(T19, 2026), yv(T20, 2026), yv(T19, 2030), yv(T20, 2030))
gap26, gap30 = t20_26 - t19_26, t20_30 - t19_30
hist_same = all(abs(yv(T19, y) - yv(T20, y)) < 0.5 for y in range(1990, 2026))
assert hist_same, "history 1990-2025 differs between V19 and V20"

# ---- gap by market, 2030 ----
NAMES = {"U KING": "United Kingdom", "PORTUGL": "Portugal", "ISRAEL": "Israel", "ITALY": "Italy",
         "GERMANY": "Germany", "NORWAY": "Norway", "SWEDEN": "Sweden", "BELGIUM": "Belgium",
         "IRELAND": "Ireland", "HUNGARY": "Hungary", "GREECE": "Greece", "ROMANIA": "Romania",
         "FINLAND": "Finland", "MALTA": "Malta", "CYPRUS": "Cyprus", "DENMARK": "Denmark",
         "ICELAND": "Iceland", "POLAND": "Poland", "FRANCE": "France", "SWITZ": "Switzerland",
         "SWITZERLAND": "Switzerland", "SPAIN": "Spain", "NETHERL": "Netherlands", "AUSTRIA": "Austria"}
by_ctry, by_row = {}, []
for r in D["rows"]:
    g = yv(r["v20"], 2030) - yv(r["v19"], 2030)
    c = NAMES.get(r["country"], r["country"].title())
    by_ctry[c] = by_ctry.get(c, 0) + g
    if abs(g) >= 1:
        by_row.append((g, c, r["cvlcv"], r["model"], r["distributor"], r["row"]))
ctry_sorted = sorted(by_ctry.items(), key=lambda kv: kv[1])
top = [kv for kv in ctry_sorted if kv[1] < 0][:10]
other = sum(v for k, v in ctry_sorted if (k, v) not in top)
by_row.sort()
row_lookup = {r["row"]: r for r in D["rows"]}
italy_ld = row_lookup[58]
uk_lcv = row_lookup[25]
isr_lcv = row_lookup[9]
it_gap = yv(italy_ld["v20"], 2030) - yv(italy_ld["v19"], 2030)
uk_gap = yv(uk_lcv["v20"], 2030) - yv(uk_lcv["v19"], 2030)
isr_gap = yv(isr_lcv["v20"], 2030) - yv(isr_lcv["v19"], 2030)
it_lcv_gap = yv(row_lookup[60]["v20"], 2030) - yv(row_lookup[60]["v19"], 2030)
cv_gap = sum(yv(r["v20"], 2030) - yv(r["v19"], 2030) for r in D["rows"] if r["cvlcv"] == "CV")
lcv_gap = sum(yv(r["v20"], 2030) - yv(r["v19"], 2030) for r in D["rows"] if r["cvlcv"] == "LCV")

# ---- Portugal ----
PR = D["portugal_registrations"]
pr = {k: {int(y): v for y, v in s.items()} for k, s in PR.items()}
pt = {r["row"]: r for r in D["rows"] if r["row"] in (51, 53, 54)}
def pt_series(rows, key, years):
    return {y: sum(yv(pt[r][key], y) for r in rows) for y in years}
PY = list(range(2015, 2031))
pt_tr = {"v19": pt_series((51, 53), "v19", PY), "v20": pt_series((51, 53), "v20", PY),
         "reg": {y: pr["LD"][y] + pr["F-Series"][y] for y in PY}}
pt_pu = {"v19": pt_series((54,), "v19", PY), "v20": pt_series((54,), "v20", PY), "reg": pr["Pickups"]}
regs = {int(y): v for y, v in D["portugal_regs_by_year"].items()}


# =====================================================================================
# SVG helpers
# =====================================================================================
def esc(s):
    return html.escape(str(s), quote=True)


def line_chart(w, h, years, series, ymin=None, ymax=None, fc_from=2026, yfmt=f0, label_right=True,
               ticks=5, note=None):
    """series: list of dict(name, color, values{year:val}, dash, width, label)"""
    pl, pr_, pt_, pb = 58, (118 if label_right else 20), 16, 30
    iw, ih = w - pl - pr_, h - pt_ - pb
    allv = [v for s in series for y, v in s["values"].items() if y in years]
    lo = ymin if ymin is not None else min(allv)
    hi = ymax if ymax is not None else max(allv)
    span = hi - lo
    step = nice_step(span / ticks)
    if not (ymin is not None and ymax is not None):
        lo = step * int(lo // step)
        hi = step * (int(hi // step) + 1)
    X = lambda y: pl + (y - years[0]) / (years[-1] - years[0]) * iw
    Y = lambda v: pt_ + ih - (v - lo) / (hi - lo) * ih
    o = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" class="chart" role="img">']
    if fc_from and fc_from <= years[-1]:
        x0 = X(fc_from - 0.5)
        o.append(f'<rect x="{x0:.1f}" y="{pt_}" width="{pl+iw-x0:.1f}" height="{ih}" fill="#2C2C2C"/>')
        o.append(f'<text x="{x0+8:.1f}" y="{pt_+14}" class="ax" fill="{MUTED}">FORECAST</text>')
        o.append(f'<text x="{x0-8:.1f}" y="{pt_+14}" class="ax" text-anchor="end" fill="{MUTED}">HISTORY</text>')
    v = lo
    while v <= hi + 1e-9:
        yy = Y(v)
        o.append(f'<line x1="{pl}" x2="{pl+iw}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{LINE2}" stroke-width="1"/>')
        o.append(f'<text x="{pl-8}" y="{yy+4:.1f}" class="ax" text-anchor="end">{yfmt(v)}</text>')
        v += step
    for y in years:
        if y % 5 == 0 or y == years[0] or y == years[-1]:
            o.append(f'<text x="{X(y):.1f}" y="{pt_+ih+20}" class="ax" text-anchor="middle">{y}</text>')
    labels = []
    for s in series:
        pts = [(X(y), Y(s["values"][y])) for y in years if y in s["values"]]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        dash = f' stroke-dasharray="{s["dash"]}"' if s.get("dash") else ""
        o.append(f'<path d="{d}" fill="none" stroke="{s["color"]}" stroke-width="{s.get("width", 2.5)}"'
                 f' stroke-linejoin="round" stroke-linecap="round"{dash}/>')
        if s.get("inline"):
            ia, dx, dy, anc = s["inline"]
            o.append(f'<text x="{X(ia)+dx:.1f}" y="{Y(s["values"][ia])+dy:.1f}" class="lbl" text-anchor="{anc}" fill="{s["color"]}">{esc(s["label"])}</text>')
        elif label_right and s.get("label"):
            ly = s["values"][years[-1]]
            labels.append([Y(ly), s])
    # de-collide end labels
    labels.sort(key=lambda t: t[0])
    for i in range(1, len(labels)):
        if labels[i][0] - labels[i - 1][0] < 30:
            labels[i][0] = labels[i - 1][0] + 30
    for yy, s in labels:
        ex, ey = X(years[-1]), Y(s["values"][years[-1]])
        o.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{s["color"]}" stroke="{BG}" stroke-width="2"/>')
        o.append(f'<text x="{pl+iw+12}" y="{yy-2:.1f}" class="lbl" fill="{INK}">{esc(s["label"])}</text>')
        o.append(f'<text x="{pl+iw+12}" y="{yy+13:.1f}" class="lblv" fill="{INK2}">{yfmt(s["values"][years[-1]])}</text>')
    # hover columns
    for y in years:
        tip = f"<b>{y}</b>" + "".join(
            f'<br><span style="color:{s["color"]}">■</span> {esc(s["name"])}: {yfmt(s["values"][y])}'
            for s in series if y in s["values"])
        x = X(y)
        half = iw / (len(years) - 1) / 2
        o.append(f'<rect class="hov" x="{x-half:.1f}" y="{pt_}" width="{2*half:.1f}" height="{ih}" data-tip="{esc(tip)}"'
                 f' data-x="{x:.1f}"/>')
    o.append(f'<line class="xhair" x1="0" x2="0" y1="{pt_}" y2="{pt_+ih}" stroke="{INK2}" stroke-width="1" opacity="0"/>')
    o.append("</svg>")
    return "".join(o)


def nice_step(raw):
    import math
    if raw <= 0:
        return 1
    e = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * e:
            return m * e
    return 10 * e


def hbar_chart(w, items, bar_h=24, gap=10, color=RED):
    """items: list of (label, value<0, tip). Bars grow left->right by magnitude."""
    pl, pr_ = 140, 90
    iw = w - pl - pr_
    mx = max(abs(v) for _, v, _ in items)
    h = len(items) * (bar_h + gap) + 6
    o = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" class="chart" role="img">']
    for i, (lab, v, tip) in enumerate(items):
        y = i * (bar_h + gap) + 3
        bw = max(2, abs(v) / mx * iw)
        col = color if lab != "All other markets" else "#6E6E6E"
        o.append(f'<text x="{pl-12}" y="{y+bar_h/2+5:.1f}" class="lbl" text-anchor="end" fill="{INK}">{esc(lab)}</text>')
        o.append(f'<path d="M{pl},{y} h{bw-4:.1f} a4,4 0 0 1 4,4 v{bar_h-8} a4,4 0 0 1 -4,4 h-{bw-4:.1f} z" fill="{col}"/>')
        o.append(f'<text x="{pl+bw+8:.1f}" y="{y+bar_h/2+5:.1f}" class="lblv" fill="{INK2}">{"−" if v < 0 else "+"}{f0(abs(v))}</text>')
        o.append(f'<rect class="hov" x="0" y="{y-3}" width="{w}" height="{bar_h+gap}" data-tip="{esc(tip)}"/>')
    o.append("</svg>")
    return "".join(o)


def legend(items):
    out = []
    for name, color, dash in items:
        sw = (f'<svg width="26" height="10"><line x1="1" x2="25" y1="5" y2="5" stroke="{color}" stroke-width="2.5"'
              f'{" stroke-dasharray=%s" % chr(34)+dash+chr(34) if dash else ""} stroke-linecap="round"/></svg>')
        out.append(f'<span class="lg">{sw}{esc(name)}</span>')
    return '<div class="legend">' + "".join(out) + "</div>"


# =====================================================================================
# slide scaffolding
# =====================================================================================
TOTAL_SLIDES = 10
SRC_BOTH = "Source: ISZE UIO workbook V19 (18 June 2026) and V20 draft (22 September 2026), sheet 1. UIO Overview."


def slide(n, kicker, title, sub, body, obs=None, src=SRC_BOTH):
    obs_html = ""
    if obs:
        li = "".join(f'<li><span class="dot" style="background:{c}"></span><span>{t}</span></li>' for c, t in obs)
        obs_html = f'<aside class="obs"><div class="obs-h">OBSERVATIONS / QUESTIONS</div><ul>{li}</ul></aside>'
    return f'''
<section class="slide" data-n="{n}">
  <div class="brand">ISZE · VEHICLE PARTS &amp; ACCESSORIES</div>
  <div class="kicker">{kicker}</div>
  <h1 class="title">{title}</h1>
  <div class="sub">{sub}</div>
  <div class="body{" has-obs" if obs else ""}">{body}</div>
  {obs_html}
  <footer><span>{src}</span><span>{n}</span></footer>
</section>'''


def card(label, value, note, color=INK, cls=""):
    return (f'<div class="card {cls}"><div class="c-lab">{label}</div>'
            f'<div class="c-val" style="color:{color}">{value}</div><div class="c-note">{note}</div></div>')


logo_b64 = base64.b64encode(open(LOGO, "rb").read()).decode()
slides = []

# ---- 1 cover ----
slides.append(f'''
<section class="slide cover" data-n="1">
  <div class="redbar"></div>
  <div class="brand">ISZE · VEHICLE PARTS &amp; ACCESSORIES</div>
  <h1 class="cover-t">Units in Operation<br>V19 versus V20</h1>
  <div class="cover-s">What changed in the car park model · Why the forecast moves · What is still open</div>
  <div class="cover-d">V19 of 18 June 2026 against the V20 draft of 22 September 2026 &nbsp;|&nbsp; Review draft, 24 September 2026</div>
  <img class="logo" src="data:image/png;base64,{logo_b64}" alt="Isuzu">
</section>''')

# ---- 2 executive view ----
up19 = t19_30 / t25 - 1
dn20 = t20_30 / t25 - 1
x_gap30 = X20[2030] - X19[2030]
cards = "".join([
    card("V19 · 2030", f0(t19_30), f"Units in operation, all markets<br>{pct(up19)} on 2025", GREY),
    card("V20 · 2030", f0(t20_30), f"Units in operation, all markets<br>{pct(dn20)} on 2025", RED),
    card("DIFFERENCE 2030", f"−{f0(-gap30)}", f"V20 against V19<br>{pct(gap30 / t19_30)}", AMBER),
    card("DIFFERENCE 2026", f"−{f0(-gap26)}", f"First forecast year<br>{pct(gap26 / t19_26)}", AMBER),
    card("2025 STARTING POINT", f0(t25), "Identical in both versions:<br>history 1990–2025 unchanged", INK),
    card("DIRECTION", "Growth → decline", f"V19 adds {f0(t19_30 - t25)} units by 2030;<br>V20 loses {f0(t25 - t20_30)}", INK, "small"),
    card("EXCLUDING MIDI · 2030", f0(X20[2030]), f"V20 against {f0(X19[2030])} in V19<br>{pct(x_gap30 / X19[2030])}", INK),
    card("TRUCKS / PICKUPS · 2030", f"−{f0(-cv_gap)} / −{f0(-lcv_gap)}", "Difference by vehicle type,<br>V20 against V19", INK, "small"),
])
body = f'''<div class="grid4">{cards}</div>
<div class="mread"><div class="mr-h">Management read</div><div class="mr-t">
V19 builds its history with a realistic vehicle life but rolls the forecast forward with a flat 3% scrap rate,
which implies a 33-year truck life. V20 applies the same survival curve to 2026–2030 that V19 already uses for
1990–2025. With the new-registration plan unchanged, the car park now declines instead of growing.</div></div>'''
slides.append(slide(2, "EXECUTIVE VIEW",
                    "V20 removes the forecast inflation in V19: the 2030 car park is "
                    f"{f0(-gap30)} units lower, and the trend turns from growth to decline",
                    "Units in operation (vehicles in service), all markets in the workbook. The V20 figures are the draft of 22 September 2026.",
                    body,
                    [(RED, "V19 stays the official version until the V20 draft is approved."),
                     (AMBER, f"Italy (MIDI Europe) accounts for {f0(-by_ctry.get('Italy', 0))} of the 2030 difference; the current plan has no new trucks for MIDI from 2026."),
                     (AMBER, f"UK pickups account for {f0(-uk_gap)}: the 2026 value is fixed at 44,926 and the fleet then ages on the pickup curve."),
                     (INK2, "Portugal and Poland corrections agreed on 24 September are not yet in these figures (slide 9)."),
                     (RED, "Registration data received since V19 for Israel and the UK is not yet used; Israel's government register shows about a quarter more trucks (slides 7–8).")]))

# ---- 3 method ----
CV = [1, .99, .98, .97, .96, .95, .9, .8, .7, .55, .4, .3, .2, .1, .05, 0]
LCV = [1, .98, .95, .92, .89, .84, .8, .65, .5, .4, .2, 0]
ages = list(range(1, 21))
sv = lambda c, a: (c[a - 1] if a <= len(c) else 0) * 100
curve_chart = line_chart(560, 330, ages, [
    {"name": "V19 forecast rule (3% a year)", "label": "V19 forecast rule", "color": GREY, "dash": "6 5",
     "values": {a: 100 * 0.97 ** (a - 1) for a in ages}, "inline": (16, 0, -12, "middle")},
    {"name": "Trucks — survival curve", "label": "Trucks", "color": RED, "values": {a: sv(CV, a) for a in ages},
     "inline": (11, 10, -4, "start")},
    {"name": "Pickups — survival curve", "label": "Pickups", "color": AMBER, "values": {a: sv(LCV, a) for a in ages},
     "inline": (9, -10, 4, "end")},
], ymin=0, ymax=100, fc_from=None, yfmt=lambda v: f"{v:.0f}%", label_right=False)
curve_chart = curve_chart.replace('text-anchor="middle">20<', 'text-anchor="middle">20 yrs<')
body = f'''<div class="two">
  <div class="panel"><div class="p-h">Share of one year's vehicles still in service, by age</div>{curve_chart}
  <div class="p-note">Age in years. Hover for values.</div></div>
  <div class="stack">
    {card("V19 FORECAST RULE", "33.3 yrs", "Average life implied by 3% scrap a year (2026–2030 only)", GREY)}
    {card("TRUCKS · SURVIVAL CURVE", "9.9 yrs", "Average life, about 10% scrapped a year. Used in both versions for 1990–2025", RED)}
    {card("PICKUPS · SURVIVAL CURVE", "8.1 yrs", "Average life, about 12% scrapped a year. Used in both versions for 1990–2025", AMBER)}
  </div></div>'''
slides.append(slide(3, "WHAT CHANGED IN THE METHOD",
                    "V19 switched to a 33-year vehicle life for the forecast; V20 keeps the realistic life for every year",
                    "Units in operation(t) = sum over registration years of new registrations × share still in service at that age.",
                    body,
                    [(RED, "In V19 the same market used two methods: a survival curve up to 2025, a flat 3% scrap rate from 2026. That seam is what made the forecast grow."),
                     (AMBER, "V20 uses one method from 1990 to 2030. There is no step at the 2025/2026 boundary: each row is rebuilt so that 2025 reproduces V19 exactly."),
                     (INK2, "New registrations for 2026–2030 follow the sales plan one-to-one on the five-year level, with the annual profile smoothed.")],
                    src="Source: survival curves on sheet 3. UIO Calculation (IMIT LCV study November 2025; IML CV developed-market curve)."))

# ---- 4 totals ----
YR = list(range(2015, 2031))
def tot_chart(s19, s20, w=440):
    hist = {y: s19[y] for y in YR if y <= 2025}
    return line_chart(w, 380, YR, [
        {"name": "History (both versions)", "color": INK, "values": hist, "width": 2.5},
        {"name": "V19", "label": "V19", "color": GREY, "dash": "6 5", "values": {y: s19[y] for y in YR if y >= 2025}},
        {"name": "V20", "label": "V20", "color": RED, "values": {y: s20[y] for y in YR if y >= 2025}},
    ], yfmt=lambda v: f"{v/1000:.0f}k")
S19 = {y: yv(T19, y) for y in YR}; S20 = {y: yv(T20, y) for y in YR}
tot_all = tot_chart(S19, S20)
tot_ex = tot_chart({y: X19[y] for y in YR}, {y: X20[y] for y in YR})
body = f'''{legend([("History, identical in both", INK, None), ("V19", GREY, "6 5"), ("V20 draft", RED, None)])}
<div class="two eq">
  <div class="panel"><div class="p-h">All markets in the workbook (MIDI included)</div>{tot_all}</div>
  <div class="panel"><div class="p-h">Excluding MIDI Europe markets</div>{tot_ex}</div>
</div>'''
slides.append(slide(4, "CAR PARK TOTAL",
                    "The two versions share the same history and split at 2026: V19 keeps rising, V20 turns down",
                    "Units in operation, 2015–2030. Hover a year for the values.",
                    body,
                    [(RED, f"All markets: V19 {f0(t19_30)} in 2030 against V20 {f0(t20_30)}. The gap widens every year, from {f0(-gap26)} in 2026 to {f0(-gap30)} in 2030."),
                     (AMBER, f"Excluding MIDI the gap is {f0(-x_gap30)} in 2030 ({pct(x_gap30 / X19[2030])}), and V20 still falls {pct(X20[2030] / X20[2025] - 1)} from 2025."),
                     (INK2, "MIDI Europe is not an ISZE distributor. It sits in the workbook total but not in ISZE's own sales views.")]))

# ---- 5 gap by market ----
items = []
for c, v in top:
    rows = [r for r in by_row if r[1] == c]
    tip = f"<b>{esc(c)}</b> · 2030 difference {f0(v)}" + "".join(
        f"<br>{esc(r[2])} {esc(r[3])} ({esc(r[4])}): {f0(r[0])}" for r in rows[:5])
    items.append((c, v, tip))
items.append(("All other markets", other, f"<b>All other markets</b> · net {f0(other)}"))
bars = hbar_chart(840, items)
it_share = it_gap / gap30
body = f'''<div class="panel wide"><div class="p-h">Difference in 2030, V20 against V19, units in operation</div>{bars}</div>'''
slides.append(slide(5, "WHERE THE DIFFERENCE SITS",
                    f"Italy and the United Kingdom carry {pct((by_ctry.get('Italy', 0) + by_ctry.get('United Kingdom', 0)) / gap30, 0).lstrip('+−')} of the 2030 difference",
                    "Units in operation, 2030. Hover a bar for the split by vehicle type.",
                    body,
                    [(RED, f"Italy (MIDI Europe) is {f0(-by_ctry.get('Italy', 0))}: light trucks {f0(-it_gap)}, pickups {f0(-it_lcv_gap)}. The plan has no new MIDI trucks from 2026, so the truck fleet ages out ({f0(yv(italy_ld['v20'], 2025))} → {f0(yv(italy_ld['v20'], 2030))})."),
                     (AMBER, f"United Kingdom is {f0(-by_ctry.get('United Kingdom', 0))}, all pickups. UK trucks are unchanged: they already run on their own registration-based model."),
                     (AMBER, f"Israel pickups: −{f0(-isr_gap)}. Israel trucks are kept at V19 values pending a separate rebuild."),
                     (INK2, "Question: MIDI forecast figures are expected to replace the plan for Italy. Until then the Italy figure is the largest single uncertainty.")]))

# ---- 6 treatment table ----
trows = [
    ("All other markets", "Rebuilt on the survival curve", "Same method as the 1990–2025 history"),
    ("United Kingdom — trucks (ITUK)", "Unchanged", "Already modelled on UK registrations with its own curves"),
    ("United Kingdom — pickups (IUK)", "2026 fixed at 44,926, then the pickup curve", "47,783 × (1 − 12.3%) + 3,020 new registrations"),
    ("Israel — trucks (UTI)", "Kept at V19 values", "Separate rebuild on Israeli registration data"),
    ("Medium duty: Ireland, Portugal, Greece, Cyprus", "Taken out of the total, kept as plan only", "No medium-duty truck shipped to these markets 2020–2026"),
    ("Germany — light trucks", "Rebuilt, marked indicative", "2025 matches the national stock; no registration history before 2025"),
    ("Belgium, Cyprus, Malta, Greece", "Rebuilt, marked low confidence", "History built from shipment backbone, not registrations"),
    ("New registrations 2026–2030", "Sales plan one-to-one on the level", "Annual profile smoothed; five-year total kept exactly"),
]
tb = "".join(f"<tr><td class='b'>{esc(a)}</td><td>{esc(b)}</td><td class='m'>{esc(c)}</td></tr>" for a, b, c in trows)
body = f'''<table class="tbl"><thead><tr><th>Scope</th><th>Treatment in V20</th><th>Why</th></tr></thead><tbody>{tb}</tbody></table>'''
slides.append(slide(6, "SCOPE",
                    "Not every row changes the same way: some are protected, some are flagged",
                    "Treatment of each part of the car park in the V20 draft.",
                    body,
                    [(RED, "The 1990–2025 history is identical in both versions for every row."),
                     (AMBER, "Taking the medium-duty plan rows out of the total removes vehicles that were planned but never shipped."),
                     (INK2, "Rows marked indicative or low confidence stay in the total but should not be used for market-level targets on their own.")]))


# ---- 7 data behind each market ----
def chip(kind):
    col = {"Used": GREEN, "Agreed": AMBER, "Not used": RED, "Check only": INK2}[kind]
    return f'<span class="chip" style="color:{col};border-color:{col}">{kind}</span>'
drows = [
    ("United Kingdom", "SMMT car park by postcode, model and registration year (via ITUK)", "Government / licensed", "Car park to 2024", "Mar 2026", "Used", "UK trucks run on it (own model, sheet 4)"),
    ("United Kingdom", "ITUK per-vehicle registration lists, 29,935 vehicles", "Distributor", "Registrations 2008–2026", "Jul 2026", "Check only", "Cross-check for UK trucks; not yet done"),
    ("Ireland", "SIMI national registration statistics", "Government / licensed", "Registrations 2010–2025", "May 2026", "Used", "Ireland history is built on it"),
    ("Germany", "Helwig Schmitt national vehicle stock, Isuzu", "Government / licensed", "Car park 31/12/2025", "Jun 2026", "Used", "2025 level matches exactly: 697 / 35 / 13,048; no history before 2025"),
    ("Portugal", "I Motors SAP registrations by model, 14,412 chassis", "Distributor, per vehicle", "Registrations 2005–2026", "Jul 2026", "Agreed", "Rebuild agreed 24 September (slide 9)"),
    ("Israel", "Registrations by weight band (UTI)", "Government basis", "Registrations 1994–2025", "Jul 2026", "Not used", "Trucks still on V19 values"),
    ("Israel", "Ministry of Transport car park by weight band, with average age", "Government", "Car park 30/06/2026", "Jul 2026", "Not used", "Shows a fleet about a quarter larger (slide 8)"),
]
dt = "".join(f"<tr><td class='b'>{esc(a)}</td><td>{esc(b)}</td><td class='m'>{esc(c)}</td><td class='m'>{esc(d)}</td>"
             f"<td class='m'>{esc(e)}</td><td>{chip(f)}</td><td class='m'>{esc(g)}</td></tr>" for a, b, c, d, e, f, g in drows)
body = f"""<table class="tbl data"><thead><tr><th>Market</th><th>Source</th><th>Basis</th><th>Covers</th><th>Received</th><th>In V20</th><th>Note</th></tr></thead>
<tbody>{dt}</tbody></table>
<div class="p-note" style="margin-top:12px">The other 22 market rows (Belgium, Cyprus, Malta, Greece, Italy, Poland, the Nordic markets, Hungary, Romania and others)
have no registration or car-park source: their history rests on shipment records and estimates.</div>"""
slides.append(slide(7, "DATA BEHIND EACH MARKET",
                    "Registration data received since V19 for Portugal, Israel and the United Kingdom is not yet used in V20",
                    "Registration and car-park sources held for the UIO, and whether the V20 draft uses them. V19 is dated 18 June 2026.",
                    body,
                    [(RED, "V20 corrects the forecast method, but it still rests on V19's history. The new data received in July has not been built in."),
                     (RED, "Israel is the largest gap: two government-based sources, neither used."),
                     (AMBER, "Portugal's registration records are agreed for the next draft."),
                     (INK2, "For 22 of 27 market rows no registration source exists. Obtaining one is a request to the distributor or a national register.")],
                    src="Source: ISZE register of UIO and registration sources (22 September 2026); ISZE UIO workbook V19 and V20 draft."))

# ---- 8 Israel ----
gov = {2020: 11514, 2022: 12557, 2024: 13323, 2025: 13881, 2026: 14019}
isr = {y: yv(row_lookup[7]["v20"], y) + yv(row_lookup[8]["v20"], y) for y in gov}
assert abs(isr[2025] - 10336) < 1 and abs(isr[2026] - 10760) < 1, isr
def isr_bars(w=560, h=300):
    pl, pr_, pt_, pb = 50, 10, 30, 30
    iw, ih = w - pl - pr_, h - pt_ - pb
    hi = 16000
    Y = lambda v: pt_ + ih - v / hi * ih
    o = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" class="chart" role="img">']
    for v in range(0, hi + 1, 4000):
        o.append(f'<line x1="{pl}" x2="{pl+iw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{LINE2}"/>')
        o.append(f'<text x="{pl-8}" y="{Y(v)+4:.1f}" class="ax" text-anchor="end">{v//1000}k</text>')
    gw = iw / len(gov); bw = 34
    for i, y in enumerate(gov):
        cx = pl + gw * i + gw / 2
        for j, (val, col) in enumerate(((isr[y], GREY), (gov[y], AMBER))):
            x = cx - bw - 1 + j * (bw + 2)
            top = Y(val)
            o.append(f'<path d="M{x},{Y(0)} V{top+4:.1f} a4,4 0 0 1 4,-4 h{bw-8} a4,4 0 0 1 4,4 V{Y(0)} z" fill="{col}"/>')
        gap = isr[y] / gov[y] - 1
        o.append(f'<text x="{cx:.1f}" y="{Y(gov[y])-10:.1f}" class="lbl" text-anchor="middle" fill="{INK}">{pct(gap,0)}</text>')
        o.append(f'<text x="{cx:.1f}" y="{pt_+ih+20}" class="ax" text-anchor="middle">{y if y != 2026 else "Jun 2026"}</text>')
        tip = f"<b>{y if y != 2026 else '30 June 2026'}</b><br>UIO model (V19 = V20): {f0(isr[y])}<br>Ministry of Transport: {f0(gov[y])}<br>Gap: {f0(gov[y]-isr[y])} trucks"
        o.append(f'<rect class="hov" x="{cx-gw/2:.1f}" y="{pt_}" width="{gw:.1f}" height="{ih}" data-tip="{esc(tip)}"/>')
    o.append("</svg>")
    return "".join(o)
bands = [("6.5 – 7.5 t", 8610, "9.4", "9.8"), ("7.6 – 10 t", 2485, "6.2", "10.7"),
         ("10.1 – 12 t", 2697, "5.9", "7.3"), ("12.1 – 16 t", 227, "5.6", "9.1")]
bt = "".join(f"<tr><td class='b'>{a}</td><td class='r'>{f0(b)}</td><td class='r'>{c}</td><td class='r m'>{d}</td></tr>" for a, b, c, d in bands)
body = f"""{legend([("UIO model, trucks (V19 and V20 identical)", GREY, None), ("Israeli Ministry of Transport, registered Isuzu trucks", AMBER, None)])}
<div class="two">
  <div class="panel"><div class="p-h">Isuzu trucks in Israel: model against government register</div>{isr_bars()}</div>
  <div class="panel" style="flex:1"><div class="p-h">Government register at 30 June 2026, by weight</div>
  <table class="tbl compact mini"><thead><tr><th>Weight class</th><th class="r">Trucks</th><th class="r">Avg age</th><th class="r">Market avg</th></tr></thead>
  <tbody>{bt}<tr><td class='b'>Total</td><td class='r b'>{f0(sum(b[1] for b in bands))}</td><td></td><td></td></tr></tbody></table>
  <div class="p-note" style="margin-top:10px">Ages in years. 1,680 trucks first registered 1999–2010 are still on the road; the model's curve reaches zero at age 20.</div></div>
</div>"""
slides.append(slide(8, "NEW DATA · ISRAEL",
                    f"The Israeli government register counts {f0(gov[2026]-isr[2026])} more Isuzu trucks than the model at June 2026: a steady gap of about a quarter",
                    "Isuzu trucks (light and medium duty) in operation. Israel trucks are kept at V19 values in the V20 draft, so both versions carry the gap.",
                    body,
                    [(RED, f"The gap is between {f0(min(gov[y]-isr[y] for y in gov))} and {f0(max(gov[y]-isr[y] for y in gov))} trucks in every year shown since 2020. A steady gap points to a missing block of vehicles, not a scrap rate that is slightly off."),
                     (AMBER, "Possible causes: the 7.6–10 t and 12.1–16 t classes have no place in the model; trucks older than 19 years are scrapped in the model but still registered; the register also counts trucks not imported by UTI."),
                     (AMBER, "The fix is a rebuild on the government registrations by weight class, not a flat uplift of 25%."),
                     (INK2, "Question for UTI: can the Ministry car-park table be supplied as a data file? We hold it only as a chart in the July presentation.")],
                    src="Source: UTI parts presentation, July 2026 (Israeli Ministry of Transport data, car park at 30 June 2026); ISZE UIO workbook V19 and V20 draft, rows 7–8."))

# ---- 9 Portugal ----
def pt_chart(d):
    return line_chart(440, 330, PY, [
        {"name": "V19", "label": "V19", "color": GREY, "dash": "6 5", "values": d["v19"]},
        {"name": "V20 draft", "label": "V20 draft", "color": RED, "values": d["v20"]},
        {"name": "From registrations", "label": "Registrations", "color": AMBER, "values": d["reg"]},
    ], yfmt=f0)
reg_total = sum(v["pickups"] + v["ld"] + v["f"] for v in regs.values())
body = f'''{legend([("V19", GREY, "6 5"), ("V20 draft", RED, None), ("Rebuilt from Portugal registration records", AMBER, None)])}
<div class="two eq">
  <div class="panel"><div class="p-h">Portugal trucks (N-Series and F-Series)</div>{pt_chart(pt_tr)}</div>
  <div class="panel"><div class="p-h">Portugal pickups (D-Max)</div>{pt_chart(pt_pu)}</div>
</div>
<div class="p-note" style="margin-top:8px">The registration records start in 2005. Vehicles registered earlier are not in them, so the registration line is a minimum before 2019 for trucks and before 2015 for pickups.</div>'''
slides.append(slide(9, "AGREED NEXT CHANGE · PORTUGAL",
                    "Portugal will be rebuilt from its own registration records, 2005 onwards",
                    f"{f0(reg_total)} registrations 2005–2025 by model, aged on the same survival curves; 2026–2030 on the current sales plan.",
                    body,
                    [(RED, f"Starting point 2025: trucks {f0(pt_tr['reg'][2025])} against {f0(pt_tr['v19'][2025])} in V19; pickups {f0(pt_pu['reg'][2025])} against {f0(pt_pu['v19'][2025])}. The Portugal total barely moves."),
                     (AMBER, f"2030: trucks {f0(pt_tr['reg'][2030])}, pickups {f0(pt_pu['reg'][2030])}. Pickups land on the V20 draft; trucks end higher."),
                     (AMBER, f"Question: the plan carries no F-Series for Portugal, while {regs[2025]['f']} were registered in 2025 and {regs[2024]['f']} in 2024."),
                     (INK2, "Also agreed: Poland pickups rebuilt on a documented method (8 units in 2030). Which pre-2019 history years to replace is still to be decided.")],
                    src="Source: I Motors SAP registration extract (Matriculas Isuzu SAP, 2005–2026); ISZE UIO workbook V19 and V20 draft."))

# ---- 8 verification & open ----
open_rows = [
    ("Israel", "Rebuild trucks on the government registrations by weight class; the register shows about a quarter more trucks"),
    ("United Kingdom", "Cross-check UK trucks against the ITUK per-vehicle registration lists received in July"),
    ("Portugal history", "Replace pickups from 2015 and trucks from 2019 (fully covered years), or from 2005 as a floor"),
    ("Cyprus pickups", "No registration data after 2014; still flagged by the independent check"),
    ("Italy (MIDI Europe)", "MIDI forecast figures to replace the plan, which has no new trucks from 2026"),
    ("Pickup survival at age 12", "10% (IMIT study) or 0% (used, to keep the UK 2026 value)"),
    ("Germany", "2025 level matches the national stock; history before 2025 still missing"),
]
ot = "".join(f"<tr><td class='b'>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in open_rows)
body = f'''<div class="grid3">
  {card("INDEPENDENT CHECK · V19", "7 of 10", "tests failed, including the forecast method test", RED)}
  {card("INDEPENDENT CHECK · V20 DRAFT", "3 of 11", "tests failed: two pickup rows (Portugal, Cyprus) and the size-of-overstatement tolerance", AMBER)}
  {card("AFTER AGREED CHANGES", "Portugal", "The Portugal pickup fail is addressed by the registration rebuild; Cyprus remains", INK, "small")}
</div>
<div class="p-h" style="margin:22px 0 8px">Open points before V20 can replace V19</div>
<table class="tbl compact"><tbody>{ot}</tbody></table>'''
slides.append(slide(10, "STATUS AND OPEN POINTS",
                    f"V20 is materially closer to a real car park; {['zero','one','two','three','four','five','six','seven','eight','nine'][len(open_rows)]} points remain open before it replaces V19",
                    "The independent check reads only the workbook values, the survival curves and the vehicle shipment register.",
                    body,
                    [(RED, "V19's forecast overstatement measured against V20: +6.8% in 2026 rising to +37.9% in 2030."),
                     (AMBER, "The remaining tolerance fail compares that overstatement with a reference estimate: it differs by up to 1.6 points in 2027–2028."),
                     (INK2, "Next step: decide the Israel rebuild, build it with the agreed Portugal and Poland changes into the next V20 draft, re-run the independent check, then decide on promotion.")],
                    src="Source: independent verification reports on V19 (22 September 2026) and on the V20 draft (22 September 2026)."))

assert len(slides) == TOTAL_SLIDES

CSS = f"""
@font-face{{font-family:AptosLocal;src:local('Aptos'),local('Aptos Display');}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:#1a1a1a;height:100%;overflow:hidden;font-family:Aptos,AptosLocal,'Segoe UI',system-ui,sans-serif;color:{INK}}}
#stage{{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}}
#deck{{width:1280px;height:720px;position:relative;transform-origin:center center}}
.slide{{position:absolute;inset:0;background:{BG};display:none;overflow:hidden}}
.slide.on{{display:block}}
.brand{{position:absolute;left:24px;top:10px;font-size:8.5px;font-weight:700;letter-spacing:.02em;color:{INK}}}
.kicker{{position:absolute;left:24px;top:41px;font-size:9.5px;font-weight:600;color:{RED};letter-spacing:.02em}}
.title{{position:absolute;left:24px;top:62px;width:900px;font-size:21px;line-height:1.3;font-weight:700;color:{INK}}}
.sub{{position:absolute;left:24px;top:133px;width:900px;font-size:9.5px;color:{INK2}}}
.body{{position:absolute;left:38px;top:168px;width:1204px;bottom:44px}}
.body.has-obs{{width:884px}}
.obs{{position:absolute;left:947px;top:140px;width:313px;height:537px;background:{CARD2};border:1px solid #6E6E6E;padding:26px 24px}}
.obs-h{{font-size:9px;font-weight:600;color:{RED};margin-bottom:26px}}
.obs ul{{list-style:none;display:flex;flex-direction:column;gap:30px}}
.obs li{{display:flex;gap:14px;font-size:10px;line-height:1.45;color:{INK}}}
.dot{{flex:0 0 9px;height:9px;border-radius:50%;margin-top:3px}}
footer{{position:absolute;left:24px;right:24px;bottom:12px;border-top:1px solid #6E6E6E;padding-top:7px;display:flex;justify-content:space-between;font-size:7.5px;color:{MUTED}}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.card{{background:{CARD2};border:1px solid #6E6E6E;padding:14px 17px 16px;min-height:153px}}
.c-lab{{font-size:8.5px;font-weight:600;color:{RED};letter-spacing:.02em}}
.c-val{{font-size:30px;font-weight:700;margin:22px 0 14px;line-height:1}}
.card.small .c-val{{font-size:22px;margin:26px 0 18px}}
.c-note{{font-size:9px;line-height:1.45;color:{INK2}}}
.stack .card{{min-height:0;padding:14px 18px}}
.stack .c-val{{font-size:26px;margin:12px 0 8px}}
.mread{{margin-top:22px;background:{CARD2};border:1px solid #6E6E6E;display:flex;gap:40px;padding:22px 20px;min-height:106px}}
.mr-h{{flex:0 0 118px;color:{RED};font-size:11px}}
.mr-t{{font-size:11px;line-height:1.5;color:{INK}}}
.two{{display:flex;gap:16px;align-items:flex-start}}
.two .stack{{display:flex;flex-direction:column;gap:12px;flex:1}}
.two.eq>.panel{{flex:1}}
.panel{{background:{CARD};border:1px solid {LINE2};padding:14px 12px 10px}}
.panel.wide{{padding:18px 20px}}
.p-h{{font-size:10.5px;font-weight:600;color:{INK};margin-bottom:10px}}
.p-note{{font-size:8.5px;color:{MUTED};margin-top:4px}}
.legend{{display:flex;gap:22px;font-size:9.5px;color:{INK2};margin:-8px 0 10px}}
.lg{{display:flex;align-items:center;gap:7px}}
svg.chart{{display:block;max-width:100%;height:auto}}
svg .ax{{font-size:9px;fill:{MUTED};font-family:inherit}}
svg .lbl{{font-size:10px;font-weight:600;font-family:inherit}}
svg .lblv{{font-size:9.5px;font-family:inherit}}
svg .hov{{fill:transparent;cursor:crosshair}}
.tbl{{width:100%;border-collapse:collapse;font-size:10.5px}}
.tbl th{{background:#3A3A3A;text-align:left;padding:12px 14px;font-weight:600;color:{INK}}}
.tbl td{{padding:12px 14px;border-bottom:1px solid {LINE2};color:{INK}}}
.tbl tr:nth-child(odd) td{{background:{CARD}}}
.tbl tr:nth-child(even) td{{background:#2A2A2A}}
.tbl td.b{{font-weight:600;width:32%}}
.tbl td.m{{color:{INK2}}}
.tbl.compact td{{padding:9px 14px}}
.tbl td.r,.tbl th.r{{text-align:right}}
.tbl.mini{{font-size:10px}} .tbl.mini td,.tbl.mini th{{padding:9px 10px}}
.tbl.data{{font-size:9.5px}} .tbl.data td,.tbl.data th{{padding:10px 9px;vertical-align:top}} .tbl.data td.b{{width:auto;white-space:nowrap}}
.chip{{display:inline-block;border:1px solid;border-radius:10px;padding:1px 8px;font-size:9px;font-weight:600;white-space:nowrap}}
.cover .redbar{{position:absolute;left:0;top:0;bottom:0;width:10px;background:{RED}}}
.cover .brand{{left:43px;top:32px}}
.cover-t{{position:absolute;left:43px;top:198px;font-size:38px;line-height:1.28;font-weight:700}}
.cover-s{{position:absolute;left:43px;top:342px;font-size:14px;color:{INK2}}}
.cover-d{{position:absolute;left:43px;top:390px;font-size:10.5px;color:{INK2}}}
.cover .logo{{position:absolute;left:43px;top:633px;width:200px}}
#tip{{position:fixed;pointer-events:none;background:#111;border:1px solid #6E6E6E;color:{INK};font-size:12px;line-height:1.5;
     padding:8px 11px;border-radius:4px;opacity:0;transition:opacity .08s;z-index:10;max-width:340px}}
#nav{{position:fixed;right:18px;bottom:40px;display:flex;gap:6px;align-items:center;font-size:12px;color:{MUTED};z-index:5;opacity:0;transition:opacity .25s}}
#nav.show{{opacity:1}}
#nav button{{background:#2E2E2E;border:1px solid #575757;color:{INK};width:30px;height:26px;cursor:pointer;border-radius:3px}}
@media print{{
  @page{{size:1280px 720px;margin:0}}
  html,body{{overflow:visible;height:auto;background:{BG}}}
  #stage{{position:static;display:block}} #deck{{transform:none!important;width:1280px;height:auto}}
  .slide{{display:block!important;position:relative;width:1280px;height:720px;page-break-after:always;break-after:page}}
  #nav,#tip{{display:none}}
  *{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
}}
"""

JS = """
const S=[...document.querySelectorAll('.slide')];let i=0;
function show(n){i=Math.max(0,Math.min(S.length-1,n));S.forEach((s,k)=>s.classList.toggle('on',k===i));
 document.getElementById('pg').textContent=(i+1)+' / '+S.length;try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function fit(){const d=document.getElementById('deck');const s=Math.min(innerWidth/1280,innerHeight/720);d.style.transform='scale('+s+')'}
addEventListener('resize',fit);
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' ','Enter'].includes(e.key)){show(i+1);e.preventDefault()}
 if(['ArrowLeft','PageUp','Backspace'].includes(e.key)){show(i-1);e.preventDefault()}
 if(e.key==='Home')show(0);if(e.key==='End')show(S.length-1)});
document.getElementById('prev').onclick=()=>show(i-1);document.getElementById('next').onclick=()=>show(i+1);
const nav=document.getElementById('nav');let nt;addEventListener('mousemove',()=>{nav.classList.add('show');clearTimeout(nt);nt=setTimeout(()=>nav.classList.remove('show'),1800)});
const tip=document.getElementById('tip');
document.querySelectorAll('.hov').forEach(r=>{
 r.addEventListener('mousemove',e=>{tip.innerHTML=r.dataset.tip;tip.style.opacity=1;
  let x=e.clientX+16,y=e.clientY+14;const w=tip.offsetWidth,h=tip.offsetHeight;
  if(x+w>innerWidth-8)x=e.clientX-w-16;if(y+h>innerHeight-8)y=e.clientY-h-14;tip.style.left=x+'px';tip.style.top=y+'px';
  const xh=r.ownerSVGElement.querySelector('.xhair');if(xh&&r.dataset.x){xh.setAttribute('x1',r.dataset.x);xh.setAttribute('x2',r.dataset.x);xh.setAttribute('opacity',.5)}});
 r.addEventListener('mouseleave',()=>{tip.style.opacity=0;const xh=r.ownerSVGElement.querySelector('.xhair');if(xh)xh.setAttribute('opacity',0)})});
const h=parseInt((location.hash||'#1').slice(1),10);fit();show(isNaN(h)?0:h-1);
"""

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UIO V19 vs V20</title>
<style>{CSS}</style></head>
<body>
<div id="stage"><div id="deck">{''.join(slides)}</div></div>
<div id="nav"><button id="prev" aria-label="Previous">‹</button><span id="pg"></span><button id="next" aria-label="Next">›</button></div>
<div id="tip"></div>
<script>{JS}</script>
</body></html>"""
open(OUT, "w", encoding="utf-8").write(doc)
print("written", OUT, len(doc) // 1024, "KB")
print("gap30", gap30, "gap26", gap26, "cv", cv_gap, "lcv", lcv_gap, "it", it_gap, "uk", uk_gap, "isr", isr_gap)
print("top", [(c, round(v)) for c, v in top], "other", round(other))
