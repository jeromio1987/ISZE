#!/usr/bin/env python3
"""Restamp live IDS HTMLs after Section E not_scored policy.

Writes country packs + full-network compare. Does not rewrite zips.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from build_ids_country_packs_v13 import (
    DASH_MIRROR,
    PACK_ROOT_DEFAULT,
    filter_country_payload,
    render_country_html,
    slug_country,
    write_readme,
)
from build_ids_dashboard import render_html
from ids_dashboard_qa import format_qa_report, validate_dashboard_payload
from ids_dealer_geo import attach_geo_to_dealers
from ids_paths import IDS_DASHBOARD_HTML, IDS_RESULT_REPORTS_DIR, ISZE_ROOT
from ids_report_extract import build_dashboard_payload

COUNTRIES = [
    "Belgium",
    "Netherlands",
    "Luxembourg",
    "Denmark",
    "Poland",
    "Greece",
    "Norway",
    "Hungary",
    "Romania",
    "Malta",
    "Cyprus",
    "UK CV",
    "UK LCV",
    "Portugal",
    "Israel LCV",
    "France",
    "Italy",
    "Spain",
    "Switzerland",
]


def _pct(v) -> str:
    return "—" if v is None else f"{float(v) * 100:.1f}%"


def main() -> int:
    print("Building payload…", flush=True)
    full = build_dashboard_payload(IDS_RESULT_REPORTS_DIR)
    geo_counts = attach_geo_to_dealers(full["dealers"], allow_country_centre=True)
    full["geo"] = geo_counts
    qa = validate_dashboard_payload(full)
    print(format_qa_report(full, qa), flush=True)
    if qa:
        print("QA failed — abort", flush=True)
        return 3

    net = full.get("network") or {}
    il = (full.get("country_profiles") or {}).get("Israel LCV") or {}
    print("NETWORK total", _pct(net.get("total_pct")), flush=True)
    print("NETWORK sections", {k: _pct(v) for k, v in (net.get("sections_pct") or {}).items()}, flush=True)
    print("ISRAEL LCV total", _pct(il.get("total_pct")), "basis", il.get("score_basis"), flush=True)
    print("ISRAEL LCV sections", {k: _pct(v) for k, v in (il.get("sections_pct") or {}).items()}, flush=True)
    print("Section E meta", json.dumps(net.get("section_e"), ensure_ascii=False)[:800], flush=True)

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    full["built_at"] = built_at
    full["version"] = "v1.4"

    written: list[str] = []

    html_full = render_html(full, built_at=built_at)
    targets_full = [
        IDS_DASHBOARD_HTML,
        DASH_MIRROR / "IDS_2026_dealer_compare.html",
        ISZE_ROOT / "02_dashboards" / "Data" / "90_INBOX" / "IDS_2026" / "_EXPORT" / "IDS_2026_dealer_compare.html",
    ]
    for p in targets_full:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html_full, encoding="utf-8")
        written.append(str(p))
        print("WROTE", p, flush=True)

    DASH_MIRROR.mkdir(parents=True, exist_ok=True)
    PACK_ROOT_DEFAULT.mkdir(parents=True, exist_ok=True)

    for country in COUNTRIES:
        if country not in (full.get("countries") or []):
            print("SKIP missing", country, flush=True)
            continue
        payload = filter_country_payload(full, country)
        payload["built_at"] = built_at
        payload["version"] = "v1.4"
        html = render_country_html(payload, country, built_at=built_at)
        slug = slug_country(country)
        name = f"IDS_2026_dealer_compare_{slug}.html"
        pack_dir = PACK_ROOT_DEFAULT / slug
        pack_dir.mkdir(parents=True, exist_ok=True)
        dests = [pack_dir / name, DASH_MIRROR / name]
        if country == "Israel LCV":
            alias = PACK_ROOT_DEFAULT / "Israel"
            alias.mkdir(parents=True, exist_ok=True)
            dests.append(alias / "IDS_2026_dealer_compare_Israel.html")
        for p in dests:
            p.write_text(html, encoding="utf-8")
            written.append(str(p))
        pinned = sum(1 for d in payload["dealers"] if (d.get("geo") or {}).get("lat") is not None)
        geo = {"geo_ok": pinned, "geo_missing": len(payload["dealers"]) - pinned}
        write_readme(pack_dir, country, dealer_count=len(payload["dealers"]), geo=geo)
        print(f"OK {country}: {len(payload['dealers'])} -> {name}", flush=True)

    summary = {
        "built_at": built_at,
        "network_total_pct": net.get("total_pct"),
        "network_sections_pct": net.get("sections_pct"),
        "israel_lcv_total_pct": il.get("total_pct"),
        "israel_lcv_sections_pct": il.get("sections_pct"),
        "section_e": net.get("section_e"),
        "files": written,
    }
    out = Path(__file__).resolve().parent / "_restamp_section_e_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", len(written), "HTML files. Summary", out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
