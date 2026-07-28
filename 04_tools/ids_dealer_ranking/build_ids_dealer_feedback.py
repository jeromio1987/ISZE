#!/usr/bin/env python3
"""IDS 2026 V2 — per-dealer feedback cards (tiered) + DB KPI context.

Outputs under IDS_2026/reports/dealer_feedback/:
  - index.html
  - {country}/{safe_dealer}.html
  - IDS_Dealer_Feedback_Register.xlsx
  - manifest.json

Tier C (default):
  - every scored dealer gets a short card
  - deep question list when any section is 'bad' OR total Δ country ≤ −10 pp

DB KPIs (fill / MOS / GPS €/UIO / PMS total capture) are distributor-level —
shown as context for the country pack, never as a dealer-owned score.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from build_ids_kaizen_full_study import extract_worst_questions
from build_ids_parts_kaizen_study import (
    COUNTRY_MAP,
    load_gps_2025,
    load_kpi_fill_mos,
    load_pms_db_2025,
)
from ids_paths import DATA_ROOT, IDS_RESULT_REPORTS_DIR
from ids_report_extract import build_dashboard_payload

OUT_DIR = DATA_ROOT / "reports" / "dealer_feedback"
DB_POSTURE_PAYLOAD = DATA_ROOT / "reports" / "kaizen_db_posture" / "study_payload.json"
SECTIONS = ("A", "B", "C", "D", "E")
SECTION_SHORT = {
    "A": "Premises",
    "B": "Organisation",
    "C": "Service",
    "D": "Parts",
    "E": "Vehicle sales",
}

BANDS = {
    "good_min_pct": 0.80,
    "medium_min_pct": 0.60,
    "near_country_pp": 0.05,
    "weak_gap_pp": -0.10,
}

SKIP_COUNTRIES = frozenset({"BENELUX"})  # rollup duplicate of BE+NL


def _pct(v: float | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v * 100:.1f}%"


def _pp(v: float | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v * 100:+.1f} pp"


def _eur(v: float | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"€{v:,.0f}"


def band_for(pct: float | None, country_avg: float | None) -> str | None:
    if pct is None:
        return None
    gap = (pct - country_avg) if country_avg is not None else None
    if gap is not None and gap <= BANDS["weak_gap_pp"]:
        return "bad"
    if pct >= BANDS["good_min_pct"] and (country_avg is None or pct >= country_avg):
        return "good"
    if pct < BANDS["medium_min_pct"] and (country_avg is None or pct < country_avg):
        return "bad"
    if gap is not None and abs(gap) <= BANDS["near_country_pp"]:
        return "medium"
    if BANDS["medium_min_pct"] <= pct < BANDS["good_min_pct"]:
        return "medium"
    if country_avg is not None and pct < country_avg:
        return "bad"
    if pct >= BANDS["good_min_pct"]:
        return "good"
    return "medium"


def band_label(b: str | None) -> str:
    return {"good": "Good", "medium": "Medium", "bad": "Bad"}.get(b or "", "—")


def safe_name(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", name.strip(), flags=re.UNICODE)
    return s.strip("_")[:80] or "dealer"


def load_db_kpi_by_country() -> dict[str, dict[str, Any]]:
    """Map IDS country → DB KPI context (same for all dealers in that pack)."""
    pms = load_pms_db_2025()
    gps = load_gps_2025()
    kpi = load_kpi_fill_mos()
    out: dict[str, dict[str, Any]] = {}
    for country, meta in COUNTRY_MAP.items():
        prism = meta.get("prism")
        kpi_name = meta.get("kpi")
        row: dict[str, Any] = {
            "prism": prism,
            "kpi_name": kpi_name,
            "note": meta.get("note") or "",
            "pms_capture_total": None,
            "gps_spu_eur": None,
            "gps_capture_vs_max": None,
            "gps_traffic": None,
            "kpi_fill_rate": None,
            "kpi_mos_days": None,
            "kpi_spu_eur": None,
            "archetype": None,
            "thesis": None,
            "ask_1": None,
            "ask_2": None,
            "dealer_cap_ask": None,
        }
        if prism and prism in pms:
            v = pms[prism].get("pms_capture_total")
            row["pms_capture_total"] = None if v is None or (isinstance(v, float) and math.isnan(v)) else v
        if prism and prism in gps:
            row["gps_spu_eur"] = gps[prism].get("gps_spu_eur")
            row["gps_capture_vs_max"] = gps[prism].get("gps_capture_vs_max")
            row["gps_traffic"] = gps[prism].get("traffic_light")
        if kpi_name and kpi_name in kpi:
            row["kpi_fill_rate"] = kpi[kpi_name].get("kpi_fill_rate")
            row["kpi_mos_days"] = kpi[kpi_name].get("kpi_mos_days")
            row["kpi_spu_eur"] = kpi[kpi_name].get("kpi_spu_eur")
        out[country] = row

    # Merge Kaizen DB posture asks / thesis (yesterday's pack)
    asks = load_db_posture_asks()
    for country, meta in asks.items():
        if country not in out:
            out[country] = {
                "prism": None,
                "kpi_name": None,
                "note": "",
                "pms_capture_total": None,
                "gps_spu_eur": None,
                "gps_traffic": None,
                "kpi_fill_rate": None,
                "kpi_mos_days": None,
                "kpi_spu_eur": None,
            }
        out[country].update(meta)
    return out


def load_db_posture_asks() -> dict[str, dict[str, Any]]:
    """Load ask_1 / ask_2 / thesis from kaizen_db_posture study_payload.json."""
    if not DB_POSTURE_PAYLOAD.is_file():
        return {}
    try:
        payload = json.loads(DB_POSTURE_PAYLOAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for card in payload.get("db_cards") or []:
        country = card.get("ids_country")
        if not country:
            continue
        out[country] = {
            "archetype": card.get("archetype"),
            "thesis": card.get("thesis"),
            "ask_1": card.get("ask_1"),
            "ask_2": card.get("ask_2"),
            # CAP example asks keyed later by dealer name
            "_cap_examples": [],
        }
    # Dealer-specific CAP asks from the D vs C split examples
    for ex in (payload.get("cap_split") or {}).get("examples") or []:
        c = ex.get("country")
        if not c or c not in out:
            continue
        out[c].setdefault("_cap_examples", []).append(
            {
                "name": ex.get("name") or "",
                "cap_type": ex.get("cap_type"),
                "ask": ex.get("ask"),
            }
        )
    return out


def dealer_cap_ask(db_kpi: dict[str, Any] | None, dealer_name: str) -> str | None:
    if not db_kpi:
        return None
    needle = (dealer_name or "").casefold()
    for ex in db_kpi.get("_cap_examples") or []:
        nm = (ex.get("name") or "").casefold()
        if nm and (nm == needle or needle in nm or nm in needle):
            return ex.get("ask")
    return None


def section_rows(dealer: dict) -> list[dict[str, Any]]:
    rows = []
    for sid in SECTIONS:
        s = (dealer.get("sections") or {}).get(sid) or {}
        pct = s.get("pct")
        c_avg = s.get("country_avg_pct")
        n_avg = s.get("network_avg_pct")
        gap = (pct - c_avg) if pct is not None and c_avg is not None else None
        rows.append(
            {
                "id": sid,
                "label": SECTION_SHORT[sid],
                "pct": pct,
                "country_avg": c_avg,
                "network_avg": n_avg,
                "gap": gap,
                "band": band_for(pct, c_avg),
            }
        )
    return rows


def needs_deep(dealer: dict, rows: list[dict]) -> bool:
    if any(r["band"] == "bad" for r in rows):
        return True
    tot = dealer.get("total_pct")
    cavg = dealer.get("country_avg_pct")
    if tot is not None and cavg is not None and (tot - cavg) <= BANDS["weak_gap_pp"]:
        return True
    return False


def radar_svg(dealer: dict, country: str, network: dict, rows: list[dict]) -> str:
    """Inline SVG spider with weak wedges + dealer / country / network."""
    ids = list(SECTIONS)
    n = len(ids)
    W, H, cx, cy, R = 360, 360, 180, 180, 125
    dv = [((dealer.get("sections") or {}).get(s) or {}).get("pct") for s in ids]
    cv = [((dealer.get("sections") or {}).get(s) or {}).get("country_avg_pct") for s in ids]
    nv = [(network.get("sections_pct") or {}).get(s) for s in ids]
    weak = [i for i, r in enumerate(rows) if r["band"] == "bad"]

    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img">']
    for t in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for i in range(n):
            a = -math.pi / 2 + (2 * math.pi * i) / n
            pts.append(f"{cx + R * t * math.cos(a):.1f},{cy + R * t * math.sin(a):.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#d4dae3" stroke-width="1"/>')
    for i, sid in enumerate(ids):
        a = -math.pi / 2 + (2 * math.pi * i) / n
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{cx + R * math.cos(a):.1f}" y2="{cy + R * math.sin(a):.1f}" stroke="#d4dae3"/>'
        )
        lx = cx + (R + 18) * math.cos(a)
        ly = cy + (R + 18) * math.sin(a)
        anchor = "middle" if abs(math.cos(a)) < 0.1 else ("start" if math.cos(a) > 0 else "end")
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
            f'font-size="11" font-weight="600" fill="#1a2744">{sid}</text>'
        )

    half = math.pi / n
    for i in weak:
        a = -math.pi / 2 + (2 * math.pi * i) / n
        xL, yL = cx + R * math.cos(a - half), cy + R * math.sin(a - half)
        xR, yR = cx + R * math.cos(a + half), cy + R * math.sin(a + half)
        parts.append(
            f'<polygon points="{cx},{cy} {xL:.1f},{yL:.1f} {xR:.1f},{yR:.1f}" fill="#1a2744" opacity="0.30"/>'
        )
        tx, ty = cx + R * 0.52 * math.cos(a), cy + R * 0.52 * math.sin(a)
        parts.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="9" font-weight="700" fill="#fff">Weak</text>'
        )

    def poly(vals: list[float | None], color: str, fill: str, width: float, dash: str = "") -> None:
        pts = []
        for i, v in enumerate(vals):
            vv = max(0.0, min(1.0, v or 0.0))
            a = -math.pi / 2 + (2 * math.pi * i) / n
            pts.append(f"{cx + R * vv * math.cos(a):.1f},{cy + R * vv * math.sin(a):.1f}")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{color}" '
            f'stroke-width="{width}"{dash_attr}/>'
        )

    poly(cv, "#1a2744", "none", 2, "6 4")
    poly(nv, "#6b7a90", "none", 1.5, "2 3")
    poly(dv, "#c45c3e", "rgba(196,92,62,0.15)", 2.5)
    parts.append(
        f'<text x="{cx}" y="{H - 6}" text-anchor="middle" font-size="9" fill="#6b7a90">'
        f"Dealer vs {escape(country)} avg vs network · weak wedges = bad</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def render_card(
    dealer: dict,
    *,
    country: str,
    network: dict,
    db_kpi: dict[str, Any] | None,
    deep: bool,
    gaps: list[dict],
    strengths_q: list[dict],
    built_at: str,
) -> str:
    rows = section_rows(dealer)
    tot = dealer.get("total_pct")
    cavg = dealer.get("country_avg_pct")
    navg = network.get("total_pct")
    name = dealer.get("name") or ""
    strengths = sorted([r for r in rows if r["gap"] is not None and r["gap"] > 0], key=lambda r: -r["gap"])[:3]
    weaks = sorted([r for r in rows if r["gap"] is not None and r["gap"] < 0], key=lambda r: r["gap"])[:3]

    db_block = ""
    cap_ask = dealer_cap_ask(db_kpi, name) if db_kpi else None
    if db_kpi and (
        db_kpi.get("kpi_name")
        or db_kpi.get("prism")
        or db_kpi.get("ask_1")
        or db_kpi.get("thesis")
    ):
        fill = db_kpi.get("kpi_fill_rate")
        # KPI fill often stored as 0–1 or 0–100
        fill_s = "—"
        if isinstance(fill, (int, float)):
            fill_s = f"{fill * 100:.1f}%" if fill <= 1.5 else f"{fill:.1f}%"
        mos = db_kpi.get("kpi_mos_days")
        mos_s = f"{mos:.0f}d" if isinstance(mos, (int, float)) else "—"
        arch = db_kpi.get("archetype")
        thesis = db_kpi.get("thesis")
        ask1 = db_kpi.get("ask_1")
        ask2 = db_kpi.get("ask_2")
        asks_html = ""
        if thesis or ask1 or ask2 or cap_ask:
            arch_badge = (
                f'<span class="badge">{escape(str(arch))}</span>' if arch else ""
            )
            lis = ""
            if ask1:
                lis += f"<li>{escape(str(ask1))}</li>"
            if ask2:
                lis += f"<li>{escape(str(ask2))}</li>"
            if cap_ask:
                lis += f"<li><em>Dealer CAP:</em> {escape(str(cap_ask))}</li>"
            asks_html = f"""
          <div class="asks">
            <h3>DB Kaizen asks {arch_badge}</h3>
            {f'<p class="thesis">{escape(str(thesis))}</p>' if thesis else ""}
            <ol>{lis}</ol>
          </div>"""
        db_block = f"""
        <div class="card db">
          <h2>DB KPI context <span class="badge">distributor-level — not this dealer</span></h2>
          <p class="hint">{escape(str(db_kpi.get("kpi_name") or db_kpi.get("prism") or country))}
          {" · " + escape(db_kpi.get("note")) if db_kpi.get("note") else ""}</p>
          <div class="stats">
            <div class="stat"><strong>{fill_s}</strong><span>KPI first fill</span></div>
            <div class="stat"><strong>{mos_s}</strong><span>KPI MOS</span></div>
            <div class="stat"><strong>{_pct(db_kpi.get("gps_capture_vs_max")) if db_kpi.get("gps_capture_vs_max") is not None else _eur(db_kpi.get("gps_spu_eur"))}</strong><span>{"GPS capture % 2025" if db_kpi.get("gps_capture_vs_max") is not None else "GPS €/UIO 2025"}</span></div>
            <div class="stat"><strong>{_pct(db_kpi.get("pms_capture_total"))}</strong><span>PMS total capture 2025</span></div>
          </div>
          {asks_html}
        </div>"""
    else:
        db_block = """
        <div class="card db">
          <h2>DB KPI context</h2>
          <p class="hint">No KPI Master / GPS / PMS join mapped for this IDS country pack yet.</p>
        </div>"""

    sec_table = "".join(
        f"<tr><td><strong>{r['id']}</strong> {escape(r['label'])}</td>"
        f"<td class='num'>{_pct(r['pct'])}</td>"
        f"<td class='num'>{_pct(r['country_avg'])}</td>"
        f"<td class='num'>{_pct(r['network_avg'])}</td>"
        f"<td class='num'>{_pp(r['gap'])}</td>"
        f"<td><span class='band {r['band'] or ''}'>{band_label(r['band'])}</span></td></tr>"
        for r in rows
    )

    def q_rows(items: list[dict], empty: str) -> str:
        if not items:
            return f"<tr><td colspan='5'>{escape(empty)}</td></tr>"
        out = []
        for g in items:
            if g.get("error"):
                continue
            out.append(
                "<tr>"
                f"<td><strong>{escape(str(g.get('ref') or ''))}</strong></td>"
                f"<td>{escape(str(g.get('section') or ''))}</td>"
                f"<td class='q'>{escape(str(g.get('text') or '')[:140])}</td>"
                f"<td class='num'>{_pct(g.get('pct'))}</td>"
                f"<td class='num'>{g.get('gap_pts') if g.get('gap_pts') is not None else '—'}</td>"
                "</tr>"
            )
        return "".join(out) or f"<tr><td colspan='5'>{escape(empty)}</td></tr>"

    deep_note = (
        "<p class='hint'>Deep pack — section bad and/or total ≥10 pp below country.</p>"
        if deep
        else "<p class='hint'>Short pack — no bad section trigger; question list limited.</p>"
    )

    strength_li = "".join(
        f"<li><strong>{r['id']}</strong> {_pp(r['gap'])} vs country · {band_label(r['band'])}</li>"
        for r in strengths
    ) or "<li>No section above country average.</li>"
    weak_li = "".join(
        f"<li><strong>{r['id']}</strong> {_pp(r['gap'])} vs country · {band_label(r['band'])}</li>"
        for r in weaks
    ) or "<li>No section below country average.</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>IDS feedback — {escape(name)} ({escape(country)})</title>
<style>
:root {{ --navy:#1a2744; --terracotta:#c45c3e; --good:#2d8a5e; --amber:#c48a1a; --bad:#c45c3e; --bg:#f4f6f9; --card:#fff; --muted:#6b7a90; --mid:#d4dae3; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",system-ui,sans-serif; background:var(--bg); color:var(--navy); line-height:1.45; }}
header {{ background:linear-gradient(135deg,var(--navy),#2d3f5c); color:#fff; padding:1.1rem 1.4rem; }}
header h1 {{ margin:0 0 .2rem; font-size:1.25rem; }}
header p {{ margin:0; opacity:.85; font-size:.88rem; }}
main {{ max-width:980px; margin:0 auto; padding:1rem 1.2rem 2rem; }}
.card {{ background:var(--card); border-radius:10px; padding:1rem 1.1rem; margin-bottom:1rem; box-shadow:0 1px 4px rgba(26,39,68,.05); }}
.card h2 {{ margin:0 0 .6rem; font-size:1.02rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:.6rem; }}
.stat {{ background:#f8fafc; border-left:4px solid var(--terracotta); border-radius:8px; padding:.65rem .75rem; }}
.stat strong {{ display:block; font-size:1.15rem; }}
.stat span {{ font-size:.75rem; color:var(--muted); }}
.badge {{ font-size:.65rem; background:#fff3e8; color:var(--terracotta); border-radius:4px; padding:.1rem .35rem; font-weight:600; }}
.band {{ display:inline-block; font-size:.68rem; font-weight:700; border-radius:4px; padding:.12rem .4rem; text-transform:uppercase; }}
.band.good {{ background:#e5f4ec; color:var(--good); }}
.band.medium {{ background:#f8efd9; color:var(--amber); }}
.band.bad {{ background:#f8e6e1; color:var(--bad); }}
.split {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
@media (max-width:800px) {{ .split {{ grid-template-columns:1fr; }} }}
table.data {{ width:100%; border-collapse:collapse; font-size:.82rem; }}
table.data th, table.data td {{ padding:.35rem .45rem; border-bottom:1px solid var(--mid); text-align:left; vertical-align:top; }}
table.data th {{ color:var(--muted); font-size:.7rem; text-transform:uppercase; }}
table.data td.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
table.data td.q {{ color:var(--muted); font-size:.78rem; }}
.hint {{ font-size:.85rem; color:var(--muted); margin:0 0 .6rem; }}
.callouts {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
.callouts ul {{ margin:0; padding-left:1.1rem; font-size:.88rem; }}
.callouts h3 {{ margin:0 0 .4rem; font-size:.95rem; }}
.callouts .good h3 {{ color:var(--good); }}
.callouts .bad h3 {{ color:var(--bad); }}
.radar {{ max-width:360px; margin:0 auto; }}
.asks {{ margin-top:.85rem; padding-top:.75rem; border-top:1px solid var(--mid); }}
.asks h3 {{ margin:0 0 .4rem; font-size:.92rem; }}
.asks .thesis {{ font-size:.88rem; color:var(--navy); margin:0 0 .5rem; }}
.asks ol {{ margin:0; padding-left:1.2rem; font-size:.88rem; }}
.asks li {{ margin:.35rem 0; }}
footer {{ text-align:center; font-size:.75rem; color:var(--muted); padding:1rem; }}
@media print {{ body {{ background:#fff; }} .card {{ box-shadow:none; border:1px solid #ddd; }} }}
</style>
</head>
<body>
<header>
  <h1>{escape(name)} · {escape(country)}</h1>
  <p>IDS 2026 dealer feedback · {"deep" if deep else "short"} · built {escape(built_at)}</p>
</header>
<main>
  <div class="card">
    <div class="stats">
      <div class="stat"><strong>{_pct(tot)}</strong><span>Dealer total</span></div>
      <div class="stat"><strong>{_pct(cavg)}</strong><span>{escape(country)} avg</span></div>
      <div class="stat"><strong>{_pct(navg)}</strong><span>Network avg</span></div>
      <div class="stat"><strong>{_pp((tot - cavg) if tot is not None and cavg is not None else None)}</strong><span>Δ vs country</span></div>
      <div class="stat"><strong>{_pp((tot - navg) if tot is not None and navg is not None else None)}</strong><span>Δ vs network</span></div>
    </div>
  </div>

  {db_block}

  <div class="split">
    <div class="card">
      <h2>Profile vs benchmarks</h2>
      <div class="radar">{radar_svg(dealer, country, network, rows)}</div>
    </div>
    <div class="card">
      <h2>Sections A–E</h2>
      <table class="data"><thead><tr><th>Section</th><th class="num">Dealer</th><th class="num">Country</th><th class="num">Network</th><th class="num">Δ</th><th>Band</th></tr></thead>
      <tbody>{sec_table}</tbody></table>
    </div>
  </div>

  <div class="callouts">
    <div class="card good"><h3>Strengths (good)</h3><ul>{strength_li}</ul></div>
    <div class="card bad"><h3>Weak points (bad)</h3><ul>{weak_li}</ul></div>
  </div>

  <div class="card">
    <h2>Question focus</h2>
    {deep_note}
    <h3 style="font-size:.92rem;margin:.6rem 0 .35rem">Priority gaps</h3>
    <table class="data"><thead><tr><th>Ref</th><th>Sec</th><th>Question</th><th class="num">%</th><th class="num">Pts left</th></tr></thead>
    <tbody>{q_rows(gaps, "No scored question gaps extracted.")}</tbody></table>
    <h3 style="font-size:.92rem;margin:1rem 0 .35rem">Keep doing (relative highs)</h3>
    <table class="data"><thead><tr><th>Ref</th><th>Sec</th><th>Question</th><th class="num">%</th><th class="num">Pts left</th></tr></thead>
    <tbody>{q_rows(strengths_q, "No high-scoring questions listed.")}</tbody></table>
  </div>

  <div class="card">
    <h2>Next steps (visit notes)</h2>
    <p class="hint">Fill during DB / dealer meeting.</p>
    <ol>
      <li>_______________________________________________</li>
      <li>_______________________________________________</li>
      <li>_______________________________________________</li>
    </ol>
  </div>
</main>
<footer>IDS feedback V2 · offline HTML · print to PDF from browser</footer>
</body>
</html>
"""


def best_questions(country: str, name: str, *, top_n: int = 5) -> list[dict]:
    """Reuse worst extractor then flip sort for highs — cheap path via full list."""
    # extract_worst_questions returns lowest pct; for strengths call with large top_n and re-sort
    from build_ids_result_report import (
        COL_FIRST_DEALER,
        COL_MAX,
        COL_TEXT,
        QUESTION_RE,
        ROW_META_START,
        load_matrix_rows_from_sheet,
    )
    from ids_paths import result_report_path
    import xlrd

    path = result_report_path(country)
    if not path.is_file():
        # try exact label from report sheet names via discover
        return []
    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    col = None
    for c in range(COL_FIRST_DEALER, sh.ncols):
        nm = str(sh.cell_value(ROW_META_START, c) or "").strip()
        if nm.casefold() == name.casefold():
            col = c
            break
    if col is None:
        return []
    matrix = load_matrix_rows_from_sheet(sh)
    current_sec = None
    rows: list[dict] = []
    for row in matrix:
        ref = (row.ref or "").strip()
        if row.kind == "category":
            m = re.match(r"^([A-E])\.", ref, re.I)
            current_sec = m.group(1).upper() if m else None
            continue
        if row.kind != "question" or row.sheet_row is None:
            continue
        if not QUESTION_RE.match(ref):
            continue
        max_pts = row.max_points
        if max_pts is None:
            try:
                max_pts = float(sh.cell_value(row.sheet_row, COL_MAX) or 0) or 0.0
            except Exception:
                max_pts = 0.0
        try:
            score = float(sh.cell_value(row.sheet_row, col))
        except Exception:
            continue
        if max_pts <= 0:
            continue
        pct = score / max_pts
        text = row.text or str(sh.cell_value(row.sheet_row, COL_TEXT) or "")
        rows.append(
            {
                "ref": ref,
                "section": current_sec,
                "text": text[:200],
                "score": score,
                "max": max_pts,
                "pct": pct,
                "gap_pts": max_pts - score,
            }
        )
    rows.sort(key=lambda g: (-(g["pct"]), g["gap_pts"]))
    return rows[:top_n]


def write_register(path: Path, cards: list[dict]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Feedback"
    headers = [
        "country",
        "dealer",
        "tier",
        "total_pct",
        "country_avg_pct",
        "vs_country_pp",
        "weak_sections",
        "db_kpi_name",
        "kpi_fill_rate",
        "kpi_mos_days",
        "gps_spu_eur",
        "pms_capture_total",
        "db_archetype",
        "db_ask_1",
        "db_ask_2",
        "html_path",
    ]
    ws.append(headers)
    for c in headers:
        ws.cell(1, headers.index(c) + 1).font = Font(bold=True)
    fill_deep = PatternFill("solid", fgColor="F8E6E1")
    for row in cards:
        ws.append(
            [
                row["country"],
                row["name"],
                row["tier"],
                row.get("total_pct"),
                row.get("country_avg_pct"),
                row.get("vs_country_pp"),
                ",".join(row.get("weak_sections") or []),
                row.get("db_kpi_name"),
                row.get("kpi_fill_rate"),
                row.get("kpi_mos_days"),
                row.get("gps_spu_eur"),
                row.get("pms_capture_total"),
                row.get("db_archetype"),
                row.get("db_ask_1"),
                row.get("db_ask_2"),
                row.get("html_rel"),
            ]
        )
        if row["tier"] == "deep":
            for col in range(1, len(headers) + 1):
                ws.cell(ws.max_row, col).fill = fill_deep
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def write_index(path: Path, cards: list[dict], built_at: str) -> None:
    by_c: dict[str, list] = {}
    for c in cards:
        by_c.setdefault(c["country"], []).append(c)
    blocks = []
    for country in sorted(by_c):
        lis = "".join(
            f"<li><a href='{escape(x['html_rel'])}'>{escape(x['name'])}</a> "
            f"<span class='tier {x['tier']}'>{x['tier']}</span> "
            f"<small>{_pct(x.get('total_pct'))} · {_pp(x.get('vs_country_pp'))}</small></li>"
            for x in sorted(by_c[country], key=lambda z: (z.get("total_pct") is None, z.get("total_pct") or 0))
        )
        blocks.append(f"<h2>{escape(country)} <small>({len(by_c[country])})</small></h2><ul>{lis}</ul>")
    deep_n = sum(1 for c in cards if c["tier"] == "deep")
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>IDS dealer feedback index</title>
<style>
body{{font-family:Segoe UI,system-ui,sans-serif;max-width:900px;margin:1.5rem auto;padding:0 1rem;color:#1a2744}}
.tier{{font-size:.7rem;font-weight:700;text-transform:uppercase;border-radius:4px;padding:.1rem .35rem}}
.tier.deep{{background:#f8e6e1;color:#c45c3e}}
.tier.short{{background:#e5f4ec;color:#2d8a5e}}
h1{{font-size:1.3rem}} h2{{font-size:1.05rem;margin-top:1.4rem}}
small{{color:#6b7a90}}
</style></head>
<body>
<h1>IDS 2026 — Dealer feedback packs</h1>
<p>{len(cards)} cards · {deep_n} deep · built {escape(built_at)}</p>
<p>DB KPI metrics on each card are <strong>distributor-level</strong> context (fill / MOS / GPS / PMS), not dealer scores.</p>
{"".join(blocks)}
</body></html>"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=IDS_RESULT_REPORTS_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Optional cap for smoke tests")
    parser.add_argument("--country", type=str, default="", help="Only one country label")
    args = parser.parse_args()

    payload = build_dashboard_payload(args.reports_dir)
    if not payload.get("dealers"):
        print("No dealers in payload", file=sys.stderr)
        return 2

    db_by_c = load_db_kpi_by_country()
    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    cards_meta: list[dict] = []
    dealers = [
        d
        for d in payload["dealers"]
        if not d.get("totals_only")
        and d.get("country") not in SKIP_COUNTRIES
        and (not args.country or d.get("country") == args.country)
    ]
    dealers.sort(key=lambda d: (d.get("country") or "", d.get("name") or ""))
    if args.limit:
        dealers = dealers[: args.limit]

    network = payload.get("network") or {}
    for i, d in enumerate(dealers, 1):
        country = d["country"]
        name = d["name"]
        rows = section_rows(d)
        deep = needs_deep(d, rows)
        top_n = 8 if deep else 3
        gaps = extract_worst_questions(country, name, top_n=top_n)
        if gaps and gaps[0].get("error"):
            gaps = []
        highs = best_questions(country, name, top_n=3 if deep else 2)
        db = db_by_c.get(country)
        html = render_card(
            d,
            country=country,
            network=network,
            db_kpi=db,
            deep=deep,
            gaps=gaps,
            strengths_q=highs,
            built_at=built_at,
        )
        folder = out / country
        folder.mkdir(parents=True, exist_ok=True)
        fname = f"{safe_name(name)}.html"
        fpath = folder / fname
        fpath.write_text(html, encoding="utf-8")
        tot = d.get("total_pct")
        cavg = d.get("country_avg_pct")
        cards_meta.append(
            {
                "country": country,
                "name": name,
                "tier": "deep" if deep else "short",
                "total_pct": tot,
                "country_avg_pct": cavg,
                "vs_country_pp": (tot - cavg) if tot is not None and cavg is not None else None,
                "weak_sections": [r["id"] for r in rows if r["band"] == "bad"],
                "db_kpi_name": (db or {}).get("kpi_name"),
                "kpi_fill_rate": (db or {}).get("kpi_fill_rate"),
                "kpi_mos_days": (db or {}).get("kpi_mos_days"),
                "gps_spu_eur": (db or {}).get("gps_spu_eur"),
                "pms_capture_total": (db or {}).get("pms_capture_total"),
                "db_archetype": (db or {}).get("archetype"),
                "db_ask_1": (db or {}).get("ask_1"),
                "db_ask_2": (db or {}).get("ask_2"),
                "html_rel": f"{country}/{fname}",
            }
        )
        if i % 50 == 0 or i == len(dealers):
            print(f"  {i}/{len(dealers)} cards…")

    write_register(out / "IDS_Dealer_Feedback_Register.xlsx", cards_meta)
    write_index(out / "index.html", cards_meta, built_at)
    manifest = {
        "built_at": built_at,
        "card_count": len(cards_meta),
        "deep_count": sum(1 for c in cards_meta if c["tier"] == "deep"),
        "short_count": sum(1 for c in cards_meta if c["tier"] == "short"),
        "countries": sorted({c["country"] for c in cards_meta}),
        "db_kpi_note": "Distributor-level KPI/GPS/PMS on cards — not dealer-owned.",
        "bands": BANDS,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  cards: {manifest['card_count']} (deep {manifest['deep_count']} / short {manifest['short_count']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
