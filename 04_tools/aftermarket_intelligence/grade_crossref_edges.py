# -*- coding: utf-8 -*-
"""Task 2.2 — grade the cross-reference edges so the graph becomes usable.

THE SITUATION, MEASURED FIRST
-----------------------------
The graph holds 7,443 edges; 6,455 are 'rival' edges (our own value line and
peer-carrier numbers excluded). Those 6,455 rest on **2,461 distinct competitor
numbers**, and **2,004 of those (81%) rest on a single source file**.

The plan's original method for this task was "judge doubtful edges with DeepSeek pro" (6.2).
**That route is closed here, and this script does not take it.** Measured 2026-09-25:
**100% of the rival edges are Eucon-sourced** (6,455 of 6,455; Eucon Online extract,
PartsPool, March online, UK survey). Jerome's standing rule is that Eucon-sourced rows are
never sent to DeepSeek or any outside-EU service — a boundary he kept deliberately when he
gave the scrape go. So no part of this graph may leave the machine.

WHAT THIS DOES INSTEAD
----------------------
Grades each edge from evidence already on disk, deterministically:

  1. CORROBORATION — how many distinct source files and vintages agree.
  2. THE TWO KNOWN TRAPS — `cpn_brand_collision` (one number under several brands) and
     `cpn_multi_partno` (one rival number claimed for several of our parts).
  3. SELF-CONTRADICTION — where one rival number is claimed for several of our part
     numbers, do those parts agree on their parts category? A number that is said to
     fit both a clutch and a brake rotor is not a cross-reference, it is noise.
  4. FORMAT — whether the competitor number looks like a plausible part number at all.

Output: `state/crossref_graded.csv` — every rival edge with a tier and the reason.
Nothing is deleted; a doubtful edge is labelled, never dropped.

This is deliberately conservative: it cannot *confirm* a match the way a human or a
language model could. It separates the edges that are safe to act on from the ones that
need eyes, which is what makes the rest of the graph usable.

Run:  python 04_tools/aftermarket_intelligence/grade_crossref_edges.py
"""
from __future__ import annotations

import json
import re
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
EDGES = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_edges.parquet"
CATALOG = ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv"
OUT = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
REPORT = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "CROSSREF_GRADING_REPORT.md"

# A competitor number should look like a part number. This is a sanity filter, not a
# match test, and it is deliberately permissive: aftermarket numbering is wildly varied
# (`ISC633`, `F 026 407 311` for Bosch, `C-15670`, `MAN N1319021`, `FO-4071XX`).
#
# First version of this was `^[A-Z]{0,4}[\d][...]{4,24}$` and it rejected 2,321 edges —
# caught by auditing the rejects on 2026-09-25. Almost every one was a real part number;
# the rule simply demanded a minimum length that short numbers do not meet. A false
# reject is worse than no filter, because it hides good cross-references. So the rule now
# rejects only what clearly cannot be a part number.
PN_SHAPE = re.compile(r"^[A-Z0-9][A-Z0-9\-\_\./ ]{2,27}$")
MIN_DIGITS = 2


def plausible_part_number(value: str) -> bool:
    """True unless the value clearly cannot be a part number."""
    v = str(value or "").strip().upper()
    if len(v) < 3 or len(v) > 28:
        return False
    if not PN_SHAPE.match(v):
        return False
    # must carry some digits; a bare word is a description, not a number
    return sum(c.isdigit() for c in v) >= MIN_DIGITS


def tier_of(row) -> tuple[str, str]:
    """Return (tier, reason) for one edge. Conservative by construction."""
    reasons = []

    n_files = int(row["n_source_files"])
    n_vintages = int(row["n_vintages"])
    brand_collision = bool(row["brand_collision"])
    multi_partno = bool(row["multi_partno"])
    conflicts = bool(row["category_conflict"])
    shape_ok = bool(row["pn_shape_ok"])
    has_category = bool(row["has_category"])

    # --- hard rejects: the edge contradicts itself -----------------------------
    if conflicts:
        return "reject", "same rival number claimed for our parts in conflicting categories"
    if not shape_ok:
        return "reject", "competitor number is not shaped like a part number"

    # --- doubtful: known traps or a lone witness -------------------------------
    if brand_collision:
        reasons.append("same number appears under more than one brand")
    if multi_partno:
        reasons.append("same rival number claimed for several of our parts")
    if n_files < 2:
        reasons.append("only one source file")

    if brand_collision or multi_partno:
        return "doubtful", "; ".join(reasons)
    if n_files < 2:
        # A single source with no trap is still a single witness. Not usable alone.
        return "doubtful", "single source file, no corroboration"

    # --- corroborated ----------------------------------------------------------
    if n_files >= 3 or n_vintages >= 3:
        return "confirmed", f"{n_files} source files across {n_vintages} vintages"
    if n_files >= 2 and n_vintages >= 2:
        return "confirmed", f"{n_files} source files across {n_vintages} vintages"
    if n_files >= 2:
        return "likely", f"{n_files} source files, but one vintage"
    if has_category:
        return "likely", "single source but our part carries a known category"
    return "doubtful", "; ".join(reasons) or "insufficient corroboration"


def main() -> int:
    for p in (EDGES, CATALOG):
        if not p.exists():
            print(f"REFUSED — missing input: {p}")
            return 1

    d = pd.read_parquet(EDGES)
    print(f"edges read: {len(d):,}")

    # the boundary, asserted rather than assumed
    sf = d["source_family"].astype(str)
    eucon = sf.str.upper().str.contains("EUCON")
    print(f"Eucon-sourced: {int(eucon.sum()):,} of {len(d):,} — "
          f"these never leave this machine (stated, not inferred)")

    rival = d[(d["is_our_own_line"].astype(str) == "0") &
              (d["is_peer_carrier"].astype(str) == "0")].copy()
    print(f"rival edges to grade: {len(rival):,}")

    # --- corroboration, per competitor number ---------------------------------
    g = rival.groupby("cpn_key")
    corrob = pd.DataFrame({
        "n_source_files": g["source"].nunique(),
        "n_vintages": g["source_vintage"].nunique(),
        "n_part_numbers": g["part_no"].nunique(),
        "n_brands": g["competitor_brand_norm"].nunique(),
    })
    rival = rival.merge(corrob, left_on="cpn_key", right_index=True, how="left")

    # --- our-side categories, to test self-contradiction ----------------------
    cat = pd.read_csv(CATALOG, dtype=str, usecols=["part_number", "pms_category"])
    cat = cat.dropna().drop_duplicates("part_number")
    cat_of = dict(zip(cat["part_number"], cat["pms_category"]))
    rival["part_no"] = rival["part_no"].astype(str)
    rival["our_category"] = rival["part_no"].map(cat_of)

    # a rival number claimed for several of our parts: do those parts agree?
    cat_per_cpn = rival.dropna(subset=["our_category"]).groupby("cpn_key")["our_category"].nunique()
    conflicting = set(cat_per_cpn[cat_per_cpn > 1].index)

    rival["n_source_files"] = rival["n_source_files"].fillna(1).astype(int)
    rival["n_vintages"] = rival["n_vintages"].fillna(1).astype(int)
    rival["brand_collision"] = rival["n_brands"].fillna(1).astype(int) > 1
    rival["multi_partno"] = rival["n_part_numbers"].fillna(1).astype(int) > 1
    rival["category_conflict"] = rival["cpn_key"].isin(conflicting)
    rival["pn_shape_ok"] = rival["cpn_written"].map(plausible_part_number).fillna(False)
    rival["has_category"] = rival["our_category"].notna()

    graded = rival.apply(lambda r: pd.Series(tier_of(r), index=["tier", "reason"]), axis=1)
    rival = pd.concat([rival, graded], axis=1)

    cols = ["edge_id", "part_no", "our_category", "competitor_brand", "competitor_pn",
            "cpn_key", "source", "source_vintage", "n_source_files", "n_vintages",
            "n_part_numbers", "brand_collision", "multi_partno", "category_conflict",
            "pn_shape_ok", "has_category", "tier", "reason",
            "has_competitor_price", "competitor_price", "currency"]
    out = rival[[c for c in cols if c in rival.columns]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    counts = out["tier"].value_counts()
    print("\n" + "=" * 74)
    print(f"{'tier':<12} {'edges':>8} {'rival numbers':>15}")
    print("-" * 38)
    for t in ("confirmed", "likely", "doubtful", "reject"):
        n = int(counts.get(t, 0))
        keys = out.loc[out["tier"] == t, "cpn_key"].nunique()
        print(f"{t:<12} {n:>8,} {keys:>15,}")

    usable = out[out["tier"].isin(("confirmed", "likely"))]
    print(f"\nusable for competition work : {len(usable):,} edges "
          f"({usable['cpn_key'].nunique():,} counterpart numbers)")
    print(f"need eyes before use        : {len(out) - len(usable):,} edges")

    # spendable vs not: does a usable edge even have a price?
    with_price = usable[usable["has_competitor_price"].astype(str).isin(("1", "True", "true"))]
    print(f"  of the usable, carrying a price: {len(with_price):,}")

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "04_tools/aftermarket_intelligence/grade_crossref_edges.py",
        "rival_edges_graded": int(len(out)),
        "tiers": {k: int(v) for k, v in counts.items()},
        "usable_edges": int(len(usable)),
        "usable_counterpart_numbers": int(usable["cpn_key"].nunique()),
        "data_boundary": ("100% of rival edges are Eucon-sourced. Jerome's standing rule "
                          "bars Eucon rows from DeepSeek or any outside-EU service, so the "
                          "plan's original method for this card (DeepSeek pro, prompt 6.2) "
                          "was NOT used. Grading is local and deterministic."),
        "method_limit": ("This separates safe edges from doubtful ones. It cannot confirm a "
                         "match the way a human or a language model could, and a 'confirmed' "
                         "tier means corroborated by independent source files — not verified "
                         "against a manufacturer catalogue."),
    }
    (OUT.with_suffix(".meta.json")).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    REPORT.write_text(
        "# Cross-reference grading (task 2.2)\n\n"
        f"Built {meta['built_at']} by `grade_crossref_edges.py`.\n\n"
        f"- rival edges graded: **{len(out):,}**\n"
        f"- confirmed: **{int(counts.get('confirmed', 0)):,}**\n"
        f"- likely: **{int(counts.get('likely', 0)):,}**\n"
        f"- doubtful: **{int(counts.get('doubtful', 0)):,}**\n"
        f"- reject: **{int(counts.get('reject', 0)):,}**\n"
        f"- usable (confirmed + likely): **{len(usable):,}** edges, "
        f"{usable['cpn_key'].nunique():,} counterpart numbers\n"
        f"- of the usable, carrying a price: **{len(with_price):,}**\n\n"
        "## The boundary that shaped the method\n\n"
        "100% of the rival edges are Eucon-sourced. Jerome's standing rule bars Eucon rows "
        "from DeepSeek or any outside-EU service, so the plan's original method for this card "
        "— DeepSeek pro judging (prompt 6.2) — was **not** used. Grading here is local and "
        "deterministic.\n\n"
        "## What the tiers mean\n\n"
        "| tier | meaning |\n|---|---|\n"
        "| confirmed | corroborated by 2+ independent source files across 2+ vintages, no trap flag |\n"
        "| likely | 2+ source files, or a single source where our own part carries a category |\n"
        "| doubtful | a single source file, or one of the two known traps is set |\n"
        "| reject | the edge contradicts itself, or the number is not shaped like a part number |\n\n"
        "A 'confirmed' tier means corroborated by independent files. It is **not** verified "
        "against a manufacturer catalogue, and it is not a substitute for that.\n\n"
        "## Limit, stated plainly\n\n"
        "This separates edges that are safe to act on from edges that need eyes. It cannot "
        "confirm a match a human could.\n",
        encoding="utf-8")

    print(f"\nwrote {OUT.name}, {OUT.with_suffix('.meta.json').name}, {REPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
