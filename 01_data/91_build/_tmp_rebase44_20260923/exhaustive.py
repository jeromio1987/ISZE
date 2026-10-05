"""Exhaustive NMR membership: every column of every source file that carries a part number.

This is the "check each of the 44 for a hidden NMR token in any of its code columns —
including any column you have not looked at" step, done by brute force rather than by
choosing columns. Read only.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"
NMR = re.compile(r"\bNMR(?:85)?\b")
key = lambda s: str(s).strip().lstrip("0") or "0"
pd.set_option("display.width", 300)
pd.set_option("display.max_colwidth", 100)


def short(b):
    return b.split("_")[0] if b else ""


def np_(raw):
    return "|".join(sorted(short(t) for t in str(raw).split("|") if t)) if raw else ""


def nl(raw):
    if not raw or raw == "[]":
        return ""
    try:
        return "|".join(sorted(str(t) for t in ast.literal_eval(raw) if t))
    except (ValueError, SyntaxError):
        return "PARSE_ERROR"


tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")

m = tc[["pn", "band_list", "eur", "category"]].merge(
    ap[["pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes",
        "band_status", "eur"]], on="pn", suffixes=("_tc", "_ap"), how="inner")
m["ap_short"] = m.n_series_bands.map(np_)
m["tc_short"] = m.band_list.map(nl)
diff = m[m.ap_short != m.tc_short].copy()
diff["k"] = diff.pn.map(key)

APCOLS = ["codes_named", "parked_codes", "unresolved_codes", "n_series_bands", "band_status"]
brief44 = diff[~diff[APCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1)].copy()
print(f"brief's 44 (no NMR in the mapping's own code columns): {len(brief44)}")

# ---- gather EVERY mention of each PN from every file that has one -------------------------
print()
print("building the exhaustive mention index ...")
mentions: dict[str, list[tuple[str, str, str]]] = {}

pns = set(brief44.k)


def add(df, pncol, label):
    if pncol not in df.columns:
        return
    df = df.copy()
    df["_k"] = df[pncol].map(key)
    sub = df[df["_k"].isin(pns)]
    for _, r in sub.iterrows():
        for c in df.columns:
            if c in ("_k", pncol):
                continue
            v = str(r[c])
            if v and v.lower() not in ("nan", "none"):
                mentions.setdefault(r["_k"], []).append((label, c, v))


for name, pncol in (("vehicle_band_applicability(frozen)", "pn"),
                    ("tonnage_capable(frozen)", "pn")):
    pass
add(ap, "pn", "vehicle_band_applicability")
add(tc, "pn", "tonnage_capable")
for fn in ("epc_decode_nseries_banded.csv", "epc_decode_batch1_banded_20260919.csv",
           "vehicle_family_bands.csv", "epc_decode_worklist.csv",
           "genuine_bvp_crossref.csv", "series_to_tonnage.csv",
           "tonnage_capable_categories.csv", "_band_moves.csv",
           "tonnage_missing_families_scope_20260922.csv"):
    f = DER / fn
    if not f.exists():
        continue
    d = pd.read_csv(f, dtype=str, low_memory=False).fillna("")
    for cand in ("pn", "part_number", "genuine_pn", "bvp_pn", "series"):
        if cand in d.columns:
            add(d, cand, fn)
for fn in ("epc_decode_batch2_20260919.json",):
    f = DER / fn
    if f.exists():
        for r in json.loads(f.read_text(encoding="utf-8")):
            k = key(r.get("pn", ""))
            if k in pns:
                for kk, vv in r.items():
                    mentions.setdefault(k, []).append((fn, kk, str(vv)))
f = ROOT / "01_data" / "91_build" / "_band_moves.csv"
if f.exists():
    add(pd.read_csv(f, dtype=str, low_memory=False).fillna(""), "pn", "_band_moves(build)")

print(f"indexed mentions for {len(mentions)} of the {len(brief44)} part numbers")
print()
print("=" * 118)
print("EVERY MENTION THAT CONTAINS NMR OR NMR85")
print("=" * 118)
hits = []
for k, lst in sorted(mentions.items()):
    for label, col, v in lst:
        if NMR.search(v):
            hits.append((k, label, col, v))
hits_df = pd.DataFrame(hits, columns=["pn", "file", "column", "value"])
if len(hits_df):
    print(hits_df.to_string(index=False))
else:
    print("  (none)")
print()
carriers = sorted(set(hits_df.pn)) if len(hits_df) else []
print(f"part numbers with a hidden NMR mention : {len(carriers)}")
print(f"  {carriers}")
print()
print(f"part numbers with NO NMR mention anywhere : {len(brief44) - len(carriers)}")

# also list, for the carriers, what the published band file says vs the mapping
ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
epi = ep.set_index(ep.pn.map(key))
rows = []
for k in carriers:
    r = brief44[brief44.k == k].iloc[0]
    if k in epi.index:
        e = epi.loc[k]
        if isinstance(e, pd.DataFrame):
            e = e.iloc[0]
        rows.append({"pn": k, "in_file": "yes", "file_band": np_(e["tonnage_band"]),
                     "mapping_band": r.ap_short, "needs_rebase": np_(e["tonnage_band"]) != r.ap_short,
                     "eur_file": e["eur_all_years"], "eur_mapping": r.eur_ap})
    else:
        rows.append({"pn": k, "in_file": "no", "file_band": "", "mapping_band": r.ap_short,
                     "needs_rebase": "", "eur_file": "", "eur_mapping": r.eur_ap})
print()
print(pd.DataFrame(rows).to_string(index=False))

free = brief44[~brief44.k.isin(carriers)]
print()
print("=" * 118)
print(f"THE TRUE FREE SET — {len(free)} part numbers, no NMR anywhere")
print("=" * 118)
print(f"  euro (corrected mapping basis): EUR {pd.to_numeric(free.eur_ap).sum():,.2f}")
rows = []
for _, r in free.iterrows():
    if r.k in epi.index:
        e = epi.loc[r.k]
        if isinstance(e, pd.DataFrame):
            e = e.iloc[0]
        rows.append({"pn": r.k, "in_file": "yes", "file_band": np_(e["tonnage_band"]),
                     "mapping_band": r.ap_short, "already_correct": np_(e["tonnage_band"]) == r.ap_short,
                     "eur": r.eur_ap})
    else:
        rows.append({"pn": r.k, "in_file": "no", "file_band": "", "mapping_band": r.ap_short,
                     "already_correct": "", "eur": r.eur_ap})
fr = pd.DataFrame(rows)
print(fr.to_string(index=False))
print()
print(f"  in the published band file and already correct : "
      f"{int(fr.already_correct.eq(True).sum())}")
print(f"  in the published band file and needing re-base : "
      f"{int(fr.already_correct.eq(False).sum())}")
print(f"  not in the published band file at all          : "
      f"{int(fr.in_file.eq('no').sum())}")

brief44_out = brief44[["pn", "category", "tc_short", "ap_short", "eur_ap", "codes_named",
                       "parked_codes"]].rename(columns={
    "pn": "pn", "category": "pms_category", "tc_short": "legacy_published_band",
    "ap_short": "corrected_band", "eur_ap": "eur_corrected_mapping_basis"})
brief44_out["carries_hidden_NMR"] = brief44_out.pn.map(key).isin(carriers)
brief44_out.to_csv(SCR / "_brief44_audit.csv", index=False)
print(f"\n  written: _brief44_audit.csv ({len(brief44_out)} rows)")
