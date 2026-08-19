#!/usr/bin/env python3
"""Build per-country IDS 2026 dealer-compare packs for colleague drafts.

Country-only HTML (Leaflet map + network avg benchmark), zip, master index.
Mirrors key HTMLs under 02_dashboards/ids/.

v1.4 (2026-08-11): Tomoe Baumann average rule — FR/ES red-marked dealers stay
on the list/map but are excluded from national / section / question averages
(and from anonymous network averages). Italy + Switzerland: ALL dealers in
averages (including zero-score shells). Other markets keep zero-shell hygiene.

Default INCLUDE (separate BE/NL/LUX; skip Benelux rollup):
  Belgium, Netherlands, Luxembourg, Denmark, Poland, Greece, Norway,
  Hungary, Romania, Malta, Cyprus, UK CV

Default EXCLUDE:
  UK LCV (IUK), Portugal (Imotors), Israel LCV (UMI), MIDI (FR/IT/ES/CH), Benelux

MIDI rebuild: --countries France Italy Spain Switzerland
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_ids_dashboard import render_html
from ids_dashboard_qa import format_qa_report, validate_dashboard_payload
from ids_dealer_geo import (
    attach_geo_to_dealers,
    format_geo_sanity_report,
    sanity_check_geo_clustering,
)
from ids_paths import IDS_RESULT_REPORTS_DIR, ISZE_ROOT
from ids_report_extract import build_dashboard_payload

VERSION = "v1.4"
PACK_ROOT_DEFAULT = ISZE_ROOT / "09_meetings" / "IDS_2026_Country_Packs_v1.4"
DASH_MIRROR = ISZE_ROOT / "02_dashboards" / "ids"
MIDI_COUNTRIES = frozenset({"France", "Italy", "Spain", "Switzerland"})

# Workspace labels (ids_paths): IUK = UK LCV, ITUK = UK CV — do not flip.
DEFAULT_INCLUDE = [
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
]

DEFAULT_EXCLUDE = {
    "UK LCV",
    "Portugal",
    "Israel LCV",
    "France",
    "Italy",
    "Spain",
    "Switzerland",
    "Benelux",
}

# IDS 26 summary / Awards owners → work emails for draft To:
OWNER_EMAIL: dict[str, dict[str, str]] = {
    "Belgium": {"name": "Bart Symons", "email": "bart.symons@isuzu-e.com"},
    "Netherlands": {"name": "Bart Symons", "email": "bart.symons@isuzu-e.com"},
    "Luxembourg": {"name": "Bart Symons", "email": "bart.symons@isuzu-e.com"},
    "Poland": {"name": "Bart Symons", "email": "bart.symons@isuzu-e.com"},
    "Romania": {"name": "Bart Symons", "email": "bart.symons@isuzu-e.com"},
    "Denmark": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Hungary": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Malta": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Cyprus": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Norway": {"name": "Koen Matheussen", "email": "koen.matheussen@isuzu-e.com"},
    "Greece": {"name": "Jerome Van Der Pluym", "email": "jerome.van.der.pluym@isuzu-e.com"},
    "UK CV": {"name": "Jerome Van Der Pluym", "email": "jerome.van.der.pluym@isuzu-e.com"},
    # UK LCV (IUK) — excluded from default colleague batch; build with --countries "UK LCV"
    "UK LCV": {"name": "Koen Matheussen", "email": "koen.matheussen@isuzu-e.com"},
    # Israel LCV (UMI) — excluded from default batch; build with --countries "Israel LCV"
    "Israel LCV": {
        "name": "Jerome Van Der Pluym",
        "email": "jerome.van.der.pluym@isuzu-e.com",
    },
    "Portugal": {
        "name": "Jerome Van Der Pluym",
        "email": "jerome.van.der.pluym@isuzu-e.com",
    },
    # MIDI batch (explicit --countries France Italy Spain Switzerland)
    "France": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Italy": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Spain": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
    "Switzerland": {"name": "Tomoe Baumann", "email": "Tomoe.Baumann@isuzu.de"},
}

JEROME_EMAIL = "jerome.van.der.pluym@isuzu-e.com"


def slug_country(country: str) -> str:
    s = re.sub(r"[^\w]+", "_", country.strip(), flags=re.UNICODE)
    return s.strip("_") or "Country"


def filter_country_payload(full: dict[str, Any], country: str) -> dict[str, Any]:
    """Keep one country; retain full-network averages as anonymous benchmark."""
    network = full.get("network") or {}
    dealers = [d for d in full.get("dealers") or [] if d.get("country") == country]
    for d in dealers:
        for sid, sec in (d.get("sections") or {}).items():
            if isinstance(sec, dict):
                sec["network_avg_pct"] = (network.get("sections_pct") or {}).get(sid)

    profiles = full.get("country_profiles") or {}
    profile = profiles.get(country) or {
        "dealer_count": len(dealers),
        "total_pct": None,
        "sections_pct": {},
        "q_pct": None,
    }

    return {
        "countries": [country],
        "sections": full.get("sections") or [],
        "questions": full.get("questions") or [],
        "dealers": dealers,
        "dealer_count": len(dealers),
        "country_count": 1,
        "country_profiles": {country: profile},
        "network": network,
        "bands": full.get("bands") or {},
        "version": VERSION,
        "scope": {
            "label": f"{country} only",
            "audience": "ISZE / IMG colleagues",
            "network_benchmark": "Full IDS 2026 network average (anonymous)",
            "network_dealer_count": network.get("dealer_count"),
        },
    }


# Multi-country chrome that is redundant when the HTML already contains one country.
# Keep: national avg, anonymous network avg, Map hover vs national, Country vs network tab.
# Strip: Country filter / By country / Country radar / Changelog (Mode A colleague packs).
COUNTRY_ONLY_CSS = """
<style id="country-only-ui">
  /* Single-country pack: hide DB-level country filter and multi-country tabs/panels */
  .toolbar > div:has(#f-country) { display: none !important; }
  button.tab[data-tab="country"],
  button.tab[data-tab="country-radar"] { display: none !important; }
  #panel-country, #panel-country-radar { display: none !important; }
  /* Per-panel Country dropdowns — only one market in this file */
  .controls > div:has(#ov-country),
  .controls > div:has(#gp-country),
  .controls > div:has(#qq-country),
  .controls > div:has(#dr-country),
  .controls > div:has(#cp-country) { display: none !important; }
</style>
"""


def strip_multi_country_chrome(html: str) -> str:
    """Hide Country filter / By country / Country radar / panel country selects."""
    if 'id="country-only-ui"' not in html:
        html = html.replace("</head>", COUNTRY_ONLY_CSS + "\n</head>", 1)
    # Remove visible toolbar country filter; keep a hidden stub so JS filter fns still run.
    html = re.sub(
        r'<div><label for="f-country">Country filter</label>'
        r'<select id="f-country" multiple></select></div>\s*',
        '<select id="f-country" multiple hidden aria-hidden="true"></select>\n    ',
        html,
        count=1,
    )
    html = re.sub(
        r'\s*<button class="tab" data-tab="country-radar" type="button">'
        r"Country radar</button>",
        "",
        html,
        count=1,
    )
    html = re.sub(
        r'\s*<button class="tab" data-tab="country" type="button">'
        r"By country</button>",
        "",
        html,
        count=1,
    )
    return html


def strip_changelog_chrome(html: str) -> str:
    """Remove Changelog tab + panel from Mode A country packs (client/colleague HTML)."""
    html = re.sub(
        r'\s*<button class="tab" data-tab="changelog" type="button">'
        r"Changelog</button>",
        "",
        html,
        count=1,
    )
    html = re.sub(
        r'\s*<section id="panel-changelog" class="panel">.*?</section>',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )
    return html


def render_country_html(payload: dict[str, Any], country: str, *, built_at: str) -> str:
    html = render_html(payload, built_at=built_at)
    html = strip_multi_country_chrome(html)
    html = strip_changelog_chrome(html)
    html = html.replace(
        "<title>IDS 2026 — Dealer Compare</title>",
        f"<title>IDS 2026 — {country} dealer compare ({VERSION})</title>",
    )
    html = re.sub(
        r"<h1>IDS 2026 — Dealer comparison[^<]*(?:<span[^>]*>[^<]*</span>)?</h1>",
        f"<h1>IDS 2026 — {country} dealer comparison "
        f'<span style="font-weight:500;opacity:.85;font-size:.85em">{VERSION}</span></h1>',
        html,
        count=1,
    )
    net_n = (payload.get("network") or {}).get("dealer_count", "—")
    n_dealers = payload.get("dealer_count", 0)
    e_note = (
        " · Section E not scored (A–D only, 0/27 recorded)"
        if country == "Israel LCV"
        else ""
    )
    subtitle = (
        f"{VERSION} · {country} dealers only ({n_dealers}){e_note} · "
        f"no country filter (single market) · "
        f"map hover = dealer score vs {country} national average · "
        f"network avg from full IDS network ({net_n} dealers, anonymous; "
        f"Section E not scored / missing excluded) · "
        f"built {built_at}"
    )
    html = re.sub(
        r"<p>v1\.[34] map pins · (?:score filters · )?sections A–E \+ questions · "
        r"good / medium / bad · built [^<]+</p>",
        f"<p>{subtitle}</p>",
        html,
        count=1,
    )
    if subtitle.split(" · ")[0] not in html.split("</header>", 1)[0]:
        html = re.sub(
            r"(<header>\s*<h1>[^<]*(?:<span[^>]*>[^<]*</span>)?</h1>\s*)<p>[^<]*</p>",
            rf"\1<p>{subtitle}</p>",
            html,
            count=1,
        )

    html = html.replace(
        "<h2>Network dealer map</h2>",
        f"<h2>{country} dealer map</h2>",
        1,
    )
    html = html.replace(
        "Pins are coloured by dealer total vs that country’s national average",
        f"Pins are coloured by dealer total vs the {country} national average",
        1,
    )
    html = html.replace(
        'aria-label="IDS network dealer interactive map"',
        f'aria-label="{country} dealer interactive map"',
        1,
    )
    # Ensure no Weak-sector overlay text survives.
    if "Weak sector" in html:
        html = html.replace("Weak sector", "")
    return html


def write_readme(pack_dir: Path, country: str, *, dealer_count: int, geo: dict[str, Any]) -> None:
    text = f"""# IDS 2026 — {country} pack ({VERSION})

Country-only dealer compare for ISZE / IMG colleagues. English UI.

## Contents

| File | Role |
|------|------|
| `IDS_2026_dealer_compare_{slug_country(country)}.html` | Dealer compare — **{country} dealers only**; Map tab (Leaflet); hover = dealer score vs **{country} national average**; full-network averages kept as anonymous benchmark |
| `README.md` | This file |

## Coverage

- Dealers: **{dealer_count}**
- Geo pinned: {geo.get("geo_ok", "—")} · missing: {geo.get("geo_missing", "—")}
- Map: Leaflet + OpenStreetMap / CARTO (needs internet when opening HTML)
- **No Country filter / By country / Country radar / Changelog** — Mode A colleague pack
- Benchmarks kept: dealer vs **{country} national average**, anonymous full-network average

## Network average

Charts and heatmap “vs network avg” use the **full IDS 2026 network** average (anonymous).
Section E for Israel LCV (UMI) is **not scored** (29 dealers, 0/18 questions, 0/27 points)
and is **excluded** from that network average — not treated as a fail.
Hover the network-average figure in the HTML for the note.
"""
    (pack_dir / "README.md").write_text(text, encoding="utf-8")


def zip_pack(pack_dir: Path, zip_path: Path, html_name: str) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (html_name, "README.md"):
            p = pack_dir / name
            if p.is_file():
                zf.write(p, name)


def email_body(country: str, *, dealer_count: int, zip_name: str, html_name: str) -> str:
    owner = OWNER_EMAIL.get(country) or {}
    owner_line = ""
    if owner.get("name"):
        owner_line = f"\n(IDS follow-up owner on 26 summary: {owner['name']})\n"
    return (
        f"Dear colleague,\n\n"
        f"Please find attached the IDS 2026 dealer compare pack for {country} "
        f"({VERSION}).\n\n"
        f"What is included\n"
        f"• Offline HTML: {html_name}\n"
        f"• Zip: {zip_name}\n"
        f"• Scope: {country} dealers only ({dealer_count}) — other countries are not visible\n"
        f"• UI: no Country filter / By country tab (single-market pack)\n"
        f"• Map tab: Leaflet pins; hover shows dealer total score vs the {country} "
        f"national average (and the delta in percentage points)\n"
        f"• Network average charts still use the full IDS 2026 network as an "
        f"anonymous benchmark (no other dealer names)\n"
        f"{owner_line}\n"
        f"Open the HTML with an internet connection so map tiles can load.\n\n"
        f"Kind regards,\n"
        f"Jérôme Van der Pluym\n"
    )


def write_master_index(
    pack_root: Path,
    rows: list[dict[str, Any]],
    *,
    built_at: str,
) -> Path:
    built_names = {r["country"] for r in rows}
    midi_only = built_names == MIDI_COUNTRIES

    if midi_only:
        lines = [
            f"# IDS 2026 MIDI Country Packs {VERSION}",
            "",
            f"Built: {built_at}",
            "",
            "Scope: **MIDI only** — France, Italy, Spain, Switzerland.",
            "Other IDS markets (BE/NL/LUX, UK, Portugal, Israel, …) are **not** in this pack.",
            "",
            "## Average rule (Tomoe Baumann, 2026-07-31)",
            "",
            "| Market | Averages |",
            "|--------|----------|",
            "| **France** | Red-marked dealers **out** of averages (**20**); stay on list/map |",
            "| **Spain** | Red-marked dealers **out** of averages (**5**); stay on list/map |",
            "| **Italy** | **All** dealers in averages (including zero-score shells) |",
            "| **Switzerland** | **All** dealers in averages (including zero-score shells) |",
            "",
            "UI (country-only): Country filter / By country / Country radar / Changelog removed; "
            "national + anonymous network averages and Map hover kept.",
            "",
            "## Contents",
            "",
            "**HTML-only** country packs (dealer compare + README). Ranking / result "
            "Excel workbooks are **not** bundled here — they live under "
            "`01_data/90_INBOX/IDS_2026/rankings/` and `…/reports/` (same pattern as "
            f"the v1.3 MIDI HTML packs).",
            "",
            f"Master zip (`IDS_2026_Country_Packs_{VERSION}_ALL.zip`): four country "
            "zips + this INDEX.md + manifest.json only (no unpacked country folders).",
            "",
            "| Country | Dealers | Zip | HTML | Draft To | Geo |",
            "|---------|--------:|-----|------|----------|-----|",
        ]
    else:
        lines = [
            f"# IDS 2026 Country Packs {VERSION}",
            "",
            f"Built: {built_at}",
            "",
            "Scope: **all IDS markets** except the Benelux rollup (BE / NL / LUX stay separate).",
            "Includes UK LCV (IUK), Portugal, Israel LCV (UMI) and MIDI (FR/IT/ES/CH).",
            "",
            "UI (country-only): Country filter / By country / Country radar / Changelog removed; "
            "national + anonymous network averages and Map hover kept. "
            f"Version {VERSION}: FR/ES Baumann red-marked out of averages; "
            "IT/CH all dealers in averages.",
            "",
            f"Master zip (`IDS_2026_Country_Packs_{VERSION}_ALL.zip`): country zips + this "
            "INDEX.md + manifest.json only (no unpacked country folders).",
            "",
            "| Country | Dealers | Zip | HTML | Draft To | Geo |",
            "|---------|--------:|-----|------|----------|-----|",
        ]
    for r in rows:
        lines.append(
            f"| {r['country']} | {r['dealer_count']} | "
            f"`{r['zip_rel']}` | `{r['html_rel']}` | "
            f"{r.get('to_email') or '*(fill To)*'} | "
            f"{r.get('geo_ok', 0)}/{r['dealer_count']} |"
        )
    if midi_only:
        lines.extend(
            [
                "",
                "## Draft email",
                "",
                "Outlook draft to Tomoe Baumann via `draft_ids_midi_v14.py` "
                "(Save as draft — does not Send).",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## UK label note",
                "",
                "Workspace mapping (do not flip): **UK CV = ITUK**, **UK LCV = IUK**.",
                "This pack set includes **both** UK CV and UK LCV.",
                "",
                "## Draft emails",
                "",
                "Outlook drafts are created by `draft_ids_country_pack_emails.py` "
                "(Save as draft — does not Send).",
                "",
            ]
        )
    path = pack_root / "INDEX.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "version": VERSION,
        "built_at": built_at,
        "pack_scope": "MIDI" if midi_only else "colleague_batch",
        "countries": rows,
        "exclude": sorted(DEFAULT_EXCLUDE) if not midi_only else sorted(
            c for c in DEFAULT_EXCLUDE if c not in MIDI_COUNTRIES
        ),
    }
    (pack_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def build_one(
    full: dict[str, Any],
    country: str,
    pack_root: Path,
    *,
    built_at: str,
    skip_qa: bool,
    skip_geo_sanity: bool,
    no_mirror: bool,
) -> dict[str, Any]:
    payload = filter_country_payload(full, country)
    if not payload["dealers"]:
        raise RuntimeError(f"No dealers for {country}")

    qa_errors = validate_dashboard_payload(payload)
    totals_only_n = sum(1 for d in payload["dealers"] if d.get("totals_only"))
    # UK CV (ITUK) result report is totals-only in extract — still ship map + totals.
    allow_totals_only = totals_only_n == len(payload["dealers"]) and all(
        d.get("total_pct") is not None for d in payload["dealers"]
    )
    if qa_errors and not skip_qa and not allow_totals_only:
        raise RuntimeError(f"QA failed for {country}: {qa_errors}")
    if qa_errors and allow_totals_only:
        print(
            f"WARN {country}: totals-only extract — shipping map/totals pack "
            f"(QA notes: {len(qa_errors)})",
            flush=True,
        )

    geo_counts = attach_geo_to_dealers(payload["dealers"], allow_country_centre=True)
    payload["geo"] = geo_counts
    geo_sanity = sanity_check_geo_clustering(payload["dealers"])
    payload["geo_sanity"] = {
        "ok": geo_sanity["ok"],
        "errors": geo_sanity["errors"],
        "warnings": geo_sanity["warnings"],
        "countries": geo_sanity["countries"],
    }
    if not geo_sanity["ok"] and not skip_geo_sanity:
        raise RuntimeError(
            f"Geo sanity failed for {country}: {geo_sanity['errors']}"
        )

    payload["built_at"] = built_at
    payload["version"] = VERSION

    slug = slug_country(country)
    pack_dir = pack_root / slug
    pack_dir.mkdir(parents=True, exist_ok=True)

    html_name = f"IDS_2026_dealer_compare_{slug}.html"
    html = render_country_html(payload, country, built_at=built_at)
    compare_path = pack_dir / html_name
    compare_path.write_text(html, encoding="utf-8")

    if not no_mirror:
        DASH_MIRROR.mkdir(parents=True, exist_ok=True)
        (DASH_MIRROR / html_name).write_text(html, encoding="utf-8")

    write_readme(pack_dir, country, dealer_count=len(payload["dealers"]), geo=geo_counts)

    zip_name = f"IDS_2026_{slug}_{VERSION}.zip"
    zip_path = pack_root / zip_name
    zip_pack(pack_dir, zip_path, html_name)

    owner = OWNER_EMAIL.get(country) or {}
    subject = f"IDS 2026 — {country} dealer compare {VERSION} (map)"
    body = email_body(
        country,
        dealer_count=len(payload["dealers"]),
        zip_name=zip_name,
        html_name=html_name,
    )
    draft_meta = {
        "country": country,
        "slug": slug,
        "dealer_count": len(payload["dealers"]),
        "html_path": str(compare_path),
        "html_rel": f"{slug}/{html_name}",
        "zip_path": str(zip_path),
        "zip_rel": zip_name,
        "to_name": owner.get("name"),
        "to_email": owner.get("email"),
        "bcc": JEROME_EMAIL,
        "subject": subject,
        "body": body,
        "geo_ok": geo_counts.get("geo_ok"),
        "geo_missing": geo_counts.get("geo_missing"),
        "geo_sanity_ok": geo_sanity["ok"],
        "geo_warnings": geo_sanity.get("warnings") or [],
        "checks": {
            "version_label": VERSION in html,
            "map_tab": 'data-tab="map"' in html,
            "national_avg": "national average" in html.lower(),
            "no_weak_sector": "Weak sector" not in html,
            "leaflet": "leaflet" in html.lower() and "basemaps.cartocdn.com" in html,
            "single_country": payload["countries"] == [country],
            "no_country_filter": '<label for="f-country">Country filter</label>'
            not in html
            and 'id="country-only-ui"' in html,
            "no_by_country_tab": "By country</button>" not in html,
            "no_country_radar_tab": "Country radar</button>" not in html,
            "no_changelog": 'data-tab="changelog"' not in html
            and 'id="panel-changelog"' not in html
            and "Changelog</button>" not in html
            and "Changelog —" not in html,
        },
    }
    (pack_dir / "draft_email.json").write_text(
        json.dumps(draft_meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(format_qa_report(payload, qa_errors), flush=True)
    print(format_geo_sanity_report(geo_sanity), flush=True)
    msg = (
        f"OK {country}: {len(payload['dealers'])} dealers -> "
        f"{compare_path.name} + {zip_name}"
    )
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)
    return draft_meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=IDS_RESULT_REPORTS_DIR)
    parser.add_argument("--out-dir", type=Path, default=PACK_ROOT_DEFAULT)
    parser.add_argument(
        "--countries",
        nargs="*",
        default=None,
        help="Override country list (English labels)",
    )
    parser.add_argument("--skip-qa", action="store_true")
    parser.add_argument("--skip-geo-sanity", action="store_true")
    parser.add_argument("--no-mirror", action="store_true")
    args = parser.parse_args()

    # Explicit --countries overrides DEFAULT_EXCLUDE (e.g. rebuild UK LCV on demand).
    countries = list(args.countries) if args.countries else list(DEFAULT_INCLUDE)
    if not args.countries:
        countries = [c for c in countries if c not in DEFAULT_EXCLUDE]

    print(f"Building full network payload from {args.reports_dir}…")
    full = build_dashboard_payload(args.reports_dir)
    available = set(full.get("countries") or [])
    missing = [c for c in countries if c not in available]
    if missing:
        print(f"WARNING: not in payload: {missing}")
    countries = [c for c in countries if c in available]
    if not countries:
        print("No countries to build", flush=True)
        return 2

    pack_root = args.out_dir
    pack_root.mkdir(parents=True, exist_ok=True)
    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows: list[dict[str, Any]] = []
    failed: list[str] = []
    for country in countries:
        try:
            meta = build_one(
                full,
                country,
                pack_root,
                built_at=built_at,
                skip_qa=args.skip_qa,
                skip_geo_sanity=args.skip_geo_sanity,
                no_mirror=args.no_mirror,
            )
            rows.append(meta)
        except Exception as exc:  # noqa: BLE001 — collect per-country failures
            failed.append(f"{country}: {exc}")
            print(f"FAIL {country}: {exc}", flush=True)

    index = write_master_index(pack_root, rows, built_at=built_at)
    drafts_json = pack_root / "draft_emails.json"
    drafts_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    all_zip = pack_root / f"IDS_2026_Country_Packs_{VERSION}_ALL.zip"
    write_master_all_zip(pack_root, rows, all_zip)
    print(f"Master zip: {all_zip}")

    print(f"\nIndex: {index}")
    print(f"Drafts meta: {drafts_json}")
    print(f"Built {len(rows)} / {len(countries)} countries")
    if failed:
        print("Failures:")
        for f in failed:
            print(f"  {f}")
        return 3
    return 0


def write_master_all_zip(
    pack_root: Path, rows: list[dict[str, Any]], zip_path: Path
) -> Path:
    """One zip with per-country zips + INDEX.md + manifest.json (no unpacked folders).

    Colleagues open one country zip; no folder+zip duplicate pairs.
    """
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        index = pack_root / "INDEX.md"
        if index.is_file():
            zf.write(index, "INDEX.md")
        manifest = pack_root / "manifest.json"
        if manifest.is_file():
            zf.write(manifest, "manifest.json")
        for r in rows:
            cz = pack_root / r["zip_rel"]
            if not cz.is_file():
                raise FileNotFoundError(f"Missing country zip for ALL pack: {cz}")
            zf.write(cz, r["zip_rel"])
    return zip_path


if __name__ == "__main__":
    raise SystemExit(main())
