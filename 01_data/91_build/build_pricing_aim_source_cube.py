#!/usr/bin/env python3
"""Pricing revision x AIM x source of supply (TH / JP) - one cube, three outputs.

Basis (single, locked):
  price_bp_weighted_compare_pn.csv, in_scope == True, window 2025-07-01..2026-06-30.
  QA rows 47,617 / 15,273 part numbers / 25 in-scope customers.
  Network tie-out: step EUR 1,652,140.71 and weighted 5.9616% - the published revision.

Axes
  DB        gps_db_label (distributor trading entity, Portugal's two sold-to roll into Imotors,
            Germany's two into ISD)
  AIM       aim_l1_fixed / aim_l2_fixed / aim_l3  (the taxonomy Jerome fixed 2026-09-17)
  SOURCE    source of supply, J = Japan through IML, T = Thailand through IMIT

AIM L3 is populated on only ~14% of part numbers. It is kept, with an explicit
"Not classified at L3" bucket, so the gap shows instead of hiding.

Outputs
  01_data/00_derived/pricing_aim_source_lines.parquet   row level (for the workbook data sheet)
  01_data/00_derived/pricing_aim_source_cube.csv        DB x AIM L1 x L2 x L3 x source
  01_data/00_derived/pricing_aim_source_meta.json       coverage, tie-out, caveats

Run: python 01_data/91_build/build_pricing_aim_source_cube.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"

PN = D / "price_bp_weighted_compare_pn.csv"
AIM = D / "aim_master_v2.csv"
SIM = D / "pricing_sim_pr00_l12m.parquet"
LIST = D / "pricing_list_pn.parquet"
DIM = D / "distributor_dimension.csv"

OUT_LINES = D / "pricing_aim_source_lines.parquet"
OUT_CUBE = D / "pricing_aim_source_cube.csv"
OUT_META = D / "pricing_aim_source_meta.json"

FX = 163.7

PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None", "NaN"}
NA = "Not on AIM spine"
NA_L3 = "Not classified at L3"
NA_SRC = "Not held"
SRC_LABEL = {"J": "JP - Japan / IML", "T": "TH - Thailand / IMIT"}
SRC_SHORT = {"J": "JP - Japan", "T": "TH - Thailand"}


def main() -> int:
    # ------------------------------------------------------------------ base
    pn = pd.read_csv(PN, dtype={"part_number": str}, low_memory=False)
    pn["part_number"] = pn["part_number"].astype(str).str.zfill(10)
    pn["customer_code"] = (
        pn["customer_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    )
    ins = pn[pn["in_scope"].astype(str).str.lower().isin(["true", "1"])].copy()
    ins["priced_both"] = ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna()

    tot_rows = len(ins)
    tot_pn = ins["part_number"].nunique()
    tot_billed = float(ins["net_sales_value"].sum())
    pr = ins[ins["priced_both"]]
    tot_step = float(pr["value_eur_step"].sum())
    q = pr["billed_qty"].astype(float)
    prior_eur = float((q * pr["bp_prior_revised"].astype(float)).sum() / FX)
    new_eur = float((q * pr["bp_new_jpy"].astype(float)).sum() / FX)
    net_weighted = 100 * (new_eur / prior_eur - 1)

    # ------------------------------------------------------------------ AIM
    aim = pd.read_csv(AIM, dtype=str, low_memory=False)
    aim["part_number"] = aim["part_number"].astype(str).str.zfill(10)
    aim = aim.drop_duplicates("part_number")
    for c, src in (("aim_l1", "aim_l1_fixed"), ("aim_l2", "aim_l2_fixed"),
                   ("aim_l3", "aim_l3")):
        aim[c] = aim[src].astype(str).str.strip()
    aim_cols = aim[["part_number", "aim_l1", "aim_l2", "aim_l3",
                    "price_class_iml", "cat_pms_flag", "fig_key"]]

    # ------------------------------------------------------------------ source
    sim = pd.read_parquet(SIM, columns=["part_number", "source"])
    sim["part_number"] = sim["part_number"].astype(str).str.zfill(10)
    sim_src = (sim.dropna(subset=["source"]).drop_duplicates("part_number")
                  .set_index("part_number")["source"])

    lp = pd.read_parquet(LIST, columns=["part_number", "source"])
    lp["part_number"] = lp["part_number"].astype(str).str.zfill(10)
    lp = lp.dropna(subset=["source"])
    uniq = lp.groupby("part_number")["source"].nunique()
    single = set(uniq[uniq == 1].index)
    list_src = (lp[lp["part_number"].isin(single)].drop_duplicates("part_number")
                  .set_index("part_number")["source"])
    conflict = set(uniq[uniq > 1].index)

    # ------------------------------------------------------------------ assemble
    df = ins.merge(aim_cols, on="part_number", how="left")
    df["source"] = df["part_number"].map(sim_src)
    df["source"] = df["source"].fillna(df["part_number"].map(list_src))
    df.loc[df["part_number"].isin(conflict) & df["source"].isna(), "source"] = "X"

    df["db"] = df["gps_db_label"].fillna("Unknown").astype(str).str.strip()
    on_spine = ~df["aim_l1"].isin(PLACEHOLDER) & df["aim_l1"].notna()
    df["on_spine"] = on_spine
    df["aim_l1"] = np.where(on_spine, df["aim_l1"], NA)
    df["aim_l2"] = np.where(on_spine & ~df["aim_l2"].isin(PLACEHOLDER), df["aim_l2"], "")
    df["aim_l2"] = np.where(df["aim_l1"] == NA, NA, df["aim_l2"].replace("", NA_L3))
    df["aim_l2"] = np.where((df["aim_l1"] != NA) & (df["aim_l2"] == NA_L3), NA_L3, df["aim_l2"])
    df["aim_l3"] = np.where(on_spine & ~df["aim_l3"].isin(PLACEHOLDER), df["aim_l3"], NA_L3)
    df["source"] = df["source"].fillna(NA_SRC)
    df["source_label"] = df["source"].map(SRC_SHORT).fillna(NA_SRC)

    qq = df["billed_qty"].astype(float)
    df["billed_eur"] = df["net_sales_value"].astype(float)
    df["priced? "] = df["priced_both"]
    df["prior_eur"] = np.where(df["priced_both"], qq * df["bp_prior_revised"].astype(float) / FX, np.nan)
    df["new_eur"] = np.where(df["priced_both"], qq * df["bp_new_jpy"].astype(float) / FX, np.nan)
    df["step_eur"] = df["value_eur_step"].astype(float).fillna(0.0)
    df["delta_pct"] = df["delta_pct"].astype(float)
    df["price_class"] = df["bp_new_class"].fillna("")

    # customer name as billed, so the workbook can show the account behind the code
    df["customer_name"] = (
        df["sold_to_names"].astype(str).str.replace(r"^\[|\]$", "", regex=True)
        .str.split(",").str[0].str.strip().str.strip("'\"")
    )
    cust_fix = {
        "2575": "ISUZU TRUCK (UK) LIMITED", "2574": "IUK", "1799": "UTI Israel",
        "1797": "UMI Israel", "90": "IBX Belgium", "2516": "ISD Germany (2516)",
        "601": "ISD Germany (601)", "519": "Imotors Portugal (519)",
        "92": "Imotors Portugal (92)", "86": "Rutebileiernes Standardisering",
        "2181": "Sverige", "76": "Ireland", "2294": "Komtranskomplekt (Ukraine)",
        "66": "RSA Greece", "393": "Loutsios Cyprus", "537": "AutoWallis Hungary",
        "2679": "Nordic Finland", "2733": "Grand Avto Armenia", "1759": "GasanZammit Malta",
        "396": "ROM Auto Romania", "2734": "CBC-Trans Kazakhstan", "2027": "Danmark (2027)",
        "2751": "Danmark (2751)", "1576": "BL Iceland", "2372": "KIMA Palestine",
    }
    df["customer_name"] = [cust_fix.get(c, n) for c, n in
                           zip(df["customer_code"], df["customer_name"])]

    lines = df[[
        "db", "customer_code", "customer_name",
        "aim_l1", "aim_l2", "aim_l3", "source_label",
        "part_number", "billed_description", "price_class",
        "billed_qty", "billed_eur", "priced_both", "bp_prior_revised", "bp_new_jpy",
        "prior_eur", "new_eur", "step_eur", "delta_pct",
    ]].rename(columns={
        "billed_description": "description",
        "billed_qty": "qty",
        "source_label": "source",
        "bp_prior_revised": "prior_base_jpy",
        "bp_new_jpy": "new_base_jpy",
    })
    lines.to_parquet(OUT_LINES, index=False)

    # ------------------------------------------------------------------ cube
    # Spine = every in-scope key, including Not held / unpriced-only groups.
    # A left-join from the priced book used to drop those keys, so TH-JP and the
    # HTML Not held filter only saw ~EUR 1.3k of a ~EUR 2.23M Not held pile.
    prd = df[df["priced_both"]].copy()
    keys = ["db", "aim_l1", "aim_l2", "aim_l3", "source_label"]
    allrow = (df.groupby(keys, dropna=False)
              .apply(lambda g: pd.Series({
                  "pn": g["part_number"].nunique(),
                  "rows": len(g),
                  "qty": float(g["billed_qty"].astype(float).sum()),
                  "in_scope_eur": float(g["billed_eur"].sum()),
              }), include_groups=False)
              .reset_index())
    priced = (prd.groupby(keys, dropna=False)
              .apply(lambda g: pd.Series({
                  "billed_eur": float(g["billed_eur"].sum()),
                  "prior_eur": float(g["prior_eur"].sum()),
                  "new_eur": float(g["new_eur"].sum()),
                  "step_eur": float(g["step_eur"].sum()),
              }), include_groups=False)
              .reset_index())
    # one source per key by construction (source_label is in the group keys)
    priced["n_sources"] = 1
    cube = allrow.merge(priced, on=keys, how="left")
    for c in ("billed_eur", "prior_eur", "new_eur", "step_eur", "n_sources"):
        cube[c] = cube[c].fillna(0.0)
    cube["weighted_pct"] = np.where(
        cube["prior_eur"] > 0, 100 * (cube["new_eur"] / cube["prior_eur"] - 1), np.nan)
    cube = cube.rename(columns={"source_label": "source"})
    cube.to_csv(OUT_CUBE, index=False)

    # ------------------------------------------------------------------ coverage
    cov_src = (df.groupby("source_label")["billed_eur"].sum()
               .sort_values(ascending=False).round(2).to_dict())
    cov_src_priced = (prd.groupby("source_label")["billed_eur"].sum()
                      .sort_values(ascending=False).round(2).to_dict())
    matched_eur = float(df.loc[df["on_spine"], "billed_eur"].sum())
    l3_filled = float(df.loc[df["aim_l3"] != NA_L3, "billed_eur"].sum())

    by_db = (df.groupby("db")
             .agg(pn=("part_number", "nunique"), rows=("billed_eur", "size"),
                  billed_eur=("billed_eur", "sum"), step_eur=("step_eur", "sum"))
             .sort_values("billed_eur", ascending=False))
    prd_db = prd.groupby("db").apply(
        lambda g: pd.Series({"prior_eur": g["prior_eur"].sum(),
                             "new_eur": g["new_eur"].sum()}), include_groups=False)
    by_db["prior_eur"] = prd_db["prior_eur"]
    by_db["new_eur"] = prd_db["new_eur"]
    by_db["weighted_pct"] = (100 * (by_db["new_eur"] / by_db["prior_eur"] - 1)).round(4)

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "built_by": "01_data/91_build/build_pricing_aim_source_cube.py",
        "basis": {
            "file": "price_bp_weighted_compare_pn.csv",
            "filter": "in_scope == True",
            "window": ["2025-07-01", "2026-06-30"],
            "fx_jpy_per_eur": FX,
            "rows_in_scope": int(tot_rows),
            "part_numbers_in_scope": int(tot_pn),
            "in_scope_billed_eur": round(tot_billed, 2),
            "rows_priced_both_sides": int(len(pr)),
            "priced_billed_eur": round(float(pr["net_sales_value"].sum()), 2),
            "step_eur": round(tot_step, 2),
            "weighted_pct": round(net_weighted, 4),
        },
        "tie_out": {
            "step_matches_published": abs(tot_step - 1652140.71) < 0.01,
            "weighted_matches_published": abs(round(net_weighted, 4) - 5.9616) < 0.0002,
        },
        "taxonomy": {
            "spine": "aim_master_v2.csv -> aim_l1_fixed / aim_l2_fixed / aim_l3",
            "l1_values": int(df.loc[df["on_spine"], "aim_l1"].nunique()),
            "l2_values": int(df.loc[df["on_spine"] & (df["aim_l2"] != NA_L3), "aim_l2"].nunique()),
            "l3_values": int(df.loc[df["aim_l3"] != NA_L3, "aim_l3"].nunique()),
            "eur_on_aim_spine": round(matched_eur, 2),
            "eur_on_aim_spine_pct": round(100 * matched_eur / tot_billed, 2),
            "eur_with_l3": round(l3_filled, 2),
            "eur_with_l3_pct": round(100 * l3_filled / tot_billed, 2),
            "not_on_spine_bucket": NA,
            "l3_gap_bucket": NA_L3,
        },
        "source_of_supply": {
            "rule": ("pricing_sim_pr00_l12m.parquet, filled from pricing_list_pn.parquet "
                     "where that part number carries exactly one source"),
            "billed_eur_by_source_in_scope": cov_src,
            "billed_eur_by_source_priced": cov_src_priced,
            "share_of_in_scope_eur_labeled_pct": round(
                100 * sum(v for k, v in cov_src.items() if k != NA_SRC) / tot_billed, 2),
        },
        "by_db": by_db.round(2).to_dict("index"),
        "caveats": [
            "The weighted % is a base-price move on qty-weighted prior base price. "
            "It is not a revenue, margin or elasticity outcome.",
            "Source of supply is J/T from the pricing model plus the price list. "
            "Where it is not held the row is kept and labeled, never dropped.",
            "Israel is reported as UMI (1797) and UTI (1799) separately, never blended.",
            "AIM L3 is populated on a minority of part numbers; the explicit bucket is shown.",
            "The customer level in this pricing file is the distributor trading entity "
            "(gps_db_label), which is what the pricing enquiry was run on. "
            "It is not dealer level - sales_fact carries no dealer key.",
        ],
        "outputs": [str(OUT_LINES.relative_to(ISZE)), str(OUT_CUBE.relative_to(ISZE))],
    }
    OUT_META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    print("=" * 78)
    print("PRICING x AIM x SOURCE")
    print("=" * 78)
    print(f"in-scope rows            : {tot_rows:,}  ({tot_pn:,} part numbers)")
    print(f"in-scope billed EUR      : {tot_billed:,.2f}")
    print(f"priced both sides        : {len(pr):,} rows, "
          f"EUR {float(pr['net_sales_value'].sum()):,.2f}")
    print(f"step EUR                 : {tot_step:,.2f}   (published 1,652,140.71)")
    print(f"weighted increase        : {net_weighted:.4f}%   (published 5.9616%)")
    print(f"tie-out                  : {meta['tie_out']}")
    print()
    print(f"AIM spine coverage       : EUR {matched_eur:,.0f} "
          f"({100 * matched_eur / tot_billed:.2f}% of in-scope)")
    print(f"AIM L3 coverage          : EUR {l3_filled:,.0f} "
          f"({100 * l3_filled / tot_billed:.2f}%)")
    print(f"L1/L2/L3 values          : {meta['taxonomy']['l1_values']}/"
          f"{meta['taxonomy']['l2_values']}/{meta['taxonomy']['l3_values']}")
    print()
    print("source of supply, in-scope billed EUR:")
    for k, v in cov_src.items():
        print(f"  {k:<22} {v:>15,.2f}  {100 * v / tot_billed:6.2f}%")
    print()
    print("weighted increase per DB:")
    print(by_db[["pn", "rows", "billed_eur", "step_eur", "weighted_pct"]].round(2).to_string())
    print()
    print(f"cube rows  : {len(cube):,}")
    print(f"-> {OUT_LINES.name}")
    print(f"-> {OUT_CUBE.name}")
    print(f"-> {OUT_META.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
