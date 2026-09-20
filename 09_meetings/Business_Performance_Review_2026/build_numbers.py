"""BPR 2.0 — the sales / fill-rate backbone, computed directly from source.

Writes _bpr_numbers.json next to this file. Every value carries its source.
Read-only on all sources.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PLAN = ROOT / "01_data" / "planning"

LABELS = {
    "ITUK": "ITUK", "IUK": "IUK", "UMI": "UMI (Israel)", "UTI": "UTI (Israel)",
    "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal",
    "SWEDEN": "Sweden", "NORWAY": "Norway", "IRELAND": "Ireland",
    "GREECE": "Greece", "CYPRUS": "Cyprus", "HUNGARY": "Hungary",
    "FINLAND": "Finland", "ROMANIA": "Romania", "MALTA": "Malta",
    "ICELAND": "Iceland", "DENMARK": "Denmark",
}


def fiscal(d):
    """ISZE fiscal year label = the calendar year the FY ENDS in.

    FY2026 = April 2025 to March 2026, so month >= 4 belongs to year + 1.
    (An earlier version labelled by the April year, which put the whole of
    FY2026 into the wrong bucket.)
    """
    return np.where(d.dt.month >= 4, d.dt.year + 1, d.dt.year)


def main():
    out: dict = {"sources": {}}

    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["billing_date", "sold_to_sap", "sold_to", "net_sales_value",
                 "billed_qty", "part_number", "saty"],
    )
    sf["bd"] = pd.to_datetime(sf.billing_date)
    sf["fy"] = fiscal(sf.bd)
    out["sources"]["sales_net"] = "sales_fact.parquet (billing_date, net_sales_value, saty)"
    out["sf_max_date"] = str(sf.bd.max().date())
    out["sf_rows"] = int(len(sf))

    # distributor attribution: sold_to_sap first; the payer-only codes are the
    # ones the dimension maps by sold_to; keep a fallback on sold_to.
    dim = pd.read_csv(DER / "distributor_dimension.csv")
    cmap: dict = {}
    for col in ("sold_to_sap", "payer_code"):
        for _, r in dim.iterrows():
            dc = r.distributor_code
            if pd.isna(dc):
                continue
            key = r[col]
            if pd.isna(key):
                continue
            k = str(int(key))
            if k not in cmap:
                cmap[k] = str(dc)
    sf["dist"] = sf.sold_to_sap.astype("Int64").astype(str).map(cmap)
    # sold_to in this parquet is the consumer key on the line; only use it when
    # the SAP key did not resolve, and only if the dimension knows that code.
    if "sold_to" in sf.columns:
        fb = sf.sold_to.astype(str).str.strip().map(cmap)
        sf["dist"] = sf["dist"].fillna(fb)
    sf["dist"] = sf["dist"].where(sf["dist"].isin(LABELS))
    attributed = sf[sf["dist"].notna()]
    out["attributed_rows"] = int(len(attributed))
    out["unattributed_rows"] = int(len(sf) - len(attributed))

    for fy, key in [(2026, "fy2026"), (2027, "fy2027")]:
        sub = attributed[attributed.fy == fy]
        by = sub.groupby("dist")["net_sales_value"].sum().sort_values(ascending=False)
        out[key] = {
            "total_eur": float(sub.net_sales_value.sum()),
            "by_db": {LABELS.get(k, k): float(v) for k, v in by.items()},
            "months_present": sorted(sub.bd.dt.strftime("%Y-%m").unique().tolist()),
        }
    # FY2027 quarters
    q = attributed[attributed.fy == 2027].copy()
    q["q"] = np.where(q.bd.dt.month >= 4, q.bd.dt.month - 3, q.bd.dt.month - 3)
    q["qtr"] = np.select(
        [q.bd.dt.month.isin([4, 5, 6]), q.bd.dt.month.isin([7, 8, 9]),
         q.bd.dt.month.isin([10, 11, 12]), q.bd.dt.month.isin([1, 2, 3])],
        ["Q1", "Q2", "Q3", "Q4"],
        default="?",
    )
    out["fy2027_by_quarter"] = {
        k: float(v) for k, v in
        q.groupby("qtr")["net_sales_value"].sum().items()
    }
    out["fy2027_q2_months"] = sorted(
        q[q.qtr == "Q2"].bd.dt.strftime("%Y-%m").unique().tolist()
    )

    # GPS spend per truck, CY2025
    gps = pd.read_csv(DER / "gps_spu_by_distributor.csv")
    g25 = gps[gps.year == 2025]
    out["gps_cy2025"] = {
        "by_db": {
            LABELS.get(str(r.distributor_code), str(r.distributor_code)): {
                "spend_per_unit": float(r.spend_per_unit_eur),
                "uio": float(r.uio_units),
                "billed_eur": float(r.total_sales_eur),
            }
            for r in g25.itertuples()
        },
        "network_spend_per_unit": float(
            g25.total_sales_eur.sum() / g25.uio_units.sum()),
        "network_median_spend_per_unit": float(g25.spend_per_unit_eur.median()),
        "network_billed_eur": float(g25.total_sales_eur.sum()),
        "network_uio": float(g25.uio_units.sum()),
    }

    # wallet / ceiling CY2025
    w = pd.read_csv(DER / "wallet_waterfall.csv")
    w25 = w[w.year == 2025]
    out["ceiling_cy2025"] = {
        "theoretical_eur": float(w25.theoretical_wallet_eur.sum()),
        "captured_total_eur": float(w25.captured_total_eur.sum()),
        "uncaptured_eur": float(w25.uncaptured_eur.sum()),
        "addressable_uncaptured_eur": float(w25.addressable_uncaptured_eur.sum()),
        "capture_pct": float(w25.captured_total_eur.sum()
                             / w25.theoretical_wallet_eur.sum() * 100),
    }

    # PMS capture network + top gaps
    cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
    c25 = cap[(cap.year == 2025) & (cap.line_type == "total")]
    out["pms_cy2025"] = {
        "network_capture_pct": float(c25.actual_qty.sum() / c25.expected_qty.sum() * 100),
        "network_gap_eur": float(c25.revenue_gap_eur.sum()),
        "by_category": {
            str(r.category_label): {
                "gap_eur": float(r.revenue_gap_eur),
                "capture_pct": float(r.capture_rate * 100),
                "billed_eur": float(r.actual_rev_eur),
            }
            for r in (
                c25.groupby(["pms_category", "category_label"], as_index=False)
                .agg(revenue_gap_eur=("revenue_gap_eur", "sum"),
                     actual_qty=("actual_qty", "sum"),
                     expected_qty=("expected_qty", "sum"),
                     actual_rev_eur=("actual_rev_eur", "sum"))
                .assign(capture_rate=lambda d: d.actual_qty / d.expected_qty)
                .sort_values("revenue_gap_eur", ascending=False)
            ).itertuples()
        },
    }

    # warranty by DB
    warr = pd.read_csv(DER / "gps_spu_by_distributor.csv")[
        ["year", "distributor_code", "warranty_parts_eur", "total_sales_eur"]]
    w25d = warr[warr.year == 2025].copy()
    out["warranty_cy2025"] = {
        "network_eur": float(w25d.warranty_parts_eur.sum()),
        "network_pct_of_billed": float(
            w25d.warranty_parts_eur.sum() / w25d.total_sales_eur.sum() * 100),
        "by_db": {
            LABELS.get(str(r.distributor_code), str(r.distributor_code)): float(r.warranty_parts_eur)
            for r in w25d.itertuples() if pd.notna(r.warranty_parts_eur)
        },
    }

    # order-type / urgency mix from the saty code on the billing line
    def urgency(df):
        m = df[df.saty.notna() & (df.saty.astype(str).str.strip() != "")]
        if not len(m):
            return None
        tot = float(m.net_sales_value.sum())
        stock = m[m.saty.isin(["SOR", "PRD"])].net_sales_value.sum()
        urgent = m[m.saty.isin(["VOR", "RUSH", "SVOR"])].net_sales_value.sum()
        return {
            "matched_eur": tot,
            "matched_pct_of_all": float(tot / df.net_sales_value.sum() * 100)
            if df.net_sales_value.sum() else None,
            "stock_pct": float(stock / tot * 100),
            "urgent_pct": float(urgent / tot * 100),
            "codes": {c: int((m.saty == c).sum()) for c in
                      sorted(m.saty.astype(str).unique())[:12]},
        }

    out["urgency_fy2026"] = urgency(attributed[attributed.fy == 2026])
    out["urgency_fy2027_q1"] = urgency(
        attributed[(attributed.fy == 2027) & (attributed.bd.dt.month <= 6)]
    )
    out["urgency_by_db_fy2026"] = {
        LABELS.get(k, k): urgency(g)
        for k, g in attributed[attributed.fy == 2026].groupby("dist")
    }

    # fill rate is read in build_kpi_numbers.py from the same workbook; a second
    # parse here proved unreliable and is deliberately not repeated.

    # warranty on the canonical fiscal basis as well
    wfy = DER / "warranty_by_db_FY_canonical.csv"
    if wfy.exists():
        wdf = pd.read_csv(wfy)
        out["warranty_fy_source"] = str(wfy)
        out["warranty_fy_columns"] = list(wdf.columns)[:10]

    # FY2027 target (BP reviewed)
    bpp = ROOT / "01_data" / "91_build" / "bp_fy27_reviewed.json"
    if bpp.exists():
        try:
            bpj = json.loads(bpp.read_text(encoding="utf-8"))
            out["bp_fy27_raw_keys"] = list(bpj.keys())[:20]
        except Exception as exc:  # noqa: BLE001
            out["bp_fy27_error"] = str(exc)

    # KPI Master File — sheet inventory
    kpi_path = PLAN / "KPI Master File august 2026.xlsx"
    out["sources"]["kpi_master"] = str(kpi_path)
    if kpi_path.exists():
        try:
            xl = pd.ExcelFile(kpi_path)
            out["kpi_sheets"] = xl.sheet_names
            ph = pd.read_excel(kpi_path, sheet_name="Parts Handling", header=None)
            out["kpi_parts_handling_shape"] = list(ph.shape)
            # find the fill-rate block and the stock block
            flat = ph.astype(str)
            hits = {}
            for i in range(len(flat)):
                rowtxt = " | ".join(flat.iloc[i].tolist()[:6])
                for key in ("Fill Rate", "Days of Parts in Stock", "Back Order"):
                    if key.lower() in rowtxt.lower() and key not in hits:
                        hits[key] = i
            out["kpi_block_rows"] = hits
        except Exception as exc:  # noqa: BLE001
            out["kpi_error"] = f"{type(exc).__name__}: {exc}"

    (HERE / "_bpr_numbers.json").write_text(
        json.dumps(out, indent=1, default=float), encoding="utf-8")

    print("sales max date", out["sf_max_date"], "rows", out["sf_rows"])
    print(f"FY2026 total  EUR {out['fy2026']['total_eur']:,.0f}  "
          f"({len(out['fy2026']['by_db'])} DBs)")
    print(f"FY2027 total  EUR {out['fy2027']['total_eur']:,.0f}")
    print("FY2027 months", out["fy2027_q2_months"])
    print("FY2027 quarters", out["fy2027_by_quarter"])
    print(f"GPS CY2025 network EUR {out['gps_cy2025']['network_spend_per_unit']:,.0f}/truck "
          f"median {out['gps_cy2025']['network_median_spend_per_unit']:,.0f}")
    print(f"PMS CY2025 network capture {out['pms_cy2025']['network_capture_pct']:.1f}% "
          f"gap EUR {out['pms_cy2025']['network_gap_eur']:,.0f}")
    print(f"ceiling CY2025 capture {out['ceiling_cy2025']['capture_pct']:.1f}%")
    print(f"warranty CY2025 EUR {out['warranty_cy2025']['network_eur']:,.0f} "
          f"({out['warranty_cy2025']['network_pct_of_billed']:.1f}% of billed)")
    print("kpi sheets", out.get("kpi_sheets"))
    print("kpi blocks", out.get("kpi_block_rows"), out.get("kpi_error", ""))


if __name__ == "__main__":
    main()
