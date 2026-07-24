#!/usr/bin/env python3
"""
Export the DB parts classification to Excel and PDF.

Reads Data/derived/db_parts_mix_classification.csv (built by
build_db_parts_classification.py) and writes, for the latest year:
  - PRISM_DB_Parts_Mix_<year>.xlsx  (formatted, all years + latest summary)
  - PRISM_DB_Parts_Mix_<year>.pdf   (table + BVP/contested bar chart)

Output dir: Data/exports/
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, EXPORTS_DIR  # noqa: E402

SRC = DERIVED_DIR / "db_parts_mix_classification.csv"
EXPORT_DIR = EXPORTS_DIR

PCT_COLS = ["bvp_pct", "genuine_contested_pct", "genuine_only_pct", "contested_bvp_capture"]
EUR_COLS = ["total_eur", "bvp_eur", "genuine_contested_eur", "genuine_only_eur", "contested_eur"]


def _load() -> tuple[pd.DataFrame, int]:
    df = pd.read_csv(SRC)
    return df, int(df["year"].max())


def write_excel(df: pd.DataFrame, latest: int, path: Path) -> None:
    latest_df = df[df["year"] == latest].copy()
    with pd.ExcelWriter(path, engine="xlsxwriter") as xw:
        latest_df.to_excel(xw, sheet_name=f"CY{latest}", index=False)
        df.to_excel(xw, sheet_name="All years", index=False)
        wb = xw.book
        eur_fmt = wb.add_format({"num_format": "#,##0"})
        pct_fmt = wb.add_format({"num_format": "0.0%"})
        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1F2A44", "font_color": "white"})
        for sheet, frame in ((f"CY{latest}", latest_df), ("All years", df)):
            ws = xw.sheets[sheet]
            for ci, col in enumerate(frame.columns):
                ws.write(0, ci, col, hdr_fmt)
                if col in EUR_COLS:
                    ws.set_column(ci, ci, 16, eur_fmt)
                elif col in PCT_COLS:
                    ws.set_column(ci, ci, 14, pct_fmt)
                else:
                    ws.set_column(ci, ci, 18)
            ws.freeze_panes(1, 1)


def write_pdf(df: pd.DataFrame, latest: int, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    d = df[df["year"] == latest].sort_values("total_eur", ascending=True)
    labels = d["distributor_code"]

    with PdfPages(path) as pdf:
        # Page 1 — stacked mix bar
        fig, ax = plt.subplots(figsize=(11, 8))
        ax.barh(labels, d["bvp_pct"], color="#E2231A", label="BVP")
        ax.barh(labels, d["genuine_contested_pct"], left=d["bvp_pct"],
                color="#F5A623", label="Genuine (contested)")
        ax.barh(labels, d["genuine_only_pct"],
                left=d["bvp_pct"] + d["genuine_contested_pct"],
                color="#1F2A44", label="Genuine only")
        ax.set_xlim(0, 1)
        ax.set_xlabel("Share of total parts revenue")
        ax.set_title(f"PRISM — Parts mix per distributor (CY{latest})", fontweight="bold")
        ax.legend(loc="lower right")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # Page 2 — contested-basket BVP capture
        d2 = df[df["year"] == latest].sort_values("contested_bvp_capture", ascending=True)
        fig, ax = plt.subplots(figsize=(11, 8))
        ax.barh(d2["distributor_code"], d2["contested_bvp_capture"].fillna(0), color="#E2231A")
        ax.set_xlabel("BVP share of the conquerable (contested) basket")
        ax.set_title(f"PRISM — Where the value line is winning (CY{latest})", fontweight="bold")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    df, latest = _load()
    xlsx = EXPORT_DIR / f"PRISM_DB_Parts_Mix_{latest}.xlsx"
    pdf = EXPORT_DIR / f"PRISM_DB_Parts_Mix_{latest}.pdf"
    write_excel(df, latest, xlsx)
    write_pdf(df, latest, pdf)
    print(f"ok: {xlsx}")
    print(f"ok: {pdf}")


if __name__ == "__main__":
    main()
