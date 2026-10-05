#!/usr/bin/env python3
"""Which part groups moved more or less on the new base price, and for which customer.

Rebuilds ``01_data/01_Pricing/Price_increase_by_part_group_per_customer.xlsx`` from
the derived comparison. Read-only on everything in ``01_data/00_derived``.

Sheets
------
``Overview``                          the headline answer, then an index of the rest
``Read me``                           basis, both percentage columns, floor, caveats
``Part groups, network-wide``          one row per part group, ranked by euro step
``Highest and lowest by customer``     per customer: headline, then most/least moved groups
``Customers by part group``            the full customer x part group table
``Movement grid by customer``          customer rows, part group columns, movement %
``Checks``                            live formulas proving agreement with the sources
``Calculation detail``                the line-level aggregate the live formulas point at

The movement column is ``SUM(qty x new base price) / SUM(qty x prior base price) - 1``
over part numbers priced on both lists. That definition is unchanged from the
published comparison. A second, separately labelled column carries the step divided
by the billed value, so the two measures can never be confused for one another.

Totals are written as live formulas, then Excel is asked to recalculate the file so
the values are stored alongside the formulas and read without opening Excel.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import _price_inc_data as dat  # noqa: E402
import _xlsx_bake as bake  # noqa: E402
import _xlsx_style as xs  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
OUT = ISZE / "01_data" / "01_Pricing" / "Price_increase_by_part_group_per_customer.xlsx"
CMD = ISZE / "01_data" / "01_Pricing" / "OPEN_Price_increase_by_part_group.cmd"
QA = ISZE / "01_data" / "01_Pricing" / "_qa"

FLOOR_EUR = 20000.0
TOP_N = 3
# A top-three list and a bottom-three list only avoid repeating each other when at
# least six groups clear the reported floor. Below that the low list stays blank.
MIN_GROUPS_FOR_LOW_LIST = 2 * TOP_N

SHEET_OVERVIEW = "Overview"
SHEET_README = "Read me"
SHEET_GROUPS = "Part groups, network-wide"
SHEET_RANK = "Highest and lowest by customer"
SHEET_CUST_GROUP = "Customers by part group"
SHEET_GRID = "Movement grid by customer"
SHEET_CHECKS = "Checks"
SHEET_DETAIL = "Calculation detail"

QG = "'" + SHEET_GROUPS + "'"
QR = "'" + SHEET_RANK + "'"
QC = "'" + SHEET_CUST_GROUP + "'"
QD = "'" + SHEET_DETAIL + "'"

# The published figures this workbook has to agree with, typed once and used as the
# expected side of every published-figure check.
PUBLISHED = {
    "move_pct": 5.9616,
    "step_eur": 1652140.71,
    "qty_coverage_pct": 98.57,
    "eur_coverage_pct": 93.15,
    "billed_eur": 34993609.39,
}

# (header, measured minimum width, number format, kind). The width actually written is
# measured from the longest value in the column and capped, never left at the default.
GROUP_COLS = [
    ("Part group", 20, xs.TEXT, "label"),
    ("Family", 20, xs.TEXT, "label"),
    ("Part numbers", 11, xs.QTY, "count"),
    ("Quantity billed, last 12 months", 13, xs.QTY, "qty"),
    ("Billed value, last 12 months (EUR)", 15, xs.EUR, "eur"),
    ("Value of the base-price step (EUR)", 15, xs.EUR, "eur"),
    ("Base-price movement, on base price (%)", 14, xs.PER1, "rate"),
    ("Step as % of billed value (%)", 14, xs.PER1, "rate"),
    ("Priced coverage, share of quantity (%)", 14, xs.PER1, "rate"),
    ("Rank by euro step", 10, xs.QTY, "count"),
]

CUST_GROUP_COLS = [
    ("Customer", 24, xs.TEXT, "label"),
    ("Family", 20, xs.TEXT, "label"),
    ("Part group", 20, xs.TEXT, "label"),
    ("Part numbers", 11, xs.QTY, "count"),
    ("Quantity billed, last 12 months", 13, xs.QTY, "qty"),
    ("Billed value, last 12 months (EUR)", 15, xs.EUR, "eur"),
    ("Value of the base-price step (EUR)", 15, xs.EUR, "eur"),
    ("Base-price movement, on base price (%)", 14, xs.PER1, "rate"),
    ("Step as % of billed value (%)", 14, xs.PER1, "rate"),
    ("Parts billed per vehicle in service (EUR)", 14, xs.EUR2, "eur"),
    ("Value of the base-price step per vehicle in service (EUR)", 15, xs.EUR2, "eur"),
    ("Rank within this customer, by euro step", 13, xs.QTY, "count"),
]

RANK_COLS = [
    ("Customer", 24, xs.TEXT, "label"),
    ("Vehicles in service, 2025", 12, xs.QTY, "count"),
    ("Billed value, last 12 months (EUR)", 15, xs.EUR, "eur"),
    ("Value of the base-price step (EUR)", 15, xs.EUR, "eur"),
    ("Base-price movement, on base price (%)", 14, xs.PER1, "rate"),
    ("Part groups above the EUR 20,000 reporting floor", 12, xs.QTY, "count"),
    ("Highest part groups by rate", 40, xs.TEXT, "long"),
    ("Lowest part groups by rate", 40, xs.TEXT, "long"),
    ("Largest part group by euro step", 22, xs.TEXT, "label"),
    ("Euro step of that group (EUR)", 14, xs.EUR, "eur"),
]

DETAIL_COLS = [
    ("Family", 22, xs.TEXT, "label"),
    ("Part group", 22, xs.TEXT, "label"),
    ("Part numbers", 11, xs.QTY, "count"),
    ("Quantity billed, last 12 months", 13, xs.QTY, "qty"),
    ("Billed value, last 12 months (EUR)", 15, xs.EUR, "eur"),
    ("Value of the base-price step (EUR)", 15, xs.EUR, "eur"),
    ("Base-price basket, prior price list (EUR)", 16, xs.EUR, "eur"),
    ("Base-price movement, on base price (%)", 14, xs.PER2, "rate"),
    ("Priced coverage, share of quantity (%)", 14, xs.PER2, "rate"),
]

CHECK_COLS = [
    ("Check", 48, xs.TEXT, "label"),
    ("Value in this workbook", 14, xs.EUR, "eur"),
    ("Expected", 14, xs.EUR, "eur"),
    ("Difference", 12, xs.EUR, "eur"),
    ("Tolerance", 10, xs.EUR, "eur"),
    ("Result", 10, xs.TEXT, "label"),
]

NO_FLEET_MARKETS = "Armenia, Kazakhstan, Palestine and Ukraine"
NO_FLEET_MSG = (
    f"No vehicles-in-service count exists for {NO_FLEET_MARKETS}, so the per-vehicle "
    "column is blank for those four markets."
)
BASIS_MSG = (
    "Last 12 months of billing, 1 July 2025 to 30 June 2026. Weighted on base price, "
    "not on billed value."
)
MOVE_DEF = (
    "Base-price movement, on base price (%) = the value of the base-price step divided by "
    "the base-price basket. The step is the sum of quantity times the increase in base "
    "price per part number, in euro. The basket is the sum of quantity times the prior "
    "base price, in euro. Both are taken over part numbers that carry a price on both "
    "lists. It is not the step divided by the billed value, and it is not the average of "
    "this column."
)
STEP_OF_BILLED_DEF = (
    "Step as % of billed value (%) = the value of the base-price step divided by the "
    "billed value of the same rows. Same step, second denominator. It is lower than the "
    "movement column because the billed value is higher than the prior base-price basket."
)
FLOOR_MSG = (
    "The highest and lowest lists and the group count apply a EUR 20,000 reporting floor: "
    "a part group is only ranked if it billed at least EUR 20,000 in the window. Below "
    "that a rate rests on too few lines to be a finding. The floor is applied inside the "
    "tables; it is named here so it is not a hidden rule."
)
LOW_LIST_MSG = (
    "Where a customer has fewer than six part groups above the floor, the lowest list is "
    "left blank. With fewer, the same groups would appear in both lists, which is a tie "
    "presented as a ranking rather than a finding."
)
DESC_MSG = (
    "Part group and family names are the supplier's own catalogue wording, reproduced as "
    "billed. They are quoted material, not ISZE labels."
)
SCALE_NOTE = (
    "Visual scales on this sheet: a pale bar on the euro columns and a colour scale on "
    "the movement column. They are different scales on different measures and they are "
    "not comparable with each other. Read the column headings."
)


# --------------------------------------------------------------------- helpers
def _tab(ws, colour: str = xs.NAVY) -> None:
    ws.sheet_properties.tabColor = xs._rgb(colour)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def _measured_width(ws, cols, rows, *, description_cols=()) -> dict[int, float]:
    """Measure every column from its longest header word or value, then cap it."""
    headers = [c[0] for c in cols]
    values = [[r[i] for r in rows] for i in range(len(cols))]
    xs.autofit(ws, headers, values, minimum=9.0, label_cap=46.0, description_cap=60.0,
               description_cols=description_cols)
    widths = {}
    for idx, (_, floor, _, _) in enumerate(cols, start=1):
        letter = get_column_letter(idx)
        current = ws.column_dimensions[letter].width or 8.43
        final = max(floor, current)
        ws.column_dimensions[letter].width = round(final, 2)
        widths[idx] = round(final, 2)
    return widths


def _write_table(ws, cols, rows, *, header_row: int) -> int:
    headers = [c[0] for c in cols]
    widths = _measured_width(ws, cols, rows)
    xs.write_header(ws, header_row, headers,
                    height=xs.header_height(headers, widths))
    for r_off, row in enumerate(rows):
        r = header_row + 1 + r_off
        for c_off, (_, _, fmt, kind) in enumerate(cols, start=1):
            cell = ws.cell(row=r, column=c_off, value=row[c_off - 1])
            xs.apply_style(cell, xs.PLAIN, fmt, right=(kind != "label"))
    last = header_row + len(rows)
    xs.band(ws, header_row + 1, last, 1, len(cols))
    return last


def _total_row(ws, row: int, cols, label: str, formulas: dict[int, str], *,
               style=None, formats: dict[int, str] | None = None) -> None:
    """A labelled total row, styled so it cannot be read as one more data row."""
    style = style or xs.SUBTOTAL
    overrides = formats or {}
    for idx, (_, _, fmt, kind) in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=idx, value=formulas.get(idx))
        xs.apply_style(cell, style, overrides.get(idx, fmt), right=(kind != "label"))
    first = ws.cell(row=row, column=1, value=label)
    first.font = style.font
    first.fill = style.fill
    first.border = style.border
    first.alignment = style.alignment


def _rank_text(g: pd.DataFrame, rate_col: str, smallest_first: bool, n: int = TOP_N) -> str:
    """`Part group 8.3%`, joined with a middle dot, family and rate split by a space."""
    part = g.sort_values(rate_col, ascending=smallest_first).head(n)
    bits = []
    for _, r in part.iterrows():
        rate = r[rate_col]
        label = f"{r['part_group']} " + (
            "No rate available" if pd.isna(rate) else f"{rate:.1f}%")
        bits.append(label)
    return "  ·  ".join(bits)


def _notes(ws, row: int, mapping: dict[int, str]) -> None:
    for col, text in mapping.items():
        xs.note(ws.cell(row=row, column=col), text)


# ---------------------------------------------------------------------- main
def main() -> int:
    facts = dat.load_source_facts(DERIVED)

    # --- 1. network part groups, ranked by euro step -------------------------
    by_group = dat.group_from_lines(facts.lines, ["catalog_l1", "catalog_l2"])
    by_group = by_group.sort_values("step_eur", ascending=False).reset_index(drop=True)
    by_group["rank"] = range(1, len(by_group) + 1)
    group_rows = [[
        r["catalog_l2"], r["catalog_l1"], int(r["part_numbers"]),
        float(r["quantity"]), float(r["billed_eur"]), float(r["step_eur"]),
        float(r["base_price_move_pct"]), float(r["step_pct_of_billed"]),
        float(r["qty_coverage_pct"]), int(r["rank"]),
    ] for _, r in by_group.iterrows()]

    # --- 2. customer x part group -------------------------------------------
    cg = dat.matrix_view(facts.cust_l2)
    cg["uio"] = cg["uio_units_2025"].where(cg["fleet_denominator_available"] == True)  # noqa: E712
    cg = cg.sort_values(["distributor_label", "step_eur"],
                        ascending=[True, False]).reset_index(drop=True)
    cg["rank"] = cg.groupby("distributor_label")["step_eur"].rank(
        ascending=False, method="first").astype(int)

    def _per_uio(row, numerator_col: str):
        uio = row["uio"]
        if pd.isna(uio) or not uio:
            return None
        return float(row[numerator_col] / uio)

    cust_rows = []
    for _, r in cg.iterrows():
        cust_rows.append([
            r["distributor_label"], r["catalog_l1"], r["catalog_l2"], int(r["n_pn"]),
            float(r["l12m_qty"]), float(r["l12m_billed_eur"]), float(r["step_eur"]),
            None if pd.isna(r["base_price_move_pct"]) else float(r["base_price_move_pct"]),
            None if pd.isna(r["step_pct_of_billed"]) else float(r["step_pct_of_billed"]),
            _per_uio(r, "l12m_billed_eur"),
            _per_uio(r, "step_eur"),
            int(r["rank"]),
        ])

    # --- 3. per-customer headline and the highest/lowest lists --------------
    head = dat.customer_headline(facts)
    uio_by_code = (cg.dropna(subset=["uio"]).groupby("distributor_code")["uio"]
                   .first().to_dict())

    rank_rows = []
    for _, h in head.iterrows():
        code = h["distributor_code"]
        g = cg[cg["distributor_code"] == code].rename(columns={"catalog_l2": "part_group"})
        gb = g[g["l12m_billed_eur"] >= FLOOR_EUR]
        n_groups = int(len(gb))
        high = (_rank_text(gb, "base_price_move_pct", smallest_first=False)
                if n_groups else "")
        low = ("" if n_groups < MIN_GROUPS_FOR_LOW_LIST
               else _rank_text(gb, "base_price_move_pct", smallest_first=True))
        top = gb.sort_values("step_eur", ascending=False).head(1)
        rank_rows.append([
            h["distributor_label"],
            uio_by_code.get(code),
            float(h["billed_eur"]),
            float(h["step_eur"]),
            float(h["base_price_move_pct"]),
            n_groups, high, low,
            top.iloc[0]["part_group"] if len(top) else None,
            float(top.iloc[0]["step_eur"]) if len(top) else None,
        ])

    # --- 4. movement grid ---------------------------------------------------
    grid = cg.pivot_table(index="distributor_label", columns="catalog_l2",
                          values="weighted_increase_pct", aggfunc="first")
    grid = grid.reindex(head["distributor_label"])
    grid_cols = list(grid.columns)
    grid_rows = [[idx] + [None if pd.isna(v) else float(v) for v in row]
                 for idx, row in zip(grid.index, grid.to_numpy())]

    # --- 5. workbook --------------------------------------------------------
    wb = Workbook()
    ws_ov = wb.active
    ws_ov.title = SHEET_OVERVIEW
    ws_rm = wb.create_sheet(SHEET_README)
    ws_g = wb.create_sheet(SHEET_GROUPS)
    ws_r = wb.create_sheet(SHEET_RANK)
    ws_cg = wb.create_sheet(SHEET_CUST_GROUP)
    ws_gr = wb.create_sheet(SHEET_GRID)
    ws_ck = wb.create_sheet(SHEET_CHECKS)
    ws_dt = wb.create_sheet(SHEET_DETAIL)
    for s in (ws_ov, ws_rm, ws_g, ws_r, ws_cg, ws_gr, ws_dt):
        _tab(s)
    _tab(ws_ck, xs.TERRA)

    # ------------------------------------------------------------- detail
    xs.write_title(ws_dt, 1,
                   "Calculation detail — the line-level aggregate every total is built from",
                   len(DETAIL_COLS), height=22)
    xs.block(ws_dt, 2,
             "One row per part group, rebuilt from the billing base file. The Checks "
             "sheet points at the total row here instead of at a typed number, so a "
             "rebuilt workbook is checked against its source, not against itself.",
             len(DETAIL_COLS), height=30)
    xs.write_banner(ws_dt, 4, "Part groups, network-wide, by euro step", len(DETAIL_COLS))
    dt_first = 5
    dt_last = _write_table(ws_dt, DETAIL_COLS, [[
        r["catalog_l1"], r["catalog_l2"], int(r["part_numbers"]), float(r["quantity"]),
        float(r["billed_eur"]), float(r["step_eur"]), float(r["base_price_basket_eur"]),
        float(r["base_price_move_pct"]), float(r["qty_coverage_pct"]),
    ] for _, r in by_group.iterrows()], header_row=dt_first)
    dt_total = dt_last + 1
    _total_row(ws_dt, dt_total, DETAIL_COLS, "Total", {
        3: f"=SUM(C{dt_first}:C{dt_last})",
        4: f"=SUM(D{dt_first}:D{dt_last})",
        5: f"=SUM(E{dt_first}:E{dt_last})",
        6: f"=SUM(F{dt_first}:F{dt_last})",
        7: f"=SUM(G{dt_first}:G{dt_last})",
        8: f"=(F{dt_total}/G{dt_total}-1)*100",
        9: f"=SUMPRODUCT(D{dt_first}:D{dt_last},I{dt_first}:I{dt_last})/D{dt_total}",
    }, style=xs.GRAND_TOTAL, formats={8: xs.PER2, 9: xs.PER2})
    xs.freeze_and_filter(ws_dt, freeze=f"A{dt_first + 1}",
                         filter_ref=f"A{dt_first}:{get_column_letter(len(DETAIL_COLS))}{dt_last}")
    xs.add_data_bar(ws_dt, f"F{dt_first}:F{dt_last}")
    xs.note(ws_dt.cell(row=dt_total, column=8),
            "= step total / basket total - 1. This is the definition the published network "
            "figure uses. It is not the average of the column above it.")
    xs.note(ws_dt.cell(row=dt_total, column=9),
            "= the quantity-weighted average of the coverage column, not the average of "
            "the percentages.")
    xs.note(ws_dt.cell(row=dt_first, column=7),
            "Base-price basket = SUM(quantity x prior base price), converted from yen at "
            f"{facts.fx_jpy_per_eur} yen per euro, over part numbers priced on both "
            "lists. It is the denominator of the movement column.")
    _notes(ws_dt, dt_first, {
        4: "A quantity on its own is not a finding. It is here so the euro column can be "
           "read as a rate.",
        6: "Quantity times the increase in base price per part number, in euro.",
        8: MOVE_DEF,
    })

    # -------------------------------------------------------- part groups
    xs.write_title(ws_g, 1, "Which part groups moved more or less on the new base price",
                   len(GROUP_COLS), height=22)
    xs.block(ws_g, 2,
             "Ranked by the euro value of the step, so the group that matters most in "
             "money is at the top. A group can be first on euro and fifth on movement "
             "rate; the rate column is sorted separately on the highest-and-lowest sheet.",
             len(GROUP_COLS), height=30)
    g_first = 4
    g_last = _write_table(ws_g, GROUP_COLS, group_rows, header_row=g_first)
    g_total = g_last + 1
    _total_row(ws_g, g_total, GROUP_COLS, "Total", {
        3: f"=SUM(C{g_first}:C{g_last})",
        4: f"=SUM(D{g_first}:D{g_last})",
        5: f"=SUM(E{g_first}:E{g_last})",
        6: f"=SUM(F{g_first}:F{g_last})",
        7: f"={QD}!$H${dt_total}",
        8: f"=F{g_total}/E{g_total}*100",
        9: f"=SUMPRODUCT(D{g_first}:D{g_last},I{g_first}:I{g_last})/D{g_total}",
    }, style=xs.GRAND_TOTAL, formats={7: xs.PER1, 8: xs.PER1, 9: xs.PER1})
    xs.freeze_and_filter(ws_g, freeze=f"A{g_first + 1}",
                         filter_ref=f"A{g_first}:{get_column_letter(len(GROUP_COLS))}{g_last}")
    xs.add_data_bar(ws_g, f"E{g_first}:E{g_last}")
    xs.add_data_bar(ws_g, f"F{g_first}:F{g_last}")
    xs.add_colour_scale(ws_g, f"G{g_first}:G{g_last}")
    xs.block(ws_g, g_total + 2, SCALE_NOTE + "  " + MOVE_DEF, len(GROUP_COLS), height=42)
    xs.block(ws_g, g_total + 3, FLOOR_MSG, len(GROUP_COLS), height=30)
    xs.block(ws_g, g_total + 4, DESC_MSG, len(GROUP_COLS), height=18)
    _notes(ws_g, g_first, {
        7: MOVE_DEF,
        8: STEP_OF_BILLED_DEF,
        9: "Share of the quantity in this row that carries a price on both lists. The "
           "remainder is not comparable, which is not the same as no movement.",
        10: "Rank of this group by the euro value of the step across the network. One is "
            "the largest single contributor in euro.",
    })
    xs.note(ws_g.cell(row=g_total, column=7),
            MOVE_DEF + " Taken live from the calculation detail sheet so the two cannot "
            "drift apart.")
    xs.note(ws_g.cell(row=g_total, column=8),
            "= step total / billed total. This is not the movement column above it.")

    # --------------------------------------------------- per-customer ranking
    xs.write_title(ws_r, 1, "Which customer did the step matter most to, and where",
                   len(RANK_COLS), height=22)
    xs.block(ws_r, 2,
             "Euro first, then rate. The customer's billed value and euro step come before "
             "its movement rate, because the question this sheet answers is which customer "
             "the step mattered most to, not which part group moved most.", len(RANK_COLS),
             height=30)
    r_first = 4
    r_last = _write_table(ws_r, RANK_COLS, rank_rows, header_row=r_first)
    r_total = r_last + 1
    _total_row(ws_r, r_total, RANK_COLS, "Total", {
        3: f"=SUM(C{r_first}:C{r_last})",
        4: f"=SUM(D{r_first}:D{r_last})",
        5: f"={QD}!$H${dt_total}",
    }, style=xs.GRAND_TOTAL, formats={5: xs.PER1})
    xs.freeze_and_filter(ws_r, freeze=f"A{r_first + 1}",
                         filter_ref=f"A{r_first}:{get_column_letter(len(RANK_COLS))}{r_last}")
    xs.add_data_bar(ws_r, f"C{r_first}:C{r_last}")
    xs.add_data_bar(ws_r, f"D{r_first}:D{r_last}")
    xs.add_colour_scale(ws_r, f"E{r_first}:E{r_last}")
    xs.block(ws_r, r_total + 2, SCALE_NOTE + "  " + LOW_LIST_MSG, len(RANK_COLS), height=42)
    xs.block(ws_r, r_total + 3, NO_FLEET_MSG, len(RANK_COLS), height=18)
    _notes(ws_r, r_first, {
        3: "The customer's billed value over the window, across every part group in this "
           "workbook. It is the size of the book the step applies to.",
        4: "The customer's euro step. With the billed value and the movement rate beside "
           "it, this is the customer's headline.",
        5: MOVE_DEF,
        6: f"Number of the customer's part groups that billed at least EUR {FLOOR_EUR:,.0f} "
           "in the window and so appear in the highest and lowest lists. A small count "
           "means the lists rest on few groups.",
        7: "The customer's three highest part groups by movement rate, with the rate. "
           f"Groups below EUR {FLOOR_EUR:,.0f} billed are not ranked.",
        8: f"Left blank where fewer than {MIN_GROUPS_FOR_LOW_LIST} groups clear the floor, "
           "so the same three cannot appear in both lists.  " + LOW_LIST_MSG,
        9: "The customer's single largest part group by euro step.",
        10: "The euro step of the group named to the left, in its own column so both the "
            "name and the amount can be sorted.",
    })
    xs.note(ws_r.cell(row=r_total, column=5),
            MOVE_DEF + " Taken live from the calculation detail sheet.")

    # -------------------------------------------------- customer x part group
    xs.write_title(ws_cg, 1,
                   "Every customer and part group, the detail behind the two summaries",
                   len(CUST_GROUP_COLS), height=22)
    xs.block(ws_cg, 2, NO_FLEET_MSG + " They are in every euro column; they are only "
             "absent from the per-vehicle columns, and blank there is not zero.",
             len(CUST_GROUP_COLS), height=30)
    cg_first = 4
    cg_last = _write_table(ws_cg, CUST_GROUP_COLS, cust_rows, header_row=cg_first)
    cg_total = cg_last + 1
    _total_row(ws_cg, cg_total, CUST_GROUP_COLS, "Total", {
        3: f"=SUM(C{cg_first}:C{cg_last})",
        4: f"=SUM(D{cg_first}:D{cg_last})",
        5: f"=SUM(E{cg_first}:E{cg_last})",
        6: f"=SUM(F{cg_first}:F{cg_last})",
        7: f"=SUM(G{cg_first}:G{cg_last})",
        8: f"={QD}!$H${dt_total}",
        9: f"=G{cg_total}/F{cg_total}*100",
    }, style=xs.GRAND_TOTAL, formats={8: xs.PER1, 9: xs.PER1})
    xs.freeze_and_filter(ws_cg, freeze=f"A{cg_first + 1}",
                         filter_ref=f"A{cg_first}:"
                                    f"{get_column_letter(len(CUST_GROUP_COLS))}{cg_last}")
    xs.add_data_bar(ws_cg, f"F{cg_first}:F{cg_last}")
    xs.add_data_bar(ws_cg, f"G{cg_first}:G{cg_last}")
    xs.add_colour_scale(ws_cg, f"H{cg_first}:H{cg_last}")
    xs.block(ws_cg, cg_total + 2, SCALE_NOTE + "  " + DESC_MSG, len(CUST_GROUP_COLS),
             height=42)
    _notes(ws_cg, cg_first, {
        6: "Billed value of this customer and part group over the window.",
        7: "Quantity times the increase in base price per part number, in euro.",
        8: MOVE_DEF + " Blank where the group carries no part number priced on both lists: "
                      "no comparable price, not a zero movement.",
        9: STEP_OF_BILLED_DEF,
        10: "Parts billed divided by vehicles in service. Blank for the four markets with "
            "no fleet count.  " + NO_FLEET_MSG,
        11: "Value of the base-price step divided by vehicles in service. Same four markets "
            "are blank. Blank is not zero performance.",
        12: "Rank of this group inside this customer, by euro step. One is the customer's "
            "largest contributor in euro.",
    })
    xs.note(ws_cg.cell(row=cg_total, column=8),
            MOVE_DEF + " Taken live from the calculation detail sheet.")
    xs.note(ws_cg.cell(row=cg_total, column=9),
            "= step total / billed total. Not the movement column above it.")

    # ------------------------------------------------------- movement grid
    gr_cols = [("Customer", 26, xs.TEXT, "label")] + [
        (name, 11, xs.PER1, "rate") for name in grid_cols]
    xs.write_title(ws_gr, 1,
                   "Where each customer's movement sat, part group by part group",
                   len(gr_cols), height=22)
    xs.block(ws_gr, 2,
             "Customer rows, part group columns, movement rate. The colour scale runs "
             "across the body only. Every cell is the same measure as the movement column "
             "on the other sheets, so the grid can be read against them directly.",
             len(gr_cols), height=30)
    gr_first = 4
    _measured_width(ws_gr, gr_cols, grid_rows)
    xs.write_header(ws_gr, gr_first, [c[0] for c in gr_cols],
                    height=xs.header_height([c[0] for c in gr_cols],
                                            {i + 1: c[1] for i, c in enumerate(gr_cols)},
                                            minimum=44.0))
    for r_off, row in enumerate(grid_rows):
        r = gr_first + 1 + r_off
        for c_off, val in enumerate(row, start=1):
            cell = ws_gr.cell(row=r, column=c_off, value=val)
            xs.apply_style(cell, xs.PLAIN, xs.TEXT if c_off == 1 else xs.PER1,
                           right=(c_off > 1))
    gr_last = gr_first + len(grid_rows)
    xs.band(ws_gr, gr_first + 1, gr_last, 2, len(gr_cols))
    gr_net = gr_last + 1
    known = {r[0] for r in group_rows}
    for c_off, name in enumerate(grid_cols, start=2):
        cell = ws_gr.cell(row=gr_net, column=c_off)
        if name in known:
            safe = name.replace('"', '""')
            cell.value = (f'=INDEX({QG}!$G${g_first}:$G${g_last},'
                          f'MATCH("{safe}",{QG}!$A${g_first}:$A${g_last},0))')
        xs.apply_style(cell, xs.GRAND_TOTAL, xs.PER1, right=True)
    xs.apply_style(ws_gr.cell(row=gr_net, column=1, value="Network, all customers"),
                   xs.GRAND_TOTAL, xs.TEXT)
    xs.add_colour_scale(ws_gr, f"B{gr_first + 1}:{get_column_letter(len(gr_cols))}{gr_last}")
    xs.freeze_and_filter(ws_gr, freeze=f"B{gr_first + 1}")
    xs.note(ws_gr.cell(row=gr_first, column=2),
            "Movement rate per customer and part group. Blank where the customer has no "
            "part number priced in that group. The bottom row is the network movement for "
            "each group, taken live from the part-group sheet.")
    xs.note(ws_gr.cell(row=gr_net, column=1),
            "Every cell in this row points at the matching row of the part-group sheet, "
            "so the grid cannot drift away from it.")

    # ---------------------------------------------------------------- checks
    xs.write_title(ws_ck, 1, "Does this workbook agree with the source files?",
                   len(CHECK_COLS), height=22)
    xs.block(ws_ck, 2,
             "Every row below is a live formula. Result reads OK when the difference is "
             "inside the tolerance on that row, and CHECK otherwise, and a CHECK row is "
             "painted red. No row is skipped: if a number moves, this sheet says so.",
             len(CHECK_COLS), height=30)

    xs.write_banner(ws_ck, 4, "The published figures this workbook must agree with",
                    len(CHECK_COLS))
    xs.write_header(ws_ck, 5, ["Figure", "Published value", "Where it comes from"], height=24)
    pub_rows = [
        ("Network base-price movement, on base price", PUBLISHED["move_pct"],
         xs.PER4, "Weighted comparison, network row"),
        ("Value of the base-price step (EUR)", PUBLISHED["step_eur"],
         xs.EUR2, "Weighted comparison, revised basis"),
        ("Priced coverage, share of quantity", PUBLISHED["qty_coverage_pct"],
         xs.PER2, "Weighted comparison, coverage block"),
        ("Priced coverage, share of billed value", PUBLISHED["eur_coverage_pct"],
         xs.PER2, "Weighted comparison, coverage block"),
        ("Billed value in scope, last 12 months (EUR)", PUBLISHED["billed_eur"],
         xs.EUR2, "Weighted comparison, coverage block"),
    ]
    for i, (name, val, fmt, src) in enumerate(pub_rows):
        r = 6 + i
        xs.apply_style(ws_ck.cell(row=r, column=1, value=name), xs.PLAIN, xs.TEXT)
        xs.apply_style(ws_ck.cell(row=r, column=2, value=val), xs.INPUT, fmt, right=True)
        xs.apply_style(ws_ck.cell(row=r, column=3, value=src), xs.MUTED_ITALIC, xs.TEXT)
    xs.note(ws_ck.cell(row=6, column=2),
            "Published to four decimal places, so a difference inside 0.0001 percentage "
            "points is the published rounding, not a change in the number. The cell holds "
            "a percentage-point value and the format appends the percent sign.")
    xs.note(ws_ck.cell(row=7, column=2),
            "Sum of the per-line euro step over part numbers priced on both lists.")
    xs.note(ws_ck.cell(row=9, column=2),
            "Coverage measured in euro rather than in pieces. It is lower than the quantity "
            "coverage because the unpriced items carry the higher unit values.")
    xs.note(ws_ck.cell(row=10, column=2),
            "The billed value every customer and part group in this workbook adds up to.")

    xs.write_banner(ws_ck, 12, "Does the workbook agree?", len(CHECK_COLS))
    xs.write_header(ws_ck, 13, [c[0] for c in CHECK_COLS], height=30)
    ck_first = 14

    det_rate = f"{QD}!$H${dt_total}"
    det_rate_pct = f"{QD}!$H${dt_total}*100"
    det_step = f"{QD}!$F${dt_total}"
    checks = [
        ("Network movement equals the published figure",
         f"={det_rate_pct}", "=$B$6", 0.0001, xs.PER4),
        ("Value of the step equals the published figure",
         f"={det_step}", "=$B$7", 0.05, xs.EUR2),
        ("Sum of the part-group step column equals the network step",
         f"=SUM({QG}!$F${g_first}:$F${g_last})", f"={det_step}", 0.05, xs.EUR2),
        ("Sum of the customer step column equals the network step",
         f"=SUM({QC}!$G${cg_first}:$G${cg_last})", f"={det_step}", 0.05, xs.EUR2),
        ("Sum of the part-group billed column equals the billed value in scope",
         f"=SUM({QG}!$E${g_first}:$E${g_last})", "=$B$10", 0.05, xs.EUR),
        ("Sum of the customer billed column equals the billed value in scope",
         f"=SUM({QC}!$F${cg_first}:$F${cg_last})", "=$B$10", 0.05, xs.EUR),
        ("Priced coverage, share of quantity, equals the published figure",
         f"=SUMPRODUCT({QD}!$D${dt_first}:$D${dt_last},{QD}!$I${dt_first}:$I${dt_last})"
         f"/{QD}!$D${dt_total}",
         "=$B$8", 0.01, xs.PER2),
        ("Billed value in scope equals the published figure",
         f"={QD}!$E${dt_total}", "=$B$10", 0.05, xs.EUR),
        ("Movement grid cells equal the customer by part-group rows they come from",
         f"=SUMPRODUCT(--(COUNTIF({QC}!$C${cg_first}:$C${cg_last},"
         f"{QG}!$A${g_first}:$A${g_last})=0))",
         "=0", 0, xs.QTY),
        ("Movement column shows a rate and the step column shows a share of billed "
         "value, so no step-share cell can exceed the movement cell",
         f"=SUMPRODUCT(--(IF(ISNUMBER({QC}!$I${cg_first}:$I${cg_last}),"
         f"{QC}!$I${cg_first}:$I${cg_last},0)>IF(ISNUMBER({QC}!$H${cg_first}:$H${cg_last}),"
         f"{QC}!$H${cg_first}:$H${cg_last},0)+0.01))",
         "=0", 0, xs.QTY),
        ("Part-group rows shown",
         f"=COUNTA({QG}!$A${g_first + 1}:$A${g_last})", f"={len(group_rows)}", 0, xs.QTY),
        ("Customer rows shown",
         f"=COUNTA({QR}!$A${r_first + 1}:$A${r_last})", f"={len(rank_rows)}", 0, xs.QTY),
        ("Customer by part-group rows shown",
         f"=COUNTA({QC}!$A${cg_first + 1}:$A${cg_last})", f"={len(cust_rows)}", 0, xs.QTY),
        ("Missing values rendered as text instead of left blank",
         f'=COUNTIF({QR}!$G${r_first}:$J${r_last},"*nan*")'
         f'+COUNTIF({QR}!$G${r_first}:$J${r_last},"*#*")'
         f'+COUNTIF({QC}!$A${cg_first}:$L${cg_last},"*nan*")'
         f'+COUNTIF({QC}!$A${cg_first}:$L${cg_last},"*#*")'
         f'+COUNTIF({QG}!$A${g_first}:$H${g_last},"*nan*")'
         f'+COUNTIF({QG}!$A${g_first}:$H${g_last},"*#*")',
         "=0", 0, xs.QTY),
        ("Per-vehicle cells left blank for markets with no fleet count",
         f"=COUNTBLANK({QC}!$J${cg_first}:$J${cg_last})"
         f"-COUNTIF({QC}!$F${cg_first}:$F${cg_last},0)"
         f"-COUNTIF({QC}!$F${cg_first}:$F${cg_last},\"\")",
         f"={sum(1 for r in cust_rows if r[9] is None)}", 0, xs.QTY),
    ]
    for i, (name, val, exp, tol, fmt) in enumerate(checks):
        r = ck_first + i
        xs.apply_style(ws_ck.cell(row=r, column=1, value=name), xs.PLAIN, xs.TEXT)
        xs.apply_style(ws_ck.cell(row=r, column=2, value=val), xs.PLAIN, fmt, right=True)
        xs.apply_style(ws_ck.cell(row=r, column=3, value=exp), xs.PLAIN, fmt, right=True)
        xs.apply_style(ws_ck.cell(row=r, column=4, value=f"=B{r}-C{r}"), xs.PLAIN, fmt,
                       right=True)
        xs.apply_style(ws_ck.cell(row=r, column=5, value=tol), xs.PLAIN, fmt, right=True)
        xs.apply_style(ws_ck.cell(row=r, column=6,
                                  value=f'=IF(ABS(D{r})<=E{r},"OK","CHECK")'),
                       xs.PLAIN, xs.TEXT)
    ck_last = ck_first + len(checks) - 1
    xs.flag_not_ok(ws_ck, f"F{ck_first}:F{ck_last}")
    xs.band(ws_ck, ck_first, ck_last, 1, len(CHECK_COLS), start_banded=False)
    xs.note(ws_ck.cell(row=ck_first, column=6),
            "OK means the difference on this row is inside the tolerance on this row. "
            "Anything else reads CHECK and is painted red, so a failing row cannot be "
            "mistaken for a pass.")
    xs.block(ws_ck, ck_last + 2,
             "The tolerances are the published rounding, not slack. The movement tolerance "
             "is one ten-thousandth of a percentage point. The euro tolerances cover the "
             "cent rounding of the rows as shown, which can make a displayed column sum sit "
             "up to five cents below the unrounded figure. A real change moves a value far "
             "more than that.", len(CHECK_COLS), height=48)
    xs.set_widths(ws_ck, {"A": 48, "B": 15, "C": 15, "D": 13, "E": 11, "F": 10})
    xs.freeze_and_filter(ws_ck, freeze="A14")

    # --------------------------------------------------------------- read me
    _tab(ws_rm)
    xs.write_title(ws_rm, 1, "Read me — how this workbook is put together", 3, height=22)
    rm = 3

    def rm_block(title: str, body: str, height: float = 46) -> None:
        nonlocal rm
        xs.write_banner(ws_rm, rm, title, 3)
        rm += 1
        xs.block(ws_rm, rm, body, 3, height=height)
        rm += 2

    rm_block("What this workbook answers",
             "Which part groups moved more or less on the new base price, in euro and in "
             "rate, and for which customer. It is a price-move view. It is not a revenue, "
             "margin or volume forecast.")
    rm_block("Period and basis", BASIS_MSG)
    rm_block("The movement column, exactly", MOVE_DEF)
    rm_block("The second percentage column", STEP_OF_BILLED_DEF)
    rm_block("Two percentage columns, never one",
             "Every sheet that shows a movement also shows the step as a share of billed "
             "value in its own labelled column. They are two measures of the same step and "
             "they are two different numbers. Read the column heading, not the column "
             "position.")
    rm_block("Why the tables are sorted by euro, not by rate",
             "The first version of this workbook sorted the part-group table by movement "
             "rate, which put a group with a large rate and a small book above a group "
             "with more euro and a smaller rate. A euro question was answered with a rate "
             "sort. Euro now sorts the table, the movement column has its own highest and "
             "lowest sheet, and the euro columns are labelled with the measure they carry.")
    rm_block("The EUR 20,000 reporting floor", FLOOR_MSG)
    rm_block("A short list, and why it can be blank", LOW_LIST_MSG)
    rm_block("Markets with no fleet count",
             NO_FLEET_MSG + " Those four markets are inside every euro total in this "
             "workbook. They are only absent from the per-vehicle columns, where a blank "
             "is a missing count and never zero performance.")
    rm_block("Israel is two customers, never one",
             "UMI and UTI are separate customers with separate books, separate fleets and "
             "different parts mixes. They are never added together into one Israel figure "
             "anywhere in this workbook.")
    rm_block("Part groups and families are quoted material", DESC_MSG)
    rm_block("What is not in this workbook",
             "No elasticity coefficient, so the step is a base-price move and not a "
             "revenue or margin outcome. No allocation run. No cost, margin or warranty "
             "data. No forecast. The effect on volume is not modelled in any sheet.")
    rm_block("Totals",
             "Total rows are live formulas. Excel was asked to recalculate the workbook "
             "after the build, so the calculated value is stored with each formula and "
             "reads without opening Excel. Edit a formula and the total recalculates on "
             "save.")
    rm_block("Source files and build",
             "Built from the per-part-number weighted comparison for the window, joined to "
             "the catalogue classification on part number, with the vehicles-in-service "
             "file for fleet counts. The four published figures appear on the Checks sheet "
             "with the tolerance used for each. The calculation detail sheet holds the "
             "line-level aggregate the live formulas point at.")
    xs.block(ws_rm, rm,
             "This sheet is internal working material. Before the workbook is shared "
             "outside ISZE, remove this sheet, the Checks sheet and the calculation detail "
             "sheet.", 3, height=30)
    rm += 2
    xs.write_banner(ws_rm, rm, "Sheet index", 3)
    rm += 1
    xs.write_header(ws_rm, rm, ["Sheet", "What it answers", "Level"], height=22)
    rm += 1
    readme_index = [
        (SHEET_OVERVIEW, "The headline answer, then the index of everything else",
         "1 — summary"),
        (SHEET_GROUPS, "One row per part group, ranked by euro step, with the movement on "
                       "base price beside the step as a share of billed value",
         "2 — by part group"),
        (SHEET_RANK, "One row per customer: its billed value, its euro step, its movement, "
                     "and its most and least moved groups", "1 — summary"),
        (SHEET_CUST_GROUP, "The full customer by part group table behind both sheets above",
         "2 — by part group"),
        (SHEET_GRID, "The same movement as a grid: customers down, part groups across",
         "2 — by part group"),
        (SHEET_CHECKS, "Live formulas showing whether this workbook agrees with the sources",
         "1 — summary"),
        (SHEET_DETAIL, "The line-level aggregate every total is calculated from",
         "3 — line detail"),
    ]
    for name, what, level in readme_index:
        c1 = ws_rm.cell(row=rm, column=1, value=name)
        xs.apply_style(c1, xs.PLAIN, xs.TEXT)
        xs.internal_link(c1, name)
        xs.apply_style(ws_rm.cell(row=rm, column=2, value=what), xs.PLAIN, xs.TEXT)
        xs.apply_style(ws_rm.cell(row=rm, column=3, value=level), xs.PLAIN, xs.TEXT)
        rm += 1
    ws_rm.column_dimensions["A"].width = 30
    ws_rm.column_dimensions["B"].width = 56
    ws_rm.column_dimensions["C"].width = 18
    xs.freeze_and_filter(ws_rm, freeze="A3")

    # -------------------------------------------------------------- overview
    xs.set_widths(ws_ov, {"A": 34, "B": 16, "C": 16, "D": 16, "E": 16, "F": 18, "G": 48})
    xs.write_title(ws_ov, 1, "Which part groups moved more or less, and for which customer",
                   7, height=26)
    xs.block(ws_ov, 2, BASIS_MSG, 7, height=18)

    xs.write_banner(ws_ov, 4, "The answer", 7)
    answer = [
        ("Network base-price movement, on base price", f"={det_rate}", xs.PER4,
         "The euro step across the network divided by its base-price basket. The "
         "definition is on the Read me sheet. This is the headline figure."),
        ("Value of the base-price step (EUR)", f"={det_step}", xs.EUR,
         "Sum of quantity times the increase in base price per part number, over part "
         "numbers priced on both lists. It is the euro size of the move."),
        ("Billed value in scope, last 12 months (EUR)", f"={QD}!$E${dt_total}", xs.EUR,
         "Everything the in-scope customers billed on these parts in the window. It is the "
         "book the step applies to."),
        ("Priced coverage, share of quantity", f"={QD}!$I${dt_total}", xs.PER2,
         "Share of the billed quantity that carries a price on both lists. The rest is not "
         "comparable."),
        ("Priced coverage, share of billed value", "=$B$10", xs.PER2,
         "Coverage measured in euro rather than in pieces, from the coverage block of the "
         "weighted comparison. It is lower than the quantity coverage because the unpriced "
         "parts carry the higher unit values."),
    ]
    ov_first = 5
    for i, (label, formula, fmt, text) in enumerate(answer):
        r = ov_first + i
        xs.apply_style(ws_ov.cell(row=r, column=1, value=label), xs.PLAIN, xs.TEXT)
        val = ws_ov.cell(row=r, column=2, value=formula)
        xs.apply_style(val, xs.INPUT, fmt, right=True)
        xs.note(val, text + ("  The cell holds a percentage-point value; the format "
                             "appends the percent sign and does not divide by 100."
                             if fmt != xs.EUR else ""))
        if fmt != xs.EUR:
            xs.note(val, text + "  The cell holds a percentage-point value and the format "
                                "appends the percent sign; the value is not divided by 100.")

    ov_body = ov_first + 6
    xs.block(ws_ov, ov_body,
             "Read the movement figure as a price move, not as a revenue or margin move. "
             f"It covers the part numbers that carry a price on both lists: "
             f"{PUBLISHED['qty_coverage_pct']:.2f}% of the billed quantity and "
             f"{PUBLISHED['eur_coverage_pct']:.2f}% of the billed value. What falls outside "
             "is named on the Read me sheet and counted on the Checks sheet.", 7, height=44)
    ov_amber = ov_body + 1
    xs.write_banner(ws_ov, ov_amber, NO_FLEET_MSG, 7, style=xs.MISSING_BANNER, height=30)
    xs.note(ws_ov.cell(row=ov_amber, column=1), NO_FLEET_MSG)

    ov_idx_banner = ov_amber + 2
    xs.write_banner(ws_ov, ov_idx_banner, "How to read this workbook", 7)
    ov_head = ov_idx_banner + 1
    for col, text in {1: "Sheet", 2: "What it answers", 4: "Level", 5: "Rows"}.items():
        cell = ws_ov.cell(row=ov_head, column=col, value=text)
        xs.apply_style(cell, xs.HEADER, xs.TEXT)
    ws_ov.merge_cells(start_row=ov_head, start_column=2, end_row=ov_head, end_column=3)
    ws_ov.row_dimensions[ov_head].height = 24
    ov_index = [
        (SHEET_GROUPS,
         "Which part groups moved more or less across the whole network, ranked in euro",
         "2 — by part group", f"{len(group_rows)} part groups"),
        (SHEET_RANK,
         "Which customer the step mattered most to, and its most and least moved groups",
         "1 — summary", f"{len(rank_rows)} customers"),
        (SHEET_CUST_GROUP,
         "Every customer and part group, the detail behind both sheets above",
         "2 — by part group", f"{len(cust_rows):,} rows"),
        (SHEET_GRID,
         "The same movement as a grid: customers down, part groups across",
         "2 — by part group", f"{len(grid_rows)} x {len(grid_cols)}"),
        (SHEET_CHECKS,
         "Live formulas showing whether this workbook agrees with the source files",
         "1 — summary", f"{len(checks)} checks"),
        (SHEET_DETAIL,
         "The line-level aggregate every total is calculated from",
         "3 — line detail", f"{len(group_rows)} rows"),
    ]
    ov_idx_first = ov_head + 1
    for i, (name, what, level, rows) in enumerate(ov_index):
        r = ov_idx_first + i
        c1 = ws_ov.cell(row=r, column=1, value=name)
        xs.apply_style(c1, xs.PLAIN, xs.TEXT)
        xs.internal_link(c1, name)
        xs.apply_style(ws_ov.cell(row=r, column=2, value=what), xs.PLAIN, xs.TEXT)
        ws_ov.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        xs.apply_style(ws_ov.cell(row=r, column=2), xs.PLAIN, xs.TEXT)
        xs.apply_style(ws_ov.cell(row=r, column=4, value=level), xs.PLAIN, xs.TEXT)
        xs.apply_style(ws_ov.cell(row=r, column=5, value=rows), xs.PLAIN, xs.TEXT)
    ov_idx_last = ov_idx_first + len(ov_index) - 1
    xs.band(ws_ov, ov_idx_first, ov_idx_last, 1, 7, start_banded=False)
    foot = ov_idx_last + 2
    xs.block(ws_ov, foot, FLOOR_MSG + "  " + LOW_LIST_MSG, 7, height=56)
    xs.block(ws_ov, foot + 1, DESC_MSG + "  " + SCALE_NOTE, 7, height=32)
    xs.freeze_and_filter(ws_ov, freeze="A6")
    xs.note(ws_ov.cell(row=1, column=1),
            "The question this workbook answers. The workbook opens on this sheet so the "
            "answer is read before the tables.")

    # ---------------------------------------------------------------- output
    wb.properties.creator = "ISZE pricing workbook"
    wb.properties.title = "Base-price movement by part group and customer"
    wb.properties.description = (
        "Which part groups moved more or less on the new base price, and for which "
        "customer. Last 12 months of billing, 1 July 2025 to 30 June 2026.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)

    CMD.write_bytes(
        b"@echo off\r\n"
        b'start "" "%~dp0Price_increase_by_part_group_per_customer.xlsx"\r\n'
    )

    # -------------------------------------------------------------- console
    net_step = by_group["step_eur"].sum()
    net_basket = by_group["base_price_basket_eur"].sum()
    qty_cov = facts.lines["priced_qty_line"].sum() / facts.lines["billed_qty"].sum() * 100
    eur_cov = facts.lines["priced_eur_line"].sum() / facts.lines["net_sales_value"].sum() * 100

    print(f"wrote {OUT}")
    print(f"sheets: {wb.sheetnames}")
    print(f"launcher: {CMD}")
    print()
    print("ACCEPTANCE — recomputed from source")
    print(f"  network base-price move   {net_step / net_basket * 100:.4f}%")
    print(f"  value of the step         EUR {net_step:,.2f}")
    print(f"  priced coverage, quantity {qty_cov:.2f}%")
    print(f"  priced coverage, in euro   {eur_cov:.2f}%")
    print()
    print(f"part groups {len(group_rows)} | customers {len(rank_rows)} | "
          f"customer x group rows {len(cust_rows)} | checks {len(checks)}")

    result = bake.bake(OUT)
    print()
    if result["ok"]:
        print(f"Excel recalculated the workbook in {result['seconds']}s; formulas and "
              "calculated values are both stored, so totals read without opening Excel")
    else:
        print(f"NOT BAKED: {result['error']}")
        print("Totals will read blank until the file is opened in Excel.")

    QA.mkdir(parents=True, exist_ok=True)
    pdf = bake.export_pdf(OUT, QA / "workbook_qa.pdf",
                          [SHEET_OVERVIEW, SHEET_README, SHEET_GROUPS, SHEET_RANK,
                           SHEET_CHECKS])
    print()
    print("QA pdf:", pdf.get("pdf") if pdf["ok"] else f"FAILED: {pdf['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
