"""Narrow the EQ lookup worklist down to the parts only the parts catalogue can settle.

The classification in `export_aim_open_why_20260924/open_parts_classified.csv` gives every
open part number exactly one reason. Five of those reasons are "there is no usable wording
evidence on the master", and the report's own count for them is 199. This script keeps
exactly those five groups and nothing else -- it does not re-derive the classification.

Reads  : 01_data/91_build/export_aim_open_why_20260924/open_parts_classified.csv   (read-only)
         01_data/91_build/export_aim_eq_20260924/open_worklist_20260924.csv       (read-only, fig_key)
Writes : 01_data/91_build/export_aim_eq_20260924/open_worklist_epc_only_20260924.json
         01_data/91_build/export_aim_eq_20260924/open_worklist_epc_only_20260924.csv

The JSON is a plain list of part numbers in price order, which is what make_paste_script.py reads.

Run:  python 01_data/91_build/export_aim_eq_20260924/build_epc_only_worklist.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
CLASSIFIED = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924" / "open_parts_classified.csv"
SOURCE_WORKLIST = OUT / "open_worklist_20260924.csv"
TARGET_JSON = OUT / "open_worklist_epc_only_20260924.json"
TARGET_CSV = OUT / "open_worklist_epc_only_20260924.csv"

# The five groups open_why.py itself counts as "only the catalogue can settle this".
EPC_GROUPS = [
    "DATA_WORDING_UNKNOWN_TO_MASTER",
    "DATA_WORDING_SPLIT_ACROSS_FAMILIES",
    "DATA_FAMILY_ONE_LEAF_SPLIT",
    "DATA_NOT_IN_MASTER",
    "OTHER_MASTER_HOLDS_NO_FAMILY",
]


def main() -> None:
    c = pd.read_csv(CLASSIFIED, dtype=str, encoding="utf-8-sig")
    keep = c[c["group"].isin(EPC_GROUPS)].copy()
    keep["list_eur"] = pd.to_numeric(keep["list_eur"], errors="coerce").fillna(0.0)

    # fig_key / on_master / current marker come from the worklist already on disk; nothing re-derived.
    src = pd.read_csv(SOURCE_WORKLIST, dtype=str, encoding="utf-8-sig")
    src = src.rename(
        columns={"k": "pnk", "fig_key": "fig_key_wl", "on_master": "on_master_wl", "cur_aim_l1": "cur_aim_l1_wl"}
    )[["pnk", "rank", "fig_key_wl", "on_master_wl", "cur_aim_l1_wl"]].rename(columns={"rank": "rank_wl"})
    keep = keep.merge(src, on="pnk", how="left")
    keep["fig_key"] = keep["fig_key_wl"].fillna("")
    keep["on_master"] = keep["on_master_wl"].fillna("")
    keep["cur_aim_l1"] = keep["cur_aim_l1_wl"].fillna("")

    # keep the order the 1,097-part run already used (its rank), so the two scripts line up;
    # fall back to list price for anything the source worklist does not rank
    keep["rank_wl"] = pd.to_numeric(keep["rank_wl"], errors="coerce")
    keep = keep.sort_values(
        ["rank_wl", "list_eur", "pnk"], ascending=[True, False, True], na_position="last"
    ).reset_index(drop=True)
    keep["rank"] = range(1, len(keep) + 1)

    out = keep[[
        "rank", "pnk", "description", "list_eur", "fig_key", "on_master", "cur_aim_l1", "group",
    ]].rename(columns={"pnk": "k", "description": "Description", "list_eur": "eur"})
    out["list_eur"] = out["eur"]

    out.to_csv(TARGET_CSV, index=False, encoding="utf-8-sig")
    TARGET_JSON.write_text(json.dumps(out["k"].tolist(), ensure_ascii=False), encoding="utf-8")

    print(f"classified rows read          : {len(c):,}")
    print(f"part numbers kept (EPC only)  : {len(out):,}  (report says 199)")
    print("kept per group:")
    print(keep["group"].value_counts().to_string())
    print(f"list price of the kept set    : EUR {keep['list_eur'].sum():,.2f}")
    print(f"wrote {TARGET_JSON.name} ({TARGET_JSON.stat().st_size:,} bytes)")
    print(f"wrote {TARGET_CSV.name} ({TARGET_CSV.stat().st_size:,} bytes)")

    left_out = c[~c["group"].isin(EPC_GROUPS)]
    print(f"left out of this run          : {len(left_out):,} (the Unknown-marker decision and the rule groups)")


if __name__ == "__main__":
    main()
