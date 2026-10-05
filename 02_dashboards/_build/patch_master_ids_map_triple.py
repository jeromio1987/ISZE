"""
Patch IDS master dealer-compare HTML with a 3-layer map stack:

  1) Offline street basemap  — Esri World Street Map export (Europe+Israel) as image overlay
  2) Richer offline vector   — land + country borders + major roads + cities (Natural Earth)
  3) Live CDN tiles          — Esri → CARTO → OSM failover (works when network/IT allows)

Master only: 02_dashboards/ids/IDS_2026_dealer_compare.html
"""
from __future__ import annotations

import base64
import json
import re
import ssl
import urllib.request
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MASTER = ISZE / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
CACHE = ISZE / "01_data" / "90_INBOX" / "_ids_master_map_assets"
LEAFLET_JS = ISZE / "02_dashboards" / "_ui" / "leaflet.js"
LEAFLET_CSS = ISZE / "02_dashboards" / "_ui" / "leaflet.css"

# Europe + Israel working box (same spirit as map fitBounds)
# Wide lon span so a wide Map panel still fills with the street image at zoom 4–5
BBOX = (-40.0, 28.0, 55.0, 72.0)  # west, south, east, north
CTX = ssl.create_default_context()


def fetch(url: str, dest: Path, timeout: int = 120) -> bytes:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return dest.read_bytes()
    print(f"GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "ISZE-IDS-map-build/1.0"})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"  -> {dest.name} {len(data):,} bytes")
    return data


def in_bbox(lon: float, lat: float, pad: float = 2.0) -> bool:
    w, s, e, n = BBOX
    return (w - pad) <= lon <= (e + pad) and (s - pad) <= lat <= (n + pad)


def geom_hits_bbox(geom: dict) -> bool:
    """Cheap bbox test from GeoJSON geometry coordinates."""
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not gtype or coords is None:
        return False

    def walk(c):
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            lon, lat = float(c[0]), float(c[1])
            return in_bbox(lon, lat, pad=4.0)
        if isinstance(c, (list, tuple)):
            return any(walk(x) for x in c)
        return False

    return walk(coords)


def load_geojson_url(url: str, dest: Path) -> dict:
    raw = fetch(url, dest)
    return json.loads(raw.decode("utf-8"))


def filter_features(fc: dict, keep_fn) -> dict:
    feats = [f for f in fc.get("features", []) if keep_fn(f)]
    return {"type": "FeatureCollection", "features": feats}


def simplify_ring(ring: list, step: int) -> list:
    if step <= 1 or len(ring) < 8:
        return ring
    out = ring[::step]
    if out[-1] != ring[-1]:
        out.append(ring[-1])
    return out


def simplify_geom(geom: dict, step: int) -> dict:
    gtype = geom["type"]
    coords = geom["coordinates"]
    if gtype == "Polygon":
        return {"type": "Polygon", "coordinates": [simplify_ring(r, step) for r in coords]}
    if gtype == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [[simplify_ring(r, step) for r in poly] for poly in coords],
        }
    if gtype == "LineString":
        return {"type": "LineString", "coordinates": simplify_ring(coords, step)}
    if gtype == "MultiLineString":
        return {"type": "MultiLineString", "coordinates": [simplify_ring(r, step) for r in coords]}
    return geom


def build_vector_pack() -> dict:
    """Return dict with land, borders, roads, cities FeatureCollections (Europe-ish)."""
    ne = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"

    land_fc = load_geojson_url(f"{ne}/ne_110m_land.geojson", CACHE / "ne_110m_land.geojson")
    # keep only features that touch our box (still small file)
    land = filter_features(land_fc, lambda f: geom_hits_bbox(f.get("geometry") or {}))
    for f in land["features"]:
        f["geometry"] = simplify_geom(f["geometry"], 1)

    admin = load_geojson_url(
        f"{ne}/ne_110m_admin_0_countries.geojson", CACHE / "ne_110m_admin_0_countries.geojson"
    )
    borders = filter_features(admin, lambda f: geom_hits_bbox(f.get("geometry") or {}))
    for f in borders["features"]:
        props = f.get("properties") or {}
        f["properties"] = {
            "name": props.get("NAME") or props.get("ADMIN") or "",
            "iso": props.get("ISO_A3") or "",
        }
        f["geometry"] = simplify_geom(f["geometry"], 1)

    # Roads: 10m is large — use 10m but filter aggressively + simplify
    roads_url = f"{ne}/ne_10m_roads.geojson"
    try:
        roads_fc = load_geojson_url(roads_url, CACHE / "ne_10m_roads.geojson")
    except Exception as exc:
        print("roads download failed, continuing without:", exc)
        roads_fc = {"type": "FeatureCollection", "features": []}

    def keep_road(f: dict) -> bool:
        geom = f.get("geometry") or {}
        if not geom_hits_bbox(geom):
            return False
        props = f.get("properties") or {}
        # major only
        typ = str(props.get("type") or props.get("road") or "").lower()
        scalerank = props.get("scalerank")
        try:
            sr = int(scalerank) if scalerank is not None else 99
        except Exception:
            sr = 99
        if sr <= 4:
            return True
        if any(k in typ for k in ("major", "primary", "secondary", "motorway", "trunk", "highway")):
            return True
        return False

    roads = filter_features(roads_fc, keep_road)
    # Cap road count for HTML size
    roads["features"] = roads["features"][:2500]
    for f in roads["features"]:
        props = f.get("properties") or {}
        f["properties"] = {"name": props.get("name") or props.get("Name") or ""}
        f["geometry"] = simplify_geom(f["geometry"], 3)

    places = load_geojson_url(
        f"{ne}/ne_110m_populated_places.geojson", CACHE / "ne_110m_populated_places.geojson"
    )

    def keep_place(f: dict) -> bool:
        geom = f.get("geometry") or {}
        if geom.get("type") != "Point":
            return False
        lon, lat = geom["coordinates"][:2]
        if not in_bbox(float(lon), float(lat), pad=1.0):
            return False
        props = f.get("properties") or {}
        try:
            pop = float(props.get("POP_MAX") or props.get("pop_max") or 0)
        except Exception:
            pop = 0
        rank = props.get("SCALERANK") or props.get("scalerank")
        try:
            sr = int(rank) if rank is not None else 99
        except Exception:
            sr = 99
        return pop >= 200000 or sr <= 3

    cities = filter_features(places, keep_place)
    for f in cities["features"]:
        props = f.get("properties") or {}
        f["properties"] = {
            "name": props.get("NAME") or props.get("name") or "",
            "pop": props.get("POP_MAX") or props.get("pop_max") or 0,
        }

    print(
        "vector counts:",
        f"land={len(land['features'])}",
        f"borders={len(borders['features'])}",
        f"roads={len(roads['features'])}",
        f"cities={len(cities['features'])}",
    )
    return {"land": land, "borders": borders, "roads": roads, "cities": cities}


def build_street_image() -> tuple[str, list[float]]:
    """Download Europe street basemap PNG via Esri export; return data-URL + bounds [s,w,n,e] for L.imageOverlay."""
    w, s, e, n = BBOX
    # Esri export — World_Street_Map
    url = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/export"
        f"?bbox={w},{s},{e},{n}&bboxSR=4326&imageSR=4326&size=2400,1600&format=png&f=image"
    )
    dest = CACHE / "europe_israel_street_basemap.png"
    try:
        png = fetch(url, dest, timeout=180)
    except Exception as exc:
        print("Esri export failed, trying CARTO static-ish via OSM static —", exc)
        # Fallback: use a natural-earth raster-ish approach — solid fail → tiny placeholder
        # Second try: ArcGIS World_Topo_Map
        url2 = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/export"
            f"?bbox={w},{s},{e},{n}&bboxSR=4326&imageSR=4326&size=2000,1400&format=png&f=image"
        )
        png = fetch(url2, CACHE / "europe_israel_topo_basemap.png", timeout=180)

    if len(png) < 5000 or png[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Basemap download does not look like PNG ({len(png)} bytes)")

    b64 = base64.b64encode(png).decode("ascii")
    data_url = "data:image/png;base64," + b64
    # Leaflet imageOverlay bounds: [[south, west], [north, east]]
    bounds = [[s, w], [n, e]]
    print(f"street basemap PNG {len(png):,} bytes -> data-url {len(data_url):,} chars")
    return data_url, bounds


def js_literal(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def build_map_init_js(vectors: dict, street_data_url: str, street_bounds: list) -> str:
    """Replacement for the `if (!window.__idsMap) { ... }` block body (inside)."""
    return f"""
        window.__idsMap = L.map("ids-map", {{ scrollWheelZoom: true }});

        // Pane stack (bottom → top): street image, vector geography, CDN tiles, pins
        // Below Leaflet tilePane (200) so live tiles cover offline layers when they work
        window.__idsMap.createPane("streetPane");
        window.__idsMap.getPane("streetPane").style.zIndex = 150;
        window.__idsMap.createPane("vectorPane");
        window.__idsMap.getPane("vectorPane").style.zIndex = 175;

        // --- (1) Offline street basemap (baked Europe+Israel street image) ---
        const streetUrl = {js_literal(street_data_url)};
        const streetBounds = {js_literal(street_bounds)};
        window.__idsStreetLayer = L.imageOverlay(streetUrl, streetBounds, {{
          pane: "streetPane",
          opacity: 1,
          interactive: false,
          attribution: "Basemap &copy; Esri (offline snapshot)"
        }}).addTo(window.__idsMap);
        try {{
          window.__idsMap.setMaxBounds(streetBounds);
          window.__idsMap.options.maxBoundsViscosity = 0.85;
        }} catch (e) {{}}

        // --- (2) Richer offline vector (land / borders / roads / cities) ---
        const IDS_VECTOR = {{
          land: {js_literal(vectors["land"])},
          borders: {js_literal(vectors["borders"])},
          roads: {js_literal(vectors["roads"])},
          cities: {js_literal(vectors["cities"])}
        }};
        window.__idsVectorLand = L.geoJSON(IDS_VECTOR.land, {{
          pane: "vectorPane",
          interactive: false,
          style: {{ color: "#8a9bb0", weight: 0.4, fillColor: "#efe8dc", fillOpacity: 0.12 }}
        }}).addTo(window.__idsMap);
        window.__idsVectorBorders = L.geoJSON(IDS_VECTOR.borders, {{
          pane: "vectorPane",
          interactive: false,
          style: {{ color: "#4a5d73", weight: 1.1, fillOpacity: 0 }}
        }}).addTo(window.__idsMap);
        window.__idsVectorRoads = L.geoJSON(IDS_VECTOR.roads, {{
          pane: "vectorPane",
          interactive: false,
          style: {{ color: "#c4a574", weight: 1.15, opacity: 0.85 }}
        }}).addTo(window.__idsMap);
        window.__idsVectorCities = L.geoJSON(IDS_VECTOR.cities, {{
          pane: "vectorPane",
          interactive: false,
          pointToLayer: function (feature, latlng) {{
            const name = (feature.properties && feature.properties.name) || "";
            return L.circleMarker(latlng, {{
              radius: 2.4,
              color: "#1a2744",
              weight: 1,
              fillColor: "#f7f4ee",
              fillOpacity: 0.95
            }}).bindTooltip(name, {{ direction: "top", opacity: 0.9, className: "ids-map-tooltip" }});
          }}
        }}).addTo(window.__idsMap);

        // --- (3) Live CDN tiles (Esri → CARTO → OSM) when network / IT allows ---
        const BASEMAPS = [
          {{
            name: "Esri streets",
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}",
            opts: {{ maxZoom: 19, attribution: "Tiles &copy; Esri" }}
          }},
          {{
            name: "CARTO Voyager",
            url: "https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png",
            opts: {{
              maxZoom: 18,
              subdomains: "abcd",
              attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            }}
          }},
          {{
            name: "OpenStreetMap",
            url: "https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
            opts: {{
              maxZoom: 19,
              attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }}
          }}
        ];
        function setTileStatus(msg, warn) {{
          const el = document.getElementById("ids-tile-status");
          if (!el) return;
          el.textContent = msg;
          if (warn) el.classList.add("warn"); else el.classList.remove("warn");
        }}
        function onTilesLive(name) {{
          window.__idsTilesOk = true;
          window.__idsTileFailed = false;
          window.__idsTileSource = name;
          // Live tiles cover the view — soften offline street image so streets aren't double-printed
          if (window.__idsStreetLayer) window.__idsStreetLayer.setOpacity(0.15);
          if (window.__idsVectorLand) window.__idsVectorLand.setStyle({{ fillOpacity: 0.08, opacity: 0.35 }});
          if (window.__idsVectorRoads) window.__idsVectorRoads.setStyle({{ opacity: 0.25 }});
          setTileStatus("Live street tiles (" + name + "). Offline street image + vector geography stay as backup.", false);
        }}
        function onTilesDead() {{
          window.__idsTilesOk = false;
          window.__idsTileFailed = true;
          if (window.__idsStreetLayer) window.__idsStreetLayer.setOpacity(1);
          // Street snapshot already paints land — keep vectors as labels/structure only
          if (window.__idsVectorLand) window.__idsVectorLand.setStyle({{ fillOpacity: 0, opacity: 0 }});
          if (window.__idsVectorBorders) window.__idsVectorBorders.setStyle({{ opacity: 0.9, weight: 1.2 }});
          if (window.__idsVectorRoads) window.__idsVectorRoads.setStyle({{ opacity: 0.7 }});
          setTileStatus("Live tile servers blocked or offline — showing baked street basemap + vector geography (borders, roads, cities).", true);
        }}
        function attachBasemap(i) {{
          if (i >= BASEMAPS.length) {{
            onTilesDead();
            return;
          }}
          const spec = BASEMAPS[i];
          const layer = L.tileLayer(spec.url, spec.opts);
          let loaded = false;
          let errors = 0;
          let switched = false;
          function failOver() {{
            if (switched || loaded) return;
            switched = true;
            try {{ window.__idsMap.removeLayer(layer); }} catch (e) {{}}
            attachBasemap(i + 1);
          }}
          layer.on("load", function () {{
            loaded = true;
            onTilesLive(spec.name);
          }});
          layer.on("tileerror", function () {{
            errors += 1;
            if (!loaded && errors >= 4) failOver();
          }});
          setTimeout(function () {{
            if (!loaded) failOver();
          }}, 2200);
          layer.addTo(window.__idsMap);
          window.__idsTileLayer = layer;
        }}
        attachBasemap(0);
        window.__idsMapLayer = L.layerGroup().addTo(window.__idsMap);
"""


def patch_master(map_init_js: str) -> None:
    html = MASTER.read_text(encoding="utf-8")
    bak = MASTER.with_suffix(MASTER.suffix + ".bak_map_triple_20260916")
    if not bak.exists():
        bak.write_text(html, encoding="utf-8")
        print("backup", bak)

    # Hint text
    html = html.replace(
        "Map tiles require an internet connection. Dealers without coordinates stay in the tables only.",
        "Three map layers: live street tiles when the network allows (Esri → CARTO → OSM), "
        "a baked Europe/Israel street basemap inside this file, and offline vector geography "
        "(borders, major roads, cities). Dealers without coordinates stay in the tables only.",
    )

    # Map background ocean
    html = html.replace(
        "#ids-map { width:100%; height:560px; border-radius:8px; border:1px solid var(--mid); background:#dce3ec; }",
        "#ids-map { width:100%; height:560px; border-radius:8px; border:1px solid var(--mid); background:#b9cfe0; }",
    )

    # Replace the init block inside renderMap
    pattern = re.compile(
        r"if \(!window\.__idsMap\) \{\s*"
        r"window\.__idsMap = L\.map\(\"ids-map\", \{ scrollWheelZoom: true \}\);"
        r".*?"
        r"window\.__idsMapLayer = L\.layerGroup\(\)\.addTo\(window\.__idsMap\);"
        r"\s*\}",
        re.S,
    )
    new_block = "if (!window.__idsMap) {" + map_init_js + "\n      }"
    html2, n = pattern.subn(new_block, html, count=1)
    if n != 1:
        raise RuntimeError(f"Failed to replace map init block (matches={n})")

    # Soften the post-render status overwrite so it doesn't wipe tile status every time
    # Find the statusEl text rebuild at end of renderMap and prepend layer note.
    status_pat = re.compile(
        r"(if \(statusEl\) \{\s*statusEl\.classList\.remove\(\"warn\"\);)",
        re.S,
    )
    # Actually the end status always clears warn — patch to preserve tile failure warn
    old_status_start = """      if (statusEl) {
        statusEl.classList.remove("warn");
        const overseasN = pinned.filter("""
    new_status_start = """      if (statusEl) {
        if (!window.__idsTileFailed) statusEl.classList.remove("warn");
        const overseasN = pinned.filter("""
    if old_status_start not in html2:
        print("WARN: status block start not found exactly — leaving pin counts as-is")
    else:
        html2 = html2.replace(old_status_start, new_status_start, 1)

    # Append layer note into the final status text assignment — find typical pattern
    # Look for statusEl.textContent = `...` near end of renderMap
    m = re.search(
        r"(statusEl\.textContent = `)([^`]*)(`;)",
        html2[html2.find("function renderMap") : html2.find("function renderMap") + 12000],
    )
    if m:
        # operate on full html with more care
        pass

    # Simpler: after pin-count status assignment, if tiles failed keep that message primary
    inject = """
      if (statusEl && window.__idsTileFailed) {
        statusEl.classList.add("warn");
        statusEl.textContent = "Offline mode: baked street basemap + vector geography (live tiles blocked). " + (statusEl.textContent || "");
      } else if (statusEl && window.__idsTilesOk && window.__idsTileSource) {
        statusEl.textContent = "Live tiles (" + window.__idsTileSource + "). " + (statusEl.textContent || "");
      }
"""
    # Insert before closing of renderMap — find setTimeout invalidateSize and add after pin status block
    anchor = "      setTimeout(function () { window.__idsMap.invalidateSize(); }, 80);"
    # Better: insert just before the final closing brace of renderMap by finding unique trailing bit
    # Find "Dealers without coordinates" style message end — use overseas note
    marker = "window.__idsMap.invalidateSize(); }, 80);"
    idx = html2.find(marker)
    if idx < 0:
        raise RuntimeError("invalidateSize anchor missing")
    # find end of status block after this — insert inject after the whole if(statusEl) that follows
    after = html2.find("\n    }\n\n    function ", idx)
    if after < 0:
        after = html2.find("\n    }\n\n    function setTab", idx)
    if after < 0:
        # try next function after renderMap
        after = html2.find("\n    function ", idx + 10)
        # go back to previous closing of renderMap
        after = html2.rfind("\n    }", idx, after if after > 0 else idx + 5000)
    if after < 0:
        raise RuntimeError("could not find end of renderMap")
    html2 = html2[:after] + "\n" + inject + html2[after:]

    MASTER.write_text(html2, encoding="utf-8")
    print("patched", MASTER, "size", MASTER.stat().st_size)


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    if not MASTER.exists():
        raise SystemExit(f"missing {MASTER}")
    if not LEAFLET_JS.exists():
        print("WARN: local leaflet.js missing at", LEAFLET_JS)

    vectors = build_vector_pack()
    street_url, street_bounds = build_street_image()
    init_js = build_map_init_js(vectors, street_url, street_bounds)
    patch_master(init_js)
    # Persist a small receipt for QA
    receipt = CACHE / "MASTER_MAP_TRIPLE_RECEIPT.json"
    receipt.write_text(
        json.dumps(
            {
                "master": str(MASTER),
                "bytes": MASTER.stat().st_size,
                "vector": {k: len(v["features"]) for k, v in vectors.items()},
                "street_data_url_chars": len(street_url),
                "street_bounds": street_bounds,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("receipt", receipt)


if __name__ == "__main__":
    main()
