#!/usr/bin/env python3
"""UTI FY27 GPS incentive model (internal). Rebuild: python build_uti_gps_incentive_proposals.py"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import openpyxl
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "04_tools"))
from build_gps_v5 import CLASS_RATE, read_uio_classes, read_warranty  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "UTI_FY27_GPS_Incentive_Model.xlsx"
OUT_ALT = Path(__file__).resolve().parents[1] / "UTI_FY27_GPS_Incentive_Model_rebuild.xlsx"

RED, YELLOW, GREEN, AMBER, BLUE, WHITE = "CC0E1E", "FFFF00", "E2EFDA", "FFF2CC", "DDEBF7", "FFFFFF"
THIN = Border(*(Side(style="thin", color="BFBFBF"),) * 4)

UTI_GROSS = {2024: 3_055_768, 2025: 2_468_339, 2026: 2_936_400}

NETWORK_KB = [
    ("ITUK", 85_000), ("IUK", 78_000), ("UMI", 38_000), ("UTI", 36_000),
    ("IBX", 28_000), ("ISD", 37_000), ("Portugal", 22_000), ("Ireland", 16_000),
    ("Norway", 21_000), ("Sweden", 17_000), ("KTK", 15_000),
]

# Calc block row anchors on Model sheet (column B = value)
R = {
    "bp_k": 40, "stretch_k": 41, "uplift_k": 42, "uplift_pct": 43,
    "ld_uio": 44, "md_uio": 45, "total_uio": 46, "max_spend": 47,
    "stretch_eur": 48, "net_bill": 49, "gps_active": 50, "gps_gross": 51,
    "eur_uio": 52, "d_gps": 53, "d_eur_uio": 54, "gps_bonus": 55, "total_inc": 56,
    "implied_bruto": 57, "gap_gps": 58,
}
# FY2026 actuals on Data sheet row 6 (for deltas)
DATA_FY26_ROW = 6


def F(**kw):
    kw.setdefault("name", "Arial")
    kw.setdefault("size", 10)
    return Font(**kw)


def fl(c: str) -> PatternFill:
    return PatternFill("solid", fgColor=c)


def hdr_row(ws, r: int, n: int) -> None:
    for c in range(1, n + 1):
        x = ws.cell(r, c)
        x.font = F(bold=True, color=WHITE)
        x.fill = fl(RED)
        x.alignment = Alignment(horizontal="center", wrap_text=True, vertical="center")
        x.border = THIN


def inp(cell, val, fmt=None):
    cell.value = val
    cell.font = F(color="0000FF", bold=True)
    cell.fill = fl(YELLOW)
    if fmt:
        cell.number_format = fmt


def dv_list(ws, cell_range: str, options: str) -> None:
    d = DataValidation(type="list", formula1=f'"{options}"', allow_blank=False)
    ws.add_data_validation(d)
    d.add(cell_range)


def ms_for_year(uio_data: dict, fy: int) -> tuple[int, int, int, int]:
    classes = uio_data.get("UTI", {}).get(fy, {})
    ld = classes.get("LD", 0)
    md = classes.get("MD", 0) + classes.get("F-Series", 0)
    total = ld + md
    ms = int(ld * CLASS_RATE["LD"] + md * CLASS_RATE["MD"])
    return ld, md, total, ms


def _b(key: str) -> str:
    return f"Model!B{R[key]}"


def sheet_model(wb, warr: dict, uio_data: dict) -> None:
    ws = wb.create_sheet("Model")
    ws["A1"] = "UTI FY26/27 GPS incentive — INTERNAL"
    ws["A1"].font = F(bold=True, size=14, color=RED)
    ws["A2"] = (
        "Decision: YES — stretch €3,298K bruto (+€200K vs BP) + 39% GPS → €16K bonus on top of €36K regular"
    )
    ws["A2"].font = F(bold=True, color="006100")
    ws["A2"].fill = fl(GREEN)
    ws.merge_cells("A2:D2")

    # ── Inputs (yellow) ───────────────────────────────────────────────────────
    ws["A4"] = "INPUTS — edit yellow cells only"
    ws["A4"].font = F(bold=True, size=11, color=RED)

    ws["A5"], ws["D5"] = "WARRANTY VIEW", "GROSS or NET"
    inp(ws["B5"], "GROSS", "@")
    dv_list(ws, "B5", "GROSS,NET")

    ws["A6"], ws["D6"] = "Warranty FY2027 estimate (€)", "Proxy: last closed FY in file"
    inp(ws["B6"], warr[2026], "€#,##0")

    ws["A7"], ws["D7"] = "UIO BASIS", "FY2026 = last FY · FY2027 = projected"
    inp(ws["B7"], "FY2027", "@")
    dv_list(ws, "B7", "FY2026,FY2027")

    ws["A8"], ws["D8"] = "BP bruto FY27 (€K)", "Baseline kickback"
    inp(ws["B8"], 3098.1, "#,##0.0")

    ws["A9"], ws["D9"] = "Stretch bruto (€K)", "BP + €200K"
    inp(ws["B9"], 3298.0, "#,##0.0")

    ws["A10"], ws["D10"] = "GPS target %", "Full FY measure"
    inp(ws["B10"], 0.39, "0.0%")

    ws["A11"], ws["D11"] = "Bonus tier 1 GPS% / €", ""
    inp(ws["B11"], 0.38, "0.0%")
    inp(ws["C11"], 8000, "€#,##0")

    ws["A12"], ws["D12"] = "Bonus tier 2 GPS% / €", ""
    inp(ws["B12"], 0.39, "0.0%")
    inp(ws["C12"], 16000, "€#,##0")

    ws["A13"], ws["D13"] = "Regular kickback (€)", "Not GPS-linked"
    inp(ws["B13"], 36000, "€#,##0")

    ws["A14"], ws["D14"] = "GPS bonus pool (€)", "Network additional pool"
    inp(ws["B14"], 200000, "€#,##0")

    ws["A15"], ws["D15"] = "LD / MD rate €/UIO", ""
    inp(ws["B15"], CLASS_RATE["LD"], "€#,##0")
    inp(ws["C15"], CLASS_RATE["MD"], "€#,##0")

    # UIO lookup (same sheet — avoids cross-tab refs)
    ld26, md26, tot26, _ = ms_for_year(uio_data, 2026)
    ld27, md27, tot27, _ = ms_for_year(uio_data, 2027)
    ws["A17"] = "UIO lookup (read-only)"
    ws["A17"].font = F(bold=True, size=9, color="666666")
    for col, h in enumerate(["Basis", "LD", "MD", "Total"], 1):
        ws.cell(18, col, h).font = F(bold=True, size=9)
    ws["A19"], ws["B19"], ws["C19"], ws["D19"] = "FY2026", ld26, md26, tot26
    ws["A20"], ws["B20"], ws["C20"], ws["D20"] = "FY2027", ld27, md27, tot27

    # ── Summary (references calc block below) ─────────────────────────────────
    ws["A22"] = "SUMMARY"
    ws["A22"].font = F(bold=True, size=11, color=RED)
    hdr_row(ws, 23, 3)
    ws.cell(23, 1, "Metric")
    ws.cell(23, 2, "Value")
    ws.cell(23, 3, "Note")

    summary = [
        ("BP bruto FY27 (€K)", f"={_b('bp_k')}", "#,##0.0", "Baseline"),
        ("Stretch bruto (€K)", f"={_b('stretch_k')}", "#,##0.0", "Agreed target"),
        ("Uplift vs BP (€K)", f"={_b('uplift_k')}", "#,##0.0", ""),
        ("UIO basis", "=Model!B7", "@", ""),
        ("Total UIO", f"={_b('total_uio')}", "#,##0", ""),
        ("Max spend", f"={_b('max_spend')}", "€#,##0", ""),
        ("Bruto (stretch)", f"={_b('stretch_eur')}", "€#,##0", ""),
        ("GPS% at stretch bruto", f"={_b('gps_active')}", "0.0%", "Implied — not bonus trigger"),
        ("GPS target (bonus)", "=Model!B10", "0.0%", "39% = tier for €16K"),
        ("€/UIO", f"={_b('eur_uio')}", "€#,##0", ""),
        ("Δ GPS vs FY26", f"={_b('d_gps')}", "+0.0%", ""),
        ("Regular kickback", "=Model!B13", "€#,##0", "€36K"),
        ("GPS bonus (agreed tier)", f"={_b('gps_bonus')}", "€#,##0", "€16K if targets met at FY close"),
        ("Total incentive", f"={_b('total_inc')}", "€#,##0", "€52K if both conditions met"),
        ("Pool remaining", "=Data!B49", "€#,##0", "After all allocations"),
    ]
    for i, (lab, formula, fmt, note) in enumerate(summary, 24):
        ws.cell(i, 1, lab)
        ws.cell(i, 2, formula)
        ws.cell(i, 2).number_format = fmt
        ws.cell(i, 3, note)
        if "GPS bonus" in lab or "Total incentive" in lab:
            ws.cell(i, 2).fill = fl(GREEN)

    ws["A39"] = (
        '=CONCATENATE("FY26/27: BP €",TEXT(B8,"#,##0.0"),"K → €36K · Stretch €",TEXT(B9,"#,##0"),'
        '"K + ",TEXT(B10,"0%")," GPS → +€",TEXT(B55,"#,##0")," = €",TEXT(B56,"#,##0")," total if met")'
    )
    ws.merge_cells("A39:D39")
    ws["A39"].alignment = Alignment(wrap_text=True)

    # ── Calc engine (hidden-ish — row 40+) ────────────────────────────────────
    ws["A38"] = "Calc engine"
    ws["A38"].font = F(size=9, color="999999")

    fy26_gps_gross = UTI_GROSS[2026] / ms_for_year(uio_data, 2026)[3]
    fy26_eur_uio = UTI_GROSS[2026] / tot26

    calcs = [
        ("BP bruto €K", "=B8", "#,##0.0"),
        ("Stretch €K", "=B9", "#,##0.0"),
        ("Uplift €K", f"=B{R['stretch_k']}-B{R['bp_k']}", "#,##0.0"),
        ("Uplift %", f"=B{R['uplift_k']}/B{R['bp_k']}", "0.0%"),
        ("LD UIO", '=IF(B7="FY2027",B20,B19)', "#,##0"),
        ("MD UIO", '=IF(B7="FY2027",C20,C19)', "#,##0"),
        ("Total UIO", f"=B{R['ld_uio']}+B{R['md_uio']}", "#,##0"),
        ("Max spend", f"=B{R['ld_uio']}*B15+B{R['md_uio']}*C15", "€#,##0"),
        ("Stretch bruto €", f"=B{R['stretch_k']}*1000", "€#,##0"),
        ("Net billing €", f'=B{R["stretch_eur"]}-IF(B5="NET",B6,0)', "€#,##0"),
        ("GPS% active", f'=IF(B5="NET",B{R["net_bill"]}/B{R["max_spend"]},B{R["stretch_eur"]}/B{R["max_spend"]})', "0.0%"),
        ("GPS% gross", f"=B{R['stretch_eur']}/B{R['max_spend']}", "0.0%"),
        ("€/UIO", f'=IF(B5="NET",B{R["net_bill"]}/B{R["total_uio"]},B{R["stretch_eur"]}/B{R["total_uio"]})', "€#,##0"),
        ("Δ GPS vs FY26", f"=B{R['gps_active']}-{fy26_gps_gross:.6f}", "+0.0%"),
        ("Δ €/UIO vs FY26", f"=B{R['eur_uio']}-{fy26_eur_uio:.2f}", "€#,##0"),
        ("GPS bonus € (agreed tier)", f'=IF(B10>=B12,C12,IF(B10>=B11,C11,0))', "€#,##0"),
        ("Total incentive €", f"=B13+B{R['gps_bonus']}", "€#,##0"),
        ("Implied bruto @ GPS target", "=B10*B47", "€#,##0"),
        ("Gap vs GPS target bruto", f"=B{R['implied_bruto']}-B{R['stretch_eur']}", "€#,##0"),
    ]
    for i, (lab, formula, fmt) in enumerate(calcs):
        row = R["bp_k"] + i
        ws.cell(row, 1, lab)
        ws.cell(row, 1).font = F(size=9, color="999999")
        ws.cell(row, 2, formula)
        ws.cell(row, 2).number_format = fmt

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 36


def sheet_data(wb, uio_data: dict, warr: dict) -> None:
    ws = wb.create_sheet("Data")
    ws["A1"] = "UIO · GPS history · sensitivity · pool"
    ws["A1"].font = F(bold=True, size=13, color=RED)

    # ── UIO / GPS by FY ───────────────────────────────────────────────────────
    hdr = [
        "FY", "LD UIO", "MD UIO", "Total", "Max spend", "Bruto €", "Warranty €",
        "GPS% gross", "GPS% net", "€/UIO gross",
    ]
    for i, h in enumerate(hdr, 1):
        ws.cell(3, i, h)
    hdr_row(ws, 3, len(hdr))

    r = 4
    for fy in (2024, 2025, 2026, 2027):
        ld, md, tot, ms = ms_for_year(uio_data, fy)
        gross = UTI_GROSS.get(fy)
        w = warr.get(fy) if fy <= 2026 else None
        ws.cell(r, 1, f"FY{fy}")
        ws.cell(r, 2, ld)
        ws.cell(r, 3, md)
        ws.cell(r, 4, tot)
        ws.cell(r, 5, ms)
        ws.cell(r, 5).number_format = "€#,##0"
        if gross:
            ws.cell(r, 6, gross)
        elif fy == 2027:
            ws.cell(r, 6, "=Model!B48")
        ws.cell(r, 6).number_format = "€#,##0"
        if w is not None:
            ws.cell(r, 7, w)
        elif fy == 2027:
            ws.cell(r, 7, "=Model!B6")
        ws.cell(r, 7).number_format = "€#,##0"
        ws.cell(r, 8, f'=IF(D{r}>0,F{r}/E{r},"")')
        ws.cell(r, 8).number_format = "0.0%"
        ws.cell(r, 9, f'=IF(D{r}>0,(F{r}-G{r})/E{r},"")')
        ws.cell(r, 9).number_format = "0.0%"
        ws.cell(r, 10, f'=IF(D{r}>0,F{r}/D{r},"")')
        ws.cell(r, 10).number_format = "€#,##0"
        if fy == 2026:
            for c in range(1, 11):
                ws.cell(r, c).fill = fl(AMBER)
        if fy == 2027:
            for c in range(1, 11):
                ws.cell(r, c).fill = fl(BLUE)
        r += 1

    # ── GPS sensitivity (starts row 12) ─────────────────────────────────────────
    sens = 12
    ws.cell(sens, 1, "GPS sensitivity (0.5pp steps)").font = F(bold=True)
    sens += 1
    sh = ["GPS%", "Implied bruto €", "€/UIO", "Δ GPS vs FY26", "Bonus tier", "GPS bonus €", "Total €"]
    for i, h in enumerate(sh, 1):
        ws.cell(sens, i, h)
    hdr_row(ws, sens, len(sh))
    start = sens + 1
    fy26_gps = UTI_GROSS[2026] / ms_for_year(uio_data, 2026)[3]
    for i, pct in enumerate([x / 200 for x in range(68, 85)]):
        row = start + i
        ws.cell(row, 1, pct)
        ws.cell(row, 1).number_format = "0.0%"
        ws.cell(row, 2, f"=A{row}*Model!B47")
        ws.cell(row, 2).number_format = "€#,##0"
        ws.cell(row, 3, f"=B{row}/Model!B46")
        ws.cell(row, 3).number_format = "€#,##0"
        ws.cell(row, 4, f"=A{row}-{fy26_gps:.6f}")
        ws.cell(row, 4).number_format = "+0.0%"
        ws.cell(row, 5, f'=IF(A{row}>=Model!B12,"Tier 2",IF(A{row}>=Model!B11,"Tier 1","—"))')
        ws.cell(row, 6, f'=IF(A{row}>=Model!B12,Model!C12,IF(A{row}>=Model!B11,Model!C11,0))')
        ws.cell(row, 6).number_format = "€#,##0"
        ws.cell(row, 7, f"=Model!B13+F{row}")
        ws.cell(row, 7).number_format = "€#,##0"

    ws.conditional_formatting.add(
        f"A{start}:G{start + 16}",
        FormulaRule(
            formula=[f"AND(A{start}>=Model!B10-0.005,A{start}<=Model!B10+0.005)"],
            fill=fl(GREEN),
        ),
    )

    # ── Pool (starts row 32) ────────────────────────────────────────────────────
    pool = 32
    ws.cell(pool, 1, "€200K GPS bonus pool").font = F(bold=True)
    ws.cell(pool + 1, 1, (
        "UTI €16K = agreed allocation at GPS target tier — conditional: stretch bruto + GPS% both at FY close"
    ))
    ws.merge_cells(f"A{pool + 1}:C{pool + 1}")
    ws.cell(pool + 1, 1).font = F(italic=True, size=9)
    pool += 2
    ws.cell(pool, 1, "Distributor")
    ws.cell(pool, 2, "Regular KB")
    ws.cell(pool, 3, "GPS bonus")
    hdr_row(ws, pool, 3)
    pr = pool + 1
    for name, kb in NETWORK_KB:
        ws.cell(pr, 1, name)
        ws.cell(pr, 2, kb)
        ws.cell(pr, 2).number_format = "€#,##0"
        if name == "UTI":
            ws.cell(pr, 3, "=Model!B55")
            ws.cell(pr, 3).fill = fl(GREEN)
        else:
            ws.cell(pr, 3, 0)
            ws.cell(pr, 3).font = F(color="0000FF")
            ws.cell(pr, 3).fill = fl(YELLOW)
        ws.cell(pr, 3).number_format = "€#,##0"
        pr += 1
    ws.cell(pr, 1, "TOTAL").font = F(bold=True)
    ws.cell(pr, 2, f"=SUM(B{pool + 1}:B{pr - 1})")
    ws.cell(pr, 2).number_format = "€#,##0"
    ws.cell(pr, 3, f"=SUM(C{pool + 1}:C{pr - 1})")
    ws.cell(pr, 3).number_format = "€#,##0"
    ws.cell(pr + 2, 1, "Pool budget")
    ws.cell(pr + 2, 2, "=Model!B14")
    ws.cell(pr + 2, 2).number_format = "€#,##0"
    ws.cell(pr + 3, 1, "Allocated")
    ws.cell(pr + 3, 2, f"=C{pr}")
    ws.cell(pr + 3, 2).number_format = "€#,##0"
    ws.cell(pr + 4, 1, "Remaining")
    ws.cell(pr + 4, 2, f"=B{pr + 2}-B{pr + 3}")
    ws.cell(pr + 4, 2).number_format = "€#,##0"

    for col, w in enumerate([12, 10, 10, 10, 14, 14, 14, 10, 10, 12], 1):
        ws.column_dimensions[get_column_letter(col)].width = w


def sheet_notes(wb, warr: dict) -> None:
    ws = wb.create_sheet("Notes")
    ws["A1"] = "Assumptions & caveats"
    ws["A1"].font = F(bold=True, size=13, color=RED)
    w3yr = (warr[2024] + warr[2025] + warr[2026]) / 3
    lines = [
        f"Generated {date.today().isoformat()} · Internal only · Do not share with UTI.",
        "",
        "HOW TO USE: Sheet「Model」— yellow inputs + summary. Sheet「Data」— detail tables.",
        "",
        "DECISION: Stretch €3,298K bruto + 39% GPS → €16K bonus on €36K regular (€52K total).",
        "FY2027 = Apr 2026 – Mar 2027. Rebuild: UTI/_build/build_uti_gps_incentive_proposals.py",
        "",
        "WARRANTY — why €260K is not '3 months':",
        f"  warr_FY2026 = full year Apr 2025 – Mar 2026 (€{warr[2026]:,.0f}), not current-FY YTD.",
        "  FY2027 (Apr 2026 – Mar 2027) has no warranty column in file yet.",
        f"  3-yr average: €{w3yr:,.0f}. Default GROSS view unless finance confirms NET.",
        "",
    ]
    for i, t in enumerate(lines, 3):
        ws.cell(i, 1, t)

    # Risks table
    rr = len(lines) + 4
    ws.cell(rr, 1, "Risks & veronderstellingen").font = F(bold=True)
    rr += 1
    hdr = ["#", "Area", "Issue", "Mitigation"]
    for i, h in enumerate(hdr, 1):
        ws.cell(rr, i, h)
    hdr_row(ws, rr, len(hdr))
    risks = [
        (1, "Warranty", "€260K is full FY Apr25–Mar26 — easy to misread as Q1 YTD", "Default GROSS; see Notes"),
        (2, "UIO", "FY2027 UIO projected — not confirmed by UTI", "Reconcile parc before sign-off"),
        (3, "Billing", "UTI CV routes via UMI payer 1797", "Monthly reconcile"),
        (4, "GPS%", "Capture = bruto ÷ max spend — not PMS/filter", "Separate comms from filter KPIs"),
        (5, "Stretch", "Bruto stretch + GPS target are two separate FY-close conditions", "Bonus tier uses GPS target %, not implied GPS at stretch bruto"),
        (6, "Pool", "Only UTI modelled — other DBs manual on Data sheet", "Allocate before policy"),
        (7, "Timing", "Full FY2027 measurement — no interim payout", "Policy"),
    ]
    for i, row in enumerate(risks, rr + 1):
        for j, val in enumerate(row, 1):
            ws.cell(i, j, val)
            ws.cell(i, j).alignment = Alignment(wrap_text=True)

    ws.column_dimensions["A"].width = 90
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 42
    ws.column_dimensions["D"].width = 28


def build() -> Path:
    uio_data = read_uio_classes()
    warr = read_warranty()["UTI"]

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    sheet_model(wb, warr, uio_data)
    sheet_data(wb, uio_data, warr)
    sheet_notes(wb, warr)

    for path in (OUT, OUT_ALT):
        try:
            wb.save(path)
            return path
        except PermissionError:
            continue
    raise PermissionError("Close the Excel file and rebuild.")


if __name__ == "__main__":
    print(f"Wrote {build()}")
