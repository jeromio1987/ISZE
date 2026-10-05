"""Core blocks: the executive page, plan against actual, sales to dealer, availability.

Every number on these pages comes from a file. Nothing is typed in, so the deck can be
re-derived by anyone and cannot drift from the dashboards.
"""
from __future__ import annotations

import pandas as pd
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from ..context import BuildContext
from ..errors import BprError
from ..periods import Period, eur_compact, pct, qty, ratio
from ..theme import Deck

MOS_DAYS_PER_MONTH = 30.0


# ------------------------------------------------------------------ small helpers

def _delta(now: float | None, before: float | None) -> str:
    if not now or not before:
        return ""
    if before == 0:
        return ""
    return f"{(now / before - 1.0) * 100:+.1f}% on the same period last year"


def _last(values: pd.Series) -> float | None:
    if values is None or len(values) == 0:
        return None
    return float(values.iloc[-1])


def _first(values: pd.Series) -> float | None:
    if values is None or len(values) == 0:
        return None
    return float(values.iloc[0])


def _mean(values: pd.Series, tail: int = 3) -> float | None:
    if values is None or len(values) == 0:
        return None
    return float(values.tail(tail).mean())


def _period_bits(ctx: BuildContext) -> dict:
    """Everything the core pages share, gathered once."""
    bits: dict = {
        "billed_eur": None, "billed_prior": None, "billed_qty": None,
        "plan_eur": None, "plan_window": ([], []),
        "s2d_eur": None, "s2d_prior": None, "s2d_series": pd.Series(dtype="float64"),
        "s2d_through": None,
        "plan_source": "", "s2d_source": "",
    }

    billing = ctx.get("billing")
    if billing is not None:
        bits["billed_eur"] = billing.eur(ctx.period.start, ctx.period.end)
        bits["billed_prior"] = billing.eur(ctx.prior.start, ctx.prior.end)
        bits["billed_qty"] = billing.qty(ctx.period.start, ctx.period.end)
        bits["billed_series"] = billing.monthly(ctx.period.start, ctx.period.end)
    else:
        bits["billed_series"] = pd.Series(dtype="float64")

    plan = ctx.get("plan")
    if plan is not None:
        bits["plan_source"] = plan.source
        bits["plan_window"] = plan.window(ctx.period.start, ctx.period.end)
        bits["plan_eur"] = float(sum(bits["plan_window"][1]))
        bits["plan_map"] = plan.month_map()

    s2d = ctx.kpi_window("sales_to_dealer_eur")
    if not s2d.empty:
        bits["s2d_series"] = s2d
        bits["s2d_eur"] = float(s2d.sum())
        bits["s2d_through"] = s2d.index[-1]
        prior = ctx.kpi_window("sales_to_dealer_eur", ctx.prior)
        bits["s2d_prior"] = float(prior.sum()) if not prior.empty else None
        bits["s2d_source"] = "KPI Master File, Parts Sales DB to DLR in EUR"
    return bits


def _kpi_panel(ctx: BuildContext, extra: list[str] | None = None) -> list[str]:
    """The observations for the availability page, written from the numbers."""
    out: list[str] = list(extra or [])
    fill = ctx.kpi_window("fill_rate")
    mos = ctx.kpi_window("mos_days")
    back = ctx.kpi_window("back_orders")

    latest_fill = _last(fill)
    if latest_fill is not None:
        month = fill.index[-1]
        if latest_fill < 0.95:
            out.append(f"Individual fill rate is {pct(latest_fill)} at {month:%b %Y}, "
                       f"{(0.95 - latest_fill) * 100:.0f} points below the 95% target.")
        else:
            out.append(f"Individual fill rate is {pct(latest_fill)} at {month:%b %Y}, at or above the 95% target.")

    latest_mos = _last(mos)
    first_mos = _first(mos)
    if latest_mos is not None:
        months = latest_mos / MOS_DAYS_PER_MONTH
        line = f"Stock depth is {months:.1f} months at {mos.index[-1]:%b %Y}"
        if first_mos:
            line += f", against {first_mos / MOS_DAYS_PER_MONTH:.1f} months in {mos.index[0]:%b %Y}"
        out.append(line + ".")

    latest_back = _last(back)
    first_back = _first(back)
    if latest_back is not None and first_back is not None and first_back:
        change = (latest_back / first_back - 1) * 100
        out.append(f"Open back-order lines are {qty(latest_back)}, {change:+.0f}% over the period. "
                   "Read this with the fill rate, not on its own: fewer lines does not by itself mean better supply.")
    return out


# ------------------------------------------------------------------ executive

def render_exec(deck: Deck, ctx: BuildContext) -> list:
    """Eight tiles, each from a file, plus the management read."""
    bits = _period_bits(ctx)
    d = ctx.dist

    plan_eur = bits.get("plan_eur")
    billed = bits.get("billed_eur")
    plan_note = "the plan workbook" if bits.get("plan_source") else "no plan row found"
    if plan_eur and billed is not None:
        gap = billed - plan_eur
        vs = f"{gap / plan_eur * 100:+.1f}% against plan" if plan_eur else ""
        plan_big, plan_sub = eur_compact(billed), f"{ctx.period.label} billed vs {eur_compact(plan_eur)} planned\n{vs}"
        plan_colour = deck.pal.amber if gap < 0 else deck.pal.green
    else:
        plan_big, plan_sub, plan_colour = eur_compact(billed), f"billed in {ctx.period.label}", deck.pal.ink

    s2d = bits.get("s2d_eur")
    s2d_line = _delta(s2d, bits.get("s2d_prior"))
    s2d_sub = f"{ctx.period.label} reported by {d.display}"
    if s2d_line:
        s2d_sub += f"\n{s2d_line}"

    fill = _last(ctx.kpi_window("fill_rate"))
    mos_days = _last(ctx.kpi_window("mos_days"))
    back = _last(ctx.kpi_window("back_orders"))

    gps_info = None
    try:
        gps_info = ctx.get("gps")
    except BprError:
        gps_info = None

    fleet = None
    try:
        fleet = ctx.get("fleet")
    except BprError:
        fleet = None
    from ..periods import fiscal_year_of
    fy = fiscal_year_of(ctx.period.start)
    fleet_units = fleet.units(fy) if fleet else None

    tiles = [
        ("ISZE SALES VS PLAN", plan_big, plan_sub, plan_colour),
        ("SALES TO DEALER", eur_compact(s2d) if s2d else "not reported", s2d_sub, deck.pal.ink),
        ("INDIVIDUAL FILL RATE", pct(fill) if fill is not None else "not reported",
         "latest reported month\nagainst the 95% target", deck.pal.ink),
        ("MONTHS OF STOCK", f"{mos_days / MOS_DAYS_PER_MONTH:.1f}" if mos_days is not None else "not reported",
         f"from {mos_days:.0f} days of parts in stock" if mos_days is not None else "no stock depth reported",
         deck.pal.ink),
        ("BACK-ORDER LINES", qty(back) if back is not None else "not reported",
         "latest reported month", deck.pal.ink),
        ("GENUINE PARTS SHARE", pct(gps_info["capture"]) if gps_info and gps_info.get("capture") else "not quotable",
         f"parts billed against modelled spend\n{eur_compact(gps_info['billed_eur']) if gps_info and gps_info.get('billed_eur') else ''}".strip(),
         deck.pal.ink),
        ("FLEET", f"{fleet_units:,.0f}" if fleet_units else "not available",
         (f"vehicles in service, {ctx.period.label}\n{fleet.source.replace('_', ' ')}" if fleet else ""),
         deck.pal.ink),
    ]

    s = deck.add("Executive view",
                 f"{d.display}: where the plan, the dealer network and availability stand",
                 f"{ctx.period.label}, fiscal year unless the subtitle says otherwise",
                 "Sources: " + _source_line(ctx))
    tw, th, gx, gy = 2.2, 1.55, 0.13, 0.14
    for i, (label, big, sub, colour) in enumerate(tiles[:4]):
        s.tile(0.40 + i * (tw + gx), 1.82, tw, th, label, big, sub, colour, 22)
    for i, (label, big, sub, colour) in enumerate(tiles[4:7]):
        s.tile(0.40 + i * (tw + gx), 3.50, tw, th, label, big, sub, colour, 22)

    s.rect(0.40, 5.20, 9.20, 1.50, deck.pal.panel, deck.pal.border or None)
    s.text(0.60, 5.35, 8.8, 0.22, "MANAGEMENT READ", 8, deck.pal.accent, True)
    read_lines = _management_read(ctx, bits)
    s.text(0.60, 5.65, 8.8, 1.0, read_lines, 9.5, deck.pal.ink, spacing=7)

    s.panel(_exec_panel(ctx, bits))
    return [s]


def _source_line(ctx: BuildContext) -> str:
    return ("ISZE billing; I Motors sales-to-dealer reporting via the KPI Master File; "
            "the FY plan workbook; ISZE target-spend and service-demand files.")


def _management_read(ctx: BuildContext, bits: dict) -> list[str]:
    out = []
    billed, plan = bits.get("billed_eur"), bits.get("plan_eur")
    s2d, s2d_prior = bits.get("s2d_eur"), bits.get("s2d_prior")
    fill = _last(ctx.kpi_window("fill_rate"))

    if billed is not None and plan:
        gap = plan - billed
        if gap > 0:
            out.append(f"ISZE billing is {eur_compact(gap)} behind this period's plan.")
        else:
            out.append(f"ISZE billing is {eur_compact(-gap)} ahead of this period's plan.")
    if s2d and s2d_prior:
        out.append(f"The dealer network is {'up' if s2d > s2d_prior else 'down'} "
                   f"{abs(s2d / s2d_prior - 1) * 100:.0f}% on the same period last year, "
                   "so demand inside the network and replenishment from ISZE are telling different stories.")
    if fill is not None and fill < 0.95:
        out.append(f"Availability is the execution gap: fill rate is {pct(fill)} against a 95% target.")
    if not out:
        out.append("Not enough of the shared inputs are available to write a management read for this distributor.")
    return out


def _exec_panel(ctx: BuildContext, bits: dict) -> list[str]:
    out = []
    billed, plan = bits.get("billed_eur"), bits.get("plan_eur")
    if billed is not None and plan:
        out.append(f"Billing is {eur_compact(billed)} against {eur_compact(plan)} planned in {ctx.period.label}.")
    s2d = bits.get("s2d_eur")
    if s2d:
        out.append(f"The distributor reports {eur_compact(s2d)} of dealer sales in the same period "
                   "(their own reporting, not our billing).")
    out.append("Sales to dealer and ISZE billing are different stages at different prices. "
               "Do not read the two euro levels as a like-for-like margin.")
    out.append("Question: which families and which dealers moved, and did their replenishment follow?")
    return out


# ------------------------------------------------------------------ plan against actual

def render_plan(deck: Deck, ctx: BuildContext) -> list:
    bits = _period_bits(ctx)
    plan = ctx.get("plan")
    if plan is None:
        raise BprError("E401", "This distributor has no plan row, so plan against actual cannot be shown.",
                       db=ctx.dist.key)

    labels, planned = bits["plan_window"]
    billed_series = bits.get("billed_series", pd.Series(dtype="float64"))
    actual = []
    for month in plan.months:
        if not (ctx.period.start <= month <= ctx.period.end):
            continue
        value = billed_series.get(month if month in billed_series.index else None)
        if value is None and len(billed_series):
            hits = billed_series[billed_series.index.to_period("M") == month.to_period("M")]
            value = float(hits.iloc[0]) if len(hits) else 0.0
        actual.append(float(value or 0.0))

    planned_total = sum(planned)
    actual_total = sum(actual)
    gap = actual_total - planned_total

    s = deck.add("Plan against actual",
                 f"Monthly plan and what we billed, {ctx.period.label}",
                 f"{ctx.dist.display}  |  plan from the BP workbook, billing from the sales file  |  EUR",
                 f"Sources: {plan.source}; ISZE billing to {ctx.dist.display}.")

    cd = CategoryChartData()
    cd.categories = labels
    cd.add_series("Plan", s.chart_values(planned))
    cd.add_series("Billed", s.chart_values(actual))
    ch = s.chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.40, 1.80, 9.20, 3.60)
    s.style_chart(ch, '#,##0')
    for series, colour in zip(ch.plots[0].series, [deck.pal.grey, deck.pal.accent]):
        s.bar_fill(series, colour)

    s.tile(0.40, 5.55, 2.93, 1.15, "PLANNED", eur_compact(planned_total), f"for {ctx.period.label}", deck.pal.ink, 20)
    s.tile(3.53, 5.55, 2.93, 1.15, "BILLED", eur_compact(actual_total),
           f"{(actual_total / planned_total * 100) if planned_total else 0:.0f}% of plan",
           deck.pal.green if gap >= 0 else deck.pal.amber, 20)
    s.tile(6.67, 5.55, 2.93, 1.15, "GAP", eur_compact(gap),
           f"{gap / planned_total * 100:+.1f}% against plan" if planned_total else "",
           deck.pal.green if gap >= 0 else deck.pal.amber, 20)

    panel = [
        f"Plan for the period is {eur_compact(planned_total)}; we billed {eur_compact(actual_total)}"
        + (f", a gap of {eur_compact(-gap)}." if gap < 0 else f", {eur_compact(gap)} ahead."),
        "The plan row comes from the BP workbook by SAP sold-to code, so it can be re-derived; "
        "it is not a figure typed in from a report.",
    ]
    short_months = [i for i, (p, a) in enumerate(zip(planned, actual)) if p and a < p * 0.75]
    if gap < 0 and short_months:
        worst = ", ".join(labels[i] for i in short_months[:4])
        panel.append(f"The shortfall is concentrated in {worst}.")
    panel.append("Question: which categories and which dealers explain the gap, and what would close it?")
    s.panel(panel)
    return [s]


# ------------------------------------------------------------------ sales to dealer, euros

def render_s2d(deck: Deck, ctx: BuildContext) -> list:
    bits = _period_bits(ctx)
    series = bits.get("s2d_series", pd.Series(dtype="float64"))
    if series.empty:
        raise BprError("E401", f"{ctx.dist.display} has no reported dealer sales in {ctx.period.label}.",
                       db=ctx.dist.key)

    prior = ctx.kpi_window("sales_to_dealer_eur", ctx.prior)
    total, prior_total = float(series.sum()), float(prior.sum()) if not prior.empty else None

    s = deck.add("Sales to dealer",
                 f"{ctx.dist.display} reported dealer sales for {ctx.period.label}",
                 "The distributor's own reporting, in euros  |  their file, our read",
                 f"Source: KPI Master File.xlsx, Parts Handling - Parts Sales DB to DLR in EUR; "
                 f"latest reported month {series.index[-1]:%b %Y}.")

    cd = CategoryChartData()
    cd.categories = [f"{m:%b %y}" for m in series.index]
    cd.add_series(ctx.period.label, s.chart_values([float(v) for v in series.values]))
    if not prior.empty:
        cd.add_series(ctx.prior.label, s.chart_values([float(v) for v in prior.reindex(series.index).fillna(0).values]))
    ch = s.chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.40, 1.80, 9.20, 3.30)
    s.style_chart(ch, '#,##0')
    for series_obj, colour in zip(ch.plots[0].series, [deck.pal.accent, deck.pal.grey]):
        s.bar_fill(series_obj, colour)

    line = _delta(total, prior_total)
    s.tile(0.40, 5.25, 2.93, 1.45, ctx.period.label, eur_compact(total),
           line or "reported dealer sales", deck.pal.ink, 22)
    s.tile(3.53, 5.25, 2.93, 1.45, ctx.prior.label, eur_compact(prior_total) if prior_total else "not reported",
           "same window last year", deck.pal.muted, 22)
    peak_month = series.idxmax()
    s.tile(6.67, 5.25, 2.93, 1.45, "LARGEST MONTH", eur_compact(series.max()),
           f"{peak_month:%B %Y}", deck.pal.ink, 22)

    s.panel([
        f"Dealer sales in the period are {eur_compact(total)}"
        + (f", {line}." if line else "."),
        "This is the distributor's own reporting and it is not our billing. "
        "The two are different sales stages at different prices.",
        "Question: did their replenishment from ISZE follow the stronger dealer demand?",
        "Question: which dealers and families drove the peak month?",
    ])
    return [s]


# ------------------------------------------------------------------ availability

def render_avail(deck: Deck, ctx: BuildContext) -> list:
    fill = ctx.kpi_window("fill_rate")
    mos = ctx.kpi_window("mos_days")
    back = ctx.kpi_window("back_orders")
    if fill.empty and mos.empty and back.empty:
        raise BprError("E401", f"{ctx.dist.display} has no availability reporting in {ctx.period.label}.",
                       db=ctx.dist.key)

    s = deck.add("Availability",
                 "Fill rate, stock depth and back orders: the execution side of the same period",
                 f"{ctx.dist.display}  |  {ctx.period.label}  |  the distributor's own KPI reporting",
                 "Source: KPI Master File.xlsx, Parts Handling - First Fill Rate, Days of Parts in Stock, "
                 f"Back Order Lines; latest reported month "
                 f"{max([x.index[-1] for x in (fill, mos, back) if not x.empty], default=None):%b %Y}.")

    if not fill.empty:
        cd = CategoryChartData()
        cd.categories = [f"{m:%b %y}" for m in fill.index]
        cd.add_series("Individual fill rate", s.chart_values([float(v) for v in fill.values]))
        target = [0.95] * len(fill)
        cd.add_series("Target 95%", s.chart_values(target))
        ch = s.chart(XL_CHART_TYPE.LINE_MARKERS, cd, 0.40, 1.80, 4.45, 3.20)
        s.style_chart(ch, '0%', legend=True)
        s.axis_percent(ch)
        s.line_fmt(ch.plots[0].series[0], deck.pal.accent, 2.25, True, False)
        s.line_fmt(ch.plots[0].series[1], deck.pal.grey, 1.5, False, True)
        latest = float(fill.iloc[-1])
        s.text(0.40, 5.05, 4.45, 0.25,
               f"Latest {pct(latest)} at {fill.index[-1]:%b %Y} against the 95% target",
               9, deck.pal.ink, True)

    if not mos.empty:
        cd = CategoryChartData()
        cd.categories = [f"{m:%b %y}" for m in mos.index]
        cd.add_series("Days of parts in stock", s.chart_values([float(v) for v in mos.values]))
        ch = s.chart(XL_CHART_TYPE.LINE_MARKERS, cd, 5.10, 1.80, 4.50, 3.20)
        s.style_chart(ch, '#,##0', legend=False)
        s.line_fmt(ch.plots[0].series[0], deck.pal.amber, 2.25, True, False)
        latest_mos = float(mos.iloc[-1])
        s.text(5.10, 5.05, 4.50, 0.25,
               f"Latest {latest_mos:.0f} days = {latest_mos / MOS_DAYS_PER_MONTH:.1f} months at {mos.index[-1]:%b %Y}",
               9, deck.pal.ink, True)

    if not back.empty:
        cd = CategoryChartData()
        cd.categories = [f"{m:%b %y}" for m in back.index]
        cd.add_series("Open back-order lines", s.chart_values([float(v) for v in back.values]))
        ch = s.chart(XL_CHART_TYPE.LINE_MARKERS, cd, 0.40, 5.42, 9.20, 1.55)
        s.style_chart(ch, '#,##0', legend=False)
        s.line_fmt(ch.plots[0].series[0], deck.pal.green, 2.0, True, False)
        s.axis_bounds(ch)

    s.panel(_kpi_panel(ctx))
    return [s]
