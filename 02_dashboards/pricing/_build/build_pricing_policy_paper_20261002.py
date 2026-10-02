# -*- coding: utf-8 -*-
"""
Builds the merged parts pricing policy paper of 2 October 2026.

One paper replaces the earlier policy papers (17 Sep, 17 Sep revision 2, 19 Sep revision 3, the 24 Sep
rebuild) and the management decks (v1.0 to v1.4). Where later work supersedes a statement or a number,
the later one is used. The older papers are archived in
01_data/92_archive/pricing_papers_superseded_2026-10-02/.

Self-contained HTML (no CDN, no script, charts as inline SVG drawn here), then a PDF via headless Chrome.

Numbers read at build time (traceable):
  _build/price_5pct_proposal_2026-09-29/price_5pct_proposal_summary_2026-09-29.json   +5% proposal
  _build/price_5pct_proposal_2026-09-29/market_exercise_decisions_2026-09-30.json      21-market holds
  _build/price_5pct_proposal_2026-09-29/market_facts_2026-09-30.json                   market grid
  _build/price_5pct_proposal_2026-09-29/dealer_price_response_2026-09-29.json          dealer response
  _build/price_5pct_proposal_2026-09-29/room_to_raise_2026-10-02/*                     where the +5% comes from
     room_to_raise_summary_2026-10-02.json, room_to_raise_scenarios_2026-10-02.csv,
     room_to_raise_scenarios_by_segment_market_2026-10-02.csv, lever4_order_terms_2026-10-02.csv,
     dealer_response_by_category_2026-10-02.csv,
     room_to_raise_variant_B_iuk_exempt_2026-10-02.{json,csv}   (scan builder, --variant-b-iuk-exempt)
Carried-over facts from the September papers and decks are constants below, each with its origin.

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
UBO = pd.read_csv(UTIP / "t6b_uti_backorder_summary.csv").set_index("seg")
UST = pd.read_csv(UTIP / "t8b_uti_step_master_vs_release.csv")

BASE = RS["proposal"]["base_eur"]
STEP = RS["proposal"]["step_eur"]
K = RS["proposal"]["scaling_k"]
assert abs(K - PSUM["k"]) < 1e-6 and abs(STEP - PSUM["step_eur"]) < 1
HOLDS = RS["holds"]["recomputed_total_step"]
HR = RS["holds"]["recomputed_here"]


def scen(letter, ceiling="factory+5pts", panels=False):
    s = SCN[(SCN.scenario.str.startswith(letter)) & (SCN.ceiling == ceiling) & (SCN.uti_panels_held == panels)]
    assert len(s) == 1
    return s.iloc[0]


A, B, C = scen("A"), scen("B"), scen("C")
B12 = scen("B", "12% max")
VB, VI = VAR["B_as_published"], VAR["B_iuk_exempt"]
assert abs(VB["uplift_above_proposal_eur"] - B.uplift_above_proposal_eur) < 2 and abs(VB["solver_t_pts"] - B.solver_t) < 1e-5
assert abs(VI["total_step_eur"] - STEP) < 2


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
cat_iuk_body = CATR[(CATR.market == "IUK") & (CATR.aim_l1 == "Accident & Body")].iloc[0]
maxpart = PART.loc[PART.proposal_move.idxmax()]
pads = PART[PART.padkit == 1]
pad794 = PART[PART.pn == "8982447940"].iloc[0]
pad922 = PART[PART.pn == "8982169220"].iloc[0]
held_lost_parts = int((PART.h_lost > 0).sum())
room_parts = int(((PART.proposal_move > PART.factory_move.clip(lower=0) * K * (1 - PART.h_lost) + 1e-4)
                  & (PART.padkit == 0)).sum())
fact15 = int((PART.factory_move > 0.15).sum())

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


def nice_ticks(vmax, n=5):
    import math
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw:
            step = m * mag
            break
    ticks, t = [], 0.0
    while t <= vmax * 1.0001 + 1e-12:
        ticks.append(t)
        t += step
    if ticks[-1] < vmax:
        ticks.append(ticks[-1] + step)
    return ticks


def svg_open(w, h, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{esc(label)}" '
            f'style="font-family:{FONT};display:block">')


def svg_hbar(rows, fmt, label, width=680, label_w=230, bar_h=20, gap=9, ref=None, vmax=None, value_w=86):
    """rows: (label, value, colour). Horizontal bars, value printed at the bar end (or inside if long)."""
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


def svg_bridge():
    """Proposal step -> holds -> ceiling cuts -> option B recovery -> result."""
    cut = float(B.cut_below_proposal_by_ceiling_eur)
    up = float(B.uplift_above_proposal_eur)
    cols = [("Proposal, all markets", 0, STEP, NAVY, e0(STEP)),
            ("Given up by the market holds", STEP - HOLDS, STEP, RED, "-" + e0(HOLDS)),
            ("Cut by the per-part ceiling (5 parts)", STEP - HOLDS - cut, STEP - HOLDS, RED, "-" + e0(cut)),
            ("Recovered on captive repair and body parts", STEP - HOLDS - cut, STEP, BLUE, "+" + e0(up)),
            ("Result: +5.00% on the book", 0, STEP, NAVY, e0(STEP))]
    w, h, left, top, bottom = 680, 230, 60, 22, 46
    plot_h = h - top - bottom
    vmax = 1_700_000
    sy = lambda v: top + plot_h * (1 - v / vmax)
    cw = (w - left - 10) / len(cols)
    o = [svg_open(w, h, "Bridge from the proposal to the decided option B")]
    for t in range(0, 1_600_001, 400_000):
        y = sy(t)
        o.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - 10}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{left - 6}" y="{y + 3.5:.1f}" font-size="10" fill="{MUTED}" text-anchor="end">{t / 1e6:.1f}M</text>')
    for i, (lab, lo, hi, col, val) in enumerate(cols):
        x = left + i * cw + cw * 0.2
        bw = cw * 0.6
        o.append(f'<rect x="{x:.1f}" y="{sy(hi):.1f}" width="{bw:.1f}" height="{max(sy(lo) - sy(hi), 1.5):.1f}" fill="{col}" rx="2"/>')
        o.append(f'<text x="{x + bw / 2:.1f}" y="{sy(hi) - 6:.1f}" font-size="11" font-weight="600" fill="{INK}" text-anchor="middle">{esc(val)}</text>')
        words, lines, cur = lab.split(), [], ""
        for wd in words:
            if len(cur + " " + wd) > 22 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for j, ln in enumerate(lines):
            o.append(f'<text x="{x + bw / 2:.1f}" y="{h - bottom + 14 + j * 11}" font-size="10" fill="{INK}" text-anchor="middle">{esc(ln)}</text>')
        if 0 < i < len(cols) - 1:
            pass
    o.append("</svg>")
    return "".join(o)


def svg_segments():
    rows = []
    for seg, lab in (("service", "Service parts"), ("repair", "Repair parts"), ("body", "Body and lighting")):
        b, p, billed = segavg("B", "segment", seg)
        rows.append((lab, p, b, billed))
    w, label_w, value_w = 680, 150, 70
    bar_h, gap_in, gap_out = 14, 2, 12
    top, bottom = 4, 26
    h = top + len(rows) * (2 * bar_h + gap_in + gap_out) + bottom
    vmax = 0.10
    plot_w = w - label_w - value_w
    sx = lambda v: label_w + plot_w * v / vmax
    o = [svg_open(w, h, "Average move by segment, proposal against option B")]
    for t in (0, 0.02, 0.04, 0.06, 0.08, 0.10):
        x = sx(t)
        o.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{GRID}"/>')
        o.append(f'<text x="{x:.1f}" y="{h - 8}" font-size="10" fill="{MUTED}" text-anchor="middle">{t * 100:.0f}%</text>')
    for i, (lab, p, b, billed) in enumerate(rows):
        y = top + i * (2 * bar_h + gap_in + gap_out)
        o.append(f'<text x="{label_w - 8}" y="{y + bar_h + 4}" font-size="11" fill="{INK}" text-anchor="end" font-weight="600">{esc(lab)}</text>')
        o.append(f'<text x="{label_w - 8}" y="{y + bar_h + 17}" font-size="9.5" fill="{MUTED}" text-anchor="end">{esc(em(billed, 1))} billed</text>')
        for j, (v, col, tag) in enumerate(((p, GREY, "proposal"), (b, BLUE, "option B"))):
            yy = y + j * (bar_h + gap_in)
            o.append(f'<rect x="{label_w}" y="{yy}" width="{max(sx(v) - label_w, 1):.1f}" height="{bar_h}" fill="{col}" rx="2"/>')
            o.append(f'<text x="{sx(v) + 6:.1f}" y="{yy + bar_h - 4}" font-size="10.5" fill="{INK}">{v * 100:.1f}% {tag}</text>')
    o.append("</svg>")
    return "".join(o)


NAME = {"IUK": "UK — IUK (D-Max)", "ITUK": "UK — ITUK (trucks)", "UTI": "Israel — UTI (trucks)",
        "UMI": "Israel — UMI (D-Max)", "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal",
        "NORWAY": "Norway", "SWEDEN": "Sweden", "IRELAND": "Ireland", "UKRAINE": "Ukraine", "GREECE": "Greece",
        "CYPRUS": "Cyprus", "HUNGARY": "Hungary", "FINLAND": "Finland", "ARMENIA": "Armenia (CIS)",
        "MALTA": "Malta", "ROMANIA": "Romania", "KAZAKHSTAN": "Kazakhstan (CIS)", "DENMARK": "Denmark",
        "ICELAND": "Iceland", "PALESTINE": "Palestine"}


def svg_markets(top_n=12):
    t = VMK.sort_values("billed_eur", ascending=False).head(top_n)
    w, label_w, tbl_w = 680, 150, 210
    row_h, top, bottom = 22, 22, 26
    h = top + len(t) * row_h + bottom
    plot_l, plot_r = label_w, w - tbl_w - 14
    vmax = 0.08
    sx = lambda v: plot_l + (plot_r - plot_l) * v / vmax
    o = [svg_open(w, h, "Average move by market: proposal, option B and option B with IUK exempted")]
    for v in (0, 0.02, 0.04, 0.06, 0.08):
        x = sx(v)
        o.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - bottom + 2}" stroke="{GRID}"/>')
        o.append(f'<text x="{x:.1f}" y="{h - 8}" font-size="10" fill="{MUTED}" text-anchor="middle">{v * 100:.0f}%</text>')
    cx = [w - tbl_w + 30, w - tbl_w + 100, w - tbl_w + 172]
    for x, lab in zip(cx, ("Proposal", "Option B", "B, IUK exempt")):
        o.append(f'<text x="{x}" y="{top - 8}" font-size="9.5" fill="{MUTED}" text-anchor="middle" font-weight="600">{lab}</text>')
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
            ("Any competitor evidence (number or price)", s["2_competitive_evidence_brief_definition"]["billed_pct"], RED, "insufficient to prove captive"),
            ("Aftermarket shop price", s["1_outside_prices_aftermarket_street_any_date"]["billed_pct"], AMBER, "partial: top sellers only"),
            ("Competitor part number, confirmed or likely", s["2_competitor_number_confirmed_likely"]["billed_pct"], RED, "thin")]
    w, label_w, value_w = 680, 250, 190
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
    # aftermarket below the line, genuine above
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
        held = 0.0
        pr = m.get("proposal", {})
        if d["service"].startswith("hold"):
            held += pr["service"]["step"]
        out.append(dict(k=k, billed=m["billed"].get("2025") or 0, fc=fc, fw=fw, s25=s25, ch=ch, sor=sor,
                        service=d["service"], body=d["body"], held=held))
    return out


def cls_fleet(v):
    return "na" if v is None else ("bad" if v <= 0 else "mid" if v < 0.1 else "good")


def grid_html():
    rows = grid_rows()
    hold_body = {"UMI": HR["UMI body/collision hold"]["step"] + HR["UMI lighting hold"]["step"],
                 "UTI": HR["UTI lighting hold"]["step"]}
    o = ["<table class='grid'><thead><tr><th>Market</th><th class='r'>Parts billed 2025</th><th class='r'>Fleet 2023→25</th>"
         "<th class='r'>Fleet 2026 forecast</th><th class='r'>Service share 2025</th><th class='r'>Change since 2023</th>"
         "<th class='r'>Pays vs list, stock orders</th><th>Service parts</th><th>Body and lighting</th><th class='r'>Step held</th></tr></thead><tbody>"]
    for r in rows:
        s25, ch = r["s25"], r["ch"]
        sk = "na" if s25 is None else ("bad" if s25 < NET * 0.8 else "mid" if s25 < NET * 1.2 else "good")
        stxt = "n/a" if s25 is None else ("over 100%*" if s25 > 1.0 else ("100%*" if s25 >= 0.995 else f"{s25 * 100:.0f}%"))
        ck = "na" if ch is None else ("bad" if ch < 0 else "mid" if ch < 0.05 else "good")
        fwk = "na" if r["fw"] is None else ("bad" if r["fw"] <= -0.03 else "mid" if r["fw"] < 0.03 else "good")
        held = r["held"] + hold_body.get(r["k"], 0.0)
        sor_txt = "n/a" if r["sor"] is None else f"{r['sor']:.1f}%"
        svc_cls = "hold" if r["service"].startswith("hold") else ("move" if r["service"] == "factory move" else "na")
        body_cls = "hold" if r["body"].startswith("hold") else ("move" if r["body"] == "factory move" else "na")
        svc_txt = "hold" if r["service"].startswith("hold") else r["service"]
        body_txt = {"hold body, collision and lighting": "hold body, collision, lighting", "hold lighting": "hold lighting"}.get(r["body"], r["body"])
        o.append("<tr>"
                 f"<td><b>{esc(NAME[r['k']])}</b></td><td class='r'>{em(r['billed'])}</td>"
                 f"<td class='r {cls_fleet(r['fc'])}'>{'n/a' if r['fc'] is None else p0(r['fc'], True)}</td>"
                 f"<td class='r {fwk}'>{'n/a' if r['fw'] is None else p0(r['fw'], True)}</td>"
                 f"<td class='r {sk}'>{stxt}</td>"
                 f"<td class='r {ck}'>{'n/a' if ch is None else f'{ch * 100:+.1f} pts'}</td>"
                 f"<td class='r'>{sor_txt}</td>"
                 f"<td class='{svc_cls}'>{esc(svc_txt)}</td><td class='{body_cls}'>{esc(body_txt)}</td>"
                 f"<td class='r'>{'' if held == 0 else ek(held)}</td></tr>")
    o.append("</tbody></table>")
    return "".join(o)


def holds_rows():
    rows = []
    for r in grid_rows():
        if r["held"] > 0:
            rows.append((f"{NAME[r['k']]}: service parts", r["held"], RED))
    rows += [("Israel — UMI: body and collision", HR["UMI body/collision hold"]["step"], AMBER),
             ("Israel — UTI: lighting", HR["UTI lighting hold"]["step"], AMBER),
             ("Israel — UMI: lighting", HR["UMI lighting hold"]["step"], AMBER)]
    return sorted(rows, key=lambda x: -x[1])


# ======================================================================= levers outside the price list
LV = LEV[~LEV.cis_untouched].copy()
gap_rows = LV.sort_values("a_stock_halve_gap_to_list_eur", ascending=False)
gap_rows = gap_rows[gap_rows.a_stock_halve_gap_to_list_eur >= 5000]

# ======================================================================= carried-over constants
# Origin: management deck v1.4 (20 Sep 2026), slides 4, 5, 6, 19, 22; pricing policy paper revision 3 (19 Sep),
# sections 2, 9-14; revision 1 (17 Sep) sections 4.4 and 4.7. All archived with this paper's predecessors.
CLASS_MARGINS = [("C", "53.0%"), ("D", "52.0%"), ("M", "50.0%"), ("F", "47.5%"), ("V", "45.0%"), ("J", "44.5%"),
                 ("P", "56.0%"), ("T", "20.0%")]

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
.callout{border-left:3px solid var(--terra);background:var(--paper);padding:3mm 4mm;margin:3mm 0;break-inside:avoid}
.callout.navy{border-left-color:var(--navy)}
.tag{display:inline-block;font-size:8.6px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:.6mm 2mm;border-radius:2px;margin-right:2mm;vertical-align:1px}
.tag.dec{background:#1a2b4a;color:#fff}.tag.sug{background:#eda100;color:#2a1d00}.tag.open{background:#e24b4a;color:#fff}
.tag.neg{background:#5b4a8a;color:#fff}.tag.next{background:#888780;color:#fff}.tag.pend{background:#fff;color:#c0552d;border:1px solid #c0552d}
table{width:100%;border-collapse:collapse;margin:2mm 0 3mm;font-size:9.4px;break-inside:avoid}
th{background:var(--navy);color:#fff;text-align:left;padding:1.6mm 2mm;font-size:8.6px;font-weight:600;vertical-align:bottom}
td{padding:1.4mm 2mm;border-bottom:.5px solid var(--line);vertical-align:top}
tbody tr:nth-child(even){background:var(--paper)}
tr{break-inside:avoid}
.r{text-align:right;white-space:nowrap}
table.grid{font-size:8.5px}table.grid td{padding:1.1mm 1.5mm}table.grid th{padding:1.3mm 1.5mm;font-size:8px}
td.good{background:#e3f2ec!important;color:#1f6b4c}td.mid{background:#fdf3dc!important;color:#7a5a00}td.bad{background:#fbe3e1!important;color:#9b2c2b}
td.hold{color:#9b2c2b;font-weight:600}td.move{color:#2b4a78}td.na{color:#888}
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
.placeholder{border:2px dashed var(--terra);background:#fff7f3;padding:5mm 5mm;margin:3mm 0;break-inside:avoid}
.negbox{border:2px solid #5b4a8a;background:#f5f3fa;padding:3mm 4mm;margin:3mm 0;break-inside:avoid}
.negbox b.h{color:#5b4a8a}
.two{display:flex;gap:5mm}.two>div{flex:1}
.small{font-size:9.2px}
.muted{color:var(--muted)}
.footer{display:none;position:fixed;bottom:0;left:0;right:0;font-size:7.6px;color:var(--muted);display:flex;justify-content:space-between;border-top:.5px solid var(--line);padding-top:1.2mm}
@media screen{body{background:#e9e6df}.wrap{background:#fff;padding:12mm 15mm 20mm;margin:0 auto;max-width:210mm}
  .cover{margin:-12mm -15mm 0;height:auto;min-height:262mm}.footer{display:none}}
@media screen and (max-width:700px){.wrap{padding:6mm 4mm}.cover{margin:-6mm -4mm 0;padding:14mm 8mm}.cards,.two{flex-direction:column}
  table{display:block;overflow-x:auto}}
"""


def section(no, title, body, src, pb=True):
    cls = " class='pb'" if pb else ""
    return (f"<section{cls}><h2 class='sec'><span class='no'>{no}</span>{esc(title)}</h2>{body}"
            f"<div class='src'><b>Sources.</b> {src}</div></section>")


def card(label, value, note, cls=""):
    return f"<div class='card {cls}'><div class='l'>{esc(label)}</div><div class='v'>{esc(value)}</div><div class='n'>{esc(note)}</div></div>"


seg_b = {s: segavg("B", "segment", s) for s in ("service", "repair", "body")}
vl_b = {s: segavg("B", "vehicle_line", s) for s in ("LCV (D-Max)", "Truck")}
uk = VMK.loc["UKRAINE"]
iuk = VMK.loc["IUK"]
held_share = HOLDS / STEP
umi_service_step = MF["markets"]["UMI"]["proposal"]["service"]["step"]
umi_service_billed = MF["markets"]["UMI"]["proposal"]["service"]["billed"]
iuk_rb_uplift = VB["uplift_on_iuk_repair_body_eur"]

S = []

# ---------------------------------------------------------------- cover
S.append(f"""
<div class='cover'>
 <div class='kicker'>Isuzu Motors Europe · Parts pricing · Management</div>
 <h1>Parts pricing policy</h1>
 <div class='sub'>The +5% price revision by part number, market by market, and where the money comes from</div>
 <div class='rule'></div>
 <div class='meta'>2 October 2026<br>Consolidated paper: replaces the pricing policy papers of 17 and 19 September 2026 and the management decks v1.0 to v1.4<br>
 Decisions recorded up to 2 October 2026</div>
 <div class='toc'>
  <div><b>1</b>Summary and decisions</div><div><b>2</b>How a price is set today, and what changes</div>
  <div><b>3</b>The +5% proposal by part number</div><div><b>4</b>Market by market: the 21-market exercise</div>
  <div><b>5</b>Where the +5% comes from: option B</div><div><b>6</b>The IUK risk, and a suggested variant</div>
  <div><b>7</b>Outside price evidence: what it can carry</div><div><b>8</b>Collision, insurance and lighting in Israel</div>
  <div><b>9</b>Order terms: a negotiation topic</div><div><b>10</b>P700 and the next price list</div>
  <div><b>11</b>UTI truck panels: no hold, availability first</div><div><b>12</b>Background that still stands</div>
  <div><b>13</b>Open points and next steps</div><div><b>A</b>Terms and source register</div>
 </div>
 <div class='status'>Status: a proposal on paper. Nothing in this document changes a price, the price list or a distributor condition.
 Labels used throughout: <b>decided</b> (management decision taken), <b>suggested, not decided</b>, <b>open</b>, <b>negotiation topic</b>, <b>next price list</b>.</div>
</div>""")

# ---------------------------------------------------------------- 1 summary
S.append(section("1", "Summary and decisions", f"""
<p class='lead'>The price list rises by <b>+5.00%</b> on parts billed: {e0(STEP)} on {e0(BASE)} of parts billed between July 2025 and June 2026.
Every part moves with its own factory base-price change, scaled so that the book lands exactly on +5%. Twenty-one markets were then read one by one;
in eight of them service parts are held at today's price, and in Israel body, collision and lighting parts are held as well. Those holds give up
<b>{e0(HOLDS)}</b> ({p1(held_share)} of the step). The decision is to recover that amount on <b>captive repair and body parts</b> &mdash; parts where no competitor
has been found &mdash; and not on service parts.</p>
<div class='cards'>
 {card("Step on the book", e0(STEP), "+5.00% on " + em(BASE, 1) + " parts billed")}
 {card("Given up by the market holds", e0(HOLDS), p1(held_share) + " of the step, 8 service holds + Israel body/lighting", "terra")}
 {card("Option B: extra on captive repair and body", f"+{B.solver_t * 100:.1f} pts", f"{int(B.weighted_parts):,} parts, {em(B.weighted_base_eur, 1)} billed; nothing extra on service", "blue")}
 {card("Average move after option B", f"{B.avg_move_on_free_lines * 100:.2f}%", "on lines not held; book stays at +5.00%")}
</div>
<table>
<thead><tr><th style='width:23%'>Status</th><th>Item</th></tr></thead><tbody>
<tr><td><span class='tag dec'>Decided</span></td><td><b>Factory-led +5% by part number</b> (29 September): each part follows its own factory base-price change, times {K:.3f}, landing on +5.00%.</td></tr>
<tr><td><span class='tag dec'>Decided</span></td><td><b>All {len(pads)} brake pad kits stay at today's price</b> (30 September), {e0(pads.billed_eur_l12m.sum())} billed. This includes front pad kit 8982447940, which the 29 September draft would have raised by 17%.</td></tr>
<tr><td><span class='tag dec'>Decided</span></td><td><b>The 21-market holds</b> (30 September), including the UMI lighting hold, which is now counted ({e0(HR['UMI lighting hold']['step'])} of step).</td></tr>
<tr><td><span class='tag dec'>Decided</span></td><td><b>Option B</b> (2 October): the {ek(HOLDS)} is recovered on captive repair and body parts at about +{B.solver_t * 100:.1f} points on top of their proposal move. Service parts carry nothing extra.</td></tr>
<tr><td><span class='tag sug'>Suggested, not decided</span></td><td><b>Option B with IUK exempted</b>: keep UK D-Max (IUK) repair and body parts at their proposal move, because IUK is the only market where dealers measurably bought less after the April rise. The other markets then carry +{VI['solver_t_pts'] * 100:.1f} points instead of +{B.solver_t * 100:.1f}. Section 6.</td></tr>
<tr><td><span class='tag dec'>Decided</span></td><td><b>Ukraine buys on the main price list</b>, so it takes the normal increase like every market outside Armenia and Kazakhstan (as in option B).</td></tr>
<tr><td><span class='tag open'>Open</span></td><td><b>UMI leasing share</b>: unknown, and not being requested now; UMI's service hold stays until it is known. Section 13.</td></tr>
<tr><td><span class='tag dec'>Decided</span></td><td><b>UTI truck panels are not held</b> (2 October): they take the normal step. The issue is availability, addressed by stocking P700 panels against UTI's forecast. Section 11.</td></tr>
<tr><td><span class='tag neg'>Negotiation topic</span></td><td><b>Order terms</b> (stock-order discount, gap to list, rush and vehicle-off-road surcharge): of the same order of size as the holds, but a condition negotiated per distributor, <b>not a price list change</b>. Section 9.</td></tr>
<tr><td><span class='tag next'>Next price list</span></td><td><b>P700 new parts</b>: they have almost no billing yet, so they need a first price on the next list rather than an increase now. Section 10.</td></tr>
</tbody></table>
<div class='callout'><b>What the evidence can and cannot carry.</b> Order lines, order types and the D-Max/truck split cover 98&ndash;100% of the euro and are sound.
Outside prices are thinner: an aftermarket shop price exists for {SUF['1_outside_prices_aftermarket_street_any_date']['parts']} parts ({p1(SUF['1_outside_prices_aftermarket_street_any_date']['billed_pct'])} of parts billed),
and a competitor part number for {SUF['2_competitor_number_confirmed_likely']['parts']} parts. "Captive" therefore mostly means <b>no competitor found</b>, not competition proven absent.
Where we do have aftermarket prices, they sit at a median {IDX['aftermarket_street']['median']:.2f}x our reference dealer price. Option B is the cleanest allocation of the euro; it is not
evidence that those parts can bear more. Section 7.</div>
""", "the +5% proposal of 29&ndash;30 September 2026 (summary of the part-number build); the 21-market exercise of 30 September 2026 and its decision record; "
     "the room-to-raise scan of 2 October 2026 (inputs: approved parts classification release of 2 October, price observation ledger as of 2 October, "
     "graded competitor cross-references, SAP parts billing July 2025&ndash;June 2026). Decisions as recorded on 29 September, 30 September and 2 October 2026.", pb=True))

# ---------------------------------------------------------------- 2 how a price is set
cls_rows = "".join(f"<tr><td>Class {c}</td><td class='r'>{m}</td></tr>" for c, m in CLASS_MARGINS)
S.append(section("2", "How a price is set today, and what changes", f"""
<p>Our selling price is built from the factory's yen base price, converted at the corporate exchange rate, reduced by our purchase discount, and divided by
one minus the <b>class margin</b>. The class is a letter the factory (Isuzu Motors Limited, IML) assigns to each part, and the letter alone sets the margin.
Nothing about the part's competition, market or demand enters the formula.</p>
<div class='two'>
<div>
<table><thead><tr><th>Price class</th><th class='r'>Formula margin</th></tr></thead><tbody>{cls_rows}</tbody></table>
</div>
<div>
<div class='cards' style='flex-direction:column;margin-top:2mm'>
{card("Classed part numbers in class C", "74.9%", "206,598 of 275,992; one 53% margin across very different parts")}
{card("Book margin, priced in-scope lines", "51.09%", "EUR 15.15M gross profit on EUR 29.65M billed; 84.3% of the book earns between 45% and 56%")}
</div></div></div>
<h3>Purchase terms and exchange rate</h3>
<p>From 5 January 2026 the Japan purchase discount fell from 38.0% to 32.7% (we now pay 67.3% of the yen base instead of 62.0%); Thailand is unchanged at 38.9%.
The weaker yen largely offsets it. For an unchanged base of JPY 16,370, the formula cost is <b>EUR 62.00</b> on the October 2025 list basis (163.7 JPY/EUR),
<b>EUR 63.83</b> in April&ndash;September 2026 (172.6) and <b>EUR 61.72</b> at the rate announced for October 2026 to March 2027 (178.5): &minus;0.45% against the list basis.
The exchange rate moves the euro price and the euro gross profit; it never moves the margin percentage. Whether the announced rate also applies to Thailand-sourced parts is to be confirmed.</p>
<h3>Principles agreed in September, still standing</h3>
<ul class='tight'>
<li><b>Replace the automatic class margin</b> with part-by-part decisions: reduce selectively where a credible competing offer leaves the distributor too little room, hold where the position is right, increase selectively where a genuine advantage supports it.</li>
<li><b>No universal 8% ceiling</b> on a part's move. Larger moves need evidence and approval. (The +5% revision uses a per-part ceiling of the part's own factory move plus 5 points; section 5.)</li>
<li><b>Parts identity is live</b>: every part sits in a three-level product tree (family, subgroup, part type), anchored on the factory catalogue. The tree identifies the part; market evidence guides the price.</li>
<li><b>Class T prices (20% formula margin) stay unchanged.</b></li>
<li><b>How a price is approved</b>: compare the alternative offer (product, quality, date, availability, price level); allow distributor and dealer room; check our net economics (cost, exchange rate, selling support); record the evidence, the commercial purpose and the expected result.</li>
<li><b>Every priced line carries a reason</b>, and separates our decision from a change passed through from the factory (a base-price correction, a part out of production). The revision should also state its own effect on parts billed per truck in service, split into price, volume, mix and fleet, so that next year's increase is not read as an improvement.</li>
</ul>
<p class='small muted'>Two reminders on the arithmetic of a cut: a 5% lower net price needs about 11% more volume to keep gross profit at a 50% margin (an illustration, not a forecast);
and a reported internal precedent &mdash; a battery-electric vehicle battery priced at about 1% margin to answer an insurance-cost concern &mdash; shows that an exception can serve the wider vehicle offer. The battery case is management-reported and not verified here.</p>
""", "price class margins and the 74.9% class C share: 2026 price file (snapshot 9 August 2026); book margin: priced in-scope lines July 2025&ndash;June 2026, as measured on 19 September 2026; "
     "purchase discount and exchange rates: supplier notice of 22 December 2025 and the corporate rate notifications, as recorded in the management deck of 20 September 2026; "
     "agreed principles: management deck v1.4, appendix D (policy status, 20 September 2026); reason-code and per-truck principles: pricing policy paper of 17 September 2026."))

# ---------------------------------------------------------------- 3 the proposal
S.append(section("3", "The +5% proposal by part number", f"""
<p>The factory's new base prices (September 2026 against September 2025) move the book by <b>+{PSUM['recipe_check'] * 100:.2f}%</b> on billed volume. The proposal passes on
<b>{K:.3f}</b> of each part's own move, so that the book lands on exactly <b>+5.00%</b> ({e0(STEP)}). One list price per part; no market sees a different list.</p>
<div class='cards'>
 {card("Typical part (median)", p1(PSUM['median_move'], True), "9 in 10 parts move by +" + p1(PSUM['p90_move']) + " or less")}
 {card("Parts held at 0%", f"{PSUM['parts_at_zero']:,}", em(PSUM['eur_at_zero']) + " billed: pad kits, no factory rise, or lost categories")}
 {card("Parts with a factory move above 15%", f"{fact15}", "reviewed individually; the largest move is " + p0(maxpart.proposal_move, True))}
 {card("Margin effect", f"{PSUM['margin_pts_proposal'] * 100:+.1f} pts", "weighted class margin, at today's rate and purchase terms")}
</div>
<h3>Three rules on top of the factory move</h3>
<ol class='tight'>
<li><b>Brake pad kits stay at today's price.</b> {len(pads)} kits, {e0(pads.billed_eur_l12m.sum())} billed. Two kits carry large factory moves: 8982447940 ({p1(pad794.factory_move, True)}) and 8982169220 ({p1(pad922.factory_move, True)}).
 At an unchanged price their class margin falls from 45% to about 31&ndash;33%. Kit 8982447940 is the front pad kit bought mainly by ITUK and UTI; the 29 September draft had it at +17.0%. Holding it answers the leading dealer complaint in the UK truck network.</li>
<li><b>Held at 0% where the distributor already loses the category</b>: on lines where a distributor sells under 45% of what its trucks need in that category ({held_lost_parts} part numbers affected).</li>
<li><b>A small extra on {room_parts} parts</b> where a UK trade web shop sells the same part number dearer than our reference dealer price, capped at the evidence limit.</li>
</ol>
<h3>What dealers did after the April 2026 rise</h3>
<p>The April 2026 list change (median +{inv['median_list_change'] * 100:.1f}%, confirmed on UK truck invoices at +{inv['median_invoice_change'] * 100:.1f}%) gives the first usable test of how dealers react.
Pooled over UK trucks, UK D-Max, Ireland and Portugal, a part that rose 1% more than similar parts sold {abs(r_pool['beta_dlp']):.2f}% fewer units (standard error {r_pool['se_dlp']:.2f}):
statistically indistinguishable from no reaction. It is not precise enough to set prices part by part and is used only for volume scenarios.
<b>UK D-Max (IUK) is the exception</b>: {r_iuk['beta_dlp']:.2f} (&plusmn;{1.96 * r_iuk['se_dlp']:.2f}), and its dealer units fell {abs(iuk_units) * 100:.1f}% over the same months.</p>
<p>On the proposal as built on 29&ndash;30 September (before the market holds), the step of {em(STEP)} becomes about <b>{em(PSUM['revenue_central'])}</b> if the pooled reaction holds,
and {em(PSUM['revenue_stress'])} in a pessimistic case using the lowest 95% bound of the measurements. The pessimistic case is a stress test, not a forecast.</p>
<h3>Four live front pad kits, one function</h3>
<p>Four front pad kits share one description at four list prices: 8975056801 and 8975546610 at EUR 82.25, 8982447940 at EUR 89.11, 8982169210 at EUR 102.65 &mdash; a 25% spread &mdash;
and each network buys almost only its own (IUK the cheapest, ITUK and UTI the two dearest). None is superseded by another. Whether they are interchangeable is a catalogue question that is still open (section 13).</p>
""", "the +5% proposal of 29&ndash;30 September 2026: factory base prices of September 2026 against September 2025, parts billed July 2025&ndash;June 2026 (15,273 part numbers), "
     "measured distributor shares of need by category; dealer response: sales-to-dealer monthly files for UK trucks (2023&ndash;2026), UK D-Max, Ireland and Portugal (2025&ndash;2026) against the dated list changes, "
     "with an invoice check on UK truck billing; pad-kit list prices and buying networks: 2026 price file and billing, as reported on 19 September 2026."))

# ---------------------------------------------------------------- 4 market exercise
S.append(section("4", "Market by market: the 21-market exercise", f"""
<p>Each market was read on the same evidence: what it buys, how its fleet moves, how much of its service work we win (the <b>service share</b>: service parts its distributor
bought against what its fleet should need at the service intervals; network {NET * 100:.0f}% in 2025), what it pays against our list, and what dealers and distributors say.
The list stays one price per part; a hold is applied as a <b>distributor condition</b> on that part group, the way stock-order and customer conditions already differ today.</p>
<div class='callout navy'><b>Rules behind a service hold.</b> Imported vehicles we do not count buy in the market; or dealers measurably reacted to the April 2026 rise; or the fleet is flat
or shrinking while our service share is below the network or falling; or a documented price complaint on service parts together with a low or falling share.
Repair parts follow their factory move in every market. Israel adds collision and lighting, because of the insurance total-loss rule (section 8). Armenia and Kazakhstan (CIS) are left to their proposal move.</div>
<div class='fig'><div class='ttl'>Who gives up what: the euro of step held, by market and part group</div>
{svg_hbar(holds_rows(), lambda v, ax: (f"{v / 1e3:.0f}k" if ax else ek(v)), "Step held by market and part group", label_w=250, value_w=70)}
</div>
<p class='small'>Total held: <b>{e0(HOLDS)}</b>. The exercise published {e0(DEC['held_step'])}; the difference of {e0(HOLDS - DEC['held_step'])} is the UMI lighting hold,
which the exercise named but did not count and which is now kept. Holding service parts in UK D-Max alone gives up {ek(MF['markets']['IUK']['proposal']['service']['step'])}, the largest single item.</p>

""", "the 21-market exercise of 30 September 2026: SAP parts billing 2023&ndash;August 2026, the in-scope revision base, dated main-list price files, the service-share measure by market and category, "
     "fleet planning estimates (July 2026, corrected 2026 column), sales-to-dealer files for the UK, Ireland and Portugal, distributor review minutes July&ndash;August 2026, IMIE monthly market packs; "
     "Israel holds recomputed in the room-to-raise scan of 2 October 2026."))

S.append(f"""<section class='pb'><h3 style='margin-top:0'>The 21 markets on one page</h3>{grid_html()}
<p class='small muted'>Colours: fleet red = flat or shrinking; service share red = below 80% of the network; change red = falling. * More than the counted fleet should need: vehicles we do not count buy here; not a real share.
Step held = the proposal euro given up on the held part groups (service holds from the exercise; Israel body and lighting recomputed on the approved classification).</p>
<div class='src'><b>Sources.</b> as for section 4.</div></section>""")

# ---------------------------------------------------------------- 5 option B
S.append(section("5", "Where the +5% comes from: option B", f"""
<p class='lead'><span class='tag dec'>Decided</span> The {ek(HOLDS)} given up by the holds is recovered on <b>captive repair and body parts</b>: about <b>+{B.solver_t * 100:.1f} points</b>
on top of their proposal move, on {int(B.weighted_parts):,} parts ({em(B.weighted_base_eur, 1)} billed on lines that are not held). Service parts carry nothing extra. Armenia and Kazakhstan keep their proposal move.</p>
<div class='fig'><div class='ttl'>From the proposal to option B: the book stays at +5.00%</div>{svg_bridge()}</div>
<p class='small'>Ceiling per part: its own factory move plus 5 points. Five proposal moves exceed it and are cut by {e0(B.cut_below_proposal_by_ceiling_eur)}, recovered as well (uplift {e0(B.uplift_above_proposal_eur)});
{int(B.parts_at_ceiling)} parts reach it ({ek(B.billed_at_ceiling_eur)} billed). Largest single move: {p0(B.max_move, True)}, on a part whose factory price more than doubled.</p>
<h3>What it does to each segment</h3>
<div class='fig'>{svg_segments()}</div>
<p>Averages over all lines, held lines included. Service parts fall from {p1(seg_b['service'][1])} in the proposal to {p1(seg_b['service'][0])}, because they carry the holds and nothing extra;
repair parts rise from {p1(seg_b['repair'][1])} to {p1(seg_b['repair'][0])} and body parts from {p1(seg_b['body'][1])} to {p1(seg_b['body'][0])}. A typical captive repair or body part moves about 10% instead of about 6.3%.
Because the holds sit mostly on D-Max markets, D-Max parts average {p1(vl_b['LCV (D-Max)'][0])} and truck parts {p1(vl_b['Truck'][0])} (proposal {p1(vl_b['LCV (D-Max)'][1])} and {p1(vl_b['Truck'][1])}).</p>
<h3>Why option B and not the others</h3>
<table><thead><tr><th></th><th>A: rest of book, proportionally</th><th>B: captive repair and body (decided)</th><th>C: room score</th></tr></thead><tbody>
<tr><td>How</td><td>every free part x{1 + A.solver_t:.2f} of its proposal move</td><td>+{B.solver_t * 100:.1f} pts on {int(B.weighted_parts):,} captive repair and body parts</td><td>+{C.solver_t * 100:.1f} pts per room-score point on {int(C.weighted_parts):,} parts</td></tr>
<tr><td>Uplift on service / repair / body</td><td class='r'>{ek(A.uplift_service_eur)} / {ek(A.uplift_repair_eur)} / {ek(A.uplift_body_eur)}</td><td class='r'><b>0</b> / {ek(B.uplift_repair_eur)} / {ek(B.uplift_body_eur)}</td><td class='r'>{ek(C.uplift_service_eur)} / {ek(C.uplift_repair_eur)} / {ek(C.uplift_body_eur)}</td></tr>
<tr><td>Share of uplift on parts with no competitor found</td><td class='r'>{p0(A.uplift_on_captive_strict_pct)}</td><td class='r'><b>{p0(B.uplift_on_captive_strict_pct)}</b></td><td class='r'>{p0(C.uplift_on_captive_strict_pct)}</td></tr>
<tr><td>Parts at the ceiling (factory move + 5 pts)</td><td class='r'>{int(A.parts_at_ceiling)}</td><td class='r'><b>{int(B.parts_at_ceiling)}</b></td><td class='r'>{int(C.parts_at_ceiling)}</td></tr>
<tr><td>Typical (median) part move</td><td class='r'>{p1(A.median_move_free_parts)}</td><td class='r'>{p1(B.median_move_free_parts)}</td><td class='r'>{p1(C.median_move_free_parts)}</td></tr>
</tbody></table>
<p>Option B moves no service part beyond its proposal move &mdash; which is where the complaints and the holds are &mdash; the ceiling barely binds, and all of the extra lands on parts with no competitor evidence.
Option A pushes hardest on parts whose factory price already jumped. Option C depends on a room score that is a choice, not a measurement, and is driven mostly by "captive", slow movers and urgent-order share because the outside prices are thin.
All three land on exactly {e0(STEP)}. With a flat 12% ceiling instead, option B would leave {int(B12.parts_at_ceiling)} parts at the ceiling.</p>
""", "room-to-raise scan of 2 October 2026: one list move per part on the lines not held by the market exercise; segments from the approved parts classification release of 2 October 2026 "
     "(body = Accident &amp; Body; service = maintenance-service categories; repair = the rest); captive = no confirmed or likely competitor number, no aftermarket price observed, no cheaper Isuzu value-line alternative, "
     "not in the competitive-parts family, and not measured as a category the distributor loses; D-Max/truck split from vehicle-family bands, the August 2026 parts lists and who buys the part."))

# ---------------------------------------------------------------- 6 IUK risk
S.append(section("6", "The IUK risk, and a suggested variant", f"""
<p><b>IUK (UK D-Max) is the one market where dealers measurably bought less after the April 2026 rise</b>: {r_iuk['beta_dlp']:.2f} (&plusmn;{1.96 * r_iuk['se_dlp']:.2f}), dealer units {p1(iuk_units, True)}
over April&ndash;July against the same months of 2025. Only its service parts are held. Option B puts <b>{ek(iuk_rb_uplift)}</b> of extra on IUK repair and body parts. And the IUK body parts
that rose in April fell {abs(cat_iuk_body.median_rel_change_pct) * 100:.1f}% against IUK's own median, on {int(cat_iuk_body.parts)} parts &mdash; a noise-level reading, but it points at exactly the parts option B raises.
The UK D-Max market is also under pressure from outside: the double-cab benefit-in-kind change of April 2025, and pickup registrations down 61.2% year on year in August 2026.</p>
<div class='callout' style='border-left-color:#eda100'><span class='tag sug'>Suggested, not decided</span> <b>Option B with IUK exempted.</b> IUK repair and body lines keep their proposal move
(through the same distributor-condition mechanism as the holds); the recovery is spread over captive repair and body parts in the other markets.
The book still lands on {e0(VI['total_step_eur'])}; captive repair and body parts outside IUK carry <b>+{VI['solver_t_pts'] * 100:.1f} points</b> instead of +{B.solver_t * 100:.1f}.
IUK averages {p1(iuk.B_iuk_exempt_avg_move)} instead of {p1(iuk.B_avg_move)} (proposal {p1(iuk.proposal_avg_move)}). Parts at the ceiling stay at {VI['parts_at_ceiling']}; the typical moved part rises to about {p1(VI['median_move_flex_parts'])}.</div>
<div class='fig'><div class='ttl'>Average move by market, all lines, the twelve largest markets</div>
<div class='legend'><i style='background:{GREY}'></i>Proposal (before holds)<i style='background:{BLUE}'></i>Option B (decided)<i class='sq' style='background:{AMBER}'></i>Option B with IUK exempted (suggested)</div>
{svg_markets(12)}</div>
<p class='small'>Averages include held lines at 0%, which is why the hold markets sit below +5%. The other markets carry the IUK relief: UK trucks (ITUK) {p1(VMK.loc['ITUK'].B_avg_move)} to {p1(VMK.loc['ITUK'].B_iuk_exempt_avg_move)},
UTI {p1(VMK.loc['UTI'].B_avg_move)} to {p1(VMK.loc['UTI'].B_iuk_exempt_avg_move)}, Germany {p1(VMK.loc['GERMANY'].B_avg_move)} to {p1(VMK.loc['GERMANY'].B_iuk_exempt_avg_move)}. The trade-off is {ek(iuk_rb_uplift)} moved from the market that showed a reaction to markets that did not.</p>
""", "dealer response: sales-to-dealer files UK D-Max April&ndash;July 2025 against 2026, within-family estimate against the April 2026 list change; category reading: IUK parts with a rise of 3% or more, "
     "against IUK's own median; variant: the room-to-raise scan re-run on 2 October 2026 with IUK repair and body lines kept at the proposal move (option B reproduced exactly before the variant was computed); "
     "UK market: HMRC benefit-in-kind guidance (April 2025) and SMMT registrations, as reported on 19 September 2026."))

# ---------------------------------------------------------------- 7 evidence
am, gg = IDX["aftermarket_street"], IDX["genuine_grey"]
src_gg = RS["genuine_grey_sources_parts"]
S.append(section("7", "Outside price evidence: what it can carry", f"""
<p>An outside price is compared with our <b>reference dealer price</b>: the price list x 2.19, standing for what a dealer customer pays at the counter after distributor and dealer margins.
<b>The x2.19 basis is provisional</b> (set on 2 October 2026). The September papers used x1.785 (distributor x1.40, dealer x1.275); their ratios are not comparable with the ones below and are not carried over.
The <b>index</b> is the outside price, without VAT, divided by our reference dealer price: below 1.0 the outside seller is cheaper than us.</p>
<div class='fig'><div class='ttl'>Outside prices against our reference dealer price (median per part)</div>{svg_index_line()}</div>
<div class='two'>
<div><h3>Aftermarket brands: cheaper than us</h3>
<p>{am['parts']} parts carry an aftermarket shop price, {p1(SUF['1_outside_prices_aftermarket_street_any_date']['billed_pct'])} of parts billed. Median index <b>{am['median']:.2f}x</b>
(euro-weighted {am['billed_weighted_median']:.2f}x). {am['parts_below_0_8']} of them, {em(am['billed_below_0_8'], 1)} billed, sit below 0.8x; only {am['parts_at_or_above_1']} parts ({em(am['billed_at_or_above_1'])}) have a rival dearer than us.
The data mostly names parts to hold, not parts to raise.</p></div>
<div><h3>Genuine sold outside our network: dearer than us</h3>
<p>{gg['parts']:,} parts carry a price for genuine Isuzu parts sold outside our network, {p1(SUF['1_outside_prices_genuine_grey']['billed_pct'])} of parts billed. Median index <b>{gg['median']:.2f}x</b>;
on {gg['parts_at_or_above_1']:,} parts ({em(gg['billed_at_or_above_1'], 1)} billed) it is at or above our reference dealer price. <b>This rests mostly on one source</b>: an exporter's retail prices
({src_gg.get('amayama', 0):,} of the {gg['parts']:,} parts), and on the provisional x2.19 basis.</p></div>
</div>
<h3>Is the data good enough?</h3>
<div class='fig'>{svg_coverage()}</div>
<ul class='tight'>
<li><b>"Captive" is mostly absence of evidence.</b> {p0(SUF['2_captive_strict']['parts_pct'])} of parts ({p0(SUF['2_captive_strict']['billed_pct'])} of the euro) pass the strict captive test; only {SUF['2_competitive_evidence_brief_definition']['parts']} parts have any competitor evidence at all.
Body parts look almost entirely captive, but pattern (non-genuine) body parts have simply not been searched. A pattern-part price check on the top 50 body parts would show whether option B's body set holds.</li>
<li><b>A part has a price range, not one aftermarket price.</b> Front pad kit 8975546610 (list EUR 82.25) appears in 42 online listings in March 2026, from EUR 17.09 to EUR 213.40, median EUR 58.09, across very different brands and transaction levels.</li>
<li><b>We do not hold distributor or dealer resale prices</b> and will not obtain them. Every dealer-level figure is constructed. Whether a distributor passes a change in our price on to its dealers is unknown and can only be answered by asking.</li>
<li><b>Israel is not a discount channel.</b> Of the Israeli shop lines checked in September, none sat below a distributor purchase floor; the cheapest was 2.4x its floor. Parallel trade inside the EEA is lawful and cannot be closed by agreement.</li>
</ul>
""", "price observation ledger as of 2 October 2026 (aftermarket web shops, brand recommended retail prices, genuine parts sold outside the network; VAT stripped, median per part, last 12 months first); "
     "graded competitor cross-references with brand aliases and a second independent source (2 October 2026); approved parts classification release of 2 October 2026; pad kit price range: Eucon/PartsPool batch of 29 March 2026; "
     "Israel shop check: shop sweep of 18 September 2026 against distributor purchase floors."))

# ---------------------------------------------------------------- 8 collision
S.append(section("8", "Collision, insurance and lighting in Israel", f"""
<p>In Israel a vehicle is declared a total loss when damage reaches 60% of its pre-accident value, and the insurer may settle as a constructive total loss from 50&ndash;55% (two policy readings differ).
The repair estimate is built from our parts list prices. A high parts line can therefore push a repairable vehicle over the threshold and lose the whole repair &mdash; and, for a fleet on a repair-and-maintenance contract,
the parts for the remaining contract years. Routine service parts are not affected.</p>
<ul class='tight'>
<li><b>The thresholds were verified in the policy for vehicles up to 3.5 tonnes</b> &mdash; which covers the D-Max (UMI). The clause for heavier vehicles was not found, so for UTI's trucks the exposure is unverified.</li>
<li>The same policy allows a light to be replaced by a part of "similar description or characteristic", and requires new or genuine parts only for vehicles up to two years old.</li>
<li>UTI's July 2026 presentation shows the collision package rising from EUR 679 to EUR 2,144 (N 7.5 t) and EUR 924 to EUR 2,314 (F 10 t) between the old model and the P700; a rear light +1,228%;
the bumper split from one part at EUR 143.37 into four at EUR 320.00. Part of the lamp gap may be a different lamp rather than a list increase. UTI runs 1,700 trucks on five-year repair-and-maintenance contracts.</li>
<li>UTI lighting is EUR 133,667 of billing (3.9% of UTI's parts book), already 74% in the lowest-margin class (47.5%).</li>
</ul>
<div class='callout navy'><span class='tag dec'>Decided</span> UMI holds body, collision and lighting at today's price ({ek(HR['UMI body/collision hold']['step'] + HR['UMI lighting hold']['step'])} of step);
UTI holds lighting ({ek(HR['UTI lighting hold']['step'])}). This replaces the September proposal to give lighting a smaller share of the increase than bodywork.
Beyond price, two levers remain: the bumper and grille packaging on the P700, which is a question for IML, and a paid-on-genuine-use arrangement with insurers &mdash; in 2018 a funded rebate to the insurer, split equally between IML and ISZE, was proposed for exactly this case.</div>
""", "Israeli motor policy wordings for vehicles up to 3.5 tonnes, read 19 September 2026; UTI presentation, July 2026 (pages 8, 27, 30, 31); UTI lighting and collision billing, last twelve months to September 2026; "
     "2018 correspondence on an insurer rebate, as carried in the research paper of 19 September 2026 (reported, not re-verified); holds: the 21-market exercise and the room-to-raise scan."))

# ---------------------------------------------------------------- 9 order terms
lever_rows = [("Halve each market's gap to list on stock orders", L4["stock_halve_gap_eur"], "#5b4a8a"),
              ("Narrow the stock-order discount by 1 point", L4["stock_narrow_1pt_eur"], "#5b4a8a"),
              ("Rush and vehicle-off-road surcharge +2 points", L4["urgent_plus2pt_eur"], "#8f7fc0"),
              ("Rush and vehicle-off-road surcharge +1 point", L4["urgent_plus1pt_eur"], "#8f7fc0")]
gap_bar = [(NAME.get(k, k.title()) + f" (pays {r.SOR_pays_pct_list * 100:.1f}%)", r.a_stock_halve_gap_to_list_eur, "#5b4a8a")
           for k, r in gap_rows.iterrows()]
S.append(section("9", "Order terms: a negotiation topic", f"""
<div class='negbox'><b class='h'>NEGOTIATION TOPIC &mdash; NOT A PRICE LIST CHANGE.</b> Everything in this section is a distributor condition: what a distributor pays against the list on stock orders,
and what it pays on rush and vehicle-off-road orders. None of it changes a list price, and none of it is part of the +5% revision.</div>
<p>On stock orders most markets pay 99&ndash;100% of list, but several pay less through customer conditions: UTI {LV.loc['UTI'].SOR_pays_pct_list * 100:.1f}%, UMI {LV.loc['UMI'].SOR_pays_pct_list * 100:.1f}%,
Norway {LV.loc['NORWAY'].SOR_pays_pct_list * 100:.1f}%, ITUK {LV.loc['ITUK'].SOR_pays_pct_list * 100:.1f}%, IUK {LV.loc['IUK'].SOR_pays_pct_list * 100:.1f}%. Rush and vehicle-off-road orders are billed above list in most markets.
Valued on calendar-2025 order lines at the 2025 list (Armenia and Kazakhstan left out):</p>
<div class='fig'><div class='ttl'>What each order-terms lever is worth a year, against the euro given up by the holds</div>
{svg_hbar(lever_rows, lambda v, ax: (f"{v / 1e3:.0f}k" if ax else ek(v)), "Order-terms levers", label_w=260, value_w=70, ref=(HOLDS, "holds " + ek(HOLDS)), vmax=500_000)}</div>
<div class='fig'><div class='ttl'>Halving the gap to list on stock orders, by market</div>
{svg_hbar(gap_bar, lambda v, ax: (f"{v / 1e3:.0f}k" if ax else ek(v)), "Halving the gap to list by market", label_w=260, value_w=70)}</div>
<p>Narrowing the stock-order discount by 1 point everywhere is worth {ek(L4['stock_narrow_1pt_eur'])}, of which {ek(L4['stock_narrow_1pt_eur_excl_service_hold_markets'])} in markets without a service hold.
The rush and vehicle-off-road lever sits on {em(L4['urgent_list_value'])} of urgent list value. The constraints are real: UTI's and UMI's levels are negotiated customer conditions,
and UMI and IUK are markets where service parts are being held. These are items for the distributor negotiations, to be decided separately from the price list.</p>
""", "SAP parts billing, calendar year 2025, by order type (stock, rush, vehicle-off-road), valued at the 2025 main-list price per part; Armenia and Kazakhstan excluded; room-to-raise scan of 2 October 2026.", pb=False))

# ---------------------------------------------------------------- 10 P700
S.append(section("10", "P700 and the next price list", f"""
<p class='lead'><span class='tag next'>Next price list</span> The new P700 parts are a lever for the <b>next</b> price list, not for this year's revision.</p>
<div class='cards'>
 {card("P700-only new part numbers", f"{P7['parts']:,}", "on the provisional new-parts list")}
 {card("Ever billed, 2023 to August 2026", f"{P7['with_any_billing_2023_aug2026']}", em(P7['billed_eur_2023_aug2026'], 2) + f", of which {ek(P7['by_year']['2023'])} in 2023")}
 {card("In this year's base", f"{P7['in_proposal_base']}", e0(P7['proposal_base_billed']) + " billed")}
 {card("Billed July&ndash;August 2026".replace('&ndash;', '-'), f"{P7['with_billing_jul_aug_2026']}", e0(P7['billed_eur_jul_aug_2026']))}
</div>
<p>They need a first price, not an increase. What the September launch work established, and still holds:</p>
<ul class='tight'>
<li><b>New parts carry no weight in a volume-weighted increase</b>, so a revision target does not bind them. But most new numbers are not unpriced: of the 1,132 P700 and D-Max 2.2L part numbers without billing history in September, 1,048 already carry four consecutive published prices (2023&ndash;2026). The pricing latitude is the zero weight, not the absence of a reference.</li>
<li><b>The 13 functional SCR and AdBlue parts</b> (sensors, pumps, control units, catalyst, particulate filter assembly) sit exactly at their class price (within 0.45%) and have no aftermarket equivalent in any source on file. On the price book they could carry +25% to +35%; that level is a judgment, anchored only on a particulate-filter sensor (8978808270) that earns 69.3% gross margin against 56% in its class.</li>
<li><b>Do not commit a launch number before one question is answered</b>: whether the factory base price already contains a premium over transfer cost. If it does, the headroom is smaller.</li>
<li><b>Class assignment is margin assignment.</b> 922 of 1,071 classed new parts sit in class C (53% margin), 2 in class P (56%). Whether ISZE has a voice in how the factory classes new parts is worth more than most of this year's revision.</li>
<li><b>Failure-driven parts in the warranty window</b>: set the launch price towards the top of the band and hold it flat once each vehicle's own warranty ends. The modelled D-Max 2.2L comparison is close to neutral over ten years and depends on the warranty term (it pays from about three years); the term and mileage cap must be confirmed market by market.</li>
<li>Israel's export list sits a measured 13.95% below the standard list (not the recorded 10%); any Israeli P700 price must be restated before it is read across.</li>
</ul>
""", "P700 new-only parts: provisional new-parts weights list and SAP billing 2023&ndash;August 2026 (room-to-raise scan, 2 October 2026); launch facts: P700 and D-Max 2.2L launch pricing work of 19 September 2026 "
     "(2026 price file, published price history 2023&ndash;2026, competitor files); warranty-window model: pricing specification, section 9.3; Israel export list: UTI export list against the standard list on 134,896 matched part numbers."))

# ---------------------------------------------------------------- 11 UTI truck panels
pb_ = UN["panels_eur_bridge_janaug"]
pp_ = UN["panels_same_part_price_change_janaug_25_26"]
bo_ = UBO.loc["Panels"]
panel_step = float(UST[(UST.master_body) & (UST.grp == "Panels")].step.sum())
body_step = float(UST[(UST.master_body) & (UST.grp != "Lighting")].step.sum())
assert abs(panel_step - RS["holds"]["uti_panels_optional"]["step"]) < 1
eur_chg = pb_["eur_2026"] / pb_["eur_2025"] - 1
unit_chg = (pb_["units_both_2026"] / pb_["units_both_2025"] - 1)
eur_chg_same = pb_["eur_both_2026"] / pb_["eur_both_2025"] - 1
S.append(section("11", "UTI truck panels: no hold, availability first", f"""
<div class='callout navy'><span class='tag dec'>Decided</span> <b>UTI truck panels are not held at today's price</b> (2 October 2026). They take the normal step. The issue is availability, and it is addressed by stocking P700 panels against UTI's forecast.</div>
<p class='lead'><b>Finding: UTI's panel business is held back mainly by availability, not by price.</b> The price complaint is real on a few named parts, but billing shows no measurable volume lost to price.
Holding all UTI panels at today's price would not have addressed what UTI has raised.</p>
<div class='cards'>
 {card("Panels billed, Jan-Aug 2026 vs 2025", p1(eur_chg, True), f"{e0(pb_['eur_2025'])} to {e0(pb_['eur_2026'])}, while units rose")}
 {card("Same panels, both years", "units " + p1(unit_chg, True), "euro " + p1(eur_chg_same, True))}
 {card("Panel back orders, 1 July 2026", f"{int(bo_.lines)} lines", f"{int(bo_.units)} units, {ek(bo_.value_at_list)} at list, open up to {int(bo_.max_days_open)} days", "terra")}
 {card("Step kept by not holding panels", e0(panel_step), f"a hold on all UTI body except lighting would have given up up to {e0(body_step)}", "blue")}
</div>
<h3>Availability</h3>
<p>UTI has reported repeated back orders on body and panel parts through 2026, four to sixteen weeks from order to shipment, with the same part numbers on back order month after month,
and has asked ISZE to stock P700 items to raise the fill rate. Our back-order list of 1 July 2026 shows {int(bo_.lines)} panel lines open, up to {int(bo_.max_days_open)} days; a roof panel was open 139 days,
and one front inner lid had been ordered four times, on normal, rush and vehicle-off-road terms, and was still open. The urgent (rush and vehicle-off-road) share of panel order lines rose from 5.3% in the first half of 2025 to 15.6% in January&ndash;March 2026.</p>
<h3>Billing and price</h3>
<ul class='tight'>
<li>Panel billing fell {abs(eur_chg) * 100:.1f}% in January&ndash;August 2026 against 2025, while units rose. 53% of the euro drop is a single F-series grille (8972670504), a 2025 stock build being used up.
On the panels bought in both periods, units rose {p1(unit_chg)} and euro fell {abs(eur_chg_same) * 100:.1f}%. UTI's other parts fell 11.8%; other markets' panels rose 7.6%. UTI's own panel sales to its customers held at about 560&ndash;590 units a month.</li>
<li>On the same panels UTI paid a median {p1(pp_['median'], True)} in 2026 against a median list rise of {p1(pp_['list_change_same_parts_median'], True)}; UTI pays about 74% of list on panels (79% in 2025).
Across {UN['t5c_parts_used']} panels, larger list rises did not lose more volume (rank correlation {UN['t5c_rank_corr_listchange_vs_unitgrowth']:+.2f}).</li>
<li>UTI's cost on P700 body parts is about a quarter of its own selling price (its July 2026 sales report), so a 6.4% step adds at most about 1.6% to its shelf price.</li>
<li>The price complaint names three body parts as competing with aftermarket and used parts: grille 8974289771 (+3%), front panel 8981226950 (+16%) and door 8982606020 (+16%).
Two of them fit a price story: the front panel fell from 20 to 7 units and the grille from 28 to 12. The P700 collision-package increase (section 8) is a model change, not the April price change.</li>
</ul>
<p><b>What follows from the decision.</b> Agree a stocking plan for P700 body panels against UTI's forecast, so that the fill rate, not the price, is what changes for UTI.
The three parts UTI named stay visible in the price evidence; no Israeli copy-panel price is on file yet.</p>
<p class='small muted'>Limits: one back-order snapshot is on file (the weekly lists sit with UTI); order types are missing in our billing for April&ndash;June 2026; no Israeli copy-panel price is in the price ledger;
and lost jobs are not visible in our data &mdash; only UTI can supply them.</p>
""", "UTI correspondence February&ndash;October 2026 (read only); SAP parts billing to 31 August 2026; ISZE back-order list of 1 July 2026; UTI's own P700 body-parts sales report (July 2026, cost-to-sales ratio only); "
     "approved parts classification release of 2 October 2026 (Accident &amp; Body &gt; Panels); price observation ledger as of 2 October 2026; increase at stake from the +5% proposal on UTI lines July 2025&ndash;June 2026.", pb=False))

# ---------------------------------------------------------------- 12 background
S.append(section("12", "Background that still stands", f"""
<p>The September papers carried four strands of work that are not superseded by the +5% revision. They are kept here in short; each still bears on the next price list.</p>
<h3>The pickup buyer is not a truck buyer</h3>
<p>The UK operator's licence does not bind the D-Max: it is plated at 3,100 kg (the threshold is 3,500 kg) and is exempt as a dual-purpose vehicle. The exception is towing: with a 6,000 kg train weight, a D-Max towing plant is a licensed combination,
and that customer is less price-sensitive &mdash; but we cannot tell him apart in our sales data. Independent UK garages advertise D-Max servicing at up to 50% below the dealer while preserving the warranty, and the parts are visible on consumer price sites.
Ireland carries the heaviest compliance burden (an annual commercial roadworthiness test and a statutory maintenance duty); Portugal buys the pickup as a tax instrument (over 90% homologated with three seats).
UMI's D-Maxes run 34,443 km a year, the highest of the pickup markets; 66.4% of D-Maxes on Israeli roads are privately owned, while the best-selling new trim goes mostly to leasing companies.</p>
<h3>Refurbishment is a third price level below the aftermarket brands</h3>
<p>A cleaned particulate filter costs roughly 3&ndash;30% of a new part, depending on market and vehicle class. Israeli regulation permits removing the filter for cleaning, repair or replacement (reported, not re-verified),
and a specialised refurbishment trade serves garages, insurers and leasing companies there. Our own warranty book shows UTI truck filter claims of EUR 696,907, 76% of the filter cost outside the stated 3-year / 100,000 km terms,
and claim costs of 1.2&ndash;1.8 times our own list price (mechanism not established). The lever is timing rather than price: hold the aftertreatment price flat once each vehicle's warranty ends.
Isuzu Truck UK has supplied new filters at remanufactured-level prices on a new-in-lieu basis since 2017; the question is why Israel does not get that answer.</p>
<h3>How other manufacturers price</h3>
<p>Cost-plus by class is what most manufacturers do; the money is on the captive side (practitioner bands: competitive parts 25&ndash;35% margin, captive parts 55&ndash;75%), while our book earns one band around 51% for both.
"Matching quality" parts from the same supplier in its own box sit at roughly 60&ndash;80% of a genuine price. Listed independent distributors earn 27&ndash;29% gross margin. Sensors and aftertreatment are contested in the truck channel;
the genuinely gated parts are VIN-paired and software-coded modules and, until EU Regulation 2026/699 opens it from 23 December 2026, ADAS calibration. Every European truck maker runs a lower-priced own parts line; ours is the BVP (Best Value Parts) range.</p>
<h3>Volume response cannot be read from history</h3>
<p>Uniform increases leave almost no price variation to measure against; the April 2026 rise was the first with enough spread, and it shows a pooled reaction indistinguishable from zero (section 3).
The only route to a real coefficient is a field test: one family, a group of distributors, a matched control group.</p>
""", "pickup market research of 19 September 2026 (UK, Irish, Portuguese and Israeli regulations and statistics; UK fleet mileage file 2020&ndash;2026); refurbishment and particulate-filter research of 19 September 2026 "
     "(supplier catalogues, regulators, ISZE warranty files); external review of manufacturer and aftermarket pricing practice, 17 September 2026 (figures graded there as measured or trade-reported); EU Delegated Regulation 2026/699."))

# ---------------------------------------------------------------- 13 open points
S.append(section("13", "Open points and next steps", f"""
<h3>Open in this revision</h3>
<p class='small'><span class='tag dec'>Settled on 2 October</span> Ukraine buys on the main price list and takes the normal increase ({em(uk.billed_eur)} billed in the base; average move {p1(uk.B_avg_move)} under option B). UTI truck panels are not held (section 11).</p>
<table><thead><tr><th style='width:22%'>Point</th><th>What is open</th><th style='width:22%'>What is at stake</th></tr></thead><tbody>
<tr><td><span class='tag open'>Open</span><br><b>UMI leasing share</b></td><td>Leased double cabs in Israel must use genuine parts in their first two years and run the highest mileage of the pickup markets. If leasing is most of UMI's volume, its service hold could be lifted.
The share is unknown and is <b>not being requested now</b>; the hold stays until it is known.</td>
<td class='small'>UMI service parts {em(umi_service_billed)} billed; {ek(umi_service_step)} of step held.</td></tr>
<tr><td><span class='tag sug'>Suggested</span><br><b>IUK exemption</b></td><td>Option B with IUK repair and body kept at the proposal move (section 6).</td><td class='small'>{ek(iuk_rb_uplift)} moved from IUK to the other markets.</td></tr>

</tbody></table>
<h3>Questions carried over from September, still open</h3>
<ol class='tight'>
<li>Are the four front pad kits interchangeable? A catalogue question; if they are, a 25% price spread across networks on one safety-critical wear part is a commercial finding.</li>
<li>Does the factory base price embed a premium over transfer cost? It decides the P700 launch headroom.</li>
<li>What is the total-loss threshold for vehicles above 3.5 tonnes in Israel, and how often does a parts line actually tip a repair?</li>
<li>What do distributors do with a change in our price &mdash; pass it on, or keep the difference? A conversation with ITUK and the others, not a data request.</li>
<li>Does ISZE have a voice in the class assignment of new part numbers?</li>
<li>Is the BVP range deliberately priced against the aftermarket brands in front of those parts, and should its cross-reference be extended?</li>
<li>Why does Israel get the remanufactured-filter answer and the UK the new-in-lieu answer? And what is the filter warranty term in each market?</li>
<li>Does the announced exchange-rate treatment also apply to Thailand-sourced parts?</li>
</ol>
<h3>Next steps</h3>
<ol class='tight'>
<li>Decide the IUK exemption.</li>
<li>Agree a stocking plan for P700 body panels against UTI's forecast (section 11).</li>
<li>Add the market-condition layer to the proposal workbook (holds and option B as distributor conditions; the list stays one price per part). Not built yet.</li>
<li>Run a pattern-part price check on the top 50 body parts before the body share of option B is fixed.</li>
<li>Confirm the reference dealer price basis (x2.19, provisional).</li>
<li>Take the order-terms levers into the distributor negotiations as a separate item.</li>
<li>Prepare first prices for the P700 new parts for the next price list.</li>
</ol>
""", "this paper, sections 3&ndash;11; market exercise decision record (Ukraine, UMI); room-to-raise scan open points of 2 October 2026; carried-over questions from the pricing policy papers of 17 and 19 September 2026 and the management deck of 20 September 2026."))

# ---------------------------------------------------------------- appendix
S.append(section("A", "Terms and source register", f"""
<h3>Terms</h3>
<table class='small'><tbody>
<tr><td style='width:24%'><b>Parts billed</b></td><td>Our net sales of parts to distributors. The revision base is July 2025 to June 2026, in-scope parts priced on both sides: {e0(BASE)}, 15,273 part numbers.</td></tr>
<tr><td><b>Step</b></td><td>The euro value of a price move on the volume actually billed, before any dealer reaction.</td></tr>
<tr><td><b>Factory move</b></td><td>A part's own change in the factory (IML) base price, September 2026 against September 2025.</td></tr>
<tr><td><b>Hold</b></td><td>A part group kept at today's price in one market, applied as a distributor condition; the list stays one price per part.</td></tr>
<tr><td><b>Service / repair / body</b></td><td>Service = maintenance-service parts (filters, brakes, clutch and similar); body = the Accident &amp; Body family including lighting; repair = everything else. From the approved parts classification of 2 October 2026.</td></tr>
<tr><td><b>Captive</b></td><td>No confirmed or likely competitor part number, no aftermarket price observed, no cheaper Isuzu BVP alternative, not in the competitive-parts family, and not a category the distributor is measured to lose. In practice: no competitor found.</td></tr>
<tr><td><b>Reference dealer price</b></td><td>Our price list x 2.19 (provisional, 2 October 2026): what a dealer customer pays at the counter after distributor and dealer margins. A construction, not an observation.</td></tr>
<tr><td><b>Index</b></td><td>Outside price without VAT divided by our reference dealer price. Below 1.0 the outside seller is cheaper.</td></tr>
<tr><td><b>Service share</b></td><td>Service parts a market's distributor bought, against what its fleet should need at the service intervals.</td></tr>
<tr><td><b>Dealer response</b></td><td>How much less of a part dealers bought per 1% that it rose more than similar parts. Measured on the April 2026 list change.</td></tr>
<tr><td><b>IUK / ITUK, UMI / UTI</b></td><td>The UK D-Max and UK truck distributors; the Israeli D-Max and truck distributors. Never combined.</td></tr>
<tr><td><b>CIS</b></td><td>Armenia and Kazakhstan, as used in the market exercise. Ukraine is not included: it buys on the main price list.</td></tr>
<tr><td><b>Main price list</b></td><td>The standard list price per part (the PR00 base price condition in SAP). One price per part for every market on it.</td></tr>
<tr><td><b>BVP</b></td><td>Best Value Parts, Isuzu's own value-line range.</td></tr>
<tr><td><b>Stock / rush / vehicle-off-road</b></td><td>Order types. Rush and vehicle-off-road orders are urgent orders, usually billed above list.</td></tr>
</tbody></table>
<h3>Source register</h3>
<div class='small muted' style='line-height:1.55'>
Proposal: <i>02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29/</i> price_5pct_proposal_summary_2026-09-29.json, dealer_price_response_2026-09-29.json; workbook 01_data/01_Pricing/Price_Increase_5pct_Proposal_2026-09-29.xlsx (read only, not changed).<br>
Market exercise: market_exercise_decisions_2026-09-30.json, market_facts_2026-09-30.json; report 02_dashboards/pricing/ISZE_Market_Pricing_Exercise_2026-09-30.html.<br>
Where the +5% comes from: <i>room_to_raise_2026-10-02/</i> room_to_raise_summary_2026-10-02.json, room_to_raise_scenarios_2026-10-02.csv, room_to_raise_scenarios_by_segment_market_2026-10-02.csv,
lever4_order_terms_2026-10-02.csv, dealer_response_by_category_2026-10-02.csv, room_to_raise_by_part_2026-10-02.csv; IUK variant room_to_raise_variant_B_iuk_exempt_2026-10-02.json / .csv
(build_room_to_raise_20261002.py --variant-b-iuk-exempt). Inputs fingerprinted in the summary file: price ledger {RS['input_fingerprints']['price_observations.parquet']['sha256_12']}, cross-references {RS['input_fingerprints']['crossref_graded.csv']['sha256_12']},
classification release 2026-10-02 {RS['aim_release']['sha256'][:12]}, billing {RS['input_fingerprints']['sales_fact.parquet']['sha256_12']}.<br>
Carried over from the archived papers (01_data/92_archive/pricing_papers_superseded_2026-10-02/): pricing policy paper revision 3 of 19 September 2026 (class margins, book margin, Israel insurance, pickup market, P700 launch, refurbishment, external review);
revision 1 of 17 September 2026 (reason codes, per-truck effect, warranty window); management deck v1.4 of 20 September 2026 (purchase terms, exchange rates, class C share, agreed principles, battery precedent, pad-kit price range).
</div>
""", "as listed above. Built by 02_dashboards/pricing/_build/build_pricing_policy_paper_20261002.py."))

FOOT = "<div class='footer'><span>ISZE · Parts pricing policy · 2 October 2026</span><span>Proposal on paper — no price, list or condition changed</span></div>"
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Parts Pricing Policy</title>
<style>{CSS}</style></head>
<body><div class="wrap">{''.join(S)}</div></body></html>"""

# guards: self-contained, banned labels, no file names before the source register
low = page.lower()
for bad in ("http://", "https://", "<script", "street", "sell-out", "sellout", "wallet", "mode a", "mode b", "iml v7", "model b"):
    assert bad not in low, bad
assert not re.search(r"\bbook b\b", low), "Book B"
body = page.split("<h3>Source register</h3>")[0]
body_nosrc = re.sub(r"<div class='src'>.*?</div>", "", body, flags=re.S)
assert not re.search(r"\bnan\b|\bNaN\b|>None<|EUR nan", body_nosrc), "nan"
for bad in (".json", ".csv", ".py", ".parquet", ".xlsx", "_build", "room_to_raise"):
    assert bad not in body_nosrc, bad
OUT_HTML.write_text(page, encoding="utf-8")
OUT_CMD.write_bytes(f'@echo off\r\nstart "" "%~dp0{OUT_HTML.name}"\r\n'.encode("ascii"))
print("written", OUT_HTML, f"{OUT_HTML.stat().st_size / 1024:.0f} KB")
print("written", OUT_CMD)
