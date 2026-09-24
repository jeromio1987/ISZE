"""Which column set makes the 132/44 split? Sweep every code-bearing column in both
the published band file and the corrected mapping, and report the split under each
definition. Read only.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SCR = ROOT / "01_data" / "91_build" / "_tmp_rebase44_20260923"

pd.set_option("display.width", 260)
pd.set_option("display.max_colwidth", 60)


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


def main() -> int:
    tc = pd.read_csv(SCR / "tc_frozen_HEAD.csv", dtype=str).fillna("")
    ap = pd.read_csv(SCR / "ap_frozen_HEAD.csv", dtype=str).fillna("")
    ep = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")

    m = tc[["pn", "band_list", "eur", "category", "exclusive_band"]].merge(
        ap[["pn", "n_series_bands", "exclusive_band", "eur", "parked_codes", "codes_named",
            "unresolved_codes", "band_status", "band_reason", "vehicle_bands",
            "vehicle_type_label"]],
        on="pn", suffixes=("_tc", "_ap"), how="inner")
    epx = ep.add_prefix("ep_")
    m = m.merge(epx, left_on="pn", right_on="ep_pn", how="left")

    m["ap_short"] = m["n_series_bands"].map(norm_pipe)
    m["tc_short"] = m["band_list"].map(norm_literal)
    diff = m[m["ap_short"] != m["tc_short"]].copy()
    eur = pd.to_numeric(diff["eur_ap"])
    print(f"176 check: {len(diff)} rows  EUR {eur.sum():,.2f}")
    print(f"how many of the 176 are present in the published band file: {diff['ep_pn'].notna().sum()}")
    print(f"  of those, in_n_series_family == yes: {int((diff['ep_in_n_series_family'] == 'yes').sum())}")

    defs = {
        "ap codes_named+unresolved+parked": ["codes_named", "unresolved_codes", "parked_codes"],
        "ap band_reason (series prose)": ["band_reason"],
        "ep series_from_epc+crossref": ["ep_series_from_epc", "ep_series_from_crossref"],
        "ep series_all": ["ep_series_all"],
        "ep series_all+unresolved": ["ep_series_all", "ep_series_unresolved"],
        "ep all series + band_reason": ["ep_series_from_epc", "ep_series_from_crossref",
                                        "ep_series_all", "ep_series_unresolved", "ep_band_reason"],
        "EVERY code column in both files": [
            "codes_named", "unresolved_codes", "parked_codes", "band_reason", "vehicle_bands",
            "exclusive_band_ap", "n_series_bands", "band_list",
            "ep_series_from_epc", "ep_series_from_crossref", "ep_registry_model_band",
            "ep_series_all", "ep_series_unresolved", "ep_band_reason", "ep_tonnage_band"],
    }
    print()
    print("=" * 110)
    print("SPLIT UNDER EACH DEFINITION OF 'names NMR / NMR85'")
    print("=" * 110)
    for label, cols in defs.items():
        cols = [c for c in cols if c in diff.columns]
        mask = diff[cols].apply(
            lambda r: any(re.search(r"\bNMR85?\b", str(v)) for v in r), axis=1)
        print(f"  {label:36s}  NMR-bearing {int(mask.sum()):4d}  EUR {eur[mask].sum():>15,.2f}"
              f"   |  neither {int((~mask).sum()):4d}  EUR {eur[~mask].sum():>15,.2f}")

    # who are the 24 my strict sweep found, and the 152
    strict_cols = ["codes_named", "unresolved_codes", "parked_codes", "band_reason", "vehicle_bands",
                   "exclusive_band_ap", "n_series_bands", "band_list", "ep_series_from_epc",
                   "ep_series_from_crossref", "ep_registry_model_band", "ep_series_all",
                   "ep_series_unresolved", "ep_band_reason", "ep_tonnage_band"]
    strict = diff[strict_cols].apply(lambda r: any(re.search(r"\bNMR85?\b", str(v)) for v in r), axis=1)
    print()
    print("=" * 110)
    print("THE 24 THAT NAME NMR UNDER THE STRICT SWEEP")
    print("=" * 110)
    print(diff.loc[strict, ["pn", "category", "tc_short", "ap_short", "eur_ap", "codes_named",
                            "parked_codes", "ep_series_all", "ep_series_unresolved",
                            "ep_tonnage_band"]].to_string(index=False))

    print()
    print("=" * 110)
    print("SAMPLE OF THE 152 THE STRICT SWEEP CALLS 'NEITHER' (first 20)")
    print("=" * 110)
    print(diff.loc[~strict, ["pn", "category", "tc_short", "ap_short", "eur_ap", "codes_named",
                             "unresolved_codes", "parked_codes", "ep_series_from_epc",
                             "ep_series_from_crossref", "ep_series_all",
                             "ep_series_unresolved"]].head(20).to_string(index=False))

    # For the 152, does any of them carry NMR in ANY column of either file at all?
    print()
    print("=" * 110)
    print("FULL-TEXT NMR SWEEP over the whole merged row, on the 'neither' set")
    print("=" * 110)
    free = diff[~strict]
    allcols = [c for c in diff.columns if not c.startswith("ep_") or True]
    fulltext = free[allcols].apply(
        lambda r: bool(re.search(r"NMR85?", " ".join(str(v) for v in r.values))), axis=1)
    print(f"  of the {len(free)} 'neither' rows, rows containing the literal 'NMR' anywhere: "
          f"{int(fulltext.sum())}")
    if fulltext.any():
        print(free.loc[fulltext, ["pn", "tc_short", "ap_short", "eur_ap"]].head(20).to_string(index=False))

    # distribution of where NMR shows up
    print()
    print("  per-column NMR hit counts across all 176:")
    for c in allcols:
        n = int(diff[c].apply(lambda v: bool(re.search(r"NMR85?", str(v)))).sum())
        if n:
            print(f"    {c:34s} {n:4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
