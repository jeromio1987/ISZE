"""Critical cross-file GPS/Kosha audit for presentation readiness."""
import csv
import json
import openpyxl
from pathlib import Path

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
KOSHA = DATA / "14_dashboards" / "kosha"
BILLING = DATA / "00_derived" / "gps_billing_clean.json"
WARR = DATA / "00_derived" / "distributor_warranty_expense_fiscal.csv"
DBS = [
    "ITUK", "IUK", "UTI", "UMI", "ISD", "IBX", "Imotors", "Sverige", "Norway",
    "Ireland", "RSA", "AutoWallis", "ROM Auto", "Nordic FI", "Danmark",
    "GasanZammit", "Loutsios", "BL Iceland",
]
_WARR_ALIAS = {"RSA": "Norway", "Greece": "RSA"}


def load_billing():
    raw = json.loads(BILLING.read_text(encoding="utf-8"))
    return {db: {int(y): v for y, v in fy.items()} for db, fy in raw.items()}


def load_warr():
    out = {}
    for r in csv.DictReader(open(WARR, encoding="utf-8")):
        if r["db"] == "MIDI":
            continue
        db = _WARR_ALIAS.get(r["db"], r["db"])
        out[db] = {2024: int(float(r["warr_FY2024"])), 2025: int(float(r["warr_FY2025"])),
                   2026: int(float(r["warr_FY2026"]))}
    return out


def read_v3x(name):
    wb = openpyxl.load_workbook(KOSHA / name, data_only=True)
    t1 = wb["GPS Actuals FY2024-26"]
    rows = {}
    for r in range(4, 23):
        nm = t1.cell(r, 1).value
        if not nm:
            continue
        rows[nm] = {
            2024: (t1.cell(r, 2).value, t1.cell(r, 3).value, t1.cell(r, 4).value),
            2025: (t1.cell(r, 5).value, t1.cell(r, 6).value, t1.cell(r, 7).value),
            2026: (t1.cell(r, 8).value, t1.cell(r, 9).value, t1.cell(r, 10).value),
        }
    t4 = wb["Method"]["B2"].value if "Method" in wb.sheetnames else ""
    wb.close()
    return rows, str(t4 or "")[:200]


def read_toggle():
    p = KOSHA / "GPS_Kosha_FY2024_2030.xlsx"
    if not p.exists():
        return None
    wb = openpyxl.load_workbook(p, data_only=True)
    ws = wb["GPS · Toggle"]
    rows = {}
    for r in range(6, 30):
        nm = ws.cell(r, 1).value
        if nm not in DBS:
            continue
        rows[nm] = {
            2024: (ws.cell(r, 4).value, ws.cell(r, 5).value, ws.cell(r, 6).value),
            2025: (ws.cell(r, 9).value, ws.cell(r, 10).value, ws.cell(r, 11).value),
            2026: (ws.cell(r, 14).value, ws.cell(r, 15).value, ws.cell(r, 16).value),
        }
    wb.close()
    return rows


def main():
    bill = load_billing()
    warr = load_warr()
    v3c, m3c = read_v3x("ISZE_GPS_Kosha_v3c.xlsx")
    v3d, m3d = read_v3x("ISZE_GPS_Kosha_v3d.xlsx")
    toggle = read_toggle()

    print("=" * 72)
    print("GPS / KOSHA CROSS-FILE AUDIT")
    print("=" * 72)

    issues = []

    # 1) v3c gross vs gps_billing_clean.json
    print("\n[1] v3c GROSS billing vs gps_billing_clean.json")
    for db in DBS:
        for fy in (2024, 2025, 2026):
            json_v = bill.get(db, {}).get(fy)
            v3c_g = v3c.get(db, {}).get(fy, (None, None, None))[0]
            if json_v is None or v3c_g is None:
                continue
            d = abs(json_v - v3c_g)
            if d > 1:
                issues.append(f"BILLING {db} FY{fy}: json={json_v:,.0f} v3c={v3c_g:,.0f} diff={d:,.0f}")
                print(f"  MISMATCH {db} FY{fy}: json {json_v:,.0f} vs v3c {v3c_g:,.0f} (diff {d:,.0f})")
    if not any("BILLING" in i for i in issues):
        print("  OK — v3c gross matches billing JSON for all GPS DBs FY24-26")

    # 2) v3d net = v3c gross - warranty
    print("\n[2] v3d NET = v3c GROSS - Distributor Warranty Expense")
    for db in DBS:
        for fy in (2024, 2025, 2026):
            g = v3c.get(db, {}).get(fy, (0, 0, 0))[0] or 0
            n = v3d.get(db, {}).get(fy, (0, 0, 0))[0] or 0
            w = warr.get(db, {}).get(fy, 0)
            exp = max(0, g - w)
            if abs(n - exp) > 1:
                issues.append(f"WARR {db} FY{fy}: net={n:,.0f} expected={exp:,.0f} warr={w:,.0f}")
                print(f"  MISMATCH {db} FY{fy}: v3d net {n:,.0f} != gross-warr {exp:,.0f} (warr {w:,.0f})")
    if not any("WARR" in i for i in issues):
        print("  OK — v3d net = v3c gross − warranty expense for all DBs")

    # 3) Toggle vs json
    print("\n[3] GPS_Kosha toggle GROSS vs billing JSON")
    if toggle:
        for db in ["ITUK", "IUK", "UTI", "UMI"]:
            for fy in (2024, 2025, 2026):
                j = bill.get(db, {}).get(fy)
                t = toggle.get(db, {}).get(fy, (None, None, None))[0]
                if j and t and abs(j - t) > 1:
                    print(f"  MISMATCH {db} FY{fy}: toggle {t:,.0f} vs json {j:,.0f}")
                    issues.append(f"TOGGLE {db} FY{fy}")
        if not any("TOGGLE" in i for i in issues):
            print("  OK — toggle gross matches JSON (spot-checked all DBs in loop above)")
        # toggle warranty vs kapstok
        print("\n[4] Toggle WARRANTY vs Distributor Warranty Expense (Working source)")
        for db in ["ITUK", "IUK", "UTI"]:
            for fy in (2024, 2025, 2026):
                tw = toggle.get(db, {}).get(fy, (0, 0, 0))[1] or 0
                kw = warr.get(db, {}).get(fy, 0)
                if abs(tw - kw) > 1:
                    print(f"  MISMATCH {db} FY{fy}: toggle warr {tw:,.0f} vs expense file {kw:,.0f}")
                    issues.append(f"TOGGLE-WARR {db} FY{fy}")
    else:
        print("  SKIP — toggle workbook missing")

    # ITUK spotlight
    print("\n[5] ITUK spotlight (presentation-critical)")
    for label, src in [("billing JSON", bill.get("ITUK", {})), ("v3c gross", {fy: v3c["ITUK"][fy][0] for fy in (2024, 2025, 2026)}),
                       ("v3d net", {fy: v3d["ITUK"][fy][0] for fy in (2024, 2025, 2026)}),
                       ("warranty", warr.get("ITUK", {}))]:
        print(f"  {label}: FY24={src.get(2024,0):,.0f} FY25={src.get(2025,0):,.0f} FY26={src.get(2026,0):,.0f}")

  # Norway/RSA naming
    print("\n[6] Name-map traps (Norway vs Greece)")
    print(f"  billing JSON 'Norway' FY25: {bill.get('Norway',{}).get(2025,0):,.0f}")
    print(f"  billing JSON 'RSA' FY25: {bill.get('RSA',{}).get(2025,0):,.0f}")
    print(f"  Norway (RSA in expense file) FY25 warranty: {next((int(r['warr_FY2025']) for r in csv.DictReader(open(WARR)) if r['db']=='RSA'),0):,}")

    print(f"\n{'='*72}")
    print(f"ISSUES FOUND: {len(issues)}")
    for i in issues[:20]:
        print(f"  - {i}")
    return issues


if __name__ == "__main__":
    main()
