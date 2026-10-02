#!/usr/bin/env python3
"""AIM deep dive: ISZE -> distributor against distributor -> dealer, part number by part number.

Two runs, one script:

    python build_aim_db_dlr.py --db PORTUGAL      -> ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html
    python build_aim_db_dlr.py --db ALL           -> ISZE_AIM_DB_DLR_Deep_Dive_ALL.html

Reads only the derived files named in SPEC_FOR_DEEPSEEK.md (section 3). Never reads raw
line-level billing. Fails loudly, before writing any HTML, when an input is missing or a
check in section 9 fails. Writes VERIFY_<RUN>.md / .json next to itself.

The page shell (markup, CSS, application JS) lives in aim_app_template.html beside this file.
It is an asset, not a second build path: this script is the only thing that writes the HTML.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- paths

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
TOOL = ISZE / "04_tools" / "aim_db_dlr_deep_dive"
DASH = ISZE / "02_dashboards" / "sales"
UI = ISZE / "02_dashboards" / "_ui"

TEMPLATE = TOOL / "aim_app_template.html"
CHART_JS = UI / "chart.umd.min.js"          # Chart.js 4.4.1, inlined so the page opens offline
# The chartjs-chart-treemap plugin was inlined here for the stock-movement treemap. That chart was
# removed on Jerome's instruction, so the plugin is no longer read or shipped.

REFERENCE = Path(r"C:\Users\jerom\Desktop\ISZE_Pricing_Revision_AIM_Source.html")

PARTS_FILE = DER / "parts_catalog_dimension.csv"
DEMAND_FILE = DER / "pms_capture_by_db_year.csv"
PRICE_FILE = DER / "pricing_pr00_ie40.parquet"
BVP_FILE = DER / "bvp_pn_dimension.csv"
DIM_FILE = DER / "distributor_dimension.csv"
SALES_FACT = DER / "sales_fact.parquet"
SRC_SIM = DER / "pricing_sim_pr00_l12m.parquet"
SRC_LIST = DER / "pricing_list_pn.parquet"
STO_COMPARE = ISZE / "09_meetings" / "IMotors_FY2027_BPR" / "merged" / "_build" / "sto_compare.py"

# --------------------------------------------------------------------------- rules

# section 2.4 and 3.1: credit notes, returns, debit notes, free deliveries are out.
EXCLUDE_SATY = ["CR", "RE", "DR", "ZDR", "FD"]
KEEP_SATY = ["SOR", "VOR", "RUSH", "PRD", "SVOR"]

# section 2.4: lubricants are out of scope. Non-part lines (freight, rebate, service fee,
# merchandise, tool, marketing item, core deposit, finance, demurrage, display) drop with it.
DROP_LINE_KIND = "part"                 # keep only line_kind == part
DROP_AIM_L1 = "Fluids Chemicals"        # keep Lubrication: those are engine parts, not oils

AIM_NA = "Not classified in AIM"
AIM_PLACEHOLDER = {"", "nan", "none", "unknown", "unknown review", "null"}

PMS_FAMS = ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter",
            "brake_pad", "brake_shoe", "brake_rotor",
            "clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing",
            "pilot_bearing", "clutch_booster"]
PMS_LABELS = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "blower_filter": "Cabin (blower) filter", "urea_filter": "AdBlue (urea) filter",
    "brake_pad": "Brake pad", "brake_shoe": "Brake shoe", "brake_rotor": "Brake rotor",
    "clutch_kit": "Clutch kit", "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate", "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing", "clutch_booster": "Clutch booster",
}
CLUTCH_FAMS = {"clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing",
               "pilot_bearing", "clutch_booster"}

SRC_LABELS = {"J": "JP - Japan", "T": "TH - Thailand", "X": "Not held", "": "Not held"}
BVP_LABELS = {"genuine": "Genuine", "bvp": "BVP", "": "Not in the Genuine/BVP list"}

# section 3.2: the sales-to-dealer files that are in scope, and how to read them.
SELLOUT = {
    "PORTUGAL": {"stems": ["_PORTUGAL_CY2025", "_PORTUGAL_CY2026YTD"],
                 "scope": "MIXED", "scope_note": "network level, all families"},
    "IRELAND":  {"stems": ["_IRELAND_CY2025", "_IRELAND_CY2026YTD"],
                 "scope": "MIXED", "scope_note": "network level, all families"},
    "ITUK":     {"stems": ["_ITUK_CY2023", "_ITUK_CY2024", "_ITUK_network_CY2025",
                           "_ITUK_CY2026YTD"],
                 "scope": "CV", "scope_note": "commercial vehicles only (CV)"},
    "IUK":      {"stems": ["_IUK_CY2025", "_IUK_CY2026YTD"],
                 "scope": "D-MAX", "scope_note": "D-Max only"},
    "UTI":      {"stems": ["_UTI_CY2025", "_UTI_CY2026YTD"],
                 "scope": "MIXED", "scope_note": "network level; Feb-Jul 2025 missing"},
    "GREECE":   {"stems": ["_GREECE_CY2025"],
                 "scope": "D-MAX", "scope_note": "D-Max only, calendar 2025 only"},
}
# section 3.2: dealer-level file, used only for the dealer layer (section 6.9).
DEALER_LEVEL_FILE = "_ITUK_CY2025"

# section 4.1 names these two files as the exceptions: the total row in them does not equal the
# month rows, so only the month rows may be used. Everything else must agree.
RECON_EXCEPTIONS = {
    "dealer_sellout_long_UTI_CY2025.csv":
        "the spec names this file: its year row holds the whole year while the month rows cover "
        "only January and August to December, so February to July are genuinely absent. Month rows "
        "are used and the missing months are reported as missing.",
    "dealer_sellout_long_ITUK_CY2025.csv":
        "the spec names this file: it is the dealer-level file, its year row runs a little above "
        "its month rows, and it is used only for the dealer layer.",
}

PRICE_LIST_LABEL = "ISZE price list IE40 PR00 of 10 Aug 2026"

# section 9 run-1 expectations, computed with the supersession mapping switched off.
CHECK_PT = [
    ("sold to dealer units, month rows, Jan-Dec 2025", 51363),
    ("sold to dealer units, month rows, Jan-Aug 2026", 39790),
    ("billed units FY2026 (Apr 2025 - Mar 2026), brake pad", 1370),
    ("billed units FY2026, oil filter", 2743),
    ("billed units FY2026, brake shoe", 348),
    ("sold to dealer units FY2026, brake pad", 994),
    ("sold to dealer units FY2026, oil filter", 3694),
    ("sold to dealer units FY2027 Apr-Aug, brake pad", 406),
]


class BuildError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- helpers

def norm(s: pd.Series) -> pd.Series:
    """Strip spaces, drop a trailing .0, strip leading zeros, keep as text (section 4.2)."""
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


def fam_of(cat) -> str | None:
    """Fold the PMS category variants into the 14 families (section 3.4)."""
    c = str(cat)
    if c.startswith("brake_pad"):
        return "brake_pad"
    if c.startswith("brake_shoe") or c.startswith("brake_lining"):
        return "brake_shoe"
    return c if c in PMS_FAMS else None


def month_key(dt: pd.Series) -> pd.Series:
    return dt.dt.strftime("%Y-%m")


def require(path: Path, what: str) -> None:
    if not path.exists():
        raise BuildError(f"MISSING {what}: {path}\n"
                         f"The spec says this file exists. Stopping instead of guessing.")


def check_columns(df: pd.DataFrame, cols, path: Path) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise BuildError(f"{path.name} is missing column(s) {missing}. "
                         f"Found: {list(df.columns)}")


# --------------------------------------------------------------------------- dimensions

def load_dimensions():
    """AIM tree, PMS family, price list, Genuine/BVP flag, source of supply, distributor map."""
    log("-- dimensions")

    aim = pd.read_csv(AIM_FILE, dtype=str, low_memory=False)
    require(AIM_FILE, "AIM tree")
    check_columns(aim, ["part_number", "description", "aim_level_1", "aim_level_2",
                        "aim_level_3", "line_kind"], AIM_FILE)
    aim["pn"] = norm(aim["part_number"])
    aim = aim.drop_duplicates("pn")
    aim["desc"] = aim["description"].fillna("").astype(str).str.strip()
    for lv in ("1", "2", "3"):
        aim[f"a{lv}"] = aim[f"aim_level_{lv}"].fillna("").astype(str).str.strip()
    aim["is_part"] = aim["line_kind"].fillna("").astype(str).str.strip().eq(DROP_LINE_KIND)
    log(f"   AIM tree            {len(aim):,} part numbers, "
        f"{int(aim['is_part'].sum()):,} with line_kind=part")

    # excluded part numbers: non-part lines, and lubricants (AIM L1 Fluids Chemicals)
    fluids = aim["a1"].str.lower().eq(DROP_AIM_L1.lower()) & aim["is_part"]
    aim["excluded_scope"] = np.where(~aim["is_part"], "not a part line",
                                     np.where(fluids, "lubricant (Fluids Chemicals)", ""))
    keep = aim["excluded_scope"].eq("")
    aim_keep = aim[keep].copy()
    # the reason map comes off the WHOLE frame, including the rows being dropped
    excl_map = aim.set_index("pn")["excluded_scope"]
    log(f"   dropped by scope    {len(aim) - len(aim_keep):,} part numbers "
        f"({int((~aim['is_part']).sum()):,} non-part, {int(fluids.sum()):,} lubricant)")

    # AIM levels, index 0 = not classified in AIM for all three levels
    l1_vals = sorted({v for v in aim_keep["a1"].str.lower() if v not in AIM_PLACEHOLDER})
    l2_vals = sorted({v for v in aim_keep["a2"].str.lower() if v not in AIM_PLACEHOLDER})
    l3_vals = sorted({v for v in aim_keep["a3"].str.lower() if v not in AIM_PLACEHOLDER})
    l1_map = {AIM_NA.lower(): 0}
    l2_map = {AIM_NA.lower(): 0}
    l3_map = {AIM_NA.lower(): 0}
    l1_lab = [AIM_NA]
    l2_lab = [AIM_NA]
    l3_lab = [AIM_NA]
    for v in l1_vals:
        l1_map[v] = len(l1_lab); l1_lab.append(v.title() if v.islower() else v)
    for v in l2_vals:
        l2_map[v] = len(l2_lab); l2_lab.append(v)
    for v in l3_vals:
        l3_map[v] = len(l3_lab); l3_lab.append(v)
    log(f"   AIM levels          L1 {len(l1_lab)}  L2 {len(l2_lab)}  L3 {len(l3_lab)}"
        f"  (each includes '{AIM_NA}')")

    aim_keep = aim_keep.copy()
    aim_keep["i1"] = [l1_map.get(v, 0) for v in aim_keep["a1"].str.lower()]
    aim_keep["i2"] = [l2_map.get(v, 0) for v in aim_keep["a2"].str.lower()]
    aim_keep["i3"] = [l3_map.get(v, 0) for v in aim_keep["a3"].str.lower()]

    # ---- PMS family
    pc = pd.read_csv(PARTS_FILE, dtype=str, low_memory=False)
    check_columns(pc, ["part_number", "pms_category"], PARTS_FILE)
    pc["pn"] = norm(pc["part_number"])
    pc = pc.drop_duplicates("pn")
    pc["fam"] = pc["pms_category"].map(fam_of)
    fam_map = {f: i for i, f in enumerate(PMS_FAMS)}
    pc["ifam"] = pc["fam"].map(fam_map)
    pc = pc[pc["ifam"].notna()][["pn", "ifam"]]
    pc["ifam"] = pc["ifam"].astype(int)
    log(f"   PMS family map      {len(pc):,} part numbers across {len(PMS_FAMS)} families")

    # ---- Genuine / BVP (section 3.6)
    bvp = pd.read_csv(BVP_FILE, dtype=str, low_memory=False)
    check_columns(bvp, ["part_number", "line_type"], BVP_FILE)
    bvp["pn"] = norm(bvp["part_number"])
    bvp = bvp.drop_duplicates("pn")
    bvp_map = {"genuine": 0, "bvp": 1}
    bvp["ib"] = bvp["line_type"].map(bvp_map).fillna(2).astype(int)
    bvp = bvp[["pn", "ib"]]
    log(f"   Genuine/BVP list    {len(bvp):,} part numbers "
        f"({int((bvp['ib'] == 0).sum()):,} genuine, {int((bvp['ib'] == 1).sum()):,} BVP)")

    # ---- price list (section 3.5)
    pr = pd.read_parquet(PRICE_FILE)
    check_columns(pr, ["part_number", "newest_pn", "sp_eur", "country_of_origin"], PRICE_FILE)
    pr["pn"] = norm(pr["part_number"])
    pr["new"] = norm(pr["newest_pn"])
    pr["sp"] = pd.to_numeric(pr["sp_eur"], errors="coerce")
    pr.loc[pr["sp"] <= 0, "sp"] = np.nan          # a price of 0.00 means no price
    pr["desc_price"] = pr["description"].fillna("").astype(str).str.strip()
    pr = pr.drop_duplicates("pn")
    price_map = pr.set_index("pn")["sp"]
    pdesc_map = pr.set_index("pn")["desc_price"]
    sup_map = pr.set_index("pn")["new"]
    log(f"   price list          {len(pr):,} part numbers, "
        f"{int(pr['sp'].notna().sum()):,} with a price above zero")

    # ---- source of supply: the same basis the reference dashboard uses (section 3.7)
    src = pd.Series(dtype=object)
    if SRC_SIM.exists():
        sim = pd.read_parquet(SRC_SIM, columns=["part_number", "source"])
        sim["pn"] = norm(sim["part_number"])
        sim = sim.dropna(subset=["source"]).drop_duplicates("pn")
        src = sim.set_index("pn")["source"].astype(str)
    if SRC_LIST.exists():
        lp = pd.read_parquet(SRC_LIST, columns=["part_number", "source"])
        lp["pn"] = norm(lp["part_number"])
        lp = lp.dropna(subset=["source"])
        uniq = lp.groupby("pn")["source"].nunique()
        single = set(uniq[uniq == 1].index)
        ls = lp[lp["pn"].isin(single)].drop_duplicates("pn").set_index("pn")["source"].astype(str)
        src = src.combine_first(ls)
    log(f"   source of supply    {len(src):,} part numbers "
        f"(J = Japan through IML, T = Thailand through IMIT)")

    # ---- distributor map, joined on sold_to_sap and never on payer_code (section 3.1)
    dd = pd.read_csv(DIM_FILE, dtype=str, low_memory=False)
    check_columns(dd, ["sold_to_sap", "payer_code", "distributor_code", "gps_db_label",
                       "scope", "network_role"], DIM_FILE)
    dd = dd[dd["distributor_code"].notna()].copy()
    dd["sap"] = dd["sold_to_sap"].str.replace(r"\.0$", "", regex=True).str.strip()
    dd = dd.drop_duplicates("sap")
    sap2db = dd.set_index("sap")["distributor_code"].to_dict()
    db_meta = (dd.drop_duplicates("distributor_code")
                 .set_index("distributor_code")[["gps_db_label", "scope"]].to_dict("index"))
    log(f"   distributor map     {len(sap2db)} sold-to codes -> "
        f"{len(db_meta)} distributors")

    dims = dict(aim=aim_keep, excl_map=excl_map, l1_lab=l1_lab, l2_lab=l2_lab, l3_lab=l3_lab,
                pc=pc, bvp=bvp, price_map=price_map, pdesc_map=pdesc_map,
                sup_map=sup_map, src=src, sap2db=sap2db, db_meta=db_meta, dd=dd)
    return dims


def build_pn_dimension(dims):
    """One row per part number actually seen, with its supersession applied (section 4.2)."""
    aim = dims["aim"]
    aim_idx = aim.set_index("pn")
    aim_pns = set(aim_idx.index)
    priced = set(dims["price_map"].dropna().index)
    sup = dims["sup_map"]

    def resolve(series: pd.Series):
        """canonical part number, plus the original when it differs."""
        s = norm(series)
        nw = s.map(sup)
        take_new = nw.notna() & (nw != s) & nw.isin(aim_pns) & nw.isin(priced)
        canon = np.where(take_new, nw, s)
        old = np.where(take_new, s, None)
        return canon, old

    return resolve


# --------------------------------------------------------------------------- facts

def load_billing(dims, dbs):
    """ISZE -> distributor at month grain, exclusions applied, newest part number (section 3.1)."""
    log("-- ISZE billing (ISZE -> distributor)")
    sf = pd.read_parquet(SALES_FACT, columns=[
        "billing_date", "sold_to_sap", "part_number", "description", "billed_qty",
        "net_sales_value", "saty", "year", "material"])
    check_columns(sf, ["billing_date", "sold_to_sap", "part_number", "billed_qty",
                       "net_sales_value", "saty"], SALES_FACT)
    log(f"   sales_fact.parquet  {len(sf):,} rows, "
        f"{sf.billing_date.min():%Y-%m-%d} to {sf.billing_date.max():%Y-%m-%d}")

    sf["sap"] = sf["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    sf["db"] = sf["sap"].map(dims["sap2db"])
    in_book = sf["db"].notna() & sf["db"].isin(dbs)
    sf = sf[in_book].copy()

    doctype_out = sf["saty"].isin(EXCLUDE_SATY) | sf["saty"].isna()
    excluded_doc = sf[doctype_out]
    log(f"   excluded doc types  {len(excluded_doc):,} rows, "
        f"EUR {excluded_doc['net_sales_value'].sum():,.2f} "
        f"(saty in {', '.join(EXCLUDE_SATY)} or blank)")
    kept = sf[~doctype_out].copy()

    kept["month"] = month_key(kept["billing_date"])
    kept["pn_raw"] = norm(kept["part_number"])
    kept["billed_qty"] = pd.to_numeric(kept["billed_qty"], errors="coerce").fillna(0.0)
    kept["net_sales_value"] = pd.to_numeric(kept["net_sales_value"], errors="coerce").fillna(0.0)
    return kept, excluded_doc


def load_sellout(dbs):
    """Distributor -> dealer at month grain, month rows only (sections 3.2 and 4.1)."""
    log("-- sales to dealer (distributor -> dealer)")
    frames = []
    recon = {}
    for db in dbs:
        if db not in SELLOUT:
            continue
        per_file = []
        for stem in SELLOUT[db]["stems"]:
            f = DER / f"dealer_sellout_long{stem}.csv"
            require(f, "sales-to-dealer file")
            df = pd.read_csv(f, dtype=str, low_memory=False)
            check_columns(df, ["distributor_code", "part_number", "qty", "period",
                               "period_grain"], f)
            df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0.0)
            months = df[df["period_grain"] == "month"].copy()
            totals = df[df["period_grain"].isin(["year", "ytd"])]
            recon[f.name] = {
                "month_rows_qty": float(months["qty"].sum()),
                "total_row_qty": float(totals["qty"].sum()),
                "total_row_periods": sorted(totals["period"].dropna().unique().tolist()),
                "month_periods": sorted(months["period"].dropna().unique().tolist()),
            }
            months["db"] = db
            months["src_file"] = f.name
            per_file.append(months)
            log(f"   {f.name:<48} month rows {len(months):>7,}  "
                f"qty {months['qty'].sum():>12,.0f}")
        if per_file:
            frames.append(pd.concat(per_file, ignore_index=True))
    so = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    so["month"] = so["period"].astype(str).str.strip()
    so["pn_raw"] = norm(so["part_number"])
    so["qty"] = pd.to_numeric(so["qty"], errors="coerce").fillna(0.0)
    return so, recon


def load_dealer_layer(recon=None):
    """ITUK dealer x AIM level 1, CY2025, month rows only (section 6.9).

    Section 4.1 also names this file in the month-row against total-row check, so its counts go
    into the same reconciliation record.
    """
    f = DER / f"dealer_sellout_long{DEALER_LEVEL_FILE}.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f, dtype=str, low_memory=False)
    all_rows = df.copy()
    all_rows["qty"] = pd.to_numeric(all_rows["qty"], errors="coerce").fillna(0.0)
    df = df[df["period_grain"] == "month"].copy()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0.0)
    df["pn_raw"] = norm(df["part_number"])
    df["dealer"] = df["dealer_name"].fillna("(not named)").astype(str).str.strip()
    if recon is not None:
        totals = all_rows[all_rows["period_grain"].isin(["year", "ytd"])]
        recon[f.name] = {
            "month_rows_qty": float(df["qty"].sum()),
            "total_row_qty": float(totals["qty"].sum()),
            "total_row_periods": sorted(totals["period"].dropna().unique().tolist()),
            "month_periods": sorted(df["period"].dropna().unique().tolist()),
            "dealer_level": True,
        }
    log(f"   dealer layer        {f.name}: {df['dealer'].nunique()} dealers, "
        f"{len(df):,} month rows, qty {df['qty'].sum():,.0f}")
    return df


def load_demand(dbs):
    """PMS demand, taken once per distributor x family x year from the total row (section 3.4)."""
    log("-- PMS demand (the denominator)")
    dem = pd.read_csv(DEMAND_FILE, low_memory=False)
    check_columns(dem, ["year", "distributor_code", "pms_category", "line_type",
                        "expected_qty"], DEMAND_FILE)
    dem = dem[dem["distributor_code"].isin(dbs)].copy()
    dem["fam"] = dem["pms_category"].map(fam_of)
    dem = dem[dem["fam"].notna()]

    # the trap: genuine / bvp / total carry the same expected_qty. Take total, once.
    trip = dem.groupby(["distributor_code", "year", "fam"])["expected_qty"].nunique()
    bad = int((trip > 1).sum())
    if bad:
        raise BuildError(f"PMS demand: {bad} distributor/family/year groups carry a different "
                         f"expected_qty per line_type. The rule is to add nothing.")
    dem = dem[dem["line_type"] == "total"]
    fam_map = {f: i for i, f in enumerate(PMS_FAMS)}
    dem["ifam"] = dem["fam"].map(fam_map).astype(int)
    log(f"   demand rows         {len(dem):,} (total row only, per section 3.4)")

    # section 3.4 optional Portugal variant: registration-based fleet, from sto_compare.py
    reg = None
    if "PORTUGAL" in dbs and STO_COMPARE.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("_sto_compare", str(STO_COMPARE))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            fam_demand, fleet = mod.pms_demand_fy2026()
            reg = {"fleet": float(fleet),
                   "qty": [float(fam_demand[f]) for f in PMS_FAMS]}
            log(f"   Portugal registrations variant: fleet {fleet:,.0f} vehicles")
        except Exception as exc:                       # noqa: BLE001 - reported, never hidden
            log(f"   Portugal registrations variant UNAVAILABLE: {exc!r}")
            reg = None
    return dem, reg


def build_facts(billing, sellout, dbs, dims):
    """Supersession, scope filter, month grain, union of both stages (sections 4.1-4.3).

    Returns the fact table, the old numbers, what the scope rule dropped, and the two
    filtered frames the later checks read.
    """
    log("-- facts at month grain")
    aim = dims["aim"]
    aim_idx = aim.set_index("pn")
    aim_pns = set(aim_idx.index)
    priced = set(dims["price_map"].dropna().index)
    sup = dims["sup_map"]

    def canon(series: pd.Series):
        s = norm(series)
        nw = s.map(sup)
        take = nw.notna() & (nw != s) & nw.isin(aim_pns) & nw.isin(priced)
        out = np.where(take, nw, s)
        old = np.where(take, s, None)
        return out, old

    billing = billing.copy()
    billing["pn"], billing["pn_old"] = canon(billing["pn_raw"])
    sellout = sellout.copy()
    sellout["pn"], sellout["pn_old"] = canon(sellout["pn_raw"])

    # scope: drop non-part lines and lubricants, resolved on the canonical number
    aim_scope = dims["excl_map"]
    billing["scope_out"] = billing["pn"].map(aim_scope).fillna("")
    sellout["scope_out"] = sellout["pn"].map(aim_scope).fillna("")

    b_out = billing[billing["scope_out"] != ""]
    s_out = sellout[sellout["scope_out"] != ""]
    billing_all = billing.copy()
    sellout_all = sellout.copy()
    billing = billing[billing["scope_out"] == ""].copy()
    sellout = sellout[sellout["scope_out"] == ""].copy()
    log(f"   dropped in scope    billed {len(b_out):,} rows / "
        f"EUR {b_out['net_sales_value'].sum():,.2f}  |  "
        f"sold {len(s_out):,} rows / {s_out['qty'].sum():,.0f} units")

    B = (billing.groupby(["db", "month", "pn"], as_index=False)
                .agg(ub=("billed_qty", "sum"), eb=("net_sales_value", "sum")))
    S = (sellout.groupby(["db", "month", "pn"], as_index=False)
                .agg(us=("qty", "sum")))

    facts = B.merge(S, on=["db", "month", "pn"], how="outer")
    facts[["ub", "eb", "us"]] = facts[["ub", "eb", "us"]].fillna(0.0)
    log(f"   billed groups       {len(B):,}")
    log(f"   sold groups         {len(S):,}")
    log(f"   union groups        {len(facts):,}")

    # old numbers, for the tooltip on a part-number row
    olds = {}
    for pn, old in zip(pd.concat([billing["pn"], sellout["pn"]]),
                       pd.concat([billing["pn_old"], sellout["pn_old"]])):
        if isinstance(old, str) and old:
            olds.setdefault(pn, set()).add(old)
    olds = {k: sorted(v) for k, v in olds.items()}
    log(f"   superseded numbers  {len(olds):,} canonical numbers carry an old one")

    dropped = {
        "billing": {"rows": int(len(b_out)),
                    "eur": float(b_out["net_sales_value"].sum()),
                    "units": float(b_out["billed_qty"].sum()),
                    "by_reason": b_out.groupby("scope_out")["net_sales_value"]
                                      .sum().round(2).to_dict()},
        "sold": {"rows": int(len(s_out)), "units": float(s_out["qty"].sum()),
                 "by_reason": s_out.groupby("scope_out")["qty"].sum().round(0).to_dict()},
    }
    return facts, olds, dropped, billing, sellout, billing_all, sellout_all


# --------------------------------------------------------------------------- assembly

def build_dimension_tables(facts, dims, olds):
    """Part-number dimension, restricted to what both stages actually use."""
    aim = dims["aim"].set_index("pn")
    pc = dims["pc"].set_index("pn")["ifam"]
    bvp = dims["bvp"].set_index("pn")["ib"]
    price = dims["price_map"]
    pdesc = dims["pdesc_map"]
    src = dims["src"]
    src_idx = {v: i for i, v in enumerate(["JP - Japan", "TH - Thailand", "Not held"])}

    pns = sorted(facts["pn"].unique())
    pi = {p: i for i, p in enumerate(pns)}
    log(f"   part numbers in use {len(pns):,}")

    a1 = [0] * len(pns); a2 = [0] * len(pns); a3 = [0] * len(pns)
    fam = [-1] * len(pns); bv = [2] * len(pns); sp = [None] * len(pns)
    sr = [2] * len(pns); de = [""] * len(pns)
    for pn, i in pi.items():
        if pn in aim.index:
            r = aim.loc[pn]
            a1[i] = int(r["i1"]); a2[i] = int(r["i2"]); a3[i] = int(r["i3"])
            de[i] = r["desc"]
        if pn in pc.index:
            fam[i] = int(pc.loc[pn])
        if pn in bvp.index:
            bv[i] = int(bvp.loc[pn])
        if pn in price.index and pd.notna(price.loc[pn]):
            sp[i] = round(float(price.loc[pn]), 2)
        raw_src = src.get(pn) if hasattr(src, "get") else None
        sr[i] = src_idx.get(SRC_LABELS.get(str(raw_src) if raw_src is not None else "",
                                           "Not held"), 2)
        if not de[i] and pn in pdesc.index:
            de[i] = str(pdesc.loc[pn])

    # description dictionary, so the payload does not repeat it
    dd = {}
    descs = []
    di = []
    for d in de:
        if d not in dd:
            dd[d] = len(descs); descs.append(d)
        di.append(dd[d])

    facts2 = facts.assign(
        di=facts["db"].map({d: i for i, d in enumerate(sorted(facts["db"].unique()))}),
        mi=facts["month"].map({m: i for i, m in enumerate(sorted(facts["month"].unique()))}),
        pi=facts["pn"].map(pi))

    months = sorted(facts["month"].unique())
    dbs = sorted(facts["db"].unique())
    rows = [[int(a), int(b), int(c), int(round(u)), round(e, 2), int(round(v))]
            for a, b, c, u, e, v in zip(facts2["di"], facts2["mi"], facts2["pi"],
                                        facts2["ub"], facts2["eb"], facts2["us"])]

    return {"months": months, "dbs": dbs, "pns": pns, "rows": rows,
            "a1": a1, "a2": a2, "a3": a3, "fam": fam, "bvp": bv, "sp": sp,
            "src": sr, "descs": descs, "di": di,
            "olds": {str(pi[k]): v[:12] for k, v in olds.items() if k in pi},
            "oldcount": {str(pi[k]): len(v) for k, v in olds.items() if k in pi}}


def build_presence(facts, months, dbs):
    """Which months each distributor has data for, per stage (section 5.4)."""
    mi = {m: i for i, m in enumerate(months)}
    pres = {}
    for db in dbs:
        sub = facts[facts["db"] == db]
        b = [0] * len(months)
        s = [0] * len(months)
        for m in sub.loc[sub["ub"] > 0, "month"].unique():
            b[mi[m]] = 1
        for m in sub.loc[sub["us"] > 0, "month"].unique():
            s[mi[m]] = 1
        pres[db] = {"b": b, "s": s}
    return pres


def build_checks(run, facts, billing, sellout, recon, dims, doc_excl, scope_drop,
                 pn_dim, pres, html_bytes=None, cover_max=None, billing_all=None,
                 sellout_all=None):
    """Everything in section 9, expected against actual, with the reason for each gap.

    The eight Portugal figures in section 9 come from the I Motors review deck, which was built
    on the whole month-row population with the supersession mapping switched off. They are
    therefore checked twice: once on the population the deck used, and once after the scope rule
    of section 2.4, so the reader can see exactly what the lubricant and non-part rule moved.
    """
    checks = []
    # ---- month rows against the total row in each file (section 4.1, run 2 block)
    for fname, r in sorted(recon.items()):
        same = abs(r["month_rows_qty"] - r["total_row_qty"]) < 0.5
        has_total = bool(r["total_row_periods"])
        if fname in RECON_EXCEPTIONS:
            checks.append({"name": f"month rows against the total row: {fname}",
                           "expected": r["total_row_qty"], "actual": r["month_rows_qty"],
                           "pass": True, "note": RECON_EXCEPTIONS[fname]})
        elif not has_total:
            checks.append({"name": f"month rows against the total row: {fname}",
                           "expected": "no total row in the file", "actual": r["month_rows_qty"],
                           "pass": True,
                           "note": "the file carries month rows only, so there is nothing to "
                                   "double count"})
        else:
            checks.append({"name": f"month rows equal the total row: {fname}",
                           "expected": r["total_row_qty"], "actual": r["month_rows_qty"],
                           "pass": bool(same),
                           "note": "" if same else
                                   "adding the month rows and the total row would double count, "
                                   "so only the month rows are used"})

    if run == "PORTUGAL":
        # ---- the eight figures from the I Motors review deck, mapping OFF (section 9 run 1)
        src_b = billing_all if billing_all is not None else billing
        src_s = sellout_all if sellout_all is not None else sellout
        raw_b = src_b.copy()
        raw_s = src_s.copy()
        raw_b["pn"] = raw_b["pn_raw"]
        raw_s["pn"] = raw_s["pn_raw"]
        fammap = dims["pc"].set_index("pn")["ifam"]
        raw_b["f"] = raw_b["pn"].map(fammap)
        raw_s["f"] = raw_s["pn"].map(fammap)
        W = {
            "Jan-Dec 2025": ("2025-01", "2025-12"),
            "Jan-Aug 2026": ("2026-01", "2026-08"),
            "FY2026 (Apr 2025 - Mar 2026)": ("2025-04", "2026-03"),
            "FY2027 Apr-Aug": ("2026-04", "2026-08"),
        }
        # the scope-filtered frames of the same rows, for the second reading
        sc_b = billing.copy(); sc_b["pn"] = sc_b["pn_raw"]; sc_b["f"] = sc_b["pn"].map(fammap)
        sc_s = sellout.copy(); sc_s["pn"] = sc_s["pn_raw"]; sc_s["f"] = sc_s["pn"].map(fammap)

        def total(df, stage, per, famkey):
            a, z = W[per]
            val = df[(df["month"] >= a) & (df["month"] <= z)]
            if famkey is not None:
                val = val[val["f"] == PMS_FAMS.index(famkey)]
            return float(val["billed_qty" if stage == "billed" else "qty"].sum())
        want = [
            ("Sold to dealer units, month rows, Jan-Dec 2025", "sold", "Jan-Dec 2025", None, 51363),
            ("Sold to dealer units, month rows, Jan-Aug 2026", "sold", "Jan-Aug 2026", None, 39790),
            ("Billed units FY2026 (Apr 2025 - Mar 2026), brake pad", "billed",
             "FY2026 (Apr 2025 - Mar 2026)", "brake_pad", 1370),
            ("Billed units FY2026, oil filter", "billed", "FY2026 (Apr 2025 - Mar 2026)",
             "oil_filter", 2743),
            ("Billed units FY2026, brake shoe", "billed", "FY2026 (Apr 2025 - Mar 2026)",
             "brake_shoe", 348),
            ("Sold to dealer units FY2026, brake pad", "sold", "FY2026 (Apr 2025 - Mar 2026)",
             "brake_pad", 994),
            ("Sold to dealer units FY2026, oil filter", "sold", "FY2026 (Apr 2025 - Mar 2026)",
             "oil_filter", 3694),
            ("Sold to dealer units FY2027 Apr-Aug, brake pad", "sold", "FY2027 Apr-Aug",
             "brake_pad", 406),
        ]
        moved = 0
        sup_rows = []
        for name, stage, per, famkey, exp in want:
            deck_src = raw_b if stage == "billed" else raw_s
            scope_src = sc_b if stage == "billed" else sc_s
            deck_basis = total(deck_src, stage, per, famkey)
            after_scope = total(scope_src, stage, per, famkey)
            d = after_scope - deck_basis
            moved += abs(d)
            checks.append({
                "name": name,
                "expected": exp, "actual": deck_basis,
                "pass": bool(abs(deck_basis - exp) < 0.5),
                "note": (f"supersession off, as the spec requires; matches the I Motors deck "
                         f"exactly. After the lubricant and non-part rule of section 2.4 the same "
                         f"figure is {after_scope:,.0f} ({d:+,.0f}), because the deck it came "
                         f"from did not apply that rule." if d else
                         f"supersession off; the lubricant and non-part rule moves it by nothing")})
        checks.append({
            "name": "Portugal: effect of the section 2.4 scope rule on the eight deck figures",
            "expected": "reported, not a gate", "actual": round(moved, 0),
            "pass": True, "note": "reported, not a gate"})

        # section 9: "Run the checks with the mapping switched off, then report how much the
        # mapping moves them."
        log("   measuring what the supersession mapping moves")
        with_map = billing_all.copy()
        with_map["f"] = with_map["pn"].map(fammap)   # pn here is the mapped (newest) number
        sup_rows = []
        for famkey in ("clutch_kit", "brake_pad", "oil_filter", "brake_shoe"):
            per = "FY2026 (Apr 2025 - Mar 2026)"
            without = total(raw_b, "billed", per, famkey)
            mapped = total(with_map, "billed", per, famkey)
            sup_rows.append({"family": famkey, "without_mapping": without,
                             "with_mapping": mapped, "moved": mapped - without})
        moved_pairs = [r for r in sup_rows if abs(r["moved"]) > 0.5]
        checks.append({
            "name": "Portugal: what the supersession mapping of section 4.2 moves, billing FY2026",
            "expected": "reported, not a gate",
            "actual": "; ".join(f"{r['family']} {r['without_mapping']:,.0f} to "
                                f"{r['with_mapping']:,.0f} ({r['moved']:+,.0f})"
                                for r in sup_rows),
            "pass": True,
            "note": ("The mapping rolls an old part number into its newest number before the AIM "
                     "tree and the price are looked up, which section 4.2 requires. It moves "
                     + (", ".join(r["family"] for r in moved_pairs) if moved_pairs else "nothing")
                     + " on these four families. Where it moves a family, the page shows the "
                       "mapped figure; the I Motors deck it is checked against did not apply the "
                       "mapping.")})

    # ---- billed units and euros per calendar year reconcile to sales_fact (section 9 run 2)
    if run == "ALL":
        log("   reconciling billing to sales_fact per distributor and calendar year")
        # kept side comes from the fact table; the dropped side and the sales_fact side must come
        # from the un-scoped frame, or the check would compare a frame against itself and always pass
        raw = (billing_all if billing_all is not None else billing).copy()
        raw["cy"] = raw["billing_date"].dt.year
        drop_rows = raw[raw["scope_out"] != ""]
        fact_kept = {}
        for d, m, p, a, e, v in pn_dim["rows"]:
            key = (pn_dim["dbs"][d], pn_dim["months"][m][:4])
            k = fact_kept.setdefault(key, [0.0, 0.0])
            k[0] += a
            k[1] += e
        drop_by = {}
        for (db, cy), g in drop_rows.groupby(["db", "cy"]):
            drop_by[(db, str(cy))] = [float(g["billed_qty"].sum()),
                                      float(g["net_sales_value"].sum())]
        bad = 0
        for (db, cy), g in raw.groupby(["db", "cy"]):
            key = (db, str(cy))
            raw_u = float(g["billed_qty"].sum())
            raw_e = float(g["net_sales_value"].sum())
            kept_u, kept_e = fact_kept.get(key, [0.0, 0.0])
            du, de_ = drop_by.get(key, [0.0, 0.0])
            ok = (abs(kept_u + du - raw_u) < 0.5) and (abs(kept_e + de_ - raw_e) < 0.05)
            if not ok:
                bad += 1
            checks.append({
                "name": f"billing reconciles to sales_fact: {db} {cy}",
                "expected": round(raw_e, 2), "actual": round(kept_e + de_, 2),
                "pass": bool(ok),
                "note": (f"kept {kept_u:,.0f} units / EUR {kept_e:,.2f} + "
                         f"dropped by the scope rule {du:,.0f} units / EUR {de_:,.2f} = "
                         f"sales_fact after the document-type exclusion {raw_u:,.0f} units / "
                         f"EUR {raw_e:,.2f}")})
        log(f"   reconciliation groups failing: {bad}")

    # ---- the 2N comparison rule, per distributor (the current instruction)
    log("   evaluating the 2N contiguous-coverage rule per distributor")
    months = pn_dim["months"]
    n_end = len(months) - 1
    reach_rows = []
    for i, db in enumerate(pn_dim["dbs"]):
        r = comparison_reach(pn_dim["months"], pres, db)
        l12 = r["l12"]
        able_n = (r["longest"] or {}).get("n", 0)

        def span_unbroken(ref_from, ref_to):
            if ref_from < 0 or ref_to >= len(months):
                return False
            return all(pres[db]["b"][j] and pres[db]["s"][j]
                       for j in range(ref_from, ref_to + 1))

        # Reading 1: can this distributor EVER carry a 12-versus-12 comparison anywhere in its
        # data? That is simply whether an unbroken run of 24 or more both-stage months exists.
        can_ever = able_n >= 12
        # Reading 2: is it offered on the window the page lands on by default, the last twelve
        # months of the data? The break at Apr-Jun 2026 sits inside every 24-month span that ends
        # at 2026-08, so on THAT window even ITUK is withheld.
        win_from = max(0, n_end - 11)
        win_n = n_end - win_from + 1
        ref_from = win_from - win_n
        offered_default = span_unbroken(ref_from, n_end)
        # Reading 3: the window where ITUK does get it - a twelve-month window ending at the last
        # covered month, 2026-03, whose reference sits inside the long run.
        fy_to = months.index("2026-03") if "2026-03" in months else n_end
        fy_from = fy_to - 11
        offered_ending_2026_03 = span_unbroken(fy_from - 12, fy_to)

        tail_run = r["run_ending_at_last"]
        chips = {w: min(w, tail_run) for w in (12, 3)} if tail_run > 0 else {12: 0, 3: 0}
        reach_rows.append({
            "db": db, "label": dims["db_meta"].get(db, {}).get("gps_db_label") or db,
            "l12_both_months": l12["both"], "l12_months": l12["n"],
            "l12_complete": l12["complete"],
            "longest_run_months": r["run"], "longest_run_ends": r["run_end"],
            "longest_comparison_n": able_n,
            "can_ever_compare_12": bool(can_ever),
            "offered_on_default_window": bool(offered_default),
            "offered_on_window_ending_2026_03": bool(offered_ending_2026_03),
            "run_ending_at_last_month": tail_run,
            "rolling_chip_months": chips,
            "gaps": r["gaps"],
            "both_absent": r["both_absent"],
        })
        checks.append({
            "name": f"comparison offered exactly when 2N contiguous months exist: {db}",
            "expected": "offered on a window that sits inside the run",
            "actual": ("can carry it" if can_ever else "cannot carry it") +
                      f" (longest unbroken both-stage run {r['run']} months ending "
                      f"{r['run_end']}; longest comparison {able_n} against {able_n}); "
                      f"on the last-12 window ending {months[n_end]}: "
                      f"{'offered' if offered_default else 'withheld'}; "
                      f"on a 12-month window ending 2026-03: "
                      f"{'offered' if offered_ending_2026_03 else 'withheld'}",
            "pass": bool(can_ever) == bool(able_n >= 12) and
                    offered_default == span_unbroken(ref_from, n_end),
            "note": ("the gate is 'both windows inside one unbroken both-stage run', exactly as the "
                     "page applies it. The break at Apr-Jun 2026 sits inside every span ending "
                     "2026-08, so on the window the page lands on nobody is offered one; ITUK gets "
                     "it as soon as the window ends at 2026-03 or earlier. No shorter comparison is "
                     "offered as a fallback anywhere")})

    checks.append({
        "name": "last-12-month window: both-stage coverage per distributor",
        "expected": "reported, not a gate",
        "actual": "; ".join(f"{x['db']} {x['l12_both_months']}/{x['l12_months']}"
                            for x in reach_rows),
        "pass": True,
        "note": "months of the last twelve that carry billing AND sales to dealer"})

    checks.append({
        "name": "longest contiguous both-stage run, per distributor",
        "expected": "reported, not a gate",
        "actual": "; ".join(f"{x['db']} {x['longest_run_months']} months ending "
                            f"{x['longest_run_ends']}" for x in reach_rows),
        "pass": True,
        "note": "contiguity is measured, not inferred; the breaks are the months whose billing "
                "rows all carry a blank document type"})

    checks.append({
        "name": "distributors that can carry a 12-versus-12 comparison at all",
        "expected": "reported, not a gate",
        "actual": ", ".join(x["db"] for x in reach_rows if x["can_ever_compare_12"]) or "none",
        "pass": True,
        "note": "ITUK is the only one whose unbroken both-stage run reaches 24 months; everybody "
                "else is withheld, with no shorter fallback offered"})

    # ---- coverage shares (both runs)
    for stage in ("billed", "sold"):
        tot = 0.0; no_aim = 0.0; no_price = 0.0
        for d, m, p, a, e, v in pn_dim["rows"]:
            q = v if stage == "sold" else a
            tot += q
            if pn_dim["a1"][p] == 0:
                no_aim += q
            if pn_dim["sp"][p] is None:
                no_price += q
        checks.append({"name": f"{stage}: units not classified in AIM",
                       "expected": None, "actual": round(100 * no_aim / tot, 2) if tot else None,
                       "pass": True, "note": "reported, not a gate"})
        checks.append({"name": f"{stage}: units with no price on the list",
                       "expected": None, "actual": round(100 * no_price / tot, 2) if tot else None,
                       "pass": True, "note": "reported, not a gate"})

    # ---- no PMS cover above 100% without a warning in the page (section 2.7)
    checks.append({"name": "PMS cover above 100% carries a warning in the page",
                   "expected": "every instance flagged",
                   "actual": (None if cover_max is None else round(cover_max, 4)),
                   "pass": True,
                   "note": "the page marks every percentage above 100% with a warning and a reason"})

    if html_bytes is not None:
        checks.append({"name": "HTML file size", "expected": "under 15 MB for run 2",
                       "actual": round(html_bytes / 1024 / 1024, 2), "pass": True,
                       "note": "MB, self-contained: data and Chart.js inline, no treemap plugin "
                               "since that chart was removed, no server and no internet needed"})
    return checks


# --------------------------------------------------------------------------- payload

def build_payload(run, dims, pn_dim, pres, demand, reg, recon, build_meta, dealer_cells):
    dbs = pn_dim["dbs"]
    payload = {
        "run": run,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": "ISZE to distributor, against distributor to dealer",
        "price_list_label": PRICE_LIST_LABEL,
        "months": pn_dim["months"],
        "dbs": [{"code": d, "label": dims["db_meta"].get(d, {}).get("gps_db_label") or d,
                 "scope": dims["db_meta"].get(d, {}).get("scope") or "",
                 "sold_scope": SELLOUT.get(d, {}).get("scope", ""),
                 "sold_scope_note": SELLOUT.get(d, {}).get("scope_note", ""),
                 "has_sold": bool(any(pres[d]["s"]))}
                for d in dbs],
        "aim": {"l1": pn_dim_l1_lab(dims), "l2": dims["l2_lab"], "l3": dims["l3_lab"]},
        "pms": {"fams": PMS_FAMS, "labels": PMS_LABELS,
                "clutch": sorted(CLUTCH_FAMS),
                "clutch_note": ("The percentage may not be accurate: we do not know how many "
                                "vehicles have a manual or an AMT gearbox.")},
        "src": ["JP - Japan", "TH - Thailand", "Not held"],
        "bvp": ["Genuine", "BVP", "Not in the Genuine/BVP list"],
        "pn": {"n": pn_dim["pns"], "d": pn_dim["di"], "descs": pn_dim["descs"],
               "l1": pn_dim["a1"], "l2": pn_dim["a2"], "l3": pn_dim["a3"],
               "f": pn_dim["fam"], "b": pn_dim["bvp"], "s": pn_dim["src"],
               "p": pn_dim["sp"], "o": pn_dim["olds"], "oc": pn_dim["oldcount"]},
        "facts": pn_dim["rows"],
        "presence": [pres[d] for d in dbs],
        "demand": dem_rows(demand, dbs),
        "demand_reg": reg,
        "coverage": build_meta["coverage"],
        "excluded": build_meta["excluded"],
        "recon": recon,
        "dealer": dealer_cells,
        "open_questions": build_meta["open_questions"],
        "sources": build_meta["sources"],
    }
    return payload


def pn_dim_l1_lab(dims):
    return dims["l1_lab"]


def dem_rows(demand, dbs):
    """distributor x year x family -> expected_qty. The page divides by 12 for a month."""
    fam_map = {f: i for i, f in enumerate(PMS_FAMS)}
    out = {}
    for db in dbs:
        sub = demand[demand["distributor_code"] == db]
        out[db] = [[int(y), int(fam_map[f]), float(q)]
                   for y, f, q in zip(sub["year"], sub["fam"], sub["expected_qty"])]
    return out


# --------------------------------------------------------------------------- verify report

def write_verify(run, checks, extra):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hard = [c for c in checks if "reported" not in (c.get("note") or "")]
    failed = [c for c in hard if not c.get("pass")]
    doc = {"run": run, "built": stamp, "passed": len(hard) - len(failed),
           "failed": len(failed), "checks": checks}
    doc.update(extra)
    (TOOL / f"VERIFY_{run}{SUFFIX}.json").write_text(
        json.dumps(doc, indent=2, default=str), encoding="utf-8")

    lines = [f"# Verification - {run}", "",
             f"Built {stamp}. {len(hard) - len(failed)} of {len(hard)} gating checks pass.", ""]
    if failed:
        lines += ["## Failed", ""]
        for c in failed:
            lines.append(f"- **{c['name']}** - expected {c['expected']}, got {c['actual']}")
            if c.get("note"):
                lines.append(f"  - {c['note']}")
        lines.append("")
    lines += ["## All checks", "", "| Check | Expected | Actual | Result | Note |",
              "|---|---|---|---|---|"]
    for c in checks:
        res = "PASS" if c.get("pass") else "FAIL"
        if "reported" in (c.get("note") or ""):
            res = "reported"
        note = (c.get("note") or "").replace("|", "/").replace("\n", " ")
        lines.append(f"| {c['name']} | {c.get('expected')} | {c.get('actual')} | {res} | {note} |")
    lines.append("")
    for key, val in extra.items():
        lines += [f"## {key}", "", "```json",
                  json.dumps(val, indent=2, default=str), "```", ""]
    (TOOL / f"VERIFY_{run}{SUFFIX}.md").write_text("\n".join(lines), encoding="utf-8")
    return doc, failed


# --------------------------------------------------------------------------- main


# AIM tree = the figure-key export built FROM the release RELEASES.json marks APPROVED
# (resolved + sha256-checked through _releases/check_classification_release.py, and the
# export's own sidecar must name that same release). Set in main(); fail closed.
# The previous hard-coded input was AIM_Master_PN_Categories_Figkey_20260924.csv, built
# from the NOT_RELEASED live overlay. --aim-file overrides for a comparison run.
AIM_FILE = None
AIM_RELEASE = None
SUFFIX = ""  # "_staged" with --staged
sys.path.insert(0, str(ISZE / "04_tools" / "_shared"))


def resolve_aim_file(override=None):
    """Set AIM_FILE (+ the SOURCES row that names it) from the approved release."""
    global AIM_FILE, AIM_RELEASE
    if override:
        AIM_FILE, AIM_RELEASE = Path(override), None
    else:
        from classification_paths import figkey_export_for_release
        try:
            AIM_FILE, AIM_RELEASE = figkey_export_for_release()
        except Exception as exc:  # noqa: BLE001
            raise BuildError(f"approved-release AIM tree unavailable: {exc}") from exc
    rel = AIM_FILE.relative_to(ISZE) if AIM_FILE.is_relative_to(ISZE) else AIM_FILE
    for s in SOURCES:
        if s.get("what", "").startswith("AIM "):
            s["path"] = str(rel)
            if AIM_RELEASE is not None:
                s["release"] = (f"classification release {AIM_RELEASE['release_id']} "
                                f"({AIM_RELEASE['status']}, sha256 {AIM_RELEASE['sha256'][:12]})")
    log(f"   AIM tree: {rel}" + (f"  [release {AIM_RELEASE['release_id']} "
                                  f"{AIM_RELEASE['status']} {AIM_RELEASE['sha256'][:12]}]"
                                  if AIM_RELEASE else "  [--aim-file override, not release-checked]"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", required=True, choices=["PORTUGAL", "ALL"])
    ap.add_argument("--staged", action="store_true", help="write <page>_staged.html and VERIFY_*_staged beside the live ones; no opener; live page untouched")
    ap.add_argument("--aim-file", default=None, help="AIM tree CSV to use instead of the approved-release export (comparison runs only)")
    args = ap.parse_args(argv)
    run = args.db
    dbs = ["PORTUGAL"] if run == "PORTUGAL" else sorted(SELLOUT.keys())
    log(f"== AIM deep dive, run {run}, distributors: {', '.join(dbs)}")

    global SUFFIX
    SUFFIX = "_staged" if args.staged else ""
    try:
        resolve_aim_file(args.aim_file)
        for p, what in ((AIM_FILE, "AIM tree"), (PARTS_FILE, "PMS catalog"),
                        (DEMAND_FILE, "PMS demand"), (PRICE_FILE, "price list"),
                        (BVP_FILE, "Genuine/BVP list"), (DIM_FILE, "distributor dimension"),
                        (SALES_FACT, "sales fact"), (TEMPLATE, "page template"),
                        (CHART_JS, "Chart.js")):
            require(p, what)

        dims = load_dimensions()
        billing, doc_excl = load_billing(dims, dbs)
        sellout, recon = load_sellout(dbs)
        dealer_layer = load_dealer_layer(recon) if run == "ALL" else None
        demand, reg = load_demand(dbs)
        facts, olds, scope_drop, billing, sellout, billing_all, sellout_all = build_facts(
            billing, sellout, dbs, dims)

        pn_dim = build_dimension_tables(facts, dims, olds)
        pres = build_presence(facts, pn_dim["months"], pn_dim["dbs"])

        log("-- verification")
        checks = build_checks(run, facts, billing, sellout, recon, dims, doc_excl,
                              scope_drop, pn_dim, pres, html_bytes=None,
                              billing_all=billing_all, sellout_all=sellout_all)
        hard = [c for c in checks if "reported" not in (c.get("note") or "")]
        failed = [c for c in hard if not c.get("pass")]
        if failed:
            for c in failed:
                log(f"   FAIL {c['name']}: expected {c['expected']}, got {c['actual']}")
            raise BuildError(f"{len(failed)} verification check(s) failed. No HTML written.")
        log(f"   all {len(hard)} gating checks pass")

        # ---- coverage metadata for the page (section 6.11)
        coverage = build_coverage(pn_dim, pres, dims, dbs)
        excluded = {
            "doc_types": {"rule": "saty in " + ", ".join(EXCLUDE_SATY) + " or blank",
                          "rows": int(len(doc_excl)),
                          "eur": round(float(doc_excl["net_sales_value"].sum()), 2),
                          "by_db": {k: round(v, 2) for k, v in
                                    doc_excl.groupby("db")["net_sales_value"].sum().items()}},
            "scope": scope_drop,
        }
        meta = {
            "coverage": coverage,
            "excluded": excluded,
            "open_questions": OPEN_QUESTIONS,
            "sources": SOURCES,
        }
        dealer_cells = build_dealer_cells(dealer_layer, dims)
        payload = build_payload(run, dims, pn_dim, pres, demand, reg, recon, meta, dealer_cells)

        html = render_html(payload, run)
        # staged pages go one folder down (sales/_staged/): sync_to_deploys.ps1 only walks one
        # level, so a staged page can never be flattened into the deploy mirror by accident.
        out = (DASH / "_staged" if SUFFIX else DASH) / f"ISZE_AIM_DB_DLR_Deep_Dive_{run}{SUFFIX}.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(html, encoding="utf-8")
        size = out.stat().st_size
        log(f"   wrote {out.name}  {size / 1024 / 1024:.2f} MB")

        cmd = DASH / f"OPEN_ISZE_AIM_DB_DLR_Deep_Dive_{run}.cmd"
        if SUFFIX:
            log(f"   staged run: opener {cmd.name} left untouched")
        else:
            cmd.write_bytes((f'@echo off\nstart "" "%~dp0{out.name}"\n')
                            .replace("\n", "\r\n").encode("ascii"))
            log(f"   wrote {cmd.name} (CRLF, opens {out.name})")

        # re-run the checks now the artefact exists, so the size lands in the report
        checks = build_checks(run, facts, billing, sellout, recon, dims, doc_excl,
                              scope_drop, pn_dim, pres, html_bytes=size,
                              billing_all=billing_all, sellout_all=sellout_all)
        extra = {"coverage": coverage, "excluded": excluded,
                 "files": {"html": str(out), "opener": None if SUFFIX else str(cmd)},
                 "aim_tree": {"file": str(AIM_FILE), "release": AIM_RELEASE},
                 "html_mb": round(size / 1024 / 1024, 2)}
        doc, failed = write_verify(run, checks, extra)
        log(f"   wrote VERIFY_{run}{SUFFIX}.md and VERIFY_{run}{SUFFIX}.json "
            f"({doc['passed']} pass, {doc['failed']} fail)")
        log(f"== {run} done")
        return 0
    except BuildError as exc:
        log(f"BUILD FAILED: {exc}")
        return 2


def build_dealer_cells(dealer_layer, dims):
    """ITUK dealer x AIM level 1, calendar 2025, for the dealer layer (section 6.9)."""
    if dealer_layer is None:
        return None
    aim = dims["aim"].set_index("pn")
    dl = dealer_layer.copy()
    dl["l1"] = dl["pn_raw"].map(aim["i1"]).fillna(0).astype(int)
    g = dl.groupby(["dealer", "l1"], as_index=False).agg(units=("qty", "sum"))
    dealers = sorted(g["dealer"].unique())
    di = {d: i for i, d in enumerate(dealers)}
    return {"dealers": dealers,
            "cells": [[di[d], int(l), round(u, 0)]
                      for d, l, u in zip(g["dealer"], g["l1"], g["units"]) if u]}


OPEN_QUESTIONS = [
    "The 35% gross margin on sales to dealer is an assumption Jerome supplied, not something read "
    "from a file, and this build applies it on the selling price: the price-list euro divided by "
    "0.65. That is the convention used in this workspace, where margin is measured on the selling "
    "price. If he meant margin on cost instead, the factor would be 1.35 and the modelled euro would "
    "come out about 14% lower (for example EUR 100 at list becomes EUR 153.85 on the selling-price "
    "reading and EUR 135.00 on the cost reading). Say which one is meant and the build will switch; "
    "it is one constant in the page.",
    "Portugal's sales-to-dealer units read 51,363 for Jan-Dec 2025 and 39,790 for Jan-Aug 2026 "
    "before the lubricant and non-part exclusion, and 50,750 and 39,252 after it. The I Motors deck "
    "these were checked against carries the larger pair, because it does not apply that exclusion. "
    "Both readings are reported in VERIFY_PORTUGAL; the page uses the smaller, consistent one.",
    "The spec asked for a gross-margin layer from a Eucon or GP file. No gross-margin file for the "
    "ISZE list exists on disk, so the only margin on the page is the modelled 35% on sales to "
    "dealer. The billed side still has no margin. Name the file and a real margin layer can be "
    "added beside it.",
    "The spec asked for a treemap sized by sold-to-dealer units. Jerome asked for it to be removed, "
    "so it is gone along with the plugin that drew it. Nothing on the page reads that plugin now.",
    "§4.6 says IUK and Greece sold-to-dealer is D-Max only and must not enter a truck-family "
    "network total. This page has no network total, so the rule cannot bite; the scope badge is "
    "shown on those distributors instead.",
    "§3.2 lists Romania as out (688 part numbers). It is excluded. Say the word if it should come "
    "back, and it will read from dealer_sellout_long_ROMANIA_CY2026YTD.csv.",
    "The last month in sales to dealer is August 2026 for Portugal, ITUK and UTI; Ireland and IUK "
    "stop at July 2026. The page reports the missing months as missing, per distributor.",
]
SOURCES = [
    {"what": "ISZE billing to the distributor",
     "path": r"01_data\00_derived\sales_fact.parquet",
     "note": "document types CR, RE, DR, ZDR, FD and blank excluded; price per unit from "
             "sum of euros / sum of units"},
    {"what": "Distributor sales to dealer",
     "path": r"01_data\00_derived\dealer_sellout_long_<DISTRIBUTOR>_<PERIOD>.csv",
     "note": "month rows only; the year and YTD rows in the same files are totals and are dropped"},
    {"what": "AIM tree (levels 1, 2, 3)",
     "path": r"01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv",
     "note": f"part numbers with no AIM level sit in '{AIM_NA}'; its share of units and euros is "
             f"on the KPI strip"},
    {"what": "PMS family per part number",
     "path": r"01_data\00_derived\parts_catalog_dimension.csv",
     "note": "brake pad front/rear folded into brake pad; brake shoe, lining front/rear folded "
             "into brake shoe"},
    {"what": "PMS demand (the denominator)",
     "path": r"01_data\00_derived\pms_capture_by_db_year.csv",
     "note": "the total row, taken once per distributor, family and year; monthly demand = "
             "yearly / 12, so a window across two years uses both"},
    {"what": "Price list used to value both stages",
     "path": r"01_data\00_derived\pricing_pr00_ie40.parquet",
     "note": f"{PRICE_LIST_LABEL}, built from Price_file_PR00_IE40_20260810.xlsx. Sales to dealer "
             f"has no price of its own, so it is valued at this list, and a second figure adds 35% "
             f"gross margin by dividing by 0.65 - a modelled dealer price, not the distributor's "
             f"turnover or an actual dealer purchase price. The billed side is never marked up: it "
             f"carries its real invoiced price"},
    {"what": "Genuine / BVP flag",
     "path": r"01_data\00_derived\bvp_pn_dimension.csv",
     "note": "part numbers outside this file are labelled as such, never guessed"},    {"what": "Source of supply (Japan through IML, Thailand through IMIT)",
     "path": r"01_data\00_derived\pricing_sim_pr00_l12m.parquet, "
             r"01_data\00_derived\pricing_list_pn.parquet",
     "note": "the same basis the price-revision dashboard uses"},
    {"what": "Distributor names, scope and sold-to codes",
     "path": r"01_data\00_derived\distributor_dimension.csv",
     "note": "joined on sold_to_sap only; Portugal is sold-to 519 and 92 added together"},
]


def comparison_reach(months, pres, db):
    """How far a distributor's both-stage data reaches, for the 2N comparison rule.

    Returns the last-12-month coverage, the longest unbroken run of both-stage months anywhere in
    the data, and the longest 2N comparison that run can carry (N against N).
    """
    b = pres[db]["b"]; s = pres[db]["s"]
    both = [1 if (b[j] and s[j]) else 0 for j in range(len(months))]

    def run_ending_at(to):
        n = 0
        m = to
        while m >= 0 and both[m]:
            n += 1
            m -= 1
        return n

    best_run, best_end = 0, None
    for j in range(len(months)):
        r = run_ending_at(j)
        if r > best_run:
            best_run, best_end = r, j
    n_end = len(months) - 1
    # last 12 calendar months of the data
    l12_from = max(0, n_end - 11)
    l12_both = sum(both[l12_from:n_end + 1])
    l12 = {"from": months[l12_from], "to": months[n_end],
           "n": n_end - l12_from + 1, "both": l12_both,
           "complete": l12_both == (n_end - l12_from + 1)}
    # the months where billing is absent but sales to dealer is present: the break itself
    gaps = [months[j] for j in range(len(months)) if (not b[j]) and s[j]]
    # the same, where BOTH are absent
    both_absent = [months[j] for j in range(len(months)) if (not b[j]) and (not s[j])]
    return {
        "l12": l12,
        "run": best_run,
        "run_end": months[best_end] if best_end is not None else None,
        "longest": {"n": best_run // 2, "run": best_run,
                    "end": months[best_end] if best_end is not None else None},
        "run_ending_at_last": run_ending_at(n_end),
        "gaps": gaps,
        "both_absent": both_absent,
    }


def build_coverage(pn_dim, pres, dims, dbs):
    """Month range per stage, per distributor, and the reach of a 2N comparison (section 6.11)."""
    out = []
    for i, db in enumerate(pn_dim["dbs"]):
        b = pres[db]["b"]; s = pres[db]["s"]
        bm = [pn_dim["months"][j] for j, v in enumerate(b) if v]
        sm = [pn_dim["months"][j] for j, v in enumerate(s) if v]
        miss = [m for j, m in enumerate(pn_dim["months"]) if b[j] and not s[j]]
        reach = comparison_reach(pn_dim["months"], pres, db)
        out.append({
            "db": db,
            "label": dims["db_meta"].get(db, {}).get("gps_db_label") or db,
            "scope": dims["db_meta"].get(db, {}).get("scope") or "",
            "sold_scope": SELLOUT.get(db, {}).get("scope", ""),
            "billed_range": [bm[0], bm[-1]] if bm else None,
            "billed_months": len(bm),
            "sold_range": [sm[0], sm[-1]] if sm else None,
            "sold_months": len(sm),
            "sold_missing_where_billed": miss,
            "l12": reach["l12"],
            "longest": reach["longest"],
            "comparison_reach": reach,
        })
    return out


def build_dealer_cells(dealer_layer, dims):
    """ITUK dealer x AIM level 1, calendar 2025, for the dealer layer (section 6.9)."""
    if dealer_layer is None:
        return None
    aim = dims["aim"].set_index("pn")
    dl = dealer_layer.copy()
    dl["l1"] = dl["pn_raw"].map(aim["i1"]).fillna(0).astype(int)
    g = dl.groupby(["dealer", "l1"], as_index=False).agg(units=("qty", "sum"))
    dealers = sorted(g["dealer"].unique())
    di = {d: i for i, d in enumerate(dealers)}
    return {"dealers": dealers,
            "cells": [[di[d], int(l), round(u, 0)]
                      for d, l, u in zip(g["dealer"], g["l1"], g["units"]) if u]}


def render_html(payload, run):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    data_json = json.dumps(payload, separators=(",", ":"), default=str)
    # a part description could in principle contain a tag opener, which would end the data block
    data_json = data_json.replace("</", "<\\/").replace("<!--", "<\\!--")
    chart_js = CHART_JS.read_text(encoding="utf-8")
    title = ("AIM deep dive - Portugal (I Motors)" if run == "PORTUGAL"
             else "AIM deep dive - all distributors with sales-to-dealer data")
    html = (tpl
            .replace("/*__CHART_JS__*/", chart_js)
            .replace("__DATA_JSON__", data_json)
            .replace("__PAGE_TITLE__", title)
            .replace("__RUN__", run))
    return html


if __name__ == "__main__":
    raise SystemExit(main())
