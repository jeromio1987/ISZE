#!/usr/bin/env python3
"""
N-series tonnage bands: series -> tonnage, the banded part numbers, and the evolution.

Why this exists
---------------
The family page stops at "N-series truck", because the EPC vehicle family `TRUCKS N` spans NLR to
NQR and a family label carries no weight. That is true of the *family* label. It is **not** true of
the EPC editions themselves: each edition string names the series range it covers, for example

    '2018 NNR/NPR-RHD EURO6 EUROPE'   -> NNR, NPR
    '18-  NLR/NMR-RHD EURO6 EUROPE'   -> NLR, NMR
    '15-  NN/NP/NQR EURO5,5B+,6 LHD'  -> NN, NP, NQR

so the series is already in hand per part number. What was missing is a **sourced** series ->
tonnage mapping, which is a far smaller problem than "tonnage is unknowable".

How a series is read, and the one pattern that may be used
---------------------------------------------------------
`epc_decode_batch1_banded_20260919.csv` already carries `model_codes`, the series tokens the EPC
returns for that part number, produced by stripping the leading model year off each edition string
and splitting the `NLR/NMR` block on the slash. This script reads those tokens and the
cross-reference's `vehicle_model` column.

Every token is matched as a **whole token**, never as a substring: `NLR` matches `NLR` and nothing
else. That matters here — an earlier error in this workstream came from an `F*` substring test that
also matched `TF*` (the D-Max pickup) and inflated a heavy-truck figure by EUR 1.8M. The wildcard
tokens the cross-reference carries (`N*`, `TF*`, `N*R`) are recorded as `wildcard_token` and are
**not** converted into a band: `N*` spans the whole N-series and would put a part in all three bands
at once, which is not a fact about the vehicle.

Sources, in the order they are trusted
--------------------------------------
1. Duncan Young / ITUK PMS brake deck, slide 14 — names NLR87/NLR88 as N35 (3.5 t) and NPR75/NPR88
   as N75 (7.5 t) by segment name.
2. René Paul / GIDSS workshop-manual prints — the maintenance schedules are headed by model set:
   p1 'NLR88/NMR88/NPR88 models (4JZ1 engine model)', p3 'NPR75 model (4HK1 engine model)',
   p6 'NLR87 model (RZ4E engine model)'. They separate NLR87 from the NLR88/NMR88/NPR88 group but
   do not give a weight for NMR.
3. The JP VIN register (`01_data/07_UIO/vin/model_dimension.csv`) — the manufacturer's own model
   names, e.g. `NMR85L-FH5AYE` with the register's GVW column at 5.5 t, `NLR88L-FC5Y` at 3.5 t,
   `NPR75L-FL5VAY` at 7.5 t, `NNR85U-HD5AYE` at 6.5 t. This is a measured value, not a quote.

A series neither source names is written `unresolved` with the reason. No guess, no wildcard.

Reads : 01_data/00_derived/epc_decode_batch1_banded_20260919.csv
        01_data/00_derived/epc_decode_batch1_20260919.json
        01_data/00_derived/epc_decode_batch2_20260919.json
        01_data/00_derived/vehicle_family_bands.csv
        01_data/00_derived/genuine_bvp_crossref.csv
        01_data/00_derived/bvp_pn_dimension.csv
        03_analytics/Isuzu/prism/data/pms_capture_supplement.csv
        02_dashboards/sales/_build/_deep_billing_cache.parquet   (the tagged service-part billing;
             rebuilt from source if the cache is absent, through the project's own tagging path)
Writes: 01_data/00_derived/series_to_tonnage.csv
        01_data/00_derived/epc_decode_nseries_banded.csv
        01_data/00_derived/nseries_tonnage_evolution.csv
        01_data/00_derived/nseries_tonnage_evolution.meta.json

Run: python 03_analytics/Isuzu/prism/scripts/build_nseries_tonnage_bands.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
PDATA = PRISM / "data"
CACHE = ROOT / "02_dashboards" / "sales" / "_build" / "_deep_billing_cache.parquet"

sys.path.insert(0, str(PRISM))
from modules import vehicle_bands  # noqa: E402

OUT_SERIES = DER / "series_to_tonnage.csv"
OUT_BANDED = DER / "epc_decode_nseries_banded.csv"
OUT_EVO = DER / "nseries_tonnage_evolution.csv"
OUT_META = DER / "nseries_tonnage_evolution.meta.json"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# The date the EPC decode / series mapping this file is built from was taken. It is NOT the
# billing window: the billing runs to whatever the tagged frame carries, and the billing window
# is written to the meta as `billing_through`, read from the data. Named `snapshot` until
# 2026-09-22, which read as though it dated the billing and was misquoted as the billing window.
DECODE_SNAPSHOT = "2026-09-19"

BAND_N35 = "3.5t_N35"
BAND_N50 = "5.5t_N50_N55"
BAND_N75 = "7.5t_N50_N62_N75"

# --- CANONICAL FOUR-BAND SET (Jerome, 2026-09-22) ---------------------------------------------
# Decision: the car park and every dashboard show FOUR bands, and they must match the GPS wallet
# bands in `prism/data/gps_model_targets.csv` so a band never carries a weight it does not contain.
#
#   3.5 t        -> N35 Grafter                                  wallet EUR 296
#   5.5 - 7.5 t  -> N55 / N65 / N75  (NMR 5.5, NNR 6.5, NPR 7.5) wallet EUR 739
#   11 - 13.5 t  -> F110 / F135      (FRR 11, FSR 13.5)          wallet EUR 887
#   pickup       -> D-Max / LCV                                  wallet EUR 250
#
# DELIBERATE: the top band is labelled "11-13.5 t", NOT "13.5 t". We shipped 284 FRR (11 t) against
# only 30 FSR (13.5 t), so a band named 13.5 would be ~90% eleven-tonne trucks wearing the wrong
# name. There is no 10 t and no 11.5 t truck in the European range (N35 3.5 / N55 5.5 / N65 6.5 /
# N75 7.5 / F110 11 / F135 13.5); the Israeli ministry's 10-12 t band is a foreign reporting band,
# not an Isuzu model, and is mapped onto these bands rather than reproduced as a row.
BAND_F_SERIES = "11_13_5t_F110_F135"
BAND_LCV_PICKUP = "pickup_LCV"

CANONICAL_FOUR_BANDS = [BAND_N35, BAND_N50, BAND_N75, BAND_F_SERIES]
CANONICAL_BAND_LABEL = {
    BAND_N35: "3.5 t",
    BAND_N50: "5.5 - 7.5 t",
    BAND_N75: "5.5 - 7.5 t",
    BAND_F_SERIES: "11 - 13.5 t",
    BAND_LCV_PICKUP: "Pickup",
}
UNRESOLVED = "unresolved"
NOT_N = "not_n_series"
BANDS = [BAND_N35, BAND_N50, BAND_N75]
BAND_LABEL = {
    BAND_N35: "3.5 t GVW (N35 Grafter)",
    BAND_N50: "5.5 t GVW (N50 / N55)",
    BAND_N75: "7.5 t class (N50 / N62 / N75)",
}
# The page groups: the three bands, the pool, and the series the sources do not state.
GROUP_SHARED = "shared_across_bands"
GROUP_UNRESOLVED = "unresolved_series"
GROUP_ORDER = [BAND_N35, BAND_N50, BAND_N75, GROUP_SHARED, GROUP_UNRESOLVED]
GROUP_LABEL = {
    BAND_N35: "3.5 t (N35 Grafter)",
    BAND_N50: "5.5 t (N50 / N55)",
    BAND_N75: "7.5 t (N50 / N62 / N75)",
    GROUP_SHARED: "Parts shared across more than one band",
    GROUP_UNRESOLVED: "Tonnage not stated by the sources",
}

# The extract this used to cite (01_data/90_INBOX/_ituk_brake_spa_20260915/pptx_dump.txt) is gone
# from disk (checked 2026-09-23); the same four interval rows survive verbatim in the April deck text.
DUNCAN = ("Duncan Young / ITUK PMS brake deck, slide 14 'Appendix: Service Intervals' — the same four "
          "interval rows, verbatim, in the Isuzu Truck UK 'PMS Project Feedback 27 April 2026' deck "
          "text, table 'Maintenance Interval Implications' — "
          "09_meetings/Preparation Meetings/IML_ITUK_PMS/feedback_deck_text.txt lines 17-22")
RENE24 = ("René Paul / GIDSS workshop-manual print GIDSS_maint_N_MY24.pdf — "
          "01_data/03_PMS/service_schedules/")
RENE14 = ("René Paul / GIDSS workshop-manual print GIDSS_maint_N_MY14.pdf — "
          "01_data/03_PMS/service_schedules/")
VINREG = ("JP VIN register — 01_data/07_UIO/vin/model_dimension.csv, the GVW column beside the "
          "manufacturer's own model names (NLR88L-FC5Y / NMR85L-FH5AYE / NPR75L-FL5VAY)")

# ---------------------------------------------------------------------------------------------
# The series table is NO LONGER held here.
#
# Until 2026-09-23 this file carried its own `TABLE` dictionary of series -> band, and two other
# files carried their own copies. They disagreed (the retired probe had `NKR` at 5.5 t; the
# model-code table put `NMR` on the 7.5 t band while its own weight label read 5.5 t), so the
# same truck could get a different weight depending on which file was opened.
#
# The single authored source is now `03_analytics/Isuzu/prism/data/series_to_band.csv`, read
# through `modules/vehicle_bands.py`. This file keeps NO dictionary. To change a mapping, edit
# the CSV - not this script.
# ---------------------------------------------------------------------------------------------
TABLE: dict[str, tuple[str, str, str, str, str]] = {}


def _load_table() -> dict[str, tuple[str, str, str, str, str]]:
    """The sourced series table, from the one canonical file."""
    out: dict[str, tuple[str, str, str, str, str]] = {}
    for code, r in vehicle_bands.load_map().items():
        band = (r.get("tonnage_band") or "").strip()
        out[code] = (
            band or vehicle_bands.UNRESOLVED,
            (r.get("weight_label") or "").strip(),
            (r.get("evidence_source") or "").strip(),
            (r.get("evidence_quote") or "").strip(),
            (r.get("confidence") or "").strip(),
        )
    return out


TABLE = _load_table()


# ── the series table now comes from the canonical map, so the per-series `add()` calls that
#    used to sit here are gone. NLR / NKR (3.5 t), NMR (5.5 t interim, pending ruling), NPR /
#    NQR / NNR / NPS / NRR (7.5 t) and every unresolved code all come from
#    `03_analytics/Isuzu/prism/data/series_to_band.csv` via `_load_table()` above.

# ── series named on N-series part numbers that neither authoritative source resolves.
#    The notes live in the canonical CSV now; this list only says which codes are meant to be
#    unresolved, so a code added to the CSV without a note is caught rather than assumed.
UNRESOLVED_NOTES = {
    "NN", "NP", "NHR", "NJR", "NJS", "NKS", "NK", "NJ", "NL", "NLS", "NMS", "NMS85", "NNS",
    "NQS", "NHS", "NQ", "PHR", "QKR", "QLR", "QMR", "TBR", "NAN",
}


# ── the anchors that are on the same part numbers but are not a rung of the N-series ladder.
#    The D-Max pickup/SUV and the F&G heavy range are vehicle groups in their own right, not
#    tonnage rungs, and the canonical map is where that is recorded now. The old `not_n_series`
#    label is kept as an alias so nothing that reads it breaks.
NOT_N = "not_n_series"


def _check_canonical() -> None:
    """Fail loudly if the canonical map drifts from what this build assumes."""
    missing = UNRESOLVED_NOTES - set(TABLE)
    if missing:
        raise SystemExit(f"canonical map is missing unresolved codes: {sorted(missing)}")
    for code in ("NLR", "NKR", "NPR", "NMR", "NNR"):
        if not TABLE.get(code):
            raise SystemExit(f"canonical map has no row for {code}")
    for code in ("NMR",):
        if not vehicle_bands.is_pending_ruling(code):
            print(f"  NOTE: {code} is no longer marked pending_ruling in the canonical map.")


_check_canonical()


# ── the registry supplement inside the cross-reference file. 27 of the 544 pairs carry a
# `registry_model` tag of the form N35_RZ4E / N75_4HK1 / N75_4JZ1, which is the same split the ITUK
# brake deck draws on slide 14. It is used as a second opinion beside the deck's vehicle string,
# and where the two disagree the part is pooled rather than trusted to either.
REGISTRY_PREFIX_BAND = {"N35": BAND_N35, "N50": BAND_N50, "N55": BAND_N50,
                        "N62": BAND_N75, "N65": BAND_N75, "N75": BAND_N75}


def band_from_registry_model(value: str) -> tuple[str, str, str]:
    """(band, quote, confidence) from a `registry_model` tag such as N75_4JZ1. Empty when absent."""
    v = str(value or "").strip().upper()
    if not v or v in ("NAN", "NONE"):
        return "", "", ""
    head = v.split("_", 1)[0]
    band = REGISTRY_PREFIX_BAND.get(head)
    if not band:
        return "", "", ""
    eng = v.split("_", 1)[1] if "_" in v else ""
    quote = (f"the cross-reference's own registry model tag '{v}' for this part number. "
             f"Duncan slide 14 ties the {head} segment to these engine codes "
             f"('N35.125 | NLR87 / RZ4E', 'N35.150 | NLR88 / 4JZ1', 'N75 | NPR75 / 4HK1', "
             f"'N75 | NPR88 / 4JZ1'). It is a second opinion, taken beside the deck's own vehicle "
             f"string — where the two disagree the part is pooled.")
    if eng == "4JZ1":
        quote += (" Caution: 4JZ1 is the engine in both NLR88 (the deck's N35.150) and NPR88 (N75), "
                  "so the engine code alone cannot separate 3.5 t from 7.5 t.")
    return band, quote, "medium"


def tbl(code: str) -> tuple[str, str, str, str, str]:
    return TABLE.get(code.upper(), (UNRESOLVED, "not stated in the two authoritative sources",
                                    "no source — left blank on purpose",
                                    "Not named in any source on disk.", "unresolved"))


# ── token parsing. Whole tokens only, never substrings.
TOKEN_RE = re.compile(r"^N[A-Z]{1,4}\d{0,3}$")
WILDCARD_RE = re.compile(r"^N[A-Z]{0,2}\*$")


def tokens_from_model_codes(value: str) -> tuple[list[str], list[str]]:
    """(series tokens, wildcard tokens) from the `model_codes` column the EPC decode already wrote."""
    out, wild = [], []
    for t in (x.strip().upper() for x in str(value or "").split(",")):
        if not t:
            continue
        if WILDCARD_RE.match(t):
            wild.append(t)
        elif TOKEN_RE.match(t) and not t.startswith("NAN"):
            out.append(t)
    return out, wild


def tokens_from_crossref(value: str) -> tuple[list[str], list[str]]:
    out, wild = [], []
    # '、' and '，' are list separators too: the cross-reference writes 'NKR、NMR,NLR' for
    # 5878320470, and splitting on ',' alone left 'NKR、NMR' as one unmatched token, so the part
    # read as NLR-only and landed in the 3.5 t exclusive set (EUR 2,645.43; corrected 2026-09-23).
    for raw in re.split(r"[,\s、，]+", str(value or "").upper()):
        t = raw.strip().strip("()[]{}").strip()
        if not t:
            continue
        if WILDCARD_RE.match(t):
            wild.append(t)
        elif TOKEN_RE.match(t) and t != "NAN":
            out.append(t)
    return out, wild


def bands_for(tokens: list[str]) -> tuple[list[str], list[str]]:
    """(bands, tokens that stayed unresolved). Anchors outside the N-series are ignored."""
    bands, unknown = [], []
    for t in tokens:
        band = tbl(t)[0]
        if band in BANDS:
            if band not in bands:
                bands.append(band)
        elif band == UNRESOLVED:
            unknown.append(t)
    return sorted(bands), sorted(set(unknown))


# ── billing: the project's own tagged service-part frame, the same one the page uses
BOOK_MARKETS = None


def read_billing() -> tuple[pd.DataFrame, str]:
    if CACHE.is_file():
        return pd.read_parquet(CACHE), str(CACHE)
    sys.path.insert(0, str(PRISM))
    from config import resolve_mapping_path  # noqa: PLC0415
    from modules.data_prep import load_distributor_mapping  # noqa: PLC0415
    from modules.pms_tagging import tag_pms_sales  # noqa: PLC0415
    from modules.sales_loader import load_prism_sales  # noqa: PLC0415

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    raw, _ = load_prism_sales(df_map)
    dim = pd.concat([pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str, low_memory=False),
                     pd.read_csv(PDATA / "pms_capture_supplement.csv", dtype=str,
                                 low_memory=False)], ignore_index=True)
    sf = tag_pms_sales(raw, dim, fill_catalog_pms=True)
    sf = sf[sf.is_pms.fillna(False)].copy()
    if "is_credit_note" in sf.columns:
        sf = sf[~sf.is_credit_note.fillna(False).astype(bool)].copy()
    if "pms_capture_eligible" in sf.columns:
        sf = sf[sf.pms_capture_eligible.fillna(True).astype(bool)].copy()
    sf = sf.rename(columns={"net_sales_value": "net_sales_value"})
    sf["pn"] = sf.part_number.map(norm)
    sf["db"] = sf.distributor_code
    sf["y"] = sf.year.astype("Int64")
    sf["m"] = sf.month.astype("Int64")
    sf["fy"] = sf.y + (sf.m >= 4).astype("Int64")
    return sf[["pn", "db", "y", "m", "fy", "net_sales_value", "billed_qty"]], "rebuilt from source"


def main() -> int:
    # ── 1. the series table. Written FROM the canonical map, not from anything held here.
    rows = []
    for code, (band, label, source, quote, conf) in sorted(TABLE.items()):
        rows.append({"series": code, "tonnage_band": band, "weight_label": label,
                     "evidence_source": source, "evidence_quote": quote, "confidence": conf})
    pd.DataFrame(rows).to_csv(OUT_SERIES, index=False)
    print(f"series table  : {len(rows)} series -> {OUT_SERIES.name} "
          f"(from {vehicle_bands.MAP_CSV.name})")
    print(f"  resolved    : {sum(1 for r in rows if r['tonnage_band'] in BANDS)}   "
          f"unresolved: {sum(1 for r in rows if r['tonnage_band'] == UNRESOLVED)}   "
          f"not N-series: {sum(1 for r in rows if r['tonnage_band'] == NOT_N)}")
    pend = vehicle_bands.pending_ruling_codes()
    if pend:
        print(f"  PENDING RULING (interim band, do not quote as settled): {pend}")

    # ── 2. band every N-series part number
    bands_tbl = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False)
    bands_tbl["pn"] = bands_tbl.pn.map(norm)
    fam_of = dict(zip(bands_tbl.pn, bands_tbl.family))
    res_of = dict(zip(bands_tbl.pn, bands_tbl.resolution))
    cat_of = dict(zip(bands_tbl.pn, bands_tbl.pms_category))

    b1 = pd.read_csv(DER / "epc_decode_batch1_banded_20260919.csv", dtype=str, low_memory=False)
    b1["pn"] = b1.pn.map(norm)
    epc_series: dict[str, list[str]] = {}
    epc_series_unresolved: dict[str, list[str]] = {}
    for r in b1.itertuples():
        s, _w = tokens_from_model_codes(r.model_codes)
        epc_series[r.pn] = s
    dec2 = json.loads((DER / "epc_decode_batch2_20260919.json").read_text(encoding="utf-8"))
    for r in dec2:
        pn = norm(r["pn"])
        codes = []
        for m in r.get("models") or []:
            codes.extend(parse_codes_from_edition(m))
        s, _w = tokens_from_model_codes(", ".join(codes))
        if pn in epc_series:
            epc_series[pn] = sorted(set(epc_series[pn]) | set(s))
        else:
            epc_series[pn] = sorted(set(s))

    xr = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False)
    xr_series: dict[str, list[str]] = defaultdict(list)
    xr_wild: dict[str, list[str]] = defaultdict(list)
    xr_regband: dict[str, set[str]] = defaultdict(set)
    xr_regquote: dict[str, dict[str, str]] = defaultdict(dict)
    xr_reg_source: dict[str, str] = {}
    for r in xr.itertuples():
        s, w = tokens_from_crossref(r.vehicle_model)
        rb, rq, rc = band_from_registry_model(getattr(r, "registry_model", ""))
        for pn in {norm(r.genuine_pn), norm(r.bvp_pn)}:
            xr_series[pn] = sorted(set(xr_series[pn]) | set(s))
            xr_wild[pn] = sorted(set(xr_wild[pn]) | set(w))
            if rb:
                xr_regband[pn].add(rb)
                xr_regquote[pn][rb] = rq
                xr_reg_source[pn] = ("the cross-reference file's registry_model column for this "
                                     "part number — 01_data/00_derived/genuine_bvp_crossref.csv")

    # the universe: every part number the family table calls an N-series truck, plus every part
    # number the EPC itself families as TRUCKS N or TRUCKS Q (so nothing is silently left out).
    epc_n_pns = set()
    for r in b1.itertuples():
        if "TRUCKS N" in str(r.families) or "TRUCKS Q" in str(r.families):
            epc_n_pns.add(r.pn)
    for r in dec2:
        if any(f in ("TRUCKS N", "TRUCKS Q") for f in (r.get("families") or [])):
            epc_n_pns.add(norm(r["pn"]))
    fam_n_pns = {p for p, f in fam_of.items() if f == "n_series_truck"}
    universe = sorted(fam_n_pns | epc_n_pns)
    print(f"N-series universe: {len(universe)} part numbers "
          f"({len(fam_n_pns)} in the N-series family, {len(epc_n_pns)} the EPC families as TRUCKS N/Q)")

    sf, billing_source = read_billing()
    # the cache names the market column `db`; the published book names it `distributor_code`
    sf = sf.rename(columns={"db": "distributor_code"})
    mm = pd.read_csv(DER / "pms_capture_by_db_year.csv")
    book = sorted(mm.loc[mm.line_type == "total", "distributor_code"].unique())
    sf = sf[sf.distributor_code.isin(book)].copy()
    sf["pn"] = sf.pn.astype(str)
    billed_years = sorted(int(y) for y in sf.y.dropna().unique())
    billed_months = sorted({(int(y), int(m)) for y, m in zip(sf.y.dropna(), sf.m.dropna())})
    billing_through = (f"{billed_months[-1][0]}-{billed_months[-1][1]:02d}"
                       if billed_months else "")
    print(f"billing window: {billed_years[0] if billed_years else '-'} to {billing_through} "
          f"({len(billed_months)} months, {len(billed_years)} calendar years)")

    by_pn_year = (sf.groupby(["pn", "y"], dropna=True)
                  .agg(eur=("net_sales_value", "sum"), units=("billed_qty", "sum"))
                  .reset_index())
    pn_all = sf.groupby("pn").agg(eur=("net_sales_value", "sum"),
                                  units=("billed_qty", "sum")).to_dict("index")
    pn_year: dict[str, dict[int, tuple[float, float]]] = defaultdict(dict)
    for r in by_pn_year.itertuples():
        pn_year[r.pn][int(r.y)] = (float(r.eur), float(r.units))
    pn_months = sf.groupby("pn").m.nunique().to_dict()

    band_rows = []
    for pn in universe:
        s_epc = epc_series.get(pn, [])
        s_xr = xr_series.get(pn, [])
        all_tokens = sorted(set(s_epc) | set(s_xr))
        b_epc, u_epc = bands_for(s_epc)
        b_xr, u_xr = bands_for(s_xr)
        reg = sorted(xr_regband.get(pn, set()))
        # a band only counts if a *named* series carries it; an unresolved series can widen the
        # shared set but can never be the sole reason a band is claimed
        named, _un = bands_for([t for t in all_tokens if tbl(t)[0] != UNRESOLVED])
        believed = sorted(set(b_epc) | set(b_xr) | set(reg))
        widened = bool(_un) and bool(named)
        bands = sorted(set(named) | set(reg))
        unresolved_named = sorted(set([t for t in all_tokens if tbl(t)[0] == UNRESOLVED]))
        if not all_tokens:
            status, band_str = "no_series_found", ""
            reason = ("The EPC found no vehicle for this part number and the cross-reference names "
                      "no model code, so no series can be read.")
        elif widened:
            status = "shared_across_bands"
            band_str = "|".join(believed)
            reason = ("Fits more than one band, from the series named on this part number: "
                      + ", ".join(all_tokens) + ". The band set is widened rather than decided by "
                      "the series the sources do not resolve (" + ", ".join(unresolved_named)
                      + "), because a code that sits at more than one rung of the ladder cannot "
                      "narrow a part to one. Pooled — never apportioned.")
        elif len(bands) == 1:
            status, band_str = "single_band", bands[0]
            reason = ("One band from the series named on this part number: "
                      + ", ".join(all_tokens) + ".")
            if reg:
                reason += (" The cross-reference's registry model tag '" + "/".join(reg)
                           + "' agrees.")
            elif not named:
                reason = ("One band from the cross-reference's registry model tag for this part "
                          "number (" + "/".join(reg) + ").")
        elif len(bands) > 1:
            status, band_str = "shared_across_bands", "|".join(bands)
            reason = ("Fits more than one band, from the series named on this part number: "
                      + ", ".join(all_tokens) + ". Pooled — never apportioned.")
            if reg:
                reason += " The registry model tag on the cross-reference row also names " \
                          + "/".join(reg) + "."
        else:
            status, band_str = "series_unresolved", ""
            reason = ("Every series named on this part number is one the sources do not resolve: "
                      + ", ".join(unresolved_named or all_tokens) + ". Left blank rather than guessed.")
        info = pn_all.get(pn, {"eur": 0.0, "units": 0.0})
        row = {
            "pn": pn,
            "in_n_series_family": "yes" if pn in fam_n_pns else "no",
            "family": fam_of.get(pn, "") or "",
            "family_resolution": res_of.get(pn, "") or "",
            "pms_category": cat_of.get(pn, "") or "",
            "series_from_epc": "; ".join(s_epc),
            "series_from_crossref": "; ".join(s_xr),
            "registry_model_band": "|".join(reg),
            "series_all": "; ".join(all_tokens),
            "series_unresolved": "; ".join(unresolved_named),
            "in_epc_decode": "yes" if pn in epc_series and epc_series[pn] else "no",
            "tonnage_band": band_str,
            "band_count": len(bands),
            "band_status": status,
            "band_reason": reason,
            "eur_all_years": round(float(info["eur"]), 2),
            "units_all_years": round(float(info["units"]), 1),
            "months_with_billing": int(pn_months.get(pn, 0)),
        }
        for y in billed_years:
            e, u = pn_year[pn].get(y, (0.0, 0.0))
            row[f"eur_{y}"] = round(e, 2)
            row[f"units_{y}"] = round(u, 1)
        band_rows.append(row)
    banded = pd.DataFrame(band_rows).sort_values(
        ["band_status", "eur_all_years"], ascending=[True, False])
    banded.to_csv(OUT_BANDED, index=False)

    fam_rows = banded[banded.in_n_series_family == "yes"]
    print(f"banded file   : {len(banded)} part numbers -> {OUT_BANDED.name}")
    for st, g in banded.groupby("band_status"):
        print(f"  {st:22s} {len(g):4d} PNs   EUR {g.eur_all_years.sum():14,.0f}")
    print(f"  of which in the N-series family: {len(fam_rows)}  "
          f"EUR {fam_rows.eur_all_years.sum():,.0f}")
    print(f"  EPC-N but pooled into another family and therefore not in a band: "
          f"{int((banded.in_n_series_family == 'no').sum())}")
    print(f"  banded from the registry model tag alone: "
          f"{int((banded.registry_model_band.fillna('') != '').sum())} part numbers carry one")

    # ── 3. the evolution: market x band x period x clock, the previous period beside it
    #
    # Membership. Three views of the same euro, and only one of them adds up to the N-series total:
    #   single_band_only    fits this band and nothing else — the only band euro that is exclusive
    #   also_fits_band      fits this band AND at least one other — reported per band, so the three
    #                       band views overlap and must never be summed together
    #   pooled_all_bands    the whole shared set once, so the overlap is visible rather than hidden
    #   series_unresolved   a series the sources do not resolve
    #   sums_to_n_series_total is written per row so a reader (or a script) cannot sum the wrong one.
    fam_pn = dict(zip(bands_tbl.pn, bands_tbl.family))
    band_sets: dict[str, set[str]] = {}
    for r in banded.itertuples():
        if r.in_n_series_family != "yes":
            continue
        band_sets[r.pn] = set(str(r.tonnage_band).split("|")) if r.tonnage_band else set()

    member_rows: list[tuple[str, str, bool]] = []
    for pn, bs in band_sets.items():
        if len(bs) == 1:
            member_rows.append((pn, next(iter(bs)), True))          # single_band_only
        elif len(bs) > 1:
            for b in sorted(bs):
                member_rows.append((pn, b, False))                  # also_fits_band
            member_rows.append((pn, GROUP_SHARED, True))            # pooled_all_bands — once
        else:
            member_rows.append((pn, GROUP_UNRESOLVED, True))        # series_unresolved
    mem = pd.DataFrame(member_rows, columns=["pn", "band", "sums"])
    mem["membership"] = mem.apply(
        lambda r: ("single_band_only" if r["sums"] and r["band"] in BANDS
                   else ("pooled_all_bands" if r["band"] == GROUP_SHARED
                         else ("series_unresolved" if r["band"] == GROUP_UNRESOLVED
                               else "also_fits_band"))), axis=1)

    ns = sf[sf.pn.map(lambda p: fam_pn.get(p) == "n_series_truck")].copy()
    banded_pns = set(band_sets)
    # a part number can carry a band and never have been billed in these 18 markets; what must not
    # happen is a billed N-series part number with no band, because then its euro would be absent
    missing = sorted(set(ns.pn) - banded_pns)
    if missing:
        raise SystemExit(f"BUILD FAIL: billed N-series part numbers with no band: {missing[:8]}")
    never_billed = sorted(banded_pns - set(ns.pn))
    print(f"  banded but never billed in these 18 markets: {len(never_billed)} part numbers "
          f"(EUR 0 each, kept in the banded file rather than dropped)")
    ns_total = float(ns.net_sales_value.sum())
    fam_total = float(banded.loc[banded.in_n_series_family == "yes", "eur_all_years"].sum())
    if abs(ns_total - fam_total) > 1.0:
        raise SystemExit(f"BUILD FAIL: the banded table and the tagged billing disagree on the "
                         f"N-series total: EUR {ns_total:,.2f} against EUR {fam_total:,.2f}")

    lane = dict(zip(pd.read_csv(DER / "pms_tonnage_model.csv").distributor_code,
                    pd.read_csv(DER / "pms_tonnage_model.csv").lane))
    frames = []
    for clock, col in (("CY", "y"), ("FY", "fy")):
        sub = ns.dropna(subset=[col]).merge(mem, on="pn", how="inner")
        g = (sub.groupby(["distributor_code", col, "band", "membership", "sums"], dropna=False)
             .agg(billed_eur=("net_sales_value", "sum"), units=("billed_qty", "sum"),
                  distinct_pns=("pn", "nunique"), months=("m", "nunique"))
             .reset_index().rename(columns={col: "period", "months": "months_in_period"}))
        g["clock"] = clock
        frames.append(g)
    evo = pd.concat(frames, ignore_index=True)
    evo["period"] = evo.period.astype(int)
    evo["period_is_complete"] = evo.months_in_period >= 12
    evo["lane"] = evo.distributor_code.map(lane)
    evo["band_label"] = evo.band.map(GROUP_LABEL)
    evo["family_scope"] = "n_series_truck"
    evo["period_label"] = evo.apply(
        lambda r: (f"CY{int(r.period)} = January to December {int(r.period)}" if r.clock == "CY"
                   else f"FY{int(r.period)} = April {int(r.period) - 1} to March {int(r.period)}"),
        axis=1)

    # the previous period beside it, and a delta only where both periods are full twelve-month spans
    out = []
    for (clock, db, band, membership), g in evo.groupby(
            ["clock", "distributor_code", "band", "membership"], dropna=False):
        g = g.sort_values("period").reset_index(drop=True)
        for i, r in enumerate(g.itertuples()):
            p = g.iloc[i - 1] if i else None
            comparable = bool(p is not None and r.period_is_complete
                              and bool(p["period_is_complete"]) and int(p["months_in_period"]) >= 12)
            de = du = dpe = dpu = None
            if comparable:
                pe, pu = float(p["billed_eur"]), float(p["units"])
                de, du = r.billed_eur - pe, r.units - pu
                dpe = (r.billed_eur / pe - 1) if pe else None
                dpu = (r.units / pu - 1) if pu else None
            out.append({
                "family_scope": "n_series_truck", "clock": r.clock, "period": int(r.period),
                "period_label": r.period_label, "months_in_period": int(r.months_in_period),
                "period_is_complete": bool(r.period_is_complete),
                "distributor_code": r.distributor_code, "lane": r.lane,
                "tonnage_band": r.band, "band_label": r.band_label,
                "membership": r.membership,
                "sums_to_n_series_total": "yes" if bool(r.sums) else "no",
                "billed_eur": round(float(r.billed_eur), 2),
                "units": round(float(r.units), 1),
                "distinct_pns": int(r.distinct_pns),
                "prev_period": int(p["period"]) if p is not None else None,
                "prev_period_label": p["period_label"] if p is not None else None,
                "prev_billed_eur": round(float(p["billed_eur"]), 2) if p is not None else None,
                "prev_units": round(float(p["units"]), 1) if p is not None else None,
                "delta_eur": round(de, 2) if de is not None else None,
                "delta_pct": round(dpe, 4) if dpe is not None else None,
                "delta_units": round(du, 1) if du is not None else None,
                "delta_units_pct": round(dpu, 4) if dpu is not None else None,
                "comparable_to_previous": comparable,
            })
    ev = pd.DataFrame(out).sort_values(
        ["clock", "tonnage_band", "membership", "distributor_code", "period"])
    ev.to_csv(OUT_EVO, index=False)
    print(f"evolution     : {len(ev):,} rows -> {OUT_EVO.name}")

    # the tie-out the file itself must satisfy: the mutually exclusive rows are the N-series total
    excl = ev[ev.sums_to_n_series_total == "yes"]
    excl_total = float(excl[excl.clock == "CY"].groupby("period").billed_eur.sum().sum())
    all_total = float(ns.net_sales_value.sum())
    if abs(excl_total - all_total) > 1.0:
        raise SystemExit(f"BUILD FAIL: the mutually exclusive evolution rows sum to "
                         f"EUR {excl_total:,.2f} against the tagged N-series billing "
                         f"EUR {all_total:,.2f}")

    # per band: how much of the band's own billing is single-band, and how much is shared parts
    # that also fit this band. That split is what decides whether a band can carry a trend.
    pns_in_band = defaultdict(list)
    for r in banded.itertuples():
        if r.in_n_series_family != "yes":
            continue
        if r.band_status == "single_band":
            pns_in_band[f"single:{r.tonnage_band}"].append(r.pn)
        elif r.band_status == "shared_across_bands":
            for b in str(r.tonnage_band).split("|"):
                pns_in_band[f"also_fits:{b}"].append(r.pn)
    eur_of = dict(zip(banded.pn, banded.eur_all_years.astype(float)))

    def sum_pns(key: str) -> float:
        return round(sum(eur_of.get(p, 0.0) for p in pns_in_band.get(key, [])), 2)

    band_split = {}
    for b in BANDS:
        band_split[b] = {
            "label": GROUP_LABEL[b],
            "single_band_pns": len(pns_in_band.get(f"single:{b}", [])),
            "single_band_eur": sum_pns(f"single:{b}"),
            "shared_pns_that_also_fit": len(pns_in_band.get(f"also_fits:{b}", [])),
            "shared_eur_that_also_fits": sum_pns(f"also_fits:{b}"),
        }
    shared_eur = float(banded.loc[banded.band_status == "shared_across_bands",
                                  "eur_all_years"].sum())
    unres_eur = float(banded.loc[banded.band_status == "series_unresolved", "eur_all_years"].sum())

    meta = {
        # the decode date, deliberately kept so nothing downstream breaks; see the definition above
        "snapshot": DECODE_SNAPSHOT,
        "snapshot_field_meaning": (
            "decode_snapshot -- the date the EPC decode and the series-to-tonnage mapping behind "
            "this file were taken. It is NOT the billing window; read `billing_through` for that."),
        "decode_snapshot": DECODE_SNAPSHOT,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "03_analytics/Isuzu/prism/scripts/build_nseries_tonnage_bands.py",
        "outputs": {"series_to_tonnage": str(OUT_SERIES), "banded": str(OUT_BANDED),
                    "evolution": str(OUT_EVO)},
        "bands": BANDS,
        "groups": GROUP_ORDER,
        "billing_source": billing_source,
        "billing_through": billing_through,
        "billing_window": (
            f"{billed_years[0] if billed_years else ''}-01 to {billing_through}"
            if billing_through else ""),
        "book_markets": book,
        "billed_years": billed_years,
        "clock_definition": {
            "CY": "calendar year, January to December",
            "FY": "ISZE year, April to March, labelled by the closing year "
                  "(FY2026 = April 2025 to March 2026)",
        },
        "universe": {
            "n_series_family": len(fam_n_pns),
            "epc_families_as_trucks_n_or_q": len(epc_n_pns),
            "banded_rows": int(len(banded)),
            "in_band_scope": int(len(fam_rows)),
            "epc_n_but_pooled_into_another_family": int((banded.in_n_series_family == "no").sum()),
        },
        "by_status": {st: {"part_numbers": int(len(g)),
                           "eur_all_years": round(float(g.eur_all_years.sum()), 2)}
                      for st, g in banded.groupby("band_status")},
        "band_split_single_versus_shared": band_split,
        "n_series_total_eur_all_years": round(ns_total, 2),
        "shared_across_bands_eur": round(shared_eur, 2),
        "series_unresolved_eur": round(unres_eur, 2),
        "tie_out": {
            # Kept under its old name so nothing that reads it breaks. It is the WHOLE in-family
            # total, i.e. all four band_status buckets below, not three of them: read literally,
            # "bands + shared + unresolved" leaves out `no_series_found` (corrected 2026-09-23).
            "bands_plus_shared_plus_unresolved_eur": round(
                float(banded.loc[banded.in_n_series_family == "yes", "eur_all_years"].sum()), 2),
            "components_in_family": {
                st: {"part_numbers": int(len(g)), "eur_all_years": round(float(g.eur_all_years.sum()), 2)}
                for st, g in banded[banded.in_n_series_family == "yes"].groupby("band_status")},
            "components_note": (
                "single_band + shared_across_bands + series_unresolved + no_series_found = the "
                "in-family total. The evolution file files the last two together as one "
                "`series_unresolved` membership, so its unresolved euro equals the band file's "
                "series_unresolved plus no_series_found."),
            "tagged_n_series_billing_eur": round(ns_total, 2),
            "delta_eur": round(abs(ns_total - fam_total), 2),
        },
        "rules": [
            "A series is matched as a whole token, never as a substring. Wildcard tokens (N*, N*R) "
            "are recorded and never converted into a band.",
            "A part number that fits more than one band is pooled as shared_across_bands and is "
            "never apportioned across the bands it fits.",
            "A series neither authorised source names leaves the band blank, with the reason "
            "written in band_reason.",
            "A part number outside the N-series family (EPC 'TRUCKS N' but also a heavy or light "
            "vehicle part) is not put in a band: it belongs to the pooled family row of the parent "
            "page, and banding it here would double-count it.",
            "The three bands plus the pool plus the unresolved group sum to the tagged N-series "
            "billing, asserted at build time. 'The unresolved group' means both band_status "
            "buckets with no band - series_unresolved (a series is named but none resolves) and "
            "no_series_found (no series named at all); the evolution file carries the two as one "
            "`series_unresolved` membership. Without no_series_found the sum falls short.",
        ],
        "sources": [DUNCAN, RENE24, RENE14, VINREG,
                    "the cross-reference file's registry_model column — "
                    "01_data/00_derived/genuine_bvp_crossref.csv"],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print()
    print("band split, single-band versus shared (all years, 18 markets):")
    for b, v in band_split.items():
        print(f"  {v['label']:34s} single {v['single_band_pns']:3d} PNs "
              f"EUR {v['single_band_eur']:12,.0f} | shared parts that also fit "
              f"{v['shared_pns_that_also_fit']:3d} PNs EUR {v['shared_eur_that_also_fits']:12,.0f}")
    print(f"  shared across bands: EUR {shared_eur:,.0f}   unresolved series: EUR {unres_eur:,.0f}")
    print(f"  N-series total EUR {ns_total:,.0f} (tie-out delta EUR {abs(ns_total - fam_total):,.2f})")
    print(f"written -> {OUT_EVO}")
    print(f"written -> {OUT_META}")
    return 0


def parse_codes_from_edition(text: str) -> list[str]:
    """Leading series block(s) of an EPC edition string, e.g. '2018 NNR/NPR-RHD EURO6 EUROPE'."""
    t = str(text or "").strip().upper()
    for _ in range(6):
        before = t
        t = re.sub(r"^\(?\d{2,4}\.\d\s*-?\s*", "", t)
        t = re.sub(r"^\(?\d{2,4}\s*\)?\s*-+\s*", "", t)
        t = re.sub(r"^\d{2,4}\s+(?=[A-Z])", "", t)
        t = re.sub(r"^\(?\d{2,4}\)?\s*", "", t)
        t = re.sub(r"^\d{2,3}(?=[A-Z]{2})", "", t)
        if t == before:
            break
    blk = t.split("(", 1)[0].split()[0] if t.split() else ""
    out = []
    for part in blk.replace("-", "/").split("/"):
        part = part.strip()
        if part and TOKEN_RE.match(part):
            out.append(part)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
