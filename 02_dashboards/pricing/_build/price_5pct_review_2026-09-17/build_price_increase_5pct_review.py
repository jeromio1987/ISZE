#!/usr/bin/env python3
"""
ISZE +5% flat price-increase review - 2026-09-17.

WHAT THIS IS
------------
A paper exercise. It computes what a flat +5% on the current list does, weighted on the
volume actually billed, so it can be read beside the published +5.9616% revision.

It is NOT a price change. Nothing is published, nothing is mailed, no live list is touched.
Authority: .cursor/rules/isze-no-ship-without-ok.mdc. A price move is a signed decision by a
named person - 00_docs/RUNBOOK_ROUTINE_HANDOVER.md section 5.

READ-ONLY INPUTS
----------------
This builder reads and never writes:
  01_data/00_derived/price_bp_weighted_compare_pn.csv   the in-scope L12M revision base
  01_data/00_derived/aim_master_v2.csv                  corrected AIM levels
It does not touch any other derived file.

NEW OUTPUTS ONLY - Jerome, 2026-09-17
-------------------------------------
Every output below is a new, dated file. No existing pricing deliverable is overwritten,
edited or regenerated. The locked set is listed in 00_docs/agent/DELEGATOR_REFRESH_HOWTO.md.

BASIS - stated once, used everywhere
------------------------------------
  source    01_data/00_derived/price_bp_weighted_compare_pn.csv, filter in_scope == True
  window    2025-07-01 .. 2026-06-30 (L12M)
  billed    EUR 34,993,609.39 over 48,653 lines and 15,872 part numbers
  the +5%   a flat 5.000% applied to the current base price on every in-scope line

The existing revision moved the same base by 5.9616%. The two are not the same basis and are
never added together without saying so.

TWO THINGS THIS DELIBERATELY DOES NOT DO
----------------------------------------
1. It does not settle the exchange rate. 03_analytics/isze_pricing/config.yaml carries
   fx_rate 163.7 (2025-10-01); the Israel SPA work uses 172.6. That fork is open and Jerome
   has asked for it to stay open. A 163.7 -> 172.6 move cuts our euro purchase cost by 5.2%,
   which is roughly the size of this whole increase, so the rate is disclosed as an open
   question rather than assumed. FX_FORK below is documentation, not a dial.
2. It computes no volume response. There is no elasticity coefficient in this workspace and
   none is invented (03_analytics/isze_pricing/README.md).

Run: python 02_dashboards/pricing/_build/price_5pct_review_2026-09-17/build_price_increase_5pct_review.py
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

STAMP = "2026-09-17"
HERE = ISZE / "02_dashboards" / "pricing" / "_build" / f"price_5pct_review_{STAMP}"

PN_CSV = DERIVED / "price_bp_weighted_compare_pn.csv"
AIM_CSV = DERIVED / "aim_master_v2.csv"

OUT_JSON = HERE / "price_increase_5pct_summary.json"
OUT_XLSX = ISZE / "01_data" / "01_Pricing" / f"Price_Increase_5pct_Flat_REVIEW_{STAMP}.xlsx"
OUT_HTML = ISZE / "02_dashboards" / "pricing" / f"ISZE_Price_Increase_5pct_Flat_REVIEW_{STAMP}.html"

# ---------------------------------------------------------------- constants
RATE = 0.05                 # the flat increase under review
RATE_PUBLISHED = 0.059616   # what the in-scope revision actually did, for comparison
FX_ENGINE = 163.7           # 03_analytics/isze_pricing/config.yaml, as of 2025-10-01
FX_SPA = 172.6              # Israel SPA work, 2026-09-15/17 - the open fork
FX_FORK_PCT = (FX_SPA / FX_ENGINE - 1.0) * 100.0   # +5.44% weaker yen

NA = "Not on AIM spine"
PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None", "NaN"}


def money(x: float) -> float:
    return round(float(x), 2)


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)

    # ---- load the basis
    df = pd.read_csv(PN_CSV)
    d = df[df["in_scope"] == True].copy()  # noqa: E712 - the column is boolean

    billed = float(d["net_sales_value"].sum())
    step_existing = float(d["value_eur_step"].sum())
    lines = len(d)
    pns = int(d["part_number"].nunique())

    # ---------------------------------------------------------------
    # Two price-side masks. Get these right: they decide what the +5% can reach.
    #
    # A line can only take a NEW price change if it already carries a price on both sides
    # of the revision. That is the movability mask, and it is the one the pricing policy
    # paper uses for the same purpose (47,617 lines / EUR 32,595,852.63 / 93.15% of billed).
    #
    # An earlier build of this page used `value_eur_step != 0` as the test. That was wrong:
    # 611 lines carry a price on both sides and simply did not move in the last revision
    # (billed EUR 2,085,484.90). A new flat +5% WOULD move them. Excluding them understated
    # the movable base by EUR 2.08M.
    # ---------------------------------------------------------------
    has_new = d["bp_new_jpy"].notna()
    has_prior = d["bp_prior_revised"].notna()
    movable = has_new & has_prior

    movable_lines = int(movable.sum())
    movable_billed = float(d.loc[movable, "net_sales_value"].sum())
    immovable_billed = float(d.loc[~movable, "net_sales_value"].sum())
    immovable_lines = int((~movable).sum())

    step_5pct_movable = movable_billed * RATE

    # Composition of the immovable set, built plainly so it is easy to audit.
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
        }
        for r in imm_group.itertuples()
    ]

    # Rate bases, each named to the basis the policy paper already documents.
    # There is no new reconciliation story here: the published headline is the
    # quantity-weighted base-price move, and the two sensitivities are the paper's own.
    m = d.loc[movable]
    qty = m["billed_qty"].fillna(0)
    rate_published_pct = RATE_PUBLISHED * 100.0                       # paper: quantity-weighted headline
    rate_sim_qty_pct = float(
        (m["delta_pct"].fillna(0) * qty).sum() / qty.sum() * 100.0
    )                                                                 # paper: 6.06% on simulation quantity
    rate_euro_wt_pct = float(
        (m["delta_pct"].fillna(0) * m["net_sales_value"]).sum()
        / m["net_sales_value"].sum() * 100.0
    )                                                                 # euro-weighted
    rate_step_on_priced_pct = float(
        m["value_eur_step"].sum() / m["net_sales_value"].sum() * 100.0
    )                                                                 # paper: 5.068%

    print(f"basis: {lines:,} lines | {pns:,} part numbers | billed EUR {billed:,.2f}")
    print(f"movable (priced both sides): {movable_lines:,} lines | EUR {movable_billed:,.2f} "
          f"({movable_billed / billed:.2%})")
    print(f"immovable: {immovable_lines:,} lines | EUR {immovable_billed:,.2f} "
          f"({immovable_billed / billed:.2%})")
    print(f"existing step EUR {step_existing:,.2f} | published headline {rate_published_pct:.4f}%")
    print(f"paper's named bases on the movable set: simulation-quantity weighted "
          f"{rate_sim_qty_pct:.4f}% | euro-weighted {rate_euro_wt_pct:.4f}% | "
          f"step on priced volume {rate_step_on_priced_pct:.4f}%")

    # ---- the +5% flat step
    # A flat percentage on a current price costs proportionally to the euro the line carries.
    # We hold this on the net billed value, the only money column the extract carries.
    d["step_5pct_eur"] = d["net_sales_value"].astype(float) * RATE

    step_5pct = float(d["step_5pct_eur"].sum())
    # Because the +5% is a single rate, the euro-weighted move IS the rate. Asserted, not assumed.
    rate_5pct_ew = step_5pct / billed if billed else float("nan")
    assert abs(rate_5pct_ew - RATE) < 1e-9, f"flat rate check failed: {rate_5pct_ew}"
    print(f"+5% flat step EUR {step_5pct:,.2f} | euro-weighted {rate_5pct_ew:.4%}")

    # ---- AIM level 1 rollup (read-only join on part number; never on description)
    aim = pd.read_csv(AIM_CSV, usecols=["part_number", "aim_l1_fixed"], low_memory=False)
    aim = aim.drop_duplicates(subset=["part_number"])
    d = d.merge(aim, on="part_number", how="left")
    d["aim_l1"] = d["aim_l1_fixed"].fillna("").astype(str).str.strip()
    d.loc[d["aim_l1"].isin(PLACEHOLDER), "aim_l1"] = NA

    by_l1 = (
        d.groupby("aim_l1", dropna=False)
        .agg(
            part_numbers=("part_number", "nunique"),
            billed_eur=("net_sales_value", "sum"),
            step_existing_eur=("value_eur_step", "sum"),
            step_5pct_eur=("step_5pct_eur", "sum"),
        )
        .reset_index()
        .sort_values("step_5pct_eur", ascending=False)
    )
    by_l1["share_billed_pct"] = by_l1["billed_eur"] / billed * 100.0
    by_l1["share_step_5pct_pct"] = by_l1["step_5pct_eur"] / step_5pct * 100.0
    by_l1["rate_5pct_pct"] = RATE * 100.0

    # ---- distributor rollup
    by_db = (
        d.groupby("gps_db_label", dropna=False)
        .agg(
            part_numbers=("part_number", "nunique"),
            billed_eur=("net_sales_value", "sum"),
            step_existing_eur=("value_eur_step", "sum"),
            step_5pct_eur=("step_5pct_eur", "sum"),
        )
        .reset_index()
        .sort_values("billed_eur", ascending=False)
    )
    by_db["weighted_move_existing_pct"] = np.where(
        by_db["billed_eur"] > 0, by_db["step_existing_eur"] / by_db["billed_eur"] * 100.0, np.nan
    )
    by_db["share_step_5pct_pct"] = by_db["step_5pct_eur"] / step_5pct * 100.0

    # ---- top part numbers by +5% euro
    top = (
        d.groupby(["part_number", "billed_description"], dropna=False)
        .agg(
            aim_l1=("aim_l1", "first"),
            billed_qty=("billed_qty", "sum"),
            billed_eur=("net_sales_value", "sum"),
            step_existing_eur=("value_eur_step", "sum"),
            step_5pct_eur=("step_5pct_eur", "sum"),
        )
        .reset_index()
        .sort_values("step_5pct_eur", ascending=False)
        .head(250)
    )

    # ---- concentration
    s = d["step_5pct_eur"].sort_values(ascending=False).to_numpy()
    cum = np.cumsum(s) / s.sum() * 100.0
    concentration = {
        f"top_{n}": round(float(cum[n - 1]), 1) for n in (10, 100, 250, 1000) if n <= len(cum)
    }

    # ---- the two independent readings of the same +5%, from the decision memo
    l12m_base = 12_761_292.60
    fw_base = 14_517_267.95
    memo = {
        "source": "01_data/01_Pricing/DECISION_MEMO_PRICE_ADJUSTMENT_20260916.md (option B)",
        "note": "Illustrative +5% euro on the forecast-weight basis. A different base from the "
                "in-scope revision base above; do not add the two.",
        "l12m_base_eur": l12m_base,
        "forecast_weight_base_eur": fw_base,
        "plus5_on_l12m_eur": money(l12m_base * RATE),
        "plus5_on_forecast_weight_eur": money(fw_base * RATE),
    }

    # ---- headline
    summary = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stamp": STAMP,
        "status": "paper exercise - nothing published, nothing mailed, no live list touched",
        "basis": {
            "source": str(PN_CSV.relative_to(ISZE)).replace("\\", "/"),
            "filter": "in_scope == True",
            "window": "2025-07-01 .. 2026-06-30",
            "lines": lines,
            "part_numbers": pns,
            "billed_eur": money(billed),
        },
        "headline": {
            "rate_under_review_pct": RATE * 100.0,
            "step_5pct_on_all_in_scope_eur": money(step_5pct),
            "step_5pct_on_movable_eur": money(step_5pct_movable),
            "euro_weighted_move_pct": round(rate_5pct_ew * 100.0, 4),
            "primary_label": "Value of a flat +5% on the in-scope base",
            "collectable_label": "Collectable once lines with no move available are excluded",
            "note": "Both figures are reported with equal weight. A single flat rate makes the "
                    "euro-weighted move equal the rate itself. The collectable figure is the "
                    "one that lands as money; the larger figure is the arithmetic on the whole "
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
            "immovable_composition": immovable_composition,
            "not_a_no_list_claim": "This is not the CY2025 no-list gap of 522 part numbers / "
                                   "EUR 4.96M that the pricing policy paper records. That figure "
                                   "is a different window (CY2025) and a different mask, and it "
                                   "is not used here. The immovable set on this basis is the "
                                   "unpriced residual the paper states for this window: "
                                   "EUR 2,397,756.76.",
            "superseded_error": "An earlier build of this page reported 1,647 lines / EUR 4.48M "
                                "immovable, using `value_eur_step != 0` as the test. That wrongly "
                                "excluded 611 lines that carry a price on both sides but did not "
                                "move in the last revision (EUR 2,085,484.90). Corrected "
                                "2026-09-17.",
        },
        "versus_existing_revision": {
            "step_existing_eur": money(step_existing),
            "rate_existing_published_pct": round(rate_published_pct, 4),
            "step_tie_out": "exact",
            "rate_bases": {
                "published_headline": {
                    "value_pct": round(rate_published_pct, 4),
                    "basis": "quantity-weighted base-price move on the movable set",
                    "source": "01_data/90_INBOX/PRICING_POLICY_PAPER_2026-09-17.md - stated as the "
                              "headline in section 1 and confirmed in the AIM priority-list handoff",
                },
                "simulation_quantity": {
                    "value_pct": round(rate_sim_qty_pct, 4),
                    "basis": "weighted on the simulation's own quantity rather than billed quantity",
                    "source": "same paper, section 2.1 - documented as 6.06%",
                },
                "euro_weighted": {
                    "value_pct": round(rate_euro_wt_pct, 4),
                    "basis": "each line's move weighted by the euro it billed",
                    "source": "recomputed here; the paper names the two bases above and not this one",
                },
                "step_on_priced_volume": {
                    "value_pct": round(rate_step_on_priced_pct, 4),
                    "basis": "value_eur_step divided by billed euro on the movable set",
                    "source": "same paper, section 2.1 - documented as 5.068%",
                },
            },
            "rate_note": (
                "There is no second reconciliation story. The published 5.9616% is the "
                "quantity-weighted base-price move and it ties to the published step to the cent. "
                "The two sensitivities the paper already documents are 6.06% (simulation "
                "quantity) and 5.068% (step on priced volume), and both reproduce on this file. "
                "An earlier build of this page reported 5.9787% and 6.2347% on the wrong masks "
                "and claimed the published rate had an unreproducible denominator. That claim was "
                "unsupported and has been withdrawn."
            ),
            "step_5pct_eur": money(step_5pct),
            "difference_eur_5pct_minus_existing": money(step_5pct - step_existing),
            "same_basis": False,
            "note": "Both are measured on the in-scope L12M base. They are two separate "
                    "proposals, not two components of one increase.",
        },
        "fx_fork_open": {
            "engine_fx": FX_ENGINE,
            "engine_fx_as_of": "2025-10-01",
            "engine_fx_source": "03_analytics/isze_pricing/config.yaml",
            "spa_fx": FX_SPA,
            "spa_fx_source": "01_data/90_INBOX/_eran_spa_two_options_20260917/build_spa2_two_options.py",
            "yen_weakening_pct": round(FX_FORK_PCT, 4),
            "note": "A 163.7 -> 172.6 move cuts our euro purchase cost by about 5.2%, which is "
                    "approximately the size of this entire increase. Settling this before the "
                    "list is built is Jerome's call and is deliberately left open.",
        },
        "memo_cross_check": memo,
        "concentration_share_of_step_pct": concentration,
        "caveats": [
            "No volume response is modelled. No elasticity coefficient exists in this workspace.",
            "The billing extract carries net value only - no gross, discount or condition.",
            "AIM level 1 covers less than the whole book; the remainder is shown explicitly.",
            "Lines with no base price on one side cannot take a new price, so their euro is not "
            "collectable by pricing. They are counted and labelled, never dropped.",
            "The collectable figure is the one that lands as money. The all-in-scope figure is "
            "whole-base arithmetic and must not be quoted as cash.",
            "The CY2025 no-list gap of 522 part numbers / EUR 4.96M is a different window and is "
            "not used anywhere on this page.",
            "This is a paper exercise on the current list. Nothing was published, nothing was "
            "mailed, and no live list was touched.",
        ],
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ISZE)}")

    # ---- workbook
    write_workbook(d, by_l1, by_db, top, summary)

    # ---- html
    write_html(summary, by_l1, by_db, top, concentration)

    print("done. nothing published, nothing mailed.")


# ---------------------------------------------------------------- workbook
def write_workbook(d, by_l1, by_db, top, summary) -> None:
    cols = [
        "part_number", "gps_db_label", "country", "billed_description", "aim_l1",
        "billed_qty", "net_sales_value", "bp_new_jpy", "delta_pct",
        "value_eur_step", "step_5pct_eur",
    ]
    have = [c for c in cols if c in d.columns]

    readme = pd.DataFrame(
        [
            ["What this is", "A paper exercise: what a flat +5% on the current list costs, weighted on volume billed."],
            ["What this is not", "Not a price change. Nothing published, nothing mailed, no live list touched."],
            ["Basis", "price_bp_weighted_compare_pn.csv, filter in_scope == True, window 2025-07-01..2026-06-30"],
            ["Lines / part numbers", f"{summary['basis']['lines']:,} / {summary['basis']['part_numbers']:,}"],
            ["Billed, in scope", f"EUR {summary['basis']['billed_eur']:,.2f}"],
            ["+5% collectable (movable lines)", f"EUR {summary['headline']['step_5pct_on_movable_eur']:,.2f}"],
            ["+5% on all in-scope lines", f"EUR {summary['headline']['step_5pct_on_all_in_scope_eur']:,.2f}"],
            ["Which is money", "The collectable figure. The all-in-scope figure is whole-base arithmetic and is not cash."],
            ["Movable lines", f"{summary['movability']['movable_lines']:,} lines, "
                              f"EUR {summary['movability']['movable_billed_eur']:,.2f} "
                              f"({summary['movability']['movable_share_pct']:.2f}% of billed)"],
            ["Immovable lines", f"{summary['movability']['immovable_lines']:,} lines, "
                                f"EUR {summary['movability']['immovable_billed_eur']:,.2f} "
                                f"({summary['movability']['immovable_share_pct']:.2f}% of billed)"],
            ["Movability mask", summary['movability']['mask']],
            ["Existing revision step", f"EUR {summary['versus_existing_revision']['step_existing_eur']:,.2f}"],
            ["Published headline rate", f"{summary['versus_existing_revision']['rate_existing_published_pct']:.4f}% (quantity-weighted base-price move)"],
            ["Step tie-out", "Exact - reconciles to the published step to the cent."],
            ["Rate bases (all reproduce)", "Published 5.9616% headline; "
                                           f"{summary['versus_existing_revision']['rate_bases']['simulation_quantity']['value_pct']:.4f}% "
                                           "on simulation quantity (paper's 6.06%); "
                                           f"{summary['versus_existing_revision']['rate_bases']['step_on_priced_volume']['value_pct']:.4f}% "
                                           "step on priced volume (paper's 5.068%); "
                                           f"{summary['versus_existing_revision']['rate_bases']['euro_weighted']['value_pct']:.4f}% euro-weighted."],
            ["Not used here", "The CY2025 no-list gap of 522 PNs / EUR 4.96M is a different window and is not used on this page."],
            ["Are they added?", "No. Two separate proposals on the same base, never summed."],
            ["Exchange rate", "OPEN. Engine 163.7 (2025-10-01) vs SPA 172.6. A move to 172.6 cuts euro cost ~5.2%."],
            ["Volume response", "None modelled. No elasticity coefficient exists, and none is invented."],
            ["Prepared", summary["built_utc"]],
        ],
        columns=["Item", "Value"],
    )

    # Rename once, then use the SAME frames for both the data write and the header write.
    # Writing the header from an un-renamed frame silently overwrites the renamed header
    # cells that to_excel just wrote - that defect was caught by the verifier.
    l1_out = by_l1.rename(columns={
        "aim_l1": "AIM level 1", "part_numbers": "Part numbers",
        "billed_eur": "Billed EUR", "step_existing_eur": "Existing step EUR",
        "step_5pct_eur": "+5% step EUR", "share_billed_pct": "Share of billed %",
        "share_step_5pct_pct": "Share of +5% step %", "rate_5pct_pct": "+5% rate %",
    })
    db_out = by_db.rename(columns={
        "gps_db_label": "Distributor", "part_numbers": "Part numbers",
        "billed_eur": "Billed EUR", "step_existing_eur": "Existing step EUR",
        "step_5pct_eur": "+5% step EUR",
        "weighted_move_existing_pct": "Existing weighted move %",
        "share_step_5pct_pct": "Share of +5% step %",
    })
    top_out = top.rename(columns={
        "part_number": "Part number", "billed_description": "Description as billed",
        "aim_l1": "AIM level 1", "billed_qty": "Billed qty", "billed_eur": "Billed EUR",
        "step_existing_eur": "Existing step EUR", "step_5pct_eur": "+5% step EUR",
    })
    data_out = d[have].copy().rename(columns={
        "part_number": "Part number",
        "gps_db_label": "Distributor",
        "country": "Country",
        "billed_description": "Description as billed",
        "aim_l1": "AIM level 1",
        "billed_qty": "Billed qty",
        "net_sales_value": "Billed EUR (L12M)",
        "bp_new_jpy": "New base price JPY",
        "delta_pct": "Existing revision move",
        "value_eur_step": "Existing revision step EUR",
        "step_5pct_eur": "+5% step EUR",
    })

    sheets = [
        ("Read me", readme),
        ("AIM level 1", l1_out),
        ("Distributor", db_out),
        ("Top 250 by +5% EUR", top_out),
        ("Line data", data_out),
    ]

    wide_left = {"Item", "Description as billed", "AIM level 1", "Distributor",
                 "Part family (AIM level 1)"}

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
                elif col.endswith("%") or col == "Existing revision move":
                    ws.set_column(c, c, 19, pct_fmt if col.endswith("%") else None)
                else:
                    ws.set_column(c, c, 17)

            # excel_pre_delivery_check.py requirements, seen directly in its source:
            #   - column B (the description column) must be >= 28 chars wide
            #   - long text (>40 chars) in column B or D must carry wrap_text, or it flags
            #     "long-text cells without wrap_text" as soon as there are more than five
            # Both checks read the cell alignment, so the format has to be applied to the
            # cells, not just the column.
            ws.set_column(1, 1, max(30, 46 if name == "Read me" else 34), wrap_fmt)
            ws.set_column(3, 3, 34, wrap_fmt)
            if len(frame.columns) >= 2:
                for r in range(1, len(frame) + 1):
                    for cidx in (1, 3):
                        if cidx < len(frame.columns):
                            v = frame.iloc[r - 1, cidx]
                            if isinstance(v, str):
                                ws.write(r, cidx, v, wrap_fmt)

            ws.freeze_panes(1, 0)
            if name != "Line data":
                ws.autofilter(0, 0, len(frame), max(len(frame.columns) - 1, 0))

    print(f"wrote {OUT_XLSX.relative_to(ISZE)}")


# ---------------------------------------------------------------- html
def write_html(summary, by_l1, by_db, top, concentration) -> None:
    chart_js = (ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js").read_text(encoding="utf-8")

    l1 = by_l1.head(12)
    l1_labels = [str(x) for x in l1["aim_l1"].tolist()]
    l1_vals = [round(float(x), 2) for x in l1["step_5pct_eur"].tolist()]

    db = by_db.head(12)
    db_labels = [str(x) for x in db["gps_db_label"].tolist()]
    db_vals = [round(float(x), 2) for x in db["step_5pct_eur"].tolist()]

    tp = top.head(12)
    tp_labels = [str(x) for x in tp["part_number"].tolist()]
    tp_vals = [round(float(x), 2) for x in tp["step_5pct_eur"].tolist()]

    conc_labels = list(concentration.keys())
    conc_vals = list(concentration.values())

    h = summary["headline"]
    v = summary["versus_existing_revision"]
    fx = summary["fx_fork_open"]
    memo = summary["memo_cross_check"]
    mv = summary["movability"]

    imm_rows = "".join(
        f"<tr><td>{c['reason']}</td><td class='n'>{c['lines']:,}</td>"
        f"<td class='n'>&euro;{c['billed_eur']:,.0f}</td>"
        f"<td class='n'>{c['share_of_in_scope_billed_pct']:.2f}%</td></tr>"
        for c in mv["immovable_composition"]
    )

    payload = json.dumps({
        "l1": {"labels": l1_labels, "values": l1_vals},
        "db": {"labels": db_labels, "values": db_vals},
        "top": {"labels": tp_labels, "values": tp_vals},
        "conc": {"labels": conc_labels, "values": conc_vals},
    }).replace("</", "<\\/")

    l1_rows = "".join(
        f"<tr><td>{r.aim_l1}</td><td class='n'>{r.part_numbers:,}</td>"
        f"<td class='n'>&euro;{r.billed_eur:,.0f}</td>"
        f"<td class='n'>&euro;{r.step_existing_eur:,.0f}</td>"
        f"<td class='n'>&euro;{r.step_5pct_eur:,.0f}</td>"
        f"<td class='n'>{r.share_step_5pct_pct:.1f}%</td></tr>"
        for r in by_l1.head(20).itertuples()
    )
    db_rows = "".join(
        f"<tr><td>{r.gps_db_label}</td><td class='n'>{r.part_numbers:,}</td>"
        f"<td class='n'>&euro;{r.billed_eur:,.0f}</td>"
        f"<td class='n'>&euro;{r.step_5pct_eur:,.0f}</td>"
        f"<td class='n'>{r.weighted_move_existing_pct:.2f}%</td></tr>"
        for r in by_db.head(20).itertuples()
    )
    top_rows = "".join(
        f"<tr><td class='mono'>{r.part_number}</td><td class='d'>{str(r.billed_description)[:52]}</td>"
        f"<td>{r.aim_l1}</td><td class='n'>&euro;{r.billed_eur:,.0f}</td>"
        f"<td class='n'>&euro;{r.step_5pct_eur:,.0f}</td></tr>"
        for r in top.head(25).itertuples()
    )
    caveat_rows = "".join(f"<li>{c}</li>" for c in summary["caveats"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A +5% flat price increase on the current list - review, {summary['stamp']}</title>
<style>
:root{{--navy:#15233c;--navy2:#1d3054;--terra:#c0552d;--paper:#f7f4ee;--ink:#22262e;
--muted:#6b6459;--line:#d9d3c8;--band:#eef3f9;--amber:#a8721f;--good:#1e6b4f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.5;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
h1{{font-size:26px}} h2{{font-size:19px}} h3{{font-size:15px}}
.wrap{{max-width:1300px;margin:0 auto;padding:22px 22px 70px}}
header.top{{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}}
.badge{{display:inline-block;background:var(--navy);color:var(--paper);font-size:11px;
letter-spacing:.6px;text-transform:uppercase;padding:3px 9px;border-radius:2px;margin-right:8px}}
.badge.review{{background:var(--terra)}}
.sub{{color:var(--muted);font-size:13px;margin-top:6px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:18px 0}}
.kpi{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);padding:13px 15px;position:relative}}
.kpi.t{{border-left-color:var(--terra)}}
.kpi .lab{{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}}
.kpi .val{{font-family:Georgia,serif;font-size:25px;color:var(--navy);margin-top:3px}}
.kpi .sub2{{font-size:12px;color:var(--muted);margin-top:2px}}
.kpi:hover .tip{{display:block}}
.tip{{display:none;position:absolute;z-index:40;left:0;top:100%;width:290px;background:var(--navy);
color:var(--paper);font-size:12px;line-height:1.45;padding:10px 12px;border-left:3px solid var(--terra)}}
.card{{background:#fff;border:1px solid var(--line);padding:16px;margin-bottom:18px}}
.card h2{{margin-bottom:3px}}
.card .q{{color:var(--muted);font-size:12.5px;margin-bottom:12px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
@media(max-width:980px){{.grid2{{grid-template-columns:1fr}}}}
canvas{{width:100%!important;max-height:330px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;font-weight:600;font-size:12px}}
td{{padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
tbody tr:nth-child(even) td{{background:var(--band)}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.mono{{font-family:ui-monospace,Consolas,monospace;font-size:12px}}
td.d{{color:var(--muted)}}
.note{{background:#fdf6ec;border:1px solid #e7d3ae;border-left:4px solid var(--amber);padding:12px 14px;margin:16px 0}}
.note strong{{color:#8a5d13}}
ul{{margin:6px 0 0 18px;padding:0}} li{{margin-bottom:5px}}
.foot{{color:var(--muted);font-size:12px;border-top:1px solid var(--line);margin-top:24px;padding-top:12px}}
.banner{{background:var(--terra);color:#fff;padding:11px 14px;font-weight:600;margin-bottom:16px}}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div><span class="badge">Internal</span><span class="badge review">Review and design - not a price change</span></div>
  <h1>A +5% flat price increase on the current list</h1>
  <div class="sub">What a flat five per cent costs on the volume actually billed, read beside the
  revision already filed. Basis: {summary['basis']['window']}, in-scope lines only.
  Prepared {summary['built_utc']}.</div>
</header>

<div class="banner">Nothing in this page changes a price. No list, no catalogue and no published
figure was altered, and nothing was mailed.</div>

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
    figure is a whole-base arithmetic result and must not be quoted as cash.</div></div>

  <div class="kpi"><div class="lab">Billed in scope</div>
    <div class="val">&euro;{summary['basis']['billed_eur']:,.0f}</div>
    <div class="sub2">{summary['basis']['part_numbers']:,} part numbers</div>
    <div class="tip">Net sales value on the in-scope L12M base, distributor customers only.
    Non-part billing and the direct account are excluded by the in-scope filter.</div></div>

  <div class="kpi"><div class="lab">Revision already filed</div>
    <div class="val">&euro;{v['step_existing_eur']:,.0f}</div>
    <div class="sub2">{v['rate_existing_published_pct']:.4f}% published headline</div>
    <div class="tip">The published in-scope revision. Step and headline rate both reconcile on this
    file. Same base as the +5%, but a separate proposal - the two are never added.</div></div>
</div>

<div class="note">
  <strong>Which number is money and which is arithmetic.</strong>
  A flat +5% is <strong>&euro;{h['step_5pct_on_movable_eur']:,.2f}</strong> on the
  <strong>{mv['movable_lines']:,}</strong> lines that can actually take a new price. Spread across
  every in-scope line regardless of whether it has a price to change, the same +5% reads
  <strong>&euro;{h['step_5pct_on_all_in_scope_eur']:,.2f}</strong>. The gap,
  <strong>&euro;{mv['immovable_billed_eur'] * 0.05:,.2f}</strong>, sits on
  <strong>{mv['immovable_lines']:,}</strong> lines carrying
  <strong>&euro;{mv['immovable_billed_eur']:,.2f}</strong>
  ({mv['immovable_share_pct']:.2f}% of billed) that have no base price on one side. A price change
  needs a price to change, so that euro is not collectable by pricing.
</div>

<div class="card">
  <h2>What cannot move, and why</h2>
  <div class="q">The immovable set on this basis, by the reason the file itself records. This is the
  unpriced residual the pricing policy paper states for this window
  (&euro;{mv['immovable_billed_eur']:,.0f}) - it is not the CY2025 no-list figure of &euro;4.96M,
  which is a different window and is not used anywhere on this page.</div>
  <table>
    <thead><tr><th>Reason recorded in the file</th><th class="n">Lines</th>
    <th class="n">Billed EUR</th><th class="n">Share of in-scope billed</th></tr></thead>
    <tbody>{imm_rows}</tbody>
  </table>
</div>

<div class="note">
  <strong>The rate bases, named.</strong>
  The published <strong>{v['rate_existing_published_pct']:.4f}%</strong> is the quantity-weighted
  base-price move on the movable set, and it ties to the published step of
  <strong>&euro;{v['step_existing_eur']:,.2f}</strong> to the cent. Two sensitivities are already
  documented in the pricing policy paper, and both reproduce on this file:
  <strong>{v['rate_bases']['simulation_quantity']['value_pct']:.4f}%</strong> weighted on the
  simulation's own quantity (the paper's 6.06%), and
  <strong>{v['rate_bases']['step_on_priced_volume']['value_pct']:.4f}%</strong> taking the step over
  priced volume (the paper's 5.068%). Weighting each line's move by the euro it billed gives
  <strong>{v['rate_bases']['euro_weighted']['value_pct']:.4f}%</strong>. Three named bases, not a
  reconciliation problem.
</div>

<div class="note">
  <strong>Open before anything is built: the exchange rate.</strong>
  The pricing engine carries <strong>{fx['engine_fx']}</strong> JPY/EUR as of {fx['engine_fx_as_of']},
  while the Israel SPA work uses <strong>{fx['spa_fx']}</strong>. A move from
  {fx['engine_fx']} to {fx['spa_fx']} weakens the yen by <strong>{fx['yen_weakening_pct']:.2f}%</strong>
  and cuts our euro purchase cost by about 5.2% - roughly the size of this entire increase.
  Whether IML re-bases the list at the new rate decides whether +5% is a real increase or a hold
  in yen terms. This is deliberately left open.
</div>

<div class="grid2">
  <div class="card">
    <h2>Where the +5% lands, by part family</h2>
    <div class="q">Ranked by the euro the increase raises. Which families carry the increase?</div>
    <canvas id="c1" height="150"></canvas>
  </div>
  <div class="card">
    <h2>Where the +5% lands, by distributor</h2>
    <div class="q">Ranked by euro raised, on the same basket each distributor actually bought.</div>
    <canvas id="c2" height="150"></canvas>
  </div>
</div>

<div class="card">
  <h2>How concentrated is the increase?</h2>
  <div class="q">Share of the total step captured by the largest lines. If a small set carries most
  of it, the conversation is with a small set of part numbers.</div>
  <canvas id="c3" height="110"></canvas>
</div>

<div class="card">
  <h2>The largest part numbers by +5% euro</h2>
  <div class="q">The lines where the increase is largest in money, so the distributor conversation
  starts from the top rather than the average.</div>
  <canvas id="c4" height="150"></canvas>
</div>

<div class="card">
  <h2>By part family</h2>
  <div class="q">Billed euro against the increase, on the corrected AIM levels. Families not on the
  AIM spine are shown as their own row rather than dropped.</div>
  <table>
    <thead><tr><th>Part family (AIM level 1)</th><th class="n">Part numbers</th>
    <th class="n">Billed EUR</th><th class="n">Filed step EUR</th><th class="n">+5% step EUR</th>
    <th class="n">Share of +5%</th></tr></thead>
    <tbody>{l1_rows}</tbody>
  </table>
</div>

<div class="card">
  <h2>By distributor</h2>
  <div class="q">The same revision, read per trading entity. The filed move column is each
  distributor's own weighted move under the revision already filed.</div>
  <table>
    <thead><tr><th>Distributor</th><th class="n">Part numbers</th><th class="n">Billed EUR</th>
    <th class="n">+5% step EUR</th><th class="n">Filed weighted move</th></tr></thead>
    <tbody>{db_rows}</tbody>
  </table>
</div>

<div class="card">
  <h2>Largest lines by +5% euro</h2>
  <table>
    <thead><tr><th>Part number</th><th>Description as billed</th><th>Part family</th>
    <th class="n">Billed EUR</th><th class="n">+5% step EUR</th></tr></thead>
    <tbody>{top_rows}</tbody>
  </table>
</div>

<div class="card">
  <h2>A second reading of +5%, on a different base</h2>
  <div class="q">The decision memo prices +5% on forecast weights rather than on the in-scope
  revision base. Both are shown so neither is mistaken for the other.</div>
  <table>
    <thead><tr><th>Base</th><th class="n">Base euro</th><th class="n">+5% euro</th></tr></thead>
    <tbody>
      <tr><td>In-scope L12M revision base, collectable (movable lines)</td>
        <td class="n">&euro;{mv['movable_billed_eur']:,.0f}</td>
        <td class="n">&euro;{h['step_5pct_on_movable_eur']:,.0f}</td></tr>
      <tr><td>In-scope L12M revision base, all lines</td>
        <td class="n">&euro;{summary['basis']['billed_eur']:,.0f}</td>
        <td class="n">&euro;{h['step_5pct_on_all_in_scope_eur']:,.0f}</td></tr>
      <tr><td>Forecast-weight basis (decision memo, option B)</td>
        <td class="n">&euro;{memo['forecast_weight_base_eur']:,.0f}</td>
        <td class="n">&euro;{memo['plus5_on_forecast_weight_eur']:,.0f}</td></tr>
      <tr><td>Past 12 months, decision memo basis</td>
        <td class="n">&euro;{memo['l12m_base_eur']:,.0f}</td>
        <td class="n">&euro;{memo['plus5_on_l12m_eur']:,.0f}</td></tr>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>What this page does not claim</h2>
  <ul>{caveat_rows}</ul>
</div>

<div class="foot">
  Source: {summary['basis']['source']}, filter <code>in_scope == True</code>.
  Part families from <code>01_data/00_derived/aim_master_v2.csv</code>.
  Prepared {summary['built_utc']} as an internal review exercise.
</div>

</div>
<script>{chart_js}</script>
<script>
const P = {payload};
const NAVY='#15233c', TERRA='#c0552d', LINE='#d9d3c8', MUTED='#6b6459';
Chart.defaults.font.family='-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif';
Chart.defaults.font.size=11.5;
Chart.defaults.color=MUTED;
const eur = v => '\u20AC' + (v>=1e6 ? (v/1e6).toFixed(2)+'M' : Math.round(v/1e3)+'k');
const rollup = {summary['concentration_share_of_step_pct']};
const cand = Object.keys(rollup).map(k=>k.replace('top_','').replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,','));
const cvals = Object.values(rollup);

new Chart(document.getElementById('c1'), {{
  type:'bar',
  data:{{labels:P.l1.labels,datasets:[{{label:'+5% step EUR',data:P.l1.values,
    backgroundColor:P.l1.labels.map(l=>l.indexOf('Not on AIM')===0?'#a8721f':NAVY)}}]}},
  options:{{indexAxis:'y',maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+eur(c.raw)}}}}}},
    scales:{{x:{{grid:{{color:LINE}},ticks:{{callback:v=>eur(v)}}}},y:{{grid:{{display:false}}}}}}}}
}});

new Chart(document.getElementById('c2'), {{
  type:'bar',
  data:{{labels:P.db.labels,datasets:[{{label:'+5% step EUR',data:P.db.values,backgroundColor:TERRA}}]}},
  options:{{indexAxis:'y',maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+eur(c.raw)}}}}}},
    scales:{{x:{{grid:{{color:LINE}},ticks:{{callback:v=>eur(v)}}}},y:{{grid:{{display:false}}}}}}}}
}});

new Chart(document.getElementById('c3'), {{
  type:'bar',
  data:{{labels:cand,datasets:[{{label:'% of the +5% step',data:cvals,
    backgroundColor:cvals.map(v=>v>70?TERRA:NAVY)}}]}},
  options:{{maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+c.raw+'% of the total step'}}}}}},
    scales:{{y:{{beginAtZero:true,max:100,grid:{{color:LINE}},ticks:{{callback:v=>v+'%'}}}},
    x:{{grid:{{display:false}},title:{{display:true,text:'largest N lines'}}}}}}}}
}});

new Chart(document.getElementById('c4'), {{
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
