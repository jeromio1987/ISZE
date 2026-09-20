"""Shared path helpers for IDS_2026 country folders."""

from __future__ import annotations

import sys
from pathlib import Path

_WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
if str(_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE))

from isze_paths import INBOX_DIR, ISZE_ROOT  # noqa: E402

REPO = ISZE_ROOT
DATA_ROOT = INBOX_DIR / "IDS_2026"
RANKINGS_DIR = DATA_ROOT / "rankings"
IDS_REPORTS_DIR = DATA_ROOT / "reports"
IDS_RESULT_REPORTS_DIR = IDS_REPORTS_DIR / "evaluation_result"
IDS_RESULT_DELTA_DIR = IDS_RESULT_REPORTS_DIR / "_delta"
IDS_DASHBOARD_DIR = IDS_REPORTS_DIR / "dashboard"
IDS_DASHBOARD_HTML = IDS_DASHBOARD_DIR / "IDS_2026_dealer_compare.html"
IDS_RESULT_TEMPLATE_NAME = "2026 IDS Evaluation Result Report_DK.xls"
IDS_RESULT_TEMPLATE = IDS_REPORTS_DIR / "_template" / IDS_RESULT_TEMPLATE_NAME
_LEGACY_RESULT_TEMPLATE = REPO / "01_data" / IDS_RESULT_TEMPLATE_NAME

RSA_TEMPLATE = DATA_ROOT / "RSA" / "IDS Evaluation Sheet_rev11 Alta Motorsenter.xlsx"
BE_TEMPLATE = DATA_ROOT / "BE" / "BE" / "IDS Evaluation Sheet - De Corte.xlsx"
NL_OUTPUT = DATA_ROOT / "IDS Evaluation Sheet 2026 - NL.xlsx"
ITUK_INPUT = DATA_ROOT / "ITUK" / "IDS ITUK self evaluations.xlsx"
ITUK_OUTPUT = RANKINGS_DIR / "ITUK_dealer_ranking.xlsx"
MIDI_FILE = DATA_ROOT / "MIDI" / "MIDI_FR.xlsx"

SKIP_DIRS = {"rankings", "reports", "__pycache__", "MIDI", "_EXPORT"}

# On-disk folder name -> English country / tab label (shared — shared sheets & dashboard)
#
# UK: do not flip these two. IUK = I.M. PARTS & SERVICE Limited (sold-to 2574),
# the LCV / D-Max distributor. ITUK = ISUZU TRUCK (UK) LIMITED (sold-to 2575),
# the CV / truck distributor. Confirmed by dealer populations (IUK = pickup
# dealers, ITUK = truck centres) and by IMG's own "26 summary" workbook.
COUNTRY_LABELS: dict[str, str] = {
    "Gasanzammit": "Malta",
    "Loutsios": "Cyprus",
    "BE": "Belgium",
    "NL": "Netherlands",
    "LUX": "Luxembourg",
    "Petros": "Greece",
    "RSA": "Norway",
    "IUK": "UK LCV",
    "ITUK": "UK CV",
    "Israel": "Israel LCV",
}

# Legacy codes / MIDI tags / ALL-CAPS sheet values → English display name
COUNTRY_DISPLAY_ALIASES: dict[str, str] = {
    "BE": "Belgium",
    "NL": "Netherlands",
    "LUX": "Luxembourg",
    "BENELUX": "Benelux",
    "Benelux": "Benelux",
    "MIDI_CH": "Switzerland",
    "MIDI_FR": "France",
    "MIDI_IT": "Italy",
    "MIDI_ES": "Spain",
    "CH": "Switzerland",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "PETROS": "Greece",
    "Petros": "Greece",
    "RSA": "Norway",
    "IUK": "UK LCV",
    "ITUK": "UK CV",
    "UK (IUK)": "UK LCV",
    "UK (ITUK)": "UK CV",
    "UK CV": "UK CV",
    "UK LCV": "UK LCV",
    "Israel": "Israel LCV",
    "Israel LCV": "Israel LCV",
    "Gasanzammit": "Malta",
    "Loutsios": "Cyprus",
    "MALTA": "Malta",
    "CYPRUS": "Cyprus",
    "HUNGARY": "Hungary",
    "ISRAEL": "Israel LCV",
    "POLAND": "Poland",
    "PORTUGAL": "Portugal",
    "ROMANIA": "Romania",
    "DENMARK": "Denmark",
    "GREECE": "Greece",
    "NORWAY": "Norway",
    "SWITZERLAND": "Switzerland",
    "FRANCE": "France",
    "ITALY": "Italy",
    "SPAIN": "Spain",
    "BELGIUM": "Belgium",
    "NETHERLANDS": "Netherlands",
    "LUXEMBOURG": "Luxembourg",
}

LABEL_TO_FOLDER: dict[str, str] = {v: k for k, v in COUNTRY_LABELS.items()}
for _folder in COUNTRY_LABELS:
    LABEL_TO_FOLDER.setdefault(_folder, _folder)


def country_label(folder_name: str) -> str:
    return COUNTRY_LABELS.get(folder_name, folder_name)


def country_display_name(name: str) -> str:
    """English label for sheets, dashboard filters, and Country row text."""
    raw = (name or "").strip()
    if not raw:
        return raw
    if raw in COUNTRY_DISPLAY_ALIASES:
        return COUNTRY_DISPLAY_ALIASES[raw]
    if raw in COUNTRY_LABELS:
        return COUNTRY_LABELS[raw]
    upper = raw.upper()
    if upper in COUNTRY_DISPLAY_ALIASES:
        return COUNTRY_DISPLAY_ALIASES[upper]
    if raw.isupper() and len(raw) > 2 and " " not in raw and "(" not in raw:
        return raw.title()
    return raw


def resolve_dk_template() -> Path:
    """DK master .xls — preferred under IDS_2026/reports/_template/, legacy 01_data fallback."""
    if IDS_RESULT_TEMPLATE.is_file():
        return IDS_RESULT_TEMPLATE
    if _LEGACY_RESULT_TEMPLATE.is_file():
        return _LEGACY_RESULT_TEMPLATE
    return IDS_RESULT_TEMPLATE


def result_report_path(country: str) -> Path:
    """Wide matrix report for a country (DK-clone .xls)."""
    label = country_display_name(country)
    return IDS_RESULT_REPORTS_DIR / f"2026 IDS Evaluation Result Report_{label}.xls"


def result_report_delta_path(country: str) -> Path:
    """Plain delta workbook vs country average (no DK formatting — not the main report)."""
    label = country_display_name(country)
    return IDS_RESULT_DELTA_DIR / f"2026 IDS Evaluation Result Report_{label}_Delta.xlsx"


def data_folder_for_country(country: str) -> str:
    return LABEL_TO_FOLDER.get(country, country)


def resolve_input_dir(country: str, data_root: Path = DATA_ROOT) -> Path:
    """Find the folder that contains dealer .xlsx files for a country."""
    folder = data_folder_for_country(country)
    base = data_root / folder
    nested = base / country
    if nested.is_dir() and _has_xlsx(nested):
        return nested
    nested_code = base / folder
    if nested_code.is_dir() and nested_code != base and _has_xlsx(nested_code):
        return nested_code
    if _has_xlsx(base):
        return base
    if base.is_dir():
        for child in sorted(base.iterdir(), key=lambda p: p.name.casefold()):
            if child.is_dir() and _has_xlsx(child):
                return child
    return base


def _has_xlsx(folder: Path) -> bool:
    return any(
        p.is_file() and not p.name.startswith("~$")
        for p in folder.glob("*.xlsx")
    )


def discover_country_folders(data_root: Path = DATA_ROOT) -> list[str]:
    """English country labels for folders that contain at least one dealer workbook."""
    if not data_root.is_dir():
        return []

    countries: list[str] = []
    for p in sorted(data_root.iterdir(), key=lambda x: x.name.casefold()):
        if not p.is_dir() or p.name in SKIP_DIRS:
            continue
        if p.name.startswith("_"):
            continue
        if p.name.upper() == "ITUK":
            if (p / "IDS ITUK self evaluations.xlsx").is_file():
                countries.append(country_label("ITUK"))
            continue
        if _has_xlsx(resolve_input_dir(p.name, data_root)):
            countries.append(country_label(p.name))
    ituk_label = country_label("ITUK")
    if ituk_label in countries:
        countries = [c for c in countries if c != ituk_label] + [ituk_label]
    return countries
