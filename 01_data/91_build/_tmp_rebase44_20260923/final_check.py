"""Final decisions.

1. `epc_decode_nseries_banded.csv` has no `band_list` column at all — prove the 176 census
   cannot have been computed on it.
2. Decide the 8 rows whose NMR membership the derived tables disagree on, using the raw EPC
   edition strings (which is what the bander itself parses).
3. Examine 5876102900, the one published-file band disagreement that names no NMR.
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
pd.set_option("display.max_colwidth", 120)

ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")

print("=" * 120)
print("1. DOES THE FILE THE BRIEF NAMES EVEN HAVE THE COLUMN THE CENSUS USED?")
print("=" * 120)
print(f"  tonnage_capable_part_numbers.csv columns include 'band_list' : "
      f"{'band_list' in tc.columns}")
print(f"  epc_decode_nseries_banded.csv  columns include 'band_list' : "
      f"{'band_list' in ep.columns}")
print(f"  epc_decode_nseries_banded.csv band-ish columns : "
      f"{[c for c in ep.columns if 'band' in c]}")
print("  => the 176 comparison was made on a column that only exists in "
      "tonnage_capable_part_numbers.csv")

print()
print("=" * 120)
print("2. THE 8 ROWS — membership from the raw EPC edition strings")
print("=" * 120)
eight = ["8975167220", "8978808270", "8982473951", "8982482712", "8983320620",
         "8983459492", "8983550720", "8983753330"]
b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str, low_memory=False).fillna("")
b1["k"] = b1.pn.map(key)
b1c = dict(zip(b1.k, b1.model_codes))
dec2 = {key(r["pn"]): r for r in json.loads((DER / "epc_decode_batch2_20260919.json").read_text(encoding="utf-8"))}
xr = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False).fillna("")
xr_veh: dict[str, list[str]] = {}
for r in xr.itertuples():
    for pn in {key(r.genuine_pn), key(r.bvp_pn)}:
        xr_veh.setdefault(pn, []).append(str(r.vehicle_model))

TOKEN = re.compile(r"N[A-Z]{1,4}\d{0,3}")
rows = []
for pn in eight:
    b1s = str(b1c.get(pn, ""))
    d2 = dec2.get(pn, {})
    d2s = " | ".join(str(m) for m in (d2.get("models") or []))
    xrs = " | ".join(xr_veh.get(pn, []))
    # split compound tokens on / , ; and whitespace, exactly as the EPC writes them
    toks = set()
    for src in (b1s, d2s, xrs):
        for raw in re.split(r"[,\s;|]+", src.upper()):
            for part in raw.split("/"):
                part = part.strip().strip("()[]{}")
                if part:
                    toks.add(part)
    has = sorted(t for t in toks if NMR.fullmatch(t))
    rows.append({"pn": pn, "narodec_nmr": bool(has), "where": ",".join(has),
                 "batch1_model_codes": b1s[:80]})
print(pd.DataFrame(rows).to_string(index=False))
print()
print(f"  all 8 carry an NMR token in the raw EPC decode / cross-reference: "
      f"{all(r['narodec_nmr'] for r in rows)}")

print()
print("=" * 120)
print("3. THE ONE PUBLISHED-FILE DISAGREEMENT THAT NAMES NO NMR — 5876102900")
print("=" * 120)
for lbl, d in (("frozen legacy (band_list)", tc), ("corrected mapping", ap)):
    r = d[d.pn.map(key) == "5876102900"]
    if len(r):
        cols = [c for c in ["pn", "band_list", "n_series_bands", "bands", "eur", "codes_named",
                            "parked_codes", "unresolved_codes", "band_status", "category",
                            "pms_category"] if c in r.columns]
        print(f"  {lbl}:")
        print(r[cols].to_string(index=False))
r = ep[ep.pn.map(key) == "5876102900"]
print("  published band file:")
print(r[["pn", "in_n_series_family", "pms_category", "series_from_epc", "series_from_crossref",
         "series_all", "tonnage_band", "band_status", "eur_all_years"]].to_string(index=False))
print()
print(f"  is it in the 176? frozen band_list vs mapping ...")

print()
print("=" * 120)
print("4. WHERE DOES 5876102900 SIT IN THE 176/121 SPLIT?")
print("=" * 120)
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
        return "ERR"
m = tc[["pn", "band_list", "eur"]].merge(ap[["pn", "n_series_bands", "eur"]], on="pn",
                                         suffixes=("_tc", "_ap"))
m["ap_short"] = m.n_series_bands.map(np_)
m["tc_short"] = m.band_list.map(nl)
one = m[m.pn.map(key) == "5876102900"].iloc[0]
print(f"  frozen band_list {one.tc_short!r}  vs mapping {one.ap_short!r} "
      f"-> in the 176? {one.tc_short != one.ap_short}")
print()
print("  so: the published band file disagrees with the mapping on this row, but the")
print("  legacy band_list agrees with the mapping. The two derived tables disagree about")
print("  the row and the census (built on band_list) never saw it.")
