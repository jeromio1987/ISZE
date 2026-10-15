#!/usr/bin/env python3
"""Proposal only: pad kits that sit outside AIM L3 "Brake Pad Kit" in release 2026-10-11.

Found 2026-10-15 while building the price revision tool by AIM level. Jerome decided on
30 Sep 2026 that brake pad kits stay at today's price; the tool holds them through L3
"Brake Pad Kit", so a pad kit with another label escapes that hold.

Scope: every part whose description starts with "PAD KIT" and whose aim_l3_fixed is not
"Brake Pad Kit". Where the release row has no description, the PR00 price list description is
used. Target is the existing leaf Brakes > Pads & Shoes > Brake Pad Kit (no new labels).
Three groups:
  disc_brk_kit_as_disc    five disc-brake kits the AIM workbook filed under Discs & Drums > Brake Disc
  rear_caliper_blank      rear kits with no AIM label (never billed), same description and figure
                          as five rear kits already on Brake Pad Kit
  no_release_description  unlabelled kits (never billed) named PAD KIT only on the price list

Writes the proposal CSV + summary JSON in _releases. Does NOT cut a release, does not touch
the release file, aim_master_v2.csv, the live overlay or RELEASES.json. On Jerome's go the
apply follows _aim_hotfix_residues_release_20261011.py (cut from 2026-10-11, sync master +
overlay, register, re-export the Power BI file).

    python build_next_release_proposal_pad_kits_20261015.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BASE_ID = "2026-10-11"
BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
SALES = DER / "sales_fact.parquet"
ENQ = DER / "pricing_pn_enquiry.parquet"
OUT = REL / "next_release_proposal_pad_kits_2026-10-15.csv"
OUT_SUM = OUT.with_suffix(".summary.json")

# the price revision tool's own billed base (in-scope lines priced on both sides, Jul 2025 - Jun 2026)
sys.path.insert(0, str(ISZE / "02_dashboards" / "pricing" / "_build" / "price_5pct_proposal_2026-09-29"))
from evidence_lib import load_base  # noqa: E402

AIM_COLS = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]
TARGET = ("Brakes", "Pads & Shoes", "Brake Pad Kit")
FY26 = ("2025-04-01", "2026-03-31")
STATUS = "PROPOSED - not applied to any release; Jerome approves"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    reg = json.loads((REL / "RELEASES.json").read_text(encoding="utf-8"))
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED", base_entry["status"]
    base_sha = sha256(BASE)
    assert base_sha == base_entry["sha256"], "base release hash differs from RELEASES.json"

    rel = pd.read_csv(BASE, dtype=str, keep_default_na=False)
    for c in rel.columns:
        rel[c] = rel[c].str.strip()
    assert rel.part_number.is_unique
    desc = rel.description_norm.str.upper()
    leaves = set(zip(*(rel[c] for c in AIM_COLS)))
    assert TARGET in leaves, "target leaf missing from the base release"

    # some release rows carry no description; the PR00 price list (pricing_pn_enquiry) still names them
    enq = pd.read_parquet(ENQ, columns=["part_number", "description", "newest_pn", "sp_eur_pr00_ie40"])
    enq["pn"] = enq.part_number.astype(str).str.strip().str.zfill(10)
    enq = enq.drop_duplicates("pn").set_index("pn")
    lp = pd.to_numeric(enq.sp_eur_pr00_ie40, errors="coerce")
    list_desc = rel.part_number.map(enq.description).fillna("").astype(str).str.strip()
    rel_has = desc.str.startswith("PAD KIT")
    list_has = desc.eq("") & list_desc.str.upper().str.startswith("PAD KIT")

    pick = (rel_has | list_has) & rel.aim_l3_fixed.ne(TARGET[2])
    sel = rel[pick].copy()
    sel["desc_shown"] = sel.description_norm.where(rel_has[pick], list_desc[pick])
    sel["description_source"] = rel_has[pick].map({True: "release", False: "PR00 price list"})
    blank = sel[AIM_COLS].eq("").all(axis=1)
    sel["change_group"] = "disc_brk_kit_as_disc"
    sel.loc[blank & rel_has[pick], "change_group"] = "rear_caliper_blank"
    sel.loc[blank & ~rel_has[pick], "change_group"] = "no_release_description"
    unexpected = sel[~blank & sel.aim_l3_fixed.ne("Brake Disc")]
    assert unexpected.empty, f"pad kits on an unexpected label: {unexpected.part_number.tolist()}"
    assert not sel.loc[sel.change_group.eq("rear_caliper_blank"), "desc_shown"].ne("PAD KIT; CALIPER,RR").any()

    # euros: price tool basis, FY2026 and all history in sales_fact
    pns = set(sel.part_number)
    L = load_base()
    L = L[L.movable & L.pn.isin(pns)]
    tool = L.groupby("pn").net_sales_value.sum()
    sf = pd.read_parquet(SALES, columns=["billing_date", "part_number", "net_sales_value"])
    sf["pn"] = sf.part_number.astype(str).str.strip().str.zfill(10)
    sf = sf[sf.pn.isin(pns)]
    sf["billing_date"] = pd.to_datetime(sf.billing_date)
    fy = sf[(sf.billing_date >= FY26[0]) & (sf.billing_date <= FY26[1])].groupby("pn").net_sales_value.sum()
    allh = sf.groupby("pn").net_sales_value.sum()
    last = sf.groupby("pn").billing_date.max()

    reason = {
        "disc_brk_kit_as_disc": ("Pad kit, not a disc. The AIM workbook filed it under Discs & Drums > Brake Disc and "
                                 "every release since 20 Sep 2026 carried that. 8978279580 and 8978279600, the same "
                                 "kit description in the same figure 302-133, are already Brake Pad Kit."),
        "rear_caliper_blank": ("Pad kit with no AIM label; not billed since Jan 2023. Five parts with the same "
                               "description PAD KIT; CALIPER,RR in figure 306-009 are already Brake Pad Kit."),
        "no_release_description": ("Pad kit by the PR00 price list description; the release has no description and "
                                   "no AIM label; not billed since Jan 2023. Its figure's pad kits are already "
                                   "Brake Pad Kit."),
    }
    p = sel.set_index("part_number")
    out = pd.DataFrame({
        "part_number": p.index,
        "description": p.desc_shown.values,
        "description_source": p.description_source.values,
        "fig_key": p.fig_key.values,
        "change_group": p.change_group.values,
        "current_aim_l1": p.aim_l1_fixed.values,
        "current_aim_l2": p.aim_l2_fixed.values,
        "current_aim_l3": p.aim_l3_fixed.values,
        "proposed_aim_l1": TARGET[0],
        "proposed_aim_l2": TARGET[1],
        "proposed_aim_l3": TARGET[2],
        "current_aim_source": p.aim_source.values,
        "eur_billed_jul25_jun26_price_tool": tool.reindex(p.index).fillna(0.0).round(2).values,
        "eur_billed_fy2026": fy.reindex(p.index).fillna(0.0).round(2).values,
        "eur_billed_jan23_aug26": allh.reindex(p.index).fillna(0.0).round(2).values,
        "last_billed": last.reindex(p.index).dt.strftime("%Y-%m-%d").fillna("").values,
        "pr00_list_eur_ie40": lp.reindex(p.index).round(2).values,
        "replaced_by_pn": [n if isinstance(n, str) and n.strip() not in ("", pn) else ""
                           for pn, n in zip(p.index, enq.newest_pn.reindex(p.index))],
        "reason": [reason[g] for g in p.change_group],
        "apply": "NO",
        "status": STATUS,
    })
    out = out.sort_values(["change_group", "eur_billed_jul25_jun26_price_tool", "part_number"],
                          ascending=[True, False, True])
    out.to_csv(OUT, index=False, encoding="utf-8")

    # dry run in memory: apply to a copy and prove nothing else moves
    dry = rel.copy()
    m = dry.part_number.isin(pns)
    for c, v in zip(AIM_COLS, TARGET):
        dry.loc[m, c] = v
    diff = (dry[AIM_COLS] != rel[AIM_COLS])
    changed_rows = int(diff.any(axis=1).sum())
    changed_cells = int(diff.values.sum())
    assert changed_rows == len(pns) and not diff[~m].any().any()
    left = dry[(rel_has | list_has) & dry.aim_l3_fixed.ne(TARGET[2])]
    assert left.empty

    g = out.groupby("change_group").agg(parts=("part_number", "size"),
                                        eur_tool=("eur_billed_jul25_jun26_price_tool", "sum"),
                                        eur_fy2026=("eur_billed_fy2026", "sum"),
                                        with_pr00_list=("pr00_list_eur_ie40", "count"))
    summary = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_next_release_proposal_pad_kits_20261015.py",
        "status": STATUS,
        "base_release": BASE_ID,
        "base_sha256": base_sha,
        "rule": ("description starts with 'PAD KIT' (release description, or the PR00 price list description where "
                 "the release has none) and aim_l3_fixed != 'Brake Pad Kit'"),
        "target_leaf": list(TARGET),
        "parts": int(len(out)),
        "by_group": {k: {kk: (round(float(vv), 2) if "eur" in kk else int(vv)) for kk, vv in r.items()}
                     for k, r in g.to_dict("index").items()},
        "eur_basis": {
            "price_tool": "price_bp_weighted_compare_pn.csv in-scope lines priced on both sides (load_base), "
                          "the base of ISZE_Price_Revision_by_AIM_Level_2026-10-15.xlsx, Jul 2025 - Jun 2026",
            "fy2026": f"sales_fact.parquet net_sales_value {FY26[0]}..{FY26[1]}",
            "release_column_note": "the release's own l12m_billed_eur is Jan 2025 - Jun 2026 (18 months); not used here",
        },
        "dry_run": {
            "rows_changed": changed_rows,
            "cells_changed": changed_cells,
            "other_rows_changed": 0,
            "pad_kits_outside_brake_pad_kit_after": int(len(left)),
            "brake_pad_kit_parts_before": int(rel.aim_l3_fixed.eq(TARGET[2]).sum()),
            "brake_pad_kit_parts_after": int(dry.aim_l3_fixed.eq(TARGET[2]).sum()),
        },
        "not_touched": ["release files", "aim_master_v2.csv", "aim_pn_classification_20260920.csv", "RELEASES.json"],
    }
    OUT_SUM.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
