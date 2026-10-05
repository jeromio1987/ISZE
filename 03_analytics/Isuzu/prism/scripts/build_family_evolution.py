#!/usr/bin/env python3
"""
Join the EPC decode to the billing and build the evolution by family, per customer, CY and FY.

This is the deliverable behind the whole tonnage question: the EPC tells us which vehicle family
each part number fits, and the billing tells us when and where it sold. Together they give units and
euro by family, by market, by year — on both clocks — from measured fitment rather than inference.

What the decode gives, and its limit
------------------------------------
`epc_decode_batch1_20260919.json` carries, per part number, the vehicle families it fits:
PASSENGER VEHICLE PICK UP / SUV (light), TRUCKS N (N-series), TRUCKS F&G and TRUCKS C&E (heavy),
BUSES, INDUSTRIAL, COMPONENT.

That is a **family** split, not a tonnage split. `TRUCKS N` spans NLR through NQR, so it does not
separate 3.5 t from 7.5 t. This script therefore reports families: light / N-series / heavy / bus /
other. The tonnage split needs the separate model-code table and is deliberately NOT attempted here
— reporting a tonnage band from a family label would be the same class of inference that produced
the Malta error.

What comes out
--------------
`01_data/00_derived/family_evolution_by_market.csv` — market x family x year x clock (CY, FY)

Usage:
    python 03_analytics/Isuzu/prism/scripts/build_family_evolution.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
DECODE = DER / "epc_decode_batch1_20260919.json"
OUT = DER / "family_evolution_by_market.csv"
META = DER / "family_evolution_by_market.meta.json"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# Family label -> the group we report. The EPC's raw labels are kept in the meta for traceability.
FAMILY_MAP = {
    "PASSENGER VEHICLE PICK UP": "light_vehicle",
    "PASSENGER VEHICLE SUV": "light_vehicle",
    "TRUCKS N": "n_series_truck",
    "TRUCKS Q": "n_series_truck",
    "TRUCKS F&G": "heavy_truck",
    "TRUCKS C&E": "heavy_truck",
    "BUSES LR": "bus",
    "BUSES LT, LV": "bus",
    "BUSES GR, MR": "bus",
    "INDUSTRIAL ENGINE 4-CYLINDER": "other",
    "INDUSTRIAL ENGINE 6-CYLINDER": "other",
    "COMPONENT COMPONENT": "other",
}
GROUP_LABEL = {
    "light_vehicle": "Light vehicle (D-Max pickup and SUV)",
    "n_series_truck": "N-series truck",
    "heavy_truck": "Heavy truck (F-series and C&E)",
    "bus": "Bus",
    "other": "Other and industrial",
}


def band_for(families: list[str]) -> tuple[str, int]:
    """Reported group, plus how many distinct groups the part fits.

    A part fitting more than one group cannot be attributed to one, and is flagged so nobody reads a
    shared part as evidence about a single family.
    """
    groups = {FAMILY_MAP[f] for f in families if f in FAMILY_MAP}
    groups.discard("other")
    if not groups:
        return "other", 0
    # A light-vehicle part that is also a truck part is reported as shared rather than guessing.
    return ("|".join(sorted(groups)), len(groups))


def main() -> int:
    if not DECODE.is_file():
        print(f"decode missing: {DECODE}")
        return 1

    dec = json.loads(DECODE.read_text(encoding="utf-8"))
    rows = []
    for r in dec:
        fams = r.get("families") or []
        group, n = band_for(fams)
        rows.append({
            "pn": norm(r.get("pn")),
            "families": "; ".join(fams),
            "group": group,
            "group_count": n,
            "editions": r.get("editions"),
            "found": r.get("found"),
        })
    dim = pd.DataFrame(rows).drop_duplicates("pn")
    print(f"decode part numbers      : {len(dim):,}")
    print(f"  single-group           : {(dim.group_count == 1).sum():,}")
    print(f"  shared across groups   : {(dim.group_count > 1).sum():,}")
    print(f"  unresolved / other     : {(dim.group_count == 0).sum():,}")

    sf = pd.read_parquet(DER / "sales_fact.parquet")
    sf["pn"] = sf["part_number"].map(norm)
    d = pd.read_csv(DER / "distributor_dimension.csv")
    sf["distributor_code"] = sf["sold_to_sap"].map(dict(zip(d.sold_to_sap, d.distributor_code)))
    sf = sf[sf.distributor_code.notna()].copy()
    sf["d"] = pd.to_datetime(sf.billing_date, errors="coerce")
    sf = sf.dropna(subset=["d"])
    sf["year"] = sf["d"].dt.year
    sf["month"] = sf["d"].dt.month
    # ISZE financial year: April to March, labelled by the year that closes it.
    sf["fy"] = sf["year"] + (sf["month"] >= 4).astype(int)

    m = sf.merge(dim[["pn", "group", "group_count"]], on="pn", how="inner")
    # Only a part that fits exactly ONE group can be attributed to that group. Parts fitting
    # several are pooled into 'shared' rather than apportioned, because apportioning them would be
    # an assumption and this whole exercise is about removing those.
    m["report_group"] = np.where(m["group_count"] == 1, m["group"], "shared_across_families")
    covered = m.net_sales_value.sum()
    total = sf.net_sales_value.sum()
    print()
    print(f"billed euro joined       : EUR {covered:,.0f} ({100 * covered / total:.1f}% of the book)")

    frames = []
    for clock, col in (("CY", "year"), ("FY", "fy")):
        g = (
            m.groupby(["distributor_code", col, "report_group"], dropna=False)
            .agg(billed_eur=("net_sales_value", "sum"),
                 units=("billed_qty", "sum"),
                 distinct_pns=("pn", "nunique"))
            .reset_index()
            .rename(columns={col: "period"})
        )
        g["clock"] = clock
        frames.append(g)
    out = pd.concat(frames, ignore_index=True)
    out["group_label"] = out["report_group"].map(GROUP_LABEL).fillna(out["report_group"])
    out["billed_eur"] = out["billed_eur"].round(2)
    out = out.sort_values(["clock", "distributor_code", "report_group", "period"])
    out.to_csv(OUT, index=False)

    META.write_text(json.dumps({
        "decode_source": str(DECODE),
        "rows": int(len(out)),
        "groups": sorted(out["report_group"].unique()),
        "covered_eur": round(float(covered), 2),
        "coverage_pct_of_book": round(100 * covered / total, 2),
        "clock_definition": {
            "CY": "calendar year January to December",
            "FY": "ISZE financial year April to March, labelled by the closing year "
                  "(FY2026 = Apr 2025 to Mar 2026)",
        },
        "limit": [
            "The EPC gives vehicle FAMILY, not tonnage. TRUCKS N spans NLR to NQR, so 3.5 t and "
            "7.5 t are NOT separated here. A tonnage band needs the model-code table.",
            "Only the part numbers in EPC batch 1 are covered — the top 250 by value. Everything "
            "else is absent rather than zero.",
            "A part fitting more than one family is pooled as 'shared_across_families' and is NOT "
            "apportioned, because apportioning would be an assumption.",
        ],
    }, indent=2), encoding="utf-8")

    print(f"  -> {len(out):,} rows -> {OUT.name}")

    def show(clock: str, value: str, title: str, fmt: str = ",.0f") -> None:
        print()
        print("=" * 96)
        print(title)
        print("=" * 96)
        g = out[out.clock == clock]
        piv = g.pivot_table(index="group_label", columns="period", values=value, aggfunc="sum")
        years = [c for c in piv.columns if c <= 2025]
        piv[2026] = piv.get(2026)
        if years:
            piv["23-25 chg"] = [
                (piv.loc[i, years[-1]] / piv.loc[i, years[0]] - 1) * 100
                if piv.loc[i, years[0]] else float("nan")
                for i in piv.index
            ]
        with pd.option_context("display.float_format", lambda v: format(v, fmt)):
            print(piv.to_string())
        print(f"  (2026 is a part year. '23-25 chg' compares complete calendar years only.)")

    show("CY", "billed_eur", "EURO BY FAMILY, CALENDAR YEAR")
    show("CY", "units", "UNITS BY FAMILY, CALENDAR YEAR")
    show("CY", "distinct_pns", "DISTINCT PART NUMBERS BILLED, CALENDAR YEAR", ".0f")

    print()
    print("=" * 96)
    print("ATTRIBUTABLE VERSUS SHARED, share of the joined euro")
    print("=" * 96)
    tot = out[(out.clock == "CY")].groupby("report_group").billed_eur.sum()
    for k, v in tot.sort_values(ascending=False).items():
        print(f"  {k:26s} EUR {v:14,.0f}   {100*v/tot.sum():5.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
