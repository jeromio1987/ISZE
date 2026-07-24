#!/usr/bin/env python3
"""IDS Section D × DB KPI/GPS/PMS correlation study + Wave-1 Kaizen pack.

Outputs under IDS_2026/reports/kaizen_parts/:
  - IDS_Parts_Kaizen_Study_2026.html  (self-contained)
  - IDS_Parts_Kaizen_Register.xlsx
  - study_payload.json
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import xlrd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from build_ids_result_report import (
    COL_FIRST_DEALER,
    COL_LABEL,
    COL_MAX,
    COL_TEXT,
    QUESTION_RE,
    ROW_META_START,
    load_matrix_rows_from_sheet,
)
from ids_kaizen_hygiene import dealers_for_stats, hygienic_country_profiles, is_rollup_country
from ids_paths import DATA_ROOT, IDS_RESULT_REPORTS_DIR
from ids_report_extract import build_dashboard_payload, discover_result_reports

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
KPI_MASTER = ISZE / "01_data" / "11_planning" / "KPI Master File june 2026.xlsx"
CHART_JS = ISZE / "09_meetings" / "Preparation Meetings" / "PMS_Top10" / "assets" / "chart.umd.min.js"
OUT_DIR = DATA_ROOT / "reports" / "kaizen_parts"

# IDS country label → PRISM / KPI join keys
COUNTRY_MAP: dict[str, dict[str, Any]] = {
    "BE": {"prism": "BELGIUM", "kpi": "IBX (BENELUX)", "note": "Benelux IBX"},
    "NL": {"prism": "BELGIUM", "kpi": "IBX (BENELUX)", "note": "NL dealers; PMS/GPS via BELGIUM/IBX"},
    "POLAND": {"prism": "POLAND", "kpi": "Isuzu Polska", "note": ""},
    "PETROS": {"prism": "GREECE", "kpi": "Petros Petropoulos", "note": ""},
    "RSA": {"prism": "NORWAY", "kpi": "RSA", "note": "RSA cluster; PMS proxy NORWAY (largest Nordic)"},
    "IUK": {"prism": "IUK", "kpi": "IUK", "note": ""},
    "ITUK": {"prism": "ITUK", "kpi": "ITUK", "note": "IDS totals-only — no Section D heatmap"},
    "ISRAEL": {
        "prism": "UMI",
        "kpi": "UMI",
        "note": "IDS Israel = UMI network only. UTI did not participate — never blend UTI+UMI.",
    },
    "MALTA": {"prism": "MALTA", "kpi": "GasanZammit", "note": ""},
    "CYPRUS": {"prism": "CYPRUS", "kpi": "Loutsios Group", "note": ""},
    "ROMANIA": {"prism": "ROMANIA", "kpi": "Isuzu Rom Auto", "note": ""},
    "PORTUGAL": {"prism": "PORTUGAL", "kpi": "Astara Portugal", "note": "KPI name may vary"},
    "HUNGARY": {"prism": "HUNGARY", "kpi": None, "note": "No KPI Master monthly row for Hungary"},
}

# Wave-1 shortlist preference (overridden if correlation study finds stronger cases)
PREFERRED_FOCUS = [
    ("IUK", "YORK VAN CENTRE LTD"),
    ("IUK", "Adam"),
    ("ROMANIA", "SIMODE CRAIOVA"),
    ("BE", "Garage Degroote"),
]


def _f(x: Any) -> float | None:
    if x is None or x == "":
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v):
        return None
    return v


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def load_pms_db_2025() -> dict[str, dict[str, float]]:
    path = DERIVED / "pms_capture_by_db_year.csv"
    exp_t: dict[str, float] = defaultdict(float)
    act_t: dict[str, float] = defaultdict(float)
    gap_t: dict[str, float] = defaultdict(float)
    exp_g: dict[str, float] = defaultdict(float)
    act_g: dict[str, float] = defaultdict(float)
    for row in csv_dict(path):
        if row.get("year") != "2025":
            continue
        db = row["distributor_code"]
        lt = (row.get("line_type") or "").lower()
        exp = _f(row.get("expected_qty")) or 0.0
        act = _f(row.get("actual_qty")) or 0.0
        gap = _f(row.get("revenue_gap_eur")) or 0.0
        if lt == "total":
            exp_t[db] += exp
            act_t[db] += act
            gap_t[db] += gap
        elif lt == "genuine":
            exp_g[db] += exp
            act_g[db] += act
    out: dict[str, dict[str, float]] = {}
    for db in set(exp_t) | set(exp_g):
        tot = (act_t[db] / exp_t[db]) if exp_t[db] > 0 else None
        gen = (act_g[db] / exp_g[db]) if exp_g[db] > 0 else None
        out[db] = {
            "pms_capture_total": tot if tot is not None else float("nan"),
            "pms_capture_genuine": gen if gen is not None else float("nan"),
            "pms_gap_eur": gap_t[db],
            "genuine_vs_total_pp": (
                (tot - gen) * 100 if tot is not None and gen is not None else float("nan")
            ),
        }
    return out


def load_gps_2025() -> dict[str, dict[str, Any]]:
    """GPS €/UIO for CY2025.

    Headline spend_per_unit_eur INCLUDES warranty parts (embedded in ERP genuine sales).
    Also expose ex-warranty SPU for comparison.
    """
    out: dict[str, dict[str, Any]] = {}
    for row in csv_dict(DERIVED / "gps_spu_by_distributor.csv"):
        if row.get("year") != "2025":
            continue
        spu = _f(row.get("spend_per_unit_eur"))
        if spu is None:
            continue
        out[row["distributor_code"]] = {
            "gps_spu_eur": spu,
            "gps_spu_ex_warranty_eur": _f(row.get("spend_per_unit_ex_warranty_eur")),
            "warranty_parts_eur": _f(row.get("warranty_parts_eur")),
            "warranty_data_gap": str(row.get("warranty_data_gap") or "").lower() in {"true", "1", "yes"},
            "traffic_light": row.get("traffic_light") or "",
            "traffic_light_ex_warranty": row.get("traffic_light_v9_ex_warranty") or "",
            "gps_capture_vs_max": _f(row.get("gps_capture_vs_max")),
        }
    return out


def load_genuine_share_2025() -> dict[str, float]:
    """Genuine EUR / (Genuine+BVP) on PMS-family mix — 'GPS' as parts share."""
    ge: dict[str, float] = defaultdict(float)
    tot: dict[str, float] = defaultdict(float)
    for row in csv_dict(DERIVED / "mix_genuine_bvp_pms.csv"):
        if row.get("year") != "2025":
            continue
        db = row["distributor_code"]
        ge[db] += _f(row.get("genuine_eur")) or 0.0
        tot[db] += _f(row.get("total_eur")) or 0.0
    return {db: ge[db] / tot[db] for db in tot if tot[db] > 0}


def csv_dict(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_kpi_fill_mos() -> dict[str, dict[str, float | None]]:
    """Average of last up-to-6 numeric months for First Fill and MOS (days)."""
    if not KPI_MASTER.is_file():
        return {}
    wb = load_workbook(KPI_MASTER, read_only=True, data_only=True)
    ws = wb["Parts Handling"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    def block(start_label: str) -> dict[str, list[float]]:
        start = None
        for i, r in enumerate(rows):
            if r and r[0] == start_label:
                start = i
                break
        if start is None:
            return {}
        # header at start+2, data until blank distributor block
        header = rows[start + 2]
        data_start = start + 3
        by_db: dict[str, list[float]] = {}
        for r in rows[data_start:]:
            if not r or r[0] in (None, ""):
                # stop at next section title or empty streak
                if r and r[0] in ("First Fill Rate", "Back Order Lines", "Parts Sales DB to DLR in €", "Parts Sales per Unit in €"):
                    break
                if not r or all(c in (None, "") for c in r[:3]):
                    # allow one blank; break on second structural gap
                    continue
            name = str(r[0]).strip()
            if name in (
                "First Fill Rate",
                "Back Order Lines",
                "Parts Sales DB to DLR in €",
                "Parts Sales per Unit in €",
                "Distributor",
            ):
                break
            vals: list[float] = []
            for c in r[1:]:
                if isinstance(c, (int, float)) and not isinstance(c, bool):
                    vals.append(float(c))
                # skip N/D N/A strings
            if vals:
                by_db[name] = vals[-6:]  # last 6 reported numerics
        return by_db

    mos = block("Days of Parts in Stock")
    fill = block("First Fill Rate")
    spu = block("Parts Sales per Unit in €")

    names = set(mos) | set(fill) | set(spu)
    out: dict[str, dict[str, float | None]] = {}
    for n in names:
        out[n] = {
            "kpi_mos_days": mean(mos[n]) if n in mos and mos[n] else None,
            "kpi_fill_rate": mean(fill[n]) if n in fill and fill[n] else None,
            "kpi_spu_eur": mean(spu[n]) if n in spu and spu[n] else None,
        }
    return out


def ids_country_section_d(payload: dict) -> dict[str, dict[str, Any]]:
    """Section D country stats with Benelux rollup + 0% shell hygiene."""
    profiles = hygienic_country_profiles(payload)
    out: dict[str, dict[str, Any]] = {}
    for c, prof in profiles.items():
        if is_rollup_country(c):
            continue
        dealers = [
            d
            for d in dealers_for_stats(payload)
            if d["country"] == c and not d.get("totals_only")
        ]
        d_vals = [
            d["sections"]["D"]["pct"]
            for d in dealers
            if d.get("sections", {}).get("D", {}).get("pct") is not None
        ]
        out[c] = {
            "ids_d_avg": prof.get("sections_pct", {}).get("D"),
            "ids_total_avg": prof.get("total_pct"),
            "dealer_count_scored": len(d_vals) if d_vals else prof.get("dealer_count") or 0,
            "ids_d_min": min(d_vals) if d_vals else None,
            "ids_d_p25": sorted(d_vals)[max(0, len(d_vals) // 4)] if d_vals else None,
        }
    return out


def build_join_rows(
    ids_d: dict[str, dict[str, Any]],
    pms: dict[str, dict[str, float]],
    gps: dict[str, dict[str, Any]],
    genuine: dict[str, float],
    kpi: dict[str, dict[str, float | None]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for country, meta in COUNTRY_MAP.items():
        if country not in ids_d:
            continue
        prism = meta["prism"]
        kpi_name = meta.get("kpi")
        p = pms.get(prism, {})
        g = gps.get(prism, {})
        gen_share = genuine.get(prism)

        k = kpi.get(kpi_name or "", {}) if kpi_name else {}
        idrow = ids_d[country]
        if idrow.get("ids_d_avg") is None:
            continue
        rows.append(
            {
                "ids_country": country,
                "prism_db": prism,
                "kpi_name": kpi_name,
                "note": meta.get("note") or "",
                "ids_d_avg": idrow["ids_d_avg"],
                "ids_total_avg": idrow["ids_total_avg"],
                "dealer_count": idrow["dealer_count_scored"],
                "ids_d_min": idrow["ids_d_min"],
                "pms_capture_total": p.get("pms_capture_total"),
                "pms_capture_genuine": p.get("pms_capture_genuine"),
                "pms_gap_eur": p.get("pms_gap_eur"),
                "genuine_share_eur": gen_share,
                "gps_spu_eur": g.get("gps_spu_eur"),
                "gps_spu_ex_warranty_eur": g.get("gps_spu_ex_warranty_eur"),
                "warranty_parts_eur": g.get("warranty_parts_eur"),
                "warranty_data_gap": g.get("warranty_data_gap"),
                "gps_light": g.get("traffic_light"),
                "gps_light_ex_warranty": g.get("traffic_light_ex_warranty"),
                "kpi_fill_rate": k.get("kpi_fill_rate"),
                "kpi_mos_days": k.get("kpi_mos_days"),
                "kpi_spu_eur": k.get("kpi_spu_eur"),
            }
        )
    return rows


def correlations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Pearson r: IDS Section D avg vs each DB metric (markets with both values)."""
    targets = [
        ("pms_capture_total", "PMS total capture"),
        ("pms_capture_genuine", "PMS genuine capture"),
        ("genuine_share_eur", "Genuine parts share (€ mix)"),
        ("gps_spu_eur", "GPS spend per unit (€/UIO)"),
        ("kpi_fill_rate", "KPI first fill rate"),
        ("kpi_mos_days", "KPI MOS (days)"),
        ("kpi_spu_eur", "KPI parts sales per unit"),
    ]
    out: dict[str, Any] = {}
    for key, label in targets:
        pairs = [
            (r["ids_d_avg"], r[key])
            for r in rows
            if r.get("ids_d_avg") is not None
            and r.get(key) is not None
            and not (isinstance(r[key], float) and math.isnan(r[key]))
        ]
        if len(pairs) < 3:
            out[key] = {"label": label, "n": len(pairs), "r": None, "markets": [p for p, _ in []]}
            continue
        xs = [p[0] for p in pairs]
        ys = [float(p[1]) for p in pairs]
        # For fill rate stored 0-1 already
        r = _pearson(xs, ys)
        markets = [
            row["ids_country"]
            for row in rows
            if row.get("ids_d_avg") is not None
            and row.get(key) is not None
            and not (isinstance(row[key], float) and math.isnan(row[key]))
        ]
        out[key] = {"label": label, "n": len(pairs), "r": r, "markets": markets}
    return out


def extract_section_d_gaps(country: str, dealer_name: str, top_n: int = 12) -> list[dict[str, Any]]:
    """Read result report .xls and list worst Section D questions for one dealer."""
    # filename country casing
    candidates = list(IDS_RESULT_REPORTS_DIR.glob("2026 IDS Evaluation Result Report_*.xls"))
    path = None
    for p in candidates:
        stem = p.stem.replace("2026 IDS Evaluation Result Report_", "")
        if stem.upper() == country.upper() or stem.upper() == country.replace("HUNGARY", "Hungary").upper():
            path = p
            break
        if country.upper() == "HUNGARY" and stem.lower() == "hungary":
            path = p
            break
        if country.upper() == "CYPRUS" and stem.lower() == "cyprus":
            path = p
            break
        if country.upper() == "ISRAEL" and stem.lower() == "israel":
            path = p
            break
        if country.upper() == "PORTUGAL" and stem.lower() == "portugal":
            path = p
            break
        if country.upper() == "ROMANIA" and stem.lower() == "romania":
            path = p
            break
        if country.upper() == "POLAND" and stem.lower() == "poland":
            path = p
            break
        if country.upper() == "PETROS" and stem.lower() == "petros":
            path = p
            break
    if path is None:
        # fuzzy
        for p in candidates:
            if country.lower() in p.name.lower():
                path = p
                break
    if path is None:
        return [{"error": f"no result report for {country}"}]

    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    # find dealer col
    col = None
    for c in range(COL_FIRST_DEALER, sh.ncols):
        name = str(sh.cell_value(ROW_META_START, c) or "").strip()
        if name.casefold() == dealer_name.casefold():
            col = c
            break
    if col is None:
        # partial
        for c in range(COL_FIRST_DEALER, sh.ncols):
            name = str(sh.cell_value(ROW_META_START, c) or "").strip()
            if dealer_name.casefold() in name.casefold() or name.casefold() in dealer_name.casefold():
                col = c
                break
    if col is None:
        return [{"error": f"dealer {dealer_name!r} not in {path.name}"}]

    matrix = load_matrix_rows_from_sheet(sh)
    # Section D category row
    in_d = False
    gaps: list[dict[str, Any]] = []
    for row in matrix:
        ref = (row.ref or "").strip()
        if row.kind == "category":
            in_d = bool(re.match(r"^D\.", ref, re.I))
            continue
        if not in_d:
            continue
        if row.kind != "question" or row.sheet_row is None:
            continue
        if not QUESTION_RE.match(ref):
            continue
        max_pts = row.max_points or _f(sh.cell_value(row.sheet_row, COL_MAX)) or 0.0
        raw = sh.cell_value(row.sheet_row, col)
        score = _f(raw)
        if score is None:
            continue
        if max_pts <= 0:
            continue
        pct = score / max_pts
        text = row.text or str(sh.cell_value(row.sheet_row, COL_TEXT) or "")
        gaps.append(
            {
                "ref": ref,
                "text": text[:180],
                "score": score,
                "max": max_pts,
                "pct": pct,
                "gap_pts": max_pts - score,
            }
        )
    gaps.sort(key=lambda g: (g["pct"], -g["gap_pts"]))
    return gaps[:top_n]


def pick_focus_dealers(payload: dict, join_rows: list[dict[str, Any]], n: int = 4) -> list[dict[str, Any]]:
    """Prefer weak Section D dealers in markets where DB parts KPIs are also weak."""
    # Score each market on DB weakness (lower capture / SPU / fill = weaker)
    db_weak: dict[str, float] = {}
    for r in join_rows:
        scores = []
        if r.get("pms_capture_genuine") is not None and not math.isnan(r["pms_capture_genuine"]):
            scores.append(1 - float(r["pms_capture_genuine"]))
        if r.get("genuine_share_eur") is not None:
            scores.append(1 - float(r["genuine_share_eur"]))
        if r.get("gps_spu_eur") is not None:
            # normalize roughly: 50€ red, 200€ green
            scores.append(max(0.0, min(1.0, (200 - float(r["gps_spu_eur"])) / 150)))
        if r.get("kpi_fill_rate") is not None:
            scores.append(max(0.0, 0.95 - float(r["kpi_fill_rate"])) / 0.2)
        if scores:
            db_weak[r["ids_country"]] = mean(scores)

    candidates: list[dict[str, Any]] = []
    for d in payload["dealers"]:
        if d.get("totals_only"):
            continue
        dp = d.get("sections", {}).get("D", {}).get("pct")
        if dp is None:
            continue
        country = d["country"]
        weak = db_weak.get(country, 0.4)
        # priority = how bad D is + how weak DB is
        priority = (1 - dp) * 0.65 + weak * 0.35
        candidates.append(
            {
                "country": country,
                "name": d["name"],
                "id": d["id"],
                "ids_total_pct": d["total_pct"],
                "ids_d_pct": dp,
                "ids_c_pct": d.get("sections", {}).get("C", {}).get("pct"),
                "db_weakness": weak,
                "priority": priority,
            }
        )
    candidates.sort(key=lambda x: -x["priority"])

    # Ensure preferred names surface if present
    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for country, name in PREFERRED_FOCUS:
        for c in candidates:
            if c["country"] == country and name.casefold() in c["name"].casefold():
                if c["id"] not in seen:
                    picked.append(c)
                    seen.add(c["id"])
                break
    for c in candidates:
        if len(picked) >= n:
            break
        if c["id"] in seen:
            continue
        # diversify countries
        if sum(1 for p in picked if p["country"] == c["country"]) >= 2:
            continue
        picked.append(c)
        seen.add(c["id"])
    return picked[:n]


def write_register(path: Path, focus: list[dict[str, Any]], join_by_country: dict[str, dict]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Kaizen_Wave1"
    headers = [
        "Tier",
        "Country",
        "Dealer",
        "IDS total %",
        "IDS Section D %",
        "IDS Section C %",
        "DB PMS genuine capture %",
        "DB genuine share %",
        "DB GPS €/UIO",
        "DB KPI fill %",
        "Top IDS-D gaps (ref)",
        "Root cause (draft)",
        "Kaizen actions (K#)",
        "Owner DB",
        "Owner dealer",
        "Due date",
        "Verify metric",
        "Baseline",
        "Target",
        "Status",
    ]
    header_fill = PatternFill("solid", fgColor="1A2B4A")
    header_font = Font(color="FFFFFF", bold=True)
    for i, h in enumerate(headers, 1):
        cell = ws.cell(1, i, h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    for i, f in enumerate(focus, 2):
        j = join_by_country.get(f["country"], {})
        gaps = f.get("gaps") or []
        gap_txt = "; ".join(
            f"{g['ref']} {g['score']:g}/{g['max']:g}" for g in gaps[:6] if "ref" in g
        )
        ws.cell(i, 1, "T1")
        ws.cell(i, 2, f["country"])
        ws.cell(i, 3, f["name"])
        ws.cell(i, 4, round(f["ids_total_pct"] * 100, 1) if f.get("ids_total_pct") is not None else None)
        ws.cell(i, 5, round(f["ids_d_pct"] * 100, 1) if f.get("ids_d_pct") is not None else None)
        ws.cell(i, 6, round(f["ids_c_pct"] * 100, 1) if f.get("ids_c_pct") is not None else None)
        gen_c = j.get("pms_capture_genuine")
        ws.cell(i, 7, round(gen_c * 100, 1) if gen_c is not None and not math.isnan(gen_c) else None)
        gs = j.get("genuine_share_eur")
        ws.cell(i, 8, round(gs * 100, 1) if gs is not None else None)
        ws.cell(i, 9, round(j["gps_spu_eur"], 1) if j.get("gps_spu_eur") is not None else None)
        fr = j.get("kpi_fill_rate")
        ws.cell(i, 10, round(fr * 100, 1) if fr is not None else None)
        ws.cell(i, 11, gap_txt)
        ws.cell(i, 12, "")
        ws.cell(i, 13, "K1 / K2 / K3")
        ws.cell(i, 14, j.get("kpi_name") or j.get("prism_db") or "")
        ws.cell(i, 15, "")
        ws.cell(i, 16, "")
        ws.cell(i, 17, "IDS-D re-score + RO genuine/PMS check")
        ws.cell(i, 18, f"D={round(f['ids_d_pct']*100,1)}%")
        ws.cell(i, 19, "D +8pp / 90 days")
        ws.cell(i, 20, "Open")

    ws2 = wb.create_sheet("DB_Correlation")
    ws2.append(
        [
            "IDS country",
            "PRISM DB",
            "IDS D avg %",
            "PMS total %",
            "PMS genuine %",
            "Genuine share %",
            "GPS €/UIO",
            "KPI fill %",
            "KPI MOS days",
            "Note",
        ]
    )
    for r in join_by_country.values():
        ws2.append(
            [
                r.get("ids_country"),
                r.get("prism_db"),
                _pct100(r.get("ids_d_avg")),
                _pct100(r.get("pms_capture_total")),
                _pct100(r.get("pms_capture_genuine")),
                _pct100(r.get("genuine_share_eur")),
                round(r["gps_spu_eur"], 1) if r.get("gps_spu_eur") is not None else None,
                _pct100(r.get("kpi_fill_rate")),
                round(r["kpi_mos_days"], 1) if r.get("kpi_mos_days") is not None else None,
                r.get("note"),
            ]
        )

    ws3 = wb.create_sheet("Gap_Detail")
    ws3.append(["Country", "Dealer", "Ref", "Score", "Max", "Pct %", "Question"])
    for f in focus:
        for g in f.get("gaps") or []:
            if "ref" not in g:
                continue
            ws3.append(
                [
                    f["country"],
                    f["name"],
                    g["ref"],
                    g["score"],
                    g["max"],
                    round(g["pct"] * 100, 1),
                    g.get("text", ""),
                ]
            )

    for sheet in wb.worksheets:
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 16
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _pct100(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return round(float(v) * 100, 1)



def _json_safe(payload: dict) -> str:
    """JSON for embedding in script tags — no NaN/Infinity (breaks browsers)."""

    def scrub(o: Any) -> Any:
        if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
            return None
        if isinstance(o, dict):
            return {k: scrub(v) for k, v in o.items()}
        if isinstance(o, list):
            return [scrub(v) for v in o]
        return o

    return json.dumps(scrub(payload), ensure_ascii=False, allow_nan=False)


_TEMPLATE = Path(__file__).resolve().parent / "ids_parts_kaizen_template.html"
_APP_JS = Path(__file__).resolve().parent / "ids_parts_kaizen_app.js"


def render_html(payload: dict, chart_js: str) -> str:
    """Self-contained HTML — template + app.js (no Python f-string brace eating)."""
    tpl = _TEMPLATE.read_text(encoding="utf-8")
    app = _APP_JS.read_text(encoding="utf-8")
    return (
        tpl.replace("__BUILT_AT__", payload.get("built_at", ""))
        .replace("__CHART_JS__", chart_js)
        .replace("__DATA_JSON__", _json_safe(payload))
        .replace("__APP_JS__", app)
    )



def suggest_actions(gaps: list[dict[str, Any]]) -> str:
    refs = " ".join(g.get("ref", "") for g in gaps).upper()
    texts = " ".join(g.get("text", "") for g in gaps).lower()
    acts = []
    if any(x in texts for x in ("genuine", "non-genuine", "bvp", "brand")) or "D.1" in refs:
        acts.append("K2 genuine default")
    if any(x in texts for x in ("stock", "fill", "inventory", "order", "turnover", "bin")):
        acts.append("K3 min/max + fill")
    if any(x in texts for x in ("promot", "display", "campaign")):
        acts.append("K2 + parts display audit")
    if not acts:
        acts = ["K1 PMS basket", "K2 genuine default", "K3 stock fill"]
    if "K1" not in " ".join(acts):
        acts.insert(0, "K1 PMS basket on ROs")
    return " · ".join(acts[:3])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    payload_ids = build_dashboard_payload(IDS_RESULT_REPORTS_DIR)
    ids_d = ids_country_section_d(payload_ids)
    pms = load_pms_db_2025()
    gps = load_gps_2025()
    genuine = load_genuine_share_2025()
    kpi = load_kpi_fill_mos()
    join_rows = build_join_rows(ids_d, pms, gps, genuine, kpi)
    corr = correlations(join_rows)

    focus = pick_focus_dealers(payload_ids, join_rows, n=4)
    join_by = {r["ids_country"]: r for r in join_rows}

    for f in focus:
        gaps = extract_section_d_gaps(f["country"], f["name"])
        f["gaps"] = gaps
        f["suggested_actions"] = suggest_actions(gaps)
        j = join_by.get(f["country"], {})
        f["db_context"] = {
            "pms_gen": _fmt_pct(j.get("pms_capture_genuine")),
            "gen_share": _fmt_pct(j.get("genuine_share_eur")),
            "gps": f"{j['gps_spu_eur']:.0f}" if j.get("gps_spu_eur") is not None else "—",
            "fill": _fmt_pct(j.get("kpi_fill_rate")),
        }

    study = {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "scored_dealers": sum(1 for d in payload_ids["dealers"] if not d.get("totals_only")),
        "join_rows": join_rows,
        "correlations": corr,
        "focus_dealers": focus,
        "metric_notes": {
            "genuine_parts_share": "Genuine EUR / (Genuine+BVP) on PMS-family mix CY2025",
            "gps_spu": "PRISM spend per unit EUR/UIO CY2025",
            "pms": "Weighted capture = sum(actual)/sum(expected) across PMS categories, line_type total|genuine",
            "kpi": "KPI Master June 2026 Parts Handling — mean of last ≤6 numeric months",
        },
    }

    json_path = OUT_DIR / "study_payload.json"
    json_path.write_text(json.dumps(study, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    xlsx_path = OUT_DIR / "IDS_Parts_Kaizen_Register.xlsx"
    write_register(xlsx_path, focus, join_by)

    if not CHART_JS.is_file():
        print(f"Chart.js missing: {CHART_JS}", file=sys.stderr)
        return 2
    chart_js = CHART_JS.read_text(encoding="utf-8")
    # strip sourceMappingURL if present
    chart_js = re.sub(r"\n//# sourceMappingURL=.*$", "", chart_js)

    html = render_html(study, chart_js)
    html_path = OUT_DIR / "IDS_Parts_Kaizen_Study_2026.html"
    html_path.write_text(html, encoding="utf-8")

    # also copy to Downloads for Jerome
    downloads = Path.home() / "Downloads"
    if downloads.is_dir():
        (downloads / html_path.name).write_text(html, encoding="utf-8")
        import shutil

        shutil.copy2(xlsx_path, downloads / xlsx_path.name)

    print("Wrote", html_path)
    print("Wrote", xlsx_path)
    print("Wrote", json_path)
    print("\nCorrelations (r):")
    for k, v in corr.items():
        print(f"  {v['label']}: r={None if v['r'] is None else round(v['r'],3)} n={v['n']}")
    print("\nFocus dealers:")
    for f in focus:
        print(f"  {f['country']} | {f['name']} | D={f['ids_d_pct']*100:.0f}% | gaps={len(f.get('gaps') or [])}")
        for g in (f.get("gaps") or [])[:4]:
            if "ref" in g:
                print(f"     - {g['ref']}: {g['score']}/{g['max']} ({g['pct']*100:.0f}%)")
    return 0


def _fmt_pct(v: Any) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{float(v)*100:.0f}%"


if __name__ == "__main__":
    raise SystemExit(main())
