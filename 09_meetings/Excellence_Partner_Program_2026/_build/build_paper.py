"""Build the white paper (HTML + PDF) from the Markdown source and the ROI model.

Inputs : Excellence_Partner_White_Paper_2026-10-09.md  (placeholders {{CHART:x}} and {{TABLE:x}})
         Excellence_Partner_ROI_Model_2026-10-09.xlsx   (recalculated, cached values)
         order_mix_fy2026.csv, IDS payloads, bp_fy27_reviewed.json
Outputs: Excellence_Partner_White_Paper_2026-10-09.html (self-contained) and .pdf

Run from the ISZE root:  python 09_meetings/Excellence_Partner_Program_2026/_build/build_paper.py [--no-pdf]
"""
import html
import json
import re
import sys
from pathlib import Path

import markdown
import pandas as pd
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = HERE.parents[2]
MD = PACK / "Excellence_Partner_White_Paper_2026-10-09.md"
OUT_HTML = PACK / "Excellence_Partner_White_Paper_2026-10-09.html"
OUT_PDF = PACK / "Excellence_Partner_White_Paper_2026-10-09.pdf"

wb = load_workbook(PACK / "Excellence_Partner_ROI_Model_2026-10-09.xlsx", data_only=True)
inp, dist, var, uni, sens = wb["Inputs"], wb["Distributors"], wb["Design_variants"], wb["Universe"], wb["Sensitivity"]
V = lambda ws, ref: ws[ref].value

INK, RED, AMB, BLU, GRN, GRY, LGT = "#1d2124", "#D71920", "#E6A23C", "#4f6d8f", "#2e7d4f", "#8a9096", "#e6e8ea"
NAMES = ["1 Deck", "2 Growth only", "3 Hybrid small", "4 Hybrid bigger", "5 Tiered"]
COLS = [BLU, GRN, AMB, RED, GRY]


def eur(v):
    a = abs(v)
    s = "−" if v < 0 else ""
    return f"{s}€{a/1e6:.2f}M" if a >= 1e6 else f"{s}€{a/1e3:,.0f}k"


def pct(v, d=1):
    return f"{v*100:.{d}f}%"


REBATE = V(inp, "B14")
designs = []
for k in range(5):
    designs.append({"name": NAMES[k], "y": [V(var, f"{c}{10+k}") for c in "BCD"], "tot": V(var, f"E{10+k}"),
                    "net": [V(var, f"{c}{24+k}") for c in "CDE"], "be": V(var, f"F{24+k}")})

svg_open = lambda w, h: f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" font-family="Arial,Helvetica,sans-serif" role="img">'


def T(x, y, s, sz=13, col=INK, anc="start", wt=400):
    return f'<text x="{x}" y="{y}" font-size="{sz}" fill="{col}" text-anchor="{anc}" font-weight="{wt}">{html.escape(str(s))}</text>'


def fig(inner, cap, src):
    return f'<figure class="chart">{inner}<figcaption>{cap}</figcaption><p class="source">Source: {src}</p></figure>'


# ---------------------------------------------------------------- charts
def chart_coverage():
    rows = [("Isuzu Truck UK", "no", "dealer", "2025 only, 64 dealers"), ("Isuzu UK pickup", "yes", "net", "automated monthly feed agreed"),
            ("Ireland", "yes", "net", "sent to Nov 2025, monthly to follow"), ("UTI", "yes", "net", ""), ("Portugal", "yes", "net", "agreed in principle, Jul 2026"),
            ("Greece", "no", "net", "monthly feed agreed"), ("Romania", "no", "net", "after formal request, Sep 2026"),
            ("Germany", "yes", "reg", "monthly since May 2025 per minutes"), ("Benelux", "yes", "none", "unknown"), ("Sweden", "yes", "none", "unknown"),
            ("Norway", "yes", "none", "unknown"), ("UMI", "yes", "none", "unknown"),
            ("Cyprus, Hungary, Finland, Malta, Denmark, Iceland, Palestine", "no", "none", "unknown")]
    lab = {"dealer": "per dealer", "net": "network total", "reg": "not in register", "none": "nothing on file"}
    cell = "".join(f'<div class="cov-row"><div>{html.escape(n)}</div><div class="muted">{"kickback" if k == "yes" else ""}</div>'
                   f'<div class="pill {g}">{lab[g]}</div><div class="muted">{html.escape(note)}</div></div>' for n, k, g, note in rows)
    return fig(f'<div class="cov">{cell}</div>', "<b>Sales to dealer: what is on file, and what the field says</b> · best detail per distributor",
               "sales-to-dealer register and long files; August 2026 sales-review minutes. ‘Not in register’ means the minutes record a feed that the workspace does not hold.")


def chart_cost():
    w, h, x0, x1, mx = 900, 330, 270, 760, 1_000_000
    o = svg_open(w, h)
    for g in range(5):
        gx = x0 + (x1 - x0) * g / 4
        o += f'<line x1="{gx}" y1="20" x2="{gx}" y2="270" stroke="{LGT}"/>' + T(gx, 292, "€0" if g == 0 else eur(g * 250000), 12, GRY, "middle")
    for i, d in enumerate(designs):
        y = 30 + i * 48
        v = d["y"][2]
        o += T(x0 - 12, y + 18, d["name"], 14, INK, "end", 700) + f'<rect x="{x0}" y="{y}" width="{(x1-x0)*v/mx:.1f}" height="28" fill="{COLS[i]}" rx="3"/>'
        o += T(x0 + (x1 - x0) * v / mx + 8, y + 19, f"{eur(v)} ({v/REBATE:.1f}× today)", 13, INK, "start", 700)
    lx = x0 + (x1 - x0) * REBATE / mx
    o += f'<line x1="{lx}" y1="14" x2="{lx}" y2="272" stroke="{AMB}" stroke-width="2" stroke-dasharray="6 4"/>' + T(lx + 5, 12, f"rebates paid today {eur(REBATE)}", 12, AMB, "start", 700)
    return fig(o + "</svg>", "<b>Discount cost per year in year 3 (FY2030), five designs, same 19 distributors</b>", "ROI model, Design_variants; rebate credits from billing FY2026.")


def chart_net():
    w, h, x0, x1 = 900, 380, 290, 860
    vmin, vmax = -2_000_000, 1_000_000
    px = lambda v: x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)
    o = svg_open(w, h)
    for v in range(vmin, vmax + 1, 500_000):
        o += f'<line x1="{px(v)}" y1="20" x2="{px(v)}" y2="330" stroke="{LGT}"/>' + T(px(v), 352, "€0" if v == 0 else eur(v), 12, GRY, "middle")
    o += f'<line x1="{px(0)}" y1="20" x2="{px(0)}" y2="330" stroke="{INK}" stroke-width="1.5"/>'
    for i, d in enumerate(designs):
        y = 30 + i * 60
        lo, mid, hi = d["net"]
        o += T(x0 - 12, y + 18, d["name"], 14, INK, "end", 700) + T(x0 - 12, y + 34, f"break-even +{pct(d['be'])}", 11, GRY, "end")
        o += f'<rect x="{min(px(0), px(mid)):.1f}" y="{y}" width="{abs(px(mid)-px(0)):.1f}" height="26" fill="{GRN if mid >= 0 else RED}" opacity=".85" rx="3"/>'
        o += f'<line x1="{px(lo):.1f}" y1="{y+13}" x2="{px(hi):.1f}" y2="{y+13}" stroke="{INK}" stroke-width="2.5"/><circle cx="{px(mid):.1f}" cy="{y+13}" r="6" fill="{INK}"/>'
        o += T(px(max(mid, hi, 0)) + 12, y + 19, eur(mid), 13, INK, "start", 700)
    return fig(o + "</svg>", "<b>Net result over three years by design</b> · dot = Base case · line = Low to High", "ROI model, Design_variants. Low, Base and High are our assumptions, not measured results.")


def chart_ladder():
    w, h, X0, X1, Y0, Y1 = 900, 400, 70, 860, 340, 30
    gmin, gmax, rmax = -0.10, 0.20, 0.07
    px = lambda g: X0 + (X1 - X0) * (g - gmin) / (gmax - gmin)
    py = lambda r: Y0 - (Y0 - Y1) * r / rmax
    o = svg_open(w, h)
    for r in range(8):
        o += f'<line x1="{X0}" y1="{py(r/100)}" x2="{X1}" y2="{py(r/100)}" stroke="{LGT}"/>' + T(X0 - 8, py(r / 100) + 4, f"{r}%", 12, GRY, "end")
    for g in range(-10, 21, 5):
        o += T(px(g / 100), Y0 + 22, f"{g:+d}%" if g else "0%", 12, GRY, "middle")
    o += T((X0 + X1) / 2, Y0 + 46, "growth of the distributor's stock orders against last year", 12, GRY, "middle")

    def hy(col):
        return {"f1": V(inp, f"{col}41"), "l1": V(inp, f"{col}43"), "l2": V(inp, f"{col}44"), "r1": [V(inp, f"{col}{r}") for r in (45, 46, 47)]}

    def bonus(g, p):
        if g <= 0:
            return p["f1"]
        a = min(g, p["l1"]); b = max(0, min(g, p["l2"]) - p["l1"]); c = max(0, g - p["l2"])
        return p["f1"] + p["r1"][0] * a + p["r1"][1] * b + p["r1"][2] * c

    tiers = ([V(inp, "B33"), V(inp, "B34"), V(inp, "B35")], [V(inp, f"C{r}") for r in (33, 34, 35, 36)])
    tier = lambda g: tiers[1][0] if g < tiers[0][0] else tiers[1][1] if g < tiers[0][1] else tiers[1][2] if g < tiers[0][2] else tiers[1][3]
    mu, sg = V(inp, "B12"), V(inp, "B31")
    import math
    pts = " ".join(f"{px(gmin + (gmax-gmin)*k/60):.1f},{Y0 - 55*math.exp(-0.5*((gmin+(gmax-gmin)*k/60-mu)/sg)**2):.1f}" for k in range(61))
    o += f'<polygon points="{pts} {px(gmax)},{Y0} {px(gmin)},{Y0}" fill="{INK}" opacity=".07"/>' + T(X0 + 8, Y1 + 12, "grey shape: where distributors land in a normal year", 11, GRY)

    def path(fn, col, wd):
        d = " ".join(("M" if k == 0 else "L") + f"{px(gmin+(gmax-gmin)*k/300):.1f},{py(fn(gmin+(gmax-gmin)*k/300)):.1f}" for k in range(301))
        return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{wd}" stroke-linejoin="round"/>'

    o += path(lambda g: V(inp, "B4"), GRY, 2.5) + T(px(-0.095), py(V(inp, "B4")) - 8, "Deck: flat 2.5% on all stock orders", 12, GRY, "start", 700)
    o += path(tier, BLU, 2.5) + T(px(0.2), py(0.05) - 8, "Tiered: all stock orders, jumps at each limit", 12, BLU, "end", 700)
    o += path(lambda g: bonus(g, hy("C")), RED, 3) + T(px(0.2), py(bonus(0.2, hy("C"))) - 10, "Hybrid bigger (level 1)", 12, RED, "end", 700)
    o += path(lambda g: bonus(g, hy("B")), AMB, 3) + T(px(0.2), py(bonus(0.2, hy("B"))) - 10, "Hybrid small (level 1)", 12, AMB, "end", 700)
    o += f'<line x1="{px(mu)}" y1="{Y1}" x2="{px(mu)}" y2="{Y0}" stroke="{INK}" stroke-dasharray="4 4" opacity=".5"/>' + T(px(mu) + 5, Y1 + 12, "planned growth +5%", 11, INK)
    return fig(o + "</svg>", "<b>Reward as % of last year's stock orders, by the distributor's own growth</b> · level 1", "ROI model, Inputs. The hybrids pay each band's rate only on the growth inside that band; tiered pays one rate on everything.")


def chart_power():
    w, h = 900, 330
    ns = [4, 6, 8, 9]
    sgs = [(0.138, "spread 13.8% (FY2026)", AMB), (0.205, "spread 20.5% (two-year pooled)", RED)]
    o = svg_open(w, h)
    x0, x1, mx = 90, 860, 0.45
    py = lambda v: 270 - 240 * v / mx
    for g in (0, 0.1, 0.2, 0.3, 0.4):
        o += f'<line x1="{x0}" y1="{py(g)}" x2="{x1}" y2="{py(g)}" stroke="{LGT}"/>' + T(x0 - 8, py(g) + 4, f"{int(g*100)}%", 12, GRY, "end")
    gw = (x1 - x0) / len(ns)
    for i, n in enumerate(ns):
        cx = x0 + gw * i + gw / 2
        o += T(cx, 296, f"{n} per group" + (" (the most 19 allow)" if n == 9 else ""), 12, GRY, "middle")
        for j, (sg, lab, col) in enumerate(sgs):
            mde = 2.8 * sg * (2 / n) ** 0.5
            bx = cx - 52 + j * 54
            o += f'<rect x="{bx}" y="{py(mde):.1f}" width="48" height="{270-py(mde):.1f}" fill="{col}" rx="2"/>' + T(bx + 24, py(mde) - 5, pct(mde, 0), 12, INK, "middle", 700)
    o += f'<line x1="{x0}" y1="{py(0.03)}" x2="{x1}" y2="{py(0.03)}" stroke="{GRN}" stroke-width="2" stroke-dasharray="6 4"/>'
    for j, (sg, lab, col) in enumerate(sgs):
        o += f'<rect x="{x0 + j*260}" y="312" width="12" height="12" fill="{col}"/>' + T(x0 + j * 260 + 18, 323, lab, 12)
    o += f'<line x1="{x0 + 520}" y1="318" x2="{x0 + 548}" y2="318" stroke="{GRN}" stroke-width="2" stroke-dasharray="6 4"/>' + T(x0 + 554, 323, "effect in the High case: 3%", 12)
    return fig(o + "</svg>", "<b>Smallest effect a one-year comparison between distributors could detect</b> (80% power, 5% significance)", "gps_clean_all_fy_v2.csv, FY2025 and FY2026, twelve larger distributors; MDE ≈ 2.8 × spread × √(2 ÷ n).")


def chart_timeline():
    w, h = 900, 330
    months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"]
    x0, cw = 250, 31
    o = svg_open(w, h)
    for i, m in enumerate(months):
        o += T(x0 + i * cw + cw / 2, 18, m, 11, GRY, "middle")
    o += T(x0 + 1.5 * cw, 34, "2026", 11, INK, "middle", 700) + T(x0 + 8 * cw, 34, "2027", 11, INK, "middle", 700) + T(x0 + 17 * cw, 34, "2028", 11, INK, "middle", 700)
    tasks = [("Management paper, concept and ceiling", 0, 2, RED), ("Legal review, written rules, register update", 1, 3, BLU), ("Phase 0: intake, validator, report", 2, 5, AMB),
             ("No-discount trial, 3–4 distributors", 3, 6, GRN), ("SAP condition, trainings ready", 5, 6, BLU), ("Level 1 live (FY2028)", 6, 19, RED),
             ("Quarterly checks", 8, 19, GRY), ("Phase 1 decision, if indicators say so", 11, 14, AMB), ("Level 2 assessment and award", 17, 19, GRN)]
    for i, (n, a, b, c) in enumerate(tasks):
        y = 46 + i * 31
        o += T(x0 - 8, y + 16, n, 12, INK, "end") + f'<rect x="{x0 + a*cw}" y="{y}" width="{(b-a+ (0.0))*cw:.1f}" height="20" fill="{c}" rx="3"/>'
    ax = x0 + 6 * cw
    o += f'<line x1="{ax}" y1="40" x2="{ax}" y2="{46+len(tasks)*31}" stroke="{INK}" stroke-dasharray="4 3"/>' + T(ax + 4, 328, "1 April 2027", 12, INK, "start", 700)
    return fig(o + "</svg>", "<b>Timeline, October 2026 to May 2028</b>", "chapter 9 of this paper; owners and dates are proposals.")


CHARTS = {"coverage": chart_coverage, "cost": chart_cost, "net": chart_net, "ladder": chart_ladder, "power": chart_power, "timeline": chart_timeline}


# ---------------------------------------------------------------- tables (as Markdown)
def mdtable(head, rows, align=None):
    a = align or ["---"] * len(head)
    return "\n".join(["| " + " | ".join(head) + " |", "| " + " | ".join(a) + " |"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def table_designs():
    rows = [[d["name"], eur(d["y"][0]), eur(d["y"][1]), eur(d["y"][2]), eur(d["tot"]), f"{d['y'][2]/REBATE:.1f}×"] for d in designs]
    return mdtable(["Design", "Year 1 FY2028", "Year 2 FY2029", "Year 3 FY2030", "3 years", "Year 3 against rebates today"], rows, ["---", "---:", "---:", "---:", "---:", "---:"])


def table_results():
    rows = [[d["name"], eur(d["tot"]), eur(d["net"][0]), eur(d["net"][1]), eur(d["net"][2]), "+" + pct(d["be"])] for d in designs]
    return mdtable(["Design", "3-year cost", "Net, Low", "Net, Base", "Net, High", "Extra sales to break even (year 3)"], rows, ["---", "---:", "---:", "---:", "---:", "---:"])


def table_sens():
    rows = []
    for r in range(5, 14):
        rows.append([pct(V(sens, f"A{r}"), 0)] + [eur(V(sens, f"{c}{r}")) for c in "BCDEF"])
    return mdtable(["Extra sales beyond plan", "1 Deck", "2 Growth only", "3 Hybrid small", "4 Hybrid bigger", "5 Tiered"], rows, ["---:"] * 6) + \
        "\n\nNet result per year at full effect, year-3 participants, extra sales as the only benefit. Negative: the programme costs more than it earns."


def table_dist():
    ids = json.loads((ROOT / "01_data/08_Distributor/IDS_2026/reports/kaizen_ids/study_payload.json").read_text(encoding="utf-8"))
    idsmap = {c["country"]: c["total_pct"] for c in ids["country_matrix"]}
    cards = json.loads((ROOT / "01_data/08_Distributor/IDS_2026/reports/kaizen_db_posture/study_payload.json").read_text(encoding="utf-8"))["db_cards"]
    fill = {c["ids_country"]: c.get("kpi_fill_rate") for c in cards}
    kp = json.loads((ROOT / "01_data/08_Distributor/IDS_2026/reports/kaizen_db_posture/study_payload.json").read_text(encoding="utf-8"))["kpi_spu_coverage"]["rows"]
    for rr in kp:
        for ctry in str(rr["ids_countries"]).split(", "):
            if rr.get("kpi_fill_rate") and not fill.get(ctry):
                fill[ctry] = rr["kpi_fill_rate"]
    code2ids = {"ITUK": "ITUK", "IUK": "IUK", "UMI": "ISRAEL", "BELGIUM": "BE", "PORTUGAL": "PORTUGAL", "NORWAY": "RSA", "GREECE": "PETROS", "CYPRUS": "CYPRUS",
                "HUNGARY": "HUNGARY", "MALTA": "MALTA", "ROMANIA": "ROMANIA", "DENMARK": "DENMARK"}
    bp = json.loads((ROOT / "01_data/91_build/bp_fy27_reviewed.json").read_text(encoding="utf-8"))["by_gps_code"]
    rows = []
    for r in range(5, 24):
        code = V(dist, f"A{r}")
        billed, sor = V(dist, f"C{r}"), V(dist, f"D{r}")
        ic = code2ids.get(code)
        rows.append([V(dist, f"B{r}"), eur(billed), eur(sor), pct(V(dist, f"E{r}"), 0), eur(V(dist, f"R{r}")) if V(dist, f"R{r}") else "–",
                     V(dist, f"G{r}") if V(dist, f"G{r}") != "nothing on file" else "–", pct(idsmap[ic]) if ic in idsmap else "–",
                     pct(fill[ic], 0) if ic in fill and fill[ic] else "–", pct(bp[code] / billed - 1, 0) if code in bp else "–",
                     f"{V(dist, f'I{r}')}/{V(dist, f'J{r}')}/{V(dist, f'K{r}')}"])
    return mdtable(["Distributor", "Billed FY2026", "Stock orders", "Share", "Rebate credits FY2026", "Sales to dealer in workspace", "IDS 2026", "First fill rate", "Plan growth FY2027", "Plan level Y1/Y2/Y3"],
                   rows, ["---", "---:", "---:", "---:", "---:", "---", "---:", "---:", "---:", "---"]) + \
        "\n\nBenelux IDS is Belgium only (Netherlands 76.1%). Plan growth = reviewed business plan FY2027 against FY2026 billed. Plan level is the illustrative participation plan of the model (0 = not in, 1 = level 1, 2 = level 2). Fill rate: KPI master, average of available months."


TABLES = {"designs": table_designs, "results": table_results, "sensitivity": table_sens, "distributors": table_dist}

# ---------------------------------------------------------------- convert
src = MD.read_text(encoding="utf-8")
src = re.sub(r"\{\{TABLE:(\w+)\}\}", lambda m: "\n" + TABLES[m.group(1)]() + "\n", src)
holders = {}


def keep(m):
    k = f"CHARTHOLDER{len(holders)}X"
    holders[k] = CHARTS[m.group(1)]()
    return f"\n\n{k}\n\n"


src = re.sub(r"\{\{CHART:(\w+)\}\}", keep, src)
title_m = re.match(r"# (.*)\n", src)
src = re.sub(r"^# .*\n", "", src, count=1)
src = re.sub(r"^\*\*The case, the economics and the design\*\*.*\n", "", src, count=1, flags=re.M)
body = markdown.markdown(src, extensions=["tables", "sane_lists"])
for k, v in holders.items():
    body = body.replace(f"<p>{k}</p>", v)
toc = []


def addid(m):
    lvl, inner = m.group(1), m.group(2)
    plain = re.sub(r"<[^>]+>", "", inner)
    sid = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:60]
    if lvl == "2":
        toc.append((sid, plain))
    return f'<h{lvl} id="{sid}">{inner}</h{lvl}>'


body = re.sub(r"<h([23])>(.*?)</h\1>", addid, body)
body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
body = re.sub(r"\*\*\[([MIAPU])\]\*\*", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span>', body)
body = re.sub(r"<strong>\[([MIAPU])\]</strong>", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span>', body)
body = re.sub(r"<strong>\[([MIAPU])\]/\[([MIAPU])\]</strong>", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span><span class="tag t{m.group(2)}">{m.group(2)}</span>', body)
nav = "".join(f'<a href="#{s}">{html.escape(t)}</a>' for s, t in toc)

CSS = """
:root{--ink:#1d2124;--mut:#5f676e;--line:#dfe2e5;--panel:#f4f5f6;--red:#D71920;--navy:#15233C;--bg:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.6 Arial,Helvetica,sans-serif}
header.cover{background:#24282C;color:#fff;padding:44px 28px 36px}
header.cover .in{max-width:1180px;margin:0 auto}
.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#ff6b70;font-weight:700}
header.cover h1{font-size:38px;line-height:1.15;margin:8px 0 8px}
header.cover p{margin:0;color:#c9ced3;max-width:800px;font-size:17px}
.layout{max-width:1180px;margin:0 auto;display:grid;grid-template-columns:240px minmax(0,1fr);gap:36px;padding:24px 28px}
.layout>*{min-width:0}
nav.toc{position:sticky;top:12px;align-self:start;max-height:calc(100vh - 24px);overflow:auto;font-size:13px}
nav.toc a{display:block;color:var(--ink);text-decoration:none;padding:4px 0 4px 10px;border-left:2px solid var(--line)}
nav.toc a:hover{border-left-color:var(--red);color:var(--red)}
main h2{font-size:25px;margin:48px 0 10px;padding-top:10px;border-top:2px solid var(--ink)}
main h3{font-size:18px;margin:26px 0 8px;color:var(--navy)}
main p,main li{max-width:860px}
main code{font-size:12.5px;background:var(--panel);padding:1px 5px;border-radius:4px;word-break:break-all}
main hr{border:none;border-top:1px solid var(--line);margin:26px 0}
.tablewrap{overflow-x:auto;margin:14px 0 20px;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:7px 9px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--panel);font-weight:700}tr:last-child td{border-bottom:none}
.tag{display:inline-block;font-size:10.5px;font-weight:700;border-radius:4px;padding:0 5px;margin:0 2px;vertical-align:1px;color:#fff;line-height:16px}
.tM{background:#2e7d4f}.tI{background:#4f6d8f}.tA{background:#b26a00}.tP{background:#6b4fa0}.tU{background:#8a9096}
figure.chart{margin:18px 0 24px;padding:14px 16px;background:var(--panel);border-radius:10px;max-width:900px}
figure.chart svg{width:100%;height:auto;display:block}
figcaption{font-size:13.5px;margin:0 0 10px}
.source{font-size:11.5px;color:var(--mut);margin:8px 0 0}
.muted{color:var(--mut)}
.cov-row{display:grid;grid-template-columns:minmax(0,1.5fr) 70px 140px minmax(0,1.3fr);gap:8px;align-items:center;padding:4px 0;border-bottom:1px solid var(--line);font-size:12.5px}
.cov-row:last-child{border-bottom:none}
.pill{font-size:11.5px;font-weight:700;border-radius:999px;padding:2px 8px;text-align:center;color:#fff}
.pill.dealer{background:#2e7d4f}.pill.net{background:#b26a00}.pill.reg{background:#6b4fa0}.pill.none{background:#c9ced3;color:#1d2124}
footer{max-width:1180px;margin:0 auto;padding:0 28px 40px;font-size:12px;color:var(--mut)}
@media screen and (max-width:900px){.layout{grid-template-columns:1fr;padding:16px}nav.toc{position:static;max-height:none}header.cover h1{font-size:28px}
.cov-row{grid-template-columns:minmax(0,1fr) auto}.cov-row div:nth-child(2),.cov-row div:nth-child(4){grid-column:1/-1}}
@media print{body{font-size:11.5px}nav.toc{display:none}.layout{grid-template-columns:1fr;padding:0}header.cover{padding:24px 0;background:#fff;color:#000}
header.cover p{color:#333}main h2{break-after:avoid;margin-top:28px}figure.chart,.tablewrap{break-inside:avoid}.tag{border:1px solid #888}}
"""
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Excellence Partner Program — white paper</title><style>{CSS}</style></head><body>
<header class="cover"><div class="in"><div class="eyebrow">Internal draft v1 · 9 October 2026</div>
<h1>{html.escape(title_m.group(1))}</h1>
<p>The case, the economics and the design. For management decision and for the developer. Euros, fiscal years, stock orders only. Claims are labelled <span class="tag tM">M</span> measured <span class="tag tI">I</span> inferred <span class="tag tA">A</span> assumption <span class="tag tP">P</span> proposal <span class="tag tU">U</span> unknown.</p></div></header>
<div class="layout"><nav class="toc" aria-label="Contents">{nav}</nav><main>{body}</main></div>
<footer>Built from the Markdown source and the ROI model with _build/build_paper.py. Self-contained: no external files.</footer></body></html>"""
OUT_HTML.write_text(page, encoding="utf-8")
print(OUT_HTML, f"{len(page)/1024:.0f} KB", "h2:", len(toc))

if "--no-pdf" not in sys.argv:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = b.new_page()
        pg.goto(f"file://{OUT_HTML}")
        pg.wait_for_timeout(500)
        pg.pdf(path=str(OUT_PDF), format="A4", print_background=True, margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               display_header_footer=True, header_template="<span></span>",
               footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#666">Excellence Partner Program — internal draft v1 — page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
        b.close()
    print(OUT_PDF)
