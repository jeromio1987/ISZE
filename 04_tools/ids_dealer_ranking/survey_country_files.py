"""Survey every IDS country compare file: dealer coordinate spread, duplicate copies, patch readiness.

Writes nothing. Answers three questions before the multi-country bake:
  1. What lat/lon box does each country's dealers actually occupy, once overseas outliers are
     set aside? (Portugal's Azores stretched the picture to mostly ocean - avoid that everywhere.)
  2. Which copies of each file are byte-identical duplicates, so archiving removes nothing unique?
  3. Does each file still carry the map init block the patcher expects?
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
IDS = ISZE / "02_dashboards" / "ids"

COORD_RE = re.compile(r'"lat":\s*(-?\d+\.?\d*)\s*,\s*"lon":\s*(-?\d+\.?\d*)')
INIT_RE = re.compile(
    r'if \(!window\.__idsMap\) \{\s*'
    r'window\.__idsMap = L\.map\("ids-map"'
)
HAS_STREET = re.compile(r"__idsStreetLayer")


def coords_of(path: Path) -> list[tuple[float, float]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [(float(a), float(b)) for a, b in COORD_RE.findall(text)]


def robust_bbox(coords: list[tuple[float, float]], pad_frac: float = 0.18, pad_deg: float = 0.4):
    """Box around the main cluster. Points far from the median are treated as overseas and left out,
    because Leaflet can still pan to them but they must not stretch the map picture."""
    if not coords:
        return None, [], []
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    med_lat, med_lon = statistics.median(lats), statistics.median(lons)

    def mad(vals, med):
        return statistics.median([abs(v - med) for v in vals]) or 1.0

    tol_lat = max(1.5, 3.0 * mad(lats, med_lat))
    tol_lon = max(1.5, 3.0 * mad(lons, med_lon))
    inside = [(la, lo) for la, lo in coords if abs(la - med_lat) <= tol_lat and abs(lo - med_lon) <= tol_lon]
    outside = [c for c in coords if c not in inside]
    if not inside:
        inside, outside = coords, []

    la_min, la_max = min(c[0] for c in inside), max(c[0] for c in inside)
    lo_min, lo_max = min(c[1] for c in inside), max(c[1] for c in inside)
    d_lat = (la_max - la_min) * pad_frac + pad_deg
    d_lon = (lo_max - lo_min) * pad_frac + pad_deg
    box = (
        round(lo_min - d_lon, 3),
        round(la_min - d_lat, 3),
        round(lo_max + d_lon, 3),
        round(la_max + d_lat, 3),
    )
    if box[2] - box[0] < 0.8:
        mid = (box[0] + box[2]) / 2
        box = (round(mid - 0.4, 3), box[1], round(mid + 0.4, 3), box[3])
    if box[3] - box[1] < 0.8:
        mid = (box[1] + box[3]) / 2
        box = (box[0], round(mid - 0.4, 3), box[2], round(mid + 0.4, 3))
    return box, inside, outside


def sha(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    canon = sorted(p for p in IDS.glob("IDS_2026_dealer_compare*.html") if ".bak" not in p.name)
    print(f"canonical working files in 02_dashboards/ids: {len(canon)}\n")

    # every copy of these files anywhere, excluding archives
    allcopies = [
        p
        for p in ISZE.rglob("IDS_2026_dealer_compare*.html")
        if not any(x in p.parts for x in ("90_archive", "07_deploy", "node_modules", "worktrees"))
        and ".bak" not in p.name
    ]
    by_hash: dict[str, list[str]] = {}
    for p in allcopies:
        by_hash.setdefault(sha(p), []).append(str(p.relative_to(ISZE)))

    print("=== per country: coordinate box and patch readiness ===")
    rows = []
    for p in canon:
        country = p.stem.replace("IDS_2026_dealer_compare_", "") or "ALL"
        text = p.read_text(encoding="utf-8", errors="ignore")
        coords = coords_of(p)
        box, inside, outside = robust_bbox(coords)
        rows.append(
            {
                "country": country,
                "file": p.name,
                "kb": round(p.stat().st_size / 1024),
                "dealers": len(coords),
                "bbox_wsen": box,
                "outside_box": [f"{a},{b}" for a, b in outside],
                "init_block": bool(INIT_RE.search(text)) if country != "ALL" else None,
                "already_baked": bool(HAS_STREET.search(text)),
                "sha": sha(p)[:10],
                "copies": [c for c in by_hash.get(sha(p), [])],
            }
        )

    for r in rows:
        print(
            f"{r['country']:<12} dealers={r['dealers']:<4} {r['kb']:>5} KB  "
            f"box={r['bbox_wsen']}  init={'Y' if r['init_block'] else '-'} "
            f"baked={'Y' if r['already_baked'] else '-'} copies={len(r['copies'])}"
        )
        if r["outside_box"]:
            print(f"{'':<12} outside the box (overseas, left off the picture): {r['outside_box']}")

    print("\n=== duplicate sets (same bytes in more than one place) ===")
    for h, paths in sorted(by_hash.items(), key=lambda kv: -len(kv[1])):
        if len(paths) > 1:
            print(f"  {h[:10]}  x{len(paths)}")
            for q in paths:
                print(f"      {q}")

    print("\n=== backup / superseded files of this type ===")
    baks = sorted(
        p
        for p in ISZE.rglob("IDS_2026_dealer_compare*.html.*")
        if not any(x in p.parts for x in ("90_archive", "07_deploy", "worktrees"))
    )
    for p in baks:
        print(f"  {p.stat().st_size/1024:>8.0f} KB  {p.relative_to(ISZE)}")
    print(f"  total {len(baks)} backup files")

    out = ISZE / "02_dashboards" / "ids" / "_qa_dealer_compare_20260924" / "survey.json"
    out.write_text(json.dumps({"rows": rows, "backups": [str(p) for p in baks]}, indent=2), encoding="utf-8")
    print("\nsurvey written:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
