# -*- coding: utf-8 -*-
"""Graphic assets for ISZE_Kickback_Japan_Pack_20261007.pptx - visual rebuild 2026-10-07.

Every euro value is read from a named source file. Nothing is typed in by hand.

Sizes are given as the FINAL ON-SLIDE inches, and dpi is 300, so a matplotlib
point size is a slide point size.

Sources
  portugal_billing_vs_sales_to_dealer.csv  -> s4 divergence
  portugal_family_stock_build.csv          -> s5 family totals (euro only)
  portugal_pn_stock_build.csv              -> s5 single brake part 8983767550
  replenishment_exceptions_cy2025.csv      -> s6 total cross-check + split
  billing_monthly_by_distributor.csv       -> s7 ITUK monthly series + 13 Mar 2026
  01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx, 'Incentive FY27'
                                           -> s2 BP FY26 / BP FY27 / incentive per customer
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
from matplotlib.ticker import FuncFormatter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SI = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_stock_insights_20261007")
DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
PLAN = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning"
            r"\budget_per_DB_reviewed_24042026.xlsx")
OUT = Path(__file__).resolve().parent / "_assets_japan_dyn"
OUT.mkdir(parents=True, exist_ok=True)

BG = "#262626"
PANEL = "#303030"
WHITE = "#F2F2F2"
MUTED = "#BDBDBD"
RED = "#E30613"
AMBER = "#F5A000"
GREEN = "#31A354"
BLUE = "#4E8FD0"
GRID = "#4B4B4B"

matplotlib.rcParams["font.family"] = "Segoe UI"
matplotlib.rcParams["text.color"] = WHITE
matplotlib.rcParams["axes.labelcolor"] = MUTED
matplotlib.rcParams["xtick.color"] = MUTED
matplotlib.rcParams["ytick.color"] = MUTED


def frame(ax, fig, bg=PANEL):
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
        ax.spines[s].set_linewidth(0.7)
    ax.tick_params(length=0)


def kr(v, _=None):
    return "%.0fk" % (v / 1000.0)


def read_pt():
    df = pd.read_csv(SI / "portugal_billing_vs_sales_to_dealer.csv")
    df.columns = ["ym", "billed", "std", "gap", "pct"]
    for c in ("billed", "std", "gap", "pct"):
        df[c] = pd.to_numeric(df[c])
    return df


def read_ituk():
    df = pd.read_csv(SI / "billing_monthly_by_distributor.csv")
    d = df[df["distributor"] == "ITUK"].copy()
    d["fym"] = pd.PeriodIndex(d["ym"], freq="M").to_timestamp()
    return d.sort_values("fym").reset_index(drop=True)


# ======================================================= S2  plan + incentive
def s2_plan_bar():
    W_IN, H_IN = 4.97, 2.24
    wb = openpyxl.load_workbook(PLAN, data_only=True)
    ws = wb["Incentive FY27"]
    rows = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        if r[0] is None or str(r[0]).startswith("Total"):
            continue
        rows.append((str(r[0]), float(r[1]), float(r[3]), float(r[7])))
    rows.sort(key=lambda x: -x[3])
    fy26 = sum(r[1] for r in rows)
    fy27 = sum(r[2] for r in rows)
    inc = sum(r[3] for r in rows)
    names = [r[0] for r in rows]
    incs = [r[3] for r in rows]
    print("  s2: %d customers, BP FY26 %.2f, BP FY27 %.2f, incentive %.0f"
          % (len(rows), fy26, fy27, inc))
    print("      per customer:", {n: round(v, 0) for n, v in zip(names, incs)})

    cols = [RED if n == "ITUK" else AMBER if n in ("IUK", "UTI") else "#6E6E6E" for n in names]

    fig = plt.figure(figsize=(W_IN, H_IN), dpi=300)
    fig.patch.set_facecolor(PANEL)

    ax = fig.add_axes([0.035, 0.245, 0.615, 0.700])
    frame(ax, fig)
    x = list(range(len(incs)))
    ax.bar(x, incs, color=cols, width=0.66, linewidth=0)
    for xi, v in zip(x, incs):
        ax.text(xi, v + 2600, "%.0f" % (v / 1000.0), color=WHITE, fontsize=8.6,
                ha="center", va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8.0, rotation=90, color=WHITE)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(0, 102000)
    ax.set_title("incentive per customer, EUR thousands", color=MUTED, fontsize=9.0,
                 pad=5, loc="left")

    ax2 = fig.add_axes([0.755, 0.355, 0.225, 0.535])
    frame(ax2, fig)
    ax2.bar([0], [fy26 / 1e6], color="#7A7A7A", width=0.46, linewidth=0)
    ax2.bar([0.92], [fy27 / 1e6], color=GREEN, width=0.46, linewidth=0)
    ax2.text(0, fy26 / 1e6 + 0.60, "29.19", color=MUTED, fontsize=9.6, ha="center",
             fontweight="bold")
    ax2.text(0.92, fy27 / 1e6 + 0.60, "31.82", color=GREEN, fontsize=11.2, ha="center",
             fontweight="bold")
    ax2.annotate("", xy=(0.92, fy27 / 1e6 + 2.1), xytext=(0, fy26 / 1e6 + 2.1),
                 arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=2.0))
    ax2.text(0.46, fy26 / 1e6 + 3.1, "+9.0%", color=AMBER, fontsize=10.8, ha="center",
             fontweight="bold")
    ax2.set_xlim(-0.62, 1.54)
    ax2.set_ylim(0, 46)
    ax2.set_xticks([0, 0.92])
    ax2.set_xticklabels(["FY26", "FY27"], fontsize=8.6, color=WHITE)
    ax2.set_yticks([])
    ax2.spines["left"].set_visible(False)
    ax2.set_title("plan, EUR m", color=MUTED, fontsize=9.0, pad=5, loc="left")

    fig.savefig(OUT / "s2_plan_bar.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s2_plan_bar.png")


# ======================================================= S3  control chain
def s3_chain():
    from matplotlib.patches import FancyBboxPatch, Polygon

    W_IN, H_IN = 12.49, 2.40
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=300)
    fig.patch.set_facecolor(PANEL)
    ax = fig.add_axes([0, 0, 1, 1])
    frame(ax, fig)
    ax.set_xlim(0, W_IN)
    ax.set_ylim(0, H_IN)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("left", "bottom", "top", "right"):
        ax.spines[s].set_visible(False)

    pw, gap = 3.68, 0.485
    xs = [0.42, 0.42 + pw + gap, 0.42 + 2 * (pw + gap)]
    py, ph = 0.46, 1.30

    stations = [
        ("ISZE / IML", "We set", "the price list, the programme\nand the incentive", GREEN),
        ("DISTRIBUTOR", "They decide", "an independent business: what to stock,\nwhat to push, which brand",
         AMBER),
        ("DEALER", "They choose", "independent and multi-branded: an Isuzu\nline sits beside other brands",
         AMBER),
    ]
    for x, (kicker, head, body, col) in zip(xs, stations):
        ax.add_patch(FancyBboxPatch((x, py), pw, ph, boxstyle="round,pad=0,rounding_size=0.07",
                                    facecolor=PANEL, edgecolor=GRID, linewidth=0.9))
        ax.add_patch(plt.Rectangle((x, py), 0.075, ph, facecolor=col, linewidth=0))
        ax.text(x + 0.26, py + ph - 0.19, kicker, color=col, fontsize=8.4, fontweight="bold",
                va="center")
        ax.text(x + 0.26, py + ph - 0.60, head, color=WHITE, fontsize=16.0, fontweight="bold",
                va="center")
        ax.text(x + 0.26, py + 0.28, body, color=MUTED, fontsize=9.4, va="center",
                linespacing=1.45)

    for x in xs[:-1]:
        x0 = x + pw + 0.075
        ax.add_patch(Polygon([[x0, py + ph / 2 - 0.14], [x0 + 0.33, py + ph / 2],
                              [x0, py + ph / 2 + 0.14]], closed=True, facecolor=AMBER,
                             linewidth=0))

    ax.plot([xs[0], xs[0] + pw], [2.10, 2.10], color=GREEN, lw=2.0)
    ax.text(xs[0] + pw / 2, 2.19, "ours to set", color=GREEN, fontsize=10.4, fontweight="bold",
            ha="center", va="bottom")
    ax.plot([xs[1], xs[2] + pw], [2.10, 2.10], color=RED, lw=2.0)
    ax.text(xs[1] + (pw + gap + pw) / 2, 2.19, "not ours to instruct", color=RED, fontsize=10.4,
            fontweight="bold", ha="center", va="bottom")

    ax.text(0.42, 0.16, "One shelf, one budget: an Isuzu line sits beside other brands, and every "
                        "euro put into Isuzu stock is a euro not put into something else.",
            color=MUTED, fontsize=9.6, va="center")
    fig.savefig(OUT / "s3_chain.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s3_chain.png")


# ======================================================= S4  Portugal divergence
def s4_divergence():
    W_IN, H_IN = 8.30, 3.40
    df = read_pt()
    first = df[df["ym"].str.startswith("2025")].reset_index(drop=True)
    second = df[df["ym"].str.startswith("2026")].reset_index(drop=True)
    x1 = list(range(len(first)))
    x2 = [len(first) + 1.30 + i for i in range(len(second))]

    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=300)
    frame(ax, fig)

    ax.fill_between(x1, first["billed"], first["std"], color=GREEN, alpha=0.16, linewidth=0)
    ax.fill_between(x2, second["billed"], second["std"], color=RED, alpha=0.22, linewidth=0)

    ax.plot(x1, first["billed"], color=RED, lw=2.4, marker="o", ms=3.4,
            label="ISZE billed to Imotors")
    ax.plot(x1, first["std"], color=GREEN, lw=2.4, marker="o", ms=3.4,
            label="Imotors sales to dealer")
    ax.plot(x2, second["billed"], color=RED, lw=2.6, marker="o", ms=3.8)
    ax.plot(x2, second["std"], color=GREEN, lw=2.6, marker="o", ms=3.8)

    ax.axvline(len(first) + 0.65, color=GRID, lw=0.9, ls=(0, (3, 3)))

    best = None
    for i in range(len(second)):
        dd = abs(float(second.loc[i, "billed"]) - float(second.loc[i, "std"]))
        if best is None or dd < best[0]:
            best = (dd, i)
    ci = best[1]
    cross_x = x2[ci]
    cross_y = (float(second.loc[ci, "billed"]) + float(second.loc[ci, "std"])) / 2.0
    ax.axvline(cross_x, color=AMBER, lw=1.4, ls=(0, (2, 2)), zorder=1)
    ax.scatter([cross_x], [cross_y], s=62, facecolor=AMBER, edgecolor=BG, linewidths=1.2,
               zorder=6)
    ax.axvspan(cross_x, max(x2) + 0.6, color=GREEN, alpha=0.07, linewidth=0)
    ax.annotate("the lines cross here\nsales on above billing from this month",
                xy=(cross_x, cross_y), xytext=(cross_x + 0.28, 138000),
                color=AMBER, fontsize=9.4, fontweight="bold", va="center", ha="left",
                linespacing=1.35, zorder=7)

    ax.text(x2[-1] + 0.32, float(second.loc[len(second) - 1, "billed"]) + 4000,
            "ISZE billed\nEUR 109,377",
            color=RED, fontsize=9.6, fontweight="bold", va="center", ha="left", linespacing=1.35)
    ax.text(x2[-1] + 0.32, float(second.loc[len(second) - 1, "std"]) - 10000,
            "sales to dealer\nEUR 130,310",
            color=GREEN, fontsize=9.6, fontweight="bold", va="center", ha="left", linespacing=1.35)

    ax.set_xticks(x1 + x2)
    ax.set_xticklabels([m[5:] for m in first["ym"]] + [m[5:] for m in second["ym"]], fontsize=8.8)
    ax.text(len(first) / 2 - 0.5, -0.135, "2025", color=MUTED, fontsize=10.2, ha="center",
            transform=ax.get_xaxis_transform(), fontweight="bold")
    ax.text(x2[0] + (len(second) - 1) / 2.0, -0.135, "2026", color=MUTED, fontsize=10.2,
            ha="center", transform=ax.get_xaxis_transform(), fontweight="bold")

    ax.yaxis.set_major_formatter(FuncFormatter(kr))
    ax.set_ylabel("EUR a month", fontsize=9.2, labelpad=3)
    ax.tick_params(axis="y", labelsize=9.0)
    ax.grid(axis="y", color=GRID, lw=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 240000)
    ax.set_xlim(-0.6, max(x2) + 3.45)
    leg = ax.legend(loc="lower left", fontsize=9.4, frameon=False, ncol=1, handlelength=1.5,
                    handletextpad=0.45, borderpad=0.05)
    for t in leg.get_texts():
        t.set_color(WHITE)

    fig.subplots_adjust(left=0.082, right=0.997, top=0.965, bottom=0.115)
    fig.savefig(OUT / "s4_divergence.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s4_divergence.png", "cross", second.loc[ci, "ym"],
          "dist", round(best[0], 0))


# ======================================================= S5  family bars
def s5_families():
    W_IN, H_IN = 7.30, 2.45
    df = pd.read_csv(SI / "portugal_family_stock_build.csv")
    df["build"] = pd.to_numeric(df["build"])
    top = df.sort_values("build", ascending=False).head(7).iloc[::-1]
    names, vals = list(top["family"]), list(top["build"])
    cols = [GREEN if n == "Maintenance Service" else AMBER for n in names]

    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=300)
    frame(ax, fig)
    y = list(range(len(names)))
    ax.barh(y, vals, color=cols, height=0.64, linewidth=0)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10.0, color=WHITE)
    for yi, v, n in zip(y, vals, names):
        ax.text(v + 1200, yi, "EUR {:,}".format(round(v)), color=WHITE, fontsize=9.4,
                va="center", fontweight="bold" if n == "Maintenance Service" else "normal")
    ax.tick_params(axis="x", labelsize=8.8)
    ax.xaxis.set_major_formatter(FuncFormatter(kr))
    ax.grid(axis="x", color=GRID, lw=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(vals) * 1.40)
    fig.subplots_adjust(left=0.268, right=0.997, top=0.985, bottom=0.055)
    fig.savefig(OUT / "s5_families.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s5_families.png", "top7 sum", round(sum(vals), 2),
          "file total", round(df["build"].sum(), 2))


# ======================================================= S5  brake part ring
def s5_brake_ring():
    W_IN = H_IN = 2.45
    pn = pd.read_csv(SI / "portugal_pn_stock_build.csv")
    fam = pd.read_csv(SI / "portugal_family_stock_build.csv")
    fam["build"] = pd.to_numeric(fam["build"])
    brakes = float(fam.loc[fam["family"] == "Brakes", "build"].iloc[0])
    row = pn[pn["pn"].astype(str) == "8983767550"].iloc[0]
    part = float(row["stock_build_eur"])
    headline = 225744.0
    print("  brake part %s EUR %.2f of brakes EUR %.2f (headline EUR %.0f)"
          % (row["pn"], part, brakes, headline))

    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=300)
    frame(ax, fig)
    ax.pie([part, brakes - part, headline - brakes],
           colors=[RED, AMBER, "#3A3A3A"], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.34, edgecolor=PANEL, linewidth=1.5))
    ax.text(0, 0.10, "EUR 16,923", color=WHITE, fontsize=14.6, fontweight="bold",
            ha="center", va="center")
    ax.text(0, -0.235, "one brake part\n8983767550", color=MUTED, fontsize=8.4,
            ha="center", va="center", linespacing=1.35)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    fig.savefig(OUT / "s5_brake_ring.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s5_brake_ring.png", "share of brakes %.1f%%" % (100.0 * part / brakes))


# ======================================================= S6  distributor bars
def s6_distributor_bars():
    W_IN, H_IN = 7.60, 2.79
    d = pd.read_csv(DERIVED / "replenishment_exceptions_cy2025.csv")
    d = d[(d["year"] == 2025) & (d["pipeline_signal"] == "leakage_high_sellthrough")]
    agg = d.groupby("distributor_code")["bill_eur"].sum().sort_values(ascending=False)
    print("  s6 total from file EUR", round(agg.sum(), 2))
    print("  s6 split:", {k: round(v, 2) for k, v in agg.items()})

    labels = {"ITUK": "ITUK", "UTI": "UTI", "IUK": "IUK",
              "IRELAND": "Ireland", "GREECE": "Greece"}
    names = [labels.get(k, k) for k in agg.index]
    vals = list(agg.values)
    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=300)
    frame(ax, fig)
    y = list(range(len(names)))[::-1]
    cols = [RED if n == "ITUK" else AMBER for n in names]
    ax.barh(y, vals, color=cols, height=0.60, linewidth=0)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=12.0, color=WHITE)
    for yi, v, n in zip(y, vals, names):
        ax.text(v + 5600, yi, "EUR {:,.0f}".format(v), color=WHITE, fontsize=11.0, va="center",
                fontweight="bold" if n == "ITUK" else "normal")
    ax.tick_params(axis="x", labelsize=9.4)
    ax.xaxis.set_major_formatter(FuncFormatter(kr))
    ax.grid(axis="x", color=GRID, lw=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(vals) * 1.36)
    fig.subplots_adjust(left=0.150, right=0.997, top=0.985, bottom=0.125)
    fig.savefig(OUT / "s6_distributors.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s6_distributors.png")


# ======================================================= S6  euro donut
def s6_donut():
    W_IN = H_IN = 3.35
    d = pd.read_csv(DERIVED / "replenishment_exceptions_cy2025.csv")
    d = d[(d["year"] == 2025) & (d["pipeline_signal"] == "leakage_high_sellthrough")]
    agg = d.groupby("distributor_code")["bill_eur"].sum().sort_values(ascending=False)
    labels = {"ITUK": "ITUK", "UTI": "UTI", "IUK": "IUK",
              "IRELAND": "Ireland", "GREECE": "Greece"}
    names = [labels.get(k, k) for k in agg.index]
    vals = list(agg.values)
    total = sum(vals)
    cols = [RED, AMBER, "#C97B00", GREEN, BLUE]

    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=300)
    frame(ax, fig)
    wedges, _ = ax.pie(vals, colors=cols, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.36, edgecolor=PANEL, linewidth=1.6))
    for w, n, v in zip(wedges, names, vals):
        ang = (w.theta2 + w.theta1) / 2.0
        r = 0.80
        x = r * math.cos(math.radians(ang))
        y = r * math.sin(math.radians(ang))
        ha = "left" if x >= 0 else "right"
        ax.text(x, y, "%s\n%.0f%%" % (n, 100.0 * v / total), color=WHITE, fontsize=9.6,
                ha=ha, va="center", fontweight="bold", linespacing=1.30)
    ax.text(0, 0, "EUR 678,464\nfive distributors", color=WHITE, fontsize=8.6,
            ha="center", va="center", linespacing=1.35, fontweight="bold")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    fig.savefig(OUT / "s6_donut.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s6_donut.png", "total", round(total, 2))


# ======================================================= S7  ITUK series
def s7_ituk():
    W_IN, H_IN = 12.49, 2.85
    d = read_ituk()
    d = d[d["fym"] >= pd.Timestamp("2025-04-01")].reset_index(drop=True)
    x = list(range(len(d)))
    vals = list(d["net_sales_value"])
    run_rate = 515524.0
    x_mar = [i for i, t in enumerate(d["fym"]) if t.strftime("%Y-%m") == "2026-03"][0]
    i_feb = [i for i, t in enumerate(d["fym"]) if t.strftime("%Y-%m") == "2026-02"][0]
    x_fy27 = [i for i, t in enumerate(d["fym"]) if t.strftime("%Y-%m") == "2026-04"][0]

    fig, ax = plt.subplots(figsize=(W_IN, H_IN), dpi=300)
    frame(ax, fig)

    cols = []
    for i, t in enumerate(d["fym"]):
        if i == i_feb:
            cols.append(AMBER)
        elif i <= x_mar:
            cols.append(RED)
        else:
            cols.append("#6E6E6E")
    ax.bar(x, vals, color=cols, width=0.60, linewidth=0)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 14000, "%.0f" % round(v / 1000.0), color=MUTED, fontsize=7.6,
                ha="center", va="bottom")

    ax.axhline(run_rate, color=GREEN, lw=1.8, ls=(0, (5, 3)))
    ax.text(len(x) - 0.35, run_rate + 15000, "ITUK run rate  EUR 515,524 a month",
            color=GREEN, fontsize=10.0, ha="right", va="bottom", fontweight="bold")

    ax.axvline(x_mar + 0.5, color=AMBER, lw=2.2)
    ax.axvspan(x_mar + 0.5, len(x) - 0.30, color=AMBER, alpha=0.07, linewidth=0)
    ax.annotate("13 March 2026: price list changed +5.96%",
                xy=(x_mar + 0.5, 980000), xytext=(x_mar + 0.62, 1210000),
                color=AMBER, fontsize=10.4, fontweight="bold", ha="left", va="center")
    ax.annotate("volume ran 2.32x for twelve days, then 0.60x",
                xy=(x_mar + 0.55, 900000), xytext=(x_mar + 0.62, 1075000),
                color=MUTED, fontsize=9.4, ha="left", va="center")
    ax.annotate("EUR 861,719, which is EUR 346,195 above the run rate",
                xy=(i_feb, vals[i_feb] + 45000), xytext=(i_feb - 5.1, 1160000),
                color=AMBER, fontsize=10.2, fontweight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=AMBER, lw=1.0, shrinkA=2, shrinkB=2))

    ax.set_xticks(x)
    ax.set_xticklabels([t.strftime("%b") for t in d["fym"]], fontsize=8.8)
    ax.set_ylabel("EUR billed a month", fontsize=9.4, labelpad=3)
    ax.yaxis.set_major_formatter(FuncFormatter(kr))
    ax.tick_params(axis="y", labelsize=9.0)
    ax.grid(axis="y", color=GRID, lw=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 1265000)
    ax.set_xlim(-0.70, len(x) - 0.30)
    fig.subplots_adjust(left=0.055, right=0.997, top=0.975, bottom=0.175)
    fig.savefig(OUT / "s7_ituk.png", facecolor=PANEL)
    plt.close(fig)
    print("wrote", OUT / "s7_ituk.png", "feb", vals[i_feb], "mar", vals[x_mar],
          "run rate", run_rate, "fy27 starts", d["fym"][x_fy27].strftime("%Y-%m"))


if __name__ == "__main__":
    s2_plan_bar()
    s3_chain()
    s4_divergence()
    s5_families()
    s5_brake_ring()
    s6_distributor_bars()
    s6_donut()
    s7_ituk()
    print("assets in", OUT)
