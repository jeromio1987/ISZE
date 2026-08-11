"""Distributor Sales Review deck for one DB.

    python build_deck.py --db ISD

Reads _<db>_summary.json from build_parts_analysis.py and writes
ISZE_<DB>_Sales_Review_FY2027.pptx. Slides that a DB has no data for are
dropped rather than faked (IDS, incomplete Power BI cut). The target story uses
Sales-to-Dealer amounts; an unavailable FY2026 KPI base is clearly imputed.

The output is a meeting-ready DRAFT, not a finished deck: the decline slides
carry templated questions and the narrative bullets are computed, so read them
once and sharpen the wording for the specific relationship before sending.
Tone rules that must survive editing are in
..\\ppt_template_v2\\DB_SALES_REVIEW_BLUEPRINT.md section 3.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOOLS = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ppt_template_v2"
sys.path.insert(0, TOOLS)

import isze_chart_theme as ct          # noqa: E402
import isze_deck_builder as db         # noqa: E402
from pptx.util import Inches, Pt, Emu  # noqa: E402
from pptx.dml.color import RGBColor    # noqa: E402
from pptx.enum.text import PP_ALIGN    # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402

import common as C                      # noqa: E402

ct.FONT_FAMILY = "Calibri"

RED = RGBColor(0xCC, 0x0E, 0x1E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY_BG = RGBColor(0xEC, 0xEC, 0xEC)


# --------------------------------------------------------------- slide utils --
def styled_table(slide, rows, left, top, width, height, col_widths,
                 bold_last=True, size=12.5, left_cols=(0,)):
    left_cols = set(left_cols)
    tbl = slide.shapes.add_table(len(rows), len(rows[0]), left, top, width, height).table
    for c, w in enumerate(col_widths):
        tbl.columns[c].width = w
    for r in range(len(rows)):
        for c in range(len(rows[0])):
            cell = tbl.cell(r, c)
            cell.text = rows[r][c] if rows[r][c] else " "
            para = cell.text_frame.paragraphs[0]
            if not para.runs:
                para.add_run().text = ""
            run = para.runs[0]
            run.font.size, run.font.name = Pt(size), "Calibri"
            para.alignment = PP_ALIGN.LEFT if c in left_cols else PP_ALIGN.RIGHT
            cell.vertical_anchor = 3
            cell.margin_left = cell.margin_right = Inches(0.08)
            is_last = bold_last and r == len(rows) - 1
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = RED
                run.font.bold = True; run.font.color.rgb = WHITE
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = GRAY_BG if is_last else (WHITE if r % 2 else GRAY_BG)
                run.font.bold = is_last
                run.font.color.rgb = RED if is_last else BLACK
    return tbl


def card(slide, left, top, width, height, letter, header, lines):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    try:
        shp.adjustments[0] = 0.06
    except Exception:
        pass
    shp.fill.solid(); shp.fill.fore_color.rgb = GRAY_BG
    shp.line.fill.background(); shp.shadow.inherit = False

    oval = slide.shapes.add_shape(MSO_SHAPE.OVAL, left + Inches(0.22), top + Inches(0.22),
                                  Inches(0.5), Inches(0.5))
    oval.fill.solid(); oval.fill.fore_color.rgb = RED
    oval.line.fill.background(); oval.shadow.inherit = False
    tf = oval.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    para = tf.paragraphs[0]; para.alignment = PP_ALIGN.CENTER
    run = para.add_run(); run.text = letter
    run.font.size, run.font.bold = Pt(18), True
    run.font.color.rgb, run.font.name = WHITE, "Calibri"

    db.txt(slide, header, left + Inches(0.9), top + Inches(0.22), width - Inches(1.1),
           Inches(0.45), size=15, bold=True, color=BLACK)
    db.bullet_list(slide, lines, left + Inches(0.32), top + Inches(0.85),
                   width - Inches(0.6), height - Inches(1.0), size=12.5, line_spacing=1.15)


def diverging_bar(categories, values, filename, title=None, figsize=(10.2, 4.3)):
    import matplotlib.pyplot as plt
    import numpy as np
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor(ct.WHITE); ax.set_facecolor(ct.WHITE)
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.axhline(0, color=ct.GRAY_LIGHT, linewidth=1, zorder=2)
    ax.tick_params(axis="x", colors=ct.GRAY, labelsize=10.5, length=0)
    ax.tick_params(axis="y", colors=ct.GRAY, labelsize=10, length=0)
    ax.yaxis.grid(True, color=ct.GRAY_BG, linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    x = np.arange(len(categories))
    bars = ax.bar(x, values, color=[ct.RED if v < 0 else ct.CHARCOAL for v in values],
                  width=0.6, zorder=3)
    for b, v in zip(bars, values):
        ax.annotate(f"{v:+,.0f}", (b.get_x() + b.get_width() / 2, v),
                    xytext=(0, -4 if v < 0 else 4), textcoords="offset points",
                    ha="center", va="top" if v < 0 else "bottom",
                    fontsize=9.5, color=ct.CHARCOAL, fontweight="bold")
    # long category names collide past ~9 bars, so the caller caps the count and
    # the font steps down with it
    fs = 10.5 if len(categories) <= 7 else 9.0
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=fs, color=ct.CHARCOAL)
    lo, hi = min(values + [0]), max(values + [0])
    ax.set_ylim(lo * 1.35 if lo < 0 else -1, hi * 1.45 if hi > 0 else 1)
    if title:
        ax.set_title(title, fontsize=13, color=ct.CHARCOAL, loc="left", fontweight="bold", pad=12)
    fig.tight_layout(pad=0.6)
    fig.savefig(filename, dpi=200, facecolor=ct.WHITE)
    plt.close(fig)


def wrap_label(s, width=11):
    # attach a standalone slash to the word before it, otherwise "Hydraulic /
    # mechanical" wraps to "Hydraulic" + "/" and the last word is lost
    s = str(s).replace(" / ", "/ ")
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > 2:                      # never drop a word — fold the tail up
        lines = [lines[0], " ".join(lines[1:])]
    return "\n".join(lines)


def eur(v, k=False):
    if v is None:
        return "—"
    return f"EUR {v/1000:,.0f}K" if k else f"EUR {v:,.0f}"


# ------------------------------------------------ per-category question bank --
# Framed as questions, never as an asserted cause — distributors essentially
# never source competitively at DB level, so lead with price/service/stock.
QUESTIONS = {
    "Brake parts": [
        "Is pad and rotor pricing competitive against what the dealers can buy locally?",
        "Is any of this stock timing on your side rather than end demand?",
        "Are dealers still quoting these part numbers, or have they dropped off the workshop menu?",
    ],
    "Filters": [
        "Are dealers stocking filters, or ordering line-by-line against each job?",
        "How much servicing do you estimate is happening outside the franchised network?",
        "Would a service-pack offer on oil and fuel filters be workable for your dealers?",
    ],
    "Clutch parts": [
        "Is clutch pricing a barrier against local competition for you?",
        "What would make the biggest difference to keep this business with us?",
        "Worth a joint look at the specific part numbers together?",
    ],
    "Lighting": [
        "Is this availability, pricing, or genuinely fewer accident repairs?",
        "Are the bodyshops in your network sourcing lamps elsewhere?",
    ],
    "Air conditioning": [
        "Is the seasonal pattern different this year, or is this a real shift?",
        "Are cabin filters and A/C service being sold as a package?",
    ],
    "Injectors": [
        "Is this fewer failures, or repairs moving out of the network?",
        "Is the exchange/reman route competing with new parts here?",
        "Are dealers still quoting these part numbers, or have they dropped off the workshop menu?",
    ],
    "Turbo": [
        "Is this fewer turbo failures, or jobs moving to independents?",
        "Is reman / exchange competing with new units on price or lead time?",
        "Any availability problems on the fast-moving turbo lines?",
    ],
    "Suspension": [
        "Is this pricing against the independent aftermarket?",
        "Are dealers quoting suspension work at all, or referring it out?",
    ],
    "Transmission parts": [
        "Is this a mix shift towards assemblies, or fewer component-level repairs?",
        "Any availability problems on the fast-moving lines?",
    ],
}
GENERIC_QUESTIONS = [
    "Is this pricing against what the dealers can buy locally?",
    "Is any of this stock timing on your side rather than end demand?",
    "What would make the biggest difference to keep this business with us?",
]


def build(dbkey: str):
    p = C.load_profile(dbkey)
    out_dir = C.OUT_ROOT / f"{p['key']}_Sales_Review_2026"
    sfile = out_dir / "_summary.json"
    if not sfile.exists():
        raise SystemExit(f"No {sfile} — run:  python build_parts_analysis.py --db {p['key']}")
    S = json.loads(sfile.read_text(encoding="utf-8"))
    d = S["defaults"]
    # Live reload so fleet / GPS / S2D growth pick up the carpark pack without
    # forcing a full parts-analysis rebuild.
    fy = C.load_fy27(p)
    s2d = fy["s2d_target"]
    gps = C.load_segmented_gps(p)
    uio_live = C.load_uio(p)
    pbi_raw = S["pbi"]
    pbi_complete = bool(
        pbi_raw
        and pbi_raw.get("sales")
        and pbi_raw.get("budget")
        and pbi_raw.get("prev_year")
        and all(v is not None for k in ("sales", "budget", "prev_year")
                for v in pbi_raw.get(k, []))
        and len(pbi_raw["sales"]) == len(pbi_raw["months"])
        == len(pbi_raw["budget"]) == len(pbi_raw["prev_year"])
    )
    PBI = pbi_raw if pbi_complete else None
    if pbi_raw and not pbi_complete:
        print(f"[{p['key']}] WARNING: incomplete Power BI cut — sales-review slide skipped.")
    # Live labels from profile defaults so CY vs FY wording stays current
    # (summary.json may still hold the old "Q1 2026" strings).
    L25 = p["defaults"].get("window_label_prior") or S["label_prior"]
    L26 = p["defaults"].get("window_label_current") or S["label_current"]
    disp = S["display"]

    chart_dir = out_dir / "charts_out"
    chart_dir.mkdir(parents=True, exist_ok=True)

    def cp(n):
        return str(chart_dir / n)

    # ------------------------------------------------------------- charts --
    if PBI:
        ct.bar_chart(
            PBI["months"],
            {f"Sales (EUR K)": [v // 1000 for v in PBI["sales"]],
             "Budget (EUR K)": [v // 1000 for v in PBI["budget"]],
             "Prior year (EUR K)": [v // 1000 for v in PBI["prev_year"]]},
            cp("quarter.png"),
            title=f"{disp} {PBI['quarter']} — sales vs budget vs prior year (EUR K)",
            ylabel="EUR K", value_fmt="{:,.0f}", figsize=(10.2, 4.5))

    cats = [c for c in S["categories"] if c["cat"] != "UNCLASSIFIED" and abs(c["d"]) > 1000]
    cats = sorted(cats, key=lambda c: c["d"])
    pick = cats[:5] + cats[-4:] if len(cats) > 9 else cats
    diverging_bar([wrap_label(c["cat"], 9) for c in pick], [c["d"] for c in pick],
                  cp("category_movers.png"),
                  title=f"{disp} {L26} vs {L25} — biggest category moves (EUR)")

    peers = S["pms_peers"]
    plabels = {"oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
               "brake_pad": "Brake pad", "brake_rotor": "Brake rotor"}
    pkeys = [k for k in plabels if k in peers]
    pms_yr = S.get("pms_year")
    ct.bar_chart(
        [plabels[k] for k in pkeys],
        {disp: [peers[k]["db"] for k in pkeys],
         "Network (all other markets)": [peers[k]["network"] for k in pkeys],
         "Best market in the network": [peers[k]["best"] for k in pkeys]},
        cp("pms.png"),
        title=(f"Service-parts capture by category — {disp} vs network "
               f"(CY{pms_yr} full year, %)" if pms_yr else
               f"Service-parts capture by category — {disp} vs the rest of the network (%)"),
        ylabel="% of fleet service demand captured", value_fmt="{:,.1f}", figsize=(10.2, 4.5))

    uio = uio_live
    total = {int(k): v for k, v in uio["total"].items()}
    years = [y for y in sorted(total) if 2019 <= y <= 2026]
    series = {}
    segs = {k: v for k, v in uio.items() if k != "total"}
    namemap = {"lcv": "LCV / D-Max", "ld": "CV — LD", "md": "CV — MD", "f_series": "F-Series"}
    # Avoid Total ≈ dominant-segment double line (IBX: LCV ~98% of fleet).
    # Plot Total only when one segment dominates; otherwise plot meaningful
    # segments (≥5% of latest year) without a redundant Total series.
    latest = years[-1] if years else None
    tot_latest = float(total.get(latest, 0) or 0) if latest is not None else 0.0
    seg_latest = {}
    for seg, vals in segs.items():
        vv = {int(k): v for k, v in vals.items()}
        if sum(vv.values()) > 0:
            seg_latest[seg] = float(vv.get(latest, 0) or 0)
    dominant_share = (max(seg_latest.values()) / tot_latest) if tot_latest and seg_latest else 1.0
    meaningful = [
        seg for seg, v in seg_latest.items()
        if tot_latest and (v / tot_latest) >= 0.05
    ]
    fleet_mix_note = None
    if len(seg_latest) <= 1 or dominant_share >= 0.90 or len(meaningful) <= 1:
        series["Total fleet"] = [total.get(y, 0) for y in years]
        if seg_latest and tot_latest:
            parts = [
                f"{namemap.get(s, s)} {seg_latest[s]:,.0f}"
                for s in sorted(seg_latest, key=lambda s: -seg_latest[s])
            ]
            fleet_mix_note = (
                f"End-{latest} mix: " + "; ".join(parts) + "."
            )
    else:
        for seg in sorted(meaningful, key=lambda s: -seg_latest[s]):
            vv = {int(k): v for k, v in segs[seg].items()}
            series[namemap.get(seg, seg)] = [vv.get(y, 0) for y in years]
        tiny = [s for s in seg_latest if s not in meaningful]
        if tiny:
            fleet_mix_note = (
                "Smaller segments not plotted (<5% of fleet): "
                + ", ".join(f"{namemap.get(s, s)} {seg_latest[s]:,.0f}" for s in tiny)
                + "."
            )
    ct.trend_line([str(y) for y in years], series, cp("uio.png"),
                  title=f"{disp} fleet — {total[years[0]]:,} ({years[0]}) to "
                        f"{total[years[-1]]:,} ({years[-1]} forecast)",
                  value_fmt="{:,.0f}")
    S["fleet_mix_note"] = fleet_mix_note

    # -------------------------------------------------------------- deck --
    prs = db.new_presentation()
    db.build_cover(prs, title=f"{disp} Sales Review\n& FY2027 Target",
                   subtitle=f"{S['name']}  ·  August 2026",
                   eyebrow=f"ISZE  ·  {S['country'].upper()}  ·  {p['key']}")

    # Skip catch-all / junk categories on the deep-dive stage (e.g. radio + DEF
    # under Miscellaneous). Prefer real commodity drops: brakes, injectors, turbo.
    _DECLINE_SKIP = {"Miscellaneous", "UNCLASSIFIED", "Hardware", "Belts"}
    decliners = [c for c in cats if c["d"] < 0 and c["cat"] not in _DECLINE_SKIP][:3]
    agenda = ["Q1 FY2027 Sales Review"] if PBI else []
    agenda += ["Parts Performance — category movers"]
    agenda += [f"Parts Performance — {c['cat']}" for c in decliners]
    agenda += ["Parts Performance — where volume grew"]
    _nb_agenda = [
        x for x in (S.get("new_business") or [])
        if str(x.get("pn") or "").strip().upper() not in {"TRANSPORT", "FREIGHT", "SHIPPING"}
        and "transport" not in str(x.get("desc") or "").lower()
    ]
    if _nb_agenda:
        agenda += ["New Business — validation queue"]
    agenda += ["Sales-to-Dealer Outlook"]
    if gps:
        agenda += ["GPS Capture"]
    agenda += ["Service-Parts Coverage"]
    if S["ids"]:
        agenda += ["IDS 2026 — Dealer Standard"]
    agenda += ["Fleet & FY2027 Target", "SPA — status", "R&M — market discussion",
               "Data request: part-level Sales-to-Dealer", "Next steps"]
    s = db.build_content(prs, "Agenda", eyebrow=f"{p['key']} Meeting", page_no=2)
    # 13+ items at size 16 overflow behind the footer logo — scale to fit the
    # 5.2in content band rather than letting the last items disappear.
    a_size = 16 if len(agenda) <= 11 else (14.5 if len(agenda) <= 13 else 13)
    db.bullet_list(s, agenda, Inches(0.32), Inches(1.32), Inches(11.5), Inches(5.2),
                   size=a_size, line_spacing=1.1)

    page = 3

    # ---- official quarter --------------------------------------------------
    if PBI:
        tot_s, tot_b, tot_p = sum(PBI["sales"]), sum(PBI["budget"]), sum(PBI["prev_year"])
        var = [PBI["sales"][i] / PBI["budget"][i] - 1 for i in range(len(PBI["months"]))]
        best = max(range(len(var)), key=lambda i: var[i])
        others_below = all(var[i] < 0 for i in range(len(var)) if i != best)
        takeaways = [
            f"Sales {eur(tot_s, True)} against a {eur(tot_b, True)} budget — {tot_s/tot_b-1:+.0%}, "
            f"and {tot_s/tot_p-1:+.0%} on last year's {eur(tot_p, True)}."]
        if others_below and var[best] > 0:
            takeaways.append(
                f"The beat is entirely {PBI['months'][best]}: {eur(PBI['sales'][best], True)} against "
                f"{eur(PBI['budget'][best], True)}. " +
                " and ".join(f"{PBI['months'][i]} {var[i]:+.0%}"
                             for i in range(len(var)) if i != best) + " are both below budget.")
        else:
            takeaways.append("By month vs budget: " + ", ".join(
                f"{PBI['months'][i]} {var[i]:+.0%}" for i in range(len(var))) + ".")
        if PBI.get("order_intake_total"):
            oi = PBI["order_intake_total"]
            takeaways.append(f"Order intake for the quarter was {eur(oi, True)} against "
                             f"{eur(tot_s, True)} billed — orders ran at about {oi/tot_s:.0%} "
                             "of shipments.")
        takeaways.append("Worth walking through the shape of the quarter together, and what the "
                         "order book looks like from here.")
        db.build_two_col(
            prs, title=f"{PBI['quarter']}: {eur(tot_s, True)}, {tot_s/tot_b-1:+.0%} vs budget",
            chart_path=cp("quarter.png"),
            eyebrow=f"{PBI['quarter']} Sales Review", page_no=page, takeaways=takeaways[:4])
        page += 1

    # ---- category movers --------------------------------------------------
    gp, gc = S["gross_prior"], S["gross_current"]
    cred = S["credits_current"]
    take = [f"Parts billing {eur(gc, True)} against {eur(gp, True)} a year earlier — "
            f"{S['gross_delta_pct']:+.1%}."]
    if abs(cred) > 1000:
        take[0] += f" After {eur(abs(cred), True)} of credit notes the net figure is {eur(S['net_current'], True)}."
    if decliners:
        take.append("Biggest declines: " + "; ".join(
            f"{c['cat']} {eur(c['d'], True)}" for c in decliners) + ".")
    risers = [c for c in cats if c["d"] > 0][-3:][::-1]
    if risers:
        take.append("Growing: " + ", ".join(
            f"{c['cat']} {c['dp']:+.0%}" for c in risers if c["dp"] is not None) + ".")
    take.append(f"{L26} against {L25} (calendar Jan–Jun, Q1+Q2) — like-for-like half-year cut.")
    db.build_two_col(prs, title=f"Parts Performance — {L26} vs {L25}",
                     chart_path=cp("category_movers.png"),
                     eyebrow="Parts Performance", page_no=page, takeaways=take[:4])
    page += 1

    # ---- one slide per material declining category ------------------------
    for n_cat, cat in enumerate(decliners):
        rows = [r for r in S["top_decl_itc"] if r["cat"] == cat["cat"]][:3]
        # Title-case the category so "Brake parts" does not read "Brake parts Performance"
        cat_title = cat["cat"][0].upper() + cat["cat"][1:]
        s = db.build_content(prs, f"{cat_title} — {L26} vs {L25}",
                             eyebrow=f"Parts Performance — {cat['cat']}", page_no=page)
        bullets = [f"{eur(cat['prior'])} ({L25}) to {eur(cat['current'])} ({L26}), "
                   f"down {eur(abs(cat['d']))}" + (f" ({cat['dp']:.0%})." if cat['dp'] else ".")]
        for r in rows:
            q = f", {abs(r['dq']):,.0f} fewer pieces" if r["dq"] < 0 else ""
            bullets.append(f"{r['pn']} ({r['desc']}): {eur(r['prior'])} to {eur(r['current'])}{q}.")
        # Do NOT attach whole-window BVP movement to a single category decline —
        # that BVP total is cross-category and reads as a false value-tier proof.
        db.bullet_list(s, bullets, Inches(0.32), Inches(1.32), Inches(12.7), Inches(2.9), size=14)
        db.txt(s, "Questions for us to work through together", Inches(0.32), Inches(4.20),
               Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
        db.bullet_list(s, QUESTIONS.get(cat["cat"], GENERIC_QUESTIONS),
                       Inches(0.32), Inches(4.55), Inches(12.7), Inches(1.9), size=14)
        page += 1

    # ---- growth ------------------------------------------------------------
    s = db.build_content(prs, f"Where volume grew — {L26} vs {L25}",
                         eyebrow="Parts Performance — Growth", page_no=page)
    grow = S["top_grow_itc"][:6]
    rows = [["Part", "Description", L25, L26]] + [
        [g["pn"], str(g["desc"])[:34], eur(g["prior"]), eur(g["current"])] for g in grow]
    styled_table(s, rows, Inches(0.32), Inches(1.32), Inches(12.7), Inches(2.6),
                 [Inches(2.4), Inches(4.9), Inches(2.7), Inches(2.7)],
                 bold_last=False, size=12, left_cols=(0, 1))
    gbul = []
    if risers:
        gbul.append(", ".join(f"{c['cat']} {c['dp']:+.0%}" for c in risers if c["dp"] is not None)
                    + " — where the volume went.")
    if S.get("warranty_claim"):
        gbul.append(
            f"Several of these are the kind of item that also moves on a campaign or claim. "
            f"{S['country']} CY2025 warranty parts (claim-price basis) were "
            f"{eur(S['warranty_claim'], True)} — separate from fiscal GPS warranty expense. "
            "Do not read this growth list as purely commercial without checking claims together."
        )
    gbul.append("Worth agreeing which of these are repeatable and which were one-off.")
    db.bullet_list(s, gbul, Inches(0.32), Inches(4.20), Inches(12.7), Inches(2.4), size=14)
    page += 1

    # ---- New Business quarantine ------------------------------------------
    new_biz = [
        x for x in (S.get("new_business") or [])
        if str(x.get("pn") or "").strip().upper() not in {"TRANSPORT", "FREIGHT", "SHIPPING"}
        and "transport" not in str(x.get("desc") or "").lower()
    ]
    if new_biz:
        s = db.build_content(prs, f"New Business — validation queue ({L26})",
                             eyebrow="Parts Performance", page_no=page)
        nb = new_biz[:6]
        rows = [["Part", "Description", "Current sales", "Review"]]
        rows += [[x["pn"], str(x["desc"])[:31], eur(x["current"]),
                  "Warranty / campaign" if x.get("warranty_campaign") else "Validate"]
                 for x in nb]
        styled_table(s, rows, Inches(0.32), Inches(1.32), Inches(12.7), Inches(2.8),
                     [Inches(2.4), Inches(4.4), Inches(2.4), Inches(3.5)],
                     bold_last=False, size=11.5, left_cols=(0, 1, 3))
        db.bullet_list(s, [
            "These lines had no prior-period sales, so they are kept out of the incremental-growth table.",
            "A first sale can be a new model, a supersession, timing, or a warranty campaign. "
            "It is not treated as a commercial win until that cause is confirmed.",
        ], Inches(0.32), Inches(4.45), Inches(12.7), Inches(1.5), size=14)
        page += 1

    # ---- Sales-to-Dealer lens ---------------------------------------------
    s = db.build_content(prs, "Sales-to-Dealer outlook — FY2027",
                         eyebrow="Sales-to-Dealer", page_no=page)
    base_label = "working estimate" if s2d["s2d_imputed"] else "reported KPI"
    db.bullet_list(s, [
        f"FY2026 Sales-to-Dealer is {eur(s2d['fy26'])} ({base_label}).",
        f"The working fleet movement into FY2027 is {s2d['uio_growth']:+.1%}.",
        f"Applying fleet movement, the 5% price adjustment and 1.8% additional growth gives "
        f"a FY2027 Sales-to-Dealer target of {eur(s2d['fy27'])}.",
        "The discussion is held in Sales-to-Dealer amounts; ISZE billing remains an internal "
        "reconciliation measure.",
    ], Inches(0.32), Inches(1.35), Inches(11.9), Inches(4.2), size=15)
    page += 1

    # ---- GPS Capture (Portugal-style: one clean number, no recon trail) ----
    if gps:
        g26 = gps["gps_FY2026"]
        if gps["show_pct"]:
            pct_lab = f"{g26 * 100:.1f}%"
            s = db.build_content(prs, f"GPS Capture: {pct_lab}",
                                 eyebrow="GPS", page_no=page)
            db.bullet_list(s, [
                "GPS measures your actual parts purchases against the full potential of your fleet.",
                f"{disp} today: {pct_lab} (FY2026 purchases against the CY2025 fleet potential).",
                f"Fleet potential: {eur(gps['wallet_2025'], True)} on {gps['uio_2025']:,} vehicles.",
                f"Real, sustained headroom above {pct_lab} — the service-parts and SPA discussion "
                "are both direct levers on it.",
            ], Inches(0.32), Inches(1.35), Inches(11.5), Inches(3.5), size=15)
        else:
            s = db.build_content(prs, "GPS — amount view",
                                 eyebrow="GPS", page_no=page)
            db.bullet_list(s, [
                "GPS compares actual parts purchases to the theoretical potential of the fleet.",
                f"FY2026 purchases: {eur(gps['net_FY2026'], True)}.",
                f"CY2025 fleet potential: {eur(gps['wallet_2025'], True)} "
                f"({gps['uio_2025']:,} vehicles).",
                "Purchases sit above that theoretical potential — we discuss the amount and the "
                "per-vehicle rate, not a capture percentage.",
            ], Inches(0.32), Inches(1.35), Inches(11.5), Inches(3.5), size=15)
        page += 1

    # ---- PMS ---------------------------------------------------------------
    below = sorted(peers.items(), key=lambda kv: kv[1]["db"] - kv[1]["network"])
    worst = below[:2]
    ptake = [f"{plabels[k]} {v['db']:.1f}% against {v['network']:.1f}% for the rest of the network."
             for k, v in worst]
    ptake.append("Every market here is measured on the same fleet-and-interval model, so the "
                 "comparison is like-for-like even where the underlying interval assumption is "
                 "debatable.")
    ptake.append("Worth agreeing which category we tackle first, and what the joint action is.")
    above = [k for k, v in peers.items() if v["db"] >= v["network"]]
    title_pms = ("Service-parts coverage sits below the network on every routine category"
                 if not above else
                 f"Service-parts coverage: {plabels[worst[0][0]].lower()} is the clear gap")
    db.build_two_col(prs, title=title_pms, chart_path=cp("pms.png"),
                     eyebrow="Service-Parts Coverage", page_no=page, takeaways=ptake[:4])
    page += 1

    # ---- IDS ---------------------------------------------------------------
    if S["ids"]:
        I = S["ids"]
        s = db.build_content(
            prs, f"IDS 2026: {disp} averages {I['db_avg']:.1f}%, "
                 f"{'above' if I['db_avg'] >= I['network_avg'] else 'below'} the "
                 f"{I['network_avg']:.1f}% network benchmark",
            eyebrow="IDS 2026 — Dealer Standard", page_no=page)
        rows = [["Dealer", "Total %", "Global rank"]]
        rows += [[str(x["dealer"]).title(), f"{x['pts']:.1f}%", f"#{x['grank']}"] for x in I["top"]]
        rows += [[f"{disp} country average", f"{I['db_avg']:.1f}%", "—"],
                 ["Network average (all IDS 2026)", f"{I['network_avg']:.1f}%", "—"]]
        rows += [[str(x["dealer"]).title(), f"{x['pts']:.1f}%", f"#{x['grank']}"] for x in I["bottom"]]
        styled_table(s, rows, Inches(0.32), Inches(1.32), Inches(12.7), Inches(3.0),
                     [Inches(7.1), Inches(2.8), Inches(2.8)], bold_last=False, size=11.5)
        spread = I["top"][0]["pts"] - I["bottom"][-1]["pts"]
        db.bullet_list(s, [
            f"{I['n']} dealers assessed across Premises, Organisation, Service, Parts and Vehicle Sales.",
            f"The country average sits {abs(I['db_avg']-I['network_avg']):.1f} points "
            f"{'above' if I['db_avg'] >= I['network_avg'] else 'below'} the network.",
            f"The spread is the point: {spread:.0f} points between the strongest and weakest dealer.",
            "Dealer-by-dealer detail and individual feedback are available as a separate pack — "
            "worth agreeing which dealers to visit, and when.",
        ], Inches(0.32), Inches(4.55), Inches(12.7), Inches(2.2), size=13.5)
        page += 1

    # ---- fleet -------------------------------------------------------------
    growth = (total.get(2026, 0) / total.get(2025, 1) - 1) if total.get(2025) else 0
    fleet_title = ("The fleet is expected to decline in 2026" if growth < 0
                   else "The fleet is expected to grow in 2026")
    fleet_takes = [
        f"Fleet size (calendar year): {total.get(2025, 0):,} vehicles in 2025 → "
        f"{total.get(2026, 0):,} working estimate for end-2026 ({growth:+.1%}).",
        "The chart is calendar years 2019–2026 only. 2026 is a working year-end estimate, "
        "not a fiscal-year figure.",
    ]
    if S.get("fleet_mix_note"):
        fleet_takes.append(S["fleet_mix_note"])
    fleet_takes.append(
        f"The FY2027 Sales-to-Dealer target starts from that fleet change, then applies "
        f"a {s2d['price']:.0%} price adjustment and {s2d['additional']:.1%} additional growth."
    )
    fleet_takes.append(
        "So the target is built from a slightly smaller fleet — not from an assumed growth story."
        if growth < 0 else
        "The target reflects the working fleet outlook without extending the chart beyond 2026."
    )
    db.build_two_col(
        prs, title=fleet_title,
        chart_path=cp("uio.png"), eyebrow="Fleet & FY2027 Target", page_no=page,
        takeaway_heading="What this means for FY2027",
        takeaways=fleet_takes)
    page += 1

    # ---- target build-up ---------------------------------------------------
    s = db.build_content(prs, "How the FY2027 target is built",
                         eyebrow="Fleet & FY2027 Target", page_no=page)
    db.txt(s, "Sales-to-Dealer amount bridge",
           Inches(0.32), Inches(1.28), Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
    base = s2d["fy26"]
    after_uio = base * (1 + s2d["uio_growth"])
    after_price = after_uio * (1 + s2d["price"])
    up = s2d["fy27"] / base - 1 if base else 0
    trows = [
        ["Step", "Amount"],
        [f"FY2026 Sales-to-Dealer ({'working estimate' if s2d['s2d_imputed'] else 'reported KPI'})",
         eur(base)],
        [f"After fleet movement ({s2d['uio_growth']:+.1%})", eur(after_uio)],
        [f"After price adjustment (+{s2d['price']:.0%})", eur(after_price)],
        [f"FY2027 target after additional growth (+{s2d['additional']:.1%})",
         eur(s2d["fy27"])],
    ]
    styled_table(s, trows, Inches(0.32), Inches(1.65), Inches(9.4), Inches(2.35),
                 [Inches(6.2), Inches(3.2)], size=12.5)
    foot = [
        f"The FY2027 target is {up:+.1%} versus the FY2026 Sales-to-Dealer base.",
        ("The FY2026 base is a working estimate (ISZE billing ÷ 0.65): the KPI Dashboard has "
         "no usable Sales-to-Dealer row for this market." if s2d["s2d_imputed"] else
         "The FY2026 base is the reported Sales-to-Dealer KPI."),
    ]
    db.bullet_list(s, foot, Inches(0.32), Inches(4.35), Inches(12.7),
                   Inches(1.3), size=13)
    page += 1

    # ---- growth / price / incentive ---------------------------------------
    s = db.build_content(prs, "What the FY2027 target reflects",
                         eyebrow="FY2027 Target", page_no=page)
    card(s, Inches(0.32), Inches(1.35), Inches(6.0), Inches(2.2), "1", "Your fleet",
         [f"The working fleet movement used in the target is {s2d['uio_growth']:+.1%}."])
    card(s, Inches(6.5), Inches(1.35), Inches(6.5), Inches(2.2), "2", "The price move",
         [f"ISZE is applying a {d['price_increase_fy27']:.0%} price adjustment for FY2027, "
          "consistent with every ISZE market this year.",
          "It is built into the per-vehicle rate above, not added separately on top."])
    db.txt(s, "What it means for your target", Inches(0.32), Inches(3.80), Inches(9.4),
           Inches(0.3), size=13, bold=True, color=RED)
    styled_table(s, [["", "Value"],
                     ["FY2027 Sales-to-Dealer target", eur(s2d["fy27"])],
                     [f"vs FY2026 Sales-to-Dealer ({eur(base)})", f"{up:+.1%}"]],
                 Inches(0.32), Inches(4.14), Inches(9.4), Inches(1.35), [Inches(5.5), Inches(3.9)])
    db.bullet_list(s, [
        "As in previous cycles we would expect an incentive to sit alongside this adjustment — "
        "that approval is still pending on our side.",
        "Until the incentive is confirmed, treat the FY2027 target as the working bridge "
        "(fleet × price × additional growth), not a locked commercial commitment.",
    ], Inches(0.32), Inches(5.55), Inches(12.7), Inches(1.05), size=12.5)
    page += 1

    # ---- SPA ---------------------------------------------------------------
    s = db.build_content(prs, "SPA", eyebrow="SPA", page_no=page)
    for i, (letter, hdr, line) in enumerate([
            ("1", f"{p['key']} proposal", f"{S['name']} submits a proposed parts list."),
            ("2", "ISZE review", "ISZE reviews the proposal against network data and fit."),
            ("3", "Counter-proposal", "ISZE returns a counter-proposal where needed."),
            ("4", "Final approval", "Signed off by ISZE management.")]):
        card(s, Inches(0.32 + i * 3.21), Inches(1.35), Inches(3.06), Inches(3.4),
             letter, hdr, [line])
    db.txt(s, "Purpose: higher turnover for both sides.", Inches(0.32), Inches(5.00),
           Inches(9.4), Inches(0.4), size=14, bold=True, color=RED)
    page += 1

    # ---- R&M --------------------------------------------------------------
    s = db.build_content(prs, "R&M — let's align on the market", eyebrow="R&M", page_no=page)
    card(s, Inches(0.32), Inches(1.30), Inches(6.0), Inches(4.4), "M", "Market",
         ["How is the market moving for you right now?",
          "How much of your volume is fleet business rather than retail?",
          "Where do you see the biggest hurdles this year?",
          "Where are your real strengths in this segment?"])
    card(s, Inches(6.5), Inches(1.30), Inches(6.5), Inches(4.4), "S", "Servicing & R&M",
         ["Do you offer an R&M or service-plan product today?",
          "What share of the parc do you retain for servicing after year three?",
          "Does R&M business come bundled with fleet tenders — roughly what share?",
          "What would it take to bring more out-of-network servicing back?"])
    page += 1

    # ---- data request -----------------------------------------------------
    has_s2d = not s2d["s2d_imputed"]
    s = db.build_content(prs, "Part-level Sales-to-Dealer Data", eyebrow="Ask", page_no=page)
    first = ("You already report Sales-to-Dealer monthly. The ask is the same data at "
             "part-number level." if has_s2d else
             "We have no Sales-to-Dealer figures from you for FY2026. The ask is monthly "
             "Sales-to-Dealer, at part-number level.")
    card(s, Inches(0.32), Inches(1.35), Inches(3.95), Inches(2.6), "1",
         "Already halfway there" if has_s2d else "The starting point", [first])
    card(s, Inches(4.47), Inches(1.35), Inches(3.95), Inches(2.6), "2", "Sharper insight",
         ["Part-by-part visibility separates a stock movement from a lost job — and tells us where "
          "the volume actually went."])
    card(s, Inches(8.62), Inches(1.35), Inches(3.95), Inches(2.6), "3", "Shared benefit",
         ["Better availability on your fast movers, a sharper target for us, and a factual basis "
          "for the SPA — same data, both sides gain."])
    db.txt(s, "Requested from 01/01/2025, part number level, monthly.", Inches(0.32),
           Inches(4.25), Inches(9.4), Inches(0.4), size=14, bold=True, color=RED)
    page += 1

    # ---- next steps -------------------------------------------------------
    s = db.build_content(prs, "Next steps", eyebrow="Summary", page_no=page)
    if S.get("incentive_fy27") is None:
        steps = [
            "Align on the FY2027 Sales-to-Dealer bridge (fleet, price, additional growth) — "
            f"working figure {eur(s2d['fy27'])} ({up:+.1%} vs FY2026 base).",
            "Confirm the incentive alongside the price adjustment; lock the target once that "
            "approval is through.",
        ]
    else:
        steps = [f"Confirm FY2027 Sales-to-Dealer target: {eur(s2d['fy27'])} "
                 f"({up:+.1%} vs FY2026 Sales-to-Dealer).",
                 "Confirm the incentive alongside the price adjustment once approved on our side."]
    if decliners:
        steps.append(f"{' / '.join(c['cat'] for c in decliners)}: agree which category we tackle "
                     "first, and what the joint action is.")
    steps.append("Agree part-level Sales-to-Dealer data sharing, effective 01/01/2025.")
    steps.append(f"SPA: {p['key']} proposal, ISZE review and counter-proposal cycle to follow.")
    if S["ids"]:
        steps.append("IDS 2026: agree dealer visit dates, starting with the lower-scoring dealers.")
    if PBI and PBI.get("order_intake_total"):
        steps.append("Q2 outlook: review the order book against the Q1 shipment pattern.")
    db.bullet_list(s, steps, Inches(0.32), Inches(1.35), Inches(12.7), Inches(4.6), size=15)

    db.build_closing(prs)

    import os
    out = os.environ.get("ISZE_DECK_OUT") or str(
        out_dir / f"ISZE_{p['key']}_Sales_Review_FY2027.pptx"
    )
    prs.save(out)
    print(f"[{p['key']}] saved {out}   ({len(prs.slides)} slides)")
    if gps:
        g = gps["gps_FY2026"]
        gtxt = f"{g*100:.1f}%" if gps["show_pct"] else "amount-only (>100%)"
        print(f"  GPS FY2026: {gtxt}  "
              f"(net {gps['net_FY2026']:,.0f} / wallet CY2025 {gps['wallet_2025']:,.0f}; "
              f"UIO {gps['uio_2025']:,} → {gps['uio_2026']:,})")
    if S["watch"]:
        print("  WATCH before sending:")
        for w in S["watch"]:
            print(f"    · {w}")
    print(f"  QA:  python qa_contact_sheet.py --pptx \"{out}\"")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help=f"one of: {', '.join(C.list_profiles())}")
    build(ap.parse_args().db)
