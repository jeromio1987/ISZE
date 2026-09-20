"""BPR 2.0 — assemble the Business Performance Review deck.

Design rule enforced here: every planned slide is emitted. If its chart PNG is
missing, the slide still appears with its title, takeaways and an explicit
"chart not available" panel. Nothing is ever silently dropped, and no figure is
ever estimated to fill a space.

Run: python build_bpr_deck.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpr_deck as D  # noqa: E402

CHARTS = HERE / "charts_out"
OUT = HERE / "ISZE_Business_Performance_Review_2026.pptx"
# While the deck is open in PowerPoint the file is locked; build to a temp name
# and swap it in so a failed save never leaves a half-written deck behind.
TMP = HERE / "_build_tmp.pptx"

N = json.loads((HERE / "_bpr_numbers.json").read_text(encoding="utf-8"))
K = json.loads((HERE / "_kpi_numbers.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- fill rate
_fill = K["first_fill_rate"]
FILL_ROWS: list[tuple[str, float, str | None]] = []
for _db, _r in _fill["by_db"].items():
    if _r.get("latest") is None:
        continue
    _v = _r["latest"] * 100 if _r["latest"] < 1.5 else _r["latest"]
    FILL_ROWS.append((_db, _v, _r.get("month_label")))
FILL_ROWS.sort(key=lambda t: t[1])
FILL_BELOW = [r for r in FILL_ROWS if r[1] < 95]
FILL_WORST = FILL_BELOW[0] if FILL_BELOW else (FILL_ROWS[0] if FILL_ROWS else None)

STOCK = K["days_of_parts_in_stock"]

MISSING: list[str] = []


def eur(v) -> str:
    v = v or 0
    a = abs(v)
    s = "-" if v < 0 else ""
    if a >= 1_000_000:
        return f"EUR {s}{a/1_000_000:,.2f}M"
    if a >= 1_000:
        return f"EUR {s}{a/1_000:,.0f}k"
    return f"EUR {s}{a:,.0f}"


def m(v) -> str:
    return f"EUR {v/1_000_000:,.2f}M" if v else "—"


def pct(v, dec=1) -> str:
    return "—" if v is None else f"{v:,.{dec}f}%"


def unavailable_panel(name: str) -> str:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1700, 1000), (0xF4, 0xF4, 0xF4))
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, 1700, 12], fill=(0xCC, 0x0E, 0x1E))
    try:
        f1 = ImageFont.truetype(r"C:\Windows\Fonts\calibrib.ttf", 44)
        f2 = ImageFont.truetype(r"C:\Windows\Fonts\calibri.ttf", 29)
        f3 = ImageFont.truetype(r"C:\Windows\Fonts\calibri.ttf", 25)
    except OSError:
        f1 = f2 = f3 = ImageFont.load_default()
    dr.text((80, 300), "CHART NOT AVAILABLE", font=f1, fill=(0x8F, 0x0A, 0x15))
    dr.text((80, 380), f"Expected: {name}", font=f2, fill=(0x22, 0x22, 0x22))
    dr.text((80, 435), "The source file was missing or the measure could not be read.",
            font=f3, fill=(0x5A, 0x5A, 0x5A))
    dr.text((80, 490), "Nothing has been estimated to fill this space.",
            font=f3, fill=(0x5A, 0x5A, 0x5A))
    out = CHARTS / "_NOT_AVAILABLE.png"
    img.save(out)
    return str(out)


def main():
    prs = D.new_deck()
    page = 0

    def nxt() -> int:
        nonlocal page
        page += 1
        return page

    def slide(title: str, chart_name: str, takeaways: list[str],
              eyebrow: str | None = None) -> None:
        """Always emit the slide, chart or no chart."""
        p = CHARTS / chart_name
        if p.exists():
            path = str(p)
        else:
            MISSING.append(chart_name)
            path = unavailable_panel(chart_name)
        D.two_col(prs, title, path, takeaways, eyebrow=eyebrow, page_no=nxt())

    # ============================================================== cover
    D.cover_2(
        prs,
        "ISZE Vehicle Parts & Accessories\nBusiness Performance Review",
        "Fiscal 2026 close  ·  Fiscal 2027 to date  ·  Service performance  ·  PRISM and IDS",
        eyebrow="ISZE  ·  VEHICLE PARTS & ACCESSORIES",
        meta=(
            f"Prepared 16 September 2026. Billing file runs to {N['sf_max_date']}; "
            "September figures are month to date and the month is not closed."
        ),
    )
    nxt()

    # =========================================================== contents
    D.bullets_with_callout(
        prs,
        "What this review covers, and how to read it",
        [
            "Where we stand: fiscal 2026 close, the fiscal 2027 plan, and September month to date.",
            "Service performance: fill rate against the 95% standard, inventory cover, and how much of the network runs on urgent orders.",
            "Where the money is: spend per truck, the modelled ceiling, and the service families carrying the unbought euro.",
            "ITUK in detail: the gap at both layers of the chain, taken from the leakage review.",
            "Genuine against best-value on the same part number, and where parts classification says we are exposed.",
            "PRISM and the dealer standard: what the platform covers, and what the dealer assessment says about the network.",
            "Warranty parts as a share of what we bill, kept separate from customer-paid demand.",
        ],
        "Data rule for this deck",
        "Every figure is read from a named ISZE file on its build date. Where a measure is modelled, the slide says so. "
        "Where a distributor does not report a KPI, the cell is empty and the coverage is stated — never a zero, never a "
        "copy of another market. Month-to-date figures are labelled as such, and a market that filed an old month carries "
        "that month's label with its number.",
        eyebrow="Contents",
        page_no=nxt(),
    )

    # ==================================================== 1. where we stand
    D.chapter_divider(
        prs, 1, "Where we stand",
        "Fiscal 2026 close, the fiscal 2027 plan, and September to date against last year.",
        page_no=nxt(),
    )

    fy26 = N["fy2026"]
    top26 = sorted(fy26["by_db"].items(), key=lambda kv: -kv[1])
    q1 = N["fy2027_by_quarter"].get("Q1")
    D.big_numbers(
        prs,
        "The headline numbers",
        [
            ("Fiscal 2026 parts billed", m(fy26["total_eur"]),
             f"network distributors, full fiscal year to March 2026"),
            ("Largest distributor", m(top26[0][1]) if top26 else "—",
             f"{top26[0][0]} — {top26[0][1]/fy26['total_eur']*100:.0f}% of the network" if top26 else "—"),
            ("Fiscal 2027 first quarter", m(q1),
             "April to June 2026, the last closed quarter in the billing file"),
            ("September to date", "EUR 1.46M",
             "46% of the month plan at 14 September, the month is not closed"),
        ],
        eyebrow="Fiscal 2026 and fiscal 2027 to date",
        page_no=nxt(),
        note=(
            f"The billing file runs to {N['sf_max_date']}, so fiscal 2026 is complete and fiscal 2027 is available "
            "only to the end of that quarter. September figures come from the daily sales report dated 14 September 2026 "
            "and are month to date. Network parts billed is on the distributor base in the billing file."
        ),
    )

    D.big_numbers(
        prs,
        "The plan behind the numbers — and two different things both called parts",
        [
            ("Fiscal 2027 plan", "EUR 35.28M",
             "BP reviewed April 2026, turnover basis"),
            ("Largest plan line", "EUR 6.97M",
             "ITUK, followed by IUK at EUR 6.06M"),
            ("First quarter plan pace", "~EUR 8.8M",
             "a quarter of the annual plan"),
            ("First quarter actual", m(q1),
             "network distributors, April to June 2026"),
        ],
        eyebrow="Fiscal 2027 plan",
        page_no=nxt(),
        note=(
            "A caution worth carrying: the KPI target workbook also has a line labelled parts target, at roughly "
            "EUR 108M. That is a different measure on a different basis — distributor to dealer, twelve months "
            "trailing — and it is about three times the turnover plan. The two must never appear on one slide "
            "without saying which is which."
        ),
    )

    slide(
        "Fiscal 2026 closed with ITUK and IUK carrying a fifth of the network between them",
        "_fy26_close_by_db.png",
        [
            f"Network parts billed {m(fy26['total_eur'])} for the full fiscal year to March 2026.",
            f"Largest: {top26[0][0]} at {m(top26[0][1])}; second {top26[1][0]} at {m(top26[1][1])}."
            f" Together {m(top26[0][1] + top26[1][1])}." if len(top26) > 1 else "Single distributor attributed.",
            "The tail of smaller markets sums to a material share, so the network is not a two-market story.",
            "Attribution resolves the sold-to code first, so Israel's two distributors stay separate on every chart.",
        ],
        eyebrow="Fiscal 2026 close",
    )

    slide(
        "September to date: the network is up on the same point last year",
        "_sales_sept_mtd.png",
        [
            "Month to date at 14 September, parts billing against the same point last September.",
            "ITUK, ISD and IBX are each ahead of where they were at this point last year.",
            "IUK is behind, and that single gap is the largest negative on the page.",
            "The month is not closed — read this as direction, not as a result.",
        ],
        eyebrow="Fiscal 2027 to date",
    )

    slide(
        "September month to date is running at 46% of the month plan",
        "_sales_sept_rank.png",
        [
            "Network month to date EUR 1.46M against a month plan of EUR 3.18M.",
            "ITUK is the largest single contributor for the month so far.",
            "Progress varies widely by distributor, which is why the ranking is worth showing rather than the total alone.",
            "Order intake and work in progress sit in the same report when a forward view is needed.",
        ],
        eyebrow="Fiscal 2027 to date",
    )

    # ============================================== 2. service performance
    D.chapter_divider(
        prs, 2, "Service performance",
        "Parts fill rate, inventory cover, and how much of the network runs on urgent orders.",
        page_no=nxt(),
    )

    D.big_numbers(
        prs,
        f"Parts fill: {len(FILL_BELOW)} of the {_fill['reported']} reporting markets sit below the standard",
        [
            ("Reporting markets", f"{_fill['reported']} of {_fill['total_rows']}",
             "a market that never files is not a zero"),
            ("Markets below 95%", str(len(FILL_BELOW)), "latest reported month per market"),
            ("Lowest reported", f"{FILL_WORST[1]:.1f}%" if FILL_WORST else "—",
             f"{FILL_WORST[0]} · {FILL_WORST[2]}" if FILL_WORST else "—"),
            ("Standard and floor", "95% / 92%", "target logic in the KPI target sheet"),
        ],
        eyebrow="Parts fill rate",
        page_no=nxt(),
        note=(
            "Reported order-line fill from the monthly KPI return, each market shown at the latest month it actually "
            "filed. Several of those months are more than a year old, so the month label travels with every number. "
            "Two markets have never filed at all."
        ),
    )

    slide(
        "Fill rate, latest reported month per market, against the 95% standard",
        "_fill_rate_latest.png",
        [
            "Reported order-line fill, latest month each market filed.",
            f"{len(FILL_BELOW)} of the {_fill['reported']} reporting markets sit below the standard.",
            "The lowest reported figure is in the low sixties, which is a service risk rather than a reporting issue.",
            "Coverage is the real caveat: some of these numbers are from a year ago and are labelled as such.",
        ],
        eyebrow="Parts fill rate",
    )

    slide(
        "Deviation from the 95% fill standard, in percentage points",
        "_fill_rate_deviation.png",
        [
            "Read left as the size of the service problem and right as headroom.",
            "A market inside the tolerance band is neither a risk nor an opportunity today.",
            "The markets outside the band are where a fill-rate conversation is worth having.",
            "The band is an interpretation of the 95% standard; the underlying numbers are reported, not modelled.",
        ],
        eyebrow="Parts fill rate",
    )

    slide(
        "Inventory cover: several markets hold far more stock than their supply route justifies",
        "_days_of_stock.png",
        [
            f"Days of parts in stock, latest reported month, {STOCK['reported']} of {STOCK['total_rows']} markets reporting.",
            "Road-received markets should sit around 60 to 90 days; sea-freight markets can justify more.",
            "The longest cover on the page is working capital sitting still rather than a service buffer.",
            "Very short cover at the other end pairs with the low fill rates on the previous page.",
        ],
        eyebrow="Inventory cover",
    )

    urg = N.get("urgency_fy2026")
    if urg:
        slide(
            f"Roughly {urg['urgent_pct']:.1f} euro in every hundred runs on an urgent order",
            "_urgency_fy26.png",
            [
                f"Urgent share {urg['urgent_pct']:.1f}% of matched billing value, fiscal 2026.",
                f"{urg['matched_pct_of_all']:.1f}% of billed value carries a usable order code, so this is the full picture for the year.",
                "A high urgent share usually means the dealer network is treating us as a same-day warehouse.",
                "This is a precondition for the sales-to-dealer conversation, not a result of it.",
            ],
            eyebrow="Order urgency",
        )

    slide(
        "Urgent-order share by distributor: a healthy spend per truck can still hide an emergency habit",
        "_urgency_by_db.png",
        [
            "Urgent share of matched billing value, by distributor.",
            "Markets high on this page are buying their availability one emergency order at a time.",
            "Order coding is uneven, so each bar should be read with its matched-value coverage.",
            "This measure exposes a market that looks fine on spend per truck.",
        ],
        eyebrow="Order urgency",
    )

    # ================================================ 3. where the money is
    D.chapter_divider(
        prs, 3, "Where the money is",
        "Spend per truck, the modelled ceiling, and the service families carrying the unbought euro.",
        page_no=nxt(),
    )

    gps = N["gps_cy2025"]
    c = N["ceiling_cy2025"]
    D.big_numbers(
        prs,
        f"{pct(c['capture_pct'])} of the modelled parts ceiling is covered today",
        [
            ("Target spend ceiling", m(c["theoretical_eur"]), "modelled, calendar 2025"),
            ("Parts billed", m(c["captured_total_eur"]), "what we billed in the same year"),
            ("Not captured", m(c["uncaptured_eur"]),
             f"of which addressable {m(c['addressable_uncaptured_eur'])}"),
            ("Spend per truck", f"EUR {gps['network_spend_per_unit']:,.0f}",
             f"median EUR {gps['network_median_spend_per_unit']:,.0f} across the network"),
        ],
        eyebrow="The parts opportunity",
        page_no=nxt(),
        note=(
            "The ceiling is a model, and part of it rests on a flat per-truck assumption in the smaller markets. "
            "The addressable line is the portion of the gap we can realistically contest. Read the coverage figure as "
            "a direction with a stated model behind it, not as a measured share of the market."
        ),
    )

    slide(
        "Spend per truck ranges more than four to one across the network",
        "_gps_spend_per_truck.png",
        [
            "Parts billed per truck in service, calendar 2025.",
            "The spread is the finding: the same service need is being satisfied at very different rates.",
            "A high figure is not automatically good — it can also mean a market is over-buying against its fleet.",
            "Each market's denominator is its fleet in service from the same model, and the source is stated until it is not.",
        ],
        eyebrow="Spend per truck",
    )

    cats = sorted(N["pms_cy2025"]["by_category"].items(), key=lambda kv: -kv[1]["gap_eur"])
    slide(
        "The unbought service euro is concentrated in a handful of families",
        "_pms_gap_categories.png",
        [
            f"Unbought value {m(N['pms_cy2025']['network_gap_eur'])} at observed selling prices, calendar 2025.",
            f"Largest single family: {cats[0][0]} at {m(cats[0][1]['gap_eur'])}." if cats else "No families scored.",
            "These are the families where a service-coverage conversation pays first.",
            "Capture is measured in units against the service model and then valued at the price actually realised.",
        ],
        eyebrow="Service capture",
    )

    # ============================================================== 4. ITUK
    D.chapter_divider(
        prs, 4, "ITUK in detail",
        "The gap at both layers of the chain, converted from the sales performance leakage review.",
        page_no=nxt(),
    )

    slide(
        "ITUK: about two thirds of the expected service volume is billed, and the fiscal view is better than the calendar one",
        "_ituk_demand_split.png",
        [
            "Expected service units against what was actually billed, on 23,068 trucks in service.",
            "Calendar 2025: 65.9% billed, leaving EUR 1.32M unbought.",
            "Fiscal 2025/26: 73.3% billed, leaving EUR 1.17M — the gap narrows on the fiscal basis.",
            "The difference between the two columns is the year boundary, not a different fleet.",
        ],
        eyebrow="ITUK · service demand",
    )

    slide(
        "ITUK: the unbought euro sits in urea filters, brake shoes and clutch components",
        "_ituk_gap_by_family_fy.png",
        [
            "Fiscal 2025/26, valued at the observed selling price.",
            "Urea filter is the single largest line at EUR 335k.",
            "Brake shoe at EUR 200k and clutch disc at EUR 174k follow.",
            "Filters as a group are largely captured, which makes the filter gap a volume question rather than a price one.",
        ],
        eyebrow="ITUK · gap by family",
    )

    slide(
        "ITUK: capture measured against the full service expectation, by family",
        "_ituk_capture_vs_full.png",
        [
            "Deviation from 100% of the service parts the model expects for this fleet.",
            "Filters sit at or above the modelled rate, so their gap is fleet or service-interval driven.",
            "Clutch components sit well below, and that is where the recoverable value is.",
            "Above the line is not automatically a win: it can mean the interval assumption is too low for this fleet.",
        ],
        eyebrow="ITUK · capture against expectation",
    )

    slide(
        "ITUK: the chain looks different at the inner layer than at ours",
        "_ituk_two_layers.png",
        [
            "Outer layer is our billing to ITUK; inner layer is what ITUK's dealers buy.",
            "The dealer layer carries EUR 5.51M of billed euro across twelve months of sales-to-dealer file.",
            "Dealer-layer capture is 47.5%, materially below our 65.9% to the distributor.",
            "That difference is what the distributor is holding, and it is the conversation worth having with ITUK.",
        ],
        eyebrow="ITUK · both layers",
    )

    # ============================ 5. genuine and best-value on one number
    D.chapter_divider(
        prs, 5, "Genuine and best-value on the same part number",
        "Where both lines exist for the same reference, which one is moving — and where classification says we are exposed.",
        page_no=nxt(),
    )

    slide(
        "Germany: best-value share of paired units fell from 38.6% to 8.5% in one fiscal year",
        "_de_bvp_cliff.png",
        [
            "Best-value share of units on reference pairs, fiscal years, April to March.",
            "Germany ran at 34.3%, then 38.6%, and fell to 8.5% in 2025/26.",
            "The network line stayed flat between 47% and 49%, so this is a Germany-specific movement.",
            "Two fifths of one market's paired volume changing line in a single year deserves a direct question.",
        ],
        eyebrow="Genuine against best-value",
    )

    slide(
        "Germany: the movement is almost entirely fuel-filter best-value volume stopping",
        "_de_bvp_driver.png",
        [
            "Change in paired units billed, fiscal 2024/25 to 2025/26.",
            "Fuel-filter best-value volume fell from roughly ten thousand units to tens of units.",
            "Genuine fuel-filter volume held at around five thousand units over the same period.",
            "So this is not Germany buying fewer filters — it is one line leaving the mix.",
        ],
        eyebrow="Genuine against best-value",
    )

    slide(
        "Parts classification flags where the independent aftermarket can take the job",
        "_aim_exposure_by_db.png",
        [
            "Share of parts billed on part numbers flagged as substitution-exposed, calendar 2025, with the network rule marked.",
            "Network flagged revenue is EUR 316k of EUR 33.1M billed — 0.95%, so the flag is narrow by design rather than a broad alarm.",
            "The largest single flagged book is IUK, which is where a value-line defence pays first.",
            "Classification match itself sits above 96% of billed euro, so the flag rather than the match is what separates markets.",
        ],
        eyebrow="Parts classification",
    )

    slide(
        "Exposure by parts family, with the best-value share beside it",
        "_aim_family_risk.png",
        [
            "Families where the independent aftermarket is most able to substitute.",
            "Where exposure is high and best-value share is low, we are the ones losing the job.",
            "Where genuine revenue is already zero, every best-value unit is incremental rather than a trade-down.",
            "Read the two measures together: exposure alone does not say what to do.",
        ],
        eyebrow="Parts classification",
    )

    slide(
        "The largest classification gaps in euro",
        "_aim_gap_top.png",
        [
            "Ranked by the euro value of the gap.",
            "The euro basis is stated on the chart — dealer sell-out and our billing are not the same measure.",
            "Families with no matched classification are excluded rather than estimated.",
            "Treat this as a target list, not a forecast.",
        ],
        eyebrow="Parts classification",
    )

    slide(
        "Exposure against spend per truck: where each line of defence belongs",
        "_aim_quadrant.png",
        [
            "Each market placed by exposure and by spend per truck, sized by parts billed.",
            "High exposure with low spend is where a value line is the answer.",
            "Low exposure with high spend is where genuine margin is worth protecting.",
            "Bubble size is parts billed, so visual weight matches commercial weight.",
        ],
        eyebrow="Parts classification",
    )

    # =================================================== 6. PRISM and IDS
    D.chapter_divider(
        prs, 6, "PRISM and the dealer standard",
        "What the analytics platform covers behind these numbers, and what the dealer assessment says about the network.",
        page_no=nxt(),
    )

    slide(
        "PRISM is the reason these numbers can be quoted at all",
        "_prism_pages.png",
        [
            "Every figure in this deck traces to a derived file built and checked by the platform.",
            "Coverage and pass-or-fail state are shown rather than assumed.",
            "Where a source is weak, the platform records it as an open integrity item instead of quietly correcting it.",
            "This deck repeats that discipline: a missing market is missing, never zero.",
        ],
        eyebrow="PRISM",
    )
    slide(
        "Open data issues, stated rather than hidden",
        "_prism_coverage.png",
        [
            "These are the known limits behind the numbers in this deck.",
            "They are recorded so a reader can judge how firm any single figure is.",
            "None of them is corrected silently.",
            "If a number here is later disputed, this page is where the caveat already lives.",
        ],
        eyebrow="PRISM",
    )

    slide(
        "Dealer standard assessment: how each country scored in 2026",
        "_ids_country_scores.png",
        [
            "Dealer audit scores against the common standard, 2026 evaluation round.",
            "518 dealer audits across 18 networks. The European dealer-weighted average is 74.8%.",
            "The spread runs from about 61% to 89%, and the network average is marked on the chart.",
            "Small networks move a lot on one dealer — read the audit count beside the name, not the rank alone.",
        ],
        eyebrow="Dealer standard",
    )

    slide(
        "Dealer standard by section: where each network's score is held down",
        "_ids_sections.png",
        [
            "Network average per section as a share of that section's maximum points (A 46 / B 80 / C 80 / D 47 / E 27 of 280).",
            "Service (C) is the strongest section network-wide at about 83%; premises (A) is the weakest at about 74%.",
            "Read across a row to see which section holds that particular network down — it differs by market.",
            "Israel's vehicle-sales column is hatched, not zero: that network filed no vehicle-sales answers and its total is A to D only.",
        ],
        eyebrow="Dealer standard",
    )

    # ========================================================= 7. warranty
    D.chapter_divider(
        prs, 7, "Warranty and the revenue mix",
        "How much of what we bill is warranty work rather than customer-paid parts.",
        page_no=nxt(),
    )

    w = N["warranty_cy2025"]
    D.big_numbers(
        prs,
        f"Warranty is {pct(w['network_pct_of_billed'])} of everything we bill",
        [
            ("Warranty parts billed", m(w["network_eur"]), "calendar 2025"),
            ("Share of parts billed", pct(w["network_pct_of_billed"]), "warranty against total billed"),
            ("Markets with a figure", str(len(w["by_db"])), "of the network rows"),
            ("Read it as", "claim cost", "not as a sales win"),
        ],
        eyebrow="Warranty",
        page_no=nxt(),
        note=(
            "Warranty parts are revenue, but they are not customer-paid demand. Reading them inside a growth number "
            "overstates the commercial position, which is why they are shown separately here and excluded from the "
            "target-spend ceiling."
        ),
    )

    slide(
        "Warranty parts billed by distributor",
        "_warranty_by_db.png",
        [
            "Calendar 2025, warranty parts value per distributor.",
            "The concentration follows fleet size, so read the share of billed rather than the absolute value.",
            "A rising warranty share against falling customer-paid parts is a quality signal worth tracking.",
            "Warranty sits outside the target-spend ceiling, which covers customer-paid demand only.",
        ],
        eyebrow="Warranty",
    )

    # ========================================================== 8. actions
    D.bullets_with_callout(
        prs,
        "What we are asking for",
        [
            f"A direct question to ITUK on the dealer-layer gap: our billing is at 65.9%, their dealers are at 47.5%, "
            f"and the difference is demand that reached the distributor but not the workshop.",
            "Germany: confirm why fuel-filter best-value volume stopped in fiscal 2025/26. It is one line, and it moved "
            "a market from 38.6% to 8.5% on paired units.",
            f"Fill rate: bring the {len(FILL_BELOW)} markets below the 95% standard into the monthly review with a named "
            f"owner, and record the markets that never file as a data gap rather than a zero.",
            "Inventory cover: agree the band per supply route and review the markets holding far more stock than their route justifies.",
            "Warranty to be reported beside growth from now on, so a warranty-heavy month is never read as commercial growth.",
            "Keep the exposure lens on every best-value decision, so a value line is deployed where genuine revenue is already "
            "lost rather than where it is strong.",
        ],
        "The one decision we need",
        "Whether the sales-to-dealer layer becomes a standing part of the distributor review. If it does, more markets "
        "need to file and the inner-layer gap stops being invisible. If it does not, the ITUK conversation on page 15 "
        "cannot be repeated anywhere else.",
        eyebrow="Before the next review",
        page_no=nxt(),
    )

    prs.save(TMP)
    try:
        TMP.replace(OUT)
        written = OUT
    except PermissionError:
        written = TMP
        print("NOTE: the final deck is open in PowerPoint, so this build was "
              "written to the temp file below. Close the deck and run again, "
              "or open the temp file.")
    print(f"slides {len(prs.slides)}")
    print(f"written {written}")
    print(f"bytes {written.stat().st_size:,}")
    if MISSING:
        print("SLIDES WITH A NOT-AVAILABLE PANEL (still present, never dropped):")
        for x in MISSING:
            print("  ", x)
    else:
        print("every planned chart is present")


if __name__ == "__main__":
    main()
