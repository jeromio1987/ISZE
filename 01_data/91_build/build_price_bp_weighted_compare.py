"""Base-price impact, weighted by the last 12 months of sales.

Compares the NEW PRICE CD (2026-09-10) against the CY2026 revised base price
(PRICE CD 250912) and weights every part number by what that customer actually
bought in the last 12 months of billing.

This is STEP 1 only: a weighted base-price comparison.
It does NOT apply FX, does NOT change a list, and does NOT run the allocation
engine. Per SPEC ISZE_Pricing_Spec_v1.md the FOB/SP formula is IML-owned and
untouched here.

Outputs (01_data/00_derived/):
  price_bp_weighted_compare_pn.csv        one row per part number x customer
  price_bp_weighted_compare_customer.csv  one row per customer + roll-ups
  price_bp_weighted_compare_meta.json     inputs, window, coverage, class map

Method
------
  delta_jpy      = bp_new - bp_prior                     (JPY per unit)
  delta_pct      = bp_new / bp_prior - 1                 (per unit, unweighted)
  weighted_pct   = sum(qty * bp_new) / sum(qty * bp_prior) - 1
                   == sum(qty * delta_jpy) / sum(qty * bp_prior)

Both bases satisfy  sum(w * bp_new) / sum(w * bp_prior) - 1 == sum(w*pct),
so the two read-outs are the same statistic. The euro value of the step is
reported separately so the FX effect is never mixed into the percentage.

Run:  python 01_data/91_build/build_price_bp_weighted_compare.py
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
RAW = ISZE / "01_data" / "01_Pricing" / "_raw"
DERIVED = ISZE / "01_data" / "00_derived"

NEW_PRICE_CD = RAW / "PRICE_CD_20260910.xlsx"
SIM_XLSX = RAW / "pricing_simulation_2026_5pct.xlsx"
SALES_FACT = DERIVED / "sales_fact.parquet"
REVISION_CD = DERIVED / "pricing_revision_cd.parquet"
DIST_DIM = DERIVED / "distributor_dimension.csv"

OUT_PN = DERIVED / "price_bp_weighted_compare_pn.csv"
OUT_CUST = DERIVED / "price_bp_weighted_compare_customer.csv"
OUT_META = DERIVED / "price_bp_weighted_compare_meta.json"

# Last 12 months of available billing (sales_fact ends 2026-06-30).
L12M_START = pd.Timestamp("2025-07-01")
L12M_END = pd.Timestamp("2026-06-30")

# FX in force (Legend sheet 2025-10-01 + 03_analytics/isze_pricing/config.yaml).
# Used ONLY to value the JPY step in EUR. Never mixed into a percentage.
FX_JPY_PER_EUR = 163.7
FX_AS_OF = "2025-10-01"

# PRICE CD 250912 is the revision already wired into derived tables.
# The L12M window opens before that revision so its first months ran on the
# older price. Which vintage counts as "prior" is therefore a judgement call,
# submitted to a sensitivity: see bp_prior_billed / sensitivity block.
REVISION_EFFECTIVE = pd.Timestamp("2025-09-12")

# PRICE CD uses 2-char codes; the pricing formula needs 1 letter.
# Reuse of build_pricing_enquiry_tables.map_cd_class (do not reinvent).
CLASS_OK = set("CDFJMPVTYXZBEWG")

# Non-parts billing (service fee / demurrage) is not a priceable book.
SCOPE_EXCLUDE = {"excluded_non_parts"}
# Customers that are not ISZE network distributors.
ROLE_NOT_CUSTOMER = {"not_a_customer", "excluded_entity"}
# Weight on the simulation's own l12m quantity, for comparison with billing.
SENS_SIM_QTY = "sim_l12m_qty"

# Lubricants. Two independent signals must agree before an unpriced line is called
# a lubricant: the SAP part-number family (the 05 prefix) and the billed
# description naming a lubricant. The prefix alone is a guess about any material
# numbered 05..., and the description alone is a guess about free text; together
# they are a check a reader can follow. The build below asserts that tightening
# the rule did not move a single row out of (or into) the lubricant bucket.
LUBRICANT_DESC_TOKENS = ("RIMULA", "RIM R", "RIMR", "TELLUS", "SHELL", "HELIX",
                         "SPIRAX", "OMALA", "GADUS", "A246 LUB")

# Reader-facing copy for the excluded buckets, held here so the HTML page and the
# workbook cannot drift apart: both render this one block. A machine label such as
# "rebate_or_non_part_admin" tells a reader nothing about what the euro is, whose
# it is, or why it could not be priced.
EXCLUDED_COPY = {
    "no_price_on_one_side": {
        "what": "Parts with no matching price on one side",
        "why": ("Genuine parts, but the two price lists do not both cover the number, "
                "so there is no pair to compare."),
    },
    "rebate_or_non_part_admin": {
        "what": "Non-parts lines: rebates, transport, service fees",
        "why": ("Not parts at all, so no catalogue price sits behind them: annual rebate "
                "credits, transport charges and service fees."),
    },
    "lubricant_no_pr00_in_sap": {
        "what": "Lubricants and engine oil, UMI Israel",
        "why": ("The new price file carries no lubricant part numbers, so there is nothing "
                "to compare them against."),
    },
}
EXCLUDED_COPY_OUT_OF_SCOPE = {
    "non_parts": {
        "what": "Non-part billing: service fee and demurrage",
        "why": "Not a priceable part - a service charge, not goods.",
    },
    "direct_account": {
        "what": "Outside the network: direct account",
        "why": "Trades with ISZE but is not a network distributor.",
    },
}


def norm_pn(value) -> str | None:
    """PRICE CD integer-drops leading zeros. Everything keys on 10 chars."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        digits = str(int(value))
    else:
        digits = re.sub(r"\D", "", str(value).strip())
    if len(digits) < 8:
        return None
    return digits.zfill(10)


def sap_code(value) -> str | None:
    """sales_fact.sold_to_sap is a float; the dimension uses plain ints."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(int(value))


def map_cd_class(raw) -> str | None:
    """2-char PRICE CD code -> 1-letter pricing class. Copied verbatim from
    build_pricing_enquiry_tables.map_cd_class so both agree by construction."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip().upper()
    if not s or s in {"NAN", "NONE"}:
        return None
    if len(s) == 1 and s in CLASS_OK:
        return s
    if s[-1] in CLASS_OK:
        return s[-1]
    return s[0] if s[0] in CLASS_OK else None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def customer_labeler(frame: pd.DataFrame):
    """Return a function that turns a sold-to code into a label a reader can place.

    The bucket tables name their customers, so the code alone is not enough. The
    distributor code is preferred because it is the same label the rest of the
    pack uses (UMI, UTI, ITUK, IUK); the paid name is the fallback.
    """
    def label(code: str) -> str:
        f = frame[frame["cust"] == code]
        for col in ("distributor_code", "gps_db_label", "customer_name"):
            if col in f.columns:
                vals = [str(v).strip() for v in f[col].dropna().unique()
                        if str(v).strip() and str(v).strip().lower() != "nan"]
                if vals:
                    return vals[0]
        names: set[str] = set()
        for lst in f["sold_to_names"].dropna():
            for nm in lst:
                nm = str(nm).strip()
                if nm and not nm.replace(".", "").isdigit() and nm.lower() != "nan":
                    names.add(nm)
        return sorted(names)[0] if names else f"sold-to {code}"
    return label


def _sheet_rows(path: Path, sheet) -> tuple[list[str], list[tuple]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    it = ws.iter_rows(values_only=True)
    header = [str(x).strip() if x is not None else "" for x in next(it)]
    rows = [r for r in it if any(v is not None for v in r)]
    wb.close()
    return header, rows


def load_new_price_cd() -> pd.DataFrame:
    """New PRICE CD: 10-char PN -> new base price (JPY) + raw class code."""
    header, rows = _sheet_rows(NEW_PRICE_CD, "Sheet1")
    idx = {h.lower(): i for i, h in enumerate(header)}
    i_pno, i_bp = idx["pno"], idx["base price"]
    i_cls = idx.get("class")
    i_new = idx.get("new pno")

    pns, bps, clss, news = [], [], [], []
    for r in rows:
        pn = norm_pn(r[i_pno])
        if not pn:
            continue
        pns.append(pn)
        bps.append(pd.to_numeric(r[i_bp], errors="coerce"))
        clss.append(r[i_cls] if i_cls is not None else None)
        news.append(norm_pn(r[i_new]) if i_new is not None else pn)

    df = pd.DataFrame({"part_number": pns, "bp_new_jpy": bps,
                       "class_new_raw": clss, "newest_pn_new": news})
    # A PN must appear once; keep the first occurrence and count collisions.
    dup = int(df["part_number"].duplicated().sum())
    df = df.drop_duplicates("part_number").set_index("part_number")
    df.attrs["dup_pn_rows"] = dup
    df.attrs["rows_read"] = len(rows)
    return df


def load_prior_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prior base price, two vintages:
      bp_prior_revised  = CY2026 revision (PRICE CD 250912) -- single vintage
      bp_jpy_current    = the pre-revision price, for the timing sensitivity
    """
    sim = pd.read_parquet(DERIVED / "pricing_sim_pr00_l12m.parquet")
    sim = sim[sim["market"] == "PR00"][
        ["part_number", "qty_l12m", "bp_jpy_2025", "bp_jpy_2026", "price_class"]
    ].rename(columns={"qty_l12m": SENS_SIM_QTY})

    rev = pd.read_parquet(
        REVISION_CD, columns=["part_number", "bp_jpy_new", "bp_jpy_current"]
    ).drop_duplicates("part_number")

    prior = sim.merge(rev, on="part_number", how="outer")
    prior["bp_prior_revised"] = prior["bp_jpy_2026"].fillna(prior["bp_jpy_new"])
    prior["bp_prior_billed"] = prior["bp_jpy_current"]
    return prior.drop_duplicates("part_number").set_index("part_number"), sim


def load_dimension() -> pd.DataFrame:
    dim = pd.read_csv(DIST_DIM, dtype=str)
    dim["sold_to_sap"] = dim["sold_to_sap"].str.strip()
    dim["customer_name"] = dim["customer_name"].fillna("").str.strip()

    # The dimension carries no country column. Take it from the GPS distributor
    # table on distributor_code, latest year, so roll-ups stay consistent with
    # the rest of the workspace rather than being invented here.
    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
    gps = (gps.sort_values("year").drop_duplicates("distributor_code", keep="last")
           [["distributor_code", "country", "region"]]
           .rename(columns={"country": "gps_country", "region": "gps_region"}))
    dim = dim.merge(gps, on="distributor_code", how="left")
    dim["country"] = dim["gps_country"].fillna(dim["region"])
    return dim


def coverage_block(pn: pd.DataFrame) -> dict:
    """Matched vs total, at PN and at EUR/quantity level. Never silently drop."""
    tot_rows = int(len(pn))
    m_bp = pn["bp_new_jpy"].notna() & pn["bp_prior_revised"].notna()
    m_both = m_bp
    return {
        "pn_rows_l12m": tot_rows,
        "pn_rows_matched_new_bp": int(pn["bp_new_jpy"].notna().sum()),
        "pn_rows_missing_new_bp": int(pn["bp_new_jpy"].isna().sum()),
        "pn_rows_matched_prior_bp": int(pn["bp_prior_revised"].notna().sum()),
        "pn_rows_priced_both": int(m_both.sum()),
        "pn_rows_unpriced": int((~m_both).sum()),
        "qty_total": float(pn["billed_qty"].sum()),
        "qty_priced": float(pn.loc[m_both, "billed_qty"].sum()),
        "qty_coverage_pct": round(100 * float(pn.loc[m_both, "billed_qty"].sum())
                                  / float(pn["billed_qty"].sum()), 2),
        "eur_total": float(pn["net_sales_value"].sum()),
        "eur_priced": float(pn.loc[m_both, "net_sales_value"].sum()),
        "eur_coverage_pct": round(100 * float(pn.loc[m_both, "net_sales_value"].sum())
                                  / float(pn["net_sales_value"].sum()), 2),
    }


def main() -> int:
    DERIVED.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- inputs
    new = load_new_price_cd()
    prior, sim = load_prior_sources()
    dim = load_dimension()

    sf = pd.read_parquet(
        SALES_FACT,
        columns=["billing_date", "sold_to_sap", "sold_to", "part_number",
                 "description", "billed_qty", "net_sales_value"],
    )
    l12 = sf[(sf["billing_date"] >= L12M_START) & (sf["billing_date"] <= L12M_END)].copy()
    l12["part_number"] = l12["part_number"].astype(str).str.zfill(10)
    l12["cust"] = l12["sold_to_sap"].map(sap_code)

    # billed_qty x net_sales_value is additive; part_number is not, so aggregate
    # it away before the join rather than duplicating a row per PN.
    agg = (
        l12.groupby(["cust", "part_number"], as_index=False)
        .agg(billed_qty=("billed_qty", "sum"), net_sales_value=("net_sales_value", "sum"))
    )
    # The billed description is what the reader sees next to an excluded part
    # number. One line per part number is the normal case; where SAP carries more
    # than one wording they are joined rather than silently truncated.
    desc = (
        l12.groupby("part_number")["description"]
        .agg(lambda s: " / ".join(sorted({str(x).strip() for x in s
                                          if str(x).strip() and str(x).lower() != "nan"})))
        .rename("billed_description")
    )
    named = l12.groupby("cust")["sold_to"].agg(
        lambda s: sorted({str(x) for x in s if str(x).strip()})
    ).rename("sold_to_names")

    # ---------------------------------------------------------------- joins
    pn = agg.merge(new, left_on="part_number", right_index=True, how="left")
    pn = pn.merge(prior, left_on="part_number", right_index=True, how="left")
    pn = pn.merge(dim, left_on="cust", right_on="sold_to_sap", how="left")
    pn = pn.merge(desc, left_on="part_number", right_index=True, how="left")
    pn["sold_to_names"] = pn["cust"].map(named)

    # Scope. network_role is the reliable flag (scope is null on several rows):
    #  - network_db        -> the comparison set
    #  - direct_account    -> trades but is not a network distributor; listed apart
    #  - excluded_non_parts-> service fee / demurrage, not a priceable part
    #  - not_a_customer / excluded_entity -> dropped
    role = pn["network_role"].fillna("")
    scope = pn["scope"].fillna("")
    non_parts = (role == "excluded_non_parts") | (scope == "excluded_non_parts")
    pn["is_non_parts"] = non_parts
    pn["in_scope"] = (role == "network_db") & ~non_parts
    pn["is_direct_account"] = (role == "direct_account") & ~non_parts

    pn["delta_jpy"] = pn["bp_new_jpy"] - pn["bp_prior_revised"]
    pn["delta_pct"] = pn["bp_new_jpy"] / pn["bp_prior_revised"] - 1
    pn["value_jpy"] = pn["billed_qty"] * pn["delta_jpy"]
    pn["value_eur_step"] = pn["value_jpy"] / FX_JPY_PER_EUR
    pn["bp_prior_billed"] = pn["bp_prior_billed"]
    pn["bp_new_class"] = pn["class_new_raw"].map(map_cd_class)
    pn["class_mapped"] = pn["bp_new_class"].notna()

    # Why a billed line has no price on either side. A residual that is not
    # classified reads as an unexplained hole; these three cover nearly all
    # of it (checked 2026-09-17).
    #
    # The lubricant test is deliberately two-signal. The 05 prefix alone is a
    # guess: 26 part numbers in this window start with 05, and 19 of them are
    # bolts that DO carry a price on both sides. Requiring the billed
    # description to name a lubricant as well keeps the test honest.
    priced_both = pn["bp_new_jpy"].notna() & pn["bp_prior_revised"].notna()
    pn["unpriced_reason"] = None
    desc_u = pn["billed_description"].fillna("").str.upper()
    desc_is_lub = desc_u.str.contains("|".join(LUBRICANT_DESC_TOKENS), regex=True)
    pn05 = pn["part_number"].str.startswith("05")
    lub = pn05 & desc_is_lub
    # The former rule (prefix 05 only) is kept here purely so the build can prove
    # the tighter test changed nothing. A mismatch aborts the build.
    lub_former = pn05
    rebate = pn["part_number"].str.upper().str.contains("REBATE", na=False) | \
        ~pn["part_number"].str.fullmatch(r"\d{10}", na=False)
    pn.loc[~priced_both & rebate, "unpriced_reason"] = "rebate_or_non_part_admin"
    pn.loc[~priced_both & ~rebate & lub, "unpriced_reason"] = "lubricant_no_pr00_in_sap"
    pn.loc[~priced_both & ~rebate & ~lub, "unpriced_reason"] = "no_price_on_one_side"

    lub_former_rows = pn[~priced_both & ~rebate & lub_former]
    lub_new_rows = pn[~priced_both & ~rebate & lub]
    lub_rule = {
        "signal_1_prefix": "SAP part number starts with 05",
        "signal_2_description": "billed description names a lubricant: "
                                + ", ".join(LUBRICANT_DESC_TOKENS),
        "rows_former_prefix_rule": int(len(lub_former_rows)),
        "rows_new_two_signal_rule": int(len(lub_new_rows)),
        "pn_former_prefix_rule": int(lub_former_rows["part_number"].nunique()),
        "pn_new_two_signal_rule": int(lub_new_rows["part_number"].nunique()),
        "eur_new": round(float(lub_new_rows["net_sales_value"].sum()), 2),
        "qty_new": int(lub_new_rows["billed_qty"].sum()),
        "identical_to_former_rule": bool(
            set(lub_former_rows["part_number"]) == set(lub_new_rows["part_number"])
            and len(lub_former_rows) == len(lub_new_rows)
        ),
        "note": ("the tighter test is used because the 05 prefix alone would "
                 "classify any 05-numbered bolt as a lubricant"),
    }
    if not lub_rule["identical_to_former_rule"]:
        raise SystemExit(
            "lubricant rule changed the row set - aborting rather than moving a "
            f"published figure: {lub_rule}"
        )

    # ---------------------------------------------------------------- class map
    raw_counts = pn["class_new_raw"].astype(str).str.upper().value_counts()
    unmapped = sorted(
        k for k in raw_counts.index
        if k not in {"NAN", "NONE", ""} and map_cd_class(k) is None
    )
    class_map_note = {
        "raw_codes_seen": int(len(raw_counts)),
        "unmapped_raw_codes": unmapped,
        "unmapped_pn_rows": int(
            (~pn["class_mapped"] & pn["class_new_raw"].notna()).sum()
        ),
        "null_or_blank_class_rows": int(pn["class_new_raw"].isna().sum()),
        "method": "build_pricing_enquiry_tables.map_cd_class (last char, else first)",
    }

    # The class table only covers rows that HAVE a class. Rows without one are a
    # named residual, not a silent gap between the class total and the network
    # total (that gap is what the Checks sheet exists to catch).
    priced_mask = pn["bp_new_jpy"].notna() & pn["bp_prior_revised"].notna()
    noclass = pn[pn["in_scope"] & priced_mask & pn["bp_new_class"].isna()]
    class_coverage = {
        "priced_rows_with_class": int((pn["in_scope"] & priced_mask & pn["bp_new_class"].notna()).sum()),
        "priced_rows_without_class": int(len(noclass)),
        "step_eur_without_class": round(float(noclass["value_eur_step"].sum()), 2),
        "l12m_eur_without_class": round(float(noclass["net_sales_value"].sum()), 2),
        "note": "class-less rows are excluded from the class table by definition; named here",
    }

    # ---------------------------------------------------------------- roll-ups
    scoped = pn[pn["in_scope"]].copy()
    priced = scoped[scoped["bp_new_jpy"].notna() & scoped["bp_prior_revised"].notna()]

    # Non-part billing is excluded, not dropped: it is named and quantified so
    # the reader can see what the comparison does not cover.
    non_parts = pn[pn["is_non_parts"]]
    code_label = customer_labeler(pn)

    non_parts_block = {
        "rows": int(len(non_parts)),
        "l12m_billed_eur": round(float(non_parts["net_sales_value"].sum()), 2),
        "customers": sorted(non_parts["cust"].dropna().unique().tolist()),
        "customers_named": [
            {"code": str(c), "label": code_label(str(c))}
            for c in sorted(non_parts["cust"].dropna().unique().tolist())
        ],
        "note": "service fee / demurrage, not a priceable part (audit Check 1 exclusion)",
    }
    non_parts_block.update(EXCLUDED_COPY_OUT_OF_SCOPE["non_parts"])

    def wavg(frame: pd.DataFrame):
        w = frame["billed_qty"]
        new_v = (w * frame["bp_new_jpy"]).sum()
        prior_v = (w * frame["bp_prior_revised"]).sum()
        if prior_v == 0 or not np.isfinite(prior_v):
            return np.nan, np.nan, np.nan
        return (new_v / prior_v - 1), new_v, prior_v

    def row(label: str, level: str, frame: pd.DataFrame, cust: str | None = None) -> dict:
        p = frame[frame["bp_new_jpy"].notna() & frame["bp_prior_revised"].notna()]
        pct, new_v, prior_v = wavg(p)
        all_qty = frame["billed_qty"].sum()
        p_qty = p["billed_qty"].sum()
        return {
            "level": level,
            "customer_code": cust,
            "label": label,
            "weighted_increase_pct": None if pd.isna(pct) else round(100 * pct, 4),
            "value_step_eur": round(float(p["value_eur_step"].sum()), 2),
            "revenue_prior_eur": round(float(prior_v / FX_JPY_PER_EUR), 2),
            "revenue_new_eur": round(float(new_v / FX_JPY_PER_EUR), 2),
            "l12m_billed_eur": round(float(frame["net_sales_value"].sum()), 2),
            "l12m_billed_qty": int(all_qty),
            "priced_qty": int(p_qty),
            "qty_coverage_pct": round(100 * p_qty / all_qty, 2) if all_qty else None,
            "n_pn_priced": int(p["part_number"].nunique()),
            "n_pn_total": int(frame["part_number"].nunique()),
        }

    rows: list[dict] = []
    rows.append(row("Network (all in-scope customers)", "network", scoped))

    cust_rows = []
    for cust, frame in scoped.groupby("cust", sort=False):
        nm = ", ".join(frame["sold_to_names"].dropna().iloc[0]) if frame["sold_to_names"].notna().any() else ""
        label = frame["distributor_code"].dropna().iloc[0] if frame["distributor_code"].notna().any() else (nm or cust)
        cust_rows.append(row(f"{cust} - {label}", "customer", frame, cust))
    cust_rows.sort(key=lambda r: -r["l12m_billed_eur"])
    rows.extend(cust_rows)

    # Distributor roll-up. Several sold-to codes settle against one distributor
    # (Germany 2516+601, Portugal 519+92, Denmark 2027+2751), so the sold-to view
    # alone double-lists a country. This is the level a price conversation is
    # actually held at. Israel stays two rows: 1797=UMI, 1799=UTI are separate
    # distributor codes and are never merged.
    scoped = scoped.copy()
    scoped["dist_key"] = scoped["distributor_code"].where(
        scoped["distributor_code"].notna() & (scoped["distributor_code"] != ""),
        scoped["country"].fillna(scoped["cust"]),
    )
    dist_rows = []
    for key, frame in scoped.groupby("dist_key", sort=False):
        dist_rows.append(row(str(key), "distributor", frame))
    dist_rows.sort(key=lambda r: -r["l12m_billed_eur"])
    rows.extend(dist_rows)

    # Israel: two codes, never one blended number.
    il = scoped[scoped["cust"].isin(["1797", "1799"])]
    for cust in ["1797", "1799"]:
        f = il[il["cust"] == cust]
        if len(f):
            rows.append(row(f"{cust} - {'UMI' if cust == '1797' else 'UTI'} (Israel)",
                            "israel", f, cust))
    if len(il):
        rows.append(row("Israel (1797 + 1799)", "israel_combined", il))

    for country, frame in scoped.groupby("country", sort=False):
        rows.append(row(f"{country}", "country", frame))

    cust_df = pd.DataFrame(rows)

    # ------------------------------------------------- unpriced bucket, named
    # "Unmatched is reported as a named bucket, never silently dropped."
    # A bucket that shows only a total is not a finding: the reader cannot tell
    # what it is or whose it is. Each bucket therefore carries its own customer
    # concentration, by name, and the lubricant bucket carries its part numbers.
    unpriced = scoped[~(scoped["bp_new_jpy"].notna() & scoped["bp_prior_revised"].notna())]
    customer_label = customer_labeler(pn)

    # Lubricant detail: the part numbers themselves, so the excluded euro is
    # attributable line by line rather than as an anonymous lump.
    lub_detail = []
    for pnum, f in unpriced[unpriced["unpriced_reason"] == "lubricant_no_pr00_in_sap"] \
            .groupby("part_number"):
        lub_detail.append({
            "pn": str(pnum),
            "description": str(f["billed_description"].iloc[0] or ""),
            "qty": int(f["billed_qty"].sum()),
            "eur": round(float(f["net_sales_value"].sum()), 2),
            "customers": sorted({str(c) for c in f["cust"].unique()}),
        })
    lub_detail.sort(key=lambda d: -d["eur"])

    unp_blocks = []
    for bucket, f in unpriced.groupby("unpriced_reason", dropna=False):
        by_cust = (f.groupby("cust")["net_sales_value"].sum()
                   .sort_values(ascending=False))
        total = float(f["net_sales_value"].sum())
        key = str(bucket)
        blurb = EXCLUDED_COPY.get(key, {})
        block = {
            "bucket": key,
            "what": blurb.get("what") or key.replace("_", " "),
            "why": blurb.get("why", ""),
            "rows": int(len(f)),
            "l12m_billed_eur": round(total, 2),
            "l12m_qty": int(f["billed_qty"].sum()),
            "pct_of_unpriced_eur": round(100 * total
                                         / float(unpriced["net_sales_value"].sum()), 1) if len(unpriced) else None,
            "rows_new_price_only": int((f["bp_new_jpy"].notna()
                                        & f["bp_prior_revised"].isna()).sum()),
            "rows_prior_price_only": int((f["bp_new_jpy"].isna()
                                          & f["bp_prior_revised"].notna()).sum()),
            "rows_no_price_either_side": int((f["bp_new_jpy"].isna()
                                              & f["bp_prior_revised"].isna()).sum()),
            "top_customers": by_cust.head(5).round(0).to_dict(),
            "n_customers": int(by_cust.size),
            "top_customer_name": customer_label(str(by_cust.index[0])) if len(by_cust) else None,
            "top_customer_share_pct": round(100 * float(by_cust.iloc[0]) / total, 1)
            if len(by_cust) and total else None,
            "top_customers_named": [
                {"code": str(code), "label": customer_label(str(code)),
                 "eur": round(float(v), 2),
                 "share_pct": round(100 * float(v) / total, 1) if total else None}
                for code, v in by_cust.head(5).items()
            ],
        }
        if str(bucket) == "lubricant_no_pr00_in_sap":
            block["pn_detail"] = lub_detail
        unp_blocks.append(block)
    unp_blocks.sort(key=lambda b: -b["l12m_billed_eur"])
    unpriced_block = {
        "rows": int(len(unpriced)),
        "l12m_billed_eur": round(float(unpriced["net_sales_value"].sum()), 2),
        "l12m_qty": int(unpriced["billed_qty"].sum()),
        "buckets": unp_blocks,
        "note": ("priced_qty excludes these; they are the residual of the adjusted "
                 "PR00 coverage, not a pricing decision"),
    }

    # ------------------------------------------------------------ sensitivity
    # idx2: the L12M window opens before the CY2026 revision. Weighting the
    # pre-revision months by the price actually in force is an approximation
    # (billing carries no price), so it is a bound, not an estimate.
    pre = scoped[scoped["part_number"].notna()].copy()
    pre["delta_billed"] = pre["bp_new_jpy"] - pre["bp_prior_billed"]
    pre["value_eur_billed_basis"] = pre["billed_qty"] * pre["delta_billed"] / FX_JPY_PER_EUR
    sens_prior_vintage = {
        "note": ("L12M opens before the CY2026 revision; weighting the whole year "
                 "on the revision is the file-supported basis. The billed-vintage "
                 "figure below is an approximation bound, not a measurement."),
        "revision_effective": REVISION_EFFECTIVE.date().isoformat(),
        "pre_revision_days_in_window": int((REVISION_EFFECTIVE - L12M_START).days),
        "value_step_eur_revised_basis": round(float(scoped["value_eur_step"].sum()), 2),
        "value_step_eur_billed_basis": round(float(pre["value_eur_billed_basis"].sum()), 2),
    }

    # sim-quantity weighting, to show billing is the weight that matters.
    # Paired like-for-like: both bases are computed on the SAME rows (those that
    # carry a simulation quantity), so the difference is the weight base alone
    # and not a different population. The workbook computes the full billed base
    # separately, on every priced row.
    simw = priced[priced[SENS_SIM_QTY].notna() & (priced[SENS_SIM_QTY] > 0)]
    if len(simw):
        pct_sim = (float((simw[SENS_SIM_QTY] * simw["bp_new_jpy"]).sum())
                   / float((simw[SENS_SIM_QTY] * simw["bp_prior_revised"]).sum()) - 1)
        pct_bill_paired = (float((simw["billed_qty"] * simw["bp_new_jpy"]).sum())
                           / float((simw["billed_qty"] * simw["bp_prior_revised"]).sum()) - 1)
        pct_bill_all = (float((priced["billed_qty"] * priced["bp_new_jpy"]).sum())
                        / float((priced["billed_qty"] * priced["bp_prior_revised"]).sum()) - 1)
        sens_weight = {
            "weighted_increase_pct_billing_qty": round(100 * pct_bill_all, 4),
            "weighted_increase_pct_sim_l12m_qty": round(100 * pct_sim, 4),
            "weighted_increase_pct_billing_qty_paired_subset": round(100 * pct_bill_paired, 4),
            "paired_pn_rows": int(len(simw)),
            "priced_pn_rows": int(len(priced)),
            "note": ("the simulation-vs-billing comparison is quoted on the paired rows only, "
                     "so both bases cover the same population; the workbook headline is the "
                     "all-priced-rows billing figure"),
        }
    else:
        sens_weight = {"note": "no overlap with simulation quantity"}

    # ---------------------------------------------------------------- outputs
    pn_out = pn[[
        "cust", "sold_to_names", "distributor_code", "gps_db_label", "country", "region",        "scope", "network_role", "in_scope", "is_non_parts", "is_direct_account",
        "part_number", "billed_description", "billed_qty", "net_sales_value",
        "class_new_raw", "bp_new_class", "class_mapped", "unpriced_reason",
        "bp_new_jpy", "bp_prior_revised", "bp_prior_billed", "delta_jpy", "delta_pct",
        "value_jpy", "value_eur_step",
    ]].rename(columns={"cust": "customer_code"})
    pn_out.to_csv(OUT_PN, index=False, encoding="utf-8-sig")
    cust_df.to_csv(OUT_CUST, index=False, encoding="utf-8-sig")

    meta = {
        "generated": date.today().isoformat(),
        "purpose": ("Step 1 - sales-weighted base-price comparison of the new PRICE CD "
                    "against the prior base price. No FX applied to prices, no list change, "
                    "no allocation run."),
        "window": {"start": L12M_START.date().isoformat(), "end": L12M_END.date().isoformat(),
                   "basis": "last 12 months of available billing (sales_fact ends 2026-06-30)"},
        "fx": {"jpy_per_eur": FX_JPY_PER_EUR, "as_of": FX_AS_OF,
               "use": "values the JPY step in EUR only; never mixed into a percentage"},
        "inputs": {
            "new_price_cd": {"path": str(NEW_PRICE_CD.relative_to(ISZE)),
                             "sha256": sha256(NEW_PRICE_CD),
                             "rows_read": new.attrs.get("rows_read"),
                             "duplicate_pn_rows_dropped": new.attrs.get("dup_pn_rows")},
            "simulation": {"path": str(SIM_XLSX.relative_to(ISZE)),
                           "sha256": sha256(SIM_XLSX),
                           "note": "byte-identical to the landed copy; used for l12m qty only"},
            "sales_fact": {"path": str(SALES_FACT.relative_to(ISZE))},
            "prior_revision": {"path": str(REVISION_CD.relative_to(ISZE)),
                               "source_sheet": "PRICE CD 250912 (CY2026 revision)"},
            "customer_dimension": {"path": str(DIST_DIM.relative_to(ISZE))},
        },
        "coverage": coverage_block(scoped),
        "coverage_including_out_of_scope": coverage_block(pn),
        "unpriced_bucket": unpriced_block,
        "lubricant_rule": lub_rule,
        "non_parts_excluded": non_parts_block,
        "direct_account_excluded": {
            "rows": int(pn["is_direct_account"].sum()),
            "l12m_billed_eur": round(float(pn.loc[pn["is_direct_account"], "net_sales_value"].sum()), 2),
            "customers": sorted(pn.loc[pn["is_direct_account"], "cust"].dropna().unique().tolist()),
            "customers_named": [
                {"code": str(c), "label": code_label(str(c))}
                for c in sorted(pn.loc[pn["is_direct_account"], "cust"].dropna().unique().tolist())
            ],
            "note": "trades but is not a network distributor",
            **EXCLUDED_COPY_OUT_OF_SCOPE["direct_account"],
        },
        "class_mapping": class_map_note,
        "class_coverage": class_coverage,
        "sensitivity": {"prior_vintage": sens_prior_vintage, "weight_base": sens_weight},
        "caveats": [
            "sold_to_sap is the customer key. The sold_to NAME column is unusable for "
            "Israel: it was relabelled 2026-04-01 and now reads UNIVERSAL MOTORS ISRAEL "
            "LTD for both 1797 and 1799.",
            "Israel is reported as 1797 (UMI) and 1799 (UTI) separately plus a combined "
            "row. Never one blended Israel figure on its own.",
            "The % is a base-price move, not a revenue or margin move. No elasticity "
            "coefficient is applied (Spec C1: elasticity is not quotable at ISZE->DB).",
            "Unpriced part numbers are reported as a named bucket, not dropped.",
        ],
        "outputs": [str(OUT_PN.relative_to(ISZE)), str(OUT_CUST.relative_to(ISZE))],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # ---------------------------------------------------------------- console
    print("=" * 78)
    print("BASE-PRICE IMPACT, WEIGHTED BY L12M SALES  "
          f"({L12M_START.date()} to {L12M_END.date()})")
    print("=" * 78)
    net = cust_df[cust_df["level"] == "network"].iloc[0]
    print(f"NETWORK weighted increase : {net['weighted_increase_pct']:.4f}%")
    print(f"  euro value of the step  : EUR {net['value_step_eur']:,.0f} "
          f"(at {FX_JPY_PER_EUR} JPY/EUR)")
    print(f"  coverage                : {net['qty_coverage_pct']:.1f}% of quantity, "
          f"{meta['coverage']['eur_coverage_pct']:.1f}% of L12M value")
    print()
    print("ISRAEL (two codes, never blended):")
    for _, r in cust_df[cust_df["level"] == "israel"].iterrows():
        print(f"  {r['label']:<28} {r['weighted_increase_pct']:>7.4f}%  "
              f"step EUR {r['value_step_eur']:>12,.0f}  "
              f"L12M EUR {r['l12m_billed_eur']:>12,.0f}")
    print()
    print("TOP CUSTOMERS BY L12M VALUE:")
    cc = cust_df[cust_df["level"] == "customer"].head(20)
    for _, r in cc.iterrows():
        print(f"  {r['label']:<42} {r['weighted_increase_pct']:>7.4f}%  "
              f"step EUR {r['value_step_eur']:>12,.0f}  "
              f"L12M EUR {r['l12m_billed_eur']:>12,.0f}  "
              f"cov {r['qty_coverage_pct']:>5.1f}%")
    print()
    print("DISTRIBUTOR LEVEL (sold-to codes rolled up):")
    dd = cust_df[cust_df["level"] == "distributor"]
    for _, r in dd.iterrows():
        print(f"  {r['label']:<24} {r['weighted_increase_pct']:>7.4f}%  "
              f"step EUR {r['value_step_eur']:>12,.0f}  "
              f"L12M EUR {r['l12m_billed_eur']:>12,.0f}  "
              f"cov {r['qty_coverage_pct']:>5.1f}%")
    print()
    print("weight-base sensitivity:", sens_weight)
    print("class mapping:", json.dumps(class_map_note, indent=2))
    print("lubricant rule:", json.dumps(lub_rule, indent=2))
    print()
    print("wrote:", OUT_PN.name, OUT_CUST.name, OUT_META.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
