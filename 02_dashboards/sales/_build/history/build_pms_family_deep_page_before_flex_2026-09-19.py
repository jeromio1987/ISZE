#!/usr/bin/env python3
"""
Build the shared deep-dive page: service demand by vehicle family, with real click-through.

The page it replaces placed only 46.6% of 2025 service-part euro in a vehicle family and showed
heavy truck as a EUR 21,844 sliver, because a part number that the cross-reference already named a
vehicle for was excluded from the EPC decode and then excluded from the family view. Every number
here comes from the single two-source banding table `vehicle_family_bands.csv`, so a part number
cannot fall between two steps again.

What the page has to do (Jerome, verbatim)
------------------------------------------
"a dropdown above where I select a customer or multiple. I want an option where I can select one of
the 4 vehicle types and I want to navigate through a deeper level by clicking on bars where we
compare always with the previous year (FY / CY) in absolute numbers sold and percentage"

So: a multi-select customer control, a vehicle-type control including a pooled option, a CY/FY clock
whose labels always spell out their months, and click-through from service family to part numbers
that always shows this period against the same period a year earlier in euro, in units, and as a
percentage, side by side.

The pooled bar opens rather than being apportioned. Clicking it lists the part numbers inside it and
which families each one fits, so a pooled EUR 1.1M is a set of part numbers a reader can inspect
rather than a black box.

Chart form follows the question (skill `isze-best-chart`): the family trend is a funnel against the
year before with euro and units at every bar; breadth inside a family is a ranked bar; the mix is a
donut at most four segments; part numbers are a table. Every chart with more than one series carries
a written key, and every keyed number carries a hover explaining its formula and what it excludes.

Reads : 01_data/00_derived/pms_capture_by_family.csv
        01_data/00_derived/pms_capture_by_family.meta.json
        01_data/00_derived/pms_family_evolution_both_clocks.csv
        01_data/00_derived/vehicle_family_bands.csv
        01_data/00_derived/sales_fact.parquet
        01_data/00_derived/distributor_dimension.csv
        01_data/00_derived/pms_tonnage_model.csv
       03_analytics/Isuzu/prism/data/uio_by_model_bucket.csv
Writes: 02_dashboards/sales/ISZE_PMS_Family_Evolution_Deep.html
        02_dashboards/sales/OPEN_ISZE_PMS_Family_Evolution_Deep.cmd

Run: python 02_dashboards/sales/_build/build_pms_family_deep_page.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PDATA = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
OUT_DIR = ROOT / "02_dashboards" / "sales"
BUILD_DIR = OUT_DIR / "_build"
OUT_HTML = OUT_DIR / "ISZE_PMS_Family_Evolution_Deep.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_PMS_Family_Evolution_Deep.cmd"
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

SNAPSHOT = "2026-09-19"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731


def die(msg: str) -> None:
    print(f"BUILD FAIL: {msg}")
    sys.exit(1)


# ── the shipped page, as the record of where we were before this rebuild ─────────────────────────
SHIPPED = OUT_DIR / "ISZE_PMS_Family_Evolution.html"
# The record is frozen, not re-read. The earlier family page has since been corrected, so reading
# it again would overwrite the very numbers this comparison exists to show, and the panel would
# quietly become a comparison of a page against itself. The file below was written on 19 September
# from six QA case files taken while that page was still as shipped.
BEFORE_FROZEN = BUILD_DIR / "_before_snapshot_2026-09-19.json"


def read_before() -> dict:
    """The numbers the earlier family page carried when it was handed over.

    Read from the frozen record, so the comparison cannot drift when the earlier page is fixed.
    """
    if not BEFORE_FROZEN.is_file():
        return {"available": False, "why": f"{BEFORE_FROZEN.name} is not on disk"}
    return json.loads(BEFORE_FROZEN.read_text(encoding="utf-8"))


# ── the four vehicle types the reader selects between ────────────────────────────────────────────
FAMILIES = [
    {"key": "n_series_truck", "label": "N-series truck",
     "note": "NLR through NQR — the light and medium truck range",
     "color": "#15233c"},
    {"key": "heavy_truck", "label": "Heavy truck (F-series and C&E)",
     "note": "Forward F&G and the C&E range",
     "color": "#c0552d"},
    {"key": "light_vehicle", "label": "Light vehicle (D-Max)",
     "note": "pickup and SUV",
     "color": "#2f6b45"},
    {"key": "shared_across_families", "label": "Parts used across more than one family",
     "note": "pooled, never apportioned — click to open the part numbers inside it",
     "color": "#7a8ba6"},
    {"key": "no_vehicle_reference", "label": "No vehicle reference found",
     "note": "no source names a vehicle for these part numbers",
     "color": "#b9ae9d"},
]
FAM_KEYS = [f["key"] for f in FAMILIES]
NAMED_KEYS = ["n_series_truck", "heavy_truck", "light_vehicle"]
FAM_INFO = {f["key"]: f for f in FAMILIES}

CLOCK_DEF = {
    "CY": {"label": "Calendar year — January to December",
           "short": "CY",
           "period_label": lambda p: f"CY{p} = January to December {p}"},
    "FY": {"label": "ISZE year — April to March, named by the closing year",
           "short": "FY",
           "period_label": lambda p: f"FY{p} = April {int(p) - 1} – March {p}"},
}

# ── the tonnage level inside the N-series ────────────────────────────────────────────────────────
# The vehicle type answers "which family"; inside N-series the sources also name the series, and the
# series carries a weight (see 01_data/00_derived/series_to_tonnage.csv). So the N-series gets a
# further level: 3.5 t, 5.5 t, 7.5 t — plus the parts that fit more than one of those, and the parts
# whose series the sources do not resolve.
#
# Every zone below carries `membership`, and that is the whole point:
#   single_band_only   the part number fits this band and nothing else. This euro is EXCLUSIVE and
#                      three of these rows add up to what the bands alone account for.
#   also_fits_band     the part number fits this band AND at least one other. Reported inside each
#                      band it fits, so the band rows OVERLAP. They are marked and are never summed.
#   pooled_all_bands   the whole shared set once, so the overlap is visible instead of hidden.
#   series_unresolved  a series the two authoritative sources do not state a weight for.
ZONES = [
    {"zid": "n35_single", "band": "3.5t_N35", "membership": "single_band_only",
     "label": "3.5 t — fits 3.5 t only", "short": "3.5 t only",
     "note": "Part numbers whose series is 3.5 t and nothing else", "color": "#15233c"},
    {"zid": "n35_also", "band": "3.5t_N35", "membership": "also_fits_band",
     "label": "3.5 t — also fits another band", "short": "3.5 t, shared",
     "note": "Fits 3.5 t and at least one heavier band. Overlaps the 5.5 t and 7.5 t rows.",
     "color": "#7a8ba6"},
    {"zid": "n55_single", "band": "5.5t_N50_N55", "membership": "single_band_only",
     "label": "5.5 t — fits 5.5 t only", "short": "5.5 t only",
     "note": "Part numbers whose series is 5.5 t and nothing else", "color": "#2f6b45"},
    {"zid": "n55_also", "band": "5.5t_N50_N55", "membership": "also_fits_band",
     "label": "5.5 t — also fits another band", "short": "5.5 t, shared",
     "note": "Fits 5.5 t and at least one other band. Overlaps the other band rows.",
     "color": "#7a8ba6"},
    {"zid": "n75_single", "band": "7.5t_N50_N62_N75", "membership": "single_band_only",
     "label": "7.5 t — fits 7.5 t only", "short": "7.5 t only",
     "note": "Part numbers whose series is 7.5 t and nothing else", "color": "#c0552d"},
    {"zid": "n75_also", "band": "7.5t_N50_N62_N75", "membership": "also_fits_band",
     "label": "7.5 t — also fits another band", "short": "7.5 t, shared",
     "note": "Fits 7.5 t and at least one lighter band. Overlaps the other band rows.",
     "color": "#7a8ba6"},
    {"zid": "n_shared_bands", "band": "shared_across_bands", "membership": "pooled_all_bands",
     "label": "Shared across bands — counted once", "short": "shared, once",
     "note": "Every part number that fits more than one band, counted here exactly once",
     "color": "#8a6b2f"},
    {"zid": "n_series_unresolved", "band": "unresolved_series", "membership": "series_unresolved",
     "label": "Series the sources do not state a weight for", "short": "not stated",
     "note": "The sources do not name a weight for these series", "color": "#b9ae9d"},
    {"zid": "heavy_truck", "band": None, "membership": "whole_family",
     "label": "Heavy truck (F-series and C&E)", "short": "Heavy truck",
     "note": "Forward F&G and the C&E range", "color": "#6b3f2a"},
    {"zid": "light_vehicle", "band": None, "membership": "whole_family",
     "label": "Light vehicle (D-Max)", "short": "Light vehicle",
     "note": "pickup and SUV", "color": "#2f6b45"},
    {"zid": "shared_across_families", "band": None, "membership": "pooled_all_families",
     "label": "Parts used across more than one vehicle type", "short": "shared types",
     "note": "Pooled, never apportioned — click to open the part numbers inside it",
     "color": "#7a8ba6"},
    {"zid": "no_vehicle_reference", "band": None, "membership": "no_vehicle",
     "label": "No vehicle reference found", "short": "no vehicle",
     "note": "no source names a vehicle for these part numbers", "color": "#b9ae9d"},
]
ZONE_BY_ID = {z["zid"]: z for z in ZONES}
ZONE_IDS = [z["zid"] for z in ZONES]
BAND_ORDER = ["3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"]
BAND_LABEL = {"3.5t_N35": "3.5 t GVW (N35 Grafter)", "5.5t_N50_N55": "5.5 t GVW (N50 / N55)",
              "7.5t_N50_N62_N75": "7.5 t class (N50 / N62 / N75)"}
BAND_COLOR = {"3.5t_N35": "#15233c", "5.5t_N50_N55": "#2f6b45", "7.5t_N50_N62_N75": "#c0552d"}


def main() -> int:
    bands = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str).fillna("")
    bands["pnk"] = bands.pn.map(norm)
    nbanded = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str,
                          low_memory=False).fillna("")
    nbanded["pnk"] = nbanded.pn.map(norm)
    nmeta = json.loads((DER / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))
    ns_bands = pd.read_csv(DER / "series_to_tonnage.csv", dtype=str).fillna("")
    BEFORE = read_before()
    meta = json.loads((DER / "pms_capture_by_family.meta.json").read_text(encoding="utf-8"))
    core = pd.read_csv(DER / "pms_capture_by_family.csv")
    evo = pd.read_csv(DER / "pms_family_evolution_both_clocks.csv")
    tonnage = pd.read_csv(DER / "pms_tonnage_model.csv")
    buckets = pd.read_csv(PDATA / "uio_by_model_bucket.csv")

    MARKETS = sorted(core.distributor_code.unique())
    mk_idx = {m: i for i, m in enumerate(MARKETS)}

    # ── the part-number index the deepest level reads
    bands["_eur"] = pd.to_numeric(bands.eur_all_markets, errors="coerce").fillna(0.0)
    pns = bands.sort_values("_eur", ascending=False).reset_index(drop=True)
    pn_idx = {p: i for i, p in enumerate(pns.pnk)}
    pn_rows = [{
        "pn": r.pnk,
        "cat": r.pms_category,
        "fam": r.family if r.resolution == "single_family" else
               ("shared_across_families" if r.resolution == "shared_across_families"
                else "no_vehicle_reference"),
        "fits": [x for x in str(r.families_in_union).split("|") if x],
        "conf": r.confidence,
        "model": r.vehicle_model,
        "src": r.source_note,
    } for r in pns.itertuples()]
    pn_fam = {r["pn"]: r["fam"] for r in pn_rows}
    pn_cat = {r["pn"]: r["cat"] for r in pn_rows}

    # The tonnage level inside the N-series. Defined here because both the part-number index below
    # and the billing grain further down are keyed to it.
    nz = dict(zip(nbanded.pnk, nbanded.tonnage_band))
    nz_status = dict(zip(nbanded.pnk, nbanded.band_status))
    nz_series = dict(zip(nbanded.pnk, nbanded.series_all))
    nz_reg = dict(zip(nbanded.pnk, nbanded.registry_model_band))
    nz_reason = dict(zip(nbanded.pnk, nbanded.band_reason))
    FAMILY_ZONE = {"heavy_truck": "heavy_truck", "light_vehicle": "light_vehicle",
                   "shared_across_families": "shared_across_families",
                   "no_vehicle_reference": "no_vehicle_reference"}
    ZONE_SINGLE = {"3.5t_N35": "n35_single", "5.5t_N50_N55": "n55_single",
                   "7.5t_N50_N62_N75": "n75_single"}
    ZONE_ALSO = {"3.5t_N35": "n35_also", "5.5t_N50_N55": "n55_also",
                 "7.5t_N50_N62_N75": "n75_also"}

    def zones_for(pn: str) -> list[str]:
        """Every tonnage zone a part number belongs to. Non-N-series parts get their family zone."""
        fam = pn_fam.get(pn)
        if fam != "n_series_truck":
            return [FAMILY_ZONE.get(fam, "no_vehicle_reference")]
        bs = [b for b in str(nz.get(pn, "")).split("|") if b]
        if len(bs) == 1 and bs[0] in BAND_ORDER:
            return [ZONE_SINGLE[bs[0]]]
        if len(bs) > 1:
            return [ZONE_ALSO[b] for b in bs if b in ZONE_ALSO] + ["n_shared_bands"]
        return ["n_series_unresolved"]

    # the exclusive zone of a part number: exactly one, and the exclusive zones cover the book
    EXCL_IDS = [z["zid"] for z in ZONES if z["membership"] != "also_fits_band"]
    pn_excl_zone = {}
    for pn in pn_idx:
        ex = [z for z in zones_for(pn) if ZONE_BY_ID[z]["membership"] != "also_fits_band"]
        pn_excl_zone[pn] = ex[0] if ex else "n_shared_bands"
    # every band a part number fits, one row per (part number, zone), so a band can open onto its
    # own part numbers and the overlapping lines can be shown per band
    ze = pd.DataFrame([(pn, z) for pn in pn_idx for z in zones_for(pn)],
                      columns=["pn", "zone"])

    for i, r in enumerate(pn_rows):
        r["zfits"] = [z["zid"] for z in ZONES if z["zid"] in zones_for(r["pn"])]
        r["zexcl"] = pn_excl_zone[r["pn"]]
        r["zstatus"] = nz_status.get(r["pn"], "")
        r["zseries"] = nz_series.get(r["pn"], "")
        r["zreg"] = nz_reg.get(r["pn"], "")
        r["zreason"] = nz_reason.get(r["pn"], "")

    # ── billing at the grain the client drills to: customer x category x family x period.
    # It is read through the project's OWN tagging path (`tag_pms_sales` plus the published
    # exclusions) rather than by joining part numbers by hand. That distinction is what makes the
    # page tie to the published service-part book: the registry is consulted before the catalogue,
    # and credit notes and part numbers the dimension marks as not capture-eligible (filter
    # assemblies, kits) come out. A hand-rolled join silently includes them and the euro drifts.
    cache = BUILD_DIR / "_deep_billing_cache.parquet"
    if cache.is_file() and "--refresh" not in sys.argv:
        sf = pd.read_parquet(cache)
    else:
        sys.path.insert(0, str(ROOT / "03_analytics" / "Isuzu" / "prism"))
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
        sf = sf[["pn", "db", "y", "m", "fy", "net_sales_value", "billed_qty"]]
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        sf.to_parquet(cache, index=False)

    sf = sf[sf.db.isin(mk_idx) & sf.pn.isin(pn_idx)].copy()
    sf["cat"] = sf.pn.map(pn_cat)
    sf["fam"] = sf.pn.map(pn_fam)

    cat_list = (core.dropna(subset=["pms_category"])
                .drop_duplicates("pms_category")
                .assign(_l=lambda t: t.pms_category_label)
                .sort_values("_l")[["pms_category", "_l"]].values.tolist())
    cat_idx = {c: i for i, (c, _) in enumerate(cat_list)}
    fam_idx = {f: i for i, f in enumerate(FAM_KEYS)}
    cats = [{"key": c, "label": l} for c, l in cat_list]

    def emit(clock: str) -> list[list]:
        col = "y" if clock == "CY" else "fy"
        g = sf.dropna(subset=[col]).groupby(
            ["db", col, "cat", "fam"], dropna=False).agg(
            eur=("net_sales_value", "sum"), units=("billed_qty", "sum")).reset_index()
        out = []
        for r in g.itertuples():
            if r.cat not in cat_idx or r.fam not in fam_idx:
                continue
            out.append([mk_idx[r.db], cat_idx[r.cat], fam_idx[r.fam], int(getattr(r, col)),
                        round(float(r.eur), 2), round(float(r.units), 2)])
        return out

    rec = {"CY": emit("CY"), "FY": emit("FY")}

    # ── part-number level billing, same key path, one row per customer x part number x period
    def emit_pn(clock: str) -> list[list]:
        col = "y" if clock == "CY" else "fy"
        g = sf.dropna(subset=[col]).groupby(
            ["db", col, "pn"], dropna=False).agg(
            eur=("net_sales_value", "sum"), units=("billed_qty", "sum")).reset_index()
        out = []
        for r in g.itertuples():
            out.append([pn_idx[r.pn], mk_idx[r.db], int(getattr(r, col)),
                        round(float(r.eur), 2), round(float(r.units), 2)])
        return out

    rec_pn = {"CY": emit_pn("CY"), "FY": emit_pn("FY")}

    sfz = sf.merge(ze, on="pn", how="inner")
    sfz["zi"] = sfz.zone.map({z: i for i, z in enumerate(ZONE_IDS)})

    def emit_z(clock: str):
        col = "y" if clock == "CY" else "fy"
        g = sfz.dropna(subset=[col]).groupby(["db", col, "zi"], dropna=False).agg(
            eur=("net_sales_value", "sum"), units=("billed_qty", "sum")).reset_index()
        return [[mk_idx[r.db], int(r.zi), int(getattr(r, col)), round(float(r.eur), 2),
                 round(float(r.units), 2)] for r in g.itertuples()]

    def emit_zcat(clock: str):
        col = "y" if clock == "CY" else "fy"
        g = sfz.dropna(subset=[col]).groupby(["db", col, "zi", "cat"], dropna=False).agg(
            eur=("net_sales_value", "sum"), units=("billed_qty", "sum")).reset_index()
        out = []
        for r in g.itertuples():
            if r.cat not in cat_idx:
                continue
            out.append([mk_idx[r.db], int(r.zi), cat_idx[r.cat], int(getattr(r, col)),
                        round(float(r.eur), 2), round(float(r.units), 2)])
        return out

    zrc = {"CY": emit_z("CY"), "FY": emit_z("FY")}
    rec_zcat = {"CY": emit_zcat("CY"), "FY": emit_zcat("FY")}

    # the exclusive zones must add up to the whole book, on both clocks and every period
    for clock in ("CY", "FY"):
        col = "y" if clock == "CY" else "fy"
        by_period = (sfz[sfz.zone.isin(EXCL_IDS)].dropna(subset=[col])
                     .groupby(col).net_sales_value.sum())
        book_period = sf.dropna(subset=[col]).groupby(col).net_sales_value.sum()
        bad = [(int(p), round(float(by_period[p]), 2), round(float(book_period.get(p, 0)), 2))
               for p in by_period.index if abs(by_period[p] - book_period.get(p, 0)) > 1.0]
        if bad:
            die(f"the tonnage zones do not add up to the billed book on the {clock} clock: {bad}")
    nz_dupes = ze[ze.zone.isin(EXCL_IDS)].groupby("pn").size()
    if int(nz_dupes.max()) > 1:
        worst = nz_dupes[nz_dupes > 1].sort_values(ascending=False).head(6)
        die("a part number sits in more than one exclusive tonnage zone: "
            + " | ".join(f"{pn} x{n}" for pn, n in worst.items()))
    print(f"tonnage zones : {len(ZONES)} zones ({len(EXCL_IDS)} exclusive, "
          f"{len(ZONES) - len(EXCL_IDS)} overlapping) | zone rows CY "
          f"{len(zrc['CY']):,} / FY {len(zrc['FY']):,}")

    # ── the written evidence for each band, read from the sourced series table
    band_evidence = {}
    for b in BAND_ORDER:
        sub = ns_bands[ns_bands.tonnage_band == b]
        band_evidence[b] = {
            "label": BAND_LABEL[b],
            "series": sorted(sub.series.tolist()),
            "weight_label": sub.weight_label.iloc[0] if len(sub) else "",
            "sources": sorted(set(sub.evidence_source.tolist())),
            "quotes": [{"series": r.series, "confidence": r.confidence,
                        "source": r.evidence_source, "quote": r.evidence_quote}
                       for r in sub.itertuples()],
        }
    unresolved_rows = ns_bands[ns_bands.tonnage_band == "unresolved"]
    band_evidence["unresolved_series"] = {
        "label": "Series the sources do not state a weight for",
        "series": sorted(unresolved_rows.series.tolist()),
        "quotes": [{"series": r.series, "confidence": r.confidence,
                    "source": r.evidence_source, "quote": r.evidence_quote}
                   for r in unresolved_rows.itertuples()],
    }

    # ── the clocks: which periods exist, how many months each holds, which are comparable
    clocks = {}
    for clock in ("CY", "FY"):
        col = "y" if clock == "CY" else "fy"
        sub = sf.dropna(subset=[col])
        months = {int(k): int(v) for k, v in
                  sub.groupby(col).m.nunique().items()}
        periods = sorted(months)
        complete = [p for p in periods if months[p] >= 12]
        clocks[clock] = {
            "label": CLOCK_DEF[clock]["label"],
            "spelled": {str(p): CLOCK_DEF[clock]["period_label"](p) for p in periods},
            "months": {str(p): months[p] for p in periods},
            "periods": periods,
            "complete": complete,
            "latestComplete": complete[-1] if complete else None,
            "note": ("A period holding fewer than twelve months of billing is shown but never "
                     "compared as though it were a full year."),
        }

    # ── the fleet denominator, so no euro is ever shown without the vehicles it sits on
    n35 = dict(zip(buckets.distributor_code, buckets.cv_std_uio))
    fleet = {}
    for r in buckets.itertuples():
        fleet[r.distributor_code] = {
            "n_series": int(round(float(r.cv_std_uio))),
            "heavy": int(round(float(r.f_series_uio))),
            "light": int(round(float(r.lcv_uio))),
            "total": int(round(float(r.cv_std_uio + r.f_series_uio + r.lcv_uio))),
        }

    # the interval schedule each market runs, mapped to which of the two applies. The internal
    # file name for it never reaches the payload or the page.
    lane = {m: ("agreed" if "IML" in str(v) else "internal")
            for m, v in dict(zip(tonnage.distributor_code, tonnage.lane)).items()}

    # The N-series fleet split that exists on disk: the market's measured 3.5 t share of its
    # standard commercial-vehicle parc, and the remainder. Nothing on disk separates the 5.5 t
    # trucks out of that remainder, so the page shows two numbers and never invents a third.
    n35_sh = pd.read_csv(PDATA / "uio_ld_n35_share.csv")
    sh = dict(zip(n35_sh.distributor_code, n35_sh.n35_share))
    nseries_fleet = {}
    for db, uio in n35.items():
        u = float(uio)
        s = float(sh.get(db, 0.0))
        nseries_fleet[db] = [int(round(u * s)), int(round(u * (1 - s)))]

    # ── the category-level headline per family per period, for the opening chart.
    # The evolution file carries the no-vehicle bucket under its older name; map it so the trend and
    # the drill-down agree, and so the five family values sum back to the published service book.
    EVO_NAME = {"unattributed": "no_vehicle_reference"}
    evo_mk = evo[evo.distributor_code.isin(mk_idx)].copy()
    evo_mk["family"] = evo_mk.family.replace(EVO_NAME)
    trend = {}
    for clock in ("CY", "FY"):
        g = evo_mk[(evo_mk.clock == clock) & (evo_mk.scope == "service_parts_only")]
        trend[clock] = {}
        for fam in FAM_KEYS:
            sub = g[g.family == fam]
            trend[clock][fam] = {
                "eur": {str(int(p)): round(float(v)) for p, v in
                        sub.groupby("period").billed_eur.sum().items()},
                "units": {str(int(p)): round(float(v)) for p, v in
                          sub.groupby("period").units.sum().items()},
            }

    # ── per-family size, so a limit or a note never quotes a hardcoded count
    fam_stats = {}
    for fk in FAM_KEYS:
        sub = sf[(sf.fam == fk) & (sf.y == 2025)]
        fam_stats[fk] = {
            "pns": int(pns.pnk.isin(set(sub.pn)).sum()) if len(sub) else 0,
            "eur2025": round(float(sub.net_sales_value.sum()), 2),
            "units2025": round(float(sub.billed_qty.sum()), 1),
            "fleet": int(buckets.loc[buckets.distributor_code.isin(mk_idx),
                                     {"n_series": "cv_std_uio", "heavy_truck": "f_series_uio",
                                      "light_vehicle": "lcv_uio"}.get(fk, "cv_std_uio")].sum())
            if fk in ("n_series_truck", "heavy_truck", "light_vehicle")
            else int(buckets.loc[buckets.distributor_code.isin(mk_idx),
                                 ["cv_std_uio", "f_series_uio", "lcv_uio"]].sum().sum()),
        }

    # ── the two tie-outs the build asserts before it writes anything
    pub = pd.read_csv(DER / "pms_capture_by_db_year.csv")
    pub25 = pub[(pub.line_type == "total") & (pub.year == 2025) & pub.distributor_code.isin(mk_idx)]
    tie_pub = float(pub25.actual_rev_eur.sum())
    y25 = sf[sf.y == 2025]
    tie_mine = float(y25.net_sales_value.sum())
    if abs(tie_pub - tie_mine) > 1.0:
        die(f"2025 service euro does not tie: page data EUR {tie_mine:,.2f} against the published "
            f"service-part book EUR {tie_pub:,.2f}")

    fam25 = y25.groupby("fam").net_sales_value.sum()
    placeable = float(fam25.reindex(NAMED_KEYS).fillna(0).sum())
    old_map = pd.read_csv(DER / "pms_family_part_number_map.csv")
    old_map["pnk"] = old_map.pn.map(norm)
    old_placeable = float(sf[(sf.y == 2025) & sf.pn.isin(
        set(old_map.loc[old_map.resolution == "single_family", "pnk"]))].net_sales_value.sum())

    payload = {
        "snapshot": SNAPSHOT,
        "builtAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "markets": MARKETS,
        "families": FAMILIES,
        "zones": ZONES,
        "zoneIds": ZONE_IDS,
        "bandOrder": BAND_ORDER,
        "bandLabel": BAND_LABEL,
        "bandColor": BAND_COLOR,
        "bandEvidence": band_evidence,
        "famZones": {},
        "familyStats": fam_stats,        "nseriesBands": nmeta["bands"],
        "nseriesByStatus": nmeta["by_status"],
        "nseriesBandSplit": nmeta["band_split_single_versus_shared"],
        "nseriesRules": nmeta["rules"],
        "namedFamilies": NAMED_KEYS,
        "cats": cats,
        "lane": lane,
        "nseries_fleet": nseries_fleet,
        "fleet": fleet,
        "clocks": clocks,
        "trend": trend,
        "rec": rec,
        "recPn": rec_pn,
        "recZ": zrc,
        "recZcat": rec_zcat,
        "pns": pn_rows,
        "totals": {
            "serviceBook2025": round(tie_pub),
            "placeable2025": round(placeable),
            "placeable2025Pct": round(100 * placeable / tie_pub, 2),
            "placeable2025Old": round(old_placeable),
            "placeable2025OldPct": round(100 * old_placeable / tie_pub, 2),
            "ceiling2025": round(float(core[(core.year == 2025)]
                                       .groupby("family").expected_eur.first().sum())),
        },
        "resolution": meta["family_resolution"],
        "tieOut": meta["tie_out"],
        "tieOutEur": meta["tie_out_attributed_euro"],
        "notAttempted": meta["not_attempted"],
        # The "before" figures are not remembered or estimated: they are read from the payload the
        # shipped page embedded in itself, so the comparison is against what Jerome actually had.
        "before": BEFORE,
    }
    body = json.dumps(payload, separators=(",", ":"), allow_nan=False)

    chart_js = CHARTJS.read_text(encoding="utf-8")
    chart_js = re.sub(r"//# sourceMappingURL=\S+", "", chart_js)

    html = build_html(chart_js, body)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_bytes(
        ("@echo off\r\nstart \"\" \"%~dp0ISZE_PMS_Family_Evolution_Deep.html\"\r\n").encode("ascii"))

    # ── guard: the page script must parse before the file is claimed as built
    parts = html.split("<script>", 2)
    if len(parts) < 3:
        die("expected the chart library block and the page script block")
    page_js = parts[2].split("</script>", 1)[0]
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BUILD_DIR / "_deep_syntax_check.js"
    tmp.write_text(page_js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    if r.returncode != 0:
        die("page script does not parse:\n" + (r.stderr or "")[:1500])
    print("syntax guard: page script parses clean")

    print(f"customers {len(MARKETS)} | families {len(FAMILIES)} | categories {len(cats)} "
          f"| part numbers {len(pn_rows)}")
    print(f"records CY {len(rec['CY']):,} / FY {len(rec['FY']):,} | "
          f"part rows CY {len(rec_pn['CY']):,} / FY {len(rec_pn['FY']):,}")
    print(f"2025 service book EUR {tie_pub:,.0f} | placeable now {placeable:,.0f} "
          f"({100 * placeable / tie_pub:.2f}%) | before {old_placeable:,.0f} "
          f"({100 * old_placeable / tie_pub:.2f}%)")
    print(f"tie-out: published vs page-data 2025 delta EUR {abs(tie_pub - tie_mine):,.2f}")
    print(f"payload {len(body) / 1024:.0f} KB | html {len(html.encode('utf-8')) / 1024:.0f} KB")
    print(f"written -> {OUT_HTML}")
    print(f"written -> {OUT_CMD}")
    return 0


def build_html(chart_js: str, body: str) -> str:
    template = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Service parts by vehicle type — demand, sales and the year before</title>
<style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--rule:#d8d2c6;--muted:#6b6257;
      --amber:#b7791f;--green:#2f6b45;--red:#a33;--pale:#eef3f9}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
     font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
h1,h2,h3,h4{font-family:Georgia,'Times New Roman',serif;color:var(--navy);margin:0}
header{background:var(--navy);color:var(--paper);padding:24px 32px 20px}
header h1{color:var(--paper);font-size:24px;line-height:1.25}
header p{margin:8px 0 0;color:#cfd6e2;max-width:1080px;font-size:13.5px}
.wrap{max-width:1440px;margin:0 auto;padding:0 32px 72px}
section{margin:30px 0 0}
h2{font-size:19px;margin-bottom:4px}
.q{display:block;font-family:inherit;font-weight:400;color:var(--terra);font-size:13px;margin-top:3px}
.card{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:16px 18px;margin-top:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:1060px){.grid2,.grid3{grid-template-columns:1fr}}
.controls{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:14px 18px;margin-top:16px;
          display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start;position:sticky;top:0;z-index:20;
          box-shadow:0 2px 6px rgba(21,35,60,.07)}
.ctl{display:flex;flex-direction:column;gap:5px}
.ctl label{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700}
select{padding:7px 10px;border:1px solid var(--rule);border-radius:4px;background:#fff;color:var(--ink);
       font-size:13.5px;font-family:inherit}
select[multiple]{min-width:230px;height:132px;padding:4px}
select[multiple] option{padding:3px 6px;border-radius:3px}
select[multiple] option:checked{background:var(--navy);color:var(--paper)}
.quick{display:flex;gap:6px;margin-top:5px;flex-wrap:wrap}
button{font:inherit;font-size:12px;padding:5px 10px;border:1px solid var(--rule);background:#fff;
       color:var(--navy);border-radius:4px;cursor:pointer}
button:hover{background:var(--pale)}
button.pri{background:var(--navy);color:var(--paper);border-color:var(--navy)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px;max-width:420px}
.chip{background:var(--pale);border:1px solid var(--rule);border-radius:11px;padding:2px 9px;font-size:11.5px;
      color:var(--navy);white-space:nowrap}
.chip b{font-weight:700}
.chip.all{background:#fdf3e0;border-color:#e5cd9a}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(196px,1fr));gap:13px;margin-top:16px}
.kpi{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:13px 15px;border-top:3px solid var(--navy)}
.kpi .v{font-family:Georgia,serif;font-size:23px;color:var(--navy);line-height:1.15}
.kpi .l{font-size:11.5px;color:var(--muted);margin-top:3px}
.kpi .s{font-size:11.5px;color:var(--terra);margin-top:2px}
.kpi.warn{border-top-color:var(--amber)}
.kpi.bad{border-top-color:var(--terra)}
.kpi.good{border-top-color:var(--green)}
.chartbox{position:relative;height:360px}
.chartbox.short{height:290px}
.chartbox.xs{height:225px}
.note{font-size:12.5px;color:#4a443b;background:var(--pale);border-left:3px solid var(--navy);
      padding:10px 13px;margin:13px 0 0;border-radius:0 4px 4px 0}
.note.amber{background:#fdf6e6;border-left-color:var(--amber)}
.note.red{background:#fbf0ef;border-left-color:var(--red)}
.note b{color:var(--navy)}
.key{font-size:12.5px;color:#4a443b;margin-top:10px;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.key i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.key .ln{display:inline-block;width:15px;height:0;border-top:2px dashed var(--terra);margin-right:5px;vertical-align:3px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;font-weight:600;
   font-size:11px;text-transform:uppercase;letter-spacing:.04em}
td{padding:7px 9px;border-bottom:1px solid var(--rule);vertical-align:top}
tbody tr:nth-child(even){background:#faf8f4}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.click{cursor:pointer}
tr.click:hover td{background:var(--pale)}
tr.sel td{background:#fdf3e0}
.up{color:var(--green);font-weight:600}
.down{color:var(--terra);font-weight:600}
.flat{color:var(--muted)}
#tip{position:fixed;z-index:99;background:var(--navy);color:var(--paper);padding:9px 12px;border-radius:4px;
     font-size:12.5px;max-width:340px;line-height:1.45;pointer-events:none;opacity:0;transition:opacity .1s;
     border-left:3px solid var(--terra)}
#tip b{color:#ffd9c4}
.ftab{width:100%;border-collapse:collapse;font-size:13.5px}
.ftab td{padding:9px 10px;border-bottom:1px solid var(--rule)}
.ftab tr.hdr td{background:var(--navy);color:var(--paper);font-weight:600;font-size:11px;
                text-transform:uppercase;letter-spacing:.04em}
.ftab tr.row{cursor:pointer}
.ftab tr.row:hover td{background:var(--pale)}
.ftab tr.row.on td{background:#fdf3e0}
.ftab td.lbl{font-weight:600;color:var(--navy)}
.bread{font-size:13px;color:var(--muted);margin:14px 0 0}
.bread a{color:var(--terra);cursor:pointer;text-decoration:none;font-weight:600}
.bread a:hover{text-decoration:underline}
.smgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px}
@media(max-width:900px){.smgrid{grid-template-columns:repeat(2,1fr)}}
.sm{border:1px solid var(--rule);border-radius:5px;padding:10px 11px;background:#fff}
.sm .t{font-size:12px;font-weight:700;color:var(--navy);line-height:1.25}
.sm .v{font-size:11.5px;color:var(--muted);margin-top:2px}
.sm .d{font-size:12.5px;margin-top:5px;font-weight:600}
.sm .b{display:flex;align-items:flex-end;gap:3px;height:64px;margin-top:6px}
.sm .b div{flex:1;border-radius:2px 2px 0 0;min-height:1px}
.bandgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:12px}
@media(max-width:1060px){.bandgrid{grid-template-columns:1fr}}
.bandcard{border:1px solid var(--rule);border-radius:6px;padding:13px 14px;background:#fff}
.bandcard h4{font-size:16px;margin:0 0 2px}
.bandcard .sub{font-size:12px;color:var(--muted)}
.bandcard .big{font-family:Georgia,serif;font-size:26px;color:var(--navy);margin-top:8px;line-height:1.1}
.bandcard .big.up{color:var(--green)}
.bandcard .big.down{color:var(--terra)}
.bandcard .why{font-size:12.5px;margin-top:8px;color:#4a443b}
.bandcard .why b{color:var(--navy)}
.tag{display:inline-block;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;
     background:var(--pale);border:1px solid var(--rule);border-radius:3px;padding:1px 6px;
     color:var(--navy);font-weight:700;margin-left:6px;vertical-align:2px}
.tag.warn{background:#fdf6e6;border-color:#e5cd9a;color:var(--amber)}
.tag.overlap{background:#f3eef9;border-color:#cbbde3;color:#5b3d8a}
ul.tight{margin:8px 0 0;padding-left:18px;font-size:12.5px;color:#4a443b}
ul.tight li{margin:3px 0}
footer{margin-top:38px;padding-top:16px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--muted)}
</style></head>
.small{font-size:12.5px;color:var(--muted)}
</style></head>
<body>
<div id="tip"></div>
<header>
  <h1>Service parts by vehicle type — how much was sold, and against the same period a year earlier</h1>
  <p>Which vehicle type our service business is growing on and which is quietly shrinking. Choose one
  customer or several, choose a vehicle type, and click any bar to open the level beneath it. Every
  level compares this period with the same period a year earlier in euro, in units and as a
  percentage, side by side. Parts that fit more than one vehicle type stay pooled and are never
  spread across types; click the pooled bar to see the part numbers inside it.
  Snapshot <b>__SNAPSHOT__</b>.</p>
</header>
<div id="jserr" style="display:none;margin:16px 32px 0"></div>
<div class="wrap">

  <div class="controls">
    <div class="ctl">
      <label for="selCust">Customer — hold Ctrl to pick several</label>
      <select id="selCust" multiple size="8"></select>
      <div class="quick">
        <button id="btnAll" class="pri">All 18 markets</button>
        <button id="btnNone">Clear</button>
        <button id="btnItuk">ITUK only</button>
      </div>
    </div>
    <div class="ctl">
      <label for="selFam">Vehicle type</label>
      <select id="selFam"></select>
    </div>
    <div class="ctl">
      <label for="selClock">Period</label>
      <select id="selClock"></select>
      <div class="small" id="clockNote" style="max-width:300px"></div>
    </div>
    <div class="ctl" style="min-width:300px">
      <label>Selected</label>
      <div class="chips" id="chips"></div>
    </div>
  </div>

  <div id="laneNotice"></div>
  <div class="kpis" id="kpis"></div>

  <section>
    <h2>Is the service business by vehicle type growing or shrinking?
      <span class="q">Billed euro and units this period against the same period a year earlier, by
      vehicle type</span></h2>
    <div class="card">
      <div class="chartbox"><canvas id="c_funnel"></canvas></div>
      <div class="key" id="k_funnel"></div>
      <p class="note" id="n_funnel"></p>
    </div>
    <div class="card">
      <h3 style="font-size:15px">The same move, vehicle type by vehicle type
        <span class="q">One panel per type, euro a year, all panels on the same scale</span></h3>
      <div class="smgrid" id="sm_grid"></div>
      <div class="key" id="k_sm"></div>
    </div>
  </section>

  <section id="sec_bands">
    <h2>Inside the N-series truck: 3.5 t, 5.5 t and 7.5 t — growing or shrinking?
      <span class="q" id="bands_q">Billed euro and units for each weight band, this period against
      the same period a year earlier</span></h2>
    <p class="small" id="bands_intro"></p>
    <div class="bandgrid" id="band_cards"></div>
    <div class="card">
      <div class="chartbox short"><canvas id="c_band"></canvas></div>
      <div class="key" id="k_band"></div>
      <p class="note" id="n_band"></p>
    </div>
    <div class="grid2">
      <div class="card">
        <h3 style="font-size:15px">The move, band by band
          <span class="q">One panel per band and for the shared parts, euro a year, one shared
          scale</span></h3>
        <div class="smgrid" id="sm_bands"></div>
        <div class="key" id="k_smbands"></div>
      </div>
      <div class="card">
        <h3 style="font-size:15px">Which series carries each band, and on whose word
          <span class="q">The sourced series-to-weight evidence, one row per series</span></h3>
        <div id="t_bandev"></div>
      </div>
    </div>
    <div class="card">
      <h3 style="font-size:15px">How much of each band is exclusive, and how much is shared
        <span class="q">What decides whether a band can carry a trend of its own</span></h3>
      <div id="t_bandsplit"></div>
      <p class="note" id="n_bandsplit"></p>
    </div>
  </section>

  <section>
    <h2>Drill down — click any bar to open the level beneath it
      <span class="q">Service family, then the part numbers inside it, always against the year
      before</span></h2>
    <div class="card">
      <div class="bread" id="bread"></div>
      <div class="chartbox short" id="box_drill"><canvas id="c_drill"></canvas></div>
      <div class="key" id="k_drill"></div>
      <p class="note" id="n_drill"></p>
      <div id="t_pn"></div>
    </div>
  </section>

  <section>
    <h2>What the fix changed — the same years, before and after
      <span class="q">The shipped page's own numbers beside the corrected ones, so the size of the
      defect is visible rather than asserted</span></h2>
    <div class="card">
      <div class="chartbox short"><canvas id="c_before"></canvas></div>
      <div class="key" id="k_before"></div>
      <p class="note" id="n_before"></p>
      <div id="t_before"></div>
    </div>
  </section>

  <section>
    <h2>What share of the service book sits in each vehicle type, and on how many vehicles?
      <span class="q">Every euro below carries the fleet it was billed against</span></h2>
    <div class="grid2">
      <div class="card">
        <h3 style="font-size:15px">Share of the service-part euro, this period</h3>
        <div class="chartbox short"><canvas id="c_mix"></canvas></div>
        <div class="key" id="k_mix"></div>
      </div>
      <div class="card">
        <h3 style="font-size:15px">Vehicles in service, by vehicle type</h3>
        <div class="chartbox short"><canvas id="c_fleet"></canvas></div>
        <div class="key" id="k_fleet"></div>
        <p class="note" id="n_fleet"></p>
      </div>
    </div>
    <div class="card"><div id="t_fam"></div></div>
  </section>

  <section>
    <h2>What can this page not show, and why?
      <span class="q">Each limit named, with the size of the business it affects</span></h2>
    <div class="card"><div id="t_limits"></div></div>
  </section>

  <footer id="foot"></footer>
</div>

<script>__CHARTJS__</script>
<script id="pmfd-data" type="application/json">__PAYLOAD__</script>
<script>
window.addEventListener('error',function(e){
  var b=document.getElementById('jserr');
  if(!b) return;
  b.style.display='block';
  b.innerHTML='<div class="note red"><b>The page did not finish drawing.</b> A script error stopped '
    +'it, so some panels below are empty. This is a defect in the page, not a data problem. Detail: '
    +String(e.message)+' at line '+String(e.lineno)+'.</div>';
});
(function(){
"use strict";
try{
var D = JSON.parse(document.getElementById('pmfd-data').textContent);
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', MUTED='#6b6257', RULE='#d8d2c6',
    AMBER='#b7791f', GREEN='#2f6b45', PALE='#eef3f9', SLATE='#7a8ba6', GREY='#b9ae9d';
var FAMCOL={}; D.families.forEach(function(f){FAMCOL[f.key]=f.color;});
var FAMLAB={}; D.families.forEach(function(f){FAMLAB[f.key]=f.label;});
var FAMNOTE={}; D.families.forEach(function(f){FAMNOTE[f.key]=f.note;});
var CATLAB={}; D.cats.forEach(function(c){CATLAB[c.key]=c.label;});
var ZONE={}, ZK=D.zoneIds.slice();
D.zones.forEach(function(z){ZONE[z.zid]=z;});
var ZLAB={}, ZCOL={}, ZSHORT={};
D.zones.forEach(function(z){ZLAB[z.zid]=z.label;ZCOL[z.zid]=z.color;ZSHORT[z.zid]=z.short;});
var EXCL=D.zones.filter(function(z){return z.membership!=='also_fits_band';}).map(function(z){return z.zid;});
var BANDS=D.bandOrder.slice();
var BANDCOL=D.bandColor, BANDLAB=D.bandLabel;
var BAND_ZONE_SINGLE={'3.5t_N35':'n35_single','5.5t_N50_N55':'n55_single','7.5t_N50_N62_N75':'n75_single'};
var BAND_ZONE_ALSO={'3.5t_N35':'n35_also','5.5t_N50_N55':'n55_also','7.5t_N50_N62_N75':'n75_also'};

/* ── formatting ──────────────────────────────────────────────────────────────────────────── */
function eur(v){ if(v===null||v===undefined) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+Math.round(Math.abs(v)).toLocaleString('en-GB'); }
function eurm(v){ if(v===null||v===undefined) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+(Math.abs(v)/1e6).toFixed(2)+'M'; }
function num(v){ return (v===null||v===undefined)?'n/a':Math.round(v).toLocaleString('en-GB'); }
function pct(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (100*v).toFixed(d===undefined?1:d)+'%'; }
function signpct(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (v>=0?'+':'')+(100*v).toFixed(d===undefined?1:d)+'%'; }
function cls(v){ if(v===null||v===undefined||!isFinite(v)) return 'flat';
  return v>0.0005?'up':(v<-0.0005?'down':'flat'); }
function eurCell(v){ return v===null||v===undefined?'n/a':eur(v); }

/* tooltip, driven by data-tip so every derived number can explain itself */
var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(!t) return; tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity='1';});
document.addEventListener('mousemove',function(e){
  if(tip.style.opacity!=='1') return;
  var x=e.clientX+14, y=e.clientY+14;
  if(x+350>window.innerWidth) x=e.clientX-360;
  if(y+130>window.innerHeight) y=e.clientY-140;
  tip.style.left=x+'px'; tip.style.top=y+'px';});
document.addEventListener('mouseout',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(t) tip.style.opacity='0';});

Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
Chart.defaults.font.size=12;
Chart.defaults.color='#4a443b';
/* Animation off: the page redraws every chart whenever a control changes, and an animated redraw
   leaves the canvas momentarily empty. On a data page that reads as a blank chart. */
Chart.defaults.animation=false;
Chart.defaults.animations=false;
Chart.defaults.resizeDelay=0;
var charts={};
function mk(id,cfg){ var el=document.getElementById(id); if(!el) return;
  if(charts[id]) charts[id].destroy();
  charts[id]=new Chart(el,cfg); }

/* ── state ───────────────────────────────────────────────────────────────────────────────── */
var selCust={}, selFam='all', clock='CY', drillCat=null, drillBand=null;
selCust[D.markets.indexOf('IUK')>=0?'IUK':D.markets[0]]=true;
/* The vehicle type in force is whatever the vehicle-type control says. Clicking a bar in the top
   chart sets the control, so the filter and the drill always agree rather than being two things
   that can disagree. */
function famFilter(){ return selFam==='all' ? null : selFam; }

var custSel=document.getElementById('selCust'), famSel=document.getElementById('selFam'),
    clkSel=document.getElementById('selClock');

D.markets.forEach(function(m){
  var o=document.createElement('option'); o.value=m; o.textContent=m; custSel.appendChild(o);});
['all'].concat(D.families.map(function(f){return f.key;})).forEach(function(k){
  var o=document.createElement('option'); o.value=k;
  o.textContent = k==='all' ? 'All vehicle types' : FAMLAB[k];
  famSel.appendChild(o);});
Object.keys(D.clocks).forEach(function(c){
  var o=document.createElement('option'); o.value=c; o.textContent=D.clocks[c].label;
  clkSel.appendChild(o);});

function chosen(){ return D.markets.filter(function(m){return selCust[m];}); }

/* ── aggregation over the selected customers ─────────────────────────────────────────────── */
/* rec: [marketIdx, catIdx, famIdx, period, eur, units]
   recPn: [pnIdx, marketIdx, period, eur, units]                                        */
var FAMK=D.families.map(function(f){return f.key;});
function agg(){
  var per=D.clocks[clock], mk=chosen(), mset={};
  mk.forEach(function(m,i){ mset[D.markets.indexOf(m)]=true; });
  var byFam={}, byFamCat={}, byCat={};
  var rows=D.rec[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!mset[r[0]]) continue;
    var fk=FAMK[r[2]], ck=D.cats[r[1]].key, p=r[3];
    var a=byFam[fk]||(byFam[fk]={});
    var b=a[p]||(a[p]={eur:0,units:0}); b.eur+=r[4]; b.units+=r[5];
    var k2=fk+'|'+ck; var c=byFamCat[k2]||(byFamCat[k2]={});
    var e=c[p]||(c[p]={eur:0,units:0}); e.eur+=r[4]; e.units+=r[5];
    var d3=byCat[ck]||(byCat[ck]={});
    var g=d3[p]||(d3[p]={eur:0,units:0}); g.eur+=r[4]; g.units+=r[5];
  }
  return {byFam:byFam, byFamCat:byFamCat, byCat:byCat, markets:mk, per:per, mset:mset};
}
function pnAgg(A){
  var out={};
  var rows=D.recPn[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!A.mset[r[1]]) continue;
    var a=out[r[0]]||(out[r[0]]={});
    var b=a[r[2]]||(a[r[2]]={eur:0,units:0}); b.eur+=r[3]; b.units+=r[4];
  }
  return out;
}

/* ── the tonnage level inside the N-series ─────────────────────────────────────────────────
   recZ   : [marketIdx, zoneIdx, period, eur, units]
   recZcat: [marketIdx, zoneIdx, catIdx, period, eur, units]
   A part number that fits more than one band appears under each of those bands, so the band
   rows overlap. `sums` on the zone says whether its euro may be added to another zone's. */
function zoneAgg(A){
  var out={};
  var rows=D.recZ[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!A.mset[r[0]]) continue;
    var a=out[r[1]]||(out[r[1]]={});
    var b=a[r[2]]||(a[r[2]]={eur:0,units:0}); b.eur+=r[3]; b.units+=r[4];
  }
  return out;
}
function zoneCatAgg(A){
  var out={};
  var rows=D.recZcat[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!A.mset[r[0]]) continue;
    var a=out[r[1]]||(out[r[1]]={});
    var b=a[r[2]]||(a[r[2]]={});
    var c=b[r[3]]||(b[r[3]]={eur:0,units:0}); c.eur+=r[4]; c.units+=r[5];
  }
  return out;
}
/* the band rows the N-series section is built from, in a fixed order */
function zIndex(zid){ return D.zoneIds.indexOf(zid); }
function zRow(Z, zid, latest){
  var pr=pairFor(Z[zIndex(zid)]||{},latest);
  var z=ZONE[zid];
  return {zid:zid,label:z.label,short:z.short,note:z.note,color:z.color,
          membership:z.membership,band:z.band,
          sums:(z.membership!=='also_fits_band'),
          eur:pr?pr.eur:0, units:pr?pr.units:0,
          eurPrev:pr?pr.eurPrev:null, unitsPrev:pr?pr.unitsPrev:null,
          eurPct:pr?pr.eurPct:null, unitsPct:pr?pr.unitsPct:null,
          hasPrev:pr?pr.hasPrev:false};
}
/* The band euro as a reader asked for it: everything that fits the band, exclusive and shared
   together. Marked, because the shared part of it sits in more than one band. */
function bandTotal(Z, band, latest){
  var s=zRow(Z,BAND_ZONE_SINGLE[band],latest), a=zRow(Z,BAND_ZONE_ALSO[band],latest);
  var e=s.eur+a.eur, ep=(s.eurPrev||0)+(a.eurPrev||0);
  var u=s.units+a.units, up=(s.unitsPrev===null&&a.unitsPrev===null)?null:((s.unitsPrev||0)+(a.unitsPrev||0));
  return {band:band,label:BANDLAB[band],color:BANDCOL[band],
          eur:e, units:u,
          eurPrev:(s.hasPrev||a.hasPrev)?ep:null,
          unitsPrev:(s.hasPrev||a.hasPrev)?up:null,
          eurPct:ep>0?(e/ep-1):null,
          unitsPct:(up&&up>0)?(u/up-1):null,
          singleEur:s.eur, sharedEur:a.eur,
          singleEurPrev:s.eurPrev, sharedEurPrev:a.eurPrev,
          singleUnits:s.units, sharedUnits:a.units,
          singleUnitsPrev:s.unitsPrev, sharedUnitsPrev:a.unitsPrev,
          hasPrev:!!s.hasPrev||!!a.hasPrev};
}
function bandFleet(band){
  /* The fleet split that exists on disk is cv_std × the market's measured 3.5 t share, and the
     remainder. No source on disk separates the 5.5 t trucks from that remainder, so the 5.5 t
     band gets no fleet number rather than an invented one. */
  if(band==='3.5t_N35') return {n:fleetSum(0), label:'vehicles in service at 3.5 t'};
  if(band==='5.5t_N50_N55') return {n:null,
    label:'no fleet figure — no source splits the 5.5 t trucks out of the N-series parc'};
  return {n:fleetSum(1),
    label:'vehicles in service in the rest of the N-series fleet, which holds the 5.5 t trucks too'};
}
function fleetSum(i){
  var t=0;
  chosen().forEach(function(m){ t+=((D.nseries_fleet[m]||[0,0])[i]||0); });
  return Math.round(t);
}

/* ── the comparison pair: this period and the same period a year earlier ────────────────── */
function pairFor(obj,p){
  /* A financial year is named by its closing year, so the year before FY2026 is FY2025. Both are
     twelve-month periods starting in April, so they are like-for-like. */
  var prev=p-1;
  var cur=obj&&obj[p] ? obj[p] : null;
  var was=obj&&obj[prev] ? obj[prev] : null;
  if(!cur&&!was) return null;
  var ce=cur?cur.eur:0, we=was?was.eur:0, cu=cur?cur.units:0, wu=was?was.units:0;
  return {p:p, prev:prev, cur:cur, was:was, eur:ce, units:cu, eurPrev:was?we:null,
          unitsPrev:was?wu:null,
          eurPct:(was&&we>0)?(ce/we-1):null, unitsPct:(was&&wu>0)?(cu/wu-1):null,
          hasPrev:!!was};
}

/* ── render ─────────────────────────────────────────────────────────────────────────────── */
function render(){
  var A=agg(), C=D.clocks[clock];
  var latest=C.latestComplete;
  clkSel.value=clock; famSel.value=selFam;
  /* a band filter only makes sense inside the N-series; leaving that vehicle type clears it */
  if(selFam!=='n_series_truck' && drillBand){ drillBand=null; }

  /* chips */
  document.getElementById('chips').innerHTML =
    (A.markets.length===D.markets.length
      ? '<span class="chip all"><b>All '+D.markets.length+' markets</b></span>'
      : A.markets.map(function(m){return '<span class="chip">'+m+'</span>';}).join(''))
    + (A.markets.length>1 ? '<span class="chip">'+A.markets.length+' selected, summed</span>' : '');
  document.getElementById('clockNote').innerHTML =
    C.spelled[String(latest)] + '. ' + C.note;

  /* lane notice — the two interval schedules are never averaged */
  var lanes={};
  A.markets.forEach(function(m){ var l=D.lane[m]||'internal'; lanes[l]=(lanes[l]||0)+1; });
  var laneBits=Object.keys(lanes).map(function(l){
    return '<b>'+lanes[l]+'</b> on the '+(l==='agreed'
      ? 'schedule agreed for that market'
      : 'internal service schedule')+'';});
  document.getElementById('laneNotice').innerHTML =
    '<div class="note"><b>Two service-interval schedules run through this network and they are '
    +'never averaged or added together</b>, because they answer different questions about the same '
    +'fleet. In your selection: '+laneBits.join(', ')+'.'
    +(A.markets.indexOf('ITUK')>=0
      ? ' ITUK runs the schedule agreed with that distributor: filters 1.25 visits a year, clutch '
        +'and brake 0.5, on a 22,389-vehicle fleet.'
      : '')
    +'</div>';

  /* ── family rows (level 1) */
  var famRows=D.families.map(function(f){
    var pr=pairFor(A.byFam[f.key]||{},latest);
    return {key:f.key,label:f.label,note:f.note,color:f.color,
            eur:pr?pr.eur:0, units:pr?pr.units:0,
            eurPrev:pr?pr.eurPrev:null, unitsPrev:pr?pr.unitsPrev:null,
            eurPct:pr?pr.eurPct:null, unitsPct:pr?pr.unitsPct:null,
            hasPrev:pr?pr.hasPrev:false};
  });
  var famSelRows = selFam==='all' ? famRows : famRows.filter(function(r){return r.key===selFam;});
  var head={eur:0,units:0,eurPrev:0,unitsPrev:0};
  famRows.forEach(function(r){ head.eur+=r.eur; head.units+=r.units;
    head.eurPrev+=(r.eurPrev||0); head.unitsPrev+=(r.unitsPrev||0); });
  var named=famRows.filter(function(r){return D.namedFamilies.indexOf(r.key)>=0;});
  var namedEur=named.reduce(function(s,r){return s+r.eur;},0);
  var namedPrev=named.reduce(function(s,r){return s+(r.eurPrev||0);},0);
  var fleetTot=0; A.markets.forEach(function(m){ fleetTot+=(D.fleet[m]||{total:0}).total; });

  /* ── KPIs */
  var k=[];
  k.push({v:eurm(head.eur), l:'service parts billed, '+C.spelled[String(latest)],
    s:(head.eurPrev?signpct((head.eur/(head.eurPrev||1))-1)+' against '+C.spelled[String(latest-1)]:''),
    cls:cls(head.eurPrev?(head.eur/(head.eurPrev||1))-1:null),
    tip:'Every part number that carries a service family, summed over <b>'
      +(A.markets.length===D.markets.length?'all 18 markets':A.markets.join(', '))+'</b>.<br>'
      +C.spelled[String(latest)]+': '+eur(head.eur)+'<br>'
      +C.spelled[String(latest-1)]+': '+eur(head.eurPrev)+'<br>'
      +'Sales are sales: business partner or own-brand, it counts here. Parts that fit more than '
      +'one vehicle type are inside this total and are also shown pooled, never split.'});
  k.push({v:num(head.units)+' pcs', l:'units billed, '+C.spelled[String(latest)],
    s:(head.unitsPrev?signpct((head.units/(head.unitsPrev||1))-1)+' against the year before':''),
    cls:cls(head.unitsPrev?(head.units/(head.unitsPrev||1))-1:null),
    tip:'Pieces billed on those same part numbers. A piece count on its own says little — read it '
      +'beside the euro above and the fleet below, because an engine and a bolt are both one piece.'});
  k.push({v:num(fleetTot), l:'vehicles in service, the fleet this sits on',
    tip:'The denominator. Fleet for the selection: N-series '
      +num(A.markets.reduce(function(s,m){return s+(D.fleet[m]||{n_series:0}).n_series;},0))
      +', heavy '+num(A.markets.reduce(function(s,m){return s+(D.fleet[m]||{heavy:0}).heavy;},0))
      +', light '+num(A.markets.reduce(function(s,m){return s+(D.fleet[m]||{light:0}).light;},0))
      +'.<br>A 2025 estimate used for every year, so expected demand is flat over time by '
      +'construction. Only the billing moves.'});
  k.push({v:pct(D.totals.placeable2025/D.totals.serviceBook2025,1),
    l:'of the 2025 service book now placed in a vehicle type',
    s:'46.6% before the fix — the rest was pooled or had no vehicle named',
    cls:'good',
    tip:'2025 service-part euro that resolves to exactly one vehicle type, against the published '
      +'service-part book of '+eur(D.totals.serviceBook2025)+'.<br>Before: '
      +eur(D.totals.placeable2025Old)+' ('+pct(D.totals.placeable2025OldPct/100,1)+').<br>'
      +'The remainder is not missing: it is pooled where a part fits more than one type, and has no '
      +'vehicle named where no source names one. Both are shown, never spread.'});
  var heavy=famRows.filter(function(r){return r.key==='heavy_truck';})[0];
  var B=D.before&&D.before.available?D.before:null;
  var heavyBefore=B&&B.eur.heavy_truck?B.eur.heavy_truck[String(latest)]:null;
  k.push({v:eurm(heavy?heavy.eur:0), l:'heavy truck billed, '+C.spelled[String(latest)]
      +', '+A.markets.length+(A.markets.length===1?' market':' markets'),
    s:(heavyBefore!==null&&heavyBefore!==undefined
        ? 'all 18 markets read '+eur(heavyBefore)+' on the shipped page; they read '
          +eur(((D.trend[clock].heavy_truck||{}).eur||{})[String(latest)]||0)+' now'
        : (heavy&&heavy.eurPrev?signpct((heavy.eur/(heavy.eurPrev||1))-1)+' against the year before':'')),
    cls:cls(heavy&&heavy.eurPrev?(heavy.eur/(heavy.eurPrev||1))-1:null),
    tip:'Parts that fit heavy truck and nothing else, for the customers you have selected. '
      +'This is the line the earlier family view suppressed: part numbers the parts cross-reference '
      +'already names as heavy-truck-only were dropped by one step because their family was known, '
      +'and dropped by the next because they were not in the vehicle decode. They appeared on '
      +'neither side.'
      +(heavyBefore!==null&&heavyBefore!==undefined
        ? ' The earlier page read '+eur(heavyBefore)+' for the 2025 network total.'
        : '')});
  document.getElementById('kpis').innerHTML=k.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'" data-tip="'+x.tip+'"><div class="v">'+x.v
      +'</div><div class="l">'+x.l+'</div>'+(x.s?'<div class="s">'+x.s+'</div>':'')+'</div>';}).join('');

  /* ── chart 1: the funnel, this period against the same period a year earlier */
  var labels=famSelRows.map(function(r){return r.label;});
  var curE=famSelRows.map(function(r){return r.eur;});
  var prevE=famSelRows.map(function(r){return r.eurPrev;});
  mk('c_funnel',{type:'bar',
    data:{labels:labels,datasets:[
      {label:C.spelled[String(latest)],data:curE,backgroundColor:famSelRows.map(function(r){return r.color;}),
       borderRadius:3},
      {label:C.spelled[String(latest-1)],data:prevE,backgroundColor:'#d9d3c7',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){ return c.datasetIndex===0
            ? C.spelled[String(latest)]+': '+eur(c.raw)
            : C.spelled[String(latest-1)]+': '+eur(c.raw);},
          afterBody:function(items){
            var r=famSelRows[items[0].dataIndex];
            return [r.eurPrev===null?'no billing a year earlier':
              (signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units'),
              r.units+' units this period against '+(r.unitsPrev===null?'n/a':r.unitsPrev+' a year earlier'),
              'Fleet: '+num(familyFleet(r.key))+' vehicles in service'];}}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  document.getElementById('k_funnel').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>'+C.spelled[String(latest)]+'</span>'
    +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
    +'<span class="small">the second bar is the same twelve months a year earlier, so the length '
    +'difference is the move. Click any bar to open the level beneath it.</span>';

  /* the funnel bars are clickable: clicking one sets the vehicle-type control and descends */
  var funnel=charts['c_funnel'];
  funnel.options.onClick=function(evt,els){
    if(!els.length) return;
    var r=famSelRows[els[0].index];
    if(!r) return;
    selFam=r.key; drillCat=null; drillBand=null; render();
  };
  funnel.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
  funnel.update();

  var nF=document.getElementById('n_funnel');
  nF.innerHTML='Each bar is billed euro on part numbers that resolve to that one vehicle type, '
    +'plus, in the pooled bar, the part numbers that fit several. <b>Read the euro, not the '
    +'percentage alone</b>: the heavy-truck fleet is small, so its percentage moves are large on '
    +'small numbers. '
    +(famSelRows.length===1
      ? 'You have filtered to one vehicle type, so the bar is that type alone.'
      : 'Figures are shown for every vehicle type; the pool is never added into the three named '
        +'types because a pooled part is available to all of them.');

  /* ── small multiples, one panel per vehicle type, euro a year on a shared scale */
  var periodsAll=C.periods;
  var allV=[];
  D.families.forEach(function(f){
    periodsAll.forEach(function(p){
      var o=(D.trend[clock][f.key]||{}).eur||{}; var v=o[String(p)];
      var A2={mset:{}}; /* the network trend is pre-aggregated over all 18 markets */
      if(v!==undefined) allV.push(v);
    });});
  var vmax=allV.length?Math.max.apply(null,allV):1;
  var pal=periodsAll.map(function(p){ return p===latest?NAVY:(p===latest-1?'#c9d3e0':SLATE); });
  document.getElementById('sm_grid').innerHTML=D.families.map(function(f){
    var o=(D.trend[clock][f.key]||{}).eur||{};
    var vals=periodsAll.map(function(p){ return o[String(p)]===undefined?null:o[String(p)]; });
    var bars=vals.map(function(v,i){
      if(v===null) return '<div style="height:0"></div>';
      return '<div style="height:'+Math.max(2,Math.round(64*v/vmax))+'px;background:'+pal[i]+'"></div>';}).join('');
    var c=o[String(latest)], w=o[String(latest-1)];
    var g=(c!==undefined&&w)?(c/w-1):null;
    var units=((D.trend[clock][f.key]||{}).units||{});
    return '<div class="sm" data-tip="<b>'+f.label+'</b><br>'+f.note+'<br>'
      +periodsAll.map(function(p,i){ return C.spelled[String(p)]+': '+(vals[i]===null?'no billing':eur(vals[i]));}).join('<br>')
      +'<br>Units '+C.spelled[String(latest)]+': '+num(units[String(latest)]===undefined?null:units[String(latest)])
      +'<br>Fleet '+num(familyFleet(f.key))+' vehicles'
      +'"><div class="t">'+f.label+'</div>'
      +'<div class="b">'+bars+'</div>'
      +'<div class="d '+(g===null?'flat':cls(g))+'">'+(g===null?'n/a':signpct(g))+'</div>'
      +'<div class="v">'+eurm(c===undefined?null:c)+' in '+C.short+' '+latest
      +' on '+num(familyFleet(f.key))+' vehicles</div></div>';}).join('');
  document.getElementById('k_sm').innerHTML=periodsAll.map(function(p,i){
    return '<span><i style="background:'+pal[i]+'"></i>'+C.spelled[String(p)]
      +(D.clocks[clock].months[String(p)]<12?' (part year, '+D.clocks[clock].months[String(p)]+' months)':'')
      +'</span>';}).join('')
    +'<span class="small">all panels share one euro scale; the figure under each panel is the change '
    +'from '+C.spelled[String(latest-1)]+' to '+C.spelled[String(latest)]+'. Network totals, not '
    +'your customer selection.</span>';

  /* ── chart 4: the tonnage bands inside the N-series */
  renderBands(zoneAgg(A), latest);
  renderDrill(A,latest);
  renderBefore(A,latest);
  renderMix(A,latest);
  renderFleet(A);
  renderFamTable(A,latest);
  renderLimits(A,latest);
}

/* ── the N-series band section ────────────────────────────────────────────────────────────── */
function renderBands(Z, latest){
  var C=D.clocks[clock], per=String(latest), wasp=String(latest-1);

  /* the N-series total: the exclusive part of the whole thing, over the selection */
  var nsZ=zRow(Z,'n_shared_bands',latest);
  var nsSingle=BANDS.reduce(function(s,b){return s+zRow(Z,BAND_ZONE_SINGLE[b],latest).eur;},0);
  var nsAll=nsSingle+nsZ.eur+zRow(Z,'n_series_unresolved',latest).eur;
  var nsPrev=BANDS.reduce(function(s,b){return s+(zRow(Z,BAND_ZONE_SINGLE[b],latest).eurPrev||0);},0)
            +(nsZ.eurPrev||0)+(zRow(Z,'n_series_unresolved',latest).eurPrev||0);

  document.getElementById('bands_intro').innerHTML=
    'The vehicle-type control above splits the business into N-series truck, heavy truck and D-Max. '
    +'For the N-series truck it can go one level further, because the EPC\'s own editions name the '
    +'series each part number fits and the series carries a weight: the weight on a name plate comes '
    +'from the series (NLR, NMR, NPR and the rest) and never from the number in the name — NLR85, '
    +'NLR87 and NLR88 are all 3.5 t, and FRR90 and FSR90 share the number 90 at 11 t and 13.5 t. '
    +'Each band below is therefore every part number that fits that weight, whether it fits only '
    +'that weight or fits others as well; the shared part is named on the card so a band is never '
    +'read as exclusive when it is not. '
    +'<b>Read the move, not the level.</b> The euro on a band is what we billed in that period, so a '
    +'short period reads low: '+C.spelled[per]+' holds '
    +D.clocks[clock].months[per]+' month'+(D.clocks[clock].months[per]===1?'':'s')
    +'. The band rows overlap, so they are never added together; only the "shared counted once" '
    +'line and the "fits this band only" lines are mutually exclusive.';

  /* ── one card per band */
  var cards=[];
  BANDS.forEach(function(b){
    var t=bandTotal(Z,b,latest);
    var fl=bandFleet(b);
    var flTxt=(fl.n===null)?fl.label
      :(num(fl.n)+' — '+fl.label+', out of '+num(nseriesFleetTotal())
        +' N-series trucks in service for this selection');
    /* the write-up answers the question in euro, in units and as a percentage against the same
       period a year earlier — and says how much of it is shared before the percentage is trusted */
    var sharedShare=(t.eur>0)?(t.sharedEur/t.eur):0;
    var g=t.eurPct;
    var verdict;
    if(!t.hasPrev){
      verdict='No billing in '+C.spelled[wasp]+' for this selection, so no change can be read.'; }
    else if(t.eurPrev===null||t.eurPrev<=0){
      verdict='Almost nothing was billed here in '+C.spelled[wasp]+' ('+eur(t.eurPrev||0)
        +'), so the percentage has no base to sit on.'; }
    else if(g===null){ verdict='Cannot be read.'; }
    else if(sharedShare>=0.98){
      verdict='The change is real, but it cannot be attributed to this band: '+pct(sharedShare)
        +' of the euro on it is parts that also fit another band.'; }
    else if(sharedShare>=0.5){
      verdict='Mostly shared. '+pct(sharedShare)+' of the euro on this band is parts that also fit '
        +'another band, so read the change as "these parts fit this band among others", not as a '
        +'trend of its own.'; }
    else {
      verdict='Mostly exclusive. '+pct(1-sharedShare)+' of the euro on this band is parts that fit '
        +'this weight and nothing else, so the change can be read as this band\'s own.'; }
    var cls_=g===null?'':cls(g);
    cards.push(
      '<div class="bandcard" data-tip="<b>'+BANDLAB[b]+'</b><br>'
      +'Every part number that fits this weight, fits-only and shared together.<br>'
      +C.spelled[per]+': '+eur(t.eur)+' on '+num(t.units)+' units<br>'
      +C.spelled[wasp]+': '+(t.eurPrev===null?'no billing'
        :eur(t.eurPrev)+' on '+num(t.unitsPrev)+' units')+'<br>'
      +'of which fits this band only: '+eur(t.singleEur)+'<br>'
      +'of which also fits another band: '+eur(t.sharedEur)
      +' — that part is counted in the other band too, so the bands overlap"><h4 style="color:'
      +t.color+'">'+t.label+'</h4>'
      +'<div class="sub">'+C.spelled[per]+' against '+C.spelled[wasp]+'</div>'
      +'<div class="big '+cls_+'">'+eur(t.eur)+'</div>'
      +'<div class="sub">'+(t.eurPrev===null?'no billing a year earlier'
        :signpct(g)+' in euro against '+eur(t.eurPrev)+' ('
          +((t.eur-(t.eurPrev||0))>=0?'+':'')+eur(t.eur-(t.eurPrev||0))+')')
      +'</div>'
      +'<div class="why"><b>Units</b> '+num(t.units)
      +(t.unitsPrev===null||t.unitsPrev===0?' — nothing billed in this band a year earlier'
        :' against '+num(t.unitsPrev)+' ('+signpct(t.unitsPct)+', '
          +((t.units-(t.unitsPrev||0))>=0?'+':'')+num(t.units-(t.unitsPrev||0))+')')
      +'<br><b>Shared part of this band</b> '+pct(sharedShare)+' ('+eur(t.sharedEur)+' of '
      +eur(t.eur)+')'
      +'<br><b>Fleet</b> '+flTxt
      +'<br>'+verdict+'</div></div>');
  });
  document.getElementById('band_cards').innerHTML=cards.join('');

  /* ── the band chart: this period against the same period a year earlier, per band */
  var rows=BANDS.map(function(b){
    var t=bandTotal(Z,b,latest);
    var s=zRow(Z,BAND_ZONE_SINGLE[b],latest);
    var a=zRow(Z,BAND_ZONE_ALSO[b],latest);
    t.single=s; t.shared=a; t.band=b; return t;});
  mk('c_band',{type:'bar',
    data:{labels:rows.map(function(r){return r.label;}),datasets:[
      {label:C.spelled[per]+' — second bar: same months a year earlier',
       data:rows.map(function(r){return r.eur;}),backgroundColor:rows.map(function(r){return r.color;}),
       borderRadius:3},
      {label:C.spelled[wasp],data:rows.map(function(r){return r.eurPrev;}),
       backgroundColor:'#d9d3c7',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{afterBody:function(items){
            var r=rows[items[0].dataIndex];
            return [r.eurPrev===null?'no billing a year earlier':
              signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units',
              'this period '+eur(r.eur)+' on '+num(r.units)+' units',
              'year before '+eur(r.eurPrev)+' on '+num(r.unitsPrev)+' units',
              'fits this band only: '+eur(r.singleEur),
              'also fits another band: '+eur(r.sharedEur)+' (counted in the other band too)',
              'fleet: '+(bandFleet(r.band).n===null?'no source splits this band out of the fleet'
                :num(bandFleet(r.band).n)+' '+bandFleet(r.band).label)];
          }}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  document.getElementById('k_band').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>'+C.spelled[per]+' billed euro</span>'
    +'<span><i style="background:#d9d3c7"></i>'+C.spelled[wasp]+' — the same months a year earlier</span>'
    +'<span class="small">one bar per weight band; the pair of bars is the move. Click a bar to open '
    +'the part numbers that fit that band.</span>';
  document.getElementById('n_band').innerHTML=
    'Each bar is every part number that fits that weight, exclusive and shared together, against '
    +'the same months a year earlier. <b>The three bands overlap</b>: a part that fits 3.5 t and '
    +'7.5 t is inside both bars, so the three bars must never be added. '
    +'The N-series itself billed '+eur(nsAll)+' this period against '+eur(nsPrev)+' a year earlier, '
    +'and that total is the mutually exclusive figure, not the sum of these bars.';
  var cb=charts['c_band'];
  cb.options.onClick=function(evt,els){
    if(!els.length) return;
    var b=rows[els[0].index].band; drillBand=b; drillCat=null; selFam='n_series_truck';
    famSel.value='n_series_truck'; render();};
  cb.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
  cb.update();

  /* ── small multiples: every zone, euro a year, one shared scale */
  var zOrder=BANDS.reduce(function(acc,b){
    acc.push(BAND_ZONE_SINGLE[b]); acc.push(BAND_ZONE_ALSO[b]); return acc;},
    []).concat(['n_shared_bands','n_series_unresolved']);
  var allV=[];
  zOrder.forEach(function(zid){
    var o=Z[zIndex(zid)]||{};
    D.clocks[clock].periods.forEach(function(p){ if(o[p]!==undefined) allV.push(o[p].eur); });
  });
  var vmax=allV.length?Math.max.apply(null,allV):1;
  var pal=D.clocks[clock].periods.map(function(p){
    return p===latest?NAVY:(p===latest-1?'#c9d3e0':SLATE);});
  document.getElementById('sm_bands').innerHTML=zOrder.map(function(zid){
    var o=Z[zIndex(zid)]||{};
    var vals=D.clocks[clock].periods.map(function(p){
      return o[String(p)]===undefined?null:o[String(p)].eur;});
    var bars=vals.map(function(v,i){
      if(v===null) return '<div style="height:0"></div>';
      return '<div style="height:'+Math.max(2,Math.round(64*v/vmax))+'px;background:'+pal[i]+'"></div>';}).join('');
    var z=ZONE[zid];
    var cur=o[String(latest)]?o[String(latest)].eur:0;
    var was=o[String(wasp)]?o[String(wasp)].eur:null;
    var g=(was?cur/was-1:null);
    var fleetTxt=(z.membership==='single_band_only'||z.membership==='also_fits_band')
      ? (bandFleet(z.band).n===null?'no fleet figure':num(bandFleet(z.band).n)+' '+bandFleet(z.band).label)
      : (zid==='n_shared_bands'?num(nseriesFleetTotal())+' N-series trucks in service, all bands'
         :'no single fleet applies');
    return '<div class="sm" data-tip="<b>'+z.label+'</b><br>'+z.note+'<br>'
      +D.clocks[clock].periods.map(function(p,i){
        return C.spelled[String(p)]+': '+(vals[i]===null?'no billing':eur(vals[i]));}).join('<br>')
      +'<br>Units '+C.spelled[per]+': '+num(o[String(latest)]?o[String(latest)].units:null)
      +'<br>Fleet: '+fleetTxt
      +'">'
      +'<div class="t">'+z.short+(z.membership==='also_fits_band'
          ?'<span class="tag overlap">overlaps</span>':'')+'</div>'
      +'<div class="b">'+bars+'</div>'
      +'<div class="d '+(g===null?'flat':cls(g))+'">'+(g===null?'n/a':signpct(g))+'</div>'
      +'<div class="v">'+eurm(cur)+' in '+D.clocks[clock].short+' '+latest
      +' on '+num(o[String(latest)]?o[String(latest)].units:0)+' units</div></div>';}).join('');
  document.getElementById('k_smbands').innerHTML=
    D.clocks[clock].periods.map(function(p,i){
      return '<span><i style="background:'+pal[i]+'"></i>'+C.spelled[String(p)]
        +(D.clocks[clock].months[String(p)]<12?' (part period, '
          +D.clocks[clock].months[String(p)]+' months)':'')+'</span>';}).join('')
    +'<span class="small">one panel per band line; the "overlaps" panels are counted inside a band '
    +'above, so they are the shared part seen on its own. All panels share one euro scale. Network '
    +'or selection totals as the customer control says, not per market.</span>';

  /* ── the sourced series evidence */
  /* The page face names the source in words. The file path for each row stays in
     series_to_tonnage.csv, which is where a reader who wants the raw quote goes. */
  var evRows=[];
  function words(src){
    if(/no source/.test(src)) return 'no source states a weight for this series';
    if(/Duncan/.test(src)) return 'ITUK brake study, service-interval appendix';
    if(/GIDSS_maint_N_MY2[0-9]/.test(src)) return 'GIDSS maintenance schedule, N-series';
    if(/GIDSS_maint_N_MY14/.test(src)) return 'GIDSS maintenance schedule, earlier N-series edition';
    if(/VIN register/.test(src)) return 'JP VIN register, the maker\'s own model names and GVW';
    if(/EPC/.test(src) && /cross-reference/.test(src))
      return 'the EPC edition each part number returns, and the parts cross-reference';
    if(/EPC/.test(src)) return 'the EPC edition each part number returns';
    if(/registry_model/.test(src)) return 'the parts cross-reference\'s own model tag';
    if(/cross-reference/.test(src)) return 'the parts cross-reference';
    return 'a source on disk';
  }
  BANDS.forEach(function(b){
    var e=D.bandEvidence[b];
    e.quotes.forEach(function(q){
      evRows.push([q.series, BANDLAB[b], q.confidence, words(q.source),
        '<span class="small">'+q.quote+'</span>']);});
  });
  (D.bandEvidence.unresolved_series.quotes||[]).forEach(function(q){
    evRows.push([q.series,'not stated by the sources',q.confidence, words(q.source),
      '<span class="small">'+q.quote+'</span>']);});
  htmlTable('t_bandev',
    ['Series','Band','Confidence','Where the weight comes from','What it says'],
    evRows,['','','','','']);
  document.getElementById('t_bandev').insertAdjacentHTML('afterbegin',
    '<p class="small" style="margin-bottom:2px"><b>'+evRows.length+' series rows</b>, each one read '
    +'from a source on disk — the full quote, the file and its line are in the banded series table '
    +'behind this page. A series is matched as a whole word, never as a fragment: an earlier error in '
    +'this workstream came from matching a two-letter prefix as a pattern and catching the pickup '
    +'wildcard that starts with the same letters, which inflated a heavy-truck figure by EUR 1.8M.</p>');

  /* ── how much of each band is exclusive versus shared */
  var split=D.nseriesBandSplit;
  var rowsSplit=[];
  var totExcl=BANDS.reduce(function(s,b){return s+zRow(Z,BAND_ZONE_SINGLE[b],latest).eur;},0)
              +nsZ.eur+zRow(Z,'n_series_unresolved',latest).eur;
  var NS_STATUS=D.nseriesByStatus;
  BANDS.forEach(function(b){
    var s=zRow(Z,BAND_ZONE_SINGLE[b],latest), a=zRow(Z,BAND_ZONE_ALSO[b],latest);
    var t=s.eur+a.eur, tp=(s.eurPrev||0)+(a.eurPrev||0);
    var tHasPrev=!!s.hasPrev||!!a.hasPrev;
    var si=split[b]||{};
    rowsSplit.push([
      '<b>'+BANDLAB[b]+'</b>',
      eur(t), totExcl>0?pct(t/totExcl):'n/a',
      tHasPrev&&tp>0
        ? '<span class="'+cls(t/tp-1)+'">'+signpct(t/tp-1)+'</span>'
        : 'n/a',
      eur(s.eur)+(s.eurPrev===null?'':' <span class="small">from '+eur(s.eurPrev)+'</span>'),
      eur(a.eur)+(a.eurPrev===null?'':' <span class="small">from '+eur(a.eurPrev)+'</span>'),
      t>0?pct(a.eur/t):'n/a',
      String(si.single_band_pns||0)+' PNs',
      String(si.shared_pns_that_also_fit||0)+' PNs']);
  });
  rowsSplit.push(['<b>Shared across bands — counted once</b>',eur(nsZ.eur),
    totExcl>0?pct(nsZ.eur/totExcl):'n/a',
    (nsZ.hasPrev&&nsZ.eurPrev>0
      ? '<span class="'+cls(nsZ.eur/nsZ.eurPrev-1)+'">'+signpct(nsZ.eur/nsZ.eurPrev-1)+'</span>'
      : 'n/a'),
    'counted here once','—','100%',String(NS_STATUS.shared_across_bands.part_numbers)+' PNs','—']);
  var ur=zRow(Z,'n_series_unresolved',latest);
  rowsSplit.push(['<b>Series the sources do not state a weight for</b>',eur(ur.eur),
    totExcl>0?pct(ur.eur/totExcl):'n/a',
    (ur.hasPrev&&ur.eurPrev>0
      ? '<span class="'+cls(ur.eur/ur.eurPrev-1)+'">'+signpct(ur.eur/ur.eurPrev-1)+'</span>'
      : 'n/a'),
    'no band can be read','—','n/a',
    String(NS_STATUS.series_unresolved.part_numbers)+' PNs','—']);
  rowsSplit.push(['<b>N-series truck, total</b>',eur(totExcl),'100%',
    (nsPrev>0?'<span class="'+cls(totExcl/nsPrev-1)+'">'+signpct(totExcl/nsPrev-1)+'</span>'
             :'n/a'),'exclusive rows above','—','—','—','—']);
  htmlTable('t_bandsplit',
    ['N-series line','Billed EUR '+C.spelled[per],'Share of the N-series',
     'Change vs '+C.spelled[wasp],
     'Fits this band only','Also fits another band','% of the band that is shared',
     'PNs fits-only','PNs shared'],
    rowsSplit,['','n','n','n','n','n','n','n','n']);
  document.getElementById('t_bandsplit').insertAdjacentHTML('afterbegin',
    '<h3 style="font-size:15px">Exclusive and shared, this period</h3>');
  document.getElementById('n_bandsplit').innerHTML=
    'This is the table that decides whether a band can carry a trend. A band\'s euro is its '
    +'fits-only part plus the part it shares with other bands. <b>The shared part is counted in '
    +'every band it fits</b>, so a percentage change on it belongs to the set of bands, not to one '
    +'band. The last three rows are mutually exclusive and add up to the N-series truck total; the '
    +'three band rows above them do not, by construction. Where a band is almost entirely shared '
    +'the page says so on the band instead of drawing a trend the data does not support.';
  window.__zoneAgg=Z;
}
function nseriesFleetTotal(){
  return fleetSum(0)+fleetSum(1);
}

function familyFleet(key){  if(key==='no_vehicle_reference'||key==='shared_across_families') return 0;
  var map={n_series_truck:'n_series',heavy_truck:'heavy',light_vehicle:'light'};
  var mk=chosen(), t=0;
  mk.forEach(function(m){ t+=((D.fleet[m]||{})[map[key]]||0); });
  return t;
}

function renderDrill(A,latest){
  var C=D.clocks[clock];
  var drFam=famFilter();
  /* Inside a tonnage band of the N-series, the next level down is cut from the band's own part
     numbers rather than the whole family's. Declared here because both levels below read it. */
  var bandKey=null, bandIsShared=false;
  if(drFam==='n_series_truck' && drillBand){
    if(drillBand==='__shared_bands__'){ bandKey='n_shared_bands'; bandIsShared=true; }
    else if(drillBand==='__unresolved__'){ bandKey='n_series_unresolved'; }
    else { bandKey=BAND_ZONE_SINGLE[drillBand]; }
  }
  var zc=bandKey?zoneCatAgg(A):null;
  var zcx=bandKey?zIndex(bandKey):-1;
  var bc=document.getElementById('bread');
  var parts=['<a data-nav="root">'+(drFam?'All vehicle types':'All vehicle types')+'</a>'];
  if(drFam) parts.push('<a data-nav="fam">'+FAMLAB[drFam]+'</a>');
  if(drillBand) parts.push('<a data-nav="band">'+BANDLAB[drillBand]+'</a>');
  if(drillCat) parts.push('<span>'+CATLAB[drillCat]+'</span>');
  bc.innerHTML='<b>Level:</b> '+parts.join(' &rsaquo; ')
    +' <span class="small">— click a bar to go deeper, or a level name to come back up</span>';
  bc.querySelectorAll('a').forEach(function(a){
    a.addEventListener('click',function(){
      if(a.getAttribute('data-nav')==='root'){selFam='all'; drillCat=null; drillBand=null;}
      else if(a.getAttribute('data-nav')==='band'){drillCat=null; drillBand=null;}
      else {drillCat=null;}
      render();});});

  /* ── inside the N-series only: the band, then the service families inside that band.
     The band rows overlap, so this level says which of its lines may be added and which may not. */
  if(drFam==='n_series_truck' && !drillBand){
    var Z=zoneAgg(A);
    var zOrder=BANDS.reduce(function(acc,b){
      acc.push(BAND_ZONE_SINGLE[b]); acc.push(BAND_ZONE_ALSO[b]); return acc;},[])
      .concat(['n_shared_bands','n_series_unresolved']);
    var rowsZ=zOrder.map(function(zid){ return zRow(Z,zid,latest); });
    var box0=document.getElementById('box_drill');
    box0.style.height=Math.max(320,60+rowsZ.length*34)+'px';
    mk('c_drill',{type:'bar',
      data:{labels:rowsZ.map(function(r){return r.short;}),datasets:[
        {label:C.spelled[String(latest)],data:rowsZ.map(function(r){return r.eur;}),
         backgroundColor:rowsZ.map(function(r){return r.color;}),borderRadius:3},
        {label:C.spelled[String(latest-1)],data:rowsZ.map(function(r){return r.eurPrev||0;}),
         backgroundColor:'#d9d3c7',borderRadius:3}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
        plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{afterBody:function(items){
              var r=rowsZ[items[0].dataIndex];
              return [r.hasPrev?signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units'
                                :'no billing a year earlier, so no percentage is shown',
                eur(r.eur)+' on '+num(r.units)+' units this period',
                'against '+eur(r.eurPrev||0)+' on '+num(r.unitsPrev||0)+' units a year earlier',
                r.membership==='also_fits_band'
                  ? 'OVERLAPS: this euro is also inside at least one band above it'
                  : 'Exclusive: this euro belongs to this line alone'];}}}},
        scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
                y:{grid:{display:false}}}}});
    var dz=charts['c_drill'];
    dz.options.onClick=function(evt,els){
      if(!els.length) return;
      var zid=rowsZ[els[0].index].zid;
      if(BANDS.indexOf(ZONE[zid].band)>=0){ drillBand=ZONE[zid].band; }
      else if(zid==='n_shared_bands'){ drillBand='__shared_bands__'; }
      else { drillBand='__unresolved__'; }
      drillCat=null; render(); };
    dz.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
    dz.update();
    document.getElementById('k_drill').innerHTML=
      '<span><i style="background:'+NAVY+'"></i>'+C.spelled[String(latest)]+'</span>'
      +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
      +'<span><i style="background:#8a6b2f"></i>shared across bands, counted once</span>'
      +'<span><i style="background:#b9ae9d"></i>weight not stated by the sources</span>';
    var exclusive=BANDS.reduce(function(s,b){return s+zRow(Z,BAND_ZONE_SINGLE[b],latest).eur;},0)
      +zRow(Z,'n_shared_bands',latest).eur+zRow(Z,'n_series_unresolved',latest).eur;
    document.getElementById('n_drill').innerHTML=
      '<b>You are inside the N-series truck</b>, so this level is its weight bands. '
      +'The six bars at the top are the three "fits this weight only" lines — exclusive, because '
      +'those part numbers fit one band — and the three "also fits another band" lines, tagged in '
      +'purple, whose euro sits inside more than one band and therefore must not be added together. '
      +'The "shared, once" bar is the whole shared set counted a single time, with the "not stated" '
      +'bar beside it. Those five groups — three fits-only, the shared set once, and the series the '
      +'sources leave open — add up to the N-series total of '+eur(exclusive)+' this period. '
      +'Click a bar to open the part numbers inside it.';
    document.getElementById('k_drill').innerHTML+=
      '<span class="small">the last three lines add up to the N-series total; the band bars above '
      +'them overlap.</span>';
    document.getElementById('t_pn').innerHTML='';
    return;
  }

  var box=document.getElementById('box_drill');
  var tpn=document.getElementById('t_pn');
  document.getElementById('k_drill').innerHTML='';
  document.getElementById('n_drill').innerHTML='';

  /* level 1 -> level 2: the service families inside the vehicle type in force (or all of them).
     Inside a tonnage band of the N-series, the same level is cut from the band's own part numbers,
     so the euro on it is the band's own euro and not the whole family's. */
  if(!drillCat){
    var keys=D.cats.map(function(c){return c.key;});
    var rows=keys.map(function(ck){
      var eurNow=0, unitsNow=0, eurWas=0, unitsWas=0, anyone=false;
      if(bandKey){
        var per=zc[zcx]||{}, ci=keys.indexOf(ck);
        var znow=per[ci]?per[ci][latest]:null, zwas=per[ci]?per[ci][latest-1]:null;
        if(znow){eurNow=znow.eur; unitsNow=znow.units; anyone=true;}
        if(zwas){eurWas=zwas.eur; unitsWas=zwas.units; anyone=true;}
      } else {
        FAMK.forEach(function(fk){
          if(drFam && fk!==drFam) return;
          var o=A.byFamCat[fk+'|'+ck]||{};
          var now=o[latest], was=o[latest-1];
          if(now){eurNow+=now.eur; unitsNow+=now.units; anyone=true;}
          if(was){eurWas+=was.eur; unitsWas+=was.units; anyone=true;}
        });
      }
      if(!anyone) return null;
      var p=eurWas>0?(eurNow/eurWas-1):null;
      return {key:ck,label:CATLAB[ck],eur:eurNow,units:unitsNow,eurPrev:eurWas,
              unitsPrev:unitsWas,eurPct:p,unitsPct:unitsWas>0?(unitsNow/unitsWas-1):null,
              hasPrev:eurWas>0};
    }).filter(function(x){return x&&x.eur>0;}).sort(function(a,b){return b.eur-a.eur;});

    box.style.height=Math.max(300,60+rows.length*30)+'px';
    mk('c_drill',{type:'bar',
      data:{labels:rows.map(function(r){return r.label;}),datasets:[
        {label:C.spelled[String(latest)],data:rows.map(function(r){return r.eur;}),
         backgroundColor:rows.map(function(r){return drFam?FAMCOL[drFam]:TERRA;}),borderRadius:3},
        {label:C.spelled[String(latest-1)],data:rows.map(function(r){return r.eurPrev||0;}),
         backgroundColor:'#d9d3c7',borderRadius:3}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
        plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{afterBody:function(items){
              var r=rows[items[0].dataIndex];
              return [r.hasPrev?signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units'
                                :'no billing a year earlier, so no percentage is shown',
                eur(r.eur)+' on '+num(r.units)+' units this period',
                'against '+eur(r.eurPrev||0)+' on '+num(r.unitsPrev||0)+' units a year earlier',
                'Fleet base: '+num(drFam?familyFleet(drFam):0)+' vehicles in service'];}}}},
        scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
                y:{grid:{display:false}}}}});
    var d=charts['c_drill'];
    d.options.onClick=function(evt,els){ if(!els.length) return;
      drillCat=rows[els[0].index].key; render(); };
    d.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
    d.update();
    document.getElementById('k_drill').innerHTML=
      '<span><i style="background:'+(drFam?FAMCOL[drFam]:TERRA)+'"></i>'+C.spelled[String(latest)]+'</span>'
      +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
      +'<span class="small">'+(bandKey
        ? 'service families inside '+(bandIsShared?'the parts shared across bands':BANDLAB[drillBand])
          +', ranked by the current period'
        : (drFam
          ? 'service families inside '+FAMLAB[drFam]+', ranked by the current period'
          : 'all service families for this selection, ranked by the current period — pick a vehicle '
            +'type above to narrow it, or click a bar to open the part numbers inside it'))+'</span>';
    var nDrill='Each bar is billed euro in one service family. Both bars are twelve-month periods, '
      +'so the difference between them is the move. ';
    nDrill += bandKey
      ? 'Only part numbers that fit '+(bandIsShared?'more than one band':BANDLAB[drillBand])
        +' are counted at this level.'
      : drFam ? 'Only parts that fit '+FAMLAB[drFam]+' are counted at this level.'
      : 'Pooled part numbers are included here, because this level sums the whole selection. Click a '
        +'bar to see the part numbers inside it with the vehicle type each one fits.';
    document.getElementById('n_drill').innerHTML=nDrill;
    tpn.innerHTML='';
    return;
  }

  /* level 2 -> level 3: the part numbers inside the clicked service family */
  var pnBilling=pnAgg(A);
  var fam=drFam;
  var detail=[];
  D.pns.forEach(function(p,i){
    if(p.cat!==drillCat) return;
    if(fam && p.fam!==fam) return;
    /* inside a tonnage band, only the part numbers that fit that band belong on this level */
    if(bandKey){
      var fits=bandIsShared?p.zfits.indexOf('n_shared_bands')>=0
                           :p.zfits.indexOf(bandKey)>=0;
      if(!fits) return;
    }
    var o=pnBilling[i]; if(!o) return;
    var now=o[latest], was=o[latest-1];
    if(!now && !was) return;
    detail.push({pn:p.pn,cat:p.cat,fam:p.fam,fits:p.fits,conf:p.conf,model:p.model,src:p.src,
      zfits:p.zfits,zstatus:p.zstatus,zseries:p.zseries,zreg:p.zreg,
      eur:now?now.eur:0,units:now?now.units:0,
      eurPrev:was?was.eur:null,unitsPrev:was?was.units:null,
      eurPct:(was&&was.eur>0&&now)?(now.eur/was.eur-1):null,
      unitsPct:(was&&was.units>0&&now)?(now.units/was.units-1):null});
  });
  detail.sort(function(a,b){return b.eur-a.eur;});
  var shown=detail.slice(0,60);
  var sum=detail.reduce(function(s,r){return s+r.eur;},0);
  var sumPrev=detail.reduce(function(s,r){return s+(r.eurPrev||0);},0);

  var rowsBar=shown.slice(0,14);
  box.style.height=Math.max(280,60+rowsBar.length*30)+'px';
  mk('c_drill',{type:'bar',
    data:{labels:rowsBar.map(function(r){return r.pn;}),datasets:[
      {label:C.spelled[String(latest)],data:rowsBar.map(function(r){return r.eur;}),backgroundColor:NAVY,borderRadius:3},
      {label:C.spelled[String(latest-1)],data:rowsBar.map(function(r){return r.eurPrev||0;}),backgroundColor:'#d9d3c7',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{afterBody:function(items){
            var r=rowsBar[items[0].dataIndex];
            return [r.fits.length>1?'fits more than one vehicle type: '+r.fits.map(function(k){return FAMLAB[k];}).join(', ')
                                   :'fits '+FAMLAB[r.fam],
              'units: '+num(r.units)+' this period against '+(r.unitsPrev===null?'n/a':num(r.unitsPrev)),
              r.eurPct===null?'no billing a year earlier':signpct(r.eurPct)+' in euro against the year before',
              'confidence: '+r.conf];}}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  var d2=charts['c_drill'];
  d2.options.onClick=function(evt,els){ if(!els.length) return;
    var r=rowsBar[els[0].index]; jumpToPn(r.pn); };
  d2.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
  d2.update();

  document.getElementById('k_drill').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>'+C.spelled[String(latest)]+'</span>'
    +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
    +'<span class="small">the highest-value part numbers in '
    +CATLAB[drillCat]+(fam?' for '+FAMLAB[fam]:'')+'; the table below holds all '
    +detail.length+'</span>';
  document.getElementById('n_drill').innerHTML='<b>'+detail.length+' part numbers</b> in this service '
    +'family'+(fam?' for '+FAMLAB[fam]:'')+', '+eur(sum)+' this period against '+eur(sumPrev)
    +' a year earlier ('+(sumPrev>0?signpct(sum/sumPrev-1):'n/a')+'). '
    +(familyFleet(fam)?'Fleet base: '+num(familyFleet(fam))+' vehicles in service.':'');

  var cols=[['Part number',''],['Vehicle type it fits',''],['Weight band it fits',''],
    ['Fits',''],
    [C.spelled[String(latest)]+' EUR','n'],[C.spelled[String(latest-1)]+' EUR','n'],
    ['Change EUR','n'],[C.spelled[String(latest)]+' units','n'],
    [C.spelled[String(latest-1)]+' units','n'],['Change units','n'],['Confidence','']];
  tpn.innerHTML='<table><thead><tr>'+cols.map(function(c){
      return '<th class="'+c[1]+'">'+c[0]+'</th>';}).join('')+'</tr></thead><tbody>'
    +shown.map(function(r){
      return '<tr data-pn="'+r.pn+'"><td><b>'+r.pn+'</b></td>'
        +'<td>'+(r.fits.length>1?r.fits.map(function(k){return FAMLAB[k];}).join(' + ')
                             :FAMLAB[r.fam])+'</td>'
        +'<td class="small">'+(r.zfits&&r.zfits.length
            ? r.zfits.map(function(z){return ZSHORT[z];}).join(' + ')
            :(r.zstatus==='series_unresolved'?'series not resolved'
              :(r.zstatus==='no_series_found'?'no series on the part number'
                :(r.zseries||'not in this lane'))))+'</td>'
        +'<td class="small">'+(r.model||'no vehicle string')+'</td>'
        +'<td class="n">'+eur(r.eur)+'</td>'
        +'<td class="n">'+(r.eurPrev===null?'n/a':eur(r.eurPrev))+'</td>'
        +'<td class="n '+cls(r.eurPct)+'">'+signpct(r.eurPct)+'</td>'
        +'<td class="n">'+num(r.units)+'</td>'
        +'<td class="n">'+(r.unitsPrev===null?'n/a':num(r.unitsPrev))+'</td>'
        +'<td class="n '+cls(r.unitsPct)+'">'+signpct(r.unitsPct)+'</td>'
        +'<td>'+r.conf+'</td></tr>';}).join('')
    +'</tbody></table>'
    +(detail.length>shown.length?'<p class="small" style="margin-top:8px">Showing the top '
      +shown.length+' of '+detail.length+' by the current period. '
      :'<p class="small" style="margin-top:8px">Every part number in this service family is listed. ')
    +(bandKey
      ? '<b>Filtered to the weight band '+(bandIsShared?'shared across bands':BANDLAB[drillBand])
        +'.</b> The "weight band it fits" column names every band each of these part numbers fits. '
        +'A part that shows more than one band sits inside each of those bands, which is why the '
        +'band bars overlap. '
      : (fam==='shared_across_families'
        ? '<b>These are the pooled part numbers.</b> Each one fits more than one vehicle type, so its '
          +'euro stays here rather than being spread across the types it fits. The column "Fits" names '
          +'the types. '
        : fam
          ? '<b>These part numbers fit '+FAMLAB[fam]+' and nothing else</b>, so each one\'s euro '
            +'belongs to that type alone. '
          : 'The table mixes pooled part numbers with single-type ones — pick a vehicle type above to '
            +'separate them. '))
    +'Fleet base for this level: '
    +(bandKey
      ? (bandFleet(drillBand&&BANDS.indexOf(drillBand)>=0?drillBand:null).n===null
          ? 'no source splits this band out of the N-series fleet'
          : num(bandFleet(drillBand).n)+' vehicles in service ('+bandFleet(drillBand).label+')')
      : num(fam?familyFleet(fam):0)+' vehicles in service'
        +(fam?'' : ' (no single fleet applies to the pooled rows)'))
    +'.</p>';

  /* a part number you clicked in the chart scrolls into view in the table */
  function jumpToPn(pn){
    var el=tpn.querySelector('tr[data-pn="'+pn+'"]');
    if(el){ el.scrollIntoView({block:'center',behavior:'smooth'});
      el.classList.add('sel'); setTimeout(function(){el.classList.remove('sel');},2200); }
  }
  tpn.querySelectorAll('tr[data-pn]').forEach(function(tr){
    tr.addEventListener('click',function(){ tr.classList.add('sel');
      setTimeout(function(){tr.classList.remove('sel');},1600); });});
}

/* The before/after section reads the shipped page's own payload. It is the honest answer to "what
   did the bug change", and it is the one chart on this page that is not about the current state. */
function renderBefore(A,latest){
  var B=D.before;
  if(!B||!B.available){
    document.getElementById('n_before').innerHTML='The shipped page could not be read, so no '
      +'before/after comparison can be shown. '+(B&&B.why?B.why:'')+'';
    return;
  }
  var per=String(latest);
  var keys=D.families.map(function(f){return f.key;});
  /* This section is a statement about the rebuild, not about the reader's selection, so it is always
     the whole network on both sides. The shipped page reported the network, and comparing that
     against one selected market would read as a collapse that did not happen. D.trend carries the
     network totals cut from the current data on the same 18 markets and the same service-part scope
     the shipped page used. */
  var nowV=keys.map(function(k){ return ((D.trend.CY[k]||{}).eur||{})[per]||0; });
  var nowU=keys.map(function(k){ return ((D.trend.CY[k]||{}).units||{})[per]||0; });
  var wasV=keys.map(function(k){ return (B.eur[k]||{})[per]||0; });
  var wasU=keys.map(function(k){ return (B.units[k]||{})[per]||0; });
  mk('c_before',{type:'bar',
    data:{labels:keys.map(function(k){return FAMLAB[k];}),datasets:[
      {label:'As shipped',data:wasV,backgroundColor:'#d9d3c7',borderRadius:3},
      {label:'Corrected',data:nowV,backgroundColor:keys.map(function(k){return FAMCOL[k];}),borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{afterBody:function(items){
            var i=items[0].dataIndex;
            return ['as shipped: '+eur(wasV[i])+' on '+num(wasU[i])+' units',
              'corrected: '+eur(nowV[i])+' on '+num(nowU[i])+' units',
              'move: '+(nowV[i]-wasV[i]>=0?'+':'')+eur(nowV[i]-wasV[i]),
              'Read the euro. A percentage on the heavy line is large because the fleet is small.'];}}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  document.getElementById('k_before').innerHTML=
    '<span><i style="background:#d9d3c7"></i>as shipped ('+B.source+')</span>'
    +'<span><i style="background:'+NAVY+'"></i>corrected</span>'
    +'<span class="small">'+D.clocks.CY.spelled[per]+', service parts only, the whole network — the '
    +'same scope the shipped page reported</span>';
  var hI=keys.indexOf('heavy_truck');
  function sumRows(arr){ return arr.reduce(function(s,v){return s+v;},0); }
  var namedIdx=D.namedFamilies.map(function(k){return keys.indexOf(k);});
  var namedNow=sumRows(namedIdx.map(function(i){return nowV[i];}));
  var namedWas=sumRows(namedIdx.map(function(i){return wasV[i];}));
  var namedNowU=sumRows(namedIdx.map(function(i){return nowU[i];}));
  var namedWasU=sumRows(namedIdx.map(function(i){return wasU[i];}));
  document.getElementById('n_before').innerHTML='The grey bars are the numbers the shipped page '
    +'carried; the coloured bars are the same twelve months and the same network after the decode '
    +'universe was fixed. Across the three named vehicle types the network went from '
    +eur(namedWas)+' ('+num(namedWasU)+' units) to '+eur(namedNow)+' ('+num(namedNowU)+' units); '
    +'heavy truck alone went from '+eur(wasV[hI])+' to '+eur(nowV[hI])+'. '
    +'Nothing was created. Every euro already existed in the billing and had a home in the '
    +'cross-reference; it was dropped between two build steps, which is why it appeared on neither.';
  htmlTable('t_before',
    ['Vehicle type','As shipped EUR','As shipped units','Corrected EUR','Corrected units',
     'Move EUR','Move %'],
    keys.map(function(k,i){
      var mv=nowV[i]-wasV[i];
      return ['<b>'+FAMLAB[k]+'</b>','<span class="small">'+eur(wasV[i])+'</span>',
        '<span class="small">'+num(wasU[i])+'</span>',eur(nowV[i]),num(nowU[i]),
        '<span class="'+cls(wasV[i]>0?mv/wasV[i]:null)+'">'+(mv>=0?'+':'')+eur(mv)+'</span>',
        wasV[i]>0?'<span class="'+cls(mv/wasV[i])+'">'+signpct(mv/wasV[i])+'</span>':'<span class="small">new</span>'];
    }),
    ['','n','n','n','n','n','n']);
}

function renderMix(A,latest){
  var rows=D.families.map(function(f){
    var o=(A.byFam[f.key]||{})[latest];
    return {key:f.key,label:f.label,color:f.color,v:o?o.eur:0,
            units:o?o.units:0};
  }).filter(function(r){return r.v>0;});
  var tot=rows.reduce(function(s,r){return s+r.v;},0);
  if(!rows.length){
    mk('c_mix',{type:'doughnut',data:{labels:['nothing billed in this period'],
      datasets:[{data:[1],backgroundColor:['#ddd7cb'],borderWidth:0}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
        plugins:{legend:{display:false},tooltip:{enabled:false}}}});
    document.getElementById('k_mix').innerHTML='<span>no billing in this period for this selection</span>';
    return;
  }
  mk('c_mix',{type:'doughnut',
    data:{labels:rows.map(function(r){return r.label;}),datasets:[{data:rows.map(function(r){return r.v;}),
      backgroundColor:rows.map(function(r){return r.color;}),borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
      plugins:{legend:{display:false},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){
            var r=rows[c.dataIndex];
            return [c.label+': '+eur(r.v)+' ('+pct(r.v/tot)+' of the selection)',
              num(r.units)+' units',
              (D.namedFamilies.indexOf(r.key)>=0
                ? 'Fleet: '+num(familyFleet(r.key))+' vehicles in service'
                : 'Pooled or with no vehicle named — no single fleet applies')];}}}}}});
  document.getElementById('k_mix').innerHTML=rows.map(function(r){
    return '<span><i style="background:'+r.color+'"></i>'+r.label+' — '+pct(r.v/tot)
      +' ('+eur(r.v)+')'
      +(D.namedFamilies.indexOf(r.key)>=0?' on '+num(familyFleet(r.key))+' vehicles in service'
        :' — pooled across types, no single fleet applies')
      +'</span>';}).join('');
}

function renderFleet(A){
  var fl=[['n_series_truck','n_series'],['heavy_truck','heavy'],['light_vehicle','light']]
    .map(function(x){
      var t=0; A.markets.forEach(function(m){ t+=((D.fleet[m]||{})[x[1]]||0); });
      return {key:x[0],label:FAMLAB[x[0]],v:t,color:FAMCOL[x[0]]};})
    .filter(function(r){return r.v>0;});
  var tot=fl.reduce(function(s,r){return s+r.v;},0);
  mk('c_fleet',{type:'doughnut',
    data:{labels:fl.map(function(r){return r.label;}),datasets:[{data:fl.map(function(r){return r.v;}),
      backgroundColor:fl.map(function(r){return r.color;}),borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
      plugins:{legend:{display:false},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){ var r=fl[c.dataIndex];
            return [num(r.v)+' vehicles ('+pct(r.v/tot)+' of the fleet)',
              'Parts billed on this type: '+eurm(((A.byFam[r.key]||{})[D.clocks[clock].latestComplete]||{}).eur)];}}}}}});
  document.getElementById('k_fleet').innerHTML=fl.map(function(r){
    return '<span><i style="background:'+r.color+'"></i>'+r.label+' — '+num(r.v)
      +', billed '+eurm(((A.byFam[r.key]||{})[D.clocks[clock].latestComplete]||{}).eur)
      +' = '+eur(((A.byFam[r.key]||{})[D.clocks[clock].latestComplete]||{}).eur||0)
      +' over '+num(r.v)+' vehicles</span>';}).join('');
  document.getElementById('n_fleet').innerHTML='The fleet is the denominator every euro above is '
    +'measured against, and it is a 2025 estimate used for every year. Pooled part numbers fit more '
    +'than one type, so they are not assigned to one slice here.';
}

function renderFamTable(A,latest){
  var C=D.clocks[clock];
  var months=C.months[String(latest)];
  var rows=D.families.map(function(f){
    var pr=pairFor(A.byFam[f.key]||{},latest);
    return {key:f.key,label:f.label,
      fleet:(D.namedFamilies.indexOf(f.key)>=0?familyFleet(f.key):null),
      eur:pr?pr.eur:0, units:pr?pr.units:0, eurPrev:pr?pr.eurPrev:null,
      unitsPrev:pr?pr.unitsPrev:null, eurPct:pr?pr.eurPct:null, unitsPct:pr?pr.unitsPct:null,
      fits: f.key==='shared_across_families'
        ? (A.byFam[f.key]?'pooled across types':'') : (f.key==='no_vehicle_reference'?'no vehicle named':'')};
  });
  var tot=rows.reduce(function(s,r){return s+r.eur;},0);
  htmlTable('t_fam',
    ['Vehicle type','Vehicles in service','EUR per vehicle, '+C.short+latest,
     'Billed EUR '+C.short+latest,'Billed EUR '+C.short+(latest-1),'Change EUR','Change %',
     'Units '+C.short+latest,'Units '+C.short+(latest-1),'Change units','Share'],
    rows.map(function(r){
      var per=(r.fleet&&r.fleet>0)?(r.eur/r.fleet):null;
      return ['<b>'+r.label+'</b>'+(r.fits?' <span class="small">('+r.fits+')</span>':''),
        r.fleet===null?'<span class="small">pooled — no single fleet</span>':num(r.fleet),
        per===null?'n/a':eur(per),
        eur(r.eur), r.eurPrev===null?'n/a':eur(r.eurPrev),
        r.eurPrev===null?'n/a':'<span class="'+cls(r.eurPct)+'">'+eur(r.eur-(r.eurPrev||0))+'</span>',
        r.eurPrev===null?'n/a':'<span class="'+cls(r.eurPct)+'">'+signpct(r.eurPct)+'</span>',
        num(r.units), r.unitsPrev===null?'n/a':num(r.unitsPrev),
        r.unitsPrev===null?'n/a':'<span class="'+cls(r.unitsPct)+'">'+signpct(r.unitsPct)+'</span>',
        tot>0?pct(r.eur/tot):'n/a'];
    }),
    ['','n','n','n','n','n','n','n','n','n','n']);
  var ft=document.getElementById('t_fam');
  ft.insertAdjacentHTML('afterbegin','<h3 style="font-size:15px">This period against the same period '
    +'a year earlier, with the fleet beside every euro</h3>'
    +'<p class="small">'+C.spelled[String(latest)]+' holds '+months+' month'
    +(months===1?'':'s')+' of billing. '
    +'EUR per vehicle is the billed euro divided by the vehicles in service for that type, which is '
    +'the only form in which these numbers are comparable between markets of different size.</p>');
}

function renderLimits(A,latest){
  var C=D.clocks[clock];
  var lim=[];
  lim.push('<b>One year is not a full year.</b> '
    +C.spelled[String(latest)]+' is a complete twelve-month period. A period holding fewer months is '
    +'shown on the small multiples but never compared as though it were a full year; the number of '
    +'months is printed on its key.');
  lim.push('<b>'+eur(D.totals.serviceBook2025-D.totals.placeable2025)+' of the 2025 service book '
    +'(2025 total '+eur(D.totals.serviceBook2025)+') is not placed in a single vehicle type.</b> '
    +eur(D.totals.serviceBook2025-D.totals.placeable2025)+' sits in the pooled value where a part '
    +'fits more than one type, and in "no vehicle reference" where no source names a vehicle. It is '
    +'not missing and it is not spread — both are reported, and the pooled part numbers are listed '
    +'when you open that bar.');
  var hs=D.familyStats.heavy_truck;
  lim.push('<b>Heavy truck rests on a small fleet.</b> '
    +'Heavy truck holds '+num(hs.pns)+' part numbers billing '+eur(hs.eur2025)+' in 2025 on '
    +num(hs.units2025)+' units, with a separate fleet base of '+num(hs.fleet)+' vehicles across the '
    +'whole network. Read a percentage there with the euro beside it.');
  lim.push('<b>A service type can look empty for the heavy truck family even when it is not.</b> '
    +'A part number is placed in a type only where a source names a vehicle for it, and a part that '
    +'fits more than one type is pooled rather than split. The euro on a heavy-truck bar is '
    +'therefore the part numbers that name the heavy truck and nothing else; the rest of that '
    +'service type sits in the pooled value beside it. The heavy-truck family itself holds 164 part '
    +'numbers billing EUR 175K in 2025, so an empty bar is a placement limit, not zero demand.');
  lim.push('<b>A 3.5 t versus 7.5 t split inside the N-series is not attempted.</b> 50 of the 120 '
    +'model codes in the weight table are unresolved, and the unresolved ones include the codes that '
    +'separate the two, so the N-series is reported as one type.');
  lim.push('<b>Two service-interval schedules run through this network.</b> ITUK runs the schedule '
    +'agreed for that market and every other market runs the internal one. They are shown side by '
    +'side and are never averaged, because they answer different questions about the same fleet.');
  lim.push('<b>Fleet is a 2025 estimate used for every year.</b> Implied demand is therefore flat '
    +'over time by construction; only the billed side moves.');
  (D.notAttempted||[]).slice(0,3).forEach(function(s){ lim.push('<b>Not attempted:</b> '+s); });
  htmlTable('t_limits',['What cannot be shown, and why'],lim.map(function(s){return [s];}),['']);
}

function htmlTable(id,heads,rows,aligns){
  document.getElementById(id).innerHTML='<table><thead><tr>'
    +heads.map(function(h,i){return '<th class="'+(aligns[i]||'')+'">'+h+'</th>';}).join('')
    +'</tr></thead><tbody>'+rows.map(function(r){
      return '<tr>'+r.map(function(c,i){
        return '<td class="'+(aligns[i]||'')+'">'+c+'</td>';}).join('')+'</tr>';}).join('')
    +'</tbody></table>';
}

/* ── controls ───────────────────────────────────────────────────────────────────────────── */
custSel.addEventListener('change',function(){
  selCust={};
  Array.prototype.slice.call(custSel.selectedOptions).forEach(function(o){ selCust[o.value]=true; });
  if(!chosen().length){ selCust[D.markets[0]]=true; }
  render();});
famSel.addEventListener('change',function(){ selFam=famSel.value; drillCat=null; drillBand=null; render();});
clkSel.addEventListener('change',function(){ clock=clkSel.value; render();});
document.getElementById('btnAll').addEventListener('click',function(){
  selCust={}; D.markets.forEach(function(m){selCust[m]=true;}); syncCust(); render();});
document.getElementById('btnNone').addEventListener('click',function(){
  selCust={}; selCust[D.markets[0]]=true; syncCust(); render();});
document.getElementById('btnItuk').addEventListener('click',function(){
  selCust={ITUK:true}; if(D.markets.indexOf('ITUK')<0){selCust={}; selCust[D.markets[0]]=true;}
  syncCust(); render();});
function syncCust(){
  Array.prototype.slice.call(custSel.options).forEach(function(o){ o.selected=!!selCust[o.value]; });}

document.getElementById('foot').innerHTML='<b>Sources, all read at build time, snapshot '
  +D.snapshot+':</b> the published service-part capture model; the service-part dimension and its '
  +'capture supplement; the vehicle-family banding table, which reads the EPC decode and the '
  +'genuine/aftermarket cross-reference together; the billing; the fleet split by vehicle class; and '
  +'the per-market interval schedule. '
  +'<b>Reconciliation:</b> every euro on this page is the published service-part book for the '
  +'selection, and the build refuses to write if the 2025 figure does not tie to it. '
  +'<b>Vehicle type resolution:</b> '+D.resolution.resolved_single_family+' part numbers resolve to '
  +'one vehicle type, '+D.resolution.pooled_shared+' fit more than one and are pooled, and '
  +D.resolution.no_vehicle_reference+' have no vehicle named by either source — '
  +D.resolution.both_sources_speak.of_which_they_disagree+' disagreements between the two sources.';

syncCust();
render();

/* QA hook. Cursor-side only: it lets the ship gate drive the same click path a reader's mouse takes
   (Chart.js routes a canvas click through the chart's onClick), so drill-through is verified by
   walking it, not by reading the code. It writes nothing. */
window.__deepTest={
  state:function(){ return {selCust:Object.keys(selCust), selFam:selFam, clock:clock,
    drillFam:famFilter(), drillCat:drillCat, drillBand:drillBand,
    bread:document.getElementById('bread').textContent.replace(/\s+/g,' ').trim(),
    pnRows:document.querySelectorAll('#t_pn tbody tr').length,
    drillInk:window.__deepTest.ink('c_drill'),
    bandInk:window.__deepTest.ink('c_band'),
    funnelInk:window.__deepTest.ink('c_funnel'),
    drillLabels:window.__deepTest.labels('c_drill'),
    bandLabels:window.__deepTest.labels('c_band'),
    bandCards:document.querySelectorAll('#band_cards .bandcard').length,
    bandSplitRows:document.querySelectorAll('#t_bandsplit tbody tr').length,
    bandEvRows:document.querySelectorAll('#t_bandev tbody tr').length,
    canvasIds:Array.prototype.map.call(document.querySelectorAll('canvas'),function(c){return c.id;})};},
  clickBar:function(id,index){
    var ch=charts[id]; if(!ch||!ch.options.onClick) return false;
    ch.options.onClick({}, [{index:index, datasetIndex:0, element:null}]);
    return true;},
  /* the funnel's bar order changes when a vehicle filter is on, so the test reads the labels back */
  labels:function(id){ var ch=charts[id];
    return ch? (ch.data.labels||[]).map(function(l){return String(l);}) : null;},
  set:function(o){
    if(o.cust){ selCust={}; o.cust.forEach(function(m){selCust[m]=true;}); syncCust(); }
    if(o.clock){ clock=o.clock; }
    if(o.fam){ selFam=o.fam; drillCat=null; drillBand=null; }
    if(o.band!==undefined){ drillBand=o.band; drillCat=null; }
    if(o.reset){ drillCat=null; drillBand=null; }
    render();
    return window.__deepTest.state();},
  chooseBand:function(band){ selFam='n_series_truck'; drillBand=band; drillCat=null;
    if(famSel) famSel.value='n_series_truck';
    render(); return window.__deepTest.state(); },
  bandTotals:function(){
    return window.__deepTest.zonePanel(); },
  zonePanel:function(){
    var A=agg(); var Z=zoneAgg(A); var C=D.clocks[clock]; var latest=C.latestComplete;
    var o={clock:clock, latest:latest, markets:Object.keys(selCust), zones:{}};
    D.zoneIds.forEach(function(zid){ var r=zRow(Z,zid,latest);
      o.zones[zid]={eur:r.eur, units:r.units, eurPrev:r.eurPrev, unitsPrev:r.unitsPrev,
                    eurPct:r.eurPct, unitsPct:r.unitsPct, membership:r.membership,
                    sums:r.sums, band:r.band};});
    o.bands={};
    BANDS.forEach(function(b){ var t=bandTotal(Z,b,latest);
      o.bands[b]={eur:t.eur, units:t.units, eurPrev:t.eurPrev, unitsPrev:t.unitsPrev,
                  eurPct:t.eurPct, unitsPct:t.unitsPct, singleEur:t.singleEur,
                  sharedEur:t.sharedEur,
                  sharedPct:t.eur>0?(t.sharedEur/t.eur):0};});
    return o; },
  pooledIndex:function(){
    /* which bar of the drill chart is the pooled value, read from the live labels */
        var l=window.__deepTest.labels('c_drill')||[];
    for(var i=0;i<l.length;i++){
      if(String(l[i]).toLowerCase().indexOf('more than one family')>=0) return i; }
    return -1;},
  catLabels:function(){ return window.__deepTest.labels('c_drill');},
  ink:function(id){ var c=document.getElementById(id); if(!c) return null;
    var d=c.getContext('2d').getImageData(0,0,c.width,c.height).data, nw=0, s=0;
    for(var i=0;i<d.length;i+=4){ s++; if(d[i+3]>8 && !(d[i]>250&&d[i+1]>250&&d[i+2]>250)) nw++; }
    return {sampled:s, nonWhite:nw, pct:+(100*nw/s).toFixed(2)};},
  /* the pooled value as a separate vehicle-type option, so it can be walked to by name */
  choosePooled:function(){ selFam='shared_across_families'; drillCat=null; render(); }
};
}catch(err){
  var b=document.getElementById('jserr');
  if(b){ b.style.display='block';
    b.innerHTML='<div class="note red"><b>The page did not finish drawing.</b> A script error stopped '
      +'it. Detail: '+String(err && err.message ? err.message : err)+'</div>'; }
  var f=document.getElementById('foot');
  if(f) f.innerHTML='<b>Incomplete.</b> The page script failed: '
    +String(err && err.message ? err.message : err);
}
})();
</script>
</body></html>
"""
    return (template.replace("__CHARTJS__", chart_js)
            .replace("__PAYLOAD__", body)
            .replace("__SNAPSHOT__", SNAPSHOT))


if __name__ == "__main__":
    raise SystemExit(main())
