# -*- coding: utf-8 -*-
"""
Aftermarket intelligence — one match index, step 1 of
00_docs/agent/AFTERMARKET_INTELLIGENCE_STATE_20260924.md

One row = our part number x one competitor (brand + number) x one source file x one source date.
This is a MATCH table first and a price table second. Purpose (Jerome, 2026-09-24) is market
intelligence for PRISM: the cross-reference is the asset, the prices are a bonus where a source
genuinely carries one.

Two rules, both learned from defects found in the new Eucon files on 2026-09-24:

  RULE 1 — a row is a PRICE row only if the source file actually holds a competitor price.
           In Eucon_Online28072025.xlsx there are TWO price columns and neither is what it looks
           like. 'RRP' (with a declared currency) is a real competitor price: 904 rows, 18%, 59 of
           the 88 part numbers. 'OE RRP' is a price for OUR PART NUMBER from the OE side: 4,652
           rows, 92%. It is NOT our IE40 list (checked: it runs 2.46x to 3.14x our list on the 8
           numbers where both exist) and it is NOT a competitor's aftermarket price. It must never
           be used as one, and I have not established what it is.
           CORRECTION 2026-09-24: an earlier note said the 4,652 rows were our own ie40 list
           copied in, worth EUR 3.70M. That was wrong. 3.70M was only ever the value of the 88
           part numbers in total; the copied-list claim was never checked and does not survive it.

  RULE 2 — a competitor part is identified by brand AND number together, never by either alone.
           108 competitor numbers in the July file sit under two brand spellings, and the pattern
           is agent or subsidiary names against the manufacturer name ('BOSCH' vs 'KGK (BOSCH)',
           'GMB' vs 'GMB OCEANIA'). The normaliser unwraps a bracketed brand so those merge; a
           suffix variant like GMB OCEANIA does not, and stays flagged. We keep the raw brand AND
           the normalised brand so a join can never split them silently.

READ-ONLY on every source. Writes only into 04_tools/aftermarket_intelligence/state/.

Run:  python 04_tools/aftermarket_intelligence/build_match_index.py
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
STATE.mkdir(parents=True, exist_ok=True)

BOOK = ROOT / "01_data/00_derived"

OUT_MATCH = STATE / "match_index.csv"
OUT_REACH = STATE / "seed_reach_tierA.csv"
OUT_PAIRS = STATE / "reachable_pairs.csv"        # competitor brand+number we may search with
OUT_REPORT = STATE / "MATCH_INDEX_REPORT.md"

# ---------------------------------------------------------------- helpers


def pn_norm(x):
    """Our part-number key. 10-digit zero-padded when the value is numeric; otherwise the token is
    kept as written. NEVER collapse a non-numeric key to zeros - doing that silently merged seven
    non-part lines (REBATE, TRANSPORT, SERVICE FEE lines) into one key on the first run."""
    if pd.isna(x):
        return ""
    t = str(x).strip()
    if t.endswith(".0"):
        t = t[:-2]
    if t.isdigit() and len(t) <= 10:
        return t.zfill(10)
    return t.upper()


def z(s):
    ser = pd.Series(s, dtype="string")
    out = ser.map(pn_norm)
    out.index = ser.index
    return out


def znb(x):
    """Normalise a competitor part number for display: strip, upper, keep inner spacing."""
    return str(x).strip().upper() if pd.notna(x) else ""


def brand_norm(b):
    """Brand as written, minus reseller prefixes and punctuation noise.

    'Wilmink Group (BLUE PRINT)' -> 'BLUE PRINT'.  Nothing is invented; we only unwrap a bracket
    when the bracket contains the whole brand, and we drop a trailing '(x)' qualifier.
    """
    if pd.isna(b):
        return ""
    t = str(b).strip().upper()
    m = re.match(r"^[^(]*\(\s*([^()]+?)\s*\)\s*$", t)          # 'ANYTHING (BRAND)'
    if m:
        t = m.group(1)
    t = re.sub(r"\s*\([^()]*\)\s*$", "", t)                     # drop trailing qualifier
    t = re.sub(r"\s+", " ", t)
    return t.strip(" -.,")


def fnum(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


rows = []
report = []


def add(pn, brand_raw, cpn, source, source_date, price=None, currency=None,
        price_type="", country="", note="", has_price_col=False, vat=""):
    pn = "" if pd.isna(pn) else str(pn).strip()
    b = "" if pd.isna(brand_raw) else str(brand_raw).strip()
    c = znb(cpn)
    if not pn or not c:
        return
    n = brand_norm(b)
    price = fnum(price)
    # RULE 1
    is_price = bool(has_price_col and price is not None and price > 0)
    rows.append(dict(
        part_no=pn,
        competitor_brand=b,
        competitor_brand_norm=n,
        competitor_pn=c,
        match_key=f"{n}|{c}",
        source=source,
        source_vintage=source_date,
        has_competitor_price=int(is_price),
        competitor_price=price if is_price else None,
        currency=currency if is_price else "",
        vat=vat if is_price else "",
        price_type=price_type if is_price else "",
        country=country,
        note=note,
    ))


# ---------------------------------------------------------------- billed book + tiers

t = pd.read_csv(ROOT / "04_tools/delegation/state/refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = z(t["part_no"])
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"], errors="coerce")
t = t.drop_duplicates("part_no")

import sys as _sys
_sys.path.insert(0, str(ROOT / "04_tools" / "_shared"))
from classification_paths import figkey_export_for_release  # noqa: E402
# AIM figure-key export of the APPROVED release (sidecar + sha256 checked; raises otherwise)
FIGKEY_EXPORT, _FIGKEY_RELEASE = figkey_export_for_release()
master = pd.read_csv(FIGKEY_EXPORT, dtype=str)
master["part_no"] = z(master["part_number"])
master = master.drop_duplicates("part_no")
t = t.merge(master[["part_no", "description", "aim_level_1", "aim_level_2", "aim_level_3",
                    "figure_key", "line_kind"]], on="part_no", how="left")
t["line_kind"] = t["line_kind"].fillna("not_on_master")
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, t.billed_eur_t12m))

tier_fn = ROOT / "04_tools/delegation/state/refresh_tiers.csv"
raw_fn = ROOT / "04_tools/delegation/state/refresh_tiers_LOCAL.csv"
n_nonpart = int((t.line_kind != "part").sum())
report.append(f"- ranked list: {len(t)} lines; {n_nonpart} are not parts "
              f"(lubricant, tool, fee) and carry EUR "
              f"{t[t.line_kind != 'part'].billed_eur_t12m.sum():,.0f} of billed value")

# ---------------------------------------------------------------- 1. Eucon PartsPool crossref 2026-03

f = ROOT / "02_dashboards/Data/01_Pricing/_raw/eucon_crossref_iam_20260329.csv"
x = pd.read_csv(f, dtype=str)
x["pn"] = z(x["isze_pn"])
for _, r in x.iterrows():
    add(r.pn, r.Competitor_Brand, r.competitor_pn,
        "Eucon crossref (PartsPool)", "2026-03-29",
        price=r.get("med_online_eur"), currency="EUR", price_type="online_median",
        country=r.get("Country", ""), has_price_col=True,
        note="online IAM median, DE/NO" + ("" if str(r.get("n_obs", "")).strip() in ("", "1") else f", n={r.get('n_obs')}"))
report.append(f"- Eucon crossref 2026-03: {len(x)} rows, {x.pn.nunique()} Isuzu numbers, "
              f"{x.competitor_pn.nunique()} competitor numbers")

# ---------------------------------------------------------------- 2. Eucon Online 2025-07 (rule 1 applies)

f = ROOT / "01_data/Eucon_Online28072025.xlsx"
e = pd.read_excel(f, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
ownlist_rows = e[e["OE RRP"].notna()]
report.append(f"- Eucon Online 2025-07: {len(e)} rows. Two price columns, different meanings: "
              f"'RRP' + a declared currency is a real competitor price on {e['RRP'].notna().sum()} rows "
              f"({100 * e['RRP'].notna().mean():.0f}%), covering {e[e['RRP'].notna()].pn.nunique()} of "
              f"{e.pn.nunique()} part numbers. 'OE RRP' is a price for OUR part number on "
              f"{e['OE RRP'].notna().sum()} rows ({100 * e['OE RRP'].notna().mean():.0f}%) - "
              f"loaded as MATCH rows with no competitor price (RULE 1).")
for _, r in e.iterrows():
    has_price = pd.notna(r["RRP"]) and str(r.get("Currency (RRP)", "")).strip() != ""
    add(r.pn, r.get("Brand"), r.get("Part Number"),
        "Eucon Online extract", "2025-07-28",
        currency=(str(r.get("Currency (RRP)")).strip() if pd.notna(r.get("Currency (RRP)")) else ""),
        price_type="online_retail", country=r.get("Country", ""),
        has_price_col=has_price,
        note="" if has_price else "match only - this row has no competitor price")
    # additional / superseded competitor numbers on the same row
    extra = r.get("Additional Part Numbers")
    if isinstance(extra, str) and extra.strip():
        for c in extra.split(","):
            c = c.strip()
            if c:
                add(r.pn, r.get("Brand"), c,
                    "Eucon Online extract (additional no.)", "2025-07-28",
                    note="listed as an additional number for this brand")
report.append(f"  - distinct Isuzu numbers {e.pn.nunique()}; competitor numbers "
              f"{e['Part Number'].nunique()}; brand+number pairs "
              f"{(e['Brand'].fillna('') + '|' + e['Part Number'].fillna('')).nunique()}")

# ---------------------------------------------------------------- 3. Eucon Online 2024-03

f = ROOT / "01_data/Eucon_March.xlsx"
m = pd.read_excel(f, sheet_name="Online 15032024", dtype=str)
m["pn"] = z(m["Searched Part Number"])
for _, r in m.iterrows():
    add(r.pn, r.get("Brand"), r.get("Part Number"),
        "Eucon March online", "2024-03-15",
        price=r.get("Online Price"), currency="EUR", price_type="online_retail",
        country=r.get("Country", ""), has_price_col=pd.notna(r.get("Online Price")),
        note=f"web shop {r.get('Webshop','')}".strip())
report.append(f"- Eucon March online 2024-03: {len(m)} rows, {m.pn.nunique()} Isuzu numbers, "
              f"{m['Part Number'].nunique()} competitor numbers, "
              f"{m['Online Price'].notna().sum()} priced")

# ---------------------------------------------------------------- 4. Eucon March RRP MODE (own number, no competitor)

f = ROOT / "01_data/Eucon_March.xlsx"
r4 = pd.read_excel(f, sheet_name="RRP MODE", dtype=str)
r4["pn"] = z(r4["Searched Part Number"])
for _, r in r4.iterrows():
    add(r.pn, "Isuzu (our own number)", r["Searched Part Number"],
        "Eucon March RRP", "2024-03-15",
        price=r.get("RRP"), currency=str(r.get("Currency (RRP)") or "").strip(),
        price_type="oem_recommended_retail", country=r.get("Country", ""),
        has_price_col=pd.notna(r.get("RRP")),
        note="competitor recommended retail for OUR number, not an aftermarket equivalent")
report.append(f"- Eucon March RRP 2024-03: {len(r4)} rows, {r4.pn.nunique()} Isuzu numbers, "
              f"our-number RRP only")

# ---------------------------------------------------------------- 5. Eucon UK/ITUK 2023 IAM survey

f = ROOT / "01_data/01_Pricing/_raw/Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx"
for sheet, d in pd.read_excel(f, sheet_name=None, dtype=str).items():
    d.columns = [c.strip() for c in d.columns]
    d["pn"] = z(d["Isuzu Part Number"])
    for _, r in d.iterrows():
        if str(r.get("Competitor Part Number", "")).strip() in ("", "nan"):
            continue
        add(r.pn, r.get("Manufacturer Brand"), r.get("Competitor Part Number"),
            "Eucon UK IAM survey", "2023 (file 2024-01-09)",
            price=r.get("Workshop Purchase Price"), currency="GBP", vat="excl",
            price_type="survey_workshop", country="UK",
            has_price_col=pd.notna(r.get("Workshop Purchase Price")),
            note=f"{sheet}: {r.get('Comparability Quality','')}".strip(" :"))
    report.append(f"- Eucon UK IAM survey [{sheet}]: {len(d)} rows")

# ---------------------------------------------------------------- 6. Isuzu genuine -> BVP value line

b = pd.read_csv(BOOK / "genuine_bvp_crossref.csv", dtype=str)
b["pn"] = z(b["genuine_pn"])
for _, r in b.iterrows():
    add(r.pn, "Isuzu BVP (our own value line)", r.get("bvp_pn"),
        "Isuzu genuine to BVP catalogue", "catalogue",
        note=f"{r.get('product_family','')} / {r.get('product_subgroup','')}".strip(" /"))
report.append(f"- Isuzu genuine to BVP (our OWN cheaper line, not a rival): {len(b)} rows, "
              f"{b.pn.nunique()} Isuzu numbers, {b['bvp_pn'].nunique()} BVP numbers")

# ---------------------------------------------------------------- 7. peer-maker number map (DAF/Toyota/Ford)

o = pd.read_csv(ROOT / "02_dashboards/Data/00_derived/eucon_comparable_oem_gap_20260810.csv", dtype=str)
o["pn"] = z(o["isze_pn"])
for _, r in o.iterrows():
    if str(r.get("comparability", "")).strip().upper() == "NOT COMPARABLE":
        continue
    add(r.pn, str(r.get("brand", "")).strip(), r.get("peer_oe_pn"),
        "Peer carrier number (Eucon OEM survey)", "2023",
        country=r.get("src", ""),
        note=f"{r.get('veh_desc','')} - {r.get('comparability','')}".strip(" -"))
report.append(f"- peer-maker map (the CARRIER's own number, not an aftermarket rival): {len(o)} rows, "
              f"{o.pn.nunique()} Isuzu numbers, {o['peer_oe_pn'].nunique()} peer numbers, "
              f"{(o.comparability.str.upper() == 'NOT COMPARABLE').sum()} NOT COMPARABLE excluded")

# ---------------------------------------------------------------- 8. KS shop listings (numbers we can search with)

d = pd.read_csv(ROOT / "04_tools/autodoc_scraper/_snapshots/2026-09-22/ks_results.csv", dtype=str)
n_ks = 0
for _, r in d.iterrows():
    pn = z(pd.Series([r["PN"]])).iloc[0]
    skus = r.get("KS_AM_SKUs")
    if isinstance(skus, str) and skus.strip() not in ("", "|"):
        for tok in [s.strip() for s in skus.split("|") if s.strip()]:
            # the SKU token is a shop-side identifier, not always a brand+number pair
            add(pn, "KS shop listing", tok, "KS International shop", "2026-09-22",
                country="UK", note="shop SKU seen on a KS result page")
            n_ks += 1
report.append(f"- KS shop listings: {n_ks} shop SKU tokens added as searchable objects")

# ---------------------------------------------------------------- write the match index

mi = pd.DataFrame(rows)
mi = mi.drop_duplicates(["part_no", "competitor_brand_norm", "competitor_pn", "source", "country"])

# RULE 2 — flag numbers that appear under more than one brand
collide = mi.groupby("competitor_pn").competitor_brand_norm.nunique()
mi["cpn_brand_collision"] = mi.competitor_pn.map(collide).fillna(0).astype(int) > 1

# and numbers that sit under more than one of OUR part numbers
multi = mi.groupby("competitor_pn").part_no.nunique()
mi["cpn_multi_partno"] = mi.competitor_pn.map(multi).fillna(0).astype(int) > 1

mi = mi.sort_values(["part_no", "source", "competitor_brand_norm", "competitor_pn"])
mi.to_csv(OUT_MATCH, index=False, encoding="utf-8")

# ---------------------------------------------------------------- reach

g = mi.groupby("part_no").agg(
    n_competitors=("competitor_pn", "nunique"),
    n_brands=("competitor_brand_norm", "nunique"),
    n_sources=("source", "nunique"),
    n_price_rows=("has_competitor_price", "sum"),
    newest_source=("source_vintage", "max"),
).reset_index()

t2 = t.merge(g, on="part_no", how="left")
t2["n_competitors"] = t2.n_competitors.fillna(0).astype(int)
t2["n_brands"] = t2.n_brands.fillna(0).astype(int)
t2["n_sources"] = t2.n_sources.fillna(0).astype(int)
t2["n_price_rows"] = t2.n_price_rows.fillna(0).astype(int)
t2["has_crossref"] = (t2.n_competitors > 0).astype(int)

# reach is graded, because "a competitor number" and "a price we can use now" are not the same
# thing, and neither is a peer carrier's own number.
peer_set = set(o[o.comparability.str.upper() != "NOT COMPARABLE"].pn)
price_set = set(mi[mi.has_competitor_price == 1].part_no)
inside_set = set(mi[mi.competitor_brand_norm != "Isuzu (our own number)"].part_no)
rival_set = set(mi[(mi.competitor_brand_norm != "Isuzu (our own number)")
                   & (~mi.source.str.startswith("Isuzu genuine to BVP"))
                   & (~mi.source.str.startswith("Peer carrier"))].part_no)


def reach_of(pn):
    if pn in price_set:
        return "price_now"
    if pn in rival_set:
        return "rival_number_no_price"
    if pn in inside_set:
        return "inside_the_brand_only"
    if pn in peer_set:
        return "peer_number_only"
    return "none"


t2["reach"] = t2.part_no.map(reach_of)

A = t2[t2.tier == "A"].copy()
A = A[["part_no", "description", "aim_level_1", "aim_level_2", "figure_key", "billed_eur_t12m",
       "line_kind", "reach", "n_competitors", "n_brands", "n_sources", "n_price_rows",
       "newest_source"]]
A = A.sort_values(["reach", "n_competitors", "billed_eur_t12m"], ascending=[True, False, False])
A.to_csv(OUT_REACH, index=False, encoding="utf-8")

# competitor objects we could search with
pr = mi[mi.competitor_brand_norm != ""][["match_key", "competitor_brand_norm", "competitor_pn"]]
pr = pr.drop_duplicates("match_key").sort_values("match_key")
pr.to_csv(OUT_PAIRS, index=False, encoding="utf-8")

# ---------------------------------------------------------------- report

tot = t.billed_eur_t12m.sum()
Aall = t2[t2.tier == "A"]
reach_summary = (Aall.groupby("reach")
                 .agg(parts=("part_no", "size"), billed=("billed_eur_t12m", "sum"))
                 .reset_index())

report.append("")
report.append("## Match index")
report.append(f"- rows: {len(mi)}")
report.append(f"- distinct Isuzu numbers matched: {mi.part_no.nunique()}")
report.append(f"- distinct competitor numbers: {mi.competitor_pn.nunique()}")
report.append(f"- distinct competitor brands: {mi.competitor_brand_norm.nunique()}")
report.append(f"- rows carrying a usable competitor price: {int(mi.has_competitor_price.sum())} "
              f"({100 * mi.has_competitor_price.mean():.1f}%)")
report.append(f"- competitor numbers under more than one brand (RULE 2 flag): "
              f"{int((mi.groupby('competitor_pn').competitor_brand_norm.nunique() > 1).sum())}")
report.append(f"- Isuzu numbers still with no competitor number: "
              f"{len(t2) - t2.has_crossref.sum()} of {len(t2)}")
report.append("")
report.append("## Tier A reach, graded")
report.append("(price_now = a real competitor price exists today; rival_number_no_price = a rival's "
              "number exists but no price; inside_the_brand_only = only our own value line or our "
              "own number; peer_number_only = only a peer CARRIER's own number, which is not an "
              "aftermarket rival; none = nothing to search with)")
for _, r in reach_summary.iterrows():
    report.append(f"- {r['reach']}: {r.parts} parts, EUR {r.billed:,.0f} "
                  f"({100 * r.billed / Aall.billed_eur_t12m.sum():.1f}% of Tier A)")
report.append("")
report.append(f"## Whole book: {t2.has_crossref.sum()} of {len(t2)} parts carry SOME number "
              f"(rival, our own, or a peer carrier), EUR "
              f"{t2[t2.has_crossref == 1].billed_eur_t12m.sum():,.0f} "
              f"({100 * t2[t2.has_crossref == 1].billed_eur_t12m.sum() / tot:.1f}% of billed). "
              f"Parts carrying an actual RIVAL number: {len(rival_set)}.")
report.append("")
report.append("## Corrections to the 2026-09-24 state note")
report.append("- The note said 4,652 rows in the July file carried our own list price. Wrong. "
              "4,652 rows carry 'OE RRP', a price for our part number that is NOT our list "
              "(2.46x-3.14x our list on the 8 numbers where both exist) and is NOT an aftermarket "
              "price either. What it is has not been established.")
report.append("- The note said the mislabelled rows were worth EUR 3.70M. There is no such "
              "figure in the file. 3.70M was the billed value of all 88 part numbers; the "
              "EUR 3.70M in the 2024 RRP sheet is a different figure entirely.")
report.append("- The note said the ranked list had duplicate part numbers. It does not: 16,511 "
              "rows, 16,511 distinct numbers. The duplicate was in the PRICE LIST (165,366 rows, "
              "165,366 distinct numbers) and was a different thing.")
report.append("- Three of the four 'defects' in that note did not survive checking. The brand "
              "variants are real (108 numbers under two spellings, mostly 'BOSCH' vs 'KGK (BOSCH)' "
              "and 'GMB' vs 'GMB OCEANIA').")

(OUT_REPORT).write_text(
    "# Match index build report\n\n"
    f"Built {datetime.now(timezone.utc).isoformat(timespec='seconds')} by "
    "`04_tools/aftermarket_intelligence/build_match_index.py`\n\n"
    "One row = our part number x competitor brand and number x source file x source date.\n\n"
    + "\n".join(report) + "\n", encoding="utf-8")

print("\n".join(report))
print("\nwrote:")
for p in (OUT_MATCH, OUT_REACH, OUT_PAIRS, OUT_REPORT):
    print("  ", p)
