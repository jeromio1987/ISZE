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
# Second, independent source (Jerome's go, 2026-10-02): Spareto's /oe/<isuzu number> pages,
# parsed by `site_spareto.py --from-pass`. Not Eucon. Its prices are NOT used here.
SPARETO = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "spareto_crossref.csv"
SPARETO_NEW = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_spareto_new_edges.csv"
SPARETO_MOVES = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_spareto_moves.csv"
STEP_UP = {"reject": "doubtful", "doubtful": "likely", "likely": "confirmed", "confirmed": "confirmed"}


def _key(v) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def _brand_agrees(a, b) -> bool:
    """Normalised containment, also on a bracketed brand: `Wilmink Group (Febi)` -> FEBI."""
    def forms(x):
        x = str(x or "")
        return {_key(x)} | {_key(m) for m in re.findall(r"\(([^)]+)\)", x)}
    for fa in forms(a):
        for fb in forms(b):
            if fa and fb and (fa == fb or fa in fb or fb in fa):
                return True
    return False


def load_spareto(path: Path = SPARETO) -> pd.DataFrame:
    """Spareto (part_no, cpn_key, brand) pairs. Empty frame if the file is absent."""
    if not path.exists():
        return pd.DataFrame(columns=["part_no", "cpn_key", "sp_brand", "sp_cpn"])
    sp = pd.read_csv(path, dtype=str)
    sp = sp[sp["part_no"].str.fullmatch(r"\d{10}", na=False)]
    sp = sp[sp["competitor_brand"].str.upper() != "ISUZU"]          # genuine card, not a rival
    out = pd.DataFrame({"part_no": sp["part_no"], "cpn_key": sp["competitor_pn"].map(_key),
                        "sp_brand": sp["competitor_brand"], "sp_cpn": sp["competitor_pn"]})
    return out[out["cpn_key"] != ""].drop_duplicates(["part_no", "cpn_key", "sp_brand"])

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


def apply_second_source(rival: pd.DataFrame, sp: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Grade an edge up ONE step when Spareto lists the same (our part, rival number) pair
    under an agreeing brand. One step only, never more, never down:
        reject -> doubtful, doubtful -> likely, likely -> confirmed.
    The Eucon-only tier is kept in `tier_eucon_only` so every move is auditable."""
    rival = rival.copy()
    rival["tier_eucon_only"] = rival["tier"]
    rival["spareto_pair"] = False
    rival["spareto_brand_agrees"] = False
    rival["spareto_brand"] = ""
    stats = {"spareto_pairs": 0, "pairs_matching_graph_edges": 0,
             "edges_pair_matched": 0, "edges_pair_matched_brand_differs": 0, "edges_moved": 0}
    if sp.empty:
        return rival, stats
    stats["spareto_pairs"] = int(sp[["part_no", "cpn_key"]].drop_duplicates().shape[0])
    rival["_k"] = rival["cpn_key"].map(_key)
    brands = sp.groupby(["part_no", "cpn_key"])["sp_brand"].agg(lambda x: sorted(set(x))).to_dict()
    for i, r in rival.iterrows():
        bl = brands.get((r["part_no"], r["_k"]))
        if not bl:
            continue
        rival.at[i, "spareto_pair"] = True
        rival.at[i, "spareto_brand"] = "; ".join(bl)
        if any(_brand_agrees(b, r["competitor_brand"]) for b in bl):
            rival.at[i, "spareto_brand_agrees"] = True
            new = STEP_UP[r["tier"]]
            if new != r["tier"]:
                rival.at[i, "tier"] = new
                rival.at[i, "reason"] = (f"{r['reason']}; graded up {r['tier']} -> {new}: "
                                         f"Spareto lists the same pair (independent, non-Eucon)")
            else:
                rival.at[i, "reason"] = f"{r['reason']}; Spareto also lists the pair"
    graph_pairs = set(zip(rival["part_no"], rival["_k"]))
    sp_pairs = set(zip(sp["part_no"], sp["cpn_key"]))
    stats["pairs_matching_graph_edges"] = len(sp_pairs & graph_pairs)
    # rival number known to the graph, but Spareto ties it to a DIFFERENT Isuzu part:
    # not a corroboration of any edge, so nothing moves; counted so it is visible.
    graph_keys = set(rival["_k"])
    stats["pairs_key_in_graph_other_part"] = len({(p, k) for p, k in sp_pairs - graph_pairs
                                                  if k in graph_keys})
    stats["spareto_part_numbers"] = int(sp["part_no"].nunique())
    stats["spareto_part_numbers_in_graph"] = len(set(sp["part_no"]) & set(rival["part_no"]))
    stats["edges_pair_matched"] = int(rival["spareto_pair"].sum())
    stats["edges_pair_matched_brand_differs"] = int(
        (rival["spareto_pair"] & ~rival["spareto_brand_agrees"]).sum())
    stats["edges_moved"] = int((rival["tier"] != rival["tier_eucon_only"]).sum())
    moved = rival[rival["tier"] != rival["tier_eucon_only"]]
    stats["distinct_pairs_moved"] = int(moved[["part_no", "_k"]].drop_duplicates().shape[0])
    rival = rival.drop(columns=["_k"])
    return rival, stats


def main() -> int:
    use_spareto = "--no-spareto" not in sys.argv
    out_path = OUT
    if "--out" in sys.argv:
        out_path = Path(sys.argv[sys.argv.index("--out") + 1])
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

    # --- second, independent source: Spareto (not Eucon) ----------------------
    sp_stats = {}
    if use_spareto:
        sp = load_spareto(SPARETO)
        print(f"Spareto pairs read: {len(sp):,} (from {SPARETO.name})" if len(sp)
              else f"Spareto: no file at {SPARETO} - Eucon-only grading")
        rival, sp_stats = apply_second_source(rival, sp)
        if not sp.empty and out_path == OUT:
            graph_pairs = set(zip(rival["part_no"], rival["cpn_key"].map(_key)))
            new_edges = sp[[(p_, k) not in graph_pairs
                            for p_, k in zip(sp["part_no"], sp["cpn_key"])]].copy()
            new_edges = (new_edges.groupby(["part_no", "cpn_key"])
                         .agg(competitor_brand=("sp_brand", lambda x: "; ".join(sorted(set(x)))),
                              competitor_pn=("sp_cpn", "first")).reset_index())
            new_edges["source"] = "Spareto /oe/ page"
            new_edges["tier"] = "doubtful"
            new_edges["reason"] = "single source (Spareto only), not in the Eucon graph"
            new_edges.to_csv(SPARETO_NEW, index=False)
            moves = rival[rival["tier"] != rival["tier_eucon_only"]]
            moves[["edge_id", "part_no", "competitor_brand", "competitor_pn", "spareto_brand",
                   "tier_eucon_only", "tier", "reason"]].to_csv(SPARETO_MOVES, index=False)
            sp_stats["new_pairs_not_in_graph"] = int(len(new_edges))
            sp_stats["new_pairs_part_numbers"] = int(new_edges["part_no"].nunique())
            sp_stats["moves"] = {f"{a} -> {b}": int(n) for (a, b), n in
                                 moves.groupby(["tier_eucon_only", "tier"]).size().items()}
        print(json.dumps(sp_stats, indent=2))

    cols = ["edge_id", "part_no", "our_category", "competitor_brand", "competitor_pn",
            "cpn_key", "source", "source_vintage", "n_source_files", "n_vintages",
            "n_part_numbers", "brand_collision", "multi_partno", "category_conflict",
            "pn_shape_ok", "has_category", "tier", "reason",
            "has_competitor_price", "competitor_price", "currency",
            "tier_eucon_only", "spareto_pair", "spareto_brand_agrees", "spareto_brand"]
    out = rival[[c for c in cols if c in rival.columns]]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    if out_path != OUT:
        print(f"\nwrote {out_path} only (comparison run; meta and report untouched)")
        return 0

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
        "second_source": ({"file": str(SPARETO.relative_to(ROOT)), **sp_stats,
                           "rule": "one step up (reject->doubtful->likely->confirmed) when Spareto "
                                   "lists the same (part_no, rival number) pair under an agreeing "
                                   "brand; never down. Spareto's upstream data source is not stated "
                                   "on its pages: independent of Eucon as a pipeline, not proven "
                                   "independent upstream."} if sp_stats else None),
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
        + (("## Second source: Spareto (added 2026-10-02)\n\n"
            f"Spareto `/oe/<isuzu number>` pages, file `{SPARETO.name}`. An edge moves up ONE "
            "tier when Spareto lists the same (our part, rival number) pair under an agreeing "
            "brand; never down. The Eucon-only tier is kept in `tier_eucon_only`.\n\n"
            f"- edges whose pair Spareto lists: {sp_stats.get('edges_pair_matched', 0):,} "
            f"(brand differs, not moved: {sp_stats.get('edges_pair_matched_brand_differs', 0):,})\n"
            f"- edges moved: {sp_stats.get('edges_moved', 0):,} "
            f"({', '.join(f'{k}: {v}' for k, v in sp_stats.get('moves', {}).items()) or 'none'})\n"
            f"- Spareto pairs not in the graph (new, single-source, doubtful): "
            f"{sp_stats.get('new_pairs_not_in_graph', 0):,} -> `{SPARETO_NEW.name}`\n\n"
            "Spareto's own upstream source is not stated on its pages: it is independent of "
            "Eucon as a pipeline, not proven independent upstream.\n\n") if sp_stats else "")
        + "## Limit, stated plainly\n\n"
        "This separates edges that are safe to act on from edges that need eyes. It cannot "
        "confirm a match a human could.\n",
        encoding="utf-8")

    print(f"\nwrote {OUT.name}, {OUT.with_suffix('.meta.json').name}, {REPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
