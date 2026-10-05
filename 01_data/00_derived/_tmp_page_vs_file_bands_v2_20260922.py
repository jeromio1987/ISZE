"""Correct staleness test: decode the page's own band convention, then compare.

build_family_evolution_v2.py `band_members()`:
    bs = file bands in the three real bands
    if exactly one -> [that band]
    if several    -> bs + ["shared_across_bands"]   (a deliberate extra display token)
    if none       -> ["unresolved_series"]
Only part numbers whose family is `n_series_truck` get a band list at all; the other
part numbers 451 of them are carried for the drill-down with an empty list.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731
REAL_BANDS = ["3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"]

html = HTML.read_text(encoding="utf-8")
p = json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                         html, re.S).group(1))
pn = p["pn"]

nband = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
nband["pnk"] = nband.pn.map(norm)
file_bands = {r.pnk: [x for x in str(r.tonnage_band).split("|") if x]
              for r in nband.itertuples()}
file_status = dict(zip(nband.pnk, nband.band_status))

FAM_N = "n_series_truck"
page_fam_key = [f["key"] for f in p["families"]]
FAM_IX = {f["key"]: i for i, f in enumerate(p["families"])}

band_mismatch = []
for i, num in enumerate(pn["number"]):
    k = norm(str(num))
    pbands = pn["bands"][i]
    is_n = page_fam_key[pn["fam"][i]] == FAM_N
    fb = file_bands.get(k, [])
    if not is_n:
        expected = []
    elif not fb:
        expected = ["unresolved_series"]
    elif len(fb) == 1:
        expected = fb
    else:
        expected = fb + ["shared_across_bands"]
    if pbands != expected:
        band_mismatch.append((num, pbands, expected, is_n, file_status.get(k, "-")))

print(f"part numbers on page: {len(pn['number'])}")
print(f"  of which family=n_series_truck: {sum(1 for i in range(len(pn['number'])) if page_fam_key[pn['fam'][i]]==FAM_N)}")
print(f"  carrying a non-empty band list: {sum(1 for b in pn['bands'] if b)}")
print(f"file rows: {len(nband)}")
print(f"\nBAND-LIST MISMATCHES after decoding the page convention: {len(band_mismatch)}")
for r in band_mismatch[:15]:
    print(f"  pn={r[0]} page={r[1]} expected={r[2]} is_n_series={r[3]} file_status={r[4]}")

# nbands: the page stores the COUNT OF REAL BANDS, not including the shared token
nb_mismatch = []
for i, num in enumerate(pn["number"]):
    k = norm(str(num))
    fb = file_bands.get(k, [])
    if pn["nbands"][i] != len(fb):
        nb_mismatch.append((num, pn["nbands"][i], len(fb)))
print(f"\nNBANDS MISMATCHES: {len(nb_mismatch)}")
for r in nb_mismatch[:15]:
    print(f"  pn={r[0]} page={r[1]} file={r[2]}")

# the statuses the page quotes vs the file
print(f"\npage weightEvidence.noSeriesPns  {p['weightEvidence']['noSeriesPns']} "
      f"vs file {(nband.band_status=='no_series_found').sum()}")
print(f"page weightEvidence.unresolvedPns {p['weightEvidence']['unresolvedPns']} "
      f"vs file {(nband.band_status=='series_unresolved').sum()}")

# the evo file the page reads but never uses: what changed in it?
evo = pd.read_csv(DER / "nseries_tonnage_evolution.csv")
print(f"\nevolution file rows: {len(evo)} (read by the page at one line; never referenced again)")
