#!/usr/bin/env python3
"""AIM period-over-period comparison: what grew and what fell, from AIM level 1 to part number.

Two runs, one script:

    python build_aim_comparison.py --db PORTUGAL   -> ISZE_AIM_Comparison_PORTUGAL.html
    python build_aim_comparison.py --db ALL        -> ISZE_AIM_Comparison_ALL.html

The basis is SALES TO DEALER. The period pair is the longest equal split the sales-to-dealer
months can carry, under the rule that a comparison of two N-month windows needs 2N contiguous
months of sales-to-dealer data. ISZE billing is shown beside it as context where it exists and
never decides which months are comparable.

Reads derived files only. Fails loudly, before writing any HTML, when an input is missing or a
check fails. Writes VERIFY_COMPARISON_<RUN>.md / .json next to itself.
"""
from __future__ import annotations

import argparse
import json
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

TEMPLATE = TOOL / "aim_cmp_template.html"
CHART_JS = UI / "chart.umd.min.js"          # Chart.js 4.4.1, inlined so the page opens offline

AIM_FILE = DER / "AIM_Master_PN_Categories_Figkey_20260921.csv"
PARTS_FILE = DER / "parts_catalog_dimension.csv"
PRICE_FILE = DER / "pricing_pr00_ie40.parquet"
BVP_FILE = DER / "bvp_pn_dimension.csv"
DIM_FILE = DER / "distributor_dimension.csv"
SALES_FACT = DER / "sales_fact.parquet"
SRC_SIM = DER / "pricing_sim_pr00_l12m.parquet"
SRC_LIST = DER / "pricing_list_pn.parquet"

# --------------------------------------------------------------------------- rules

EXCLUDE_SATY = ["CR", "RE", "DR", "ZDR", "FD"]
DROP_LINE_KIND = "part"
DROP_AIM_L1 = "Fluids Chemicals"            # keep Lubrication: engine parts, not oils
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
SRC_LABELS = {"J": "JP - Japan", "T": "TH - Thailand"}
SRC_LIST_OUT = ["JP - Japan", "TH - Thailand", "Not held"]
BVP_LIST_OUT = ["Genuine", "BVP", "Not in the Genuine/BVP list"]

GM_DIVISOR = 0.65                            # 35% gross margin measured on the selling price
PRICE_LIST_LABEL = "ISZE price list IE40 PR00 of 10 Aug 2026"

# a comparison is shown only where the data carries twice the window length; a quarter per side
# is the shortest window the page will draw at all
MIN_SIDE_MONTHS = 3
MAX_PAIRS = 5                                # options offered in the pair control

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
                 "scope": "MIXED", "scope_note": "network level; Feb-Jul 2025 absent"},
    "GREECE":   {"stems": ["_GREECE_CY2025"],
                 "scope": "D-MAX", "scope_note": "D-Max only, calendar 2025 only"},
}
ALL_DBS = sorted(SELLOUT.keys())

# the two files the brief names as exceptions to the month-row against total-row rule
RECON_EXCEPTIONS = {
    "dealer_sellout_long_UTI_CY2025.csv":
        "the brief names this file: its year row holds the whole year (92,660) while the month "
        "rows cover January and August to December only (55,570), because February to July 2025 "
        "are genuinely absent. Only the month rows are used, and the missing months are reported.",
    "dealer_sellout_long_ITUK_CY2025.csv":
        "the brief names this file: it is the dealer-level cut of ITUK's 2025 report, the one "
        "Jerome excluded for network totals. Its year row runs a little above its month rows "
        "(224,001 against 223,897), so it is not the basis here.",
}

MONTH_FROM, MONTH_TO = (2023, 1), (2026, 8)


class BuildError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- helpers

def norm(s: pd.Series) -> pd.Series:
    """Strip spaces, drop a trailing .0, strip leading zeros, keep as text."""
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


def fam_of(cat) -> str | None:
    c = str(cat)
    if c.startswith("brake_pad"):
        return "brake_pad"
    if c.startswith("brake_shoe") or c.startswith("brake_lining"):
        return "brake_shoe"
    return c if c in PMS_FAMS else None


def month_axis():
    out, y, m = [], MONTH_FROM[0], MONTH_FROM[1]
    while (y, m) <= MONTH_TO:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def runs_of(flags):
    """Contiguous True runs as (start_index, length)."""
    out, i = [], 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j + 1 < len(flags) and flags[j + 1]:
                j += 1
            out.append((i, j - i + 1))
            i = j + 1
        else:
            i += 1
    return out


def require(path: Path, what: str) -> None:
    if not path.exists():
        raise BuildError(f"MISSING {what}: {path}")


def check_columns(df: pd.DataFrame, cols, path: Path) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise BuildError(f"{path.name} is missing column(s) {missing}. "
                         f"Found: {list(df.columns)}")


# --------------------------------------------------------------------------- facts

def load_sellout(dbs):
    """Distributor -> dealer, month rows only, read by column name (file orders differ)."""
    log("-- sales to dealer (the basis)")
    frames, recon = [], {}
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
            df["qq"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0.0)
            months = df[df["period_grain"] == "month"].copy()
            totals = df[df["period_grain"].isin(["year", "ytd"])]
            recon[f.name] = {
                "distributor": db,
                "month_rows": int(len(months)),
                "month_rows_qty": float(months["qq"].sum()),
                "total_row_qty": float(totals["qq"].sum()),
                "total_row_periods": sorted(totals["period"].dropna().unique().tolist()),
                "month_periods": sorted(months["period"].dropna().unique().tolist()),
            }
            months["db"] = db
            per_file.append(months)
            log(f"   {f.name:<46} month rows {len(months):>7,}  qty {months['qq'].sum():>12,.0f}")
        if per_file:
            frames.append(pd.concat(per_file, ignore_index=True))
    so = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    so["month"] = so["period"].astype(str).str.strip()
    so["pn_raw"] = norm(so["part_number"])
    so["us"] = pd.to_numeric(so["qq"], errors="coerce").fillna(0.0)
    return so, recon


def load_billing(dims, dbs):
    """ISZE -> distributor, month grain, document types excluded (context beside the movement)."""
    log("-- ISZE billing (shown as context beside the movement)")
    sf = pd.read_parquet(SALES_FACT, columns=[
        "billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "saty"])
    check_columns(sf, ["billing_date", "sold_to_sap", "part_number", "billed_qty",
                       "net_sales_value", "saty"], SALES_FACT)
    log(f"   sales_fact.parquet   {len(sf):,} rows, "
        f"{sf.billing_date.min():%Y-%m-%d} to {sf.billing_date.max():%Y-%m-%d}")
    sf["sap"] = sf["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    sf["db"] = sf["sap"].map(dims["sap2db"])
    sf = sf[sf["db"].notna() & sf["db"].isin(dbs)].copy()

    # the scope rule needs the canonical number, so it is applied after the supersession step
    doc_out = sf["saty"].isin(EXCLUDE_SATY) | sf["saty"].isna()
    kept = sf[~doc_out].copy()
    excluded = sf[doc_out].copy()
    for f in (kept, excluded):
        f["month"] = f["billing_date"].dt.strftime("%Y-%m")
        f["pn_raw"] = norm(f["part_number"])
        f["ub"] = pd.to_numeric(f["billed_qty"], errors="coerce").fillna(0.0)
        f["eb"] = pd.to_numeric(f["net_sales_value"], errors="coerce").fillna(0.0)
    log(f"   excluded document types {len(excluded):,} rows, EUR {excluded['eb'].sum():,.2f} "
        f"(rule: saty in {', '.join(EXCLUDE_SATY)} or blank)")
    return kept, sf, excluded


def load_dimensions():
    """AIM tree, PMS family, price list, Genuine/BVP, source of supply, distributor map."""
    log("-- dimensions")
    aim = pd.read_csv(AIM_FILE, dtype=str, low_memory=False)
    check_columns(aim, ["part_number", "description", "aim_level_1", "aim_level_2",
                        "aim_level_3", "line_kind"], AIM_FILE)
    aim["pn"] = norm(aim["part_number"])
    aim = aim.drop_duplicates("pn")
    aim["desc"] = aim["description"].fillna("").astype(str).str.strip()
    for lv in ("1", "2", "3"):
        aim[f"a{lv}"] = aim[f"aim_level_{lv}"].fillna("").astype(str).str.strip()
    aim["is_part"] = aim["line_kind"].fillna("").astype(str).str.strip().eq(DROP_LINE_KIND)
    fluids = aim["a1"].str.lower().eq(DROP_AIM_L1.lower()) & aim["is_part"]
    aim["excluded_scope"] = np.where(~aim["is_part"], "not a part line",
                                     np.where(fluids, "lubricant (Fluids Chemicals)", ""))
    keep = aim["excluded_scope"].eq("")
    excl_map = aim.set_index("pn")["excluded_scope"]
    aim_keep = aim[keep].copy()
    log(f"   AIM tree             {len(aim):,} part numbers, dropped by scope "
        f"{int((~keep).sum()):,} ({int((~aim['is_part']).sum()):,} non-part, {int(fluids.sum()):,} "
        f"lubricant)")

    l1_vals = sorted({v for v in aim_keep["a1"].str.lower() if v not in AIM_PLACEHOLDER})
    l2_vals = sorted({v for v in aim_keep["a2"].str.lower() if v not in AIM_PLACEHOLDER})
    l3_vals = sorted({v for v in aim_keep["a3"].str.lower() if v not in AIM_PLACEHOLDER})
    l1_lab, l2_lab, l3_lab = [AIM_NA], [AIM_NA], [AIM_NA]
    l1_map = {AIM_NA.lower(): 0}
    l2_map = {AIM_NA.lower(): 0}
    l3_map = {AIM_NA.lower(): 0}
    for v in l1_vals:
        l1_map[v] = len(l1_lab); l1_lab.append(v.title() if v.islower() else v)
    for v in l2_vals:
        l2_map[v] = len(l2_lab); l2_lab.append(v)
    for v in l3_vals:
        l3_map[v] = len(l3_lab); l3_lab.append(v)
    log(f"   AIM levels           L1 {len(l1_lab)}  L2 {len(l2_lab)}  L3 {len(l3_lab)}")
    aim_keep = aim_keep.assign(
        i1=[l1_map.get(v, 0) for v in aim_keep["a1"].str.lower()],
        i2=[l2_map.get(v, 0) for v in aim_keep["a2"].str.lower()],
        i3=[l3_map.get(v, 0) for v in aim_keep["a3"].str.lower()])

    pc = pd.read_csv(PARTS_FILE, dtype=str, low_memory=False)
    check_columns(pc, ["part_number", "pms_category"], PARTS_FILE)
    pc["pn"] = norm(pc["part_number"])
    pc = pc.drop_duplicates("pn")
    pc["fam"] = pc["pms_category"].map(fam_of)
    fam_map = {f: i for i, f in enumerate(PMS_FAMS)}
    pc["ifam"] = pc["fam"].map(fam_map)
    pc = pc[pc["ifam"].notna()][["pn", "ifam"]]
    pc["ifam"] = pc["ifam"].astype(int)

    bvp = pd.read_csv(BVP_FILE, dtype=str, low_memory=False)
    check_columns(bvp, ["part_number", "line_type"], BVP_FILE)
    bvp["pn"] = norm(bvp["part_number"])
    bvp = bvp.drop_duplicates("pn")
    bvp["ib"] = bvp["line_type"].map({"genuine": 0, "bvp": 1}).fillna(2).astype(int)
    bvp = bvp[["pn", "ib"]]
    log(f"   Genuine/BVP list     {len(bvp):,} part numbers")

    pr = pd.read_parquet(PRICE_FILE)
    check_columns(pr, ["part_number", "newest_pn", "sp_eur"], PRICE_FILE)
    pr["pn"] = norm(pr["part_number"])
    pr["new"] = norm(pr["newest_pn"])
    pr["sp"] = pd.to_numeric(pr["sp_eur"], errors="coerce")
    pr.loc[pr["sp"] <= 0, "sp"] = np.nan          # 0.00 means no price
    pr["desc_price"] = pr["description"].fillna("").astype(str).str.strip()
    pr = pr.drop_duplicates("pn")
    price_map = pr.set_index("pn")["sp"]
    pdesc_map = pr.set_index("pn")["desc_price"]
    sup_map = pr.set_index("pn")["new"]
    log(f"   price list           {len(pr):,} part numbers, "
        f"{int(pr['sp'].notna().sum()):,} with a price above zero")

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
    log(f"   source of supply     {len(src):,} part numbers")

    dd = pd.read_csv(DIM_FILE, dtype=str, low_memory=False)
    check_columns(dd, ["sold_to_sap", "payer_code", "distributor_code", "gps_db_label",
                       "scope", "network_role"], DIM_FILE)
    dd = dd[dd["distributor_code"].notna()].copy()
    dd["sap"] = dd["sold_to_sap"].str.replace(r"\.0$", "", regex=True).str.strip()
    dd = dd.drop_duplicates("sap")
    sap2db = dd.set_index("sap")["distributor_code"].to_dict()
    db_meta = (dd.drop_duplicates("distributor_code")
                 .set_index("distributor_code")[["gps_db_label", "scope"]].to_dict("index"))
    log(f"   distributor map      {len(sap2db)} sold-to codes -> {len(db_meta)} distributors")

    return {"aim": aim_keep, "excl_map": excl_map, "l1": l1_lab, "l2": l2_lab, "l3": l3_lab,
            "pc": pc, "bvp": bvp, "price_map": price_map, "pdesc_map": pdesc_map,
            "sup_map": sup_map, "src": src, "sap2db": sap2db, "db_meta": db_meta,
            "_all_dbs": ALL_DBS}


def canon_pn(series: pd.Series, sup, pns_in_aim: set, priced: set):
    """Newest number where the mapping holds, with the original kept for the tooltip."""
    s = norm(series)
    nw = s.map(sup)
    ok = nw.notna() & nw.ne("") & nw.ne("0") & (nw != s)
    canon = np.where(ok, nw, s)
    old = np.where(ok, s, None)
    return canon, old


def build_facts(sellout, billing, dims, dbs):
    """Supersession, scope filter, month grain, and the union of both stages."""
    log("-- facts at month grain")
    pns_aim = set(dims["aim"]["pn"])
    priced = set(dims["price_map"].dropna().index)
    sup = dims["sup_map"]

    so = sellout.copy()
    so["pn"], so["pn_old"] = canon_pn(so["pn_raw"], sup, pns_aim, priced)
    bi = billing.copy()
    bi["pn"], bi["pn_old"] = canon_pn(bi["pn_raw"], sup, pns_aim, priced)

    aim_scope = dims["excl_map"]
    so["scope_out"] = so["pn"].map(aim_scope).fillna("")
    bi["scope_out"] = bi["pn"].map(aim_scope).fillna("")
    so_out = so[so["scope_out"] != ""]
    bi_out = bi[bi["scope_out"] != ""]
    so = so[so["scope_out"] == ""].copy()
    bi = bi[bi["scope_out"] == ""].copy()
    log(f"   dropped by scope     sold {len(so_out):,} rows / {so_out['us'].sum():,.0f} units  |  "
        f"billed {len(bi_out):,} rows / EUR {bi_out['eb'].sum():,.2f}")

    B = (bi.groupby(["db", "month", "pn"], as_index=False)
           .agg(ub=("ub", "sum"), eb=("eb", "sum")))
    S = (so.groupby(["db", "month", "pn"], as_index=False).agg(us=("us", "sum")))
    facts = B.merge(S, on=["db", "month", "pn"], how="outer")
    facts[["ub", "eb", "us"]] = facts[["ub", "eb", "us"]].fillna(0.0)
    log(f"   billed groups {len(B):,} | sold groups {len(S):,} | union {len(facts):,}")

    olds = {}
    for pn, old in zip(pd.concat([bi["pn"], so["pn"]]),
                       pd.concat([bi["pn_old"], so["pn_old"]])):
        if isinstance(old, str) and old:
            olds.setdefault(pn, set()).add(old)
    olds = {k: sorted(v) for k, v in olds.items()}

    dropped = {
        "sold": {"rows": int(len(so_out)), "units": float(so_out["us"].sum()),
                 "by_reason": {k: float(v) for k, v in
                               so_out.groupby("scope_out")["us"].sum().items()}},
        "billed": {"rows": int(len(bi_out)), "eur": float(bi_out["eb"].sum()),
                   "by_reason": {k: round(float(v), 2) for k, v in
                                 bi_out.groupby("scope_out")["eb"].sum().items()}},
    }
    return facts, olds, dropped, so, bi, so_out, bi_out


def build_pn_dimension(facts, dims, olds):
    """One row per part number in use, with its AIM levels, family, flags and price."""
    aim = dims["aim"].set_index("pn")
    pc = dims["pc"].set_index("pn")["ifam"]
    bvp = dims["bvp"].set_index("pn")["ib"]
    price = dims["price_map"]
    pdesc = dims["pdesc_map"]
    src = dims["src"]
    src_idx = {v: i for i, v in enumerate(SRC_LIST_OUT)}

    pns = sorted(facts["pn"].unique())
    pi = {p: i for i, p in enumerate(pns)}
    n = len(pns)
    log(f"   part numbers in use  {n:,}")

    a1, a2, a3 = [0] * n, [0] * n, [0] * n
    fam, bv, sp, sr = [-1] * n, [2] * n, [None] * n, [2] * n
    de = [""] * n
    for pn, i in pi.items():
        if pn in aim.index:
            r = aim.loc[pn]
            a1[i], a2[i], a3[i] = int(r["i1"]), int(r["i2"]), int(r["i3"])
            de[i] = r["desc"]
        if pn in pc.index:
            fam[i] = int(pc.loc[pn])
        if pn in bvp.index:
            bv[i] = int(bvp.loc[pn])
        if pn in price.index and pd.notna(price.loc[pn]):
            sp[i] = round(float(price.loc[pn]), 2)
        raw = src.get(pn) if hasattr(src, "get") else None
        sr[i] = src_idx.get(SRC_LABELS.get(str(raw)) if raw is not None else None, 2)
        if not de[i] and pn in pdesc.index:
            de[i] = str(pdesc.loc[pn])

    dd, descs, di = {}, [], []
    for d in de:
        if d not in dd:
            dd[d] = len(descs); descs.append(d)
        di.append(dd[d])

    months = sorted(facts["month"].unique())
    dbs = sorted(facts["db"].unique())
    mi = {m: i for i, m in enumerate(months)}
    dbi = {d: i for i, d in enumerate(dbs)}
    rows = [[int(dbi[db]), int(mi[m]), int(pi[p]),
             round(float(ub), 1), round(float(eb), 2), round(float(us), 1)]
            for db, m, p, ub, eb, us in zip(facts["db"], facts["month"], facts["pn"],
                                            facts["ub"], facts["eb"], facts["us"])]
    return {"months": months, "dbs": dbs, "pns": pns, "rows": rows, "desc": di, "descs": descs,
            "a1": a1, "a2": a2, "a3": a3, "fam": fam, "bvp": bv, "sp": sp, "src": sr,
            "old": {str(pi[k]): v[:12] for k, v in olds.items() if k in pi},
            "oldn": {str(pi[k]): len(v) for k, v in olds.items() if k in pi}}


def presence(pn_dim):
    """Which months each distributor carries, per stage."""
    mi = {m: i for i, m in enumerate(pn_dim["months"])}
    out = {}
    for di, db in enumerate(pn_dim["dbs"]):
        s = [0] * len(mi)
        b = [0] * len(mi)
        for r in pn_dim["rows"]:
            if r[0] != di:
                continue
            if r[5] > 0:
                s[r[1]] = 1
            if r[3] > 0:
                b[r[1]] = 1
        out[db] = {"s": s, "b": b}
    return out


# ------------------------------------------------------------------ period pair selection

def sold_runs(pres, db):
    return runs_of([bool(x) for x in pres[db]["s"]])


def _set_min_side(n: int) -> None:
    """Set the shortest window per side the page will draw at all."""
    global MIN_SIDE_MONTHS
    MIN_SIDE_MONTHS = n


def pairs_for_single(months, pres, db):
    """Every honest pair for one distributor: longest equal split first, latest alignment."""
    rr = sorted(sold_runs(pres, db), key=lambda t: -t[1])
    out = []
    if not rr:
        return out
    seen = set()
    for start, length in rr:
        n = length // 2
        if n < MIN_SIDE_MONTHS:
            continue
        alignments = [start + length - 2 * n, start]        # latest, then earliest
        for a0 in alignments:
            if a0 in seen:
                continue
            seen.add(a0)
            out.append({"n": n, "a_from": a0, "b_from": a0 + n,
                        "run_from": start, "run_len": length,
                        "dbs": [db]})
        if len(out) >= MAX_PAIRS:
            break
    return out[:MAX_PAIRS]


def pairs_for_all(months, pres, dbs):
    """Pairs for the combined view.

    Best first, ranked by how many distributors carry the pair, then by the length of the window,
    then by how recent it is. Then, still above the floor: a shorter window that brings more
    distributors in, and the longest pair any single distributor can carry.
    """
    L = len(months)
    cand = []
    for n in range(L // 2, MIN_SIDE_MONTHS - 1, -1):
        for a0 in range(0, L - 2 * n + 1):
            cover = [db for db in dbs if all(pres[db]["s"][j] for j in range(a0, a0 + 2 * n))]
            if cover:
                cand.append({"n": n, "a_from": a0, "b_from": a0 + n, "dbs": cover})
    if not cand:
        return []
    cand.sort(key=lambda c: (-len(c["dbs"]), -c["n"], -c["a_from"]))
    best = cand[0]
    out = [dict(best)]
    for c in cand:                        # shorter window, more distributors
        if len(c["dbs"]) > len(best["dbs"]):
            out.append(dict(c))
            break
    for c in cand:                        # the same distributors at a shorter window, if offered
        if set(c["dbs"]) == set(best["dbs"]) and c["n"] < best["n"]:
            out.append(dict(c))
            break
    singles = [c for c in cand if len(c["dbs"]) == 1]
    if singles:
        out.append(dict(max(singles, key=lambda c: c["n"])))
    seen, uniq = set(), []
    for p in out:
        key = (p["n"], p["a_from"], tuple(sorted(p["dbs"])))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq[:MAX_PAIRS]


def pair_excluded(months, pres, dbs, pair):
    """Which distributors a pair cannot carry, with the reason, so the page names them."""
    out = []
    for db in dbs:
        if db in pair["dbs"]:
            continue
        gap = [months[j] for j in range(pair["a_from"], pair["b_from"] + pair["n"])
               if not pres[db]["s"][j]]
        out.append({"db": db, "months_missing": gap})
    return out


def describe_pair(months, p):
    return {"n": p["n"],
            "a_from": months[p["a_from"]], "a_to": months[p["a_from"] + p["n"] - 1],
            "b_from": months[p["b_from"]], "b_to": months[p["b_from"] + p["n"] - 1],
            "dbs": p["dbs"],
            "n_dbs": len(p["dbs"]),
            "months_a": [months[j] for j in range(p["a_from"], p["a_from"] + p["n"])],
            "months_b": [months[j] for j in range(p["b_from"], p["b_from"] + p["n"])]}


# --------------------------------------------------------------------------- checks

def build_checks(run, pn_dim, pres, recon, sellout_source, billing_source, so_out, bi_out,
                 doc_excl, scope_drop, pairs, html_bytes=None):
    checks = []

    def add(name, expected, actual, ok, note=""):
        checks.append({"name": name, "expected": expected, "actual": actual,
                       "pass": bool(ok), "note": note})

    # 1. month rows against the total row, with the two named exceptions
    for fname, r in sorted(recon.items()):
        same = abs(r["month_rows_qty"] - r["total_row_qty"]) < 0.5
        if fname in RECON_EXCEPTIONS:
            add(f"month rows against the total row: {fname}", r["total_row_qty"],
                r["month_rows_qty"], True, RECON_EXCEPTIONS[fname])
        elif not r["total_row_periods"]:
            add(f"month rows against the total row: {fname}", "no total row in the file",
                r["month_rows_qty"], True, "the file carries month rows only")
        else:
            add(f"month rows equal the total row: {fname}", r["total_row_qty"],
                r["month_rows_qty"], same,
                "" if same else "the total row must never be added to the month rows")

    # the two exceptions the brief names, asserted by value rather than by description
    uti = recon.get("dealer_sellout_long_UTI_CY2025.csv")
    if uti is not None:
        add("UTI 2025: year row 92,660 against month rows 55,570",
            92660.0, uti["total_row_qty"], abs(uti["total_row_qty"] - 92660.0) < 0.5,
            f"month rows {uti['month_rows_qty']:,.0f}; the brief states 55,570, measured "
            f"{uti['month_rows_qty']:,.0f}")
    itd = recon.get("dealer_sellout_long_ITUK_CY2025.csv")
    if itd is not None:
        add("ITUK dealer-level 2025: year row 224,001 against month rows 223,897",
            224001.0, itd["total_row_qty"], abs(itd["total_row_qty"] - 224001.0) < 0.5,
            f"month rows {itd['month_rows_qty']:,.0f}; this file is not a basis for network "
            f"totals, it is only the dealer cut")

    # 2. the longest contiguous sales-to-dealer run per distributor, and the pair it gives
    for db in pn_dim["dbs"]:
        rr = sorted(sold_runs(pres, db), key=lambda t: -t[1])
        if not rr:
            add(f"longest unbroken sales-to-dealer run: {db}", "no months", 0, False,
                "no sales-to-dealer months at all")
            continue
        st, ln = rr[0]
        n = ln // 2
        add(f"longest unbroken sales-to-dealer run: {db}", "reported, not a gate",
            f"{ln} months, {pn_dim['months'][st]} to {pn_dim['months'][st + ln - 1]}, "
            f"longest equal split {n} against {n}", True, "reported, not a gate")

    # 2b. the same for the both-stage run, which is what the brief measured against. The page
    # ranks on sales to dealer, so this is reported for comparison rather than used as the rule.
    for db in pn_dim["dbs"]:
        both = [1 if (pres[db]["b"][j] and pres[db]["s"][j]) else 0
                for j in range(len(pn_dim["months"]))]
        rr = sorted(runs_of([bool(x) for x in both]), key=lambda t: -t[1])
        if not rr:
            add(f"longest unbroken both-stage run: {db}", "reported, not a gate",
                "no month carries both stages", True, "reported, not a gate")
            continue
        st, ln = rr[0]
        add(f"longest unbroken both-stage run (ISZE billing and sales to dealer together): {db}",
            "reported, not a gate",
            f"{ln} months, {pn_dim['months'][st]} to {pn_dim['months'][st + ln - 1]}, "
            f"longest equal split {ln // 2} against {ln // 2}", True,
            "reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of "
            "April to June 2026 do not decide the period pair; they only shorten this second run")

    # 3. every selected pair must be carried by 2N contiguous months of sales-to-dealer data
    for p in pairs:
        for db in p["dbs"]:
            ok = all(pres[db]["s"][j] for j in range(p["a_from"], p["b_from"] + p["n"]))
            add(f"pair is carried by 2N contiguous months: {db} "
                f"{pn_dim['months'][p['a_from']]}..{pn_dim['months'][p['b_from']+p['n']-1]}",
                "2N contiguous months present", f"{2 * p['n']} months", ok)

    # 4. units and euro per period reconcile to the source rows for the selected distributor
    dbs = pn_dim["dbs"]
    for p in pairs[:1]:
        for db in p["dbs"]:
            a, b = p["a_from"], p["b_from"]
            src = sorted(set(range(a, a + p["n"])) | set(range(b, b + p["n"])))
            src_months = [pn_dim["months"][j] for j in src]
            src_units = float(sellout_source[(sellout_source["db"] == db) &
                                             (sellout_source["month"].isin(src_months))]["us"].sum())
            pay_units = 0.0
            for r in pn_dim["rows"]:
                if dbs[r[0]] == db and r[1] in src:
                    pay_units += r[5]
            drop_units = float(so_out[(so_out["db"] == db) &
                                      (so_out["month"].isin(src_months))]["us"].sum())
            add(f"units reconcile to the sales-to-dealer rows: {db} "
                f"{pn_dim['months'][a]}..{pn_dim['months'][b + p['n'] - 1]}",
                round(src_units, 1), round(pay_units + drop_units, 1),
                abs(src_units - pay_units - drop_units) < 0.5,
                f"on the page {pay_units:,.1f} units + {drop_units:,.1f} units dropped by the "
                f"scope rule (non-part lines and lubricants) = {src_units:,.1f} source units" +
                (f". {db} reports part of its sales to dealer in half units; they are kept as "
                 f"reported rather than rounded, so the figures still sum to the source"
                 if int(round(src_units)) != src_units or
                 float(sellout_source[sellout_source["db"] == db]["us"].mod(1).sum()) else ""))

    # 5. shares per period: units not in AIM, units with no list price
    for p in pairs[:1]:
        for label, span in (("period A", range(p["a_from"], p["a_from"] + p["n"])),
                            ("period B", range(p["b_from"], p["b_from"] + p["n"]))):
            tot = no_aim = no_price = 0.0
            for r in pn_dim["rows"]:
                if r[1] in span and r[5] > 0:
                    tot += r[5]
                    if pn_dim["a1"][r[2]] == 0:
                        no_aim += r[5]
                    if pn_dim["sp"][r[2]] is None:
                        no_price += r[5]
            add(f"sales to dealer, {label}: units not classified in AIM",
                "reported, not a gate", f"{100*no_aim/tot:.2f}% of {tot:,.0f} units"
                if tot else None, True, "reported, not a gate")
            add(f"sales to dealer, {label}: units with no price on the list",
                "reported, not a gate", f"{100*no_price/tot:.2f}% of {tot:,.0f} units"
                if tot else None, True, "reported, not a gate")

    # 6. the growth and decline euro sums back to the total movement, computed two ways
    for p in pairs[:1]:
        span_a = set(range(p["a_from"], p["a_from"] + p["n"]))
        span_b = set(range(p["b_from"], p["b_from"] + p["n"]))
        per_pn = {}
        for r in pn_dim["rows"]:
            pn = r[2]
            sp = pn_dim["sp"][pn]
            if sp is None:
                continue
            cur = per_pn.setdefault(pn, [0.0, 0.0])
            if r[1] in span_a:
                cur[0] += r[5] * sp
            elif r[1] in span_b:
                cur[1] += r[5] * sp
        deltas = [b_ - a_ for a_, b_ in per_pn.values()]
        up = sum(d for d in deltas if d > 0)
        down = sum(d for d in deltas if d < 0)
        sum_a = sum(a_ for a_, _ in per_pn.values())
        sum_b = sum(b_ for _, b_ in per_pn.values())
        add("the growth and decline euro sums back to the movement between the two period totals",
            round(sum_b - sum_a, 2), round(up + down, 2),
            abs(up + down - (sum_b - sum_a)) < 0.05,
            f"{up:,.2f} up and {down:,.2f} down across {len(per_pn):,} priced part numbers. The "
            f"right-hand figure is the difference between the two period totals read straight from "
            f"the periods, so nothing is lost between the two ranked lists. The tolerance is five "
            f"cents, which is the rounding the page carries at this size")

        # the drill must conserve the euro: the children of a group have to add back to the group
        for lv, child in ((1, 2), (2, 3), (3, None)):
            parent_arr = pn_dim[f"a{lv}"]
            kids = {}
            for pn, d in ((pn, b_ - a_) for pn, (a_, b_) in per_pn.items()):
                key = parent_arr[pn]
                if child is not None:
                    kids.setdefault(key, {})
                    k2 = pn_dim[f"a{child}"][pn]
                    kids[key][k2] = kids[key].get(k2, 0.0) + d
            worst, worst_key = 0.0, None
            for key, sub in kids.items():
                parent_total = sum(b_ - a_ for pn, (a_, b_) in per_pn.items()
                                   if parent_arr[pn] == key)
                gap = abs(sum(sub.values()) - parent_total)
                if gap > worst:
                    worst, worst_key = gap, key
            label = {1: "AIM level 1 group against its level 2 groups",
                     2: "level 2 group against its level 3 groups",
                     3: "level 3 group against its part numbers"}[lv]
            add(f"the drill conserves the euro: {label}", 0.0, round(worst, 2), worst < 0.05,
                "opening a bar must not lose or double count any euro; the largest gap found "
                f"across all groups is {worst:.4f} euro"
                + (f" (in group {worst_key})" if worst_key is not None else ""))

    # 7. no NaN can reach the embedded data
    bad = 0
    for r in pn_dim["rows"]:
        for v in r:
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                bad += 1
    add("no NaN or infinity in the embedded rows", 0, bad, bad == 0)
    for k, v in (("a1", pn_dim["a1"]), ("sp", pn_dim["sp"]), ("fam", pn_dim["fam"]),
                 ("bvp", pn_dim["bvp"]), ("src", pn_dim["src"])):
        bad = sum(1 for x in v if isinstance(x, float) and (np.isnan(x) or np.isinf(x)))
        add(f"no NaN or infinity in the part-number dimension: {k}", 0, bad, bad == 0)

    # 8. scope and document-type exclusions, reported
    add("ISZE billing euro excluded by document type", "reported, not a gate",
        round(float(doc_excl["eb"].sum()), 2), True,
        f"{len(doc_excl):,} rows, saty in {', '.join(EXCLUDE_SATY)} or blank")
    frac = sellout_source[sellout_source["us"] % 1 != 0]
    add("sales to dealer reported in half units", "reported, not a gate",
        f"{len(frac):,} rows", True,
        ("IUK is the only distributor that reports part of its sales to dealer in half units, "
         "and they are kept as reported so the figures still sum to the source. By distributor: "
         + "; ".join(f"{k}: {v:,}" for k, v in
                     frac.groupby("db").size().items())) if len(frac) else "none")
    add("sales to dealer units dropped by the scope rule (lubricants and non-part lines)",
        "reported, not a gate", round(float(so_out["us"].sum()), 0), True,
        "; ".join(f"{k}: {v:,.0f}" for k, v in scope_drop["sold"]["by_reason"].items()) or "none")
    add("ISZE billing euro dropped by the scope rule", "reported, not a gate",
        round(float(bi_out["eb"].sum()), 2), True,
        "; ".join(f"{k}: {v:,.2f}" for k, v in scope_drop["billed"]["by_reason"].items())
        or "none")

    if html_bytes is not None:
        add("HTML file size", "under 15 MB", round(html_bytes / 1024 / 1024, 2),
            html_bytes < 15 * 1024 * 1024,
            "MB; self-contained, data and Chart.js inline, no server and no internet")
    return checks


# --------------------------------------------------------------------------- payload

OPEN_QUESTIONS = [
    "The 35% gross margin on sales to dealer is an assumption supplied by Jerome, applied as "
    "list / 0.65 because margin is measured on the selling price. If he meant margin on cost "
    "(list x 1.35) the figure is about 14% lower. It is a modelled dealer price, not the "
    "distributor's turnover, its revenue, or an actual dealer purchase price.",
    "The shortest window per side the page will draw at all is three months. That floor is a "
    "judgement made in this build. If a shorter window should be allowed, it changes only which "
    "pairs appear in the control; the default pair, which is always the longest equal split, would "
    "not move.",
    "For the all-distributors view the default pair is the one that covers the most distributors, "
    "and ties are broken toward the longer window and then the more recent one. The other "
    "candidate pairs are in the control.",
    "Sales to dealer has no price of its own. Both periods are valued on the same ISZE price list "
    "of 10 Aug 2026, so a price change inside the comparison window is not visible in it.",
    "ITUK's sales-to-dealer history starts in January 2023, so its longest equal split is "
    "twenty-two months against twenty-two. If a shorter window is wanted for ITUK, the pair "
    "control allows it.",
    "In the all-distributors view the scopes differ between distributors: ITUK is commercial "
    "vehicles only, IUK and Greece are D-Max only, and the rest are the whole network. Adding "
    "them together mixes those scopes, which the page states rather than hides.",
]

SOURCES = [
    {"what": "Sales to dealer, the basis for the ranking",
     "path": r"01_data\00_derived\dealer_sellout_long_<distributor>_<period>.csv",
     "note": "month rows only; the total rows in these files are the same data added up again, so "
             "they are never used"},
    {"what": "ISZE billing, shown beside the movement as context",
     "path": r"01_data\00_derived\sales_fact.parquet",
     "note": "credit notes, returns, debit notes and free deliveries excluded; 3 January 2023 to "
             "31 August 2026"},
    {"what": "AIM product tree",
     "path": r"01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260921.csv",
     "note": "165,213 rows, about 24,756 with an AIM level; a part number with no level sits in a "
             "bucket called Not classified in AIM at all three levels"},
    {"what": "PMS family per part number",
     "path": r"01_data\00_derived\parts_catalog_dimension.csv",
     "note": "the front and rear brake pad variants are folded into one family, as are the brake "
             "shoe and lining variants"},
    {"what": "Price list used to value sales to dealer",
     "path": r"01_data\00_derived\pricing_pr00_ie40.parquet",
     "note": PRICE_LIST_LABEL + "; a price of 0.00 means no price and is treated as missing"},
    {"what": "Supersession, part number to newest number",
     "path": r"01_data\00_derived\pricing_pr00_ie40.parquet",
     "note": "applied on both periods before grouping, then the AIM tree and the price are looked "
             "up on the newest number; the old numbers appear on the part-number row"},
    {"what": "Genuine / BVP flag",
     "path": r"01_data\00_derived\bvp_pn_dimension.csv",
     "note": "919 part numbers; anything outside the list is labelled as such"},
    {"what": "Source of supply",
     "path": r"01_data\00_derived\pricing_sim_pr00_l12m.parquet, "
             r"01_data\00_derived\pricing_list_pn.parquet",
     "note": "J = Japan through IML, T = Thailand through IMIT; where it is not held the row is "
             "kept and labelled"},
    {"what": "Distributor names and scope",
     "path": r"01_data\00_derived\distributor_dimension.csv",
     "note": "joined on the sold-to code, never on the payer code; Portugal is sold-to 519 and 92 "
             "added together"},
]


def build_payload(run, dims, pn_dim, pres, pairs, recon, coverage, scope_drop, doc_excl,
                  open_q, html_bytes, views, half_units=None):
    dbs = pn_dim["dbs"]
    # the half-unit sources, so the page can state which distributor reports them
    return {
        "run": run,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": "Sales to dealer, period against period, from AIM level 1 to part number",
        "price_list_label": PRICE_LIST_LABEL,
        "gm_divisor": GM_DIVISOR,
        "min_side_months": MIN_SIDE_MONTHS,
        "months": pn_dim["months"],
        "views": views,
        "dbs": [{"code": d,
                 "label": dims["db_meta"].get(d, {}).get("gps_db_label") or d,
                 "scope": dims["db_meta"].get(d, {}).get("scope") or "",
                 "sold_scope": SELLOUT.get(d, {}).get("scope", ""),
                 "sold_scope_note": SELLOUT.get(d, {}).get("scope_note", ""),
                 "sold_months": int(sum(pres[d]["s"])),
                 "billed_months": int(sum(pres[d]["b"])),
                 "sold_presence": pres[d]["s"],
                 "billed_presence": pres[d]["b"]}
                for d in dbs],
        "aim": {"l1": dims["l1"], "l2": dims["l2"], "l3": dims["l3"]},
        "pms": {"fams": PMS_FAMS, "labels": PMS_LABELS},
        "src": SRC_LIST_OUT,
        "bvp": BVP_LIST_OUT,
        "pn": {"n": pn_dim["pns"], "d": pn_dim["desc"], "descs": pn_dim["descs"],
               "l1": pn_dim["a1"], "l2": pn_dim["a2"], "l3": pn_dim["a3"],
               "f": pn_dim["fam"], "b": pn_dim["bvp"], "s": pn_dim["src"], "p": pn_dim["sp"],
               "o": pn_dim["old"], "oc": pn_dim["oldn"]},
        "facts": pn_dim["rows"],
        "pairs": {k: [dict(describe_pair(pn_dim["months"], p),
                           excluded=pair_excluded(pn_dim["months"], pres, dims["_all_dbs"], p))
                      for p in v] for k, v in pairs.items()},
        "coverage": coverage,
        "half_units": half_units or [],
        "excluded": {"doc_types": {"rule": "saty in " + ", ".join(EXCLUDE_SATY) + " or blank",
                                   "rows": int(len(doc_excl)),
                                   "eur": round(float(doc_excl["eb"].sum()), 2),
                                   "by_db": {k: round(float(v), 2) for k, v in
                                             doc_excl.groupby("db")["eb"].sum().items()}},
                     "scope": scope_drop},
        "recon": recon,
        "open_questions": open_q,
        "sources": SOURCES,
    }


def render_html(payload, run):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    data_json = json.dumps(payload, separators=(",", ":"), default=str)
    data_json = data_json.replace("</", "<\\/").replace("<!--", "<\\!--")
    chart_js = CHART_JS.read_text(encoding="utf-8")
    title = ("AIM comparison - Portugal (I Motors)" if run == "PORTUGAL"
             else "AIM comparison - all distributors with sales-to-dealer data")
    return (tpl.replace("/*__CHART_JS__*/", chart_js)
               .replace("__DATA_JSON__", data_json)
               .replace("__PAGE_TITLE__", title)
               .replace("__RUN__", run))


def build_half_units(sellout):
    """Which distributors report sales to dealer in half units, and how many rows."""
    frac = sellout[sellout["us"] % 1 != 0]
    if not len(frac):
        return []
    return [{"db": k, "rows": int(v)} for k, v in frac.groupby("db").size().items()]


def coverage_rows(pn_dim, pres, dims, pairs):
    out = []
    for db in pn_dim["dbs"]:
        rr = sorted(sold_runs(pres, db), key=lambda t: -t[1])
        span = (f"{pn_dim['months'][rr[0][0]]} to "
                f"{pn_dim['months'][rr[0][0] + rr[0][1] - 1]}") if rr else "-"
        long = max((p["n"] for p in pairs.get(db, [])), default=0)
        out.append({
            "db": db,
            "label": dims["db_meta"].get(db, {}).get("gps_db_label") or db,
            "scope": dims["db_meta"].get(db, {}).get("scope") or "",
            "sold_scope": SELLOUT.get(db, {}).get("scope", ""),
            "sold_scope_note": SELLOUT.get(db, {}).get("scope_note", ""),
            "sold_months": int(sum(pres[db]["s"])),
            "billed_months": int(sum(pres[db]["b"])),
            "run_months": rr[0][1] if rr else 0,
            "run_span": span,
            "max_n": rr[0][1] // 2 if rr else 0,
            "offers": bool(rr and rr[0][1] // 2 >= MIN_SIDE_MONTHS),
            "longest_pair_n": long,
            "sold_missing_where_billed": [pn_dim["months"][j]
                                          for j in range(len(pn_dim["months"]))
                                          if pres[db]["b"][j] and not pres[db]["s"][j]],
        })
    return out


# --------------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", required=True, choices=["PORTUGAL", "ALL"])
    ap.add_argument("--min-side", type=int, default=MIN_SIDE_MONTHS)
    args = ap.parse_args(argv)
    _set_min_side(min(args.min_side, 12))
    run = args.db
    dbs = ["PORTUGAL"] if run == "PORTUGAL" else ALL_DBS
    log(f"== AIM comparison, run {run}, distributors: {', '.join(dbs)}")

    try:
        for p, what in ((AIM_FILE, "AIM tree"), (PARTS_FILE, "PMS catalog"),
                        (PRICE_FILE, "price list"), (BVP_FILE, "Genuine/BVP list"),
                        (DIM_FILE, "distributor dimension"), (SALES_FACT, "sales fact"),
                        (TEMPLATE, "page template"), (CHART_JS, "Chart.js")):
            require(p, what)

        dims = load_dimensions()
        dims["_all_dbs"] = list(dbs)
        sellout, recon = load_sellout(dbs)
        billing, _, doc_excl = load_billing(dims, dbs)
        facts, olds, scope_drop, so_kept, bi_kept, so_out, bi_out = build_facts(
            sellout, billing, dims, dbs)
        pn_dim = build_pn_dimension(facts, dims, olds)
        pres = presence(pn_dim)

        log("-- period pairs")
        all_pairs = {}
        for db in pn_dim["dbs"]:
            all_pairs[db] = pairs_for_single(pn_dim["months"], pres, db)
            rr = sorted(sold_runs(pres, db), key=lambda t: -t[1])
            log(f"   {db:<9} {sum(pres[db]['s'])} sales-to-dealer months, longest unbroken run "
                f"{rr[0][1] if rr else 0} months "
                f"({pn_dim['months'][rr[0][0]]} to "
                f"{pn_dim['months'][rr[0][0]+rr[0][1]-1] if rr else '-'}), "
                f"pairs offered {len(all_pairs[db])}")
        all_pairs["ALL"] = (pairs_for_all(pn_dim["months"], pres, dims["_all_dbs"])
                            if run == "ALL" else [])
        if run == "ALL":
            log(f"   ALL combined pairs offered: {len(all_pairs['ALL'])}")
        if not all_pairs[run]:
            raise BuildError(
                f"{run} cannot carry any comparison: no unbroken run of "
                f"{2 * MIN_SIDE_MONTHS} sales-to-dealer months exists. No HTML written, so the "
                f"page cannot suggest a comparison the data does not support.")
        dbs = ["ALL"] + pn_dim["dbs"] if run == "ALL" else list(pn_dim["dbs"])
        pairs = {k: all_pairs[k] for k in dbs}
        p0 = pairs[run][0]
        log(f"   default pair: {pn_dim['months'][p0['a_from']]} to "
            f"{pn_dim['months'][p0['b_from'] + p0['n'] - 1]} "
            f"({p0['n']} against {p0['n']}), distributors {', '.join(p0['dbs'])}")

        coverage = coverage_rows(pn_dim, pres, dims, pairs)

        log("-- verification")
        checks = build_checks(run, pn_dim, pres, recon, sellout, billing, so_out, bi_out,
                              doc_excl, scope_drop, pairs[run])
        failed = [c for c in checks if not c["pass"]]
        if failed:
            for c in failed:
                log(f"   FAIL {c['name']}: expected {c['expected']}, got {c['actual']}")
            raise BuildError(f"{len(failed)} verification check(s) failed. No HTML written.")
        log(f"   all {len(checks)} checks pass")

        scope_notes = {d: (SELLOUT.get(d, {}).get("scope", "") + " sales to dealer; ISZE billing "
                           "scope " + (dims["db_meta"].get(d, {}).get("scope") or "not stated"))
                       for d in pn_dim["dbs"]}
        views = []
        if run == "ALL":
            views.append({"code": "ALL", "label": "All distributors with sales-to-dealer data",
                          "scope_label": "CV / D-Max / mixed, read per distributor below",
                          "sold_months": int(max(sum(pres[d]["s"]) for d in pn_dim["dbs"]))})
        for d in pn_dim["dbs"]:
            views.append({"code": d,
                          "label": dims["db_meta"].get(d, {}).get("gps_db_label") or d,
                          "scope_label": scope_notes[d],
                          "sold_months": int(sum(pres[d]["s"]))})

        payload = build_payload(run, dims, pn_dim, pres, pairs, recon, coverage, scope_drop,
                                doc_excl, OPEN_QUESTIONS, None, views,
                                half_units=build_half_units(sellout))
        html = render_html(payload, run)
        out = DASH / f"ISZE_AIM_Comparison_{run}.html"
        out.write_text(html, encoding="utf-8")
        size = out.stat().st_size
        log(f"   wrote {out} ({size/1024/1024:.2f} MB)")

        cmd = DASH / f"OPEN_ISZE_AIM_Comparison_{run}.cmd"
        cmd.write_bytes((f'@echo off\nstart "" "%~dp0{out.name}"\n').replace("\n", "\r\n")
                        .encode("ascii"))
        log(f"   wrote {cmd.name} (CRLF, opens {out.name})")

        # rewrite once more so the page carries its own final size in the checks
        checks2 = build_checks(run, pn_dim, pres, recon, sellout, billing, so_out, bi_out,
                               doc_excl, scope_drop, pairs[run], html_bytes=size)
        payload = build_payload(run, dims, pn_dim, pres, pairs, recon, coverage, scope_drop,
                                doc_excl, OPEN_QUESTIONS, size, views,
                                half_units=build_half_units(sellout))
        out.write_text(render_html(payload, run), encoding="utf-8")
        size = out.stat().st_size
        checks2 = build_checks(run, pn_dim, pres, recon, sellout, billing, so_out, bi_out,
                               doc_excl, scope_drop, pairs[run], html_bytes=size)
        log(f"   final size {size/1024/1024:.2f} MB")

        write_verify(run, checks2, {
            "default_pair": describe_pair(pn_dim["months"], p0),
            "pairs_offered": {k: [describe_pair(pn_dim["months"], p) for p in v]
                              for k, v in pairs.items()},
            "coverage": coverage,
            "reconciliation_month_rows_vs_total_rows": recon,
            "open_questions": OPEN_QUESTIONS,
        })
        return 0

    except BuildError as exc:
        log(f"BUILD FAILED: {exc}")
        return 2


def write_verify(run, checks, extra):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    failed = [c for c in checks if not c["pass"]]
    doc = {"run": run, "built": stamp, "passed": len(checks) - len(failed),
           "failed": len(failed), "checks": checks}
    doc.update(extra)
    (TOOL / f"VERIFY_COMPARISON_{run}.json").write_text(
        json.dumps(doc, indent=2, default=str), encoding="utf-8")

    lines = [f"# Verification - AIM comparison, {run}", "",
             f"Built {stamp}. {len(checks) - len(failed)} of {len(checks)} checks pass.", ""]
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
        note = (c.get("note") or "").replace("|", "/").replace("\n", " ")
        lines.append(f"| {c['name']} | {c.get('expected')} | {c.get('actual')} | "
                     f"{'PASS' if c['pass'] else 'FAIL'} | {note} |")
    lines.append("")
    for key, val in extra.items():
        lines += [f"## {key}", "", "```json", json.dumps(val, indent=2, default=str), "```", ""]
    (TOOL / f"VERIFY_COMPARISON_{run}.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
