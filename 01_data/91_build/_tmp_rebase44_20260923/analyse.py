"""Read-only census: reproduce the published-band contradiction and split it into
the parked NMR group and the 44 that are wrong either way.

Nothing is written to any derived file. Output is printed and optionally written to
the step folder here.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"

pd.set_option("display.width", 220)


def short(band: str) -> str:
    """'3.5t_N35' -> '3.5t'. Full band names use '_' only after the short token."""
    if not band:
        return ""
    return band.split("_")[0]


def norm_short_pipe(raw: str) -> str:
    """Normalise a pipe-joined full-name list into a sorted pipe of short names."""
    if not raw:
        return ""
    return "|".join(sorted(short(t) for t in raw.split("|") if t))


def norm_literal(raw: str) -> str:
    """Normalise a Python list literal of short names."""
    if not raw or raw == "[]":
        return ""
    try:
        items = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return "PARSE_ERROR:" + raw
    return "|".join(sorted(str(t) for t in items if t))


def main() -> int:
    tc = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str).fillna("")
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str).fillna("")
    ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")

    print("=" * 100)
    print("FILES")
    print("=" * 100)
    for name, d in (("tonnage_capable_part_numbers", tc), ("vehicle_band_applicability", ap),
                    ("epc_decode_nseries_banded", ep)):
        print(f"  {name:34s} rows={len(d):5d} cols={len(d.columns)}")

    # ---- the basis ----------------------------------------------------------
    merged = tc[["pn", "band_list", "eur", "exclusive_band", "n_bands", "category"]].merge(
        ap[["pn", "n_series_bands", "band_list", "eur", "exclusive_band", "parked_codes",
            "codes_named", "unresolved_codes", "band_status", "pms_category"]],
        on="pn", suffixes=("_tc", "_ap"), how="inner")

    eur_tc = pd.to_numeric(merged["eur_tc"])
    eur_ap = pd.to_numeric(merged["eur_ap"])
    print()
    print("  euro per PN identical between the two files:", bool((eur_tc - eur_ap).abs().le(0.01).all()),
          f"(max abs diff {float((eur_tc - eur_ap).abs().max()):.4f})")

    merged["ap_short"] = merged["n_series_bands"].map(norm_short_pipe)
    merged["tc_norm"] = merged["band_list_tc"].map(norm_literal)
    same = merged["ap_short"] == merged["tc_norm"]

    n_same, n_diff = int(same.sum()), int((~same).sum())
    print()
    print("=" * 100)
    print("THE SPLIT  (legacy band_list vs corrected n_series_bands, short names)")
    print("=" * 100)
    print(f"  identical : {n_same:4d} PNs   EUR {eur_ap[same].sum():>15,.2f}")
    print(f"  different : {n_diff:4d} PNs   EUR {eur_ap[~same].sum():>15,.2f}")
    print(f"  total     : {len(merged):4d} PNs   EUR {eur_ap.sum():>15,.2f}")

    diff = merged[~same].copy()

    # ---- every code-bearing column, not just the obvious ones ---------------
    code_cols_ap = ["codes_named", "unresolved_codes", "parked_codes", "band_reason",
                    "n_series_bands", "vehicle_bands", "exclusive_band", "band_labels",
                    "bands", "band_list_ap", "vehicle_groups"]
    code_cols_tc = ["parked_codes", "exclusive_band_tc", "vehicle_bands_tc", "vehicle_groups_tc"]

    def nmr_any(row) -> bool:
        for c in code_cols_ap + code_cols_tc:
            if c in row.index and re.search(r"\bNMR85?\b", str(row[c])):
                return True
        return False

    diff["nmr_token"] = diff.apply(nmr_any, axis=1)
    parked = diff[diff["nmr_token"]]
    free = diff[~diff["nmr_token"]]

    print()
    print("  of the different set:")
    print(f"    names NMR / NMR85 somewhere : {len(parked):4d} PNs   EUR {eur_ap[diff['nmr_token']].sum():>15,.2f}")
    print(f"    names neither               : {len(free):4d} PNs   EUR {eur_ap[~diff['nmr_token']].sum():>15,.2f}")

    # also check the published band file for NMR on those pns
    ep_codes = ["series_from_epc", "series_from_crossref", "registry_model_band", "series_all",
                "series_unresolved", "band_reason", "family", "tonnage_band", "family_resolution"]
    ep_idx = ep.set_index("pn")
    hidden = []
    for pn in free["pn"]:
        if pn in ep_idx.index:
            row = ep_idx.loc[pn]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            for c in ep_codes:
                if c in row.index and re.search(r"\bNMR85?\b", str(row[c])):
                    hidden.append((pn, c, str(row[c])))
    print()
    print(f"  hidden NMR tokens found in epc_decode_nseries_banded.csv on the 'neither' set: {len(hidden)}")
    for pn, c, v in hidden[:30]:
        print(f"    {pn}  {c} = {v[:120]}")

    # ---- shape table --------------------------------------------------------
    print()
    print("=" * 100)
    print("SHAPE TABLE  (all 176)")
    print("=" * 100)
    grp = diff.groupby(["tc_norm", "ap_short"], dropna=False).agg(
        pns=("pn", "size"), eur=("eur_ap", lambda s: pd.to_numeric(s).sum())).reset_index()
    grp = grp.sort_values("eur", ascending=False)
    for _, r in grp.iterrows():
        print(f"  {str(r['tc_norm']):24s} -> {str(r['ap_short']):24s} {r['pns']:4d}  EUR {r['eur']:>15,.2f}")

    # ---- the 5.5t-alone set in the legacy file ------------------------------
    print()
    print("=" * 100)
    print("LEGACY band_list == ['5.5t']  (the '16 rows / EUR 17,477.34' claim)")
    print("=" * 100)
    alone = tc[tc["band_list"] == "['5.5t']"].copy()
    alone_ap = alone.merge(ap[["pn", "exclusive_band", "n_series_bands", "parked_codes",
                               "codes_named", "unresolved_codes", "pms_category"]], on="pn",
                           how="left", suffixes=("", "_ap"))
    excl = (alone_ap["exclusive_band"] == "3.5t_N35").sum()
    print(f"  rows whose band_list == ['5.5t']        : {len(alone)}")
    print(f"  euro on those rows                      : EUR {pd.to_numeric(alone['eur']).sum():,.2f}")
    print(f"  carry exclusive_band == 3.5t_N35        : {int(excl)}")
    print(f"  carry '3.5t' anywhere in band_list      : {int(alone['band_list'].str.contains('3.5t').sum())}")
    print()
    print(alone_ap[["pn", "pms_category", "band_list", "eur", "n_series_bands",
                    "exclusive_band", "codes_named", "parked_codes"]].to_string(index=False))

    # ---- 16-row claim against the applicability table -----------------------
    print()
    print("  cross-check: rows in vehicle_band_applicability whose short list is '5.5t' only")
    ap55 = ap[ap["n_series_bands"].map(norm_short_pipe) == "5.5t"]
    print(f"    count {len(ap55)}   EUR {pd.to_numeric(ap55['eur']).sum():,.2f}")
    if len(ap55):
        print(ap55[["pn", "n_series_bands", "exclusive_band", "eur", "parked_codes"]].to_string(index=False))

    if OUT.exists():
        free.to_csv(OUT / "_free_candidates.csv", index=False)
        parked.to_csv(OUT / "_parked_candidates.csv", index=False)
        diff.to_csv(OUT / "_all_diff_176.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
