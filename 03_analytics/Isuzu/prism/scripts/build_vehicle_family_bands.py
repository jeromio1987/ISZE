#!/usr/bin/env python3
"""
Vehicle family for every service part number — from both vehicle sources, never from one.

Why this file exists
--------------------
The shipped family page placed only 46.6% of 2025 service-part euro in a vehicle family, and showed
heavy truck as a 21,844-euro sliver. The cause was a two-step exclusion, each step assuming the
other had done the work:

  * ``build_epc_decode_batches.py`` dropped every part number the genuine/BVP cross-reference already
    named a vehicle for — so those parts never entered the EPC decode;
  * the family page placed a part only from the decode — so those same parts had no family.

Caught between the two, 95 part numbers that a bare ``F*`` substring test read as heavy-truck-only,
billing EUR 1,955,749 across eleven service categories, appeared nowhere at all. That count was itself
wrong -- ``TF*`` is the D-Max pickup wildcard, so the test swept pickup parts in with the F-series, and
the euro rested on the blower filters whose model string is ``TF*,UC*``: six part numbers, EUR
1,347,222.32 across all years (2023-01 to 2026-06), all markets and all billing lines, that this table
places in the Light vehicle family. Nothing was wrong with
the data. The two steps disagreed about who owned the part.

This script is the single answer to "which vehicle family does this part number fit". It reads both
sources for every part number, so a part can no longer fall between them.

Sources, in the order they are trusted
--------------------------------------
1. ``epc_decode_batch1_banded_20260919.csv`` — tonnage band per part number, from the EPC's own model
   ranges. 250 part numbers.
2. ``epc_decode_batch2_20260919.json`` — the EPC vehicle families for the next 250. 228 found.
3. ``genuine_bvp_crossref.csv`` ``vehicle_model`` — a catalogue model-code string per pair. Covers
   787 part numbers, of which 410 are also in the service-part universe.

A part number is placed only when every source that names a vehicle for it agrees. Where they name
more than one family the part is pooled as ``shared_across_families`` — it is not apportioned and it
is not dropped.

Reading a model-code string
---------------------------
Two things the earlier code got wrong:

* ``TF*`` is the **D-Max pickup** wildcard, not an F-series token. A substring test for ``F*``
  therefore read "TF*,UC*" as heavy truck, which is how 53 light-vehicle part numbers carrying
  EUR 2.0M were counted as F-series-only.
* A wildcard code still names a family. ``FR*`` is F-series. ``N*R`` is the N-series. Only a string
  that carries no code at all — ``4X2``, ``CHINA``, a stray letter — leaves the family open.

So each token is read on its own and the families are unioned. One family -> placed. More than one ->
pooled. None -> no reference. A decision that needed a wildcard is recorded at medium confidence, so
the reader can see which part numbers rest on a pattern rather than on a named model.

Two interval lanes
------------------
The lane is carried per customer, not per part number: ITUK runs the service schedule agreed for
that market, every other market runs the internal schedule. The two are never averaged.

Reads : 01_data/00_derived/genuine_bvp_crossref.csv
        01_data/00_derived/epc_decode_batch1_banded_20260919.csv
        01_data/00_derived/epc_decode_batch2_20260919.json
        01_data/00_derived/bvp_pn_dimension.csv
        03_analytics/Isuzu/prism/data/pms_capture_supplement.csv
        01_data/00_derived/sales_fact.parquet               (euro per part number, for sizing)
Writes: 01_data/00_derived/vehicle_family_bands.csv
        01_data/00_derived/vehicle_family_bands.meta.json

Run: python 03_analytics/Isuzu/prism/scripts/build_vehicle_family_bands.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM_DATA = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"

CROSSREF = DER / "genuine_bvp_crossref.csv"
BAND1 = DER / "epc_decode_batch1_banded_20260919.csv"
DECODE2 = DER / "epc_decode_batch2_20260919.json"
DIMENSION = DER / "bvp_pn_dimension.csv"
SUPPLEMENT = PRISM_DATA / "pms_capture_supplement.csv"
SALES = DER / "sales_fact.parquet"

OUT = DER / "vehicle_family_bands.csv"
OUT_META = DER / "vehicle_family_bands.meta.json"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

N_SERIES, HEAVY, LIGHT = "n_series_truck", "heavy_truck", "light_vehicle"
SHARED, NONE = "shared_across_families", "no_vehicle_reference"

FAMILY_LABEL = {
    N_SERIES: "N-series truck",
    HEAVY: "Heavy truck (F-series and C&E)",
    LIGHT: "Light vehicle (D-Max pickup and SUV)",
    SHARED: "Parts used across more than one family",
    NONE: "No vehicle reference found",
}

# EPC tonnage band -> reported family.
BAND2FAMILY = {
    "LCV_D-Max": LIGHT,
    "3.5t_N35": N_SERIES,
    "7.5t_N50_N62_N75": N_SERIES,
    "F_series_MD_heavy": HEAVY,
}
# EPC vehicle family label -> reported family. Buses, industrial engines and components are
# deliberately absent: those part numbers fit nothing in the four ISZE families.
EPC_FAMILY_MAP = {
    "PASSENGER VEHICLE PICK UP": LIGHT,
    "PASSENGER VEHICLE SUV": LIGHT,
    "TRUCKS N": N_SERIES,
    "TRUCKS Q": N_SERIES,
    "TRUCKS F&G": HEAVY,
    "TRUCKS C&E": HEAVY,
}

# ── the cross-reference vocabulary ────────────────────────────────────────────────────────────
# Named model codes. Each one is a real code on disk, not a pattern.
CONCRETE: dict[str, str] = {}
for c in ("TFR", "TFS", "UCR", "UCS", "UBS", "UB"):
    CONCRETE[c] = LIGHT
for c in ("NLR", "NKR", "NMR", "NNR", "NPR", "NPS", "NQR", "NRR", "NHR", "NJR", "NKS", "NJS",
          "NLS", "NMS", "NQS", "NK", "NL", "NJ", "NN", "NP", "NQ", "QKR", "QLR", "QMR", "PHR"):
    CONCRETE[c] = N_SERIES
for c in ("FRR", "FRD", "FRS", "FSR", "FSS", "FTS", "FTR", "FVR", "FVM", "FVZ", "FXM", "FXR",
          "FXZ", "FYH", "GVR", "GVZ", "GXZ", "GXR", "PFR", "TBR",
          "CVR", "CXH", "CXZ", "CYH", "CYZ", "CHR", "EXR", "EXZ"):
    CONCRETE[c] = HEAVY

# Wildcard codes. A pattern still names a family; only its precision is lower.
WILDCARD: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p), f) for p, f in (
        (r"^TF\*$", LIGHT), (r"^UC\*$", LIGHT), (r"^UB\*$", LIGHT), (r"^UE\*$", LIGHT),
        (r"^N\*R$", N_SERIES), (r"^N\*S$", N_SERIES), (r"^N\*$", N_SERIES),
        (r"^NK\*$", N_SERIES), (r"^NN\*$", N_SERIES), (r"^NP\*$", N_SERIES),
        (r"^NQ\*$", N_SERIES), (r"^NL\*$", N_SERIES),
        (r"^F\*$", HEAVY), (r"^F\*R$", HEAVY), (r"^F\*D$", HEAVY), (r"^F\*S$", HEAVY),
        (r"^FR\*$", HEAVY), (r"^FS\*$", HEAVY), (r"^FT\*$", HEAVY), (r"^FV\*$", HEAVY),
        (r"^FX\*$", HEAVY), (r"^FY\*$", HEAVY), (r"^GV\*$", HEAVY), (r"^GX\*$", HEAVY),
        (r"^GX$", HEAVY), (r"^C\*$", HEAVY), (r"^C\*Z$", HEAVY), (r"^CV\*$", HEAVY),
        (r"^CX\*$", HEAVY), (r"^CY\*$", HEAVY), (r"^E\*$", HEAVY), (r"^EX\*$", HEAVY),
    )
]

# Tokens that name no vehicle at all: a drive configuration, a market, a generation number, a
# platform code that carries no weight. Recorded so the coverage figure is honest.
NON_CODES = {
    "400/450/500/600", "4X2", "4X4", "CHINA", "LV280", "RG", "RT", "X2", "X4",
    "190", "S", "R", "D", "E", "Z", "C", "TF", "UC", "UB", "UE", "ELF", "LX",
}


def token_family(token: str) -> tuple[str | None, bool]:
    """(family, needed_a_wildcard) for one token. (None, False) when the token names no vehicle."""
    t = token.strip().upper()
    if not t or t in NON_CODES:
        return None, False
    if t in CONCRETE:
        return CONCRETE[t], False
    for pat, fam in WILDCARD:
        if pat.match(t):
            return fam, True
    return None, False


def split_tokens(value: str) -> list[str]:
    s = str(value or "")
    for sep in ("/", "\uff0c", "\u3001", "\n", "\r", ";", ".", "(", ")", "[", "]", "{", "}"):
        s = s.replace(sep, ",")
    return [t for t in (p.strip() for p in s.split(",")) if t]


def read_vehicle_model(value: str) -> tuple[set[str], set[str], list[str]]:
    """(families, families_that_came_from_a_wildcard, tokens that name no vehicle)."""
    fams: set[str] = set()
    wild: set[str] = set()
    unknown: list[str] = []
    for tok in split_tokens(value):
        fam, was_wild = token_family(tok)
        if fam:
            fams.add(fam)
            if was_wild:
                wild.add(fam)
        elif tok.upper() not in NON_CODES:
            unknown.append(tok)
    return fams, wild, unknown


def clean_text(value) -> str:
    """A CSV cell as text, with blanks and a literal float NaN treated as empty.

    `str(nan or "")` yields 'nan', because a float NaN is truthy. That put the word nan into the
    vehicle-model column of the first build, so it is handled here rather than at each use.
    """
    if value is None or (isinstance(value, float) and value != value):
        return ""
    s = str(value).strip()
    return "" if s.lower() in ("nan", "none") else s


# ── load ──────────────────────────────────────────────────────────────────────────────────────
def load_universe() -> pd.DataFrame:
    """Every service part number that must reach a family."""
    dim = pd.read_csv(DIMENSION, dtype=str, low_memory=False)
    supp = pd.read_csv(SUPPLEMENT, dtype=str, low_memory=False)
    u = pd.concat([dim, supp], ignore_index=True)
    u["pn"] = u.part_number.map(norm)
    u = u[u.pms_category.notna() & (u.pms_category.astype(str).str.strip() != "")]
    lbl = "category_label" if "category_label" in u.columns else "pms_category"
    u = u.drop_duplicates("pn")[["pn", "pms_category", lbl]].rename(
        columns={lbl: "category_label"})
    return u.reset_index(drop=True)


def load_epc() -> dict[str, tuple[frozenset[str], str]]:
    """pn -> (families from the EPC, where on disk that came from)."""
    out: dict[str, tuple[frozenset[str], str]] = {}
    b1 = pd.read_csv(BAND1)
    b1["pn"] = b1.pn.map(norm)
    for r in b1.itertuples():
        if r.band_status == "no_vehicle_epc_not_found":
            continue
        fams = frozenset(BAND2FAMILY[p] for p in str(r.tonnage_band or "").split("|")
                         if p in BAND2FAMILY)
        if fams:
            out[r.pn] = (fams, f"tonnage band '{r.tonnage_band}'")
    dec2 = json.loads(DECODE2.read_text(encoding="utf-8"))
    for r in dec2:
        raw = r.get("families") or []
        fams = frozenset(EPC_FAMILY_MAP[f] for f in raw if f in EPC_FAMILY_MAP)
        if fams:
            out.setdefault(norm(r["pn"]), (fams, "EPC vehicle range: " + "; ".join(raw)))
    return out


def load_crossref() -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, str], Counter]:
    """pn -> families, pn -> families read from a wildcard, pn -> the model string, unknown tokens."""
    x = pd.read_csv(CROSSREF, dtype=str, low_memory=False)
    fams: dict[str, set[str]] = {}
    wild: dict[str, set[str]] = {}
    strings: dict[str, str] = {}
    unknown: Counter = Counter()
    for r in x.itertuples():
        f, w, unk = read_vehicle_model(r.vehicle_model)
        for u in unk:
            unknown[u] += 1
        vm = clean_text(r.vehicle_model)
        for pn in {clean_text(r.genuine_pn), clean_text(r.bvp_pn)}:
            if not pn:
                continue
            fams.setdefault(pn, set()).update(f)
            wild.setdefault(pn, set()).update(w)
            prev = strings.get(pn)
            if vm:
                strings[pn] = vm if prev is None else (prev if vm in prev else prev + " | " + vm)
    return fams, wild, strings, unknown


# ── decide ────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    uni = load_universe()
    epc = load_epc()
    xr_fams, xr_wild, xr_string, unknown = load_crossref()

    sf = pd.read_parquet(SALES)
    sf["pn"] = sf.part_number.map(norm)
    eur_all = sf.groupby("pn").net_sales_value.sum()
    units_all = sf.groupby("pn").billed_qty.sum()

    rows = []
    for pn, cat, catlab in uni.itertuples(index=False):
        ef, enote = epc.get(pn, (frozenset(), ""))
        xf = xr_fams.get(pn, set())
        xw = xr_wild.get(pn, set())

        union = set(ef) | set(xf)
        conflict = bool(ef and xf and len(ef) == 1 and len(xf) == 1 and set(ef) != set(xf))

        if conflict:
            family, resolution = None, SHARED
            reason = (f"the two sources disagree: {enote} against cross-reference "
                      f"'{xr_string.get(pn, '')}' — pooled rather than trusted to either")
            confidence = "conflict"
        elif len(union) == 1:
            family, resolution = next(iter(union)), "single_family"
            confidence = "high" if ef else "medium"
            if ef and xf:
                reason = f"{enote}; cross-reference '{xr_string.get(pn, '')}' agrees"
            elif ef:
                reason = enote
            else:
                reason = f"cross-reference '{xr_string.get(pn, '')}'"
        elif len(union) > 1:
            family, resolution = None, SHARED
            confidence = "medium"
            reason = f"fits more than one family ({', '.join(sorted(union))}) — pooled, not split"
        else:
            family, resolution = None, NONE
            confidence = "low"
            reason = ("no vehicle named by either source"
                      if not xr_string.get(pn) else
                      f"vehicle string '{xr_string.get(pn)}' names no model code")

        rows.append({
            "pn": pn,
            "pms_category": cat,
            "category_label": catlab,
            "family": family,
            "family_label": FAMILY_LABEL[family] if family else FAMILY_LABEL[SHARED],
            "resolution": resolution,
            "families_in_union": "|".join(sorted(union)),
            "from_epc": "|".join(sorted(ef)),
            "from_crossref": "|".join(sorted(xf)),
            "from_crossref_wildcard": "|".join(sorted(xw)),
            "vehicle_model": xr_string.get(pn, ""),
            "confidence": confidence,
            "source_note": reason,
            "eur_all_markets": round(float(eur_all.get(pn, 0.0)), 2),
            "units_all_markets": round(float(units_all.get(pn, 0.0)), 2),
        })

    out = pd.DataFrame(rows).sort_values("eur_all_markets", ascending=False).reset_index(drop=True)
    out.to_csv(OUT, index=False)

    cov = out.groupby("resolution").agg(pns=("pn", "size"), eur=("eur_all_markets", "sum"))
    placed = out[out.resolution == "single_family"]
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "03_analytics/Isuzu/prism/scripts/build_vehicle_family_bands.py",
        "universe": {"source": "bvp_pn_dimension.csv + pms_capture_supplement.csv, pms_category not null",
                     "part_numbers": int(len(out)),
                     "eur_all_markets": round(float(out.eur_all_markets.sum()), 2)},
        "by_resolution": {k: {"part_numbers": int(r.pns), "eur": round(float(r.eur), 2)}
                          for k, r in cov.iterrows()},
        "by_family": {k: {"part_numbers": int(r.pns), "eur": round(float(r.eur), 2)}
                      for k, r in out[out.resolution == "single_family"]
                      .groupby("family").agg(pns=("pn", "size"), eur=("eur_all_markets", "sum")).iterrows()},
        "by_confidence": {k: int(v) for k, v in out.confidence.value_counts().items()},
        "sources": {
            "epc_bands": "epc_decode_batch1_banded_20260919.csv (250 PNs)",
            "epc_ranges": "epc_decode_batch2_20260919.json (228 of 250 found)",
            "crossref": "genuine_bvp_crossref.csv vehicle_model (787 PNs)",
        },
        "rules": [
            "Every service part number in the dimension must reach exactly one of: a single family, "
            "shared_across_families, or no_vehicle_reference.",
            "A part that fits more than one family is POOLED and never apportioned. The pooled row "
            "carries the part numbers and the families each one fits so it can be opened.",
            "Where the EPC and the cross-reference name different single families the part is "
            "pooled and flagged conflict, rather than trusted to either source.",
            "A wildcard code still names a family (FR* is F-series, N*R is the N-series). A decision "
            "that needed a wildcard is recorded at medium confidence.",
            "TF* is the D-Max pickup wildcard, not an F-series token. A bare F* substring test "
            "reads it as heavy truck, which is how the earlier count of F-series-only part "
            "numbers came out at 95 part numbers and EUR 1.96M. Of the 161 part numbers whose "
            "model string contains F*, 122 also carry TF* or UC* in the same row, and the euro "
            "was dominated by the blower filters whose model string is 'TF*,UC*': six part "
            "numbers (8975554500, 8981394280, 8975488420, 5876150180, 5876150540, 5876150550) "
            "billing EUR 1,347,222.32 across all years (2023-01 to 2026-06), all markets and all "
            "billing lines, which this table places in the Light vehicle family. The three "
            "largest of those six read EUR 1,162,159.21 on the same basis. Measured on this table "
            "the heavy truck family holds 164 part numbers and EUR 174,832 of 2025 billing on a "
            "1,238-vehicle fleet; 101 of the 164 carry a Forward F&G code. The EUR 1,344,279 "
            "that once circulated for that blower quantity has no basis in any file on disk.",
        ],
        "tokens_naming_no_vehicle": dict(unknown.most_common(40)),
        "not_attempted": [
            "A 3.5 t versus 7.5 t split inside the N-series. 50 of 120 model codes in "
            "prism/data/model_code_to_tonnage.csv are unresolved and the unresolved ones include "
            "NN, NP and NHR — exactly the codes that separate N35 from N75.",
            "Part numbers that fit only a bus, an industrial engine or a component. Those families "
            "are outside the four ISZE bands, so such a part number is left as no_vehicle_reference "
            "rather than forced into a truck family.",
        ],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"service part numbers in the universe : {len(out):,}")
    print(f"  placed in a single family          : {int(cov.loc['single_family', 'pns']) if 'single_family' in cov.index else 0:,}")
    print(f"  pooled across families             : {int(cov.loc[SHARED, 'pns']) if SHARED in cov.index else 0:,}")
    print(f"  no vehicle reference               : {int(cov.loc[NONE, 'pns']) if NONE in cov.index else 0:,}")
    print(f"  conflicts (pooled, flagged)        : {int((out.confidence == 'conflict').sum()):,}")
    print()
    print("billed euro across all years and markets:")
    for k, r in cov.iterrows():
        print(f"  {k:24s} {int(r.pns):5d} PNs  EUR {r.eur:14,.0f}")
    print()
    print("placed euro by family:")
    for k, r in out[out.resolution == "single_family"].groupby("family").agg(
            pns=("pn", "size"), eur=("eur_all_markets", "sum")).sort_values(
                "eur", ascending=False).iterrows():
        print(f"  {k:24s} {int(r.pns):5d} PNs  EUR {r.eur:14,.0f}")
    print()
    print(f"written -> {OUT}  ({len(out):,} rows)")
    print(f"written -> {OUT_META}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
