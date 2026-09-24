"""Decide the 44 decisively.

Two candidate definitions of "carries an NMR code" are in play and they disagree on 8 rows.
This resolves them against the PRIMARY source (the EPC decode and the BVP cross-reference),
not against either derived table.
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
pd.set_option("display.max_colwidth", 90)


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
b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str, low_memory=False).fillna("")
dec2 = json.loads((DER / "epc_decode_batch2_20260919.json").read_text(encoding="utf-8"))
xr = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False).fillna("")

APCOLS = ["codes_named", "parked_codes", "unresolved_codes", "n_series_bands",
          "exclusive_band", "band_status"]
EPCOLS = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
          "series_unresolved", "band_reason"]

# ---- primary-source token sets -----------------------------------------------------------
b1i = b1.set_index(b1.pn.map(lambda s: str(s).strip().lstrip("0") or "0"))
epc_codes: dict[str, set[str]] = {}
for pn, r in b1i.iterrows():
    toks = {t.strip().upper() for t in str(r.model_codes).split(",") if t.strip()}
    epc_codes[str(pn)] = toks
for r in dec2:
    k = str(r["pn"]).strip().lstrip("0") or "0"
    toks = set()
    for m in (r.get("models") or []):
        for raw in re.split(r"[,\s]+", str(m).upper()):
            t = raw.strip().strip("()[]{}")
            if t:
                toks.add(t)
    epc_codes[k] = epc_codes.get(k, set()) | toks

xr_codes: dict[str, set[str]] = {}
for r in xr.itertuples():
    toks = {t.strip().upper() for t in re.split(r"[,\s]+", str(r.vehicle_model)) if t.strip()}
    for pn in {str(r.genuine_pn).strip().lstrip("0") or "0",
               str(r.bvp_pn).strip().lstrip("0") or "0"}:
        xr_codes[pn] = xr_codes.get(pn, set()) | toks


def primary_nmr(pn: str) -> tuple[bool, list[str]]:
    hits = []
    e = epc_codes.get(pn, set())
    if any(NMR.fullmatch(t) for t in e):
        hits.append("EPC:" + ",".join(sorted(t for t in e if NMR.fullmatch(t))))
    x = xr_codes.get(pn, set())
    if any(NMR.fullmatch(t) for t in x):
        hits.append("XREF:" + ",".join(sorted(t for t in x if NMR.fullmatch(t))))
    return bool(hits), hits


# ---- the two candidate sets --------------------------------------------------------------
m = tc[["pn", "band_list", "eur", "category"]].merge(
    ap[["pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes",
        "exclusive_band", "band_status", "eur"]],
    on="pn", suffixes=("_tc", "_ap"), how="inner")
m["ap_short"] = m["n_series_bands"].map(norm_pipe)
m["tc_short"] = m["band_list"].map(norm_literal)
diff = m[m["ap_short"] != m["tc_short"]].copy()
diff["key"] = diff.pn.map(lambda s: str(s).strip().lstrip("0") or "0")

diff["nmr_ap"] = diff[APCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1)

epi = ep.set_index(ep.pn.map(lambda s: str(s).strip().lstrip("0") or "0"))
def ep_nmr(pn):
    if pn not in epi.index:
        return False
    r = epi.loc[pn]
    if isinstance(r, pd.DataFrame):
        r = r.iloc[0]
    return any(NMR.search(str(r[c])) for c in EPCOLS if c in r.index)
diff["nmr_ep"] = diff.key.map(ep_nmr)
diff["nmr_primary"], diff["primary_where"] = zip(*diff.key.map(primary_nmr))

print("=" * 130)
print("THE THREE DEFINITIONS, OVER THE 176")
print("=" * 130)
eur = pd.to_numeric(diff.eur_ap)
for lbl, col in (("applies its own codes_named/parked (the note's basis)", "nmr_ap"),
                 ("the published band file's series columns", "nmr_ep"),
                 ("the EPC decode + cross-reference (primary)", "nmr_primary")):
    mask = diff[col]
    print(f"  {lbl:54s} NMR {int(mask.sum()):4d}  EUR {eur[mask].sum():>15,.2f} | "
          f"neither {int((~mask).sum()):4d}  EUR {eur[~mask].sum():>15,.2f}")

print()
print("  cross-tab: ap says no NMR, does the published file say NMR?")
nomnr = diff[~diff.nmr_ap]
print(pd.crosstab(nomnr.nmr_ep, nomnr.nmr_primary,
                  rownames=["published file names NMR"], colnames=["primary names NMR"]).to_string())

print()
print("=" * 130)
print("THE 8 THE PUBLISHED FILE CALLS NMR BUT THE CORRECTED MAPPING DOES NOT")
print("=" * 130)
sus = diff[~diff.nmr_ap & diff.nmr_ep]
for _, r in sus.iterrows():
    pn = r.key
    e = epi.loc[pn]
    if isinstance(e, pd.DataFrame):
        e = e.iloc[0]
    print(f"  {pn:>12s}  {r['category']:14s} tc={r['tc_short']:18s} ap={r['ap_short']:14s} "
          f"EUR {float(r['eur_ap']):>12,.2f}")
    print(f"      ap codes_named     : {r['codes_named']}")
    print(f"      published series   : {e['series_from_epc']}  |  {e['series_from_crossref']}")
    print(f"      EPC batch1+2 codes : {sorted(epc_codes.get(pn, set()))}")
    print(f"      crossref codes     : {sorted(xr_codes.get(pn, set()))}")
    print(f"      PRIMARY NMR?       : {r['nmr_primary']}  {r['primary_where']}")

print()
print("=" * 130)
print("VERDICT SETS")
print("=" * 130)
for lbl, col in (("published-file definition", "nmr_ep"),
                 ("primary-source definition", "nmr_primary")):
    free = diff[~diff[col]]
    print(f"  {lbl:28s} -> free {len(free):3d}  EUR {pd.to_numeric(free.eur_ap).sum():>14,.2f}"
          f"   parked {int(diff[col].sum()):3d}  EUR {eur[diff[col]].sum():>14,.2f}")
diff[["pn", "category", "tc_short", "ap_short", "eur_ap", "nmr_ap", "nmr_ep", "nmr_primary",
      "codes_named", "parked_codes"]].to_csv(SCR / "_definitions_176.csv", index=False)
print("\n  written: _definitions_176.csv")
