#!/usr/bin/env python3
"""Verify OFFLINE Part-Groups HTML is self-contained for file://."""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "ISZE_PartGroups_Sales_Explorer_OFFLINE.html"


def main() -> None:
    t = OUT.read_text(encoding="utf-8")
    mb = OUT.stat().st_size / (1024 * 1024)
    print(f"file: {OUT}")
    print(f"size_mb: {mb:.2f}")

    # Extract app script: last non-json inline script after plotly
    scripts = list(
        re.finditer(r"<script(?![^>]*src=)(?![^>]*id=)(?![^>]*type=)>(.*?)</script>", t, re.I | re.S)
    )
    app = None
    for m in scripts:
        body = m.group(1).strip()
        if body.startswith("(function") or "'use strict'" in body[:80]:
            app = body
    assert app, "app JS not found"
    assert "fetch(" not in app, "app JS must not fetch"
    assert "partgroups_data/" not in app, "app must not reference sibling JSON path"
    assert "loadJson" not in app, "slim loader must not be present"
    assert "parseCompact('agg-data')" in app
    assert "parseCompact('pnyear-data')" in app

    for sid in ["agg-data", "pnyear-data", "competitive-data", "meta-data"]:
        m = re.search(
            rf'<script id="{sid}" type="application/json">(.*?)</script>',
            t,
            re.I | re.S,
        )
        assert m, f"missing embedded {sid}"
        obj = json.loads(m.group(1))
        if sid == "meta-data":
            assert "date_max" in obj and "db_codes_present" in obj
            print(f"  {sid}: date_max={obj.get('date_max')} dbs={len(obj.get('db_codes_present', []))}")
        else:
            assert "columns" in obj and "rows" in obj
            print(f"  {sid}: cols={len(obj['columns'])} rows={len(obj['rows'])}")

    # Plotly inlined in <head> (before megabyte JSON)
    head = t[: t.find("</head>")]
    assert "plotly.js" in head.lower() or "var Plotly" in head or "Plotly=" in head
    assert "tab-bar" not in t
    assert "Aftermarket scrape" not in t
    assert "GPS + PMS" not in t
    assert "partgroups_scrape" not in t
    assert "partgroups_gps_pms" not in t
    assert 'src="_ui/plotly' not in t
    assert 'src="partgroups_data' not in t

    # fetch may appear inside plotly bundle — ensure not in our app / data URLs
    fetch_hits = [m.start() for m in re.finditer(r"fetch\(", t)]
    print(f"fetch( occurrences in whole file: {len(fetch_hits)} (plotly bundle OK)")
    print("OK: self-contained sales offline HTML")


if __name__ == "__main__":
    main()
