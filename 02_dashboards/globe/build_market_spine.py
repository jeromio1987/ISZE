#!/usr/bin/env python
"""
build_market_spine.py — build data/market_spine.json for the ISZE 3D globe.

What this does
--------------
Joins the GPS parts-spend measures to market coordinates and to the entity
dimension, attaches the PMS capture panel numbers, generates a small square
polygon per market (MapLibre has no native point-column layer, so each market
becomes a fill-extrusion), and writes one JSON file the page fetches.

The metric that drives column height and the metric that drives column colour
are NOT hardcoded in the page. They are named in the `settings` block of the
output JSON, and the page reads them from there. Change the settings block and
the same page renders a different measure.

Join keys
---------
gps_spu_by_distributor.csv      -> distributor_code
distributor_geo.csv             -> distributor_code
pms_capture_by_db_year.csv      -> distributor_code
distributor_dimension.csv       -> distributor_code

All four files carry `distributor_code`, so no crosswalk table is needed.
The dimension file is joined on distributor_code (not payer_code). The
sold_to_sap / payer_code distinction matters because payer 1797 covers both
Israel businesses; this script verifies that UMI and UTI resolve to distinct
sold_to_sap values and aborts if they do not.

Run
---
    python 02_dashboards/globe/build_market_spine.py
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Paths — resolved from this file, never hardcoded to a user profile.
# --------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent  # 02_dashboards/globe -> 02_dashboards -> ISZE root

GPS_CSV = REPO / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
GEO_CSV = REPO / "03_analytics" / "Isuzu" / "prism" / "data" / "distributor_geo.csv"
PMS_CSV = REPO / "01_data" / "00_derived" / "pms_capture_by_db_year.csv"
DIM_CSV = REPO / "01_data" / "00_derived" / "distributor_dimension.csv"

OUT_JSON = HERE / "data" / "market_spine.json"

# --------------------------------------------------------------------------
# Geometry constants
#
# Column footprints and pair separations are defined in kilometres and then
# converted to degrees per market, because a degree of longitude shrinks as
# latitude rises. A fixed degree offset would overlap in Israel and leave a
# gap in Scotland.
# --------------------------------------------------------------------------

FOOTPRINT_HALF_KM = 60.0  # 120 km square column footprint
PAIR_SEPARATION_KM = 160.0  # centre-to-centre distance for markets sharing a coordinate

KM_PER_DEG_LAT = 110.574


def km_per_deg_lon(lat: float) -> float:
    return 111.320 * math.cos(math.radians(lat))


def square_ring(lat: float, lon: float, half_km: float) -> list[list[float]]:
    """Closed ring for a square centred on lat/lon, sized in ground kilometres."""
    dlat = half_km / KM_PER_DEG_LAT
    dlon = half_km / km_per_deg_lon(lat)
    w, e, s, n = lon - dlon, lon + dlon, lat - dlat, lat + dlat
    return [[w, s], [e, s], [e, n], [w, n], [w, s]]


# --------------------------------------------------------------------------
# Display labels
#
# Some distributor codes are countries, some are business units inside a
# country. Two pairs share a country (ITUK/IUK in the UK, UMI/UTI in Israel),
# so a country name alone would print the same label twice.
# --------------------------------------------------------------------------

SHORT_LABELS = {
    "ITUK": "Isuzu Truck UK",
    "IUK": "Isuzu UK",
    "UMI": "UMI Israel",
    "UTI": "UTI Israel",
    "BELGIUM": "Benelux (IBX)",
    "GERMANY": "Germany (ISD)",
    "PORTUGAL": "Portugal (Imotors)",
    "CYPRUS": "Cyprus (Loutsios)",
    "GREECE": "Greece (RSA)",
    "HUNGARY": "Hungary (AutoWallis)",
    "FINLAND": "Finland (Nordic)",
    "ICELAND": "Iceland (BL)",
    "MALTA": "Malta (GasanZammit)",
    "ROMANIA": "Romania (ROM Auto)",
    "DENMARK": "Denmark",
    "NORWAY": "Norway (Rutebiler)",
    "SWEDEN": "Sweden",
    "IRELAND": "Ireland",
}

# Plain-English gloss for acronyms, shown once in the panel header area.
GLOSSARY = {
    "GPS": "Global Parts Support — the parts-spend model that sets a target spend per truck.",
    "PMS": "Parts Market Scan — the model that compares what a market should buy against what it did buy.",
    "UIO": "Units In Operation — the vehicles in service that could buy parts.",
    "DB": "Distributor.",
}


def title_code(code: str) -> str:
    return code.replace("_", " ").title()


def get_short_label(code: str, country: str | None) -> str:
    if code in SHORT_LABELS:
        return SHORT_LABELS[code]
    if isinstance(country, str) and country.strip():
        return country.strip()
    return title_code(code)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def nan_to_none(value):
    """Convert pandas/numpy scalars to JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def clean_float(value, digits: int = 2):
    v = nan_to_none(value)
    if v is None:
        return None
    return round(float(v), digits)


def clean_int(value):
    v = nan_to_none(value)
    if v is None:
        return None
    return int(round(float(v)))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


# --------------------------------------------------------------------------
# Step 1 — read sources
# --------------------------------------------------------------------------


def read_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = [str(p) for p in (GPS_CSV, GEO_CSV, PMS_CSV, DIM_CSV) if not p.exists()]
    if missing:
        raise SystemExit("Missing source file(s):\n  " + "\n  ".join(missing))

    gps = pd.read_csv(GPS_CSV)
    geo = pd.read_csv(GEO_CSV)
    pms = pd.read_csv(PMS_CSV)
    dim = pd.read_csv(DIM_CSV)

    print(f"gps   {len(gps):>5} rows  {GPS_CSV.name}")
    print(f"geo   {len(geo):>5} rows  {GEO_CSV.name}")
    print(f"pms   {len(pms):>5} rows  {PMS_CSV.name}")
    print(f"dim   {len(dim):>5} rows  {DIM_CSV.name}")
    return gps, geo, pms, dim


# --------------------------------------------------------------------------
# Step 2 — pick the reporting year
# --------------------------------------------------------------------------


def pick_year(gps: pd.DataFrame) -> tuple[int, pd.DataFrame]:
    """
    Most recent FULL YEAR that actually carries a target spend.

    Partial-year rows are excluded: putting a half year next to a full year
    would compare unlike periods on the same map. 2026 is partial, and 2023
    and 2024 have no max_spend_eur, so this lands on 2025.
    """
    full = gps[gps["period_basis"] == "full_year"].copy()
    per_year = (
        full.groupby("year")["max_spend_eur"]
        .apply(lambda s: int(s.notna().sum()))
        .sort_index()
    )
    print("\nfull-year rows with a usable target spend, by year:")
    for yr, n in per_year.items():
        print(f"  {yr}: {n} of {int((full['year'] == yr).sum())}")

    usable = per_year[per_year > 0]
    if usable.empty:
        raise SystemExit(
            "\nSTOP: no full_year row in gps_spu_by_distributor.csv carries a "
            "populated max_spend_eur. The column-height measure (target spend "
            "minus what we billed) cannot be built. Not substituting another "
            "metric silently."
        )

    year = int(usable.index.max())
    print(f"\nchosen year: {year} (most recent full year with a target spend)")
    return year, full[full["year"] == year].copy()


# --------------------------------------------------------------------------
# Step 3 — market rows: measures + coordinates + dimension
# --------------------------------------------------------------------------


def build_markets(
    year_df: pd.DataFrame, geo: pd.DataFrame, dim: pd.DataFrame, year: int
) -> tuple[list[dict], list[dict], list[str]]:
    log: list[str] = []

    # --- coordinates -------------------------------------------------------
    geo_valid = geo[geo["lat"].notna() & geo["lon"].notna()].copy()
    dropped_geo = geo[geo["lat"].isna() | geo["lon"].isna()]
    for _, row in dropped_geo.iterrows():
        log.append(
            f"excluded from the map: {row['distributor_code']} — no coordinates in "
            f"distributor_geo.csv"
        )

    # --- dimension, one row per distributor_code ---------------------------
    # Prefer a network_db row that carries a customer name.
    dim_sorted = dim.copy()
    dim_sorted["_has_name"] = dim_sorted["customer_name"].notna().astype(int)
    dim_sorted["_is_network"] = (dim_sorted["network_role"] == "network_db").astype(int)
    dim_one = (
        dim_sorted.sort_values(
            ["distributor_code", "_is_network", "_has_name"],
            ascending=[True, False, False],
        )
        .drop_duplicates(subset=["distributor_code"], keep="first")
        .set_index("distributor_code")
    )

    # Verify the Israel split is preserved (payer 1797 covers two businesses).
    for code, expected_sap in (("UMI", "1797"), ("UTI", "1799")):
        if code in dim_one.index:
            got = str(nan_to_none(dim_one.loc[code, "sold_to_sap"]))
            if got != expected_sap:
                raise SystemExit(
                    f"\nSTOP: {code} resolves to sold_to_sap {got}, expected "
                    f"{expected_sap}. The Israel entity split is not what this "
                    f"script assumes — refusing to build rather than blending UMI "
                    f"and UTI."
                )
    log.append(
        "verified: UMI -> sold_to_sap 1797 and UTI -> sold_to_sap 1799 are distinct, "
        "even though both sit under payer 1797. The Israel split is preserved."
    )

    # --- join --------------------------------------------------------------
    df = year_df.merge(
        geo_valid[["distributor_code", "lat", "lon", "territory_label"]],
        on="distributor_code",
        how="left",
        suffixes=("", "_geo"),
    )

    unmapped_codes = sorted(df[df["lat"].isna()]["distributor_code"].unique().tolist())
    for code in unmapped_codes:
        log.append(
            f"excluded from the map: {code} — has GPS measures for {year} but no "
            f"coordinates in distributor_geo.csv"
        )

    df = df[df["lat"].notna() & df["lon"].notna()].copy()

    # --- spread markets that share one coordinate --------------------------
    df["_latr"] = df["lat"].round(4)
    df["_lonr"] = df["lon"].round(4)
    duplicates: list[str] = []
    for (lat_r, lon_r), group in df.groupby(["_latr", "_lonr"]):
        if len(group) < 2:
            continue
        codes = sorted(group["distributor_code"].tolist())
        duplicates.append(" and ".join(codes))
        n = len(codes)
        for idx, code in enumerate(codes):
            # Deterministic spread: offset along longitude, centred on the
            # original point, in ground kilometres.
            offset_deg = (
                (idx - (n - 1) / 2.0) * PAIR_SEPARATION_KM / km_per_deg_lon(lat_r)
            )
            sel = df["distributor_code"] == code
            df.loc[sel, "lon"] = df.loc[sel, "lon"] + offset_deg
            df.loc[sel, "lat"] = df.loc[sel, "lat"] + 0.0
            df.loc[sel, "_offset"] = True
            df.loc[sel, "_shared_with"] = "|".join(c for c in codes if c != code)
    for pair in duplicates:
        log.append(
            f"coordinate shared in the source by {pair}; spread apart on the map "
            f"({PAIR_SEPARATION_KM:.0f} km centre-to-centre), both labelled."
        )

    # --- assemble ---------------------------------------------------------
    columns: list[dict] = []
    unmodelled: list[dict] = []

    for _, row in df.sort_values("distributor_code").iterrows():
        code = str(row["distributor_code"])
        lat = float(row["lat"])
        lon = float(row["lon"])

        billed = clean_float(row.get("total_sales_eur"))
        target = clean_float(row.get("max_spend_eur"))
        capture = clean_float(row.get("gps_capture_vs_max"), 4)
        uio = clean_int(row.get("uio_units"))
        uio_valid = uio is not None and uio > 0

        gap = None
        if target is not None and billed is not None:
            gap = round(target - billed, 2)

        dim_row = dim_one.loc[code] if code in dim_one.index else None
        customer = (
            nan_to_none(dim_row["customer_name"]) if dim_row is not None else None
        )
        region = nan_to_none(dim_row["region"]) if dim_row is not None else None
        if region is None:
            region = nan_to_none(row.get("region"))
        scope = nan_to_none(dim_row["scope"]) if dim_row is not None else None

        shared_with = nan_to_none(row.get("_shared_with"))
        # Careful: after any row is flagged, the _offset column exists for the
        # whole frame and unset rows hold NaN, which is truthy in Python.
        offset_flag = row.get("_offset")
        has_offset = bool(offset_flag) if offset_flag is not None and not pd.isna(offset_flag) else False

        notes: list[str] = []
        if shared_with:
            notes.append(
                f"distributor_geo.csv puts {code} on the same coordinate as "
                f"{shared_with}; the two are drawn as offset columns here."
            )
        if not uio_valid:
            notes.append(
                "no vehicles-in-service count (UIO) in the source; the fleet "
                "denominator is missing, so no euro-per-truck rate is shown. "
                "This is a data gap, not a zero."
            )
        warranty_gap = nan_to_none(row.get("warranty_data_gap"))
        if warranty_gap not in (None, "", False, 0, "False"):
            notes.append(str(warranty_gap))

        record = {
            "id": slugify(code),
            "distributor_code": code,
            "label": get_short_label(code, nan_to_none(row.get("country"))),
            "display_name": customer if customer else get_short_label(
                code, nan_to_none(row.get("country"))
            ),
            "country": nan_to_none(row.get("country")),
            "region": region,
            "scope": scope,
            "territory_label": nan_to_none(row.get("territory_label")),
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "coord_offset_applied": has_offset,
            "coord_shared_with": shared_with.split("|") if shared_with else [],
            "year": year,
            "period_basis": nan_to_none(row.get("period_basis")),
            # measures
            "gap_eur": gap,
            "total_sales_eur": billed,
            "max_spend_eur": target,
            "capture_vs_max": capture,
            "spend_per_unit_eur": clean_float(row.get("spend_per_unit_eur")),
            "spend_per_unit_ex_warranty_eur": clean_float(
                row.get("spend_per_unit_ex_warranty_eur")
            ),
            "uio_units": uio if uio_valid else None,
            "uio_missing": not uio_valid,
            "uio_source": nan_to_none(row.get("uio_source")),
            "traffic_light": nan_to_none(row.get("traffic_light")),
            "coverage_note": nan_to_none(row.get("coverage_note")),
            "notes": notes,
            "geometry": {
                "type": "Polygon",
                "coordinates": [square_ring(lat, lon, FOOTPRINT_HALF_KM)],
            },
        }

        if gap is None:
            unmodelled.append(record)
        else:
            columns.append(record)

    return columns, unmodelled, log


# --------------------------------------------------------------------------
# Step 4 — PMS capture panel numbers
# --------------------------------------------------------------------------


def build_pms(pms: pd.DataFrame, year: int) -> dict[str, dict]:
    """
    Value-weighted capture per market, led by `total`.

    House rule: the panel leads with total capture. Genuine and bvp are extra
    lenses, never the headline.

    Weighted capture = sum(actual revenue) / sum(actual revenue + revenue gap),
    taken over the part families that carry a quotable gap. A family with no
    modelled expectation has no gap and is excluded from both sides rather than
    counted as a zero.
    """
    p = pms[pms["year"] == year].copy()
    out: dict[str, dict] = {}

    for code, group in p.groupby("distributor_code"):
        entry: dict = {"year": year}

        for line_type in ("total", "genuine", "bvp"):
            sub = group[(group["line_type"] == line_type) & (group["revenue_gap_quotable"])]
            if sub.empty:
                entry[line_type] = None
                continue
            actual = float(sub["actual_rev_eur"].sum())
            gap = float(sub["revenue_gap_eur"].sum())
            expected = actual + gap
            entry[line_type] = {
                "actual_rev_eur": round(actual, 2),
                "revenue_gap_eur": round(gap, 2),
                "expected_rev_eur": round(expected, 2),
                "capture_weighted": round(actual / expected, 4) if expected > 0 else None,
                "families": int(len(sub)),
            }

        # Category detail comes off the total line only, so the families add up.
        total_sub = group[(group["line_type"] == "total") & (group["revenue_gap_quotable"])]
        fams = (
            total_sub.sort_values("revenue_gap_eur", ascending=False)
            .head(3)
            .apply(
                lambda r: {
                    "category": r["category_label"],
                    "gap_eur": round(float(r["revenue_gap_eur"]), 2),
                    "capture_rate": round(float(r["capture_rate"]), 4),
                },
                axis=1,
            )
            .tolist()
        )
        entry["top_gap_families"] = fams

        out[str(code)] = entry

    return out


# --------------------------------------------------------------------------
# Step 5 — settings block (the metric switch)
# --------------------------------------------------------------------------


def build_metrics(columns: list[dict]) -> dict:
    """
    The metric registry. Every measure the page can plot is described here,
    with its own label, unit, scale and height reference. The page never
    hardcodes a measure; it looks the chosen field up in this registry and
    paints whatever it finds.

    `height_reference` is the value that maps to the full column height: the
    largest value in the market set, or 1.0 for a share where the top of the
    scale is meaningfully 100%.
    """
    euro_ramp = [
        {"at": 0.0, "color": "#e8e2d6"},
        {"at": 1.0, "color": "#c0552d"},
    ]

    def top_of(field: str) -> float | None:
        vals = [c[field] for c in columns if c.get(field) is not None]
        return max(vals) if vals else None

    return {
        "gap_eur": {
            "label": "Uncaptured parts spend",
            "long_label": "Target spend for the market minus what we billed for parts",
            "unit": "EUR",
            "format": "eur",
            "height_reference": top_of("gap_eur"),
            "color_scale": {
                "type": "ramp",
                "mode": "sqrt",
                "stops": euro_ramp,
                "missing_color": "#6b7280",
                "note": (
                    "Continuous ramp on a square-root scale. Euro values span two "
                    "orders of magnitude across these markets, so equal-width colour "
                    "bands would put every market except three in the palest class."
                ),
            },
        },
        "capture_vs_max": {
            "label": "Share of target spend captured",
            "long_label": "Parts billed divided by the target spend for the market",
            "unit": "share",
            "format": "pct",
            "height_reference": 1.0,
            "color_scale": {
                "type": "step",
                "classes": [
                    {"max": 0.4, "color": "#b23a3a", "label": "under 40% captured"},
                    {"max": 0.55, "color": "#c0552d", "label": "40% to 55% captured"},
                    {"max": 0.7, "color": "#d99a3c", "label": "55% to 70% captured"},
                    {"max": 0.85, "color": "#7fa96b", "label": "70% to 85% captured"},
                    {"max": 1.01, "color": "#3f7d4f", "label": "85% captured or more"},
                ],
                "missing_color": "#6b7280",
                "note": (
                    "Class breaks sit in the gaps between natural clusters in the 2025 "
                    "data, not on round numbers: 35% | 40-55% (six markets) | 55-70% "
                    "(four) | 70-85% (four) | 84-92% (three)."
                ),
            },
        },
        "spend_per_unit_eur": {
            "label": "What we billed per truck",
            "long_label": "Parts billed divided by the vehicles in service",
            "unit": "EUR per truck",
            "format": "eur",
            "height_reference": top_of("spend_per_unit_eur"),
            "color_scale": {
                "type": "step",
                "classes": [
                    {"max": 150, "color": "#b23a3a", "label": "under EUR 150 per truck"},
                    {"max": 190, "color": "#c0552d", "label": "EUR 150 to 190 per truck"},
                    {"max": 230, "color": "#d99a3c", "label": "EUR 190 to 230 per truck"},
                    {"max": 280, "color": "#7fa96b", "label": "EUR 230 to 280 per truck"},
                    {"max": 100000, "color": "#3f7d4f", "label": "EUR 280 or more per truck"},
                ],
                "missing_color": "#6b7280",
                "note": "Observed range EUR 88 to 389 across the 18 markets.",
            },
        },
        "total_sales_eur": {
            "label": "Parts billed",
            "long_label": "Parts revenue billed into the market",
            "unit": "EUR",
            "format": "eur",
            "height_reference": top_of("total_sales_eur"),
            "color_scale": {
                "type": "ramp",
                "mode": "sqrt",
                "stops": euro_ramp,
                "missing_color": "#6b7280",
            },
        },
        "max_spend_eur": {
            "label": "Target spend for the market",
            "long_label": "Modelled parts spend the market should support",
            "unit": "EUR",
            "format": "eur",
            "height_reference": top_of("max_spend_eur"),
            "color_scale": {
                "type": "ramp",
                "mode": "sqrt",
                "stops": euro_ramp,
                "missing_color": "#6b7280",
            },
        },
    }


def build_settings(columns: list[dict], year: int) -> dict:
    metrics = build_metrics(columns)
    gaps = [c["gap_eur"] for c in columns if c["gap_eur"] is not None]
    reference = max(gaps) if gaps else 1.0

    return {
        "schema_version": 2,
        # --- the metric switch -------------------------------------------
        # Change `height_metric` and/or `color_metric` and the same page paints
        # a different measure. Keys must exist in `metrics`.
        "height_metric": "gap_eur",
        "color_metric": "capture_vs_max",
        "metrics": metrics,
        # --- how a metric value becomes a column height -------------------
        "height": {
            "mode": "sqrt_floor",
            "floor_m": 35000,
            "peak_m": 700000,
            "reference": reference,
            "note": (
                "Column height above ground, read by MapLibre as fill-extrusion "
                "height in metres. The gap ranges from EUR 16,218 to EUR 6,271,367, "
                "a 387-fold spread, so every column gets a 35 km base from which the "
                "square root of the value adds up to 700 km. On a plain linear scale "
                "the smallest fifteen markets would be a flat line, and the floor is "
                "what makes a small gap still clickable and visible."
            ),
        },
        "projection": {
            "default": "globe",
            "fallback": "mercator",
            "note": (
                "Globe is the default. If the browser cannot paint the extruded "
                "columns on the globe, the toolbar switch drops to a flat map."
            ),
        },
        "projection": {
            "default": "globe",
            "fallback": "mercator",
            "note": (
                "Globe is the default. If the browser cannot paint the extruded "
                "columns on the globe, the toolbar switch drops to a flat map."
            ),
        },
        "year": year,
        "footprint_half_km": FOOTPRINT_HALF_KM,
        "pair_separation_km": PAIR_SEPARATION_KM,
        "gap_range_eur": {
            "min": min(gaps) if gaps else None,
            "max": max(gaps) if gaps else None,
        },
        "glossary": GLOSSARY,
    }


# --------------------------------------------------------------------------
# Step 6 — not-yet-wired list (explicit, never fabricated)
# --------------------------------------------------------------------------


def build_not_included() -> list[dict]:
    return [
        {
            "item": "Warranty parts",
            "why": (
                "Source sits with IMG and is market-level only, on three conflicting "
                "euro bases. Not reconciled, so not plotted."
            ),
        },
        {
            "item": "Fleet size workbook (UIO)",
            "why": (
                "The workbook needs a name crosswalk to distributor codes before its "
                "counts can be joined to this map."
            ),
        },
        {
            "item": "Price revision",
            "why": "Separate track. No market-level figures wired into this data set.",
        },
        {
            "item": "Live tenders",
            "why": (
                "Tracked elsewhere and not keyed to distributor_code, so it does not "
                "join to these columns."
            ),
        },
        {
            "item": "Sales to dealer",
            "why": (
                "Not wired for every market on this map; coverage is partial, so it "
                "would compare unlike things."
            ),
        },
    ]


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def main() -> int:
    os.chdir(HERE)
    print("=" * 72)
    print("build_market_spine.py")
    print("=" * 72)
    print(f"repo root: {REPO}\n")

    gps, geo, pms, dim = read_sources()
    year, year_df = pick_year(gps)

    columns, unmodelled, log = build_markets(year_df, geo, dim, year)
    pms_by_code = build_pms(pms, year)

    for record in columns + unmodelled:
        record["pms"] = pms_by_code.get(record["distributor_code"])

    settings = build_settings(columns, year)

    # ---- scale preview, printed for the build log -------------------------
    print("\ncolumn height scale:")
    hs = settings["height"]
    ref = hs["reference"]
    preview = []
    for c in sorted(columns, key=lambda r: -r["gap_eur"]):
        norm = math.sqrt(max(c["gap_eur"], 0.0) / ref) if ref else 0.0
        h = hs["floor_m"] + (hs["peak_m"] - hs["floor_m"]) * norm
        preview.append((c["distributor_code"], c["gap_eur"], h))
    for code, gap, h in preview:
        print(f"  {code:<12} gap EUR {gap:>12,.0f}   height {h:>9,.0f} m")

    # ---- colour class tally (uses the configured colour metric) -----------
    color_field = settings["color_metric"]
    cs = settings["metrics"][color_field]["color_scale"]
    print(f"\ncolour metric: {settings['metrics'][color_field]['label']} ({color_field})")
    if cs["type"] == "step":
        tally = {cdef["label"]: 0 for cdef in cs["classes"]}
        for c in columns:
            val = c.get(color_field)
            if val is None:
                continue
            for cdef in cs["classes"]:
                if val < cdef["max"]:
                    tally[cdef["label"]] += 1
                    break
        for cdef in cs["classes"]:
            print(f"  {cdef['label']:<26} {tally[cdef['label']]:>3} markets   {cdef['color']}")
    else:
        vals = [c.get(color_field) for c in columns if c.get(color_field) is not None]
        print(
            f"  continuous ramp ({cs['mode']}), "
            f"{min(vals):,.0f} to {max(vals):,.0f}, "
            f"{cs['stops'][0]['color']} -> {cs['stops'][-1]['color']}"
        )

    # ---- output ----------------------------------------------------------
    out = {
        "generated": date.today().isoformat(),
        "generator": "02_dashboards/globe/build_market_spine.py",
        "sources": {
            "measures": "01_data/00_derived/gps_spu_by_distributor.csv",
            "coordinates": "03_analytics/Isuzu/prism/data/distributor_geo.csv",
            "pms_panel": "01_data/00_derived/pms_capture_by_db_year.csv",
            "entities": "01_data/00_derived/distributor_dimension.csv",
        },
        "settings": settings,
        "columns": columns,
        "unmodelled": unmodelled,
        "not_included": build_not_included(),
        "build_log": log,
    }

    # ---- guard: the configured metrics must resolve to real values --------
    for role in ("height_metric", "color_metric"):
        field = settings[role]
        if field not in settings["metrics"]:
            raise SystemExit(
                f"\nSTOP: settings.{role} is '{field}' but that key is not in the "
                f"metric registry. The page would paint nothing."
            )
        n = sum(1 for c in columns if c.get(field) is not None)
        print(f"{role:<14} = {field:<26} populated for {n} of {len(columns)} columns")
        if n == 0:
            raise SystemExit(
                f"\nSTOP: settings.{role} = '{field}' has no values in this build."
            )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"columns drawn      : {len(columns)}")
    print(f"markets without a target spend: {len(unmodelled)} "
          f"({', '.join(r['distributor_code'] for r in unmodelled)})")
    print(f"wrote              : {OUT_JSON}  ({OUT_JSON.stat().st_size:,} bytes)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
