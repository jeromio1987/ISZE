#!/usr/bin/env python3
"""Full per-country geo health audit on rebuilt dealer compare HTML."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ids_dealer_geo import (  # noqa: E402
    _COUNTRY_BOUNDS,
    _coords_in_country_bounds,
    _haversine_km,
    _is_verified_dom_tom,
    sanity_check_geo_clustering,
)


def load_data(html: Path) -> dict:
    text = html.read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\s*(?:const|let|var|function|//|\n\s*</script>)", text, re.S)
    if not m:
        m = re.search(r"const DATA = (\{.*\});", text, re.S)
    if not m:
        raise SystemExit("DATA not found")
    return json.loads(m.group(1))


def main() -> int:
    data = load_data(HTML)
    dealers = data["dealers"]
    by: dict[str, list] = defaultdict(list)
    for d in dealers:
        by[d.get("country") or "?"].append(d)

    print(f"HTML: {HTML}")
    print(f"dealers={len(dealers)} countries={len(by)}")
    print()
    print(f"{'Country':<16} {'n':>3} {'map':>3} {'excl':>4} {'city':>4} {'fb':>3} {'places':>6} {'oob':>3} {'status'}")
    print("-" * 72)

    problems = []
    for c in sorted(by):
        rows = by[c]
        pinned = [d for d in rows if (d.get("geo") or {}).get("lat") is not None]
        on_map = [d for d in pinned if not (d.get("geo") or {}).get("map_exclude")]
        excl = [d for d in pinned if (d.get("geo") or {}).get("map_exclude")]
        city = sum(
            1
            for d in pinned
            if "country centre" not in ((d.get("geo") or {}).get("geo_label") or "")
        )
        fb = len(pinned) - city
        places = {
            ((d.get("geo") or {}).get("place") or "").strip()
            for d in on_map
            if (d.get("geo") or {}).get("place")
        }
        places.discard("")

        oob = []
        for d in on_map:
            g = d["geo"]
            la, lo = float(g["lat"]), float(g["lon"])
            if _is_verified_dom_tom(place=g.get("place"), lat=la, lon=lo):
                continue  # French DOM-TOM OK on map
            # Europe/Israel box for map
            if lo < -12 or lo > 40 or la < 28 or la > 72:
                if c == "Portugal" and -32 <= lo <= -6 and 32 <= la <= 40:
                    continue
                if c == "Spain" and -19 <= lo <= -13 and 27 <= la <= 30:
                    continue
                oob.append(d)
                continue
            if c in _COUNTRY_BOUNDS and not _coords_in_country_bounds(la, lo, c):
                if c == "Portugal" and -32 <= lo <= -6 and 32 <= la <= 40:
                    continue
                if c == "Spain" and -19 <= lo <= -13 and 27 <= la <= 30:
                    continue
                oob.append(d)

        # cluster share on map
        coords = [(float(d["geo"]["lat"]), float(d["geo"]["lon"])) for d in on_map]
        cluster_max = 0
        for i, (la, lo) in enumerate(coords):
            near = sum(1 for lb, lob in coords if _haversine_km(la, lo, lb, lob) <= 10)
            cluster_max = max(cluster_max, near)
        share = (cluster_max / len(coords)) if coords else 0

        status = "OK"
        if oob:
            status = "OOB"
            problems.append((c, "oob", oob))
        elif len(on_map) >= 5 and share >= 0.5 and len(places) <= 2:
            status = "BLOB"
            problems.append((c, "blob", on_map))
        elif len(on_map) >= 5 and fb / max(1, len(pinned)) >= 0.5:
            status = "WARN-fb"
            problems.append((c, "fallback", []))

        print(
            f"{c:<16} {len(rows):3d} {len(on_map):3d} {len(excl):4d} {city:4d} {fb:3d} "
            f"{len(places):6d} {len(oob):3d} {status}"
        )
        if excl:
            for d in excl:
                g = d["geo"]
                print(f"    EXCL {d['name'][:40]:40} {g.get('place')} ({g['lat']:.2f},{g['lon']:.2f})")
        if oob:
            for d in oob[:5]:
                g = d["geo"]
                print(f"    OOB  {d['name'][:40]:40} {g.get('place')} ({g['lat']:.2f},{g['lon']:.2f}) {g.get('geo_label')}")

    # Sofia check
    sofia = [d for d in dealers if "Sofia" in (d.get("name") or "")]
    print("\nSofia France Auto geo:", [(d["name"], d.get("geo")) for d in sofia])

    san = sanity_check_geo_clustering(dealers)
    print("\nAutomated sanity:", "PASS" if san["ok"] else "FAIL")
    for e in san.get("errors") or []:
        print("  FAIL:", e)
    for w in san.get("warnings") or []:
        print("  WARN:", w)

    print("\nPROBLEMS:", len(problems))
    return 0 if not any(p[1] == "oob" for p in problems) and san["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
