"""Generate the missing *.preload.js siblings so the two dashboards can render offline.

The loader pattern (already used by isze_data.preload.js) is:

    window.__PRELOADS__ = window.__PRELOADS__ || {};
    window.__PRELOADS__["<relative path the page fetches>"] = <the JSON verbatim>;

MASTER_DASHBOARD.html fetches ../Data/dashboards/viz/risk_cockpit.json
ISZE_Tender_Monitor_v2.html fetches ../Data/dashboards/tender_data.json

Neither preload existed, so window.__localFetch fell through to fetch(), which is
blocked on file://, and both pages silently degraded.
"""
import json
import pathlib

DATA = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\dashboards")

TARGETS = [
    # (json file, preload file, key the page fetches)
    (DATA / "viz" / "risk_cockpit.json",
     DATA / "viz" / "risk_cockpit.preload.js",
     "../Data/dashboards/viz/risk_cockpit.json"),
    (DATA / "tender_data.json",
     DATA / "tender_data.preload.js",
     "../Data/dashboards/tender_data.json"),
]

for src, dest, key in TARGETS:
    if not src.exists():
        print(f"SKIP  {src.name} missing")
        continue

    raw = src.read_text("utf-8", errors="strict")
    parsed = json.loads(raw)  # fail loudly on bad JSON rather than ship a broken preload

    body = (
        "/* generated 2026-09-16 by _audit/build_preloads.py\n"
        f"   source: {src.name}\n"
        "   do not edit by hand; regenerate when the source JSON changes. */\n"
        "window.__PRELOADS__ = window.__PRELOADS__ || {};\n"
        f"window.__PRELOADS__[{json.dumps(key)}] = "
        + json.dumps(parsed, ensure_ascii=False, separators=(", ", ": "))
        + ";\n"
    )

    dest.write_text(body, encoding="utf-8")
    print(f"WROTE {dest.relative_to(DATA.parent.parent)}")
    print(f"      source {src.name}  {src.stat().st_size:,} bytes")
    print(f"      preload           {dest.stat().st_size:,} bytes")
    print(f"      key   {key}")
    print(f"      parsed OK: {type(parsed).__name__}"
          + (f" with {len(parsed)} top-level keys" if isinstance(parsed, dict) else ""))
    print()
