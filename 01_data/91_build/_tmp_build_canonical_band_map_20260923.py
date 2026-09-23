#!/usr/bin/env python3
"""Author the ONE canonical vehicle-band mapping, once.

Why this exists
---------------
Three files held their own series -> band dictionary: the bander
(`build_nseries_tonnage_bands.py`, dict `TABLE`), the retired probe
(`pn_ammo_probe_20260918/_tonnage_capable.py`, dict `SERIES_BAND`) and the model-code
builder (`build_model_code_to_tonnage.py`, a list of `add()` calls). They disagreed:
the probe had `NKR -> 5.5t` and the model-code table had `NMR` on band 7.5 t while its own
weight label on the same row read 5.5 t. Anything downstream could therefore pick a
different answer for the same truck.

This script writes `03_analytics/Isuzu/prism/data/series_to_band.csv`: one row per vehicle
code, with the band, the vehicle group the code belongs to, the evidence, the quote and a
confidence. It is AUTHORED SOURCE, not a build output - edit the CSV to change a mapping.
Every downstream tonnage script reads it; none keeps its own.

Behaviour is deliberately unchanged for everything already resolved. The two rows that are
NOT settled stay visible as such:

* `NMR` - the 5.5 t / 7.5 t question. `status = pending_ruling`, band left as the interim
  value the pipeline uses today so nothing moves before the ruling, and both candidate
  bands recorded in `quarantine_candidates`.
* `NKR` - the retired probe put it at 5.5 t against every sourced table. The sourced answer
  (3.5 t) is kept. Recorded here because the probe's error is what made the 5.5 t band look
  populated.

Vehicle groups are the four the workspace ships plus the two non-N-series classes:
`n_series_truck`, `light_vehicle` (D-Max pickup / SUV), `heavy_truck` (F&G and C&E),
`out_of_scope` (bus, industrial, export-only) and `unresolved`.

Run: python 01_data/91_build/_tmp_build_canonical_band_map_20260923.py
Writes: 03_analytics/Isuzu/prism/data/series_to_band.csv (only)
"""
from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
OUT = PRISM / "data" / "series_to_band.csv"

N_SERIES = "n_series_truck"
LIGHT = "light_vehicle"
HEAVY = "heavy_truck"
OUT_OF_SCOPE = "out_of_scope"
UNRESOLVED = "unresolved"

# Canonical band names. The four the workspace ships, used verbatim by
# `build_pms_tonnage_model.py` and `build_vehicle_family_bands.py`.
BAND_LCV = "LCV_D-Max"
BAND_N35 = "3.5t_N35"
BAND_N50 = "5.5t_N50_N55"
BAND_N75 = "7.5t_N50_N62_N75"
BAND_F = "F_series_MD_heavy"
NOT_IN_SCOPE = "not_in_scope"

BAND_TO_GROUP = {
    BAND_LCV: LIGHT,
    BAND_N35: N_SERIES,
    BAND_N50: N_SERIES,
    BAND_N75: N_SERIES,
    BAND_F: HEAVY,
    NOT_IN_SCOPE: OUT_OF_SCOPE,
}


def load_bander_table() -> dict[str, tuple[str, str, str, str, str]]:
    """The bander's sourced table, read - not retyped - so the evidence quotes carry over."""
    spec = importlib.util.spec_from_file_location(
        "bnb", PRISM / "scripts" / "build_nseries_tonnage_bands.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bnb"] = mod
    spec.loader.exec_module(mod)
    return mod.TABLE


def load_family_groups() -> dict[str, str]:
    """The vehicle group per code, from the family builder's own dictionary.

    The N-series bander only knows three answers (`3.5t_N35` / `5.5t_N50_N55` /
    `7.5t_N50_N62_N75`) plus `not_n_series` and `unresolved`, and `not_n_series` lumps the
    D-Max pickup together with the F&G heavy trucks. The family builder already separates
    them, so the group is read from there rather than rederived.
    """
    spec = importlib.util.spec_from_file_location(
        "bvfb", PRISM / "scripts" / "build_vehicle_family_bands.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bvfb"] = mod
    spec.loader.exec_module(mod)
    groups = dict(mod.CONCRETE)
    groups.update({c: mod.LIGHT for c, _ in mod.WILDCARD})  # not used as a code, kept for shape
    return dict(mod.CONCRETE)


def load_gvw() -> dict[str, tuple[str, str]]:
    """{code: (gvw_t, where it came from)} from the two files that state a weight.

    `series_to_tonnage.csv` carries a weight label per series; `model_dimension.csv` is the JP
    VIN register's own series -> GVW table. Both are read rather than retyped. The register's
    `gvw_t` is NOT a measurement - `build_vin_register.py` writes it from its own hand-typed
    `SERIES_GVW_T` dictionary - so it is recorded as a stated value, not as measured evidence.
    """
    out: dict[str, tuple[str, str]] = {}
    reg = PRISM / ".." / ".." / ".." / "01_data" / "07_UIO" / "vin" / "model_dimension.csv"
    reg = (ROOT / "01_data" / "07_UIO" / "vin" / "model_dimension.csv")
    if reg.is_file():
        with open(reg, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                s = (r.get("series") or "").strip().upper()
                g = (r.get("gvw_t") or "").strip()
                if s and g:
                    out.setdefault(s, (g, "model_dimension.csv (register GVW column)"))
    with open(ROOT / "01_data" / "00_derived" / "series_to_tonnage.csv",
              encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            s = (r.get("series") or "").strip().upper()
            lab = (r.get("weight_label") or "")
            m = re.search(r"(\d+(?:\.\d+)?)\s*t\b", lab)
            if s and m and s not in out:
                out[s] = (m.group(1), f"series_to_tonnage.csv weight label: '{lab.strip()}'")
    return out


def load_model_code_table() -> dict[str, tuple[str, str, str, str, str]]:
    """The model-code table's own rows, for the codes the N-series bander does not carry."""
    path = PRISM / "data" / "model_code_to_tonnage.csv"
    out: dict[str, tuple[str, str, str, str, str]] = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            code = (r.get("model_code") or "").strip().upper()
            if not code:
                continue
            out[code] = (
                (r.get("tonnage_band") or "").strip(),
                (r.get("weight_class_label") or "").strip(),
                (r.get("evidence_source") or "").strip(),
                (r.get("evidence_quote") or "").strip(),
                (r.get("confidence") or "").strip(),
            )
    return out


def main() -> int:
    bander = load_bander_table()
    model = load_model_code_table()
    groups = load_family_groups()
    gvw = load_gvw()

    rows: list[dict[str, str]] = []
    for code in sorted(set(bander) | set(model)):
        b = bander.get(code)
        m = model.get(code)

        origin = "series_to_band (authored)"
        if b and m and m[0] in {BAND_LCV, BAND_F} and b[0] == "not_n_series":
            # The bander says only "not N-series"; the model-code table says which class. The
            # class is the finer answer, so take its band and label and keep the bander's quote.
            band, label, source, quote, conf = m[0], m[1], m[2], m[3], m[4]
            origin += " <- both tables (band from model_code_to_tonnage.csv)"
        elif b:
            band, label, source, quote, conf = b
            origin += " <- build_nseries_tonnage_bands.py TABLE"
        else:
            band, label, source, quote, conf = m
            origin += " <- model_code_to_tonnage.csv"

        if band == "other":
            band, conf = NOT_IN_SCOPE, conf or "medium"

        status = "resolved"
        candidates = ""
        if not band or band in {"unresolved", ""}:
            band, status, conf = UNRESOLVED, "unresolved", "unresolved"
        elif band == NOT_IN_SCOPE:
            status = "out_of_scope"
        elif band == "not_n_series":
            # No class named by either table for this code.
            band, status, conf = UNRESOLVED, "unresolved", "unresolved"
        group = groups.get(code) or BAND_TO_GROUP.get(band, UNRESOLVED)

        # ── the two codes that need care, marked rather than silently placed ────────────────
        if code in ("NMR", "NMR85"):
            # NMR is a 5.5 t / 7.5 t open question and must not be settled by this pass. The two
            # codes are treated differently on purpose:
            #   NMR    - the shipped pipeline already banded it as 5.5 t, so that interim value
            #            stays (marked) and nothing moves.
            #   NMR85  - the shipped pipeline had NO band for it, so it gets none now. Handing it
            #            the older table's 7.5 t would be a new classification, which is the one
            #            thing this pass must not do.
            status = "pending_ruling"
            candidates = f"{BAND_N50}|{BAND_N75}"
            if code == "NMR85":
                band, label, conf = UNRESOLVED, "not stated by any source", "unresolved"
            else:
                band, label, conf = BAND_N50, "5.5 t GVW (N50 / N55) - INTERIM, NOT SETTLED", "medium"
            quote += (
                " || QUARANTINED PENDING RULING: this file does NOT settle whether NMR / NMR85 "
                "belong to the 5.5 t or the 7.5 t band. "
                f"Both candidates recorded: {BAND_N50} (series_to_tonnage.csv, model_dimension.csv) "
                f"and {BAND_N75} (model_code_to_tonnage.csv band column, from the older "
                "model_code_to_tonnage.py). No source states 7,500 kg for any NMR. "
                "The 5.5 t value carried on NMR here is the interim value the shipped pipeline "
                "already used, kept so nothing moves before the ruling - it is not an answer. "
                "Evidence note: 01_data/90_INBOX/NMR_EVIDENCE_NOTE_2026-09-23.md"
            )
        elif code == "NKR":
            # Kept at the sourced answer. Recorded because the retired probe said 5.5 t, which is
            # what made the 5.5 t band look populated.
            quote += (
                " || The retired probe dict `SERIES_BAND` in pn_ammo_probe_20260918/_tonnage_capable.py "
                "hard-coded NKR at 5.5 t. That entry is contradicted by this table, by "
                "series_to_tonnage.csv and by model_code_to_tonnage.csv, and it is retired with the "
                "probe. NKR stays at 3.5 t here."
            )

        rows.append({
            "code": code,
            "vehicle_group": group,
            "tonnage_band": band,
            "gvw_t": gvw.get(code, ("", ""))[0],
            "gvw_source": gvw.get(code, ("", ""))[1],
            "weight_label": label,
            "evidence_source": source,
            "evidence_quote": quote,
            "confidence": conf,
            "status": status,
            "quarantine_candidates": candidates,
            "recorded_by": origin,
        })

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"canonical map: {len(rows)} codes -> {OUT}")
    for st in sorted({r["status"] for r in rows}):
        sel = [r for r in rows if r["status"] == st]
        print(f"  {st:16s} {len(sel):3d}")
    print()
    for grp in (N_SERIES, LIGHT, HEAVY, OUT_OF_SCOPE, UNRESOLVED):
        sel = [r["code"] for r in rows if r["vehicle_group"] == grp and r["tonnage_band"] not in
               (UNRESOLVED, NOT_IN_SCOPE)]
        print(f"  {grp:16s} banded {len(sel):3d}  {sorted(sel)[:18]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
