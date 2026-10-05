"""Parts needing a source or origin - readable workbook for Jerome.

Answers: which part numbers in the last-12-months priced set have no recorded
source of supply, no recorded country of origin, or a contradiction between the
files, so the information can be requested.

Read-only against everything except its three declared outputs.

Outputs
-------
  01_data/01_Pricing/Parts_needing_source_or_origin.xlsx
  01_data/01_Pricing/OPEN_Parts_needing_source_or_origin.cmd
  01_data/00_derived/parts_needing_source_or_origin.meta.json

Run:  python 01_data/91_build/build_parts_needing_source_or_origin.py
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
PRICING = ISZE / "01_data" / "01_Pricing"

OUT_XLSX = PRICING / "Parts_needing_source_or_origin.xlsx"
OUT_CMD = PRICING / "OPEN_Parts_needing_source_or_origin.cmd"
OUT_META = DERIVED / "parts_needing_source_or_origin.meta.json"

WINDOW_START, WINDOW_END = "1 Jul 2025", "30 Jun 2026"
FX = 163.7
SPEC_XLSX = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Simulation_Spec_Basis.xlsx"
SEPT_XLSX = ISZE / "01_data" / "PRICE CD 260910.xlsx"
ISZJ_XLSX = ISZE / "01_data" / "01_Pricing" / "ISZJ_master_data_competitive_parts.xlsx"

# House palette.
NAVY = "15233C"
TERRACOTTA = "C0552D"
CREAM = "F7F4EE"
PALE = "EEF3F9"
BAND = "DCE4EE"

SOURCE_LABEL = {"J": "J - Japan / IML", "T": "T - Thailand / IMIT"}
ORIGIN_NAME = {
    "JP": "Japan", "TH": "Thailand", "CN": "China", "US": "United States",
    "VN": "Vietnam", "DE": "Germany", "PH": "Philippines", "TW": "Taiwan",
    "ID": "Indonesia", "IN": "India", "KR": "South Korea", "FR": "France",
    "MY": "Malaysia", "SG": "Singapore", "HU": "Hungary", "GB": "United Kingdom",
    "IT": "Italy", "PL": "Poland", "BR": "Brazil", "AU": "Australia",
    "CZ": "Czechia", "MX": "Mexico", "SE": "Sweden", "AT": "Austria",
    "SK": "Slovakia", "TR": "Turkiye", "CA": "Canada", "ES": "Spain",
    "DK": "Denmark", "CL": "Chile", "NO": "Norway", "RO": "Romania",
    "PT": "Portugal", "NL": "Netherlands", "CH": "Switzerland", "BD": "Bangladesh",
    "BA": "Bosnia and Herzegovina", "BE": "Belgium", "SI": "Slovenia", "MM": "Myanmar",
}


def norm_pn(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        d = str(int(v))
    else:
        d = re.sub(r"\D", "", str(v).strip())
    return d.zfill(10) if len(d) >= 8 else None


def blank(s: pd.Series) -> pd.Series:
    """True where the value is absent, empty or the string 'nan'."""
    return s.isna() | s.astype(str).str.strip().str.lower().isin(["", "nan", "none", "unknown"])


def main() -> int:
    # ------------------------------------------------------------ base set
    pn = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv",
                     dtype={"part_number": str}, low_memory=False)
    pn["part_number"] = pn["part_number"].str.zfill(10)
    base = pn[(pn["in_scope"] == True)  # noqa: E712
              & pn["bp_new_jpy"].notna()
              & pn["bp_prior_revised"].notna()].copy()
    base["customer_code"] = base["customer_code"].astype(str).str.split(".").str[0]

    tot_eur = float(base["net_sales_value"].sum())
    tot_qty = float(base["billed_qty"].sum())

    # ---------------------------------------------- source of supply fields
    lp = pd.read_parquet(DERIVED / "pricing_list_pn.parquet",
                         columns=["part_number", "newest_pn", "description", "source"])
    lp["part_number"] = lp["part_number"].astype(str).str.zfill(10)
    lp["newest_pn"] = lp["newest_pn"].astype(str).str.zfill(10)
    lp_list = lp.drop_duplicates("part_number").set_index("part_number")
    src_list = lp_list["source"]
    desc_list = lp_list["description"]

    sim = pd.read_parquet(DERIVED / "pricing_sim_pr00_l12m.parquet",
                          columns=["part_number", "source"])
    sim["part_number"] = sim["part_number"].astype(str).str.zfill(10)
    src_sim = sim.drop_duplicates("part_number").set_index("part_number")["source"]

    wb = openpyxl.load_workbook(SPEC_XLSX, read_only=True, data_only=True)
    ws = wb["PN data"]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    i_pn, i_so = hdr.index("part_number"), hdr.index("supply_origin")
    spec = pd.DataFrame([(str(r[i_pn]).zfill(10), r[i_so]) for r in it],
                        columns=["part_number", "supply_origin"])
    wb.close()
    src_spec = spec.drop_duplicates("part_number").set_index("part_number")["supply_origin"]

    # ------------------------------------------- country of origin fields
    # Reading 533k rows out of the September workbook takes about a minute, so
    # cache the two columns we need in the system temp folder rather than
    # leaving a stray file in the derived data folder.
    import tempfile
    cache = Path(tempfile.gettempdir()) / "isze_price_cd_origin_cache.parquet"
    if cache.exists():
        coo = pd.read_parquet(cache)
    else:
        wb = openpyxl.load_workbook(SEPT_XLSX, read_only=True, data_only=True)
        ws = wb["Sheet1"]
        rows = [(norm_pn(r[3]), norm_pn(r[4]), r[0])
                for r in ws.iter_rows(min_row=2, values_only=True)]
        wb.close()
        coo = pd.DataFrame(rows, columns=["part_number", "newest_pn", "origin_new"])
        coo.to_parquet(cache, index=False)
    or_sept = coo.drop_duplicates("part_number").set_index("part_number")["origin_new"]

    # ISZJ master data - a Japan-side file covering a narrow slice, but the only
    # one that carries a shipping location (J/T) next to its own origin claim.
    wb = openpyxl.load_workbook(ISZJ_XLSX, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    it = ws.iter_rows(values_only=True)
    h = [str(x).strip() if x is not None else "" for x in next(it)]
    ix = {k: h.index(k) for k in ("Parts No", "Origin", "Ship Loc.", "Activated in IE40")}
    iszj_rows = []
    for r in it:
        p = norm_pn(r[ix["Parts No"]])
        if not p:
            continue
        iszj_rows.append((p, r[ix["Origin"]], r[ix["Ship Loc."]], r[ix["Activated in IE40"]]))
    wb.close()
    iszj = pd.DataFrame(iszj_rows,
                        columns=["part_number", "iszj_origin", "iszj_ship", "iszj_active"])
    iszj = iszj.drop_duplicates("part_number").set_index("part_number")

    ie = pd.read_parquet(DERIVED / "pricing_pr00_ie40.parquet",
                         columns=["part_number", "newest_pn", "country_of_origin"])
    ie["part_number"] = ie["part_number"].astype(str).str.zfill(10)
    ie = ie.drop_duplicates("part_number")
    or_ie = ie.set_index("part_number")["country_of_origin"]

    # --------------------------------------------------------- assemble
    pn_agg = base.groupby("part_number").agg(
        eur=("net_sales_value", "sum"),
        qty=("billed_qty", "sum"),
        customers=("customer_code", "nunique"),
    )
    pn_agg["description"] = base.groupby("part_number")["billed_description"].first()
    w = pn_agg.join([
        src_list.rename("source_list"),
        src_sim.rename("source_sim"),
        src_spec.rename("source_spec"),
        or_sept.rename("origin_sept"),
        or_ie.rename("origin_ie40"),
        desc_list.rename("description_list"),
        iszj,
    ])
    w["description"] = w["description"].fillna(w["description_list"]).fillna("")

    # Part group from the parts catalogue - a label a reader can place.
    cat = pd.read_csv(DERIVED / "parts_catalog_dimension.csv",
                      dtype=str, low_memory=False,
                      usecols=["part_number", "pr00_group", "pr00_family"])
    cat = cat.drop_duplicates("part_number").set_index("part_number")
    w = w.join(cat)
    w["pr00_group"] = w["pr00_group"].fillna("Not classified")

    # ------------------------------------------------ gap flags
    spec_unknown = w["source_spec"].astype(str).str.startswith("UNKNOWN")
    no_src_direct = blank(w["source_list"].astype(object))
    no_src_sim = blank(w["source_sim"].astype(object))
    w["gap_no_source"] = spec_unknown | (no_src_direct & no_src_sim)
    # Origin: the IE40 PR00 list is the reference origin file. A blank there is a
    # gap even where the September file fills it, but say so, because the two are
    # not the same claim.
    w["gap_no_origin"] = blank(w["origin_ie40"].astype(object))
    w["gap_no_origin_anywhere"] = w["gap_no_origin"] & blank(w["origin_sept"].astype(object))
    w["origin_only_sept"] = w["gap_no_origin"] & ~blank(w["origin_sept"].astype(object))
    both_origin = ~blank(w["origin_ie40"].astype(object)) & ~blank(w["origin_sept"].astype(object))
    w["gap_origin_conflict"] = both_origin & (
        w["origin_ie40"].astype(str).str.strip().str.upper()
        != w["origin_sept"].astype(str).str.strip().str.upper())
    # The Japan master file carries its own origin claim on a narrow slice. Where
    # it disagrees with the reference list, the origin is not settled either.
    both_iszj = ~blank(w["origin_ie40"].astype(object)) & ~blank(w["iszj_origin"].astype(object))
    w["gap_origin_conflict_iszj"] = both_iszj & (
        w["origin_ie40"].astype(str).str.strip().str.upper()
        != w["iszj_origin"].astype(str).str.strip().str.upper())
    w["origin_conflict_any"] = w["gap_origin_conflict"] | w["gap_origin_conflict_iszj"]
    both_src = ~blank(w["source_list"].astype(object)) & ~blank(w["source_sim"].astype(object))
    w["gap_source_conflict"] = both_src & (w["source_list"] != w["source_sim"])

    # A source the reader can act on: prefer the price list, then the model.
    w["source_held"] = w["source_list"].where(~blank(w["source_list"].astype(object)))
    w["source_held"] = w["source_held"].fillna(
        w["source_sim"].where(~blank(w["source_sim"].astype(object))))

    # Uneven population of the September origin column, split by source of supply.
    w["origin_sept_filled"] = ~blank(w["origin_sept"].astype(object))
    w["origin_thai"] = (w["source_held"] == "T") & w["origin_sept_filled"]
    w["origin_japan"] = (w["source_held"] == "J") & w["origin_sept_filled"]

    # A source the reader can act on: prefer the price list, then the model.
    # The price list is the authority for the source of supply, so a part with a
    # source only in the pricing model still needs the price list completed. Say
    # which file the value came from, or the column reads as a contradiction.
    w["source_held"] = w["source_list"].where(~blank(w["source_list"].astype(object)))
    w["source_held"] = w["source_held"].fillna(
        w["source_sim"].where(~blank(w["source_sim"].astype(object))))
    w["source_from_list"] = ~blank(w["source_list"].astype(object))
    w["source_only_model"] = ~w["source_from_list"] & ~blank(w["source_sim"].astype(object))

    needs = w[w["gap_no_source"] | w["gap_no_origin"]
              | w["gap_origin_conflict"] | w["gap_source_conflict"]
              | w["gap_origin_conflict_iszj"]].copy()

    # ------------------------------------------------------- what is missing
    def missing_text(r):
        parts = []
        if r["gap_no_source"]:
            parts.append("No source of supply in the price list"
                         if r["source_only_model"] else "No source of supply recorded")
        if r["gap_no_origin"]:
            if r["origin_only_sept"]:
                parts.append("No country of origin in the reference origin list "
                             "(the September file fills it)")
            else:
                parts.append("No country of origin recorded")
        if r["gap_origin_conflict"]:
            a = str(r["origin_ie40"]).strip().upper()
            b = str(r["origin_sept"]).strip().upper()
            parts.append(f"Conflicting country of origin ({ORIGIN_NAME.get(a, a)} vs {ORIGIN_NAME.get(b, b)}), "
                         "reference list vs September update")
        if r["gap_origin_conflict_iszj"]:
            a = str(r["origin_ie40"]).strip().upper()
            b = str(r["iszj_origin"]).strip().upper()
            parts.append(f"Conflicting country of origin ({ORIGIN_NAME.get(a, a)} vs {ORIGIN_NAME.get(b, b)}), "
                         "reference list vs Japan master file")
        if r["gap_source_conflict"]:
            parts.append("Conflicting source of supply (price list vs model)")
        return "; ".join(parts)

    needs["missing"] = needs.apply(missing_text, axis=1)

    def source_held_text(r):
        v = r["source_held"]
        if pd.isna(v) or str(v).strip() in ("", "nan"):
            return "None held"
        label = SOURCE_LABEL.get(str(v).strip(), str(v).strip())
        if r["source_from_list"]:
            return f"{label} (price list)"
        return f"{label} (model only)"

    needs["source_held_label"] = needs.apply(source_held_text, axis=1)
    n_model_only = int((needs["gap_no_source"] & needs["source_only_model"]).sum())
    n_none_anywhere = int((needs["gap_no_source"] & ~needs["source_only_model"]).sum())
    needs = needs.sort_values("eur", ascending=False)

    needs_eur = float(needs["eur"].sum())
    needs_qty = float(needs["qty"].sum())

    # --------------------------------------------------------- by customer
    gap_pns = set(needs.index)
    bycust = (
        base[base["part_number"].isin(gap_pns)]
        .groupby("customer_code")
        .agg(**{
            "Part numbers needing a source": ("part_number", "nunique"),
            "Parts billed (EUR)": ("net_sales_value", "sum"),
        })
    )
    basket = base.groupby("customer_code")["net_sales_value"].sum()
    bycust["Share of that customer's basket"] = (
        100 * bycust["Parts billed (EUR)"] / basket).round(1)

    # Customer names from the same file the pack uses.
    labels = (base.dropna(subset=["distributor_code"])
              .groupby("customer_code")["distributor_code"]
              .agg(lambda s: s.dropna().iloc[0] if len(s.dropna()) else ""))
    bycust["Customer"] = [
        (labels.get(c, "") + " (" + c + ")").strip() if labels.get(c, "") else c
        for c in bycust.index]
    bycust = bycust.reset_index(drop=True).set_index("Customer")
    bycust = bycust.sort_values("Parts billed (EUR)", ascending=False).reset_index()
    bycust.columns = ["Customer", "Part numbers needing a source",
                      "Parts billed (EUR)", "Share of that customer's basket"]

    # ----------------------------------------------------------- coverage
    cov_rows = []
    for label, series, note in [
        ("Source of supply", w["source_list"].astype(object), "Our price list"),
        ("Source of supply", w["source_sim"].astype(object), "Pricing model"),
        ("Source of supply", w["source_spec"].astype(object), "Pricing specification"),
        ("Country of origin", w["origin_ie40"].astype(object), "Reference price list"),
        ("Country of origin", w["origin_sept"].astype(object), "September price update"),
        ("Country of origin", w["iszj_origin"].astype(object), "Japan master file (narrow slice)"),
    ]:
        ok = ~blank(series)
        cov_rows.append({
            "What": label,
            "Where it is held": note,
            "Part numbers with it": int(ok.sum()),
            "Share of part numbers": round(100 * ok.sum() / len(w), 1),
            "Parts billed (EUR) with it": float(w.loc[ok, "eur"].sum()),
            "Share of parts billed": round(100 * w.loc[ok, "eur"].sum() / tot_eur, 1),
            "Units with it": float(w.loc[ok, "qty"].sum()),
        })
    cov = pd.DataFrame(cov_rows)

    # --------------------------------------------------------- write xlsx
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        pd.DataFrame().to_excel(xl, sheet_name="What this is")
        pd.DataFrame().to_excel(xl, sheet_name="By part number")
        pd.DataFrame().to_excel(xl, sheet_name="By customer")
        pd.DataFrame().to_excel(xl, sheet_name="Coverage")

    book = openpyxl.load_workbook(OUT_XLSX)

    # ---- shared styling helpers
    fill_navy = PatternFill("solid", fgColor=NAVY)
    fill_cream = PatternFill("solid", fgColor=CREAM)
    fill_pale = PatternFill("solid", fgColor=PALE)
    fill_input = PatternFill("solid", fgColor="FBEEE8")
    fill_band = PatternFill("solid", fgColor=BAND)
    thin = Side(style="thin", color="B8C2D0")
    input_side = Side(style="medium", color=TERRACOTTA)
    font_head = Font(bold=True, color="FFFFFF", size=10)
    font_title = Font(bold=True, color=NAVY, size=15)
    font_body = Font(size=10)
    font_bold = Font(size=10, bold=True)

    def head_row(ws, row, ncols):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=row, column=c)
            cell.fill = fill_navy
            cell.font = font_head
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = Border(bottom=thin)
        ws.row_dimensions[row].height = 30

    def set_widths(ws, widths):
        for i, wd in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = min(wd, 45)

    # ================================================= Sheet 1: What this is
    s1 = book["What this is"]
    s1.sheet_view.showGridLines = False
    s1["A1"] = "Parts where we do not hold the source or the country of origin"
    s1["A1"].font = font_title
    s1["A3"] = (
        f"Of the {len(w):,} part numbers priced on both sides in the last twelve months, "
        f"{len(needs):,} need something we cannot answer from the files we hold. "
        f"They carry EUR {needs_eur:,.0f} of the EUR {tot_eur:,.0f} billed in the window "
        f"({100 * needs_eur / tot_eur:.1f} percent) and {needs_qty:,.0f} units.")
    s1["A3"].font = font_body
    s1.merge_cells("A3:F3")
    s1["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    s1.row_dimensions[3].height = 32

    s1["A5"] = "Why it is only these"
    s1["A5"].font = Font(bold=True, color=NAVY, size=11)
    s1["A6"] = (
        "Two different things live in the files and they are not the same thing. "
        "The source of supply says which entity supplies the part - Japan through IML, "
        "or Thailand through IMIT. The country of origin says where the part is made. "
        "A part can be supplied from Japan and made in China, so a Japanese source with a "
        "Chinese origin is not a contradiction. It is only listed here when the files "
        "actually disagree with each other.")
    s1.merge_cells("A6:F6")
    s1["A6"].alignment = Alignment(wrap_text=True, vertical="top")
    s1.row_dimensions[6].height = 58

    s1["A8"] = "What is missing, and what it is worth"
    s1["A8"].font = Font(bold=True, color=NAVY, size=11)
    kind_rows = [
        ("No source of supply in the price list (a value exists in the pricing model only)",
         n_model_only, float(needs.loc[needs["gap_no_source"] & needs["source_only_model"], "eur"].sum())),
        ("No source of supply anywhere we hold",
         n_none_anywhere, float(needs.loc[needs["gap_no_source"] & ~needs["source_only_model"], "eur"].sum())),
        ("No country of origin in the reference list (the September file fills it)",
         int(w["origin_only_sept"].sum()), float(w.loc[w["origin_only_sept"], "eur"].sum())),
        ("No country of origin recorded in any file",
         int(w["gap_no_origin_anywhere"].sum()), float(w.loc[w["gap_no_origin_anywhere"], "eur"].sum())),
        ("Country of origin contradicts between the two origin files",
         int(w["gap_origin_conflict"].sum()), float(w.loc[w["gap_origin_conflict"], "eur"].sum())),
        ("Country of origin contradicts between the reference list and the Japan master file",
         int(w["gap_origin_conflict_iszj"].sum()), float(w.loc[w["gap_origin_conflict_iszj"], "eur"].sum())),
        ("Source of supply contradicts between two files",
         int(w["gap_source_conflict"].sum()), float(w.loc[w["gap_source_conflict"], "eur"].sum())),
    ]
    s1["A9"], s1["B9"], s1["C9"] = "What is missing", "Part numbers", "Parts billed (EUR)"
    head_row(s1, 9, 3)
    r = 10
    for label, n, e in kind_rows:
        s1.cell(row=r, column=1, value=label).font = font_body
        s1.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        s1.cell(row=r, column=2, value=n).font = font_body
        c = s1.cell(row=r, column=3, value=e)
        c.font = font_body
        c.number_format = "#,##0"
        s1.row_dimensions[r].height = 30
        if label in ("No country of origin recorded in any file",):
            s1.cell(row=r, column=1).font = Font(size=10, color="5A6472")
            s1.cell(row=r, column=2).font = Font(size=10, color="5A6472")
            s1.cell(row=r, column=3).font = Font(size=10, color="5A6472")
        r += 1
    s1.cell(row=r, column=1, value="Part numbers needing something (union)").font = font_bold
    s1.cell(row=r, column=2, value=len(needs)).font = font_bold
    tc = s1.cell(row=r, column=3, value=needs_eur)
    tc.font = font_bold
    tc.number_format = "#,##0"
    for c in range(1, 4):
        s1.cell(row=r, column=c).fill = fill_band
        s1.cell(row=r, column=c).border = Border(top=Side(style="medium", color=NAVY))

    r += 3
    s1.cell(row=r, column=1, value="What we do hold, on the same set").font = Font(bold=True, color=NAVY, size=11)
    r += 1
    start = r
    cc = cov[["What", "Where it is held", "Part numbers with it",
              "Share of part numbers", "Share of parts billed"]]
    for j, col in enumerate(cc.columns, start=1):
        s1.cell(row=r, column=j, value=col)
    head_row(s1, r, len(cc.columns))
    r += 1
    for _, row in cc.iterrows():
        for j, col in enumerate(cc.columns, start=1):
            cell = s1.cell(row=r, column=j, value=row[col])
            cell.font = font_body
            if col == "Share of part numbers" or col == "Share of parts billed":
                cell.number_format = "0.0"
        r += 1

    r += 2
    s1.cell(row=r, column=1, value="How to use it").font = Font(bold=True, color=NAVY, size=11)
    r += 1
    s1.cell(row=r, column=1,
            value=("Go to the sheet By part number. It is sorted by what the part is worth. "
                   "Fill in the last column, Source you provide, and the file becomes the request "
                   "back to the supplier. Sheet By customer shows the same list per market, so you "
                   "can see whether it sits in a few places or everywhere. Sheet Coverage shows "
                   "what we already hold."))
    s1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    s1.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    s1.row_dimensions[r].height = 46

    r += 2
    legend = s1.cell(row=r, column=1,
                     value="The pale orange column, Source you provide, is for you to fill in. "
                           "Everything else is read from the files.")
    legend.font = Font(size=10, italic=True, color=TERRACOTTA)
    s1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)

    r += 2
    s1.cell(row=r, column=1,
            value=(f"Window: {WINDOW_START} to {WINDOW_END}. Priced on both sides of the "
                   f"comparison, network customers only. Euro at {FX} JPY per EUR."))
    s1.cell(row=r, column=1).font = Font(size=9, color="5A6472")
    s1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)

    set_widths(s1, [46, 26, 22, 20, 22, 18])

    # ================================================= Sheet 2: By part number
    s2 = book["By part number"]
    s2.sheet_view.showGridLines = False
    cols2 = ["Part number", "Description", "Part group", "Parts billed (EUR)", "Units",
             "Customers", "What is missing", "Source we hold", "Source you provide"]
    for j, c in enumerate(cols2, start=1):
        s2.cell(row=1, column=j, value=c)
    head_row(s2, 1, len(cols2))

    r = 2
    for _, row in needs.iterrows():
        s2.cell(row=r, column=1, value=row.name).font = font_body
        s2.cell(row=r, column=2, value=str(row["description"])[:120]).font = font_body
        s2.cell(row=r, column=3, value=row["pr00_group"]).font = font_body
        c = s2.cell(row=r, column=4, value=round(float(row["eur"]), 2))
        c.font = font_body
        c.number_format = "#,##0.00"
        c = s2.cell(row=r, column=5, value=int(row["qty"]))
        c.font = font_body
        c.number_format = "#,##0"
        s2.cell(row=r, column=6, value=int(row["customers"])).font = font_body
        mc = s2.cell(row=r, column=7, value=row["missing"])
        mc.font = font_body
        # The conflict wording runs long; wrap it rather than let it clip at the
        # 45-character column limit, and give the row the height to show it.
        mc.alignment = Alignment(wrap_text=True, vertical="top")
        if len(str(row["missing"])) > 52:
            s2.row_dimensions[r].height = 30
        s2.cell(row=r, column=8, value=row["source_held_label"]).font = font_body
        inp = s2.cell(row=r, column=9, value=None)
        inp.fill = fill_input
        inp.border = Border(left=input_side, right=input_side, top=thin, bottom=thin)
        for c in range(1, 9):
            s2.cell(row=r, column=c).border = Border(bottom=thin)
        if r % 2 == 1:
            for c in range(1, 9):
                if not s2.cell(row=r, column=c).fill.fgColor.rgb:
                    s2.cell(row=r, column=c).fill = fill_cream
        r += 1

    # Total row, clearly separated and never mistakable for a data row.
    tr = r + 1
    s2.cell(row=tr, column=1, value="TOTAL").font = Font(bold=True, color=NAVY, size=10)
    s2.cell(row=tr, column=2,
            value=f"{len(needs):,} part numbers needing a source or origin").font = Font(bold=True, color=NAVY, size=10)
    tot = s2.cell(row=tr, column=4, value=needs_eur)
    tot.font = Font(bold=True, color=NAVY, size=10)
    tot.number_format = "#,##0.00"
    tq = s2.cell(row=tr, column=5, value=int(needs_qty))
    tq.font = Font(bold=True, color=NAVY, size=10)
    tq.number_format = "#,##0"
    for c in range(1, len(cols2) + 1):
        cell = s2.cell(row=tr, column=c)
        cell.fill = fill_band
        cell.border = Border(top=Side(style="medium", color=NAVY), bottom=Side(style="medium", color=NAVY))

    s2.freeze_panes = "A2"
    s2.auto_filter.ref = f"A1:I{r - 1}"
    set_widths(s2, [14, 42, 22, 18, 12, 11, 46, 22, 22])

    # ==================================================== Sheet 3: By customer
    s3 = book["By customer"]
    s3.sheet_view.showGridLines = False
    for j, c in enumerate(bycust.columns, start=1):
        s3.cell(row=1, column=j, value=c)
    head_row(s3, 1, len(bycust.columns))
    r = 2
    for _, row in bycust.iterrows():
        s3.cell(row=r, column=1, value=row["Customer"]).font = font_body
        s3.cell(row=r, column=2, value=int(row["Part numbers needing a source"])).font = font_body
        c = s3.cell(row=r, column=3, value=round(float(row["Parts billed (EUR)"]), 2))
        c.font = font_body
        c.number_format = "#,##0.00"
        c = s3.cell(row=r, column=4, value=float(row["Share of that customer's basket"]))
        c.font = font_body
        c.number_format = "0.0"
        for cc_ in range(1, 5):
            s3.cell(row=r, column=cc_).border = Border(bottom=thin)
        r += 1
    tr = r + 1
    s3.cell(row=tr, column=1, value="NETWORK TOTAL").font = Font(bold=True, color=NAVY, size=10)
    s3.cell(row=tr, column=2, value=len(needs)).font = Font(bold=True, color=NAVY, size=10)
    tc = s3.cell(row=tr, column=3, value=needs_eur)
    tc.font = Font(bold=True, color=NAVY, size=10)
    tc.number_format = "#,##0.00"
    s3.cell(row=tr, column=4, value=round(100 * needs_eur / tot_eur, 1)).font = Font(bold=True, color=NAVY, size=10)
    s3.cell(row=tr, column=4).number_format = "0.0"
    for c in range(1, 5):
        s3.cell(row=tr, column=c).fill = fill_band
        s3.cell(row=tr, column=c).border = Border(top=Side(style="medium", color=NAVY), bottom=Side(style="medium", color=NAVY))
    tr += 1
    s3.cell(row=tr, column=1,
            value=("Part numbers and shares are not additive down the column: one part number "
                   "can be billed by several customers, and each share is against that "
                   "customer's own basket."))
    s3.cell(row=tr, column=1).font = Font(size=9, italic=True, color="5A6472")
    s3.merge_cells(start_row=tr, start_column=1, end_row=tr, end_column=4)
    s3.freeze_panes = "A2"
    s3.auto_filter.ref = f"A1:D{r - 1}"
    set_widths(s3, [30, 26, 20, 26])

    # ====================================================== Sheet 4: Coverage
    s4 = book["Coverage"]
    s4.sheet_view.showGridLines = False
    s4["A1"] = "What we do hold, on the parts that matter"
    s4["A1"].font = font_title
    s4["A3"] = (f"Base set: {len(w):,} part numbers priced on both sides, "
                f"EUR {tot_eur:,.0f} of parts billed, {tot_qty:,.0f} units, "
                f"{WINDOW_START} to {WINDOW_END}.")
    s4["A3"].font = font_body
    s4.merge_cells("A3:F3")
    r = 5
    for j, c in enumerate(cov.columns, start=1):
        s4.cell(row=r, column=j, value=c)
    head_row(s4, r, len(cov.columns))
    r += 1
    for _, row in cov.iterrows():
        for j, c in enumerate(cov.columns, start=1):
            cell = s4.cell(row=r, column=j, value=row[c])
            cell.font = font_body
            if c in ("Part numbers with it", "Units with it"):
                cell.number_format = "#,##0"
            elif c in ("Share of part numbers", "Share of parts billed"):
                cell.number_format = "0.0"
            elif c == "Parts billed (EUR) with it":
                cell.number_format = "#,##0.00"
        r += 1

    r += 2
    s4.cell(row=r, column=1, value="Where each field lives, and what it means").font = Font(bold=True, color=NAVY, size=11)
    r += 1
    field_rows = [
        ("Source of supply",
         "Which entity supplies the part. Two values only: J is Japan through IML, T is Thailand through IMIT.",
         "Our price list, the pricing model, and the pricing specification."),
        ("Country of origin",
         "Where the part is made. More than forty countries, and it is not the same thing as the source of supply.",
         "The reference price list, and the September price update."),
    ]
    s4.cell(row=r, column=1, value="Field")
    s4.cell(row=r, column=2, value="What it means")
    s4.cell(row=r, column=3, value="Where it is held")
    head_row(s4, r, 3)
    r += 1
    for a, b, c in field_rows:
        s4.cell(row=r, column=1, value=a).font = font_body
        s4.cell(row=r, column=2, value=b).font = font_body
        s4.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        s4.cell(row=r, column=3, value=c).font = font_body
        s4.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        s4.row_dimensions[r].height = 34
        r += 1

    set_widths(s4, [22, 62, 52])

    # A finding in its own right: the September file's origin column is not
    # populated evenly. It largely restates the Thai list.
    r += 2
    s4.cell(row=r, column=1,
            value="The September price file fills its origin column unevenly").font = Font(bold=True, color=NAVY, size=11)
    r += 1
    s4.cell(row=r, column=1,
            value=(f"On the same {len(w):,} part numbers, the September file records a country "
                   f"of origin for {int((w['origin_thai']).sum()):,} of the "
                   f"Thai-sourced parts and only {int((w['origin_japan']).sum()):,} of the "
                   f"Japan-sourced parts. On the Japan-sourced parts that it does fill in, "
                   f"the origin is usually not Japan - it is where the part is actually made, "
                   f"such as the United States, Czechia or China. The column is therefore a "
                   f"partial origin field, not a copy of the source of supply."))
    s4.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    s4.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    s4.row_dimensions[r].height = 62
    r += 1
    s4.cell(row=r, column=1,
            value=("The reference price list, by contrast, records an origin for "
                   f"{int((~blank(w['origin_ie40'].astype(object))).sum()):,} of the same part numbers, "
                   "so that is the field to read for origin today."))
    s4.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    s4.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    s4.row_dimensions[r].height = 30

    book.move_sheet("What this is", offset=-3)
    book.save(OUT_XLSX)

    # ------------------------------------------------------------- launcher
    OUT_CMD.write_bytes(
        ("@echo off\r\n"
         'start "" "%~dp0Parts_needing_source_or_origin.xlsx"\r\n').encode("ascii"))

    # ----------------------------------------------------------------- meta
    meta = {
        "generated": date.today().isoformat(),
        "window": {"start": "2025-07-01", "end": "2026-06-30"},
        "base": {
            "rows": int(len(base)),
            "part_numbers": int(len(w)),
            "parts_billed_eur": round(tot_eur, 2),
            "units": int(tot_qty),
            "source": "01_data/00_derived/price_bp_weighted_compare_pn.csv, in_scope and priced both sides",
        },
        "needs": {
            "part_numbers": int(len(needs)),
            "parts_billed_eur": round(needs_eur, 2),
            "units": int(needs_qty),
            "share_of_parts_billed": round(100 * needs_eur / tot_eur, 1),
            "share_of_units": round(100 * needs_qty / tot_qty, 1),
            "source_in_model_only": n_model_only,
            "source_nowhere": n_none_anywhere,
            "origin_not_in_reference_list": int(w["origin_only_sept"].sum()),
            "origin_nowhere": int(w["gap_no_origin_anywhere"].sum()),
        },
        "september_origin_population": {
            "thai_sourced_with_origin": int(w["origin_thai"].sum()),
            "japan_sourced_with_origin": int(w["origin_japan"].sum()),
            "note": "the September file's origin column is populated far more densely on Thai-sourced parts",
        },
        "japan_master_file": {
            "path": "01_data/01_Pricing/ISZJ_master_data_competitive_parts.xlsx",
            "part_numbers_in_file": int(len(iszj)),
            "overlap_with_base_set": int(w["iszj_origin"].notna().sum()),
            "parts_billed_eur_in_overlap": round(float(w.loc[w["iszj_origin"].notna(), "eur"].sum()), 2),
            "note": ("carries its own Origin and a Ship Loc. (J/T). Overlaps only a narrow slice of "
                     "the billed book, so it fills none of the missing-source part numbers"),
        },
        "origin_conflicts_with_japan_master_file": [
            {"part_number": str(i), "reference_list": r["origin_ie40"], "japan_master": r["iszj_origin"],
             "parts_billed_eur": round(float(r["eur"]), 2)}
            for i, r in w[w["gap_origin_conflict_iszj"]].sort_values("eur", ascending=False).iterrows()
        ],
        "by_kind": {label: {"part_numbers": n, "parts_billed_eur": round(e, 2)}
                    for label, n, e in kind_rows},
        "by_part_group": (needs.groupby("pr00_group")
                          .agg(part_numbers=("eur", "size"), parts_billed_eur=("eur", "sum"))
                          .sort_values("parts_billed_eur", ascending=False)
                          .round(2).to_dict("index")),
        "coverage": cov.to_dict("records"),
        "conflict_examples": {
            "source_of_supply": [
                {"part_number": str(i), "price_list": r["source_list"], "model": r["source_sim"],
                 "parts_billed_eur": round(float(r["eur"]), 2)}
                for i, r in w[w["gap_source_conflict"]].iterrows()
            ],
            "country_of_origin": [
                {"part_number": str(i), "ie40": r["origin_ie40"], "september": r["origin_sept"],
                 "parts_billed_eur": round(float(r["eur"]), 2)}
                for i, r in w[w["gap_origin_conflict"]].sort_values("eur", ascending=False).iterrows()
            ],
        },
        "outputs": [str(OUT_XLSX.relative_to(ISZE)), str(OUT_CMD.relative_to(ISZE))],
        "not_inspected": [
            "No SAP material master or purchasing-source table (MARC/EINA/EORD class) was found "
            "under 01_data/12_raw, 01_data/08_Distributor or 01_data/90_INBOX.",
            "The SAP margin extract in 01_data/90_INBOX/margin_analysis_mail_pull carries a Plant "
            "column, but it maps one-to-one to the sales organisation (ISZ7=IE40, ISZ5=IE30, "
            "ISZ9=IE50), so it does not discriminate between a Japan and a Thailand source.",
            "The grid of 12_raw subfolders was listed by name only; nothing under it was read.",
        ],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # -------------------------------------------------------------- console
    print("=" * 78)
    print("PARTS NEEDING A SOURCE OR ORIGIN")
    print("=" * 78)
    print(f"base part numbers        : {len(w):,}")
    print(f"base parts billed (EUR)  : {tot_eur:,.2f}")
    print(f"needing something        : {len(needs):,} part numbers, "
          f"EUR {needs_eur:,.2f} ({100 * needs_eur / tot_eur:.1f}%), {needs_qty:,.0f} units")
    print(f"  of which a value exists in the model only : {n_model_only} PN")
    print(f"  of which nothing anywhere                 : {n_none_anywhere} PN")
    print()
    for label, n, e in kind_rows:
        print(f"  {label:72} {n:5d} PN  EUR {e:14,.2f}")
    print()
    print("top 25 by euro:")
    show = needs.head(25)[["eur", "qty", "customers", "missing", "source_held_label"]].copy()
    show.insert(0, "pn", show.index)
    show["eur"] = show["eur"].round(0)
    print(show.to_string(index=False))
    print()
    print("missing-source concentration by part group:")
    g = (needs.groupby("pr00_group")
         .agg(pn=("eur", "size"), eur=("eur", "sum"))
         .sort_values("eur", ascending=False))
    print(g.to_string())
    print()
    print("by customer (top 25):")
    print(bycust.head(25).to_string(index=False))
    print()
    print("wrote:", OUT_XLSX.name, "|", OUT_CMD.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
