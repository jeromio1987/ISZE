#!/usr/bin/env python3
"""
Deterministic verification for ISZE Data/derived pipeline (P0–P5).

Run after any agent or manual build:
  python scripts/verify_derived_pipeline.py

Writes:
  Data/derived/_verification_report.json
  Data/derived/_verification_report.md

Exit 0 = all checks passed; 1 = one or more failures (for CI / hooks).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    BVP_CATALOG_XLSX,
    DATA_ROOT,
    DERIVED_DIR,
    RAW_SALES_DIR,
    SALES_FACT_PARQUET,
    data_status,
)
from modules.bvp_analytics import UIO_OVERRIDES  # noqa: E402
from modules.bvp_dashboard_data import is_ready, load_bvp_bundle  # noqa: E402
from modules.year_coverage import is_partial, latest_complete_year  # noqa: E402

FIXTURES_PATH = PRISM_ROOT / "data" / "verification_fixtures.yaml"
REPORT_JSON = DERIVED_DIR / "_verification_report.json"
REPORT_MD = DERIVED_DIR / "_verification_report.md"


@dataclass
class Check:
    id: str
    status: str  # pass | warn | fail
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    generated_at: str
    data_root: str
    checks: list[Check] = field(default_factory=list)

    def add(self, check: Check) -> None:
        self.checks.append(check)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")

    @property
    def warned(self) -> int:
        return sum(1 for c in self.checks if c.status == "warn")

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    def ok(self) -> bool:
        return self.failed == 0


def _load_fixtures() -> dict[str, Any]:
    if not FIXTURES_PATH.exists():
        raise FileNotFoundError(f"Missing fixtures: {FIXTURES_PATH}")
    with FIXTURES_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _chk(
    report: Report,
    cid: str,
    ok: bool,
    msg: str,
    warn: bool = False,
    **detail: Any,
) -> None:
    status = "pass" if ok else ("warn" if warn else "fail")
    report.add(Check(cid, status, msg, detail))


def check_raw_files(report: Report, fx: dict[str, Any]) -> None:
    # Fixture paths use the legacy "raw/" prefix; resolve through config so the
    # check works on numbered folders (12_raw) after legacy junction removal.
    from config import RAW_REFERENCE_DIR, RAW_SALES_DIR

    prefix_map = {"raw/sales": RAW_SALES_DIR, "raw/reference": RAW_REFERENCE_DIR}
    for rel in fx.get("required_raw", []):
        rel_norm = rel.replace("\\", "/")
        p = DATA_ROOT / rel_norm
        if not p.exists():
            for prefix, resolved_dir in prefix_map.items():
                if rel_norm.startswith(prefix + "/"):
                    p = resolved_dir / rel_norm[len(prefix) + 1 :]
                    break
        _chk(report, f"raw.{rel}", p.exists(), f"{'Found' if p.exists() else 'Missing'} {rel}", path=str(p))


def check_derived_files(report: Report, fx: dict[str, Any]) -> None:
    for name in fx.get("required_derived", []):
        p = DERIVED_DIR / name
        _chk(report, f"derived.{name}", p.exists(), f"{'Found' if p.exists() else 'Missing'} {name}", path=str(p))


def check_sales_fact(report: Report, fx: dict[str, Any]) -> None:
    cfg = fx.get("sales_fact", {})
    if not SALES_FACT_PARQUET.exists():
        _chk(report, "sales_fact.exists", False, "sales_fact.parquet missing")
        return

    df = pd.read_parquet(SALES_FACT_PARQUET)
    n = len(df)
    expected = int(cfg.get("row_count", 0))
    tol_pct = float(cfg.get("row_tolerance_pct", 0.5))
    if expected > 0:
        delta_pct = abs(n - expected) / expected * 100
        ok = delta_pct <= tol_pct
        _chk(
            report,
            "sales_fact.row_count",
            ok,
            f"Row count {n:,} (expected ~{expected:,}, Δ {delta_pct:.2f}%)",
            actual=n,
            expected=expected,
            warn=not ok and delta_pct <= tol_pct * 2,
        )
    else:
        _chk(report, "sales_fact.row_count", n > 0, f"Row count {n:,}")

    # Parquet is pre-mapping; distributor_code is applied in sales_loader at read time.
    required_cols = {"year", "sold_to", "part_number", "net_sales_value", "billed_qty", "billing_date"}
    missing = required_cols - set(df.columns)
    _chk(report, "sales_fact.schema", not missing, "Schema OK" if not missing else f"Missing {missing}")

    if "year" in df.columns:
        years = sorted(int(y) for y in df["year"].dropna().unique())
        want = cfg.get("years", [])
        _chk(report, "sales_fact.years", all(y in years for y in want), f"Years present: {years}", years=years)

    saty_cfg = fx.get("sales_fact_saty", {})
    col = saty_cfg.get("required_column", "saty")
    if col in df.columns:
        pct = df[col].notna().sum() / n * 100 if n else 0
        min_pct = float(saty_cfg.get("min_non_null_pct", 95))
        _chk(
            report,
            "sales_fact.saty",
            pct >= min_pct,
            f"SaTy populated on {pct:.1f}% of rows (min {min_pct}%)",
            non_null_pct=pct,
        )
    elif saty_cfg:
        _chk(report, "sales_fact.saty", False, f"Missing column {col} — re-run build_sales_fact_from_cy.py")

    fig_cfg = fx.get("sales_fact_fig_key", {})
    if fig_cfg:
        if "fig_key" in df.columns:
            pct = df["fig_key"].notna().sum() / n * 100 if n else 0
            min_pct = float(fig_cfg.get("min_non_null_pct", 90))
            _chk(
                report,
                "sales_fact.fig_key",
                pct >= min_pct,
                f"fig_key populated on {pct:.1f}% of rows (min {min_pct}%)",
                non_null_pct=pct,
            )
        else:
            _chk(report, "sales_fact.fig_key", False, "Missing column fig_key — re-run build_sales_fact_from_cy.py")

    try:
        from config import resolve_mapping_path
        from modules.data_prep import load_distributor_mapping
        from modules.sales_loader import load_prism_sales

        df_mapped, _ = load_prism_sales(
            load_distributor_mapping(str(resolve_mapping_path()))
        )
        nm = len(df_mapped)
        unmapped = int((df_mapped["distributor_code"] == "UNMAPPED").sum())
        pct = unmapped / nm * 100 if nm else 0
        max_pct = float(cfg.get("max_unmapped_pct", 1.0))
        _chk(
            report,
            "sales_fact.unmapped",
            pct <= max_pct,
            f"UNMAPPED {unmapped:,} ({pct:.2f}%) after distributor map",
            unmapped=unmapped,
            max_pct=max_pct,
        )
    except Exception as e:
        _chk(report, "sales_fact.unmapped", False, f"Could not check UNMAPPED: {e}")


def check_dimension(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "bvp_pn_dimension.csv"
    if not path.exists():
        return
    cfg = fx.get("bvp_pn_dimension", {})
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, "p0.rows", n >= int(cfg.get("min_rows", 1)), f"Dimension {n:,} PNs", rows=n)
    if "pms_flag" in df.columns:
        pms = int(df["pms_flag"].sum())
        _chk(
            report,
            "p0.pms_flagged",
            pms >= int(cfg.get("min_pms_flagged", 1)),
            f"PMS-flagged {pms:,}",
            pms=pms,
        )
    if "line_type" in df.columns:
        allowed = set(cfg.get("line_types", ["genuine", "bvp"]))
        bad = set(df["line_type"].dropna().unique()) - allowed
        _chk(report, "p0.line_type", not bad, f"line_type values OK" if not bad else f"Unexpected: {bad}")


def check_bvp_addressable_basket(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "bvp_addressable_basket.csv"
    if not path.exists():
        return
    cfg = fx.get("bvp_addressable_basket", {})
    df = pd.read_csv(path, dtype={"genuine_pn": str, "bvp_pn": str})
    n = len(df)
    _chk(report, "bvp_addr.rows", n >= int(cfg.get("min_rows", 1)), f"Addressable basket {n:,} rows", rows=n)

    required = set(cfg.get("required_columns", []))
    missing = required - set(df.columns)
    _chk(
        report,
        "bvp_addr.schema",
        not missing,
        "Schema OK" if not missing else f"Missing {missing}",
    )

    min_dist = int(cfg.get("min_distinct_distributors", 25))
    n_dist = df["distributor_code"].nunique() if "distributor_code" in df.columns else 0
    _chk(
        report,
        "bvp_addr.distributors",
        n_dist >= min_dist,
        f"{n_dist} distributors (min {min_dist})",
        distributors=n_dist,
    )

    min_sg = int(cfg.get("min_distinct_subgroups", 22))
    n_sg = df["product_subgroup"].nunique() if "product_subgroup" in df.columns else 0
    _chk(
        report,
        "bvp_addr.subgroups",
        n_sg >= min_sg,
        f"{n_sg} product subgroups (min {min_sg})",
        subgroups=n_sg,
    )

    ituk = df[df["distributor_code"] == "ITUK"] if "distributor_code" in df.columns else pd.DataFrame()
    if not ituk.empty and "bvp_pn" in ituk.columns:
        n_addr = ituk["bvp_pn"].nunique()
        n_sell = ituk.loc[ituk["currently_selling_bvp"] == True, "bvp_pn"].nunique()  # noqa: E712
        pct = n_sell / n_addr * 100 if n_addr else 0
        _chk(
            report,
            "bvp_addr.ituk_penetration",
            pct >= 50,
            f"ITUK BVP penetration {n_sell}/{n_addr} ({pct:.0f}%)",
            warn=pct < 50,
            selling=n_sell,
            addressable=n_addr,
        )


def check_crossref(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "genuine_bvp_crossref.csv"
    if not path.exists():
        return
    cfg = fx.get("genuine_bvp_crossref", {})
    df = pd.read_csv(path, dtype={"genuine_pn": str, "bvp_pn": str})
    n = len(df)
    _chk(report, "p0b.rows", n >= int(cfg.get("min_rows", 1)), f"Crossref {n:,} pairs", rows=n)
    if "pair_source" in df.columns:
        allowed = set(cfg.get("pair_sources", []))
        if allowed:
            bad = set(df["pair_source"].dropna().unique()) - allowed
            _chk(
                report,
                "p0b.pair_source",
                not bad,
                "pair_source OK" if not bad else f"Unexpected: {bad}",
            )
        n_cat = int(df["pair_source"].astype(str).str.startswith("catalog").sum())
        _chk(
            report,
            "p0b.catalog_pairs",
            n_cat >= int(cfg.get("min_catalog_pairs", 1)),
            f"Catalog-derived pairs {n_cat:,}",
            catalog_pairs=n_cat,
        )
    dup = df.duplicated(subset=["genuine_pn", "bvp_pn"]).sum()
    _chk(report, "p0b.unique_pairs", dup == 0, f"Duplicate (genuine,bvp) keys: {dup}")


def check_pms_capture(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "pms_capture_by_db_year.csv"
    if not path.exists():
        return
    cfg = fx.get("pms_capture", {})
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, "p1.rows", n >= int(cfg.get("min_rows", 1)), f"PMS capture {n:,} rows", rows=n)

    required = {
        "year",
        "distributor_code",
        "pms_category",
        "line_type",
        "capture_rate",
        "uio_units",
        "expected_qty",
        "actual_qty",
    }
    missing = required - set(df.columns)
    _chk(report, "p1.schema", not missing, "Schema OK" if not missing else f"Missing {missing}")

    if "line_type" in df.columns:
        allowed = set(cfg.get("line_types", ["genuine", "bvp", "total"]))
        bad = set(df["line_type"].dropna().unique()) - allowed
        _chk(report, "p1.line_type", not bad, "line_type OK" if not bad else f"Unexpected {bad}")

    totals = df[df["line_type"] == "total"] if "line_type" in df.columns else df
    if not totals.empty and "capture_rate" in totals.columns:
        cap_max = float(cfg.get("capture_rate_max", 1.05))
        over = totals[totals["capture_rate"] > cap_max]
        _chk(
            report,
            "p1.capture_cap",
            over.empty,
            f"All total capture_rate ≤ {cap_max}" if over.empty else f"{len(over)} rows over cap",
            sample=over.head(3).to_dict("records") if not over.empty else [],
        )

    pilot = fx.get("ituk_pilot", {})
    dist = pilot.get("distributor_code", "ITUK")
    uio_exp = int(pilot.get("uio_units", 22389))
    uio_tol = int(pilot.get("uio_tolerance", 0))
    ituk = df[(df["distributor_code"] == dist) & (df["line_type"] == "total")]
    if not ituk.empty:
        uio_vals = ituk["uio_units"].dropna().unique()
        uio_ok = all(abs(int(v) - uio_exp) <= uio_tol for v in uio_vals)
        _chk(
            report,
            "p1.ituk.uio",
            uio_ok,
            f"ITUK uio_units {list(uio_vals)} (expected {uio_exp})",
            expected=uio_exp,
            override=UIO_OVERRIDES.get(dist),
        )

        bands = pilot.get("oil_filter_total_capture", {})
        oil = ituk[ituk["pms_category"] == "oil_filter"]
        for year, band in bands.items():
            row = oil[oil["year"] == int(year)]
            if row.empty:
                _chk(report, f"p1.ituk.oil_filter.{year}", False, f"No ITUK oil_filter row for {year}")
                continue
            cap = float(row["capture_rate"].iloc[0])
            lo, hi = float(band.get("min", 0)), float(band.get("max", 1))
            ok = lo <= cap <= hi
            _chk(
                report,
                f"p1.ituk.oil_filter.{year}",
                ok,
                f"ITUK oil_filter {year} capture {cap:.1%} (band {lo:.0%}–{hi:.0%})",
                capture_rate=cap,
            )
    else:
        _chk(report, "p1.ituk.present", False, "No ITUK total rows in pms_capture")


def check_gps_spu_warranty(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "gps_spu_by_distributor.csv"
    cfg = fx.get("gps_spu_warranty", {})
    if not cfg or not path.exists():
        return
    df = pd.read_csv(path)
    req = set(cfg.get("required_columns", []))
    missing = req - set(df.columns)
    _chk(
        report,
        "gps.warranty.schema",
        not missing,
        "GPS warranty columns OK" if not missing else f"Missing {missing}",
    )
    wyear = int(cfg.get("warranty_year", 2025))
    sub = df[df["year"] == wyear]
    if not sub.empty and "warranty_parts_eur" in df.columns:
        has_w = sub["warranty_parts_eur"].notna()
        n = int(has_w.sum())
        need = int(cfg.get("min_dbs_with_warranty", 17))
        _chk(
            report,
            "gps.warranty.coverage",
            n >= need,
            f"CY{wyear} warranty on {n} DBs (min {need})",
            distributors=n,
        )
        if "sales_ex_warranty_eur" in sub.columns:
            bad = sub[has_w & (sub["sales_ex_warranty_eur"] > sub["total_sales_eur"])]
            _chk(
                report,
                "gps.warranty.sales_bounds",
                bad.empty,
                "ex-warranty sales ≤ total" if bad.empty else f"{len(bad)} rows exceed total sales",
            )


def check_pms_all_distributors(report: Report, fx: dict[str, Any]) -> None:
    pms_path = DERIVED_DIR / "pms_capture_by_db_year.csv"
    summ_path = DERIVED_DIR / "pms_summary_by_db.csv"
    cfg_cap = fx.get("pms_capture", {})
    cfg_sum = fx.get("pms_summary_by_db", {})

    if pms_path.exists() and cfg_cap.get("min_distributors"):
        df = pd.read_csv(pms_path)
        totals = df[df["line_type"] == "total"]
        years = [int(y) for y in totals["year"].dropna().unique()]
        complete_yr = latest_complete_year(years)
        dbs = totals[totals["year"] == complete_yr]["distributor_code"].nunique()
        need = int(cfg_cap["min_distributors"])
        _chk(
            report,
            "p1.distributor_count",
            dbs >= need,
            f"PMS capture {dbs} distributors @ complete {complete_yr} (min {need})",
            distributors=dbs,
            year=complete_yr,
        )

    if not summ_path.exists() or not cfg_sum:
        return
    df = pd.read_csv(summ_path)
    n = len(df)
    need = int(cfg_sum.get("min_distributors", 18))
    _chk(
        report,
        "pms.summary.rows",
        n >= need,
        f"pms_summary_by_db {n} distributors (min {need})",
        rows=n,
    )
    if "year" in df.columns and n:
        summ_years = sorted({int(y) for y in df["year"].dropna().unique()})
        capture_years = [int(y) for y in pd.read_csv(pms_path)["year"].dropna().unique()] if pms_path.exists() else summ_years
        complete_yr = latest_complete_year(capture_years)
        _chk(
            report,
            "pms.summary.complete_year",
            summ_years == [complete_yr],
            f"pms_summary_by_db year {summ_years} == complete {complete_yr}"
            if summ_years == [complete_yr]
            else f"pms_summary_by_db year {summ_years} is not latest complete {complete_yr} (partial-year trap)",
            years=summ_years,
            complete_year=complete_yr,
        )
        _chk(
            report,
            "pms.summary.not_partial",
            not any(is_partial(y) for y in summ_years),
            "pms_summary_by_db is a complete billing year"
            if not any(is_partial(y) for y in summ_years)
            else f"pms_summary_by_db includes partial year {summ_years}",
        )
    req = set(cfg_sum.get("required_columns", []))
    missing = req - set(df.columns)
    _chk(
        report,
        "pms.summary.schema",
        not missing,
        "PMS summary schema OK" if not missing else f"Missing {missing}",
    )


def check_pms_opportunity_matrix(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "pms_opportunity_matrix.csv"
    if not path.exists():
        return
    cfg = fx.get("pms_opportunity_matrix", {})
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, "contract3.rows", n >= int(cfg.get("min_rows", 1)), f"PMS opportunity matrix {n:,} rows", rows=n)

    required = {
        "distributor_code",
        "pms_category",
        "year",
        "capture_rate_total",
        "capture_rate_genuine",
        "revenue_gap_eur",
        "avg_sp_eur",
        "tam_eur",
        "uio_units",
        "genuine_bvp_gap_pp",
        "country",
        "region",
    }
    missing = required - set(df.columns)
    _chk(report, "contract3.schema", not missing, "Schema OK" if not missing else f"Missing {missing}")

    cap_max = float(cfg.get("capture_rate_max", 1.05))
    over = df[df["capture_rate_total"] > cap_max]
    _chk(
        report,
        "contract3.capture_cap",
        over.empty,
        f"All capture_rate_total ≤ {cap_max}" if over.empty else f"{len(over)} rows over cap",
    )

    tam_min = float(cfg.get("tam_eur_min", 1.0))
    # TAM is zero only when avg SP is zero (no sales); rows with revenue should meet floor.
    low_tam = df[(df["avg_sp_eur"] > 0) & (df["tam_eur"] < tam_min)] if "tam_eur" in df.columns else pd.DataFrame()
    _chk(
        report,
        "contract3.tam_eur",
        low_tam.empty,
        f"tam_eur ≥ {tam_min} where avg_sp_eur > 0" if low_tam.empty else f"{len(low_tam)} rows below tam floor",
    )


def check_network_percentile(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "network_percentile.csv"
    if not path.exists():
        return
    cfg = fx.get("network_percentile", {})
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, "contract10.rows", n >= int(cfg.get("min_rows", 1)), f"Network percentile {n:,} rows", rows=n)

    required = {
        "distributor_code",
        "year",
        "metric",
        "raw_value",
        "percentile_rank",
        "network_median",
        "vs_median",
        "n_distributors",
    }
    missing = required - set(df.columns)
    _chk(report, "contract10.schema", not missing, "Schema OK" if not missing else f"Missing {missing}")

    want_metrics = cfg.get("metrics", [])
    if want_metrics:
        have = set(df["metric"].dropna().unique())
        missing_m = set(want_metrics) - have
        _chk(
            report,
            "contract10.metrics",
            not missing_m,
            "All metrics present" if not missing_m else f"Missing metrics: {missing_m}",
            metrics=sorted(have),
        )

    lo, hi = cfg.get("percentile_range", [0, 100])
    pr = df["percentile_rank"].dropna()
    if not pr.empty:
        ok = pr.min() >= float(lo) - 0.01 and pr.max() <= float(hi) + 0.01
        _chk(
            report,
            "contract10.percentile_range",
            ok,
            f"percentile_rank in [{lo}, {hi}] (actual {pr.min():.1f}–{pr.max():.1f})",
        )


def _check_csv_min_rows(report: Report, fx: dict[str, Any], key: str, cid: str) -> None:
    cfg = fx.get(key, {})
    if not cfg:
        return
    rel = {
        "vor_airfreight_risk": "vor_airfreight_risk.csv",
        "vor_seasonality": "vor_seasonality.csv",
        "vor_profile": "vor_profile.csv",
        "capture_trajectory": "capture_trajectory.csv",
        "part_lifecycle": "part_lifecycle.csv",
        "revenue_concentration": "revenue_concentration.csv",
        "revenue_waterfall": "revenue_waterfall.csv",
        "price_premium": "price_premium.csv",
        "basket_correlation": "basket_correlation.csv",
        "substitution_timeline": "substitution_timeline.csv",
        "capture_recovery_model": "capture_recovery_model.csv",
    }.get(key)
    if not rel:
        return
    path = DERIVED_DIR / rel
    if not path.exists():
        return
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, cid, n >= int(cfg.get("min_rows", 1)), f"{key} {n:,} rows", rows=n)


def check_parts_catalog_dimension(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "parts_catalog_dimension.csv"
    cfg = fx.get("parts_catalog_dimension", {})
    if not path.exists():
        return
    df = pd.read_csv(path, dtype=str)
    n = len(df)
    _chk(
        report,
        "figkey.catalog.rows",
        n >= int(cfg.get("min_rows", 1000)),
        f"parts_catalog_dimension {n:,} rows",
        rows=n,
    )
    if "fig_key" in df.columns:
        has_fk = df["fig_key"].notna() & (df["fig_key"].astype(str).str.strip() != "")
        n_fk = int(has_fk.sum())
        pct = 100.0 * n_fk / max(n, 1)
        need_n = int(cfg.get("min_with_fig_key", 1000))
        need_pct = float(cfg.get("min_fig_key_pct", 0))
        _chk(
            report,
            "figkey.catalog.coverage",
            n_fk >= need_n and pct >= need_pct,
            f"PNs with fig_key: {n_fk:,} ({pct:.1f}%, min {need_pct:.0f}%)",
        )
    if "pms_registry" in df.columns and "fig_key" in df.columns:
        reg = df["pms_registry"].astype(str).str.lower().isin(("true", "1"))
        with_fk = reg & df["fig_key"].notna() & (df["fig_key"].astype(str).str.strip() != "")
        need = int(cfg.get("min_registry_with_fig_key", 1))
        _chk(
            report,
            "figkey.catalog.registry_fig",
            with_fk.sum() >= need,
            f"Registry PNs with fig_key: {with_fk.sum()} (min {need})",
        )


def check_sales_by_fig_key(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "sales_by_db_fig_key_year.csv"
    cfg = fx.get("sales_by_db_fig_key_year", {})
    if not path.exists():
        return
    df = pd.read_csv(path)
    n = len(df)
    _chk(
        report,
        "figkey.sales.rows",
        n >= int(cfg.get("min_rows", 10)),
        f"sales_by_db_fig_key_year {n:,} rows",
        rows=n,
    )
    mapped = df[df["fig_key"].astype(str) != "unmapped"]
    need = int(cfg.get("min_mapped_fig_key_rows", 1))
    _chk(
        report,
        "figkey.sales.mapped",
        len(mapped) >= need,
        f"Mapped fig_key rows: {len(mapped)} (min {need})",
    )


def check_ituk_pms_pn_audit(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "ituk_pms_pn_audit.csv"
    cfg = fx.get("ituk_pms_pn_audit", {})
    if not cfg or not path.exists():
        return
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, "contract16.rows", n >= int(cfg.get("min_rows", 1)), f"ITUK PMS PN audit {n:,} rows", rows=n)

    required = set(cfg.get("required_columns", []))
    missing = required - set(df.columns)
    _chk(
        report,
        "contract16.schema",
        not missing,
        "Schema OK" if not missing else f"Missing {missing}",
    )

    dist = cfg.get("distributor_code", "ITUK")
    if "distributor_code" in df.columns:
        bad = set(df["distributor_code"].dropna().unique()) - {dist}
        _chk(
            report,
            "contract16.distributor",
            not bad,
            f"All rows {dist}" if not bad else f"Unexpected distributors: {bad}",
        )

    oil = df[df["pms_category"] == "oil_filter"] if "pms_category" in df.columns else pd.DataFrame()
    if not oil.empty:
        for year, grp in oil.groupby("year"):
            n_pn = grp["part_number"].nunique()
            min_pn = int(cfg.get("oil_filter_min_pns", 3))
            _chk(
                report,
                f"contract16.oil_filter.{int(year)}",
                n_pn >= min_pn,
                f"ITUK oil_filter {int(year)}: {n_pn} PNs (min {min_pn})",
                pns=n_pn,
            )


def check_strategic_contracts(report: Report, fx: dict[str, Any]) -> None:
    for key in (
        "vor_airfreight_risk",
        "vor_seasonality",
        "vor_profile",
        "capture_trajectory",
        "part_lifecycle",
        "revenue_concentration",
        "revenue_waterfall",
        "price_premium",
        "basket_correlation",
        "substitution_timeline",
        "capture_recovery_model",
    ):
        _check_csv_min_rows(report, fx, key, f"contract.{key}")

    geo_cfg = fx.get("distributor_geo", {})
    if geo_cfg:
        from config import PRISM_DATA_DIR

        geo_path = PRISM_DATA_DIR / "distributor_geo.csv"
        if geo_path.exists():
            gdf = pd.read_csv(geo_path)
            n = len(gdf)
            _chk(
                report,
                "contract.distributor_geo",
                n >= int(geo_cfg.get("min_rows", 1)),
                f"distributor_geo {n:,} rows",
                path=str(geo_path),
            )


def check_aim_gps_matrix(report: Report, fx: dict[str, Any]) -> None:
    path = DERIVED_DIR / "aim_gps_matrix.csv"
    cfg = fx.get("aim_gps_matrix", {})
    if not path.exists():
        _chk(report, "aim_gps.rows", False, "aim_gps_matrix.csv missing")
        return
    df = pd.read_csv(path)
    n = len(df)
    _chk(
        report,
        "aim_gps.rows",
        n >= int(cfg.get("min_rows", 50)),
        f"AIM×GPS matrix {n:,} rows",
    )
    if "quadrant" in df.columns and cfg.get("quadrants"):
        ok = set(df["quadrant"].dropna().unique()).issubset(set(cfg["quadrants"]))
        _chk(report, "aim_gps.quadrants", ok, "Quadrant values OK")


def check_prism_bundle(report: Report) -> None:
    try:
        bundle = load_bvp_bundle()
        ready = is_ready(bundle)
        _chk(
            report,
            "prism.bvp_bundle",
            ready,
            "BVP dashboard bundle ready" if ready else "Bundle incomplete (pms_capture or mix missing)",
            pms_rows=len(bundle.get("pms_capture", [])),
            mix_subgroup=len(bundle.get("mix_subgroup", [])),
            mix_pms=len(bundle.get("mix_pms", [])),
        )
    except Exception as e:
        _chk(report, "prism.bvp_bundle", False, f"Bundle load failed: {e}")


def check_config_status(report: Report) -> None:
    st = data_status()
    critical = ["sales_parquet", "bvp_dimension", "bvp_pms_capture", "raw_cy2025", "raw_cy2023_24"]
    missing = [k for k in critical if not st.get(k)]
    _chk(
        report,
        "config.data_status",
        not missing,
        "Core data_status OK" if not missing else f"Missing flags: {missing}",
        status=st,
    )
    _chk(report, "config.bvp_catalog", BVP_CATALOG_XLSX.exists(), f"BVP catalog at {BVP_CATALOG_XLSX.name}")


def write_reports(report: Report) -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": report.generated_at,
        "data_root": report.data_root,
        "summary": {
            "pass": report.passed,
            "warn": report.warned,
            "fail": report.failed,
            "ok": report.ok(),
        },
        "checks": [asdict(c) for c in report.checks],
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# ISZE derived pipeline verification",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Data root:** `{report.data_root}`",
        "",
        f"| Pass | Warn | Fail |",
        f"|------|------|------|",
        f"| {report.passed} | {report.warned} | {report.failed} |",
        "",
        "## Checks",
        "",
    ]
    for c in report.checks:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(c.status, "•")
        lines.append(f"- {icon} **{c.id}** — {c.message}")
    lines.extend(
        [
            "",
            "## Claude / Cursor workflow",
            "",
            "1. Agent runs builds (`run_pipeline_and_verify.ps1` or individual `build_*.py`).",
            "2. This script runs automatically at the end.",
            "3. **Claude reads** `_verification_report.md` before claiming success.",
            "4. On any ❌, fix and re-run — do not present numbers from a failed build.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    fx = _load_fixtures()
    report = Report(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        data_root=str(DATA_ROOT),
    )

    check_raw_files(report, fx)
    check_derived_files(report, fx)
    check_config_status(report)
    check_sales_fact(report, fx)
    check_dimension(report, fx)
    check_crossref(report, fx)
    check_bvp_addressable_basket(report, fx)
    check_pms_capture(report, fx)
    check_pms_all_distributors(report, fx)
    check_gps_spu_warranty(report, fx)
    check_pms_opportunity_matrix(report, fx)
    check_network_percentile(report, fx)
    check_ituk_pms_pn_audit(report, fx)
    check_parts_catalog_dimension(report, fx)
    check_sales_by_fig_key(report, fx)
    check_aim_gps_matrix(report, fx)
    check_strategic_contracts(report, fx)
    check_prism_bundle(report)
    write_reports(report)

    print(f"Verification: {report.passed} pass, {report.warned} warn, {report.failed} fail")
    print(f"Report: {REPORT_MD}")
    for c in report.checks:
        if c.status != "pass":
            mark = "WARN" if c.status == "warn" else "FAIL"
            print(f"  [{mark}] {c.id}: {c.message}")

    return 0 if report.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())
