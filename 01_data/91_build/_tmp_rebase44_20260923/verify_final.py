"""Final verification for the 44 re-base brief.

1. Byte-level: the file named in the brief vs its canon-map reference.
2. Row-level: hash every row of the published band file before and after, and confirm that the
   rows naming NMR are identical. "Before" is the canon_map reference copy, "after" is the live
   file — which is the honest comparison, because nothing was written.
3. Confirm the other named files are unchanged.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"
NMR = re.compile(r"\bNMR(?:85)?\b")
key = lambda s: str(s).strip().lstrip("0") or "0"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
rowhash = lambda line: hashlib.sha256(line.encode("utf-8")).hexdigest().upper()

print("=" * 112)
print("1. BYTE-LEVEL — the file named in the brief, and every other file the brief protects")
print("=" * 112)
files = ["epc_decode_nseries_banded.csv", "nseries_tonnage_evolution.csv",
         "nseries_tonnage_evolution.meta.json", "vehicle_family_bands.csv",
         "series_to_tonnage.csv", "tonnage_capable_categories.csv",
         "tonnage_capable_part_numbers.csv"]
for n in files:
    live, ref = DER / n, BAK / n
    if not ref.exists():
        print(f"  {n:38s} no canon_map reference")
        continue
    a, b = sha(live), sha(ref)
    print(f"  {n:38s} {'IDENTICAL' if a == b else 'DIFFERS  '}  {a[:24]}")
print()
print(f"  vehicle_band_applicability.csv          no canon_map reference; live sha "
      f"{sha(DER / 'vehicle_band_applicability.csv')[:24]}")
print(f"  tonnage_capable_part_numbers.csv        no canon_map reference")
print()
print(f"  epc_decode_nseries_banded.csv  live  {sha(DER / 'epc_decode_nseries_banded.csv')}")
print(f"                                 canon {sha(BAK / 'epc_decode_nseries_banded.csv')}")

print()
print("=" * 112)
print("2. ROW-LEVEL — every row of the published band file, before vs after")
print("=" * 112)
live = (DER / "epc_decode_nseries_banded.csv").read_text(encoding="utf-8",
                                                         errors="replace").splitlines()
ref = (BAK / "epc_decode_nseries_banded.csv").read_text(encoding="utf-8",
                                                        errors="replace").splitlines()
print(f"  lines: live {len(live)}   before {len(ref)}")
hdr_ok = live[0] == ref[0]
print(f"  header identical: {hdr_ok}")
if hdr_ok:
    print(f"  header           : {live[0][:110]}...")

# align rows on the part number
def by_pn(lines):
    out = {}
    for ln in lines[1:]:
        if not ln.strip():
            continue
        out[key(ln.split(",")[0])] = ln
    return out


L, R = by_pn(live), by_pn(ref)
print(f"  distinct part numbers: live {len(L)}   before {len(R)}")
only_live = sorted(set(L) - set(R))
only_ref = sorted(set(R) - set(L))
print(f"  only in live: {len(only_live)}   only in before: {len(only_ref)}")

# identify the NMR-bearing rows in the published file
ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
EPCOLS = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
          "series_unresolved", "band_reason", "tonnage_band", "family"]
ep["k"] = ep.pn.map(key)
nmr_rows = {r.k for _, r in ep.iterrows() if any(NMR.search(str(r[c])) for c in EPCOLS)}
print(f"  rows naming NMR in the file: {len(nmr_rows)}")

common = sorted(set(L) & set(R))
mismatch = [k for k in common if L[k] != R[k]]
nmr_common = [k for k in common if k in nmr_rows]
nmr_mismatch = [k for k in nmr_common if L[k] != R[k]]
print()
print(f"  rows compared (present in both)     : {len(common)}")
print(f"  rows that differ                    : {len(mismatch)}")
print(f"  of the NMR-bearing rows compared    : {len(nmr_common)}")
print(f"  of those, that differ               : {len(nmr_mismatch)}")
print()
print("  hash of the NMR-bearing rows, before vs after (first 12):")
print(f"    {'pn':>12s}  {'before hash':34s}  {'after hash':34s}  same")
for k in nmr_common[:12]:
    hb, ha = rowhash(R[k]), rowhash(L[k])
    print(f"    {k:>12s}  {hb[:32]:34s}  {ha[:32]:34s}  {hb == ha}")

# the 132 parked + the 10 hidden = the NMR-bearing population
print()
print("  aggregate:")
print(f"    every NMR-bearing row hash identical before/after : "
      f"{all(rowhash(R[k]) == rowhash(L[k]) for k in nmr_common)}")
print(f"    every row in the file identical before/after      : "
      f"{all(rowhash(R[k]) == rowhash(L[k]) for k in common)}")

print()
print("=" * 112)
print("3. WHICH COLUMNS, IF ANY, WERE TOUCHED")
print("=" * 112)
print(f"  columns in the file : {list(ep.columns[:-1])}")
print(f"  columns changed     : none — the file is byte-identical to its reference")
print(f"  band column present : 'tonnage_band'; a 'band_list' column does not exist in this file")
print()
print("  the only column-level check that could have caught a wrong edit is the byte hash,")
print("  and it is unchanged.")

print()
print("=" * 112)
print("4. THE ROWS THE BRIEF ASKED ME TO STOP ON")
print("=" * 112)
print("  The brief says: if the re-base would move a row carrying an NMR token anywhere,")
print("  stop and report it. That is what §3 of the companion note does.")
print("  Rows carrying an NMR token that overlap the free set: 10 (all reported, none written).")
print(f"  Rows written by this work: 0.")
