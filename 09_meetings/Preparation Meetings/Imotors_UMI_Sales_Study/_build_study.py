# -*- coding: utf-8 -*-
"""Full ORDER/SALES hierarchy study — Imotors (PORTUGAL) + UMI, FY2024–FY2025 (+ CY H1 2026 from PBI notes)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PARQUET = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
SAP_MAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "sap_sold_to_mapping.csv"
GPS = ROOT / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
PMS = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived" / "pms_summary_by_db.csv"
PMS_CAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived" / "pms_capture_by_db_year.csv"
MIX = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived" / "db_parts_mix_classification.csv"

TARGETS = {
    "IMOTORS": {"code": "PORTUGAL", "label": "I Motors (Portugal)", "sap_codes": []},
    "UMI": {"code": "UMI", "label": "UMI (Israel LCV)", "sap_codes": [1797]},
}


def _money(x: float) -> float:
    return round(float(x), 2)


def load_sales() -> pd.DataFrame:
    sap = pd.read_csv(SAP_MAP)
    sap = sap.rename(columns={"sap_sold_to_pt": "sold_to_sap"})
    sap["sold_to_sap"] = pd.to_numeric(sap["sold_to_sap"], errors="coerce")

    for k, meta in TARGETS.items():
        hit = sap.loc[sap["distributor_code"].astype(str).str.upper() == meta["code"]]
        TARGETS[k]["sap_codes"] = sorted({int(x) for x in hit["sold_to_sap"].dropna().tolist()})

    dataset = ds.dataset(PARQUET)
    keep = [
        "billing_date",
        "sold_to_sap",
        "part_number",
        "description",
        "billed_qty",
        "net_sales_value",
        "saty",
        "year",
        "material",
        "fig_key",
    ]
    df = dataset.to_table(columns=keep).to_pandas()
    df["billing_date"] = pd.to_datetime(df["billing_date"])
    df["month"] = df["billing_date"].dt.month
    df["year"] = df["billing_date"].dt.year
    df["fiscal_year"] = df.apply(
        lambda r: int(r["year"]) if int(r["month"]) >= 4 else int(r["year"]) - 1, axis=1
    )
    df["sold_to_sap"] = pd.to_numeric(df["sold_to_sap"], errors="coerce")
    df = df.merge(sap[["sold_to_sap", "distributor_code"]], on="sold_to_sap", how="left")
    df["part_number"] = df["part_number"].astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str)
    df["saty"] = df["saty"].fillna("(blank)").astype(str)
    df["fig_key"] = df["fig_key"].fillna("(none)").astype(str)
    return df


def slice_db(df: pd.DataFrame, code: str) -> pd.DataFrame:
    return df[df["distributor_code"] == code].copy()


def fy_totals(g: pd.DataFrame) -> dict:
    out = {}
    for fy, sub in g.groupby("fiscal_year"):
        out[str(int(fy))] = {
            "sales_eur": _money(sub["net_sales_value"].sum()),
            "qty": _money(sub["billed_qty"].sum()),
            "lines": int(len(sub)),
            "distinct_pn": int(sub["part_number"].nunique()),
            "months": int(sub["billing_date"].dt.to_period("M").nunique()),
            "date_min": str(sub["billing_date"].min().date()),
            "date_max": str(sub["billing_date"].max().date()),
        }
    return out


def monthly(g: pd.DataFrame, fys: list[int]) -> list[dict]:
    sub = g[g["fiscal_year"].isin(fys)].copy()
    sub["ym"] = sub["billing_date"].dt.to_period("M").astype(str)
    rows = (
        sub.groupby(["fiscal_year", "ym"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values("ym")
    )
    return [
        {
            "fiscal_year": int(r.fiscal_year),
            "ym": r.ym,
            "sales_eur": _money(r.sales_eur),
            "qty": _money(r.qty),
            "lines": int(r.lines),
        }
        for r in rows.itertuples()
    ]


def by_saty(g: pd.DataFrame, fys: list[int]) -> list[dict]:
    sub = g[g["fiscal_year"].isin(fys)]
    rows = (
        sub.groupby(["fiscal_year", "saty"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values(["fiscal_year", "sales_eur"], ascending=[True, False])
    )
    out = []
    for fy, chunk in rows.groupby("fiscal_year"):
        tot = chunk["sales_eur"].sum() or 1
        for r in chunk.itertuples():
            out.append(
                {
                    "fiscal_year": int(fy),
                    "saty": r.saty,
                    "sales_eur": _money(r.sales_eur),
                    "share_pct": round(100 * float(r.sales_eur) / float(tot), 2),
                    "qty": _money(r.qty),
                    "lines": int(r.lines),
                }
            )
    return out


def by_fig(g: pd.DataFrame, fys: list[int], top_n: int = 25) -> list[dict]:
    sub = g[g["fiscal_year"].isin(fys)]
    rows = (
        sub.groupby(["fiscal_year", "fig_key"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values(["fiscal_year", "sales_eur"], ascending=[True, False])
    )
    out = []
    for fy, chunk in rows.groupby("fiscal_year"):
        tot = chunk["sales_eur"].sum() or 1
        for r in chunk.head(top_n).itertuples():
            out.append(
                {
                    "fiscal_year": int(fy),
                    "fig_key": r.fig_key,
                    "sales_eur": _money(r.sales_eur),
                    "share_pct": round(100 * float(r.sales_eur) / float(tot), 2),
                    "qty": _money(r.qty),
                    "lines": int(r.lines),
                }
            )
    return out


def top_pn(g: pd.DataFrame, fys: list[int], top_n: int = 40) -> list[dict]:
    sub = g[g["fiscal_year"].isin(fys)]
    # description mode
    desc = (
        sub.groupby("part_number")["description"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "")
        .to_dict()
    )
    rows = (
        sub.groupby(["fiscal_year", "part_number"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values(["fiscal_year", "sales_eur"], ascending=[True, False])
    )
    out = []
    for fy, chunk in rows.groupby("fiscal_year"):
        tot = chunk["sales_eur"].sum() or 1
        for i, r in enumerate(chunk.head(top_n).itertuples(), 1):
            out.append(
                {
                    "fiscal_year": int(fy),
                    "rank": i,
                    "part_number": r.part_number,
                    "description": str(desc.get(r.part_number, ""))[:80],
                    "sales_eur": _money(r.sales_eur),
                    "share_pct": round(100 * float(r.sales_eur) / float(tot), 2),
                    "qty": _money(r.qty),
                    "lines": int(r.lines),
                }
            )
    return out


def pn_movers(g: pd.DataFrame, fy_a: int, fy_b: int, top_n: int = 20) -> dict:
    """Biggest € up / down between two fiscal years at PN level."""
    a = g[g["fiscal_year"] == fy_a].groupby("part_number")["net_sales_value"].sum()
    b = g[g["fiscal_year"] == fy_b].groupby("part_number")["net_sales_value"].sum()
    both = pd.DataFrame({"fy_a": a, "fy_b": b}).fillna(0.0)
    both["delta"] = both["fy_b"] - both["fy_a"]
    desc = (
        g.groupby("part_number")["description"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "")
        .to_dict()
    )

    def pack(series: pd.Series) -> list[dict]:
        out = []
        for pn, delta in series.items():
            out.append(
                {
                    "part_number": pn,
                    "description": str(desc.get(pn, ""))[:80],
                    "fy_a_eur": _money(both.loc[pn, "fy_a"]),
                    "fy_b_eur": _money(both.loc[pn, "fy_b"]),
                    "delta_eur": _money(delta),
                }
            )
        return out

    gainers = pack(both["delta"].sort_values(ascending=False).head(top_n))
    losers = pack(both["delta"].sort_values(ascending=True).head(top_n))
    return {"fy_from": fy_a, "fy_to": fy_b, "gainers": gainers, "losers": losers}


def concentration(g: pd.DataFrame, fy: int) -> dict:
    sub = g[g["fiscal_year"] == fy]
    by_pn = sub.groupby("part_number")["net_sales_value"].sum().sort_values(ascending=False)
    tot = float(by_pn.sum()) or 1.0
    cum = by_pn.cumsum() / tot
    return {
        "fiscal_year": fy,
        "top10_share_pct": round(100 * float(by_pn.head(10).sum()) / tot, 2),
        "top25_share_pct": round(100 * float(by_pn.head(25).sum()) / tot, 2),
        "top50_share_pct": round(100 * float(by_pn.head(50).sum()) / tot, 2),
        "pn_for_80pct": int((cum <= 0.80).sum() + 1),
        "distinct_pn": int(by_pn.shape[0]),
    }


def build_db(df: pd.DataFrame, key: str) -> dict:
    meta = TARGETS[key]
    g = slice_db(df, meta["code"])
    fys = [2024, 2025]
    # also calendar 2025 full + 2026 YTD if present
    cy = {}
    for y in [2024, 2025, 2026]:
        sub = g[g["year"] == y]
        if len(sub):
            cy[str(y)] = {
                "sales_eur": _money(sub["net_sales_value"].sum()),
                "qty": _money(sub["billed_qty"].sum()),
                "lines": int(len(sub)),
                "date_min": str(sub["billing_date"].min().date()),
                "date_max": str(sub["billing_date"].max().date()),
            }

    return {
        "key": key,
        "label": meta["label"],
        "distributor_code": meta["code"],
        "sap_sold_to": meta["sap_codes"],
        "billing_span": {
            "min": str(g["billing_date"].min().date()) if len(g) else None,
            "max": str(g["billing_date"].max().date()) if len(g) else None,
            "rows": int(len(g)),
        },
        "fy_totals": fy_totals(g),
        "cy_totals": cy,
        "monthly": monthly(g, fys),
        "by_saty": by_saty(g, fys),
        "by_fig_key_top25": by_fig(g, fys, 25),
        "top_pn": top_pn(g, fys, 40),
        "pn_movers_fy24_to_fy25": pn_movers(g, 2024, 2025, 20),
        "concentration": {
            "FY2024": concentration(g, 2024),
            "FY2025": concentration(g, 2025),
        },
    }


def enrich_prism(payload: dict) -> None:
    gps = pd.read_csv(GPS)
    pms = pd.read_csv(PMS)
    mix = pd.read_csv(MIX)
    cap = pd.read_csv(PMS_CAP)
    for db in payload["distributors"]:
        code = db["distributor_code"]
        db["gps"] = []
        for _, r in gps[(gps["distributor_code"] == code) & (gps["year"].isin([2024, 2025, 2026]))].iterrows():
            db["gps"].append(
                {
                    "year": int(r["year"]),
                    "sales_eur": _money(r["total_sales_eur"]),
                    "uio": float(r["uio_units"]),
                    "spu": _money(r.get("spend_per_unit_eur") or 0),
                    "gps_capture_vs_max": None
                    if pd.isna(r.get("gps_capture_vs_max"))
                    else round(float(r["gps_capture_vs_max"]), 4),
                    "traffic_light": r.get("traffic_light"),
                }
            )
        db["pms_summary"] = []
        for _, r in pms[(pms["distributor_code"] == code) & (pms["year"] == 2025)].iterrows():
            db["pms_summary"].append(
                {
                    "year": 2025,
                    "capture_rate_total_wtd": round(float(r["capture_rate_total_wtd"]), 4),
                    "capture_rate_genuine_wtd": round(float(r["capture_rate_genuine_wtd"]), 4),
                    "revenue_gap_eur": _money(r["revenue_gap_eur_sum"]),
                    "oil_filter_capture": round(float(r["oil_filter_capture"]), 4),
                    "top_gap_categories": r["top_gap_categories"],
                }
            )
        db["mix"] = []
        for _, r in mix[(mix["distributor_code"] == code) & (mix["year"].isin([2024, 2025]))].iterrows():
            db["mix"].append(
                {
                    "year": int(r["year"]),
                    "total_eur": _money(r["total_eur"]),
                    "bvp_pct": round(100 * float(r["bvp_pct"]), 2),
                    "genuine_only_pct": round(100 * float(r["genuine_only_pct"]), 2),
                }
            )
        db["pms_categories_total"] = []
        for _, r in cap[
            (cap["distributor_code"] == code) & (cap["year"] == 2025) & (cap["line_type"] == "total")
        ].iterrows():
            db["pms_categories_total"].append(
                {
                    "category": r["pms_category"],
                    "capture_rate": round(float(r["capture_rate"]), 4),
                    "revenue_gap_eur": _money(r["revenue_gap_eur"]),
                    "actual_rev_eur": _money(r["actual_rev_eur"]),
                }
            )


def main() -> None:
    df = load_sales()
    print("TARGETS", TARGETS)
    print("date range", df["billing_date"].min(), df["billing_date"].max())
    print("FY counts", df["fiscal_year"].value_counts().sort_index().to_dict())

    # PBI H1 2026 snapshot from SALES page (data updated 2026-07-21)
    pbi_h1_2026 = {
        "period": "2026-01-01 to 2026-06-30",
        "source": "Power BI SALES DATA VP NEW · SALES page · data updated 2026-07-21",
        "network_sales_eur": 17715211.56,
        "network_sales_ly_eur": 15546435.80,
        "customers": {
            "IMOTORS": {"sales_eur": 935000, "share_pct": 5.28, "ly_eur": 814000, "yoy_pct": 15},
            "UMI": {"sales_eur": 1197000, "share_pct": 6.76, "ly_eur": 1475000, "yoy_pct": -19},
            "UTI": {"sales_eur": 1719000, "share_pct": 9.70, "ly_eur": 1500000, "yoy_pct": 15},
        },
        "markets_top3": [
            {"market": "United Kingdom", "sales_k": 6666.01, "share_pct": 60.04, "yoy_pct": 22.18},
            {"market": "Israel", "sales_k": 2915.59, "share_pct": 26.26, "yoy_pct": -2.01},
            {"market": "Germany", "sales_k": 1520.34, "share_pct": 13.69, "yoy_pct": 32.16},
        ],
        "note": "Israel market in PBI includes UMI + UTI; do not blend for IDS. UMI alone is the meeting counterparty.",
    }

    payload = {
        "generated": "2026-07-26",
        "fiscal_definition": "ISZE FY = Apr–Mar. FY2024=Apr2024–Mar2025; FY2025=Apr2025–Mar2026.",
        "local_billing_max": str(df["billing_date"].max().date()),
        "scope": "I Motors (PORTUGAL) and UMI — full hierarchy FY2024–FY2025 from billing; H1 CY2026 from Power BI",
        "verification": "01_data/00_derived/_verification_report.json green at generation time",
        "pbi_h1_2026": pbi_h1_2026,
        "distributors": [build_db(df, "IMOTORS"), build_db(df, "UMI")],
    }
    enrich_prism(payload)

    out_json = OUT / "study_data.json"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", out_json)

    # compact console summary
    for db in payload["distributors"]:
        print("===", db["key"], db["sap_sold_to"])
        print("FY", db["fy_totals"])
        print("conc FY25", db["concentration"]["FY2025"])
        print("top3 PN FY25", db["top_pn"][:3])


if __name__ == "__main__":
    main()
