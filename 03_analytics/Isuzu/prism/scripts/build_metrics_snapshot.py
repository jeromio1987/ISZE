#!/usr/bin/env python3
"""
Metrics snapshot — metrics-as-code for ISZE headline numbers.

Computes every FACTS.md-grade headline figure directly from the verified
derived layer and writes ONE machine-readable snapshot with source + as-of
per metric. Decks, memos and FACTS.md reconcile to this file; nothing is
hand-transcribed.

Output: Data/derived/metrics_snapshot.json
Run from prism/ AFTER the pipeline (and ideally the decision-model builders).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    PMS_CAPTURE_BY_DB_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_JSON = DERIVED_DIR / "metrics_snapshot.json"


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def main() -> int:
    metrics: dict[str, dict] = {}

    def put(key: str, value, source: str, note: str = "") -> None:
        metrics[key] = {"value": value, "source": source, "note": note}

    # --- sales_fact base -----------------------------------------------------
    raw = pd.read_parquet(SALES_FACT_PARQUET)
    put("sales_fact.rows", int(len(raw)), SALES_FACT_PARQUET.name)
    put("sales_fact.raw_total_eur", round(float(raw["net_sales_value"].sum()), 0),
        SALES_FACT_PARQUET.name, "includes internal/excluded codes")

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df, _ = load_prism_sales(df_map)
    df = df[~df["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    # Flag H (2026-07-03): exclude SaTy CR/RE credit-note/return lines — see
    # sales_loader._finish_sales_frame for rationale.
    if "is_credit_note" in df.columns:
        df = df[~df["is_credit_note"]]
    put("sales.gps_facing_all_lines_eur", round(float(df["net_sales_value"].sum()), 0),
        "load_prism_sales after distributor exclusion, ex-credit-notes/returns")
    parts = df[df["line_kind"] == "part"] if "line_kind" in df.columns else df
    put("sales.parts_base_eur", round(float(parts["net_sales_value"].sum()), 0),
        "GPS-facing, parts only (line_kind=part), ex-credit-notes/returns", "the parts base")

    # --- parts base bridge ---------------------------------------------------
    # The parts base moves for two independent reasons: a new billing period, and
    # any change to the exclusion rules. Recomputing 2026-09-17 showed the second
    # one silently: NON_PARTS rows leaked EUR 180,715 into the base after the
    # 2026-08-25 snapshot. Emit both cut-offs so a period movement can never be
    # mistaken for a method movement again. See FACTS.md section 4.
    if "billing_date" in parts.columns and parts["billing_date"].notna().any():
        dmax = pd.Timestamp(parts["billing_date"].max())
        # prior calendar quarter end (starting January) to the quarter holding dmax
        q_idx = (dmax.month - 1) // 3
        if q_idx == 0:
            p_q_end_month, p_q_end_year = 12, dmax.year - 1
        else:
            p_q_end_month, p_q_end_year = q_idx * 3, dmax.year
        prev_q_end = (pd.Timestamp(p_q_end_year, p_q_end_month, 1)
                      + pd.offsets.MonthEnd(0))
        prior = parts[parts["billing_date"] <= prev_q_end]
        put("sales.parts_base_data_through",
            dmax.strftime("%Y-%m-%d"),
            "max billing_date in sales_fact", "billing horizon behind the parts base")
        put("sales.parts_base_through_prior_quarter_eur",
            round(float(prior["net_sales_value"].sum()), 0),
            "GPS-facing, parts only, cut at the prior quarter end",
            f"same method, data through {prev_q_end.strftime('%Y-%m-%d')} — "
            "bridge companion to sales.parts_base_eur")

    # --- ITUK oil-filter capture (dispute anchor) ----------------------------
    cap = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    m = cap[(cap["distributor_code"] == "ITUK") & (cap["pms_category"] == "oil_filter")]
    for _, r in m.iterrows():
        k = f"ituk.oil_filter.{int(r['year'])}.{r['line_type']}"
        put(f"{k}.capture_uncapped_pct", round(float(r["capture_rate"]) * 100, 1),
            PMS_CAPTURE_BY_DB_CSV.name)
        put(f"{k}.actual_qty", int(r["actual_qty"]), PMS_CAPTURE_BY_DB_CSV.name)
        put(f"{k}.revenue_eur", round(float(r["actual_rev_eur"]), 0), PMS_CAPTURE_BY_DB_CSV.name)
    if not m.empty:
        put("ituk.oil_filter.uio_units", int(m["uio_units"].iloc[0]),
            PMS_CAPTURE_BY_DB_CSV.name, "model_bucket_split: cv_std 22,190.9 + f_series 877.0")
        put("ituk.oil_filter.expected_qty", round(float(m["expected_qty"].iloc[0]), 1),
            PMS_CAPTURE_BY_DB_CSV.name,
            "23068 bucket UIO; cv_std at 0.5 x (1 + N35 share) svc/yr (N35 on the 20,000 km interval), F-series 0.667; 100% addressable")

    # --- overall genuine/BVP mix CY2025 (crossref-authoritative) -------------
    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    bvp_pns = set(_norm(xref["bvp_pn"].dropna()))
    p25 = parts[parts["year"] == 2025].copy()
    p25["is_bvp"] = _norm(p25["part_number"]).isin(bvp_pns)
    for dist in ("ITUK", "UTI"):
        d = p25[p25["distributor_code"] == dist]
        tot = float(d["net_sales_value"].sum())
        if tot > 0:
            bvp_eur = float(d.loc[d["is_bvp"], "net_sales_value"].sum())
            put(f"mix.{dist}.genuine_share_eur_pct_2025",
                round((1 - bvp_eur / tot) * 100, 1),
                "sales_fact + genuine_bvp_crossref", "overall parts mix, EUR basis")

    # --- decision-model layer headlines ---------------------------------------
    wf_path = DERIVED_DIR / "wallet_waterfall.csv"
    if wf_path.exists():
        wf = pd.read_csv(wf_path)
        w25 = wf[wf["year"] == 2025]
        put("waterfall.network.wallet_eur_2025", round(float(w25["theoretical_wallet_eur"].sum()), 0),
            wf_path.name, "GPS max-spend ceiling")
        put("waterfall.network.captured_eur_2025", round(float(w25["captured_total_eur"].sum()), 0),
            wf_path.name)
        put("waterfall.network.gps_pct_2025",
            round(float(w25["captured_total_eur"].sum() / w25["theoretical_wallet_eur"].sum() * 100), 1),
            wf_path.name)
    rw_path = DERIVED_DIR / "revenue_runway.csv"
    if rw_path.exists():
        rw = pd.read_csv(rw_path)
        net = rw.groupby("year")["wallet_eur"].sum()
        put("runway.network.wallet_eur_2030", round(float(net.get(2030, float("nan"))), 0),
            rw_path.name, "age-flat wallet, UIO v17 projection")
    da_path = DERIVED_DIR / "defection_alerts.csv"
    if da_path.exists():
        da = pd.read_csv(da_path)
        put("defection.active_alerts", int(da["alert"].sum()), da_path.name,
            f"data horizon {da['data_horizon'].iloc[0] if len(da) else 'n/a'}")
    dl_path = DERIVED_DIR / "dealer_leakage_ituk.csv"
    if dl_path.exists():
        dl = pd.read_csv(dl_path)
        put("leakage.ituk.benchmark_gap_eur", round(float(dl["gap_eur"].sum()), 0),
            dl_path.name, "relative benchmark vs network-median dealer mix")

    # --- verification status ---------------------------------------------------
    vr = DERIVED_DIR / "_verification_report.json"
    if vr.exists():
        rep = json.loads(vr.read_text(encoding="utf-8"))
        checks = rep.get("checks", rep if isinstance(rep, list) else [])
        statuses = [c.get("status") for c in checks] if checks else []
        put("verify.pass", statuses.count("pass"), vr.name)
        put("verify.fail", statuses.count("fail"), vr.name)
        put("verify.generated", rep.get("generated_at", "unknown") if isinstance(rep, dict) else "unknown", vr.name)

    snapshot = {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/build_metrics_snapshot.py",
        "metrics": metrics,
    }
    OUT_JSON.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"snapshot: {len(metrics)} metrics -> {OUT_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
