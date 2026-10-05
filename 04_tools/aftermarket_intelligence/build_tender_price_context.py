# -*- coding: utf-8 -*-
"""Connect the tender engine to the parts price data.

WHY THIS EXISTS
---------------
These were two separate programmes. The tender engine knows, per live notice, which
parts categories a fleet will consume and what that demand is worth — but it values it
at **our own** price (`avg_sp_eur`). Nothing in it knows what the aftermarket charges.
The parts side knows competitor prices for a small number of part numbers but has no
idea which of them matter commercially.

This script joins them on one key: the parts category.

    tender notice  ->  pms_category  ->  our part numbers in that category
                                    ->  do any of those carry a competitor observation?

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not claim we know competitor prices broadly. Only a small number of part
numbers carry one today. So the honest output is a **coverage** statement per notice:
of the parts this fleet will need, how many can we actually benchmark, and what is the
basket worth. That tells us both what we know and how far the scraper still has to go.

Output:
  01_data/00_derived/tender_price_context.csv   one row per opportunity x category
  01_data/00_derived/tender_price_context.meta.json

Run:  python 04_tools/aftermarket_intelligence/build_tender_price_context.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parents[2]
TENDER = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
CATALOG = ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv"
LEDGER = ROOT / "01_data" / "00_derived" / "price_observations.parquet"
OUT = ROOT / "01_data" / "00_derived" / "tender_price_context.csv"
META = OUT.with_suffix(".meta.json")

# Price types that are an AFTERMARKET BRAND's price — the real rival.
# 2026-10-01 on Jerome's go: `genuine_grey` and `dealer` used to sit in this set. They are
# a genuine Isuzu part sold outside our network (Amayama, KS genuine listings), not an
# aftermarket brand, and counting them overstated coverage roughly 2.5x (166 parts against
# 66 aftermarket-only across the 14 families). They now go in separate `genuine_*` columns.
# `estimate` and `oem_value_line` are modelled or our own value line, so they are in neither.
RIVAL_PRICE_TYPES = {
    "aftermarket_retail", "aftermarket_trade", "aftermarket_rrp",
    "online_median", "marketplace", "quote", "survey_workshop", "survey_list",
}
GENUINE_PRICE_TYPES = {"genuine_grey", "dealer"}


def load_category_map() -> pd.DataFrame:
    """part_number -> pms_category, from the catalogue."""
    d = pd.read_csv(CATALOG, dtype=str, usecols=["part_number", "pms_category"])
    d = d[d["pms_category"].notna() & (d["pms_category"].astype(str).str.strip() != "")]
    return d.drop_duplicates("part_number")


def load_observed() -> pd.DataFrame:
    """Every part number that carries an observed price, and by whom."""
    d = pd.read_parquet(LEDGER)
    d = d[d["price"].notna()].copy()
    d["part_no"] = d["part_no"].astype(str)
    return d


def main() -> int:
    for p in (TENDER, CATALOG, LEDGER):
        if not p.exists():
            print(f"REFUSED — missing input: {p}")
            return 1

    tender = json.loads(TENDER.read_text(encoding="utf-8"))
    notices = tender.get("notices", [])
    cat_map = load_category_map()
    obs = load_observed()

    print(f"notices                       : {len(notices):,}")
    print(f"catalogue parts with a category: {len(cat_map):,}")
    print(f"observed price rows           : {len(obs):,}")
    print(f"  of which a rival price      : "
          f"{int(obs['price_type'].isin(RIVAL_PRICE_TYPES).sum()):,}")

    # parts carrying at least one rival observation
    rival = obs[obs["price_type"].isin(RIVAL_PRICE_TYPES)]
    genuine = obs[obs["price_type"].isin(GENUINE_PRICE_TYPES)].copy()
    rival_by_pn = rival.groupby("part_no").agg(
        n_obs=("price", "size"),
        min_price=("price", "min"),
        max_price=("price", "max"),
        sources=("source", lambda s: "|".join(sorted(set(s)))),
        currencies=("currency", lambda s: "|".join(sorted(set(s.dropna())))),
        price_types=("price_type", lambda s: "|".join(sorted(set(s)))),
    )

    # which categories do our observed parts fall in?
    cat_of_pn = dict(zip(cat_map["part_number"], cat_map["pms_category"]))
    rival = rival.copy()
    rival["pms_category"] = rival["part_no"].map(cat_of_pn)
    genuine["pms_category"] = genuine["part_no"].map(cat_of_pn)
    cats_with_price = set(rival["pms_category"].dropna())
    print(f"\nobserved part numbers         : {rival['part_no'].nunique():,}")
    print(f"  landing in a known category : {int(rival['pms_category'].notna().sum()):,} rows")
    print(f"  distinct categories covered : {len(cats_with_price)}")

    # how many of OUR parts exist per category (the denominator)
    parts_per_cat = cat_map.groupby("pms_category")["part_number"].nunique()

    # 2026-10-01: read OPPORTUNITIES, not notices. Reading notices counted a tender twice
    # when two notices sat under one opportunity (28 identical repeat rows), and kept demand
    # the opportunity layer had already blanked (van / repair-only / weak fit, e.g. a
    # 740-vehicle whole-fleet count on a tender for one other brand's machines).
    opportunities = tender.get("opportunities", [])
    notices_with_cats = sum(1 for n in notices if n.get("pms_demand_by_category"))
    opps_dropped_by_opp_layer = len(
        {n.get("opportunity_id") for n in notices if n.get("pms_demand_by_category")}
        - {o.get("opportunity_id") for o in opportunities if o.get("pms_demand_by_category")}
    )

    rows = []
    opps_with_cats = 0
    for n in opportunities:
        demand = n.get("pms_demand_by_category")
        if not demand:
            continue
        opps_with_cats += 1
        for item in demand:
            cat = item.get("pms_category")
            if not cat:
                continue
            total_parts = int(parts_per_cat.get(cat, 0))
            priced_rows = rival[rival["pms_category"] == cat]
            priced_pns = int(priced_rows["part_no"].nunique())
            gen_rows = genuine[genuine["pms_category"] == cat]
            gen_pns = int(gen_rows["part_no"].nunique())

            rows.append({
                "opportunity_id": n.get("opportunity_id"),
                "title": n.get("title"),
                "country": n.get("country"),
                "buyer": n.get("buyer"),
                "distributor_code": n.get("distributor_code"),
                "ids_dealer_name": n.get("ids_dealer_name"),
                "product_segment": n.get("product_segment"),
                "fleet_size": n.get("fleet_size"),
                "deadline": n.get("deadline_date"),
                "pms_category": cat,
                "category_label": item.get("category_label"),
                "expected_qty": item.get("expected_qty"),
                "addressable_eur": item.get("addressable_eur"),
                "our_avg_sp_eur": item.get("avg_sp_eur"),
                # the join: what we can actually benchmark
                "our_parts_in_category": total_parts,
                "parts_with_rival_price": priced_pns,
                "coverage_pct": round(100 * priced_pns / total_parts, 2) if total_parts else None,
                "rival_min_eur": (round(float(priced_rows["price_eur"].min()), 2)
                                  if priced_pns and priced_rows["price_eur"].notna().any() else None),
                "rival_max_eur": (round(float(priced_rows["price_eur"].max()), 2)
                                  if priced_pns and priced_rows["price_eur"].notna().any() else None),
                "rival_sources": "|".join(sorted(set(priced_rows["source"]))) if priced_pns else "",
                # genuine Isuzu parts sold outside our network — shown, never counted as rival
                "parts_with_genuine_price": gen_pns,
                "genuine_coverage_pct": round(100 * gen_pns / total_parts, 2) if total_parts else None,
                "genuine_min_eur": (round(float(gen_rows["price_eur"].min()), 2)
                                    if gen_pns and gen_rows["price_eur"].notna().any() else None),
                "genuine_max_eur": (round(float(gen_rows["price_eur"].max()), 2)
                                    if gen_pns and gen_rows["price_eur"].notna().any() else None),
                "genuine_sources": "|".join(sorted(set(gen_rows["source"]))) if gen_pns else "",
            })

    out = pd.DataFrame(rows)
    if out.empty:
        print("\nno opportunity carries category demand — nothing to join")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    covered = out[out["parts_with_rival_price"] > 0]
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "04_tools/aftermarket_intelligence/build_tender_price_context.py",
        "join_key": "pms_category (tender demand -> our part numbers -> observed rival prices)",
        "notices_total": len(notices),
        "notices_with_category_demand": notices_with_cats,
        "opportunities_total": len(opportunities),
        "opportunities_with_category_demand": opps_with_cats,
        "opportunities_blanked_by_opportunity_layer": opps_dropped_by_opp_layer,
        "unit": "one row per opportunity x category; addressable_eur is per year at our avg selling price",
        "rows": int(len(out)),
        "categories_touched": int(out["pms_category"].nunique()),
        "rows_with_any_rival_price": int(len(covered)),
        "observed_part_numbers_total": int(rival["part_no"].nunique()),
        "rival_definition": "aftermarket-brand prices only: " + ", ".join(sorted(RIVAL_PRICE_TYPES)),
        "genuine_definition": "genuine Isuzu sold outside our network, separate columns: "
                              + ", ".join(sorted(GENUINE_PRICE_TYPES)),
        "genuine_part_numbers_total": int(genuine["part_no"].nunique()),
        "honest_note": (
            "The tender engine values a fleet's parts demand at OUR price. This file adds "
            "the competitive side, but only where an observed rival price exists. Most "
            "categories currently show 0% coverage because the parts scraper has only "
            "covered a small number of part numbers — do not read a blank as 'no competitor'."
        ),
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*78}")
    print(f"notices with category demand : {notices_with_cats} of {len(notices)}")
    print(f"opportunities with demand    : {opps_with_cats} of {len(opportunities)} "
          f"({opps_dropped_by_opp_layer} blanked by the opportunity layer)")
    print(f"rows written                 : {len(out)}")
    print(f"categories touched           : {out['pms_category'].nunique()}")
    print(f"rows with any rival price    : {len(covered)}")
    print(f"\nwrote {OUT}")
    print(f"wrote {META}")

    print(f"\n{'category':<20} {'notices':>8} {'our parts':>10} {'with rival':>11} {'basket EUR':>12}")
    print("-" * 66)
    g = out.groupby("pms_category").agg(
        notices=("opportunity_id", "nunique"),
        our_parts=("our_parts_in_category", "max"),
        with_rival=("parts_with_rival_price", "max"),
        basket=("addressable_eur", "sum"),
    ).sort_values("basket", ascending=False)
    for cat, r in g.iterrows():
        print(f"{str(cat):<20} {int(r['notices']):>8} {int(r['our_parts']):>10} "
              f"{int(r['with_rival']):>11} {float(r['basket']):>12,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
