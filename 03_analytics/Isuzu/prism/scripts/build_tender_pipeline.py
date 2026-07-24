#!/usr/bin/env python3
"""
Tender pipeline — flatten tender_data.json into a chartable derived table.

Source: Data/dashboards/tender_data.json (520 scored public-tender opportunities,
each with country, decision, fit/win/econ scores, owner, deadline, parts/R&M flags).

This is a QUALIFIED-PIPELINE view: counts and scores are real for every row, but
value_amount is present on only ~12 of 520 and deadline on ~55 — so we do NOT chart
€ pipeline or award prices. tenders_output.xlsx (awarded line items) is still empty;
when it lands, the price/win-loss view can be added on top of this.

Output: Data/derived/tender_pipeline.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DASHBOARDS_JSON_DIR, DERIVED_DIR  # noqa: E402

SRC = DASHBOARDS_JSON_DIR / "tender_data.json"
OUT = DERIVED_DIR / "tender_pipeline.csv"

KEEP = [
    "opportunity_id", "title", "buyer", "country", "country_code",
    "deadline_date", "days_to_deadline", "urgency", "value_amount", "currency",
    "lifecycle", "fit_score", "win_score", "econ_score", "opportunity_score",
    "decision", "evidence_label", "parts_signal", "rm_contract",
    "owner_suggested", "status_suggested", "cpv_desc", "url",
]


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    opps = data.get("opportunities", [])
    if not opps:
        raise SystemExit("no opportunities in tender_data.json")

    df = pd.DataFrame([{k: o.get(k) for k in KEEP} for o in opps])

    # tidy types
    for c in ["fit_score", "win_score", "econ_score", "opportunity_score",
              "days_to_deadline", "value_amount"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["parts_signal", "rm_contract"]:
        df[c] = df[c].fillna(False).astype(bool)
    df["country"] = df["country"].fillna("Unknown").replace("", "Unknown")
    df["decision"] = df["decision"].fillna("Ignore").replace("", "Ignore")
    df["owner_suggested"] = df["owner_suggested"].fillna("Unassigned").replace("", "Unassigned")
    # actionable = anything we'd actually pursue or keep an eye on
    df["actionable"] = df["decision"].isin(["Attack", "Selective", "Watch"])

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"ok: {len(df)} rows -> {OUT}")
    print("  decisions:", df["decision"].value_counts().to_dict())
    print("  actionable:", int(df["actionable"].sum()),
          "| parts_signal:", int(df["parts_signal"].sum()),
          "| rm_contract:", int(df["rm_contract"].sum()))


if __name__ == "__main__":
    main()
