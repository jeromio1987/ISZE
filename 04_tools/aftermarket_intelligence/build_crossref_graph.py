# -*- coding: utf-8 -*-
"""
Task card 2.1 — the cross-reference GRAPH, and the fetch-ready seed list with evidence.

Input : 04_tools/aftermarket_intelligence/state/match_index.csv  (built 2026-09-24)
Output: 04_tools/aftermarket_intelligence/state/
          crossref_edges.parquet     one edge per Isuzu number x competitor number x source
          crossref_edges.csv         same, readable
          evidence_seed.csv          fetch-ready: competitor number + brand + the Isuzu parts it
                                     fits + how many INDEPENDENT sources agree + the price
          CROSSREF_GRAPH_REPORT.md   build log

The acceptance rule for 2.1 is "every edge has a source and a date". That is enforced here: an edge
without both is refused and counted.

Two things are deliberately separate in this output:

  EDGES      the graph. Isuzu number <-> competitor number, with provenance. No judgement.
  EVIDENCE   the fetch seed. Ranked by how many independent sources agree, NOT by what we bill.
             Our billed value says nothing about whether a rival part is on a shelf.

THE SPACING TRAP (found 2026-09-24): competitor numbers are written with and without spaces and
dots - 'F 026 402 115' and 'F026402115' are the same Bosch number. 174 numbers in the index exist
in more than one written form. Counting sources on the written form UNDERSTATES agreement; counting
sources on the loose form INFLATES it. Both readings are kept, and the report says which is which.

Nothing is fetched. Nothing is written outside this folder.

Run: python 04_tools/aftermarket_intelligence/build_crossref_graph.py
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
STATE.mkdir(parents=True, exist_ok=True)

MATCH = STATE / "match_index.csv"
E_PARQ = STATE / "crossref_edges.parquet"
E_CSV = STATE / "crossref_edges.csv"
SEED = STATE / "evidence_seed.csv"
REPORT = STATE / "CROSSREF_GRAPH_REPORT.md"

log = []


def compact(x):
    """Loose form: the same number written two ways collapses to one key."""
    return re.sub(r"[\s.\-/]", "", str(x)).upper()


def tight(x):
    """Written form, but whitespace collapsed - the conservative key."""
    return re.sub(r"\s+", " ", str(x)).strip().upper()


mi = pd.read_csv(MATCH, dtype=str)
log.append(f"- match index rows read: {len(mi)}")

# ------------------------------------------------ edges (the graph)

e = mi.copy()
e["cpn_key"] = e.competitor_pn.map(compact)
e["cpn_written"] = e.competitor_pn.map(tight)

# drop rows that are not an Isuzu <-> rival relationship
# FIX 2026-09-24: this used to test competitor_brand_norm against ("Isuzu BVP", "Isuzu (our"), but the
# normalised brand reads "OUR OWN NUMBER" / "OUR OWN VALUE LINE", so nothing ever matched. The 237
# "Eucon March RRP" rows (our own number, our own retail) went into the ratio model as a competitor.
# Test the raw brand AND the normalised brand, and treat our own number written as the rival number
# as our own line whatever the brand says.
NOT_A_RIVAL = ("ISUZU BVP", "ISUZU (OUR", "OUR OWN")
e["is_our_own_line"] = (
    e.competitor_brand.fillna("").str.upper().str.startswith(NOT_A_RIVAL)
    | e.competitor_brand_norm.fillna("").str.upper().str.startswith(NOT_A_RIVAL)
    | (e.competitor_pn.map(compact) == e.part_no.map(compact))
).astype(int)
e["is_peer_carrier"] = (e.source.str.startswith("Peer carrier")).astype(int)

# ACCEPTANCE: every edge carries a source and a date
before = len(e)
e = e[e.source.notna() & (e.source.str.strip() != "")]
e = e[e.source_vintage.notna() & (e.source_vintage.str.strip() != "")]
refused = before - len(e)
log.append(f"- edges refused for a missing source or date: {refused}")

e["edge_id"] = (e.part_no + "|" + e.cpn_key + "|" + e.source + "|"
                + e.country.fillna("")).map(lambda s: hashlib.md5(s.encode()).hexdigest()[:16])
e = e.drop_duplicates("edge_id")

# SOURCE FAMILY - one family is one witness. The Eucon files are one vendor re-cutting one database, so
# four Eucon files are ONE witness, not four. Our own catalogue and the peer-carrier map point back at
# us and confirm nothing about a rival part: weight 0. An unmapped source stops the build, so a new
# file cannot slip in as an extra "independent" witness by accident.
SOURCE_FAMILY = {
    "Eucon Online extract": ("EUCON", 1),
    "Eucon Online extract (additional no.)": ("EUCON", 1),
    "Eucon March online": ("EUCON", 1),
    "Eucon March RRP": ("EUCON", 1),
    "Eucon crossref (PartsPool)": ("EUCON", 1),
    "Eucon UK IAM survey": ("UK_WORKSHOP_SURVEY", 1),
    "Isuzu genuine to BVP catalogue": ("OWN_CATALOGUE", 0),
    "Peer carrier number (Eucon OEM survey)": ("PEER_CARRIER", 0),
}
unmapped = sorted(set(e.source) - set(SOURCE_FAMILY))
if unmapped:
    raise SystemExit(f"source(s) with no family in SOURCE_FAMILY - add them before building: {unmapped}")
e["source_family"] = e.source.map(lambda s: SOURCE_FAMILY[s][0])
e["witness_weight"] = e.source.map(lambda s: SOURCE_FAMILY[s][1])
# the UK survey is a Eucon product too. It counts as its own family because it is a workshop survey,
# not a catalogue re-cut - that is a judgement, and the report says so.

cols = ["edge_id", "part_no", "competitor_brand", "competitor_brand_norm", "competitor_pn",
        "cpn_key", "cpn_written", "source", "source_family", "witness_weight", "source_vintage",
        "has_competitor_price",
        "competitor_price", "currency", "vat", "price_type", "country", "note",
        "is_our_own_line", "is_peer_carrier", "cpn_brand_collision", "cpn_multi_partno"]
e = e[cols].sort_values(["part_no", "cpn_key", "source"])
try:
    e.to_parquet(E_PARQ, index=False)
    wrote_parquet = True
except Exception as ex:                                     # pyarrow may be absent
    wrote_parquet = False
    log.append(f"- parquet not written ({type(ex).__name__}); CSV only")
e.to_csv(E_CSV, index=False, encoding="utf-8")
log.append(f"- edges written: {len(e)}"
           + (f" (parquet + csv)" if wrote_parquet else " (csv only)"))
log.append(f"- distinct Isuzu numbers on an edge: {e.part_no.nunique()}")
log.append(f"- distinct competitor numbers: {e.cpn_key.nunique()}")
log.append(f"- of those, already carrying a price: "
           f"{e[e.has_competitor_price.astype(int) == 1].cpn_key.nunique()}")

# ------------------------------------------------ evidence seed (the fetch list)

r = e[(e.is_our_own_line == 0) & (e.is_peer_carrier == 0)].copy()
log.append("")
log.append(f"- rival edges only (our own BVP line and the peer-carrier map excluded): {len(r)}")

g = r.groupby("cpn_key").agg(
    n_sources=("source", "nunique"),
    n_witnesses=("source_family", lambda s: s[r.loc[s.index, "witness_weight"] == 1].nunique()),
    families=("source_family", lambda s: "|".join(sorted(set(s)))),
    n_brands=("competitor_brand_norm", "nunique"),
    n_part_numbers=("part_no", "nunique"),
    n_countries=("country", lambda s: len({x for x in s.dropna() if str(x).strip()})),
    n_price_rows=("has_competitor_price", lambda s: int(s.astype(int).sum())),
    has_price=("has_competitor_price", lambda s: int(s.astype(int).any())),
    written_forms=("cpn_written", "nunique"),
    brands=("competitor_brand_norm", lambda s: "|".join(sorted(set(s.dropna())))),
    sources=("source", lambda s: "|".join(sorted(set(s.dropna())))),
    newest_source=("source_vintage", "max"),
).reset_index()

# sources BEFORE normalising the number, for the report
gw = r.groupby("cpn_written").source.nunique()
n_inflated = int((gw >= 1).sum())
log.append(f"- competitor numbers, written form as the key: {r.cpn_written.nunique()}")
log.append(f"- competitor numbers, spelling normalised      : {g.cpn_key.nunique()}")
log.append(f"- numbers written in more than one form       : {int((g.written_forms > 1).sum())}")

# how many independent sources could have seen this number at all, per spelling-normalised key
# ranked on INDEPENDENT witnesses first; file count only breaks ties
g = g.sort_values(["n_witnesses", "n_sources", "n_brands", "n_part_numbers"],
                  ascending=False).reset_index(drop=True)
g["rank_by_evidence"] = g.index + 1
g["confirmed_by_3plus"] = (g.n_sources >= 3).astype(int)        # FILES - kept for continuity only
g["confirmed_by_2plus"] = (g.n_sources >= 2).astype(int)        # FILES - kept for continuity only
g["single_source"] = (g.n_sources == 1).astype(int)
g["witnessed_by_2plus"] = (g.n_witnesses >= 2).astype(int)      # the honest count

# the Isuzu parts it fits, biggest first
tops = r.groupby("cpn_key").apply(
    lambda d: "|".join(sorted(set(d.part_no))[:5]), include_groups=False)
g["isuzu_parts"] = g.cpn_key.map(tops)

g[["cpn_key", "brands", "n_witnesses", "families", "n_sources", "n_brands", "n_part_numbers",
   "n_countries", "has_price", "n_price_rows", "written_forms", "witnessed_by_2plus",
   "confirmed_by_2plus", "confirmed_by_3plus", "single_source",
   "rank_by_evidence", "sources", "newest_source", "isuzu_parts"]].to_csv(
    SEED, index=False, encoding="utf-8")
log.append(f"- evidence seed rows written: {len(g)}")
log.append(f"  - 1 source FILE only      : {int(g.single_source.sum())}")
log.append(f"  - 2 source FILES or more  : {int(g.confirmed_by_2plus.sum())}")
log.append(f"  - 3 source FILES or more  : {int(g.confirmed_by_3plus.sum())}")
log.append(f"  - INDEPENDENT witnesses (source families, own catalogue and peer map count 0):")
for k, v in g.n_witnesses.value_counts().sort_index().items():
    log.append(f"      {k} witness(es): {v}")
log.append(f"  - already carry a price: {int(g.has_price.sum())}")

# ------------------------------------------------ check: brand names that are probably one brand
# Two normalised brands where one name contains the other AND they share at least one competitor
# number are almost certainly one brand written twice ('FEBI' / 'FEBI BILSTEIN'). Listed, not merged:
# a merge is a judgement a person signs off.
bn = r.groupby("competitor_brand_norm").cpn_key.agg(set)
names = sorted(bn.index, key=len)
pairs = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if len(a) >= 3 and re.search(rf"\b{re.escape(a)}\b", b):
            shared = bn[a] & bn[b]
            pairs.append(dict(short=a, long=b, shared_numbers=len(shared),
                              numbers_short=len(bn[a]), numbers_long=len(bn[b]),
                              example=next(iter(shared), "")))
bp = pd.DataFrame(pairs, columns=["short", "long", "shared_numbers", "numbers_short",
                                  "numbers_long", "example"])
bp = bp.sort_values("shared_numbers", ascending=False)
bp.to_csv(STATE / "check_brand_alias_candidates.csv", index=False, encoding="utf-8")
log.append("")
log.append("### check: brand written two ways")
log.append(f"- brand pairs where one name contains the other: {len(bp)}; "
           f"of which sharing a competitor number (near-certain alias): {int((bp.shared_numbers > 0).sum())}")
log.append("- listed in check_brand_alias_candidates.csv - NOT merged; merging needs sign-off")

# ------------------------------------------------ check: matches that a newer Eucon cut dropped
# If a newer Eucon file covers the same Isuzu part but no longer lists a rival number an older one
# did, the older match may have been withdrawn. Union-merging keeps it silently.
eu = e[(e.source_family == "EUCON") & (e.is_our_own_line == 0)]
vint = eu.groupby("source").source_vintage.first().sort_values()
dropped = []
for older, v_old in vint.items():
    newer = [s for s, v in vint.items() if v > v_old]
    if not newer:
        continue
    newest_cover = eu[eu.source.isin(newer)]
    covered_parts = set(newest_cover.part_no)
    newer_pairs = set(zip(newest_cover.part_no, newest_cover.cpn_key))
    old = eu[(eu.source == older) & eu.part_no.isin(covered_parts)]
    for pn, ck, br in set(zip(old.part_no, old.cpn_key, old.competitor_brand_norm)):
        if (pn, ck) not in newer_pairs:
            dropped.append(dict(part_no=pn, cpn_key=ck, brand=br, listed_in=older,
                                listed_vintage=v_old, absent_from="|".join(newer)))
dr = pd.DataFrame(dropped, columns=["part_no", "cpn_key", "brand", "listed_in", "listed_vintage",
                                    "absent_from"])
dr.to_csv(STATE / "check_eucon_dropped_matches.csv", index=False, encoding="utf-8")
log.append("")
log.append("### check: matches a newer Eucon file no longer lists (same Isuzu part still covered)")
log.append(f"- such matches: {len(dr)} (distinct Isuzu parts {dr.part_no.nunique()}) - "
           "check_eucon_dropped_matches.csv. Not removed: absence may be a narrower cut, not a "
           "withdrawal. Put five of them into the next manual check.")

# ------------------------------------------------ report with the money attached

t = pd.read_csv(ROOT / "04_tools/delegation/state/refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = t.part_no.astype(str).str.strip()
t["billed_eur_t12m"] = pd.to_numeric(t.billed_eur_t12m, errors="coerce")
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, t.billed_eur_t12m))


def reach(sub):
    pns = set(r[r.cpn_key.isin(set(sub.cpn_key))].part_no)
    val = sum(billed.get(p, 0) or 0 for p in pns)
    ta = [p for p in pns if tier.get(p) == "A"]
    return len(pns), val, len(ta), sum(billed.get(p, 0) or 0 for p in ta)


for label, sub in [("all rival numbers", g),
                   ("2+ sources", g[g.n_sources >= 2]),
                   ("3+ sources", g[g.n_sources >= 3]),
                   ("2+ INDEPENDENT witnesses", g[g.n_witnesses >= 2])]:
    n, val, na, vala = reach(sub)
    log.append("")
    log.append(f"### {label}")
    log.append(f"- competitor numbers: {len(sub)}")
    log.append(f"- Isuzu part numbers reached: {n} of {len(t)}")
    log.append(f"- billed value of those parts: EUR {val:,.0f}")
    log.append(f"- of which Tier A: {na} parts, EUR {vala:,.0f}")

# overlap with what we can already price, so we do not re-buy what we hold
already = set(e[e.has_competitor_price.astype(int) == 1].cpn_key)
g["already_priced"] = g.cpn_key.isin(already).astype(int)
need = g[(g.n_sources >= 2) & (g.already_priced == 0)]
n, val, na, vala = reach(need)
log.append("")
log.append("### what is actually worth fetching")
log.append(f"- 2+ source numbers with NO price yet: {len(need)}")
log.append(f"- they reach {n} Isuzu parts, EUR {val:,.0f} billed; Tier A {na} parts, EUR {vala:,.0f}")

(REPORT).write_text(
    "# Cross-reference graph — build report (task card 2.1)\n\n"
    f"Built {datetime.now(timezone.utc).isoformat(timespec='seconds')} by "
    "`04_tools/aftermarket_intelligence/build_crossref_graph.py`\n\n"
    "Acceptance rule for 2.1: every edge carries a source and a date, or it is refused.\n\n"
    + "\n".join(log) + "\n\n"
    "## Files\n"
    "- `crossref_edges.parquet` / `.csv` — the graph, one edge per Isuzu number x competitor "
    "number x source x country\n"
    "- `evidence_seed.csv` — the fetch list, ranked by independent confirmation\n\n"
    "## Caution\n"
    "`n_sources` counts distinct FILES, not independent verifications. `n_witnesses` counts SOURCE "
    "FAMILIES: all Eucon catalogue files are one witness; our own catalogue and the peer-carrier map "
    "count zero. The UK workshop survey is also a Eucon product; it is counted as its own family "
    "because it was collected by survey, not re-cut from the catalogue. That is a judgement, not a "
    "proven fact. Rank on `n_witnesses`.\n",
    encoding="utf-8")

print("\n".join(log))
print("\nwrote:", E_PARQ.name if wrote_parquet else "(no parquet)", E_CSV.name, SEED.name, REPORT.name)
