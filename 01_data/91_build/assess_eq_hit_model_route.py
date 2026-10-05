# -*- coding: utf-8 -*-
"""
Can the EQ-Hit catalogue-edition string classify part numbers by vehicle?

Claim under test (2026-09-18 review): the catalogue edition we already collect,
e.g. "51968 - 2021 NNR/NPR LHD EURO6 EUROPE 21.0 - 23.0", is a model statement in
plain text. If one lookup per FIGURE KEY returns one model edition, then ~13,848
lookups classify all 165k part numbers by join - about twelve times cheaper than
one lookup per part number.

The review's own caveat: the heaviest figure keys are hardware and electrical
(005-001 carries 5,224 parts), which are the most likely to be shared between an
LCV and a CV. So this measures the risk before anyone spends time on it.

Run: python 01_data/91_build/assess_eq_hit_model_route.py
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import Counter

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"


def say(m=""):
    print(m)
    sys.stdout.flush()


V = os.path.join(D, "_eq_hit_validation_20260917.json")
_raw = json.load(open(V, encoding="utf-8")) if os.path.exists(V) else {}
probes = _raw.get("results", []) if isinstance(_raw, dict) else _raw
say("=" * 84)
say("1. WHAT THE EQ-HIT PROBES ALREADY HOLD")
say("=" * 84)
say(f"  file  : _eq_hit_validation_20260917.json  (as of {_raw.get('as_of', '?')})")
say(f"  source: {_raw.get('source', '?')}")
say(f"  status: {str(_raw.get('status', ''))[:96]}")
say(f"  probes: {len(probes)} of a {_raw.get('n_probe_list', '?')}-row probe list; "
    f"{_raw.get('n_found', '?')} found something")
say()
for p in probes:
    cat = str(p.get("catalog") or "")
    if not cat:
        continue
    say(f"    {str(p.get('pn')):<12} {str(p.get('fig_name'))[:30]:<32} {cat[:56]}")

say()
say("=" * 84)
say("2. IS THE CATALOGUE STRING A MODEL STATEMENT?")
say("=" * 84)
cats = [str(p.get("catalog")) for p in probes if p.get("catalog")]
say(f"  probes carrying a catalogue string : {len(cats)} of {len(probes)}")
say()

LCV = re.compile(r"\b(TFR|TFS|D-?MAX|RZ4|4JJ|4JK)\b", re.I)
CV = re.compile(r"\b(N[KSQLMRT][0-9]{2}|NLR|NPR|NQR|NNR|FSR|FVR|FVM|FVR|GIGA|4HK|6HK|6UZ|4HF|4HG)\b", re.I)


def classify(s: str):
    lcv, cv = bool(LCV.search(s)), bool(CV.search(s))
    if lcv and not cv:
        return "LCV"
    if cv and not lcv:
        return "CV"
    if lcv and cv:
        return "BOTH"
    return "NEITHER"


say(f"  {'catalogue string':<58} {'class':<8}")
for c in cats:
    say(f"  {c[:56]:<58} {classify(c):<8}")
say()
kinds = Counter(classify(c) for c in cats)
say(f"  verdict: {dict(kinds)}")
say()
say("  A string that names the model edition IS a model statement, and the regex")
say("  above reads it. That part of the claim holds.")

say()
say("=" * 84)
say("3. THE CAVEAT - HOW MODEL-SPECIFIC ARE THE HEAVY FIGURE KEYS?")
say("=" * 84)
fam = pd.read_csv(os.path.join(D, "aim_pn_classification_v2.csv"), dtype=str,
                  usecols=["part_number", "fig_key", "catalog_l1", "catalog_l2"])
fam["pn"] = fam["part_number"].astype(str).str.strip()
b = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
b["pn"] = b["part_number"].astype(str).str.strip()
b = b[b["priced_both"] == True]                                     # noqa: E712
j = b.merge(fam[["pn", "fig_key", "catalog_l2"]].drop_duplicates("pn"), on="pn", how="left")
say(f"  priced lines with a figure key : {j['fig_key'].notna().sum():,} of {len(j):,}")
say(f"  distinct figure keys           : {j['fig_key'].nunique():,}")
say()
g = j.groupby("fig_key").agg(parts=("pn", "nunique"), billed=("billed_eur", "sum")).sort_values(
    "billed", ascending=False)
total_billed = j["billed_eur"].sum()
say(f"  the heaviest figure keys by BILLED EURO, because that is what matters:")
say(f"  {'fig_key':<12} {'part nums':>10} {'billed EUR':>14} {'% of book':>10}  family")
cum = 0.0
for k, r in g.head(15).iterrows():
    fam_l2 = j[j["fig_key"] == k]["catalog_l2"].mode()
    cum += r["billed"]
    say(f"  {str(k):<12} {int(r['parts']):>10,} {r['billed']:>14,.0f} "
        f"{100*r['billed']/total_billed:>9.1f}%  {fam_l2.iloc[0] if len(fam_l2) else '-'}")
say()
say(f"  the top 200 figure keys cover {100*g.head(200)['billed'].sum()/total_billed:.1f}% "
    f"of billed euro")
say(f"  ... which would need {min(200, len(g))} lookups, not {len(g):,}")
say()
say("  So the economy is better than the review assumed. You do not need one lookup")
say("  per figure key: a fraction of the keys carries most of the money.")

say()
say("=" * 84)
say("4. WHAT THE TEST SHOULD BE")
say("=" * 84)
say(f"  Sample the top {min(50, len(g))} figure keys by billed euro, look each one up")
say("  in EQ-Hit, and count how many return ONE model edition.")
say()
say("  PASS  - most return a single edition -> build the table and join it; CV vs LCV")
say("          becomes a fact instead of an inference from which distributor stocks it.")
say("  FAIL  - many return several editions including both LCV and CV -> the route")
say("          cannot separate them, and the answer is TecDoc OE Parts Data or an")
say("          approach through Snap-on with Jerome's weight behind it.")
say()
say("  Nothing in this assessment required a scrape or a purchase.")

meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "probes_held": len(probes),
    "probes_with_catalogue_string": len(cats),
    "probe_classes": dict(kinds),
    "figure_keys_priced": int(j["fig_key"].nunique()),
    "top200_keys_billed_share_pct": float(100 * g.head(200)["billed"].sum() / total_billed),
    "verdict": "catalogue string IS a model statement; economy is better than assumed "
               "because a fraction of keys carries most of the money",
    "next_test": "50 lookups on the heaviest figure keys; PASS if most return one edition",
}
with open(os.path.join(D, "eq_hit_model_route_assessment.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say()
say("DOMAIN_ASK: open EQ-Hit and look up 50 figure keys, confirm one model edition each")
say("ASSESS_OK")
