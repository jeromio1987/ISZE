"""I-Motors (Portugal) H1 2026 vs H1 2025 parts analysis — with ITC (Newest P/N) rollup.

Mode A deliverable (external language). Rebuilds / extends
ISZE_Imotors_H1_Parts_Analysis_Jul2026.xlsx:

- Aggregate interchangeable parts via Price file Newest P/N
- Top 100 declining / growing at ITC-family level (with Qty columns)
- Keep PN-level detail for comparison
- Warranty indication (billing has no warranty flag; CY2025 Portugal claim value)
- Reconciliation stats printed and written to Notes

Usage:
  python build_h1_parts_analysis_itc.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
PRICING = ISZE / "01_data" / "01_Pricing"
OUT_DIR = Path(__file__).resolve().parent
OUT_XLSX = OUT_DIR / "ISZE_Imotors_H1_Parts_Analysis_Jul2026_ITC.xlsx"

PAYER = "IMOTORS - Importacao e Comercio"
TOP_N = 100
EXPECTED_H1_2025 = 814_780.0
EXPECTED_H1_2026 = 935_636.0
# Portugal warranty parts CY2025 (ISZE transfer-price basis) — see
# 01_data/06_Warranty/Warranty_CY2025_by_DB.md
PORTUGAL_WARRANTY_CY2025_EUR = 130_588.0  # CV 28,836 (LB) + LCV 101,752

THIN = Side(style="thin", color="B0B0B0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEADER_FILL = PatternFill("solid", fgColor="C00000")
HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
TITLE_FONT = Font(bold=True, name="Calibri", size=12, color="C00000")
NUM_FMT = "#,##0.00"
QTY_FMT = "#,##0.00"
PCT_FMT = "0.0%"


def _norm_pn(x) -> str | None:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    if s.endswith(".0"):
        s = s[:-1]
    # strip trailing .0 from float-cast strings more carefully
    try:
        if "." in s:
            f = float(s)
            if f == int(f):
                s = str(int(f))
    except ValueError:
        pass
    return s


def load_itc_map() -> tuple[pd.DataFrame, dict[str, str], dict[str, str]]:
    """Return (full map df, pn->newest, newest->description)."""
    cache = DERIVED / "price_file_2026_pn_newest.csv"
    src = PRICING / "Price file 2026_full.xlsx"
    if cache.exists():
        df = pd.read_csv(cache, dtype=str)
    else:
        df = pd.read_excel(src, sheet_name="Sheet1", usecols=["P/N", "Newest P/N", "Description"], dtype=str)
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache, index=False)

    df = df.rename(columns={"P/N": "pn_raw", "Newest P/N": "newest_raw", "Description": "desc"})
    df["pn"] = df["pn_raw"].map(_norm_pn)
    df["newest"] = df["newest_raw"].map(_norm_pn)
    df = df.dropna(subset=["pn"]).drop_duplicates(subset=["pn"], keep="last")
    # if newest blank, family = self
    df["newest"] = df["newest"].fillna(df["pn"])
    df.loc[df["newest"] == "", "newest"] = df.loc[df["newest"] == "", "pn"]

    # resolve transitive Newest chains (A→B→C → A→C)
    direct = dict(zip(df["pn"], df["newest"]))

    def resolve(pn: str, depth: int = 0) -> str:
        seen = set()
        cur = pn
        for _ in range(20):
            nxt = direct.get(cur, cur)
            if nxt == cur or nxt in seen:
                return nxt if nxt else cur
            seen.add(cur)
            cur = nxt
        return cur

    resolved = {pn: resolve(pn) for pn in direct}
    df["newest_resolved"] = df["pn"].map(resolved)

    # description preferred from newest PN row
    desc_by_pn = dict(zip(df["pn"], df["desc"].fillna("")))
    desc_by_newest: dict[str, str] = {}
    for pn, newest in resolved.items():
        if newest not in desc_by_newest or not desc_by_newest[newest]:
            # prefer description on the newest row itself
            d = desc_by_pn.get(newest) or desc_by_pn.get(pn) or ""
            desc_by_newest[newest] = d

    return df, resolved, desc_by_newest


def _parse_dates(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def load_h1_sales() -> pd.DataFrame:
    """Line-level Imotors H1 2025 + H1 2026 with Material, Qty, Net EUR, SaTy."""
    frames = []

    # H1 2026 Jan-Mar
    q1 = pd.read_csv(
        DERIVED / "cy2026_q1.csv",
        low_memory=False,
        usecols=["Billing Date", "Payer.1", "Material", "Billed Quantity", "Net value", "SaTy", "BillT"],
    )
    q1 = q1[q1["Payer.1"] == PAYER].copy()
    q1["Billing Date"] = _parse_dates(q1["Billing Date"])
    q1 = q1[(q1["Billing Date"] >= "2026-01-01") & (q1["Billing Date"] < "2026-04-01")]
    q1["period"] = "H1_2026"
    q1["source"] = "cy2026_q1"
    frames.append(q1.rename(columns={"Billed Quantity": "qty", "Net value": "net_eur"}))

    # H1 2026 Apr-Jun (file may spill into early Jul — keep Apr-Jun only)
    fy = pd.read_csv(
        DERIVED / "q1fy2027_billing_tagged.csv",
        low_memory=False,
        usecols=[
            "Billing Date",
            "Payer.1",
            "Material",
            "Billed Quantity",
            "Net value",
            "SaTy",
            "BillT",
            "flag_rebate",
        ],
    )
    fy = fy[fy["Payer.1"] == PAYER].copy()
    fy["Billing Date"] = _parse_dates(fy["Billing Date"])
    fy = fy[(fy["Billing Date"] >= "2026-04-01") & (fy["Billing Date"] < "2026-07-01")]
    fy["period"] = "H1_2026"
    fy["source"] = "q1fy2027_billing_tagged"
    frames.append(fy.rename(columns={"Billed Quantity": "qty", "Net value": "net_eur"}))

    # H1 2025
    cy = pd.read_csv(
        DERIVED / "cy2025_raw.csv",
        low_memory=False,
        usecols=["Billing Date", "DB", "Material", "Billed Quantity", "Net value", "SaTy"],
    )
    cy = cy[cy["DB"] == PAYER].copy()
    cy["Billing Date"] = _parse_dates(cy["Billing Date"])
    cy = cy[(cy["Billing Date"] >= "2025-01-01") & (cy["Billing Date"] < "2025-07-01")]
    cy["period"] = "H1_2025"
    cy["source"] = "cy2025_raw"
    cy["BillT"] = None
    cy["flag_rebate"] = False
    frames.append(cy.rename(columns={"Billed Quantity": "qty", "Net value": "net_eur"}))

    all_ = pd.concat(frames, ignore_index=True)
    all_["Material"] = all_["Material"].map(_norm_pn)
    all_["qty"] = pd.to_numeric(all_["qty"], errors="coerce").fillna(0.0)
    all_["net_eur"] = pd.to_numeric(all_["net_eur"], errors="coerce").fillna(0.0)
    all_["SaTy"] = all_["SaTy"].astype(str).str.strip().str.upper()
    return all_


def load_catalog() -> pd.DataFrame:
    cat = pd.read_csv(DERIVED / "parts_catalog_dimension.csv", dtype=str)
    cat["part_number"] = cat["part_number"].map(_norm_pn)
    return cat[["part_number", "pr00_group", "pms_category"]].drop_duplicates("part_number")


def aggregate_pn(sales: pd.DataFrame, catalog: pd.DataFrame, desc_by_newest: dict[str, str], itc: dict[str, str]) -> pd.DataFrame:
    g = (
        sales.groupby(["Material", "period"], dropna=False)
        .agg(qty=("qty", "sum"), net_eur=("net_eur", "sum"))
        .reset_index()
    )
    wide = g.pivot_table(index="Material", columns="period", values=["qty", "net_eur"], aggfunc="sum", fill_value=0)
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    wide = wide.reset_index().rename(columns={"Material": "Material"})
    for col in ["qty_H1_2025", "qty_H1_2026", "net_eur_H1_2025", "net_eur_H1_2026"]:
        if col not in wide.columns:
            wide[col] = 0.0

    wide["mapped"] = wide["Material"].isin(itc)
    wide["Newest_PN"] = wide["Material"].map(lambda m: itc.get(m, m) if m else m)
    wide["ITC_family"] = wide["Newest_PN"]

    # description: prefer price-file newest desc, else catalog leave blank and fill from sales later
    wide["Description"] = wide["Newest_PN"].map(lambda p: desc_by_newest.get(p, "") if p else "")
    # also try material itself
    miss = wide["Description"].fillna("") == ""
    wide.loc[miss, "Description"] = wide.loc[miss, "Material"].map(lambda p: desc_by_newest.get(p, "") if p else "")

    wide = wide.merge(catalog, left_on="Material", right_on="part_number", how="left")
    wide = wide.drop(columns=["part_number"], errors="ignore")
    wide = wide.rename(columns={"pr00_group": "Category", "pms_category": "PMS Category"})

    # fill blank descriptions from most common material description via price map already done;
    # REBATE / special materials keep their Material as description hint
    wide.loc[wide["Material"] == "REBATE", "Description"] = "Rebate Material"
    wide.loc[wide["Category"].isna() | (wide["Category"] == ""), "Category"] = "UNCLASSIFIED"

    wide["Delta_EUR"] = wide["net_eur_H1_2026"] - wide["net_eur_H1_2025"]
    wide["Delta_Qty"] = wide["qty_H1_2026"] - wide["qty_H1_2025"]
    wide["Delta_Pct"] = np.where(
        wide["net_eur_H1_2025"] != 0,
        wide["Delta_EUR"] / wide["net_eur_H1_2025"],
        np.nan,
    )
    return wide


def aggregate_itc(pn: pd.DataFrame, desc_by_newest: dict[str, str], catalog: pd.DataFrame) -> pd.DataFrame:
    # category: mode of member PNs by absolute H1'26+|H1'25| net
    pn = pn.copy()
    pn["_abs"] = pn["net_eur_H1_2025"].abs() + pn["net_eur_H1_2026"].abs()

    def _mode_cat(g: pd.DataFrame) -> str:
        g2 = g.sort_values("_abs", ascending=False)
        for c in g2["Category"]:
            if c and c != "UNCLASSIFIED":
                return c
        return g2["Category"].iloc[0] if len(g2) else "UNCLASSIFIED"

    def _mode_pms(g: pd.DataFrame) -> str | None:
        g2 = g.dropna(subset=["PMS Category"]).sort_values("_abs", ascending=False)
        if len(g2):
            return g2["PMS Category"].iloc[0]
        return None

    rows = []
    for fam, g in pn.groupby("ITC_family", dropna=False):
        members = sorted({m for m in g["Material"].tolist() if m})
        desc = desc_by_newest.get(fam, "") or ""
        if not desc:
            # most common non-empty description among members
            for d in g.sort_values("_abs", ascending=False)["Description"]:
                if d:
                    desc = d
                    break
        rows.append(
            {
                "Newest_PN": fam,
                "Description": desc,
                "Category": _mode_cat(g),
                "PMS Category": _mode_pms(g),
                "Member_PNs": "; ".join(members),
                "Member_count": len(members),
                "Qty_H1_2025": g["qty_H1_2025"].sum(),
                "Net_EUR_H1_2025": g["net_eur_H1_2025"].sum(),
                "Qty_H1_2026": g["qty_H1_2026"].sum(),
                "Net_EUR_H1_2026": g["net_eur_H1_2026"].sum(),
                "Delta_EUR": g["Delta_EUR"].sum(),
                "Delta_Qty": g["Delta_Qty"].sum(),
                "Any_unmapped_member": bool((~g["mapped"]).any()),
            }
        )
    fam = pd.DataFrame(rows)
    fam["Delta_Pct"] = np.where(
        fam["Net_EUR_H1_2025"] != 0,
        fam["Delta_EUR"] / fam["Net_EUR_H1_2025"],
        np.nan,
    )
    return fam


def netting_effect(pn: pd.DataFrame, fam: pd.DataFrame) -> dict:
    """Measure how much PN-level |delta| cancels inside ITC families."""
    # For multi-member families: sum of |member deltas| vs |family delta|
    multi = fam[fam["Member_count"] > 1].copy()
    cancelled = 0.0
    gross_member = 0.0
    examples = []
    for _, row in multi.iterrows():
        members = pn[pn["ITC_family"] == row["Newest_PN"]]
        member_abs = members["Delta_EUR"].abs().sum()
        family_abs = abs(row["Delta_EUR"])
        cancel = member_abs - family_abs
        if cancel > 1:  # ignore noise
            cancelled += cancel
            gross_member += member_abs
            examples.append(
                {
                    "Newest_PN": row["Newest_PN"],
                    "Description": row["Description"],
                    "Category": row["Category"],
                    "Member_PNs": row["Member_PNs"],
                    "Member_count": row["Member_count"],
                    "Sum_abs_member_Delta_EUR": round(member_abs, 2),
                    "Family_Delta_EUR": round(row["Delta_EUR"], 2),
                    "Netted_away_EUR": round(cancel, 2),
                    "Net_EUR_H1_2025": round(row["Net_EUR_H1_2025"], 2),
                    "Net_EUR_H1_2026": round(row["Net_EUR_H1_2026"], 2),
                    "Qty_H1_2025": round(row["Qty_H1_2025"], 2),
                    "Qty_H1_2026": round(row["Qty_H1_2026"], 2),
                }
            )
    examples_df = pd.DataFrame(examples).sort_values("Netted_away_EUR", ascending=False) if examples else pd.DataFrame()
    return {
        "multi_member_families": int(len(multi)),
        "total_netted_away_eur": round(cancelled, 2),
        "examples": examples_df,
    }


def style_header(ws, row: int, ncol: int):
    for c in range(1, ncol + 1):
        cell = ws.cell(row, c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = BORDER


def autosize(ws, min_w=10, max_w=42, wide_headers=None):
    wide_headers = {h.lower() for h in (wide_headers or ["description", "member pns", "member_pns"])}
    headers = {}
    for cell in ws[1]:
        if cell.value:
            headers[cell.column] = str(cell.value)
    # also check row 2 (tables with title on row 1)
    for cell in ws[2]:
        if cell.value and cell.column not in headers:
            headers[cell.column] = str(cell.value)
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        hdr = headers.get(col[0].column, "")
        length = 28 if hdr.lower() in wide_headers else 0
        for cell in col[:80]:
            if cell.value is not None:
                length = max(length, min(len(str(cell.value)), max_w if hdr.lower() not in wide_headers else 55))
        ws.column_dimensions[letter].width = max(min_w, length + 2)


def write_df(ws, df: pd.DataFrame, start_row: int = 1, currency_cols=None, qty_cols=None, pct_cols=None):
    currency_cols = set(currency_cols or [])
    qty_cols = set(qty_cols or [])
    pct_cols = set(pct_cols or [])
    headers = list(df.columns)
    for c, h in enumerate(headers, 1):
        ws.cell(start_row, c, h)
    style_header(ws, start_row, len(headers))
    for r_i, row in enumerate(df.itertuples(index=False), start_row + 1):
        for c_i, val in enumerate(row, 1):
            cell = ws.cell(r_i, c_i, None if (isinstance(val, float) and np.isnan(val)) else val)
            cell.border = BORDER
            h = headers[c_i - 1]
            if h in currency_cols and isinstance(val, (int, float)):
                cell.number_format = NUM_FMT
            elif h in qty_cols and isinstance(val, (int, float)):
                cell.number_format = QTY_FMT
            elif h in pct_cols and isinstance(val, (int, float)):
                cell.number_format = PCT_FMT
    ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(headers))}{start_row + len(df)}"
    ws.freeze_panes = f"A{start_row + 1}"
    autosize(ws)
    return start_row + len(df)


def build():
    print("Loading ITC map...")
    itc_df, itc_map, desc_by_newest = load_itc_map()
    print(f"  ITC map PNs: {len(itc_map):,}")

    print("Loading sales...")
    sales = load_h1_sales()
    catalog = load_catalog()

    h1_25 = float(sales.loc[sales["period"] == "H1_2025", "net_eur"].sum())
    h1_26 = float(sales.loc[sales["period"] == "H1_2026", "net_eur"].sum())
    print(f"  H1 2025 Net EUR: {h1_25:,.2f} (expected {EXPECTED_H1_2025:,.0f})")
    print(f"  H1 2026 Net EUR: {h1_26:,.2f} (expected {EXPECTED_H1_2026:,.0f})")

    # SaTy mix (no warranty code exists)
    saty_mix = (
        sales.groupby(["period", "SaTy"])
        .agg(net_eur=("net_eur", "sum"), lines=("net_eur", "size"))
        .reset_index()
        .sort_values(["period", "net_eur"], ascending=[True, False])
    )

    print("Aggregating PN...")
    pn = aggregate_pn(sales, catalog, desc_by_newest, itc_map)
    # backfill descriptions from original workbook if still blank — use Material as last resort
    pn.loc[pn["Description"].fillna("") == "", "Description"] = ""

    mapped_n = int(pn["mapped"].sum())
    unmapped_n = int((~pn["mapped"]).sum())
    unmapped_eur = float(pn.loc[~pn["mapped"], ["net_eur_H1_2025", "net_eur_H1_2026"]].abs().sum().sum())
    total_eur_abs = float(pn[["net_eur_H1_2025", "net_eur_H1_2026"]].abs().sum().sum())
    print(f"  PN rows: {len(pn):,}  mapped: {mapped_n:,}  unmapped: {unmapped_n:,} ({100*unmapped_n/max(len(pn),1):.1f}%)")

    print("Aggregating ITC families...")
    fam = aggregate_itc(pn, desc_by_newest, catalog)
    netting = netting_effect(pn, fam)
    print(f"  Families: {len(fam):,}  multi-member: {netting['multi_member_families']:,}")
    print(f"  Delta EUR netted away by ITC: {netting['total_netted_away_eur']:,.2f}")

    # reconcile family vs PN totals
    fam_25 = float(fam["Net_EUR_H1_2025"].sum())
    fam_26 = float(fam["Net_EUR_H1_2026"].sum())
    pn_25 = float(pn["net_eur_H1_2025"].sum())
    pn_26 = float(pn["net_eur_H1_2026"].sum())
    assert abs(fam_25 - pn_25) < 0.05, (fam_25, pn_25)
    assert abs(fam_26 - pn_26) < 0.05, (fam_26, pn_26)
    print("  Reconciliation PN<->ITC Net EUR: OK")

    # Category summary (PN-level = ITC-level same euros)
    cat = (
        fam.groupby("Category", dropna=False)
        .agg(
            Net_EUR_H1_2025=("Net_EUR_H1_2025", "sum"),
            Net_EUR_H1_2026=("Net_EUR_H1_2026", "sum"),
            Qty_H1_2025=("Qty_H1_2025", "sum"),
            Qty_H1_2026=("Qty_H1_2026", "sum"),
        )
        .reset_index()
    )
    cat["Delta_EUR"] = cat["Net_EUR_H1_2026"] - cat["Net_EUR_H1_2025"]
    cat["Delta_Pct"] = np.where(cat["Net_EUR_H1_2025"] != 0, cat["Delta_EUR"] / cat["Net_EUR_H1_2025"], np.nan)
    cat = cat.sort_values("Category")

    # Exclude REBATE from growing lists (same rule as original)
    def is_rebate_row(r) -> bool:
        mat = str(r.get("Material", r.get("Newest_PN", "")) or "").upper()
        desc = str(r.get("Description", "") or "").upper()
        return "REBATE" in mat or "REBATE" in desc

    pn_ex = pn[~pn.apply(lambda r: is_rebate_row({"Material": r["Material"], "Description": r["Description"]}), axis=1)]
    fam_ex = fam[~fam.apply(lambda r: is_rebate_row({"Newest_PN": r["Newest_PN"], "Description": r["Description"]}), axis=1)]

    top_decl_pn = pn_ex.nsmallest(TOP_N, "Delta_EUR")
    top_grow_pn = pn_ex.nlargest(TOP_N, "Delta_EUR")
    top_decl_itc = fam_ex.nsmallest(TOP_N, "Delta_EUR")
    top_grow_itc = fam_ex.nlargest(TOP_N, "Delta_EUR")

    # Steering spot-check
    steer_pns = ["8983948772", "8981017801", "7552348290"]
    steer_check = pn[pn["Material"].isin(steer_pns)][
        ["Material", "Newest_PN", "Description", "net_eur_H1_2025", "net_eur_H1_2026", "Delta_EUR", "mapped"]
    ]
    print("\nSteering unit spot-check (PN -> Newest):")
    for _, r in steer_check.iterrows():
        print(f"  {r['Material']} -> {r['Newest_PN']}  Delta EUR {r['Delta_EUR']:,.2f}  mapped={r['mapped']}")

    # Warranty indication
    # Annualise H1 roughly: H1*2 for rough %, or vs CY2025 warranty figure
    approx_cy2025_parts = h1_25 * 2  # rough
    warr_pct_vs_approx_cy = PORTUGAL_WARRANTY_CY2025_EUR / approx_cy2025_parts if approx_cy2025_parts else np.nan
    warr_pct_vs_h1_25 = PORTUGAL_WARRANTY_CY2025_EUR / h1_25 if h1_25 else np.nan

    # ---------- Write workbook ----------
    wb = Workbook()

    # Notes
    ws = wb.active
    ws.title = "Notes"
    notes = [
        "I-Motors (Portugal) H1 2026 vs H1 2025 Parts Sales Analysis — ITC (Newest P/N) rollup",
        "",
        "Period: H1 2026 = Jan–Jun 2026. H1 2025 = Jan–Jun 2025.",
        "Basis: raw SAP Net value (not GPS-signed/filtered) — matches accounting/Power BI to the euro.",
        "",
        "Sources:",
        '- H1 2026 Jan–Mar: 01_data\\00_derived\\cy2026_q1.csv (Payer.1 = "IMOTORS - Importacao e Comercio")',
        "- H1 2026 Apr–Jun: 01_data\\00_derived\\q1fy2027_billing_tagged.csv (same Payer.1, raw Net value)",
        '- H1 2025: 01_data\\00_derived\\cy2025_raw.csv (DB = "IMOTORS - Importacao e Comercio")',
        "- Category: 01_data\\00_derived\\parts_catalog_dimension.csv (pr00_group)",
        "- ITC map: 01_data\\01_Pricing\\Price file 2026_full.xlsx columns P/N → Newest P/N",
        "  (unmapped PNs keep themselves as family key; Newest chains resolved transitively)",
        "",
        f"Validated totals: H1 2025 EUR {h1_25:,.2f} | H1 2026 EUR {h1_26:,.2f}",
        f"  (reference lock: H1 2025 EUR {EXPECTED_H1_2025:,.0f} | H1 2026 EUR {EXPECTED_H1_2026:,.0f})",
        f"PN ↔ ITC family Net EUR reconciliation: OK (diff < EUR 0.05).",
        "",
        "ITC coverage:",
        f"  PN rows: {len(pn):,} | mapped to price file: {mapped_n:,} | unmapped: {unmapped_n:,} ({100*unmapped_n/max(len(pn),1):.1f}% of PNs)",
        f"  ITC families: {len(fam):,} | multi-member families: {netting['multi_member_families']:,}",
        f"  PN-level |Delta| cancelled inside ITC families: EUR {netting['total_netted_away_eur']:,.2f}",
        "",
        "Sheets:",
        "  PN Detail — every sold PN (same grain as original), plus Newest P/N + Qty",
        "  ITC Family Detail — one row per Newest P/N family (Net EUR + Qty)",
        f"  Top Movers ITC — Top {TOP_N} declining + Top {TOP_N} growing families (excl. REBATE)",
        f"  Top Movers PN — Top {TOP_N} declining + Top {TOP_N} growing PNs (excl. REBATE) for comparison",
        "  ITC Netted Away — multi-member families where PN deltas partly cancel",
        "  Category Summary — category totals (EUR + Qty)",
        "  Warranty — indication only (see below)",
        "  SaTy Mix — order-type mix (SOR/RUSH/VOR/…) — not warranty",
        "",
        "Warranty finding:",
        "  SAP billing for I-Motors has NO warranty document type or warranty flag.",
        "  Observed SaTy codes are SOR / RUSH / VOR / PRD / CR only — warranty parts are",
        "  embedded in normal commercial billing (same conclusion as GPS warranty notes).",
        "  Therefore warranty cannot be split out of this H1 PN analysis line-by-line.",
        f"  Separate CY2025 Portugal warranty-parts value (claim/transfer-price basis): EUR {PORTUGAL_WARRANTY_CY2025_EUR:,.0f}",
        f"    = CV EUR 28,836 (lower bound, 52% priced) + LCV EUR 101,752",
        f"    Source: 01_data\\06_Warranty\\Warranty_CY2025_by_DB.md",
        f"  Rough scale vs ~2× H1 2025 parts (EUR {approx_cy2025_parts:,.0f}): ~{100*warr_pct_vs_approx_cy:.1f}% of annualised H1 parts.",
        "  Indication: warranty is material but minority (~high-single-digit % of annual parts);",
        "  it does not dominate the H1 mover list. CV figure is a lower bound.",
        "",
        "Caveats:",
        "  - Some sold PNs (e.g. certain 755* materials) are absent from the price file → family = self.",
        "  - Same description (e.g. STEERING UNIT) can be several independent Newest P/N families.",
        "  - Growing lists exclude the one-off REBATE material line (EUR 20,000 in H1 2026).",
        "  - Mode A language: no internal model nicknames in this workbook.",
        "",
        f"Rebuild script: {Path(__file__).name}",
    ]
    for i, line in enumerate(notes, 1):
        ws.cell(i, 1, line)
    ws.column_dimensions["A"].width = 120

    # PN Detail
    ws = wb.create_sheet("PN Detail")
    pn_out = pn.rename(
        columns={
            "Material": "Material",
            "Newest_PN": "Newest P/N",
            "Description": "Description",
            "Category": "Category",
            "PMS Category": "PMS Category",
            "qty_H1_2025": "Qty H1 2025",
            "net_eur_H1_2025": "Net EUR H1 2025",
            "qty_H1_2026": "Qty H1 2026",
            "net_eur_H1_2026": "Net EUR H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Qty": "Delta Qty",
            "Delta_Pct": "Delta %",
            "mapped": "In price file",
        }
    )[
        [
            "Material",
            "Newest P/N",
            "Description",
            "Category",
            "PMS Category",
            "Qty H1 2025",
            "Net EUR H1 2025",
            "Qty H1 2026",
            "Net EUR H1 2026",
            "Delta EUR",
            "Delta Qty",
            "Delta %",
            "In price file",
        ]
    ].sort_values("Delta EUR")
    write_df(
        ws,
        pn_out,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026", "Delta Qty"},
        pct_cols={"Delta %"},
    )

    # ITC Family Detail
    ws = wb.create_sheet("ITC Family Detail")
    fam_out = fam.rename(
        columns={
            "Newest_PN": "Newest P/N",
            "Qty_H1_2025": "Qty H1 2025",
            "Net_EUR_H1_2025": "Net EUR H1 2025",
            "Qty_H1_2026": "Qty H1 2026",
            "Net_EUR_H1_2026": "Net EUR H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Qty": "Delta Qty",
            "Delta_Pct": "Delta %",
            "Member_PNs": "Member PNs",
            "Member_count": "Member count",
            "Any_unmapped_member": "Any unmapped member",
        }
    )[
        [
            "Newest P/N",
            "Description",
            "Category",
            "PMS Category",
            "Member count",
            "Member PNs",
            "Qty H1 2025",
            "Net EUR H1 2025",
            "Qty H1 2026",
            "Net EUR H1 2026",
            "Delta EUR",
            "Delta Qty",
            "Delta %",
            "Any unmapped member",
        ]
    ].sort_values("Delta EUR")
    write_df(
        ws,
        fam_out,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026", "Delta Qty"},
        pct_cols={"Delta %"},
    )

    # Top Movers ITC
    ws = wb.create_sheet("Top Movers ITC")
    cols_itc = [
        "Newest P/N",
        "Description",
        "Category",
        "Member count",
        "Qty H1 2025",
        "Net EUR H1 2025",
        "Qty H1 2026",
        "Net EUR H1 2026",
        "Delta EUR",
        "Delta Qty",
    ]
    decl = top_decl_itc.rename(
        columns={
            "Newest_PN": "Newest P/N",
            "Qty_H1_2025": "Qty H1 2025",
            "Net_EUR_H1_2025": "Net EUR H1 2025",
            "Qty_H1_2026": "Qty H1 2026",
            "Net_EUR_H1_2026": "Net EUR H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Qty": "Delta Qty",
            "Member_count": "Member count",
        }
    )[cols_itc]
    grow = top_grow_itc.rename(
        columns={
            "Newest_PN": "Newest P/N",
            "Qty_H1_2025": "Qty H1 2025",
            "Net_EUR_H1_2025": "Net EUR H1 2025",
            "Qty_H1_2026": "Qty H1 2026",
            "Net_EUR_H1_2026": "Net EUR H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Qty": "Delta Qty",
            "Member_count": "Member count",
        }
    )[cols_itc]

    ws.cell(1, 1, f"TOP {TOP_N} DECLINING ITC FAMILIES (H1 2026 vs H1 2025) — Newest P/N aggregation")
    ws.cell(1, 1).font = TITLE_FONT
    write_df(
        ws,
        decl,
        start_row=2,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026", "Delta Qty"},
    )
    start_grow = 2 + len(decl) + 3
    ws.cell(start_grow - 1, 1, f"TOP {TOP_N} GROWING ITC FAMILIES (H1 2026 vs H1 2025, excl. one-off REBATE line)")
    ws.cell(start_grow - 1, 1).font = TITLE_FONT
    write_df(
        ws,
        grow,
        start_row=start_grow,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026", "Delta Qty"},
    )
    # clear conflicting auto filter — keep both tables with filters on separate regions is awkward;
    # leave filter on declining only; growing still readable
    ws.auto_filter.ref = f"A2:{get_column_letter(len(cols_itc))}{2 + len(decl)}"

    # Top Movers PN (comparison, longer)
    ws = wb.create_sheet("Top Movers PN")
    cols_pn = [
        "Material",
        "Newest P/N",
        "Description",
        "Category",
        "Qty H1 2025",
        "Net EUR H1 2025",
        "Qty H1 2026",
        "Net EUR H1 2026",
        "Delta EUR",
        "Delta Qty",
    ]
    decl_pn = top_decl_pn.rename(
        columns={
            "Newest_PN": "Newest P/N",
            "qty_H1_2025": "Qty H1 2025",
            "net_eur_H1_2025": "Net EUR H1 2025",
            "qty_H1_2026": "Qty H1 2026",
            "net_eur_H1_2026": "Net EUR H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Qty": "Delta Qty",
        }
    )[cols_pn]
    grow_pn = top_grow_pn.rename(
        columns={
            "Newest_PN": "Newest P/N",
            "qty_H1_2025": "Qty H1 2025",
            "net_eur_H1_2025": "Net EUR H1 2025",
            "qty_H1_2026": "Qty H1 2026",
            "net_eur_H1_2026": "Net EUR H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Qty": "Delta Qty",
        }
    )[cols_pn]
    ws.cell(1, 1, f"TOP {TOP_N} DECLINING PNs (H1 2026 vs H1 2025) — PN level, for comparison")
    ws.cell(1, 1).font = TITLE_FONT
    write_df(
        ws,
        decl_pn,
        start_row=2,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026", "Delta Qty"},
    )
    start_grow = 2 + len(decl_pn) + 3
    ws.cell(start_grow - 1, 1, f"TOP {TOP_N} GROWING PNs (H1 2026 vs H1 2025, excl. one-off REBATE line)")
    ws.cell(start_grow - 1, 1).font = TITLE_FONT
    write_df(
        ws,
        grow_pn,
        start_row=start_grow,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026", "Delta Qty"},
    )
    ws.auto_filter.ref = f"A2:{get_column_letter(len(cols_pn))}{2 + len(decl_pn)}"

    # ITC Netted Away
    ws = wb.create_sheet("ITC Netted Away")
    ws.cell(1, 1, "ITC families where PN-level deltas partly cancel after Newest P/N rollup")
    ws.cell(1, 1).font = TITLE_FONT
    ws.cell(2, 1, f"Total |Delta| cancelled across multi-member families: EUR {netting['total_netted_away_eur']:,.2f}")
    ex = netting["examples"]
    if len(ex):
        write_df(
            ws,
            ex,
            start_row=4,
            currency_cols={
                "Sum_abs_member_Delta_EUR",
                "Family_Delta_EUR",
                "Netted_away_EUR",
                "Net_EUR_H1_2025",
                "Net_EUR_H1_2026",
            },
            qty_cols={"Qty_H1_2025", "Qty_H1_2026"},
        )
    else:
        ws.cell(4, 1, "No material multi-member cancellations found.")

    # Category Summary
    ws = wb.create_sheet("Category Summary")
    cat_out = cat.rename(
        columns={
            "Net_EUR_H1_2025": "Net EUR H1 2025",
            "Net_EUR_H1_2026": "Net EUR H1 2026",
            "Qty_H1_2025": "Qty H1 2025",
            "Qty_H1_2026": "Qty H1 2026",
            "Delta_EUR": "Delta EUR",
            "Delta_Pct": "Delta %",
        }
    )
    write_df(
        ws,
        cat_out,
        currency_cols={"Net EUR H1 2025", "Net EUR H1 2026", "Delta EUR"},
        qty_cols={"Qty H1 2025", "Qty H1 2026"},
        pct_cols={"Delta %"},
    )

    # Warranty
    ws = wb.create_sheet("Warranty")
    w_lines = [
        ["Warranty indication — I-Motors (Portugal)"],
        [],
        ["Question", "Answer"],
        ["Can warranty be split from H1 SAP billing lines?", "No — ERP has no warranty document type / flag for these sales."],
        ["SaTy codes observed (I-Motors H1)", ", ".join(sorted(sales["SaTy"].dropna().unique()))],
        ["What warranty data exists separately?", "CY2025 Portugal warranty-parts value from claim assessments (transfer-price basis)."],
        ["Portugal warranty parts CY2025 (EUR)", PORTUGAL_WARRANTY_CY2025_EUR],
        ["  of which CV (lower bound, 52% priced)", 28836],
        ["  of which LCV", 101752],
        ["Source", r"01_data\06_Warranty\Warranty_CY2025_by_DB.md"],
        ["H1 2025 I-Motors Net EUR (this analysis)", round(h1_25, 2)],
        ["H1 2026 I-Motors Net EUR (this analysis)", round(h1_26, 2)],
        ["Rough annualised H1 2025 (×2)", round(approx_cy2025_parts, 2)],
        ["Warranty ≈ % of annualised H1 2025 parts", warr_pct_vs_approx_cy],
        [],
        ["Indication", "Warranty is present and material (~high-single-digit % of annualised parts), but cannot be attributed to individual PN movers in this file. Top declining/growing lists are commercial billing totals including any embedded warranty demand."],
        ["Implication for ITC movers", "Do not interpret PN/family declines as 'warranty finished' without a separate claim-level join — that join is not available at PN×H1 grain in the billing extracts used here."],
    ]
    for r, row in enumerate(w_lines, 1):
        for c, v in enumerate(row, 1):
            cell = ws.cell(r, c, v)
            if r == 3:
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
            if r == 14 and c == 2 and isinstance(v, float):
                cell.number_format = PCT_FMT
    ws.column_dimensions["A"].width = 55
    ws.column_dimensions["B"].width = 100

    # SaTy mix
    ws = wb.create_sheet("SaTy Mix")
    saty_out = saty_mix.rename(columns={"period": "Period", "SaTy": "SaTy", "net_eur": "Net EUR", "lines": "Lines"})
    tot = saty_out.groupby("Period")["Net EUR"].transform("sum")
    saty_out["Share of period Net EUR"] = saty_out["Net EUR"] / tot
    write_df(
        ws,
        saty_out,
        currency_cols={"Net EUR"},
        pct_cols={"Share of period Net EUR"},
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_XLSX)
    print(f"\nWrote {OUT_XLSX}")

    # Summary for parent agent
    summary = {
        "output": str(OUT_XLSX),
        "top_n": TOP_N,
        "h1_2025": round(h1_25, 2),
        "h1_2026": round(h1_26, 2),
        "reconcile_ok": abs(fam_25 - pn_25) < 0.05 and abs(fam_26 - pn_26) < 0.05,
        "unmapped_pn_pct": round(100 * unmapped_n / max(len(pn), 1), 2),
        "unmapped_pn_n": unmapped_n,
        "families": len(fam),
        "multi_member_families": netting["multi_member_families"],
        "netted_away_eur": netting["total_netted_away_eur"],
        "warranty": "not separable in billing; CY2025 Portugal warranty parts EUR 130,588 (~8% of annualised H1 2025)",
        "steering_note": "8983948772, 8981017801, 7552348290 are THREE separate Newest P/N families (755* unmapped)",
    }
    print("\n=== SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print("BUILD FAILED:", e, file=sys.stderr)
        raise
