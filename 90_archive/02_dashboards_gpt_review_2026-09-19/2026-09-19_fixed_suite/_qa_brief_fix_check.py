"""One-shot QA for the 2026-09-19 HTML dashboard fix brief."""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
FILES = [
    "ISZE_Lost_Sales_Model.html",
    "ISZE_PMS_Tonnage_Evolution.html",
    "ISZE_DB_DLR_Replenishment_CY2025.html",
    "ISZE_DB_Leakage_Review_CY2025.html",
    "ISZE_Aftermarket_BI_Command_Center.html",
    "ISZE_PMS_Family_Evolution_v2.html",
]


def main() -> int:
    ok = True
    for name in FILES:
        t = (BASE / name).read_text(encoding="utf-8")
        print(f"\n{name} ({(BASE / name).stat().st_size / 1024:.1f} KB)")
        checks = {
            "has_basis": bool(
                re.search(r"OBSERVED|Observed|basis-strip|class=\"basis\"", t)
            ),
            "never_bought": "Never bought" in t,
            "sell_through": bool(re.search(r"sell-through|Sell-through", t, re.I)),
            "internal_internal": bool(re.search(r"[Ii]nternal internal", t)),
            "half_register": "Roughly half the register" in t,
            "monday": "Monday pricing" in t,
            # Same-line glue only (brief bug). Separate-line comment + chart is correct.
            "verdict_bug": any(
                "outcome." in ln and "new Chart" in ln for ln in t.splitlines()
            ),
            "losing_h1": "<h1>Where are we losing sales" in t,
            "modelled_opp": bool(
                re.search(r"[Mm]odelled opportunity|[Mm]odelled aftermarket", t)
            ),
            "retired": "retired" in t.lower(),
        }
        for k, v in checks.items():
            print(f"  {k}: {v}")

        if name == "ISZE_Lost_Sales_Model.html":
            if "new Chart(document.getElementById('c_verdict')" not in t:
                print("  FAIL: c_verdict chart missing")
                ok = False
            bad = [
                ln
                for ln in t.splitlines()
                if "c_verdict" in ln and ln.strip().startswith("//") and "new Chart" in ln
            ]
            if bad:
                print("  FAIL: commented c_verdict", bad)
                ok = False
            if checks["losing_h1"] or checks["never_bought"] or checks["verdict_bug"]:
                ok = False
            if not checks["modelled_opp"] or not checks["has_basis"]:
                ok = False

        if name == "ISZE_DB_DLR_Replenishment_CY2025.html":
            if checks["sell_through"] or checks["internal_internal"]:
                ok = False
            if not checks["has_basis"]:
                ok = False

        if name == "ISZE_Aftermarket_BI_Command_Center.html":
            if checks["half_register"] or checks["monday"]:
                ok = False
            if not checks["retired"]:
                ok = False

        if name == "ISZE_PMS_Tonnage_Evolution.html":
            if "uncaptured spend largest, by band" in t.lower():
                print("  FAIL: old band uncaptured title")
                ok = False
            if not checks["has_basis"]:
                ok = False

        if name == "ISZE_DB_Leakage_Review_CY2025.html":
            if "Where parts revenue leaves the network" in t:
                print("  FAIL: old leakage title")
                ok = False
            if "not additive" not in t.lower():
                print("  FAIL: missing non-additive note")
                ok = False

        if name == "ISZE_PMS_Family_Evolution_v2.html":
            if not checks["has_basis"]:
                ok = False

    print("\nOVERALL", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
