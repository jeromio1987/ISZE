#!/usr/bin/env python3
"""
Export the tender / R&M opportunity pipeline to Excel and PDF.

Reads Data/derived/tender_pipeline.csv (built by build_tender_pipeline.py)
and writes:
  - PRISM_Tender_Pipeline.xlsx  (action queue + full pipeline + summary)
  - PRISM_Tender_Pipeline.pdf   (decision funnel + by-country + by-owner)

Qualified-pipeline view: counts and scores only. Value is present on just
12/520 rows and deadlines on 55/520, so NO euro pipeline is charted.

Output dir: Data/exports/
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, EXPORTS_DIR  # noqa: E402

SRC = DERIVED_DIR / "tender_pipeline.csv"
EXPORT_DIR = EXPORTS_DIR

DECISION_ORDER = ["Attack", "Selective", "Watch", "Ignore"]
DECISION_COLORS = {"Attack": "#E2231A", "Selective": "#E87722",
                   "Watch": "#1B3A6B", "Ignore": "#94A3B8"}

QUEUE_COLS = ["title", "country", "owner_suggested", "opportunity_score",
              "decision", "deadline_date", "url"]
SCORE_COLS = ["fit_score", "win_score", "econ_score", "opportunity_score"]


def _load() -> pd.DataFrame:
    d = pd.read_csv(SRC)
    if d["actionable"].dtype != bool:
        d["actionable"] = d["actionable"].astype(str).str.lower().isin(["true", "1"])
    return d


def write_excel(df: pd.DataFrame, path: Path) -> None:
    queue = (
        df[df["decision"].isin(["Attack", "Selective"])]
        .sort_values("opportunity_score", ascending=False)[QUEUE_COLS]
    )
    summary = (
        df.groupby("decision")
        .agg(opportunities=("opportunity_id", "count"),
             avg_score=("opportunity_score", "mean"),
             parts_signal=("parts_signal", "sum"),
             rm_contract=("rm_contract", "sum"))
        .reindex(DECISION_ORDER).reset_index()
    )
    with pd.ExcelWriter(path, engine="xlsxwriter") as xw:
        queue.to_excel(xw, sheet_name="Action queue", index=False)
        df.to_excel(xw, sheet_name="Full pipeline", index=False)
        summary.to_excel(xw, sheet_name="Summary", index=False)
        wb = xw.book
        num_fmt = wb.add_format({"num_format": "#,##0.0"})
        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1B3A6B", "font_color": "white"})
        link_fmt = wb.add_format({"font_color": "#1B3A6B", "underline": 1})
        widths = {"title": 52, "buyer": 40, "cpv_desc": 40, "url": 50,
                  "owner_suggested": 22, "country": 14, "deadline_date": 14}
        for sheet, frame in (("Action queue", queue), ("Full pipeline", df),
                             ("Summary", summary)):
            ws = xw.sheets[sheet]
            for ci, col in enumerate(frame.columns):
                ws.write(0, ci, col, hdr_fmt)
                if col in SCORE_COLS or col == "avg_score":
                    ws.set_column(ci, ci, 14, num_fmt)
                else:
                    ws.set_column(ci, ci, widths.get(col, 16))
                if col == "url":
                    for ri, val in enumerate(frame[col], start=1):
                        if isinstance(val, str) and val.startswith("http"):
                            ws.write_url(ri, ci, val, link_fmt, "Open notice")
            ws.freeze_panes(1, 0)


def write_pdf(df: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    funnel = (df["decision"].value_counts().reindex(DECISION_ORDER).fillna(0))
    act = df[df["actionable"]]
    by_country = act["country"].value_counts().head(12).sort_values()
    by_owner = act["owner_suggested"].value_counts().sort_values()

    with PdfPages(path) as pdf:
        # Page 1 — decision funnel
        fig, ax = plt.subplots(figsize=(11, 7))
        ax.bar(funnel.index, funnel.values,
               color=[DECISION_COLORS[d] for d in funnel.index])
        for i, v in enumerate(funnel.values):
            ax.text(i, v + 3, f"{int(v)}", ha="center", fontweight="bold")
        ax.set_ylabel("Opportunities")
        ax.set_title("PRISM — Tender pipeline by decision (520 scored notices)",
                     fontweight="bold")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # Page 2 — actionable by country
        fig, ax = plt.subplots(figsize=(11, 7))
        ax.barh(by_country.index, by_country.values, color="#1B3A6B")
        for i, v in enumerate(by_country.values):
            ax.text(v + 0.3, i, f"{int(v)}", va="center")
        ax.set_xlabel("Actionable opportunities (Attack / Selective / Watch)")
        ax.set_title("PRISM — Actionable tenders by country", fontweight="bold")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # Page 3 — actionable by suggested owner
        fig, ax = plt.subplots(figsize=(11, 7))
        ax.barh(by_owner.index, by_owner.values, color="#E87722")
        for i, v in enumerate(by_owner.values):
            ax.text(v + 0.3, i, f"{int(v)}", va="center")
        ax.set_xlabel("Actionable opportunities")
        ax.set_title("PRISM — Actionable tenders by suggested owner", fontweight="bold")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    df = _load()
    xlsx = EXPORT_DIR / "PRISM_Tender_Pipeline.xlsx"
    pdf = EXPORT_DIR / "PRISM_Tender_Pipeline.pdf"
    write_excel(df, xlsx)
    write_pdf(df, pdf)
    print(f"ok: {xlsx}")
    print(f"ok: {pdf}")


if __name__ == "__main__":
    main()
