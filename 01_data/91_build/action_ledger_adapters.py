"""P8 Action Ledger — nine source adapters (Mode B, deterministic).

Each adapter returns a DataFrame in the opportunity schema (§4.1) or raises.
Euro figures are carried verbatim from the named source column — never recomputed.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
INTERACTIONS = ISZE / "01_data" / "17_interactions"
SALES_FACT_PQ = DERIVED / "sales_fact.parquet"


def _billing_horizon_from_sales_fact() -> date:
    """Max sales_fact.billing_date — never invent a horizon ahead of SAP extract."""
    if not SALES_FACT_PQ.exists():
        raise FileNotFoundError(f"sales_fact missing: {SALES_FACT_PQ}")
    s = pd.read_parquet(SALES_FACT_PQ, columns=["billing_date"])["billing_date"]
    mx = pd.to_datetime(s, errors="coerce").max()
    if pd.isna(mx):
        raise ValueError("sales_fact.billing_date has no usable max")
    return mx.date()


BILLING_HORIZON = _billing_horizon_from_sales_fact()

OPPORTUNITY_COLS = [
    "opportunity_id",
    "signal_type",
    "db_code",
    "entity_key",
    "entity_grain",
    "eur_at_stake",
    "eur_basis",
    "source_file",
    "source_column",
    "source_as_of",
    "raised_on",
    "last_seen_on",
    "recommended_action",
    "also_seen_in",
    "evidence_ref",
    "adapter_name",
    "horizon_date",
    "count_basis_n",
]

log = logging.getLogger("action_ledger.adapters")


def _sha1_id(signal_type: str, db_code: str | None, entity_grain: str, entity_key: str) -> str:
    raw = f"{signal_type}|{db_code or ''}|{entity_grain}|{entity_key}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _file_as_of(path: Path, preferred: date | None = None) -> date:
    if preferred is not None:
        return preferred
    mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
    return mtime


def _parse_date(val: Any) -> date | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "nat"):
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y%m%d"):
        try:
            return datetime.strptime(s[:10] if len(s) >= 10 and fmt != "%Y-%m" else s[:7] if fmt == "%Y-%m" else s, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None


def _require_cols(df: pd.DataFrame, required: list[str], source: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{source}: schema change — missing columns {missing}; have {list(df.columns)}")


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=OPPORTUNITY_COLS)


def _finish(
    rows: list[dict[str, Any]],
    *,
    adapter_name: str,
    count_in: int,
    source_file: str,
) -> pd.DataFrame:
    count_out = len(rows)
    log.info("adapter=%s source=%s count_in=%s count_out=%s", adapter_name, source_file, count_in, count_out)
    if count_out == 0 and count_in > 0:
        log.warning("adapter=%s produced 0 rows from %s input rows", adapter_name, count_in)
    if not rows:
        df = _empty_frame()
        df.attrs["count_in"] = count_in
        df.attrs["count_out"] = 0
        df.attrs["adapter_name"] = adapter_name
        df.attrs["source_file"] = source_file
        return df
    df = pd.DataFrame(rows)
    for c in OPPORTUNITY_COLS:
        if c not in df.columns:
            df[c] = None
    df = df[OPPORTUNITY_COLS]
    df.attrs["count_in"] = count_in
    df.attrs["count_out"] = count_out
    df.attrs["adapter_name"] = adapter_name
    df.attrs["source_file"] = source_file
    return df


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------


def adapt_dealer_leakage_ituk(path: Path | None = None) -> pd.DataFrame:
    """#1 DEALER × CATEGORY · gap_eur · LEAKAGE (ITUK dealers)."""
    path = path or (DERIVED / "dealer_leakage_ituk.csv")
    name = "dealer_leakage_ituk"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["dealer_name", "category", "gap_eur"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        dealer = str(r["dealer_name"]).strip()
        cat = str(r["category"]).strip()
        if not dealer or not cat or dealer.lower() == "nan":
            continue
        entity_key = f"{dealer}|{cat}"
        eur = r["gap_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        db = "ITUK"
        oid = _sha1_id("LEAKAGE", db, "DEALER", entity_key)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "LEAKAGE",
                "db_code": db,
                "entity_key": entity_key,
                "entity_grain": "DEALER",
                "eur_at_stake": eur_f,
                "eur_basis": "CY2025",
                "source_file": path.name,
                "source_column": "gap_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": None,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|dealer={dealer}|category={cat}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_revision_exception_queue(path: Path | None = None) -> pd.DataFrame:
    """#2 DB × PN · pr00_eur · PRICE_REVISION."""
    path = path or (DERIVED / "revision_exception_queue.csv")
    name = "revision_exception_queue"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["distributor_code", "part_number", "pr00_eur"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["distributor_code"]).strip().upper()
        pn = str(r["part_number"]).strip()
        if not db or not pn or db.lower() == "nan":
            continue
        eur = r["pr00_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        action = r.get("recommended_action")
        action_s = str(action).strip() if pd.notna(action) else None
        oid = _sha1_id("PRICE_REVISION", db, "PN", pn)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "PRICE_REVISION",
                "db_code": db,
                "entity_key": pn,
                "entity_grain": "PN",
                "eur_at_stake": eur_f,
                "eur_basis": "ANNUALISED_SOURCE",
                "source_file": path.name,
                "source_column": "pr00_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": action_s,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}|pn={pn}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_replenishment_exceptions(path: Path | None = None) -> pd.DataFrame:
    """#3 DB × PN · bill_eur · REPLENISHMENT."""
    path = path or (DERIVED / "replenishment_exceptions_cy2025.csv")
    name = "replenishment_exceptions_cy2025"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["distributor_code", "part_number", "bill_eur"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["distributor_code"]).strip().upper()
        pn = str(r["part_number"]).strip()
        if not db or not pn:
            continue
        eur = r["bill_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        oid = _sha1_id("REPLENISHMENT", db, "PN", pn)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "REPLENISHMENT",
                "db_code": db,
                "entity_key": pn,
                "entity_grain": "PN",
                "eur_at_stake": eur_f,
                "eur_basis": "CY2025",
                "source_file": path.name,
                "source_column": "bill_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": None,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}|pn={pn}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_early_warning(path: Path | None = None) -> pd.DataFrame:
    """#4 DB · eur_exposed · EARLY_WARNING."""
    path = path or (DERIVED / "early_warning.csv")
    name = "early_warning"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["distributor_code", "eur_exposed"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["distributor_code"]).strip().upper()
        if not db or db.lower() == "nan":
            continue
        eur = r["eur_exposed"]
        eur_f = float(eur) if pd.notna(eur) else None
        why = r.get("why_this_cycle")
        action_s = str(why).strip()[:500] if pd.notna(why) else None
        n_sig = r.get("n_signals")
        n_f = int(n_sig) if pd.notna(n_sig) else None
        oid = _sha1_id("EARLY_WARNING", db, "DB", db)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "EARLY_WARNING",
                "db_code": db,
                "entity_key": db,
                "entity_grain": "DB",
                "eur_at_stake": eur_f,
                "eur_basis": "CY2025",
                "source_file": path.name,
                "source_column": "eur_exposed",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": action_s,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": n_f,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_defection_alerts(path: Path | None = None) -> pd.DataFrame:
    """#5 DB × CATEGORY · trailing_12m_rev_eur · DEFECTION."""
    path = path or (DERIVED / "defection_alerts.csv")
    name = "defection_alerts"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["distributor_code", "pms_category", "trailing_12m_rev_eur"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["distributor_code"]).strip().upper()
        cat = str(r["pms_category"]).strip()
        if not db or not cat:
            continue
        entity_key = f"{db}|{cat}"
        eur = r["trailing_12m_rev_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        hz = _parse_date(r.get("data_horizon")) or BILLING_HORIZON
        oid = _sha1_id("DEFECTION", db, "CATEGORY", entity_key)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "DEFECTION",
                "db_code": db,
                "entity_key": entity_key,
                "entity_grain": "CATEGORY",
                "eur_at_stake": eur_f,
                "eur_basis": "TRAILING_12M",
                "source_file": path.name,
                "source_column": "trailing_12m_rev_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": None,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}|cat={cat}",
                "adapter_name": name,
                "horizon_date": hz,
                "count_basis_n": int(r["active_months"]) if pd.notna(r.get("active_months")) else None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_no_pr00_gap(path: Path | None = None) -> pd.DataFrame:
    """#6 PN · cy2025_eur · CATALOGUE_GAP."""
    path = path or (DERIVED / "no_pr00_gap_cy2025_ranked.csv")
    name = "no_pr00_gap_cy2025_ranked"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["part_number", "cy2025_eur"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        pn = str(r["part_number"]).strip()
        if not pn:
            continue
        eur = r["cy2025_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        flag = r.get("flag")
        action_s = str(flag).strip() if pd.notna(flag) else None
        oid = _sha1_id("CATALOGUE_GAP", None, "PN", pn)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "CATALOGUE_GAP",
                "db_code": None,
                "entity_key": pn,
                "entity_grain": "PN",
                "eur_at_stake": eur_f,
                "eur_basis": "CY2025",
                "source_file": path.name,
                "source_column": "cy2025_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": action_s,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|pn={pn}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": int(r["n_lines"]) if pd.notna(r.get("n_lines")) else None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_revision_book_b(path: Path | None = None) -> pd.DataFrame:
    """#7 DB × PN · l12m_eur · BOOK_B."""
    path = path or (DERIVED / "revision_book_b_top_review.csv")
    name = "revision_book_b_top_review"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["pn", "distributor_code", "l12m_eur"], name)
    as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["distributor_code"]).strip().upper()
        pn = str(r["pn"]).strip()
        if not db or not pn:
            continue
        eur = r["l12m_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        action = r.get("recommended_action")
        action_s = str(action).strip() if pd.notna(action) else None
        oid = _sha1_id("BOOK_B", db, "PN", pn)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "BOOK_B",
                "db_code": db,
                "entity_key": pn,
                "entity_grain": "PN",
                "eur_at_stake": eur_f,
                "eur_basis": "L12M",
                "source_file": path.name,
                "source_column": "l12m_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": action_s,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}|pn={pn}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_leakage_monday_actions(path: Path | None = None) -> pd.DataFrame:
    """#8 DB × PN · gap_eur · LEAKAGE (dedupes into #1 when ids collide)."""
    path = path or (DERIVED / "leakage_monday_actions_20260819.csv")
    name = "leakage_monday_actions"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["db", "pn", "gap_eur"], name)
    as_of = _file_as_of(path)
    # Prefer date encoded in filename if present
    if "20260819" in path.name:
        as_of = date(2026, 8, 19)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["db"]).strip().upper()
        pn = str(r["pn"]).strip()
        if not db or not pn:
            continue
        eur = r["gap_eur"]
        eur_f = float(eur) if pd.notna(eur) else None
        action = r.get("recommended_action")
        action_s = str(action).strip() if pd.notna(action) else None
        oid = _sha1_id("LEAKAGE", db, "PN", pn)
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "LEAKAGE",
                "db_code": db,
                "entity_key": pn,
                "entity_grain": "PN",
                "eur_at_stake": eur_f,
                "eur_basis": "ANNUALISED_SOURCE",
                "source_file": path.name,
                "source_column": "gap_eur",
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": action_s,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}|pn={pn}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


def adapt_account_health(path: Path | None = None) -> pd.DataFrame:
    """#9 DB × month · no € · ACCOUNT_HEALTH."""
    path = path or (INTERACTIONS / "account_health_latest_flagged.csv")
    name = "account_health_latest_flagged"
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    count_in = len(df)
    _require_cols(df, ["db_code", "year_month"], name)
    file_as_of = _file_as_of(path)
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        db = str(r["db_code"]).strip().upper()
        ym = str(r["year_month"]).strip()
        if not db or not ym:
            continue
        entity_key = f"{db}|{ym}"
        as_of = _parse_date(r.get("as_of")) or file_as_of
        reasons = r.get("alert_reasons")
        action_s = str(reasons).strip()[:500] if pd.notna(reasons) else None
        level = r.get("alert_level")
        if pd.notna(level):
            action_s = f"[{level}] {action_s or ''}".strip()
        oid = _sha1_id("ACCOUNT_HEALTH", db, "DB", entity_key)
        n30 = r.get("n_30d")
        rows.append(
            {
                "opportunity_id": oid,
                "signal_type": "ACCOUNT_HEALTH",
                "db_code": db,
                "entity_key": entity_key,
                "entity_grain": "DB",
                "eur_at_stake": None,  # non-monetary by design
                "eur_basis": None,
                "source_file": path.name,
                "source_column": None,
                "source_as_of": as_of,
                "raised_on": as_of,
                "last_seen_on": as_of,
                "recommended_action": action_s,
                "also_seen_in": None,
                "evidence_ref": f"{path.name}#row={i}|db={db}|ym={ym}",
                "adapter_name": name,
                "horizon_date": BILLING_HORIZON,
                "count_basis_n": int(n30) if pd.notna(n30) else None,
            }
        )
    return _finish(rows, adapter_name=name, count_in=count_in, source_file=path.name)


ADAPTERS: list[tuple[str, Callable[[], pd.DataFrame]]] = [
    ("dealer_leakage_ituk", adapt_dealer_leakage_ituk),
    ("revision_exception_queue", adapt_revision_exception_queue),
    ("replenishment_exceptions_cy2025", adapt_replenishment_exceptions),
    ("early_warning", adapt_early_warning),
    ("defection_alerts", adapt_defection_alerts),
    ("no_pr00_gap_cy2025_ranked", adapt_no_pr00_gap),
    ("revision_book_b_top_review", adapt_revision_book_b),
    ("leakage_monday_actions", adapt_leakage_monday_actions),
    ("account_health_latest_flagged", adapt_account_health),
]

# Deliberately excluded (rollup of #4+#9 — would double-count)
EXCLUDED_SOURCES = [
    "portfolio_triage_20260819.csv — rollup of early_warning + account_health; excluded to avoid double-count",
]

GRAIN_RANK = {"PN": 3, "DEALER": 2, "CATEGORY": 2, "DB": 1, "NETWORK": 0}


def run_all_adapters() -> tuple[pd.DataFrame, list[dict[str, Any]], list[str]]:
    """Run all nine adapters. Returns (concat frame, per-adapter stats, build_log lines)."""
    frames: list[pd.DataFrame] = []
    stats: list[dict[str, Any]] = []
    log_lines: list[str] = []
    for name, fn in ADAPTERS:
        try:
            df = fn()
            frames.append(df)
            stats.append(
                {
                    "adapter": name,
                    "source_file": df.attrs.get("source_file"),
                    "count_in": df.attrs.get("count_in", 0),
                    "count_out": df.attrs.get("count_out", 0),
                    "status": "ok",
                }
            )
            log_lines.append(
                f"ADAPTER {name}: count_in={df.attrs.get('count_in')} count_out={df.attrs.get('count_out')}"
            )
        except Exception as e:
            stats.append({"adapter": name, "status": "FAIL", "error": str(e)})
            log_lines.append(f"ADAPTER {name}: FAIL — {e}")
            raise
    for note in EXCLUDED_SOURCES:
        log_lines.append(f"EXCLUDED: {note}")
    if not frames:
        return _empty_frame(), stats, log_lines
    out = pd.concat(frames, ignore_index=True)
    return out, stats, log_lines
