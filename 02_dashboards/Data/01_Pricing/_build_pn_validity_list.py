"""Simple 2-col list: Part Number | Validity date window for SAP pull."""
from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

PRICING = Path(__file__).resolve().parent
SRC = PRICING / "SAP_Pricing_History_Data_Request_by_Year.xlsx"
OUT = PRICING / "SAP_Pull_PN_Validity_List.xlsx"

WINDOWS = {
    "2023": ("01/01/2023", "31/12/2023"),
    "2024": ("01/01/2024", "31/01/2025"),
    "2025": ("01/02/2025", "17/03/2026"),
}


def sanitize_xlsx_for_excel_desktop(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}
    wb_xml = files["xl/workbook.xml"].decode("utf-8")
    wb_xml = re.sub(r"<workbookProtection\b[^/]*/>", "", wb_xml)
    wb_xml = re.sub(
        r"<workbookProtection\b[^>]*>.*?</workbookProtection>",
        "",
        wb_xml,
        flags=re.DOTALL,
    )
    files["xl/workbook.xml"] = wb_xml.encode("utf-8")
    styles = files["xl/styles.xml"].decode("utf-8")
    styles = styles.replace("<patternFill/>", '<patternFill patternType="none"/>')
    styles = styles.replace("<patternFill />", '<patternFill patternType="none"/>')
    styles = re.sub(r'rgb="00([0-9A-Fa-f]{6})"', r'rgb="FF\1"', styles)
    styles = re.sub(r'\s+pivotButton="0"', "", styles)
    styles = re.sub(r'\s+quotePrefix="0"', "", styles)
    files["xl/styles.xml"] = styles.encode("utf-8")
    rels = files["xl/_rels/workbook.xml.rels"].decode("utf-8")
    rels = rels.replace('Target="/xl/worksheets/', 'Target="worksheets/')
    rels = rels.replace('Target="/xl/theme/', 'Target="theme/')
    rels = rels.replace('Target="/xl/styles.xml"', 'Target="styles.xml"')
    rels = rels.replace('Target="/xl/sharedStrings.xml"', 'Target="sharedStrings.xml"')
    files["xl/_rels/workbook.xml.rels"] = rels.encode("utf-8")
    tmp = path.with_suffix(".sanitize.tmp.xlsx")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)
    tmp.replace(path)


def main() -> None:
    wb_in = load_workbook(SRC, read_only=True, data_only=True)
    ws_in = wb_in["Parts_To_Pull"]
    rows = list(ws_in.iter_rows(values_only=True))
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == "part_number")
    hdr = list(rows[hdr_i])
    idx = {h: i for i, h in enumerate(hdr)}

    pairs: list[tuple[str, str]] = []
    for r in rows[hdr_i + 1 :]:
        if not r or not r[0]:
            continue
        pn = str(r[0]).strip()
        for yr, (vf, vt) in WINDOWS.items():
            y_pr00 = str(r[idx[f"Pull_PR00_{yr}"]] or "").strip().upper() == "Y"
            y_zpr1 = str(r[idx[f"Pull_ZPR1_{yr}"]] or "").strip().upper() == "Y"
            if y_pr00 or y_zpr1:
                pairs.append((pn, f"{vf} - {vt}"))
    wb_in.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "PN_Validity"
    ws["A1"] = "Part Number"
    ws["B1"] = "PR00 Validity date (Valid From - Valid To)"
    hdr_fill = PatternFill("solid", fgColor="FF1F4E79")
    for col in (1, 2):
        cell = ws.cell(1, col)
        cell.fill = hdr_fill
        cell.font = Font(bold=True, color="FFFFFFFF")
    thin = Border(
        left=Side(style="thin", color="FFB0B0B0"),
        right=Side(style="thin", color="FFB0B0B0"),
        top=Side(style="thin", color="FFB0B0B0"),
        bottom=Side(style="thin", color="FFB0B0B0"),
    )
    for i, (pn, validity) in enumerate(pairs, start=2):
        a = ws.cell(i, 1, pn)
        b = ws.cell(i, 2, validity)
        a.number_format = "@"
        a.alignment = Alignment(horizontal="left")
        a.border = thin
        b.border = thin

    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 42
    ws.auto_filter.ref = f"A1:B{len(pairs) + 1}"
    ws.freeze_panes = "A2"

    note = wb.create_sheet("Note", 1)
    note["A1"] = "Simple pull list for SAP"
    note["A2"] = (
        "Column A = part number. Column B = PR00 Valid From - Valid To for the SAP extract."
    )
    note["A3"] = "PR00 only. One row per PN x window where a pull is needed."
    note["A4"] = (
        "Windows: 2023 = 01/01/2023-31/12/2023 | "
        "2024 = 01/01/2024-31/01/2025 | "
        "2025 = 01/02/2025-17/03/2026"
    )
    note["A5"] = f"Total rows: {len(pairs)}"
    note.column_dimensions["A"].width = 110

    wb.save(OUT)
    sanitize_xlsx_for_excel_desktop(OUT)

    wb2 = load_workbook(OUT, read_only=True, data_only=True)
    ws2 = wb2["PN_Validity"]
    n = ws2.max_row - 1
    c = Counter(r[1] for r in ws2.iter_rows(min_row=2, values_only=True) if r[1])
    sample = list(ws2.iter_rows(min_row=1, max_row=5, values_only=True))
    wb2.close()
    print(f"OK {OUT}")
    print(f"rows={n}")
    print(f"by_window={dict(c)}")
    print(f"sample={sample}")


if __name__ == "__main__":
    main()
