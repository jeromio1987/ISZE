"""Rebuild AIM billed-euro coverage measure for the Universe board (live from sales_fact)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "01_data" / "91_build" / "_aim_coverage_measure_20260924.json"
FACT = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"

# Mirror of prism sales_loader.NON_PART_LINE_KIND keys (part_number values).
NON_PART_PN = {
    "TRANSPORT",
    "REBATE",
    "LATE PAYMENT INTEREST",
    "DISRACK01",
    "5874123810",
    "5874123811",
    "5874123812",
    "SERVICE",
    "SERVICE FEE OUTSIDE EUROPE",
    "COST DEMURRAGE",
    "COMPENSATIONS SALE E-CREDIT",
}


def _load_data_prep():
    prism_root = ROOT / "03_analytics" / "Isuzu" / "prism"
    sys.path.insert(0, str(prism_root))
    sys.path.insert(0, str(prism_root / "modules"))
    spec = importlib.util.spec_from_file_location(
        "data_prep", prism_root / "modules" / "data_prep.py"
    )
    dp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dp)
    return dp


def main() -> int:
    dp = _load_data_prep()
    fact = pd.read_parquet(FACT)
    fact["net_sales_value"] = pd.to_numeric(fact["net_sales_value"], errors="coerce").fillna(0.0)
    fact["billed_qty"] = pd.to_numeric(fact["billed_qty"], errors="coerce").fillna(0.0)
    fact["billing_date"] = pd.to_datetime(fact["billing_date"], errors="coerce")
    fact = fact[fact["billing_date"].notna() & (fact["billed_qty"] > 0)].copy()
    fact["pn"] = fact["part_number"].astype(str).str.strip()
    fact = fact[~fact["pn"].str.upper().isin(NON_PART_PN)]

    fact["sold_to_sap"] = pd.to_numeric(fact["sold_to_sap"], errors="coerce")
    fact["code"] = fact["sold_to_sap"].map(
        lambda x: dp.SAP_SOLD_TO_OVERRIDES.get(int(x)) if pd.notna(x) else None
    )
    fact = fact[fact["code"].notna() & ~fact["code"].isin(dp.EXCLUDED_CODES)]

    to_dt = pd.Timestamp("2026-08-31")
    from_dt = pd.Timestamp("2025-09-01")
    win = fact[(fact["billing_date"] >= from_dt) & (fact["billing_date"] <= to_dt)].copy()

    master = pd.read_csv(MASTER, dtype=str, low_memory=False)
    master["_pn"] = master["part_number"].fillna("").astype(str).str.strip()
    has = (
        master.drop_duplicates("_pn")
        .set_index("_pn")["has_aim"]
        .map(lambda x: str(x).strip() in {"1", "true", "True", "yes", "Y"})
    )

    win["_has_fam"] = win["pn"].map(lambda p: bool(has.get(p, False)))

    total_eur = float(win["net_sales_value"].sum())
    covered_eur = float(win.loc[win["_has_fam"], "net_sales_value"].sum())
    residual = (
        win.loc[~win["_has_fam"]]
        .groupby("pn", as_index=False)
        .agg(billed_eur=("net_sales_value", "sum"), description=("description", "first"))
        .sort_values("billed_eur", ascending=False)
    )
    top15 = [
        {
            "part_number": r["pn"],
            "billed_eur": float(r["billed_eur"]),
            "description": str(r.get("description") or ""),
            "family": "",
        }
        for _, r in residual.head(15).iterrows()
    ]

    doc = {
        "window": {
            "from": from_dt.strftime("%Y-%m-%d"),
            "to": to_dt.strftime("%Y-%m-%d"),
            "basis": (
                "sales_fact.parquet GPS-facing sold_to (PRISM exclusions), "
                "NON_PART_LINE_KIND removed, positive billed_qty; "
                "aim_master_v2.csv has_aim=1"
            ),
        },
        "totals": {
            "eur": total_eur,
            "rows": int(len(win)),
            "part_numbers": int(win["pn"].nunique()),
        },
        "covered": {
            "eur": covered_eur,
            "share": (covered_eur / total_eur) if total_eur else 0.0,
            "part_numbers": int(win.loc[win["_has_fam"], "pn"].nunique()),
        },
        "residual_top15": top15,
        "source_files": [FACT.name, MASTER.name],
        "built_at": pd.Timestamp.now().isoformat(timespec="seconds"),
    }
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"  window {doc['window']['from']} -> {doc['window']['to']}")
    print(f"  covered {doc['covered']['share']*100:.2f}%  EUR {covered_eur:,.0f} of {total_eur:,.0f}")
    print(f"  residual >=5k in top15: {sum(1 for r in top15 if r['billed_eur'] >= 5000)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
