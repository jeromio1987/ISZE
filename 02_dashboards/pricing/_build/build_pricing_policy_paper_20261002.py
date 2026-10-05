# -*- coding: utf-8 -*-
"""
Builds the parts pricing policy paper of 2 October 2026 for management.

Rewritten on 2 October 2026 for a management audience: every decision is named by what it does,
with its reason and its euro effect; no internal working labels; distributors named in words; the
average IML/IMIT price increase to ISZE is computed here and stated up front.

Self-contained HTML (no CDN, no script, charts as inline SVG drawn here), then a PDF via headless Chrome.

Numbers read at build time (traceable; file names stay in this docstring, never in the paper):
  _build/price_5pct_proposal_2026-09-29/price_5pct_proposal_summary_2026-09-29.json   +5% build
  _build/price_5pct_proposal_2026-09-29/market_exercise_decisions_2026-09-30.json      21-market decisions
  _build/price_5pct_proposal_2026-09-29/market_facts_2026-09-30.json                   market grid
  _build/price_5pct_proposal_2026-09-29/dealer_price_response_2026-09-29.json          dealer response
  _build/price_5pct_proposal_2026-09-29/room_to_raise_2026-10-02/*                     recovery of the EUR 389k
  _build/price_5pct_proposal_2026-09-29/uti_panels_2026-10-02/*                        Israel truck panels
  01_data/01_Pricing/Price_Increase_5pct_Proposal_2026-09-29.xlsx (read only)          source of supply per part
IML/IMIT increase = per-part factory base-price change (Sep 2026 revision vs Sep 2025, yen), weighted by
parts billed Jul 2025 - Jun 2026 (room_to_raise_by_part: factory_move x billed_eur_l12m).

Run:   python 02_dashboards/pricing/_build/build_pricing_policy_paper_20261002.py
Writes 02_dashboards/pricing/ISZE_Pricing_Policy_Paper_2026-10-02.html
       02_dashboards/pricing/OPEN_ISZE_Pricing_Policy_Paper_2026-10-02.cmd   (CRLF, cmd-only opener)
PDF:   python <visueel-rapport>/scripts/render_and_qa.py <html> <pdf>
"""
from __future__ import annotations

import html
import io
import re
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PR = ISZE / "02_dashboards" / "pricing"
PROP = PR / "_build" / "price_5pct_proposal_2026-09-29"
RTR = PROP / "room_to_raise_2026-10-02"
PROPXL = ISZE / "01_data" / "01_Pricing" / "Price_Increase_5pct_Proposal_2026-09-29.xlsx"
OUT_HTML = PR / "ISZE_Pricing_Policy_Paper_2026-10-02.html"
OUT_CMD = PR / "OPEN_ISZE_Pricing_Policy_Paper_2026-10-02.cmd"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ======================================================================= data
PSUM = jload(PROP / "price_5pct_proposal_summary_2026-09-29.json")
DEC = jload(PROP / "market_exercise_decisions_2026-09-30.json")
MF = jload(PROP / "market_facts_2026-09-30.json")
RESP = jload(PROP / "dealer_price_response_2026-09-29.json")
RS = jload(RTR / "room_to_raise_summary_2026-10-02.json")
VAR = jload(RTR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.json")
SCN = pd.read_csv(RTR / "room_to_raise_scenarios_2026-10-02.csv")
SEG = pd.read_csv(RTR / "room_to_raise_scenarios_by_segment_market_2026-10-02.csv")
LEV = pd.read_csv(RTR / "lever4_order_terms_2026-10-02.csv").set_index("db")
CATR = pd.read_csv(RTR / "dealer_response_by_category_2026-10-02.csv")
VMK = pd.read_csv(RTR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.csv").set_index("market")
PART = pd.read_csv(RTR / "room_to_raise_by_part_2026-10-02.csv", dtype={"pn": str}, low_memory=False)
UTIP = PROP / "uti_panels_2026-10-02"
UN = jload(UTIP / "_numbers.json")
UNB = jload(UTIP / "_numbers_bo_trend.json")
UBO = pd.read_csv(UTIP / "t6b_uti_backorder_summary.csv").set_index("seg")
UST = pd.read_csv(UTIP / "t8b_uti_step_master_vs_release.csv")
UBW = pd.read_csv(UTIP / "t13b_uti_bo_weekly_summary.csv")
REC = pd.read_csv(UTIP / "t13c_uti_bo_body_recurring_parts.csv")
XP = pd.read_excel(PROPXL, "Proposal", usecols=["Part number", "Source of supply"], dtype={"Part number": str})

BASE = RS["proposal"]["base_eur"]
INC = RS["proposal"]["step_eur"]          # euro value of the +5% on parts billed
K = RS["proposal"]["scaling_k"]
assert abs(K - PSUM["k"]) < 1e-6 and abs(INC - PSUM["step_eur"]) < 1
GIVEN = RS["holds"]["recomputed_total_step"]     # euro given up by the market decisions (EUR 389k)
HR = RS["holds"]["recomputed_here"]


def scen(letter, ceiling="factory+5pts", panels=False):
    s = SCN[(SCN.scenario.str.startswith(letter)) & (SCN.ceiling == ceiling) & (SCN.uti_panels_held == panels)]
    assert len(s) == 1
    return s.iloc[0]


WA, WB, WC = scen("A"), scen("B"), scen("C")     # the three ways of recovering the EUR 389k; WB decided
WB12 = scen("B", "12% max")
VB, VI = VAR["B_as_published"], VAR["B_iuk_exempt"]
assert abs(VB["uplift_above_proposal_eur"] - WB.uplift_above_proposal_eur) < 2 and abs(VB["solver_t_pts"] - WB.solver_t) < 1e-5
assert abs(VI["total_step_eur"] - INC) < 2
assert abs(GIVEN - WB.held_step_given_up_eur) < 2


def segavg(letter, dim, group):
    s = SEG[(SEG.scenario.str.startswith(letter)) & (SEG.ceiling == "factory+5pts") & (~SEG.uti_panels_held)
            & (SEG.dimension == dim) & (SEG.group == group)].iloc[0]
    return s.step_eur / s.billed_eur, s.proposal_step_eur / s.billed_eur, s.billed_eur


SUF = RS["sufficiency"]
IDX = RS["index_distribution"]
L4 = RS["lever4_cy2025"]
P7 = RS["p700_new_only"]
r_iuk = RESP["four_markets_april_2026"]["by_market"]["IUK (UK D-Max)"]
r_pool = RESP["four_markets_april_2026"]["pooled"]
iuk_units = RESP["four_markets_april_2026"]["dealer_units"]["IUK (UK D-Max)"]["change"]
inv = RESP["invoice_check_ituk"]["April 2026"]
prev_rev = RESP["cy2026_cd_weighted_base_price_move"]["value"]
cat_iuk_body = CATR[(CATR.market == "IUK") & (CATR.aim_l1 == "Accident & Body")].iloc[0]
maxpart = PART.loc[PART.proposal_move.idxmax()]
pads = PART[PART.padkit == 1]
pad794 = PART[PART.pn == "8982447940"].iloc[0]
pad922 = PART[PART.pn == "8982169220"].iloc[0]
lost_parts = int((PART.h_lost > 0).sum())
extra_parts = int(((PART.proposal_move > PART.factory_move.clip(lower=0) * K * (1 - PART.h_lost) + 1e-4)
                   & (PART.padkit == 0)).sum())
fact15 = int((PART.factory_move > 0.15).sum())

# ----------------------------------------------------------------------- IML / IMIT increase to ISZE (computed)
b = PART.billed_eur_l12m
fm = PART.factory_move
assert abs(b.sum() - BASE) < 5, (b.sum(), BASE)
FM_AVG = float((fm * b).sum() / b.sum())
FM_EUR = float((fm * b).sum())
FM_SEG = {s: float((g.factory_move * g.billed_eur_l12m).sum() / g.billed_eur_l12m.sum()) for s, g in PART.groupby("segment")}
SEG_BILLED = PART.groupby("segment").billed_eur_l12m.sum().to_dict()
_src = PART.merge(XP.rename(columns={"Part number": "pn", "Source of supply": "src"}), on="pn", how="left")
assert _src.src.notna().all()
FM_SRC = {s: (float((g.factory_move * g.billed_eur_l12m).sum() / g.billed_eur_l12m.sum()), float(g.billed_eur_l12m.sum()), len(g))
          for s, g in _src.groupby("src")}
FM_QTY = PSUM["recipe_check"]          # same revision, weighted by quantity x yen base price
NO_RISE_PARTS = int((fm <= 0).sum())
NO_RISE_SHARE = float(b[fm <= 0].sum() / b.sum())

# bridge: full IML/IMIT increase -> 90.5% pass-on -> exceptions -> +5.00%
D_FULL = FM_EUR
D_K = float((K * fm.clip(lower=0) * b).sum())
D_PADS = float((K * fm.clip(lower=0) * b)[PART.padkit == 1].sum())
D_LOST = float((K * fm.clip(lower=0) * b * PART.h_lost)[PART.padkit == 0].sum())
np_ = PART.padkit == 0
D_EXTRA = float(((PART.proposal_move - K * fm.clip(lower=0) * (1 - PART.h_lost)).clip(lower=0) * b)[np_].sum())
D_OTHER = float((PART.proposal_move * b).sum()) - (D_K - D_PADS - D_LOST + D_EXTRA)
assert abs((D_K - D_PADS - D_LOST + D_EXTRA + D_OTHER) - INC) < 2
assert abs(D_OTHER) < 3000, D_OTHER

# ----------------------------------------------------------------------- parts categories (approved 2 Oct)
CAT_UNK = PART.aim_l1_fixed.fillna("Unknown").str.startswith("Unknown")
CAT_FAM = PART[~CAT_UNK].aim_l1_fixed.nunique()
CAT_L2 = PART[~CAT_UNK].aim_l2_fixed.nunique()
CAT_L3 = PART[~CAT_UNK].aim_l3_fixed.nunique()
CAT_UNK_PARTS = int(CAT_UNK.sum())
CAT_UNK_EUR = float(PART[CAT_UNK].billed_eur_l12m.sum())
CAT_TOP = PART[~CAT_UNK].groupby("aim_l1_fixed").billed_eur_l12m.sum().sort_values(ascending=False).head(12)
PADS_CAT = float(PART[PART.aim_l2_fixed == "Pads & Shoes"].billed_eur_l12m.sum())

# ======================================================================= formatting
def e0(x):
    return f"EUR {x:,.0f}"


def ek(x):
    return f"EUR {x / 1e3:,.0f}k"


def em(x, d=2):
    return f"EUR {x / 1e6:,.{d}f}M"


def p1(x, sign=False):
    return f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%"


def p0(x, sign=False):
    return f"{x * 100:+.0f}%" if sign else f"{x * 100:.0f}%"


def esc(s):
    return html.escape(str(s))


# ======================================================================= colours (house style)
NAVY, NAVY2, TERRA = "#1a2b4a", "#2b4a78", "#c0552d"
BLUE, LBLUE, GREY, RED, GREEN, AMBER = "#2a78d6", "#85b7eb", "#888780", "#e24b4a", "#1d9e75", "#eda100"
INK, GRID, MUTED = "#3d3c38", "#e1e0d9", "#6b6256"
FONT = "Segoe UI, Helvetica, Arial, sans-serif"

NAME = {"IUK": "Isuzu UK (D-Max)", "ITUK": "Isuzu Truck UK", "UTI": "Israel trucks distributor",
        "UMI": "Israel D-Max distributor", "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal",
        "NORWAY": "Norway", "SWEDEN": "Sweden", "IRELAND": "Ireland", "UKRAINE": "Ukraine", "GREECE": "Greece",
        "CYPRUS": "Cyprus", "HUNGARY": "Hungary", "FINLAND": "Finland", "ARMENIA": "Armenia",
        "MALTA": "Malta", "ROMANIA": "Romania", "KAZAKHSTAN": "Kazakhstan", "DENMARK": "Denmark",
        "ICELAND": "Iceland", "PALESTINE": "Palestine"}
SEG_NAME = {"service": "Service parts", "repair": "Repair parts", "body": "Body and collision parts"}


def nice_ticks(vmax, n=5):
    import math
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw:
            step_ = m * mag
            break
    ticks, t = [], 0.0
    while t <= vmax * 1.0001 + 1e-12:
        ticks.append(t)
        t += step_
    if ticks[-1] < vmax:
        ticks.append(ticks[-1] + step_)
    return ticks


def svg_open(w, h, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{esc(label)}" '
            f'style="font-family:{FONT};display:block">')


def svg_hbar(rows, fmt, label, width=680, label_w=230, bar_h=20, gap=9, ref=None, vmax=None, value_w=86):
    """rows: (label, value, colour). Horizontal bars, value printed at the bar end."""
    n = len(rows)
    top, bottom = 6, 26
    h = top + n * (bar_h + gap) + bottom
    plot_w = width - label_w - value_w
    vmax = vmax or max(v for _, v, _ in rows)
    ticks = nice_ticks(vmax, 4)
    vmax = ticks[-1]
    sx = lambda v: label_w + plot_w * v / vmax
    o = [svg_open(width, h, label)]
    for t in ticks:
        x = sx(t)
        o.append(f'<line x1="{x:.1f}" y1="{top - 2}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{GRID}" stroke-width="1"/>')
        o.append(f'<text x="{x:.1f}" y="{h - 8}" font-size="10" fill="{MUTED}" text-anchor="middle">{esc(fmt(t, True))}</text>')
    for i, (lab, v, col) in enumerate(rows):
        y = top + i * (bar_h + gap)
        o.append(f'<text x="{label_w - 8}" y="{y + bar_h / 2 + 4:.1f}" font-size="11" fill="{INK}" text-anchor="end">{esc(lab)}</text>')
        o.append(f'<rect x="{label_w}" y="{y}" width="{max(sx(v) - label_w, 1.5):.1f}" height="{bar_h}" fill="{col}" rx="2"/>')
        o.append(f'<text x="{sx(v) + 6:.1f}" y="{y + bar_h / 2 + 4:.1f}" font-size="11" fill="{INK}" font-weight="600">{esc(fmt(v, False))}</text>')
    if ref is not None:
        rv, rl = ref
        x = sx(rv)
        o.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{TERRA}" stroke-width="1.6" stroke-dasharray="5 3"/>')
        o.append(f'<text x="{x - 4:.1f}" y="{h - bottom - 4}" font-size="10" fill="{TERRA}" text-anchor="end" font-weight="600">{esc(rl)}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_waterfall(cols, label, vmax, tick, tick_fmt, h=250, wrap=20):
    """cols: (label, lo, hi, colour, value text). Floating bars, labels wrapped under each bar."""
    w, left, top, bottom = 680, 60, 22, 66
    plot_h = h - top - bottom
    sy = lambda v: top + plot_h * (1 - v / vmax)
    cw = (w - left - 10) / len(cols)
    o = [svg_open(w, h, label)]
    t = 0.0
    while t <= vmax + 1e-9:
        y = sy(t)
        o.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - 10}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{left - 6}" y="{y + 3.5:.1f}" font-size="10" fill="{MUTED}" text-anchor="end">{tick_fmt(t)}</text>')
        t += tick
    for i, (lab, lo, hi, col, val) in enumerate(cols):
        x = left + i * cw + cw * 0.18
        bw = cw * 0.64
        o.append(f'<rect x="{x:.1f}" y="{sy(hi):.1f}" width="{bw:.1f}" height="{max(sy(lo) - sy(hi), 1.5):.1f}" fill="{col}" rx="2"/>')
        o.append(f'<text x="{x + bw / 2:.1f}" y="{sy(hi) - 6:.1f}" font-size="11" font-weight="600" fill="{INK}" text-anchor="middle">{esc(val)}</text>')
        words, lines, cur = lab.split(), [], ""
        for wd in words:
            if len(cur + " " + wd) > wrap and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        assert len(lines) <= 5, lab
        for j, ln in enumerate(lines):
            o.append(f'<text x="{x + bw / 2:.1f}" y="{h - bottom + 14 + j * 11}" font-size="9.6" fill="{INK}" text-anchor="middle">{esc(ln)}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_cost_bridge():
    v1 = D_K
    v2 = v1 - D_PADS
    v3 = v2 - D_LOST
    v4 = v3 + D_EXTRA + D_OTHER
    cols = [("Full IML/IMIT increase on every part", 0, D_FULL, GREY, em(D_FULL)),
            ("Each part passes on 90.5% of its own increase", 0, v1, NAVY2, em(v1)),
            (f"{len(pads)} brake pad kits kept at today's price", v2, v1, RED, "-" + ek(D_PADS)),
            ("Categories the distributor already loses kept at today's price", v3, v2, RED, "-" + ek(D_LOST)),
            ("Small extra where UK web shops sell dearer than us", v3, v4, BLUE, "+" + ek(D_EXTRA + D_OTHER)),
            ("Result: +5.00% on parts billed", 0, INC, NAVY, em(INC))]
    assert abs(v4 - INC) < 2
    return svg_waterfall(cols, "From the IML/IMIT increase to the +5% on our price list", 2_100_000, 500_000,
                         lambda t: f"{t / 1e6:.1f}M", h=260, wrap=19)


def svg_recovery_bridge():
    cut = float(WB.cut_below_proposal_by_ceiling_eur)
    up = float(WB.uplift_above_proposal_eur)
    cols = [("+5% following IML/IMIT, all markets", 0, INC, NAVY, e0(INC)),
            ("Kept at today's price: eight markets and Israel body and lighting", INC - GIVEN, INC, RED, "-" + e0(GIVEN)),
            ("Capped: 5 parts rising more than 5 points above their own increase", INC - GIVEN - cut, INC - GIVEN, RED, "-" + e0(cut)),
            ("Recovered on repair and body parts with no aftermarket alternative", INC - GIVEN - cut, INC, BLUE, "+" + e0(up)),
            ("Result: +5.00% on parts billed", 0, INC, NAVY, e0(INC))]
    return svg_waterfall(cols, "From the +5% before market decisions to the decided recovery", 1_700_000, 400_000,
                         lambda t: f"{t / 1e6:.1f}M", h=250, wrap=21)


def svg_fm_bars():
    rows = [("All parts billed", FM_AVG, NAVY)]
    for s in ("service", "repair", "body"):
        rows.append((SEG_NAME[s], FM_SEG[s], BLUE))
    rows.append(("Parts supplied from Japan (IML)", FM_SRC["Japan (IML)"][0], GREY))
    rows.append(("Parts supplied from Thailand (IMIT)", FM_SRC["Thailand (IMIT)"][0], GREY))
    return svg_hbar(rows, lambda v, ax: (f"{v * 100:.0f}%" if ax else f"{v * 100:.1f}%"),
                    "Average IML/IMIT price increase to ISZE, weighted by parts billed", label_w=230, value_w=60, vmax=0.08, bar_h=18, gap=8)


def svg_segments():
    rows = []
    for seg in ("service", "repair", "body"):
        bb, p, billed = segavg("B", "segment", seg)
        rows.append((SEG_NAME[seg], p, bb, billed))
    w, label_w, value_w = 680, 170, 120
    bar_h, gap_in, gap_out = 14, 2, 12
    top, bottom = 4, 26
    h = top + len(rows) * (2 * bar_h + gap_in + gap_out) + bottom
    vmax = 0.10
    plot_w = w - label_w - value_w
    sx = lambda v: label_w + plot_w * v / vmax
    o = [svg_open(w, h, "Average increase by part group, before and after the recovery")]
    for t in (0, 0.02, 0.04, 0.06, 0.08, 0.10):
        x = sx(t)
        o.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{GRID}"/>')
        o.append(f'<text x="{x:.1f}" y="{h - 8}" font-size="10" fill="{MUTED}" text-anchor="middle">{t * 100:.0f}%</text>')
    for i, (lab, p, bb, billed) in enumerate(rows):
        y = top + i * (2 * bar_h + gap_in + gap_out)
        o.append(f'<text x="{label_w - 8}" y="{y + bar_h + 4}" font-size="11" fill="{INK}" text-anchor="end" font-weight="600">{esc(lab)}</text>')
        o.append(f'<text x="{label_w - 8}" y="{y + bar_h + 17}" font-size="9.5" fill="{MUTED}" text-anchor="end">{esc(em(billed, 1))} billed</text>')
        for j, (v, col, tag) in enumerate(((p, GREY, "before market decisions"), (bb, BLUE, "decided"))):
            yy = y + j * (bar_h + gap_in)
            o.append(f'<rect x="{label_w}" y="{yy}" width="{max(sx(v) - label_w, 1):.1f}" height="{bar_h}" fill="{col}" rx="2"/>')
            o.append(f'<text x="{sx(v) + 6:.1f}" y="{yy + bar_h - 4}" font-size="10.5" fill="{INK}">{v * 100:.1f}% {tag}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_markets(top_n=12):
    t = VMK.sort_values("billed_eur", ascending=False).head(top_n)
    w, label_w, tbl_w = 680, 170, 230
    row_h, top, bottom = 22, 34, 26
    h = top + len(t) * row_h + bottom
    plot_l, plot_r = label_w, w - tbl_w - 14
    vmax = 0.08
    sx = lambda v: plot_l + (plot_r - plot_l) * v / vmax
    o = [svg_open(w, h, "Average increase by market: before market decisions, decided, and with Isuzu UK (D-Max) exempted")]
    for v in (0, 0.02, 0.04, 0.06, 0.08):
        x = sx(v)
        o.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{GRID}"/>')
        o.append(f'<text x="{x:.1f}" y="{h - 8}" font-size="10" fill="{MUTED}" text-anchor="middle">{v * 100:.0f}%</text>')
    cx = [w - tbl_w + 34, w - tbl_w + 112, w - tbl_w + 190]
    heads = (("Before market", "decisions"), ("Decided", ""), ("UK D-Max", "exempted"))
    for x, (l1, l2) in zip(cx, heads):
        o.append(f'<text x="{x}" y="{top - 20}" font-size="9.5" fill="{MUTED}" text-anchor="middle" font-weight="600">{l1}</text>')
        if l2:
            o.append(f'<text x="{x}" y="{top - 9}" font-size="9.5" fill="{MUTED}" text-anchor="middle" font-weight="600">{l2}</text>')
    for i, (mk, r) in enumerate(t.iterrows()):
        y = top + i * row_h + row_h / 2
        if i % 2 == 0:
            o.append(f'<rect x="0" y="{y - row_h / 2:.1f}" width="{w}" height="{row_h}" fill="#f7f4ee"/>')
        o.append(f'<text x="{label_w - 8}" y="{y + 4:.1f}" font-size="11" fill="{INK}" text-anchor="end">{esc(NAME.get(mk, mk.title()))}</text>')
        vals = [(r.proposal_avg_move, GREY, 6), (r.B_avg_move, BLUE, 6), (r.B_iuk_exempt_avg_move, AMBER, 5)]
        xs = [sx(v) for v, _, _ in vals]
        o.append(f'<line x1="{min(xs):.1f}" y1="{y:.1f}" x2="{max(xs):.1f}" y2="{y:.1f}" stroke="#c8c6bd" stroke-width="2"/>')
        for (v, col, rad), x in zip(vals, xs):
            shape = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{col}" stroke="#fff" stroke-width="1.2"/>' if col != AMBER else
                     f'<rect x="{x - rad:.1f}" y="{y - rad:.1f}" width="{2 * rad}" height="{2 * rad}" fill="{col}" stroke="#fff" stroke-width="1.2" transform="rotate(45 {x:.1f} {y:.1f})"/>')
            o.append(shape)
        for x, v in zip(cx, (r.proposal_avg_move, r.B_avg_move, r.B_iuk_exempt_avg_move)):
            o.append(f'<text x="{x}" y="{y + 4:.1f}" font-size="10.5" fill="{INK}" text-anchor="middle">{v * 100:.1f}%</text>')
    o.append("</svg>")
    return "".join(o)


def svg_coverage():
    s = SUF
    rows = [("Order lines and order type", s["4_order_type_found"]["billed_pct"], GREEN, "sufficient"),
            ("Vehicle line (D-Max or truck)", s["6_vehicle_line_any"]["billed_pct"], GREEN, "sufficient"),
            ("Dealer response to the April 2026 rise", s["5_dealer_response_measured"]["billed_pct"], AMBER, "partial: a flag only"),
            ("Genuine Isuzu sold outside our network", s["1_outside_prices_genuine_grey"]["billed_pct"], AMBER, "partial: one main source"),
            ("Any competitor evidence (number or price)", s["2_competitive_evidence_brief_definition"]["billed_pct"], RED, "too thin to prove no alternative"),
            ("Aftermarket shop price", s["1_outside_prices_aftermarket_street_any_date"]["billed_pct"], AMBER, "partial: top sellers only"),
            ("Competitor part number, confirmed or likely", s["2_competitor_number_confirmed_likely"]["billed_pct"], RED, "thin")]
    w, label_w, value_w = 680, 250, 200
    bar_h, gap, top, bottom = 18, 8, 4, 26
    h = top + len(rows) * (bar_h + gap) + bottom
    plot_w = w - label_w - value_w
    sx = lambda v: label_w + plot_w * v
    o = [svg_open(w, h, "Coverage of parts billed by each kind of evidence")]
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        x = sx(t)
        o.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{GRID}"/>')
        o.append(f'<text x="{x:.1f}" y="{h - 8}" font-size="10" fill="{MUTED}" text-anchor="middle">{t * 100:.0f}%</text>')
    for i, (lab, v, col, verdict) in enumerate(rows):
        y = top + i * (bar_h + gap)
        o.append(f'<text x="{label_w - 8}" y="{y + bar_h - 5}" font-size="10.5" fill="{INK}" text-anchor="end">{esc(lab)}</text>')
        o.append(f'<rect x="{label_w}" y="{y}" width="{max(sx(v) - label_w, 1.5):.1f}" height="{bar_h}" fill="{col}" rx="2"/>')
        o.append(f'<text x="{sx(1.0) + 8:.1f}" y="{y + bar_h - 5}" font-size="10.5" fill="{INK}"><tspan font-weight="600">{v * 100:.1f}%</tspan>'
                 f'<tspan fill="{MUTED}"> · {esc(verdict)}</tspan></text>')
    o.append("</svg>")
    return "".join(o)


def svg_index_line():
    am, gg = IDX["aftermarket_street"], IDX["genuine_grey"]
    w, h, l, r = 680, 150, 40, 40
    vmin, vmax = 0.0, 1.5
    sx = lambda v: l + (w - l - r) * (v - vmin) / (vmax - vmin)
    y0 = 78
    o = [svg_open(w, h, "Outside prices against our reference dealer price")]
    o.append(f'<rect x="{sx(0):.1f}" y="{y0 - 10}" width="{sx(1.0) - sx(0):.1f}" height="20" fill="#fbe9e3"/>')
    o.append(f'<rect x="{sx(1.0):.1f}" y="{y0 - 10}" width="{sx(1.5) - sx(1.0):.1f}" height="20" fill="#e3f2ec"/>')
    o.append(f'<line x1="{sx(0):.1f}" y1="{y0}" x2="{sx(1.5):.1f}" y2="{y0}" stroke="{MUTED}"/>')
    for t in (0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        o.append(f'<line x1="{sx(t):.1f}" y1="{y0 + 10}" x2="{sx(t):.1f}" y2="{y0 + 15}" stroke="{MUTED}"/>')
        o.append(f'<text x="{sx(t):.1f}" y="{y0 + 27}" font-size="10" fill="{MUTED}" text-anchor="middle">{t:.2f}x</text>')
    o.append(f'<line x1="{sx(1.0):.1f}" y1="{y0 - 40}" x2="{sx(1.0):.1f}" y2="{y0 + 15}" stroke="{TERRA}" stroke-width="2"/>')
    o.append(f'<text x="{sx(1.0):.1f}" y="{y0 + 44}" font-size="10.5" fill="{TERRA}" text-anchor="middle" font-weight="600">1.00x = our reference dealer price</text>')
    o.append(f'<text x="{sx(0.5):.1f}" y="{y0 - 22}" font-size="9.5" fill="{MUTED}" text-anchor="middle">outside seller cheaper than us</text>')
    o.append(f'<text x="{sx(1.25):.1f}" y="{y0 - 22}" font-size="9.5" fill="{MUTED}" text-anchor="middle">outside seller dearer than us</text>')
    x = sx(am["median"])
    o.append(f'<circle cx="{x:.1f}" cy="{y0}" r="7" fill="{RED}" stroke="#fff" stroke-width="1.5"/>')
    o.append(f'<text x="{x:.1f}" y="{y0 + 44}" font-size="10.5" fill="{INK}" text-anchor="middle"><tspan font-weight="600">Aftermarket shop price {am["median"]:.2f}x</tspan></text>')
    o.append(f'<text x="{x:.1f}" y="{y0 + 57}" font-size="9.5" fill="{MUTED}" text-anchor="middle">median of {am["parts"]} parts</text>')
    x = sx(gg["median"])
    o.append(f'<circle cx="{x:.1f}" cy="{y0}" r="7" fill="{GREEN}" stroke="#fff" stroke-width="1.5"/>')
    o.append(f'<text x="{x:.1f}" y="{y0 - 46}" font-size="10.5" fill="{INK}" text-anchor="middle"><tspan font-weight="600">Genuine sold outside our network {gg["median"]:.2f}x</tspan></text>')
    o.append(f'<text x="{x:.1f}" y="{y0 - 34}" font-size="9.5" fill="{MUTED}" text-anchor="middle">median of {gg["parts"]:,} parts</text>')
    o.append("</svg>")
    return "".join(o)


# ======================================================================= market grid (21 markets)
NET = MF["network_service_share_2025"]
ORDER = sorted(MF["markets"], key=lambda k: -(MF["markets"][k]["billed"].get("2025") or 0))
DEC_TXT_SVC = {"hold at today's price": "today's price", "factory move": "follows IML/IMIT", "not touched": "left out"}
DEC_TXT_BODY = {"hold body, collision and lighting": "today's price: body, collision, lighting",
                "hold lighting": "today's price: lighting", "factory move": "follows IML/IMIT", "not touched": "left out"}
KEEP_BODY = {"UMI": HR["UMI body/collision hold"]["step"] + HR["UMI lighting hold"]["step"], "UTI": HR["UTI lighting hold"]["step"]}


def grid_rows():
    out = []
    for k in ORDER:
        m, d = MF["markets"][k], DEC["decisions"][k]
        f = m.get("fleet", {})
        f23, f25, f26 = f.get("2023"), f.get("2025"), m.get("fleet_2026_corrected")
        fc = (f25 / f23 - 1) if f23 and f25 else None
        fw = (f26 / f25 - 1) if f25 and f26 else None
        sh = m.get("service_share", {}) or {}
        s23 = (sh.get("2023") or {}).get("total")
        s25 = (sh.get("2025") or {}).get("total")
        ch = (s25 - s23) if s23 is not None and s25 is not None else None
        sor = (m.get("pays_pct_list") or {}).get("SOR")
        given = 0.0
        pr = m.get("proposal", {})
        if d["service"].startswith("hold"):
            given += pr["service"]["step"]
        out.append(dict(k=k, billed=m["billed"].get("2025") or 0, fc=fc, fw=fw, s25=s25, ch=ch, sor=sor,
                        service=d["service"], body=d["body"], given=given))
    return out


def cls_fleet(v):
    return "na" if v is None else ("bad" if v <= 0 else "mid" if v < 0.1 else "good")


def grid_html():
    rows = grid_rows()
    o = ["<table class='grid'><colgroup>" + "".join(f"<col style='width:{w}%'>" for w in (16, 8, 7, 8, 7, 8, 8, 11, 18, 9)) + "</colgroup>"
         "<thead><tr><th>Market</th><th class='r'>Parts billed 2025</th><th class='r'>Fleet 2023→25</th>"
         "<th class='r'>Fleet 2026 forecast</th><th class='r'>Service share 2025</th><th class='r'>Change since 2023</th>"
         "<th class='r'>Pays vs list, stock orders</th><th>Service parts</th><th>Body and lighting</th><th class='r'>Increase given up</th></tr></thead><tbody>"]
    for r in rows:
        s25, ch = r["s25"], r["ch"]
        sk = "na" if s25 is None else ("bad" if s25 < NET * 0.8 else "mid" if s25 < NET * 1.2 else "good")
        stxt = "n/a" if s25 is None else ("over 100%*" if s25 > 1.0 else ("100%*" if s25 >= 0.995 else f"{s25 * 100:.0f}%"))
        ck = "na" if ch is None else ("bad" if ch < 0 else "mid" if ch < 0.05 else "good")
        fwk = "na" if r["fw"] is None else ("bad" if r["fw"] <= -0.03 else "mid" if r["fw"] < 0.03 else "good")
        given = r["given"] + KEEP_BODY.get(r["k"], 0.0)
        sor_txt = "n/a" if r["sor"] is None else f"{r['sor']:.1f}%"
        svc_cls = "keep" if r["service"].startswith("hold") else ("move" if r["service"] == "factory move" else "na")
        body_cls = "keep" if r["body"].startswith("hold") else ("move" if r["body"] == "factory move" else "na")
        o.append("<tr>"
                 f"<td><b>{esc(NAME[r['k']])}</b></td><td class='r'>{em(r['billed'])}</td>"
                 f"<td class='r {cls_fleet(r['fc'])}'>{'n/a' if r['fc'] is None else p0(r['fc'], True)}</td>"
                 f"<td class='r {fwk}'>{'n/a' if r['fw'] is None else p0(r['fw'], True)}</td>"
                 f"<td class='r {sk}'>{stxt}</td>"
                 f"<td class='r {ck}'>{'n/a' if ch is None else f'{ch * 100:+.1f} pts'}</td>"
                 f"<td class='r'>{sor_txt}</td>"
                 f"<td class='{svc_cls}'>{esc(DEC_TXT_SVC[r['service']])}</td><td class='{body_cls}'>{esc(DEC_TXT_BODY[r['body']])}</td>"
                 f"<td class='r'>{'' if given == 0 else ek(given)}</td></tr>")
    o.append("</tbody></table>")
    return "".join(o)


def given_rows():
    rows = []
    for r in grid_rows():
        if r["given"] > 0:
            rows.append((f"{NAME[r['k']]}: service parts", r["given"], RED))
    rows += [("Israel D-Max distributor: body and collision", HR["UMI body/collision hold"]["step"], AMBER),
             ("Israel trucks distributor: lighting", HR["UTI lighting hold"]["step"], AMBER),
             ("Israel D-Max distributor: lighting", HR["UMI lighting hold"]["step"], AMBER)]
    return sorted(rows, key=lambda x: -x[1])


SVC_MARKETS = [NAME[r["k"]] for r in grid_rows() if r["given"] > 0]
assert len(SVC_MARKETS) == 8, SVC_MARKETS

# ======================================================================= discounts and surcharges outside the list
LV = LEV[~LEV.cis_untouched].copy()
gap_rows = LV.sort_values("a_stock_halve_gap_to_list_eur", ascending=False)
gap_rows = gap_rows[gap_rows.a_stock_halve_gap_to_list_eur >= 5000]

# ======================================================================= carried-over constants
# Origin: management deck v1.4 (20 Sep 2026), slides 4, 5, 6, 19, 22; pricing policy paper revision 3 (19 Sep),
# sections 2, 9-14; revision 1 (17 Sep) sections 4.4 and 4.7. All archived with this paper's predecessors.
MARGIN_LEVELS = ["56%", "53%", "52%", "50%", "47.5%", "45%", "44.5%", "20%"]

# ======================================================================= page
CSS = """
*{box-sizing:border-box}
:root{--ink:#222;--navy:#1a2b4a;--terra:#c0552d;--paper:#f7f4ee;--line:#d9d3c8;--muted:#6b6256}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;background:#fff}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:var(--ink);font-size:10.4px;line-height:1.5}
h1,h2,h3,h4{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
@page{size:A4;margin:15mm 15mm 20mm 15mm;@bottom-left{content:'ISZE · Parts pricing policy · 2 October 2026';font-family:'Segoe UI',Arial,sans-serif;font-size:7.6px;color:#6b6256;vertical-align:middle}@bottom-right{content:'Proposal on paper — no price, list or condition changed · page ' counter(page);font-family:'Segoe UI',Arial,sans-serif;font-size:7.6px;color:#6b6256;vertical-align:middle}}@page:first{@bottom-left{content:none}@bottom-right{content:none}}
.wrap{max-width:180mm;margin:0 auto}
.cover{position:relative;height:262mm;margin:-15mm -15mm 0;padding:28mm 22mm 20mm;
  background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%);color:#eef1f6;break-after:page}
.cover .kicker{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#c9d3e6}
.cover h1{color:#fff;font-size:40px;line-height:1.1;margin-top:10mm}
.cover .sub{font-family:Georgia,serif;font-size:17px;color:#dfe6f2;margin-top:6mm;max-width:150mm}
.cover .rule{width:54mm;height:3px;background:var(--terra);margin:10mm 0 8mm}
.cover .meta{font-size:11px;color:#c9d3e6;line-height:1.7}
.cover .status{position:absolute;left:22mm;right:22mm;bottom:22mm;border-top:1px solid rgba(255,255,255,.25);padding-top:5mm;font-size:10px;color:#c9d3e6}
.cover .toc{margin-top:12mm;font-size:10.5px;color:#dfe6f2;columns:2;column-gap:10mm}
.cover .toc div{break-inside:avoid;margin-bottom:1.6mm}
.cover .toc b{color:#f0b49d;font-family:Georgia,serif;margin-right:2mm}
h2.sec{font-size:18px;margin:8mm 0 1mm;padding-bottom:2.2mm;border-bottom:2px solid var(--navy);break-after:avoid}
h2.sec .no{color:var(--terra);margin-right:2.5mm}
h3{font-size:12.5px;margin:5mm 0 1.5mm;break-after:avoid}
p{margin:1.6mm 0 2.2mm}
.lead{font-size:11.6px;line-height:1.5;color:#1d2433}
.intro{background:#eef2f8;border-left:3px solid var(--navy);padding:2.6mm 4mm;margin:3mm 0 3.5mm;font-size:11px;line-height:1.5;color:#1d2433;break-inside:avoid}
.intro b.k{color:var(--navy);font-family:Georgia,serif;margin-right:1.5mm}
.howto{border:1.5px solid var(--navy);padding:3.5mm 5mm;margin:0 0 4mm;break-inside:avoid}
.howto h3{margin-top:0}
.howto dl{margin:1mm 0 0;display:grid;grid-template-columns:34mm 1fr;gap:1.2mm 3mm}
.howto dt{font-weight:700;color:var(--navy)}.howto dd{margin:0}
.callout{border-left:3px solid var(--terra);background:var(--paper);padding:3mm 4mm;margin:3mm 0;break-inside:avoid}
.callout.navy{border-left-color:var(--navy)}
.tag{display:inline-block;font-size:8.6px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:.6mm 2mm;border-radius:2px;margin-right:2mm;vertical-align:1px;white-space:nowrap}
.tag.dec{background:#1a2b4a;color:#fff}.tag.sug{background:#eda100;color:#2a1d00}.tag.open{background:#e24b4a;color:#fff}
.tag.neg{background:#5b4a8a;color:#fff}.tag.next{background:#888780;color:#fff}.tag.new{background:#1d9e75;color:#fff}
table{width:100%;border-collapse:collapse;margin:2mm 0 3mm;font-size:9.4px;break-inside:avoid}
th{background:var(--navy);color:#fff;text-align:left;padding:1.6mm 2mm;font-size:8.6px;font-weight:600;vertical-align:bottom}
td{padding:1.4mm 2mm;border-bottom:.5px solid var(--line);vertical-align:top}
tbody tr:nth-child(even){background:var(--paper)}
tr{break-inside:avoid}
table.dec{font-size:9.1px;break-inside:auto}table.dec td{padding:1.5mm 1.8mm}table.dec td.eur{white-space:normal;font-weight:600;color:var(--navy)}
.r{text-align:right;white-space:nowrap}
table.grid{font-size:8.5px;table-layout:fixed}table.grid th{white-space:normal}table.grid td{padding:1.1mm 1.5mm}table.grid th{padding:1.3mm 1.5mm;font-size:8px}
td.good{background:#e3f2ec!important;color:#1f6b4c}td.mid{background:#fdf3dc!important;color:#7a5a00}td.bad{background:#fbe3e1!important;color:#9b2c2b}
td.keep{color:#9b2c2b;font-weight:600}td.move{color:#2b4a78}td.na{color:#888}
.fig{margin:2.5mm 0 1mm;break-inside:avoid}
.fig .ttl{font-weight:600;font-size:10.6px;color:var(--navy);margin-bottom:1.2mm}
.legend{font-size:9px;color:var(--muted);margin:1mm 0 2mm}
.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 1.2mm 0 3mm;vertical-align:-1px}
.legend i.sq{border-radius:1px;transform:rotate(45deg)}
.src{font-size:7.9px;color:var(--muted);border-top:.5px solid var(--line);margin-top:3mm;padding-top:1.2mm;line-height:1.45}
.cards{display:flex;gap:3mm;margin:3mm 0;break-inside:avoid}
.card{flex:1;background:var(--paper);border-radius:2px;padding:2.6mm 3mm;border-top:2px solid var(--navy)}
.card .l{font-size:8.6px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.card .v{font-family:Georgia,serif;font-size:17px;color:var(--navy);margin-top:.8mm}
.card .n{font-size:8.6px;color:var(--muted);margin-top:.6mm}
.card.terra{border-top-color:var(--terra)}.card.blue{border-top-color:#2a78d6}.card.amber{border-top-color:#eda100}
ul.tight{margin:1mm 0 2mm 4.5mm;padding:0}ul.tight li{margin:.8mm 0}
ol.tight{margin:1mm 0 2mm 5mm;padding:0}ol.tight li{margin:1mm 0}
.pb{break-before:page}
.avoid{break-inside:avoid}
.negbox{border:2px solid #5b4a8a;background:#f5f3fa;padding:3mm 4mm;margin:3mm 0;break-inside:avoid}
.negbox b.h{color:#5b4a8a}
.two{display:flex;gap:5mm}.two>div{flex:1}
.small{font-size:9.2px}
.muted{color:var(--muted)}
sup.fn{font-size:7px;color:var(--terra);font-weight:700}
@media screen{body{background:#e9e6df}.wrap{background:#fff;padding:12mm 15mm 20mm;margin:0 auto;max-width:210mm}
  .cover{margin:-12mm -15mm 0;height:auto;min-height:262mm}}
@media screen and (max-width:700px){.wrap{padding:6mm 4mm}.cover{margin:-6mm -4mm 0;padding:14mm 8mm}.cards,.two{flex-direction:column}
  table{display:block;overflow-x:auto}.howto dl{grid-template-columns:1fr}}
"""


def section(no, title, intro, body, src, pb=True):
    cls = " class='pb'" if pb else ""
    return (f"<section{cls}><h2 class='sec'><span class='no'>{no}</span>{esc(title)}</h2>"
            f"<div class='intro'><b class='k'>In short.</b>{intro}</div>{body}"
            f"<div class='src'><b>Sources.</b> {src}</div></section>")


def card(label, value, note, cls=""):
    return f"<div class='card {cls}'><div class='l'>{esc(label)}</div><div class='v'>{esc(value)}</div><div class='n'>{esc(note)}</div></div>"


seg_b = {s: segavg("B", "segment", s) for s in ("service", "repair", "body")}
vl_b = {s: segavg("B", "vehicle_line", s) for s in ("LCV (D-Max)", "Truck")}
uk = VMK.loc["UKRAINE"]
iuk = VMK.loc["IUK"]
given_share = GIVEN / INC
umi_service_step = MF["markets"]["UMI"]["proposal"]["service"]["step"]
umi_service_billed = MF["markets"]["UMI"]["proposal"]["service"]["billed"]
iuk_rb_uplift = VB["uplift_on_iuk_repair_body_eur"]
iuk_svc_given = MF["markets"]["IUK"]["proposal"]["service"]["step"]
pb_ = UN["panels_eur_bridge_janaug"]
pp_ = UN["panels_same_part_price_change_janaug_25_26"]
bo_ = UBO.loc["Panels"]
panel_inc = float(UST[(UST.master_body) & (UST.grp == "Panels")].step.sum())
body_inc = float(UST[(UST.master_body) & (UST.grp != "Lighting")].step.sum())
assert abs(panel_inc - RS["holds"]["uti_panels_optional"]["step"]) < 1
eur_chg = pb_["eur_2026"] / pb_["eur_2025"] - 1
unit_chg = (pb_["units_both_2026"] / pb_["units_both_2025"] - 1)
eur_chg_same = pb_["eur_both_2026"] / pb_["eur_both_2025"] - 1
bw = UBW[UBW.scope.str.startswith("Panels")].copy()
assert len(bw) == 39
bw["per"] = pd.cut(bw.week, [0, 13, 26, 40], labels=["WK2-13", "WK14-26", "WK27-40"])
bwp = bw.groupby("per", observed=True)[["lines", "units"]].mean()
bw_peak = bw.loc[bw.lines.idxmax()]
bw_last = bw.loc[bw.week.idxmax()]
waits = UNB["eran_9jun"]["total_weeks_values"]
assert int(waits["min"]) == 4 and int(waits["max"]) == 16

STATUS_TAGS = ("<span class='tag dec'>Decided</span> <span class='tag sug'>Suggested, not decided</span> <span class='tag open'>Open</span> "
               "<span class='tag neg'>Negotiation topic</span> <span class='tag next'>Next price list</span>")

S = []

# ---------------------------------------------------------------- cover
S.append(f"""
<div class='cover'>
 <div class='kicker'>Isuzu Motors Europe · Parts pricing · Management</div>
 <h1>Parts pricing policy</h1>
 <div class='sub'>The +5% price revision: what IML and IMIT change, what we decide, why, and what each decision is worth</div>
 <div class='rule'></div>
 <div class='meta'>2 October 2026<br>Consolidated paper: replaces the pricing policy papers of 17 and 19 September 2026 and the earlier management decks<br>
 Decisions recorded up to 2 October 2026</div>
 <div class='toc'>
  <div><b>1</b>Summary and decisions</div><div><b>2</b>How prices are set, and what IML and IMIT changed</div>
  <div><b>3</b>Prices per parts category</div><div><b>4</b>How the +5% is spread over the parts</div>
  <div><b>5</b>Market by market: where service parts stay at today's price</div><div><b>6</b>How the {ek(GIVEN)} is recovered: three ways considered</div>
  <div><b>7</b>Isuzu UK (D-Max): the risk, and a suggested exemption</div><div><b>8</b>Outside price evidence: what it can carry</div>
  <div><b>9</b>Collision, insurance and lighting in Israel</div><div><b>10</b>Israel truck body panels: delivery times, not price</div>
  <div><b>11</b>Discounts and surcharges outside the price list</div><div><b>12</b>New N-Series (P700) parts and the next price list</div>
  <div><b>13</b>Background that still stands</div><div><b>14</b>Open points and next actions</div>
  <div><b>A</b>Terms and sources</div>
 </div>
 <div class='status'>Status: a proposal on paper. Nothing in this document changes a price, the price list or a distributor condition.</div>
</div>""")

# ---------------------------------------------------------------- how to read
S.append(f"""
<div class='howto pb'>
<h3>How to read this paper</h3>
<dl>
<dt>"+5%"</dt><dd>The average rise of our price list &mdash; the price at which we bill our distributors &mdash; weighted by parts billed from July 2025 to June 2026.
The same parts at the same volumes would bill 5% more: {em(INC)} on {em(BASE, 1)}. Individual parts move more or less than 5%. Whether distributors pass it on in their sales to dealer is their decision; we do not see their resale prices.</dd>
<dt>Parts billed</dt><dd>Our net sales of parts to distributors, in euro. It is the weight behind every average in this paper.</dd>
<dt>Sales to dealer</dt><dd>What our distributors sell on to their dealers, from the distributors' own monthly files. Used to see whether dealers bought less after a price rise.</dd>
<dt>Genuine</dt><dd>Isuzu-branded parts, supplied through IML (Japan) or IMIT (Thailand) and sold by us.</dd>
<dt>Aftermarket</dt><dd>Parts made by other brands to fit Isuzu vehicles, sold by independent shops and garages, usually cheaper than genuine.</dd>
<dt>Reference dealer price</dt><dd>What a customer pays at a dealer counter for a genuine part: our list price times 2.19, covering distributor and dealer margins. A construction used to compare outside prices with ours; provisional.</dd>
<dt>Euro effects</dt><dd>Every euro figure is the effect of a price change on the volume billed in the last twelve months, before any change in what dealers buy.</dd>
<dt>Status labels</dt><dd>{STATUS_TAGS}<br><span class='small muted'>Decided = management decision taken. Suggested, not decided = recommended, awaiting a decision. Open = cannot be decided yet; what is missing is named.
Negotiation topic = a commercial term per distributor, not a price list change. Next price list = for the following revision, not this one.</span></dd>
</dl>
</div>""")

# ---------------------------------------------------------------- 1 summary
pad_eur = pads.billed_eur_l12m.sum()
umi_given_body = HR["UMI body/collision hold"]["step"] + HR["UMI lighting hold"]["step"]
S.append(section("1", "Summary and decisions",
    f"IML and IMIT raise their prices to us; this paper sets how our price list follows. The list rises by 5% on average, worth {em(INC)} a year, "
    f"with exceptions where a price rise would cost us business; every exception is paid for elsewhere on the list, so the total stays at +5%.",
f"""
<p class='lead'><b>IML and IMIT raise their prices to us by {p1(FM_AVG)} on average</b> in their September 2026 price revision, weighted by parts billed
(service parts {p1(FM_SEG['service'])}, repair parts {p1(FM_SEG['repair'])}, body and collision parts {p1(FM_SEG['body'])}).<sup class='fn'>1</sup>
Our price list rises by <b>+5.0% on average</b>: {e0(INC)} on {e0(BASE)} of parts billed. Each part follows its own IML/IMIT increase, so parts IML and IMIT raised more go up more.
Where a rise would cost us business &mdash; brake pads, service parts in eight markets under pressure, body and lighting parts in Israel &mdash; prices stay where they are today;
the {e0(GIVEN)} this gives up is recovered on repair and body parts for which we found no aftermarket alternative.</p>
<div class='callout navy'><span class='tag new'>New</span><b>Prices can now be set per parts category.</b> Every part number sits in a parts category (filters, brake pads, body panels, lighting and so on),
so a decision can apply to a whole category in one market instead of part number by part number or to the whole list. Every decision below was made this way. Section 3.</div>
<div class='cards'>
 {card("IML/IMIT increase to us", p1(FM_AVG), "average, weighted by parts billed")}
 {card("Our price list", "+5.0%", em(INC) + " on " + em(BASE, 1) + " parts billed")}
 {card("Kept at today's price", ek(GIVEN), "service parts in 8 markets; Israel body and lighting", "terra")}
 {card("Recovered on repair and body", f"+{WB.solver_t * 100:.1f} pts", f"on {int(WB.weighted_parts):,} parts with no aftermarket alternative found", "blue")}
</div>
<p class='small muted'><sup class='fn'>1</sup> Each part's IML or IMIT base price in September 2026 against September 2025, in yen, weighted by what we billed of that part from July 2025 to June 2026
({len(PART):,} part numbers). Parts supplied from Japan (IML) {p1(FM_SRC['Japan (IML)'][0])}, from Thailand (IMIT) {p1(FM_SRC['Thailand (IMIT)'][0])}.
The purchase discount and the exchange rate are not included; they are covered in section 2.</p>
""", "IML and IMIT base prices of September 2025 and September 2026 per part; SAP parts billing July 2025&ndash;June 2026; the +5% calculation by part number of 29&ndash;30 September 2026; "
     "the market-by-market review of 30 September 2026 and its decision record; the recovery analysis of 2 October 2026. Decisions as recorded on 29 September, 30 September and 2 October 2026.", pb=False))

# decision table on its own page
rows_dec = [
    ("dec", "Decided",
     f"<b>Prices rise 5% on average.</b> Each part follows its own IML/IMIT cost increase, scaled evenly so that every part passes on 90.5% of its own increase and the total is exactly +5%. "
     f"Parts IML and IMIT raised more go up more; parts with no increase stay flat ({NO_RISE_PARTS} part numbers, {p1(NO_RISE_SHARE)} of parts billed).",
     f"IML and IMIT raise their prices to us by {p1(FM_AVG)} on average. Following each part's own increase keeps every price tied to its cost; +5% is the target for this revision.",
     f"+{em(INC)} a year on {em(BASE, 1)} parts billed (passing on the full {p1(FM_AVG)} would be {em(FM_EUR)})"),
    ("dec", "Decided",
     f"<b>The {len(pads)} brake pad kits stay at today's price</b> ({em(pad_eur)} billed).",
     "Brake pads compete directly with aftermarket brands. Front pad kit 8982447940 would otherwise have risen 17%; it is the main pad kit bought in the Isuzu Truck UK and Israel trucks networks.",
     f"{ek(D_PADS)} of increase not taken; absorbed within the +5%"),
    ("dec", "Decided",
     f"<b>No increase on service parts in eight markets under pressure</b>: {', '.join(SVC_MARKETS[:-1])} and {SVC_MARKETS[-1]}. "
     "The Israel D-Max distributor also keeps body, collision and lighting parts at today's price; the Israel trucks distributor keeps lighting only.",
     "Ageing fleets, a weak service-parts position (we supply a small share of what the fleet needs) and documented price complaints. "
     "Isuzu UK (D-Max): dealers measurably bought less after the April 2026 rise. Cyprus and Malta: vehicles outside our fleet count also buy there. Israel body and lighting: the insurance total-loss rule.",
     f"Gives up {e0(GIVEN)} ({p0(given_share)} of the +5%)"),
    ("dec", "Decided",
     f"<b>The {ek(GIVEN)} is recovered on repair and body parts where we found no aftermarket alternative</b>: about +{WB.solver_t * 100:.1f} points on top of their own increase, on {int(WB.weighted_parts):,} parts. "
     "Service parts get nothing extra. Two alternatives were considered: spreading it over all remaining parts, and weighting each part by outside prices (section 6).",
     "Service parts are where the alternatives, the complaints and the market decisions are. Outside price data is too thin to weight part by part.",
     f"+{e0(WB.uplift_above_proposal_eur)} (repair {ek(WB.uplift_repair_eur)}, body {ek(WB.uplift_body_eur)}, service 0); total stays +5.00%"),
    ("sug", "Suggested, not decided",
     f"<b>Exempt Isuzu UK (D-Max) from that extra.</b> Its repair and body parts keep their own IML/IMIT-based increase.",
     "The only market with measured lower buying after the April 2026 change. The other markets then carry "
     f"+{VI['solver_t_pts'] * 100:.1f} points instead of +{WB.solver_t * 100:.1f}.",
     f"{ek(iuk_rb_uplift)} moves from Isuzu UK (D-Max) to the other markets; total unchanged"),
    ("dec", "Decided",
     "<b>Ukraine takes the normal increase.</b> Ukraine buys on the standard price list. Armenia and Kazakhstan are the only markets left out of the market decisions; their price basis is a separate, open decision.",
     "Ukraine has no fleet or service-share measure that would justify an exception.",
     f"Ukraine: {em(uk.billed_eur)} billed, average {p1(uk.B_avg_move, True)}"),
    ("open", "Open",
     "<b>Israel D-Max distributor: share of leasing fleets.</b> Service parts there stay at today's price until it is known.",
     "Leasing fleets must use genuine parts in the vehicle's first two years and run the highest mileage of the pickup markets; if they are most of the volume, the service parts could take the normal increase.",
     f"{ek(umi_service_step)} of increase at stake on {em(umi_service_billed)} of service parts billed"),
    ("dec", "Decided",
     "<b>Israel truck body panels are not kept at today's price.</b> They take the normal increase.",
     "Sales are lost mainly to delivery times (back orders of 4 to 16 weeks), not to price. "
     "The answer is to stock new N-Series (P700) panels against the distributor's forecast (section 10).",
     f"Keeps {e0(panel_inc)} of increase"),
    ("neg", "Negotiation topic",
     "<b>Discounts and surcharges outside the price list</b>: the stock-order discount, distributors paying well below list, and the surcharge on urgent orders.",
     "About as large as the price list measures above, but they are commercial terms agreed per distributor, not part of the price list.",
     f"Halving each market's gap to list on stock orders {ek(L4['stock_halve_gap_eur'])}; 1 point less stock-order discount {ek(L4['stock_narrow_1pt_eur'])}; urgent surcharge +1 point {ek(L4['urgent_plus1pt_eur'])}"),
    ("next", "Next price list",
     "<b>New N-Series (P700) parts</b> need a well-set first price on the next price list.",
     "They are hardly billed yet, so this year's increase does not reach them; their first price matters more than any increase.",
     f"None this year ({P7['in_proposal_base']} parts, {e0(P7['proposal_base_billed'])} in the base)"),
]
dec_html = "".join(f"<tr><td><span class='tag {c}'>{t}</span></td><td>{what}</td><td>{why}</td><td class='eur'>{eur}</td></tr>"
                   for c, t, what, why, eur in rows_dec)
S.append(f"""<section class='pb'><h3 style='margin-top:0'>The decisions: what each does, why, and what it is worth</h3>
<table class='dec'><thead><tr><th style='width:14%'>Status</th><th style='width:34%'>What it does</th><th style='width:32%'>Why</th><th style='width:20%'>Effect in euro a year</th></tr></thead>
<tbody>{dec_html}</tbody></table>
<div class='callout'><b>What the evidence can and cannot carry.</b> Order lines, order types and the D-Max/truck split cover 98&ndash;100% of parts billed and are sound.
Outside prices are thinner: an aftermarket shop price exists for {SUF['1_outside_prices_aftermarket_street_any_date']['parts']} parts ({p1(SUF['1_outside_prices_aftermarket_street_any_date']['billed_pct'])} of parts billed),
and a competitor part number for {SUF['2_competitor_number_confirmed_likely']['parts']} parts. "No aftermarket alternative found" therefore mostly means that none was found, not that none exists.
Where we do have aftermarket prices, they sit at a median {IDX['aftermarket_street']['median']:.2f} times our reference dealer price (section 8).</div>
<div class='src'><b>Sources.</b> as for section 1; euro effects on parts billed July 2025&ndash;June 2026, except the discounts and surcharges (calendar year 2025 order lines at the 2025 list).</div></section>""")

# ---------------------------------------------------------------- 2 how prices are set
S.append(section("2", "How prices are set, and what IML and IMIT changed",
    f"Our list price follows what IML and IMIT charge us, through a fixed formula. In their September 2026 revision IML and IMIT raise their prices to us by "
    f"{p1(FM_AVG)} on average; each part passes on 90.5% of its own increase, which lands our list at +5.0% overall ({em(INC)}) after a few exceptions.",
f"""
<div class='fig'><div class='ttl'>Average IML/IMIT price increase to ISZE, September 2026 against September 2025, weighted by parts billed</div>{svg_fm_bars()}</div>
<p class='small'>Parts billed: service {em(SEG_BILLED['service'], 1)}, repair {em(SEG_BILLED['repair'], 1)}, body and collision {em(SEG_BILLED['body'], 1)};
from Japan {em(FM_SRC['Japan (IML)'][1], 1)}, from Thailand {em(FM_SRC['Thailand (IMIT)'][1], 1)}. {FM_SRC['No source label'][2]} part numbers ({em(FM_SRC['No source label'][1], 1)} billed) carry no source of supply; they average {p1(FM_SRC['No source label'][0])}, mostly no change.
Weighted on IML's own basis (quantity times yen base price) the same revision is {FM_QTY * 100:.2f}%, against {FM_AVG * 100:.2f}% weighted by parts billed. The previous revision, of September 2025, was about {p1(prev_rev)} (weighted by quantity billed) and fed our April 2026 list.</p>
<h3>From the IML/IMIT increase to +5% on our list</h3>
<div class='fig'>{svg_cost_bridge()}</div>
<p>Passing on the full IML/IMIT increase would raise our list by {p1(FM_AVG)} ({em(FM_EUR)}). Instead every part passes on the same 90.5% of its own increase.
The pad kits and the parts in categories a distributor already loses stay at today's price, and a small extra applies where UK web shops sell the same part dearer than us (section 4); together these land the list at exactly +5.00%.
Our margin falls by about {abs(PSUM['margin_pts_proposal']) * 100:.1f} points, because our list rises less than our cost.</p>
<h3>The formula behind every list price</h3>
<p>Our selling price is built from IML's or IMIT's yen base price, converted at the corporate exchange rate, reduced by our purchase discount, and divided by
one minus a <b>class margin</b>. IML assigns each part to a margin class, and the class alone sets the margin; nothing about the part's competition, market or demand enters the formula.
There are eight margin levels: {', '.join(MARGIN_LEVELS)}. Three in four part numbers (74.9%) carry 53%. On the priced lines our margin is 51.09% ({em(15.15e6)} gross profit on {em(29.65e6)} billed), and 84.3% of parts billed earns between 45% and 56%.</p>
<h3>Purchase terms and exchange rate</h3>
<p>From 5 January 2026 the purchase discount on Japan-sourced parts fell from 38.0% to 32.7% (we now pay 67.3% of the yen base instead of 62.0%); Thailand is unchanged at 38.9%.
The weaker yen largely offsets it. For an unchanged base of JPY 16,370, our cost is <b>EUR 62.00</b> on the October 2025 list basis (163.7 JPY/EUR),
<b>EUR 63.83</b> in April&ndash;September 2026 (172.6) and <b>EUR 61.72</b> at the rate announced for October 2026 to March 2027 (178.5): &minus;0.45% against the list basis.
The exchange rate moves the euro price and the euro gross profit; it never moves the margin percentage. Whether the announced rate also applies to Thailand-sourced parts is to be confirmed.</p>
<h3>Principles agreed in September, still standing</h3>
<ul class='tight'>
<li><b>Replace the automatic class margin</b> with decisions part by part and category by category: reduce selectively where a credible competing offer leaves the distributor too little margin, keep the price where the position is right, increase selectively where a genuine advantage supports it.</li>
<li><b>No universal 8% ceiling</b> on a part's increase. Larger increases need evidence and approval. This revision caps every part at its own IML/IMIT increase plus 5 points (section 6).</li>
<li><b>Parts in the 20% margin class keep their price.</b></li>
<li><b>How a price is approved</b>: compare the alternative offer (product, quality, date, availability, price level); allow distributor and dealer margin; check our net economics (cost, exchange rate, selling support); record the evidence, the commercial purpose and the expected result.</li>
<li><b>Every priced line carries a reason</b>, and separates our decision from a change passed through from IML or IMIT. The revision should also state its own effect on parts billed per truck in service, split into price, volume, mix and fleet, so that next year's increase is not read as an improvement.</li>
</ul>
<p class='small muted'>Two reminders on the arithmetic of a cut: a 5% lower net price needs about 11% more volume to keep gross profit at a 50% margin (an illustration, not a forecast);
and a reported internal precedent &mdash; a battery-electric vehicle battery priced at about 1% margin to answer an insurance-cost concern &mdash; shows that an exception can serve the wider vehicle offer. The battery case is management-reported and not verified here.</p>
""", "IML/IMIT increase: per-part base prices of September 2025 and September 2026 (yen) against SAP parts billing July 2025&ndash;June 2026, computed for this paper; source of supply per part from the +5% workbook of 29 September 2026; "
     "previous revision: September 2025 price revision weighted by quantity billed July 2024&ndash;June 2025; margin classes: 2026 price file (9 August 2026); book margin as measured on 19 September 2026; "
     "purchase discount and exchange rates: supplier notice of 22 December 2025 and the corporate rate notifications; agreed principles: management deck of 20 September 2026 and pricing policy paper of 17 September 2026."))

# ---------------------------------------------------------------- 3 parts category
cat_bars = [(k, v, NAVY2) for k, v in CAT_TOP.items()]
S.append(section("3", "Prices per parts category",
    "Every part number now sits in a parts category, so a price decision can apply to a whole category instead of to one part number at a time or to the whole list. "
    "That is how the decisions in this paper were made: a category facing competition stays at today's price in the markets where it matters, while the rest of the list moves. "
    "The categories carry no euro effect of their own; they are the means by which each decision's euro effect is applied.",
f"""
<p>The parts categories were approved on 2 October 2026. They arrange the list into {CAT_FAM} main families, {CAT_L2} categories and {CAT_L3} part types, anchored on the Isuzu parts catalogue.
All {len(PART):,} part numbers in this revision are found in it; {CAT_UNK_PARTS:,} of them ({em(CAT_UNK_EUR, 2)}, {p1(CAT_UNK_EUR / BASE)} of parts billed) still have no category assigned.</p>
<div class='fig'><div class='ttl'>Parts billed by main parts family, the twelve largest (July 2025&ndash;June 2026)</div>
{svg_hbar(cat_bars, lambda v, ax: (f"{v / 1e6:.0f}M" if ax else em(v, 1)), "Parts billed by main parts family", label_w=200, value_w=70, bar_h=16, gap=6)}</div>
<h3>How each decision uses the categories</h3>
<table><thead><tr><th style='width:34%'>Decision</th><th>Category it applies to</th><th style='width:24%'>Where</th></tr></thead><tbody>
<tr><td>Brake pad kits at today's price</td><td>Brakes &gt; Pads and shoes ({len(pads)} pad kits, {em(PADS_CAT)} billed)</td><td>All markets</td></tr>
<tr><td>Service parts at today's price</td><td>Categories used in scheduled maintenance: filters, brake pads and discs, clutch, and similar</td><td>Eight markets (section 5)</td></tr>
<tr><td>Body, collision and lighting at today's price</td><td>Accident and body; Lighting</td><td>Israel D-Max distributor</td></tr>
<tr><td>Lighting at today's price</td><td>Lighting</td><td>Israel trucks distributor</td></tr>
<tr><td>Recovery of the {ek(GIVEN)}</td><td>Repair and body categories, only on parts with no aftermarket alternative found</td><td>All markets except Armenia and Kazakhstan</td></tr>
<tr><td>Truck body panels not kept at today's price</td><td>Accident and body &gt; Panels</td><td>Israel trucks distributor</td></tr>
</tbody></table>
<p>Before the categories, a price could only be changed part number by part number, or by the same percentage across the whole list. The list itself stays one price per part;
a category decision for one market is applied as a distributor condition, the way stock-order and customer conditions already differ between distributors today.</p>
""", "parts categories approved on 2 October 2026 (three levels, anchored on the Isuzu parts catalogue); SAP parts billing July 2025&ndash;June 2026; decisions of 30 September and 2 October 2026."))

# ---------------------------------------------------------------- 4 spread over the parts
S.append(section("4", "How the +5% is spread over the parts",
    f"This chapter shows what the +5% does part by part. A typical part rises by {p1(PSUM['median_move'], True)}; {PSUM['parts_at_zero']:,} parts ({em(PSUM['eur_at_zero'])} billed) stay at today's price, "
    f"and the April 2026 rise shows no measurable fall in what dealers buy, except at Isuzu UK (D-Max).",
f"""
<p>Each part passes on 90.5% of its own IML/IMIT increase, which lands the list on exactly <b>+5.00%</b> ({e0(INC)}). One list price per part; no market sees a different list.</p>
<div class='cards'>
 {card("Typical part (median)", p1(PSUM['median_move'], True), "9 in 10 parts rise by " + p1(PSUM['p90_move']) + " or less")}
 {card("Parts at today's price", f"{PSUM['parts_at_zero']:,}", em(PSUM['eur_at_zero']) + " billed: pad kits, no IML/IMIT increase, or categories already lost")}
 {card("IML/IMIT increase above 15%", f"{fact15}", "reviewed one by one; the largest increase is " + p0(maxpart.proposal_move, True))}
 {card("Margin effect", f"{PSUM['margin_pts_proposal'] * 100:+.1f} pts", "weighted class margin, at today's rate and purchase terms")}
</div>
<h3>Three rules on top of each part's own increase</h3>
<ol class='tight'>
<li><b>Brake pad kits stay at today's price.</b> {len(pads)} kits, {e0(pad_eur)} billed. Two kits carry large IML/IMIT increases: 8982447940 ({p1(pad794.factory_move, True)}) and 8982169220 ({p1(pad922.factory_move, True)}).
 At an unchanged price their class margin falls from 45% to about 31&ndash;33%. Kit 8982447940 is the front pad kit bought mainly by Isuzu Truck UK and the Israel trucks distributor; the first draft of 29 September had it at +17.0%. Keeping it at today's price answers the leading dealer complaint in the UK truck network.</li>
<li><b>Parts at today's price where the distributor already loses the category</b>: on lines where a distributor sells under 45% of what its vehicles need in that category ({lost_parts} part numbers affected).</li>
<li><b>A small extra on {extra_parts} parts</b> where a UK trade web shop sells the same part number dearer than our reference dealer price, limited to what that evidence supports.</li>
</ol>
<h3>What dealers did after the April 2026 rise</h3>
<p>The April 2026 list change (median +{inv['median_list_change'] * 100:.1f}%, confirmed on Isuzu Truck UK invoices at +{inv['median_invoice_change'] * 100:.1f}%) gives the first usable test of how dealers react, measured on the distributors' sales to dealer.
Pooled over Isuzu Truck UK, Isuzu UK (D-Max), Ireland and Portugal, a part that rose 1% more than similar parts sold {abs(r_pool['beta_dlp']):.2f}% fewer units (standard error {r_pool['se_dlp']:.2f}):
statistically indistinguishable from no reaction. It is not precise enough to set prices part by part and is used only for volume scenarios.
<b>Isuzu UK (D-Max) is the exception</b>: {r_iuk['beta_dlp']:.2f} (&plusmn;{1.96 * r_iuk['se_dlp']:.2f}), and its dealer units fell {abs(iuk_units) * 100:.1f}% over the same months.</p>
<p>Before the market decisions, the {em(INC)} becomes about <b>{em(PSUM['revenue_central'])}</b> if the pooled reaction applies,
and {em(PSUM['revenue_stress'])} in a pessimistic case using the lowest 95% bound of the measurements. The pessimistic case is a stress test, not a forecast.</p>
<h3>Four front pad kits, one function</h3>
<p>Four front pad kits share one description at four list prices: 8975056801 and 8975546610 at EUR 82.25, 8982447940 at EUR 89.11, 8982169210 at EUR 102.65 &mdash; a 25% spread &mdash;
and each network buys almost only its own (Isuzu UK (D-Max) the cheapest, Isuzu Truck UK and the Israel trucks distributor the two dearest). None is superseded by another. Whether they are interchangeable is a catalogue question that is still open (section 14).</p>
""", "the +5% calculation by part number of 29&ndash;30 September 2026: IML/IMIT base prices of September 2026 against September 2025, parts billed July 2025&ndash;June 2026 (15,273 part numbers), "
     "measured distributor shares of need by category; dealer response: sales to dealer monthly files for Isuzu Truck UK (2023&ndash;2026), Isuzu UK (D-Max), Ireland and Portugal (2025&ndash;2026) against the dated list changes, "
     "with an invoice check on Isuzu Truck UK billing; pad-kit list prices and buying networks: 2026 price file and billing, as reported on 19 September 2026."))

# ---------------------------------------------------------------- 5 market by market
S.append(section("5", "Market by market: where service parts stay at today's price",
    f"Twenty-one markets were read one by one on the same evidence, to find where a price rise would cost us service business. "
    f"In eight markets service parts stay at today's price, and in Israel body, collision and lighting parts as well; together this gives up {e0(GIVEN)} of the +5%.",
f"""
<p>Each market was read on what it buys, how its fleet moves, how much of its service work we win (the <b>service share</b>: service parts its distributor
bought against what its fleet should need at the service intervals; network {NET * 100:.0f}% in 2025), what it pays against our list, and what dealers and distributors say.
The list stays one price per part; keeping a category at today's price in one market is applied as a distributor condition on that category.</p>
<div class='callout navy'><b>When service parts stay at today's price.</b> Vehicles we do not count buy in the market; or dealers measurably reacted to the April 2026 rise; or the fleet is flat
or shrinking while our service share is below the network or falling; or a documented price complaint on service parts together with a low or falling share.
Repair parts follow IML/IMIT in every market. Israel adds body, collision and lighting, because of the insurance total-loss rule (section 9). Armenia and Kazakhstan are left out of the market decisions.</div>
<div class='fig'><div class='ttl'>Who gives up what: increase not taken, by market and part group</div>
{svg_hbar(given_rows(), lambda v, ax: (f"{v / 1e3:.0f}k" if ax else ek(v)), "Increase given up by market and part group", label_w=290, value_w=70)}
</div>
<p class='small'>Total given up: <b>{e0(GIVEN)}</b>. Service parts at Isuzu UK (D-Max) alone are {ek(iuk_svc_given)}, the largest single item. The figure includes the Israel D-Max lighting decision ({e0(HR['UMI lighting hold']['step'])}),
which the market review of 30 September named but had not yet counted.</p>
""", "market-by-market review of 30 September 2026: SAP parts billing 2023&ndash;August 2026, dated price lists, the service-share measure by market and category, "
     "fleet planning estimates (July 2026, corrected 2026 column), sales to dealer files for the UK, Ireland and Portugal, distributor review minutes July&ndash;August 2026, Isuzu monthly market packs; "
     "Israel body and lighting recomputed in the recovery analysis of 2 October 2026."))

S.append(f"""<section class='pb'><h3 style='margin-top:0'>The 21 markets on one page</h3>{grid_html()}
<p class='small muted'>Colours: fleet red = flat or shrinking; service share red = below 80% of the network; change red = falling. * More than the counted fleet should need: vehicles we do not count buy here; not a real share.
"Follows IML/IMIT" = the normal increase; "today's price" = kept at today's price; "left out" = not part of the market decisions. Increase given up = the euro of the +5% not taken on the categories kept at today's price.</p>
<div class='src'><b>Sources.</b> as for section 5.</div></section>""")

# ---------------------------------------------------------------- 6 recovery: three ways
S.append(section("6", f"How the {ek(GIVEN)} is recovered: three ways considered",
    f"Keeping prices at today's level in eight markets and in Israel gives up {e0(GIVEN)}. To keep the average at +5%, that amount is recovered elsewhere on the list. "
    f"Three ways were compared; the decision is to recover it only on repair and body parts for which we found no aftermarket alternative, about +{WB.solver_t * 100:.1f} points on {int(WB.weighted_parts):,} parts, with nothing extra on service parts.",
f"""
<div class='fig'><div class='ttl'>From the +5% before market decisions to the decided recovery: the total stays at +5.00%</div>{svg_recovery_bridge()}</div>
<p class='small'>No part rises more than 5 points above its own IML/IMIT increase. Five parts would exceed that cap; the {e0(WB.cut_below_proposal_by_ceiling_eur)} cut from them is recovered as well, so the recovery totals {e0(WB.uplift_above_proposal_eur)}.</p>
<h3>The three ways</h3>
<table><thead><tr><th style='width:22%'></th><th>(a) Spread over all remaining parts, in proportion</th><th>(b) Only repair and body parts with no aftermarket alternative <span class='tag dec'>Decided</span></th><th>(c) Weighted part by part on outside prices</th></tr></thead><tbody>
<tr><td>How it works</td><td>Every part not kept at today's price rises {1 + WA.solver_t:.2f} times its own increase</td><td>+{WB.solver_t * 100:.1f} points on top of their own increase, on {int(WB.weighted_parts):,} repair and body parts ({em(WB.weighted_base_eur, 1)} billed)</td>
<td>Each part gets an extra in proportion to a score from 0 to 5: outside prices, genuine sold outside our network, no alternative found, slow seller, share of urgent orders, dealer response</td></tr>
<tr><td>Extra on service parts</td><td class='r'>{e0(WA.uplift_service_eur)}</td><td class='r'><b>0</b></td><td class='r'>{e0(WC.uplift_service_eur)}</td></tr>
<tr><td>Extra on repair parts</td><td class='r'>{e0(WA.uplift_repair_eur)}</td><td class='r'><b>{e0(WB.uplift_repair_eur)}</b></td><td class='r'>{e0(WC.uplift_repair_eur)}</td></tr>
<tr><td>Extra on body and collision parts</td><td class='r'>{e0(WA.uplift_body_eur)}</td><td class='r'><b>{e0(WB.uplift_body_eur)}</b></td><td class='r'>{e0(WC.uplift_body_eur)}</td></tr>
<tr><td>Share of the extra on parts with no aftermarket alternative found</td><td class='r'>{p0(WA.uplift_on_captive_strict_pct)}</td><td class='r'><b>{p0(WB.uplift_on_captive_strict_pct)}</b></td><td class='r'>{p0(WC.uplift_on_captive_strict_pct)}</td></tr>
<tr><td>Parts reaching the cap</td><td class='r'>{int(WA.parts_at_ceiling)}</td><td class='r'><b>{int(WB.parts_at_ceiling)}</b></td><td class='r'>{int(WC.parts_at_ceiling)}</td></tr>
<tr><td>Typical increase of a part that moves</td><td class='r'>{p1(WA.median_move_free_parts)}</td><td class='r'>{p1(WB.median_move_free_parts)}</td><td class='r'>{p1(WC.median_move_free_parts)}</td></tr>
</tbody></table>
<h3>Why (b)</h3>
<ul class='tight'>
<li><b>Service parts have alternatives.</b> Filters, pads, discs and clutches are sold by aftermarket brands, and service parts are where the complaints and the market decisions are. Way (a) would put {ek(WA.uplift_service_eur)} back on service parts, and way (c) {ek(WC.uplift_service_eur)}; way (b) puts nothing there.</li>
<li><b>Not enough outside price data for (c).</b> An aftermarket price exists for only {SUF['1_outside_prices_aftermarket_street_any_date']['parts']} parts; the score is therefore driven mostly by whether an alternative was found, how slowly the part sells and its share of urgent orders. It is a choice of weights, not a measurement.</li>
<li><b>Way (a) pushes hardest on parts IML and IMIT already raised most</b>, so {int(WA.parts_at_ceiling)} parts reach the cap, against {int(WB.parts_at_ceiling)} under (b).</li>
<li>All three ways land on exactly {e0(INC)}. With a flat 12% cap per part instead, way (b) would leave {int(WB12.parts_at_ceiling)} parts at the cap.</li>
</ul>
<h3>What the decided way does to each part group</h3>
<div class='fig'>{svg_segments()}</div>
<p>Averages over all lines, including those kept at today's price. Service parts fall from {p1(seg_b['service'][1])} to {p1(seg_b['service'][0])}, because they carry the market decisions and nothing extra;
repair parts rise from {p1(seg_b['repair'][1])} to {p1(seg_b['repair'][0])} and body and collision parts from {p1(seg_b['body'][1])} to {p1(seg_b['body'][0])}. A typical repair or body part with no aftermarket alternative found rises about {p1(WB.median_move_free_parts)} instead of about 6.3%.
Because the market decisions sit mostly on D-Max markets, D-Max parts average {p1(vl_b['LCV (D-Max)'][0])} and truck parts {p1(vl_b['Truck'][0])} (before the market decisions {p1(vl_b['LCV (D-Max)'][1])} and {p1(vl_b['Truck'][1])}).</p>
""", "recovery analysis of 2 October 2026: one list increase per part on the lines not kept at today's price; part groups from the parts categories approved on 2 October 2026 "
     "(body = Accident and body; service = categories used in scheduled maintenance; repair = the rest, including lighting); no aftermarket alternative found = no confirmed or likely competitor number, no aftermarket price observed, no cheaper Isuzu value-line alternative, "
     "not in the competitive-parts family, and not a category the distributor is measured to lose; D-Max/truck split from vehicle-family bands, the August 2026 parts lists and who buys the part."))

# ---------------------------------------------------------------- 7 Isuzu UK (D-Max)
S.append(section("7", "Isuzu UK (D-Max): the risk, and a suggested exemption",
    f"Isuzu UK (D-Max) is the only market where dealers measurably bought less after the April 2026 rise. Its service parts already stay at today's price, "
    f"but the decided recovery adds {ek(iuk_rb_uplift)} on its repair and body parts. Exempting it is suggested, not decided: the other markets would then carry that {ek(iuk_rb_uplift)}.",
f"""
<p><b>Isuzu UK (D-Max) dealers measurably bought less after the April 2026 rise</b>: {r_iuk['beta_dlp']:.2f} (&plusmn;{1.96 * r_iuk['se_dlp']:.2f}) &mdash; for every 1% a part rose more than similar parts, dealers bought about {abs(r_iuk['beta_dlp']):.1f}% fewer &mdash;
and dealer units fell {abs(iuk_units) * 100:.1f}% over April&ndash;July against the same months of 2025. The recovery puts <b>{ek(iuk_rb_uplift)}</b> of extra on its repair and body parts. Its body parts
that rose in April fell {abs(cat_iuk_body.median_rel_change_pct) * 100:.1f}% against its own median, on {int(cat_iuk_body.parts)} parts &mdash; a noise-level reading, but it points at exactly the parts the recovery raises.
The UK D-Max market is also under pressure from outside: the double-cab benefit-in-kind change of April 2025, and pickup registrations down 61.2% year on year in August 2026.</p>
<div class='callout' style='border-left-color:#eda100'><span class='tag sug'>Suggested, not decided</span> <b>Exempt Isuzu UK (D-Max) from the recovery.</b> Its repair and body parts keep their own IML/IMIT-based increase
(through the same distributor condition as the service parts); the {ek(GIVEN)} is recovered on repair and body parts in the other markets.
The total still lands on {e0(VI['total_step_eur'])}; repair and body parts with no aftermarket alternative outside Isuzu UK (D-Max) carry <b>+{VI['solver_t_pts'] * 100:.1f} points</b> instead of +{WB.solver_t * 100:.1f}.
Isuzu UK (D-Max) averages {p1(iuk.B_iuk_exempt_avg_move)} instead of {p1(iuk.B_avg_move)} (before market decisions {p1(iuk.proposal_avg_move)}). Parts at the cap stay at {VI['parts_at_ceiling']}; the typical moved part rises about {p1(VI['median_move_flex_parts'])}.</div>
<div class='fig'><div class='ttl'>Average increase by market, all lines, the twelve largest markets</div>
<div class='legend'><i style='background:{GREY}'></i>Before market decisions<i style='background:{BLUE}'></i>Decided<i class='sq' style='background:{AMBER}'></i>With Isuzu UK (D-Max) exempted (suggested)</div>
{svg_markets(12)}</div>
<p class='small'>Averages include the lines kept at today's price at 0%, which is why those markets sit below +5%. The other markets carry the relief: Isuzu Truck UK {p1(VMK.loc['ITUK'].B_avg_move)} to {p1(VMK.loc['ITUK'].B_iuk_exempt_avg_move)},
Israel trucks distributor {p1(VMK.loc['UTI'].B_avg_move)} to {p1(VMK.loc['UTI'].B_iuk_exempt_avg_move)}, Germany {p1(VMK.loc['GERMANY'].B_avg_move)} to {p1(VMK.loc['GERMANY'].B_iuk_exempt_avg_move)}. The trade-off is {ek(iuk_rb_uplift)} moved from the market that showed a reaction to markets that did not.</p>
""", "dealer response: sales to dealer files of Isuzu UK (D-Max), April&ndash;July 2025 against 2026, measured within part families against the April 2026 list change; body-part reading: parts with a rise of 3% or more, "
     "against the market's own median; exemption: the recovery analysis re-run on 2 October 2026 with Isuzu UK (D-Max) repair and body lines at their own increase (decided recovery reproduced exactly first); "
     "UK market: HMRC benefit-in-kind guidance (April 2025) and SMMT registrations, as reported on 19 September 2026."))

# ---------------------------------------------------------------- 8 evidence
am, gg = IDX["aftermarket_street"], IDX["genuine_grey"]
src_gg = RS["genuine_grey_sources_parts"]
S.append(section("8", "Outside price evidence: what it can carry",
    "We compare outside prices with what a customer pays at our dealers, to see where a rise is safe and where it would push customers to an alternative. "
    f"Aftermarket brands are mostly cheaper than us; genuine parts sold outside our network are mostly dearer. The data covers {p1(SUF['1_outside_prices_aftermarket_street_any_date']['billed_pct'])} of parts billed for aftermarket prices, too little to set prices part by part, and it carries no euro effect of its own.",
f"""
<p>An outside price is compared with our <b>reference dealer price</b>: our list price times 2.19, standing for what a customer pays at the dealer counter after distributor and dealer margins.
<b>The 2.19 basis is provisional</b> (set on 2 October 2026). The September papers used 1.785 times the list (1.40 to the dealer, then 1.275 to the customer); their ratios are not comparable with the ones below and are not carried over.
The <b>index</b> is the outside price, without VAT, divided by our reference dealer price: below 1.0 the outside seller is cheaper than us.</p>
<div class='fig'><div class='ttl'>Outside prices against our reference dealer price (median per part)</div>{svg_index_line()}</div>
<div class='two'>
<div><h3>Aftermarket brands: cheaper than us</h3>
<p>{am['parts']} parts carry an aftermarket shop price, {p1(SUF['1_outside_prices_aftermarket_street_any_date']['billed_pct'])} of parts billed. Median index <b>{am['median']:.2f}</b>
(weighted by parts billed {am['billed_weighted_median']:.2f}). {am['parts_below_0_8']} of them, {em(am['billed_below_0_8'], 1)} billed, sit below 0.8; only {am['parts_at_or_above_1']} parts ({em(am['billed_at_or_above_1'])}) have a rival dearer than us.
The data mostly names parts to keep at today's price, not parts to raise.</p></div>
<div><h3>Genuine sold outside our network: dearer than us</h3>
<p>{gg['parts']:,} parts carry a price for genuine Isuzu parts sold outside our network, {p1(SUF['1_outside_prices_genuine_grey']['billed_pct'])} of parts billed. Median index <b>{gg['median']:.2f}</b>;
on {gg['parts_at_or_above_1']:,} parts ({em(gg['billed_at_or_above_1'], 1)} billed) it is at or above our reference dealer price. <b>This rests mostly on one source</b>: an exporter's retail prices
({src_gg.get('amayama', 0):,} of the {gg['parts']:,} parts), and on the provisional 2.19 basis.</p></div>
</div>
<h3>Is the data good enough?</h3>
<div class='fig'>{svg_coverage()}</div>
<ul class='tight'>
<li><b>"No aftermarket alternative found" is mostly absence of evidence.</b> {p0(SUF['2_captive_strict']['parts_pct'])} of parts ({p0(SUF['2_captive_strict']['billed_pct'])} of parts billed) pass that test; only {SUF['2_competitive_evidence_brief_definition']['parts']} parts have any competitor evidence at all.
Body parts look almost entirely without alternative, but non-genuine (pattern) body parts have simply not been searched. A price check on pattern parts for the top 50 body parts would show whether the body share of the recovery is safe.</li>
<li><b>A part has a price range, not one aftermarket price.</b> Front pad kit 8975546610 (list EUR 82.25) appears in 42 online listings in March 2026, from EUR 17.09 to EUR 213.40, median EUR 58.09, across very different brands and transaction levels.</li>
<li><b>We do not have distributor or dealer resale prices</b> and will not obtain them. Every dealer-level figure is constructed. Whether a distributor passes a change in our price on to its dealers is unknown and can only be answered by asking.</li>
<li><b>Israel is not a discount channel.</b> Of the Israeli shop lines checked in September, none sat below a distributor purchase price; the cheapest was 2.4 times it. Parallel trade inside the EEA is lawful and cannot be closed by agreement.</li>
</ul>
""", "price observations as of 2 October 2026 (aftermarket web shops, brand recommended retail prices, genuine parts sold outside the network; VAT removed, median per part, last 12 months first); "
     "graded competitor cross-references with a second independent source (2 October 2026); parts categories approved on 2 October 2026; pad kit price range: Eucon/PartsPool batch of 29 March 2026; "
     "Israel shop check of 18 September 2026 against distributor purchase prices."))

# ---------------------------------------------------------------- 9 collision Israel
S.append(section("9", "Collision, insurance and lighting in Israel",
    "In Israel a high parts price can make an insurer write off a repairable vehicle, and we lose the whole repair. "
    f"For that reason the Israel D-Max distributor keeps body, collision and lighting parts at today's price ({ek(umi_given_body)} of increase given up) and the Israel trucks distributor keeps lighting ({ek(HR['UTI lighting hold']['step'])}).",
f"""
<p>In Israel a vehicle is declared a total loss when damage reaches 60% of its pre-accident value, and the insurer may settle as a constructive total loss from 50&ndash;55% (two policy readings differ).
The repair estimate is built from our parts list prices. A high parts line can therefore push a repairable vehicle over that limit and lose the whole repair &mdash; and, for a fleet on a repair-and-maintenance contract,
the parts for the remaining contract years. Routine service parts are not affected.</p>
<ul class='tight'>
<li><b>The limits were verified in the policy for vehicles up to 3.5 tonnes</b>, which covers the D-Max. The clause for heavier vehicles was not found, so for the Israel trucks distributor the exposure is unverified.</li>
<li>The same policy allows a light to be replaced by a part of "similar description or characteristic", and requires new or genuine parts only for vehicles up to two years old.</li>
<li>The Israel trucks distributor's July 2026 presentation shows the collision package rising from EUR 679 to EUR 2,144 (N-Series 7.5 t) and EUR 924 to EUR 2,314 (F-Series 10 t) between the old model and the new N-Series (P700); a rear light +1,228%;
the bumper split from one part at EUR 143.37 into four at EUR 320.00. Part of the lamp gap may be a different lamp rather than a list increase. The distributor runs 1,700 trucks on five-year repair-and-maintenance contracts.</li>
<li>Its lighting is EUR 133,667 of billing (3.9% of its parts billed), already 74% in the lowest-margin class (47.5%).</li>
</ul>
<div class='callout navy'><span class='tag dec'>Decided</span> The Israel D-Max distributor keeps body, collision and lighting at today's price ({ek(umi_given_body)} of increase);
the Israel trucks distributor keeps lighting ({ek(HR['UTI lighting hold']['step'])}). This replaces the September idea of giving lighting a smaller share of the increase than bodywork.
Beyond price, two levers remain: the bumper and grille packaging on the new N-Series, which is a question for IML, and a paid-on-genuine-use arrangement with insurers &mdash; in 2018 a funded rebate to the insurer, split equally between IML and ISZE, was proposed for exactly this case.</div>
""", "Israeli motor policy wordings for vehicles up to 3.5 tonnes, read 19 September 2026; Israel trucks distributor presentation, July 2026 (pages 8, 27, 30, 31); its lighting and collision billing, last twelve months to September 2026; "
     "2018 correspondence on an insurer rebate, as carried in the research paper of 19 September 2026 (reported, not re-verified); market-by-market review and recovery analysis."))

# ---------------------------------------------------------------- 10 Israel truck panels
S.append(section("10", "Israel truck body panels: delivery times, not price",
    "The Israel trucks distributor has complained about both prices and delivery of body panels. The data shows that it loses panel sales mainly to delivery times, not to price, "
    f"so its panels take the normal increase ({e0(panel_inc)} kept) and the answer is to stock new N-Series (P700) panels against its forecast.",
f"""
<div class='callout navy'><span class='tag dec'>Decided</span> <b>Israel truck body panels are not kept at today's price</b> (2 October 2026). They take the normal increase. The issue is availability, addressed by stocking new N-Series (P700) panels against the distributor's forecast.</div>
<div class='cards'>
 {card("Panels billed, Jan-Aug 2026 vs 2025", p1(eur_chg, True), f"{e0(pb_['eur_2025'])} to {e0(pb_['eur_2026'])}, while units rose")}
 {card("Same panels, both years", "units " + p1(unit_chg, True), "euro " + p1(eur_chg_same, True))}
 {card("Waiting time on back orders", f"{int(waits['min'])}-{int(waits['max'])} weeks", f"median {int(waits['50%'])} weeks, distributor's marked list of 9 June", "terra")}
 {card("Increase kept by not exempting panels", e0(panel_inc), f"exempting all its body parts except lighting would have given up up to {e0(body_inc)}", "blue")}
</div>
<h3>Availability</h3>
<p>The distributor has reported repeated back orders on body and panel parts through 2026, four to sixteen weeks from order to shipment, with the same part numbers on back order month after month,
and has asked ISZE to stock new N-Series (P700) items to raise the fill rate. Our weekly back-order lists for weeks 2 to 40 of 2026 confirm it: open panel lines averaged {bwp.loc['WK2-13', 'lines']:.0f} a week in weeks 2&ndash;13,
{bwp.loc['WK14-26', 'lines']:.0f} in weeks 14&ndash;26 (peak {int(bw_peak.lines)} in week {int(bw_peak.week)}) and {bwp.loc['WK27-40', 'lines']:.0f} in weeks 27&ndash;40; in week {int(bw_last.week)} {int(bw_last.lines)} lines were open.
The same body parts keep returning: {int((REC.weeks_on_list >= 13).sum())} body parts sat on 13 or more of the 39 weekly lists. On the list of 1 July a roof panel was open 139 days, and one front inner lid had been ordered four times, on normal, rush and vehicle-off-road terms, and was still open.
The urgent (rush and vehicle-off-road) share of panel order lines rose from 5.3% in the first half of 2025 to 15.6% in January&ndash;March 2026.</p>
<h3>Billing and price</h3>
<ul class='tight'>
<li>Panel billing fell {abs(eur_chg) * 100:.1f}% in January&ndash;August 2026 against 2025, while units rose. 53% of the euro drop is a single F-Series grille (8972670504), a 2025 stock build being used up.
On the panels bought in both periods, units rose {p1(unit_chg)} and euro fell {abs(eur_chg_same) * 100:.1f}%. The distributor's other parts fell 11.8%; other markets' panels rose 7.6%. Its own panel sales to its customers held at about 560&ndash;590 units a month.</li>
<li>On the same panels the distributor paid a median {p1(pp_['median'], True)} in 2026 against a median list rise of {p1(pp_['list_change_same_parts_median'], True)}; it pays about 74% of list on panels (79% in 2025).
Across {UN['t5c_parts_used']} panels, larger list rises did not lose more volume (rank correlation {UN['t5c_rank_corr_listchange_vs_unitgrowth']:+.2f}).</li>
<li>The distributor's cost on new N-Series body parts is about a quarter of its own selling price (its July 2026 sales report), so a 6.4% increase adds at most about 1.6% to its shelf price.</li>
<li>Its price complaint names three body parts as competing with aftermarket and used parts: grille 8974289771 (+3%), front panel 8981226950 (+16%) and door 8982606020 (+16%).
Two of them fit a price story: the front panel fell from 20 to 7 units and the grille from 28 to 12. The new N-Series collision-package increase (section 9) is a model change, not the April price change.</li>
</ul>
<p><b>What follows from the decision.</b> Agree a stocking plan for new N-Series body panels against the distributor's forecast, so that the fill rate, not the price, is what changes. The three parts it named stay visible in the price evidence.</p>
<p class='small muted'>Limits: the value of open back-order lines is at today's list price; order types are missing in our billing for April&ndash;June 2026; lost jobs are not visible in our data &mdash; only the distributor can supply them.</p>
""", "Israel trucks distributor correspondence February&ndash;October 2026 (read only) and its marked back-order list of 9 June 2026; SAP parts billing to 31 August 2026; ISZE weekly back-order lists, weeks 2&ndash;40 of 2026; "
     "the distributor's own new N-Series body-parts sales report (July 2026, cost-to-sales ratio only); parts categories approved on 2 October 2026 (Accident and body &gt; Panels); increase at stake from the +5% calculation on its lines July 2025&ndash;June 2026."))

# ---------------------------------------------------------------- 11 discounts and surcharges
lever_rows = [("Halve each market's gap to list on stock orders", L4["stock_halve_gap_eur"], "#5b4a8a"),
              ("Narrow the stock-order discount by 1 point", L4["stock_narrow_1pt_eur"], "#5b4a8a"),
              ("Urgent-order surcharge +2 points", L4["urgent_plus2pt_eur"], "#8f7fc0"),
              ("Urgent-order surcharge +1 point", L4["urgent_plus1pt_eur"], "#8f7fc0")]
gap_bar = [(NAME.get(k, k.title()) + f" (pays {r.SOR_pays_pct_list * 100:.1f}%)", r.a_stock_halve_gap_to_list_eur, "#5b4a8a")
           for k, r in gap_rows.iterrows()]
S.append(section("11", "Discounts and surcharges outside the price list",
    "Besides the list price, what a distributor pays depends on its stock-order discount and on the surcharge on urgent orders. "
    f"These terms are worth about as much as the price list measures (halving each market's gap to list on stock orders alone is {ek(L4['stock_halve_gap_eur'])} a year), "
    "but they are commercial terms negotiated per distributor and are not part of this price revision.",
f"""
<div class='negbox'><b class='h'>NEGOTIATION TOPIC &mdash; NOT A PRICE LIST CHANGE.</b> Everything in this section is a distributor condition: what a distributor pays against the list on stock orders,
and what it pays on rush and vehicle-off-road orders. None of it changes a list price, and none of it is part of the +5%.</div>
<p>On stock orders most markets pay 99&ndash;100% of list, but several pay less through customer conditions: the Israel trucks distributor {LV.loc['UTI'].SOR_pays_pct_list * 100:.1f}%, the Israel D-Max distributor {LV.loc['UMI'].SOR_pays_pct_list * 100:.1f}%,
Norway {LV.loc['NORWAY'].SOR_pays_pct_list * 100:.1f}%, Isuzu Truck UK {LV.loc['ITUK'].SOR_pays_pct_list * 100:.1f}%, Isuzu UK (D-Max) {LV.loc['IUK'].SOR_pays_pct_list * 100:.1f}%. Rush and vehicle-off-road orders are billed above list in most markets.
Valued on calendar-2025 order lines at the 2025 list (Armenia and Kazakhstan left out):</p>
<div class='fig'><div class='ttl'>What each term is worth a year, against the increase given up by the market decisions</div>
{svg_hbar(lever_rows, lambda v, ax: (f"{v / 1e3:.0f}k" if ax else ek(v)), "Discounts and surcharges", label_w=260, value_w=70, ref=(GIVEN, "given up " + ek(GIVEN)), vmax=500_000)}</div>
<div class='fig'><div class='ttl'>Halving the gap to list on stock orders, by market</div>
{svg_hbar(gap_bar, lambda v, ax: (f"{v / 1e3:.0f}k" if ax else ek(v)), "Halving the gap to list by market", label_w=270, value_w=70)}</div>
<p>Narrowing the stock-order discount by 1 point everywhere is worth {ek(L4['stock_narrow_1pt_eur'])}, of which {ek(L4['stock_narrow_1pt_eur_excl_service_hold_markets'])} in markets where service parts take the normal increase.
The urgent-order surcharge applies to {em(L4['urgent_list_value'])} of urgent orders at list value. The constraints are real: the two Israeli distributors' levels are negotiated customer conditions,
and the Israel D-Max distributor and Isuzu UK (D-Max) are markets where service parts stay at today's price. These are items for the distributor negotiations, to be decided separately from the price list.</p>
""", "SAP parts billing, calendar year 2025, by order type (stock, rush, vehicle-off-road), valued at the 2025 list price per part; Armenia and Kazakhstan excluded; recovery analysis of 2 October 2026."))

# ---------------------------------------------------------------- 12 new N-Series
S.append(section("12", "New N-Series (P700) parts and the next price list",
    f"The new N-Series (P700) brings {P7['parts']:,} part numbers that we have hardly billed yet ({e0(P7['proposal_base_billed'])} in this year's base), so this year's increase does not reach them. "
    "What matters is a well-set first price on the next price list; there is no euro effect this year.",
f"""
<p class='lead'><span class='tag next'>Next price list</span> The new N-Series parts are a matter for the <b>next</b> price list, not for this year's revision.</p>
<div class='cards'>
 {card("New N-Series-only part numbers", f"{P7['parts']:,}", "on the provisional new-parts list")}
 {card("Ever billed, 2023 to August 2026", f"{P7['with_any_billing_2023_aug2026']}", em(P7['billed_eur_2023_aug2026'], 2) + f", of which {ek(P7['by_year']['2023'])} in 2023")}
 {card("In this year's base", f"{P7['in_proposal_base']}", e0(P7['proposal_base_billed']) + " billed")}
 {card("Billed July-August 2026", f"{P7['with_billing_jul_aug_2026']}", e0(P7['billed_eur_jul_aug_2026']))}
</div>
<p>They need a first price, not an increase. What the September launch work established, and still stands:</p>
<ul class='tight'>
<li><b>New parts carry no weight in an increase weighted by parts billed</b>, so a revision target does not bind them. But most new numbers are not unpriced: of the 1,132 new N-Series and D-Max 2.2L part numbers without billing history in September, 1,048 already carry four consecutive published prices (2023&ndash;2026). The pricing freedom comes from the zero weight, not from the absence of a reference.</li>
<li><b>The 13 exhaust after-treatment parts (SCR and AdBlue sensors, pumps, control units, catalyst, particulate filter assembly)</b> sit exactly at their class price (within 0.45%) and have no aftermarket equivalent in any source on file. On the price list they could carry +25% to +35%; that level is a judgment, anchored only on a particulate-filter sensor (8978808270) that earns 69.3% gross margin against 56% in its class.</li>
<li><b>Do not commit a launch price before one question is answered</b>: whether IML's base price already contains a premium over transfer cost. If it does, there is less scope to price higher.</li>
<li><b>Class assignment is margin assignment.</b> 922 of 1,071 new parts with a class sit in the 53% margin class, 2 in the 56% class. Whether ISZE has a voice in how IML classes new parts is worth more than most of this year's revision.</li>
<li><b>Parts that fail in the warranty window</b>: set the launch price towards the top of the band and keep it flat once each vehicle's own warranty ends. The modelled D-Max 2.2L comparison is close to neutral over ten years and depends on the warranty term (it pays from about three years); the term and mileage cap must be confirmed market by market.</li>
<li>Israel's export list sits a measured 13.95% below the standard list (not the recorded 10%); any Israeli new N-Series price must be restated before it is read across.</li>
</ul>
""", "new N-Series-only parts: provisional new-parts list and SAP billing 2023&ndash;August 2026 (recovery analysis, 2 October 2026); launch facts: new N-Series and D-Max 2.2L launch pricing work of 19 September 2026 "
     "(2026 price file, published price history 2023&ndash;2026, competitor files); warranty-window model: pricing specification, section 9.3; Israel export list against the standard list on 134,896 matched part numbers."))

# ---------------------------------------------------------------- 13 background
S.append(section("13", "Background that still stands",
    "The September papers carried four strands of work that this revision does not replace. They are kept here in short because each bears on the next price list; none of them changes the euro effects in this paper.",
f"""
<h3>The pickup buyer is not a truck buyer</h3>
<p>The UK operator's licence does not bind the D-Max: it is plated at 3,100 kg (the licence applies from 3,500 kg) and is exempt as a dual-purpose vehicle. The exception is towing: with a 6,000 kg train weight, a D-Max towing plant is a licensed combination,
and that customer is less price-sensitive &mdash; but we cannot tell him apart in our sales data. Independent UK garages advertise D-Max servicing at up to 50% below the dealer while preserving the warranty, and the parts are visible on consumer price sites.
Ireland carries the heaviest compliance burden (an annual commercial roadworthiness test and a statutory maintenance duty); Portugal buys the pickup as a tax instrument (over 90% registered with three seats).
In Israel D-Maxes run 34,443 km a year, the highest of the pickup markets; 66.4% of D-Maxes on Israeli roads are privately owned, while the best-selling new trim goes mostly to leasing companies.</p>
<h3>Refurbishment is a third price level below the aftermarket brands</h3>
<p>A cleaned particulate filter costs roughly 3&ndash;30% of a new part, depending on market and vehicle class. Israeli regulation permits removing the filter for cleaning, repair or replacement (reported, not re-verified),
and a specialised refurbishment trade serves garages, insurers and leasing companies there. Our own warranty records show the Israel trucks distributor's filter claims at EUR 696,907, 76% of the filter cost outside the stated 3-year / 100,000 km terms,
and claim costs of 1.2&ndash;1.8 times our own list price (mechanism not established). The lever is timing rather than price: keep the after-treatment price flat once each vehicle's warranty ends.
Isuzu Truck UK has supplied new filters at remanufactured-level prices on a new-in-lieu basis since 2017; the question is why Israel does not get that answer.</p>
<h3>How other manufacturers price</h3>
<p>Cost-plus by class is what most manufacturers do; the money is on parts without an alternative (practitioner bands: competitive parts 25&ndash;35% margin, parts without an alternative 55&ndash;75%), while our list earns one band around 51% for both.
"Matching quality" parts from the same supplier in its own box sit at roughly 60&ndash;80% of a genuine price. Listed independent distributors earn 27&ndash;29% gross margin. Sensors and after-treatment are contested in the truck channel;
the parts genuinely closed to others are modules paired and coded to the individual vehicle and, until EU Regulation 2026/699 opens it from 23 December 2026, driver-assistance (ADAS) calibration. Every European truck maker runs a lower-priced own parts line; ours is the Best Value Parts (BVP) range.</p>
<h3>Volume response cannot be read from history</h3>
<p>Uniform increases leave almost no price variation to measure against; the April 2026 rise was the first with enough spread, and it shows a pooled reaction indistinguishable from zero (section 4).
The only route to a real measure is a field test: one family, a group of distributors, a matched control group.</p>
""", "pickup market research of 19 September 2026 (UK, Irish, Portuguese and Israeli regulations and statistics; UK fleet mileage 2020&ndash;2026); refurbishment and particulate-filter research of 19 September 2026 "
     "(supplier catalogues, regulators, ISZE warranty files); external review of manufacturer and aftermarket pricing practice, 17 September 2026 (figures graded there as measured or trade-reported); EU Delegated Regulation 2026/699."))

# ---------------------------------------------------------------- 14 open points
S.append(section("14", "Open points and next actions",
    f"Two points remain open in this revision: the Israel D-Max leasing share ({ek(umi_service_step)} of increase at stake) and the suggested Isuzu UK (D-Max) exemption ({ek(iuk_rb_uplift)} moved between markets). "
    "The rest of this chapter lists the questions carried over from September and the actions that follow from the decisions.",
f"""
<h3>Open in this revision</h3>
<table><thead><tr><th style='width:24%'>Point</th><th>What is open</th><th style='width:24%'>What is at stake</th></tr></thead><tbody>
<tr><td><span class='tag open'>Open</span><br><b>Israel D-Max distributor: leasing share</b></td><td>Leased double cabs in Israel must use genuine parts in their first two years and run the highest mileage of the pickup markets. If leasing fleets are most of the distributor's volume, its service parts could take the normal increase.
The share is unknown and is <b>not being requested now</b>; its service parts stay at today's price until it is known.</td>
<td class='small'>{em(umi_service_billed)} of service parts billed; {ek(umi_service_step)} of increase given up.</td></tr>
<tr><td><span class='tag sug'>Suggested</span><br><b>Isuzu UK (D-Max) exemption</b></td><td>Its repair and body parts keep their own IML/IMIT-based increase, without a share of the recovery (section 7).</td><td class='small'>{ek(iuk_rb_uplift)} moved from Isuzu UK (D-Max) to the other markets.</td></tr>
</tbody></table>
<p class='small'><span class='tag dec'>Settled on 2 October</span> Ukraine takes the normal increase ({em(uk.billed_eur)} billed in the base; average {p1(uk.B_avg_move)}). Israel truck body panels take the normal increase (section 10).</p>
<h3>Questions carried over from September, still open</h3>
<ol class='tight'>
<li>Are the four front pad kits interchangeable? A catalogue question; if they are, a 25% price spread across networks on one safety-critical wear part is a commercial finding.</li>
<li>Does IML's base price embed a premium over transfer cost? It decides how high the new N-Series parts can be priced at launch.</li>
<li>What is the total-loss limit for vehicles above 3.5 tonnes in Israel, and how often does a parts line actually tip a repair?</li>
<li>What do distributors do with a change in our price &mdash; pass it on, or keep the difference? A conversation with Isuzu Truck UK and the others, not a data request.</li>
<li>Does ISZE have a voice in how IML assigns new part numbers to a margin class?</li>
<li>Is the Best Value Parts range deliberately priced against the aftermarket brands in front of those parts, and should its cross-reference be extended?</li>
<li>Why does Israel get the remanufactured-filter answer and the UK the new-in-lieu answer? And what is the filter warranty term in each market?</li>
<li>Does the announced exchange-rate treatment also apply to Thailand-sourced parts?</li>
</ol>
<h3>Next actions</h3>
<ol class='tight'>
<li>Decide the Isuzu UK (D-Max) exemption.</li>
<li>Agree a stocking plan for new N-Series body panels against the Israel trucks distributor's forecast (section 10).</li>
<li>Set up the market decisions and the recovery as distributor conditions per parts category; the list stays one price per part. Not built yet.</li>
<li>Run a price check on pattern parts for the top 50 body parts before the body share of the recovery is fixed.</li>
<li>Confirm the reference dealer price basis (2.19 times the list, provisional).</li>
<li>Take the discounts and surcharges into the distributor negotiations as a separate item.</li>
<li>Prepare first prices for the new N-Series parts for the next price list.</li>
</ol>
""", "this paper, sections 4&ndash;12; market-by-market decision record (Ukraine, Israel D-Max distributor); open points of the recovery analysis of 2 October 2026; questions carried over from the pricing policy papers of 17 and 19 September 2026 and the management deck of 20 September 2026."))

# ---------------------------------------------------------------- appendix
S.append(section("A", "Terms and sources",
    "This appendix explains the terms used in the paper and names the sources behind the numbers in plain words. It carries no decision and no euro effect.",
f"""
<h3>Terms</h3>
<table class='small'><tbody>
<tr><td style='width:26%'><b>Parts billed</b></td><td>Our net sales of parts to distributors. The revision base is July 2025 to June 2026, parts with an IML/IMIT price on both dates: {e0(BASE)}, {len(PART):,} part numbers.</td></tr>
<tr><td><b>Sales to dealer</b></td><td>What our distributors sell on to their dealers, from the distributors' own monthly files.</td></tr>
<tr><td><b>IML/IMIT increase</b></td><td>A part's change in the IML (Japan) or IMIT (Thailand) base price, September 2026 against September 2025, in yen, before purchase discount and exchange rate.</td></tr>
<tr><td><b>Kept at today's price</b></td><td>A category kept at its current price in one market, applied as a distributor condition; the list stays one price per part.</td></tr>
<tr><td><b>Distributor condition</b></td><td>A term agreed with one distributor that sets what it pays against the list, the way stock-order and customer conditions already work.</td></tr>
<tr><td><b>Parts category</b></td><td>The three-level grouping of every part number (family, category, part type), approved on 2 October 2026.</td></tr>
<tr><td><b>Service / repair / body parts</b></td><td>Service = parts used in scheduled maintenance (filters, brake pads and discs, clutch and similar); body = the Accident and body family (panels, bumpers, glass, doors); repair = everything else, including lighting.</td></tr>
<tr><td><b>No aftermarket alternative found</b></td><td>No confirmed or likely competitor part number, no aftermarket price observed, no cheaper Best Value Parts alternative, not in the competitive-parts family, and not a category the distributor is measured to lose.</td></tr>
<tr><td><b>Genuine</b></td><td>Isuzu-branded parts supplied through IML or IMIT. <b>Genuine sold outside our network</b>: the same parts offered by exporters and shops that do not buy from us.</td></tr>
<tr><td><b>Aftermarket</b></td><td>Parts made by other brands to fit Isuzu vehicles, sold by independent shops and garages.</td></tr>
<tr><td><b>Reference dealer price</b></td><td>Our list price times 2.19 (provisional, 2 October 2026): what a customer pays at the dealer counter after distributor and dealer margins. A construction, not an observation.</td></tr>
<tr><td><b>Index</b></td><td>Outside price without VAT divided by our reference dealer price. Below 1.0 the outside seller is cheaper.</td></tr>
<tr><td><b>Service share</b></td><td>Service parts a market's distributor bought, against what its fleet should need at the service intervals.</td></tr>
<tr><td><b>Dealer response</b></td><td>How much less of a part dealers bought per 1% that it rose more than similar parts. Measured on the April 2026 list change.</td></tr>
<tr><td><b>Distributors</b></td><td>Isuzu UK (D-Max) and Isuzu Truck UK are the two UK distributors; the Israel D-Max distributor and the Israel trucks distributor are the two Israeli distributors. Never combined.</td></tr>
<tr><td><b>Standard price list</b></td><td>The list price per part, one price for every market on it. Ukraine buys on it. The price basis for Armenia and Kazakhstan is a separate, open decision.</td></tr>
<tr><td><b>Best Value Parts (BVP)</b></td><td>Isuzu's own lower-priced parts range.</td></tr>
<tr><td><b>New N-Series (P700)</b></td><td>The new generation of the Isuzu N-Series truck.</td></tr>
<tr><td><b>Stock / rush / vehicle-off-road</b></td><td>Order types. Rush and vehicle-off-road orders are urgent orders, usually billed above list.</td></tr>
</tbody></table>
<h3>Sources</h3>
<div class='small muted' style='line-height:1.55'>
SAP parts billing (July 2025&ndash;June 2026 for the revision base; 2023&ndash;August 2026 for trends). IML and IMIT base prices of September 2025 and September 2026 per part. The +5% calculation by part number of 29&ndash;30 September 2026 and its workbook (read only, not changed).
The market-by-market review of 30 September 2026 and its decision record. The recovery analysis of 2 October 2026, including the Isuzu UK (D-Max) exemption run. The parts categories approved on 2 October 2026.
Price observations collected up to 2 October 2026 and graded competitor cross-references. Sales to dealer files of Isuzu Truck UK, Isuzu UK (D-Max), Ireland and Portugal. ISZE weekly back-order lists for the Israel trucks distributor, weeks 2&ndash;40 of 2026, and the distributor's correspondence.
Carried over from the archived September papers: pricing policy paper of 19 September 2026 (margin classes, book margin, Israel insurance, pickup market, new N-Series launch, refurbishment, external review);
pricing policy paper of 17 September 2026 (reasons per priced line, per-truck effect, warranty window); management deck of 20 September 2026 (purchase terms, exchange rates, share of the 53% class, agreed principles, battery precedent, pad-kit price range).
</div>
""", "as listed above."))

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Parts Pricing Policy</title>
<style>{CSS}</style></head>
<body><div class="wrap">{''.join(S)}</div></body></html>"""

# ======================================================================= guards
low = page.lower()
for bad in ("http://", "https://", "<script"):
    assert bad not in low, bad
no_style = re.sub(r"<style>.*?</style>", "", page, flags=re.S)
visible = html.unescape(re.sub(r"<[^>]+>", " ", no_style))
vlow = visible.lower()
BANNED_CI = ["option a", "option b", "option c", "captive", "proposal move", "step", "hold", "x0.905", "0.905",
             "room", "edges", "tier", "release", "factory-led", "factory move", "street", "sell-out", "sellout", "wallet",
             "mode a", "mode b", "iml v7", "model b", "book b", ".json", ".csv", ".py", ".parquet", ".xlsx", "_build"]
BANNED_CS = ["IUK", "ITUK", "UMI", "UTI", "ISD", "AIM", "PR00", "CIS", "KS"]
hits = {w: vlow.count(w) for w in BANNED_CI if w in vlow}
hits.update({w: len(re.findall(rf"\b{w}\b", visible)) for w in BANNED_CS if re.search(rf"\b{w}\b", visible)})
# attributes too (aria-labels), not only visible text
attr_low = " ".join(re.findall(r'(?:aria-label|title)="([^"]*)"', no_style)).lower()
hits.update({"attr:" + w: attr_low.count(w) for w in BANNED_CI if w in attr_low})
for w in hits:
    for mm in re.finditer(re.escape(w.replace("attr:", "")), vlow):
        print("BANNED", w, "...", visible[max(0, mm.start() - 50): mm.end() + 30].replace("\n", " "))
assert not hits, hits
assert not re.search(r"\bnan\b|\bNaN\b|EUR nan|EUR None|None%", visible) and ">None<" not in page, "nan"
OUT_HTML.write_text(page, encoding="utf-8")
OUT_CMD.write_bytes(f'@echo off\r\nstart "" "%~dp0{OUT_HTML.name}"\r\n'.encode("ascii"))
print(f"IML/IMIT avg increase (billed-weighted) {FM_AVG:.4%}; by segment {({k: round(v, 4) for k, v in FM_SEG.items()})}; "
      f"by source {({k: round(v[0], 4) for k, v in FM_SRC.items()})}; qty x yen basis {FM_QTY:.4%}")
print(f"bridge: full {D_FULL:,.0f}  k {D_K:,.0f}  pads -{D_PADS:,.0f}  lost -{D_LOST:,.0f}  extra +{D_EXTRA:,.0f}  other {D_OTHER:+,.0f}  = {INC:,.0f}")
print("written", OUT_HTML, f"{OUT_HTML.stat().st_size / 1024:.0f} KB")
print("written", OUT_CMD)
