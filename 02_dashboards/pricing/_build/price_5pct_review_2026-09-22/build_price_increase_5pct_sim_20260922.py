#!/usr/bin/env python3
"""
ISZE +5% flat price-increase SIMULATION - 2026-09-22.

WHAT THIS IS
------------
A paper exercise. It computes what a flat +5% on the current list does, weighted on the
volume actually billed, so it can be read beside the already-filed revision.

It is NOT a price change. Nothing is published, nothing is mailed, no live list, price file
or pricing configuration is touched. This run writes new, dated files only.

RELATION TO THE 2026-09-17 RUN
------------------------------
Same basis, same mask, same builder logic as
    02_dashboards/pricing/_build/price_5pct_review_2026-09-17/build_price_increase_5pct_review.py
This run is the refresh Jerome asked for on 2026-09-22 and it re-states the 17 Sep figures
beside the recomputed ones so any difference is visible rather than asserted away.

READ-ONLY INPUTS
----------------
    01_data/00_derived/price_bp_weighted_compare_pn.csv   the in-scope L12M revision base
    01_data/00_derived/aim_master_v2.csv                  corrected AIM levels
    01_data/00_derived/pricing_list_pn.parquet          source of supply (J / T) per part number
    02_dashboards/_ui/chart.umd.min.js                   inlined Chart.js
Nothing else is read, and nothing that is read is written.

BASIS - stated once, used everywhere
------------------------------------
  source    price_bp_weighted_compare_pn.csv, filter in_scope == True
  window    2025-07-01 .. 2026-06-30 (L12M)
  billed    EUR 34,993,609.39 over 48,653 lines and 15,872 part numbers
  the +5%   a flat 5.000% applied to the current base price on every movable line

Two things are kept strictly apart and are never added:
  * the +5% flat proposal  - this page
  * the filed revision     - already published, measured at +5.9616%
They are two separate readings of one base, not two components of one increase.

Run: python 02_dashboards/pricing/_build/price_5pct_review_2026-09-22/build_price_increase_5pct_sim_20260922.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- paths
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"

STAMP = "2026-09-22"
PRIOR_STAMP = "2026-09-17"
HERE = ISZE / "02_dashboards" / "pricing" / "_build" / f"price_5pct_review_{STAMP}"

PN_CSV = DERIVED / "price_bp_weighted_compare_pn.csv"
AIM_CSV = DERIVED / "aim_master_v2.csv"
SRC_PARQUET = DERIVED / "pricing_aim_source_lines.parquet"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"

OUT_JSON = HERE / f"price_increase_5pct_sim_summary_{STAMP}.json"
OUT_XLSX = ISZE / "01_data" / "01_Pricing" / f"Price_Increase_5pct_Flat_SIMULATION_{STAMP}.xlsx"
OUT_HTML = ISZE / "02_dashboards" / "pricing" / f"ISZE_Price_Increase_5pct_Flat_SIMULATION_{STAMP}.html"

# ---------------------------------------------------------------- constants
RATE = 0.05                 # the flat increase under review
RATE_PUBLISHED = 0.059616   # what the in-scope revision actually did, for comparison

# What the 17 Sep 2026 run reported. Repeated here so the refresh can be compared, not asserted.
PRIOR = {
    "lines": 48_653,
    "part_numbers": 15_872,
    "billed_eur": 34_993_609.39,
    "step_5pct_all_eur": 1_749_680.47,
    "step_5pct_movable_eur": 1_629_792.63,
    "step_filed_eur": 1_652_140.71,
    "rate_filed_pct": 5.9616,
    "movable_lines": 47_617,
    "movable_billed_eur": 32_595_852.63,
    "immovable_lines": 1_036,
    "immovable_billed_eur": 2_397_756.76,
}

# Market masks, copied verbatim from 01_data/91_build/apply_pricing_stack_20260919.py so the
# market codes here are the same four the published per-market figures use.
PR00_REGIONS = ("WEST", "SOUTH", "EAST", "NORDICS", "MIDDLE_EAST")
MARKETS = [
    ("PR00", "Main EU distributor list (WEST / SOUTH / EAST / NORDICS / MIDDLE_EAST regions)."),
    ("UTI", "Israel, sold-to 1799. Never combined with UMI."),
    ("UMI", "Israel, sold-to 1797. Never combined with UTI."),
    ("CIS", "GA Armenia and CBC Kazakhstan."),
]

NA = "Not on AIM spine"
PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None", "NaN"}

SUB_REASON = {
    631: "Has a new base price but no prior base price (nothing to lift from)",
    140: "Has a prior base price but no new base price (nothing was revised)",
    239: "No base price on either side (not in either price list)",
}


def money(x: float) -> float:
    return round(float(x), 2)


def market_mask(df: pd.DataFrame, code: str) -> pd.Series:
    if code == "PR00":
        return df["region"].isin(PR00_REGIONS)
    if code == "UTI":
        return df["customer_code"].astype(str).str.strip().eq("1799")
    if code == "UMI":
        return df["customer_code"].astype(str).str.strip().eq("1797")
    return df["region"].eq("CIS")


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)

    # ---- load the basis -------------------------------------------------
    df = pd.read_csv(PN_CSV, dtype={"part_number": str, "customer_code": str})
    d = df[df["in_scope"] == True].copy()  # noqa: E712 - the column is boolean

    billed = float(d["net_sales_value"].sum())
    step_filed = float(d["value_eur_step"].sum())
    lines = len(d)
    pns = int(d["part_number"].nunique())

    # ---- the published index recipe, reproduced ------------------------
    rec = d[d["unpriced_reason"].isna()].copy()
    rec["weight"] = rec["billed_qty"] * rec["bp_prior_revised"]
    rec["step_yen"] = rec["billed_qty"] * rec["delta_jpy"]
    index_published = float(rec["step_yen"].sum() / rec["weight"].sum())
    assert abs(index_published - RATE_PUBLISHED) < 1e-6, index_published

    # ---- movability ----------------------------------------------------
    # A line can take a NEW price change only if it already carries a price on both sides of
    # the revision. An earlier build used `value_eur_step != 0`, which wrongly excluded 611
    # lines that carry a price on both sides and simply did not move last time. A new flat
    # +5% WOULD move them. The corrected mask is used here (same as the 17 Sep correction).
    has_new = d["bp_new_jpy"].notna()
    has_prior = d["bp_prior_revised"].notna()
    movable = has_new & has_prior
    # Held as a column so later joins (which reset the index) cannot misalign the mask.
    d["movable"] = movable.values
    only_new = has_new & ~has_prior
    only_prior = ~has_new & has_prior
    neither = ~has_new & ~has_prior

    movable_lines = int(movable.sum())
    movable_billed = float(d.loc[movable, "net_sales_value"].sum())
    immovable_lines = int((~movable).sum())
    immovable_billed = float(d.loc[~movable, "net_sales_value"].sum())

    # ---- the +5% flat step ---------------------------------------------
    d["step_5pct_eur"] = d["net_sales_value"].astype(float) * RATE
    step_5pct_all = float(d["step_5pct_eur"].sum())
    step_5pct_movable = movable_billed * RATE
    # A single flat rate makes the euro-weighted move equal the rate itself. Asserted.
    assert abs(step_5pct_all / billed - RATE) < 1e-12

    imm_group = (
        d.loc[~movable]
        .groupby(d.loc[~movable, "unpriced_reason"].fillna("(blank)"))
        .agg(lines=("part_number", "size"), billed=("net_sales_value", "sum"))
        .reset_index()
        .sort_values("billed", ascending=False)
    )
    immovable_composition = [
        {
            "reason": str(r.unpriced_reason),
            "lines": int(r.lines),
            "billed_eur": money(r.billed),
            "share_of_in_scope_billed_pct": round(r.billed / billed * 100.0, 2),
            "step_5pct_eur_if_it_could_move": money(r.billed * RATE),
        }
        for r in imm_group.itertuples()
    ]

    # Per-line diagnosis of the real blocker on each immovable line. This is what shows why
    # the 17 Sep "1,647 lines / EUR 4.48M" reading was wrong rather than merely different.
    sub_masks = [
        {
            "sub_reason": "Has a new price but no prior price",
            "lines": int(only_new.sum()),
            "billed_eur": money(d.loc[only_new, "net_sales_value"].sum()),
        },
        {
            "sub_reason": "Has a prior price but no new price",
            "lines": int(only_prior.sum()),
            "billed_eur": money(d.loc[only_prior, "net_sales_value"].sum()),
        },
        {
            "sub_reason": "No price on either side",
            "lines": int(neither.sum()),
            "billed_eur": money(d.loc[neither, "net_sales_value"].sum()),
        },
    ]
    assert sum(s["lines"] for s in sub_masks) == immovable_lines
    assert abs(sum(s["billed_eur"] for s in sub_masks) - immovable_billed) < 0.01

    # ---- named rate bases (same three the policy paper names) -----------
    m = d.loc[movable]
    qty = m["billed_qty"].fillna(0)
    rate_sim_qty = float((m["delta_pct"].fillna(0) * qty).sum() / qty.sum())
    rate_euro_wt = float(
        (m["delta_pct"].fillna(0) * m["net_sales_value"]).sum() / m["net_sales_value"].sum()
    )
    rate_step_on_priced = float(m["value_eur_step"].sum() / m["net_sales_value"].sum())

    # ---- source of supply (Japan / Thailand) ----------------------------
    # The published per-source figures (+6.2081% Japan / +6.3088% Thailand / +3.0601% unlabelled)
    # come from `pricing_list_pn.parquet` with the source column carrying J / T, superseded rows
    # dropped, one row per part number. That file was verified to reproduce the published split
    # exactly, and it is used here rather than the aim-source parquet, which labels the same parts
    # with the longer strings.
    pl = pd.read_parquet(
        DERIVED / "pricing_list_pn.parquet", columns=["part_number", "source", "is_superseded_row"]
    )
    pl = pl[pl["is_superseded_row"] != True]  # noqa: E712
    pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
    pl = pl.drop_duplicates("pn")[["pn", "source"]]

    d["pn"] = d["part_number"].astype(str).str.strip().str.zfill(10)
    d = d.merge(pl, on="pn", how="left")
    d["srclab"] = d["source"].where(d["source"].isin(["J", "T"]), "(none)")
    d["src_label"] = d["srclab"].map(
        {"J": "Japan (IML)", "T": "Thailand (IMIT)", "(none)": "No source label"}
    )

    # Tie-out: the movable rows must reproduce the published per-source split, or this page would
    # be reporting a different source attribution from the one already on record.
    _mvm = d[d["movable"] == True]  # noqa: E712
    for _s, _rows, _eur, _pct in (
        ("J", 22_731, 15_401_370.75, 6.2081),
        ("T", 23_085, 14_252_360.90, 6.3088),
        ("(none)", 1_801, 2_942_120.98, 3.0601),
    ):
        _g = _mvm[_mvm["srclab"] == _s]
        _w = (_g["billed_qty"] * _g["bp_prior_revised"]).sum()
        _st = (_g["billed_qty"] * _g["delta_jpy"]).sum()
        assert len(_g) == _rows, f"source {_s}: rows {len(_g)} != published {_rows}"
        assert abs(_g["net_sales_value"].sum() - _eur) < 0.01, f"source {_s}: EUR mismatch"
        assert abs(_st / _w * 100.0 - _pct) < 0.001, f"source {_s}: rate mismatch"

    # ---- market assignment + explicit residual --------------------------
    d["market"] = "UK (ITUK + IUK)"
    for code, _note in reversed(MARKETS):
        d.loc[market_mask(d, code).values, "market"] = code

    def block(g: pd.DataFrame) -> dict:
        # Every rate in this block is measured on the MOVABLE rows only, exactly as the published
        # per-market figures are. Including rows with no price on one side would drag a weighted
        # percentage down for a data-coverage reason and misstate the price move.
        mg = g[g["movable"] == True]  # noqa: E712
        w = (mg["billed_qty"] * mg["bp_prior_revised"]).sum()
        s = (mg["billed_qty"] * mg["delta_jpy"]).sum()
        return {
            "lines": int(len(g)),
            "part_numbers": int(g["pn"].nunique()),
            "billed_eur": money(g["net_sales_value"].sum()),
            "step_filed_eur": money(g["value_eur_step"].sum()),
            "movable_lines": int(len(mg)),
            "movable_billed_eur": money(mg["net_sales_value"].sum()),
            "immovable_lines": int(len(g) - len(mg)),
            "immovable_billed_eur": money(g["net_sales_value"].sum() - mg["net_sales_value"].sum()),
            "step_5pct_movable_eur": money(mg["net_sales_value"].sum() * RATE),
            "step_5pct_all_lines_eur": money(g["step_5pct_eur"].sum()),
            "filed_weighted_pct": round(float(s / w) * 100.0, 4) if w else float("nan"),
        }


    market_rows = []
    for code, note in MARKETS:
        g = d[d["market"] == code]
        b = block(g)
        b["market"] = code
        b["note"] = note
        b["share_of_billed_pct"] = round(b["billed_eur"] / billed * 100.0, 2)
        market_rows.append(b)
    resid = d[d["market"] == "UK (ITUK + IUK)"]
    b = block(resid)
    b["market"] = "UK (ITUK + IUK)"
    b["note"] = ("The UK carries no PR00 / UTI / UMI / CIS code, so it is not inside any of the four "
                 "market codes the published per-market figures use. It is ISZE's largest single "
                 "trading block by billed value and it is shown as its own row so the table sums to "
                 "the whole in-scope book.")
    b["share_of_billed_pct"] = round(b["billed_eur"] / billed * 100.0, 2)
    market_rows.append(b)
    assert sum(r["lines"] for r in market_rows) == lines
    assert abs(sum(r["billed_eur"] for r in market_rows) - billed) < 0.01

    # ---- source of supply rollup ---------------------------------------
    source_rows = []
    for code, label in (("J", "Japan (IML)"), ("T", "Thailand (IMIT)"), ("(none)", "No source label")):
        g = d[d["srclab"] == code]
        if not len(g):
            continue
        b = block(g)
        b["source"] = label
        b["share_of_billed_pct"] = round(b["billed_eur"] / billed * 100.0, 2)
        source_rows.append(b)
    assert sum(r["lines"] for r in source_rows) == lines

    # ---- market x source -------------------------------------------------
    cross_rows = []
    for code, _n in MARKETS + [("UK (ITUK + IUK)", "")]:
        for scode, label in (("J", "Japan (IML)"), ("T", "Thailand (IMIT)"), ("(none)", "No source label")):
            g = d[(d["market"] == code) & (d["srclab"] == scode)]
            if not len(g) or not g["movable"].any():
                continue
            gg = g[g["movable"]]
            w = (gg["billed_qty"] * gg["bp_prior_revised"]).sum()
            s = (gg["billed_qty"] * gg["delta_jpy"]).sum()
            cross_rows.append({
                "market": code,
                "source": label,
                "movable_lines": int(len(gg)),
                "billed_eur": money(gg["net_sales_value"].sum()),
                "filed_weighted_pct": round(float(s / w) * 100.0, 4) if w else float("nan"),
                "step_5pct_eur": money(gg["net_sales_value"].sum() * RATE),
            })

    # ---- AIM level 1 rollup --------------------------------------------
    aim = pd.read_csv(AIM_CSV, usecols=["part_number", "aim_l1_fixed"], low_memory=False)
    aim["pn"] = aim["part_number"].astype(str).str.strip().str.zfill(10)
    aim = aim.drop_duplicates(subset=["pn"])[["pn", "aim_l1_fixed"]]
    d = d.merge(aim, on="pn", how="left")
    d["aim_l1"] = d["aim_l1_fixed"].fillna("").astype(str).str.strip()
    d.loc[d["aim_l1"].isin(PLACEHOLDER), "aim_l1"] = NA

    by_l1 = (
        d.groupby("aim_l1", dropna=False)
        .agg(
            part_numbers=("pn", "nunique"),
            billed_eur=("net_sales_value", "sum"),
            step_filed_eur=("value_eur_step", "sum"),
            step_5pct_eur=("step_5pct_eur", "sum"),
        )
        .reset_index()
        .sort_values("step_5pct_eur", ascending=False)
    )
    by_l1["share_billed_pct"] = by_l1["billed_eur"] / billed * 100.0
    by_l1["share_step_5pct_pct"] = by_l1["step_5pct_eur"] / step_5pct_all * 100.0

    # ---- distributor rollup ---------------------------------------------
    by_db = (
        d.groupby("gps_db_label", dropna=False)
        .agg(
            part_numbers=("pn", "nunique"),
            billed_eur=("net_sales_value", "sum"),
            step_filed_eur=("value_eur_step", "sum"),
            step_5pct_eur=("step_5pct_eur", "sum"),
        )
        .reset_index()
        .sort_values("billed_eur", ascending=False)
    )
    by_db["weighted_move_filed_pct"] = np.where(
        by_db["billed_eur"] > 0, by_db["step_filed_eur"] / by_db["billed_eur"] * 100.0, np.nan
    )
    by_db["share_step_5pct_pct"] = by_db["step_5pct_eur"] / step_5pct_all * 100.0
    by_db = by_db.rename(columns={"gps_db_label": "distributor"})

    # ---- top part numbers by +5% euro ------------------------------------
    top = (
        d.groupby(["pn", "billed_description"], dropna=False)
        .agg(
            aim_l1=("aim_l1", "first"),
            market=("market", "first"),
            source=("src_label", "first"),
            billed_qty=("billed_qty", "sum"),
            billed_eur=("net_sales_value", "sum"),
            step_filed_eur=("value_eur_step", "sum"),
            step_5pct_eur=("step_5pct_eur", "sum"),
        )
        .reset_index()
        .sort_values("step_5pct_eur", ascending=False)
        .head(250)
    )

    # ---- concentration ---------------------------------------------------
    s = d["step_5pct_eur"].sort_values(ascending=False).to_numpy()
    cum = np.cumsum(s) / s.sum() * 100.0
    concentration = {f"top_{n}": round(float(cum[n - 1]), 1) for n in (10, 100, 250, 1000)}

    # ---- what cannot move, as its own deliverable list -------------------
    immovable_list = d.loc[d["movable"] == False, [  # noqa: E712
        "pn", "billed_description", "market", "src_label", "gps_db_label", "country",
        "billed_qty", "net_sales_value", "unpriced_reason", "bp_new_jpy",
        "bp_prior_revised", "bp_prior_billed",
    ]].copy()
    immovable_list["step_5pct_eur_if_it_could_move"] = immovable_list["net_sales_value"] * RATE
    immovable_list = immovable_list.sort_values("net_sales_value", ascending=False)

    # ---- headline --------------------------------------------------------
    summary = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stamp": STAMP,
        "status": "SIMULATION ONLY - nothing published, nothing mailed, no live price list, "
                  "price file or pricing configuration touched",
        "basis": {
            "source": str(PN_CSV.relative_to(ISZE)).replace("\\", "/"),
            "filter": "in_scope == True",
            "window": "2025-07-01 .. 2026-06-30",
            "lines": lines,
            "part_numbers": pns,
            "billed_eur": money(billed),
            "source_file_mtime": datetime.fromtimestamp(
                PN_CSV.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "headline": {
            "rate_under_review_pct": RATE * 100.0,
            "step_5pct_on_movable_eur": money(step_5pct_movable),
            "step_5pct_on_all_in_scope_eur": money(step_5pct_all),
            "euro_weighted_move_pct": 5.0,
            "primary_label": "Value of a flat +5% on the in-scope base",
            "collectable_label": "Collectable once lines with no move available are excluded",
            "note": "Both figures are reported with equal weight. A single flat rate makes the "
                    "euro-weighted move equal the rate itself. The collectable figure is the one "
                    "that lands as money; the larger figure is the arithmetic on the whole "
                    "in-scope base and must not be quoted as cash.",
        },
        "movability": {
            "mask": "bp_new_jpy.notna() AND bp_prior_revised.notna()",
            "mask_note": "A line can take a new price only if it already carries a price on both "
                         "sides of the revision. This is the same mask the pricing policy paper "
                         "uses when it states 47,617 lines / EUR 32,595,852.63 / 93.15% of billed.",
            "movable_lines": movable_lines,
            "movable_billed_eur": money(movable_billed),
            "movable_share_pct": round(movable_billed / billed * 100.0, 2),
            "immovable_lines": immovable_lines,
            "immovable_billed_eur": money(immovable_billed),
            "immovable_share_pct": round(immovable_billed / billed * 100.0, 2),
            "immovable_step_5pct_if_it_could_move_eur": money(immovable_billed * RATE),
            "immovable_composition": immovable_composition,
            "immovable_sub_masks": sub_masks,
            "why_not_the_1647_reading": (
                "The 2026-09-17 page recorded '1,647 lines / EUR 4.48M / 12.81%' as the lines "
                "that cannot move, using `value_eur_step != 0` as the test. That mask is wrong. "
                "611 of those lines carry a base price on both sides and simply did not move in "
                "the filed revision (EUR 2,085,484.90 billed); a new flat +5% WOULD move them, so "
                "they are movable. The 611 lines sit today on exactly the three reasons in "
                "`immovable_composition` (lubricant_no_pr00_in_sap, rebate_or_non_part_admin, "
                "no_price_on_one_side), which is why the two readings land on the same order of "
                "magnitude while disagreeing on every count. Corrected on 2026-09-17 and "
                "reproduced here: 1,036 lines / EUR 2,397,756.76 / 6.85%."
            ),
            "not_a_no_list_claim": "This is not the CY2025 no-list gap of 522 part numbers / "
                                   "EUR 4.96M that the pricing policy paper records. That figure "
                                   "is a different window and a different mask, and it is not "
                                   "used anywhere on this page.",
        },
        "versus_filed_revision": {
            "step_filed_eur": money(step_filed),
            "rate_filed_published_pct": round(RATE_PUBLISHED * 100.0, 4),
            "index_reproduced_pct": round(index_published * 100.0, 6),
            "step_tie_out": "exact",
            "difference_filed_minus_flat_eur": money(step_filed - step_5pct_movable),
            "difference_filed_minus_flat_on_all_lines_eur": money(step_filed - step_5pct_all),
            "same_basis": False,
            "note": "Both are measured on the same in-scope L12M base. The filed revision is the "
                    "published, quantity-weighted price move. The +5% flat is a proposal and does "
                    "not exist. They are two separate readings of one base, never two components "
                    "of one increase, and are never summed.",
            "rate_bases_on_movable_set": {
                "published_headline": {
                    "value_pct": round(RATE_PUBLISHED * 100.0, 4),
                    "basis": "quantity-weighted base-price move on the movable set",
                },
                "simulation_quantity": {
                    "value_pct": round(rate_sim_qty * 100.0, 4),
                    "basis": "weighted on the simulation's own quantity",
                },
                "euro_weighted": {
                    "value_pct": round(rate_euro_wt * 100.0, 4),
                    "basis": "each line's move weighted by the euro it billed",
                },
                "step_on_priced_volume": {
                    "value_pct": round(rate_step_on_priced * 100.0, 4),
                    "basis": "value_eur_step divided by billed euro on the movable set",
                },
            },
        },
        "by_market": market_rows,
        "by_source": source_rows,
        "by_market_source": cross_rows,
        "refresh_vs_2026_09_17": {
            "prior_run": PRIOR_STAMP,
            "note": "Comparison is recomputed, not quoted. 'delta' is this run minus 17 Sep.",
            "fields": [
                {"field": "in-scope lines", "prior": PRIOR["lines"], "now": lines,
                 "delta": lines - PRIOR["lines"]},
                {"field": "part numbers", "prior": PRIOR["part_numbers"], "now": pns,
                 "delta": pns - PRIOR["part_numbers"]},
                {"field": "billed EUR", "prior": PRIOR["billed_eur"], "now": money(billed),
                 "delta": money(billed - PRIOR["billed_eur"])},
                {"field": "+5% on all in-scope lines EUR", "prior": PRIOR["step_5pct_all_eur"],
                 "now": money(step_5pct_all), "delta": money(step_5pct_all - PRIOR["step_5pct_all_eur"])},
                {"field": "+5% collectable EUR", "prior": PRIOR["step_5pct_movable_eur"],
                 "now": money(step_5pct_movable),
                 "delta": money(step_5pct_movable - PRIOR["step_5pct_movable_eur"])},
                {"field": "filed revision step EUR", "prior": PRIOR["step_filed_eur"],
                 "now": money(step_filed), "delta": money(step_filed - PRIOR["step_filed_eur"])},
                {"field": "movable lines", "prior": PRIOR["movable_lines"], "now": movable_lines,
                 "delta": movable_lines - PRIOR["movable_lines"]},
                {"field": "movable billed EUR", "prior": PRIOR["movable_billed_eur"],
                 "now": money(movable_billed), "delta": money(movable_billed - PRIOR["movable_billed_eur"])},
                {"field": "immovable lines", "prior": PRIOR["immovable_lines"],
                 "now": immovable_lines, "delta": immovable_lines - PRIOR["immovable_lines"]},
                {"field": "immovable billed EUR", "prior": PRIOR["immovable_billed_eur"],
                 "now": money(immovable_billed),
                 "delta": money(immovable_billed - PRIOR["immovable_billed_eur"])},
            ],
            "verdict": "The base file has not moved since 2026-09-17, so every figure reproduces "
                       "to the cent and the deltas are zero.",
        },
        "concentration_share_of_step_pct": concentration,
        "caveats": [
            "SIMULATION ONLY. Nothing was published, nothing was mailed, and no live price list, "
            "price file or pricing configuration was touched.",
            "No volume response is modelled. No elasticity coefficient exists in this workspace, "
            "and none is invented.",
            "The billing extract carries net value only - no gross, discount or condition, so the "
            "step is stated on net billed value, not on list value.",
            "AIM level 1 covers less than the whole book; the remainder is labelled, never dropped.",
            "Lines with no base price on one side cannot take a new price, so their euro is not "
            "collectable by pricing. They are counted and labelled, never dropped.",
            "The +5% flat proposal and the filed +5.9616% revision are two separate readings of "
            "the same base. They are never added together.",
            "The four market codes do not cover the whole in-scope book. The UK (ITUK and IUK, "
            "EUR 13.17M billed) sits outside them and is shown as its own row so the table sums "
            "to the total.",
            "The CY2025 no-list gap of 522 part numbers / EUR 4.96M is a different window and is "
            "not used anywhere on this page.",
        ],
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ISZE)}")

    write_workbook(d, by_l1, by_db, top, immovable_list, market_rows, source_rows, cross_rows, summary)
    write_html(summary, by_l1, by_db, top, concentration)

    print("done. nothing published, nothing mailed.")


# ---------------------------------------------------------------- workbook
def write_workbook(d, by_l1, by_db, top, immovable_list, market_rows, source_rows, cross_rows, summary) -> None:
    h = summary["headline"]
    mv = summary["movability"]
    v = summary["versus_filed_revision"]

    readme = pd.DataFrame(
        [
            ["What this is", "A SIMULATION: what a flat +5% on the current list costs, weighted on the volume billed."],
            ["What this is not", "Not a price change. Nothing published, nothing mailed, no live price list, price file or pricing configuration touched."],
            ["Basis", "price_bp_weighted_compare_pn.csv, filter in_scope == True, window 2025-07-01..2026-06-30"],
            ["Lines / part numbers", f"{summary['basis']['lines']:,} / {summary['basis']['part_numbers']:,}"],
            ["Billed, in scope", f"EUR {summary['basis']['billed_eur']:,.2f}"],
            ["+5% collectable (movable lines)", f"EUR {h['step_5pct_on_movable_eur']:,.2f}"],
            ["+5% on all in-scope lines", f"EUR {h['step_5pct_on_all_in_scope_eur']:,.2f}"],
            ["Which is money", "The collectable figure. The all-in-scope figure is whole-base arithmetic and is not cash."],
            ["Movable lines", f"{mv['movable_lines']:,} lines, EUR {mv['movable_billed_eur']:,.2f} "
                              f"({mv['movable_share_pct']:.2f}% of billed)"],
            ["Cannot move", f"{mv['immovable_lines']:,} lines, EUR {mv['immovable_billed_eur']:,.2f} "
                            f"({mv['immovable_share_pct']:.2f}% of billed) - no base price on one side"],
            ["Movability mask", mv["mask"]],
            ["Filed revision step", f"EUR {v['step_filed_eur']:,.2f}"],
            ["Filed headline rate", f"{v['rate_filed_published_pct']:.4f}% (quantity-weighted base-price move), reproduced here at {v['index_reproduced_pct']:.4f}%"],
            ["Step tie-out", "Exact - the filed step reconciles to the cent on this file."],
            ["Are the two added?", "NO. The +5% flat proposal and the filed +5.9616% revision are two separate readings of one base."],
            ["Refresh vs 2026-09-17", summary["refresh_vs_2026_09_17"]["verdict"]],
            ["Markets", "PR00 / UTI / UMI / CIS, the same four codes the published per-market figures use. The UK carries no code and is shown as its own row so the table sums to the total."],
            ["Source of supply", "Japan (IML) and Thailand (IMIT) from pricing_list_pn.parquet; the split reproduces the published +6.2081% Japan / +6.3088% Thailand / +3.0601% unlabelled exactly. Rows with no label are kept and shown separately."],
            ["Volume response", "None modelled. No elasticity coefficient exists, and none is invented."],
            ["Purpose", "Requested by Jerome on 2026-09-22. The price-ambition question is closed permanently; this simulation is its last output."],
            ["Prepared", summary["built_utc"]],
        ],
        columns=["Item", "Value"],
    )

    market_out = pd.DataFrame(market_rows)[[
        "market", "lines", "part_numbers", "billed_eur", "share_of_billed_pct",
        "movable_lines", "movable_billed_eur", "immovable_lines", "immovable_billed_eur",
        "step_filed_eur", "step_5pct_movable_eur", "step_5pct_all_lines_eur", "filed_weighted_pct",
    ]].rename(columns={
        "market": "Market", "lines": "In-scope lines", "part_numbers": "Part numbers",
        "billed_eur": "Billed EUR", "share_of_billed_pct": "Share of billed %",
        "movable_lines": "Movable lines", "movable_billed_eur": "Movable billed EUR",
        "immovable_lines": "Cannot move, lines", "immovable_billed_eur": "Cannot move, billed EUR",
        "step_filed_eur": "Filed step EUR", "step_5pct_movable_eur": "+5% step, movable EUR",
        "step_5pct_all_lines_eur": "+5% step, all lines EUR", "filed_weighted_pct": "Filed weighted %",
    })

    source_out = pd.DataFrame(source_rows)[[
        "source", "lines", "part_numbers", "billed_eur", "share_of_billed_pct",
        "movable_lines", "movable_billed_eur", "immovable_lines", "immovable_billed_eur",
        "step_filed_eur", "step_5pct_movable_eur", "filed_weighted_pct",
    ]].rename(columns={
        "source": "Source of supply", "lines": "In-scope lines", "part_numbers": "Part numbers",
        "billed_eur": "Billed EUR", "share_of_billed_pct": "Share of billed %",
        "movable_lines": "Movable lines", "movable_billed_eur": "Movable billed EUR",
        "immovable_lines": "Cannot move, lines", "immovable_billed_eur": "Cannot move, billed EUR",
        "step_filed_eur": "Filed step EUR", "step_5pct_movable_eur": "+5% step, movable EUR",
        "filed_weighted_pct": "Filed weighted %",
    })

    cross_out = pd.DataFrame(cross_rows).rename(columns={
        "market": "Market", "source": "Source of supply", "movable_lines": "Movable lines",
        "billed_eur": "Movable billed EUR", "filed_weighted_pct": "Filed weighted %",
        "step_5pct_eur": "+5% step EUR",
    })

    refresh_out = pd.DataFrame(summary["refresh_vs_2026_09_17"]["fields"]).rename(columns={
        "field": "Measure", "prior": "2026-09-17 run", "now": "2026-09-22 run", "delta": "Difference",
    })

    imm_reason_out = pd.DataFrame(mv["immovable_composition"]).rename(columns={
        "reason": "Reason recorded in the file", "lines": "Lines", "billed_eur": "Billed EUR",
        "share_of_in_scope_billed_pct": "Share of in-scope billed %",
        "step_5pct_eur_if_it_could_move": "+5% step it could not collect EUR",
    })
    imm_sub_out = pd.DataFrame(mv["immovable_sub_masks"]).rename(columns={
        "sub_reason": "What is actually missing", "lines": "Lines", "billed_eur": "Billed EUR",
    })

    l1_out = by_l1.rename(columns={
        "aim_l1": "AIM level 1", "part_numbers": "Part numbers", "billed_eur": "Billed EUR",
        "step_filed_eur": "Filed step EUR", "step_5pct_eur": "+5% step EUR",
        "share_billed_pct": "Share of billed %", "share_step_5pct_pct": "Share of +5% step %",
    })
    db_out = by_db.rename(columns={
        "distributor": "Distributor", "part_numbers": "Part numbers", "billed_eur": "Billed EUR",
        "step_filed_eur": "Filed step EUR", "step_5pct_eur": "+5% step EUR",
        "weighted_move_filed_pct": "Filed weighted move %", "share_step_5pct_pct": "Share of +5% step %",
    })
    top_out = top.rename(columns={
        "pn": "Part number", "billed_description": "Description as billed", "aim_l1": "AIM level 1",
        "market": "Market", "source": "Source of supply", "billed_qty": "Billed qty",
        "billed_eur": "Billed EUR", "step_filed_eur": "Filed step EUR", "step_5pct_eur": "+5% step EUR",
    })
    imm_out = immovable_list.rename(columns={
        "pn": "Part number", "billed_description": "Description as billed", "market": "Market",
        "src_label": "Source of supply", "gps_db_label": "Distributor", "country": "Country",
        "billed_qty": "Billed qty", "net_sales_value": "Billed EUR",
        "unpriced_reason": "Reason recorded in the file", "bp_new_jpy": "New base price JPY",
        "bp_prior_revised": "Prior base price JPY", "bp_prior_billed": "Prior billed price JPY",
        "step_5pct_eur_if_it_could_move": "+5% not collectable EUR",
    })

    data_out = d[[
        "pn", "gps_db_label", "country", "market", "src_label", "aim_l1", "billed_description",
        "billed_qty", "net_sales_value", "bp_new_jpy", "bp_prior_revised", "delta_pct",
        "value_eur_step", "step_5pct_eur", "movable",
    ]].copy().rename(columns={
        "pn": "Part number", "gps_db_label": "Distributor", "country": "Country",
        "market": "Market", "src_label": "Source of supply", "aim_l1": "AIM level 1",
        "billed_description": "Description as billed", "billed_qty": "Billed qty",
        "net_sales_value": "Billed EUR (L12M)", "bp_new_jpy": "New base price JPY",
        "bp_prior_revised": "Prior base price JPY", "delta_pct": "Filed revision move",
        "value_eur_step": "Filed revision step EUR", "step_5pct_eur": "+5% step EUR",
        "movable": "Can take a new price",
    })

    sheets = [
        ("Read me", readme),
        ("Refresh vs 17 Sep", refresh_out),
        ("By market", market_out),
        ("By source", source_out),
        ("Market x source", cross_out),
        ("Cannot move - reasons", imm_reason_out),
        ("Cannot move - detail", imm_sub_out),
        ("Cannot move - lines", imm_out),
        ("AIM level 1", l1_out),
        ("Distributor", db_out),
        ("Top 250 by +5% EUR", top_out),
        ("Line data", data_out),
    ]

    wide_left = {"Item", "Description as billed", "AIM level 1", "Distributor", "Market",
                 "Source of supply", "Reason recorded in the file", "What is actually missing",
                 "Country", "Measure"}

    with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as xl:
        for name, frame in sheets:
            frame.to_excel(xl, sheet_name=name, index=False)

        wb = xl.book
        money_fmt = wb.add_format({"num_format": "#,##0.00"})
        pct_fmt = wb.add_format({"num_format": "0.00%"})
        head_fmt = wb.add_format({"bold": True, "bg_color": "#15233C", "font_color": "#F7F4EE",
                                  "border": 1, "text_wrap": True, "valign": "top"})
        wrap_fmt = wb.add_format({"text_wrap": True, "valign": "top"})

        for name, frame in sheets:
            ws = xl.sheets[name]
            for c, col in enumerate(frame.columns):
                ws.write(0, c, col, head_fmt)
                if col in wide_left:
                    ws.set_column(c, c, 46 if col != "Item" else 30, wrap_fmt)
                elif "EUR" in col:
                    ws.set_column(c, c, 19, money_fmt)
                else:
                    ws.set_column(c, c, 18)

            ws.set_column(1, 1, max(30, 46 if name == "Read me" else 34), wrap_fmt)
            ws.set_column(3, 3, 34, wrap_fmt)
            if len(frame.columns) >= 2:
                for r in range(1, len(frame) + 1):
                    for cidx in (1, 3):
                        if cidx < len(frame.columns):
                            v_ = frame.iloc[r - 1, cidx]
                            if isinstance(v_, str):
                                ws.write(r, cidx, v_, wrap_fmt)

            ws.freeze_panes(1, 0)
            if name != "Line data":
                ws.autofilter(0, 0, len(frame), max(len(frame.columns) - 1, 0))

    print(f"wrote {OUT_XLSX.relative_to(ISZE)}")


# ---------------------------------------------------------------- html
def write_html(summary, by_l1, by_db, top, concentration) -> None:
    chart_js = CHART_JS.read_text(encoding="utf-8")

    h = summary["headline"]
    mv = summary["movability"]
    v = summary["versus_filed_revision"]
    mk = summary["by_market"]
    src = summary["by_source"]
    refresh = summary["refresh_vs_2026_09_17"]

    mk_labels = [r["market"] for r in mk]
    mk_filed = [r["filed_weighted_pct"] for r in mk]
    mk_flat = [5.0 for _ in mk]
    mk_step = [r["step_5pct_movable_eur"] for r in mk]

    sr_labels = [r["source"] for r in src]
    sr_billed = [r["billed_eur"] for r in src]
    sr_filed = [r["filed_weighted_pct"] for r in src]

    imm_money = mv["immovable_composition"]

    conc_labels = list(concentration.keys())
    conc_vals = list(concentration.values())

    tp = top.head(12)
    tp_labels = [str(x) for x in tp["pn"].tolist()]
    tp_vals = [round(float(x), 2) for x in tp["step_5pct_eur"].tolist()]

    payload = json.dumps({
        "mk": {"labels": mk_labels, "filed": mk_filed, "flat": mk_flat, "step": mk_step},
        "sr": {"labels": sr_labels, "billed": sr_billed, "filed": sr_filed},
        "imm": {"labels": [c["reason"] for c in imm_money],
                "values": [c["billed_eur"] for c in imm_money]},
        "conc": {"labels": conc_labels, "values": conc_vals},
        "top": {"labels": tp_labels, "values": tp_vals},
    }).replace("</", "<\\/")

    def money_cell(x):
        return f"&euro;{x:,.0f}"

    mk_rows = "".join(
        f"<tr><td><strong>{r['market']}</strong></td><td class='n'>{r['lines']:,}</td>"
        f"<td class='n'>{money_cell(r['billed_eur'])}</td>"
        f"<td class='n'>{r['share_of_billed_pct']:.2f}%</td>"
        f"<td class='n'>{r['movable_lines']:,}</td>"
        f"<td class='n'>{money_cell(r['movable_billed_eur'])}</td>"
        f"<td class='n'>{r['filed_weighted_pct']:.4f}%</td>"
        f"<td class='n'>{money_cell(r['step_5pct_movable_eur'])}</td></tr>"
        for r in mk
    )
    sr_rows = "".join(
        f"<tr><td><strong>{r['source']}</strong></td><td class='n'>{r['lines']:,}</td>"
        f"<td class='n'>{money_cell(r['billed_eur'])}</td>"
        f"<td class='n'>{r['share_of_billed_pct']:.2f}%</td>"
        f"<td class='n'>{r['filed_weighted_pct']:.4f}%</td>"
        f"<td class='n'>{r['immovable_lines']:,}</td>"
        f"<td class='n'>{money_cell(r['immovable_billed_eur'])}</td>"
        f"<td class='n'>{money_cell(r['step_5pct_movable_eur'])}</td></tr>"
        for r in src
    )
    imm_rows = "".join(
        f"<tr><td>{r['reason']}</td><td class='n'>{r['lines']:,}</td>"
        f"<td class='n'>{money_cell(r['billed_eur'])}</td>"
        f"<td class='n'>{r['share_of_in_scope_billed_pct']:.2f}%</td>"
        f"<td class='n'>{money_cell(r['step_5pct_eur_if_it_could_move'])}</td></tr>"
        for r in mv["immovable_composition"]
    )
    imm_sub_rows = "".join(
        f"<tr><td>{r['sub_reason']}</td><td class='n'>{r['lines']:,}</td>"
        f"<td class='n'>{money_cell(r['billed_eur'])}</td></tr>"
        for r in mv["immovable_sub_masks"]
    )
    ref_rows = "".join(
        f"<tr><td>{r['field']}</td><td class='n'>{r['prior'] if isinstance(r['prior'], str) else format(r['prior'], ',.2f')}</td>"
        f"<td class='n'>{r['now'] if isinstance(r['now'], str) else format(r['now'], ',.2f')}</td>"
        f"<td class='n'>{r['delta'] if isinstance(r['delta'], str) else format(r['delta'], ',.2f')}</td></tr>"
        for r in refresh["fields"]
    )
    l1_rows = "".join(
        f"<tr><td>{r.aim_l1}</td><td class='n'>{r.part_numbers:,}</td>"
        f"<td class='n'>{money_cell(r.billed_eur)}</td>"
        f"<td class='n'>{r.share_step_5pct_pct:.1f}%</td></tr>"
        for r in by_l1.head(14).itertuples()
    )
    db_rows = "".join(
        f"<tr><td>{r.distributor}</td><td class='n'>{r.part_numbers:,}</td>"
        f"<td class='n'>{money_cell(r.billed_eur)}</td>"
        f"<td class='n'>{r.weighted_move_filed_pct:.2f}%</td>"
        f"<td class='n'>{money_cell(r.step_5pct_eur)}</td></tr>"
        for r in by_db.head(14).itertuples()
    )
    top_rows = "".join(
        f"<tr><td class='mono'>{r.pn}</td><td class='d'>{str(r.billed_description)[:48]}</td>"
        f"<td>{r.market}</td><td class='n'>{money_cell(r.billed_eur)}</td>"
        f"<td class='n'>{money_cell(r.step_5pct_eur)}</td></tr>"
        for r in top.head(20).itertuples()
    )
    caveat_rows = "".join(f"<li>{c}</li>" for c in summary["caveats"])
    basis_rows = "".join(
        f"<tr><td>{k}</td><td class='n'>{val}</td></tr>" for k, val in [
            ("Published headline rate", f"{v['rate_filed_published_pct']:.4f}%"),
            ("Reproduced on this file", f"{v['index_reproduced_pct']:.4f}%"),
            ("Simulation-quantity weighted", f"{v['rate_bases_on_movable_set']['simulation_quantity']['value_pct']:.4f}%"),
            ("Euro-weighted", f"{v['rate_bases_on_movable_set']['euro_weighted']['value_pct']:.4f}%"),
            ("Step on priced volume", f"{v['rate_bases_on_movable_set']['step_on_priced_volume']['value_pct']:.4f}%"),
        ]
    )

    css = """
:root{--navy:#15233c;--navy2:#1d3054;--terra:#c0552d;--paper:#f7f4ee;--ink:#22262e;
--muted:#6b6459;--line:#d9d3c8;--band:#eef3f9;--amber:#a8721f;--good:#1e6b4f}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.5;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:26px} h2{font-size:19px} h3{font-size:15px;margin:14px 0 4px}
.wrap{max-width:1300px;margin:0 auto;padding:22px 22px 70px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:14px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);font-size:11px;
letter-spacing:.6px;text-transform:uppercase;padding:3px 9px;border-radius:2px;margin-right:8px}
.badge.review{background:var(--terra)}
.sub{color:var(--muted);font-size:13px;margin-top:6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;margin:18px 0}
.kpi{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);padding:13px 15px;position:relative}
.kpi.t{border-left-color:var(--terra)}
.kpi .lab{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}
.kpi .val{font-family:Georgia,serif;font-size:24px;color:var(--navy);margin-top:3px}
.kpi .sub2{font-size:12px;color:var(--muted);margin-top:2px}
.kpi:hover .tip{display:block}
.tip{display:none;position:absolute;z-index:40;left:0;top:100%;width:300px;background:var(--navy);
color:var(--paper);font-size:12px;line-height:1.45;padding:10px 12px;border-left:3px solid var(--terra)}
.card{background:#fff;border:1px solid var(--line);padding:16px;margin-bottom:18px}
.card h2{margin-bottom:3px}
.card .q{color:var(--muted);font-size:12.5px;margin-bottom:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:980px){.grid2{grid-template-columns:1fr}}
canvas{width:100%!important;max-height:330px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;font-weight:600;font-size:12px}
td{padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even) td{background:var(--band)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
td.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}
td.d{color:var(--muted)}
.note{background:#fdf6ec;border:1px solid #e7d3ae;border-left:4px solid var(--amber);padding:12px 14px;margin:16px 0}
.note strong{color:#8a5d13}
.note.navy{background:#eef3f9;border-color:#c2d2e4;border-left-color:var(--navy)}
.note.navy strong{color:var(--navy)}
ul{margin:6px 0 0 18px;padding:0} li{margin-bottom:5px}
.foot{color:var(--muted);font-size:12px;border-top:1px solid var(--line);margin-top:24px;padding-top:12px}
.banner{background:var(--terra);color:#fff;padding:11px 14px;font-weight:600;margin-bottom:16px}
.split{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0}
.split .box{background:#fff;border:1px solid var(--line);border-top:4px solid var(--navy);padding:13px 15px}
.split .box.b{border-top-color:var(--terra)}
.split .box .t{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}
.split .box .v{font-family:Georgia,serif;font-size:22px;color:var(--navy);margin:4px 0}
.split .box .d{font-size:12.5px;color:var(--muted)}
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A +5% flat price increase - simulation, {summary['stamp']}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div><span class="badge">Internal</span><span class="badge review">Simulation only - not a price change</span></div>
  <h1>A +5% flat price increase - simulation</h1>
  <div class="sub">What a flat five per cent costs on the volume actually billed, read beside the
  revision already filed. Basis: {summary['basis']['window']}, in-scope lines only.
  Computed {summary['built_utc']}.</div>
</header>

<div class="banner">This is a simulation. No price list, price file or pricing setting was changed,
and nothing was mailed.</div>

<div class="kpis">
  <div class="kpi t"><div class="lab">Collectable once lines with no move available are excluded</div>
    <div class="val">&euro;{h['step_5pct_on_movable_eur']:,.0f}</div>
    <div class="sub2">on {mv['movable_lines']:,} lines that can take a new price
    ({mv['movable_share_pct']:.2f}% of billed)</div>
    <div class="tip">A flat 5.000% on the current base price, valued on the volume billed, counted
    only on lines that already carry a price on both sides of the revision. This is the figure that
    lands as money.</div></div>

  <div class="kpi t"><div class="lab">Value of a flat +5% on the in-scope base</div>
    <div class="val">&euro;{h['step_5pct_on_all_in_scope_eur']:,.0f}</div>
    <div class="sub2">arithmetic on all {summary['basis']['lines']:,} in-scope lines</div>
    <div class="tip">What a flat 5.000% comes to if every in-scope line could move. The difference
    against the collectable figure is the euro sitting on lines with no price on one side. This
    figure is whole-base arithmetic and must not be quoted as cash.</div></div>

  <div class="kpi"><div class="lab">Revision already filed</div>
    <div class="val">&euro;{v['step_filed_eur']:,.0f}</div>
    <div class="sub2">{v['rate_filed_published_pct']:.4f}% published headline</div>
    <div class="tip">The published in-scope revision. Step and headline rate both reconcile on this
    file. Same base as the +5%, but a separate reading - the two are never added.</div></div>

  <div class="kpi"><div class="lab">Billed in scope</div>
    <div class="val">&euro;{summary['basis']['billed_eur']:,.0f}</div>
    <div class="sub2">{summary['basis']['part_numbers']:,} part numbers</div>
    <div class="tip">Net sales value on the in-scope L12M base, distributor customers only.
    Non-part billing and the direct account are excluded by the in-scope filter.</div></div>
</div>

<div class="note navy">
  <strong>These are two readings of one base, not two increases.</strong>
  The revision already filed moved the same book by <strong>{v['rate_filed_published_pct']:.4f}%</strong>,
  worth <strong>&euro;{v['step_filed_eur']:,.2f}</strong> on the {mv['movable_lines']:,} movable lines.
  The +5% flat is a proposal worth <strong>&euro;{h['step_5pct_on_movable_eur']:,.2f}</strong> on the
  same lines. The filed revision is the larger by
  <strong>&euro;{v['difference_filed_minus_flat_eur']:,.2f}</strong>. They are never added together.
</div>

<div class="split">
  <div class="box">
    <div class="t">Can move</div>
    <div class="v">{mv['movable_lines']:,} lines</div>
    <div class="d">&euro;{mv['movable_billed_eur']:,.2f} billed ({mv['movable_share_pct']:.2f}%) -
    a base price on both sides of the revision, so a new price can be set.</div>
  </div>
  <div class="box b">
    <div class="t">Cannot move</div>
    <div class="v">{mv['immovable_lines']:,} lines</div>
    <div class="d">&euro;{mv['immovable_billed_eur']:,.2f} billed ({mv['immovable_share_pct']:.2f}%) -
    no base price on one side, so there is nothing to lift. The +5% would be
    &euro;{mv['immovable_step_5pct_if_it_could_move_eur']:,.2f} on this euro and it is not collectable.</div>
  </div>
</div>

<div class="card">
  <h2>Market by market</h2>
  <div class="q">The same four market codes the published per-market figures use. UTI is sold-to 1799
  and UMI is sold-to 1797; they are separate distributors and are never blended. The four codes do
  not cover the whole book: the UK carries no code, is ISZE's largest single trading block by billed
  value, and is shown as its own row so the table sums to the total.</div>
  <table>
    <thead><tr><th>Market</th><th class="n">In-scope lines</th><th class="n">Billed EUR</th>
    <th class="n">Share of billed</th><th class="n">Movable lines</th>
    <th class="n">Movable billed EUR</th><th class="n">Filed weighted move</th>
    <th class="n">+5% step EUR</th></tr></thead>
    <tbody>{mk_rows}</tbody>
  </table>
</div>

<div class="grid2">
  <div class="card">
    <h2>Filed move against the +5% flat, by market</h2>
    <div class="q">Each market's own measured move under the filed revision, beside the flat 5.000%
    proposal on the same rows.</div>
    <canvas id="c1" height="150"></canvas>
  </div>
  <div class="card">
    <h2>What the +5% raises, by market</h2>
    <div class="q">Euro raised per market, counted only on lines that can take a new price.</div>
    <canvas id="c2" height="150"></canvas>
  </div>
</div>

<div class="card">
  <h2>By source of supply</h2>
  <div class="q">Japan and Thailand are the two sources. Rows the price list does not label are kept
  and shown separately rather than assigned to either.</div>
  <table>
    <thead><tr><th>Source of supply</th><th class="n">In-scope lines</th><th class="n">Billed EUR</th>
    <th class="n">Share of billed</th><th class="n">Filed weighted move</th>
    <th class="n">Cannot move, lines</th><th class="n">Cannot move, billed EUR</th>
    <th class="n">+5% step EUR</th></tr></thead>
    <tbody>{sr_rows}</tbody>
  </table>
  <h3>Source, read on the euro it carries</h3>
  <canvas id="c3" height="130"></canvas>
</div>

<div class="card">
  <h2>What cannot move, and why</h2>
  <div class="q">The immovable set on this basis, by the reason the file itself records, then by what
  is actually missing on the line.</div>
  <table>
    <thead><tr><th>Reason recorded in the file</th><th class="n">Lines</th>
    <th class="n">Billed EUR</th><th class="n">Share of in-scope billed</th>
    <th class="n">+5% that could not be collected</th></tr></thead>
    <tbody>{imm_rows}</tbody>
  </table>
  <h3>What is actually missing on the line</h3>
  <table>
    <thead><tr><th>What is missing</th><th class="n">Lines</th><th class="n">Billed EUR</th></tr></thead>
    <tbody>{imm_sub_rows}</tbody>
  </table>
</div>

<div class="note">
  <strong>Why this says {mv['immovable_lines']:,} lines and the 17 September page also mentions 1,647.</strong>
  The 17 September page first reported <strong>1,647 lines / &euro;4.48M / 12.81%</strong> as the lines
  that cannot move, testing with <code>value_eur_step != 0</code>. That test is wrong: 611 of those
  lines carry a base price on both sides and simply did not move in the filed revision
  (&euro;2,085,484.90 billed). A flat +5% would move them, so they can move. The 611 lines sit on
  exactly the three reasons listed above, which is why the two readings land on the same order of
  magnitude while disagreeing on every count. The corrected figure, used here, is
  <strong>{mv['immovable_lines']:,} lines / &euro;{mv['immovable_billed_eur']:,.2f} /
  {mv['immovable_share_pct']:.2f}% of billed</strong>. This is not the CY2025 no-list gap of 522 part
  numbers / &euro;4.96M, which is a different window and is not used on this page.
</div>

<div class="card">
  <h2>Refresh against the 17 September 2026 run</h2>
  <div class="q">Recomputed on today's copy of the base file, not quoted from the earlier page.
  A non-zero difference would mean the base moved.</div>
  <table>
    <thead><tr><th>Measure</th><th class="n">2026-09-17 run</th><th class="n">2026-09-22 run</th>
    <th class="n">Difference</th></tr></thead>
    <tbody>{ref_rows}</tbody>
  </table>
  <div class="q" style="margin-top:10px">{refresh['verdict']} Base file:
  <code>{summary['basis']['source']}</code>, last written {summary['basis']['source_file_mtime']}.</div>
</div>

<div class="card">
  <h2>The rate bases, named</h2>
  <div class="q">The published headline under the filed revision, and the two sensitivities the
  pricing policy paper already documents, all reproduced on today's file.</div>
  <table>
    <thead><tr><th>Reading</th><th class="n">Rate</th></tr></thead>
    <tbody>{basis_rows}</tbody>
  </table>
</div>

<div class="card">
  <h2>How concentrated is the increase?</h2>
  <div class="q">Share of the total +5% step captured by the largest lines.</div>
  <canvas id="c4" height="110"></canvas>
</div>

<div class="card">
  <h2>The largest part numbers by +5% euro</h2>
  <div class="q">Where the increase is largest in money, so the distributor conversation starts from
  the top rather than the average.</div>
  <canvas id="c5" height="150"></canvas>
  <table>
    <thead><tr><th>Part number</th><th>Description as billed</th><th>Market</th>
    <th class="n">Billed EUR</th><th class="n">+5% step EUR</th></tr></thead>
    <tbody>{top_rows}</tbody>
  </table>
</div>

<div class="grid2">
  <div class="card">
    <h2>By part family</h2>
    <div class="q">Share of the +5% step by corrected AIM level 1. Families not on the AIM spine are
    shown as their own row rather than dropped.</div>
    <table>
      <thead><tr><th>Part family</th><th class="n">Part numbers</th><th class="n">Billed EUR</th>
      <th class="n">Share of +5%</th></tr></thead>
      <tbody>{l1_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>By distributor</h2>
    <div class="q">The same increase, read per trading entity.</div>
    <table>
      <thead><tr><th>Distributor</th><th class="n">Part numbers</th><th class="n">Billed EUR</th>
      <th class="n">Filed move</th><th class="n">+5% step EUR</th></tr></thead>
      <tbody>{db_rows}</tbody>
    </table>
  </div>
</div>

<div class="card">
  <h2>What this page does not claim</h2>
  <ul>{caveat_rows}</ul>
</div>

<div class="foot">
  Source: {summary['basis']['source']}, filter <code>in_scope == True</code>. Part families from
  <code>01_data/00_derived/aim_master_v2.csv</code>. Source of supply from
  <code>01_data/00_derived/pricing_list_pn.parquet</code> (J / T), which reproduces the published
  per-source split exactly.
  Computed {summary['built_utc']} as an internal simulation.
</div>

</div>
<script>{chart_js}</script>
<script>
const P = {payload};
const NAVY='#15233c', TERRA='#c0552d', LINE='#d9d3c8', MUTED='#6b6459', GOOD='#1e6b4f';
Chart.defaults.font.family='-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif';
Chart.defaults.font.size=11.5;
Chart.defaults.color=MUTED;
const eur = v => '\\u20AC' + (Math.abs(v)>=1e6 ? (v/1e6).toFixed(2)+'M' : Math.round(v/1e3)+'k');

new Chart(document.getElementById('c1'), {{
  type:'bar',
  data:{{labels:P.mk.labels,datasets:[
    {{label:'Filed revision %',data:P.mk.filed,backgroundColor:NAVY}},
    {{label:'+5% flat %',data:P.mk.flat,backgroundColor:TERRA}}]}},
  options:{{maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom'}},tooltip:{{callbacks:{{label:c=>' '+c.dataset.label+': '+c.raw.toFixed(4)+'%'}}}}}},
    scales:{{y:{{beginAtZero:true,grid:{{color:LINE}},ticks:{{callback:v=>v+'%'}}}},x:{{grid:{{display:false}}}}}}}}
}});

new Chart(document.getElementById('c2'), {{
  type:'bar',
  data:{{labels:P.mk.labels,datasets:[{{label:'+5% step EUR',data:P.mk.step,backgroundColor:TERRA}}]}},
  options:{{maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+eur(c.raw)}}}}}},
    scales:{{y:{{beginAtZero:true,grid:{{color:LINE}},ticks:{{callback:v=>eur(v)}}}},x:{{grid:{{display:false}}}}}}}}
}});

new Chart(document.getElementById('c3'), {{
  type:'bar',
  data:{{labels:P.sr.labels,datasets:[
    {{label:'Filed revision %',data:P.sr.filed,backgroundColor:NAVY}}]}},
  options:{{indexAxis:'y',maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' filed move '+c.raw.toFixed(4)+'%'}}}}}},
    scales:{{x:{{grid:{{color:LINE}},ticks:{{callback:v=>v+'%'}}}},y:{{grid:{{display:false}}}}}}}}
}});

new Chart(document.getElementById('c4'), {{
  type:'bar',
  data:{{labels:P.conc.labels.map(k=>k.replace('_',' ')),datasets:[{{label:'% of the +5% step',
    data:P.conc.values,backgroundColor:P.conc.values.map(v=>v>50?TERRA:NAVY)}}]}},
  options:{{maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+c.raw+'% of the total step'}}}}}},
    scales:{{y:{{beginAtZero:true,max:100,grid:{{color:LINE}},ticks:{{callback:v=>v+'%'}}}},
    x:{{grid:{{display:false}}}}}}}}
}});

new Chart(document.getElementById('c5'), {{
  type:'bar',
  data:{{labels:P.top.labels,datasets:[{{label:'+5% step EUR',data:P.top.values,backgroundColor:NAVY}}]}},
  options:{{indexAxis:'y',maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+eur(c.raw)}}}}}},
    scales:{{x:{{grid:{{color:LINE}},ticks:{{callback:v=>eur(v)}}}},y:{{grid:{{display:false}}}}}}}}
}});
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"wrote {OUT_HTML.relative_to(ISZE)}")


if __name__ == "__main__":
    main()
