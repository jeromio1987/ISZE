#!/usr/bin/env python
"""Rebuild PN-level IAM street joins for all 18 GPS DBs (CY2025 books).

Does NOT invent Auto 365 PN matches — that catalog has no OEM key
(see 04_tools/autodoc_scraper/AUTO365_PN_JOIN.md). Family-level Israel
street stays in iam_israel_street.csv (written by enrich_street.py).

Writes:
  01_data/00_derived/iam_ks_price_gap.csv          (db × PN; all 18 books)
  01_data/00_derived/iam_mekonomen_price_gap.csv   (PN-bearing source only)

Sign: delta_pct = (competitor_avg - ISZE_net) / ISZE_net
  POSITIVE = ISZE cheaper = good. NEGATIVE = ISZE above market = exposed.
Also stores proj_retail_eur = ISZE_net × 1.785 and delta_vs_proj_retail_pct.

Never attributes network gp_at_risk. Never reads competitiveness_autodoc_risk.csv.
Never blends UMI 1797 with UTI 1799.

    python build_iam_street_joins.py
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone

import pandas as pd

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
SCRAPER = os.path.join(ISZE, "04_tools", "autodoc_scraper")

# sources.yaml as_of 2026-05-01
GBP_EUR = 1.17
SEK_EUR = 0.089
KS_PLACEHOLDER_GBP = 2.00  # skip AM prices at or below the £2 no-results placeholder
CY = 2025

# ---------------------------------------------------------------------------
# RETIRED — Mekonomen, 2026-09-24 (Jerome's go, card 0.4/C3).
#
# Mekonomen's part-number search does not search by part number. It echoes the
# query and serves one unrelated in-stock item, and the scraper records the first
# price on the page against our part. Verified against the scraper's own dump,
# `autodoc_scraper/_diag/MEK_8975056801.txt`: asking for 8975056801
# "PAD KIT; CALIPER,DISC BRK,FRT" returns "Spiralfjaeder Lesjoefors" (a coil
# spring) at 957 SEK. All seven "ok" rows are this shape, and every number returns
# exactly ONE hit, on every snapshot from 2026-07-09 to 2026-09-22.
#
# These are false positives, not misses, so no row from this source is written.
# The seven PNs below carried EUR 582,085 of UMI CY2025 billed revenue between
# them (largest: the brake pad kit, EUR 308,819) — pricing a brake pad against a
# coil spring made our position read as undercut by far more than it is.
#
# The scraper is also retired from the weekly run, see
# `autodoc_scraper/refresh_and_check_drift.py` JOBS.
#
# To re-enable: set MEKONOMEN_RETIRED = False AND delete the PN from the false set
# only with a real product page in hand showing that part number and a price on
# the same page. `mekonomen_results.csv` stays on disk for the audit trail.
# ---------------------------------------------------------------------------
MEKONOMEN_RETIRED = True
MEKONOMEN_FALSE_PNS = frozenset({
    "8975056801",  # PAD KIT; CALIPER,DISC BRK,FRT -> returned a Kilen coil spring, 957 SEK
    "8983373180",  # SENSOR ASM; DEF TANK
    "8982932120",  # DRIVE ASM; FINAL,RR
    "8982924321",  # SENSOR; SPD,FRT WHEEL
    "8983937793",  # SUPPORT; RR BUMPER
    "8983288004",  # LAMP ASM; RR COMB
    "8982606011",  # DOOR ASM; FRT,WO/TRIM
})
CHANNEL_COMBINED = 1.785  # PR00 × 1.40 × 1.275 projected retail
# 18 GPS DBs. Israel split at sold_to — never blend 1797/1799, never "Israel".
NETWORK_SOLD_TO = {
    "ITUK": [2575],
    "IUK": [2574],
    "UTI": [1799],
    "UMI": [1797],
    "BELGIUM": [90],
    "GERMANY": [2516, 601],
    "NORWAY": [86],
    "SWEDEN": [2181],
    "IRELAND": [76],
    "PORTUGAL": [519, 92],
    "GREECE": [66],
    "CYPRUS": [393],
    "HUNGARY": [537],
    "FINLAND": [2679],
    "MALTA": [1759],
    "ROMANIA": [396],
    "DENMARK": [2027, 2751],
    "ICELAND": [1576],
}
SOLD_TO = NETWORK_SOLD_TO  # back-compat alias

# T4=+30% … T1=+250% — same ladder as enrich_street / pricing engine
CEILING_BY_TIER = {4: 30, 3: 60, 2: 150, 1: 250}


def r2(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return round(float(x), 6)


def norm_pn(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    return digits.zfill(10)[-10:]


def _norm_brand(s: str) -> str:
    s = str(s or "").upper()
    s = s.replace("&", " ").replace("+", " ").replace("AMP", " ")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_brand_lookup() -> dict:
    path = os.path.join(SCRAPER, "iam_brand_tiers.csv")
    if not os.path.exists(path):
        return {}
    t = pd.read_csv(path)
    lookup = {}
    for _, rw in t.iterrows():
        key = _norm_brand(rw.brand)
        if key:
            lookup[key] = int(rw.tier) if pd.notna(rw.tier) else 1
    return lookup


def score_brands(brands_found: str, lookup: dict) -> tuple[str, int, int]:
    """Return (brands_found, best_tier, ceiling_pct). Unmapped -> T1 / +250%."""
    raw = str(brands_found or "").strip()
    if not raw or raw in {"|", "-", "nan", "None"}:
        return "", 1, CEILING_BY_TIER[1]
    parts = [p.strip() for p in re.split(r"[|,;/]+", raw) if p.strip()]
    if not parts:
        return "", 1, CEILING_BY_TIER[1]
    tiers = []
    for p in parts:
        tiers.append(lookup.get(_norm_brand(p), 1))
    best = max(tiers)
    return ", ".join(parts), best, CEILING_BY_TIER.get(best, 250)


def load_cy2025_books() -> dict[str, pd.DataFrame]:
    """Per-DB CY2025 PN book from sales_fact. Credits (SaTy CR) excluded, never subtracted."""
    path = os.path.join(DERIVED, "sales_fact.parquet")
    if not os.path.exists(path):
        path = os.path.join(DERIVED, "sales_fact.csv")
    if path.endswith(".parquet"):
        sf = pd.read_parquet(
            path,
            columns=[
                "sold_to_sap", "part_number", "description",
                "billed_qty", "net_sales_value", "saty", "year",
            ],
        )
    else:
        sf = pd.read_csv(
            path,
            usecols=[
                "sold_to_sap", "part_number", "description",
                "billed_qty", "net_sales_value", "saty", "year",
            ],
        )
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf["year"] = pd.to_numeric(sf["year"], errors="coerce")
    sf["saty"] = sf["saty"].astype(str).str.upper().str.strip()
    sf = sf[(sf["year"] == CY) & (sf["saty"] != "CR")].copy()
    sf["pn"] = sf["part_number"].map(norm_pn)
    sf = sf[sf["pn"] != ""]
    sap = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    books = {}
    for db, codes in NETWORK_SOLD_TO.items():
        g = sf[sap.isin(codes)]
        if g.empty:
            books[db] = pd.DataFrame(
                columns=["pn", "description", "qty", "rev_eur", "realized_unit_eur"]
            )
            continue
        agg = g.groupby("pn", as_index=False).agg(
            description=("description", "first"),
            qty=("billed_qty", "sum"),
            rev_eur=("net_sales_value", "sum"),
        )
        agg["realized_unit_eur"] = agg.apply(
            lambda r: (r.rev_eur / r.qty) if r.qty and r.qty != 0 else None, axis=1
        )
        books[db] = agg
    return books


def load_ie40_pr00() -> pd.Series:
    """Current IE40 PR00 list (sp_eur). Zero prices treated as missing."""
    path = os.path.join(DERIVED, "pricing_pr00_ie40.parquet")
    pr = pd.read_parquet(path, columns=["part_number", "sp_eur", "price_condition"])
    pr = pr[pr["price_condition"].astype(str).str.upper() == "PR00"]
    pr["pn"] = pr["part_number"].map(norm_pn)
    pr["sp_eur"] = pd.to_numeric(pr["sp_eur"], errors="coerce")
    pr = pr[(pr["pn"] != "") & (pr["sp_eur"] > 0)]
    # unique PNs in this extract
    return pr.drop_duplicates("pn").set_index("pn")["sp_eur"]


def pick_isze_price(pn: str, realized, ie40: pd.Series, scrape_pr00) -> tuple[float | None, str]:
    if pn in ie40.index:
        return float(ie40.loc[pn]), "IE40_PR00"
    if realized is not None and not (isinstance(realized, float) and pd.isna(realized)) and realized > 0:
        return float(realized), "sales_fact_realized_cy2025"
    if scrape_pr00 is not None and not (isinstance(scrape_pr00, float) and pd.isna(scrape_pr00)) and float(scrape_pr00) > 0:
        return float(scrape_pr00), "scraper_seed_PR00"
    return None, "missing"


def load_ks_am() -> pd.DataFrame:
    ks = pd.read_csv(os.path.join(SCRAPER, "ks_results.csv"))
    ks["pn"] = ks["PN"].map(norm_pn)
    ks["status"] = ks["Status"].astype(str).str.strip().str.lower()
    ks["am_min_gbp"] = pd.to_numeric(ks["KS_AM_MinPrice_GBP"], errors="coerce")
    ks["am_avg_gbp"] = pd.to_numeric(ks["KS_AM_AvgPrice_GBP"], errors="coerce")
    ks["am_count"] = pd.to_numeric(ks["KS_AM_Count"], errors="coerce").fillna(0).astype(int)
    # Skip no_results, genuine-only (no AM price), and £2 placeholder
    keep = (
        (ks["status"] == "ok")
        & ks["am_min_gbp"].notna()
        & (ks["am_min_gbp"] > KS_PLACEHOLDER_GBP)
        & (ks["am_count"] > 0)
    )
    out = ks.loc[keep].copy()
    out["ks_am_min_eur"] = out["am_min_gbp"] * GBP_EUR
    out["ks_am_avg_eur"] = out["am_avg_gbp"].fillna(out["am_min_gbp"]) * GBP_EUR
    return out


def load_mekonomen_am() -> pd.DataFrame:
    """RETIRED 2026-09-24 — returns an empty frame unless someone deliberately
    re-enables the source. Mekonomen's PN search returns unrelated items (a Kilen
    coil spring for a brake pad kit); all seven of its rows were false, so none is
    usable. See the MEKONOMEN_RETIRED block at the top of this file."""
    if MEKONOMEN_RETIRED:
        print("  Mekonomen: RETIRED — source not read (all 7 historical rows were "
              "false positives; see load_mekonomen_am docstring)")
        return pd.DataFrame(
            columns=["pn", "status", "am_min_sek", "am_avg_sek", "am_count",
                     "mek_am_min_eur", "mek_am_avg_eur"]
        )
    path = os.path.join(SCRAPER, "mekonomen_results.csv")
    mek = pd.read_csv(path)
    mek["pn"] = mek["PN"].map(norm_pn)
    mek["status"] = mek["Status"].astype(str).str.strip().str.lower()
    mek["am_min_sek"] = pd.to_numeric(mek["MEK_AM_MinPrice_SEK"], errors="coerce")
    mek["am_avg_sek"] = pd.to_numeric(mek["MEK_AM_AvgPrice_SEK"], errors="coerce")
    mek["am_count"] = pd.to_numeric(mek["MEK_AM_Count"], errors="coerce").fillna(0).astype(int)
    # even if re-enabled wholesale, the proven-false PNs never come back
    mek = mek[~mek["pn"].isin(MEKONOMEN_FALSE_PNS)]
    keep = (
        (mek["status"] == "ok")
        & mek["am_min_sek"].notna()
        & (mek["am_min_sek"] > 0)
        & (mek["am_count"] > 0)
    )
    out = mek.loc[keep].copy()
    out["mek_am_min_eur"] = out["am_min_sek"] * SEK_EUR
    out["mek_am_avg_eur"] = out["am_avg_sek"].fillna(out["am_min_sek"]) * SEK_EUR
    return out


def join_source(books, ie40, scrape: pd.DataFrame, lookup: dict, kind: str) -> tuple[pd.DataFrame, dict]:
    rows = []
    stats = {}
    for db, book in books.items():
        book_tot = float(book["rev_eur"].sum()) if len(book) else 0.0
        merged = book.merge(scrape, on="pn", how="inner")
        matched_rev = 0.0
        n = 0
        for _, rw in merged.iterrows():
            scrape_pr00 = pd.to_numeric(rw.get("PR00_EUR"), errors="coerce")
            price, src = pick_isze_price(rw.pn, rw.get("realized_unit_eur"), ie40, scrape_pr00)
            if price is None or price <= 0:
                continue
            if kind == "ks":
                cmin = float(rw.ks_am_min_eur)
                cavg = float(rw.ks_am_avg_eur)
                url = rw.get("KS_URL") or ""
                brands_raw = rw.get("KS_AM_SKUs") or ""
                titles = str(rw.get("KS_AllProducts") or "")
                count = int(rw.am_count)
                scraped_at = rw.get("Scraped_At") or ""
            else:
                cmin = float(rw.mek_am_min_eur)
                cavg = float(rw.mek_am_avg_eur)
                url = rw.get("MEK_URL") or ""
                brands_raw = rw.get("MEK_AM_Brands") or ""
                titles = str(rw.get("MEK_AllProducts") or "")
                count = int(rw.am_count)
                scraped_at = rw.get("Scraped_At") or ""
            delta = (cavg - price) / price
            proj = round(price * CHANNEL_COMBINED, 2)
            delta_vs_proj = (cavg - proj) / proj if proj else None
            brands, tier, ceiling = score_brands(brands_raw, lookup)
            desc = rw.get("description") or rw.get("Description") or rw.get("description_x") or ""
            rec = {
                "db": db,
                "pn": rw.pn,
                "description": desc,
                "isze_price_eur": round(price, 2),
                "isze_price_source": src,
                "proj_retail_eur": proj,
                "delta_pct": round(delta, 6),
                "delta_vs_proj_retail_pct": round(delta_vs_proj, 6) if delta_vs_proj is not None else None,
                "isze_exposed": bool(delta < 0),
                "brands_found": brands,
                "brand_tier": tier,
                "brand_ceiling_pct": ceiling,
                "competitor_count": count,
                "status": rw.get("status") or "ok",
                "scraped_at": scraped_at,
                "scrape_titles": titles[:400],
            }
            if kind == "ks":
                rec.update({
                    "ks_am_min_eur": round(cmin, 2),
                    "ks_am_avg_eur": round(cavg, 2),
                    "ks_url": url,
                    "fx_gbp_eur": GBP_EUR,
                    "fx_note": "GBP_EUR=1.17 from autodoc_scraper/_HANDOFF_BUNDLE/sources.yaml as_of 2026-05-01. KS prices are ex-VAT.",
                })
            else:
                rec.update({
                    "mek_am_min_eur": round(cmin, 2),
                    "mek_am_avg_eur": round(cavg, 2),
                    "mek_url": url,
                    "fx_sek_eur": SEK_EUR,
                    "fx_note": "SEK_EUR=0.089 from autodoc_scraper/_HANDOFF_BUNDLE/sources.yaml as_of 2026-05-01.",
                })
            rows.append(rec)
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
    return df, stats


def category_only_note() -> str:
    return (
        "TMC (tmc_results.csv) and Tranzparts (tranzparts_results.csv) are category "
        "crawls — no Isuzu OEM PN column. Left category-only; not joined."
    )


def main():
    os.makedirs(DERIVED, exist_ok=True)
    lookup = load_brand_lookup()
    books = load_cy2025_books()
    ie40 = load_ie40_pr00()
    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ks = load_ks_am()
    ks_df, ks_stats = join_source(books, ie40, ks, lookup, "ks")
    ks_path = os.path.join(DERIVED, "iam_ks_price_gap.csv")
    ks_df.to_csv(ks_path, index=False)

    mek = load_mekonomen_am()
    mek_df, mek_stats = join_source(books, ie40, mek, lookup, "mek")
    mek_path = os.path.join(DERIVED, "iam_mekonomen_price_gap.csv")
    mek_df.to_csv(mek_path, index=False)

    print("build_iam_street_joins")
    print(f"  built_at_utc {built}")
    print(f"  KS AM joinable rows (ok, AM>GBP {KS_PLACEHOLDER_GBP:.0f}): {len(ks)}")
    print(f"  wrote {ks_path}  n={len(ks_df)}")
    for db, st in ks_stats.items():
        print(f"    {db}: matches={st['matches']}  "
              f"coverage={st['coverage_pct']}% of CY{CY} €{st['book_eur']:,.0f} "
              f"(matched €{st['matched_eur']:,.0f} / {st['book_pns']} book PNs)")
    print(f"  Mekonomen AM joinable rows: {len(mek)}")
    print(f"  wrote {mek_path}  n={len(mek_df)}")
    for db, st in mek_stats.items():
        print(f"    {db}: matches={st['matches']}  "
              f"coverage={st['coverage_pct']}% of CY{CY} €{st['book_eur']:,.0f} "
              f"(matched €{st['matched_eur']:,.0f})")
    print(f"  Auto365 PN join: NO — see {os.path.join(SCRAPER, 'AUTO365_PN_JOIN.md')}")
    print(f"  {category_only_note()}")
    print("  FX: GBP_EUR=1.17  SEK_EUR=0.089  (sources.yaml 2026-05-01)")
    print("  Sign: delta_pct=(competitor_avg-ISZE_net)/ISZE_net  positive=ISZE cheaper")
    print(f"  Also stored: proj_retail_eur=ISZE_net×{CHANNEL_COMBINED}  delta_vs_proj_retail_pct")
    print("  DBs: all 18 GPS books · UMI 1797 != UTI 1799")
    return 0


if __name__ == "__main__":
    sys.exit(main())
