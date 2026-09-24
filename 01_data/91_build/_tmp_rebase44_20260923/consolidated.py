"""Consolidated, read-only verification for the 44 re-base brief.

Produces every figure the note has to state:
  * the three groups (44 / 132 / 176) and the corrected ones
  * the exclusive_band = 3.5t_N35 count on the 16 rows
  * whether the requested target file contains any of the 44 at all
  * the blast radius on nseries_tonnage_evolution.csv / .meta.json
  * the published exclusive-attribution share, derived read-only
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"
NMR = re.compile(r"\bNMR(?:85)?\b")
key = lambda s: str(s).strip().lstrip("0") or "0"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
pd.set_option("display.width", 300)
pd.set_option("display.max_colwidth", 95)


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
tc_live = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str).fillna("")
ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")
ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
evo = pd.read_csv(DER / "nseries_tonnage_evolution.csv", dtype=str).fillna("")
meta = json.loads((DER / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))

print("#" * 116)
print("A. THE THREE GROUPS, AND THE CORRECTION")
print("#" * 116)
m = tc[["pn", "band_list", "eur", "category", "exclusive_band"]].merge(
    ap[["pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes",
        "exclusive_band", "band_status", "eur"]],
    on="pn", suffixes=("_tc", "_ap"), how="inner")
m["ap_short"] = m.n_series_bands.map(np_)
m["tc_short"] = m.band_list.map(nl)
diff = m[m.ap_short != m.tc_short].copy()
same = m[m.ap_short == m.tc_short]
eur = pd.to_numeric(diff.eur_ap)
print(f"  identical  {len(same):4d}   EUR {pd.to_numeric(same.eur_ap).sum():>15,.2f}")
print(f"  different  {len(diff):4d}   EUR {eur.sum():>15,.2f}   <- the brief's 176")
print(f"  total      {len(m):4d}   EUR {pd.to_numeric(m.eur_ap).sum():>15,.2f}")

APCOLS = ["codes_named", "parked_codes", "unresolved_codes", "n_series_bands",
          "exclusive_band_ap", "band_status"]
EPCOLS = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
          "series_unresolved", "band_reason", "tonnage_band", "family"]

diff["nmr_ap"] = diff[APCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1)

# membership from EVERY primary source (EPC batch1 + batch2 editions, cross-reference, both
# derived tables, and the published band file)
b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str, low_memory=False).fillna("")
b1["k"] = b1.pn.map(key)
b1c = dict(zip(b1.k, b1.model_codes))
dec2 = {}
for r in json.loads((DER / "epc_decode_batch2_20260919.json").read_text(encoding="utf-8")):
    dec2.setdefault(key(r["pn"]), []).extend(str(m) for m in (r.get("models") or []))
xr = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False).fillna("")
xrv: dict[str, list[str]] = {}
for r in xr.itertuples():
    for pn in {key(r.genuine_pn), key(r.bvp_pn)}:
        xrv.setdefault(pn, []).append(str(r.vehicle_model))
epi = ep.set_index(ep.pn.map(key))


def primary_hits(pn: str) -> list[str]:
    out = []
    for src, label in ((b1c.get(pn, ""), "EPC-batch1"), (" ".join(dec2.get(pn, [])), "EPC-batch2"),
                       (" ".join(xrv.get(pn, [])), "crossref")):
        toks = {p.strip() for raw in re.split(r"[,\s;|]+", str(src).upper())
                for p in raw.split("/") if p.strip()}
        if any(NMR.fullmatch(t) for t in toks):
            out.append(label)
    if pn in epi.index:
        r = epi.loc[pn]
        if isinstance(r, pd.DataFrame):
            r = r.iloc[0]
        if any(NMR.search(str(r[c])) for c in EPCOLS if c in r.index):
            out.append("published-band-file")
    return out


diff["k"] = diff.pn.map(key)
diff["primary"] = diff.k.map(primary_hits)
diff["nmr_anywhere"] = diff.nmr_ap | diff.primary.map(bool)

print()
print("  membership, three ways:")
print(f"    corrected mapping's own codes_named/parked : {int(diff.nmr_ap.sum()):4d} NMR "
      f"EUR {eur[diff.nmr_ap].sum():>15,.2f}  |  neither {int((~diff.nmr_ap).sum()):4d} "
      f"EUR {eur[~diff.nmr_ap].sum():>15,.2f}    <- the brief's 132 / 44")
print(f"    published band file's series columns       : "
      f"{int(diff.primary.map(lambda v: 'published-band-file' in v).sum()):4d} NMR "
      f"|  neither {int((~diff.primary.map(lambda v: 'published-band-file' in v)).sum()):4d}")
print(f"    EVERY source (mapping + EPC + crossref + published file) : "
      f"{int(diff.nmr_anywhere.sum()):4d} NMR  EUR {eur[diff.nmr_anywhere].sum():>15,.2f}"
      f"  |  neither {int((~diff.nmr_anywhere).sum()):4d}  EUR {eur[~diff.nmr_anywhere].sum():>15,.2f}")

moved = diff[diff.nmr_ap & ~diff.nmr_ap.eq(diff.nmr_anywhere)]
print()
print(f"  >>> rows the brief calls 'no NMR' but that DO carry NMR somewhere: "
      f"{int((~diff.nmr_ap & diff.nmr_anywhere).sum())}")
print(f"      euro they carry: EUR {eur[~diff.nmr_ap & diff.nmr_anywhere].sum():,.2f}")
print()
print(diff[~diff.nmr_ap & diff.nmr_anywhere][
    ["pn", "category", "tc_short", "ap_short", "eur_ap", "codes_named", "primary"]].to_string(index=False))

print()
print(f"  corrected split: parked {int(diff.nmr_anywhere.sum())}  EUR {eur[diff.nmr_anywhere].sum():,.2f}"
      f" | free {int((~diff.nmr_anywhere).sum())}  EUR {eur[~diff.nmr_anywhere].sum():,.2f}")

free = diff[~diff.nmr_anywhere].copy()

print()
print("#" * 116)
print("B. DOES THE FILE THE BRIEF NAMES CONTAIN ANY OF THE FREE SET?")
print("#" * 116)
free["in_ep"] = free.k.isin(epi.index)
print(f"  free (no NMR anywhere)        : {len(free)}")
print(f"  of those in the published band file: {int(free.in_ep.sum())}")
agree = 0
for _, r in free[free.in_ep].iterrows():
    e = epi.loc[r.k]
    if isinstance(e, pd.DataFrame):
        e = e.iloc[0]
    if np_(e["tonnage_band"]) == r.ap_short:
        agree += 1
print(f"  of those, band already agrees with the mapping: {agree}")
print(f"  of those, band would need re-basing           : {int(free.in_ep.sum()) - agree}")

print()
print("  the whole published band file against the mapping:")
e2 = ep.copy()
e2["k"] = e2.pn.map(key)
e2["ap_short"] = e2.k.map(lambda k: np_(ap.set_index(ap.pn.map(key)).loc[k, "n_series_bands"])
                          if k in ap.set_index(ap.pn.map(key)).index else "")
e2["ep_short"] = e2.tonnage_band.map(np_)
e2["names_nmr"] = e2.apply(lambda r: any(NMR.search(str(r[c])) for c in EPCOLS if c in r.index), axis=1)
dis = e2[(e2.ap_short != "") & (e2.ep_short != e2.ap_short)]
print(f"    rows in the file                       : {len(e2)}")
print(f"    rows whose band differs from the mapping: {len(dis)}  EUR "
      f"{pd.to_numeric(dis.eur_all_years).sum():,.2f}")
print(f"      of those naming NMR                   : {int(dis.names_nmr.sum())}")
print(f"      of those naming no NMR                : {int((~dis.names_nmr).sum())}")
print()
print("    those naming no NMR:")
print(dis[~dis.names_nmr][["pn", "in_n_series_family", "pms_category", "tonnage_band",
                           "ap_short", "series_all", "band_status",
                           "eur_all_years"]].to_string(index=False))
print()
print(f"    rows in the file carrying 5.5 t          : {int(e2.tonnage_band.str.contains('5.5t').sum())}")
print(f"    of those naming NMR in the file          : "
      f"{int(e2[e2.tonnage_band.str.contains('5.5t')].names_nmr.sum())}")
print(f"    of those naming no NMR                   : "
      f"{int((~e2[e2.tonnage_band.str.contains('5.5t')].names_nmr).sum())}")

print()
print("#" * 116)
print("C. THE 16 ROWS / EXCLUSIVE_BAND = 3.5t_N35")
print("#" * 116)
alone = tc[tc.band_list == "['5.5t']"].copy()
al = alone[["pn"]].merge(ap[["pn", "exclusive_band", "n_series_bands"]], on="pn", how="left")
al.insert(1, "category", alone["category"].values)
al.insert(2, "band_list", alone["band_list"].values)
al.insert(3, "eur", alone["eur"].values)
al["states_35"] = al.n_series_bands.map(np_)
v_frozen = int((al.exclusive_band == "3.5t_N35").sum())
al_live = alone.merge(tc_live[["pn", "exclusive_band"]], on="pn", how="left", suffixes=("", "_live"))
v_live = int((al_live.exclusive_band_live == "3.5t_N35").sum())
print(f"  rows whose legacy band_list == ['5.5t']            : {len(alone)}")
print(f"  euro on them                                       : EUR {pd.to_numeric(alone.eur).sum():,.2f}")
print(f"  exclusive_band == 3.5t_N35, frozen basis (HEAD)    : {v_frozen}")
print(f"  exclusive_band == 3.5t_N35, live basis (now)       : {v_live}")
print(f"  '3.5t' inside band_list on those rows              : "
      f"{int(alone.band_list.str.contains('3.5t').sum())}")
print()
print(al[["pn", "category", "band_list", "eur", "n_series_bands", "exclusive_band",
          "states_35"]].to_string(index=False))
print()
print("  the raw exclusive_band values on the 16:")
print(al.exclusive_band.fillna("(blank)").value_counts().to_string())

print()
print("#" * 116)
print("D. BLAST RADIUS — nseries_tonnage_evolution.csv / .meta.json")
print("#" * 116)
print(f"  rows {len(evo)}")
print(f"  tonnage_band values: {sorted(evo.tonnage_band.unique())}")
print(f"  membership values  : {sorted(evo.membership.unique())}")
print(f"  sums_to_n_series_total: {evo.sums_to_n_series_total.value_counts().to_dict()}")
tot = evo[pd.to_numeric(evo.sums_to_n_series_total, errors='coerce').notna()]
print(f"  meta keys: {sorted(meta.keys())}")
print()
print("  the published exclusive-attribution share, derived read-only:")
sub = evo[evo.sums_to_n_series_total.astype(str).str.lower() == "yes"]
print(f"    rows with sums_to_n_series_total yes   : {len(sub)}")
print(f"    billed_eur on them                     : EUR {pd.to_numeric(sub.billed_eur).sum():,.2f}")
ax = sub[sub.membership == "single_band_only"]
print(f"    single_band_only rows                  : {len(ax)}")
print(f"    single_band_only billed_eur            : EUR {pd.to_numeric(ax.billed_eur).sum():,.2f}")
for b in ("3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"):
    s = sub[sub.tonnage_band == b]
    print(f"      {b:22s} rows {len(s):4d}  EUR {pd.to_numeric(s.billed_eur).sum():>14,.2f}")
print()
print("    by membership:")
for mem, g in sub.groupby("membership"):
    print(f"      {mem:22s} rows {len(g):4d}  EUR {pd.to_numeric(g.billed_eur).sum():>14,.2f}")
print()
print(f"    brief's figures: EUR 1,340,013.94 / EUR 4,501,286.47 = 29.7696%")
for num, den, lbl in ((1340013.94, 4501286.47, "brief"),
                      (pd.to_numeric(ax.billed_eur).sum(), pd.to_numeric(sub.billed_eur).sum(), "derived")):
    print(f"    {lbl:8s}: {num:,.2f} / {den:,.2f} = {num / den * 100:.4f}%")
print()
print("    meta 'by_status' / 'band_split_single_versus_shared':")
print(f"      by_status      : {meta.get('by_status')}")
print(f"      band_split     : {meta.get('band_split_single_versus_shared')}")
print(f"      tie_out        : {meta.get('tie_out')}")
print(f"      n_series_total : {meta.get('n_series_total_eur_all_years')}")
print(f"      generated_at   : {meta.get('generated_at')}")
print(f"      generated_by   : {meta.get('generated_by')}")
print(f"      decode_snapshot: {meta.get('decode_snapshot')}")

print()
print("#" * 116)
print("E. HAS THE FREE SET ALREADY BEEN RE-BASED IN ITS OWN FILE?")
print("#" * 116)
tl = tc_live.set_index(tc_live.pn.map(key))
api = ap.set_index(ap.pn.map(key))
n_old = n_new = 0
for _, r in free.iterrows():
    hold = nl(tl.loc[r.k, "band_list"]) if r.k in tl.index else "(absent)"
    n_old += 1
    n_new += int(hold == r.ap_short)
print(f"  free set (no NMR anywhere)                    : {len(free)}")
print(f"  of them agreeing with the mapping in the LIVE tonnage_capable : {n_new} of {n_old}")
print()
print("  for reference, the frozen set the census used:")
print(f"    frozen rows {len(tc)}   live rows {len(tc_live)}")
print(f"    frozen sha {sha(SCR / 'tc_frozen_HEAD.csv')[:24]}")
print(f"    live   sha {sha(DER / 'tonnage_capable_part_numbers.csv')[:24]}")
print(f"    published band file sha {sha(DER / 'epc_decode_nseries_banded.csv')[:24]}")
