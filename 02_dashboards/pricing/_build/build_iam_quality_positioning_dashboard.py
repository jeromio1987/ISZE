#!/usr/bin/env python
"""Build ISZE vs IAM quality-positioning dashboards (internal).

All proposed prices, bands, actions, and the ISZE→DB→DLR→retail chain are
computed in position_engine.py. This file only renders.

    python build_iam_quality_positioning_dashboard.py
    python build_iam_quality_positioning_dashboard.py --db UMI
    python build_iam_quality_positioning_dashboard.py --db ITUK
    python build_iam_quality_positioning_dashboard.py --db ISD
    python build_iam_quality_positioning_dashboard.py --db IMOTORS
    python build_iam_quality_positioning_dashboard.py --all

Does not overwrite:
  UMI_Operating_Dashboard.html
  UMI_SPA_Proposed_Prices.html
  ISZE_Pricing_Engine_Readiness_Dashboard.html
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(ISZE / "04_tools" / "autodoc_scraper"))

from position_engine import (  # noqa: E402
    DB_REGISTRY,
    resolve_db,
    score_db,
)

HERE = Path(__file__).resolve().parent
UI = ISZE / "02_dashboards" / "_ui"
OUT_DIR = ISZE / "02_dashboards" / "pricing"
TPL = HERE / "_iam_quality_template.html"
OV_TPL = HERE / "_iam_quality_overview_template.html"
SPA_REL = "../spa_internal/UMI_SPA_Proposed_Prices.html"

# Output stems. Registry key GERMANY → ISD file; PORTUGAL → IMOTORS file.
FILE_STEM = {
    "UMI": "ISZE_IAM_Quality_Positioning_Engine",
    "ITUK": "ISZE_IAM_Quality_Positioning_Engine_ITUK",
    "GERMANY": "ISZE_IAM_Quality_Positioning_Engine_ISD",
    "PORTUGAL": "ISZE_IAM_Quality_Positioning_Engine_IMOTORS",
}
BUILD_ORDER = ["UMI", "ITUK", "GERMANY", "PORTUGAL"]
OV_STEM = "ISZE_IAM_Quality_Positioning_Overview"


def esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def chart_js_inline() -> str:
    raw = (UI / "chart.umd.min.js").read_text(encoding="utf-8")
    return "\n".join(ln for ln in raw.splitlines() if "sourceMappingURL" not in ln)


def write_cmd(html_path: Path) -> Path:
    cmd = html_path.with_name(f"OPEN_{html_path.stem}.cmd")
    cmd.write_text(f'@echo off\nstart "" "%~dp0{html_path.name}"\n', encoding="ascii")
    return cmd


def sibling_nav(active_key: str | None) -> str:
    links = [('ISZE_IAM_Quality_Positioning_Overview.html', 'Overview', None)]
    for k in BUILD_ORDER:
        stem = FILE_STEM[k]
        short = DB_REGISTRY[k]["short"]
        links.append((f"{stem}.html", short, k))
    parts = []
    for href, label, key in links:
        cls = "on" if key == active_key or (active_key is None and label == "Overview") else ""
        parts.append(f'<a class="{cls}" href="{href}">{esc(label)}</a>')
    return "".join(parts)


def kpi_html(payload: dict) -> str:
    parts = []
    for k in payload["kpis"]:
        parts.append(
            '<div class="kpi" tabindex="0" data-tip="'
            + esc(k["tip"])
            + '"><div class="lbl">'
            + esc(k["label"])
            + '</div><div class="val">'
            + esc(k["value"])
            + '</div><div class="sub">'
            + esc(k["sub"])
            + "</div></div>"
        )
    return "".join(parts)


def margin_chips_html(ch: dict) -> str:
    db_tip = (
        f"DB sell = ISZE net (PR00) × {ch['db_factor']:.2f} "
        f"(+{ch['db_markup_pct']:.0f}% markup, not gross margin). "
        f"Source: {ch['source_file']} (channel factor 1.40 × 1.275 = 1.785). "
        f"Snapshot: {ch['source_as_of']}. "
        f"{ch['origin']}: already in local files — not an invented 20/25/30. "
        "Working channel rule, not observed SPA terms. Distributors set their own resale."
    )
    dlr_tip = (
        f"DLR sell = DB sell × {ch['dlr_factor']:.3f} "
        f"(+{ch['dlr_markup_pct']:.1f}% markup on DB). "
        f"Projected retail = DLR sell (no extra retail markup in local files). "
        f"Combined ISZE net × {ch['combined_factor']:.3f}. "
        f"Source: {ch['source_file']}. Snapshot: {ch['source_as_of']}. "
        f"Cross-check: {ch['cross_check']}. "
        "Not the iam_scoring.py 37/25 GM divide."
    )
    origin = "From local files" if ch["origin"] == "local_file" else "ASSUMPTION — edit in position_engine.py"
    return (
        '<div class="margrow">'
        '<div class="kpi chipbox" tabindex="0" data-tip="' + esc(db_tip) + '">'
        '<div class="lbl">DB margin used</div>'
        f'<div class="val">+{ch["db_markup_pct"]:.0f}%</div>'
        f'<div class="sub">markup ×{ch["db_factor"]:.2f} · {esc(origin)}</div>'
        "</div>"
        '<div class="kpi chipbox" tabindex="0" data-tip="' + esc(dlr_tip) + '">'
        '<div class="lbl">DLR margin used</div>'
        f'<div class="val">+{ch["dlr_markup_pct"]:.1f}%</div>'
        f'<div class="sub">markup ×{ch["dlr_factor"]:.3f} · {esc(origin)}</div>'
        "</div>"
        "</div>"
    )


def conclusion_items_html(concl: dict) -> str:
    return "".join(f"<li>{esc(b)}</li>" for b in concl.get("bullets") or [])


def pad_capture_txt(payload: dict) -> str:
    short = payload["meta"]["db_short"]
    pad = next((x for x in payload.get("pms_capture") or [] if x.get("cat") == "brake_pad"), None)
    if pad and pad.get("capture_pct") is not None:
        return (
            f"{short} genuine pad capture is {pad['capture_pct']:.1f}% (PMS total, CY{payload['meta']['cy']}). "
            "Filters are not the same fight. Tightness multiplies the T3/T4 ceiling only. "
            "Lighting and body keep the full ladder — we do not invent a pad-style haircut there."
        )
    return (
        f"{short} pad capture is not in the PMS extract. Tightness still multiplies T3/T4 only. "
        "Lighting and body keep the full ladder."
    )


def build_payload(db_key: str) -> dict:
    d = score_db(db_key)
    m = d["meta"]
    short = m["db_short"]
    d["meta"]["as_of"] = date.today().isoformat()
    d["meta"]["title"] = f"ISZE vs IAM — quality positioning engine · {short}"
    d["meta"]["audience"] = "internal"
    rows = d["rows"]
    hero = max(rows, key=lambda r: (r.get("book_cy2025_eur") or r.get("umi_cy2025_eur") or 0)) if rows else {}
    d["hero"] = {
        "pn": hero.get("pn"),
        "description": hero.get("description"),
        "family_label": hero.get("family_label"),
        "isze_eur": hero.get("isze_eur"),
        "proj_db_eur": hero.get("proj_db_eur"),
        "proj_dlr_eur": hero.get("proj_dlr_eur"),
        "proj_retail_eur": hero.get("proj_retail_eur"),
        "iam_offer_eur": hero.get("iam_offer_eur"),
        "iam_point_kind": hero.get("iam_point_kind"),
        "iam_point_note": hero.get("iam_point_note"),
        "quality_brand": hero.get("quality_brand"),
        "quality_source": hero.get("quality_source"),
        "gap_vs_proj_retail": hero.get("gap_vs_proj_retail"),
        "gap_vs_proj_retail_eur": hero.get("gap_vs_proj_retail_eur"),
        "umi_cy2025_eur": hero.get("umi_cy2025_eur"),
        "book_cy2025_eur": hero.get("book_cy2025_eur") or hero.get("umi_cy2025_eur"),
    }
    sold_note = m["sold_to_note"]
    d["kpis"] = [
        {
            "id": "scored",
            "label": f"{short} PNs scored",
            "value": str(m["n_scored"]),
            "sub": f"{m['n_ks']} KS + {m['n_mek']} Mekonomen + {m['n_eucon_in_book']} Eucon in book",
            "tip": (
                f"Distinct {short} part numbers with a usable KS, Mekonomen, or Eucon IAM price, "
                f"joined to the CY{m['cy']} billed book ({sold_note}). KS aftermarket "
                f"at or below £{m['ks_placeholder_gbp']:.0f} dropped. Snapshot "
                f"scrapes 10 Aug 2026; Eucon is a 2023 DE/NO survey. {m['not_blend']}. "
                "Not included: Auto 365 (no OEM PN), Autodoc risk file, raw sales workbooks."
            ),
        },
        {
            "id": "mix",
            "label": "Competitive vs T1 vs hold",
            "value": f"{m['n_competitive']} / {m['n_t1_only']} / {m['n_captive']}",
            "sub": "named T3/T4 · T1-only · no named IAM",
            "tip": (
                "On the priced set: Competitive = named T3/T4 IAM or Best Value in the "
                "crossref. T1-only = unmapped listing — monitor, never auto-cut. "
                "Captive on this priced set is rare because a listing is what got the PN "
                "scored. Book-level ‘no IAM / Best Value observed’ is a separate mix "
                "(incomplete crossref ≠ no Best Value in the catalogue)."
            ),
        },
        {
            "id": "cut",
            "label": "Cut-to-band",
            "value": str(m["n_cut"]),
            "sub": "vs best-quality IAM, not cheapest",
            "tip": (
                "Fires only when a T3/T4 brand is mapped, the listing is not suspect, "
                "ISZE net-to-DB sits above quality_IAM × (1 + effective ceiling), and "
                "the IAM offer is not a mixed Eucon assembly mismatch. Proposed = the "
                "band high. T1 / unmapped listings never auto-fire. Not a flat 20% cut."
            ),
        },
        {
            "id": "book",
            "label": f"{short} CY{m['cy']} on scored PNs",
            "value": f"€{m['rev_scored_eur']:,.0f}",
            "sub": f"of €{m['rev_book_eur']:,.0f} billed book · {m['n_book']} PNs",
            "tip": (
                f"Calendar {m['cy']} net billed to {short} ({sold_note}). Credit notes excluded, "
                f"not subtracted. {m['not_blend']}. Not GPS%."
            ),
        },
    ]
    return d


def html_page(payload: dict, chart_js: str) -> str:
    meta = payload["meta"]
    ch = payload["channel"]
    concl = payload.get("conclusion") or {}
    short = meta["db_short"]
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    payload_json = payload_json.replace("<", "\\u003c")
    spa = ""
    if meta["db_key"] == "UMI":
        spa = f' · <a href="{SPA_REL}">SPA proposed-price workbench</a>'
    banner_right = (
        f"{short} sold-to {esc(str(meta['sold_to']))} · {esc(meta['not_blend'])}{spa}"
    )
    hero_p = (
        "Position vs the <b>best-quality named IAM</b> on the part — T4 / T3 compress the ceiling; "
        "T1 / no-name / unmapped does not. Pads sit tighter than filters. Captive systems are held. "
        "ISZE net is PR00 to the distributor. Projected DB / DLR / retail uses the pricing-engine "
        "channel markup already in local files. IAM scrapes are trade or retail — flagged when not like-for-like."
    )
    channel_lead = (
        "Channel markup from the pricing engine: ISZE net (PR00) × DB +40% × DLR +27.5% "
        "= ×1.785 projected retail. Hover the chips above for source file and snapshot date. "
        "This is a working channel rule, not observed SPA terms. Distributors set their own resale. "
        "Projected retail equals DLR sell — local files have no extra retail markup after the dealer."
    )
    table_lead = (
        "Internal only. ISZE net → projected DB → projected DLR / retail vs the IAM offer. "
        "Gap = (IAM − projected retail) / projected retail. Positive = projected retail cheaper. "
        "This engine replaces a blunt 20% cut."
    )
    foot = (
        f"Internal quality-positioning engine for {short} ({meta['sold_to_note']}). "
        f"Not the customer operating dashboard. {meta['not_blend']}. "
        "Sources: IAM brand-tier table; pricing-engine ladder and channel markup "
        "(config.yaml 1.40 × 1.275); KS International trade listings "
        "(10 Aug 2026, AM ≤ £2 dropped); Mekonomen.se (10 Aug 2026, noisy titles flagged); "
        "PartsPool Autodoc DE/NO (29 Mar 2026) vs IE40 list — not the 2023 UK workshop survey; calendar-2025 billed (credits excluded); "
        "Best Value crossref; AIM classification; PMS intervals and capture. "
        f"FX GBP 1.17 / SEK 0.089 as of 1 May 2026. Built {meta['as_of']}."
    )
    html = TPL.read_text(encoding="utf-8")
    return (
        html.replace("%%PAGE_TITLE%%", f"ISZE vs IAM quality positioning — {short} internal")
        .replace("%%BANNER_RIGHT%%", banner_right)
        .replace("%%HERO_H1%%", f"ISZE vs IAM quality positioning — {short}")
        .replace("%%HERO_P%%", hero_p)
        .replace("%%SIBLING_NAV%%", sibling_nav(meta["db_key"]))
        .replace("%%AS_OF%%", str(meta["as_of"]))
        .replace("%%KPI_HTML%%", kpi_html(payload))
        .replace("%%MARGIN_CHIPS%%", margin_chips_html(ch))
        .replace("%%CONCLUSION_TITLE%%", esc(concl.get("title") or f"Positioning conclusion — {short}"))
        .replace("%%CONCLUSION_LEAD%%", esc(concl.get("lead") or ""))
        .replace("%%CONCLUSION_ITEMS%%", conclusion_items_html(concl))
        .replace("%%CHANNEL_LEAD%%", channel_lead)
        .replace("%%PRODUCT_LEAD%%", pad_capture_txt(payload))
        .replace("%%TABLE_LEAD%%", table_lead)
        .replace("%%FOOT%%", foot)
        .replace("%%CHART_JS%%", chart_js)
        .replace("%%PAYLOAD%%", payload_json)
    )


def _act_map(payload: dict) -> dict:
    return {a["action"]: a["n"] for a in payload.get("actions") or []}


def overview_row(payload: dict) -> dict:
    m = payload["meta"]
    act = _act_map(payload)
    pad = next((x for x in payload.get("pms_capture") or [] if x.get("cat") == "brake_pad"), None)
    cover = (100.0 * (m["rev_scored_eur"] or 0) / m["rev_book_eur"]) if m["rev_book_eur"] else 0.0
    return {
        "db_key": m["db_key"],
        "short": m["db_short"],
        "display": m["db_display"],
        "sold_to_note": m["sold_to_note"],
        "not_blend": m["not_blend"],
        "href": FILE_STEM[m["db_key"]] + ".html",
        "n_scored": m["n_scored"],
        "n_book": m["n_book"],
        "n_ks": m["n_ks"],
        "n_mek": m["n_mek"],
        "n_eucon": m["n_eucon_in_book"],
        "n_competitive": m["n_competitive"],
        "n_t1": m["n_t1_only"],
        "n_captive": m["n_captive"],
        "n_cut": m["n_cut"],
        "n_spa": m["n_spa"],
        "n_bvp": int(act.get("has_bvp") or 0),
        "n_hold": int(act.get("hold") or 0),
        "n_pads": m["n_pads"],
        "rev_scored_eur": m["rev_scored_eur"],
        "rev_book_eur": m["rev_book_eur"],
        "cover_pct": round(cover, 1),
        "pad_capture_pct": pad.get("capture_pct") if pad else None,
        "conclusion_bullets": (payload.get("conclusion") or {}).get("bullets") or [],
    }


def overview_matrix_html(rows: list[dict]) -> str:
    dims = [
        ("n_scored", "PNs scored", False),
        ("rev_scored_eur", "Billed on scored", True),
        ("cover_pct", "Share of that book", False),
        ("n_competitive", "Named T3/T4 or BVP", False),
        ("n_t1", "T1 only (monitor)", False),
        ("n_cut", "Cut-to-band", False),
        ("n_spa", "SPA candidates", False),
        ("n_bvp", "Push Best Value", False),
        ("pad_capture_pct", "Pad capture (PMS)", False),
    ]
    head = "<tr><th>Dimension</th>" + "".join(
        f'<th>{esc(r["short"])}</th>' for r in rows
    ) + "</tr>"
    body = []
    for key, label, money in dims:
        cells = [f"<td>{esc(label)}</td>"]
        for r in rows:
            v = r.get(key)
            if v is None:
                txt, kind = "—", "incomplete"
            elif key == "cover_pct":
                txt, kind = f"{v:.1f}%", "competitive" if v >= 12 else ("monitor" if v >= 6 else "incomplete")
            elif key == "pad_capture_pct":
                txt, kind = f"{v:.1f}%", "competitive" if v >= 20 else ("incomplete" if v >= 10 else "monitor")
            elif money:
                txt, kind = f"€{v:,.0f}", "bvp"
            elif key == "n_cut":
                txt, kind = str(v), "cut" if v else "hold"
            elif key == "n_spa":
                txt, kind = str(v), "spa" if v else "hold"
            elif key == "n_bvp":
                txt, kind = str(v), "bvp"
            else:
                txt, kind = str(v), "hold"
            cells.append(f'<td class="n {kind}">{esc(txt)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<table class="pns mtx"><thead>' + head + "</thead><tbody>"
        + "".join(body) + "</tbody></table>"
        '<p class="src">Each column is one distributor book. Do not add the columns — not a network total.</p>'
    )


def overview_kpis(rows: list[dict]) -> str:
    parts = []
    for r in rows:
        tip = (
            f"{r['display']} · {r['sold_to_note']}. {r['n_scored']} PNs scored, "
            f"€{r['rev_scored_eur']:,.0f} of €{r['rev_book_eur']:,.0f} CY2025 billed "
            f"({r['cover_pct']:.1f}%). {r['not_blend']}. Same engine as the other books."
        )
        parts.append(
            '<a class="kpi" href="' + esc(r["href"]) + '" tabindex="0" data-tip="' + esc(tip) + '">'
            '<div class="lbl">' + esc(r["short"]) + " scored</div>"
            '<div class="val">' + str(r["n_scored"]) + "</div>"
            '<div class="sub">€' + f"{r['rev_scored_eur']:,.0f}" + f" · {r['cover_pct']:.1f}% of book</div>"
            "</a>"
        )
    return "".join(parts)


def overview_conclusion(rows: list[dict]) -> dict:
    densest = max(rows, key=lambda r: r["n_scored"])
    ks_heavy = max(rows, key=lambda r: r["n_ks"])
    spa_max = max(r["n_spa"] for r in rows)
    cut_max = max(r["n_cut"] for r in rows)
    spa_names = ", ".join(r["short"] for r in rows if r["n_spa"] == spa_max)
    cut_names = ", ".join(r["short"] for r in rows if r["n_cut"] == cut_max)
    none_spa = ", ".join(r["short"] for r in rows if r["n_spa"] == 0) or "none"
    pad_sorted = [r for r in rows if r.get("pad_capture_pct") is not None]
    pad_low = min(pad_sorted, key=lambda r: r["pad_capture_pct"]) if pad_sorted else None
    bullets = [
        (
            "Same engine on four books — never blended. Benchmark is the best-quality named IAM, "
            "not the cheapest T1. T4 +30 / T3 +60 / T2 +150 / T1 +250; pads tighter (T4 pad +15). "
            "T1 never auto-cuts. Captive hold. Best Value is retention, never a red cut."
        ),
        (
            f"Scrape density is uneven. {densest['short']} has the most priced PNs ({densest['n_scored']}); "
            f"{ks_heavy['short']} is the KS-heaviest join ({ks_heavy['n_ks']} KS hits). "
            "IAM prices are PN-level market observations joined to each sold-to list. "
            "A KS hit scraped for another DB is still a valid trade quote on that PN — billed euros stay in the owning book."
        ),
        (
            f"SPA vs hold vs push Best Value. {spa_names} have {spa_max} SPA candidates each on this scrape; "
            f"{cut_names} have {cut_max} cut-to-band fire(s). Zero SPA on {none_spa}. "
            "Cut only when ISZE net-to-DB sits above quality IAM × (1 + effective ceiling). "
            "Inside the band: hold unless a SPA is wanted. Best Value rows: push BVP, do not discount genuine."
        ),
        (
            "Pads vs filters is the same rule everywhere, with different capture. "
            + (
                f"{pad_low['short']} pad capture is {pad_low['pad_capture_pct']:.1f}% — the tight T4 pad ceiling (+15%) applies there, "
                "not a copied haircut onto filters."
                if pad_low
                else "Pad capture missing on at least one book — do not invent it."
            )
        ),
        (
            "Projected retail is PR00 × 1.40 × 1.275 = ×1.785 on every book (pricing-engine channel rule, "
            "not observed SPA terms). IAM offers are trade (KS) or retail (Mekonomen) or PartsPool Autodoc DE/NO dated 29 Mar 2026 — "
            "flagged when not like-for-like vs ISZE net-to-DB. Do not treat that gap as a like-for-like walk-out price."
        ),
        (
            "Coverage is a priced sample, not the aftermarket. Scored euros are a slice of each CY2025 book "
            "(PartsPool Autodoc DE/NO 29 Mar 2026; KS/Mekonomen 10 Aug 2026). Incomplete crossref ≠ no Best Value in the catalogue. "
            "Open the per-DB page for the part table and the 8-point conclusion for that sold-to list."
        ),
    ]
    return {
        "title": "Aftermarket position — four books, one engine",
        "lead": "How ISZE should sit versus T4/T3 versus T1, and which lever to use. Columns are separate distributors.",
        "bullets": bullets,
    }


def overview_html(payloads: list[dict], chart_js: str) -> str:
    rows = [overview_row(p) for p in payloads]
    ch = payloads[0]["channel"]
    concl = overview_conclusion(rows)
    slim = {
        "meta": {"as_of": date.today().isoformat(), "n_dbs": len(rows)},
        "rows": [{k: v for k, v in r.items() if k != "conclusion_bullets"} for r in rows],
        "channel": ch,
        "conclusion": concl,
    }
    payload_json = json.dumps(slim, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    payload_json = payload_json.replace("<", "\\u003c")
    foot = (
        "Internal aftermarket-position overview. Four distributor books (UMI, ITUK, ISD, Imotors) — "
        "not added together. Same quality-positioning engine. Channel markup from config.yaml "
        "(1.40 × 1.275 = 1.785). KS trade 10 Aug 2026; Mekonomen.se 10 Aug 2026; PartsPool Autodoc DE/NO 29 Mar 2026; "
        f"CY2025 billed (credits excluded). Built {slim['meta']['as_of']}."
    )
    html = OV_TPL.read_text(encoding="utf-8")
    return (
        html.replace("%%AS_OF%%", slim["meta"]["as_of"])
        .replace("%%SIBLING_NAV%%", sibling_nav(None))
        .replace("%%KPI_HTML%%", overview_kpis(rows))
        .replace("%%MARGIN_CHIPS%%", margin_chips_html(ch))
        .replace("%%MATRIX_HTML%%", overview_matrix_html(rows))
        .replace("%%CONCLUSION_TITLE%%", esc(concl["title"]))
        .replace("%%CONCLUSION_LEAD%%", esc(concl["lead"]))
        .replace("%%CONCLUSION_ITEMS%%", conclusion_items_html(concl))
        .replace("%%FOOT%%", foot)
        .replace("%%CHART_JS%%", chart_js)
        .replace("%%PAYLOAD%%", payload_json)
    )


def write_one(db_key: str, chart_js: str) -> tuple[Path, Path, dict]:
    payload = build_payload(db_key)
    html = html_page(payload, chart_js)
    out = OUT_DIR / f"{FILE_STEM[payload['meta']['db_key']]}.html"
    out.write_text(html, encoding="utf-8")
    cmd = write_cmd(out)
    return out, cmd, payload


def main() -> None:
    ap = argparse.ArgumentParser(description="Build IAM quality-positioning HTML.")
    ap.add_argument("--db", help="REGISTRY key or alias: UMI, ITUK, ISD/GERMANY, IMOTORS/PORTUGAL")
    ap.add_argument("--all", action="store_true", help="UMI + ITUK + ISD + Imotors + overview")
    ap.add_argument("--overview-only", action="store_true", help="rebuild overview from --all scores (implies --all)")
    a = ap.parse_args()
    chart_js = chart_js_inline()
    keys = BUILD_ORDER if (a.all or a.overview_only or not a.db) else [resolve_db(a.db)]
    payloads = []
    for k in keys:
        out, cmd, payload = write_one(k, chart_js)
        payloads.append(payload)
        m = payload["meta"]
        ch = payload["channel"]
        print(f"Wrote {out}")
        print(f"Wrote {cmd}")
        print(
            f"  {m['db_short']} scored={m['n_scored']} competitive={m['n_competitive']} "
            f"t1={m['n_t1_only']} captive={m['n_captive']} pads={m['n_pads']} "
            f"cut={m['n_cut']} spa={m['n_spa']}"
        )
        print(
            f"  channel origin={ch['origin']} DB=+{ch['db_markup_pct']}% "
            f"DLR=+{ch['dlr_markup_pct']}% combined=×{ch['combined_factor']}"
        )
    if len(keys) > 1 or a.all or a.overview_only or not a.db:
        ov = OUT_DIR / f"{OV_STEM}.html"
        ov.write_text(overview_html(payloads if len(payloads) == 4 else [build_payload(k) for k in BUILD_ORDER], chart_js), encoding="utf-8")
        ov_cmd = write_cmd(ov)
        print(f"Wrote {ov}")
        print(f"Wrote {ov_cmd}")


if __name__ == "__main__":
    main()
