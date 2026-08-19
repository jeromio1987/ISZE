"""Build-time chart/table renderers — visible HTML/SVG without Chart.js.

Used by Aftermarket BI Command Center and sibling Tier A dashboards.
Page must look complete with JavaScript disabled.
"""

from __future__ import annotations

import html
import math
from typing import Any, Callable

# House palette (matches tier_a_dashboard_common CHART_COLORS)
COLORS = {
    "leak": "#c0552d",
    "over": "#15233c",
    "bal": "#1d9e75",
    "ink": "#52514e",
    "grid": "#e1e0d9",
    "blue": "#2a78d6",
    "paper": "#eef3f9",
}

SSR_CHART_CSS = """
.ssr-chart{width:100%;min-height:120px}
.bar-rows{display:flex;flex-direction:column;gap:5px;padding:4px 0}
.bar-row{display:flex;align-items:center;gap:8px;font-size:12px;line-height:1.2}
.bar-row .lbl{flex:0 0 auto;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#52514e;font-size:11px}
.bar-row .track{flex:1;height:16px;background:#eef3f9;border-radius:2px;overflow:hidden;min-width:40px}
.bar-row .fill{height:100%;border-radius:2px;min-width:2px}
.bar-row .val{flex:0 0 76px;text-align:right;font-variant-numeric:tabular-nums;color:#222;font-size:11px}
.ssr-svg{display:block;width:100%;height:auto;max-height:320px}
.ssr-legend{display:flex;flex-wrap:wrap;gap:10px 16px;margin-top:10px;font-size:11px;color:#52514e}
.ssr-legend span{display:inline-flex;align-items:center;gap:5px}
.ssr-legend i{display:inline-block;width:10px;height:10px;border-radius:2px}
.mix-bar{display:flex;height:22px;border-radius:3px;overflow:hidden;margin:8px 0 4px}
.mix-seg{height:100%;min-width:2px}
.ssr-line-chart .grid-line{stroke:#e1e0d9;stroke-width:1}
.ssr-line-chart .line-bill{fill:none;stroke:#15233c;stroke-width:2}
.ssr-line-chart .line-sell{fill:none;stroke:#c0552d;stroke-width:2}
.ssr-line-chart text{font-size:10px;fill:#52514e}
"""


def esc(s: Any) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def fmt_eur(n: Any) -> str:
    if n is None or n == "":
        return "—"
    try:
        f = float(n)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(f) or math.isinf(f):
        return "—"
    return "€" + f"{round(f):,}"


def fmt_int(n: Any) -> str:
    if n is None or n == "":
        return "—"
    try:
        return f"{round(float(n)):,}"
    except (TypeError, ValueError):
        return "—"


def fmt_num(n: Any, digits: int = 2) -> str:
    if n is None or n == "":
        return "—"
    try:
        return f"{float(n):.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def pill(cls: str, txt: str) -> str:
    return f'<span class="pill {esc(cls)}">{esc(txt)}</span>'


def _max_val(items: list[dict[str, Any]], value_key: str) -> float:
    vals = [float(x.get(value_key) or 0) for x in items]
    return max(vals) if vals else 1.0


def horizontal_bar_rows(
    items: list[dict[str, Any]],
    *,
    label_key: str,
    value_key: str,
    color: str = COLORS["leak"],
    max_items: int | None = None,
    label_width: int = 120,
    reverse: bool = False,
    label_fn: Callable[[dict[str, Any]], str] | None = None,
    value_fn: Callable[[Any], str] | None = None,
) -> str:
    """CSS horizontal bars — works without JS."""
    rows = list(items)
    if reverse:
        rows = list(reversed(rows))
    if max_items:
        rows = rows[:max_items]
    if not rows:
        return '<p class="cap">No data.</p>'
    mx = max(_max_val(rows, value_key), 1.0)
    parts = ['<div class="bar-rows ssr-chart">']
    for item in rows:
        lbl = label_fn(item) if label_fn else str(item.get(label_key) or "—")
        val = float(item.get(value_key) or 0)
        pct = min(100.0, 100.0 * val / mx) if mx else 0
        if val > 0 and pct < 0.5:
            pct = 0.5
        disp = value_fn(val) if value_fn else fmt_eur(val)
        parts.append(
            f'<div class="bar-row"><span class="lbl" style="width:{label_width}px" title="{esc(lbl)}">{esc(lbl)}</span>'
            f'<span class="track"><span class="fill" style="width:{pct:.1f}%;background:{color}"></span></span>'
            f'<span class="val">{disp}</span></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def vertical_bar_svg(
    items: list[dict[str, Any]],
    *,
    label_key: str,
    value_key: str,
    color: str = COLORS["leak"],
    width: int = 480,
    height: int = 260,
    value_fmt: Callable[[Any], str] | None = None,
) -> str:
    """Simple SVG vertical bar chart."""
    if not items:
        return '<p class="cap">No data.</p>'
    mx = max(_max_val(items, value_key), 1.0)
    n = len(items)
    pad_l, pad_r, pad_t, pad_b = 48, 12, 12, 36
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    bar_w = max(8, chart_w / max(n, 1) * 0.65)
    gap = chart_w / max(n, 1)
    lines = [
        f'<svg class="ssr-svg ssr-vbar" viewBox="0 0 {width} {height}" role="img" aria-label="Bar chart">',
        f'<line x1="{pad_l}" y1="{pad_t + chart_h}" x2="{width - pad_r}" y2="{pad_t + chart_h}" stroke="{COLORS["grid"]}"/>',
    ]
    for i, item in enumerate(items):
        val = float(item.get(value_key) or 0)
        h = chart_h * val / mx if mx else 0
        x = pad_l + i * gap + (gap - bar_w) / 2
        y = pad_t + chart_h - h
        lbl = str(item.get(label_key) or "")[:10]
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{max(h,1):.1f}" fill="{color}" rx="2"/>')
        lines.append(
            f'<text x="{x + bar_w/2:.1f}" y="{height - 8}" text-anchor="middle" font-size="10" fill="{COLORS["ink"]}">{esc(lbl)}</text>'
        )
        if value_fmt and val > 0:
            disp = value_fmt(val)
            lines.append(
                f'<text x="{x + bar_w/2:.1f}" y="{max(y - 4, pad_t + 8):.1f}" text-anchor="middle" font-size="9" fill="{COLORS["ink"]}">{esc(disp)}</text>'
            )
    lines.append("</svg>")
    return "".join(lines)


def pipeline_mix_bar(
    mix: dict[str, Any],
    *,
    labels: tuple[str, str, str] = ("Leakage €", "Overstock €", "Balanced sell-out €"),
    keys: tuple[str, str, str] = ("leakage", "overstock", "balanced"),
    colors: tuple[str, str, str] = (COLORS["leak"], COLORS["over"], COLORS["bal"]),
) -> str:
    vals = [float(mix.get(k) or 0) for k in keys]
    total = sum(vals) or 1.0
    segs = []
    legend = ['<div class="mix-bar ssr-chart">']
    for v, c in zip(vals, colors):
        pct = 100.0 * v / total
        if pct > 0:
            segs.append(f'<div class="mix-seg" style="width:{pct:.2f}%;background:{c}" title="{fmt_eur(v)}"></div>')
    legend.append("".join(segs))
    legend.append("</div><div class='ssr-legend'>")
    for lbl, v, c in zip(labels, vals, colors):
        legend.append(f"<span><i style='background:{c}'></i>{esc(lbl)}: {fmt_eur(v)}</span>")
    legend.append("</div>")
    return "".join(legend)


def line_chart_svg(
    points: list[dict[str, Any]],
    *,
    label_key: str = "label",
    series: tuple[tuple[str, str, str], ...] = (
        ("bill_eur", COLORS["ink"], "Bill €"),
        ("sellout_eur", COLORS["leak"], "Sell-out €"),
    ),
    width: int = 520,
    height: int = 260,
) -> str:
    if not points:
        return '<p class="cap">No monthly data.</p>'
    all_vals = []
    for _, key, _ in series:
        all_vals.extend(float(p.get(key) or 0) for p in points)
    mx = max(all_vals) if all_vals else 1.0
    mx = mx or 1.0
    pad_l, pad_r, pad_t, pad_b = 56, 16, 16, 32
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    n = len(points)
    if n < 2:
        return '<p class="cap">Insufficient months.</p>'

    def xy(i: int, val: float) -> tuple[float, float]:
        x = pad_l + (i / max(n - 1, 1)) * chart_w
        y = pad_t + chart_h - (val / mx) * chart_h
        return x, y

    lines = [
        f'<svg class="ssr-svg ssr-line-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Trend chart">',
        f'<line x1="{pad_l}" y1="{pad_t + chart_h}" x2="{width - pad_r}" y2="{pad_t + chart_h}" stroke="{COLORS["grid"]}"/>',
    ]
    for frac in (0.25, 0.5, 0.75, 1.0):
        gy = pad_t + chart_h * (1 - frac)
        gv = mx * frac
        lines.append(f'<line class="grid-line" x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}"/>')
        lines.append(f'<text x="{pad_l - 6}" y="{gy + 3:.1f}" text-anchor="end">{esc(fmt_eur(gv))}</text>')

    legend_bits = ['<div class="ssr-legend">']
    for key, color, name in series:
        coords = []
        path = []
        for i, p in enumerate(points):
            x, y = xy(i, float(p.get(key) or 0))
            coords.append((x, y))
            path.append(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}")
        lines.append(f'<polyline class="line" fill="none" stroke="{color}" stroke-width="2" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in coords)}"/>')
        legend_bits.append(f"<span><i style='background:{color}'></i>{esc(name)}</span>")
    legend_bits.append("</div>")

    for i, p in enumerate(points):
        x = pad_l + (i / max(n - 1, 1)) * chart_w
        lines.append(
            f'<text x="{x:.1f}" y="{height - 8}" text-anchor="middle">{esc(str(p.get(label_key) or ""))}</text>'
        )
    lines.append("</svg>")
    return "".join(lines) + "".join(legend_bits)


def hero_kpis(chips: list[tuple[str, str, str, str, Any]]) -> str:
    """Render hero KPI row. Each chip: (value_html, label, note, tip)."""
    parts = []
    for value_html, label, note, tip in chips:
        parts.append(
            f'<div class="hk" tabindex="0"><div class="v">{value_html}</div>'
            f'<div class="l">{esc(label)}</div><div class="n">{note}</div>'
            f'<div class="tip">{tip}</div></div>'
        )
    return "".join(parts)


def heatmap_table(
    data: list[dict[str, Any]],
    *,
    bucket_key: str = "bucket",
    action_key: str = "action",
    count_key: str = "count",
) -> str:
    if not data:
        return '<p class="cap">No heatmap data.</p>'
    buckets = list(dict.fromkeys(str(x.get(bucket_key) or "") for x in data))
    actions = list(dict.fromkeys(str(x.get(action_key) or "") for x in data))
    max_c = max(int(x.get(count_key) or 0) for x in data) or 1
    html_parts = ['<table class="matrix heatmap"><thead><tr><th class="rowhead">Bucket ↓ · Action →</th>']
    for a in actions:
        html_parts.append(f"<th>{esc(a.replace('REVIEW_', ''))}</th>")
    html_parts.append("</tr></thead><tbody>")
    for b in buckets:
        html_parts.append(f'<tr><td class="rowhead">{esc(b)}</td>')
        for a in actions:
            hit = next((x for x in data if x.get(bucket_key) == b and x.get(action_key) == a), None)
            v = int(hit.get(count_key) or 0) if hit else 0
            if v >= max_c * 0.6:
                cls = "hot"
            elif v >= max_c * 0.25:
                cls = "warm"
            elif v:
                cls = "cool"
            else:
                cls = "zero"
            html_parts.append(f'<td class="{cls}">{v if v else "—"}</td>')
        html_parts.append("</tr>")
    html_parts.append("</tbody></table>")
    return "".join(html_parts)
