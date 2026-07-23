"""Build gps_dual_basis.json — CY/FY switchable actuals + GPS target tiers (base / stretch / extended).

Sources:
  CY sales     — build_gps_v9 SALES_25 / sales_fact calendar year
  FY sales     — gps_billing_clean.json (Apr–Mar, label = start year)
  CY warranty  — gps_warranty_cy2025.json / build_gps_v9 WARRANTY
  FY warranty  — distributor_warranty_expense_fiscal.csv
  Base FY27    — reviewed budget (budget_per_DB_reviewed_24042026.xlsx + BP 2027 VP turnover)
  Max spend    — uio_v19_gps.json FY25 anchor + FY27 projection
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

from gps_v9_loaders import GPS_DBS, build_gps_uio_package
from load_bp_fy27 import bp_fy27_for_gps_dbs

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DATA = ROOT / "01_data"
BUILD = DATA / "91_build"
DERIVED = DATA / "00_derived"
OUT = BUILD / "gps_dual_basis.json"

# CY2025 ISZE→DB sales (same as build_gps_v9)
SALES_CY2025 = {
    "ITUK": 5_769_867.82,
    "IUK": 6_221_920.41,
    "UMI": 3_388_801.28,
    "UTI": 3_402_116.94,
    "GERMANY": 2_577_765.90,
    "BELGIUM": 2_143_951.90,
    "IRELAND": 1_213_660.33,
    "NORWAY": 1_438_472.63,
    "SWEDEN": 1_289_481.04,
    "DENMARK": 150_218.49,
    "FINLAND": 285_912.53,
    "ICELAND": 87_259.89,
    "CYPRUS": 429_512.03,
    "GREECE": 528_390.82,
    "MALTA": 206_502.27,
    "ROMANIA": 177_276.35,
    "HUNGARY": 330_030.58,
    "PORTUGAL": 1_712_790.96,
}

WARRANTY_CY2025 = {
    "ITUK": 374_426.05,
    "IUK": 1_054_395,
    "UMI": 1_791_020.28,
    "UTI": 255_967.77,
    "GERMANY": 259_675,
    "BELGIUM": 74_677,
    "IRELAND": 34_857,
    "NORWAY": 290_712,
    "SWEDEN": 189_618,
    "DENMARK": 9_115,
    "FINLAND": 48_676,
    "ICELAND": 7_035,
    "CYPRUS": 28_041,
    "GREECE": 56_159,
    "MALTA": 18_219,
    "ROMANIA": 19_377,
    "HUNGARY": 77_434,
    "PORTUGAL": 130_588,
}

# Kosha billing name → GPS v9 distributor code
BILLING_TO_GPS: dict[str, str] = {
    "ITUK": "ITUK",
    "IUK": "IUK",
    "UMI": "UMI",
    "UTI": "UTI",
    "ISD": "GERMANY",
    "IBX": "BELGIUM",
    "Ireland": "IRELAND",
    "Norway": "NORWAY",
    "Sverige": "SWEDEN",
    "Danmark": "DENMARK",
    "Nordic FI": "FINLAND",
    "BL Iceland": "ICELAND",
    "Loutsios": "CYPRUS",
    "GasanZammit": "MALTA",
    "ROM Auto": "ROMANIA",
    "AutoWallis": "HUNGARY",
    "Imotors": "PORTUGAL",
}

# Warranty CSV db → GPS v9 code (RSA row = Norway warranty entity per DISTRIBUTOR_WARRANTY_EXPENSE.md)
WARRANTY_FY_TO_GPS: dict[str, str] = {
    "ITUK": "ITUK",
    "IUK": "IUK",
    "UTI": "UTI",
    "UMI": "UMI",
    "ISD": "GERMANY",
    "IBX": "BELGIUM",
    "Ireland": "IRELAND",
    "RSA": "NORWAY",
    "Sverige": "SWEDEN",
    "Greece": "GREECE",
    "Danmark": "DENMARK",
    "Nordic FI": "FINLAND",
    "BL Iceland": "ICELAND",
    "Loutsios": "CYPRUS",
    "GasanZammit": "MALTA",
    "ROM Auto": "ROMANIA",
    "AutoWallis": "HUNGARY",
    "Imotors": "PORTUGAL",
}


def _load_fy_billing() -> dict[str, dict[int, float]]:
    billing = json.loads((DERIVED / "gps_billing_clean.json").read_text(encoding="utf-8"))
    out: dict[str, dict[int, float]] = {db: {} for db in GPS_DBS}
    for kosha_name, years in billing.items():
        gps = BILLING_TO_GPS.get(kosha_name)
        if not gps:
            continue
        for fy_label, val in years.items():
            out[gps][int(fy_label)] = out[gps].get(int(fy_label), 0) + float(val or 0)
    # Greece: payer not in billing_clean — use gps_master canonical row
    master = DERIVED / "gps_master.csv"
    if master.is_file():
        for r in csv.DictReader(open(master, encoding="utf-8")):
            db_name = (r.get("") or list(r.values())[0] or "").strip()
            if db_name == "Greece":
                for fy in (2024, 2025, 2026):
                    col = f"bill_FY{fy}"
                    if col in r and r[col]:
                        out["GREECE"][fy] = float(r[col])
    return out


def _load_fy_warranty() -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = {db: {} for db in GPS_DBS}
    p = DERIVED / "distributor_warranty_expense_fiscal.csv"
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if r["db"] == "MIDI":
            continue
        gps = WARRANTY_FY_TO_GPS.get(r["db"])
        if not gps:
            continue
        out[gps][2024] = out[gps].get(2024, 0) + float(r["warr_FY2024"])
        out[gps][2025] = out[gps].get(2025, 0) + float(r["warr_FY2025"])
        out[gps][2026] = out[gps].get(2026, 0) + float(r["warr_FY2026"])
    return out


def _stretch_pp(gps_ex: float, gps_plan: float) -> float:
    """Realistic one-year GPS pp uplift — not full gap to plan."""
    gap_pp = (gps_plan - gps_ex) * 100
    if gap_pp <= 0:
        return 0.5
    if gps_ex < 0.35:
        return round(min(5.0, max(2.5, gap_pp * 0.25)), 2)
    if gps_ex < 0.55:
        return round(min(4.0, max(2.0, gap_pp * 0.35)), 2)
    return round(min(2.5, max(1.0, gap_pp * 0.40)), 2)


def _extended_pp(gps_ex: float, gps_plan: float, stretch: float) -> float:
    """Ambitious but defensible — ~60% of remaining gap after stretch, cap +8pp YoY."""
    gap_pp = max(0.0, (gps_plan - gps_ex) * 100 - stretch)
    extra = gap_pp * 0.60
    return round(min(8.0, stretch + extra), 2)


def main() -> None:
    pkg = build_gps_uio_package()
    dist = pkg["distributors"]
    fy_sales = _load_fy_billing()
    fy_warr = _load_fy_warranty()

    base_targets = bp_fy27_for_gps_dbs()

    distributors = []
    for db in GPS_DBS:
        max25 = dist[db]["max_spend"][2025]
        max26 = dist[db]["max_spend"][2026]
        max27 = dist[db]["max_spend"][2027]
        cy_sales = SALES_CY2025[db]
        cy_warr = WARRANTY_CY2025.get(db, 0)
        fy25_sales = fy_sales[db].get(2025, 0)
        fy25_warr = fy_warr[db].get(2025, 0)
        fy26_sales = fy_sales[db].get(2026, 0)
        fy26_warr = fy_warr[db].get(2026, 0)
        fy24_sales = fy_sales[db].get(2024, 0)
        fy24_warr = fy_warr[db].get(2024, 0)

        gps_cy_ex = (cy_sales - cy_warr) / max25 if max25 else 0
        gps_fy25_ex = (fy25_sales - fy25_warr) / max25 if max25 and fy25_sales else None
        gps_fy26_ex = (
            (fy26_sales - fy26_warr) / max26
            if max26 and fy26_sales
            else None
        )

        base_eur = base_targets[db]
        gps_plan = base_eur / max27 if max27 else 0
        stretch_pp = _stretch_pp(gps_cy_ex, gps_plan)
        extended_pp = _extended_pp(gps_cy_ex, gps_plan, stretch_pp)
        stretch_eur = gps_cy_ex * max27 + (stretch_pp / 100) * max27 + cy_warr
        extended_eur = gps_cy_ex * max27 + (extended_pp / 100) * max27 + cy_warr

        distributors.append(
            {
                "code": db,
                "scope": dist[db]["scope"],
                "max_spend": {"cy2025": max25, "fy2026": max26, "fy2027": max27},
                "actuals": {
                    "calendar": {
                        "2024": None,
                        "2025": {
                            "sales_gross_eur": cy_sales,
                            "warranty_eur": cy_warr,
                            "sales_ex_warranty_eur": cy_sales - cy_warr,
                            "gps_ex_warranty": round(gps_cy_ex, 4),
                        },
                    },
                    "fiscal": {
                        "2024": {
                            "sales_gross_eur": fy24_sales,
                            "warranty_eur": fy24_warr,
                            "sales_ex_warranty_eur": fy24_sales - fy24_warr,
                            "gps_ex_warranty": round((fy24_sales - fy24_warr) / max25, 4)
                            if max25 and fy24_sales
                            else None,
                        },
                        "2025": {
                            "sales_gross_eur": fy25_sales,
                            "warranty_eur": fy25_warr,
                            "sales_ex_warranty_eur": fy25_sales - fy25_warr,
                            "gps_ex_warranty": round(gps_fy25_ex, 4) if gps_fy25_ex is not None else None,
                        },
                        "2026": {
                            "sales_gross_eur": fy26_sales if fy26_sales else None,
                            "warranty_eur": fy26_warr if fy26_sales else None,
                            "sales_ex_warranty_eur": fy26_sales - fy26_warr if fy26_sales else None,
                            "gps_ex_warranty": round(gps_fy26_ex, 4) if gps_fy26_ex is not None else None,
                            "note": "FY2026 = Apr 2025–Mar 2026 (complete). GPS % = ex-warr sales ÷ FY26 max spend.",
                        },
                    },
                },
                "targets_fy2027": {
                    "base_plan_eur": round(base_eur, 2),
                    "base_gps_implied": round(gps_plan, 4),
                    "stretch": {
                        "eur": round(stretch_eur, 2),
                        "gps_pp_uplift": stretch_pp,
                        "gps_implied": round(gps_cy_ex + stretch_pp / 100, 4),
                    },
                    "extended": {
                        "eur": round(extended_eur, 2),
                        "gps_pp_uplift": extended_pp,
                        "gps_implied": round(gps_cy_ex + extended_pp / 100, 4),
                    },
                },
            }
        )

    payload = {
        "generated": date.today().isoformat(),
        "conventions": {
            "fiscal_year": "Apr–Mar, label = start year (FY2025 = Apr 2024 – Mar 2025)",
            "calendar_year": "Jan–Dec",
            "current_fy": "FY2027 (Apr 2026 – Mar 2027)",
            "last_complete_fy": "FY2026 (Apr 2025 – Mar 2026) — billing file label FY2026",
            "primary_actual_cy": 2025,
            "primary_actual_fy": 2026,
            "warranty_cy_basis": "claim-file Written Date_YMD (see Warranty_CY2025_by_DB.md)",
            "warranty_fy_basis": "distributor_warranty_expense_fiscal.csv",
        },
        "target_methodology": {
            "base": "Reviewed BP FY27 per DB (budget_per_DB_reviewed_24042026.xlsx · VP turnover 24 Apr 2026)",
            "stretch": "Current GPS ex-warr + realistic 1-year pp uplift (25–40% of gap to plan, tiered by capture band)",
            "extended": "Stretch + 60% of remaining gap to plan GPS; cap +8pp YoY total",
        },
        "network_totals": {
            "cy2025_sales_eur": round(sum(SALES_CY2025.values()), 2),
            "fy2025_sales_eur": round(sum(fy_sales[d].get(2025, 0) for d in GPS_DBS), 2),
            "fy2026_sales_eur": round(sum(fy_sales[d].get(2026, 0) for d in GPS_DBS), 2),
            "base_fy2027_eur": round(sum(base_targets.values()), 2),
            "stretch_fy2027_eur": round(sum(d["targets_fy2027"]["stretch"]["eur"] for d in distributors), 2),
            "extended_fy2027_eur": round(sum(d["targets_fy2027"]["extended"]["eur"] for d in distributors), 2),
        },
        "distributors": distributors,
    }

    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("written", OUT)
    print(
        f"Network CY2025 €{payload['network_totals']['cy2025_sales_eur']/1e6:.2f}M | "
        f"FY2025 €{payload['network_totals']['fy2025_sales_eur']/1e6:.2f}M | "
        f"FY2026 €{payload['network_totals']['fy2026_sales_eur']/1e6:.2f}M | "
        f"Base €{payload['network_totals']['base_fy2027_eur']/1e6:.2f}M | "
        f"Stretch €{payload['network_totals']['stretch_fy2027_eur']/1e6:.2f}M | "
        f"Extended €{payload['network_totals']['extended_fy2027_eur']/1e6:.2f}M"
    )


if __name__ == "__main__":
    main()
