"""Generate 01_data/90_INBOX/PUBLISHED_BAND_PN_DIFF_44_2026-09-23.csv.

Population: the 44 the brief names — part numbers whose published band list differs from the
corrected mapping and whose mapping code columns name no NMR.

Three band bases are recorded side by side, because the brief's phrase "the current published
band" is ambiguous and the answer differs depending on which file is meant:
  published_band_list        the frozen legacy `band_list` in tonnage_capable_part_numbers.csv
                             (this is the column the 176 census was computed on)
  published_band_file_band   the `tonnage_band` in epc_decode_nseries_banded.csv (the file the
                             brief nominates for the edit) — that file has NO band_list column
  corrected_band             `n_series_bands` in vehicle_band_applicability.csv
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
INBOX = ROOT / "01_data" / "90_INBOX"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"

NMR = re.compile(r"\bNMR(?:85)?\b")
key = lambda s: str(s).strip().lstrip("0") or "0"


def short(b):
    return b.split("_")[0] if b else ""


def np_(raw):
    """'3.5t_N35|7.5t_N50_N62_N75' -> '3.5t|7.5t'."""
    return "|".join(sorted(short(t) for t in str(raw).split("|") if t)) if raw else ""


def nl(raw):
    """"['3.5t', '5.5t']" -> '3.5t|5.5t'."""
    if raw is None or str(raw).strip() == "" or str(raw).strip() == "[]":
        return ""
    try:
        return "|".join(sorted(str(t) for t in ast.literal_eval(raw) if t))
    except (ValueError, SyntaxError):
        return "PARSE_ERROR"


WHY = {
    ("5.5t", "3.5t"): "the published band list files this at 5.5 t alone; the corrected map reads "
                      "only NHR / NKR / NLR on the row, and all of those are 3.5 t",
    ("3.5t|5.5t", "3.5t"): "the published band list adds a 5.5 t rung that no code on the row "
                           "supports once NMR is parked",
    ("3.5t|5.5t|7.5t", "3.5t|7.5t"): "the 5.5 t rung in the published list is not carried by any "
                                     "code the corrected map resolves",
    ("5.5t|7.5t", "3.5t|7.5t"): "the published list reads 5.5 t where the corrected map reads "
                                "3.5 t on the same named codes",
    ("5.5t|7.5t", "7.5t"): "the published list reads 5.5 t; the corrected map reads 7.5 t",
    ("3.5t", ""): "the published list claims 3.5 t where the corrected map refuses a band",
    ("5.5t", ""): "the published list claims 5.5 t where the corrected map refuses a band",
    ("3.5t|5.5t", "3.5t|7.5t"): "5.5 t in the published list should read 7.5 t",
    ("", "3.5t"): "the published list gives no band; the corrected map reads 3.5 t",
}


def main() -> int:
    tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
    ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")
    ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
    b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str,
                     low_memory=False).fillna("")
    xr = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False).fillna("")
    fam = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False).fillna("")
    dec2 = json.loads((DER / "epc_decode_batch2_20260919.json").read_text(encoding="utf-8"))

    m = tc[["pn", "band_list", "eur", "category"]].merge(
        ap[["pn", "n_series_bands", "codes_named", "parked_codes", "unresolved_codes",
            "band_status", "eur"]], on="pn", suffixes=("_tc", "_ap"), how="inner")
    m["ap_short"] = m.n_series_bands.map(np_)
    m["tc_short"] = m.band_list.map(nl)
    diff = m[m.ap_short != m.tc_short].copy()

    # PMS category: the legacy table carries it on 23 of the 44 and is blank on the rest, so fill
    # from the corrected mapping and the family table too, and say plainly where none of them has it.
    famcat = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str,
                         low_memory=False).fillna("")
    cat_sources = [
        dict(zip(tc.pn.map(key), tc.category)),
        dict(zip(ap.pn.map(key), ap.pms_category if "pms_category" in ap.columns else [""] * len(ap))),
        dict(zip(ep.pn.map(key), ep.pms_category)),
        dict(zip(famcat.pn.map(key), famcat.pms_category)),
    ]

    def best_cat(pn: str) -> str:
        for src in cat_sources:
            v = (src.get(pn) or "").strip()
            if v:
                return v
        return "(no PMS category in any source)"
    APCOLS = ["codes_named", "parked_codes", "unresolved_codes", "n_series_bands", "band_status"]
    four4 = diff[~diff[APCOLS].apply(lambda r: any(NMR.search(str(v)) for v in r), axis=1)].copy()
    four4["k"] = four4.pn.map(key)

    pns = set(four4.k)
    hits: dict[str, list[str]] = {}

    def scan(df, pncol, label):
        if pncol not in df.columns:
            return
        d = df.copy()
        d["_k"] = d[pncol].map(key)
        for _, r in d[d._k.isin(pns)].iterrows():
            for c in d.columns:
                if c in ("_k", pncol):
                    continue
                v = str(r[c])
                if v and NMR.search(v):
                    hits.setdefault(r["_k"], []).append(f"{label}:{c}")

    scan(ap, "pn", "vehicle_band_applicability")
    scan(tc, "pn", "tonnage_capable_part_numbers")
    scan(ep, "pn", "epc_decode_nseries_banded")
    scan(b1, "pn", "epc_decode_batch1_20260919")
    scan(xr, "genuine_pn", "genuine_bvp_crossref(genuine_pn)")
    scan(xr, "bvp_pn", "genuine_bvp_crossref(bvp_pn)")
    scan(fam, "pn", "vehicle_family_bands")
    for r in dec2:
        k = key(r.get("pn", ""))
        if k in pns:
            for kk, vv in r.items():
                if NMR.search(str(vv)):
                    hits.setdefault(k, []).append(f"epc_decode_batch2_20260919:{kk}")

    epi = ep.set_index(ep.pn.map(key))
    ep_pns = set(epi.index)
    rows = []
    for _, r in four4.iterrows():
        k = r["k"]
        in_file = k in ep_pns
        file_band = ""
        eur_file = ""
        if in_file:
            e = epi.loc[k]
            if isinstance(e, pd.DataFrame):
                e = e.iloc[0]
            file_band = np_(e["tonnage_band"])
            eur_file = round(float(pd.to_numeric(e["eur_all_years"], errors="coerce") or 0), 2)
        nmr_found = sorted(set(hits.get(k, [])))
        if nmr_found:
            group, action = "parked (names NMR)", "MOVE TO PARKED - carries an NMR token"
        else:
            group = "free"
            if not in_file:
                action = "not in the published band file - no re-base possible here"
            elif file_band == r["ap_short"]:
                action = "already correct in the published band file"
            else:
                action = "would need re-basing in the published band file"
        rows.append({
            "pn": k,
            "pms_category": best_cat(r["pn"]) or "(no PMS category in any source)",
            "published_band_list": r["tc_short"],
            "in_published_band_file": "yes" if in_file else "no",
            "published_band_file_band": (file_band or "(no band in this file)") if in_file
                                       else "(not in this file)",
            "corrected_band": r["ap_short"] or "(no band - every code parked or unresolved)",
            "why_they_disagree": WHY.get((r["tc_short"], r["ap_short"]),
                                         "the published band list and the corrected mapping "
                                         "name different rungs on the same part number"),
            "eur_published_band_list_basis": round(float(pd.to_numeric(r["eur_tc"],
                                                                       errors="coerce") or 0), 2),
            "eur_corrected_mapping_basis": round(float(pd.to_numeric(r["eur_ap"],
                                                                     errors="coerce") or 0), 2),
            "eur_published_band_file_basis": eur_file,
            "hidden_nmr_token": "yes" if nmr_found else "no",
            "nmr_evidence": "; ".join(nmr_found),
            "group": group,
            "action": action,
            "mapping_codes_named": r["codes_named"],
            "mapping_parked_codes": r["parked_codes"],
            "mapping_band_status": r["band_status"],
        })

    out = pd.DataFrame(rows).sort_values("eur_corrected_mapping_basis",
                                         ascending=False).reset_index(drop=True)
    dest = INBOX / "PUBLISHED_BAND_PN_DIFF_44_2026-09-23.csv"
    out.to_csv(dest, index=False, encoding="utf-8")

    eur_ap = pd.to_numeric(out.eur_corrected_mapping_basis)
    free = out.hidden_nmr_token == "no"
    print(f"wrote {dest}")
    print(f"  rows                                    : {len(out)}")
    print(f"  euro (corrected mapping basis)          : EUR {eur_ap.sum():,.2f}")
    print(f"  hidden_nmr_token == yes                 : {int((~free).sum())}  "
          f"EUR {eur_ap[~free].sum():,.2f}")
    print(f"  hidden_nmr_token == no  (the true free) : {int(free.sum())}  "
          f"EUR {eur_ap[free].sum():,.2f}")
    print(f"  action counts                           : {out.action.value_counts().to_dict()}")
    print(f"  groups                                  : {out.group.value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
