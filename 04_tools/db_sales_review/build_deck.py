"""Distributor Sales Review deck for one DB.

    python build_deck.py --db ISD

Reads _summary.json from build_parts_analysis.py and writes the meeting-core
deck (plus appendix PN / process slides). Structure follows the Sep 2026 craft
rules in presentation.md / DB_SALES_REVIEW_BLUEPRINT.md §2: storyline →
finding headlines → leakage cards → joint plan; PN tables in appendix.

The output is a meeting-ready DRAFT: computed narrative still needs a human
pass for the specific relationship before send.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

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


def _pn_label(r, desc_len=28):
    """Short PN + description (+ model when known) for takeaway bullets."""
    desc = str(r.get("desc") or "")[:desc_len]
    model = str(r.get("model") or "").strip()
    base = f"{r['pn']} ({desc})" if desc else str(r["pn"])
    return f"{base} [{model}]" if model else base


def _fmt_pn_delta(r, desc_len=28):
    q = ""
    dq = r.get("dq")
    if dq is not None and abs(dq) >= 1:
        q = f", {abs(dq):,.0f} {'fewer' if dq < 0 else 'more'} pcs"
    return f"{_pn_label(r, desc_len)} {eur(r['d'], True)}{q}"


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
    "Shell lubricants": [
        "When can the Shell price discussion close so lubricant orders restart?",
        "How much of the Original BP gap is lubricants vs the rest of the basket?",
        "Is any Shell volume moving outside ISZE while the hold continues?",
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

# Recommended first action on the leakage cards (meeting core).
FIRST_ACTIONS = {
    "Brake parts": "Brake / rotor pilot",
    "Filters": "Service pack",
    "Shell lubricants": "Close Shell price",
    "Clutch parts": "Pricing / SPA",
    "Lighting": "Lamps",
    "Air conditioning": "Seasonal package",
    "Injectors": "Availability / reman",
    "Turbo": "Availability / reman",
    "Suspension": "Pricing / availability",
    "Transmission parts": "Availability",
    "Hydraulic / mechanical": "Pricing / availability",
    "Exhaust": "Pricing / availability",
    "Mirrors": "Pricing / availability",
}
GENERIC_FIRST_ACTION = "Pricing / availability"


def build(dbkey: str):
    p = C.load_profile(dbkey)
    out_dir = C.OUT_ROOT / f"{p['key']}_Sales_Review_2026"
    sfile = out_dir / "_summary.json"
    if not sfile.exists():
        raise SystemExit(f"No {sfile} — run:  python build_parts_analysis.py --db {p['key']}")
    S = json.loads(sfile.read_text(encoding="utf-8"))
    d = S["defaults"]
    deck_opt = dict(p.get("deck") or {})
    # Live reload so fleet / GPS / S2D growth pick up the carpark pack without
    # forcing a full parts-analysis rebuild.
    fy = C.load_fy27(p)
    s2d = fy["s2d_target"]
    gps = C.load_segmented_gps(p)
    uio_live = C.load_uio(p)
    # Profile PBI wins when complete (meeting cut can be newer than summary.json).
    pbi_raw = p.get("pbi") if p.get("pbi") else S.get("pbi")
    if p.get("pbi"):
        S["pbi"] = p["pbi"]
    pbi_complete = bool(
        pbi_raw
        and pbi_raw.get("sales")
        and pbi_raw.get("prev_year")
        and all(v is not None for k in ("sales", "prev_year")
                for v in pbi_raw.get(k, []))
        and len(pbi_raw["sales"]) == len(pbi_raw["months"]) == len(pbi_raw["prev_year"])
    )
    PBI = pbi_raw if pbi_complete else None
    if pbi_raw and not pbi_complete:
        print(f"[{p['key']}] WARNING: incomplete Power BI cut — sales-review slide skipped.")

    # Plan line for the official-cut slide. The BP workbook is a file we can
    # point at; the Power BI "budget" bars are a browser read with nothing
    # behind them in the workspace, so BP wins wherever the DB has a BP row.
    ref = ref_label = None
    if PBI:
        bp_month = C.load_bp_monthly(p)
        if bp_month:
            cand = [bp_month.get(m) for m in PBI["months"]]
            if all(v is not None for v in cand):
                ref, ref_label = cand, "BP"
        if ref is None and PBI.get("budget") and all(
                v is not None for v in PBI["budget"]) and len(PBI["budget"]) == len(PBI["months"]):
            ref, ref_label = PBI["budget"], "budget"
        if ref is None:
            print(f"[{p['key']}] WARNING: no BP or budget series — official-cut slide "
                  "shows sales vs prior year only.")
    # Live labels from profile defaults so CY vs FY wording stays current
    # (summary.json may still hold the old "Q1 2026" strings).
    L25 = p["defaults"].get("window_label_prior") or S["label_prior"]
    L26 = p["defaults"].get("window_label_current") or S["label_current"]
    disp = S["display"]

    # Optional UIO adders (e.g. IBX Poland UIO10) — widen GPS denominator without
    # waiting on missing NL/LUX rows.
    gps_adders = list(p.get("gps_uio_adders") or [])
    if gps and gps_adders:
        add_uio = sum(int(a.get("uio") or 0) for a in gps_adders)
        add_wallet = sum(float(a.get("uio") or 0) * float(a.get("rate") or 250) for a in gps_adders)
        gps = dict(gps)
        gps["uio_2025_base"] = gps["uio_2025"]
        gps["wallet_2025_base"] = gps["wallet_2025"]
        gps["uio_2025"] = int(gps["uio_2025"]) + add_uio
        gps["wallet_2025"] = float(gps["wallet_2025"]) + add_wallet
        if gps["wallet_2025"]:
            gps["gps_FY2026"] = float(gps["net_FY2026"]) / float(gps["wallet_2025"])
            gps["show_pct"] = gps["gps_FY2026"] <= 1.05
        gps["adder_note"] = "; ".join(
            f"{a.get('label') or 'adder'}: +{int(a.get('uio') or 0):,} UIO"
            for a in gps_adders
        )

    ext_target = p.get("ext_target_v31")
    if ext_target is None and fy.get("ext_target"):
        ext_target = fy["ext_target"].get("fy27")
    use_ext = bool(deck_opt.get("use_isze_ext_target") and ext_target)

    chart_dir = out_dir / "charts_out"
    chart_dir.mkdir(parents=True, exist_ok=True)
    # Windows can return EINVAL when overwriting PNGs that are still held
    # (Explorer preview / Defender). Write into a fresh stamp folder each run.
    from datetime import datetime, timezone as _tz
    _stamp = datetime.now(_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    chart_dir = chart_dir / f"run_{_stamp}"
    chart_dir.mkdir(parents=True, exist_ok=True)

    def cp(n):
        return str(chart_dir / n)

    # ------------------------------------------------------------- charts --
    if PBI:
        series = {f"Sales (EUR K)": [v // 1000 for v in PBI["sales"]]}
        if ref:
            series[f"{'BP FY2027' if ref_label == 'BP' else 'Budget'} (EUR K)"] = [
                round(v / 1000) for v in ref]
        series["Prior year (EUR K)"] = [v // 1000 for v in PBI["prev_year"]]
        if (
            not deck_opt.get("skip_pbi_orders")
            and PBI.get("order_intake")
            and len(PBI["order_intake"]) == len(PBI["months"])
        ):
            series = {
                "Orders (EUR K)": [v // 1000 for v in PBI["order_intake"]],
                **series,
            }
        ct.bar_chart(
            PBI["months"], series, cp("quarter.png"),
            title=(f"{disp} {PBI['quarter']} — sales vs "
                   f"{'BP' if ref_label == 'BP' else 'budget'} vs prior year (EUR K)"
                   if ref else f"{disp} {PBI['quarter']} — sales vs prior year (EUR K)"),
            ylabel="EUR K", value_fmt="{:,.0f}", figsize=(10.2, 4.5))

    exclude_movers = set(deck_opt.get("exclude_movers_cats") or [])
    cats_all = [c for c in S["categories"] if c["cat"] != "UNCLASSIFIED" and abs(c["d"]) > 1000]
    cats_all = sorted(cats_all, key=lambda c: c["d"])
    cats = [c for c in cats_all if c["cat"] not in exclude_movers]
    # Chart scale: exclude mega-categories when requested (IBX Body), keep full list for takeaways.
    pick_src = cats if exclude_movers else cats_all
    pick = pick_src[:5] + pick_src[-4:] if len(pick_src) > 9 else pick_src
    movers_title = f"{disp} {L26} vs {L25} — commercial category moves, ex-warranty (EUR)"
    if exclude_movers:
        movers_title += f" — excl. {', '.join(sorted(exclude_movers))}"
    diverging_bar([wrap_label(c["cat"], 9) for c in pick], [c["d"] for c in pick],
                  cp("category_movers.png"),
                  title=movers_title)
    cats = cats_all  # decline / growth logic still uses full commercial set

    peers = S["pms_peers"]
    plabels = {"oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
               "brake_pad": "Brake pad", "brake_rotor": "Brake rotor"}
    # Categories whose capture rate breaches the model ceiling are withheld, not
    # plotted — see C.quotable_pms for why.
    _ok, _drop = C.quotable_pms({k: peers[k] for k in plabels if k in peers})
    pkeys = [k for k in plabels if k in _ok]
    pms_dropped = [plabels[k] for k in plabels if k in _drop]
    show_pms = len(pkeys) >= 3
    if pms_dropped:
        print(f"[{p['key']}] capture >100% withheld: {', '.join(pms_dropped)}"
              + ("" if show_pms else " — coverage slide dropped (under 3 usable categories)"))
    pms_yr = S.get("pms_year")
    if show_pms:
        pms_series = {
            disp: [peers[k]["db"] for k in pkeys],
            "Network (all other markets)": [peers[k]["network"] for k in pkeys],
        }
        # Never plot "Best market" when any best > 100% (same artefact).
        best_vals = [peers[k]["best"] for k in pkeys]
        if best_vals and max(best_vals) <= 100:
            pms_series["Best market in the network"] = best_vals
        ct.bar_chart(
            [plabels[k] for k in pkeys],
            pms_series,
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

    # Skip catch-all / junk categories on the leakage stage.
    _DECLINE_SKIP = {"Miscellaneous", "UNCLASSIFIED", "Hardware", "Belts"}
    decliners = [c for c in cats if c["d"] < 0 and c["cat"] not in _DECLINE_SKIP][:3]
    _nb_list = [
        x for x in (S.get("new_business") or [])
        if str(x.get("pn") or "").strip().upper() not in {"TRANSPORT", "FREIGHT", "SHIPPING"}
        and "transport" not in str(x.get("desc") or "").lower()
    ]
    shell_cat = next((c for c in cats if c["cat"] == "Shell lubricants"), None)

    # ---- Executive storyline (replaces topic agenda) ----------------------
    gp0 = S.get("commercial_prior", S["gross_prior"])
    gc0 = S.get("commercial_current", S["gross_current"])
    g_pct0 = S.get("commercial_delta_pct", S["gross_delta_pct"])
    fact_cards = []
    if PBI and ref:
        tot_s, tot_p = sum(PBI["sales"]), sum(PBI["prev_year"])
        tot_b = sum(ref)
        fact_cards.append((
            "YTD sales", eur(tot_s, True),
            f"{tot_s / tot_b - 1:+.0%} vs {ref_label}; {tot_s / tot_p - 1:+.0%} vs LY",
        ))
    elif PBI:
        tot_s, tot_p = sum(PBI["sales"]), sum(PBI["prev_year"])
        fact_cards.append((
            "YTD sales", eur(tot_s, True),
            f"{tot_s / tot_p - 1:+.0%} vs LY",
        ))
    fact_cards.append((
        "Commercial parts", f"{g_pct0:+.1%}",
        f"{L26} vs {L25}",
    ))
    if gps and gps.get("show_pct"):
        fact_cards.append((
            "GPS capture", f"{gps['gps_FY2026'] * 100:.1f}%",
            f"{eur(gps['wallet_2025'], True)} fleet potential",
        ))
    if use_ext and ext_target:
        fact_cards.append((
            "FY2027 target", eur(ext_target, True),
            "Extended target (locked)",
        ))
    else:
        fact_cards.append((
            "FY2027 target", eur(s2d["fy27"], True),
            f"{s2d['fy27'] / s2d['fy26'] - 1:+.1%} vs FY2026 sales to dealer"
            if s2d.get("fy26") else "Working bridge",
        ))
    fact_cards = fact_cards[:4]

    decisions = []
    if shell_cat and (
        abs(shell_cat.get("d") or 0) > 1000
        or "shell" in str((PBI or {}).get("source") or "").lower()
    ):
        decisions.append((
            "Close the lubricant blocker",
            "Agree when Shell price discussion closes and whether any volume is "
            "moving outside ISZE while the hold continues.",
        ))
    if decliners:
        decisions.append((
            "Choose the first recovery category",
            f"Start with {decliners[0]['cat']}; make the action visible dealer-by-dealer.",
        ))
    decisions.append((
        "Unlock part-level sales-to-dealer data",
        "Monthly sales to dealer at part number level from 01/01/2025 to separate "
        "stock movements from lost jobs.",
    ))
    if len(decisions) < 3 and S.get("ids"):
        decisions.append((
            "Agree IDS dealer visits",
            "Start with the lower-scoring dealers and set visit dates.",
        ))
    decisions = decisions[:3]

    story_title = (
        "The meeting should align three commercial facts and three joint decisions"
    )
    s = db.build_content(prs, story_title, eyebrow="Executive storyline", page_no=2)
    n_fc = max(len(fact_cards), 1)
    tile_w = Inches(12.4) / n_fc - Inches(0.12)
    for i, (lab, val, sub) in enumerate(fact_cards):
        left = Inches(0.32) + i * (tile_w + Inches(0.12))
        shp = s.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.28), tile_w, Inches(1.55)
        )
        shp.fill.solid()
        shp.fill.fore_color.rgb = GRAY_BG
        shp.line.fill.background()
        db.txt(s, lab, left + Inches(0.12), Inches(1.35), tile_w - Inches(0.2),
               Inches(0.28), size=11, color=BLACK)
        db.txt(s, val, left + Inches(0.12), Inches(1.65), tile_w - Inches(0.2),
               Inches(0.55), size=22, bold=True, color=RED)
        db.txt(s, sub, left + Inches(0.12), Inches(2.25), tile_w - Inches(0.2),
               Inches(0.45), size=10, color=BLACK)
    diag = (
        f"Commercial parts billing moved {g_pct0:+.1%} ({L26} vs {L25}). "
        "Use the meeting to agree which lever we pull first — not to re-read every "
        "part number."
    )
    if decliners:
        diag = (
            f"Commercial parts billing moved {g_pct0:+.1%}, but "
            + ", ".join(c["cat"] for c in decliners)
            + " still need a joint recovery plan."
        )
    db.txt(s, diag, Inches(0.32), Inches(3.00), Inches(12.7), Inches(0.55),
           size=13, color=BLACK)
    for i, (hdr, line) in enumerate(decisions):
        card(
            s, Inches(0.32 + i * 4.2), Inches(3.65), Inches(4.0), Inches(2.35),
            str(i + 1), hdr, [line],
        )

    page = 3

    # ---- official quarter --------------------------------------------------
    if PBI:
        tot_s, tot_p = sum(PBI["sales"]), sum(PBI["prev_year"])
        tot_b = sum(ref) if ref else None
        var = ([PBI["sales"][i] / ref[i] - 1 for i in range(len(PBI["months"]))]
               if ref else [])
        best = max(range(len(var)), key=lambda i: var[i]) if var else 0
        others_below = bool(var) and all(var[i] < 0 for i in range(len(var)) if i != best)
        if ref:
            takeaways = [
                f"Sales {eur(tot_s, True)} against {ref_label} {eur(tot_b, True)} — "
                f"{tot_s/tot_b-1:+.0%}, and {tot_s/tot_p-1:+.0%} on last year's "
                f"{eur(tot_p, True)}."]
        else:
            takeaways = [f"Sales {eur(tot_s, True)} — {tot_s/tot_p-1:+.0%} on last year's "
                         f"{eur(tot_p, True)}."]
        # Original BP and the BP plan line are the same series — only quote it
        # separately when the plan line came from the Power BI budget instead.
        if (ref_label != "BP" and PBI.get("original_bp")
                and all(v is not None for v in PBI["original_bp"])):
            tot_bp = sum(PBI["original_bp"])
            takeaways.append(
                f"Against Original BP {eur(tot_bp, True)} the period is {tot_s/tot_bp-1:+.0%}."
            )
        yoy = [PBI["sales"][i] / PBI["prev_year"][i] - 1
               for i in range(len(PBI["months"])) if PBI["prev_year"][i]]
        shell_hold = "shell" in str(PBI.get("source") or "").lower() and "hold" in str(PBI.get("source") or "").lower()
        if yoy and yoy[-1] < -0.2:
            if shell_hold:
                takeaways.append(
                    f"{PBI['months'][-1]} is {yoy[-1]:+.0%} YoY — Shell lubricants on hold "
                    "(price not agreed) is the stated turnover gap into August."
                )
            else:
                takeaways.append(
                    f"{PBI['months'][-1]} softened ({yoy[-1]:+.0%} YoY) — holiday timing / stock "
                    "build can explain a quiet month after a strong spring."
                )
        if (
            not deck_opt.get("skip_pbi_orders")
            and PBI.get("order_intake_total")
        ):
            oi = PBI["order_intake_total"]
            takeaways.append(
                f"Order intake {eur(oi, True)} against {eur(tot_s, True)} billed "
                f"(orders ~{oi/tot_s:.0%} of shipments)."
            )
        if len(takeaways) < 4 and var:
            if others_below and var[best] > 0:
                rest = [f"{PBI['months'][i]} {var[i]:+.0%}"
                        for i in range(len(var)) if i != best]
                joined = (" and ".join(rest) if len(rest) < 3
                          else ", ".join(rest[:-1]) + " and " + rest[-1])
                takeaways.append(
                    f"The beat is entirely {PBI['months'][best]}: {eur(PBI['sales'][best], True)} against "
                    f"{eur(ref[best], True)}. {joined} "
                    f"{'are' if len(rest) > 1 else 'is'} below {ref_label}.")
            else:
                takeaways.append(f"By month vs {ref_label}: " + ", ".join(
                    f"{PBI['months'][i]} {var[i]:+.0%}" for i in range(len(var))) + ".")
        if len(takeaways) < 4:
            takeaways.append(
                "The conversation should move quickly from what happened to which lever "
                "we jointly pull first."
            )
        if ref:
            perf_title = (
                f"{PBI['quarter']} is {tot_s/tot_b-1:+.0%} vs {ref_label}, "
                f"but {tot_s/tot_p-1:+.0%} vs last year"
                if tot_s >= tot_b and tot_s < tot_p else
                f"{PBI['quarter']}: {eur(tot_s, True)}, {tot_s/tot_b-1:+.0%} vs {ref_label}"
            )
        else:
            perf_title = f"{PBI['quarter']}: {eur(tot_s, True)}"
        db.build_two_col(
            prs, title=perf_title,
            chart_path=cp("quarter.png"),
            eyebrow="Performance", page_no=page, takeaways=takeaways[:4])
        page += 1

    # ---- category movers (commercial / ex-warranty) -----------------------
    # Prefer commercial totals when present; fall back to blended gross for older summaries.
    gp = S.get("commercial_prior", S["gross_prior"])
    gc = S.get("commercial_current", S["gross_current"])
    g_pct = S.get("commercial_delta_pct", S["gross_delta_pct"])
    cred = S["credits_current"]
    w_strip = S.get("warranty_stripped_current") or 0
    top_decl_pn = list(S.get("top_decl_pn") or [])
    top_grow_pn = list(S.get("top_grow_pn") or [])
    # Fallback for older summaries that only carried ITC movers
    if not top_decl_pn:
        top_decl_pn = list(S.get("top_decl_itc") or [])
    if not top_grow_pn:
        top_grow_pn = list(S.get("top_grow_itc") or [])
    cat_pn = S.get("category_pn_drivers") or {}

    risers = [c for c in cats if c["d"] > 0][-3:][::-1]
    # Biggest EUR-growing category (category chart is sorted by delta ascending)
    top_rising_cat = max((c for c in cats if c.get("d") and c["d"] > 0),
                         key=lambda c: c["d"], default=None)
    take = [
        f"Commercial parts billing (warranty/campaign excluded) {eur(gc, True)} against "
        f"{eur(gp, True)} a year earlier — {g_pct:+.1%} "
        f"({L26} vs {L25}, Jan–Jun)."
    ]
    if top_decl_pn:
        take.append("Largest PN drops (all categories): " + "; ".join(
            _fmt_pn_delta(r, 20) for r in top_decl_pn[:3]) + ".")
    elif decliners:
        take.append("Biggest commercial declines: " + "; ".join(
            f"{c['cat']} {eur(c['d'], True)}" for c in decliners) + ".")
    if top_grow_pn:
        take.append("Largest PN gains (all categories): " + "; ".join(
            _fmt_pn_delta(r, 20) for r in top_grow_pn[:3]) + ".")
    elif risers:
        take.append("Growing: " + ", ".join(
            f"{c['cat']} {c['dp']:+.0%}" for c in risers if c["dp"] is not None) + ".")
    # Category +~EUR move is a sum of many PNs — surface top PNs inside the
    # biggest growing category so the takeaways don't look like they "explain"
    # the bar with three global (cross-category) PN lines.
    if top_rising_cat:
        within = (cat_pn.get(top_rising_cat["cat"]) or {}).get("grow") or []
        if within:
            take.append(
                f"Within {top_rising_cat['cat']} "
                f"({eur(top_rising_cat['d'], True)}"
                + (f", {top_rising_cat['dp']:+.0%}" if top_rising_cat.get("dp") is not None else "")
                + "): "
                + "; ".join(_fmt_pn_delta(r, 20) for r in within[:3])
                + "."
            )
    if exclude_movers:
        for excl in sorted(exclude_movers):
            hit = next((c for c in cats_all if c["cat"] == excl), None)
            if hit:
                take.insert(
                    1,
                    (
                        f"{excl} {eur(hit['d'], True)}"
                        + (f" ({hit['dp']:+.0%})" if hit.get("dp") is not None else "")
                        + " is covered in the appendix — kept off the chart scale so the "
                        "rest of the basket stays readable."
                    ),
                )
    if abs(cred) > 1000:
        take.append(
            f"Credit notes of {eur(abs(cred), True)} stay on the net bridge "
            f"(net {eur(S['net_current'], True)}); not in the movers."
        )
    elif w_strip and abs(w_strip) > 1000:
        take.append(
            f"About {eur(abs(w_strip), True)} of claim-matched PN billing was stripped "
            "so this chart is aftermarket demand, not warranty."
        )
    else:
        take.append(
            "The problem is not the whole basket; the problem is where the basket is leaking."
        )
    mix_title = (
        f"Commercial parts grew {g_pct:+.1%} — the leaks sit in specific families"
        if g_pct and g_pct > 0 else
        f"Commercial mix — {L26} vs {L25} (ex-warranty)"
    )
    db.build_two_col(prs, title=mix_title,
                     chart_path=cp("category_movers.png"),
                     eyebrow="Mix", page_no=page, takeaways=take[:4])
    page += 1

    # ---- Leakage: one card page (PN detail → appendix) ----------------------
    if decliners:
        s = db.build_content(
            prs,
            "Category gaps that deserve a direct customer conversation",
            eyebrow="Leakage", page_no=page,
        )
        n_d = len(decliners)
        card_w = Inches(12.4) / n_d - Inches(0.15)
        for i, cat in enumerate(decliners):
            qs = QUESTIONS.get(cat["cat"], GENERIC_QUESTIONS)
            q1 = qs[0] if qs else GENERIC_QUESTIONS[0]
            action = FIRST_ACTIONS.get(cat["cat"], GENERIC_FIRST_ACTION)
            left = Inches(0.32) + i * (card_w + Inches(0.15))
            shp = s.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.35), card_w, Inches(4.6)
            )
            shp.fill.solid()
            shp.fill.fore_color.rgb = GRAY_BG
            shp.line.fill.background()
            db.txt(s, cat["cat"], left + Inches(0.18), Inches(1.50),
                   card_w - Inches(0.3), Inches(0.35), size=14, bold=True, color=RED)
            db.txt(
                s,
                f"{eur(cat['prior'], True)} → {eur(cat['current'], True)}"
                + (f"  ({cat['dp']:.0%})" if cat.get("dp") is not None else ""),
                left + Inches(0.18), Inches(1.95), card_w - Inches(0.3), Inches(0.4),
                size=16, bold=True, color=BLACK,
            )
            db.txt(s, q1, left + Inches(0.18), Inches(2.55),
                   card_w - Inches(0.3), Inches(1.6), size=12, color=BLACK)
            db.txt(
                s, f"Recommended first action: {action}",
                left + Inches(0.18), Inches(4.40), card_w - Inches(0.3), Inches(0.9),
                size=12, bold=True, color=RED,
            )
        db.txt(
            s,
            "Full part-number detail is in the appendix — use this page to decide what we do.",
            Inches(0.32), Inches(6.15), Inches(12.7), Inches(0.35), size=11, color=BLACK,
        )
        page += 1

    # ---- Opportunities: short list + decision lens ------------------------
    grow = (top_grow_pn or S.get("top_grow_itc") or [])[:6]
    s = db.build_content(
        prs,
        "Use the growth list as a repeatability discussion, not just a table",
        eyebrow="Opportunities", page_no=page,
    )
    for i, g in enumerate(grow[:6]):
        row = i // 3
        col = i % 3
        left = Inches(0.32) + col * Inches(4.2)
        top = Inches(1.30) + row * Inches(1.05)
        lab = f"{str(g.get('desc') or '')[:28]}\n{g.get('pn') or ''}"
        db.txt(s, lab, left, top, Inches(2.8), Inches(0.55), size=11, color=BLACK)
        db.txt(s, f"+{eur(g['d'], True)}" if g.get("d", 0) >= 0 else eur(g["d"], True),
               left + Inches(2.7), top, Inches(1.3), Inches(0.45),
               size=14, bold=True, color=RED)
    db.txt(s, "Decision lens", Inches(0.32), Inches(3.55), Inches(12.0), Inches(0.3),
           size=13, bold=True, color=RED)
    card(s, Inches(0.32), Inches(3.95), Inches(4.0), Inches(2.15), "1", "Repeatable?",
         ["Which lines reflect structural dealer demand rather than one-off accident "
          "or stock movements?"])
    card(s, Inches(4.47), Inches(3.95), Inches(4.0), Inches(2.15), "2", "Protectable?",
         ["Which lines are most exposed to IAM or parallel sourcing if we do nothing?"])
    card(s, Inches(8.62), Inches(3.95), Inches(4.0), Inches(2.15), "3", "Actionable?",
         ["Which lines can be supported through SPA, service packs or availability "
          "focus within 90 days?"])
    page += 1

    # Deep-dive category list (Body / Shell / excluded mega-movers) — appendix only
    BODY_GROWTH_Q = [
        "Is this collision / glass volume from a few fleet events, or a sustained workshop pattern?",
        "Are windshields and bumpers staying with the network, or is bodywork leaking to IAM?",
        "Which models drive the glass and bumper PNs — and is stock aligned?",
    ]
    deep_dive_cats = []
    for excl in sorted(exclude_movers):
        hit = next((c for c in cats if c["cat"] == excl and c["d"] > 0), None)
        if hit:
            deep_dive_cats.append(hit)
    if (
        deck_opt.get("body_deep_dive")
        and "Body parts" not in exclude_movers
    ):
        body = next((c for c in cats if c["cat"] == "Body parts" and c["d"] > 0), None)
        if body:
            deep_dive_cats.append(body)
    shell = next((c for c in cats if c["cat"] == "Shell lubricants" and abs(c["d"]) > 1000), None)
    if shell and shell not in deep_dive_cats:
        deep_dive_cats.append(shell)
    new_biz = _nb_list

    # ---- skip New Business / PN declines here — appendix after joint plan --

    # ---- Sales to dealer lens ---------------------------------------------
    if not deck_opt.get("skip_s2d"):
        s = db.build_content(prs, "Sales to dealer outlook — FY2027",
                             eyebrow="Sales to dealer", page_no=page)
        base_label = "working estimate" if s2d["s2d_imputed"] else "reported KPI"
        db.bullet_list(s, [
            f"FY2026 sales to dealer is {eur(s2d['fy26'])} ({base_label}).",
            f"The working fleet movement into FY2027 is {s2d['uio_growth']:+.1%}.",
            f"Applying fleet movement, the 5% price adjustment and 1.8% additional growth gives "
            f"a FY2027 sales-to-dealer target of {eur(s2d['fy27'])}.",
            "The discussion is held in sales-to-dealer amounts; ISZE billing remains an internal "
            "reconciliation measure.",
        ], Inches(0.32), Inches(1.35), Inches(11.9), Inches(4.2), size=15)
        page += 1

    # ---- GPS Capture -------------------------------------------------------
    if gps:
        g26 = gps["gps_FY2026"]
        saty = p.get("saty_note")
        if gps["show_pct"]:
            pct_lab = f"{g26 * 100:.1f}%"
            uncap = max(0.0, float(gps["wallet_2025"]) - float(gps["net_FY2026"]))
            cap_eur = float(gps["net_FY2026"])
            s = db.build_content(
                prs,
                f"A {pct_lab} capture rate leaves {eur(uncap, True)} of fleet potential outside ISZE",
                eyebrow="GPS capture", page_no=page)
            gbullets = [
                f"Captured {eur(cap_eur, True)} · Uncaptured potential {eur(uncap, True)}.",
                f"Fleet potential: {eur(gps['wallet_2025'], True)} on {gps['uio_2025']:,} vehicles.",
                f"{disp} today: {pct_lab} (FY2026 purchases against the CY2025 fleet potential).",
            ]
            if gps.get("adder_note"):
                gbullets.append(
                    f"Denominator widened vs Belgium-only file: {gps['adder_note']} "
                    f"(base was {gps.get('uio_2025_base', 0):,} / "
                    f"{eur(gps.get('wallet_2025_base', 0), True)}). NL/LUX still 0 in carpark."
                )
            if saty:
                gbullets.append(saty)
            else:
                gbullets.append(
                    "Meeting question: which portion of the uncaptured potential is realistic "
                    "to pursue through service-parts coverage, dealer standards and SPA?"
                )
            db.bullet_list(s, gbullets[:5], Inches(0.32), Inches(1.35), Inches(11.5),
                           Inches(4.0), size=14)
        else:
            s = db.build_content(prs, "GPS — amount view",
                                 eyebrow="GPS", page_no=page)
            gbullets = [
                "GPS compares actual parts purchases to the theoretical potential of the fleet.",
                f"FY2026 purchases: {eur(gps['net_FY2026'], True)}.",
                f"CY2025 fleet potential: {eur(gps['wallet_2025'], True)} "
                f"({gps['uio_2025']:,} vehicles).",
                "Purchases sit above that theoretical potential — we discuss the amount and the "
                "per-vehicle rate, not a capture percentage.",
            ]
            if saty:
                gbullets.append(saty)
            db.bullet_list(s, gbullets[:5], Inches(0.32), Inches(1.35), Inches(11.5),
                           Inches(4.0), size=14)
        page += 1

    # ---- PMS ---------------------------------------------------------------
    if show_pms:
        shown = {k: peers[k] for k in pkeys}
        below = sorted(shown.items(), key=lambda kv: kv[1]["db"] - kv[1]["network"])
        worst = below[:2]
        ptake = [f"{plabels[k]} {v['db']:.1f}% against {v['network']:.1f}% for the rest of the network."
                 for k, v in worst]
        ptake.append("Every market here is measured on the same fleet-and-interval model, so the "
                     "comparison is like-for-like even where the underlying interval assumption is "
                     "debatable.")
        if pms_dropped:
            ptake.append(
                f"{', '.join(pms_dropped)} is not shown: the modelled demand base for that "
                "category does not hold for this market, so the rate is not quotable.")
        ptake.append("Worth agreeing which category we tackle first, and what the joint action is.")
        above = [k for k, v in shown.items() if v["db"] >= v["network"]]
        title_pms = ("Service-parts coverage sits below the network on every routine category"
                     if not above else
                     f"Service-parts coverage: {plabels[worst[0][0]].lower()} is the clear gap")
        db.build_two_col(prs, title=title_pms, chart_path=cp("pms.png"),
                         eyebrow="Service-Parts Coverage", page_no=page, takeaways=ptake[:4])
        page += 1

    # ---- IDS ---------------------------------------------------------------
    if S["ids"]:
        I = S["ids"]
        # Round before comparing: 79.44 vs 79.41 must not print as "above" when
        # both render as 79.4.
        _gap = round(I["db_avg"], 1) - round(I["network_avg"], 1)
        _dir = "above" if _gap > 0 else ("below" if _gap < 0 else "in line with")
        s = db.build_content(
            prs, f"IDS 2026: {disp} averages {I['db_avg']:.1f}%, {_dir} the "
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
        n_skipped = I.get("n_not_assessed") or 0
        ids_notes = [
            f"{I['n']} dealers assessed across Premises, Organisation, Service, Parts and Vehicle Sales."
            + ((f" {n_skipped} further dealer did not return an assessment and is excluded "
                "from every figure on this slide." if n_skipped == 1 else
                f" {n_skipped} further dealers did not return an assessment and are excluded "
                "from every figure on this slide.") if n_skipped else ""),
            (f"The country average sits {abs(_gap):.1f} points "
             f"{'above' if _gap > 0 else 'below'} the network — both averages are taken on "
             "assessed dealers only."
             if _gap else
             "The country average is level with the network — both averages are taken on "
             "assessed dealers only."),
            f"The spread is the point: {spread:.0f} points between the strongest and weakest "
            "assessed dealer.",
            "Dealer-by-dealer detail and individual feedback are available as a separate pack — "
            "worth agreeing which dealers to visit, and when.",
        ]
        db.bullet_list(s, ids_notes, Inches(0.32), Inches(4.55), Inches(12.7), Inches(2.2),
                       size=13.5)
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
    if use_ext:
        fleet_takes.append(
            f"The FY2027 extended target (ISZE→DB) applies a {s2d['price']:.0%} price "
            f"adjustment and {s2d['additional']:.1%} stretch — locked at {eur(ext_target)} "
            f"from GPS Extended Target V3.1 (Dashboard column I)."
        )
    else:
        fleet_takes.append(
            f"The FY2027 sales-to-dealer target starts from that fleet change, then applies "
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
    bp27 = (fy.get("actual") or {}).get("fy27")
    stretch_pct = (fy.get("stretch_pct") or {}).get("fy27") or s2d.get("additional") or 0.018
    stretch_eur = (fy.get("stretch_eur") or {}).get("fy27")
    max27 = (fy.get("max_spend") or {}).get("fy27")
    if use_ext:
        s = db.build_content(prs, "How the FY2027 extended target is built",
                             eyebrow="Fleet & FY2027 Target", page_no=page)
        db.txt(s, "ISZE → DB extended target (V3.1 Dashboard column I)",
               Inches(0.32), Inches(1.28), Inches(11.5), Inches(0.3), size=13, bold=True,
               color=RED)
        trows = [["Step", "Amount"]]
        if bp27 is not None:
            trows.append(["Business Plan / actual FY27 base", eur(bp27)])
        if max27 is not None:
            trows.append(["Market potential (max spend FY27)", eur(max27)])
        if stretch_eur is not None:
            trows.append([f"Stretch (+{stretch_pct:.1%} of max spend)", eur(stretch_eur)])
        trows.append(["FY2027 EXTENDED TARGET (locked)", eur(ext_target)])
        styled_table(s, trows, Inches(0.32), Inches(1.65), Inches(9.4), Inches(2.55),
                     [Inches(6.2), Inches(3.2)], size=12.5)
        db.bullet_list(s, [
            f"Extended target = BP + stretch; stretch default is {stretch_pct:.1%} "
            "(network rule from GPS Extended Target V3.1).",
            f"Figure locked from {p.get('ext_target_source') or 'V3.1 Dashboard column I'}: "
            f"{eur(ext_target)}.",
        ], Inches(0.32), Inches(4.45), Inches(12.7), Inches(1.4), size=13)
        up = (ext_target / bp27 - 1) if bp27 else 0
        base = bp27 or ext_target
        page += 1
    else:
        s = db.build_content(prs, "How the FY2027 target is built",
                             eyebrow="Fleet & FY2027 Target", page_no=page)
        db.txt(s, "Sales to dealer amount bridge",
               Inches(0.32), Inches(1.28), Inches(9.4), Inches(0.3), size=13, bold=True,
               color=RED)
        base = s2d["fy26"]
        after_uio = base * (1 + s2d["uio_growth"])
        after_price = after_uio * (1 + s2d["price"])
        up = s2d["fy27"] / base - 1 if base else 0
        trows = [
            ["Step", "Amount"],
            [f"FY2026 sales to dealer ({'working estimate' if s2d['s2d_imputed'] else 'reported KPI'})",
             eur(base)],
            [f"After fleet movement ({s2d['uio_growth']:+.1%})", eur(after_uio)],
            [f"After price adjustment (+{s2d['price']:.0%})", eur(after_price)],
            [f"FY2027 target after additional growth (+{s2d['additional']:.1%})",
             eur(s2d["fy27"])],
        ]
        styled_table(s, trows, Inches(0.32), Inches(1.65), Inches(9.4), Inches(2.35),
                     [Inches(6.2), Inches(3.2)], size=12.5)
        foot = [
            f"The FY2027 target is {up:+.1%} versus the FY2026 sales-to-dealer base.",
            ("The FY2026 base is a working estimate (ISZE billing ÷ 0.65): the KPI Dashboard has "
             "no usable sales-to-dealer row for this market." if s2d["s2d_imputed"] else
             "The FY2026 base is the reported sales-to-dealer KPI."),
        ]
        db.bullet_list(s, foot, Inches(0.32), Inches(4.35), Inches(12.7),
                       Inches(1.3), size=13)
        page += 1

    # ---- growth / price / incentive ---------------------------------------
    s = db.build_content(prs, "What the FY2027 target reflects",
                         eyebrow="FY2027 Target", page_no=page)
    card(s, Inches(0.32), Inches(1.35), Inches(6.0), Inches(2.2), "1",
         "The FY2027 business plan" if use_ext else "Your fleet",
         ([f"The target starts from the FY2027 Business Plan for this market, "
           f"{eur(bp27)}." if bp27 else "The target starts from the FY2027 Business Plan.",
           f"Your fleet outlook ({growth:+.1%}) sets the market potential the stretch is "
           "measured against."]
          if use_ext else
          [f"The working fleet movement used in the target is {s2d['uio_growth']:+.1%}."]))
    card(s, Inches(6.5), Inches(1.35), Inches(6.5), Inches(2.2), "2", "The price move",
         [f"ISZE is applying a {d['price_increase_fy27']:.0%} price adjustment for FY2027, "
          "consistent with every ISZE market this year.",
          "It is built into the per-vehicle rate above, not added separately on top."])
    db.txt(s, "What it means for your target", Inches(0.32), Inches(3.80), Inches(9.4),
           Inches(0.3), size=13, bold=True, color=RED)
    if use_ext:
        styled_table(s, [["", "Value"],
                         ["FY2027 extended target (V3.1 col I)", eur(ext_target)],
                         [f"vs BP FY27 ({eur(base)})", f"{up:+.1%}"],
                         [f"Stretch included", f"+{stretch_pct:.1%}"]],
                     Inches(0.32), Inches(4.14), Inches(9.4), Inches(1.55),
                     [Inches(5.5), Inches(3.9)])
    else:
        styled_table(s, [["", "Value"],
                         ["FY2027 sales-to-dealer target", eur(s2d["fy27"])],
                         [f"vs FY2026 sales to dealer ({eur(base)})", f"{up:+.1%}"]],
                     Inches(0.32), Inches(4.14), Inches(9.4), Inches(1.35),
                     [Inches(5.5), Inches(3.9)])
    db.bullet_list(s, [
        "As in previous cycles we would expect an incentive to sit alongside this adjustment — "
        "that approval is still pending on our side.",
        ("Until the incentive is confirmed, treat the FY2027 extended target as the working "
         "figure (BP + stretch), not a locked commercial commitment." if use_ext else
         "Until the incentive is confirmed, treat the FY2027 target as the working bridge "
         "(fleet × price × additional growth), not a locked commercial commitment."),
    ], Inches(0.32), Inches(5.55), Inches(12.7), Inches(1.05), size=12.5)
    page += 1

    # ---- Joint plan (meeting close — always; skip_next_steps was the old
    #      bullet summary and must not suppress this craft page) -------------
    s = db.build_content(
        prs,
        "End the customer meeting with clear workstreams and owners",
        eyebrow="Joint plan", page_no=page,
    )
    streams = []
    if shell_cat and abs(shell_cat.get("d") or 0) > 1000:
        streams.append((
            "Lubricants",
            "Close Shell price agreement; confirm restart timing and any temporary leakage.",
        ))
    if decliners:
        streams.append((
            "Service-parts pilot",
            f"Pick {decliners[0]['cat']} as the first joint recovery category.",
        ))
    streams.append((
        "SPA list",
        f"{S['name']} submits a target list; ISZE counters with network data and margin logic.",
    ))
    streams.append((
        "Sales-to-dealer data",
        "Monthly part-level data from 01/01/2025 to support factual targets and SPA.",
    ))
    if use_ext:
        streams.insert(0, (
            "FY2027 target",
            f"Confirm extended target {eur(ext_target)} and incentive status.",
        ))
    elif S.get("incentive_fy27") is None:
        streams.insert(0, (
            "FY2027 target",
            f"Align on the sales-to-dealer bridge — working figure {eur(s2d['fy27'])}.",
        ))
    streams = streams[:4]
    for i, (hdr, line) in enumerate(streams):
        card(
            s, Inches(0.32 + (i % 4) * 3.21), Inches(1.35), Inches(3.06), Inches(3.5),
            str(i + 1), hdr, [line],
        )
    db.txt(
        s,
        "Fewer slides in the room, clearer decisions, and a direct link between "
        f"{S['name']}'s asks and ISZE support.",
        Inches(0.32), Inches(5.15), Inches(12.7), Inches(0.55), size=13, color=BLACK,
    )
    page += 1

    db.build_closing(prs)

    # ---- Appendix: PN detail + process slides (not spoken by default) -----
    s = db.build_content(
        prs,
        "Appendix — detail behind the meeting story",
        eyebrow=f"{disp} · {S['name']}",
        page_no=page,
    )
    db.bullet_list(
        s,
        [
            "Part-number declines, growth deep dives, New Business validation, "
            "SPA process, R&M questions and the data request.",
            "Use selectively — the spoken meeting ends on the previous closing slide.",
        ],
        Inches(0.32), Inches(1.45), Inches(12.0), Inches(4.0), size=15,
    )
    page += 1

    for cat in decliners:
        drivers = (cat_pn.get(cat["cat"]) or {}).get("decl") or []
        if not drivers:
            drivers = [r for r in S.get("top_decl_itc") or [] if r["cat"] == cat["cat"]][:5]
        drivers = drivers[:4]
        cat_title = cat["cat"][0].upper() + cat["cat"][1:]
        s = db.build_content(
            prs, f"{cat_title} — {L26} vs {L25} (commercial, ex-warranty)",
            eyebrow=f"Appendix — {cat['cat']}", page_no=page,
        )
        bullets = [
            f"{eur(cat['prior'])} ({L25}) to {eur(cat['current'])} ({L26}), "
            f"down {eur(abs(cat['d']))}" + (f" ({cat['dp']:.0%})." if cat.get("dp") else ".")
        ]
        bullets.append("Largest part numbers driving the decline (by EUR):")
        for r in drivers:
            q = (
                f", {abs(r['dq']):,.0f} fewer pieces"
                if r.get("dq") is not None and r["dq"] < 0 else ""
            )
            model = f" · {r['model']}" if r.get("model") else ""
            bullets.append(
                f"{r['pn']} ({str(r.get('desc') or '')[:40]}{model}): "
                f"{eur(r['prior'])} to {eur(r['current'])}{q}."
            )
        db.bullet_list(s, bullets, Inches(0.32), Inches(1.32), Inches(12.7), Inches(2.9), size=13)
        db.txt(s, "Questions for us to work through together", Inches(0.32), Inches(4.20),
               Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
        db.bullet_list(
            s, QUESTIONS.get(cat["cat"], GENERIC_QUESTIONS),
            Inches(0.32), Inches(4.55), Inches(12.7), Inches(1.9), size=14,
        )
        page += 1

    for body in deep_dive_cats:
        cat_name = body["cat"]
        grow_b = (cat_pn.get(cat_name) or {}).get("grow") or []
        decl_b = (cat_pn.get(cat_name) or {}).get("decl") or []
        cat_title = cat_name[0].upper() + cat_name[1:]
        s = db.build_content(
            prs, f"{cat_title} — {L26} vs {L25} (commercial, ex-warranty)",
            eyebrow=f"Appendix — {cat_name}", page_no=page,
        )
        bullets = [
            f"{eur(body['prior'])} ({L25}) to {eur(body['current'])} ({L26}), "
            f"up {eur(body['d'])}"
            + (f" ({body['dp']:+.0%})." if body.get("dp") is not None else "."),
            "Largest part numbers driving the increase (by EUR):",
        ]
        for r in grow_b[:4]:
            q = (f", {r['dq']:+,.0f} pcs" if r.get("dq") is not None else "")
            bullets.append(
                f"{r['pn']} ({str(r.get('desc') or '')[:40]}): "
                f"{eur(r['prior'])} to {eur(r['current'])}{q}."
            )
        if decl_b:
            bullets.append(
                f"Largest {cat_name} declines: "
                + "; ".join(_fmt_pn_delta(r, 18) for r in decl_b[:2]) + "."
            )
        db.bullet_list(s, bullets, Inches(0.32), Inches(1.32), Inches(12.7), Inches(3.2), size=13)
        db.txt(s, "Questions for us to work through together", Inches(0.32), Inches(4.55),
               Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
        qs = (
            BODY_GROWTH_Q if cat_name == "Body parts"
            else QUESTIONS.get(cat_name, GENERIC_QUESTIONS)
        )
        db.bullet_list(s, qs, Inches(0.32), Inches(4.90), Inches(12.7), Inches(1.6), size=14)
        page += 1

    if new_biz and not deck_opt.get("skip_new_business"):
        s = db.build_content(
            prs, f"New Business — validation queue ({L26})",
            eyebrow="Appendix", page_no=page,
        )
        nb = new_biz[:6]
        rows = [["Part", "Description", "Current sales", "Review"]]
        rows += [
            [
                x["pn"], str(x["desc"])[:31], eur(x["current"]),
                "Warranty / campaign" if x.get("warranty_campaign") else "Validate",
            ]
            for x in nb
        ]
        styled_table(
            s, rows, Inches(0.32), Inches(1.32), Inches(12.7), Inches(2.8),
            [Inches(2.4), Inches(4.4), Inches(2.4), Inches(3.5)],
            bold_last=False, size=11.5, left_cols=(0, 1, 3),
        )
        db.bullet_list(
            s,
            [
                "These lines had no prior-period sales, so they are kept out of the "
                "incremental-growth table.",
                "A first sale can be a new model, a supersession, timing, or a warranty "
                "campaign. It is not treated as a commercial win until that cause is confirmed.",
            ],
            Inches(0.32), Inches(4.45), Inches(12.7), Inches(1.5), size=14,
        )
        page += 1

    s = db.build_content(prs, "SPA", eyebrow="Appendix — SPA", page_no=page)
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

    s = db.build_content(prs, "R&M — let's align on the market", eyebrow="Appendix — R&M",
                         page_no=page)
    card(s, Inches(0.32), Inches(1.30), Inches(6.0), Inches(4.4), "M", "Market",
         ["How is the market moving for you right now?",
          "How much of your volume is fleet business rather than retail?",
          "Where do you see the biggest hurdles this year?",
          "Where are your real strengths in this segment?"])
    card(s, Inches(6.5), Inches(1.30), Inches(6.5), Inches(4.4), "S", "Servicing & R&M",
         ["Do you offer an R&M or service-plan product today?",
          "What share of the trucks in service do you retain for servicing after year three?",
          "Does R&M business come bundled with fleet tenders — roughly what share?",
          "What would it take to bring more out-of-network servicing back?"])
    page += 1

    has_s2d = not s2d["s2d_imputed"]
    s = db.build_content(
        prs, "Part-level sales-to-dealer data", eyebrow="Appendix — Ask", page_no=page,
    )
    first = (
        "You already report sales to dealer monthly. The ask is the same data at "
        "part-number level." if has_s2d else
        "We have no sales-to-dealer figures from you for FY2026. The ask is monthly "
        "sales to dealer, at part-number level."
    )
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

    import os
    from datetime import datetime, timezone
    preferred = os.environ.get("ISZE_DECK_OUT") or str(
        out_dir / f"ISZE_{p['key']}_Sales_Review_FY2027.pptx"
    )
    candidates = [preferred]
    stem = Path(preferred)
    candidates += [
        str(stem.with_name(stem.stem + "_share.pptx")),
        str(stem.with_name(
            stem.stem + f"_rebuild_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.pptx"
        )),
    ]
    # de-dupe while preserving order
    seen, out = set(), None
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        try:
            prs.save(cand)
            out = cand
            if cand != preferred:
                print(f"[{p['key']}] (preferred PPTX locked — wrote → {Path(cand).name})")
            break
        except (PermissionError, OSError) as exc:
            print(f"[{p['key']}] save failed {Path(cand).name}: {exc}")
            continue
    if out is None:
        raise SystemExit(f"[{p['key']}] cannot save PPTX — all candidates locked: {candidates}")
    print(f"[{p['key']}] saved {out}   ({len(prs.slides)} slides)")
    if gps:
        g = gps["gps_FY2026"]
        gtxt = f"{g*100:.1f}%" if gps["show_pct"] else "amount-only (>100%)"
        print(f"  GPS FY2026: {gtxt}  "
              f"(net {gps['net_FY2026']:,.0f} / target spend CY2025 {gps['wallet_2025']:,.0f}; "
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
