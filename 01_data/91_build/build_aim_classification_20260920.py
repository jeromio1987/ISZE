#!/usr/bin/env python3
"""Build the separated classification file from the live master + the declared sources.

WHY THIS EXISTS
---------------
The live master (aim_master_v2.csv) is the spine: AIM family, Japan codes, figures,
euro. But it cannot serve as the classification file because:

  1. it is missing 14 of the 15 columns the classification file's consumer contract
     needs (description_norm, filter_part_role, workbook_l1/l2/l3, catalog_*,
     catalog_node_present, catalog_residual, workbook_axis_kind, workbook_source,
     axis_conflict);
  2. its cat_l1/l2/l3 columns are a STALE ONE-TIME COPY of pr00_classification.csv,
     taken by build_aim_master.py on 17 Sep 22:06. pr00 was corrected twice after
     that and was never re-copied, which is why the master is at 98.34% agreement
     with its own declared upstream while the older file is at 99.36%.

So this builder does the JOIN the file always needed:
    spine        <- aim_master_v2.csv     (AIM family, Europe codes, figs, euro)
    catalogue    <- pr00_classification.csv  (the DECLARED source, re-read live)
    contract cols<- aim_pn_classification.csv (description text, filter role, legacy axis)

NON-DESTRUCTIVE. Writes a new dated file. Nothing in 00_derived is overwritten and
no gate report is touched.

Outputs
-------
  01_data/00_derived/aim_pn_classification_20260920.csv
  01_data/00_derived/aim_pn_classification_20260920.meta.json
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

DERIVED = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
SPINE = os.path.join(DERIVED, "aim_master_v2.csv")
PR00 = os.path.join(DERIVED, "pr00_classification.csv")
V1 = os.path.join(DERIVED, "aim_pn_classification.csv")
OUT_CSV = os.path.join(DERIVED, "aim_pn_classification_20260920.csv")
OUT_META = os.path.join(DERIVED, "aim_pn_classification_20260920.meta.json")

# Axis A identity vocabulary, unchanged (the gate enforces this set).
AXIS_A_L1 = {
    "Competitive parts", "Repair parts", "Accident parts", "High value repair",
    "Comfort parts", "Hardware & consumables", "Other / review",
}
PLACEHOLDER_L1 = {"Unknown", "Unknown Review"}
RESIDUAL_L1 = "Other / review"

# ---------------------------------------------------------------------------
# Non-part lines that sit inside the sales extract as placeholder part numbers.
# COPIED from 03_analytics/Isuzu/prism/modules/sales_loader.py (NON_PART_LINE_KIND),
# so this file uses the house rule rather than inventing a second one. That file is
# PRISM-owned production code and was NOT edited. Keys are normalised before matching
# (uppercase, spaces removed, leading zeros stripped) because the master carries
# "REBATE" and "0000REBATE" and "LATEPAYMENTINTEREST" for the same entities.
# One entry is an ADDITION not present upstream - flagged in the meta.
# ---------------------------------------------------------------------------
NON_PART_RULE = {
    "TRANSPORT": "freight",
    "REBATE": "rebate",
    "LATEPAYMENTINTEREST": "finance",
    "DISRACK01": "adjustment",
    "5874123810": "tool",
    "5874123811": "tool",
    "5874123812": "tool",
    "SERVICE": "service_fee",
    "SERVICEFEEOUTSIDEEUROPE": "service_fee",
    "SERVICEFEEWITHINEEUROPE": "service_fee",   # ADDITION, not in sales_loader.py
    "COSTDEMURRAGE": "demurrage",
    "COMPENSATIONSSALEE-CREDIT": "e_credit",
}


def norm_key(k: str) -> str:
    k = (k or "").strip().upper().replace(" ", "")
    return k.lstrip("0") or k


NON_PART_NORM = {norm_key(k): v for k, v in NON_PART_RULE.items()}


def pad(pn: str) -> str:
    pn = (pn or "").strip()
    return pn.zfill(10) if pn.isdigit() else pn


def s(v) -> str:
    return (v or "").strip()


def workbook_axis_kind(v: str) -> str:
    v = s(v)
    if v == "":
        return "blank"
    if v in PLACEHOLDER_L1:
        return "placeholder"
    if v in AXIS_A_L1:
        return "axis_a_vocabulary_echo"
    return "system"


def read_csv(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    for p in (SPINE, PR00, V1):
        if not os.path.isfile(p):
            print("FATAL: missing %s" % p)
            return 2

    spine = {pad(r.get("part_number")): r for r in read_csv(SPINE)}
    pr00 = {pad(r.get("pn_norm")): r for r in read_csv(PR00)}
    v1 = {pad(r.get("part_number")): r for r in read_csv(V1)}
    print("spine rows %s | pr00 rows %s | v1 rows %s" % (
        f"{len(spine):,}", f"{len(pr00):,}", f"{len(v1):,}"))

    # ambiguous descriptions: one description claiming two different Axis A L1s.
    # Both the description and the category come from v1's own aim_l1 (NOT workbook_l1,
    # which does not exist in that file - keying on it silently flagged nothing).
    desc_l1 = {}
    for r in v1.values():
        d = s(r.get("description_norm"))
        if d:
            desc_l1.setdefault(d, set()).add(s(r.get("aim_l1")))
    ambiguous = {d for d, st in desc_l1.items() if len(st) > 1}

    rows = []
    counts = Counter()
    catalog_changed = []          # catalogue differs from the stale master copy
    for pn, sp in spine.items():
        v1r = v1.get(pn, {})
        q = pr00.get(pn)

        # --- Axis A: catalogue identity, re-read from the DECLARED source ---
        if q is not None:
            cat1, cat2, cat3 = s(q.get("family")), s(q.get("group")), s(q.get("level3_type"))
            counts["catalog_from_pr00"] += 1
        else:
            # no upstream row: keep "Other / review" so the residual is named, never invented
            cat1, cat2, cat3 = RESIDUAL_L1, "Miscellaneous", "Review needed"
            counts["catalog_no_upstream"] += 1

        # did this row's catalogue move against the stale copy the master already held?
        m1, m2, m3 = s(sp.get("cat_l1")), s(sp.get("cat_l2")), s(sp.get("cat_l3"))
        changed = (m1, m2, m3) != (cat1, cat2, cat3)
        if changed:
            counts["catalog_moved"] += 1
            catalog_changed.append((pn, float(s(sp.get("l12m_billed_eur")) or 0),
                                    "%s / %s" % (m2, m3), "%s / %s" % (cat2, cat3)))

        has_node = cat1 not in ("", RESIDUAL_L1)
        is_residual = cat1 == RESIDUAL_L1

        # --- legacy AIM workbook axis (context only, neither Axis A nor Axis B) ---
        wk1 = s(v1r.get("workbook_l1")) or s(sp.get("aim_l1"))
        wk2 = s(v1r.get("workbook_l2")) or s(sp.get("aim_l2"))
        wk3 = s(v1r.get("workbook_l3")) or s(sp.get("aim_l3"))
        kind = workbook_axis_kind(wk1)

        d = s(v1r.get("description_norm")) or s(sp.get("description"))
        if d:
            counts["desc_present"] += 1

        # non-part financial / freight lines: tag them, never drop them
        line_kind = NON_PART_NORM.get(norm_key(pn), "part")
        if line_kind != "part":
            counts["non_part_rows"] += 1
            counts["non_part_eur"] = counts.get("non_part_eur", 0.0) + (
                float(s(sp.get("l12m_billed_eur")) or 0))

        rows.append({
            "part_number": pn,
            "description_norm": d,
            # --- Axis A: identity tree ---
            "catalog_l1": cat1,
            "catalog_l2": cat2,
            "catalog_l3": cat3,
            "catalog_node_present": "1" if has_node else "0",
            "catalog_residual": "1" if is_residual else "0",
            # --- legacy AIM workbook vocabulary (context; not Axis B) ---
            "workbook_l1": wk1,
            "workbook_l2": wk2,
            "workbook_l3": wk3,
            "workbook_axis_kind": kind,
            "workbook_source": s(v1r.get("aim_source")) or s(sp.get("aim_source")),
            # --- the governed AIM family (added: what a pack actually charts) ---
            "aim_l1_fixed": s(sp.get("aim_l1_fixed")),
            "aim_l2_fixed": s(sp.get("aim_l2_fixed")),
            "aim_l3_fixed": s(sp.get("aim_l3")),
            # --- Japan codes (added: present on the spine, absent from the old file) ---
            "jp_zkk": s(sp.get("jp_zkk")),
            "jp_zuk": s(sp.get("jp_zuk")),
            "jp_hkk": s(sp.get("jp_hkk")),
            "jp_class_new": s(sp.get("jp_class_new")),
            # --- money ---
            "l12m_billed_eur": s(sp.get("l12m_billed_eur")),
            # --- flags ---
            "axis_conflict": "1" if kind == "system" else "0",
            "desc_ambiguous": "1" if d in ambiguous else "0",
            "catalog_changed_vs_master": "1" if changed else "0",
            "line_kind": line_kind,
            # --- passthrough ---
            "fig_key": s(v1r.get("fig_key")) or s(sp.get("fig_key")),
            "filter_part_role": s(v1r.get("filter_part_role")),
        })

    fields = list(rows[0].keys())
    with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    l2 = {s(r["catalog_l2"]) for r in rows if s(r["catalog_l2"])}
    l3 = {s(r["catalog_l3"]) for r in rows if s(r["catalog_l3"])}
    dups = len(rows) - len({r["part_number"] for r in rows})
    orphans = sum(1 for r in rows
                  if not s(r["catalog_l1"]) and (s(r["catalog_l2"]) or s(r["catalog_l3"])))
    residual = sum(1 for r in rows if r["catalog_residual"] == "1")
    l1vals = {s(r["catalog_l1"]) for r in rows} - {""}
    unexpected_l1 = l1vals - AXIS_A_L1
    amb_rows = sum(1 for r in rows if r["desc_ambiguous"] == "1")
    lead0 = sum(1 for r in rows if r["part_number"].startswith("0"))
    conflict = sum(1 for r in rows if r["axis_conflict"] == "1")

    moved_eur = sum(x[1] for x in catalog_changed)

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "built_by": "01_data/91_build/build_aim_classification_20260920.py",
        "purpose": (
            "Two-axes lock 2026-09-17: Axis A = catalog_l1/l2/l3 identity (catalogue, from the "
            "declared upstream pr00_classification.csv); Axis B = commercial score beside Axis A "
            "(contested per part per market) - not built as scored columns here yet. "
            "legacy workbook_l* is context only. Do not invent a fourth layer."
        ),
        "supersedes_for_rebuild": "aim_pn_classification_v2.csv (18 Sep) - read-only, not replaced",
        "sources": {
            "spine": SPINE,
            "spine_modified": datetime.fromtimestamp(os.path.getmtime(SPINE), timezone.utc).isoformat(),
            "catalog": PR00,
            "catalog_modified": datetime.fromtimestamp(os.path.getmtime(PR00), timezone.utc).isoformat(),
            "contract_columns": V1,
            "contract_modified": datetime.fromtimestamp(os.path.getmtime(V1), timezone.utc).isoformat(),
        },
        "catalog_source_note": (
            "catalog_l1/l2/l3 are read LIVE from pr00_classification.csv, the source the master's "
            "own cat_* columns are copied from. The master's copy is stale (taken 17 Sep 22:06) and "
            "disagrees with that upstream on 2,843 rows. Building from the stale copy would import "
            "the drift; building from the declared source does not. Rows where the two disagree are "
            "flagged catalog_changed_vs_master=1, so the movement is auditable, not silent."
        ),
        "non_part_rule": {
            "source": "03_analytics/Isuzu/prism/modules/sales_loader.py NON_PART_LINE_KIND (copied, that file NOT edited)",
            "keys": NON_PART_RULE,
            "additions_not_in_source": ["SERVICEFEEWITHINEEUROPE"],
            "matching": "normalised: uppercase, spaces removed, leading zeros stripped (the master carries REBATE and 0000REBATE, and LATEPAYMENTINTEREST and 'LATE PAYMENT INTEREST', for the same entities)",
            "effect": "tags line_kind; rows are kept, never dropped. Consumers that want parts revenue filter line_kind=='part'.",
        },
        "rows": len(rows),
        "counts": {
            "duplicate_keys": dups,
            "hierarchy_orphans": orphans,
            "catalog_from_pr00": counts["catalog_from_pr00"],
            "catalog_no_upstream_row": counts["catalog_no_upstream"],
            "catalog_moved_vs_master": counts["catalog_moved"],
            "catalog_moved_l12m_eur": round(moved_eur, 2),
            "catalog_residual_other_review": residual,
            "axis_conflict_rows": conflict,
            "description_ambiguous_rows": amb_rows,
            "distinct_ambiguous_descriptions": len(ambiguous),
            "leading_zero_keys": lead0,
            "description_present": counts["desc_present"],
            "catalog_l2_count": len(l2),
            "catalog_l3_count": len(l3),
            "non_part_rows": counts["non_part_rows"],
            "non_part_l12m_eur": round(counts.get("non_part_eur", 0.0), 2),
        },
        "gate_expectations": {
            "axis_a_l2_approved": 27,
            "axis_a_l3_approved": 176,
            "note": "verify_aim_classification.py approves L2=27 / L3=176 (leaf_add_battery_tools_20260918)",
        },
        "consumer_contract": [
            "Axis A (identity): group by catalog_l1/l2/l3. Wear and family views hang from catalog_l2/l3 or fig_key - never from a commercial posture parent.",
            "Axis B (commercial score): contested/captive per part per market sits beside Axis A. Never the hang-from parent for identity views.",
            "filter catalog_node_present=1 for a real Axis A family view.",
            "Report catalog_residual=1 (Other / review) as a named residual, never as a family.",
            "workbook_l1 is legacy AIM system context - neither Axis A nor Axis B. Never group workbook_l1 with catalog_l2.",
            "aim_l1_fixed = the governed functional family (what a family question charts).",
            "jp_zkk / jp_zuk are CATALOGUE ATTRIBUTES from the Japan price file. Never chart on them; they are not a family (one code holds 42% of the book across 415 part types).",
            "line_kind != 'part' marks freight / rebate / service-fee / demurrage rows. Filter line_kind=='part' for parts revenue; never let these into a family chart.",
        ],
    }
    with io.open(OUT_META, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, indent=2))

    print()
    print("rows                    %s" % f"{len(rows):,}")
    print("duplicate keys          %s" % dups)
    print("hierarchy orphans       %s" % orphans)
    print("catalog from pr00       %s" % f"{counts['catalog_from_pr00']:,}")
    print("catalog no upstream     %s" % f"{counts['catalog_no_upstream']:,}")
    print("catalog moved vs master %s rows  EUR %s" % (
        f"{counts['catalog_moved']:,}", f"{moved_eur:,.2f}"))
    print("catalog L2 / L3         %d / %d   (gate wants 27 / 176)" % (len(l2), len(l3)))
    print("residual Other/review   %s  (%.2f%%)" % (f"{residual:,}", 100*residual/len(rows)))
    print("unexpected L1 values    %s" % (sorted(unexpected_l1) or "none"))
    print("axis conflict rows      %s  (%.2f%%)" % (f"{conflict:,}", 100*conflict/len(rows)))
    print("desc ambiguous rows     %s" % f"{amb_rows:,}")
    print("leading-zero keys       %s" % f"{lead0:,}")
    print("non-part rows           %s  EUR %s" % (
        counts["non_part_rows"], f"{counts.get('non_part_eur', 0.0):,.2f}"))
    print()
    print("-> %s" % OUT_CSV)
    print("-> %s" % OUT_META)

    if catalog_changed:
        print()
        print("top catalogue moves vs the stale master copy:")
        mv = Counter()
        for pn, e, a, b in catalog_changed:
            mv[(a, b)] += 1
        for (a, b), n in mv.most_common(15):
            e = sum(x[1] for x in catalog_changed if x[2] == a and x[3] == b)
            print("  %5d rows  EUR %14s   %-40s -> %s" % (n, f"{e:,.0f}", a[:40], b[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
