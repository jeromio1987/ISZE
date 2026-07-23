"""Load reviewed BP FY27 (VP turnover) — single source for all GPS builds.

Sources (priority):
  1. Incentive FY27 sheet — kickback / named distributors (exact EUR)
  2. BP 2027 (FY) VP turnover — OTHERS breakdown (000 EUR × 1_000)

Reviewed file: 01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx
Snapshot:     01_data/91_build/bp_fy27_reviewed.json
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import openpyxl

from gps_v9_loaders import GPS_DBS

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILD = ROOT / "01_data" / "91_build"
PLANNING = ROOT / "01_data" / "11_planning"
BP_REVIEWED_XLSX = PLANNING / "budget_per_DB_reviewed_24042026.xlsx"
BP_REVIEWED_JSON = BUILD / "bp_fy27_reviewed.json"

# Incentive FY27 sheet → GPS v9 code
INCENTIVE_NAME_TO_GPS: dict[str, str] = {
    "ITUK": "ITUK",
    "IUK": "IUK",
    "UMI": "UMI",
    "UTI": "UTI",
    "IBX": "BELGIUM",
    "ISD": "GERMANY",
    "Portugal": "PORTUGAL",
    "Ireland": "IRELAND",
    "Norway": "NORWAY",
    "Sweden": "SWEDEN",
    "KTK": "KAZAKHSTAN",
}

# BP 2027 (FY) VP turnover — reviewed 24 Apr 2026 (values in EUR, from 000 EUR column)
VP_TURNOVER_FY27: dict[str, dict] = {
    "2194": {"name": "ITUK (IC)", "eur": 6_974_200, "gps": "ITUK"},
    "89": {"name": "IUK", "eur": 6_063_000, "gps": "IUK"},
    "1797": {"name": "UMI", "eur": 2_973_300, "gps": "UMI"},
    "1799": {"name": "UTI", "eur": 3_098_100, "gps": "UTI"},
    "90": {"name": "IBX", "eur": 2_296_600, "gps": "BELGIUM"},
    "93": {"name": "ISD", "eur": 2_913_700, "gps": "GERMANY"},
    "105": {"name": "IMG (IC)", "eur": 19_400, "gps": None},
    "92": {"name": "IMOTORS", "eur": 1_858_300, "gps": "PORTUGAL"},
    "76": {"name": "ISUZU IRELAND", "eur": 1_267_400, "gps": "IRELAND"},
    "86": {"name": "RSA", "eur": 1_764_800, "gps": "NORWAY"},
    "2181": {"name": "ISUZU SVERIGE", "eur": 1_464_300, "gps": "SWEDEN"},
    "2294": {"name": "KTK", "eur": 1_143_900, "gps": "KAZAKHSTAN"},
    "393": {"name": "LOUTSIOS", "eur": 539_600, "gps": "CYPRUS"},
    "66": {"name": "PETROS PETROPOULOS", "eur": 574_400, "gps": "GREECE"},
    "88": {"name": "MIDI", "eur": 357_700, "gps": None},
    "2679": {"name": "Nordic Automotive Trading", "eur": 360_300, "gps": "FINLAND"},
    "537": {"name": "AW Distribution", "eur": 349_600, "gps": "HUNGARY"},
    "2731": {"name": "Grand Avto", "eur": 267_100, "gps": None},
    "2732": {"name": "CBC-Trans", "eur": 207_500, "gps": None},
    "1759": {"name": "GASANZAMMIT", "eur": 233_100, "gps": "MALTA"},
    "2027": {"name": "ISUZU DANMARK", "eur": 187_600, "gps": "DENMARK"},
    "1576": {"name": "BL", "eur": 104_600, "gps": "ICELAND"},
    "2372": {"name": "KIMA", "eur": 50_700, "gps": None},
}

VP_NETWORK_TOTAL_EUR = 35_284_400

# Not in reviewed VP turnover breakdown — retain prior Kosha row until next budget review
BP_FY27_FALLBACK: dict[str, float] = {
    "ROMANIA": 199_587.57,
}


def _load_incentive_sheet() -> dict[str, float]:
    if not BP_REVIEWED_XLSX.is_file():
        raise FileNotFoundError(f"Missing reviewed budget: {BP_REVIEWED_XLSX}")
    wb = openpyxl.load_workbook(BP_REVIEWED_XLSX, data_only=True, read_only=True)
    ws = wb["Incentive FY27"]
    out: dict[str, float] = {}
    for r in range(3, ws.max_row + 1):
        name = ws.cell(r, 1).value
        bp27 = ws.cell(r, 4).value
        if not name or not isinstance(bp27, (int, float)) or name == "Total Budget":
            continue
        gps = INCENTIVE_NAME_TO_GPS.get(str(name).strip())
        if gps:
            out[gps] = float(bp27)
    wb.close()
    return out


def _vp_turnover_by_gps() -> dict[str, float]:
    out: dict[str, float] = {}
    for row in VP_TURNOVER_FY27.values():
        gps = row.get("gps")
        if gps:
            out[gps] = out.get(gps, 0.0) + float(row["eur"])
    return out


def load_bp_fy27_reviewed(*, write_json: bool = True) -> dict[str, float]:
    """Return BP FY27 EUR per GPS v9 distributor code."""
    incentive = _load_incentive_sheet()
    vp_gps = _vp_turnover_by_gps()

    by_gps: dict[str, float] = {}
    for gps in GPS_DBS:
        if gps in incentive:
            by_gps[gps] = incentive[gps]
        elif gps in vp_gps:
            by_gps[gps] = vp_gps[gps]
        elif gps in BP_FY27_FALLBACK:
            by_gps[gps] = BP_FY27_FALLBACK[gps]

    if write_json:
        payload = {
            "generated": date.today().isoformat(),
            "source_xlsx": str(BP_REVIEWED_XLSX),
            "source_vp_turnover": "BP 2027 (FY) reviewed 24 Apr 2026 — VP turnover 000 EUR",
            "reviewed": "2026-04-24",
            "vp_network_total_eur": VP_NETWORK_TOTAL_EUR,
            "note": "Replaces Kosha €35.3M CY2025 sales-share proxy. Incentive sheet overrides VP where both exist.",
            "by_gps_code": {k: round(v, 2) for k, v in sorted(by_gps.items())},
            "by_customer_id": {
                cid: {"name": row["name"], "eur": row["eur"], "gps": row["gps"]}
                for cid, row in VP_TURNOVER_FY27.items()
            },
            "fallback_gps_dbs": {
                k: {"eur": v, "reason": "not in reviewed VP turnover — prior Kosha proxy"}
                for k, v in BP_FY27_FALLBACK.items()
                if k in by_gps
            },
            "missing_gps_dbs": [g for g in GPS_DBS if g not in by_gps],
            "non_gps_customers_eur": {
                row["name"]: row["eur"]
                for row in VP_TURNOVER_FY27.values()
                if not row.get("gps")
            },
        }
        BP_REVIEWED_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return by_gps


def bp_fy27_for_gps_dbs() -> dict[str, float]:
    """Convenience: BP map restricted to GPS_DBS (raises if any DB missing)."""
    bp = load_bp_fy27_reviewed()
    missing = [g for g in GPS_DBS if g not in bp]
    if missing:
        raise KeyError(f"BP FY27 missing for GPS DBs: {', '.join(missing)}")
    return {g: bp[g] for g in GPS_DBS}
