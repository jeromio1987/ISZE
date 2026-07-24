#!/usr/bin/env python3
"""
Export aggregated, GPT-safe CSVs to Data/gpt_safe/ (no raw billing rows).

Requires green verification (or pass --force after manual review).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, GPT_SAFE_DIR  # noqa: E402

REPORT_MD = DERIVED_DIR / "_verification_report.md"
REPORT_JSON = DERIVED_DIR / "_verification_report.json"

EXPORTS: list[tuple[str, Path, str]] = [
    ("pms_capture_by_db_year_summary.csv", DERIVED_DIR / "pms_capture_by_db_year.csv", "pms_capture"),
    ("pms_opportunity_matrix.csv", DERIVED_DIR / "pms_opportunity_matrix.csv", "copy"),
    ("network_percentile.csv", DERIVED_DIR / "network_percentile.csv", "copy"),
    ("ituk_pms_pn_audit.csv", DERIVED_DIR / "ituk_pms_pn_audit.csv", "copy"),
    ("ituk_pilot_capture.csv", DERIVED_DIR / "pms_capture_by_db_year.csv", "ituk_pilot"),
    ("gps_spu_by_distributor.csv", DERIVED_DIR / "gps_spu_by_distributor.csv", "copy"),
    ("mix_genuine_bvp_pms.csv", DERIVED_DIR / "mix_genuine_bvp_pms.csv", "copy"),
    ("sales_by_db_fig_key_year.csv", DERIVED_DIR / "sales_by_db_fig_key_year.csv", "copy"),
    ("verification_summary.json", REPORT_JSON, "copy"),
]


def _summarize_pms_capture(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    totals = df[df["line_type"] == "total"].copy()
    return totals.groupby(
        ["year", "distributor_code", "pms_category", "scope"],
        as_index=False,
    ).agg(
        uio_units=("uio_units", "max"),
        expected_qty=("expected_qty", "sum"),
        actual_qty=("actual_qty", "sum"),
        capture_rate=("capture_rate", "mean"),
        revenue_gap_eur=("revenue_gap_eur", "sum"),
    )


def _ituk_pilot(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    sub = df[(df["distributor_code"] == "ITUK") & (df["line_type"] == "total")]
    cols = [
        "year",
        "pms_category",
        "category_label",
        "uio_units",
        "uio_source",
        "expected_qty",
        "actual_qty",
        "capture_rate",
        "revenue_gap_eur",
        "scope",
    ]
    return sub[[c for c in cols if c in sub.columns]].sort_values(["pms_category", "year"])


def _require_verify_ok(force: bool) -> None:
    if force:
        print("WARNING: --force skips verification gate", flush=True)
        return
    if not REPORT_MD.exists():
        raise SystemExit(f"Missing {REPORT_MD} — run verify_derived_pipeline.py first")
    text = REPORT_MD.read_text(encoding="utf-8")
    if REPORT_JSON.exists():
        summary = json.loads(REPORT_JSON.read_text(encoding="utf-8")).get("summary", {})
        if summary.get("fail", 0) > 0:
            raise SystemExit("Verification has failures — fix before gpt_safe export")
        if not summary.get("ok", False):
            raise SystemExit("Verification not OK — run verify_derived_pipeline.py")
    elif "❌" in text:
        raise SystemExit("Verification report shows failures — fix before gpt_safe export")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Export even if verify not green")
    parser.add_argument("--verify", action="store_true", help="Run verify_derived_pipeline.py first")
    args = parser.parse_args()

    if args.verify:
        rc = subprocess.call([sys.executable, str(PRISM_ROOT / "scripts" / "verify_derived_pipeline.py")])
        if rc != 0:
            return rc

    _require_verify_ok(args.force)
    GPT_SAFE_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for out_name, src, mode in EXPORTS:
        out_path = GPT_SAFE_DIR / out_name
        if not src.exists():
            print(f"SKIP (missing): {src.name}")
            continue
        if mode == "pms_capture":
            df = _summarize_pms_capture(src)
        elif mode == "ituk_pilot":
            df = _ituk_pilot(src)
        else:
            df = pd.read_csv(src) if src.suffix == ".csv" else None
            if out_name.endswith(".json"):
                out_path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                manifest.append({"file": out_name, "rows": "n/a", "source": src.name})
                print(f"  -> {out_name}")
                continue
        if df is not None:
            df.to_csv(out_path, index=False)
            manifest.append({"file": out_name, "rows": len(df), "source": src.name})
            print(f"  -> {out_name} ({len(df):,} rows)")

    readme = GPT_SAFE_DIR / "EXPORT_MANIFEST.md"
    lines = [
        "# GPT-safe export",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "Aggregates only — no `raw/sales/*.XLSX` or line-level billing.",
        "",
        "| File | Rows | Source |",
        "|------|------|--------|",
    ]
    for m in manifest:
        lines.append(f"| {m['file']} | {m['rows']} | {m['source']} |")
    readme.write_text("\n".join(lines), encoding="utf-8")
    print(f"Manifest: {readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
