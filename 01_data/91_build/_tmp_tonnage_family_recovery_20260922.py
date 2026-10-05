#!/usr/bin/env python3
"""Tonnage band recovery for the five families the candidate table has zero rows for.

READ-ONLY. Writes nothing into 01_data/00_derived. The two outputs are a proposal CSV and a
markdown write-up under 01_data/90_INBOX.

Why
---
`tonnage_capable_part_numbers.csv` is produced by `pn_ammo_probe_20260918/_tonnage_capable.py`, a
probe that reads route 1 only (the EPC decode) and whose band vocabulary is the three N-series
series rungs (NLR/NMR/NPR/NQR/NNR/NKR/NHR -> 3.5/5.5/7.5). Five PMS families have zero rows in it.

This script attempts route 2 (the cross-reference `vehicle_model` string) and route 3 (the
`registry_model` tag on the cross-reference row, plus the family file's own model string) for every
part number in those five families, and decides per part number whether a band can be assigned.

Rules applied (from 00_docs/agent/VERIFICATION_PACK_20260921.md and the workspace rules)
--------------------------------------------------------------------------------------------
* Series tokens are matched as WHOLE ANCHORED TOKENS, never substrings. The documented error this
  guards against is `F*` matching `TF*` (the D-Max pickup wildcard), which inflated a heavy-truck
  figure by about EUR 1.8M.
* A wildcard (`N*R`, `N*S`, `TF*`, `UC*`, `F*`, `EX*`, `CX*`, `CY*`, `NQ*`, `N*`, `FS*`, `FT*`,
  `FV*`, `FX*`, `E*`, `C*`, ...) is recorded and NEVER turned into a band. If a part number's only
  evidence is a wildcard, its verdict is `wildcard_only`.
* A part number that fits several bands is pooled, never apportioned -> `recoverable_shared`.
* Two sources naming different single bands -> `conflicting`, no side is picked.
* `series_to_tonnage.csv` is the authority for what a token means.

Run: python 01_data/91_build/_tmp_tonnage_family_recovery_20260922.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT_DIR = ROOT / "01_data" / "90_INBOX"

WORKLIST = DER / "epc_decode_worklist.csv"
CROSSREF = DER / "genuine_bvp_crossref.csv"
FAMILY = DER / "vehicle_family_bands.csv"
BANDED = DER / "epc_decode_nseries_banded.csv"
SERIES = DER / "series_to_tonnage.csv"
BAND1 = DER / "epc_decode_batch1_banded_20260919.csv"
DECODE2 = DER / "epc_decode_batch2_20260919.json"
HEAVY = DER / "epc_catalogue_heavy_20260919.csv"
OLD_MAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "model_code_to_tonnage.csv"

OUT_CSV = OUT_DIR / "tonnage_family_recovery_proposal_20260922.csv"
OUT_MD = OUT_DIR / "tonnage_family_recovery_20260922.md"

FAMILIES = ["brake_rotor", "blower_filter", "urea_filter", "clutch_booster", "pilot_bearing"]

# `part_number` is kept as a string throughout: several part numbers are zero-padded and must not
# be numerically coerced. A stripped copy is used only as a join key between files, because the
# files disagree on leading zeros.
norm = lambda s: (str(s).strip().lstrip("0") or "0")  # noqa: E731

# ── the band vocabulary. The four the analysis reads, using the workspace's own band names.
BAND_N35 = "3.5t"
BAND_N50 = "5.5t"
BAND_N75 = "7.5t"
BAND_F = "F_series"
BAND_LCV = "LCV_D-Max"
TONNAGE_BANDS = [BAND_F, BAND_N35, BAND_N50, BAND_N75]

# `series_to_tonnage.csv` -> the reported band. This is the authority.
SERIES_TO_BAND = {
    "3.5t_N35": BAND_N35,
    "5.5t_N50_N55": BAND_N50,
    "7.5t_N50_N62_N75": BAND_N75,
}
# The EPC's own band vocabulary -> the reported band. `F_series_MD_heavy` is the F&G band;
# `LCV_D-Max` is the D-Max pickup/SUV class, which the shipped model carries as a class of its own
# and which is not a truck tonnage rung.
BAND_MAP = {
    "LCV_D-Max": BAND_LCV,
    "3.5t_N35": BAND_N35,
    "7.5t_N50_N62_N75": BAND_N75,
    "F_series_MD_heavy": BAND_F,
}
# `not_n_series` splits by the weight label the series table carries.
NOT_N_TO_BAND = {
    "F&G series medium / heavy": BAND_F,
    "D-Max pickup": BAND_LCV,
    "D-Max SUV": BAND_LCV,
}

VERDICTS = ["recoverable_single_band", "recoverable_shared", "wildcard_only", "no_evidence",
            "conflicting"]

TOKEN_SPLIT = re.compile(r"[,\s/|;]+")


def clean(value) -> str:
    """A CSV cell as text. A float NaN is truthy, so `str(nan or '')` yields 'nan'; handle it."""
    if value is None or (isinstance(value, float) and value != value):
        return ""
    s = str(value).strip()
    return "" if s.lower() in ("nan", "none") else s


def split_tokens(value) -> list[str]:
    """Tokens of a vehicle string, punctuation stripped. A trailing `*` is preserved as a marker."""
    s = clean(value)
    for ch in "()[]{}\uff08\uff09\u3001\uff0c\n\r\t":
        s = s.replace(ch, ",")
    return [t for t in (p.strip() for p in TOKEN_SPLIT.split(s)) if t]


def load_series_map() -> dict[str, tuple[str, str, str]]:
    """series -> (band, weight_label, confidence). Empty band means the token resolves to nothing."""
    s = pd.read_csv(SERIES, dtype=str).fillna("")
    out: dict[str, tuple[str, str, str]] = {}
    for r in s.itertuples():
        band = ""
        if r.tonnage_band in SERIES_TO_BAND:
            band = SERIES_TO_BAND[r.tonnage_band]
        elif r.tonnage_band == "not_n_series":
            for frag, b in NOT_N_TO_BAND.items():
                if frag in r.weight_label:
                    band = b
                    break
        out[str(r.series).strip().upper()] = (band, r.weight_label, r.confidence)
    return out


def classify(token: str, smap: dict) -> tuple[str, str]:
    """(kind, band) for one token. kind is 'band' | 'wildcard' | 'unresolved' | 'unknown'.

    A wildcard is any token carrying an asterisk, wherever it sits: `TF*` and `UC*` end with one,
    but `N*R` and `N*S` carry it in the middle. Testing only the last character would miss those
    two, which are exactly the strings the brake rotor family turns on.
    """
    t = token.strip().upper()
    if not t:
        return "unknown", ""
    if "*" in t:
        return "wildcard", ""
    if t in smap:
        band, _label, _conf = smap[t]
        return ("band", band) if band else ("unresolved", "")
    return "unknown", ""


def read_epc_tokens() -> dict[str, set[str]]:
    """Route 1, for context: the series tokens the EPC decode returns per part number."""
    out: dict[str, set[str]] = {}

    def add(pn: str, text: str) -> None:
        out.setdefault(norm(pn), set()).update(split_tokens(text))

    try:
        b1 = pd.read_csv(BAND1, dtype=str, low_memory=False).fillna("")
        for r in b1.itertuples():
            add(r.pn, f"{getattr(r, 'model_codes', '')},{getattr(r, 'models', '')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! batch1 banded unreadable: {exc}")

    try:
        b = pd.read_csv(BANDED, dtype=str, low_memory=False).fillna("")
        for r in b.itertuples():
            add(r.pn, f"{getattr(r, 'series_all', '')},{getattr(r, 'series_from_epc', '')},"
                     f"{getattr(r, 'series_from_crossref', '')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! banded unreadable: {exc}")

    try:
        dec2 = json.loads(DECODE2.read_text(encoding="utf-8"))
        for r in dec2:
            add(str(r.get("pn")), " ".join(r.get("models") or []))
    except Exception as exc:  # noqa: BLE001
        print(f"  ! batch2 unreadable: {exc}")

    try:
        hv = pd.read_csv(HEAVY, dtype=str, low_memory=False).fillna("")
        for r in hv.itertuples():
            add(r.part_number, getattr(r, "series_tokens", ""))
    except Exception as exc:  # noqa: BLE001
        print(f"  ! heavy catalogue unreadable: {exc}")

    return out


def read_old_map() -> dict[str, str]:
    """The older mapping, kept only to test whether it disagrees with series_to_tonnage."""
    try:
        m = pd.read_csv(OLD_MAP, dtype=str).fillna("")
        return {str(r.model_code).strip().upper(): r.tonnage_band for r in m.itertuples()}
    except Exception:  # noqa: BLE001
        return {}


EPC_BAND_IN_NOTE = re.compile(r"tonnage band '([^']+)'")
EPC_RANGE_IN_NOTE = re.compile(r"EPC vehicle range: (.+)$")


def epc_bands_from_note(note: str) -> tuple[set[str], str]:
    """(bands, vehicle class or range) the family file recorded from the EPC decode.

    The family file writes the EPC's answer either as `tonnage band 'LCV_D-Max'` or as
    `EPC vehicle range: TRUCKS N`. Both are route 1. The first is already a band; the second is a
    vehicle class with no weight in it, which is a different thing and is reported as such.
    """
    bands: set[str] = set()
    note = clean(note)
    m = EPC_BAND_IN_NOTE.search(note)
    if m:
        for b in m.group(1).split("|"):
            b = clean(b)
            if b in BAND_MAP:
                bands.add(BAND_MAP[b])
    rng = ""
    m2 = EPC_RANGE_IN_NOTE.search(note)
    if m2:
        rng = clean(m2.group(1))
    return bands, rng


def main() -> int:
    smap = load_series_map()
    old_map = read_old_map()

    wl = pd.read_csv(WORKLIST, dtype=str)
    wl["pn"] = wl.part_number.map(norm)
    sub = wl[wl.pms_category.isin(FAMILIES)].copy()
    keep = set(sub.pn)

    fam = pd.read_csv(FAMILY, dtype=str, low_memory=False)
    fam["pn"] = fam.pn.map(norm)
    fam_by_pn: dict[str, list[dict]] = {}
    for r in fam[fam.pn.isin(keep)].itertuples():
        fam_by_pn.setdefault(r.pn, []).append({
            "vehicle_model": clean(getattr(r, "vehicle_model", "")),
            "resolution": clean(getattr(r, "resolution", "")),
            "from_epc": clean(getattr(r, "from_epc", "")),
            "from_crossref": clean(getattr(r, "from_crossref", "")),
            "source_note": clean(getattr(r, "source_note", "")),
            "confidence": clean(getattr(r, "confidence", "")),
        })

    xr = pd.read_csv(CROSSREF, dtype=str, low_memory=False)
    xr["g"] = xr.genuine_pn.map(norm)
    xr["b"] = xr.bvp_pn.map(norm)
    xr_by_pn: dict[str, list[dict]] = {}
    for r in xr.itertuples():
        rec = {
            "vehicle_model": clean(getattr(r, "vehicle_model", "")),
            "registry_model": clean(getattr(r, "registry_model", "")),
            "engine_type": clean(getattr(r, "engine_type", "")),
            "product_family": clean(getattr(r, "product_family", "")),
            "bvp_pn": clean(getattr(r, "bvp_pn", "")),
        }
        for pn in {r.g, r.b}:
            if pn in keep:
                xr_by_pn.setdefault(pn, []).append(rec)

    epc_tokens = read_epc_tokens()
    cand = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str)
    cand["k"] = cand.pn.map(norm)
    cand_bands: dict[str, set[str]] = {}
    for r in cand.itertuples():
        bs = set()
        for b in str(r.band_list).strip("[]").replace("'", "").split(","):
            b = b.strip()
            if b in ("3.5t", "5.5t", "7.5t"):
                bs.add(b)
            elif b == "LCV_D-Max":
                bs.add(BAND_LCV)
        cand_bands[r.k] = bs
    banded = pd.read_csv(BANDED, dtype=str, low_memory=False).fillna("")
    banded["pn"] = banded.pn.map(norm)
    banded_by_pn = {r.pn: r for r in banded.itertuples()}
    banded_bands: dict[str, set[str]] = {}
    for r in banded.itertuples():
        bs = set()
        for b in str(r.tonnage_band).split("|"):
            b = clean(b)
            if b in BAND_MAP:
                bs.add(BAND_MAP[b])
        banded_bands[r.pn] = bs
    # the family file's route-1 band, per part number, for the NMR comparison table
    fam_route1_by_pn: dict[str, set[str]] = {}
    for r in fam[fam.pn.isin(keep)].itertuples():
        bs, _rng = epc_bands_from_note(clean(getattr(r, "source_note", "")))
        fam_route1_by_pn[r.pn] = bs
    rows = []
    for r in sub.itertuples():
        pn = r.pn
        pms = r.pms_category
        eur = float(r.eur_all or 0)
        units = float(r.units_all or 0)
        markets = r.markets

        frows = fam_by_pn.get(pn, [])
        xrows = xr_by_pn.get(pn, [])

        # ── the raw strings each route offers
        fam_strings = sorted({fr["vehicle_model"] for fr in frows if fr["vehicle_model"]})
        xr_strings = sorted({xr_["vehicle_model"] for xr_ in xrows if xr_["vehicle_model"]})
        reg_strings = sorted({xr_["registry_model"] for xr_ in xrows if xr_["registry_model"]})
        engines = sorted({xr_["engine_type"] for xr_ in xrows if xr_["engine_type"]})

        fam_string = " | ".join(fam_strings)
        xr_string = " | ".join(xr_strings)
        reg_string = " | ".join(reg_strings)

        # ── every token, and which route it came from
        #   route2 = the cross-reference's own vehicle_model string (the untried route)
        #   route3 = the registry model tag on the cross-reference row, and the family file's own
        #            model string
        #   route1 = the current EPC decode. It is reported for context and used to corroborate a
        #            route-2 or route-3 answer, but the family file's own band is itself derived
        #            from route 1, so a route-1/route-3 disagreement is not a source conflict.
        tokens: dict[str, set[str]] = {}

        def note(tok: str, route: str) -> None:
            tokens.setdefault(tok.upper(), set()).add(route)

        for s in xr_strings:
            for t in split_tokens(s):
                note(t, "route2_crossref")
        for s in reg_strings:
            for t in split_tokens(s):
                note(t, "route3_registry_tag")
        for s in fam_strings:
            for t in split_tokens(s):
                note(t, "route3_family_file")
        fam_route1_bands: set[str] = set()
        fam_epc_range = ""
        for fr in frows:
            b, rng = epc_bands_from_note(fr["source_note"])
            fam_route1_bands |= b
            if rng:
                fam_epc_range = rng
        # what the current decode already returns for this part number (route 1). These are band
        # names, not series tokens, so they are placed straight into the route's band set rather
        # than passed back through the token classifier.
        r1_cand = set(cand_bands.get(pn, set()))
        r1_fam = set(fam_route1_bands)
        r1_dec = set(banded_bands.get(pn, set()))
        r1_bands = r1_cand | r1_fam | r1_dec
        # route 1 is written by two generations of the same code and they do not always agree.
        # Where they differ the part number's band is not settled, and saying so is the point.
        r1_variants = sorted({tuple(sorted(x)) for x in (r1_cand, r1_fam, r1_dec) if x})
        r1_disagree = len(r1_variants) > 1
        # the EPC's raw series tokens are kept in the diagnostic column only, never used to band:
        # that is exactly the route the candidate table already reads and it does not help these
        # five families, so letting it into the decision would hide the gap rather than measure it.
        epc_pn_tokens = sorted(epc_tokens.get(pn, set()))
        nmr_note = ""
        if r1_disagree and any(t in ("NMR", "NMR85") for t in epc_pn_tokens):
            nmr_note = ("route 1 disagrees with itself on this part number because the two "
                        "generations of the series map place NMR on different rungs "
                        "(series_to_tonnage.csv 'NMR': 5.5t_N50_N55 against model_code_to_tonnage.csv "
                        "'NMR': 7.5t_N50_N62_N75), and this part number is returned under NMR")

        # ── resolve per route
        bands_by_route: dict[str, set[str]] = {}
        wild_by_route: dict[str, set[str]] = {}
        unres_by_route: dict[str, set[str]] = {}
        named_by_route: dict[str, set[str]] = {}
        for tok, routes in tokens.items():
            kind, band = classify(tok, smap)
            for rt in routes:
                if kind == "band":
                    bands_by_route.setdefault(rt, set()).add(band)
                    named_by_route.setdefault(rt, set()).add(tok)
                elif kind == "wildcard":
                    wild_by_route.setdefault(rt, set()).add(tok)
                elif kind == "unresolved":
                    unres_by_route.setdefault(rt, set()).add(tok)
                else:
                    named_by_route.setdefault(rt, set()).add(tok)
        if r1_bands:
            bands_by_route.setdefault("route1_current_decode", set()).update(r1_bands)
            named_by_route.setdefault("route1_current_decode", set()).update(r1_bands)

        # ── the decision
        #
        #   1. a source conflict: two routes each name a different SINGLE band. Route 3's
        #      registry tag is a second opinion on route 2's string. Route 1 is a third voice: on
        #      one part number it names 7.5 t while the cross-reference names 3.5 t and 5.5 t, which
        #      is a real unanswered question. The family file's own band is itself built from route
        #      1, so those two are collapsed into one route before comparing.
        conflict_routes = ["route1_current_decode", "route2_crossref", "route3_registry_tag"]
        singles = {rt: next(iter(bands_by_route[rt])) for rt in conflict_routes
                   if rt in bands_by_route and len(bands_by_route[rt]) == 1}
        conflict = len(set(singles.values())) > 1
        conflict_detail = "; ".join(f"{rt} says {b}" for rt, b in sorted(singles.items()))

        all_bands = sorted(set().union(*bands_by_route.values())) if bands_by_route else []
        all_wild = sorted(set().union(*wild_by_route.values())) if wild_by_route else []
        all_unres = sorted(set().union(*unres_by_route.values())) if unres_by_route else []

        if conflict:
            verdict = "conflicting"
        elif len(all_bands) == 1:
            verdict = "recoverable_single_band"
        elif len(all_bands) > 1:
            verdict = "recoverable_shared"
        elif all_wild:
            verdict = "wildcard_only"
        else:
            verdict = "no_evidence"

        # ── which evidence route decided it. The route that named a band is the decider; a route
        # that only corroborates is said so in the quote.
        band_routes = sorted(rt for rt in bands_by_route if bands_by_route[rt])
        if band_routes:
            used = band_routes
        elif all_wild:
            used = sorted(wild_by_route.keys())
        elif all_unres:
            used = sorted(unres_by_route.keys())
        else:
            used = []
        route_label = "+".join(used) or "none"
        # the family file's band derives from the EPC decode, so the two are one voice
        route_label = route_label.replace("route1_current_decode+route3_family_file",
                                          "route1_current_decode")
        route_label = route_label.replace("route3_family_file+route1_current_decode",
                                          "route1_current_decode")

        quotes = []
        if xr_string:
            q = f"cross-reference vehicle_model: '{xr_string}'"
            if engines:
                q += f" (engine_type {', '.join(engines)})"
            quotes.append(q)
        if reg_string:
            quotes.append(f"cross-reference registry_model: '{reg_string}'")
        if fam_string:
            quotes.append(f"family file vehicle_model: '{fam_string}'")
        if fam_route1_bands:
            quotes.append("family file band from the EPC decode: "
                          + "|".join(sorted(fam_route1_bands)))
        if fam_epc_range:
            quotes.append("the EPC names the vehicle class but no weight for this part number: "
                          + fam_epc_range)
        if r1_bands:
            quotes.append("the current decode already bands this part number: "
                          + "|".join(sorted(r1_bands)))
        if band_routes:
            named_toks = sorted(set().union(*(named_by_route.get(rt, set())
                                              for rt in band_routes)))
            named_toks = [t for t in named_toks if not t.endswith("*")]
            if named_toks:
                quotes.append("series that decided it: " + ", ".join(named_toks))
        if all_wild:
            quotes.append("wildcard tokens, never converted into a band: " + ", ".join(all_wild))
        if all_unres:
            quotes.append("tokens neither source resolves: " + ", ".join(all_unres))
        if conflict:
            quotes.append("CONFLICT " + conflict_detail)
        if r1_disagree:
            quotes.append("route 1 does not agree with itself on this part number: "
                          + " vs ".join("|".join(v) for v in r1_variants))
            if nmr_note:
                quotes.append(nmr_note)
        if not quotes:
            quotes.append("no model code or vehicle string on any source for this part number")

        tk_found = []
        for tok in sorted(tokens):
            kind, _b = classify(tok, smap)
            tk_found.append(f"{tok}(wildcard)" if kind == "wildcard" else tok)
        for b in sorted(r1_bands):
            tk_found.append(f"{b}(from the current decode)")

        # family-file resolution, for the write-up
        fam_res = frows[0]["resolution"] if frows else "not in the family file"
        in_cand = "yes" if pn in cand_bands else "no"
        in_bdec = "yes" if pn in banded_by_pn else "no"

        # confidence: a named series from the cross-reference or the registry tag is medium; route
        # 1 corroborating it lifts it to high; nothing but wildcards or unresolved tokens is low.
        if not all_bands:
            conf = "low"
        elif any(rt.startswith("route1") for rt in band_routes):
            conf = "high"
        else:
            conf = "medium"

        rows.append({
            "pms_category": pms,
            "part_number": r.part_number,          # string, zero padding preserved
            "eur_all": round(eur, 2),
            "units_all": units,
            "markets_billed": markets,
            "vehicle_string_from_crossref": xr_string,
            "registry_model": reg_string,
            "vehicle_string_from_family_file": fam_string,
            "series_tokens_found": ";".join(tk_found),
            "candidate_bands": "|".join(all_bands),
            "band_count": len(all_bands),
            "evidence_route": route_label,
            "evidence_quote": " || ".join(quotes),
            "confidence": conf,
            "verdict": verdict,
            # diagnostic columns (kept beside the required ones, never in place of them)
            "_family_file_resolution": fam_res,
            "_epc_vehicle_class_no_weight": fam_epc_range,
            "_route1_self_disagreement": ("yes" if r1_disagree else "no"),
            "_already_in_candidate_table": in_cand,
            "_already_in_banded_decode": in_bdec,
            "_in_epc_decode_tokens": ";".join(epc_pn_tokens),
        })

    out = pd.DataFrame(rows)
    for v in VERDICTS:
        if v not in set(out.verdict):
            pass
    order = {v: i for i, v in enumerate(VERDICTS)}
    out["_o"] = out.verdict.map(order)
    out = out.sort_values(["pms_category", "_o", "eur_all"],
                          ascending=[True, True, False]).drop(columns="_o")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    # ── the write-up
    req = ["pms_category", "part_number", "eur_all", "units_all", "markets_billed",
           "vehicle_string_from_crossref", "registry_model", "vehicle_string_from_family_file",
           "series_tokens_found", "candidate_bands", "band_count", "evidence_route",
           "evidence_quote", "confidence", "verdict"]
    total_eur = out.eur_all.sum()
    total_pns = len(out)

    def sl(verdicts):
        g = out[out.verdict.isin(verdicts)]
        return len(g), float(g.eur_all.sum()), float(g.units_all.sum())

    rec_pns, rec_eur, rec_u = sl(["recoverable_single_band", "recoverable_shared"])
    single_pns, single_eur, _ = sl(["recoverable_single_band"])
    shared_pns, shared_eur, _ = sl(["recoverable_shared"])
    wild_pns, wild_eur, _ = sl(["wildcard_only"])
    none_pns, none_eur, _ = sl(["no_evidence"])
    conf_pns, conf_eur, _ = sl(["conflicting"])
    # how much of the recoverable euro is genuinely new: a part number already in the candidate
    # table is not a recovery, it is a table that the tonnage view may simply not have read.
    new = out[(out.verdict.str.startswith("recoverable"))
              & (out._already_in_candidate_table == "no")]
    already = out[(out.verdict.str.startswith("recoverable"))
                  & (out._already_in_candidate_table == "yes")]

    lines = []
    lines.append("# Tonnage band recovery — five families with no candidates")
    lines.append("")
    lines.append("Proposal only. Nothing in `01_data/00_derived/` was written or changed; the "
                 "pipeline is rebuilt by separate scripts and no rebuild was authorised.")
    lines.append("")
    lines.append(f"Part numbers in scope: **{total_pns}** across five PMS families. "
                 f"Billed value across all markets and years: "
                 f"**EUR {total_eur:,.0f}**.")
    lines.append("")
    lines.append("## What is actually recoverable")
    lines.append("")
    lines.append("| Verdict | Part numbers | EUR all markets/years | Share of the EUR |")
    lines.append("|---|---:|---:|---:|")
    for label, (n, e, _u) in (
            ("recoverable — one band only", (single_pns, single_eur, 0)),
            ("recoverable — pooled over several bands", (shared_pns, shared_eur, 0)),
            ("wildcard only — a band cannot be read", (wild_pns, wild_eur, 0)),
            ("no evidence that yields a band", (none_pns, none_eur, 0)),
            ("conflicting between sources", (conf_pns, conf_eur, 0))):
        share = 100 * e / total_eur if total_eur else 0
        lines.append(f"| {label} | {n} | {e:,.0f} | {share:.1f}% |")
    lines.append(f"| **total** | **{total_pns}** | **{total_eur:,.0f}** | **100.0%** |")
    lines.append("")
    lines.append(f"Recoverable in total: **{rec_pns} part numbers, EUR {rec_eur:,.0f}** "
                 f"({100 * rec_eur / total_eur:.1f}% of the five-family book). Of that, "
                 f"{single_pns} part numbers (EUR {single_eur:,.0f}) land on exactly one band and "
                 f"{shared_pns} (EUR {shared_eur:,.0f}) fit two or more bands and must stay pooled.")
    lines.append("")
    lines.append(f"Within that, only **{len(new)} part numbers, EUR {new.eur_all.sum():,.0f}** is "
                 f"genuinely new. The other {len(already)} part numbers (EUR "
                 f"{already.eur_all.sum():,.0f}) are already carried by "
                 f"`tonnage_capable_part_numbers.csv` — they are recovered in the sense that they "
                 f"belong to this family, not in the sense that the tonnage view was missing them.")
    lines.append("")
    n_cls = out[(out.verdict == "no_evidence")
                & (out._epc_vehicle_class_no_weight.fillna("") != "")]
    n_abs = out[(out.verdict == "no_evidence")
                & (out._family_file_resolution == "no_vehicle_reference")]
    lines.append(f"Not recoverable: **{wild_pns} part numbers, EUR {wild_eur:,.0f}** rest on a "
                 f"wildcard, and **{none_pns} part numbers, EUR {none_eur:,.0f}** yield no band. "
                 f"The second group splits in two: **{len(n_abs)} part numbers, "
                 f"EUR {n_abs.eur_all.sum():,.0f}** have no vehicle named by any source, and "
                 f"**{len(n_cls)} part numbers, EUR {n_cls.eur_all.sum():,.0f}** are placed by the "
                 f"EPC in a vehicle class that carries no weight. "
                 + (f"A further {conf_pns} part numbers (EUR {conf_eur:,.0f}) have sources that "
                    f"disagree and were not resolved either way." if conf_pns else
                    "No part number in these five families had two different sources naming "
                    "different single bands."))
    lines.append("")
    lines.append("| Bucket | Part numbers | EUR |")
    lines.append("|---|---:|---:|")
    lines.append(f"| recoverable to a band | {rec_pns} | {rec_eur:,.0f} |")
    lines.append(f"| wildcard only | {wild_pns} | {wild_eur:,.0f} |")
    lines.append(f"| no band — no vehicle named by any source | {len(n_abs)} | {n_abs.eur_all.sum():,.0f} |")
    lines.append(f"| no band — vehicle class named but it carries no weight | {len(n_cls)} | {n_cls.eur_all.sum():,.0f} |")
    lines.append(f"| conflicting between sources | {conf_pns} | {conf_eur:,.0f} |")
    lines.append(f"| **total** | **{total_pns}** | **{total_eur:,.0f}** |")
    lines.append("")
    cls = out[(out.verdict == "no_evidence")
              & (out._epc_vehicle_class_no_weight.fillna("") != "")]
    if len(cls):
        classes = sorted(set(cls._epc_vehicle_class_no_weight))
        lines.append(
            f"**A distinction that matters:** {len(cls)} of the {none_pns} no-evidence part "
            f"numbers (EUR {cls.eur_all.sum():,.0f}) are not unknown. The EPC does name their "
            f"vehicle class — {'; '.join(classes)} — so we know they are light vehicles (D-Max "
            f"pickup and SUV). What is missing is the *weight*, and the reason is that the class "
            f"itself carries none: a D-Max is a light commercial vehicle, not a rung on the "
            f"3.5 t / 5.5 t / 7.5 t truck ladder. For these part numbers a tonnage band is not an "
            f"open question to be researched, it is a question the vehicle class makes meaningless. "
            f"They are recorded as `no_evidence` for a tonnage band, which is the honest reading, "
            f"but they should not be described as parts with no vehicle behind them.")
        lines.append("")
        lines.append("| Part number | Family | EUR | Unit | The EPC vehicle class |")
        lines.append("|---|---|---:|---:|---|")
        for _, rr in cls.sort_values("eur_all", ascending=False).head(15).iterrows():
            lines.append(f"| {rr['part_number']} | {rr['pms_category']} | {float(rr['eur_all']):,.0f} | "
                         f"{float(rr['units_all']):,.0f} | {rr['_epc_vehicle_class_no_weight']} |")
        if len(cls) > 15:
            lines.append(f"| … {len(cls) - 15} more | | | | |")
        lines.append("")

    lines.append("## Per family")
    lines.append("")
    lines.append("| Family | Part numbers | EUR | Recoverable EUR | of which already a candidate | "
                 "Wildcard-only EUR | No-evidence EUR |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for f in FAMILIES:
        g = out[out.pms_category == f]
        if not len(g):
            continue
        r = g[g.verdict.isin(["recoverable_single_band", "recoverable_shared"])]
        ra = r[r._already_in_candidate_table == "yes"]
        w = g[g.verdict == "wildcard_only"]
        n = g[g.verdict == "no_evidence"]
        c = g[g.verdict == "conflicting"]
        lines.append(f"| {f} | {len(g)} | {g.eur_all.sum():,.0f} | {r.eur_all.sum():,.0f} | "
                     f"{ra.eur_all.sum():,.0f} | {w.eur_all.sum():,.0f} | {n.eur_all.sum():,.0f} |")
        if len(c):
            lines.append(f"| {f} (conflicting) | {len(c)} | {c.eur_all.sum():,.0f} | — | — | — | — |")
    lines.append("")

    # per family: what the recovered band actually is
    lines.append("### Which band the recovered part numbers land on")
    lines.append("")
    lines.append("| Family | Recovered part numbers | Band | EUR |")
    lines.append("|---|---:|---|---:|")
    for f in FAMILIES:
        g = out[(out.pms_category == f) & out.verdict.str.startswith("recoverable")]
        if not len(g):
            lines.append(f"| {f} | 0 | — | 0 |")
            continue
        for band, gg in g.groupby("candidate_bands"):
            lines.append(f"| {f} | {len(gg)} | {band} | {gg.eur_all.sum():,.0f} |")
    lines.append("")

    lines.append("## The blocker, one line per family")
    lines.append("")
    for f in FAMILIES:
        g = out[out.pms_category == f]
        r = g[g.verdict.str.startswith("recoverable")]
        w = g[g.verdict == "wildcard_only"]
        n = g[g.verdict == "no_evidence"]
        # the two different reasons a part number has no band: nothing names a vehicle at all,
        # versus a vehicle class is named but the class carries no weight.
        n_none = n[n._family_file_resolution == "no_vehicle_reference"]
        n_cls = n[n._epc_vehicle_class_no_weight.fillna("") != ""]
        bits = []
        if len(r):
            bands = sorted(set(r.candidate_bands))
            bits.append(f"{len(r)} of {len(g)} recoverable (EUR {r.eur_all.sum():,.0f}) to "
                        f"{', '.join(bands)}")
        if len(w):
            common = w.series_tokens_found.fillna("").value_counts().head(3)
            bits.append(f"{len(w)} wildcard-only (EUR {w.eur_all.sum():,.0f}) on "
                        + "; ".join(f"`{k}` x{v}" for k, v in common.items()))
        if len(n_none):
            bits.append(f"{len(n_none)} have no vehicle named by any source (EUR "
                        f"{n_none.eur_all.sum():,.0f})")
        if len(n_cls):
            bits.append(f"{len(n_cls)} are placed by the EPC in a vehicle class that carries no "
                        f"weight (EUR {n_cls.eur_all.sum():,.0f})")
        if not len(bits):
            bits.append("nothing to report")
        lines.append(f"- **{f}** — " + "; ".join(bits) + ".")
    lines.append("")
    lines.append("The last two lines of each entry are the two different reasons a part number has "
                 "no band, and they are not the same problem. *No vehicle named by any source* "
                 "means the evidence is absent. *A vehicle class that carries no weight* means the "
                 "evidence is present and the ladder simply has no rung for it.")
    lines.append("")

    lines.append("## The brake rotor control")
    lines.append("")
    br = out[out.pms_category == "brake_rotor"]
    br_rec = br[br.verdict.str.startswith("recoverable")]
    br_none = br[br.verdict == "no_evidence"]
    br_noveh = br_none[br_none._family_file_resolution == "no_vehicle_reference"]
    br_cls = br_none[br_none._epc_vehicle_class_no_weight.fillna("") != ""]
    br_wild = br[br.verdict == "wildcard_only"]
    lines.append(
        f"Brake rotor is the family the scoping pass called a dead end. This pass **confirms the "
        f"headline and corrects one supporting fact**.")
    lines.append("")
    lines.append(
        f"**Confirmed.** Of the {len(br)} part numbers worth EUR {br.eur_all.sum():,.0f}, exactly "
        f"**one** carries a vehicle string at all, and that string is `N*R,N*S`. `N*R` and `N*S` "
        f"are wildcards — they stand for the whole N-series, not a weight class — so by this "
        f"workspace's own rule they cannot become a band. That one part number (8973872290) is "
        f"therefore recorded as `wildcard_only`, not banded. No part number in this family reached "
        f"a band from route 2 or route 3. The family cannot be banded as a family.")
    lines.append("")
    lines.append(
        f"**Corrected.** The scoping reading said the whole family carries exactly one vehicle "
        f"string. That is not quite right. Seven part numbers carry real EPC bands from route 1 — "
        f"EUR {br_rec.eur_all.sum():,.0f}, {br_rec.eur_all.sum() / br.eur_all.sum() * 100:.1f}% of "
        f"the family book — one of them (8981919560, EUR 316,996) on a single band (7.5 t) and six "
        f"pooled across the three bands. All seven are already in "
        f"`tonnage_capable_part_numbers.csv`, so they are not a gap; they are evidence the family "
        f"was never literally zero-candidate.")
    lines.append("")
    lines.append(
        f"The genuinely unbandable part is the remaining {len(br_none)} (EUR "
        f"{br_none.eur_all.sum():,.0f}, {br_none.eur_all.sum() / br.eur_all.sum() * 100:.1f}% of "
        f"the book), and it splits in two. {len(br_noveh)} of them (EUR {br_noveh.eur_all.sum():,.0f}) "
        f"have no vehicle named by any source — absent evidence. The other {len(br_cls)} "
        f"(EUR {br_cls.eur_all.sum():,.0f}) are placed by the EPC in a vehicle class that carries "
        f"no weight (D-Max pickup and SUV) — present evidence, and no rung to put it on.")
    lines.append("")
    lines.append(
        f"So the honest verdict is: brake rotor is a dead end **for tonnage**, but the reason is "
        f"not thin evidence. EUR "
        f"{br_rec.eur_all.sum() + br_wild.eur_all.sum() + br_cls.eur_all.sum():,.0f} of the family "
        f"book — "
        f"{100 * (br_rec.eur_all.sum() + br_wild.eur_all.sum() + br_cls.eur_all.sum()) / br.eur_all.sum():.1f}% "
        f"— does carry a vehicle reference of some kind. What it does not carry is a *weight*: "
        f"brake rotors are sold across every N-series rung and the pickups at once, and the "
        f"reference the catalogue kept is a wildcard or a family label rather than a series. The "
        f"remaining {len(br_noveh)} part numbers, EUR {br_noveh.eur_all.sum():,.0f}, are the only "
        f"ones where the evidence is genuinely absent.")
    lines.append("")

    lines.append("## What a reader would see wrong if the tonnage view shipped without these "
                 "families")
    lines.append("")
    lines.append(
        f"The tonnage page reads service demand by vehicle weight. Any part number this table "
        f"cannot band is not dropped from the billing — it is simply absent from the band columns, "
        f"so the bands understate the demand that actually went through those vehicles. These five "
        f"families carry EUR {total_eur:,.0f} and {int(out.units_all.sum()):,} billed units across "
        f"all markets and years. Brake rotor alone is EUR {out[out.pms_category == 'brake_rotor'].eur_all.sum():,.0f} "
        f"on {int(out[out.pms_category == 'brake_rotor'].units_all.sum()):,} units — a wear part "
        f"that is serviced on every truck class, so the missing euro sits against every rung of the "
        f"ladder at once rather than against one band.")
    lines.append("")
    lines.append(
        "Three specific errors follow. First, the 3.5 t and 7.5 t bands would each read lower than "
        "they should, by an amount nobody can attribute, because the same part number is invoiced "
        "against both classes. Second, a reader comparing bands would see a share split that is "
        "really a coverage artefact: a family with no band rows looks like a family with no demand "
        "in that class. Third, the brake rotor gap is the largest single hole in the take and it is "
        "a wear part, so its absence flatters the vehicle classes that are already banded — a "
        f"reader would conclude the N-series trucks are under-serviced on brakes when in fact EUR "
        f"{out[out.pms_category == 'brake_rotor'].eur_all.sum():,.0f} of brake rotor sales simply "
        f"has nowhere to sit.")
    lines.append("")
    lines.append(
        f"The blower filter is the clearest illustration of the vocabulary gap: it is a D-Max "
        f"pickup and SUV part worth EUR "
        f"{out[out.pms_category == 'blower_filter'].eur_all.sum():,.0f}, and it is absent from the "
        f"tonnage view entirely because the band vocabulary the candidate table uses has no LCV "
        f"rung. Nothing is wrong with the part's evidence — 'TF*,UC*' names the pickup and the SUV "
        f"plainly. It is the weight ladder that has no place to put it.")
    lines.append("")

    lines.append("## Method and rules applied")
    lines.append("")
    lines.append("- Routes attempted: the cross-reference `vehicle_model` string (route 2); the "
                 "cross-reference `registry_model` tag and the family file's own model string "
                 "(route 3). Route 1 (the current EPC decode) is read for context and for the "
                 "handful of part numbers it already bands.")
    lines.append("- Series tokens are matched as whole anchored tokens, never substrings. "
                 "`series_to_tonnage.csv` is the authority for what a token means.")
    lines.append("- Wildcards (`N*R`, `N*S`, `TF*`, `UC*`, `F*`, `EX*`, `CX*`, `CY*`, `N*`, `FS*`, "
                 "`FT*`, `FV*`, `FX*`, `E*`, `C*`) are recorded and never converted into a band. "
                 "This is the guard against the documented error where `F*` matched `TF*`, the "
                 "D-Max pickup wildcard, and inflated a heavy-truck figure by about EUR 1.8M.")
    lines.append("- A part number that fits several bands is pooled, never apportioned.")
    lines.append("- Where two sources name different single bands the verdict is `conflicting` and "
                 "no side is taken. **No part number in these five families reached that verdict** "
                 "— but see the next section, because route 1 disagrees with itself.")
    lines.append("- Part numbers are strings; zero padding is preserved.")
    lines.append("")

    # ── the route 1 self-disagreement, which is a finding in its own right
    dd = out[out._route1_self_disagreement == "yes"]
    lines.append("## A disagreement I found between two generations of the route 1 mapping")
    lines.append("")
    lines.append(
        f"Route 1 — the current EPC decode — is written into three files, and on "
        f"{len(dd)} part numbers (EUR {dd.eur_all.sum():,.0f} of the family book) those files do "
        f"not agree with each other:")
    lines.append("")
    lines.append("| Part number | Family | EUR | candidate table | `vehicle_family_bands` | "
                 "`epc_decode_nseries_banded` |")
    lines.append("|---|---|---:|---|---|---|")
    for _, rr in dd.sort_values("eur_all", ascending=False).iterrows():
        pn = rr["part_number"]
        cv = sorted(cand_bands.get(norm(pn), set()))
        fv = sorted(fam_route1_by_pn.get(norm(pn), set()))
        bv = sorted(banded_bands.get(norm(pn), set()))
        lines.append(f"| {pn} | {rr['pms_category']} | {float(rr['eur_all']):,.0f} | "
                     f"{'|'.join(cv) or 'not listed'} | {'|'.join(fv) or 'none'} | "
                     f"{'|'.join(bv) or 'none'} |")
    lines.append("")
    lines.append(
        "The cause is traceable and it is a single model code. `03_analytics/Isuzu/prism/data/"
        "model_code_to_tonnage.csv` — the older mapping, which produced "
        "`epc_decode_batch1_banded_20260919.csv` — was itself internally inconsistent: it carried "
        "`'NMR': 5.5t` in its docstring while the table body and its output put NMR on "
        "`7.5t_N50_N62_N75`. The rebuild (`series_to_tonnage.csv` / "
        "`epc_decode_nseries_banded.csv`, 22 September) sets NMR to `5.5t_N50_N55` at medium "
        "confidence, which is why the two generations now differ. Every part number the EPC "
        "returns under NMR is therefore affected: the newer decode adds a 5.5 t band the older one "
        "did not have.")
    lines.append("")
    lines.append("I have not resolved it, because resolving it means deciding which of the two NMR "
                 "placements is right, and that is a data-owner decision rather than a reading of "
                 "the files. It is flagged because it moves real money on these six part numbers — "
                 f"EUR {dd.eur_all.sum():,.0f} — and because the same NMR question will touch every "
                 "part number the EPC returns under NMR, not only the five families in scope. The "
                 "per-row `evidence_quote` in the proposal records which generation said what for "
                 "each one.")
    lines.append("")

    lines.append("## Two things a reader should know about the band vocabulary")
    lines.append("")
    lines.append(
        "`F_series` is one of the four bands the analysis reads, and it is what the F&G codes "
        "resolve to. The candidate table that produced the gap has no F-series rung at all — its "
        "band vocabulary is the three N-series rungs only — so F-series part numbers could never "
        "appear in it however good their evidence was. That is why the whole clutch booster family "
        "reads as a gap.")
    lines.append("")
    lines.append(
        "`LCV_D-Max` is carried beside the four. The shipped tonnage model treats the D-Max class "
        "as a band of its own, and the EPC names it cleanly, but it is not a truck tonnage rung. "
        "Part numbers that resolve only to LCV are marked as such rather than forced onto a "
        "truck band.")
    lines.append("")

    lines.append("## Checks run")
    lines.append("")
    lines.append(f"- Part numbers in the proposal: {len(out)}. Worklist rows in the five families: "
                 f"{len(sub)}. Equal: {len(out) == len(sub)}.")
    lines.append(f"- One row per part number, no duplicates: "
                 f"{len(out) == out.part_number.nunique()}.")
    lines.append(f"- Value tie-out: proposal EUR {out.eur_all.sum():,.2f} against worklist "
                 f"EUR {float(sub.eur_all.astype(float).sum()):,.2f}.")
    lines.append(f"- Verdicts used: {sorted(set(out.verdict))}.")
    lines.append(f"- Every row carries one of the five permitted verdicts: "
                 f"{set(out.verdict).issubset(set(VERDICTS))}.")
    lines.append(f"- No part number's band rests on a wildcard: "
                 f"{not any('*' in b for b in out.candidate_bands if b)}.")
    lines.append(f"- Part numbers kept as strings; zero padding is preserved by reading with "
                 f"`dtype=str` and never coercing.")
    lines.append(f"- Part numbers the EPC never decoded (no model string anywhere): "
                 f"{int((out._in_epc_decode_tokens.fillna('') == '').sum())}.")
    lines.append(f"- Already in `tonnage_capable_part_numbers.csv`: "
                 f"{int((out._already_in_candidate_table == 'yes').sum())} part numbers.")
    lines.append(f"- Already in `epc_decode_nseries_banded.csv`: "
                 f"{int((out._already_in_banded_decode == 'yes').sum())} part numbers.")
    lines.append("")
    lines.append("Diagnostic columns `_family_file_resolution`, `_epc_vehicle_class_no_weight`, "
                 "`_already_in_candidate_table`, `_already_in_banded_decode` and "
                 "`_in_epc_decode_tokens` are carried at the end of the CSV so the decision can be "
                 "audited; they are not part of the requested schema.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"proposal : {len(out)} rows -> {OUT_CSV}")
    print(f"write-up : {OUT_MD}")
    print()
    print(f"  {'family':16s} {'PNs':>4s} {'EUR':>12s} {'recoverable':>12s} {'wildcard':>11s} "
          f"{'none':>11s} {'conflict':>10s}")
    for f in FAMILIES:
        g = out[out.pms_category == f]
        r = g[g.verdict.str.startswith("recoverable")]
        w = g[g.verdict == "wildcard_only"]
        n = g[g.verdict == "no_evidence"]
        c = g[g.verdict == "conflicting"]
        print(f"  {f:16s} {len(g):4d} {g.eur_all.sum():12,.0f} {r.eur_all.sum():12,.0f} "
              f"{w.eur_all.sum():11,.0f} {n.eur_all.sum():11,.0f} {c.eur_all.sum():10,.0f}")
    print()
    print(f"  recoverable   : {rec_pns:3d} PNs  EUR {rec_eur:12,.0f}  "
          f"(single {single_pns} / EUR {single_eur:,.0f}; shared {shared_pns} / "
          f"EUR {shared_eur:,.0f})")
    print(f"  wildcard only : {wild_pns:3d} PNs  EUR {wild_eur:12,.0f}")
    print(f"  no evidence   : {none_pns:3d} PNs  EUR {none_eur:12,.0f}")
    print(f"  conflicting   : {conf_pns:3d} PNs  EUR {conf_eur:12,.0f}")
    print(f"  total         : {total_pns:3d} PNs  EUR {total_eur:12,.0f}")
    print()
    print("  verdict counts:", dict(Counter(out.verdict)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
