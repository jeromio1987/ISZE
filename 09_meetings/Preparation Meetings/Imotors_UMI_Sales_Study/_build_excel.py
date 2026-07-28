# -*- coding: utf-8 -*-
"""Build Excel workbook from study_data.json — I Motors + UMI Sales/Order study."""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "study_data.json").read_text(encoding="utf-8"))
XLSX = OUT / "ISZE_Imotors_UMI_Sales_Order_Study.xlsx"

NAVY = PatternFill("solid", fgColor="1A2B4A")
TERR = PatternFill("solid", fgColor="C0552D")
HEAD = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
TITLE = Font(name="Calibri", bold=True, color="1A2B4A", size=14)
BOLD = Font(name="Calibri", bold=True, size=11)
BODY = Font(name="Calibri", size=10)
WRAP = Alignment(wrap_text=True, vertical="top")
NUM = Alignment(horizontal="right", vertical="center")
THIN = Border(
    left=Side(style="thin", color="D9D3C8"),
    right=Side(style="thin", color="D9D3C8"),
    top=Side(style="thin", color="D9D3C8"),
    bottom=Side(style="thin", color="D9D3C8"),
)
ZEBRA = PatternFill("solid", fgColor="F7F4EE")


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row, c)
        cell.fill = NAVY
        cell.font = HEAD
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = THIN


def autosize(ws, widths):
    # Pre-delivery check requires col B (and description-like cols) >= 28
    fixed = []
    for i, w in enumerate(widths):
        if i == 1:  # column B (0-based index 1)
            fixed.append(max(w, 28))
        else:
            fixed.append(w)
    for i, w in enumerate(fixed, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_table(ws, start_row, headers, rows, money_cols=(), pct_cols=()):
    for j, h in enumerate(headers, 1):
        ws.cell(start_row, j, h)
    style_header(ws, start_row, len(headers))
    for i, row in enumerate(rows):
        r = start_row + 1 + i
        for j, val in enumerate(row, 1):
            cell = ws.cell(r, j, val)
            cell.font = BODY
            cell.border = THIN
            cell.alignment = WRAP if j == 1 or isinstance(val, str) else NUM
            if i % 2:
                cell.fill = ZEBRA
            if j in money_cols and isinstance(val, (int, float)):
                cell.number_format = '#,##0'
            if j in pct_cols and isinstance(val, (int, float)):
                cell.number_format = '0.0'


def sheet_readme(wb):
    ws = wb.active
    ws.title = "00_README"
    ws["A1"] = "ISZE — I Motors & UMI Sales & Order Study"
    ws["A1"].font = TITLE
    lines = [
        "",
        f"Generated: {DATA['generated']}",
        DATA["fiscal_definition"],
        f"Local billing max: {DATA['local_billing_max']}",
        DATA["scope"],
        "",
        "Sheets:",
        "01_Executive — FY + H1 headline contrast",
        "02_Imotors_FY — FY2024/FY2025 totals, SaTy, concentration, GPS/PMS",
        "03_UMI_FY — same for UMI (not blended with UTI)",
        "04_PBI_H1 — Power BI SALES/ORDER H1 CY2026 drills",
        "05_Imotors_PN — top PN + movers",
        "06_UMI_PN — top PN + movers",
        "07_PMS_gaps — CY2025 total-capture gaps by category",
        "",
        "Rules: primary = total sales / total PMS capture. UMI ≠ UTI. No raw line billing.",
        "Companion HTML: FULL_SALES_ORDER_STUDY.html",
    ]
    for i, t in enumerate(lines, 2):
        ws.cell(i, 1, t).font = BODY
        ws.cell(i, 1).alignment = WRAP
    ws.column_dimensions["A"].width = 100
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22


def sheet_exec(wb):
    ws = wb.create_sheet("01_Executive")
    ws["A1"] = "Executive contrast — I Motors vs UMI"
    ws["A1"].font = TITLE
    imo = next(d for d in DATA["distributors"] if d["key"] == "IMOTORS")
    umi = next(d for d in DATA["distributors"] if d["key"] == "UMI")
    pbi = DATA["pbi_h1_2026"]
    drills = pbi.get("drills", {})
    order = pbi.get("order", {})

    headers = ["Metric", "I Motors", "UMI", "Note"]
    imo24 = imo["fy_totals"]["2024"]["sales_eur"]
    imo25 = imo["fy_totals"]["2025"]["sales_eur"]
    umi24 = umi["fy_totals"]["2024"]["sales_eur"]
    umi25 = umi["fy_totals"]["2025"]["sales_eur"]
    rows = [
        ["FY2024 sales €", imo24, umi24, "Apr2024–Mar2025"],
        ["FY2025 sales €", imo25, umi25, "Apr2025–Mar2026"],
        ["FY YoY %", round(100 * (imo25 - imo24) / imo24, 1), round(100 * (umi25 - umi24) / umi24, 1), ""],
        ["H1 CY2026 sales €", drills["IMOTORS"]["sales_eur"], drills["UMI"]["sales_eur"], pbi["period"]],
        ["H1 sales YoY %", drills["IMOTORS"]["yoy_pct"], drills["UMI"]["yoy_pct"], "Power BI SALES"],
        [
            "H1 demand €",
            order["customers"]["IMOTORS"]["demand_eur"],
            order["customers"]["UMI"]["demand_eur"],
            "Power BI ORDER",
        ],
        [
            "H1 demand YoY %",
            order["customers"]["IMOTORS"]["yoy_pct"],
            order["customers"]["UMI"]["yoy_pct"],
            "",
        ],
        [
            "H1 sales–demand gap €",
            order["sales_vs_demand"]["IMOTORS"]["gap_eur"],
            order["sales_vs_demand"]["UMI"]["gap_eur"],
            "Demand − sales",
        ],
        [
            "PMS total capture CY2025",
            round(100 * imo["pms_summary"][0]["capture_rate_total_wtd"], 1),
            round(100 * umi["pms_summary"][0]["capture_rate_total_wtd"], 1),
            "%",
        ],
        [
            "PMS revenue gap €",
            imo["pms_summary"][0]["revenue_gap_eur"],
            umi["pms_summary"][0]["revenue_gap_eur"],
            "total lens",
        ],
        [
            "Top-10 PN share FY2025 %",
            imo["concentration"]["FY2025"]["top10_share_pct"],
            umi["concentration"]["FY2025"]["top10_share_pct"],
            "",
        ],
    ]
    write_table(ws, 3, headers, rows, money_cols={2, 3}, pct_cols=set())
    autosize(ws, [32, 18, 18, 40])
    ws.freeze_panes = "A4"
    ws["A20"] = "UMI ≠ UTI. Israel market demand up is largely UTI — do not blend."
    ws["A20"].font = BOLD
    ws["A20"].alignment = WRAP


def sheet_db_fy(wb, key, title):
    db = next(d for d in DATA["distributors"] if d["key"] == key)
    ws = wb.create_sheet(title)
    ws["A1"] = f"{db['label']} — FY totals & mix"
    ws["A1"].font = TITLE
    ws["A2"] = f"SAP: {db['sap_sold_to']} · code {db['distributor_code']}"
    ws["A2"].font = BODY

    headers = ["Fiscal year", "Sales €", "Qty", "Lines", "Distinct PN", "Months", "Date min", "Date max"]
    rows = []
    for fy in sorted(db["fy_totals"].keys()):
        t = db["fy_totals"][fy]
        rows.append(
            [
                int(fy),
                t["sales_eur"],
                t["qty"],
                t["lines"],
                t["distinct_pn"],
                t["months"],
                t["date_min"],
                t["date_max"],
            ]
        )
    write_table(ws, 4, headers, rows, money_cols={2, 3})

    r0 = 4 + len(rows) + 3
    ws.cell(r0, 1, "SaTy share % by FY").font = BOLD
    saty_h = ["FY", "SaTy", "Sales €", "Share %", "Qty", "Lines"]
    saty_rows = [
        [x["fiscal_year"], x["saty"], x["sales_eur"], x["share_pct"], x["qty"], x["lines"]]
        for x in db["by_saty"]
        if x["fiscal_year"] in (2024, 2025)
    ]
    write_table(ws, r0 + 1, saty_h, saty_rows, money_cols={3}, pct_cols={4})

    r1 = r0 + 1 + len(saty_rows) + 3
    ws.cell(r1, 1, "GPS / PMS").font = BOLD
    gps_h = ["Year", "Sales €", "UIO", "SPU €", "GPS capture vs max", "Traffic light"]
    gps_rows = [
        [
            g["year"],
            g["sales_eur"],
            g["uio"],
            g["spu"],
            g["gps_capture_vs_max"],
            g["traffic_light"],
        ]
        for g in db["gps"]
    ]
    write_table(ws, r1 + 1, gps_h, gps_rows, money_cols={2, 4})
    if db.get("pms_summary"):
        p = db["pms_summary"][0]
        rr = r1 + 1 + len(gps_rows) + 2
        ws.cell(rr, 1, "PMS CY2025 total capture %").font = BOLD
        ws.cell(rr, 2, round(100 * p["capture_rate_total_wtd"], 2))
        ws.cell(rr + 1, 1, "PMS genuine capture %")
        ws.cell(rr + 1, 2, round(100 * p["capture_rate_genuine_wtd"], 2))
        ws.cell(rr + 2, 1, "Revenue gap €")
        ws.cell(rr + 2, 2, p["revenue_gap_eur"]).number_format = "#,##0"
        ws.cell(rr + 3, 1, "Oil filter capture %")
        ws.cell(rr + 3, 2, round(100 * p["oil_filter_capture"], 2))
        ws.cell(rr + 4, 1, "Top gap categories")
        ws.cell(rr + 4, 2, p["top_gap_categories"]).alignment = WRAP

    conc = db["concentration"]["FY2025"]
    rc = r1 + 1 + len(gps_rows) + 10
    ws.cell(rc, 1, "Concentration FY2025").font = BOLD
    for i, (lab, val) in enumerate(
        [
            ("Top-10 share %", conc["top10_share_pct"]),
            ("Top-25 share %", conc["top25_share_pct"]),
            ("Top-50 share %", conc["top50_share_pct"]),
            ("PNs for 80%", conc["pn_for_80pct"]),
            ("Distinct PN", conc["distinct_pn"]),
        ]
    ):
        ws.cell(rc + 1 + i, 1, lab)
        ws.cell(rc + 1 + i, 2, val)

    autosize(ws, [22, 14, 14, 12, 14, 10, 14, 14])
    ws.freeze_panes = "A5"


def sheet_pbi(wb):
    ws = wb.create_sheet("04_PBI_H1")
    ws["A1"] = "Power BI H1 CY2026 — SALES drills + ORDER"
    ws["A1"].font = TITLE
    pbi = DATA["pbi_h1_2026"]
    drills = pbi["drills"]
    order = pbi["order"]
    ws["A2"] = f"{pbi['period']} · {pbi['source']}"
    ws["A2"].alignment = WRAP

    headers = ["Customer", "Sales €", "LY €", "YoY %", "Demand €", "Demand YoY %", "Gap €"]
    rows = []
    for key in ("IMOTORS", "UMI"):
        d = drills[key]
        o = order["customers"][key]
        g = order["sales_vs_demand"][key]
        rows.append(
            [
                key,
                d["sales_eur"],
                d["ly_eur"],
                d["yoy_pct"],
                o["demand_eur"],
                o["yoy_pct"],
                g["gap_eur"],
            ]
        )
    write_table(ws, 4, headers, rows, money_cols={2, 3, 5, 7}, pct_cols={4, 6})

    r = 10
    for key, title in (("IMOTORS", "I Motors"), ("UMI", "UMI")):
        ws.cell(r, 1, f"{title} — H1 category").font = BOLD
        cats = drills[key].get("category", [])
        write_table(
            ws,
            r + 1,
            ["Category", "€", "Share %", "YoY %"],
            [[c["name"], c["eur"], c["pct"], c.get("yoy")] for c in cats],
            money_cols={2},
            pct_cols={3, 4},
        )
        r = r + 1 + len(cats) + 3
        ws.cell(r, 1, f"{title} — H1 source").font = BOLD
        srcs = drills[key].get("source", [])
        write_table(
            ws,
            r + 1,
            ["Source", "€", "Share %", "YoY %"],
            [[s["name"], s["eur"], s["pct"], s.get("yoy")] for s in srcs],
            money_cols={2},
            pct_cols={3, 4},
        )
        r = r + 1 + len(srcs) + 3

    autosize(ws, [28, 14, 12, 10, 14, 14, 12])
    ws.freeze_panes = "A5"


def sheet_pn(wb, key, title):
    db = next(d for d in DATA["distributors"] if d["key"] == key)
    ws = wb.create_sheet(title)
    ws["A1"] = f"{db['label']} — PN deep dive FY2025"
    ws["A1"].font = TITLE
    pn = [x for x in db["top_pn"] if x["fiscal_year"] == 2025][:40]
    write_table(
        ws,
        3,
        ["Rank", "Part number", "Description", "Sales €", "Share %", "Qty", "Lines"],
        [
            [x["rank"], x["part_number"], x["description"], x["sales_eur"], x["share_pct"], x["qty"], x["lines"]]
            for x in pn
        ],
        money_cols={4},
        pct_cols={5},
    )
    r = 3 + len(pn) + 3
    ws.cell(r, 1, "Gainers FY2024 → FY2025").font = BOLD
    g = db["pn_movers_fy24_to_fy25"]["gainers"][:20]
    write_table(
        ws,
        r + 1,
        ["PN", "Description", "FY24 €", "FY25 €", "Delta €"],
        [[x["part_number"], x["description"], x["fy_a_eur"], x["fy_b_eur"], x["delta_eur"]] for x in g],
        money_cols={3, 4, 5},
    )
    r2 = r + 1 + len(g) + 3
    ws.cell(r2, 1, "Losers FY2024 → FY2025").font = BOLD
    losers = db["pn_movers_fy24_to_fy25"]["losers"][:20]
    write_table(
        ws,
        r2 + 1,
        ["PN", "Description", "FY24 €", "FY25 €", "Delta €"],
        [[x["part_number"], x["description"], x["fy_a_eur"], x["fy_b_eur"], x["delta_eur"]] for x in losers],
        money_cols={3, 4, 5},
    )
    autosize(ws, [8, 18, 42, 12, 10, 10, 10])
    ws.freeze_panes = "A4"


def sheet_pms(wb):
    ws = wb.create_sheet("07_PMS_gaps")
    ws["A1"] = "PMS category gaps CY2025 — total sales lens"
    ws["A1"].font = TITLE
    r = 3
    for key, title in (("IMOTORS", "I Motors"), ("UMI", "UMI")):
        db = next(d for d in DATA["distributors"] if d["key"] == key)
        ws.cell(r, 1, title).font = BOLD
        cats = sorted(db["pms_categories_total"], key=lambda x: -x["revenue_gap_eur"])
        write_table(
            ws,
            r + 1,
            ["Category", "Capture rate", "Actual rev €", "Gap €"],
            [
                [c["category"], c["capture_rate"], c["actual_rev_eur"], c["revenue_gap_eur"]]
                for c in cats
            ],
            money_cols={3, 4},
        )
        # format capture as %
        for i in range(len(cats)):
            ws.cell(r + 2 + i, 2).number_format = "0.0%"
        r = r + 1 + len(cats) + 3
    autosize(ws, [28, 14, 14, 14])
    ws.freeze_panes = "A3"


def main():
    wb = Workbook()
    sheet_readme(wb)
    sheet_exec(wb)
    sheet_db_fy(wb, "IMOTORS", "02_Imotors_FY")
    sheet_db_fy(wb, "UMI", "03_UMI_FY")
    sheet_pbi(wb)
    sheet_pn(wb, "IMOTORS", "05_Imotors_PN")
    sheet_pn(wb, "UMI", "06_UMI_PN")
    sheet_pms(wb)
    wb.save(XLSX)
    print("wrote", XLSX)


if __name__ == "__main__":
    main()
