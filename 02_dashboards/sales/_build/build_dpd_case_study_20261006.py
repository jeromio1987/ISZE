# -*- coding: utf-8 -*-
"""DPD god-tier case study — merge full clickable analysis + reman/mail/anchors."""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ROOT / "02_dashboards" / "sales"
BUILD = OUT_DIR / "_build"
sys.path.insert(0, str(BUILD))
from build_dpd_reman_feasibility_20261006 import feasibility_section_html  # noqa: E402

FULL_JSON = BUILD / "dpd_full_analysis_20261006_payload.json"
REMAN_JSON = BUILD / "dpd_reman_feasibility_20261006_payload.json"
OUT_HTML = OUT_DIR / "ISZE_DPD_Case_Study_20261006.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_DPD_Case_Study.cmd"
OUT_JSON = BUILD / "dpd_case_study_20261006_payload.json"
OUT_WORKLIST = OUT_DIR / "ISZE_DPD_Reman_Price_Collection_Worklist_20261006.csv"

PN_A = "8975359391"
PN_A_REF = "8981776324"
PN_B = "8975074422"
PN_B_GREY = "8982278993"
PN_B_CLAIM = ["8982049420", "8982050610", "8982878080"]
REMAN_HERO_PNS = {PN_A, PN_A_REF, PN_B, PN_B_GREY, *PN_B_CLAIM}


def feur(v, d=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(x):
        return "—"
    if d == 0:
        return f"€{x:,.0f}"
    return f"€{x:,.{d}f}"


def fnum(v, d=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(x):
        return "—"
    if d == 0:
        return f"{x:,.0f}"
    return f"{x:,.{d}f}"


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def bar_rows(items, max_eur=None, label_key="key", eur_key="eur"):
    if not items:
        return "<p class='muted'>No data.</p>"
    mx = max_eur or max(float(i[eur_key] or 0) for i in items) or 1
    bits = []
    for i in items:
        eur = float(i[eur_key] or 0)
        w = 100.0 * eur / mx
        qty = i.get("qty")
        n_pn = i.get("n_pn")
        sub = ""
        if qty is not None:
            sub = f"<div class='sub'>{fnum(qty)} pcs"
            if n_pn is not None:
                sub += f" · {n_pn} PN"
            sub += "</div>"
        pn_attr = f" data-pn=\"{esc(i['pn'])}\" tabindex=\"0\" role=\"button\"" if i.get("pn") else ""
        bits.append(
            f"<div class='bar-row{(' clickbar' if i.get('pn') else '')}'{pn_attr}>"
            f"<div class='bar-lab'>{esc(i[label_key])}{sub}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{w:.1f}%'></div></div>"
            f"<div class='bar-val'>{feur(eur)}</div></div>"
        )
    return "\n".join(bits)


def stack_table(stack):
    body = []
    for r in stack or []:
        cls = "collect" if r.get("status") == "collect" else ""
        body.append(
            f"<tr class='{cls}'><td>{esc(r['rung'])}</td>"
            f"<td class='num'>{feur(r['eur'], 0) if r.get('eur') is not None else 'COLLECT'}</td>"
            f"<td class='small'>{esc(r.get('note') or '')}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Rung</th><th class='num'>€</th><th>Note</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def core_box(c, title):
    if not c or not c.get("vins"):
        return f"<p class='muted'>{esc(title)}: no VINs in cut.</p>"
    return (
        f"<div class='core'>"
        f"<strong>{esc(c.get('label') or title)}</strong>"
        f"<div class='kpis tiny'>"
        f"<div class='kpi'><div class='v'>{c['vins']}</div><div class='l'>VINs</div></div>"
        f"<div class='kpi'><div class='v'>{fnum(c.get('median_km'))}</div><div class='l'>Median km</div></div>"
        f"<div class='kpi'><div class='v'>{(c.get('reman_candidate_share') or 0)*100:.0f}%</div><div class='l'>Wear-out pool</div></div>"
        f"<div class='kpi'><div class='v'>{(c.get('early_share') or 0)*100:.0f}%</div><div class='l'>Early &lt;30k</div></div>"
        f"</div>"
        f"<p class='sub'>Wear-out = reman-candidate clock. Early fails are poor reman cores. Claims book only.</p>"
        f"</div>"
    )


def verdict_box(v):
    bits = "".join(f"<li>{r}</li>" for r in v.get("reasons") or [])
    return f"<div class='verdict'><div class='call'>{esc(v.get('call') or '')}</div><ul>{bits}</ul></div>"


def build_sandwich_index(reman: dict) -> dict:
    """PN -> {stack, verdict, track, list_eur} for drawers."""
    a = reman["track_a"]
    b = reman["track_b"]
    out = {
        PN_A: {
            "track": "A",
            "label": "Track A — D-Max Euro 6d",
            "stack": a["stack"],
            "verdict": a["verdict"],
            "list_eur": a.get("list_eur"),
        },
        PN_A_REF: {
            "track": "A_REF",
            "label": "Euro 5 reference can (cleaning / IAM floor)",
            "stack": a["ref_stack"],
            "verdict": None,
            "list_eur": None,
        },
        PN_B: {
            "track": "B",
            "label": "Track B — ITUK truck ASM",
            "stack": b["stack"],
            "verdict": b["verdict"],
            "list_eur": b.get("list_eur"),
        },
        PN_B_GREY: {
            "track": "B_GREY",
            "label": "Grey reference CV ASM",
            "stack": b["grey_stack"],
            "verdict": None,
            "list_eur": None,
        },
    }
    for c in b.get("claim_lists") or []:
        out[c["pn"]] = {
            "track": "B_CLAIM",
            "label": "Claim / FILTER ASM (insert — not full can reman)",
            "stack": [
                {
                    "rung": "Our list (IE40 PR00)",
                    "eur": c.get("list_eur"),
                    "note": c.get("description") or "",
                    "status": "observed" if c.get("list_eur") is not None else "collect",
                },
                {
                    "rung": "Warranty parts € (this PN)",
                    "eur": c.get("warranty_eur"),
                    "note": "Claims book total — not a unit price",
                    "status": "observed" if c.get("warranty_eur") else "collect",
                },
                {
                    "rung": "Cleaning / reman specialist quote",
                    "eur": None,
                    "note": "COLLECT — insert reman ≠ full can",
                    "status": "collect",
                },
            ],
            "verdict": None,
            "list_eur": c.get("list_eur"),
        }
    return out


def merge_payload(full: dict, reman: dict) -> dict:
    sandwich = build_sandwich_index(reman)
    meta = dict(full["meta"])
    meta.update(
        {
            "title": "DPD case study — billed assemblies, reman sandwich, exchange programme",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audience": "internal",
            "product": "case_study_merge",
            "sources": {
                **(meta.get("sources") or {}),
                "full_payload": str(FULL_JSON),
                "reman_payload": str(REMAN_JSON),
                "mail_extract": reman.get("mail_brief", {}).get("source_file"),
            },
        }
    )
    return {
        "meta": meta,
        "hero": full["hero"],
        "assemblies": full["assemblies"],
        "cuts": full["cuts"],
        "db_matrix": full["db_matrix"],
        "top_asm_pns": full["top_asm_pns"],
        "warranty": full["warranty"],
        "capture": full["capture"],
        "mail_brief": reman["mail_brief"],
        "portugal_visit": reman.get("portugal_visit"),
        "db_interest": reman.get("db_interest"),
        "web_anchors": reman["web_anchors"],
        "feasibility_economics": reman.get("feasibility_economics"),
        "track_a": reman["track_a"],
        "track_b": reman["track_b"],
        "worklist": reman["worklist"],
        "sandwich_by_pn": sandwich,
        "reman_hero_pns": sorted(REMAN_HERO_PNS),
    }


def render_html(p: dict) -> str:
    h = p["hero"]
    m = p["meta"]
    a = p["track_a"]
    b = p["track_b"]
    mb = p.get("mail_brief") or {}
    anchors = p.get("web_anchors") or []

    pt = p.get("portugal_visit") or {}
    pt_qs = "".join(
        f"<li><strong>Q{q['n']}.</strong> {esc(q['ask'])}"
        f"<div class='muted'>{esc(q['why'])}</div></li>"
        for q in (pt.get("questions") or [])
    )
    pt_dont = "".join(f"<li>{esc(x)}</li>" for x in (pt.get("do_not") or []))
    pt_html = ""
    if pt:
        pt_html = f"""
<section id="sec-portugal">
  <h2>Portugal dealer visit — interest questions</h2>
  <p>{esc(pt.get('purpose') or '')}</p>
  <p class="muted">{esc(pt.get('context_one_liner') or '')}</p>
  <ol>{pt_qs}</ol>
  <div class="callout bad"><strong>Do not</strong><ul>{pt_dont}</ul></div>
  <p class="small"><strong>Report back:</strong> {esc(pt.get('report_back') or '')}</p>
</section>
"""

    dbi = p.get("db_interest") or {}
    db_mkts = "".join(
        f"<li><strong>{esc(mkt['label'])}</strong> ({esc(mkt['code'])}) — {esc(mkt['angle'])}</li>"
        for mkt in (dbi.get("markets") or [])
    )
    db_qs = "".join(f"<li>{esc(q)}</li>" for q in (dbi.get("questions") or []))
    db_html = ""
    if dbi:
        db_html = f"""
<section id="sec-db-interest">
  <h2>Distributor interest (IUK / UMI / Sweden)</h2>
  <p class="muted">{esc(dbi.get('purpose') or '')}</p>
  <ul>{db_mkts}</ul>
  <h3>Ask</h3>
  <ul>{db_qs}</ul>
</section>
"""

    top = p["assemblies"][:12]
    mx = top[0]["eur"] if top else 1
    top_bars_html = bar_rows(
        [
            {"key": f"{r['pn']} · {r['segment']}", "eur": r["eur"], "qty": r["qty"], "n_pn": 1, "pn": r["pn"]}
            for r in top
        ],
        mx,
    )

    asm_table_rows = []
    for r in p["assemblies"]:
        shared = " shared" if r["band_status"] == "shared_across_bands" else ""
        reman_mark = " reman-hero" if r["pn"] in REMAN_HERO_PNS else ""
        series = ", ".join(r.get("series") or []) or "—"
        years = "–".join(x for x in [r.get("year_from"), r.get("year_to")] if x) or "—"
        badge = ""
        if r["pn"] == PN_A:
            badge = "<span class='badge'>Track A</span>"
        elif r["pn"] == PN_B:
            badge = "<span class='badge'>Track B</span>"
        elif r["pn"] == PN_A_REF:
            badge = "<span class='badge mutedb'>Euro 5 ref</span>"
        asm_table_rows.append(
            f"<tr class='clickrow{shared}{reman_mark}' data-kind='pn' data-id='{esc(r['pn'])}' tabindex='0'>"
            f"<td class='mono'>{esc(r['pn'])}{badge}</td>"
            f"<td>{esc(r['description'])}</td>"
            f"<td class='num'>{feur(r['eur'])}</td>"
            f"<td class='num'>{fnum(r['qty'])}</td>"
            f"<td>{esc(r['segment'])}</td>"
            f"<td>{esc(r['tonnage'])}</td>"
            f"<td>{esc(r['billed_emission_label'])}<div class='sub'>{esc(r.get('euro_method') or '')}</div></td>"
            f"<td>{esc(series)}</td>"
            f"<td>{esc(years)}</td>"
            f"<td class='num'>{fnum(r['pcs_per_year'],1)}/yr</td>"
            f"</tr>"
        )

    pn_heads = "".join(f"<th class='mono small'>{esc(pn)}</th>" for pn in p["top_asm_pns"])
    db_rows = []
    for r in p["db_matrix"]:
        cells = "".join(
            f"<td class='num'>{feur(r['by_pn'][pn]['eur']) if r['by_pn'][pn]['eur'] else '—'}</td>"
            for pn in p["top_asm_pns"]
        )
        zero = " zero" if not r["has_sales"] else ""
        iv = r.get("pcs_per_1000_uio_per_year")
        ivs = f"{iv} / 1,000 / yr" if iv is not None else "—"
        db_rows.append(
            f"<tr class='clickrow{zero}' data-kind='db' data-id='{esc(r['distributor_code'])}' tabindex='0'>"
            f"<td><strong>{esc(r['label'])}</strong><div class='sub'>{esc(r['distributor_code'])} · {esc(r['scope'])}</div></td>"
            f"<td class='num'>{feur(r['asm_eur'])}</td>"
            f"<td class='num'>{fnum(r['asm_qty'])}</td>"
            f"<td class='num'>{feur(r['lcv_eur'])}</td>"
            f"<td class='num'>{feur(r['cv_eur'])}</td>"
            f"<td>{esc(ivs)}<div class='sub'>{esc(r.get('interval_txt') or '')}</div></td>"
            f"{cells}</tr>"
        )

    def ops_table(rows):
        if not rows:
            return "<p class='muted'>No matching operations.</p>"
        body = []
        for r in rows:
            lim = ""
            if r.get("outside_limits_share") is not None:
                lim = f"<div class='sub'>Outside stated limits: {r['outside_limits_share']*100:.0f}% ({feur(r.get('outside_limits_eur'))})</div>"
            body.append(
                f"<tr><td>{esc(r['operation'])}{lim}</td>"
                f"<td class='num'>{r['claim_lines']}</td>"
                f"<td class='num'>{feur(r['parts_turnover_eur'])}</td>"
                f"<td class='num'>{fnum(r['median_odometer_km']) if r.get('median_odometer_km') is not None else '—'} km</td>"
                f"<td class='num'>{fnum(r['median_age_years'],1) if r.get('median_age_years') is not None else '—'} yr</td>"
                f"<td class='num'>{r['markets_present']}</td></tr>"
            )
        return (
            "<table><thead><tr><th>Operation</th><th>Lines</th><th>Parts €</th>"
            "<th>Median km</th><th>Median age</th><th>Markets</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    def wart_pn_table(rows):
        if not rows:
            return "<p class='muted'>No billed DPD ASM PNs in this warranty extract.</p>"
        body = []
        for r in rows[:25]:
            body.append(
                f"<tr class='clickrow' data-kind='pn' data-id='{esc(r['pn'])}' tabindex='0'>"
                f"<td class='mono'>{esc(r['pn'])}</td>"
                f"<td class='num'>{feur(r['parts_turnover_eur'])}</td>"
                f"<td class='num'>{r['claim_lines']}</td>"
                f"<td class='num'>{fnum(r['median_odometer_km']) if r.get('median_odometer_km') is not None else '—'} km</td>"
                f"<td>{esc(r.get('segment') or '—')}</td></tr>"
            )
        return (
            "<table><thead><tr><th>PN</th><th>Parts €</th><th>Lines</th><th>Median km</th>"
            "<th>LCV/CV</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    mkt_rows = "".join(
        f"<tr><td>{esc(r['market'])}</td><td class='num'>{feur(r['parts_turnover_eur'])}</td>"
        f"<td class='num'>{r['claim_lines']}</td>"
        f"<td class='num'>{(r['part_number_coverage'] or 0)*100:.0f}%</td></tr>"
        for r in p["warranty"]["cv_markets"][:20]
    )

    mail_cards = "".join(
        (
            f"<div class='mail'>"
            f"<div class='who'>{esc(mail['who'])} · {esc(mail['date'])}</div>"
            f"<div class='subj'>{esc(mail['subject'])}</div>"
            f"<p><strong>Ask:</strong> {esc(mail['ask'])}</p>"
            f"<p><strong>Markets / names:</strong> {esc(mail['named_pns_markets'])}</p>"
            + (
                f"<p><strong>€ / £:</strong> {esc(mail['money'])}</p>"
                if mail.get("money")
                else "<p class='muted'>No € / £ in body.</p>"
            )
            + f"<p><strong>Open:</strong> {esc(mail['decision_or_open'])}</p>"
            f"</div>"
        )
        for mail in mb.get("mails") or []
    )
    impact = "".join(f"<li>{esc(x)}</li>" for x in (mb.get("study_impact") or []))

    anchor_rows = "".join(
        (
            f"<tr><td>{esc(anc['label'])}</td>"
            f"<td>{esc(anc['country'])}</td>"
            f"<td class='num'>"
            + (
                f"{esc(anc['currency'])} {anc['amount']:,.2f}"
                if anc.get("amount") is not None and anc.get("currency")
                else esc(anc.get("amount_note") or "—")
            )
            + "</td>"
            f"<td class='small'>{esc(anc.get('implication') or '')}</td>"
            f"<td class='small'><a href=\"{esc(anc['source_url'])}\" target=\"_blank\" rel=\"noopener\">{esc((anc['source_url'] or '')[:52])}…</a>"
            f"<div class='muted'>{esc(anc.get('caveat') or '')} · observed {esc(anc.get('observed_at') or '')}</div></td></tr>"
        )
        for anc in anchors
    )

    def reman_db_table(rows, pns):
        heads = "".join(f"<th class='mono small'>{esc(pn)}</th>" for pn in pns)
        body = []
        for r in rows[:12]:
            cells = "".join(
                f"<td class='num'>{feur(r['by_pn'].get(pn, {}).get('eur')) if r['by_pn'].get(pn, {}).get('eur') else '—'}</td>"
                for pn in pns
            )
            body.append(
                f"<tr class='clickrow' data-kind='db' data-id='{esc(r['distributor_code'])}' tabindex='0'>"
                f"<td><strong>{esc(r['label'])}</strong><div class='sub'>{esc(r['distributor_code'])}</div></td>"
                f"<td class='num'>{feur(r['eur'])}</td><td class='num'>{fnum(r['qty'])}</td>{cells}</tr>"
            )
        return (
            f"<table><thead><tr><th>DB</th><th class='num'>€</th><th class='num'>Pcs</th>{heads}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    wl_rows = "".join(
        f"<tr class='clickrow' data-kind='pn' data-id='{esc(r['pn'])}' tabindex='0'>"
        f"<td class='mono'>{esc(r['pn'])}</td><td>{esc(r['market'])}</td>"
        f"<td>{esc(r['quote_type'])}</td><td class='amber'>{esc(r['status'])}</td>"
        f"<td class='small'>{esc(r.get('notes') or '')}</td></tr>"
        for r in p["worklist"][:45]
    )

    payload_json = json.dumps(p, ensure_ascii=False).replace("NaN", "null")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(m['title'])}</title>
<style>
:root {{
  --navy:#15233c; --ink:#1a2332; --paper:#f7f4ee; --line:#d9d2c5;
  --terra:#c0552d; --ok:#2f6b4f; --amber:#b45309; --muted:#5c6570;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI", system-ui, sans-serif; color:var(--ink); background:var(--paper); }}
header {{ background:var(--navy); color:#f7f4ee; padding:24px 28px 16px; }}
header h1 {{ margin:0 0 8px; font-family:Georgia, serif; font-weight:600; font-size:26px; }}
header .meta {{ color:#c8d0dc; font-size:13px; line-height:1.45; max-width:1100px; }}
.toolbar {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:12px; }}
.toolbar input {{ padding:8px 10px; border:1px solid #3a4a63; background:#0f1a2c; color:#f7f4ee; min-width:220px; }}
.chip {{ border:1px solid #6a778a; background:transparent; color:#f7f4ee; padding:6px 10px; cursor:pointer; font-size:12px; }}
.chip.on {{ background:var(--terra); border-color:var(--terra); }}
.navstick {{ position:sticky; top:0; z-index:10; background:rgba(247,244,238,.96); border-bottom:1px solid var(--line); padding:8px 28px; display:flex; flex-wrap:wrap; gap:8px; }}
.navstick a {{ color:var(--navy); text-decoration:none; font-size:12px; border:1px solid var(--line); padding:5px 10px; background:#fff; }}
.navstick a:hover, .navstick a.on {{ border-color:var(--terra); color:var(--terra); background:#fff8ef; }}
main {{ padding:16px 28px 80px; max-width:1320px; margin:0 auto; }}
h2 {{ font-family:Georgia, serif; color:var(--navy); margin:32px 0 10px; font-size:22px; scroll-margin-top:56px; }}
h3 {{ color:var(--navy); margin:16px 0 8px; font-size:15px; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin:12px 0; }}
.kpis.tiny .kpi .v {{ font-size:16px; }}
.kpi {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--terra); padding:10px 12px; }}
.kpi .v {{ font-size:18px; font-weight:700; color:var(--navy); }}
.kpi .l {{ font-size:11px; color:var(--muted); margin-top:3px; }}
.callout {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--amber); padding:12px 14px; margin:12px 0; font-size:14px; line-height:1.45; }}
.callout.bad {{ border-left-color:var(--terra); }}
.bar-row {{ display:grid; grid-template-columns:240px 1fr 90px; gap:10px; align-items:center; margin:6px 0; }}
.bar-row.clickbar {{ cursor:pointer; padding:4px 6px; border-radius:2px; }}
.bar-row.clickbar:hover {{ background:#efe8dc; }}
.bar-lab {{ font-size:13px; }}
.bar-lab .sub, .sub, .small, .muted {{ font-size:11px; color:var(--muted); }}
.bar-track {{ background:#e8e2d6; height:14px; border-radius:2px; overflow:hidden; }}
.bar-fill {{ background:var(--terra); height:100%; }}
.bar-val {{ text-align:right; font-variant-numeric:tabular-nums; font-size:13px; font-weight:600; }}
table {{ width:100%; border-collapse:collapse; background:#fff; font-size:13px; }}
th, td {{ border-bottom:1px solid var(--line); padding:7px 9px; text-align:left; vertical-align:top; }}
th {{ background:var(--navy); color:#f7f4ee; font-weight:600; position:sticky; top:0; z-index:1; }}
td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
tr.shared td {{ background:#fff8ef; }}
tr.reman-hero td {{ box-shadow:inset 3px 0 0 var(--terra); }}
tr.zero td {{ color:#8a9098; }}
tr.clickrow {{ cursor:pointer; }}
tr.clickrow:hover td {{ background:#efe8dc; }}
tr.clickrow.active td {{ background:#e4d5c4; }}
tr.collect td {{ background:#fff8ef; }}
.mono {{ font-family:ui-monospace, Consolas, monospace; font-size:12px; }}
.amber {{ color:var(--amber); font-weight:600; }}
.badge {{ display:inline-block; margin-left:6px; font-size:10px; background:var(--terra); color:#fff; padding:1px 6px; vertical-align:middle; }}
.badge.mutedb {{ background:#5c6570; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.grid3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }}
@media (max-width:980px) {{ .grid2, .grid3 {{ grid-template-columns:1fr; }} .bar-row {{ grid-template-columns:1fr; }} }}
.card {{ background:#fff; border:1px solid var(--line); padding:14px 16px; }}
.card h2 {{ margin-top:0; font-size:18px; border-bottom:3px solid var(--terra); padding-bottom:6px; }}
.scroll {{ overflow:auto; max-height:520px; border:1px solid var(--line); }}
.mail {{ background:#fff; border:1px solid var(--line); padding:10px 12px; font-size:13px; line-height:1.4; }}
.mail .who {{ font-weight:700; color:var(--navy); }}
.mail .subj {{ font-size:12px; color:var(--muted); margin:2px 0 8px; }}
.mail p {{ margin:4px 0; }}
.verdict {{ background:#15233c; color:#f7f4ee; padding:12px 14px; margin-top:12px; }}
.verdict .call {{ font-family:Georgia, serif; font-size:17px; color:#f0c9b8; margin-bottom:8px; }}
.verdict ul {{ margin:0; padding-left:18px; font-size:13px; line-height:1.4; }}
.verdict li {{ margin:4px 0; }}
.core {{ border:1px dashed var(--line); padding:10px; margin:8px 0; }}
.ladder {{ display:grid; grid-template-columns:1fr auto 1fr auto 1fr; gap:8px; align-items:stretch; margin:14px 0; }}
.ladder .rung {{ background:#fff; border:1px solid var(--line); padding:12px; text-align:center; }}
.ladder .rung strong {{ display:block; color:var(--navy); font-family:Georgia, serif; margin-bottom:4px; }}
.ladder .rung .lvl {{ font-size:11px; color:var(--muted); }}
.ladder .arrow {{ align-self:center; color:var(--terra); font-weight:700; }}
.ladder .rung.mid {{ border-color:var(--terra); box-shadow:inset 0 0 0 1px var(--terra); }}
table.sens td.pos {{ background:#e8f2ea; }}
table.sens td.neg {{ background:#fff0e8; color:var(--terra); font-weight:600; }}
.drawer {{ position:fixed; top:0; right:0; width:min(480px,100%); height:100%; background:#fff; border-left:4px solid var(--terra);
  box-shadow:-8px 0 24px rgba(21,35,60,.18); padding:18px 18px 40px; overflow:auto; z-index:40; display:none; }}
.drawer.open {{ display:block; }}
.drawer h2 {{ margin-top:8px; }}
.drawer .x {{ float:right; border:0; background:var(--navy); color:#f7f4ee; padding:6px 10px; cursor:pointer; }}
.drawer .sandwich {{ margin-top:12px; border:1px solid var(--line); }}
.drawer .chipv {{ display:inline-block; background:var(--navy); color:#f0c9b8; padding:4px 8px; font-size:12px; margin:6px 0; }}
.drawer .copy {{ border:1px solid var(--line); background:#f7f4ee; padding:4px 8px; cursor:pointer; font-size:11px; margin-left:8px; }}
.drawer .jump {{ display:inline-block; margin:8px 0 4px; border:1px solid var(--terra); color:var(--terra); background:#fff8ef; padding:6px 10px; cursor:pointer; font-size:12px; text-decoration:none; }}
.scrim {{ position:fixed; inset:0; background:rgba(21,35,60,.35); z-index:35; display:none; }}
.scrim.on {{ display:block; }}
#match-count {{ font-size:12px; color:#c8d0dc; margin-left:4px; }}
.ed {{ font-size:12px; margin:4px 0; padding-left:8px; border-left:3px solid var(--line); }}
footer {{ margin-top:40px; font-size:12px; color:var(--muted); }}
a {{ color:var(--terra); }}
</style>
</head>
<body>
<header>
  <h1>DPD case study — assemblies, reman sandwich, exchange</h1>
  <div class="meta">
    Internal. {esc(m['window_start'])} → {esc(m['window_end'])}.
    DPD ASM / DPF ASM only — no sensors, gaskets, FILTER ASM 150-558 as billed hero.
    Click a PN or distributor. Reman hero PNs open a price sandwich.
    {esc(m.get('uti_umi') or 'UTI and UMI stay separate')}. Generated {esc(m['as_of'])}.
  </div>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Search PN, distributor, Euro 6d…"/>
    <button class="chip on" data-f="all" type="button">All</button>
    <button class="chip" data-f="LCV" type="button">LCV / D-Max</button>
    <button class="chip" data-f="CV" type="button">CV truck</button>
    <button class="chip" data-f="e6d" type="button">Euro 6d</button>
    <button class="chip" data-f="e6" type="button">Euro 6</button>
    <button class="chip" data-f="e5" type="button">Euro 5</button>
    <button class="chip" data-f="reman" type="button">Reman heroes</button>
    <span id="match-count" aria-live="polite"></span>
  </div>
</header>
<nav class="navstick" aria-label="Sections">
  <a href="#sec-mail">Peter / Osamu</a>
  <a href="#sec-portugal">Portugal visit</a>
  <a href="#sec-db-interest">DB interest</a>
  <a href="#sec-anchors">Anchors</a>
  <a href="#sec-asm">Assemblies</a>
  <a href="#sec-cuts">Cuts</a>
  <a href="#sec-db">Distributors</a>
  <a href="#sec-warranty">Warranty</a>
  <a href="#sec-reman">Reman</a>
  <a href="#sec-feasibility">Demand pipes</a>
  <a href="#sec-worklist">Worklist</a>
  <a href="#sec-read">How to read</a>
</nav>
<main>

<section id="sec-hero">
  <div class="kpis">
    <div class="kpi"><div class="v">{feur(h['asm_eur'])}</div><div class="l">DPD ASM billed · {fnum(h['asm_qty'])} pcs · {h['asm_pns']} PNs</div></div>
    <div class="kpi"><div class="v">{feur(h['lcv_eur'])}</div><div class="l">LCV / D-Max</div></div>
    <div class="kpi"><div class="v">{feur(h['cv_eur'])}</div><div class="l">CV truck</div></div>
    <div class="kpi"><div class="v">{h['dbs_with_asm']} / {h['dbs_total_network']}</div><div class="l">network DBs with DPD ASM</div></div>
    <div class="kpi"><div class="v">{feur(h['warranty_cv_ops_eur'])}</div><div class="l">CV warranty ops (particulate / DPD)</div></div>
    <div class="kpi"><div class="v">{feur(h['warranty_lcv_ops_eur'])}</div><div class="l">LCV warranty ops (particulate / DPD)</div></div>
  </div>
  <div class="callout bad">
    Reman clears only if it sits <strong>above cleaning</strong> and <strong>below grey / new</strong>
    (trucks: beside or under ITUK <strong>new-in-lieu</strong>).
    Return rate, reman unit cost and yield % are <strong>UNKNOWN</strong> — COLLECT, not invented.
    Mail 2026-10-06: prior vehicle cleaning failed mainly on <strong>pricing</strong>; NG cores empty the pool.
  </div>
  <div class="callout">{esc(h.get('capture_one_liner') or '')}</div>
  <div class="callout">{esc(m.get('emission_rule') or '')}</div>
</section>

<section id="sec-mail">
  <h2>What Peter / Osamu asked</h2>
  <p class="muted">{esc(mb.get('name_note') or '')} {esc(mb.get('coverage_note') or '')}</p>
  <div class="grid3">{mail_cards}</div>
  <div class="callout"><strong>How this moves the study</strong><ul>{impact}</ul></div>
</section>

{pt_html}
{db_html}

<section id="sec-anchors">
  <h2>Public competitive anchors</h2>
  <p class="muted">Not dealer transactions. Source URL + country + observed date. Prefer COLLECT for live dealer €.</p>
  <div class="scroll">
  <table>
    <thead><tr><th>Anchor</th><th>Country</th><th class="num">Observed</th><th>Implication</th><th>Source</th></tr></thead>
    <tbody>{anchor_rows}</tbody>
  </table>
  </div>
</section>

<section id="sec-asm">
  <h2>1. Ranked DPD assemblies — click a row</h2>
  {top_bars_html}
  <div class="scroll" style="margin-top:16px">
  <table id="pn-table">
    <thead><tr>
      <th>PN</th><th>Desc</th><th class="num">€</th><th class="num">Pcs</th>
      <th>LCV/CV</th><th>Tonnage</th><th>Emission (billed mix)</th><th>Series</th><th>Years</th><th class="num">Pcs/yr</th>
    </tr></thead>
    <tbody>{''.join(asm_table_rows)}</tbody>
  </table>
  </div>
</section>

<section id="sec-cuts">
  <h2>2. Emission of the billed euros</h2>
  <p class="muted">This cut uses who we billed, plus Europe/Israel model year — not a blank “not in EPC string”.</p>
  {bar_rows(p['cuts']['euro_norm'], label_key='key')}
  <div class="grid2">
    <div><h3>LCV vs CV</h3>{bar_rows(p['cuts']['segment'], label_key='key')}</div>
    <div><h3>Tonnage</h3>{bar_rows(p['cuts']['tonnage'], label_key='key')}</div>
  </div>
</section>

<section id="sec-db">
  <h2>3. Every distributor — click for interval and mix</h2>
  <p class="muted">{esc(m.get('interval_rule') or '')}</p>
  <div class="scroll">
  <table id="db-table">
    <thead><tr>
      <th>Distributor</th><th class="num">ASM €</th><th class="num">Pcs</th>
      <th class="num">LCV €</th><th class="num">CV €</th><th>Observed interval</th>
      {pn_heads}
    </tr></thead>
    <tbody>{''.join(db_rows)}</tbody>
  </table>
  </div>
</section>

<section id="sec-warranty">
  <h2>4. Warranty — DPD / particulate operations only</h2>
  <h3>CV truck</h3>
  {ops_table(p['warranty']['ops_cv'])}
  <h3>LCV / D-Max</h3>
  {ops_table(p['warranty']['ops_lcv'])}
  <div class="grid2">
    <div><h3>CV — billed DPD ASM in claims</h3>{wart_pn_table(p['warranty']['pn_cv'])}</div>
    <div><h3>LCV — billed DPD ASM in claims</h3>{wart_pn_table(p['warranty']['pn_lcv'])}</div>
  </div>
  <h3>CV claim book — markets</h3>
  <p class="muted">MIDI ES/IT appear in the claim book as geography — not an ISZE action list.</p>
  <div class="scroll"><table><thead><tr><th>Market</th><th class="num">Parts €</th><th class="num">Lines</th><th class="num">PN coverage</th></tr></thead>
  <tbody>{mkt_rows}</tbody></table></div>
</section>

<section id="sec-reman">
  <h2>5. Reman feasibility — two tracks</h2>
  <div class="ladder" aria-label="Three-way price sandwich">
    <div class="rung"><strong>Cleaning</strong><div class="lvl">Floor · Optymha / Ceramex · COLLECT dealer €</div></div>
    <div class="arrow">→</div>
    <div class="rung mid"><strong>Reman / exchange</strong><div class="lvl">Must clear above cleaning · yield UNKNOWN</div></div>
    <div class="arrow">→</div>
    <div class="rung"><strong>New / new-in-lieu</strong><div class="lvl">Ceiling · ITUK programme · dealer € COLLECT</div></div>
  </div>
  <p class="muted">No invented euros on this strip — only the order reman must sit in. Track A HOLD / Track B CONDITIONAL below use observed list/ASP only.</p>
  {feasibility_section_html(p.get("feasibility_economics"))}
  <div class="grid2">
    <section class="card">
      <h2>Track A — D-Max Euro 6d</h2>
      <p class="muted">Hero PN {esc(PN_A)}. Euro 5 {esc(PN_A_REF)} is price reference only.</p>
      <div class="kpis">
        <div class="kpi"><div class="v">{feur(a['volume']['eur'])}</div><div class="l">Billed · {fnum(a['volume']['qty'])} pcs</div></div>
        <div class="kpi"><div class="v">{feur(a['volume']['asp'],0)}</div><div class="l">ASP to DB</div></div>
        <div class="kpi"><div class="v">{a['volume']['share_of_asm']*100:.0f}%</div><div class="l">of network DPD ASM €</div></div>
        <div class="kpi"><div class="v">{feur(a.get('list_eur'))}</div><div class="l">IE40 list</div></div>
      </div>
      <h3>Who billed it</h3>
      {reman_db_table(a['db_cut'], [PN_A])}
      <h3>Price stack — click PN in assemblies for drawer</h3>
      {stack_table(a['stack'])}
      <h3>Euro 5 reference ladder ({esc(PN_A_REF)})</h3>
      {stack_table(a['ref_stack'])}
      <h3>Core pool (VIN)</h3>
      {core_box(a['core'].get('hero_pn'), 'Hero PN')}
      {core_box(a['core'].get('all_assembly'), 'All D-Max assembly')}
      {verdict_box(a['verdict'])}
    </section>
    <section class="card">
      <h2>Track B — ITUK truck</h2>
      <p class="muted">Billed ASM {esc(PN_B)}. Claim FILTER ASM PNs are a separate product.</p>
      <div class="kpis">
        <div class="kpi"><div class="v">{feur(b['volume']['eur'])}</div><div class="l">Billed ASM · {fnum(b['volume']['qty'])} pcs</div></div>
        <div class="kpi"><div class="v">{feur(b['volume']['asp'],0)}</div><div class="l">ASP to DB</div></div>
        <div class="kpi"><div class="v">{feur(b.get('list_eur'))}</div><div class="l">IE40 list (ASM)</div></div>
        <div class="kpi"><div class="v">{(b['core'].get('billed_pn_share_of_asm_claims') or 0)*100:.0f}%</div><div class="l">billed PN share of ASM claims</div></div>
      </div>
      <h3>Who billed the ASM</h3>
      {reman_db_table(b['db_cut'], [PN_B])}
      <h3>Claim PN list prices</h3>
      <table><thead><tr><th>PN</th><th>Desc</th><th class="num">IE40 €</th></tr></thead><tbody>
      {''.join(
        f"<tr class='clickrow' data-kind='pn' data-id='{esc(c['pn'])}' tabindex='0'><td class='mono'>{esc(c['pn'])}</td><td>{esc(c.get('description') or '')}</td>"
        f"<td class='num'>{feur(c.get('list_eur'))}</td></tr>"
        for c in b['claim_lists']
      )}
      </tbody></table>
      <h3>Price stack — billed ASM</h3>
      {stack_table(b['stack'])}
      <div class="callout">
        <strong>ITUK new-in-lieu:</strong> brand new priced like reman + core return.
        Dealer € = <span class="amber">COLLECT</span> from ITUK parts.
      </div>
      <h3>Grey reference ({esc(PN_B_GREY)})</h3>
      {stack_table(b['grey_stack'])}
      <h3>Core pool (VIN)</h3>
      {core_box(b['core'].get('uk_assembly'), 'UK assembly')}
      {core_box(b['core'].get('uk_filter'), 'UK filter')}
      {core_box(b['core'].get('israel_filter_footnote'), 'Israel filter footnote')}
      {verdict_box(b['verdict'])}
    </section>
  </div>
</section>

<section id="sec-worklist">
  <h2>6. Price collection worklist</h2>
  <p class="muted">{len(p['worklist'])} rows (named specialists first). First 45 shown. Full CSV beside this file.</p>
  <div class="scroll">
  <table>
    <thead><tr><th>PN</th><th>Market</th><th>Quote type</th><th>Status</th><th>Notes</th></tr></thead>
    <tbody>{wl_rows}</tbody>
  </table>
  </div>
</section>

<section id="sec-read">
  <h2>7. How to read this</h2>
  <div class="callout">
    <ul>
      <li>Lead with <strong>euros</strong>, not piece counts. A gasket and a can are not comparable in pieces.</li>
      <li>Observed pcs / 1,000 UIO is <strong>not</strong> an IML service interval and not a capture %.</li>
      <li>COLLECT means we do not have a dealer transaction — do not invent one from public listings.</li>
      <li>UTI ≠ UMI. IUK ≠ ITUK. MIDI ES/IT claim geography is context, not an ISZE chase list.</li>
      <li>FILTER ASM claim PNs are inserts — reman of the insert is not reman of the full can.</li>
      <li>Click a bar, table row or worklist PN to open the drawer. Esc or the dimmed page closes it. Enter / Space on a focused row also opens.</li>
      <li><strong>Demand pipes:</strong> warranty first-claim, commercial billed, and fleet pcs/1,000 UIO are separate. Billed pcs ≠ market size. First-DPD warranty % cannot be computed. Cleaning / freight bands are ASSUMPTION until Optymha quotes land (COLLECT).</li>
    </ul>
  </div>
</section>

<footer>
  Double-click <code>OPEN_ISZE_DPD_Case_Study.cmd</code>.
  Worklist: <code>ISZE_DPD_Reman_Price_Collection_Worklist_20261006.csv</code>.
  Prior Full Analysis and Reman pages remain on disk as earlier cuts.
</footer>
</main>

<div class="scrim" id="scrim" hidden></div>
<aside class="drawer" id="drawer" hidden>
  <button class="x" type="button" id="dx">Close</button>
  <div id="dbody"></div>
</aside>
<script type="application/json" id="payload">{payload_json}</script>
<script>
(function(){{
  const P = JSON.parse(document.getElementById('payload').textContent);
  const byPn = Object.fromEntries(P.assemblies.map(r => [r.pn, r]));
  const byDb = Object.fromEntries(P.db_matrix.map(r => [r.distributor_code, r]));
  const sandwich = P.sandwich_by_pn || {{}};
  const remanHero = new Set(P.reman_hero_pns || []);
  const drawer = document.getElementById('drawer');
  const dbody = document.getElementById('dbody');
  const scrim = document.getElementById('scrim');
  const matchCount = document.getElementById('match-count');
  const eur = n => (n==null || n==='') ? '—' : ('€' + Math.round(n||0).toLocaleString('en-GB'));
  function openDrawer(html){{
    dbody.innerHTML = html;
    drawer.hidden = false;
    drawer.classList.add('open');
    if(scrim){{ scrim.hidden = false; scrim.classList.add('on'); }}
  }}
  function closeDrawer(){{
    drawer.classList.remove('open');
    drawer.hidden = true;
    if(scrim){{ scrim.classList.remove('on'); scrim.hidden = true; }}
    document.querySelectorAll('tr.active').forEach(t => t.classList.remove('active'));
  }}
  function openPn(id){{
    if(byPn[id]) openDrawer(pnHtml(byPn[id]));
    else if(sandwich[id]) openDrawer('<h2>'+id+' <button class="copy" type="button" data-copy="'+id+'">Copy PN</button></h2>'+sandwichHtml(id)+anchorsForPn(id)+(remanHero.has(id)?'<p><button class="jump" type="button" data-jump="sec-reman">Jump to reman chapter</button></p>':''));
    else openDrawer('<h2>'+id+' <button class="copy" type="button" data-copy="'+id+'">Copy PN</button></h2><p class="muted">No billed DPD ASM row and no reman sandwich for this PN — still on the COLLECT worklist.</p>');
  }}
  document.getElementById('dx').onclick = closeDrawer;
  if(scrim) scrim.onclick = closeDrawer;
  document.addEventListener('keydown', e => {{
    if(e.key==='Escape') closeDrawer();
    const t = e.target.closest('tr.clickrow, .bar-row.clickbar');
    if(t && (e.key==='Enter' || e.key===' ')){{
      e.preventDefault();
      t.click();
    }}
  }});

  function sandwichHtml(pn){{
    const s = sandwich[pn];
    if(!s) return '';
    const rows = (s.stack||[]).map(r => {{
      const val = (r.eur==null) ? '<span class="amber">COLLECT</span>' : eur(r.eur);
      return '<tr class="'+(r.status==='collect'?'collect':'')+'"><td>'+escTxt(r.rung)+'</td><td class="num">'+val+'</td><td class="small">'+escTxt(r.note||'')+'</td></tr>';
    }}).join('');
    const ver = s.verdict ? '<div class="chipv">'+escTxt(s.verdict.call||'')+'</div>' : '';
    return '<div class="sandwich"><h3>Price sandwich — '+escTxt(s.label||pn)+'</h3>'+ver
      +'<table><thead><tr><th>Rung</th><th class="num">€</th><th>Note</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
  }}
  function anchorsForPn(pn){{
    const bits = (P.web_anchors||[]).filter(a => {{
      if(pn==='8975074422' || pn==='8982049420' || pn==='8982050610' || pn==='8982878080' || pn==='8982278993') return /ITUK|Driveline|Directfit|Freedom|Optymha/i.test(a.label||'');
      if(pn==='8975359391' || pn==='8981776324') return /Optymha|Ceramex|Freedom/i.test(a.label||'');
      return false;
    }}).map(a => '<div class="ed"><strong>'+escTxt(a.label)+'</strong> · '+(a.currency&&a.amount!=null?(a.currency+' '+a.amount):escTxt(a.amount_note||'COLLECT'))
      +'<div class="muted">'+escTxt(a.caveat||'')+'</div></div>').join('');
    return bits ? '<h3>Related public anchors</h3>'+bits : '';
  }}
  function escTxt(s){{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

  function pnHtml(r){{
    const dbs = (r.top_dbs||[]).map(d => '<div>'+d.db+' · '+eur(d.eur)+' · '+(d.qty)+' pcs</div>').join('');
    const eu = (r.europe_editions||[]).map(m => '<div class="ed">'+m+'</div>').join('') || '<div class="muted">None</div>';
    const ex = (r.exp_editions||[]).map(m => '<div class="ed">'+m+'</div>').join('') || '<div class="muted">None</div>';
    const wart = (P.warranty.pn_lcv||[]).concat(P.warranty.pn_cv||[]).filter(w => w.pn===r.pn);
    const wartHtml = wart.length
      ? '<h3>Warranty on this PN</h3>'+wart.map(w => '<div>'+escTxt(w.bag)+' · '+eur(w.parts_turnover_eur)+' · '+w.claim_lines+' lines · median '+(w.median_odometer_km!=null?Math.round(w.median_odometer_km).toLocaleString('en-GB')+' km':'—')+'</div>').join('')
      : '';
    const jump = remanHero.has(r.pn)
      ? '<p><button class="jump" type="button" data-jump="sec-reman">Jump to reman chapter</button></p>'
      : '';
    return '<h2>'+r.pn+' <button class="copy" type="button" data-copy="'+r.pn+'">Copy PN</button></h2><p>'+escTxt(r.description)+'</p>'
      +'<p><strong>'+eur(r.eur)+'</strong> · '+r.qty+' pcs · '+escTxt(r.segment)+' · '+escTxt(r.tonnage)+'</p>'
      +'<p><strong>Billed emission:</strong> '+escTxt(r.billed_emission_label)+'</p>'
      +'<p class="muted">'+escTxt(r.billed_emission_note)+'</p>'
      +'<p class="muted">'+escTxt(r.euro_method)+'</p>'
      + jump
      + sandwichHtml(r.pn)
      + anchorsForPn(r.pn)
      + wartHtml
      +'<h3>Who bought it</h3>'+dbs
      +'<h3>Europe / Israel editions</h3>'+eu
      +'<h3>EXP editions</h3>'+ex;
  }}
  function dbHtml(r){{
    const pns = Object.entries(r.by_pn_all||{{}}).sort((a,b)=>b[1].eur-a[1].eur)
      .map(([pn,v]) => '<div class="clickpn" data-id="'+pn+'" style="cursor:pointer;padding:4px 0">'+pn+' · '+eur(v.eur)+' · '+v.qty+' pcs</div>').join('')
      || '<p class="muted">No DPD ASM in the window.</p>';
    const focus = ['8975359391','8975074422','8981776324'];
    const focusBits = focus.map(pn => {{
      const cell = (r.by_pn_all||{{}})[pn] || (r.by_pn||{{}})[pn];
      if(!cell || !cell.eur) return '';
      return '<div class="clickpn" data-id="'+pn+'" style="cursor:pointer;padding:4px 0"><strong>'+pn+'</strong> · '+eur(cell.eur)+' · '+cell.qty+' pcs (reman hero)</div>';
    }}).filter(Boolean).join('');
    const remanNote = (r.distributor_code==='UMI'||r.distributor_code==='IUK'||r.distributor_code==='ITUK')
      ? '<h3>Reman heroes on this DB</h3>'+(focusBits||'<p class="muted">No Track A/B hero euros here.</p>')
      : '';
    return '<h2>'+escTxt(r.label)+'</h2><p>'+escTxt(r.distributor_code)+' · '+escTxt(r.scope)+'</p>'
      +'<p><strong>'+eur(r.asm_eur)+'</strong> · '+r.asm_qty+' pcs</p>'
      +'<p><strong>Observed interval:</strong> '+escTxt(r.interval_txt||'—')+'</p>'
      +'<p class="muted">Trucks in service used: '+(r.uio_used||'—')+' ('+escTxt(r.uio_note||'')+'). LCV UIO '+(r.uio_lcv||'—')+' · CV UIO '+(r.uio_cv||'—')+'.</p>'
      + remanNote
      +'<h3>Parts billed here</h3>'+pns;
  }}

  document.body.addEventListener('click', e => {{
    const copy = e.target.closest('[data-copy]');
    if(copy){{
      const v = copy.getAttribute('data-copy');
      if(navigator.clipboard) navigator.clipboard.writeText(v);
      copy.textContent = 'Copied';
      setTimeout(() => {{ copy.textContent = 'Copy PN'; }}, 1200);
      return;
    }}
    const jump = e.target.closest('[data-jump]');
    if(jump){{
      const id = jump.getAttribute('data-jump');
      closeDrawer();
      const el = document.getElementById(id);
      if(el) el.scrollIntoView({{behavior:'smooth', block:'start'}});
      return;
    }}
    const bar = e.target.closest('.bar-row.clickbar');
    if(bar){{
      openPn(bar.getAttribute('data-pn'));
      return;
    }}
    const row = e.target.closest('tr.clickrow');
    const pnlink = e.target.closest('.clickpn');
    if(pnlink){{
      openPn(pnlink.getAttribute('data-id'));
      return;
    }}
    if(!row) return;
    document.querySelectorAll('tr.active').forEach(t => t.classList.remove('active'));
    row.classList.add('active');
    const kind = row.getAttribute('data-kind');
    const id = row.getAttribute('data-id');
    if(kind==='pn') openPn(id);
    if(kind==='db' && byDb[id]) openDrawer(dbHtml(byDb[id]));
  }});

  let filter = 'all';
  document.querySelectorAll('.chip').forEach(ch => {{
    ch.onclick = () => {{
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
      ch.classList.add('on');
      filter = ch.getAttribute('data-f');
      apply();
    }};
  }});
  const q = document.getElementById('q');
  q.addEventListener('input', apply);
  function apply(){{
    const s = (q.value||'').toLowerCase();
    let pnShown = 0, pnTotal = 0, dbShown = 0, dbTotal = 0;
    document.querySelectorAll('#pn-table tbody tr').forEach(tr => {{
      const id = tr.getAttribute('data-id');
      const r = byPn[id];
      if(!r) return;
      pnTotal += 1;
      let ok = true;
      if(filter==='LCV' || filter==='CV') ok = r.segment === filter;
      if(filter==='e6d') ok = /6d/i.test(r.billed_emission_label||'');
      if(filter==='e6') ok = /Euro 6(?!d)/i.test(r.billed_emission_label||'') || /Euro 6 \\(/i.test(r.billed_emission_label||'');
      if(filter==='e5') ok = /Euro 5/i.test(r.billed_emission_label||'');
      if(filter==='reman') ok = remanHero.has(r.pn);
      const hay = (r.pn+' '+r.description+' '+(r.billed_emission_label||'')+' '+(r.series||[]).join(' ')+' '+(r.top_dbs||[]).map(d=>d.db).join(' ')).toLowerCase();
      if(s && hay.indexOf(s)<0) ok = false;
      tr.style.display = ok ? '' : 'none';
      if(ok) pnShown += 1;
    }});
    document.querySelectorAll('#db-table tbody tr').forEach(tr => {{
      const id = tr.getAttribute('data-id');
      const r = byDb[id];
      if(!r) return;
      dbTotal += 1;
      const hay = (r.label+' '+r.distributor_code+' '+(r.interval_txt||'')).toLowerCase();
      const ok = (!s || hay.indexOf(s)>=0);
      tr.style.display = ok ? '' : 'none';
      if(ok) dbShown += 1;
    }});
    if(matchCount){{
      const filtering = filter!=='all' || !!s;
      matchCount.textContent = filtering
        ? (pnShown+' of '+pnTotal+' assemblies · '+dbShown+' of '+dbTotal+' distributors')
        : '';
    }}
  }}
  apply();

  // Sticky nav highlight
  const secs = [...document.querySelectorAll('section[id]')];
  const navLinks = [...document.querySelectorAll('.navstick a')];
  function spy(){{
    const y = window.scrollY + 70;
    let cur = secs[0] && secs[0].id;
    secs.forEach(s => {{ if(s.offsetTop <= y) cur = s.id; }});
    navLinks.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#'+cur));
  }}
  window.addEventListener('scroll', spy, {{passive:true}});
  spy();

  // Deep-link ?pn=8975359391
  const params = new URLSearchParams(location.search);
  const deep = params.get('pn');
  if(deep) openPn(deep);
}})();
</script>
</body>
</html>
"""


def main() -> None:
    if not FULL_JSON.exists():
        raise SystemExit(f"Missing full payload: {FULL_JSON}")
    if not REMAN_JSON.exists():
        raise SystemExit(f"Missing reman payload: {REMAN_JSON}")

    print("loading payloads…")
    full = json.loads(FULL_JSON.read_text(encoding="utf-8"))
    reman = json.loads(REMAN_JSON.read_text(encoding="utf-8"))
    payload = merge_payload(full, reman)

    BUILD.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT_JSON)

    pd.DataFrame(payload["worklist"]).to_csv(OUT_WORKLIST, index=False, encoding="utf-8")
    print("wrote", OUT_WORKLIST, "rows", len(payload["worklist"]))

    html = render_html(payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_DPD_Case_Study_20261006.html"\r\n',
        encoding="utf-8",
        newline="",
    )
    print("wrote", OUT_HTML, OUT_HTML.stat().st_size)
    print("A", payload["track_a"]["verdict"]["call"])
    print("B", payload["track_b"]["verdict"]["call"])
    print("assemblies", len(payload["assemblies"]), "dbs", len(payload["db_matrix"]))


if __name__ == "__main__":
    main()
