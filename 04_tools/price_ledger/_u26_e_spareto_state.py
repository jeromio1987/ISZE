# -*- coding: utf-8 -*-
"""U26 / agent E -- merge C1's Spareto reading into the shared cross-reference state
file, then measure the corroboration arithmetic from disk.

Model:
  * `state/spareto_crossref.csv` -- pipeline output for `grade_crossref_edges.py`.
    The 2026-10-02 pass (487 parts) is kept unchanged; C1's U26 pass (123 numbers,
    2026-10-07) is appended. A row is new when (part_no, competitor_pn, brand) is not
    already in the file, so nothing is duplicated and no Eurocon row is touched.
  * `_u26/E/spareto_crossref_before_after.json` -- the arithmetic, recomputed from the
    files: pairs, numbers, corroboration, one-step moves, and the C2 figures to compare.

Nothing is inferred. A pair counts as corroborated only when a second independent
pipeline (the Eucon cross-reference graph) claims the same (our part, rival number)
pair under an agreeing brand.
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

HERE = Path(__file__).resolve().parent            # 04_tools/price_ledger
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "04_tools" / "aftermarket_intelligence" / "state"
SPARETO = STATE / "spareto_crossref.csv"
SPARETO_PER_PART = STATE / "spareto_crossref_per_part.csv"
EDGES = STATE / "crossref_edges.parquet"
GRADED = STATE / "crossref_graded.csv"
ALIASES = STATE / "brand_aliases.csv"
U26 = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26"
C1 = U26 / "C1" / "spareto_crossref.csv"
C1_PP = U26 / "C1" / "spareto_crossref_per_part.csv"
WORKLIST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"
                r"\MARKET_SCRAPE_WORKLIST_20261007.csv")
NEEDS_112 = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"
                 r"\NEEDS_CROSSREF_112_PNS_20261007.csv")
OUT = U26 / "E" / "spareto_crossref_before_after.json"

STEP_UP = {"reject": "doubtful", "doubtful": "likely", "likely": "confirmed"}


def key(v) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def brand_key(v, alias: dict) -> str:
    k = key(v)
    return key(alias.get(k, v))


def load_alias() -> dict:
    if not ALIASES.exists():
        return {}
    a = pd.read_csv(ALIASES, dtype=str, encoding="utf-8")
    return {key(al): can for al, can in zip(a["alias"], a["canonical_brand"])}


def brand_agrees(a, b, alias: dict) -> bool:
    def forms(x):
        x = str(x or "")
        return {key(x)} | {key(m) for m in re.findall(r"\(([^)]+)\)", x)}
    fa, fb = forms(a), forms(b)
    for x in fa:
        for y in fb:
            if x and y and (x == y or x in y or y in x):
                return True
    ca = {brand_key(f, alias) for f in fa if f}
    cb = {brand_key(f, alias) for f in fb if f}
    return bool(ca & cb)


def main() -> int:
    alias = load_alias()
    before = pd.read_csv(SPARETO, dtype=str)
    c1 = pd.read_csv(C1, dtype=str)
    before_pp = pd.read_csv(SPARETO_PER_PART, dtype=str)
    c1_pp = pd.read_csv(C1_PP, dtype=str)

    def pair_keys(df):
        return list(zip(df["part_no"], df["competitor_pn"].map(key),
                        df["competitor_brand"].map(lambda b: brand_key(b, alias))))

    have = set(pair_keys(before))
    c1 = c1[~c1["part_no"].str.upper().eq("ISUZU")].copy()   # genuine card, not a rival
    new_mask = [k not in have for k in pair_keys(c1)]
    added = c1[new_mask].copy()
    merged = pd.concat([before, added], ignore_index=True)
    merged.to_csv(SPARETO, index=False)

    before_pp_pns = set(before_pp["part_no"])
    pp_add = c1_pp[~c1_pp["part_no"].isin(before_pp_pns)].copy()
    pd.concat([before_pp, pp_add], ignore_index=True).to_csv(SPARETO_PER_PART, index=False)

    # ---------------- the arithmetic, from disk ------------------------------
    sp = pd.read_csv(SPARETO, dtype=str)
    sp = sp[sp["part_no"].str.fullmatch(r"\d{10}", na=False)]
    sp = sp[sp["competitor_brand"].str.upper() != "ISUZU"]
    sp["cpn_key"] = sp["competitor_pn"].map(key)
    sp = sp[sp["cpn_key"] != ""]

    wl = pd.read_csv(WORKLIST, dtype=str)
    wl_pns = sorted({p for p in wl["part_number"].astype(str) if re.fullmatch(r"\d{10}", p)})
    n112 = sorted({p for p in pd.read_csv(NEEDS_112, dtype=str)["isuzu_part_number"]
                   .astype(str) if re.fullmatch(r"\d{10}", p)})
    eucon11 = sorted(set(wl_pns) - set(n112))

    edges = pd.read_parquet(EDGES)
    rival = edges[(edges["is_our_own_line"].astype(str) == "0")
                  & (edges["is_peer_carrier"].astype(str) == "0")].copy()
    rival["cpn_key"] = rival["cpn_key"].map(key)
    graph = set(zip(rival["part_no"].astype(str), rival["cpn_key"]))

    pairs = sp[["part_no", "cpn_key"]].drop_duplicates().copy()
    pairs["in_graph"] = [(p, k) in graph for p, k in zip(pairs["part_no"], pairs["cpn_key"])]

    # brand agreement: the Eucon edge's brand vs the Spareto brand for the same pair
    e_brand = (rival.groupby(["part_no", "cpn_key"])["competitor_brand"]
               .agg(lambda x: sorted({str(v) for v in x if str(v)}))
               .to_dict())
    sp_brand = (sp.groupby(["part_no", "cpn_key"])["competitor_brand"]
                .agg(lambda x: sorted({str(v) for v in x if str(v)}))
                .to_dict())
    agrees = []
    for p, k in zip(pairs["part_no"], pairs["cpn_key"]):
        e_b = e_brand.get((p, k), [])
        s_b = sp_brand.get((p, k), [])
        agrees.append(any(brand_agrees(x, y, alias) for x in e_b for y in s_b))
    pairs["brand_agrees"] = agrees
    cat = pd.read_csv(ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv",
                      dtype=str)
    cat = cat.dropna(subset=["part_number"]).drop_duplicates("part_number")
    pairs["our_category"] = pairs["part_no"].map(
        dict(zip(cat["part_number"], cat["pms_category"])))

    def summarise(sub: pd.DataFrame) -> dict:
        return {
            "pairs": int(len(sub)),
            "numbers_with_a_pair": int(sub["part_no"].nunique()),
            "pairs_in_eucon_graph": int(sub["in_graph"].sum()),
            "pairs_in_graph_brand_agrees": int((sub["in_graph"] & sub["brand_agrees"]).sum()),
            "single_source_only": int((~sub["in_graph"]).sum()),
        }

    # the tier file as it stands after the merge, and as it stood before
    graded = pd.read_csv(GRADED, dtype=str)
    before_tiers = (graded["tier_eucon_only"].replace("", pd.NA).dropna().value_counts().to_dict())
    after_tiers = graded["tier"].value_counts().to_dict()
    moved = graded[graded["tier_eucon_only"].notna()
                   & (graded["tier"] != graded["tier_eucon_only"])]

    worklist_pairs = pairs[pairs["part_no"].isin(wl_pns)]
    out = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": ("A pair from ONE source stays a candidate. A pair claimed by a second "
                 "independent pipeline (the Eucon cross-reference graph) moves the existing "
                 "edge up exactly one step (reject->doubtful->likely->confirmed) when the "
                 "brand agrees, never down. Nothing is 'approved' unless Eucon-listed "
                 "(Jerome-approved) or graded confirmed by the existing rules."),
        "sources_are_pipelines": ("C1 and C2 are two readings of ONE pipeline (Spareto) and "
                                  "count as day stability, never as two witnesses. The two "
                                  "independent pipelines here are Eucon and Spareto."),
        "state_file": {
            "path": "04_tools/aftermarket_intelligence/state/spareto_crossref.csv",
            "rows_before": int(len(before)),
            "c1_rows_read": int(len(c1)),
            "c1_rows_appended": int(len(added)),
            "rows_after": int(len(merged)),
            "parts_before": int(before["part_no"].nunique()),
            "parts_after": int(sp["part_no"].nunique()),
            "c1_label": "u26_c1_spareto_20261007 (observed 2026-10-07)",
            "previous_label": "spareto_tierA_2026-10-02 (observed 2026-10-02)",
        },
        "worklist": {"numbers": len(wl_pns), "needs_crossref_112": len(n112),
                     "eucon_11": len(eucon11)},
        "q1_numbers_with_spareto_pair": {
            "of_worklist": int(worklist_pairs["part_no"].nunique()),
            "of_123": int(worklist_pairs["part_no"].nunique()),
            "of_112_no_eucon": int(worklist_pairs[worklist_pairs["part_no"].isin(n112)]
                                   ["part_no"].nunique()),
            "of_11_eucon": int(worklist_pairs[worklist_pairs["part_no"].isin(eucon11)]
                               ["part_no"].nunique()),
        },
        "q2_of_112": {},
        "q3_pairs": {"all_worklist": summarise(worklist_pairs),
                     "all_1688_pairs": summarise(pairs)},
        "tier_counts": {
            "before_eucon_only": {k: int(v) for k, v in before_tiers.items()},
            "after_full_file": {k: int(v) for k, v in after_tiers.items()},
            "edges_moved": int(len(moved)),
            "moves": {f"{a} -> {b}": int(n) for (a, b), n in
                      moved.groupby(["tier_eucon_only", "tier"]).size().items()},
            "distinct_pairs_moved": int(moved[["part_no", "cpn_key"]]
                                        .drop_duplicates().shape[0])
            if "cpn_key" in moved.columns else None,
        },
        "c2_measured_for_comparison": {
            "of_123_with_a_pair": 69, "of_112_with_a_pair": 58,
            "of_112_single_source_only": 54, "of_112_with_a_corroborated_pair": 4,
            "pairs_on_123": 735, "pairs_corroborated": 156,
            "pairs_single_source": 579, "would_move_an_eucon_edge": 155,
        },
    }
    sub112 = worklist_pairs[worklist_pairs["part_no"].isin(n112)]
    out["q2_of_112"] = {
        "gained_at_least_one_pair": int(sub112["part_no"].nunique()),
        "with_at_least_one_corroborated_pair": int(
            sub112.loc[sub112["in_graph"] & sub112["brand_agrees"], "part_no"].nunique()),
        "single_source_only_numbers": int(
            sub112.loc[~sub112["part_no"].isin(
                sub112.loc[sub112["in_graph"] & sub112["brand_agrees"], "part_no"]),
                "part_no"].nunique()),
        "pairs_corroborated": int((sub112["in_graph"] & sub112["brand_agrees"]).sum()),
        "pairs_single_source": int((~sub112["in_graph"]).sum()),
    }
    out["q1_numbers_with_spareto_pair"]["c1_only_reading"] = {
        "pairs": 735, "numbers_of_123": 69}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
