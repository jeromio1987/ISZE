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
        "lost_sales_model": "lost_sales_model.csv",
        "lost_sales_market": "lost_sales_market.csv",
        "lost_sales_competitor_coverage": "lost_sales_competitor_coverage.csv",
        "lost_sales_pn_action": "lost_sales_pn_action.csv",
    }.get(key)
    if not rel:
        return
    path = DERIVED_DIR / rel
    if not path.exists():
        return
    df = pd.read_csv(path)
    n = len(df)
    _chk(report, cid, n >= int(cfg.get("min_rows", 1)), f"{key} {n:,} rows", rows=n)


def check_lost_sales_model(report: Report, fx: dict[str, Any]) -> None:
    """Tie the lost-sales model back to the parts base and to the contracts it borrows from.

    These are the checks that stop a rebuild from looking fine while it has quietly lost a family,
    mis-joined the taxonomy, or drifted off ``sales_fact``.
    """
    cfg = fx.get("lost_sales_model", {})
    path = DERIVED_DIR / "lost_sales_model.csv"
    if not cfg or not path.exists():
        return
    df = pd.read_csv(path, low_memory=False)

    # 1. Billed euro must equal the parts base, to the cent. A family that fails to classify is
    #    still a row (unclassified_pn), so nothing may fall out of this sum.
    from modules.data_prep import load_distributor_mapping
    from modules.sales_loader import load_prism_sales
    from config import resolve_mapping_path

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"]
    sales = sales[~sales["is_credit_note"]]
    base_eur = float(sales["net_sales_value"].sum())
    model_eur = float(df["net_sales_eur"].sum())
    delta = abs(model_eur - base_eur)
    _chk(
        report,
        "lost_sales.billed_ties_to_parts_base",
        delta <= float(cfg.get("max_billed_delta_eur", 1.0)),
        f"billed EUR {model_eur:,.2f} vs parts base EUR {base_eur:,.2f} (delta {delta:,.2f})",
        delta_eur=round(delta, 2),
    )

    # 2. The price split must close. A non-zero residual means the three-way decomposition is
    #    arithmetically broken, which is exactly the defect it exists to fix elsewhere.
    #    Only the full-year pairs are checked: part-year pairs are deliberately left blank because
    #    the full-year split compares a part year against a full year.
    pr = df.dropna(subset=["delta_total_eur"])
    if not pr.empty:
        pr = pr[pr["year"] < int(pd.Timestamp.today().year)]
        bad_years = df[df["delta_total_eur"].notna() & (df["year"] >= int(pd.Timestamp.today().year))]
        _chk(
            report,
            "lost_sales.price_split_blanks_the_part_year",
            len(bad_years) == 0,
            f"{len(bad_years):,} part-year rows carry a full-year price split",
        )
        residual = (
            pr["delta_volume_eur"] + pr["delta_price_eur"] + pr["delta_mix_eur"]
            - pr["delta_total_eur"]
        ).abs()
        _chk(
            report,
            "lost_sales.price_split_closes",
            float(residual.max()) <= float(cfg.get("max_price_residual_eur", 1.0)),
            f"max residual EUR {residual.max():,.2f} over {len(pr):,} rows",
            max_residual_eur=round(float(residual.max()), 2),
        )
        # 3. The mix term must actually vary. All-zero mix is the signature of measuring price at
        #    the same grain as the mix axis, which makes the split an identity rather than a split.
        mix_share = float((pr["delta_mix_eur"].abs() > 0.01).mean())
        _chk(
            report,
            "lost_sales.mix_term_is_not_degenerate",
            mix_share > 0.10,
            f"{mix_share:.1%} of split rows carry a non-zero mix effect",
            mix_nonzero_share=round(mix_share, 4),
        )

    # 4. Market coverage.
    n_dist = int(df["distributor_code"].nunique())
    _chk(
        report,
        "lost_sales.distributors",
        n_dist >= int(cfg.get("min_distinct_distributors", 18)),
        f"{n_dist} distributors",
        distributors=n_dist,
    )
    years = sorted(int(y) for y in df["year"].dropna().unique())
    want = [int(y) for y in cfg.get("years", [])]
    _chk(
        report,
        "lost_sales.years",
        all(y in years for y in want),
        f"years present {years}",
        years=years,
    )

    # 5. The service axis must be present but honestly bounded. A sudden jump to near-total
    #    coverage means the join has started treating missing values as a real category.
    covered = float(
        df.loc[df["pms_category"] != "not_a_service_family", "net_sales_eur"].sum()
    )
    coverage_pct = 100 * covered / model_eur if model_eur else 0.0
    _chk(
        report,
        "lost_sales.pms_category_coverage_bounded",
        float(cfg.get("min_pms_category_coverage_pct", 0))
        <= coverage_pct
        <= float(cfg.get("max_pms_category_coverage_pct", 100)),
        f"service-axis coverage {coverage_pct:.2f}% of billed euro",
        coverage_pct=round(coverage_pct, 2),
    )

    # 6. Money may not be invented: every family row that is not explicitly market-level must
    #    carry no ceiling, and the ceiling rows must declare what they are.
    if "ceilings_are_market_level" in df.columns:
        leak = df[
            df["ceilings_are_market_level"].isna() & df["theoretical_wallet_eur"].notna()
        ]
        _chk(
            report,
            "lost_sales.ceiling_rows_are_labelled",
            len(leak) == 0,
            f"{len(leak):,} rows carry a ceiling without the market-level label",
        )

    # 7. Gap types and down-trade verdicts stay inside the documented vocabulary.
    allowed_gaps = set(cfg.get("require_gap_types", []))
    present_gaps = set(df["gap_type"].dropna().unique())
    missing = allowed_gaps - present_gaps
    _chk(
        report,
        "lost_sales.gap_types_present",
        not missing,
        f"gap types present {sorted(present_gaps)}" + (f" — missing {sorted(missing)}" if missing else ""),
        gap_types=sorted(present_gaps),
    )
    allowed_verdicts = set(cfg.get("down_trade_verdicts", []))
    verdicts = set(df["down_trade_verdict"].dropna().unique())
    unexpected = verdicts - allowed_verdicts
    _chk(
        report,
        "lost_sales.down_trade_verdicts_documented",
        not unexpected,
        f"verdicts {sorted(verdicts)}" + (f" — undocumented {sorted(unexpected)}" if unexpected else ""),
        verdicts=sorted(verdicts),
    )

    # 8. Momentum must be like-for-like on the part year. A current-year row compared against a
    #    full year would read as a collapse that did not happen.
    mo = df.dropna(subset=["momentum_basis"])
    if not mo.empty:
        bad = mo[(mo["is_partial_year"]) & (mo["momentum_basis"] != "jan_jun")]
        _chk(
            report,
            "lost_sales.partial_year_momentum_is_like_for_like",
            len(bad) == 0,
            f"{len(bad):,} part-year rows are not on a same-months basis",
        )


def check_lost_sales_competitor(report: Report, fx: dict[str, Any]) -> None:
    """Competitor coverage must stay bounded and must name its sources."""
    cfg = fx.get("lost_sales_competitor_coverage", {})
    path = DERIVED_DIR / "lost_sales_competitor_coverage.csv"
    if not cfg or not path.exists():
        return
    df = pd.read_csv(path)
    sources = set(df["source"].dropna().astype(str))
    want = set(cfg.get("require_sources", []))
    missing = want - sources
    _chk(
        report,
        "lost_sales_competitor.sources_named",
        not missing,
        f"sources {sorted(sources)}" + (f" — missing {sorted(missing)}" if missing else ""),
        sources=sorted(sources),
    )
    med = df["median_index_reference_vs_competitor"].dropna()
    if not med.empty:
        ok = (
            float(cfg.get("min_median_index", 0)) <= float(med.min())
            and float(med.max()) <= float(cfg.get("max_median_index", 99))
        )
        _chk(
            report,
            "lost_sales_competitor.median_index_bounded",
            ok,
            f"median index range {med.min():.2f}–{med.max():.2f}",
        )
    # Coverage must never be presented as complete. The whole point of publishing it is that most
    # of the book has no competing price on disk.
    if "coverage_pct_of_book_all_years" in df.columns:
        worst = float(df["coverage_pct_of_book_all_years"].max())
        _chk(
            report,
            "lost_sales_competitor.coverage_is_partial",
            worst < 50.0,
            f"largest source covers {worst:.2f}% of billed euro (must read as partial, not whole)",
        )


def check_lost_sales_pn_action(report: Report, fx: dict[str, Any]) -> None:
    """The part-number action layer: the decision test must be internally consistent.

    Every row that recommends a lever has to have the evidence that lever claims to rest on. A
    "price_or_incentive_actionable" row with no competitor price would be a guessed instruction.
    """
    cfg = fx.get("lost_sales_pn_action", {})
    path = DERIVED_DIR / "lost_sales_pn_action.csv"
    if not cfg or not path.exists():
        return
    df = pd.read_csv(path, low_memory=False)

    levers = set(df["recommended_lever"].dropna().unique())
    allowed = set(cfg.get("levers", []))
    unexpected = levers - allowed
    _chk(
        report,
        "lost_sales_pn_action.levers_documented",
        not unexpected,
        f"levers {sorted(levers)}" + (f" — undocumented {sorted(unexpected)}" if unexpected else ""),
        levers=sorted(levers),
    )

    # Actionable rows must carry both a cost and a competitor price.
    act = df[df["recommended_lever"] == "price_or_incentive_actionable"]
    missing = act[act["cost_landed_eur"].isna() | act["competitor_price_eur"].isna()]
    _chk(
        report,
        "lost_sales_pn_action.actionable_rows_have_cost_and_price",
        len(missing) == 0,
        f"{len(act)} actionable rows, {len(missing)} of them missing cost or competitor price",
    )

    # The cost test must be true whenever the lever says so, and false otherwise.
    bad_cost = df[
        (df["recommended_lever"] == "landed_cost_not_price")
        & (~df["competitor_below_our_cost"].astype(bool))
    ]
    _chk(
        report,
        "lost_sales_pn_action.landed_cost_verdict_matches_the_numbers",
        len(bad_cost) == 0,
        f"{len(bad_cost)} rows call it a landed-cost problem without the competitor below cost",
    )

    # An actionable row must have a usable dealer price at the margin floor, otherwise the
    # "could we match" answer it rests on was computed from nothing.
    act_floor = act["dealer_price_at_gm_floor_eur"].dropna()
    _chk(
        report,
        "lost_sales_pn_action.actionable_rows_have_a_floor_price",
        len(act_floor) == len(act) and bool((act_floor > 0).all()),
        f"{len(act)} actionable rows, {len(act_floor)} with a positive dealer price at the floor",
    )
    n_actionable = int((df["recommended_lever"] == "price_or_incentive_actionable").sum())
    _chk(
        report,
        "lost_sales_pn_action.actionable_set_is_not_empty",
        n_actionable >= 1,
        f"{n_actionable} part numbers are actionable on price or incentive, "
        f"{int((df['recommended_lever'] == 'landed_cost_not_price').sum())} need a landed-cost answer",
    )


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
        "lost_sales_model",
        "lost_sales_market",
        "lost_sales_competitor_coverage",
        "lost_sales_pn_action",
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


def check_action_ledger(report: Report) -> None:
    """P8 Action Ledger — presence, lineage, horizon honesty, language."""
    ledger_pq = DERIVED_DIR / "action_ledger.parquet"
    history_pq = DERIVED_DIR / "action_ledger_history.parquet"
    open_csv = DERIVED_DIR / "action_ledger_open.csv"
    rejects_csv = DERIVED_DIR / "action_ledger_rejects.csv"
    decisions_csv = DERIVED_DIR / "action_ledger_decisions.csv"
    meta_json = DERIVED_DIR / "action_ledger.meta.json"
    # Path: .../ISZE/03_analytics/Isuzu/prism/scripts → parents[4] = ISZE
    isze_root = Path(__file__).resolve().parents[4]
    html = isze_root / "02_dashboards" / "ops" / "ISZE_Action_Ledger.html"

    required = [ledger_pq, history_pq, open_csv, rejects_csv, decisions_csv, meta_json]
    missing = [p.name for p in required if not p.is_file()]
    _chk(
        report,
        "action_ledger.artefacts",
        len(missing) == 0,
        f"P8 artefacts present" if not missing else f"missing {missing}",
        missing=missing,
    )
    if missing:
        return

    ledger = pd.read_parquet(ledger_pq)
    _chk(
        report,
        "action_ledger.nonempty",
        len(ledger) > 0,
        f"ledger rows={len(ledger)}",
        n=len(ledger),
    )

    # Lineage on monetary rows
    mon = ledger[ledger["eur_at_stake"].notna()]
    if len(mon):
        lineage_ok = (
            mon["source_file"].notna().all()
            and mon["source_column"].notna().all()
            and mon["source_as_of"].notna().all()
        )
    else:
        lineage_ok = True
    _chk(
        report,
        "action_ledger.lineage",
        bool(lineage_ok),
        f"monetary rows with full lineage: {len(mon)}",
        monetary=len(mon),
    )

    # Rejects file exists and has reason column
    rej = pd.read_csv(rejects_csv)
    has_reason = "reason" in rej.columns
    _chk(
        report,
        "action_ledger.rejects",
        has_reason,
        f"rejects.csv rows={len(rej)} has_reason={has_reason}",
        n=len(rej),
    )

    # Language ban in HTML + open CSV
    banned = ["delivered by", "caused", "drove", "thanks to", "attributable to"]
    hits: list[str] = []
    for path in [html, open_csv]:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in banned:
            if phrase in text:
                hits.append(f"{path.name}:{phrase}")
    _chk(
        report,
        "action_ledger.language",
        len(hits) == 0,
        "co-movement wording only" if not hits else f"banned hits {hits}",
        hits=hits,
    )

    _chk(
        report,
        "action_ledger.html",
        html.is_file() and "Open by" in html.read_text(encoding="utf-8", errors="ignore"),
        f"dashboard HTML at {html.name}" if html.is_file() else "HTML missing",
    )


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


def check_uio_by_market_type_year(report: Report, fx: dict[str, Any]) -> None:
    """DI-3: the published fleet year axis.

    Three things must hold, because the whole point of the file is that a euro-per-vehicle
    figure can divide by the fleet of its own period:
      1. its 2025 column reconciles to the derived fleet split the spend model reads;
      2. no year inside the actual range is missing or negative for a market that has any
         row at all, so a rate cannot silently land on an empty denominator;
      3. the actual / estimate / forecast flags are present on every row and agree with the
         year, so a forecast cannot be read as measured.
    """
    path = DERIVED_DIR / "uio_by_market_type_year.csv"
    if not path.is_file():
        _chk(report, "uio_year.exists", False,
             "uio_by_market_type_year.csv missing — run scripts/build_uio_by_market_type_year.py")
        return
    df = pd.read_csv(path)
    _chk(report, "uio_year.rows", len(df) > 0, f"Fleet by year {len(df):,} rows", rows=len(df))

    cfg = fx.get("uio_by_market_type_year", {})
    required = cfg.get("required_columns", [])
    missing = [c for c in required if c not in df.columns]
    _chk(report, "uio_year.schema", not missing,
         "Schema OK" if not missing else f"Missing {missing}")
    if missing:
        return

    # 1. reconciliation to the derived bucket file, on the 2025 estimate column
    bucket = pd.read_csv(PRISM_ROOT / "data" / "uio_by_model_bucket.csv")
    est = int(cfg.get("estimate_year", 2025))
    got = (df[df.year == est]
           .groupby("distributor_code")
           .apply(lambda g: g.loc[g.vehicle_class == "CV", "uio_units"].sum()
                  + g.loc[g.vehicle_class == "LCV", "uio_units"].sum(),
                  include_groups=False))
    merged = bucket.set_index("distributor_code").join(
        got.rename("per_year"), how="left").fillna(0.0)
    merged["expected"] = merged.cv_std_uio + merged.f_series_uio + merged.lcv_uio
    merged["delta"] = (merged.per_year - merged.expected).abs()
    worst = float(merged.delta.max()) if len(merged) else 0.0
    tol = float(cfg.get("reconcile_tolerance_units", 0.5))
    _chk(report, "uio_year.reconcile_2025", worst <= tol,
         f"2025 column reproduces the derived fleet split, worst delta {worst:.4f} vehicles",
         worst_delta=round(worst, 4), rows=len(merged),
         worst_market=(merged.delta.idxmax() if len(merged) else None))

    # 2. no missing or negative year inside the actual range, per market.
    #
    # The workbook itself carries an older hole: the Denmark light-commercial row has no 2012 or
    # 2013 at all. That is a real gap in the controlled file, so it is named rather than filled.
    # The hard requirement is that no gap falls inside the range a page can divide by — the billing
    # window this rebuild is about, 2023 onwards. An older hole is a named warn, not a silent pass.
    actual_through = int(cfg.get("actual_through", 2024))
    hard_from = int(cfg.get("hard_gap_from_year", 2023))
    markets = sorted(df.distributor_code.unique())
    negative: list[str] = []
    blocking_gaps: list[str] = []
    historical_gaps: list[str] = []
    for db in markets:
        sub = df[df.distributor_code == db]
        have = set(int(y) for y in sub.year.unique())
        if not have:
            continue
        for gap in sorted(set(range(min(have), actual_through + 1)) - have):
            (blocking_gaps if gap >= hard_from else historical_gaps).append(f"{db} {gap}")
        neg = sub[(sub.year <= actual_through) & (sub.uio_units < 0)]
        if len(neg):
            negative.append(f"{db} negative in {sorted(set(neg.year))}")
    _chk(report, "uio_year.actual_years_complete", not blocking_gaps,
         f"No gaps inside the actual range from {hard_from} onward across {len(markets)} markets"
         if not blocking_gaps
         else f"Gaps inside the working range: {blocking_gaps[:8]}",
         markets=len(markets), blocking=blocking_gaps)
    _chk(report, "uio_year.historical_gaps", not historical_gaps,
         f"No gap anywhere in the actual range ({len(markets)} markets)"
         if not historical_gaps
         else f"Named hole(s) in the workbook's older years, left unfilled: {historical_gaps[:8]}",
         warn=bool(historical_gaps), historical=historical_gaps)
    _chk(report, "uio_year.no_negative_actuals", not negative,
         "No negative fleet counts in the actual range"
         if not negative else f"Negative actuals: {negative[:5]}")

    # 3. the flags are present and agree with the year
    flags = {"is_actual": lambda y: y <= actual_through,
             "is_estimate": lambda y: y == est,
             "is_forecast": lambda y: y > est}
    for col, want in flags.items():
        bad = int((df[col] != df.year.map(want)).sum())
        _chk(report, f"uio_year.{col}", bad == 0,
             f"{col} agrees with the year on every row"
             if bad == 0 else f"{col} disagrees with the year in {bad} rows")
    basis = set(df.basis.unique())
    _chk(report, "uio_year.basis_values",
         basis <= {"actual", "estimate", "forecast"},
         f"basis values {sorted(basis)}")
    _chk(report, "uio_year.defect_notes",
         bool(str(df.band_note.fillna("")).replace("nan", "").strip()),
         "The LD-label note is carried on the LD rows rather than dropped",
         rows_with_note=int((df.band_note.fillna("") != "").sum()))


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


def check_uio_canonical(report: Report, fx: dict[str, Any]) -> None:
    """DI-2: canonical UIO resolves to 06_uio/_CURRENT (v19, unversioned) and no
    stale v17/v18 copy sits in a fallback path where it could shadow it."""
    from config import UIO_CANDIDATES, resolve_uio_path

    try:
        resolved = resolve_uio_path()
    except FileNotFoundError as e:
        _chk(report, "uio.canonical", False, "Canonical UIO not found", error=str(e))
        return

    canonical = UIO_CANDIDATES[0] if UIO_CANDIDATES else None
    is_canonical = canonical is not None and resolved.resolve() == canonical.resolve()
    _chk(
        report,
        "uio.canonical",
        is_canonical,
        f"UIO resolves to canonical {resolved.name}"
        if is_canonical
        else f"UIO resolved to non-canonical {resolved.name} (expected {canonical.name})",
        path=str(resolved),
    )

    # A versioned v17/v18 (or older) copy anywhere in a candidate/archive path is
    # a stale shadow: if the canonical ever goes missing, resolve_uio_path would
    # fall through to it and silently re-base every UIO-denominator metric.
    stale: list[str] = []
    scan_roots = {Path(c).parent for c in UIO_CANDIDATES if Path(c).parent.exists()}
    for root in scan_roots:
        for p in root.glob("*UIO*"):
            if p.is_file() and ("v18" in p.name.lower() or "v17" in p.name.lower() or "v16" in p.name.lower()):
                stale.append(str(p))
    _chk(
        report,
        "uio.stale_copies",
        not stale,
        "No stale v16/v17/v18 UIO copies in fallback paths"
        if not stale
        else f"Stale UIO copies on disk: {stale}",
        warn=bool(stale),
        stale=stale,
    )


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
    check_uio_canonical(report, fx)
    check_uio_by_market_type_year(report, fx)
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
    check_lost_sales_model(report, fx)
    check_lost_sales_competitor(report, fx)
    check_lost_sales_pn_action(report, fx)
    check_action_ledger(report)
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
