"""Where does the published band file's 5.5 t actually sit, and who put it there?
Read only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"

NMR = re.compile(r"\bNMR(?:85)?\b")
pd.set_option("display.width", 300)
pd.set_option("display.max_colwidth", 95)

ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str, low_memory=False).fillna("")
ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")

EPCODE = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
          "series_unresolved", "band_reason"]
b1i = b1.set_index("pn")
api = ap.set_index("pn")

ep["carries_55"] = ep.tonnage_band.str.contains("5.5t")
print("=" * 130)
print("EVERY ROW IN THE PUBLISHED BAND FILE THAT CARRIES 5.5 t")
print("=" * 130)
print(f"  rows carrying 5.5t : {int(ep.carries_55.sum())} of {len(ep)}")
print(f"  euro on them       : EUR {pd.to_numeric(ep.loc[ep.carries_55, 'eur_all_years']).sum():,.2f}")

rows = []
for _, r in ep[ep.carries_55].iterrows():
    pn = r["pn"]
    ep_names_nmr = any(NMR.search(str(r[c])) for c in EPCODE if c in r.index)
    mc = b1i.loc[pn, "model_codes"] if pn in b1i.index else "(no epc decode row)"
    aprow = api.loc[pn] if pn in api.index else None
    if isinstance(aprow, pd.DataFrame):
        aprow = aprow.iloc[0]
    rows.append({
        "pn": pn,
        "in_family": r["in_n_series_family"],
        "ep_tonnage_band": r["tonnage_band"],
        "ep_names_NMR": ep_names_nmr,
        "epc_model_codes": str(mc),
        "epc_names_NMR": bool(NMR.search(str(mc))),
        "ap_n_series_bands": aprow["n_series_bands"] if aprow is not None else "(not in mapping)",
        "ap_codes_named": aprow["codes_named"] if aprow is not None else "",
        "eur": float(r["eur_all_years"]),
    })
d = pd.DataFrame(rows)
print()
print(f"  of those rows: name NMR in the published file : {int(d.ep_names_NMR.sum())}")
print(f"  of those rows: name NMR in the EPC decode     : {int(d.epc_names_NMR.sum())}")
print(f"  of those rows: name NMR in neither            : {int((~d.ep_names_NMR & ~d.epc_names_NMR).sum())}")
print()
print("  by category of cause:")
print(f"    NKR-caused (epc codes name NKR)            : "
      f"{int(d.epc_model_codes.str.contains(r'\\bNKR\\b').sum())}")
print(f"    NMR-caused (epc codes name NMR, no NKR)    : "
      f"{int((~d.epc_model_codes.str.contains(r'\\bNKR\\b') & d.epc_names_NMR).sum())}")
print()
print("  rows carrying 5.5t that name NMR in the EPC decode but NOT in the ap codes_named:")
q = d[d.epc_names_NMR & ~d.ap_codes_named.apply(lambda s: bool(NMR.search(str(s))))]
print(f"    {len(q)}")
if len(q):
    print(q[["pn", "ep_tonnage_band", "epc_model_codes", "ap_codes_named",
             "ap_n_series_bands", "eur"]].to_string(index=False))

print()
print("=" * 130)
print("THE ap codes_named vs THE EPC DECODE — do they agree on NMR for the 176?")
print("=" * 130)
tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")


def short(b):
    return b.split("_")[0] if b else ""


import ast
def norm_pipe(raw):
    return "|".join(sorted(short(t) for t in str(raw).split("|") if t)) if raw else ""


def norm_literal(raw):
    if not raw or raw == "[]":
        return ""
    try:
        return "|".join(sorted(str(t) for t in ast.literal_eval(raw) if t))
    except (ValueError, SyntaxError):
        return "PARSE_ERROR"


m = tc[["pn", "band_list", "eur"]].merge(
    ap[["pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes", "eur"]],
    on="pn", suffixes=("_tc", "_ap")).merge(
    b1[["pn", "model_codes"]], on="pn", how="left").fillna("")
m["ap_short"] = m["n_series_bands"].map(norm_pipe)
m["tc_short"] = m["band_list"].map(norm_literal)
diff = m[m["ap_short"] != m["tc_short"]].copy()
diff["ap_nmr"] = diff[["codes_named", "parked_codes", "unresolved_codes"]].apply(
    lambda r: any(NMR.search(str(v)) for v in r), axis=1)
diff["epc_nmr"] = diff["model_codes"].map(lambda s: bool(NMR.search(str(s))))
print(f"  176 rows; have an EPC decode row: {int((diff.model_codes != '').sum())}")
print(pd.crosstab(diff.ap_nmr, diff.epc_nmr, rownames=["ap names NMR"], colnames=["EPC names NMR"]).to_string())
dis = diff[diff.ap_nmr != diff.epc_nmr]
print(f"\n  rows where ap and the EPC decode disagree on NMR: {len(dis)}")
print(f"  euro on those rows: EUR {pd.to_numeric(dis['eur_ap']).sum():,.2f}")
print(dis[["pn", "tc_short", "ap_short", "eur_ap", "codes_named", "model_codes"]].to_string(index=False))
