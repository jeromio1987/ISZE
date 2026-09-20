#!/usr/bin/env python
"""
prep_basemap.py — build data/basemap_land.geojson for the ISZE globe.

Why this exists
---------------
The globe must paint geography with no network. Natural Earth vectors already
sit on disk in the IDS master map asset cache, so this script copies them into
the globe folder instead of downloading tiles.

Source assets (read only, never modified):
  01_data/90_INBOX/_ids_master_map_assets/ne_110m_land.geojson
  01_data/90_INBOX/_ids_master_map_assets/ne_110m_admin_0_countries.geojson

Output: one FeatureCollection where each feature carries a `layer` property:
  "land"    -> country/land polygons, filled
  "border"  -> country outlines as lines, drawn on top

Properties from the source are stripped so the file stays small.

Run
---
    python 02_dashboards/globe/prep_basemap.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ASSETS = REPO / "01_data" / "90_INBOX" / "_ids_master_map_assets"

LAND_SRC = ASSETS / "ne_110m_land.geojson"
COUNTRIES_SRC = ASSETS / "ne_110m_admin_0_countries.geojson"
OUT = HERE / "data" / "basemap_land.geojson"


def rings(polygon: list) -> list[list]:
    """Return the exterior ring of each polygon in a Polygon coordinate array."""
    return [polygon[0]] if polygon else []


def to_lines(geometry: dict) -> list[list]:
    """Outline a Polygon or MultiPolygon as a list of line coordinate arrays."""
    out: list[list] = []
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if gtype == "Polygon":
        out.extend(rings(coords))
    elif gtype == "MultiPolygon":
        for polygon in coords:
            out.extend(rings(polygon))
    return out


def main() -> int:
    for src in (LAND_SRC, COUNTRIES_SRC):
        if not src.exists():
            raise SystemExit(f"Missing source asset: {src}")

    features: list[dict] = []

    # --- land polygons -----------------------------------------------------
    land = json.loads(LAND_SRC.read_text(encoding="utf-8"))
    n_land = 0
    for feat in land.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        features.append(
            {"type": "Feature", "properties": {"layer": "land"}, "geometry": geom}
        )
        n_land += 1

    # --- country outlines --------------------------------------------------
    countries = json.loads(COUNTRIES_SRC.read_text(encoding="utf-8"))
    n_border = 0
    for feat in countries.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        for line in to_lines(geom):
            if len(line) < 2:
                continue
            features.append(
                {
                    "type": "Feature",
                    "properties": {"layer": "border"},
                    "geometry": {"type": "LineString", "coordinates": line},
                }
            )
            n_border += 1

    collection = {"type": "FeatureCollection", "features": features}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(collection, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )

    print(f"land polygons      : {n_land}")
    print(f"border line strings: {n_border}")
    print(f"wrote              : {OUT}  ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
