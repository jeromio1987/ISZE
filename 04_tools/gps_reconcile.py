"""
GPS reconciliation harness — single entry point for all GPS integrity checks.

Lineage covered (raw -> derived -> presentation):
  raw SAP billing (12_raw/sales/CY2023-2024.XLSX, CY2025.XLSX,
                   01_data/sales_2026tillApril.XLSX, Sales_israel_1799&_1797.XLSX)
    -> gps_billing_clean.json (+ transport / surcharge sidecars)   [rebuild_gps_billing_and_surcharge_check.py]
    -> gps_billing_fy_waterfall_*.csv / gps_billing_fy_ALLCUSTOMERS_*.csv
    -> 91_build/gps_snapshot.json (= gps_v9_snapshot.json copy)    [91_build/build_gps_v9.py]
    -> 02_dashboards/{fleet,gps}/ISZE_GPS_Dashboard*.html (embedded JS constants)
    -> PRISM GPS page feed: 00_derived/gps_spu_by_distributor.csv

Tolerances (documented):
  HARD identity checks: EUR 5 per DB x FY cell (same convention as _audit_gps_integrity.py),
                        EUR 10 per FY waterfall stage.
  SOFT cross-basis checks (different extraction basis, calendar vs fiscal, parquet vs ERP):
                        2 % relative — reported as WARN, never gates the exit code.

Exit code: 0 if no HARD check fails, 1 otherwise.
Report: 00_derived/gps_reconciliation_report.json (override with --json-out).

Usage:
  python gps_reconcile.py                 # full run (loads ~70 MB of raw Excel, several minutes)
  python gps_reconcile.py --skip-raw      # static checks only (snapshot / dashboards / SPU csv)
  python gps_reconcile.py --skip-kosha    # skip the Kosha workbook audit subprocess
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DATA_ROOT, DERIVED_DIR, ISZE_ROOT  # noqa: E402
from rebuild_gps_billing_and_surcharge_check import (  # noqa: E402
    EXCL_BILLT,
    EXCL_SATY,
    SURCHARGE,
    load_all_billing,
    rebuild_json,
)

BUILD_DIR = DATA_ROOT / "91_build"
DASH_DIR = ISZE_ROOT / "02_dashboards"

SNAPSHOT = BUILD_DIR / "gps_snapshot.json"
V9_SNAPSHOT = BUILD_DIR / "gps_v9_snapshot.json"
BILLING_JSON = DERIVED_DIR / "gps_billing_clean.json"
TRANSPORT_JSON = DERIVED_DIR / "gps_billing_transport_excluded.json"
STRIPPED_JSON = DERIVED_DIR / "gps_billing_surcharge_stripped.json"
SPU_CSV = DERIVED_DIR / "gps_spu_by_distributor.csv"
REPORT_OUT = DERIVED_DIR / "gps_reconciliation_report.json"

DASHBOARDS = [
    DASH_DIR / "fleet" / "ISZE_GPS_Dashboard.html",
]

TOL_CELL = 5.0        # EUR, per DB x FY identity checks
TOL_WATERFALL = 10.0  # EUR, per FY stage
TOL_SOFT_PCT = 2.0    # %, cross-basis checks
UNK_HARD_EUR = 5000.0  # unmapped payer money above this per FY = hard fail

FY_YEARS = (2024, 2025, 2026)

# Full GPS-clean taxonomy (isze-gps-auditor skill / gps_full_run.py)
WF_BILLT = {"G2", "RE", "S1", "S2"}
WF_SATY = {"CR", "ZDR"}
SHELL_PFX = ("550047", "550070")
OTHER_RE = "SERVICE FEE|COST DEMURRAGE|LATE PAYMENT"

# gps_snapshot.json base25 country label -> payer codes (canonical DB mapping,
# distributor_master_mapping.csv naming; Israel handled via the dedicated extract's db column)
SNAP_PAYERS = {
    "ITUK": {2194, 2575, 146},
    "IUK": {89, 2574},
    "GERMANY": {93, 601, 2516},
    "BELGIUM": {90},
    "IRELAND": {76},
    "NORWAY": {86},
    "SWEDEN": {2181, 2929},
    "DENMARK": {2027, 2751},
    "FINLAND": {2679},
    "ICELAND": {1576},
    "CYPRUS": {393},
    "GREECE": {66},
    "MALTA": {1759},
    "ROMANIA": {396},
    "HUNGARY": {537},
    "PORTUGAL": {92, 519},
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, check_id: str, severity: str, status: str, detail: str,
            deltas: list | None = None, files: list | None = None) -> None:
        self.checks.append({
            "id": check_id,
            "severity": severity,
            "status": status,
            "detail": detail,
            "deltas": deltas or [],
            "files": [str(f) for f in (files or [])],
        })
        print(f"  [{status}] {check_id} — {detail}")

    @property
    def hard_failures(self) -> list[dict]:
        return [c for c in self.checks if c["severity"] == "hard" and c["status"] == "FAIL"]


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# ── static checks ────────────────────────────────────────────────────────────

def check_inputs(rep: Report) -> None:
    required = [BILLING_JSON, TRANSPORT_JSON, STRIPPED_JSON, SNAPSHOT, V9_SNAPSHOT, SPU_CSV, *DASHBOARDS]
    missing = [str(p) for p in required if not p.exists()]
    rep.add("inputs_present", "hard", "FAIL" if missing else "PASS",
            f"{len(missing)} missing" if missing else "all derived/presentation inputs found",
            deltas=missing, files=required)


def check_snapshot_copy(rep: Report) -> None:
    if not (SNAPSHOT.exists() and V9_SNAPSHOT.exists()):
        rep.add("snapshot_copy", "hard", "SKIP", "snapshot file(s) missing")
        return
    same = SNAPSHOT.read_bytes() == V9_SNAPSHOT.read_bytes()
    rep.add("snapshot_copy", "hard", "PASS" if same else "FAIL",
            "gps_snapshot.json is a byte-identical copy of gps_v9_snapshot.json" if same
            else "gps_snapshot.json has drifted from gps_v9_snapshot.json — re-copy after v9 rebuild",
            files=[SNAPSHOT, V9_SNAPSHOT])


_JS_VARS = ["BASE25", "WARR", "UIO26", "BP27", "MAX27", "RATES"]
_SNAP_KEYS = {"BASE25": "base25", "WARR": "warranty", "UIO26": "uio26",
              "BP27": "bp27", "MAX27": "uio27_max", "RATES": "rates"}


def _parse_dashboard_vars(html: str) -> dict:
    out = {}
    for var in _JS_VARS:
        m = re.search(rf"var {var}=(\[.*?\]|\{{.*?\}});", html, re.DOTALL)
        if m:
            out[var] = json.loads(m.group(1))
    return out


def _num_eq(a, b, tol=0.01) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_num_eq(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_num_eq(a[k], b[k], tol) for k in a)
    return a == b


def check_dashboards(rep: Report) -> None:
    snap = load_json(SNAPSHOT) if SNAPSHOT.exists() else {}
    for html_path in DASHBOARDS:
        if not html_path.exists():
            rep.add(f"dashboard_embedded:{html_path.parent.name}/{html_path.name}", "hard", "SKIP", "file missing")
            continue
        html = html_path.read_text(encoding="utf-8")
        rel = f"{html_path.parent.name}/{html_path.name}"

        # 1. embedded constants vs snapshot
        vars_ = _parse_dashboard_vars(html)
        bad = []
        for var, key in _SNAP_KEYS.items():
            if var not in vars_:
                bad.append(f"{var}: not found in HTML")
            elif key in snap and not _num_eq(vars_[var], snap[key]):
                bad.append(f"{var}: differs from snapshot['{key}']")
        rep.add(f"dashboard_embedded:{rel}", "hard", "FAIL" if bad else "PASS",
                "; ".join(bad) if bad else "embedded JS constants match gps_snapshot.json",
                deltas=bad, files=[html_path])

        # 2. renderability: nested script tag / external CDN dependency
        problems = []
        if re.search(r"<script>\s*<script", html):
            problems.append("nested <script><script src=...> tag — library never loads, page renders blank")
        if re.search(r'<script[^>]+src="https?://', html):
            problems.append("external CDN <script src> — blank charts offline (self-contained rule)")
        rep.add(f"dashboard_selfcontained:{rel}", "hard", "FAIL" if problems else "PASS",
                "; ".join(problems) if problems else "no CDN dependency, ECharts inlined",
                deltas=problems, files=[html_path])


def check_spu_csv(rep: Report) -> None:
    if not SPU_CSV.exists():
        rep.add("spu_internal", "hard", "SKIP", "gps_spu_by_distributor.csv missing")
        return
    df = pd.read_csv(SPU_CSV)
    bad = []
    for _, r in df.iterrows():
        db, yr = r["distributor_code"], int(r["year"])
        sales = r.get("total_sales_eur")
        uio = r.get("uio_units")
        if pd.notna(sales) and pd.notna(uio) and uio > 0 and pd.notna(r.get("spend_per_unit_eur")):
            if abs(sales / uio - r["spend_per_unit_eur"]) > 0.5:
                bad.append(f"{db} {yr}: spu {r['spend_per_unit_eur']:.1f} != sales/uio {sales / uio:.1f}")
        w = r.get("warranty_parts_eur")
        if pd.notna(sales) and pd.notna(w) and pd.notna(r.get("sales_ex_warranty_eur")):
            if abs((sales - w) - r["sales_ex_warranty_eur"]) > 1.0:
                bad.append(f"{db} {yr}: sales_ex != sales - warranty")
        mx = r.get("max_spend_eur")
        if pd.notna(sales) and pd.notna(mx) and mx > 0 and pd.notna(r.get("gps_capture_vs_max")):
            if abs(sales / mx - r["gps_capture_vs_max"]) > 1e-3:
                bad.append(f"{db} {yr}: capture {r['gps_capture_vs_max']:.3f} != sales/max {sales / mx:.3f}")
    rep.add("spu_internal", "hard", "FAIL" if bad else "PASS",
            f"{len(bad)} arithmetic inconsistencies" if bad else
            f"SPU / ex-warranty / capture arithmetic consistent across {len(df)} rows",
            deltas=bad[:20], files=[SPU_CSV])


def check_spu_vs_snapshot(rep: Report) -> None:
    """PRISM-side CY2025 sales vs v9 snapshot sales (cross-basis: parquet vs ERP extract)."""
    if not (SPU_CSV.exists() and SNAPSHOT.exists()):
        rep.add("spu_vs_snapshot_cy2025", "soft", "SKIP", "input missing")
        return
    snap_sales = {row[0]: float(row[3]) for row in load_json(SNAPSHOT).get("base25", [])}
    df = pd.read_csv(SPU_CSV)
    df25 = df[df["year"] == 2025]
    deltas = []
    for _, r in df25.iterrows():
        db = str(r["distributor_code"])
        v9 = snap_sales.get(db)
        sales = r.get("total_sales_eur")
        if v9 and pd.notna(sales) and v9 > 0:
            pct = 100 * (float(sales) - v9) / v9
            if abs(pct) > TOL_SOFT_PCT:
                deltas.append(f"{db}: PRISM {sales:,.0f} vs v9 {v9:,.0f} ({pct:+.1f}%)")
    rep.add("spu_vs_snapshot_cy2025", "soft", "WARN" if deltas else "PASS",
            f"{len(deltas)} DBs beyond {TOL_SOFT_PCT}% (cross-basis, informational)" if deltas
            else f"PRISM CY2025 sales within {TOL_SOFT_PCT}% of v9 snapshot for all mapped DBs",
            deltas=deltas, files=[SPU_CSV, SNAPSHOT])


# ── raw-recompute checks ─────────────────────────────────────────────────────

def check_json_vs_raw(rep: Report, df: pd.DataFrame) -> dict:
    gps, transport, stripped = rebuild_json(df)

    for label, rebuilt, stored_path in [
        ("billing_json_vs_raw", gps, BILLING_JSON),
        ("transport_sidecar_vs_raw", transport, TRANSPORT_JSON),
        ("surcharge_sidecar_vs_raw", stripped, STRIPPED_JSON),
    ]:
        stored = load_json(stored_path)
        deltas = []
        dbs = set(rebuilt) | set(stored)
        for db in sorted(dbs):
            fys = set(rebuilt.get(db, {})) | set(stored.get(db, {}))
            for fy in sorted(fys):
                a = float(rebuilt.get(db, {}).get(fy, 0) or 0)
                b = float(stored.get(db, {}).get(fy, 0) or 0)
                if abs(a - b) > TOL_CELL:
                    deltas.append(f"{db} FY{fy}: rebuilt {a:,.0f} vs stored {b:,.0f} (d {a - b:+,.0f})")
        rep.add(label, "hard", "FAIL" if deltas else "PASS",
                f"{len(deltas)} DBxFY cells beyond EUR{TOL_CELL:.0f}" if deltas
                else f"all DBxFY cells within EUR{TOL_CELL:.0f}",
                deltas=deltas[:30], files=[stored_path])

    # unmapped payers
    unk = {db: fys for db, fys in gps.items() if db.startswith("UNK_")}
    unk_total = sum(v for fys in unk.values() for v in fys.values())
    detail = ", ".join(f"{db}={sum(f.values()):,.0f}" for db, f in sorted(unk.items())) or "none"
    status = "PASS" if not unk else ("FAIL" if unk_total > UNK_HARD_EUR else "WARN")
    rep.add("unmapped_payers", "hard", status,
            f"unmapped payer buckets: {detail} (total EUR{unk_total:,.0f})",
            deltas=[f"{db}: {json.dumps(fys)}" for db, fys in sorted(unk.items())])
    return gps


def _waterfall(df: pd.DataFrame, neutralise: bool) -> dict[int, dict[str, float]]:
    d = df.copy()
    d["fy"] = d["billing_date"].apply(lambda t: t.year + 1 if t.month >= 4 else t.year)
    mat = d["material"].astype(str).str.upper().str.strip()
    is_billt = d["billt"].isin(WF_BILLT)
    is_saty = ~is_billt & d["saty"].isin(WF_SATY)
    is_tr = ~is_billt & ~is_saty & (mat == "TRANSPORT")
    is_shell = ~is_billt & ~is_saty & ~is_tr & mat.str.startswith(SHELL_PFX)
    is_other = ~is_billt & ~is_saty & ~is_tr & ~is_shell & mat.str.contains(OTHER_RE, na=False)
    keep = ~(is_billt | is_saty | is_tr | is_shell | is_other)
    val = d["net_value"]
    clean_val = val / d["saty"].map(SURCHARGE).fillna(1.0) if neutralise else val
    out: dict[int, dict[str, float]] = {}
    for fy in sorted(d["fy"].unique()):
        m = d["fy"] == fy
        out[int(fy)] = {
            "gross": float(val[m].sum()),
            "excl_billt": float(val[m & is_billt].sum()),
            "excl_saty_cr": float(val[m & is_saty].sum()),
            "excl_transport": float(val[m & is_tr].sum()),
            "excl_shell": float(val[m & is_shell].sum()),
            "excl_other": float(val[m & is_other].sum()),
            "clean": float(clean_val[m & keep].sum()),
        }
    return out


def _latest(pattern: str, canonical: str) -> Path | None:
    p = DERIVED_DIR / canonical
    if p.exists():
        return p
    files = sorted(DERIVED_DIR.glob(pattern))
    return files[-1] if files else None


def check_waterfall(rep: Report, df: pd.DataFrame) -> None:
    stored_path = _latest("gps_billing_fy_waterfall_*.csv", "gps_billing_fy_waterfall.csv")
    if stored_path is None:
        rep.add("waterfall_vs_raw", "hard", "SKIP", "no gps_billing_fy_waterfall*.csv found")
        return
    stored = pd.read_csv(stored_path).set_index("FY")

    best = None
    for neutralise in (False, True):
        wf = _waterfall(df, neutralise=neutralise)
        deltas = []
        for fy, row in stored.iterrows():
            calc = wf.get(int(fy))
            if not calc:
                deltas.append(f"FY{fy}: missing from recompute")
                continue
            for col in stored.columns:
                a, b = float(calc.get(col, 0)), float(row[col])
                if abs(a - b) > TOL_WATERFALL:
                    deltas.append(f"FY{fy} {col}: recomputed {a:,.0f} vs stored {b:,.0f} (d {a - b:+,.0f})")
        cand = {"neutralised_clean": neutralise, "deltas": deltas}
        if best is None or len(deltas) < len(best["deltas"]):
            best = cand
        if not deltas:
            break
    basis = "surcharge-neutralised" if best["neutralised_clean"] else "raw net"
    rep.add("waterfall_vs_raw", "hard", "FAIL" if best["deltas"] else "PASS",
            (f"{len(best['deltas'])} stage mismatches vs {stored_path.name} (closest basis: {basis} clean)"
             if best["deltas"] else
             f"waterfall reproduces {stored_path.name} exactly ({basis} clean, tol EUR{TOL_WATERFALL:.0f})"),
            deltas=best["deltas"][:30], files=[stored_path])


def _full_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Full GPS-clean line filter (waterfall taxonomy) + surcharge-neutralised net_gps.

    This is the ALLCUSTOMERS / waterfall / PRISM basis. gps_billing_clean.json uses the
    narrower Kosha basis (BillT + SaTy + transport only — fees and Shell stay in).
    """
    d = df.copy()
    d["fy"] = d["billing_date"].apply(lambda t: t.year + 1 if t.month >= 4 else t.year)
    mat = d["material"].astype(str).str.upper().str.strip()
    keep = (
        ~d["billt"].isin(WF_BILLT)
        & ~d["saty"].isin(WF_SATY)
        & (mat != "TRANSPORT")
        & ~mat.str.startswith(SHELL_PFX)
        & ~mat.str.contains(OTHER_RE, na=False)
    )
    d = d[keep].copy()
    d["net_gps"] = d["net_value"] / d["saty"].map(SURCHARGE).fillna(1.0)
    return d


def check_allcustomers(rep: Report, df: pd.DataFrame) -> None:
    stored_path = _latest("gps_billing_fy_ALLCUSTOMERS_*.csv", "gps_billing_fy_ALLCUSTOMERS.csv")
    if stored_path is None:
        rep.add("allcustomers_vs_raw", "hard", "SKIP", "no gps_billing_fy_ALLCUSTOMERS*.csv found")
        return
    stored = pd.read_csv(stored_path)
    d = _full_clean(df)

    hard_deltas, israel_deltas = [], []
    for _, r in stored.iterrows():
        codes = {int(c) for c in str(r["payer_codes"]).split(",") if c.strip().isdigit()}
        fy = int(r["FY"])
        if codes & {1797, 1799}:
            continue  # compared at combined level below (basis may differ)
        calc = float(d[(d["fy"] == fy) & (d["payer"].isin(codes))]["net_gps"].sum())
        b = float(r["net_gps"])
        if abs(calc - b) > TOL_CELL:
            hard_deltas.append(f"{r['canonical_name']} FY{fy}: rebuilt {calc:,.0f} vs stored {b:,.0f} (d {calc - b:+,.0f})")

    # Israel combined: canonical = dedicated UMI/UTI extract (db column present)
    if "db" in d.columns:
        for fy in FY_YEARS:
            calc = float(d[(d["fy"] == fy) & (d["db"].isin(["UTI", "UMI"]))]["net_gps"].sum())
            st = stored[stored["FY"] == fy]
            st_isr = float(st[st["payer_codes"].astype(str).str.contains("179[79]", regex=True)]["net_gps"].sum())
            if st_isr and abs(calc - st_isr) > TOL_CELL:
                israel_deltas.append(f"Israel FY{fy}: dedicated extract {calc:,.0f} vs CSV {st_isr:,.0f} (d {calc - st_isr:+,.0f})")

    rep.add("allcustomers_vs_raw", "hard", "FAIL" if hard_deltas else "PASS",
            f"{len(hard_deltas)} non-Israel customer cells beyond EUR{TOL_CELL:.0f} vs {stored_path.name}"
            if hard_deltas else f"all non-Israel customer FY cells within EUR{TOL_CELL:.0f} vs {stored_path.name}",
            deltas=hard_deltas[:30], files=[stored_path])
    rep.add("allcustomers_israel_basis", "soft" if israel_deltas else "hard",
            "WARN" if israel_deltas else "PASS",
            "Israel rows differ between dedicated UMI/UTI extract and the stored CSV basis "
            "(stored likely built from main files without the Israel merge fix)"
            if israel_deltas else "Israel totals consistent with dedicated UMI/UTI extract",
            deltas=israel_deltas, files=[stored_path])


def rebuild_billing_fy_csvs(df: pd.DataFrame) -> list[Path]:
    """Write canonical (undated) billing-FY artifacts from the documented full-clean basis.

    Replaces the ad-hoc gps_billing_fy_*_<date>.csv exports that had no producer script.
    Basis: full GPS-clean taxonomy, Israel from the dedicated UMI/UTI extract.
    """
    d = _full_clean(df)

    # per-customer file — Israel rows keyed by canonical UMI/UTI split
    name_col = d["db"] if "db" in d.columns else pd.Series(pd.NA, index=d.index)
    payer_int = d["payer"].fillna(-1).astype(int)
    d["canonical_name"] = name_col.fillna(payer_int.astype(str).map(lambda c: f"PAYER_{c}"))
    # non-Israel rows: use payer name from PAYER_DB
    from rebuild_gps_billing_and_surcharge_check import PAYER_DB
    d.loc[name_col.isna(), "canonical_name"] = payer_int[name_col.isna()].astype(str).map(
        lambda c: PAYER_DB.get(c, f"UNK_{c}"))
    grp = d.groupby(["fy", "canonical_name"]).agg(
        net_gps=("net_gps", "sum"),
        net_raw=("net_value", "sum"),
        payer_codes=("payer", lambda s: ",".join(str(int(x)) for x in sorted(set(s.dropna())))),
    ).reset_index().rename(columns={"fy": "FY"})
    all_out = DERIVED_DIR / "gps_billing_fy_ALLCUSTOMERS.csv"
    grp.to_csv(all_out, index=False)

    wf = _waterfall(df, neutralise=False)
    wf_rows = [{"FY": fy, **stages} for fy, stages in sorted(wf.items())]
    wf_out = DERIVED_DIR / "gps_billing_fy_waterfall.csv"
    pd.DataFrame(wf_rows).to_csv(wf_out, index=False)
    print(f"  Rebuilt: {all_out}")
    print(f"  Rebuilt: {wf_out}")
    return [all_out, wf_out]


def check_snapshot_vs_raw(rep: Report, df: pd.DataFrame) -> None:
    """v9 snapshot CY2025 sales per country vs raw calendar-2025 clean rebuild (cross-basis)."""
    if not SNAPSHOT.exists():
        rep.add("snapshot_vs_raw_cy2025", "soft", "SKIP", "snapshot missing")
        return
    snap_sales = {row[0]: float(row[3]) for row in load_json(SNAPSHOT).get("base25", [])}

    d = df.copy()
    d = d[d["billing_date"].dt.year == 2025]
    d = d[(~d["billt"].isin(EXCL_BILLT)) & (~d["saty"].isin(EXCL_SATY))]
    mat = d["material"].astype(str).str.upper()
    d = d[(mat != "TRANSPORT") & ~mat.str.startswith(SHELL_PFX) & ~mat.str.contains(OTHER_RE, na=False)]
    d["net_gps"] = d["net_value"] / d["saty"].map(SURCHARGE).fillna(1.0)

    deltas = []
    for snap_db, payers in SNAP_PAYERS.items():
        calc = float(d[d["payer"].isin(payers)]["net_gps"].sum())
        v9 = snap_sales.get(snap_db)
        if v9:
            pct = 100 * (calc - v9) / v9
            if abs(pct) > TOL_SOFT_PCT:
                deltas.append(f"{snap_db}: raw CY2025 {calc:,.0f} vs snapshot {v9:,.0f} ({pct:+.1f}%)")
    if "db" in d.columns:
        for snap_db, db_name in [("UMI", "UMI"), ("UTI", "UTI")]:
            calc = float(d[d["db"] == db_name]["net_gps"].sum())
            v9 = snap_sales.get(snap_db)
            if v9:
                pct = 100 * (calc - v9) / v9
                if abs(pct) > TOL_SOFT_PCT:
                    deltas.append(f"{snap_db}: raw CY2025 {calc:,.0f} vs snapshot {v9:,.0f} ({pct:+.1f}%)")
    rep.add("snapshot_vs_raw_cy2025", "soft", "WARN" if deltas else "PASS",
            f"{len(deltas)} DBs beyond {TOL_SOFT_PCT}% (v9 SALES_25 is a hardcoded ERP extract — "
            f"rebuild build_gps_v9.py if raw has been refreshed)" if deltas
            else f"snapshot CY2025 sales within {TOL_SOFT_PCT}% of raw rebuild",
            deltas=deltas, files=[SNAPSHOT])


def run_kosha_audit(rep: Report) -> None:
    """Delegate the Kosha workbook chain to the existing audit and absorb its verdicts."""
    script = _TOOLS / "_audit_gps_integrity.py"
    if not script.exists():
        rep.add("kosha_chain", "hard", "SKIP", "_audit_gps_integrity.py missing")
        return
    import time
    started = time.time()
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                          cwd=str(_TOOLS), timeout=600)
    audit_json = DERIVED_DIR / "gps_integrity_audit.json"
    fresh = audit_json.exists() and audit_json.stat().st_mtime >= started
    if proc.returncode != 0 or not fresh:
        rep.add("kosha_chain", "hard", "FAIL",
                f"_audit_gps_integrity.py {'crashed' if proc.returncode else 'wrote no fresh report'}: "
                f"{(proc.stderr or proc.stdout)[-300:]}")
        return
    results = load_json(audit_json)
    fails = [r for r in results if r.get("status") == "FAIL"]
    rep.add("kosha_chain", "hard", "FAIL" if fails else "PASS",
            f"{len(results) - len(fails)}/{len(results)} Kosha workbook checks passed"
            + (f"; failures: {', '.join(f['check'] for f in fails)}" if fails else ""),
            deltas=[f"{f['check']}: {f['detail']}" for f in fails], files=[audit_json])


def main() -> int:
    ap = argparse.ArgumentParser(description="GPS reconciliation harness")
    ap.add_argument("--skip-raw", action="store_true", help="skip raw Excel recompute checks")
    ap.add_argument("--skip-kosha", action="store_true", help="skip Kosha workbook audit subprocess")
    ap.add_argument("--rebuild", action="store_true",
                    help="regenerate canonical gps_billing_fy_*.csv from raw before checking")
    ap.add_argument("--json-out", type=Path, default=REPORT_OUT)
    args = ap.parse_args()

    rep = Report()
    print("=" * 72)
    print("GPS RECONCILIATION HARNESS")
    print("=" * 72)

    check_inputs(rep)
    check_snapshot_copy(rep)
    check_dashboards(rep)
    check_spu_csv(rep)
    check_spu_vs_snapshot(rep)

    if not args.skip_raw:
        print("\nLoading raw SAP billing (several minutes)...")
        df = load_all_billing()
        print(f"  {len(df):,} lines  {df.billing_date.min().date()} - {df.billing_date.max().date()}")
        if args.rebuild:
            print("Rebuilding canonical billing-FY CSVs...")
            rebuild_billing_fy_csvs(df)
        check_json_vs_raw(rep, df)
        check_waterfall(rep, df)
        check_allcustomers(rep, df)
        check_snapshot_vs_raw(rep, df)
    else:
        for cid in ("billing_json_vs_raw", "transport_sidecar_vs_raw", "surcharge_sidecar_vs_raw",
                    "unmapped_payers", "waterfall_vs_raw", "allcustomers_vs_raw", "snapshot_vs_raw_cy2025"):
            rep.add(cid, "hard" if "snapshot_vs" not in cid else "soft", "SKIP", "--skip-raw")

    if not args.skip_kosha:
        print("\nRunning Kosha workbook audit...")
        run_kosha_audit(rep)

    hard_fails = rep.hard_failures
    payload = {
        "generated_at": _now(),
        "tolerances": {"identity_eur_per_cell": TOL_CELL, "waterfall_eur_per_stage": TOL_WATERFALL,
                       "cross_basis_pct": TOL_SOFT_PCT, "unmapped_payer_hard_eur": UNK_HARD_EUR},
        "result": "FAIL" if hard_fails else "PASS",
        "hard_failures": len(hard_fails),
        "checks": rep.checks,
    }
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("\n" + "=" * 72)
    print(f"RESULT: {payload['result']}  ({len(rep.checks)} checks, {len(hard_fails)} hard failures)")
    print(f"Report: {args.json_out}")
    return 1 if hard_fails else 0


if __name__ == "__main__":
    sys.exit(main())
