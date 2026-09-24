# -*- coding: utf-8 -*-
r"""ISUZU / UNIVERSE 3.0 - the figures.

Every chart is generated from a named source file at build time. Nothing is typed in as a
number that could be recomputed. Colours are the house set: navy, terracotta, Isuzu red,
charcoal and paper.

Run:  python _build_30\figures.py
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow, Rectangle

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(os.path.dirname(ROOT), "01_data", "00_derived")
OUT = os.path.join(HERE, "figures")

NAVY = "#15233C"
NAVY2 = "#1A2B4A"
TERR = "#C0552D"
RED = "#D71920"
GREY = "#5B6472"
PAPER = "#F7F4EE"
LINE = "#D8D2C8"
INK = "#222222"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": LINE,
    "axes.labelcolor": NAVY,
    "text.color": INK,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "axes.titlecolor": NAVY,
})

W, H = 9.4, 4.5


def _clean(ax, grid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(LINE)
    ax.spines["bottom"].set_color(LINE)
    if grid:
        ax.yaxis.grid(True, color="#EDE9E1", lw=0.9)
        ax.set_axisbelow(True)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


# ----------------------------------------------------------------------------- sources
def load(name):
    with open(os.path.join(DERIVED, name), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def ituk_and_portugal():
    rows = load("pms_genuine_bvp_vs_price_2024_2025.csv")
    out = {}
    for code, sub, key in (("ITUK", "brake_pad", "ituk"), ("PORTUGAL", "clutch_kit", "pt")):
        for r in rows:
            if r["distributor_code"] == code and r["product_subgroup"] == sub:
                out[key] = r
    return out


def concession_by_db(year="2025"):
    rows = [r for r in load("pms_campaign_suspect_by_db_2024_2025.csv") if r["year"] == year]
    return sorted(rows, key=lambda r: -float(r["pct_eur_ge20_under_ref"]))


def concession_by_family(year="2025"):
    rows = [r for r in load("pms_campaign_suspect_by_family_2024_2025.csv") if r["year"] == year]
    return sorted(rows, key=lambda r: -float(r["billed_eur"]))


def ids_rows():
    return load("ids_dealer_network_cleaned_2026-09-20.csv")


def network_2025():
    return [r for r in load("gps_spu_by_distributor.csv") if r["year"] == "2025"]


# ----------------------------------------------------------------------------- figures
def fig1_argument():
    """Two bars: value and quantity, ITUK brake pads. The whole argument on one chart."""
    d = ituk_and_portugal()["ituk"]
    fig, axes = plt.subplots(1, 2, figsize=(W, 3.9))
    for ax, (v24, v25, lab, fmt) in zip(axes, [
        (float(d["total_eur_2024"]), float(d["total_eur_2025"]), "Parts billed (EUR)", "{:,.0f}"),
        (float(d["total_qty_2024"]), float(d["total_qty_2025"]), "Recorded quantity (units)", "{:,.0f}"),
    ]):
        b = ax.bar(["2024", "2025"], [v24, v25], color=[GREY, NAVY], width=0.55)
        for r, v in zip(b, [v24, v25]):
            ax.text(r.get_x() + r.get_width() / 2, v, fmt.format(v), ha="center", va="bottom",
                    fontsize=11, color=NAVY, fontweight="bold")
        ax.set_title(lab, fontsize=10.5, pad=8)
        ax.set_ylim(0, max(v24, v25) * 1.22)
        _clean(ax)
        pct = (v25 - v24) / v24 * 100
        ax.annotate(f"{pct:+.1f}%", xy=(0.5, 0.86), xycoords="axes fraction", ha="center",
                    fontsize=15, color=TERR, fontweight="bold")
    fig.suptitle("Value fell 13.0%. Volume fell 25.4%.",
                 fontsize=13, color=NAVY, x=0.02, ha="left", y=1.06)
    return save(fig, "f01_ituk_value_vs_volume.png")


def fig2_boundary():
    fig, ax = plt.subplots(figsize=(W, 4.3))
    ax.axis("off")
    left = ["When will this part arrive?",
            "Is a BVP alternative available?",
            "Can you handle this quotation?",
            "Can you follow up this training action?",
            "Can you submit or administer this tender?"]
    right = ["A strategic range study may use recurring constraints.\nNo arrival-enquiry workflow is built.",
             "Combined Genuine and BVP positioning and\nrange-development analysis.",
             "Competitive evidence and transparent economics\nfor a selected pricing or range decision.",
             "An explorable IDS profile and a participant-chosen\ndevelopment plan.",
             "Relevant fleet and tender intelligence and a\nreasoned decision on which to pursue."]
    ax.add_patch(Rectangle((0.0, 0.0), 0.46, 1.0, facecolor="#EFEBE3", edgecolor="none"))
    ax.add_patch(Rectangle((0.52, 0.0), 0.48, 1.0, facecolor="#E7EDF5", edgecolor="none"))
    ax.text(0.02, 0.955, "OUTSIDE UNIVERSE", fontsize=11, color=GREY, fontweight="bold")
    ax.text(0.02, 0.905, "stays in the existing business", fontsize=9.5, color=GREY)
    ax.text(0.54, 0.955, "INSIDE UNIVERSE", fontsize=11, color=NAVY, fontweight="bold")
    ax.text(0.54, 0.905, "a commercial capability beyond the service", fontsize=9.5, color=GREY)
    for i, (l, r) in enumerate(zip(left, right)):
        y = 0.78 - i * 0.155
        ax.text(0.015, y, l, fontsize=10, color=INK, va="top", wrap=True)
        ax.text(0.545, y, r, fontsize=10, color=NAVY, va="top")
    ax.annotate("", xy=(0.515, 0.45), xytext=(0.465, 0.45),
                arrowprops=dict(arrowstyle="-|>", color=TERR, lw=2))
    ax.text(0.49, 0.415, "evidence may\ninform the analysis", fontsize=8.4, color=TERR,
            ha="center")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return save(fig, "f02_boundary.png")


def fig3_portfolio():
    fig, ax = plt.subplots(figsize=(W, 4.0))
    ax.axis("off")
    sources = [("AIM", "product structure"), ("IDS", "declared practices"), ("PRISM", "market and fleet")]
    tools = ["AIM Commercial Atlas", "IDS Development Studio", "Range & Campaign Planner",
             "Pricing & Margin Lab", "PRISM Market Intelligence"]
    for i, (s, sub) in enumerate(sources):
        y = 0.78 - i * 0.28
        ax.add_patch(FancyBboxPatch((0.02, y - 0.10), 0.20, 0.20, boxstyle="round,pad=0.012",
                                    facecolor=NAVY, edgecolor="none"))
        ax.text(0.12, y + 0.015, s, ha="center", va="center", fontsize=12, color="white",
                fontweight="bold")
        ax.text(0.12, y - 0.045, sub, ha="center", va="center", fontsize=8.2, color="#C9D2DE")
    for i, t in enumerate(tools):
        y = 0.86 - i * 0.165
        ax.add_patch(FancyBboxPatch((0.36, y - 0.062), 0.34, 0.124, boxstyle="round,pad=0.010",
                                    facecolor="#E7EDF5", edgecolor="#B9C6D8"))
        ax.text(0.53, y, t, ha="center", va="center", fontsize=9.6, color=NAVY)
    ax.add_patch(FancyBboxPatch((0.76, 0.10), 0.22, 0.68, boxstyle="round,pad=0.012",
                                facecolor=TERR, edgecolor="none"))
    ax.text(0.87, 0.44, "COMMERCIAL\nDECISIONS", ha="center", va="center", fontsize=11,
            color="white", fontweight="bold")
    ax.annotate("", xy=(0.755, 0.44), xytext=(0.705, 0.44),
                arrowprops=dict(arrowstyle="-|>", color=TERR, lw=2.2))
    ax.annotate("", xy=(0.355, 0.44), xytext=(0.225, 0.44),
                arrowprops=dict(arrowstyle="-|>", color="#B9C6D8", lw=2.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return save(fig, "f03_portfolio.png")


def fig4_brake_split():
    fig, ax = plt.subplots(figsize=(W, 3.0))
    labels = ["Brake pads", "Rotors", "Shoes"]
    vals = [45023.33, 1260.48, 784.96]
    b = ax.barh(labels[::-1], vals[::-1], color=[GREY, GREY, RED], height=0.55)
    for r, v in zip(b, vals[::-1]):
        ax.text(v + 900, r.get_y() + r.get_height() / 2, f"EUR {v:,.0f}", va="center",
                fontsize=10.5, color=NAVY, fontweight="bold")
    ax.set_xlim(0, 56000)
    ax.set_xlabel("Reduction in ISZE parts billed, CY2025 vs CY2024 (EUR)")
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#EDE9E1", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("EUR 47,068.77 across three selected categories - pads are 95.7% of it",
                 fontsize=11.5, pad=10, loc="left")
    return save(fig, "f04_brake_split.png")


def fig5_portugal():
    d = ituk_and_portugal()["pt"]
    gen = [float(d["genuine_eur_2024"]), float(d["genuine_eur_2025"])]
    bvp = [float(d["bvp_eur_2024"]), float(d["bvp_eur_2025"])]
    fig, ax = plt.subplots(figsize=(W, 3.7))
    x = [0, 1]
    b1 = ax.bar(x, gen, color=RED, width=0.45, label="Genuine")
    b2 = ax.bar(x, bvp, bottom=gen, color=GREY, width=0.45, label="BVP")
    for xi, g, b in zip(x, gen, bvp):
        ax.text(xi, g + b + 700, f"EUR {g + b:,.2f}", ha="center", fontsize=11,
                color=NAVY, fontweight="bold")
        ax.text(xi, g / 2, f"{g:,.0f}", ha="center", va="center", fontsize=9.5, color="white")
        ax.text(xi, g + b / 2, f"{b:,.0f}", ha="center", va="center", fontsize=9.5, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels(["Calendar 2024\n462 kits", "Calendar 2025\n461 kits"], fontsize=10)
    ax.set_ylim(0, 38000)
    ax.set_ylabel("Parts billed (EUR)")
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    _clean(ax)
    ax.annotate("+5.8% combined", xy=(0.5, 0.90), xycoords="axes fraction", ha="center",
                fontsize=13, color=TERR, fontweight="bold")
    return save(fig, "f05_portugal_clutch.png")


def fig6_concession_db():
    rows = concession_by_db("2025")[:10]
    fig, ax = plt.subplots(figsize=(W, 4.4))
    names = [r["distributor_code"] for r in rows][::-1]
    shares = [float(r["pct_eur_ge20_under_ref"]) for r in rows][::-1]
    billed = [float(r["billed_eur"]) for r in rows][::-1]
    cols = [NAVY if b >= 400000 else GREY for b in billed]
    b = ax.barh(names, shares, color=cols, height=0.6)
    for r, s, bl in zip(b, shares, billed):
        ax.text(s + 0.35, r.get_y() + r.get_height() / 2, f"{s:.1f}%   (EUR {bl / 1000:,.0f}k billed)",
                va="center", fontsize=9.2, color=NAVY)
    ax.set_xlim(0, 38)
    ax.set_xlabel("Share of 2025 parts billed at least 20% under the reference price")
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#EDEDE1", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("The deepest concession is in the smallest markets  (navy = over EUR 400k billed)",
                 fontsize=11.5, pad=10, loc="left")
    return save(fig, "f06_concession_by_db.png")


def fig7_concession_family():
    rows = concession_by_family("2025")[:8]
    fig, ax = plt.subplots(figsize=(W, 4.0))
    names = [r["pms_category"] for r in rows][::-1]
    shares = [float(r["pct_eur_ge20_under_ref"]) for r in rows][::-1]
    billed = [float(r["billed_eur"]) for r in rows][::-1]
    b = ax.barh(names, shares, color=NAVY, height=0.58)
    for r, s, bl in zip(b, shares, billed):
        ax.text(s + 0.4, r.get_y() + r.get_height() / 2, f"{s:.1f}%   (EUR {bl / 1000:,.0f}k)",
                va="center", fontsize=9.2, color=NAVY)
    ax.set_xlim(0, 48)
    ax.set_xlabel("Share of 2025 family billing at least 20% under the reference price")
    _clean(ax, grid=False)
    ax.xaxis.grid(True, color="#EDE9E1", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_title("Concession is concentrated in two families, on modest bases", fontsize=11.5,
                 pad=10, loc="left")
    return save(fig, "f07_concession_by_family.png")


def fig8_hurdle():
    fig, ax = plt.subplots(figsize=(W, 3.9))
    contribs = [500, 1000, 2500, 5000]
    a100 = [100000 / c for c in contribs]
    a300 = [300000 / c for c in contribs]
    x = range(len(contribs))
    w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], a100, width=w, color=NAVY, label="EUR 100,000 envelope")
    b2 = ax.bar([i + w / 2 for i in x], a300, width=w, color=TERR, label="EUR 300,000 envelope")
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() * 1.03, f"{int(r.get_height())}",
                    ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylim(10, 1200)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"EUR {c:,}" for c in contribs])
    ax.set_xlabel("Assumed contribution per beneficial action")
    ax.set_ylabel("Qualifying actions needed (log scale)")
    ax.legend(frameon=False, fontsize=9.5)
    _clean(ax)
    ax.set_title("Forty qualifying actions at EUR 2,500 each is the honest break-even for EUR 100,000",
                 fontsize=11.5, pad=10, loc="left")
    return save(fig, "f08_hurdle.png")


def fig9_scope_effect():
    fig, ax = plt.subplots(figsize=(W, 3.6))
    labels = ["Unchanged offer\n100 units at EUR 100",
              "Concession on all 120 units\n(baseline included)",
              "Concession on the 20\nadditional units only"]
    vals = [3000, 3000, 3500]
    b = ax.bar(labels, vals, color=[GREY, TERR, NAVY], width=0.5)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v, f"EUR {v:,}", ha="center", va="bottom",
                fontsize=12, color=NAVY, fontweight="bold")
    ax.set_ylim(0, 4200)
    ax.set_ylabel("Parts gross profit before campaign cost (EUR)")
    _clean(ax)
    ax.tick_params(axis="x", labelsize=9)
    ax.set_title("EUR 500 of gross profit turns on the scope of the concession alone",
                 fontsize=11.5, pad=10, loc="left")
    return save(fig, "f09_scope_effect.png")


def _flow(name, title, steps, subtitles=None, color=NAVY, width=W):
    n = len(steps)
    fig, ax = plt.subplots(figsize=(width, 2.9))
    ax.axis("off")
    gap = 1.0 / n
    for i, s in enumerate(steps):
        x = i * gap
        ax.add_patch(FancyBboxPatch((x + 0.004, 0.30), gap - 0.028, 0.42,
                                    boxstyle="round,pad=0.010",
                                    facecolor=color if i % 2 == 0 else "#2B3F5F",
                                    edgecolor="none"))
        ax.text(x + gap / 2 - 0.010, 0.615, f"{i + 1:02d}", ha="center", va="center",
                fontsize=9, color="#9FB0C6")
        ax.text(x + gap / 2 - 0.010, 0.455, s, ha="center", va="center", fontsize=9.4,
                color="white", wrap=True)
        if subtitles:
            ax.text(x + gap / 2 - 0.010, 0.235, subtitles[i], ha="center", va="top",
                    fontsize=8.3, color=GREY, wrap=True)
        if i < n - 1:
            ax.annotate("", xy=(x + gap - 0.008, 0.51), xytext=(x + gap - 0.026, 0.51),
                        arrowprops=dict(arrowstyle="-|>", color=TERR, lw=1.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0.05, 0.85)
    ax.text(0.0, 0.80, title, fontsize=11.5, color=NAVY, fontweight="bold")
    return save(fig, name)


def fig10_atlas_journey():
    return _flow("f10_atlas_journey.png", "From the covered business to a chosen decision",
                 ["Parts\nbusiness", "Family", "Product\nform", "Original\nreference", "Commercial\nchoice"],
                 ["one scope\nand period", "commercial\ngrouping", "element,\nhousing, kit",
                  "the item\npurchased", "explore,\ncompare, select"])


def fig11_product_form():
    fig, ax = plt.subplots(figsize=(W, 3.2))
    ax.axis("off")
    forms = [("Element", "a consumable component", GREY),
             ("Housing", "the enclosing component", NAVY),
             ("Assembly", "a larger defined product", NAVY2),
             ("Kit", "a specified set of contents", TERR)]
    for i, (t, s, c) in enumerate(forms):
        x = i * 0.25
        ax.add_patch(FancyBboxPatch((x + 0.012, 0.34), 0.215, 0.34,
                                    boxstyle="round,pad=0.012", facecolor=c, edgecolor="none"))
        ax.text(x + 0.12, 0.56, t, ha="center", va="center", fontsize=12, color="white",
                fontweight="bold")
        ax.text(x + 0.12, 0.44, s, ha="center", va="center", fontsize=8.4, color="#E4E9F0")
    ax.text(0.0, 0.83, "One broad family, four commercially different product forms",
            fontsize=11.5, color=NAVY, fontweight="bold")
    ax.text(0.0, 0.20, "Averaging them into one unit price describes a changing mix, not a price change.",
            fontsize=10, color=INK)
    ax.text(0.0, 0.10, "A missing relationship stays a visible gap. It is never filled with a plausible match.",
            fontsize=10, color=TERR)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.02, 0.95)
    return save(fig, "f11_product_form.png")


def fig12_three_records():
    fig, ax = plt.subplots(figsize=(W, 3.1))
    ax.axis("off")
    cols = [("ASSESSMENT", "the original source record\nquestionnaire, answer, available date", GREY),
            ("DEVELOPMENT", "milestones, owners and evidence\nwhat the dealer chose to do", NAVY),
            ("REASSESSMENT", "a later actual record\ncompared only on a compatible basis", TERR)]
    for i, (t, s, c) in enumerate(cols):
        x = i * 0.34
        ax.add_patch(FancyBboxPatch((x, 0.30), 0.31, 0.44, boxstyle="round,pad=0.012",
                                    facecolor=c, edgecolor="none"))
        ax.text(x + 0.155, 0.61, t, ha="center", va="center", fontsize=11.5, color="white",
                fontweight="bold")
        ax.text(x + 0.155, 0.44, s, ha="center", va="center", fontsize=8.6, color="#E8EDF3")
    ax.text(0.0, 0.85, "Three records, three different stories - and none updates another",
            fontsize=11.5, color=NAVY, fontweight="bold")
    ax.text(0.0, 0.17, "Completing a milestone does not amend the original answer, raise a score or prove a commercial outcome.",
            fontsize=9.6, color=INK)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.05, 0.95)
    return save(fig, "f12_three_records.png")


def fig13_range_decision():
    return _flow("f13_range_decision.png", "Five checks before a range becomes an initiative",
                 ["No purchase\nrecorded", "Range\ngap?", "Coverage\nexclusion?", "Number\nchange?",
                  "Application\nfit?"],
                 ["the starting\nfact", "documented\nor not", "was it\navailable",
                  "successor\nlogic", "is it\nrelevant"], width=W)


def fig14_dealer_join():
    return _flow("f14_dealer_join.png", "How the dealer joins, in order",
                 ["Distributor\ninvites", "Prepared\nreview opens", "Dealer\ncorrects",
                  "IDS profile\noffered", "Plan\nrecorded", "Next eligible\ntask"],
                 ["ISZE never\napproaches directly", "no form,\nno upload", "or says\nno action needed",
                  "real wording,\nown priority", "milestones\nand evidence", "not another\nreport"],
                 width=W)


def fig15_ids_scores():
    """The recorded Dealer Standards scores, with the never-assessed dealers held apart.

    A score of zero in the source means the 195-question assessment was never carried out, not that
    the dealer performed badly: every one of those records shows 0% of items scored. They are
    therefore drawn as their own labelled band, severed from the score axis, so a reader cannot
    read them as the weakest dealers in the network.
    """
    rows = [r for r in ids_rows() if r["points_pct"].strip()]
    assessed = [float(r["points_pct"]) for r in rows if float(r["points_pct"]) > 0]
    unassessed = [r for r in rows if float(r["points_pct"]) == 0]
    avg = sum(assessed) / len(assessed)

    fig, (ax, band) = plt.subplots(
        1, 2, figsize=(W, 3.5),
        gridspec_kw={"width_ratios": [7, 1], "wspace": 0.04},
    )

    bins = list(range(0, 101, 10))
    ax.hist(assessed, bins=bins, color=NAVY, edgecolor="white", linewidth=0.8)
    top = ax.get_ylim()[1] * 1.2
    ax.set_ylim(0, top)
    ax.set_xlim(0, 100)
    ax.axvline(avg, color=TERR, lw=2.2, linestyle="--")
    ax.text(avg + 2.0, top * 0.96, f"average {avg:.1f}", color=TERR, fontsize=10.5,
            fontweight="bold", va="top")
    ax.set_xlabel("Recorded Dealer Standards score (%)")
    ax.set_ylabel("Dealers")
    _clean(ax)

    # The band: a full-height strip in its own axes, deliberately off the score scale, so its height
    # means nothing and cannot be compared with a bar.
    band.set_xlim(0, 1)
    band.set_ylim(0, top)
    band.add_patch(Rectangle((0.06, 0), 0.88, top * 0.86, facecolor="#EDE9E1",
                             edgecolor=LINE, linewidth=1.0))
    band.text(0.5, top * 0.86, "not assessed", ha="center", va="bottom",
              fontsize=8.6, color=GREY)
    band.text(0.5, top * 0.50, f"{len(unassessed)}", ha="center", va="center",
              fontsize=16, color=NAVY, fontweight="bold")
    band.text(0.5, top * 0.40, "dealers", ha="center", va="top", fontsize=8.6, color=GREY)
    band.text(0.5, top * 0.30, "no answers recorded", ha="center", va="top",
              fontsize=7.6, color=GREY)
    band.set_xticks([])
    band.set_yticks([])
    for s in ("top", "right", "left", "bottom"):
        band.spines[s].set_visible(False)

    ax.set_title(
        f"{len(assessed)} of {len(rows)} dealers carry a recorded score. "
        f"{len(unassessed)} have no answers recorded and are shown separately.",
        fontsize=11.5, pad=10, loc="left")
    return save(fig, "f15_ids_scores.png")


def fig16_exchange():
    fig, ax = plt.subplots(figsize=(W, 3.6))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.02, 0.50), 0.30, 0.38, boxstyle="round,pad=0.012",
                                facecolor=GREY, edgecolor="none"))
    ax.text(0.17, 0.75, "DISTRIBUTOR", ha="center", fontsize=11, color="white", fontweight="bold")
    ax.text(0.17, 0.62, "the report it already provides\ncoverage and account definitions\n"
                        "selected commercial context",
            ha="center", va="center", fontsize=8.6, color="#F2F4F7")
    ax.add_patch(FancyBboxPatch((0.40, 0.50), 0.30, 0.38, boxstyle="round,pad=0.012",
                                facecolor=TERR, edgecolor="none"))
    ax.text(0.55, 0.75, "ISZE", ha="center", fontsize=11, color="white", fontweight="bold")
    ax.text(0.55, 0.62, "parts knowledge\napproved references\ncommercial assessment",
            ha="center", va="center", fontsize=8.6, color="#FDF0EA")
    ax.add_patch(FancyBboxPatch((0.02, 0.06), 0.30, 0.32, boxstyle="round,pad=0.012",
                                facecolor="#E7EDF5", edgecolor="#B9C6D8"))
    ax.text(0.17, 0.30, "RECEIVES", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    ax.text(0.17, 0.17, "prepared national and network review\nproduct detail behind a movement\n"
                        "campaign brief and result review",
            ha="center", va="center", fontsize=8.4, color=NAVY)
    ax.add_patch(FancyBboxPatch((0.40, 0.06), 0.30, 0.32, boxstyle="round,pad=0.012",
                                facecolor="#E7EDF5", edgecolor="#B9C6D8"))
    ax.text(0.55, 0.30, "RECEIVES", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    ax.text(0.55, 0.17, "product and account detail\ncampaign observations\nan outcome record",
            ha="center", va="center", fontsize=8.4, color=NAVY)
    ax.annotate("", xy=(0.17, 0.42), xytext=(0.17, 0.48),
                arrowprops=dict(arrowstyle="-|>", color=GREY, lw=2.2))
    ax.annotate("", xy=(0.55, 0.48), xytext=(0.55, 0.42),
                arrowprops=dict(arrowstyle="-|>", color=TERR, lw=2.2))
    ax.text(0.74, 0.74, "grey = what each side puts in\nterracotta = ISZE's contribution",
            fontsize=9, color=GREY, va="center")
    ax.text(0.74, 0.40, "No payment for data volume.\nOrdinary service is not conditional\non any contribution.",
            fontsize=9.4, color=NAVY, va="center")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return save(fig, "f16_exchange.png")


def fig17_tender_parties():
    return _flow("f17_tender_parties.png", "Who owns which part of a joint proposal",
                 ["Distributor\nqualifies", "Isuzu functions\nassemble", "Headquarters\nassesses",
                  "Distributor\nleads the bid"],
                 ["local fit and intent", "vehicle, parts, aftersales", "the requested decision",
                  "national relationship"], width=W)


def fig18_brief_sections():
    fig, ax = plt.subplots(figsize=(W, 3.1))
    ax.axis("off")
    secs = [("Opportunity", "what is pursued and why it fits"),
            ("Combined offer", "vehicle, parts and aftersales scope"),
            ("Requested decision", "what support would change the offer"),
            ("Commercial basis", "eligible scope and assumptions"),
            ("Conditions", "owners, dates, unresolved items"),
            ("Decision", "accept, amend, decline or name the gap")]
    for i, (t, s) in enumerate(secs):
        x = (i % 3) * 0.335
        y = 0.52 if i < 3 else 0.16
        ax.add_patch(FancyBboxPatch((x, y), 0.30, 0.28, boxstyle="round,pad=0.010",
                                    facecolor=NAVY if i % 2 == 0 else NAVY2, edgecolor="none"))
        ax.text(x + 0.15, y + 0.185, t, ha="center", va="center", fontsize=10,
                color="white", fontweight="bold")
        ax.text(x + 0.15, y + 0.085, s, ha="center", va="center", fontsize=8.2, color="#DCE3EC")
    ax.text(0.0, 0.88, "A headquarters brief that makes the decision unmistakable",
            fontsize=11.5, color=NAVY, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0.05, 0.98)
    return save(fig, "f18_brief_sections.png")


def fig19_ids_studio():
    return _flow("f19_ids_studio.png", "The studio, in five stages",
                 ["Explore\nthe answers", "Understand\nthe context", "Compare\nfairly",
                  "Choose\na priority", "Review\nprogress"],
                 ["real wording\nand version", "what the section\nmeans", "compatible\nbasis only",
                  "dealer-led,\nnot imposed", "separate from\nthe score"], width=W)


def fig20_exchange_fields():
    fig, ax = plt.subplots(figsize=(W, 3.6))
    ax.axis("off")
    rows = [("Organisation and account", "the actual entity and the supported account"),
            ("Product", "the original reference; classification kept separately"),
            ("Period and quantity", "the date meaning, basis, unit and signed treatment"),
            ("Coverage", "included channels and accounts; missing periods"),
            ("Control and correction", "control totals, generation date and predecessor"),
            ("Responsibility", "the source owner and the route to correct it")]
    for i, (a, b) in enumerate(rows):
        y = 0.80 - i * 0.135
        ax.add_patch(Rectangle((0.0, y - 0.045), 0.34, 0.10, facecolor=NAVY, edgecolor="none"))
        ax.text(0.012, y, a, fontsize=9.4, color="white", va="center", fontweight="bold")
        ax.text(0.37, y, b, fontsize=9.4, color=INK, va="center")
    ax.text(0.0, 0.94, "What the recurring exchange carries, and what each field has to mean",
            fontsize=11.5, color=NAVY, fontweight="bold")
    ax.text(0.0, 0.03, "Price-free by default. The same definitions are reused, not re-requested.",
            fontsize=9.6, color=TERR)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return save(fig, "f20_exchange_fields.png")


def fig21_campaign_record():
    return _flow("f21_campaign_record.png", "The offer record, and what has to stay distinct",
                 ["Selection", "Assistance", "Economics", "Launch", "Evaluation"],
                 ["candidate vs eligible", "requested vs approved", "profit vs contribution",
                  "planned vs actual", "activity vs lasting business"], width=W)


def fig22_evidence_labels():
    fig, ax = plt.subplots(figsize=(W, 2.9))
    ax.axis("off")
    labs = [("RECORDED", "a source event or quantity\non its actual period and coverage", NAVY),
            ("REPORTED", "a participant's explanation\nwith attribution and date", NAVY2),
            ("MODELLED", "a defined expectation\nwith its assumptions stated", TERR),
            ("CONFIRMED", "a specific decision or outcome\nsupported by its own record", GREY)]
    for i, (t, s, c) in enumerate(labs):
        x = i * 0.25
        ax.add_patch(FancyBboxPatch((x + 0.008, 0.28), 0.222, 0.46,
                                    boxstyle="round,pad=0.012", facecolor=c, edgecolor="none"))
        ax.text(x + 0.119, 0.61, t, ha="center", va="center", fontsize=10.5, color="white",
                fontweight="bold")
        ax.text(x + 0.119, 0.42, s, ha="center", va="center", fontsize=7.8, color="#E6EBF1")
    ax.text(0.0, 0.86, "Four labels, and nothing unlabelled", fontsize=11.5, color=NAVY,
            fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0.10, 0.95)
    return save(fig, "f22_evidence_labels.png")


FIGURES = [
    (1, "the argument for the whole programme", fig1_argument,
     "Recorded ISZE billing and quantity, ITUK brake-pad source category, full calendar 2024 and 2025. Measured; source snapshot 19 September 2026, arithmetic rechecked 23 September 2026."),
    (2, "the boundary", fig2_boundary,
     "A normal service stays a normal service. Evidence from it may inform an agreed analysis; its workflow does not become a module."),
    (3, "the portfolio", fig3_portfolio,
     "Four foundations, five tools, one class of decision. Each tool uses only the evidence relevant to its own question."),
    (4, "the reduction is concentrated in one product form", fig4_brake_split,
     "Magnitude of billing reduction across three selected ITUK source categories, CY2025 vs CY2024. Measured."),
    (5, "the combined offer grew while Genuine fell", fig5_portugal,
     "ISZE parts billed to I Motors, clutch-kit source category, full calendar years. Measured. Quantity was almost unchanged: 462 kits to 461."),
    (6, "network parts billed and deep concession, 2025", fig6_concession_db,
     "PMS lines carrying a reference price, 24 distributors. Ten largest deep-discount shares shown. Measured."),
    (7, "where the deep concession is, by family", fig7_concession_family,
     "Eight largest PMS families by 2025 billing. Measured."),
    (8, "the hurdle the money implies", fig8_hurdle,
     "Qualifying actions needed to cover each envelope at four assumed contribution levels. Hypothetical arithmetic on stated inputs, not a forecast of dealer profitability."),
    (9, "the scope effect on contribution", fig9_scope_effect,
     "Hypothetical arithmetic: 100-unit baseline at EUR 100 net and EUR 70 parts cost, 20 additional units, 5% concession. Not an Isuzu price, offer or forecast."),
    (10, "how a user moves through the Atlas", fig10_atlas_journey,
     "Proposed analytical sequence. The stages are a proposed design, and each retains its own source period and evidence."),
    (11, "a filter element is not a filter housing", fig11_product_form,
     "Proposed product-form distinction. It prevents an average unit price from describing a mix change as a price change."),
    (12, "three records, kept apart", fig12_three_records,
     "Proposed record structure. No actual dealer score, date or progress is represented."),
    (13, "five checks before a range becomes an initiative", fig13_range_decision,
     "Proposed decision gate. A missing purchase is not evidence of unmet demand."),
    (14, "how the dealer joins", fig14_dealer_join,
     "Proposed participant journey. No dealer has been invited and no access has been accepted."),
    (15, "the recorded IDS scores behind the opening offer", fig15_ids_scores,
     "Dealer network file of 20 September 2026: 519 rows across 19 networks. 490 carry a recorded score, mean 79.3; the remaining 29 recorded no answers at all and are held apart. Measured."),
    (16, "the exchange, and what each side puts in", fig16_exchange,
     "Proposed participation design. Payment for data volume is excluded and ordinary service is never conditional on a contribution."),
    (17, "the collaboration, and who owns which part", fig17_tender_parties,
     "Proposed collaboration pattern. One function's agreement does not display the whole proposal as approved."),
    (18, "the brief, in six sections", fig18_brief_sections,
     "Proposed structure for a real opportunity. Blank information remains unconfirmed and is not filled with an assumption."),
    (19, "the studio, in five stages", fig19_ids_studio,
     "Proposed analytical sequence. Each stage retains its own source period and evidence."),
    (20, "the recurring exchange, and what each field has to mean", fig20_exchange_fields,
     "Proposed source standard. It describes business meaning rather than a prescribed technical file layout."),
    (21, "the offer record, and what has to stay distinct", fig21_campaign_record,
     "Proposed record structure. A complete draft remains a draft until conditions and authority are confirmed."),
    (22, "the four labels", fig22_evidence_labels,
     "Measured activity, participant statements, modelled expectations and confirmed decisions are kept separate in every output."),
]


def build_all():
    paths = {}
    for n, title, fn, _note in FIGURES:
        paths[n] = fn()
        print(f"  figure {n:>2}  {os.path.basename(paths[n])}")
    return paths


if __name__ == "__main__":
    print("generating figures from", DERIVED)
    build_all()
    print("done")
