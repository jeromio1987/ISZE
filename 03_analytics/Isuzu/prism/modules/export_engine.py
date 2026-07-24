"""
PRISM — Export Engine
=====================
Generates formatted Excel workbooks for GPS Dashboard data.

Sheets produced:
  1. Executive Summary — KPI tiles + top 10 table
  2. Spend per Unit    — full distributor table with traffic lights
  3. Year on Year      — year-matched SPU trends (V13 2020–2024 actual)
  4. Metadata          — data quality notes, exclusions, methodology

Used by: pages/2_GPS.py (Export section)
Depends on: GPS calculations from modules/gps_engine.py

Part of PRISM — Parts Revenue Intelligence & Sales Monitor
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import io

try:
    import openpyxl
    from openpyxl.styles import (
        PatternFill, Font, Alignment, Border, Side, numbers
    )
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference, LineChart
    from openpyxl.chart.series import DataPoint
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ─── ISZE BRAND COLOURS ──────────────────────────────────────────────────────
ISZE_DARK_BLUE = "1B3A6B"
ISZE_LIGHT_BLUE = "D6E4F0"
ISZE_ORANGE = "E87722"
GREY_HEADER = "F2F2F2"
WHITE = "FFFFFF"

# Traffic light thresholds for spend/unit (EUR)
TRAFFIC_LOW = 50    # red: below €50/unit
TRAFFIC_MID = 150   # amber: €50–€150/unit
# green: above €150/unit

RED_FILL = PatternFill("solid", fgColor="FFCCCC") if HAS_OPENPYXL else None
AMBER_FILL = PatternFill("solid", fgColor="FFE5B4") if HAS_OPENPYXL else None
GREEN_FILL = PatternFill("solid", fgColor="C8E6C9") if HAS_OPENPYXL else None
BLUE_FILL = PatternFill("solid", fgColor=ISZE_DARK_BLUE) if HAS_OPENPYXL else None
LIGHT_BLUE_FILL = PatternFill("solid", fgColor=ISZE_LIGHT_BLUE) if HAS_OPENPYXL else None
GREY_FILL = PatternFill("solid", fgColor=GREY_HEADER) if HAS_OPENPYXL else None


def _traffic_light_color(value, low=TRAFFIC_LOW, mid=TRAFFIC_MID):
    """Return fill colour based on spend/unit thresholds."""
    if pd.isna(value):
        return None
    if value < low:
        return RED_FILL
    elif value < mid:
        return AMBER_FILL
    else:
        return GREEN_FILL


def _header_style(ws, row, col, value, bold=True, bg=ISZE_DARK_BLUE, fg=WHITE, size=10):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = Font(bold=bold, color=fg, size=size)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    return cell


def _set_col_widths(ws, widths: dict):
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width


def export_gps_dashboard_excel(
    df_spu: pd.DataFrame,
    df_trend: pd.DataFrame,
    selected_year: int,
    year_type: str,
    output_path: str = None,
) -> bytes:
    """
    Generate the GPS Dashboard Excel workbook.

    Sheets:
      1. Executive Summary — KPI tiles + top/bottom table
      2. Spend per Unit — full distributor table with traffic lights
      3. Year on Year — year-matched spend/unit trends (V13 2020–2024 actual)
      4. Metadata — data quality, filters, export info

    Returns bytes (for Streamlit download) OR writes to output_path.
    """
    buf = io.BytesIO()
    wb = openpyxl.Workbook()

    # ── Sheet 1: Executive Summary ────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Executive Summary"
    _build_exec_summary(ws1, df_spu, selected_year, year_type)

    # ── Sheet 2: Spend per Unit (Full) ────────────────────────────────────────
    ws2 = wb.create_sheet("Spend per Unit")
    _build_spu_sheet(ws2, df_spu, selected_year, year_type)

    # ── Sheet 3: Trends ───────────────────────────────────────────────────────
    ws3 = wb.create_sheet("Year on Year")
    _build_trends_sheet(ws3, df_trend, year_type)

    # ── Sheet 4: Metadata ─────────────────────────────────────────────────────
    ws4 = wb.create_sheet("Metadata")
    _build_metadata_sheet(ws4, df_spu, selected_year, year_type)

    wb.save(buf)
    buf.seek(0)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(buf.read())
        buf.seek(0)

    return buf.read()


def _build_exec_summary(ws, df_spu, year, year_type):
    period_label = f"FY{year}" if year_type == "fiscal" else str(year)
    uio_note = "2024 proxy" if year > 2024 else f"{year} actual" if year in [2020, 2021, 2022, 2023, 2024] else "2024 proxy"

    # Title
    ws.merge_cells("A1:H1")
    t = ws["A1"]
    t.value = f"ISZE GPS Dashboard — Spend per Unit | {period_label}"
    t.font = Font(bold=True, color=WHITE, size=14)
    t.fill = PatternFill("solid", fgColor=ISZE_DARK_BLUE)
    t.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:H2")
    sub = ws["A2"]
    sub.value = f"Exported: {datetime.now().strftime('%d %b %Y %H:%M')} | UIO source: V13 Excel | UIO year: {uio_note}"
    sub.font = Font(italic=True, size=9, color="666666")
    sub.alignment = Alignment(horizontal='center')

    # KPI tiles (row 4)
    df_with_uio = df_spu[df_spu['uio_units'] > 0]
    total_sales = df_spu['total_sales_eur'].sum()
    n_dist = df_spu['distributor_code'].nunique()
    avg_spu = df_with_uio['spend_per_unit_eur'].mean()
    top_dist = df_with_uio.nlargest(1, 'spend_per_unit_eur')['distributor_code'].values
    top_val = df_with_uio['spend_per_unit_eur'].max()

    kpis = [
        ("Total Sales", f"€{total_sales:,.0f}"),
        ("Active Distributors", str(n_dist)),
        ("Avg Spend/Unit*", f"€{avg_spu:,.1f}"),
        ("Top Performer", f"{top_dist[0] if len(top_dist) else 'N/A'} (€{top_val:,.1f})"),
    ]

    for i, (label, val) in enumerate(kpis):
        col = i * 2 + 1
        ws.merge_cells(start_row=4, start_column=col, end_row=4, end_column=col+1)
        ws.merge_cells(start_row=5, start_column=col, end_row=5, end_column=col+1)
        lc = ws.cell(row=4, column=col, value=label)
        lc.font = Font(bold=True, size=9, color="666666")
        lc.alignment = Alignment(horizontal='center')
        vc = ws.cell(row=5, column=col, value=val)
        vc.font = Font(bold=True, size=13, color=ISZE_DARK_BLUE)
        vc.alignment = Alignment(horizontal='center')

    # Top/Bottom table (row 8+)
    ws.cell(row=7, column=1, value="* Based on distributors with UIO data available")
    ws.cell(row=7, column=1).font = Font(italic=True, size=8, color="888888")

    ws.merge_cells("A8:D8")
    h = ws.cell(row=8, column=1, value="TOP 10 MARKETS — SPEND PER UNIT")
    h.font = Font(bold=True, color=WHITE)
    h.fill = PatternFill("solid", fgColor=ISZE_DARK_BLUE)
    h.alignment = Alignment(horizontal='center')

    headers = ["Distributor", "Country", "Total Sales EUR", "Spend/Unit EUR"]
    for j, hd in enumerate(headers):
        _header_style(ws, 9, j+1, hd, bg=GREY_HEADER, fg="000000")

    top10 = df_with_uio.nlargest(10, 'spend_per_unit_eur').reset_index(drop=True)
    for ri, row in top10.iterrows():
        r = 10 + ri
        ws.cell(r, 1, row['distributor_code'])
        ws.cell(r, 2, row.get('country', ''))
        c_sales = ws.cell(r, 3, round(row['total_sales_eur'], 0))
        c_sales.number_format = '€#,##0'
        c_spu = ws.cell(r, 4, round(row['spend_per_unit_eur'], 1))
        c_spu.number_format = '€#,##0.0'
        fill = _traffic_light_color(row['spend_per_unit_eur'])
        if fill:
            c_spu.fill = fill
        # Alternate row shading
        if ri % 2 == 0:
            for col in range(1, 4):
                ws.cell(r, col).fill = PatternFill("solid", fgColor="F9F9F9")

    _set_col_widths(ws, {"A": 18, "B": 18, "C": 20, "D": 18, "E": 18, "F": 18, "G": 18, "H": 18})
    ws.freeze_panes = "A3"


def _build_spu_sheet(ws, df_spu, year, year_type):
    period_label = f"FY{year}" if year_type == "fiscal" else str(year)

    # Header row
    headers = [
        "Distributor Code", "Country", "Region",
        "Total Sales EUR", "Qty Sold", "Invoice Lines",
        "Credit Notes EUR", "UIO (year-matched)", "Spend/Unit EUR", "UIO Proxy?"
    ]
    ws.merge_cells("A1:J1")
    t = ws["A1"]
    t.value = f"Spend per Unit by Distributor | {period_label}"
    t.font = Font(bold=True, color=WHITE, size=12)
    t.fill = PatternFill("solid", fgColor=ISZE_DARK_BLUE)
    t.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25

    for j, h in enumerate(headers):
        _header_style(ws, 2, j+1, h, bg=GREY_HEADER, fg="000000")

    df_sorted = df_spu.sort_values('spend_per_unit_eur', ascending=False, na_position='last').reset_index(drop=True)

    for ri, row in df_sorted.iterrows():
        r = ri + 3
        ws.cell(r, 1, row['distributor_code'])
        ws.cell(r, 2, row.get('country', ''))
        ws.cell(r, 3, row.get('region', ''))

        c4 = ws.cell(r, 4, round(row['total_sales_eur'], 0))
        c4.number_format = '€#,##0'

        ws.cell(r, 5, int(row.get('total_qty', 0)))

        ws.cell(r, 6, int(row.get('invoice_lines', 0)))

        c7 = ws.cell(r, 7, round(row.get('credit_notes_eur', 0), 0))
        c7.number_format = '€#,##0'

        ws.cell(r, 8, int(row.get('uio_units', 0)))

        spu_val = row.get('spend_per_unit_eur')
        if pd.notna(spu_val):
            c9 = ws.cell(r, 9, round(spu_val, 1))
            c9.number_format = '€#,##0.0'
            fill = _traffic_light_color(spu_val)
            if fill:
                c9.fill = fill
        else:
            ws.cell(r, 9, "No UIO data")
            ws.cell(r, 9).font = Font(italic=True, color="888888")

        proxy = row.get('uio_proxy', False)
        wp = ws.cell(r, 10, "Yes (est.)" if proxy else "No")
        if proxy:
            wp.font = Font(italic=True, color="CC8800")

        # Alternate row
        if ri % 2 == 0:
            for col in range(1, 9):
                if not ws.cell(r, col).fill or ws.cell(r, col).fill.fgColor.rgb in ('00000000', ''):
                    ws.cell(r, col).fill = PatternFill("solid", fgColor="F9F9F9")

    _set_col_widths(ws, {
        "A": 18, "B": 16, "C": 12, "D": 18, "E": 12,
        "F": 14, "G": 18, "H": 12, "I": 16, "J": 14
    })

    # Legend
    legend_row = len(df_sorted) + 4
    ws.cell(legend_row, 1, "Traffic light: ").font = Font(bold=True, size=8)
    l1 = ws.cell(legend_row, 2, f"Green = >€{150}/unit")
    l1.fill = GREEN_FILL
    l2 = ws.cell(legend_row, 3, f"Amber = €{50}–€{150}/unit")
    l2.fill = AMBER_FILL
    l3 = ws.cell(legend_row, 4, f"Red = <€{50}/unit")
    l3.fill = RED_FILL

    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:J{len(df_sorted)+2}"



def _build_trends_sheet(ws, df_trend, year_type):
    """Year-on-year trends using year-matched UIO from V13 (2020–2024 actual, 2025/2026 = 2024 proxy)."""
    ws.merge_cells("A1:H1")
    t = ws["A1"]
    t.value = "Year-on-Year Spend per Unit Trends — Year-matched UIO (V13 2020–2024 actual; 2025/2026 = 2024 proxy)"
    t.font = Font(bold=True, color=WHITE, size=12)
    t.fill = PatternFill("solid", fgColor=ISZE_DARK_BLUE)
    t.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25

    if df_trend.empty:
        ws.cell(3, 1, "No trend data available")
        return

    headers = ["Distributor", "Country", "Region", "Year", "Total Sales EUR", "UIO Units", "Spend/Unit EUR", "UIO Proxy?"]
    for j, h in enumerate(headers):
        _header_style(ws, 2, j+1, h, bg=GREY_HEADER, fg="000000")

    df_sorted = df_trend.sort_values(['distributor_code', 'year_value']).reset_index(drop=True)

    for ri, row in df_sorted.iterrows():
        r = ri + 3
        ws.cell(r, 1, row.get('distributor_code', ''))
        ws.cell(r, 2, row.get('country', ''))
        ws.cell(r, 3, row.get('region', ''))
        ws.cell(r, 4, int(row.get('year_value', 0)))
        c5 = ws.cell(r, 5, round(row.get('total_sales_eur', 0), 0))
        c5.number_format = '€#,##0'
        ws.cell(r, 6, int(row.get('uio_units', 0)))
        spu = row.get('spend_per_unit_eur')
        if pd.notna(spu):
            c7 = ws.cell(r, 7, round(spu, 1))
            c7.number_format = '€#,##0.0'
            fill = _traffic_light_color(spu)
            if fill:
                c7.fill = fill
        proxy = row.get('uio_proxy', False)
        wp = ws.cell(r, 8, "Yes" if proxy else "No")
        if proxy:
            wp.font = Font(italic=True, color="CC8800")

    _set_col_widths(ws, {"A": 18, "B": 16, "C": 12, "D": 10, "E": 20, "F": 14, "G": 18, "H": 12})
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:H{len(df_sorted)+2}"


def _build_metadata_sheet(ws, df_spu, year, year_type):
    period_label = f"FY{year}" if year_type == "fiscal" else str(year)

    rows = [
        ("Export Date", datetime.now().strftime("%d %b %Y %H:%M")),
        ("Selected Period", period_label),
        ("Year Type", "Fiscal Year (Apr–Mar)" if year_type == "fiscal" else "Calendar Year (Jan–Dec)"),
        ("UIO Reference", "V13 Excel (ISUZU_UIO_Overview_2026_v13.xlsx) — 2020–2024 actual; 2025/2026 = 2024 proxy"),
        ("", ""),
        ("EXCLUSIONS APPLIED", ""),
        ("Isuzu Motors Germany GmbH", "Excluded — internal service dept (not distributor sales)"),
        ("MIDI EUROPE S.R.L.", "Excluded — Italy UIO (92k) not usable for GPS; no ISZE sales data"),
        ("IML / Isuzu Motors Limited", "Excluded — Japan parent (internal transfers)"),
        ("", ""),
        ("DISTRIBUTOR MAPPING NOTES", ""),
        ("IMOTORS / I Motors → PORTUGAL", "Variant name for Portugal distributor"),
        ("ISUZU IRELAND → IRELAND", "Variant of 'Isuzu Ireland' in SAP"),
        ("Petros Petropoulos (VEHICLE) → GREECE", "Variant of PETROS PETROPOULOS S.A."),
        ("ISUZU ROM AUTO SRL → ROMANIA", "Romania distributor — added, not in master file"),
        ("XXX ISUZU SALES DEUTSCHLAND → GERMANY", "Legacy/test code — mapped to Germany"),
        ("ISUZU TRUCK UK LIMITED → ITUK", "Variant spelling of ISUZU TRUCK (UK) LIMITED"),
        ("", ""),
        ("UIO SEGMENTATION (UK / ISRAEL)", ""),
        ("ITUK", "CV trucks only (LD + F-Series UIO from V13). 2024 UIO: 22,389"),
        ("IUK", "LCV D-Max only (IUK row in V13). 2024 UIO: 48,876"),
        ("UTI", "CV trucks only — Universal Trucks Israel (LD + MD from V13). 2024 UIO: 10,668"),
        ("UMI", "LCV D-Max only — Universal Motors Israel (UMI row in V13). 2024 UIO: 18,349"),
        ("All others", "Sum of all CV+LCV rows in V13 for that distributor (total addressable fleet)"),
        ("", ""),
        ("TRAFFIC LIGHT THRESHOLDS", ""),
        ("Green", "Spend/Unit > €150"),
        ("Amber", "Spend/Unit €50–€150"),
        ("Red", "Spend/Unit < €50"),
        ("", ""),
        ("DATA SOURCE", ""),
        ("Sales data", "sales_detailed_for_claude_full_fixed.tsv"),
        ("UIO data", "ISUZU_UIO_Overview_2026_v13.xlsx — sheet '1.UIO Overview' (2020–2024 actual per distributor)"),
        ("Distributor mapping", "distributor_master_mapping.csv"),
    ]

    ws.merge_cells("A1:B1")
    t = ws["A1"]
    t.value = "Data Quality & Methodology Notes"
    t.font = Font(bold=True, color=WHITE, size=12)
    t.fill = PatternFill("solid", fgColor=ISZE_DARK_BLUE)
    t.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25

    for ri, (key, val) in enumerate(rows):
        r = ri + 2
        kc = ws.cell(r, 1, key)
        ws.cell(r, 2, val)
        if key.isupper() and key != "" and key != "UIO REFERENCE YEAR":
            kc.font = Font(bold=True, color=ISZE_DARK_BLUE)
        if key == "":
            pass
        elif ri % 2 == 0 and key != "":
            kc.fill = PatternFill("solid", fgColor="F9F9F9")
            ws.cell(r, 2).fill = PatternFill("solid", fgColor="F9F9F9")

    _set_col_widths(ws, {"A": 40, "B": 60})
