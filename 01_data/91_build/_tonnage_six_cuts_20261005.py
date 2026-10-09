"""One-shot: six tonnage-band insight cuts after series_to_band fix. Internal only."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

BAND_LABEL = {
    "LCV_D-Max": "D-Max / LCV",
    "3.5t_N35": "3.5 t (N35)",
    "5.5t_N50_N55": "5.5 t (N55)",
    "7.5t_N50_N62_N75": "7.5 t (N75 class)",
    "F_series_MD_heavy": "F-series",
    "shared_across_bands": "Shared across N-series bands",
    "unresolved_series": "Unresolved series",
}


def main() -> None:
    pm = pd.read_csv(DER / "pms_tonnage_model.csv")
    ns = pd.read_csv(DER / "nseries_tonnage_evolution.csv")
    vb = pd.read_csv(DER / "vehicle_band_applicability.csv")
    km = pd.read_csv(DER / "warranty_cv_km_age_by_market.csv")
    n55 = pd.read_csv(ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "uio_n55_share.csv")

    vb["eur"] = pd.to_numeric(vb["eur"], errors="coerce").fillna(0)
    ex = vb[vb["band_status"] == "single_band"].copy()
    shared = vb[vb["band_status"] == "shared_across_bands"].copy()

    cat_rows = []
    for band, g in ex.groupby("exclusive_band"):
        cat_rows.append(
            {
                "band": band,
                "label": BAND_LABEL.get(band, band),
                "exclusive_pns": int(g["pn"].nunique()),
                "exclusive_eur_all_years": round(float(g["eur"].sum()), 0),
            }
        )
    cat_rows.append(
        {
            "band": "shared_across_bands",
            "label": "Shared across bands",
            "exclusive_pns": int(shared["pn"].nunique()),
            "exclusive_eur_all_years": round(float(shared["eur"].sum()), 0),
        }
    )
    cat_rows = sorted(cat_rows, key=lambda x: -x["exclusive_eur_all_years"])

    ns_ladder = vb[vb["n_series_bands"].fillna("") != ""]
    ns_ex = ns_ladder[ns_ladder["band_status"] == "single_band"]
    ns_sh = ns_ladder[ns_ladder["band_status"] == "shared_across_bands"]

    fy = ns[(ns["clock"] == "FY") & (ns["period"] == 2026)].copy()
    fy_mem = fy.groupby(["tonnage_band", "membership"], as_index=False).agg(
        billed_eur=("billed_eur", "sum"),
        units=("units", "sum"),
        markets=("distributor_code", "nunique"),
    )
    fy_sum = fy[
        fy["sums_to_n_series_total"].astype(str).str.lower().isin(["yes", "true", "1"])
    ]
    fy_net = {
        "period": "FY2026 (Apr 2025–Mar 2026)",
        "exclusive_eur": round(
            float(fy_sum.loc[fy_sum["membership"] == "single_band_only", "billed_eur"].sum()),
            0,
        ),
        "pooled_shared_eur": round(
            float(fy_sum.loc[fy_sum["membership"] == "pooled_all_bands", "billed_eur"].sum()),
            0,
        ),
        "unresolved_eur": round(
            float(fy_sum.loc[fy_sum["membership"] == "series_unresolved", "billed_eur"].sum()),
            0,
        ),
        "total_eur": round(float(fy_sum["billed_eur"].sum()), 0),
    }
    fy_net["exclusive_pct"] = (
        round(100 * fy_net["exclusive_eur"] / fy_net["total_eur"], 1) if fy_net["total_eur"] else 0
    )

    top_ex_cats = []
    for band in ["LCV_D-Max", "7.5t_N50_N62_N75", "3.5t_N35", "F_series_MD_heavy"]:
        sub = ex[ex["exclusive_band"] == band]
        if sub.empty:
            continue
        top = (
            sub.groupby("pms_category", as_index=False)
            .agg(eur=("eur", "sum"), pns=("pn", "nunique"))
            .sort_values("eur", ascending=False)
            .head(5)
        )
        for _, r in top.iterrows():
            top_ex_cats.append(
                {
                    "band": BAND_LABEL[band],
                    "family": r["pms_category"],
                    "eur": round(float(r["eur"]), 0),
                    "pns": int(r["pns"]),
                }
            )

    also = fy[fy["membership"] == "also_fits_band"].groupby("tonnage_band", as_index=False)[
        "billed_eur"
    ].sum()
    ex55 = ex[ex["exclusive_band"] == "5.5t_N50_N55"]
    ex55_detail = [
        {"pn": str(r["pn"]), "family": r["pms_category"], "eur": float(r["eur"])}
        for _, r in ex55.iterrows()
    ]

    # Fleet
    pm25 = pm[(pm["year"] == 2025) & (pm["lane"] == "PRISM network")].copy()
    fleet = pm25.groupby(["distributor_code", "band"], as_index=False)["uio_units"].first()
    fleet_band = fleet.groupby("band", as_index=False)["uio_units"].sum()
    fleet_band["uio_units"] = fleet_band["uio_units"].round(1)

    n_bands = ["3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"]
    fleet_n = fleet[fleet["band"].isin(n_bands)].copy()
    piv = fleet_n.pivot(index="distributor_code", columns="band", values="uio_units").fillna(0)
    piv["n_series_total"] = piv.sum(axis=1)
    piv = piv[piv["n_series_total"] > 0].sort_values("n_series_total", ascending=False)
    market_fleet = []
    for db, r in piv.iterrows():
        total = float(r["n_series_total"])
        market_fleet.append(
            {
                "market": db,
                "uio_3_5": round(float(r.get("3.5t_N35", 0)), 1),
                "uio_5_5": round(float(r.get("5.5t_N50_N55", 0)), 1),
                "uio_7_5": round(float(r.get("7.5t_N50_N62_N75", 0)), 1),
                "n_total": round(total, 1),
                "pct_3_5": round(100 * float(r.get("3.5t_N35", 0)) / total, 1),
                "pct_5_5": round(100 * float(r.get("5.5t_N50_N55", 0)) / total, 1),
                "pct_7_5": round(100 * float(r.get("7.5t_N50_N62_N75", 0)) / total, 1),
            }
        )

    # Exclusive €/truck
    ex_bill = (
        fy[fy["membership"] == "single_band_only"]
        .groupby(["distributor_code", "tonnage_band"], as_index=False)["billed_eur"]
        .sum()
    )
    ex_bill = ex_bill.merge(
        fleet.rename(columns={"band": "tonnage_band"}),
        on=["distributor_code", "tonnage_band"],
        how="left",
    )
    ex_bill["eur_per_truck"] = np.where(
        ex_bill["uio_units"] > 0, ex_bill["billed_eur"] / ex_bill["uio_units"], np.nan
    )
    excl_rate = []
    for _, r in ex_bill.sort_values("billed_eur", ascending=False).iterrows():
        if pd.isna(r["uio_units"]) or r["uio_units"] <= 0:
            continue
        excl_rate.append(
            {
                "market": r["distributor_code"],
                "band": BAND_LABEL.get(r["tonnage_band"], r["tonnage_band"]),
                "exclusive_eur": round(float(r["billed_eur"]), 0),
                "uio": round(float(r["uio_units"]), 1),
                "eur_per_truck": round(float(r["eur_per_truck"]), 1),
            }
        )

    ex_net = (
        fy[fy["membership"] == "single_band_only"]
        .groupby("tonnage_band", as_index=False)["billed_eur"]
        .sum()
    )
    ex_net = ex_net.merge(
        fleet_band.rename(columns={"band": "tonnage_band"}), on="tonnage_band", how="left"
    )
    ex_net["eur_per_truck"] = np.where(
        ex_net["uio_units"] > 0, ex_net["billed_eur"] / ex_net["uio_units"], np.nan
    )
    excl_rate_net = []
    for _, r in ex_net.iterrows():
        excl_rate_net.append(
            {
                "band": BAND_LABEL.get(r["tonnage_band"], r["tonnage_band"]),
                "exclusive_eur": round(float(r["billed_eur"]), 0),
                "uio_network": round(float(r["uio_units"]), 1)
                if pd.notna(r["uio_units"])
                else None,
                "eur_per_truck": round(float(r["eur_per_truck"]), 1)
                if pd.notna(r["eur_per_truck"])
                else None,
            }
        )

    # Opportunity
    gap = pm25.groupby(["band", "pms_category"], as_index=False).agg(
        gap_eur=("gap_eur_band_share", "sum")
    )
    gap_top = []
    for band in [
        "LCV_D-Max",
        "7.5t_N50_N62_N75",
        "3.5t_N35",
        "5.5t_N50_N55",
        "F_series_MD_heavy",
    ]:
        sub = gap[gap["band"] == band].nlargest(6, "gap_eur")
        for _, r in sub.iterrows():
            gap_top.append(
                {
                    "band": BAND_LABEL[band],
                    "family": r["pms_category"],
                    "gap_eur_band_share": round(float(r["gap_eur"]), 0),
                }
            )
    gap_band = gap.groupby("band", as_index=False)["gap_eur"].sum().sort_values(
        "gap_eur", ascending=False
    )

    # Portugal km sensitivity
    INTERVAL = {
        "3.5t_N35": 20000,
        "5.5t_N50_N55": 30000,
        "7.5t_N50_N62_N75": 40000,
        "LCV_D-Max": 20000,
        "F_series_MD_heavy": 40000,
    }
    KM_PT = {
        "3.5t_N35": 26584,
        "5.5t_N50_N55": None,
        "7.5t_N50_N62_N75": 40223,
        "LCV_D-Max": None,
        "F_series_MD_heavy": 17285,
    }
    pt = pm25[pm25["distributor_code"] == "PORTUGAL"].copy()
    families = [
        "oil_filter",
        "fuel_filter",
        "air_filter",
        "brake_pad",
        "brake_shoe",
        "clutch_disc",
        "clutch_kit",
    ]
    pt_fam = pt[pt["pms_category"].isin(families)]
    pt_rows = []
    for _, r in pt_fam.iterrows():
        band = r["band"]
        km_m = KM_PT.get(band)
        interv = INTERVAL.get(band)
        visits_meas = (km_m / interv) if (km_m and interv) else None
        scale = (
            (visits_meas / r["visits_per_year"])
            if (visits_meas and r["visits_per_year"])
            else None
        )
        exp_adj = r["expected_qty_per_year"] * scale if scale else None
        pt_rows.append(
            {
                "band": BAND_LABEL.get(band, band),
                "family": r["pms_category"],
                "uio": round(float(r["uio_units"]), 1),
                "visits_model": float(r["visits_per_year"]),
                "visits_measured": round(visits_meas, 2) if visits_meas else None,
                "scale": round(scale, 2) if scale else None,
                "expected_model": round(float(r["expected_qty_per_year"]), 1),
                "expected_km_adj": round(float(exp_adj), 1) if exp_adj is not None else None,
                "market_actual_qty": round(float(r["market_actual_qty"]), 0),
                "market_capture_pct": round(100 * float(r["market_capture_rate"]), 1)
                if pd.notna(r["market_capture_rate"])
                else None,
                "gap_eur_band_share": round(float(r["gap_eur_band_share"]), 0),
            }
        )

    km_rows = []
    for _, r in km.iterrows():
        km_rows.append(
            {
                "market": r["market"],
                "vins": int(r["vins_cv_claims"]) if pd.notna(r["vins_cv_claims"]) else 0,
                "km_all": int(r["km_yr_all_median"]) if pd.notna(r["km_yr_all_median"]) else None,
                "km_N35": int(r["km_yr_N35"]) if pd.notna(r["km_yr_N35"]) else None,
                "km_N75": int(r["km_yr_N75"]) if pd.notna(r["km_yr_N75"]) else None,
                "km_F": int(r["km_yr_F"]) if pd.notna(r["km_yr_F"]) else None,
            }
        )
    km_rows = sorted(km_rows, key=lambda x: -(x["vins"] or 0))[:15]

    n55_rows = [
        {
            "market": r["distributor_code"],
            "n55_share_pct": round(100 * float(r["n55_share"]), 1),
            "basis": r["basis"],
        }
        for _, r in n55.iterrows()
    ]

    pt_fleet = [m for m in market_fleet if m["market"] == "PORTUGAL"]
    pt_lcv = float(
        fleet.loc[
            (fleet["distributor_code"] == "PORTUGAL") & (fleet["band"] == "LCV_D-Max"),
            "uio_units",
        ].sum()
        or 0
    )
    pt_f = float(
        fleet.loc[
            (fleet["distributor_code"] == "PORTUGAL")
            & (fleet["band"] == "F_series_MD_heavy"),
            "uio_units",
        ].sum()
        or 0
    )

    # Highlight markets with real 5.5 slice
    hot_55 = [m for m in market_fleet if m["uio_5_5"] >= 5]

    payload = {
        "as_of": "2026-10-05",
        "sources": {
            "map": "series_to_band.csv (NMR=5.5t Europe; NKR=3.5t)",
            "applicability": "vehicle_band_applicability.csv",
            "evolution": "nseries_tonnage_evolution.csv FY2026",
            "pms": "pms_tonnage_model.csv CY2025 PRISM lane",
            "mileage": "warranty_cv_km_age_by_market.csv",
            "n55": "uio_n55_share.csv",
        },
        "catalogue": {
            "by_band": cat_rows,
            "n_series_exclusive_pns": int(ns_ex["pn"].nunique()),
            "n_series_shared_pns": int(ns_sh["pn"].nunique()),
            "n_series_exclusive_eur": round(float(ns_ex["eur"].sum()), 0),
            "n_series_shared_eur": round(float(ns_sh["eur"].sum()), 0),
            "fy2026_n_series_billed": fy_net,
            "fy2026_by_membership": [
                {
                    "band": BAND_LABEL.get(r["tonnage_band"], r["tonnage_band"]),
                    "membership": r["membership"],
                    "eur": round(float(r["billed_eur"]), 0),
                    "markets": int(r["markets"]),
                }
                for _, r in fy_mem.iterrows()
            ],
            "top_exclusive_families": top_ex_cats,
            "exclusive_5_5_detail": ex55_detail,
            "also_fits_fy2026": [
                {
                    "band": BAND_LABEL.get(r["tonnage_band"], r["tonnage_band"]),
                    "eur": round(float(r["billed_eur"]), 0),
                }
                for _, r in also.iterrows()
            ],
        },
        "fleet": {
            "network_by_band": [
                {
                    "band": BAND_LABEL.get(r["band"], r["band"]),
                    "uio": float(r["uio_units"]),
                }
                for _, r in fleet_band.sort_values("uio_units", ascending=False).iterrows()
            ],
            "n_series_by_market": market_fleet,
            "markets_with_5_5": hot_55,
            "n55_shares": n55_rows,
            "portugal": {
                "n_series": pt_fleet[0] if pt_fleet else None,
                "lcv_uio": round(pt_lcv, 1),
                "f_uio": round(pt_f, 1),
            },
            "uti_note": (
                "UTI n55_share=0; CV claims show no NLR/NKR/NMR — no 3.5 t or 5.5 t class"
            ),
        },
        "exclusive_rate": {
            "network": excl_rate_net,
            "by_market": excl_rate,
            "caveat": (
                "Only parts exclusive to one N-series band. Shared platform euro excluded. "
                "D-Max/F not in this N-series evolution cut."
            ),
        },
        "portugal_pms_km": {
            "measured_km_yr": KM_PT,
            "intervals_km": INTERVAL,
            "rows": [
                r
                for r in pt_rows
                if r["band"] in ["3.5 t (N35)", "7.5 t (N75 class)"]
                and r["family"]
                in ["oil_filter", "fuel_filter", "brake_pad", "clutch_disc"]
            ],
            "all_key_rows": pt_rows,
            "verdict": (
                "Measured Portugal distance raises N35 filter visits from 0.5 to ~1.33/yr "
                "and N75 from 0.5 to ~1.01/yr. Flat 0.5 visits understates expected demand, "
                "so capture looks better than the odometer supports."
            ),
        },
        "opportunity": {
            "gap_by_band_eur": [
                {
                    "band": BAND_LABEL.get(r["band"], r["band"]),
                    "gap_eur_band_share": round(float(r["gap_eur"]), 0),
                }
                for _, r in gap_band.iterrows()
            ],
            "top_families": gap_top,
            "caveat": (
                "gap_eur_band_share = market euro gap × band share of expected demand. "
                "Not band purchases."
            ),
        },
        "warranty_km": km_rows,
    }

    outp = DER / "tonnage_bands_six_cuts_20261005.json"
    outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", outp)
    print("FY net", fy_net)
    print("fleet", payload["fleet"]["network_by_band"])
    print("excl net", excl_rate_net)
    print("5.5 markets", hot_55)
    print("gap", payload["opportunity"]["gap_by_band_eur"])


if __name__ == "__main__":
    main()
