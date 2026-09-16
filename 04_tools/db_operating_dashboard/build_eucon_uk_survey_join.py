#!/usr/bin/env python
"""Join 2023 UK IAM Price Survey workshop/list GBP onto all 18 DB CY2025 books.

This is NOT the PartsPool March 2026 Autodoc DE/NO extract
(eucon_price_gap.csv — leave that file alone).

Writes:
  01_data/00_derived/eucon_uk_survey_2023_price_gap.csv
  01_data/00_derived/eucon_uk_survey_2023_price_gap.meta.json
  01_data/00_derived/eucon_price_gap.meta.json   (label only; does not touch the 44-PN CSV)

Pricing point: UK IAM workshop purchase GBP (median across brands), else list.
FX: GBP_EUR=1.17 (sources.yaml 2026-05-01) — labeled, not the empty Eucon EXCHG cell.
Sign: delta_pct = (IAM_eur - ISZE_net) / ISZE_net. POSITIVE = ISZE cheaper.
Also stores proj_retail_eur = ISZE_net × 1.785.

Never reads competitiveness_autodoc_risk.csv. Never opens raw sales XLSX.
Never puts OEM GBP list into the competitor column.
Never blends UMI 1797 with UTI 1799.

    python build_eucon_uk_survey_join.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import openpyxl
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_iam_street_joins import (
    CHANNEL_COMBINED,
    CY,
    DERIVED,
    GBP_EUR,
    ISZE,
    NETWORK_SOLD_TO,
    load_cy2025_books,
    load_ie40_pr00,
    norm_pn,
    pick_isze_price,
    score_brands,
    load_brand_lookup,
)

RAW = os.path.join(ISZE, "01_data", "01_Pricing", "_raw")
IAM_XLSX = os.path.join(RAW, "Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx")
OUT_CSV = os.path.join(DERIVED, "eucon_uk_survey_2023_price_gap.csv")
OUT_META = os.path.join(DERIVED, "eucon_uk_survey_2023_price_gap.meta.json")
POOL_META = os.path.join(DERIVED, "eucon_price_gap.meta.json")


def to_float(x):
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)) and not (isinstance(x, float) and pd.isna(x)):
        return float(x)
    try:
        return float(str(x).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None


def load_iam_priced() -> pd.DataFrame:
    """One row per Isuzu PN with a 2023 UK IAM workshop (preferred) or list price."""
    wb = openpyxl.load_workbook(IAM_XLSX, read_only=True, data_only=True)
    rows = []
    for sheet in ("LCV", "HCV"):
        for r in wb[sheet].iter_rows(min_row=2, values_only=True):
            pn = norm_pn(r[1])
            if not pn or pn.lower() in {"pleas", "please"}:
                continue
            brand = str(r[4] or "").strip()
            if brand.lower() in {"none", "nan"}:
                brand = ""
            comp_pn = norm_pn(r[5]) if r[5] else ""
            lst = to_float(r[6])
            ws = to_float(r[7])
            if lst is None and ws is None:
                continue
            rows.append({
                "pn": pn,
                "desc": str(r[2] or ""),
                "brand": brand,
                "comp_pn": comp_pn,
                "list_gbp": lst,
                "workshop_gbp": ws,
                "sheet": sheet,
            })
    wb.close()
    if not rows:
        return pd.DataFrame()

    by_pn = defaultdict(list)
    for rec in rows:
        by_pn[rec["pn"]].append(rec)

    out = []
    for pn, grp in by_pn.items():
        ws_vals = [g["workshop_gbp"] for g in grp if g["workshop_gbp"] is not None]
        list_vals = [g["list_gbp"] for g in grp if g["list_gbp"] is not None]
        brands = sorted({g["brand"] for g in grp if g["brand"]})
        desc = next((g["desc"] for g in grp if g["desc"]), "")
        if ws_vals:
            gbp = float(pd.Series(ws_vals).median())
            kind = "workshop"
            gbp_min = min(ws_vals)
        elif list_vals:
            gbp = float(pd.Series(list_vals).median())
            kind = "list"
            gbp_min = min(list_vals)
        else:
            continue
        out.append({
            "pn": pn,
            "description": desc,
            "brands_found": ", ".join(brands),
            "competitor_count": len(grp),
            "iam_point_kind": kind,
            "workshop_gbp_median": float(pd.Series(ws_vals).median()) if ws_vals else None,
            "list_gbp_median": float(pd.Series(list_vals).median()) if list_vals else None,
            "competitor_gbp": gbp,
            "competitor_gbp_min": gbp_min,
            "competitor_avg_eur": round(gbp * GBP_EUR, 2),
            "competitor_min_eur": round(gbp_min * GBP_EUR, 2),
        })
    return pd.DataFrame(out)


def main():
    os.makedirs(DERIVED, exist_ok=True)
    lookup = load_brand_lookup()
    books = load_cy2025_books()
    ie40 = load_ie40_pr00()
    iam = load_iam_priced()
    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows = []
    stats = {}
    for db, book in books.items():
        book_tot = float(book["rev_eur"].sum()) if len(book) else 0.0
        merged = book.merge(iam, on="pn", how="inner")
        n = 0
        matched_rev = 0.0
        for _, rw in merged.iterrows():
            price, src = pick_isze_price(rw.pn, rw.get("realized_unit_eur"), ie40, None)
            if price is None or price <= 0:
                continue
            cavg = float(rw.competitor_avg_eur)
            cmin = float(rw.competitor_min_eur)
            delta = (cavg - price) / price
            proj = round(price * CHANNEL_COMBINED, 2)
            delta_vs_proj = (cavg - proj) / proj if proj else None
            brands, tier, ceiling = score_brands(rw.get("brands_found") or "", lookup)
            desc = rw.get("description_x") or rw.get("description") or rw.get("description_y") or ""
            rows.append({
                "db": db,
                "pn": rw.pn,
                "description": desc,
                "isze_price_eur": round(price, 2),
                "isze_price_source": src,
                "proj_retail_eur": proj,
                "competitor_avg_eur": cavg,
                "competitor_min_eur": cmin,
                "delta_pct": round(delta, 6),
                "delta_vs_proj_retail_pct": round(delta_vs_proj, 6) if delta_vs_proj is not None else None,
                "isze_exposed": bool(delta < 0),
                "brands_found": brands,
                "brand_tier": tier,
                "brand_ceiling_pct": ceiling,
                "competitor_count": int(rw.competitor_count),
                "iam_point_kind": rw.iam_point_kind,
                "workshop_gbp_median": rw.workshop_gbp_median,
                "list_gbp_median": rw.list_gbp_median,
                "fx_gbp_eur": GBP_EUR,
                "vintage": "UK_IAM_PriceSurvey_2023",
                "probe": "eucon_uk_2023",
                "probe_label": "Eucon UK IAM workshop 2023 — outdated",
                "fx_note": (
                    "GBP_EUR=1.17 from autodoc_scraper/_HANDOFF_BUNDLE/sources.yaml "
                    "as_of 2026-05-01. 2023 UK IAM workshop (median) else list. "
                    "NOT Autodoc DE/NO. NOT PR00×1.785 projected retail."
                ),
                "db_revenue_cy_eur": round(float(rw.rev_eur), 2) if pd.notna(rw.rev_eur) else None,
            })
            n += 1
            matched_rev += float(rw.rev_eur) if pd.notna(rw.rev_eur) else 0.0
        stats[db] = {
            "matches": n,
            "book_pns": int(book["pn"].nunique()) if len(book) else 0,
            "book_eur": round(book_tot, 2),
            "matched_eur": round(matched_rev, 2),
            "coverage_pct": round(100.0 * matched_rev / book_tot, 2) if book_tot else None,
        }

    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["db", "isze_exposed", "delta_pct"], ascending=[True, False, True])
    df.to_csv(OUT_CSV, index=False)

    meta = {
        "built_at_utc": built,
        "source_xlsx": IAM_XLSX,
        "pricing_point": "UK IAM workshop purchase GBP 2023 (median across brands); list if no workshop",
        "fx_gbp_eur": GBP_EUR,
        "fx_source": "sources.yaml as_of 2026-05-01",
        "not": [
            "Not 2026 projected retail.",
            "Not PartsPool Autodoc DE/NO (that is eucon_price_gap.csv).",
            "Not OEM GBP list from the 2023 OEM survey sheets.",
        ],
        "sign": "delta_pct=(IAM_eur - ISZE_net)/ISZE_net ; positive = ISZE cheaper",
        "proj_retail": f"proj_retail_eur = ISZE_net × {CHANNEL_COMBINED}",
        "iam_priced_unique_pns": int(iam["pn"].nunique()) if len(iam) else 0,
        "join_rows": int(len(df)),
        "unique_pns_joined": int(df["pn"].nunique()) if len(df) else 0,
        "by_db": stats,
        "grain": "db × PN · CY2025 billed book ∩ 2023 UK IAM priced PNs",
        "israel": "UMI sold-to 1797 ≠ UTI sold-to 1799",
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    pool_meta = {
        "file": os.path.join(DERIVED, "eucon_price_gap.csv"),
        "what": "PartsPool Autodoc DE/NO online IAM, 44 PNs",
        "as_of": "2026-03-29",
        "source_xlsx": os.path.join(RAW, "eucon_pricing_partspool_20260329.xlsx"),
        "not": "Not the 2023 UK/ITUK Price Survey. Do not label this file Eucon 2023.",
        "countries": ["DE", "NO"],
        "n_pns": 44,
        "relabelled_at_utc": built,
        "csv_untouched": True,
    }
    with open(POOL_META, "w", encoding="utf-8") as fh:
        json.dump(pool_meta, fh, indent=2)

    print("build_eucon_uk_survey_join")
    print(f"  built_at_utc {built}")
    print(f"  IAM priced unique PNs (workshop or list): {len(iam)}")
    print(f"  wrote {OUT_CSV}  rows={len(df)}  unique_pn={df['pn'].nunique() if len(df) else 0}")
    for db, st in stats.items():
        print(f"    {db}: matches={st['matches']}  "
              f"coverage={st['coverage_pct']}% of CY{CY} €{st['book_eur']:,.0f} "
              f"(matched €{st['matched_eur']:,.0f})")
    print(f"  labelled PartsPool 44 as Autodoc DE/NO 2026-03-29 -> {POOL_META}")
    print("  did NOT overwrite eucon_price_gap.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
