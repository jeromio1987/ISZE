"""Cross-check: how the 176 / 132 / 44 map onto the file I am asked to edit
(epc_decode_nseries_banded.csv), and whether the 'neither' set really names no NMR.
Read only.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"

NMR = re.compile(r"\bNMR(?:85)?\b")
pd.set_option("display.width", 280)
pd.set_option("display.max_colwidth", 70)


def short(b):
    return b.split("_")[0] if b else ""


def norm_pipe(raw):
    return "|".join(sorted(short(t) for t in str(raw).split("|") if t)) if raw else ""


def norm_literal(raw):
    if not raw or raw == "[]":
        return ""
    try:
        return "|".join(sorted(str(t) for t in ast.literal_eval(raw) if t))
    except (ValueError, SyntaxError):
        return "PARSE_ERROR"


tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")
ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")

m = tc[["pn", "band_list", "eur", "category"]].merge(
    ap[["pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes",
        "exclusive_band", "band_status", "eur"]],
    on="pn", suffixes=("_tc", "_ap"), how="inner")
m["ap_short"] = m["n_series_bands"].map(norm_pipe)
m["tc_short"] = m["band_list"].map(norm_literal)
diff = m[m["ap_short"] != m["tc_short"]].copy()

APCOLS = ["codes_named", "parked_codes", "unresolved_codes", "n_series_bands",
          "exclusive_band", "band_status"]
diff["nmr_ap"] = diff[APCOLS].apply(
    lambda r: any(NMR.search(str(v)) for v in r), axis=1)
parked = diff[diff["nmr_ap"]]
free = diff[~diff["nmr_ap"]].copy()

print("=" * 120)
print("THE 44 (ap columns name no NMR) — annotated against the published band file")
print("=" * 120)
epi = ep.set_index("pn")
rows = []
for _, r in free.iterrows():
    pn = r["pn"]
    e = epi.loc[pn] if pn in epi.index else None
    if isinstance(e, pd.DataFrame):
        e = e.iloc[0]
    ep_series = " ".join(str(e[c]) for c in
                         ["series_from_epc", "series_from_crossref", "series_all",
                          "series_unresolved", "band_reason"]) if e is not None else "(not in file)"
    rows.append({
        "pn": pn,
        "category": r["category"],
        "tc_band_list": r["tc_short"],
        "ap_n_series_bands": r["ap_short"],
        "eur": float(r["eur_ap"]),
        "in_ep_file": "yes" if e is not None else "no",
        "ep_tonnage_band": norm_pipe(e["tonnage_band"]) if e is not None else "",
        "ep_names_nmr": bool(NMR.search(ep_series)) if e is not None else False,
        "ap_codes_named": r["codes_named"],
        "ap_parked": r["parked_codes"],
    })
free_df = pd.DataFrame(rows)
print(free_df.to_string(index=False))

print()
print(f"  of the 44: present in the published band file : {int((free_df.in_ep_file == 'yes').sum())}")
print(f"  of the 44: name NMR in the published band file : {int(free_df.ep_names_nmr.sum())}")
print(f"  of the 44: name neither anywhere              : {int((~free_df.ep_names_nmr).sum())}")

print()
print("  of the 132 parked: present in the published band file :",
      int(diff.loc[diff["nmr_ap"], "pn"].isin(ep.pn).sum()))

print()
print("=" * 120)
print("DOES 'ap_names_nmr' AGREE WITH 'ep_names_nmr'?  (whole 176)")
print("=" * 120)
allrows = []
for _, r in diff.iterrows():
    pn = r["pn"]
    e = epi.loc[pn] if pn in epi.index else None
    if isinstance(e, pd.DataFrame):
        e = e.iloc[0]
    ep_series = " ".join(str(e[c]) for c in
                         ["series_from_epc", "series_from_crossref", "series_all",
                          "series_unresolved", "band_reason"]) if e is not None else ""
    allrows.append({"pn": pn, "nmr_ap": r["nmr_ap"],
                    "in_ep": e is not None,
                    "nmr_ep": bool(NMR.search(ep_series)) if e is not None else False,
                    "tc": r["tc_short"], "ap": r["ap_short"], "eur": float(r["eur_ap"])})
allf = pd.DataFrame(allrows)
both = allf[allf.in_ep]
print(f"  overlapping with the published file : {len(both)}")
print(pd.crosstab(both.nmr_ap, both.nmr_ep, rownames=["names NMR in ap"],
                  colnames=["names NMR in ep"]).to_string())
mismatch = both[both.nmr_ap != both.nmr_ep]
print()
print(f"  rows where the two files disagree on whether the PN names NMR: {len(mismatch)}")
print(mismatch.to_string(index=False))

# what band does ep carry vs ap for the overlapping rows?
print()
print("=" * 120)
print("EP vs AP BAND DISAGREEMENT (overlapping rows, short names)")
print("=" * 120)
both = both.copy()
both["ep_short"] = epi.loc[both.pn, "tonnage_band"].map(norm_pipe).values
disagree = both[both.ep_short != both.ap]
print(f"  overlapping rows                        : {len(both)}")
print(f"  ep band == ap band                      : {int((both.ep_short == both.ap).sum())}")
print(f"  ep band != ap band                      : {len(disagree)}")
print(f"  eur on the disagreeing rows             : EUR {disagree.eur.sum():,.2f}")
print(f"  of the disagreeing, ap names NMR        : {int(disagree.nmr_ap.sum())}")
print(f"  of the disagreeing, ap names no NMR     : {int((~disagree.nmr_ap).sum())}")
print()
print("  shape table for the ep-vs-ap disagreements:")
g = disagree.groupby(["ep_short", "ap"]).agg(
    n=("pn", "size"), eur=("eur", "sum")).reset_index()
print(g.sort_values("eur", ascending=False).to_string(index=False))
