#!/usr/bin/env python3
"""
Wallet Waterfall — one € identity per distributor x year.

    theoretical wallet (UIO model mix x GPS max-spend targets)
      = captured genuine + captured BVP + addressable uncaptured (ASSUMPTION split)
        + structural non-addressable + over-target capture

Every € of theoretical demand lands in exactly one bucket. GPS %, capture and
mix become views of this table and can no longer contradict each other.

Sources
-------
- theoretical wallet: gps_engine.calculate_model_weighted_gps (UIO v17 x
  prism/data/gps_model_targets.csv — official ISZE max wallet)
- captured split: sales_fact tagged via genuine_bvp_crossref (authoritative)
- addressable_pct: decision_model_assumptions.yaml (ASSUMPTION, flagged)

Output: Data/derived/wallet_waterfall.csv
Run from prism/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.data_prep import (  # noqa: E402
    EXCLUDED_CODES,
    get_distributor_metadata,
    load_distributor_mapping,
    load_uio_detail_from_excel,
)
from modules.gps_engine import calculate_model_weighted_gps  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_CSV = DERIVED_DIR / "wallet_waterfall.csv"
ASSUMPTIONS = PRISM_ROOT / "data" / "decision_model_assumptions.yaml"


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def main() -> int:
    cfg = yaml.safe_load(ASSUMPTIONS.read_text(encoding="utf-8"))["wallet_waterfall"]
    addressable_pct = float(cfg["addressable_pct"])
    years = [int(y) for y in cfg["years"]]

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df_meta = get_distributor_metadata(df_map)
    df_sales, src = load_prism_sales(df_map)
    print(f"waterfall: {len(df_sales):,} sales rows from {src}")

    df_sales = df_sales[~df_sales["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    if "line_kind" in df_sales.columns:
        df_sales = df_sales[df_sales["line_kind"] == "part"]

    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    bvp_pns = set(_norm(xref["bvp_pn"].dropna()))

    df_sales = df_sales.copy()
    df_sales["_pn"] = _norm(df_sales["part_number"])
    df_sales["is_bvp"] = df_sales["_pn"].isin(bvp_pns)

    df_uio_detail = load_uio_detail_from_excel(str(resolve_uio_path()))

    rows = []
    for year in years:
        summary, _ = calculate_model_weighted_gps(
            df_sales, df_uio_detail, df_meta, year=year, year_type="calendar"
        )
        sl = df_sales[df_sales["year"] == year]
        split = (
            sl.groupby(["distributor_code", "is_bvp"])["net_sales_value"]
            .sum()
            .unstack(fill_value=0.0)
            .rename(columns={False: "captured_genuine_eur", True: "captured_bvp_eur"})
        )
        for col in ("captured_genuine_eur", "captured_bvp_eur"):
            if col not in split.columns:
                split[col] = 0.0

        for _, r in summary.iterrows():
            dist = r["distributor_code"]
            wallet = r.get("target_wallet_eur")
            if pd.isna(wallet) or wallet <= 0:
                continue
            gen = float(split["captured_genuine_eur"].get(dist, 0.0))
            bvp = float(split["captured_bvp_eur"].get(dist, 0.0))
            captured = gen + bvp
            uncaptured = max(wallet - captured, 0.0)
            over = max(captured - wallet, 0.0)
            rows.append(
                {
                    "distributor_code": dist,
                    "country": r.get("country", ""),
                    "year": year,
                    "uio_units": r.get("uio_units"),
                    "uio_proxy": bool(r.get("uio_proxy", False)),
                    "theoretical_wallet_eur": round(float(wallet), 2),
                    "captured_genuine_eur": round(gen, 2),
                    "captured_bvp_eur": round(bvp, 2),
                    "captured_total_eur": round(captured, 2),
                    "uncaptured_eur": round(uncaptured, 2),
                    "addressable_uncaptured_eur": round(uncaptured * addressable_pct, 2),
                    "structural_nonaddressable_eur": round(
                        uncaptured * (1 - addressable_pct), 2
                    ),
                    "over_target_eur": round(over, 2),
                    "gps_pct": round(captured / wallet * 100, 1),
                    "bvp_share_of_captured_pct": round(
                        (bvp / captured * 100) if captured > 0 else 0.0, 1
                    ),
                    "assumption_note": (
                        f"addressable split = {addressable_pct:.0%} ASSUMPTION "
                        "(PMS convention); wallet = GPS max-spend targets (ceiling, "
                        "not forecast); targets flat across vehicle age"
                    ),
                }
            )

    out = pd.DataFrame(rows).sort_values(["year", "theoretical_wallet_eur"], ascending=[True, False])
    out.to_csv(OUT_CSV, index=False)

    net = out[out["year"] == max(years)]
    print(
        f"waterfall: {len(out)} rows -> {OUT_CSV.name} | CY{max(years)} network: "
        f"wallet EUR{net['theoretical_wallet_eur'].sum()/1e6:.1f}M, captured "
        f"EUR{net['captured_total_eur'].sum()/1e6:.1f}M, addressable gap "
        f"EUR{net['addressable_uncaptured_eur'].sum()/1e6:.1f}M (assumption-split)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
