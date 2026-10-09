"""Pre-ship QA for the IDS offline dealer comparison dashboard.

Fails the build when the HTML shell would load but section heatmaps /
radars would be empty (the July 2026 failure mode: formula cells blank
in xlrd, extract wrote null section pcts).
"""

from __future__ import annotations

from typing import Any

from ids_paths import country_display_name

UKCV_LABEL = country_display_name("ITUK")
UKCV_SCORE_BASIS = "UKCV-AH"
UKCV_REQUIRED_SECTIONS = ("A", "B", "C", "D", "E", "F", "G", "H")
REQUIRED_SECTIONS = ("A", "B", "C", "D", "E")


def _has_section_pct(dealer: dict[str, Any]) -> bool:
    sections = dealer.get("sections") or {}
    return any(
        isinstance(sec, dict) and sec.get("pct") is not None
        for sec in sections.values()
    )


def _is_ukcv_dealer(dealer: dict[str, Any]) -> bool:
    return (
        dealer.get("score_basis") == UKCV_SCORE_BASIS
        or dealer.get("country") == UKCV_LABEL
    )


def _country_is_ukcv(country: str, rows: list[dict[str, Any]]) -> bool:
    if country == UKCV_LABEL:
        return True
    return any(_is_ukcv_dealer(d) for d in rows)


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
    ukcv_only = bool(countries) and all(c == UKCV_LABEL for c in countries)

    if ukcv_only:
        missing_secs = [s for s in UKCV_REQUIRED_SECTIONS if s not in sec_ids]
        if missing_secs:
            errors.append(
                f"UK CV missing section definitions: {', '.join(missing_secs)}"
            )
    else:
        missing_secs = [s for s in REQUIRED_SECTIONS if s not in sec_ids]
        if missing_secs:
            errors.append(f"missing section definitions: {', '.join(missing_secs)}")

    with_sections = [d for d in dealers if _has_section_pct(d)]
    if not with_sections:
        errors.append(
            "0 dealers have section pct — heatmap would be all grey "
            "(check extract: category rows are formulas; must sum questions; "
            "UK CV needs Sheet2 A–H enrich)"
        )

    coverage = len(with_sections) / len(dealers)
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
        if _country_is_ukcv(country, rows):
            # Country-only pack: live A–H on dealers. Multi-country shell: A–H
            # stashed on _ukcv_sections (dealers look totals_only on A–E).
            ah_source = [
                (d.get("_ukcv_sections") or d.get("sections") or {}) for d in rows
            ]
            with_ah = [
                secs
                for secs in ah_source
                if sum(
                    1
                    for sid in UKCV_REQUIRED_SECTIONS
                    if (secs.get(sid) or {}).get("pct") is not None
                )
                >= 6
            ]
            if rows and len(with_ah) / len(rows) < 0.8:
                errors.append(
                    f"UK CV A–H coverage too low: {len(with_ah)}/{len(rows)} dealers"
                )
            if ukcv_only:
                still_totals = [d for d in rows if d.get("totals_only")]
                if still_totals:
                    errors.append(
                        f"UK CV still totals_only after enrich: {len(still_totals)} dealers"
                    )
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
    if ukcv_only:
        # Within UK CV pack, network section overlay is intentionally empty.
        pass
    elif with_sections and not any(net_secs.get(s) is not None for s in REQUIRED_SECTIONS):
        errors.append("network.sections_pct is empty despite dealers with sections")

    profiles = payload.get("country_profiles") or {}
    for country in countries:
        prof = profiles.get(country) or {}
        sp = prof.get("sections_pct") or {}
        rows = by_country.get(country) or []
        if not any(_has_section_pct(d) for d in rows):
            continue
        if _country_is_ukcv(country, rows):
            if not any(sp.get(s) is not None for s in UKCV_REQUIRED_SECTIONS):
                errors.append(f"country_profiles[{country}].sections_pct empty (UK CV A–H)")
        else:
            if not any(sp.get(s) is not None for s in REQUIRED_SECTIONS):
                errors.append(f"country_profiles[{country}].sections_pct empty")

    return errors


def format_qa_report(payload: dict[str, Any], errors: list[str]) -> str:
    dealers = payload.get("dealers") or []
    with_sec = sum(1 for d in dealers if _has_section_pct(d))
    totals_only = sum(1 for d in dealers if d.get("totals_only"))
    ukcv_n = sum(1 for d in dealers if _is_ukcv_dealer(d))
    lines = [
        f"dealers: {len(dealers)}",
        f"with section pct: {with_sec}",
        f"totals_only: {totals_only}",
        f"ukcv_ah: {ukcv_n}",
        f"countries: {payload.get('country_count')} ({', '.join(payload.get('countries') or [])})",
    ]
    qn = len(payload.get("questions") or [])
    with_q = sum(1 for d in dealers if isinstance(d.get("q"), list))
    lines.append(f"questions: {qn}")
    lines.append(f"dealers with q[]: {with_q}")
    if errors:
        lines.append("FAIL:")
        lines.extend(f"  - {e}" for e in errors)
    else:
        lines.append("PASS: section heatmap data present")
    return "\n".join(lines)
