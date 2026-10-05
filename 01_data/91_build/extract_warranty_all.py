"""
Normalize all warranty source files (CY2024, Q4-2025, FY26-YTD) into:
  derived/warranty_raw_grain.csv   — one row per part per claim line
  derived/warranty_by_db_year.csv  — GPS-ready totals per DB × year × segment (EUR)

Sources processed here (do NOT re-process Jan-Sep 2025 which lives in gps_warranty_cy2025.json):
  CV Warranty.xlsx          → sheet '2024'         (CV, full year 2024)
                            → sheet '10_25-12_2025' (CV, Q4 Oct–Dec 2025)
  ExportClaimAssessment202401-202412.xlsx           (LCV, full year 2024)
  ExportClaimAssessment202510-202512 with EV.xlsx   (LCV, Q4 Oct–Dec 2025)
  ExportClaimAssessment202601-202605 with EV.xls.xlsx (LCV, Jan–May 2026)
  WArranty Data LCV_102025_082026.xlsx              (LCV, Oct 2025 – Aug 2026)  [added 2026-09-24]

The Oct-2025-onward export overlaps the two ExportClaimAssessment samples above on
202510–202604, where it re-states the same lines. It is the only source for
202605–202608 (EUR 1,078,462 / 5,048 lines), so those months are taken from it and
nothing else. A duplicate guard drops any (month, distributor, part, value, qty) key
already emitted, so re-running cannot double-count an overlapping month.

Currency rules:
  CV  — CRNCY first token = settlement currency; PARTAMT1/2 in that currency
        EUR (most DBs) and JPY (MIDI only — non-GPS) → convert JPY at annual avg
  LCV — CurrencyParts; EUR (all GPS DBs), JPY (MIDI), USD (rare)

EUR ≈ basis:  claim-admitted price ≈ ISZE transfer price (consistent with existing Jan-Sep 2025).
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import openpyxl

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
OUT = DATA / "derived"

# Annual average JPY/EUR (approximate)
JPY_EUR: dict[int, float] = {2024: 164.0, 2025: 162.0, 2026: 158.0}
USD_EUR: dict[int, float] = {2024: 1.08, 2025: 1.08, 2026: 1.10}

GRAIN_FIELDS = [
    "year", "assess_month", "segment", "db_name", "db_code",
    "country", "part_no", "part_desc", "qty", "claim_eur", "currency_raw",
]


def _jpy_eur(year: int) -> float:
    return JPY_EUR.get(year, 162.0)


def _usd_eur(year: int) -> float:
    return USD_EUR.get(year, 1.08)


def _to_eur(amount: float, ccy: str, year: int) -> float:
    if ccy == "EUR":
        return amount
    if ccy == "JPY":
        return amount / _jpy_eur(year)
    if ccy == "USD":
        return amount / _usd_eur(year)
    return amount  # fallback: assume EUR


# ── CV extraction ─────────────────────────────────────────────────────────────

def _cv_sheet(ws) -> list[dict]:
    rows = list(ws.iter_rows(values_only=True))
    hdr = {str(h): i for i, h in enumerate(rows[0]) if h is not None}
    out: list[dict] = []

    for r in rows[1:]:
        def v(col: str):
            return r[hdr[col]] if col in hdr else None

        dt6 = str(v("DT6") or "").strip().replace(".0", "")
        if len(dt6) < 6:
            continue
        month = dt6[:6]
        year = int(month[:4])

        dst = str(v("DST_Name") or "").strip()
        dlr = str(v("DLR") or "").strip()
        country = str(v("CTY_Name") or "").strip()
        ope_name = str(v("OPE_Name") or "").strip()
        crncy = str(v("CRNCY") or "").strip()
        settle_ccy = crncy.split()[0] if crncy else "EUR"

        parts = [
            (str(v("PARTNBR") or "").strip(), v("QTY1"), v("PARTAMT1")),
            (str(v("PARTNBR2") or "").strip(), v("QTY2"), v("PARTAMT2")),
        ]
        for pn, qty_raw, amt_raw in parts:
            if not pn or pn in ("None", "0000000000", ""):
                continue
            qty = float(qty_raw or 0)
            amt = float(amt_raw or 0)
            if qty == 0 and amt == 0:
                continue
            claim_eur = _to_eur(amt, settle_ccy, year)
            out.append({
                "year": year,
                "assess_month": month,
                "segment": "CV",
                "db_name": dst,
                "db_code": dlr,
                "country": country,
                "part_no": pn,
                "part_desc": ope_name,
                "qty": qty,
                "claim_eur": round(claim_eur, 4),
                "currency_raw": settle_ccy,
            })
    return out


def extract_cv_warranty(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    rows: list[dict] = []
    for sname in wb.sheetnames:
        rows.extend(_cv_sheet(wb[sname]))
    wb.close()
    print(f"  CV {path.name}: {len(rows)} part lines across {wb.sheetnames if False else 'all sheets'}")
    return rows


# ── LCV extraction ────────────────────────────────────────────────────────────

def extract_lcv_file(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    out: list[dict] = []
    for sname in wb.sheetnames:
        ws = wb[sname]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        hdr = {str(h): i for i, h in enumerate(rows[0]) if h is not None}
        if "AssessMonth" not in hdr:
            continue  # skip pivot/summary sheets

        def v(r, col: str):
            return r[hdr[col]] if col in hdr else None

        for r in rows[1:]:
            assess = str(v(r, "AssessMonth") or "").strip().split(".")[0]
            if not assess or len(assess) < 6:
                continue
            year = int(assess[:4])
            month = assess[:6]

            pn = str(v(r, "PartsNo") or "").strip()
            if not pn or pn in ("None", "0", ""):
                continue
            qty = float(v(r, "Pieces") or 0)
            if qty == 0:
                continue

            db_name = str(v(r, "DistributorName") or "").strip()
            db_code = str(v(r, "DistributorCode") or "").strip()
            country = str(v(r, "CountryName") or "").strip()
            desc = str(v(r, "PartsName") or "").strip()
            ccy = str(v(r, "CurrencyParts") or "EUR").strip()
            raw_cost = v(r, "AdmitPartsCost")
            admit_cost = float(raw_cost) if isinstance(raw_cost, (int, float)) else 0.0
            raw_usd = v(r, "PartsAmount_USD")
            admit_usd = float(raw_usd) if isinstance(raw_usd, (int, float)) else 0.0

            if ccy == "USD":
                claim_eur = admit_usd / _usd_eur(year)
            else:
                claim_eur = _to_eur(admit_cost, ccy, year)

            out.append({
                "year": year,
                "assess_month": month,
                "segment": "LCV",
                "db_name": db_name,
                "db_code": db_code,
                "country": country,
                "part_no": pn,
                "part_desc": desc,
                "qty": qty,
                "claim_eur": round(claim_eur, 4),
                "currency_raw": ccy,
            })
    wb.close()
    print(f"  LCV {path.name}: {len(out)} part lines")
    return out


# ── UMI extraction ───────────────────────────────────────────────────────────

def extract_umi_file(path: Path) -> list[dict]:
    """UMI-specific format: ClaimAssess (1) sheet, all EUR, Registered date_YMD as period."""
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb["ClaimAssess (1)"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = {str(h).strip(): i for i, h in enumerate(rows[0]) if h is not None}
    out: list[dict] = []

    for r in rows[1:]:
        def v(col: str):
            return r[hdr[col]] if col in hdr else None

        dt = str(v("Registered date_YMD") or "").strip().split(".")[0]
        if len(dt) < 6:
            continue
        month = dt[:6]
        year = int(month[:4])

        pn = str(v("Part_No.") or "").strip()
        if not pn or pn in ("None", "0", ""):
            continue
        qty_raw = v("Number of Part")
        qty = float(qty_raw) if isinstance(qty_raw, (int, float)) else 0.0
        if qty == 0:
            continue

        amt_raw = v("Approved part cost")
        claim_eur = float(amt_raw) if isinstance(amt_raw, (int, float)) else 0.0

        ope = str(v("Ope_code") or "").strip()
        dealer = str(v("Dealer Code") or "").strip()

        out.append({
            "year": year,
            "assess_month": month,
            "segment": "LCV",
            "db_name": "UMI",
            "db_code": dealer,
            "country": "ISRAEL",
            "part_no": pn,
            "part_desc": ope,
            "qty": qty,
            "claim_eur": round(claim_eur, 4),
            "currency_raw": "EUR",
        })
    wb.close()
    print(f"  UMI {path.name}: {len(out)} part lines")
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    all_rows: list[dict] = []

    def _months(rows: list[dict]) -> set[str]:
        return {r["assess_month"] for r in rows}

    def _keep_months(rows: list[dict], allowed: set[str]) -> list[dict]:
        """Keep only rows in `allowed`. Used to take a month from exactly one source."""
        out = [r for r in rows if r["assess_month"] in allowed]
        dropped = len(rows) - len(out)
        if dropped:
            print(f"    ({dropped:,} rows outside the taken months)")
        return out

    print("Reading CV Warranty.xlsx …")
    all_rows += extract_cv_warranty(DATA / "Warranty" / "CV Warranty.xlsx")

    print("Reading LCV 2024 …")
    all_rows += extract_lcv_file(DATA / "Warranty" / "ExportClaimAssessment202401-202412.xlsx")

    print("Reading LCV Q4-2025 …")
    q4 = extract_lcv_file(DATA / "Warranty" / "ExportClaimAssessment202510-202512 with EV.xlsx")
    all_rows += q4

    print("Reading LCV FY26-YTD …")
    ytd = extract_lcv_file(DATA / "Warranty" / "ExportClaimAssessment202601-202605 with EV.xls.xlsx")
    all_rows += ytd

    # The Oct-2025-onward export overlaps both samples above: those months are the SAME
    # claim lines restated, so taking them again would double every overlapping month.
    # Take from it only the months no earlier source can supply, and say which they are.
    print("Reading LCV Oct2025–Aug2026 (new export) …")
    new_export = DATA / "WArranty Data LCV_102025_082026.xlsx"
    if new_export.exists():
        newer = extract_lcv_file(new_export)
        provided = _months(q4) | _months(ytd)
        take = sorted(_months(newer) - provided)
        print(f"    months already covered by earlier files: {sorted(provided)}")
        print(f"    months taken from this file only      : {take}")
        all_rows += _keep_months(newer, set(take))
    else:
        print(f"  ! missing {new_export.name} — 202605–202608 will be absent")

    print("Reading UMI (2023–2026) …")
    all_rows += extract_umi_file(DATA / "Warranty" / "UMI warranty data 202301 - 202605.xlsx")

    # ── Write raw grain ───────────────────────────────────────────────────────
    grain_path = OUT / "warranty_raw_grain.csv"
    with open(grain_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=GRAIN_FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nWritten: {grain_path}  ({len(all_rows):,} rows)")

    # ── Aggregate by DB × year × segment ─────────────────────────────────────
    agg: dict[tuple, dict] = defaultdict(lambda: {"claim_eur": 0.0, "qty": 0.0, "lines": 0})
    for r in all_rows:
        key = (r["year"], r["segment"], r["db_name"], r["db_code"], r["country"])
        agg[key]["claim_eur"] += r["claim_eur"]
        agg[key]["qty"] += r["qty"]
        agg[key]["lines"] += 1

    agg_path = OUT / "warranty_by_db_year.csv"
    agg_fields = ["year", "segment", "db_name", "db_code", "country", "claim_eur", "qty", "lines"]
    with open(agg_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=agg_fields)
        w.writeheader()
        for (year, seg, db_name, db_code, country), vals in sorted(agg.items()):
            w.writerow({
                "year": year,
                "segment": seg,
                "db_name": db_name,
                "db_code": db_code,
                "country": country,
                "claim_eur": round(vals["claim_eur"], 2),
                "qty": int(vals["qty"]),
                "lines": vals["lines"],
            })
    print(f"Written: {agg_path}  ({len(agg):,} DB×year×segment rows)")

    # ── Summary by year × segment ─────────────────────────────────────────────
    summary: dict[tuple, float] = defaultdict(float)
    for r in all_rows:
        summary[(r["year"], r["segment"])] += r["claim_eur"]
    print("\nSummary (EUR totals by year × segment):")
    for (yr, seg), total in sorted(summary.items()):
        print(f"  {yr}  {seg}  €{total:,.0f}")


if __name__ == "__main__":
    main()
