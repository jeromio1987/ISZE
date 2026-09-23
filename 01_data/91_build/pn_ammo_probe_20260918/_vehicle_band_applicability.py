#!/usr/bin/env python3
"""Which vehicle band(s) a part number fits - the one table every tonnage view reads.

Replaces the retired probe `_tonnage_capable.py`, which carried its own hard-coded
`SERIES_BAND` dictionary (`NLR` 3.5 / `NMR` 5.5 / `NKR` 5.5 / `NPR` 7.5 ...). That dictionary
had `NKR` at 5.5 t against every sourced table, and because it was the only map in the file
the whole 5.5 t band looked populated when in truth the euro was 3.5 t money.

Everything now comes from `modules/vehicle_bands.py`, which reads the single authored map
`03_analytics/Isuzu/prism/data/series_to_band.csv`. This script keeps no dictionary of its own.

What it writes
--------------
* `01_data/00_derived/vehicle_band_applicability.csv` - the neutral table. One row per part
  number, and it can express a D-Max or an F-series part without implying it is a rung on the
  N-series tonnage ladder:
      vehicle_groups      what kind of vehicle the codes name (| separated)
      vehicle_bands       every band the part number fits, all four groups
      n_series_bands      the subset that are truck-tonnage rungs
      exclusive_band      the single band, only when exactly one fits, else blank
      band_count          how many of the four fit
      unresolved_codes    codes named but with no band
* `01_data/00_derived/tonnage_capable_part_numbers.csv` - kept so nothing breaks, but its
  schema is unchanged in the fields that exist and it now carries ALL vehicle groups, not the
  three N-series rungs only. `band_list` / `bands` / `n_bands` keep their old meaning (the
  N-series ladder) so the family-evolution page reads them exactly as before;
  `vehicle_bands` / `vehicle_groups` / `exclusive_band` are the new columns and the ones new
  work should read.
* `01_data/00_derived/tonnage_capable_categories.csv` - per PMS category, unchanged schema.

Evidence routes
---------------
Route 1: the EPC decode (batch 1 and batch 2) - `models` and `families` strings.
Route 2: the cross-reference `vehicle_model` string.
Route 3: the cross-reference `registry_model` tag.
Nothing is inferred from a part description, a family name, a sales pattern or commercial
judgement. Wildcards (`N*R`, `TF*`, `F*`, `NQ*` ...) are recorded and never converted.

Run: python 01_data/91_build/pn_ammo_probe_20260918/_vehicle_band_applicability.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))

from modules.vehicle_bands import (  # noqa: E402
    BAND_F,
    BAND_LABEL,
    BAND_LCV,
    BAND_N35,
    BAND_N50,
    BAND_N75,
    BAND_ORDER,
    GROUP_UNRESOLVED,
    N_SERIES_BANDS,
    NOT_IN_SCOPE,
    PENDING_RULING,
    UNRESOLVED,
    band_for,
    group_for,
    is_pending_ruling,
    load_map,
)

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# The retired probe's own short band names, kept for the legacy columns only so an existing
# reader of `tonnage_capable_part_numbers.csv` sees the vocabulary it saw before.
SHORT = {BAND_N35: "3.5t", BAND_N50: "5.5t", BAND_N75: "7.5t",
         BAND_LCV: "LCV_D-Max", BAND_F: "F_series"}

OUT_APPLICABILITY = DER / "vehicle_band_applicability.csv"
OUT_LEGACY = DER / "tonnage_capable_part_numbers.csv"
OUT_CATS = DER / "tonnage_capable_categories.csv"
OUT_META = DER / "vehicle_band_applicability.meta.json"

WILDCARD_RE = re.compile(r"^[A-Z]{1,4}\d{0,3}\*$")


def _known_codes() -> set[str]:
    return set(load_map())


# ── token parsing. Whole anchored tokens, never substrings: 'TF*' must not yield an F-series
#    band, and 'N*R' must not yield an N-series band. This is the guard against the documented
#    error where F* matched TF* (the D-Max pickup) and inflated a heavy-truck figure ~EUR 1.8M.
def tokens_from_text(text: str) -> tuple[list[str], list[str]]:
    """(known codes, wildcard tokens) found in a model string."""
    known = _known_codes()
    out: list[str] = []
    wild: list[str] = []
    raw = str(text or "").upper()
    for tok in re.split(r"[,\s/;]+", raw):
        t = tok.strip().strip("()[]{}").strip()
        if not t:
            continue
        if WILDCARD_RE.match(t) or t.endswith("*"):
            wild.append(t)
            continue
        if t in known:
            out.append(t)
    return out, wild


def collect_evidence() -> pd.DataFrame:
    """One row per (part number, code, source) - the raw evidence, before any band is read."""
    rows: list[dict[str, str]] = []

    xref = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False)
    for _, r in xref.iterrows():
        for col in ("genuine_pn", "bvp_pn"):
            pn = norm(r.get(col))
            if not pn or pn == "0":
                continue
            for src, txt in (("crossref_vehicle_model", r.get("vehicle_model")),
                             ("crossref_registry_model", r.get("registry_model"))):
                codes, wild = tokens_from_text(txt)
                for c in codes:
                    rows.append({"pn": pn, "code": c, "source": src, "wildcard": ""})
                for w in wild:
                    rows.append({"pn": pn, "code": w, "source": src, "wildcard": "yes"})

    for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        path = DER / f
        if not path.is_file():
            continue
        dec = json.loads(path.read_text(encoding="utf-8"))
        for r in dec:
            if not isinstance(r, dict):
                continue
            pn = norm(r.get("pn"))
            if not pn or pn == "0":
                continue
            txt = " ".join(r.get("models") or []) + " " + " ".join(r.get("families") or [])
            codes, wild = tokens_from_text(txt)
            for c in codes:
                rows.append({"pn": pn, "code": c, "source": "epc_decode", "wildcard": ""})
            for w in wild:
                rows.append({"pn": pn, "code": w, "source": "epc_decode", "wildcard": "yes"})

    return pd.DataFrame(rows).drop_duplicates() if rows else pd.DataFrame(
        columns=["pn", "code", "source", "wildcard"])


def build() -> pd.DataFrame:
    ev = collect_evidence()

    # ── the part-number universe: everything the worklist and the banded decode name
    work = pd.read_csv(DER / "epc_decode_worklist.csv", dtype=str, low_memory=False)
    work["pn"] = work.part_number.map(norm)
    cat = dict(zip(work.pn, work.pms_category))
    eur = dict(zip(work.pn, pd.to_numeric(work.eur_all, errors="coerce").fillna(0.0)))
    units = dict(zip(work.pn, pd.to_numeric(work.units_all, errors="coerce").fillna(0.0)))

    # ── the vehicle-type dimension, from the family builder. This is what makes the table a
    #    PART-NUMBER table: a brake rotor is vehicle-type unknown with no code, while an oil
    #    filter may be known-N-series but not bandsplit. Bands are then read only for the part
    #    numbers whose family is actually an N-series truck - the same filter the shipped band
    #    file applies - so this table reconciles with it instead of contradicting it.
    fam = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False)
    fam["pn"] = fam.pn.map(norm)
    fam = fam.drop_duplicates("pn")
    pn_family = dict(zip(fam.pn, fam.family.fillna("")))
    pn_resolution = dict(zip(fam.pn, fam.resolution.fillna("")))
    pn_fam_label = dict(zip(fam.pn, fam.family_label.fillna("")))
    pn_model = dict(zip(fam.pn, fam.vehicle_model.fillna("")))

    # billing of record, so a part number with no worklist row still carries euro
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    sf["pn"] = sf.part_number.map(norm)
    money = sf.groupby("pn").net_sales_value.sum()
    qty = sf.groupby("pn").billed_qty.sum()

    universe = sorted(set(work.pn) | set(ev.pn))
    rows = []
    for pn in universe:
        codes = sorted(set(ev.loc[ev.pn == pn, "code"])) if len(ev) else []
        real = [c for c in codes if not c.endswith("*")]
        wild = [c for c in codes if c.endswith("*")]
        vehicle_type = pn_family.get(pn, "")

        # Codes that name a truck with no settled weight. The bands they could sit on are NOT
        # read into this row - an open question must not become an exclusive band.
        parked = sorted({c for c in real if is_pending_ruling(c)})
        settled = [c for c in real if not is_pending_ruling(c)]

        # Bands are read from the evidence for every part number, ALL FOUR groups. This is the
        # neutral table: a D-Max brake rotor is exclusive to the LCV / D-Max group and says so,
        # rather than being forced onto a truck rung or dropped.
        # `not_in_scope` is NOT a band - it records that a code names a vehicle outside the four
        # groups (a bus, a C&E truck, an export name) - so it is kept out of the band columns.
        n_bands = sorted({b for b in (band_for(c) for c in settled)
                          if b not in (UNRESOLVED, NOT_IN_SCOPE)})
        ns = [b for b in n_bands if b in N_SERIES_BANDS]
        groups = sorted({group_for(c) for c in settled} - {GROUP_UNRESOLVED})
        unresolved = sorted({c for c in settled if band_for(c) == UNRESOLVED})

        e = float(money.get(pn, 0.0) or 0.0)
        q = float(qty.get(pn, 0.0) or 0.0)

        rows.append({
            "pn": pn,
            "pms_category": cat.get(pn, ""),
            "vehicle_type": vehicle_type,
            "vehicle_type_resolution": pn_resolution.get(pn, ""),
            "vehicle_type_label": pn_fam_label.get(pn, ""),
            "codes_named": ";".join(real),
            "wildcards_named": ";".join(wild),
            "unresolved_codes": ";".join(unresolved),
            "parked_codes": ";".join(parked),
            "vehicle_groups": "|".join(groups),
            "vehicle_bands": "|".join(n_bands),
            "n_series_bands": "|".join(ns),
            "exclusive_band": (n_bands[0] if (len(n_bands) == 1 and not parked) else ""),
            "band_count": len(n_bands),
            # legacy columns, old vocabulary and old meaning: the three N-series rungs only
            "n_bands": len(ns),
            "band_list": "|".join(SHORT[b] for b in ns),
            "bands": "+".join(SHORT[b] for b in ns),
            "band_labels": "|".join(BAND_LABEL.get(b, b) for b in n_bands),
            "band_status": ("pending_ruling" if parked else
                            "single_band" if len(n_bands) == 1 else
                            "shared_across_bands" if len(n_bands) > 1 else
                            "no_band_read"),
            # Exclusivity is a claim about ALL the vehicles a part fits. While a code is parked
            # the vehicle list is incomplete, so exclusivity is NOT established even where the
            # settled codes happen to agree on one band.
            "exclusivity_established": ("no - a code on this part number is parked"
                                        if parked else
                                        "yes" if len(n_bands) == 1 else
                                        "no - fits more than one band" if len(n_bands) > 1 else
                                        "no band read"),
            "band_reason": ("; ".join(parked) + " quarantined pending the NMR ruling, so this "
                            "part number's band list is incomplete - see "
                            "01_data/90_INBOX/NMR_EVIDENCE_NOTE_2026-09-23.md"
                            if parked else
                            "bands read from the codes named in codes_named"
                            if n_bands else
                            "no band from any code named; wildcards recorded but never converted"),
            "eur": round(e, 2),
            "units": round(q, 2),
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_APPLICABILITY, index=False)

    # ── the legacy view. `tonnage_capable_part_numbers.csv` is read by the shipped
    #    family-evolution page (`02_dashboards/sales/_build/build_family_evolution_v2.py`) for:
    #    how many bands a part number fits, which part numbers fit exactly one, and per PMS
    #    category whether any part number fits one band only. Re-basing it on the corrected map
    #    moves all three (297 -> 322 rows, 143 -> 230 "fits one band", and three PMS categories
    #    flip to placeable), because the old probe's `NKR -> 5.5t` is what made those part
    #    numbers look shared. That is a real correction, but it changes what a SHIPPED page
    #    tells a reader, so it is not made here as a side effect of a schema fix.
    #
    #    So the legacy file's band values are FROZEN at what the page reads today, and only new
    #    columns are added. The corrected mapping lives in `vehicle_band_applicability.csv`.
    #    Rebasing the page is a separate, flagged decision - see the reconciliation note.
    LEGACY_BASELINE = ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv"
    if LEGACY_BASELINE.is_file():
        base = pd.read_csv(LEGACY_BASELINE, dtype=str, low_memory=False).fillna("")
        base["_k"] = base.pn.map(norm)

        # ── the one thing the brief asks for on the legacy file itself: the seven brake rotors
        #    it already carried were never tagged with their PMS category, because the old probe
        #    read the category from a dimension file those part numbers are absent from. The
        #    category is filled from the worklist, which does carry it. Bands are untouched.
        cat_fill = {norm(k): v for k, v in cat.items() if str(v).strip()}
        before_blank = base.category.map(lambda s: not str(s).strip()).sum()
        base["category"] = [cat_fill.get(k, c) for k, c in zip(base._k, base.category)]
        after_blank = base.category.map(lambda s: not str(s).strip()).sum()
        gained = sorted(set(base.loc[base.category.astype(str).str.strip() != "", "category"]
                            .dropna()) - {"nan"})
        print(f"legacy file   : category tagged on {before_blank - after_blank} previously blank "
              f"rows (the brake rotors); categories now present: {len(gained)}")

        add = out[["pn", "vehicle_type", "vehicle_groups", "vehicle_bands", "exclusive_band",
                   "band_count", "parked_codes", "exclusivity_established"]].copy()
        add["_k"] = add.pn.map(norm)
        legacy = base.merge(add.drop(columns=["pn"]), on="_k", how="left").drop(columns=["_k"])
        legacy["frozen_note"] = ("band values frozen at the pre-2026-09-23 basis; see "
                                 "vehicle_band_applicability.csv for the corrected mapping")
        legacy.to_csv(OUT_LEGACY, index=False)
        print(f"legacy file   : FROZEN at the page's current basis, {len(legacy):,} rows "
              f"(+ {len(add.columns) - 1} new columns)")
    else:
        print(f"legacy file   : baseline {LEGACY_BASELINE.name} not found - NOT written, "
              f"so a shipped page cannot change by accident")

    cat_rows = []
    for c, g in out[out.pms_category.notna() & out.pms_category.ne("")].groupby("pms_category"):
        single = g[g.band_count == 1]
        shared = g[g.band_count > 1]
        cat_rows.append({"category": c, "pns": len(g), "single": len(single), "shared": len(shared),
                         "eur_single": single.eur.sum(), "eur_shared": shared.eur.sum()})
    pd.DataFrame(cat_rows).to_csv(OUT_CATS, index=False)

    meta = {
        "generated_by": "01_data/91_build/pn_ammo_probe_20260918/_vehicle_band_applicability.py",
        "mapping_source": "03_analytics/Isuzu/prism/data/series_to_band.csv (authored)",
        "reader": "03_analytics/Isuzu/prism/modules/vehicle_bands.py",
        "band_vocabulary": BAND_ORDER,
        "n_series_ladder": N_SERIES_BANDS,
        "note": ("vehicle_bands covers all four vehicle groups; n_series_bands / band_list / "
                 "bands keep their old three-rung meaning. A D-Max or F-series part is written "
                 "with its own group and never as a rung of the N-series ladder."),
        "routes": ["epc_decode", "crossref_vehicle_model", "crossref_registry_model"],
        "wildcards_are_never_converted": True,
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def main() -> int:
    out = build()
    print("=" * 100)
    print("VEHICLE BAND APPLICABILITY")
    print("=" * 100)
    print(f"part numbers            : {len(out):,}")
    print(f"with a band             : {(out.band_count > 0).sum():,}")
    print(f"exclusive to one band   : {(out.exclusive_band != '').sum():,}")
    print(f"no band from any source : {(out.band_count == 0).sum():,}")
    print(f"wildcard-only evidence  : {((out.band_count == 0) & (out.wildcards_named != '')).sum():,}")
    print()
    print("by vehicle group (all four):")
    for grp in ["n_series_truck", "light_vehicle", "heavy_truck"]:
        sel = out[out.vehicle_groups.str.contains(grp, na=False)]
        print(f"  {grp:16s} {len(sel):5,d} PNs   EUR {sel.eur.sum():14,.0f}")
    print()
    print("exclusive to a single band:")
    for b in BAND_ORDER:
        sel = out[out.exclusive_band == b]
        print(f"  {b:18s} {len(sel):4,d} PNs   EUR {sel.eur.sum():14,.0f}")
    print()
    print("on the N-series ladder (band_list), single versus shared:")
    for b in N_SERIES_BANDS:
        single = out[out.band_list == SHORT[b]]
        also = out[out.band_list.str.contains(SHORT[b], na=False) & (out.band_list != SHORT[b])]
        print(f"  {b:18s} exclusive {len(single):4,d} PNs EUR {single.eur.sum():12,.0f} | "
              f"shared    {len(also):4,d} PNs EUR {also.eur.sum():12,.0f}")
    print()
    print("part numbers whose only evidence is a wildcard (recorded, never converted):")
    wonly = out[(out.band_count == 0) & (out.wildcards_named != "")]
    print(f"  {len(wonly):,} PNs   EUR {wonly.eur.sum():,.0f}")
    print()
    print(f"written -> {OUT_APPLICABILITY.name}, {OUT_LEGACY.name}, {OUT_CATS.name}, "
          f"{OUT_META.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
