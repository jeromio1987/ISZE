#!/usr/bin/env python3
"""Truck geometry: four side-profile vehicles with clickable zones.

Coordinates are in truck units: x runs 0 (front) to ~104 (rear), y runs 0
(ground) upward. Every vehicle is drawn at ONE shared scale, so the D-Max
reads smaller than the F-Series rather than all four looking the same size.

The zones tile the silhouette: five positional zones plus the electrical layer,
which is deliberately an overlay because a sensor or a loom is not in one place
on a truck.

The build rasterises its own output and reports any point inside the silhouette
that no zone covers (a gap) or that two zones both claim (an overlap, the
electrical overlay excluded because it is a layer). Gaps and overlaps in the
positional zones are a defect, not a style choice.

Realism comes from three things the page does with this data, not from more
polygons here: the zones are extruded into 3D and shown from a three-quarter
camera, the body is a neutral material with shading and the zone colour only
appears on hover or click, and the wheels sit in dark recesses drawn over the
body. That last one gives the wheel-arch look without carving the tiling, which
would put the coverage check at risk for no visual gain.

Writes vehicle_geometry.json next to this file.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "vehicle_geometry.json"


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def sq(x, y, s):
    return rect(x, y, x + s, y + s)


# ---------------------------------------------------------------------------
# D-Max: pickup. Bonnet, a cab with a raked windscreen, a load bed behind.
# ---------------------------------------------------------------------------
DMAX = {
    "outline": [[0, 4], [0, 13], [2, 13.5], [15, 14], [17, 14], [21, 24],
                [22, 29.5], [52, 30], [54, 22], [54, 10], [98, 21], [100, 10], [100, 4]],
    "zones": {
        "front":   [[[0, 4], [6, 4], [6, 13.93], [2, 13.5], [0, 13]]],
        "engine":  [[[6, 10], [15, 10], [15, 14], [6, 13.93]]],
        "cab":     [[[15, 10], [15, 14], [17, 14], [21, 24], [22, 29.5], [52, 30],
                     [54, 22], [54, 10]]],
        "chassis": [[[6, 4], [100, 4], [100, 10], [6, 10]]],
        "rear":    [[[54, 10], [54, 22], [98, 21], [100, 10]]],
        "elec":    [sq(9, 10.4, 3.5), sq(30, 10.4, 3.5), sq(62, 10.4, 3.5),
                    sq(90, 10.4, 3.5)],
    },
    "anchors": {
        "front":   [3.5, 12, -1, -0.2],
        "engine":  [10.5, 12, -0.5, 1],
        "cab":     [34, 22, 0, -1],
        "chassis": [55, 7, -0.35, 1],
        "rear":    [76, 15, 1, -0.5],
        "elec":    [40, 12, 1, 1],
    },
    "details": {
        "wheels": [[17.5, 5.4, 5.4, 2.6], [82, 5.4, 5.4, 2.6]],
        "glass": [[21.8, 24.4], [24.2, 29.3], [29.5, 29.4], [26.2, 24.4]],
        "sideGlass": [[30.5, 24.4], [53.6, 25.0], [53.6, 29.4], [31.0, 29.4]],
        "panelLines": [[[19.8, 11], [19.8, 24.2]], [[19.8, 24.2], [21.8, 24.2]],
                       [[54.2, 10.6], [54.2, 29.6]]],
        "doorHandle": [[23.2, 23.0], [26.4, 23.0]],
        "bedRails": [[54.6, 10.9], [97.6, 10.9]],
        "fuelCap": [66.5, 8.2],
    },
}

# ---------------------------------------------------------------------------
# Cab-over trucks: NLR, NMR, FRR. A tall flat front, a cab, then a cargo box.
# Shared construction at three sizes.
# ---------------------------------------------------------------------------
def cabover(key, o, front_x, cab_x, box_x, top, rail, fr, rr, wr, wy):
    """Build the five positional zones and the electrical overlay.

    o is the outline: o[1] is the top of the vertical nose face, o[2] the cab
    front top, o[3] the roof start, o[4] the box top front. The cab polygon runs
    from the nose face, up the front slope, across the cab roof and up the short
    roof slope to the box, so nothing is left uncovered behind the cab.
    """
    n1y = o[1][1]      # top of the vertical nose face
    c2x, c2y = o[2]    # cab front top
    c3x, c3y = o[3]    # roof start
    c4x, c4y = o[4]    # box top front
    cab_base = rail + 10   # the cab floor line: the engine sits below it

    z = {
        "front": [[[0, 4], [front_x, 4], [front_x, cab_base], [0, cab_base]]],
        "engine": [[[front_x, 4], [cab_x, 4], [cab_x, cab_base],
                    [front_x, cab_base]]],
        "cab": [[[0, cab_base], [0, n1y], [c2x, c2y], [c3x, c3y], [c4x, c4y],
                 [c4x, cab_base]]],
        "chassis": [[[cab_x, 4], [box_x, 4], [box_x, rail], [cab_x, rail]]],
        "rear": [[[cab_x, rail], [box_x, rail], [box_x, c4y], [cab_x, c4y]]],
        "elec": [sq(3.0, cab_base + 2, 3.5), sq(cab_x - 8.0, rail + 3, 3.5),
                 sq(cab_x + 18.0, rail + 3, 3.5), sq(box_x - 14.0, rail + 3, 3.5)],
    }
    a = {
        "front": [front_x * 0.5, rail + 5, -1, -0.2],
        "engine": [front_x + 4, rail - 4, -0.4, 1],
        "cab": [cab_x * 0.55, c3y - 6, -0.2, -1],
        "chassis": [(cab_x + box_x) / 2, rail - 4, -0.2, 1],
        "rear": [(cab_x + box_x) / 2, c4y - 6, 1, -0.2],
        "elec": [cab_x + 14, rail + 8, 1, 1],
    }
    det = {
        "wheels": [[fr, wy, wr, 2.8], [rr, wy, wr, 2.8], [rr + 7.0, wy, wr, 2.8]],
        "bodyBottom": 4.0,
        "glass": [[1.2, c2y - 3.6], [c3x - 5.0, c3y - 3.2],
                  [c3x - 5.0, c3y - 9.6], [1.2, c2y - 10.0]],
        "panelLines": [[[cab_x - 1.0, rail], [cab_x - 1.0, c3y - 1]],
                       [[box_x - 0.6, rail], [box_x - 0.6, c4y - 1]]],
        "doorHandle": [[cab_x - 7.5, cab_base + 5], [cab_x - 4.5, cab_base + 5]],
        "grilleLines": [[0.6, cab_base - 3], [front_x - 0.6, cab_base - 3]],
    }
    return {"outline": o, "zones": z, "anchors": a, "details": det}


NLR = cabover(
    "nlr",
    [[0, 4], [0, 30], [1.5, 36], [22, 36.5], [24, 41], [94, 41], [94, 4]],
    front_x=7.0, cab_x=24.0, box_x=94.0, top=41.0, rail=12.0,
    fr=13.0, rr=78.0, wr=6.5, wy=6.6,
)

NMR = cabover(
    "nmr",
    [[0, 4], [0, 33], [1.5, 39], [24, 39.5], [26, 46], [98, 46], [98, 4]],
    front_x=8.0, cab_x=26.0, box_x=98.0, top=46.0, rail=13.0,
    fr=14.0, rr=80.0, wr=7.5, wy=7.6,
)

FRR = cabover(
    "frr",
    [[0, 4], [0, 36], [1.5, 43], [27, 43.5], [29, 50], [104, 50], [104, 4]],
    front_x=9.0, cab_x=29.0, box_x=104.0, top=50.0, rail=14.0,
    fr=15.0, rr=86.0, wr=8.5, wy=8.6,
)

VEHICLES = {"dmax": DMAX, "nlr": NLR, "nmr": NMR, "frr": FRR}
POSITIONAL = ["front", "cab", "engine", "chassis", "rear"]


def in_poly(px, py, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y1 > py) != (y2 > py):
            xin = (x2 - x1) * (py - y1) / (y2 - y1) + x1
            if px < xin:
                inside = not inside
    return inside


def zone_claims(poly_groups, px, py):
    """zones[z] is a list of polygons; a point is in the zone if it is in any of them."""
    for poly in poly_groups:
        if in_poly(px, py, poly):
            return True
    return False


def coverage_report(name, veh, step=0.3):
    o = veh["outline"]
    xs = [p[0] for p in o]
    ys = [p[1] for p in o]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    gaps, overlaps, inside = [], [], 0
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            if in_poly(x, y, o):
                inside += 1
                hits = [z for z in POSITIONAL if zone_claims(veh["zones"][z], x, y)]
                if not hits:
                    gaps.append((round(x, 1), round(y, 1)))
                elif len(hits) > 1:
                    overlaps.append((round(x, 1), round(y, 1), hits))
            y += step
        x += step
    return {
        "vehicle": name,
        "points_inside": inside,
        "gap_points": len(gaps),
        "overlap_points": len(overlaps),
        "gap_examples": gaps[:6],
        "overlap_examples": overlaps[:6],
        "gap_pct": round(100 * len(gaps) / inside, 3) if inside else 0.0,
        "overlap_pct": round(100 * len(overlaps) / inside, 3) if inside else 0.0,
    }


def wheel_report(name, veh):
    """Every wheel must land inside a positional zone, or the arch recess will
    be drawn over nothing. Also reports how much of each wheel the body hides,
    which is what makes a wheel look seated rather than stuck on."""
    out = {"vehicle": name, "wheels": []}
    for w in veh["details"]["wheels"]:
        cx, cy, r = w[0], w[1], w[2]
        covered = 0
        total = 0
        for a in range(0, 360, 5):
            px = cx + r * 0.7 * math.cos(math.radians(a))
            py = cy + r * 0.7 * math.sin(math.radians(a))
            total += 1
            if zone_claims(veh["outline"] and [veh["outline"]], px, py):
                covered += 1
        out["wheels"].append({
            "x": cx, "r": r,
            "in_body_pct": round(100 * covered / total, 1) if total else 0.0,
        })
    return out


def main() -> int:
    reports = [coverage_report(k, v) for k, v in VEHICLES.items()]
    wheels = [wheel_report(k, v) for k, v in VEHICLES.items()]

    allx, ally = [], []
    for v in VEHICLES.values():
        for p in v["outline"]:
            allx.append(p[0])
            ally.append(p[1])

    OUT.write_text(json.dumps({
        "vehicles": VEHICLES,
        "bounds": {"x0": min(allx), "x1": max(allx), "y0": min(ally), "y1": max(ally)},
        "positional": POSITIONAL,
        "coverage": reports,
        "wheels": wheels,
    }, separators=(",", ":")), encoding="utf-8")

    print("=" * 78)
    print("TRUCK GEOMETRY")
    print("=" * 78)
    bad = 0
    for r in reports:
        ok = r["gap_points"] == 0 and r["overlap_points"] == 0
        if not ok:
            bad += 1
        print(f"  {r['vehicle']:<6} inside {r['points_inside']:>6}  "
              f"gaps {r['gap_points']:>4} ({r['gap_pct']}%)  "
              f"overlaps {r['overlap_points']:>4} ({r['overlap_pct']}%)  "
              f"{'OK' if ok else 'DEFECT'}")
        if r["gap_examples"]:
            print(f"         gap at {r['gap_examples']}")
        if r["overlap_examples"]:
            print(f"         overlap at {r['overlap_examples']}")
    print()
    for w in wheels:
        shapes = "  ".join(f"x={x['x']} r={x['r']} body {x['in_body_pct']}%"
                           for x in w["wheels"])
        print(f"  {w['vehicle']:<6} {shapes}")
    print()
    print(f"shared bounds: x {min(allx)}..{max(allx)}  y {min(ally)}..{max(ally)}")
    print(f"-> {OUT.name}")
    print("GEOMETRY_OK" if bad == 0 else "GEOMETRY_DEFECTS")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
