"""Clock split, blast-radius structure, and the two family pages.
Read only — the builder is NOT run.
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


evo = pd.read_csv(DER / "nseries_tonnage_evolution.csv", dtype=str).fillna("")
ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")

print("=" * 110)
print("CLOCK SPLIT — why the brief's euro figures are half of the file's total")
print("=" * 110)
sub = evo[evo.sums_to_n_series_total.astype(str).str.lower() == "yes"].copy()
sub["eur"] = pd.to_numeric(sub.billed_eur)
for clock, g in sub.groupby("clock"):
    ax = g[g.membership == "single_band_only"]
    tot = g.eur.sum()
    exc = ax.eur.sum()
    print(f"  clock {clock}: rows {len(g):4d}  total EUR {tot:>14,.2f}  "
          f"single_band_only EUR {exc:>13,.2f}  share {exc / tot * 100:.4f}%")
print()
print(f"  both clocks summed: EUR {sub.eur.sum():,.2f}  (= 2 x 4,501,286.47)")
print(f"  brief's denominator EUR 4,501,286.47  -> a single clock")
print(f"  brief's numerator   EUR 1,340,013.94  -> a single clock's single_band_only")

print()
print("=" * 110)
print("BLAST RADIUS OF *MY* AUTHORISED CHANGE")
print("=" * 110)
print("  the file that feeds the builder is epc_decode_nseries_banded.csv.")
print("  rows that change under the brief's instruction: 0 (see below)")

print()
print("=" * 110)
print("STRUCTURE — what removing 5.5 t from the NMR rows would do (hypothetical, not run)")
print("=" * 110)
ep["nb"] = ep.tonnage_band.map(np_)
ep["has55"] = ep.tonnage_band.str.contains("5.5t")
ep["names_nmr"] = ep.apply(lambda r: any(NMR.search(str(r[c])) for c in
                                         ["series_from_epc", "series_from_crossref",
                                          "series_all", "series_unresolved", "band_reason"]), axis=1)
fam = ep[ep.in_n_series_family == "yes"].copy()
print(f"  in-family rows             : {len(fam)}")
print(f"  in-family rows with 5.5 t  : {int(fam.has55.sum())}")
print(f"  of those, also on 3.5 t    : {int((fam.has55 & fam.nb.str.contains('3.5t')).sum())}")
print(f"  of those, also on 7.5 t    : {int((fam.has55 & fam.nb.str.contains('7.5t')).sum())}")
print(f"  of those, 5.5 t alone      : {int((fam.nb == '5.5t').sum())}")
print()
# band-set shapes among in-family rows carrying 5.5t
shapes = fam[fam.has55].nb.value_counts()
print("  shapes of the in-family rows carrying 5.5 t:")
for k, v in shapes.items():
    print(f"    {k:46s} {v:4d}")
print()
# what each shape becomes if 5.5t is dropped
def drop55(s):
    return "|".join(t for t in s.split("|") if t != "5.5t")
fam["after"] = fam.nb.map(drop55)
moves = fam[fam.has55][["pn", "nb", "after", "eur_all_years"]]
moves = moves.assign(after=moves.after.map(lambda s: s if s else "(none)"))
print("  bucket transitions if the 5.5 t name were removed:")
tr = moves.groupby(["nb", "after"]).agg(n=("pn", "size"),
                                        eur=("eur_all_years", lambda s: pd.to_numeric(s).sum()))
for (b, a), r in tr.iterrows():
    print(f"    {b:44s} -> {a:26s} {int(r['n']):4d}  EUR {r['eur']:>13,.2f}")
print()
print("  => a 2-member set {3.5t,5.5t} would become single-band on 3.5t, which MOVES it out of")
print("     shared_across_bands into single_band. That is a real bucket move if the 5.5 t name")
print("     is ever removed — but it is exactly the parked NMR decision, not this brief.")
print()
print(f"  single-band euro currently on the 5.5 t rung (published): "
      f"EUR {pd.to_numeric(fam.loc[fam.nb == '5.5t', 'eur_all_years']).sum():,.2f}")

print()
print("=" * 110)
print("THE TWO FAMILY PAGES")
print("=" * 110)
pages = ["02_dashboards/sales/ISZE_PMS_Family_Evolution_v2.html",
         "02_dashboards/sales/_build/history/ISZE_PMS_Family_Evolution_Deep_retired_2026-09-19.html"]
for p in pages:
    f = ROOT / p
    if not f.exists():
        print(f"  {p}: ABSENT")
        continue
    txt = f.read_text(encoding="utf-8", errors="replace")
    print(f"  {p}")
    print(f"    bytes {len(txt):,}   mtime {pd.Timestamp(f.stat().st_mtime, unit='s')}")
    for term in ("5.5t", "5.5 t", "5.5t_N50_N55", "3.5t_N35", "7.5t_N50_N62_N75", "band_list"):
        print(f"    occurrences of {term!r}: {txt.count(term)}")
    # do any of the free PNs appear in the page payload?
    free_pns = [r.pn for _, r in tc.merge(ap[["pn"]], on="pn").iterrows()]
    hits = [pn for pn in free_pns if pn in txt]
    print(f"    free-set part numbers appearing on the page: {len(hits)}")
    if hits:
        print(f"      {hits[:20]}")
