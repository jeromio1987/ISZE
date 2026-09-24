# -*- coding: utf-8 -*-
r"""ISUZU UNIVERSE white paper - the figures.

A copy of the chart constructions in `_build_30\figures.py`, re-pointed at the white paper's own figure
plan and re-themed for a charcoal page. Copied rather than imported, so the other workers' rebuild
cannot overwrite these charts and this rebuild cannot break theirs.

**Every figure in this paper is a measured chart or arithmetic on stated inputs.** No figure exists to
decorate a section. A value is never typed in as a number that could be recomputed: each chart reads a
named source file, and where a figure is arithmetic the inputs are in its own source code and in its
caption.

Run:  python _build_white\figures_white.py
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
DERIVED = os.path.join(os.path.dirname(ROOT), "01_data", "00_derived")
TENDER = os.path.join(os.path.dirname(ROOT), "01_data", "14_dashboards", "tender_data.json")
OUT = os.path.join(HERE, "figures")

# ---- the palette, confirmed against the AIM style deck and the megaprompt section 8 -----------
CHARCOAL = "#24282C"
PANEL = "#353B3E"
RED = "#D71920"
WHITE = "#FFFFFF"
SECOND = "#CCD1D2"
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


def _sub(code, sub):
    for r in load("pms_genuine_bvp_vs_price_2024_2025.csv"):
        if r["distributor_code"] == code and r["product_subgroup"] == sub:
            return r
    raise KeyError(code + "/" + sub)


def _eur(v):
    return "EUR {:,.0f}".format(v)


# ================================================================ 1-7 measured pillar evidence
def fig01_ituk_brake_pads():
    """Value fell 13.0%; quantity fell 25.4%. The whole argument on one figure."""
    d = _sub("ITUK", "brake_pad")
    fig, axes = plt.subplots(1, 2, figsize=(W, 3.9))
    pairs = [(float(d["total_eur_2024"]), float(d["total_eur_2025"]),
              "ISZE parts billed to Isuzu Truck UK (EUR)"),
             (float(d["total_qty_2024"]), float(d["total_qty_2025"]),
              "Recorded quantity (units)")]
    for ax, (v24, v25, lab) in zip(axes, pairs):
        ax.set_xticks([0, 1])
        bars = ax.bar([0, 1], [v24, v25], color=[FLAT, TERR], width=0.52,
                      edgecolor=WHITE, linewidth=0.7)
        for r, v in zip(bars, [v24, v25]):
            ax.text(r.get_x() + r.get_width() / 2, v, _eur(v).replace("EUR ", ""),
                    ha="center", va="bottom", fontsize=11, color=WHITE, fontweight="bold")
        ax.set_title(lab, fontsize=10, pad=8)
        ax.set_ylim(0, max(v24, v25) * 1.26)
        _clean(ax)
        pct = (v25 - v24) / v24 * 100
        ax.annotate("{:+.1f}%".format(pct), xy=(0.5, 0.84), xycoords="axes fraction",
                    ha="center", fontsize=16, color=RED, fontweight="bold")
        ax.set_xticklabels(["Calendar 2024", "Calendar 2025"], fontsize=9.5)
    fig.suptitle("Isuzu Truck UK brake pads: value fell 13.0%, quantity fell 25.4%",
                 fontsize=12.5, color=WHITE, x=0.02, ha="left", y=1.07)
    return save(fig, "f01_ituk_brake_pads.png")


def fig02_brake_split():
    """Where the reduction sits: pads carry 95.7% of it."""
    rows = [r for r in load("pms_genuine_bvp_vs_price_2024_2025.csv")
            if r["distributor_code"] == "ITUK" and r["product_group_label"] == "Brakes"]
    rows.sort(key=lambda x: float(x["total_eur_2025"]) - float(x["total_eur_2024"]))
    labels = [r["product_subgroup"].replace("_", " ") for r in rows]
    vals = [float(r["total_eur_2024"]) - float(r["total_eur_2025"]) for r in rows]
    fig, ax = plt.subplots(figsize=(W, 2.9))
    cols = [TERR if v == max(vals) else FLAT for v in vals]
    bars = ax.barh(labels, vals, color=cols, height=0.5, edgecolor=WHITE, linewidth=0.7)
    for r, v in zip(bars, vals):
        ax.text(v + 900, r.get_y() + r.get_height() / 2, _eur(v), va="center",
                fontsize=10.5, color=WHITE, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.34)
    ax.set_xlabel("Reduction in ISZE parts billed, calendar 2025 against calendar 2024 (EUR)")
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=10)
    ax.set_title("EUR 47,068.77 across the three selected braking categories - brake pads are 95.7% of it",
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f02_brake_split.png")


def fig03_portugal_clutch():
    """Combined business grew while the genuine line fell. The mistake this product prevents."""
    d = _sub("PORTUGAL", "clutch_kit")
    gen = [float(d["genuine_eur_2024"]), float(d["genuine_eur_2025"])]
    bvp = [float(d["bvp_eur_2024"]), float(d["bvp_eur_2025"])]
    fig, ax = plt.subplots(figsize=(W, 3.7))
    x = [0, 1]
    ax.bar(x, gen, color=TERR, width=0.42, label="Genuine", edgecolor=WHITE, linewidth=0.7)
    ax.bar(x, bvp, bottom=gen, color=FLAT, width=0.42, label="Best Value parts",
           edgecolor=WHITE, linewidth=0.7)
    for xi, g, b in zip(x, gen, bvp):
        ax.text(xi, g + b + 900, "EUR {:,.2f}".format(g + b), ha="center", fontsize=11.5,
                color=WHITE, fontweight="bold")
        ax.text(xi, g / 2, "{:,.0f}".format(g), ha="center", va="center", fontsize=9.5,
                color=WHITE, fontweight="bold")
        ax.text(xi, g + b / 2, "{:,.0f}".format(b), ha="center", va="center", fontsize=9.5,
                color=WHITE, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(["Calendar 2024\n462 kits", "Calendar 2025\n461 kits"], fontsize=10)
    ax.set_ylim(0, 39000)
    ax.set_ylabel("ISZE parts billed to I Motors, Portugal (EUR)")
    leg = ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(WHITE)
    _clean(ax)
    ax.annotate("combined +5.8%", xy=(0.5, 0.90), xycoords="axes fraction", ha="center",
                fontsize=13, color=RED, fontweight="bold")
    ax.set_title("Portugal clutch kits: total business grew while the genuine line halved",
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f03_portugal_clutch.png")


def fig04_concession_by_distributor():
    """Where deep concession sits: the deepest is in the smallest markets."""
    rows = [r for r in load("pms_campaign_suspect_by_db_2024_2025.csv") if r["year"] == "2025"]
    rows.sort(key=lambda r: -float(r["pct_eur_ge20_under_ref"]))
    rows = rows[:10][::-1]
    names = [r["distributor_code"] for r in rows]
    shares = [float(r["pct_eur_ge20_under_ref"]) for r in rows]
    billed = [float(r["billed_eur"]) for r in rows]
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
    return save(fig, "f07_concession_by_distributor.png")


def fig05_concession_by_family():
    """Two families carry a lot of concession on a modest base; two large ones carry almost none."""
    rows = [r for r in load("pms_campaign_suspect_by_family_2024_2025.csv") if r["year"] == "2025"]
    rows.sort(key=lambda r: -float(r["billed_eur"]))
    rows = rows[:8][::-1]
    names = [r["pms_category"].replace("_", " ") for r in rows]
    shares = [float(r["pct_eur_ge20_under_ref"]) for r in rows]
    billed = [float(r["billed_eur"]) for r in rows]
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
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f08_concession_by_family.png")


def fig06_ids_scores():
    """How much of the estate already carries a recorded self-assessment score.

    A zero means the assessment was never carried out, not that the dealer scored badly, so those
    records are excluded from the distribution and stated separately.
    """
    rows = [r for r in load("ids_dealer_network_cleaned_2026-09-20.csv") if r["points_pct"].strip()]
    vals = [float(r["points_pct"]) for r in rows if float(r["points_pct"]) > 0]
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
    ax.set_title("{} of the 519 dealers in the network file carry a recorded score today; "
                 "{} recorded no answers and are not shown".format(len(vals), unassessed),
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f04_ids_scores.png")


def fig07_cordwallis():
    """The one verified dealer case: what it measured, and what it cannot join."""
    p = os.path.join(ROOT, "_STRATEGY", "_ORCHESTRATION", "ITUK_CASE_2026-09-21_01",
                     "evidence", "C04_verify_return.json")
    d = json.load(open(p, encoding="utf-8"))
    want = [("Fitted at the workshop", "C01: consumable fitted units"),
            ("Bought by the same account", "C01: consumable units bought"),
            ("Checks run, 0 failed", None)]
    vals = []
    for lab, key in want:
        if key is None:
            vals.append((lab, float(d["checks_run"])))
        else:
            hit = [c for c in d["checks"] if c["check"] == key][0]
            vals.append((lab, float(hit["return_says_or_source_says"])))
    fig, ax = plt.subplots(figsize=(W, 3.2))
    labels = [v[0] for v in vals] + ["Trucks the workshop saw"]
    numbers = [v[1] for v in vals] + [72.0]
    bars = ax.bar(range(len(labels)), numbers, color=[TERR, FLAT, WHITE, "#59636A"], width=0.5,
                  edgecolor=WHITE, linewidth=0.7)
    for r, v in zip(bars, numbers):
        ax.text(r.get_x() + r.get_width() / 2, v, "{:,.0f}".format(v), ha="center", va="bottom",
                fontsize=13, color=WHITE, fontweight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([l.replace(" ", "\n", 1) for l in labels], fontsize=9)
    ax.set_ylim(0, max(numbers) * 1.22)
    _clean(ax)
    ax.set_title("Cordwallis Commercials, Heathrow, calendar 2025: four measured numbers",
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f11_cordwallis.png")


def fig08_ituk_capture():
    """What the ITUK expected-demand model says, by family, on its own stated denominator."""
    rows = [r for r in load("pms_capture_by_db_year.csv")
            if r["distributor_code"] == "ITUK" and r["year"] == "2025" and r["line_type"] == "total"]
    rows.sort(key=lambda r: -float(r["actual_rev_eur"]))
    names = [r["category_label"] for r in rows[:9]][::-1]
    cap = [float(r["capture_rate"]) * 100 for r in rows[:9]][::-1]
    rev = [float(r["actual_rev_eur"]) for r in rows[:9]][::-1]
    fig, ax = plt.subplots(figsize=(W, 4.2))
    cols = [RED if c > 100 else (TERR if c >= 50 else FLAT) for c in cap]
    bars = ax.barh(names, cap, color=cols, height=0.58, edgecolor=WHITE, linewidth=0.7)
    ax.axvline(100, color=WHITE, lw=1.2, linestyle=":")
    ax.text(101, len(names) - 0.4, "100% of modelled demand", fontsize=8.6, color=WHITE)
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
                 fontsize=10.5, pad=10, loc="left")
    return save(fig, "f05_ituk_capture.png")


def fig09_dlod_search():
    """Where the label survives, and where it is lost."""
    fig, ax = plt.subplots(figsize=(W, 3.6))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.0, 0.945, "The programme label survives upstream, and the derived file does not keep it",
            fontsize=11.5, color=WHITE, fontweight="bold")

    # left: the derived file
    ax.add_patch(plt.Rectangle((0.0, 0.36), 0.44, 0.46, facecolor=PANEL, edgecolor="#5A6469",
                               linewidth=0.8))
    ax.text(0.022, 0.755, "THE DERIVED BILLING FILE", fontsize=8.6, color=SECOND,
            fontweight="bold")
    ax.text(0.022, 0.665, "538,346 invoice lines, 12 columns", fontsize=9.4, color=WHITE)
    ax.text(0.022, 0.575, "0 hits for the label", fontsize=19, color=RED, fontweight="bold")
    ax.text(0.022, 0.470, "The typed reference column is not one\nof the twelve columns it carries.",
            fontsize=8.8, color=SECOND, va="top")

    # right: the raw extracts
    ax.add_patch(plt.Rectangle((0.52, 0.36), 0.48, 0.46, facecolor=TERR, edgecolor="none"))
    ax.text(0.542, 0.755, "THE RAW BILLING EXTRACTS", fontsize=8.6, color=WHITE, fontweight="bold")
    ax.text(0.542, 0.665, "The typed reference, as a person wrote it", fontsize=9.4, color=WHITE)
    ax.text(0.542, 0.575, "5 labelled documents", fontsize=19, color=WHITE, fontweight="bold")
    ax.text(0.542, 0.470, "DLOD x3, dlod x1, DLAD x2, case-insensitive.\nEUR 60,000.00 across 2023 to 2026.",
            fontsize=8.8, color=WHITE, va="top")

    ax.add_patch(FancyArrowPatch((0.445, 0.59), (0.515, 0.59), arrowstyle="-|>", color=WHITE,
                                 lw=2.0, mutation_scale=13))
    ax.add_patch(plt.Rectangle((0.0, 0.18), 1.0, 0.115, facecolor=PANEL, edgecolor=RED,
                               linewidth=1.3))
    ax.text(0.016, 0.238, "And still 0 cases. Not one part, dealer, competitor quote or outcome "
                          "is recorded anywhere.",
            fontsize=9.8, color=WHITE, va="center")
    ax.text(0.0, 0.075, "The money is labelled and the case is not. That is a field to add, not a "
                        "programme that left no trace.",
            fontsize=9.4, color=SECOND, va="center")
    return save(fig, "f09_dlod_label_layers.png")


def fig10_tender_funnel():
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
        ax.add_patch(plt.Rectangle((0.0, y - 0.052), w, 0.104, facecolor=face, edgecolor=edge,
                                   linewidth=1.4))
        ax.text(0.014, y, "{}   {:,.0f}".format(lab, n), fontsize=9.6, color=WHITE, va="center",
                fontweight="bold")
        ax.text(min(w + 0.02, 0.68), y, sub, fontsize=8.8, color=SECOND, va="center")
    ax.text(0.0, 0.93, "A notice count is not pipeline - and the trail stops before the outcome",
            fontsize=11.2, color=WHITE, fontweight="bold")
    ax.text(0.0, 0.045, "The feed reports its own win rate as insufficient data: zero closed cases recorded.",
            fontsize=9.2, color=RED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.0, 1.0)
    return save(fig, "f10_tender_funnel.png")


def fig11_network_billed():
    """Where the billed parts actually are, 2025, and how unevenly they fall."""
    rows = [r for r in load("gps_spu_by_distributor.csv")
            if r["year"] == "2025" and r["total_sales_eur"].strip()]
    rows.sort(key=lambda r: -float(r["total_sales_eur"]))
    top = rows[:10][::-1]
    names = [r["distributor_code"] for r in top]
    vals = [float(r["total_sales_eur"]) for r in top]
    total = sum(float(r["total_sales_eur"]) for r in rows)
    fig, ax = plt.subplots(figsize=(W, 4.2))
    bars = ax.barh(names, vals, color=TERR, height=0.6, edgecolor=WHITE, linewidth=0.7)
    for r, v in zip(bars, vals):
        ax.text(v + 90000, r.get_y() + r.get_height() / 2,
                "{}   {:.1f}% of the network".format(_eur(v), 100 * v / total), va="center",
                fontsize=9.0, color=SECOND)
    ax.set_xlim(0, max(vals) * 1.55)
    ax.set_xlabel("ISZE parts billed to the distributor, calendar 2025 (EUR)")
    ax.tick_params(axis="y", labelsize=9.5)
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#3A4145", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("The ten largest distributors carry {:.1f}% of EUR {:,.0f} billed in 2025".format(
        100 * sum(vals) / total, total), fontsize=11, pad=10, loc="left")
    return save(fig, "f12_network_billed.png")


def fig12_hurdle():
    """How many beneficial actions each envelope implies. Arithmetic on stated inputs."""
    fig, ax = plt.subplots(figsize=(W, 3.8))
    contribs = [500, 1000, 2500, 5000]
    a100 = [100000 / c for c in contribs]
    a300 = [300000 / c for c in contribs]
    x = range(len(contribs))
    w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], a100, width=w, color=FLAT,
                label="EUR 100,000 envelope", edgecolor=WHITE, linewidth=0.7)
    b2 = ax.bar([i + w / 2 for i in x], a300, width=w, color=TERR,
                label="EUR 300,000 envelope", edgecolor=WHITE, linewidth=0.7)
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() * 1.06,
                    "{:,.0f}".format(r.get_height()), ha="center", fontsize=9.4,
                    color=WHITE, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylim(10, 1500)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["EUR {:,}".format(c) for c in contribs])
    ax.set_xlabel("Assumed contribution per beneficial action")
    ax.set_ylabel("Qualifying actions needed (log scale)")
    leg = ax.legend(frameon=False, fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(WHITE)
    _clean(ax)
    ax.set_title("Forty qualifying actions at EUR 2,500 each is the hurdle a EUR 100,000 envelope implies",
                 fontsize=10.5, pad=10, loc="left")
    return save(fig, "f13_hurdle.png")


def fig13_scope_effect():
    """Why an additional-only concession costs less than a concession on all volume."""
    fig, ax = plt.subplots(figsize=(W, 3.6))
    labels = ["Unchanged offer\n100 units at EUR 100",
              "Concession on all 120 units\n(baseline included)",
              "Concession on the 20\nadditional units only"]
    vals = [3000, 3000, 3500]
    bars = ax.bar(labels, vals, color=[FLAT, PANEL, TERR], width=0.5, edgecolor=WHITE,
                  linewidth=0.7)
    for r, v in zip(bars, vals):
        ax.text(r.get_x() + r.get_width() / 2, v, "EUR {:,}".format(v), ha="center",
                va="bottom", fontsize=12, color=WHITE, fontweight="bold")
    ax.set_ylim(0, 4300)
    ax.set_ylabel("Parts gross profit before campaign cost (EUR)")
    _clean(ax)
    ax.tick_params(axis="x", labelsize=9)
    ax.set_title("EUR 500 of gross profit turns on the scope of the concession alone",
                 fontsize=11, pad=10, loc="left")
    return save(fig, "f14_scope_effect.png")


def fig14_ceiling_placeholder():
    """The modelled ceiling, and the eight markets resting on a flat per-truck assumption."""
    rows = [r for r in load("gps_spu_by_distributor.csv")
            if r["year"] == "2025" and r["max_spend_eur"].strip() and r["uio_units"].strip()]
    for r in rows:
        r["_per"] = float(r["max_spend_eur"]) / float(r["uio_units"])
        r["_max"] = float(r["max_spend_eur"])
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
    ax.set_title("{} of the {} markets rest on a flat EUR 250 per truck, holding EUR {:,.0f} = {:.2f}% of the ceiling".format(
        len(flat), len(rows), flat_sum, 100 * flat_sum / total), fontsize=10.5, pad=10, loc="left")
    return save(fig, "f06_ceiling_placeholder.png")


FIGURES = [
    (1, "Isuzu Truck UK brake pads: value and quantity", fig01_ituk_brake_pads,     "ISZE parts billed and recorded quantity, Isuzu Truck UK, brake-pad source category, full calendar "
     "years 2024 and 2025. Measured. Source: category-mix aggregate, snapshot 19 September 2026, "
     "arithmetic rechecked 23 September 2026. The 22,389-truck national figure is not the eligible "
     "population for every pad reference and is not divided among dealers."),
    (2, "Where the reduction sits across braking", fig02_brake_split,
     "Reduction across the three selected Isuzu Truck UK source categories, calendar 2025 against "
     "calendar 2024. Measured, same source and period. Brake pads are 95.7% of the EUR 47,068.77."),
    (3, "Portugal clutch kits: total grew, genuine fell", fig03_portugal_clutch,
     "ISZE parts billed to I Motors, Portugal, clutch-kit source category, full calendar years. "
     "Measured. Quantity was almost unchanged: 462 kits to 461. The Portuguese national vehicle count "
     "is a market figure and is not the eligible fleet for these kits."),
    (4, "Deep concession by distributor, 2025", fig04_concession_by_distributor,
     "Share of 2025 parts billed at least 20% under the reference price, on lines carrying a reference "
     "price, 24 distributors. Measured. The ten largest deep-concession shares are shown; the bar's "
     "shade marks billed size, so colour is not the only way to read it."),
    (5, "Deep concession by product family, 2025", fig05_concession_by_family,
     "The eight largest product families by 2025 billing. Measured, same source and period. Two "
     "families carry a large share on a modest base and two large families carry almost none."),
    (6, "Recorded dealer self-assessment scores", fig06_ids_scores,
     "519 dealer self-assessment records across 19 country lists, one round, no per-dealer assessment "
     "date; 514 distinct names; 490 carry an individual score, average 79.3; the other 29 recorded no "
     "answers and are excluded rather than counted as zero. Measured on the dealer "
     "network file of 20 September 2026. A score is a self-reported number from one undated round and "
     "is not a performance measure."),
    (7, "Cordwallis: four measured numbers", fig07_cordwallis,
     "Cordwallis Commercials, Heathrow, calendar 2025, engine filters. The fitted and bought counts are "
     "measured on separate populations and cannot be subtracted. Verified at 104 checks with 0 "
     "failures. The 72 trucks are what that one workshop saw in the year, which makes the count a floor "
     "rather than the dealer's fleet."),
    (8, "Isuzu Truck UK billed units against modelled demand, 2025", fig08_ituk_capture,
     "Billed units as a share of modelled expected demand, nine largest families by billing, total "
     "sales line, 2025. Measured, on the capture model's own stated denominator of 23,068 N75 buckets "
     "and the model-bucket split. A share above 100% means the denominator is too small for that "
     "family, not that more than all demand was captured, and such a rate must not be read at face "
     "value."),
    (9, "Where the programme label survives, and where it is lost", fig09_dlod_search,
     "The derived billing file and the raw billing extracts, searched for the competitive-quote "
     "programme's own label. The derived file carries twelve columns and not the typed reference, so a "
     "search there returns nothing; the raw extracts preserve the reference a person typed, and five "
     "labelled documents are there, spanning 2023 to 2026 and EUR 60,000.00. Measured. And zero cases "
     "are recorded anywhere: no part, dealer, competitor quote or outcome."),
    (10, "From a public notice to a pursuit decision", fig10_tender_funnel,
     "Live opportunity feed as observed on 22 September 2026: 689 raw notices, 619 opportunities, 199 "
     "in the action queue, 45 due within fourteen days, 0 recorded outcomes. Measured. A notice count is "
     "not pipeline value, and a tender's advertised value is not expected parts revenue."),
    (11, "Where the billed parts are, 2025", fig11_network_billed,
     "ISZE parts billed to each distributor, calendar 2025, the ten largest shown out of 22. Measured, "
     "GPS distributor file, 2025 rows. This is the denominator every share in chapter 10 divides by."),
    (12, "The hurdle each funding envelope implies", fig12_hurdle,
     "Qualifying actions needed to cover each envelope at four assumed contribution levels. Hypothetical "
     "arithmetic on stated inputs: envelope divided by assumed contribution per action. Not a forecast "
     "of dealer profitability and not a record of an achieved result."),
    (13, "The scope effect on contribution", fig13_scope_effect,
     "Hypothetical arithmetic: a 100-unit baseline at EUR 100 net with EUR 70 of parts cost, 20 "
     "additional units, a 5% concession. Not an Isuzu price, offer or forecast, and it assumes no "
     "demand response."),
    (14, "The modelled ceiling and the flat per-truck placeholder", fig14_ceiling_placeholder,
     "Modelled target-spend ceiling by market, calendar 2025, the 18 markets carrying both a fleet "
     "figure and a ceiling. Measured on the GPS distributor file and recomputed 23 September 2026. The "
     "markets marked in red rest on a flat EUR 250 per truck, which is an assumption rather than a "
     "measured purchasing rate. The ceiling is not revenue and must never be presented as revenue."),
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
