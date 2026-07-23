"""
Full GPS / Kosha data-integrity audit.

Checks:
  1. gps_billing_clean.json + transport.json = raw JSON-rules total (no double-count)
  2. gps_billing_clean.json vs raw SAP (per DB FY24-26)
  3. gps_master.csv == gps_clean_all_fy_v2 net_gps == v3c gross
  4. v3d net == v3c gross - Distributor Warranty Expense
  5. GPS_Kosha toggle gross/warranty vs rebuilt JSON + warranty expense (if workbook exists)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import openpyxl
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DERIVED_DIR, DATA_ROOT  # noqa: E402

KOSHA = DATA_ROOT / "14_dashboards" / "kosha"
GPS_DBS = [
    "ITUK", "IUK", "UTI", "UMI", "ISD", "IBX", "Imotors", "Sverige", "Norway",
    "Ireland", "RSA", "AutoWallis", "ROM Auto", "Nordic FI", "Danmark",
    "GasanZammit", "Loutsios", "BL Iceland",
]
FY = (2024, 2025, 2026)
TOL = 5.0  # EUR


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def read_v3x(name: str) -> dict[str, dict[int, float]]:
    p = KOSHA / name
    if not p.exists():
        return {}
    wb = openpyxl.load_workbook(p, data_only=True)
    t1 = wb["GPS Actuals FY2024-26"]
    out: dict[str, dict[int, float]] = {}
    for r in range(4, 23):
        nm = t1.cell(r, 1).value
        if not nm:
            continue
        out[nm] = {
            2024: float(t1.cell(r, 2).value or 0),
            2025: float(t1.cell(r, 5).value or 0),
            2026: float(t1.cell(r, 8).value or 0),
        }
    wb.close()
    return out


# canonical v3c name → toggle / billing row name
WARRANTY_DB_ALIASES = {"RSA": "Norway", "Greece": "RSA"}


def warranty_expense_for_toggle(kap: dict, toggle_db: str, fy: int) -> float:
    for k, v in WARRANTY_DB_ALIASES.items():
        if v == toggle_db:
            return kap.get(k, {}).get(fy, 0)
    return kap.get(toggle_db, {}).get(fy, 0)


def load_warranty_expense() -> dict[str, dict[int, float]]:
    w: dict[str, dict[int, float]] = {}
    p = DERIVED_DIR / "distributor_warranty_expense_fiscal.csv"
    if not p.exists():
        p = DERIVED_DIR / "warranty_by_db_FY_canonical.csv"
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if r["db"] == "MIDI":
            continue
        db = r["db"]
        w[db] = {
            2024: float(r["warr_FY2024"]),
            2025: float(r["warr_FY2025"]),
            2026: float(r["warr_FY2026"]),
        }
    return w


def load_master() -> dict[str, dict[int, float]]:
    out = {}
    for r in csv.DictReader(open(DERIVED_DIR / "gps_master.csv", encoding="utf-8")):
        db = r[""] or list(r.values())[0]
        out[db] = {fy: float(r[f"bill_FY{fy}"]) for fy in FY}
    return out


def load_v2() -> dict[str, dict[int, float]]:
    """Aggregate gps_clean_all_fy_v2 to canonical DB names."""
    from rebuild_gps_billing_and_surcharge_check import PAYER_DB  # noqa: WPS433

    df = pd.read_csv(DERIVED_DIR / "gps_clean_all_fy_v2.csv")
    payer_map = {int(k): v for k, v in PAYER_DB.items()}
    out: dict[str, dict[int, float]] = {db: {fy: 0.0 for fy in FY} for db in GPS_DBS}
    for _, row in df.iterrows():
        p = int(row["payer"]) if pd.notna(row["payer"]) else None
        if p is None:
            continue
        db = payer_map.get(p)
        if not db and "UTI" in str(row.get("db_name", "")):
            db = "UTI"
        if not db:
            continue
        fy = int(row["FY"])
        if fy in FY and db in out:
            out[db][fy] += float(row["net_gps"])
    return out


def check(label: str, ok: bool, detail: str = "") -> dict:
    status = "PASS" if ok else "FAIL"
    line = f"  [{status}] {label}" + (f" — {detail}" if detail else "")
    print(line)
    return {"check": label, "status": status, "detail": detail}


def main() -> None:
    issues: list[dict] = []
    print("=" * 72)
    print("GPS / KOSHA DATA INTEGRITY AUDIT")
    print("=" * 72)

    bill = load_json(DERIVED_DIR / "gps_billing_clean.json")
    transport = load_json(DERIVED_DIR / "gps_billing_transport_excluded.json")
    audit_csv = DERIVED_DIR / "gps_json_vs_raw_audit.csv"
    master = load_master()
    v3c = read_v3x("ISZE_GPS_Kosha_v3c.xlsx")
    v3d = read_v3x("ISZE_GPS_Kosha_v3d.xlsx")
    kap = load_warranty_expense()
    v2 = load_v2() if (DERIVED_DIR / "gps_clean_all_fy_v2.csv").exists() else {}

    # --- 1 Israel double-count sanity ---
    uti24 = bill.get("UTI", {}).get("2024", 0)
    issues.append(check(
        "UTI FY24 not double-counted (< EUR4M)",
        uti24 < 4_000_000,
        f"UTI FY24 billing JSON = EUR{uti24:,.0f}",
    ))

    # --- 2 JSON audit CSV vs stored (transport-excluded rebuild) ---
    if audit_csv.exists():
        adf = pd.read_csv(audit_csv)
        # Re-run comparison: stored should match raw_minus_transport
        bad = adf[adf.apply(
            lambda r: abs(r["stored_json"] - r.get("raw_minus_transport", r["raw_json_rules"] - r["transport_in_json"])) > TOL,
            axis=1,
        )]
        # simpler: stored vs raw_json - transport from csv columns
        bad = adf[adf.apply(lambda r: abs(r["stored_json"] - r["raw_minus_transport"]) > TOL, axis=1)]
        issues.append(check(
            "billing JSON == raw (transport + surcharge stripped)",
            len(bad) == 0,
            f"{len(bad)} mismatches of {len(adf)}" if len(bad) else "all 54 cells match",
        ))

    # --- 3 v3c == gps_master ---
    if v3c and master:
        n_bad = 0
        for db in GPS_DBS:
            for fy in FY:
                a = v3c.get(db, {}).get(fy, 0)
                b = master.get(db, {}).get(fy, 0)
                if abs(a - b) > TOL:
                    n_bad += 1
        issues.append(check(
            "v3c gross == gps_master.csv",
            n_bad == 0,
            f"{n_bad} mismatches" if n_bad else "all 54 cells",
        ))

    # --- 4 (removed 2026-07-03) v3c vs gps_clean_all_fy_v2 compared the Kosha billing
    # basis (BillT/SaTy/transport exclusions only) against the FULL GPS-clean basis
    # (also excludes service fees, late payment, demurrage, Shell 550047/550070, ZDR).
    # The two differ by design (ITUK fees ~EUR150-200K/FY) — a false-positive failure.
    # Cross-basis reconciliation now lives in 04_tools/gps_reconcile.py.

    # --- 5 v3d net == v3c - warranty expense ---
    if v3c and v3d and kap:
        n_bad = 0
        for db in GPS_DBS:
            for fy in FY:
                g = v3c.get(db, {}).get(fy, 0)
                n = v3d.get(db, {}).get(fy, 0)
                w = kap.get(db, {}).get(fy, 0)
                exp = max(0, g - w)
                if abs(n - exp) > TOL:
                    n_bad += 1
        issues.append(check(
            "v3d net == v3c gross − Distributor Warranty Expense",
            n_bad == 0,
            f"{n_bad} mismatches" if n_bad else "all 54 cells",
        ))

    # --- 6 transport file consistency ---
    tr_net = sum(
        transport.get(db, {}).get(str(fy), 0) for db in transport for fy in FY
    )
    issues.append(check(
        "transport sidecar populated (FY24-26)",
        tr_net > 600_000,
        f"total EUR{tr_net:,.0f}",
    ))

    # --- 7 Toggle workbook ---
    toggle_p = KOSHA / "GPS_Kosha_FY2024_2030.xlsx"
    if toggle_p.exists():
        wb = openpyxl.load_workbook(toggle_p, data_only=True)
        ws = wb["GPS · Toggle"]
        n_bad_g = n_bad_w = 0
        for r in range(6, 30):
            db = ws.cell(r, 1).value
            if db not in GPS_DBS:
                continue
            for i, fy in enumerate(FY):
                gross_col = 4 + i * 5
                warr_col = gross_col + 1
                tg = ws.cell(r, gross_col).value or 0
                tw = ws.cell(r, warr_col).value or 0
                jg = float(bill.get(db, {}).get(str(fy), 0) or 0)
                kw = warranty_expense_for_toggle(kap, db, fy)
                if abs(tg - jg) > TOL:
                    n_bad_g += 1
                if abs(tw - kw) > TOL:
                    n_bad_w += 1
        wb.close()
        issues.append(check(
            "Toggle gross == rebuilt billing JSON",
            n_bad_g == 0,
            f"{n_bad_g} gross mismatches" if n_bad_g else "all checked cells",
        ))
        issues.append(check(
            "Toggle warranty == fiscal Distributor Warranty Expense",
            n_bad_w == 0,
            f"{n_bad_w} warranty mismatches" if n_bad_w else "all checked cells",
        ))
    else:
        issues.append(check("Toggle workbook present", False, str(toggle_p)))

    # --- Summary ---
    fails = [i for i in issues if i["status"] == "FAIL"]
    print("\n" + "=" * 72)
    print(f"RESULT: {len(issues) - len(fails)}/{len(issues)} checks passed")
    if fails:
        print("FAILURES:")
        for f in fails:
            print(f"  • {f['check']}: {f['detail']}")
    else:
        print("All integrity checks passed.")
    out = DERIVED_DIR / "gps_integrity_audit.json"
    out.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
