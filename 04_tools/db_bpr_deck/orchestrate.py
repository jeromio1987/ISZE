"""Assemble one deck from the chosen blocks.

Cover, agenda and a method page are always included. Every other page is a block, and a block
that cannot be filled becomes an amber "data unavailable" page rather than a missing one or a
crash, so the reader always knows a slide was meant to be there.

The agenda is written last, once the page numbers are known.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pptx.util import Inches, Pt

from . import blocks as block_defs
from .context import BuildContext
from .errors import BprError, BprWarn
from .paths import ISZE_ROOT, logo_for, output_dir, rel
from .sections import MODULES
from .theme import Deck, Slide, get as get_palette


@dataclass
class DeckResult:
    path: Path | None = None
    slides: int = 0
    written: list[dict] = field(default_factory=list)      # block key, label, first page
    unavailable: list[dict] = field(default_factory=list)  # block key, label, reason
    notes: list[BprWarn] = field(default_factory=list)


def _filename(ctx: BuildContext) -> str:
    stem = ctx.dist.key.replace(" ", "_")
    return (f"ISZE_{stem}_Business_Performance_Review_"
            f"{ctx.period.label.replace(' ', '_')}_{date.today():%Y-%m-%d}.pptx")


def build(ctx: BuildContext, selected: list[str], *, output: Path | None = None) -> DeckResult:
    palette = get_palette(ctx.theme)
    chosen = block_defs.order_for(selected)

    deck = Deck(
        pal=palette,
        db_display=ctx.dist.display,
        period_label=ctx.period.label,
        footer_note="",
    )
    result = DeckResult()

    # ---------------------------------------------------------------- cover
    title_lines = [ctx.dist.display, "Business Performance Review"]
    subtitle = (f"{ctx.period.label}  ·  plan, sales to dealer, availability, "
                "fleet and service families")
    note = f"Built {date.today():%d %B %Y} from the ISZE data files; every figure carries its source"
    deck.cover(title_lines, subtitle, note, logo=logo_for(palette.logo))

    # ---------------------------------------------------------------- agenda placeholder
    agenda = deck.add("Agenda", "Review structure",
                      f"{ctx.dist.display}, {ctx.period.label}", " ")

    # ---------------------------------------------------------------- method
    _method_page(deck, ctx, chosen)

    # ---------------------------------------------------------------- the blocks
    for key in chosen:
        ok, reason = ctx.check(key)
        label = block_defs.BLOCK_LABEL.get(key, key)
        if not ok:
            _unavailable_page(deck, ctx, label, reason)
            result.unavailable.append({"key": key, "label": label, "reason": reason})
            continue
        try:
            made = MODULES[key](deck, ctx)
        except BprError as exc:
            _unavailable_page(deck, ctx, label, exc.message)
            result.unavailable.append({"key": key, "label": label, "reason": exc.message})
            continue
        except Exception as exc:                              # noqa: BLE001
            message = f"{type(exc).__name__}: {exc}"
            ctx.warnings.append(BprWarn(f"{label} failed: {message}"))
            _unavailable_page(deck, ctx, label, "This page could not be built from the files on disk.")
            result.unavailable.append({"key": key, "label": label, "reason": message})
            continue
        first = deck.slide_count() - len(made) + 1
        result.written.append({"key": key, "label": label, "page": first})

    # ---------------------------------------------------------------- fill the agenda in
    _fill_agenda(agenda, deck, ctx, result)

    # ---------------------------------------------------------------- provenance page
    _provenance_page(deck, ctx, result)

    # ---------------------------------------------------------------- save
    if output is not None:
        target = Path(output)
    else:
        folder = ctx.output_dir or output_dir(ctx.dist.key, ctx.period.label.replace(" ", "_"))
        target = Path(folder) / _filename(ctx)
    deck.save(target)
    result.path = target
    result.slides = deck.slide_count()
    result.notes = list(ctx.warnings)
    return result


# ------------------------------------------------------------------ standing pages

def _method_page(deck: Deck, ctx: BuildContext, chosen: list[str]) -> None:
    s = deck.add("Method",
                 "What is on these pages, and what is not",
                 "How the three sales stages are kept apart",
                 "Sources: the files named on each page; nothing on this page is a derived figure.")
    left = [
        ("WHAT WE MEAN BY EACH STAGE", [
            "ISZE billing: what we invoiced the distributor. Includes a stock decision on their side.",
            "Sales to dealer: what the distributor reports selling to their dealer network, in their own file.",
            "The two are different stages at different prices. Their euro levels are not comparable.",
        ]),
        ("WHICH PERIOD", [
            f"This deck covers {ctx.period.label}"
            + (f", through {ctx.period.through}." if ctx.period.is_partial else ".")
            + " The fiscal year starts in April.",
            "Where a source is kept on a calendar year, the page says so and does not mix the two.",
        ]),
        ("WHAT WE DID NOT ASSUME", [
            "No dealer prices and no distributor margins: parts comparisons are in units.",
            "Modelled spend and service demand are models of what the fleet should need, not measured sales.",
            "A figure we cannot stand behind is shown as unavailable with the reason, never as a guess.",
        ]),
    ]
    cw = (9.20 - 2 * 0.20) / 3
    for k, (heading, points) in enumerate(left):
        x = 0.40 + k * (cw + 0.20)
        s.rect(x, 1.85, cw, 4.10, deck.pal.panel, deck.pal.border or None)
        s.text(x + 0.20, 2.02, cw - 0.40, 0.25, heading, 8, deck.pal.accent, True)
        s.text(x + 0.20, 2.40, cw - 0.40, 3.40, [f"-  {p}" for p in points], 9, deck.pal.ink, spacing=8)
    s.panel([
        f"This deck was generated for {ctx.dist.display} from the workspace data files on "
        f"{date.today():%d %B %Y}.",
        "Pages that could not be filled are shown with the reason rather than left out silently.",
        "Every page names its source in the footer, so any figure can be traced back.",
        "Question: which fleet base and which target should both sides use next time?",
    ])


def _unavailable_page(deck: Deck, ctx: BuildContext, label: str, reason: str) -> None:
    s = deck.add("Not available", label,
                 f"{ctx.dist.display}  |  {ctx.period.label}",
                 "No source file for this page; see the reason below.")
    s.banner(f"{reason}\n\nNothing is shown here rather than a figure we cannot stand behind. "
             f"This page is listed so the review can decide whether to collect the input.",
             y=2.10, h=1.60)


def _fill_agenda(agenda: Slide, deck: Deck, ctx: BuildContext, result: DeckResult) -> None:
    lines = []
    for item in result.written:
        lines.append((item["page"], item["label"]))
    for item in result.unavailable:
        lines.append((None, f"{item['label']}  (not available)"))

    y = 1.95
    step = 0.42 if len(lines) > 8 else 0.52
    if len(lines) > 13:
        step = 0.32
    for i, (page, label) in enumerate(lines):
        agenda.rect(0.40, y, 9.20, step - 0.06,
                    deck.pal.row2 if i % 2 == 0 else deck.pal.panel)
        agenda.text(0.65, y, 0.60, step - 0.06, f"{i + 1}", 12,
                    deck.pal.accent if page else deck.pal.muted, True, anchor=1)
        agenda.text(1.30, y, 6.90, step - 0.06, label, 10.5,
                    deck.pal.ink if page else deck.pal.muted, False, anchor=1)
        if page:
            agenda.text(8.10, y, 1.40, step - 0.06, f"page {page}", 9,
                        deck.pal.muted, False, align=2, anchor=1)
        y += step

    agenda.panel([
        f"{len(result.written)} pages built, {len(result.unavailable)} not available.",
        "We work in fiscal years, April to March, unless a page says calendar year.",
        "Sales-to-dealer figures are the distributor's own reporting, not our billing.",
        "Each page ends with our observations and the questions we want answered.",
    ])


def _provenance_page(deck: Deck, ctx: BuildContext, result: DeckResult) -> None:
    s = deck.add("Appendix", "Where every page's numbers come from",
                 "One line per page, so any figure can be traced",
                 "Built from the workspace data files; no figure on this page is derived.")
    rows = []
    for item in result.written:
        rows.append(("page " + str(item["page"]), item["label"], _source_for(item["key"], ctx)))
    s.table(0.40, 1.85, [0.85, 3.05, 5.30], ["Page", "Slide", "Where the numbers come from"], rows,
            row_h=0.34, bold_cols=(0,))

    if result.unavailable:
        y = 1.85 + 0.36 + 0.34 * len(rows) + 0.25
        if y < 6.4:
            s.text(0.40, y, 9.20, 0.3, "NOT BUILT", 8, deck.pal.amber, True)
            yy = y + 0.30
            for item in result.unavailable[:3]:
                s.text(0.40, yy, 9.20, 0.28, f"{item['label']}: {item['reason']}", 8.5, deck.pal.muted)
                yy += 0.28

    s.panel([
        "Every page names its source, including the period and whether the figure is measured or modelled.",
        "The deck is regenerated from files rather than copied forward, so it cannot drift from the dashboards.",
        "Questions on any figure: the source line and this appendix are the whole trail.",
    ])


def _source_for(key: str, ctx: BuildContext) -> str:
    return {
        "exec": "ISZE billing, KPI Master File, FY plan workbook, target-spend and fleet files",
        "plan": "FY2027 BP workbook, matched by SAP sold-to code",
        "s2d": "KPI Master File, Parts Sales DB to DLR in EUR",
        "avail": "KPI Master File, First Fill Rate / Days of Parts in Stock / Back Order Lines",
        "s2d_units": f"{ctx.dist.display} sales-to-dealer file, as sent; ISZE parts catalogue",
        "stock": f"ISZE billing to {ctx.dist.display} against their sales-to-dealer file, by service family",
        "fleet": "vehicle count file for this market (see the page for which source)",
        "gps": "gps_spu_by_distributor.csv and wallet_waterfall.csv, modelled target spend",
        "pms": "pms_capture_by_db_year.csv, expected replacement units by service family",
        "mix": "mix_genuine_bvp_by_family.csv, Genuine against Best Value Parts",
        "prose": "as recorded in this review; not derived from the data files",
    }.get(key, "see the page source line")


def rel_output(path: Path | None) -> str:
    return rel(path) if path else ""
