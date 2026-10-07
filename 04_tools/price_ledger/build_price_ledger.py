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
  - Eucon online 2024-03-15  01_data/Eucon_March.xlsx, sheet 'Online 15032024'   (added 2026-10-01)
  - Eucon online 2025-07-28  01_data/Eucon_Online28072025.xlsx, brand RRP only    (added 2026-10-01)
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

# FX — the rates the ledger can convert with.
#
# 2026-09-24: this used to be an inline working table with only EUR, GBP and SEK,
# sourced from autodoc_scraper sources.yaml as_of 2026-05-01 and described in the
# ledger's own meta as "not official". Every Phase 1 target except KS and Omega
# prices in NOK, DKK or USD, so every row from those sites was refused by
# validate() with "currency without FX rate" before it could be stored.
#
# The table is now read from `fx_rates.json`, written by
# `04_tools/price_ledger/build_fx_rates.py` from the European Central Bank's daily
# euro reference rates (dated, public, citable). If that file is missing or
# unreadable the inline fallback below is used, so the ledger never becomes
# dependent on a network call at build time.
#
# Convention is unchanged: value = EUR per one unit of the currency, i.e.
# `price_eur = price * FX[currency]`.
#
# REBASED 2026-09-25 on Jerome's instruction. GBP and SEK now take the ECB rate, so the
# whole ledger converts from one dated, citable source. Until today it mixed two: the
# 2026-05-01 working rates for GBP/SEK (1.17 / 0.089) and ECB rates for everything else.
#
# The move was measured before it was made, because it restates stored euro values:
# 263 GBP rows, EUR 55,016.40 -> EUR 54,686.30, a net EUR -330.10, the largest single
# row moving EUR 19.30. GBP is the only affected currency - no row in the ledger is
# priced in SEK, so the SEK rebase changes nothing today but stops the two files
# disagreeing later.
#
# The fallback below is still used when fx_rates.json is missing or unreadable, so a
# build never depends on a network call. Its values are the ECB ones now, so a fallback
# build cannot silently produce different euro figures from a normal one.
_FX_FALLBACK = {"EUR": 1.0, "GBP": 1.16298002, "SEK": 0.0887744685}
FX_FILE = Path(__file__).resolve().parent / "fx_rates.json"


def _load_fx():
    """ECB rates for every currency the ledger can convert with. Never raises.

    Since the 2026-09-25 rebase the fallback and the ECB file agree on GBP and SEK, so
    `fx_rates.json` is simply the dated source of truth and there is nothing to keep back.
    """
    fx = dict(_FX_FALLBACK)
    note = ("ECB euro reference rates (fallback: fx_rates.json not readable). "
            "GBP 1.16298002 / SEK 0.0887744685 rebased 2026-09-25 on Jerome's instruction; "
            "they were 1.17 / 0.089 from the 2026-05-01 working table before that.")
    try:
        payload = json.loads(FX_FILE.read_text(encoding="utf-8"))
        rates = {k: float(v) for k, v in (payload.get("eur_per_unit") or {}).items()}
        if rates.get("EUR") == 1.0:
            fx.update(rates)
            note = (f"ECB euro reference rates, reference date "
                    f"{payload.get('reference_date')}. Whole ledger from one source; "
                    f"GBP and SEK rebased 2026-09-25 (were 1.17 / 0.089 from the "
                    f"2026-05-01 working table).")
    except Exception:                                   # noqa: BLE001
        pass
    return fx, note


FX, FX_NOTE = _load_fx()

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
    "aftermarket_rrp",      # 2026-10-01: a brand's recommended retail list price, not a street price
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


def _eucon_date(s):
    """Eucon writes dates as DMMYYYY / DDMMYYYY without separators ('1072025', '15032024')."""
    s = str(s).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if not s.isdigit() or len(s) not in (7, 8):
        return None
    s = s.zfill(8)
    try:
        return datetime.strptime(s, "%d%m%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


# Added 2026-10-01 on Jerome's go. Eucon's own match confidence on the March 2024 web-shop
# sheet: 822 rows 'Medium', 49 'Very Low', 23 'Unknown Part'. Only 'Medium' is loaded; a
# low-confidence match priced as a rival is worse than no price.
EUCON_MARCH_MATCH_OK = {"Medium"}


def load_eucon_march_2024():
    """Eucon_March.xlsx, sheet 'Online 15032024': one web-shop price per competitor part.

    Four shops (Autodoc DE/NO, PKW Teile DE, KFZ Teile DE), all observed 15 Mar 2024.
    `Online Price` is in EUR for the NO shop too (an oil filter at 5.45 cannot be NOK).
    These are single shop listings, not medians, so they are `aftermarket_retail`.
    `Online RRP` (163 rows, the shop's struck-through price) is not loaded.
    """
    f = ROOT / "01_data/Eucon_March.xlsx"
    d = pd.read_excel(f, sheet_name="Online 15032024", dtype=str)
    d = d[d["Matching Level"].isin(EUCON_MARCH_MATCH_OK)]
    rows = []
    for _, r in d.iterrows():
        p = pd.to_numeric(r["Online Price"], errors="coerce")
        if pd.isna(p) or p <= PLACEHOLDER_MAX:
            continue
        rows.append(dict(
            part_no=_pn(r["Searched Part Number"]), match_method="crossref",
            competitor_brand=r["Brand"], competitor_pn=r["Part Number"],
            description=r.get("Description (Webshop)") if pd.notna(r.get("Description (Webshop)")) else None,
            source=f"Eucon online 2024 ({r['Webshop']})",
            source_url=r.get("Webshop Link") if pd.notna(r.get("Webshop Link")) else None,
            country=r["Country"], observed_at=_eucon_date(r["Date (Webshop)"]) or "2024-03-15",
            vintage="Eucon online 2024-03-15", price=float(p), price_avg=None, currency="EUR",
            vat="unknown", price_type="aftermarket_retail", stock="unknown", n_obs=1,
            loader="eucon_march_2024",
        ))
    return rows


def load_eucon_online_2025():
    """Eucon_Online28072025.xlsx: the competitor brand's own recommended retail price.

    Only `RRP` is loaded, and only where `Currency (RRP)` is declared (904 of 5,081 rows,
    all EUR). `OE RRP` is NOT loaded: it is a price for our own part number that runs
    2.5-3.1x our list and nobody has established what it is (see
    00_docs/agent/AFTERMARKET_INTELLIGENCE_STATE_20260924.md).

    A list RRP is not a street price, so it gets its own price type, `aftermarket_rrp`.
    The extract is dated 2025-07-28 but each RRP carries its own date, some years old;
    that date is kept in `observed_at` so a stale list price is visible, not hidden.
    """
    f = ROOT / "01_data/Eucon_Online28072025.xlsx"
    d = pd.read_excel(f, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
    d = d[d["Currency (RRP)"].notna()]
    rows = []
    for _, r in d.iterrows():
        p = pd.to_numeric(r["RRP"], errors="coerce")
        if pd.isna(p) or p <= PLACEHOLDER_MAX:
            continue
        rows.append(dict(
            part_no=_pn(r["Searched Part Number"]), match_method="crossref",
            competitor_brand=r["Brand"], competitor_pn=r["Part Number"],
            description=r.get("Description") if pd.notna(r.get("Description")) else None,
            source="Eucon online export 2025 (brand RRP)", source_url=None,
            country=r["Country"], observed_at=_eucon_date(r["RRP Date"]) or "2025-07-28",
            vintage="Eucon online export 2025-07-28", price=float(p), price_avg=None,
            currency=r["Currency (RRP)"], vat="unknown", price_type="aftermarket_rrp",
            stock="unknown", n_obs=1, loader="eucon_online_2025",
        ))
    return rows


def load_ks_crossref():
    """KS International prices found by searching the COMPETITOR number (added 2026-10-01).

    Written by `04_tools/delegation/parsers/run_crossref_queries.py`, which accepts a KS
    card only when the searched competitor number is printed on it. Missing file or no
    rows = no rows, so the ledger builds without it.
    """
    f = ROOT / "04_tools" / "price_ledger" / "KS_CROSSREF_ROWS.csv"
    if not f.exists() or f.stat().st_size == 0:
        return []
    d = pd.read_csv(f, dtype={"part_no": str, "competitor_pn": str, "competitor_brand": str})
    rows = []
    for _, r in d.iterrows():
        p = r.get("price")
        if pd.isna(p) or p <= PLACEHOLDER_MAX:
            continue
        rows.append(dict(
            part_no=_pn(r["part_no"]), match_method="crossref",
            competitor_brand=r.get("competitor_brand") if pd.notna(r.get("competitor_brand")) else None,
            competitor_pn=r.get("competitor_pn"), description=r.get("description"),
            source="KS International", source_url=r.get("source_url"), country="UK",
            observed_at=r.get("observed_at"), vintage=r.get("vintage"), price=float(p),
            price_avg=None, currency="GBP", vat="excl", price_type=r.get("price_type"),
            stock=r.get("stock") if pd.notna(r.get("stock")) else "unknown", n_obs=1,
            loader="ks_crossref",
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


def load_scraped_phase1():
    """The Phase 1 web observations, offered by `build_scraped_observations.py`.

    That script is the bridge: it reads the saved pages listed in `page_manifest.csv`,
    parses them with the per-site parsers in `04_tools/delegation/parsers/`, applies the
    ONE shared FX table and writes `OFFERED_ROWS.csv` with a verdict per row. This
    function only loads what it offered — it never fetches and never parses.

    Rows whose verdict starts with `reject:` are not loaded. Missing file = no rows,
    so the ledger still builds from local sources alone if the bridge has not been run.

    U26 (2026-10-07, agent E merge): rows whose loader is `spareto_crossref` are
    deliberately NOT loaded here. A Spareto row is a cross-reference observation, not
    a usable competitor price — the price is retail incl. VAT at a rate the page does
    not state, so the evidence rules exclude it (TAX_RATE_NOT_STATED) and it would
    inflate the ledger's row counts without adding a usable comparable. It travels
    through `04_tools/aftermarket_intelligence/state/spareto_crossref.csv`, the path
    `grade_crossref_edges.py` reads. Dropped by loader, on purpose, not by accident.
    """
    f = ROOT / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv"
    if not f.exists():
        return []
    d = pd.read_csv(f, dtype={"part_no": str, "competitor_pn": str, "obs_id": str})
    if "verdict" in d.columns:
        d = d[~d["verdict"].astype(str).str.startswith("reject:")]
    if "loader" in d.columns:
        before = len(d)
        d = d[d["loader"].astype(str) != "spareto_crossref"]
        if before != len(d):
            print(f"scrape_phase1: {before - len(d)} spareto_crossref row(s) left in the "
                  f"crossref state file on purpose (not a usable competitor price)")
    # U26 2026-10-07: one product card can appear on more than one saved category page
    # (T&M's brake and service leaves overlap). The bridge issues obs_id from the
    # observation's own identity — part, competing number, seller, date, price — not from
    # the page it was read on, so the same observation read twice shares an obs_id. It IS
    # one observation, so it is counted once; `validate()` would otherwise refuse the
    # whole file with "duplicate obs_id".
    if "obs_id" in d.columns:
        before = len(d)
        d = d.drop_duplicates(subset=["obs_id"], keep="first")
        if before != len(d):
            print(f"scrape_phase1: {before - len(d)} row(s) seen on more than one saved page "
                  f"— the same observation, counted once")
    rows = []
    for _, r in d.iterrows():
        price = r.get("price")
        rows.append(dict(
            part_no=_pn(r["part_no"]) if pd.notna(r.get("part_no")) else None,
            match_method=r.get("match_method"),
            competitor_brand=r.get("competitor_brand") if pd.notna(r.get("competitor_brand")) else None,
            competitor_pn=r.get("competitor_pn") if pd.notna(r.get("competitor_pn")) else None,
            description=r.get("description") if pd.notna(r.get("description")) else None,
            source=r.get("source"), source_url=r.get("source_url") if pd.notna(r.get("source_url")) else None,
            country=r.get("country"), observed_at=r.get("observed_at"), vintage=r.get("vintage"),
            price=float(price) if pd.notna(price) else None,
            price_avg=None,
            currency=r.get("currency") if pd.notna(r.get("currency")) else None,
            vat=r.get("vat") if pd.notna(r.get("vat")) else "unknown",
            price_type=r.get("price_type"),
            stock=r.get("stock") if pd.notna(r.get("stock")) else "unknown",
            n_obs=int(r["n_obs"]) if pd.notna(r.get("n_obs")) else 1,
            loader=r.get("loader") or "scrape_phase1",
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
    # A rate is only needed for a row that actually carries a price. A price-on-request
    # listing (autoline has 15) is a legitimate match row with no price and therefore no
    # currency; demanding an FX rate for it refused the whole file. Changed 2026-09-24.
    priced_rows = df[df["price"].notna()]
    if priced_rows["currency"].isna().any():
        errors.append(f"{int(priced_rows['currency'].isna().sum())} priced rows have no currency")
    if priced_rows["currency"].map(FX).isna().any():
        bad = sorted(set(priced_rows.loc[priced_rows["currency"].map(FX).isna(), "currency"]))
        errors.append(f"currency without FX rate: {bad}")
    if df["obs_id"].duplicated().any():
        errors.append("duplicate obs_id")
    return errors


def main():
    parts = {
        "ks": load_ks(),
        "eucon_crossref": load_eucon_crossref(),
        "eucon_survey_2023": load_eucon_survey_2023(),
        "eucon_march_2024": load_eucon_march_2024(),
        "eucon_online_2025": load_eucon_online_2025(),
        "ks_crossref": load_ks_crossref(),
        "tmc": load_category_site("tmc_results.csv", "T&M Commercials"),
        "tranzparts": load_category_site("tranzparts_results.csv", "Tranzparts"),
        "scrape_phase1": load_scraped_phase1(),
    }
    df = pd.DataFrame([r for rows in parts.values() for r in rows])
    # Rows offered by the bridge already carry their euro value; only compute it where
    # it is missing, so the one shared rate table is applied once, not twice.
    fx = df["currency"].map(FX)
    calc = (df["price"] * fx).round(2)
    if "price_eur" in df.columns:
        df["price_eur"] = df["price_eur"].where(df["price_eur"].notna(), calc)
    else:
        df["price_eur"] = calc
    if "fx_note" in df.columns:
        df["fx_note"] = df["fx_note"].where(df["fx_note"].notna(), FX_NOTE)
    else:
        df["fx_note"] = FX_NOTE
    key = df[["part_no", "competitor_brand", "competitor_pn", "source", "country", "observed_at",
              "price_type", "loader", "description", "source_url", "price", "currency"]].astype(str).agg("|".join, axis=1)
    # `price` and `currency` are in the key: Amayama quotes one part from several
    # warehouses at different prices, and without them those rows collide here and the
    # whole file is refused with "duplicate obs_id".
    computed = key.map(lambda s: hashlib.sha1(s.encode()).hexdigest()[:16])
    # The bridge already issued an obs_id for its rows; keep it when present so the two
    # scripts cannot disagree.
    if "obs_id" in df.columns:
        df["obs_id"] = df["obs_id"].where(df["obs_id"].notna(), computed)
    else:
        df["obs_id"] = computed
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
            "tranzparts": "NOTE 2026-10-07 - the retired 2026-09-24 category_only loader still "
                          "does not run (that file carried no Isuzu number). Since U26 the LIVE "
                          "Tranzparts rows are page-derived (loader `tranzparts` in "
                          "OFFERED_ROWS.csv, match_method exact_oem, the searched number is "
                          "printed on the product page) and ARE loaded, with 6 rows on the 123 "
                          "worklist.",
            "autodoc": "retired; placeholder prices",
            "spareto_crossref": "NOT loaded as a price observation (2026-10-07): Spareto prices "
                                "are retail incl. VAT at a rate the page does not state, so the "
                                "evidence rules exclude them; they are a cross-reference source "
                                "in 04_tools/aftermarket_intelligence/state/spareto_crossref.csv, "
                                "used by grade_crossref_edges.py, not a price row",
        },
        "fx": FX_NOTE,
        "rule": "price_type and vintage required; never average across price_type",
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
