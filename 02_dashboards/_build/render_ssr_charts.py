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
.donut-wrap{display:flex;flex-wrap:wrap;align-items:center;gap:16px;padding:8px 0}
.donut-svg{flex:0 0 auto;width:120px;height:120px}
.donut-legend{flex:1 1 140px;font-size:11px;color:#52514e;display:flex;flex-direction:column;gap:6px}
.donut-legend span{display:inline-flex;align-items:center;gap:6px}
.donut-legend i{display:inline-block;width:10px;height:10px;border-radius:50%}
.db-compare-strip{display:flex;gap:8px;align-items:flex-end;padding:12px 4px;min-height:160px}
.db-compare-col{flex:1 1 0;min-width:72px;display:flex;flex-direction:column;align-items:center;gap:6px}
.db-compare-col .bar{ width:100%;max-width:88px;border-radius:3px 3px 0 0;min-height:4px;background:#c0552d}
.db-compare-col .lbl{font-size:10px;color:#52514e;text-align:center;font-weight:600}
.db-compare-col .val{font-size:11px;color:#15233c;font-variant-numeric:tabular-nums;text-align:center}
.db-compare-note{font-size:10px;color:#6b6256;margin:4px 0 0;text-align:center;font-style:italic}
.db-compare-col.is-dominant .bar{opacity:.92;box-shadow:0 0 0 1px rgba(192,85,45,.35)}
.data-unavail{background:#fff3d6;border-left:4px solid #eda100;padding:14px 16px;margin:0 0 16px;font-size:14px;color:#222;border-radius:2px}
.data-unavail.greece{background:#eef3f9;border-left:4px solid #15233c;color:#15233c}
.data-unavail strong{color:#8a6500;font-family:Georgia,serif}
.data-unavail.greece strong{color:#15233c}
.chart-grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}
@media(max-width:900px){.chart-grid3{grid-template-columns:1fr}}
.ssr-line-chart .grid-line{stroke:#e1e0d9;stroke-width:1}
.ssr-line-chart .line-bill{fill:none;stroke:#15233c;stroke-width:2}
.ssr-line-chart .line-sell{fill:none;stroke:#c0552d;stroke-width:2}
.ssr-line-chart text{font-size:10px;fill:#52514e}
.ssr-waterfall{display:flex;flex-direction:column;gap:6px;padding:4px 0}
.wf-step{display:grid;grid-template-columns:120px 1fr 88px;gap:8px;align-items:center;font-size:12px}
.wf-step .lbl{color:#52514e;font-weight:600}
.wf-step .track{height:20px;background:#eef3f9;border-radius:2px;overflow:hidden}
.wf-step .fill{height:100%;border-radius:2px;min-width:2px}
.wf-step .val{text-align:right;font-variant-numeric:tabular-nums;color:#222}
.wf-step.wf-total .lbl{color:#15233c;font-family:Georgia,serif}
.spark-strip{display:flex;gap:10px;flex-wrap:wrap;padding:6px 0}
.spark-cell{flex:1 1 140px;min-width:120px;background:#faf8f4;border:1px solid #e8e4dc;padding:8px 10px}
.spark-cell .sl{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#6b6256}
.spark-cell .sv{font-size:13px;font-weight:700;color:#15233c;margin-top:2px}
.money-cards{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:12px 0}
.money-card{background:linear-gradient(145deg,#c0552d 0%,#a84826 100%);color:#f7f4ee;padding:16px 14px;border-radius:2px;min-height:120px;position:relative}
.money-card .rank{font-family:Georgia,serif;font-size:28px;opacity:.35;position:absolute;top:8px;right:12px}
.money-card .pn{font-family:Consolas,monospace;font-size:15px;font-weight:700;margin-bottom:4px}
.money-card .eur{font-size:22px;font-weight:700;letter-spacing:-.3px}
.money-card .meta{font-size:11px;opacity:.9;margin-top:8px;line-height:1.4}
.money-card .badge{display:inline-block;margin-top:8px;font-size:10px;text-transform:uppercase;letter-spacing:.06em;background:rgba(255,255,255,.18);padding:3px 8px}
.bullet-chart{padding:8px 0}
.bullet-row{margin-bottom:14px}
.bullet-row .bl{font-size:12px;color:#52514e;margin-bottom:4px;display:flex;justify-content:space-between}
.bullet-track{height:22px;background:#eef3f9;position:relative;border-radius:2px;overflow:visible}
.bullet-fill{height:100%;background:#15233c;border-radius:2px}
.bullet-mark{position:absolute;top:-4px;bottom:-4px;width:3px;background:#c0552d;z-index:2}
.bullet-legend{font-size:11px;color:#6b6256;margin-top:8px}
.treemap-wrap{display:flex;flex-wrap:wrap;gap:3px;padding:4px 0;min-height:140px}
.treemap-cell{display:flex;flex-direction:column;justify-content:flex-end;padding:8px;color:#f7f4ee;font-size:11px;min-width:48px;min-height:48px;border-radius:2px}
.treemap-cell .ta{font-weight:700;font-size:12px}
.treemap-cell .tv{font-variant-numeric:tabular-nums;margin-top:2px}
.leaderboard{list-style:none;margin:0;padding:0}
.leaderboard li{display:grid;grid-template-columns:28px 1fr auto;gap:10px;align-items:center;padding:8px 10px;border-bottom:1px solid #e8e4dc;font-size:13px;background:#fff}
.leaderboard li:nth-child(even){background:#faf8f4}
.leaderboard .rk{font-family:Georgia,serif;color:#c0552d;font-size:18px;text-align:center}
.leaderboard .nm{font-weight:600;color:#15233c}
.leaderboard .ev{font-variant-numeric:tabular-nums;color:#222;font-weight:600}
.section-nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px;padding:10px 0;position:sticky;top:48px;z-index:15;background:#f7f4ee;border-bottom:1px solid #d9d3c8}
.section-nav a{font-size:12px;color:#1a2b4a;text-decoration:none;background:#fff;border:1px solid #d9d3c8;padding:6px 12px}
.section-nav a:hover{border-color:#c0552d;color:#c0552d}
.so-what{border-left:3px solid #c0552d;background:#fff8f4;padding:8px 12px;margin:8px 0 12px;font-size:13px;color:#52514e;line-height:1.45}
.so-what strong{color:#c0552d;font-weight:600}
.radar-wrap{margin:4px 0}
.radar-toggle{display:flex;flex-wrap:wrap;gap:8px 14px;margin:0 0 10px;font-size:12px;color:#52514e}
.radar-toggle label{display:inline-flex;align-items:center;gap:4px;cursor:pointer}
.radar-toggle input{accent-color:#c0552d}
.heatmap-legend{display:flex;flex-wrap:wrap;gap:12px;margin:8px 0 0;font-size:11px;color:#52514e}
.heatmap-legend span{display:inline-flex;align-items:center;gap:4px}
.heatmap-legend i{display:inline-block;width:14px;height:14px;border-radius:2px}
.chart-footnote{font-size:10px;color:#6b6256;font-style:italic;margin:6px 0 0}
.spark-partial{font-size:9px;color:#c0552d;margin-top:2px}
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


def fmt_eur_compact(n: Any) -> str:
    """Display € — €573k / €1.2M for cards and chart labels; tables keep fmt_eur."""
    if n is None or n == "":
        return "—"
    try:
        f = float(n)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(f) or math.isinf(f):
        return "—"
    sign = "-" if f < 0 else ""
    f = abs(f)
    if f >= 1_000_000:
        v = f / 1_000_000
        return f"{sign}€{v:.1f}M".replace(".0M", "M")
    if f >= 10_000:
        return f"{sign}€{round(f / 1_000):,}k"
    if f >= 1_000:
        return f"{sign}€{f / 1_000:.1f}k".replace(".0k", "k")
    return sign + fmt_eur(f).lstrip("-")


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


def so_what(text: str) -> str:
    """Terracotta callout — one-line chart takeaway."""
    if not text:
        return ""
    return f'<p class="so-what"><strong>So what?</strong> {text}</p>'


def heatmap_color_legend(*, hot: str = "High", warm: str = "Medium", cool: str = "Low") -> str:
    """Colour-scale key for count/€ heatmaps."""
    return (
        f'<div class="heatmap-legend" aria-label="Colour scale">'
        f'<span><i style="background:#f8e4dc"></i>{esc(hot)}</span>'
        f'<span><i style="background:#fff3d6"></i>{esc(warm)}</span>'
        f'<span><i style="background:#eef3f9"></i>{esc(cool)}</span>'
        f'<span><i style="background:#fff;border:1px solid #e1e0d9"></i>None</span>'
        f"</div>"
    )


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
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(bar_w, 4):.1f}" height="{max(h, 4):.1f}" fill="{color}" rx="2"/>')
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
    labels: tuple[str, str, str] = ("Leakage €", "Overstock €", "Balanced sales to dealer €"),
    keys: tuple[str, str, str] = ("leakage", "overstock", "balanced"),
    colors: tuple[str, str, str] = (COLORS["leak"], COLORS["over"], COLORS["bal"]),
    value_fmt: Callable[[Any], str] | None = None,
) -> str:
    vals = [float(mix.get(k) or 0) for k in keys]
    total = sum(vals) or 1.0
    vf = value_fmt or fmt_eur
    segs = []
    legend = ['<div class="mix-bar ssr-chart">']
    for v, c in zip(vals, colors):
        pct = 100.0 * v / total
        if pct > 0:
            segs.append(f'<div class="mix-seg" style="width:{pct:.2f}%;background:{c}" title="{vf(v)}"></div>')
    legend.append("".join(segs))
    legend.append("</div><div class='ssr-legend'>")
    for lbl, v, c in zip(labels, vals, colors):
        legend.append(f"<span><i style='background:{c}'></i>{esc(lbl)}: {vf(v)}</span>")
    legend.append("</div>")
    return "".join(legend)


def line_chart_svg(
    points: list[dict[str, Any]],
    *,
    label_key: str = "label",
    series: tuple[tuple[str, str, str], ...] = (
        ("bill_eur", COLORS["ink"], "Bill €"),
        ("sellout_eur", COLORS["leak"], "Sales to dealer €"),
    ),
    width: int = 520,
    height: int = 260,
    partial_month_note: str | None = None,
) -> str:
    if not points:
        return '<p class="cap">No monthly data.</p>'
    all_vals = []
    for key, _, _ in series:
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

    note = partial_month_note
    if note is None and points:
        last_lbl = str(points[-1].get(label_key) or points[-1].get("month") or "")
        if last_lbl.startswith("12/") or last_lbl.endswith("-12") or "2025-12" in last_lbl:
            note = "Dec is partial month — bill line may cliff until full SAP close."
    for i, p in enumerate(points):
        x = pad_l + (i / max(n - 1, 1)) * chart_w
        lbl = str(p.get(label_key) or "")
        suffix = " †" if note and i == n - 1 else ""
        lines.append(
            f'<text x="{x:.1f}" y="{height - 8}" text-anchor="middle">{esc(lbl)}{suffix}</text>'
        )
    lines.append("</svg>")
    foot = f'<p class="chart-footnote">{esc(note)}</p>' if note else ""
    return "".join(lines) + "".join(legend_bits) + foot


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
    html_parts.append(heatmap_color_legend(hot="Hot = high count", warm="Warm = mid", cool="Cool = low"))
    return "".join(html_parts)


def waterfall_steps(
    steps: list[dict[str, Any]],
    *,
    label_key: str = "label",
    value_key: str = "eur",
    color_key: str = "color",
    default_color: str = COLORS["leak"],
) -> str:
    """CSS waterfall — network → DB → PN decomposition."""
    if not steps:
        return '<p class="cap">No waterfall data.</p>'
    mx = max(float(s.get(value_key) or 0) for s in steps) or 1.0
    parts = ['<div class="ssr-waterfall ssr-chart" role="img" aria-label="Leakage waterfall">']
    for i, s in enumerate(steps):
        lbl = str(s.get(label_key) or "—")
        val = float(s.get(value_key) or 0)
        pct = min(100.0, 100.0 * val / mx) if mx else 0
        if val > 0 and pct < 3.0 and i > 0:
            pct = 3.0
        col = str(s.get(color_key) or default_color)
        cls = "wf-step wf-total" if i == 0 or s.get("is_total") else "wf-step"
        parts.append(
            f'<div class="{cls}"><span class="lbl">{esc(lbl)}</span>'
            f'<span class="track"><span class="fill" style="width:{pct:.1f}%;background:{col}"></span></span>'
            f'<span class="val">{fmt_eur(val)}</span></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def pipeline_db_heatmap(
    rows: list[dict[str, Any]],
    *,
    db_key: str = "db",
    class_key: str = "pipe_class",
    value_key: str = "eur",
    classes: tuple[str, ...] = ("leakage", "overstock", "balanced"),
) -> str:
    """DB × pipeline class heatmap with € in cells."""
    if not rows:
        return '<p class="cap">No pipeline heatmap data.</p>'
    dbs = list(dict.fromkeys(str(r.get(db_key) or "") for r in rows))
    max_v = max(float(r.get(value_key) or 0) for r in rows) or 1.0
    parts = ['<table class="matrix heatmap ssr-chart"><thead><tr><th class="rowhead">DB ↓ · Class →</th>']
    for c in classes:
        parts.append(f"<th>{esc(c.title())}</th>")
    parts.append("</tr></thead><tbody>")
    for db in dbs:
        parts.append(f'<tr><td class="rowhead">{esc(db)}</td>')
        for c in classes:
            hit = next((r for r in rows if r.get(db_key) == db and r.get(class_key) == c), None)
            v = float(hit.get(value_key) or 0) if hit else 0
            if v >= max_v * 0.55:
                cls = "hot"
            elif v >= max_v * 0.2:
                cls = "warm"
            elif v > 0:
                cls = "cool"
            else:
                cls = "zero"
            cell = fmt_eur(v) if v else "—"
            parts.append(f'<td class="{cls}">{cell}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table>")
    parts.append(heatmap_color_legend(hot="Hot = high €", warm="Warm = mid €", cool="Cool = low €"))
    return "".join(parts)


def sell_through_bars(
    items: list[dict[str, Any]],
    *,
    label_key: str = "db",
    value_key: str = "pct",
    cap_pct: float = 200.0,
    color: str = COLORS["blue"],
) -> str:
    """Sell-through % bars — cap display width with footnote when actual > cap."""
    if not items:
        return '<p class="cap">No sell-through data.</p>'
    capped: list[dict[str, Any]] = []
    over: list[str] = []
    for item in items:
        actual = float(item.get(value_key) or 0)
        disp = min(actual, cap_pct)
        lbl = str(item.get(label_key) or "—")
        capped.append({label_key: lbl, value_key: disp, "_actual": actual})
        if actual > cap_pct:
            over.append(f"{lbl} {actual:.0f}%")
    chart = horizontal_bar_rows(
        capped,
        label_key=label_key,
        value_key=value_key,
        color=color,
        value_fn=lambda v: f"{int(v)}%",
    )
    foot = ""
    if over:
        foot = (
            f'<p class="chart-footnote">Bar capped at {int(cap_pct)}% for scale — actual: '
            f'{esc(", ".join(over))}. Ratio = dealer sales qty ÷ ISZE bill qty.</p>'
        )
    return chart + foot


def treemap_cells(
    items: list[dict[str, Any]],
    *,
    label_key: str = "aim",
    value_key: str = "gap_eur",
    max_items: int = 12,
) -> str:
    """Simple CSS treemap — area ∝ € at risk."""
    rows = sorted(items, key=lambda x: float(x.get(value_key) or 0), reverse=True)[:max_items]
    if not rows:
        return '<p class="cap">No AIM treemap data.</p>'
    total = sum(float(r.get(value_key) or 0) for r in rows) or 1.0
    palette = ["#c0552d", "#15233c", "#2a78d6", "#1d9e75", "#eda100", "#8a3030", "#6b6256", "#203759"]
    parts = ['<div class="treemap-wrap ssr-chart" role="img" aria-label="AIM treemap">']
    for i, item in enumerate(rows):
        val = float(item.get(value_key) or 0)
        flex = max(1.0, 100.0 * val / total)
        lbl = str(item.get(label_key) or "—").strip()
        if not lbl or lbl.lower() in ("—", "nan", "none"):
            lbl = "Unmapped AIM"
        col = palette[i % len(palette)]
        parts.append(
            f'<div class="treemap-cell" style="flex:{flex:.1f} 1 {int(flex * 8)}px;background:{col}" title="{esc(lbl)}: {fmt_eur(val)}">'
            f'<span class="ta">{esc(lbl[:18])}</span><span class="tv">{fmt_eur_compact(val)}</span></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def sparkline_strip(
    series_list: list[dict[str, Any]],
    *,
    points_key: str = "points",
    value_key: str = "sellout_eur",
    label_key: str = "label",
    width: int = 120,
    height: int = 36,
) -> str:
    """Mini SVG sparklines — one strip per DB or metric."""
    if not series_list:
        return '<p class="cap">No sparkline data.</p>'
    parts = ['<div class="spark-strip ssr-chart ssr-sparkline">']
    for s in series_list:
        pts = s.get(points_key) or []
        lbl = str(s.get(label_key) or "—")
        last_val = float(pts[-1].get(value_key) or 0) if pts else 0
        if len(pts) < 2:
            parts.append(
                f'<div class="spark-cell"><div class="sl">{esc(lbl)}</div>'
                f'<div class="sv">{fmt_eur(last_val)}</div><p class="cap">—</p></div>'
            )
            continue
        vals = [float(p.get(value_key) or 0) for p in pts]
        mx = max(vals) or 1.0
        pad = 2
        coords = []
        for i, v in enumerate(vals):
            x = pad + (i / max(len(vals) - 1, 1)) * (width - 2 * pad)
            y = pad + (height - 2 * pad) * (1 - v / mx)
            coords.append(f"{x:.1f},{y:.1f}")
        poly = " ".join(coords)
        partial = ""
        if pts and len(pts) >= 2:
            partial = '<div class="spark-partial">Last pt partial mo. †</div>'
        parts.append(
            f'<div class="spark-cell"><div class="sl">{esc(lbl)}</div>'
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<polyline fill="none" stroke="{COLORS["leak"]}" stroke-width="1.5" points="{poly}"/></svg>'
            f'<div class="sv">{fmt_eur_compact(last_val)}</div>{partial}</div>'
        )
    parts.append("</div>")
    parts.append(
        '<p class="chart-footnote">Sparklines end Dec CY2025 — last month is partial reporting window.</p>'
    )
    return "".join(parts)


def bullet_chart_dual(
    rows: list[dict[str, Any]],
    *,
    label_key: str = "label",
    actual_key: str = "actual_eur",
    target_key: str = "blocked_eur",
    max_key: str | None = None,
) -> str:
    """Ambition (actual) vs guardrail block marker."""
    if not rows:
        return '<p class="cap">No bullet data.</p>'
    parts = ['<div class="bullet-chart ssr-chart">']
    for r in rows:
        lbl = str(r.get(label_key) or "—")
        actual = float(r.get(actual_key) or 0)
        blocked = float(r.get(target_key) or 0)
        mx = float(r.get(max_key) or 0) if max_key and r.get(max_key) else max(actual, blocked, 1.0)
        ap = min(100.0, 100.0 * actual / mx)
        mp = min(100.0, 100.0 * blocked / mx)
        parts.append(
            f'<div class="bullet-row"><div class="bl"><span>{esc(lbl)}</span>'
            f'<span>{fmt_eur(actual)} vs block {fmt_eur(blocked)}</span></div>'
            f'<div class="bullet-track"><div class="bullet-fill" style="width:{ap:.1f}%"></div>'
            f'<div class="bullet-mark" style="left:{mp:.1f}%"></div></div></div>'
        )
    parts.append(
        f'<div class="bullet-legend"><span style="color:{COLORS["over"]}">■</span> Weighted ambition € '
        f'<span style="color:{COLORS["leak"]};margin-left:12px">|</span> Guardrail blocked €</div>'
    )
    parts.append("</div>")
    return "".join(parts)


def scatter_svg(
    points: list[dict[str, Any]],
    *,
    x_key: str = "ks_index",
    y_key: str = "gap_eur",
    label_key: str = "pn",
    width: int = 480,
    height: int = 280,
    x_label: str = "KS index",
    y_label: str = "€ gap",
) -> str:
    """SVG scatter — IAM price index vs € gap."""
    if not points:
        return '<p class="cap">No scatter data.</p>'
    xs = [float(p.get(x_key) or 0) for p in points]
    ys = [float(p.get(y_key) or 0) for p in points]
    xmin, xmax = min(xs) - 0.05, max(xs) + 0.05
    ymin, ymax = 0, max(ys) * 1.08 or 1.0
    if xmax <= xmin:
        xmax = xmin + 1
    pad_l, pad_r, pad_t, pad_b = 48, 16, 16, 32
    cw, ch = width - pad_l - pad_r, height - pad_t - pad_b

    def xy(x: float, y: float) -> tuple[float, float]:
        px = pad_l + (x - xmin) / (xmax - xmin) * cw
        py = pad_t + ch - (y - ymin) / max(ymax - ymin, 1) * ch
        return px, py

    lines = [
        f'<svg class="ssr-svg ssr-scatter" viewBox="0 0 {width} {height}" role="img" aria-label="Scatter chart">',
        f'<line x1="{pad_l}" y1="{pad_t + ch}" x2="{width - pad_r}" y2="{pad_t + ch}" stroke="{COLORS["grid"]}"/>',
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + ch}" stroke="{COLORS["grid"]}"/>',
    ]
    ref_x, _ = xy(1.0, 0)
    lines.append(
        f'<line x1="{ref_x:.1f}" y1="{pad_t}" x2="{ref_x:.1f}" y2="{pad_t + ch}" '
        f'stroke="{COLORS["leak"]}" stroke-dasharray="4,3" opacity=".6"/>'
    )
    lines.append(f'<text x="{ref_x:.1f}" y="{pad_t + 10}" text-anchor="middle" font-size="9" fill="{COLORS["leak"]}">index=1</text>')
    for p in points:
        x, y = float(p.get(x_key) or 0), float(p.get(y_key) or 0)
        px, py = xy(x, y)
        lbl = str(p.get(label_key) or "")[:8]
        col = COLORS["leak"] if x < 1 else COLORS["blue"]
        lines.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{col}" opacity=".85"><title>{esc(lbl)}: {fmt_eur(y)}</title></circle>')
    lines.append(f'<text x="{width/2:.0f}" y="{height - 6}" text-anchor="middle" font-size="10" fill="{COLORS["ink"]}">{esc(x_label)}</text>')
    lines.append(f'<text x="12" y="{pad_t + ch/2:.0f}" transform="rotate(-90 12 {pad_t + ch/2:.0f})" font-size="10" fill="{COLORS["ink"]}">{esc(y_label)}</text>')
    lines.append("</svg>")
    return "".join(lines)


def radar_lite_svg(
    entities: list[dict[str, Any]],
    *,
    label_key: str = "db",
    metrics: tuple[tuple[str, str], ...] = (
        ("leakage_pct", "Leakage"),
        ("overstock_pct", "Overstock"),
        ("sell_through", "Sell-through"),
        ("pn_density", "PN density"),
        ("gap_share", "Gap share"),
    ),
    size: int = 320,
    default_visible: int = 3,
    chart_id: str = "dbRadar",
) -> str:
    """Lightweight radar — normalized 0–100 per metric; toggle DB overlays (default top N)."""
    if not entities:
        return '<p class="cap">No radar data.</p>'
    cx, cy, r = size / 2, size / 2, size * 0.32
    n = len(metrics)
    if n < 3:
        return '<p class="cap">Need ≥3 metrics for radar.</p>'
    palette = [COLORS["leak"], COLORS["blue"], COLORS["bal"], COLORS["over"], "#eda100"]
    ranked = sorted(entities, key=lambda e: float(e.get("gap_share") or 0), reverse=True)
    default_dbs = {str(e.get(label_key) or "") for e in ranked[: max(1, default_visible)]}

    def pt(angle_i: int, val_pct: float, *, label: bool = False) -> tuple[float, float]:
        ang = -math.pi / 2 + (2 * math.pi * angle_i / n)
        scale = 1.12 if label else 1.0
        rad = r * scale * min(max(val_pct, 0), 100) / 100.0
        return cx + rad * math.cos(ang), cy + rad * math.sin(ang)

    toggles = ['<div class="radar-toggle" role="group" aria-label="DB radar layers">']
    for ei, ent in enumerate(ranked[:5]):
        db = str(ent.get(label_key) or "")
        col = palette[ei % len(palette)]
        checked = " checked" if db in default_dbs else ""
        toggles.append(
            f'<label style="color:{col}"><input type="checkbox" data-radar-db="{esc(db)}"{checked}/> {esc(db)}</label>'
        )
    toggles.append("</div>")

    lines = [
        f'<div class="radar-wrap" id="{esc(chart_id)}">',
        "".join(toggles),
        f'<svg class="ssr-svg ssr-radar" viewBox="0 0 {size} {size}" role="img" aria-label="DB comparison radar">',
    ]
    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for i in range(n):
            x, y = pt(i, ring * 100)
            pts.append(f"{x:.1f},{y:.1f}")
        lines.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="{COLORS["grid"]}" stroke-width="1"/>')
    for i, (_, mname) in enumerate(metrics):
        x, y = pt(i, 100, label=True)
        lines.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="9" fill="{COLORS["ink"]}">{esc(mname)}</text>')

    for ei, ent in enumerate(ranked[:5]):
        db = str(ent.get(label_key) or "")
        col = palette[ei % len(palette)]
        poly_pts = []
        for mi, (mkey, _) in enumerate(metrics):
            v = float(ent.get(mkey) or 0)
            x, y = pt(mi, v)
            poly_pts.append(f"{x:.1f},{y:.1f}")
        vis = "" if db in default_dbs else ' style="display:none"'
        lines.append(
            f'<g class="radar-layer" data-radar-db="{esc(db)}"{vis}>'
            f'<polygon points="{" ".join(poly_pts)}" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-width="1.5"/>'
            f"</g>"
        )

    lines.append("</svg></div>")
    lines.append(
        f"<script>(function(){{var w=document.getElementById('{esc(chart_id)}');if(!w)return;"
        f"w.querySelectorAll('input[data-radar-db]').forEach(function(cb){{"
        f"cb.onchange=function(){{var db=cb.getAttribute('data-radar-db');"
        f"w.querySelectorAll('.radar-layer[data-radar-db=\"'+db+'\"]').forEach(function(g){{"
        f"g.style.display=cb.checked?'':'none';}});}};}});}})();</script>"
    )
    return "".join(lines)


def money_on_table_cards(items: list[dict[str, Any]], *, max_cards: int = 5) -> str:
    """Large terracotta ranked cards — top leakage PNs."""
    rows = list(items)[:max_cards]
    if not rows:
        return '<p class="cap">No ranked leakage PNs.</p>'
    parts = ['<div class="money-cards ssr-chart ssr-money-cards">']
    for i, r in enumerate(rows):
        pn = str(r.get("pn") or "—")
        db = str(r.get("db") or "")
        aim = str(r.get("aim") or "—")
        action = str(r.get("action") or r.get("signal") or "Review")
        parts.append(
            f'<div class="money-card"><span class="rank">#{i + 1}</span>'
            f'<div class="pn" title="{esc(pn)}">{esc(pn)}</div><div class="eur">{fmt_eur_compact(r.get("gap_eur"))}</div>'
            f'<div class="meta">{esc(db)} · {esc(aim)}</div>'
            f'<span class="badge">{esc(action)}</span></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def mini_leaderboard(
    items: list[dict[str, Any]],
    *,
    name_key: str = "dealer",
    value_key: str = "gap_eur",
    value_fmt: Callable[[Any], str] | None = None,
) -> str:
    """Compact top-N leaderboard."""
    if not items:
        return '<p class="cap">No leaderboard data.</p>'
    vf = value_fmt or fmt_eur
    parts = ['<ol class="leaderboard ssr-chart ssr-leaderboard">']
    for i, r in enumerate(items):
        nm = str(r.get(name_key) or "—")
        val = vf(r.get(value_key))
        parts.append(f'<li><span class="rk">{i + 1}</span><span class="nm">{esc(nm)}</span><span class="ev">{val}</span></li>')
    parts.append("</ol>")
    return "".join(parts)


def section_nav(anchors: list[tuple[str, str]]) -> str:
    """Sticky in-panel section jump links."""
    if not anchors:
        return ""
    parts = ['<nav class="section-nav" aria-label="Section navigation">']
    for aid, lbl in anchors:
        parts.append(f'<a href="#{esc(aid)}">{esc(lbl)}</a>')
    parts.append("</nav>")
    return "".join(parts)


def aim_family_bars(
    items: list[dict[str, Any]],
    *,
    label_key: str = "aim",
    value_key: str = "gap_eur",
    max_items: int = 10,
    color: str = COLORS["blue"],
) -> str:
    """AIM L1 family horizontal bars — sorted by € gap."""
    rows = sorted(items, key=lambda x: float(x.get(value_key) or 0), reverse=True)[:max_items]
    if not rows:
        return '<p class="cap">No AIM family leakage € in this DB cut.</p>'
    return horizontal_bar_rows(
        rows,
        label_key=label_key,
        value_key=value_key,
        color=color,
        max_items=max_items,
        label_width=140,
    )


def pipeline_donut_svg(
    mix: dict[str, Any],
    *,
    labels: tuple[str, str, str] = ("Leakage €", "Overstock €", "Balanced €"),
    keys: tuple[str, str, str] = ("leakage", "overstock", "balanced"),
    colors: tuple[str, str, str] = (COLORS["leak"], COLORS["over"], COLORS["bal"]),
    size: int = 120,
    stroke: int = 22,
    value_fmt: Callable[[Any], str] | None = None,
) -> str:
    """Mini SVG donut — leakage vs overstock vs balanced."""
    vals = [max(0.0, float(mix.get(k) or 0)) for k in keys]
    total = sum(vals)
    vf = value_fmt or fmt_eur
    if total <= 0:
        return '<p class="cap">No pipeline € split — dealer sales missing or all zero.</p>'
    cx, cy, r = size / 2, size / 2, (size - stroke) / 2 - 2
    parts = [
        f'<div class="donut-wrap ssr-chart ssr-donut" role="img" aria-label="Pipeline mix donut">',
        f'<svg class="donut-svg" viewBox="0 0 {size} {size}">',
    ]
    start = -math.pi / 2
    for v, col in zip(vals, colors):
        if v <= 0:
            continue
        frac = v / total
        sweep = 2 * math.pi * frac
        end = start + sweep
        x1, y1 = cx + r * math.cos(start), cy + r * math.sin(start)
        x2, y2 = cx + r * math.cos(end), cy + r * math.sin(end)
        large = 1 if frac > 0.5 else 0
        parts.append(
            f'<path d="M {x1:.2f} {y1:.2f} A {r:.2f} {r:.2f} 0 {large} 1 {x2:.2f} {y2:.2f}" '
            f'fill="none" stroke="{col}" stroke-width="{stroke}" stroke-linecap="butt"/>'
        )
        start = end
    parts.append("</svg><div class='donut-legend'>")
    for lbl, v, col in zip(labels, vals, colors):
        pct = 100.0 * v / total
        parts.append(f"<span><i style='background:{col}'></i>{esc(lbl)}: {vf(v)} ({pct:.0f}%)</span>")
    parts.append("</div></div>")
    return "".join(parts)


def leakage_db_comparison(
    items: list[dict[str, Any]],
    *,
    label_key: str = "db",
    value_key: str = "gap_eur",
    color: str = COLORS["leak"],
    height: int = 120,
    log_scale: bool = True,
    value_fmt: Callable[[Any], str] | None = None,
) -> str:
    """Network comparison strip — five DBs side-by-side bars."""
    rows = list(items)
    if not rows:
        return '<p class="cap">No DB leakage to compare.</p>'
    mx = max(_max_val(rows, value_key), 1.0)
    vf = value_fmt or fmt_eur_compact
    use_log = log_scale and mx > 0 and len([r for r in rows if float(r.get(value_key) or 0) > 0]) > 1
    max_val = max(float(r.get(value_key) or 0) for r in rows)
    parts = ['<div class="db-compare-strip ssr-chart ssr-db-compare" role="img" aria-label="DB leakage comparison">']
    for item in rows:
        lbl = str(item.get(label_key) or "—")
        val = float(item.get(value_key) or 0)
        if use_log and val > 0:
            h = max(4, int(height * math.log10(val + 1) / math.log10(mx + 1)))
        else:
            h = max(4, int(height * val / mx)) if mx else 4
        col = color if val > 0 else COLORS["grid"]
        dom = " is-dominant" if val > 0 and val >= max_val * 0.85 else ""
        parts.append(
            f'<div class="db-compare-col{dom}" title="{esc(lbl)}: {vf(val)}">'
            f'<div class="val">{vf(val)}</div>'
            f'<div class="bar" style="height:{h}px;background:{col}"></div>'
            f'<div class="lbl">{esc(lbl)}</div></div>'
        )
    parts.append("</div>")
    if use_log and max_val > 0:
        ratio = mx / max(min(float(r.get(value_key) or 0) for r in rows if float(r.get(value_key) or 0) > 0), 1)
        if ratio > 5:
            parts.append('<p class="db-compare-note">Bar height log-scaled — labels show exact values · IUK-scale outlier visible</p>')
    return "".join(parts)


def data_unavailable_banner(
    db: str,
    *,
    message: str,
    overstock_pn: int = 0,
    iam_pn: int = 0,
    bill_qty: float = 0,
) -> str:
    """Banner when dealer sales qty=0 — leakage € not measurable."""
    stats = []
    if overstock_pn:
        stats.append(f"<strong>{fmt_int(overstock_pn)}</strong> overstock / no dealer sales PNs")
    if iam_pn:
        stats.append(f"<strong>{fmt_int(iam_pn)}</strong> PNs with IAM (KS) quotes")
    if bill_qty:
        stats.append(f"<strong>{fmt_int(bill_qty)}</strong> bill qty in register")
    stat_line = " · ".join(stats) if stats else "Register has rows but no positive leakage €."
    extra_cls = " greece" if db.upper() == "GREECE" else ""
    return (
        f'<div class="data-unavail{extra_cls}" role="alert">'
        f"<strong>{esc(db)} — DATA UNAVAILABLE for leakage €</strong><br/>"
        f"{esc(message)}<br/>{stat_line}</div>"
    )
