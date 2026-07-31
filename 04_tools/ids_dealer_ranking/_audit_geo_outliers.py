#!/usr/bin/env python3
"""Audit IDS dealer geo for ocean / wrong-continent outliers."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ids_dealer_geo import _COUNTRY_CENTRE, _haversine_km  # noqa: E402

# Approximate mainland bounding boxes (min_lat, max_lat, min_lon, max_lon)
# Generous to include islands that belong to the country.
_BOUNDS: dict[str, tuple[float, float, float, float]] = {
    "Portugal": (36.8, 42.3, -9.6, -6.0),  # mainland; Açores checked separately
    "Spain": (27.5, 44.0, -18.5, 5.0),
    "France": (41.0, 51.5, -5.5, 10.0),  # metro; DOM flagged separately
    "Italy": (36.0, 47.5, 6.5, 19.0),
    "Switzerland": (45.7, 47.9, 5.8, 10.6),
    "Belgium": (49.4, 51.6, 2.4, 6.5),
    "Netherlands": (50.7, 53.7, 3.2, 7.3),
    "Luxembourg": (49.4, 50.2, 5.7, 6.6),
    "Benelux": (49.4, 53.7, 2.4, 7.3),
    "Poland": (49.0, 55.0, 14.0, 24.5),
    "Denmark": (54.5, 57.9, 8.0, 15.3),
    "Norway": (57.8, 71.5, 4.5, 31.5),
    "Greece": (34.7, 41.8, 19.3, 29.7),
    "Hungary": (45.7, 48.6, 16.0, 23.0),
    "Romania": (43.5, 48.3, 20.0, 30.0),
    "Israel LCV": (29.4, 33.4, 34.2, 35.9),
    "UK CV": (49.8, 61.0, -8.5, 2.0),
    "UK LCV": (49.8, 61.0, -8.5, 2.0),
    "Cyprus": (34.5, 35.8, 32.0, 34.8),
    "Malta": (35.7, 36.1, 14.1, 14.6),
}


def load_dealers(html: Path) -> list[dict]:
    text = html.read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\s*(?:const|let|var|function|//|\n\s*</script>)", text, re.S)
    if not m:
        # fallback: greedy between const DATA = and ;\n
        m = re.search(r"const DATA = (\{.*\});", text, re.S)
    if not m:
        raise SystemExit("DATA blob not found")
    data = json.loads(m.group(1))
    return data.get("dealers") or []


def main() -> int:
    dealers = load_dealers(HTML)
    by_c: dict[str, list] = defaultdict(list)
    oceanish = []
    oob = []
    for d in dealers:
        g = d.get("geo") or {}
        lat, lon = g.get("lat"), g.get("lon")
        if lat is None or lon is None:
            continue
        c = d.get("country") or "?"
        by_c[c].append(d)
        # Rough "in ocean / wrong hemisphere" heuristics for Europe IDS
        if lon < -25 or lon > 45 or lat < 25 or lat > 72:
            # allow French DOM / Açores / Canaries somewhat
            if not any(x in (g.get("place") or "").upper() for x in ("ACORES", "AÇORES", "MADEIRA", "CANAR", "REUNION", "GUADELOUPE", "MARTINIQUE", "GUYANE", "MAYOTTE")):
                oceanish.append((c, d.get("name"), lat, lon, g.get("place"), g.get("label") or g.get("source")))
        bounds = _BOUNDS.get(c)
        if bounds:
            lo_la, hi_la, lo_lo, hi_lo = bounds
            if not (lo_la <= lat <= hi_la and lo_lo <= lon <= hi_lo):
                # France DOM / Portugal Açores exceptions
                place = (g.get("place") or "").upper()
                if c == "France" and any(x in place for x in ("REUNION", "GUADELOUPE", "MARTINIQUE", "GUYANE", "MAYOTTE", "TAHITI", "NOUMEA")):
                    continue
                if c == "Portugal" and any(x in place for x in ("ANGRA", "PONTA", "FUNCHAL", "ACORES", "AÇORES", "MADEIRA")):
                    continue
                if c == "Spain" and any(x in place for x in ("PALMAS", "TENERIFE", "CANAR", "PALMA", "MALLORCA", "IBIZA")):
                    continue
                oob.append((c, d.get("name"), lat, lon, g.get("place"), g.get("label") or g.get("source")))

    print(f"dealers with geo: {sum(len(v) for v in by_c.values())} / {len(dealers)}")
    print("\n=== Far from Europe box (possible wrong coords) ===")
    for row in sorted(oceanish, key=lambda x: (x[0], x[1] or ""))[:40]:
        print(f"  {row[0]:15} {row[1][:40]:40} lat={row[2]:.3f} lon={row[3]:.3f} place={row[4]} src={row[5]}")
    print(f"  total far: {len(oceanish)}")

    print("\n=== Outside country mainland bounds ===")
    by_oob = defaultdict(list)
    for row in oob:
        by_oob[row[0]].append(row)
    for c, rows in sorted(by_oob.items(), key=lambda x: -len(x[1])):
        print(f"\n{c}: {len(rows)} oob")
        for row in rows[:8]:
            print(f"  {row[1][:45]:45} lat={row[2]:.3f} lon={row[3]:.3f} place={row[4]} src={row[5]}")

    # Cluster densest 50km cells globally
    print("\n=== Global 5-degree cells (top clusters) ===")
    cells = Counter()
    cell_ex = defaultdict(list)
    from collections import Counter
    cells = Counter()
    for d in dealers:
        g = d.get("geo") or {}
        if g.get("lat") is None:
            continue
        key = (round(g["lat"] / 5) * 5, round(g["lon"] / 5) * 5)
        cells[key] += 1
        if len(cell_ex[key]) < 3:
            cell_ex[key].append((d.get("country"), d.get("name"), g.get("lat"), g.get("lon"), g.get("place")))
    for (la, lo), n in cells.most_common(12):
        print(f"  cell~({la},{lo}) n={n}")
        for ex in cell_ex[(la, lo)]:
            print(f"    {ex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
