"""
ISZE brand chart theme + helper functions.

Why this exists: native python-pptx charts (add_chart / XL_CHART_TYPE) render
with default-Office styling - gridlines, boxed legends, auto colors. That's
the "generic Excel chart" look. These helpers render charts with matplotlib
using the ISZE brand palette and direct labeling, save them as high-res PNGs,
and those PNGs get inserted as pictures into the slide. This is how
professional decks (consulting, IR, research) actually build charts.

Design rules baked in:
  - No gridlines except faint horizontal reference lines
  - No chart border / no top+right+left spines
  - Direct data labels instead of relying only on axis + legend
  - Legends only when 3+ series and even then: no border, small, below chart
  - Brand red reserved for the "headline" series (current period / call-out);
    everything else in charcoal/gray so red actually draws the eye
  - Waterfall: red = decrease, charcoal = increase, gray = start/end totals
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ---------------------------------------------------------------- palette --
RED         = "#CC0E1E"
RED_LIGHT   = "#DC606E"
CHARCOAL    = "#1A1A1A"
GRAY        = "#5A5A5A"
GRAY_MED    = "#8C8C8C"
GRAY_LIGHT  = "#B7B7B7"
GRAY_BG     = "#ECECEC"
WHITE       = "#FFFFFF"

# ordered ramp for >2 series - always starts red (current/headline), then
# moves through neutral grays so nothing competes with red for attention
SERIES_COLORS = [RED, CHARCOAL, GRAY_MED, GRAY_LIGHT, RED_LIGHT]

FONT_FAMILY = "DejaVu Sans"  # closest metric match available in this sandbox;
                             # on Windows/Mac substitute "Calibri" or "Arial"
                             # to match the ISZE deck body font exactly.

plt.rcParams["font.family"] = FONT_FAMILY
plt.rcParams["svg.fonttype"] = "none"


def _base_fig(figsize=(10.2, 4.3)):
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRAY_LIGHT)
    ax.spines["bottom"].set_linewidth(1)
    ax.tick_params(axis="both", colors=GRAY, labelsize=11, length=0)
    ax.yaxis.grid(True, color=GRAY_BG, linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    return fig, ax


def _save(fig, filename):
    fig.tight_layout(pad=0.6)
    fig.savefig(filename, dpi=200, transparent=False, facecolor=WHITE)
    plt.close(fig)


def bar_chart(categories, series, filename, title=None, value_fmt="{:,.0f}",
              ylabel=None, figsize=(10.2, 4.3)):
    """
    categories: list[str]
    series: dict[str, list[float]]  -- e.g. {"FY2026": [...], "FY2025": [...]}
            first key is treated as the headline series -> gets RED
    """
    fig, ax = _base_fig(figsize)
    names = list(series.keys())
    n = len(names)
    x = np.arange(len(categories))
    width = 0.72 / max(n, 1)

    for i, name in enumerate(names):
        color = SERIES_COLORS[i % len(SERIES_COLORS)]
        offset = (i - (n - 1) / 2) * width
        vals = series[name]
        bars = ax.bar(x + offset, vals, width=width * 0.92, color=color,
                       zorder=3, label=name)
        for b, v in zip(bars, vals):
            ax.annotate(value_fmt.format(v),
                        (b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9.5,
                        color=CHARCOAL, fontweight="bold" if i == 0 else "normal")

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, color=CHARCOAL)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=GRAY)
    ax.set_ylim(0, max(max(v) for v in series.values()) * 1.22)

    if n >= 2:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=n,
                   frameon=False, fontsize=10, labelcolor=CHARCOAL)
    if title:
        ax.set_title(title, fontsize=13, color=CHARCOAL, loc="left",
                     fontweight="bold", pad=12)
    _save(fig, filename)


def trend_line(x_labels, series, filename, title=None, value_fmt="{:,.0f}",
               figsize=(10.2, 4.3)):
    """
    Line chart with end-of-line direct labels instead of a legend box.
    series: dict[str, list[float]] - first key = headline -> RED, thicker line
    """
    fig, ax = _base_fig(figsize)
    x = np.arange(len(x_labels))
    names = list(series.keys())

    for i, name in enumerate(names):
        color = SERIES_COLORS[i % len(SERIES_COLORS)]
        vals = series[name]
        lw = 2.8 if i == 0 else 1.6
        ax.plot(x, vals, color=color, linewidth=lw, zorder=3,
                marker="o", markersize=4 if i == 0 else 3,
                markerfacecolor=color, markeredgecolor=WHITE, markeredgewidth=0.6)
        # direct end label
        ax.annotate(f"{name}  {value_fmt.format(vals[-1])}",
                    (x[-1], vals[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", ha="left", fontsize=10, color=color,
                    fontweight="bold" if i == 0 else "normal")

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=11, color=CHARCOAL)
    ax.margins(x=0.02)
    fig.subplots_adjust(right=0.80)  # leave room for end labels
    if title:
        ax.set_title(title, fontsize=13, color=CHARCOAL, loc="left",
                     fontweight="bold", pad=12)
    _save(fig, filename)


def waterfall(labels, values, filename, total_indices=None, title=None,
              value_fmt="{:+,.0f}", figsize=(10.2, 4.3)):
    """
    Bridge / variance waterfall.
    labels: list[str]
    values: list[float] - deltas; for a 'total' bar pass the absolute value
            and list its position (0-based) in total_indices
    total_indices: set of indices that are totals (drawn from 0, in GRAY)
    """
    total_indices = total_indices or {0, len(values) - 1}
    fig, ax = _base_fig(figsize)

    running = 0
    for i, v in enumerate(values):
        if i in total_indices:
            bottom = 0
            height = v
            running = v
            color = GRAY
        else:
            bottom = running if v >= 0 else running + v
            height = abs(v)
            color = CHARCOAL if v >= 0 else RED
            running += v

        ax.bar(i, height, bottom=bottom, color=color, width=0.6, zorder=3)
        label_val = value_fmt.format(v) if i not in total_indices else f"{v:,.0f}"
        ax.annotate(label_val, (i, bottom + height),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, color=CHARCOAL,
                    fontweight="bold")

        # connector line to next bar
        if i < len(values) - 1:
            ax.plot([i + 0.3, i + 0.7], [running, running],
                    color=GRAY_LIGHT, linewidth=1, zorder=2)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10.5, color=CHARCOAL)
    ax.set_ylim(0, max(running, max(values)) * 1.25)
    if title:
        ax.set_title(title, fontsize=13, color=CHARCOAL, loc="left",
                     fontweight="bold", pad=12)
    _save(fig, filename)


def donut_share(labels, values, filename, center_label=None, center_value=None,
                 title=None, figsize=(6.6, 4.6)):
    """Share-of-total donut with direct labels (no legend), brand ramp colors."""
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor(WHITE)
    colors = [SERIES_COLORS[i % len(SERIES_COLORS)] for i in range(len(values))]

    wedges, _ = ax.pie(values, colors=colors, startangle=90,
                        wedgeprops=dict(width=0.38, edgecolor=WHITE, linewidth=2))
    total = sum(values)
    for w, lbl, val in zip(wedges, labels, values):
        ang = (w.theta2 + w.theta1) / 2
        x = np.cos(np.radians(ang))
        y = np.sin(np.radians(ang))
        pct = val / total * 100
        ax.annotate(f"{lbl}\n{pct:.0f}%", (x * 0.78, y * 0.78),
                    ha="center", va="center", fontsize=9, color=WHITE,
                    fontweight="bold")

    if center_label:
        ax.text(0, 0.08, center_value or "", ha="center", va="center",
                 fontsize=18, color=CHARCOAL, fontweight="bold")
        ax.text(0, -0.14, center_label, ha="center", va="center",
                 fontsize=9.5, color=GRAY)

    ax.set_aspect("equal")
    if title:
        ax.set_title(title, fontsize=13, color=CHARCOAL, loc="left",
                     fontweight="bold", pad=10)
    _save(fig, filename)
