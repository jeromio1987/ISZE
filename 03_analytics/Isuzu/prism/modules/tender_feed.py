"""Live tender feed — the single reader of tender_data.json.

The ISZE Tender Monitor writes ``01_data/14_dashboards/tender_data.json`` each
week; ``meta.generated_at`` is the feed date. This module is the only place
PRISM reads it, so the Tender Pipeline page and the tender chart helpers always
show the same file.

The flattened table ``Data/derived/tender_pipeline.csv`` (last built 29 May 2026)
is no longer read by PRISM. The file and its builder
``scripts/build_tender_pipeline.py`` are both kept on disk.

Nothing here invents a number. Coverage counts are counted from the rows of the
file on disk, and missing stays missing: an absent value is NaN, never 0.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd

FEED_NAME = "tender_data.json"

# Columns normalised on load. Everything else is passed through untouched.
BOOL_COLS = ("rm_contract", "parts_signal")
NUM_COLS = (
    "fit_score", "win_score", "econ_score", "opportunity_score",
    "value_amount", "fleet_size", "days_to_deadline", "notice_count",
)
TEXT_DEFAULTS = {"country": "Unknown", "owner_suggested": "Unassigned", "decision": "Ignore"}

_CACHE: dict = {"key": None, "df": None, "meta": None}


def feed_path(derived_dir: str | Path | None = None) -> Path:
    """Path of the live feed. ISZE_TENDER_FEED overrides; config is the default."""
    if env := os.environ.get("ISZE_TENDER_FEED"):
        return Path(env)
    try:
        from config import DASHBOARDS_JSON_DIR  # noqa: WPS433

        return Path(DASHBOARDS_JSON_DIR) / FEED_NAME
    except ImportError:
        base = Path(derived_dir) if derived_dir else Path(__file__).resolve().parents[2] / "data" / "derived"
        return Path(base).parent / "14_dashboards" / FEED_NAME


def load_feed(derived_dir: str | Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Load the live feed once per file state.

    Returns ``(frame, meta)``. Raises FileNotFoundError when the feed is absent
    and ValueError when the JSON has no usable "opportunities" list.
    """
    path = feed_path(derived_dir)
    if not path.is_file():
        raise FileNotFoundError(f"Tender feed not found: {path}")

    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if _CACHE["key"] != key:
        _CACHE["key"] = key
        _CACHE["df"] = None
        _CACHE["meta"] = None

    if _CACHE["df"] is None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        opps = payload.get("opportunities") if isinstance(payload, dict) else None
        if not opps:
            raise ValueError(f'No "opportunities" rows in {path}')
        df = pd.DataFrame(opps)
        for col in BOOL_COLS:
            if col in df.columns:
                df[col] = df[col].astype(object).map(
                    lambda v: str(v).strip().lower() in ("true", "1", "yes") if v is not None else False
                ).astype(bool)
        for col in NUM_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        for col, fallback in TEXT_DEFAULTS.items():
            if col in df.columns:
                df[col] = df[col].fillna(fallback).replace("", fallback)
        if "deadline_date" in df.columns:
            df["deadline_dt"] = pd.to_datetime(df["deadline_date"], errors="coerce")
        else:
            df["deadline_dt"] = pd.NaT
        # Same rule as scripts/build_tender_pipeline.py: anything we pursue or watch.
        df["actionable"] = df["decision"].isin(["Attack", "Selective", "Watch"])
        _CACHE["df"] = df
        _CACHE["meta"] = dict(payload.get("meta") or {})

    return _CACHE["df"].copy(), dict(_CACHE["meta"])


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return not pd.isna(value)


def coverage(df: pd.DataFrame) -> dict[str, int]:
    """How much of the feed carries the fields the page would need. Counted, not assumed."""
    out = {"total": int(len(df))}
    for label, col in (
        ("value", "value_amount"),
        ("deadline", "deadline_date"),
        ("fleet_size", "fleet_size"),
        ("outcome", "outcome"),
    ):
        if col not in df.columns:
            out[label] = 0
            continue
        if col == "deadline_date":
            out[label] = int(df["deadline_dt"].notna().sum())
        else:
            out[label] = int(df[col].map(_is_present).sum())
    out["no_deadline"] = out["total"] - out["deadline"]
    return out


def feed_generated_at(meta: dict) -> str:
    """Raw ISO timestamp from the feed, or 'unknown'."""
    return str(meta.get("generated_at") or "unknown")


def feed_date_label(meta: dict) -> str:
    """Feed date as '22 Sep 2026', or 'unknown'."""
    raw = meta.get("generated_at")
    if not raw:
        return "unknown"
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return f"{dt.day} {dt.strftime('%b %Y')}"
    except ValueError:
        return str(raw)


def deadline_on_or_after(df: pd.DataFrame, on: date | None = None) -> pd.Series:
    """Rows whose published deadline is today or later. Undated rows are excluded."""
    on = on or date.today()
    return df["deadline_dt"].notna() & (df["deadline_dt"].dt.date >= on)
