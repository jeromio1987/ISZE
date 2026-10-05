"""Analysis blocks: their data, the stock comparison, fleet, genuine share, service cover, mix.

The stock comparison is the heart of these slides: what we billed the distributor against what
they told us they sold to their dealers, family by family. A fall in our billing is not a loss
if their dealer sales held up and they are living off stock; that is what this separates.
"""
from __future__ import annotations

import pandas as pd
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import MSO_ANCHOR

from ..context import BuildContext
from ..errors import BprError
from ..inputs.catalog import FAMILY_LABEL, FAMILY_KEYS, family_units
from ..periods import eur_compact, fiscal_year_of, pct, qty, ratio
from ..theme import Deck

BUYING_AHEAD = 1.15      # buying more than dealers take: stock is building
RUNNING_DOWN = 0.95      # buying less than dealers take: stock is being used up


def _family_table(ctx: BuildContext, period, label: str) -> pd.DataFrame:
    """Billed units against units they reported selling to dealers, by service family."""
    billing = ctx.get("billing")
    sellout = ctx.get("sellout")
    if billing is None or sellout is None:
        raise BprError("E402", "This slide needs both our billing and their sales-to-dealer file.",
                       db=ctx.dist.key)

    billed = billing.window(period.start, period.end)[["part_number", "billed_qty"]]
    billed = billed.rename(columns={"part_number": "pn"})
    b_fam = family_units(billed, "billed_qty")
    if b_fam.empty:
        b_fam = pd.DataFrame(columns=["family", "bought"])
    else:
        b_fam = b_fam.rename(columns={"billed_qty": "bought"})

    sold = sellout.window(period.start, period.end)[["pn", "qty"]]
    s_fam = family_units(sold, "qty") if not sold.empty else pd.DataFrame(columns=["family", "qty"])
    if s_fam.empty:
        s_fam = pd.DataFrame(columns=["family", "sold"])
    else:
        s_fam = s_fam.rename(columns={"qty": "sold"})

    out = b_fam.merge(s_fam, on="family", how="outer")
    out["family"] = out["family"].astype(str)      # merge turns the category back into objects
    for col in ("bought", "sold"):
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["period"] = label
    out["ratio"] = out.apply(lambda r: (r.bought / r.sold) if r.sold else float("nan"), axis=1)
    return out


def _reading(value: float) -> tuple[str, str]:
    """plain words, and the colour to draw them in."""
    if pd.isna(value):
        return "not comparable", "muted"
    if value > BUYING_AHEAD:
        return "bought ahead of dealer sales", "amber"
    if value < RUNNING_DOWN:
        return "running stock down", "accent"
    return "in step with dealer sales", "green"


def _stock_window_note(ctx: BuildContext, sellout) -> str:
    """Say plainly whether their file reaches the end of the window being reported.

    Romania and UTI send one workbook per month, so the file can stop short of the period. The
    reader must never imply a full year when the months are not there.
    """
    if sellout.covers(ctx.period):
        return f"their file covers the whole window, through {sellout.last_month:%B %Y}"
    return (f"their file stops at {sellout.last_month:%B %Y}, so the "
            f"{ctx.period.label.split(' to ')[0]} columns cover only the months shown")


# ------------------------------------------------------------------ how we used their data

def render_s2d_units(deck: Deck, ctx: BuildContext) -> list:
    sellout = ctx.get("sellout")
    if sellout is None:
        raise BprError("E402", "No sales-to-dealer file for this distributor.", db=ctx.dist.key)

    fam_units = family_units(sellout.frame[["pn", "qty"]], "qty")
    in_families = float(fam_units.qty.sum()) if not fam_units.empty else 0.0
    first, last = sellout.months[0], sellout.months[-1]

    s = deck.add("Your data",
                 f"How we used the data {ctx.dist.display} shared",
                 "Sales to dealer by part number and month  |  quantities only, no prices",
                 f"Sources: {ctx.dist.display} sales-to-dealer file - {sellout.source_line()}; "
                 f"ISZE billing to {ctx.dist.display}; the ISZE parts catalogue.")

    cols = [
        ("WHAT YOU SHARED", [
            f"Sales to dealer: {len(sellout.frame):,} part-number months, "
            f"{sellout.pn_count:,} part numbers, {qty(sellout.total_qty)} units, "
            f"{first:%B %Y} to {last:%B %Y}.",
            f"The file is read in the format you sent it ({sellout.kind.replace('_', ' ')}); "
            "we do not ask you to reformat it.",
        ]),
        ("WHAT WE DID WITH IT", [
            f"Grouped part numbers into service families with the ISZE parts catalogue "
            f"({qty(in_families)} units fall in the seven families shown).",
            "Compared units you sold to dealers with units ISZE billed to you, family by family "
            "and month by month.",
        ]),
        ("WHAT WE DID NOT ASSUME", [
            "No dealer prices and no margins: every comparison is in units.",
            "Nothing before the first month in your file, and nothing sold outside it.",
        ]),
    ]
    cw = (9.20 - 2 * 0.20) / 3
    for k, (heading, points) in enumerate(cols):
        x = 0.40 + k * (cw + 0.20)
        s.rect(x, 1.85, cw, 3.90, deck.pal.panel, deck.pal.border or None)
        s.text(x + 0.20, 2.02, cw - 0.40, 0.25, heading, 8, deck.pal.accent, True)
        s.text(x + 0.20, 2.40, cw - 0.40, 3.20, [f"-  {p}" for p in points], 9.5,
               deck.pal.ink, spacing=9)

    s.panel([
        "Sales to dealer is the closest measure of real demand we have. "
        "What you buy from ISZE also includes a stock decision.",
        "Comparing the two shows when you bought ahead and when you ran stock down, family by family.",
        "The next slides use this to separate stock timing from a real change in dealer demand.",
        "Question: can the monthly file keep coming, and could a monthly stock snapshot come with it?",
    ])
    return [s]


# ------------------------------------------------------------------ stock movement

def render_stock(deck: Deck, ctx: BuildContext) -> list:
    get = ctx.get
    sellout = get("sellout")
    if sellout is None:
        raise BprError("E402", "No sales-to-dealer file, so this comparison cannot be made.", db=ctx.dist.key)

    now = _family_table(ctx, ctx.period, ctx.period.label)
    before = _family_table(ctx, ctx.prior, ctx.prior.label)

    s = deck.add("Stock movement",
                 f"Bought from ISZE against sold to dealers, by service family",
                 f"Units  |  {before.period.iloc[0] if len(before) else ctx.prior.label} and "
                 f"{ctx.period.label}  |  ratio is what you bought divided by what you sold",
                 f"Source: ISZE billing to {ctx.dist.display}; {ctx.dist.display} sales to dealer - "
                 f"{sellout.source_line()}  |  {_stock_window_note(ctx, sellout)}")

    rows = []
    numeric = []
    for fam in FAMILY_KEYS:
        b = now[now.family == fam]
        a = before[before.family == fam]
        bought_now = float(b.bought.iloc[0]) if len(b) else 0.0
        sold_now = float(b.sold.iloc[0]) if len(b) else 0.0
        bought_before = float(a.bought.iloc[0]) if len(a) else 0.0
        sold_before = float(a.sold.iloc[0]) if len(a) else 0.0
        r_now = (bought_now / sold_now) if sold_now else float("nan")
        r_before = (bought_before / sold_before) if sold_before else float("nan")
        words, _colour = _reading(r_now)
        rows.append((FAMILY_LABEL[fam], qty(bought_before), qty(sold_before), ratio(r_before),
                     qty(bought_now), qty(sold_now), ratio(r_now), words))
        numeric.append((FAMILY_LABEL[fam], r_now))

    s.table(0.40, 1.85, [1.35, 0.95, 0.90, 0.72, 0.95, 0.90, 0.72, 2.71],
            ["Family",
             f"{ctx.prior.label} bought", f"{ctx.prior.label} sold", "ratio",
             f"{ctx.period.label} bought", f"{ctx.period.label} sold", "ratio", "Reading"],
            rows, row_h=0.38, bold_cols=(0, 7))

    s.text(0.40, 5.20, 9.20, 0.22,
           f"Ratio is what you bought from ISZE divided by what you sold to dealers. "
           f"Below {RUNNING_DOWN:.2f} means stock is being used up; above {BUYING_AHEAD:.2f} means stock is building.",
           7.5, deck.pal.faint)

    running_down = [name for name, r in numeric if not pd.isna(r) and r < RUNNING_DOWN]
    built = [name for name, r in numeric if not pd.isna(r) and r > BUYING_AHEAD]
    panel = []
    if running_down:
        panel.append(f"Stock is being used up in {len(running_down)} of the seven families: "
                     + ", ".join(running_down) + ".")
    if built:
        panel.append("Bought ahead of dealer sales in " + ", ".join(built) + ".")
    if not panel:
        panel.append("Purchases and dealer sales are broadly in step across the seven families.")
    panel.append("A fall in our billing is not by itself lost business: if dealer demand held up "
                 "while purchases fell, they are living off stock.")
    panel.append("Question: what stock is on hand by family, and at what level will normal orders return?")
    s.panel(panel)
    return [s]


# ------------------------------------------------------------------ fleet

def render_fleet(deck: Deck, ctx: BuildContext) -> list:
    fleet = ctx.get("fleet")
    if fleet is None or not fleet.by_fy:
        raise BprError("E401", f"No vehicle count is available for {ctx.dist.display}.",
                       db=ctx.dist.key)

    fys = sorted(fleet.by_fy)
    recent = [fy for fy in fys if fy >= fiscal_year_of(ctx.period.start) - 3]
    labels = [f"FY{fy}" for fy in recent]
    values = [fleet.by_fy[fy] for fy in recent]

    s = deck.add("Fleet",
                 "Vehicles in service, the denominator under every per-vehicle figure",
                 f"{ctx.dist.display}  |  fiscal years, April to March  |  {fleet.source.replace('_', ' ')}",
                 f"Source: {fleet.source_sentence()}")

    cd = CategoryChartData()
    cd.categories = labels
    cd.add_series("Vehicles in service", s.chart_values(values))
    ch = s.chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cd, 0.40, 1.80, 4.60, 3.40)
    s.style_chart(ch, '#,##0', legend=False)
    s.bar_fill(ch.plots[0].series[0], deck.pal.accent)

    latest_fy = recent[-1]
    growth = ""
    if len(recent) > 1:
        first, last = fleet.by_fy[recent[0]], fleet.by_fy[recent[-1]]
        if first:
            growth = f"{(last / first - 1) * 100:+.1f}% since FY{recent[0]}"

    s.tile(5.20, 1.85, 4.40, 1.00, f"FY{latest_fy}", f"{fleet.by_fy[latest_fy]:,.0f}",
           ("vehicles in service on this count\n" + growth).strip(), deck.pal.ink, 24)

    notes = fleet.by_fy_band.get(latest_fy) or {}
    if notes:
        band_rows = [(k, qty(v)) for k, v in notes.items() if v]
        s.table(5.20, 3.00, [2.10, 2.30], ["Counting method", "Vehicles"], band_rows, row_h=0.32)
    else:
        s.rect(5.20, 3.00, 4.40, 1.20, deck.pal.panel, deck.pal.border or None)
        s.text(5.40, 3.15, 4.0, 1.0,
               "No band breakdown for this market. The total is the market's own fleet table.",
               9, deck.pal.muted)

    s.panel([
        fleet.source_sentence(),
        "The fleet is the denominator under spend per vehicle, genuine parts share and service cover, "
        "so the source matters as much as the number.",
        "Question: does the distributor agree with this base for targets and for parts share?",
    ])
    return [s]


# ------------------------------------------------------------------ genuine parts share

def render_gps(deck: Deck, ctx: BuildContext) -> list:
    info = ctx.get("gps")
    if info is None:
        raise BprError("E401", f"No target-spend data for {ctx.dist.display}.", db=ctx.dist.key)

    s = deck.add("Genuine parts share",
                 "Parts billed against the modelled spend of the fleet",
                 f"{ctx.dist.display}  |  {info['period_basis'] or 'latest year available'}  |  "
                 "warranty parts included",
                 f"Source: {info['source']}; modelled target spend, not measured competitor spend.")

    s.tile(0.40, 1.85, 2.93, 1.45, "PARTS BILLED", eur_compact(info["billed_eur"]),
           f"what ISZE billed {ctx.dist.display}", deck.pal.ink, 22)
    s.tile(3.53, 1.85, 2.93, 1.45, "MODELLED SPEND", eur_compact(info["target_eur"]),
           "what the fleet should generate", deck.pal.muted, 22)
    colour = deck.pal.green if (info["capture"] or 0) >= 0.6 else deck.pal.amber
    s.tile(6.67, 1.85, 2.93, 1.45, "SHARE", pct(info["capture"]),
           "parts billed divided by modelled spend", colour, 22)

    history = None
    try:
        from ..inputs import gps as gps_mod
        history = gps_mod.gps_series(ctx.gps_code)
    except BprError:
        history = None
    if history is not None and len(history) > 1:
        cd = CategoryChartData()
        cd.categories = [str(int(y)) for y in history.year]
        cd.add_series("Share of modelled spend", s.chart_values([None if pd.isna(c) else float(c) for c in history.capture]))
        ch = s.chart(XL_CHART_TYPE.LINE_MARKERS, cd, 0.40, 3.60, 9.20, 2.30)
        s.style_chart(ch, '0%', legend=False)
        s.axis_percent(ch)
        s.line_fmt(ch.plots[0].series[0], deck.pal.accent, 2.25, True, False)

    panel = [
        f"{ctx.dist.display} billed {eur_compact(info['billed_eur'])} against a modelled "
        f"{eur_compact(info['target_eur'])}, a share of {pct(info['capture'])}.",
        "Modelled spend means what the fleet should generate. It is not measured competitor spend.",
    ]
    if info.get("warranty_eur"):
        panel.append(f"Warranty parts are {eur_compact(info['warranty_eur'])} of the billing and are "
                     "included in the share shown. They are a claim, not a dealer sale.")
    if info.get("coverage_note"):
        panel.append(str(info["coverage_note"])[:220])
    panel.append("Question: which families explain the remaining gap, and where should support land first?")
    s.panel(panel)
    return [s]


# ------------------------------------------------------------------ service-demand cover

def render_pms(deck: Deck, ctx: BuildContext) -> list:
    cover = ctx.get("pms")
    if cover is None or cover.empty:
        raise BprError("E401", f"No service-demand cover for {ctx.dist.display}.", db=ctx.dist.key)

    year = int(cover.year.max()) if "year" in cover.columns else None
    view = cover[cover.year == year] if year else cover
    view = view.sort_values("capture_rate")

    s = deck.add("Service-demand cover",
                 "What we billed against what the fleet should need, by service family",
                 f"{ctx.dist.display}  |  {'fiscal year ' + str(year) if year else ctx.period.label}  |  "
                 "denominator is expected replacement units, not full target spend",
                 "Source: ISZE billing to "
                 f"{ctx.dist.display}, credit notes excluded; ISZE service-demand model; "
                 "total billing, Genuine and value parts together.")

    rows = []
    for _, row in view.iterrows():
        label = row.get("category_label") or row.get("pms_category") or ""
        rows.append((str(label).replace("_", " ").title(),
                     qty(row.get("expected_qty")), qty(row.get("actual_qty")),
                     pct(row.get("capture_rate")),
                     eur_compact(row.get("revenue_gap_eur")) if pd.notna(row.get("revenue_gap_eur")) else "n/a"))
    s.table(0.40, 1.85, [2.30, 1.90, 1.80, 1.30, 1.90],
            ["Service family", "Expected units", "Units billed", "Cover", "Euro gap"], rows)

    lowest = view.head(3)
    names = ", ".join(str(r.get("category_label") or r.get("pms_category")).replace("_", " ")
                      for _, r in lowest.iterrows())
    panel = [
        f"Cover is what we billed divided by what the fleet should need. The lowest three families are {names}.",
        "Cover is units against a service-demand model, so it is not the same measure as genuine parts "
        "share, which is euros against a spend target.",
        "A low reading that is steady over years is a lasting gap and room to grow. A low reading in one "
        "year only is usually stock timing.",
        "Question: which of these families has demand we never see, and which is bought elsewhere?",
    ]
    s.panel(panel)
    return [s]


# ------------------------------------------------------------------ mix

def render_mix(deck: Deck, ctx: BuildContext) -> list:
    data = ctx.get("mix")
    if data is None or data.empty:
        raise BprError("E401", f"No genuine and value-parts mix for {ctx.dist.display}.", db=ctx.dist.key)

    by_year = data.groupby("year")[["genuine_eur", "bvp_eur"]].sum().reset_index()
    by_year = by_year.sort_values("year")

    s = deck.add("Genuine and value parts",
                 "What we billed, split between Genuine parts and Best Value Parts",
                 f"{ctx.dist.display}  |  the covered product families only  |  EUR",
                 f"Source: {ctx.get('mix_source') or 'mix_genuine_bvp_by_family.csv'}, "
                 "Genuine and value parts by family and year.")

    cd = CategoryChartData()
    cd.categories = [str(int(y)) for y in by_year.year]
    cd.add_series("Genuine", s.chart_values([float(v) for v in by_year.genuine_eur]))
    cd.add_series("Best Value Parts", s.chart_values([float(v) for v in by_year.bvp_eur]))
    ch = s.chart(XL_CHART_TYPE.COLUMN_STACKED, cd, 0.40, 1.80, 4.40, 4.20)
    s.style_chart(ch, '#,##0')
    for series_obj, colour in zip(ch.plots[0].series, [deck.pal.accent, deck.pal.grey]):
        s.bar_fill(series_obj, colour)

    rows = []
    for _, row in data.sort_values(["product_family", "year"]).iterrows():
        rows.append((str(row.product_family), str(int(row.year)),
                     eur_compact(row.get("total_eur")), pct(row.get("bvp_share_eur"))))
        if len(rows) >= 12:
            break
    s.table(5.00, 1.85, [1.75, 0.70, 1.20, 1.55],
            ["Family", "Year", "Billed", "Value share"], rows, row_h=0.34)

    total_now = float(by_year.iloc[-1][["genuine_eur", "bvp_eur"]].sum())
    bvp_now = float(by_year.iloc[-1]["bvp_eur"])
    share_now = bvp_now / total_now if total_now else 0
    share_first = None
    if len(by_year) > 1:
        t0 = float(by_year.iloc[0][["genuine_eur", "bvp_eur"]].sum())
        share_first = float(by_year.iloc[0]["bvp_eur"]) / t0 if t0 else None

    panel = [
        f"Value parts were {pct(share_now)} of combined billing in {int(by_year.iloc[-1].year)}"
        + (f", against {pct(share_first)} in {int(by_year.iloc[0].year)}." if share_first else "."),
        "A move in the mix is not on its own a loss: the question is whether the whole basket grew "
        "or whether value parts replaced genuine ones.",
        "Question: where is a value part supporting genuine share, and where is the whole basket lost?",
    ]
    s.panel(panel)
    return [s]
