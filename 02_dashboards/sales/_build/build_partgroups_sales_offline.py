#!/usr/bin/env python3
"""Build self-contained Part-Groups Sales Explorer for file:// double-click.

Embeds agg + pnyear + competitive + meta JSON and Plotly. No fetch, no scrape,
no GPS+PMS tabs. Output: 02_dashboards/sales/ISZE_PartGroups_Sales_Explorer_OFFLINE.html
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILD = Path(__file__).resolve().parent
EXTRACT = BUILD / "_extracted"
SIBLING = ROOT / "02_dashboards" / "sales" / "partgroups_data"
DATA_CANON = ROOT / "01_data" / "14_dashboards" / "partgroups_explorer"
PLOTLY = ROOT / "02_dashboards" / "sales" / "_ui" / "plotly.min.js"
PLOTLY_FALLBACK = ROOT / "02_dashboards" / "_ui" / "plotly.min.js"
OUT = ROOT / "02_dashboards" / "sales" / "ISZE_PartGroups_Sales_Explorer_OFFLINE.html"

PAYLOADS = [
    ("agg-data", "partgroups_agg.json"),
    ("pnyear-data", "partgroups_pnyear.json"),
    ("competitive-data", "partgroups_competitive.json"),
    ("meta-data", "partgroups_meta.json"),
]


def resolve_json(name: str) -> Path:
    for base in (SIBLING, DATA_CANON):
        p = base / name
        if p.exists():
            return p
    raise SystemExit(f"missing payload: {name}")


def mode_a_text(s: str) -> str:
    s = s.replace("internal / Jerome-only", "internal only")
    s = s.replace("internal / Jerome-only work-in-progress", "internal work-in-progress")
    s = s.replace("/ Jerome-only", "")
    s = s.replace("Jerome-only", "internal only")
    s = s.replace("Mode-B work-in-progress", "internal work-in-progress")
    s = s.replace("explicitly a internal", "explicitly an internal")
    s = s.replace("internal", "internal")
    s = s.replace("Mode-B", "internal")
    return s


def main() -> None:
    css = (EXTRACT / "original.css").read_text(encoding="utf-8")
    body = mode_a_text((EXTRACT / "original_body.html").read_text(encoding="utf-8"))
    app = mode_a_text((EXTRACT / "original_app.js").read_text(encoding="utf-8"))

    plotly_path = PLOTLY if PLOTLY.exists() else PLOTLY_FALLBACK
    if not plotly_path.exists():
        raise SystemExit(f"missing plotly: {plotly_path}")
    plotly_js = plotly_path.read_text(encoding="utf-8", errors="replace")

    # Prefer compact JSON text as stored (already separators=,:,) — avoid re-dumps of huge files
    blocks = []
    sizes = {}
    for sid, fname in PAYLOADS:
        src = resolve_json(fname)
        raw = src.read_text(encoding="utf-8")
        # validate
        json.loads(raw)
        sizes[fname] = src.stat().st_size
        blocks.append(f'<script id="{sid}" type="application/json">{raw}</script>')

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Soften competitive note path jargon slightly for shared while keeping Eucon substance
    body = body.replace(
        "Internal tool, not for distributor sharing without review",
        "Internal sales overview · offline self-contained · verify freshness before sharing",
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ISZE Part-Groups Sales Explorer (offline)</title>
<style>
{css}
</style>
<script>
{plotly_js}
</script>
</head>
<body>
{body}

<!-- Embedded payloads (no fetch / no sibling JSON required) -->
{chr(10).join(blocks)}

<script>
{app}
</script>
<!-- built {stamp} · offline sales-only · no scrape/GPS tabs -->
</body>
</html>
"""

    # Guardrails
    if "fetch(" in app:
        raise SystemExit("original_app.js still contains fetch — abort")
    if re.search(r"partgroups_scrape|partgroups_gps_pms|Aftermarket scrape|GPS \+ PMS", html):
        # body/app should not advertise those tabs; competitive "aftermarket brands" wording is OK
        bad = []
        if "partgroups_scrape" in html:
            bad.append("partgroups_scrape")
        if "partgroups_gps_pms" in html:
            bad.append("partgroups_gps_pms")
        if "Aftermarket scrape" in html:
            bad.append("Aftermarket scrape")
        if "GPS + PMS" in html:
            bad.append("GPS + PMS")
        if bad:
            raise SystemExit(f"forbidden markers in offline HTML: {bad}")

    OUT.write_text(html, encoding="utf-8")
    mb = OUT.stat().st_size / (1024 * 1024)
    print(f"wrote {OUT}")
    print(f"size: {mb:.2f} MB ({OUT.stat().st_size:,} bytes)")
    for k, v in sizes.items():
        print(f"  embedded {k}: {v/1e6:.3f} MB")
    print(f"  plotly: {plotly_path.stat().st_size/1e6:.3f} MB")
    print(f"fetch in output: {'fetch(' in html}")
    print(f"scrape json ref: {'partgroups_scrape' in html}")
    print(f"gps_pms json ref: {'partgroups_gps_pms' in html}")


if __name__ == "__main__":
    main()
