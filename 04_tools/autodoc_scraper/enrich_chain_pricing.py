"""
ISZE — Autodoc Results → Chain Pricing Enrichment
===================================================
Reads autodoc_results.csv and produces autodoc_chain_pricing.xlsx with:
  - Raw Autodoc data
  - Chain pricing calculation (DB × DLR margins applied to PR00)
  - Competitive gap analysis at DB and DLR level
  - Risk classification

Run AFTER autodoc_scraper.py has produced results.

Usage:
    python enrich_chain_pricing.py [--db-gm 0.40] [--dlr-gm 0.275] [--fx 1.18]
"""

import argparse
import sys
from pathlib import Path
import pandas as pd


def _safe_print(msg: str) -> None:
    """Avoid UnicodeEncodeError on Windows cp1252 consoles."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))

SCRIPT_DIR  = Path(__file__).parent
INPUT_CSV   = SCRIPT_DIR / "autodoc_results.csv"
OUTPUT_XLSX = SCRIPT_DIR / "autodoc_chain_pricing.xlsx"

# ─── Chain pricing logic ───────────────────────────────────────────────────────
# PR00 (ISZE to DB) → DB_Price (DB to DLR) → DLR_Price (DLR to end customer)
#
# Gross Margin convention:  GM% = (SP - Cost) / SP
#   DB buys at PR00, sells at PR00 / (1 - DB_GM)
#   DLR buys at DB_Price, sells at DB_Price / (1 - DLR_GM)
#
# Autodoc price = retail aftermarket price (what DLR can buy online)
# Trade discount = retail × (1 - TRADE_DISC) = what workshop/DLR actually pays

TRADE_DISC_DEFAULT = 0.35   # 35% off Autodoc retail = trade/workshop price


def calc_chain(df: pd.DataFrame, db_gm: float, dlr_gm: float,
               fx_gbp_eur: float, trade_disc: float) -> pd.DataFrame:
    """Add chain pricing columns to enriched df."""
    pr = df["PR00_EUR"]

    # Genuine chain prices (EUR)
    df["DB_Price_EUR"]  = pr / (1 - db_gm)        # what DLR pays for genuine
    df["DLR_Price_EUR"] = df["DB_Price_EUR"] / (1 - dlr_gm)  # genuine retail to end customer

    # Autodoc prices converted EUR
    df["Autodoc_MinPrice_EUR"] = df["Autodoc_MinPrice_GBP"] * fx_gbp_eur
    df["Autodoc_AvgPrice_EUR"] = df["Autodoc_AvgPrice_GBP"] * fx_gbp_eur

    # Trade price = what DLR/workshop actually pays for aftermarket (after trade discount)
    df["Trade_Min_EUR"] = df["Autodoc_MinPrice_EUR"] * (1 - trade_disc)
    df["Trade_Avg_EUR"] = df["Autodoc_AvgPrice_EUR"] * (1 - trade_disc)

    # ── Key competitive metrics ──────────────────────────────────────────────────
    # Delta at DB level: how much cheaper is aftermarket trade vs genuine DB price
    # Negative = aftermarket cheaper (bad for ISZE)
    df["Delta_DB_pct"] = (df["DB_Price_EUR"] - df["Trade_Min_EUR"]) / df["Trade_Min_EUR"] * 100
    # Positive = genuine DB_Price more expensive than trade min

    # Delta at DLR level: genuine retail vs aftermarket trade
    df["Delta_DLR_pct"] = (df["DLR_Price_EUR"] - df["Trade_Min_EUR"]) / df["Trade_Min_EUR"] * 100

    # Required PR00 cut for genuine to match aftermarket trade at DB level
    # DB_Price = PR00 / (1-db_gm) = Trade_Min → PR00_needed = Trade_Min × (1-db_gm)
    df["PR00_to_match_trade_EUR"] = df["Trade_Min_EUR"] * (1 - db_gm)
    df["PR00_cut_needed_pct"] = (df["PR00_EUR"] - df["PR00_to_match_trade_EUR"]) / df["PR00_EUR"] * 100
    # Positive = PR00 needs to fall by X% to compete

    # Risk classification
    def classify(row):
        if pd.isna(row["Autodoc_MinPrice_GBP"]) or row["Autodoc_ResultCount"] == 0:
            return "No data"
        cut = row["PR00_cut_needed_pct"]
        rev = row["Rev_CY2025_EUR"] if pd.notna(row["Rev_CY2025_EUR"]) else 0
        if cut > 30 and rev > 50_000:
            return "🔴 High Risk"
        elif cut > 15 and rev > 20_000:
            return "🟠 Medium Risk"
        elif cut > 0:
            return "🟡 Low Risk"
        elif cut <= 0:
            return "🟢 Competitive"
        return "⚪ Uncategorised"

    df["Risk_Band"] = df.apply(classify, axis=1)

    return df


def run(db_gm: float, dlr_gm: float, fx_gbp_eur: float, trade_disc: float):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if not INPUT_CSV.exists():
        _safe_print(f"ERROR: {INPUT_CSV} not found. Run autodoc_scraper.py first.")
        return

    df = pd.read_csv(INPUT_CSV, dtype={"PN": str})
    df["PN"] = df["PN"].astype(str).str.zfill(10)

    # Coerce numeric
    for col in ["PR00_EUR", "Rev_CY2025_EUR", "Qty_CY2025",
                "Autodoc_ResultCount", "Autodoc_MinPrice_GBP",
                "Autodoc_AvgPrice_GBP", "Autodoc_MaxPrice_GBP"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    ok = df[df["Status"] == "ok"].copy()
    _safe_print(
        f"{len(df)} total PNs scraped | {len(ok)} with results | "
        f"{len(df[df['Status']=='no_results'])} no results | "
        f"{len(df[df['Status'].isin(['error','timeout'])])} errors"
    )

    ok = calc_chain(ok, db_gm, dlr_gm, fx_gbp_eur, trade_disc)

    _safe_print("\nChain pricing parameters:")
    _safe_print(f"     DB gross margin:   {db_gm*100:.0f}%")
    _safe_print(f"     DLR gross margin:  {dlr_gm*100:.1f}%")
    _safe_print(f"     GBP/EUR FX:        {fx_gbp_eur}")
    _safe_print(f"     Trade discount:    {trade_disc*100:.0f}% off Autodoc retail")
    _safe_print(f"     Combined multiplier PR00->DLR retail: x{1/((1-db_gm)*(1-dlr_gm)):.2f}")

    # ── Summary stats ──────────────────────────────────────────────────────────
    if not ok.empty:
        exposed = ok[ok["PR00_cut_needed_pct"] > 0]
        competitive = ok[ok["PR00_cut_needed_pct"] <= 0]
        _safe_print("\nCompetitive position (vs aftermarket trade, min price):")
        _safe_print(
            f"     Exposed (genuine DB price > trade min):  {len(exposed):>4} PNs  "
            f"(EUR {exposed['Rev_CY2025_EUR'].sum():,.0f} revenue)"
        )
        _safe_print(
            f"     Competitive (genuine cheaper):           {len(competitive):>4} PNs  "
            f"(EUR {competitive['Rev_CY2025_EUR'].sum():,.0f} revenue)"
        )
        if not exposed.empty:
            _safe_print(f"     Avg PR00 cut needed (exposed):          {exposed['PR00_cut_needed_pct'].mean():.0f}%")
            _safe_print(f"     Max PR00 cut needed:                    {exposed['PR00_cut_needed_pct'].max():.0f}%")

    # ── Build Excel ────────────────────────────────────────────────────────────
    _safe_print(f"\nWriting {OUTPUT_XLSX} ...")

    # Sheet 1: Executive summary by risk band
    summary = (ok.groupby("Risk_Band")
               .agg(
                   PNs=("PN", "count"),
                   Revenue_EUR=("Rev_CY2025_EUR", "sum"),
                   Avg_PR00_EUR=("PR00_EUR", "mean"),
                   Avg_PR00_cut_pct=("PR00_cut_needed_pct", "mean"),
                   Avg_ResultCount=("Autodoc_ResultCount", "mean"),
               ).reset_index()
               .sort_values("Revenue_EUR", ascending=False))

    # Sheet 2: Full detail sorted by revenue × exposure
    detail_cols = [
        "PN", "Description", "AIM_Category", "Source", "Class",
        "Rev_CY2025_EUR", "Qty_CY2025",
        "PR00_EUR", "DB_Price_EUR", "DLR_Price_EUR",
        "Autodoc_ResultCount", "Autodoc_MinPrice_GBP", "Autodoc_AvgPrice_GBP",
        "Autodoc_MinPrice_EUR", "Autodoc_AvgPrice_EUR",
        "Trade_Min_EUR", "Trade_Avg_EUR",
        "Delta_DB_pct", "Delta_DLR_pct",
        "PR00_to_match_trade_EUR", "PR00_cut_needed_pct",
        "Autodoc_CheapestBrand", "Autodoc_AllBrands",
        "Risk_Band", "Autodoc_URL", "Scraped_At",
    ]
    avail = [c for c in detail_cols if c in ok.columns]
    detail = ok[avail].sort_values(["PR00_cut_needed_pct", "Rev_CY2025_EUR"],
                                    ascending=[False, False])

    # Sheet 3: No-data PNs (no results or errors)
    no_data = df[df["Status"] != "ok"][[
        "PN", "Description", "Rev_CY2025_EUR", "PR00_EUR",
        "Autodoc_ResultCount", "Status", "Notes", "Autodoc_URL"
    ]]

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Risk Summary", index=False)
        detail.to_excel(writer, sheet_name="Chain Pricing Detail", index=False)
        no_data.to_excel(writer, sheet_name="No Data PNs", index=False)

        # ── Format ────────────────────────────────────────────────────────────
        from openpyxl.styles import PatternFill, Font, Alignment, numbers
        from openpyxl.utils import get_column_letter

        wb = writer.book
        blue_fill = PatternFill("solid", fgColor="1E3A5F")
        gold_fill = PatternFill("solid", fgColor="C9993A")
        white_font = Font(color="FFFFFF", bold=True)

        for ws in wb.worksheets:
            # Header row
            for cell in ws[1]:
                cell.fill = blue_fill
                cell.font = white_font
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            ws.row_dimensions[1].height = 30

            # Auto width (cap at 45)
            for col_cells in ws.columns:
                max_len = max(
                    len(str(cell.value or "")) for cell in col_cells
                )
                col_letter = get_column_letter(col_cells[0].column)
                ws.column_dimensions[col_letter].width = min(max(max_len + 2, 10), 45)

            ws.freeze_panes = "A2"

    _safe_print(f"Done. Open: {OUTPUT_XLSX}")
    _safe_print("\nTip: The 'Chain Pricing Detail' sheet has all competitive metrics.")
    _safe_print("     Sort by PR00_cut_needed_pct (desc) to find most exposed PNs.")
    _safe_print("     Filter Risk_Band = High Risk for priority action.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enrich Autodoc results with chain pricing analysis"
    )
    parser.add_argument("--db-gm",   type=float, default=0.40,
                        help="DB gross margin 0-1 (default 0.40 = 40%%)")
    parser.add_argument("--dlr-gm",  type=float, default=0.275,
                        help="DLR gross margin 0-1 (default 0.275 = 27.5%%)")
    parser.add_argument("--fx",      type=float, default=1.18,
                        help="GBP/EUR exchange rate (default 1.18)")
    parser.add_argument("--trade-disc", type=float, default=0.35,
                        help="Trade discount off Autodoc retail (default 0.35 = 35%%)")
    args = parser.parse_args()

    run(
        db_gm=args.db_gm,
        dlr_gm=args.dlr_gm,
        fx_gbp_eur=args.fx,
        trade_disc=args.trade_disc,
    )
