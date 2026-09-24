"""Definitive, read-only reproduction of the published-band contradiction.

Basis pinned to the frozen legacy table (the version that carries the
'band values frozen at the pre-2026-09-23 basis' note) against the corrected
mapping. Prints every figure; writes nothing outside this scratch folder.

Regex note: the token is NMR or NMR85, so the pattern is \bNMR(?:85)?\b.
`NMR85?` is WRONG — it matches the literal "NMR8", never plain "NMR".
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"

NMR = re.compile(r"\bNMR(?:85)?\b")

pd.set_option("display.width", 250)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def short(band: str) -> str:
    return band.split("_")[0] if band else ""


def norm_pipe(raw: str) -> str:
    if not raw:
        return ""
    return "|".join(sorted(short(t) for t in str(raw).split("|") if t))


def norm_literal(raw: str) -> str:
    if not raw or raw == "[]":
        return ""
    try:
        items = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return "PARSE_ERROR"
    return "|".join(sorted(str(t) for t in items if t))


def main() -> int:
    tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
    ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")
    ap_live = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str).fillna("")
    ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")

    print("=" * 104)
    print("BASIS CHECK")
    print("=" * 104)
    print(f"  legacy table (frozen)      rows={len(tc):5d}  sha={sha(SCR / 'tc_frozen_HEAD.csv')[:20]}")
    print(f"  corrected mapping (frozen) rows={len(ap):5d}  sha={sha(SCR / 'ap_frozen_HEAD.csv')[:20]}")
    print(f"  corrected mapping (live)   rows={len(ap_live):5d}  sha={sha(DER / 'vehicle_band_applicability.csv')[:20]}")
    print(f"  published band file (live) rows={len(ep):5d}  sha={sha(DER / 'epc_decode_nseries_banded.csv')[:20]}")

    # does the live corrected mapping differ from frozen on n_series_bands / eur?
    a = ap[["pn", "n_series_bands", "exclusive_band", "eur"]].rename(
        columns={"n_series_bands": "nb_frozen", "exclusive_band": "exc_frozen", "eur": "eur_frozen"})
    b = ap_live[["pn", "n_series_bands", "exclusive_band", "eur"]].rename(
        columns={"n_series_bands": "nb_live", "exclusive_band": "exc_live", "eur": "eur_live"})
    j = a.merge(b, on="pn", how="outer", indicator=True)
    print(f"  pn sets identical between frozen and live mapping: {bool((j['_merge'] == 'both').all())}")
    if (j["_merge"] == "both").all():
        print(f"  n_series_bands differs on : {int((j.nb_frozen != j.nb_live).sum())} rows")
        print(f"  exclusive_band differs on : {int((j.exc_frozen != j.exc_live).sum())} rows")
        print(f"  eur differs on            : {int((pd.to_numeric(j.eur_frozen).round(2) != pd.to_numeric(j.eur_live).round(2)).sum())} rows")

    m = tc[["pn", "band_list", "eur", "category", "exclusive_band"]].merge(
        ap[["pn", "n_series_bands", "exclusive_band", "eur", "parked_codes", "codes_named",
            "unresolved_codes", "band_status", "band_reason"]],
        on="pn", suffixes=("_tc", "_ap"), how="inner")
    print(f"  shared part numbers       : {len(m)}")

    eur_ap = pd.to_numeric(m["eur_ap"])
    m["ap_short"] = m["n_series_bands"].map(norm_pipe)
    m["tc_short"] = m["band_list"].map(norm_literal)
    same = m["ap_short"] == m["tc_short"]

    print()
    print("=" * 104)
    print("GROUP 1 — the three headline groups")
    print("=" * 104)
    print(f"  identical   : {int(same.sum()):4d} PNs   EUR {eur_ap[same].sum():>16,.2f}")
    print(f"  different   : {int((~same).sum()):4d} PNs   EUR {eur_ap[~same].sum():>16,.2f}")
    print(f"  total       : {len(m):4d} PNs   EUR {eur_ap.sum():>16,.2f}")

    diff = m[~same].copy()

    # NMR token search across EVERY code-bearing column
    cols = ["codes_named", "unresolved_codes", "parked_codes", "band_reason",
            "n_series_bands", "exclusive_band_ap", "band_status",
            "exclusive_band_tc", "band_list"]
    def hits(row):
        return [c for c in cols if c in row.index and NMR.search(str(row[c]))]

    diff["nmr_cols"] = diff.apply(hits, axis=1)
    diff["is_nmr"] = diff["nmr_cols"].map(bool)
    parked = diff[diff["is_nmr"]]
    free = diff[~diff["is_nmr"]]

    print()
    print("  parked (names NMR / NMR85 somewhere in a code column)")
    print(f"    part numbers : {len(parked):4d}   EUR {pd.to_numeric(parked['eur_ap']).sum():>16,.2f}")
    print("  free (names neither)")
    print(f"    part numbers : {len(free):4d}   EUR {pd.to_numeric(free['eur_ap']).sum():>16,.2f}")

    # second, independent token sweep: raw text of the whole diffusion rows
    raw_nmr = diff.apply(lambda r: bool(NMR.search(" ".join(str(v) for v in r.values))), axis=1)
    print()
    print(f"  independent raw-text sweep for NMR on all 176 rows : {int(raw_nmr.sum())} rows")
    print(f"  agrees with the column sweep                       : {bool((raw_nmr == diff['is_nmr']).all())}")

    # cross-check in the published band file's own code columns
    ep_cols = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
               "series_unresolved", "band_reason", "family", "tonnage_band", "pms_category"]
    epi = ep.set_index("pn")
    hidden = []
    for pn in free["pn"]:
        if pn in epi.index:
            r = epi.loc[pn]
            if isinstance(r, pd.DataFrame):
                r = r.iloc[0]
            for c in ep_cols:
                if c in r.index and NMR.search(str(r[c])):
                    hidden.append((pn, c, str(r[c])[:70]))
    print(f"  hidden NMR tokens in the published band file on the 'free' set : {len(hidden)}")
    for h in hidden:
        print(f"    {h[0]}  {h[1]} = {h[2]}")

    print()
    print("=" * 104)
    print("GROUP 2 — shape table for all 176")
    print("=" * 104)
    g = diff.groupby(["tc_short", "ap_short"]).agg(
        pns=("pn", "size"), eur=("eur_ap", lambda s: pd.to_numeric(s).sum())).reset_index()
    for _, r in g.sort_values("eur", ascending=False).iterrows():
        print(f"  {r['tc_short']:26s} -> {r['ap_short']:26s} {r['pns']:4d}   EUR {r['eur']:>14,.2f}")

    print()
    print("=" * 104)
    print("GROUP 3 — legacy band_list == ['5.5t']  and the exclusive_band count")
    print("=" * 104)
    alone = tc[tc["band_list"] == "['5.5t']"].copy()
    al = alone.merge(ap[["pn", "exclusive_band", "n_series_bands", "parked_codes", "codes_named",
                         "unresolved_codes", "band_status"]], on="pn", how="left")
    print(f"  rows with band_list == ['5.5t']       : {len(alone)}")
    print(f"  euro on those rows                    : EUR {pd.to_numeric(alone['eur']).sum():,.2f}")
    print(f"  exclusive_band == '3.5t_N35'          : {int((al['exclusive_band'] == '3.5t_N35').sum())}")
    print(f"  '3.5t' anywhere in band_list          : {int(alone['band_list'].str.contains('3.5t').sum())}")
    print(f"  eur on the exclusive_band == 3.5t_N35 subset: "
          f"EUR {pd.to_numeric(al.loc[al['exclusive_band'] == '3.5t_N35', 'eur']).sum():,.2f}")
    print()
    print(al[["pn", "category", "band_list", "eur", "n_series_bands", "exclusive_band",
              "codes_named", "parked_codes", "band_status"]].to_string(index=False))

    print()
    print("  cross-check against the LIVE corrected mapping (post-6:50 edit):")
    al2 = alone.merge(ap_live[["pn", "exclusive_band", "n_series_bands"]], on="pn", how="left")
    print(f"    exclusive_band == '3.5t_N35' : {int((al2['exclusive_band'] == '3.5t_N35').sum())}")

    print()
    print("=" * 104)
    print("GROUP 4 — the 235-row published band file: what the 176/44 look like in it")
    print("=" * 104)
    print(f"  in_n_series_family: {ep.in_n_series_family.value_counts().to_dict()}")
    print(f"  tonnage_band shapes:")
    for k, v in ep.tonnage_band.value_counts().items():
        print(f"    {k if k else '(blank)':48s} {v:4d}   EUR {pd.to_numeric(ep.loc[ep.tonnage_band == k, 'eur_all_years']).sum():>14,.2f}")

    fam = ep[ep.in_n_series_family == "yes"]
    p3 = fam[fam.tonnage_band == "3.5t_N35|5.5t_N50_N55|7.5t_N50_N62_N75"]
    p2 = fam[fam.tonnage_band == "3.5t_N35|5.5t_N50_N55"]
    print()
    print(f"  in-family exactly 3.5t|5.5t|7.5t : {len(p3):3d}   EUR {pd.to_numeric(p3.eur_all_years).sum():>14,.2f}")
    print(f"  in-family exactly 3.5t|5.5t      : {len(p2):3d}   EUR {pd.to_numeric(p2.eur_all_years).sum():>14,.2f}")
    print(f"  in-family carrying 5.5t anywhere : {int(fam.tonnage_band.str.contains('5.5t').sum())}")
    print(f"  in-family 5.5t alone             : {int((fam.tonnage_band == '5.5t_N50_N55').sum())}")

    keep = free[["pn", "category", "tc_short", "ap_short", "eur_ap", "band_status_ap",
                 "parked_codes", "codes_named"]]
    keep.to_csv(SCR / "_free_candidates.csv", index=False)
    parked[["pn", "tc_short", "ap_short", "eur_ap", "nmr_cols"]].to_csv(
        SCR / "_parked_candidates.csv", index=False)
    print(f"\n  scratch written: _free_candidates.csv ({len(keep)}), _parked_candidates.csv ({len(parked)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
