#!/usr/bin/env python3
"""
Build aim_pn_classification_v2.csv — two axes, separate columns.

Locked 2026-09-17 (Jerome — proceed with two axes):

  Axis A — identity only: what it is / where on the truck (figure-based).
           Existing three levels only: catalog_l1 / catalog_l2 / catalog_l3.
  Axis B — commercial score beside that: contested or not, per part per market.
           NOT the box identity views hang from. Do not invent a fourth layer.

This script does NOT invent Axis B scores yet. It separates the catalogue identity
tree from the legacy AIM workbook vocabulary so consumers cannot accidentally fuse
them, and it states the consumer contract so wear views (king-pin case) never hang
from a commercial posture parent.

Non-destructive by design: v1 is never modified. Consumers migrate deliberately.
Catalogue columns are copied through and verified against pr00_classification.csv.

Outputs
-------
  01_data/00_derived/aim_pn_classification_v2.csv
  01_data/00_derived/aim_pn_classification_v2.meta.json
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
V1_CSV = DERIVED / "aim_pn_classification.csv"
PR00_CSV = DERIVED / "pr00_classification.csv"
OUT_CSV = DERIVED / "aim_pn_classification_v2.csv"
OUT_META = DERIVED / "aim_pn_classification_v2.meta.json"

# Axis A Level-1 vocabulary currently carried on catalog_l1 (identity tree).
# These names historically sound commercial; under the two-axes lock they remain
# L1 of Axis A until a scored Axis B exists. Wear views hang from L2/L3 / fig_key.
AXIS_A_L1 = {
    "Competitive parts",
    "Repair parts",
    "Accident parts",
    "High value repair",
    "Comfort parts",
    "Hardware & consumables",
    "Other / review",
}
PLACEHOLDER_L1 = {"Unknown", "Unknown Review"}


def workbook_axis_kind(v: str) -> str:
    """Label the legacy AIM workbook L1 — context only, neither Axis A nor Axis B."""
    v = (v or "").strip()
    if v == "":
        return "blank"
    if v in PLACEHOLDER_L1:
        return "placeholder"
    if v in AXIS_A_L1:
        return "axis_a_vocabulary_echo"
    return "system"


def main() -> int:
    if not V1_CSV.is_file():
        print(f"FATAL: missing {V1_CSV}")
        return 2

    with V1_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("FATAL: v1 file is empty")
        return 2

    # --- description ambiguity: one description claiming two different Level 1s ---
    desc_l1 = defaultdict(set)
    for r in rows:
        d = (r.get("description_norm") or "").strip()
        if d:
            desc_l1[d].add((r.get("aim_l1") or "").strip())
    ambiguous = {d for d, s in desc_l1.items() if len(s) > 1}

    # --- catalogue verification against pr00, if available ---
    def _pad_key(pn: str) -> str:
        pn = (pn or "").strip()
        return pn.zfill(10) if pn.isdigit() else pn

    pr00_ok = pr00_checked = 0
    pr00_map: dict[str, tuple[str, str, str]] = {}
    if PR00_CSV.is_file():
        with PR00_CSV.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                pn = _pad_key(r.get("pn_norm") or "")
                if pn:
                    pr00_map[pn] = (
                        (r.get("family") or "").strip(),
                        (r.get("group") or "").strip(),
                        (r.get("level3_type") or "").strip(),
                    )

    out_rows = []
    kinds = Counter()
    residual = 0
    node_present = 0
    conflicts = 0
    ambiguity_hits = 0

    for r in rows:
        cat1 = (r.get("catalog_l1") or "").strip()
        cat2 = (r.get("catalog_l2") or "").strip()
        cat3 = (r.get("catalog_l3") or "").strip()
        wk1 = (r.get("aim_l1") or "").strip()
        kind = workbook_axis_kind(wk1)
        kinds[kind] += 1

        has_node = cat1 not in ("", "Other / review")
        is_residual = cat1 == "Other / review"
        if has_node:
            node_present += 1
        if is_residual:
            residual += 1
        if kind == "system":
            conflicts += 1
        if (r.get("description_norm") or "").strip() in ambiguous:
            ambiguity_hits += 1

        # verify catalogue columns against pr00 on the padded join key
        pn = _pad_key(r.get("part_number") or "")
        if pn in pr00_map:
            pr00_checked += 1
            if pr00_map[pn] == (cat1, cat2, cat3):
                pr00_ok += 1

        out_rows.append(
            {
                "part_number": pn,
                "description_norm": r.get("description_norm") or "",
                # --- Axis A: identity tree (existing three levels only) ---
                "catalog_l1": cat1,
                "catalog_l2": cat2,
                "catalog_l3": cat3,
                "catalog_node_present": "1" if has_node else "0",
                "catalog_residual": "1" if is_residual else "0",
                # --- legacy AIM workbook vocabulary (context; not Axis B) ---
                "workbook_l1": wk1,
                "workbook_l2": (r.get("aim_l2") or "").strip(),
                "workbook_l3": (r.get("aim_l3") or "").strip(),
                "workbook_axis_kind": kind,
                "workbook_source": (r.get("aim_source") or "").strip(),
                # --- flags ---
                "axis_conflict": "1" if kind == "system" else "0",
                "desc_ambiguous": "1" if (r.get("description_norm") or "").strip() in ambiguous else "0",
                # --- passthrough ---
                "fig_key": (r.get("fig_key") or "").strip(),
                "filter_part_role": (r.get("filter_part_role") or "").strip(),
            }
        )

    fields = list(out_rows[0].keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "built_by": "01_data/91_build/build_aim_classification_v2.py",
        "purpose": (
            "Two-axes lock 2026-09-17: Axis A = catalog_l1/l2/l3 identity (figure-anchored); "
            "Axis B = commercial score beside Axis A (contested per part per market) — not built "
            "as scored columns in this file yet. Legacy workbook_l* is context only. "
            "Do not invent a fourth layer. Do not hang identity views from a commercial parent."
        ),
        "decision_ref": "DECISIONS.md 2026-09-17 — AIM classification: two axes locked",
        "source": str(V1_CSV),
        "source_modified": datetime.fromtimestamp(V1_CSV.stat().st_mtime, timezone.utc).isoformat(),
        "rows": len(out_rows),
        "axis_a_identity": "catalog_l1 / catalog_l2 / catalog_l3",
        "axis_b_commercial_score": (
            "separate measured attribute (contested / captive per part per market) — "
            "NOT a Level-1 parent; not scored in this CSV yet"
        ),
        "legacy_workbook_context": "workbook_l1 / workbook_l2 / workbook_l3 (neither Axis A nor Axis B)",
        "counts": {
            "catalog_node_present": node_present,
            "catalog_residual_other_review": residual,
            "workbook_axis_kind": dict(kinds),
            "axis_conflict_rows": conflicts,
            "description_ambiguous_rows": ambiguity_hits,
            "distinct_ambiguous_descriptions": len(ambiguous),
        },
        "catalogue_verification_vs_pr00": {
            "rows_checked": pr00_checked,
            "rows_matching": pr00_ok,
            "match_pct": round(100 * pr00_ok / pr00_checked, 4) if pr00_checked else None,
            "note": (
                "COPY-INTEGRITY ONLY: catalogue columns vs pr00_classification.csv. "
                "Both come from the same GPT workbook. This does NOT prove the classification "
                "is correct against customs codes, Isuzu figures, or part text. "
                "Keys are zero-padded to 10 characters on both sides."
            ),
        },
        "consumer_contract": [
            "Axis A (identity): group by catalog_l1/l2/l3. Wear and family views hang from catalog_l2/l3 or fig_key — never from a commercial posture parent (king-pin case).",
            "Axis B (commercial score): contested/captive per part per market sits beside Axis A. Never the hang-from parent for identity views. Do not invent a fourth taxonomy layer.",
            "Filter catalog_node_present=1 for a real Axis A family view.",
            "Report catalog_residual=1 (Other / review) as a named residual, never as a family.",
            "workbook_l1 is legacy AIM system context — neither Axis A nor Axis B. Never group workbook_l1 with catalog_l2.",
            "Spoken labels: shared/external vs internal; sales to dealer; price list / price revision; parts billed; reference dealer price. No street / sell-out / Book B.",
        ],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"rows                  {len(out_rows):,}")
    print(f"catalog node present  {node_present:,}")
    print(f"catalog residual      {residual:,}")
    print(f"workbook axis kinds   {dict(kinds)}")
    print(f"axis-conflict rows    {conflicts:,}  (workbook system-named)")
    print(f"ambiguous desc rows   {ambiguity_hits:,}  ({len(ambiguous)} descriptions)")
    if pr00_checked:
        print(f"pr00 verification     {pr00_ok:,}/{pr00_checked:,} = {100*pr00_ok/pr00_checked:.4f}%")
    print(f"-> {OUT_CSV}")
    print(f"-> {OUT_META}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
