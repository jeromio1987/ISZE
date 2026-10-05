#!/usr/bin/env python3
"""Build offline IDS 2026 dealer comparison dashboard (single HTML file)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from ids_dashboard_qa import format_qa_report, validate_dashboard_payload
from ids_dealer_geo import (
    attach_geo_to_dealers,
    format_geo_sanity_report,
    geo_coverage_summary,
    sanity_check_geo_clustering,
)
from ids_paths import IDS_DASHBOARD_HTML, IDS_RESULT_REPORTS_DIR, ISZE_ROOT
from ids_report_extract import build_dashboard_payload

_TEMPLATE = Path(__file__).resolve().parent / "ids_dashboard_template.html"
_DASH_MIRROR = ISZE_ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
_LEAFLET_CSS = ISZE_ROOT / "02_dashboards" / "_ui" / "leaflet.css"
_LEAFLET_JS = ISZE_ROOT / "02_dashboards" / "_ui" / "leaflet.js"


def _read_ui_asset(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required dashboard asset missing: {path}")
    return path.read_text(encoding="utf-8")


def leaflet_css_block() -> str:
    css = _read_ui_asset(_LEAFLET_CSS).replace("</style", "<\\/style")
    return f'<style id="ids-leaflet-css">\n{css}\n</style>'


def leaflet_js_block() -> str:
    js = _read_ui_asset(_LEAFLET_JS).replace("</script", "<\\/script")
    return f'<script id="ids-leaflet-js">\n{js}\n</script>'


def render_html(payload: dict, *, built_at: str) -> str:
    template = _TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        template.replace("__BUILT_AT__", built_at)
        .replace("__DATA_JSON__", blob)
        .replace("__LEAFLET_CSS_BLOCK__", leaflet_css_block())
        .replace("__LEAFLET_JS_BLOCK__", leaflet_js_block())
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=IDS_RESULT_REPORTS_DIR,
        help="Folder with country .xls result reports",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=IDS_DASHBOARD_HTML,
        help="Output HTML path",
    )
    parser.add_argument(
        "--skip-qa",
        action="store_true",
        help="Write HTML even if section-heatmap QA fails (emergency only)",
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Do not copy to 02_dashboards/ids/",
    )
    parser.add_argument(
        "--skip-geo-sanity",
        action="store_true",
        help="Do not fail build on geo clustering / country-centre blob errors",
    )
    args = parser.parse_args()

    if not _TEMPLATE.is_file():
        print(f"Template missing: {_TEMPLATE}", file=sys.stderr)
        return 1

    payload = build_dashboard_payload(args.reports_dir)
    if not payload["dealers"]:
        print(f"No dealers found in {args.reports_dir}", file=sys.stderr)
        return 2

    geo_counts = attach_geo_to_dealers(payload["dealers"])
    payload["geo"] = geo_counts
    geo_sanity = sanity_check_geo_clustering(payload["dealers"])
    payload["geo_sanity"] = {
        "ok": geo_sanity["ok"],
        "errors": geo_sanity["errors"],
        "warnings": geo_sanity["warnings"],
        "countries": geo_sanity["countries"],
    }
    payload["version"] = "v1.4"

    qa_errors = validate_dashboard_payload(payload)
    print(format_qa_report(payload, qa_errors))
    print(format_geo_sanity_report(geo_sanity))
    if qa_errors and not args.skip_qa:
        print(
            "Refusing to write dashboard — fix extract/reports or pass --skip-qa",
            file=sys.stderr,
        )
        return 3
    if not geo_sanity["ok"] and not args.skip_geo_sanity:
        print(
            "Refusing to write dashboard — geo sanity failed "
            "(fix city/address mapping or pass --skip-geo-sanity)",
            file=sys.stderr,
        )
        return 4

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    payload["built_at"] = built_at

    args.output.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(payload, built_at=built_at)
    args.output.write_text(html, encoding="utf-8")

    # Mirror to _EXPORT for hand-off (same folder tree as reports)
    export = args.output.parent.parent.parent / "_EXPORT" / args.output.name
    if export.parent.is_dir() or args.output == IDS_DASHBOARD_HTML:
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_text(html, encoding="utf-8")
        print(f"Also wrote {export}")

    if not args.no_mirror:
        _DASH_MIRROR.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.output, _DASH_MIRROR)
        print(f"Also wrote {_DASH_MIRROR}")

    cov = geo_coverage_summary(payload["dealers"])
    countries_pinned = sum(1 for c, s in cov.items() if s["pinned"] > 0)
    print(f"Wrote {args.output}")
    print(f"  version: {payload['version']}")
    print(f"  dealers: {payload['dealer_count']}")
    print(f"  countries: {payload['country_count']} ({', '.join(payload['countries'])})")
    print(
        f"  geo: {geo_counts['geo_ok']} pinned "
        f"({geo_counts['geo_city']} city / {geo_counts['geo_country_fallback']} country centre) · "
        f"{geo_counts['geo_missing']} without · "
        f"{countries_pinned}/{len(cov)} countries with pins"
    )
    print(f"  size: {args.output.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
