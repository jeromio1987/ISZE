#!/usr/bin/env python3
"""Build the family-evolution page: one compact page that drills to part numbers and shows every
move split into what actually caused it.

What this page is for
---------------------
A reader at any level should be able to answer, without arithmetic: did we do better or worse, and
was it the fleet, the price, or what we sold? A euro-to-euro bar cannot answer that, because three
things move underneath it - the number of vehicles, the price per part, and the basket of parts.
So every comparison here is:

  * per vehicle, on that period's own fleet, with the fleet count printed beside it;
  * like for like, same months on both sides, and refused when either period is incomplete;
  * split into volume / price / mix plus the fleet term, on the bar itself.

The split method is the one already in this workspace
(``prism/modules/lost_sales_build.py::build_price_layer``), including the rule that makes it real:
price is taken one level ABOVE the mix axis, otherwise ``volume + price`` equals the total by
construction and mix is identically zero. See ``decomp.py``.

Nothing here is apportioned. Part numbers that fit more than one band or family are pooled, marked,
and openable; they are never divided across the bands they fit.

Where the numbers come from
---------------------------
  * ``_deep_billing_cache.parquet`` - the only per-part-number billing read, produced through the
    project's own tagging path (``tag_pms_sales`` + the published exclusions). Every euro figure on
    the page is derived from it.
  * ``pms_capture_by_family.csv`` - the published family totals, used as the tie-out and as the
    fallback for panels this page cannot place at part-number grain.
  * ``nseries_tonnage_evolution.csv`` / ``epc_decode_nseries_banded.csv`` - the tonnage membership,
    which decides what is comparable at band level.
  * ``uio_by_market_type_year.csv`` - the fleet per market, type and year (actual / estimate /
    forecast). This is the per-period denominator.
  * ``uio_by_model_bucket.csv`` - the flat 2025E estimate, offered as the alternative denominator.

Usage
-----
    python 02_dashboards/sales/_build/build_pms_family_evolution_v2.py
    python 02_dashboards/sales/_build/build_pms_family_evolution_v2.py --refresh
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decomp import RESIDUAL_TOLERANCE_EUR, per_vehicle_terms, split_move, thin_base  # noqa: E402

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PDATA = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
OUT_DIR = ROOT / "02_dashboards" / "sales"
BUILD_DIR = OUT_DIR / "_build"
HISTORY = BUILD_DIR / "history"

OUT_HTML = OUT_DIR / "ISZE_PMS_Family_Evolution_v2.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_PMS_Family_Evolution_v2.cmd"
OLD_DEEP = OUT_DIR / "ISZE_PMS_Family_Evolution_Deep.html"
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
SNAPSHOT = "2026-09-19"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# ── the four named vehicle types, plus the two residual buckets ─────────────────────────────────
FAMILIES = [
    {"key": "n_series_truck", "label": "N-series truck", "short": "N-series",
     "note": "NLR through NQR - the light and medium truck range", "color": "#15233c"},
    {"key": "heavy_truck", "label": "Heavy truck (F-series and C&E)", "short": "Heavy truck",
     "note": "Forward F&G and the C&E range", "color": "#c0552d"},
    {"key": "light_vehicle", "label": "Light vehicle (D-Max pickup and SUV)", "short": "Light vehicle",
     "note": "pickup and SUV - where most of the fleet and most of the euro sits", "color": "#2f6b45"},
    {"key": "shared_across_families", "label": "Parts used across more than one family",
     "short": "Shared, pooled",
     "note": "pooled and never apportioned - open it to see the part numbers inside",
     "color": "#7a8ba6"},
    {"key": "unattributed", "label": "No vehicle reference found", "short": "No vehicle ref",
     "note": "no source on disk names a vehicle for these part numbers", "color": "#b9ae9d"},
]
FAM_KEYS = [f["key"] for f in FAMILIES]
FAM_BY_KEY = {f["key"]: f for f in FAMILIES}

# ── the tonnage level inside the N-series ────────────────────────────────────────────────────────
# The band keys are the ones both published files use, so the merge is a merge and not a guess.
# `shares_n_series_fleet` is the split of the N-series fleet that the market sources support; the
# per-market 3.5 t share comes from the workbook's own measured rate. No market's fleet is divided
# into a band the sources do not evidence.
BANDS = [
    {"key": "3.5t_N35", "short": "3.5t", "label": "3.5 t GVW (N35 Grafter)",
     "note": "NLR and NMR - the N35 Grafter", "color": "#15233c"},
    {"key": "5.5t_N50_N55", "short": "5.5t", "label": "5.5 t GVW (N50 / N55)",
     "note": "N50 and N55", "color": "#2f6b45"},
    {"key": "7.5t_N50_N62_N75", "short": "7.5t", "label": "7.5 t class (N50 / N62 / N75)",
     "note": "the heavier end of the N-series", "color": "#c0552d"},
    {"key": "shared_across_bands", "short": "fit several",
     "label": "Fits more than one band", "note": "counted once here, and shown again inside each "
     "band it fits - so band rows overlap and are never summed", "color": "#8a6b2f"},
    {"key": "unresolved_series", "short": "not stated",
     "label": "Tonnage the sources do not state",
     "note": "the two authoritative sources name no weight for these series", "color": "#b9ae9d"},
]
BAND_KEYS = [b["key"] for b in BANDS]
BAND_BY_KEY = {b["key"]: b for b in BANDS}

CATS = [
    ("oil_filter", "Oil filter"), ("fuel_filter", "Fuel filter"), ("air_filter", "Air filter"),
    ("blower_filter", "Blower filter"), ("urea_filter", "Urea (AdBlue) filter"),
    ("brake_pad", "Brake pad"), ("brake_shoe", "Brake shoe"), ("brake_rotor", "Brake rotor"),
    ("clutch_kit", "Clutch kit"), ("clutch_disc", "Clutch disc"),
    ("clutch_pressure_plate", "Clutch pressure plate"), ("clutch_booster", "Clutch booster"),
    ("release_bearing", "Release bearing"), ("pilot_bearing", "Pilot bearing"),
]
CAT_LABEL = dict(CATS)
CAT_KEYS = [c for c, _ in CATS]

METRICS = [
    {"key": "pv", "label": "EUR per vehicle", "unit": "eur_pv",
     "note": "This period's billed euro divided by this period's own vehicles in service. The one "
             "measure that does not move just because the fleet moved."},
    {"key": "abs", "label": "Billed euro", "unit": "eur",
     "note": "What was actually billed. Read it beside the fleet count, because a bigger fleet "
             "needs more euro just to stand still."},
    {"key": "units", "label": "Units", "unit": "units",
     "note": "Pieces billed. A unit is an ingredient, not a finding: read it with the service "
             "family and the fleet beside it."},
]

# Months that make a period comparable. One held-out month is stated on the page rather than
# compared as though it were a year.
MIN_MONTHS_FOR_PAIR = 12

CLOCK_DEF = {
    "CY": {"label": "Calendar year - January to December",
           "spelled": lambda p: f"CY{p} = January to December {p}"},
    "FY": {"label": "ISZE year - April to March, named by the closing year",
           "spelled": lambda p: f"FY{p} = April {p-1} - March {p}"},
}


def die(msg: str) -> None:
    print(f"BUILD FAIL: {msg}")
    sys.exit(1)


def rd(name: str) -> pd.DataFrame:
    p = DER / name
    if not p.is_file():
        die(f"missing {p}")
    return pd.read_csv(p, low_memory=False)


def series_evidence_table() -> pd.DataFrame:
    """The series -> band evidence table, read from the ONE authored map.

    `01_data/00_derived/series_to_tonnage.csv` is a generated copy of
    `03_analytics/Isuzu/prism/data/series_to_band.csv`: `build_nseries_tonnage_bands.py` writes it
    from that map, so it cannot disagree with it at build time - but it is a file on disk, so
    between an edit of the map and the next run it silently holds the older answer. That already
    happened once: the copy was written at 05:31 and the map was rewritten at 07:00, leaving its
    `NMR85` row reading `unresolved` while the map had moved on.

    Reading the map itself removes that window, and it is the same read `build_family_evolution_v2
    .py` already uses for the page that ships. The columns and their order are the ones the copy
    carries, so nothing downstream sees a different shape.
    """
    sys.path.insert(0, str(PDATA.parent))
    from modules import vehicle_bands  # noqa: PLC0415

    rows = []
    for code, r in sorted(vehicle_bands.load_map().items()):
        rows.append({
            "series": code,
            "tonnage_band": (r.get("tonnage_band") or "").strip() or vehicle_bands.UNRESOLVED,
            "weight_label": (r.get("weight_label") or "").strip(),
            "evidence_source": (r.get("evidence_source") or "").strip(),
            "evidence_quote": (r.get("evidence_quote") or "").strip(),
            "confidence": (r.get("confidence") or "").strip(),
        })
    return pd.DataFrame(rows)


def main() -> int:
    refresh = "--refresh" in sys.argv

    # ── the derived inputs ───────────────────────────────────────────────────────────────────────
    core = rd("pms_capture_by_family.csv")
    evo = rd("nseries_tonnage_evolution.csv")
    bands_dim = rd("vehicle_family_bands.csv").fillna("")
    nb = rd("epc_decode_nseries_banded.csv").fillna("")
    series_bands = series_evidence_table().fillna("")
    uio = rd("uio_by_market_type_year.csv")
    cap = rd("tonnage_capable_part_numbers.csv")
    buckets = pd.read_csv(PDATA / "uio_by_model_bucket.csv")
    n35share = pd.read_csv(PDATA / "uio_ld_n35_share.csv")
    meta = json.loads((DER / "pms_capture_by_family.meta.json").read_text(encoding="utf-8"))

    MARKETS = sorted(core.distributor_code.unique())
    MK = {m: i for i, m in enumerate(MARKETS)}

    # ── the interval lane each customer runs. Two lanes, never averaged. ─────────────────────────
    lane_n = core.groupby("distributor_code").lane.nunique()
    if int(lane_n.max()) > 1:
        die(f"a customer carries more than one interval lane: {lane_n[lane_n > 1].to_dict()}")
    LANE = {m: ("iml" if str(v) == "agreed" else "prism")
            for m, v in core.groupby("distributor_code").lane.first().items()}
    if set(LANE.values()) != {"iml", "prism"}:
        die(f"expected both interval lanes on the page, got {sorted(set(LANE.values()))}")

    # ── the part-number dimension: which family, which band, which service family ────────────────
    bands_dim["pnk"] = bands_dim.pn.map(norm)
    bands_dim = bands_dim.drop_duplicates("pnk")
    pn_fam_raw = dict(zip(bands_dim.pnk, bands_dim.resolution))
    PN_FAM = {}
    for pn, res in pn_fam_raw.items():
        if res == "single_family":
            PN_FAM[pn] = str(bands_dim.loc[bands_dim.pnk == pn, "family"].iloc[0])
        elif res == "shared_across_families":
            PN_FAM[pn] = "shared_across_families"
        else:
            PN_FAM[pn] = "unattributed"
    PN_FITS = {pn: [x for x in str(v).split("|") if x]
               for pn, v in zip(bands_dim.pnk, bands_dim.families_in_union)}
    PN_CAT = dict(zip(bands_dim.pnk, bands_dim.pms_category))
    PN_CAT_LABEL = dict(zip(bands_dim.pnk, bands_dim.category_label))
    PN_MODEL = dict(zip(bands_dim.pnk, bands_dim.vehicle_model))
    PN_CONF = dict(zip(bands_dim.pnk, bands_dim.confidence))
    PN_SRC = dict(zip(bands_dim.pnk, bands_dim.source_note))

    nb["pnk"] = nb.pn.map(norm)
    nb = nb.drop_duplicates("pnk")
    NB_BANDS = {pn: [x for x in str(v).split("|") if x]
                for pn, v in zip(nb.pnk, nb.tonnage_band)}
    NB_STATUS = dict(zip(nb.pnk, nb.band_status))
    NB_SERIES = dict(zip(nb.pnk, nb.series_all))
    NB_REASON = dict(zip(nb.pnk, nb.band_reason))

    def band_membership(pn: str) -> list[str]:
        """Every tonnage bucket a part number belongs to, exactly one of which is exclusive."""
        fam = PN_FAM.get(pn)
        bs = [b for b in NB_BANDS.get(pn, []) if b in BAND_KEYS[:3]]
        if fam != "n_series_truck" or not bs:
            if fam == "n_series_truck":
                # an N-series part number the banding sources cannot place at all
                return ["unresolved_series"]
            return []
        if len(bs) == 1:
            return bs
        return bs + ["shared_across_bands"]

    # exclusivity is read from the published `band_list`, so the page and the two published
    # banding files agree on which part numbers are counted once and which are shared.
    cap["pnk"] = cap.pn.map(norm)
    cap = cap.drop_duplicates("pnk")
    PN_NBANDS = dict(zip(cap.pnk, cap.n_bands))
    PN_CAP_BANDS = {pn: json.loads(str(v).replace("'", '"')) for pn, v in zip(cap.pnk, cap.band_list)}
    CAP_DEGREE = {}
    for cat, g in cap.groupby("category"):
        CAP_DEGREE[cat] = {"pns": int(len(g)),
                           "single_band": int((g.n_bands == 1).sum()),
                           "multi_band": int((g.n_bands > 1).sum()),
                           "placeable": bool((g.n_bands == 1).any())}

    # marker: a part number outside the placeable set cannot be attributed to a single band, so any
    # figure containing it is pooled rather than split. That is the decision this page makes instead
    # of printing a disclaimer on every panel.
    def cell_comparable(cat: str, rows: list[dict]) -> tuple[bool, str]:
        deg = CAP_DEGREE.get(cat)
        multi = [r for r in rows if r["nbands"] == 0 or r["nbands"] > 1]
        only = [r for r in rows if r["nbands"] == 1]
        if not multi:
            return True, ""
        share = (sum(r["e"] for r in multi) / sum(r["e"] for r in rows)) if rows else 0.0
        if not only:
            return False, (f"no {CAT_LABEL.get(cat, cat).lower()} part number on this page fits one "
                           f"band only, so this service family cannot be split by tonnage at all")
        if share > 0.5:
            return False, (f"{100*share:.0f}% of this service family's billed euro sits on part "
                           f"numbers that fit more than one band, so the band split is not available")
        return ("low", f"{100*share:.0f}% of this service family's euro sits on shared part numbers; "
                       f"read the band-only figure first")

    # ── the billing, read once. Every euro on the page is derived from this frame. ───────────────
    cache = BUILD_DIR / "_deep_billing_cache.parquet"
    if not cache.is_file() or refresh:
        die(f"{cache.name} is not on disk - run build_pms_family_deep_page.py first, or pass "
            f"--refresh to rebuild it through the tagging path")
    bill = pd.read_parquet(cache)
    bill["pn"] = bill.pn.astype(str).map(norm)
    bill = bill[bill.db.isin(MK) & bill.pn.isin(PN_FAM)].copy()
    bill["fam"] = bill.pn.map(PN_FAM)
    bill["cat"] = bill.pn.map(PN_CAT)
    bill = bill.dropna(subset=["cat"])

    # ── the fleet: one row per market x vehicle type x year, carried into service ────────────────
    # Only the three columns the fleet rows already carry are used: commercial vehicle (LD and MD),
    # F-series, and light commercial. No market is divided into a weight class the row does not name.
    uio["year"] = uio.year.astype(int)
    fleet_year: dict[str, dict[int, dict]] = {}
    for db, g in uio.groupby("distributor_code"):
        for y, gy in g.groupby("year"):
            def q(cls: str, typ: str) -> float:
                s = gy[(gy.vehicle_class == cls) & (gy.model_type == typ)].uio_units
                return float(s.sum())
            ns = q("CV", "LD") + q("CV", "MD")
            hv = q("CV", "F-Series")
            lt = q("LCV", "LCV")
            basis = str(gy.basis.iloc[0]) if len(gy) else "unknown"
            fleet_year.setdefault(db, {})[int(y)] = {
                "n_series": round(ns), "heavy": round(hv), "light": round(lt),
                "total": round(ns + hv + lt),
                "basis": basis,
                "quality": str(gy.fleet_quality_note.iloc[0]) if len(gy) else "",
            }

    bucket = {r.distributor_code: {"n_series": round(float(r.cv_std_uio)),
                                   "heavy": round(float(r.f_series_uio)),
                                   "light": round(float(r.lcv_uio)),
                                   "total": round(float(r.cv_std_uio + r.f_series_uio + r.lcv_uio))}
              for r in buckets.itertuples()}
    n35_sh = {r.distributor_code: float(r.n35_share) for r in n35share.itertuples()}
    share_basis = {r.distributor_code: str(r.basis) for r in n35share.itertuples()}

    # the model's flat 2025E estimate, offered as the second denominator rather than hidden
    for db in MARKETS:
        b = bucket.get(db)
        for y in fleet_year.get(db, {}):
            pass
    flat_est = {db: bucket.get(db, {"n_series": 0, "heavy": 0, "light": 0, "total": 0})
                for db in MARKETS}

    # ── the clocks, their periods, and which pair is drawn ───────────────────────────────────────
    def period_months(clock: str, period: int) -> int:
        if clock == "CY":
            return int(bill[bill.y == period].m.nunique())
        return int(bill[bill.fy == period].m.nunique())

    clocks = {}
    for clock in ("CY", "FY"):
        col = "y" if clock == "CY" else "fy"
        periods = sorted(int(p) for p in bill[col].dropna().unique())
        months = {p: period_months(clock, p) for p in periods}
        complete = [p for p in periods if months[p] >= 12]
        if len(complete) < 2:
            die(f"need two complete {clock} periods to compare, have {complete}")
        base, end = complete[-2], complete[-1]
        clocks[clock] = {
            "label": CLOCK_DEF[clock]["label"],
            "spelled": {str(p): CLOCK_DEF[clock]["spelled"](p) for p in periods},
            "months": {str(p): months[p] for p in periods},
            "periods": periods, "complete": complete,
            "pair": {"base": base, "end": end, "prior": base - 1,
                     "baseMonths": months[base], "endMonths": months[end],
                     "baseLabel": CLOCK_DEF[clock]["spelled"](base),
                     "endLabel": CLOCK_DEF[clock]["spelled"](end),
                     "priorLabel": CLOCK_DEF[clock]["spelled"](base - 1),
                     "sameMonths": months[base] >= MIN_MONTHS_FOR_PAIR
                     and months[end] >= MIN_MONTHS_FOR_PAIR,
                     "monthsInPair": min(months[base], months[end])},
            "heldOut": [{"period": p, "label": CLOCK_DEF[clock]["spelled"](p), "months": months[p]}
                        for p in periods if p not in complete],
        }

    # ── every euro figure, derived at part-number grain, then rolled up ──────────────────────────
    # cycles: the pair, the period a year before the base (so a part-number row can carry its own
    # percentage exactly as the brief asks), and the partial periods, which are flagged not
    # comparable rather than drawn.
    CYCLES = {}
    for clock in ("CY", "FY"):
        p = clocks[clock]["pair"]
        CYCLES[clock] = [p["prior"], p["base"], p["end"]]
        for extra in clocks[clock]["periods"]:
            if extra not in CYCLES[clock]:
                CYCLES[clock].append(extra)
        CYCLES[clock] = sorted(CYCLES[clock])
    CYC_IX = {c: {p: i for i, p in enumerate(CYCLES[c])} for c in CYCLES}
    CYC_LIST = {c: CYCLES[c] for c in CYCLES}

    # per part number x market x cycle: euro, units, customers. The atomic grain.
    PN_ROWS: dict[str, list[list]] = {}
    for clock in ("CY", "FY"):
        col = "y" if clock == "CY" else "fy"
        g = (bill.dropna(subset=[col])
             .groupby(["pn", "db", col], dropna=False)
             .agg(eur=("net_sales_value", "sum"), units=("billed_qty", "sum"))
             .reset_index())
        rows = []
        for r in g.itertuples():
            pn_i = PN_IX[r.pn]
            rows.append([pn_i, MK[r.db], CYC_IX[clock][int(getattr(r, col))],
                         round(float(r.eur), 2), round(float(r.units), 2)])
        PN_ROWS[clock] = rows
    # customers per part number x cycle, counted from the same frame
    PN_VEL: dict[str, dict] = {}
    for clock in ("CY", "FY"):
        col = "y" if clock == "CY" else "fy"
        g = (bill.dropna(subset=[col]).groupby(["pn", col]).db.nunique().reset_index())
        PN_VEL[clock] = {(PN_IX[r.pn], CYC_IX[clock][int(getattr(r, col))]): int(r.db)
                         for r in g.itertuples()}

    print(f"atomic rows CY {len(PN_ROWS['CY']):,} / FY {len(PN_ROWS['FY']):,} "
          f"| part numbers {len(PN_IX):,}")

    return write_page(
        MARKETS=MARKETS, MK=MK, LANE=LANE, clocks=clocks, CYC_LIST=CYC_LIST, CYC_IX=CYC_IX,
        PN_ROWS=PN_ROWS, PN_VEL=PN_VEL, PN_IX=PN_IX, PN_FAM=PN_FAM, PN_FITS=PN_FITS,
        PN_CAT=PN_CAT, PN_NBANDS=PN_NBANDS, PN_CAP_BANDS=PN_CAP_BANDS, CAP_DEGREE=CAP_DEGREE,
        band_membership=band_membership, cell_comparable=cell_comparable,
        fleet_year=fleet_year, flat_est=flat_est, n35_sh=n35_sh, share_basis=share_basis,
        core=core, evo=evo, series_bands=series_bands, meta=meta,
        NB_STATUS=NB_STATUS, NB_SERIES=NB_SERIES, NB_REASON=NB_REASON,
        PN_MODEL=PN_MODEL, PN_CONF=PN_CONF, PN_SRC=PN_SRC, PN_CAT_LABEL=PN_CAT_LABEL,
    )


if __name__ == "__main__":
    raise SystemExit(main())
