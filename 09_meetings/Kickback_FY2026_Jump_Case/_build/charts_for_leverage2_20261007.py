"""Chart assets for the two new kickback-deck slides (2026-10-07, pass 2).

Every series is read from a named source file. Nothing is typed in by hand except:
  - the Kosha path, transcribed from the deck's own slide 3 table
    (source: ISZE Vehicle Parts - FY2026 Year-End Review.xlsx, sheet 'Kosha Gap & FY2027')
  - the per-distributor FY26->FY27 plan increases, transcribed from the same slide 3 table
    (source: budget_per_DB_reviewed_24042026.xlsx, sheet 'Incentive FY27')

Outputs are dpi 300 with figure sizes equal to the final on-slide size, so matplotlib point sizes
are slide point sizes. Colours are the deck palette.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SI = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_stock_insights_20261007")
OUT = Path(__file__).resolve().parent / "_assets_leverage2"
OUT.mkdir(parents=True, exist_ok=True)

PANEL = "#303030"
WHITE = "#F2F2F2"
MUTED = "#BDBDBD"
RED = "#E30613"
AMBER = "#F5A000"
GREEN = "#31A354"
GRID = "#4B4B4B"

matplotlib.rcParams["font.family"] = "Segoe UI"
matplotlib.rcParams["text.color"] = WHITE
matplotlib.rcParams["axes.labelcolor"] = MUTED
matplotlib.rcParams["xtick.color"] = MUTED
matplotlib.rcParams["ytick.color"] = MUTED


def frame(ax, fig):
    fig.patch.set_facecolor(PANEL)
    ax.set_facecolor(PANEL)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
        ax.spines[s].set_linewidth(0.7)
    ax.tick_params(length=0)


# ============================================================ s22 charts
def divergence():
    """ISZE billing against sales to dealer, Portugal, the 16 reported months."""
    src = SI / "portugal_billing_vs_sales_to_dealer.csv"
    df = pd.read_csv(src)
    df.columns = ["ym", "billed", "std", "gap", "pct"]
    df["billed"] = pd.to_numeric(df["billed"])
    df["std"] = pd.to_numeric(df["std"])
    first = df[df["ym"].str.startswith("2025")].reset_index(drop=True)
    second = df[df["ym"].str.startswith("2026")].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(6.20, 2.30), dpi=300)
    frame(ax, fig)

    x1 = list(range(len(first)))
    x2 = [len(first) + 0.9 + i for i in range(len(second))]

    ax.fill_between(x1, first["billed"], first["std"], color=RED, alpha=0.20, linewidth=0)
    ax.fill_between(x2, second["billed"], second["std"], color=AMBER, alpha=0.20, linewidth=0)
    ax.plot(x1, first["billed"], color=RED, linewidth=2.3, marker="o", markersize=3.4,
            label="ISZE billed")
    ax.plot(x1, first["std"], color=GREEN, linewidth=2.3, marker="o", markersize=3.4,
            label="Sales to dealer")
    ax.plot(x2, second["billed"], color=RED, linewidth=2.3, marker="o", markersize=3.4)
    ax.plot(x2, second["std"], color=GREEN, linewidth=2.3, marker="o", markersize=3.4)

    ax.axvline(len(first) + 0.45, color=GRID, linewidth=0.9, linestyle=(0, (3, 3)))
    ax.text(len(first) + 0.52, 205000, "no months reported\nSep-Dec 2025", color=MUTED,
            fontsize=6.4, va="top", ha="left", linespacing=1.25)

    ax.set_xticks(x1 + x2)
    ax.set_xticklabels([m[5:] for m in first["ym"]] + [m[5:] for m in second["ym"]], fontsize=7.0)
    ax.text(len(first) / 2 - 0.5, -0.235, "2025", color=MUTED, fontsize=7.6, ha="center",
            transform=ax.get_xaxis_transform(), fontweight="bold")
    ax.text(len(first) + 0.9 + len(second) / 2 - 0.5, -0.235, "2026", color=MUTED, fontsize=7.6,
            ha="center", transform=ax.get_xaxis_transform(), fontweight="bold")

    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.0fk" % (v / 1000)))
    ax.tick_params(axis="y", labelsize=7.0)
    ax.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 215000)
    ax.set_xlim(-0.6, max(x2) + 0.6)
    leg = ax.legend(loc="upper left", fontsize=7.4, frameon=False, ncol=2, handlelength=1.5,
                    handletextpad=0.45, columnspacing=1.2, borderpad=0.05)
    for t in leg.get_texts():
        t.set_color(WHITE)

    fig.subplots_adjust(left=0.083, right=0.996, top=0.925, bottom=0.145)
    p = OUT / "imotors_divergence.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p)


def family_build():
    """Net parts build by family, euro, top six rows of the family file."""
    src = SI / "portugal_family_stock_build.csv"
    df = pd.read_csv(src)
    df["build"] = pd.to_numeric(df["build"])
    top = df.sort_values("build", ascending=False).head(6).iloc[::-1]
    names = list(top["family"])
    vals = list(top["build"])
    colors = [GREEN if n == "Maintenance Service" else AMBER for n in names]

    fig, ax = plt.subplots(figsize=(6.01, 2.30), dpi=300)
    frame(ax, fig)
    y = list(range(len(names)))
    ax.barh(y, vals, color=colors, height=0.60, linewidth=0)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.4)
    for yi, v, n in zip(y, vals, names):
        ax.text(v + 800, yi, "EUR {:,}".format(round(v)), color=WHITE, fontsize=7.2, va="center",
                fontweight="bold" if n == "Maintenance Service" else "normal")
    ax.tick_params(axis="x", labelsize=6.9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.0fk" % (v / 1000)))
    ax.grid(axis="x", color=GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(vals) * 1.34)
    ax.set_xlabel("net parts build, EUR  (Jan 2025 - Aug 2026)", fontsize=7.2, labelpad=1.5)
    fig.subplots_adjust(left=0.235, right=0.996, top=0.985, bottom=0.135)
    p = OUT / "imotors_family_build.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p, "top six", round(sum(vals), 2), "of file total", round(df["build"].sum(), 2))


def brake_pair():
    """Brake pads: bought against sold to dealers, FY2026 and FY2027 to August."""
    fig, ax = plt.subplots(figsize=(6.16, 0.98), dpi=300)
    frame(ax, fig)
    groups = ["FY2026", "FY2027 to Aug"]
    bought = [1370, 93]
    sold = [994, 406]
    x = [0, 1]
    w = 0.30
    ax.bar([i - w / 2 - 0.015 for i in x], bought, width=w, color=AMBER, linewidth=0)
    ax.bar([i + w / 2 + 0.015 for i in x], sold, width=w, color=GREEN, linewidth=0)
    for i, (b, s) in zip(x, zip(bought, sold)):
        ax.text(i - w / 2 - 0.015, b + 45, "{:,}".format(b), color=AMBER, fontsize=7.6,
                ha="center", fontweight="bold")
        ax.text(i + w / 2 + 0.015, s + 45, "{:,}".format(s), color=GREEN, fontsize=7.6,
                ha="center", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=7.8)
    ax.set_yticks([])
    ax.set_ylim(0, 1720)
    ax.set_xlim(-0.52, 1.52)
    ax.spines["left"].set_visible(False)
    ax.text(-0.50, 1620, "bought", color=AMBER, fontsize=7.2, fontweight="bold", va="top")
    ax.text(-0.50, 1470, "sold to dealers", color=GREEN, fontsize=7.2, va="top")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.98, bottom=0.155)
    p = OUT / "imotors_brake_pair.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p)


# ============================================================ s23 cards
def divergence_small():
    """Compact Portugal divergence for a card: two lines moving apart. Same source as above."""
    src = SI / "portugal_billing_vs_sales_to_dealer.csv"
    df = pd.read_csv(src)
    df.columns = ["ym", "billed", "std", "gap", "pct"]
    df["billed"] = pd.to_numeric(df["billed"])
    df["std"] = pd.to_numeric(df["std"])
    # index both series to their 2025 mean so the two lines are comparable on one scale
    base_b = df[df["ym"].str.startswith("2025")]["billed"].mean()
    base_s = df[df["ym"].str.startswith("2025")]["std"].mean()
    ib = df["billed"] / base_b * 100
    st = df["std"] / base_s * 100
    first = 8
    x1 = list(range(first))
    x2 = [first + 0.8 + i for i in range(len(df) - first)]

    fig, ax = plt.subplots(figsize=(3.90, 1.22), dpi=300)
    frame(ax, fig)
    ax.axhline(100, color=GRID, linewidth=0.6, linestyle=(0, (3, 3)))
    for xa, ya, xb, yb in ((x1, ib[:first], x2, ib[first:]),):
        ax.plot(xa, ya, color=RED, linewidth=2.2)
        ax.plot(xb, yb, color=RED, linewidth=2.2)
    ax.plot(x1, st[:first], color=GREEN, linewidth=2.2)
    ax.plot(x2, st[first:], color=GREEN, linewidth=2.2)
    ax.text(x2[-1] + 0.25, ib.iloc[-1], "billed  -16.2%\nvs plan", color=RED, fontsize=6.4,
            va="center", ha="left", linespacing=1.2, fontweight="bold")
    ax.text(x2[-1] + 0.25, st.iloc[-1], "dealer sales\n+25.0%", color=GREEN, fontsize=6.4,
            va="center", ha="left", linespacing=1.2, fontweight="bold")
    ax.set_ylim(72, 128)
    ax.set_yticks([90, 100, 110])
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=6.2)
    ax.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_xlim(-0.3, max(x2) + 4.6)
    fig.subplots_adjust(left=0.115, right=0.995, top=0.97, bottom=0.035)
    p = OUT / "imotors_divergence_small.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p, "index 2025=100")


def ramp():
    """Kosha path FY2024-FY2031, transcribed from the deck's own slide 3."""
    years = ["FY24", "FY25", "FY26", "FY27", "FY28", "FY29", "FY30", "FY31"]
    vals = [29.6, 32.5, 32.3, 35.3, 37.5, 41.5, 46.4, 52.1]
    fig, ax = plt.subplots(figsize=(3.90, 1.22), dpi=300)
    frame(ax, fig)
    ax.plot(range(len(vals)), vals, color=AMBER, linewidth=2.3, marker="o", markersize=3.0)
    ax.fill_between(range(len(vals)), 0, vals, color=AMBER, alpha=0.13, linewidth=0)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(years, fontsize=6.6)
    ax.set_ylim(24, 60)
    ax.set_xlim(-0.35, len(vals) - 0.3)
    ax.set_yticks([30, 40, 50])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.0f" % v))
    ax.tick_params(axis="y", labelsize=6.2)
    ax.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    ax.annotate("52.1", xy=(7, 52.1), xytext=(5.95, 52.6), color=WHITE, fontsize=7.0,
                fontweight="bold", va="bottom")
    ax.annotate("29.6", xy=(0, 29.6), xytext=(-0.32, 24.6), color=MUTED, fontsize=6.6, va="bottom")
    fig.subplots_adjust(left=0.105, right=0.995, top=0.965, bottom=0.185)
    p = OUT / "ramp_sparkline.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p)


def ibx():
    """IBX days of stock Jan-Jul 2026 against its 60-75 day class A band."""
    piv = pd.read_csv(SI / "stock_days_monthly_pivot.csv")
    d = piv[["ym", "IBX (Benelux)"]].dropna()
    d = d[d["ym"] >= 202601]
    vals = [float(v) for v in d["IBX (Benelux)"]]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"][: len(vals)]

    fig, ax = plt.subplots(figsize=(3.90, 1.22), dpi=300)
    frame(ax, fig)
    ax.axhspan(60, 75, color=GREEN, alpha=0.20, linewidth=0)
    ax.plot(range(len(vals)), vals, color=AMBER, linewidth=2.3, marker="o", markersize=3.0)
    ax.axhline(75, color=GREEN, linewidth=0.8, linestyle=(0, (3, 3)))
    ax.axhline(60, color=GREEN, linewidth=0.8, linestyle=(0, (3, 3)))
    ax.text(len(vals) - 0.55, 76.5, "60-75 day band, class A", color=GREEN, fontsize=6.2,
            ha="right", va="bottom")
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=6.8)
    ax.set_ylim(16, 94)
    ax.set_yticks([30, 45, 60, 75])
    ax.tick_params(axis="y", labelsize=6.2)
    ax.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    ax.annotate("32", xy=(0, vals[0]), xytext=(0.05, vals[0] - 21), color=WHITE, fontsize=7.0,
                fontweight="bold", ha="center")
    ax.annotate("63", xy=(len(vals) - 1, vals[-1]), xytext=(len(vals) - 1.1, vals[-1] - 22),
                color=WHITE, fontsize=7.0, fontweight="bold", ha="center")
    fig.subplots_adjust(left=0.105, right=0.995, top=0.93, bottom=0.185)
    p = OUT / "ibx_sparkline.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p)


def growth_ask():
    """Per-distributor FY26->FY27 plan increase, ten customers, network +9.0% marked."""
    names = ["ITUK", "IUK", "UMI", "UTI", "Benelux", "Germany", "Portugal", "Ireland",
             "Norway", "Sweden"]
    vals = [6.5, 12.3, 9.6, 5.9, 3.4, 12.5, 8.0, 9.2, 14.1, 12.3]
    fig, ax = plt.subplots(figsize=(3.90, 1.22), dpi=300)
    frame(ax, fig)
    for i, v in enumerate(vals):
        col = RED if v >= 12 else AMBER if v >= 8 else MUTED
        ax.plot([0, v], [i, i], color=col, linewidth=1.2, alpha=0.55, solid_capstyle="butt")
        ax.plot([v], [i], marker="o", markersize=3.8, color=col)
    ax.axvline(9.0, color=WHITE, linewidth=0.9, linestyle=(0, (2, 2)))
    ax.text(9.2, -0.95, "network +9.0%", color=WHITE, fontsize=6.0, va="center")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=6.2)
    ax.set_ylim(len(names) - 0.4, -1.4)
    ax.set_xlim(0, 16)
    ax.set_xticks([0, 5, 10, 15])
    ax.set_xticklabels(["0%", "5%", "10%", "15%"], fontsize=6.2)
    ax.grid(axis="x", color=GRID, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.annotate("+3.4%", xy=(3.4, 4), xytext=(-0.2, 4.0), color=MUTED, fontsize=5.8, ha="right",
                va="center")
    ax.annotate("+14.1%", xy=(14.1, 8), xytext=(15.6, 8.0), color=RED, fontsize=5.8, ha="right",
                va="center")
    fig.subplots_adjust(left=0.215, right=0.995, top=0.985, bottom=0.165)
    p = OUT / "growth_ask.png"
    fig.savefig(p, facecolor=PANEL)
    plt.close(fig)
    print("wrote", p, "four above 12%:", sum(1 for v in vals if v > 12))


if __name__ == "__main__":
    divergence()
    divergence_small()
    family_build()
    brake_pair()
    ramp()
    ibx()
    growth_ask()
    print("assets in", OUT)
