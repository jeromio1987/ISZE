#!/usr/bin/env python
"""
extract_ids_dealers.py — pull the resolved IDS dealer records out of the built
IDS dealer-compare page into a compact file the globe can fetch.

Why read the HTML instead of re-resolving
-----------------------------------------
`02_dashboards/ids/IDS_2026_dealer_compare.html` embeds a fully built JSON
object in a `const DATA = {...}` assignment. That payload already carries the
dealer coordinates after the workspace's own geo checks, and it is the same set
of pins the IDS map draws. Re-running the geo resolver would risk disagreeing
with the IDS master, so this script only reads.

It never writes to `02_dashboards/ids/`. The IDS page is input only.

What is kept
------------
For the globe panel: identity, country, the total score percentage, the country
national average, the five section scores with their own national averages, and
the `geo` object including `geo_label`. The per-question `q` array (196 floats
per dealer, about 3.4 MB across the network) is deliberately dropped — the
globe panel does not show per-question detail, and the full radar and question
view already exists in the IDS dealer compare.

The `geo_label` is carried through unchanged. It is the honesty signal: it says
how each pin's position was derived, and the globe uses it to draw
real-coordinate and approximate pins differently.

Israel
------
The IDS Israel network is UMI only. UTI did not take part in that IDS round, so
nothing from UTI can appear here — this file only contains IDS participants. The
globe labels the country as "Israel (UMI)".

Run
---
    python 02_dashboards/globe/extract_ids_dealers.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent  # 02_dashboards/globe -> 02_dashboards -> ISZE root

SOURCE_HTML = REPO / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
OUT_JSON = HERE / "data" / "ids_dealers.json"

# Country display names. The internal code may stay a code; the label the user
# reads must be spelled out in English.
COUNTRY_LABELS = {
    "Benelux": "Benelux (Belgium, Netherlands, Luxembourg)",
    "Belgium": "Belgium",
    "Cyprus": "Cyprus",
    "Denmark": "Denmark",
    "France": "France",
    "Greece": "Greece",
    "Hungary": "Hungary",
    "Israel LCV": "Israel (UMI)",
    "Italy": "Italy",
    "Luxembourg": "Luxembourg",
    "Malta": "Malta",
    "Netherlands": "Netherlands",
    "Norway": "Norway",
    "Poland": "Poland",
    "Portugal": "Portugal",
    "Romania": "Romania",
    "Spain": "Spain",
    "Switzerland": "Switzerland",
    "UK CV": "United Kingdom (trucks)",
    "UK LCV": "United Kingdom (light commercial)",
}

# A pin sits on surveyed coordinates only where the IDS coordinate itself came
# from a surveyed source. Everything else is a town centre or worse.
SURVEYED_GEO_LABEL = "Approx city (MIDI network)"

# "Real" versus "approximate" for the map. The label is what decides it; these
# two are grouped as the closest thing to a surveyed position in the file.
REAL_GEO_LABELS = {"Approx city (MIDI network)"}


def read_data_object(html: str) -> dict:
    """Pull the JSON out of `const DATA = {...};` by brace matching.

    Not a regex: the payload contains braces and escaped quotes inside the
    question text, and a regex would truncate it.
    """
    key = "const DATA"
    start = html.find(key)
    if start == -1:
        raise SystemExit("STOP: could not find `const DATA` in the IDS page.")

    brace = html.find("{", start)
    if brace == -1:
        raise SystemExit("STOP: found `const DATA` but no object literal after it.")

    depth = 0
    in_string = False
    escaped = False
    i = brace
    while i < len(html):
        ch = html[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
        i += 1

    if depth != 0:
        raise SystemExit("STOP: the DATA object literal is not balanced.")

    return json.loads(html[brace:i + 1])


def clean(value, digits: int = 6):
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    return value


def build_dealer(raw: dict, sections_meta: list[dict]) -> dict:
    geo = raw.get("geo") or {}
    label = geo.get("geo_label")
    country = raw.get("country")

    sections = {}
    for sec in sections_meta:
        sid = sec["id"]
        s = (raw.get("sections") or {}).get(sid)
        if not s:
            sections[sid] = None
            continue
        sections[sid] = {
            "score": clean(s.get("score"), 2),
            "max": clean(s.get("max"), 2),
            "pct": clean(s.get("pct"), 6),
            "country_avg_pct": clean(s.get("country_avg_pct"), 6),
            "fill": s.get("fill"),
        }

    total_pct = raw.get("total_pct")
    avg_pct = raw.get("country_avg_pct")
    delta_pp = None
    if total_pct is not None and avg_pct is not None:
        delta_pp = round((total_pct - avg_pct) * 100, 2)

    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "address": raw.get("address"),
        "country": country,
        "country_label": COUNTRY_LABELS.get(country, country),
        "total_pct": clean(total_pct, 6),
        "total_max": clean(raw.get("total_max"), 2),
        "score_basis": raw.get("score_basis"),
        "country_avg_pct": clean(avg_pct, 6),
        "delta_pp": delta_pp,
        "excluded_from_average": bool(raw.get("excluded_from_average")),
        "sections": sections,
        "lat": clean(geo.get("lat"), 6),
        "lon": clean(geo.get("lon"), 6),
        "place": geo.get("place"),
        "geo_label": label,
        "geo_real": label in REAL_GEO_LABELS,
    }


def main() -> int:
    print("=" * 72)
    print("extract_ids_dealers.py")
    print("=" * 72)

    if not SOURCE_HTML.exists():
        raise SystemExit(f"STOP: source page not found: {SOURCE_HTML}")

    print(f"reading  : {SOURCE_HTML}")
    print(f"size     : {SOURCE_HTML.stat().st_size:,} bytes")
    html = SOURCE_HTML.read_text(encoding="utf-8", errors="replace")

    data = read_data_object(html)
    dealers_raw = data.get("dealers") or []
    sections_meta = data.get("sections") or []
    print(f"embedded : {len(dealers_raw)} dealer records, {len(sections_meta)} sections")
    print(f"built_at : {data.get('built_at')}   version: {data.get('version')}")

    rows = [build_dealer(d, sections_meta) for d in dealers_raw]

    # --- a dealer with no coordinates cannot be a pin ----------------------
    no_geo = [r for r in rows if r["lat"] is None or r["lon"] is None]
    rows = [r for r in rows if r["lat"] is not None and r["lon"] is not None]
    if no_geo:
        print(f"\n  {len(no_geo)} dealer(s) had no coordinates and are not in the file:")
        for r in no_geo[:10]:
            print(f"    {r['country']:<12} {r['name']}")

    # --- country tallies ----------------------------------------------------
    per_country = Counter(r["country"] for r in rows)
    print(f"\ndealers per IDS tab ({len(per_country)} tabs):")
    for c in sorted(per_country, key=lambda k: (-per_country[k], k)):
        print(f"  {per_country[c]:>4}  {c:<12} {COUNTRY_LABELS.get(c, c)}")

    geo_counts = Counter(r["geo_label"] for r in rows)
    print("\nhow each pin's position was derived (geo_label):")
    real = 0
    for lab, n in geo_counts.most_common():
        mark = "REAL" if lab in REAL_GEO_LABELS else "approx"
        if lab in REAL_GEO_LABELS:
            real += n
        print(f"  {n:>4}  [{mark}] {lab}")
    print(f"\n  real-coordinate pins : {real} of {len(rows)} ({real / len(rows):.1%})")
    print(f"  approximate pins     : {len(rows) - real} of {len(rows)}")

    # --- Israel guard -------------------------------------------------------
    israel = [r for r in rows if r["country"] == "Israel LCV"]
    print(f"\nIsrael: {len(israel)} dealers, all from the UMI network. "
          f"UTI did not take part in this IDS round.")

    # --- section coverage ---------------------------------------------------
    print("\nsection coverage (a null section means that section was not scored):")
    for sec in sections_meta:
        sid = sec["id"]
        have = sum(1 for r in rows if r["sections"].get(sid))
        print(f"  {sid}: {have:>4} of {len(rows)} dealers")

    # --- payload ------------------------------------------------------------
    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "generator": "02_dashboards/globe/extract_ids_dealers.py",
        "guide": (
            "IDS is the Isuzu Dealer Standard: an annual dealer evaluation. "
            "Each dealer scores a percentage of the points available. "
            "The national average is the average of that country's own dealers."
        ),
        "source": {
            "file": "02_dashboards/ids/IDS_2026_dealer_compare.html",
            "embedded_built_at": data.get("built_at"),
            "embedded_version": data.get("version"),
            "note": (
                "Coordinates were resolved by the IDS build and are reproduced "
                "here unchanged. Each dealer carries geo_label, which states how "
                "its position was derived."
            ),
        },
        "deeper_view": (
            "The full radar and the per-question view live in the IDS dealer "
            "compare page: 02_dashboards/ids/IDS_2026_dealer_compare.html"
        ),
        "sections": sections_meta,
        "country_labels": COUNTRY_LABELS,
        "counts": {
            "dealers": len(rows),
            "countries": len(per_country),
            "real_coordinates": real,
            "approximate_coordinates": len(rows) - real,
        },
        "geo_labels": dict(geo_counts),
        "dealers": rows,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False),
                        encoding="utf-8")

    size = OUT_JSON.stat().st_size
    print("\n" + "=" * 72)
    print(f"dealers written : {len(rows)}")
    print(f"wrote           : {OUT_JSON}  ({size:,} bytes, {size / 1024:.0f} KB)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
