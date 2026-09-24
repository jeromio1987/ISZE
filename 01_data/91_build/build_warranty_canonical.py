"""
Distributor Warranty Expense — per distributor per FISCAL year (EUR)
====================================================================
FY = Apr(y-1)–Mar(y)  —  same basis as GPS billing (REPA6 / AssessMonth).

Sources:
  CV  — 06_Warranty/CV Warranty.xlsx, Warranty_CV_2025.xlsx, CV warranty01_03_2026.xlsx
  LCV — grain files + gps_warranty_cy2025.json (Jan–Sep 2025 lump split 3/9→FY25, 6/9→FY26)
  UMI — grain from UMI warranty file

Output:
  00_derived/distributor_warranty_expense_fiscal.csv  (management name)
  00_derived/warranty_by_db_FY_canonical.csv          (legacy alias, identical)
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import openpyxl
import pandas as pd

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
WARR_DIR = DATA / "06_Warranty"
GRAIN = DATA / "00_derived" / "warranty_raw_grain.csv"
JSON = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\gps_warranty_cy2025.json")
OUT = DATA / "00_derived" / "distributor_warranty_expense_fiscal.csv"
OUT_LEGACY = DATA / "00_derived" / "warranty_by_db_FY_canonical.csv"

FX_JPY_EUR = 163.7

# LCV / grain db_name → canonical v3c name
LCV_TO_CANON = {
    "ISUZU (UK)": "IUK",
    "RSA": "RSA",
    "PETROS PETROPOULOS": "Greece",
    "Isuzu Sverige AB": "Sverige",
    "IMOTORS LDA": "Imotors",
    "Isuzu Ireland 2020 Unlimited Company": "Ireland",
    "WAE LTD.": "AutoWallis",
    "Isuzu Motor Finland OY": "Nordic FI",
    "ISUZU Danmark": "Danmark",
    "ISUZU ROM AUTO SRL": "ROM Auto",
    "A. LOUTSIOS & SONS": "Loutsios",
    "GASANZAMMIT MOTORS LIMITED": "GasanZammit",
    "BL ehf.": "BL Iceland",
    "UMI": "UMI",
}
# json keys (ex-UMI) → canonical
JSON_TO_CANON = {
    "ITUK": "ITUK", "IUK": "IUK", "UTI": "UTI", "GERMANY": "ISD", "BELGIUM": "IBX",
    "IRELAND": "Ireland", "NORWAY": "RSA", "SWEDEN": "Sverige", "DENMARK": "Danmark",
    "FINLAND": "Nordic FI", "ICELAND": "BL Iceland", "CYPRUS": "Loutsios",
    "GREECE": "Greece", "MALTA": "GasanZammit", "ROMANIA": "ROM Auto",
    "HUNGARY": "AutoWallis", "PORTUGAL": "Imotors",
}
ISD_PREFIX = "ISUZU SALES DEUTSCHLAND"
IBX_PREFIX = ("ISUZU BENELUX", "Isuzu Benelux")

CV_DBS = {"ITUK", "UTI", "Ireland", "Greece", "Loutsios", "GasanZammit", "Imotors", "ISD", "RSA", "MIDI"}
GPS_DBS = [
    "ITUK", "IUK", "UTI", "UMI", "ISD", "RSA", "Sverige", "IBX", "Imotors", "Ireland",
    "Greece", "AutoWallis", "ROM Auto", "Loutsios", "GasanZammit", "Nordic FI", "Danmark", "BL Iceland",
]


def fiscal_fy(yyyymm: str) -> int:
    y, m = int(yyyymm[:4]), int(yyyymm[4:6])
    return y + 1 if m >= 4 else y


PURE_CV = {"ITUK", "UTI"}


def _cv_rows_from_xlsx(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out: list[dict] = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        hdr = {str(h): i for i, h in enumerate(rows[0]) if h is not None}
        repa_key = "REPA6" if "REPA6" in hdr else None
        if not repa_key or "DST_Name" not in hdr or "TTL_PARTS" not in hdr:
            continue  # skip summary / pivot sheets
        for r in rows[1:]:
            repa = str(r[hdr[repa_key]] or "").strip().replace(".0", "")
            if len(repa) < 6:
                continue
            crncy = str(r[hdr.get("CRNCY", -1)] or "EUR").strip()
            amt = float(r[hdr["TTL_PARTS"]] or 0)
            if amt == 0:
                continue
            eur = amt / FX_JPY_EUR if crncy.startswith("JPY") else amt
            dst = str(r[hdr["DST_Name"]]).strip()
            out.append({
                "dst": dst,
                "repa": repa,
                "crncy": crncy,
                "amt": amt,
                "eur": eur,
                "fy": fiscal_fy(repa[:6]),
            })
    wb.close()
    return out


def load_cv_warranty() -> dict[str, dict[int, float]]:
    """CV EUR by canonical DB × fiscal FY."""
    files = [
        WARR_DIR / "CV Warranty.xlsx",
        WARR_DIR / "Warranty_CV_2025.xlsx",
        WARR_DIR / "CV warranty01_03_2026.xlsx",
    ]
    rows: list[dict] = []
    for f in files:
        if f.exists():
            rows.extend(_cv_rows_from_xlsx(f))
    # dedupe identical claim lines across overlapping exports
    seen: set[tuple] = set()
    tot: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        key = (r["dst"], r["repa"], r["crncy"], r["amt"])
        if key in seen:
            continue
        seen.add(key)
        db = r["dst"] if r["dst"] != "PETROS PETROPOULOS" else "Greece"
        if "MIDI" in db.upper():
            db = "MIDI"
        tot[db][r["fy"]] += r["eur"]
    return tot


def _canon_lcv_name(name: str) -> str | None:
    if name in LCV_TO_CANON:
        return LCV_TO_CANON[name]
    if name.startswith(ISD_PREFIX):
        return "ISD"
    if any(name.startswith(p) for p in IBX_PREFIX):
        return "IBX"
    return None


def load_grain_warranty() -> dict[str, dict[int, float]]:
    tot: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    if not GRAIN.exists():
        return tot
    for r in csv.DictReader(open(GRAIN, encoding="utf-8")):
        fy = fiscal_fy(r["assess_month"])
        seg = r["segment"]
        eur = float(r["claim_eur"])
        if seg == "CV":
            db = r["db_name"]
            if db == "PETROS PETROPOULOS":
                db = "Greece"
            if "MIDI" in db.upper():
                db = "MIDI"
        else:
            db = _canon_lcv_name(r["db_name"])
            if not db:
                continue
        tot[db][fy] += eur
    return tot


def load_json_split() -> dict[str, dict[int, float]]:
    """Jan–Sep 2025 json lump → fiscal split (Jan–Mar FY25, Apr–Sep FY26)."""
    tot: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    if not JSON.exists():
        return tot
    data = json.loads(JSON.read_text(encoding="utf-8"))
    for key, eur in data.get("warranty_eur", {}).items():
        if not eur:
            continue
        db = JSON_TO_CANON.get(key)
        if not db:
            continue
        tot[db][2025] += eur * 3 / 9
        tot[db][2026] += eur * 6 / 9
    return tot


def merge(*maps: dict[str, dict[int, float]]) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for m in maps:
        for db, yrs in m.items():
            for fy, eur in yrs.items():
                out[db][fy] += eur
    return out


def build_all() -> tuple[dict[str, tuple[int, int, int]], dict[str, int]]:
    """Return (FY2024–FY2026 per DB, FY2027 per DB).

    FY2027 is carried separately on purpose. Every reader of this file reads the
    three FY2024–FY2026 columns by name, so the new column is appended and never
    re-orders them. FY2027 is a part-year (Apr 2026 – Aug 2026 at most) and must
    not be put in a chart beside a full year without saying so.
    """
    cv = load_cv_warranty()
    grain = load_grain_warranty()
    jsplit = load_json_split()
    combined = merge(grain, jsplit)

    # Pure-CV distributors: monthly REPA6 in CV exports is authoritative
    for db in PURE_CV:
        combined[db] = defaultdict(float)
        for fy in (2024, 2025, 2026, 2027):
            combined[db][fy] = cv.get(db, {}).get(fy, 0.0)

    if "MIDI" in cv:
        combined["MIDI"] = defaultdict(float, cv["MIDI"])

    result: dict[str, tuple[int, int, int]] = {}
    fy27: dict[str, int] = {}
    dbs = list(GPS_DBS)
    if "MIDI" in cv or "MIDI" in combined:
        dbs.append("MIDI")
    for db in dbs:
        d = combined.get(db, {})
        result[db] = (round(d.get(2024, 0)), round(d.get(2025, 0)), round(d.get(2026, 0)))
        fy27[db] = round(d.get(2027, 0))
    return result, fy27


def build() -> dict[str, tuple[int, int, int]]:
    """Backwards-compatible: the FY2024–FY2026 triple only."""
    return build_all()[0]


def main() -> None:
    warr, fy27 = build_all()
    notes = {
        "RSA": "=Norway distributor",
        "Greece": "=Petros Petropoulos",
        "MIDI": "MIDI Europe group; JPY-converted; non-GPS channel",
    }
    # Column order is fixed: the three readers of this file read FY2024-FY2026 by
    # name. FY2027 is appended and empty (0) wherever no claim line exists yet.
    rows = [["db", "warr_FY2024", "warr_FY2025", "warr_FY2026", "warr_FY2027_partial", "note"]]
    rows += [[db, a, b, c, fy27.get(db, 0), notes.get(db, "")] for db, (a, b, c) in warr.items()]
    for path in (OUT, OUT_LEGACY):
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

    t24 = sum(v[0] for v in warr.values())
    t25 = sum(v[1] for v in warr.values())
    t26 = sum(v[2] for v in warr.values())
    t27 = sum(fy27.values())
    print(f"Saved -> {OUT}  (+ legacy alias {OUT_LEGACY.name})  ({len(warr)} DBs)")
    print(f"Network warranty (fiscal FY): FY2024 EUR{t24/1e6:.2f}M  FY2025 EUR{t25/1e6:.2f}M  FY2026 EUR{t26/1e6:.2f}M")
    print(f"FY2027 part-year (Apr-Aug 2026 only, pickup claims): EUR{t27/1e3:.0f}k — do not chart beside a full year")
    for db in ("ITUK", "UTI", "IUK", "UMI", "ISD"):
        print(f"  {db:6} {warr[db]}  FY27p {fy27.get(db, 0):,}")


if __name__ == "__main__":
    main()
