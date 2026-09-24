#!/usr/bin/env python3
"""Bake an offline street basemap into a single-country IDS dealer-compare HTML.

Why this exists
---------------
The country files (Portugal, UK LCV, France, ...) carry no map picture. Online they fetch tiles
from Esri/CARTO/OSM; offline they show coloured pins on an empty background, and the copies inside
the v1.4 meeting packs cannot even load Leaflet (relative `../_ui/leaflet.js` + blocked CDN).

What it does
------------
1. Downloads one street-map picture of the country's bounding box from the same Esri service the
   file already uses, in Web Mercator so it lines up exactly with Leaflet's coordinate system.
2. Builds a three-layer map stack inside the file, same arrangement as the all-countries master:
      pane 150  baked street picture (offline basemap)
      pane 175  vector geography (land, borders, major roads, cities) from Natural Earth
      tilePane  live tiles when the network allows (Esri -> CARTO -> OSM failover)
   Everything is written into the HTML, so the file works with no internet and no `_ui` folder.
3. Re-requests map assets only if the cached copy is missing (idempotent rebuilds).

Usage
-----
    python bake_country_offline_map.py --country Portugal
    python bake_country_offline_map.py --country Portugal --rebuild
    python bake_country_offline_map.py --list

Backups are written once as `<file>.bak_<tag>`; they are never overwritten. Re-running the script
starts from the backup, so repeated runs cannot stack patches.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import re
import ssl
import sys
import urllib.request
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
IDS_DIR = ISZE / "02_dashboards" / "ids"
MEETINGS = ISZE / "09_meetings"
CACHE = ISZE / "01_data" / "90_INBOX" / "_ids_country_map_assets"
BOX_FILE = Path(__file__).with_name("ids_country_map_boxes.csv")
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/export"
CTX = ssl.create_default_context()
UA = {"User-Agent": "ISZE-IDS-country-map-build/1.0"}


def load_boxes() -> dict[str, tuple[float, float, float, float]]:
    """The one authored place a country's map frame is set. Hand-written on purpose: an automatic
    rule cut Sicily off Italy, Copenhagen off Denmark and half of Norway, because it treated
    islands and the far north as outliers."""
    import csv as _csv

    if not BOX_FILE.exists():
        raise SystemExit(f"missing {BOX_FILE}")
    out: dict[str, tuple[float, float, float, float]] = {}
    with BOX_FILE.open(newline="", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            name = (row.get("country") or "").strip()
            if not name or name.startswith("#"):
                continue
            out[name] = (
                float(row["west"]),
                float(row["south"]),
                float(row["east"]),
                float(row["north"]),
            )
    return out


# Extra degrees of pan allowed beyond the picture, so overseas pins stay reachable.
PAN_PAD_DEG = 3.0

# The map panel in the country files is about 1317 x 560 px, so it is roughly 2.35 : 1. A country
# box that is square (Greece) or tall (Israel) would fill only part of the panel, so the frame is
# widened around the country to bring its shape closer to the panel's. The widening is capped so a
# tall country (Norway) does not drag in half a continent and shrink itself to nothing; whatever
# shape results, the picture is drawn to that exact shape so the map is never distorted, and the
# view is then set to cover the panel.
PANEL_ASPECT = 560 / 1317  # height / width
WIDEN_CAP = 2.0

# Picture resolution, in megapixels. Roughly twice the panel's pixel count, so it stays sharp when
# the view is placed on the country; the shape follows the frame, so this is a size, not a shape.
PICTURE_MEGAPIXELS = 2.6e6
MIN_PICTURE_SIDE = 512
MAX_PICTURE_SIDE = 4096


def targets(country: str) -> list[Path]:
    """Every copy of a country file that needs to survive being opened on its own.

    First two: the working copies in 02_dashboards. The rest are the copies that get attached to
    mails or zipped into a meeting pack - those are the ones customers actually receive.
    """
    return [
        IDS_DIR / f"IDS_2026_dealer_compare_{country}.html",
        IDS_DIR / "IDS_all_dashboards_2026-08-19" / "02_country" / f"IDS_2026_dealer_compare_{country}.html",
        ISZE / "09_meetings" / "Imotors_Portugal_IDS_2026" / f"IDS_2026_dealer_compare_{country}.html",
        ISZE / "09_meetings" / "IDS_2026_Country_Packs_v1.4" / country / f"IDS_2026_dealer_compare_{country}.html",
        ISZE / "09_meetings" / "IDS_2026_MIDI_Packs" / country / f"IDS_2026_dealer_compare_{country}.html",
    ]


LEAFLET_JS = ISZE / "02_dashboards" / "_ui" / "leaflet.js"
LEAFLET_CSS = ISZE / "02_dashboards" / "_ui" / "leaflet.css"
LEAF_CSS_LINK_RE = re.compile(r'<link[^>]*href="[^"]*leaflet[^"]*\.css"[^>]*/?>\s*', re.IGNORECASE)
LEAF_JS_SRC_RE = re.compile(r'<script[^>]*src="[^"]*leaflet[^"]*\.js"[^>]*>\s*</script>\s*', re.IGNORECASE)


def inline_leaflet(html: str) -> tuple[str, bool]:
    """Put Leaflet inside the file. Without this a pack copy cannot draw a map at all, because
    ../_ui/leaflet.js does not exist inside a zip or an Outlook attachment cache."""
    if "../_ui/leaflet.js" not in html and "unpkg.com/leaflet" not in html:
        return html, False
    if not LEAFLET_JS.exists() or not LEAFLET_CSS.exists():
        raise RuntimeError(f"cannot inline Leaflet - missing {LEAFLET_JS} or {LEAFLET_CSS}")
    css = LEAFLET_CSS.read_text(encoding="utf-8")
    jsrc = LEAFLET_JS.read_text(encoding="utf-8")
    html = LEAF_CSS_LINK_RE.sub("", html)
    html = html.replace("</head>", f"<style>\n/* Leaflet 1.9.4 - inlined so this file works standalone */\n{css}\n</style>\n</head>", 1)
    html = LEAF_JS_SRC_RE.sub("", html)
    app = re.search(r"<script>\s*\n\s*(?:\(function|const|let|var|function)", html)
    block = f"<script>\n/* Leaflet 1.9.4 - inlined so this file works standalone */\n{jsrc}\n</script>\n"
    if app:
        html = html[: app.start()] + block + html[app.start() :]
    else:
        html = html.replace("</body>", block + "</body>", 1)
    return html, True


def fetch(url: str, dest: Path, rebuild: bool, timeout: int = 240) -> bytes:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 5000 and not rebuild:
        print(f"  cache hit  {dest.name}  ({dest.stat().st_size:,} bytes)")
        return dest.read_bytes()
    print(f"  GET {url[:110]}...")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"  -> {dest.name}  {len(data):,} bytes")
    return data


# ---------------------------------------------------------------- street picture

def mercator(lon: float, lat: float) -> tuple[float, float]:
    """WGS84 lon/lat -> Web Mercator metres, the projection Leaflet draws in."""
    r = 6378137.0
    return r * math.radians(lon), r * math.log(math.tan(math.pi / 4.0 + math.radians(lat) / 2.0))


def widen_to_panel(bbox) -> tuple[float, float, float, float]:
    """Widen a country box towards the panel's shape (about 2.35:1) around its centre.

    Leaflet draws in Mercator, so the shape is measured in projected metres. The widening is capped
    at WIDEN_CAP x the country's own width, so a tall narrow country is not shrunk into a thin
    stripe of a continent-wide frame. The picture is then drawn to whatever shape results, so the
    map is never stretched even when the cap applies.
    """
    w, s, e, n = bbox
    x_w, y_s = mercator(w, s)
    x_e, y_n = mercator(e, n)
    width_m, height_m = x_e - x_w, y_n - y_s
    target_w = height_m / PANEL_ASPECT
    add_w = target_w - width_m
    if add_w <= 0:  # already wider than the panel shape; leave it
        return bbox
    max_w = width_m * WIDEN_CAP
    add_w = min(add_w, max(0.0, max_w - width_m))
    half_deg = math.degrees(add_w / 2.0 / 6378137.0)
    return (round(w - half_deg, 3), s, round(e + half_deg, 3), n)


def picture_size(bbox) -> tuple[int, int]:
    """Pixel size matching the frame's projected shape, held to a pixel budget.

    The shape must follow the frame: Leaflet stretches the image to the bounds it is given, so a
    picture with a different shape would distort the map. That is what went wrong when the frame's
    widening was capped and the picture was still drawn at a fixed 2.35:1 - the map would have been
    squeezed horizontally on tall countries.
    """
    w, s, e, n = bbox
    x_w, y_s = mercator(w, s)
    x_e, y_n = mercator(e, n)
    aspect = (y_n - y_s) / (x_e - x_w)  # height / width, in projected metres
    height = round(math.sqrt(PICTURE_MEGAPIXELS * aspect))
    width = round(PICTURE_MEGAPIXELS / height)
    width = max(MIN_PICTURE_SIDE, min(MAX_PICTURE_SIDE, width))
    height = max(MIN_PICTURE_SIDE, min(MAX_PICTURE_SIDE, height))
    return width, height


def street_picture(country: str, bbox, rebuild: bool) -> tuple[str, list[list[float]]]:
    w, s, e, n = widen_to_panel(bbox)
    x_w, y_s = mercator(w, s)
    x_e, y_n = mercator(e, n)
    width, height = picture_size((w, s, e, n))
    url = (
        f"{ESRI}?bbox={x_w:.2f},{y_s:.2f},{x_e:.2f},{y_n:.2f}"
        f"&bboxSR=3857&imageSR=3857&size={width},{height}&format=jpg&f=image"
    )
    dest = CACHE / f"{country.lower()}_street_{width}x{height}_{int(w*10)}_{int(s*10)}.jpg"
    jpg = fetch(url, dest, rebuild)
    if jpg[:2] != b"\xff\xd8":
        raise RuntimeError(f"street picture is not a JPEG ({len(jpg)} bytes) - check bbox/url")
    data_url = "data:image/jpeg;base64," + base64.b64encode(jpg).decode("ascii")
    print(
        f"  picture {width}x{height} ({width * height / 1e6:.1f} MP) -> data-url {len(data_url):,} chars"
        f"  frame {w},{s},{e},{n}"
    )
    return data_url, [[s, w], [n, e]]


# ---------------------------------------------------------------- vector geography

def load_geojson(name: str, rebuild: bool) -> dict:
    return json.loads(fetch(f"{NE}/{name}", CACHE / name, rebuild).decode("utf-8"))


def in_box(lon: float, lat: float, bbox, pad: float) -> bool:
    w, s, e, n = bbox
    return (w - pad) <= lon <= (e + pad) and (s - pad) <= lat <= (n + pad)


def geom_hits(geom: dict, bbox, pad: float) -> bool:
    def walk(c) -> bool:
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            return in_box(float(c[0]), float(c[1]), bbox, pad)
        if isinstance(c, (list, tuple)):
            return any(walk(x) for x in c)
        return False

    return walk(geom.get("coordinates")) if geom else False


def thin(ring: list, step: int) -> list:
    if step <= 1 or len(ring) < 10:
        return ring
    out = ring[::step]
    if out[-1] != ring[-1]:
        out.append(ring[-1])
    return out


def simplify(geom: dict, step: int) -> dict:
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        return {"type": gtype, "coordinates": [thin(r, step) for r in coords]}
    if gtype == "MultiPolygon":
        return {"type": gtype, "coordinates": [[thin(r, step) for r in poly] for poly in coords]}
    if gtype == "LineString":
        return {"type": gtype, "coordinates": thin(coords, step)}
    if gtype == "MultiLineString":
        return {"type": gtype, "coordinates": [thin(c, step) for c in coords]}
    return geom


def features(fc: dict, keep) -> dict:
    return {"type": "FeatureCollection", "features": [f for f in fc.get("features", []) if keep(f)]}


def vector_pack(bbox, rebuild: bool) -> dict:
    land = features(load_geojson("ne_110m_land.geojson", rebuild),
                    lambda f: geom_hits(f.get("geometry") or {}, bbox, 3.0))

    borders = features(load_geojson("ne_110m_admin_0_countries.geojson", rebuild),
                       lambda f: geom_hits(f.get("geometry") or {}, bbox, 3.0))
    for f in borders["features"]:
        p = f.get("properties") or {}
        f["properties"] = {"name": p.get("NAME") or p.get("ADMIN") or "", "iso": p.get("ISO_A3") or ""}

    def keep_road(f: dict) -> bool:
        if not geom_hits(f.get("geometry") or {}, bbox, 1.0):
            return False
        p = f.get("properties") or {}
        try:
            sr = int(p.get("scalerank") if p.get("scalerank") is not None else 99)
        except Exception:  # noqa: BLE001
            sr = 99
        if sr <= 3:
            return True
        typ = str(p.get("type") or p.get("road") or "").lower()
        return any(k in typ for k in ("major", "primary", "motorway", "trunk", "highway"))

    roads = features(load_geojson("ne_10m_roads.geojson", rebuild), keep_road)
    roads["features"] = roads["features"][:1200]
    for f in roads["features"]:
        p = f.get("properties") or {}
        f["properties"] = {"name": p.get("name") or p.get("Name") or ""}
        f["geometry"] = simplify(f["geometry"], 3)

    def keep_place(f: dict) -> bool:
        g = f.get("geometry") or {}
        if g.get("type") != "Point":
            return False
        lon, lat = g["coordinates"][:2]
        if not in_box(float(lon), float(lat), bbox, 1.0):
            return False
        p = f.get("properties") or {}
        try:
            pop = float(p.get("POP_MAX") or p.get("pop_max") or 0)
        except Exception:  # noqa: BLE001
            pop = 0
        return pop >= 100000

    cities = features(load_geojson("ne_110m_populated_places.geojson", rebuild), keep_place)
    for f in cities["features"]:
        p = f.get("properties") or {}
        f["properties"] = {"name": p.get("NAME") or p.get("name") or "", "pop": p.get("POP_MAX") or 0}

    print(
        "  vector counts: "
        f"land={len(land['features'])} borders={len(borders['features'])} "
        f"roads={len(roads['features'])} cities={len(cities['features'])}"
    )
    return {"land": land, "borders": borders, "roads": roads, "cities": cities}


# ---------------------------------------------------------------- html patch

def js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


FIT_TEMPLATE_PREFIX = """      if (latLngs.length) {
"""

FIT_TEMPLATE_SUFFIX = """      } else {
        const b = window.__idsStreetBounds;
        if (b) {
          window.__idsMap.fitBounds(L.latLngBounds(b), { padding: [10, 10] });
        } else {
          window.__idsMap.setView([48.5, 10.0], 4);
        }
      }
"""

# Country files: open on the country's own framed area. Fitting to the dealer pins instead let a
# single overseas office wreck the view - France fitted to Guadeloupe and Reunion and opened at
# zoom 3, with the stored picture a 2% speck. The frame is the authored area for that country, so
# fitting to it fills the panel by construction; overseas pins stay reachable by panning.
FIT_BODY_LOCAL = """        window.__idsMap.fitBounds(L.latLngBounds(window.__idsStreetBounds), { animate: false });
        // fitBounds lands on the nearest whole zoom level, which can leave the framed area smaller
        // than the panel, so a strip of empty background shows through. Nudge in until the visible
        // area sits inside the frame, which is what makes the stored picture cover the panel. This
        // checks the actual result rather than trusting the arithmetic, so it holds whatever the
        // panel's shape happens to be.
        (function ensureCover() {
          const b = window.__idsStreetBounds;
          for (let i = 0; i < 20; i++) {
            const v = window.__idsMap.getBounds();
            if (v.getSouth() >= b[0][0] && v.getWest() >= b[0][1] &&
                v.getNorth() <= b[1][0] && v.getEast() <= b[1][1]) {
              window.__idsCoverAttempts = i;
              return;
            }
            window.__idsMap.setZoom(window.__idsMap.getZoom() + 0.2, { animate: false });
          }
          window.__idsCoverAttempts = -1;
        })();
"""

# The network-wide file's routine, kept: it deliberately stops the Azores and Canaries from
# forcing a world view, and that reasoning still holds.
FIT_BODY_NETWORK = """        // Always fit to the core of the network, never let an overseas dealer force a world view.
        const EUROPE_CORE = latLngs.filter(
          (ll) => ll.lat >= 28 && ll.lat <= 72 && ll.lng >= -12 && ll.lng <= 40
        );
        const fit = EUROPE_CORE.length >= 3 ? EUROPE_CORE : latLngs;
        window.__idsMap.fitBounds(L.latLngBounds(fit), { padding: [36, 36] });
"""


def fit_pattern() -> re.Pattern:
    """Match the existing fit block: from `if (latLngs.length) {` through to the else-branch that
    sets the Europe-wide view, so the whole block can be replaced."""
    return re.compile(
        r'if \(latLngs\.length\) \{.*?\n      \} else \{\s*\n\s*window\.__idsMap\.setView\(\[48\.5, 10\.0\], 4\);\s*\n      \}',
        re.S,
    )


def map_init_js(vectors: dict, street_url: str, street_bounds) -> str:
    return f"""
        window.__idsMap = L.map("ids-map", {{
          scrollWheelZoom: true,
          maxBoundsViscosity: 0.85,
          // Leaflet snaps to whole zoom levels by default, so fitBounds rounds down and the stored
          // picture ends up smaller than the panel (as little as a quarter of it). Allowing
          // fractional zoom lets the frame fit the panel exactly.
          zoomSnap: 0,
          zoomDelta: 0.5,
        }});

        // Layer stack, bottom to top: baked street picture (150), vector geography (175),
        // live tiles (200), dealer pins (600). Below Leaflet's tile pane so live tiles win.
        window.__idsMap.createPane("streetPane");
        window.__idsMap.getPane("streetPane").style.zIndex = 150;
        window.__idsMap.createPane("vectorPane");
        window.__idsMap.getPane("vectorPane").style.zIndex = 175;

        // --- (1) Street basemap baked into this file: works with no internet ---
        const streetBounds = {js(street_bounds)};
        window.__idsStreetBounds = streetBounds;
        window.__idsStreetLayer = L.imageOverlay(
          {js(street_url)},
          streetBounds,
          {{ pane: "streetPane", opacity: 1, interactive: false,
             attribution: "Basemap &copy; Esri (offline snapshot)" }}
        ).addTo(window.__idsMap);
        try {{
          const w = streetBounds[0][1] - {PAN_PAD_DEG}, s = streetBounds[0][0] - {PAN_PAD_DEG};
          const e = streetBounds[1][1] + {PAN_PAD_DEG}, n = streetBounds[1][0] + {PAN_PAD_DEG};
          window.__idsMap.setMaxBounds(L.latLngBounds([[s, w], [n, e]]));
        }} catch (e) {{}}

        // --- (2) Vector geography baked into this file: borders, major roads, cities ---
        const IDS_VECTOR = {{
          land: {js(vectors["land"])},
          borders: {js(vectors["borders"])},
          roads: {js(vectors["roads"])},
          cities: {js(vectors["cities"])}
        }};
        window.__idsVectorLand = L.geoJSON(IDS_VECTOR.land, {{
          pane: "vectorPane", interactive: false,
          style: {{ color: "#8a9bb0", weight: 0.4, fillColor: "#efe8dc", fillOpacity: 0.12 }}
        }}).addTo(window.__idsMap);
        window.__idsVectorBorders = L.geoJSON(IDS_VECTOR.borders, {{
          pane: "vectorPane", interactive: false,
          style: {{ color: "#4a5d73", weight: 1.1, fillOpacity: 0 }}
        }}).addTo(window.__idsMap);
        window.__idsVectorRoads = L.geoJSON(IDS_VECTOR.roads, {{
          pane: "vectorPane", interactive: false,
          style: {{ color: "#c4a574", weight: 1.15, opacity: 0.85 }}
        }}).addTo(window.__idsMap);
        window.__idsVectorCities = L.geoJSON(IDS_VECTOR.cities, {{
          pane: "vectorPane", interactive: false,
          pointToLayer: function (feature, latlng) {{
            const nm = (feature.properties && feature.properties.name) || "";
            return L.circleMarker(latlng, {{
              radius: 2.4, color: "#1a2744", weight: 1, fillColor: "#f7f4ee", fillOpacity: 0.95
            }}).bindTooltip(nm, {{ direction: "top", opacity: 0.9, className: "ids-map-tooltip" }});
          }}
        }}).addTo(window.__idsMap);

        // --- (3) Live street tiles when the network allows ---
        const BASEMAPS = [
          {{
            name: "Esri streets",
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}",
            opts: {{ maxZoom: 19, attribution: "Tiles &copy; Esri" }}
          }},
          {{
            name: "CARTO Voyager",
            url: "https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png",
            opts: {{ maxZoom: 18, subdomains: "abcd",
              attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>' }}
          }},
          {{
            name: "OpenStreetMap",
            url: "https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
            opts: {{ maxZoom: 19,
              attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }}
          }}
        ];
        function idsTileStatus(warn) {{
          const el = document.getElementById("ids-tile-status");
          if (!el) return;
          if (warn) el.classList.add("warn"); else el.classList.remove("warn");
          const base = window.__idsPinNote || "";
          el.textContent = window.__idsTileNote ? (window.__idsTileNote + (base ? " " + base : "")) : base;
        }}
        function onTilesLive(name) {{
          window.__idsTilesOk = true;
          window.__idsTileFailed = false;
          if (window.__idsStreetLayer) window.__idsStreetLayer.setOpacity(0.15);
          if (window.__idsVectorLand) window.__idsVectorLand.setStyle({{ fillOpacity: 0.08, opacity: 0.35 }});
          if (window.__idsVectorRoads) window.__idsVectorRoads.setStyle({{ opacity: 0.25 }});
          window.__idsTileNote = "Live street tiles (" + name + "). Offline street picture stays as backup.";
          idsTileStatus(false);
        }}
        function onTilesDead() {{
          window.__idsTilesOk = false;
          window.__idsTileFailed = true;
          if (window.__idsStreetLayer) window.__idsStreetLayer.setOpacity(1);
          if (window.__idsVectorLand) window.__idsVectorLand.setStyle({{ fillOpacity: 0, opacity: 0 }});
          if (window.__idsVectorBorders) window.__idsVectorBorders.setStyle({{ opacity: 0.9, weight: 1.2 }});
          if (window.__idsVectorRoads) window.__idsVectorRoads.setStyle({{ opacity: 0.7 }});
          window.__idsTileNote = "No internet - showing the street map stored inside this file, with borders, roads and cities.";
          idsTileStatus(true);
        }}
        function attachBasemap(i) {{
          if (i >= BASEMAPS.length) {{ onTilesDead(); return; }}
          const spec = BASEMAPS[i];
          const layer = L.tileLayer(spec.url, spec.opts);
          let loaded = false, errors = 0, switched = false;
          function failOver() {{
            if (switched || loaded) return;
            switched = true;
            try {{ window.__idsMap.removeLayer(layer); }} catch (e) {{}}
            attachBasemap(i + 1);
          }}
          layer.on("load", function () {{ loaded = true; onTilesLive(spec.name); }});
          layer.on("tileerror", function () {{ errors += 1; if (!loaded && errors >= 4) failOver(); }});
          setTimeout(function () {{ if (!loaded) failOver(); }}, 2200);
          layer.addTo(window.__idsMap);
          window.__idsTileLayer = layer;
        }}
        attachBasemap(0);
        window.__idsMapLayer = L.layerGroup().addTo(window.__idsMap);
"""


INIT_BLOCK_RE = re.compile(
    r'if \(!window\.__idsMap\) \{\s*'
    r'window\.__idsMap = L\.map\("ids-map", \{ scrollWheelZoom: true \}\);'
    r'.*?'
    r'window\.__idsMapLayer = L\.layerGroup\(\)\.addTo\(window\.__idsMap\);\s*\}',
    re.S,
)

# full "if (statusEl) { ... }" block inside renderMap, which sets the dealer count line
PIN_STATUS_RE = re.compile(
    r'if \(statusEl\) \{\s*(?:if \(!window\.__idsTileFailed\) )?statusEl\.classList\.remove\("warn"\);'
    r'.*?\n      \}',
    re.S,
)


def write_with_retry(path: Path, text: str, attempts: int = 6) -> None:
    """Write the file, retrying briefly on a Windows lock.

    A plain write to a file in a synced folder (SharePoint / OneDrive) or one being scanned by
    antivirus can fail with OSError errno 22 part way through a long loop. Retrying that is safe;
    the content is identical every time.
    """
    import time

    for attempt in range(1, attempts + 1):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError as exc:
            if attempt == attempts:
                raise
            print(f"    write to {path.name} failed ({exc}); retry {attempt}/{attempts - 1}")
            time.sleep(0.8 * attempt)


def patch_file(path: Path, init_js: str, tag: str, local_fit: bool = True) -> dict:
    backup = path.with_suffix(path.suffix + f".bak_{tag}")
    # always start from the clean backup, so re-runs cannot stack patches
    source = backup if backup.exists() else path
    html = source.read_text(encoding="utf-8")
    if not backup.exists():
        backup.write_text(html, encoding="utf-8")
    before = len(html)

    html, inlined = inline_leaflet(html)

    html, n_init = INIT_BLOCK_RE.subn("if (!window.__idsMap) {" + init_js + "\n      }", html, count=1)
    if n_init != 1:
        raise RuntimeError(f"{path.name}: map init block matched {n_init} times - file layout changed")

    def replace_pin_status(m: re.Match) -> str:
        block = m.group(0)
        # quiet the warn, remember the pin line, then let the layer note sit on top of it
        block = block.replace(
            'if (!window.__idsTileFailed) statusEl.classList.remove("warn");',
            'if (!window.__idsTileFailed) statusEl.classList.remove("warn");',
        )
        block = block.rstrip("}")
        block += (
            '\n        window.__idsPinNote = statusEl.textContent || "";'
            '\n        if (typeof idsTileStatus === "function") idsTileStatus(window.__idsTileFailed === true);'
            '\n      }'
        )
        return block

    html, n_status = PIN_STATUS_RE.subn(replace_pin_status, html, count=1)
    if n_status != 1:
        raise RuntimeError(f"{path.name}: pin status block matched {n_status} times")

    # Open the map on the country, not on all of Europe. Without this the stored picture is a small
    # patch in the middle of a mostly empty panel, because the file was built to start at zoom 4.
    body = FIT_BODY_LOCAL if local_fit else FIT_BODY_NETWORK
    new_fit = FIT_TEMPLATE_PREFIX + body + FIT_TEMPLATE_SUFFIX
    html, n_fit = fit_pattern().subn(lambda _m: new_fit, html, count=1)
    if n_fit != 1:
        raise RuntimeError(f"{path.name}: map fit block matched {n_fit} times")

    html = html.replace(
        "Map tiles require an internet connection. Dealers without coordinates stay in the tables only.",
        "This page carries its own street map, so it works with no internet. Three layers: live "
        "street tiles when the network allows, a street picture stored inside the file, and drawn "
        "borders, roads and cities. Dealers without coordinates stay in the tables only.",
    )
    html = html.replace(
        "#ids-map { width:100%; height:520px; border-radius:8px; border:1px solid var(--mid); background:#eef1f5; }",
        "#ids-map { width:100%; height:520px; border-radius:8px; border:1px solid var(--mid); background:#b9cfe0; }",
    )
    html = html.replace(
        '<p class="tile-note" id="ids-tile-status">Open the Map tab to load tiles',
        '<p class="tile-note" id="ids-tile-status">Open the Map tab to draw the map',
    )
    html = re.sub(
        r"<script>\s*/\*[^*]*\*/\s*if \(typeof L === \"undefined\"\)\s*\{.*?\}\s*</script>\s*",
        "",
        html,
        flags=re.S | re.IGNORECASE,
    )

    write_with_retry(path, html)
    return {
        "file": str(path),
        "bytes_before": before,
        "bytes_after": len(html),
        "leaflet_inlined": inlined,
        "backup": str(backup),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default=None, help="one country, or omit for every country in the box file")
    ap.add_argument("--rebuild", action="store_true", help="re-download cached map assets")
    ap.add_argument("--tag", default="20260924_offline_map")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    boxes = load_boxes()
    if args.list:
        for c, b in boxes.items():
            print(f"{c:<12} {b}")
        return 0

    if args.country:
        if args.country not in boxes:
            raise SystemExit(
                f"no authored map frame for {args.country!r}. Add it to {BOX_FILE.name} "
                f"(west,south,east,north) after checking the dealer coordinate range."
            )
        todo = [args.country]
    else:
        todo = list(boxes)

    CACHE.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    for country in todo:
        bbox = boxes[country]
        files = [p for p in targets(country) if p.exists()]
        if not files:
            print(f"{country}: no compare file found - skipped")
            continue
        print(f"{country}: frame {bbox}  ({len(files)} copy/copies)")

        vectors = vector_pack(bbox, args.rebuild)
        street_url, street_bounds = street_picture(country, bbox, args.rebuild)
        init_js = map_init_js(vectors, street_url, street_bounds)

        for p in files:
            is_network_file = p.stem == "IDS_2026_dealer_compare"
            r = patch_file(p, init_js, args.tag, local_fit=not is_network_file)
            print(
                f"  patched {Path(r['file']).name} in {Path(r['file']).parent.name}: "
                f"{r['bytes_before']:,} -> {r['bytes_after']:,} bytes"
                f"{'  (Leaflet inlined)' if r['leaflet_inlined'] else ''}"
            )
            results.append(r)

    receipt = CACHE / "OFFLINE_MAP_BUILD_RECEIPT.json"
    receipt.write_text(
        json.dumps(
            {
                "countries": todo,
                "boxes": {c: boxes[c] for c in todo},
                "files_patched": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\npatched {len(results)} file(s)")
    print("receipt", receipt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
