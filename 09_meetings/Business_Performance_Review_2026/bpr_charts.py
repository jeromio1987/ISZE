"""
BPR 2.0 chart library — best form per question (ISZE house palette).

Extends 04_tools/ppt_template_v2/isze_chart_theme.py with the forms the
Business Performance Review needs, chosen per skill `.cursor/skills/isze-best-chart`:

  ranked_bar      who is biggest / who wins            ranked + reference rule
  deviation       who is out of line vs a norm         two-sided from a zero line
  change_bars     what moved, split into legs          diverging, three legs
  slope_two       two points, FEW series               max ~6 labelled lines
  line_years      one series over years                direct end labels
  split_row       composition with named residual      100% row per unit
  heatmap         pattern across two dimensions        cell = value
  fan_band        projection with a method break       band + break rule
  bubble_quad     two axes, quadrants                  labelled quadrant map

Every function writes a high-res PNG and returns the path.
No gridlines except a faint horizontal reference. No chart border.
Brand red is reserved for the thing that needs attention.
"""
from __future__ import annotations

import os
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ----------------------------------------------------------------- palette
RED = "#CC0E1E"
RED_DEEP = "#8F0A15"
RED_LIGHT = "#DC606E"
CHARCOAL = "#1A1A1A"
INK = "#222222"
GRAY = "#5A5A5A"
GRAY_MED = "#8C8C8C"
GRAY_LIGHT = "#C9C9C9"
GRAY_BG = "#EFEFEF"
GREEN = "#2E6B4F"
AMBER = "#C08A2E"
WHITE = "#FFFFFF"
CREAM = "#F7F4EE"

FONT_FAMILY = "Calibri"

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts_out")
os.makedirs(OUT_DIR, exist_ok=True)


def _apply_font():
    plt.rcParams["font.family"] = FONT_FAMILY
    plt.rcParams["font.sans-serif"] = [FONT_FAMILY, "Arial", "DejaVu Sans"]


def _path(name: str) -> str:
    return os.path.join(OUT_DIR, name)


def _fig(figsize=(9.6, 4.6), dpi=200):
    _apply_font()
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRAY_LIGHT)
    ax.tick_params(axis="both", colors=GRAY, labelsize=10.5, length=0)
    ax.set_axisbelow(True)
    return fig, ax


def _title(ax, text, sub=None):
    if text:
        ax.set_title(text, loc="left", fontsize=13.5, color=INK,
                     fontweight="bold", pad=16 if sub else 10)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10, color=GRAY)


def _save(fig, name):
    p = _path(name)
    fig.tight_layout()
    fig.savefig(p, facecolor=WHITE)
    plt.close(fig)
    return p


def _fmt_eur(v, dec=0):
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1_000_000:
        return f"{sign}€{a/1_000_000:,.1f}M"
    if a >= 1_000:
        return f"{sign}€{a/1_000:,.0f}k"
    return f"{sign}€{a:,.{dec}f}"


def _fmt_pct(v, dec=1):
    return "—" if v is None else f"{v:,.{dec}f}%"


# ------------------------------------------------------------------ 1 rank
def ranked_bar(labels, values, filename, title=None, subtitle=None,
               value_fmt="{:,.0f}", reference=None, reference_label=None,
               hot_below=True, figsize=None, label_width=None):
    """Horizontal ranked bars, value printed at the bar, optional reference rule.

    hot_below=True → bars at or below the reference/median take the red accent,
    so the reader sees who is lagging without reading numbers.
    """
    n = len(labels)
    if figsize is None:
        figsize = (9.6, 1.2 + 0.33 * n)
    fig, ax = _fig(figsize=figsize)
    ref = reference if reference is not None else (
        sorted(values)[len(values) // 2] if values else 0)
    y = list(range(n))[::-1]
    for i, (lab, val) in enumerate(zip(labels, values)):
        hot = hot_below and val <= ref
        ax.barh(y[i], val, height=0.62,
                color=RED if hot else CHARCOAL, zorder=2)
        ax.text(val + max(values) * 0.012, y[i], value_fmt.format(val),
                va="center", ha="left", fontsize=10, color=INK, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5, color=INK)
    ax.set_xticks([])
    ax.set_xlim(0, max(values) * 1.16 if max(values) > 0 else 1)
    if reference is not None:
        ax.axvline(reference, color=RED_DEEP, lw=1.3, ls=(0, (4, 3)), zorder=1)
        if reference_label:
            ax.text(reference, n - 0.25, "  " + reference_label, fontsize=9.5,
                    color=RED_DEEP, va="bottom", ha="left")
    for s in ("bottom",):
        ax.spines[s].set_visible(False)
    _title(ax, title, subtitle)
    return _save(fig, filename)


# ------------------------------------------------------------- 2 deviation
def deviation(labels, values, filename, title=None, subtitle=None,
              value_fmt="{:+.1f}", band=None, figsize=None):
    """Two-sided bars around a zero line: who is out of line vs the norm.

    band=(lo,hi) colours only what sits outside the tolerance in red.
    """
    n = len(labels)
    if figsize is None:
        figsize = (9.6, 1.2 + 0.33 * n)
    fig, ax = _fig(figsize=figsize)
    y = list(range(n))[::-1]
    lim = max(abs(min(values)), abs(max(values)), 1e-9) * 1.35
    for i, (lab, val) in enumerate(zip(labels, values)):
        outside = True
        if band is not None:
            outside = val < band[0] or val > band[1]
        ax.barh(y[i], val, height=0.62,
                color=(RED if val < 0 else GREEN) if outside else GRAY_MED,
                zorder=2)
        off = lim * 0.02
        ax.text(val + (off if val >= 0 else -off), y[i], value_fmt.format(val),
                va="center", ha="left" if val >= 0 else "right",
                fontsize=10, color=INK, zorder=3)
    ax.axvline(0, color=CHARCOAL, lw=1.2, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5, color=INK)
    ax.set_xticks([])
    ax.set_xlim(-lim, lim)
    for s in ("bottom",):
        ax.spines[s].set_visible(False)
    _title(ax, title, subtitle)
    return _save(fig, filename)


# ------------------------------------------------------------ 3 change legs
def change_bars(labels, legs, filename, title=None, subtitle=None,
                value_fmt="{:+,.0f}", figsize=None):
    """Diverging bars per entity; `legs` = ordered dict name -> values.

    Used for growth split into volume / price / mix. First leg takes red.
    """
    names = list(legs.keys())
    n = len(labels)
    if figsize is None:
        figsize = (9.6, 1.2 + 0.5 * n)
    fig, ax = _fig(figsize=figsize)
    y = list(range(n))[::-1]
    colors = [RED, CHARCOAL, GRAY_MED, GRAY_LIGHT]
    total = [sum(legs[k][i] for k in names) for i in range(n)]
    lim = max(max(abs(v) for v in total), 1e-9) * 1.5
    neg = [min(0, v) for v in total]
    for i in range(n):
        left = 0.0
        for j, k in enumerate(names):
            v = legs[k][i]
            ax.barh(y[i], v, left=left, height=0.6, color=colors[j % len(colors)],
                    zorder=2, label=k if i == 0 else None)
            left += v
        ax.text(total[i] + lim * 0.015, y[i], value_fmt.format(total[i]),
                va="center", ha="left" if total[i] >= 0 else "right",
                fontsize=10, color=INK, zorder=3)
    ax.axvline(0, color=CHARCOAL, lw=1.2, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5, color=INK)
    ax.set_xticks([])
    ax.set_xlim(-lim, lim)
    ax.legend(loc="lower right", frameon=False, fontsize=10, ncol=len(names))
    _title(ax, title, subtitle)
    return _save(fig, filename)


# ---------------------------------------------------------------- 4 slope
def slope_two(labels, start, end, filename, title=None, subtitle=None,
              value_fmt="{:,.0f}", max_series=6, stagger=0.16,
              draw_reference=True, reference_start=None, reference_end=None,
              reference_label="network"):
    """Two-point slope for the LARGEST few series only (max_series).

    Anything more turns into spaghetti — use change_bars for the rest.
    Green rising, red falling. End labels are staggered so they never overlap.
    """
    assert len(labels) <= max_series, (
        f"slope_two: {len(labels)} series on one slope is a hard fail "
        f"(max {max_series}). Use change_bars for the rest.")
    fig, ax = _fig(figsize=(9.2, 5.0))
    lo = min(list(start) + list(end)) * 0.72
    hi = max(list(start) + list(end)) * 1.18
    ax.set_ylim(lo, hi)
    ax.set_xlim(-0.55, 1.75)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("bottom",):
        ax.spines[s].set_visible(False)

    if draw_reference and reference_start is not None and reference_end is not None:
        ax.plot([0, 1], [reference_start, reference_end], color=GRAY_LIGHT,
                lw=2, ls=(0, (5, 4)), zorder=1)
        ax.text(1.03, reference_end, f"  {reference_label}", fontsize=9.5,
                color=GRAY, va="center")

    ends = []
    for lab, a, b in zip(labels, start, end):
        col = GREEN if b >= a else RED
        ax.plot([0, 1], [a, b], color=col, lw=2.4, zorder=3,
                marker="o", markersize=5, markerfacecolor=col)
        pct = ((b - a) / a * 100) if a else 0
        ax.text(-0.03, a, f"{lab}  {value_fmt.format(a)}", ha="right",
                va="center", fontsize=10.5, color=INK)
        ends.append((b, f"{value_fmt.format(b)}  {pct:+.1f}%"))
    ax.text(-0.03, hi * 0.985 + (hi - lo) * 0.02, f"start", ha="right",
            va="bottom", fontsize=10, color=GRAY)
    ax.text(1.0, hi * 0.985 + (hi - lo) * 0.02, f"end", ha="center",
            va="bottom", fontsize=10, color=GRAY)

    # stagger end labels so neighbouring values never collide
    span = (hi - lo)
    order = sorted(range(len(ends)), key=lambda i: ends[i][0])
    prev = None
    for idx in order:
        val, txt = ends[idx]
        shown = val
        if prev is not None and (shown - prev) < span * stagger:
            shown = prev + span * stagger
        prev = shown
        ax.text(1.03, shown, "  " + txt, fontsize=10.5, color=INK, va="center")
    _title(ax, title, subtitle)
    return _save(fig, filename)


# --------------------------------------------------------------- 5 line yrs
def line_years(x_labels, series, filename, title=None, subtitle=None,
               value_fmt="{:,.1f}", annotation=None, figsize=(9.6, 4.4)):
    """One or two series over years with direct end labels.

    series: ordered dict name -> values. First series takes red.
    annotation: (x_index, y_value, text) to mark the break/cause on the chart.
    """
    fig, ax = _fig(figsize=figsize)
    colors = [RED, CHARCOAL, GRAY_MED]
    xs = list(range(len(x_labels)))
    for j, (name, vals) in enumerate(series.items()):
        ax.plot(xs, vals, color=colors[j % len(colors)], lw=2.6,
                marker="o", markersize=6, zorder=3, label=name,
                ls="-" if j == 0 else (0, (5, 4)))
        for i, v in enumerate(vals):
            ax.text(i, v, value_fmt.format(v), ha="center", va="bottom",
                    fontsize=10, color=INK, zorder=4)
    ax.set_xticks(xs)
    ax.set_xticklabels(x_labels, fontsize=11, color=GRAY)
    ax.set_yticks([])
    lo = min(min(v) for v in series.values())
    hi = max(max(v) for v in series.values())
    ax.set_ylim(lo - (hi - lo) * 0.35, hi + (hi - lo) * 0.30)
    if annotation:
        xi, yv, text = annotation
        ax.axvline(xi, color=RED_LIGHT, lw=1.2, ls=(0, (3, 3)), zorder=1)
        ax.annotate(text, xy=(xi, yv), xytext=(xi - 0.42, yv),
                    fontsize=10, color=RED_DEEP, va="center", ha="right")
    if len(series) > 1:
        ax.legend(loc="best", frameon=False, fontsize=10)
    for s in ("bottom",):
        ax.spines[s].set_visible(False)
    _title(ax, title, subtitle)
    return _save(fig, filename)


# ------------------------------------------------------------- 6 split rows
def split_row(labels, segments, filename, title=None, subtitle=None,
              value_fmt="{:,.1f}%", figsize=None, right_note=None):
    """100% stacked rows: composition per unit with a NAMED residual.

    segments: ordered dict name -> values (each row should sum to 100).
    If a row does not sum to 100 the remainder is drawn as an explicitly named
    "other / uncoded" leg, because an unexplained gap in a part-to-whole chart
    is the one thing a reader cannot recover from.
    """
    names = list(segments.keys())
    n = len(labels)
    sums = [sum(segments[k][i] for k in names) for i in range(n)]
    residual = [max(0.0, 100.0 - s) for s in sums]

    plot = dict(segments)
    if any(r > 0.05 for r in residual):
        names = names + ["Other / uncoded"]
        plot = dict(plot)
        plot["Other / uncoded"] = residual

    if figsize is None:
        figsize = (9.6, 1.5 + 0.40 * n)
    fig, ax = _fig(figsize=figsize)
    y = list(range(n))[::-1]
    colors = [CHARCOAL, GRAY_MED, RED, GRAY_LIGHT]
    for i in range(n):
        left = 0.0
        for j, k in enumerate(names):
            v = plot[k][i]
            if v <= 0:
                continue
            ax.barh(y[i], v, left=left, height=0.58,
                    color=colors[j % len(colors)], zorder=2,
                    label=k if i == 0 else None)
            # only label a leg that has room for the text
            if v >= 9:
                ax.text(left + v / 2, y[i], value_fmt.format(v), ha="center",
                        va="center", fontsize=9.5, color=WHITE, zorder=3)
            left += v
        ax.text(101.5, y[i], f"{left:,.1f}%", ha="left", va="center",
                fontsize=9.5, color=GRAY)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5, color=INK)
    ax.set_xticks([])
    ax.set_xlim(0, 112)
    # legend ABOVE the plot so it can never sit on the bars
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), frameon=False,
              fontsize=10, ncol=min(len(names), 4), handlelength=1.2,
              columnspacing=1.4)
    if right_note:
        ax.text(101.5, n - 0.35, right_note, fontsize=9.5, color=GRAY,
                va="bottom")
    ax.margins(y=0.14)
    _title(ax, title, subtitle)
    if subtitle:
        plt.gcf().subplots_adjust(top=0.84)
    return _save(fig, filename)


# --------------------------------------------------------------- 7 heatmap
def heatmap(rows, cols, values, filename, title=None, subtitle=None,
            value_fmt="{:,.0f}", cmap_colors=(WHITE, CHARCOAL), figsize=None,
            row_norm=True):
    """Pattern across two dimensions. Darker = higher (row-normalised by default).

    values: list of lists (rows x cols). None renders as a light hatch cell.
    """
    if figsize is None:
        figsize = (11.0, 1.4 + 0.34 * len(rows))
    fig, ax = _fig(figsize=figsize)
    nr, nc = len(rows), len(cols)
    flat = [v for r in values for v in r if v is not None]
    vmax = max(flat) if flat else 1
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("isze", list(cmap_colors))
    for i, row in enumerate(values):
        norm_row = row
        if row_norm and any(v is not None for v in row):
            mx = max(v for v in row if v is not None) or 1
            norm_row = [(v / mx if v is not None else None) for v in row]
        for j, v in enumerate(norm_row):
            if v is None:
                ax.add_patch(Rectangle((j, nr - 1 - i), 1, 1, facecolor=GRAY_BG,
                                       edgecolor=WHITE, lw=1.2, hatch="//"))
                continue
            ax.add_patch(Rectangle((j, nr - 1 - i), 1, 1,
                                   facecolor=cmap(min(v, 1) if row_norm else v / vmax),
                                   edgecolor=WHITE, lw=1.2))
            raw = row[j]
            txt_col = WHITE if (min(v, 1) if row_norm else v / vmax) > 0.55 else INK
            ax.text(j + 0.5, nr - 1 - i + 0.5, value_fmt.format(raw),
                    ha="center", va="center", fontsize=8.6, color=txt_col, zorder=3)
    ax.set_xlim(0, nc)
    ax.set_ylim(0, nr)
    ax.set_xticks([j + 0.5 for j in range(nc)])
    ax.set_xticklabels(cols, rotation=32, ha="left", fontsize=9.5, color=INK)
    ax.xaxis.set_ticks_position("top")
    ax.set_yticks([nr - 1 - i + 0.5 for i in range(nr)])
    ax.set_yticklabels(rows, fontsize=10, color=INK)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    _title(ax, title, subtitle)
    return _save(fig, filename)


# ---------------------------------------------------------------- 8 fan band
def fan_band(x_labels, history, band_lo, band_hi, filename, title=None,
             subtitle=None, break_at=None, break_label=None,
             as_published=None, value_fmt="{:,.0f}", figsize=(9.6, 4.6)):
    """Projection drawn as a RANGE between two documented methods.

    The method break is drawn on the axis, and the as-published figure is a
    dashed reference that stops before it leaves the band. Never draw a
    projection as a single unqualified line.
    """
    fig, ax = _fig(figsize=figsize)
    xs = list(range(len(x_labels)))
    n_hist = len(history)
    ax.fill_between(xs[n_hist - 1:], band_lo, band_hi, color=GRAY_BG, zorder=1)
    ax.plot(xs[:n_hist], history, color=CHARCOAL, lw=2.6, marker="o",
            markersize=5, zorder=4)
    ax.plot(xs[n_hist - 1:], band_hi, color=GRAY_MED, lw=1.6, ls=(0, (4, 3)),
            zorder=3)
    ax.plot(xs[n_hist - 1:], band_lo, color=GRAY_MED, lw=1.6, ls=(0, (4, 3)),
            zorder=3)
    if break_at is not None:
        ax.axvline(break_at, color=RED, lw=1.4, ls=(0, (3, 3)), zorder=5)
        ax.text(break_at + 0.06, ax.get_ylim()[0], break_label or "method break",
                fontsize=9.5, color=RED_DEEP, va="bottom", rotation=90)
    if as_published is not None:
        ax.plot(xs[n_hist - 1:], as_published, color=RED_DEEP, lw=2.0,
                ls=(0, (6, 4)), zorder=6, label="as published")
        ax.legend(loc="upper left", frameon=False, fontsize=10)
    ax.annotate(f"{value_fmt.format(band_hi[-1])}", xy=(xs[-1], band_hi[-1]),
                xytext=(8, 6), textcoords="offset points", fontsize=10, color=INK)
    ax.annotate(f"{value_fmt.format(band_lo[-1])}", xy=(xs[-1], band_lo[-1]),
                xytext=(8, -14), textcoords="offset points", fontsize=10, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels(x_labels, fontsize=10.5, color=GRAY)
    ax.set_yticks([])
    for s in ("bottom",):
        ax.spines[s].set_visible(False)
    _title(ax, title, subtitle)
    return _save(fig, filename)


# ------------------------------------------------------------- 9 quadrants
def bubble_quad(points, filename, title=None, subtitle=None,
                xlabel="", ylabel="", quad_labels=None,
                size_scale=1.0, figsize=(9.2, 5.6), fmt=None):
    """Two axes, four labelled quadrants, bubble size = a third measure.

    points: list of dicts {x, y, size, label, hot}
    """
    fig, ax = _fig(figsize=figsize)
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    sizes = [max(30, p.get("size", 1) * size_scale) for p in points]
    x_mid = (min(xs) + max(xs)) / 2
    y_mid = (min(ys) + max(ys)) / 2
    ax.axvline(x_mid, color=GRAY_LIGHT, lw=1.1, ls=(0, (4, 4)), zorder=1)
    ax.axhline(y_mid, color=GRAY_LIGHT, lw=1.1, ls=(0, (4, 4)), zorder=1)
    for p, sz in zip(points, sizes):
        col = RED if p.get("hot") else CHARCOAL
        ax.scatter(p["x"], p["y"], s=sz, color=col, alpha=0.72, zorder=3,
                   edgecolor=WHITE, linewidth=1.0)
        ax.text(p["x"], p["y"], "  " + p["label"], fontsize=9.4,
                color=INK, va="center", zorder=4)
    if quad_labels:
        for (qx, qy), text in quad_labels.items():
            ax.text(qx, qy, text, fontsize=9.5, color=GRAY_MED,
                    ha="center", va="center", zorder=1, style="italic")
    ax.set_xlabel(xlabel, fontsize=10.5, color=GRAY)
    ax.set_ylabel(ylabel, fontsize=10.5, color=GRAY)
    ax.set_xticks([])
    ax.set_yticks([])
    _title(ax, title, subtitle)
    return _save(fig, filename)


# --------------------------------------------------------------- 10 big num
def kpi_strip(items, filename, title=None, figsize=None, per_row=4):
    """A row of big-number callouts. items: list of (label, value, sub)."""
    rows = (len(items) + per_row - 1) // per_row
    if figsize is None:
        figsize = (11.4, 1.5 * rows)
    fig, ax = _fig(figsize=figsize)
    ax.axis("off")
    for i, (label, value, sub) in enumerate(items):
        r, c = divmod(i, per_row)
        x = c / per_row + 0.02
        y = 1 - (r + 0.5) / rows
        ax.text(x, y + 0.20, label.upper(), fontsize=10, color=RED,
                fontweight="bold", transform=ax.transAxes)
        ax.text(x, y - 0.02, value, fontsize=26, color=CHARCOAL,
                fontweight="bold", transform=ax.transAxes)
        ax.text(x, y - 0.28, sub, fontsize=9.6, color=GRAY,
                transform=ax.transAxes)
        ax.add_patch(Rectangle((c / per_row - 0.005, (rows - r - 1) / rows),
                               1 / per_row - 0.02, 1 / rows - 0.10,
                               facecolor="#F4F4F4", edgecolor="none",
                               transform=ax.transAxes, zorder=0))
    if title:
        ax.set_title(title, loc="left", fontsize=13.5, color=INK,
                     fontweight="bold")
    return _save(fig, filename)
