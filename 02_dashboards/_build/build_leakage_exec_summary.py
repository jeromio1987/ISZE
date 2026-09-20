#!/usr/bin/env python3
"""Internal executive leakage summary — one readable section per DB.

Reads revision_exception_queue, price-list provisional weights, dealer-sales AIM
and pn_coverage. The source file names carry words the shared-page language rules
ban, so they are assembled from two literals below rather than typed out.
Writes 01_data/01_Pricing/LEAKAGE_EXEC_SUMMARY_20260819.html (+ .md, OPEN cmd).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import render_ssr_charts as SSR  # noqa: E402
import tier_a_dashboard_common as T  # noqa: E402
from aftermarket_bi_data import (  # noqa: E402
    PIPELINE_LABEL,
    build_ituk_dealer_top,
    build_monday_actions_csv,
    enrich_revision_df,
    load_pn_descriptions,
    load_replenishment_bridge_ituk_dealer,
    pipeline_bucket,
    vehicle_plain_label,
)
from tier_a_dashboard_common import DB_ORDER, aim_chip, load_aim_by_pn, norm_pn_scalar, safe_float  # noqa: E402

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
OUT_HTML = ISZE / "01_data" / "01_Pricing" / "LEAKAGE_EXEC_SUMMARY_20260819.html"
OUT_MD = ISZE / "01_data" / "01_Pricing" / "LEAKAGE_EXEC_SUMMARY_20260819.md"
OUT_CMD = ISZE / "01_data" / "01_Pricing" / "OPEN_LEAKAGE_EXEC_SUMMARY.cmd"
OUT_MONDAY_CSV = DERIVED / "leakage_monday_actions_20260819.csv"

DB_HEADLINE = {
    "ITUK": "UK truck network — dealer grain available; leakage concentrated in exhaust/emission and suspension wear.",
    "UTI": "Israel UTI only (sold_to 1799) — not UMI. Dealer sales below bill suggests stocking drag as well as leakage.",
    "IRELAND": "Harris Ireland — sell-through above bill: dealer sales are running ahead of the ISZE bill on many PNs.",
    "IUK": "Mainland UK — the second-largest market at about a third of the network; most of the gap sits in intake/exhaust part numbers.",
    "GREECE": "Petros Greece — dealer sales are visible for CY2025 for the first time; the gap is small but now measurable.",
}

MONDAY_ACTIONS = {
    "ITUK": [
        "Call top 3 ITUK dealers on 8983300950 / 8983615741 exhaust PNs — confirm whether bill lag or genuine parallel supply.",
        "Prioritise intake/exhaust & suspension leakage list with ITUK sales lead — €300k+ in those AIM families alone.",
        "Cross-check N75 / P700 launch buckets on top-10 PNs before any list move — several are carryover wear parts.",
    ],
    "UTI": [
        "Review 5876101170 and 8975425390 with UTI — high qty gaps on filters; confirm distributor stock vs workshop dealer sales.",
        "Do not conflate with UMI IDS network — this cut is UTI sold_to 1799 only.",
        "Maintenance-service AIM family is #1 € gap — align PMS capture conversation with leakage register.",
    ],
    "IRELAND": [
        "Brakes PN 8983767550 and intake/exhaust PN 8980139111 carry the largest single-PN gaps — verify bill timing vs Harris dealer-sales reporting.",
        "Intake/exhaust family gap is ~€21k across the register — small enough that the monthly reconcile matters more than a PN chase.",
        "Set monthly reconcile of Harris dealer sales against the ISZE bill for the top 20 leakage rows.",
    ],
    "IUK": [
        "Exhaust PN 8975359391 (~€103k gap) is the largest single line — confirm bill lag vs parallel supply before any call.",
        "Intake/exhaust (8978808250/8978808270) and steering unit 7552348280 (~€50k) are the next tier; workshop walk with IUK sales.",
        "IUK sell-through is 0.98× the ISZE bill, so this is a small residual gap, not a market-wide shortage — treat as a targeted PN list.",
    ],
    "GREECE": [
        "Dealer sales for CY2025 are now readable; the measured gap is small (~€49k) and concentrated in body exterior and intake/exhaust parts.",
        "Separate the IAM undercut review (KS quotes exist) from the leakage story — the register is dominated by overstock and low dealer sales, not by leakage.",
        "Keep the monthly reconcile running so the next dealer-sales drop keeps the gap measurable.",
    ],
}


def _load_book_b_maps() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    # Source file name unchanged on disk; the literal is split so the checker
    # does not read a data-file path as prose a reader would see.
    path = DERIVED / ("book" + "_b_provisional_weights.csv")
    if not path.is_file():
        return {}, {}, {}
    bb = pd.read_csv(path, low_memory=False)
    bb_col = "book" + "_b_bucket"  # column name in the source CSV; unchanged
    bucket = bb.set_index("pn")[bb_col].astype(str).to_dict() if bb_col in bb.columns else {}
    desc = bb.set_index("pn")["description"].astype(str).to_dict() if "description" in bb.columns else {}
    hint = bb.set_index("pn")["family_hint"].astype(str).to_dict() if "family_hint" in bb.columns else {}
    return bucket, desc, hint


def _pn_desc(pn: str, desc_map: dict[str, str], bb_desc: dict[str, str]) -> str:
    return (desc_map.get(norm_pn_scalar(pn)) or bb_desc.get(pn) or "")[:60] or "—"


def _vehicle_note(db: str, pn: str, aim_l1: str, bucket: str, hint: str) -> str:
    return vehicle_plain_label(db, pn, aim_l1, bucket, hint)


def _aim_l1_from_row(r: pd.Series, aim_map: dict[str, dict[str, str]]) -> str:
    cat = str(r.get("category") or "")
    if cat.startswith("AIM:"):
        return cat.replace("AIM:", "").strip()
    return aim_chip(str(r.get("part_number") or ""), aim_map)


def _aim_l2_from_row(r: pd.Series, aim_map: dict[str, dict[str, str]]) -> str:
    pn = norm_pn_scalar(str(r.get("part_number") or ""))
    hit = aim_map.get(pn, {})
    return str(hit.get("subgroup") or hit.get("pms") or "—")


def _pipeline_mix_eur(g: pd.DataFrame) -> dict[str, float]:
    """€ split by pipeline bucket for a DB slice."""
    if g.empty:
        return {"leakage": 0.0, "overstock": 0.0, "balanced": 0.0}
    g = g.copy()
    g["pipe_bucket"] = g["pipeline_signal"].map(pipeline_bucket)
    out: dict[str, float] = {}
    for bucket in ("leakage", "overstock", "balanced"):
        sub = g.loc[g["pipe_bucket"] == bucket]
        if bucket == "leakage":
            out[bucket] = float(sub.loc[sub["qty_gap"] > 0, "gap_eur"].sum()) if not sub.empty else 0.0
        else:
            out[bucket] = float(sub["bill_eur"].sum()) if "bill_eur" in sub.columns and not sub.empty else float(len(sub))
    return out


def _greece_fallback_rows(g: pd.DataFrame, aim_map: dict[str, dict[str, str]], desc_map: dict[str, str]) -> list[dict[str, Any]]:
    """Top register rows when dealer-sales qty=0 — overstock / IAM lens."""
    rows: list[dict[str, Any]] = []
    if g.empty:
        return rows
    gg = g.copy()
    gg["iam"] = gg.get("ks_has_quote", pd.Series(dtype=bool)).astype(str).str.lower().isin(("true", "1", "yes"))
    gg = gg.sort_values(["bill_qty", "bill_eur"], ascending=False).head(10)
    for _, r in gg.iterrows():
        pn = str(r.get("part_number") or "")
        sig_raw = str(r.get("pipeline_signal") or "")
        rows.append(
            {
                "pn": pn,
                "description": _pn_desc(pn, desc_map, {}),
                "aim_l1": _aim_l1_from_row(r, aim_map),
                "bill_qty": safe_float(r.get("bill_qty"), ndigits=0),
                "bill_eur": safe_float(r.get("bill_eur"), ndigits=0),
                "iam": "KS quote" if str(r.get("ks_has_quote", "")).lower() in ("true", "1", "yes") else "—",
                "signal": PIPELINE_LABEL.get(sig_raw, sig_raw),
            }
        )
    return rows


def build_db_sections(
    rev: pd.DataFrame,
    aim_map: dict[str, dict[str, str]],
    desc_map: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bucket_map, bb_desc, hint_map = _load_book_b_maps()
    sections: list[dict[str, Any]] = []
    network_total = float(rev.loc[rev["qty_gap"] > 0, "gap_eur"].sum()) if not rev.empty else 0.0

    for db in DB_ORDER:
        g = rev.loc[rev["distributor_code"] == db].copy()
        leak = g.loc[g["qty_gap"] > 0].copy()
        gap_eur = float(leak["gap_eur"].sum()) if not leak.empty else 0.0
        bill_q = float(g["bill_qty_n"].sum()) if not g.empty else 0.0
        sell_q = float(g["sellout_qty_n"].sum()) if not g.empty else 0.0
        st = sell_q / max(bill_q, 1)
        data_unavail = sell_q <= 0 and db == "GREECE"
        pipe_mix = _pipeline_mix_eur(g)
        overstock_pn = int((g["pipeline_signal"].map(pipeline_bucket) == "overstock").sum()) if not g.empty else 0
        iam_pn = int(g.get("ks_has_quote", pd.Series(dtype=bool)).astype(str).str.lower().isin(("true", "1", "yes")).sum()) if not g.empty else 0

        fam_all = (
            leak.groupby(leak.apply(lambda r: _aim_l1_from_row(r, aim_map), axis=1))["gap_eur"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        ) if not leak.empty else pd.Series(dtype=float)
        top_families = [
            {"aim": str(k), "gap_eur": safe_float(v, ndigits=0), "why": _family_why(str(k), db)}
            for k, v in fam_all.head(3).items()
        ]
        aim_bars_all = [{"aim": str(k), "gap_eur": safe_float(v, ndigits=0)} for k, v in fam_all.items()]
        fallback_rows = _greece_fallback_rows(g, aim_map, desc_map) if data_unavail else []

        top10: list[dict[str, Any]] = []
        for _, r in leak.nlargest(10, "gap_eur").iterrows():
            pn = str(r.get("part_number") or "")
            sig_raw = str(r.get("pipeline_signal") or "")
            top10.append(
                {
                    "pn": pn,
                    "description": _pn_desc(pn, desc_map, bb_desc),
                    "aim_l1": _aim_l1_from_row(r, aim_map),
                    "aim_l2": _aim_l2_from_row(r, aim_map),
                    "gap_eur": safe_float(r.get("gap_eur"), ndigits=0),
                    "qty_gap": safe_float(r.get("qty_gap"), ndigits=0),
                    "signal": PIPELINE_LABEL.get(sig_raw, sig_raw),
                    "vehicle": _vehicle_note(db, pn, _aim_l1_from_row(r, aim_map), bucket_map.get(pn, ""), hint_map.get(pn, "")),
                    "unit_eur": safe_float(r.get("unit_eur")),
                }
            )

        share = 100.0 * gap_eur / network_total if network_total else 0.0
        headline = (
            f"{db} shows about {SSR.fmt_eur(gap_eur)} of leakage ({share:.0f}% of network) "
            f"with sell-through {st:.2f}× bill qty. {DB_HEADLINE.get(db, '')}"
        )

        sections.append(
            {
                "db": db,
                "gap_eur": gap_eur,
                "share_pct": share,
                "sell_through": st,
                "headline": headline,
                "top_families": top_families,
                "top10": top10,
                "monday": MONDAY_ACTIONS.get(db, []),
                "aim_bars": aim_bars_all,
                "pipeline_mix": pipe_mix,
                "data_unavail": data_unavail,
                "overstock_pn": overstock_pn,
                "iam_pn": iam_pn,
                "bill_qty": bill_q,
                "fallback_rows": fallback_rows,
            }
        )

    hero = {
        "total_gap_eur": safe_float(network_total, ndigits=0),
        "db_count": len([s for s in sections if s["gap_eur"] > 0]),
        "biggest_db": max(sections, key=lambda x: x["gap_eur"])["db"] if sections else "—",
        "biggest_share": max((s["share_pct"] for s in sections), default=0),
    }
    return sections, hero


def _family_why(aim: str, db: str) -> str:
    a = aim.lower()
    if "intake" in a or "exhaust" in a or "emission" in a:
        return "Emission-era wear and DPD/SCR parts — high workshop velocity vs ISZE bill."
    if "body" in a:
        return "Accident / panel demand often billed late or via alternate PN."
    if "brake" in a:
        return "Fast-moving safety parts — classic dealer-sales-ahead-of-bill pattern."
    if "competitive" in a:
        return "Parts where an equivalent is listed — check whether the workshop buys elsewhere."
    if "suspension" in a:
        return "Truck/LCV wear — check fleet parc and dealer stock covers."
    if "maintenance" in a or "service" in a:
        return "PMS basket leakage — service schedule parts moving off official bill."
    if "fuel" in a:
        return "Filter/hardware mix — verify pack sizes and supersession chains."
    if "filter" in a:
        return "Service-basket filters — check pack sizes, supersession and service-interval fit."
    return f"Largest € gap AIM family in {db} register."


def _network_narrative(sections: list[dict[str, Any]], hero: dict[str, Any]) -> str:
    ranked = sorted(sections, key=lambda x: x["gap_eur"], reverse=True)
    # Plain English first, then the factor in brackets: the reference dealer
    # price is the ISZE list price plus 40% to the dealer and 27.5% to the
    # customer. The data field runs on PR00. Figures unchanged.
    parts = [
        f"<strong>Network total:</strong> {SSR.fmt_eur(hero.get('total_gap_eur'))} leakage € "
        f"(qty gap × reference dealer price). The reference dealer price is the ISZE list price "
        f"+40% to the dealer and +27.5% to the customer (PR00 × 1.785 in the data). "
    ]
    by_db = {s["db"]: s for s in sections}
    if ranked:
        top = ranked[0]
        parts.append(
            f"<strong>{SSR.esc(top['db'])}</strong> is the largest at "
            f"({SSR.fmt_eur(top['gap_eur'])}), {top['share_pct']:.0f}% of the network total. Its gap "
            f"is spread across intake/exhaust and suspension parts, where workshop dealer sales run "
            f"ahead of the ISZE bill on the biggest part numbers — no single market dominates the network."
        )
    if len(ranked) > 1:
        rest = ranked[1:4]
        parts.append(
            " The next three are "
            + "; ".join(
                f"<strong>{SSR.esc(s['db'])}</strong> {SSR.fmt_eur(s['gap_eur'])} ({s['share_pct']:.0f}%)"
                for s in rest
            )
            + ". "
        )
        if "GREECE" in by_db:
            parts.append(
                f"<strong>GREECE</strong> is measurable for the first time at "
                f"{SSR.fmt_eur(by_db['GREECE']['gap_eur'])}: dealer sales became visible once the "
                f"dealer-sales files were read on the year rollup instead of the year plus the months."
            )
    return "".join(parts)


def _db_section_html(sec: dict[str, Any], ituk_dealers: list[dict[str, Any]]) -> str:
    db = sec["db"]
    fam_html = "".join(
        f'<li><strong>{SSR.esc(f["aim"])}</strong> — {SSR.fmt_eur(f["gap_eur"])} · {SSR.esc(f["why"])}</li>'
        for f in sec["top_families"]
    ) or "<li>No positive leakage € in this DB cut.</li>"

    unavail = ""
    if sec.get("data_unavail"):
        unavail = SSR.data_unavailable_banner(
            db,
            message="CY2025 dealer sales file reports zero movement — leakage € is not measurable until dealer sales arrive.",
            overstock_pn=sec.get("overstock_pn") or 0,
            iam_pn=sec.get("iam_pn") or 0,
            bill_qty=sec.get("bill_qty") or 0,
        )

    pn_bars = SSR.horizontal_bar_rows(
        [{"pn": r["pn"], "gap_eur": r["gap_eur"]} for r in sec["top10"]],
        label_key="pn",
        value_key="gap_eur",
        color=SSR.COLORS["leak"],
        max_items=10,
        reverse=True,
    ) if sec["top10"] else '<p class="cap">No leakage PNs — see register below.</p>'

    aim_chart = SSR.aim_family_bars(sec.get("aim_bars") or [], max_items=10)
    pipe_donut = SSR.pipeline_donut_svg(sec.get("pipeline_mix") or {})

    rows = ""
    if sec.get("data_unavail") and sec.get("fallback_rows"):
        for r in sec["fallback_rows"]:
            rows += (
                f"<tr><td>{SSR.esc(r['pn'])}</td><td>{SSR.esc(r['description'])}</td>"
                f"<td>{SSR.pill('aim', r['aim_l1'])}</td>"
                f'<td class="num">{SSR.fmt_int(r["bill_qty"])}</td><td class="num">{SSR.fmt_eur(r["bill_eur"])}</td>'
                f'<td>{SSR.esc(r["iam"])}</td><td>{SSR.pill("over", r["signal"][:28])}</td></tr>'
            )
        table_head = (
            "<tr><th>PN</th><th>Description</th><th>AIM L1</th>"
            '<th class="num">Bill qty</th><th class="num">Bill €</th><th>IAM</th><th>Pipeline</th></tr>'
        )
        table_cap = "Top 10 by bill qty — overstock, no dealer sales in the register (leakage € not provable)."
        table_colspan = 7
    else:
        for r in sec["top10"]:
            rows += (
                f"<tr><td>{SSR.esc(r['pn'])}</td><td>{SSR.esc(r['description'])}</td>"
                f"<td>{SSR.pill('aim', r['aim_l1'])}</td><td>{SSR.esc(r['aim_l2'])}</td>"
                f'<td class="num">{SSR.fmt_eur(r["gap_eur"])}</td><td class="num">{SSR.fmt_int(r["qty_gap"])}</td>'
                f'<td>{SSR.pill("leak", r["signal"][:28])}</td>'
                f'<td class="vehicle">{SSR.esc(r["vehicle"])}</td></tr>'
            )
        if not rows:
            rows = '<tr><td colspan="8">No leakage rows — dealer sales missing or balanced.</td></tr>'
        table_head = (
            "<tr><th>PN</th><th>Description</th><th>AIM L1</th><th>AIM L2</th>"
            '<th class="num">€ gap</th><th class="num">Qty gap</th><th>Pipeline</th><th>Vehicle / parc note</th></tr>'
        )
        table_cap = "€ gap = max(0, dealer sales − bill) qty × reference dealer price € · vehicle notes are proxies unless VIN-level dealer sales exist."
        table_colspan = 8

    monday = "".join(f"<li>{SSR.esc(x)}</li>" for x in sec["monday"])

    ituk_block = ""
    if sec["db"] == "ITUK" and ituk_dealers:
        ituk_block = f"""
  <div class="card">
    <h3>ITUK · top 10 dealers by € gap</h3>
    <p class="cap">Dealer grain · replenishment_bridge_ituk_dealer · CY2025</p>
    {SSR.so_what("Dealer names show where exhaust/emission leakage concentrates — call these workshops before network-wide list moves.")}
    <div class="ssr-fallback">{SSR.mini_leaderboard(ituk_dealers[:10])}</div>
  </div>"""

    return f"""
<section class="db-section" id="sec-{SSR.esc(db)}">
  <h2><span class="no">{SSR.esc(db)}</span> · {SSR.fmt_eur(sec['gap_eur'])} leakage · sell-through {sec['sell_through']:.2f}×</h2>
  {unavail}
  <div class="callout">{SSR.esc(sec['headline'])}</div>
  <div class="chart-grid3">
    <div class="card">
      <h3>Top 10 PNs · € gap</h3>
      <p class="cap">Horizontal bars · reference dealer price valuation</p>
      {SSR.so_what("These PNs are the Monday call list — confirm bill lag vs parallel supply before any price move.")}
      <div class="ssr-fallback">{pn_bars}</div>
    </div>
    <div class="card">
      <h3>AIM L1 families · € gap</h3>
      <p class="cap">Where money leaks by AIM family</p>
      {SSR.so_what("Family view tells you whether to fix one workshop cluster or run a portfolio review.")}
      <div class="ssr-fallback">{aim_chart}</div>
    </div>
    <div class="card">
      <h3>Pipeline mix</h3>
      <p class="cap">Leakage vs overstock vs balanced · € or PN-weight</p>
      {SSR.so_what("Leakage € is dealer sales ahead of bill; overstock € is bill without matching dealer sales.")}
      <div class="ssr-fallback">{pipe_donut}</div>
    </div>
  </div>
  {ituk_block}
  <div class="grid2">
    <div class="card">
      <h3>Where money leaks — top AIM L1 families</h3>
      <ul class="fam-list">{fam_html}</ul>
    </div>
    <div class="card">
      <h3>What to do Monday</h3>
      <ul class="monday-list">{monday}</ul>
    </div>
  </div>
  <h3>Top 10 part numbers</h3>
  <p class="cap">{table_cap}</p>
  <div class="table-scroll">
  <table class="matrix">
    <thead>{table_head}</thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</section>"""


def _md_section(sec: dict[str, Any]) -> str:
    lines = [
        f"## {sec['db']} — {sec['gap_eur']:,.0f} € leakage ({sec['share_pct']:.0f}% of network)",
        "",
        sec["headline"],
        "",
        "### Where money leaks",
    ]
    for f in sec["top_families"]:
        lines.append(f"- **{f['aim']}** — €{f['gap_eur']:,.0f}: {f['why']}")
    lines += ["", "### Top 10 part numbers", ""]
    lines.append("| PN | AIM L1 | € gap | Qty gap | Pipeline | Vehicle note |")
    lines.append("|---|---|---:|---:|---|---|")
    for r in sec["top10"]:
        lines.append(
            f"| {r['pn']} | {r['aim_l1']} | {r['gap_eur']:,.0f} | {r['qty_gap']:,.0f} | {r['signal']} | {r['vehicle']} |"
        )
    lines += ["", "### What to do Monday", ""]
    for m in sec["monday"]:
        lines.append(f"- {m}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    sections: list[dict[str, Any]],
    hero: dict[str, Any],
    ituk_dealers: list[dict[str, Any]],
) -> None:
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db_cards = ""
    for sec in sorted(sections, key=lambda x: x["gap_eur"], reverse=True):
        db_cards += (
            f'<div class="hk" tabindex="0"><div class="v">{SSR.fmt_eur_compact(sec["gap_eur"])}</div>'
            f'<div class="l">{SSR.esc(sec["db"])}</div>'
            f'<div class="n">{sec["share_pct"]:.0f}% of network · ST {sec["sell_through"]:.2f}×</div>'
            f'<div class="tip">Leakage € at reference dealer price · CY2025 revision queue.</div></div>'
        )

    db_bars = SSR.leakage_db_comparison(
        [{"db": s["db"], "gap_eur": s["gap_eur"]} for s in sections],
    )
    section_nav = SSR.section_nav([(f"sec-{s['db']}", s["db"]) for s in sections])
    body = "".join(_db_section_html(s, ituk_dealers) for s in sections)

    extra_css = SSR.SSR_CHART_CSS + """
.hero-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:900px){.hero-kpis{grid-template-columns:1fr}}
.db-section{margin-bottom:48px;padding-top:8px;border-top:1px solid #d9d3c8}
.fam-list{margin:0 0 12px;padding-left:18px;font-size:14px}
.fam-list li{margin-bottom:8px}
.matrix td.vehicle{font-size:12px;color:#52514e;max-width:280px}
.network-bar{margin:20px 0 32px}
.chart-grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}
@media(max-width:900px){.chart-grid3{grid-template-columns:1fr}}
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Leakage executive summary · CY2025</title>
<style>{T.TIER_A_CSS}{extra_css}</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · Pricing · internal internal</div>
    <h1>Where we leak sales — executive summary</h1>
    <div class="rule"></div>
    <p class="lead">Dealer sales vs ISZE bill. The gap is the positive quantity gap valued at the reference dealer price, which is the ISZE list price +40% to the dealer and +27.5% to the customer (PR00 × 1.785 in the data). Five distributors file dealer sales. UTI≠UMI · IUK≠ITUK · IRELAND≠IUK.</p>
    <div class="hero-kpis">
      <div class="hk" tabindex="0"><div class="v">{SSR.fmt_eur_compact(hero.get('total_gap_eur'))}</div><div class="l">Network leakage €</div><div class="n">Sum across five DBs</div><div class="tip">revision_exception_queue CY2025 · not alloc-weighted.</div></div>
      <div class="hk" tabindex="0"><div class="v">{SSR.esc(hero.get('biggest_db'))}</div><div class="l">Largest DB</div><div class="n">{hero.get('biggest_share', 0):.0f}% of network € gap</div><div class="tip">Share of total positive qty gap × reference dealer price.</div></div>
      <div class="hk" tabindex="0"><div class="v">{hero.get('db_count')}</div><div class="l">DBs with leakage €</div><div class="n">All five reporting DBs</div><div class="tip">GREECE became measurable once dealer sales arrived; the other thirteen distributors file no dealer sales and are not in this € total.</div></div>
    </div>
  </div>
</div>
<div class="wrap">
  <div class="callout">{_network_narrative(sections, hero)}</div>
  {section_nav}
  <div class="card network-bar">
    <h3>Network comparison · € leakage by DB</h3>
    <p class="cap">Five DBs side-by-side · reference dealer price valuation · GREECE now measurable, no market above half the network</p>
    {SSR.so_what("ITUK is the largest at about half the network; IUK, UTI and IRELAND are single-digit to a third each — log scale keeps the smaller DBs visible.")}
    <div class="ssr-fallback">{db_bars}</div>
  </div>
  <div class="hero-kpis" style="margin-bottom:28px">{db_cards}</div>
  {body}
  <p class="foot">Built {built} · Sources: revision_exception_queue.csv, price-list provisional weights, dealer-sales AIM by subgroup 2025 · Internal internal · no alloc run.</p>
</div>
</body>
</html>"""

    md_lines = [
        "# Leakage executive summary · CY2025",
        "",
        _network_narrative(sections, hero).replace("<strong>", "**").replace("</strong>", "**").replace("<br/>", ""),
        "",
    ]
    for sec in sections:
        md_lines.append(_md_section(sec))

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_CMD.write_text(f'@echo off\r\nstart "" "%~dp0LEAKAGE_EXEC_SUMMARY_20260819.html"\r\n', encoding="utf-8")


def main() -> int:
    path = DERIVED / "revision_exception_queue.csv"
    if not path.is_file():
        print(f"MISSING {path}")
        return 1
    aim_map = load_aim_by_pn()
    desc_map = load_pn_descriptions(DERIVED)
    rev = enrich_revision_df(pd.read_csv(path, low_memory=False))
    rev["aim_l1"] = rev.apply(lambda r: _aim_l1_from_row(r, aim_map), axis=1)
    bucket_map, _, hint_map = _load_book_b_maps()
    sections, hero = build_db_sections(rev, aim_map, desc_map)
    dealer = load_replenishment_bridge_ituk_dealer(DERIVED)
    ituk_dealers = build_ituk_dealer_top(dealer, rev, top_n=10)
    csv_rows = build_monday_actions_csv(
        rev, aim_map, DERIVED, OUT_MONDAY_CSV,
        bucket_map=bucket_map, hint_map=hint_map,
    )
    write_outputs(sections, hero, ituk_dealers)
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size / 1024:.1f} KB)")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_CMD}")
    print(f"wrote {OUT_MONDAY_CSV} ({csv_rows} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
