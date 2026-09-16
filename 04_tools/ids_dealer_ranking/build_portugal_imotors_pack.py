#!/usr/bin/env python3
"""Portugal-only IDS 2026 pack for Imotors meeting.

- Dealer compare HTML: Portugal dealers only; full-network averages retained as benchmark
- Ranking map workbook (+ optional approximate city map HTML)
- All Portugal dealer feedback fiches
- Locked GPS Capture = 63.3% (Jerome deck slide — do not use pipeline GPS)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from build_ids_dashboard import leaflet_css_block, leaflet_js_block, render_html
from build_ids_dealer_feedback import (
    best_questions,
    load_db_kpi_by_country,
    needs_deep,
    render_card,
    safe_name,
    section_rows,
    write_index,
    write_register,
)
from build_ids_kaizen_full_study import extract_worst_questions
from ids_dashboard_qa import format_qa_report, validate_dashboard_payload
from ids_dealer_geo import attach_geo_to_dealers, place_for_dealer
from ids_paths import DATA_ROOT, IDS_RESULT_REPORTS_DIR, ISZE_ROOT, RANKINGS_DIR
from ids_report_extract import build_dashboard_payload

# Locked slide figure (Genuine Parts Share / GPS Capture) — Portugal today.
PORTUGAL_GPS_CAPTURE_LOCKED = 0.633
PORTUGAL_GPS_CAPTURE_LABEL = "63.3%"
COUNTRY = "Portugal"


def _meeting_dir() -> Path:
    return ISZE_ROOT / "09_meetings" / "Imotors_Portugal_IDS_2026"


def filter_portugal_payload(full: dict[str, Any]) -> dict[str, Any]:
    """Keep Portugal dealers only; retain full-network averages as anonymous benchmark."""
    network = full.get("network") or {}
    dealers = [d for d in full.get("dealers") or [] if d.get("country") == COUNTRY]
    # Re-stamp network avgs (already on sections from full build; keep explicit)
    for d in dealers:
        for sid, sec in (d.get("sections") or {}).items():
            if isinstance(sec, dict):
                sec["network_avg_pct"] = (network.get("sections_pct") or {}).get(sid)

    profiles = full.get("country_profiles") or {}
    pt_profile = profiles.get(COUNTRY) or {
        "dealer_count": len(dealers),
        "total_pct": None,
        "sections_pct": {},
        "q_pct": None,
    }

    return {
        "countries": [COUNTRY],
        "sections": full.get("sections") or [],
        "questions": full.get("questions") or [],
        "dealers": dealers,
        "dealer_count": len(dealers),
        "country_count": 1,
        "country_profiles": {COUNTRY: pt_profile},
        "network": network,
        "bands": full.get("bands") or {},
        "scope": {
            "label": "Portugal only",
            "audience": "Imotors",
            "network_benchmark": "Full IDS 2026 network average (anonymous)",
            "network_dealer_count": network.get("dealer_count"),
        },
        "db_context": {
            "gps_capture": PORTUGAL_GPS_CAPTURE_LOCKED,
            "gps_capture_label": PORTUGAL_GPS_CAPTURE_LABEL,
            "gps_note": (
                "GPS Capture (genuine parts share capture) for Portugal: "
                f"{PORTUGAL_GPS_CAPTURE_LABEL} — locked meeting figure."
            ),
        },
    }


def _map_points(
    dealers: list[dict[str, Any]],
    *,
    country_avg_pct: float | None = None,
) -> list[dict[str, Any]]:
    """Ranking pins with dealer %, Portugal avg %, and delta (pp)."""
    ranked = sorted(
        [d for d in dealers if d.get("total_pct") is not None],
        key=lambda d: (-(d.get("total_pct") or 0), d.get("name") or ""),
    )
    points: list[dict[str, Any]] = []
    for i, d in enumerate(ranked, 1):
        geo = d.get("geo")
        if geo and geo.get("lat") is not None:
            lat, lon = geo["lat"], geo["lon"]
            place = geo.get("place")
            geo_label = geo.get("geo_label") or ""
        else:
            lat, lon, place, geo_label = place_for_dealer(
                d.get("name") or "",
                COUNTRY,
                allow_country_centre=False,
            )
        pct = d.get("total_pct")
        cavg = d.get("country_avg_pct")
        if cavg is None:
            cavg = country_avg_pct
        pct_disp = round(pct * 100, 1) if pct is not None else None
        cavg_disp = round(cavg * 100, 1) if cavg is not None else None
        delta_pp = (
            round((pct - cavg) * 100, 1)
            if pct is not None and cavg is not None
            else None
        )
        points.append(
            {
                "rank": i,
                "name": d.get("name"),
                "pct": pct_disp,
                "country_avg": cavg_disp,
                "delta_pp": delta_pp,
                "lat": lat,
                "lon": lon,
                "place": place,
                "geo_label": geo_label,
            }
        )
    return points


def _leaflet_map_script(
    points: list[dict[str, Any]],
    *,
    map_div_id: str = "pt-map",
    status_el_id: str = "pt-tile-status",
    auto_init: bool = False,
) -> str:
    """Client JS: Leaflet + OpenStreetMap pins; hover shows dealer score vs Portugal national average."""
    points_json = json.dumps(points, ensure_ascii=False)
    auto_flag = "true" if auto_init else "false"
    return f"""
{leaflet_js_block()}
<script>
(function () {{
  const POINTS = {points_json};
  const AUTO_INIT = {auto_flag};
  const statusEl = document.getElementById("{status_el_id}");
  const mapEl = document.getElementById("{map_div_id}");
  if (!mapEl) return;

  function tipHtml(p) {{
    const delta = p.delta_pp == null
      ? "—"
      : ((p.delta_pp > 0 ? "+" : "") + Number(p.delta_pp).toFixed(1) + " pp");
    const deltaCls = p.delta_pp == null ? "" : (p.delta_pp >= 0 ? "pos" : "neg");
    const place = p.place ? (" · " + p.place) : "";
    const pct = p.pct != null ? Number(p.pct).toFixed(1) + "%" : "—";
    const cavg = p.country_avg != null ? Number(p.country_avg).toFixed(1) + "%" : "—";
    return (
      '<p class="map-tip-title">#' + p.rank + " · " + p.name + "</p>" +
      '<p class="map-tip-meta">Dealer total score: <strong>' + pct + "</strong></p>" +
      '<p class="map-tip-meta">Portugal national average: <strong>' + cavg + "</strong></p>" +
      '<p class="map-tip-meta">Vs national average: <strong class="' + deltaCls + '">' +
      delta + "</strong></p>" +
      '<p class="map-tip-meta" style="margin-top:.35rem;font-size:.78rem">' +
      "Approx city centre" + place + " — not a surveyed street address</p>"
    );
  }}

  function initMap() {{
    if (typeof L === "undefined") {{
      if (statusEl) {{
        statusEl.textContent = "Leaflet failed to start from the bundled map library. Other compare tabs still work.";
        statusEl.classList.add("warn");
      }}
      mapEl.innerHTML = "<p style='padding:1rem;color:#9a3412'>Map library unavailable. Other compare tabs still work.</p>";
      return;
    }}
    if (window.__ptMap) return;

    const map = L.map("{map_div_id}", {{ scrollWheelZoom: true }});
    window.__ptMap = map;
    const offlineLayer = L.layerGroup().addTo(map);
    const gridStyle = {{ color: "#cdbf9f", weight: 1, opacity: 0.45, interactive: false }};
    L.rectangle([[-85, -180], [85, 180]], {{
      stroke: false,
      fillColor: "#f8f5ef",
      fillOpacity: 1,
      interactive: false,
    }}).addTo(offlineLayer);
    for (let lon = -32; lon <= -5; lon += 5) {{
      L.polyline([[32, lon], [43, lon]], gridStyle).addTo(offlineLayer);
    }}
    for (let lat = 33; lat <= 42; lat += 3) {{
      L.polyline([[lat, -32], [lat, -5]], gridStyle).addTo(offlineLayer);
    }}
    L.rectangle([[36.8, -9.6], [42.3, -6.0]], {{
      color: "#7f93ab",
      weight: 1.4,
      opacity: 0.75,
      fillColor: "#fffdf8",
      fillOpacity: 0.78,
      interactive: false,
    }}).addTo(offlineLayer);
    L.marker([39.5, -8.0], {{
      icon: L.divIcon({{ className: "offline-country-label", html: "Portugal", iconSize: [90, 16] }}),
      interactive: false,
    }}).addTo(offlineLayer);
    map.attributionControl.setPrefix("Leaflet");
    if (statusEl) {{
      statusEl.textContent = "Offline basemap · no external tile service · hover a pin for dealer score vs Portugal national average.";
      statusEl.classList.remove("warn");
    }}
    setTimeout(function () {{ map.invalidateSize(); }}, 200);

    const pinIcon = function (rank) {{
      return L.divIcon({{
        className: "",
        html: '<div class="rank-pin">' + rank + "</div>",
        iconSize: [26, 26],
        iconAnchor: [13, 13],
        popupAnchor: [0, -14],
      }});
    }};

    const latLngs = [];
    const mainland = [];
    POINTS.forEach(function (p) {{
      if (p.lat == null || p.lon == null) return;
      const ll = L.latLng(p.lat, p.lon);
      latLngs.push(ll);
      if (p.lon > -12) mainland.push(ll);
      const html = tipHtml(p);
      L.marker(ll, {{ icon: pinIcon(p.rank) }})
        .addTo(map)
        .bindTooltip(html, {{
          direction: "top",
          offset: [0, -12],
          opacity: 0.97,
          className: "pt-map-tooltip",
          sticky: false,
        }})
        .bindPopup(html);
    }});

    if (latLngs.length) {{
      const fit = mainland.length ? mainland : latLngs;
      map.fitBounds(L.latLngBounds(fit), {{ padding: [36, 36], maxZoom: 9 }});
      if (mainland.length && mainland.length < latLngs.length) {{
        baseStatus =
          "Offline basemap · mainland view; Açores pin(s) on map (zoom out / pan west). Hover a pin for score vs Portugal national average.";
        if (statusEl) statusEl.textContent = baseStatus;
      }}
    }} else {{
      map.setView([39.5, -8.0], 7);
      if (statusEl) {{
        statusEl.textContent = "No dealer coordinates available.";
        statusEl.classList.add("warn");
      }}
    }}
  }}

  function showMapTab() {{
    initMap();
    if (window.__ptMap) {{
      setTimeout(function () {{ window.__ptMap.invalidateSize(); }}, 80);
    }}
  }}

  document.querySelectorAll(".tab").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      if (btn.dataset.tab === "map") showMapTab();
    }});
  }});

  if (AUTO_INIT) {{
    showMapTab();
  }} else if (document.getElementById("panel-map") &&
      document.getElementById("panel-map").classList.contains("active")) {{
    showMapTab();
  }}
}})();
</script>
"""


def _strip_changelog_ui(html: str) -> str:
    """Remove Changelog tab/panel — Mode A client pack must not show agent update notes."""
    html = re.sub(
        r'\n?\s*<button class="tab" data-tab="changelog"[^>]*>\s*Changelog\s*</button>',
        "",
        html,
        count=1,
    )
    html = re.sub(
        r'\n?\s*<section id="panel-changelog" class="panel">.*?</section>\s*',
        "\n",
        html,
        count=1,
        flags=re.DOTALL,
    )
    return html


def render_portugal_html(payload: dict[str, Any], *, built_at: str) -> str:
    """Portugal / Imotors Mode A shell on top of the shared v1.2 template (map included)."""
    html = render_html(payload, built_at=built_at)
    html = html.replace(
        "<title>IDS 2026 — Dealer Compare</title>",
        "<title>IDS 2026 — Portugal dealer compare (Imotors)</title>",
    )
    # Template h1 may include a v1.2 span
    html = re.sub(
        r"<h1>IDS 2026 — Dealer comparison[^<]*(?:<span[^>]*>[^<]*</span>)?</h1>",
        "<h1>IDS 2026 — Portugal dealer comparison</h1>",
        html,
        count=1,
    )
    gps_note = (
        f"Portugal pack for Imotors · GPS Capture {PORTUGAL_GPS_CAPTURE_LABEL} "
        f"(genuine parts share capture — locked meeting figure) · "
        f"network avg from full IDS network ({payload.get('network', {}).get('dealer_count', '—')} dealers) · "
        f"Map tab (Leaflet)"
    )
    html = re.sub(
        r"<p>v1\.2 with map · sections A–E \+ questions · good / medium / bad · built [^<]+</p>",
        f"<p>{gps_note}</p>",
        html,
        count=1,
    )
    # Fallback if subtitle pattern drifted
    if PORTUGAL_GPS_CAPTURE_LABEL not in html.split("</header>", 1)[0]:
        html = html.replace(
            f"built {built_at}",
            gps_note,
            1,
        )

    # Retarget shared Map panel copy for Portugal / Imotors
    html = html.replace(
        "<h2>Network dealer map</h2>",
        "<h2>Portugal dealer map</h2>",
        1,
    )
    # Template v1.3+ map hint — name the Portugal benchmark explicitly.
    html = html.replace(
        "Pins are coloured by dealer total vs that country’s national average",
        "Pins are coloured by dealer total vs the Portugal national average",
    )
    html = html.replace(
        'aria-label="IDS network dealer interactive map"',
        'aria-label="Portugal dealer interactive map"',
        1,
    )

    # Shared IDS template may include an internal Changelog tab — strip for Imotors.
    html = _strip_changelog_ui(html)
    return html


def _place_from_name(
    name: str,
) -> tuple[float | None, float | None, str | None, str]:
    """Portugal city-only geo (no country-centre fallback)."""
    return place_for_dealer(name, COUNTRY, allow_country_centre=False)


def write_map_workbook(
    dealers: list[dict[str, Any]],
    out_xlsx: Path,
    *,
    network_total_pct: float | None = None,
) -> dict[str, Any]:
    """Ranking + Map sheets (B1-style map sheet pattern) with GPS footnote."""
    ranked = sorted(
        [d for d in dealers if d.get("total_pct") is not None],
        key=lambda d: (-(d.get("total_pct") or 0), d.get("name") or ""),
    )
    wb = Workbook()
    net_pct_disp = (
        round(network_total_pct * 100, 2) if network_total_pct is not None else None
    )

    # --- Ranking sheet ---
    ws = wb.active
    ws.title = "Ranking"
    headers = [
        "Rank",
        "Dealer",
        "Total %",
        "Total pts",
        "Country avg %",
        "Network avg %",
        "A Premises %",
        "B Organisation %",
        "C Service %",
        "D Parts %",
        "E Vehicle sales %",
    ]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1A2744")
        cell.alignment = Alignment(horizontal="center")

    for i, d in enumerate(ranked, 1):
        secs = d.get("sections") or {}

        def _sec(sid: str) -> float | None:
            v = (secs.get(sid) or {}).get("pct")
            return round(v * 100, 2) if v is not None else None

        ws.append(
            [
                i,
                d.get("name"),
                round((d.get("total_pct") or 0) * 100, 2),
                d.get("total"),
                round((d.get("country_avg_pct") or 0) * 100, 2)
                if d.get("country_avg_pct") is not None
                else None,
                net_pct_disp,
                _sec("A"),
                _sec("B"),
                _sec("C"),
                _sec("D"),
                _sec("E"),
            ]
        )

    # Footnotes
    note_row = len(ranked) + 3
    ws.cell(note_row, 1, "Notes")
    ws.cell(note_row, 1).font = Font(bold=True)
    ws.cell(
        note_row + 1,
        1,
        f"GPS Capture (genuine parts share capture) — Portugal: {PORTUGAL_GPS_CAPTURE_LABEL} (locked meeting figure).",
    )
    ws.cell(
        note_row + 2,
        1,
        "Network average columns / charts in the HTML compare use the full IDS 2026 network as an anonymous benchmark.",
    )
    ws.cell(note_row + 3, 1, "Mode A pack for Imotors — Portugal dealers only.")

    for col, width in zip("ABCDEFGHIJK", [8, 32, 12, 12, 14, 14, 12, 14, 12, 12, 14]):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"

    # --- Map sheet (inventory + place inference) ---
    ms = wb.create_sheet("Map", 0)
    map_headers = [
        "Rank",
        "Dealer",
        "Place (from name)",
        "Lat (approx)",
        "Lon (approx)",
        "Total %",
        "Geo source",
    ]
    ms.append(map_headers)
    for c in range(1, len(map_headers) + 1):
        cell = ms.cell(1, c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1A2744")

    geo_ok = 0
    geo_missing = 0
    for i, d in enumerate(ranked, 1):
        lat, lon, place, geo_label = _place_from_name(d.get("name") or "")
        if lat is not None:
            geo_ok += 1
            src = (
                "Approximate city centre — not a surveyed street address "
                f"({geo_label})"
            )
        else:
            geo_missing += 1
            src = "No place token / no dealer address file"
        ms.append(
            [
                i,
                d.get("name"),
                place,
                lat,
                lon,
                round((d.get("total_pct") or 0) * 100, 2),
                src,
            ]
        )

    foot = len(ranked) + 3
    ms.cell(foot, 1, "Map notes").font = Font(bold=True)
    ms.cell(
        foot + 1,
        1,
        f"GPS Capture (genuine parts share capture) — Portugal: {PORTUGAL_GPS_CAPTURE_LABEL} (locked meeting figure).",
    )
    ms.cell(
        foot + 2,
        1,
        "Coordinates are approximate city centres (from dealer names or the public Isuzu Portugal dealer directory). "
        "Not surveyed street addresses. Interactive HTML map uses Leaflet + OpenStreetMap tiles (needs internet).",
    )
    ms.cell(foot + 3, 1, f"Dealers with approx place: {geo_ok} · without: {geo_missing}")

    for col, width in zip("ABCDEFG", [8, 32, 22, 14, 14, 12, 55]):
        ms.column_dimensions[col].width = width
    ms.freeze_panes = "A2"

    # --- Cover / context ---
    cs = wb.create_sheet("Pack_context", 0)
    cs["A1"] = "IDS 2026 — Portugal (Imotors) pack"
    cs["A1"].font = Font(bold=True, size=14)
    cs["A3"] = "Country"
    cs["B3"] = COUNTRY
    cs["A4"] = "Dealers"
    cs["B4"] = len(ranked)
    cs["A5"] = "GPS Capture"
    cs["B5"] = PORTUGAL_GPS_CAPTURE_LABEL
    cs["C5"] = "Genuine parts share capture — locked meeting figure (do not use pipeline GPS)"
    cs["A6"] = "Network benchmark"
    cs["B6"] = "Full IDS 2026 network average (anonymous)"
    cs["A8"] = "Source ranking (reference)"
    cs["B8"] = str(RANKINGS_DIR / "Portugal_dealer_ranking.xlsx")
    cs.column_dimensions["A"].width = 28
    cs.column_dimensions["B"].width = 55
    cs.column_dimensions["C"].width = 70

    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)
    return {"geo_ok": geo_ok, "geo_missing": geo_missing, "dealer_count": len(ranked)}


def write_map_html(
    dealers: list[dict[str, Any]],
    out_html: Path,
    *,
    country_avg_pct: float | None = None,
) -> None:
    """Standalone Leaflet map (secondary). Primary map is the compare HTML Map tab."""
    points = _map_points(dealers, country_avg_pct=country_avg_pct)
    pinned = [pt for pt in points if pt["lat"] is not None]

    def _delta_cell(pt: dict[str, Any]) -> str:
        if pt.get("delta_pp") is None:
            return "—"
        v = pt["delta_pp"]
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.1f}"

    rows = "".join(
        f"<tr><td>{pt['rank']}</td><td>{_esc(pt['name'])}</td>"
        f"<td>{pt['pct'] if pt['pct'] is not None else '—'}%</td>"
        f"<td>{pt['country_avg'] if pt['country_avg'] is not None else '—'}%</td>"
        f"<td>{_delta_cell(pt)}</td>"
        f"<td>{_esc(pt['place'] or '—')}</td>"
        f"<td>{'Approx city' if pt['lat'] is not None else 'No geo'}</td></tr>"
        for pt in points
    )

    map_js = _leaflet_map_script(
        points,
        map_div_id="pt-map",
        status_el_id="tile-status",
        auto_init=True,
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>IDS 2026 — Portugal dealer map</title>
{leaflet_css_block()}
<style>
:root {{ --navy:#1a2744; --terracotta:#c45c3e; --bg:#f4f6f9; --card:#fff; --muted:#6b7a90; --mid:#d4dae3; --good:#2d8a5e; --bad:#c45c3e; }}
body {{ margin:0; font-family:"Segoe UI",system-ui,sans-serif; background:var(--bg); color:var(--navy); }}
header {{ background:linear-gradient(135deg,var(--navy),#2d3f5c); color:#fff; padding:1.1rem 1.4rem; }}
header h1 {{ margin:0 0 .25rem; font-size:1.25rem; }}
header p {{ margin:0; opacity:.85; font-size:.88rem; }}
main {{ max-width:1180px; margin:0 auto; padding:1rem 1.2rem 2rem; display:grid; gap:1rem; grid-template-columns:1.25fr 1fr; }}
@media (max-width:900px) {{ main {{ grid-template-columns:1fr; }} }}
.card {{ background:var(--card); border-radius:10px; padding:1rem; box-shadow:0 1px 4px rgba(26,39,68,.05); }}
.card h2 {{ margin:0 0 .6rem; font-size:1.02rem; }}
.hint {{ color:var(--muted); font-size:.85rem; margin:0 0 .75rem; }}
#pt-map {{ width:100%; height:560px; border-radius:8px; border:1px solid var(--mid); background:#f8f5ef; }}
.leaflet-container {{ font: inherit; background:#f8f5ef; }}
.rank-pin {{
  background: var(--terracotta); color:#fff; border:2px solid #fff;
  border-radius:50%; width:26px; height:26px; line-height:22px;
  text-align:center; font-size:11px; font-weight:700;
  box-shadow:0 1px 4px rgba(0,0,0,.35);
}}
.pt-map-tooltip {{
  background: #fff; border:1px solid var(--mid); border-radius:8px;
  box-shadow:0 4px 14px rgba(26,39,68,.18); padding:0; max-width:280px;
}}
.map-tip-title {{ font-weight:700; margin:0 0 .35rem; color:var(--navy); font-size:.92rem; }}
.map-tip-meta {{ margin:0.15rem 0; color:#54657a; font-size:.85rem; }}
.map-tip-meta .pos {{ color: var(--good); }}
.map-tip-meta .neg {{ color: var(--bad); }}
.tile-note {{ margin:.55rem 0 0; color:var(--muted); font-size:.78rem; }}
.tile-note.warn {{ color:#9a3412; }}
.offline-country-label {{
  color:#1a2744; font-size:12px; font-weight:800;
  text-shadow:0 1px 0 #fff, 1px 0 0 #fff, 0 -1px 0 #fff, -1px 0 0 #fff;
  white-space:nowrap; pointer-events:none;
}}
table {{ width:100%; border-collapse:collapse; font-size:.82rem; }}
th,td {{ padding:.35rem .4rem; border-bottom:1px solid var(--mid); text-align:left; }}
th {{ color:var(--muted); font-size:.72rem; text-transform:uppercase; }}
</style>
</head>
<body>
<header>
  <h1>IDS 2026 — Portugal dealer map</h1>
  <p>Imotors pack · GPS Capture {PORTUGAL_GPS_CAPTURE_LABEL} (genuine parts share capture — locked meeting figure) · hover pins for dealer score vs Portugal national average · primary map is in the dealer compare Map tab</p>
</header>
<main>
  <div class="card">
    <h2>Network map</h2>
    <p class="hint">Hover a pin for that dealer’s total score vs the Portugal national average (delta in pp). Pins are approximate city centres — not surveyed street addresses. The map library and basemap are bundled in this file; no external map tile service is required.</p>
    <div id="pt-map" role="img" aria-label="Portugal dealer interactive map"></div>
    <p class="tile-note" id="tile-status">Drawing offline map…</p>
  </div>
  <div class="card">
    <h2>Ranking</h2>
    <p class="hint">{len(points)} Portugal dealers · {len(pinned)} pinned on map · network average still used in the compare HTML as an anonymous benchmark.</p>
    <table>
      <thead><tr><th>#</th><th>Dealer</th><th>Total</th><th>PT national avg</th><th>Δ pp</th><th>Place</th><th>Geo</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</main>
{map_js}
</body>
</html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")



def _esc(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_fiches(
    payload: dict[str, Any],
    out_dir: Path,
    *,
    built_at: str,
) -> list[dict[str, Any]]:
    db_by_c = load_db_kpi_by_country()
    # Lock GPS for Portugal — override pipeline / Claude recalculated values
    db = dict(db_by_c.get(COUNTRY) or {})
    db["gps_capture_vs_max"] = PORTUGAL_GPS_CAPTURE_LOCKED
    db["gps_spu_eur"] = None  # prefer capture % display over €/UIO
    db["note"] = (
        (db.get("note") or "")
        + ("; " if db.get("note") else "")
        + f"GPS Capture locked at {PORTUGAL_GPS_CAPTURE_LABEL} (meeting figure)"
    ).strip("; ")
    db_by_c[COUNTRY] = db

    dealers = [
        d
        for d in payload["dealers"]
        if not d.get("totals_only") and d.get("country") == COUNTRY
    ]
    dealers.sort(key=lambda d: d.get("name") or "")
    network = payload.get("network") or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    cards_meta: list[dict[str, Any]] = []

    for d in dealers:
        name = d["name"]
        rows = section_rows(d)
        deep = needs_deep(d, rows)
        top_n = 8 if deep else 3
        gaps = extract_worst_questions(COUNTRY, name, top_n=top_n)
        if gaps and gaps[0].get("error"):
            gaps = []
        highs = best_questions(COUNTRY, name, top_n=3 if deep else 2)
        html = render_card(
            d,
            country=COUNTRY,
            network=network,
            db_kpi=db,
            deep=deep,
            gaps=gaps,
            strengths_q=highs,
            built_at=built_at,
        )
        # Ensure Mode A GPS label is explicit on card
        html = html.replace(
            "GPS capture % 2025",
            "GPS Capture (genuine parts share)",
        )
        folder = out_dir / COUNTRY
        folder.mkdir(parents=True, exist_ok=True)
        fname = f"{safe_name(name)}.html"
        (folder / fname).write_text(html, encoding="utf-8")
        tot = d.get("total_pct")
        cavg = d.get("country_avg_pct")
        cards_meta.append(
            {
                "country": COUNTRY,
                "name": name,
                "tier": "deep" if deep else "short",
                "total_pct": tot,
                "country_avg_pct": cavg,
                "vs_country_pp": (tot - cavg) if tot is not None and cavg is not None else None,
                "weak_sections": [r["id"] for r in rows if r["band"] == "bad"],
                "db_kpi_name": db.get("kpi_name"),
                "kpi_fill_rate": db.get("kpi_fill_rate"),
                "kpi_mos_days": db.get("kpi_mos_days"),
                "gps_spu_eur": None,
                "gps_capture_vs_max": PORTUGAL_GPS_CAPTURE_LOCKED,
                "pms_capture_total": db.get("pms_capture_total"),
                "db_archetype": db.get("archetype"),
                "db_ask_1": db.get("ask_1"),
                "db_ask_2": db.get("ask_2"),
                "html_rel": f"{COUNTRY}/{fname}",
            }
        )

    write_register(out_dir / "IDS_Dealer_Feedback_Register_Portugal.xlsx", cards_meta)
    write_index(out_dir / "index.html", cards_meta, built_at)
    manifest = {
        "built_at": built_at,
        "card_count": len(cards_meta),
        "deep_count": sum(1 for c in cards_meta if c["tier"] == "deep"),
        "short_count": sum(1 for c in cards_meta if c["tier"] == "short"),
        "countries": [COUNTRY],
        "gps_capture_locked": PORTUGAL_GPS_CAPTURE_LOCKED,
        "gps_capture_label": PORTUGAL_GPS_CAPTURE_LABEL,
        "gps_note": "Locked meeting figure — genuine parts share / GPS Capture. Do not use pipeline GPS.",
        "db_kpi_note": "Distributor-level KPI/GPS/PMS on cards — not dealer-owned.",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return cards_meta


def zip_fiches(fiches_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in fiches_dir.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(fiches_dir).as_posix())


def write_readme(pack_dir: Path, *, dealer_count: int, geo: dict[str, Any]) -> None:
    text = f"""# IDS 2026 — Portugal pack (Imotors)

Meeting pack for Imotors / Portugal. **Mode A** (external language).

## Contents

| File | Role |
|------|------|
| `IDS_2026_dealer_compare_Portugal.html` | Dealer compare — **Portugal dealers only**; **Map tab** (Leaflet) with hover = dealer score vs Portugal national average; full-network averages kept as anonymous benchmark |
| `IDS_2026_Portugal_dealer_map.xlsx` | Ranking + Map sheets |
| `IDS_2026_Portugal_dealer_map.html` | Standalone copy of the map (secondary) — same hover vs national average |
| `dealer_fiches/` | One feedback card per Portugal dealer + index |
| `dealer_fiches_Portugal.zip` | Same fiches, zipped for hand-off |

## Locked figure

**GPS Capture = {PORTUGAL_GPS_CAPTURE_LABEL}**  
(Genuine parts share / GPS Capture — Portugal today, locked meeting slide figure. Do not replace with pipeline or recalculated GPS.)

## Coverage

- Dealers: **{dealer_count}**
- Approx place on map: {geo.get("geo_ok")} · without place token: {geo.get("geo_missing")}
- Map base layer: bundled Leaflet + offline grid / country label layer (no external tile service).
- Pins: approximate city centres from dealer names and the public Isuzu Portugal dealer directory — not surveyed street addresses.

## Network average

Charts and heatmap “vs network avg” use the **full IDS 2026 network** average. Other countries’ dealers are **not** listed in filters or rows.
"""
    (pack_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=IDS_RESULT_REPORTS_DIR)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--skip-qa", action="store_true")
    args = parser.parse_args()

    pack = args.out_dir or _meeting_dir()
    pack.mkdir(parents=True, exist_ok=True)

    print("Building full network payload…")
    full = build_dashboard_payload(args.reports_dir)
    payload = filter_portugal_payload(full)
    if not payload["dealers"]:
        print("No Portugal dealers found", flush=True)
        return 2

    # QA on Portugal-only payload (heatmap still needs network stamps)
    qa_errors = validate_dashboard_payload(payload)
    print(format_qa_report(payload, qa_errors))
    if qa_errors and not args.skip_qa:
        print("QA failed — pass --skip-qa to force", flush=True)
        return 3

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    payload["built_at"] = built_at
    # Portugal pins: city / directory only (no country-centre scatter)
    attach_geo_to_dealers(payload["dealers"], allow_country_centre=False)

    compare_path = pack / "IDS_2026_dealer_compare_Portugal.html"
    html = render_portugal_html(payload, built_at=built_at)
    compare_path.write_text(html, encoding="utf-8")
    print(f"Wrote {compare_path}")

    # Mirror into 02_dashboards/ids for local browsing
    dash_mirror = ISZE_ROOT / "02_dashboards" / "ids" / compare_path.name
    dash_mirror.parent.mkdir(parents=True, exist_ok=True)
    dash_mirror.write_text(html, encoding="utf-8")
    print(f"Mirrored {dash_mirror}")

    map_xlsx = pack / "IDS_2026_Portugal_dealer_map.xlsx"
    geo = write_map_workbook(
        payload["dealers"],
        map_xlsx,
        network_total_pct=(payload.get("network") or {}).get("total_pct"),
    )
    print(f"Wrote {map_xlsx} (geo approx {geo['geo_ok']}/{geo['dealer_count']})")

    map_html = pack / "IDS_2026_Portugal_dealer_map.html"
    pt_avg = ((payload.get("country_profiles") or {}).get(COUNTRY) or {}).get("total_pct")
    write_map_html(payload["dealers"], map_html, country_avg_pct=pt_avg)
    print(f"Wrote {map_html}")
    map_mirror = ISZE_ROOT / "02_dashboards" / "ids" / map_html.name
    map_mirror.write_text(map_html.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Mirrored {map_mirror}")

    fiches_dir = pack / "dealer_fiches"
    if fiches_dir.exists():
        shutil.rmtree(fiches_dir)
    cards = build_fiches(payload, fiches_dir, built_at=built_at)
    print(f"Wrote {len(cards)} fiches under {fiches_dir}")

    zip_path = pack / "dealer_fiches_Portugal.zip"
    zip_fiches(fiches_dir, zip_path)
    print(f"Wrote {zip_path}")

    write_readme(pack, dealer_count=len(payload["dealers"]), geo=geo)

    pack_zip = pack / "Imotors_Portugal_IDS_2026_pack.zip"
    if pack_zip.exists():
        pack_zip.unlink()
    with zipfile.ZipFile(pack_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "IDS_2026_dealer_compare_Portugal.html",
            "IDS_2026_Portugal_dealer_map.html",
            "IDS_2026_Portugal_dealer_map.xlsx",
            "README.md",
            "dealer_fiches_Portugal.zip",
        ):
            p = pack / name
            if p.is_file():
                zf.write(p, name)
        for p in (pack / "dealer_fiches").rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(pack).as_posix())
    print(f"Wrote {pack_zip}")

    # Confirm GPS wiring
    sample = (fiches_dir / COUNTRY / f"{safe_name(cards[0]['name'])}.html").read_text(
        encoding="utf-8"
    )
    gps_ok = "63.3%" in sample and "63.3%" in html
    map_ok = "leaflet" in map_html.read_text(encoding="utf-8").lower()
    compare_map_ok = (
        'data-tab="map"' in html
        and "Portugal national average" in html
        and ("window.__idsMap" in html or "function renderMap" in html)
        and "no external tile service" in html
        and "Weak sector" not in html
        and ">Weak</text>" not in html
    )
    changelog_gone = (
        'data-tab="changelog"' not in html
        and 'id="panel-changelog"' not in html
        and "Changelog" not in html
    )
    print(
        f"GPS Capture locked {PORTUGAL_GPS_CAPTURE_LABEL} wired: "
        f"compare={('63.3%' in html)} fiches={('63.3%' in sample)} map_readme=yes"
    )
    print(
        f"Map Leaflet wired: standalone={map_ok} embedded_compare={compare_map_ok} · "
        f"geo {geo['geo_ok']}/{geo['dealer_count']}"
    )
    print(f"Changelog stripped (Mode A): {changelog_gone}")
    print(f"Pack: {pack}")
    print(f"  dealers: {payload['dealer_count']}")
    print(f"  countries listed: {payload['countries']}")
    print(f"  network dealers (benchmark): {payload['network'].get('dealer_count')}")
    if not gps_ok:
        return 4
    if not map_ok:
        return 5
    if not compare_map_ok:
        return 6
    if not changelog_gone:
        return 7
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
