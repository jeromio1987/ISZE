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
    pending_ruling_codes,
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


def pending_codes_in_text(text: str) -> list[str]:
    """Codes the authored map marks `pending_ruling` that this text names as whole words.

    This exists because the exact-token split above cannot see the way the EPC and the
    cross-reference actually write a quarantined code:

        '2016 NLR/NMR-LHD EURO6 EUROPE 16.0 - 17.0'  -> split on [,\\s/;]+ gives
                                                        ['2016 NLR', 'NMR-LHD EURO6 ...']
        'NKR、NMR,NLR'                                -> the '、' is not in the split set

    so `NMR` is glued to `-LHD` (or preceded by a non-ASCII separator) and never matches a map key.
    The result was that twelve part numbers whose only 5.5 t evidence is NMR were never *recorded*
    as parked: `parked_codes` came out empty, so the pre-2026-09-23 statement "a parked code
    contributes its interim band" had nothing to act on, the NMR rung was silently dropped from
    `n_series_bands`, and those rows lost their 5.5 t band on the 2026-09-23 re-base.

    Deliberately limited to the codes the map already marks `pending_ruling`. Widening whole-word
    detection to every code would reintroduce the documented `F*` vs `TF*` error, where a pickup
    was read as a heavy truck; for a quarantined code, over-naming is the safe direction because
    the answer is carried forward rather than recomputed.
    """
    raw = str(text or "").upper()
    return sorted({c for c in pending_ruling_codes()
                   if re.search(rf"(?<![A-Z0-9]){re.escape(c)}(?![A-Z0-9])", raw)})


def _pending_codes_from_raw_evidence(pns: set[str]) -> dict[str, list[str]]:
    """{part number: quarantined codes named anywhere in its raw evidence}.

    Reads the same two sources the evidence stage reads (the EPC decode and the cross-reference)
    and applies `pending_codes_in_text` to each string. Used by the legacy re-base so a
    quarantined row can be recognised even though the token split missed it. It is a local read
    for the legacy file only: the neutral table is left exactly as it was built.
    """
    out: dict[str, list[str]] = {}
    for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        path = DER / f
        if not path.is_file():
            continue
        for r in json.loads(path.read_text(encoding="utf-8")):
            if not isinstance(r, dict):
                continue
            pn = norm(r.get("pn"))
            if pn not in pns:
                continue
            txt = " ".join(r.get("models") or []) + " " + " ".join(r.get("families") or [])
            found = pending_codes_in_text(txt)
            if found:
                out[pn] = sorted(set(out.get(pn, [])) | set(found))
    xref = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False)
    for r in xref.itertuples():
        for col in ("genuine_pn", "bvp_pn"):
            pn = norm(getattr(r, col))
            if pn not in pns:
                continue
            for c in ("vehicle_model", "registry_model"):
                found = pending_codes_in_text(getattr(r, c))
                if found:
                    out[pn] = sorted(set(out.get(pn, [])) | set(found))
    return out


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
    #    category whether any part number fits one band only. All three are read off the legacy
    #    columns, so those columns have to carry the same answer the page is being asked to
    #    publish. They were frozen on 2026-09-23 while the mapping underneath was being fixed,
    #    because re-basing them moves what a SHIPPED page tells a reader; that re-base was
    #    ruled on and is made here, in the builder, once, rather than by editing the CSV.
    LEGACY_BASELINE = ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv"
    if LEGACY_BASELINE.is_file():
        base = pd.read_csv(LEGACY_BASELINE, dtype=str, low_memory=False).fillna("")
        base["_k"] = base.pn.map(norm)

        # ── the category fill the earlier pass asked for: rows the old probe left untagged
        #    (BRAKE ROTOR and FUEL FILTER hardware among them, because it read the category from
        #    a dimension file those part numbers are absent from) are tagged from the worklist.
        cat_fill = {norm(k): v for k, v in cat.items() if str(v).strip()}
        before_blank = base.category.map(lambda s: not str(s).strip()).sum()
        base["category"] = [cat_fill.get(k, c) for k, c in zip(base._k, base.category)]
        after_blank = base.category.map(lambda s: not str(s).strip()).sum()
        gained = sorted(set(base.loc[base.category.astype(str).str.strip() != "", "category"]
                            .dropna()) - {"nan"})
        print(f"legacy file   : category tagged on {before_blank - after_blank} previously blank "
              f"rows; categories now present: {len(gained)}")

        # ── RE-BASED 2026-09-23, ruled on by Jerome. The three legacy columns are written from
        #    the corrected mapping, in the legacy three-rung vocabulary only (`3.5t` / `5.5t` /
        #    `7.5t`). They are NOT read from `out`'s own `n_bands` / `band_list` / `bands`:
        #    those are the settled-codes-only answer, which is a different question from the one
        #    ruled. This block recomputes the three rungs with the ruled rule applied.
        #
        #    A quarantined code contributes its interim band. That is the ruling and it is the
        #    only rule whose answer cannot move when the ruling on it lands: a part number that
        #    fits a quarantined code and something else is shared whether that code settles on
        #    5.5 t or 7.5 t. Excluding it would assert that it contributes no rung at all, which
        #    is itself a claim about it that nobody has established, and it would inflate the
        #    exclusive count by discarding evidence rather than by adding it.
        #
        #    RE-BASED 2026-09-23, SECOND PASS. The first pass broke that rule without noticing
        #    on twelve rows. An interim band is a value someone has NOT settled, so recomputing
        #    it from `band_for()` re-decides it: where `band_for` no longer returns the band the
        #    row previously carried, the rung silently disappears. That is exactly what happened -
        #    the EPC writes NMR glued to a suffix (`NMR-LHD`) and after a non-ASCII separator
        #    (`NKR、NMR,NLR`), which the exact-token split cannot see, so ten rows were never
        #    tagged as parked, `parked_codes` came out empty, and their 5.5 t rung was dropped as
        #    though NMR were not on them at all. Ten rows lost 5.5 t and two more moved the other
        #    way (`8981868281` gained 7.5 t, `8983615742` lost 5.5 t).
        #
        #    So for a row that names a quarantined code, the band is now CARRIED FORWARD from the
        #    pre-change file rather than recomputed. That is the structural guard: an unsettled
        #    value cannot be moved by a build, and the guard is silent on every row where no
        #    quarantined code is named. The quarantined code is now also recorded as parked at the
        #    evidence stage (`pending_codes_in_text`), so `parked_codes` and
        #    `exclusivity_established` tell the truth about these rows too.
        #
        #    The row set is the part numbers this rule can place on the ladder at all: one that
        #    no code places, and whose only evidence was a wildcard fragment read as a series,
        #    leaves the file rather than sitting in it with a stale rung. Measured before this
        #    write: 297 rows / 143 fit one band  ->  324 rows / 180 fit one band. An earlier
        #    count of 230 was wrong - it came from dropping the quarantined band, not from the
        #    map.
        #
        #    The four-group columns (`vehicle_bands`, `exclusive_band`, `band_count`) and the
        #    tag on a quarantined row stay as `out` computed them, a copy of the neutral table,
        #    so this file cannot disagree with `vehicle_band_applicability.csv` about them.
        cols = ["pn", "band_list", "n_bands", "category", "bands", "eur", "vehicle_type",
                "vehicle_groups", "vehicle_bands", "exclusive_band", "band_count", "parked_codes",
                "exclusivity_established", "frozen_note"]
        note = ("re-based 2026-09-23 on the authored series-to-band map; a quarantined code "
                "contributes its interim band, carried forward from this file's previous revision "
                "rather than recomputed")
        # ── the pre-change three-rung list per part number, for the guard below
        base_rungs = {k: [b for b in str(v).split("+") if b]
                      for k, v in zip(base._k, base.bands)}
        # ── quarantined codes named in the RAW evidence, recovered here rather than at the
        #    evidence stage, because adding them there would change `vehicle_band_applicability
        #    .csv` (parked_codes, n_series_bands and the row set) and that table is not this
        #    repair's to move. See `pending_codes_in_text` for why the token split cannot see
        #    them. This touches the legacy file only.
        pending_by_pn = _pending_codes_from_raw_evidence(set(out.pn.map(norm)))
        carried = 0
        legacy_rows = []
        for r in out.itertuples():
            rungs = {b for b in str(r.n_series_bands).split("|") if b}
            for c in str(r.parked_codes).split(";"):
                c = c.strip()
                b = band_for(c) if c else UNRESOLVED
                if b in N_SERIES_BANDS:
                    rungs.add(b)
            if not rungs:
                continue
            ordered = [b for b in N_SERIES_BANDS if b in rungs]
            # ── THE GUARD. A code the map marks `pending_ruling` has an interim band: a value
            #    nobody has settled. Recomputing it here is what re-decided it and dropped the
            #    rung from twelve rows. So where this row names a quarantined code and the file
            #    already carried a band list, that list is kept. Silent on every other row.
            named = pending_by_pn.get(norm(r.pn), [])
            if named and norm(r.pn) in base_rungs:
                kept = base_rungs[norm(r.pn)]
                guard = [b for b in N_SERIES_BANDS if SHORT[b] in kept]
                if guard and guard != ordered:
                    ordered = guard
                    carried += 1
            if not ordered:
                continue
            legacy_rows.append({
                "pn": r.pn,
                # the two band spellings are kept exactly as this column has always carried
                # them: `band_list` as a Python-list literal (the page parses it with json.loads
                # after swapping the quotes) and `bands` as `+`-joined short rungs
                "band_list": "[" + ", ".join("'%s'" % SHORT[b] for b in ordered) + "]",
                "n_bands": len(ordered),
                "category": cat_fill.get(norm(r.pn), r.pms_category),
                "bands": "+".join(SHORT[b] for b in ordered),
                "eur": r.eur,
                "vehicle_type": r.vehicle_type,
                "vehicle_groups": r.vehicle_groups,
                "vehicle_bands": r.vehicle_bands,
                "exclusive_band": r.exclusive_band,
                "band_count": r.band_count,
                "parked_codes": r.parked_codes,
                "exclusivity_established": r.exclusivity_established,
                "frozen_note": note,
            })
        legacy = pd.DataFrame(legacy_rows, columns=cols)
        legacy.to_csv(OUT_LEGACY, index=False)
        single = int((legacy.n_bands == 1).sum())
        print(f"legacy file   : RE-BASED on the authored map, {len(legacy):,} rows, "
              f"{single} fit one band (was 297 rows / 143 fit one band); "
              f"{carried} row(s) on a quarantined code kept the band this file already carried")
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
