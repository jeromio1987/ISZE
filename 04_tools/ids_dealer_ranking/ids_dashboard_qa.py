"""Pre-ship QA for the IDS offline dealer comparison dashboard.

Fails the build when the HTML shell would load but section heatmaps /
radars would be empty (the July 2026 failure mode: formula cells blank
in xlrd, extract wrote null section pcts).
"""

from __future__ import annotations

from typing import Any

# Countries that ship totals only (no A–E question detail) are allowed
# to have empty section pcts. Everything else with dealers must have detail.
TOTALS_ONLY_COUNTRIES = frozenset({"ITUK"})

REQUIRED_SECTIONS = ("A", "B", "C", "D", "E")


def _has_section_pct(dealer: dict[str, Any]) -> bool:
    sections = dealer.get("sections") or {}
    return any(
        isinstance(sec, dict) and sec.get("pct") is not None
        for sec in sections.values()
    )


def validate_dashboard_payload(payload: dict[str, Any]) -> list[str]:
    """Return human-readable failure reasons (empty list = pass)."""
    errors: list[str] = []
    dealers = payload.get("dealers") or []
    sections = payload.get("sections") or []
    countries = payload.get("countries") or []

    if not dealers:
        errors.append("no dealers in payload")
        return errors

    sec_ids = {s.get("id") for s in sections if isinstance(s, dict)}
    missing_secs = [s for s in REQUIRED_SECTIONS if s not in sec_ids]
    if missing_secs:
        errors.append(f"missing section definitions: {', '.join(missing_secs)}")

    with_sections = [d for d in dealers if _has_section_pct(d)]
    if not with_sections:
        errors.append(
            "0 dealers have section A-E pct — heatmap would be all grey "
            "(check extract: category rows are formulas; must sum questions)"
        )

    coverage = len(with_sections) / len(dealers)
    # ITUK is ~14% of network; require most of the rest to have sections
    if coverage < 0.5:
        errors.append(
            f"section coverage too low: {len(with_sections)}/{len(dealers)} "
            f"({coverage:.0%}) dealers have section pct"
        )

    by_country: dict[str, list[dict[str, Any]]] = {}
    for d in dealers:
        by_country.setdefault(d.get("country") or "?", []).append(d)

    empty_detail_countries: list[str] = []
    for country, rows in sorted(by_country.items()):
        if country in TOTALS_ONLY_COUNTRIES:
            continue
        if not any(_has_section_pct(d) for d in rows):
            empty_detail_countries.append(f"{country} ({len(rows)} dealers)")

    if empty_detail_countries:
        errors.append(
            "countries with no section pct (heatmap blank): "
            + ", ".join(empty_detail_countries)
        )

    network = payload.get("network") or {}
    net_secs = network.get("sections_pct") or {}
    if with_sections and not any(net_secs.get(s) is not None for s in REQUIRED_SECTIONS):
        errors.append("network.sections_pct is empty despite dealers with sections")

    profiles = payload.get("country_profiles") or {}
    for country in countries:
        if country in TOTALS_ONLY_COUNTRIES:
            continue
        prof = profiles.get(country) or {}
        sp = prof.get("sections_pct") or {}
        if not any(sp.get(s) is not None for s in REQUIRED_SECTIONS):
            if country in by_country and any(_has_section_pct(d) for d in by_country[country]):
                errors.append(f"country_profiles[{country}].sections_pct empty")

    return errors


def format_qa_report(payload: dict[str, Any], errors: list[str]) -> str:
    dealers = payload.get("dealers") or []
    with_sec = sum(1 for d in dealers if _has_section_pct(d))
    totals_only = sum(1 for d in dealers if d.get("totals_only"))
    lines = [
        f"dealers: {len(dealers)}",
        f"with section pct: {with_sec}",
        f"totals_only: {totals_only}",
        f"countries: {payload.get('country_count')} ({', '.join(payload.get('countries') or [])})",
    ]
    if errors:
        lines.append("FAIL:")
        lines.extend(f"  - {e}" for e in errors)
    else:
        lines.append("PASS: section heatmap data present")
    return "\n".join(lines)
