# -*- coding: utf-8 -*-
"""
Price-observation ledger — task cards 0.1 + 0.2 of
00_docs/agent/SCRAPER_REDO_DELEGATION.md

One row = one competitor price seen at one source on one date.
Every row MUST carry price_type and vintage; the loader refuses rows without them,
so retail, trade, grey genuine, survey and online-median prices can never be blended.

Loads what is already on disk (no scraping, no web):
  - KS International         04_tools/autodoc_scraper/ks_results.csv
  - Eucon PartsPool crossref 02_dashboards/Data/01_Pricing/_raw/eucon_crossref_iam_20260329.csv
  - Eucon UK survey 2023     01_data/00_derived/eucon_uk_survey_2023_price_gap.csv
  - TMC, Tranzparts          04_tools/autodoc_scraper/{tmc,tranzparts}_results.csv  (category only, no Isuzu no.)
Not loaded on purpose:
  - Mekonomen  — RETIRED 2026-09-24: its part-number search returns an unrelated item
                 (a Kilen coil spring for brake pad kit 8975056801); all 7 rows were false
  - Auto365    — retired 2026-09-24: no OEM part number anywhere, so it cannot be joined
  - Tranzparts — retired 2026-09-24: carries no Isuzu (every handle is Volvo/Iveco/DAF)
  - Autodoc    — retired; £2 / 2.34 EUR placeholder values

Output:
  01_data/00_derived/price_observations.parquet
  01_data/00_derived/price_observations.meta.json

Run from anywhere:  python 04_tools/price_ledger/build_price_ledger.py
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # ISZE root
OUT = ROOT / "01_data" / "00_derived" / "price_observations.parquet"
META = OUT.with_suffix(".meta.json")

# FX — single source on disk: autodoc_scraper sources.yaml, as_of 2026-05-01. Not an official rate.
FX = {"EUR": 1.0, "GBP": 1.17, "SEK": 0.089}
FX_NOTE = "GBP 1.17 / SEK 0.089 from autodoc_scraper sources.yaml as_of 2026-05-01 (working rate, not official)"

PLACEHOLDER_MAX = 2.34      # Autodoc-style 'no result' placeholder; anything <= this is refused

COLUMNS = [
    "obs_id", "part_no", "match_method", "competitor_brand", "competitor_pn", "description",
    "source", "source_url", "country", "observed_at", "vintage",
    "price", "price_avg", "currency", "price_eur", "fx_note", "vat",
    "price_type", "stock", "n_obs", "loader",
]
PRICE_TYPES = {
    "aftermarket_trade", "aftermarket_retail", "genuine_grey", "online_median",
    "survey_workshop", "survey_list", "dealer", "quote", "oem_value_line", "marketplace", "estimate",
}
MATCH_METHODS = {"exact_oem", "crossref", "category_only"}


def _pn(x):
    """Normalise an Isuzu part number to a 10-digit string, or None."""
    if pd.isna(x):
        return None
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = "".join(ch for ch in s if ch.isdigit())
    return s.zfill(10) if s else None


def load_ks():
    f = ROOT / "04_tools/autodoc_scraper/ks_results.csv"
    d = pd.read_csv(f, dtype={"PN": str})
    d = d[d["Status"] == "ok"]
    rows = []
    for _, r in d.iterrows():
        date = str(r["Scraped_At"])[:10]
        for kind, lo, avg, cnt, stock, ptype in [
            ("AM", "KS_AM_MinPrice_GBP", "KS_AM_AvgPrice_GBP", "KS_AM_Count", "KS_AM_InStock_Count", "aftermarket_trade"),
            ("GEN", "KS_GEN_MinPrice_GBP", "KS_GEN_AvgPrice_GBP", "KS_GEN_Count", "KS_GEN_InStock_Count", "genuine_grey"),
        ]:
            p = r[lo]
            if pd.isna(p) or p <= PLACEHOLDER_MAX:
                continue
            rows.append(dict(
                part_no=_pn(r["PN"]), match_method="exact_oem", competitor_brand=None, competitor_pn=None,
                description=r.get("Description"), source="ks-international.com", source_url=r.get("KS_URL"),
                country="UK", observed_at=date, vintage=f"KS {date}",
                price=float(p), price_avg=float(r[avg]) if pd.notna(r[avg]) else None, currency="GBP",
                vat="excl", price_type=ptype,
                stock="in" if (r[stock] or 0) > 0 else "out", n_obs=int(r[cnt] or 0), loader=f"ks_{kind.lower()}",
            ))
    return rows


def load_eucon_crossref():
    f = ROOT / "02_dashboards/Data/01_Pricing/_raw/eucon_crossref_iam_20260329.csv"
    d = pd.read_csv(f, dtype={"isze_pn": str, "competitor_pn": str})
    rows = []
    for _, r in d.iterrows():
        p = r["med_online_eur"]
        if pd.isna(p) or p <= PLACEHOLDER_MAX:
            continue
        rows.append(dict(
            part_no=_pn(r["isze_pn"]), match_method="crossref", competitor_brand=r["Competitor_Brand"],
            competitor_pn=r["competitor_pn"], description=None, source="Eucon PartsPool (Autodoc/KFZ/PKW/Skruvat)",
            source_url=None, country=r["Country"], observed_at="2026-03-29", vintage="Eucon PartsPool 2026-03-29",
            price=float(p), price_avg=None, currency="EUR", vat="incl", price_type="online_median",
            stock="unknown", n_obs=int(r["n_obs"]), loader="eucon_crossref",
        ))
    return rows


def load_eucon_survey_2023():
    f = ROOT / "01_data/00_derived/eucon_uk_survey_2023_price_gap.csv"
    d = pd.read_csv(f, dtype={"pn": str})
    d = d.drop_duplicates("pn")                  # file repeats each part per distributor book
    rows = []
    for _, r in d.iterrows():
        for col, ptype in [("workshop_gbp_median", "survey_workshop"), ("list_gbp_median", "survey_list")]:
            p = r[col]
            if pd.isna(p) or p <= 0:
                continue
            rows.append(dict(
                part_no=_pn(r["pn"]), match_method="exact_oem", competitor_brand=r.get("brands_found"),
                competitor_pn=None, description=r.get("description"), source="Eucon UK IAM Price Survey 2023",
                source_url=None, country="UK", observed_at="2024-01-09", vintage="Eucon UK survey 2023 (file 2024-01-09)",
                price=float(p), price_avg=None, currency="GBP", vat="excl", price_type=ptype,
                stock="unknown", n_obs=int(r["competitor_count"]) if pd.notna(r["competitor_count"]) else None,
                loader="eucon_survey_2023",
            ))
    return rows


def load_category_site(fname, site):
    f = ROOT / "04_tools/autodoc_scraper" / fname
    if not f.exists():
        return []
    d = pd.read_csv(f)
    rows = []
    for _, r in d.iterrows():
        p = r["Price"]
        if pd.isna(p) or p <= PLACEHOLDER_MAX:
            continue
        date = str(r["Scraped_At"])[:10]
        rows.append(dict(
            part_no=None, match_method="category_only", competitor_brand=None, competitor_pn=None,
            description=r["Product_Name"], source=site, source_url=r["Product_URL"], country=r["Country"],
            observed_at=date, vintage=f"{site} {date}", price=float(p), price_avg=None, currency=r["Currency"],
            vat="unknown", price_type="aftermarket_retail", stock="unknown", n_obs=1,
            loader=f"{site.lower().replace(' ', '_').replace('&', 'and')}",
        ))
    return rows


def validate(df):
    errors = []
    if df["price_type"].isna().any() or not set(df["price_type"]).issubset(PRICE_TYPES):
        errors.append("price_type missing or unknown")
    if df["vintage"].isna().any():
        errors.append("vintage missing")
    if not set(df["match_method"]).issubset(MATCH_METHODS):
        errors.append("match_method unknown")
    if (df["price"] <= PLACEHOLDER_MAX).any():
        errors.append("placeholder-level price present")
    bad_pn = df["part_no"].notna() & (df["part_no"].str.len() != 10)
    if bad_pn.any():
        errors.append(f"{int(bad_pn.sum())} part numbers not 10 digits")
    if df["currency"].map(FX).isna().any():
        errors.append("currency without FX rate")
    if df["obs_id"].duplicated().any():
        errors.append("duplicate obs_id")
    return errors


def main():
    parts = {
        "ks": load_ks(),
        "eucon_crossref": load_eucon_crossref(),
        "eucon_survey_2023": load_eucon_survey_2023(),
        "tmc": load_category_site("tmc_results.csv", "T&M Commercials"),
        "tranzparts": load_category_site("tranzparts_results.csv", "Tranzparts"),
    }
    df = pd.DataFrame([r for rows in parts.values() for r in rows])
    df["price_eur"] = (df["price"] * df["currency"].map(FX)).round(2)
    df["fx_note"] = FX_NOTE
    key = df[["part_no", "competitor_brand", "competitor_pn", "source", "country", "observed_at",
              "price_type", "loader", "description", "source_url"]].astype(str).agg("|".join, axis=1)
    df["obs_id"] = key.map(lambda s: hashlib.sha1(s.encode()).hexdigest()[:16])
    df = df[COLUMNS]

    errors = validate(df)
    if errors:
        raise SystemExit("REFUSED — " + "; ".join(errors))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "04_tools/price_ledger/build_price_ledger.py",
        "rows": int(len(df)),
        "rows_by_loader": df["loader"].value_counts().to_dict(),
        "rows_by_price_type": df["price_type"].value_counts().to_dict(),
        "isuzu_part_numbers_with_observation": int(df["part_no"].nunique()),
        "not_loaded": {
            "mekonomen": "RETIRED 2026-09-24 - part-number search returned an unrelated item "
                         "(Kilen coil spring for brake pad kit 8975056801); all 7 rows false",
            "auto365": "retired 2026-09-24 - no OEM part number anywhere; also robots-disallowed",
            "tranzparts": "retired 2026-09-24 - carries no Isuzu (every handle is Volvo/Iveco/DAF)",
            "autodoc": "retired; placeholder prices",
        },
        "fx": FX_NOTE,
        "rule": "price_type and vintage required; never average across price_type",
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
