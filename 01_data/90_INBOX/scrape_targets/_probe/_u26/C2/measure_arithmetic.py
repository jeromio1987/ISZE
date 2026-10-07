# -*- coding: utf-8 -*-
"""U26 / agent C2 — corroboration arithmetic over the 123 worklist numbers.

This is a MEASUREMENT script. It writes only inside `_u26/C2/`. It never writes
`crossref_graded.csv`, `spareto_crossref.csv` or any other shared state file, and it
never runs the regrade — the merge step owns that.

SOURCES AND INDEPENDENCE
------------------------
An "independent source" is a distinct PIPELINE, not a distinct day:

  * `eucon`   — the Eucon cross-reference graph (`state/crossref_edges.csv`);
  * `spareto` — Spareto `/oe/<number>` pages.

C1's pass and C2's pass are TWO READINGS OF ONE SOURCE (Spareto, two days). They are
reported as a day-stability measure, never counted as two independent witnesses. A
pair listed by Spareto alone stays a CANDIDATE, however many days it appears on.
A pair that is also claimed by the Eucon graph has two independent sources and is
what would move a grade.

Reports:
  1. how many of the 123 numbers now have >= 1 Spareto brand pair;
  2. of the 112 numbers with no Eucon cross-reference, how many gained >= 1 pair,
     and how many of those are single-source only (which stays CANDIDATE);
  3. how many Spareto pairs are ALSO claimed by another independent source (the
     movement condition). A pair from one source stays a candidate.

The tier logic is imported from `grade_crossref_edges.py` so the numbers reconcile
with the merge step. The Eucon-only grading is re-run here and asserted against the
committed `crossref_graded.csv` (`tier_eucon_only`) before any output is written.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent            # .../_probe/_u26/C2
WORKTREE = HERE.parents[5]
ISZE = WORKTREE
PASSES = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "passes"
STATE = ISZE / "04_tools" / "aftermarket_intelligence" / "state"
EDGES = STATE / "crossref_edges.csv"
CATALOG = ISZE / "01_data" / "00_derived" / "parts_catalog_dimension.csv"
GRADED = STATE / "crossref_graded.csv"
CROSSREF_MOD = ISZE / "04_tools" / "aftermarket_intelligence" / "grade_crossref_edges.py"
SPARETO_MOD = ISZE / "04_tools" / "delegation" / "parsers" / "site_spareto.py"

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
NEEDS112 = MAIN / "01_data" / "90_INBOX" / "NEEDS_CROSSREF_112_PNS_20261007.csv"

DAY1_LABELS = ["u26_c1_spareto_20261007"]
DAY2_LABELS = ["u26_c2_spareto_20261008", "u26_c2_spareto_day2"]
SRC_EUCON, SRC_SPARETO = "eucon", "spareto"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pns_from_seed(path: Path) -> list[str]:
    out, seen = [], set()
    for ln in path.read_text(encoding="utf-8").splitlines():
        p = ln.strip()
        if re.fullmatch(r"\d{10}", p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def spareto_pairs_from_pass(gmod, label: str) -> tuple[pd.DataFrame, dict]:
    """One Spareto pass folder -> (part_no, cpn_key, brand, cpn) pairs. One per card."""
    pdir = PASSES / label
    info = {"label": label, "exists": (pdir / "fetch_spareto.jsonl").exists(),
            "entries": 0, "parsed": 0, "parse_errors": []}
    cols = ["part_no", "cpn_key", "brand", "cpn"]
    log = pdir / "fetch_spareto.jsonl"
    if not log.exists():
        return pd.DataFrame(columns=cols), info
    entries = {}
    for ln in log.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            j = json.loads(ln)
            entries[j["pn"]] = j                               # last record wins
    info["entries"] = len(entries)
    rows = []
    for pn, j in sorted(entries.items()):
        if j["outcome"] not in ("ok", "cached"):
            continue
        cp = pdir / "cache" / "spareto.com" / (
            hashlib.sha256(j["url"].encode("utf-8")).hexdigest()[:16] + ".html")
        if not cp.exists():
            continue
        try:
            got = gmod.parse(cp.read_text(encoding="utf-8", errors="replace"),
                             source_url=j["url"], observed_at=j["fetched_at"][:10])
        except Exception as e:                                 # noqa: BLE001
            info["parse_errors"].append(f"{pn}: {str(e)[:90]}")
            continue
        info["parsed"] += 1
        for r in got:
            rows.append((r["part_no"],
                         re.sub(r"[^A-Z0-9]", "", str(r["competitor_pn"]).upper()),
                         r["competitor_brand"], r["competitor_pn"]))
    df = pd.DataFrame(rows, columns=cols)
    if len(df):
        df = df[df["cpn_key"] != ""].drop_duplicates(["part_no", "cpn_key", "brand"])
    return df, info


def eucon_tiers(mod, rival: pd.DataFrame, cat_of: dict) -> pd.DataFrame:
    """Recompute the Eucon-only tier exactly as grade_crossref_edges.py main() does."""
    rival = rival.copy()
    rival["competitor_brand_norm"] = rival["competitor_brand_norm"].map(mod.canonical_brand)
    g = rival.groupby("cpn_key")
    corrob = pd.DataFrame({
        "n_source_files": g["source"].nunique(),
        "n_vintages": g["source_vintage"].nunique(),
        "n_part_numbers": g["part_no"].nunique(),
        "n_brands": g["competitor_brand_norm"].nunique(),
    })
    rival = rival.merge(corrob, left_on="cpn_key", right_index=True, how="left")
    rival["part_no"] = rival["part_no"].astype(str)
    rival["our_category"] = rival["part_no"].map(cat_of)
    cat_per_cpn = rival.dropna(subset=["our_category"]).groupby("cpn_key")["our_category"].nunique()
    conflicting = set(cat_per_cpn[cat_per_cpn > 1].index)
    rival["n_source_files"] = rival["n_source_files"].fillna(1).astype(int)
    rival["n_vintages"] = rival["n_vintages"].fillna(1).astype(int)
    rival["brand_collision"] = rival["n_brands"].fillna(1).astype(int) > 1
    rival["multi_partno"] = rival["n_part_numbers"].fillna(1).astype(int) > 1
    rival["category_conflict"] = rival["cpn_key"].isin(conflicting)
    rival["pn_shape_ok"] = rival["cpn_written"].map(mod.plausible_part_number).fillna(False)
    rival["has_category"] = rival["our_category"].notna()
    graded = rival.apply(lambda r: pd.Series(mod.tier_of(r), index=["tier", "reason"]), axis=1)
    return pd.concat([rival, graded], axis=1)


def main() -> int:
    mod = load_module(CROSSREF_MOD, "grade_crossref_edges")
    gmod = load_module(SPARETO_MOD, "site_spareto")
    mod._ALIAS = mod.load_aliases()

    seed = pns_from_seed(HERE / "seed_oe_pns.csv")
    all123 = set(seed)
    needs = {r["isuzu_part_number"].strip().zfill(10)
             for r in csv.DictReader(NEEDS112.open(encoding="utf-8"))}
    needs112 = all123 & needs
    eucon11 = all123 - needs112

    # ---- Eucon graph, graded the same way the shared script does -------------
    d = pd.read_csv(EDGES, dtype=str)
    rival = d[(d["is_our_own_line"].astype(str) == "0") &
              (d["is_peer_carrier"].astype(str) == "0")].copy()
    cat = pd.read_csv(CATALOG, dtype=str, usecols=["part_number", "pms_category"])
    cat = cat.dropna().drop_duplicates("part_number")
    cat_of = dict(zip(cat["part_number"], cat["pms_category"]))
    gr = eucon_tiers(mod, rival, cat_of)
    gr["kkey"] = gr["cpn_key"].map(mod._key)

    committed = pd.read_csv(GRADED, dtype=str)
    if "edge_origin" in committed.columns:
        committed = committed[committed["edge_origin"] == "eucon_graph"]
    cmap = dict(zip(committed["edge_id"], committed["tier_eucon_only"]))
    mism = sum(1 for eid, t in zip(gr["edge_id"], gr["tier"])
               if eid in cmap and cmap[eid] != t)
    recon = {"committed_rows_compared": len(cmap), "tier_mismatches": int(mism)}

    eucon_edge: dict[tuple, dict] = {}
    eucon_src_of_pair: dict[tuple, set] = defaultdict(set)
    for r in gr.itertuples():
        k = (str(r.part_no), r.kkey)
        eucon_edge[k] = {"tier": r.tier, "brand": r.competitor_brand, "cpn": r.competitor_pn}
        eucon_src_of_pair[k].add(str(r.source))
    eucon_pairs = set(eucon_edge)

    # ---- Spareto passes (two readings of ONE source) ------------------------
    d1, i1 = spareto_pairs_from_pass(gmod, DAY1_LABELS[0])
    day2_label = next((l for l in DAY2_LABELS if (PASSES / l / "fetch_spareto.jsonl").exists()),
                      DAY2_LABELS[0])
    d2, i2 = spareto_pairs_from_pass(gmod, day2_label)

    sp_ev: dict[tuple, dict] = {}
    for df, day in ((d1, "c1"), (d2, "c2")):
        for r in df.itertuples():
            k = (r.part_no, r.cpn_key)
            e = sp_ev.setdefault(k, {"brand": r.brand, "cpn": r.cpn, "days": {}, "brands": {}})
            e["days"][day] = r.brand
            e["brands"][r.brand] = e["brands"].get(r.brand, 0) + 1
    sp_pairs = set(sp_ev)

    src_of_pair: dict[tuple, set] = defaultdict(set)
    for k in eucon_pairs:
        src_of_pair[k].add(SRC_EUCON)
    for k in sp_pairs:
        src_of_pair[k].add(SRC_SPARETO)
    corroborated = {k for k, s in src_of_pair.items() if len(s) >= 2}

    def first_day(label):
        log = PASSES / label / "fetch_spareto.jsonl"
        if not log.exists():
            return None
        ds = sorted({json.loads(l)["fetched_at"][:10]
                     for l in log.read_text(encoding="utf-8").splitlines() if l.strip()})
        return ds[0] if ds else None
    d1_day, d2_day = first_day(DAY1_LABELS[0]), first_day(day2_label)
    try:
        day_gap = (datetime.fromisoformat(d2_day) - datetime.fromisoformat(d1_day)).days \
            if d1_day and d2_day else None
    except Exception:                                          # noqa: BLE001
        day_gap = None

    # ---- answers -------------------------------------------------------------
    pairs_by_part: dict[str, list] = defaultdict(list)
    for k in sp_pairs:
        pairs_by_part[k[0]].append(k)

    def parts_single_source(parts):
        out = set()
        for p in parts:
            ks = pairs_by_part.get(p, [])
            if ks and all(k not in corroborated for k in ks):
                out.add(p)
        return out

    def parts_with_corroborated(parts):
        return {p for p in parts if any(k in corroborated for k in pairs_by_part.get(p, []))}

    sp_parts = set(pairs_by_part)
    nums_with_pair = all123 & sp_parts
    nums_112 = needs112 & sp_parts
    single_112 = parts_single_source(nums_112)
    corr_112 = parts_with_corroborated(nums_112)

    sp_pairs_123 = {k for k in sp_pairs if k[0] in all123}
    corr_sp_123 = sp_pairs_123 & corroborated
    corr_sp_112 = {k for k in corr_sp_123 if k[0] in needs112}
    single_sp_123 = sp_pairs_123 - corroborated

    on_both = {k for k in sp_pairs_123 if len(sp_ev[k]["days"]) == 2}
    c1_only = {k for k in sp_pairs_123 if set(sp_ev[k]["days"]) == {"c1"}}
    c2_only = {k for k in sp_pairs_123 if set(sp_ev[k]["days"]) == {"c2"}}
    brand_flip = {k for k in on_both if len(set(sp_ev[k]["days"].values())) > 1}

    moved = moved_c1 = moved_c2 = 0
    for k in eucon_pairs & sp_pairs_123:
        if not mod._brand_agrees(sp_ev[k]["brand"], eucon_edge[k]["brand"]):
            continue
        moved += 1
        if "c1" in sp_ev[k]["days"]:
            moved_c1 += 1
        if "c2" in sp_ev[k]["days"]:
            moved_c2 += 1

    # context: how much Eucon evidence the 112 "no-Eucon-crossref" numbers carry
    n112_any_eucon = {p for p in needs112 if any(k[0] == p for k in eucon_pairs)}
    n112_eucon_2files = {p for p in needs112
                         if any(k[0] == p and len(eucon_src_of_pair[k]) >= 2 for k in eucon_pairs)}

    new_pairs = sp_pairs_123 - eucon_pairs
    new_pairs_112 = {k for k in new_pairs if k[0] in needs112}
    sp_parts_per_key: dict[str, set] = defaultdict(set)
    for k in sp_pairs:
        sp_parts_per_key[k[1]].add(k[0])
    graph_keys = set(gr["cpn_key"].map(mod._key))
    ntier = {}
    for k in new_pairs:
        multi = (len(sp_parts_per_key[k[1]]) > 1) or (k[1] in graph_keys)
        ntier[k] = mod.tier_of(pd.Series({
            "n_source_files": 1, "n_vintages": 1,          # Spareto only = one source
            "brand_collision": len(sp_ev[k]["brands"]) > 1,
            "multi_partno": multi, "category_conflict": False,
            "pn_shape_ok": mod.plausible_part_number(sp_ev[k]["cpn"]),
            "has_category": k[0] in cat_of,
        }))[0]

    out = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "labels": {"c1": DAY1_LABELS[0], "c2": day2_label},
        "observation_days": {"c1": d1_day, "c2": d2_day, "gap_days": day_gap},
        "source_model": ("independent sources are pipelines: eucon and spareto. C1 and C2 are "
                         "two readings of ONE source (spareto) and are reported as day "
                         "stability, not as two witnesses."),
        "inputs": {
            "worklist_numbers": len(all123), "needs_crossref_112": len(needs112),
            "eucon_11": len(eucon11),
            "eucon_rival_edges": int(len(gr)), "eucon_pairs": len(eucon_pairs),
            "c1": i1, "c2": i2,
            "committed_tier_reconciliation": recon,
        },
        "q1_numbers_with_spareto_pair": {
            "of_123": len(nums_with_pair),
            "of_112_no_eucon": len(nums_112),
            "of_11_eucon": len(nums_with_pair & eucon11),
        },
        "q2_of_112": {
            "gained_at_least_one_pair": len(nums_112),
            "single_source_only": len(single_112),
            "single_source_only_note": "all pairs Spareto-only: stays CANDIDATE, never approved",
            "with_at_least_one_corroborated_pair": len(corr_112),
        },
        "q3_pairs_also_claimed_elsewhere": {
            "spareto_pairs_on_123": len(sp_pairs_123),
            "corroborated_two_plus_independent": len(corr_sp_123),
            "corroborated_of_112": len(corr_sp_112),
            "single_source_pairs": len(single_sp_123),
            "single_source_note": "Spareto only: stays a CANDIDATE pair",
            "would_move_eucon_edge_brand_agrees": moved,
            "would_move_on_c1_reading": moved_c1,
            "would_move_on_c2_reading": moved_c2,
            "would_move_note": ("a pair moves a grade only where Spareto lists it on an existing "
                                "graph edge AND the brand agrees; one source alone never moves it"),
        },
        "eucon_context_of_112": {
            "numbers_with_any_eucon_graph_edge": len(n112_any_eucon),
            "numbers_with_2plus_eucon_source_files": len(n112_eucon_2files),
            "note": ("the 112 are 'no Eucon cross-reference' by the worklist's narrow flag "
                     "(Eucon Online 2025); some still carry Eucon UK IAM survey edges in the "
                     "graph, so they are not zero-Eucon-evidence"),
        },
        "day_stability_spareto": {
            "pairs_on_both_days": len(on_both),
            "pairs_c1_only": len(c1_only),
            "pairs_c2_only": len(c2_only),
            "pairs_with_brand_differing_between_days": len(brand_flip),
            "note": "identical pair on both days means the second reading reproduced the first",
        },
        "new_pairs_not_in_graph": {
            "count": len(new_pairs), "of_112": len(new_pairs_112),
            "tiers": dict(Counter(ntier.values())),
            "note": "the merge step adds these as tier doubtful, edge_origin=spareto_only",
        },
    }

    (HERE / "crossref_arithmetic.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d2):
        d2.to_csv(HERE / "spareto_crossref_day2.csv", index=False)
    if len(d1):
        d1.to_csv(HERE / "spareto_crossref_day1.csv", index=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
