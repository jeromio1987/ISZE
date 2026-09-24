"""Does the file named in the brief (epc_decode_nseries_banded.csv) contain any of the 44?

Two independent routes:
  route A  the 44 PNs, joined into the published band file, where its band differs from the
           corrected mapping and the row names no NMR
  route B  every published-band-file row whose band differs from the corrected mapping and
           whose row names no NMR anywhere
If both come back empty, the brief's file and the brief's 44 are different populations.
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
pd.set_option("display.width", 300)
pd.set_option("display.max_colwidth", 80)

key = lambda s: str(s).strip().lstrip("0") or "0"


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

tc["k"] = tc.pn.map(key)
ap["k"] = ap.pn.map(key)
ep["k"] = ep.pn.map(key)

m = tc[["k", "pn", "band_list", "eur", "category"]].merge(
    ap[["k", "pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes",
        "exclusive_band", "band_status", "eur"]],
    on="k", suffixes=("_tc", "_ap"), how="inner")
m["ap_short"] = m["n_series_bands"].map(norm_pipe)
m["tc_short"] = m["band_list"].map(norm_literal)
diff = m[m["ap_short"] != m["tc_short"]].copy()

APCOLS = ["codes_named", "parked_codes", "unresolved_codes", "n_series_bands",
          "exclusive_band", "band_status"]
diff["nmr_ap"] = diff[APCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1)
note44 = diff[~diff.nmr_ap].copy()
note132 = diff[diff.nmr_ap]
print(f"note's split: 176 total -> {len(note132)} parked, {len(note44)} free "
      f"(EUR {pd.to_numeric(note44.eur_ap).sum():,.2f})")

#if the published file is the right target, how many of the 44 are even in it?
epi = ep.set_index("k")
EPCOLS = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
          "series_unresolved", "band_reason", "tonnage_band", "family"]
in_ep = note44[note44.k.isin(epi.index)]
print()
print("=" * 120)
print("ROUTE A — the 44 joined into epc_decode_nseries_banded.csv")
print("=" * 120)
print(f"  the 44                       : {len(note44)}")
print(f"  of them present in the file  : {len(in_ep)}")
rows = []
for _, r in in_ep.iterrows():
    e = epi.loc[r.k]
    if isinstance(e, pd.DataFrame):
        e = e.iloc[0]
    ep_names = any(NMR.search(str(e[c])) for c in EPCOLS)
    rows.append({"pn": r.k, "ap_short": r.ap_short, "ep_short": norm_pipe(e["tonnage_band"]),
                 "ep_names_NMR": ep_names, "eur": float(r.eur_ap),
                 "in_n_family": e["in_n_series_family"]})
a = pd.DataFrame(rows)
print(a.to_string(index=False))
print()
print(f"  of the {len(a)}: the file already agrees with the corrected mapping : "
      f"{int((a.ap_short == a.ep_short).sum())}")
print(f"  of the {len(a)}: the file disagrees                                : "
      f"{int((a.ap_short != a.ep_short).sum())}")
print(f"  of the {len(a)}: name NMR in the file's own code columns            : "
      f"{int(a.ep_names_NMR.sum())}")
print()
print(f"  >>> rows in the 44 that the file disagrees on AND that name no NMR: "
      f"{int(((a.ap_short != a.ep_short) & ~a.ep_names_NMR).sum())}")

print()
print("=" * 120)
print("ROUTE B — every row of epc_decode_nseries_banded.csv vs the corrected mapping")
print("=" * 120)
api = ap.set_index("k")
e2 = ep.copy()
e2["ap_short"] = e2.k.map(lambda k: norm_pipe(api.loc[k, "n_series_bands"]) if k in api.index
                          else "(not in mapping)")
e2["ep_short"] = e2.tonnage_band.map(norm_pipe)
e2["ep_names_NMR"] = e2.apply(
    lambda r: any(NMR.search(str(r[c])) for c in EPCOLS if c in r.index), axis=1)
known = e2[e2.ap_short != "(not in mapping)"]
dis = known[known.ep_short != known.ap_short]
print(f"  rows in the file matched to the mapping      : {len(known)}")
print(f"  rows where the file's band differs from it   : {len(dis)}")
print(f"  euro on those rows                           : "
      f"EUR {pd.to_numeric(dis.eur_all_years).sum():,.2f}")
print(f"    of those, the row names NMR                : {int(dis.ep_names_NMR.sum())}")
print(f"    of those, the row names no NMR             : {int((~dis.ep_names_NMR).sum())}")
print()
print(f"  >>> rows the file disagrees on that name no NMR anywhere: "
      f"{int((~dis.ep_names_NMR).sum())}")
nz = dis[~dis.ep_names_NMR]
if len(nz):
    print(nz[["pn", "in_n_series_family", "pms_category", "tonnage_band", "ap_short",
              "eur_all_years"]].to_string(index=False))
else:
    print("      (empty — every band disagreement in the file is NMR-caused)")

print()
print("=" * 120)
print("WHERE THE FILE'S 5.5 t COMES FROM")
print("=" * 120)
c55 = ep[ep.tonnage_band.str.contains("5.5t")]
print(f"  rows carrying 5.5t                            : {len(c55)}")
print(f"  of those naming NMR in the file's own columns  : "
      f"{int(c55[EPCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1).sum())}")
print(f"  of those naming no NMR at all                  : "
      f"{int((~c55[EPCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1)).sum())}")

print()
print("=" * 120)
print("HOW MANY OF THE FILE'S ROWS CARRY 5.5 t *BECAUSE OF* NMR (the EPC decode)")
print("=" * 120)
b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str, low_memory=False).fillna("")
b1["k"] = b1.pn.map(key)
b1c = dict(zip(b1.k, b1.model_codes))
cnt_nmr = cnt_other = 0
for _, r in c55.iterrows():
    mc = str(b1c.get(r.k, ""))
    if NMR.search(mc):
        cnt_nmr += 1
    else:
        cnt_other += 1
print(f"  EPC decode names NMR  : {cnt_nmr}")
print(f"  EPC decode names no NMR: {cnt_other}")
print(f"  rows in the EPC decode at all: {int(c55.k.isin(b1.k).sum())} of {len(c55)}")
