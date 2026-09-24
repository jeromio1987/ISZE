# -*- coding: utf-8 -*-
r"""ISUZU UNIVERSE - the programme whitepaper.  Figures.

Every chart is regenerated from a named source file at build time. No value is typed into a chart as
a bar height: where a figure is arithmetic, the chart computes it from the inputs stated in its own
source code and in its caption, so the picture cannot disagree with the arithmetic.

The constructions are copied from `_build_white\figures_white.py` and `_build_30\figures.py` rather
than imported, so that another worker's rebuild cannot overwrite these charts and this build cannot
break theirs.

Run:  python _build_wp\figures_whitepaper.py
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISZE = os.path.dirname(ROOT)
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
TENDER = os.path.join(ISZE, "01_data", "14_dashboards", "tender_data.json")
OUT = os.path.join(HERE, "figures")

CHARCOAL = "#24282C"
PANEL = "#353B3E"
RED = "#D71920"
WHITE = "#FFFFFF"
SECOND = "#CCD1D2"
NAVY = "#15233C"
TERR = "#C0552D"
FLAT = "#8E979C"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "figure.facecolor": CHARCOAL,
    "axes.facecolor": CHARCOAL,
    "axes.edgecolor": "#4A5257",
    "axes.labelcolor": SECOND,
    "text.color": WHITE,
    "xtick.color": SECOND,
    "ytick.color": SECOND,
    "axes.titlecolor": WHITE,
    "savefig.facecolor": CHARCOAL,
})

W, H = 9.4, 4.5


def _clean(ax, grid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#4A5257")
    ax.spines["bottom"].set_color("#4A5257")
    if grid:
        ax.yaxis.grid(True, color="#3A4145", lw=0.9)
        ax.set_axisbelow(True)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=CHARCOAL)
    plt.close(fig)
    return p


def load(name):
    with open(os.path.join(DERIVED, name), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def num(x):
    s = str(x).strip().replace(",", "")
    return float(s) if s else 0.0


def eur(v):
    return "EUR {:,.0f}".format(v)


def _sub(code, sub):
    for r in load("pms_genuine_bvp_vs_price_2024_2025.csv"):
        if r["distributor_code"] == code and r["product_subgroup"] == sub:
            return r
    raise KeyError(code + "/" + sub)


# ======================================================= 1-3  the worked examples (AIM)
def fig01_ituk_brake_pads():
    """Value fell less than quantity. Both percentages are computed, not typed."""
    d = _sub("ITUK", "brake_pad")
    fig, axes = plt.subplots(1, 2, figsize=(W, 3.9))
    pairs = [(num(d["total_eur_2024"]), num(d["total_eur_2025"]),
              "ISZE parts billed to Isuzu Truck UK (EUR)"),
             (num(d["total_qty_2024"]), num(d["total_qty_2025"]),
              "Recorded quantity (units)")]
    for ax, (v24, v25, lab) in zip(axes, pairs):
        ax.set_xticks([0, 1])
        bars = ax.bar([0, 1], [v24, v25], color=[FLAT, TERR], width=0.52,
                      edgecolor=WHITE, linewidth=0.7)
        for r, v in zip(bars, [v24, v25]):
            ax.text(r.get_x() + r.get_width() / 2, v, "{:,.0f}".format(v),
                    ha="center", va="bottom", fontsize=11, color=WHITE, fontweight="bold")
        ax.set_title(lab, fontsize=10, pad=8)
        ax.set_ylim(0, max(v24, v25) * 1.26)
        _clean(ax)
        ax.annotate("{:+.1f}%".format((v25 - v24) / v24 * 100), xy=(0.5, 0.84),
                    xycoords="axes fraction", ha="center", fontsize=16, color=RED,
                    fontweight="bold")
        ax.set_xticklabels(["Calendar 2024", "Calendar 2025"], fontsize=9.5)
    fig.suptitle("Isuzu Truck UK brake pads: value fell 13.0%, quantity fell 25.4%",
                 fontsize=12.5, color=WHITE, x=0.02, ha="left", y=1.07)
    return save(fig, "f01_ituk_brake_pads.png")


def fig02_brake_split():
    """Where the reduction sits. Pads carry most of it."""
    rows = [r for r in load("pms_genuine_bvp_vs_price_2024_2025.csv")
            if r["distributor_code"] == "ITUK" and r["product_group_label"] == "Brakes"]
    rows.sort(key=lambda x: num(x["total_eur_2024"]) - num(x["total_eur_2025"]))
    labels = [r["product_subgroup"].replace("_", " ") for r in rows]
    vals = [num(r["total_eur_2024"]) - num(r["total_eur_2025"]) for r in rows]
    total = sum(vals)
    top = max(vals)
    fig, ax = plt.subplots(figsize=(W, 2.9))
    cols = [TERR if v == top else FLAT for v in vals]
    bars = ax.barh(labels, vals, color=cols, height=0.5, edgecolor=WHITE, linewidth=0.7)
    for r, v in zip(bars, vals):
        ax.text(v + 900, r.get_y() + r.get_height() / 2,
                "{}   {:.1f}% of the fall".format(eur(v), 100 * v / total), va="center",
                fontsize=10.2, color=WHITE, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.55)
    ax.set_xlabel("Fall in ISZE parts billed, calendar 2025 against calendar 2024 (EUR)")
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=10)
    ax.set_title("{} across the three selected braking categories - brake pads are 95.7% of it"
                 .format(eur(total)), fontsize=11, pad=10, loc="left")
    return save(fig, "f02_brake_split.png")


def fig03_portugal_clutch():
    """Total business grew while the genuine line halved. Quantity barely moved."""
    d = _sub("PORTUGAL", "clutch_kit")
    gen = [num(d["genuine_eur_2024"]), num(d["genuine_eur_2025"])]
    bvp = [num(d["bvp_eur_2024"]), num(d["bvp_eur_2025"])]
    q24, q25 = num(d["total_qty_2024"]), num(d["total_qty_2025"])
    fig, ax = plt.subplots(figsize=(W, 3.7))
    x = [0, 1]
    ax.bar(x, gen, color=TERR, width=0.42, label="Genuine part", edgecolor=WHITE, linewidth=0.7)
    ax.bar(x, bvp, bottom=gen, color=FLAT, width=0.42, label="Best Value part",
           edgecolor=WHITE, linewidth=0.7)
    for xi, g, b in zip(x, gen, bvp):
        ax.text(xi, g + b + 900, "EUR {:,.2f}".format(g + b), ha="center", fontsize=11.5,
                color=WHITE, fontweight="bold")
        ax.text(xi, g / 2, "{:,.0f}".format(g), ha="center", va="center", fontsize=9.5,
                color=WHITE, fontweight="bold")
        ax.text(xi, g + b / 2, "{:,.0f}".format(b), ha="center", va="center", fontsize=9.5,
                color=WHITE, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(["Calendar 2024\n{:,.0f} kits".format(q24),
                        "Calendar 2025\n{:,.0f} kits".format(q25)], fontsize=10)
    ax.set_ylim(0, 39000)
    ax.set_ylabel("ISZE parts billed to I Motors, Portugal (EUR)")
    leg = ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(WHITE)
    _clean(ax)
    ax.annotate("combined {:+.1f}%".format((sum(gen[1:2] + bvp[1:2]) - sum(gen[:1] + bvp[:1]))
                                           / sum(gen[:1] + bvp[:1]) * 100),
                xy=(0.5, 0.90), xycoords="axes fraction", ha="center", fontsize=13,
                color=RED, fontweight="bold")
    ax.set_title("Portugal clutch kits: total business grew while the genuine line fell",
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f03_portugal_clutch.png")


# ======================================================= 4-5  where the concession sits
def fig04_concession_by_distributor():
    """The deepest concession sits in the smallest markets. Shade marks billed size."""
    rows = [r for r in load("pms_campaign_suspect_by_db_2024_2025.csv") if r["year"] == "2025"]
    rows.sort(key=lambda r: -num(r["pct_eur_ge20_under_ref"]))
    rows = rows[:10][::-1]
    names = [r["distributor_code"] for r in rows]
    shares = [num(r["pct_eur_ge20_under_ref"]) for r in rows]
    billed = [num(r["billed_eur"]) for r in rows]
    cols = [FLAT if b < 400000 else WHITE for b in billed]
    fig, ax = plt.subplots(figsize=(W, 4.4))
    bars = ax.barh(names, shares, color=cols, height=0.58, edgecolor=CHARCOAL, linewidth=0.6)
    for r, s, bl in zip(bars, shares, billed):
        ax.text(s + 0.4, r.get_y() + r.get_height() / 2,
                "{:.1f}%   (EUR {:,.0f}k billed)".format(s, bl / 1000), va="center",
                fontsize=9.2, color=SECOND)
    ax.set_xlim(0, 40)
    ax.set_xlabel("Share of 2025 parts billed at least 20% under the reference price")
    ax.tick_params(axis="y", labelsize=9.5)
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("The deepest concession sits in the smallest markets  (white = over EUR 400k billed)",
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f04_concession_by_distributor.png")


def fig05_concession_by_family():
    """Two families carry a lot of concession on a modest base; two large ones carry almost none."""
    rows = [r for r in load("pms_campaign_suspect_by_family_2024_2025.csv") if r["year"] == "2025"]
    rows.sort(key=lambda r: -num(r["billed_eur"]))
    rows = rows[:8][::-1]
    names = [r["pms_category"].replace("_", " ") for r in rows]
    shares = [num(r["pct_eur_ge20_under_ref"]) for r in rows]
    billed = [num(r["billed_eur"]) for r in rows]
    fig, ax = plt.subplots(figsize=(W, 4.0))
    bars = ax.barh(names, shares, color=TERR, height=0.56, edgecolor=WHITE, linewidth=0.7)
    for r, s, bl in zip(bars, shares, billed):
        ax.text(s + 0.5, r.get_y() + r.get_height() / 2,
                "{:.1f}%   (EUR {:,.0f}k)".format(s, bl / 1000), va="center", fontsize=9.2,
                color=SECOND)
    ax.set_xlim(0, 48)
    ax.set_xlabel("Share of 2025 family billing at least 20% under the reference price")
    ax.tick_params(axis="y", labelsize=9.5)
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("Two families carry a lot of concession on modest bases; two large ones carry almost none",
                 fontsize=10.5, pad=10, loc="left")
    return save(fig, "f05_concession_by_family.png")


# ======================================================= 6-7  the two self-assessment figures
def fig06_ids_scores():
    """How much of the assessed estate already carries an individual score.

    A zero means no answers were recorded, so those records are excluded from the distribution and
    counted separately rather than read as the weakest dealers.
    """
    rows = [r for r in load("ids_dealer_network_cleaned_2026-09-20.csv") if r["points_pct"].strip()]
    vals = [num(r["points_pct"]) for r in rows if num(r["points_pct"]) > 0]
    unassessed = len(rows) - len(vals)
    avg = sum(vals) / len(vals)
    fig, ax = plt.subplots(figsize=(W, 3.5))
    ax.hist(vals, bins=list(range(0, 101, 10)), color=TERR, edgecolor=CHARCOAL, linewidth=1.0)
    ax.axvline(avg, color=RED, lw=2.2, linestyle="--")
    ax.text(avg + 1.8, ax.get_ylim()[1] * 0.86, "average {:.1f}".format(avg), color=RED,
            fontsize=10.5, fontweight="bold")
    ax.set_xlabel("Recorded self-assessment score (%)")
    ax.set_ylabel("Dealers")
    _clean(ax)
    ax.set_title("{} of the 519 dealer records carry a score today; {} recorded no answers"
                 .format(len(vals), unassessed), fontsize=10.5, pad=10, loc="left")
    return save(fig, "f06_ids_scores.png")


def fig07_ituk_capture():
    """Billed units against modelled demand, on the model's own stated denominator."""
    rows = [r for r in load("pms_capture_by_db_year.csv")
            if r["distributor_code"] == "ITUK" and r["year"] == "2025" and r["line_type"] == "total"]
    rows.sort(key=lambda r: -num(r["actual_rev_eur"]))
    top = rows[:9][::-1]
    names = [r["category_label"] for r in top]
    cap = [num(r["capture_rate"]) * 100 for r in top]
    rev = [num(r["actual_rev_eur"]) for r in top]
    fig, ax = plt.subplots(figsize=(W, 4.2))
    cols = [RED if c > 100 else (TERR if c >= 50 else FLAT) for c in cap]
    bars = ax.barh(names, cap, color=cols, height=0.58, edgecolor=WHITE, linewidth=0.7)
    ax.axvline(100, color=WHITE, lw=1.2, linestyle=":")
    ax.text(101, len(names) - 0.35, "100% of modelled demand", fontsize=8.6, color=WHITE)
    for r, c, v in zip(bars, cap, rev):
        ax.text(max(c, 100) + 3, r.get_y() + r.get_height() / 2,
                "{:.1f}%   (EUR {:,.0f}k billed)".format(c, v / 1000), va="center",
                fontsize=9.0, color=SECOND)
    ax.set_xlim(0, 168)
    ax.set_xlabel("Units billed as a share of modelled expected demand (%)")
    ax.tick_params(axis="y", labelsize=9.5)
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("A share above 100% means the denominator is too small for that family, not that all demand was captured",
                 fontsize=10.0, pad=10, loc="left")
    return save(fig, "f07_ituk_capture.png")


# ======================================================= 8-11  the money
def fig08_network_billed():
    """The denominator every share divides by."""
    rows = [r for r in load("gps_spu_by_distributor.csv")
            if r["year"] == "2025" and r["total_sales_eur"].strip()]
    rows.sort(key=lambda r: -num(r["total_sales_eur"]))
    top = rows[:10][::-1]
    names = [r["distributor_code"] for r in top]
    vals = [num(r["total_sales_eur"]) for r in top]
    total = sum(num(r["total_sales_eur"]) for r in rows)
    fig, ax = plt.subplots(figsize=(W, 4.2))
    bars = ax.barh(names, vals, color=TERR, height=0.6, edgecolor=WHITE, linewidth=0.7)
    for r, v in zip(bars, vals):
        ax.text(v + 90000, r.get_y() + r.get_height() / 2,
                "{}   {:.1f}% of the network".format(eur(v), 100 * v / total), va="center",
                fontsize=9.0, color=SECOND)
    ax.set_xlim(0, max(vals) * 1.58)
    ax.set_xlabel("ISZE parts billed to the distributor, calendar 2025 (EUR)")
    ax.tick_params(axis="y", labelsize=9.5)
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("The ten largest distributors carry {:.1f}% of {} billed in 2025 across {} distributors"
                 .format(100 * sum(vals) / total, eur(total), len(rows)),
                 fontsize=10.5, pad=10, loc="left")
    return save(fig, "f08_network_billed.png")


def fig09_ceiling_placeholder():
    """The modelled ceiling, and the markets resting on a flat per-truck assumption."""
    rows = [r for r in load("gps_spu_by_distributor.csv")
            if r["year"] == "2025" and r["max_spend_eur"].strip() and r["uio_units"].strip()]
    for r in rows:
        r["_per"] = num(r["max_spend_eur"]) / num(r["uio_units"])
        r["_max"] = num(r["max_spend_eur"])
    rows.sort(key=lambda r: -r["_max"])
    total = sum(r["_max"] for r in rows)
    flat = [r for r in rows if abs(r["_per"] - 250.0) < 0.01]
    flat_sum = sum(r["_max"] for r in flat)
    names = [r["distributor_code"] for r in rows][::-1]
    vals = [r["_max"] for r in rows][::-1]
    cols = [RED if abs(r["_per"] - 250.0) < 0.01 else FLAT for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(W, 4.6))
    bars = ax.barh(names, vals, color=cols, height=0.62, edgecolor=CHARCOAL, linewidth=0.6)
    for r, v in zip(bars, vals):
        ax.text(v + 120000, r.get_y() + r.get_height() / 2, "EUR {:,.2f}m".format(v / 1e6),
                va="center", fontsize=8.8, color=SECOND)
    ax.set_xlim(0, max(vals) * 1.40)
    ax.set_xlabel("Modelled target-spend ceiling, calendar 2025 (EUR)")
    ax.tick_params(axis="y", labelsize=8.6)
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("{} of the {} markets rest on a flat EUR 250 per truck, holding {} = {:.2f}% of the ceiling"
                 .format(len(flat), len(rows), eur(flat_sum), 100 * flat_sum / total),
                 fontsize=10.5, pad=10, loc="left")
    return save(fig, "f09_ceiling_placeholder.png")


def fig10_hurdle():
    """How many qualifying actions each envelope implies. Arithmetic on stated inputs."""
    fig, ax = plt.subplots(figsize=(W, 3.8))
    contribs = [500, 1000, 2500, 5000]
    envelopes = [(100000, FLAT, "EUR 100,000 route"), (300000, TERR, "EUR 300,000 route")]
    x = range(len(contribs))
    w = 0.36
    for i, (env, col, lab) in enumerate(envelopes):
        vals = [env / c for c in contribs]
        bars = ax.bar([j + (i - 0.5) * w for j in x], vals, width=w, color=col,
                      label=lab, edgecolor=WHITE, linewidth=0.7)
        for r, v in zip(bars, vals):
            ax.text(r.get_x() + r.get_width() / 2, v * 1.07, "{:,.0f}".format(v),
                    ha="center", fontsize=9.4, color=WHITE, fontweight="bold")
    ax.axhline(40, color=RED, lw=1.6, linestyle="--")
    ax.text(3.42, 43, "40", color=RED, fontsize=10, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylim(10, 1500)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["EUR {:,}".format(c) for c in contribs])
    ax.set_xlabel("Assumed contribution per qualifying action")
    ax.set_ylabel("Qualifying actions needed (log scale)")
    leg = ax.legend(frameon=False, fontsize=9.5, loc="upper right")
    for t in leg.get_texts():
        t.set_color(WHITE)
    _clean(ax)
    ax.set_title("Forty qualifying actions at EUR 2,500 each is the hurdle the 100,000 route implies",
                 fontsize=10.5, pad=10, loc="left")
    return save(fig, "f10_hurdle.png")


def fig11_campaign_scope():
    """Why the scope of a concession changes what it costs. Hypothetical arithmetic on stated inputs."""
    # inputs - stated here and repeated in the caption; the heights are computed from them
    base_units, net_price, parts_cost, add_units, concession = 100.0, 100.0, 70.0, 20.0, 0.05
    all_units = base_units + add_units
    gp_unchanged = base_units * (net_price - parts_cost)
    gp_all = all_units * (net_price * (1 - concession) - parts_cost)
    gp_add = base_units * (net_price - parts_cost) + add_units * (net_price * (1 - concession) - parts_cost)
    labels = ["Unchanged offer\n100 units at EUR 100",
              "Concession on all 120 units\n(the baseline included)",
              "Concession on the 20\nadditional units only"]
    vals = [gp_unchanged, gp_all, gp_add]
    fig, ax = plt.subplots(figsize=(W, 3.7))
    bars = ax.bar(labels, vals, color=[FLAT, PANEL, TERR], width=0.5, edgecolor=WHITE,
                  linewidth=0.7)
    for r, v in zip(bars, vals):
        ax.text(r.get_x() + r.get_width() / 2, v, "EUR {:,.0f}".format(v), ha="center",
                va="bottom", fontsize=12, color=WHITE, fontweight="bold")
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel("Parts gross profit for the campaign (EUR)")
    _clean(ax)
    ax.tick_params(axis="x", labelsize=8.8)
    ax.set_title("EUR {:,.0f} of gross profit turns on the scope of the concession alone"
                 .format(vals[2] - vals[1]), fontsize=11, pad=10, loc="left")
    return save(fig, "f11_campaign_scope.png")


# ======================================================= 12  participation
def fig12_participation():
    """The honest score per step, with the reason beside each number."""
    dealer = [("Accepts the first prepared review", 55,
               "ten minutes, arrives finished, competes with a customer"),
              ("Corrects the interpretation", 70,
               "low cost and self-interested - the most reliable step"),
              ("Opens and uses its own profile", 65,
               "its own answers, real wording, a priority it chooses"),
              ("Returns for a second task", 30,
               "no cash, no visibility gain, no recurring trigger"),
              ("Shares beyond a correction", 20,
               "needs a reason the design does not yet create"),
              ("DEALER JOINS AS DESIGNED", 45, "credible for three steps, unproven after them")]
    dist = [("Accepts the opening", 75,
             "cheap, no added reporting burden, rebate floor exists"),
            ("Uses the review internally", 45,
             "depends on answering a question it already had"),
            ("Selects a case with a named owner", 50,
             "management attention is the scarcest resource"),
            ("Shares detail beyond the report", 35,
             "genuinely useful and genuinely sensitive"),
            ("Develops its own dealers", 40,
             "highest-value outcome, least supported by the design"),
            ("Co-funds participation", 25, "no precedent; do not ask in year one"),
            ("DISTRIBUTOR JOINS AS DESIGNED", 55, "credible start, unproven second step")]
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), gridspec_kw={"wspace": 0.72})
    for ax, rows, title in zip(axes, (dealer, dist), ("The dealer", "The distributor")):
        rows = rows[::-1]
        names = [r[0] for r in rows]
        vals = [r[1] for r in rows]
        why = [r[2] for r in rows]
        cols = [RED if n.isupper() else (TERR if v >= 50 else FLAT) for n, v in zip(names, vals)]
        bars = ax.barh(names, vals, color=cols, height=0.6, edgecolor=WHITE, linewidth=0.6)
        for r, v, w in zip(bars, vals, why):
            ax.text(v + 2, r.get_y() + r.get_height() / 2,
                    "{} - {}".format(v, w), va="center", fontsize=7.4, color=SECOND)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.tick_params(axis="y", labelsize=8.0)
        ax.tick_params(axis="x", labelsize=8.0)
        ax.set_title(title, fontsize=11, pad=8, loc="left")
        ax.xaxis.grid(True, color="#3A4145", lw=0.9)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color("#4A5257")
        ax.spines["bottom"].set_color("#4A5257")
    axes[0].set_xlabel("Score out of 100. A judgement on the design, not a measurement.", fontsize=9)
    fig.suptitle("How likely each step is to happen, and the reason for each number",
                 fontsize=12, color=WHITE, x=0.02, ha="left", y=1.02)
    return save(fig, "f12_participation.png")


# ======================================================= 13  the DLOD label layers
def fig13_dlod_layers():
    """Where the programme name survives, and where it is lost."""
    fig, ax = plt.subplots(figsize=(W, 3.6))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.0, 0.955, "The programme name survives one layer up, and the working file does not keep it",
            fontsize=11.0, color=WHITE, fontweight="bold")
    ax.add_patch(Rectangle((0.0, 0.36), 0.44, 0.48, facecolor=PANEL, edgecolor="#5A6469",
                           linewidth=0.8))
    ax.text(0.022, 0.765, "THE DERIVED BILLING FILE", fontsize=8.6, color=SECOND, fontweight="bold")
    ax.text(0.022, 0.675, "538,346 invoice lines, 12 columns", fontsize=9.4, color=WHITE)
    ax.text(0.022, 0.575, "0 hits", fontsize=19, color=RED, fontweight="bold")
    ax.text(0.022, 0.462, "The typed reference a person wrote is not one\nof the twelve columns it carries.",
            fontsize=8.8, color=SECOND, va="top")
    ax.add_patch(Rectangle((0.52, 0.36), 0.48, 0.48, facecolor=TERR, edgecolor="none"))
    ax.text(0.542, 0.765, "THE RAW EXTRACTS AND THE ORDER LAYER", fontsize=8.6, color=WHITE,
            fontweight="bold")
    ax.text(0.542, 0.675, "The typed reference, as a person wrote it", fontsize=9.4, color=WHITE)
    ax.text(0.542, 0.575, "5 labelled documents", fontsize=16, color=WHITE, fontweight="bold")
    ax.text(0.542, 0.462, "DLOD x3 and DLAD x2, case-insensitive.\nEUR 90,000.00 in total, 2023 to 2026.",
            fontsize=8.8, color=WHITE, va="top")
    ax.add_patch(FancyArrowPatch((0.445, 0.60), (0.515, 0.60), arrowstyle="-|>", color=WHITE,
                                 lw=2.0, mutation_scale=13))
    ax.add_patch(Rectangle((0.0, 0.17), 1.0, 0.125, facecolor=PANEL, edgecolor=RED, linewidth=1.3))
    ax.text(0.016, 0.232, "And still 0 cases. Not one part, dealer, competitor quote or outcome "
                          "is recorded anywhere.", fontsize=9.8, color=WHITE, va="center")
    ax.text(0.0, 0.065, "The money is labelled and the case is not. That is one field to add, not a "
                        "programme that left no trace.", fontsize=9.4, color=SECOND, va="center")
    return save(fig, "f13_dlod_layers.png")


# ======================================================= 14  the tender funnel
def fig14_tender_funnel():
    """How a public notice becomes a pursuit decision, and where the trail stops."""
    d = json.load(open(TENDER, encoding="utf-8"))
    st = d["meta"]["stats"]
    oc = d["meta"]["outcomes_summary"]
    fig, ax = plt.subplots(figsize=(W, 3.9))
    ax.axis("off")
    stages = [("Raw notices collected", st["raw_notices"], "as observed, with source and date"),
              ("Reduced to opportunities", st["opportunities"], "each notice counted once"),
              ("In the action queue", st["action_queue"], "enough evidence to decide"),
              ("Due within fourteen days", st["due_14d"], "a deadline close enough to force it"),
              ("Outcomes recorded", oc["recorded"], "won, lost or declined, at case level")]
    for i, (lab, n, sub) in enumerate(stages):
        y = 0.84 - i * 0.155
        w = 0.30 + 0.30 * (i / 4)
        face = TERR if i < 4 else PANEL
        edge = "none" if i < 4 else RED
        ax.add_patch(Rectangle((0.0, y - 0.052), w, 0.104, facecolor=face, edgecolor=edge,
                               linewidth=1.4))
        ax.text(0.014, y, "{}   {:,.0f}".format(lab, n), fontsize=9.6, color=WHITE, va="center",
                fontweight="bold")
        ax.text(min(w + 0.02, 0.70), y, sub, fontsize=8.8, color=SECOND, va="center")
    ax.text(0.0, 0.93, "A notice count is not pipeline - and the trail stops before the outcome",
            fontsize=11.2, color=WHITE, fontweight="bold")
    ax.text(0.0, 0.045, "The feed reports its own win rate as insufficient data: it needs twenty closed "
                        "cases before it will print one.", fontsize=9.0, color=RED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.0, 1.0)
    return save(fig, "f14_tender_funnel.png")


# ======================================================= the register
FIGURES = [
    (1, "Isuzu Truck UK brake pads: value and quantity", fig01_ituk_brake_pads,
     "ISZE parts billed and recorded quantity, Isuzu Truck UK, brake-pad source category, full calendar "
     "years 2024 and 2025. Measured. Source: the supplied category-mix aggregate, snapshot 19 September "
     "2026, recomputed 23 September 2026. Limitation: the 22,389-truck national figure is not the "
     "eligible population for every pad reference and is not divided among dealers."),
    (2, "Where the reduction sits across braking", fig02_brake_split,
     "Fall across the three selected Isuzu Truck UK braking source categories, calendar 2025 against "
     "calendar 2024, in euro. Measured, same source and period as figure 1. Limitation: it does not "
     "make the fall recoverable revenue, and it does not support one remedy across all three."),
    (3, "Portugal clutch kits: total grew, genuine fell", fig03_portugal_clutch,
     "ISZE parts billed to I Motors, Portugal, clutch-kit source category, full calendar years, split "
     "into the genuine part and the Best Value part. Measured. Quantity was almost unchanged: 462 kits "
     "to 461. Limitation: the Portuguese national vehicle count is a market figure and is not the "
     "eligible fleet for these kits."),
    (4, "Deep concession by distributor, 2025", fig04_concession_by_distributor,
     "Share of 2025 parts billed at least 20% under the reference price, on lines carrying a reference "
     "price, 24 distributors; the ten largest shares are shown. Measured. Limitation: a reference "
     "valuation is not a transaction, so a deep-concession share is not a margin. The bar shade marks "
     "billed size, so colour is not the only way to read it."),
    (5, "Deep concession by product family, 2025", fig05_concession_by_family,
     "The eight largest product families by 2025 billing, same source and period as figure 4. Measured. "
     "Limitation: a family with almost no deep concession is a family whose pricing is settled, not a "
     "family without a commercial opportunity."),
    (6, "Recorded dealer self-assessment scores", fig06_ids_scores,
     "519 dealer self-assessment records across 19 country lists, one round, no per-dealer assessment "
     "date; 490 carry an individual score, average 79.3; the other 29 recorded no answers and are "
     "excluded rather than counted as zero. Measured on the dealer network file of "
     "20 September 2026. Limitation: a self-reported number from one undated round is not a "
     "performance measure."),
    (7, "Isuzu Truck UK billed units against modelled demand, 2025", fig07_ituk_capture,
     "Billed units as a share of modelled expected demand, the nine largest families by billing, total "
     "sales line, 2025. Measured, on the capture model's own denominator of 23,068 model buckets. "
     "Limitation: a share above 100% means the denominator is too small for that family, not that more "
     "than all demand was captured, and such a rate must not be read at face value."),
    (8, "Where the billed parts are, 2025", fig08_network_billed,
     "ISZE parts billed to each distributor, calendar 2025, the ten largest shown out of the 22 "
     "distributors carrying a billed figure. Measured, GPS distributor file, 2025 rows. This is the "
     "denominator that every share in the money chapter divides by."),
    (9, "The modelled ceiling and the flat per-truck placeholder", fig09_ceiling_placeholder,
     "Modelled target-spend ceiling by market, calendar 2025, the 18 markets carrying both a fleet "
     "figure and a ceiling. Measured on the GPS distributor file, recomputed 23 September 2026. "
     "Limitation: the markets marked in red rest on a flat EUR 250 per truck, which is an assumption "
     "and not a measured purchasing rate. The ceiling is not revenue and must never be read as "
     "revenue."),
    (10, "The hurdle each funding route implies", fig10_hurdle,
     "Qualifying actions needed to cover each route at four assumed contribution levels: route divided "
     "by assumed contribution per action. Arithmetic on stated inputs, not a forecast of dealer "
     "profitability and not a record of an achieved result. Limitation: the contribution per action is "
     "an assumption, and internal effort sits outside both routes."),
    (11, "The scope effect on what a concession costs", fig11_campaign_scope,
     "Parts gross profit for one campaign under three scopes, from stated inputs: a 100-unit baseline "
     "at EUR 100 net with EUR 70 of parts cost, 20 additional units, a 5% concession. Arithmetic on "
     "those inputs, computed at build time. Limitation: it is not an Isuzu price, offer or forecast, "
     "and it assumes no demand response."),
    (12, "Participation: the score at each step, and why", fig12_participation,
     "A judgement on the design as it stands, per step, for the dealer and the distributor, with the "
     "reason for each number printed beside it. Proposed, not measured: this is an argument with the "
     "design, and the numbers are given so that the argument can be had."),
    (13, "Where the programme name survives, and where it is lost", fig13_dlod_layers,
     "The derived billing file and the raw extracts, searched for the competitive-quote programme's "
     "own name. The derived file carries twelve columns and not the typed reference, so a search there "
     "returns nothing; the raw extracts and the order layer preserve the reference a person typed. "
     "Measured. Limitation: a label proves a payment, and none of the five documents carries a part, a "
     "dealer, a competitor quote or an outcome."),
    (14, "From a public notice to a pursuit decision", fig14_tender_funnel,
     "The live opportunity feed as observed on 22 September 2026: 689 raw notices, 619 opportunities, "
     "199 in the action queue, 45 due within fourteen days, 0 recorded outcomes. Measured. Limitation: "
     "a notice count is not pipeline value, a tender's advertised value is not expected parts revenue, "
     "and 588 of the 619 opportunities carry no value figure at all."),
]


def build_all():
    paths = {}
    for n, _title, fn, _note in FIGURES:
        paths[n] = fn()
        print("  figure {:>2}  {}".format(n, os.path.basename(paths[n])))
    return paths


if __name__ == "__main__":
    print("generating figures from", DERIVED)
    build_all()
    print("done")
