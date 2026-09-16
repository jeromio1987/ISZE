#!/usr/bin/env python
"""
ISZE one-distributor OPERATING DASHBOARD — numbers ledger builder.

"Where are we with this customer." One DB at a time, any DB, same conventions.

    python build_ledger.py --db UMI
    python build_ledger.py --db ITUK
    python build_ledger.py --all
    python build_ledger.py --db UMI --lcv-rate 262.50      # override the D-Max rate

Writes  09_meetings/<DB>_Operating_Dashboard_2026/NUMBERS_LEDGER.json
The HTML dashboard RENDERS that JSON. It never computes.

--------------------------------------------------------------------------------
LOCKED CONVENTIONS  (changing any of these needs a note in the DB's DATA_INTEGRITY.md)
--------------------------------------------------------------------------------
FY            Apr-Mar, labelled by END year. FY2026 = Apr 2025 - Mar 2026.
GPS %         actual / max spend, where max spend = UIO x ISZE-net rate/unit.
              FY-grain from V3.1 (Jerome's locked workbook, built on UIO V19).
              V19 is ACTUAL (Jerome, 2026-08-14) -> GPS % is signed and releasable.
PMS capture   complete CY only, line_type == 'total'. Never YTD vs full-year expected.
              uio_units in that file is FROZEN across years - no trend exists in it.
Wallet        CY. wallet_waterfall.csv is baked at EUR 250.00/unit and is NOT re-rated
              here; it is carried as a cross-check only. The live GPS spine is V3.1.
Credit notes  stored POSITIVE in sales_fact.parquet. Excluded, never subtracted.
Genuine/BVP   whole book (sales_fact + crossref bvp_pn). This reproduces
              metrics_snapshot.json exactly. mix_genuine_bvp_by_group.csv is the
              crossref-PAIRED basket only and reads wildly differently - see below.
BVP           Best Value is in-tent retention, a gross-margin question. It is never
              added to an erosion figure. Only IAM defection is real erosion.
Israel        UMI 1797 and UTI 1799 share payer 1797. Split at sold_to. Never blend.
--------------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_street import enrich, write_integrity_md
from compare_and_drill import attach_compare_and_drill

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
MEETINGS = os.path.join(ISZE, "09_meetings")
V31_XLSX = os.path.join(ISZE, "01_data", "ISZE_GPS_Extended_Target_FY27_V3.1.xlsx")
BP_JSON = os.path.join(ISZE, "01_data", "91_build", "bp_fy27_reviewed.json")
TARGETS_CSV = os.path.join(ISZE, "03_analytics", "Isuzu", "prism", "data", "gps_model_targets.csv")
UIO_V19_XLSX = os.path.join(ISZE, "06_uio", "_CURRENT", "ISUZU_UIO_Overview_2026.xlsx")

# V3.1 maps calendar year N in V19 → fiscal year N+1 (source note on each DB tab).
# FY2024 therefore uses CY2023 parc. Filter ASC/DB = ISZE. GERMANY is country GERMANY
# (Austria also carries ISD-Lang — do not blend).
V19_DIST = {
    "GERMANY":  {"dist": "ISD-Lang", "country": "GERMANY"},
    "UMI":      {"dist": "UMI"},
    "PORTUGAL": {"dist": "Imotors"},
    "ITUK":     {"dist": "ITUK"},
    "IUK":      {"dist": "IUK"},
    "UTI":      {"dist": "UTI"},
    "BELGIUM":  {"dist": "IBX"},
    "NORWAY":   {"dist": "Rutebileiernes"},
    "SWEDEN":   {"dist": "Sverige"},
    "IRELAND":  {"dist": "Ireland"},
    "GREECE":   {"dist": "RSA"},
    "CYPRUS":   {"dist": "Loutsios"},
    "HUNGARY":  {"dist": "AutoWallis"},
    "FINLAND":  {"dist": "Nordic"},
    "MALTA":    {"dist": "GasanZammit"},
    "ROMANIA":  {"dist": "ROM Auto"},
    "DENMARK":  {"dist": "Danmark"},
    "ICELAND":  {"dist": "BL"},
}
V19_MODEL = {"LD": "LD", "MD": "MD", "F": "F-Series", "F-SERIES": "F-Series", "LCV": "LCV"}
_V19_ROWS = None

GPS_FILE = "gps_pure_sales_2026-08-13_v2.csv"

# ---------------------------------------------------------------------------
# D-Max / LCV rate. ONE place. Everything rate-dependent derives from here.
#
# OPEN (Jerome 2026-08-14): "GPS dmax is now already 260 something."
# Four rates are live in the workspace and none of them is 260-something:
#   250.0000  gps_model_targets.csv LCV_D_Max (2026-06-12) -> baked into wallet_waterfall
#   219.5648  V3.1 MH LCV chain, FY26 base  (291.2 x 1.16 x 0.65)
#   230.5430  V3.1 FY27 (+5% price increase)
#   237.4593  V3.1 FY28 (+3%/yr IML policy)
# V3.1's chain is the DEFAULT because it is the only one that reconciles to the
# locked EXT TARGET figures. Pass --lcv-rate to override once the number is confirmed.
# ---------------------------------------------------------------------------
# CURRENT D-Max / LCV rate, confirmed by Jerome 2026-08-14: EUR 262.50.
# 262.50 / 1.05 = 250.00 exactly, which is gps_model_targets.csv LCV_D_Max. So 250.00 is
# the base and 262.50 is the FY2027 (+5%) rate. Today is inside FY2027 (Apr'26-Mar'27),
# hence "current" = 262.50. This reconciles gps_model_targets.csv and the +5% convention
# instead of choosing between them.
#
# This SUPERSEDES V3.1's MH LCV chain (219.5648 base / 230.5430 FY27), which applied FX
# and the 0.65 margin twice — the conflict V3.1's own Method tab records at A19-A21.
LCV_RATE_CURRENT_FY27 = 262.50
LCV_RATE_BASE = 262.50 / 1.05          # 250.00 — FY25 / FY26 basis
LCV_RATE_OVERRIDE: float | None = None  # --lcv-rate replaces the FY27 figure
# CV rates stay on the v9 convention +5% for FY27, per Jerome. Not touched by --lcv-rate.
CV_RATES = {"LD": (739.0, 775.95), "MD": (887.0, 931.35), "F-Series": (887.0, 931.35)}
V31_LCV_CHAIN = {"base": 219.5648, "fy27": 230.5430, "fy28": 237.4593}

FY_LATEST = 2026        # last complete FY
CY_LATEST = 2025        # last complete CY
RUSH = {"VOR", "RUSH", "SVOR"}
STOCK_AS_SOR = {"SOR", "PRD"}  # Jerome 2026-08-14: PRD counts as stock on the 80/20 screen
NON_ORDER_SATY = {"CR", "RE", "DR", "ZDR", "FD"}
# Projected ISZE retail = PR00 net × DB 1.40 × DLR 1.275. From pricing config.yaml
# combined factor (do not copy the yaml key name into the HTML payload).
CHANNEL_DB_FACTOR = 1.40
CHANNEL_DLR_FACTOR = 1.275
CHANNEL_COMBINED = 1.785
CHANNEL_AS_OF = "config.yaml v1.0.0 · quality-premium yaml as_of 2026-08-10"
FILTER_PMS = ("oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter")
FILTER_CORE = ("oil_filter", "air_filter", "fuel_filter")


def fy_end_year(ts) -> int:
    """FY labelled by end year. Apr 2025 → FY2026."""
    return int(ts.year + 1) if int(ts.month) >= 4 else int(ts.year)


def projected_retail(net):
    if net is None:
        return None
    try:
        if pd.isna(net):
            return None
    except (TypeError, ValueError):
        pass
    return r2(float(net) * CHANNEL_COMBINED)


def delta_vs_projected_retail(iam, net):
    pr = projected_retail(net)
    if pr is None or pr == 0 or iam is None:
        return None, pr
    try:
        if pd.isna(iam):
            return None, pr
    except (TypeError, ValueError):
        pass
    return round(100.0 * (float(iam) - pr) / pr, 1), pr


# ---------------------------------------------------------------------------
# DB registry. distributor_code is the primary key.
#   sold_to      LIST - Portugal/Germany/Denmark each bill under two SAP codes
#   gps_label    the 'db' value in gps_pure_sales (Greece is 'RSA' - live name bug,
#                which is exactly why we key on distributor_code, never on a name)
#   v31_tab      None for ITUK/UTI: they sit on the V4 as-presented basis and have
#                no per-FY tab in V3.1, only a Dashboard row.
# ---------------------------------------------------------------------------
REGISTRY = {
    "ITUK":     dict(sold_to=[2575], gps_label="ITUK",        v31_tab=None,       segment="CV",    display="Isuzu Truck UK",            country="United Kingdom", ids="UK_CV"),
    "IUK":      dict(sold_to=[2574], gps_label="IUK",         v31_tab="IUK",      segment="LCV",   display="I.M. Parts & Service",      country="United Kingdom", ids="UK_LCV"),
    "UTI":      dict(sold_to=[1799], gps_label="UTI",         v31_tab=None,       segment="CV",    display="Universal Trucks Israel",   country="Israel",         ids=None),
    "UMI":      dict(sold_to=[1797], gps_label="UMI",         v31_tab="UMI",      segment="LCV",   display="Universal Motors Israel",   country="Israel",         ids="Israel_LCV"),
    "BELGIUM":  dict(sold_to=[90],   gps_label="IBX",         v31_tab="BELGIUM",  segment="MIXED", display="Isuzu Benelux",             country="Belgium",        ids="Belgium"),
    "GERMANY":  dict(sold_to=[2516, 601], gps_label="ISD",    v31_tab="GERMANY",  segment="MIXED", display="Isuzu Sales Deutschland",   country="Germany",        ids=None),
    "NORWAY":   dict(sold_to=[86],   gps_label="Norway",      v31_tab="NORWAY",   segment="LCV",   display="Rutebileiernes Stand.",     country="Norway",         ids="Norway"),
    "SWEDEN":   dict(sold_to=[2181], gps_label="Sverige",     v31_tab="SWEDEN",   segment="LCV",   display="Isuzu Sverige",             country="Sweden",         ids=None),
    "IRELAND":  dict(sold_to=[76],   gps_label="Ireland",     v31_tab="IRELAND",  segment="MIXED", display="Isuzu Ireland",             country="Ireland",        ids=None),
    "PORTUGAL": dict(sold_to=[519, 92], gps_label="Imotors",  v31_tab="PORTUGAL", segment="MIXED", display="I-Motors",                  country="Portugal",       ids="Portugal"),
    "GREECE":   dict(sold_to=[66],   gps_label="RSA",         v31_tab="GREECE",   segment="MIXED", display="Petros Petropoulos",        country="Greece",         ids="Greece"),
    "CYPRUS":   dict(sold_to=[393],  gps_label="Loutsios",    v31_tab="CYPRUS",   segment="MIXED", display="Loutsios & Sons",           country="Cyprus",         ids="Cyprus"),
    "HUNGARY":  dict(sold_to=[537],  gps_label="AutoWallis",  v31_tab="HUNGARY",  segment="LCV",   display="AutoWallis Distribution",   country="Hungary",        ids="Hungary"),
    "FINLAND":  dict(sold_to=[2679], gps_label="Nordic FI",   v31_tab="FINLAND",  segment="LCV",   display="Nordic Automotive Trading", country="Finland",        ids=None),
    "MALTA":    dict(sold_to=[1759], gps_label="GasanZammit", v31_tab="MALTA",    segment="MIXED", display="GasanZammit Motors",        country="Malta",          ids="Malta"),
    "ROMANIA":  dict(sold_to=[396],  gps_label="ROM Auto",    v31_tab="ROMANIA",  segment="LCV",   display="Isuzu Rom Auto",            country="Romania",        ids="Romania"),
    "DENMARK":  dict(sold_to=[2027, 2751], gps_label="Danmark", v31_tab="DENMARK", segment="LCV",  display="Isuzu Danmark",             country="Denmark",        ids="Denmark"),
    "ICELAND":  dict(sold_to=[1576], gps_label="BL Iceland",  v31_tab="ICELAND",  segment="LCV",   display="BL ehf.",                   country="Iceland",        ids=None),
}

# DBs with no PMS / wallet rows at all (CIS + Palestine).
NO_PMS = {"UKRAINE", "ARMENIA", "KAZAKHSTAN", "PALESTINE"}

# GPS % above 100 means the denominator is wrong, not that capture is complete.
# Blueprint + V3.1 WATCH row 33. Never quote a percentage for these.
GPS_PCT_NOT_QUOTABLE = {"IRELAND", "FINLAND", "ICELAND"}


def d(name: str) -> str:
    return os.path.join(DERIVED, name)


def r2(x):
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return round(float(x), 2)


def json_safe(o):
    """NaN/Inf must not reach the HTML payload — JSON.parse would die."""
    if isinstance(o, dict):
        return {k: json_safe(v) for k, v in o.items()}
    if isinstance(o, list):
        return [json_safe(x) for x in o]
    if isinstance(o, float):
        if pd.isna(o) or o != o:
            return None
        if o in (float("inf"), float("-inf")):
            return None
        return o
    try:
        if o is not None and pd.isna(o):
            return None
    except (TypeError, ValueError):
        pass
    return o


def src(path, grain, filt, note="", green=False):
    return {"file": path, "grain": grain, "filter": filt, "note": note,
            "in_green_verification_report": green}


# ---------------------------------------------------------------------------
# V3.1 readers
# ---------------------------------------------------------------------------
def read_v31(db: str, tab: str | None):
    """Dashboard row for every DB; per-FY tab where one exists."""
    import openpyxl
    wb = openpyxl.load_workbook(V31_XLSX, data_only=True)

    dash = wb["Dashboard"]
    row = None
    for r in range(5, 23):
        if dash.cell(r, 1).value == db:
            row = r
            break
    out = {"v31_file": os.path.basename(V31_XLSX), "dashboard_row": row}
    if row:
        out.update({
            "segment_label": dash.cell(row, 2).value,
            "bp_fy27_eur": r2(dash.cell(row, 3).value),
            "max_spend_fy27_eur": r2(dash.cell(row, 4).value),
            "gps_pct_fy27": r2(dash.cell(row, 5).value),
            "stretch_pct": r2(dash.cell(row, 6).value),
            "stretch_eur": r2(dash.cell(row, 7).value),
            "gps_pct_fy27_after_stretch": r2(dash.cell(row, 8).value),
            "ext_target_fy27_eur": r2(dash.cell(row, 9).value),
            "basis_note": dash.cell(row, 10).value,
        })

    out["fy_series"] = None
    out["uio_v19"] = None
    if tab and tab in wb.sheetnames:
        ws = wb[tab]
        # UIO block. Pure-LCV tabs: rows 9 (LCV) + 10 (TTL).
        # Mixed tabs: rows 9-12 (LD / MD / F-Series / LCV/D-Max) + 13 (TTL).
        # Cols C/D/E = FY25/FY26/FY27.
        uio, uio_seg = {}, {}
        for r in range(8, 15):
            lab = str(ws.cell(r, 1).value or "").strip()
            if not lab:
                continue
            trio = {2025: ws.cell(r, 3).value, 2026: ws.cell(r, 4).value, 2027: ws.cell(r, 5).value}
            up = lab.upper()
            if up == "TTL":
                uio = trio
            elif up.startswith("LD"):
                uio_seg["LD"] = trio
            elif up == "MD":
                uio_seg["MD"] = trio
            elif up.startswith("F-SERIES"):
                uio_seg["F-Series"] = trio
            elif up.startswith("LCV"):
                uio_seg["LCV"] = trio
        out["uio_by_segment"] = {k: {str(y): v for y, v in t.items()} for k, t in uio_seg.items()}
        # Locate the labelled rows in the wholesale block.
        idx = {}
        for r in range(15, 30):
            lab = str(ws.cell(r, 1).value or "")
            if lab.startswith("Max spend"):
                idx["max"] = r
            elif lab.startswith("Actual (ISZE billing)"):
                idx["actual"] = r
            elif lab.startswith("Share (GPS"):
                idx["share"] = r
            elif lab.startswith("TTL amount"):
                idx["ext"] = r
            elif lab.startswith("Share (new)"):
                idx["share_new"] = r
        fy = {}
        for col, y in ((3, 2025), (4, 2026), (5, 2027)):
            fy[y] = {
                "uio_units": uio.get(y),
                "max_spend_eur": r2(ws.cell(idx["max"], col).value) if "max" in idx else None,
                "actual_eur": r2(ws.cell(idx["actual"], col).value) if "actual" in idx else None,
                "gps_pct": r2(ws.cell(idx["share"], col).value) if "share" in idx else None,
                "ext_target_eur": r2(ws.cell(idx["ext"], col).value) if "ext" in idx else None,
                "gps_pct_after_stretch": r2(ws.cell(idx["share_new"], col).value) if "share_new" in idx else None,
            }
        out["fy_series"] = fy
        out["uio_v19"] = {str(k): v for k, v in uio.items()}
        for r in range(9, 14):
            v = ws.cell(r, 1).value
            if v and "Source: UIO" in str(v):
                out["uio_source_note"] = str(v)
                break
    wb.close()
    return out


def read_v19_cy_segments(db: str) -> dict:
    """V19 UIO by calendar year and segment. Empty dict if this DB is not in the overview."""
    global _V19_ROWS
    spec = V19_DIST.get(db)
    if not spec:
        return {}
    if _V19_ROWS is None:
        import openpyxl
        wb = openpyxl.load_workbook(UIO_V19_XLSX, data_only=True, read_only=True)
        ws = wb["1.UIO Overview"]
        _V19_ROWS = [row for row in ws.iter_rows(min_row=7, max_col=50, values_only=True)]
        wb.close()
    want_dist = spec["dist"].upper()
    want_ctry = (spec.get("country") or "").upper()
    out = {}
    for row in _V19_ROWS:
        dist = str(row[5] or "").upper()
        asc = str(row[4] or "").upper()
        ctry = str(row[1] or "").upper()
        if asc != "ISZE":
            continue
        if want_dist not in dist:
            continue
        if want_ctry and ctry != want_ctry:
            continue
        seg = V19_MODEL.get(str(row[3] or "").upper())
        if not seg:
            continue
        for cy in range(2023, 2028):
            col = 7 + (cy - 1990)
            v = row[col - 1]
            if v is None:
                continue
            try:
                units = float(v)
            except (TypeError, ValueError):
                continue
            if units == 0:
                continue
            out.setdefault(cy, {})
            out[cy][seg] = out[cy].get(seg, 0.0) + units
    return out


# ---------------------------------------------------------------------------
def build(db: str) -> dict:
    if db not in REGISTRY:
        raise SystemExit(f"unknown --db {db}. known: {', '.join(sorted(REGISTRY))}")
    reg = REGISTRY[db]
    sold_to = reg["sold_to"]
    seg = reg["segment"]

    dim = pd.read_csv(d("distributor_dimension.csv"))
    dimrows = dim[dim.distributor_code == db]

    v31 = read_v31(db, reg["v31_tab"])
    bp = json.load(open(BP_JSON, encoding="utf-8"))

    rate_used = LCV_RATE_OVERRIDE if LCV_RATE_OVERRIDE else LCV_RATE_CURRENT_FY27
    rate_basis = ("--lcv-rate override" if LCV_RATE_OVERRIDE
                  else "current D-Max rate FY2027, confirmed by Jerome 2026-08-14")

    L = {
        "meta": {
            "distributor_code": db,
            "display_name": reg["display"],
            "country": reg["country"],
            "segment": seg,
            "sold_to_sap": sold_to,
            "gps_label": reg["gps_label"],
            "audience": "customer" if db == "GREECE" else "internal",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "04_tools/db_operating_dashboard/build_ledger.py",
            "purpose": "Where are we with this customer — operating the account this quarter.",
            "fy_convention": "FY = Apr-Mar, labelled by END year. FY2026 = Apr 2025 - Mar 2026.",
            "anchor_chain": "_verification_report.json (green 106/0, as_of 2026-08-03) -> "
                            "metrics_snapshot.json -> FACTS.md",
            "uio_basis": "V19 — ACTUAL, confirmed by Jerome 2026-08-14. Canonical file is "
                         "06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx (V19 internally); "
                         "V3.1 reads '1.UIO Overview' detail rows from it. Never read an "
                         "archived vN copy.",
            "rate_used_eur_per_unit": rate_used if seg != "CV" else None,
            "rate_basis": rate_basis if seg != "CV" else "CV v9 rates +5% (see cv_rates)",
            "cv_rates_base_and_fy27": CV_RATES if seg in ("CV", "MIXED") else None,
        },
        "flags": {
            "SHOW_GPS_PCT": db not in GPS_PCT_NOT_QUOTABLE,
            "GPS_PCT_NOT_QUOTABLE_REASON": (
                "GPS reads at or above 100% — the denominator is wrong, not capture complete. "
                "Discuss the amount, or agree the per-unit rate first."
                if db in GPS_PCT_NOT_QUOTABLE else None),
            "HAS_V31_FY_SERIES": v31.get("fy_series") is not None,
            "LCV_RATE_IS_PROVISIONAL": False,  # Jerome confirmed €262.50 on 2026-08-14
        },
        "channel": {
            "db_factor": CHANNEL_DB_FACTOR,
            "dlr_factor": CHANNEL_DLR_FACTOR,
            "combined_factor": CHANNEL_COMBINED,
            "formula": (
                f"Projected ISZE retail = PR00 net × {CHANNEL_DB_FACTOR:.2f} (distributor) "
                f"× {CHANNEL_DLR_FACTOR:.3f} (dealer) = ×{CHANNEL_COMBINED:g}"
            ),
            "as_of": CHANNEL_AS_OF,
            "source_note": "ISZE pricing config (distributor then dealer markup). Not observed SPA terms.",
            "delta_formula": (
                "(IAM published offer − projected ISZE retail) / projected ISZE retail. "
                "Positive = ISZE cheaper at retail. Negative = ISZE dearer."
            ),
        },
        "business_plan": {
            "bp_fy27_eur": bp["by_gps_code"].get(db),
            "reviewed": bp["reviewed"],
            "network_total_eur": bp["vp_network_total_eur"],
            "source": src("01_data/91_build/bp_fy27_reviewed.json",
                          "FY2027", f"by_gps_code['{db}']",
                          f"From {os.path.basename(bp['source_xlsx'])}, "
                          f"'{bp['source_vp_turnover']}'. Ties to V3.1 Dashboard col C.",
                          green=False),
            "ext_target_fy27_eur": v31.get("ext_target_fy27_eur"),
            "stretch_pct": v31.get("stretch_pct"),
            "stretch_eur": v31.get("stretch_eur"),
            "note": "EXT TARGET = BP FY27 + stretch. Locked in V3.1 — do not recompute "
                    "from Sales-to-Dealer (the /0.65 gross-up was invalidated 17-07-2026).",
        },
        "gps_fy_spine": {},
        "hero": {},
        "sections": {},
        "empty_states": {},
        "reconciliation": {},
    }

    # GPS actuals frame — needed by plan tracking and by the FY spine below.
    gps = pd.read_csv(d(GPS_FILE))
    g = gps[gps.db == reg["gps_label"]].set_index("fy")

    # ---------------- Plan tracking: BP -> stretch -> EXT TARGET (col I) -----
    # Jerome 2026-08-14: "see if original BP matches, and also use the extended
    # target column I - make some nice graphs with it."
    bp_json = bp["by_gps_code"].get(db)
    bp_v31 = v31.get("bp_fy27_eur")
    ext = v31.get("ext_target_fy27_eur")
    maxs27 = v31.get("max_spend_fy27_eur")
    L["sections"]["plan_tracking"] = {
        "fy": 2027,
        "bp_match": {
            "bp_from_json_eur": bp_json,
            "bp_from_v31_col_C_eur": bp_v31,
            "delta_eur": r2((bp_json - bp_v31)) if (bp_json is not None and bp_v31 is not None) else None,
            "verdict": ("MATCH" if (bp_json is not None and bp_v31 is not None
                                    and abs(bp_json - bp_v31) <= max(1.0, abs(bp_v31) * 0.001))
                        else "DIFF" if (bp_json is not None and bp_v31 is not None) else "N/A"),
            "note": "Original BP (reviewed 24-04-2026) vs the BP carried in V3.1 column C. "
                    "These must agree — V3.1 is built from that BP.",
        },
        "build_up": [
            {"step": "BP FY2027", "eur": bp_v31, "kind": "plan"},
            {"step": f"Stretch {round(100*(v31.get('stretch_pct') or 0),1)}%", "eur": v31.get("stretch_eur"), "kind": "stretch"},
            {"step": "EXT TARGET FY2027", "eur": ext, "kind": "target"},
        ],
        "against_capacity": {
            "max_spend_fy27_eur": maxs27,
            "gps_pct_at_bp": v31.get("gps_pct_fy27"),
            "gps_pct_at_ext_target": v31.get("gps_pct_fy27_after_stretch"),
            "headroom_to_ceiling_eur": r2(maxs27 - ext) if (maxs27 and ext) else None,
            "over_ceiling": bool(maxs27 and ext and ext > maxs27),
        },
        "actual_vs_plan": {
            "fy_latest": FY_LATEST,
            "fy_latest_actual_eur": r2(g.loc[FY_LATEST, "pure_sales_eur"]) if FY_LATEST in g.index else None,
            "ext_target_fy27_eur": ext,
            "implied_growth_pct": (round(100 * (ext / float(g.loc[FY_LATEST, "pure_sales_eur"]) - 1), 1)
                                   if (ext and FY_LATEST in g.index and float(g.loc[FY_LATEST, "pure_sales_eur"])) else None),
        },
        "charts": [
            "Waterfall: BP FY2027 -> stretch -> EXT TARGET, with the max-spend ceiling as a "
            "reference line. If EXT TARGET sits above the ceiling, that is the story.",
            "Grouped FY bars: actual FY2024/25/26 vs EXT TARGET FY2027, one terracotta target bar.",
            "Bullet/gauge per DB: EXT TARGET against max spend, GPS% at BP vs GPS% at target.",
        ],
        "source": src("01_data/ISZE_GPS_Extended_Target_FY27_V3.1.xlsx",
                      "FY2027", f"Dashboard row {v31.get('dashboard_row')} cols C/D/E/F/G/H/I",
                      "Col I = EXT TARGET, locked. Do not recompute from Sales-to-Dealer.",
                      green=False),
        "basis_note": v31.get("basis_note"),
    }

    # ---------------- Re-rate max spend at the CURRENT D-Max rate -----------
    # V3.1 published its max spend on the MH LCV chain (219.5648 / 230.5430). The current
    # rate is 262.50 (FY27) / 250.00 (base). Only the LCV segment moves; CV rates hold.
    # V3.1 tabs start FY2025. FY2024 uses the same formula on V19 CY2023 parc
    # (workbook source note: CY N → FY N+1). Not a calendar-year GPS%, not the wallet file.
    lcv_fy27 = LCV_RATE_OVERRIDE if LCV_RATE_OVERRIDE else LCV_RATE_CURRENT_FY27
    lcv_base = lcv_fy27 / 1.05
    have_v31_uio = bool(v31.get("uio_by_segment"))
    seg_uio = {k: dict(v) for k, v in (v31.get("uio_by_segment") or {}).items()}
    v19_cy = read_v19_cy_segments(db) if have_v31_uio else {}
    v19_fy_injected = []
    for cy, segs in v19_cy.items():
        fy = cy + 1
        if fy < 2024 or fy > 2027:
            continue
        filled = False
        for segname, units in segs.items():
            seg_uio.setdefault(segname, {})
            if not seg_uio[segname].get(str(fy)):
                seg_uio[segname][str(fy)] = units
                filled = True
        if filled:
            v19_fy_injected.append(fy)
    rerated: dict[int, dict] = {}
    if seg_uio:
        for y in (2024, 2025, 2026, 2027):
            is_fy27 = (y == 2027)
            total, parts = 0.0, {}
            for segname, trio in seg_uio.items():
                units = trio.get(str(y))
                if not units:
                    continue
                if segname == "LCV":
                    rate = lcv_fy27 if is_fy27 else lcv_base
                else:
                    if segname not in CV_RATES:
                        continue
                    base, fy27 = CV_RATES[segname]
                    rate = fy27 if is_fy27 else base
                amt = float(units) * rate
                parts[segname] = {"uio_units": int(round(float(units))), "rate_eur": round(rate, 4),
                                  "max_spend_eur": r2(amt), "uio_cy": y - 1}
                total += amt
            if total:
                rerated[y] = {
                    "max_spend_eur": r2(total),
                    "by_segment": parts,
                    "uio_cy": y - 1,
                    "uio_units": int(round(sum(p["uio_units"] for p in parts.values()))),
                    "rate_set": "FY27 +5%" if is_fy27 else "base (LCV €250 / CV v9)",
                    "method": (
                        f"max-spend = Σ (V19 UIO segment × ISZE-net rate). "
                        f"Parc is V19 calendar {y-1}, mapped to FY{y} (locked-workbook shift). "
                        f"LCV €{lcv_fy27 if is_fy27 else lcv_base:.2f}; "
                        "LD €739 / MD €887 / F-Series €887 at base."
                    ),
                }

    L["sections"]["rate_change_impact"] = {
        "current_lcv_rate_eur": lcv_fy27,
        "current_lcv_rate_base_eur": round(lcv_base, 4),
        "confirmed_by": "Jerome 2026-08-14 — 'GPS dmax is now already 260 something ... "
                        "262.50 this is the current'",
        "derivation": "262.50 / 1.05 = 250.00 = gps_model_targets.csv LCV_D_Max. 250.00 is the "
                      "base, 262.50 is FY2027 (+5%). Today sits inside FY2027.",
        "supersedes": {
            "v31_mh_lcv_chain": V31_LCV_CHAIN,
            "why": "The MH chain applies FX 1.16 and the 0.65 margin twice — V3.1's own Method "
                   "tab flags the conflict at A19-A21 (24.6% apart) and says it was carried, "
                   "not fixed.",
        },
        "cv_rates_unchanged": CV_RATES if seg_uio and set(seg_uio) - {"LCV"} else None,
        "applies_to_lcv_only": True,
        "rerated_max_spend": rerated or None,
        "v19_fy_backfilled": v19_fy_injected,
        "v19_mapping": "Calendar year N in 06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx → FY N+1. Same shift as V3.1 source note.",
        "not_rerated_reason": (None if seg_uio else
                               f"{db} has no per-FY V3.1 tab (V4 as-presented basis), so there is "
                               "no segment UIO split to re-rate. Dashboard figures stand as "
                               "published. The LCV rate change does not apply to a CV DB anyway."),
    }

    # ---------------- GPS FY spine (the primary, V19-based, FY-grain) --------
    fy_rows = []
    v31fy = v31.get("fy_series") or {}
    for fy in sorted(g.index):
        row = g.loc[fy]
        maxs_v31 = (v31fy.get(fy) or {}).get("max_spend_eur")
        maxs_rerated = (rerated.get(fy) or {}).get("max_spend_eur")
        # Same method every complete FY: V19 parc × that year's ISZE-net rate.
        maxs = maxs_rerated or maxs_v31
        actual = float(row.pure_sales_eur)
        exw = row.get("pure_sales_ex_warranty_eur")
        exw_ok = pd.notna(exw) and float(exw) > 0
        rr = rerated.get(fy) or {}
        uio_units = rr.get("uio_units") or (v31fy.get(fy) or {}).get("uio_units")
        if maxs_rerated:
            basis = (
                f"V19 × base ISZE-net rate (CY{fy-1} → FY{fy})"
                if fy <= 2026 else
                f"V19 × FY27 D-Max rate (CY{fy-1} → FY{fy})"
            )
        else:
            basis = "V3.1 as published"
        rec = {
            "fy": int(fy),
            "uio_units_v19": uio_units,
            "uio_cy": rr.get("uio_cy"),
            "max_spend_eur": maxs,
            "max_spend_basis": basis,
            "max_spend_eur_v31_published": maxs_v31,
            "max_spend_method": rr.get("method"),
            "max_spend_by_segment": rr.get("by_segment"),
            "actual_eur": r2(actual),
            "warranty_eur": r2(row.get("warranty_eur")),
            "ex_warranty_eur": r2(exw),
            "ex_warranty_renderable": bool(exw_ok),
            "shell_lubricants_excluded_eur": r2(row.get("shell_lubricants_eur")),
            "flags": str(row.get("notes") or ""),
            "partial_year": int(fy) == 2023 or "fy23_partial" in str(row.get("notes") or ""),
            "publish": int(fy) != 2023 and int(fy) <= FY_LATEST,
        }
        if maxs:
            rec["gps_pct"] = round(100 * actual / maxs, 2)
            rec["gps_pct_ex_warranty"] = round(100 * float(exw) / maxs, 2) if exw_ok else None
        if maxs_v31:
            rec["gps_pct_v31_published"] = round(100 * actual / maxs_v31, 2)
        rec["tooltip"] = {
            "formula": (
                (rr.get("method") or "GPS% = GPS-eligible billed ÷ max-spend.")
                + (f" Numerator €{r2(actual)} ÷ max-spend €{maxs}." if maxs else "")
            ),
            "snapshot": (
                f"FY{fy} · V19 CY{fy-1} parc · "
                + (rr.get("rate_set") or basis)
                + " · 06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx"
            ),
            "not_included": (
                "FY2023 (partial). Shell lubricants. Not a calendar-year GPS%. "
                "Wallet file is a different basket. V3.1 MH LCV chain is audit trail only."
            ),
        }
        fy_rows.append(rec)

    fy_pub = [r for r in fy_rows if r.get("publish")]
    years_with_pct = [r["fy"] for r in fy_pub if r.get("gps_pct") is not None]
    years_euro_only = [r["fy"] for r in fy_pub if r.get("gps_pct") is None and r.get("actual_eur") is not None]
    L["gps_fy_spine"] = {
        "rows": fy_rows,
        "v31_dashboard": {k: v for k, v in v31.items() if k != "fy_series"},
        "v31_fy_series": v31fy or None,
        "source_actuals": src(f"01_data/00_derived/{GPS_FILE}",
                              "fiscal year (Apr-Mar), end-year label",
                              f"db == '{reg['gps_label']}'",
                              "pure_sales_eur = billing_clean less Shell lubricants, other "
                              "exclusions and CR credits. Freight/surcharge stripped upstream.",
                              green=False),
        "source_denominator": src("06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx + V3.1 tab",
                                  "fiscal year (CY N parc → FY N+1)", f"db '{db}' / tab '{reg['v31_tab']}'",
                                  "max spend = V19 UIO × ISZE-net rate/unit. LCV €250 base / €262.50 FY27. "
                                  "FY2024 uses CY2023. Same method as FY2025–FY2026. V3.1 published MH chain kept as audit.",
                                  green=False),
        "chart": "Complete fiscal years FY2024–FY2026. Two lines: GPS% and GPS% ex-warranty. "
                 "Y-axis 0–100. Same V19 × rate method on every year. FY2023 is not published.",
        "years_with_gps_pct": years_with_pct,
        "years_euro_only_no_gps_pct": years_euro_only,
        "publish_years": [r["fy"] for r in fy_pub],
        "method_one_line": (
            "GPS% = GPS-eligible billed ÷ (V19 parc × that year’s ISZE-net rate). "
            "Calendar year N maps to FY N+1. Not a CY GPS%."
        ),
        "skip_incomplete": {
            "fy": 2023,
            "reason": "FY2023 is a partial year. It is not published — a partial bar would be read as growth.",
        },
        "euro_only_caption": (
            "Euros are the GPS-eligible billed numerator on the same complete fiscal years. "
            "GPS% uses V19 parc × that year’s ISZE-net rate for FY2024, FY2025 and FY2026."
        ),
        "render_rules": [
            "Do not publish FY2023. It is incomplete.",
            "FY2024–FY2026 complete years only, one method: V19 parc × ISZE-net rate (CY N → FY N+1).",
            "Two lines: GPS% and GPS% ex-warranty. Blank point if ex-warranty euro is invalid — not a zero.",
            "Any row with ex_warranty_renderable false must not draw a bar or a point.",
            "Y-axis for GPS% is 0–100. Y-axis for euros starts at 0. Never zoom 55–70%.",
            "No CY GPS% unless a published calendar-year GPS workbook figure exists. Do not invent one from the wallet.",
        ],
        "grain_control": {
            "default": "FY",
            "on_screen_label_fy": "Fiscal year (Apr–Mar, labelled by end year) — complete years only",
            "show_cy_toggle": False,
            "fy": {
                "available": True,
                "label": "FY",
            },
            "cy": {
                "available": False,
                "label": "CY",
                "disabled_reason": (
                    "The locked GPS workbook is fiscal-year only. No published calendar-year GPS% "
                    "exists for this distributor. A CY GPS% will not be invented from the wallet file "
                    "(different rate, different basket)."
                ),
            },
        },
    }
    if not v31fy:
        L["gps_fy_spine"]["no_fy_series_reason"] = (
            f"{db} has no per-FY tab in V3.1 — it sits on the V4 as-presented basis "
            "(Dashboard row only). FY GPS% series unavailable; use the Dashboard FY27 figures "
            "and show euros for history. Do not synthesise a series.")
        L["gps_fy_spine"]["grain_control"]["fy"]["available"] = bool(fy_rows)
        L["gps_fy_spine"]["grain_control"]["fy"]["note"] = (
            "Euros from the GPS actuals file. No fiscal GPS% series in the locked workbook."
        )

    # ---------------- PMS (complete CY, line_type=total) --------------------
    pms = pd.read_csv(d("pms_capture_by_db_year.csv"))
    ptot = pms[(pms.line_type == "total") & (pms.year == CY_LATEST)]
    pu = ptot[ptot.distributor_code == db]
    has_pms = len(pu) > 0

    if has_pms:
        pgen = pms[(pms.line_type == "genuine") & (pms.year == CY_LATEST) & (pms.distributor_code == db)]
        cap = pu.actual_qty.sum() / pu.expected_qty.sum()
        cap_gen = pgen.actual_qty.sum() / pgen.expected_qty.sum()
        net_cap = ptot.actual_qty.sum() / ptot.expected_qty.sum()
        pms_block = {
            "available": True,
            "year": CY_LATEST,
            "sold_to_sap": sold_to,
            "distributor_code": db,
            "gps_label": reg["gps_label"],
            "not_ireland": 76 not in sold_to,
            "not_ituk": 2575 not in sold_to,
            "capture_pct_total": round(100 * cap, 2),
            "capture_pct_genuine": round(100 * cap_gen, 2),
            "network_capture_pct": round(100 * net_cap, 2),
            "vs_network_pp": round(100 * (cap - net_cap), 1),
            "expected_qty": r2(pu.expected_qty.sum()),
            "actual_qty": r2(pu.actual_qty.sum()),
            "audit": {
                "file": "pms_capture_by_db_year.csv",
                "filter": f"distributor_code == '{db}' AND line_type == 'total' AND year == {CY_LATEST}",
                "sold_to_sap": sold_to,
                "expected_qty": r2(pu.expected_qty.sum()),
                "actual_qty": r2(pu.actual_qty.sum()),
                "capture_pct": round(100 * cap, 4),
                "arithmetic": (
                    f"{r2(pu.actual_qty.sum())} sold ÷ {r2(pu.expected_qty.sum())} expected "
                    f"= {round(100 * cap, 2)}%"
                ),
                "network_actual_qty": r2(ptot.actual_qty.sum()),
                "network_expected_qty": r2(ptot.expected_qty.sum()),
                "network_capture_pct": round(100 * net_cap, 4),
                "not_ireland_76": 76 not in sold_to,
                "not_ituk_2575": 2575 not in sold_to,
            },
            "revenue_eur": r2(pu.actual_rev_eur.sum()),
            "quotable_gap_eur": r2(pu[pu.revenue_gap_quotable == True].revenue_gap_eur.sum()),
            "categories_quotable": int(pu.revenue_gap_quotable.sum()),
            "categories_total": int(len(pu)),
            "by_category": sorted([
                {
                    "pms_category": rw.pms_category,
                    "label": rw.category_label,
                    "capture_pct": round(100 * rw.capture_rate, 2),
                    "network_capture_pct": round(
                        100 * ptot[ptot.pms_category == rw.pms_category].actual_qty.sum()
                        / ptot[ptot.pms_category == rw.pms_category].expected_qty.sum(), 2),
                    "expected_qty": r2(rw.expected_qty),
                    "actual_qty": r2(rw.actual_qty),
                    "revenue_eur": r2(rw.actual_rev_eur),
                    "revenue_gap_eur": r2(rw.revenue_gap_eur),
                    "quotable": bool(rw.revenue_gap_quotable),
                    "avg_sp_eur": r2(rw.avg_sp_eur),
                    "interval_confidence": (
                        "CONFIRMED" if rw.pms_category in ("oil_filter", "fuel_filter")
                        else "PROVISIONAL" if rw.pms_category == "air_filter"
                        else "NO OEM INTERVAL" if rw.pms_category in ("urea_filter", "blower_filter")
                        else "WEAR ITEM"),
                } for _, rw in pu.iterrows()],
                key=lambda x: -(x["revenue_gap_eur"] or 0)),
            "source": src("01_data/00_derived/pms_capture_by_db_year.csv",
                          f"complete CY{CY_LATEST}",
                          f"distributor_code == '{db}' AND line_type == 'total'",
                          "line_type is genuine/bvp/total — summing all three triple-counts. "
                          f"Sold-to on this pack: {sold_to}. Not Ireland 76, not ITUK 2575 unless those are this DB.",
                          green=True),
            "tooltip": {
                "formula": (
                    f"{r2(pu.actual_qty.sum())} sold ÷ {r2(pu.expected_qty.sum())} expected "
                    f"= {round(100 * cap, 2)}%. line_type = total, complete calendar year, "
                    "same expected-quantity model as the network. "
                    f"{reg['display']}, sold-to {sold_to}."
                ),
                "snapshot": f"Complete CY{CY_LATEST} · expected-qty model (not the partial-year by-DB summary)",
                "not_included": (
                    "Partial-year 2026 file. Frozen UIO — do not chart capture over time. "
                    "Ireland sold-to 76 and ITUK 2575 are other packs. Quotable categories only in the euro gap."
                ),
            },
            "render_rules": [
                "Never present bare — always against the network on the same expected-qty model.",
                "Do NOT chart capture over time: uio_units is frozen identical across all years "
                "for every DB. Only the numerator moves.",
                "Grey non-quotable categories and keep them out of every euro total.",
            ],
            "do_not_use": {
                "file": "01_data/00_derived/pms_summary_by_db.csv",
                "reason": "Contains year 2026 ONLY, and CY2026 is Jan-Mar actual against a "
                          "FULL-YEAR expected_qty. Structurally understates by ~4x.",
            },
        }
        for cat in pms_block["by_category"]:
            if cat.get("capture_pct") is not None and cat.get("network_capture_pct") is not None:
                cat["vs_network_pp"] = round(cat["capture_pct"] - cat["network_capture_pct"], 1)
    else:
        pms_block = {"available": False,
                     "reason": f"{db} has no rows in pms_capture_by_db_year.csv. "
                               "PMS covers 18 of 22 network DBs; CIS and Palestine have none."}
    L["sections"]["pms"] = pms_block

    # ---------------- Replenishment CY2025 (network DBs with sell-out) -------
    repl_summary_path = os.path.join(DERIVED, "replenishment_summary_cy2025.parquet")
    repl_block: dict = {"available": False}
    NETWORK_REPL = {"ITUK", "UTI", "IRELAND", "IUK", "GREECE"}
    if db in NETWORK_REPL and os.path.isfile(repl_summary_path):
        rs = pd.read_parquet(repl_summary_path)
        sub = rs[rs["distributor_code"] == db]
        if not sub.empty:
            bill = float(sub["bill_qty"].sum())
            sell = float(sub["sellout_qty"].sum())
            sig = sub["pipeline_signal"].value_counts().to_dict()
            repl_block = {
                "available": True,
                "year": 2025,
                "pn_count": int(sub["part_number"].nunique()),
                "bill_qty": round(bill, 1),
                "sellout_qty": round(sell, 1),
                "sell_through_ratio": round(sell / bill, 3) if bill > 0 else None,
                "pipeline_leakage_pns": int(
                    sig.get("leakage_high_sellthrough", 0) + sig.get("leakage_no_bill", 0)
                ),
                "pipeline_overstock_pns": int(
                    sig.get("overstock_low_sellthrough", 0) + sig.get("overstock_no_sellout", 0)
                ),
                "tooltip": {
                    "formula": "Sell-through = dealer sell-out qty ÷ ISZE bill qty (CY2025, network PN grain).",
                    "snapshot": "replenishment_summary_cy2025.parquet",
                    "not_included": "UTI≠UMI · IUK≠ITUK · IRELAND≠IUK. ITUK dealer grain is a separate bridge file.",
                },
                "israel_note": "UTI_only_not_UMI" if db == "UTI" else (
                    "IUK_not_ITUK" if db == "IUK" else (
                        "IRELAND_not_IUK" if db == "IRELAND" else ""
                    )
                ),
            }
    L["sections"]["replenishment_cy2025"] = repl_block

    # ---------------- Wallet CY (cross-check only) --------------------------
    wal = pd.read_csv(d("wallet_waterfall.csv"))
    ww = wal[wal.distributor_code == db]
    if len(ww):
        w = ww[ww.year == CY_LATEST].iloc[0]
        L["sections"]["wallet_cy"] = {
            "status": "CROSS-CHECK ONLY — baked at EUR 250.00/unit, not re-rated",
            "year": int(w.year),
            "uio_units": int(w.uio_units),
            "implied_rate_eur_per_unit": r2(w.theoretical_wallet_eur / w.uio_units),
            "ceiling_eur": r2(w.theoretical_wallet_eur),
            "captured_total_eur": r2(w.captured_total_eur),
            "captured_genuine_eur": r2(w.captured_genuine_eur),
            "captured_bvp_eur": r2(w.captured_bvp_eur),
            "addressable_uncaptured_eur": r2(w.addressable_uncaptured_eur),
            "bvp_share_of_captured_pct": r2(w.bvp_share_of_captured_pct),
            "gps_pct_at_250": r2(w.gps_pct),
            "rows_all_years": [
                {"year": int(rw.year), "ceiling_eur": r2(rw.theoretical_wallet_eur),
                 "captured_genuine_eur": r2(rw.captured_genuine_eur),
                 "captured_bvp_eur": r2(rw.captured_bvp_eur),
                 "captured_total_eur": r2(rw.captured_total_eur),
                 "addressable_uncaptured_eur": r2(rw.addressable_uncaptured_eur)}
                for _, rw in ww.sort_values("year").iterrows()],
            "source": src("01_data/00_derived/wallet_waterfall.csv", "calendar year",
                          f"distributor_code == '{db}'",
                          "Ceiling, age-flat, not a forecast. No year 2026 in the file.",
                          green=False),
            "warning": "This file's rate (EUR 250.00) disagrees with V3.1's LCV chain. "
                       "Use the V3.1 FY spine for any GPS %. This block is the CY waterfall "
                       "shape and the genuine/BVP split only.",
        }
    else:
        L["sections"]["wallet_cy"] = {"available": False,
                                      "reason": f"{db} has no wallet_waterfall rows (18-market file)."}

    # ---------------- sales_fact: book, mix, SaTy, cadence, working set -----
    sf = pd.read_parquet(d("sales_fact.parquet"),
                         columns=["billing_date", "sold_to_sap", "part_number", "description",
                                  "billed_qty", "net_sales_value", "saty", "year"])
    u = sf[sf.sold_to_sap.isin(sold_to)].copy()
    u["cy"] = u.billing_date.dt.year
    u["fy"] = u.billing_date.map(fy_end_year)

    xref = pd.read_csv(d("genuine_bvp_crossref.csv"), dtype=str)
    bvp_pns = set(xref.bvp_pn.dropna().astype(str))
    gen_pns = set(xref.genuine_pn.dropna().astype(str))
    xref_pms = {}
    if "pms_category" in xref.columns:
        for _, rw in xref.iterrows():
            cat = rw.get("pms_category")
            if pd.isna(cat) or not str(cat).strip():
                continue
            for col in ("bvp_pn", "genuine_pn"):
                pn = str(rw.get(col) or "")
                if pn:
                    xref_pms[pn] = str(cat)

    cat_path = d("parts_catalog_dimension.csv")
    pms_map, pms_lab = dict(xref_pms), {}
    if os.path.exists(cat_path):
        cat = pd.read_csv(cat_path, dtype={"part_number": str},
                          usecols=["part_number", "pms_category", "fig_key_label"],
                          low_memory=False)
        cat = cat.dropna(subset=["pms_category"])
        cat = cat[cat.pms_category.astype(str).str.strip() != ""]
        for _, rw in cat.iterrows():
            pn = str(rw.part_number)
            pms_map.setdefault(pn, str(rw.pms_category))
            pms_lab[pn] = str(rw.fig_key_label)

    book = u[(u.cy == CY_LATEST) & (u.saty != "CR")]
    book_tot = book.net_sales_value.sum()
    book_pn_str = book.part_number.astype(str)
    is_bvp_line = book_pn_str.isin(bvp_pns)
    book_bvp = book.loc[is_bvp_line, "net_sales_value"].sum()
    n_pns = int(book_pn_str.nunique())
    n_bvp_pns = int(book_pn_str[is_bvp_line].nunique())
    n_gen_pns = n_pns - n_bvp_pns

    mix = pd.read_csv(d("mix_genuine_bvp_by_group.csv"))
    mu = mix[(mix.distributor_code == db) & (mix.year == CY_LATEST)]

    def mix_slice(frame):
        if not len(frame):
            return None
        tot = float(frame.net_sales_value.sum())
        bvp_e = float(frame.loc[frame.part_number.astype(str).isin(bvp_pns), "net_sales_value"].sum())
        pns = frame.part_number.astype(str)
        n_all = int(pns.nunique())
        n_b = int(pns[pns.isin(bvp_pns)].nunique())
        return {
            "total_eur": r2(tot),
            "genuine_eur": r2(tot - bvp_e),
            "bvp_eur": r2(bvp_e),
            "genuine_share_pct": round(100 * (tot - bvp_e) / tot, 1) if tot else None,
            "bvp_share_pct": round(100 * bvp_e / tot, 1) if tot else None,
            "n_pns": n_all,
            "n_pns_bvp": n_b,
            "n_pns_genuine": n_all - n_b,
        }

    cy_evol, fy_evol = [], []
    nocred = u[u.saty != "CR"]
    for cy, g in nocred.groupby("cy"):
        if int(cy) > CY_LATEST:
            continue
        rec = mix_slice(g)
        if rec:
            rec["cy"] = int(cy)
            rec["complete"] = True
            cy_evol.append(rec)
    for fy, g in nocred.groupby("fy"):
        if int(fy) > FY_LATEST or int(fy) == 2023:
            continue
        rec = mix_slice(g)
        if rec:
            rec["fy"] = int(fy)
            rec["complete"] = True
            fy_evol.append(rec)

    def bvp_tier_year(frame, year_key, year_val):
        g = frame.copy()
        g["pn"] = g.part_number.astype(str)
        g = g[g.pn.isin(bvp_pns)]
        g["pms_cat"] = g.pn.map(pms_map).fillna("other")
        out = {"year": year_val, "grain": year_key}
        filt = g[g.pms_cat.isin(FILTER_PMS)]
        out["filter_family"] = {
            "label": "Filter family",
            "eur": r2(filt.net_sales_value.sum()),
            "qty": r2(filt.billed_qty.sum()),
            "n_pns": int(filt.pn.nunique()) if len(filt) else 0,
        }
        core = []
        for cat, lab in (("oil_filter", "Oil filter"), ("air_filter", "Air filter"), ("fuel_filter", "Fuel filter")):
            s = g[g.pms_cat == cat]
            core.append({
                "pms_category": cat, "label": lab,
                "eur": r2(s.net_sales_value.sum()),
                "qty": r2(s.billed_qty.sum()),
                "n_pns": int(s.pn.nunique()) if len(s) else 0,
            })
        out["by_filter"] = core
        pn_rows = (g.groupby(["pn", "description", "pms_cat"])
                   .agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"))
                   .reset_index().sort_values("eur", ascending=False).head(15))
        out["top_pns"] = [
            {"pn": str(rw.pn), "description": rw.description, "pms_category": rw.pms_cat,
             "eur": r2(rw.eur), "qty": r2(rw.qty)}
            for _, rw in pn_rows.iterrows()
        ]
        return out

    bvp_cy_tiers = [bvp_tier_year(nocred[nocred.cy == cy], "CY", int(cy))
                    for cy in sorted(nocred.cy.unique()) if int(cy) <= CY_LATEST]
    bvp_fy_tiers = [bvp_tier_year(nocred[nocred.fy == fy], "FY", int(fy))
                    for fy in sorted(nocred.fy.unique()) if int(fy) <= FY_LATEST and int(fy) != 2023]

    L["sections"]["genuine_vs_bvp"] = {
        "whole_book": {
            "year": CY_LATEST,
            "total_eur": r2(book_tot),
            "genuine_eur": r2(book_tot - book_bvp),
            "bvp_eur": r2(book_bvp),
            "genuine_share_pct": round(100 * (book_tot - book_bvp) / book_tot, 1) if book_tot else None,
            "bvp_share_pct": round(100 * book_bvp / book_tot, 1) if book_tot else None,
            "n_pns": n_pns,
            "n_pns_bvp": n_bvp_pns,
            "n_pns_genuine": n_gen_pns,
            "THIS_IS_THE_ONE_TO_SHOW": True,
            "audit": {
                "total_eur": r2(book_tot),
                "genuine_eur": r2(book_tot - book_bvp),
                "bvp_eur": r2(book_bvp),
                "n_pns": n_pns,
                "n_pns_genuine": n_gen_pns,
                "n_pns_bvp": n_bvp_pns,
                "bvp_share_pct": round(100 * book_bvp / book_tot, 4) if book_tot else None,
                "arithmetic": (
                    f"BVP €{r2(book_bvp)} / {n_bvp_pns} PNs of book €{r2(book_tot)} / {n_pns} PNs "
                    f"= {round(100 * book_bvp / book_tot, 2) if book_tot else 0}%"
                ),
                "definition": "part_number in genuine_bvp_crossref.bvp_pn · complete CY · credits out · whole book",
                "not_the_paired_basket": True,
            },
            "tooltip": {
                "formula": (
                    f"BVP €{r2(book_bvp)} on {n_bvp_pns} PNs ÷ book €{r2(book_tot)} on {n_pns} PNs "
                    f"= {round(100 * book_bvp / book_tot, 2) if book_tot else 0}%. "
                    "BVP = billed net on part numbers in the Best Value column of the genuine↔Best Value crossref. "
                    "Genuine = the rest of this sold-to’s complete-CY book. Credits excluded, never subtracted."
                ),
                "snapshot": f"CY{CY_LATEST} complete · sold-to {sold_to} · whole parts book",
                "not_included": (
                    "Not the paired-basket file (that is a subset of euros where both a genuine and a "
                    "Best Value PN exist). That trap is labelled separately and is not this distributor’s mix."
                ),
            },
            "source": src("01_data/00_derived/sales_fact.parquet + genuine_bvp_crossref.csv",
                          "calendar year, whole parts book",
                          f"sold_to_sap in {sold_to} AND year == {CY_LATEST} AND saty != 'CR'",
                          "BVP = part_number in crossref.bvp_pn. Reproduces metrics_snapshot.json "
                          "exactly (UTI 88.9%, ITUK 97.3%) — this is the anchor definition.",
                          green=True),
        },
        "paired_basket_only": ({
            "total_eur": r2(mu.total_eur.sum()),
            "bvp_share_pct": round(100 * mu.bvp_eur.sum() / mu.total_eur.sum(), 1),
            "coverage_pct_of_book": round(100 * mu.total_eur.sum() / book_tot, 1) if book_tot else None,
            "THIS_IS_THE_ONE_TO_SHOW": False,
            "DANGER": "Crossref-PAIRED basket only. Its BVP share is not the DB's BVP share. "
                      "If charted, the coverage % must appear on the chart itself.",
            "by_group": [
                {"group": rw.product_group_label, "genuine_eur": r2(rw.genuine_eur),
                 "bvp_eur": r2(rw.bvp_eur), "bvp_share_eur_pct": round(100 * rw.bvp_share_eur, 1)}
                for _, rw in mu.iterrows()],
            "source": src("01_data/00_derived/mix_genuine_bvp_by_group.csv", "calendar year",
                          f"distributor_code == '{db}' AND year == {CY_LATEST}", green=False),
        } if len(mu) else {"available": False}),
        "convention": "Genuine -> Best Value is in-tent retention and a gross-margin question. "
                      "Never placed in an erosion total, never coloured red. Only IAM defection "
                      "is real erosion.",
        "evolution": {
            "cy": cy_evol,
            "fy": fy_evol,
            "skip_incomplete": "CY after the last complete calendar year, FY2023 (partial), and FY after the last complete fiscal year are not published.",
        },
        "bvp_they_buy": {
            "lead": "Three-tier drill of Best Value they actually buy: filter family → oil / air / fuel → part number. Complete years only.",
            "cy": bvp_cy_tiers,
            "fy": bvp_fy_tiers,
            "core_filters": list(FILTER_CORE),
        },
    }

    # SaTy — PRD counts as stock on the 80/20 screen (Jerome 2026-08-14)
    def saty_mix_rows(frame, year_col, complete_fn, skip_years=()):
        hist = frame.pivot_table(index=year_col, columns="saty", values="net_sales_value",
                                 aggfunc="sum").fillna(0)
        hord = hist.drop(columns=[c for c in NON_ORDER_SATY if c in hist.columns], errors="ignore")
        if hord.empty:
            return [], sorted(set(hord.columns) - RUSH - STOCK_AS_SOR)
        shr = (100 * hord.div(hord.sum(axis=1), axis=0)).round(1)
        rows = []
        for yr in shr.index:
            yi = int(yr)
            if yi in skip_years:
                continue
            mixd = {c: float(shr.loc[yr, c]) for c in shr.columns if shr.loc[yr, c] != 0}
            other_codes = sorted(k for k in mixd if k not in RUSH and k not in STOCK_AS_SOR)
            other_pct = round(sum(mixd[k] for k in other_codes), 1)
            rec = {
                year_col: yi,
                "complete": bool(complete_fn(yi)),
                "mix_pct": mixd,
                "rush_class_pct": round(sum(v for k, v in mixd.items() if k in RUSH), 1),
                "stock_pct": round(sum(v for k, v in mixd.items() if k in STOCK_AS_SOR), 1),
                "prd_in_stock_pct": round(mixd.get("PRD", 0.0), 1),
                "other_coded_pct": other_pct,
                "other_coded_codes": other_codes,
            }
            if year_col == "cy":
                rec["complete_cy"] = rec["complete"]
            rows.append(rec)
        unmapped = sorted(set(shr.columns) - RUSH - STOCK_AS_SOR)
        return rows, unmapped

    saty_rows, unmapped = saty_mix_rows(u, "cy", lambda y: y <= CY_LATEST)
    fy_saty_rows, _ = saty_mix_rows(u, "fy", lambda y: y <= FY_LATEST and y != 2023, skip_years={2023})
    other_by_year = []
    for r in saty_rows:
        if not r["complete"]:
            continue
        codes = r["other_coded_codes"]
        other_by_year.append({
            "cy": r["cy"],
            "pct": r["other_coded_pct"],
            "codes": codes,
            "eur_share_by_code": {k: r["mix_pct"].get(k) for k in codes},
        })

    q1 = pd.read_csv(d("q1fy2027_export_with_saty.csv"))
    q1["s"] = q1.SaTy.astype(str).str.strip()
    qu = q1[q1.Sold_to.isin(sold_to)]
    qc = qu[~qu.s.isin(["nan", ""])]
    qb = qu[~qu.s.isin(["nan", ""] + sorted(NON_ORDER_SATY))]
    coded_pct = round(100 * qc.EUR_Amount.sum() / qu.EUR_Amount.sum(), 1) if len(qu) and qu.EUR_Amount.sum() else None
    q1mix = ((100 * qb.groupby("s").EUR_Amount.sum() / qb.EUR_Amount.sum()).round(1)
             if len(qb) and qb.EUR_Amount.sum() else pd.Series(dtype=float))
    q1_rush = round(sum(float(v) for k, v in q1mix.items() if k in RUSH), 1)
    q1_stock = round(sum(float(v) for k, v in q1mix.items() if k in STOCK_AS_SOR), 1)

    d_last = u[u.cy == CY_LATEST]
    wd = d_last.groupby(d_last.billing_date.dt.dayofweek).net_sales_value.sum()
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Meeting read that replaces ISZE invoicing rhythm (billing weekday is not a customer clock).
    cat_path = d("parts_catalog_dimension.csv")
    pms_map = {}
    pms_lab = {}
    if os.path.exists(cat_path):
        cat = pd.read_csv(cat_path, dtype={"part_number": str},
                          usecols=["part_number", "pms_category", "fig_key_label"],
                          low_memory=False)
        cat = cat.dropna(subset=["pms_category"])
        cat = cat[cat.pms_category.astype(str).str.strip() != ""]
        pms_map = dict(zip(cat.part_number.astype(str), cat.pms_category.astype(str)))
        pms_lab = dict(zip(cat.part_number.astype(str), cat.fig_key_label.astype(str)))
    fam_book = book.copy()
    fam_book["pn"] = fam_book.part_number.astype(str)
    fam_book["pms_cat"] = fam_book.pn.map(pms_map).fillna("not_pms")
    fam_book["pms_lab"] = fam_book.pn.map(pms_lab).fillna("Not a PMS part")
    fam_book["lane"] = fam_book.saty.map(
        lambda s: "rush" if s in RUSH else ("stock" if s in STOCK_AS_SOR else "other_coded"))
    fam_rows = []
    for (catk, lab), g in fam_book.groupby(["pms_cat", "pms_lab"]):
        tot = float(g.net_sales_value.sum())
        rush_e = float(g.loc[g.lane == "rush", "net_sales_value"].sum())
        stock_e = float(g.loc[g.lane == "stock", "net_sales_value"].sum())
        other_e = float(g.loc[g.lane == "other_coded", "net_sales_value"].sum())
        fam_rows.append({
            "pms_category": catk,
            "label": lab,
            "total_eur": r2(tot),
            "stock_eur": r2(stock_e),
            "rush_eur": r2(rush_e),
            "other_coded_eur": r2(other_e),
            "rush_pct": round(100 * rush_e / tot, 1) if tot else None,
            "stock_pct": round(100 * stock_e / tot, 1) if tot else None,
            "other_coded_pct": round(100 * other_e / tot, 1) if tot else None,
        })
    fam_rows.sort(key=lambda x: -(x["rush_eur"] or 0))
    rush_book = fam_book[fam_book.lane == "rush"]
    top_rush = (rush_book.groupby(["pn", "description"])
                .agg(rush_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"))
                .reset_index().sort_values("rush_eur", ascending=False).head(12))
    latest_cy_mix = next((r for r in reversed(saty_rows) if r["complete"]), {}) or {}
    latest_fy_mix = next((r for r in reversed(fy_saty_rows) if r["complete"]), {}) or {}
    cy_coded = 100.0 - 0.0  # sales_fact billed mix is coded; credits already out of the mix base
    if latest_cy_mix:
        # unmapped (other coded) still counts as coded — it is a billed code, just not stock/rush
        cy_coded = round(latest_cy_mix.get("stock_pct", 0) + latest_cy_mix.get("rush_class_pct", 0)
                         + latest_cy_mix.get("other_coded_pct", 0), 1)

    L["sections"]["order_pattern"] = {
        "guideline": {
            "stock_pct": 80, "rush_class_pct": 20,
            "rush_codes": sorted(RUSH),
            "stock_codes": sorted(STOCK_AS_SOR),
            "prd_counts_as_stock": True,
            "tooltip": {
                "formula": "Stock = SOR + PRD. Rush = VOR / RUSH / SVOR. PRD is treated as stock on this screen.",
                "snapshot": f"Complete CY through {CY_LATEST} and complete FY through {FY_LATEST} · sold-to {sold_to}",
                "not_included": "Credits. Incomplete years. Not invoicing-by-weekday.",
            },
        },
        "history": {
            "rows": saty_rows,
            "fy_rows": fy_saty_rows,
            "prd_folded_into_stock": True,
            "coded_share_note": "SaTy is coded on ~100% of euros in sales_fact for "
                                "Jan 2023 - Mar 2026. Credits excluded from the mix base. "
                                "PRD is folded into stock for the 80/20 view.",
            "unmapped_codes": unmapped,
            "unmapped_warning": ("Codes outside SOR/PRD (stock) and VOR/RUSH/SVOR (rush) still carry euros. "
                                 "They keep their own band." if unmapped else None),
            "source": src("01_data/00_derived/sales_fact.parquet", "calendar and fiscal year",
                          f"sold_to_sap in {sold_to}", green=True),
        },
        "q1_fy2027": {
            "window": "2026-04-01 .. 2026-06-30",
            "total_eur": r2(qu.EUR_Amount.sum()),
            "coded_eur": r2(qc.EUR_Amount.sum()),
            "coded_share_of_eur_pct": coded_pct,
            "mix_pct_on_order_base": {k: float(v) for k, v in q1mix.items()},
            "rush_class_pct": q1_rush,
            "stock_pct": q1_stock,
            "verdict_colour": ("amber" if (coded_pct or 0) < 70
                               else "red" if q1_rush > 25 else "green"),
            "verdict_reason": (f"Coded share {coded_pct}% is below the 70% threshold — the mix "
                               "cannot be signed, render amber."
                               if (coded_pct or 0) < 70 else
                               f"Coded share {coded_pct}% is sufficient. Rush class {q1_rush}%."),
            "source": src("01_data/00_derived/q1fy2027_export_with_saty.csv", "Apr-Jun 2026",
                          f"Sold_to in {sold_to}  (NOT Payer_code)",
                          ("UMI 1797 and UTI 1799 share payer 1797 — always filter Sold_to."
                           if db in ("UMI", "UTI")
                           else "Always filter Sold_to, never payer_code."),
                          green=False),
        },
        "cadence": {
            "do_not_render": True,
            "why_removed": (
                "We do not have customer order-clock data. Weekday euros are ISZE billing, "
                "not when the distributor ordered. Removed from the meeting screen."
            ),
            "grain": "ISZE billing date (daily) — NOT the customer's order date",
            "cy": CY_LATEST,
            "distinct_billing_dates": int(d_last.billing_date.nunique()),
            "distinct_iso_weeks": int(d_last.billing_date.dt.isocalendar().week.nunique()),
            "by_weekday_eur": {DAYS[i]: r2(v) for i, v in wd.items()},
            "source": src("01_data/00_derived/sales_fact.parquet", "daily billing date",
                          f"sold_to_sap in {sold_to} AND year == {CY_LATEST}", green=True),
        },
        "other_coded": {
            "label": "Other coded (not stock, not rush)",
            "meaning": (
                "Billed order codes that are neither stock (SOR + PRD) nor rush (VOR / RUSH / SVOR). "
                "PRD is folded into stock on this screen. Remaining other codes keep their own band."
            ),
            "codes": unmapped,
            "by_year": other_by_year,
            "prd_folded_into_stock": True,
            "tooltip": {
                "formula": "Share of billed euros on codes outside SOR/PRD and VOR/RUSH/SVOR. Credits out. PRD is stock here.",
                "snapshot": f"Complete CY through {CY_LATEST} · sold-to {sold_to}",
                "not_included": "Not stock. Not rush. Not the 80/20 mix.",
            },
        },
        "meeting_read": {
            "title": "Rush versus stock — what we actually have",
            "replaces": "ISZE invoicing rhythm",
            "grain": f"CY{CY_LATEST} complete billed euros, this sold-to. PRD treated as stock.",
            "vor_vs_target": {
                "stock_pct": latest_cy_mix.get("stock_pct"),
                "rush_pct": latest_cy_mix.get("rush_class_pct"),
                "other_coded_pct": latest_cy_mix.get("other_coded_pct"),
                "prd_in_stock_pct": latest_cy_mix.get("prd_in_stock_pct"),
                "target_stock_pct": 80,
                "target_rush_pct": 20,
                "coded_share_of_eur_pct": cy_coded,
                "coded_colour": ("amber" if (coded_pct or 100) < 70
                                 else "red" if (latest_cy_mix.get("rush_class_pct") or 0) > 25
                                 else "green"),
                "cy": CY_LATEST,
                "fy": latest_fy_mix.get("fy"),
                "fy_stock_pct": latest_fy_mix.get("stock_pct"),
                "fy_rush_pct": latest_fy_mix.get("rush_class_pct"),
            },
            "by_pms_family": fam_rows[:14],
            "top_rush_pns": [
                {"pn": str(rw.pn), "description": rw.description,
                 "rush_eur": r2(rw.rush_eur), "qty": r2(rw.qty),
                 "pms_category": pms_map.get(str(rw.pn)),
                 "pms_label": pms_lab.get(str(rw.pn))}
                for _, rw in top_rush.iterrows()
            ],
            "q1_coded_share_pct": coded_pct,
            "q1_coded_colour": ("amber" if (coded_pct or 0) < 70 else "green"),
            "q1_rush_pct": q1_rush,
        },
    }

    # Working set + warranty overlap
    warr = pd.read_csv(d("warranty_raw_grain.csv"))
    wsub = warr[warr.db_name.astype(str).str.upper().str.contains(db, na=False)]
    if not len(wsub):
        wsub = warr[warr.db_code.astype(str).isin(
            dimrows.get("payer_code", pd.Series(dtype=str)).astype(str).tolist())]
    wpns = set(wsub.part_no.astype(str))

    ws = (book.groupby(["part_number", "description"])
          .agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"),
               lines=("net_sales_value", "size"))
          .reset_index().sort_values("eur", ascending=False).head(30))
    ws_rows = []
    for _, rw in ws.iterrows():
        pn = str(rw.part_number)
        ws_rows.append({
            "pn": pn, "description": rw.description,
            "eur": r2(rw.eur), "qty": r2(rw.qty), "invoice_lines": int(rw.lines),
            "share_of_cy_eur_pct": round(100 * rw.eur / book_tot, 2) if book_tot else None,
            "is_shell_lubricant": pn.startswith("5500"),
            "on_warranty_claim_lines": pn in wpns,
            "bvp_alternative_in_crossref": pn in gen_pns,
            "is_itself_a_bvp_pn": pn in bvp_pns,
            "lever": ("EXCLUDED FROM GPS — Shell lubricant" if pn.startswith("5500")
                      else "push Best Value — crossref alternative exists" if pn in gen_pns
                      else "already the value tier — this PN IS the BVP" if pn in bvp_pns
                      else "pending aftermarket evidence"),  # SPA rewritten in enrich() — needs IAM + no BVP
        })
    n_warr = sum(1 for r in ws_rows if r["on_warranty_claim_lines"])

    L["sections"]["working_set"] = {
        "basis": f"top 30 PN by euro, CY{CY_LATEST} complete, credit notes excluded",
        "cy_total_eur": r2(book_tot),
        "distinct_pns_in_cy": int(book.part_number.nunique()),
        "top30_share_of_cy_pct": round(float(ws.eur.sum() / book_tot * 100), 1) if book_tot else None,
        "rows": ws_rows,
        "counts": {
            "shell_lubricant_pns": sum(1 for r in ws_rows if r["is_shell_lubricant"]),
            "on_warranty_claim_lines": n_warr,
            "with_bvp_alternative_in_crossref": sum(1 for r in ws_rows if r["bvp_alternative_in_crossref"]),
            "is_itself_a_bvp_pn": sum(1 for r in ws_rows if r["is_itself_a_bvp_pn"]),
            "spa_candidates": sum(1 for r in ws_rows if r["lever"].startswith("SPA")),
        },
        "warranty_exclusion_warning": (
            f"{n_warr} of 30 top PNs also appear on this DB's warranty claim lines. "
            "Applying the binary ex-warranty PN exclusion would delete them and destroy the "
            "working set. Show the commercial and blended lenses side by side and label the "
            "limitation instead." if n_warr >= 10 else None),
        "bvp_lever_note": "Per ban 20 the label is 'no BVP in crossref', never 'no BVP in "
                          "catalog'. Crossref coverage is incomplete. SPA candidate does not "
                          "mean create a SPA.",
        "source": src("01_data/00_derived/sales_fact.parquet", "calendar year",
                      f"sold_to_sap in {sold_to} AND year == {CY_LATEST} AND saty != 'CR'",
                      "Credit notes are stored POSITIVE here — excluded, not subtracted.",
                      green=True),
    }

    # Best Value alternatives on PMS parts with low capture — retention lever, not a cut.
    PRIORITY_PMS = ["oil_filter", "fuel_filter", "air_filter",
                    "brake_pad", "brake_shoe", "brake_rotor", "blower_filter"]
    pms_cap = {c["pms_category"]: c for c in (pms_block.get("by_category") or [])}
    xref_pairs = xref.dropna(subset=["genuine_pn", "bvp_pn"]).copy()
    xref_pairs["genuine_pn"] = xref_pairs.genuine_pn.astype(str)
    xref_pairs["bvp_pn"] = xref_pairs.bvp_pn.astype(str)
    book_by_pn = book.groupby(book.part_number.astype(str)).agg(
        eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"),
        description=("description", "first")).reset_index()
    book_by_pn["pn"] = book_by_pn.part_number.astype(str)
    gen_in_book = book_by_pn.merge(xref_pairs, left_on="pn", right_on="genuine_pn", how="inner")
    bvp_alt_rows = []
    for _, rw in gen_in_book.iterrows():
        fam_raw = rw.get("pms_category")
        fam = "" if fam_raw is None or (isinstance(fam_raw, float) and pd.isna(fam_raw)) else str(fam_raw)
        if fam not in PRIORITY_PMS:
            continue
        cap = pms_cap.get(fam) or {}
        bvp_alt_rows.append({
            "genuine_pn": rw.genuine_pn,
            "bvp_pn": rw.bvp_pn,
            "description": rw.description,
            "family": fam or str(rw.get("product_family") or ""),
            "family_label": cap.get("label") or str(rw.get("category_label") or rw.get("product_family") or fam),
            "genuine_eur_cy": r2(rw.eur),
            "genuine_qty_cy": r2(rw.qty),
            "pms_capture_pct": cap.get("capture_pct"),
            "pms_gap_eur": cap.get("revenue_gap_eur"),
            "lever": "Offer the Best Value alternative — retention, not a cut",
        })
    # Prefer low capture, then euro. Deduplicate genuine_pn keeping first (highest euro after sort).
    bvp_alt_rows.sort(key=lambda x: (
        0 if x["family"] in PRIORITY_PMS[:3] else 1 if x["family"] in PRIORITY_PMS else 2,
        x["pms_capture_pct"] if x["pms_capture_pct"] is not None else 999,
        -(x["genuine_eur_cy"] or 0),
    ))
    seen_g = set()
    bvp_alt_dedup = []
    for r in bvp_alt_rows:
        if r["genuine_pn"] in seen_g:
            # extra BVP PNs for the same genuine — append to existing
            hit = next(x for x in bvp_alt_dedup if x["genuine_pn"] == r["genuine_pn"])
            if r["bvp_pn"] not in hit["bvp_pns"]:
                hit["bvp_pns"].append(r["bvp_pn"])
            continue
        seen_g.add(r["genuine_pn"])
        rec = dict(r)
        rec["bvp_pns"] = [r["bvp_pn"]]
        bvp_alt_dedup.append(rec)
    for rec in bvp_alt_dedup:
        rec.pop("bvp_pn", None)
    L["sections"]["bvp_alternatives"] = {
        "title": "Best Value alternatives on low-capture PMS",
        "role": "retention — never red, never in an erosion total",
        "priority_families": PRIORITY_PMS,
        "lead": (
            "The first lever on lost service is to offer the Best Value pair where one exists, "
            "especially oil / fuel / air filters, then brakes. This keeps the euro in the authorised channel."
        ),
        "n": len(bvp_alt_dedup),
        "n_filters": sum(1 for r in bvp_alt_dedup if r["family"] in PRIORITY_PMS[:3] + ["blower_filter"]),
        "n_brakes": sum(1 for r in bvp_alt_dedup if r["family"] in ("brake_pad", "brake_shoe", "brake_rotor")),
        "rows": bvp_alt_dedup[:40],
        "source": src("01_data/00_derived/genuine_bvp_crossref.csv + sales_fact.parquet",
                      f"CY{CY_LATEST}",
                      f"genuine PN billed to sold-to {sold_to} and paired in the crossref",
                      "Crossref coverage is incomplete — ‘no pair’ is not ‘no Best Value in catalogue’.",
                      green=True),
        "tooltip": {
            "formula": "Genuine PN on this sold-to’s complete-CY book that has a Best Value PN in the crossref, restricted to PMS filter and brake families first.",
            "snapshot": f"CY{CY_LATEST} · sold-to {sold_to}",
            "not_included": "Not an erosion euro. Not a price cut. Unpaired genuine PNs are not listed here.",
        },
    }

    # ---------------- Lane 3: IAM / aftermarket price pressure -------------------
    # REAL data, but narrow. eucon_price_gap.csv holds 44 PNs with actual competitor
    # prices sourced DE+NO, plus gp_at_risk_eur. Coverage of a DB's own book varies
    # from 25.6% (Norway) to 0.0% (UTI) — so the lane is quantified per DB, never
    # assumed. Rows without gp_at_risk_eur contribute nothing.
    #
    # KS / Mekonomen PN joins (this DB only) are attached in enrich().
    # Auto 365 has no OEM PN — family-level catalogue only. Never iam_israel_price_gap.
    #
    # BLACKLISTED: 01_data/00_derived/competitiveness_autodoc_risk.csv. All 298 rows
    # carry autodoc_min_eur <= 2.34 (median exactly 2.34) — that is the GBP2.00
    # "no results" placeholder converted to EUR and propagated as if it were a
    # competitor price. It implies ISZE engine assemblies face EUR 2.34 competition.
    # Never read it. See DATA_INTEGRITY.md.
    book_pn = book.groupby(book.part_number.astype(str)).net_sales_value.sum()
    top30_pns = set(ws.part_number.astype(str))
    iam_path = d("eucon_price_gap.csv")
    iam_lane = {"label": "Aftermarket price pressure", "available": False, "rows": [], "probes": {}}
    if os.path.exists(iam_path):
        iam = pd.read_csv(iam_path)
        iam["pn"] = iam.pn.astype(str)
        matched = iam[iam.pn.isin(book_pn.index)].copy()
        matched["db_rev_cy_eur"] = matched.pn.map(book_pn)
        cov_eur = float(matched.db_rev_cy_eur.sum())
        iam_lane = {
            "label": "Aftermarket price pressure",
            "available": bool(len(matched)),
            "value_eur": None,
            "meaning": "Aftermarket price pressure on parts we actually sell. This is the ONLY "
                       "lane that is real erosion — the euro leaves the authorised channel.",
            "grain": f"PN-level, CY{CY_LATEST} revenue weighting",
            "SIGN_CONVENTION": "delta_pct = (IAM published offer − projected ISZE retail) / projected ISZE retail. "
                               "POSITIVE means ISZE is CHEAPER at retail than the named IAM offer "
                               "(competitive, good). NEGATIVE means ISZE sits ABOVE that offer at retail "
                               "(exposed). Colour positive green, negative red.",
            "delta_formula": {
                "label": "Δ % vs projected ISZE retail",
                "formula": "(IAM published unit − projected ISZE retail) / projected ISZE retail",
                "positive_means": "ISZE is cheaper at retail than that named-site offer",
                "compared_to": (
                    "Projected ISZE retail = PR00 net × 1.40 × 1.275 = ×1.785 "
                    f"({CHANNEL_AS_OF}). "
                    "The named source on the row: Eucon PartsPool = Autodoc DE/NO online IAM (2026-03-29); "
                    "Eucon UK 2023 = IAM workshop GBP (vintage trade); "
                    "KS International = UK trade, ex-VAT; Mekonomen = Sweden retail "
                    "(flag suspect titles). IAM trade vs projected retail is still not perfect like-for-like."
                ),
                "tooltip": {
                    "formula": (
                        "(IAM published − projected ISZE retail) / projected ISZE retail. "
                        "Projected retail = PR00 net × 1.40 (distributor) × 1.275 (dealer) = ×1.785. "
                        f"Source {CHANNEL_AS_OF}. Positive = ISZE cheaper at retail."
                    ),
                    "snapshot": f"CY{CY_LATEST} billed book ∩ named aftermarket catalogues · {CHANNEL_AS_OF}",
                    "not_included": "Do not compare IAM retail to ISZE net-to-distributor. Probes are not added together.",
                },
            },
            "columns": {
                "isze_net_unit": {
                    "label": "ISZE net / unit",
                    "field": "isze_price_eur",
                    "tooltip": {
                        "formula": "ISZE net to this distributor, current list (IE40 PR00), per unit.",
                        "snapshot": f"Joined to this sold-to’s CY{CY_LATEST} book",
                        "not_included": "Not billed euros, not sales-to-dealer, not a dealer or retail price.",
                    },
                },
                "projected_isze_retail": {
                    "label": "Projected ISZE retail",
                    "field": "proj_retail_eur",
                    "tooltip": {
                        "formula": "PR00 net × 1.40 (distributor) × 1.275 (dealer) = ×1.785.",
                        "snapshot": CHANNEL_AS_OF,
                        "not_included": "Not observed SPA terms. Not a scraped retail price.",
                    },
                },
                "iam_published_unit": {
                    "label": "IAM published / unit",
                    "field": "competitor_avg_eur",
                    "tooltip": {
                        "formula": "Named-site published offer used for Δ % vs projected retail. See Source and trade/retail flag on the row.",
                        "snapshot": "PartsPool Autodoc DE/NO 2026-03-29 · KS scrape · Mekonomen scrape · Eucon UK workshop 2023",
                        "not_included": "Not a local-market survey unless the source is local. T1 listings do not set a cut.",
                    },
                },
                "billed_cy": {
                    "label": f"Billed CY{CY_LATEST} €",
                    "field": "db_revenue_cy_eur",
                    "tooltip": {
                        "formula": "ISZE net sales billed to this sold-to in the complete calendar year. Credits excluded.",
                        "snapshot": f"CY{CY_LATEST} complete · sold-to {sold_to}",
                        "not_included": "Not a unit price.",
                    },
                },
            },
            "pns_matched": int(len(matched)),
            "pns_in_source": int(len(iam)),
            "db_revenue_covered_eur": r2(cov_eur),
            "db_revenue_coverage_pct": round(100 * cov_eur / book_tot, 1) if book_tot else None,
            "pns_in_top30": int(len(top30_pns & set(matched.pn))),
            "isze_exposed_pns": int(matched.isze_exposed.sum()) if "isze_exposed" in matched else None,
            "contested_pns": int(matched.contested.sum()) if "contested" in matched else None,
            "gp_at_risk_eur_NETWORK_LEVEL_DO_NOT_ATTRIBUTE": (
                r2(matched.gp_at_risk_eur.sum()) if "gp_at_risk_eur" in matched else None),
            "db_revenue_on_exposed_pns_eur": r2(
                matched.loc[matched.Avg_Delta_pct < 0, "db_rev_cy_eur"].sum()
            ) if "Avg_Delta_pct" in matched else None,
            "worst_delta_pct": (round(100 * matched.Avg_Delta_pct.min(), 1)
                                if "Avg_Delta_pct" in matched and matched.Avg_Delta_pct.notna().any() else None),
            "revenue_weighted_delta_pct": (
                round(100 * float((matched.Avg_Delta_pct * matched.db_rev_cy_eur).sum()
                                  / matched.db_rev_cy_eur.sum()), 1)
                if "Avg_Delta_pct" in matched and matched.db_rev_cy_eur.sum() else None),
            "rows": [
                {"pn": rw.pn, "description": rw.description,
                 "isze_price_eur": r2(rw.ISZE_IE40_Price_EUR),
                 "proj_retail_eur": projected_retail(rw.ISZE_IE40_Price_EUR),
                 "competitor_avg_eur": r2(rw.Avg_Competitor_EUR),
                 "competitor_min_eur": r2(rw.Min_Competitor_EUR),
                 "delta_pct": (delta_vs_projected_retail(rw.Avg_Competitor_EUR, rw.ISZE_IE40_Price_EUR)[0]
                               if pd.notna(rw.Avg_Competitor_EUR) and pd.notna(rw.ISZE_IE40_Price_EUR) else None),
                 "delta_vs_isze_net_pct": round(100 * rw.Avg_Delta_pct, 1) if pd.notna(rw.Avg_Delta_pct) else None,
                 "competitor_count": int(rw.Competitor_Count) if pd.notna(rw.Competitor_Count) else None,
                 "brands": rw.Brands_Found, "countries": rw.Countries_Found,
                 "gp_at_risk_eur": r2(rw.gp_at_risk_eur),
                 "isze_exposed": bool(rw.isze_exposed) if pd.notna(rw.isze_exposed) else None,
                 "db_revenue_cy_eur": r2(rw.db_rev_cy_eur),
                 "in_working_set": rw.pn in top30_pns,
                 "competitor_url": None,
                 "probe": "eucon",
                 "probe_label": "Eucon (DE/NO)",
                 "iam_point_kind": "mix",
                 "iam_like_for_like_note": "IAM list/workshop mix vs projected retail — still not perfect like-for-like"}
                for _, rw in matched.sort_values("db_rev_cy_eur", ascending=False).iterrows()],
            "probes": {
                "eucon": {
                    "available": bool(len(matched)),
                    "label": "Eucon (DE/NO)",
                    "n": int(len(matched)),
                    "db_revenue_covered_eur": r2(cov_eur),
                    "db_revenue_coverage_pct": round(100 * cov_eur / book_tot, 1) if book_tot else None,
                    "do_not_sum_with_other_probes": True,
                }
            },
            "source": src("01_data/00_derived/eucon_price_gap.csv", "part number",
                          f"pn present in this DB's CY{CY_LATEST} book",
                          "Competitor prices sourced DE + NO Autodoc (PartsPool 2026-03-29). 44 PNs network-wide. "
                          "Coverage of a DB's own book is stated above — read it before quoting.",
                          green=False),
            "limitations": [
                "Eucon competitor sourcing is DE + NO Autodoc (PartsPool 29 Mar 2026). It is not a local-market survey for this DB, and it is not the 2023 UK workshop survey.",
                "44 PNs network-wide — this is a probe, not a catalogue-wide price position.",
                "gp_at_risk_eur is populated on 24 of 44 PNs AND is network-level per PN — "
                "it must never be summed and presented as this DB's exposure.",
                "The DB-scoped figure is db_revenue_on_exposed_pns_eur: revenue at stake where "
                "ISZE sits above the competitor average. It is revenue, not a margin loss, and "
                "it is not a booked loss either.",
            ],
            "blacklisted_source": {
                "file": "01_data/00_derived/competitiveness_autodoc_risk.csv",
                "reason": "All 298 rows have autodoc_min_eur <= 2.34 (median exactly 2.34) — the "
                          "GBP2.00 'no results' placeholder propagated as a competitor price. "
                          "Implies engine assemblies face EUR 2.34 competition. Do not read.",
            },
        }
        if not len(matched):
            iam_lane["reason"] = (f"None of the 44 Eucon gap PNs appear in {db}'s CY{CY_LATEST} "
                                  "book. Lane is genuinely empty for this DB — empty state.")

    # Three erosion lanes, never summed
    L["sections"]["three_lanes"] = {
        "gps_gap": {
            "label": "GPS gap — addressable uncaptured wallet",
            "value_eur": (L["sections"]["wallet_cy"].get("addressable_uncaptured_eur")
                          if L["sections"]["wallet_cy"].get("available", True) else None),
            "grain": f"CY{CY_LATEST}", "meaning": "Ceiling minus captured. NOT a booked loss.",
        },
        "pms_gap": {
            "label": "PMS gap — quotable service revenue gap",
            "value_eur": pms_block.get("quotable_gap_eur"),
            "grain": f"CY{CY_LATEST}",
            "meaning": "Expected service qty minus actual, priced, quotable categories only.",
        },
        "iam_gap": iam_lane,
        "hard_rule": "Three siblings on different bases and different grains. NEVER summed into "
                     "one erosion euro. No shared axis that implies addition.",
        "pricing_reference": {
            "label": "Projected ISZE retail",
            "formula": "PR00 net × 1.40 (distributor) × 1.275 (dealer) = ×1.785",
            "source": CHANNEL_AS_OF,
            "used_for": "Lost-sales / strategy euros and any 'how much more expensive' vs a named IAM. Not ISZE net-to-DB.",
            "tooltip": {
                "formula": "Projected ISZE retail = PR00 × 1.40 × 1.275 = ×1.785. Δ% = (IAM published − projected retail) / projected retail. Positive = ISZE cheaper at retail.",
                "snapshot": CHANNEL_AS_OF,
                "not_included": "Not observed SPA terms. Not ISZE net-to-distributor. Not a scraped shop price.",
            },
        },
    }

    enrich(L, db, reg, book_tot, ws_rows, iam_lane, book_pn=book_pn, top30_pns=top30_pns)

    attach_compare_and_drill(L, db)

    # ---------------- Reconciliation ---------------------------------------
    fy_sf = u[(u.billing_date >= f"{FY_LATEST-1}-04-01") & (u.billing_date <= f"{FY_LATEST}-03-31")]
    dim_fy = dimrows.fy2026_net_sales_eur.sum() if "fy2026_net_sales_eur" in dimrows else None
    L["reconciliation"] = {
        "three_that_must_not_match": {
            "gps_pure_sales_fy_latest_eur": r2(g.loc[FY_LATEST, "pure_sales_eur"]) if FY_LATEST in g.index else None,
            "wallet_captured_cy_latest_eur": L["sections"]["wallet_cy"].get("captured_total_eur"),
            "pms_revenue_cy_latest_eur": pms_block.get("revenue_eur"),
            "why": "Three baskets, two grains. GPS pure sales is FISCAL with lubricants and "
                   "freight stripped. Wallet captured is CALENDAR over the whole GPS-facing "
                   "book including warranty-ridden lines. PMS revenue is CALENDAR over 14 "
                   "service categories only. If they ever match, something is double-counted.",
        },
        "checks": [
            {"check": "sales_fact FY vs distributor_dimension fy2026_net_sales_eur",
             "a_eur": r2(fy_sf.net_sales_value.sum()), "b_eur": r2(dim_fy)},
            {"check": "whole-book BVP share vs wallet_waterfall bvp_share_of_captured_pct",
             "a_pct": round(100 * book_bvp / book_tot, 1) if book_tot else None,
             "b_pct": L["sections"]["wallet_cy"].get("bvp_share_of_captured_pct")},
            {"check": "V3.1 tab actual vs gps_pure_sales pure_sales_eur, FY latest",
             "a_eur": (v31fy.get(FY_LATEST) or {}).get("actual_eur"),
             "b_eur": r2(g.loc[FY_LATEST, "pure_sales_eur"]) if FY_LATEST in g.index else None},
            {"check": "BP FY27 json vs V3.1 Dashboard col C",
             "a_eur": bp["by_gps_code"].get(db), "b_eur": v31.get("bp_fy27_eur")},
        ],
    }
    for c in L["reconciliation"]["checks"]:
        a, b = c.get("a_eur", c.get("a_pct")), c.get("b_eur", c.get("b_pct"))
        if a is None or b is None:
            c["verdict"] = "N/A"
        else:
            c["verdict"] = "MATCH" if abs(a - b) <= max(1.0, abs(b) * 0.001) else f"DIFF {round(a-b,2)}"

    return L


def main():
    global LCV_RATE_OVERRIDE
    ap = argparse.ArgumentParser(description="Build the operating-dashboard numbers ledger.")
    ap.add_argument("--db", help="distributor_code, e.g. UMI / ITUK / BELGIUM")
    ap.add_argument("--all", action="store_true", help="every DB in the registry")
    ap.add_argument("--lcv-rate", type=float, default=None,
                    help="override the LCV / D-Max ISZE-net rate per unit")
    ap.add_argument("--list", action="store_true", help="list known DBs and exit")
    a = ap.parse_args()

    if a.list:
        for k, v in sorted(REGISTRY.items()):
            print(f'{k:10s} sold_to={str(v["sold_to"]):12s} seg={v["segment"]:5s} '
                  f'v31_tab={str(v["v31_tab"]):9s} {v["display"]}')
        return
    if a.lcv_rate:
        LCV_RATE_OVERRIDE = a.lcv_rate
    targets = sorted(REGISTRY) if a.all else ([a.db] if a.db else [])
    if not targets:
        ap.error("give --db <KEY>, or --all, or --list")

    for db in targets:
        L = json_safe(build(db))
        outdir = os.path.join(MEETINGS, f"{db}_Operating_Dashboard_2026")
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, "NUMBERS_LEDGER.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(L, fh, indent=2, ensure_ascii=False, default=str, allow_nan=False)
        if db in ("ITUK", "GERMANY", "PORTUGAL", "GREECE"):
            integ = write_integrity_md(L, outdir)
            print(f'{"":12s} integrity {integ}')
        gps = L["gps_fy_spine"]["rows"]
        latest = next((r for r in gps if r["fy"] == FY_LATEST), {})
        bad = [c for c in L["reconciliation"]["checks"] if c["verdict"].startswith("DIFF")]
        print(f'{db:10s} -> {out}')
        print(f'{"":12s} BP FY27 {L["business_plan"]["bp_fy27_eur"]} | '
              f'FY{FY_LATEST} actual {latest.get("actual_eur")} | '
              f'GPS {latest.get("gps_pct")}% | ex-warr {latest.get("gps_pct_ex_warranty")}% | '
              f'PMS {L["sections"]["pms"].get("capture_pct_total")}% | '
              f'recon-diffs {len(bad)}')


if __name__ == "__main__":
    main()
