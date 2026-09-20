#!/usr/bin/env python3
"""
Build the EPC decode batch for the vehicle-family question — over the whole service-part universe.

What changed, and why
---------------------
The earlier version of this script dropped every part number the genuine/BVP cross-reference already
named a vehicle for:

    need = book[~book["vehicle_known"] & ~book["_pn"].isin(placeholder)]

``vehicle_known`` came from the cross-reference, so a part whose vehicle the cross-reference already
named was excluded from the EPC decode *because we knew its family* — and was then excluded from the
family view *because it was not in the decode*. Each step assumed the other had it. Every part number
the cross-reference names a vehicle for fell between the two, and appeared nowhere on the page at all.

The defect was sized at the time at 95 heavy-truck-only part numbers billing EUR 1,955,749 across
eleven service families. That count does not reproduce and both numbers are wrong. A bare ``F*``
substring test read ``TF*``, the D-Max pickup wildcard, as an F-series token, so pickup parts were
counted as heavy truck. On the corrected family table the heavy truck family holds 164 part numbers
billing EUR 174,832 in 2025 on a 1,238-vehicle fleet. The figure is not quoted here because nothing
in this script computes it; it belongs to
``01_data/00_derived/vehicle_family_bands.csv`` and the rule that builds it.

The bug was not the filter. The bug was that the worklist was built bottom-up from what the EPC had
already returned, rather than top-down from the question. The question is "is service business by
vehicle type growing or shrinking", and answering it needs every service part number to have a
family. So the universe is now the **whole service-part list**, and the EPC decode is only one of the
two ways a part number can reach a family.

What the worklist is now
------------------------
One row per service part number — every part number in ``bvp_pn_dimension.csv`` (plus the capture
supplement) that carries a ``pms_category``. Each row says:

  * ``family_known``  — true when the cross-reference already names exactly one family, so the part
    needs no EPC lookup. It is carried into the family table on the cross-reference's vehicle field.
  * ``needs_epc``     — true when nobody has named a vehicle for it yet. Those, and only those, are
    what the batch files contain.
  * ``batch``         — the sitting each one belongs to, ordered by euro so the highest value is
    decoded first.

So nothing is dropped, the count is auditable, and the euro on the worklist is the whole service
book rather than the part of it that happened to be decoded.

Reads : 01_data/00_derived/sales_fact.parquet
        01_data/00_derived/distributor_dimension.csv
        01_data/00_derived/aim_master_v2.csv
        01_data/00_derived/bvp_pn_dimension.csv
        03_analytics/Isuzu/prism/data/pms_capture_supplement.csv
        01_data/00_derived/genuine_bvp_crossref.csv
        01_data/00_derived/vehicle_family_bands.csv    (written by build_vehicle_family_bands.py)
Writes: 01_data/00_derived/epc_decode_worklist.csv
        01_data/00_derived/epc_decode_batch_<n>.txt   (one per batch, newline separated)
        01_data/00_derived/epc_decode_worklist.meta.json

Run: python 03_analytics/Isuzu/prism/scripts/build_epc_decode_batches.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM_DATA = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"

BATCH_SIZE = 250

OUT_WORKLIST = DER / "epc_decode_worklist.csv"
OUT_META = DER / "epc_decode_worklist.meta.json"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731


def main() -> int:
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    sf["_pn"] = sf["part_number"].map(norm)
    dim_d = pd.read_csv(DER / "distributor_dimension.csv")
    sf["db"] = sf["sold_to_sap"].map(dict(zip(dim_d.sold_to_sap, dim_d.distributor_code)))
    sf["year"] = pd.to_datetime(sf["billing_date"], errors="coerce").dt.year

    book = (
        sf.groupby("_pn")
        .agg(
            pn=("part_number", "first"),
            eur_all=("net_sales_value", "sum"),
            units_all=("billed_qty", "sum"),
            markets=("db", "nunique"),
            years_billed=("year", "nunique"),
        )
        .reset_index()
    )
    book["single_year"] = book["years_billed"] <= 1

    aim = pd.read_csv(
        DER / "aim_master_v2.csv", dtype=str,
        usecols=["part_number", "aim_l1", "aim_l2"], low_memory=False,
    )
    aim["_pn"] = aim["part_number"].map(norm)
    aim = aim.drop_duplicates("_pn")

    # ── the universe: every service part number, from the dimension plus the capture supplement
    dim = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str, low_memory=False)
    supp = pd.read_csv(PRISM_DATA / "pms_capture_supplement.csv", dtype=str, low_memory=False)
    u = pd.concat([dim, supp], ignore_index=True)
    u["_pn"] = u["part_number"].map(norm)
    u = u[u["pms_category"].notna() & (u["pms_category"].astype(str).str.strip() != "")]
    u = u.drop_duplicates("_pn")[["_pn", "pms_category"]]
    n_universe = len(u)

    # ── the two vehicle sources. The cross-reference is a source in its own right; a part it names
    # does not need an EPC lookup, but it is still carried into the family table.
    bands = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False)
    bands["_pn"] = bands.pn.map(norm)
    known = set(bands.loc[bands.resolution == "single_family", "_pn"])
    pooled = set(bands.loc[bands.resolution == "shared_across_families", "_pn"])
    no_ref = set(bands.loc[bands.resolution == "no_vehicle_reference", "_pn"])
    fam_of = dict(zip(bands._pn, bands.family))

    # The universe is the service-part list, exactly: every part number carrying a pms_category.
    # A part number outside that list is not part of the service question and is not in the worklist.
    work = u.copy()
    work = work.merge(book.drop(columns=["pn"]), on="_pn", how="left")
    work = work.merge(aim[["_pn", "aim_l1", "aim_l2"]], on="_pn", how="left")
    for c in ("eur_all", "units_all", "markets", "years_billed"):
        work[c] = work[c].fillna(0)
    work["single_year"] = work["years_billed"] <= 1

    # Real part numbers only. The placeholder preambles (REBATE, TRANSPORT and similar) are not part
    # numbers and the EPC cannot resolve them.
    raw = sf["part_number"].astype(str).str.strip()
    placeholder = set(sf.loc[raw.str.match(r"^[A-Z][A-Z0-9\- ]{2,}$", na=False), "_pn"])

    work["family_known"] = work._pn.isin(known)
    work["family"] = work._pn.map(fam_of)
    work["pooled"] = work._pn.isin(pooled)
    work["no_vehicle_reference"] = work._pn.isin(no_ref)
    work["vehicle_source"] = "cross-reference or decode"
    work.loc[work.family_known, "vehicle_source"] = "vehicle_family_bands.csv: cross-reference names one family"
    work.loc[work.pooled, "vehicle_source"] = "vehicle_family_bands.csv: fits more than one family, pooled"
    work.loc[work.no_vehicle_reference, "vehicle_source"] = "vehicle_family_bands.csv: no vehicle named by either source"

    # ── who still needs an EPC lookup: nobody has named a vehicle, and it is a real part number.
    work["needs_epc"] = ~work.family_known & ~work._pn.isin(placeholder)
    work["excluded_placeholder"] = work._pn.isin(placeholder)

    # Batches are ordered by euro so the highest-value part numbers are decoded first, but the
    # worklist still contains everything — the batch number is a sitting, not a cut-off.
    need = work[work.needs_epc].sort_values("eur_all", ascending=False).reset_index(drop=True)
    need["rank"] = need.index + 1
    need["batch"] = ((need["rank"] - 1) // BATCH_SIZE + 1).astype(int)
    work = work.merge(need[["_pn", "rank", "batch"]], on="_pn", how="left")

    out = work.rename(columns={"_pn": "pn_key"})[
        ["rank", "batch", "pn_key", "pms_category", "aim_l1", "aim_l2", "family", "family_known",
         "pooled", "no_vehicle_reference", "needs_epc", "excluded_placeholder", "vehicle_source",
         "eur_all", "units_all", "markets", "years_billed", "single_year"]
    ].rename(columns={"pn_key": "part_number"})
    out = out.sort_values(["needs_epc", "eur_all"], ascending=[False, False])
    out.to_csv(OUT_WORKLIST, index=False)

    n_batches = int(need["batch"].max()) if len(need) else 0
    # Remove any batch file left by an earlier run. The worklist is derived, and a stale batch file
    # beside a fresh one is how a decode gets re-run against a list that is no longer the list.
    stale = [p for p in DER.glob("epc_decode_batch_*.txt")
             if not 1 <= int(p.stem.rsplit("_", 1)[1]) <= n_batches or not p.stem.rsplit("_", 1)[1].isdigit()]
    for p in stale:
        p.unlink()
    for b in range(1, n_batches + 1):
        pns = need.loc[need["batch"] == b, "_pn"].tolist()
        (DER / f"epc_decode_batch_{b}.txt").write_text(
            "\n".join(str(x) for x in pns) + "\n", encoding="ascii")

    total_eur = float(work.eur_all.sum())
    need_eur = float(need.eur_all.sum()) if len(need) else 0.0
    known_eur = float(work.loc[work.family_known, "eur_all"].sum())
    placeholder_eur = float(work.loc[work.excluded_placeholder, "eur_all"].sum())

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "03_analytics/Isuzu/prism/scripts/build_epc_decode_batches.py",
        "batch_size": BATCH_SIZE,
        "universe": {
            "part_numbers": int(len(work)),
            "eur_all_markets_all_years": round(total_eur, 2),
            "rule": ("every part number in bvp_pn_dimension.csv or pms_capture_supplement.csv "
                     "that carries a pms_category — the whole service-part list, nothing cut off "
                     "by euro or by batch size"),
        },
        "already_carrying_a_family": {
            "part_numbers": int((work.family_known | work.pooled | work.no_vehicle_reference).sum()),
            "eur": round(float(work.loc[
                work.family_known | work.pooled | work.no_vehicle_reference, "eur_all"].sum()), 2),
            "source": "vehicle_family_bands.csv — the cross-reference or the existing decode",
        },
        "family_already_known_no_epc_needed": {
            "part_numbers": int(work.family_known.sum()),
            "eur": round(known_eur, 2),
            "source": "vehicle_family_bands.csv, resolution=single_family",
        },
        "still_needing_an_epc_lookup": {
            "part_numbers": int(len(need)),
            "eur": round(need_eur, 2),
            "batches": n_batches,
            "note": ("ordered by euro so the highest value is decoded first; nothing is cut off by "
                     "the batch size, the batch number is a sitting"),
        },
        "pooled_across_families": {
            "part_numbers": int(work.pooled.sum()),
            "eur": round(float(work.loc[work.pooled, "eur_all"].sum()), 2),
        },
        "no_vehicle_reference": {
            "part_numbers": int(work.no_vehicle_reference.sum()),
            "eur": round(float(work.loc[work.no_vehicle_reference, "eur_all"].sum()), 2),
        },
        "excluded_placeholder_preamble": {
            "part_numbers": int(work.excluded_placeholder.sum()),
            "eur": round(placeholder_eur, 2),
            "note": "REBATE, TRANSPORT and similar — not part numbers, the EPC cannot resolve them",
        },
        "defect_this_replaces": {
            "expression": 'need = book[~book["vehicle_known"] & ~book["_pn"].isin(placeholder)]',
            "effect": ("cross-reference-known part numbers were dropped from the decode because "
                       "their family was known, and then dropped from the family view because they "
                       "were not in the decode"),
            "effect_measured": ("the part numbers the cross-reference names a vehicle for were on "
                                "neither side; none of them appeared in the decode"),
            "earlier_claim_withdrawn": ("an earlier estimate of 95 heavy-truck-only part numbers at "
                                        "EUR 1,955,749 across eleven service families does not "
                                        "reproduce — see the module docstring — and is not quoted "
                                        "here; nothing in this script computes it. The corrected "
                                        "measurement lives in vehicle_family_bands.csv: the heavy "
                                        "truck family holds 164 part numbers billing EUR 174,832 "
                                        "in 2025 on a 1,238-vehicle fleet"),
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"  service part universe         : {len(work):,} part numbers  "
          f"EUR {total_eur:,.0f}")
    print(f"  already carrying a family     : "
          f"{int((work.family_known | work.pooled | work.no_vehicle_reference).sum()):,}  "
          f"EUR {float(work.loc[work.family_known | work.pooled | work.no_vehicle_reference, 'eur_all'].sum()):,.0f}")
    print(f"  family already known          : {int(work.family_known.sum()):,}  "
          f"EUR {known_eur:,.0f}   (no EPC lookup needed)")
    print(f"  still needing an EPC lookup   : {len(need):,}  EUR {need_eur:,.0f}")
    print(f"  pooled across families        : {int(work.pooled.sum()):,}  "
          f"EUR {float(work.loc[work.pooled, 'eur_all'].sum()):,.0f}")
    print(f"  no vehicle reference          : {int(work.no_vehicle_reference.sum()):,}  "
          f"EUR {float(work.loc[work.no_vehicle_reference, 'eur_all'].sum()):,.0f}")
    print(f"  placeholder preambles, not PNs: {int(work.excluded_placeholder.sum()):,}  "
          f"EUR {placeholder_eur:,.0f}")
    print(f"  batches of {BATCH_SIZE}              : {n_batches}")
    print()
    print(f"  {'batch':>5s}  {'PNs':>5s}  {'EUR in batch':>14s}  {'~time':>7s}  file")
    for b in range(1, n_batches + 1):
        g = need[need["batch"] == b]
        hrs = len(g) * 12 / 3600
        print(f"  {b:5d}  {len(g):5d}  {g['eur_all'].sum():14,.0f}  {hrs:6.1f}h  "
              f"epc_decode_batch_{b}.txt")
    print()
    print(f"written -> {OUT_WORKLIST}  ({len(out):,} rows)")
    print(f"written -> {OUT_META}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
