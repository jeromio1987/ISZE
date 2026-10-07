# -*- coding: utf-8 -*-
"""Work package D - mine what we already hold. Read only. No scraping, no network.

For the 123 worklist numbers: re-read the Eucon raw files, the UK survey files and the
Portugal online export; report every observation present in a raw file but absent from
the ledger, with the specific reason. Also builds the old->current supersession map.

Writes only inside _u26/D.
"""
import json
import re
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent

LEDGER   = MAIN / "01_data" / "00_derived" / "price_observations.parquet"
GRADED   = MAIN / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
WORKLIST = MAIN / "01_data" / "90_INBOX" / "MARKET_SCRAPE_WORKLIST_20261007.csv"
SUPMAP   = MAIN / "01_data" / "00_derived" / "pn_supersession_map.csv"
PL       = MAIN / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"

RAW = MAIN / "01_data" / "01_Pricing" / "_raw"
F_PP    = RAW / "eucon_pricing_partspool_20260329.xlsx"
F_ONL   = MAIN / "01_data" / "Eucon_Online28072025.xlsx"
F_MAR   = MAIN / "01_data" / "Eucon_March.xlsx"
F_CX    = MAIN / "02_dashboards" / "Data" / "01_Pricing" / "_raw" / "eucon_crossref_iam_20260329.csv"
F_SIAM  = RAW / "Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx"
F_SUK   = RAW / "Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx"
F_SITUK = RAW / "Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx"

PH = 2.34
counts = dict(raw_files_read=0, rows_examined=0, rows_linked_to_123=0)
files_seen = []


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


def pn1(x):
    if pd.isna(x):
        return None
    s = "".join(ch for ch in str(x) if ch.isdigit())
    if not s:
        return None
    s = s.zfill(10)
    return s if len(s) == 10 else None


def find10(x):
    if pd.isna(x):
        return []
    return re.findall(r"\b\d{10}\b", str(x))


def bkey(brand, pn):
    b = "" if brand is None or pd.isna(brand) else re.sub(r"[^A-Z0-9]", "", str(brand).upper())
    p = "" if pn is None or pd.isna(pn) else re.sub(r"[^A-Z0-9]", "", str(pn).upper())
    return b + "|" + p


w = pd.read_csv(WORKLIST, dtype=str)
w["pn"] = z(w["part_number"])
pns = sorted(set(w["pn"]))
wpn = set(pns)
fam = w.drop_duplicates("pn").set_index("pn")["pms_category"].to_dict()

led = pd.read_parquet(LEDGER)
led["pn"] = z(led["part_no"])
led = led[led.pn.isin(wpn)].copy()
led_idx = {}
for _, r in led.iterrows():
    led_idx.setdefault(r["pn"], []).append(r)


def present(pn, brand, cpn, loader, match_pn=True):
    for r in led_idx.get(pn, []):
        if str(r.get("loader")) != loader:
            continue
        if not match_pn:
            return r
        if bkey(r.get("competitor_brand"), r.get("competitor_pn")) == bkey(brand, cpn):
            return r
    return None


def any_loader(pn, brand, cpn):
    for r in led_idx.get(pn, []):
        if bkey(r.get("competitor_brand"), r.get("competitor_pn")) == bkey(brand, cpn):
            return r
    return None


raw = []
extra = {}


def add(file, sheet, loader, pn_list, brand, cpn, price, currency, note):
    counts["rows_examined"] += 1
    hit = [p for p in pn_list if p in wpn]
    if hit:
        counts["rows_linked_to_123"] += 1
    for p in hit:
        raw.append(dict(part_no=p, raw_file=file, sheet=sheet, expected_loader=loader,
                        competitor_brand=("" if pd.isna(brand) else str(brand)),
                        competitor_pn=("" if pd.isna(cpn) else str(cpn)),
                        price=(None if pd.isna(price) else price),
                        currency=currency, note=note))


# ---- Eucon PartsPool batch (2026-03-29) -----------------------------------
xl = pd.ExcelFile(F_PP)
files_seen.append((F_PP.name, xl.sheet_names))
pp = xl.parse("Eucon_Pricing_Clean", dtype=str)
counts["raw_files_read"] += 1
extra["partspool_clean_rows"] = len(pp)
for _, r in pp.iterrows():
    add(F_PP.name, "Eucon_Pricing_Clean", "eucon_crossref", [pn1(r["Searched_PN_Isuzu"])],
        r["Competitor_Brand"], r["Competitor_PN"], r["Online_Price_EUR"], r["Currency"], "partspool")
counts["rows_examined"] += len(xl.parse("Summary_by_PN", dtype=str))

# ---- Eucon online export 2025-07-28 ---------------------------------------
xl = pd.ExcelFile(F_ONL)
files_seen.append((F_ONL.name, xl.sheet_names))
onl = xl.parse("Fresh list_Export_28072025_0932", dtype=str)
counts["raw_files_read"] += 1
extra["online2025_rows"] = len(onl)
extra["online2025_addpn_nonempty"] = int((onl["Additional Part Numbers"].fillna("").str.strip() != "").sum())
for _, r in onl.iterrows():
    add(F_ONL.name, "Fresh list_Export_28072025_0932", "eucon_online_2025", find10(r["OE Part Number"]),
        r["Brand"], r["Part Number"], r["RRP"], r["Currency (RRP)"],
        "CurrencyRRP=%s" % ("blank" if pd.isna(r["Currency (RRP)"]) else r["Currency (RRP)"]))
for sh in xl.sheet_names:
    if sh != "Fresh list_Export_28072025_0932":
        counts["rows_examined"] += len(xl.parse(sh, dtype=str)) if len(xl.parse(sh, dtype=str).columns) else 0

# ---- Eucon March 2024 ------------------------------------------------------
xl = pd.ExcelFile(F_MAR)
files_seen.append((F_MAR.name, xl.sheet_names))
mar = xl.parse("Online 15032024", dtype=str)
counts["raw_files_read"] += 1
extra["march_online_rows"] = len(mar)
for _, r in mar.iterrows():
    add(F_MAR.name, "Online 15032024", "eucon_march_2024", [pn1(r["Searched Part Number"])],
        r["Brand"], r["Part Number"], r["Online Price"], "EUR",
        "MatchingLevel=%s" % r.get("Matching Level"))
rrp = xl.parse("RRP MODE", dtype=str)
extra["march_rrpmode_rows"] = len(rrp)
for _, r in rrp.iterrows():
    add(F_MAR.name, "RRP MODE", None, find10(r["OE Part Number"]), r["Brand"], r["Part Number"],
        r["RRP"], r["Currency (RRP)"], "SupersessionID=%s" % r.get("Supersession Info ID"))
for sh in ("Online comparison", "RRP comparison"):
    if sh in xl.sheet_names:
        counts["rows_examined"] += len(xl.parse(sh, dtype=str))

# ---- UK / ITUK survey files ------------------------------------------------
extra["survey_files_missing"] = []
for path in (F_SIAM, F_SUK, F_SITUK):
    if not path.exists():
        extra["survey_files_missing"].append(path.name)
        continue
    xl = pd.ExcelFile(path)
    files_seen.append((path.name, xl.sheet_names))
    counts["raw_files_read"] += 1
    for sh in xl.sheet_names:
        d = xl.parse(sh, dtype=str)
        d.columns = [c.strip() for c in d.columns]
        counts["rows_examined"] += len(d)
        if "Isuzu Part Number" in d.columns:
            for _, r in d.iterrows():
                add(path.name, sh, "eucon_survey_2023", [pn1(r["Isuzu Part Number"])],
                    r.get("Manufacturer Brand"), r.get("Competitor Part Number"),
                    r.get("Workshop Purchase Price"), "GBP", "survey IAM")
        elif "CustomerPartNumber" in d.columns:
            for _, r in d.iterrows():
                add(path.name, sh, "eucon_survey_2023", [pn1(r["CustomerPartNumber"])],
                    r.get("CompetitorBrand"), r.get("CompetitorPartNumber"),
                    r.get("CompetitorPrice"), r.get("Currency"), "survey OEM")

# ---- crossref csv (read only, for the duplicate test) ----------------------
cx = pd.read_csv(F_CX, dtype=str)
extra["crossref_csv_rows"] = len(cx)
extra["graded_rows"] = sum(1 for _ in open(GRADED, encoding="utf-8")) - 1

print("raw files read %d ; rows examined %d ; rows linked to the 123 %d"
      % (counts["raw_files_read"], counts["rows_examined"], counts["rows_linked_to_123"]))


# ===========================================================================
# classify
# ===========================================================================
rows = pd.DataFrame(raw)
rows = rows.drop_duplicates(subset=["part_no", "raw_file", "sheet", "competitor_brand", "competitor_pn", "price"])
print("distinct raw observations on the 123:", len(rows))

out = []
for _, r in rows.iterrows():
    p = r.part_no
    price = pd.to_numeric(r.price, errors="coerce")
    ld = r.expected_loader
    if ld is None:
        hit = None
    else:
        hit = present(p, r.competitor_brand, r.competitor_pn, ld,
                      match_pn=(ld != "eucon_survey_2023"))
    if hit is not None:
        continue
    other = any_loader(p, r.competitor_brand, r.competitor_pn)

    code, ev = None, ""
    if r.raw_file == F_PP.name:
        if other is not None:
            code = "DUPLICATE_NOT_IN_LEDGER"
            ev = "pair present in ledger under loader %s" % other.get("loader")
        else:
            code = "PAIR_MISSING_FROM_LOADER"
            ev = ("in Eucon_Pricing_Clean; the ledger loads the derived crossref csv "
                  "eucon_crossref_iam_20260329.csv (492 pairs, same source)")
    elif r.raw_file == F_ONL.name:
        if pd.isna(price) or price <= PH:
            code = "REQUIRED_FIELD_EMPTY"
            ev = "RRP=%s Currency(RRP)=%s: loader keeps only rows where Currency (RRP) is not null" % (price, r.currency)
        elif other is not None:
            code = "DUPLICATE_NOT_IN_LEDGER"
            ev = "pair present in ledger under loader %s" % other.get("loader")
        else:
            code = "LOADER_FILTERED_ROW"
            ev = "Currency(RRP)=%s RRP=%s: expected to load, absent" % (r.currency, price)
    elif r.raw_file == F_MAR.name and r.sheet == "Online 15032024":
        ml = str(r.note).split("=")[-1]
        if ml in ("Very Low", "Unknown Part"):
            code = "LOADER_DROPS_MATCHING_LEVEL"
            ev = "Matching Level '%s' not in EUCON_MARCH_MATCH_OK={'Medium'}" % ml
        elif pd.isna(price) or price <= PH:
            code = "LOADER_DROPS_PLACEHOLDER_PRICE"
            ev = "Online Price=%s <= %.2f" % (price, PH)
        elif other is not None:
            code = "DUPLICATE_NOT_IN_LEDGER"
            ev = "pair present in ledger under loader %s" % other.get("loader")
        else:
            code = "LOADER_FILTERED_ROW"
    elif r.raw_file == F_MAR.name and r.sheet == "RRP MODE":
        if other is not None:
            code = "DUPLICATE_NOT_IN_LEDGER"
            ev = "pair present in ledger under loader %s" % other.get("loader")
        else:
            code = "FILE_SHEET_NEVER_LOADED"
            ev = "no loader for sheet 'RRP MODE' in build_price_ledger.py (%d rows, all with Currency (RRP))" % len(rrp)
    if code is None:
        if other is not None:
            code, ev = "DUPLICATE_NOT_IN_LEDGER", "pair present in ledger under loader %s" % other.get("loader")
        else:
            code, ev = "FILE_NEVER_LOADED", "no loader in build_price_ledger.py for %s / %s" % (r.raw_file, r.sheet)

    out.append(dict(part_no=p, family=fam.get(p, ""), raw_file=r.raw_file, sheet=r.sheet,
                    competitor_brand=r.competitor_brand, competitor_pn=r.competitor_pn,
                    price=r.price, currency=r.currency, why_missing=code, evidence=ev,
                    expected_loader=(r.expected_loader or "(none)")))

mo = pd.DataFrame(out)
mo = mo.sort_values(["why_missing", "part_no"])
mo.to_csv(OUT / "missing_observations.csv", index=False, encoding="utf-8")
print("\nMISSING OBSERVATIONS: %d" % len(mo))
print(mo.why_missing.value_counts().to_dict())
print("by file:", mo.groupby("raw_file").size().to_dict())
print("distinct PNs:", mo.part_no.nunique() if len(mo) else 0)


# ---- counts -----------------------------------------------------------------
counts["distinct_raw_observations_on_123"] = int(len(rows))
counts["observations_missing"] = int(len(mo))
counts["reasons_by_count"] = mo.why_missing.value_counts().to_dict()
counts["missing_by_file"] = mo.groupby("raw_file").size().to_dict()
counts["missing_by_family"] = mo.groupby("family").size().to_dict()
counts["missing_distinct_pns"] = int(mo.part_no.nunique())
counts["files_seen"] = [list(x) for x in files_seen]
counts.update(extra)
json.dump(counts, open(OUT / "_counts.json", "w"), indent=2)
print("wrote _counts.json")
