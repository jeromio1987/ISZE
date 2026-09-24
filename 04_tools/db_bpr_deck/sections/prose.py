"""Programmes, priorities and actions.

These slides carry no data. They carry the two or three things the person running the tool
wants said, which is why the wizard collects them as free text and writes them into the
answers file. If nothing was typed, the slides are built from what the data did show, so the
deck never has an empty page.
"""
from __future__ import annotations

from ..context import BuildContext
from ..periods import pct
from ..theme import Deck, Slide


def _prose(ctx: BuildContext, key: str) -> list[str]:
    value = (ctx.prose or {}).get(key) or []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(v).strip() for v in value if str(v).strip()]


# ------------------------------------------------------------------ 1. programmes


def _programme_slide(deck: Deck, ctx: BuildContext) -> Slide | None:
    programmes = _prose(ctx, "programmes")
    extra = _prose(ctx, "programme_questions")
    if not programmes and not extra:
        return None
    s = deck.add("Programmes",
                 f"What is running with {ctx.dist.display} and where it stands",
                 "Contracts, supply programmes and open items",
                 "Source: as stated to this review; no figure on this page is derived from the data files.")
    items = programmes[:4] or ["Nothing was recorded for this review."]
    y = 1.85
    h = min(1.15, (5.90 - y) / max(len(items), 1))
    for i, line in enumerate(items):
        s.rect(0.40, y, 9.20, h, deck.pal.row2 if i % 2 == 0 else deck.pal.panel,
               deck.pal.border or None)
        s.rect(0.40, y, 0.08, h, deck.pal.accent if i == 0 else deck.pal.amber)
        s.text(0.70, y + 0.12, 8.60, h - 0.2, line, 10, deck.pal.ink)
        y += h + 0.10
    s.panel(extra or [
        "Status of each programme as recorded, without terms or commercial conditions.",
        "Question: what has changed since the last review, and what do we need from each other?",
    ])
    return s


# ------------------------------------------------------------------ 2. priorities


def render_priorities(deck: Deck, ctx: BuildContext) -> list:
    priorities = []
    for raw in _prose(ctx, "priorities"):
        parts = [p.strip() for p in raw.split("|")]
        title = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        big = parts[2] if len(parts) > 2 else ""
        priorities.append((title.upper(), big, body))
    if not priorities:
        priorities = _fallback_priorities(ctx)

    s = deck.add("Discussion priorities",
                 f"What this review should decide with {ctx.dist.display}",
                 "Read the movements net of stock before changing any terms",
                 "Sources: ISZE billing, their sales-to-dealer reporting, the KPI Master File and the "
                 "service-demand files, as available for this distributor.")
    colours = [deck.pal.accent, deck.pal.amber, deck.pal.green]
    cw = 2.93
    for k, (heading, big, body) in enumerate(priorities[:3]):
        x = 0.40 + k * (cw + 0.20)
        s.rect(x, 1.85, cw, 4.10, deck.pal.panel, deck.pal.border or None)
        s.rect(x, 1.85, cw, 0.10, colours[k % len(colours)])
        s.text(x + 0.20, 2.12, cw - 0.40, 0.60, f"{k + 1}  {heading}", 9.5, deck.pal.ink, True)
        if big:
            s.text(x + 0.20, 2.80, cw - 0.40, 0.55, big, 14, colours[k % len(colours)], True)
        s.text(x + 0.20, 3.45, cw - 0.40, 2.30, body, 9, deck.pal.muted)
    s.panel([
        "Agree the explanation before the action. A price move should follow evidence of a price "
        "problem, not simply a low cover reading.",
        "Use their sales-to-dealer reporting to locate the pattern; our billing alone measures "
        "stocking decisions as much as demand.",
        "Set the next review around a short list of families and part numbers, with availability "
        "shown beside the commercial result.",
        "Question: which of these does the distributor own, and which needs ISZE?",
    ])
    return [s]


# ------------------------------------------------------------------ 3. actions


def render_actions(deck: Deck, ctx: BuildContext) -> list:
    actions = []
    for raw in _prose(ctx, "actions"):
        parts = [p.strip() for p in raw.split("|")]
        while len(parts) < 3:
            parts.append("")
        actions.append((parts[0], parts[1], parts[2]))
    if not actions:
        actions = [
            ("Data feed", "Keep the monthly part-number file coming, and add a monthly stock snapshot "
                          "if one can be produced.", ctx.dist.display),
            ("Availability", "Identify the part numbers behind the fill-rate gap and separate stock-mix "
                             "misses from supply.", f"{ctx.dist.display} + ISZE"),
            ("Fleet base", "Agree which vehicle count both sides use for targets and for parts share.",
             "Joint"),
            ("Next review", "Recheck the same measures on the next monthly cycle.", "Joint"),
        ]

    s = deck.add("Action points",
                 "What both sides leave this review agreeing to do",
                 "Proposed discussion output, built from the evidence in this review",
                 "Proposed action structure based on the files listed on the preceding slides.")
    s.table(0.40, 1.85, [1.90, 5.60, 1.70], ["Topic", "Action", "Owner"], actions,
            row_h=0.50, bold_cols=(0,))
    s.panel([
        "Each measure should leave with an explanation and an owner, not only a red or green result.",
        "Keep the three sales stages separate: what we billed, what they sold to dealers, and what "
        "dealers sold on.",
        "Read the family figures together with stock movement: a fall in purchases can be stock "
        "being used up.",
        "The first sign of success is whether the weak families recover while availability improves "
        "without rebuilding unnecessary stock.",
    ])
    return [s]


# ------------------------------------------------------------------ what the block draws


def render_prose(deck: Deck, ctx: BuildContext) -> list:
    """The programmes page (when there is something to say), then priorities and actions."""
    slides = []
    first = _programme_slide(deck, ctx)
    if first is not None:
        slides.append(first)
    slides.extend(render_priorities(deck, ctx))
    slides.extend(render_actions(deck, ctx))
    return slides


def _fallback_priorities(ctx: BuildContext) -> list[tuple[str, str, str]]:
    """When nothing was typed, say what the numbers themselves say. Still not invented data."""
    out: list[tuple[str, str, str]] = []
    fill = ctx.kpi_window("fill_rate")
    if not fill.empty and float(fill.iloc[-1]) < 0.95:
        out.append(("CLOSE THE AVAILABILITY GAP",
                    f"Fill rate {pct(fill.iloc[-1])}",
                    "Availability is below the 95% target while dealer demand in the network is holding. "
                    "Discuss the stock mix and the replenishment cadence, not only total stock."))
    try:
        cover = ctx.get("pms")
        if cover is not None and not cover.empty:
            year = int(cover.year.max())
            lowest = cover[cover.year == year].sort_values("capture_rate").head(2)
            names = ", ".join(str(r.get("category_label") or r.get("pms_category")).replace("_", " ")
                              for _, r in lowest.iterrows())
            out.append(("DEVELOP THE LOWEST-COVER FAMILIES",
                        names,
                        "These families sit far below expected service demand. That is room to grow, "
                        "and it needs the eligible fleet, dealer breadth and price position tested "
                        "before any terms change."))
    except Exception:
        pass
    try:
        if ctx.get("sellout") is not None:
            out.append(("READ PURCHASES AGAINST DEALER SALES",
                        "stock, not billing",
                        "The comparison of what we billed against what they sold to dealers separates "
                        "stock movement from a real change in demand."))
    except Exception:
        pass
    if not out:
        out.append(("AGREE THE NEXT STEPS",
                    "this review",
                    "Not enough shared data is available for this distributor to rank the priorities "
                    "from the numbers. Use this page to record what both sides agreed."))
    return out[:3]
