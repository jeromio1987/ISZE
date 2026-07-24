#!/usr/bin/env python3
"""
Build aim_cy2026.data.js for 02_dashboards/sales/AIM_Dashboard_CY2026.html.

Sources
  01_data/00_derived/cy2026_q1.csv      — line-level SAP billing Jan–Mar 2026
                                          (derived from sales_2026tillApril.XLSX)
  01_data/00_derived/aim_pn_classification.csv
  01_data/00_derived/eucon_price_gap.csv — network-level IAM benchmark (44 PNs)
  sales_fact.parquet (via prism loader)  — CY2025 same-window comparison
  AIM workbook Parts Master              — pricing-risk flags (desc join)

Cleaning follows 04_tools/gps_full_run_v2.py: drop undated footer rows,
exclude credit notes (BillT G2/RE/S1/S2, SaTy CR/ZDR), transport, interest,
service fees, demurrage, Shell lubricants (550047*/550070*).
CY2026 figures are ACTUAL invoiced values (unlike CY2025 AIM scoring = Qty x PR00).

  python scripts/build_aim_cy2026_dashboard.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR, ISZE_ROOT, resolve_mapping_path  # noqa: E402
from modules.aim_pn_classifier import PLACEHOLDER_L1  # noqa: E402
from modules.bvp_analytics import normalize_pn_value  # noqa: E402
from modules.data_prep import EXCLUDED_CODES, apply_distributor_codes, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

_p4p5_spec = importlib.util.spec_from_file_location(
    "build_bvp_p4_p5", Path(__file__).parent / "build_bvp_p4_p5.py"
)
_p4p5 = importlib.util.module_from_spec(_p4p5_spec)
_p4p5_spec.loader.exec_module(_p4p5)

CY2026_CSV = DERIVED_DIR / "cy2026_q1.csv"
EUCON_CSV = DERIVED_DIR / "eucon_price_gap.csv"
VERIFY_JSON = DERIVED_DIR / "_verification_report.json"
OUT_JS = ISZE_ROOT / "02_dashboards" / "sales" / "aim_cy2026.data.js"

EXCL_BILLT = {"G2", "RE", "S1", "S2"}
EXCL_SATY = {"CR", "ZDR"}
SHELL_PFX = ("550047", "550070")


def _norm_pn(v) -> str:
    return normalize_pn_value(v) or ""


def _is_placeholder(v) -> bool:
    s = "" if v is None or pd.isna(v) else str(v).strip().lower()
    return s in ("", "nan") or s in PLACEHOLDER_L1


def load_cy2026() -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(CY2026_CSV, dtype=str)
    # duplicate headers: second 'Payer' column = DB name
    payer_cols = [c for c in df.columns if c.startswith("Payer")]
    df = df.rename(
        columns={
            "Billing Date": "billing_date",
            "BillT": "billt",
            "Sold-to pt": "sold_to",
            payer_cols[-1]: "db_name",
            "Material": "material_num",
            "Material Number": "material_desc",
            "Net value": "net_value",
            "SaTy": "saty",
        }
    )
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")
    df = df.dropna(subset=["billing_date"])  # drops SAP footer/total rows
    df = df[df["material_num"].notna() & (df["material_num"].str.lower() != "nan")]
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce").fillna(0)
    df["billt"] = df["billt"].astype(str).str.strip().str.upper()
    df["saty"] = df["saty"].astype(str).str.strip().str.upper()
    df["material_num"] = df["material_num"].astype(str).str.strip()

    mu = df["material_num"].str.upper()
    excl = {
        "credit_notes": df["billt"].isin(EXCL_BILLT) | df["saty"].isin(EXCL_SATY),
        "transport": mu == "TRANSPORT",
        # cy2026 file uses no-space fee materials (SERVICE, SERVICEFEEWITHINEUROPE, ...)
        "interest_fees": mu.str.contains(
            "LATE PAYMENT|INTEREST|SERVICE ?FEE|DEMURRAGE|COSTDEMURRAGE", na=False
        ) | (mu == "SERVICE"),
        "rebates": mu == "REBATE",
        "shell_lubricants": df["material_num"].str.startswith(SHELL_PFX),
    }
    any_excl = pd.Series(False, index=df.index)
    waterfall = {"gross_eur": round(float(df["net_value"].sum()))}
    for name, mask in excl.items():
        step = mask & ~any_excl
        waterfall[name + "_eur"] = round(float(df.loc[step, "net_value"].sum()))
        any_excl |= mask
    clean = df[~any_excl].copy()
    waterfall["clean_eur"] = round(float(clean["net_value"].sum()))
    return clean, waterfall


def main() -> int:
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    q1, waterfall = load_cy2026()

    q1 = apply_distributor_codes(q1, df_map)
    # cy2026 sold-to are short payer codes not in sap_sold_to_mapping —
    # fall back to the DB legal name for anything left UNMAPPED
    from modules.data_prep import build_name_to_code_map

    name_map = build_name_to_code_map(df_map)
    un = q1["distributor_code"] == "UNMAPPED"
    q1.loc[un, "distributor_code"] = (
        q1.loc[un, "db_name"].astype(str).str.strip().str.upper().map(name_map).fillna("UNMAPPED")
    )
    q1 = q1[~q1["distributor_code"].isin(EXCLUDED_CODES)].copy()
    unmapped_eur = round(float(q1.loc[q1["distributor_code"] == "UNMAPPED", "net_value"].sum()))

    # classification join
    cls = pd.read_csv(DERIVED_DIR / "aim_pn_classification.csv", dtype=str)
    cls["_pn"] = cls["part_number"].map(_norm_pn)
    cls = cls.drop_duplicates("_pn").set_index("_pn")
    q1["_pn"] = q1["material_num"].map(_norm_pn)
    q1 = q1.join(cls[["aim_l1", "aim_l2", "aim_source"]], on="_pn")
    q1["classified"] = ~q1["aim_l1"].map(_is_placeholder)

    # pricing-risk flags: same desc join as build_bvp_p4_p5 (workbook Parts Master)
    aim_master = _p4p5.load_aim_parts_master(_p4p5._resolve_aim())
    risk_map = aim_master.set_index("description_norm")["aim_high_risk"]
    q1["desc_norm"] = q1["material_desc"].fillna("").astype(str).str.strip().str.upper()
    q1["aim_high_risk"] = q1["desc_norm"].map(risk_map)
    q1["risk_matched"] = q1["aim_high_risk"].notna()

    total = float(q1["net_value"].sum())
    win = [str(q1["billing_date"].min().date()), str(q1["billing_date"].max().date())]

    # CY2025 same-window comparison (prism loader = same distributor scope)
    sf, _src = load_prism_sales(df_map)
    sf = sf[(sf["line_kind"] == "part") & (sf["year"] == 2025) & (sf["month"] <= 3)]
    prev_by_db = sf.groupby("distributor_code")["net_sales_value"].sum()
    prev_total = float(prev_by_db.sum())

    by_db_rows = []
    for code, g in q1.groupby("distributor_code"):
        eur = float(g["net_value"].sum())
        by_db_rows.append(
            {
                "db": code,
                "eur": round(eur),
                "prev_eur": round(float(prev_by_db.get(code, 0.0))),
                "coverage_pct": round(float(g.loc[g["classified"], "net_value"].sum() / eur * 100), 1) if eur else None,
                "high_risk_pct": round(
                    float(g.loc[g["aim_high_risk"].fillna(False), "net_value"].sum()
                          / g.loc[g["risk_matched"], "net_value"].sum() * 100), 2,
                ) if float(g.loc[g["risk_matched"], "net_value"].sum()) > 0 else None,
            }
        )
    by_db_rows.sort(key=lambda r: -r["eur"])

    l1 = q1.copy()
    l1["l1_label"] = np.where(l1["classified"], l1["aim_l1"], "(open / review)")
    by_l1 = [
        {"l1": k, "eur": round(float(v))}
        for k, v in l1.groupby("l1_label")["net_value"].sum().sort_values(ascending=False).items()
    ]

    q1["month"] = q1["billing_date"].dt.month
    prev_m = sf.groupby("month")["net_sales_value"].sum()
    by_month = [
        {
            "month": f"2026-{m:02d}",
            "eur": round(float(v)),
            "prev_eur": round(float(prev_m.get(m, 0.0))),
        }
        for m, v in q1.groupby("month")["net_value"].sum().items()
    ]

    top_pns = [
        {
            "pn": pn,
            "desc": str(g["desc"])[:40],
            "eur": round(float(g["eur"])),
            "l1": g["l1"] if pd.notna(g["l1"]) else "(open)",
        }
        for pn, g in q1.groupby("_pn")
        .agg(desc=("material_desc", "first"), eur=("net_value", "sum"), l1=("aim_l1", "first"))
        .sort_values("eur", ascending=False)
        .head(15)
        .iterrows()
    ]

    open_gap = (
        q1[~q1["classified"]]
        .groupby("_pn")
        .agg(desc=("material_desc", "first"), eur=("net_value", "sum"))
        .sort_values("eur", ascending=False)
        .head(10)
    )
    open_gap_rows = [
        {"pn": pn, "desc": str(r["desc"])[:40], "eur": round(float(r["eur"]))}
        for pn, r in open_gap.iterrows()
    ]

    # IAM benchmark — network-level only (Eucon/AutoDoc, 44 PNs); no DB attribution
    eu = pd.read_csv(EUCON_CSV, dtype={"pn": str})
    eu["_pn"] = eu["pn"].map(_norm_pn)
    rev26 = q1.groupby("_pn")["net_value"].sum()
    eu["cy2026_rev_eur"] = eu["_pn"].map(rev26).fillna(0.0)
    iam_pns = [
        {
            "pn": r["pn"],
            "desc": str(r["description"])[:36],
            "ie40_eur": round(float(r["ISZE_IE40_Price_EUR"]), 2),
            "iam_avg_eur": round(float(r["Avg_Competitor_EUR"]), 2),
            "iam_min_eur": round(float(r["Min_Competitor_EUR"]), 2),
            "avg_delta_pct": round(float(r["Avg_Delta_pct"]) * 100, 1),
            "cy2026_rev_eur": round(float(r["cy2026_rev_eur"])),
            "brands": int(r["Competitor_Count"]),
        }
        for _, r in eu.iterrows()
        if pd.notna(r["ISZE_IE40_Price_EUR"]) and pd.notna(r["Avg_Competitor_EUR"])
    ]
    above_avg = sum(1 for r in iam_pns if r["avg_delta_pct"] > 0)
    iam = {
        "pns": iam_pns,
        "n_benchmarked": len(iam_pns),
        "n_above_iam_avg": above_avg,
        "cy2026_rev_on_benchmarked_eur": round(sum(r["cy2026_rev_eur"] for r in iam_pns)),
    }

    verify = {}
    if VERIFY_JSON.exists():
        v = json.loads(VERIFY_JSON.read_text())
        verify = {"generated_at": v.get("generated_at"), **v.get("summary", {})}

    risk_matched_eur = float(q1.loc[q1["risk_matched"], "net_value"].sum())
    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window": win,
            "basis": "Actual SAP invoiced values (F2), GPS-auditor exclusions applied",
            "prev_window": "CY2025 Jan-Mar (sales_fact, same distributor scope)",
            "verification": verify,
            "waterfall": waterfall,
            "unmapped_eur": unmapped_eur,
        },
        "kpis": {
            "ytd_clean_eur": round(total),
            "prev_same_window_eur": round(prev_total),
            "yoy_pct": round((total / prev_total - 1) * 100, 1) if prev_total else None,
            "coverage_pct": round(float(q1.loc[q1["classified"], "net_value"].sum()) / total * 100, 1) if total else None,
            "open_review_eur": round(float(q1.loc[~q1["classified"], "net_value"].sum())),
            "high_risk_eur": round(float(q1.loc[q1["aim_high_risk"].fillna(False), "net_value"].sum())),
            "high_risk_pct_of_matched": round(
                float(q1.loc[q1["aim_high_risk"].fillna(False), "net_value"].sum()) / risk_matched_eur * 100, 2
            ) if risk_matched_eur else None,
            "risk_match_rate_pct": round(risk_matched_eur / total * 100, 1) if total else None,
        },
        "by_db": by_db_rows,
        "by_l1": by_l1,
        "by_month": by_month,
        "top_pns": top_pns,
        "open_gap": open_gap_rows,
        "iam_benchmark": iam,
    }

    body = json.dumps(payload, ensure_ascii=False, indent=1, allow_nan=False)
    OUT_JS.write_text(
        "/* Generated by build_aim_cy2026_dashboard.py — do not edit */\n"
        "window.__AIM_CY2026_DATA__ = " + body + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT_JS}")
    print(f"  clean EUR {total:,.0f} | coverage {payload['kpis']['coverage_pct']}% | "
          f"YoY {payload['kpis']['yoy_pct']}% | IAM PNs {iam['n_benchmarked']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
